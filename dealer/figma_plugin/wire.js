// АвтоЯсно — grayscale wireframes of the homepage and catalog on their own page.
// Existing pages (prototype, Brand Book) are not touched.
const UPLOAD = "https://beautiful-amp-catch-resources.trycloudflare.com";
const TOKEN = "__TOKEN__";
const G = { bg: "#FFFFFF", fill: "#F2F2F2", mid: "#E0E0E0", line: "#9E9E9E", soft: "#757575", ink: "#212121" };
const W = 1200;

function rgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 };
}
const fill = hex => [{ type: "SOLID", color: rgb(hex) }];
const STYLE = { 400: "Regular", 500: "Medium", 600: "Semi Bold", 700: "Bold" };

function box(p, x, y, w, h, o) {
  o = o || {};
  const r = figma.createRectangle();
  r.x = x; r.y = y; r.resize(w, h);
  r.fills = o.fill === null ? [] : fill(o.fill || G.fill);
  if (o.stroke !== false) { r.strokes = fill(o.stroke || G.line); r.strokeWeight = o.sw || 1.5; }
  if (o.dash) r.dashPattern = [8, 6];
  r.cornerRadius = o.r === undefined ? 6 : o.r;
  r.name = o.name || "Блок";
  p.appendChild(r);
  return r;
}
function txt(p, x, y, s, size, weight, color, name) {
  const t = figma.createText();
  t.fontName = { family: "Inter", style: STYLE[weight || 400] };
  t.characters = s; t.fontSize = size; t.fills = fill(color || G.ink);
  t.x = x; t.y = y; t.name = name || s;
  p.appendChild(t);
  return t;
}
function grp(p, nodes, name) { const g = figma.group(nodes, p); g.name = name; return g; }
// image placeholder: box with a diagonal cross and a centred caption
function ph(p, x, y, w, h, label) {
  const n = [box(p, x, y, w, h, { fill: G.mid, name: "Заглушка" })];
  for (const [ax, ay, bx, by] of [[x, y, x + w, y + h], [x + w, y, x, y + h]]) {
    const v = figma.createVector();
    v.vectorPaths = [{ windingRule: "NONE", data: `M ${ax} ${ay} L ${bx} ${by}` }];
    v.strokes = fill(G.line); v.strokeWeight = 1.2; v.name = "Диагональ";
    p.appendChild(v); n.push(v);
  }
  const t = txt(p, 0, 0, label, 17, 500, G.ink);
  const pad = box(p, 0, 0, t.width + 20, t.height + 10, { fill: G.mid, stroke: false, r: 4 });
  pad.x = x + (w - pad.width) / 2; pad.y = y + (h - pad.height) / 2;
  p.appendChild(t); t.x = pad.x + 10; t.y = pad.y + 5;
  n.push(pad, t);
  return grp(p, n, "Изображение / " + label);
}
function btn(p, x, y, w, h, label, filled) {
  const r = box(p, x, y, w, h, { fill: filled ? G.ink : G.bg, stroke: filled ? false : G.ink, r: 6 });
  const t = txt(p, 0, 0, label, 17, 600, filled ? "#FFFFFF" : G.ink);
  t.x = x + (w - t.width) / 2; t.y = y + (h - t.height) / 2;
  return grp(p, [r, t], "Кнопка / " + label);
}
function fld(p, x, y, w, label, h) {
  const r = box(p, x, y, w, h || 48, { fill: G.bg });
  const t = txt(p, x + 14, y + ((h || 48) - 21) / 2, label, 17, 400, G.soft);
  return grp(p, [r, t], "Поле / " + label);
}
function chip(p, x, y, label, on) {
  const t = txt(p, 0, 0, label, 15, 500, on ? "#FFFFFF" : G.ink);
  const r = box(p, x, y, t.width + 24, 36, { fill: on ? G.ink : G.bg, stroke: on ? false : G.line, r: 18 });
  p.appendChild(t); t.x = x + 12; t.y = y + (36 - t.height) / 2;
  return { node: grp(p, [r, t], "Чип / " + label), w: t.width + 24 };
}
function check(p, x, y, label, on) {
  const r = box(p, x, y, 20, 20, { fill: on ? G.ink : G.bg, stroke: G.ink, r: 3 });
  return grp(p, [r, txt(p, x + 30, y - 1, label, 17, 400, G.ink)], "Чекбокс / " + label);
}
function bar(p, x, y, w) { return box(p, x, y, w, 12, { fill: G.mid, stroke: false, r: 6, name: "Строка текста" }); }

