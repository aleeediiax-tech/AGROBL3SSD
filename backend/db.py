"""Persistencia de terrenos en SQLite (reemplaza al localStorage del frontend).

El frontend usa claves en camelCase (farmerName, farmName...), así que las
funciones reciben y devuelven diccionarios con esas mismas claves; la
traducción a columnas SQL se hace aquí y en ningún otro lugar.
"""
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone

import config

# clave del frontend -> columna SQL
CAMPOS = {
    "farmerName": "farmer_name",
    "farmName": "farm_name",
    "analysisDate": "analysis_date",
    "soilType": "soil_type",
    "location": "location",
    "lat": "lat",
    "lon": "lon",
    "water": "water",
    "cropHistory": "crop_history",
}

_ESQUEMA = """
CREATE TABLE IF NOT EXISTS terrenos (
    id            TEXT PRIMARY KEY,
    farmer_name   TEXT NOT NULL,
    farm_name     TEXT NOT NULL,
    analysis_date TEXT,
    soil_type     TEXT,
    location      TEXT NOT NULL,
    lat           REAL NOT NULL,
    lon           REAL NOT NULL,
    water         TEXT NOT NULL,
    crop_history  TEXT,
    created_at    TEXT NOT NULL
)
"""


def conectar():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def iniciar_db():
    with closing(conectar()) as conn, conn:
        conn.execute(_ESQUEMA)


def _a_dict(fila):
    datos = {clave: fila[col] for clave, col in CAMPOS.items()}
    datos["id"] = fila["id"]
    datos["createdAt"] = fila["created_at"]
    return datos


def crear(datos):
    """Inserta un terreno y devuelve el registro guardado (con id y createdAt)."""
    nuevo_id = uuid.uuid4().hex
    creado = datetime.now(timezone.utc).isoformat(timespec="seconds")
    columnas = ["id", "created_at"] + list(CAMPOS.values())
    valores = [nuevo_id, creado] + [datos.get(clave) for clave in CAMPOS]
    marcas = ", ".join("?" for _ in columnas)
    with closing(conectar()) as conn, conn:
        conn.execute(f"INSERT INTO terrenos ({', '.join(columnas)}) VALUES ({marcas})", valores)
    return obtener(nuevo_id)


def listar():
    """Todos los terrenos, el más reciente primero."""
    with closing(conectar()) as conn:
        filas = conn.execute("SELECT * FROM terrenos ORDER BY created_at DESC, rowid DESC").fetchall()
    return [_a_dict(f) for f in filas]


def obtener(terreno_id):
    with closing(conectar()) as conn:
        fila = conn.execute("SELECT * FROM terrenos WHERE id = ?", (terreno_id,)).fetchone()
    return _a_dict(fila) if fila else None


def eliminar(terreno_id):
    """Devuelve True si había un terreno con ese id."""
    with closing(conectar()) as conn, conn:
        cursor = conn.execute("DELETE FROM terrenos WHERE id = ?", (terreno_id,))
    return cursor.rowcount > 0
