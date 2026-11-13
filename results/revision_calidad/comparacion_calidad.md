Comparación de sensibilidad (experimentos ejecutados en Colab).

Corte 2026-02-22; entrenamiento 2693 original / 2689 conservador; 976 claves de prueba comunes.
Cambian 2 etiquetas del indicador: no es una prueba sobre un objetivo totalmente fijo.

| Modelo | F1 original | F1 conservador | Delta F1 | Brier original | Brier conservador |
|---|---|---|---|---|---|
| Mayoritaria (línea base 1) | 0.1688 | 0.1681 | -0.0007 | 0.6673 | 0.6673 |
| Persistencia Riesgo_t (línea base 2) | 0.7716 | 0.7742 | +0.0026 | 0.3930 | 0.3895 |
| Regresión logística (referencia sklearn) | 0.7935 | 0.7914 | -0.0021 | 0.3163 | 0.3170 |
| Red bayesiana propia (VE) | 0.7453 | 0.7407 | -0.0046 | 0.3693 | 0.3740 |

Mantener original como referencia reproducible con advertencias; conservar sensibilidad separada. Los filtros no son validación certificada.
Mismas claves de test, pero cambian dos etiquetas y evidencias; no es comparación estricta sobre un objetivo fijo ni prueba de significancia.