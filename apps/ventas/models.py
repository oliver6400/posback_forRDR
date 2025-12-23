from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from apps.negocio.models import Sucursal, Cliente, EstadoVenta, PuntoVenta
from apps.usuarios.models import Usuario
from apps.inventario.models import Producto


class Venta(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    punto_venta = models.ForeignKey(PuntoVenta, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="venta")
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, null=True, blank=True)
    estado_venta = models.ForeignKey(EstadoVenta, on_delete=models.PROTECT)
    fecha_hora = models.DateTimeField(auto_now_add=True)
    total_bruto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total_neto = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        app_label = 'ventas'
        verbose_name = 'Venta'
        verbose_name_plural = 'Ventas'
        db_table = 'venta'

    def __str__(self):
        return f"Venta {self.id} - {self.fecha_hora.strftime('%d/%m/%Y %H:%M')}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, related_name="detalles", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.DecimalField(max_digits=14, decimal_places=2)
    descuento = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.subtotal = (self.cantidad * self.precio_unitario) - self.descuento
        super().save(*args, **kwargs)

    class Meta:
        app_label = 'ventas'
        verbose_name = 'Detalle de Venta'
        verbose_name_plural = 'Detalles de Venta'
        db_table = 'detalle_venta'

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"

class FacturaSimulada(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    nit_ci = models.CharField(max_length=30)
    razon_social = models.CharField(max_length=255)
    numero_factura = models.CharField(max_length=100)
    fecha_emision = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'ventas'
        verbose_name = 'Factura Simulada'
        verbose_name_plural = 'Facturas Simuladas'
        db_table = 'factura_simulada'

    def __str__(self):
        return f"Factura {self.numero_factura} - Venta {self.venta.id}"

class MetodoPago(models.Model):
    nombre = models.CharField(max_length=50)

    class Meta:
            app_label = 'ventas'
            verbose_name = 'Metodo Pago'
            verbose_name_plural = 'Metodos de Pago'
            db_table = 'metodo_pago'    

    def __str__(self):
        return f"Factura {self.nombre}"
    
class VentaPago(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE)
    metodo_pago = models.ForeignKey(MetodoPago, on_delete=models.PROTECT)
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    referencia = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        app_label = 'ventas'
        verbose_name = 'Pago de Venta'
        verbose_name_plural = 'Pagos de Ventas'
        db_table = 'venta_pago'

    def __str__(self):
        return f"Pago de {self.monto} - {self.metodo_pago.nombre}"
