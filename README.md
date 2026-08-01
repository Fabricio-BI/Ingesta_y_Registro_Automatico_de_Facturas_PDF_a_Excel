# Ingesta y Registro Automático de Facturas PDF a Excel

## Aviso sobre los datos de este repositorio

Todas las facturas de muestra (`facturas_pdf/`), nombres de proveedores,
RUCs, clientes y montos usados en este proyecto son **ficticios**,
creados únicamente con fines de desarrollo y demostración. Ningún dato
corresponde a una empresa, persona o transacción real. La estructura
visual de los documentos (RIDE) sí sigue el estándar público definido
por el SRI de Ecuador, pero el contenido es inventado.

## El problema real

A fin de cada mes, un analista de conciliación recibe un lote de facturas
de proveedores bancarios recurrentes (comisiones de mantenimiento,
transferencias, tarjetas de crédito, etc.) y necesita registrar sus datos
en un Anexo Transaccional para fines fiscales y contables.

Este proceso, hecho a mano, implica:

- Descargar cada factura individualmente.
- Leer y transcribir 10 datos por factura (RUC, número de factura,
  fechas, montos, IVA, etc.).
- Revisar que los montos cuadren correctamente.

En un caso real de referencia: **12-26 facturas por mes, de 5-7
proveedores, concentradas en su mayoría en 2-3 bancos**, con un tiempo
estimado de **2 horas mensuales** y al menos un error de digitación
identificado en el proceso manual.

## La propuesta

Un sistema que automatiza las 4 etapas del proceso — lectura del PDF,
reconocimiento del proveedor, extracción de los 10 campos, y validación
aritmética — dejando al analista únicamente la revisión de los casos que
el propio sistema marca como dudosos, en vez de procesar cada factura
de punta a punta a mano.

### Por qué reglas y no IA desde el principio

Con solo **5 plantillas** (una por proveedor recurrente) se cubre el
100% del volumen mensual típico. Para este volumen y esta variedad, un
sistema de reglas (regex) es más económico y más confiable que una
solución basada en IA:

| | Reglas (este proyecto) | IA |
|---|---|---|
| Costo por factura procesada | $0 | Variable, recurrente |
| Privacidad de datos | Todo local, nada sale de la máquina | Depende del proveedor de IA |
| Previsibilidad | Determinístico -- mismo resultado siempre | Puede variar entre corridas |
| Mantenimiento | Una plantilla nueva por proveedor nuevo | Ninguno, generaliza solo |

Para un proceso con proveedores fijos y conocidos, como es este caso, el
costo de mantenimiento de las reglas es mínimo (una plantilla se escribe
una sola vez y sirve para siempre), mientras que un enfoque de IA
generaría un costo recurrente para resolver algo que las reglas ya
resuelven gratis.

## El impacto de adoptarlo

- **Tiempo:** de ~2 horas mensuales de trabajo manual a minutos de
  supervisión. Proyectado a un año, del orden de 24 horas de trabajo
  liberadas para tareas de mayor valor.
- **Errores:** la validación aritmética automática (Base Imponible +
  IVA = Total) detecta inconsistencias antes de que lleguen al Anexo
  final, en vez de descubrirlas después en una auditoría o cruce
  contable.
- **Trazabilidad:** cada fila del Excel resultante indica qué plantilla
  la procesó y si pasó o no la validación -- un registro auditable de
  cómo se generó cada dato, algo que el proceso manual no ofrecía.
- **Escalabilidad controlada:** agregar un proveedor nuevo no requiere
  tocar el motor del sistema, solo sumar una plantilla (ver más abajo).

### Por qué Markitdown como paso de conversión

El sistema no lee el PDF directamente -- primero lo convierte a texto
Markdown (librería Markitdown). Esto tiene dos beneficios, uno inmediato
y uno a futuro:

- **Hoy:** Markitdown preserva las tablas del documento original como
  filas `| col | col |`, lo que hace que los patrones de extracción
  (regex) sean mucho más simples y confiables que si se buscara sobre
  texto plano sin estructura.
- **A futuro:** si se conecta un extractor de IA como respaldo (ver
  sección siguiente), puede reutilizar este mismo texto ya convertido
  en vez de enviarle el PDF como imagen al modelo. Esto evita el uso de
  tokens de visión (sustancialmente más costosos por página que texto
  plano), y le entrega al modelo una estructura ya resuelta en vez de
  pedirle que interprete el layout visual del documento.

