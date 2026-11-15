// En producción (Railway) y con Flask local el frontend y la API comparten origen -> "/api".
// Solo con Live Server (puerto 5500) o abriendo el archivo con doble clic se apunta al backend local.
const API = (location.protocol === "file:" || location.port === "5500") ? "http://127.0.0.1:5000/api" : "/api";

async function peticion(ruta, { method = "GET", body } = {}) {
  let respuesta;
  try {
    respuesta = await fetch(`${API}${ruta}`, {
      method,
      headers: body === undefined ? undefined : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor. Verifica que el backend esté encendido (python app.py).");
  }
  let datos = null;
  try { datos = await respuesta.json(); } catch { /* respuesta sin JSON */ }
  if (!respuesta.ok) throw new Error(datos?.error || `Error del servidor (${respuesta.status}).`);
  return datos;
}

const analizarTerreno = terreno => peticion("/analisis", { method: "POST", body: terreno });
const guardarTerreno = terreno => peticion("/terrenos", { method: "POST", body: terreno });
const listarTerrenos = () => peticion("/terrenos");
const obtenerTerreno = id => peticion(`/terrenos/${encodeURIComponent(id)}`);
const eliminarTerreno = id => peticion(`/terrenos/${encodeURIComponent(id)}`, { method: "DELETE" });
const geocodificar = texto => peticion(`/geocodificar?q=${encodeURIComponent(texto)}`);

// Escapa texto antes de insertarlo con innerHTML.
function escapeHTML(value = "") {
  return String(value).replace(/[&<>"']/g, char => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[char]));
}
