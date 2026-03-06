from rest_framework import viewsets
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, Count
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import LogAuditoria, ArqueoCaja
from apps.negocio.models import PuntoVenta
from apps.ventas.models import Venta, DetalleVenta
from .serializers import LogAuditoriaSerializer, ArqueoCajaSerializer
from rest_framework.permissions import IsAuthenticated
from apps.inventario.models import InventarioSucursal
from apps.usuarios.permissions import IsSupervisorOrHigher
from .services import proyectar_reposicion_por_producto

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
            return Response({"error": "El usuario ya tiene una caja abierta en otro punto de venta."}, status=400)
        
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
            return Response({"error": "La caja ya está cerrada."}, status=400)

        if arqueo.usuario_apertura != request.user:
            return Response(
                {"error": "Solo el usuario que abrió la caja puede cerrarla."},
                status=403
            )

        monto_final_real = request.data.get("monto_final_real")
        if monto_final_real is None:
            return Response({"error": "Debe enviar monto_final_real."}, status=400)

        ventas = Venta.objects.filter(
            punto_venta=arqueo.punto_venta,
            fecha_hora__gte=arqueo.fecha_apertura,
            estado_venta__nombre="Pagada"
        )

        monto_sistema = sum(v.total_neto for v in ventas)
        monto_final_sistema = arqueo.monto_inicial + monto_sistema

        arqueo.cerrar(
            usuario_cierre=request.user,
            monto_final_real=monto_final_real,
            monto_final_sistema=monto_final_sistema
        )

        return Response({"mensaje": "Caja cerrada correctamente"}, status=200)

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
    
    # ✅ Acción: Buscar arqueo abierto por usuario
    @action(detail=False, methods=['get'])
    def abierta_usuario(self, request):
        usuario = request.user

        arqueo = ArqueoCaja.objects.filter(
            usuario_apertura=usuario,
            estado="ABIERTA"
        ).first()

        if not arqueo:
            return Response({"abierta": False}, status=200)

        return Response({
            "abierta": True,
            "arqueo": ArqueoCajaSerializer(arqueo).data
        }, status=200)
    
class AnaliticaVentasViewSet(viewsets.ViewSet):
    permission_classes = [IsSupervisorOrHigher]

    @action(detail=False, methods=["get"], url_path="prediccion-reposicion")
    def prediccion_reposicion(self, request):
        sucursal_id = request.query_params.get("sucursal")
        dias_historial = int(request.query_params.get("dias_historial", 30))
        dias_prediccion = int(request.query_params.get("dias_prediccion", 14))

        if not sucursal_id:
            return Response({"detail": "Debe enviar sucursal."}, status=400)
        if dias_historial <= 0 or dias_prediccion <= 0:
            return Response({"detail": "dias_historial y dias_prediccion deben ser mayores a cero."}, status=400)

        fecha_inicio = timezone.now() - timedelta(days=dias_historial)

        ventas_detalle = (
            DetalleVenta.objects.filter(
                venta__sucursal_id=sucursal_id,
                venta__fecha_hora__gte=fecha_inicio,
            )
            .exclude(venta__estado_venta__nombre="ANULADA")
            .values("producto_id", "producto__nombre")
            .annotate(
                cantidad_vendida=Sum("cantidad"),
                dias_con_venta=Count("venta__fecha_hora__date", distinct=True),
            )
            .order_by("producto__nombre")
        )

        inventario_map = {
            inv["producto_id"]: inv["stock_actual"]
            for inv in InventarioSucursal.objects.filter(sucursal_id=sucursal_id).values("producto_id", "stock_actual")
        }

        predicciones = []
        for row in ventas_detalle:
            proyeccion = proyectar_reposicion_por_producto(
                cantidad_vendida=row["cantidad_vendida"],
                dias_historial=dias_historial,
                dias_prediccion=dias_prediccion,
                stock_actual=inventario_map.get(row["producto_id"], 0),
            )

            frecuencia = round(dias_historial / row["dias_con_venta"], 2) if row["dias_con_venta"] else None

            predicciones.append(
                {
                    "producto_id": row["producto_id"],
                    "producto": row["producto__nombre"],
                    "cantidad_vendida_historial": row["cantidad_vendida"],
                    "dias_con_venta": row["dias_con_venta"],
                    "frecuencia_reposicion_dias": frecuencia,
                    "stock_actual": inventario_map.get(row["producto_id"], 0),
                    **proyeccion,
                }
            )

        predicciones.sort(key=lambda x: x["sugerido_reponer"], reverse=True)

        return Response(
            {
                "sucursal": int(sucursal_id),
                "dias_historial": dias_historial,
                "dias_prediccion": dias_prediccion,
                "total_productos_analizados": len(predicciones),
                "predicciones": predicciones,
            }
        )
