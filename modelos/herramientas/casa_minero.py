"""
Casa del minero: la casa del pueblo de la colonia que ve el jugador nada más entrar.

Genera, sin pantalla y sin nada hecho a mano:
  * todas las piezas como objetos separados (puerta, contraventanas, tapa del buzón... con su pivote donde giran),
  * un atlas PBR de 2048 x 2048 horneado desde una malla alta con detalle (color, normal, rugosidad,
    metalicidad, emisión),
  * el turnaround de 8 vistas con luz de estudio de 3 puntos (+ una hoja de detalles),
  * el FBX (con GIRO_IMPORTACION: 180° alrededor del eje vertical) reimportado y comprobado,
  * un JSON con triángulos, medidas, piezas y pivotes.

Escala: 1 unidad de Blender = 1 stud. La escena usa scale_length = 0,28 (1 stud = 0,28 m, la conversión del
importador de Roblox) y el FBX se exporta con «Apply Scalings: FBX All», así que llega a Studio con su tamaño.

Uso:
    python modelos/herramientas/casa_minero.py --salida modelos/pueblo/casa_minero [--rapido] [--vista]

  --vista   solo modela y renderiza unas vistas rápidas con los materiales procedurales (para modelar)
  --rapido  atlas de 512 y renders pequeños (para probar todo el proceso en pocos minutos)
"""

import argparse
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from bpy_extras.bmesh_utils import bmesh_linked_uv_islands  # noqa: E402
from bpy_extras.io_utils import axis_conversion  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import casa_materiales as cm  # noqa: E402
import casa_piezas as cp  # noqa: E402

NOMBRE = "casa_minero"
ESTUDIO_M = 0.28                 # metros por stud
GIRO_IMPORTACION = 180.0         # grados alrededor del eje vertical antes de exportar
ATLAS = 2048
COLOR_NEON = "#3DF2FF"
COLOR_NEON_CALIDO = "#FFB45A"   # piezas *_neon_calido (luz cálida de dentro)
COLOR_VIDRIO = "#79B8AE"
# Neones de otros colores: {sufijo del nombre de la pieza: (color, intensidad en el render)}. Se miran antes que
# «_neon_calido» y «_neon». Lo rellena cada casa con cfg["neones"].
NEONES = {}
# Piezas translúcidas con textura (el nombre contiene esta cadena): usan el atlas con el canal alfa del color
# (SurfaceAppearance con AlphaMode = Transparency), p. ej. el cristal con condensación del invernadero.
TRANSLUCIDO = None

# Extrusión de la jaula al hornear (studs): lo que sobresalen los detalles de la malla alta.
EXTRUSION = {"arbusto": 0.16, "casa_techo": 0.05, "casa_paredes": 0.035, "casa_zocalo": 0.03, "felpudo": 0.03,
             "botas": 0.03, "pico": 0.03}
EXTRUSION_DEFECTO = 0.04
# Empaquetado del atlas (ver la revisión: con islas pequeñas manda el margen).
PACK = dict(rotate_method="ANY", shape_method="CONCAVE", margin=0.0015)


def log(*a):
    print("[casa]", *a, flush=True)


# ======================================================================================================
# Escena y objetos
# ======================================================================================================


def escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = ESTUDIO_M
    scn.world = bpy.data.worlds.new("mundo")
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    return scn


def _preparar_bm(bm):
    """Triangula los polígonos de más de 4 lados y marca aristas duras según el tipo de cara."""
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4], quad_method="BEAUTY",
                          ngon_method="BEAUTY")
    bm.normal_update()
    capa = bm.faces.layers.int.get("suave")
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) != 2:
            e.smooth = False
            continue
        f1, f2 = e.link_faces
        ang = f1.normal.angle(f2.normal, 0.0)
        ambos = bool(f1[capa]) and bool(f2[capa]) if capa else False
        duro = (ang > math.radians(1.0) and not ambos) or ang > math.radians(62)
        e.smooth = not duro


def crear_objetos(piezas, mats):
    """Para cada pieza: objeto bajo (juego) y alto (horneado), con el origen en su pivote."""
    col_baja = bpy.data.collections.new("baja")
    col_alta = bpy.data.collections.new("alta")
    bpy.context.scene.collection.children.link(col_baja)
    bpy.context.scene.collection.children.link(col_alta)
    objs = []
    for p in piezas:
        bm = p.baja.bm
        if p.pivote is None:
            xs = [v.co for v in bm.verts]
            mn = Vector((min(c.x for c in xs), min(c.y for c in xs), min(c.z for c in xs)))
            mx = Vector((max(c.x for c in xs), max(c.y for c in xs), max(c.z for c in xs)))
            p.pivote = (mn + mx) / 2
        piv = Vector(p.pivote)
        _preparar_bm(bm)
        malla_b = bpy.data.meshes.new(p.nombre)
        bm.to_mesh(malla_b)
        # Malla alta = baja (sin lo marcado como solo_baja) + detalles.
        bh = bmesh.new()
        bh.from_mesh(malla_b)
        capa = bh.faces.layers.int.get("solo_baja")
        if capa is not None:
            fuera = [f for f in bh.faces if f[capa]]
            bmesh.ops.delete(bh, geom=fuera, context="FACES")
        if p.alta.bm.faces:
            _preparar_bm(p.alta.bm)
            tmp = bpy.data.meshes.new("tmp")
            p.alta.bm.to_mesh(tmp)
            bh.from_mesh(tmp)
            bpy.data.meshes.remove(tmp)
        malla_a = bpy.data.meshes.new(p.nombre + "_alta")
        bh.to_mesh(malla_a)
        bh.free()
        for m in (malla_b, malla_a):
            m.transform(Matrix.Translation(-piv))
            for n in p.mats:
                m.materials.append(mats[n])
        ob = bpy.data.objects.new(p.nombre, malla_b)
        oa = bpy.data.objects.new(p.nombre + "_alta", malla_a)
        ob.location = piv
        oa.location = piv
        col_baja.objects.link(ob)
        col_alta.objects.link(oa)
        ob["peso_uv"] = p.peso_uv
        objs.append((p, ob, oa))
    return objs


