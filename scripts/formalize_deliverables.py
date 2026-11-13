"""Contenido académico del informe y documentos complementarios."""
from pathlib import Path
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH


def write_report(builder):
    b = builder
    doc = b.new_doc('Asistente agroclimático para café', '')
    blocks = [
        [('Problema y datos',
          'El proyecto integra información climática, estimación del riesgo de roya y planificación de labores en una aplicación web. Su alcance es municipal: las estaciones meteorológicas representan el entorno de los cultivos, sin sustituir mediciones de cada finca. La aplicación reúne un modelo predictivo propio, un planificador y un asistente con consulta documental.'),
         ('', 'Se utilizaron datos del Instituto de Hidrología, Meteorología y Estudios Ambientales (IDEAM, s. f.) sobre precipitación, temperatura y humedad. El periodo solicitado fue del 1 de enero de 2022 al 31 de octubre de 2026. La tabla del modelo contiene 4.372 observaciones semanales de 47 municipios de Antioquia, Caldas, Risaralda y Quindío.'),
         ('', 'La preparación agrega las mediciones por estación, día, municipio y semana. Se exigen al menos cinco días válidos de lluvia y cuatro de temperatura y humedad. La lluvia de semanas con cinco o seis días se extrapola a siete. La humedad tiene una cobertura del 95,52 %. Los registros faltantes se conservan como ausencia de información.')],
        [('Método y resultados del modelo',
          'Se implementó una red bayesiana con inferencia por eliminación de variables. Predice la favorabilidad climática de la semana siguiente mediante lluvia reciente, temperatura, humedad y estacionalidad. La variable objetivo es un indicador construido con lluvia y temperatura; no corresponde a incidencia observada de roya.'),
         ('', 'La evaluación temporal separó 2.693 ejemplos de entrenamiento y 976 de prueba, con corte el 22 de febrero de 2026. Los parámetros y umbrales se calcularon con el entrenamiento. La tabla 1 presenta la comparación con las líneas base.'),
         ('TABLE_MODEL', ''),
         ('', 'La red supera la referencia mayoritaria, pero su F1 macro es inferior a persistencia y regresión logística. La variante conservadora de calidad obtuvo F1 de 0,7407; no mejoró el resultado original. Ambos experimentos se ejecutaron en Colab.'),
         ('Planificación de labores', 'Se implementó un problema de satisfacción de restricciones para asignar semanas a las labores según clima, precedencias y mano de obra. El calendario utiliza climatología histórica y supuestos de duración; no representa un pronóstico meteorológico.')],
        [('Agente y recuperación documental',
          'El agente utiliza un modelo remoto de NVIDIA y cuatro herramientas: consulta del riesgo, planificación, resumen climático y búsqueda documental. El ciclo de interacción tiene un máximo de seis iteraciones. Las respuestas se apoyan en fragmentos recuperados y conservan las fuentes consultadas.'),
         ('', 'El corpus incluye publicaciones de Cenicafé sobre severidad de roya y fertilización (López-Vásquez et al., 2018; Sadeghian, 2010; Salazar-Gutiérrez & Sadeghian, 2022). La recuperación emplea similitud textual y fragmentos con referencia a su página. Las notas del equipo se diferencian de las publicaciones originales.'),
         ('Evaluación del agente', 'Se evaluaron doce preguntas fijas. La tabla 2 distingue la selección de herramientas de la calidad de las citas. Seis respuestas de la revisión fueron reemplazadas por resúmenes de herramientas debido al control de citas o de integridad de la respuesta.'),
         ('TABLE_AGENT', ''),
         ('', 'La revisión falló al omitir la herramienta de planificación en una consulta y al sustituir un municipio inexistente por el del contexto. Las preguntas se conocían durante el desarrollo; falta una evaluación independiente.')],
        [('Limitaciones y reproducción',
          'Los datos presentan discontinuidades, especialmente en 2024, y 54 observaciones semanales requieren revisión. Los controles aplicados no certifican la calidad de los sensores. El promedio municipal y la extrapolación de días pueden introducir sesgos. El indicador no diagnostica enfermedad ni justifica tratamientos agronómicos.'),
         ('', 'El repositorio incluye los datos procesados, el modelo entrenado y las instrucciones de ejecución. El dashboard presenta mapa, series, probabilidades, calendario y chat. La descarga, el entrenamiento y las evaluaciones se reproducen en Colab. El informe de evaluación y las trazas completas se incluyen como documentos complementarios.'),
         ('Referencias', '')],
    ]
    md = ['# Asistente agroclimático para café', b.TEAM, 'Universidad EAFIT',
          'SI3003 Inteligencia Artificial | Grupo Jueves', '13 de noviembre de 2026', '']
    references = [
        ('Instituto de Hidrología, Meteorología y Estudios Ambientales. (s. f.). ',
         'Precipitación, temperatura ambiente y humedad relativa del aire',
         ' [Conjuntos de datos s54a-sgyg, sbwg-7ju4 y uext-mhny]. Datos Abiertos Colombia. https://www.datos.gov.co/'),
        ('López-Vásquez, J. M., Marín-Ramírez, G., Gaitán, A., & Ángel, C. A. (2018). ',
         'Diagrama de Área Estándar para la estimación visual de severidad de roya del cafeto',
         '. Avances Técnicos Cenicafé, 498, 1-8. https://doi.org/10.38141/10779/0498'),
        ('Sadeghian, S. (2010). ', 'Fertilización: Una práctica que determina la producción de los cafetales',
         '. Avances Técnicos Cenicafé, 391, 1-8. https://doi.org/10.38141/10779/0391'),
        ('Salazar-Gutiérrez, L. F., & Sadeghian, S. (2022). ',
         'Épocas recomendables para la fertilización del café antes y después de la zoca',
         '. Avances Técnicos Cenicafé, 545, 1-8. https://doi.org/10.38141/10779/0545'),
    ]
    for i, page in enumerate(blocks):
        if i:
            doc.add_page_break()
            md += ['<!-- PAGEBREAK -->', '']
        for heading, text in page:
            if heading == 'TABLE_MODEL':
                rows = [['Modelo', 'Exactitud', 'F1 macro'], ['Clase mayoritaria', '0,3391', '0,1688'],
                        ['Persistencia', '0,7777', '0,7716'], ['Regresión logística', '0,8002', '0,7935'],
                        ['Red bayesiana propia', '0,7480', '0,7453']]
                b.table(doc, rows, [3.6, 1.45, 1.45], 'Resultados de la evaluación temporal del modelo')
                md += ['| Modelo | Exactitud | F1 macro |', '|---|---|---|'] + ['| ' + ' | '.join(r) + ' |' for r in rows[1:]] + ['']
            elif heading == 'TABLE_AGENT':
                rows = [['Indicador', 'Original', 'Revisada'], ['Herramientas correctas', '12/12', '10/12'],
                        ['Citas originales del LLM', '5/10', '5/10'], ['Citas entregadas', '5/10', '10/10']]
                b.table(doc, rows, [3.6, 1.45, 1.45], 'Resultados de las dos evaluaciones del agente')
                md += ['| Indicador | Original | Revisada |', '|---|---|---|'] + ['| ' + ' | '.join(r) + ' |' for r in rows[1:]] + ['']
            else:
                if heading:
                    doc.add_heading(heading, 1 if i != 1 or heading != 'Planificación de labores' else 2)
                    md += ['## ' + heading, '']
                if text:
                    doc.add_paragraph(text)
                    md += [text, '']
        if i == 3:
            for author, title, rest in references:
                p = doc.add_paragraph()
                p.paragraph_format.left_indent = Inches(.5)
                p.paragraph_format.first_line_indent = Inches(-.5)
                p.add_run(author)
                p.add_run(title).italic = True
                p.add_run(rest)
                md += [author + '*' + title + '*' + rest, '']
    doc.save(b.OUT / 'INFORME.docx')
    text = '\n'.join(md)
    (b.OUT / 'INFORME.md').write_text(text, encoding='utf-8')
    (b.ROOT / 'docs/INFORME.md').write_text(text, encoding='utf-8')


