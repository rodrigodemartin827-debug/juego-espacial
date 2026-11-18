"""
Reimporta un FBX y muestra cada malla: triángulos, tamaño, centro y origen (en coordenadas del FBX = Roblox,
Y arriba), UV y materiales. Sirve para comprobar el giro, la escala (1 unidad = 1 stud) y los pivotes.

Uso: python pueblo/herramientas/verificar_fbx.py pueblo/casa_ingeniero/casa_ingeniero.fbx
"""

import sys

import bpy
from mathutils import Vector

ruta = sys.argv[-1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="-Z", axis_up="Y")
total = 0


def a_fbx(v):
    # Blender (tras importar con los mismos ejes) → FBX/Roblox: (x, y, z) → (x, z, -y)
    return Vector((v.x, v.z, -v.y))


for o in sorted(bpy.data.objects, key=lambda o: o.name):
    if o.type != "MESH":
        continue
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    total += tris
    pts = [a_fbx(o.matrix_world @ v.co) for v in o.data.vertices]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    print(f"{o.name:38s} {tris:6d} tri  tam {tuple(round(x, 2) for x in mx - mn)}  "
          f"centro {tuple(round(x, 2) for x in (mn + mx) / 2)}  origen {tuple(round(x, 2) for x in a_fbx(o.location))}"
          f"  UV {list(o.data.uv_layers.keys())}  mats {[m.name for m in o.data.materials]}")
print("TOTAL", total)
