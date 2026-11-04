"""Контактный лист: python3 sheet.py out.png img1 img2 ..."""
import sys
from PIL import Image, ImageDraw
out, paths = sys.argv[1], sys.argv[2:]
tw, th, cols = 300, 533, 6
rows = (len(paths) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + 24)), "white")
d = ImageDraw.Draw(sheet)
for i, p in enumerate(paths):
    im = Image.open(p).convert("RGB").resize((tw, th))
    x, y = (i % cols) * tw, (i // cols) * (th + 24)
    sheet.paste(im, (x, y + 24))
    d.text((x + 4, y + 4), p.split("_")[-1][:-4], fill="black")
sheet.save(out)
