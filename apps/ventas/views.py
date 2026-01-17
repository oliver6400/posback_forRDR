from django.db import transaction
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.core.exceptions import ValidationError
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

class FacturaSimuladaViewSet(viewsets.ModelViewSet):
    queryset = FacturaSimulada.objects.all()
    serializer_class = FacturaSimuladaSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def generar(self, request):
        """Generar factura simulada"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        factura = serializer.save()
        return Response({
            "mensaje": "Factura simulada generada con éxito",
            "factura": serializer.data
        })

class MetodoPagoViewSet(viewsets.ModelViewSet):
    queryset = MetodoPago.objects.all()
    serializer_class = MetodoPagoSerializer
    permission_classes = [IsAuthenticated]


class DetalleVentaViewSet(viewsets.ModelViewSet):
    queryset = DetalleVenta.objects.all()
    serializer_class = DetalleVentaSerializer
    permission_classes = [IsAuthenticated]


class VentaPagoViewSet(viewsets.ModelViewSet):
    queryset = VentaPago.objects.all()
    serializer_class = VentaPagoSerializer   # ⚠️ esto deberías cambiarlo
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'])
    def registrar_pago(self, request):
        """Registrar un pago para una venta"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        pago = serializer.save()
        return Response({
            "mensaje": "Pago registrado con éxito",
            "pago": serializer.data
        })   


