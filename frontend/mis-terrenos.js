const list = document.getElementById("terrainList");
const count = document.getElementById("terrainCount");
const profileName = document.getElementById("profileName");

function formatDate(value) {
  if (!value) return "Sin fecha";
  const date = new Date(`${value}T00:00:00`);
  return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("es-MX", { day:"numeric", month:"long", year:"numeric" }).format(date);
}
let terrains = [];
async function renderTerrains() {
  try {
    terrains = await listarTerrenos();
  } catch (error) {
    list.innerHTML = `<div class="empty-history"><div class="empty-icon">⚠️</div><h3>No se pudieron cargar tus terrenos</h3><p>${escapeHTML(error.message)}</p></div>`;
    return;
  }
  count.textContent = terrains.length;
  profileName.textContent = terrains[0]?.farmerName || "Agricultor";
  if (!terrains.length) {
    list.innerHTML = '<div class="empty-history"><div class="empty-icon">🌾</div><h3>Aún no tienes terrenos guardados</h3><p>Cuando termines un análisis, presiona “Guardar” para agregar la parcela a tu historial.</p><a class="button button-primary" href="registro.html">Registrar mi primer terreno →</a></div>';
    return;
  }
  list.innerHTML = terrains.map(terrain => `
    <article class="terrain-card" data-id="${escapeHTML(terrain.id)}">
      <div class="terrain-card-top"><div class="terrain-symbol">🌿</div><span class="terrain-date">${escapeHTML(formatDate(terrain.analysisDate))}</span></div>
      <h3>${escapeHTML(terrain.farmName || "Terreno sin nombre")}</h3>
      <p class="terrain-location">⌖ ${escapeHTML(terrain.location || "Ubicación no especificada")}</p>
      <div class="terrain-details">
        <div><span>Agricultor</span><strong>${escapeHTML(terrain.farmerName || "No especificado")}</strong></div>
        <div><span>Tipo de suelo</span><strong>${escapeHTML(terrain.soilType || "No especificado")}</strong></div>
        <div><span>Disponibilidad de agua</span><strong>${escapeHTML(terrain.water || "No especificada")}</strong></div>
        <div><span>Historial de cosechas</span><strong>${escapeHTML(terrain.cropHistory || "Sin información")}</strong></div>
      </div>
      <div class="terrain-card-actions"><a class="button button-primary" href="analisis.html?id=${encodeURIComponent(terrain.id)}">Ver análisis →</a><button class="button button-delete" type="button" data-delete="${escapeHTML(terrain.id)}">Eliminar</button></div>
    </article>`).join("");
}
list.addEventListener("click", async event => {
  const button = event.target.closest("[data-delete]");
  if (!button) return;
  const id = button.dataset.delete;
  const terrain = terrains.find(item => item.id === id);
  if (!terrain || !confirm(`¿Quieres eliminar “${terrain.farmName || "este terreno"}” de tu historial? Esta acción no se puede deshacer.`)) return;
  button.disabled = true;
  try {
    await eliminarTerreno(id);
  } catch (error) {
    button.disabled = false;
    alert(error.message);
    return;
  }
  renderTerrains();
});
renderTerrains();
