from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from apps.usuarios.models import Usuario
from apps.inventario.models import Producto
from apps.negocio.models import Sucursal, PuntoVenta
from django.utils import timezone

class LogAuditoria(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    entidad = models.CharField(max_length=100)
    accion = models.CharField(max_length=50)
    detalle_json = models.JSONField()

    class Meta:
        app_label = 'reportes'
        verbose_name = 'Log de Auditoría'
        verbose_name_plural = 'Logs de Auditoría'
        db_table = 'log_auditoria'

    def __str__(self):
        return f"{self.usuario} - {self.accion} - {self.entidad}"

class ArqueoCaja(models.Model):
    ESTADOS = [
        ("ABIERTA", "Abierta"),
        ("CERRADA", "Cerrada"),
    ]
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    punto_venta = models.ForeignKey(PuntoVenta, on_delete=models.CASCADE)
    usuario_apertura = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    usuario_cierre = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='arqueos_cerrados', null=True, blank=True)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    monto_inicial = models.DecimalField(max_digits=14, decimal_places=2)
    monto_final_sistema = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    monto_final_real = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    diferencia = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="CERRADA")

    class Meta:
        app_label = 'reportes'
        verbose_name = 'Arqueo de Caja'
        verbose_name_plural = 'Arqueos de Caja'
        db_table = 'arqueo_caja'

    def __str__(self):
        return f"Arqueo {self.id} - {self.punto_venta.nombre} - {self.usuario_apertura.username} ({self.estado})"
      
    def cerrar(self, usuario_cierre, monto_final_real):
        self.usuario_cierre = usuario_cierre
        self.monto_final_real = monto_final_real
        self.fecha_cierre = timezone.now()
        self.diferencia = self.monto_final_real - self.monto_final_sistema
        self.estado = "Cerrado"
        self.save()
