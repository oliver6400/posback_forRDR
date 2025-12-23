from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Rol

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ("id", "nombre", "activo")
    search_fields = ("nombre",)

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("id", "ci", "nombre", "apellido", "email", "rol", "is_staff", "is_active")
    search_fields = ("ci", "nombre", "apellido", "email")
    list_filter = ("is_staff", "is_active", "rol")
    fieldsets = (
        (None, {
            "fields": ("ci", "nombre", "apellido", "email", "telefono", "fecha_nacimiento", "username", "password", "rol")
        }),
        ("Permisos", {
            "fields": ("is_staff", "is_active", "is_superuser", "groups", "user_permissions")
        }),
        ("Información adicional", {
            "fields": ("password_reset_pin", "date_joined")
        }),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("ci", "nombre", "apellido", "email", "telefono", "fecha_nacimiento", "username", "password1", "password2", "is_staff", "is_active", "rol"),
        }),
    )
    ordering = ("date_joined",)