def triangulos(obj):
    return sum(len(pl.vertices) - 2 for pl in obj.data.polygons)


# ======================================================================================================
# UV: desplegado por pieza y empaquetado en un atlas común
# ======================================================================================================


def desplegar_atlas(objs):
    bajas = [ob for _, ob, _ in objs]
    bpy.ops.object.select_all(action="DESELECT")
    for ob in bajas:
        ob.data.uv_layers.new(name="UVMap")
        ob.select_set(True)
    bpy.context.view_layer.objects.active = bajas[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(52), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    # Peso de cada pieza en el atlas y menos sitio para lo que casi no se ve.
    for ob in bajas:
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        uv = bm.loops.layers.uv.active
        capa = bm.faces.layers.int.get("oculta")
        peso = ob["peso_uv"]
        for isla in bmesh_linked_uv_islands(bm, uv):
            # oculta = 1: casi no se ve (por dentro, contra la pared); 2: solo asoma en juntas finas.
            nivel = min(f[capa] for f in isla) if capa is not None else 0
            abajo = all(f.normal.z < -0.85 for f in isla)
            k = peso * {0: 0.55 if abajo else 1.0, 1: 0.3, 2: 0.12}[min(nivel, 2)]
            loops = [l for f in isla for l in f.loops]
            c = sum((l[uv].uv for l in loops), Vector((0, 0))) / len(loops)
            for l in loops:
                l[uv].uv = c + (l[uv].uv - c) * k
        bm.to_mesh(ob.data)
        bm.free()
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    t = time.time()
    bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, scale=True, merge_overlap=False,
                            margin_method="FRACTION", **PACK)
    log(f"UV empaquetadas en {time.time() - t:.1f} s")
    bpy.ops.object.mode_set(mode="OBJECT")


# ======================================================================================================
# Horneado
# ======================================================================================================


def _imagen(nombre, tam, color=True, flotante=True):
    img = bpy.data.images.new(nombre, tam, tam, alpha=True, float_buffer=flotante)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return img


def _material_horneado(img):
    m = bpy.data.materials.new("horneado")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1, 1, 1, 1)
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    n = nt.nodes.new("ShaderNodeTexImage")
    n.image = img
    nt.nodes.active = n
    return m


def _leer(img):
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