def write_declaration(b):
    doc = b.new_doc('Declaración de uso de inteligencia artificial generativa',
        'En el desarrollo del proyecto se utilizaron herramientas de inteligencia artificial para apoyar la programación, '
        'la revisión y la elaboración de documentos. Esta declaración describe su propósito y distingue ese apoyo del '
        'funcionamiento del asistente incorporado en la aplicación.')
    sections = [
        ('Herramientas utilizadas',
         'La documentación previa del repositorio atribuye a Claude, de Anthropic, el apoyo al andamiaje inicial, '
         'los borradores de módulos, las pruebas y la documentación. El alcance de ese uso histórico está sujeto a confirmación por los integrantes.'),
        ('', 'Codex, de OpenAI, se utilizó para revisar las instrucciones y el código; ajustar controles de datos, '
         'temporalidad y evaluación; preparar la ejecución en Colab; mejorar la interfaz; revisar la conexión con NVIDIA '
         'y organizar los documentos de entrega.'),
        ('', 'NVIDIA NIM sirve el modelo nvidia/nemotron-3.5-lightning-30b-a3b del agente. Su función es interpretar '
         'consultas, solicitar herramientas y redactar respuestas apoyadas en los datos y documentos recuperados. '
         'Las evaluaciones conservan las respuestas originales y las entregadas después del control de citas.'),
        ('Verificación y responsabilidad',
         'El equipo ejecutó el procesamiento, entrenamiento y evaluación originales en Colab y recuperó los resultados. '
         'La revisión posterior incluyó pruebas de implementación, auditoría de datos y una reevaluación remota autorizada. '
         'Los experimentos de entrenamiento no se realizaron en el equipo local.'),
        ('', 'El uso de estas herramientas no sustituye la revisión del trabajo ni la comprensión de sus métodos. '
         'Los resultados y las limitaciones se conservan en los documentos de entrega. La confirmación de los aportes '
         'individuales y del uso histórico de IA corresponde a cada integrante.'),
    ]
    md = ['# Declaración de uso de inteligencia artificial generativa', b.META, b.TEAM, '']
    for heading, text in sections:
        if heading:
            doc.add_heading(heading, 1)
            md += ['## ' + heading, '']
        doc.add_paragraph(text)
        md += [text, '']
    doc.add_heading('Aportes individuales', 1)
    rows = [['Integrante', 'Aportes realizados', 'Confirmación de revisión'],
            ['Jhon Jairo Pulgarin', '[Por registrar]', '[Por confirmar]'],
            ['Yesid Hurtado', '[Por registrar]', '[Por confirmar]'],
            ['Frank López', '[Por registrar]', '[Por confirmar]']]
    b.table(doc, rows, [2.2, 2.15, 2.15], 'Registro de aportes y revisión individual')
    md += ['## Aportes individuales', '', '| Integrante | Aportes realizados | Confirmación de revisión |', '|---|---|---|']
    md += ['| ' + ' | '.join(row) + ' |' for row in rows[1:]]
    doc.save(b.OUT / 'declaracion_uso_IA.docx')
    text = '\n'.join(md)
    (b.OUT / 'declaracion_uso_IA.md').write_text(text, encoding='utf-8')
    (b.ROOT / 'docs/DECLARACION_IA.md').write_text(text, encoding='utf-8')


