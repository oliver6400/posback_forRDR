from decimal import Decimal

from django.test import SimpleTestCase

from apps.reportes.services import proyectar_reposicion_por_producto


class ReposicionProjectionServiceTests(SimpleTestCase):
    def test_proyeccion_calcula_promedio_demanda_y_reposicion(self):
        data = proyectar_reposicion_por_producto(
            cantidad_vendida=Decimal("120"),
            dias_historial=30,
            dias_prediccion=15,
            stock_actual=Decimal("20"),
        )

        self.assertEqual(data["promedio_diario"], Decimal("4.00"))
        self.assertEqual(data["demanda_predicha"], Decimal("60.00"))
        self.assertEqual(data["sugerido_reponer"], Decimal("40.00"))

    def test_proyeccion_no_devuelve_reposicion_negativa(self):
        data = proyectar_reposicion_por_producto(
            cantidad_vendida=Decimal("10"),
            dias_historial=30,
            dias_prediccion=10,
            stock_actual=Decimal("100"),
        )

        self.assertEqual(data["sugerido_reponer"], Decimal("0.00"))

    def test_valida_dias_positivos(self):
        with self.assertRaises(ValueError):
            proyectar_reposicion_por_producto(
                cantidad_vendida=Decimal("10"),
                dias_historial=0,
                dias_prediccion=10,
                stock_actual=Decimal("1"),
            )
