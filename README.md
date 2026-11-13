# Asistente agroclimático para café

Proyecto 3.5, SI3003, Universidad EAFIT. Grupo Jueves.
**Jhon Jairo Pulgarin, Yesid Hurtado y Frank López.**

Red bayesiana e inferencia por eliminación de variables implementadas en NumPy; CSP propio con backtracking, MRV y forward checking; agente NVIDIA con RAG, cuatro herramientas y dashboard Streamlit.

**Estado:** históricos, entrenamiento y evaluaciones originales ejecutados en Colab y recuperados. Hay 4.372 semanas-municipio de 47 municipios; el dashboard cargó con los artefactos reales. Informe de **cuatro páginas** en [output/pdf/INFORME.pdf](output/pdf/INFORME.pdf), fuente editable en docs/INFORME.md. La auditoría identifica 54 semanas para revisión y una discontinuidad en 2024: los datos son exploratorios y no están certificados. Ver [auditoría actual](docs/REVISION_PROYECTO.md).

## Abrir la demo sin repetir los experimentos

Con data/processed/semanal.csv y modelo_roya.pkl presentes:

~~~powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
~~~

El LLM corre en NVIDIA. La red pequeña se carga ya entrenada; no hay entrenamiento al abrir el dashboard. Los experimentos de nube de la siguiente sección son para reproducir los resultados, no para iniciar la demo.


## Experimentos en Colab (sin entrenamiento en el PC)

