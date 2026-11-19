"""
Vuelve a importar pueblo/casa_familia/casa_familia.fbx en una escena vacía y comprueba lo que llega a Roblox:
mallas, triángulos, tamaño en studs, UV única, normales hacia fuera (aristas cerradas) y el pivote de la puerta.

    python pueblo/herramientas/verificar_casa.py
"""

import os
import sys

import bpy  # bpy primero: bmesh viene con él
import bmesh
from mathutils import Vector

RUTA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "casa_familia", "casa_familia.fbx"))

bpy.ops.wm.read_factory_settings(use_empty=True)
# Importar con los mismos ejes con que se exportó: lo que se ve aquí es el modelo YA girado 180° (giro de importación).
bpy.ops.import_scene.fbx(filepath=RUTA, axis_forward="-Z", axis_up="Y")
total = 0
mn, mx = Vector((1e9,) * 3), Vector((-1e9,) * 3)
fallos = []
for o in bpy.context.scene.objects:
    if o.type != "MESH":
        continue
    bm = bmesh.new()
    bm.from_mesh(o.data)
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    abiertas = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    bm.free()
    total += tris
    for v in o.data.vertices:
        w = o.matrix_world @ v.co
        mn = Vector(map(min, mn, w))
        mx = Vector(map(max, mx, w))
    print(f"{o.name:28s} {tris:6d} tris  UV={[u.name for u in o.data.uv_layers]}  aristas_abiertas={abiertas}  "
          f"origen={tuple(round(c, 2) for c in o.matrix_world.translation)}  escala={tuple(round(c, 3) for c in o.scale)}")
    if len(o.data.uv_layers) != 1:
        fallos.append(f"{o.name}: {len(o.data.uv_layers)} UV")
tam = mx - mn
print(f"total {total} triángulos; tamaño {tam.x:.2f} × {tam.y:.2f} × {tam.z:.2f} (unidades de Blender = studs)")
puerta = bpy.data.objects.get("casa_familia_Puerta")
casa = bpy.data.objects.get("casa_familia")
if puerta:
    # Tras el giro la fachada (y la puerta) quedan en +Y de Blender = -Z del FBX = delante en Roblox.
    print("pivote puerta (Blender, ya girado):", tuple(round(c, 3) for c in puerta.matrix_world.translation))
if total > 14000:
    fallos.append(f"{total} triángulos > 14000")
print("FALLOS:", fallos or "ninguno")
sys.exit(1 if fallos else 0)
