# Dictamen crítico del estado actual

Revisión: 13 de noviembre de 2026. Alcance: código, CSV diarios y semanales, modelos y evaluaciones recibidas de Colab, guía EAFIT y estado local del repositorio. No se entrenó ni se repitió una evaluación LLM en esta revisión.

## Veredicto

MVP académico funcional con los principales componentes y entregables del proyecto 3.5. No equivale a un sistema agronómico validado, ni permite afirmar que todos los datos y respuestas sean correctos. Las 49 pruebas anteriores verifican comportamiento del software; no certifican sensores, validez del objetivo ni fidelidad semántica del LLM.

## Qué se pudo comprobar

- Las fuentes configuradas son los tres conjuntos IDEAM de precipitación, temperatura y humedad; se descargaron y documentaron metadatos y consultas.
- Los tres CSV diarios coinciden con los SHA-256 del manifiesto de Colab. La agregación local reproduce los valores semanales originales.
- Dataset/modelo originales mantienen los hashes de su auditoría; los dos modelos corresponden a sus tablas y sus CPT están normalizadas.
- Hay implementación propia de CPT/inferencia y CSP, RAG con publicaciones técnicas, cuatro herramientas, parámetros, chat, visualizaciones y evaluaciones reales.
- Informe PDF de cuatro páginas, declaración de IA, doce preguntas y artefactos presentes localmente.
- Datos completos de cada variable se visualizan de forma independiente; los huecos no se rellenan con cero.

## Lo que no está demostrado

### Extracción y calidad

Coincidencia de hashes acredita que el archivo no cambió desde su descarga; reproducir la agregación acredita el cálculo desde ese archivo. Ninguna de las dos pruebas demuestra que un sensor mida bien ni que cada lectura instantánea se haya interpretado correctamente.

Hay numerosos registros simultáneos descartados, huecos importantes en 2024 y patrones sospechosos (humedad muy baja, cambios de escala, totales de lluvia proporcionales al número de lecturas). La cobertura diaria mínima admite días parciales; la lluvia de semanas con cinco/seis días se extrapola a siete. Es una aproximación explícita, con incertidumbre.

Se intentó un contraste directo adicional de tres estación-día contra la API oficial (precipitación de Pereira, humedad de Salamina y temperatura de Medellín). Los tres intentos agotaron el tiempo. Por tanto, esta revisión no confirma sumas, promedios ni unidades contra esas lecturas instantáneas. Registro: results/contraste_muestras_fuente.json. No se presentan esos intentos como verificaciones exitosas.

La variante conservadora es una sensibilidad con umbrales exploratorios, no una limpieza certificada. Conservar el original como referencia no declara sus valores sospechosos correctos.

### Modelo

El objetivo es un indicador definido por reglas de lluvia y temperatura. No se ha incorporado incidencia de roya observada para validar predicción de enfermedad. No se concluye que esas etiquetas no existan en alguna fuente pública; solamente no están en este proyecto.

F1 macro: red 0,7453, persistencia 0,7716 y logística 0,7935. La red pierde frente a ambas referencias en F1. La sensibilidad obtiene 0,7407. Esto no incumple por sí solo exigir comparación con una línea base, pero impide afirmar superioridad predictiva o validación epidemiológica.

Solo hay un corte temporal, no evaluación espacial ni un conjunto externo independiente; los terciles globales, la mezcla de estaciones y la representatividad de una finca son limitaciones.

### Vigencia temporal: limitación concreta

La semana más reciente del dataset termina el 01/11/2026. El horizonte de una semana termina como máximo el 08/11/2026; a fecha de esta revisión, los horizontes de los 47 municipios ya son pasados. Siete municipios terminan en 2023 y uno en 2025.

La fecha de referencia y el aviso retrospectivo ayudan, pero términos como “pronóstico” o “próxima semana” pueden confundirse con actualidad. Para uso público deben mostrarse explícitamente el último dato y las fechas del periodo estimado. El calendario se ancla también en datos/fecha de referencia y usa climatología, no un pronóstico meteorológico actualizado.

### Agente y RAG

Evaluación revisada: herramientas esperadas 10/12. Citas originales del LLM 5/10; la aplicación entrega 10/10 después de sustituir seis respuestas por resúmenes de herramientas. Es una protección útil, no un 100% de acierto autónomo.

El comprobador valida etiquetas, no si cada afirmación está soportada por el fragmento, si la pregunta se respondió completamente o si la herramienta omitida era necesaria. Las doce preguntas se conocían al desarrollar el sistema. Faltan preguntas independientes y revisión humana de exactitud y fidelidad.

Persisten fallos registrados al programar cosecha/fertilización y al tratar un municipio desconocido. Las notas del equipo y la extracción de texto de PDF también pueden introducir ruido.

### CSP y alcance

El solver respeta las restricciones programadas y contempla infactibilidad. Los jornales, duraciones y categorías aceptadas son supuestos del equipo, no parámetros validados con una finca. La eficiencia de heurísticas no quedó demostrada en los pequeños ejemplos usados.

El alcance es favorabilidad de roya y labores a nivel municipal como proxy; no incluye todas las plagas ni mediciones de finca. Es un recorte de MVP que debe explicarse en la entrega.

### Entrega y despliegue

Los componentes y documentos principales están presentes, pero la versión local contiene cambios y archivos aún no comprometidos. Esta revisión no confirma que la versión pública de GitHub o un despliegue web contengan el estado actual. La revisión interactiva final, publicación/envío y confirmación de aportes/comprensión del equipo siguen siendo responsabilidades pendientes.

## Prioridades antes de presentarlo como servicio público

1. Aclarar en cada salida las fechas estimadas y restringir afirmaciones de actualidad cuando el horizonte ya pasó.
2. Corregir y reevaluar manejo de municipios explícitos desconocidos e intención de programación; evaluar con preguntas nuevas.
3. Revisar fidelidad semántica del LLM, no solo etiquetas de cita; conservar evaluación antes/después y distinguir resúmenes deterministas.
4. Contrastar muestras de sensores/unidades con observaciones instantáneas o DHIME y justificar supuestos agronómicos con fuentes.
5. Verificar la demo desplegada, la versión publicada del repositorio, la declaración de IA y las instrucciones de ejecución.

La defensa académica debe ser: “implementamos y evaluamos un MVP exploratorio con estas limitaciones”. No: “validamos un predictor de roya confiable para fincas”.
