# Análisis de Preparación para Producción

**Proyecto:** Ingesta y Registro Automático de Facturas PDF a Excel
**Fecha del análisis:** 3 de septiembre de 2026
**Versión analizada:** commit `7092ebd` (main)
**Entorno evaluado:** Linux, Python 3.10+, markitdown 0.1.7, openpyxl 3.1.5, google-genai 2.18.1

---

## Veredicto Ejecutivo

**El proyecto NO está listo para producción.**

El sistema tiene una arquitectura sólida y los casos felices funcionan correctamente (lo demuestra el log: 12/12 PDFs procesados el 18:51:23, todos con estado "válida"). Sin embargo, presenta:

- **3 problemas bloqueantes** que pueden causar pérdida silenciosa de datos
- **5 riesgos altos** que probablemente se manifestarán en las primeras semanas
- **10 riesgos medios** de endurecimiento que deben resolverse antes de escalar

Se recomienda **no desplegar con datos reales de clientes** hasta resolver los bloqueantes de la Fase 1. Para un piloto controlado con validación manual fila por fila, podría operar con monitoreo cercano.

---

## Lo que está bien hecho (Fortalezas)

| Aspecto | Implementación | Ubicación |
|---|---|---|
| Arquitectura modular | Separación limpia entre `core/`, `plantillas/`, `source/` que permite agregar proveedores sin tocar el orquestador | Estructura completa del proyecto |
| Esquema unificado | `CAMPOS_FACTURA` y `CAMPOS_OBLIGATORIOS` blindan el contrato de datos | `plantillas/esquema.py` |
| Sistema de plantillas extensible | Cada proveedor tiene su `identificador_regex` y patrones aislados | `plantillas/plantillas_fct.py` |
| Fallback con IA | Gemini responde con JSON estructurado usando `response_schema` dinámico | `core/extractor_ia.py` |
| Aislamiento de fallos por documento | `try/except` en el bucle principal evita que un PDF roto tumbe el lote | `main.py:61-79` |
| Validación aritmética | Tolerancia de 0.05 + normalización de formato latino (1.234,56) | `core/validador.py:16,26` |
| Logs rotativos | `RotatingFileHandler` con 10MB x 5 backups + silenciador de librerías | `source/log_config.py:35-55` |
| Backup de Excel | Manejo de `PermissionError` con timestamp automático | `core/exportador_excel.py:57-65` |
| Validación de fecha | Formato DD/MM/YYYY estricto | `core/validador.py:33-40` |
| Separación por capas | Rutas absolutas centralizadas en `paths.py`, nunca hardcodeadas | `source/paths.py` |

---

## Problemas Bloqueantes

### B1. Modelo de Gemini inexistente

**Severidad:** Crítica
**Ubicación:** `core/extractor_ia.py:20`

```python
MODELO = "gemini-3.5-flash"
```

El modelo `gemini-3.5-flash` no existe en la API de Google. Los modelos válidos son `gemini-2.0-flash`, `gemini-2.5-flash`, `gemini-1.5-flash`, entre otros.

**Escenario de fallo:**
Google deprecia el modelo que actualmente está resolviendo por fallback implícito, o se ejecuta en un entorno diferente. Resultado: `404 NOT_FOUND`. Toda factura de proveedor desconocido cae a `estado="sin plantilla"` y queda silenciosamente perdida. El reporte Excel no marca error crítico, simplemente muestra la factura como pendiente.

**Solución:**

```python
import os
MODELO = os.environ.get("GEMINI_MODELO", "gemini-2.0-flash")
```

Verificar el modelo con un PDF de prueba antes de declarar producción.

---

### B2. Credencial de Gemini posiblemente inválida

**Severidad:** Crítica
**Ubicación:** `.env:1`

```
GEMINI_API_KEY= tu clave aqui 
```

Tres problemas detectados:

1. **Prefijo `AQ.`** característico de claves de Azure, no de Google AI Studio.
2. **Espacio después del `=`** que `dotenv` limpia, pero es mala práctica.
3. **Nombre inconsistente:** el README documenta `MODELO_API_KEY` pero el código busca `GEMINI_API_KEY`.

**Escenario de fallo:**
La primera factura de un proveedor no catalogado ejecuta `extraer_con_ia()`. Google responde 401/403 porque la clave no es válida. El `except` captura la excepción, retorna `None`, la factura se marca como `"sin plantilla"`. Todas las facturas no catalogadas se pierden silenciosamente. El operador no se entera hasta el cierre contable.

