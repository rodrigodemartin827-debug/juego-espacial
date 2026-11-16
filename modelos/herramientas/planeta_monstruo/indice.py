"""
Recorre modelos/planeta_monstruo y escribe:
  * indice.json: resumen de todos los modelos (zona, triángulos, tamaño, piezas, verificación del FBX).
  * README.md: tabla por zonas y cómo importar.
  * hojas/<zona>.jpg: una hoja con la vista 3/4 de cada modelo de la zona.
"""

import glob
import json
import os

from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, "..", "..", "planeta_monstruo"))
ZONAS = [("guaridas", "Guaridas y estructuras"), ("vegetacion", "Vegetación alienígena"), ("bestias", "Bestias cósmicas"),
         ("guerra", "Zona de guerra y entrenamiento"), ("props", "Props y decoración"), ("terreno", "Terreno y formaciones")]


def fuente(t):
    r = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(r, t) if os.path.exists(r) else ImageFont.load_default(t)


def main():
    import sys

    sys.path.insert(0, AQUI)
    import ejecutar

    lib, por_ronda = ejecutar.cargar()
    orden = [n for k in sorted(por_ronda) for n in por_ronda[k]]
    datos = {}
    for n in orden:
        r = os.path.join(RAIZ, n, f"{n}.json")
        if os.path.exists(r):
            datos[n] = json.load(open(r, encoding="utf-8"))
    indice = dict(total_modelos=len(datos), total_triangulos=sum(d["triangulos"] for d in datos.values()), modelos=[])
    for n, d in datos.items():
        indice["modelos"].append(dict(nombre=n, zona=d["zona"], clase=d["clase"], triangulos=d["triangulos"],
                                      presupuesto=d["presupuesto_triangulos"], tamano_studs=d["tamano_studs"],
                                      piezas=[p["nombre"] for p in d["piezas"]], fbx_ok=d["verificacion_fbx"]["correcto"],
                                      asientos=len(d.get("puntos_montura", [])), avisos=d.get("avisos", [])))
    json.dump(indice, open(os.path.join(RAIZ, "indice.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    os.makedirs(os.path.join(RAIZ, "hojas"), exist_ok=True)
    lineas = []
    for zona, titulo in ZONAS:
        ns = [n for n in datos if datos[n]["zona"] == zona]
        if not ns:
            continue
        lineas += [f"\n### {titulo} ({len(ns)})\n", f"![{titulo}](hojas/{zona}.jpg)\n", "| Modelo | Triángulos | Tamaño (X × Y × Z studs) | Piezas |", "| --- | ---: | --- | --- |"]
        lado, cols = 384, 5
        filas = (len(ns) + cols - 1) // cols
        hoja = Image.new("RGB", (lado * cols, 40 + filas * (lado + 26)), (14, 12, 20))
        dr = ImageDraw.Draw(hoja)
        dr.text((12, 8), f"{titulo} — Planeta Monstruo", fill=(200, 110, 255), font=fuente(22))
        for i, n in enumerate(ns):
            d = datos[n]
            t = d["tamano_studs"]
            piezas = ", ".join(f"`{p['nombre']}`" for p in d["piezas"])
            extra = f" · {len(d['puntos_montura'])} asientos" if d.get("puntos_montura") else ""
            lineas.append(f"| `{n}` | {d['triangulos']:,}".replace(",", ".") + f" | {t['x']} × {t['y']} × {t['z']}{extra} | {piezas} |")
            im = Image.open(os.path.join(RAIZ, n, f"{n}_turnaround.png")).convert("RGB")
            w = im.size[0] // 3
            tile = im.crop((w, 54, 2 * w, 54 + w)).resize((lado, lado), Image.LANCZOS)   # la vista 3/4
            x, y = (i % cols) * lado, 40 + (i // cols) * (lado + 26)
            hoja.paste(tile, (x, y))
            dr.text((x + 8, y + lado + 4), f"{n}  ·  {d['triangulos']} tris", fill=(225, 225, 235), font=fuente(14))
        hoja.save(os.path.join(RAIZ, "hojas", f"{zona}.jpg"), quality=88)
    cab = open(os.path.join(AQUI, "LEEME_plantilla.md"), encoding="utf-8").read()
    malos = [m["nombre"] for m in indice["modelos"] if not m["fbx_ok"] or m["triangulos"] > m["presupuesto"]]
    cab = cab.replace("--TOTAL--", str(len(datos))).replace("--TRIS--", f"{indice['total_triangulos']:,}".replace(",", "."))
    open(os.path.join(RAIZ, "README.md"), "w", encoding="utf-8").write(cab + "\n## Los modelos\n" + "\n".join(lineas) + "\n")
    print(len(datos), "modelos;", "con fallos:", malos or "ninguno")


if __name__ == "__main__":
    main()
