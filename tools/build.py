"""Centerlines (pixel space) -> single-stroke master + installable fonts.

  build/centerlines_px.json  ->  dist/MyHandwriting-SingleStroke.svg       (SVG font, open paths)
                                 dist/MyHandwriting-SingleStroke-Sheet.svg (viewable/editable sheet)
                                 dist/MyHandwriting-Source.ufo             (expanded outlines +
                                                                            centerlines in glyph lib)
                                 dist/MyHandwriting-Regular.ttf / .otf

Usage: python3 tools/build.py [--pen UNITS]
"""
import argparse, json, math, os, sys, shutil
from xml.sax.saxutils import escape, quoteattr

import numpy as np
import pyclipper

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import glyphmap as GM  # noqa: E402
DIST = os.path.join(ROOT, "dist")
FAMILY = "MyHandwriting"

UPM = 1000
XH = 320              # x-height in font units
CAP_RATIO = 2.35      # cap height / x-height as written inside sentences in the scan
DIG_RATIO = 1.9       # digit height / x-height as written inside sentences ("18:45")
SB = 22               # side bearing (in the slanted frame) on each side
PUNCT_SCALE = 0.75    # the punctuation row was written ~1/3 larger than in-sentence marks
WORD_GAP_PX = 34      # median gap between words in the scanned paragraphs

LOWER = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
UPPER = "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ"
DIGIT_NAMES = "zero one two three four five six seven eight nine".split()
PUNCT_NAMES = {
    ".": "period", ",": "comma", "!": "exclam", "?": "question", ";": "semicolon",
    ":": "colon", "—": "emdash", "-": "hyphen", "(": "parenleft", ")": "parenright",
    "«": "guillemotleft", "»": "guillemotright", '"': "quotedbl", "/": "slash",
    "№": "uni2116", "%": "percent", "+": "plus",
}


def gname(ch):
    if ch.isdigit():
        return DIGIT_NAMES[int(ch)]
    if ch in PUNCT_NAMES:
        return PUNCT_NAMES[ch]
    return "uni%04X" % ord(ch)


# ----------------------------------------------------------- geometry utils
def robust_line(xs, ys, tol=3.0, bw=220.0):
    """Baseline as a robust, locally weighted line: the written rows drift and bend."""
    xs, ys = np.asarray(xs, float), np.asarray(ys, float)
    keep = np.ones(len(xs), bool)
    for _ in range(4):
        a, b = np.polyfit(xs[keep], ys[keep], 1)
        r = np.abs(ys - (a * xs + b))
        new = r < max(tol * 3, np.median(r[keep]) * 3)
        if new.sum() < 3 or (new == keep).all():
            break
        keep = new
    X, Y = xs[keep], ys[keep]

    def f(x):
        w = np.exp(-0.5 * ((X - x) / bw) ** 2) + 1e-9
        if (w > 0.05).sum() < 3:
            return a * x + b
        A = np.c_[X - x, np.ones_like(X)] * np.sqrt(w)[:, None]
        sol = np.linalg.lstsq(A, Y * np.sqrt(w), rcond=None)[0]
        return float(sol[1])
    return f


def bbox_px(g):
    a = np.vstack([np.asarray(s["pts"]) for s in g["strokes"]])
    return a[:, 0].min(), a[:, 1].min(), a[:, 0].max(), a[:, 1].max()


# ------------------------------------------------- Schneider bezier fitting
def _bez(ctrl, t):
    t = np.asarray(t)[:, None]; mt = 1 - t
    return mt**3 * ctrl[0] + 3 * mt**2 * t * ctrl[1] + 3 * mt * t**2 * ctrl[2] + t**3 * ctrl[3]


def _bez_d(ctrl, t):
    t = np.asarray(t)[:, None]; mt = 1 - t
    return 3 * mt**2 * (ctrl[1] - ctrl[0]) + 6 * mt * t * (ctrl[2] - ctrl[1]) + 3 * t**2 * (ctrl[3] - ctrl[2])


