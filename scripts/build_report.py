"""Genera el informe académico editable y su PDF, sin entrenar modelos.

Requiere python-docx y Word en Windows o LibreOffice en Linux/macOS.
"""
from pathlib import Path
import shutil
import subprocess
import sys
from pypdf import PdfReader
import build_deliverables as builder
from formalize_deliverables import write_report


def build():
    builder.OUT.mkdir(exist_ok=True)
    write_report(builder)
    if sys.platform == "win32":
        subprocess.run(["powershell.exe", "-NoProfile", "-File",
            str(builder.ROOT / "scripts/export_delivery_documents.ps1"), "-OnlyReport"], check=True)
    else:
        soffice = shutil.which("soffice")
        if not soffice:
            raise RuntimeError("Informe DOCX creado. La exportación PDF requiere LibreOffice o Microsoft Word.")
        subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir",
            str(builder.OUT), str(builder.OUT / "INFORME.docx")], check=True)
        output = builder.ROOT / "output/pdf"
        output.mkdir(parents=True, exist_ok=True)
        shutil.copy2(builder.OUT / "INFORME.pdf", output / "INFORME.pdf")
    pages = len(PdfReader(builder.OUT / "INFORME.pdf").pages)
    if pages != 4:
        raise RuntimeError(f"Revisar extensión y formato: {pages} páginas; se requieren cuatro.")
    print("Informe académico: cuatro páginas.")


if __name__ == "__main__":
    build()
