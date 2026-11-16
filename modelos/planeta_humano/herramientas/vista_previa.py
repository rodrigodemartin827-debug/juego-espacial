"""Junta varios turnarounds en una sola imagen para revisarlos de un vistazo. Uso: vista_previa.py salida.png a b ..."""
import os
import sys

from PIL import Image

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
salida, nombres = sys.argv[1], sys.argv[2:]
ancho = 1300
ims = []
for n in nombres:
    im = Image.open(os.path.join(RAIZ, n, f"{n}_turnaround.png")).convert("RGB")
    ims.append(im.resize((ancho, im.height * ancho // im.width), Image.LANCZOS))
hoja = Image.new("RGB", (ancho, sum(i.height for i in ims)))
y = 0
for i in ims:
    hoja.paste(i, (0, y))
    y += i.height
hoja.save(salida, quality=88)