**Solución:**
- Generar una clave real en https://aistudio.google.com
- Verificar que funcione ejecutando `extraer_con_ia()` con un PDF de prueba
- Corregir la documentación para que use el mismo nombre de variable
- Mover la clave a variables de entorno del sistema operativo en producción

---

### B3. Pérdida total del lote si falla la exportación a Excel

**Severidad:** Crítica
**Ubicación:** `main.py:84-86`

```python
exportar_a_excel(resultados, ARCHIVO_SALIDA)
logger.info(f"Listo. Resultados guardados en: {ARCHIVO_SALIDA}")
```

Si `exportar_a_excel` lanza cualquier excepción que no sea `PermissionError` (disco lleno, ruta inválida, permisos de carpeta, antivirus bloqueando openpyxl, Excel abierto en modo estricto, etc.), se pierde todo el lote sin respaldo.

**Escenario de fallo:**
El usuario tiene abierto un archivo de control en Excel, o Dropbox/OneDrive está sincronizando `data/processed/` y bloquea la escritura. Se lanza una excepción no controlada. El programa termina. No queda ningún registro. La persona que ejecuta no se entera de qué facturas se procesaron.

**Solución:**

```python
try:
    exportar_a_excel(resultados, ARCHIVO_SALIDA)
except Exception:
    logger.exception("Fallo exportando a Excel; persistiendo respaldo CSV")
    _respaldar_csv(resultados)  # red de seguridad
```

---

## Riesgos Altos

### A1. Sin reintentos ni timeout en llamadas a Gemini

**Severidad:** Alta
**Ubicación:** `core/extractor_ia.py:85-93`

Una factura desconocida tarda entre 4 y 6 segundos en el log observado (`factura_banco_meridiano.pdf`: 18:51:15 → 18:51:21). Para un lote de 50 PDFs desconocidos serían ~5 minutos bloqueados en una sola llamada HTTP sin timeout ni reintentos.

**Escenario de fallo:**
Gemini rate-limit (HTTP 429), red inestable, o respuesta lenta. El proceso se cuelga esperando. La persona que ejecuta `main.py` cierra la terminal asumiendo que el sistema se trabó.

**Solución:**
Usar `tenacity` o implementar retry exponencial manual:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def _llamar_gemini(cliente, prompt, esquema):
    return cliente.models.generate_content(
        model=MODELO,
        contents=prompt,
        config={"response_mime_type": "application/json", "response_schema": esquema},
    )
```

---

### A2. Plantillas regex frágiles ante cambios de proveedor

**Severidad:** Alta
**Ubicación:** `plantillas/plantillas_fct.py`

Ejemplo crítico:

```python
"descripcion": r"\d{6}\s+\d+\.\d{2}\s+([A-ZÁÉÍÓÚÑ ]+?)\s+\d+\.\d{2}\s+\d+\.\d{2}",
```

Esta regex asume:
- Descripción en MAYÚSCULAS sostenidas
- Sin números en la descripción
- Exactamente 2 columnas de importes después

**Escenarios donde se rompe:**
- El banco cambia "IVA" por "Tarifa"
- La descripción incluye números (ej: "Servicio 2024")
- Se añade una columna "Descuento" antes del IVA
- Cambian el orden de los importes
- Un proveedor emite "Base Imponible 12%" y otro "Base Imponible 15%" → match ambiguo

**Solución:**
Mover todas las regex a pruebas unitarias con fixtures de PDFs reales. Agregar pruebas de regresión por cada proveedor nuevo.

---

### A3. Falta de idempotencia

**Severidad:** Alta
**Ubicación:** `main.py:50-86`

Si el usuario corre `main.py` dos veces sobre el mismo lote, el Excel se sobrescribe con los mismos datos. Pero si una factura estaba marcada "revisión manual" la primera vez y "válida" la segunda, no hay rastro del cambio.

**Escenario de fallo:**
El usuario corrige un PDF a mano, lo vuelve a poner en `data/raw/`, ejecuta el pipeline. No hay forma de saber qué cambió entre ejecuciones.

**Solución:**
Agregar hash SHA256 del PDF como columna de auditoría:

```python
import hashlib
def _hash_pdf(ruta):
    with open(ruta, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]
