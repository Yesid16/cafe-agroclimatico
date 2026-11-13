# Revisión posterior a la ejecución de Colab

**Estado:** se recuperaron y auditaron los artefactos reales. El informe está en Docs_Entregables/INFORME.pdf (cuatro páginas) y docs/INFORME.md. Se cargó el dashboard sin excepciones con los archivos extraídos. No se reentrenó el modelo localmente.

## Datos

- 4.372 semanas-municipio, 47 municipios de los cuatro departamentos requeridos y cero duplicados municipio-semana.
- Humedad disponible en 4.176 filas (95,52%); 196 faltantes explícitos.
- Se extrapoló lluvia en 1.160 semanas (26,53%) por cobertura de cinco/seis días.
- Solo 11 filas de 2024: discontinuidad importante. Tener fechas extremas 2022-2026 no equivale a cinco años completos.
- 54 semanas para revisión: 47 con humedad <20% y siete con precipitación >500 mm/semana. Son banderas exploratorias; no demuestran por sí solas un error. Los originales se conservan.
- La etiqueta 01/11/2026 es el cierre semanal de observaciones descargadas hasta el 31/10, no una lectura futura.

**Dictamen sobre los datos:** las fuentes y variables son pertinentes para un MVP climático, pero la calidad meteorológica no está certificada. Los CSV diarios ya se recuperaron y sus hashes coinciden con el manifiesto. Se reprodujo la agregación semanal original y se documentaron patrones sospechosos en docs/REVISION_DATOS_DIARIOS.md. La variante conservadora de sensibilidad queda en data/review/, sin entrenamiento ni sustitución del modelo original.

La auditoría reproducible está en cafe/audit_artifacts.py; resultados en auditoria_datos.json, observaciones_para_revision.csv y cobertura_temporal_auditada.csv. No se cambió semanal.csv ni el modelo.

## Modelo y CSP

Corte temporal 22/02/2026: 2.693 ejemplos de entrenamiento y 976 de prueba. Red bayesiana: accuracy 0,7480, F1 macro 0,7453, Brier 0,3693 y log-loss 0,6498. F1 de persistencia 0,7716 y logística 0,7935: la red no supera esas referencias. Sí mejora la clase mayoritaria. En Brier mejora persistencia pero pierde frente a logística.

La matriz de confusión muestra mayor dificultad para Medio (recall 67,47%). El objetivo es una regla de favorabilidad climática, no incidencia de roya en campo. El informe no presenta las métricas como validación epidemiológica.

CSP: escenario mixto factible en cuatro nodos con y sin heurísticas. Dos escenarios inviables se detectan antes de buscar. No se demuestra ahorro de MRV/forward checking en esos ejemplos; sí restricciones y detección de infactibilidad.

## Agente

La evaluación original en Colab se conserva intacta: 12/12 llamadas a las herramientas esperadas, 5/10 citas requeridas y 12/12 preguntas con LLM real. Fallos: preguntas 2, 5, 7, 9 y 10 por citas ficticias/alteradas; la 5 expandía mal CSP y la 9 añadía umbrales no respaldados.

Se corrigió el prompt y se añadió una protección que comprueba etiquetas contra cada herramienta consultada. Ante citas inválidas o respuesta truncada, entrega un resumen identificado de herramientas y guarda la salida original. Esta comprobación no certifica soporte semántico de cada frase.

Reevaluación remota explícitamente autorizada: 12 preguntas con NVIDIA, cero respaldos de red y cero límites agotados. Herramientas esperadas 10/12; citas entregadas 10/10. Las citas originales del LLM siguen en 5/10 y seis respuestas se sustituyeron por resúmenes de herramientas. No se atribuye el 10/10 al modelo de lenguaje por sí solo. Fallos de herramientas: pregunta 6 (no llamó schedule) y 12 (no obtuvo el error de municipio desconocido esperado). El prompt no elimina todas las limitaciones.

Resultados separados en eval_agente_llm_revisado.json, con raw_answer, answer_source y validación de citas. Se permiten herramientas adicionales: la métrica no es exactitud de selección exclusiva. El router determinista tiene ventaja por diseño y no acredita el requisito de LLM real.

La reevaluación se bloqueó inicialmente por revisión automática del envío de contenido; después el usuario autorizó explícitamente las preguntas, datos agregados y fragmentos públicos a NVIDIA. Se encontró además endpoint/modelo vacíos en el .env local y se completaron conservando la clave. El intento incompleto queda separado en results/diagnostico_configuracion/; no es evidencia de desempeño del LLM.


## Revisión diaria posterior

La tabla original se reproduce desde los tres CSV. Se identificaron 1.620 días de humedad baja y 30 días de lluvia señalados por la política conservadora. La variante conserva 4.368 filas/47 municipios y modifica 192 valores de humedad en semanas comunes. El experimento separado ya se ejecutó en Colab: F1 0,7407, Brier 0,3740. La comparación completa está en results/revision_calidad/comparacion_calidad.md. Las causas en el sensor y los extremos restantes no se consideran validados.

## Cierre del experimento conservador

Artefactos recibidos y coherentes: 4.368 filas, 47 municipios; entrenamiento 2.689, test 976, mismo corte temporal. Red con F1 0,7407 frente a 0,7453 original; Brier 0,3740 frente a 0,3693. Son las mismas claves de test, pero cambian dos etiquetas en Frontino: no se interpreta como comparación estricta sobre un objetivo fijo ni como evidencia de significancia.

Se conservan ambos experimentos. El original permanece como referencia de la demo con avisos de calidad; la variante es una sensibilidad cuyos umbrales no están certificados. La decisión no convierte datos sospechosos en correctos y no selecciona un supuesto modelo validado de enfermedad. El informe de cuatro páginas y el dashboard muestran los resultados y sus límites.

No se requieren más ejecuciones en Colab para la revisión. Quedan por parte del equipo la inspección interactiva final, comprensión/aportes de integrantes y publicación/envío del repositorio según la guía.

## Acceso web con clave por visitante

Se añadió un campo de contraseña y botón de olvido por sesión. El agente recibe credenciales por llamada, sin cambiar .env/configuración global; la web pasa una clave explícita y el endpoint NVIDIA. Una clave vacía no activa credenciales del servidor. CLI/evaluaciones mantienen configuración de entorno. Pruebas: 45 pasaron, incluidos concurrencia y aislamiento entre sesiones, limpieza de clave y ausencia de claves en mensajes/trazas. No se desplegó el servicio en esta modificación.

## Corrección de series de tiempo

La gráfica ya no depende exclusivamente de la tabla conjunta del modelo. Se creó clima_semanal.csv con unión externa de lluvia, temperatura y humedad y sus respectivos días válidos, sin imputar datos. La vista reindexa el calendario, distingue lluvia cero de dato ausente e interrumpe líneas en huecos. El rango de dos años cuenta semanas de calendario; hay una opción de histórico completo y detalle de semanas faltantes. No se restituyó el aviso global de calidad retirado por el usuario.

Medellín: 144 semanas válidas de lluvia, 160 de temperatura y 142 de humedad en la serie independiente; antes la gráfica solo disponía de las 143 filas conjuntas del modelo. La semana 01/06/2025 conserva 19 mm aunque falte temperatura. El dataset y el modelo originales mantienen sus hashes. No se entrenó para esta corrección.