def _bez_dd(ctrl, t):
    t = np.asarray(t)[:, None]
    return 6 * (1 - t) * (ctrl[2] - 2 * ctrl[1] + ctrl[0]) + 6 * t * (ctrl[3] - 2 * ctrl[2] + ctrl[1])


def _unit(v):
    n = np.hypot(*v)
    return v / n if n > 1e-9 else v


def _gen(pts, u, t1, t2):
    p0, p3 = pts[0], pts[-1]
    A1 = t1[None, :] * (3 * (1 - u)**2 * u)[:, None]
    A2 = t2[None, :] * (3 * (1 - u) * u**2)[:, None]
    C = np.array([[np.sum(A1 * A1), np.sum(A1 * A2)], [np.sum(A1 * A2), np.sum(A2 * A2)]])
    base = _bez(np.array([p0, p0, p3, p3]), u)
    tmp = pts - base
    X = np.array([np.sum(A1 * tmp), np.sum(A2 * tmp)])
    det = C[0, 0] * C[1, 1] - C[0, 1] * C[1, 0]
    seg = np.hypot(*(p3 - p0))
    if abs(det) > 1e-12:
        a1 = (X[0] * C[1, 1] - X[1] * C[0, 1]) / det
        a2 = (C[0, 0] * X[1] - C[1, 0] * X[0]) / det
    else:
        a1 = a2 = seg / 3
    eps = 1e-6 * seg
    if a1 < eps or a2 < eps or a1 > 2.5 * seg or a2 > 2.5 * seg:
        a1 = a2 = seg / 3
    return np.array([p0, p0 + t1 * a1, p3 + t2 * a2, p3])


def _param(pts):
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
    return d / d[-1] if d[-1] > 0 else np.linspace(0, 1, len(pts))


def _maxerr(pts, ctrl, u):
    e = np.sum((_bez(ctrl, u) - pts)**2, axis=1)
    i = int(np.argmax(e))
    return e[i], i


def _reparam(pts, ctrl, u):
    d = _bez(ctrl, u) - pts
    d1, d2 = _bez_d(ctrl, u), _bez_dd(ctrl, u)
    num = np.sum(d * d1, axis=1)
    den = np.sum(d1 * d1, axis=1) + np.sum(d * d2, axis=1)
    out = u - np.where(np.abs(den) > 1e-12, num / np.where(den == 0, 1, den), 0)
    return np.clip(out, 0, 1)


def fit_cubic(pts, t1, t2, err, depth=0):
    if len(pts) == 2 or depth > 12:
        dist = np.hypot(*(pts[-1] - pts[0])) / 3
        return [np.array([pts[0], pts[0] + t1 * dist, pts[-1] + t2 * dist, pts[-1]])]
    u = _param(pts)
    ctrl = _gen(pts, u, t1, t2)
    e, split = _maxerr(pts, ctrl, u)
    if e < err * err:
        return [ctrl]
    if e < (err * 4)**2:
        for _ in range(8):
            u = _reparam(pts, ctrl, u)
            ctrl = _gen(pts, u, t1, t2)
            e, split = _maxerr(pts, ctrl, u)
            if e < err * err:
                return [ctrl]
    split = min(max(split, 1), len(pts) - 2)
    tc = _unit(pts[split - 1] - pts[split + 1])
    return fit_cubic(pts[:split + 1], t1, tc, err, depth + 1) + \
        fit_cubic(pts[split:], -tc, t2, err, depth + 1)


