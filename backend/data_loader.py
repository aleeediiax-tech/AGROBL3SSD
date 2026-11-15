"""Carga única de los datos al arrancar el servidor.

Expone tres objetos listos para importar:
  df          -> DataFrame con dataset_puebla.csv
  CULTIVOS    -> dict {id_cultivo: {...}} de cultivos.json
  ROTACIONES  -> lista de rotaciones de rotaciones.json
Además deja precalculadas las coordenadas en radianes (LAT_RAD, LON_RAD)
para que la búsqueda de vecinos cercanos sea rápida.
"""
import json

import numpy as np
import pandas as pd

import config

COLUMNAS_REQUERIDAS = (
    "Latitud", "Longitud", "Temp_Media_C", "Precipitacion_Mensual_mm",
    "Humedad_Relativa_%", "Arcilla_%", "Arena_%", "Limo_%", "Riesgo_Plagas",
)


def _leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


df = pd.read_csv(config.CSV_PATH)
_faltan = [c for c in COLUMNAS_REQUERIDAS if c not in df.columns]
if _faltan:
    raise ValueError(f"Al dataset le faltan columnas: {_faltan}")

LAT_RAD = np.radians(df["Latitud"].to_numpy(dtype=float))
LON_RAD = np.radians(df["Longitud"].to_numpy(dtype=float))

CULTIVOS = _leer_json(config.CULTIVOS_PATH)["cultivos"]
ROTACIONES = _leer_json(config.ROTACIONES_PATH)

# Validación temprana: toda rotación debe referirse a cultivos que existen.
for _rot in ROTACIONES:
    for _cid in _rot["secuencia"]:
        if _cid not in CULTIVOS:
            raise ValueError(f"La rotación '{_rot['id']}' usa un cultivo inexistente: {_cid}")
