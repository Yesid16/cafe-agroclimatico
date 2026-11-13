import pytest
from cafe.compare_quality import compare_metrics


def metrics(name,value):
    return {'modelo':name,'accuracy':value,'f1_macro':value,'brier':value,'log_loss':value}


def test_comparison_preserves_both_metrics_and_delta():
    x=compare_metrics({'resultados':[metrics('BN',.7453)]},{'resultados':[metrics('BN',.7407)]})
    assert x[0]['f1_macro_original']==.7453
    assert x[0]['f1_macro_conservador']==.7407
    assert x[0]['delta_f1_macro']==-.0046


def test_comparison_rejects_missing_or_mismatched_models():
    with pytest.raises(ValueError):
        compare_metrics({'resultados':[metrics('BN',.7)]},{'resultados':[]})
    with pytest.raises(ValueError):
        compare_metrics({'resultados':[metrics('BN',.7)]},{'resultados':[metrics('Other',.7)]})
