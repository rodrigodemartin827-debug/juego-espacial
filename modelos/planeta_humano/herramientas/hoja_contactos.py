"""Hoja con la vista 3/4 de los 105 modelos, por zonas. Uso: python hoja_contactos.py [salida.jpg]"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import generar

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
M = generar.cargar()
T, COL = 300, 10
nombres = sorted(M, key=lambda n: M[n]["num"])
filas = (len(nombres) + COL - 1) // COL
hoja = Image.new("RGB", (COL * T, 80 + filas * (T + 34)), (18, 20, 26))
d = ImageDraw.Draw(hoja)
f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 34)
f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
d.text((16, 18), "Planeta Humano · 105 modelos (vista 3/4)", fill=(61, 242, 255), font=f1)
for i, n in enumerate(nombres):
    x, y = (i % COL) * T, 80 + (i // COL) * (T + 34)
    ruta = os.path.join(RAIZ, n, f"{n}_turnaround.png")
    if os.path.exists(ruta):
        im = Image.open(ruta).convert("RGB").crop((640, 70, 1280, 710)).resize((T, T), Image.LANCZOS)
        hoja.paste(im, (x, y))
    d.text((x + 8, y + T + 6), f"{M[n]['num']:03d} {n}", fill=(225, 230, 238), font=f2)
salida = sys.argv[1] if len(sys.argv) > 1 else os.path.join(RAIZ, "hoja_contactos.jpg")
hoja.save(salida, quality=86)
print(salida)
