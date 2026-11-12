"""Overlay extracted centerlines on the scan crops -> build/debug_*.png."""
import json, os, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(__file__))
import glyphmap as GM

Z = 6


def tile(g, e):
    x0, y0, x1, y1 = e["ink_box"]
    c = cv2.cvtColor(g[y0:y1, x0:x1], cv2.COLOR_GRAY2BGR)
    c = cv2.resize(c, None, fx=Z, fy=Z, interpolation=cv2.INTER_CUBIC)
    c = (c * 0.6 + 255 * 0.4).astype(np.uint8)
    cols = [(0, 0, 230), (0, 150, 0), (200, 0, 0), (0, 140, 220), (160, 0, 160), (90, 90, 0)]
    for k, s in enumerate(e["strokes"]):
        a = (np.asarray(s["pts"]) - [x0, y0]) * Z
        a = a.astype(np.int32)
        cv2.polylines(c, [a], s["closed"], cols[k % len(cols)], 2, cv2.LINE_AA)
        cv2.circle(c, tuple(a[0]), 4, cols[k % len(cols)], -1)
        for ci in s["corners"]:
            cv2.circle(c, tuple(a[ci]), 5, (0, 0, 0), 1)
    lab = e["char"] + ("'" if e["alt"] else "")
    return c, lab


def main():
    from PIL import Image, ImageDraw, ImageFont
    d = json.load(open(os.path.join(ROOT, "build", "centerlines_px.json")))
    g = cv2.imread(os.path.join(ROOT, GM.SCAN), 0)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
    tiles = [tile(g, e) for e in d["glyphs"]]
    W, per = 1500, None
    sheets, cur, x, y, rowh = [], [], 0, 0, 0
    for t, lab in tiles:
        h, w = t.shape[:2]
        if x + w > W:
            x, y, rowh = 0, y + rowh + 30, 0
        if y + h > 1400:
            sheets.append(cur); cur, x, y, rowh = [], 0, 0, 0
        cur.append((t, lab, x, y)); x += w + 12; rowh = max(rowh, h)
    sheets.append(cur)
    for i, sh in enumerate(sheets):
        H = max(yy + t.shape[0] for t, _, _, yy in sh) + 40
        im = Image.new("RGB", (W, H), "white"); dr = ImageDraw.Draw(im)
        for t, lab, xx, yy in sh:
            im.paste(Image.fromarray(t[:, :, ::-1]), (xx, yy + 28))
            dr.text((xx + 2, yy), lab, fill="black", font=font)
        im.save(os.path.join(ROOT, "build", f"debug_{i}.png"))
    print(len(sheets), "sheets")


if __name__ == "__main__":
    main()
