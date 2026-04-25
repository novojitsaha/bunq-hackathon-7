"""Generate a synthetic Albert Heijn-style receipt for testing Claude Vision."""
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

W, H = 480, 760
img = Image.new("RGB", (W, H), "white")
draw = ImageDraw.Draw(img)

# Use default PIL font (no font files needed)
try:
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf", 22)
    body_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 16)
    small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 13)
except OSError:
    title_font = ImageFont.load_default()
    body_font = ImageFont.load_default()
    small_font = ImageFont.load_default()

y = 24
draw.text((W/2 - 80, y), "ALBERT HEIJN", fill="black", font=title_font); y += 32
draw.text((W/2 - 90, y), "Sloterdijk Amsterdam", fill="black", font=small_font); y += 20
draw.text((W/2 - 70, y), "25-04-2026  14:32", fill="black", font=small_font); y += 28
draw.line([(20, y), (W-20, y)], fill="black", width=1); y += 14

items = [
    ("RED BULL 250ML",  "2x", "3.98"),
    ("CHIPS PAPRIKA",   "1x", "2.49"),
    ("COLA 1.5L",       "1x", "2.19"),
    ("HALFV MELK 1L",   "1x", "1.25"),
    ("CHOCOLADEREEP",   "2x", "2.98"),
    ("APPELS 1KG",      "1x", "2.29"),
    ("STATIEGELD",      "1x", "0.50"),
    ("VOLKOREN BROOD",  "1x", "2.29"),
]

for name, qty, price in items:
    draw.text((25, y), name, fill="black", font=body_font)
    draw.text((W-130, y), qty, fill="black", font=body_font)
    draw.text((W-70, y), f"€{price}", fill="black", font=body_font)
    y += 22

y += 8
draw.line([(20, y), (W-20, y)], fill="black", width=1); y += 14
draw.text((25, y), "TOTAAL", fill="black", font=title_font)
draw.text((W-110, y), "€17.97", fill="black", font=title_font); y += 32
draw.text((25, y), "PIN BETALING", fill="black", font=body_font); y += 24
draw.line([(20, y), (W-20, y)], fill="black", width=1); y += 18
draw.text((W/2 - 110, y), "BEDANKT EN TOT ZIENS!", fill="black", font=body_font)

out = Path("/home/claude/bbb/backend/.test_data/receipt_ah.png")
out.parent.mkdir(parents=True, exist_ok=True)
img.save(out, "PNG")
print(f"Saved: {out}  size={out.stat().st_size}")
