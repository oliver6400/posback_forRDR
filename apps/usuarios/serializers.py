from django.contrib.auth.hashers import make_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Usuario, Rol


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = ["id", "nombre"]
        read_only_fields = ["id"]

    def validate_nombre(self, value):
        qs = Rol.objects.filter(nombre__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Ya existe un rol con este nombre")
        return value


class UsuarioSerializer(serializers.ModelSerializer):
    rol = RolSerializer(read_only=True)
    rol_id = serializers.PrimaryKeyRelatedField(queryset=Rol.objects.all(), source="rol", write_only=True)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "ci",
            "username",
            "email",
            "nombre",
            "apellido",
            "telefono",
            "fecha_nacimiento",
            "rol_id",
            "rol",
            "is_active",
            "is_staff",
            "date_joined",
            "password",
        ]
        extra_kwargs = {
            "password": {"write_only": True},
            "is_active": {"read_only": True},
            "date_joined": {"read_only": True},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return attrs

        actor_role = request.user.rol.nombre
        target_role = attrs.get("rol", getattr(self.instance, "rol", None))
        target_role_name = target_role.nombre if target_role else ""

        # Superadmin puede crear admins y cualquier rol
        if actor_role == "SuperAdmin":
            return attrs

        # Admin solo puede crear/editar personal operativo
        if actor_role == "Admin":
            if target_role_name in {"SuperAdmin", "Admin"}:
                raise serializers.ValidationError(
                    "Un Admin solo puede crear/gestionar usuarios operativos (Supervisor/Cajero)."
                )
            attrs["is_staff"] = False
            attrs["is_superuser"] = False
            return attrs

        raise serializers.ValidationError("No tiene permisos para gestionar usuarios.")

    def create(self, validated_data):
        validated_data["password"] = make_password(validated_data.get("password"))
        return super().create(validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if password:
            instance.password = make_password(password)
        return super().update(instance, validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        token["nombre"] = user.nombre
        token["apellido"] = user.apellido
        token["rol"] = user.rol.nombre if user.rol else None
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_serializer = UsuarioSerializer(self.user)
        data["user"] = user_serializer.data
        return data