def write_demo(b):
    doc = b.new_doc('Demostración funcional del asistente agroclimático', '')
    md = ['# Demostración funcional del asistente agroclimático', b.META, b.TEAM, '']
    for field in ['Aplicación web: [Enlace de la aplicación desplegada]',
                  'Fecha de la demostración: [Fecha]',
                  'Municipio y fecha de referencia: [Municipio y fecha]',
                  'Video de respaldo, opcional: [Enlace]']:
        p = doc.add_paragraph(field)
        p.paragraph_format.first_line_indent = Inches(0)
        md += [field, '']
    pages = [
        ('Vista general del dashboard',
         'Presentación de la página inicial, las tarjetas de resumen y los controles de selección de municipio y fecha.',
         'Descripción de la vista general: [Texto]'),
        ('Mapa de favorabilidad climática',
         'Distribución municipal de la favorabilidad de roya. La evidencia incluye la leyenda, el detalle de un municipio y la fecha del dato utilizado.',
         'Municipio y lectura del mapa: [Texto]'),
        ('Series históricas del clima',
         'Visualización de precipitación, temperatura y humedad en el periodo seleccionado. Los espacios sin registros se distinguen de las semanas con lluvia observada igual a cero.',
         'Periodo y comportamiento observado: [Texto]'),
        ('Estimación del riesgo climático',
         'Distribución de probabilidades y condiciones utilizadas por el modelo. Se identifican la semana de la última observación y la semana estimada.',
         'Resultado e interpretación del indicador: [Texto]'),
        ('Planificación de labores',
         'Calendario de actividades según área, horizonte de planificación y mano de obra. La evidencia muestra el resultado de una modificación de estos parámetros.',
         'Parámetro modificado y efecto en el calendario: [Texto]'),
        ('Conversación con el agente',
         'Consulta y respuesta del asistente, con las fuentes y herramientas utilizadas. La captura identifica el modo de ejecución y mantiene oculta la clave de acceso a NVIDIA.',
         'Pregunta, herramientas y fuentes consultadas: [Texto]'),
        ('Resultados de la evaluación',
         'Métricas del modelo y comparación con las líneas base. La evidencia distingue las citas del texto original del LLM de las citas de la respuesta entregada.',
         'Resultado destacado y limitaciones: [Texto]'),
    ]
    for i, (title, text, field) in enumerate(pages):
        if i:
            doc.add_page_break()
        doc.add_heading(title, 1)
        doc.add_paragraph(text)
        b.placeholder(doc, '[Espacio para la captura correspondiente]', 1.1 if i == 0 else 3.2)
        doc.add_paragraph(field)
        if i:
            doc.add_paragraph('Resultado de la comprobación: [Descripción]')
        md += ['## ' + title, '', text, '', '[Espacio para la captura correspondiente]', '', field, '']
    doc.save(b.OUT / 'demostración_funcional.docx')
    (b.OUT / 'demostración_funcional.md').write_text('\n'.join(md), encoding='utf-8')
