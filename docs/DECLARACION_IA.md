# Declaración de uso de IA generativa

**SI3003, EAFIT · Proyecto 3.5 · Grupo Jueves**
**Jhon Jairo Pulgarin, Yesid Hurtado y Frank López**
Fecha de revisión: 12 de noviembre de 2026. Códigos institucionales pendientes de completar si se requieren.

| Herramienta | Propósito | Alcance |
|---|---|---|
| Claude (Anthropic), según la declaración previa del repositorio | Andamiaje inicial, borradores de módulos, pruebas y documentación | El equipo debe confirmar el uso histórico exacto |
| Codex (OpenAI) | Revisión de la guía y código; detección/corrección de filtros, temporalidad, evaluación y configuración; preparación de ejecución en Colab y documentación | Cambios de esta revisión y pruebas pequeñas; no se ejecutaron experimentos reales de entrenamiento en el PC |
| NVIDIA NIM, nvidia/nemotron-3.5-lightning-30b-a3b | LLM remoto del agente con llamadas a herramientas | Evaluación original de doce preguntas ejecutada por el equipo en Colab; reevaluación remota autorizada explícitamente, con control de citas y registro separado |

**Actividades verificadas en esta sesión:** el equipo ejecutó el pipeline en Colab y recuperó el ZIP con datos, modelo y evaluaciones. La revisión Codex auditó esos resultados, añadió controles de citas, reevaluó el agente con autorización y preparó el informe de cuatro páginas. Quedan por confirmar la revisión de sensores, la demo interactiva y la comprensión por cada integrante. El reparto individual y las actividades efectivamente realizadas deben documentarse por los integrantes antes de entregar; esta declaración no certifica trabajo aún no ejecutado.

**Comprensión pendiente de confirmación por cada integrante:** eliminación de variables y CPT, suavizado, objetivo heurístico y split temporal, restricciones y heurísticas del CSP, recuperación documental, tool calling, significado de métricas y limitaciones. No se afirma que el equipo ya haya revisado o comprendido todo el código.

Las notas del corpus y los jornales/ventanas del CSP son aproximaciones exploratorias, no parámetros validados por un agrónomo. Las publicaciones originales tienen atribución en corpus/FUENTES.md. No se incluyen datos sintéticos como evidencia de desempeño real, ni se inventan resultados para llenar el informe. El uso de IA está declarado; la responsabilidad de verificar y comprender la entrega es del equipo.
