"""Specimen: HTML (real @font-face TTF + single-stroke master) -> PDF via headless Chrome."""
import base64, html, json, os, subprocess, sys
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphmap as GM  # noqa: E402

B, D = os.path.join(ROOT, "build"), os.path.join(ROOT, "dist")

P1 = ("Вчера Фёдор и Юля шли через тихий парк. У беседки рыжий кот прыгнул на скамью, "
      "а щенок вдруг залаял. «Чья это шапка?» — спросила Юля. Фёдор поднял её и заметил "
      "записку: «Жду вас в 18:45 у подъезда».")
P2 = ("Дома их ждали горячий чай, мягкий хлеб, сыр и клубничный джем. Позже они открыли "
      "большой ящик, нашли фотоаппарат и письмо. На улице ёж шуршал в траве, а цыплёнок "
      "клевал зёрна.")
WORDS = "мама, письмо, шоссе, аллея, Россия."
NEW = [
    "Съешь же ещё этих мягких французских булок, да выпей чаю.",
    "В чащах юга жил бы цитрус? Да, но фальшивый экземпляр!",
    "Завтра утром я позвоню бабушке и расскажу о поездке на дачу.",
    "Мы встретимся в среду, 3 июля, в 9:30 у старого моста (вход №2).",
    "Эй, жлоб! Где туз? Прячь юных съёмщиц в шкаф.",
    "Осенью листья желтеют, а ветер уносит их далеко-далеко.",
    "Цена снизилась на 15% — теперь билет стоит 270 рублей.",
]


def stroke_svg(text, master, size_pt, width_units=None, hairline=False):
    """Typeset text directly from the single-stroke master (open paths, stroke only)."""
    G = master["glyphs"]; m = master["meta"]
    cmap = {g["char"]: n for n, g in G.items() if g["unicode"]}
    x, parts = 0, []
    for ch in text:
        if ch == " ":
            x += m["space"]; continue
        n = cmap.get(ch)
        if not n:
            continue
        for s in G[n]["strokes"]:
            c = s["cubic"]
            d = "M%.1f %.1f" % tuple(c[0][0]) + "".join(
                " C%.1f %.1f %.1f %.1f %.1f %.1f" % (*q[1], *q[2], *q[3]) for q in c)
            if s["closed"]:
                d += " Z"
            parts.append(f'<path transform="translate({x} 0)" d="{d}"/>')
        x += G[n]["advance"]
    sw = 4 if hairline else (width_units or m["pen"])
    col = "#c0392b" if hairline else "#000"
    asc, desc = m["asc"], m["desc"]
    h = asc - desc
    return (f'<svg viewBox="0 {-asc} {x} {h}" style="height:{size_pt * h / 1000:.1f}pt">'
            f'<g transform="scale(1 -1)" fill="none" stroke="{col}" stroke-width="{sw}" '
            f'stroke-linecap="round" stroke-linejoin="round">{"".join(parts)}</g></svg>')


