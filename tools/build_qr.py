"""
Generates a QR code for the game's GitHub Pages URL and a one-page A4
printable around it, into printables/.

Usage:
    ../.venv/bin/python build_qr.py
"""

from pathlib import Path

import qrcode
from qrcode.constants import ERROR_CORRECT_H

ROOT_DIR = Path(__file__).resolve().parent.parent
OUT_PNG = ROOT_DIR / "printables" / "qr_code.png"
OUT_HTML = ROOT_DIR / "printables" / "qr_code.html"

URL = "https://reidan-dev.github.io/escape-room-game/"

qr = qrcode.QRCode(
    error_correction=ERROR_CORRECT_H,  # high error correction: survives print wear/folds
    box_size=12,
    border=2,
)
qr.add_data(URL)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
img.save(OUT_PNG)
print("Wrote", OUT_PNG)

html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Cure Line — QR</title>
<style>
  @page {{ size: A4; margin: 0; }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    width: 210mm;
    height: 297mm;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: Georgia, 'Times New Roman', serif;
    color: #111;
  }}
  .card {{
    text-align: center;
  }}
  .card h1 {{
    font-size: 30px;
    letter-spacing: 2px;
    margin: 0 0 6px;
  }}
  .card .sub {{
    font-size: 13px;
    font-style: italic;
    color: #444;
    margin-bottom: 28px;
  }}
  .card img {{
    width: 70mm;
    height: 70mm;
    border: 10px solid #fff;
    outline: 1px solid #ccc;
  }}
  .card .url {{
    margin-top: 22px;
    font-size: 12px;
    color: #555;
    letter-spacing: 0.5px;
  }}
</style>
</head>
<body>
  <div class="card">
    <h1>ANG DAILY CHISMIS</h1>
    <div class="sub">Scan to reach the Cure Line</div>
    <img src="qr_code.png" alt="QR code">
    <div class="url">{URL}</div>
  </div>
</body>
</html>
"""

with open(OUT_HTML, "w") as f:
    f.write(html)

print("Wrote", OUT_HTML)
