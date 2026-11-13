# Asistente agroclimático para café

**Aplicación web / dashboard interactivo:** 

**Universidad EAFIT · SI3003 Inteligencia Artificial · Proyecto 3.5 · Grupo Jueves**

**Integrantes:** Jhon Jairo Pulgarin, Yesid Hurtado y Frank López.

## Descripción

Aplicación web para explorar las condiciones climáticas de municipios cafeteros, estimar la favorabilidad climática de la roya y organizar labores agrícolas. Integra datos históricos del IDEAM, un modelo propio y un asistente que consulta datos y publicaciones técnicas de Cenicafé.

El proyecto combina una red bayesiana para estimar el riesgo climático, un planificador de labores con restricciones de clima y mano de obra, y un agente de lenguaje con consulta de documentos y herramientas.

## Funciones de la aplicación

| Vista | Contenido |
|---|---|
| Mapa | Favorabilidad climática de roya por municipio. |
| Clima | Históricos de lluvia, temperatura y humedad. |
| Riesgo climático | Probabilidades estimadas y condiciones utilizadas. |
| Plan de labores | Calendario según actividades, área y mano de obra disponible. |
| Asistente | Conversación sobre clima, roya y labores, con fuentes y herramientas consultadas. |
| Evaluación | Resultados del modelo y del agente. |

La interfaz permite seleccionar municipio, fecha de referencia y parámetros de planificación. El asistente utiliza NVIDIA con la clave ingresada por cada visitante en el panel lateral. La clave se mantiene en su sesión y no se guarda en archivos. Sin clave, o si el servicio no está disponible, el chat identifica sus respuestas como modo demostración.

## Datos y fuentes

Los datos climáticos proceden del IDEAM a través de datos.gov.co e incluyen precipitación, temperatura y humedad relativa. El análisis abarca **47 municipios de Antioquia, Caldas, Risaralda y Quindío**, con registros solicitados entre el **1 de enero de 2022 y el 31 de octubre de 2026**.

El conjunto utilizado por el modelo contiene **4.372 observaciones semanales distribuidas entre esos municipios**. Las publicaciones técnicas de Cenicafé aportan las fuentes documentales del asistente. El origen de los datos y documentos está registrado en el [manifiesto de datos](data/raw/manifest.json) y en las [fuentes del corpus](corpus/FUENTES.md).

## Resultados

El modelo se evaluó con datos posteriores a los utilizados para su entrenamiento y se comparó con tres referencias.

| Modelo | F1 macro |
|---|---:|
| Clase mayoritaria | 0,1688 |
| Persistencia | 0,7716 |
| Regresión logística | 0,7935 |
| Red bayesiana del proyecto | 0,7453 |

La red bayesiana supera la referencia mayoritaria, pero no supera a persistencia ni a regresión logística en esta métrica.

La evaluación revisada del agente incluye **12 preguntas**: seleccionó correctamente las herramientas en **10 de 12** y entregó citas válidas en los **10 casos que las requerían**. Las respuestas originales del modelo citaron correctamente en 5 de esos 10 casos; seis respuestas fueron reemplazadas por resúmenes de las herramientas. La evaluación conserva las respuestas, las llamadas realizadas y los fallos encontrados.

## Entregables

| Entregable | Documento o ubicación |
|---|---|
| Código e instrucciones de ejecución | Este repositorio y la sección de ejecución. |
| Informe breve de cuatro páginas | [Informe del proyecto](Docs_Entregables/INFORME.pdf). |
| Demostración funcional | [Documento de demostración](Docs_Entregables/demostración_funcional.md), con espacio para el enlace y las capturas del dashboard. |
| Evaluación del agente | [Evaluación de las 12 preguntas](Docs_Entregables/evaluacion_agente.pdf). |
| Declaración de uso de IA generativa | [Declaración de uso de IA](Docs_Entregables/declaracion_uso_IA.pdf). |

La carpeta [Docs_Entregables](Docs_Entregables) reúne el informe, la evaluación del agente y la declaración de IA en PDF, junto con la demostración funcional en Markdown. Las evidencias de evaluación se conservan en results/.

## Ejecución de la aplicación

Requiere Python 3.12 o superior. Desde la carpeta del repositorio:

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

La aplicación utiliza los datos procesados y el modelo entrenado incluidos en el repositorio; abrirla no requiere descargar nuevamente los históricos ni repetir el entrenamiento. Las consultas al modelo de lenguaje se ejecutan en NVIDIA.

La reproducción de la descarga, el entrenamiento y las evaluaciones se realiza en Google Colab mediante el [notebook del proyecto](notebooks/02_Colab_pipeline.ipynb). El procedimiento está documentado en la [guía de ejecución en nube](docs/EJECUCION_NUBE.md).

## Alcance y limitaciones

El riesgo representa **favorabilidad climática para la roya**, no presencia ni incidencia observada de la enfermedad. Las estaciones se utilizan como referencia municipal y no describen las condiciones exactas de cada finca. El calendario es orientativo y utiliza supuestos de clima y mano de obra.

Los históricos presentan semanas sin datos y observaciones que requieren revisión. Los huecos en las gráficas indican datos faltantes, no ausencia de lluvia. La aplicación muestra información histórica y no ofrece monitoreo en tiempo real ni sustituye la evaluación de campo de un profesional.
