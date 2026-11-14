"""
Imágenes finales de la forja, a partir de las piezas ya horneadas (_render_tmp/<pieza>.blend):
  * renders/forja_montada.png y forja_montada_2.png: todas las piezas colocadas como en el juego (MONTAJE).
  * renders/hoja_piezas.png: cada pieza por separado, con su nombre, triángulos y medidas.
  * datos/forja_montaje.json: dónde va cada pieza, en ejes de Roblox.

    python hojas.py [--solo montada|piezas] [--muestras 96]
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import piezas  # noqa: E402
import proceso as pr  # noqa: E402

ORDEN = ["yunque", "horno", "mesa", "barril", "estanteria", "suelo"]


def fuente(tam, negrita=True):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if negrita else "")
    return ImageFont.truetype(ruta, tam) if os.path.exists(ruta) else ImageFont.load_default(tam)


def cargar(tmp, clave):
    """Trae del .blend de la pieza sus mallas (forja_*)."""
    ruta = os.path.join(tmp, clave + ".blend")
    with bpy.data.libraries.load(ruta) as (origen, destino):
        destino.objects = [n for n in origen.objects if n.startswith("forja_")]
    obs = [o for o in destino.objects if o is not None]
    for o in obs:
        bpy.context.scene.collection.objects.link(o)
    return obs


def matriz_montaje(clave):
    x, y, giro = piezas.MONTAJE[clave]
    z = 0.0 if clave == "suelo" else piezas.ALTO_SUELO
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(giro), 4, "Z")


def maniqui(scn, pos, giro=0.0):
    """Figura R6 gris (5 studs de alto) para ver la escala."""
    m = bpy.data.materials.new("maniqui")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.2, 0.21, 0.23, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    obs = []
    base = Matrix.Translation(pos) @ Matrix.Rotation(math.radians(giro), 4, "Z")
    for c, t in (((0, 0, 3), (2, 1, 2)), ((0, 0, 4.6), (1.2, 1.2, 1.2)), ((-1.5, 0, 3), (1, 1, 2)),
                 ((1.5, 0, 3), (1, 1, 2)), ((-0.5, 0, 1), (1, 1, 2)), ((0.5, 0, 1), (1, 1, 2))):
        bpy.ops.mesh.primitive_cube_add(size=1)
        o = bpy.context.active_object
        o.data.materials.append(m)
        o.matrix_world = base @ Matrix.Translation(c) @ Matrix.Diagonal((*t, 1.0))
        obs.append(o)
    return obs


def montada(salida, tmp, muestras):
    scn = pr.escena_vacia()
    pr.estudio(scn, fuerza_mundo=1.0)
    scn.world.node_tree.nodes["Background"].inputs[0].default_value = (0.012, 0.015, 0.024, 1)
    pr.suelo_estudio(scn, color=(0.022, 0.02, 0.018))
    montaje = {}
    for clave in ORDEN:
        m = matriz_montaje(clave)
        obs = cargar(tmp, clave)
        for o in obs:
            o.matrix_world = m
        with open(os.path.join(salida, "datos", f"forja_{clave}.json"), encoding="utf-8") as f:
            d = json.load(f)
        x, y, giro = piezas.MONTAJE[clave]
        for o in obs:
            mn, mx = pr.caja([o])                          # ya colocado (Blender)
            c = (mn + mx) / 2
            local = m.inverted() @ c                       # centro de la malla en el marco de la pieza
            montaje[o.name] = {
                "posicion": [round(c.x, 3), round(c.z, 3), round(-c.y, 3)], "giro_y_grados": giro,
                "anclajes": {k: [round(v[0] - local.x, 3), round(v[1] - local.z, 3), round(v[2] + local.y, 3)]
                             for k, v in d["anclajes"].items()} if o.name == d["pieza"] else {},
            }
    with open(os.path.join(salida, "datos", "forja_montaje.json"), "w", encoding="utf-8") as f:
        json.dump({"nota": "Posición del centro de cada MeshPart (studs, ejes de Roblox) respecto al centro del suelo "
                           "a ras de tierra, y giro sobre el eje Y. CFrame = CFrame.new(posicion) * "
                           "CFrame.Angles(0, math.rad(giro_y_grados), 0). anclajes: Position de cada Attachment "
                           "dentro de su MeshPart.",
                   "piezas": montaje}, f, ensure_ascii=False, indent=2)
    # Luz: noche fría, una clave suave para que se lea todo y el fuego del horno
    hx_, hy, _ = piezas.MONTAJE["horno"]
    pr.luz(scn, "luna", "AREA", 26000, (-16, -26, 30), (0.62, 0.72, 1.0), 22, (0, 0, 3))
    pr.luz(scn, "relleno", "AREA", 9000, (26, -16, 12), (1.0, 0.86, 0.7), 20, (0, 0, 4))
    pr.luz(scn, "contra", "AREA", 14000, (10, 26, 22), (0.6, 0.7, 1.0), 14, (0, 0, 5))
    pr.luz(scn, "fuego", "POINT", 9000, (hx_, hy - 3.3, 3.2), (1.0, 0.42, 0.1), 0.6)
    pr.luz(scn, "fuego2", "POINT", 2500, (hx_, hy - 1.0, 3.2), (1.0, 0.45, 0.12), 0.5)
    os.makedirs(os.path.join(salida, "renders"), exist_ok=True)
    pr.camara(scn, (15.5, -31, 15), (-0.8, 0.5, 5.2), lente=36)
    pr.render(scn, os.path.join(salida, "renders", "forja_montada.png"), 1920, 1200, muestras)
    bpy.data.objects.remove(scn.camera)
    man = maniqui(scn, (5.6, -6.2, piezas.ALTO_SUELO), 160)
    pr.camara(scn, (4.5, -31, 6.5), (-0.8, 0.5, 5.6), lente=30)
    pr.render(scn, os.path.join(salida, "renders", "forja_montada_2.png"), 1920, 1200, muestras)
    for o in man:
        bpy.data.objects.remove(o)


def hoja_piezas(salida, tmp, muestras, tam=640):
    filas = []
    for clave in ORDEN:
        scn = pr.escena_vacia()
        pr.estudio(scn)
        pr.suelo_estudio(scn)
        obs = cargar(tmp, clave)
        with open(os.path.join(salida, "datos", f"forja_{clave}.json"), encoding="utf-8") as f:
            d = json.load(f)
        if clave == "horno":
            c = pr.caja(obs)
            pr.luz(scn, "fuego", "POINT", 1500, (0, -3.3, 2.6), (1.0, 0.42, 0.1), 0.5)
        fila = []
        malla = pr.material_malla()
        vistas = [(-35, 20, False), (145, 26, False), (-35, 20, True)]
        if clave == "suelo":
            vistas = [(-25, 38, False), (155, 50, False), (-25, 38, True)]
        for i, (az, el, alambre) in enumerate(vistas):
            _, c, radio = pr.encuadrar(scn, obs, az, el, margen=1.05)
            ls = pr.luces_pieza(scn, c, radio)
            scn.view_layers[0].material_override = malla if alambre else None
            ruta = os.path.join(tmp, f"hoja_{clave}_{i}.png")
            pr.render(scn, ruta, tam, tam, muestras)
            fila.append(ruta)
            for l in ls:
                bpy.data.objects.remove(l)
        filas.append((d, fila))
    cab = 96
    hoja = Image.new("RGB", (3 * tam, cab + len(filas) * tam), (14, 14, 16))
    dib = ImageDraw.Draw(hoja)
    dib.text((20, 14), "Forja del planeta humano · piezas", fill=(255, 190, 110), font=fuente(34))
    dib.text((22, 60), "Cada pieza: vista delantera, vista trasera y malla. Medidas en studs (ancho × alto × fondo). "
                       "Atlas PBR de 1024 px por pieza.", fill=(200, 200, 205), font=fuente(17, False))
    for j, (d, fila) in enumerate(filas):
        y = cab + j * tam
        for i, ruta in enumerate(fila):
            hoja.paste(Image.open(ruta).convert("RGB"), (i * tam, y))
            dib.rectangle((i * tam, y, (i + 1) * tam - 1, y + tam - 1), outline=(40, 40, 46))
        t = d["tamano_studs"]
        dib.text((16, y + 12), d["pieza"] + ".fbx", fill=(255, 255, 255), font=fuente(26))
        dib.text((16, y + 46), f"{d['triangulos']:,} tris (límite {d['limite']:,})  ·  {t[0]:.1f} × {t[1]:.1f} × {t[2]:.1f} studs"
                 .replace(",", "."), fill=(255, 190, 110), font=fuente(17))
        dib.text((2 * tam + 16, y + 12), "malla", fill=(255, 255, 255), font=fuente(20))
    ruta = os.path.join(salida, "renders", "hoja_piezas.png")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    hoja.save(ruta)
    print("[ok]", ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", default="")
    ap.add_argument("--muestras", type=int, default=96)
    ap.add_argument("--salida", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    a = ap.parse_args()
    salida = os.path.abspath(a.salida)
    tmp = os.path.join(salida, "_render_tmp")
    if a.solo in ("", "montada"):
        montada(salida, tmp, a.muestras)
    if a.solo in ("", "piezas"):
        hoja_piezas(salida, tmp, a.muestras)


if __name__ == "__main__":
    main()