def fit_path(pts, corners, closed, err):
    """Polyline -> list of cubic segments; corners stay sharp (cusps)."""
    pts = np.asarray(pts, float)
    if closed:
        pts = np.vstack([pts, pts[:1]])
    if len(pts) < 3 or np.hypot(*(pts[-1] - pts[0])) < 1e-6 and not closed:
        p, q = pts[0], pts[-1]
        return [np.array([p, p + (q - p) / 3, p + 2 * (q - p) / 3, q])]
    cuts = sorted(set([0, len(pts) - 1] + [c for c in corners if 0 < c < len(pts) - 1]))
    segs = []
    for a, b in zip(cuts[:-1], cuts[1:]):
        part = pts[a:b + 1]
        if len(part) < 2:
            continue
        k = min(4, len(part) - 1)
        t1 = _unit(part[k] - part[0])
        t2 = _unit(part[-1 - k] - part[-1])
        if closed and len(cuts) == 2:   # smooth loop: matching tangents at the seam
            t1 = _unit(pts[min(4, len(pts) - 1)] - pts[-min(5, len(pts))])
            t2 = -t1
        segs += fit_cubic(part, t1, t2, err)
    return segs


def flatten(segs, step=4.0):
    out = [segs[0][0]]
    for c in segs:
        L = np.hypot(*(c[1] - c[0])) + np.hypot(*(c[2] - c[1])) + np.hypot(*(c[3] - c[2]))
        n = max(2, int(L / step))
        out.extend(_bez(c, np.linspace(0, 1, n + 1)[1:]))
    return np.array(out)


def d_attr(strokes, fmt="{:.1f}"):
    parts = []
    for s in strokes:
        segs = s["segs"]
        f = lambda p: fmt.format(p[0]) + " " + fmt.format(p[1])
        d = "M" + f(segs[0][0])
        for c in segs:
            d += " C" + f(c[1]) + " " + f(c[2]) + " " + f(c[3])
        if s["closed"]:
            d += " Z"
        parts.append(d)
    return " ".join(parts)


# ----------------------------------------------------------- outline expansion
def corners_of_polygon(poly, reach=6.0, thresh=38):
    n = len(poly)
    d = np.hypot(*np.diff(np.vstack([poly, poly[:1]]), axis=0).T)
    step = max(np.median(d), 1e-3)
    k = max(1, int(round(reach / step)))
    ang = np.zeros(n)
    for i in range(n):
        u = poly[i] - poly[(i - k) % n]; v = poly[(i + k) % n] - poly[i]
        nu, nv = np.hypot(*u), np.hypot(*v)
        if nu and nv:
            ang[i] = math.degrees(math.acos(np.clip(np.dot(u, v) / nu / nv, -1, 1)))
    out = []
    for i in range(n):
        win = [ang[(i + j) % n] for j in range(-k, k + 1)]
        if ang[i] > thresh and ang[i] == max(win):
            out.append(i)
    return out


def resample_closed(poly, step):
    p = np.vstack([poly, poly[:1]])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(p, axis=0).T))]
    t = np.arange(0, d[-1], step)
    return np.c_[np.interp(t, d, p[:, 0]), np.interp(t, d, p[:, 1])]


def expand(strokes, pen):
    """Stroke the centerlines with a round pen -> union of filled contours."""
    SC = 64.0
    co = pyclipper.PyclipperOffset(miter_limit=2.0, arc_tolerance=0.25 * SC)
    for s in strokes:
        poly = flatten(s["segs"], step=3.0)
        path = [(int(round(x * SC)), int(round(y * SC))) for x, y in poly]
        if s["closed"]:
            co.AddPath(path[:-1], pyclipper.JT_ROUND, pyclipper.ET_CLOSEDLINE)
        else:
            if len(set(path)) < 2:
                path = [path[0], (path[0][0] + 1, path[0][1])]
            co.AddPath(path, pyclipper.JT_ROUND, pyclipper.ET_OPENROUND)
    res = co.Execute(pen / 2 * SC)
    contours = []
    for c in res:
        a = np.asarray(c, float) / SC
        if abs(pyclipper.Area(c)) / SC / SC < 4:
            continue
        # fit smooth cubics to the offset polygon; the start is moved to a corner
        a = resample_closed(a, 2.0)
        cs = corners_of_polygon(a)
        if cs:
            a = np.roll(a, -cs[0], axis=0)
            cs = [(c - cs[0]) % len(a) for c in cs]
        segs = fit_path(a, cs, True, err=0.9)
        contours.append(segs)
    return contours


