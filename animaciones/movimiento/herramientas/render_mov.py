"""
Render de las animaciones de movimiento: hoja de contactos (frente, lateral y 3/4) y GIF en bucle.

El suelo es una cuadrícula que CORRE hacia atrás a la velocidad de la animación, como una cinta: si un pie apoyado
se mueve respecto a las casillas, está patinando. Las casillas miden lo justo para que el GIF también cierre el bucle
(el suelo recorre un número entero de pares de casillas en un ciclo).
"""

import math
import os

import bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont

import rig_r6 as r6

E = r6.ESTUDIO
ANCHO, ALTO = 340, 420

VISTAS = {
    "Frente": Vector((0.0, -5.6, 1.0)),
    "Lateral": Vector((-5.8, 0.0, 1.0)),  # desde su derecha
    "3/4": Vector((-4.1, -4.1, 1.25)),
}
PUNTO_MIRADO = Vector((0.0, 0.0, 0.74))


def _material(nombre, color, rugosidad=0.7):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rugosidad
    return mat


def preparar_escena(casilla_studs, muestras=16):
    """Devuelve (cámara, nodo de mapeo del suelo)."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = muestras
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = ANCHO, ALTO
    scn.render.film_transparent = False

    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    suelo = bpy.context.active_object
    suelo.name = "Suelo_render"
    mat = bpy.data.materials.new("suelo")
    mat.use_nodes = True
    nt = mat.node_tree
    coords = nt.nodes.new("ShaderNodeTexCoord")
    mapeo = nt.nodes.new("ShaderNodeMapping")
    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Color1"].default_value = (0.66, 0.68, 0.72, 1)
    chk.inputs["Color2"].default_value = (0.47, 0.49, 0.54, 1)
    chk.inputs["Scale"].default_value = 1.0 / (casilla_studs * E)  # casilla = 1/escala (en metros)
    nt.links.new(coords.outputs["Object"], mapeo.inputs["Vector"])
    nt.links.new(mapeo.outputs["Vector"], chk.inputs["Vector"])
    nt.links.new(chk.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.8
    mapeo.inputs["Location"].default_value[2] = 0.5  # evita el borde de la casilla en z = 0
    suelo.data.materials.append(mat)

    scn.world = bpy.data.worlds.new("mundo")
    scn.world.use_nodes = True
    fondo = scn.world.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.80, 0.86, 0.97, 1)
    fondo.inputs["Strength"].default_value = 0.85
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy = 3.6
    sol.angle = math.radians(10)
    objsol = bpy.data.objects.new("sol", sol)
    objsol.rotation_euler = (math.radians(42), 0, math.radians(-30))
    scn.collection.objects.link(objsol)

    cam = bpy.data.cameras.new("cam")
    cam.lens = 92
    objcam = bpy.data.objects.new("cam", cam)
    scn.collection.objects.link(objcam)
    scn.camera = objcam
    mira = bpy.data.objects.new("mira", None)
    scn.collection.objects.link(mira)
    mira.location = PUNTO_MIRADO
    c = objcam.constraints.new("TRACK_TO")
    c.target = mira
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return objcam, mapeo


def casilla_para(distancia_ciclo):
    """Tamaño de casilla (studs) para que el suelo recorra un número entero de pares de casillas por ciclo."""
    if distancia_ciclo <= 1e-6:
        return 1.0
    pares = max(1, round(distancia_ciclo / 2.0))
    return distancia_ciclo / (2 * pares)


def renderizar(fotogramas, directorio, velocidad, fps, distancia_ciclo, vistas=None, muestras=16):
    """Renderiza los fotogramas (números, pueden repetirse entre llamadas) en cada vista. Devuelve {(vista, f): ruta}."""
    os.makedirs(directorio, exist_ok=True)
    cam, mapeo = preparar_escena(casilla_para(distancia_ciclo), muestras)
    scn = bpy.context.scene
    rutas = {}
    for nombre_vista in vistas or VISTAS:
        cam.location = VISTAS[nombre_vista]
        for f in fotogramas:
            scn.frame_set(f)
            # el suelo corre hacia atrás (+Y) como el pie apoyado
            mapeo.inputs["Location"].default_value[1] = -velocidad * (f / fps) * E
            ruta = os.path.join(directorio, f"{nombre_vista.replace('/', '-')}_{f:03d}.png")
            scn.render.filepath = ruta
            bpy.ops.render.render(write_still=True)
            rutas[(nombre_vista, f)] = ruta
    return rutas


def _fuente(tam):
    for ruta in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ):
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default(tam)


def hoja(rutas, fotogramas_clave, salida, titulo=""):
    cab_izq, cab_arriba = 90, 54 + (30 if titulo else 0)
    vistas = list(VISTAS)
    img = Image.new("RGB", (cab_izq + ANCHO * len(fotogramas_clave), cab_arriba + ALTO * len(vistas)), (24, 26, 32))
    d = ImageDraw.Draw(img)
    f_tit, f_peq = _fuente(17), _fuente(13)
    if titulo:
        d.text((10, 8), titulo, fill=(255, 255, 255), font=_fuente(20))
    y0 = cab_arriba - 54
    for i, (f, nombre) in enumerate(fotogramas_clave):
        x = cab_izq + i * ANCHO
        d.text((x + 8, y0 + 6), f"f{f}", fill=(255, 210, 90), font=f_tit)
        d.text((x + 8, y0 + 30), nombre, fill=(220, 220, 230), font=f_peq)
        for j, v in enumerate(vistas):
            img.paste(Image.open(rutas[(v, f)]).convert("RGB"), (x, cab_arriba + j * ALTO))
    for j, v in enumerate(vistas):
        d.text((10, cab_arriba + j * ALTO + ALTO // 2 - 10), v, fill=(255, 255, 255), font=f_tit)
    img.save(salida)
    return salida


def gif(rutas, fotogramas, salida, fps, vistas=None, escala=1.0, rotulo=""):
    """GIF en bucle con las vistas una al lado de otra. `fotogramas` NO incluye el último (que es igual al primero)."""
    vistas = vistas or list(VISTAS)
    fuente = _fuente(14)
    cuadros = []
    for f in fotogramas:
        img = Image.new("RGB", (ANCHO * len(vistas), ALTO), (24, 26, 32))
        for j, v in enumerate(vistas):
            img.paste(Image.open(rutas[(v, f)]).convert("RGB"), (j * ANCHO, 0))
        if rotulo:
            ImageDraw.Draw(img).text((8, 6), rotulo, fill=(20, 22, 30), font=fuente)
        if escala != 1.0:
            img = img.resize((int(img.width * escala), int(img.height * escala)), Image.LANCZOS)
        cuadros.append(img.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    paso = fotogramas[1] - fotogramas[0] if len(fotogramas) > 1 else 1
    cuadros[0].save(
        salida, save_all=True, append_images=cuadros[1:], duration=round(1000 * paso / fps), loop=0, optimize=True
    )
    return salida
