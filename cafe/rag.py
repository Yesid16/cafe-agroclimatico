"""RAG sobre el corpus de corpus/ (.md, .txt, .pdf). Backend TF-IDF (por defecto, sin descargas)
o embeddings multilingües (sentence-transformers + FAISS si está instalado, si no numpy)."""
import re
from pathlib import Path

import numpy as np

from . import config as C


def _read(path: Path) -> str:
    if path.suffix.lower() == ".pdf":
        from pypdf import PdfReader
        return "\n".join((p.extract_text() or "") for p in PdfReader(str(path)).pages)
    return path.read_text(encoding="utf-8")


def chunk(text: str, size: int = 110, overlap: int = 25):
    words = text.split()
    step = size - overlap
    for i in range(0, max(len(words) - overlap, 1), step):
        yield " ".join(words[i:i + size])


class Retriever:
    def __init__(self, corpus_dir: Path = C.CORPUS_DIR, backend: str = C.RAG_BACKEND):
        self.chunks = []
        for p in sorted(Path(corpus_dir).glob("*")):
            if p.suffix.lower() in {".md", ".txt", ".pdf"} and p.name.upper() != "FUENTES.MD":
                for i, c in enumerate(chunk(_read(p))):
                    self.chunks.append({"fuente": p.name, "id": f"{p.name}#{i}", "texto": c})
        if not self.chunks:
            raise RuntimeError(f"Corpus vacío en {corpus_dir}")
        self.backend = backend
        texts = [c["texto"] for c in self.chunks]
        if backend == "st":
            from sentence_transformers import SentenceTransformer
            self.enc = SentenceTransformer(C.EMBED_MODEL)
            self.emb = self.enc.encode(texts, normalize_embeddings=True).astype("float32")
            try:
                import faiss
                self.index = faiss.IndexFlatIP(self.emb.shape[1])
                self.index.add(self.emb)
            except ImportError:
                self.index = None
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.vec = TfidfVectorizer(strip_accents="unicode", lowercase=True, ngram_range=(1, 2), sublinear_tf=True)
            self.mat = self.vec.fit_transform(texts)

    def search(self, query: str, k: int = 4, min_score: float = 0.05):
        if self.backend == "st":
            q = self.enc.encode([query], normalize_embeddings=True).astype("float32")
            if self.index is not None:
                s, ix = self.index.search(q, k)
                pairs = list(zip(ix[0], s[0]))
            else:
                sc = (self.emb @ q[0])
                pairs = [(i, sc[i]) for i in np.argsort(-sc)[:k]]
            min_score = max(min_score, 0.25)
        else:
            sc = (self.mat @ self.vec.transform([query]).T).toarray().ravel()
            pairs = [(i, sc[i]) for i in np.argsort(-sc)[:k]]
        return [{**self.chunks[i], "score": round(float(s), 3)} for i, s in pairs if s >= min_score]


_cache = {}


def get_retriever() -> Retriever:
    if "r" not in _cache:
        _cache["r"] = Retriever()
    return _cache["r"]


if __name__ == "__main__":
    import sys
    q = " ".join(sys.argv[1:]) or "¿qué condiciones favorecen la roya?"
    for r in get_retriever().search(q):
        print(r["score"], r["id"], "→", re.sub(r"\s+", " ", r["texto"])[:160])
