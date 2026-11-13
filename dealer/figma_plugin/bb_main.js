
// ================================================================ Brand Book
// Builds the brand book on a dedicated "Brand Book" page; the prototype page is not touched.
const FW = 1600, FH = 1300, GAP_X = 160, GAP_Y = 200, TOTAL = 8;

function rectF(p, x, y, w, h, hex, op, o) {
  const r = rect(p, x, y, w, h, hex, o);
  r.fills = fill(hex, op);
  return r;
}
function label(f, x, y, s, color) {
  const t = text(f, x, y, s.toUpperCase(), 13, 600, color || C.accent, { name: "Метка раздела" });
  t.letterSpacing = { value: 1.5, unit: "PIXELS" };
  return t;
}
function para(f, x, y, s, w, o) {
  o = o || {};
  const size = o.size || 17;
  return text(f, x, y, s, size, o.weight || 400, o.color || C.text, { w: w, lh: Math.round(size * 1.5), op: o.op, name: o.name });
}
function center(node, x, y, w, h) {
  node.x = Math.round(x + (w - node.width) / 2);
  node.y = Math.round(y + (h - node.height) / 2);
  return node;
}
// variant: light | dark | blue | mono  (mark, letter, wordmark colours)
function brandLogo(p, x, y, s, variant, word) {
  const V = {
    light: [C.accent, "#FFFFFF", C.text], dark: [C.accent, "#FFFFFF", "#FFFFFF"],
    blue: ["#FFFFFF", C.accent, "#FFFFFF"], mono: [C.text, "#FFFFFF", C.text],
  }[variant || "light"];
  const mark = rect(p, x, y, s, s, V[0], { r: Math.round(s * 0.25), name: "Знак" });
  const fs = Math.round(s * 0.55);
  const a = text(p, 0, 0, "А", fs, 700, V[1], { name: "Буква «А»" });
  a.x = x + (s - a.width) / 2; a.y = y + (s - a.height) / 2;
  const nodes = [mark, a];
  if (word !== false) {
    const w = text(p, 0, 0, "АвтоЯсно", fs, 700, V[2], { name: "Словесный знак" });
    w.x = x + Math.round(s * 1.3); w.y = y + (s - w.height) / 2;
    nodes.push(w);
  }
  return group(p, nodes, word === false ? "Знак «АвтоЯсно»" : "Логотип «АвтоЯсно»");
}
function tr(d, dx, dy) {
  let i = 0;
  return d.trim().split(/\s+/).map(tok => /^[A-Za-z]$/.test(tok) ? tok : String(parseFloat(tok) + (i++ % 2 === 0 ? dx : dy))).join(" ");
}
const ICONS = {
  "Автомобиль": { d: "M 6 32 L 6 26 L 11 17 Q 13 14 17 14 L 31 14 Q 35 14 37 17 L 42 26 L 42 32 Z M 6 25 L 42 25", e: [[15, 33, 4.5], [33, 33, 4.5]] },
  "Тест-драйв": { d: "M 8 12 L 40 12 L 40 40 L 8 40 Z M 8 20 L 40 20 M 16 7 L 16 15 M 32 7 L 32 15 M 18 30 L 22 34 L 30 26" },
  "Кредит": { d: "M 6 13 L 42 13 L 42 35 L 6 35 Z M 6 20 L 42 20 M 12 29 L 22 29" },
  "Трейд-ин": { d: "M 8 17 L 38 17 M 31 10 L 38 17 L 31 24 M 40 31 L 10 31 M 17 24 L 10 31 L 17 38" },
  "Гарантия": { d: "M 24 6 L 39 12 L 39 23 Q 39 36 24 42 Q 9 36 9 23 L 9 12 Z M 17 24 L 22 29 L 31 19" },
  "Адрес салона": { d: "M 24 43 Q 11 30 11 20 Q 11 7 24 7 Q 37 7 37 20 Q 37 30 24 43 Z", e: [[24, 20, 5]] },
  "Поиск": { d: "M 29 29 L 40 40", e: [[20, 20, 12]] },
};
function icon(p, x, y, name, color) {
  const tile = rect(p, x, y, 72, 72, C.soft, { r: 14, name: "Подложка иконки" });
  const ox = x + 12, oy = y + 12, nodes = [tile];
  const v = figma.createVector();
  v.vectorPaths = [{ windingRule: "NONE", data: tr(ICONS[name].d, ox, oy) }];
  v.strokes = fill(color || C.accent); v.strokeWeight = 2.5; v.strokeCap = "ROUND"; v.strokeJoin = "ROUND"; v.fills = [];
  v.name = "Контур";
  p.appendChild(v); nodes.push(v);
  for (const [cx, cy, r] of ICONS[name].e || []) {
    const e = figma.createEllipse();
    e.resize(r * 2, r * 2); e.x = ox + cx - r; e.y = oy + cy - r;
    e.fills = fill(C.soft); e.strokes = fill(color || C.accent); e.strokeWeight = 2.5;
    p.appendChild(e); nodes.push(e);
  }
  return group(p, nodes, "Иконка / " + name);
}
function bbPage(bb, idx, title, subtitle, dark) {
  const f = figma.createFrame();
  f.name = String(idx).padStart(2, "0") + " " + title;
  f.x = ((idx - 1) % 4) * (FW + GAP_X);
  f.y = Math.floor((idx - 1) / 4) * (FH + GAP_Y);
  f.resize(FW, FH);
  f.fills = fill(dark ? C.text : C.bg);
  bb.appendChild(f);
  const fg = dark ? "#FFFFFF" : C.text;
  const top = [brandLogo(f, 80, 52, 32, dark ? "dark" : "light")];
  const meta = text(f, 0, 58, "Брендбук · 2026", 15, 500, fg, { op: 0.6 });
  meta.x = FW - 80 - meta.width; top.push(meta);
  top.push(rectF(f, 80, 112, FW - 160, 1, dark ? "#FFFFFF" : C.line, dark ? 0.15 : 1));
  group(f, top, "Колонтитул");
  const head = [text(f, 80, 150, String(idx).padStart(2, "0"), 20, 600, C.accent, { name: "Номер раздела" })];
  head.push(text(f, 80, 180, title, 56, 700, fg, { name: "Заголовок раздела" }));
  if (subtitle) head.push(para(f, 80, 258, subtitle, 1100, { size: 19, color: fg, op: 0.68, name: "Подзаголовок" }));
  group(f, head, "Заголовок");
  const foot = [text(f, 80, FH - 56, "АвтоЯсно — мультибрендовый автосалон · учебный концепт", 14, 400, fg, { op: 0.55 })];
  const num = text(f, 0, FH - 56, idx + " / " + TOTAL, 14, 500, fg, { op: 0.55 });
  num.x = FW - 80 - num.width; foot.push(num);
  group(f, foot, "Подвал");
  return f;
}
function tileWithLogo(f, x, y, w, h, bg, variant, s, name) {
  const t = rect(f, x, y, w, h, bg, { r: 14, stroke: bg === "#FFFFFF" ? C.line : null, name: "Фон" });
  const l = center(brandLogo(f, 0, 0, s || 40, variant), x, y, w, h);
  return { tile: t, logo: l, g: group(f, [t, l], name || "Плитка логотипа") };
}

