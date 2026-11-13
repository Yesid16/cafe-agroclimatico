"""IDEAM/Socrata: descarga agregada diaria con caché mensual y trazabilidad.
Ejecutar en Colab/CPU: python -m cafe.data_download --desde 2022-01-01 --hasta 2026-10-31
"""
import argparse
import hashlib
import json
import time
from datetime import date, datetime, timedelta, timezone

import pandas as pd
import requests
from . import config as C

PAGE = 50000
DAILY_COLUMNS = ['codigoestacion', 'municipio', 'departamento', 'latitud', 'longitud',
                 'dia', 'valor', 'n', 'n_total', 'horas']


class QueryTimeout(RuntimeError):
    """Consulta agotada: se puede intentar un intervalo menor."""

SPECS = {
    C.DS_PRECIP: ('precip_diaria.csv', 'sum', 0, 100, 'mm', 144),
    C.DS_TEMP: ('temp_diaria.csv', 'avg', -5, 45, '°C', 24),
    C.DS_HUM: ('humedad_diaria.csv', 'avg', 0, 100, '%', 24),
}


def _query(ds, params, retries=2):
    headers = {'X-App-Token': C.SOCRATA_APP_TOKEN} if C.SOCRATA_APP_TOKEN else {}
    for i in range(retries):
        try:
            r = requests.get(f'{C.SOCRATA_BASE}/{ds}.json', params=params, headers=headers, timeout=(15, 60))
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            response = getattr(exc, 'response', None)
            detail = (f'HTTP {response.status_code}: {response.text[:500]}' if response is not None
                      else f'{type(exc).__name__}: {exc}')
            print(f'{ds}: intento {i + 1}/{retries}: {detail}', flush=True)
            if getattr(exc, 'response', None) is not None and exc.response.status_code in (400, 401, 403, 404):
                raise RuntimeError(f'Consulta inválida a {ds}: {exc.response.text[:500]}') from exc
            if i == retries - 1:
                splittable = isinstance(exc, requests.ReadTimeout) or (
                    response is not None and response.status_code in (408, 500, 502, 503, 504))
                error = QueryTimeout if splittable else RuntimeError
                raise error(f'Falló {ds}: {detail}. Se conserva la caché.') from exc
            time.sleep(2 ** (i + 1))


def _months(desde, hasta):
    if desde > hasta:
        raise ValueError('--desde debe ser anterior o igual a --hasta')
    y, m = desde.year, desde.month
    while (y, m) <= (hasta.year, hasta.month):
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        yield max(date(y, m, 1), desde), min(date(ny, nm, 1), hasta + timedelta(days=1))
        y, m = ny, nm


def _where(vmin, vmax, ini, fin):
    deptos = ','.join(f"'{d}'" for d in C.DEPARTAMENTOS)
    return (f"upper(departamento) in({deptos}) AND fechaobservacion >= '{ini}T00:00:00' "
            f"AND fechaobservacion < '{fin}T00:00:00' AND valorobservado >= {vmin} "
            f"AND valorobservado <= {vmax}")


def _cache_path(ds, agg, where, ini, cache):
    # Mantener la firma anterior para reutilizar los meses ya descargados en Colab.
    signature = hashlib.sha256((where + agg + 'v3-hours').encode()).hexdigest()[:12]
    return cache / f'{ds}_{ini}_{signature}.csv'


