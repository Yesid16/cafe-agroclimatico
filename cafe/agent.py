"""Agente LLM con loop agéntico manual (T_max), RAG y 4 herramientas.

- Con LLM_API_KEY: usa un endpoint compatible con OpenAI (Groq, NVIDIA NIM, Ollama...).
- Sin clave: modo "mock" determinista (enrutador por palabras clave + respuesta compuesta
  desde las observaciones). Sirve para pruebas reproducibles y como plan B de la demo.
Los errores de las herramientas se devuelven al modelo como observación.
"""
import json
import re

from . import config as C
from . import tools as T

SYSTEM = """Eres un asistente agroclimático para caficultores de Antioquia y el Eje Cafetero.
Reglas:
1. Para datos, riesgo o calendarios usa SIEMPRE las herramientas; no inventes cifras. Para conceptos técnicos usa search_docs.
2. Responde en español, breve y claro. Copia literalmente las etiquetas de cita (campo "cita", p. ej. [archivo.md#2]) de las herramientas que uses.
3. El riesgo es un indicador CLIMÁTICO de favorabilidad de la roya, no incidencia medida. No des consejo médico, legal ni de seguridad ni dosis de agroquímicos; remite al extensionista del Comité de Cafeteros.
4. Si el municipio no está claro, usa el del contexto. Si una herramienta devuelve error, explícalo y propón alternativa.
5. Si la pregunta no es sobre café, clima o labores agrícolas, di amablemente que está fuera de tu alcance y no llames herramientas."""

OUT_OF_SCOPE = "Esa consulta está fuera de mi alcance: solo puedo ayudar con clima, riesgo de roya y labores del café en Antioquia y el Eje Cafetero."
LABOR_WORDS = {"deshierba": "deshierba", "fertiliz": "fertilizacion", "aspers": "aspersion_roya", "fumig": "aspersion_roya",
               "cosech": "recoleccion", "recolec": "recoleccion", "poda": "poda_zoca", "zoca": "poda_zoca"}
KW_RISK = ("riesgo", "probabilidad", "roya hoy", "roya esta", "roya en", "pronóstico", "pronostico", "alto", "próxima semana", "proxima semana")
KW_SCHED = ("calendario", "cronograma", "programa", "planifica", "cuándo", "cuando", "semana para", "labores")
KW_DOCS = ("qué es", "que es", "síntoma", "sintoma", "cómo", "como ", "condiciones", "favorece", "manejo", "umbral", "recomend", "por qué", "porque", "explica", "variedad", "control")
KW_WEATHER = ("lluvia", "llovió", "llovio", "temperatura", "últimas semanas", "ultimas semanas", "clima reciente", "histórico", "historico")
KW_AGRO = KW_RISK + KW_SCHED + KW_DOCS + KW_WEATHER + ("café", "cafe", "roya", "cosecha", "finca", "cultivo", "fertiliz")


def _find_municipio(q: str, ctx: dict):
    from .data_prep import norm
    nq = norm(q)
    try:
        for m in T.municipios():
            if m in nq:
                return m
    except Exception:  # noqa: BLE001
        pass
    cand = re.search(r"\ben ([A-ZÁÉÍÓÚÑ][\wáéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][\wáéíóúñ]+)*)", q)  # municipio nombrado pero desconocido
    return cand.group(1) if cand else ctx.get("municipio")


def _mock_plan(q: str, ctx: dict):
    ql = q.lower()
    if not any(k in ql for k in KW_AGRO):
        return []
    mun = _find_municipio(q, ctx)
    explicit_mun = _find_municipio(q, {}) is not None
    plan = []
    labores = sorted({v for k, v in LABOR_WORDS.items() if k in ql})
    if any(k in ql for k in KW_SCHED) or (labores and explicit_mun and any(w in ql for w in ("cuándo", "cuando", "programo"))):
        args = {"municipio": mun}
        if labores:
            args["labores"] = labores
        plan.append(("schedule", args))
    if any(k in ql for k in KW_RISK):
        plan.append(("risk", {"municipio": mun}))
    if any(k in ql for k in KW_WEATHER):
        plan.append(("weather_summary", {"municipio": mun}))
    if any(k in ql for k in KW_DOCS) or not plan:
        plan.append(("search_docs", {"query": q}))
    return plan