// ---------------------------------------------------------------- pages
function pIdentity(bb) {
  const f = bbPage(bb, 1, "Идентичность бренда", null, true);
  brandLogo(f, 80, 290, 88, "dark");
  const W2 = "#FFFFFF";
  label(f, 80, 430, "Концепция");
  para(f, 80, 460, "«АвтоЯсно» — мультибрендовый автосалон новых автомобилей и автомобилей с пробегом. Название объединяет слова «авто» и «ясно»: всё, что важно покупателю, понятно с первого взгляда — цена, условия и состояние машины.", 640, { size: 21, color: W2 });
  label(f, 80, 660, "Миссия");
  para(f, 80, 690, "Сделать покупку автомобиля прозрачной и спокойной: одна итоговая цена, честные условия кредита и трейд-ина, тест-драйв в удобное время.", 640, { size: 21, color: W2 });
  label(f, 80, 860, "Слоган");
  text(f, 80, 890, "Всё ясно. Можно ехать.", 44, 700, W2, { name: "Слоган" });
  label(f, 80, 990, "Тон общения");
  para(f, 80, 1020, "Спокойно, по делу и на «вы». Короткие фразы, цифры вместо обещаний, никаких звёздочек и мелкого шрифта.", 640, { size: 19, color: W2, op: 0.8 });

  label(f, 840, 290, "Ценности");
  const V = [["Прозрачность", "Итоговая цена без скрытых условий и заранее отмеченных скидок."],
    ["Честность", "Реальные фото, история и проверка каждого автомобиля."],
    ["Скорость", "До заявки на тест-драйв — не больше трёх шагов."],
    ["Забота", "Консультация без давления и помощь после покупки."]];
  V.forEach(([t, d], i) => {
    const x = 840 + (i % 2) * 350, y = 322 + Math.floor(i / 2) * 210;
    const n = [rectF(f, x, y, 330, 190, "#FFFFFF", 0.06, { r: 14 })];
    n.push(text(f, x + 28, y + 26, "0" + (i + 1), 16, 600, C.accent));
    n.push(text(f, x + 28, y + 56, t, 24, 600, W2));
    n.push(para(f, x + 28, y + 100, d, 274, { size: 16, color: W2, op: 0.72 }));
    group(f, n, "Ценность / " + t);
  });
  label(f, 840, 780, "Позиционирование");
  para(f, 840, 810, "Для жителей города 25–55 лет, которые выбирают автомобиль онлайн, «АвтоЯсно» — салон, где цена на сайте совпадает с ценой в договоре. В отличие от крупных дилерских сетей с акциями и сносками, бренд делает ставку на ясность и предсказуемость.", 680, { size: 20, color: W2 });
  label(f, 840, 1020, "Характер");
  let cx = 840;
  for (const k of ["Надёжный", "Открытый", "Современный", "Спокойный"]) {
    const t = text(f, 0, 0, k, 15, 500, W2);
    const r = rectF(f, cx, 1050, t.width + 32, 38, "#FFFFFF", 0.1, { r: 19 });
    t.x = cx + 16; t.y = 1059; f.appendChild(t);
    group(f, [r, t], "Чип / " + k); cx += t.width + 44;
  }
}

