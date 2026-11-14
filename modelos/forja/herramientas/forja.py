"""
Genera las piezas de la forja: modela, hornea el atlas PBR, exporta el FBX y guarda una vista de comprobación.

    python forja.py [--piezas yunque,horno,...] [--tam 1024] [--salida modelos/forja]

Cada pieza se guarda también en <salida>/_render_tmp/<pieza>.blend; con ellas hojas.py monta las imágenes finales.
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import nodos  # noqa: E402
import piezas  # noqa: E402
import proceso as pr  # noqa: E402

LIMITES = {"yunque": 5000, "horno": 8000, "mesa": 4000, "barril": 1500, "estanteria": 4000, "suelo": 2000}


def generar(clave, salida, tam, vista=True):
    t0 = time.time()
    scn = pr.escena_vacia()
    pieza, cfg = piezas.PIEZAS[clave]()
    nombre = pieza.nombre
    mats = {m: nodos.crear(nombre, m, cfg) for m in pieza.mats}
    ob = pieza.objeto(mats)
    pr.desplegar(ob)
    con_emision = "brasa" in mats
    mat, rutas = pr.hornear(ob, os.path.join(salida, "texturas"), nombre, tam=tam, con_emision=con_emision)
    por_mat = pr.poner_material(ob, mat)
    objetos = [ob]
    if con_emision:
        objetos.append(pr.separar(ob, por_mat["brasa"], nombre + "_brasas"))
    tris = {o.name: pr.triangulos(o) for o in objetos}
    total = sum(tris.values())
    mn, mx = pr.caja(objetos)
    pr.exportar_fbx(os.path.join(salida, nombre + ".fbx"), objetos)
    # Datos en ejes de Roblox (X, Y arriba, Z = -Y de Blender), tal como queda la pieza en Studio con el giro ya aplicado.
    def rbx(v):
        return [round(v.x, 3), round(v.z, 3), round(-v.y, 3)]

    datos = {
        "pieza": nombre, "triangulos": total, "limite": LIMITES[clave], "mallas": tris,
        "tamano_studs": [round(mx.x - mn.x, 3), round(mx.z - mn.z, 3), round(mx.y - mn.y, 3)],
        "centro_caja": rbx((mn + mx) / 2),
        "texturas": {k: os.path.basename(v) for k, v in rutas.items()},
        "anclajes": {k: rbx(Vector(v)) for k, v in cfg.get("anclajes", {}).items()},
        "nota": cfg.get("nota", ""),
    }
    os.makedirs(os.path.join(salida, "datos"), exist_ok=True)
    with open(os.path.join(salida, "datos", nombre + ".json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    tmp = os.path.join(salida, "_render_tmp")
    os.makedirs(tmp, exist_ok=True)
    for im in bpy.data.images:
        if im.filepath:
            im.filepath = os.path.abspath(bpy.path.abspath(im.filepath))
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(tmp, clave + ".blend"), relative_remap=False)
    estado = "OK" if total <= LIMITES[clave] else "SE PASA"
    print(f"[{estado}] {nombre}: {total} tris (límite {LIMITES[clave]}), {datos['tamano_studs']} studs, "
          f"{time.time() - t0:.0f} s de modelado y horneado")
    if vista:
        pr.estudio(scn)
        pr.suelo_estudio(scn)
        rutas_v = []
        for i, (az, el) in enumerate(((-35, 22), (145, 28))):
            _, c, radio = pr.encuadrar(scn, objetos, az, el)
            ls = pr.luces_pieza(scn, c, radio)
            rutas_v.append(pr.render(scn, os.path.join(tmp, f"{clave}_{i}.png"), 760, 760, 40))
            for l in ls:
                bpy.data.objects.remove(l)
        from PIL import Image
        ims = [Image.open(r) for r in rutas_v]
        hoja = Image.new("RGB", (760 * len(ims), 760))
        for i, im in enumerate(ims):
            hoja.paste(im, (760 * i, 0))
        hoja.save(os.path.join(tmp, f"{clave}_vista.jpg"), quality=88)
    return datos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--piezas", default=",".join(LIMITES))
    ap.add_argument("--tam", type=int, default=1024)
    ap.add_argument("--salida", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
    ap.add_argument("--sin-vista", action="store_true")
    a = ap.parse_args()
    salida = os.path.abspath(a.salida)
    for clave in a.piezas.split(","):
        generar(clave, salida, a.tam, vista=not a.sin_vista)


if __name__ == "__main__":
    main()
