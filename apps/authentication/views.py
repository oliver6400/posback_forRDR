# apps/authentication/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from apps.usuarios.serializers import UsuarioSerializer

@api_view(['POST'])
@permission_classes([AllowAny])  # Permitir acceso sin autenticación
def login(request):
    """
    Endpoint para iniciar sesión
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'message': 'Username y password son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Intentar autenticar usuario
    user = authenticate(username=username, password=password)
    
    if user:
        if not user.is_active:
            return Response({
                'message': 'Usuario inactivo'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Crear o obtener token
        token, created = Token.objects.get_or_create(user=user)
        
        # Serializar datos del usuario
        serializer = UsuarioSerializer(user)
        
        return Response({
            'user': serializer.data,
            'auth': {
                'access_token': token.key,
                'token_type': 'Bearer',
                'expires_in': 3600
            },
            'message': 'Login exitoso'
        }, status=status.HTTP_200_OK)
    
    else:
        return Response({
            'message': 'Credenciales inválidas'
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
def logout(request):
    """
    Endpoint para cerrar sesión
    """
    try:
        # Obtener y eliminar el token del usuario
        token = Token.objects.get(user=request.user)
        token.delete()
        return Response({
            'message': 'Logout exitoso'
        }, status=status.HTTP_200_OK)
    except Token.DoesNotExist:
        return Response({
            'message': 'Token no encontrado'
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def verify_token(request):
    """
    Endpoint para verificar si el token es válido
    """
    if request.user.is_authenticated:
        serializer = UsuarioSerializer(request.user)
        return Response({
            'valid': True,
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    else:
        return Response({
            'valid': False,
            'message': 'Token inválido'
        }, status=status.HTTP_401_UNAUTHORIZED)