function pLogo(bb) {
  const f = bbPage(bb, 2, "Логотип", "Логотип состоит из знака — синего скруглённого квадрата с буквой «А» — и словесного знака «АвтоЯсно», набранного Inter Bold. Это тот же логотип, что в шапке сайта.");
  label(f, 80, 340, "Основная версия");
  const main = rect(f, 80, 372, 860, 360, C.soft, { r: 16, name: "Фон" });
  group(f, [main, center(brandLogo(f, 0, 0, 96, "light"), 80, 372, 860, 360)], "Основная версия");
  label(f, 80, 770, "Цветовые версии");
  [["На тёмном фоне", C.text, "dark"], ["На синем фоне", C.accent, "blue"], ["Монохромная", "#FFFFFF", "mono"]].forEach(([n, bg, v], i) => {
    const x = 80 + i * 292;
    const t = tileWithLogo(f, x, 802, 276, 150, bg, v, 34, "Версия / " + n);
    muted(f, x, 966, n, 15);
  });
  label(f, 1000, 340, "Упрощённая версия — знак");
  let x = 1000;
  for (const [s, cap] of [[96, "96 px"], [56, "56 px"], [32, "32 px"], [20, "20 px · фавикон"]]) {
    brandLogo(f, x, 372 + (96 - s), s, "light", false);
    muted(f, x, 482, cap, 14);
    x += s + 40;
  }
  text(f, 1000, 540, "Значение", 24, 700, C.text);
  para(f, 1000, 580, "Знак похож на кнопку приложения или клавишу: «нажми — и всё понятно». Буква «А» — первая буква слов «АвтоЯсно» и «автомобиль». Синий цвет передаёт надёжность и спокойствие, графитовый словесный знак — деловой характер. Скругления знака повторяют скругления кнопок и карточек сайта.", 520, { size: 16 });
  text(f, 1000, 830, "Правила использования", 24, 700, C.text);
  para(f, 1000, 870, "• Охранное поле — не меньше половины высоты знака со всех сторон\n• Минимальный размер знака: 20 px на экране, 8 мм в печати\n• Только утверждённые цветовые версии\n• Не искажать, не поворачивать и не добавлять эффекты\n• Знак без надписи — для аватаров, фавикона и мелких носителей", 520, { size: 16 });
}

