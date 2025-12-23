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
        if ArqueoCaja.objects.filter(usuario_apertura=usuario, punto_venta=punto_venta, estado="Abierto").exists():
            raise serializers.ValidationError("Ya tienes una caja abierta en este punto de venta.")

        return data

    def create(self, validated_data):
        validated_data["usuario_apertura"] = self.context["request"].user
        return ArqueoCaja.objects.create(**validated_data)

    def close_caja(self, instance, monto_final_real):
        """Calcular totales y cerrar la caja."""
        usuario = self.context["request"].user

        # Calcular totales de ventas en la caja
        ventas = Venta.objects.filter(
            punto_venta=instance.punto_venta,
            usuario=instance.usuario_apertura,
            fecha_hora__gte=instance.fecha_apertura,
            estado_venta__nombre="Pagada"
        )

        monto_final_sistema = sum(v.total_neto for v in ventas)
        diferencia = (monto_final_sistema) - (instance.monto_inicial + monto_final_real)

        instance.monto_final_real = monto_final_real
        instance.monto_final_sistema = monto_final_sistema
        instance.diferencia = diferencia
        instance.usuario_cierre = usuario
        instance.fecha_cierre = timezone.now()
        instance.estado = "CERRADA"
        instance.save()

        return instance
        