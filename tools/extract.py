"""Scan -> single-stroke centerlines (pixel space).

Pipeline per glyph:
  ink ownership -> 4x cubic upsample -> threshold -> fill pinholes ->
  skeletonize -> pixel graph -> prune spurs -> pair edges through junctions by
  direction continuity (pen keeps going straight through crossings) ->
  smooth polylines + corner (cusp) indices.

Output: build/centerlines_px.json
"""
import json, math, os, sys
import cv2
import numpy as np
from scipy import ndimage
from skimage.morphology import skeletonize, remove_small_holes

sys.path.insert(0, os.path.dirname(__file__))
import glyphmap as GM

S = 4             # upsampling factor
INK = 200         # gray threshold for ink (paper is ~223)
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def load():
    g = cv2.imread(os.path.join(ROOT, GM.SCAN), 0)
    ink = g < INK
    # components on a dilated mask so faint broken strokes stay together
    dil = cv2.dilate(ink.astype(np.uint8), np.ones((3, 3), np.uint8))
    lab, n = ndimage.label(dil, structure=np.ones((3, 3)))
    lab = lab * ink
    idx = np.arange(1, n + 1)
    area = ndimage.sum(ink, lab, idx)
    cy, cx = np.array(ndimage.center_of_mass(ink, lab, idx)).T if n else ([], [])
    comps = [(i, a, x, y) for i, a, x, y in zip(idx, area, cx, cy)]
    return g, lab, comps


def glyph_mask(g, lab, comps, box, min_area=3):
    x0, y0, x1, y1 = box[:4]
    if len(box) > 4 and box[4] == "clip":   # touching neighbours: hard clip
        m = np.zeros(lab.shape, bool)
        m[y0:y1, x0:x1] = lab[y0:y1, x0:x1] > 0
    else:
        keep = [i for i, a, x, y in comps if a >= min_area and x0 <= x <= x1 and y0 <= y <= y1]
        # owned components may extend beyond the box
        m = np.isin(lab, keep)
    ys, xs = np.nonzero(m)
    if len(xs) == 0:
        raise ValueError(f"no ink in box {box}")
    P = 4
    X0, Y0, X1, Y1 = xs.min() - P, ys.min() - P, xs.max() + P + 1, ys.max() + P + 1
    crop = g[Y0:Y1, X0:X1].astype(np.float32)
    own = m[Y0:Y1, X0:X1]
    # grey ramp only around owned ink so anti-aliasing survives the upsample
    near = cv2.dilate(own.astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    crop[~near] = 255
    return crop, (X0, Y0)


def skeleton_of(crop):
    up = cv2.resize(crop, None, fx=S, fy=S, interpolation=cv2.INTER_CUBIC)
    up = cv2.GaussianBlur(up, (0, 0), S * 0.35)
    m = up < 195
    m = cv2.morphologyEx(m.astype(np.uint8), cv2.MORPH_CLOSE,
                         cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))) > 0
    m = remove_small_holes(m, max_size=int((S * 1.6) ** 2))
    lab, n = ndimage.label(m, structure=np.ones((3, 3)))
    if n > 1:  # drop tiny noise blobs (but keep dots: >= ~2px of original ink)
        sizes = ndimage.sum(m, lab, range(1, n + 1))
        for i, sz in enumerate(sizes, 1):
            if sz < 3 * S * S:
                m[lab == i] = False
    sk = skeletonize(m)
    # stroke width estimate: area / skeleton length
    width = m.sum() / max(sk.sum(), 1) / S
    return m, sk, width


