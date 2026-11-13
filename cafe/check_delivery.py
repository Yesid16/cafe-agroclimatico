"""Verifica evidencia mínima; no sustituye revisión académica del informe."""
import json
from . import config as C


def main():
    needed = [C.WEEKLY, C.MODEL_PATH, C.CORPUS_DIR / 'manifest.json']
    needed += [C.RESULTS_DIR / n for n in ['calidad_datos.json', 'metricas_modelo.json',
               'eval_csp.json', 'eval_agente_llm.json', 'eval_agente_mock.json']]
    missing = [str(p.relative_to(C.ROOT)) for p in needed if not p.exists()]
    if missing:
        raise SystemExit('Evidencias pendientes: ' + ', '.join(missing))
    corpus = json.loads((C.CORPUS_DIR / 'manifest.json').read_text(encoding='utf-8'))
    if len(corpus.get('documentos', [])) < 2 or corpus.get('errores'):
        raise SystemExit('Corpus original incompleto')
    quality = json.loads((C.RESULTS_DIR / 'calidad_datos.json').read_text(encoding='utf-8'))
    if quality['cobertura_humedad'] == 0:
        raise SystemExit('No se ha verificado humedad válida para la opción 3.5')
    ev = json.loads((C.RESULTS_DIR / 'eval_agente_llm.json').read_text(encoding='utf-8'))['resumen']
    if not 10 <= ev['n'] <= 15 or ev['n_llm_real'] != ev['n'] or ev['n_agotadas']:
        raise SystemExit('Evaluación LLM incompleta: revisar modo real/límite de iteraciones')
    if ev['citas_requeridas_ok'] < ev['n_cita_requerida']:
        print(f"AVISO: evaluación original con citas {ev['citas_requeridas_ok']}/{ev['n_cita_requerida']}; ver revisión separada.")
    audit = C.RESULTS_DIR / 'auditoria_datos.json'
    if audit.exists():
        a = json.loads(audit.read_text(encoding='utf-8'))
        if a['filas_para_revision']:
            print(f"AVISO: {a['filas_para_revision']} semanas con banderas de calidad; no se certifican datos meteorológicos.")
    print('Evidencias presentes. Revise fallos, interpretación, informe de máximo 4 páginas y demo.')


if __name__ == '__main__':
    main()
