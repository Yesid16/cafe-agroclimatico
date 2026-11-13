# Ejecución en nube y recuperación de resultados

 El notebook notebooks/02_Colab_pipeline.ipynb automatiza el flujo mediante Colab manual, sin entrenar en el PC.

1. En PowerShell: **python scripts/package_colab.py**. Solo comprime código y documentos; excluye .env, .git, .venv, datos y modelos.
2. Abre https://colab.research.google.com/ y sube notebooks/02_Colab_pipeline.ipynb.
3. Selecciona CPU. No se requiere GPU: las CPT son conteos y la regresión logística es pequeña. El LLM se sirve desde NVIDIA, no se carga ni entrena en Colab.
4. Ejecuta la primera celda y sube artifacts/cafe_colab_source.zip. Se usa el estado actual del código aunque todavía no esté publicado en GitHub.
5. Crea el secreto NVIDIA_API_KEY y habilita acceso al notebook. No pongas la clave en una celda compartida.
6. Ejecuta verificación y descargas. Socrata puede tardar; se guardan meses completos en caché. Reejecuta la celda si falla. Reiniciar Colab borra almacenamiento temporal: conserva resultados.
7. Revisa cobertura, rango, humedad y semanas extrapoladas antes de entrenar. Si faltan datos, usa DHIME o estaciones con cobertura verificable; no reduzcas filtros arbitrariamente.
8. Ejecuta modelo, CSP y ambas evaluaciones del agente. La evaluación LLM falla explícitamente si hubo respaldo; revisa el JSON de trazas antes de reportar.
9. Ejecuta el chequeo de evidencias y revisa preguntas fallidas. La existencia de archivos no demuestra buen desempeño.
10. Descarga cafe_resultados.zip: tablas semanales, modelo, corpus, manifiestos y resultados sin clave. Incluye results/entorno.txt con versiones efectivas.

requirements-cloud.txt fija las versiones comprobadas en este equipo para Python >= 3.12. En un runtime anterior el notebook usa requirements.txt y registra las versiones resueltas. La ejecución completa de Colab fue realizada por el equipo; sus artefactos están en data/processed/ y results/. No hace falta repetirla para abrir la demo.

## Mostrar la aplicación

**PC como interfaz:** extrae el ZIP en la raíz del repositorio y ejecuta streamlit run app.py. Solo carga artefactos preparados en nube y consulta NVIDIA. Reinicia Streamlit tras cambiar artefactos porque hay cachés.

**Toda la demo en nube:** prepara código y artefactos en GitHub y despliega app.py en Streamlit Community Cloud usando las mismas dependencias del entrenamiento. La instantánea pequeña de data/processed/ ya está permitida por .gitignore; comprueba que esos dos archivos y las dependencias estén incluidos al publicar el repositorio. No publiques claves. Cada visitante ingresa su propia clave NVIDIA en la barra lateral; no se requiere una clave compartida en los secretos del hosting. El dashboard usa la clave de sesión y el endpoint NVIDIA fijo. LLM_API_KEY/.env siguen siendo útiles para los comandos de evaluación, pero no se usan como respaldo de credenciales en la web. Este despliegue no se realizó en la revisión.

## Qué devolver para cerrar la revisión

Copia results/ y data/processed/ del ZIP al proyecto. Con eso se pueden interpretar F1/Brier, matriz de confusión, casos fallidos del agente y terminar el informe. Añade una captura del dashboard o el video opcional. No hace falta compartir la API key.

## Contingencias

- Socrata 400: revisar mensaje y consulta; no se reintenta indefinidamente.
- Socrata 429/5xx: esperar y reintentar; la caché conserva meses completos.
- Cenicafé: el listado usa publicaciones.cenicafe.org, sin depender del antiguo subdominio biblioteca.
- NVIDIA 401/403: revisar clave/permisos. 404/410: revisar modelos habilitados en GET /v1/models; el catálogo puede mostrar modelos no habilitados para la cuenta.
- Datos insuficientes: conservar el reporte y solicitar exportación DHIME con frecuencia, unidades y estación identificadas. Nunca usar datos sintéticos en los resultados.

## Si Colab solo muestra CalledProcessError

Ese traceback describe el proceso que falló, no la causa. La versión actual de run transmite stdout y stderr a la celda y guarda el registro en results/logs/. En una sesión ya abierta, copia la función de scripts/colab_run.py a una celda, ejecútala y vuelve a llamar solo cafe.data_download y después cafe.data_prep. Conserva data/raw/cache/; no hace falta volver a subir el ZIP ni descargar otra vez el corpus.

Si el fallo persiste, comparte el mensaje HTTP/timeout/traceback que aparece antes del RuntimeError, o el registro results/logs/cafe_data_download.log. No es necesario compartir la clave NVIDIA.

## Timeouts de IDEAM durante un mes

