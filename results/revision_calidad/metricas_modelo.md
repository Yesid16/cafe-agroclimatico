Corte temporal: entrenamiento ≤ 2026-02-22; n_train=2689, n_test=976; parámetros de la red=919.

| Modelo | Accuracy | F1 macro | Brier | Log-loss |
|---|---|---|---|---|
| Mayoritaria (línea base 1) | 0.3371 | 0.1681 | 0.6673 | 1.0995 |
| Persistencia Riesgo_t (línea base 2) | 0.7797 | 0.7742 | 0.3895 | 0.7421 |
| Regresión logística (referencia sklearn) | 0.7982 | 0.7914 | 0.317 | 0.5437 |
| Red bayesiana propia (VE) | 0.7428 | 0.7407 | 0.374 | 0.6577 |