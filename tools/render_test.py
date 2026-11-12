"""Render sample text with the compiled TTF (FreeType via Pillow) -> build/render_test.png."""
import os, sys
from PIL import Image, ImageDraw, ImageFont, features

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEXT = sys.argv[1:] or [
    "Вчера Фёдор и Юля шли через тихий парк. У беседки рыжий",
    "кот прыгнул на скамью, а щенок вдруг залаял. «Чья это",
    "шапка?» — спросила Юля. Жду вас в 18:45 у подъезда.",
    "Съешь же ещё этих мягких французских булок, да выпей чаю.",
    "АБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ 0123456789",
    "абвгдеёжзийклмнопрстуфхцчшщъыьэюя .,!?;:—-()«»\"/№%+",
]


def main():
    eng = ImageFont.Layout.RAQM if features.check("raqm") else ImageFont.Layout.BASIC
    f = ImageFont.truetype(os.path.join(ROOT, "dist", "MyHandwriting-Regular.ttf"), 54,
                           layout_engine=eng)
    W, lh = 1900, 100
    im = Image.new("L", (W, lh * len(TEXT) + 60), 255)
    d = ImageDraw.Draw(im)
    for i, t in enumerate(TEXT):
        y = 30 + i * lh
        d.line([(0, y + 70), (W, y + 70)], fill=225)
        d.text((20, y), t, font=f, fill=0)
    im.save(os.path.join(ROOT, "build", "render_test.png"))
    print("layout:", "raqm" if eng == ImageFont.Layout.RAQM else "basic")


if __name__ == "__main__":
    main()
