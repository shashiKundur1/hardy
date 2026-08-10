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

const TYPEAHEAD_RESET_MS = 700;

const buildCombo = (select) => {
  const label = document.querySelector(`label[for="${select.id}"]`);
  if (label && !label.id) label.id = `${select.id}-label`;

  const root = document.createElement("div");
  root.className = "combo";

  const field = document.createElement("button");
  field.type = "button";
  field.className = "combo__field";
  field.id = `${select.id}-combo`;
  field.setAttribute("role", "combobox");
  field.setAttribute("aria-haspopup", "listbox");
  field.setAttribute("aria-expanded", "false");
  field.setAttribute("aria-controls", `${select.id}-listbox`);
  if (label) field.setAttribute("aria-labelledby", `${label.id} ${select.id}-value`);

  const value = document.createElement("span");
  value.className = "combo__value";
  value.id = `${select.id}-value`;

  const caret = document.createElement("span");
  caret.className = "combo__caret";
  caret.setAttribute("aria-hidden", "true");
  field.append(value, caret);

  const list = document.createElement("ul");
  list.className = "combo__list";
  list.id = `${select.id}-listbox`;
  list.setAttribute("role", "listbox");
  if (label) list.setAttribute("aria-labelledby", label.id);
  list.hidden = true;

  const items = Array.from(select.options).map((option, index) => {
    const item = document.createElement("li");
    item.className = "combo__option";
    item.id = `${select.id}-option-${index}`;
    item.setAttribute("role", "option");
    item.dataset.index = String(index);
    item.textContent = option.textContent.trim();
    list.append(item);
    return item;
  });

  root.append(field, list);
  select.after(root);
  select.hidden = true;
  return { label, root, field, value, list, items };
};

const enhanceSelect = (select) => {
  const ui = buildCombo(select);
  let active = Math.max(select.selectedIndex, 0);
  let typed = "";
  let typedAt = 0;

  const paint = () => {
    ui.value.textContent = ui.items[select.selectedIndex]?.textContent ?? "";
    ui.items.forEach((item, index) => {
      item.setAttribute("aria-selected", String(index === select.selectedIndex));
      item.classList.toggle("is-active", index === active);
    });
  };

  const point = () => {
    ui.field.setAttribute("aria-activedescendant", ui.items[active].id);
    ui.items[active].scrollIntoView({ block: "nearest" });
  };

  const isOpen = () => !ui.list.hidden;

  const open = () => {
    ui.list.hidden = false;
    ui.field.setAttribute("aria-expanded", "true");
    active = Math.max(select.selectedIndex, 0);
    paint();
    point();
  };

  const shut = () => {
    ui.list.hidden = true;
    ui.field.setAttribute("aria-expanded", "false");
    ui.field.removeAttribute("aria-activedescendant");
  };

  const moveTo = (index) => {
    active = Math.min(Math.max(index, 0), ui.items.length - 1);
    paint();
    point();
  };

  const choose = (index) => {
    select.selectedIndex = index;
    select.dispatchEvent(new Event("change", { bubbles: true }));
    active = index;
    paint();
  };

  const seek = (key) => {
    const now = Date.now();
    typed = now - typedAt > TYPEAHEAD_RESET_MS ? key : typed + key;
    typedAt = now;
    const from = typed.length === 1 ? active + 1 : active;
    for (let step = 0; step < ui.items.length; step += 1) {
      const index = (from + step) % ui.items.length;
      if (ui.items[index].textContent.toLowerCase().startsWith(typed.toLowerCase())) {
        if (isOpen()) moveTo(index);
        else choose(index);
        return;
      }
    }
  };

  ui.field.addEventListener("click", () => (isOpen() ? shut() : open()));

  ui.field.addEventListener("keydown", (event) => {
    const { key, altKey } = event;
    if (key.length === 1 && key !== " " && !event.ctrlKey && !event.metaKey && !altKey) {
      if (!isOpen()) open();
      seek(key);
      event.preventDefault();
      return;
    }
    if (!isOpen()) {
      if (key === "ArrowDown" || key === "ArrowUp" || key === "Enter" || key === " ") {
        open();
        if (key === "ArrowUp") moveTo(ui.items.length - 1);
        event.preventDefault();
      }
      return;
    }
    if (key === "ArrowDown") moveTo(active + 1);
    else if (key === "ArrowUp") moveTo(active - 1);
    else if (key === "Home") moveTo(0);
    else if (key === "End") moveTo(ui.items.length - 1);
    else if (key === "PageDown") moveTo(active + 10);
    else if (key === "PageUp") moveTo(active - 10);
    else if (key === "Escape") shut();
    else if (key === "Enter" || key === " " || (key === "ArrowUp" && altKey)) {
      choose(active);
      shut();
    } else if (key === "Tab") {
      choose(active);
      shut();
      return;
    } else return;
    event.preventDefault();
  });

  ui.field.addEventListener("blur", () => {
    if (isOpen()) shut();
  });

  ui.list.addEventListener("mousedown", (event) => {
    const item = event.target.closest(".combo__option");
    if (!item) return;
    event.preventDefault();
    choose(Number(item.dataset.index));
    shut();
    ui.field.focus();
  });

  if (ui.label) {
    ui.label.addEventListener("click", (event) => {
      event.preventDefault();
      ui.field.focus();
    });
  }

  select.addEventListener("change", paint);
  paint();
};

document.querySelectorAll("select.input").forEach(enhanceSelect);
