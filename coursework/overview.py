import glob, sys
from PIL import Image
fs = sorted(glob.glob(sys.argv[1] if len(sys.argv) > 1 else "pg-*.png"))
ims = [Image.open(f) for f in fs]
w = max(i.width for i in ims); h = max(i.height for i in ims)
cols = 7; rows = (len(ims) + cols - 1) // cols
o = Image.new("RGB", (cols * (w + 6), rows * (h + 6)), "gray")
for k, i in enumerate(ims):
    o.paste(i, ((k % cols) * (w + 6), (k // cols) * (h + 6)))
o.save("overview.png")
