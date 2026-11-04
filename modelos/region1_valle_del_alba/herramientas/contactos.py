"""
Hoja de contactos: monta varios renders en una cuadrícula con su título.

Uso:
    python modelos/region1_valle_del_alba/herramientas/contactos.py --salida hoja.png render1.png:"Título" ...
"""

import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFont


def fuente(tam):
    for r in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"):
        if os.path.exists(r):
            return ImageFont.truetype(r, tam)
    return ImageFont.load_default()


def hoja(entradas, salida, columnas=3, ancho=800, titulo="Región 1 · Valle del Alba"):
    ims = [(Image.open(r).convert("RGB"), t) for r, t in entradas]
    alto = int(ancho * ims[0][0].height / ims[0][0].width)
    filas = math.ceil(len(ims) / columnas)
    cab, pie, m = 90, 40, 14
    W = columnas * ancho + (columnas + 1) * m
    H = cab + filas * (alto + pie + m) + m
    o = Image.new("RGB", (W, H), (22, 24, 28))
    d = ImageDraw.Draw(o)
    d.text((m, 24), titulo, font=fuente(40), fill=(245, 234, 210))
    f = fuente(20)
    for i, (im, t) in enumerate(ims):
        x = m + (i % columnas) * (ancho + m)
        y = cab + (i // columnas) * (alto + pie + m)
        o.paste(im.resize((ancho, alto), Image.LANCZOS), (x, y))
        d.text((x + 4, y + alto + 8), t, font=f, fill=(225, 225, 225))
    o.save(salida, optimize=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--columnas", type=int, default=3)
    ap.add_argument("--titulo", default="Región 1 · Valle del Alba")
    ap.add_argument("imagenes", nargs="+")
    a = ap.parse_args()
    hoja([tuple(x.split(":", 1)) if ":" in x else (x, os.path.basename(x)) for x in a.imagenes], a.salida,
         a.columnas, titulo=a.titulo)
