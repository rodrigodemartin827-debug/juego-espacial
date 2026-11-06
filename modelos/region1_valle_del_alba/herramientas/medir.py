"""
Mide cuántos triángulos se dibujarían desde una vista: los de todo objeto (o instancia) cuya caja envolvente cae,
aunque sea en parte, dentro del campo de visión de la cámara. Es lo que queda tras el «frustum culling»; no descuenta
lo que tapan otros objetos (Roblox hace algo de oclusión, así que en el juego sería algo menos).

Se cuentan por separado las categorías (terreno, edificios, mobiliario, vegetación, agua, referencia...) y se ignora la
colección de referencia (resto del planeta y mar), que no es de la región.

Uso:
    python modelos/region1_valle_del_alba/herramientas/medir.py --blend <.blend> --vistas 04,10 [--salida datos.json]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import render as RD  # noqa: E402


def categoria(ob):
    """Categoría por la colección (o la colección del padre) del objeto."""
    o = ob
    while o.parent is not None and not o.parent.name.startswith("Pivote"):
        o = o.parent  # una pieza de un edificio cuenta como el edificio
    nombres = [c.name for c in o.users_collection]
    n = " ".join(nombres)
    if "Referencia" in n or o.name.startswith(("Planeta_", "Mar_", "Pivote")):
        return None
    if "Terreno" in n:
        return "terreno"
    if "Edificios" in n:
        return "edificios"
    if "Silueta" in n:
        return "edificios"
    if "Mobiliario" in n or "Caminos" in n:
        return "mobiliario"
    if "Vegetacion" in n or "Fuentes" in n:
        return "vegetacion"
    if "Campos" in n:
        return "campos"
    if "Agua" in n:
        return "agua"
    return "otros"


def triangulos(me):
    me.calc_loop_triangles()
    return len(me.loop_triangles)


def contar(cam):
    dg = bpy.context.evaluated_depsgraph_get()
    s = bpy.context.scene
    proy = cam.calc_matrix_camera(dg, x=s.render.resolution_x, y=s.render.resolution_y)
    vista = cam.matrix_world.inverted()
    pv = proy @ vista
    cache = {}
    tot = {}
    n_obj = {}
    for inst in dg.object_instances:
        ob = inst.instance_object if inst.is_instance else inst.object
        if ob.type != "MESH":
            continue
        orig = ob.original if hasattr(ob, "original") else ob
        par = inst.parent.original if inst.is_instance and inst.parent else None
        cat = categoria(par or orig)
        if cat is None:
            continue
        if (par or orig).hide_render:
            continue
        me = ob.data
        clave = me.name
        if clave not in cache:
            cache[clave] = triangulos(me)
        nt = cache[clave]
        if nt == 0:
            continue
        mw = inst.matrix_world
        bb = [mw @ Vector(c) for c in ob.bound_box]
        dentro = False
        xs, ys, delante, detras = [], [], 0, 0
        for p in bb:
            h = pv @ p.to_4d()
            if h.w <= 1e-6:
                detras += 1
                continue
            delante += 1
            xs.append(h.x / h.w)
            ys.append(h.y / h.w)
        if delante == 0:
            continue
        if detras > 0:
            dentro = True  # cruza el plano de la cámara: se cuenta (conservador)
        else:
            dentro = min(xs) <= 1 and max(xs) >= -1 and min(ys) <= 1 and max(ys) >= -1
        if dentro:
            tot[cat] = tot.get(cat, 0) + nt
            n_obj[cat] = n_obj.get(cat, 0) + 1
    tot["total"] = sum(v for k, v in tot.items())
    return tot, n_obj


def totales():
    """Triángulos de TODA la región si se dibujara todo en su versión detallada (sin LOD ni recorte), y triángulos
    de mallas DISTINTAS (lo que hay que guardar y subir)."""
    dg = bpy.context.evaluated_depsgraph_get()
    tot, unicos, vistos = {}, {}, set()
    for inst in dg.object_instances:
        ob = inst.instance_object if inst.is_instance else inst.object
        if ob.type != "MESH":
            continue
        orig = ob.original
        par = inst.parent.original if inst.is_instance and inst.parent else None
        cat = categoria(par or orig)
        if cat is None:
            continue
        nombre = orig.name
        if nombre.endswith("__lejos") or orig.get("nivel") == "lejos" or orig.name == "Aurora_Silueta":
            continue  # las versiones lejanas no suman en «todo detallado»
        me = ob.data
        nt = triangulos(me)
        tot[cat] = tot.get(cat, 0) + nt
        if me.name not in vistos:
            vistos.add(me.name)
            unicos[cat] = unicos.get(cat, 0) + nt
    tot["total"] = sum(tot.values())
    unicos["total"] = sum(unicos.values())
    return tot, unicos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--vistas", default="04,10")
    ap.add_argument("--salida", default="")
    ap.add_argument("--sin-lod", action="store_true", help="no aplicar el LOD por distancia (escena antigua)")
    ap.add_argument("--todo", action="store_true", help="contar también toda la escena (todo detallado)")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    RD.preparar(os.path.abspath(a.blend))
    res = {}
    for v in [x for x in RD.VISTAS if any(x.startswith(p) for p in a.vistas.split(","))]:
        RD.situar(v, 1920, 64, aplicar_lod=not a.sin_lod)
        tot, n = contar(bpy.context.scene.camera)
        res[v] = dict(triangulos=tot, objetos=n)
        print(v, json.dumps(tot), json.dumps(n), flush=True)
    if a.todo:
        if not a.sin_lod and "LOD" in bpy.data.texts:
            import lod

            # todo en detalle: la cámara «en todas partes» no existe; se fuerza el nivel detallado a mano
            for o in bpy.data.objects:
                if o.get("lod") == "terreno":
                    o.hide_render = o["nivel"] != "detalle"
                elif o.get("lod") == "silueta":
                    o.hide_render = True
                elif "lod" in o.keys() and o["lod"] != "nube":
                    lod._poner_nivel(o, "detalle")
            for o in bpy.data.objects:
                if o.get("lod") == "nube":
                    me = o.data
                    n = len(me.vertices)
                    base = np.zeros(n, np.int32)
                    me.attributes["tipo_base"].data.foreach_get("value", base)
                    me.attributes["tipo"].data.foreach_set("value", base)
                    me.attributes["oculto"].data.foreach_set("value", np.zeros(n, bool))
                    me.update()
        tot, unicos = totales()
        res["todo"] = dict(triangulos=tot, mallas_distintas=unicos)
        print("todo", json.dumps(tot), "distintas", json.dumps(unicos), flush=True)
    if a.salida:
        with open(a.salida, "w") as f:
            json.dump(res, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
