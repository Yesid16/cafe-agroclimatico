"""Organiza evidencia existente y crea documentos editables, sin entrenar ni consultar APIs.

Ejecutar con el Python del runtime de documentos (python-docx).
La exportación PDF y revisión visual se realizan por separado.
"""
from pathlib import Path
from shutil import copy2
import json
import re

from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Docs_Entregables'
TEAM = 'Jhon Jairo Pulgarin, Yesid Hurtado y Frank López'
META = 'SI3003 · EAFIT · Grupo Jueves · Proyecto 3.5'


def new_doc(title, intro):
    doc = Document()
    for border in list(doc.styles.element.iter(qn('w:pBdr'))):
        border.getparent().remove(border)
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Inches(8.5), Inches(11)
    sec.top_margin = sec.bottom_margin = Inches(1)
    sec.left_margin = sec.right_margin = Inches(1)
    sec.header_distance = Inches(.5)
    for name in ('Normal', 'Title', 'Heading 1', 'Heading 2', 'Heading 3'):
        style = doc.styles[name]
        style.font.name = 'Times New Roman'
        style.font.size = Pt(12)
        style.font.color.rgb = RGBColor(0, 0, 0)
        style.paragraph_format.space_before = Pt(0)
        style.paragraph_format.space_after = Pt(0)
        style.paragraph_format.line_spacing = 2
        style.paragraph_format.first_line_indent = Inches(.5) if name == 'Normal' else Inches(0)
        style.font.bold = name != 'Normal'
    # Word puede dar prioridad a las fuentes del tema sobre las explícitas.
    for fonts in doc.styles.element.iter(qn('w:rFonts')):
        for key in list(fonts.attrib):
            if 'theme' in key.lower():
                del fonts.attrib[key]
        for key in ('ascii', 'hAnsi', 'cs', 'eastAsia'):
            fonts.set(qn('w:' + key), 'Times New Roman')
    for name in ('Title', 'Heading 1', 'Heading 2', 'Heading 3'):
        rpr = doc.styles[name].element.get_or_add_rPr()
        for tag in ('spacing', 'kern'):
            for item in list(rpr.findall(qn('w:' + tag))):
                rpr.remove(item)
    doc.styles['Title'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.styles['Heading 1'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.styles['Heading 2'].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT
    doc.add_paragraph(title, 'Title')
    for text in (TEAM, 'Universidad EAFIT', 'SI3003 Inteligencia Artificial | Grupo Jueves', '13 de noviembre de 2026'):
        p = doc.add_paragraph(text)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Inches(0)
    if intro:
        doc.add_paragraph(intro)
    header = sec.header.paragraphs[0]
    header.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    header.paragraph_format.first_line_indent = Inches(0)
    f = OxmlElement('w:fldSimple')
    f.set(qn('w:instr'), 'PAGE')
    header._p.append(f)
    doc.core_properties.author = TEAM
    doc.core_properties.title = title
    return doc


def inline(paragraph, text):
    for i, part in enumerate(re.split(r'\*\*(.*?)\*\*', text)):
        run = paragraph.add_run(part.replace('`', ''))
        run.bold = bool(i % 2)


def table(doc, rows, widths, caption='Resultados de la evaluación'):
    number = len(doc.tables) + 1
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Inches(0)
    p.add_run(f'Tabla {number}').bold = True
    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Inches(0)
    p.add_run(caption).italic = True
    tab = doc.add_table(rows=0, cols=len(widths))
    tab.alignment = WD_TABLE_ALIGNMENT.CENTER
    tab.autofit = False
    widths = [w * 6.5 / sum(widths) for w in widths]
    for col, width in zip(tab.columns, widths):
        col.width = Inches(width)
    borders = OxmlElement('w:tblBorders')
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        item = OxmlElement('w:' + edge)
        item.set(qn('w:val'), 'single' if edge in ('top', 'bottom') else 'nil')
        item.set(qn('w:sz'), '6')
        item.set(qn('w:color'), '000000')
        borders.append(item)
    tab._tbl.tblPr.append(borders)
    margins = OxmlElement('w:tblCellMar')
    for edge in ('top', 'left', 'bottom', 'right'):
        item = OxmlElement('w:' + edge)
        item.set(qn('w:w'), '70')
        item.set(qn('w:type'), 'dxa')
        margins.append(item)
    tab._tbl.tblPr.append(margins)
    for i, values in enumerate(rows):
        row = tab.add_row()
        row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
        if i == 0:
            row._tr.get_or_add_trPr().append(OxmlElement('w:tblHeader'))
        for j, (cell, value) in enumerate(zip(row.cells, values)):
            cell.width = Inches(widths[j])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            p = cell.paragraphs[0]
            p.paragraph_format.first_line_indent = Inches(0)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.line_spacing = 1
            inline(p, str(value))
            for r in p.runs:
                r.font.size = Pt(11)
                r.bold = i == 0
            if i == 0:
                b = OxmlElement('w:tcBorders')
                rule = OxmlElement('w:bottom')
                rule.set(qn('w:val'), 'single')
                rule.set(qn('w:sz'), '6')
                rule.set(qn('w:color'), '000000')
                b.append(rule)
                cell._tc.get_or_add_tcPr().append(b)
    doc.add_paragraph().paragraph_format.line_spacing = 1
    return tab


def markdown_doc(doc, text):
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                values = [v.strip() for v in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch('[-:]+', v) for v in values):
                    rows.append(values)
                i += 1
            widths = [1.45, 2.35, 3.2] if len(rows[0]) == 3 else [7 / len(rows[0])] * len(rows[0])
            table(doc, rows, widths)
            continue
        if line.startswith('# '):
            i += 1
            continue
        if line.startswith('## '):
            doc.add_heading(line[3:], level=1)
        else:
            inline(doc.add_paragraph(), line)
        i += 1


def write_eval():
    revised = json.loads((ROOT / 'results/eval_agente_llm_revisado.json').read_text(encoding='utf-8'))
    original = json.loads((ROOT / 'results/eval_agente_llm.json').read_text(encoding='utf-8'))
    r, o = revised['resumen'], original['resumen']
    intro = ('Evaluación de doce preguntas fijas. Se comparan las ejecuciones original y revisada '
             'mediante las herramientas utilizadas y las fuentes citadas.')
    doc = new_doc('Evaluación del agente agroclimático', intro)
    md = ['# Evaluación del agente agroclimático', META, TEAM, '', intro, '', '## Protocolo y criterios']
    protocol = ('Modelo remoto: ' + r['modelo'] + '. Se exige la herramienta prevista y la resolución del caso. '
                'Diez preguntas requieren cita. La comprobación valida etiquetas de fuentes, no el soporte de cada afirmación.')
    doc.add_heading('Protocolo y criterios', 1)
    doc.add_paragraph(protocol)
    md += [protocol, '', '## Resultados comparados']
    doc.add_heading('Resultados comparados', 1)
    rows = [['Indicador', 'Original', 'Revisada'],
            ['Herramientas correctas', f"{o['herramienta_ok']}/12", f"{r['herramienta_ok']}/12"],
            ['Citas del texto original del LLM', f"{o['citas_requeridas_ok']}/10", f"{r['citas_originales_requeridas_ok']}/10"],
            ['Citas en la respuesta entregada', f"{o['citas_requeridas_ok']}/10", f"{r['citas_requeridas_ok']}/10"],
            ['Consultas con LLM real', f"{o['n_llm_real']}/12", f"{r['n_llm_real']}/12"],
            ['Respuestas con resumen de herramientas', str(o.get('n_resumen_herramientas', 0)), str(r['n_resumen_herramientas'])]]
    table(doc, rows, [3.8, 1.6, 1.6], 'Comparación entre las evaluaciones original y revisada')
    md += ['| Indicador | Original | Revisada |', '|---|---|---|'] + ['| ' + ' | '.join(x) + ' |' for x in rows[1:]]
    finding = ('La revisión acertó las herramientas en 10/12 consultas. Entregó citas válidas en 10/10 casos, '
               'frente a 5/10 en el texto original del LLM. Seis respuestas se sustituyeron por resúmenes de herramientas; '
               'este resultado no acredita acierto autónomo total.')
    doc.add_paragraph(finding)
    md += ['', finding, '', '## Resultados por pregunta']
    md += ['| Nº | Pregunta | Esperadas | Invocadas | Herramienta correcta | Cita entregada |', '|---|---|---|---|---|---|']
    for start in (0, 6):
        doc.add_page_break()
        doc.add_heading(f'Resultados de las preguntas {start + 1} a {start + 6}', 1)
        cases = [['Nº', 'Pregunta y herramienta esperada', 'Invocadas', 'Correcta', 'Cita']]
        for q in revised['preguntas'][start:start+6]:
            expected = ', '.join(q['esperadas']) or 'Ninguna'
            called = ', '.join(q['llamadas']) or 'Ninguna'
            cite = ('Sí' if q['cita_ok'] else 'No') if q['id'] <= 10 else 'No aplica'
            ok = 'Sí' if q['herramienta_ok'] else 'No'
            cases.append([str(q['id']), q['pregunta'] + '\nEsperada: ' + expected, called, ok, cite])
            md.append('| ' + ' | '.join([str(q['id']), q['pregunta'], expected, called, ok, cite]) + ' |')
        table(doc, cases, [.35, 3.25, 1.65, .8, .95], f'Evaluación de las preguntas {start + 1} a {start + 6}')
        if start == 6:
            doc.add_heading('Fallos y límites de la evaluación', 2)
            limitations = ('Pregunta 6: llamó search_docs y weather_summary sin invocar schedule para programar labores. '
                'Pregunta 12: sustituyó Atlantis por el municipio del contexto y no reconoció el error esperado. '
                'Las preguntas se conocían durante el desarrollo; falta un conjunto independiente. '
                'La evaluación automática no certifica calidad agronómica, fidelidad completa de las respuestas ni disponibilidad continua del servicio.')
            doc.add_paragraph(limitations)
            doc.add_paragraph("Las respuestas completas y las trazas se conservan en Anexos/eval_agente_llm.json y Anexos/eval_agente_llm_revisado.json.")
            md += ['', '## Fallos y límites de la evaluación', limitations]
    doc.save(OUT / 'evaluacion_agente.docx')
    (OUT / 'evaluacion_agente.md').write_text('\n'.join(md), encoding='utf-8')


def placeholder(doc, label, height=3.3):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Inches(height / 2)
    p.paragraph_format.space_after = Inches(height / 2)
    r = p.add_run(label)
    r.italic = True
    r.font.color.rgb = RGBColor.from_string('000000')


def main():
    OUT.mkdir(exist_ok=True)
    annex = OUT / 'Anexos'
    annex.mkdir(exist_ok=True)
    import sys
    import formalize_deliverables as formal
    formal.write_report(sys.modules[__name__])
    for name in ('eval_agente_llm.json', 'eval_agente_llm_revisado.json', 'eval_agente_mock.json',
                 'metricas_modelo.json', 'metricas_modelo.md', 'eval_csp.json', 'eval_csp.md'):
        copy2(ROOT / 'results' / name, annex / name)
    copy2(ROOT / 'corpus/FUENTES.md', annex / 'FUENTES.md')
    copy2(ROOT / 'data/raw/manifest.json', annex / 'manifiesto_datos.json')
    write_eval()
    formal.write_declaration(sys.modules[__name__])
    formal.write_demo(sys.modules[__name__])
    (OUT / 'README.md').write_text('''# Documentos de entrega

**Aplicación web:** [ENLACE DE LA APP DESPLEGADA]

**Universidad EAFIT · SI3003 Inteligencia Artificial · Proyecto 3.5 · Grupo Jueves**

**Integrantes:** Jhon Jairo Pulgarin, Yesid Hurtado y Frank López.

Esta carpeta reúne la documentación del Asistente agroclimático para café, de acuerdo con los entregables de la guía del proyecto final.

## Documentos principales

| Entregable | Documento | Versión editable |
|---|---|---|
| Informe breve de cuatro páginas | [Informe del proyecto](INFORME.pdf) | [Word](INFORME.docx) y [Markdown](INFORME.md) |
| Demostración funcional | [Demostración del dashboard](demostración_funcional.docx) | [Markdown](demostración_funcional.md) |
| Evaluación del agente con 12 preguntas | [Evaluación del agente](evaluacion_agente.pdf) | [Word](evaluacion_agente.docx) y [Markdown](evaluacion_agente.md) |
| Declaración de uso de IA generativa | [Declaración de uso de IA](declaracion_uso_IA.pdf) | [Word](declaracion_uso_IA.docx) y [Markdown](declaracion_uso_IA.md) |
| Repositorio e instrucciones de ejecución | [Repositorio GitHub](https://github.com/Yesid16/cafe-agroclimatico) | [README del proyecto](../README.md) |

El documento de demostración contiene los espacios para el enlace público y las capturas de las seis vistas del dashboard. La declaración incluye un apartado de aportes individuales para el registro de cada integrante.

## Anexos de evidencia

La carpeta [Anexos](Anexos) contiene las evaluaciones original y revisada del agente, las respuestas y llamadas a herramientas, la evaluación del modo demostración, las métricas del modelo y del planificador, las fuentes documentales y el manifiesto de datos.

Los anexos complementan el informe principal y conservan los resultados y las limitaciones de las ejecuciones registradas.

## Reproducibilidad

El código, los datos procesados y el modelo entrenado están incluidos en el repositorio. La ejecución del dashboard se describe en el [README principal](../README.md). La reproducción de los experimentos en Colab está documentada en la [guía de ejecución en nube](../docs/EJECUCION_NUBE.md).
''', encoding='utf-8')
    print('Documentos organizados en', OUT)


if __name__ == '__main__':
    main()
