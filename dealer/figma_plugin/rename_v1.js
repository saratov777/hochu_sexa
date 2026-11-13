// 1) Exports brand-coloured copies of the two wireframes (temporary clones, deleted afterwards).
// 2) Renames every layer on every page to generic names. Pages, content and appearance are untouched.
const UPLOAD = "https://beautiful-amp-catch-resources.trycloudflare.com";
const TOKEN = "__TOKEN__";
const B = { white: "#FFFFFF", soft: "#F1F4F8", photo: "#E3E8EF", line: "#D3DAE3", text: "#17202C", accent: "#1A56DB" };

function rgb(hex) { const n = parseInt(hex.slice(1), 16); return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 }; }
function hexOf(paints) {
  if (!Array.isArray(paints) || !paints.length || paints[0].type !== "SOLID") return null;
  const c = paints[0].color, h = v => Math.round(v * 255).toString(16).padStart(2, "0");
  return ("#" + h(c.r) + h(c.g) + h(c.b)).toUpperCase();
}
const solid = (hex, op) => [{ type: "SOLID", color: rgb(hex), opacity: op === undefined ? 1 : op }];

// ---------------------------------------------------------------- recolour a clone
function recolor(root) {
  const all = root.findAll(() => true);
  for (const n of all) {
    const anc = []; for (let p = n.parent; p && p !== root; p = p.parent) anc.push(p.name || "");
    const inLogo = anc.some(a => a === "Изображение / Логотип");
    const inOutlineBtn = anc.some(a => a.startsWith("Кнопка /")) && n.parent.children.some(c => c.type === "RECTANGLE" && hexOf(c.strokes) === "#212121" && hexOf(c.fills) === "#FFFFFF");
    if (n.type === "TEXT") {
      const h = hexOf(n.fills);
      if (inLogo) n.fills = solid(B.white);
      else if (h === "#212121") {
        const link = /→$/.test(n.characters) || n.characters === "Сбросить фильтры";
        const activeNav = n.characters === "Каталог" && anc.some(a => a.startsWith("Шапка")) && n.fontName.style === "Bold";
        n.fills = solid(link || activeNav || inOutlineBtn ? B.accent : B.text);
      } else if (h === "#757575") n.fills = solid(B.text, 0.68);
      continue;
    }
    if (!("fills" in n)) continue;
    const f = hexOf(n.fills), s = hexOf(n.strokes);
    if (inLogo) {
      if (n.type === "VECTOR") n.strokes = solid(B.white, 0.35); else { n.fills = solid(B.accent); n.strokes = []; }
      continue;
    }
    if (n.type === "ELLIPSE") { n.fills = solid(B.accent); n.strokes = []; continue; }
    if (n.type === "VECTOR") { n.strokes = solid(B.line); continue; }
    if (f === "#212121") n.fills = solid(B.accent);          // filled buttons, active chips, checks, active menu bar
    else if (f === "#F2F2F2") n.fills = solid(B.soft);
    else if (f === "#E0E0E0") n.fills = solid(B.photo);
    else if (f === "#757575") n.fills = solid(B.text);       // footer
    else if (f === "#9E9E9E") n.fills = solid(B.line);       // header divider
    if (s === "#9E9E9E") n.strokes = solid(B.line);
    else if (s === "#212121") n.strokes = solid(f === "#212121" ? B.accent : (n.width <= 24 ? B.line : B.accent));
  }
}

// ---------------------------------------------------------------- snapshot of visible content
function snap(page) {
  const out = [];
  page.findAll(() => true).forEach(n => {
    const r = [n.type, n.id, Math.round(n.x * 10), Math.round(n.y * 10), Math.round(n.width * 10), Math.round(n.height * 10), n.visible, n.opacity];
    if ("fills" in n) r.push(JSON.stringify(n.fills));
    if ("strokes" in n) r.push(JSON.stringify(n.strokes));
    if (n.type === "TEXT") r.push(n.characters, JSON.stringify(n.fontName), n.fontSize);
    if ("reactions" in n) r.push(JSON.stringify(n.reactions));
    out.push(r.join("|"));
  });
  return out;
}

