"""Descarga corpus verificable, valida PDF/texto y registra SHA-256 y URL."""
import hashlib
import json
from urllib.parse import unquote, urlparse
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from pathlib import Path
from pypdf import PdfReader
from . import config as C


def main():
    urls = C.CORPUS_DIR / 'urls.txt'
    if not urls.exists():
        raise FileNotFoundError('Falta corpus/urls.txt')
    records, errors = [], []
    session = requests.Session()
    session.mount('https://', HTTPAdapter(max_retries=Retry(total=2, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])))
    for url in urls.read_text(encoding='utf-8').splitlines():
        url = url.strip()
        if not url or url.startswith('#'):
            continue
        if '|' in url:
            name, url = url.split('|', 1)
        else:
            name = unquote(urlparse(url).path.rsplit('/', 1)[-1])
        if name != Path(name).name:
            raise ValueError('Nombre de archivo inválido')
        if not name.lower().endswith('.pdf'):
            raise ValueError(f'Se requiere enlace PDF directo: {url}')
        path = C.CORPUS_DIR / name
        try:
            if not path.exists():
                r = session.get(url, timeout=(15, 90))
                r.raise_for_status()
                if not r.content.startswith(b'%PDF-'):
                    raise ValueError('La URL no devuelve un PDF')
                path.write_bytes(r.content)
            reader = PdfReader(path)
            words = sum(len((p.extract_text() or '').split()) for p in reader.pages)
            if words < 50:
                raise ValueError('PDF escaneado o sin texto: requiere OCR antes de indexar')
            records.append({'archivo': name, 'url': url, 'paginas': len(reader.pages), 'palabras': words,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            print('OK', name, words, 'palabras')
        except Exception as exc:
            errors.append({'url': url, 'error': str(exc)})
            print('ERROR', url, type(exc).__name__)
    (C.CORPUS_DIR / 'manifest.json').write_text(json.dumps({'documentos': records, 'errores': errors}, ensure_ascii=False, indent=2), encoding='utf-8')
    if errors:
        raise RuntimeError('Corpus incompleto: consulte corpus/manifest.json y reintente')


if __name__ == '__main__':
    main()
