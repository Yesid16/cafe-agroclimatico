# Asistente agroclimático para café: riesgo climático de roya y planeación de labores

**SI3003 – Inteligencia Artificial · EAFIT 2026-1 · Proyecto final** · Equipo: [COMPLETAR] · Repositorio: [COMPLETAR URL]

> Instrucciones: los campos **[COMPLETAR]** y las tablas de la sección 5 se llenan con los archivos de `results/` generados al ejecutar el pipeline con los datos reales. Borre esta nota y mantenga el informe en ≤ 4 páginas.

## 1. Problema
El caficultor debe decidir cuándo fertilizar, deshierbar, controlar la roya y cosechar según un clima cambiante, y la roya (*Hemileia vastatrix*) se ve favorecida por temperaturas medias de ~21–25 °C y por lluvia reciente. Construimos un asistente que (i) pronostica el riesgo **climático** de roya por municipio para la semana siguiente, (ii) propone un calendario de labores que respeta clima esperado y mano de obra, y (iii) responde preguntas en lenguaje natural citando documentos técnicos y datos.

## 2. Datos
IDEAM, datos.gov.co (API Socrata): precipitación (`s54a-sgyg`, lecturas cada 10 min, mm) y temperatura (`sbwg-7ju4`), Antioquia, Caldas, Risaralda y Quindío, [COMPLETAR rango de fechas]. Agregación: suma/promedio diario por estación en el servidor (filtro de valores fuera de rango y de días con < 72 lecturas), promedio entre estaciones del municipio y agregación semanal (semanas que terminan en domingo; ≥ 5 días válidos para lluvia y ≥ 4 para temperatura). Resultado: [COMPLETAR n] municipios y [COMPLETAR n] semanas-municipio. El IDEAM advierte que los datos son crudos y no validados. Corpus RAG: [COMPLETAR lista final: notas del equipo + PDF de Cenicafé/FNC/IDEAM utilizados].

## 3. Parte 1: técnicas clásicas implementadas por el equipo
**Indicador de riesgo.** No existe una serie pública de incidencia de roya por municipio-semana, por lo que definimos `Riesgo ∈ {Bajo, Medio, Alto}` con una regla de favorabilidad: puntaje de temperatura (Óptima 21–25 °C = 2; Fresca 18–21 °C o Cálida > 25 °C = 1; Fría < 18 °C = 0) más puntaje de lluvia (promedio de las últimas dos semanas, terciles del entrenamiento: 0/1/2); Bajo ≤ 1, Medio = 2, Alto ≥ 3.

**Red bayesiana (`bayes_net.py`, `risk_model.py`).** Nodos: `Trim` (trimestre de la semana pronosticada), `Lluvia_prev`, `Lluvia`, `Temp` y `Riesgo` (semana t+1), con `Riesgo` dependiente de los otros cuatro. Las tablas de probabilidad condicional se aprenden por conteo con suavizado de Laplace (α = 1) y la inferencia exacta usa **eliminación de variables** con orden de mínimo grado, soportando evidencia parcial (una variable no observada se marginaliza). Se verificó contra enumeración por fuerza bruta (prueba automática). Validación **temporal**: terciles y CPT con datos ≤ fecha de corte y prueba en el 20 % final, sin fuga del objetivo. Líneas base: clase mayoritaria, persistencia (`Riesgo_t`) y regresión logística (referencia de librería).

**CSP (`csp.py`).** Variables: semana de inicio de cada labor; restricciones: lluvia esperada permitida por labor, capacidad semanal de jornales, precedencia (deshierba antes de fertilizar) y separación (fertilización–aspersión). Búsqueda por backtracking con MRV y forward checking; se compara con búsqueda sin heurísticas en nodos explorados. El clima esperado por semana es la moda histórica del municipio para ese mes (no un pronóstico meteorológico).

## 4. Parte 2: agente con RAG y herramientas
Loop agéntico manual (`agent.py`) sobre un endpoint compatible con OpenAI [COMPLETAR modelo/proveedor], con `T_max = 6`, herramientas devueltas al modelo como observación (incluidos los errores) y respuesta final con etiquetas de cita. Herramientas: `risk(municipio, fecha)` → red bayesiana; `schedule(municipio, labores, semanas, hectáreas, capacidad)` → CSP; `search_docs(query)` → RAG; `weather_summary(municipio)` → datos IDEAM. RAG: fragmentos de ~110 palabras con solape, recuperación [TF-IDF | embeddings multilingües] con umbral mínimo de similitud (si no hay evidencia, el agente lo dice). El mensaje de sistema prohíbe inventar cifras, exige citar y excluye consejo agronómico, médico o legal y dosis. Sin clave de LLM existe un modo local determinista (plan B de la demo y base de la evaluación reproducible).

## 5. Resultados
**5.1 Modelo (corte temporal).** [PEGAR `results/metricas_modelo.md`]

Lectura: [COMPLETAR: ¿la red supera a las líneas base en F1 macro y Brier? ¿Frente a la regresión logística? Discuta que `Riesgo_t` es una referencia fuerte porque el indicador es persistente, y qué clases se confunden.] 

**5.2 CSP.** Nodos explorados con y sin MRV/FC: [COMPLETAR con un ejemplo del dashboard o de una prueba]. Casos infactibles: el solver devuelve el motivo (p. ej., ninguna semana de lluvia Media para fertilizar).

**5.3 Agente.** [PEGAR `results/eval_agente.md`: 12 preguntas, herramienta correcta y cita]. Nota metodológica: con el enrutador local la evaluación es reproducible pero favorable (las reglas se escribieron conociendo las preguntas); repita `python -m cafe.evaluate_agent` **con el LLM real** y reporte ambos resultados. Fallos observados: [COMPLETAR].

**5.4 Dashboard.** Mapa de riesgo por municipio, serie de lluvia/temperatura, probabilidades del pronóstico, calendario tipo Gantt con clima esperado y chat con trazas de herramientas. [Opcional: capturas en `docs/figures/`]

## 6. Limitaciones y uso responsable
1) El riesgo es un indicador climático, no incidencia medida en campo; la métrica evalúa el pronóstico de ese indicador, no la roya real. 2) Municipio como proxy de finca; la altitud modifica la temperatura. 3) Datos crudos sin validar, con huecos y rezago; sensores de precipitación pueden fallar. 4) Terciles de lluvia globales: municipios muy húmedos o secos quedan sesgados. 5) Calendario con climatología, y jornales/ventanas del catálogo son parámetros orientativos. 6) El LLM puede equivocarse; se mitiga con herramientas, citas y rechazo de preguntas fuera de alcance. Ningún resultado debe tomarse como consejo agronómico, médico, legal o de seguridad: consulte al extensionista del Comité de Cafeteros y el pronóstico oficial del IDEAM.

## 7. Reproducibilidad y uso de IA
Pasos exactos en el `README.md`; pruebas con `pytest -q` (usan datos sintéticos únicamente para verificar el código). Declaración de uso de IA generativa en `docs/DECLARACION_IA.md`.
