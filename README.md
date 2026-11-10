# ☕ Asistente agroclimático para café (Antioquia y Eje Cafetero)

Proyecto final SI3003 – Inteligencia Artificial (EAFIT 2026-1). Idea 3.5: riesgo climático de roya y planeación de labores.

| Parte | Técnica | Dónde |
|---|---|---|
| **Parte 1** | Red bayesiana discreta propia (CPT por conteo + inferencia por **eliminación de variables**) con validación temporal y 3 líneas base | `cafe/bayes_net.py`, `cafe/risk_model.py` |
| **Parte 1** | **CSP** propio (backtracking + MRV + forward checking) para programar labores | `cafe/csp.py` |
| **Parte 2** | Agente LLM con loop manual (T_max), **RAG** (TF-IDF o embeddings) y 4 herramientas (`risk`, `schedule`, `search_docs`, `weather_summary`) | `cafe/agent.py`, `cafe/tools.py`, `cafe/rag.py` |
| Dashboard | Streamlit: mapa, series, pronóstico, calendario, chat | `app.py` |

## Datos (reales)
IDEAM en datos.gov.co (API Socrata): precipitación `s54a-sgyg` (lectura cada 10 min) y temperatura `sbwg-7ju4`, departamentos Antioquia, Caldas, Risaralda y Quindío. Son datos **crudos no validados** (aviso del IDEAM). Se agregan en el servidor por estación-día, luego por municipio-semana.
**Plan B:** si la API falla, coloque en `data/raw/` dos CSV con columnas `codigoestacion, municipio, departamento, latitud, longitud, dia, valor, n` (`precip_diaria.csv` = suma diaria en mm; `temp_diaria.csv` = promedio diario en °C), por ejemplo exportados de DHIME/datos.gov.co, y continúe en el paso 3.

## Ejecución (Python ≥ 3.10)
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # opcional: agregue LLM_API_KEY (Groq/NIM/Ollama)
python -m cafe.data_download --desde 2022-01-01        # 1. descarga (varios minutos)
python -m cafe.data_prep                               # 2. agrega a municipio-semana
python -m cafe.risk_model                              # 3. entrena, evalúa vs. líneas base y guarda el modelo
python -m cafe.evaluate_agent                          # 4. evalúa el agente (12 preguntas fijas) → results/
streamlit run app.py                                   # 5. dashboard
```
Todo en uno: `./run_all.sh`. Pruebas automáticas (usan datos SINTÉTICOS solo para probar el código): `pytest -q`.

**Corpus RAG:** `corpus/notas_*.md` son notas de síntesis del equipo (no oficiales). Agregue PDF abiertos de Cenicafé/FNC/IDEAM (ver `corpus/FUENTES.md`, `python -m cafe.fetch_corpus`); se indexan automáticamente.

**Modos del agente:** con `LLM_API_KEY` usa el LLM (loop agéntico, `T_max=6`, errores de herramientas devueltos como observación, degradación automática a modo local si el LLM falla). Sin clave usa un enrutador determinista: sirve como plan B de la demo y para evaluar de forma reproducible.

## Estructura
```
app.py                  dashboard Streamlit          corpus/   documentos del RAG
cafe/                   código (datos, modelo, CSP, RAG, agente, evaluación)
eval/preguntas.json     12 preguntas de prueba del agente
results/                métricas generadas (metricas_modelo.*, eval_agente.*)
docs/INFORME.md         informe (≤ 4 páginas)    docs/DECLARACION_IA.md
tests/                  pruebas (BN vs. enumeración, CSP, RAG, agente)
```

## Limitaciones (resumen; ver informe)
- No hay serie pública de incidencia de roya por municipio: la variable `Riesgo` es un **indicador climático de favorabilidad** (regla temperatura + lluvia), no incidencia real. La métrica mide pronóstico de ese indicador.
- La estación/municipio es un proxy de la finca; la altitud cambia mucho la temperatura.
- Datos crudos IDEAM sin validar y con rezago. Calendario con clima esperado por climatología (no pronóstico meteorológico).
- Herramienta analítica: **no es consejo agronómico, médico, legal ni de seguridad**.
