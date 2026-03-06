# Revisión técnica backend POS + facturación electrónica

## Resultado general

El backend tiene una base funcional para **POS** (ventas, detalle, inventario, caja y pagos), pero la capa de **facturación electrónica** está implementada solo como simulación y no cumple todavía un flujo tributario real.

## Validaciones y correcciones aplicadas

1. **Factura simulada asociada correctamente a venta**
   - Se habilitó `venta_id` en el serializer para que la API pueda crear facturas vinculadas a una venta.
   - Se agregó validación para evitar más de una factura simulada por la misma venta.

2. **Control de sobrepago en ventas**
   - Se añadió validación en pagos para impedir registrar montos que superen `total_neto` de la venta.

3. **Ajuste menor en endpoint de generación de factura**
   - Se eliminó variable no usada al guardar factura (`factura = serializer.save()`), manteniendo respuesta consistente.

## Cobertura actual POS (sí implementado)

- Gestión de sucursales y puntos de venta.
- Registro de venta con detalle.
- Descuento de stock al vender.
- Validación de caja abierta para operar ventas/anulación.
- Anulación de venta con devolución de stock y movimiento inventario.
- Registro de pagos por método.
- Dashboard básico de ventas y ranking de productos.

## Brechas para facturación electrónica real (pendiente)

Actualmente el proyecto solo maneja `FacturaSimulada`. Para una facturación electrónica real faltan, como mínimo:

- Integración con proveedor/servicio tributario (envío, recepción, eventos).
- Generación de estructura fiscal formal (XML/JSON normativo).
- Identificador fiscal único (ej. CUF/CUFD según normativa local).
- Firma digital y almacenamiento de acuses/códigos de validación.
- Estados fiscales de factura (emitida, observada, anulada, contingencia).
- Reintentos, colas y trazabilidad operativa de envío.

## Recomendación de siguiente fase

1. Crear módulo `facturacion_electronica` separado de `FacturaSimulada`.
2. Definir modelo `FacturaElectronica` con estados y metadatos de validación.
3. Implementar servicio de emisión asincrónica (cola + reintentos).
4. Incorporar pruebas automatizadas de flujo fiscal (unitarias + integración).

## IA para predicción de reposición (implementado)

Se incorporó un endpoint de analítica para apoyar decisiones de reposición:

- Ruta base: `reportes/analitica-ventas/prediccion-reposicion/`
- Parámetros:
  - `sucursal` (requerido)
  - `dias_historial` (opcional, por defecto 30)
  - `dias_prediccion` (opcional, por defecto 14)
- Salida por producto:
  - `promedio_diario`
  - `demanda_predicha`
  - `stock_actual`
  - `sugerido_reponer`
  - `frecuencia_reposicion_dias`

Esto habilita un motor de recomendación inicial basado en ventas recientes para sugerir cuánto reponer y cada cuánto revisar reposición.

## Facturación electrónica real (estado)

La base sigue siendo de factura simulada. Para cerrar completamente la funcionalidad de facturación electrónica aún se requiere:

- Integración formal con el proveedor/servicio fiscal.
- Firma digital y trazabilidad de envío/acuse.
- Estados fiscales completos y contingencia.
- Reintentos automáticos y cola de emisión.