def hornear_atlas(objs, tam, carpeta, rapido):
    scn = bpy.context.scene
    tmp = _imagen("tmp_horneado", tam, color=False)
    mat_h = _material_horneado(tmp)
    ceros = np.zeros(tam * tam * 4, dtype=np.float32)
    canales = ["blanco", "color", "rug", "met", "emi", "alfa", "normal"]
    atlas = {k: np.zeros((tam, tam, 3), dtype=np.float32) for k in ("color", "emi", "normal")}
    atlas["rug"] = np.zeros((tam, tam), dtype=np.float32)
    atlas["met"] = np.zeros((tam, tam), dtype=np.float32)
    atlas["ao"] = np.ones((tam, tam), dtype=np.float32)
    atlas["alfa"] = np.ones((tam, tam), dtype=np.float32)
    lleno = np.zeros((tam, tam), dtype=bool)
    ids = np.full((tam, tam), -1, dtype=np.int16)
    informe = {}

    # Las mallas bajas pasan a usar el material de horneado (las altas conservan los procedurales).
    originales = {}
    for _, ob, _ in objs:
        originales[ob.name] = [m for m in ob.data.materials]
        ob.data.materials.clear()
        ob.data.materials.append(mat_h)

    # Canal "blanco": todo emite 1. Sirve para saber qué píxeles han encontrado la malla alta.
    for m in bpy.data.materials:
        if m.name in cm.CANALES:
            cm.CANALES[m.name]["blanco"] = 1.0

    todos = [o for o in scn.objects if o.type == "MESH"]
    muestras = {"blanco": 1, "color": 2 if rapido else 4, "rug": 2 if rapido else 4, "met": 2 if rapido else 4,
                "emi": 1, "alfa": 2 if rapido else 4, "normal": 2 if rapido else 6}
    t0 = time.time()
    for idx, (p, ob, oa) in enumerate(objs):
        ti = time.time()
        for o in todos:
            o.hide_render = o not in (ob, oa)
        # 1) Máscara de la isla (qué píxeles son de esta pieza).
        tmp.pixels.foreach_set(ceros)
        scn.cycles.samples = 1
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.bake(type="EMIT", margin=0, use_selected_to_active=False)
        mascara = _leer(tmp)[..., 0] > 0.5
        mats_alta = {m for m in oa.data.materials if m is not None}
        tiene_emision = any(m.name.startswith("neon") for m in mats_alta)
        tiene_alfa = any("alfa" in cm.CANALES.get(m.name, {}) for m in mats_alta)
        ext = EXTRUSION.get(p.nombre, EXTRUSION_DEFECTO)
        acierto = mascara
        for canal in canales:
            if canal == "emi" and not tiene_emision:
                continue
            if canal == "alfa" and not tiene_alfa:
                continue
            for m in mats_alta:
                cm.poner_canal(m, canal)
            tmp.pixels.foreach_set(ceros)
            scn.cycles.samples = muestras[canal]
            bpy.ops.object.select_all(action="DESELECT")
            oa.select_set(True)
            ob.select_set(True)
            bpy.context.view_layer.objects.active = ob
            tipo = "NORMAL" if canal == "normal" else "EMIT"
            kw = {"normal_space": "TANGENT"} if canal == "normal" else {}
            bpy.ops.object.bake(type=tipo, margin=0, use_selected_to_active=True, cage_extrusion=ext,
                                max_ray_distance=ext * 3.0, **kw)
            px = _leer(tmp)
            if canal == "blanco":
                acierto = mascara & (px[..., 0] > 0.5)
                continue
            sel = acierto
            if canal in ("color", "emi", "normal"):
                atlas[canal][sel] = px[..., :3][sel]
            else:
                atlas[canal][sel] = px[..., 0][sel]
        for m in mats_alta:
            cm.poner_canal(m, "normal")
        lleno |= acierto
        ids[acierto] = idx
        fallos = int(mascara.sum() - acierto.sum())
        informe[p.nombre] = {"pixeles": int(mascara.sum()), "sin_alta": fallos}
        log(f"  horneada {p.nombre:34s} {int(mascara.sum()):8d} px, {fallos:5d} sin malla alta, "
            f"{time.time() - ti:5.1f} s")

    # 2) Oclusión ambiental desde las mallas bajas, todas visibles (contacto entre piezas).
    for o in todos:
        o.hide_render = o.name.endswith("_alta")
    scn.world.light_settings.distance = 1.6
    scn.cycles.samples = 16 if rapido else 64
    for idx, (p, ob, oa) in enumerate(objs):
        tmp.pixels.foreach_set(ceros)
        bpy.ops.object.select_all(action="DESELECT")
        ob.select_set(True)
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.bake(type="AO", margin=0, use_selected_to_active=False)
        sel = ids == idx
        atlas["ao"][sel] = _leer(tmp)[..., 0][sel]
    log(f"Horneado completo en {time.time() - t0:.0f} s")

    # Restaurar materiales de las bajas.
    for _, ob, _ in objs:
        ob.data.materials.clear()
        for m in originales[ob.name]:
            ob.data.materials.append(m)
    return atlas, lleno, ids, informe


