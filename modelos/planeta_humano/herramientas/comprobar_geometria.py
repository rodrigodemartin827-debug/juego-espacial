"""Pasada rápida: construye la geometría de los modelos (sin hornear) y avisa de errores, tamaño y presupuesto."""
import sys
import traceback

import bpy
import bmesh
from mathutils import Vector

import generar
from geometria import Modelo
from tuberia import PRESUPUESTOS

M = generar.cargar()
nombres = sys.argv[1:] or sorted(M, key=lambda n: M[n]["num"])
for n in nombres:
    info = M[n]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        m = Modelo(n, info)
        info["fn"](m)
        tris = 0
        ab = 0
        mn, mx = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        for d in m.partes.values():
            bm = d["bm"]
            tris += sum(len(f.verts) - 2 for f in bm.faces)
            ab += sum(1 for e in bm.edges if len(e.link_faces) != 2)
            for v in bm.verts:
                mn = Vector(map(min, mn, v.co))
                mx = Vector(map(max, mx, v.co))
        d = mx - mn
        ob = info["objetivo"]
        pres = PRESUPUESTOS[info["categoria"]]
        avisos = []
        if tris > pres:
            avisos.append("TRIS")
        if ab:
            avisos.append(f"abiertas={ab}")
        if any(abs(a - b) > max(0.6, 0.18 * b) for a, b in zip((d.x, d.y, d.z), ob)):
            avisos.append("TAMAÑO")
        if mn.z < -0.3:
            avisos.append(f"zmin={mn.z:.2f}")
        print(f"{info['num']:3d} {n:32s} {tris:6d}/{pres:<6d} {d.x:5.1f}x{d.y:5.1f}x{d.z:5.1f} obj {ob} {' '.join(avisos)}", flush=True)
    except Exception:
        print(f"{info['num']:3d} {n:32s} ERROR", flush=True)
        traceback.print_exc(limit=3)
