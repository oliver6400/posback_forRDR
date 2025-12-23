from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Venta, DetalleVenta, MetodoPago, FacturaSimulada, VentaPago

class DetalleVentaInline(admin.TabularInline):
    model = DetalleVenta
    extra = 1
    autocomplete_fields = ["producto"]
    fields = ["producto", "cantidad", "precio_unitario", "descuento", "subtotal"]
    readonly_fields = ["subtotal"]

class VentaPagoInline(admin.TabularInline):
    model = VentaPago
    extra = 1
    autocomplete_fields = ["metodo_pago"]
    fields = ["metodo_pago", "monto", "referencia"]

class FacturaSimuladaInline(admin.StackedInline):
    model = FacturaSimulada
    extra = 0
    max_num = 1
    fields = ["nit_ci", "razon_social", "numero_factura", "fecha_emision"]
    readonly_fields = ["fecha_emision"]

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ("id", "fecha_hora", "sucursal", "usuario", "cliente", "estado_venta", "total_neto")
    list_filter = ("sucursal", "estado_venta", "fecha_hora")
    search_fields = ("id", "cliente__nombre", "usuario__username")
    date_hierarchy = "fecha_hora"
    inlines = [DetalleVentaInline, VentaPagoInline, FacturaSimuladaInline]
    readonly_fields = ("fecha_hora",)

    fieldsets = (
        ("Información de la Venta", {
            "fields": ("sucursal", "usuario", "cliente", "estado_venta", "fecha_hora")
        }),
        ("Totales", {
            "fields": ("total_bruto", "total_descuento", "total_neto")
        }),
    )

@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)