function swatch(f, x, y, w, h, hex, name, role, op) {
  const n = [rectF(f, x, y, w, h, hex, op === undefined ? 1 : op, { r: 14, stroke: hex === "#FFFFFF" ? C.line : null, name: "Цвет " + hex })];
  const c = rgb(hex);
  n.push(text(f, x, y + h + 16, name, 20, 600, C.text));
  n.push(text(f, x, y + h + 46, hex + (op ? " · " + Math.round(op * 100) + "%" : ""), 17, 500, C.text));
  n.push(muted(f, x, y + h + 72, "RGB " + [c.r, c.g, c.b].map(v => Math.round(v * 255)).join(" · "), 14));
  n.push(muted(f, x, y + h + 94, role, 14, { w: w }));
  return group(f, n, "Образец / " + name);
}
function pColors(bb) {
  const f = bbPage(bb, 3, "Цветовая палитра", "Палитра повторяет цвета прототипа сайта: светлая деловая основа и один насыщенный синий акцент, который всегда означает действие.");
  label(f, 80, 340, "Основные и акцентный цвета");
  swatch(f, 80, 372, 460, 200, "#1A56DB", "Синий «Ясный» — акцентный", "Кнопки, ссылки, активные элементы, знак логотипа");
  swatch(f, 570, 372, 460, 200, "#17202C", "Графит — основной", "Текст, заголовки, тёмные поверхности");
  swatch(f, 1060, 372, 460, 200, "#FFFFFF", "Белый — основной", "Фон страниц, карточек и носителей");
  label(f, 80, 730, "Вспомогательные цвета");
  swatch(f, 80, 762, 340, 120, "#F1F4F8", "Туман", "Подложки блоков, панель фильтров");
  swatch(f, 440, 762, 340, 120, "#E3E8EF", "Подложка фото", "Заглушки изображений");
  swatch(f, 800, 762, 340, 120, "#D3DAE3", "Серо-голубой", "Рамки полей, разделители");
  swatch(f, 1160, 762, 340, 120, "#17202C", "Графит 68%", "Второстепенный текст и подписи", 0.68);
  label(f, 80, 1060, "Пропорции в макетах");
  let x = 80; const parts = [["Белый 60%", "#FFFFFF", 0.6, C.text], ["Туман и рамки 25%", "#F1F4F8", 0.25, C.text], ["Графит 10%", "#17202C", 0.1, "#FFFFFF"], ["Синий 5%", "#1A56DB", 0.05, "#FFFFFF"]];
  const n = [];
  for (const [l, hex, share, tc] of parts) {
    const w = Math.round(1440 * share);
    n.push(rect(f, x, 1092, w, 56, hex, { stroke: C.line }));
    const t = text(f, x + 14, 1110, share >= 0.1 ? l : "5%", 14, 600, tc); n.push(t);
    x += w;
  }
  group(f, n, "Пропорции цветов");
}

function pType(bb) {
  const f = bbPage(bb, 4, "Типографика", "Единственный фирменный шрифт — Inter. Он же используется во всех экранах прототипа.");
  const n = [rect(f, 80, 340, 560, 840, C.soft, { r: 16, name: "Фон" })];
  n.push(text(f, 116, 360, "Аа", 200, 700, C.text));
  n.push(text(f, 116, 620, "Inter", 44, 700, C.text));
  n.push(para(f, 116, 684, "Открытая лицензия SIL OFL, полная поддержка кириллицы, хорошая читаемость цифр и цен на экране.", 488, { size: 16, op: 0.75 }));
  n.push(text(f, 116, 800, "АБВГДЕЁЖЗИЙКЛМНОП\nРСТУФХЦЧШЩЪЫЬЭЮЯ\nабвгдеёжзийклмнопрстуфхцчшщъыьэюя\n0123456789  ₽  %  №  «»  —", 18, 400, C.text, { lh: 30, w: 488 }));
  let x = 116;
  for (const [w, s] of [[400, "Regular"], [500, "Medium"], [600, "Semi Bold"], [700, "Bold"]]) {
    const t = text(f, x, 1000, s, 18, w, C.text); n.push(t); n.push(muted(f, x, 1030, String(w), 13)); x += t.width + 28;
  }
  n.push(para(f, 116, 1080, "Кириллица и латиница набираются одним шрифтом.", 488, { size: 14, op: 0.68 }));
  group(f, n, "Образец шрифта");
  label(f, 700, 340, "Иерархия");
  const rows = [["H1 · Bold 40 / 48", "Честная итоговая цена", 40, 700, 1, 84],
    ["H2 · Bold 30 / 38", "Автомобили в наличии", 30, 700, 1, 70],
    ["H3 · Semi Bold 22 / 30", "Geely Monjaro, 2024", 22, 600, 1, 60],
    ["Цена · Bold 28", "4 349 000 ₽", 28, 700, 1, 66],
    ["Текст · Regular 18 / 27", "Цена указана с НДС и не зависит от выбора кредита или трейд-ина.", 18, 400, 1, 84],
    ["Подпись · Regular 14, 68%", "в кредит от 58 900 ₽/мес", 14, 400, 0.68, 50]];
  let y = 380;
  for (const [meta, s, size, w, op, h] of rows) {
    const g = [muted(f, 700, y + 6, meta, 14, { w: 220 }), text(f, 940, y, s, size, w, C.text, { op: op, w: 580, lh: Math.round(size * 1.3) }), rect(f, 700, y + h - 14, 820, 1, C.line)];
    group(f, g, "Стиль / " + meta.split(" · ")[0]);
    y += h;
  }
  const b = [muted(f, 700, y + 16, "Кнопка · Semi Bold 17", 14, { w: 220 }), button(f, 940, y, 300, 56, "Записаться на тест-драйв", "primary")];
  group(f, b, "Стиль / Кнопка");
  text(f, 700, 920, "Правила набора", 22, 700, C.text);
  para(f, 700, 958, "• Не больше трёх размеров текста на одном экране\n• Длинный текст — по левому краю, строка до 70 знаков\n• Прописные — только для коротких меток разделов\n• Цены — с пробелами между разрядами: 4 349 000 ₽", 820, { size: 17 });
}

