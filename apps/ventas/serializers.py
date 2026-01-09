from rest_framework import serializers
from .models import Venta, DetalleVenta, MetodoPago, FacturaSimulada, VentaPago
from apps.inventario.models import InventarioSucursal
from apps.reportes.models import ArqueoCaja
from django.db import transaction

class DetalleVentaSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)

    class Meta:
        model = DetalleVenta
        fields = ["id", "producto", "producto_nombre", "cantidad", "precio_unitario", "descuento", "subtotal"]
        
class VentaSerializer(serializers.ModelSerializer):
    detalles = DetalleVentaSerializer(many=True)

    class Meta:
        model = Venta
        fields = "__all__"
        read_only_fields = ("usuario", "total_bruto", "total_descuento", "total_neto")

    def validate(self, data):
        usuario = self.context["request"].user
        punto_venta = data.get("punto_venta")
        sucursal = data.get("sucursal")

        if not sucursal:
            raise serializers.ValidationError("Debe seleccionar una sucursal.")

        if not punto_venta:
            raise serializers.ValidationError("Debe seleccionar un punto de venta.")

        # Validar relación
        if punto_venta.sucursal_id != sucursal.id:
            raise serializers.ValidationError("El punto de venta no pertenece a esa sucursal.")

        # Validar caja abierta
        caja_abierta = ArqueoCaja.objects.filter(
            usuario_apertura=usuario,
            punto_venta=punto_venta,
            estado="ABIERTA"
        ).first()

        if not caja_abierta:
            raise serializers.ValidationError("Debe aperturar una caja para este punto de venta.")

        return data


    @transaction.atomic
    def create(self, validated_data):
        """Crear venta, registrar detalles y descontar stock."""
        detalles_data = validated_data.pop("detalles")
        validated_data["usuario"] = self.context["request"].user

        venta = Venta.objects.create(**validated_data)

        total_bruto = 0
        total_descuento = 0

        for detalle_data in detalles_data:
            producto = detalle_data["producto"]
            cantidad = detalle_data["cantidad"]
            precio_unitario = detalle_data["precio_unitario"]
            descuento = detalle_data.get("descuento", 0)

            # 🔒 Bloquear fila de inventario para evitar condiciones de carrera
            try:
                inventario = InventarioSucursal.objects.select_for_update().get(
                    sucursal=venta.sucursal, producto=producto
                )
            except InventarioSucursal.DoesNotExist:
                raise serializers.ValidationError(f"El producto {producto.nombre} no tiene stock en esta sucursal.")

            if inventario.stock_actual < cantidad:
                raise serializers.ValidationError(f"No hay suficiente stock de {producto.nombre}.")

            inventario.stock_actual -= cantidad
            inventario.save()

            DetalleVenta.objects.create(
                venta=venta,
                producto=producto,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                descuento=descuento,
            )

            total_bruto += cantidad * precio_unitario
            total_descuento += descuento

        venta.total_bruto = total_bruto
        venta.total_descuento = total_descuento
        venta.total_neto = total_bruto - total_descuento
        venta.save()

        return venta

class FacturaSimuladaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FacturaSimulada
        fields = ["id", "nit_ci", "razon_social", "numero_factura", "fecha_emision"]

class MetodoPagoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MetodoPago
        fields = "__all__"

class VentaPagoSerializer(serializers.ModelSerializer):
    metodo_pago = MetodoPagoSerializer(read_only=True)
    metodo_pago_id = serializers.PrimaryKeyRelatedField(
        queryset=MetodoPago.objects.all(), source="metodo_pago", write_only=True
    )
    venta_id = serializers.PrimaryKeyRelatedField(
        queryset=Venta.objects.all(), source="venta", write_only=True
    )

    class Meta:
        model = VentaPago
        fields = ["id", "venta_id", "metodo_pago", "metodo_pago_id", "monto", "referencia"]

    