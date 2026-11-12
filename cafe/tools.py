"""Herramientas del agente: risk, schedule, search_docs, weather_summary.
Cada una devuelve un dict JSON-serializable con `cita` (etiqueta que el agente debe copiar en su respuesta)
o {"error": "..."} (los errores se devuelven al LLM como observación, no se lanzan)."""
import difflib
from functools import lru_cache

import numpy as np
import pandas as pd

from . import config as C
from . import csp as csp_mod
from .data_prep import norm
from .rag import get_retriever
from .risk_model import RoyaRiskModel

AVISO = "Indicador climático, no es diagnóstico de campo ni recomendación agronómica."


def _data_citation() -> str:
    if C.is_demo_data():
        return "[DEMO: datos sintéticos locales; no son datos IDEAM]"
    return "[IDEAM datos.gov.co: s54a-sgyg, sbwg-7ju4]"


@lru_cache(maxsize=1)
def _weekly() -> pd.DataFrame:
    if not C.WEEKLY.exists():
        raise FileNotFoundError("Falta data/processed/semanal.csv. Ejecute: python -m cafe.data_download && python -m cafe.data_prep")
    return pd.read_csv(C.WEEKLY, parse_dates=["semana"])


@lru_cache(maxsize=1)
def _model() -> RoyaRiskModel:
    if not C.MODEL_PATH.exists():
        raise FileNotFoundError("Falta el modelo. Ejecute: python -m cafe.risk_model")
    return RoyaRiskModel.load()


def clear_caches():
    _weekly.cache_clear()
    _model.cache_clear()


def municipios() -> list:
    return sorted(_weekly()["municipio"].unique())


def resolve_municipio(txt: str):
    ms = municipios()
    n = norm(txt or "")
    if n in ms:
        return n
    m = difflib.get_close_matches(n, ms, n=1, cutoff=0.75)
    return m[0] if m else None


def risk(municipio: str, fecha: str | None = None) -> dict:
    try:
        m = resolve_municipio(municipio)
        if not m:
            return {"error": f"Municipio '{municipio}' no disponible. Disponibles: {', '.join(municipios()[:25])}"}
        mod, w = _model(), _weekly()
        got = mod.evidence_for(w, m, fecha)
        if got is None:
            return {"error": f"Sin datos suficientes para {m} hasta {fecha}."}
        ev, last = got
        p = mod.predict_proba(ev)
        best = max(p, key=p.get)
        return {"municipio": m, "semana_ultimo_dato": str(last["semana"].date()),
                "evidencia": ev, "prob_riesgo_semana_siguiente": {k: round(v, 3) for k, v in p.items()},
                "riesgo_mas_probable": best, "lluvia_ultima_semana_mm": round(float(last["lluvia_mm"]), 1),
                "temp_ultima_semana_c": round(float(last["temp_c"]), 1), "aviso": AVISO, "cita": _data_citation()}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def _clima_esperado(m: str, start: pd.Timestamp, horizonte: int) -> list:
    """Categoría de lluvia esperada por semana = moda histórica del municipio para ese mes."""
    mod, w = _model(), _weekly()
    d = w[w["municipio"] == m].copy()
    d["cat"] = pd.cut(d["lluvia_mm"], [-np.inf, mod.q[0], mod.q[1], np.inf], labels=["Baja", "Media", "Alta"])
    d["mes"] = d["semana"].dt.month
    moda = d.groupby("mes")["cat"].agg(lambda s: s.value_counts().idxmax() if len(s.dropna()) else "Media")
    out = []
    for i in range(horizonte):
        mes = (start + pd.Timedelta(days=7 * (i + 1))).month
        out.append(str(moda.get(mes, "Media")))
    return out


