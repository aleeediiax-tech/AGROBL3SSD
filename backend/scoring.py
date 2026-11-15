"""Puntuación de rotaciones de cultivos para un terreno.

IMPORTANTE: es un modelo heurístico y transparente, NO una recomendación
agronómica validada. Parte de las 7 dimensiones de cada cultivo
(cultivos.json), las promedia por rotación y las pondera según las
condiciones del terreno (agua, suelo, plagas). Después suma ajustes simples
por estructura de la rotación (diversidad, cobertura, familias repetidas),
déficit de agua, helada e historial. Todo el desglose se devuelve en la
respuesta para poder auditarlo.
"""
import re
import unicodedata
from statistics import mean

import data_loader as datos

DIMENSIONES = ("suelo", "agua", "erosion", "nitrogeno", "plagas", "ingresos", "clima")
ETIQUETAS = {
    "suelo": "salud del suelo",
    "agua": "uso de agua",
    "erosion": "control de erosión",
    "nitrogeno": "aporte de nitrógeno",
    "plagas": "manejo de plagas",
    "ingresos": "ingresos",
    "clima": "adaptación al clima",
}
UMBRAL_DIFERENCIA = 8  # puntos de diferencia frente a la rotación actual para citarla
AVISO = (
    "Estimación orientativa basada en parámetros generales de cultivos y en el dataset "
    "de la zona. No es una recomendación agronómica validada; consúltala con un técnico local."
)


def _normalizar(texto):
    t = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in t if not unicodedata.combining(c)).lower()


def _construir_patrones():
    """palabra clave (primera palabra del nombre) -> (id_cultivo, regex)."""
    patrones = {}
    for cid, cultivo in datos.CULTIVOS.items():
        palabra = re.sub(r"[^a-z]", "", _normalizar(cultivo["nombre"]).split()[0])
        if len(palabra) < 3 or palabra in patrones:
            continue  # ya existe: el primero del JSON gana (maiz_grano antes que maiz_forrajero)
        if palabra.endswith("z"):
            cuerpo = f"(?:{palabra}|{palabra[:-1]}ces)"
        else:
            cuerpo = f"{palabra}(?:es|s)?"
        patrones[palabra] = (cid, re.compile(rf"\b{cuerpo}\b"))
    return patrones


_PATRONES = _construir_patrones()


def detectar_historial(texto):
    """Ids de cultivos mencionados en el texto, en orden de aparición.

    Supuesto: el primero que se menciona es el más reciente
    ("El año pasado sembré maíz y antes frijol").
    """
    norm = _normalizar(texto or "")
    hallados = []
    for cid, patron in _PATRONES.values():
        m = patron.search(norm)
        if m:
            hallados.append((m.start(), cid))
    hallados.sort()
    return [cid for _, cid in hallados]


def grupo_suelo(texto):
    t = _normalizar(texto or "")
    if "arenos" in t:
        return "arenoso"
    if "arcill" in t:
        return "arcilloso"
    if "franco" in t or "limo" in t:
        return "franco"
    return None


def _agua_disponible(agua, precip_anual):
    if agua == "Riego disponible":
        return 0.95
    if agua == "Depende de la lluvia":
        return min(0.85, max(0.25, precip_anual / 1200))
    if agua == "Disponibilidad limitada":
        return 0.35
    if agua == "Disponibilidad variable":
        return 0.55
    return 0.6


def _pesos(agua, grupo, precip_anual, indice_plagas):
    pesos = {d: 1.0 for d in DIMENSIONES}
    if agua == "Disponibilidad limitada":
        pesos["agua"] = 1.8
    elif agua == "Disponibilidad variable":
        pesos["agua"] = 1.4
    elif agua == "Depende de la lluvia":
        pesos["agua"] = 1.4 if precip_anual < 700 else 1.1
    elif agua == "Riego disponible":
        pesos["agua"] = 0.8
    if grupo == "arenoso":
        pesos["erosion"] += 0.4
    if precip_anual > 1500:
        pesos["erosion"] += 0.2
    pesos["plagas"] = 1.0 + 2.0 * indice_plagas
    return pesos


def _contexto(terreno, zona):
    agua = terreno.get("water") or ""
    precip = zona["clima"]["precipitacion_anual_mm"]
    temp = zona["clima"]["temperatura_c"]
    grupo = grupo_suelo(terreno.get("soilType")) or grupo_suelo(zona["suelo"]["textura"])
    historial = detectar_historial(terreno.get("cropHistory"))
    reciente = datos.CULTIVOS[historial[0]] if historial else None
    return {
        "agua_disp": _agua_disponible(agua, precip),
        "pesos": _pesos(agua, grupo, precip, zona["plagas"]["indice"]),
        "riesgo_helada": min(1.0, max(0.0, (14 - temp) / 8)),
        "historial": historial,
        "familia_reciente": reciente["familia"] if reciente else None,
        "nombre_reciente": reciente["nombre"] if reciente else None,
    }


def _dimensiones(cultivos):
    return {d: mean(c["dimensiones"][d] for c in cultivos) for d in DIMENSIONES}


