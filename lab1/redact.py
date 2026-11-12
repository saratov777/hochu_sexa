"""Redact the account e-mail shown in the Settings sidebar; trim the window border."""
import os
from PIL import Image, ImageFilter

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screens_doc")
os.makedirs(OUT, exist_ok=True)
EMAIL_BOX = (92, 89, 270, 110)   # sidebar e-mail line in a 1500x1000 Settings capture
# empty space below the content of each page (y limit in the 1500x1000 capture)
BOTTOM = {1: 840, 2: 630, 3: 725, 4: 770, 5: 905}

for n in range(1, 6):
    im = Image.open(os.path.join(D, f"fig{n}.png")).convert("RGB")
    if n >= 2:
        reg = im.crop(EMAIL_BOX).filter(ImageFilter.GaussianBlur(7))
        im.paste(reg, EMAIL_BOX[:2])
    im = im.crop((1, 1, im.width - 8, BOTTOM[n]))   # also drops PrintWindow's dark right frame
    im.save(os.path.join(OUT, f"fig{n}.png"))
print("ok")
