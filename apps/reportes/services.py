# apps/reportes/services.py
from decimal import Decimal, ROUND_HALF_UP


def proyectar_reposicion_por_producto(*, cantidad_vendida, dias_historial, dias_prediccion, stock_actual):
    """
    Proyección simple de reposición basada en promedio diario de ventas.
    """
    if dias_historial <= 0:
        raise ValueError("dias_historial debe ser mayor a cero")
    if dias_prediccion <= 0:
        raise ValueError("dias_prediccion debe ser mayor a cero")

    cantidad_vendida = Decimal(cantidad_vendida or 0)
    stock_actual = Decimal(stock_actual or 0)

    promedio_diario = (cantidad_vendida / Decimal(dias_historial)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    demanda_predicha = (promedio_diario * Decimal(dias_prediccion)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    sugerido_reponer = demanda_predicha - stock_actual
    if sugerido_reponer < 0:
        sugerido_reponer = Decimal("0.00")

    return {
        "promedio_diario": promedio_diario,
        "demanda_predicha": demanda_predicha,
        "sugerido_reponer": sugerido_reponer.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
    }