# ---------------------------------------------------------------- graph
def build_graph(sk):
    pts = set(zip(*np.nonzero(sk)))
    def nb(p):
        return [(p[0] + dy, p[1] + dx) for dy, dx in N8 if (p[0] + dy, p[1] + dx) in pts]
    deg = {p: len(nb(p)) for p in pts}
    nodepix = {p for p in pts if deg[p] != 2}
    # cluster adjacent node pixels
    node_of, nodes = {}, []
    for p in nodepix:
        if p in node_of:
            continue
        stack, mem = [p], []
        node_of[p] = len(nodes)
        while stack:
            q = stack.pop(); mem.append(q)
            for r in nb(q):
                if r in nodepix and r not in node_of:
                    node_of[r] = len(nodes); stack.append(r)
        c = np.mean(mem, axis=0)
        nodes.append((c[0], c[1]))
    edges, seen = [], set()
    for p in nodepix:
        for q in nb(p):
            if q in nodepix:
                if node_of[q] != node_of[p]:
                    key = tuple(sorted([p, q]))
                    if key not in seen:
                        seen.add(key)
                        edges.append([node_of[p], node_of[q], [p, q]])
                continue
            if q in seen:
                continue
            path, prev, cur = [p, q], p, q
            seen.add(q)
            while True:
                nxt = [r for r in nb(cur) if r != prev and r not in path[-3:]]
                nodehit = [r for r in nxt if r in nodepix]
                if nodehit:
                    path.append(nodehit[0]); end = node_of[nodehit[0]]; break
                nxt = [r for r in nxt if r not in seen]
                if not nxt:
                    end = None; break
                prev, cur = cur, nxt[0]
                seen.add(cur); path.append(cur)
            if end is None:
                continue
            edges.append([node_of[p], end, path])
    # isolated cycles (e.g. a lone "о")
    for p in pts:
        if p in nodepix or p in seen:
            continue
        path, prev, cur = [p], None, p
        seen.add(p)
        while True:
            nxt = [r for r in nb(cur) if r != prev and r not in seen]
            if not nxt:
                break
            prev, cur = cur, nxt[0]; seen.add(cur); path.append(cur)
        if len(path) > 6:
            nid = len(nodes); nodes.append(path[0])
            edges.append([nid, nid, path + [path[0]]])
    return nodes, edges


def plen(path):
    a = np.asarray(path, float)
    return float(np.sum(np.hypot(*np.diff(a, axis=0).T))) if len(a) > 1 else 0.0


def prune(nodes, edges, spur):
    changed = True
    while changed:
        changed = False
        deg = [0] * len(nodes)
        for a, b, _ in edges:
            deg[a] += 1; deg[b] += 1
        for i, (a, b, path) in enumerate(edges):
            L = plen(path)
            if a == b and L < spur * 2.2:          # tiny blob loop
                edges.pop(i); changed = True; break
            tip = (deg[a] == 1) != (deg[b] == 1)
            if tip and L < spur and (deg[a] >= 3 or deg[b] >= 3):
                edges.pop(i); changed = True; break
        if not changed:  # tiny double edges between same pair -> keep one
            for i in range(len(edges)):
                for j in range(i + 1, len(edges)):
                    ei, ej = edges[i], edges[j]
                    if {ei[0], ei[1]} == {ej[0], ej[1]} and ei[0] != ei[1] and \
                            plen(ei[2]) + plen(ej[2]) < spur * 2.5:
                        edges.pop(j if plen(ej[2]) >= plen(ei[2]) else i)
                        changed = True; break
                if changed:
                    break
    return edges


def end_dir(path, at_start, reach):
    a = np.asarray(path if at_start else path[::-1], float)
    d = np.cumsum(np.r_[0, np.hypot(*np.diff(a, axis=0).T)])
    k = min(np.searchsorted(d, reach), len(a) - 1)
    v = a[k] - a[0]
    n = np.hypot(*v)
    return v / n if n > 0 else v


