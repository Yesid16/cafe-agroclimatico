Corte temporal: entrenamiento ≤ 2026-02-22; n_train=2693, n_test=976; parámetros de la red=919.

| Modelo | Accuracy | F1 macro | Brier | Log-loss |
|---|---|---|---|---|
| Mayoritaria (línea base 1) | 0.3391 | 0.1688 | 0.6673 | 1.0996 |
| Persistencia Riesgo_t (línea base 2) | 0.7777 | 0.7716 | 0.393 | 0.748 |
| Regresión logística (referencia sklearn) | 0.8002 | 0.7935 | 0.3163 | 0.5425 |
| Red bayesiana propia (VE) | 0.748 | 0.7453 | 0.3693 | 0.6498 |