"""Configuración central. Todo lo ajustable vive aquí o en variables de entorno (.env)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
CORPUS_DIR = ROOT / "corpus"
RESULTS_DIR = ROOT / "results"
DEMO_MARKER = DATA_RAW / ".synthetic_demo"


def is_demo_data() -> bool:
    return DEMO_MARKER.exists()

# Carga opcional de .env (sin dependencia dura)
_env = ROOT / ".env"
if _env.exists():
    for line in _env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# --- Datos: IDEAM en datos.gov.co (Socrata) ---
SOCRATA_BASE = "https://www.datos.gov.co/resource"
DS_PRECIP = "s54a-sgyg"   # Precipitación (lectura cada 10 min, mm)
DS_TEMP = "sbwg-7ju4"     # Temperatura (red de estaciones IDEAM)
DEPARTAMENTOS = ["ANTIOQUIA", "CALDAS", "RISARALDA", "QUINDIO", "QUINDÍO"]
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN")  # opcional: sube el límite de peticiones

PRECIP_DAILY = DATA_RAW / "precip_diaria.csv"
TEMP_DAILY = DATA_RAW / "temp_diaria.csv"
WEEKLY = DATA_PROC / "semanal.csv"
MODEL_PATH = DATA_PROC / "modelo_roya.pkl"

# Calidad: lecturas mínimas por día (10 min → 144 lecturas/día)
MIN_N_DAY = 72
MIN_DAYS_WEEK_RAIN = 5
MIN_DAYS_WEEK_TEMP = 4
MIN_WEEKS_MUNICIPIO = 60

# --- LLM (endpoint compatible con OpenAI). Sin clave => modo "mock" determinista ---
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.groq.com/openai/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
T_MAX = int(os.getenv("AGENT_T_MAX", "6"))  # iteraciones máximas del loop agéntico

# --- RAG ---
RAG_BACKEND = os.getenv("RAG_BACKEND", "tfidf")  # "tfidf" | "st" (sentence-transformers)
EMBED_MODEL = os.getenv("EMBED_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")
