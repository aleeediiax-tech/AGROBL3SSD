const root = document.documentElement;
document.getElementById("increaseText")?.addEventListener("click", () => {
  const current = Number(getComputedStyle(root).getPropertyValue("--font-scale").trim()) || 1;
  root.style.setProperty("--font-scale", Math.min(1.3, +(current + 0.1).toFixed(2)));
});
document.getElementById("decreaseText")?.addEventListener("click", () => {
  const current = Number(getComputedStyle(root).getPropertyValue("--font-scale").trim()) || 1;
  root.style.setProperty("--font-scale", Math.max(0.85, +(current - 0.1).toFixed(2)));
});
document.getElementById("contrastToggle")?.addEventListener("click", (event) => {
  const enabled = document.body.classList.toggle("high-contrast");
  event.currentTarget.setAttribute("aria-pressed", String(enabled));
  event.currentTarget.innerHTML = enabled ? "◑ <span>Contraste alto</span>" : "◐ <span>Contraste</span>";
});
const menuToggle = document.getElementById("menuToggle");
menuToggle?.addEventListener("click", () => {
  const nav = document.getElementById("mainNav");
  const opened = nav.classList.toggle("open");
  menuToggle.setAttribute("aria-expanded", String(opened));
  menuToggle.setAttribute("aria-label", opened ? "Cerrar menú" : "Abrir menú");
});
document.querySelectorAll(".desktop-nav a").forEach(link => link.addEventListener("click", () => {
  document.getElementById("mainNav")?.classList.remove("open");
  menuToggle?.setAttribute("aria-expanded", "false");
}));
