from rest_framework import serializers
from .models import LogAuditoria, ArqueoCaja
from apps.ventas.models import Venta
from django.utils import timezone

class LogAuditoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogAuditoria
        fields = "__all__"

class ArqueoCajaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArqueoCaja
        fields = "__all__"
        read_only_fields = ("usuario_apertura", "usuario_cierre", "fecha_apertura", "fecha_cierre", "estado")

    def validate(self, data):
        usuario = self.context["request"].user
        punto_venta = data.get("punto_venta")

        # Validar que el usuario no tenga otra caja abierta
        if ArqueoCaja.objects.filter(
            usuario_apertura=usuario,
            estado="ABIERTA"
        ).exists():
            raise serializers.ValidationError(
                "Ya tienes una caja abierta, debes cerrarla primero."
            )
        return data

    def create(self, validated_data):
        validated_data["usuario_apertura"] = self.context["request"].user
        return ArqueoCaja.objects.create(**validated_data)

        