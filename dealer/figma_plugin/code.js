// АвтоЯсно — draws the schematic website prototype as editable Figma layers.
// Private development plugin; it only creates nodes in the open file.
const C = {
  bg: "#FFFFFF", text: "#17202C", soft: "#F1F4F8", accent: "#1A56DB", line: "#D3DAE3",
};
const W = 1440;

function rgb(hex) {
  const n = parseInt(hex.slice(1), 16);
  return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 };
}
function fill(hex, opacity) {
  return [{ type: "SOLID", color: rgb(hex), opacity: opacity === undefined ? 1 : opacity }];
}
const STYLE = { 400: "Regular", 500: "Medium", 600: "Semi Bold", 700: "Bold" };

function rect(p, x, y, w, h, color, o) {
  o = o || {};
  const r = figma.createRectangle();
  r.x = x; r.y = y; r.resize(w, h);
  r.fills = color ? fill(color) : [];
  if (o.r) r.cornerRadius = o.r;
  if (o.stroke) { r.strokes = fill(o.stroke); r.strokeWeight = o.sw || 1; }
  if (o.name) r.name = o.name;
  p.appendChild(r);
  return r;
}
function text(p, x, y, s, size, weight, color, o) {
  o = o || {};
  const t = figma.createText();
  t.fontName = { family: "Inter", style: STYLE[weight || 400] };
  t.characters = s;
  t.fontSize = size;
  t.fills = fill(color || C.text, o.op);
  if (o.lh) t.lineHeight = { value: o.lh, unit: "PIXELS" };
  if (o.w) { t.textAutoResize = "HEIGHT"; t.resize(o.w, t.height); }
  if (o.align) t.textAlignHorizontal = o.align;
  t.x = x; t.y = y;
  if (o.name) t.name = o.name;
  p.appendChild(t);
  return t;
}
const muted = (p, x, y, s, size, o) => text(p, x, y, s, size, 400, C.text, Object.assign({ op: 0.68 }, o || {}));

function group(p, nodes, name) {
  const g = figma.group(nodes, p);
  g.name = name;
  return g;
}
// button: kind = primary | secondary | ghost
function button(p, x, y, w, h, label, kind, name) {
  const b = figma.createFrame();
  b.name = name || "Кнопка / " + label;
  b.x = x; b.y = y; b.resize(w, h);
  b.cornerRadius = 10;
  b.fills = kind === "primary" ? fill(C.accent) : kind === "secondary" ? fill(C.bg) : [];
  if (kind === "secondary") { b.strokes = fill(C.accent); b.strokeWeight = 1.5; }
  const t = figma.createText();
  t.fontName = { family: "Inter", style: "Semi Bold" };
  t.characters = label;
  t.fontSize = h >= 52 ? 17 : 15;
  t.fills = fill(kind === "primary" ? "#FFFFFF" : C.accent);
  b.appendChild(t);
  t.x = Math.round((w - t.width) / 2); t.y = Math.round((h - t.height) / 2);
  p.appendChild(b);
  return b;
}
function field(p, x, y, w, label, placeholder, o) {
  o = o || {};
  const nodes = [];
  if (label) nodes.push(text(p, x, y, label, 14, 500, C.text));
  const fy = label ? y + 24 : y;
  const h = o.h || 48;
  nodes.push(rect(p, x, fy, w, h, C.bg, { r: 10, stroke: C.line }));
  nodes.push(muted(p, x + 16, fy + (h - 20) / 2, placeholder, 15));
  if (o.chevron) nodes.push(muted(p, x + w - 30, fy + (h - 20) / 2, "▾", 15));
  if (o.icon) nodes.push(muted(p, x + w - 34, fy + (h - 20) / 2, o.icon, 15));
  return group(p, nodes, "Поле / " + (label || placeholder));
}
function chip(p, x, y, label, active) {
  const t = figma.createText();
  t.fontName = { family: "Inter", style: "Medium" };
  t.characters = label; t.fontSize = 14;
  t.fills = fill(active ? "#FFFFFF" : C.text);
  const w = t.width + 28;
  const r = rect(p, x, y, w, 34, active ? C.accent : C.soft, { r: 17, stroke: active ? null : C.line });
  p.appendChild(t); t.x = x + 14; t.y = y + 8;
  return { node: group(p, [r, t], "Чип / " + label), w: w };
}
function checkbox(p, x, y, label, checked) {
  const box = rect(p, x, y, 20, 20, checked ? C.accent : C.bg, { r: 5, stroke: checked ? C.accent : C.line, sw: 1.5 });
  const nodes = [box];
  if (checked) nodes.push(text(p, x + 4, y + 1, "✓", 14, 700, "#FFFFFF"));
  nodes.push(text(p, x + 30, y + 1, label, 15, 400, C.text));
  return group(p, nodes, "Чекбокс / " + label);
}
// schematic image placeholder: soft box with a diagonal cross and a caption
function photo(p, x, y, w, h, label) {
  const nodes = [rect(p, x, y, w, h, "#E3E8EF", { r: 12 })];
  for (const [ax, ay, bx, by] of [[x, y, x + w, y + h], [x + w, y, x, y + h]]) {
    const l = figma.createVector();
    l.vectorPaths = [{ windingRule: "NONE", data: `M ${ax} ${ay} L ${bx} ${by}` }];
    l.strokes = fill(C.line); l.strokeWeight = 1;
    p.appendChild(l); nodes.push(l);
  }
  const t = text(p, 0, 0, label || "Фото автомобиля", 13, 500, C.text, { op: 0.55 });
  const pad = rect(p, 0, 0, t.width + 20, 28, "#E3E8EF", { r: 6 });
  pad.x = x + (w - pad.width) / 2; pad.y = y + (h - 28) / 2;
  t.x = pad.x + 10; t.y = pad.y + 6;
  p.appendChild(t);
  nodes.push(pad, t);
  return group(p, nodes, "Изображение / " + (label || "Фото автомобиля"));
}

