"""Descarga datos reales del IDEAM (datos.gov.co, API Socrata) YA AGREGADOS POR DÍA en el servidor.

Uso:
    python -m cafe.data_download --desde 2022-01-01 --hasta 2026-10-31

Escribe data/raw/precip_diaria.csv y data/raw/temp_diaria.csv con columnas:
    codigoestacion, municipio, departamento, latitud, longitud, dia, valor, n
  - precipitación: valor = suma diaria (mm);  temperatura: valor = promedio diario (°C)
  - n = número de lecturas del día (se usa para filtrar días incompletos)

PLAN B (si la API falla): descargue manualmente un CSV con esas mismas columnas
(p. ej. desde DHIME o el botón "Exportar" de datos.gov.co) y guárdelo en data/raw/.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date
import time

import pandas as pd
import requests

from . import config as C

PAGE = 50000


def _query(ds: str, params: dict, retries: int = 4) -> list:
    url = f"{C.SOCRATA_BASE}/{ds}.json"
    headers = {"X-App-Token": C.SOCRATA_APP_TOKEN} if C.SOCRATA_APP_TOKEN else {}
    for i in range(retries):
        try:
            r = requests.get(url, params=params, headers=headers, timeout=180)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            wait = 2 ** (i + 1)
            print(f"   reintento {i + 1}/{retries} ({e}); espero {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Falló la consulta a {ds}. Use el plan B (CSV manual en data/raw/).")


def _months(desde: date, hasta: date):
    y, m = desde.year, desde.month
    while (y, m) <= (hasta.year, hasta.month):
        ny, nm = (y + 1, 1) if m == 12 else (y, m + 1)
        yield date(y, m, 1), date(ny, nm, 1)
        y, m = ny, nm


def download(ds: str, agg: str, vmin: float, vmax: float, desde: date, hasta: date) -> pd.DataFrame:
    deptos = ",".join(f"'{d}'" for d in C.DEPARTAMENTOS)
    months_list = list(_months(desde, hasta))

    def _fetch_month(span):
        ini, fin = span
        where = (f"upper(departamento) in({deptos}) AND fechaobservacion >= '{ini}T00:00:00' "
                 f"AND fechaobservacion < '{fin}T00:00:00' AND valorobservado >= {vmin} "
                 f"AND valorobservado <= {vmax}")
        offset = 0
        mframes = []
        while True:
            rows = _query(ds, {
                "$select": ("codigoestacion, municipio, departamento, latitud, longitud, "
                            f"date_trunc_ymd(fechaobservacion) as dia, {agg}(valorobservado) as valor, "
                            "count(*) as n"),
                "$where": where,
                "$group": "codigoestacion, municipio, departamento, latitud, longitud, dia",
                "$limit": PAGE, "$offset": offset})
            if rows:
                mframes.append(pd.DataFrame(rows))
            if len(rows) < PAGE:
                break
            offset += PAGE
        print(f"  {ds} {ini:%Y-%m}: ok", flush=True)
        return mframes

    frames = []
    with ThreadPoolExecutor(max_workers=4) as ex:
        for month_frames in ex.map(_fetch_month, months_list):
            frames.extend(month_frames)

    if not frames:
        raise RuntimeError(f"Sin datos para {ds} en el rango pedido.")
    df = pd.concat(frames, ignore_index=True)
    df["dia"] = pd.to_datetime(df["dia"]).dt.date
    for c in ("valor", "n", "latitud", "longitud"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2022-01-01")
    ap.add_argument("--hasta", default=date.today().isoformat())
    a = ap.parse_args()
    d0, d1 = date.fromisoformat(a.desde), date.fromisoformat(a.hasta)
    C.DATA_RAW.mkdir(parents=True, exist_ok=True)
    print("Precipitación (suma diaria, mm)…")
    # Lectura por 10 min: valores válidos 0–100 mm; más allá se asume error de sensor
    download(C.DS_PRECIP, "sum", 0, 100, d0, d1).to_csv(C.PRECIP_DAILY, index=False)
    print("Temperatura (promedio diario, °C)…")
    download(C.DS_TEMP, "avg", -5, 45, d0, d1).to_csv(C.TEMP_DAILY, index=False)
    C.DEMO_MARKER.unlink(missing_ok=True)
    print("Listo →", C.PRECIP_DAILY, C.TEMP_DAILY)


if __name__ == "__main__":
    main()
