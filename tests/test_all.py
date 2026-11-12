import numpy as np
import pandas as pd
import pytest

from cafe import config as C
from cafe import csp, data_prep, risk_model, tools
from cafe.agent import run_agent
from cafe.bayes_net import DiscreteBN
from cafe.rag import Retriever
from tests.synthetic import make_raw


@pytest.fixture(scope="module")
def pipeline(tmp_path_factory):
    d = tmp_path_factory.mktemp("d")
    make_raw(d)
    C.PRECIP_DAILY, C.TEMP_DAILY = d / "precip_diaria.csv", d / "temp_diaria.csv"
    C.WEEKLY, C.MODEL_PATH = d / "semanal.csv", d / "m.pkl"
    data_prep.build_weekly().to_csv(C.WEEKLY, index=False)
    w = pd.read_csv(C.WEEKLY, parse_dates=["semana"])
    risk_model.RoyaRiskModel().fit(w).save(C.MODEL_PATH)
    tools.clear_caches()
    return w


def test_bn_ve_equals_bruteforce():
    rng = np.random.default_rng(1)
    st = {"A": ["a0", "a1"], "B": ["b0", "b1", "b2"], "C": ["c0", "c1"], "D": ["d0", "d1"]}
    df = pd.DataFrame({k: rng.choice(v, 400) for k, v in st.items()})
    bn = DiscreteBN({"A": [], "B": ["A"], "C": ["A", "B"], "D": ["C"]}, st).fit(df)
    for ev in [{}, {"B": "b1"}, {"A": "a0", "D": "d1"}]:
        p, q = bn.query("C", ev), bn.query_bruteforce("C", ev)
        assert all(abs(p[k] - q[k]) < 1e-9 for k in p)
        assert abs(sum(p.values()) - 1) < 1e-9


def test_weekly_and_model(pipeline):
    assert pipeline["municipio"].nunique() == 4
    out = risk_model.evaluate(pipeline)
    names = [r["modelo"] for r in out["resultados"]]
    assert len(names) == 4 and out["n_test"] > 50
    p = tools._model().predict_proba({"Trim": "MAM", "Lluvia": "Alta"})  # evidencia parcial
    assert abs(sum(p.values()) - 1) < 1e-9


def test_csp_respects_constraints():
    clima = ["Media", "Baja", "Media", "Alta", "Media", "Media", "Baja", "Media"]
    labs = [csp.CATALOGO[n] for n in ("deshierba", "fertilizacion", "aspersion_roya", "recoleccion")]
    r = csp.solve(labs, clima, capacidad=20)
    assert r.ok
    a = r.asignacion
    assert a["deshierba"] < a["fertilizacion"] and clima[a["fertilizacion"]] == "Media"
    assert abs(a["fertilizacion"] - a["aspersion_roya"]) >= 1
    assert all(clima[w] != "Alta" for w in range(a["recoleccion"], a["recoleccion"] + 2))
    naive = csp.solve(labs, clima, capacidad=20, smart=False)
    assert naive.ok and r.nodos <= naive.nodos + 5


def test_csp_infeasible_has_reason():
    r = csp.solve([csp.CATALOGO["fertilizacion"]], ["Alta"] * 6, 30)
    assert not r.ok and "fertilizacion" in r.motivo


def test_rag():
    hits = Retriever(backend="tfidf").search("condiciones que favorecen la roya temperatura lluvia")
    assert hits and hits[0]["fuente"].startswith("notas_")


def test_agent_tools_and_errors(pipeline):
    mun = tools.municipios()[0]
    o = run_agent(f"¿Cuál es el riesgo de roya en {mun.title()}?", {"municipio": mun}, force_mock=True)
    expected_source = "[DEMO" if C.is_demo_data() else "[IDEAM"
    assert [t["tool"] for t in o["trace"]] == ["risk"] and expected_source in o["answer"]
    o = run_agent("Dame el riesgo de roya en Atlantis", {}, force_mock=True)
    assert "error" in o["trace"][0]["result"]
    o = run_agent("¿Cuál es el precio del dólar hoy?", {}, force_mock=True)
    assert o["trace"] == []
