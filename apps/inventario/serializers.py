from rest_framework import serializers
from .models import (
    Producto, ImagenProducto, 
    InventarioSucursal, MovimientoInventario, 
    MovimientoInventarioDetalle, 
)

class ImagenProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ImagenProducto
        fields = "__all__"

class ProductoSerializer(serializers.ModelSerializer):
    imagenes = ImagenProductoSerializer(many=True, source="imagenproducto_set", read_only=True)
    stock_actual = serializers.SerializerMethodField()
    stock_minimo = serializers.SerializerMethodField()

    def get_stock_actual(self, obj):
        sucursal_id = self.context.get("sucursal")
        inv = InventarioSucursal.objects.filter(producto=obj, sucursal_id=sucursal_id).first()
        return inv.stock_actual if inv else 0

    def get_stock_minimo(self, obj):
        sucursal_id = self.context.get("sucursal")
        inv = InventarioSucursal.objects.filter(producto=obj, sucursal_id=sucursal_id).first()
        return inv.stock_minimo if inv else 0

    class Meta:
        model = Producto
        fields = "__all__"

class InventarioSucursalSerializer(serializers.ModelSerializer):
    producto = serializers.PrimaryKeyRelatedField(queryset=Producto.objects.all())  # Asegúrate de usar solo el id

    class Meta:
        model = InventarioSucursal
        fields = [
            "id",
            "sucursal",
            "producto",
            "stock_actual",
            "stock_minimo",
        ]

class MovimientoInventarioDetalleSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = MovimientoInventarioDetalle
        fields = [
            "id",
            "movimiento",
            "producto",
            "cantidad",
            "costo_unitario",
        ]

class MovimientoInventarioSerializer(serializers.ModelSerializer):
    detalles = MovimientoInventarioDetalleSerializer(many=True, read_only=True)

    class Meta:
        model = MovimientoInventario
        fields = [
            "id",
            "sucursal",
            "usuario",
            "fecha_hora",
            "tipo_movimiento",
            "origen_tipo",
            "origen_id",
            "observacion",
            "detalles",
        ]


