from rest_framework import serializers
from .models import Cliente, Sucursal, Ciudad, PuntoVenta, EstadoVenta

class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = "__all__"

class PuntoVentaSerializer(serializers.ModelSerializer):
    sucursal_nombre = serializers.CharField(source='sucursal.nombre', read_only=True)
    ciudad_nombre = serializers.CharField(source='sucursal.ciudad.nombre', read_only=True)
    class Meta:
        model = PuntoVenta
        fields = "__all__"

class EstadoVentaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoVenta
        fields = "__all__"

class CiudadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ciudad
        fields = "__all__"