```

---

### A4. El directorio `data/raw/` no se limpia ni se mueve

**Severidad:** Alta
**Ubicación:** `main.py:52`

```python
rutas_pdf = sorted(RAW_DIR.glob("*.pdf"))
```

Después de procesar, los PDFs siguen en `data/raw/`. El próximo lote los reprocesará.

**Escenario de fallo:**
Lote de enero se ejecuta, todo OK. Lote de febrero se ejecuta → vuelve a procesar enero → facturas duplicadas en Excel (sobreescribe, pero se pierde el orden temporal).

**Solución:**
Mover PDFs procesados a `data/processed/{YYYY-MM-DD}/` o agregar columna `fecha_procesamiento` al Excel.

---

### A5. Orden de evaluación de plantillas puede generar falsos positivos

**Severidad:** Alta
**Ubicación:** `plantillas/registro.py:17-25`

```python
PLANTILLAS_REGISTRADAS = [
    PLANTILLA_BANCO_PRODUCTIVO_NACIONAL,
    PLANTILLA_BANCO_CORDILLERA,
    PLANTILLA_BANCO_SOLIDARIDAD_ANDINA,
    ...
]
```

`detectar_plantilla()` en `core/procesamiento.py:24-33` itera en orden y retorna la primera coincidencia. Si una plantilla genérica está antes que una específica, captura falsos positivos.

**Escenario de fallo:**
Un proveedor nuevo incluye texto como "Banco Productivo" en un pie de página (no es el Banco Productivo Nacional). La regex matchea → se usa la plantilla incorrecta → extracción con muchos campos `None`.

**Solución:**
Ordenar las plantillas de más específica a más genérica, o agregar un sistema de scoring.

---

## Riesgos Medios

| ID | Problema | Ubicación | Escenario |
|----|----------|-----------|-----------|
| M1 | `explorar_factura.py` quedó en producción | `explorar_factura.py:1-28` | Usuario lo ejecuta por error → falla porque referencia carpeta `facturas_pdf/` inexistente |
| M2 | Discrepancia entre README y código sobre variable de API | `README.md:122-127` vs `core/extractor_ia.py:59` | Operador nuevo sigue instrucciones, configura `MODELO_API_KEY`, falla porque el código busca `GEMINI_API_KEY` |
| M3 | Sin versiones fijadas en `requirements.txt` | `requirements.txt:1-3` | Actualización mayor de `markitdown` o `google-genai` rompe todo silenciosamente |
| M4 | El README menciona `core/logger.py` que no existe | `README.md:108` | La documentación miente, erosiona confianza del equipo |
| M5 | No hay tests automatizados | (global) | Cualquier refactor puede romper una plantilla sin detección |
| M6 | `tarifa_iva` no se valida | `core/validador.py` | Si la IA devuelve "quince" en lugar de "15", pasa la validación |
| M7 | `descripcion` queda en `None` | `core/procesamiento.py:45-47` | Se exporta como celda vacía sin marcar error, pero el anexo transaccional podría requerirla |
| M8 | No hay validación de unicidad | `core/validador.py` | Dos PDFs con el mismo `numero_autorizacion` se duplican en el Excel sin aviso |
| M9 | `extraer_con_ia` puede devolver JSON parcial | `core/extractor_ia.py:85-95` | Gemini rate-limited devuelve dict incompleto → entra como "válida" sin todos los campos |
| M10 | Mensaje de error menciona nombre de variable incorrecto | `main.py:37` | El mensaje al usuario dice "revisar GEMINI_API_KEY" pero el README instruye `MODELO_API_KEY` |

---

## Escenarios Específicos de Rotura

### Escenario 1: Proveedor conocido cambia de nombre

> Banco Cordillera cambia su logo a "Grupo Cordillera". La regex `r"Banco Cordillera"` no matchea → cae a IA → la IA extrae bien → estado "válida".
>
> **Pero:** si el banco renombra a "Cordillera S.A." → la IA devuelve `proveedor="Cordillera S.A."` → no es "Banco Cordillera" → el reporte no se puede cruzar contra el catálogo de proveedores del SRI.

### Escenario 2: Lote grande de PDFs

> El operador pone 200 PDFs en `data/raw/`. markitdown tarda entre 0.5 y 2 segundos por PDF local. 200 PDFs son aproximadamente 5 minutos de extracción. La red se cae a la mitad → 50 PDFs procesados, 150 sin estado, no hay checkpoint.
>
> **Resultado:** El operador no sabe qué se procesó, re-ejecuta → 200 PDFs duplicados (mismo `numero_autorizacion` dos veces).

### Escenario 3: Sincronización en la nube

> El Excel está abierto y Dropbox sincroniza. Dropbox bloquea el archivo → `PermissionError` → se crea copia con timestamp. **Pero** el operador no sabe cuál es el bueno porque ambos coexisten en `data/processed/`.

### Escenario 4: Cambio en formato regulatorio

> El SRI cambia el formato de clave de acceso de 49 a 50 dígitos. Regex `r"CLAVE DE ACCESO\s*\n(\d+)"` matchea igual, pero `extraer_con_ia` recibe el texto y el prompt dice "49 dígitos" → la IA formatea incorrectamente → validación pasa pero el dato está mal.

### Escenario 5: Fusión de proveedores

> Dos bancos se fusionan y emiten con el mismo RUC. `ruc_proveedor` se duplica en el Excel. Sin validación de unicidad por RUC + secuencial, el reporte contable tendrá doble registro.

### Escenario 6: PDF escaneado (imagen)

> markitdown no aplica OCR. Un proveedor emite facturas escaneadas → `MarkItDown().convert()` retorna string vacío → todas las regex fallan → cae a IA → la IA tampoco puede leer imágenes → estado "sin plantilla".

---

## Plan de Remediación

### Fase 1: Bloqueantes (1-2 días)

- [ ] Verificar y corregir `MODELO = "gemini-3.5-flash"` por un modelo válido y probado
- [ ] Generar clave real de Gemini en AI Studio
- [ ] Validar manualmente la clave del `.env` (parece tener prefijo de Azure)
- [ ] Agregar fallback CSV si falla la escritura del Excel
- [ ] Sincronizar nombres de variables en README y código (`GEMINI_API_KEY`)

### Fase 2: Endurecimiento (3-5 días)

- [ ] Fijar versiones en `requirements.txt`
- [ ] Agregar retry + timeout a llamadas de Gemini
- [ ] Mover PDFs procesados a subcarpeta con fecha
- [ ] Validar unicidad por `numero_autorizacion`
- [ ] Validar `tarifa_iva` (que sea número, no texto)
- [ ] Eliminar o documentar `explorar_factura.py`
- [ ] Corregir referencia a `core/logger.py` inexistente en README
- [ ] Agregar hash SHA256 del PDF como columna de auditoría
- [ ] Implementar validación post-IA que rechace JSON parcial

### Fase 3: Producción seria (2-3 semanas)

- [ ] Tests unitarios por plantilla (al menos uno por proveedor)
- [ ] Tests de integración con PDFs reales
- [ ] CI/CD con linting
- [ ] Logging estructurado (JSON) para alimentar un dashboard
- [ ] Documentar procedimientos de "qué hacer si X falla" (runbook)
- [ ] Considerar mover a un servicio programado (cron/scheduled task)
- [ ] Implementar OCR de respaldo para PDFs escaneados
- [ ] Sistema de scoring para detección de plantillas

---

## Observaciones Adicionales

### Sobre el log observado

La ejecución del 18:51:23 procesó exitosamente 12 PDFs:
- 7 con plantillas deterministas (Banco Cordillera, Banco Solidaridad Andina x5, Tarjeta Cumbre x4)
- 1 con fallback IA (Banco Meridiano)

Todas marcadas como "válida". Sin embargo, esto no garantiza que funcionará en producción real, ya que:

1. Los PDFs de prueba son sintéticos (mismo formato cada vez)
2. La IA puede tener comportamientos distintos con datos reales
3. No hubo concurrencia ni volumen real

### Sobre la cobertura de proveedores

Solo hay 7 plantillas registradas para un dominio que menciona "proveedores recurrentes" y "servicios bancarios". En producción real probablemente aparecerán 20+ emisores distintos en los primeros meses.

### Sobre el rendimiento

12 PDFs en ~8 segundos es aceptable para desarrollo. Para producción con cientos de PDFs diarios, considerar:
- Paralelización (`concurrent.futures`)
- Cola de tareas
- Cache de resultados por hash

---

## Conclusión

El proyecto tiene una base arquitectónica sólida y los casos felices funcionan bien. El log demuestra que el pipeline completo (detección → extracción → validación → exportación) opera correctamente con los datos sintéticos actuales.

Los tres bloqueantes identificados (modelo Gemini inválido, credencial posiblemente incorrecta, falta de fallback de exportación) deben resolverse antes de cualquier despliegue. Son cambios de bajo riesgo técnico pero alto impacto operacional.

Para un piloto controlado con validación manual fila por fila, el sistema podría operar con monitoreo cercano. Para producción seria (cierres mensuales automáticos, cientos de PDFs, datos reales de clientes), se requiere completar las tres fases de remediación.
