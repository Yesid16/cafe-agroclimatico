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
from .risk_model import RoyaRiskModel, rain_bin as csp_rain_bin

CITA_IDEAM = "[IDEAM datos.gov.co: s54a-sgyg, sbwg-7ju4, uext-mhny]"
AVISO = "Indicador climático, no es diagnóstico de campo ni recomendación agronómica."


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
    base = [m for m in ms if m.split(" / ")[0] == n]
    if len(base) == 1:
        return base[0]
    if len(base) > 1:
        return None
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
        warnings = []
        humidity = last.get("humedad_pct", np.nan)
        if pd.notna(humidity) and humidity < 20:
            warnings.append("Humedad semanal menor a 20%: revisar sensor y unidades.")
        if last["lluvia_mm"] > 500:
            warnings.append("Lluvia semanal mayor a 500 mm: revisar acumulados y sensor.")
        reference = pd.Timestamp(fecha) if fecha else pd.Timestamp.now(tz="America/Bogota").tz_localize(None)
        if (reference - last["semana"]).days > 28:
            warnings.append("El último dato tiene más de cuatro semanas de rezago; el horizonte parte de ese dato.")
        return {"municipio": m, "semana_ultimo_dato": str(last["semana"].date()),
                "avisos_datos": warnings, "semana_objetivo_fin": str((last["semana"] + pd.Timedelta(days=7)).date()),
                "evidencia": ev, "prob_riesgo_semana_siguiente": {k: round(v, 3) for k, v in p.items()},
                "riesgo_mas_probable": best, "lluvia_ultima_semana_mm": round(float(last["lluvia_mm"]), 1),
                "temp_ultima_semana_c": round(float(last["temp_c"]), 1), "aviso": AVISO, "cita": CITA_IDEAM}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def _clima_esperado(m: str, start: pd.Timestamp, horizonte: int) -> list:
    """Categoría de lluvia esperada por semana = moda histórica del municipio para ese mes."""
    mod, w = _model(), _weekly()
    d = w[(w["municipio"] == m) & (w["semana"] <= start)].copy()
    if d.empty:
        raise ValueError("Sin historia anterior a la fecha de referencia")
    q = tuple(np.quantile(d["lluvia_mm"], [1 / 3, 2 / 3]))
    d["cat"] = csp_rain_bin(d["lluvia_mm"], q)
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
        if hectareas <= 0 or capacidad_jornales <= 0:
            return {"error": "Hectáreas y capacidad deben ser positivas."}
        if labores is None:
            labores = ["deshierba", "fertilizacion", "recoleccion"]
        if not labores:
            return {"error": "Seleccione al menos una labor."}
        bad = [l for l in labores if l not in csp_mod.CATALOGO]
        if bad:
            return {"error": f"Labores desconocidas {bad}. Válidas: {list(csp_mod.CATALOGO)}"}
        semanas = int(max(2, min(semanas, 16)))
        w = _weekly()
        d = w[w["municipio"] == m]
        if fecha:
            d = d[d["semana"] <= pd.Timestamp(fecha)]
        if d.empty:
            return {"error": "Sin datos anteriores a la fecha elegida."}
        start = d["semana"].max()
        clima = _clima_esperado(m, start, semanas)
        res = csp_mod.solve([csp_mod.CATALOGO[l] for l in labores], clima, capacidad_jornales, hectareas)
        base = {"municipio": m, "clima_esperado_por_semana": clima, "cita": "[CSP calendario: clima esperado = climatología IDEAM del municipio]",
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
        hits = get_retriever().search(query, k=max(1, min(int(k), 8)))
        if not hits:
            return {"resultados": [], "nota": "No se encontró información relevante en el corpus."}
        return {"resultados": [{"cita": f"[{h['id']}]", "score": h["score"], "texto": h["texto"],
                                  "fuente": h["fuente"], "pagina": h.get("pagina"), "url": h.get("url")} for h in hits]}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


def weather_summary(municipio: str, semanas: int = 6, fecha: str | None = None) -> dict:
    try:
        m = resolve_municipio(municipio)
        if not m:
            return {"error": f"Municipio '{municipio}' no disponible."}
        d = _weekly().query("municipio == @m").sort_values("semana")
        if fecha:
            d = d[d["semana"] <= pd.Timestamp(fecha)]
        d = d.tail(int(max(1, min(semanas, 26))))
        if d.empty:
            return {"error": "Sin datos para la fecha elegida."}
        return {"municipio": m, "semanas": [{"semana": str(r.semana.date()), "lluvia_mm": round(r.lluvia_mm, 1),
                                           "temp_c": round(r.temp_c, 1),
                                           "humedad_pct": None if pd.isna(getattr(r, "humedad_pct", np.nan)) else round(r.humedad_pct, 1)} for r in d.itertuples()], "cita": CITA_IDEAM}
    except Exception as e:  # noqa: BLE001
        return {"error": f"{type(e).__name__}: {e}"}


REGISTRY = {"risk": risk, "schedule": schedule, "search_docs": search_docs, "weather_summary": weather_summary}

SCHEMAS = [
    {"type": "function", "function": {"name": "risk", "description": "Probabilidad de riesgo climático de roya (Bajo/Medio/Alto) para la semana siguiente en un municipio, con una red bayesiana entrenada con datos IDEAM.",
        "parameters": {"type": "object", "properties": {"municipio": {"type": "string"}, "fecha": {"type": "string", "description": "YYYY-MM-DD opcional; por defecto el último dato"}}, "required": ["municipio"]}}},
    {"type": "function", "function": {"name": "schedule", "description": "Calendario de labores (deshierba, fertilizacion, aspersion_roya, recoleccion, poda_zoca) resuelto como CSP con clima esperado y mano de obra.",
        "parameters": {"type": "object", "properties": {"municipio": {"type": "string"}, "labores": {"type": "array", "items": {"type": "string"}},
                       "semanas": {"type": "integer"}, "hectareas": {"type": "number"}, "fecha": {"type": "string"}, "capacidad_jornales": {"type": "number"}}, "required": ["municipio"]}}},
    {"type": "function", "function": {"name": "search_docs", "description": "Busca en el corpus técnico (roya, manejo, labores, clima) y devuelve fragmentos con su cita.",
        "parameters": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}}},
    {"type": "function", "function": {"name": "weather_summary", "description": "Lluvia y temperatura semanales recientes de un municipio (datos IDEAM).",
        "parameters": {"type": "object", "properties": {"municipio": {"type": "string"}, "semanas": {"type": "integer"}, "fecha": {"type": "string"}}, "required": ["municipio"]}}},
]
