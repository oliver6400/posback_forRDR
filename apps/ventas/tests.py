from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.inventario.models import Producto
from apps.negocio.models import Ciudad, EstadoVenta, PuntoVenta, Sucursal
from apps.reportes.models import ArqueoCaja
from apps.usuarios.models import Rol, Usuario
from apps.ventas.models import DetalleVenta, Venta


class VentaDashboardTests(APITestCase):
    def setUp(self):
        self.rol = Rol.objects.create(nombre="Cajero")
        self.user = Usuario.objects.create_user(
            username="cajero",
            ci="123456",
            email="cajero@example.com",
            nombre="Caja",
            apellido="Uno",
            fecha_nacimiento="1990-01-01",
            password="test12345",
            rol=self.rol,
        )
        self.client.force_authenticate(user=self.user)

        self.ciudad = Ciudad.objects.create(nombre="La Paz")
        self.sucursal = Sucursal.objects.create(
            ciudad=self.ciudad,
            nombre="Central",
            direccion="Av. Principal",
        )
        self.punto_venta = PuntoVenta.objects.create(sucursal=self.sucursal, nombre="Caja 1")

        self.estado_pagada = EstadoVenta.objects.create(nombre="PAGADA")
        self.estado_anulada = EstadoVenta.objects.create(nombre="ANULADA")

        ArqueoCaja.objects.create(
            sucursal=self.sucursal,
            punto_venta=self.punto_venta,
            usuario_apertura=self.user,
            monto_inicial=Decimal("100.00"),
            estado="ABIERTA",
        )

    def test_dashboard_sin_fechas_devuelve_ranking(self):
        producto = Producto.objects.create(
            codigo_barras="111",
            codigo="P-111",
            nombre="Teclado",
            unidad="UND",
            precio_venta=Decimal("100.00"),
            costo_promedio=Decimal("70.00"),
        )
        venta = Venta.objects.create(
            sucursal=self.sucursal,
            punto_venta=self.punto_venta,
            usuario=self.user,
            estado_venta=self.estado_pagada,
            total_bruto=Decimal("200.00"),
            total_descuento=Decimal("0.00"),
            total_neto=Decimal("200.00"),
        )
        DetalleVenta.objects.create(
            venta=venta,
            producto=producto,
            cantidad=2,
            precio_unitario=Decimal("100.00"),
            descuento=Decimal("0.00"),
        )

        url = reverse("ventas-dashboard")
        response = self.client.get(url, {"sucursal": self.sucursal.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["cantidad_ventas"], 1)
        self.assertEqual(str(response.data["total_vendido"]), "200")
        self.assertEqual(len(response.data["ranking_productos"]), 1)
        self.assertEqual(response.data["ranking_productos"][0]["producto__nombre"], "Teclado")

    def test_dashboard_fecha_invalida_devuelve_400(self):
        url = reverse("ventas-dashboard")
        response = self.client.get(url, {"sucursal": self.sucursal.id, "fecha": "2026-99-40"})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Fecha inválida", response.data["detail"])
