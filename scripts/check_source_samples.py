"""Contraste acotado de tres estación-día públicos contra Socrata; no descarga históricos."""
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import json
from pathlib import Path
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.datos.gov.co/resource'


def check(spec):
    kind,ds,station,day,agg,lo,hi=spec
    path=ROOT/'data/raw'/f'{kind}_diaria.csv'
    source=pd.read_csv(path,dtype={'codigoestacion':str})
    chosen=source[source.codigoestacion.eq(station) & source.dia.str[:10].eq(day)]
    if chosen.empty:
        return {'dataset':ds,'estacion':station,'dia':day,'estado':'sin fila diaria para comparar'}
    end=(pd.Timestamp(day)+pd.Timedelta(days=1)).date().isoformat()
    params={'$select':'codigoestacion,codigosensor,fechaobservacion,valorobservado,unidadmedida,descripcionsensor',
        '$where':f"codigoestacion = '{station}' AND fechaobservacion >= '{day}T00:00:00' AND fechaobservacion < '{end}T00:00:00'",
        '$order':'fechaobservacion ASC','$limit':5000}
    try:
        r=requests.get(f'{BASE}/{ds}.json',params=params,timeout=(10,30))
        r.raise_for_status()
        rows=r.json()
        if not rows or len(rows)>=5000:
            return {'dataset':ds,'estacion':station,'dia':day,'estado':'muestra vacía o truncada; no verificada','filas':len(rows)}
        raw=pd.DataFrame(rows)
        raw['valorobservado']=pd.to_numeric(raw.valorobservado,errors='coerce')
        valid=raw[raw.valorobservado.between(lo,hi)].copy()
        stamp=pd.to_datetime(valid.fechaobservacion)
        value=float(valid.valorobservado.sum() if agg=='sum' else valid.valorobservado.mean())
        old=chosen.iloc[0]
        new={'valor':value,'n':int(stamp.nunique()),'n_total':len(valid),'horas':int(stamp.dt.hour.nunique())}
        equal=all(abs(float(old[k])-float(v))<=max(1e-8,abs(float(v))*1e-9) for k,v in new.items())
        return {'dataset':ds,'estacion':station,'dia':day,'estado':'coincide' if equal else 'difiere',
            'valor_guardado':float(old.valor),'recalculado':new,'filas_api_sin_filtrar':len(raw),
            'unidades':sorted(raw.unidadmedida.dropna().unique().tolist()),
            'sensores':sorted(raw.codigosensor.dropna().unique().tolist()),
            'valores_distintos':int(valid.valorobservado.nunique()),
            'min':float(valid.valorobservado.min()),'max':float(valid.valorobservado.max()),
            'url_consultada':r.url}
    except requests.RequestException as exc:
        return {'dataset':ds,'estacion':station,'dia':day,'estado':'no se pudo contrastar','error':type(exc).__name__}


def main():
    temp=pd.read_csv(ROOT/'data/raw/temp_diaria.csv',dtype={'codigoestacion':str})
    match=temp[temp.municipio.str.upper().isin(['MEDELLIN','MEDELLÍN']) & temp.n.ge(12) & temp.horas.ge(12) & temp.n_total.eq(temp.n)].iloc[-1]
    specs=[('precip','s54a-sgyg','0026125710','2022-03-01','sum',0,100),
           ('humedad','uext-mhny','0026180250','2026-08-12','avg',0,100),
           ('temp','sbwg-7ju4',str(match.codigoestacion),str(match.dia)[:10],'avg',-5,45)]
    with ThreadPoolExecutor(max_workers=3) as pool:
        results=list(pool.map(check,specs))
    out=ROOT/'results/contraste_muestras_fuente.json'
    out.write_text(json.dumps({'alcance':'Tres muestras, no verificación exhaustiva de extracción ni sensores. Comparación contra API pública actual; la fuente puede cambiar.',
                               'muestras':results},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(results,ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