function pVisual(bb) {
  const f = bbPage(bb, 5, "Визуальный стиль", "Спокойная, чистая и технологичная подача: много воздуха, реальные автомобили, тонкие линии и один синий акцент.");
  label(f, 80, 340, "Фотография: набор ракурсов");
  ["3/4 спереди", "Профиль", "3/4 сзади", "Салон", "Панель приборов", "Багажник"].forEach((l, i) => {
    photo(f, 80 + (i % 3) * 296, 372 + Math.floor(i / 3) * 196, 280, 170, l);
  });
  text(f, 1000, 372, "Правила съёмки", 24, 700, C.text);
  para(f, 1000, 412, "• Только реальные фото конкретного автомобиля из наличия\n• Светлый нейтральный фон, естественный свет\n• Единый набор ракурсов, камера на высоте около 1 м\n• Без фильтров, рамок, надписей и стоковых изображений\n• Номерной знак и личные вещи скрываются", 520, { size: 17 });
  para(f, 1000, 640, "В макетах фото обозначены заглушками; реальные снимки добавляются при наполнении сайта.", 520, { size: 15, op: 0.68 });
  label(f, 80, 790, "Иконки");
  Object.keys(ICONS).forEach((k, i) => {
    const x = 80 + i * 112;
    icon(f, x, 822, k);
    muted(f, x, 904, k, 13, { w: 100 });
  });
  para(f, 80, 960, "Линейные иконки на сетке 48 px, обводка 2,5 px, скруглённые концы и углы. Цвет — синий для действий, графитовый для справочной информации. Подложка — скруглённый квадрат цвета «Туман».", 760, { size: 16, op: 0.8 });
  label(f, 1000, 790, "Графические элементы");
  const ge = [rect(f, 1000, 822, 220, 130, C.bg, { r: 14, stroke: C.line, name: "Карточка 14 px" }),
    muted(f, 1018, 840, "Карточка · 14 px", 13), rect(f, 1018, 870, 120, 10, C.soft, { r: 5 }), rect(f, 1018, 890, 80, 10, C.soft, { r: 5 }), rect(f, 1018, 916, 100, 22, C.accent, { r: 6 })];
  const c1 = chip(f, 1244, 822, "Чип · 17 px", true); const c2 = chip(f, 1244, 866, "Новый", false);
  ge.push(c1.node, c2.node, rect(f, 1244, 922, 240, 1, C.line, { name: "Линия 1 px" }), muted(f, 1244, 930, "Разделитель 1 px", 13));
  group(f, ge, "Графические элементы");
  label(f, 1000, 990, "Направление");
  let cx = 1000;
  for (const k of ["Спокойно", "Чисто", "Технологично", "Честно"]) { const c = chip(f, cx, 1020, k, false); cx += c.w + 10; }
  para(f, 1000, 1076, "Акцент на автомобиле и цене, а не на декоре: никаких градиентов, бликов и агрессивных акций.", 520, { size: 15, op: 0.68 });
}

