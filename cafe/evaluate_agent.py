"""Evalúa el agente con preguntas fijas: ¿llamó a las herramientas correctas? ¿citó la fuente?
Uso: python -m cafe.evaluate_agent [--mock]   (sin --mock usa el LLM si hay LLM_API_KEY)"""
import argparse
import json
import re

from . import config as C
from . import tools as T
from .agent import OUT_OF_SCOPE, run_agent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mock", action="store_true")
    a = ap.parse_args()
    qs = json.loads((C.ROOT / "eval" / "preguntas.json").read_text(encoding="utf-8"))
    mun = T.municipios()[0]
    ctx = {"municipio": mun}
    rows, ok_tool, ok_cit = [], 0, 0
    for q in qs:
        text = q["pregunta"].format(municipio=mun.title())
        out = run_agent(text, ctx, force_mock=a.mock)
        called = [t["tool"] for t in out["trace"]]
        tool_ok = set(q["tools"]) <= set(called) and (called == [] if not q["tools"] else True)
        errs = [t for t in out["trace"] if "error" in t["result"]]
        if q.get("espera_error"):
            tool_ok = tool_ok and bool(errs)  # la herramienta debe devolver error y el agente explicarlo
        tags = set(re.findall(r"\[[^\]]+\]", out["answer"]))
        valid = set()
        for t in out["trace"]:
            r = t["result"]
            if "cita" in r:
                valid.add(r["cita"])
            valid |= {h["cita"] for h in r.get("resultados", [])}
        cited = bool(tags & valid)
        cit_ok = cited if q["cita"] else True
        ok_tool += tool_ok
        ok_cit += cit_ok
        rows.append({"id": q["id"], "pregunta": text, "esperadas": q["tools"], "llamadas": called,
                     "herramienta_ok": tool_ok, "cita_ok": cit_ok, "iter": out["iterations"], "modo": out["mode"]})
    n = len(qs)
    md = [f"Modo: {rows[0]['modo']}. Herramienta correcta: **{ok_tool}/{n}**; cita de fuente (donde aplica): **{ok_cit}/{n}**.", "",
          "| # | Pregunta | Esperadas | Llamadas | Herr. OK | Cita OK |", "|---|---|---|---|---|---|"]
    md += [f"| {r['id']} | {r['pregunta']} | {', '.join(r['esperadas']) or '—'} | {', '.join(r['llamadas']) or '—'} | "
           f"{'✅' if r['herramienta_ok'] else '❌'} | {'✅' if r['cita_ok'] else '❌'} |" for r in rows]
    C.RESULTS_DIR.mkdir(exist_ok=True)
    (C.RESULTS_DIR / "eval_agente.md").write_text("\n".join(md), encoding="utf-8")
    (C.RESULTS_DIR / "eval_agente.json").write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n".join(md))


if __name__ == "__main__":
    main()
