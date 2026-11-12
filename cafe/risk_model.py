"""Modelo de riesgo agroclimático de roya (Parte 1) con red bayesiana propia.

IMPORTANTE (limitación declarada): no existe una serie pública de incidencia real de roya a
nivel de municipio-semana. La variable objetivo `Riesgo` es un INDICADOR CLIMÁTICO DE
FAVORABILIDAD definido por una regla parametrizable (temperatura óptima + lluvia reciente),
inspirada en la literatura (la roya se favorece con 21–25 °C y agua libre sobre la hoja).
La red aprende a PRONOSTICAR ese indicador para la semana siguiente a partir de lo observado
hoy. La métrica mide capacidad de pronóstico climático, NO validación contra incidencia en campo.
"""
import json
import pickle

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score

from . import config as C
from .bayes_net import DiscreteBN

TRIM = {12: "DEF", 1: "DEF", 2: "DEF", 3: "MAM", 4: "MAM", 5: "MAM",
        6: "JJA", 7: "JJA", 8: "JJA", 9: "SON", 10: "SON", 11: "SON"}
STATES = {
    "Trim": ["DEF", "MAM", "JJA", "SON"],
    "Lluvia_prev": ["Baja", "Media", "Alta"],
    "Lluvia": ["Baja", "Media", "Alta"],
    "Temp": ["Fria", "Fresca", "Optima", "Calida"],
    "Riesgo": ["Bajo", "Medio", "Alto"],
}
STRUCTURE = {
    "Trim": [],
    "Lluvia_prev": ["Trim"],
    "Lluvia": ["Trim", "Lluvia_prev"],
    "Temp": ["Trim"],
    "Riesgo": ["Trim", "Lluvia_prev", "Lluvia", "Temp"],
}
TEMP_EDGES = (18.0, 21.0, 25.0)  # Fria <18 | Fresca 18–21 | Optima 21–25 | Calida >25


def temp_bin(t):
    a, b, c = TEMP_EDGES
    return np.select([t < a, t < b, t < c], ["Fria", "Fresca", "Optima"], "Calida")


def rain_bin(x, q):
    return np.select([x < q[0], x < q[1]], ["Baja", "Media"], "Alta")


def risk_rule(rain2w, temp, q):
    """Regla de favorabilidad: puntaje temperatura (0–2) + lluvia 2 semanas (0–2)."""
    ts = np.select([temp < TEMP_EDGES[0], temp < TEMP_EDGES[1], temp < TEMP_EDGES[2]], [0, 1, 2], 1)
    rs = np.select([rain2w < q[0], rain2w < q[1]], [0, 1], 2)
    s = ts + rs
    return np.select([s <= 1, s == 2], ["Bajo", "Medio"], "Alto")


def build_dataset(weekly: pd.DataFrame, q) -> pd.DataFrame:
    """Una fila por (municipio, semana t) con evidencia en t y objetivo Riesgo en t+1."""
    rows = []
    for mun, d in weekly.groupby("municipio"):
        d = d.set_index("semana").sort_index()
        d = d[~d.index.duplicated()].asfreq("7D")  # semanas faltantes → NaN
        d["rain2w"] = (d["lluvia_mm"] + d["lluvia_mm"].shift(1)) / 2
        f = pd.DataFrame(index=d.index)
        f["municipio"] = mun
        f["Lluvia"] = np.where(d["lluvia_mm"].notna(), rain_bin(d["lluvia_mm"], q), None)
        f["Lluvia_prev"] = f["Lluvia"].shift(1)
        f["Temp"] = np.where(d["temp_c"].notna(), temp_bin(d["temp_c"]), None)
        ok = d["rain2w"].notna() & d["temp_c"].notna()
        r = pd.Series(np.where(ok, risk_rule(d["rain2w"], d["temp_c"], q), None), index=d.index)
        f["Riesgo_t"] = r
        f["Riesgo"] = r.shift(-1)
        f["Trim"] = [TRIM[(i + pd.Timedelta(days=7)).month] for i in d.index]
        rows.append(f.reset_index().rename(columns={"index": "semana"}))
    out = pd.concat(rows, ignore_index=True)
    return out.dropna(subset=["Lluvia", "Lluvia_prev", "Temp", "Riesgo_t", "Riesgo"]).reset_index(drop=True)


class RoyaRiskModel:
    def __init__(self):
        self.q = None
        self.bn = None
        self.cutoff = None

    def fit(self, weekly: pd.DataFrame, cutoff=None):
        train_w = weekly if cutoff is None else weekly[weekly["semana"] <= cutoff]
        self.q = tuple(np.quantile(train_w["lluvia_mm"], [1 / 3, 2 / 3]))  # terciles SOLO de entrenamiento
        ds = build_dataset(weekly, self.q)
        tr = ds if cutoff is None else ds[ds["semana"] <= cutoff - pd.Timedelta(days=7)]  # sin fuga del objetivo
        self.bn = DiscreteBN(STRUCTURE, STATES, alpha=1.0).fit(tr)
        self.cutoff = cutoff
        return self

    def predict_proba(self, evidence: dict) -> dict:
        """evidence puede ser parcial (p. ej. sin Temp): la variable oculta se marginaliza."""
        return self.bn.query("Riesgo", evidence)

    def evidence_for(self, weekly: pd.DataFrame, municipio: str, fecha=None):
        d = weekly[weekly["municipio"] == municipio].sort_values("semana")
        if fecha is not None:
            d = d[d["semana"] <= pd.Timestamp(fecha)]
        if len(d) < 2:
            return None
        last, prev = d.iloc[-1], d.iloc[-2]
        ev = {"Trim": TRIM[(last["semana"] + pd.Timedelta(days=7)).month],
              "Lluvia": str(rain_bin(last["lluvia_mm"], self.q)),
              "Temp": str(temp_bin(last["temp_c"]))}
        if (last["semana"] - prev["semana"]).days == 7:
            ev["Lluvia_prev"] = str(rain_bin(prev["lluvia_mm"], self.q))
        return ev, last

    def save(self, path=None):
        with open(path or C.MODEL_PATH, "wb") as fh:
            pickle.dump(self, fh)

    @staticmethod
    def load(path=None):
        with open(path or C.MODEL_PATH, "rb") as fh:
            return pickle.load(fh)