def _dilatar(arr, lleno, pasos=24):
    """Rellena los píxeles vacíos con la media de sus vecinos llenos (margen contra costuras al hacer mipmaps)."""
    a = arr.copy()
    m = lleno.copy()
    for _ in range(pasos):
        if m.all():
            break
        suma = np.zeros_like(a)
        cuenta = np.zeros(m.shape, dtype=np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            mm = np.roll(np.roll(m, dy, 0), dx, 1)
            aa = np.roll(np.roll(a, dy, 0), dx, 1)
            if a.ndim == 3:
                suma += aa * mm[..., None]
            else:
                suma += aa * mm
            cuenta += mm
        nuevos = (~m) & (cuenta > 0)
        if a.ndim == 3:
            a[nuevos] = suma[nuevos] / cuenta[nuevos][:, None]
        else:
            a[nuevos] = suma[nuevos] / cuenta[nuevos]
        m |= nuevos
    return a, m


def _a_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def guardar_atlas(atlas, lleno, carpeta):
    """Combina la oclusión con el color, dilata los bordes y guarda los PNG (de arriba abajo, como Roblox)."""
    rutas = {}
    ao = atlas["ao"]
    factor = 1.0 - 0.55 * np.power(np.clip(1.0 - ao, 0, 1), 1.15)
    color = atlas["color"] * factor[..., None]
    fondo_normal = np.zeros_like(atlas["normal"])
    fondo_normal[:] = (0.5, 0.5, 1.0)
    normal = np.where(lleno[..., None], atlas["normal"], fondo_normal)
    translucido = bool((atlas["alfa"] < 0.995).any())
    color_srgb = _a_srgb(color)
    if translucido:
        # El alfa va en el PNG de color (RGBA): solo las islas del cristal tienen alfa < 1.
        color_srgb = np.concatenate([color_srgb, atlas["alfa"][..., None]], axis=2)
    salidas = {
        "color": (color_srgb, True),
        "normal": (normal, True),
        "roughness": (atlas["rug"], False),
        "metalness": (atlas["met"], False),
        "emision": (_a_srgb(atlas["emi"]), True),
    }
    for nombre, (arr, rgb) in salidas.items():
        dil, _ = _dilatar(arr, lleno)
        img = np.clip(dil * 255 + 0.5, 0, 255).astype(np.uint8)
        img = img[::-1]  # Blender guarda de abajo arriba
        modo = ("RGBA" if img.ndim == 3 and img.shape[2] == 4 else "RGB") if rgb else "L"
        ruta = os.path.join(carpeta, f"{NOMBRE}_{nombre}.png")
        Image.fromarray(img, modo).save(ruta, optimize=True)
        rutas[nombre] = ruta
        log("  guardada", ruta)
    return rutas


def revisar_atlas(objs, lleno, tam, carpeta):
    """
    Revisión del horneado: rasteriza los triángulos UV de cada pieza y comprueba que todos sus píxeles están
    horneados (sin agujeros negros) y que ninguna isla pisa a otra.
    """
    esperado = Image.new("L", (tam, tam), 0)
    solape = np.zeros((tam, tam), dtype=np.uint8)
    for _, ob, _ in objs:
        capa = Image.new("L", (tam, tam), 0)
        d = ImageDraw.Draw(capa)
        uv = ob.data.uv_layers.active.data
        for pl in ob.data.polygons:
            pts = [(uv[i].uv.x * tam, (1 - uv[i].uv.y) * tam) for i in pl.loop_indices]
            d.polygon(pts, fill=255)
        arr = np.array(capa) > 0
        solape += arr.astype(np.uint8)
        esperado.paste(255, mask=capa)
    esp = np.array(esperado)[::-1] > 0  # a la orientación de Blender
    # Erosión de 1 px: los bordes exactos dependen del muestreo.
    er = esp & np.roll(esp, 1, 0) & np.roll(esp, -1, 0) & np.roll(esp, 1, 1) & np.roll(esp, -1, 1)
    agujeros = er & ~lleno
    solapes = int((solape > 1).sum())
    uso = float(esp.mean())
    log(f"Revisión del atlas: uso {uso * 100:.1f} %, píxeles sin hornear dentro de islas: {int(agujeros.sum())}, "
        f"píxeles con islas solapadas: {solapes}")
    # Imagen de control: islas en gris, agujeros en rojo.
    vista = np.zeros((tam, tam, 3), dtype=np.uint8)
    vista[esp] = (90, 90, 100)
    vista[lleno] = (60, 160, 90)
    vista[agujeros] = (255, 40, 40)
    Image.fromarray(vista[::-1]).save(os.path.join(carpeta, "_control_atlas.png"))
    return {"uso_atlas": round(uso, 4), "agujeros": int(agujeros.sum()), "solapes": solapes}


# ======================================================================================================
# Materiales finales (lo que verá Roblox) y render
# ======================================================================================================


def materiales_finales(objs, rutas):
    imgs = {k: bpy.data.images.load(v) for k, v in rutas.items()}
    for k in ("normal", "roughness", "metalness"):
        imgs[k].colorspace_settings.name = "Non-Color"

    m = bpy.data.materials.new(f"{NOMBRE}_atlas")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]

    def tex(nombre):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = imgs[nombre]
        return n

    nt.links.new(tex("color").outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex("roughness").outputs["Color"], b.inputs["Roughness"])
    nt.links.new(tex("metalness").outputs["Color"], b.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal").outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(tex("emision").outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 0.0

    vid = bpy.data.materials.new(f"{NOMBRE}_cristal")
    vid.use_nodes = True
    bv = vid.node_tree.nodes["Principled BSDF"]
    bv.inputs["Base Color"].default_value = (*cm.lin(COLOR_VIDRIO), 1)
    # En el render el cristal deja ver lo de dentro como en Studio (Glass con Transparency 0,4).
    bv.inputs["Roughness"].default_value = 0.02
    bv.inputs["Transmission Weight"].default_value = 0.0
    bv.inputs["Alpha"].default_value = 0.14
    bv.inputs["IOR"].default_value = 1.45
    vid.diffuse_color = (*cm.lin(COLOR_VIDRIO), 0.5)

    neo = bpy.data.materials.new(f"{NOMBRE}_neon")
    neo.use_nodes = True
    bn = neo.node_tree.nodes["Principled BSDF"]
    bn.inputs["Base Color"].default_value = (*cm.lin(COLOR_NEON), 1)
    bn.inputs["Emission Color"].default_value = (*cm.lin(COLOR_NEON), 1)
    bn.inputs["Emission Strength"].default_value = 6.0
    neo.diffuse_color = (*cm.lin(COLOR_NEON), 1)

    calido = bpy.data.materials.new(f"{NOMBRE}_neon_calido")
    calido.use_nodes = True
    bc = calido.node_tree.nodes["Principled BSDF"]
    bc.inputs["Base Color"].default_value = (*cm.lin(COLOR_NEON_CALIDO), 1)
    bc.inputs["Emission Color"].default_value = (*cm.lin(COLOR_NEON_CALIDO), 1)
    bc.inputs["Emission Strength"].default_value = 3.0
    calido.diffuse_color = (*cm.lin(COLOR_NEON_CALIDO), 1)

    otros = {}
    for sufijo, (hexa, fuerza) in NEONES.items():
        mn = bpy.data.materials.new(f"{NOMBRE}{sufijo}")
        mn.use_nodes = True
        bx = mn.node_tree.nodes["Principled BSDF"]
        bx.inputs["Base Color"].default_value = (*cm.lin(hexa), 1)
        bx.inputs["Emission Color"].default_value = (*cm.lin(hexa), 1)
        bx.inputs["Emission Strength"].default_value = fuerza
        mn.diffuse_color = (*cm.lin(hexa), 1)
        otros[sufijo] = mn

    trans = None
    if TRANSLUCIDO:
        # Mismo atlas, con el alfa del PNG de color (como AlphaMode = Transparency en Studio).
        trans = m.copy()
        trans.name = f"{NOMBRE}_atlas_translucido"
        nodos = trans.node_tree.nodes
        bt = nodos["Principled BSDF"]
        tc = [n for n in nodos if n.type == "TEX_IMAGE" and n.image == imgs["color"]][0]
        trans.node_tree.links.new(tc.outputs["Alpha"], bt.inputs["Alpha"])
        imgs["color"].alpha_mode = "STRAIGHT"

    for p, ob, oa in objs:
        ob.data.materials.clear()
        sufijo = next((k for k in NEONES if ob.name.endswith(k)), None)
        if sufijo:
            ob.data.materials.append(otros[sufijo])
        elif TRANSLUCIDO and TRANSLUCIDO in ob.name:
            ob.data.materials.append(trans)
        elif ob.name.endswith("_neon_calido"):
            ob.data.materials.append(calido)
        elif ob.name.endswith("_neon"):
            ob.data.materials.append(neo)
        elif "cristal" in ob.name:
            ob.data.materials.append(vid)
        else:
            ob.data.materials.append(m)
        for pl in ob.data.polygons:
            pl.material_index = 0
    return m


DETALLES = [("Puerta", -12, 8, (1.6, -3.9, 2.9), 2.6), ("Ventana", 18, 10, (-2.35, -3.9, 3.4), 2.1),
            ("Pico y botas", -25, 18, (0.1, -4.0, 1.4), 1.5), ("Buzón y maceta", 25, 12, (3.7, -3.9, 2.4), 1.6),
            ("Lámpara y número", -20, 5, (0.8, -3.9, 4.9), 1.4), ("Medidor y cable", 70, 10, (4.8, -1.3, 3.8), 2.0),
            ("Chimenea", -60, 25, (-2.35, 1.75, 7.4), 1.3), ("Panel solar", 60, 40, (2.6, -0.55, 6.6), 1.9),
            ("Zócalo y bajante", -60, 10, (-4.6, -3.0, 1.6), 1.6), ("Rejilla y ventana", -90, 5, (-4.6, 0.6, 3.0), 1.9)]


def _material_caras():
    m = bpy.data.materials.new("caras")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    a = nt.nodes.new("ShaderNodeBsdfDiffuse")
    a.inputs["Color"].default_value = (0.6, 0.62, 0.66, 1)
    # Rojo difuso (no emisivo): las caras de espaldas escondidas no iluminan lo de alrededor y no confunden.
    b = nt.nodes.new("ShaderNodeBsdfDiffuse")
    b.inputs["Color"].default_value = (1, 0, 0, 1)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(geo.outputs["Backfacing"], mix.inputs["Fac"])
    nt.links.new(a.outputs[0], mix.inputs[1])
    nt.links.new(b.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs["Surface"])
    return m


def _mira():
    o = bpy.data.objects.get("mira")
    if o is None:
        o = bpy.data.objects.new("mira", None)
        bpy.context.scene.collection.objects.link(o)
    return o


def preparar_estudio():
    scn = bpy.context.scene
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.cycles.use_denoising = True
    w = scn.world
    w.use_nodes = True
    fondo = w.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.42, 0.47, 0.56, 1)
    fondo.inputs["Strength"].default_value = 0.35
    # Suelo de estudio que recibe sombras.
    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=60, fill_type="NGON", location=(0, 0, -0.001))
    s = bpy.context.active_object
    s.name = "suelo_estudio"
    ms = bpy.data.materials.new("suelo_estudio")
    ms.use_nodes = True
    bs = ms.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.12, 0.125, 0.135, 1)
    bs.inputs["Roughness"].default_value = 0.95
    s.data.materials.append(ms)
    luces = {}
    for nombre, energia, color, tam in (("clave", 2600, (1.0, 0.93, 0.84), 6), ("relleno", 700, (0.78, 0.86, 1.0), 10),
                                        ("contra", 2200, (0.9, 0.95, 1.0), 4)):
        d = bpy.data.lights.new(nombre, "AREA")
        d.energy = energia
        d.color = color
        d.size = tam
        o = bpy.data.objects.new(nombre, d)
        scn.collection.objects.link(o)
        c = o.constraints.new("TRACK_TO")
        c.target = _mira()
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        luces[nombre] = o
    return luces


