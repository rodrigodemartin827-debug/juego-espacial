"""
Quita un edificio de region1_valle_del_alba.blend sin repetir toda la exportación: borra su vacío y sus piezas, lo
saca de datos/edificios_<Sitio>.json y, si es de Aurora, borra su caja de la silueta y vuelve a exportar
silueta/Aurora_Silueta.fbx y datos/silueta_Aurora.json.

En la silueta, cada edificio es una caja (cuatro paredes, dos faldones y dos hastiales). Una cara es del edificio
quitado si, en el marco del edificio, todos sus vértices caen dentro de su caja (con el alero) y en los planos de
esa caja (x = 0, ancho o el vuelo del alero). Así no se toca la cara de un vecino aunque se meta dentro de la caja.
Se comprueba que salen justo 14 triángulos.

Uso:
    blender -b --factory-startup --python modelos/region1_valle_del_alba/herramientas/quitar_edificio.py --
        --blend modelos/region1_valle_del_alba/region1_valle_del_alba.blend
        --salida modelos/region1_valle_del_alba/roblox
        --edificio Aurora_Plaza_NO
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bmesh  # noqa: E402
import bpy  # noqa: E402
import numpy as np  # noqa: E402

import sin_dependencias  # noqa: E402, F401
import exportar as EX  # noqa: E402

TRIANGULOS_CAJA = 14  # 4 paredes y 2 faldones (2 triángulos cada uno) y 2 hastiales


def quitar_de_silueta(sil, ed):
    ancho, fondo = float(ed["ancho"]), float(ed["fondo"])
    a_edificio = np.linalg.inv(np.array(ed.matrix_world)) @ np.array(sil.matrix_world)
    planos_x = (0.0, ancho, -0.8, ancho + 0.8)
    bm = bmesh.new()
    bm.from_mesh(sil.data)
    bm.faces.ensure_lookup_table()
    quitar = []
    for f in bm.faces:
        ps = np.array([(a_edificio @ np.array([*v.co, 1.0]))[:3] for v in f.verts])
        dentro = (ps[:, 0].min() > -0.9 and ps[:, 0].max() < ancho + 0.9 and ps[:, 1].min() > -1.1
                  and ps[:, 1].max() < fondo + 1.1 and ps[:, 2].min() > -1.6)
        en_planos = all(min(abs(x - p) for p in planos_x) < 0.05 for x in ps[:, 0])
        if dentro and en_planos:
            quitar.append(f)
    tris = sum(len(f.verts) - 2 for f in quitar)
    if tris != TRIANGULOS_CAJA:
        raise RuntimeError(f"la caja de {ed.name} en la silueta tiene {tris} triángulos, se esperaban {TRIANGULOS_CAJA}")
    bmesh.ops.delete(bm, geom=quitar, context="FACES")
    sueltos = [v for v in bm.verts if not v.link_faces]
    bmesh.ops.delete(bm, geom=sueltos, context="VERTS")
    bm.to_mesh(sil.data)
    bm.free()
    print(f"silueta: quitados {tris} triángulos de {ed.name}")


def exportar_silueta(sil, sal):
    # Mismas cuentas que exportar.py.
    centro, tam = EX.caja_malla(sil.data)
    p, Rr, _ = EX.a_roblox_m(np.array(sil.matrix_world))
    datos = dict(nombre=sil.name, fbx="silueta/Aurora_Silueta.fbx", cframe=EX.cframe(p, Rr),
                 centro=[round(float(v), 4) for v in EX.C @ centro],
                 tamano=[round(float(v), 4) for v in np.abs(EX.C @ tam)],
                 triangulos=EX.triangulos(sil.data),
                 centro_lod=[round(float(v), 3) for v in EX.C @ np.array(sil["centro"])])
    with open(os.path.join(sal, "datos", "silueta_Aurora.json"), "w") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
    t = EX.objeto_temporal(sil.data, sil.name)
    EX.exportar_fbx(t, os.path.join(sal, "silueta", "Aurora_Silueta.fbx"))
    bpy.data.objects.remove(t)
    print(f"silueta exportada: {datos['triangulos']} triángulos")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--edificio", required=True)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))
    sal = os.path.abspath(a.salida)

    ed = bpy.data.objects.get(a.edificio)
    if ed is None or ed.type != "EMPTY" or "ancho" not in ed.keys():
        raise RuntimeError(f"no hay un edificio {a.edificio} en el .blend")
    sitio = ed.get("sitio") or "Region"

    sil = bpy.data.objects.get("Aurora_Silueta")
    if sitio == "Aurora" and sil is not None:
        quitar_de_silueta(sil, ed)
        exportar_silueta(sil, sal)

    ruta = os.path.join(sal, "datos", f"edificios_{sitio}.json")
    with open(ruta, encoding="utf-8") as f:
        lista = json.load(f)
    antes = len(lista)
    lista = [e for e in lista if e["nombre"] != a.edificio]
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(lista, f, ensure_ascii=False, separators=(",", ":"))
    print(f"edificios_{sitio}: {antes} -> {len(lista)}")

    hijos = list(ed.children)
    for h in hijos:
        bpy.data.objects.remove(h)
    bpy.data.objects.remove(ed)
    print(f"{a.edificio}: borrado del .blend con {len(hijos)} piezas")
    bpy.ops.wm.save_mainfile()


main()
