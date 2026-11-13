"""Regresiones de datos, temporalidad y errores del agente. Sin red ni modelos grandes."""
from datetime import date
from types import SimpleNamespace
import json
import numpy as np
import pandas as pd
import pytest
from cafe import config as C, data_prep, tools
from cafe.data_download import _months
from cafe.evaluate_agent import score_case
from cafe.agent import run_agent
from cafe.risk_model import build_dataset, humidity_bin
from cafe import csp


def test_download_respects_partial_months():
    assert list(_months(date(2024, 1, 17), date(2024, 2, 3))) == [
        (date(2024, 1, 17), date(2024, 2, 1)),
        (date(2024, 2, 1), date(2024, 2, 4))]
    with pytest.raises(ValueError):
        list(_months(date(2024, 3, 1), date(2024, 2, 1)))


def test_hourly_data_quality_and_duplicates(tmp_path):
    df = pd.DataFrame({
        'codigoestacion': ['001', '001', '001'], 'municipio': ['Jardín'] * 3,
        'departamento': ['Antioquia'] * 3, 'latitud': [5.6] * 3, 'longitud': [-75.8] * 3,
        'dia': ['2024-01-01', '2024-01-02', '2024-01-03'], 'valor': [22, 23, 24],
        'n': [24, 11, 12], 'n_total': [24, 11, 13]})
    p = tmp_path / 'hourly.csv'
    df.to_csv(p, index=False)
    valid = data_prep._municipio_dia(p, 'temp_c', C.MIN_N_DAY_TEMP)
    assert len(valid) == 1 and valid.iloc[0].temp_c == 22
    pd.concat([df, df.iloc[:1]]).to_csv(p, index=False)
    with pytest.raises(ValueError, match='duplicada'):
        data_prep._municipio_dia(p, 'temp_c', C.MIN_N_DAY_TEMP)


def test_missing_weeks_are_not_shifted_as_consecutive():
    w = pd.DataFrame({'municipio': ['A / CALDAS'] * 4,
        'semana': pd.to_datetime(['2024-01-07', '2024-01-14', '2024-01-28', '2024-02-04']),
        'lluvia_mm': [20., 30., 40., 50.], 'temp_c': [22.] * 4})
    assert build_dataset(w, (25., 45.)).empty
    assert humidity_bin(np.nan) == 'SinDato'
    assert humidity_bin(90) == 'Desde80'


def test_homonymous_municipality_must_be_qualified(monkeypatch):
    monkeypatch.setattr(tools, 'municipios', lambda: ['ARMENIA / ANTIOQUIA', 'ARMENIA / QUINDIO'])
    assert tools.resolve_municipio('Armenia') is None
    assert tools.resolve_municipio('Armenia / Quindío') == 'ARMENIA / QUINDIO'


def test_climatology_excludes_future(monkeypatch):
    w = pd.DataFrame({'municipio': ['A'] * 3, 'semana': pd.to_datetime(['2023-01-08', '2023-01-15', '2025-01-05']),
                      'lluvia_mm': [20., 30., 10000.]})
    monkeypatch.setattr(tools, '_weekly', lambda: w)
    monkeypatch.setattr(tools, '_model', lambda: SimpleNamespace(q=(25., 40.)))
    before = tools._clima_esperado('A', pd.Timestamp('2024-01-07'), 2)
    w.loc[2, 'lluvia_mm'] = 0
    assert tools._clima_esperado('A', pd.Timestamp('2024-01-07'), 2) == before


def test_failed_tool_and_invented_citation_do_not_pass():
    q = {'tools': ['risk'], 'cita': True}
    out = {'trace': [{'tool': 'risk', 'result': {'error': 'sin datos'}}], 'answer': '[IDEAM]'}
    result = score_case(q, out)
    assert not result['herramienta_ok'] and not result['cita_ok']
    out = {'trace': [{'tool': 'risk', 'result': {'cita': '[IDEAM]'}}], 'answer': '[IDEAM] [inventada]'}
    assert not score_case(q, out)['cita_ok']