function logo(p, x, y) {
  const mark = rect(p, x, y, 40, 40, C.accent, { r: 10 });
  const a = text(p, x, y, "А", 22, 700, "#FFFFFF");
  a.x = x + (40 - a.width) / 2; a.y = y + (40 - a.height) / 2;
  const word = text(p, x + 52, y + 7, "АвтоЯсно", 22, 700, C.text);
  return group(p, [mark, a, word], "Логотип «АвтоЯсно»");
}
const NAV = ["Каталог", "Сравнение", "Кредит", "Трейд-ин", "Тест-драйв", "О салоне", "Контакты"];
function header(f, active) {
  const nodes = [rect(f, 0, 0, W, 80, C.bg, { name: "Фон шапки" }), rect(f, 0, 79, W, 1, C.line)];
  nodes.push(logo(f, 80, 20));
  let x = 330;
  for (const item of NAV) {
    const t = text(f, x, 29, item, 16, item === active ? 600 : 500, item === active ? C.accent : C.text);
    nodes.push(t);
    if (item === active) nodes.push(rect(f, x, 76, t.width, 3, C.accent, { r: 2 }));
    x += t.width + 30;
  }
  nodes.push(text(f, 1060, 20, "+7 (495) 000-00-00", 16, 600, C.text));
  nodes.push(muted(f, 1060, 42, "ежедневно 9:00–21:00", 13));
  nodes.push(button(f, 1240, 18, 120, 44, "Войти", "secondary"));
  return group(f, nodes, "Шапка сайта");
}
function crumbs(f, y, parts) {
  return muted(f, 80, y, parts.join("  /  "), 14, { name: "Хлебные крошки" });
}
function frame(name, x, h) {
  const f = figma.createFrame();
  f.name = name; f.x = x; f.y = 0; f.resize(W, h);
  f.fills = fill(C.bg);
  figma.currentPage.appendChild(f);
  return f;
}
function carCard(f, x, y, w, car, o) {
  o = o || {};
  const h = o.compact ? 384 : 412;
  const nodes = [rect(f, x, y, w, h, C.bg, { r: 14, stroke: C.line })];
  nodes.push(photo(f, x + 12, y + 12, w - 24, 168));
  const badge = chip(f, x + 24, y + 24, car.state, false);
  nodes.push(badge.node);
  nodes.push(text(f, x + 20, y + 196, car.name, 18, 600, C.text, { w: w - 40 }));
  nodes.push(muted(f, x + 20, y + 226, car.specs, 14, { w: w - 40, lh: 20 }));
  nodes.push(text(f, x + 20, y + 276, car.price, 22, 700, C.text));
  nodes.push(muted(f, x + 20, y + 306, car.credit, 14));
  nodes.push(button(f, x + 20, y + h - 64, o.compare ? w - 150 : w - 40, 44, "Подробнее", "primary"));
  if (o.compare) nodes.push(checkbox(f, x + w - 118, y + h - 52, "Сравнить", car.cmp));
  return group(f, nodes, "Карточка авто / " + car.name);
}
const CARS = [
  { name: "Haval Jolion, 2024", state: "Новый", specs: "1.5 л, 143 л.с. · Робот · Передний", price: "2 299 000 ₽", credit: "в кредит от 31 900 ₽/мес" },
  { name: "Geely Monjaro, 2024", state: "Новый", specs: "2.0 л, 238 л.с. · Автомат · Полный", price: "4 349 000 ₽", credit: "в кредит от 58 900 ₽/мес", cmp: true },
  { name: "Toyota Camry, 2021", state: "С пробегом", specs: "54 000 км · 2.5 л · Автомат", price: "2 890 000 ₽", credit: "в кредит от 39 800 ₽/мес", cmp: true },
  { name: "Kia Rio, 2020", state: "С пробегом", specs: "71 000 км · 1.6 л · Автомат", price: "1 390 000 ₽", credit: "в кредит от 19 400 ₽/мес" },
  { name: "Chery Tiggo 7 Pro Max", state: "Новый", specs: "1.5 л, 147 л.с. · Вариатор · Передний", price: "2 790 000 ₽", credit: "в кредит от 38 100 ₽/мес" },
  { name: "Skoda Octavia, 2019", state: "С пробегом", specs: "88 000 км · 1.4 л · Робот", price: "1 750 000 ₽", credit: "в кредит от 24 300 ₽/мес" },
];

