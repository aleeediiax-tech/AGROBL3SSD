"""Servidor Flask: recibe peticiones del frontend y delega en las demás capas.

Rutas de la API:
  GET    /api/salud               estado del servidor y datos cargados
  GET    /api/geocodificar?q=...  texto -> coordenadas
  POST   /api/analisis            clima, suelo y rotaciones para un terreno (no guarda nada)
  GET    /api/terrenos            lista de terrenos guardados
  POST   /api/terrenos            guarda un terreno
  GET    /api/terrenos/<id>       un terreno
  DELETE /api/terrenos/<id>       elimina un terreno

También sirve el frontend en "/" para poder usar todo desde http://127.0.0.1:5000
"""
import math
import os
from datetime import date

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from werkzeug.exceptions import HTTPException

import config
import data_loader as datos
import db
import geo
import scoring

app = Flask(__name__, static_folder=None)
CORS(app, resources={r"/api/*": {"origins": config.ALLOWED_ORIGINS}})
db.iniciar_db()


class ErrorValidacion(Exception):
    """Datos de entrada inválidos (HTTP 400)."""


def _texto(cuerpo, clave, obligatorio=False, maximo=200):
    valor = cuerpo.get(clave)
    valor = "" if valor is None else str(valor).strip()
    if obligatorio and not valor:
        raise ErrorValidacion(f"Falta el campo obligatorio: {clave}.")
    if len(valor) > maximo:
        raise ErrorValidacion(f"El campo {clave} excede {maximo} caracteres.")
    return valor


def _numero(cuerpo, clave, minimo, maximo):
    try:
        valor = float(cuerpo.get(clave))
    except (TypeError, ValueError):
        raise ErrorValidacion(f"El campo {clave} debe ser un número.")
    if not math.isfinite(valor) or not (minimo <= valor <= maximo):
        raise ErrorValidacion(f"El campo {clave} debe estar entre {minimo} y {maximo}.")
    return valor


def validar_terreno(cuerpo):
    """Devuelve el terreno limpio (solo los campos conocidos) o lanza ErrorValidacion."""
    if not isinstance(cuerpo, dict):
        raise ErrorValidacion("Se esperaba un objeto JSON.")
    fecha = _texto(cuerpo, "analysisDate", maximo=10) or date.today().isoformat()
    try:
        date.fromisoformat(fecha)
    except ValueError:
        raise ErrorValidacion("analysisDate debe tener formato AAAA-MM-DD.")
    agua = _texto(cuerpo, "water", obligatorio=True)
    if agua not in config.OPCIONES_AGUA:
        raise ErrorValidacion("water debe ser una de: " + ", ".join(config.OPCIONES_AGUA) + ".")
    return {
        "farmerName": _texto(cuerpo, "farmerName", obligatorio=True),
        "farmName": _texto(cuerpo, "farmName", obligatorio=True),
        "analysisDate": fecha,
        "soilType": _texto(cuerpo, "soilType", maximo=60),
        "location": _texto(cuerpo, "location", obligatorio=True),
        "lat": _numero(cuerpo, "lat", -90, 90),
        "lon": _numero(cuerpo, "lon", -180, 180),
        "water": agua,
        "cropHistory": _texto(cuerpo, "cropHistory", maximo=2000),
    }


def _cuerpo_json():
    cuerpo = request.get_json(silent=True)
    if cuerpo is None:
        raise ErrorValidacion("El cuerpo de la petición debe ser JSON.")
    return cuerpo


# ---------- Errores ----------
@app.errorhandler(ErrorValidacion)
def _error_validacion(e):
    return jsonify(error=str(e)), 400


@app.errorhandler(geo.FueraDeCobertura)
def _error_cobertura(e):
    return jsonify(error=str(e)), 422


@app.errorhandler(HTTPException)
def _error_http(e):
    if request.path.startswith("/api/"):
        return jsonify(error=e.description), e.code
    return e


# ---------- API ----------
@app.get("/api/salud")
def salud():
    return jsonify(
        estado="ok",
        puntos_dataset=len(datos.df),
        cultivos=len(datos.CULTIVOS),
        rotaciones=len(datos.ROTACIONES),
    )


@app.get("/api/geocodificar")
def geocodificar():
    resultado = geo.geocodificar(request.args.get("q", ""))
    if resultado is None:
        return jsonify(error="No se encontraron coordenadas para esa ubicación."), 404
    return jsonify(resultado)


@app.post("/api/analisis")
def analisis():
    terreno = validar_terreno(_cuerpo_json())
    zona = geo.resumen_zona(terreno["lat"], terreno["lon"])
    evaluacion = scoring.evaluar(terreno, zona)
    zona["suelo"]["declarado"] = terreno["soilType"] or None
    return jsonify({**zona, **evaluacion})


@app.get("/api/terrenos")
def listar_terrenos():
    return jsonify(db.listar())


@app.post("/api/terrenos")
def crear_terreno():
    terreno = validar_terreno(_cuerpo_json())
    geo.resumen_zona(terreno["lat"], terreno["lon"])  # rechaza coordenadas fuera de cobertura
    return jsonify(db.crear(terreno)), 201


@app.get("/api/terrenos/<terreno_id>")
def obtener_terreno(terreno_id):
    terreno = db.obtener(terreno_id)
    if terreno is None:
        return jsonify(error="Terreno no encontrado."), 404
    return jsonify(terreno)


@app.delete("/api/terrenos/<terreno_id>")
def eliminar_terreno(terreno_id):
    if not db.eliminar(terreno_id):
        return jsonify(error="Terreno no encontrado."), 404
    return jsonify(eliminado=True)


# ---------- Frontend estático ----------
@app.get("/")
def inicio():
    return send_from_directory(config.FRONTEND_DIR, "index.html")


@app.get("/<path:archivo>")
def estaticos(archivo):
    return send_from_directory(config.FRONTEND_DIR, archivo)


if __name__ == "__main__":
    app.run(host=config.HOST, port=config.PORT, debug=os.environ.get("AGRO_DEBUG") == "1")