# ------------------------------ Evaluación ------------------------------
def _onehot(df):
    return pd.get_dummies(df[["Trim", "Lluvia_prev", "Lluvia", "Temp", "Riesgo_t"]]).astype(float)


def _logloss(P, y, classes):
    idx = [classes.index(v) for v in y]
    return float(-np.mean(np.log(np.clip(np.asarray(P)[np.arange(len(y)), idx], 1e-6, 1))))


def _brier(P, y, classes):
    Y = np.eye(len(classes))[[classes.index(v) for v in y]]
    return float(np.mean(np.sum((P - Y) ** 2, axis=1)))


def evaluate(weekly: pd.DataFrame, test_frac: float = 0.2) -> dict:
    semanas = np.sort(weekly["semana"].unique())
    cutoff = pd.Timestamp(semanas[int(len(semanas) * (1 - test_frac))])
    model = RoyaRiskModel().fit(weekly, cutoff=cutoff)
    ds = build_dataset(weekly, model.q)
    train = ds[ds["semana"] <= cutoff - pd.Timedelta(days=7)]
    test = ds[ds["semana"] > cutoff].reset_index(drop=True)
    cls = STATES["Riesgo"]
    y = test["Riesgo"].tolist()

    # Red bayesiana (VE con caché por combinación de evidencia)
    cache = {}
    P = []
    for _, r in test.iterrows():
        key = (r.Trim, r.Lluvia_prev, r.Lluvia, r.Temp)
        if key not in cache:
            p = model.predict_proba(dict(zip(["Trim", "Lluvia_prev", "Lluvia", "Temp"], key)))
            cache[key] = [p[c] for c in cls]
        P.append(cache[key])
    P = np.array(P)

    # Líneas base
    maj = train["Riesgo"].mode()[0]
    prior = train["Riesgo"].value_counts(normalize=True).reindex(cls).fillna(0).values
    P_maj = np.tile(prior, (len(test), 1))
    P_per = np.full((len(test), 3), 0.05)
    for i, v in enumerate(test["Riesgo_t"]):
        P_per[i, cls.index(v)] = 0.90
    Xtr, Xte = _onehot(train), _onehot(test).reindex(columns=_onehot(train).columns, fill_value=0.0)
    lr = LogisticRegression(max_iter=1000).fit(Xtr, train["Riesgo"])
    P_lr = lr.predict_proba(Xte)
    full = np.zeros((len(test), len(cls)))
    for j, c in enumerate(lr.classes_):
        full[:, cls.index(c)] = P_lr[:, j]
    P_lr = full

    def metrics(name, P_, pred):
        return {"modelo": name, "accuracy": round(accuracy_score(y, pred), 4),
                "f1_macro": round(f1_score(y, pred, average="macro", labels=cls), 4),
                "brier": round(_brier(P_, y, cls), 4),
                "log_loss": round(_logloss(P_, y, cls), 4)}

    res = [metrics("Mayoritaria (línea base 1)", P_maj, [maj] * len(test)),
           metrics("Persistencia Riesgo_t (línea base 2)", P_per, test["Riesgo_t"].tolist()),
           metrics("Regresión logística (referencia sklearn)", P_lr, lr.predict(Xte).tolist()),
           metrics("Red bayesiana propia (VE)", P, [cls[i] for i in P.argmax(1)])]
    out = {"cutoff": str(cutoff.date()), "n_train": len(train), "n_test": len(test),
           "parametros_red": model.bn.n_params(), "distribucion_test": test["Riesgo"].value_counts().to_dict(),
           "resultados": res}
    return out


def main():
    weekly = pd.read_csv(C.WEEKLY, parse_dates=["semana"])
    out = evaluate(weekly)
    C.RESULTS_DIR.mkdir(exist_ok=True)
    (C.RESULTS_DIR / "metricas_modelo.json").write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    md = [f"Corte temporal: entrenamiento ≤ {out['cutoff']}; n_train={out['n_train']}, n_test={out['n_test']}; "
          f"parámetros de la red={out['parametros_red']}.", "",
          "| Modelo | Accuracy | F1 macro | Brier | Log-loss |", "|---|---|---|---|---|"]
    md += [f"| {r['modelo']} | {r['accuracy']} | {r['f1_macro']} | {r['brier']} | {r['log_loss']} |" for r in out["resultados"]]
    (C.RESULTS_DIR / "metricas_modelo.md").write_text("\n".join(md), encoding="utf-8")
    print("\n".join(md))
    # modelo final: entrena con todos los datos para pronosticar hacia adelante
    from cafe.risk_model import RoyaRiskModel as _M  # evita pickle con módulo __main__
    _M().fit(weekly).save()
    C.DEMO_MARKER.unlink(missing_ok=True)
    print("Modelo guardado en", C.MODEL_PATH)


if __name__ == "__main__":
    main()
