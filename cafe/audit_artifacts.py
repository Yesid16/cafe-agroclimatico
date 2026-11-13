"""Auditoría de artefactos existentes: no descarga ni entrena modelos."""
import hashlib
import json
from datetime import datetime, timezone
from . import config as C
import numpy as np
import pandas as pd


def audit(weekly):
    w = weekly.copy()
    w['semana'] = pd.to_datetime(w['semana'])
    flags = pd.DataFrame(index=w.index)
    # Banderas exploratorias de revisión, no reglas para borrar observaciones.
    flags['humedad_menor20'] = w['humedad_pct'].lt(20)
    flags['lluvia_mayor500'] = w['lluvia_mm'].gt(500)
    flags['humedad_faltante'] = w['humedad_pct'].isna()
    flagged = w.loc[flags[['humedad_menor20','lluvia_mayor500']].any(axis=1)].copy()
    flagged['motivo_revision'] = flags.loc[flagged.index].apply(
        lambda r: '; '.join(r.index[r].tolist()), axis=1)
    counts = w.groupby('municipio')['semana'].agg(['count', 'min', 'max'])
    counts['semanas_entre_extremos'] = ((counts['max'] - counts['min']).dt.days // 7 + 1)
    counts['cobertura_entre_extremos'] = counts['count'] / counts['semanas_entre_extremos']
    n = len(w)
    summary = {
        'filas': n, 'municipios': int(w['municipio'].nunique()),
        'duplicados_municipio_semana': int(w.duplicated(['municipio', 'semana']).sum()),
        'humedad_disponible': int(w.humedad_pct.notna().sum()),
        'humedad_faltante': int(w.humedad_pct.isna().sum()),
        'cobertura_humedad': float(w.humedad_pct.notna().mean()),
        'lluvia_extrapolada': int(w.dias_lluvia_mm.lt(7).sum()),
        'proporcion_lluvia_extrapolada': float(w.dias_lluvia_mm.lt(7).mean()),
        'humedad_menor20': int(flags.humedad_menor20.sum()),
        'lluvia_mayor500': int(flags.lluvia_mayor500.sum()),
        'filas_para_revision': len(flagged),
        'filas_por_ano': {str(k): int(v) for k,v in w.groupby(w.semana.dt.year).size().items()},
        'departamentos': w.groupby('departamento').municipio.nunique().to_dict(),
        'rango_etiquetas_semanales': [str(w.semana.min().date()), str(w.semana.max().date())],
        'criterio_banderas': 'Humedad semanal <20% o lluvia >500 mm/semana: investigar sensores/unidades; no confirman error ni se eliminan automáticamente.',
        'estado': 'Datos pertinentes para MVP exploratorio; calidad meteorológica no certificada. Revisar anomalías y discontinuidad antes de inferencia agronómica.'
    }
    return summary, flagged, counts.reset_index()


def main():
    w = pd.read_csv(C.WEEKLY, parse_dates=['semana'])
    summary, flagged, coverage = audit(w)
    summary['utc'] = datetime.now(timezone.utc).isoformat()
    summary['artefactos_sha256'] = {p.relative_to(C.ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                                  for p in [C.WEEKLY, C.MODEL_PATH]}
    C.RESULTS_DIR.mkdir(exist_ok=True)
    flagged.to_csv(C.RESULTS_DIR / 'observaciones_para_revision.csv', index=False)
    coverage.to_csv(C.RESULTS_DIR / 'cobertura_temporal_auditada.csv', index=False)
    (C.RESULTS_DIR / 'auditoria_datos.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
