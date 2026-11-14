"""
Lo que se hace con cada pieza después de modelarla: UV, horneado del atlas PBR, exportación FBX y comprobaciones.

Horneado (Cycles, CPU), todo sobre la propia malla low-poly:
  * color, rugosidad, metal y luz propia: cada canal del material procedural se conecta a un nodo de emisión y se
    hornea como EMIT (así el color de los metales no sale negro, como pasa con el pase DIFFUSE).
  * normales: pase NORMAL en espacio tangente. Lleva el relieve (bump) de los materiales y las aristas redondeadas
    del nodo Bevel. Formato OpenGL (Y+), el que usa Roblox.
  * oclusión ambiental: se multiplica dentro del color (Roblox no tiene mapa de oclusión).
"""

import math
import os

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

import nodos

# Giro que Roblox Studio aplica al importar las mallas de este proyecto: entran giradas 180° sobre el eje vertical
# (ver MontarRegion.GIRO_IMPORTACION en modelos/region1_valle_del_alba). Aquí se aplica el giro contrario a la malla
# antes de exportar, así que en Studio llega derecha y NO hay que girarla después.
GIRO_IMPORTACION = Matrix.Rotation(math.pi, 4, "Z")  # el eje vertical de Blender (Z) es el Y de Roblox


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "NONE"
    scn.world = bpy.data.worlds.new("mundo")
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.render.threads_mode = "AUTO"
    return scn