1. Desde el proyecto ejecuta: **python scripts/package_colab.py**. Genera artifacts/cafe_colab_source.zip con el código actual, sin la clave.
2. Abre [Google Colab](https://colab.research.google.com/), selecciona Subir notebook y abre notebooks/02_Colab_pipeline.ipynb.
3. Usa runtime **CPU**. Ejecuta las celdas en orden y sube el ZIP cuando lo pida.
4. Agrega NVIDIA_API_KEY en Secretos de Colab, con acceso al notebook; también hay entrada oculta.
5. Revisa results/cobertura_datos.csv y calidad_datos.json. Continúa con entrenamiento y evaluaciones del modelo, CSP y agente.
6. Descarga cafe_resultados.zip al finalizar. Extrae sus carpetas en la raíz del proyecto y completa docs/INFORME.md con los resultados.

Ver [ejecución en nube](docs/EJECUCION_NUBE.md).

## Dashboard después de recuperar artefactos

Python >= 3.12 para el perfil fijado. En PowerShell:

~~~powershell
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-cloud.txt
streamlit run app.py
~~~

El dashboard carga data/processed/semanal.csv y modelo_roya.pkl ya calculados. El LLM se ejecuta en NVIDIA por API. En el dashboard cada visitante ingresa su propia clave en “Tu API key de NVIDIA”, en la barra lateral. La web usa únicamente esa clave de sesión; si queda vacía, no usa la clave privada del servidor. El .env se conserva para comandos CLI/evaluaciones y no se publica.

Modelo verificado: **nvidia/nemotron-3.5-lightning-30b-a3b**, endpoint https://integrate.api.nvidia.com/v1. Las cuotas dependen de la cuenta NVIDIA. Sin clave o ante fallo del proveedor existe un respaldo determinista identificado como mock/fallback: no acredita el requisito de LLM real.

Si el chat muestra APIConnectionError, falló la conexión desde el servidor a NVIDIA; no demuestra que la clave sea incorrecta. El chat reintenta una vez los fallos transitorios y muestra un diagnóstico sin publicar cuerpos del proveedor ni credenciales. Comprueba Internet, proxy, DNS y certificados en el equipo que ejecuta Streamlit. Si aparece un bloqueo de permisos de red en un entorno restringido, inicia Streamlit desde una terminal con acceso a Internet. Mantén activa la verificación HTTPS. Los errores HTTP 401, 403 y 429 se identifican por separado como autenticación, acceso y límite de uso.

## Datos y calidad

| Variable IDEAM | Conjunto | Unidad/frecuencia declarada | Mínimo por día |
|---|---|---|---|
| Precipitación | s54a-sgyg | mm, cada 10 minutos | 72 timestamps |
| Temperatura | sbwg-7ju4 | °C, horaria | 12 timestamps |
| Humedad relativa | uext-mhny | %, horaria | 12 timestamps |

Departamentos: Antioquia, Caldas, Risaralda, Quindío. Rango reproducible: 2022-01-01 a 2026-10-31. Los metadatos se guardan con la descarga; IDEAM advierte sobre rezago, inconsistencias y validaciones adicionales.

Agregación: estación-día, promedio municipal entre estaciones y semana terminada en domingo. Se requieren 5 días de precipitación y 4 de temperatura/humedad; lluvia de semanas con 5/6 días se extrapola a 7 y se contabiliza en calidad. Se requieren 60 semanas válidas por municipio. Los municipios se califican con departamento para evitar homónimos. Las estaciones representan el municipio; no se atribuyen mediciones a una finca.

Las muestras históricas consultadas presentaron hasta 288 lecturas/día aunque los metadatos actuales declaran frecuencias menores. La descarga cuenta además horas distintas y exige al menos 12 horas cubiertas por día, para no confundir alta frecuencia con buena cobertura. El CSV manual sin horas permite únicamente el filtro por conteo y debe documentar su frecuencia.

Se rechazan días con registros simultáneos por estación, valores inválidos y estación-día duplicada. Los umbrales son controles exploratorios, no una validación meteorológica. Revise cobertura de humedad, huecos, ubicación/altitud y estaciones antes de aceptar el análisis.

**Objetivo:** indicador heurístico de favorabilidad climática en t+1, construido con lluvia y temperatura. Humedad es un predictor adicional, con estado explícito SinDato; no se imputa desde lluvia. El repositorio no contiene etiquetas de incidencia de roya. F1/Brier/log-loss miden pronóstico del indicador, no enfermedad observada. No se modelan otras plagas.

**Plan B:** CSV diarios en data/raw/ con columnas codigoestacion,municipio,departamento,latitud,longitud,dia,valor,n. Archivos: precip_diaria.csv (suma diaria mm), temp_diaria.csv (media diaria °C), humedad_diaria.csv (media diaria %). n cuenta timestamps válidos según la frecuencia. No basta exportar registros instantáneos y renombrarlos: primero agregue por estación-día. Documente fuente, rango y hash. Continúe en Colab desde cafe.data_prep.

## Pipeline (runtime de nube)

~~~bash
python -m cafe.verify_services
python -m cafe.fetch_corpus
python -m cafe.data_download --desde 2022-01-01 --hasta 2026-10-31
python -m cafe.data_prep
python -m cafe.risk_model
python -m cafe.evaluate_csp
python -m cafe.evaluate_agent --mock
python -m cafe.evaluate_agent
python -m cafe.check_delivery
~~~

La descarga conserva caché mensual y manifiesto SHA-256. run_all.sh ejecuta esos pasos en Linux/Colab; no lo uses en el PC para entrenar.

El corpus se reconstruye con corpus/urls.txt; corpus/manifest.json guarda origen y hash. RAG TF-IDF no descarga un modelo. Los PDF conservan citas por página. Las notas del equipo se distinguen de publicaciones originales. Embeddings son alternativa opcional para ejecutar en nube; el PDF los sugiere, no los exige.

Validación temporal: terciles y CPT solo con entrenamiento; objetivo t+1 separado del test. Regresión logística usa las mismas evidencias que la red; persistencia es otra referencia. El modelo final usa toda la serie: consultas históricas del dashboard son retrospectivas, no backtesting. El calendario usa historia hasta la fecha consultada y climatología, no pronóstico meteorológico.

## Pruebas y entregables

Pruebas pequeñas, sin red, con datos sintéticos solo para verificar código:

~~~powershell
New-Item -ItemType Directory -Force tmp
python -m pytest -q --basetemp=tmp/pytest-manual
~~~

- output/pdf/INFORME.pdf: informe de cuatro páginas con resultados reales, revisado visualmente; docs/INFORME.md es la fuente editable.
- docs/DECLARACION_IA.md: declaración; el equipo debe revisar su contribución y comprensión.
- eval/preguntas.json: 12 preguntas; eval_agente_llm.* y eval_agente_mock.* guardan respuestas, trazas y citas por separado.
- results/metricas_modelo.*, eval_csp.*, calidad_datos.json, cobertura_datos.csv: evidencia del pipeline.
- Demo: mapa, series, humedad, distribución de favorabilidad, calendario, alertas y chat con trazas.

**Entrega:** viernes 13 de noviembre de 2026, 6:00 p. m. Cada integrante envía el repositorio al correo del PDF, asunto si3003-AI-grupo-nombre. Video de 3–4 minutos opcional como respaldo. El documento indica que no habrá sustentación; el repositorio debe ser autosuficiente.

Herramienta exploratoria. Los jornales y ventanas del CSP son supuestos ajustables, no recomendaciones validadas.

## Resultados verificados

- Red bayesiana: accuracy 0,7480; F1 macro 0,7453. Persistencia: F1 0,7716; logística: F1 0,7935. La red no supera esas referencias en F1.
- Agente original en Colab: herramientas esperadas 12/12; citas 5/10; LLM real 12/12.
- Revisión separada: herramientas 10/12; citas entregadas 10/10; citas originales del LLM 5/10. Seis respuestas se sustituyeron por resúmenes de herramientas; esto no equivale a acierto autónomo del LLM. Fallos de herramienta: preguntas 6 y 12.
- results/observaciones_para_revision.csv enumera 47 semanas con humedad <20% y siete con lluvia >500 mm. No se borraron datos ni se modificaron métricas del modelo.
- La auditoría se reproduce sin entrenar con python -m cafe.audit_artifacts.
- La evaluación revisada se reproduce por API con python -m cafe.evaluate_agent --tag revisado. Guarda originales y revisión por separado.
- Para volver a crear el PDF se necesitan reportlab y pypdf: python scripts/build_report.py.

## Revisión de CSV diarios

Los tres archivos diarios recuperados coinciden con los hashes de Colab; su agregación reproduce la tabla original. El análisis está en [docs/REVISION_DATOS_DIARIOS.md](docs/REVISION_DATOS_DIARIOS.md). Se preparó una variante conservadora en data/review/, separada de la demo: 4.368 filas de los mismos 47 municipios. Los umbrales son una política exploratoria de sensibilidad, no una certificación de errores de sensores.

No se modificaron los datos/modelo originales ni sus métricas. Para medir la variante sin descargar históricos, usa el paso “Sensibilidad de calidad” de docs/EJECUCION_NUBE.md y artifacts/cafe_revision_calidad.zip. El módulo cafe.review_experiment rechaza entrenar en este PC y guarda el experimento en carpetas independientes de Colab.

## Sensibilidad de calidad completada

Los artefactos de la variante ya se recuperaron de Colab. Red bayesiana conservadora: accuracy 0,7428; F1 macro 0,7407; Brier 0,3740; log-loss 0,6577. Original: F1 0,7453 y Brier 0,3693. La variante no mejora esas métricas. Las pruebas comparten 976 claves municipio/fecha, con dos etiquetas del indicador modificadas; no es una prueba sobre un objetivo fijo ni de significancia.

Se conserva el original como referencia de la demo y la variante como sensibilidad documentada, sin certificar sus filtros como correcciones de sensores. Ambos modelos se entrenaron en Colab y corresponden a sus respectivas tablas; no se reentrenó localmente. No hace falta otra ejecución en Colab para esta comparación.

La comparación completa está en results/revision_calidad/comparacion_calidad.md y es visible en Métricas del dashboard. Se reproduce sin entrenar con python -m cafe.compare_quality.

Verificación final: 49 pruebas automáticas pasaron. Informe PDF de cuatro páginas revisado visualmente; instantánea y sensibilidad verificadas sin reentrenar en el PC.

## Clave propia por visitante en la web

Cada usuario pega su clave NVIDIA en el campo oculto de la barra lateral. Se mantiene en la memoria de su sesión Streamlit y se pasa directamente al cliente de esa consulta; no se escribe en .env ni en archivos de conversaciones, ni se configura globalmente. “Olvidar mi clave” vacía el campo de esa sesión. Sin clave funciona el modo demostración, aunque el servidor tenga una clave en su entorno.

La petición pasa por el backend de la aplicación y después por NVIDIA: no es una conexión exclusivamente desde el navegador. El hosting debe servir HTTPS. El equipo que opera el servidor sigue siendo una parte de confianza. La aplicación no implementa almacenamiento persistente de claves ni una bóveda de cuentas. Una recarga/nueva sesión puede requerir ingresarla de nuevo.

No hace falta configurar LLM_API_KEY en el hosting para este modo. Los scripts de evaluación siguen usando .env/variables de entorno para su configuración original. El modelo se configura por el operador, no por el visitante. Las cuotas/permisos de NVIDIA son los de la clave del visitante.

Documentación oficial: https://docs.streamlit.io/develop/api-reference/widgets/st.text_input y https://docs.streamlit.io/develop/concepts/architecture/session-state.

## Series climáticas y semanas faltantes

La pestaña Series de tiempo usa data/processed/clima_semanal.csv, una tabla independiente por variable. La lluvia válida no desaparece por faltar temperatura; la tabla del modelo sigue exigiendo ambas variables. Se conservan los huecos como NaN, las líneas no conectan semanas sin datos y los ceros observados de lluvia se marcan con puntos. El periodo permite los últimos dos años de calendario o todo el histórico disponible.

La tabla para gráficos se genera automáticamente durante cafe.data_prep o por separado con python -m cafe.climate_series. Este segundo comando solo agrega los CSV diarios existentes: no descarga ni entrena y no modifica semanal.csv/modelo_roya.pkl. El paquete de entrega incluye la tabla para gráficos, de modo que el despliegue no necesita los CSV diarios.

En Medellín la visualización independiente recupera la semana 01/06/2025 con 19 mm y sin temperatura; hay 144 semanas válidas de lluvia frente a 143 en la tabla conjunta del modelo. Siguen existiendo huecos reales por calidad/cobertura de las estaciones, especialmente en 2024.
