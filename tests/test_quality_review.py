from datetime import timedelta
import pandas as pd
from cafe.quality_review import repeated_rate_flags, coverage_mask


def rows(values, n=None, days=None, stations=None):
    count=len(values)
    return pd.DataFrame({'codigoestacion':stations or ['001']*count,
        'dia':pd.to_datetime(days) if days else pd.date_range('2022-01-01',periods=count),
        'valor':values,'n':n or [144]*count,'n_total':n or [144]*count,'horas':[24]*count})


def test_same_positive_rate_with_varying_counts_is_flagged():
    x=rows([288.,240.,200.],n=[144,120,100])
    assert repeated_rate_flags(x).all()


def test_gaps_stations_and_changing_rate_do_not_form_a_run():
    assert not repeated_rate_flags(rows([288.,288.,288.],
        days=['2022-01-01','2022-01-02','2022-01-04'])).any()
    assert not repeated_rate_flags(rows([288.,288.,288.],stations=['001','002','003'])).any()
    assert not repeated_rate_flags(rows([288.,240.,200.])).any()


def test_zero_rain_and_short_series_are_retained():
    assert not repeated_rate_flags(rows([0.,0.,0.,0.])).any()
    assert not repeated_rate_flags(rows([288.,288.])).any()


def test_duplicate_counts_are_not_validated_by_dividing_sum():
    x=rows([288.,288.,288.])
    x['n_total']=288
    assert not coverage_mask(x,72).any()
    assert not repeated_rate_flags(x).any()


def test_experiment_directories_are_separate_and_restored(tmp_path, monkeypatch):
    import os
    from cafe.review_experiment import experiment_environment
    monkeypatch.setenv('CAFE_DATA_PROC','prior')
    monkeypatch.delenv('CAFE_RESULTS_DIR',raising=False)
    try:
        with experiment_environment(tmp_path):
            assert os.environ['CAFE_DATA_PROC']==str(tmp_path/'data/review/processed')
            assert os.environ['CAFE_RESULTS_DIR']==str(tmp_path/'results/revision_calidad')
            raise ValueError('simulated failed cloud execution')
    except ValueError:
        pass
    assert os.environ['CAFE_DATA_PROC']=='prior'
    assert 'CAFE_RESULTS_DIR' not in os.environ
