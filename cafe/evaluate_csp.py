"""Comparación CSP en escenarios controlados, no son mediciones agronómicas."""
import json
from . import config as C
from . import csp


def main():
    escenarios = {
        'mixto': (['Media', 'Baja', 'Media', 'Alta', 'Media', 'Media', 'Baja', 'Media'], 20),
        'solo_alta': (['Alta'] * 8, 20),
        'capacidad_baja': (['Media'] * 8, 5),
    }
    labs = [csp.CATALOGO[n] for n in ('deshierba', 'fertilizacion', 'recoleccion')]
    rows = []
    for name, (clima, cap) in escenarios.items():
        for smart in (False, True):
            r = csp.solve(labs, clima, cap, smart=smart)
            rows.append({'escenario': name, 'smart': smart, 'factible': r.ok,
                         'nodos': r.nodos, 'asignacion': r.asignacion, 'motivo': r.motivo})
    C.RESULTS_DIR.mkdir(exist_ok=True)
    (C.RESULTS_DIR / 'eval_csp.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    md = ['Escenarios controlados; jornales y categorías son supuestos del equipo.', '',
          '| Escenario | MRV/FC | Factible | Nodos |', '|---|---|---|---|']
    md += [f"| {r['escenario']} | {r['smart']} | {r['factible']} | {r['nodos']} |" for r in rows]
    (C.RESULTS_DIR / 'eval_csp.md').write_text('\n'.join(md), encoding='utf-8')
    print('\n'.join(md))


if __name__ == '__main__':
    main()
