"""Limpieza estación-día y agregación municipio-semana con reporte de cobertura."""
import json
import unicodedata
import numpy as np
import pandas as pd
from . import config as C

KEYS = ['departamento', 'municipio']


def norm(s):
    s = unicodedata.normalize('NFKD', str(s)).encode('ascii', 'ignore').decode()
    return ' '.join(s.upper().split())


def _municipio_dia(path, kind, min_n):
    df = pd.read_csv(path, dtype={'codigoestacion': str})
    required = {'codigoestacion', 'municipio', 'departamento', 'latitud', 'longitud', 'dia', 'valor', 'n'}
    if missing := required - set(df.columns):
        raise ValueError(f'{path}: faltan columnas {sorted(missing)}')
    df['dia'] = pd.to_datetime(df['dia'], errors='coerce').dt.normalize()
    for col in ('valor', 'n', 'latitud', 'longitud'):
        df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=list(required))
    for col in KEYS:
        df[col] = df[col].map(norm)
    # Rechazar duplicados ambiguos; el CSV manual también debe ser estación-día.
    if df.duplicated(['codigoestacion', 'dia']).any():
        raise ValueError(f'{path}: estación-día duplicada; revise sensores/ubicaciones antes de agregar')
    if 'horas' in df:
        df = df[pd.to_numeric(df['horas'], errors='coerce') >= 12]
    if 'n_total' in df:
        df = df[pd.to_numeric(df['n_total'], errors='coerce') == df['n']]
    bounds = {'lluvia_mm': (0, 14400), 'temp_c': (-5, 45), 'humedad_pct': (0, 100)}
    lo, hi = bounds[kind]
    df = df[(df['n'] >= min_n) & df['valor'].between(lo, hi) & df['n'].gt(0)]
    if df.empty:
        raise ValueError(f'{path}: sin días válidos con mínimo {min_n} lecturas; revise frecuencia/unidad')
    return df.groupby(KEYS + ['dia']).agg(
        **{kind: ('valor', 'mean'), f'n_est_{kind}': ('codigoestacion', 'nunique')},
        lat=('latitud', 'mean'), lon=('longitud', 'mean')).reset_index()


def _weekly(g, col, how, min_days):
    out = []
    for (dep, mun), d in g.groupby(KEYS):
        w = d.set_index('dia')[col].resample('W-SUN')
        cnt = w.count()
        # Extrapolación explícita de lluvia cuando hay 5/6 días, no lluvia medida completa.
        v = w.sum() * 7 / cnt.replace(0, np.nan) if how == 'sum' else w.mean()
        v[cnt < min_days] = np.nan
        o = v.rename(col).reset_index().rename(columns={'dia': 'semana'})
        o['departamento'], o['municipio'] = dep, mun
        o['lat'], o['lon'] = d['lat'].mean(), d['lon'].mean()
        o[f'dias_{col}'] = cnt.values
        o[f'n_est_{col}'] = d.set_index('dia')[f'n_est_{col}'].resample('W-SUN').max().values
        out.append(o)
    return pd.concat(out, ignore_index=True)


def build_weekly(precip_path=None, temp_path=None, hum_path=None):
    p = _municipio_dia(precip_path or C.PRECIP_DAILY, 'lluvia_mm', C.MIN_N_DAY)
    t = _municipio_dia(temp_path or C.TEMP_DAILY, 'temp_c', C.MIN_N_DAY_TEMP)
    wp = _weekly(p, 'lluvia_mm', 'sum', C.MIN_DAYS_WEEK_RAIN)
    wt = _weekly(t, 'temp_c', 'mean', C.MIN_DAYS_WEEK_TEMP)
    keys = KEYS + ['semana']
    w = wp.merge(wt.drop(columns=['lat', 'lon']), on=keys, how='inner', validate='one_to_one')
    humidity_path = C.HUM_DAILY if hum_path is None else hum_path
    if humidity_path.exists():
        h = _municipio_dia(humidity_path, 'humedad_pct', C.MIN_N_DAY_HUM)
        wh = _weekly(h, 'humedad_pct', 'mean', C.MIN_DAYS_WEEK_HUM)
        w = w.merge(wh.drop(columns=['lat', 'lon']), on=keys, how='left', validate='one_to_one')
    else:
        w['humedad_pct'] = np.nan  # nunca inventar humedad a partir de lluvia
    w = w.dropna(subset=['lluvia_mm', 'temp_c'])
    counts = w.groupby(KEYS)['semana'].transform('count')
    w = w[counts >= C.MIN_WEEKS_MUNICIPIO].sort_values(KEYS + ['semana']).reset_index(drop=True)
    if w.empty:
        raise ValueError('No quedan municipios con cobertura suficiente; revise datos y reporte de descarga')
    # Nombre calificado evita mezclar municipios homónimos de distintos departamentos.
    w['municipio_nombre'] = w['municipio']
    w['municipio'] = w['municipio'] + ' / ' + w['departamento']
    return w


def main():
    w = build_weekly()
    C.DATA_PROC.mkdir(parents=True, exist_ok=True)
    w.to_csv(C.WEEKLY, index=False)
    from .climate_series import build_climate_weekly
    build_climate_weekly().to_csv(C.CLIMATE_WEEKLY, index=False)
    coverage = w.groupby(KEYS).agg(semanas=('semana', 'count'), desde=('semana', 'min'),
        hasta=('semana', 'max'), semanas_con_humedad=('humedad_pct', 'count')).reset_index()
    C.RESULTS_DIR.mkdir(exist_ok=True)
    coverage.to_csv(C.RESULTS_DIR / 'cobertura_datos.csv', index=False)
    quality = {'filas': len(w), 'municipios': w['municipio'].nunique(), 'desde': str(w.semana.min().date()),
        'hasta': str(w.semana.max().date()), 'cobertura_humedad': float(w.humedad_pct.notna().mean()),
        'lluvia_semanas_extrapoladas': int(w.dias_lluvia_mm.lt(7).sum()),
        'limitacion': 'Promedio municipal de estaciones; humedad no mide agua libre foliar. No hay etiquetas de incidencia de roya.'}
    (C.RESULTS_DIR / 'calidad_datos.json').write_text(json.dumps(quality, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(quality, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