function pUI(bb) {
  const f = bbPage(bb, 6, "UI-компоненты", "Компоненты взяты из прототипа сайта и используются на всех страницах без изменений.");
  label(f, 80, 340, "Навигация");
  const nav = figma.createFrame();
  nav.name = "Шапка сайта"; nav.x = 80; nav.y = 372; nav.resize(1440, 80);
  nav.cornerRadius = 12; nav.strokes = fill(C.line); nav.strokeWeight = 1; nav.fills = fill(C.bg);
  f.appendChild(nav); header(nav, "Каталог");
  label(f, 80, 490, "Кнопки");
  const B = [[300, 56, "Записаться на тест-драйв", "primary", "Основная · 56"], [230, 56, "Смотреть каталог", "secondary", "Второстепенная · 56"],
    [160, 44, "Подробнее", "primary", "Компактная · 44"], [200, 44, "Сбросить фильтры", "ghost", "Текстовая"], [220, 56, "Отправить заявку", "primary", "Неактивная · 40%"]];
  let x = 80;
  for (const [w, h, l, k, cap] of B) {
    const b = button(f, x, 522, w, h, l, k);
    if (cap.startsWith("Неактивная")) { b.opacity = 0.4; b.name = "Кнопка / неактивная"; }
    muted(f, x, 592, cap, 13); x += w + 24;
  }
  label(f, 80, 640, "Поля, чипы и отметки");
  field(f, 80, 672, 360, "Телефон", "+7 (___) ___-__-__");
  field(f, 470, 672, 280, "Марка", "Любая", { chevron: true });
  let cx = 790;
  for (const [l, a] of [["Все", true], ["Новые", false], ["С пробегом", false]]) { const c = chip(f, cx, 708, l, a); cx += c.w + 8; }
  checkbox(f, cx + 24, 715, "Сравнить", true);
  label(f, 80, 790, "Карточки автомобиля");
  carCard(f, 80, 822, 310, CARS[0], {});
  carCard(f, 410, 822, 310, CARS[2], { compare: true });
  text(f, 780, 822, "Стиль интерфейса", 24, 700, C.text);
  para(f, 780, 864, "• Скругления: кнопки и поля 10 px, карточки 14 px, чипы 17 px\n• Высота элементов: 56 / 48 / 44 px\n• Обводка: 1 px #D3DAE3, активная — 1,5 px #1A56DB\n• Сетка 8 px, поля страницы 80 px, ширина макета 1440 px\n• Активный пункт меню — синий текст и полоса 3 px снизу\n• Неактивный элемент — непрозрачность 40%\n• В карточке всегда есть итоговая цена, платёж и одно главное действие", 740, { size: 17 });
}