function header(f, active) {
  const n = [box(f, 0, 0, W, 72, { fill: G.bg, stroke: false, r: 0, name: "Фон шапки" }), box(f, 0, 71, W, 1, { fill: G.line, stroke: false, r: 0 })];
  n.push(ph(f, 40, 14, 150, 44, "Логотип"));
  let x = 222;
  for (const item of ["Каталог", "Сравнение", "Кредит", "Трейд-ин", "Тест-драйв", "Контакты"]) {
    const t = txt(f, x, 25, item, 17, item === active ? 700 : 400, G.ink); n.push(t);
    if (item === active) n.push(box(f, x, 66, t.width, 4, { fill: G.ink, stroke: false, r: 0 }));
    x += t.width + 22;
  }
  n.push(txt(f, 900, 25, "Телефон", 17, 600, G.ink));
  n.push(btn(f, 1060, 16, 100, 40, "Войти", false));
  return grp(f, n, "Шапка: логотип, меню, телефон, вход");
}
function card(f, x, y, w, h, i) {
  const n = [box(f, x, y, w, h, { fill: G.bg })];
  n.push(ph(f, x + 12, y + 12, w - 24, Math.round(h * 0.4), "Фото"));
  const ty = y + 24 + Math.round(h * 0.4);
  n.push(txt(f, x + 16, ty, "Марка, модель, год", 18, 600, G.ink));
  n.push(bar(f, x + 16, ty + 34, w - 80));
  n.push(txt(f, x + 16, ty + 58, "Цена, ₽", 20, 700, G.ink));
  n.push(txt(f, x + 16, ty + 88, "Платёж в месяц", 16, 400, G.soft));
  n.push(btn(f, x + 16, y + h - 56, w - 32, 42, "Подробнее", true));
  return grp(f, n, "Карточка автомобиля " + i);
}
function frame(name, x, h) {
  const f = figma.createFrame();
  f.name = name; f.x = x; f.y = 0; f.resize(W, h); f.fills = fill(G.bg);
  figma.currentPage.appendChild(f);
  return f;
}

function buildHome() {
  const f = frame("Схема 1 — Главная страница", 0, 1184);
  header(f);
  // hero
  const hero = [txt(f, 40, 112, "Новые и подержанные автомобили\nс честной итоговой ценой", 30, 700, G.ink, "Заголовок H1")];
  hero.push(bar(f, 40, 220, 480), bar(f, 40, 244, 400));
  hero.push(btn(f, 40, 286, 220, 52, "Смотреть каталог", true), btn(f, 276, 286, 290, 52, "Записаться на тест-драйв", false));
  hero.push(ph(f, 660, 100, 500, 300, "Фото автомобиля / салона"));
  grp(f, hero, "Первый экран");
  // quick search
  const qs = [box(f, 40, 428, 1120, 144, { fill: G.fill, name: "Фон блока" }), txt(f, 64, 448, "Быстрый подбор", 21, 700, G.ink)];
  let cx = 260;
  for (const [l, on] of [["Все", true], ["Новые", false], ["С пробегом", false]]) { const c = chip(f, cx, 444, l, on); qs.push(c.node); cx += c.w + 10; }
  ["Марка ▾", "Модель ▾", "Кузов ▾", "Цена до ▾"].forEach((l, i) => qs.push(fld(f, 64 + i * 226, 500, 210, l)));
  qs.push(btn(f, 968, 500, 168, 48, "Показать", true));
  grp(f, qs, "Быстрый подбор");
  // inventory
  const inv = [txt(f, 40, 600, "Автомобили в наличии", 26, 700, G.ink), txt(f, 1020, 608, "Весь каталог →", 18, 600, G.ink)];
  for (let i = 0; i < 4; i++) inv.push(card(f, 40 + i * 285, 652, 265, 330, i + 1));
  grp(f, inv, "Автомобили в наличии");
  // benefits
  const ben = [];
  ["Итоговая цена", "Тест-драйв", "Кредит", "Трейд-ин"].forEach((l, i) => {
    const x = 40 + i * 285;
    const c = figma.createEllipse(); c.resize(48, 48); c.x = x; c.y = 1006; c.fills = fill(G.mid); c.strokes = fill(G.line); c.name = "Иконка"; f.appendChild(c);
    ben.push(c, txt(f, x + 62, 1006, l, 19, 600, G.ink), bar(f, x + 62, 1038, 170));
  });
  grp(f, ben, "Преимущества");
  const ft = [box(f, 0, 1088, W, 96, { fill: G.soft, stroke: false, r: 0 }), txt(f, 40, 1124, "Подвал: адрес, телефон, часы работы, карта, соцсети", 18, 500, "#FFFFFF")];
  grp(f, ft, "Подвал");
  return f;
}