def triangulos(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def activar(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def desplegar(ob, margen=0.004):
    """UV automáticas con la misma densidad de texel en toda la pieza, empaquetadas en un atlas."""
    activar(ob)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=margen, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    try:
        bpy.ops.uv.pack_islands(rotate=True, margin=margen, margin_method="ADD", shape_method="CONCAVE")
    except TypeError:
        bpy.ops.uv.pack_islands(rotate=True, margin=margen)
    bpy.ops.object.mode_set(mode="OBJECT")
    ob.data.uv_layers[0].name = "UVMap"


def _imagen(nombre, tam, color):
    img = bpy.data.images.new(nombre, tam, tam, alpha=False, float_buffer=False)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return img


def _destino(ob, img):
    for slot in ob.material_slots:
        nt = slot.material.node_tree
        n = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "destino"
        n.image = img
        nt.nodes.active = n


def _px(img):
    w, h = img.size
    return np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)


def _guardar(img, ruta, gris=False):
    img.filepath_raw = ruta
    img.file_format = "PNG"
    scn = bpy.context.scene
    s = scn.render.image_settings
    s.file_format = "PNG"
    s.color_mode = "BW" if gris else "RGB"
    s.compression = 100
    img.save_render(ruta, scene=scn) if gris else img.save()
    img.filepath = ruta
    img.source = "FILE"
    img.reload()


def hornear(ob, carpeta, nombre, tam=1024, muestras=16, con_emision=False, fuerza_ao=0.6):
    """Hornea el atlas PBR de `ob` y le deja un material único con las texturas. Devuelve {canal: ruta}."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.use_denoising = False
    scn.render.bake.margin = 6
    scn.render.bake.use_selected_to_active = False
    estado = {o: o.hide_render for o in scn.objects}
    for o in scn.objects:
        o.hide_render = o is not ob
    activar(ob)
    os.makedirs(carpeta, exist_ok=True)
    imgs = {}
    canales = [("color", True), ("rug", False), ("metal", False)] + ([("emision", True)] if con_emision else [])
    for canal, es_color in canales:
        for slot in ob.material_slots:
            nodos.modo(slot.material, canal)
        img = _imagen(f"{nombre}_{canal}", tam, es_color)
        _destino(ob, img)
        scn.cycles.samples = muestras
        bpy.ops.object.bake(type="EMIT")
        imgs[canal] = img
    for slot in ob.material_slots:
        nodos.modo(slot.material, "pbr")
    img = _imagen(f"{nombre}_normal", tam, False)
    _destino(ob, img)
    scn.cycles.samples = muestras * 2
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    imgs["normal"] = img
    img = _imagen(f"{nombre}_ao", tam, False)
    _destino(ob, img)
    scn.cycles.samples = 96
    bpy.ops.object.bake(type="AO")
    # Oclusión dentro del color (suave: solo oscurece los rincones)
    c = _px(imgs["color"])
    a = np.clip(_px(img)[..., :1], 0, 1)
    c[..., :3] *= 1.0 - fuerza_ao * (1.0 - a) ** 1.2
    imgs["color"].pixels.foreach_set(c.ravel())
    imgs["color"].update()
    bpy.data.images.remove(img)

    sufijos = {"color": "color", "rug": "rugosidad", "metal": "metal", "normal": "normal", "emision": "emision"}
    rutas = {}
    for canal, img in imgs.items():
        ruta = os.path.join(carpeta, f"{nombre}_{sufijos[canal]}.png")
        _guardar(img, ruta, gris=canal in ("rug", "metal"))
        rutas[canal] = ruta
    for o, h in estado.items():
        o.hide_render = h

    # Material final: lo que verá Roblox en la SurfaceAppearance
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    p = nt.nodes.new("ShaderNodeBsdfPrincipled")
    sal = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(p.outputs[0], sal.inputs[0])

    def tex(canal):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = imgs[canal]
        return n.outputs[0]

    nt.links.new(tex("color"), p.inputs["Base Color"])
    nt.links.new(tex("rug"), p.inputs["Roughness"])
    nt.links.new(tex("metal"), p.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal"), nm.inputs["Color"])
    nt.links.new(nm.outputs[0], p.inputs["Normal"])
    if con_emision:
        nt.links.new(tex("emision"), p.inputs["Emission Color"])
        p.inputs["Emission Strength"].default_value = 5.0
    return mat, rutas


def poner_material(ob, mat):
    """Sustituye los materiales procedurales por el horneado. Devuelve los índices de cara de cada material viejo."""
    por_mat = {}
    for p in ob.data.polygons:
        por_mat.setdefault(ob.material_slots[p.material_index].material.name.split("__")[-1], []).append(p.index)
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.material_index = 0
    return por_mat


def separar(ob, caras, nombre):
    """Saca las caras `caras` de `ob` a un objeto nuevo (mismas UV y material)."""
    otro = ob.copy()
    otro.data = ob.data.copy()
    otro.name = otro.data.name = nombre
    bpy.context.scene.collection.objects.link(otro)
    caras = set(caras)
    for o, quitar_estas in ((ob, True), (otro, False)):
        bm = bmesh.new()
        bm.from_mesh(o.data)
        fuera = [f for f in bm.faces if (f.index in caras) == quitar_estas]
        bmesh.ops.delete(bm, geom=fuera, context="FACES")
        bm.to_mesh(o.data)
        bm.free()
    return otro


def caja(objetos):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objetos:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


def exportar_fbx(ruta, objetos):
    """
    FBX para Roblox: 1 unidad = 1 stud (importar con «Scale Unit = Stud»), Y arriba, -Z delante, y el giro de
    importación ya aplicado a la malla. Lleva incrustadas las texturas de color y normales.
    """
    for o in objetos:
        o.data.transform(GIRO_IMPORTACION)
        o.data.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=True, axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=False, mesh_smooth_type="OFF", use_tspace=False, add_leaf_bones=False, bake_anim=False,
        path_mode="COPY", embed_textures=True)
    for o in objetos:
        o.data.transform(GIRO_IMPORTACION.inverted())
        o.data.update()
    return ruta


# ---- Render de comprobación ----------------------------------------------------------------------------------


def estudio(scn, fuerza_mundo=0.9):
    scn.render.engine = "CYCLES"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    w = scn.world
    w.use_nodes = True
    f = w.node_tree.nodes.get("Background") or w.node_tree.nodes.new("ShaderNodeBackground")
    if not f.outputs[0].is_linked:
        sal = w.node_tree.nodes.get("World Output") or w.node_tree.nodes.new("ShaderNodeOutputWorld")
        w.node_tree.links.new(f.outputs[0], sal.inputs[0])
    f.inputs[0].default_value = (0.05, 0.055, 0.07, 1)
    f.inputs[1].default_value = fuerza_mundo


def luz(scn, nombre, tipo, energia, pos, color=(1, 1, 1), tam=4.0, mira=(0, 0, 1.5)):
    d = bpy.data.lights.new(nombre, tipo)
    d.energy = energia
    d.color = color
    if tipo == "AREA":
        d.size = tam
    elif tipo == "POINT":
        d.shadow_soft_size = tam
    elif tipo == "SUN":
        d.angle = math.radians(tam)
    o = bpy.data.objects.new(nombre, d)
    o.location = pos
    scn.collection.objects.link(o)
    o.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    return o


def camara(scn, pos, mira, lente=50):
    d = bpy.data.cameras.new("cam")
    d.lens = lente
    d.clip_end = 2000
    o = bpy.data.objects.new("cam", d)
    scn.collection.objects.link(o)
    o.location = pos
    o.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    scn.camera = o
    return o


def suelo_estudio(scn, z=0.0, color=(0.03, 0.032, 0.038)):
    bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, z))
    s = bpy.context.active_object
    s.name = "suelo_estudio"
    m = bpy.data.materials.new("suelo_estudio")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1)
    b.inputs["Roughness"].default_value = 1.0
    s.data.materials.append(m)
    return s


def encuadrar(scn, objetos, az, el, lente=50, margen=1.1):
    """Coloca la cámara mirando a `objetos` desde un azimut (0 = frente, -Y) y una elevación en grados."""
    mn, mx = caja(objetos)
    c = (mn + mx) / 2
    radio = (mx - mn).length / 2
    fov = 2 * math.atan(18 / lente)
    dist = radio * margen / math.sin(fov / 2)
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    if scn.camera:
        bpy.data.objects.remove(scn.camera)
    return camara(scn, c + d * dist, c, lente), c, radio


def luces_pieza(scn, c, radio):
    k = radio
    return [
        luz(scn, "clave", "AREA", 230 * k * k, c + Vector((-1.6, -2.2, 2.4)) * k, (1.0, 0.93, 0.84), k * 1.2, c),
        luz(scn, "relleno", "AREA", 70 * k * k, c + Vector((2.6, -1.4, 0.8)) * k, (0.7, 0.8, 1.0), k * 2.5, c),
        luz(scn, "contra", "AREA", 220 * k * k, c + Vector((1.2, 2.6, 2.2)) * k, (1.0, 0.72, 0.5), k * 1.2, c),
    ]


def material_malla():
    m = bpy.data.materials.new("vista_malla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    sal = nt.nodes.new("ShaderNodeOutputMaterial")
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 0.9
    base = nt.nodes.new("ShaderNodeBsdfDiffuse")
    base.inputs["Color"].default_value = (0.3, 0.31, 0.34, 1)
    lin = nt.nodes.new("ShaderNodeEmission")
    lin.inputs["Color"].default_value = (1.0, 0.55, 0.15, 1)
    lin.inputs["Strength"].default_value = 1.4
    mz = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wire.outputs[0], mz.inputs[0])
    nt.links.new(base.outputs[0], mz.inputs[1])
    nt.links.new(lin.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], sal.inputs[0])
    return m


def material_caras_al_reves():
    """Negro por la cara buena y blanco por la de atrás: sirve para contar píxeles de caras vistas del revés."""
    m = bpy.data.materials.new("caras_al_reves")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    sal = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(geo.outputs["Backfacing"], em.inputs[0])
    nt.links.new(em.outputs[0], sal.inputs[0])
    return m


def render(scn, ruta, ancho, alto, muestras=64):
    scn.render.resolution_x = ancho
    scn.render.resolution_y = alto
    scn.render.resolution_percentage = 100
    scn.cycles.samples = muestras
    scn.render.image_settings.file_format = "PNG"
    scn.render.image_settings.color_mode = "RGB"
    scn.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
    return ruta
