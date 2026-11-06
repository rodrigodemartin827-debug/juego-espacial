"""
Guarda la hoja de contactos de una ronda en modelos/<modelo>/rondas/ en JPG (pesa mucho menos que el PNG).

Uso: python modelos/herramientas/guardar_ronda.py <hoja.png> <modelos/<modelo>/rondas/ronda_N.jpg>
"""

import os
import sys

from PIL import Image

origen, destino = sys.argv[1], sys.argv[2]
os.makedirs(os.path.dirname(destino), exist_ok=True)
img = Image.open(origen).convert("RGB")
if img.width > 2000:
    img = img.resize((2000, round(img.height * 2000 / img.width)), Image.LANCZOS)
img.save(destino, quality=86, optimize=True)
print("[ok]", destino)
