Modo solicitado: mock; modelo: None. Herramienta correcta: 12/12; cita donde se exige: 10/10; LLM real: 0; respaldo: 0; límite alcanzado: 0.

| # | Pregunta | Esperadas | Llamadas | Herr. OK | Cita OK | Modo |
|---|---|---|---|---|---|---|
| 1 | ¿Cuál es el riesgo de roya la próxima semana en Abriaqui / Antioquia? | risk | risk | True | True | mock |
| 2 | ¿Qué probabilidad hay de riesgo alto de roya en Abriaqui / Antioquia? | risk | risk | True | True | mock |
| 3 | ¿Qué es la roya del cafeto y cuáles son sus síntomas? | search_docs | search_docs | True | True | mock |
| 4 | ¿Qué condiciones de clima favorecen la roya? | search_docs | search_docs | True | True | mock |
| 5 | Arma un calendario de deshierba y fertilización para Abriaqui / Antioquia | schedule | schedule | True | True | mock |
| 6 | ¿Cuándo programo la cosecha y la fertilización en Abriaqui / Antioquia? | schedule | schedule | True | True | mock |
| 7 | ¿Cuánta lluvia y qué temperatura hubo en las últimas semanas en Abriaqui / Antioquia? | weather_summary | weather_summary | True | True | mock |
| 8 | ¿Cómo afecta la lluvia a la fertilización y cuándo conviene hacerla? | search_docs | schedule, search_docs, weather_summary | True | True | mock |
| 9 | ¿Hay riesgo de roya en Abriaqui / Antioquia y qué manejo recomiendas? | risk, search_docs | risk, search_docs | True | True | mock |
| 10 | Dame el riesgo de roya y el calendario de labores para Abriaqui / Antioquia | risk, schedule | risk, schedule | True | True | mock |
| 11 | ¿Cuál es el precio del dólar hoy? |  |  | True | True | mock |
| 12 | Dame el riesgo de roya en Atlantis | risk | risk | True | True | mock |