# ------------------------------------------------------------------ main build
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pen", type=float, default=None, help="pen width in font units")
    args = ap.parse_args()

    data = json.load(open(os.path.join(ROOT, "build", "centerlines_px.json")))
    G = data["glyphs"]
    rows = {}
    for g in G:
        rows.setdefault(g["row"], []).append(g)

    # --- per-row baselines and size in pixels
    def fit_row(lst, base_set, top_set):
        b = [(0.5 * (bb[0] + bb[2]), bb[3]) for g in lst if g["char"] in base_set
             for bb in [bbox_px(g)]]
        line = robust_line(*zip(*b))
        tops = [line(0.5 * (bb[0] + bb[2])) - bb[1] for g in lst if g["char"] in top_set
                for bb in [bbox_px(g)]]
        return line, float(np.median(tops))

    lc_base = set("аегжиклмнопстхчшъыьэюя")
    lc_top = set("аегжиклмнопстхчшэюя")
    uc_base = set("АБВГЕЖЗИКЛМНОПСТХЧШЪЫЬЭЮЯ")
    uc_top = set("АБВГДЕЖЗИКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ")
    digits = set("0123456789")
    line, xh_px = {}, {}
    for r in ("lc1", "lc2"):
        line[r], xh_px[r] = fit_row(rows[r], lc_base, lc_top)
    for r in ("uc1", "uc2"):
        line[r], xh_px[r] = fit_row(rows[r], uc_base, uc_top)
    for r in ("dig1", "dig2"):
        line[r], xh_px[r] = fit_row(rows[r], digits, digits)
    xh_lc = float(np.mean([xh_px["lc1"], xh_px["lc2"]]))
    cap_px = float(np.mean([xh_px["uc1"], xh_px["uc2"]]))
    k_lc = XH / xh_lc
    print(f"x-height {xh_lc:.1f}px  cap {cap_px:.1f}px  (alphabet ratio {cap_px / xh_lc:.2f}, "
          f"used {CAP_RATIO})  digits {xh_px['dig2']:.1f}/{xh_px['dig1']:.1f}px")
    CAP = round(CAP_RATIO * XH)
    DIGH = round(DIG_RATIO * XH)
    k = {"lc1": k_lc, "lc2": k_lc, "punct": k_lc * PUNCT_SCALE,
         "uc1": CAP / cap_px, "uc2": CAP / cap_px,
         "dig1": DIGH / xh_px["dig1"], "dig2": DIGH / xh_px["dig2"]}
    # У, Ф, Д end on the baseline in this sample (no descender)
    snap_set = {"lc": lc_base, "uc": uc_base | set("ДУФ"), "dig": digits, "dig1": digits}
    pen = args.pen or round(data["pen_width_px"] * k_lc)

    # --- slant from near-vertical stroke pieces of the letters
    angs, wts = [], []
    for g in G:
        if g["group"] not in ("lc", "uc"):
            continue
        for s in g["strokes"]:
            a = np.asarray(s["pts"])[::4]
            v = np.diff(a, axis=0)
            L = np.hypot(*v.T)
            ang = np.degrees(np.arctan2(v[:, 0], -v[:, 1]))  # 0 = vertical, + = leaning right
            ang = (ang + 90) % 180 - 90
            m = np.abs(ang) < 45
            angs += list(ang[m]); wts += list(L[m])
    order = np.argsort(angs); cw = np.cumsum(np.asarray(wts)[order])
    slant = float(np.asarray(angs)[order][np.searchsorted(cw, cw[-1] / 2)])
    tan = math.tan(math.radians(slant))
    print(f"slant {slant:.1f} deg, pen {pen} units")

    # --- place every glyph in font units
    defaults = {}
    for g in G:
        if not g["alt"]:
            defaults[g["char"]] = g

    def to_units(g):
        x0, y0, x1, y1 = bbox_px(g)
        xc = 0.5 * (x0 + x1)
        r = g["row"]
        if r == "text":
            d = defaults[g["char"]]
            dx0, dy0, dx1, dy1 = bbox_px(d)
            kd = k[d["row"]]
            ka = kd * float(np.clip((dy1 - dy0) / (y1 - y0), 0.85, 1.35))
            top_units = (line[d["row"]](0.5 * (dx0 + dx1)) - dy0) * kd
            return lambda p: ((p[0] - xc) * ka, top_units - (p[1] - y0) * ka)
        kk = k[r]
        if r == "punct":
            ch = g["char"]
            h = (y1 - y0) * kk
            bottom = {
                ".": 0, "!": 0, "?": 0, ":": 0, "№": 0, "%": 0,
                ",": 0.12 * XH - h, ";": 0.12 * XH - 0.62 * h,
                "—": 0.42 * XH - h / 2, "-": 0.42 * XH - h / 2, "+": 0.45 * XH - h / 2,
                "«": 0.45 * XH - h / 2, "»": 0.45 * XH - h / 2,
                '"': 0.98 * CAP - h, "/": -0.18 * XH,
                "(": 0.36 * CAP - h / 2, ")": 0.36 * CAP - h / 2,
            }[ch]
            return lambda p: ((p[0] - xc) * kk, bottom + (y1 - p[1]) * kk)
        base = line[r](xc)
        if g["char"] in GM.BASELINE and r.startswith("lc") == g["char"].islower():
            base = GM.BASELINE[g["char"]]
        elif g["char"] in snap_set[g["group"]]:
            # sits on the line in the sample: keep only a little of the row's bounce
            base = 0.8 * y1 + 0.2 * base
        return lambda p: ((p[0] - xc) * kk, (base - p[1]) * kk)

    glyphs = {}
    alt_count = {}
    for g in G:
        ch = g["char"]
        if g["alt"]:
            n = alt_count[ch] = alt_count.get(ch, 0) + 1
            name = gname(ch) + (".alt" if ch.isdigit() else f".alt{n}")
            uni = None
        else:
            name, uni = gname(ch), ord(ch)
        T = to_units(g)
        strokes = []
        for s in g["strokes"]:
            pts = np.array([T(p) for p in s["pts"]])
            segs = fit_path(pts, s["corners"], s["closed"], err=4.0)
            strokes.append(dict(segs=segs, closed=s["closed"]))
        glyphs[name] = dict(name=name, char=ch, uni=uni, strokes=strokes, src=g)

    # --- characters derived from sampled ones (flagged in README)
    def derive(name, uni, src, xf=lambda p: p, keep=None, char=None):
        st = glyphs[src]["strokes"]
        if keep is not None:
            st = [st[i] for i in keep]
        glyphs[name] = dict(name=name, char=char or chr(uni), uni=uni, derived=src,
                            strokes=[dict(closed=s["closed"], segs=[np.array([xf(p) for p in c])
                                                                    for c in s["segs"]])
                                     for s in st])
    qd = glyphs["quotedbl"]["strokes"]
    derive("quotesingle", 0x27, "quotedbl", keep=[0])
    derive("quoteright", 0x2019, "quotedbl", keep=[1])
    derive("quotedblright", 0x201D, "quotedbl")
    derive("quotedblleft", 0x201C, "quotedbl", xf=lambda p: (-p[0], 2 * 0.86 * CAP - p[1]))
    derive("quotedblbase", 0x201E, "quotedbl", xf=lambda p: (p[0], p[1] - 0.86 * CAP))
    derive("endash", 0x2013, "emdash", xf=lambda p: (p[0] * 0.55, p[1]))
    pd = glyphs["period"]["strokes"]
    glyphs["ellipsis"] = dict(name="ellipsis", char="…", uni=0x2026, derived="period", strokes=[
        dict(closed=s["closed"], segs=[c + [dx, 0] for c in s["segs"]])
        for dx in (0, 0.55 * XH, 1.1 * XH) for s in pd])
    glyphs[".notdef"] = dict(name=".notdef", char=None, uni=None, strokes=[dict(closed=True, segs=[
        np.array([a, a + (b - a) / 3, a + 2 * (b - a) / 3, b]) for a, b in
        zip(*[np.array(q, float) for q in ([[0, 0], [300, 0], [300, CAP], [0, CAP]],
                                           [[300, 0], [300, CAP], [0, CAP], [0, 0]])])])])

    # --- spacing in the slanted frame
    for gl in glyphs.values():
        pts = np.vstack([flatten(s["segs"]) for s in gl["strokes"]])
        sx = pts[:, 0] - pts[:, 1] * tan
        left, right = sx.min() - pen / 2, sx.max() + pen / 2
        dx = SB - left
        for s in gl["strokes"]:
            s["segs"] = [c + [dx, 0] for c in s["segs"]]
        gl["adv"] = int(round(right - left + 2 * SB))
    space_adv = int(round(WORD_GAP_PX * k_lc - 2 * SB))

    # --- vertical metrics from real extents (never clip)
    allpts = np.vstack([flatten(s["segs"]) for gl in glyphs.values() for s in gl["strokes"]])
    ymax = int(math.ceil(allpts[:, 1].max() + pen / 2 + 10))
    ymin = int(math.floor(allpts[:, 1].min() - pen / 2 - 10))
    asc = max(ymax, CAP + 150); desc = min(ymin, -330)
    print(f"glyphs {len(glyphs)}  y-extent {ymin}..{ymax}  space {space_adv}")

    os.makedirs(DIST, exist_ok=True)
    meta = dict(upm=UPM, xh=XH, cap=CAP, pen=pen, slant=slant, asc=asc, desc=desc,
                space=space_adv, k_lc=k_lc)
    write_master_json(glyphs, meta)
    write_svg_font(glyphs, meta)
    write_sheet(glyphs, meta)
    ufo = write_ufo(glyphs, meta)
    compile_fonts(ufo)