def _fetch_window(ds, agg, vmin, vmax, ini, fin, cache):
    where = _where(vmin, vmax, ini, fin)
    cp = _cache_path(ds, agg, where, ini, cache)
    if cp.exists():
        print(f'{ds} {ini} a {fin} (fin exclusivo): caché', flush=True)
        return pd.read_csv(cp, dtype={'codigoestacion': str})
    print(f'{ds}: consultando {ini} a {fin} (fin exclusivo)', flush=True)
    offset, rows_window = 0, []
    try:
        while True:
            rows = _query(ds, {
                '$select': ('codigoestacion, municipio, departamento, latitud, longitud, '
                            f'date_trunc_ymd(fechaobservacion) as dia, {agg}(valorobservado) as valor, '
                            'count(distinct fechaobservacion) as n, count(*) as n_total, '
                            'count(distinct date_extract_hh(fechaobservacion)) as horas'),
                '$where': where,
                '$group': 'codigoestacion, municipio, departamento, latitud, longitud, dia',
                '$order': 'codigoestacion ASC, dia ASC, municipio ASC, departamento ASC, latitud ASC, longitud ASC',
                '$limit': PAGE, '$offset': offset})
            rows_window.extend(rows)
            if len(rows) < PAGE:
                break
            offset += PAGE
        frame = pd.DataFrame(rows_window, columns=DAILY_COLUMNS)
    except QueryTimeout as exc:
        days = (fin - ini).days
        if days <= 1:
            raise RuntimeError(
                f'{ds}: IDEAM no pudo completar ni el día {ini}. '
                'Reintente más tarde o use CSV oficiales; las particiones completas siguen en caché.'
            ) from exc
        mid = ini + timedelta(days=days // 2)
        print(f'{ds}: el intervalo {ini} a {fin} agotó el tiempo; dividiendo en {mid}.', flush=True)
        # Intervalos disjuntos: sumar lluvia diaria sigue siendo válido, sin duplicar datos.
        left = _fetch_window(ds, agg, vmin, vmax, ini, mid, cache)
        right = _fetch_window(ds, agg, vmin, vmax, mid, fin, cache)
        frame = pd.concat([left, right], ignore_index=True)
    # Un fallo no deja un CSV parcial que pueda confundirse con una partición completa.
    temporary = cp.with_suffix('.csv.tmp')
    frame.to_csv(temporary, index=False)
    temporary.replace(cp)
    print(f'{ds} {ini} a {fin}: {len(frame)} estación-día', flush=True)
    return frame


def download(ds, agg, vmin, vmax, desde, hasta):
    cache = C.DATA_RAW / 'cache'
    cache.mkdir(parents=True, exist_ok=True)
    frames = [_fetch_window(ds, agg, vmin, vmax, ini, fin, cache)
              for ini, fin in _months(desde, hasta)]
    if not frames or not any(len(f) for f in frames):
        raise RuntimeError(f'Sin datos para {ds} en el rango solicitado')
    df = pd.concat(frames, ignore_index=True)
    df['dia'] = pd.to_datetime(df['dia']).dt.normalize()
    for col in ('valor', 'n', 'latitud', 'longitud'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--desde', default='2022-01-01')
    ap.add_argument('--hasta', default=(date.today() - timedelta(days=1)).isoformat())
    args = ap.parse_args()
    d0, d1 = date.fromisoformat(args.desde), date.fromisoformat(args.hasta)
    if d0 > d1:
        ap.error('--desde debe ser anterior o igual a --hasta')
    C.DATA_RAW.mkdir(parents=True, exist_ok=True)
    manifest = {'desde': str(d0), 'hasta_inclusive': str(d1), 'datasets': []}
    for ds, (name, agg, lo, hi, unit, frequency) in SPECS.items():
        print(f'{ds}: consultando metadatos; rango {d0} a {d1}', flush=True)
        meta = requests.get(f'https://www.datos.gov.co/api/views/{ds}.json', timeout=60)
        meta.raise_for_status()
        (C.DATA_RAW / f'{ds}_metadata.json').write_text(json.dumps(meta.json(), ensure_ascii=False, indent=2), encoding='utf-8')
        df = download(ds, agg, lo, hi, d0, d1)
        path = C.DATA_RAW / name
        df.to_csv(path, index=False)
        manifest['datasets'].append({'id': ds, 'url': f'{C.SOCRATA_BASE}/{ds}.json', 'archivo': name,
            'agregacion': agg, 'unidad': unit, 'lecturas_esperadas_dia': frequency,
            'filtro_valor': [lo, hi], 'filas': len(df), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        manifest['descargado_utc'] = datetime.now(timezone.utc).isoformat()
        (C.DATA_RAW / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
