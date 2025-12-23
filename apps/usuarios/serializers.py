# apps/usuarios/serializers.py
from rest_framework import serializers
from .models import Usuario, Rol
from django.contrib.auth.hashers import make_password
from django.contrib.auth import authenticate
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ['id', 'nombre']
        read_only_fields = ['id']
        extra_kwargs = {
            'nombre': {'required': True, 'allow_blank': False},
        }

    def validate_nombre(self, value):
        """Valida que el nombre del rol sea único (case insensitive)"""
        qs = Rol.objects.filter(nombre__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)

        if qs.exists():
            raise serializers.ValidationError("Ya existe un rol con este nombre")
        return value

class UsuarioSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)
    rol_id = serializers.PrimaryKeyRelatedField(
        queryset=Rol.objects.all(),
        source='rol',
        write_only=True
    )

    class Meta:
        model = Usuario
        fields = [
            'id', 'ci', 'username', 'email', 'nombre', 'apellido',
            'telefono', 'fecha_nacimiento', 
            'rol_id', 'rol', 'is_active', 'is_staff', 'date_joined', 'password'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'is_active': {'read_only': True},
            'date_joined': {'read_only': True},
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data.get('password'))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        if password:
            instance.password = make_password(password)
        return super().update(instance, validated_data)

# ← NUEVO: Serializer para JWT personalizado
class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Agregar claims personalizados al token
        token['username'] = user.username
        token['nombre'] = user.nombre
        token['apellido'] = user.apellido
        token['rol'] = user.rol.nombre if user.rol else None
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Agregar datos del usuario a la respuesta
        user_serializer = UsuarioSerializer(self.user)
        data['user'] = user_serializer.data
        
        return data
