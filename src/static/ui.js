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