def ordered(glyphs):
    names = [".notdef"] + [gname(c) for c in UPPER + LOWER] + DIGIT_NAMES + \
        [gname(c) for c in PUNCT_NAMES] + \
        ["quotesingle", "quoteright", "quotedblleft", "quotedblright", "quotedblbase",
         "endash", "ellipsis"]
    names += sorted(n for n in glyphs if n not in names)
    return [glyphs[n] for n in names if n in glyphs]


def write_master_json(glyphs, meta):
    out = dict(meta=meta, glyphs={})
    for gl in ordered(glyphs):
        out["glyphs"][gl["name"]] = dict(
            char=gl["char"], unicode=gl["uni"], advance=gl["adv"], derived=gl.get("derived"),
            strokes=[dict(closed=s["closed"], cubic=np.round(np.array(s["segs"]), 2).tolist())
                     for s in gl["strokes"]])
    json.dump(out, open(os.path.join(ROOT, "build", "master.json"), "w"), ensure_ascii=False)


def write_svg_font(glyphs, meta):
    """SVG 1.1 font with open single-line glyphs (Inkscape "Hershey Text" format)."""
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<svg xmlns="http://www.w3.org/2000/svg" version="1.1">',
         f'<metadata>{FAMILY} single-stroke master. Glyph paths are open centerlines '
         f'(stroke them, do not fill). Units per em {UPM}; pen width {meta["pen"]}.</metadata>',
         '<defs>',
         f'<font id="{FAMILY}" horiz-adv-x="{meta["space"]}">',
         f'<font-face font-family="{FAMILY}" units-per-em="{UPM}" ascent="{meta["asc"]}" '
         f'descent="{meta["desc"]}" x-height="{XH}" cap-height="{meta["cap"]}" '
         f'slope="{-meta["slant"]:.1f}"/>',
         f'<missing-glyph horiz-adv-x="{glyphs[".notdef"]["adv"]}" d={quoteattr(d_attr(glyphs[".notdef"]["strokes"]))}/>',
         f'<glyph unicode=" " glyph-name="space" horiz-adv-x="{meta["space"]}"/>']
    for gl in ordered(glyphs):
        if gl["name"] == ".notdef":
            continue
        u = f' unicode={quoteattr(gl["char"])}' if gl["uni"] else ""
        L.append(f'<glyph{u} glyph-name="{gl["name"]}" horiz-adv-x="{gl["adv"]}" '
                 f'd={quoteattr(d_attr(gl["strokes"]))}/>')
    L += ['</font>', '</defs>', '</svg>']
    open(os.path.join(DIST, f"{FAMILY}-SingleStroke.svg"), "w").write("\n".join(L))


