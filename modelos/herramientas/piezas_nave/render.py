"""
Turnaround de cada pieza: 6 vistas (frente, detrás, izquierda, derecha, arriba y 3/4) + una vista con los puntos
de acople marcados con flechas de colores, y una ficha con los datos. Se monta en una hoja JPG.
"""

import math
import os

import bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont

from . import datos, texturas

V = Vector

# (nombre, dirección de la cámara desde el centro, ortográfica)
VISTAS = [
    ("Frente", (0, -1, 0.0), True),
    ("Detrás", (0, 1, 0.0), True),
    ("Izquierda", (1, 0, 0.0), True),
    ("Derecha", (-1, 0, 0.0), True),
    ("Arriba", (0, 0, 1), True),
    ("3/4", (0.62, -0.68, 0.42), False),
    ("Acoples", (-0.6, 0.55, 0.62), False),
]


def _fuente(tam, negrita=True):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrita else \
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(ruta):
        return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def preparar_estudio():
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.render.threads_mode = "AUTO"
    scn.world.use_nodes = True
    fondo = scn.world.node_tree.nodes["Background"]
    # el fondo se ve oscuro, pero los reflejos del metal ven un cielo gris claro (como el cielo de Roblox)
    nt = scn.world.node_tree
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    camino = nt.nodes.new("ShaderNodeLightPath")
    cielo = nt.nodes.new("ShaderNodeBackground")
    cielo.inputs["Color"].default_value = (0.42, 0.46, 0.55, 1)
    cielo.inputs["Strength"].default_value = 1.0
    fondo.inputs["Color"].default_value = (0.05, 0.055, 0.075, 1)
    fondo.inputs["Strength"].default_value = 1.0
    salida = nt.nodes["World Output"]
    nt.links.new(camino.outputs["Is Camera Ray"], mezcla.inputs["Fac"])
    nt.links.new(cielo.outputs[0], mezcla.inputs[1])
    nt.links.new(fondo.outputs[0], mezcla.inputs[2])
    nt.links.new(mezcla.outputs[0], salida.inputs["Surface"])

    mira = bpy.data.objects.new("Mira_estudio", None)
    scn.collection.objects.link(mira)

    def luz(nombre, energia, pos, color, tam):
        d = bpy.data.lights.new(nombre, "AREA")
        d.energy = energia
        d.color = color
        d.size = tam
        o = bpy.data.objects.new(nombre, d)
        o["pos_base"] = pos
        o["energia_base"] = energia
        scn.collection.objects.link(o)
        c = o.constraints.new("TRACK_TO")
        c.target = mira
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        o["luz_estudio"] = True
        return o

    # posiciones para una pieza de radio 1: se escalan con el tamaño
    luz("clave", 260, (-2.2, -3.0, 3.4), (1.0, 0.95, 0.88), 2.5)
    luz("relleno", 90, (3.2, -1.6, 1.2), (0.75, 0.85, 1.0), 3.5)
    luz("contra", 220, (1.4, 3.4, 2.6), (0.8, 0.9, 1.0), 2.0)
    luz("abajo", 40, (0.0, -0.6, -3.0), (0.85, 0.85, 0.95), 4.0)
    return mira


def _marcadores(acoples_mundo, escala):
    """Flechas de colores en cada acople (en la dirección de su normal)."""
    objs = []
    for a in acoples_mundo:
        color = datos.CONECTORES[a["tipo"]]["color"]
        mat = texturas.material_plano(f"marca_{a['nombre']}", "neon", color)
        largo = escala * 0.16
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=largo * 0.22, radius2=0, depth=largo * 0.45)
        punta = bpy.context.active_object
        bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=largo * 0.07, depth=largo * 0.6)
        palo = bpy.context.active_object
        n = V(a["normal"]).normalized()
        q = n.to_track_quat("Z", "Y")
        for o, d in ((palo, largo * 0.3), (punta, largo * 0.6 + largo * 0.22)):
            o.rotation_mode = "QUATERNION"
            o.rotation_quaternion = q
            o.location = V(a["pos"]) + n * d
            o.data.materials.append(mat)
            o["marcador"] = True
            objs.append(o)
        if a["direccion"] == "entrada":
            # las entradas llevan un aro, para distinguirlas de las salidas
            bpy.ops.mesh.primitive_torus_add(major_radius=largo * 0.2, minor_radius=largo * 0.04)
            aro = bpy.context.active_object
            aro.rotation_mode = "QUATERNION"
            aro.rotation_quaternion = q
            aro.location = V(a["pos"]) + n * largo * 0.05
            aro.data.materials.append(mat)
            aro["marcador"] = True
            objs.append(aro)
    return objs


