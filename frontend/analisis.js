const DRAFT_KEY = "agrobl3ssedCurrentTerrain";
const LETTERS = ["A", "B", "C"];
const byId = id => document.getElementById(id);
const selectedId = new URLSearchParams(location.search).get("id");

const farmTitle = byId("farmTitle");
const resultSubtitle = byId("resultSubtitle");
const saveButton = byId("saveTerrain");
const zoneNote = byId("zoneNote");
let current = null; // terreno que se está viendo; tiene id solo si ya está guardado

function setNote(text, isError = false) {
  zoneNote.textContent = text;
  zoneNote.classList.toggle("is-error", isError);
}

function markSaved() {
  saveButton.textContent = "✓ Terreno guardado";
  saveButton.disabled = true;
  saveButton.classList.add("is-saved");
}

function showUnavailable() {
  ["metricTempNote", "metricRainNote", "metricHumidityNote"].forEach(id => { byId(id).textContent = "No disponible"; });
  byId("cropChips").innerHTML = "";
  byId("rotationList").innerHTML = "";
  byId("comparisonBody").innerHTML = "<p>No disponible.</p>";
  byId("recommendationBody").innerHTML = "<p>No disponible.</p>";
}

function showNoTerrain(message) {
  resultSubtitle.textContent = message || "Aún no hay datos registrados. Completa el formulario para personalizar esta vista.";
  document.querySelector(".notice").insertAdjacentHTML("afterend", '<p class="empty-state">Para generar el análisis de tu parcela, primero <a href="registro.html">registra tu terreno</a>.</p>');
  saveButton.disabled = true;
  saveButton.textContent = "Sin terreno para guardar";
  showUnavailable();
}

function paintMetrics(r) {
  byId("metricTemp").textContent = `${r.clima.temperatura_c} °C`;
  byId("metricTempNote").textContent = "Promedio de la zona";
  byId("metricRain").textContent = `${r.clima.precipitacion_mensual_mm} mm`;
  byId("metricRainNote").textContent = `Promedio mensual · ≈ ${r.clima.precipitacion_anual_mm} mm al año`;
  byId("metricHumidity").textContent = `${r.clima.humedad_relativa} %`;
  byId("metricHumidityNote").textContent = "Humedad del aire en la zona";

  const s = r.suelo;
  const parts = [`Suelo de la zona: ${s.textura} (${s.arcilla} % arcilla, ${s.arena} % arena, ${s.limo} % limo)`];
  if (s.declarado) parts.push(`declarado por ti: ${s.declarado}`);
  parts.push(`riesgo de plagas predominante: ${r.plagas.predominante.toLowerCase()}`);
  parts.push(`calculado con ${r.zona.puntos_usados} puntos a ${r.zona.distancia_min_km}–${r.zona.distancia_max_km} km`);
  if (r.historial_detectado.length) parts.push(`historial reconocido: ${r.historial_detectado.map(c => c.nombre).join(", ")}`);
  setNote(parts.join(" · ") + ".");
}

function paintCrops(r) {
  const names = [...new Set(r.rotaciones.flatMap(rot => rot.secuencia.map(c => c.nombre)))];
  byId("cropChips").innerHTML = names.map(n => `<span>${escapeHTML(n)}</span>`).join("");
}

function paintRotations(r) {
  byId("rotationList").innerHTML = r.rotaciones.map((rot, i) => {
    const badge = rot.id === r.recomendacion.id ? ' <span class="badge-reco">Recomendada</span>' : "";
    const sequence = rot.secuencia.map(c => escapeHTML(c.nombre)).join(" → ");
    return `<div class="rotation-item"><b>Alternativa ${LETTERS[i]} · ${Math.round(rot.puntaje)}/100${badge}</b><span>${sequence}</span><small>${escapeHTML(rot.subtitulo)}</small></div>`;
  }).join("");
}

function paintComparison(r) {
  const list = (cls, items) => `<ul class="${cls}">${items.map(t => `<li>${escapeHTML(t)}</li>`).join("")}</ul>`;
  byId("comparisonBody").innerHTML = '<div class="compare-grid">' + r.rotaciones.map((rot, i) =>
    `<div class="compare-item"><h4>Alternativa ${LETTERS[i]} · ${escapeHTML(rot.nombre)}</h4>${list("pros", rot.ventajas)}${list("cons", rot.desventajas)}</div>`
  ).join("") + "</div>";
}

function paintRecommendation(r) {
  const rec = r.recomendacion;
  const highlights = rec.destacados.map(t => `<li>${escapeHTML(t)}</li>`).join("");
  byId("recommendationBody").innerHTML =
    `<p><strong>${escapeHTML(rec.nombre)}</strong> · ${Math.round(rec.puntaje)}/100</p>` +
    `<p>${escapeHTML(rec.motivo)}</p><div class="compare-item"><ul class="pros">${highlights}</ul></div>` +
    `<p><small>${escapeHTML(r.aviso)}</small></p>`;
}

async function loadAnalysis() {
  setNote("Calculando el análisis de tu terreno…");
  try {
    const result = await analizarTerreno(current);
    paintMetrics(result);
    paintCrops(result);
    paintRotations(result);
    paintComparison(result);
    paintRecommendation(result);
  } catch (error) {
    showUnavailable();
    setNote(error.message, true);
  }
}

saveButton.addEventListener("click", async () => {
  if (!current || current.id) return;
  saveButton.disabled = true;
  saveButton.textContent = "Guardando…";
  try {
    current = await guardarTerreno(current);
    sessionStorage.setItem(DRAFT_KEY, JSON.stringify(current));
    try { history.replaceState(null, "", `analisis.html?id=${encodeURIComponent(current.id)}`); } catch { /* file:// */ }
    markSaved();
  } catch (error) {
    saveButton.disabled = false;
    saveButton.textContent = "Guardar terreno ✓";
    setNote(error.message, true);
  }
});

async function init() {
  if (selectedId) {
    try { current = await obtenerTerreno(selectedId); }
    catch (error) { showNoTerrain(error.message); return; }
  } else {
    try { current = JSON.parse(sessionStorage.getItem(DRAFT_KEY) || "null"); }
    catch { current = null; }
  }
  if (!current) { showNoTerrain(); return; }

  farmTitle.textContent = current.farmName || "Tu parcela";
  const details = [current.location, current.farmerName ? `Agricultor: ${current.farmerName}` : "", current.analysisDate ? `Fecha: ${current.analysisDate}` : ""].filter(Boolean);
  resultSubtitle.textContent = details.join(" · ");
  if (current.id) markSaved();
  await loadAnalysis();
}
init();
