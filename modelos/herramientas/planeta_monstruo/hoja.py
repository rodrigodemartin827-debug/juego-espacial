"""Junta los turnarounds de varios modelos en una hoja reducida (para revisar una ronda de un vistazo)."""
import os
import sys

from PIL import Image

salida, carpeta, nombres = sys.argv[1], sys.argv[2], sys.argv[3:]
ims = []
for n in nombres:
    r = os.path.join(carpeta, n, f"{n}_turnaround.png")
    if os.path.exists(r):
        ims.append(Image.open(r).convert("RGB").resize((768, 539), Image.LANCZOS))
cols = 2
hoja = Image.new("RGB", (768 * cols, 539 * ((len(ims) + 1) // cols)), (0, 0, 0))
for i, im in enumerate(ims):
    hoja.paste(im, ((i % cols) * 768, (i // cols) * 539))
hoja.save(salida, quality=88)
