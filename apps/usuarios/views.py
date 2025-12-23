# apps/usuarios/views.py
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from .models import Usuario, Rol
from .serializers import UsuarioSerializer, RolSerializer, CustomTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

# ← NUEVO: Vista personalizada para JWT Login
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == 'register':
            permission_classes = [AllowAny]  # Permitir registro sin autenticación
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    # ← NUEVO: Obtener usuario actual autenticado
    @action(detail=False, methods=['get'], url_path='me')
    def get_current_user(self, request):
        """Obtiene los datos del usuario actual autenticado"""
        if request.user.is_authenticated:
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            return Response(
                {"error": "No autenticado"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()

        # Asignar rol si viene en la request
        rol_id = request.data.get('rol_id')
        if rol_id:
            try:
                rol = Rol.objects.get(id=rol_id)
                user.rol = rol
                user.save()
            except Rol.DoesNotExist:
                return Response({"error": "Rol no encontrado"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {
                'user': UsuarioSerializer(user).data,
                'message': 'Usuario registrado exitosamente'
            },
            status=status.HTTP_201_CREATED
        )

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.all()
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'], url_path='list-roles')
    def list_roles(self, request):
        roles = self.get_queryset()
        serializer = self.get_serializer(roles, many=True)
        return Response(serializer.data)