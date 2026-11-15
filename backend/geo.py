import json
import urllib.error
import urllib.parse
import urllib.request

import numpy as np

import config
import data_loader as datos

RADIO_TIERRA_KM = 6371.0


class FueraDeCobertura(Exception):
    """El punto está demasiado lejos de cualquier dato del dataset."""


def distancias_km(lat, lon):
    """Distancia haversine (km) del punto dado a cada fila del dataset."""
    lat0, lon0 = np.radians(lat), np.radians(lon)
    a = (np.sin((datos.LAT_RAD - lat0) / 2) ** 2
         + np.cos(lat0) * np.cos(datos.LAT_RAD) * np.sin((datos.LON_RAD - lon0) / 2) ** 2)
    return 2 * RADIO_TIERRA_KM * np.arcsin(np.sqrt(a))


def clasificar_textura(arcilla, arena, limo):
    """Clase de textura según el triángulo USDA, en español."""
    c, a, s = arcilla, arena, limo
    if s + 1.5 * c < 15:
        return "Arenoso"
    if s + 1.5 * c >= 15 and s + 2 * c < 30:
        return "Arenoso franco"
    if (7 <= c < 20 and a > 52 and s + 2 * c >= 30) or (c < 7 and s < 50 and s + 2 * c >= 30):
        return "Franco arenoso"
    if 7 <= c < 27 and 28 <= s < 50 and a <= 52:
        return "Franco"
    if (s >= 50 and 12 <= c < 27) or (50 <= s < 80 and c < 12):
        return "Franco limoso"
    if s >= 80 and c < 12:
        return "Limoso"
    if 20 <= c < 35 and s < 28 and a > 45:
        return "Franco arcillo-arenoso"
    if 27 <= c < 40 and 20 < a <= 45:
        return "Franco arcilloso"
    if 27 <= c < 40 and a <= 20:
        return "Franco arcillo-limoso"
    if c >= 35 and a > 45:
        return "Arcillo-arenoso"
    if c >= 40 and s >= 40:
        return "Arcillo-limoso"
    if c >= 40 and a <= 45 and s < 40:
        return "Arcilloso"
    return "Franco"


def resumen_zona(lat, lon):
    """Resumen del clima, suelo y plagas alrededor de (lat, lon).

    Lanza FueraDeCobertura si el dato más cercano está a más de
    config.MAX_DISTANCIA_KM.
    """
    d = distancias_km(lat, lon)
    if d.min() > config.MAX_DISTANCIA_KM:
        raise FueraDeCobertura(
            f"Las coordenadas quedan fuera de la zona cubierta por los datos "
            f"(el punto más cercano está a {d.min():.0f} km). "
            f"Los datos disponibles cubren Puebla y sus alrededores."
        )

    n = min(config.N_VECINOS, len(d))
    idx = np.argpartition(d, n - 1)[:n]
    vecinos = datos.df.iloc[idx]

    arcilla = float(vecinos["Arcilla_%"].mean())
    arena = float(vecinos["Arena_%"].mean())
    limo = float(vecinos["Limo_%"].mean())

    conteo = vecinos["Riesgo_Plagas"].value_counts(normalize=True)
    plagas = {nivel: round(float(conteo.get(nivel, 0.0)), 3) for nivel in ("Bajo", "Medio", "Alto")}
    indice_plagas = 0.5 * plagas["Medio"] + 1.0 * plagas["Alto"]

    precip_mensual = float(vecinos["Precipitacion_Mensual_mm"].mean())

    return {
        "zona": {
            "puntos_usados": int(n),
            "distancia_min_km": round(float(d[idx].min()), 1),
            "distancia_max_km": round(float(d[idx].max()), 1),
        },
        "clima": {
            "temperatura_c": round(float(vecinos["Temp_Media_C"].mean()), 1),
            "precipitacion_mensual_mm": round(precip_mensual, 1),
            "precipitacion_anual_mm": round(precip_mensual * 12, 0),
            "humedad_relativa": round(float(vecinos["Humedad_Relativa_%"].mean()), 1),
        },
        "suelo": {
            "arcilla": round(arcilla, 1),
            "arena": round(arena, 1),
            "limo": round(limo, 1),
            "textura": clasificar_textura(arcilla, arena, limo),
        },
        "plagas": {
            **plagas,
            "indice": round(indice_plagas, 3),
            "predominante": max(plagas, key=plagas.get),
        },
    }


def geocodificar(consulta):
    """Texto -> {"lat", "lon", "nombre"} o None si no se encuentra o no hay internet."""
    consulta = (consulta or "").strip()
    if not consulta:
        return None
    params = urllib.parse.urlencode(
        {"q": consulta, "format": "json", "limit": 1, "countrycodes": "mx"}
    )
    peticion = urllib.request.Request(
        f"{config.GEOCODER_URL}?{params}",
        headers={"User-Agent": config.GEOCODER_USER_AGENT, "Accept-Language": "es"},
    )
    try:
        with urllib.request.urlopen(peticion, timeout=config.GEOCODER_TIMEOUT) as resp:
            resultados = json.load(resp)
        if not resultados:
            return None
        primero = resultados[0]
        return {
            "lat": float(primero["lat"]),
            "lon": float(primero["lon"]),
            "nombre": primero.get("display_name", ""),
        }
    except (OSError, ValueError, KeyError, TypeError):
        # OSError cubre URLError y timeouts; el resto, respuestas mal formadas.
        return None
