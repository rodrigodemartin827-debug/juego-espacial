"""
Utilidades de escena para Blender (Cycles sin pantalla): cielo, sol, cámaras y render. Las «luces del día» de cada
render (día, atardecer) están en ILUMINACIONES: todo ajustable aquí.
"""

import math

import bpy
import numpy as np
from mathutils import Matrix, Vector

import materiales as MAT

# Cada iluminación: altura y rumbo del sol (grados, respecto al marco local del sitio: rumbo 0 = norte, 90 = este),
# fuerza, color, niebla (inicio, distancia, máximo, color sRGB) y luces encendidas.
ILUMINACIONES = {
    "dia": dict(elevacion=38.0, rumbo=235.0, fuerza=4.2, color="#FFF3E0", cielo=1.0, aire=1.0, polvo=1.4,
                niebla=(260.0, 3200.0, 0.55, "#B9CCE0"), luces=0.0, exposicion=-0.7),
    "manana": dict(elevacion=24.0, rumbo=120.0, fuerza=3.8, color="#FFE6C4", cielo=1.0, aire=1.0, polvo=1.8,
                   niebla=(200.0, 2600.0, 0.6, "#C8D2DC"), luces=0.0, exposicion=-0.6),
    "atardecer": dict(elevacion=3.2, rumbo=268.0, fuerza=4.5, color="#FFB070", cielo=1.0, aire=1.2, polvo=3.0,
                      niebla=(120.0, 1500.0, 0.75, "#E6A880"), brillo_niebla=1.4, luces=1.6, exposicion=-0.1),
}


def limpiar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def configurar_render(ancho=1600, alto=900, muestras=64, ruta=None):
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    s.cycles.device = "CPU"
    s.cycles.samples = muestras
    s.cycles.use_denoising = True
    s.cycles.denoiser = "OPENIMAGEDENOISE"
    s.cycles.max_bounces = 4
    s.cycles.diffuse_bounces = 2
    s.cycles.glossy_bounces = 2
    s.cycles.transmission_bounces = 2
    s.cycles.transparent_max_bounces = 4
    s.cycles.use_adaptive_sampling = True
    s.cycles.adaptive_threshold = 0.02
    s.render.resolution_x = ancho
    s.render.resolution_y = alto
    s.render.resolution_percentage = 100
    s.render.image_settings.file_format = "PNG"
    s.render.image_settings.color_mode = "RGB"
    s.view_settings.view_transform = "AgX"
    s.view_settings.look = "AgX - Punchy"
    if ruta:
        s.render.filepath = ruta
    s.render.threads_mode = "AUTO"


def mundo_cielo(sol_dir_mundo, ilum):
    """Cielo físico (multiple scattering) con el sol en la dirección dada (vector del mundo, hacia el sol).

    El cielo de Blender toma +Z del mundo como «arriba». En un planeta la vertical cambia de un sitio a otro (en la
    colina del atardecer está inclinada 18°): por eso render.py gira el PLANETA entero (con orientar_planeta) para que
    la vertical del sitio que se mira sea +Z. Sin eso un atardecer local sería un mediodía para el cielo."""
    s = bpy.context.scene
    w = s.world or bpy.data.worlds.new("Cielo")
    s.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    cielo = nt.nodes.new("ShaderNodeTexSky")
    cielo.sky_type = "MULTIPLE_SCATTERING"
    d = Vector(sol_dir_mundo).normalized()
    cielo.sun_elevation = math.asin(max(min(d.z, 1), -1))
    cielo.sun_rotation = math.atan2(d.x, d.y)  # rotación del sol alrededor de Z (0 = +Y)
    cielo.air_density = ilum["aire"]
    cielo.aerosol_density = ilum["polvo"]
    cielo.sun_disc = True
    cielo.sun_intensity = 0.25
    fondo = nt.nodes.new("ShaderNodeBackground")
    fondo.inputs["Strength"].default_value = ilum["cielo"] * 0.22
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(cielo.outputs[0], fondo.inputs[0])
    # Por debajo del horizonte el cielo físico es negro (un «suelo» infinito). En un planeta pequeño la cámara ve
    # direcciones por debajo del horizonte (el limbo del planeta, los reflejos del mar): ahí se pone el color del
    # horizonte, con una transición suave.
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value = 0.0
    mr.inputs["From Max"].default_value = -0.12
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    hz = nt.nodes.new("ShaderNodeBackground")
    ini, dist, mx, col = ilum["niebla"]
    hz.inputs["Color"].default_value = (*MAT.srgb_a_lineal(col), 1)
    hz.inputs["Strength"].default_value = ilum.get("brillo_niebla", 3.0) * 0.7
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs[0], mix.inputs[0])
    nt.links.new(fondo.outputs[0], mix.inputs[1])
    nt.links.new(hz.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs[0])
    return cielo