def chain(nodes, edges, reach):
    """Pair edge-ends at each node by continuity and walk them into strokes."""
    ends = {}  # node -> list of (edge, is_start)
    for e, (a, b, _) in enumerate(edges):
        ends.setdefault(a, []).append((e, True))
        ends.setdefault(b, []).append((e, False))
    partner = {}
    for n, lst in ends.items():
        dirs = {k: end_dir(edges[k[0]][2], k[1], reach) for k in lst}
        free = list(lst)
        cands = sorted(((float(np.dot(dirs[u], dirs[v])), u, v)
                        for i, u in enumerate(free) for v in free[i + 1:]))
        used = set()
        for dot, u, v in cands:
            if u in used or v in used or u[0] == v[0] and len(lst) > 2:
                continue
            if len(lst) == 2 or dot < -0.2:
                partner[u], partner[v] = v, u
                used |= {u, v}
    strokes, done = [], set()

    def walk(e, from_start):
        pts = []
        while e not in done:
            done.add(e)
            path = edges[e][2] if from_start else edges[e][2][::-1]
            pts.extend(path)
            nxt = partner.get((e, not from_start))
            if nxt is None:
                break
            e, from_start = nxt[0], nxt[1]
        return pts

    starts = [(e, s) for n, lst in ends.items() for (e, s) in lst if (e, s) not in partner]
    for e, s in starts:
        if e not in done:
            strokes.append((walk(e, s), False))
    for e in range(len(edges)):
        if e not in done:
            strokes.append((walk(e, True), True))
    return strokes


def resample(a, step):
    d = np.cumsum(np.r_[0, np.hypot(*np.diff(a, axis=0).T)])
    if d[-1] < step:
        return a
    t = np.linspace(0, d[-1], max(int(d[-1] / step) + 1, 2))
    return np.c_[np.interp(t, d, a[:, 0]), np.interp(t, d, a[:, 1])]


def corners(a, closed, reach_pts, thresh_deg=62):
    n = len(a)
    if n < 2 * reach_pts + 1:
        return []
    ang = np.zeros(n)
    for i in range(n):
        if not closed and (i < reach_pts or i >= n - reach_pts):
            continue
        p, q, r = a[(i - reach_pts) % n], a[i], a[(i + reach_pts) % n]
        u, v = q - p, r - q
        nu, nv = np.hypot(*u), np.hypot(*v)
        if nu == 0 or nv == 0:
            continue
        ang[i] = math.degrees(math.acos(np.clip(np.dot(u, v) / nu / nv, -1, 1)))
    out = []
    for i in range(n):
        if ang[i] > thresh_deg and ang[i] == ang[max(0, i - reach_pts):i + reach_pts + 1].max():
            if not out or i - out[-1] > reach_pts:
                out.append(i)
    return out


def tangent(a, at_end, reach=2.0):
    """Unit direction pointing out of the stroke at one of its ends."""
    b = a if at_end else a[::-1]           # b[-1] is the end in question
    d = np.cumsum(np.r_[0, np.hypot(*np.diff(b[::-1], axis=0).T)])
    k = min(int(np.searchsorted(d, reach)), len(b) - 1)
    v = b[-1] - b[len(b) - 1 - k]
    n = np.hypot(*v)
    return v / n if n > 0 else None


def join_fragments(strokes, max_gap=3.6):
    """Re-connect strokes broken by faint ink when the gap continues the line."""
    while True:
        best = None
        for i, (a, ca) in enumerate(strokes):
            for j, (b, cb) in enumerate(strokes):
                if i == j or ca or cb:
                    continue
                for ea in (True, False):          # end of a (True) or start
                    for sb in (True, False):      # start of b (True) or end
                        p = a[-1] if ea else a[0]
                        q = b[0] if sb else b[-1]
                        gvec = q - p
                        gap = float(np.hypot(*gvec))
                        if gap > max_gap or (best and gap >= best[0]):
                            continue
                        if gap > 1.0:
                            ta = tangent(a, ea)
                            tb = tangent(b, not sb)
                            g = gvec / gap
                            if ta is not None and np.dot(ta, g) < 0.45:
                                continue
                            if tb is not None and np.dot(tb, -g) < 0.45:
                                continue
                        best = (gap, i, j, ea, sb)
        if not best:
            return strokes
        _, i, j, ea, sb = best
        a, b = strokes[i][0], strokes[j][0]
        a = a if ea else a[::-1]
        b = b if sb else b[::-1]
        merged = np.vstack([a, b])
        strokes = [s for k, s in enumerate(strokes) if k not in (i, j)] + [(merged, False)]


DIACRITIC = set("ёЁйЙ")
KEEP_ALL = set(".,!?;:\"%«»—-()/№+")