## ¿Está listo para incorporar IA si el volumen o la variedad de proveedores crece?

**La arquitectura sí está preparada; falta el código específico del
extractor de IA en sí.** Esto es intencional: no tiene sentido pagar
por una capacidad que hoy no se necesita, pero sí conviene que el
sistema esté diseñado para no requerir un rediseño el día que se
necesite.

Concretamente:

- Existe un **contrato de datos fijo** (`CAMPOS_FACTURA`, en
  `plantillas/esquema.py`) que cualquier extractor -- por reglas o por
  IA -- debe respetar. Un extractor de IA que devuelva esos mismos 10
  campos se integraría sin modificar el validador ni el exportador.
- Existe un **punto de enganche ya identificado** en `main.py`: cuando
  ninguna plantilla reconoce una factura, hoy se marca como "sin
  plantilla"; ahí es donde, en el futuro, se llamaría al extractor de
  IA como respaldo, antes de dar la factura por perdida.
- El **validador aritmético es agnóstico al origen del dato** -- una
  factura resuelta por IA pasaría exactamente por el mismo control de
  calidad que una resuelta por regex.

Lo que faltaría desarrollar, si llega el momento:

1. Un módulo nuevo (`core/extractor_ia.py`) que reciba el texto de la
   factura y devuelva un diccionario con los mismos 10 campos.
2. Una modificación puntual en `main.py` para llamar a ese módulo
   cuando `detectar_plantilla` no reconozca ningún proveedor.
3. Definir cuándo activarlo: se recomienda hacerlo cuantitativamente --
   por ejemplo, si el porcentaje de facturas "sin plantilla" supera un
   umbral (10-15% del volumen mensual) durante 2-3 meses seguidos, es
   señal de que conviene invertir en esa pieza.

## Cómo se ve el proceso, paso a paso

```
PDF de la factura
   |
   v
[1] Conversión a Markdown (Markitdown)
   |
   v
[2] Reconocimiento del proveedor (5 plantillas registradas)
   |
   v
[3] Extracción de los 10 campos (regex por proveedor)
   |
   v
[4] Validación (completitud + Base Imponible + IVA = Total)
   |
   +-- Válida --------------------> Excel (fila normal)
   |
   +-- Inconsistente / incompleta -> Excel (fila marcada en rojo)
```

## Estructura del proyecto

```
Ingesta_y_Registro_Automatico_de_Facturas_PDF_a_Excel/
├── main.py                        Orquestador del flujo completo
├── explorar_factura.py            Inspecciona el Markdown de una factura
├── procesar_conciliacion.bat      Ejecución con doble clic (Windows)
├── requirements.txt
├── core/
│   ├── procesamiento.py           Conversión + detección + extracción
│   ├── validador.py               Completitud + coherencia aritmética
│   └── exportador_excel.py        Generación del Excel final
├── plantillas/
│   ├── esquema.py                 Contrato de los 10 campos
│   ├── plantillas_bancos.py       Las 5 plantillas de proveedores
│   └── registro.py                Lista de plantillas activas
├── facturas_pdf/                  Carpeta de entrada
└── salida/                        Carpeta de salida (Excel generado)
```

## Proveedores cubiertos hoy

| Proveedor | Plantilla |
|---|---|
| Banco Productivo Nacional | `banco_productivo_nacional` |
| Banco Cordillera | `banco_cordillera` |
| Banco Solidaridad Andina | `banco_solidaridad_andina` |
| Tarjeta Cumbre Zenith / Prisma / Nortis / Elite Pay | `tarjeta_cumbre_*` (patrones compartidos) |

## Cómo usarlo

1. Colocar los PDFs de las facturas del mes en `facturas_pdf/`.
2. Doble clic en `procesar_conciliacion.bat` (o `python main.py` desde
   la terminal, con el entorno virtual activado).
3. Retirar el Excel de `salida/facturas_extraidas.xlsx`.
4. Revisar únicamente las filas marcadas en rojo, si las hay.

## Cómo agregar un proveedor nuevo

1. Colocar una factura de muestra en `facturas_pdf/` y correr
   `explorar_factura.py` para ver su texto real.
2. Agregar una `Plantilla` nueva en `plantillas/plantillas_bancos.py`.
3. Registrarla en `plantillas/registro.py`.
4. No es necesario modificar `core/` ni `main.py`.
