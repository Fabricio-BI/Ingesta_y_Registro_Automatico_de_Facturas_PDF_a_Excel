# Ingesta y Registro Automático de Facturas PDF a Excel (Anexo Transaccional)

Este proyecto es una solución automatizada de nivel empresarial diseñada para optimizar el proceso de conciliación fiscal mensual. Automatiza la ingesta de facturas PDF, el reconocimiento del proveedor, la extracción estructurada de datos y la validación aritmética, consolidando toda la información en un reporte Excel listo para el Anexo Transaccional.

---

## 🎯 Justificación del Proyecto e Impacto en el Negocio

A fin de cada mes, un analista de conciliación recibe un lote de facturas de proveedores bancarios recurrentes y debe transcribir manualmente al menos 10 campos por factura (RUC, autorizaciones, fechas, montos, IVA). Este proceso manual implica descargar archivos, digitar datos y verificar cuadres aritméticos de forma repetitiva.

### El Impacto de esta Solución (ROI Estimado)

Al automatizar el pipeline de ingesta y validación, transformamos un proceso manual propenso a errores en un flujo de supervisión rápido y controlado:

*   **Ahorro de Tiempo:** Reducción del tiempo de procesamiento mensual de **~2 horas de transcripción manual a menos de 1 minuto** de ejecución automatizada. Proyectado a un año, libera el equivalente a **24 horas laborales** para tareas de análisis de mayor valor.
*   **Eliminación de Errores Humanos:** La validación aritmética integrada (Base Imponible + IVA = Total) detecta e introduce alertas visuales sobre inconsistencias antes de que ingresen al sistema contable final, previniendo multas y auditorías costosas.
*   **Trazabilidad 100% Auditable:** Cada registro en el reporte de salida documenta qué plantilla procesó el documento y si pasó los controles de calidad, ofreciendo un registro auditable del que carecía el proceso manual.

---

## 🧠 Enfoque Arquitectónico: Reglas Deterministas + Fallback de IA

Una de las decisiones clave de ingeniería en este proyecto es su enfoque pragmático y costo-eficiente: **¿Por qué usar reglas en lugar de Inteligencia Artificial para el volumen recurrente?**

| Métrica | Enfoque por Reglas (Este Proyecto) | Enfoque Puro con IA |
| :--- | :--- | :--- |
| **Costo por factura** | **$0.00** (Ejecución local) | Variable y recurrente (Costos de API) |
| **Privacidad de datos** | **100% Local** (La información no sale de la red) | Depende de políticas de terceros |
| **Previsibilidad** | **Determinista** (Mismo entrada = idéntico resultado) | Estocástico (Puede variar entre ejecuciones) |
| **Mantenimiento** | Una plantilla por nuevo banco emisor | Ninguno (pero requiere monitoreo de alucinaciones) |

### El Flujo de Trabajo Híbrido
Para optimizar costos y garantizar robustez, el sistema utiliza un **pipeline híbrido**:
1.  **Conversión Estructurada:** El PDF se convierte a Markdown preservando el formato de tablas (gracias a `MarkItDown`), lo que simplifica enormemente las expresiones regulares.
2.  **Motor de Reglas (100% Gratis):** Intenta extraer los datos utilizando plantillas Regex optimizadas para proveedores conocidos.
3.  **Fallback Inteligente con IA:** Si el proveedor no es reconocido, el sistema activa automáticamente un extractor basado en **Google Gemini** que, bajo un contrato de datos estricto, recupera los campos faltantes sin detener la ejecución.

```
PDF de la Factura
       │
       ▼
[1] Conversión a Markdown (Estructuración de tablas)
       │
       ▼
[2] Motor de Reglas (Regex) ───¿Reconocido?───► [Sí] ──► Extracción por Plantilla ──┐
       │                                                                            │
      [No]                                                                          ▼
       │                                                                  [3] Validador Aritmético
       ▼                                                                   (Base + IVA == Total)
[Fallback con Gemini-3.5-Flash] ────────────────────────────────────────────────────│
                                                                                    ▼
                                                                        [4] Reporte Excel Generado
                                                                        (Filas con error en ROJO)
```

---

## 🛠️ Arquitectura y Tecnologías Demostradas (Para Tech Leads)

Este repositorio ha sido diseñado aplicando buenas prácticas de ingeniería de software y patrones de diseño modernos:

