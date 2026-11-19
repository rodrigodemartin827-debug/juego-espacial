"""Índice del Planeta Humano: tabla de modelos (desde los JSON) y hoja de contactos con todos.

    python3 indice.py      # escribe ../INDICE.md y ../hoja_planeta_humano.png
"""

import json
import os
from glob import glob

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ZONAS = [("comercial", "Zona comercial"), ("industrial", "Zona industrial"), ("hangar", "Zona del hangar"),
         ("naturaleza", "Naturaleza"), ("especiales", "Edificios especiales"), ("urbano", "Mobiliario urbano")]
F = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def main():
    lineas = ["# Índice de modelos del Planeta Humano", "",
              "Generado por `herramientas/indice.py` a partir de los JSON de cada modelo.", ""]
    miniaturas = []
    for zona, titulo in ZONAS:
        filas = []
        for ruta in sorted(glob(os.path.join(RAIZ, zona, "*", "*.json"))):
            d = json.load(open(ruta, encoding="utf-8"))
            t = d["tam_studs"]
            v = d["verificacion_fbx"]
            neon = [p["nombre"] for p in d["piezas"] if p["tipo"] == "neon"]
            moviles = [p["nombre"] for p in d["piezas"] if p["tipo"] == "textura" and p["nombre"] != d["nombre"]]
            filas.append(f"| `{d['nombre']}` | {t['ancho_x']} × {t['fondo_z']} × {t['alto_y']} | "
                         f"{d['triangulos']:,} / {d['presupuesto']:,} | {len(d['piezas'])} | "
                         f"{', '.join('`' + n.replace(d['nombre'] + '_', '') + '`' for n in moviles) or '—'} | "
                         f"{'sí' if v['ok'] and v['normales_fuera'] else 'NO'} |")
            mini = os.path.join(os.path.dirname(ruta), "_render", "3-4_Frontal.png")
            if os.path.exists(mini):
                miniaturas.append((d["nombre"], mini))
        if not filas:
            continue
        lineas += [f"## {titulo} ({len(filas)})", "",
                   "| Modelo | Tamaño (studs, ancho × fondo × alto) | Triángulos / máx | Mallas | Piezas móviles | FBX verificado |",
                   "| --- | --- | ---: | ---: | --- | --- |"] + filas + [""]
    with open(os.path.join(RAIZ, "INDICE.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    if miniaturas:
        tam = 300
        cols = 8
        filas = (len(miniaturas) + cols - 1) // cols
        hoja = Image.new("RGB", (cols * tam, filas * tam + 60), (16, 18, 24))
        d = ImageDraw.Draw(hoja)
        d.text((14, 12), f"Planeta Humano · {len(miniaturas)} modelos", fill=(255, 214, 102),
               font=ImageFont.truetype(F, 30))
        for i, (n, r) in enumerate(miniaturas):
            x, y = (i % cols) * tam, 60 + (i // cols) * tam
            hoja.paste(Image.open(r).convert("RGB").resize((tam, tam)), (x, y))
            d.text((x + 6, y + 6), n, fill=(255, 255, 255), font=ImageFont.truetype(F, 14))
        hoja.save(os.path.join(RAIZ, "hoja_planeta_humano.png"), optimize=True)
    print("ok", len(miniaturas))


if __name__ == "__main__":
    main()