const KIND = { FRAME: "Frame", GROUP: "Group", RECTANGLE: "Rectangle", TEXT: "Text", ELLIPSE: "Ellipse", LINE: "Line", COMPONENT: "Component", INSTANCE: "Instance", POLYGON: "Polygon", STAR: "Star", BOOLEAN_OPERATION: "Boolean", SECTION: "Section" };
function kindOf(n) {
  if (n.type === "VECTOR") {
    const d = (n.vectorPaths && n.vectorPaths[0] && n.vectorPaths[0].data) || "";
    return (d.match(/[A-Za-z]/g) || []).length === 2 ? "Line" : "Vector";
  }
  return KIND[n.type] || "Layer";
}

async function main() {
  for (const s of ["Regular", "Medium", "Semi Bold", "Bold"]) await figma.loadFontAsync({ family: "Inter", style: s });
  await figma.loadAllPagesAsync();
  const pages = figma.root.children.slice();
  const report = { pages: pages.map(p => p.name) };

  // 1. coloured wireframe exports
  const wf = pages.find(p => p.name === "Схемы страниц (вайрфреймы)");
  await figma.setCurrentPageAsync(wf);
  const files = [];
  const srcFrames = wf.children.filter(n => n.type === "FRAME").sort((a, b) => a.x - b.x);
  const before = {}; for (const p of pages) before[p.id] = snap(p);
  for (const [fr, name] of [[srcFrames[0], "wf_home_color.png"], [srcFrames[1], "wf_catalog_color.png"]]) {
    const c = fr.clone(); c.x = -20000; c.y = 0;
    recolor(c);
    files.push({ name, bytes: await c.exportAsync({ format: "PNG", constraint: { type: "SCALE", value: 2 } }) });
    c.remove();
  }
  report.wireframeFrames = srcFrames.map(f => f.name);

  // 2. rename
  report.renamed = {};
  for (const p of pages) {
    const cnt = {};
    const next = k => (cnt[k] = (cnt[k] || 0) + 1, k + " " + cnt[k]);
    const tops = p.children.slice().sort((a, b) => (a.y - b.y) || (a.x - b.x));
    const walk = n => { n.name = next(kindOf(n)); if ("children" in n) n.children.forEach(walk); };
    tops.forEach(walk);
    report.renamed[p.name] = cnt;
  }

  // 3. verify nothing visible changed
  report.unchanged = {};
  for (const p of pages) {
    const a = before[p.id], b = snap(p);
    report.unchanged[p.name] = a.length === b.length && a.every((v, i) => v === b[i]) ? "OK (" + b.length + " слоёв)" : "ИЗМЕНЕНО";
  }
  report.badNames = [];
  for (const p of pages) p.findAll(n => !/^(Frame|Group|Rectangle|Text|Ellipse|Line|Vector|Component|Instance|Polygon|Star|Boolean|Section|Layer) \d+$/.test(n.name)).slice(0, 5).forEach(n => report.badNames.push(n.name));
  report.pagesAfter = figma.root.children.map(p => p.name);
  const proto = pages.find(p => p.name.startsWith("Прототип"));
  report.flow = proto.flowStartingPoints;
  report.reactions = proto.findAll(n => "reactions" in n && n.reactions.length > 0).length;
  report.topFrames = {}; for (const p of pages) report.topFrames[p.name] = p.children.map(n => n.name);
  report.leftovers = wf.children.filter(n => n.x <= -20000).length;

  const json = new TextEncoder().encode(JSON.stringify(report, null, 1));
  files.push({ name: "rename_report.json", bytes: json });
  figma.showUI(`<script>
    onmessage = async (e) => {
      const out = [];
      for (const f of e.data.pluginMessage.files) {
        try { const r = await fetch("${UPLOAD}/" + f.name + "?t=${TOKEN}", { method: "POST", body: new Blob([f.bytes]) }); out.push(f.name + ":" + r.status); }
        catch (err) { out.push(f.name + ":" + err); }
      }
      parent.postMessage({ pluginMessage: out.join(" ") }, "*");
    };
  </script>`, { visible: false });
  figma.ui.onmessage = msg => { figma.notify("Готово. " + msg, { timeout: 20000 }); figma.closePlugin(); };
  figma.ui.postMessage({ files });
}
main().catch(e => { figma.notify("Ошибка: " + e.message, { error: true, timeout: 30000 }); figma.closePlugin(); });
