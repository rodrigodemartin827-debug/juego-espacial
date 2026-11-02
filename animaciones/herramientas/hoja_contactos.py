"""
Renderiza los fotogramas clave desde tres cámaras (frente, lateral y 3/4) con Cycles en CPU y
los junta en una hoja de contactos con Pillow.
"""

import math
import os

import bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont

import rig_r6 as r6

ANCHO, ALTO = 340, 420
E = r6.ESTUDIO

# Posiciones de cámara en metros.
VISTAS = {
    "Frente": Vector((0.0, -5.0, 0.95)),
    "Lateral": Vector((-5.2, -0.5, 0.95)),  # mirando desde el lado del brazo que pega
    "3/4": Vector((-3.7, -4.0, 1.1)),
}
PUNTO_MIRADO = Vector((-0.1, -0.5, 0.82))


def _material(nombre, color, rugosidad=0.7):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rugosidad
    return mat


def preparar_escena(punto_impacto):
    """punto_impacto = (posición del puño, dirección del golpe) en studs: ahí se coloca el saco."""
    puno, direccion = punto_impacto
    centro_saco = (puno + direccion * 0.62) * E
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 20
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = ANCHO, ALTO
    scn.render.film_transparent = False

    # Suelo con cuadrícula (ayuda a ver si los pies patinan) y saco de golpeo.
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    suelo = bpy.context.active_object
    suelo.name = "Suelo_render"
    mat = bpy.data.materials.new("suelo")
    mat.use_nodes = True
    nt = mat.node_tree
    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Color1"].default_value = (0.62, 0.64, 0.68, 1)
    chk.inputs["Color2"].default_value = (0.5, 0.52, 0.56, 1)
    chk.inputs["Scale"].default_value = 30
    nt.links.new(chk.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    suelo.data.materials.append(mat)

    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.62 * E, location=centro_saco, segments=24, ring_count=16)
    saco = bpy.context.active_object
    saco.name = "Saco_render"
    saco.scale.z = 1.5
    saco.data.materials.append(_material("saco", (0.35, 0.35, 0.4)))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04 * E, depth=3.0 * E, location=centro_saco + Vector((0, 0, -0.75 * E)))
    bpy.context.active_object.name = "Poste_render"
    bpy.context.active_object.data.materials.append(_material("poste", (0.2, 0.2, 0.2)))

    # Luz: cielo claro + sol con sombras suaves.
    scn.world = bpy.data.worlds.new("mundo")
    scn.world.use_nodes = True
    fondo = scn.world.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.82, 0.88, 0.98, 1)
    fondo.inputs["Strength"].default_value = 0.9
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy = 3.5
    sol.angle = math.radians(12)
    objsol = bpy.data.objects.new("sol", sol)
    objsol.rotation_euler = (math.radians(50), 0, math.radians(-35))
    scn.collection.objects.link(objsol)

    cam = bpy.data.cameras.new("cam")
    cam.lens = 62
    objcam = bpy.data.objects.new("cam", cam)
    scn.collection.objects.link(objcam)
    scn.camera = objcam
    objetivo = bpy.data.objects.new("mira", None)
    scn.collection.objects.link(objetivo)
    objetivo.location = PUNTO_MIRADO
    c = objcam.constraints.new("TRACK_TO")
    c.target = objetivo
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return objcam


def _fuente(tam):
    for ruta in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ):
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default(tam)


def renderizar(fotogramas, directorio, salida_hoja, punto_impacto):
    """fotogramas: [(numero, nombre)]. Devuelve la ruta de la hoja."""
    os.makedirs(directorio, exist_ok=True)
    cam = preparar_escena(punto_impacto)
    scn = bpy.context.scene
    rutas = {}
    for nombre_vista, pos in VISTAS.items():
        cam.location = pos
        for o in bpy.data.objects:
            if o.name.endswith("_render") and o.name != "Suelo_render":
                o.hide_render = nombre_vista == "Frente"  # en la vista frontal el saco tapa al personaje
        for f, _ in fotogramas:
            scn.frame_set(f)
            ruta = os.path.join(directorio, f"{nombre_vista.replace('/', '-')}_{f:02d}.png")
            scn.render.filepath = ruta
            bpy.ops.render.render(write_still=True)
            rutas[(nombre_vista, f)] = ruta

    cab_izq, cab_arriba = 90, 54
    hoja = Image.new("RGB", (cab_izq + ANCHO * len(fotogramas), cab_arriba + ALTO * len(VISTAS)), (24, 26, 32))
    d = ImageDraw.Draw(hoja)
    f_tit, f_peq = _fuente(17), _fuente(13)
    for i, (f, nombre) in enumerate(fotogramas):
        x = cab_izq + i * ANCHO
        d.text((x + 8, 6), f"f{f}", fill=(255, 210, 90), font=f_tit)
        d.text((x + 8, 30), nombre, fill=(220, 220, 230), font=f_peq)
        for j, nombre_vista in enumerate(VISTAS):
            hoja.paste(Image.open(rutas[(nombre_vista, f)]).convert("RGB"), (x, cab_arriba + j * ALTO))
    for j, nombre_vista in enumerate(VISTAS):
        d.text((10, cab_arriba + j * ALTO + ALTO // 2 - 10), nombre_vista, fill=(255, 255, 255), font=f_tit)
    hoja.save(salida_hoja)
    return salida_hoja
