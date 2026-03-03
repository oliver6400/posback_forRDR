from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import Usuario, Rol
from .serializers import UsuarioSerializer, RolSerializer, CustomTokenObtainPairSerializer
from .permissions import IsSuperAdmin, IsAdminOrSuperAdmin


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related("rol").all()
    serializer_class = UsuarioSerializer

    def get_permissions(self):
        if self.action in {"get_current_user"}:
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAdminOrSuperAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user
        qs = super().get_queryset()

        # Superadmin administra todos los usuarios
        if user.rol.nombre == "SuperAdmin":
            return qs

        # Admin no puede gestionar superadmins ni otros admins
        if user.rol.nombre == "Admin":
            return qs.exclude(rol__nombre__in=["SuperAdmin", "Admin"])

        return qs.none()

    @action(detail=False, methods=["get"], url_path="me")
    def get_current_user(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="register")
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "user": UsuarioSerializer(user).data,
                "message": "Usuario registrado exitosamente",
            },
            status=status.HTTP_201_CREATED,
        )


class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsSuperAdmin]

    @action(detail=False, methods=["get"], url_path="list-roles")
    def list_roles(self, request):
        roles = self.get_queryset()
        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data)