def renderizar(objetos, acoples_mundo, carpeta_tmp, prefijo, tam=420, muestras=40):
    scn = bpy.context.scene
    mira = bpy.data.objects.get("Mira_estudio") or preparar_estudio()
    os.makedirs(carpeta_tmp, exist_ok=True)
    scn.cycles.samples = muestras
    scn.render.resolution_x = scn.render.resolution_y = tam
    scn.render.image_settings.file_format = "PNG"

    for o in scn.objects:
        if o.type == "MESH" and not o.get("marcador"):
            o.hide_render = o not in objetos
    mn = V((1e9,) * 3)
    mx = V((-1e9,) * 3)
    for o in objetos:
        for v in o.data.vertices:
            mn = V(map(min, mn, v.co))
            mx = V(map(max, mx, v.co))
    c = (mn + mx) / 2
    ext = mx - mn
    radio = ext.length / 2
    mira.location = c
    for o in scn.objects:
        if o.get("luz_estudio"):
            o.location = c + V(o["pos_base"]) * radio * 1.3
            o.data.energy = o["energia_base"] * (radio * 1.3) ** 2
            o.data.size = o.data.size if o.get("tam_fijado") else o.data.size * radio
            o["tam_fijado"] = True

    marcas = _marcadores(acoples_mundo, max(ext) if max(ext) < 14 else 14 + (max(ext) - 14) * 0.4)

    cam_d = bpy.data.cameras.new("cam")
    cam_d.clip_end = 5000
    cam = bpy.data.objects.new("cam", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    rutas = []
    for nombre, d, orto in VISTAS:
        for m in marcas:
            m.hide_render = nombre != "Acoples"
        d = V(d).normalized()
        if orto:
            cam_d.type = "ORTHO"
            # tamaño visible en el plano de la vista
            ejes = [k for k in range(3) if abs(d[k]) < 0.5]
            cam_d.ortho_scale = max(ext[k] for k in ejes) * 1.18 + 0.2
            dist = radio * 4 + 5
        else:
            cam_d.type = "PERSP"
            cam_d.lens = 50
            fov = 2 * math.atan(18 / 50)
            dist = radio * 1.12 / math.sin(fov / 2)
        cam.location = c + d * dist
        up = "Y" if abs(d.z) < 0.9 else "Y"
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", up).to_euler()
        if abs(d.z) > 0.9:
            # vista de arriba: el morro hacia arriba de la imagen
            cam.rotation_euler = (0, 0, math.pi)
        ruta = os.path.join(carpeta_tmp, f"{prefijo}_{nombre.replace('/', '-')}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        rutas.append((nombre, ruta))
    bpy.data.objects.remove(cam)
    for m in marcas:
        bpy.data.objects.remove(m)
    return rutas


def hoja(rutas, salida, ficha):
    """Monta las vistas (4 × 2) y la ficha de datos a la derecha."""
    tam = Image.open(rutas[0][1]).size[0]
    ancho_ficha = 560
    cab = 64
    W = 4 * tam + ancho_ficha
    H = cab + 2 * tam
    img = Image.new("RGB", (W, H), (14, 16, 22))
    d = ImageDraw.Draw(img)
    d.text((16, 12), ficha["titulo_hoja"], fill=(255, 214, 102), font=_fuente(28))
    d.text((16, 44), ficha["subtitulo"], fill=(200, 205, 215), font=_fuente(14, False))
    for i, (nombre, ruta) in enumerate(rutas):
        x = (i % 4) * tam
        y = cab + (i // 4) * tam
        img.paste(Image.open(ruta).convert("RGB"), (x, y))
        d.rectangle((x, y, x + tam - 1, y + tam - 1), outline=(40, 44, 56))
        d.text((x + 10, y + 8), nombre, fill=(255, 255, 255), font=_fuente(16))
    # celda 8: leyenda de tipos de conector
    x0, y0 = 3 * tam, cab + tam
    if len(rutas) < 8:
        d.text((x0 + 14, y0 + 10), "Conectores", fill=(255, 255, 255), font=_fuente(16))
        yy = y0 + 38
        for tipo, spec in datos.CONECTORES.items():
            col = tuple(int(spec["color"][k:k + 2], 16) for k in (1, 3, 5))
            d.rectangle((x0 + 14, yy + 3, x0 + 28, yy + 15), fill=col)
            forma = "□" if spec["forma"] == "cuadrado" else "○"
            t = f"{tipo}  {forma}{spec['tam']:.1f}" if spec["tam"] else tipo
            d.text((x0 + 36, yy), t, fill=(220, 224, 232), font=_fuente(13, False))
            yy += 22
        d.text((x0 + 14, yy + 8), "flecha = salida · flecha con aro = entrada", fill=(160, 166, 180),
               font=_fuente(12, False))
    # ficha
    fx = 4 * tam + 18
    fy = cab + 6
    for linea, estilo in ficha["lineas"]:
        if fy > H - 18:
            d.text((fx, fy), "…", fill=(200, 200, 200), font=_fuente(13, False))
            break
        if estilo == "titulo":
            d.text((fx, fy), linea, fill=(255, 255, 255), font=_fuente(16))
            fy += 24
        elif estilo == "acople":
            d.text((fx, fy), linea, fill=(190, 230, 255), font=_fuente(12, False))
            fy += 17
        else:
            d.text((fx, fy), linea, fill=(215, 219, 228), font=_fuente(13, False))
            fy += 19
    img.save(salida, quality=88, optimize=True)
    return salida
