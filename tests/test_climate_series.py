import numpy as np
import pandas as pd
from cafe import config as C
from cafe.climate_series import build_climate_weekly,calendar_view
from cafe.data_prep import build_weekly


def daily(days,value,n):
    return pd.DataFrame({'codigoestacion':'001','municipio':'M','departamento':'D',
        'latitud':5,'longitud':-75,'dia':days,'valor':value,'n':n,'n_total':n,'horas':24})


def test_rain_is_preserved_when_temperature_is_insufficient(tmp_path,monkeypatch):
    days=pd.date_range('2024-01-01',periods=14)
    p,t,h=(tmp_path/name for name in ['p.csv','t.csv','h.csv'])
    daily(days,10,144).to_csv(p,index=False)
    daily(days,22,24).drop(index=[3,4,5,6]).to_csv(t,index=False)
    daily(days,80,24).to_csv(h,index=False)
    climate=build_climate_weekly(p,t,h)
    first=climate.loc[climate.semana.eq(pd.Timestamp('2024-01-07'))].iloc[0]
    assert first.lluvia_mm==70 and np.isnan(first.temp_c)
    assert first.humedad_pct==80
    assert first.dias_temp_c==3
    monkeypatch.setattr(C,'MIN_WEEKS_MUNICIPIO',1)
    model_table=build_weekly(p,t,h)
    assert len(model_table)==1 and len(climate)==2


def test_calendar_gaps_are_nan_and_observed_zero_stays_zero():
    d=pd.DataFrame({'municipio':['M','M'],'semana':pd.to_datetime(['2024-01-07','2024-01-21']),
                    'lluvia_mm':[0.,14.],'temp_c':[22.,23.]})
    view=calendar_view(d,'M','2024-01-21',weeks=None)
    assert len(view)==3
    assert view.iloc[0].lluvia_mm==0
    assert view.iloc[1][['lluvia_mm','temp_c','humedad_pct']].isna().all()
    assert view.iloc[2].lluvia_mm==14
    trailing=calendar_view(d,'M','2024-01-28',weeks=2)
    assert len(trailing)==2 and np.isnan(trailing.iloc[-1].lluvia_mm)


def test_window_is_calendar_weeks_and_never_includes_future_week():
    d=pd.DataFrame({'municipio':['M','M'],'semana':pd.to_datetime(['2022-01-09','2026-01-04']),
                    'lluvia_mm':[1.,2.],'temp_c':[22.,23.]})
    view=calendar_view(d,'M','2026-01-09',weeks=4)  # viernes: último domingo 04/01
    assert len(view)==4
    assert view.semana.max()==pd.Timestamp('2026-01-04')
    assert view.lluvia_mm.notna().sum()==1


def test_before_first_record_returns_no_invented_observations():
    d=pd.DataFrame({'municipio':['M'],'semana':pd.to_datetime(['2026-01-04']),'lluvia_mm':[5.]})
    assert calendar_view(d,'M','2025-12-31').empty
