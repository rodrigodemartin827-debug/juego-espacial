"""
Construye kit_valle_del_alba.blend (todas las piezas del kit, detalladas y simples, ordenadas por categorías, y
unos edificios de ejemplo montados con COPIAS de las piezas) y renderiza la hoja del kit: en cada miniatura, la
versión detallada a la izquierda y la simple a la derecha, con sus triángulos.

Uso:
    python modelos/region1_valle_del_alba/herramientas/kit_blend.py --salida modelos/region1_valle_del_alba
        [--sin-miniaturas] [--muestras 24] [--solo Pared_Ventana,Farola]
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import atlas as AT  # noqa: E402
import edificios as ED  # noqa: E402
import escena as E  # noqa: E402
import kit as K  # noqa: E402
import materiales as MAT  # noqa: E402

EJEMPLOS = [
    ("Ejemplo_Casa_3x2", lambda: ED.edificio(3, 2, 2, 11, "casa")),
    ("Ejemplo_Rustica_2x2", lambda: ED.edificio(2, 2, 2, 12, "rustica")),
    ("Ejemplo_Tienda_3x2", lambda: ED.edificio(3, 2, 2, 13, "tienda", emblema="espada")),
    ("Ejemplo_Casa_Alta_2x3", lambda: ED.edificio(2, 3, 3, 14, "casa")),
    ("Ejemplo_Ayuntamiento", lambda: ED.ayuntamiento()),
]


def fuente_texto(tam):
    for r in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf"):
        if os.path.exists(r):
            return ImageFont.truetype(r, tam)
    return ImageFont.load_default()


def _caja(obs):
    pts = []
    for o in obs:
        for c in o.bound_box:
            pts.append(np.array(o.matrix_world @ Vector(c)))
    pts = np.array(pts)
    return pts.min(axis=0), pts.max(axis=0)


def construir(mats, solo=None):
    """Una entrada por pieza: (nombre, categoría, [objetos detallados], [objetos simples], tris det, tris simple)."""
    raiz = bpy.data.collections.new("Kit_Valle_del_Alba")
    bpy.context.scene.collection.children.link(raiz)
    cats = {}
    entradas = []
    fila = {}
    K.losa_nombre(3, 2)
    K.registrar_puente(64.0, 8.0, 3)
    from region import Biblioteca

    for nombre, (det, sim, color, cat) in K.PIEZAS.items():
        if solo and nombre not in solo:
            continue
        if cat not in cats:
            c = bpy.data.collections.new(cat)
            raiz.children.link(c)
            cats[cat] = c
            fila[cat] = 0.0
        md = det()
        ms = sim() if sim is not None else None
        obd = md.a_blender(nombre, mats, cats[cat])
        obd.color = (*MAT.srgb_a_lineal(color), 1)
        lo, hi = md.limites()
        iy = list(cats).index(cat)
        obd.location = (fila[cat] - lo[0], iy * 150.0, 0)
        obd["categoria"] = cat
        obd["tamano_studs"] = [round(float(v), 2) for v in (hi - lo)]
        sep = (hi[0] - lo[0]) + 3.0
        obs_s = []
        if ms is not None:
            obs = ms.a_blender(nombre + "__lejos", mats, cats[cat])
            obs.color = obd.color
            obs.location = (obd.location.x + sep, obd.location.y, 0)
            obs_s = [obs]
            ts = ms.n_triangulos
        else:
            ts = 0 if sim is K.SIN_LEJOS else md.n_triangulos
        fila[cat] += 2 * sep + 12.0
        entradas.append((nombre, cat, [obd], obs_s, md.n_triangulos, ts, sim))
    if solo:
        return entradas
    # edificios de ejemplo: grupos de copias de las piezas (como en la región)
    c = bpy.data.collections.new("Ejemplos")
    raiz.children.link(c)
    cbib = bpy.data.collections.new("Kit_Mallas_Ejemplos")
    raiz.children.link(cbib)
    bib = Biblioteca(mats, cbib)
    x = 0.0
    for nombre, f in EJEMPLOS:
        ed = f()
        grupos = []
        for lejos in (False, True):
            e = bpy.data.objects.new(nombre + ("__lejos" if lejos else ""), None)
            c.objects.link(e)
            e.matrix_world = Matrix.Translation((x + (ed.ancho + 8) * lejos, -400.0, 0))
            hijos = []
            for k, (p, ml, col) in enumerate(ed.piezas):
                me = bib.malla(p, lejos)
                if me is None:
                    continue
                ob = bib.copia(p, ml, col, padre=e, col=c, nombre_obj=f"{e.name}.{k:03d}")
                ob.data = me
                hijos.append(ob)
            grupos.append(hijos)
        tris = [sum(sum(len(p.vertices) - 2 for p in h.data.polygons) for h in g) for g in grupos]
        entradas.append((nombre, "Ejemplos", grupos[0], grupos[1], tris[0], tris[1], True))
        x += 2 * ed.ancho + 40
    bpy.data.collections["Kit_Mallas_Ejemplos"].hide_render = True
    return entradas


def miniaturas(entradas, carpeta, muestras):
    """Renderiza cada pieza (detallada a la izquierda, simple a la derecha) en vista de 3/4 y monta la hoja."""
    E.configurar_render(520, 360, muestras)
    s = bpy.context.scene
    E.iluminar("dia")
    s.view_settings.exposure = -0.9
    MAT.ajustar_niebla(1e6, 1e6, 0.0, (1, 1, 1))
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
    todos = [o for e in entradas for o in e[2] + e[3]]
    for o in todos:
        o.hide_render = True
    rutas = []
    for (nombre, cat, det, sim, td, ts, simple) in entradas:
        obs = det + sim
        for o in obs:
            o.hide_render = False
        lo, hi = _caja(obs)
        c = (lo + hi) / 2
        r = float(np.linalg.norm(hi - lo)) / 2
        suelo.location = (0, 0, max(float(lo[2]), -0.6))
        d = np.array([-0.45, -1.0, 0.55])
        d /= np.linalg.norm(d)
        dist = r / math.tan(math.radians(15)) * 1.0
        E.camara(tuple(c + d * dist), tuple(c), lente=50, recorte=(0.1, 5000))
        ruta = os.path.join(tmp, f"{nombre}.png")
        E.render(ruta)
        etiqueta = f"{nombre}  {td} / " + ("—" if simple is K.SIN_LEJOS else str(ts))
        rutas.append((ruta, etiqueta))
        for o in obs:
            o.hide_render = True
    s.collection.objects.unlink(suelo)
    col, tw, th = 6, 390, 270
    filas = math.ceil(len(rutas) / col)
    cab = 110
    hoja = Image.new("RGB", (col * tw, cab + filas * (th + 30)), (24, 26, 30))
    dr = ImageDraw.Draw(hoja)
    dr.text((20, 18), "Kit de construcción · Valle del Alba (optimizado)", font=fuente_texto(36), fill=(245, 236, 214))
    dr.text((20, 66), "En cada pieza: detallada (izquierda) y simple, para lejos (derecha). "
                      "Números: triángulos detallada / simple (— = de lejos no se dibuja).", font=fuente_texto(17),
            fill=(200, 200, 200))
    f = fuente_texto(15)
    for i, (ruta, etiqueta) in enumerate(rutas):
        im = Image.open(ruta).resize((tw, th), Image.LANCZOS)
        x, y = (i % col) * tw, cab + (i // col) * (th + 30)
        hoja.paste(im, (x, y))
        dr.text((x + 6, y + th + 6), etiqueta, font=f, fill=(230, 230, 230))
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
    ra, rd = AT.generar(os.path.abspath(os.path.join(a.salida, "texturas")))
    mats["Atlas_Kit"] = MAT.material_atlas(ra, rd)
    entradas = construir(mats, set(a.solo.split(",")) if a.solo else None)
    print(f"{len(entradas)} entradas")
    for (n, cat, det, sim, td, ts, simple) in entradas:
        print(f"  {n:26s} {td:6d} / {ts:5d}")
    if not a.sin_miniaturas:
        print("hoja:", miniaturas(entradas, a.salida, a.muestras))
    if not a.solo:
        bpy.context.scene.camera = None
        ruta = os.path.abspath(os.path.join(a.salida, "kit_valle_del_alba.blend"))
        for img in bpy.data.images:
            if img.filepath:
                img.filepath = bpy.path.relpath(img.filepath, start=os.path.dirname(ruta))
        bpy.context.preferences.filepaths.save_version = 0
        bpy.ops.wm.save_as_mainfile(filepath=ruta, compress=True)


if __name__ == "__main__":
    main()