function buildCatalog() {
  const f = frame("Схема 2 — Каталог автомобилей", W + 160, 1100);
  header(f, "Каталог");
  const top = [txt(f, 40, 92, "Главная / Каталог", 16, 400, G.soft), txt(f, 40, 118, "Каталог автомобилей", 30, 700, G.ink)]; top.push(txt(f, 40 + top[1].width + 16, 128, "64 автомобиля", 18, 400, G.soft));
  top.push(fld(f, 350, 172, 510, "Поиск по марке или модели"), fld(f, 880, 172, 280, "Сортировка ▾"));
  grp(f, top, "Заголовок, поиск и сортировка");
  // filters
  const fp = [box(f, 40, 172, 280, 900, { fill: G.fill, name: "Фон панели" }), txt(f, 60, 190, "Фильтры", 21, 700, G.ink)];
  fp.push(txt(f, 60, 230, "Состояние", 16, 600, G.ink));
  let cx = 60;
  for (const [l, on] of [["Все", true], ["Новые", false], ["С пробегом", false]]) { const c = chip(f, cx, 254, l, on); fp.push(c.node); cx += c.w + 6; }
  fp.push(fld(f, 60, 310, 240, "Марка ▾"), fld(f, 60, 370, 240, "Модель ▾"));
  fp.push(txt(f, 60, 436, "Цена, ₽", 16, 600, G.ink), fld(f, 60, 460, 112, "от"), fld(f, 188, 460, 112, "до"));
  fp.push(txt(f, 60, 526, "Кузов", 16, 600, G.ink));
  ["Седан", "Кроссовер", "Хэтчбек", "Универсал"].forEach((l, i) => fp.push(check(f, 60, 554 + i * 32, l, i < 2)));
  fp.push(txt(f, 60, 690, "Коробка передач", 16, 600, G.ink));
  ["Автомат", "Робот", "Механика"].forEach((l, i) => fp.push(check(f, 60, 718 + i * 32, l, false)));
  fp.push(fld(f, 60, 822, 240, "Привод ▾"), fld(f, 60, 882, 240, "Год выпуска ▾"));
  fp.push(btn(f, 60, 956, 240, 48, "Показать 64", true), txt(f, 112, 1024, "Сбросить фильтры", 17, 600, G.ink));
  grp(f, fp, "Панель фильтров");
  // active filters
  const af = [txt(f, 350, 240, "Выбрано:", 17, 400, G.soft)];
  cx = 440;
  for (const l of ["Седан ×", "Кроссовер ×", "до 5 млн ₽ ×"]) { const c = chip(f, cx, 234, l, false); af.push(c.node); cx += c.w + 8; }
  grp(f, af, "Активные фильтры");
  // grid
  const grid = [];
  for (let i = 0; i < 6; i++) grid.push(card(f, 350 + (i % 3) * 276, 290 + Math.floor(i / 3) * 372, 256, 352, i + 1));
  grp(f, grid, "Сетка карточек 3 × 2");
  const pg = []; let px = 600;
  for (const l of ["‹", "1", "2", "3", "…", "11", "›"]) { const c = chip(f, px, 1036, l, l === "1"); pg.push(c.node); px += c.w + 8; }
  grp(f, pg, "Пагинация");
  return f;
}

async function main() {
  for (const s of ["Regular", "Medium", "Semi Bold", "Bold"]) await figma.loadFontAsync({ family: "Inter", style: s });
  let page = figma.root.children.find(p => p.name === "Схемы страниц (вайрфреймы)");
  if (!page) { page = figma.createPage(); page.name = "Схемы страниц (вайрфреймы)"; }
  await figma.setCurrentPageAsync(page);
  for (const n of page.children.slice()) n.remove();
  const home = buildHome(), cat = buildCatalog();
  figma.viewport.scrollAndZoomIntoView([home, cat]);
  // export the real frames and hand them to a hidden UI that uploads them
  const files = [];
  for (const [fr, name] of [[home, "wf_home.png"], [cat, "wf_catalog.png"]]) {
    files.push({ name, bytes: await fr.exportAsync({ format: "PNG", constraint: { type: "SCALE", value: 2 } }) });
  }
  figma.showUI(`<script>
    onmessage = async (e) => {
      const out = [];
      for (const f of e.data.pluginMessage.files) {
        try {
          const r = await fetch("${UPLOAD}/" + f.name + "?t=${TOKEN}", { method: "POST", body: new Blob([f.bytes]) });
          out.push(f.name + ":" + r.status);
        } catch (err) { out.push(f.name + ":" + err); }
      }
      parent.postMessage({ pluginMessage: out.join(" ") }, "*");
    };
  </script>`, { visible: false });
  figma.ui.onmessage = msg => {
    figma.notify("Схемы созданы. Экспорт: " + msg, { timeout: 20000 });
    figma.closePlugin();
  };
  figma.ui.postMessage({ files });
}
main().catch(e => { figma.notify("Ошибка: " + e.message, { error: true, timeout: 20000 }); figma.closePlugin(); });