def test_llm_failure_is_visible(monkeypatch):
    import openai
    def fail(**kwargs):
        raise RuntimeError('provider unavailable')
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=fail)))
    monkeypatch.setattr(openai, 'OpenAI', lambda **kwargs: client)
    monkeypatch.setattr(C, 'LLM_API_KEY', 'test')
    out = run_agent('precio del dólar')
    assert out['mode'] == 'fallback' and out['llm_error'] == 'RuntimeError'


def test_agent_iteration_limit_and_context(monkeypatch):
    import openai
    invocations, calls = [], []
    tc = SimpleNamespace(id='test-call', function=SimpleNamespace(name='weather_summary', arguments='{"municipio":"A"}'))
    tc.model_dump = lambda **kwargs: {'id': tc.id, 'type': 'function',
        'function': {'name': tc.function.name, 'arguments': tc.function.arguments}}
    msg = SimpleNamespace(content=None, tool_calls=[tc])
    def create(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    monkeypatch.setattr(openai, 'OpenAI', lambda **kwargs: client)
    monkeypatch.setattr(C, 'LLM_API_KEY', 'test')
    monkeypatch.setattr(C, 'T_MAX', 2)
    monkeypatch.setitem(tools.REGISTRY, 'weather_summary',
        lambda **kwargs: invocations.append(kwargs) or {'municipio':'A', 'semanas':[], 'cita':'[IDEAM]'})
    out = run_agent('clima en A', {'fecha':'2024-01-07'})
    assert len(calls) == 2 and out['exhausted']
    assert all(x['fecha'] == '2024-01-07' for x in invocations)


def test_csp_budget_does_not_claim_infeasibility():
    labs = [csp.CATALOGO['deshierba'], csp.CATALOGO['fertilizacion']]
    r = csp.solve(labs, ['Media'] * 4, capacidad=20, max_nodos=1)
    assert not r.ok and 'no determinada' in r.motivo
    assert r.nodos <= 1

def test_temperature_dense_sampling_needs_hours(tmp_path):
    df = pd.DataFrame({'codigoestacion':['A','A'], 'municipio':['M','M'], 'departamento':['D','D'],
        'latitud':[5,5], 'longitud':[-75,-75], 'dia':['2024-01-01','2024-01-02'],
        'valor':[22,22], 'n':[144,24], 'horas':[2,24]})
    p = tmp_path / 'dense.csv'
    df.to_csv(p,index=False)
    valid = data_prep._municipio_dia(p,'temp_c',12)
    assert len(valid) == 1 and valid.iloc[0].dia == pd.Timestamp('2024-01-02')


def test_weekly_keeps_homonyms_and_humidity(tmp_path, monkeypatch):
    days = pd.date_range('2024-01-01', periods=14, freq='D')
    frames = []
    for code,dep in [('A','Antioquia'),('B','Quindío')]:
        frames.append(pd.DataFrame({'codigoestacion':code,'municipio':'Armenia','departamento':dep,
            'latitud':5,'longitud':-75,'dia':days,'valor':22,'n':144}))
    raw = pd.concat(frames)
    paths = []
    for name,value in [('p',10),('t',22),('h',90)]:
        p = tmp_path / (name+'.csv')
        raw.assign(valor=value).to_csv(p,index=False)
        paths.append(p)
    monkeypatch.setattr(C,'PRECIP_DAILY',paths[0])
    monkeypatch.setattr(C,'TEMP_DAILY',paths[1])
    monkeypatch.setattr(C,'HUM_DAILY',paths[2])
    monkeypatch.setattr(C,'MIN_WEEKS_MUNICIPIO',2)
    w = data_prep.build_weekly()
    assert set(w.municipio) == {'ARMENIA / ANTIOQUIA','ARMENIA / QUINDIO'}
    assert w.humedad_pct.eq(90).all()


def test_rag_pdf_citation_has_page(tmp_path):
    from cafe.rag import Retriever
    from pypdf import PdfWriter
    # Corpus real descargado: comprobar estructura sin depender del orden de scores.
    pdfs = list(C.CORPUS_DIR.glob('*.pdf'))
    if not pdfs:
        pytest.skip('Corpus original aún no descargado')
    retriever = Retriever()
    official = [h for h in retriever.chunks if h['fuente'].endswith('.pdf')]
    assert official and all(h['pagina'] >= 1 and ':p' in h['id'] for h in official)
