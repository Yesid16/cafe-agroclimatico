"""Descarga los PDF listados en corpus/urls.txt hacia corpus/ (fuentes abiertas: Cenicafé, FNC, IDEAM)."""
import requests

from . import config as C


def main():
    f = C.CORPUS_DIR / "urls.txt"
    if not f.exists():
        print("Cree corpus/urls.txt con una URL de PDF por línea.")
        return
    for url in [u.strip() for u in f.read_text().splitlines() if u.strip() and not u.startswith("#")]:
        name = url.split("?")[0].rstrip("/").split("/")[-1] or "doc.pdf"
        if not name.lower().endswith(".pdf"):
            name += ".pdf"
        try:
            r = requests.get(url, timeout=120)
            r.raise_for_status()
            (C.CORPUS_DIR / name).write_bytes(r.content)
            print("ok", name)
        except Exception as e:  # noqa: BLE001
            print("falló", url, e)


if __name__ == "__main__":
    main()