def _puntuar(rot, ctx, dims_base):
    cultivos = [datos.CULTIVOS[i] for i in rot["secuencia"]]
    dims = _dimensiones(cultivos)
    peso_total = sum(ctx["pesos"].values())
    base = sum(ctx["pesos"][d] * dims[d] for d in DIMENSIONES) / peso_total

    familias = [c["familia"] for c in cultivos]
    ratio = len(set(familias)) / len(familias)
    if len(familias) == 1:
        pares = []
    elif len(familias) == 2:
        pares = [(familias[0], familias[1])]
    else:
        pares = list(zip(familias, familias[1:] + familias[:1]))  # la rotación es cíclica
    repetidas = sum(1 for a, b in pares if a == b)

    demanda = mean(c["demanda_agua"] for c in cultivos)
    deficit = max(0.0, demanda - ctx["agua_disp"])
    sens_helada = mean(c["sensibilidad_helada"] for c in cultivos)
    repite_reciente = bool(ctx["familia_reciente"]) and familias[0] == ctx["familia_reciente"]

    desglose = {
        "base": round(base, 1),
        "diversidad": round(12 * (ratio - 0.5), 1),
        "cobertura": 4.0 if any(c["es_cobertura"] for c in cultivos) else 0.0,
        "familias_consecutivas": -5.0 * repetidas,
        "agua": round(-50 * deficit, 1),
        "helada": round(-15 * ctx["riesgo_helada"] * sens_helada, 1),
        "historial": -6.0 if repite_reciente else 0.0,
    }
    desglose = {k: v + 0.0 for k, v in desglose.items()}  # evita mostrar "-0.0"
    puntaje = max(0.0, min(100.0, sum(desglose.values())))

    ventajas, desventajas = [], []
    if dims_base:
        for d in DIMENSIONES:
            dif = dims[d] - dims_base[d]
            if dif >= UMBRAL_DIFERENCIA:
                ventajas.append(f"Mejora en {ETIQUETAS[d]}: +{dif:.0f} pts frente a tu rotación actual.")
            elif dif <= -UMBRAL_DIFERENCIA:
                desventajas.append(f"Menor puntaje en {ETIQUETAS[d]}: {dif:.0f} pts frente a tu rotación actual.")
    if "Fabaceae" in familias:
        ventajas.append("Incluye una leguminosa, que aporta nitrógeno al suelo.")
    if desglose["cobertura"]:
        ventajas.append("Incluye un cultivo de cobertura que protege el suelo.")
    if ratio == 1 and len(familias) > 1:
        ventajas.append("Alterna familias botánicas distintas, lo que reduce plagas y enfermedades comunes.")
    if repetidas:
        desventajas.append("Hay cultivos de la misma familia seguidos, lo que favorece plagas y enfermedades comunes.")
    if deficit > 0.05:
        desventajas.append(
            f"Su demanda de agua ({demanda:.0%}) supera la disponibilidad estimada de tu terreno ({ctx['agua_disp']:.0%})."
        )
    if ctx["riesgo_helada"] > 0.2 and sens_helada > 0.5:
        desventajas.append("Sus cultivos son sensibles a heladas y la zona tiene temperaturas medias bajas.")
    if repite_reciente:
        desventajas.append(f"Empieza con la misma familia botánica que tu cultivo más reciente ({ctx['nombre_reciente']}).")

    return {
        "id": rot["id"],
        "nombre": rot["nombre"],
        "subtitulo": rot.get("subtitulo", ""),
        "actual": bool(rot.get("actual")),
        "notas": rot.get("notas", ""),
        "secuencia": [{"id": i, "nombre": datos.CULTIVOS[i]["nombre"]} for i in rot["secuencia"]],
        "puntaje": round(puntaje, 1),
        "dimensiones": {d: round(v, 1) for d, v in dims.items()},
        "desglose": desglose,
        "ventajas": (ventajas or ["Sin ventajas destacadas frente a tu rotación actual."])[:4],
        "desventajas": (desventajas or ["Sin desventajas destacadas para las condiciones registradas."])[:4],
    }


def evaluar(terreno, zona, n_alternativas=3):
    """Evalúa todas las rotaciones y devuelve alternativas, línea base y recomendación."""
    ctx = _contexto(terreno, zona)

    actual = next((r for r in datos.ROTACIONES if r.get("actual")), None)
    dims_base = _dimensiones([datos.CULTIVOS[i] for i in actual["secuencia"]]) if actual else None
    linea_base = _puntuar(actual, ctx, None) if actual else None

    puntuadas = [_puntuar(r, ctx, dims_base) for r in datos.ROTACIONES if not r.get("actual")]
    puntuadas.sort(key=lambda r: (-r["puntaje"], r["nombre"]))
    alternativas = puntuadas[:n_alternativas]

    mejor = alternativas[0]
    if linea_base and mejor["puntaje"] > linea_base["puntaje"]:
        diferencia = mejor["puntaje"] - linea_base["puntaje"]
        motivo = (
            f"{mejor['nombre']} obtiene {mejor['puntaje']:.0f}/100, {diferencia:.0f} puntos más que tu "
            f"rotación actual ({linea_base['nombre']}, {linea_base['puntaje']:.0f}/100)."
        )
    elif linea_base:
        motivo = (
            f"Ninguna alternativa supera a tu rotación actual ({linea_base['nombre']}, "
            f"{linea_base['puntaje']:.0f}/100) con los datos registrados. "
            f"La mejor alternativa es {mejor['nombre']} ({mejor['puntaje']:.0f}/100)."
        )
    else:
        motivo = f"{mejor['nombre']} obtiene {mejor['puntaje']:.0f}/100 con los datos registrados."

    return {
        "rotaciones": alternativas,
        "linea_base": linea_base,
        "recomendacion": {
            "id": mejor["id"],
            "nombre": mejor["nombre"],
            "puntaje": mejor["puntaje"],
            "motivo": motivo,
            "destacados": mejor["ventajas"][:2],
        },
        "historial_detectado": [
            {"id": i, "nombre": datos.CULTIVOS[i]["nombre"]} for i in ctx["historial"]
        ],
        "pesos": {d: round(v, 2) for d, v in ctx["pesos"].items()},
        "aviso": AVISO,
    }
