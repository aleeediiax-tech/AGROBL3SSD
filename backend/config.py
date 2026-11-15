"""Configuración central del backend: rutas, parámetros y opciones.

Aquí no hay lógica; los demás módulos importan estas constantes.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR.parent / "frontend"

CSV_PATH = DATA_DIR / "dataset_puebla.csv"
CULTIVOS_PATH = DATA_DIR / "cultivos.json"
ROTACIONES_PATH = DATA_DIR / "rotaciones.json"
DB_PATH = Path(os.environ.get("AGRO_DB_PATH", BASE_DIR / "terrenos.db"))

# Servidor
HOST = os.environ.get("AGRO_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT") or os.environ.get("AGRO_PORT", "5000"))

# Orígenes del frontend que pueden llamar a la API (Live Server, Flask, archivo local).
# "null" es el origen que envía el navegador al abrir index.html con doble clic.
# Es válido para desarrollo local; en producción déjalo solo con tu dominio real.
ALLOWED_ORIGINS = [
    "http://127.0.0.1:5500",
    "http://localhost:5500",
    "http://127.0.0.1:5000",
    "http://localhost:5000",
    "null",
]
# En producción el frontend se sirve desde el mismo dominio, así que CORS no hace falta.
# Si algún día usas otro dominio para el frontend: AGRO_ALLOWED_ORIGINS="https://mi-sitio.com,https://otro.com"
if os.environ.get("AGRO_ALLOWED_ORIGINS"):
    ALLOWED_ORIGINS = [o.strip() for o in os.environ["AGRO_ALLOWED_ORIGINS"].split(",") if o.strip()]

# Análisis de la zona
N_VECINOS = 40            # puntos del dataset que se promedian alrededor del terreno
MAX_DISTANCIA_KM = 25     # si el punto más cercano está más lejos, el terreno está fuera de cobertura

# Valores válidos del campo "Disponibilidad de agua" del formulario
OPCIONES_AGUA = (
    "Riego disponible",
    "Depende de la lluvia",
    "Disponibilidad limitada",
    "Disponibilidad variable",
)

# Geocodificador gratuito (OpenStreetMap Nominatim). Requiere internet.
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
GEOCODER_USER_AGENT = "AgroBl3SSED/1.0 (proyecto academico)"
GEOCODER_TIMEOUT = 8
