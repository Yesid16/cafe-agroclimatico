from cafe.answer_validation import validate_citations
from cafe.agent import _finalize_llm
from cafe.evaluate_agent import score_case


def test_citations_require_each_tool_and_reject_placeholders():
    trace = [{'tool':'risk','result':{'cita':'[IDEAM]'}},
             {'tool':'schedule','result':{'cita':'[CSP]'}}]
    assert not validate_citations('[IDEAM]',trace)['ok']
    assert not validate_citations('[IDEAM] [CSP] [archivo.md#1]',trace)['ok']
    assert validate_citations('[IDEAM] [CSP]',trace)['ok']


def test_invalid_llm_citations_use_visible_tool_summary():
    result = {'municipio':'A', 'semanas':[], 'cita':'[IDEAM]'}
    trace=[{'tool':'weather_summary','result':result}]
    out=_finalize_llm('clima','Inventado [archivo.md#1]',trace,2)
    assert out['answer_source']=='tool_summary'
    assert out['raw_answer']=='Inventado [archivo.md#1]'
    assert 'Inventado' not in out['answer']
    assert '[IDEAM]' in out['answer'] and '\n\n' in out['answer']


def test_successful_retry_supersedes_error_in_summary():
    trace=[{'tool':'weather_summary','result':{'error':"Datos faltantes ['A']"}},
           {'tool':'weather_summary','result':{'municipio':'A','semanas':[],'cita':'[IDEAM]'}}]
    out=_finalize_llm('clima','[archivo.md#1]',trace,3)
    assert 'Datos faltantes' not in out['answer']
    assert score_case({'tools':['weather_summary'],'cita':True},out)['cita_ok']


def test_valid_llm_answer_is_retained():
    trace=[{'tool':'search_docs','result':{'resultados':[{'cita':'[doc.pdf:p1#0]','texto':'texto'}]}}]
    answer='Respuesta con evidencia [doc.pdf:p1#0]'
    out=_finalize_llm('concepto',answer,trace,2)
    assert out['answer_source']=='llm' and out['answer']==answer


def test_truncation_uses_tool_summary_even_with_valid_tag():
    trace=[{'tool':'weather_summary','result':{'municipio':'A','semanas':[],'cita':'[IDEAM]'}}]
    out=_finalize_llm('clima','[IDEAM] texto cortado',trace,2,'length')
    assert out['answer_source']=='tool_summary'
