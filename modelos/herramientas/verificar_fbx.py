"""
Reimporta un FBX en una escena vacía y muestra lo que lleva: mallas, triángulos, tamaño en studs, materiales,
texturas y huesos. Sirve para comprobar la exportación sin Studio.

Uso: python modelos/herramientas/verificar_fbx.py <archivo.fbx> [...]
"""

import sys

import bpy

ESTUDIO = 0.28

for ruta in sys.argv[1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta)
    print(f"\n== {ruta}")
    total = 0
    for o in sorted(bpy.context.scene.objects, key=lambda o: o.name):
        if o.type == "MESH":
            tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
            total += tris
            d = o.dimensions / ESTUDIO
            texs = sorted({n.image.name for m in o.data.materials if m and m.node_tree
                           for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image})
            print(f"  malla {o.name!r}: {tris} tri, {d.x:.2f} x {d.y:.2f} x {d.z:.2f} studs (Blender), "
                  f"UV={len(o.data.uv_layers)}, texturas={texs}")
        elif o.type == "ARMATURE":
            print(f"  esqueleto {o.name!r}: huesos {[b.name for b in o.data.bones]}")
    print(f"  TOTAL {total} triángulos")
