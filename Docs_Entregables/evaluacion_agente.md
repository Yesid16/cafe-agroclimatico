# Evaluación del agente agroclimático
SI3003 · EAFIT · Grupo Jueves · Proyecto 3.5
Jhon Jairo Pulgarin, Yesid Hurtado y Frank López

Evaluación de doce preguntas fijas. Se comparan las ejecuciones original y revisada mediante las herramientas utilizadas y las fuentes citadas.

## Protocolo y criterios
Modelo remoto: nvidia/nemotron-3.5-lightning-30b-a3b. Se exige la herramienta prevista y la resolución del caso. Diez preguntas requieren cita. La comprobación valida etiquetas de fuentes, no el soporte de cada afirmación.

## Resultados comparados
| Indicador | Original | Revisada |
|---|---|---|
| Herramientas correctas | 12/12 | 10/12 |
| Citas del texto original del LLM | 5/10 | 5/10 |
| Citas en la respuesta entregada | 5/10 | 10/10 |
| Consultas con LLM real | 12/12 | 12/12 |
| Respuestas con resumen de herramientas | 0 | 6 |

La revisión acertó las herramientas en 10/12 consultas. Entregó citas válidas en 10/10 casos, frente a 5/10 en el texto original del LLM. Seis respuestas se sustituyeron por resúmenes de herramientas; este resultado no acredita acierto autónomo total.

## Resultados por pregunta
| Nº | Pregunta | Esperadas | Invocadas | Herramienta correcta | Cita entregada |
|---|---|---|---|---|---|
| 1 | ¿Cuál es el riesgo de roya la próxima semana en Abriaqui / Antioquia? | risk | risk | Sí | Sí |
| 2 | ¿Qué probabilidad hay de riesgo alto de roya en Abriaqui / Antioquia? | risk | risk | Sí | Sí |
| 3 | ¿Qué es la roya del cafeto y cuáles son sus síntomas? | search_docs | search_docs | Sí | Sí |
| 4 | ¿Qué condiciones de clima favorecen la roya? | search_docs | search_docs | Sí | Sí |
| 5 | Arma un calendario de deshierba y fertilización para Abriaqui / Antioquia | schedule | schedule | Sí | Sí |
| 6 | ¿Cuándo programo la cosecha y la fertilización en Abriaqui / Antioquia? | schedule | search_docs, weather_summary | No | Sí |
| 7 | ¿Cuánta lluvia y qué temperatura hubo en las últimas semanas en Abriaqui / Antioquia? | weather_summary | weather_summary | Sí | Sí |
| 8 | ¿Cómo afecta la lluvia a la fertilización y cuándo conviene hacerla? | search_docs | search_docs, weather_summary | Sí | Sí |
| 9 | ¿Hay riesgo de roya en Abriaqui / Antioquia y qué manejo recomiendas? | risk, search_docs | risk, search_docs | Sí | Sí |
| 10 | Dame el riesgo de roya y el calendario de labores para Abriaqui / Antioquia | risk, schedule | risk, schedule | Sí | Sí |
| 11 | ¿Cuál es el precio del dólar hoy? | Ninguna | Ninguna | Sí | No aplica |
| 12 | Dame el riesgo de roya en Atlantis | risk | risk | No | No aplica |

## Fallos y límites de la evaluación
Pregunta 6: llamó search_docs y weather_summary sin invocar schedule para programar labores. Pregunta 12: sustituyó Atlantis por el municipio del contexto y no reconoció el error esperado. Las preguntas se conocían durante el desarrollo; falta un conjunto independiente. La evaluación automática no certifica calidad agronómica, fidelidad completa de las respuestas ni disponibilidad continua del servicio.