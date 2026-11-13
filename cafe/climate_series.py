"""Series para visualización: conservar cada variable y los huecos de calendario."""
from pathlib import Path
import pandas as pd
from . import config as C
from .data_prep import KEYS, _municipio_dia, _weekly

VARIABLES = ('lluvia_mm','temp_c','humedad_pct')


def build_climate_weekly(precip_path=None,temp_path=None,hum_path=None):
    specs=[
        (Path(precip_path or C.PRECIP_DAILY),'lluvia_mm','sum',C.MIN_N_DAY,C.MIN_DAYS_WEEK_RAIN),
        (Path(temp_path or C.TEMP_DAILY),'temp_c','mean',C.MIN_N_DAY_TEMP,C.MIN_DAYS_WEEK_TEMP),
        (Path(hum_path or C.HUM_DAILY),'humedad_pct','mean',C.MIN_N_DAY_HUM,C.MIN_DAYS_WEEK_HUM)]
    out=None
    keys=KEYS+['semana']
    for path,col,agg,min_n,min_days in specs:
        if col=='humedad_pct' and not path.exists():
            continue
        daily=_municipio_dia(path,col,min_n)
        weekly=_weekly(daily,col,agg,min_days).drop(columns=['lat','lon'])
        out=weekly if out is None else out.merge(weekly,on=keys,how='outer',validate='one_to_one')
    for col in VARIABLES:
        if col not in out:
            out[col]=float('nan')
        count=f'dias_{col}'
        if count not in out:
            out[count]=0
        out[count]=out[count].fillna(0).astype(int)
    out['municipio_nombre']=out['municipio']
    out['municipio']=out['municipio']+' / '+out['departamento']
    return out.sort_values(['municipio','semana']).reset_index(drop=True)


def calendar_view(climate,municipio,fecha,weeks=104):
    """Sin imputación. El límite se expresa en semanas de calendario, no filas válidas."""
    end=pd.Timestamp(fecha).normalize()
    end=end-pd.Timedelta(days=(end.weekday()+1)%7)  # último domingo ya terminado
    d=climate.loc[climate.municipio.eq(municipio)].copy()
    d['semana']=pd.to_datetime(d['semana'])
    d=d[d.semana.le(end)].sort_values('semana')
    if d.empty:
        return d
    if d.semana.duplicated().any():
        raise ValueError('Municipio-semana duplicado en la serie climática')
    start=d.semana.min()
    if weeks is not None:
        if weeks<1:
            raise ValueError('weeks debe ser positivo')
        start=max(start,end-pd.Timedelta(weeks=weeks-1))
    index=pd.date_range(start,end,freq='W-SUN',name='semana')
    view=d.set_index('semana').reindex(index).reset_index()
    view['municipio']=municipio
    for col in VARIABLES:
        if col not in view:
            view[col]=float('nan')
    return view


def main():
    frame=build_climate_weekly()
    C.DATA_PROC.mkdir(parents=True,exist_ok=True)
    frame.to_csv(C.CLIMATE_WEEKLY,index=False)
    print(f'Series independientes: {len(frame)} semanas-municipio -> {C.CLIMATE_WEEKLY}. No se entrena ni modifica el modelo.')


if __name__=='__main__':
    main()
