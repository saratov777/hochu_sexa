"""Quality checks for the generated fonts and single-stroke master. Exit code 1 on failure."""
import hashlib, os, re, shutil, subprocess, sys
import xml.etree.ElementTree as ET
from fontTools.ttLib import TTFont
from fontTools.pens.recordingPen import RecordingPen
from fontTools.pens.boundsPen import BoundsPen

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "dist")
UP = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
LO = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
REQUIRED = UP + LO + "0123456789" + " .,!?;:—-()«»\"/№%+"
fails = []


def check(ok, msg):
    print(("PASS " if ok else "FAIL ") + msg)
    if not ok:
        fails.append(msg)


def outline_hash(gs, name):
    p = RecordingPen(); gs[name].draw(p)
    return hashlib.md5(repr(p.value).encode()).hexdigest()


for fn in ("MyHandwriting-Regular.ttf", "MyHandwriting-Regular.otf"):
    f = TTFont(os.path.join(D, fn))
    cmap, gs = f.getBestCmap(), f.getGlyphSet()
    missing = [c for c in REQUIRED if ord(c) not in cmap]
    check(not missing, f"{fn}: all {len(REQUIRED)} required characters mapped {missing or ''}")
    latin = [c for c in UP + LO if not cmap[ord(c)].startswith("uni04")]
    check(not latin, f"{fn}: Cyrillic code points use dedicated Cyrillic glyphs")
    same = [u for u, l in zip(UP, LO) if outline_hash(gs, cmap[ord(u)]) == outline_hash(gs, cmap[ord(l)])]
    check(not same, f"{fn}: uppercase and lowercase outlines are distinct")

    def ncont(c):
        p = RecordingPen(); gs[cmap[ord(c)]].draw(p)
        return sum(1 for op, _ in p.value if op in ("closePath", "endPath"))
    check(ncont("ё") > ncont("е") and ncont("Ё") > ncont("Е"),
          f"{fn}: ё/Ё carry diacritic dots (contours е={ncont('е')} ё={ncont('ё')} "
          f"Е={ncont('Е')} Ё={ncont('Ё')})")
    os2, hhea = f["OS/2"], f["hhea"]
    clipped = []
    for g in f.getGlyphOrder():
        bp = BoundsPen(gs); gs[g].draw(bp)
        if bp.bounds and (bp.bounds[3] > os2.usWinAscent or bp.bounds[1] < -os2.usWinDescent):
            clipped.append(g)
    check(not clipped, f"{fn}: no glyph exceeds winAscent/winDescent {clipped or ''}")
    print(f"INFO {fn}: vertical metrics asc={hhea.ascent} desc={hhea.descent} "
          f"win={os2.usWinAscent}/{os2.usWinDescent}")
    check(os2.fsType == 0, f"{fn}: fsType=0 (installable embedding)")
    check(bool(os2.ulCodePageRange1 & (1 << 2)), f"{fn}: cp1251 Cyrillic code page bit set")
    feats = {fr.FeatureTag for fr in f["GSUB"].table.FeatureList.FeatureRecord}
    check({"calt", "salt"} <= feats, f"{fn}: GSUB features {sorted(feats)}")

# OpenType Sanitizer (same validator browsers use)
try:
    import ots
    for fn in ("MyHandwriting-Regular.ttf", "MyHandwriting-Regular.otf"):
        r = ots.sanitize(os.path.join(D, fn), os.devnull, capture_output=True)
        check(r.returncode == 0, f"OTS sanitizer accepts {fn} {r.stderr.decode()[:200] if r.returncode else ''}")
except ImportError:
    print("SKIP ots not installed")

# fontconfig: install into the user font dir and look it up
fdir = os.path.expanduser("~/.local/share/fonts")
os.makedirs(fdir, exist_ok=True)
shutil.copy(os.path.join(D, "MyHandwriting-Regular.ttf"), fdir)
subprocess.run(["fc-cache", "-f", fdir], capture_output=True)
q = subprocess.run(["fc-list", ":family=MyHandwriting", "family", "style", "lang"],
                   capture_output=True, text=True).stdout
check("MyHandwriting" in q and re.search(r"\bru\b", q) is not None,
      "installed font is found by fontconfig and covers lang=ru")

# single-stroke master: every glyph is open/centerline strokes, never filled outlines
svg = ET.parse(os.path.join(D, "MyHandwriting-SingleStroke.svg")).getroot()
ns = "{http://www.w3.org/2000/svg}"
glyphs = svg.findall(f".//{ns}glyph")
n_open = n_closed = 0
for g in glyphs:
    for sub in re.findall(r"M[^M]*", g.get("d", "")):
        if sub.strip().endswith("Z"):
            n_closed += 1
        else:
            n_open += 1
uni = {g.get("unicode") for g in glyphs}
check(all(c in uni for c in REQUIRED.strip()), "single-stroke SVG font covers all required characters")
check(n_open > 5 * n_closed, f"single-stroke master: {n_open} open strokes, {n_closed} closed loops "
      "(loops are drawn ovals such as о/0, not outline contours)")
# a traced outline would give a pair of near-parallel closed contours per stroke; the master
# has as many paths as pen strokes, and the TTF has more contours only where loops create holes
print(f"\n{len(fails)} failure(s)")
sys.exit(1 if fails else 0)