def _compose(q: str, obs: list) -> str:
    if not obs:
        return OUT_OF_SCOPE
    parts = []
    for name, res in obs:
        if "error" in res:
            parts.append(f"No pude completar '{name}': {res['error']}")
        elif name == "risk":
            p = res["prob_riesgo_semana_siguiente"]
            parts.append(f"En {res['municipio']} (último dato: semana del {res['semana_ultimo_dato']}; lluvia {res['lluvia_ultima_semana_mm']} mm, "
                         f"{res['temp_ultima_semana_c']} °C) el riesgo climático de roya más probable para la próxima semana es **{res['riesgo_mas_probable']}** "
                         f"(Bajo {p['Bajo']:.0%}, Medio {p['Medio']:.0%}, Alto {p['Alto']:.0%}). {res['aviso']} {res['cita']}")
        elif name == "schedule":
            if res.get("factible"):
                items = "; ".join(f"{c['labor']}: semana {c['semana_inicio']} (~{c['fecha_inicio_aprox']}, lluvia esperada {c['lluvia_esperada']})" for c in res["calendario"])
                parts.append(f"Calendario sugerido para {res['municipio']}: {items}. {res['aviso']} {res['cita']}")
            else:
                parts.append(f"No fue posible armar el calendario: {res['motivo']} {res['cita']}")
        elif name == "weather_summary":
            s = ", ".join(f"{x['semana']}: {x['lluvia_mm']} mm/{x['temp_c']} °C" for x in res["semanas"])
            parts.append(f"Clima semanal reciente en {res['municipio']}: {s}. {res['cita']}")
        elif name == "search_docs":
            if not res.get("resultados"):
                parts.append("No encontré información sobre eso en el corpus disponible.")
            else:
                for h in res["resultados"][:2]:
                    parts.append(re.sub(r"\s+", " ", h["texto"])[:420] + "… " + h["cita"])
    return "\n\n".join(parts)


def run_agent(question: str, context: dict | None = None, history: list | None = None, force_mock: bool = False) -> dict:
    ctx = context or {}
    trace = []
    use_llm = bool(C.LLM_API_KEY) and not force_mock
    if not use_llm:
        obs = []
        for name, args in _mock_plan(question, ctx):
            res = T.REGISTRY[name](**args)
            trace.append({"tool": name, "args": args, "result": res})
            obs.append((name, res))
        return {"answer": _compose(question, obs), "trace": trace, "mode": "mock", "iterations": 1}

    from openai import OpenAI
    client = OpenAI(api_key=C.LLM_API_KEY, base_url=C.LLM_BASE_URL)
    sys_msg = SYSTEM + (f"\nContexto de la interfaz: {json.dumps(ctx, ensure_ascii=False)}" if ctx else "")
    messages = [{"role": "system", "content": sys_msg}] + (history or []) + [{"role": "user", "content": question}]
    for it in range(1, C.T_MAX + 1):
        try:
            resp = client.chat.completions.create(model=C.LLM_MODEL, messages=messages, tools=T.SCHEMAS,
                                                   tool_choice="auto", temperature=0.2)
        except Exception as e:  # noqa: BLE001  (fallo de red/clave → degrada a mock)
            out = run_agent(question, ctx, history, force_mock=True)
            out["answer"] = f"(LLM no disponible: {type(e).__name__}; respuesta en modo local)\n\n" + out["answer"]
            return out
        msg = resp.choices[0].message
        if not msg.tool_calls:
            return {"answer": msg.content or "", "trace": trace, "mode": "llm", "iterations": it}
        messages.append(msg.model_dump(exclude_none=True))
        for tc in msg.tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
                fn = T.REGISTRY.get(tc.function.name)
                res = fn(**args) if fn else {"error": f"Herramienta desconocida: {tc.function.name}"}
            except Exception as e:  # noqa: BLE001
                args, res = {}, {"error": f"{type(e).__name__}: {e}"}
            trace.append({"tool": tc.function.name, "args": args, "result": res})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(res, ensure_ascii=False)[:6000]})
    messages.append({"role": "user", "content": "Responde ya con la información reunida, sin más herramientas."})
    resp = client.chat.completions.create(model=C.LLM_MODEL, messages=messages, temperature=0.2)
    return {"answer": (resp.choices[0].message.content or "") + "\n\n(Se alcanzó el máximo de iteraciones.)",
            "trace": trace, "mode": "llm", "iterations": C.T_MAX}
