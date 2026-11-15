"""Monta la hoja de cada ronda (la vista 3/4 de cada modelo) a partir de los turnaround ya renderizados.

    python hoja_ronda.py            # todas las rondas
    python hoja_ronda.py r03 r04
"""
import glob
import importlib
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
RAIZ = os.path.dirname(AQUI)

from PIL import Image, ImageDraw, ImageFont  # noqa: E402


def fuente(tam):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(ruta, tam) if os.path.exists(ruta) else ImageFont.load_default(tam)


def modelos_de(ronda):
    """Lee la lista MODELOS del módulo sin importarlo (necesitaría Blender): nombre y categoría."""
    import re
    texto = open(glob.glob(os.path.join(AQUI, f"{ronda}_*.py"))[0], encoding="utf-8").read()
    return re.findall(r'\("([a-z0-9_]+)", "([a-z_]+)", \d+, ', texto.split("MODELOS = [")[1])


def main():
    rondas = sys.argv[1:] or sorted({os.path.basename(p)[:3] for p in glob.glob(os.path.join(AQUI, "r[0-9][0-9]_*.py"))})
    os.makedirs(os.path.join(RAIZ, "rondas"), exist_ok=True)
    for ronda in rondas:
        minis = []
        for nombre, cat in modelos_de(ronda):
            ruta = os.path.join(RAIZ, cat, nombre, f"{nombre}_turnaround.png")
            if not os.path.exists(ruta):
                continue
            im = Image.open(ruta).convert("RGB")
            t = (im.size[0] - 8) // 3
            tris = json.load(open(os.path.join(RAIZ, cat, nombre, f"{nombre}.json"), encoding="utf-8"))["triangulos"]
            minis.append((nombre, tris, im.crop((2 + t + 2, 58, 2 + t + 2 + t, 58 + t))))
        if not minis:
            continue
        t = minis[0][2].size[0]
        cols = min(4, len(minis))
        filas = (len(minis) + cols - 1) // cols
        hoja = Image.new("RGB", (cols * t, filas * t), (22, 24, 30))
        dr = ImageDraw.Draw(hoja)
        for i, (nombre, tris, im) in enumerate(minis):
            x, y = (i % cols) * t, (i // cols) * t
            hoja.paste(im, (x, y))
            dr.rectangle((x, y, x + t, y + 26), fill=(22, 24, 30))
            dr.text((x + 8, y + 5), f"{nombre} · {tris} tri", font=fuente(14), fill=(255, 255, 255))
        hoja.save(os.path.join(RAIZ, "rondas", f"{ronda}.jpg"), quality=88)
        print("hoja", ronda, len(minis))


if __name__ == "__main__":
    main()
