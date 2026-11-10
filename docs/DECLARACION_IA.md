# Declaración de uso de IA generativa (SI3003 – Proyecto final)

**Equipo:** [COMPLETAR nombres y códigos]  ·  **Fecha:** [COMPLETAR]

| Herramienta | Propósito | Dónde se usó |
|---|---|---|
| Claude (Anthropic) | Generación del andamiaje inicial del repositorio: estructura de módulos, primer borrador del código (red bayesiana, CSP, RAG, agente, dashboard), pruebas, README y borrador del informe | Todo el repositorio |
| [LLM del agente: p. ej. Llama 3.3 70B vía Groq] | Componente de la solución (el agente responde con él en tiempo de ejecución) | `cafe/agent.py` |

**Trabajo propio del equipo** (ajustar con honestidad): [COMPLETAR: descarga y verificación de datos, decisiones de umbrales, revisión línea a línea del código, ejecución de experimentos, análisis de resultados, redacción final, corpus de Cenicafé añadido].

**Verificación y comprensión:** el equipo revisó, ejecutó y modificó el código generado, y puede explicar la inferencia por eliminación de variables, la búsqueda del CSP (MRV + forward checking), la definición del indicador de riesgo, el protocolo de evaluación y las limitaciones. [COMPLETAR/CONFIRMAR]

**Límites de la IA:** los textos del corpus `notas_*.md` y los parámetros del catálogo de labores (jornales, ventanas de lluvia) son aproximaciones que deben contrastarse con fuentes oficiales; la IA generativa pudo cometer errores y no sustituye la validación del equipo.
