from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import LogAuditoria, ArqueoCaja

@admin.register(LogAuditoria)
class LogAuditoriaAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "fecha_hora", "entidad", "accion")
    search_fields = ("usuario__username", "entidad", "accion")
    list_filter = ("fecha_hora", "accion")
    ordering = ("-fecha_hora",)  # 👈 muestra lo más reciente primero

@admin.register(ArqueoCaja)
class ArqueoCajaAdmin(admin.ModelAdmin):
    list_display = (
        "id", 
        "punto_venta", 
        "usuario_apertura", 
        "usuario_cierre", 
        "fecha_apertura", 
        "fecha_cierre", 
        "monto_inicial", 
        "monto_final_sistema", 
        "monto_final_real", 
        "diferencia", 
        "estado"
    )
    list_filter = ("estado", "fecha_apertura", "fecha_cierre", "punto_venta")
    search_fields = ("usuario_apertura__username", "usuario_cierre__username", "punto_venta__nombre")
    date_hierarchy = "fecha_apertura"
    ordering = ("-fecha_apertura",)
    readonly_fields = ("fecha_apertura", "fecha_cierre", "diferencia")  # 👈 campos que no deberían editarse manualmente
    
