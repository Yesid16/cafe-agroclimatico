"""Red bayesiana discreta implementada desde cero (Parte 1).

- Factor: producto, marginalización y restricción (evidencia) sobre arreglos numpy.
- DiscreteBN: aprendizaje de CPTs por conteo con suavizado de Laplace + inferencia exacta
  por ELIMINACIÓN DE VARIABLES (orden de mínimo grado). También hay enumeración por fuerza
  bruta (`query_bruteforce`) usada solo en las pruebas para verificar la corrección.
"""
import itertools

import numpy as np
import pandas as pd


class Factor:
    def __init__(self, variables, values):
        self.vars = list(variables)
        self.values = np.asarray(values, dtype=float)
        assert self.values.ndim == len(self.vars)

    def restrict(self, var, idx):
        if var not in self.vars:
            return self
        ax = self.vars.index(var)
        return Factor([v for v in self.vars if v != var], np.take(self.values, idx, axis=ax))

    def marginalize(self, var):
        ax = self.vars.index(var)
        return Factor([v for v in self.vars if v != var], self.values.sum(axis=ax))

    def multiply(self, other):
        union = self.vars + [v for v in other.vars if v not in self.vars]
        letter = {v: chr(97 + i) for i, v in enumerate(union)}
        sa = "".join(letter[v] for v in self.vars)
        sb = "".join(letter[v] for v in other.vars)
        so = "".join(letter[v] for v in union)
        return Factor(union, np.einsum(f"{sa},{sb}->{so}", self.values, other.values))


class DiscreteBN:
    def __init__(self, structure: dict, states: dict, alpha: float = 1.0):
        """structure: nodo -> lista de padres; states: nodo -> lista de estados."""
        self.parents = structure
        self.states = states
        self.alpha = alpha
        self.cpt: dict[str, Factor] = {}

    # ---------- aprendizaje ----------
    def fit(self, df: pd.DataFrame):
        for node, pa in self.parents.items():
            cols = pa + [node]
            idx = [df[c].map({s: i for i, s in enumerate(self.states[c])}) for c in cols]
            mask = np.logical_and.reduce([i.notna() for i in idx])
            shape = [len(self.states[c]) for c in cols]
            counts = np.zeros(shape)
            np.add.at(counts, tuple(i[mask].astype(int).values for i in idx), 1)
            counts += self.alpha
            self.cpt[node] = Factor(cols, counts / counts.sum(axis=-1, keepdims=True))
        return self

    def n_params(self):
        return sum(int(np.prod(f.values.shape[:-1])) * (f.values.shape[-1] - 1) for f in self.cpt.values())

    # ---------- inferencia exacta: eliminación de variables ----------
    def query(self, target: str, evidence: dict | None = None) -> dict:
        evidence = {k: v for k, v in (evidence or {}).items() if v is not None and k != target}
        factors = []
        for node, f in self.cpt.items():
            for var, val in evidence.items():
                f = f.restrict(var, self.states[var].index(val))
            factors.append(f)
        hidden = [v for v in self.cpt if v != target and v not in evidence]
        while hidden:
            # heurística de mínimo grado: variable que aparece con menos vecinos
            def degree(v):
                nb = set()
                for f in factors:
                    if v in f.vars:
                        nb |= set(f.vars)
                return len(nb)
            v = min(hidden, key=degree)
            hidden.remove(v)
            related = [f for f in factors if v in f.vars]
            factors = [f for f in factors if v not in f.vars]
            if not related:
                continue
            prod = related[0]
            for f in related[1:]:
                prod = prod.multiply(f)
            factors.append(prod.marginalize(v))
        res = factors[0]
        for f in factors[1:]:
            res = res.multiply(f)
        vals = res.values / res.values.sum()
        return dict(zip(self.states[target], vals.tolist()))

    # ---------- referencia por enumeración (solo pruebas) ----------
    def query_bruteforce(self, target: str, evidence: dict | None = None) -> dict:
        evidence = evidence or {}
        nodes = list(self.cpt)
        out = np.zeros(len(self.states[target]))
        for combo in itertools.product(*[range(len(self.states[n])) for n in nodes]):
            a = dict(zip(nodes, combo))
            if any(self.states[k][a[k]] != v for k, v in evidence.items()):
                continue
            p = 1.0
            for n in nodes:
                f = self.cpt[n]
                p *= f.values[tuple(a[v] for v in f.vars)]
            out[a[target]] += p
        out /= out.sum()
        return dict(zip(self.states[target], out.tolist()))
