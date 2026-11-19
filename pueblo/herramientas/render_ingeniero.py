"""
Renders de revisión de la casa del ingeniero (Cycles, con las texturas horneadas: lo que llegará a Roblox).

  * casa_ingeniero_turnaround.png: 8 vistas alrededor, cada 45°.
  * casa_ingeniero_detalles.png: primeros planos (puertas, ventana del lab, silla, techo, generador...) + malla.
"""

import math
import os

import bpy
from mathutils import Vector
from PIL import Image

import kit_casas as K

V = Vector

# (nombre, azimut desde el frente (-Y) hacia la derecha, elevación) — giro completo cada 45°
VISTAS_GIRO = [("Frente", 0, 14), ("Frente-derecha", 45, 18), ("Derecha (lab)", 90, 14),
               ("Detrás-derecha", 135, 20), ("Detrás", 180, 14), ("Detrás-izquierda", 225, 20),
               ("Izquierda", 270, 14), ("Frente-izquierda", 315, 18)]

# primeros planos: (nombre, posición de la cámara, punto al que mira, lente)
DETALLES = [
    ("Puerta principal", (-1.2, -11.5, 3.6), (-2.1, -4.5, 3.0), 50),
    ("Placa y cerradura", (-1.7, -7.9, 4.1), (-1.85, -4.4, 3.55), 42),
    ("Puerta del lab y cámara", (10.5, -10.5, 3.4), (9.0, -2.2, 2.4), 40),
    ("Ventana del lab (dentro)", (16.5, 0.6, 3.0), (10.0, 0.4, 2.6), 45),
    ("Silla de pensar", (-3.0, -8.6, 3.4), (-4.85, -5.85, 1.6), 50),
    ("Techo técnico", (-9.0, -9.5, 15.5), (0.0, 0.5, 7.0), 32),
    ("Generador y RAEE", (15.8, -5.8, 3.6), (11.8, 0.2, 1.0), 38),
    ("Cuadro eléctrico y panel FV-X", (-11.8, -9.6, 4.4), (-6.6, -3.4, 1.8), 40),
    ("Estación meteo y antenas", (-6.5, -9.0, 10.5), (-1.5, 0.5, 8.6), 40),
    ("Malla", None, None, 0),
]


def _camara(pos, mira, lente):
    scn = bpy.context.scene
    cam = scn.camera
    if cam is None:
        d = bpy.data.cameras.new("cam_rev")
        cam = bpy.data.objects.new("cam_rev", d)
        scn.collection.objects.link(cam)
        scn.camera = cam
    cam.data.lens = lente
    cam.data.clip_end = 1000
    cam.location = V(pos)
    cam.rotation_euler = (V(mira) - V(pos)).to_track_quat("-Z", "Y").to_euler()
    return cam


def _material_malla():
    m = bpy.data.materials.new("vista_malla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 0.9
    base = nt.nodes.new("ShaderNodeBsdfDiffuse")
    base.inputs["Color"].default_value = (0.5, 0.52, 0.56, 1)
    linea = nt.nodes.new("ShaderNodeEmission")
    linea.inputs["Color"].default_value = (0.15, 0.75, 1.0, 1)
    linea.inputs["Strength"].default_value = 1.4
    mez = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wire.outputs["Fac"], mez.inputs["Fac"])
    nt.links.new(base.outputs["BSDF"], mez.inputs[1])
    nt.links.new(linea.outputs["Emission"], mez.inputs[2])
    nt.links.new(mez.outputs["Shader"], out.inputs["Surface"])
    return m


def _render(ruta, tam, muestras):
    scn = bpy.context.scene
    scn.render.resolution_x, scn.render.resolution_y = tam
    scn.cycles.samples = muestras
    scn.render.filepath = ruta
    bpy.ops.render.render(write_still=True)


