"""
Hoja de una ronda: recorta la vista 3/4 del turnaround de cada pieza y las junta (5 × 2) con su nombre.

Uso: python -m piezas_nave.hoja_ronda <carpeta nave_piezas> <ronda> [salida.jpg]
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from piezas_nave import catalogo  # noqa: E402


def fuente(t):
    return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", t)


def hoja(carpeta, nombres, salida, titulo, vista=5):
    celdas = []
    for n in nombres:
        ruta = os.path.join(carpeta, n, f"{n}_turnaround.jpg")
        if not os.path.exists(ruta):
            continue
        img = Image.open(ruta)
        tam = (img.size[0] - 560) // 4
        i = vista
        x, y = (i % 4) * tam, 64 + (i // 4) * tam
        celdas.append((n, img.crop((x, y + 30, x + tam, y + tam))))
    if not celdas:
        return None
    w, h = celdas[0][1].size
    cols = 5
    filas = (len(celdas) + cols - 1) // cols
    out = Image.new("RGB", (cols * w, 50 + filas * (h + 26)), (14, 16, 22))
    d = ImageDraw.Draw(out)
    d.text((12, 10), titulo, fill=(255, 214, 102), font=fuente(26))
    for k, (n, im) in enumerate(celdas):
        x, y = (k % cols) * w, 50 + (k // cols) * (h + 26)
        out.paste(im, (x, y + 26))
        d.text((x + 8, y + 4), n, fill=(255, 255, 255), font=fuente(15))
    out.save(salida, quality=85)
    return salida


if __name__ == "__main__":
    carpeta, ronda = sys.argv[1], int(sys.argv[2])
    nombres = [p["nombre"] for p in catalogo.PIEZAS[(ronda - 1) * 10: ronda * 10]]
    salida = sys.argv[3] if len(sys.argv) > 3 else os.path.join(carpeta, "rondas", f"ronda_{ronda:02d}.jpg")
    os.makedirs(os.path.dirname(salida), exist_ok=True)
    print(hoja(carpeta, nombres, salida, f"Piezas de nave — ronda {ronda}"))
