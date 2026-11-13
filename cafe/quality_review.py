"""Audita CSV diarios y prepara una sensibilidad conservadora, sin entrenar ni tocar originales."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from . import config as C
from .data_prep import norm, build_weekly

SPECS = [('precip', C.PRECIP_DAILY, 72), ('temp', C.TEMP_DAILY, 12), ('humedad', C.HUM_DAILY, 12)]


def coverage_mask(df, min_n):
    return df.n.ge(min_n) & df.horas.ge(12) & df.n_total.eq(df.n)


def repeated_rate_flags(df, min_days=3):
    """Misma media positiva por lectura varios días: bandera, no prueba de sensor fijo."""
    x=df.sort_values(['codigoestacion','dia']).copy()
    rate=x.valor / x.n.replace(0,np.nan)
    previous=rate.groupby(x.codigoestacion).shift(1)
    previous_day=x.groupby('codigoestacion').dia.shift(1)
    eligible=coverage_mask(x,72) & x.valor.gt(100)
    same_station=x.codigoestacion.eq(x.codigoestacion.shift(1))
    continued=(same_station & eligible & eligible.shift(1,fill_value=False)
               & (x.dia-previous_day).eq(pd.Timedelta(days=1))
               & np.isclose(rate,previous,rtol=0,atol=1e-9))
    run=(~continued).cumsum()
    lengths=eligible.groupby(run).transform('sum')
    flag=eligible & lengths.ge(min_days)
    return flag.reindex(df.index,fill_value=False)


def main():
    review=C.ROOT/'data/review'
    output=C.ROOT/'results/revision_diaria'
    (review/'raw').mkdir(parents=True,exist_ok=True)
    (review/'processed').mkdir(exist_ok=True)
    output.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((C.DATA_RAW/'manifest.json').read_text(encoding='utf-8'))
    expected={x['archivo']:x for x in manifest['datasets']}
    weeks=pd.read_csv(C.ROOT/'results/observaciones_para_revision.csv',parse_dates=['semana'])
    targets=weeks[['departamento','municipio','semana']].copy()
    targets['municipio']=targets.municipio.str.split(' / ').str[0]
    summary={'politica':{
        'humedad': 'Omitir medias diarias <20% antes de promediar estaciones.',
        'lluvia': 'Omitir días >300 mm o series de >=3 días consecutivos con igual valor/n y total diario >100 mm.',
        'interpretacion': 'Sensibilidad conservadora, no límites físicos certificados. Puede excluir extremos reales; no sustituye validar sensores.',
        'sin_cambios': 'No se escala humedad ni se deduplican totales agregados por división; se conservan fuentes y experimento original.'},
        'datasets':[], 'entrenamiento_ejecutado': False}
    trace=[]; flags=[]; paths={}
    for kind,path,min_n in SPECS:
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        verified=digest==expected[path.name]['sha256']
        if not verified:
            raise ValueError(f'{path.name}: SHA-256 distinto del manifiesto; no aplicar la revisión a otra descarga')
        df=pd.read_csv(path,dtype={'codigoestacion':str},parse_dates=['dia'])
        for col in ['departamento','municipio']:
            df[col]=df[col].map(norm)
        ok=coverage_mask(df,min_n)
        df['semana']=df.dia.dt.to_period('W-SUN').dt.end_time.dt.normalize()
        reasons=pd.Series('',index=df.index,dtype='str')
        if kind=='humedad':
            reasons.loc[ok & df.valor.lt(20)]='humedad_diaria_menor20'
        if kind=='precip':
            reasons.loc[ok & df.valor.gt(300)]='lluvia_diaria_mayor300'
            repeated=repeated_rate_flags(df)
            reasons.loc[repeated]=reasons.loc[repeated].map(lambda s:(s+'; ' if s else '')+'tasa_media_lluvia_repetida')
        suspect=reasons.ne('')
        rows=df.loc[suspect].copy()
        rows['variable']=kind; rows['motivo_revision']=reasons[suspect]
        flags.append(rows)
        joined=df.assign(variable=kind,cumple_cobertura=ok,motivo_revision=reasons).merge(
            targets,on=['departamento','municipio','semana'],how='inner',validate='many_to_one')
        trace.append(joined)
        y=df[df.dia.dt.year.eq(2024)]
        summary['datasets'].append({
            'variable':kind,'archivo':path.name,'sha256_verificado':verified,
            'filas_originales':len(df),'dias_cumplen_cobertura':int(ok.sum()),
            'filas_omitidas_solo_en_variante':int(suspect.sum()),
            'motivos':reasons[suspect].value_counts().to_dict(),
            'ano2024':{'filas':len(y),'n_total_distinto_n':int(y.n_total.ne(y.n).sum()),
                       'cumplen_cobertura':int(coverage_mask(y,min_n).sum())}})
        dest=review/'raw'/path.name
        # Mantener estructura de entrada; columna semana es solo evidencia de esta auditoría.
        df.loc[~suspect].drop(columns='semana').to_csv(dest,index=False)
        paths[kind]=dest
    pd.concat(trace,ignore_index=True).to_csv(output/'trazabilidad_54_semanas.csv',index=False)
    suspects=pd.concat(flags,ignore_index=True)
    suspects.to_csv(output/'dias_para_revision.csv',index=False)
    stations=suspects.groupby(['variable','codigoestacion','departamento','municipio']).agg(
        dias=('dia','count'),desde=('dia','min'),hasta=('dia','max'),
        valor_min=('valor','min'),valor_mediana=('valor','median'),valor_max=('valor','max')).reset_index()
    stations.to_csv(output/'estaciones_para_revision.csv',index=False)
    baseline=build_weekly()
    actual=pd.read_csv(C.WEEKLY,parse_dates=['semana'])
    keys=['departamento','municipio','semana']
    merged=baseline.merge(actual,on=keys,how='outer',suffixes=('_recalculado','_colab'),indicator=True,validate='one_to_one')
    same_keys=merged['_merge'].eq('both').all()
    same_values=same_keys and all(np.allclose(merged[c+'_recalculado'],merged[c+'_colab'],equal_nan=True,atol=1e-8,rtol=1e-9)
                                for c in ['lluvia_mm','temp_c','humedad_pct'])
    if not same_values:
        raise ValueError('La agregación diaria no reproduce la tabla de Colab; revisar antes de preparar sensibilidad')
    candidate=build_weekly(paths['precip'],paths['temp'],paths['humedad'])
    candidate.to_csv(review/'processed/semanal.csv',index=False)
    summary['agregacion_original_reproducida']=bool(same_values)
    summary['original']={'filas':len(actual),'municipios':int(actual.municipio.nunique()),
        'humedad_disponible':int(actual.humedad_pct.notna().sum()),
        'semanas_humedad_menor20':int(actual.humedad_pct.lt(20).sum()),
        'semanas_lluvia_mayor500':int(actual.lluvia_mm.gt(500).sum())}
    summary['variante']={'filas':len(candidate),'municipios':int(candidate.municipio.nunique()),
        'humedad_disponible':int(candidate.humedad_pct.notna().sum()),
        'cobertura_humedad':float(candidate.humedad_pct.notna().mean()),
        'semanas_humedad_menor20':int(candidate.humedad_pct.lt(20).sum()),
        'semanas_lluvia_mayor500':int(candidate.lluvia_mm.gt(500).sum()),
        'archivo':'data/review/processed/semanal.csv',
        'sha256':hashlib.sha256((review/'processed/semanal.csv').read_bytes()).hexdigest()}
    comparison=actual.merge(candidate,on=keys,how='outer',suffixes=('_original','_variante'),indicator=True,validate='one_to_one')
    comparison.to_csv(output/'comparacion_semanal.csv',index=False)
    summary['comparacion']={'solo_original':int(comparison['_merge'].eq('left_only').sum()),
        'solo_variante':int(comparison['_merge'].eq('right_only').sum()),
        'comunes':int(comparison['_merge'].eq('both').sum())}
    common=comparison['_merge'].eq('both')
    for column in ['humedad_pct','lluvia_mm','temp_c']:
        changed=common & ~np.isclose(comparison[column+'_original'],comparison[column+'_variante'],
                                    equal_nan=True,atol=1e-8,rtol=1e-9)
        summary['comparacion'][column+'_modificada_en_semanas_comunes']=int(changed.sum())

    (output/'auditoria_diaria.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
