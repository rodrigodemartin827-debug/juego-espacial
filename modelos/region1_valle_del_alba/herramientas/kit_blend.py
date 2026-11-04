"""
Construye kit_valle_del_alba.blend (todas las piezas del kit, ordenadas por categorías, más unos edificios de ejemplo
montados con ellas) y renderiza la hoja del kit: una miniatura por pieza con su nombre.

Uso:
    python modelos/region1_valle_del_alba/herramientas/kit_blend.py --salida modelos/region1_valle_del_alba
        [--sin-miniaturas] [--muestras 24]
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import edificios as ED  # noqa: E402
import escena as E  # noqa: E402
import kit as K  # noqa: E402
import materiales as MAT  # noqa: E402

EJEMPLOS = [
    ("Ejemplo_Casa_3x2", lambda: ED.edificio(3, 2, 2, 11, "casa").malla),
    ("Ejemplo_Rustica_2x2", lambda: ED.edificio(2, 2, 2, 12, "rustica").malla),
    ("Ejemplo_Tienda_3x2", lambda: ED.edificio(3, 2, 2, 13, "tienda", emblema="espada").malla),
    ("Ejemplo_Casa_Alta_2x2", lambda: ED.edificio(2, 2, 3, 14, "casa").malla),
    ("Ejemplo_Ayuntamiento", lambda: ED.ayuntamiento().malla),
]


def fuente_texto(tam):
    for r in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"):
        if os.path.exists(r):
            return ImageFont.truetype(r, tam)
    return ImageFont.load_default()


def construir(mats):
    raiz = bpy.data.collections.new("Kit_Valle_del_Alba")
    bpy.context.scene.collection.children.link(raiz)
    cats = {}
    objetos = []
    x = 0.0
    fila = {}
    for nombre, cat, f in CATALOGO_COMPLETO():
        if cat not in cats:
            c = bpy.data.collections.new(cat)
            raiz.children.link(c)
            cats[cat] = c
            fila[cat] = 0.0
        malla = f()
        ob = malla.a_blender(nombre, mats, cats[cat])
        lo, hi = malla.limites()
        ob["categoria"] = cat
        ob["tamano_studs"] = [round(float(v), 2) for v in (hi - lo)]
        # en fila por categoría (solo para ordenar la escena)
        iy = list(cats).index(cat)
        ob.location = (fila[cat] - lo[0], iy * 120.0, 0)
        fila[cat] += (hi[0] - lo[0]) + 12.0
        objetos.append((ob, malla, cat))
    return objetos


def CATALOGO_COMPLETO():
    return [(n, c, f) for n, c, f in K.CATALOGO] + [(n, "Ejemplos", f) for n, f in EJEMPLOS]


def miniaturas(objetos, carpeta, muestras):
    """Renderiza cada pieza sola, encuadrada en vista de 3/4, y monta la hoja con los nombres."""
    E.configurar_render(420, 420, muestras)
    s = bpy.context.scene
    s.view_settings.look = "AgX - Medium High Contrast"
    E.iluminar("dia")
    MAT.ajustar_niebla(1e6, 1e6, 0.0, (1, 1, 1))
    # suelo neutro
    sm = bpy.data.meshes.new("Suelo")
    sm.from_pydata([(-1e4, -1e4, 0), (1e4, -1e4, 0), (1e4, 1e4, 0), (-1e4, 1e4, 0)], [], [(0, 1, 2, 3)])
    suelo = bpy.data.objects.new("Suelo_Estudio", sm)
    s.collection.objects.link(suelo)
    ms = bpy.data.materials.new("Estudio")
    ms.use_nodes = True
    ms.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.6, 0.5, 1)
    sm.materials.append(ms)
    tmp = os.path.join(carpeta, "_miniaturas")
    os.makedirs(tmp, exist_ok=True)
    rutas = []
    for ob in [o for o, _, _ in objetos]:
        ob.hide_render = True
    for ob, malla, cat in objetos:
        ob.hide_render = False
        lo, hi = malla.limites()
        c = (lo + hi) / 2 + np.array(ob.location)
        r = float(np.linalg.norm(hi - lo)) / 2
        suelo.location = (0, 0, max(float(lo[2]), -0.6) + float(ob.location.z))  # las losas bajan a -4: se entierran
        d = np.array([-0.55, -1.0, 0.62])
        d /= np.linalg.norm(d)
        dist = r / math.tan(math.radians(17)) * 1.02
        E.camara(tuple(c + d * dist), tuple(c), lente=50, recorte=(0.1, 5000))
        ruta = os.path.join(tmp, f"{ob.name}.png")
        E.render(ruta)
        rutas.append((ruta, ob.name, cat, ob["triangulos"]))
        ob.hide_render = True
    for ob in [o for o, _, _ in objetos]:
        ob.hide_render = False
    s.collection.objects.unlink(suelo)
    # hoja
    col = 8
    t = 300
    filas = math.ceil(len(rutas) / col)
    cab = 90
    hoja = Image.new("RGB", (col * t, cab + filas * (t + 34)), (24, 26, 30))
    dr = ImageDraw.Draw(hoja)
    dr.text((20, 22), "Kit de construcción · Valle del Alba", font=fuente_texto(38), fill=(245, 236, 214))
    f = fuente_texto(17)
    for i, (ruta, nombre, cat, tris) in enumerate(rutas):
        im = Image.open(ruta).resize((t, t), Image.LANCZOS)
        x, y = (i % col) * t, cab + (i // col) * (t + 34)
        hoja.paste(im, (x, y))
        dr.text((x + 8, y + t + 6), f"{nombre}  ({tris} tri)", font=f, fill=(230, 230, 230))
    ruta_hoja = os.path.join(carpeta, "renders", "kit_hoja_piezas.png")
    os.makedirs(os.path.dirname(ruta_hoja), exist_ok=True)
    hoja.save(ruta_hoja, optimize=True)
    return ruta_hoja


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--sin-miniaturas", action="store_true")
    ap.add_argument("--muestras", type=int, default=24)
    ap.add_argument("--solo", default="", help="lista de nombres separados por comas (para pruebas)")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    E.limpiar()
    mats = MAT.todos()
    objetos = construir(mats)
    if a.solo:
        quedan = set(a.solo.split(","))
        objetos = [o for o in objetos if o[0].name in quedan]
    total = sum(o["triangulos"] for o, _, _ in objetos)
    print(f"{len(objetos)} piezas, {total} triángulos")
    for o, _, _ in objetos:
        print(f"  {o.name:28s} {o['triangulos']:6d} tri  {o['tamano_studs']}")
    if not a.sin_miniaturas:
        print("hoja:", miniaturas(objetos, a.salida, a.muestras))
    if not a.solo:
        bpy.context.scene.camera = None
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(os.path.join(a.salida, "kit_valle_del_alba.blend")),
                                    compress=True)


if __name__ == "__main__":
    main()
