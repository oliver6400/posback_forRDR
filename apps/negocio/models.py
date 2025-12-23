from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin

class Cliente(models.Model):
    nit = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=150)
    razon_social = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    
    class Meta:
        app_label = 'negocio'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        db_table = 'cliente'  

    def __str__(self):
        return self.nombre
    

class EstadoVenta(models.Model):
    nombre = models.CharField(max_length=50)

    class Meta:
        app_label = 'negocio'
        verbose_name = 'Estado de Venta'
        verbose_name_plural = 'Estados de Venta'
        db_table = 'estado_venta'

    def __str__(self):
        return self.nombre

class Ciudad(models.Model):
    nombre = models.CharField(max_length=100)

    class Meta:
        app_label = 'negocio'
        verbose_name = 'Ciudad'
        verbose_name_plural = 'Ciudades'
        db_table = 'ciudad'

    def __str__(self):
        return self.nombre

class Sucursal(models.Model):
    ciudad = models.ForeignKey(Ciudad, on_delete=models.PROTECT)
    nombre = models.CharField(max_length=100)
    direccion = models.TextField()
    activo = models.BooleanField(default=True)
    
    class Meta:
        app_label = 'negocio'
        verbose_name = 'Sucursal'
        verbose_name_plural = 'Sucursales'
        db_table = 'sucursal'

    def __str__(self):
        return f"{self.ciudad} - {self.nombre}"

class PuntoVenta(models.Model):
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        app_label = 'negocio'
        verbose_name = 'Punto de Venta'
        verbose_name_plural = 'Puntos de Venta'
        db_table = 'punto_venta'

    def __str__(self):
        return f"{self.nombre} - {self.sucursal.nombre}"