async function link(node, dest) {
  const r = [{ trigger: { type: "ON_CLICK" }, actions: [{ type: "NODE", destinationId: dest.id, navigation: "NAVIGATE", transition: null, preserveScrollPosition: false }] }];
  try { await node.setReactionsAsync(r); } catch (e) { try { node.reactions = r; } catch (e2) {} }
}

async function main() {
  for (const s of ["Regular", "Medium", "Semi Bold", "Bold"]) await figma.loadFontAsync({ family: "Inter", style: s });
  try { figma.root.name = "АвтоЯсно — прототип сайта автосалона"; } catch (e) {}
  const page = figma.currentPage;
  page.name = "Прототип сайта «АвтоЯсно»";

  // ---------------------------------------------------------------- 1 Главная
  const home = frame("01 Главная", 0, 1240);
  header(home, null);
  rect(home, 0, 80, W, 470, C.soft, { name: "Фон первого экрана" });
  text(home, 80, 140, "Новые и подержанные автомобили\nс честной итоговой ценой", 46, 700, C.text, { lh: 56, name: "Заголовок первого экрана" });
  muted(home, 80, 272, "Цена в каталоге — окончательная: без обязательного допоборудования и скрытых платежей. Подберите автомобиль, сравните варианты и запишитесь на тест-драйв онлайн.", 18, { w: 600, lh: 28 });
  const toCatalog = button(home, 80, 372, 230, 56, "Смотреть каталог", "primary");
  const toDrive = button(home, 326, 372, 270, 56, "Записаться на тест-драйв", "secondary");
  photo(home, 760, 120, 600, 340, "Фото автомобилей в салоне");
  // search panel overlapping the hero
  const s = [rect(home, 80, 470, 1280, 150, C.bg, { r: 16, stroke: C.line, name: "Фон панели поиска" })];
  s.push(text(home, 112, 492, "Быстрый подбор", 20, 600, C.text));
  let cx = 300;
  for (const [lbl, act] of [["Все", true], ["Новые", false], ["С пробегом", false]]) { const c = chip(home, cx, 490, lbl, act); s.push(c.node); cx += c.w + 8; }
  const fw = 230;
  s.push(field(home, 112, 542, fw, null, "Марка", { chevron: true }));
  s.push(field(home, 112 + (fw + 16), 542, fw, null, "Модель", { chevron: true }));
  s.push(field(home, 112 + 2 * (fw + 16), 542, fw, null, "Кузов", { chevron: true }));
  s.push(field(home, 112 + 3 * (fw + 16), 542, fw, null, "Цена до, ₽"));
  const showBtn = button(home, 112 + 4 * (fw + 16), 542, 200, 48, "Показать 248 авто", "primary");
  s.push(showBtn);
  group(home, s, "Панель быстрого поиска");
  text(home, 80, 668, "Автомобили в наличии", 30, 700, C.text);
  text(home, 1210, 678, "Весь каталог →", 17, 600, C.accent);
  let fx = 80; const cards = [];
  for (const car of CARS.slice(0, 4)) { cards.push(carCard(home, fx, 724, 305, car, { compact: true })); fx += 325; }
  const perks = [["₽", "Итоговая цена", "без обязательных допов"], ["⚑", "Тест-драйв", "в удобный день и время"], ["%", "Кредит и рассрочка", "расчёт платежа онлайн"], ["⇄", "Трейд-ин", "оценка вашего авто за 1 день"]];
  let px = 80;
  for (const [ic, a, b] of perks) {
    const n = [rect(home, px, 1138, 52, 52, C.soft, { r: 12 }), text(home, px + 16, 1150, ic, 22, 700, C.accent), text(home, px + 68, 1138, a, 17, 600, C.text), muted(home, px + 68, 1164, b, 15)];
    group(home, n, "Преимущество / " + a); px += 325;
  }

  // ---------------------------------------------------------------- 2 Каталог
  const cat = frame("02 Каталог", W + 200, 1240);
  header(cat, "Каталог");
  crumbs(cat, 104, ["Главная", "Каталог"]);
  text(cat, 80, 134, "Каталог автомобилей", 36, 700, C.text);
  muted(cat, 470, 150, "248 автомобилей", 17);
  field(cat, 400, 196, 560, null, "Поиск по марке или модели", { icon: "⌕" });
  field(cat, 980, 196, 380, null, "Сортировка: сначала дешевле", { chevron: true });
  // filter panel
  const fp = [rect(cat, 80, 196, 290, 980, C.soft, { r: 14, name: "Фон панели фильтров" }), text(cat, 104, 216, "Фильтры", 20, 700, C.text)];
  fp.push(text(cat, 104, 258, "Состояние", 14, 500, C.text));
  let chx = 104; for (const [l, a] of [["Все", false], ["Новые", true], ["С пробегом", false]]) { const c = chip(cat, chx, 282, l, a); fp.push(c.node); chx += c.w + 6; }
  fp.push(field(cat, 104, 334, 242, "Марка", "Любая", { chevron: true }));
  fp.push(field(cat, 104, 414, 242, "Модель", "Любая", { chevron: true }));
  fp.push(text(cat, 104, 494, "Цена, ₽", 14, 500, C.text));
  fp.push(field(cat, 104, 518, 116, null, "от"), field(cat, 230, 518, 116, null, "до 3 000 000"));
  fp.push(text(cat, 104, 584, "Кузов", 14, 500, C.text));
  let cy = 612; for (const [l, ch] of [["Седан", false], ["Кроссовер", true], ["Хэтчбек", false], ["Универсал", false]]) { fp.push(checkbox(cat, 104, cy, l, ch)); cy += 32; }
  fp.push(text(cat, 104, 750, "Коробка передач", 14, 500, C.text));
  cy = 778; for (const [l, ch] of [["Автомат", true], ["Робот", false], ["Механика", false]]) { fp.push(checkbox(cat, 104, cy, l, ch)); cy += 32; }
  fp.push(field(cat, 104, 884, 242, "Привод", "Любой", { chevron: true }));
  fp.push(field(cat, 104, 964, 242, "Год выпуска", "от 2018", { chevron: true }));
  fp.push(button(cat, 104, 1060, 242, 48, "Показать 248", "primary"));
  fp.push(text(cat, 172, 1124, "Сбросить фильтры", 15, 600, C.accent));
  group(cat, fp, "Панель фильтров");
  let ax = 400; const af = [muted(cat, 400, 270, "Выбрано:", 15)]; ax = 476;
  for (const l of ["Новые ×", "Кроссовер ×", "до 3 000 000 ₽ ×", "Автомат ×"]) { const c = chip(cat, ax, 262, l, false); af.push(c.node); ax += c.w + 8; }
  group(cat, af, "Активные фильтры");
  const catCards = [];
  for (let i = 0; i < 6; i++) {
    const col = i % 3, row = Math.floor(i / 3);
    catCards.push(carCard(cat, 400 + col * 330, 316 + row * 432, 310, CARS[i], { compare: true }));
  }
  const pg = []; let pgx = 760;
  for (const l of ["‹", "1", "2", "3", "…", "21", "›"]) { const c = chip(cat, pgx, 1186, l, l === "1"); pg.push(c.node); pgx += c.w + 8; }
  group(cat, pg, "Пагинация");

  // ---------------------------------------------------------------- 3 Карточка авто
  const det = frame("03 Карточка автомобиля", 2 * (W + 200), 1240);
  header(det, "Каталог");
  crumbs(det, 104, ["Главная", "Каталог", "Geely", "Monjaro"]);
  photo(det, 80, 140, 780, 440, "Фото автомобиля — галерея");
  for (let i = 0; i < 5; i++) photo(det, 80 + i * 160, 596, 140, 84, "Фото " + (i + 2));
  const info = [rect(det, 900, 140, 460, 540, C.bg, { r: 16, stroke: C.line, name: "Фон блока покупки" })];
  info.push(text(det, 932, 168, "Geely Monjaro, 2024", 30, 700, C.text));
  let tx = 932; for (const l of ["Новый", "В наличии", "Полный привод"]) { const c = chip(det, tx, 216, l, false); info.push(c.node); tx += c.w + 8; }
  info.push(text(det, 932, 272, "4 349 000 ₽", 40, 700, C.text, { name: "Цена" }));
  info.push(muted(det, 932, 324, "Итоговая цена с НДС. Обязательного допоборудования нет.", 15, { w: 400, lh: 22 }));
  info.push(text(det, 932, 372, "В кредит от 58 900 ₽/мес  ·  Рассчитать →", 16, 600, C.accent));
  const detDrive = button(det, 932, 420, 396, 56, "Записаться на тест-драйв", "primary");
  info.push(detDrive);
  info.push(button(det, 932, 488, 396, 52, "Получить консультацию", "secondary"));
  info.push(checkbox(det, 932, 560, "Добавить к сравнению", false));
  info.push(rect(det, 932, 600, 396, 56, C.soft, { r: 10 }));
  info.push(text(det, 948, 610, "Есть автомобиль на обмен?", 15, 600, C.text));
  info.push(text(det, 948, 632, "Оценим его по трейд-ин →", 14, 600, C.accent));
  group(det, info, "Блок покупки");
  // tabs
  const tabs = [rect(det, 80, 760, 1280, 1, C.line)];
  let tbx = 80;
  for (const [l, a] of [["Характеристики", true], ["Комплектация", false], ["Кредит и трейд-ин", false], ["Гарантия и сервис", false]]) {
    const t = text(det, tbx, 724, l, 18, a ? 600 : 500, a ? C.accent : C.text);
    tabs.push(t); if (a) tabs.push(rect(det, tbx, 758, t.width, 3, C.accent, { r: 2 }));
    tbx += t.width + 40;
  }
  group(det, tabs, "Вкладки");
  const spec = [text(det, 80, 796, "Технические характеристики", 22, 700, C.text)];
  const rows = [["Двигатель", "бензиновый, 2.0 л, 238 л.с."], ["Коробка передач", "автомат, 8 ступеней"], ["Привод", "полный"], ["Кузов", "кроссовер, 5 мест"], ["Цвет", "серый металлик"], ["Пробег", "новый автомобиль"]];
  let ry = 844;
  rows.forEach(([k, v], i) => {
    spec.push(rect(det, 80, ry, 760, 48, i % 2 ? C.bg : C.soft, { r: 6 }));
    spec.push(muted(det, 100, ry + 14, k, 16)); spec.push(text(det, 400, ry + 14, v, 16, 500, C.text));
    ry += 48;
  });
  group(det, spec, "Таблица характеристик");
  const eq = [text(det, 900, 796, "Основная комплектация", 22, 700, C.text)];
  let ey = 848;
  for (const l of ["Камера кругового обзора 360°", "Адаптивный круиз-контроль", "Подогрев сидений и руля", "Бесключевой доступ", "Мультимедиа с экраном 12,3″", "Панорамная крыша"]) {
    eq.push(text(det, 900, ey, "✓", 16, 700, C.accent)); eq.push(text(det, 928, ey, l, 16, 400, C.text)); ey += 38;
  }
  eq.push(text(det, 900, ey + 8, "Вся комплектация →", 16, 600, C.accent));
  group(det, eq, "Комплектация");
  muted(det, 80, 1180, "Данные в прототипе приведены для примера.", 13);

  // ---------------------------------------------------------------- 4 Тест-драйв
  const td = frame("04 Запись на тест-драйв", 3 * (W + 200), 1120);
  header(td, "Тест-драйв");
  crumbs(td, 104, ["Главная", "Тест-драйв"]);
  text(td, 80, 134, "Запись на тест-драйв", 36, 700, C.text);
  muted(td, 80, 186, "Выберите удобные дату и время — менеджер подтвердит запись по телефону. Поездка бесплатная, с собой нужно взять водительское удостоверение.", 17, { w: 820, lh: 26 });
  const form = [rect(td, 80, 260, 820, 800, C.bg, { r: 16, stroke: C.line, name: "Фон формы" })];
  form.push(text(td, 112, 288, "Выбранный автомобиль", 15, 500, C.text, { op: 0.68 }));
  form.push(rect(td, 112, 316, 756, 104, C.soft, { r: 12 }));
  form.push(photo(td, 124, 328, 128, 80, "Фото"));
  form.push(text(td, 272, 340, "Geely Monjaro, 2024", 20, 600, C.text));
  form.push(muted(td, 272, 372, "Новый · полный привод · 4 349 000 ₽", 15));
  form.push(text(td, 780, 356, "Изменить", 15, 600, C.accent));
  form.push(field(td, 112, 448, 368, "Имя", "Как к вам обращаться"));
  form.push(field(td, 500, 448, 368, "Телефон", "+7 (___) ___-__-__"));
  form.push(field(td, 112, 540, 368, "Желаемая дата", "Выберите дату", { icon: "▦" }));
  form.push(field(td, 500, 540, 368, "Салон", "ул. Примерная, 1", { chevron: true }));
  form.push(text(td, 112, 632, "Удобное время", 14, 500, C.text));
  let tcx = 112; for (const [l, a] of [["10:00", false], ["12:00", false], ["14:00", true], ["16:00", false], ["18:00", false], ["20:00", false]]) { const c = chip(td, tcx, 658, l, a); form.push(c.node); tcx += c.w + 10; }
  form.push(field(td, 112, 716, 756, "Комментарий (необязательно)", "Например: хочу сравнить с другой моделью", { h: 80 }));
  form.push(checkbox(td, 112, 838, "Согласен на обработку персональных данных", true));
  form.push(button(td, 112, 884, 300, 56, "Отправить заявку", "primary"));
  form.push(muted(td, 112, 960, "Заявка ни к чему не обязывает. Менеджер свяжется с вами в течение 15 минут в рабочее время.", 14, { w: 700, lh: 20 }));
  group(td, form, "Форма записи на тест-драйв");
  const side = [rect(td, 940, 260, 420, 440, C.soft, { r: 16, name: "Фон подсказки" }), text(td, 972, 292, "Как проходит тест-драйв", 20, 700, C.text)];
  let sy = 340;
  for (const [n, l] of [["1", "Оставляете заявку на сайте"], ["2", "Менеджер подтверждает время"], ["3", "Приезжаете в салон с правами"], ["4", "Поездка 30–40 минут с консультантом"]]) {
    side.push(rect(td, 972, sy, 32, 32, C.accent, { r: 16 })); side.push(text(td, n === "1" ? 984 : 983, sy + 6, n, 15, 700, "#FFFFFF"));
    side.push(text(td, 1018, sy + 6, l, 16, 400, C.text)); sy += 56;
  }
  side.push(rect(td, 972, 572, 356, 1, C.line));
  side.push(text(td, 972, 592, "Адрес и часы работы", 16, 600, C.text));
  side.push(muted(td, 972, 620, "ул. Примерная, 1 · ежедневно 9:00–21:00", 15));
  side.push(text(td, 972, 650, "Показать на карте →", 15, 600, C.accent));
  group(td, side, "Подсказка о тест-драйве");

  // ---------------------------------------------------------------- 5 Стиль
  const st = frame("05 Цвета и типографика", 4 * (W + 200), 760);
  logo(st, 80, 60);
  text(st, 80, 140, "Цветовая палитра", 28, 700, C.text);
  const sw = [["#FFFFFF", "Основной фон"], ["#F1F4F8", "Дополнительный фон"], ["#17202C", "Основной текст"], ["#1A56DB", "Акцент: кнопки, ссылки"], ["#D3DAE3", "Рамки и разделители"]];
  sw.forEach(([hex, l], i) => {
    const x = 80 + i * 256;
    group(st, [rect(st, x, 196, 232, 120, hex, { r: 14, stroke: C.line }), text(st, x, 330, hex, 18, 700, C.text), muted(st, x, 358, l, 15)], "Цвет / " + hex);
  });
  text(st, 80, 430, "Типографика — Inter", 28, 700, C.text);
  text(st, 80, 486, "Заголовок H1 — Inter Bold 46", 46, 700, C.text);
  text(st, 80, 560, "Заголовок H2 — Inter Bold 30", 30, 700, C.text);
  text(st, 80, 612, "Основной текст — Inter Regular 16–18, межстрочный интервал 1,5", 18, 400, C.text);
  button(st, 80, 660, 230, 56, "Основная кнопка", "primary");
  button(st, 326, 660, 230, 56, "Второстепенная", "secondary");
  const c1 = chip(st, 580, 672, "Активный чип", true); const c2 = chip(st, 580 + c1.w + 10, 672, "Чип", false);

  // clickable prototype links between screens
  await link(toCatalog, cat); await link(showBtn, cat); await link(toDrive, td);
  for (const c of cards.concat(catCards)) {
    const btn = c.findOne(n => n.name === "Кнопка / Подробнее");
    if (btn) await link(btn, det);
  }
  await link(detDrive, td);
  try { page.flowStartingPoints = [{ nodeId: home.id, name: "Сайт АвтоЯсно" }]; } catch (e) {}

  figma.viewport.scrollAndZoomIntoView([home, cat, det, td, st]);
  figma.notify("АвтоЯсно: прототип создан");
  figma.closePlugin();
}

main().catch(e => { figma.notify("Ошибка: " + e.message, { error: true }); figma.closePlugin(); });