def postprocess(strokes, ch):
    strokes = join_fragments(strokes)
    big = [s for s in strokes if plen(s[0]) >= 3.0]
    if ch in KEEP_ALL:
        keep = strokes
    elif ch in DIACRITIC:
        top = min(float(s[0][:, 1].min()) for s in big) if big else 1e9
        body = [s for s in big if s[0][:, 1].mean() > top + 6] or big
        btop = min(float(s[0][:, 1].min()) for s in body)
        keep = big + [s for s in strokes if plen(s[0]) < 3.0 and s[0][:, 1].mean() < btop]
    else:
        keep = big or strokes
    out = []
    for a, closed in keep:
        if closed:
            k = int(np.argmin(a[:, 1]))          # loops start at the top ...
            a = np.roll(a, -k, axis=0)
            x, y = a[:, 0], a[:, 1]
            if np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y) > 0:
                a = np.vstack([a[:1], a[1:][::-1]])   # ... and run anticlockwise
        else:
            if a[-1, 0] + 0.6 * a[-1, 1] < a[0, 0] + 0.6 * a[0, 1]:
                a = a[::-1]                       # writing direction: left/top first
        out.append((a, closed))
    # main strokes left to right, dots and diacritics last
    out.sort(key=lambda s: (plen(s[0]) < 3.0 and ch not in KEEP_ALL, float(s[0][0, 0])))
    return out


def extract(crop, origin, ch):
    m, sk, width = skeleton_of(crop)
    nodes, edges = build_graph(sk)
    edges = prune(nodes, edges, spur=S * max(2.2, 1.3 * width))
    strokes = chain(nodes, edges, reach=S * 2.5)
    raw = []
    for pts, closed in strokes:
        a = np.asarray(pts, float)[:, ::-1]  # (x, y)
        a = resample(a, 1.0)
        if len(a) >= 5:
            mode = "wrap" if closed else "nearest"
            sm = ndimage.gaussian_filter1d(a, S * 0.55, axis=0, mode=mode)
            if not closed:
                sm[0], sm[-1] = a[0], a[-1]
                sm = ndimage.gaussian_filter1d(sm, S * 0.25, axis=0, mode="nearest")
            a = sm
        a = a / S + np.asarray(origin, float)
        a = resample(a, 0.25)
        if closed and len(a) > 2:
            a = a[:-1]
        if plen(a) < 1.0:  # dot -> very short dash; renders as a round dot
            c = a.mean(axis=0); a = np.array([c - [0.3, 0], c + [0.3, 0]])
            closed = False
        raw.append((a, bool(closed)))
    out = []
    for a, closed in postprocess(raw, ch):
        a = resample(a, 0.25) if len(a) > 2 else a
        cs = corners(a, closed, reach_pts=10)
        out.append(dict(pts=np.round(a, 3).tolist(), closed=closed,
                        corners=[int(c) for c in cs]))
    return out, width


def entries():
    for row, (group, lst) in GM.ROWS.items():
        for i, (ch, box) in enumerate(lst):
            yield dict(row=row, group=group, char=ch, box=box, alt=row == "dig1")
    for i, (ch, box) in enumerate(GM.ALT):
        yield dict(row="text", group="lc", char=ch, box=box, alt=True)


def main():
    g, lab, comps = load()
    res, widths = [], []
    for e in entries():
        try:
            crop, origin = glyph_mask(g, lab, comps, e["box"])
        except ValueError as err:
            print("WARNING", e["char"], e["row"], err)
            continue
        strokes, w = extract(crop, origin, e["char"])
        widths.append(w)
        e = dict(e, strokes=strokes, width=float(w),
                 ink_box=[int(origin[0]), int(origin[1]), int(origin[0] + crop.shape[1]),
                          int(origin[1] + crop.shape[0])])
        res.append(e)
    os.makedirs(os.path.join(ROOT, "build"), exist_ok=True)
    json.dump(dict(glyphs=res, pen_width_px=float(np.median(widths))),
              open(os.path.join(ROOT, "build", "centerlines_px.json"), "w"), ensure_ascii=False)
    print(len(res), "glyphs; median pen width px", np.median(widths))


if __name__ == "__main__":
    main()