def renderizar_todo(objetos, salida, nombre, rapido, total, tris):
    tmp = os.path.join(salida, "_tmp", "render")
    os.makedirs(tmp, exist_ok=True)
    K.preparar_estudio(radio_suelo=80)
    scn = bpy.context.scene
    scn.render.film_transparent = False
    # los cristales de Roblox no refractan: aquí se renderizan finos (sin desviar) para parecerse
    cr = bpy.data.materials.get("cristal")
    if cr:
        b = cr.node_tree.nodes["Principled BSDF"]
        b.inputs["IOR"].default_value = 1.05
        try:
            b.inputs["Thin Wall"].default_value = True
        except (TypeError, AttributeError):
            pass
    # Luces interiores: las mismas que indica el JSON para Studio (sin ellas, los interiores salen negros)
    for n_luz, pos, energia, color in (("luz_lab", (9.2, 0.4, 4.2), 60, (0.9, 0.95, 1.0)),
                                        ("luz_casa", (1.0, -1.5, 5.6), 90, (1.0, 0.92, 0.8))):
        ld = bpy.data.lights.new(n_luz, "POINT")
        ld.energy = energia
        ld.color = color
        ld.shadow_soft_size = 0.6
        lo = bpy.data.objects.new(n_luz, ld)
        lo.location = pos
        # que no se vea la bola de luz (tampoco a través del cristal, que cuenta como transmisión)
        lo.visible_camera = lo.visible_transmission = lo.visible_glossy = False
        scn.collection.objects.link(lo)
    scn.cycles.max_bounces = 8
    scn.cycles.transparent_max_bounces = 8
    tam = (640, 480) if rapido else (1000, 750)
    muestras = 24 if rapido else 96

    # centro del conjunto (casa + lab) y distancia para que quepa
    centro = V((1.8, -1.5, 3.4))
    dist = 28.5
    rutas = []
    for n, az, el in VISTAS_GIRO:
        a, e = math.radians(az), math.radians(el)
        d = V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        _camara(centro + d * dist, centro, 40)
        r = os.path.join(tmp, f"giro_{len(rutas):02d}.png")
        _render(r, tam, muestras)
        rutas.append((n, r))
        print("[render]", n)
    notas = [f"{total} triángulos (presupuesto 14.000) · atlas 2048² con color, normal, rugosidad, metal y emisión · "
             "1 unidad = 1 stud",
             "Piezas: " + ", ".join(f"{k} {v}" for k, v in tris.items())]
    K.hoja(4, rutas, os.path.join(salida, f"{nombre}_turnaround.png"), "Casa del ingeniero — giro (8 vistas)",
           notas)

    rd = []
    for n, pos, mira, lente in DETALLES:
        r = os.path.join(tmp, f"det_{len(rd):02d}.png")
        if n == "Malla":
            a, e = math.radians(35), math.radians(22)
            d = V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
            _camara(centro + d * dist, centro, 40)
            scn.view_layers[0].material_override = _material_malla()
            suelo = bpy.data.objects.get("suelo_estudio")
            suelo.hide_render = True
            _render(r, tam, max(8, muestras // 4))
            scn.view_layers[0].material_override = None
            suelo.hide_render = False
        else:
            _camara(pos, mira, lente)
            _render(r, tam, muestras)
        rd.append((n, r))
        print("[render]", n)
    # los cuatro mapas del atlas en una casilla más
    mapas = [Image.open(os.path.join(salida, f"{nombre}_{m}.png")).convert("RGB").resize((tam[1] // 2, tam[1] // 2))
             for m in ("color", "normal", "roughness", "metalness")]
    casilla = Image.new("RGB", tam, (16, 18, 24))
    x0 = (tam[0] - tam[1]) // 2
    for i, m in enumerate(mapas):
        casilla.paste(m, (x0 + (i % 2) * (tam[1] // 2), (i // 2) * (tam[1] // 2)))
    rm = os.path.join(tmp, "det_mapas.png")
    casilla.save(rm)
    rd.append(("Atlas: color · normal · rugosidad · metal", rm))
    K.hoja(4, rd, os.path.join(salida, f"{nombre}_detalles.png"), "Casa del ingeniero — detalles", notas[:1])
