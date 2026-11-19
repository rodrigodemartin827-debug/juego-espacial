"""Render de revisión de cerca a partir del FBX exportado (solo para revisar, no es parte de la entrega).
python primer_plano.py <ruta.fbx> <salida.png> az el dist objetivo_x objetivo_y objetivo_z"""
import math, sys, json, os
import bpy
from mathutils import Vector as V
a = sys.argv[1:]
fbx, out = a[0], a[1]
az, el, dist = map(float, a[2:5]); obj = V(map(float, a[5:8]))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
datos = json.load(open(fbx[:-4] + ".json"))
col = {p["nombre"]: p for p in datos["piezas"]}
def h(x):
    x = x.lstrip("#"); return tuple((int(x[i:i+2], 16) / 255) ** 2.2 for i in (0, 2, 4))
for o in bpy.context.scene.objects:
    if o.type != "MESH": continue
    p = col.get(o.name)
    if p and p["tipo"] != "textura":
        m = bpy.data.materials.new(o.name); m.use_nodes = True
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*h(p["color"]), 1)
        if p["tipo"] == "neon":
            b.inputs["Emission Color"].default_value = (*h(p["color"]), 1); b.inputs["Emission Strength"].default_value = 6
        else:
            b.inputs["Transmission Weight"].default_value = 1; b.inputs["Roughness"].default_value = 0.03
        o.data.materials.clear(); o.data.materials.append(m)
scn = bpy.context.scene
scn.render.engine = "CYCLES"; scn.cycles.samples = 48; scn.cycles.use_denoising = True
scn.render.resolution_x = 1100; scn.render.resolution_y = 800
scn.view_settings.view_transform = "AgX"
scn.world = bpy.data.worlds.new("w"); scn.world.use_nodes = True
scn.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.5, 0.55, 0.62, 1)
scn.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.6
s = bpy.data.lights.new("sol", "SUN"); s.energy = 3.5; so = bpy.data.objects.new("sol", s); scn.collection.objects.link(so)
so.rotation_euler = (math.radians(50), 0, math.radians(200))
# tras importar, el frente del modelo está en +Y de Blender
ar, er = math.radians(az), math.radians(el)
d = V((-math.sin(ar) * math.cos(er), math.cos(ar) * math.cos(er), math.sin(er)))
cd = bpy.data.cameras.new("c"); cd.lens = 40; cam = bpy.data.objects.new("c", cd); scn.collection.objects.link(cam)
cam.location = obj + d * dist
cam.rotation_euler = (obj - cam.location).to_track_quat("-Z", "Y").to_euler(); scn.camera = cam
scn.render.filepath = out; bpy.ops.render.render(write_still=True)
