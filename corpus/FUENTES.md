# Fuentes del corpus RAG

Los archivos `notas_*.md` de esta carpeta son **notas de síntesis redactadas por el equipo** con
conocimiento agronómico general y NO sustituyen la literatura oficial. Para cumplir con el rigor
del proyecto, **descargue y agregue a esta carpeta (PDF) publicaciones abiertas verificables**:

- Cenicafé – Avances Técnicos y Boletines (roya, manejo integrado, fertilización, cosecha): https://www.cenicafe.org
- Federación Nacional de Cafeteros – publicaciones y Manual del Cafetero Colombiano: https://federaciondecafeteros.org
- IDEAM – boletines agroclimáticos y de predicción climática (ENSO): https://www.ideam.gov.co

Escriba las URLs directas de los PDF en `corpus/urls.txt` (una por línea) y ejecute
`python -m cafe.fetch_corpus`. Luego reinicie la app: el RAG indexa automáticamente todos los PDF.
Este archivo no se indexa. Registre en el informe qué documentos usó finalmente.