def sol(sol_dir_mundo, ilum):
    if "Sol" in bpy.data.objects:
        ob = bpy.data.objects["Sol"]
    else:
        luz = bpy.data.lights.new("Sol", "SUN")
        ob = bpy.data.objects.new("Sol", luz)
        bpy.context.scene.collection.objects.link(ob)
    luz = ob.data
    luz.energy = ilum["fuerza"]
    luz.color = MAT.srgb_a_lineal(ilum["color"])
    luz.angle = math.radians(0.8)
    d = Vector(sol_dir_mundo).normalized()
    # la luz SUN apunta por su -Z: se orienta para que -Z = -d
    ob.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return ob


def direccion_sol(arriba, norte, este, elevacion, rumbo):
    """Vector hacia el sol en el marco local (arriba, norte, este) de un sitio."""
    e, r = math.radians(elevacion), math.radians(rumbo)
    v = (np.asarray(arriba) * math.sin(e) + math.cos(e) * (np.asarray(norte) * math.cos(r) +
                                                           np.asarray(este) * math.sin(r)))
    return v / np.linalg.norm(v)


def iluminar(nombre, arriba=(0, 0, 1), norte=(0, 1, 0), este=(1, 0, 0)):
    ilum = ILUMINACIONES[nombre]
    d = direccion_sol(arriba, norte, este, ilum["elevacion"], ilum["rumbo"])
    mundo_cielo(d, ilum)
    sol(d, ilum)
    ini, dist, mx, col = ilum["niebla"]
    MAT.ajustar_niebla(ini, dist, mx, MAT.srgb_a_lineal(col), ilum.get("brillo_niebla", 3.0))
    MAT.ajustar_luces(ilum["luces"])
    bpy.context.scene.view_settings.exposure = ilum["exposicion"]
    return d


def orientar_planeta(este, norte, arriba):
    """Gira toda la escena (colgada de un Empty «Pivote_Planeta») para que el marco local dado sea el del mundo."""
    s = bpy.context.scene
    piv = bpy.data.objects.get("Pivote_Planeta")
    if piv is None:
        piv = bpy.data.objects.new("Pivote_Planeta", None)
        s.collection.objects.link(piv)
        for ob in list(s.objects):
            if ob.parent is None and ob is not piv and ob.type != "LIGHT" and ob.type != "CAMERA":
                ob.parent = piv
    rot = Matrix((Vector(este), Vector(norte), Vector(arriba)))  # mundo -> local
    piv.matrix_world = rot.to_4x4()
    return rot


def camara(posicion, mira, arriba=(0, 0, 1), lente=35.0, nombre="Camara", recorte=(0.5, 20000.0)):
    if nombre in bpy.data.objects:
        ob = bpy.data.objects[nombre]
    else:
        cam = bpy.data.cameras.new(nombre)
        ob = bpy.data.objects.new(nombre, cam)
        bpy.context.scene.collection.objects.link(ob)
    ob.data.lens = lente
    ob.data.clip_start, ob.data.clip_end = recorte
    p = Vector(posicion)
    f = (Vector(mira) - p).normalized()
    up = Vector(arriba).normalized()
    derecha = f.cross(up).normalized()
    up2 = derecha.cross(f)
    rot = Matrix((derecha, up2, -f)).transposed()
    ob.matrix_world = Matrix.Translation(p) @ rot.to_4x4()
    bpy.context.scene.camera = ob
    return ob


def render(ruta):
    bpy.context.scene.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
