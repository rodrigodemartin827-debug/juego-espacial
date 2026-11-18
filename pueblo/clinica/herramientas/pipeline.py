"""
Genera la clínica completa:

    python pueblo/clinica/herramientas/pipeline.py --salida pueblo/clinica [--previa] [--tam 2048]

  1. Rótulos (Pillow) y materiales procedurales.
  2. Geometría (clinica.py) -> un objeto por pieza.
  3. UV de todas las piezas en un único atlas (las caras con texto reciben más resolución).
  4. Horneado del atlas de 2048: color (con oclusión y alfa de los cristales), normal, rugosidad, metal, emisión.
  5. Pivotes (puertas), GIRO_IMPORTACION (180° alrededor del eje vertical, el Y de Roblox) y FBX.
  6. Vuelta de 8 vistas con el atlas horneado y clinica.json.

--previa solo construye y renderiza unas vistas con los materiales procedurales (para revisar la geometría).
"""

import argparse
import json
import math
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import clinica  # noqa: E402
import geo  # noqa: E402
import materiales  # noqa: E402
import rotulos  # noqa: E402

PRESUPUESTO = 12000
GIRO_IMPORTACION = math.pi  # 180° alrededor del eje vertical (Z en Blender = Y en Roblox)

# Qué es cada pieza en Roblox
ROLES = {
    "Edificio": "Paredes, zócalo, techo, ventanas, marquesina y mecanismo de la puerta",
    "Interior": "Suelo, tabiques, mostrador y bancada de la sala de espera",
    "Techo_Equipos": "Climatizador, panel solar y antena",
    "Detalles": "Cruz (carcasa), placa, tablón, gel, botiquín, medidor y tubo con filtro HEPA",
    "Rampa": "Rellano, rampa con barandillas y escalón trasero",
    "Mobiliario": "Banco, papelera, señal de parking y farola",
    "Cristales": "Ventanas, tablón y tapa del mecanismo (SurfaceAppearance con AlphaMode = Transparency)",
    "Puerta_Izq": "Hoja corredera izquierda (anima)",
    "Puerta_Der": "Hoja corredera derecha (anima)",
    "Puerta_Izq_Cristal": "Cristal de la hoja izquierda (soldar a Puerta_Izq)",
    "Puerta_Der_Cristal": "Cristal de la hoja derecha (soldar a Puerta_Der)",
    "Puerta_Trasera": "Puerta de suministros (gira en las bisagras)",
}
NEON = {
    "Cruz_neon": ("#FFFFFF", "Cruz médica luminosa"),
    "Marquesina_neon": ("#FFE1B5", "Dos luces empotradas de la marquesina (blanco cálido)"),
    "Farola_neon": ("#FFFFFF", "Difusor de la farola (blanco)"),
    "Medidor_neon": ("#5CFF9A", "Pantalla del medidor (si se quiere ver la cifra: SurfaceAppearance en vez de Neon)"),
    "Sensor_neon": ("#FF2E2E", "LED del sensor de movimiento"),
    "Interior_neon": ("#FFFFFF", "Paneles de luz del techo interior"),
    "Antena_neon": ("#FF2E2E", "Baliza de la antena"),
}


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0
    scn.world = bpy.data.worlds.new("mundo")
    return scn


def construir(carpeta_tmp):
    rot = rotulos.generar(os.path.join(carpeta_tmp, "rotulos"))
    mats, socks = materiales.construir(rot)
    grupos, datos = clinica.construir()
    objetos = {}
    for nombre in clinica.GRUPOS:
        g = grupos[nombre]
        if not g.bm.faces:
            continue
        objetos[nombre] = geo.a_objeto(g, mats)
    return objetos, datos, mats, socks


