# Lista de entrega del proyecto

- [x] Código: red bayesiana e inferencia propias, CSP propio, agente LLM, RAG y cuatro herramientas.
- [x] Datos IDEAM identificados y reproducibles, manifiestos y corpus técnico original con fuentes.
- [x] Entrenamiento y métricas reales del modelo frente a tres referencias en Colab.
- [x] Evaluaciones original y revisada del agente, doce preguntas, respuestas y trazas; fallos conservados.
- [x] Auditoría de CSV diarios, sensibilidad conservadora entrenada en Colab y comparación documentada.
- [x] Informe: output/pdf/INFORME.pdf, cuatro páginas.
- [x] Declaración de IA: docs/DECLARACION_IA.md.
- [x] README, dependencias, artefactos de ambas variantes y pruebas.
- [x] Carga programática del dashboard con artefactos reales, seis pestañas.
- [ ] Revisión interactiva por el equipo: mapa, series, calendario, parámetros y conversación con NVIDIA.
- [ ] Cada integrante revisa y confirma aportes, uso histórico de IA y comprensión del código; agregar códigos si se requieren.
- [ ] Publicar/actualizar el repositorio GitHub con los archivos de entrega. No publicar .env ni claves.
- [ ] Cada integrante envía el repositorio al correo y con el asunto indicados en la guía EAFIT.
- [ ] Opcional: video de respaldo de tres-cuatro minutos.

La fecha máxima según la guía es el viernes 13 de noviembre de 2026 a las 6:00 p. m., hora de Colombia. Esta revisión no publicó el repositorio ni envió correos.

La evidencia documenta un MVP exploratorio con limitaciones. No certifica sensores meteorológicos ni predice incidencia de roya en campo. Las dos preguntas de herramienta fallidas en la revisión del agente y los casos de citas sustituidas están reportados; no se ocultan para declarar éxito total.

La demo conserva el experimento original como referencia con advertencias. La variante conservadora se incluye como análisis de sensibilidad, no como datos certificados ni como un modelo superior. Ambos modelos se entrenaron en Colab.

Para iniciar la demo, desde la raíz del proyecto:

~~~powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
~~~

El paquete artifacts/cafe_entrega.zip incluye código, evidencias, PDF y las dos variantes. No incluye la API key ni los CSV diarios grandes; los manifiestos y las instrucciones permiten reproducir su obtención.

En la web cada visitante ingresa su clave NVIDIA en la barra lateral y puede olvidarla. Sin clave, el chat opera en modo demostración; para verificar LLM real hay que ingresar una clave válida. La web no usa automáticamente LLM_API_KEY del servidor. Pruebas actuales: 49 pasaron, incluido aislamiento de claves entre sesiones.
