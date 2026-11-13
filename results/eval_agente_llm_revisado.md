Modo solicitado: llm; modelo: nvidia/nemotron-3.5-lightning-30b-a3b. Herramienta correcta: 10/12; cita donde se exige: 10/10; LLM real: 12; respaldo: 0; límite alcanzado: 0.
Citas originales del LLM: 5/10; respuestas sustituidas por resumen de herramientas: 6. No equivale a acierto autónomo del LLM.

| # | Pregunta | Esperadas | Llamadas | Herr. OK | Cita OK | Modo |
|---|---|---|---|---|---|---|
| 1 | ¿Cuál es el riesgo de roya la próxima semana en Abriaqui / Antioquia? | risk | risk | True | True | llm |
| 2 | ¿Qué probabilidad hay de riesgo alto de roya en Abriaqui / Antioquia? | risk | risk | True | True | llm |
| 3 | ¿Qué es la roya del cafeto y cuáles son sus síntomas? | search_docs | search_docs | True | True | llm |
| 4 | ¿Qué condiciones de clima favorecen la roya? | search_docs | search_docs | True | True | llm |
| 5 | Arma un calendario de deshierba y fertilización para Abriaqui / Antioquia | schedule | schedule | True | True | llm |
| 6 | ¿Cuándo programo la cosecha y la fertilización en Abriaqui / Antioquia? | schedule | search_docs, weather_summary | False | True | llm |
| 7 | ¿Cuánta lluvia y qué temperatura hubo en las últimas semanas en Abriaqui / Antioquia? | weather_summary | weather_summary | True | True | llm |
| 8 | ¿Cómo afecta la lluvia a la fertilización y cuándo conviene hacerla? | search_docs | search_docs, weather_summary | True | True | llm |
| 9 | ¿Hay riesgo de roya en Abriaqui / Antioquia y qué manejo recomiendas? | risk, search_docs | risk, search_docs | True | True | llm |
| 10 | Dame el riesgo de roya y el calendario de labores para Abriaqui / Antioquia | risk, schedule | risk, schedule | True | True | llm |
| 11 | ¿Cuál es el precio del dólar hoy? |  |  | True | True | llm |
| 12 | Dame el riesgo de roya en Atlantis | risk | risk | False | True | llm |