def main():
    master = json.load(open(os.path.join(B, "master.json")))
    scan = Image.open(os.path.join(ROOT, GM.SCAN))
    scan.crop((100, 55, 1690, 330)).save(os.path.join(B, "scan_p1.png"))
    scan.crop((100, 340, 1690, 640)).save(os.path.join(B, "scan_p2.png"))
    e = html.escape
    up, lo = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ", "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    meta = master["meta"]
    css = f"""
@font-face {{ font-family: MyHandwriting; src: url('../dist/MyHandwriting-Regular.ttf'); }}
@page {{ size: A4; margin: 16mm 15mm; }}
body {{ font-family: DejaVu Sans, sans-serif; font-size: 9.5pt; color: #222; }}
h1 {{ font-size: 18pt; margin: 0 0 2mm; }} h2 {{ font-size: 11pt; margin: 6mm 0 2mm;
  border-bottom: 1px solid #ccc; padding-bottom: 1mm; color: #444; }}
.hw {{ font-family: MyHandwriting; font-feature-settings: "calt" 1; line-height: 1.55; }}
.s16 {{ font-size: 16pt; }} .s20 {{ font-size: 20pt; }} .s26 {{ font-size: 26pt; }}
.s36 {{ font-size: 36pt; }} .s12 {{ font-size: 12pt; }}
.grid {{ display: flex; flex-wrap: wrap; gap: 1mm; }}
.cell {{ width: 15mm; height: 17mm; border: 1px solid #e3e3e3; text-align: center; }}
.cell .g {{ font-family: MyHandwriting; font-size: 24pt; line-height: 13mm; }}
.cell .l {{ font-size: 6.5pt; color: #999; }}
.note {{ color: #777; font-size: 8pt; }} img {{ max-width: 100%; }}
.pb {{ page-break-before: always; }} .noc {{ font-feature-settings: "calt" 0; }}
"""
    cells = lambda chars: "".join(
        f'<div class="cell"><div class="g">{e(c)}</div><div class="l">U+{ord(c):04X}</div></div>'
        for c in chars)
    h = [f"<!doctype html><html lang='ru'><meta charset='utf-8'><style>{css}</style><body>",
         "<h1>MyHandwriting — specimen</h1>",
         f"<p class='note'>Single-stroke handwriting font built from one scanned sample. "
         f"UPM 1000, x-height {meta['xh']}, cap height {meta['cap']}, slant {meta['slant']:.0f}°, "
         f"pen {meta['pen']} units. Text below is set with the installable TTF; "
         f"contextual alternates (calt) are on.</p>",
         "<h2>Original paragraphs</h2>",
         f"<p class='hw s20'>{e(P1)}</p><p class='hw s20'>{e(P2)}</p>",
         f"<p class='hw s20'>{e(WORDS)}</p>",
         "<h2>New sentences (not in the scan)</h2>",
         "".join(f"<p class='hw s20' style='margin:1mm 0'>{e(t)}</p>" for t in NEW),
         "<h2 class='pb'>Uppercase</h2>", f"<div class='grid'>{cells(up)}</div>",
         "<h2>Lowercase</h2>", f"<div class='grid'>{cells(lo)}</div>",
         "<h2>Digits, punctuation, derived characters</h2>",
         f"<div class='grid'>{cells('0123456789')}</div><div class='grid' style='margin-top:1mm'>"
         f"{cells('.,!?;:—-()«»' + chr(34) + '/№%+')}</div>",
         f"<div class='grid' style='margin-top:1mm'>{cells(chr(39) + '’“”„–…')}</div>",
         "<p class='note'>Last row is derived from sampled marks (not written in the scan).</p>",
         "<h2>Alphabets and numbers in running text</h2>",
         f"<p class='hw s20'>{' '.join(up)}</p><p class='hw s20'>{' '.join(lo)}</p>",
         "<p class='hw s20'>0123456789 &nbsp; 0 1 2 3 4 5 6 7 8 9 &nbsp; .,!?;:—-()«»\"/№%+</p>",
         "<h2>Sizes</h2>",
         "".join(f"<p class='hw s{s}' style='margin:0'>Жду вас в 18:45 у подъезда.</p>"
                 for s in (12, 16, 26, 36)),
         "<h2>Natural variation (contextual alternates)</h2>",
         "<p class='note'>Written variants of и, а, в, у (from words in the paragraphs) and of all "
         "digits (from the first digit row) rotate automatically. Top: calt on; bottom: off.</p>",
         "<p class='hw s26' style='margin:0'>и а в у 1111 2222 1980 2025 мама и папа</p>",
         "<p class='hw s26 noc' style='margin:0'>и а в у 1111 2222 1980 2025 мама и папа</p>",
         "<h2 class='pb'>Scan vs. font</h2>",
         "<p class='note'>Scanned paragraph 1:</p><img src='scan_p1.png'>",
         f"<p class='note'>Same text set in the font:</p><p class='hw s16'>{e(P1)}</p>",
         "<p class='note'>Scanned paragraph 2:</p><img src='scan_p2.png'>",
         f"<p class='note'>Same text set in the font:</p><p class='hw s16'>{e(P2)}</p>",
         "<h2 class='pb'>Single-stroke master (centerline geometry)</h2>",
         "<p class='note'>Typeset directly from the open centerline paths in "
         "MyHandwriting-SingleStroke.svg. Red: hairline, showing that each stroke is a single "
         "open path (no double outlines). Black: the same paths stroked with the default pen.</p>",
         stroke_svg("Съешь же ещё этих мягких французских булок", master, 20, hairline=True),
         "<br>",
         stroke_svg("Съешь же ещё этих мягких французских булок", master, 20),
         "<br>", stroke_svg("да выпей чаю. Жду вас в 18:45!", master, 20, width_units=70),
         "<p class='note'>Above: thicker pen (70 units), the master can be stroked at any width.</p>",
         "<h2 class='pb'>Full single-stroke glyph sheet</h2><p class='note'>MyHandwriting-SingleStroke-Sheet.svg (blue: baseline and x-height; grey: advance width; * = derived).</p>",
         "<img src='../dist/MyHandwriting-SingleStroke-Sheet.svg' style='width:100%;max-height:235mm;object-fit:contain'>",
         "</body></html>"]
    path = os.path.join(B, "specimen.html")
    open(path, "w").write("\n".join(h))
    out = os.path.join(D, "MyHandwriting-Specimen.pdf")
    chrome = os.environ.get("CHROME", "google-chrome")
    subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--allow-file-access-from-files", "--no-pdf-header-footer",
                    f"--print-to-pdf={out}", "file://" + path],
                   check=True, capture_output=True, timeout=180)
    print("wrote", out, os.path.getsize(out))


if __name__ == "__main__":
    main()