def _material_malla():
    m = bpy.data.materials.new("vista_malla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 1.0
    base = nt.nodes.new("ShaderNodeBsdfDiffuse")
    base.inputs["Color"].default_value = (0.36, 0.38, 0.42, 1)
    linea = nt.nodes.new("ShaderNodeEmission")
    linea.inputs["Color"].default_value = (0.25, 0.9, 1.0, 1)
    linea.inputs["Strength"].default_value = 1.5
    mez = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wire.outputs["Fac"], mez.inputs["Fac"])
    nt.links.new(base.outputs["BSDF"], mez.inputs[1])
    nt.links.new(linea.outputs["Emission"], mez.inputs[2])
    nt.links.new(mez.outputs["Shader"], out.inputs["Surface"])
    return m


def render_vista(objetos, luces, nombre, az, el, ruta, tam, muestras, centro=None, radio=None, lente=50,
                 malla=False, ortho=False):
    """Cámara a `az` grados (0 = de frente, desde -Y; 90 = desde +X) y `el` de elevación; luces de 3 puntos."""
    scn = bpy.context.scene
    scn.render.resolution_x = scn.render.resolution_y = tam
    scn.cycles.samples = muestras
    if centro is None or radio is None:
        mn = Vector((1e9,) * 3)
        mx = Vector((-1e9,) * 3)
        for o in objetos:
            for c in o.bound_box:
                w = o.matrix_world @ Vector(c)
                mn = Vector(map(min, mn, w))
                mx = Vector(map(max, mx, w))
        centro = (mn + mx) / 2 if centro is None else Vector(centro)
        radio = (mx - mn).length / 2 if radio is None else radio
    centro = Vector(centro)
    _mira().location = centro
    a, e = math.radians(az), math.radians(el)
    dirv = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = lente
    cam_d.clip_end = 1000
    cam = bpy.data.objects.new("cam", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    fov = 2 * math.atan(18 / lente)
    dist = radio * 1.08 / math.sin(fov / 2)
    if ortho:
        cam_d.type = "ORTHO"
        cam_d.ortho_scale = radio * 2.1
    cam.location = centro + dirv * dist
    cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()

    def colocar(o, az_rel, el_l, distancia):
        aa, ee = math.radians(az + az_rel), math.radians(el_l)
        dv = Vector((math.sin(aa) * math.cos(ee), -math.cos(aa) * math.cos(ee), math.sin(ee)))
        o.location = centro + dv * distancia

    k = max(1.0, radio / 6.0)
    colocar(luces["clave"], -50, 42 if el < 60 else 70, 16 * k)
    colocar(luces["relleno"], 65, 18, 18 * k)
    colocar(luces["contra"], 170, 38, 16 * k)
    anterior = scn.view_layers[0].material_override
    if malla:
        scn.view_layers[0].material_override = _material_malla()
    scn.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
    scn.view_layers[0].material_override = anterior if not malla else None
    bpy.data.objects.remove(cam)
    return ruta


def _fuente(tam, negrita=True):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrita else \
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(ruta, tam) if os.path.exists(ruta) else ImageFont.load_default()


def hoja(rutas, salida, titulo, notas, columnas=4):
    tam = Image.open(rutas[0][1]).size[0]
    filas = math.ceil(len(rutas) / columnas)
    cab = 70 + 22 * len(notas)
    img = Image.new("RGB", (columnas * tam, cab + filas * tam), (16, 18, 24))
    d = ImageDraw.Draw(img)
    d.text((16, 12), titulo, fill=(255, 214, 102), font=_fuente(30))
    for i, n in enumerate(notas):
        d.text((18, 54 + i * 22), n, fill=(210, 214, 224), font=_fuente(17, False))
    for i, (nombre, ruta) in enumerate(rutas):
        x, y = (i % columnas) * tam, cab + (i // columnas) * tam
        img.paste(Image.open(ruta).convert("RGB"), (x, y))
        d.rectangle((x, y, x + tam - 1, y + tam - 1), outline=(40, 44, 56))
        d.text((x + 12, y + 10), nombre, fill=(255, 255, 255), font=_fuente(22))
    img.save(salida)
    log("hoja:", salida)
    return salida


# ======================================================================================================
# Exportación, verificación y JSON
# ======================================================================================================


def aplicar_giro(objetos):
    """GIRO_IMPORTACION: gira todo 180° alrededor del eje vertical (en la malla y en la posición del pivote)."""
    R = Matrix.Rotation(math.radians(GIRO_IMPORTACION), 4, "Z")
    for o in objetos:
        o.data.transform(R)
        o.location = R @ o.location
    return R


def exportar_fbx(ruta, objetos):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH"},
        global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="Z", axis_up="Y", bake_space_transform=False,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True, use_triangles=False,
        add_leaf_bones=False, bake_anim=False, embed_textures=True, path_mode="COPY",
    )
    log("FBX:", ruta)


def verificar_fbx(ruta):
    """Reimporta el FBX en una escena limpia y devuelve lo que trae."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta)
    res = {"mallas": {}, "texturas": set()}
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
        mats = [m.name for m in o.data.materials if m]
        for m in o.data.materials:
            if m and m.node_tree:
                for n in m.node_tree.nodes:
                    if n.type == "TEX_IMAGE" and n.image:
                        res["texturas"].add(n.image.name)
        res["mallas"][o.name] = {"triangulos": tris, "uv": len(o.data.uv_layers), "materiales": mats}
    tam_m = mx - mn
    res["tam_metros"] = [round(v, 3) for v in tam_m]
    res["tam_studs"] = [round(v / ESTUDIO_M, 2) for v in tam_m]
    res["texturas"] = sorted(res["texturas"])
    res["total_triangulos"] = sum(m["triangulos"] for m in res["mallas"].values())
    return res


def a_roblox(v):
    """Punto de Blender (studs) -> coordenadas de Roblox (studs) tal como llega en el FBX (con el giro)."""
    conv = axis_conversion(to_forward="Z", to_up="Y").to_4x4()
    R = Matrix.Rotation(math.radians(GIRO_IMPORTACION), 4, "Z")
    w = conv @ R @ Vector(v)
    return [round(w.x, 3), round(w.y, 3), round(w.z, 3)]


ANIMABLES = {
    "puerta": ("Bisagras (eje vertical). Se abre hacia fuera.", "Y", [0, -100]),
    "ventana_frontal_contraventana_izq": ("Bisagras (eje vertical). Modelada entreabierta 115°.", "Y", [-115, 0]),
    "ventana_frontal_contraventana_der": ("Bisagras (eje vertical). Modelada entreabierta 95°.", "Y", [95, 0]),
    "buzon_tapa": ("Bisagra de atrás (eje horizontal, paralelo a la fachada). Modelada abierta 16°.", "X", [-16, 0]),
    "buzon_bandera": ("Remache (eje horizontal, perpendicular al lateral del buzón). Modelada levantada.", "X",
                      [0, 90]),
    "medidor_puerta": ("Bisagras (eje vertical) en el canto delantero.", "Y", [0, 110]),
}


def tipo_roblox(nombre):
    for sufijo, (hexa, _) in NEONES.items():
        if nombre.endswith(sufijo):
            return f"Neon, Color {hexa}"
    if TRANSLUCIDO and TRANSLUCIDO in nombre:
        return "SurfaceAppearance (atlas) con AlphaMode = Transparency"
    if nombre.endswith("_neon_calido"):
        return f"Neon, Color {COLOR_NEON_CALIDO}"
    if nombre.endswith("_neon"):
        return f"Neon, Color {COLOR_NEON}"
    if "cristal" in nombre:
        return f"Glass, Color {COLOR_VIDRIO}, Transparency 0.4"
    return "SurfaceAppearance (atlas)"


# ======================================================================================================
# Principal
# ======================================================================================================


def vistas_rapidas(objs, carpeta, alta=True):
    """Renders rápidos con los materiales procedurales (para modelar sin hornear)."""
    luces = preparar_estudio()
    visibles = [oa if alta else ob for _, ob, oa in objs]
    for o in bpy.context.scene.objects:
        if o.type == "MESH" and o.name != "suelo_estudio":
            o.hide_render = o not in visibles
    rutas = []
    for nombre, az, el in (("Frente", 0, 8), ("3/4 Frontal", -38, 20), ("Lateral Izq", -90, 8),
                           ("Lateral Der", 90, 8), ("3/4 Trasera", 140, 22), ("Arriba", 0, 75)):
        r = os.path.join(carpeta, f"vista_{nombre.replace('/', '-').replace(' ', '_')}.png")
        render_vista(visibles, luces, nombre, az, el, r, 640, 24)
        rutas.append((nombre, r))
    return rutas


def generar(cfg):
    """
    Proceso completo para una casa. cfg: nombre, titulo, descripcion, presupuesto, construir() -> (piezas, P),
    materiales(P) -> {nombre: material}, y opcionalmente extrusion, detalles, animables, color_vidrio.
    """
    global NOMBRE, EXTRUSION, DETALLES, ANIMABLES, COLOR_VIDRIO, NEONES, TRANSLUCIDO
    NOMBRE = cfg["nombre"]
    EXTRUSION = cfg.get("extrusion", EXTRUSION)
    DETALLES = cfg.get("detalles", DETALLES)
    ANIMABLES = cfg.get("animables", ANIMABLES)
    COLOR_VIDRIO = cfg.get("color_vidrio", COLOR_VIDRIO)
    NEONES = cfg.get("neones", NEONES)
    TRANSLUCIDO = cfg.get("translucido", TRANSLUCIDO)
    titulo = cfg["titulo"]
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--vista", action="store_true")
    ap.add_argument("--detalles", action="store_true", help="solo para --vista: primeros planos")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    carpeta = os.path.abspath(args.salida)
    tmp = os.path.join(carpeta, "_render_tmp")
    os.makedirs(tmp, exist_ok=True)
    t0 = time.time()

    escena()
    piezas, P = cfg["construir"]()
    mats = cfg["materiales"](P)
    objs = crear_objetos(piezas, mats)
    total = sum(triangulos(ob) for _, ob, _ in objs)
    log(f"{len(objs)} piezas, {total} triángulos (malla baja)")
    for p, ob, oa in objs:
        log(f"  {ob.name:36s} {triangulos(ob):6d} tri   alta {triangulos(oa):7d}")

    if args.vista:
        if args.detalles:
            luces = preparar_estudio()
            altas = [oa for _, _, oa in objs]
            for o in bpy.context.scene.objects:
                if o.type == "MESH" and o.name != "suelo_estudio":
                    o.hide_render = o not in altas
            det = []
            for nombre, az, el, c, rad in DETALLES:
                r = os.path.join(tmp, f"vd_{nombre.replace(' ', '_')}.png")
                render_vista(altas, luces, nombre, az, el, r, 560, 32, centro=c, radio=rad)
                det.append((nombre, r))
            # Comprobación de normales: caras de espaldas en rojo.
            m = _material_caras()
            bpy.context.scene.view_layers[0].material_override = m
            for nombre, az, el in (("Normales frente", -38, 20), ("Normales detrás", 140, 22)):
                r = os.path.join(tmp, f"vd_{nombre.replace(' ', '_')}.png")
                bajas = [ob for _, ob, _ in objs]
                for o in bpy.context.scene.objects:
                    if o.type == "MESH" and o.name != "suelo_estudio":
                        o.hide_render = o not in bajas
                render_vista(bajas, luces, nombre, az, el, r, 560, 8)
                bpy.context.scene.view_layers[0].material_override = m
                det.append((nombre, r))
            bpy.context.scene.view_layers[0].material_override = None
            hoja(det, os.path.join(carpeta, "_vista_detalles.png"), f"{titulo} — detalles (malla alta)", [],
                 columnas=5)
            return
        rutas = vistas_rapidas(objs, tmp)
        hoja(rutas, os.path.join(carpeta, "_vista_modelado.png"), f"{titulo} — modelado (malla alta)",
             [f"{total} triángulos en la malla baja"], columnas=3)
        return

    tam = 512 if args.rapido else ATLAS
    desplegar_atlas(objs)
    atlas, lleno, ids, informe = hornear_atlas(objs, tam, carpeta, args.rapido)
    control = revisar_atlas(objs, lleno, tam, carpeta)
    rutas = guardar_atlas(atlas, lleno, carpeta)

    # Escena final: solo las mallas bajas con el atlas.
    for _, _, oa in objs:
        bpy.data.objects.remove(oa)
    bajas = [ob for _, ob, _ in objs]
    materiales_finales(objs, rutas)
    luces = preparar_estudio()
    for pos, energia, color in cfg.get("luces_render", ()):
        # Luces de dentro (solo para el render; en Studio van como PointLight en el anclaje del JSON).
        d = bpy.data.lights.new("luz_interior", "POINT")
        d.energy = energia
        d.color = color
        d.shadow_soft_size = 0.8
        o = bpy.data.objects.new("luz_interior", d)
        o.location = pos
        bpy.context.scene.collection.objects.link(o)
    tr = 520 if args.rapido else 900
    mu = 24 if args.rapido else 96
    vistas = [("Frente", 0, 6), ("3/4 Frontal", -38, 20), ("Lateral Izq", -90, 6), ("3/4 Trasera", 140, 22),
              ("Trasera", 180, 6), ("Lateral Der", 90, 6), ("Arriba", 0, 89), ("Wireframe", -38, 20)]
    rutas_v = []
    for nombre, az, el in vistas:
        r = os.path.join(tmp, f"t_{nombre.replace('/', '-').replace(' ', '_')}.png")
        render_vista(bajas, luces, nombre, az, el, r, tr, mu, malla=nombre == "Wireframe")
        rutas_v.append((nombre, r))
    dims = _dimensiones(bajas)
    hoja(rutas_v, os.path.join(carpeta, f"{NOMBRE}_turnaround.png"), f"{titulo} — {NOMBRE}",
         [f"{total} triángulos · {dims[0]:.1f} × {dims[1]:.1f} × {dims[2]:.1f} studs (ancho × fondo × alto) · "
          f"atlas PBR {ATLAS}² · {len(bajas)} piezas"])
    # Primeros planos (puerta, ventana, entorno, medidor).
    det = []
    for nombre, az, el, c, rad in DETALLES:
        r = os.path.join(tmp, f"d_{nombre.replace(' ', '_')}.png")
        render_vista(bajas, luces, nombre, az, el, r, 600 if not args.rapido else 360, mu, centro=c, radio=rad)
        det.append((nombre, r))
    hoja(det, os.path.join(carpeta, f"{NOMBRE}_detalles.png"), f"{titulo} — detalles", [], columnas=4)

    # Exportación con el giro, y JSON.
    info_piezas = []
    for p, ob, _ in objs:
        mn, mx = _caja([ob])
        info = {
            "nombre": ob.name,
            "triangulos": triangulos(ob),
            "roblox": tipo_roblox(ob.name),
            "pivote_blender": [round(v, 3) for v in ob.location],
            "pivote_roblox": a_roblox(ob.location),
            "centro_caja_roblox": a_roblox((mn + mx) / 2),
            "tam_studs_blender": [round(v, 3) for v in (mx - mn)],
        }
        if ob.name in ANIMABLES:
            texto, eje, rango = ANIMABLES[ob.name]
            info["animable"] = {"descripcion": texto, "eje_roblox": eje, "angulos": rango}
        if p.extra:
            info["anclajes_roblox"] = {k: a_roblox(v) for k, v in p.extra.items()
                                       if isinstance(v, (list, tuple)) and len(v) == 3}
        info_piezas.append(info)
    aplicar_giro(bajas)
    ruta_fbx = os.path.join(carpeta, f"{NOMBRE}.fbx")
    exportar_fbx(ruta_fbx, bajas)
    verif = verificar_fbx(ruta_fbx)
    log(f"Reimportado: {len(verif['mallas'])} mallas, {verif['total_triangulos']} triángulos, "
        f"{verif['tam_studs']} studs, texturas {verif['texturas']}")
    datos = {
        "nombre": NOMBRE,
        "descripcion": cfg["descripcion"],
        "triangulos": total,
        "presupuesto_triangulos": cfg["presupuesto"],
        "tam_studs": {"ancho_x": round(dims[0], 2), "fondo": round(dims[1], 2), "alto": round(dims[2], 2)},
        "escala": "1 unidad de Blender = 1 stud; FBX en metros (1 stud = 0,28 m), Apply Scalings: FBX All",
        "giro_importacion": f"{GIRO_IMPORTACION}° alrededor del eje vertical antes de exportar",
        "frente": "En Blender la fachada mira a -Y. Con el giro, en el FBX mira a +Z.",
        "texturas": {k: os.path.basename(v) for k, v in rutas.items()},
        "atlas": {"tam": ATLAS, **control},
        "horneado": informe,
        "verificacion_fbx": verif,
        "piezas": info_piezas,
        "luces_sugeridas_roblox": [{"posicion": a_roblox(pos), "color": [round(c, 2) for c in color]}
                                   for pos, _, color in cfg.get("luces_render", ())],
    }
    with open(os.path.join(carpeta, f"{NOMBRE}.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    log(f"Terminado en {(time.time() - t0) / 60:.1f} min")


def _caja(objetos):
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objetos:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


def _dimensiones(objetos):
    mn, mx = _caja(objetos)
    return list(mx - mn)


def main():
    generar({
        "nombre": "casa_minero",
        "titulo": "Casa del minero",
        "descripcion": "Casa de un minero en el pueblo de la colonia humana. Piezas separadas con un atlas PBR.",
        "presupuesto": 12000,
        "construir": cp.construir,
        "materiales": cm.crear_materiales,
    })


if __name__ == "__main__":
    main()
