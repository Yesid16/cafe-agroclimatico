"""Create a clearly labeled synthetic dataset for a local UI demonstration only."""
import argparse

import numpy as np
import pandas as pd

from . import config as C
from . import data_prep
from .risk_model import RoyaRiskModel


def make_raw(outdir, n_mun=4, start="2022-01-03", weeks=170, seed=0):
    outdir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed)
    days = pd.date_range(start, periods=weeks * 7, freq="D")
    precip, temp_frames = [], []
    for k in range(n_mun):
        municipio = ["CHINCHINA", "SALGAR", "JARDIN", "ANDES", "MANIZALES"][k]
        lat, lon = 5 + 0.3 * k, -75.6 + 0.1 * k
        season = np.sin(2 * np.pi * (days.day_of_year / 365.0) * 2)
        rain = np.clip(rng.gamma(1.2, 4.0, len(days)) * (1.2 + season), 0, None)
        temp = 21 + 2 * np.sin(2 * np.pi * days.day_of_year / 365.0) + rng.normal(0, 1, len(days)) - 0.5 * k
        for station in range(2):
            common = {"codigoestacion": f"{k}{station}", "municipio": municipio.title(),
                      "departamento": "Caldas", "latitud": lat, "longitud": lon, "dia": days, "n": 144}
            precip.append(pd.DataFrame({**common, "valor": rain * rng.uniform(.9, 1.1)}))
            temp_frames.append(pd.DataFrame({**common, "valor": temp}))
    pd.concat(precip).to_csv(outdir / "precip_diaria.csv", index=False)
    pd.concat(temp_frames).to_csv(outdir / "temp_diaria.csv", index=False)


def main():
    parser = argparse.ArgumentParser(description="Prepare synthetic data for local UI testing only.")
    parser.parse_args()
    if C.PRECIP_DAILY.exists() or C.TEMP_DAILY.exists():
        raise SystemExit("Ya existen CSV en data/raw. No se sobrescribieron; muévalos antes de crear la demo.")

    make_raw(C.DATA_RAW)
    weekly = data_prep.build_weekly()
    if weekly.empty:
        raise RuntimeError("No se pudieron crear datos semanales sintéticos.")
    C.DATA_PROC.mkdir(parents=True, exist_ok=True)
    weekly.to_csv(C.WEEKLY, index=False)
    RoyaRiskModel().fit(weekly).save(C.MODEL_PATH)
    C.DEMO_MARKER.write_text("Synthetic demonstration data; not IDEAM observations.\n", encoding="utf-8")
    print(f"Demo lista: {len(weekly)} semanas-municipio, {weekly['municipio'].nunique()} municipios.")
    print("No use estos datos para análisis, evaluaciones ni informes.")


if __name__ == "__main__":
    main()
