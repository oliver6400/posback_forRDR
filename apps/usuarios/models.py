from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager, PermissionsMixin
from django.utils import timezone

class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)

    class Meta:
        app_label = 'usuarios'
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
        db_table = 'rol'

    def __str__(self):
        return self.nombre

class UsuarioManager(BaseUserManager):
    def create_user(self, ci, email, nombre, apellido, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        if not ci:
            raise ValueError('El CI es obligatorio')
        
        email = self.normalize_email(email)
        user = self.model(
            ci=ci,
            email=email,
            nombre=nombre,
            apellido=apellido,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, ci, email, nombre, apellido, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        # Obtener o crear rol de SuperAdmin
        rol, _ = Rol.objects.get_or_create(nombre='SuperAdmin')
        extra_fields.setdefault('rol', rol)
        
        return self.create_user(ci, email, nombre, apellido, password, **extra_fields)

class Usuario(AbstractUser, PermissionsMixin):
    ci = models.CharField(max_length=20, unique=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    username = models.CharField(max_length=40, unique=True)
    password = models.CharField(max_length=128)
    activo = models.BooleanField(default=True)

    rol = models.ForeignKey(Rol, on_delete=models.PROTECT)
    password_reset_pin = models.CharField(max_length=6, blank=True, null=True)

    # Campos requeridos para el modelo de usuario personalizado
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UsuarioManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['ci', 'email', 'nombre', 'apellido', 'fecha_nacimiento']  # Actualización de campos requeridos

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuario'

    def __str__(self):
        return f"{self.nombre} {self.apellido}"

    def get_full_name(self):
        return f"{self.nombre} {self.apellido}"

    def get_short_name(self):
        return self.nombre
 