*   **Principio Abierto/Cerrado (SOLID OCP):** El motor de procesamiento (`core/procesamiento.py`) está completamente cerrado a modificación pero abierto a la extensión. Para dar soporte a un nuevo banco, solo se agrega una estructura de datos en `plantillas/plantillas_fct.py` sin tocar el código fuente del sistema.
*   **Diseño Guiado por Contratos:** El sistema define un esquema rígido de datos (`CAMPOS_FACTURA` en `plantillas/esquema.py`). El extractor de IA consume este esquema dinámicamente para estructurar sus outputs en formato JSON, garantizando consistencia.
*   **Programación Defensiva:** El módulo `core/validador.py` aísla los errores de digitación y fallos de formato, previniendo interrupciones inesperadas del programa (*crashes*) y asegurando la continuidad del procesamiento de lotes grandes.

### Estructura de Archivos del Proyecto

```
├── main.py                     # Orquestador principal del pipeline
├── explorar_factura.py         # Utilidad CLI para analizar el Markdown de nuevos PDFs
├── procesar_conciliacion.bat   # Script ejecutable de doble clic para Windows (UX Contable)
├── core/
│   ├── procesamiento.py        # Conversor de PDF a MD y despachador de plantillas
│   ├── validador.py            # Validador de completitud y coherencia de montos
│   ├── extractor_ia.py         # Fallback inteligente con Google Gemini API
│   └── exportador_excel.py     # Generador de reportes visuales con openpyxl
├── plantillas/
│   ├── esquema.py              # Definición del contrato de datos y clases base
│   ├── plantillas_fct.py       # Expresiones regulares para cada banco conocido
│   └── registro.py             # Registro centralizado de plantillas activas
├── facturas_pdf/               # Carpeta de entrada para los PDFs mensuales
└── salida/                     # Carpeta de salida del reporte Excel final
```

---

## 📊 Vista Previa del Reporte de Salida (Excel)

Cuando el proceso finaliza, genera un libro de Excel formateado. Las facturas que no pasan la validación aritmética se marcan en **Rojo Claro** indicando el motivo para que el analista realice una **revisión por excepción**:

| Proveedor | Número Factura | Fecha Emisión | Base Imponible | Monto IVA | Total | Plantilla Usada | Estado | Errores |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| Banco Cordillera | 001-002-0000451 | 15/10/2025 | 100.00 | 15.00 | 115.00 | `banco_cordillera` | **Válida** | |
| Tarjeta Cumbre Zenith | 005-010-0000897 | 20/10/2025 | 50.00 | 7.50 | 57.50 | `tarjeta_cumbre_zenith` | **Válida** | |
| <font color="red">Proveedor Desconocido</font> | 002-001-0000123 | 21/10/2025 | 80.00 | 10.00 | **120.00** | `ia_gemini` | <font color="red">**Revisión Manual**</font> | <font color="red">Inconsistencia aritmética: 80.00 + 10.00 != 120.00</font> |

---

## 🚀 Guía de Uso Rápido

### Requisitos Previos
1. Python 3.10 o superior instalado.
2. Instalar las dependencias del proyecto:
   ```bash
   pip install -r requirements.txt
   ```
3. *(Opcional)* Si deseas habilitar el fallback de IA, configura tu variable de entorno:
   ```bash
   # En Windows (CMD)
   set GEMINI_API_KEY=tu_api_key_aquí
   # En Linux/macOS
   export GEMINI_API_KEY="tu_api_key_aquí"
   ```

### Instrucciones de Ejecución
1.  Coloca las facturas PDF del mes dentro de la carpeta `facturas_pdf/`.
2.  Ejecuta el programa:
    *   **En Windows:** Haz doble clic sobre el archivo `procesar_conciliacion.bat`.
    *   **Desde Consola:** Corre `python main.py`.
3.  Retira el reporte resultante desde `salida/facturas_extraidas.xlsx` y revisa únicamente las filas marcadas en rojo.

---

## 🛠️ Próximos Pasos (Roadmap de Producción)

Para escalar esta herramienta local a una solución SaaS o un microservicio en la nube, se tiene contemplado:

1.  **Ingesta Automática:** Integrar un conector IMAP para descargar facturas directamente desde un correo dedicado (`facturas@empresa.com`).
2.  **Pruebas de Regresión (`pytest`):** Automatizar pruebas unitarias sobre textos Markdown de prueba para garantizar que los ajustes en las expresiones de Regex no rompan extracciones anteriores.
3.  **Dockerización:** Empaquetar el servicio en un contenedor Docker para despliegues portables y robustos en AWS ECS o Google Cloud Run.
4.  **Monitoreo con Logs:** Reemplazar las salidas de consola (`print`) por el módulo nativo de `logging` para una auditoría avanzada en servidores.
