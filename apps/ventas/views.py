from django.db import transaction
from django.utils import timezone
from datetime import datetime, time
from django.db.models import F, Sum, Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Sum, Count
from decimal import Decimal
from django.utils.dateparse import parse_date
from django.core.exceptions import ValidationError
from rest_framework.exceptions import ValidationError as DRFValidationError
from apps.negocio.models import EstadoVenta
from apps.reportes.models import ArqueoCaja
from django_filters.rest_framework import DjangoFilterBackend

from .models import Venta, DetalleVenta, MetodoPago, FacturaSimulada, VentaPago
from .serializers import (
    VentaSerializer,
    DetalleVentaSerializer,
    MetodoPagoSerializer,
    FacturaSimuladaSerializer,
    VentaPagoSerializer,
)

from apps.inventario.models import (
    InventarioSucursal,
    MovimientoInventario,
    MovimientoInventarioDetalle,
)

class VentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.select_related(
        "sucursal", "punto_venta", "usuario", "estado_venta"
    ).prefetch_related("detalles")
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]

    filter_backends = [DjangoFilterBackend]
    filterset_fields = {
        "estado_venta__nombre": ["exact"],
        "fecha_hora": ["date", "gte", "lte"],
        "punto_venta": ["exact"],
        "sucursal": ["exact"],
    }

    # El serializer necesita el request para CurrentUserDefault, etc.
    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        ctx.update({"request": self.request})
        return ctx
    
    @staticmethod
    def validar_caja_abierta(usuario, punto_venta):
        arqueo = ArqueoCaja.objects.filter(
            punto_venta=punto_venta,
            usuario_apertura=usuario,
            estado="ABIERTA"
        ).first()

        if not arqueo:
            raise ValidationError("Debe aperturar una caja antes de realizar ventas.")
        return arqueo

    @transaction.atomic
    def perform_create(self, serializer):
        usuario = self.request.user
        punto_venta = serializer.validated_data.get("punto_venta")

        if not punto_venta:
            raise ValidationError("Debe seleccionar un punto de venta.")

        # Validar arqueo abierto ANTES de guardar
        self.validar_caja_abierta(usuario, punto_venta)

        # 🔒 estado inicial garantizado
        estado_pagada, _ = EstadoVenta.objects.get_or_create(nombre="PAGADA")

        serializer.save(
            usuario=usuario,
            estado_venta=estado_pagada,
        )

    @action(detail=True, methods=["post"])
    def agregar_detalle(self, request, pk=None):
        venta = self.get_object()

        # Validar caja abierta para el punto de venta actual
        self.validar_caja_abierta(request.user, venta.punto_venta)

        ser = DetalleVentaSerializer(
            data=request.data, context=self.get_serializer_context()
        )
        if ser.is_valid():
            ser.save(venta=venta)
            return Response(ser.data, status=status.HTTP_201_CREATED)
        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=["post"])
    @transaction.atomic
    def anular(self, request, pk=None):
        venta = self.get_object()
        usuario = request.user

        # 🔒 Validar caja
        self.validar_caja_abierta(usuario, venta.punto_venta)

        if venta.estado_venta.nombre == "ANULADA":
            return Response(
                {"detail": "La venta ya está anulada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estado_anulada, _ = EstadoVenta.objects.get_or_create(nombre="ANULADA")

        # 🔁 Devolver stock
        for det in venta.detalles.select_for_update():
            inventario, _ = InventarioSucursal.objects.select_for_update().get_or_create(
                sucursal=venta.sucursal,
                producto=det.producto,
                defaults={"stock_actual": 0, "stock_minimo": 0},
            )
            inventario.stock_actual += det.cantidad
            inventario.save()

        # 📦 Registrar movimiento
        mov = MovimientoInventario.objects.create(
            sucursal=venta.sucursal,
            usuario=usuario,
            tipo_movimiento="Entrada",
            origen_tipo="ANULACION_VENTA",
            origen_id=venta.id,
            observacion=f"Anulación de venta {venta.id}",
        )

        for det in venta.detalles.all():
            MovimientoInventarioDetalle.objects.create(
                movimiento=mov,
                producto=det.producto,
                cantidad=det.cantidad,
                costo_unitario=det.precio_unitario,
            )

        # 🔄 Cambiar estado
        venta.estado_venta = estado_anulada
        venta.save()

        return Response(
            {"detail": f"Venta {venta.id} anulada correctamente."},
            status=status.HTTP_200_OK,
        )

    def perform_update(self, serializer):
        raise ValidationError("Las ventas no se pueden modificar directamente.")
    
    @action(detail=False, methods=["get"])
    def dashboard(self, request):

        sucursal_id = request.query_params.get("sucursal")
        fecha = request.query_params.get("fecha")
        fecha_inicio = request.query_params.get("fecha_inicio")
        fecha_fin = request.query_params.get("fecha_fin")

        if not sucursal_id:
            return Response({"detail": "Debe enviar sucursal."}, status=400)

        ventas = Venta.objects.filter(sucursal_id=sucursal_id)

        inicio = None
        fin = None

        if fecha:
            fecha_obj = parse_date(fecha)
            if not fecha_obj:
                return Response({"detail": "Fecha inválida. Use el formato YYYY-MM-DD."}, status=400)
            inicio = timezone.make_aware(datetime.combine(fecha_obj, time.min))
            fin = timezone.make_aware(datetime.combine(fecha_obj, time.max))

        elif fecha_inicio and fecha_fin:
            fecha_inicio_obj = parse_date(fecha_inicio)
            fecha_fin_obj = parse_date(fecha_fin)
            if not fecha_inicio_obj or not fecha_fin_obj:
                return Response({"detail": "Rango de fechas inválido. Use el formato YYYY-MM-DD."}, status=400)
            inicio = timezone.make_aware(datetime.combine(fecha_inicio_obj, time.min))
            fin = timezone.make_aware(datetime.combine(fecha_fin_obj, time.max))

        if inicio and fin:
            ventas = ventas.filter(fecha_hora__range=(inicio, fin))

        ventas = ventas.exclude(estado_venta__nombre="ANULADA")

        data = ventas.aggregate(
            total=Sum("total_neto"),
            cantidad=Count("id")
        )

        total = data["total"] or Decimal("0.00")
        cantidad = data["cantidad"] or 0
        ticket_promedio = total / cantidad if cantidad > 0 else Decimal("0.00")

        ranking = DetalleVenta.objects.filter(
            venta__sucursal_id=sucursal_id,
        ).exclude(venta__estado_venta__nombre="ANULADA")

        if inicio and fin:
            ranking = ranking.filter(venta__fecha_hora__range=(inicio, fin))

        ranking = (
            ranking.values("producto__nombre")
            .annotate(
                cantidad_total=Sum("cantidad"),
                total_generado=Sum(F("cantidad") * F("precio_unitario"))
            )
            .order_by("-cantidad_total")[:10]
        )

        return Response({
            "total_vendido": total,
            "cantidad_ventas": cantidad,
            "ticket_promedio": ticket_promedio,
            "ranking_productos": list(ranking)
        })
    
    def get_queryset(self):
        queryset = Venta.objects.all()

        sucursal = self.request.query_params.get('sucursal')
        fecha = self.request.query_params.get('fecha')

        if sucursal:
            queryset = queryset.filter(sucursal_id=sucursal)

        if fecha:
            fecha_obj = parse_date(fecha)
            if not fecha_obj:
                raise DRFValidationError("Fecha inválida. Use el formato YYYY-MM-DD.")
            inicio = timezone.make_aware(datetime.combine(fecha_obj, time.min))
            fin = timezone.make_aware(datetime.combine(fecha_obj, time.max))
            queryset = queryset.filter(fecha_hora__range=(inicio, fin))

        return queryset

class FacturaSimuladaViewSet(viewsets.ModelViewSet):
    queryset = FacturaSimulada.objects.all()
    serializer_class = FacturaSimuladaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generar(self, request):
        """Generar factura simulada"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({
            "mensaje": "Factura simulada generada con éxito",
            "factura": serializer.data
        })

class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer
    permission_classes = [IsAuthenticated]


class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = VentaPago.objects.select_related("venta", "metodo_pago")
    serializer_class = VentaPagoSerializer
    permission_classes = [IsAuthenticated]


class VentaPagoViewSet(viewsets.ModelViewSet):
    queryset = VentaPago.objects.all()
    serializer_class = VentaPagoSerializer   # ⚠️ esto deberías cambiarlo
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    @staticmethod
    def _resumen_pago_venta(venta):
        total_pagado = (
            VentaPago.objects.filter(venta=venta).aggregate(total=Sum("monto"))["total"]
            or Decimal("0.00")
        )
        total_venta = venta.total_neto or Decimal("0.00")
        cambio = max(total_pagado - total_venta, Decimal("0.00"))
        pendiente = max(total_venta - total_pagado, Decimal("0.00"))

        return {
            "total_venta": total_venta,
            "total_pagado": total_pagado,
            "pendiente": pendiente,
            "cambio": cambio,
            "pagada_completa": pendiente == Decimal("0.00"),
        }
    
    @action(detail=False, methods=["post"])
    def registrar_pago(self, request):
        """Registrar un pago para una venta"""
        """Registrar uno o más pagos por venta y calcular pendiente/cambio."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pago = serializer.save()
        return Response({
            "mensaje": "Pago registrado con éxito",
            "pago": serializer.data
        })   

        resumen = self._resumen_pago_venta(pago.venta)

        return Response(
            {
                "mensaje": "Pago registrado con éxito",
                "pago": serializer.data,
                "resumen_pago": resumen,
            }
        )