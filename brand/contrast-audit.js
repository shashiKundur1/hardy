const parse = (value) => (value.match(/[\d.]+/g) || []).map(Number);

const luminance = (rgb) => {
  const [r, g, b] = rgb.slice(0, 3).map((channel) => {
    const v = channel / 255;
    return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
  });
  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
};

const opaqueBackground = (element) => {
  let node = element;
  while (node && node.nodeType === 1) {
    const parts = parse(getComputedStyle(node).backgroundColor);
    if (parts.length && (parts.length < 4 || parts[3] > 0.9)) return parts;
    node = node.parentElement;
  }
  return parse(getComputedStyle(document.body).backgroundColor);
};

const contrast = (foreground, background) => {
  const [light, dark] = [luminance(foreground), luminance(background)].sort((a, b) => b - a);
  return (light + 0.05) / (dark + 0.05);
};

window.hardyContrastAudit = () => {
  const measured = new Map();
  document.querySelectorAll("body *").forEach((element) => {
    let own = "";
    element.childNodes.forEach((node) => {
      if (node.nodeType === 3) own += node.textContent.trim();
    });
    if (!own || element.closest(".skip")) return;
    const styles = getComputedStyle(element);
    if (styles.visibility === "hidden" || styles.display === "none") return;
    const size = parseFloat(styles.fontSize);
    const weight = parseInt(styles.fontWeight, 10) || 400;
    const large = size >= 24 || (size >= 18.66 && weight >= 700);
    const ratio = contrast(parse(styles.color), opaqueBackground(element));
    const name =
      typeof element.className === "string" && element.className
        ? element.className
        : element.tagName.toLowerCase();
    const key = `${name}|${Math.round(size)}|${weight}`;
    if (measured.has(key)) return;
    measured.set(key, {
      style: name,
      px: Math.round(size * 10) / 10,
      weight,
      ratio: Math.round(ratio * 100) / 100,
      required: large ? 3 : 4.5,
      passes: ratio >= (large ? 3 : 4.5),
      sample: own.slice(0, 24),
    });
  });
  const rows = Array.from(measured.values()).sort((a, b) => a.ratio - b.ratio);
  return { measured: rows.length, failing: rows.filter((row) => !row.passes), rows };
};
