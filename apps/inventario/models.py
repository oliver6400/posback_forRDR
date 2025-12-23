from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from apps.negocio.models import Sucursal
from apps.usuarios.models import Usuario
from django.core.exceptions import ValidationError

class Producto(models.Model):
    codigo_barras = models.CharField(max_length=80, unique=True)
    codigo = models.CharField(max_length=40, unique=True)
    nombre = models.CharField(max_length=50)
    unidad = models.CharField(max_length=50)
    precio_venta = models.DecimalField(max_digits=14, decimal_places=2)
    costo_promedio = models.DecimalField(max_digits=14, decimal_places=2)
    activo = models.BooleanField(default=True)

    class Meta:
        app_label = 'inventario'
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'
        db_table = 'producto'

    def __str__(self):
        return self.nombre

class ImagenProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    imagen = models.ImageField(upload_to="productos/")
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label = 'inventario'
        verbose_name = 'Imagen de Producto'
        verbose_name_plural = 'Imágenes de Productos'
        db_table = 'imagen_producto'

    def __str__(self):
        return f"Imagen de {self.producto.nombre}"


class InventarioSucursal(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    stock_actual = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    stock_minimo = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        app_label = 'inventario'
        verbose_name = 'Inventario por Sucursal'
        verbose_name_plural = 'Inventarios por Sucursal'
        db_table = 'inventario_sucursal'
        unique_together = ('sucursal', 'producto')

    def clean(self):
        """Validación de stock"""
        if self.stock_actual < 0:
            raise ValidationError('El stock actual no puede ser negativo.')

    def __str__(self):
        return f"{self.producto.nombre} - {self.sucursal.nombre} ({self.sucursal.ciudad.nombre})"
      
class MovimientoInventario(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="movimiento_inventario")
    fecha_hora = models.DateTimeField(auto_now_add=True)
    tipo_movimiento = models.CharField(max_length=20)  # Entrada / Salida
    origen_tipo = models.CharField(max_length=50)
    origen_id = models.IntegerField()
    observacion = models.TextField(blank=True, null=True)

    class Meta:
        app_label = 'inventario'
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        db_table = 'movimiento_inventario'

    def __str__(self):
            # OJO: el campo correcto es fecha_hora, no "fecha"
            return f"{self.tipo_movimiento} · {self.sucursal.nombre} · {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"

class MovimientoInventarioDetalle(models.Model):
    movimiento = models.ForeignKey(MovimientoInventario, related_name="detalles", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    costo_unitario = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        app_label = 'inventario'
        verbose_name = 'Detalle de Movimiento de Inventario'
        verbose_name_plural = 'Detalles de Movimientos de Inventario'
        db_table = 'movimiento_inventario_detalle'

    def __str__(self):
        return f"{self.producto.nombre} - {self.cantidad}"
