# Auditoría de los CSV diarios

## Dictamen

Los tres CSV coinciden byte a byte con los SHA-256 del manifiesto de Colab. No contienen estación-día duplicada. La agregación del código reproduce las 4.372 filas semanales y sus valores de lluvia, temperatura y humedad, dentro de tolerancia numérica de 1e-8. La transferencia y la agregación quedan comprobadas; esto no valida los sensores originales.

Los problemas no se limitan a las 54 semanas visibles: una media municipal puede ocultar estaciones sospechosas al promediarlas con estaciones de valores altos. Se revisaron primero los datos diarios con cobertura suficiente, antes de mezclar estaciones.

## Hallazgos

| Variable | Filas recibidas | Días con cobertura y sin registros simultáneos | Días señalados en la variante |
|---|---|---|---|
| Precipitación | 78.264 | 64.988 | 30 |
| Temperatura | 55.224 | 44.744 | 0 |
| Humedad | 55.516 | 43.233 | 1.620 |

Los días señalados no son errores certificados por IDEAM: se usan para una sensibilidad conservadora y se conservan en la evidencia.

- **Pereira, estación 0026125710:** durante varias secuencias de febrero-marzo de 2022, el total diario es exactamente dos veces el número de lecturas: 288 mm/144, 240 mm/120, etc. La igualdad de medias por lectura es compatible con una señal fija o codificación anómala, pero no demuestra que cada lectura instantánea sea constante. Veinte días cumplen la regla de secuencia conservadora; no se supone automáticamente un error de unidades.
- **Salamina, estación 0026180250:** mediana de humedad diaria 84,6875% en 2025 frente a 8,125% en los 79 días válidos disponibles de 2026. No hay evidencia suficiente para multiplicar por diez; se marca el tramo.
- **Yolombó, estación 0023105070:** 115 días con humedad <20% en 2022, incluyendo medias próximas a cero; en periodos posteriores hay valores de otro orden de magnitud.
- **Otras estaciones:** la tabla estaciones_para_revision.csv identifica todos los códigos, municipios, rangos y número de días, incluidos valores bajos que el promedio municipal ocultó.
- **Lluvia:** diez días con más de 300 mm, además de las veinte observaciones de secuencias repetidas. Un extremo aislado puede ser real; omitirlo se presenta como sensibilidad, no validación meteorológica.

## Por qué casi desaparece 2024

| Variable | Días agregados en 2024 | n_total distinto de n | Días que pasan cobertura |
|---|---|---|---|
| Precipitación | 6.326 | 4.850 | 1.379 |
| Temperatura | 3.756 | 3.489 | 212 |
| Humedad | 3.761 | 3.495 | 209 |

n cuenta timestamps distintos; n_total cuenta registros. Una diferencia indica varios registros por timestamp. Sin las observaciones instantáneas no se sabe si son duplicados idénticos, varios sensores o valores contradictorios. No se corrige la suma dividiendo por n_total/n: eso podría alterar lluvia de forma injustificada. Se mantiene el rechazo original y se explica la pérdida de cobertura.

## Variante conservadora, separada del experimento original

Política fija, sin consultar métricas de test:

1. Omitir humedad diaria <20% antes del promedio entre estaciones; no imputar ni cambiar unidades.
2. Omitir lluvia diaria >300 mm y secuencias de al menos tres días consecutivos con igual media valor/n y total diario >100 mm.
3. Mantener los filtros de cobertura y duplicados originales. No interpolar el hueco de 2024.

Estos umbrales son decisiones exploratorias conservadoras, no límites físicos oficiales. Pueden descartar extremos auténticos; se propone comparar contra el experimento original y no usar el resultado para reclamar una limpieza certificada.

La variante conserva **4.368 filas y los mismos 47 municipios**. Se pierden cuatro semanas de Pereira por cobertura de lluvia insuficiente; no se fabrican datos para rellenarlas. En las semanas comunes cambian tres valores de lluvia y 192 de humedad; temperatura no cambia. Humedad disponible: **4.121/4.368 (94,35%)**, sin medias semanales <20%. Persisten tres semanas con lluvia >500 mm (Medellín y Titiribí); se mantienen porque no cumplen las reglas diarias de la variante.

Archivos:

- results/revision_diaria/auditoria_diaria.json: políticas, verificación, cobertura y comparación.
- results/revision_diaria/trazabilidad_54_semanas.csv: estación-día detrás de las 54 semanas iniciales.
- results/revision_diaria/dias_para_revision.csv: todos los días señalados, incluidos los ocultos por promedios municipales.
- results/revision_diaria/comparacion_semanal.csv: comparación original/variante.
- data/review/processed/semanal.csv: candidata para sensibilidad; no reemplaza data/processed/semanal.csv.
- cafe/quality_review.py: reproduce la auditoría y la candidata, sin entrenar.
- cafe/review_experiment.py: entrena y evalúa la sensibilidad solo en Colab, con resultados y modelo en carpetas separadas.

## Sensibilidad ejecutada y comparada

El equipo ejecutó el experimento conservador en Colab y devolvió los artefactos. Se validaron el hash de la candidata, la correspondencia de cuantiles de cada modelo con su tabla y la normalización de las CPT. Los originales conservan los hashes de la auditoría anterior.

| Métrica de la red | Original | Conservadora |
|---|---|---|
| Accuracy | 0,7480 | 0,7428 |
| F1 macro | 0,7453 | 0,7407 |
| Brier | 0,3693 | 0,3740 |
| Log-loss | 0,6498 | 0,6577 |

Mismo corte 22/02/2026, 2.693/2.689 ejemplos de entrenamiento y 976 claves municipio/fecha de test en ambas variantes. Cambian dos etiquetas Alto a Medio en Frontino (evidencias 11 y 18 de octubre de 2026). No es una comparación sobre etiquetas fijas ni demuestra diferencias significativas.

No se adopta la política exploratoria como limpieza certificada. Se conserva el original como referencia reproducible, con sus advertencias, y se presenta la variante como sensibilidad. La pérdida de F1 no demuestra que los sensores sospechosos sean correctos; tampoco la desaparición de banderas prueba una corrección verdadera.

Resultados en results/revision_calidad/; modelo y tabla conservadores en data/review/processed/. La comparación reproducible está en cafe/compare_quality.py y no entrena. Ya no hace falta repetir descargas o entrenamiento para esta revisión.

La revisión de CSV diarios queda documentada. Confirmar fallos o cambios de escala en origen requiere registros instantáneos/metadatos de mantenimiento o datos oficiales validados de IDEAM/DHIME; los totales y medias diarios no conservan esa información.
