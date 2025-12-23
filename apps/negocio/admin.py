from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Cliente, Ciudad, EstadoVenta, PuntoVenta, Sucursal 


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("id", "razon_social", "nit")
    search_fields = ("razon_social", "nit")

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'ciudad', 'direccion', 'activo']
    list_filter = ['ciudad', 'activo']
    search_fields = ('nombre', 'direccion')  # 👈 búsqueda rápida

@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)

@admin.register(PuntoVenta)
class PuntoVentaAdmin(admin.ModelAdmin):
    list_display = ['id', 'nombre', 'sucursal', 'activo']
    list_filter = ['sucursal', 'activo']  # <-- campos reales

@admin.register(EstadoVenta)
class EstadoVentaAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre")
    search_fields = ("nombre",)
