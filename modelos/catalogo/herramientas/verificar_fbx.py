"""Reimporta un FBX del catálogo y muestra mallas, triángulos, tamaño en unidades del archivo (studs), UV y materiales.

    python verificar_fbx.py ruta/modelo.fbx [...]
"""
import sys

import bpy

for ruta in sys.argv[1:]:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta)
    print(ruta)
    for o in bpy.data.objects:
        if o.type != "MESH":
            print("  ", o.type, o.name)
            continue
        me = o.data
        tris = sum(len(p.vertices) - 2 for p in me.polygons)
        # El importador de Blender lee el FBX en centímetros: ×100 = unidades del archivo = studs.
        d = [round(v * 100, 2) for v in o.dimensions]
        img = [n.image.name for m in me.materials if m and m.node_tree for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image]
        print(f"   {o.name}: {tris} tri · {d} studs · UV {len(me.uv_layers)} · mat {[m.name for m in me.materials]} · tex {img}")
