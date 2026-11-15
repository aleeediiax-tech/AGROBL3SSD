# Acceso a la Web
http://agrobl3ssd-production.up.railway.app/



# AgroBl3SSED — frontend + backend conectados

```
AgroBl3SSED/
├── backend/            API en Flask
│   ├── config.py       rutas, parámetros (vecinos, distancia máxima, CORS)
│   ├── data_loader.py  carga cultivos.json, rotaciones.json y dataset_puebla.csv al arrancar
│   ├── db.py           SQLite: guardar / listar / obtener / eliminar terrenos
│   ├── geo.py          vecinos más cercanos, textura de suelo (USDA), geocodificación
│   ├── scoring.py      puntuación de rotaciones (heurística transparente)
│   ├── app.py          rutas de la API y servidor del frontend
│   ├── data/           los 3 archivos de datos
│   └── requirements.txt
└── frontend/           tus páginas; api.js reemplaza a storage.js
```

## Ejecutar

```bash
cd backend
pip install -r requirements.txt
python app.py
```

Abre **http://127.0.0.1:5000** (Flask sirve también el frontend). También funciona abriendo
`frontend/` con Live Server (puerto 5500): `api.js` apunta solo a `127.0.0.1:5000` y el CORS ya lo permite.
La base `backend/terrenos.db` se crea sola en el primer arranque.

## API

| Método | Ruta | Qué hace |
|---|---|---|
| GET | `/api/salud` | Estado y datos cargados |
| GET | `/api/geocodificar?q=Atlixco` | Texto → `{lat, lon, nombre}` (OpenStreetMap, requiere internet) |
| POST | `/api/analisis` | Calcula clima, suelo, plagas y rotaciones. No guarda nada |
| GET / POST | `/api/terrenos` | Listar / guardar |
| GET / DELETE | `/api/terrenos/<id>` | Ver / eliminar |

Entrada (`/api/analisis` y `POST /api/terrenos`): `farmerName`, `farmName`, `location`, `lat`, `lon`,
`water` (una de las 4 opciones del formulario) y opcionales `analysisDate`, `soilType`, `cropHistory`.
Errores: `400` datos inválidos, `422` coordenadas fuera de la cobertura del dataset, `404` no encontrado.

Salida de `/api/analisis`: `clima`, `suelo`, `plagas`, `zona`, `rotaciones` (3 alternativas con
`puntaje`, `ventajas`, `desventajas`, `desglose`), `linea_base`, `recomendacion`,
`historial_detectado`, `pesos` y `aviso`.

## Qué cambió en el frontend

- **Nuevo** `api.js` (reemplaza a `storage.js`, que se eliminó).
- `registro.html/js`: campos de latitud y longitud; «Buscar en mapa» ahora también las rellena.
  Se corrigió la opción «Lim francoso» → «Franco limoso».
- `analisis.html/js`: las tarjetas, las alternativas, la comparación y la recomendación se llenan con la respuesta de la API.
  «Humedad del suelo» pasó a «Humedad relativa», porque eso es lo que trae el dataset.
- `mis-terrenos.js`: lee y elimina desde el backend.
- Se corrigió el `\n` literal que aparecía en el menú de `index`, `registro` y `analisis`.
- Los terrenos que ya estaban en el `localStorage` del navegador **no se migran**.

## Limitaciones a tener presentes

- **El dataset actual no tiene estructura geográfica ni estacional**: todos los terrenos de Puebla
  reciben valores casi iguales (~21 °C, ~60–80 mm/mes). Cuando tengas datos reales con las mismas
  columnas, basta con reemplazar `backend/data/dataset_puebla.csv`.
- El puntaje de rotaciones es una **heurística** sobre los parámetros generales de `cultivos.json`;
  no es una recomendación agronómica validada. El desglose de cada puntaje viene en la respuesta.
- El historial de cosechas se interpreta buscando nombres de cultivos en el texto; se asume que el
  primero mencionado es el más reciente.
- No hay autenticación: todos los terrenos son visibles para cualquiera que alcance el servidor.
  Está pensado para uso local (escucha solo en 127.0.0.1).
- La sección «Mapas del terreno» del análisis sigue siendo un marcador de posición.
