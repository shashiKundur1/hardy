const showShot = (thumb) => {
  const hero = document.getElementById("gallery-hero");
  if (!hero || !thumb) return;
  hero.src = thumb.dataset.shot;
  hero.alt = thumb.dataset.alt;
  document
    .querySelectorAll(".gallery__thumb")
    .forEach((other) => other.setAttribute("aria-pressed", String(other === thumb)));
};

document.addEventListener("click", (event) => {
  const thumb = event.target.closest(".gallery__thumb");
  if (thumb) showShot(thumb);
});

document.addEventListener("keydown", (event) => {
  const thumb = event.target.closest(".gallery__thumb");
  if (thumb && (event.key === "ArrowRight" || event.key === "ArrowLeft")) {
    const thumbs = Array.from(document.querySelectorAll(".gallery__thumb"));
    const step = event.key === "ArrowRight" ? 1 : -1;
    const next = thumbs[(thumbs.indexOf(thumb) + step + thumbs.length) % thumbs.length];
    next.focus();
    showShot(next);
    event.preventDefault();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const open = document.querySelector("details.menu[open]");
  if (!open) return;
  open.removeAttribute("open");
  open.querySelector("summary").focus();
});

document.addEventListener("click", (event) => {
  const toggle = event.target.closest("[data-reveal]");
  if (toggle) {
    const input = document.getElementById(toggle.dataset.reveal);
    if (!input) return;
    const shown = input.type === "text";
    input.type = shown ? "password" : "text";
    toggle.setAttribute("aria-pressed", String(!shown));
    const label = toggle.querySelector(".reveal__label");
    if (label) label.textContent = shown ? "Show" : "Hide";
    return;
  }
  document.querySelectorAll("details.menu[open]").forEach((menu) => {
    if (!menu.contains(event.target)) menu.removeAttribute("open");
  });
});

document.addEventListener("click", (event) => {
  const step = event.target.closest("[data-quantity]");
  if (!step) return;
  const field = step.parentElement.querySelector(".counter__field");
  if (!field) return;
  const low = Number(field.min) || 1;
  const high = Number(field.max) || 10;
  const next = Number(field.value) + Number(step.dataset.quantity);
  field.value = Math.min(high, Math.max(low, next));
  step.parentElement
    .querySelectorAll("[data-quantity]")
    .forEach((other) => {
      const bound = Number(other.dataset.quantity) < 0 ? low : high;
      other.disabled = Number(field.value) === bound;
    });
});
