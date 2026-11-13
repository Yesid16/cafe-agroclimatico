# Asistente agroclimático para café
**SI3003 - EAFIT - Grupo Jueves - Proyecto 3.5**
**Jhon Jairo Pulgarin, Yesid Hurtado y Frank López**
Repositorio: https://github.com/Yesid16/cafe-agroclimatico
## 1. Problema y alcance
El asistente integra una red bayesiana y un CSP propios con un agente LLM, RAG y dashboard. Explora favorabilidad climática de roya y programación de labores según lluvia y mano de obra. Se usan estaciones como proxy municipal en Antioquia, Caldas, Risaralda y Quindío. No se dispone de incidencia de roya en campo ni se modelan otras plagas; el resultado es un indicador exploratorio.
## 2. Datos y control de calidad
Fuentes IDEAM/Socrata: precipitación s54a-sgyg (mm), temperatura sbwg-7ju4 (°C) y humedad relativa uext-mhny (%). Colab descargó 78.264, 55.224 y 55.516 filas estación-día, respectivamente. El manifiesto conserva consulta, rango y SHA-256. Rango solicitado: 01/01/2022-31/10/2026.
La tabla contiene **4,372 semanas-municipio y 47 municipios**, sin duplicados: 28 de Antioquia, 8 de Caldas, 7 de Quindío y 4 de Risaralda. Etiquetas semanales: 09/01/2022-01/11/2026; el domingo 01/11 es cierre de la última semana parcial, no una observación posterior al 31/10.
Se suma lluvia y se promedia temperatura/humedad por estación-día; luego se promedian estaciones del municipio y se agrega a semana terminada en domingo. Se exigen >=72 lecturas de lluvia, >=12 de temperatura/humedad y >=12 horas distintas, >=5 días de lluvia y >=4 de temperatura/humedad. Duplicados simultáneos se rechazan. Se conservan municipios con >=60 semanas válidas, identificados por nombre y departamento.
Humedad disponible: **4.176/4.372 (95,52%)**; faltan 196 valores. Se extrapoló lluvia en **1.160 semanas (26,53%)** con 5/6 días válidos. La auditoría marca **54 registros para revisión**: 47 con humedad <20% y 7 con lluvia >500 mm/semana; son banderas exploratorias, no errores confirmados ni reglas de borrado.
En 2024 solo quedaron **11 registros**; no es una serie completa de cinco años por municipio. La calidad y continuidad limitan el experimento y exigen investigar estaciones, sensores y unidades antes de uso agronómico.
<!-- PAGEBREAK -->
# Método clásico y resultados
## 3. Red bayesiana implementada por el proyecto
Objetivo heurístico en t+1: se suma un puntaje de temperatura (<18°C=0; 18-21°C=1; 21-25°C=2; >=25°C=1) y otro de lluvia media de dos semanas según terciles de entrenamiento (0/1/2). Bajo <=1, Medio=2 y Alto>=3. No es una etiqueta de incidencia observada.
Evidencias en t: trimestre de la semana objetivo, lluvia t y t-1, temperatura y humedad (<80%, >=80% o SinDato). CPT por conteo con suavizado de Laplace alpha=1; inferencia exacta por eliminación de variables en NumPy. Se comprobó frente a enumeración. Humedad no se imputa desde lluvia; umbral y estructura son elecciones exploratorias.
Validación temporal: corte **2026-02-22**, **2693 filas de entrenamiento y 976 de prueba**, 919 parámetros. Los objetivos de entrenamiento no exceden el corte; terciles y CPT usan entrenamiento. Evidencias de prueba: 01/03/2026-25/10/2026. El modelo final se ajustó con toda la serie en Colab para la demo; sus consultas históricas no son backtesting.
| Modelo | Accuracy | F1 macro | Brier | Log-loss |
|---|---|---|---|---|
| Mayoritaria | 0.3391 | 0.1688 | 0.6673 | 1.0996 |
| Persistencia Riesgo_t | 0.7777 | 0.7716 | 0.3930 | 0.7480 |
| Regresión logística | 0.8002 | 0.7935 | 0.3163 | 0.5425 |
| Red bayesiana propia | 0.7480 | 0.7453 | 0.3693 | 0.6498 |
La red supera a la clase mayoritaria, pero su F1 macro es **0,0263 inferior a persistencia** y **0,0482 inferior a logística**. En Brier mejora persistencia (0,3693 frente a 0,3930), pero pierde frente a logística (0,3163). No se afirma superioridad de la red ni validación epidemiológica.
**Sensibilidad conservadora (Colab).** Entrenamiento: 2689 filas; prueba: 976. Red: accuracy 0.7428, F1 macro 0.7407, Brier 0.3740 y log-loss 0.6577. F1 cambia de 0,7453 a 0,7407; no mejora las métricas de la red. Se mantienen 976 claves municipio/fecha, pero cambian dos etiquetas del objetivo, por lo que no es una prueba sobre un objetivo fijo ni de significancia. Se conserva el original como referencia reproducible y la sensibilidad por separado; no se certifican los filtros.
La prueba contiene 353 casos Bajo, 292 Medio y 331 Alto. Matriz de confusión (filas reales; columnas predichas):
| Real / predicho | Bajo | Medio | Alto |
|---|---|---|---|
| Bajo | 275 | 75 | 3 |
| Medio | 44 | 197 | 51 |
| Alto | 19 | 54 | 258 |
Medio concentra confusiones con ambas clases; recall 197/292=67,47%. La persistencia fuerte es coherente con el objetivo suavizado en dos semanas.
## 4. Programación CSP
Variables: inicio semanal de labor. Restricciones: clima permitido, jornales, precedencia deshierba-fertilización y separación. Backtracking, MRV y forward checking propios; climatología anterior a la referencia, no pronóstico meteorológico. Jornales/ventanas son supuestos del equipo.
En el escenario mixto ambas búsquedas exploraron **4 nodos** y encontraron solución. Solo lluvia alta y capacidad baja se descartaron en consistencia de nodo (**0 nodos**). Estos ejemplos prueban restricciones, pero **no demuestran ahorro por heurísticas**. Presupuesto agotado se distingue de infactibilidad.
<!-- PAGEBREAK -->
# Agente, RAG y dashboard
## 5. Diseño e interacción
LLM remoto NVIDIA NIM: nvidia/nemotron-3.5-lightning-30b-a3b. Loop manual de hasta seis llamadas; herramientas risk (red bayesiana), schedule (CSP), search_docs (RAG) y weather_summary (datos). Los errores vuelven como observación. La interfaz pasa municipio, fecha, área, capacidad, horizonte y labores cuando no se especifican argumentos.
RAG TF-IDF, fragmentos de unas 110 palabras con solape y citas por página. Corpus: Avances Técnicos Cenicafé 498 (severidad de roya), 391 (fertilización) y 545 (fertilización antes/después de zoca): tres PDF, 24 páginas, texto extraíble y hashes. Las notas del proyecto se distinguen de documentos oficiales. Embeddings son opcionales, no necesarios para este MVP.
El dashboard presenta mapa, lluvia/temperatura/humedad, probabilidades, calendario, alertas y chat con trazas. Admite municipio, fecha y parámetros de labores. La carga programática con los artefactos reales no generó excepciones y presentó seis pestañas; falta la inspección interactiva final del equipo.
## 6. Evaluación del agente
Se usan doce preguntas fijas, diez con cita requerida: riesgo, probabilidad, síntomas, clima favorable, calendario, cosecha/fertilización, serie reciente, lluvia/fertilización, riesgo/manejo, riesgo/calendario, dólar fuera de alcance y Atlantis sin datos. Se evalúa inclusión de herramientas esperadas, éxito (salvo error esperado) y etiquetas respaldadas. Se permiten herramientas adicionales; no se mide exactitud de selección exclusiva.
| Ejecución original en Colab | Herramientas esperadas | Citas requeridas | LLM real |
|---|---|---|---|
| NVIDIA | 12/12 | 5/10 | 12/12 |
| Router determinista | 12/12 | 10/10 | No aplica |
La ejecución original no tuvo respaldo ni agotamiento, pero falló citas en preguntas 2, 5, 7, 9 y 10: marcadores ficticios, etiquetas alteradas y fuentes adicionales inventadas. La pregunta 5 también expandió mal CSP y la 9 añadió umbrales/manejo no respaldados. Elegir bien una herramienta no garantiza una respuesta fiel.
Se retiraron ejemplos de cita que el LLM copiaba, se aclaró el significado de CSP, la autoría del modelo y las fechas semanales. Una protección compara citas con todas las fuentes de las herramientas y reemplaza respuestas inválidas o truncadas por un resumen identificado; conserva raw_answer y answer_source. Esto comprueba procedencia de etiquetas, no soporte semántico de cada afirmación.
La revisión posterior obtuvo herramientas correctas en 10/12 y citas entregadas correctas en 10/10. La redacción original del LLM citó correctamente en 5/10; 6 respuestas se sustituyeron por resumen de herramientas. Se conservan la salida original y la entregada; el resumen no acredita acierto autónomo del LLM.
Los resultados originales siguen en eval_agente_llm.json; la revisión está separada en eval_agente_llm_revisado.json. La revisión falló en la pregunta 6 (no llamó schedule) y en la 12 (no obtuvo el error de municipio desconocido esperado). El router tiene ventaja por diseño y no sustituye evaluar el LLM. Las preguntas se conocían al desarrollar el sistema: falta un conjunto independiente.
<!-- PAGEBREAK -->
# Limitaciones, reproducción y entrega
## 7. Interpretación responsable
Los datos requeridos de clima están presentes y proceden de IDEAM, pero **su calidad meteorológica no está certificada**. La media municipal puede mezclar pisos térmicos y no acredita condiciones de una finca o de un lote cafetero. Lluvia/humedad no equivalen a mojado foliar, variedad, fenología ni incidencia. El experimento original conserva todas las observaciones y enumera las sospechosas en results/observaciones_para_revision.csv.
Los tres CSV diarios coinciden con el manifiesto y reproducen la tabla semanal. Se detectaron 1.620 días con humedad <20%, 20 días de secuencias con igual media de lluvia por lectura y diez días >300 mm. Pereira presenta totales proporcionales al número de lecturas y Salamina un salto de escala de humedad: son indicios, no errores certificados. Una sensibilidad separada omite esos días antes de promediar estaciones: conserva 4.368 filas/47 municipios, modifica 192 valores semanales de humedad y mantiene tres extremos de lluvia. La variante se entrenó en Colab: sus métricas se presentan en la sección 3 y se conservan separadas del original. Detalle: docs/REVISION_DATOS_DIARIOS.md.
La discontinuidad de 2024, los terciles globales, el promedio de estaciones y la extrapolación de días pueden sesgar resultados. Un único corte no cuantifica incertidumbre ni generalización espacial. Las métricas describen esta tabla y este indicador; se requiere análisis de sensibilidad tras validar anomalías. No se reentrenó para esconder un desempeño inferior a las referencias.
El control de citas no demuestra que cada afirmación sea correcta. El LLM y el corpus tienen límites; no se fijan dosis ni tratamientos por el indicador. Los calendarios usan climatología y supuestos de mano de obra. Las decisiones de campo corresponden al caficultor y al Servicio de Extensión.
## 8. Reproducibilidad
El notebook 02_Colab_pipeline.ipynb ejecuta descarga, agregación, entrenamiento y evaluaciones en CPU de Colab; NVIDIA sirve el LLM por API. La descarga reanuda particiones y divide intervalos ante timeout. Los manifiestos guardan hashes; results/entorno.txt registra versiones. Los artefactos semanal.csv y modelo_roya.pkl se recuperaron sin alterar las métricas originales. No se entrenaron modelos reales en el PC.
La demo carga esos artefactos con streamlit run app.py. requirements-cloud.txt coincide con las versiones principales de Colab. Pruebas pequeñas verifican implementación, no desempeño real. Los resultados del CSP son escenarios controlados y se identifican como tales. El README permite usar la instantánea o reproducir todo en nube.
La declaración de IA describe el andamiaje previo atribuido a Claude, revisión con Codex y LLM NVIDIA. El equipo debe confirmar su contribución individual y comprensión. Se mantienen la guía, las doce preguntas, respuestas completas, trazas y el informe en el repositorio.
## Referencias y evidencias
IDEAM, datos.gov.co: conjuntos s54a-sgyg, sbwg-7ju4 y uext-mhny; metadatos y manifiesto en data/raw/. Página de acceso: https://www.datos.gov.co/.
López y colaboradores (2018), Avance 498; Sadeghian (2010), Avance 391; Salazar-Gutiérrez y Sadeghian (2022), Avance 545. URLs originales, autores y hashes en corpus/FUENTES.md y corpus/manifest.json.
NVIDIA: https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b.
Evidencia: results/metricas_modelo.json, eval_csp.json, eval_agente_llm.json, eval_agente_llm_revisado.json y auditoria_datos.json.
**Cierre:** MVP ejecutado con resultados reales; quedan por verificar las anomalías de datos y la demo interactiva. Este informe expone esas limitaciones y no certifica predicción de enfermedad.