def schedule(municipio: str, labores: list | None = None, semanas: int = 8, hectareas: float = 1.0,
             capacidad_jornales: float = 30.0, fecha: str | None = None) -> dict:
    try:
        m = resolve_municipio(municipio)
        if not m:
            return {"error": f"Municipio '{municipio}' no disponible."}
        labores = labores or ["deshierba", "fertilizacion", "aspersion_roya", "recoleccion"]
        bad = [l for l in labores if l not in csp_mod.CATALOGO]
        if bad:
            return {"error": f"Labores desconocidas {bad}. Válidas: {list(csp_mod.CATALOGO)}"}
        semanas = int(max(2, min(semanas, 16)))
        w = _weekly()
        d = w[w["municipio"] == m]
        if fecha:
            d = d[d["semana"] <= pd.Timestamp(fecha)]
        start = d["semana"].max()
        clima = _clima_esperado(m, start, semanas)
        res = csp_mod.solve([csp_mod.CATALOGO[l] for l in labores], clima, capacidad_jornales, hectareas)
        source = "datos sintéticos de demostración" if C.is_demo_data() else "climatología IDEAM del municipio"
        base = {"municipio": m, "clima_esperado_por_semana": clima, "cita": f"[CSP calendario: clima esperado = {source}]",
                "aviso": "Calendario orientativo; valide con el extensionista y el pronóstico oficial del IDEAM."}
        if not res.ok:
            return {**base, "factible": False, "motivo": res.motivo, "nodos": res.nodos}
        cal = []
        for n, s in sorted(res.asignacion.items(), key=lambda kv: kv[1]):
            ini = start + pd.Timedelta(days=7 * (s + 1) - 6)
            cal.append({"labor": n, "semana_inicio": s + 1, "duracion_sem": csp_mod.CATALOGO[n].duracion,
                        "fecha_inicio_aprox": str(ini.date()), "lluvia_esperada": clima[s]})
        return {**base, "factible": True, "calendario": cal, "nodos": res.nodos}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def search_docs(query: str, k: int = 4) -> dict:
    try:
        hits = get_retriever().search(query, k=k)
        if not hits:
            return {"resultados": [], "nota": "No se encontró información relevante en el corpus."}
        return {"resultados": [{"cita": f"[{h['id']}]", "score": h["score"], "texto": h["texto"]} for h in hits]}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def weather_summary(municipio: str, semanas: int = 6) -> dict:
    try:
        m = resolve_municipio(municipio)
        if not m:
            return {"error": f"Municipio '{municipio}' no disponible."}
        d = _weekly().query("municipio == @m").tail(int(max(1, min(semanas, 26))))
        return {"municipio": m, "semanas": [{"semana": str(r.semana.date()), "lluvia_mm": round(r.lluvia_mm, 1),
                                           "temp_c": round(r.temp_c, 1)} for r in d.itertuples()], "cita": _data_citation()}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


REGISTRY = {"risk": risk, "schedule": schedule, "search_docs": search_docs, "weather_summary": weather_summary}

SCHEMAS = [
    {"type": "function", "function": {"name": "risk", "description": "Probabilidad de riesgo climático de roya (Bajo/Medio/Alto) para la semana siguiente en un municipio, con una red bayesiana entrenada con datos IDEAM.",
        "parameters": {"type": "object", "properties": {"municipio": {"type": "string"}, "fecha": {"type": "string", "description": "YYYY-MM-DD opcional; por defecto el último dato"}}, "required": ["municipio"]}}},
    {"type": "function", "function": {"name": "schedule", "description": "Calendario de labores (deshierba, fertilizacion, aspersion_roya, recoleccion, poda_zoca) resuelto como CSP con clima esperado y mano de obra.",
        "parameters": {"type": "object", "properties": {"municipio": {"type": "string"}, "labores": {"type": "array", "items": {"type": "string"}},
                       "semanas": {"type": "integer"}, "hectareas": {"type": "number"}, "capacidad_jornales": {"type": "number"}}, "required": ["municipio"]}}},
    {"type": "function", "function": {"name": "search_docs", "description": "Busca en el corpus técnico (roya, manejo, labores, clima) y devuelve fragmentos con su cita.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "weather_summary", "description": "Lluvia y temperatura semanales recientes de un municipio (datos IDEAM).",
        "parameters": {"type": "object", "properties": {"municipio": {"type": "string"}, "semanas": {"type": "integer"}}, "required": ["municipio"]}}},
]