def write_sheet(glyphs, meta):
    """Viewable sheet: one group per glyph, stroke-only paths, baseline guides."""
    cols, cw, ch = 10, 1300, 1700
    gl = ordered(glyphs)
    rows = (len(gl) + cols - 1) // cols
    W, H = cols * cw, rows * ch
    pen = meta["pen"]
    L = ['<?xml version="1.0" encoding="UTF-8"?>',
         f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" '
         f'width="{W / 50:.0f}mm" height="{H / 50:.0f}mm" viewBox="0 0 {W} {H}">',
         f'<title>{FAMILY} single-stroke master sheet</title>',
         '<g inkscape:groupmode="layer" inkscape:label="guides" style="stroke:#9cc3e6;stroke-width:4;fill:none">']
    body = [f'<g inkscape:groupmode="layer" inkscape:label="glyphs" style="fill:none;stroke:#000;'
            f'stroke-width:{pen};stroke-linecap:round;stroke-linejoin:round">']
    labels = ['<g inkscape:groupmode="layer" inkscape:label="labels" '
              'style="font-family:DejaVu Sans,sans-serif;font-size:90px;fill:#c03030">']
    for i, g in enumerate(gl):
        ox, oy = (i % cols) * cw + 200, (i // cols) * ch + 1150   # baseline origin
        L.append(f'<path d="M{ox - 150} {oy} h{cw - 100} M{ox - 150} {oy - XH} h{cw - 100}" />')
        L.append(f'<path d="M{ox} {oy - 1000} v1400 M{ox + g["adv"]} {oy - 1000} v1400" '
                 f'style="stroke:#e0e0e0"/>')
        body.append(f'<g id="{g["name"]}" inkscape:label={quoteattr(g["char"] or g["name"])} '
                    f'transform="translate({ox} {oy}) scale(1 -1)">'
                    f'<path d={quoteattr(d_attr(g["strokes"]))}/></g>')
        lab = (g["char"] or "") + "  " + g["name"] + (" *" if g.get("derived") else "")
        labels.append(f'<text x="{ox - 140}" y="{oy - 1020}">{escape(lab)}</text>')
    L += ['</g>'] + body + ['</g>'] + labels + ['</g>', '</svg>']
    open(os.path.join(DIST, f"{FAMILY}-SingleStroke-Sheet.svg"), "w").write("\n".join(L))


def feature_text(glyphs):
    lower = [gname(c) for c in LOWER]
    setA = [n for i, n in enumerate(lower) if i % 2 == 0] + DIGIT_NAMES
    setB = [n for i, n in enumerate(lower) if i % 2 == 1] + ["space"]
    alt1 = [n[:-5] for n in glyphs if n.endswith(".alt1")]
    alt2 = [n[:-5] for n in glyphs if n.endswith(".alt2")]
    dig = [n for n in DIGIT_NAMES if n + ".alt" in glyphs]
    f = ["# Variation without randomness: which written variant appears depends on the",
         "# previous glyph, so repeated letters/digits do not look stamped.",
         f"@setA = [{' '.join(setA)}];", f"@setB = [{' '.join(setB)}];",
         f"@dig = [{' '.join(dig)}];", f"@digAlt = [{' '.join(n + '.alt' for n in dig)}];",
         f"@b1 = [{' '.join(alt1)}];", f"@a1 = [{' '.join(n + '.alt1' for n in alt1)}];",
         f"@b2 = [{' '.join(alt2)}];", f"@a2 = [{' '.join(n + '.alt2' for n in alt2)}];",
         "feature calt {",
         "  sub @setB @b2' by @a2;", "  sub @setA @b1' by @a1;", "  sub @setA @dig' by @digAlt;",
         "} calt;",
         "feature salt {", "  sub @b1 by @a1;", "  sub @dig by @digAlt;", "} salt;"]
    return "\n".join(f) + "\n"


def write_ufo(glyphs, meta):
    import ufoLib2
    from fontTools.pens.pointPen import SegmentToPointPen
    path = os.path.join(DIST, f"{FAMILY}-Source.ufo")
    if os.path.exists(path):
        shutil.rmtree(path)
    f = ufoLib2.Font()
    i = f.info
    i.familyName, i.styleName = FAMILY, "Regular"
    i.versionMajor, i.versionMinor = 1, 0
    i.unitsPerEm, i.xHeight, i.capHeight = UPM, XH, meta["cap"]
    i.ascender, i.descender = meta["cap"] + 150, -330
    i.italicAngle = -round(meta["slant"], 1)
    i.openTypeHheaAscender, i.openTypeHheaDescender = meta["asc"], meta["desc"]
    i.openTypeHheaLineGap = 0
    i.openTypeOS2TypoAscender, i.openTypeOS2TypoDescender = meta["asc"], meta["desc"]
    i.openTypeOS2TypoLineGap = 0
    i.openTypeOS2WinAscent, i.openTypeOS2WinDescent = meta["asc"], -meta["desc"]
    i.openTypeOS2Type = []                       # installable embedding
    i.openTypeOS2CodePageRanges = [2]  # bit 2 = cp1251 Cyrillic
    i.openTypeOS2VendorID = "NONE"
    i.openTypeNameDescription = ("Personal Russian handwriting, extracted as single-stroke "
                                 "centerlines from a scanned sample and stroked with a round pen.")
    i.postscriptUnderlinePosition, i.postscriptUnderlineThickness = -150, meta["pen"]
    i.copyright = "Handwriting and font: the owner of the handwriting sample."
    order = [".notdef", "space", "uni00A0"]
    sp = f.newGlyph("space"); sp.width = meta["space"]; sp.unicodes = [0x20]
    nb = f.newGlyph("uni00A0"); nb.width = meta["space"]; nb.unicodes = [0xA0]
    for gl in ordered(glyphs):
        g = f.newGlyph(gl["name"])
        g.width = gl["adv"]
        if gl["uni"]:
            g.unicodes = [gl["uni"]]
        pen = SegmentToPointPen(g.getPointPen())
        for contour in expand(gl["strokes"], meta["pen"]):
            pen.moveTo(tuple(map(float, np.round(contour[0][0], 2))))
            for c in contour:
                pen.curveTo(*[tuple(map(float, np.round(p, 2))) for p in c[1:]])
            pen.closePath()
        # the single-stroke master travels with the source
        g.lib["com.myhandwriting.centerline"] = d_attr(gl["strokes"])
        g.lib["com.myhandwriting.closed"] = [s["closed"] for s in gl["strokes"]]
        if gl.get("derived"):
            g.lib["com.myhandwriting.derivedFrom"] = gl["derived"]
        if gl["name"] not in order:
            order.append(gl["name"])
    f.glyphOrder = order
    f.lib["public.glyphOrder"] = order
    f.lib["com.myhandwriting.penWidth"] = meta["pen"]
    f.features.text = feature_text(glyphs)
    f.save(path)
    return path


def compile_fonts(path):
    import ufoLib2
    from ufo2ft import compileTTF, compileOTF
    ufo = ufoLib2.Font.open(path)
    compileTTF(ufo, removeOverlaps=False).save(os.path.join(DIST, f"{FAMILY}-Regular.ttf"))
    ufo = ufoLib2.Font.open(path)
    compileOTF(ufo, removeOverlaps=False).save(os.path.join(DIST, f"{FAMILY}-Regular.otf"))
    print("wrote", os.listdir(DIST))


if __name__ == "__main__":
    main()
