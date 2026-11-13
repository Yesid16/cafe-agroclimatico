"""Evaluación fija: distingue LLM real, respaldo y herramientas que fallaron."""
import argparse
import json
import re
from datetime import datetime, timezone
from . import config as C
from . import tools as T
from .agent import run_agent


def score_case(q, out):
    trace = out['trace']
    called = {t['tool'] for t in trace}
    success = {t['tool'] for t in trace if 'error' not in t['result']}
    expected = set(q['tools'])
    errors = [t for t in trace if 'error' in t['result']]
    tool_ok = expected <= success if expected else not called
    if q.get('espera_error'):
        tool_ok = expected <= called and bool(errors)
    tags = set(re.findall(r'\[[^\]]+\]', out['answer']))
    valid = set()
    for t in trace:
        r = t['result']
        if 'error' in r:
            continue
        if 'cita' in r:
            valid.add(r['cita'])
        valid.update(h['cita'] for h in r.get('resultados', []))
    # Una etiqueta válida no disculpa citas inventadas adicionales.
    citation_ok = bool(tags & valid) and not (tags - valid) if q['cita'] else not (tags - valid)
    return {'herramienta_ok': bool(tool_ok), 'cita_ok': bool(citation_ok),
            'errores_herramienta': len(errors), 'llamadas': sorted(called),
            'citas_validas': sorted(tags & valid), 'citas_no_respaldadas': sorted(tags - valid)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mock', action='store_true')
    ap.add_argument('--tag', default='', choices=['', 'revisado'])
    args = ap.parse_args()
    if not args.mock and not C.LLM_API_KEY:
        ap.error('La evaluación LLM exige LLM_API_KEY; use --mock para el respaldo')
    questions = json.loads((C.ROOT / 'eval' / 'preguntas.json').read_text(encoding='utf-8'))
    if not 10 <= len(questions) <= 15:
        raise ValueError('La entrega exige entre 10 y 15 preguntas')
    mun = T.municipios()[0]
    rows = []
    for q in questions:
        text = q['pregunta'].format(municipio=mun.title())
        out = run_agent(text, {'municipio': mun}, force_mock=args.mock)
        raw_score = score_case(q, {**out, 'answer': out.get('raw_answer', out['answer'])})
        row = {'id': q['id'], 'pregunta': text, 'esperadas': q['tools'], **score_case(q, out),
               'modo': out['mode'], 'iter': out['iterations'], 'answer': out['answer'],
               'trace': out['trace'], 'exhausted': out.get('exhausted', False),
               'raw_answer': out.get('raw_answer', out['answer']),
               'cita_original_ok': raw_score['cita_ok'] if out['mode'] == 'llm' else None,
               'answer_source': out.get('answer_source', out['mode']),
               'citation_validation': out.get('citation_validation')}
        rows.append(row)
        print(q['id'], row['modo'], row['herramienta_ok'], row['cita_ok'], flush=True)
    n = len(rows)
    summary = {'modo_solicitado': 'mock' if args.mock else 'llm', 'modelo': None if args.mock else C.LLM_MODEL,
        'utc': datetime.now(timezone.utc).isoformat(), 'n': n,
        'herramienta_ok': sum(r['herramienta_ok'] for r in rows), 'cita_ok': sum(r['cita_ok'] for r in rows),
        'n_cita_requerida': sum(q['cita'] for q in questions),
        'citas_requeridas_ok': sum(r['cita_ok'] for q, r in zip(questions, rows) if q['cita']),
        'n_llm_real': sum(r['modo'] == 'llm' for r in rows),
        'n_fallback': sum(r['modo'] == 'fallback' for r in rows),
        'n_agotadas': sum(r['exhausted'] for r in rows),
        'n_resumen_herramientas': sum(r['answer_source'] == 'tool_summary' for r in rows),
        'citas_originales_requeridas_ok': sum(bool(r['cita_original_ok']) for q,r in zip(questions,rows) if q['cita'] and r['modo']=='llm'),
        'n_citas_requeridas_llm': sum(q['cita'] and r['modo']=='llm' for q,r in zip(questions,rows))}
    mode = summary['modo_solicitado']
    suffix = f'_{args.tag}' if args.tag else ''
    md = [f"Modo solicitado: {mode}; modelo: {summary['modelo']}. Herramienta correcta: {summary['herramienta_ok']}/{n}; "
          f"cita donde se exige: {summary['citas_requeridas_ok']}/{summary['n_cita_requerida']}; "
          f"LLM real: {summary['n_llm_real']}; respaldo: {summary['n_fallback']}; límite alcanzado: {summary['n_agotadas']}.",
          f"Citas originales del LLM: {summary['citas_originales_requeridas_ok']}/{summary['n_citas_requeridas_llm']}; "
          f"respuestas sustituidas por resumen de herramientas: {summary['n_resumen_herramientas']}. No equivale a acierto autónomo del LLM.", '',
          '| # | Pregunta | Esperadas | Llamadas | Herr. OK | Cita OK | Modo |', '|---|---|---|---|---|---|---|']
    md += [f"| {r['id']} | {r['pregunta']} | {', '.join(r['esperadas'])} | {', '.join(r['llamadas'])} | {r['herramienta_ok']} | {r['cita_ok']} | {r['modo']} |" for r in rows]
    C.RESULTS_DIR.mkdir(exist_ok=True)
    (C.RESULTS_DIR / f'eval_agente_{mode}{suffix}.md').write_text('\n'.join(md), encoding='utf-8')
    (C.RESULTS_DIR / f'eval_agente_{mode}{suffix}.json').write_text(json.dumps({'resumen': summary, 'preguntas': rows}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('\n'.join(md))
    if not args.mock and summary['n_llm_real'] != n:
        raise SystemExit('Evaluación LLM incompleta: hubo respaldos; no reportar como LLM íntegro')


if __name__ == '__main__':
    main()