Un ReadTimeout no significa que se haya perdido la caché ni que NVIDIA falle. El descargador conserva las firmas de los meses de la versión inicial. Tras dos intentos de hasta 60 segundos de lectura, un timeout o HTTP 408/500/502/503/504 divide el intervalo en dos partes disjuntas y repite el procedimiento, hasta un día. Cada partición completa se guarda de forma atómica. Los intervalos sin datos se guardan con cabecera válida. Errores de consulta/permisos no se ocultan dividiendo fechas.

El parche artifacts/cafe_descarga_fix.zip contiene solo cafe/data_download.py y puede extraerse en el proyecto existente en Colab sin borrar data/raw/cache/. Después se repite el comando con todo el rango original; no se deben concatenar manualmente meses o acortar fechas para saltar el fallo.

Si incluso una consulta de un día falla, se informa la fecha y se detiene sin omitir datos. Hay que reintentar cuando IDEAM se recupere o usar los CSV oficiales del plan B. No se garantiza disponibilidad del servicio. El aviso de bottleneck instalado en Colab es independiente del timeout; se puede actualizar opcionalmente con python -m pip install --upgrade "bottleneck>=1.5.0".

## Exportar CSV diarios para investigar las anomalías

El ZIP de resultados inicial no contiene los CSV diarios. Para revisar sensores y unidades de las 54 semanas señaladas, ejecuta esta celda en la misma sesión Colab que conserva la descarga. No descarga de nuevo ni entrena:

~~~python
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from google.colab import files

root = Path("/content/cafe-agroclimatico")
output = Path("/content/cafe_datos_diarios.zip")
names = ["precip_diaria.csv", "temp_diaria.csv", "humedad_diaria.csv"]
missing = [name for name in names if not (root / "data/raw" / name).exists()]
if missing:
    raise FileNotFoundError(f"No están los CSV diarios: {missing}")
with ZipFile(output, "w", ZIP_DEFLATED) as z:
    for name in names:
        path = root / "data/raw" / name
        z.write(path, "data/raw/" + name)
files.download(str(output))
~~~

Extrae cafe_datos_diarios.zip en el proyecto. Permitirá rastrear anomalías sin alterar los originales ni volver a entrenar localmente. Si la sesión Colab se perdió, los datos diarios deben recuperarse de una copia o regenerarse en nube con la caché; los agregados semanales no permiten reconstruirlos.

## Sensibilidad de calidad: sin repetir la descarga

La auditoría diaria ya produjo una candidata separada de la demo. Para medir el efecto de la política conservadora, descarga artifacts/cafe_revision_calidad.zip del proyecto y ejecuta esta celda en el Colab que usaste. Sube ese ZIP pequeño (aproximadamente 337 KiB), no el ZIP inicial del proyecto. Solo entrena/evalúa la red y las líneas base en CPU de Colab; no vuelve a consultar IDEAM ni a evaluar el LLM.

~~~python
from google.colab import files
from pathlib import Path
from zipfile import ZipFile
from io import BytesIO
import os

work = Path("/content/cafe-agroclimatico")
if not work.is_dir():
    raise FileNotFoundError("Usa la sesión Colab del proyecto, con las dependencias ya instaladas.")
uploaded = files.upload()
with ZipFile(BytesIO(next(iter(uploaded.values())))) as z:
    for name in z.namelist():
        if not (work / name).resolve().is_relative_to(work.resolve()):
            raise ValueError("Ruta inválida en el ZIP")
    z.extractall(work)
os.chdir(work)
exec((work / "scripts/colab_run.py").read_text(encoding="utf-8"))
run("cafe.review_experiment")
files.download(str(work / "artifacts/cafe_resultados_calidad.zip"))
~~~

Extrae cafe_resultados_calidad.zip en el proyecto. Sus archivos quedan en data/review/ y results/revision_calidad/: no reemplazan la instantánea de la demo ni resultados originales. La comparación deberá considerar cambios de población y faltantes; una mejora de métricas no demostraría por sí sola que el sensor esté corregido.

La auditoría es reproducible mediante python -m cafe.quality_review sin entrenar. Si quieres repetir también la preparación en Colab, ejecuta esa auditoría antes del experimento usando los CSV diarios originales. El experimento comprueba el hash de la candidata y restaura las variables de entorno al finalizar o fallar.

## Estado actual: sensibilidad ya completada

El ZIP conservador ya se recuperó y comparó: F1 macro de la red 0,7407, frente a 0,7453 original. Se conserva como experimento separado. No hace falta repetir las celdas anteriores para abrir la demo o consultar esta comparación. Son instrucciones de reproducción.

Los resultados y modelos de ambas variantes están en el proyecto; la comparación sin entrenamiento se ejecuta con python -m cafe.compare_quality. El dashboard conserva el experimento original como referencia y muestra la sensibilidad en Métricas.