def triangulos(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ----------------------------------------------------------------------------------------------------------------
# Render (previa y vuelta)
# ----------------------------------------------------------------------------------------------------------------


def preparar_luz(scn, noche=False):
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.world.use_nodes = True
    nt = scn.world.node_tree
    nt.nodes.clear()
    cielo = nt.nodes.new("ShaderNodeTexSky")
    try:
        cielo.sky_type = "NISHITA"
        cielo.sun_elevation = math.radians(38)
        cielo.sun_rotation = math.radians(215)
        cielo.sun_intensity = 0.35
    except Exception:  # noqa: BLE001
        pass
    fondo = nt.nodes.new("ShaderNodeBackground")
    fondo.inputs["Strength"].default_value = 0.25
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(cielo.outputs[0], fondo.inputs[0])
    nt.links.new(fondo.outputs[0], out.inputs[0])
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy = 4.2
    sol.angle = math.radians(2.5)
    sol.color = (1.0, 0.96, 0.9)
    o = bpy.data.objects.new("sol", sol)
    o.rotation_euler = (math.radians(52), 0, math.radians(215))
    scn.collection.objects.link(o)
    o["estudio"] = True
    # suelo: tierra apisonada con algo de hierba
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, -2, -0.002))
    s = bpy.context.active_object
    s.name = "Suelo_estudio"
    s["estudio"] = True
    m = bpy.data.materials.new("suelo_estudio")
    m.use_nodes = True
    nb = materiales.N(m)
    b = m.node_tree.nodes["Principled BSDF"]
    r = nb.ruido(0.6, 6, 0.6)
    c = nb.mix(nb.rango(r, 0.45, 0.6), "#7C6E58", "#5E7046")
    nb.link(c, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    s.data.materials.append(m)


def renderizar(objetos, carpeta, vistas, tam=900, muestras=64, centro=None, dist=None, lente=40, prefijo=""):
    scn = bpy.context.scene
    scn.cycles.samples = muestras
    scn.render.resolution_x = tam
    scn.render.resolution_y = int(tam * 0.78)
    os.makedirs(carpeta, exist_ok=True)
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = lente
    cam_d.clip_end = 1000
    cam = bpy.data.objects.new("cam", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    c = Vector(centro or (0.3, -2.2, 3.6))
    rutas = []
    for nombre, az, el, d in vistas:
        a, e = math.radians(az), math.radians(el)
        direc = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = c + direc * (d or dist or 28)
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        ruta = os.path.join(carpeta, f"{prefijo}{nombre}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        rutas.append((nombre, ruta))
    bpy.data.objects.remove(cam)
    return rutas


# (nombre, azimut, elevación, distancia). Azimut positivo = la cámara a la derecha del edificio (+X).
VUELTA = [
    ("1 Frente", 0, 12, None), ("2 Tres cuartos frontal derecha", 45, 18, None), ("3 Lateral derecho", 90, 12, None),
    ("4 Tres cuartos trasera derecha", 135, 20, None), ("5 Detras", 180, 12, None),
    ("6 Tres cuartos trasera izquierda", -135, 20, None), ("7 Lateral izquierdo", -90, 12, None),
    ("8 Tres cuartos frontal izquierda", -45, 18, None),
]

# Primeros planos: (nombre, centro, azimut, elevación, distancia)
DETALLES = [
    ("Puerta y mecanismo", (-1.2, -5.2, 3.4), 12, 8, 9.5),
    ("Placa, tablón y sensor", (-2.6, -5.1, 4.3), -25, 6, 5.0),
    ("Cruz, ventana y banco", (3.4, -5.6, 3.6), 22, 10, 7.5),
    ("Rampa y barandillas", (-1.2, -8.2, 1.6), -40, 22, 9.0),
    ("Botiquín y ventana sala de espera", (-5.2, -1.6, 3.2), -80, 6, 7.0),
    ("Tubo HEPA, medidor, consulta", (5.2, 0.0, 4.0), 80, 10, 8.5),
    ("Puerta trasera y teclado", (1.6, 5.2, 3.2), 165, 6, 7.0),
    ("Techo: clima, solar, antena", (0.0, 0.5, 7.6), 160, 38, 12.0),
]
def renderizar_detalles(carpeta, girado=False, tam=720, muestras=64):
    scn = bpy.context.scene
    rutas = []
    for nombre, c, az, el, d in DETALLES:
        c = girar(c) if girado else Vector(c)
        az2 = (az + 180) if girado else az
        rutas += renderizar(None, carpeta, [(nombre, az2, el, d)], tam=tam, muestras=muestras, centro=c, lente=35)
    return rutas


def hoja_contactos(rutas, salida, titulo, notas, columnas=4):
    ims = [Image.open(r).convert("RGB") for _, r in rutas]
    w, h = ims[0].size
    filas = math.ceil(len(ims) / columnas)
    cab = 70 + 22 * len(notas)
    hoja = Image.new("RGB", (w * columnas, cab + h * filas), (18, 20, 26))
    d = ImageDraw.Draw(hoja)
    f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    f3 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
    d.text((18, 14), titulo, fill=(255, 214, 102), font=f1)
    for i, n in enumerate(notas):
        d.text((20, 56 + i * 22), n, fill=(210, 214, 224), font=f2)
    for i, ((nombre, _), im) in enumerate(zip(rutas, ims)):
        x, y = (i % columnas) * w, cab + (i // columnas) * h
        hoja.paste(im, (x, y))
        d.rectangle((x, y, x + w - 1, y + h - 1), outline=(44, 48, 60))
        d.text((x + 12, y + 10), nombre, fill=(255, 255, 255), font=f3, stroke_width=2, stroke_fill=(0, 0, 0))
    hoja.save(salida)
    return salida


# ----------------------------------------------------------------------------------------------------------------
# UV del atlas
# ----------------------------------------------------------------------------------------------------------------

MATS_TEXTO = {"placa", "rot_solo_personal", "rot_parking_p", "rot_parking_sub", "rot_horario", "rot_medidor",
              "rot_gel", "rot_residuos", "rot_cartel", "teclado", "botiquin_texto"}


def desplegar_atlas(objs, margen=0.0025):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")

    # Las caras con texto ganan resolución; las que nunca se ven (apoyadas en el suelo) casi no ocupan.
    for o in objs:
        me = o.data
        uv = me.uv_layers["UVMap"].data
        nombres = [m.name for m in me.materials]
        for p in me.polygons:
            esc = 1.0
            nm = nombres[p.material_index] if p.material_index < len(nombres) else ""
            if nm in MATS_TEXTO:
                esc = 4.0 if nm in ("teclado", "rot_gel", "rot_medidor", "botiquin_texto", "placa") else 3.0
            elif nm.startswith("neon"):
                esc = 0.35
            elif p.normal.z < -0.95 and (o.matrix_world @ p.center).z < 0.05:
                esc = 0.05
            elif o.name == "Interior":
                esc = 0.6
            if esc != 1.0:
                ids = list(p.loop_indices)
                cen = sum((uv[i].uv for i in ids), Vector((0, 0))) / len(ids)
                for i in ids:
                    uv[i].uv = cen + (uv[i].uv - cen) * esc
    # Las islas de una sola cara escaladas así siguen siendo islas: el empaquetado las coloca de nuevo.
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, scale=True, margin_method="FRACTION",
                            margin=margen, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


# ----------------------------------------------------------------------------------------------------------------
# Horneado
# ----------------------------------------------------------------------------------------------------------------


def _imagen(nombre, tam, color=True, alfa=False):
    img = bpy.data.images.new(nombre, tam, tam, alpha=alfa, float_buffer=not color)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return img


def hornear(objs, mats, socks, tam, carpeta_tex, muestras_ao=48):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.render.bake.margin = 6
    scn.render.bake.margin_type = "EXTEND"
    usados = {m for o in objs for m in o.data.materials}

    def destino(img):
        for m in usados:
            nt = m.node_tree
            n = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
            n.name = "destino"
            n.image = img
            nt.nodes.active = n

    def seleccionar():
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]

    def via_emision(clave):
        """Conecta el socket `clave` de cada material a una emisión pura y hornea EMIT."""
        guard = {}
        for m in usados:
            s = socks[m.name]
            nt = m.node_tree
            em = nt.nodes.new("ShaderNodeEmission")
            em.inputs["Strength"].default_value = 1.0
            nt.links.new(s[clave], em.inputs["Color"])
            nt.links.new(em.outputs[0], s["salida"].inputs[0])
            guard[m] = em
        seleccionar()
        scn.cycles.samples = 4
        bpy.ops.object.bake(type="EMIT", margin=6)
        for m, em in guard.items():
            nt = m.node_tree
            nt.nodes.remove(em)
            nt.links.new(socks[m.name]["bsdf"], socks[m.name]["salida"].inputs[0])

    resultados = {}
    t0 = time.time()
    for clave, nombre, color in (("color", "color", True), ("metal", "metalness", False),
                                 ("alfa", "alfa", False), ("emis", "emision", True)):
        img = _imagen(f"hornear_{nombre}", tam, color=color)
        destino(img)
        via_emision(clave)
        resultados[nombre] = img
        print(f"[horneado] {nombre}: {time.time() - t0:.0f} s", flush=True)

    img = _imagen("hornear_roughness", tam, color=False)
    destino(img)
    seleccionar()
    scn.cycles.samples = 4
    bpy.ops.object.bake(type="ROUGHNESS", margin=6)
    resultados["roughness"] = img
    print(f"[horneado] roughness: {time.time() - t0:.0f} s", flush=True)

    img = _imagen("hornear_normal", tam, color=False)
    destino(img)
    seleccionar()
    scn.cycles.samples = 4
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", margin=6)
    resultados["normal"] = img
    print(f"[horneado] normal: {time.time() - t0:.0f} s", flush=True)

    # Oclusión ambiental, con el suelo presente (ensucia el contacto con el terreno).
    bpy.ops.mesh.primitive_plane_add(size=60, location=(0, -2, 0))
    suelo_ao = bpy.context.active_object
    suelo_ao.data.materials.append(bpy.data.materials.new("suelo_ao"))
    img = _imagen("hornear_ao", tam, color=False)
    destino(img)
    seleccionar()
    scn.world.light_settings.distance = 1.0
    scn.cycles.samples = muestras_ao
    bpy.ops.object.bake(type="AO", margin=6)
    resultados["ao"] = img
    bpy.data.objects.remove(suelo_ao)
    print(f"[horneado] oclusión: {time.time() - t0:.0f} s", flush=True)

    # --- Componer y guardar --------------------------------------------------------------------------------------
    def arr(img):
        return np.array(img.pixels[:], dtype=np.float32).reshape(tam, tam, 4)

    def guardar(nombre, datos, modo):
        # Blender guarda las filas de abajo arriba
        datos = np.flipud(np.clip(datos, 0, 1))
        im = Image.fromarray((datos * 255 + 0.5).astype(np.uint8), modo)
        ruta = os.path.join(carpeta_tex, f"clinica_{nombre}.png")
        im.save(ruta, optimize=True)
        return ruta

    def a_srgb(x):
        return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(np.maximum(x, 0), 1 / 2.4) - 0.055)

    rutas = {}
    col = arr(resultados["color"])[..., :3]  # lineal (imagen sRGB en memoria = lineal en pixels)
    ao = arr(resultados["ao"])[..., :1]
    factor = 1.0 - 0.7 * (1.0 - np.clip(ao, 0, 1)) ** 1.4
    col = col * factor
    alfa = arr(resultados["alfa"])[..., :1]
    rgba = np.concatenate([a_srgb(col), alfa], axis=2)
    rutas["color"] = guardar("color", rgba, "RGBA")
    rutas["normal"] = guardar("normal", arr(resultados["normal"])[..., :3], "RGB")
    rutas["roughness"] = guardar("roughness", arr(resultados["roughness"])[..., 0], "L")
    rutas["metalness"] = guardar("metalness", arr(resultados["metalness"])[..., 0], "L")
    rutas["emision"] = guardar("emision", a_srgb(arr(resultados["emision"])[..., :3]), "RGB")
    return rutas


def material_atlas(rutas):
    """Material final: las cinco texturas del atlas (lo que se exporta y lo que se ve en la vuelta)."""
    m = bpy.data.materials.new("clinica_atlas")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]

    def tex(clave, color):
        img = bpy.data.images.load(rutas[clave])
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = img
        return n

    c = tex("color", True)
    nt.links.new(c.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(c.outputs["Alpha"], b.inputs["Alpha"])
    nt.links.new(tex("roughness", False).outputs["Color"], b.inputs["Roughness"])
    nt.links.new(tex("metalness", False).outputs["Color"], b.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal", False).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    e = tex("emision", True)
    nt.links.new(e.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 4.0
    try:
        m.surface_render_method = "BLENDED"
    except AttributeError:
        pass
    return m


# ----------------------------------------------------------------------------------------------------------------
# Principal
# ----------------------------------------------------------------------------------------------------------------


def roblox(v):
    """Blender (ya con el GIRO aplicado) -> Roblox: x, z, -y."""
    return [round(v.x, 3), round(v.z, 3), round(-v.y, 3)]


def girar(v):
    return Matrix.Rotation(GIRO_IMPORTACION, 3, "Z") @ Vector(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=os.path.join(AQUI, ".."))
    ap.add_argument("--tmp", default=os.path.join(AQUI, "..", "_tmp"))
    ap.add_argument("--previa", action="store_true")
    ap.add_argument("--tam", type=int, default=2048)
    ap.add_argument("--muestras", type=int, default=96)
    ap.add_argument("--vistas", default="")
    ap.add_argument("--detalles", action="store_true")
    args, _ = ap.parse_known_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    salida = os.path.abspath(args.salida)
    tmp = os.path.abspath(args.tmp)
    os.makedirs(tmp, exist_ok=True)

    escena_vacia()
    objetos, datos, mats, socks = construir(tmp)
    total = 0
    for n, o in objetos.items():
        t = triangulos(o)
        total += t
        print(f"  {n:22s} {t:6d}")
    print(f"  {'TOTAL':22s} {total:6d}  (presupuesto {PRESUPUESTO})", flush=True)

    if args.previa:
        preparar_luz(bpy.context.scene)
        vistas = VUELTA
        if args.vistas:
            vistas = [v for v in VUELTA if v[0][0] in args.vistas]
        rutas = renderizar(list(objetos.values()), os.path.join(tmp, "previa"), vistas, tam=720,
                           muestras=args.muestras)
        if rutas:
            hoja_contactos(rutas, os.path.join(tmp, "previa.png"), "Clínica — previa (materiales procedurales)",
                           [f"{total} triángulos"])
        if args.detalles:
            rd = renderizar_detalles(os.path.join(tmp, "previa_det"), muestras=args.muestras)
            hoja_contactos(rd, os.path.join(tmp, "previa_det.png"), "Clínica — detalles (previa)", [])
        return

    # --- Atlas -------------------------------------------------------------------------------------------------
    objs = list(objetos.values())
    t0 = time.time()
    desplegar_atlas(objs)
    print(f"[uv] {time.time() - t0:.0f} s", flush=True)
    carpeta_tex = salida
    os.makedirs(carpeta_tex, exist_ok=True)
    rutas_tex = hornear(objs, mats, socks, args.tam, carpeta_tex)
    atlas = material_atlas(rutas_tex)
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(atlas)
        for p in o.data.polygons:
            p.material_index = 0
        o.data.uv_layers.remove(o.data.uv_layers["deco"])

    # --- Pivotes, giro y exportación ---------------------------------------------------------------------------
    pivotes = {n: Vector((0, 0, 0)) for n in objetos}
    for n in ("Puerta_Izq", "Puerta_Der"):
        pivotes[n] = datos[n]["pivote"]
        pivotes[n + "_Cristal"] = datos[n]["pivote"]
    pivotes["Puerta_Trasera"] = datos["Puerta_Trasera"]["pivote"]
    giro = Matrix.Rotation(GIRO_IMPORTACION, 4, "Z")
    for n, o in objetos.items():
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        # malla relativa al pivote, ya girada; el objeto queda en el pivote girado
        bmesh.ops.transform(bm, matrix=giro @ Matrix.Translation(-pivotes[n]), verts=bm.verts)
        bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
        bm.to_mesh(me)
        bm.free()
        o.location = giro @ pivotes[n]

    ruta_fbx = os.path.join(salida, "clinica.fbx")
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta_fbx, use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL", global_scale=1.0,
        axis_forward="-Z", axis_up="Y", bake_space_transform=False,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True,
        bake_anim=False, embed_textures=True, path_mode="COPY",
    )
    print("[ok] FBX:", ruta_fbx, flush=True)

    tris = {n: triangulos(o) for n, o in objetos.items()}

    # --- Vuelta con el atlas -----------------------------------------------------------------------------------
    preparar_luz(bpy.context.scene)
    # la cámara mira al modelo ya girado: la vista "Frente" mira la fachada (que ahora está en +Y)
    vistas = [(n, (az + 180) % 360, el, d) for n, az, el, d in VUELTA]
    rutas = renderizar(objs, os.path.join(tmp, "vuelta"), vistas, tam=900, muestras=args.muestras,
                       centro=girar((0.3, -2.2, 3.6)))
    hoja_contactos(rutas, os.path.join(salida, "clinica_turnaround.png"),
                   "Clínica Colonial — vuelta de 8 vistas (atlas horneado 2048)",
                   [f"{sum(tris.values())} triángulos · {len(objs)} piezas · 10,4 × 10 × 7,4 studs (edificio)",
                    "Texturas: color (+AO, alfa en cristales), normal, rugosidad, metal, emisión · el neón se ve "
                    "por emisión"])
    escribir_json(salida, datos, tris, objetos)


def escribir_json(salida, datos, tris, objetos):
    def r(v):
        return roblox(girar(v))

    piezas = {}
    for n, o in objetos.items():
        e = {"triangulos": tris[n]}
        if n in NEON:
            e.update({"material": "Neon", "color": NEON[n][0], "que_es": NEON[n][1]})
        else:
            e.update({"material": "SurfaceAppearance (atlas)", "que_es": ROLES.get(n, "")})
            if "Cristal" in n:
                e["alpha_mode"] = "Transparency"
        e["pivote_roblox"] = roblox(o.location)
        piezas[n] = e

    j = {
        "nombre": "clinica",
        "descripcion": "Clínica Colonial de la Dra. Voss: el único edificio médico del pueblo.",
        "unidades": "1 unidad = 1 stud. FBX exportado con Apply Scalings = FBX All: en el importador de Roblox "
                    "elige la unidad Stud si el tamaño no sale a ~10 studs de ancho.",
        "giro_importacion": "GIRO_IMPORTACION aplicado: 180° alrededor del eje vertical (Y de Roblox) antes de "
                            "exportar. La fachada mira a -Z (el delante de Roblox).",
        "ejes": "Coordenadas en studs, ejes de Roblox, origen en el centro del edificio a ras de suelo.",
        "tamano_studs": {"edificio": [10.4, 7.42, 10.0], "con_equipos_del_techo": [10.4, 11.02, 10.0],
                         "con_rampa_y_entorno": [14.4, 11.02, 16.5]},
        "triangulos": {"total": sum(tris.values()), "presupuesto": PRESUPUESTO, "por_pieza": tris},
        "texturas": {
            "ColorMap": "clinica_color.png (sRGB, oclusión horneada; el alfa solo baja en los cristales)",
            "NormalMap": "clinica_normal.png (tangente, OpenGL +Y)",
            "RoughnessMap": "clinica_roughness.png",
            "MetalnessMap": "clinica_metalness.png",
            "Emision": "clinica_emision.png (máscara de emisión: pantalla del medidor, neones)",
            "tam": 2048,
        },
        "piezas": piezas,
        "puertas_correderas": {
            "como": "Tween del CFrame de cada hoja (y su cristal soldado) a lo largo del eje indicado. Abrir: "
                    "0,6 s Quad Out; cerrar: 0,8 s Quad InOut, a los 3 s sin nadie delante del sensor.",
            "Puerta_Izq": {"pivote": r(datos["Puerta_Izq"]["pivote"]),
                           "desplazamiento_abrir": roblox(girar(datos["Puerta_Izq"]["abrir"]))},
            "Puerta_Der": {"pivote": r(datos["Puerta_Der"]["pivote"]),
                           "desplazamiento_abrir": roblox(girar(datos["Puerta_Der"]["abrir"]))},
            "nota": "Las hojas se esconden dentro de la pared (bolsillos); el carro y las ruedas van con la hoja "
                    "por el raíl visible tras la tapa transparente.",
        },
        "puerta_trasera": {
            "pivote_bisagras": r(datos["Puerta_Trasera"]["pivote"]),
            "eje": "Y (vertical)",
            "abrir": "CFrame.Angles(0, math.rad(95), 0) alrededor del pivote: abre hacia fuera (hacia +Z).",
        },
        "luces": {
            "Cruz": {"pos": r(datos["Cruz"]), "tipo": "PointLight", "color": "#FFFFFF", "brillo": 1.5, "rango": 10},
            "Marquesina": [{"pos": r(p), "tipo": "SpotLight hacia abajo", "color": "#FFE1B5", "brillo": 2,
                            "rango": 12, "angulo": 70} for p in datos["LucesMarquesina"]],
            "Farola": {"pos": r(datos["Farola"]), "tipo": "SpotLight hacia abajo", "color": "#FFFFFF",
                       "brillo": 3, "rango": 22, "angulo": 100},
            "Interior": [{"pos": r(p), "tipo": "SurfaceLight/PointLight", "color": "#F4FBFF", "brillo": 0.8,
                          "rango": 10} for p in datos["LucesInterior"]],
            "Baliza": {"pos": r(datos["Baliza"]), "tipo": "PointLight parpadeante", "color": "#FF2E2E"},
            "Sensor_LED": {"pos": r(datos["Sensor_LED"]), "nota": "verde cuando detecta (abre), rojo en reposo"},
        },
        "anclajes": {"Banco_asientos_centro": r(datos["Banco"]), "Papelera": r(datos["Papelera"])},
        "colision": "Edificio, Interior, Rampa y Mobiliario: CollisionFidelity = PreciseConvexDecomposition. "
                    "Detalles, Techo_Equipos, Cristales y neones: CanCollide = false salvo Cristales de ventanas.",
    }
    with open(os.path.join(salida, "clinica.json"), "w", encoding="utf-8") as f:
        json.dump(j, f, ensure_ascii=False, indent=2)
    print("[ok] json")


if __name__ == "__main__":
    main()
