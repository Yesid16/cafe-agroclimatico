"""CSP implementado desde cero (Parte 1): programación de labores del cultivo de café.

Variables: semana de inicio de cada labor (dominio 0..H-1).
Restricciones:
  - Unarias: cada semana cubierta por la labor debe tener una categoría de lluvia permitida.
  - Capacidad: jornales/semana de las labores activas ≤ capacidad de mano de obra.
  - Binarias: precedencia (A termina antes de que B empiece) y separación mínima entre labores.
Búsqueda: backtracking con MRV + comprobación hacia adelante (forward checking).
`solve(..., smart=False)` desactiva MRV/FC para comparar nodos expandidos (rigor experimental).
"""
from dataclasses import dataclass, field


@dataclass
class Labor:
    nombre: str
    duracion: int            # semanas consecutivas
    jornales_ha: float       # jornales por hectárea por semana
    lluvia_ok: tuple         # categorías de lluvia permitidas en cada semana de la labor
    descripcion: str = ""


# Catálogo por defecto (valores orientativos del equipo; ajústelos con el agrónomo/la finca)
CATALOGO = {
    "deshierba": Labor("deshierba", 1, 4.0, ("Baja", "Media"), "Control de arvenses (plateo/guadaña)"),
    "fertilizacion": Labor("fertilizacion", 1, 3.0, ("Media",),
                           "Aplicar con suelo húmedo; evitar lluvia fuerte (arrastre) y sequía"),
    "aspersion_roya": Labor("aspersion_roya", 1, 2.5, ("Baja", "Media"),
                            "Control de roya si el monitoreo lo indica; no aplicar con lluvia fuerte"),
    "recoleccion": Labor("recoleccion", 2, 8.0, ("Baja", "Media"), "Cosecha selectiva (2 semanas)"),
    "poda_zoca": Labor("poda_zoca", 1, 5.0, ("Baja", "Media"), "Renovación/poda de lotes"),
}
# (A, B, tipo, k): "antes" → fin(A) < inicio(B); "sep" → |inicio(A)-inicio(B)| >= k
RESTRICCIONES_DEFECTO = [("deshierba", "fertilizacion", "antes", 0),
                         ("fertilizacion", "aspersion_roya", "sep", 1)]


@dataclass
class CSPResult:
    ok: bool
    asignacion: dict = field(default_factory=dict)
    nodos: int = 0
    motivo: str = ""


def solve(labores: list, clima: list, capacidad: float, hectareas: float = 1.0,
          restricciones: list | None = None, smart: bool = True, max_nodos: int = 200000) -> CSPResult:
    """clima: lista (len=H) con la categoría de lluvia esperada por semana."""
    if capacidad <= 0 or hectareas <= 0:
        return CSPResult(False, motivo="Capacidad y hectáreas deben ser positivas.")
    if not labores or not clima:
        return CSPResult(False, motivo="Se requieren labores y horizonte de clima.")
    if len({l.nombre for l in labores}) != len(labores):
        return CSPResult(False, motivo="Labores duplicadas.")
    H = len(clima)
    names = [l.nombre for l in labores]
    L = {l.nombre: l for l in labores}
    rest = [r for r in (RESTRICCIONES_DEFECTO if restricciones is None else restricciones) if r[0] in L and r[1] in L]
    jor = {n: L[n].jornales_ha * hectareas for n in names}

    # 1) consistencia de nodo (restricciones unarias + capacidad individual)
    dom = {}
    for n in names:
        lab = L[n]
        dom[n] = [s for s in range(H - lab.duracion + 1)
                  if all(clima[w] in lab.lluvia_ok for w in range(s, s + lab.duracion)) and jor[n] <= capacidad]
        if not dom[n]:
            return CSPResult(False, motivo=f"'{n}' no tiene ninguna ventana viable: el clima esperado no es "
                                            f"adecuado (requiere lluvia {'/'.join(lab.lluvia_ok)}) o excede la mano de obra.")

    def carga(asig):
        c = [0.0] * H
        for n, s in asig.items():
            for w in range(s, s + L[n].duracion):
                c[w] += jor[n]
        return c

    def consistente(asig, n, s):
        a = dict(asig)
        a[n] = s
        if max(carga(a)) > capacidad + 1e-9:
            return False
        for A, B, tipo, k in rest:
            if A in a and B in a:
                if tipo == "antes" and not (a[A] + L[A].duracion - 1 < a[B]):
                    return False
                if tipo == "sep" and abs(a[A] - a[B]) < k:
                    return False
        return True

    nodos = [0]

    def bt(asig, dominios):
        if len(asig) == len(names):
            return dict(asig)
        if nodos[0] >= max_nodos:
            return None
        libres = [n for n in names if n not in asig]
        n = min(libres, key=lambda x: len(dominios[x])) if smart else libres[0]  # MRV vs orden fijo
        for s in sorted(dominios[n]):
            if nodos[0] >= max_nodos:
                return None
            nodos[0] += 1
            if not consistente(asig, n, s):
                continue
            asig[n] = s
            nuevo = dominios
            if smart:  # forward checking
                nuevo = {m: [v for v in dominios[m] if m in asig or consistente(asig, m, v)] for m in names}
                if any(not nuevo[m] for m in libres if m != n):
                    del asig[n]
                    continue
            r = bt(asig, nuevo)
            if r:
                return r
            del asig[n]
        return None

    sol = bt({}, dom)
    if sol is None and nodos[0] >= max_nodos:
        return CSPResult(False, nodos=nodos[0], motivo="Límite de búsqueda alcanzado; factibilidad no determinada.")
    if sol is None:
        return CSPResult(False, nodos=nodos[0], motivo="No existe calendario que cumpla todas las restricciones "
                         "(capacidad de mano de obra, precedencias y clima esperado). Amplíe el horizonte o la capacidad.")
    return CSPResult(True, sol, nodos[0])