function pApps(bb) {
  const f = bbPage(bb, 7, "Носители бренда", "Примеры применения фирменного стиля. Имена, контакты и адрес — демонстрационные.");
  label(f, 80, 340, "Визитная карточка · 90 × 50 мм");
  const fr = rect(f, 80, 372, 450, 250, C.accent, { r: 12, name: "Фон" });
  const fl = center(brandLogo(f, 0, 0, 52, "blue"), 80, 372, 450, 210);
  const ft = text(f, 0, 0, "Всё ясно. Можно ехать.", 15, 500, "#FFFFFF", { op: 0.85 }); center(ft, 80, 540, 450, 40);
  group(f, [fr, fl, ft], "Визитка / лицевая сторона");
  const b = [rect(f, 550, 372, 450, 250, C.bg, { r: 12, stroke: C.line, name: "Фон" })];
  b.push(text(f, 582, 404, "Иван Петров", 24, 700, C.text), muted(f, 582, 438, "Менеджер по продажам", 15));
  b.push(rect(f, 582, 478, 386, 1, C.line));
  b.push(text(f, 582, 496, "+7 (495) 000-00-00", 16, 600, C.text), text(f, 582, 524, "i.petrov@avtoyasno.ru", 15, 400, C.text));
  b.push(muted(f, 582, 552, "г. Москва, ул. Примерная, 1 · avtoyasno.ru", 14));
  b.push(brandLogo(f, 936, 404, 32, "light", false));
  group(f, b, "Визитка / оборотная сторона");
  muted(f, 80, 634, "Лицевая сторона", 14); muted(f, 550, 634, "Оборотная сторона", 14);

  label(f, 1060, 340, "Социальные сети");
  const av = figma.createEllipse(); av.resize(96, 96); av.x = 1060; av.y = 372; av.fills = fill(C.accent); f.appendChild(av);
  const avA = text(f, 0, 0, "А", 52, 700, "#FFFFFF"); center(avA, 1060, 372, 96, 96);
  group(f, [av, avA], "Аватар");
  text(f, 1176, 392, "АвтоЯсно", 22, 700, C.text); muted(f, 1176, 424, "@avtoyasno · аватар сообщества", 14);
  const post = [rect(f, 1060, 492, 230, 230, C.accent, { r: 12, name: "Фон" })];
  post.push(text(f, 1082, 514, "Тест-драйв\nза 5 минут", 28, 700, "#FFFFFF", { lh: 34 }));
  post.push(text(f, 1082, 600, "Выберите авто и время\nна сайте", 14, 400, "#FFFFFF", { op: 0.85, lh: 20 }));
  post.push(brandLogo(f, 1082, 676, 26, "blue"));
  group(f, post, "Пост 1:1");
  const st = [rect(f, 1310, 492, 130, 230, C.text, { r: 12, name: "Фон" })];
  st.push(photo(f, 1320, 502, 110, 92, "Фото"));
  st.push(text(f, 1322, 606, "Новинки\nнедели", 17, 700, "#FFFFFF", { lh: 22 }));
  st.push(button(f, 1322, 670, 106, 34, "Смотреть", "primary"));
  group(f, st, "Сторис 9:16");
  muted(f, 1060, 734, "Пост 1:1", 14); muted(f, 1310, 734, "Сторис 9:16", 14);

  label(f, 80, 700, "Вывеска на фасаде");
  const fa = [rect(f, 80, 732, 920, 460, C.soft, { r: 16, name: "Фон" })];
  fa.push(rect(f, 140, 820, 800, 372, C.bg, { stroke: C.line, name: "Здание" }));
  fa.push(rect(f, 140, 820, 800, 96, C.text, { name: "Фриз" }));
  fa.push(center(brandLogo(f, 0, 0, 56, "dark"), 140, 820, 800, 96));
  for (const wx of [180, 420, 700]) fa.push(rect(f, wx, 950, wx === 420 ? 240 : 200, 242, C.line, { name: wx === 420 ? "Вход" : "Витрина" }));
  fa.push(text(f, 450, 960, "Новые · С пробегом", 14, 600, C.text, { op: 0.7 }));
  group(f, fa, "Фасад автосалона");
  label(f, 1060, 790, "Пилон и указатель");
  const py = [rect(f, 1060, 822, 130, 370, C.accent, { r: 10, name: "Пилон" })];
  py.push(brandLogo(f, 1093, 852, 64, "blue", false));
  py.push(text(f, 1060, 950, "Новые\nС пробегом\nТрейд-ин\nКредит\nСервис", 16, 600, "#FFFFFF", { lh: 30, w: 130, align: "CENTER" }));
  group(f, py, "Пилон у въезда");
  const sg = [rect(f, 1220, 822, 300, 84, C.bg, { r: 10, stroke: C.line, name: "Фон" }), brandLogo(f, 1240, 844, 40, "light", false), text(f, 1296, 850, "Тест-драйв →", 22, 600, C.text)];
  group(f, sg, "Указатель");
  para(f, 1220, 930, "Пилон: высота 6 м, синий фон, белый знак и список услуг. Указатели на территории — белые, со знаком и стрелкой.", 300, { size: 15, op: 0.75 });
}

