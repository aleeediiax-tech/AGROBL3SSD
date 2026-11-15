const form = document.getElementById("farmForm");
const formMessage = document.getElementById("formMessage");
const locationInput = document.getElementById("locationInput");
const latInput = document.getElementById("latInput");
const lonInput = document.getElementById("lonInput");
const mapFrame = document.getElementById("mapFrame");
const map = L.map("map").setView([19.0414, -98.2063], 9);
document.getElementById("analysisDate").value = new Date().toISOString().slice(0, 10);

let marker = null;

function showMap(query, zoom = 13) {
  mapFrame.src = `https://maps.google.com/maps?q=${encodeURIComponent(query)}&t=&z=${zoom}&ie=UTF8&iwloc=&output=embed`;
}

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap"
}).addTo(map);

async function updateMap() {
  const found = await geocodificar(place);

  seleccionarPunto(found.lat, found.lon);

  formMessage.textContent = "Ubicación encontrada. Verifica que corresponda a tu terreno.";
  try {
    const found = await geocodificar(place);
    latInput.value = found.lat.toFixed(5);
    lonInput.value = found.lon.toFixed(5);
    showMap(`${found.lat},${found.lon}`, 14);
    formMessage.textContent = "Coordenadas encontradas. Verifica que el lugar mostrado corresponda a tu terreno.";
  } catch (error) {
    formMessage.textContent = `${error.message} Escribe la latitud y la longitud manualmente.`;
  }
}
document.getElementById("searchLocation").addEventListener("click", updateMap);
locationInput.addEventListener("keydown", event => {
  if (event.key === "Enter") { event.preventDefault(); updateMap(); }
});

// Si el usuario corrige las coordenadas a mano, el mapa las sigue.
function followCoordinates() {
  const lat = parseFloat(latInput.value), lon = parseFloat(lonInput.value);
  if (Number.isFinite(lat) && Number.isFinite(lon)) showMap(`${lat},${lon}`, 14);
}
latInput.addEventListener("change", followCoordinates);
lonInput.addEventListener("change", followCoordinates);

form.addEventListener("submit", event => {
  event.preventDefault();
  if (!form.reportValidity()) return;
  const data = Object.fromEntries(new FormData(form).entries());
  data.lat = Number(data.lat);
  data.lon = Number(data.lon);
  // El id lo asigna el backend al guardar; aquí solo se pasa el borrador al análisis.
  sessionStorage.setItem("agrobl3ssedCurrentTerrain", JSON.stringify(data));
  window.location.href = "analisis.html";
});

function seleccionarPunto(lat, lon) {

    latInput.value = lat.toFixed(6);
    lonInput.value = lon.toFixed(6);

    if (marker) {
        map.removeLayer(marker);
    }

    marker = L.marker([lat, lon]).addTo(map);

    marker.bindPopup("Ubicación seleccionada").openPopup();

    map.setView([lat, lon], 15);
}

map.on("click", function(event) {

    const lat = event.latlng.lat;
    const lon = event.latlng.lng;

    seleccionarPunto(lat, lon);

    locationInput.value = "Punto seleccionado en el mapa";

    formMessage.textContent = "Ubicación seleccionada correctamente.";

});

document.getElementById("getLocation").addEventListener("click", function() {

    if (!navigator.geolocation) {
        formMessage.textContent = "Tu navegador no soporta geolocalización.";
        return;
    }

    formMessage.textContent = "Obteniendo tu ubicación...";

    navigator.geolocation.getCurrentPosition(

        function(position) {

            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            seleccionarPunto(lat, lon);

            locationInput.value = "Mi ubicación actual";

            formMessage.textContent = "Ubicación obtenida correctamente.";

        },

        function(error) {

            formMessage.textContent =
                "No fue posible obtener tu ubicación. Verifica los permisos del navegador.";

        },

        {
            enableHighAccuracy: true,
            timeout: 10000
        }

    );

});