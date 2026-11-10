"""SOLO PARA PRUEBAS AUTOMÁTICAS. Genera datos SINTÉTICOS con el mismo esquema que la descarga real.
NO son datos reales y nunca deben usarse en el informe ni en los resultados."""
import numpy as np
import pandas as pd


def make_raw(outdir, n_mun=4, start="2022-01-03", weeks=170, seed=0):
    rng = np.random.default_rng(seed)
    days = pd.date_range(start, periods=weeks * 7, freq="D")
    P, T = [], []
    for k in range(n_mun):
        mun = ["CHINCHINA", "SALGAR", "JARDIN", "ANDES", "MANIZALES"][k]
        lat, lon = 5 + 0.3 * k, -75.6 + 0.1 * k
        season = np.sin(2 * np.pi * (days.dayofyear / 365.0) * 2)  # bimodal
        rain = np.clip(rng.gamma(1.2, 4.0, len(days)) * (1.2 + season), 0, None)
        temp = 21 + 2 * np.sin(2 * np.pi * days.dayofyear / 365.0) + rng.normal(0, 1, len(days)) - 0.5 * k
        for e in range(2):
            P.append(pd.DataFrame({"codigoestacion": f"{k}{e}", "municipio": mun.title(), "departamento": "Caldas",
                                   "latitud": lat, "longitud": lon, "dia": days, "valor": rain * rng.uniform(.9, 1.1), "n": 144}))
            T.append(pd.DataFrame({"codigoestacion": f"{k}{e}", "municipio": mun.title(), "departamento": "Caldas",
                                   "latitud": lat, "longitud": lon, "dia": days, "valor": temp, "n": 144}))
    pd.concat(P).to_csv(outdir / "precip_diaria.csv", index=False)
    pd.concat(T).to_csv(outdir / "temp_diaria.csv", index=False)
