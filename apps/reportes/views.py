from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LogAuditoria, ArqueoCaja
from apps.negocio.models import PuntoVenta
from apps.ventas.models import Venta
from .serializers import LogAuditoriaSerializer, ArqueoCajaSerializer
from rest_framework.permissions import IsAuthenticated

class LogAuditoriaViewSet(viewsets.ModelViewSet):
    queryset = LogAuditoria.objects.all()
    serializer_class = LogAuditoriaSerializer
    permission_classes = [IsAuthenticated]

class ArqueoCajaViewSet(viewsets.ModelViewSet):
    queryset = ArqueoCaja.objects.all().order_by('-fecha_apertura')
    serializer_class = ArqueoCajaSerializer
    permission_classes = [IsAuthenticated]

    # ✅ Acción: abrir caja
    @action(detail=False, methods=['post'])
    def abrir(self, request):
        usuario = request.user
        punto_venta_id = request.data.get("punto_venta")
        monto_inicial = request.data.get("monto_inicial")

        if not punto_venta_id:
            return Response({"error": "Debe enviar un punto de venta."}, status=400)

        if monto_inicial is None:
            return Response({"error": "Debe enviar un monto inicial."}, status=400)
        
        # 🔍 Validar punto de venta
        try:
            punto = PuntoVenta.objects.get(id=punto_venta_id)
        except PuntoVenta.DoesNotExist:
            return Response({"error": "Punto de venta no existe."}, status=404)

        # 🔒 Validar que el usuario NO tenga otra caja abierta
        abierta_usuario = ArqueoCaja.objects.filter(
            usuario_apertura=usuario,
            estado="ABIERTA"
        ).first()

        if abierta_usuario:
            return Response({"error": "Ya existe una caja abierta en este punto de venta."}, status=400)
        
        # 🔒 Validar que el punto de venta no tenga caja abierta
        abierta = ArqueoCaja.objects.filter(
            punto_venta=punto,
            estado="ABIERTA"
        ).first()

        if abierta:
            return Response(
                {"error": "Este punto de venta ya tiene una caja abierta."},
                status=400
            )

        arqueo = ArqueoCaja.objects.create(
            sucursal=punto.sucursal,
            punto_venta=punto,
            usuario_apertura=usuario,
            monto_inicial=monto_inicial,
            estado="ABIERTA"
        )

        return Response(ArqueoCajaSerializer(arqueo).data, status=201)

    # ✅ Acción: cerrar caja
    @action(detail=True, methods=['post'])
    def cerrar(self, request, pk=None):
        arqueo = self.get_object()

        if arqueo.estado != "ABIERTA":
            return Response({"error": "Esta caja ya fue cerrada."}, status=400)
        
        # calcular monto sistema
        ventas = Venta.objects.filter(
            punto_venta=arqueo.punto_venta,
            fecha__gte=arqueo.fecha_apertura,
        )
        monto_sistema = sum(venta.monto_total for venta in ventas)

        monto_final_sistema = arqueo.monto_inicial + monto_sistema
        monto_final_real = request.data.get("monto_final_real")
        diferencia = monto_final_sistema - monto_final_real
        usuario_cierre = request.user

        arqueo.cerrar(usuario_cierre, monto_real)
        arqueo.estado = "CERRADA"

        return Response({"mensaje": "Caja cerrada exitosamente"}, status=200)

    # ✅ Acción: obtener caja abierta actual
    @action(detail=False, methods=['get'])
    def abierta(self, request):
        punto_venta_id = request.query_params.get('punto_venta')

        if not punto_venta_id:
            return Response({"error": "Debe enviar punto_venta como parámetro."}, status=400)

        arqueo = ArqueoCaja.objects.filter(
            punto_venta_id=punto_venta_id, 
            estado="ABIERTA"
        ).first()

        if not arqueo:
            return Response({"abierta": False}, status=200)

        return Response({
            "abierta": True,
            "arqueo": ArqueoCajaSerializer(arqueo).data
        }, status=200)
