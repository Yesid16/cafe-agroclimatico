"""Comprueba etiquetas contra las fuentes de las observaciones, no su veracidad semántica."""
import re


def validate_citations(answer, trace):
    tags = set(re.findall(r'\[[^\]]+\]', answer))
    valid = set()
    required = []
    for item in trace:
        result = item['result']
        if 'error' in result:
            continue
        sources = set()
        if result.get('cita'):
            sources.add(result['cita'])
        sources.update(h['cita'] for h in result.get('resultados', []) if h.get('cita'))
        valid.update(sources)
        if sources:
            required.append((item['tool'], sources))
    missing = [name for name, sources in required if not tags.intersection(sources)]
    invented = sorted(tags - valid)
    return {'ok': not missing and not invented,
            'citas_no_respaldadas': invented, 'herramientas_sin_cita': sorted(set(missing))}
