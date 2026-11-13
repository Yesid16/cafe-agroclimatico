"""Comprueba acceso de bajo volumen; nunca imprime claves ni ejecuta modelos locales."""
import json
from datetime import datetime, timezone
import requests
from openai import OpenAI
from cafe import config as C


def main():
    report = {'utc': datetime.now(timezone.utc).isoformat(), 'ideam': [], 'nvidia': {}}
    for ds in (C.DS_PRECIP, C.DS_TEMP, C.DS_HUM):
        meta = requests.get(f'https://www.datos.gov.co/api/views/{ds}.json', timeout=45)
        meta.raise_for_status()
        probe = requests.get(f'{C.SOCRATA_BASE}/{ds}.json', params={'$limit': 1}, timeout=45)
        probe.raise_for_status()
        sample = probe.json()
        first = sample[0]
        day = first['fechaobservacion'][:10]
        aggregate = requests.get(f'{C.SOCRATA_BASE}/{ds}.json', params={
            '$select': 'codigoestacion, date_trunc_ymd(fechaobservacion) as dia, count(distinct date_extract_hh(fechaobservacion)) as horas',
            '$where': f"codigoestacion = '{first['codigoestacion']}' AND fechaobservacion between '{day}T00:00:00' and '{day}T23:59:59'",
            '$group': 'codigoestacion, dia', '$limit': 1}, timeout=45)
        aggregate.raise_for_status()
        report['ideam'].append({'id': ds, 'metadata_status': meta.status_code, 'data_status': probe.status_code,
            'nombre': meta.json()['name'], 'muestra': sample, 'prueba_horas': aggregate.json(),
            'descripcion': meta.json().get('description'), 'url': f'{C.SOCRATA_BASE}/{ds}.json'})
    client = OpenAI(api_key=C.LLM_API_KEY, base_url=C.LLM_BASE_URL, timeout=C.LLM_TIMEOUT, max_retries=0)
    schema = {'type': 'function', 'function': {'name': 'search_docs', 'description': 'Buscar documentos técnicos',
              'parameters': {'type': 'object', 'properties': {'query': {'type': 'string'}}, 'required': ['query']}}}
    try:
        out = client.chat.completions.create(model=C.LLM_MODEL, messages=[{'role': 'user', 'content':
            'Usa search_docs para consultar condiciones de la roya del café.'}], tools=[schema],
            tool_choice='auto', max_tokens=512, temperature=0)
        calls = [tc.function.name for tc in (out.choices[0].message.tool_calls or [])]
        report['nvidia'] = {'modelo': out.model, 'tool_calling_ok': 'search_docs' in calls,
                            'tools': calls, 'tokens': out.usage.total_tokens if out.usage else None}
    except Exception as exc:
        report['nvidia'] = {'modelo': C.LLM_MODEL, 'tool_calling_ok': False, 'error': type(exc).__name__}
    C.RESULTS_DIR.mkdir(exist_ok=True)
    path = C.RESULTS_DIR / 'verificacion_servicios.json'
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'ideam': [x['data_status'] for x in report['ideam']], 'nvidia': report['nvidia']}, ensure_ascii=False))
    if not report['nvidia']['tool_calling_ok']:
        raise SystemExit('La prueba de herramientas NVIDIA falló')


if __name__ == '__main__':
    main()
