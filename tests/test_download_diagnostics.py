"""Diagnóstico de errores de descarga y salida de procesos en notebooks; sin red."""
from pathlib import Path
import runpy

import pytest
import requests
from cafe import data_download


def test_retry_reports_provider_error(monkeypatch, capsys):
    response = requests.Response()
    response.status_code = 503
    response._content = b'upstream temporarily unavailable'
    attempts = []
    def fail(*args, **kwargs):
        attempts.append(1)
        raise requests.HTTPError('service unavailable', response=response)
    monkeypatch.setattr(data_download.requests, 'get', fail)
    monkeypatch.setattr(data_download.time, 'sleep', lambda _: None)
    with pytest.raises(RuntimeError, match='HTTP 503: upstream temporarily unavailable'):
        data_download._query('example', {}, retries=2)
    assert len(attempts) == 2
    assert 'intento 2/2' in capsys.readouterr().out


def test_bad_query_is_not_retried(monkeypatch):
    response = requests.Response()
    response.status_code = 400
    response._content = b'invalid SoQL'
    attempts = []
    def fail(*args, **kwargs):
        attempts.append(1)
        raise requests.HTTPError('bad request', response=response)
    monkeypatch.setattr(data_download.requests, 'get', fail)
    with pytest.raises(RuntimeError, match='invalid SoQL'):
        data_download._query('example', {})
    assert len(attempts) == 1


def test_colab_runner_surfaces_stderr_and_saves_log(tmp_path, monkeypatch, capsys):
    helper = Path(__file__).resolve().parents[1] / 'scripts' / 'colab_run.py'
    run = runpy.run_path(str(helper))['run']
    monkeypatch.chdir(tmp_path)
    with pytest.raises(RuntimeError, match='Error completo arriba'):
        run('cafe_nonexistent_module_for_diagnostic_test')
    out = capsys.readouterr().out
    assert 'No module named' in out
    log = tmp_path / 'results/logs/cafe_nonexistent_module_for_diagnostic_test.log'
    assert 'No module named' in log.read_text(encoding='utf-8')


def test_colab_runner_success(tmp_path, monkeypatch, capsys):
    helper = Path(__file__).resolve().parents[1] / 'scripts' / 'colab_run.py'
    run = runpy.run_path(str(helper))['run']
    monkeypatch.chdir(tmp_path)
    run('json.tool', '--help')
    assert 'Completado: json.tool' in capsys.readouterr().out
    assert (tmp_path / 'results/logs/json_tool.log').exists()


def _row(day):
    return {'codigoestacion': '001', 'municipio': 'JARDIN', 'departamento': 'ANTIOQUIA',
            'latitud': '5.6', 'longitud': '-75.8', 'dia': str(day) + 'T00:00:00.000',
            'valor': '3', 'n': '144', 'n_total': '144', 'horas': '24'}


def _interval(params):
    import re
    from datetime import date
    dates = re.findall(r"'(\d{4}-\d{2}-\d{2})T", params['$where'])
    return date.fromisoformat(dates[0]), date.fromisoformat(dates[1])


def test_month_cache_from_previous_version_is_reused(tmp_path, monkeypatch):
    import hashlib
    from datetime import date
    import pandas as pd
    ini, fin = date(2024, 11, 1), date(2024, 12, 1)
    deps = ','.join(f"'{d}'" for d in data_download.C.DEPARTAMENTOS)
    old_where = (f"upper(departamento) in({deps}) AND fechaobservacion >= '{ini}T00:00:00' "
                 f"AND fechaobservacion < '{fin}T00:00:00' AND valorobservado >= 0 "
                 "AND valorobservado <= 100")
    signature = hashlib.sha256((old_where + 'sum' + 'v3-hours').encode()).hexdigest()[:12]
    path = tmp_path / f's54a-sgyg_{ini}_{signature}.csv'
    pd.DataFrame([_row(ini)]).to_csv(path, index=False)
    def unexpected(*args, **kwargs):
        pytest.fail('La caché anterior no debe provocar consulta de red')
    monkeypatch.setattr(data_download, '_query', unexpected)
    frame = data_download._fetch_window('s54a-sgyg', 'sum', 0, 100, ini, fin, tmp_path)
    assert frame.iloc[0].codigoestacion == '001'


def test_timeout_splits_without_gaps_or_duplicate_rain(tmp_path, monkeypatch):
    from datetime import date, timedelta
    calls = []
    def query(ds, params):
        ini, fin = _interval(params)
        calls.append((ini, fin))
        if (fin - ini).days > 7:
            raise data_download.QueryTimeout('slow server')
        return [_row(ini + timedelta(days=i)) for i in range((fin - ini).days)]
    monkeypatch.setattr(data_download, '_query', query)
    ini, fin = date(2024, 11, 1), date(2024, 12, 1)
    frame = data_download._fetch_window('ds', 'sum', 0, 100, ini, fin, tmp_path)
    assert len(frame) == 30
    assert frame.dia.nunique() == 30
    assert sum(float(v) for v in frame.valor) == 90
    assert len(calls) > 1
    calls.clear()
    cached = data_download._fetch_window('ds', 'sum', 0, 100, ini, fin, tmp_path)
    assert len(cached) == 30 and calls == []


def test_partial_split_can_resume_from_successful_child(tmp_path, monkeypatch):
    from datetime import date, timedelta
    ini, mid, fin = date(2024, 11, 1), date(2024, 11, 3), date(2024, 11, 5)
    blocked = [True]
    calls = []
    def query(ds, params):
        start, end = _interval(params)
        calls.append((start, end))
        if (start, end) == (ini, fin):
            raise data_download.QueryTimeout('split')
        if start == mid and blocked[0]:
            raise RuntimeError('temporary interruption')
        return [_row(start + timedelta(days=i)) for i in range((end-start).days)]
    monkeypatch.setattr(data_download, '_query', query)
    with pytest.raises(RuntimeError, match='temporary interruption'):
        data_download._fetch_window('ds', 'sum', 0, 100, ini, fin, tmp_path)
    root = data_download._cache_path('ds', 'sum', data_download._where(0, 100, ini, fin), ini, tmp_path)
    assert not root.exists()
    blocked[0] = False
    calls.clear()
    frame = data_download._fetch_window('ds', 'sum', 0, 100, ini, fin, tmp_path)
    assert len(frame) == 4
    assert (ini, mid) not in calls


def test_day_timeout_is_explicit_and_not_cached(tmp_path, monkeypatch):
    from datetime import date
    def query(*args, **kwargs):
        raise data_download.QueryTimeout('server busy')
    monkeypatch.setattr(data_download, '_query', query)
    with pytest.raises(RuntimeError, match='ni el día 2024-11-01'):
        data_download._fetch_window('ds', 'sum', 0, 100, date(2024,11,1), date(2024,11,2), tmp_path)
    assert list(tmp_path.glob('*.csv')) == []


def test_empty_window_cache_remains_readable(tmp_path, monkeypatch):
    from datetime import date
    calls = []
    monkeypatch.setattr(data_download, '_query', lambda *args: calls.append(1) or [])
    args = ('ds', 'sum', 0, 100, date(2024,11,1), date(2024,11,2), tmp_path)
    assert data_download._fetch_window(*args).empty
    assert data_download._fetch_window(*args).empty
    assert calls == [1]
