# Asistente agroclimático para café
Jhon Jairo Pulgarin, Yesid Hurtado y Frank López
Universidad EAFIT
SI3003 Inteligencia Artificial | Grupo Jueves
13 de noviembre de 2026

## Problema y datos

El proyecto integra información climática, estimación del riesgo de roya y planificación de labores en una aplicación web. Su alcance es municipal: las estaciones meteorológicas representan el entorno de los cultivos, sin sustituir mediciones de cada finca. La aplicación reúne un modelo predictivo propio, un planificador y un asistente con consulta documental.

Se utilizaron datos del Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM, s. f.) sobre precipitación, temperatura y humedad. El periodo solicitado fue del 1 de enero de 2022 al 31 de octubre de 2026. La tabla del modelo contiene 4.372 observaciones semanales de 47 municipios de Antioquia, Caldas, Risaralda y Quindío.

La preparación agrega las mediciones por estación, día, municipio y semana. Se exigen al menos cinco días válidos de lluvia y cuatro de temperatura y humedad. La lluvia de semanas con cinco o seis días se extrapola a siete. La humedad tiene una cobertura del 95,52 %. Los registros faltantes se conservan como ausencia de información.

<!-- PAGEBREAK -->

## Método y resultados del modelo

Se implementó una red bayesiana con inferencia por eliminación de variables. Predice la favorabilidad climática de la semana siguiente mediante lluvia reciente, temperatura, humedad y estacionalidad. La variable objetivo es un indicador construido con lluvia y temperatura; no corresponde a incidencia observada de roya.

La evaluación temporal separó 2.693 ejemplos de entrenamiento y 976 de prueba, con corte el 22 de febrero de 2026. Los parámetros y umbrales se calcularon con el entrenamiento. La tabla 1 presenta la comparación con las líneas base.

| Modelo | Exactitud | F1 macro |
|---|---|---|
| Clase mayoritaria | 0,3391 | 0,1688 |
| Persistencia | 0,7777 | 0,7716 |
| Regresión logística | 0,8002 | 0,7935 |
| Red bayesiana propia | 0,7480 | 0,7453 |

La red supera la referencia mayoritaria, pero su F1 macro es inferior a persistencia y regresión logística. La variante conservadora de calidad obtuvo F1 de 0,7407; no mejoró el resultado original. Ambos experimentos se ejecutaron en Colab.

## Planificación de labores

Se implementó un problema de satisfacción de restricciones para asignar semanas a las labores según clima, precedencias y mano de obra. El calendario utiliza climatología histórica y supuestos de duración; no representa un pronóstico meteorológico.

<!-- PAGEBREAK -->

## Agente y recuperación documental

El agente utiliza un modelo remoto de NVIDIA y cuatro herramientas: consulta del riesgo, planificación, resumen climático y búsqueda documental. El ciclo de interacción tiene un máximo de seis iteraciones. Las respuestas se apoyan en fragmentos recuperados y conservan las fuentes consultadas.

El corpus incluye publicaciones de Cenicafé sobre severidad de roya y fertilización (López-Vásquez et al., 2018; Sadeghian, 2010; Salazar-Gutiérrez & Sadeghian, 2022). La recuperación emplea similitud textual y fragmentos con referencia a su página. Las notas del equipo se diferencian de las publicaciones originales.

## Evaluación del agente

Se evaluaron doce preguntas fijas. La tabla 2 distingue la selección de herramientas de la calidad de las citas. Seis respuestas de la revisión fueron reemplazadas por resúmenes de herramientas debido al control de citas o de integridad de la respuesta.

| Indicador | Original | Revisada |
|---|---|---|
| Herramientas correctas | 12/12 | 10/12 |
| Citas originales del LLM | 5/10 | 5/10 |
| Citas entregadas | 5/10 | 10/10 |

La revisión falló al omitir la herramienta de planificación en una consulta y al sustituir un municipio inexistente por el del contexto. Las preguntas se conocían durante el desarrollo; falta una evaluación independiente.

<!-- PAGEBREAK -->

## Limitaciones y reproducción

Los datos presentan discontinuidades, especialmente en 2024, y 54 observaciones semanales requieren revisión. Los controles aplicados no certifican la calidad de los sensores. El promedio municipal y la extrapolación de días pueden introducir sesgos. El indicador no diagnostica enfermedad ni justifica tratamientos agronómicos.

El repositorio incluye los datos procesados, el modelo entrenado y las instrucciones de ejecución. El dashboard presenta mapa, series, probabilidades, calendario y chat. La descarga, el entrenamiento y las evaluaciones se reproducen en Colab. El informe de evaluación y las trazas completas se incluyen como documentos complementarios.

## Referencias

Instituto de Hidrología, Meteorología y Estudios Ambientales. (s. f.). *Precipitación, temperatura ambiente y humedad relativa del aire* [Conjuntos de datos s54a-sgyg, sbwg-7ju4 y uext-mhny]. Datos Abiertos Colombia. https://www.datos.gov.co/

López-Vásquez, J. M., Marín-Ramírez, G., Gaitán, A., & Ángel, C. A. (2018). *Diagrama de Área Estándar para la estimación visual de severidad de roya del cafeto*. Avances Técnicos Cenicafé, 498, 1-8. https://doi.org/10.38141/10779/0498

Sadeghian, S. (2010). *Fertilización: Una práctica que determina la producción de los cafetales*. Avances Técnicos Cenicafé, 391, 1-8. https://doi.org/10.38141/10779/0391

Salazar-Gutiérrez, L. F., & Sadeghian, S. (2022). *Épocas recomendables para la fertilización del café antes y después de la zoca*. Avances Técnicos Cenicafé, 545, 1-8. https://doi.org/10.38141/10779/0545
