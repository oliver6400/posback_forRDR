from django.db import transaction
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.reportes.models import ArqueoCaja

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
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    permission_classes = [IsAuthenticated]

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

        serializer.save(
            usuario=usuario,
            fecha_hora=timezone.now()
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

    @transaction.atomic
    def perform_update(self, serializer):
        usuario = self.request.user
        venta_actual = self.get_object()

        # Validar caja antes de permitir actualizaciones que impliquen stock o pagos
        self.validar_caja_abierta(usuario, venta_actual.punto_venta)

        venta_antes = Venta.objects.get(pk=venta_actual.pk)
        estado_antes = venta_antes.estado_venta_id

        venta = serializer.save()
        estado_despues = venta.estado_venta_id

        EN_PROCESO = 1
        PAGADA = 2
        ANULADA = 3

        # ---- PAGADA ----
        if estado_antes != PAGADA and estado_despues == PAGADA:
            existe_salida = MovimientoInventario.objects.filter(
                sucursal=venta.sucursal,
                origen_tipo="VENTA",
                origen_id=venta.id,
                tipo_movimiento="Salida",
            ).exists()

            if not existe_salida:
                mov = MovimientoInventario.objects.create(
                    sucursal=venta.sucursal,
                    usuario=usuario,
                    tipo_movimiento="Salida",
                    origen_tipo="VENTA",
                    origen_id=venta.id,
                    observacion=f"Venta {venta.id} pagada (consumo de reserva)",
                )
                for det in venta.detalles.all():
                    MovimientoInventarioDetalle.objects.create(
                        movimiento=mov,
                        producto=det.producto,
                        cantidad=det.cantidad,
                        costo_unitario=det.precio_unitario,
                    )

        # ---- ANULADA ----
        elif estado_antes in (EN_PROCESO, PAGADA) and estado_despues == ANULADA:

            # 1) devolver stock
            for det in venta.detalles.select_for_update():
                inv, _ = InventarioSucursal.objects.select_for_update().get_or_create(
                    sucursal=venta.sucursal,
                    producto=det.producto,
                    defaults={"stock_actual": 0, "stock_minimo": 0},
                )
                inv.stock_actual += det.cantidad
                inv.save()

            # 2) registrar movimiento
            if estado_antes == PAGADA:
                existe_entrada = MovimientoInventario.objects.filter(
                    sucursal=venta.sucursal,
                    origen_tipo="ANULACION_VENTA",
                    origen_id=venta.id,
                    tipo_movimiento="Entrada",
                ).exists()

                if not existe_entrada:
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


