"""Limpieza y agregación: estación-día → municipio-semana (semanas que terminan en domingo)."""
import unicodedata

import numpy as np
import pandas as pd

from . import config as C


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def _municipio_dia(path, kind: str, min_n: int) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["dia"] = pd.to_datetime(df["dia"])
    df = df[df["n"] >= min_n].dropna(subset=["valor", "municipio"])
    df["municipio"] = df["municipio"].map(norm)
    df["departamento"] = df["departamento"].map(norm)
    # por estación-día ya viene agregado; ahora promedio entre estaciones del municipio
    g = df.groupby(["departamento", "municipio", "dia"]).agg(
        valor=("valor", "mean"), n_est=("codigoestacion", "nunique"),
        lat=("latitud", "mean"), lon=("longitud", "mean")).reset_index()
    return g.rename(columns={"valor": kind, "n_est": f"n_est_{kind}"})


def _weekly(g: pd.DataFrame, col: str, how: str, min_days: int) -> pd.DataFrame:
    out = []
    for (dep, mun), d in g.groupby(["departamento", "municipio"]):
        s = d.set_index("dia")[col]
        w = s.resample("W-SUN")
        cnt = w.count()
        v = w.sum() * 7 / cnt.replace(0, np.nan) if how == "sum" else w.mean()
        v[cnt < min_days] = np.nan
        o = v.rename(col).reset_index().rename(columns={"dia": "semana"})
        o["departamento"], o["municipio"] = dep, mun
        o["lat"], o["lon"] = d["lat"].mean(), d["lon"].mean()
        o[f"n_est_{col}"] = d[f"n_est_{col}"].max()
        out.append(o)
    return pd.concat(out, ignore_index=True)


def build_weekly() -> pd.DataFrame:
    p = _municipio_dia(C.PRECIP_DAILY, "lluvia_mm", C.MIN_N_DAY)
    t = _municipio_dia(C.TEMP_DAILY, "temp_c", C.MIN_N_DAY)
    wp = _weekly(p, "lluvia_mm", "sum", C.MIN_DAYS_WEEK_RAIN)
    wt = _weekly(t, "temp_c", "mean", C.MIN_DAYS_WEEK_TEMP)
    w = wp.merge(wt[["departamento", "municipio", "semana", "temp_c", "n_est_temp_c"]],
                 on=["departamento", "municipio", "semana"], how="inner")
    w = w.dropna(subset=["lluvia_mm", "temp_c"])
    keep = w.groupby("municipio")["semana"].count()
    keep = keep[keep >= C.MIN_WEEKS_MUNICIPIO].index
    w = w[w["municipio"].isin(keep)].sort_values(["municipio", "semana"]).reset_index(drop=True)
    return w


def main():
    w = build_weekly()
    C.DATA_PROC.mkdir(parents=True, exist_ok=True)
    w.to_csv(C.WEEKLY, index=False)
    print(f"{len(w)} filas semana-municipio, {w['municipio'].nunique()} municipios, "
          f"{w['semana'].min():%Y-%m-%d} → {w['semana'].max():%Y-%m-%d} → {C.WEEKLY}")


if __name__ == "__main__":
    main()