function pRules(bb) {
  const f = bbPage(bb, 8, "Правила применения", "Как использовать логотип, цвета и шрифт, чтобы бренд оставался узнаваемым.");
  label(f, 80, 340, "Логотип: правильно и неправильно");
  const tiles = [];
  for (let i = 0; i < 8; i++) tiles.push([80 + (i % 4) * 360, 372 + Math.floor(i / 4) * 250]);
  const ok = (i, bg, v, cap) => { const [x, y] = tiles[i]; tileWithLogo(f, x, y, 340, 180, bg, v, 40, "Так / " + cap); text(f, x, y + 192, "✓  " + cap, 15, 600, C.accent); };
  const bad = (i, cap, build, bg) => {
    const [x, y] = tiles[i];
    const t = rect(f, x, y, 340, 180, bg || "#FFFFFF", { r: 14, stroke: bg ? null : C.line, name: "Фон" });
    const l = build(); center(l, x, y, 340, 180);
    const cross = figma.createVector();
    cross.vectorPaths = [{ windingRule: "NONE", data: `M ${x + 306} ${y + 16} L ${x + 324} ${y + 34} M ${x + 324} ${y + 16} L ${x + 306} ${y + 34}` }];
    cross.strokes = fill(C.text); cross.strokeWeight = 2.5; cross.strokeCap = "ROUND"; cross.name = "Знак запрета"; f.appendChild(cross);
    group(f, [t, l, cross], "Не так / " + cap);
    text(f, x, y + 192, "✕  " + cap, 15, 600, C.text);
  };
  ok(0, "#FFFFFF", "light", "На белом фоне");
  ok(1, C.text, "dark", "На графитовом фоне");
  ok(2, C.accent, "blue", "На синем фоне");
  bad(3, "Не растягивать", () => {
    const m = rect(f, 0, 0, 72, 40, C.accent, { r: 10 }); const a = text(f, 0, 0, "А", 22, 700, "#FFFFFF"); center(a, 0, 0, 72, 40);
    const w = text(f, 86, 6, "АвтоЯсно", 22, 700, C.text); w.letterSpacing = { value: 9, unit: "PIXELS" };
    return group(f, [m, a, w], "Искажённый логотип");
  });
  bad(4, "Не менять цвета", () => {
    const g = brandLogo(f, 0, 0, 40, "light"); g.children[0].fills = fill("#2FA36B"); g.children[2].fills = fill(C.accent); return g;
  });
  bad(5, "Не поворачивать", () => { const g = brandLogo(f, 0, 0, 40, "light"); g.rotation = -14; return g; });
  bad(6, "Не ставить на неконтрастный фон", () => brandLogo(f, 0, 0, 40, "light"), C.text);
  bad(7, "Не добавлять тени и эффекты", () => {
    const g = brandLogo(f, 0, 0, 40, "light");
    g.effects = [{ type: "DROP_SHADOW", color: { r: 0, g: 0, b: 0, a: 0.45 }, offset: { x: 4, y: 6 }, radius: 8, spread: 0, visible: true, blendMode: "NORMAL" }];
    return g;
  });

  label(f, 80, 890, "Охранное поле");
  const lg = brandLogo(f, 128, 970, 48, "light");
  const box = rect(f, 104, 946, lg.width + 48, 96, null, { stroke: C.accent, name: "Охранное поле" }); box.dashPattern = [6, 6];
  group(f, [box, lg], "Схема охранного поля");
  para(f, 80, 1060, "x = ½ высоты знака. Внутри поля не размещаются текст, края носителя и другие логотипы.", 440, { size: 15, op: 0.8 });

  label(f, 600, 890, "Цветовые сочетания");
  [["#FFFFFF", C.text, true], [C.accent, "#FFFFFF", true], [C.text, "#FFFFFF", true], [C.text, C.accent, false], [C.soft, C.line, false]].forEach(([bg, fg, good], i) => {
    const x = 600 + i * 88;
    const r = rect(f, x, 922, 76, 64, bg, { r: 10, stroke: bg === "#FFFFFF" ? C.line : null });
    const a = text(f, 0, 0, "Аа", 22, 700, fg); center(a, x, 922, 76, 64);
    const m = text(f, x + 26, 994, good ? "✓" : "✕", 18, 700, good ? C.accent : C.text);
    group(f, [r, a, m], "Сочетание " + (good ? "допустимо" : "недопустимо"));
  });
  para(f, 600, 1040, "Текст и фон — только с высоким контрастом. Синий не используется для текста на графите.", 420, { size: 15, op: 0.8 });

  label(f, 1080, 890, "Типографика");
  para(f, 1080, 922, "✓  Только Inter, четыре начертания\n✓  Левое выравнивание длинного текста\n✓  Цены и цифры — тем же шрифтом\n✕  Другие шрифты, курсив и обводка\n✕  Растянутый или сжатый текст\n✕  Текст поверх фото без подложки", 440, { size: 16 });
}

async function buildBrandBook() {
  for (const s of ["Regular", "Medium", "Semi Bold", "Bold"]) await figma.loadFontAsync({ family: "Inter", style: s });
  let bb = figma.root.children.find(p => p.name === "Brand Book");
  if (!bb) { bb = figma.createPage(); bb.name = "Brand Book"; }
  await figma.setCurrentPageAsync(bb);
  for (const n of bb.children.slice()) n.remove();
  for (const fn of [pIdentity, pLogo, pColors, pType, pVisual, pUI, pApps, pRules]) fn(bb);
  const frames = bb.children.filter(n => n.type === "FRAME");
  const texts = bb.findAll(n => n.type === "TEXT").length;
  const images = bb.findAll(n => "fills" in n && Array.isArray(n.fills) && n.fills.some(p => p.type === "IMAGE")).length;
  figma.viewport.scrollAndZoomIntoView(frames);
  figma.notify(`Brand Book: фреймов ${frames.length}, текстовых слоёв ${texts}, растровых изображений ${images}`, { timeout: 20000 });
  figma.closePlugin();
}
buildBrandBook().catch(e => { figma.notify("Ошибка брендбука: " + e.message, { error: true, timeout: 20000 }); figma.closePlugin(); });
