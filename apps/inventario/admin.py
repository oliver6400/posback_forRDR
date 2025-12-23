from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Producto, ImagenProducto, InventarioSucursal, MovimientoInventario, MovimientoInventarioDetalle

class ImagenProductoInline(admin.TabularInline):
    model = ImagenProducto
    extra = 1


class MovimientoInventarioDetalleInline(admin.TabularInline):
    model = MovimientoInventarioDetalle
    extra = 1

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "unidad", "precio_venta", "costo_promedio", "activo")
    list_filter = ("activo",)
    search_fields = ("codigo", "codigo_barras", "nombre")
    inlines = [ImagenProductoInline]

@admin.register(InventarioSucursal)
class InventarioSucursalAdmin(admin.ModelAdmin):
    list_display = ("sucursal", "producto", "stock_actual", "stock_minimo")
    list_filter = ("sucursal", "producto")
    search_fields = ("producto__nombre", "sucursal__nombre")
    list_editable = ("stock_actual", "stock_minimo")

@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = ("id", "sucursal", "usuario", "fecha_hora", "tipo_movimiento", "origen_tipo", "origen_id")
    list_filter = ("sucursal", "tipo_movimiento", "fecha_hora")
    search_fields = ("usuario__username", "origen_tipo", "origen_id")
    date_hierarchy = "fecha_hora"
    inlines = [MovimientoInventarioDetalleInline]

@admin.register(MovimientoInventarioDetalle)
class MovimientoInventarioDetalleAdmin(admin.ModelAdmin):
    list_display = ("movimiento", "producto", "cantidad", "costo_unitario")
    search_fields = ("producto__nombre", "movimiento__id")
    list_filter = ("producto",)

