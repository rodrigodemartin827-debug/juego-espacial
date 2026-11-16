"""
Tubería de un modelo del Planeta Humano: escena limpia -> modelado -> UV -> horneado PBR al atlas 1024 ->
turnaround de 6 vistas -> FBX (con GIRO_IMPORTACION) -> JSON -> verificación reimportando el FBX.
"""

import json
import math
import os
import time

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from PIL import Image, ImageDraw, ImageFont

from geometria import Modelo
from materiales import crear_material, spec, srgb

TAM_ATLAS = 1024
GIRO_IMPORTACION = math.pi  # 180° alrededor de la vertical (el eje Y de Roblox) antes de exportar
PRESUPUESTOS = {"edificio_grande": 15000, "edificio_mediano": 8000, "prop": 2000, "vegetacion": 4000,
                "vehiculo": 10000}
RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


# --------------------------------------------------------------------------------------------------------------
# UV
# --------------------------------------------------------------------------------------------------------------

def _caras_ocultas(objs):
    """
    Caras que no se ven nunca: las que quedan enterradas dentro de otro sólido opaco y las que miran al suelo en
    z = 0. Siguen en la malla (cada pieza es un sólido cerrado), pero en el atlas se encogen para dejar los
    texels a lo que sí se ve.
    """
    from mathutils.bvhtree import BVHTree
    verts, polys = [], []
    for o in objs:
        if "cristal" in o["parte"] or "agua" in o["parte"]:
            continue
        base = len(verts)
        verts += [v.co.copy() for v in o.data.vertices]
        polys += [[base + i for i in p.vertices] for p in o.data.polygons]
    arbol = BVHTree.FromPolygons(verts, polys, epsilon=0.0)
    d = Vector((0.3137, 0.5291, 0.7885)).normalized()

    def dentro(p):
        n = 0
        o = p
        for _ in range(48):
            loc, nor, _i, _d = arbol.ray_cast(o, d)
            if loc is None:
                break
            n += 1 if nor.dot(d) > 0 else -1
            o = loc + d * 1e-4
        return n > 0

    ocultas = {}
    for o in objs:
        me = o.data
        lista = []
        for p in me.polygons:
            c = p.center
            nrm = p.normal
            if nrm.z < -0.95 and c.z < 0.03:
                lista.append(p.index)
                continue
            pts = [c] + [c.lerp(me.vertices[i].co, 0.85) for i in p.vertices]
            if all(dentro(q + nrm * 0.006) for q in pts):
                lista.append(p.index)
        ocultas[o.name] = lista
    return ocultas


def desplegar(objs):
    """Un solo atlas para todas las piezas: proyección inteligente y empaquetado conjunto."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.data.uv_layers.new(name="UVMap")
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    ocultas = _caras_ocultas(objs)
    n_oc = 0
    for o in objs:
        uv = o.data.uv_layers.active.data
        for pi in ocultas[o.name]:
            p = o.data.polygons[pi]
            li = list(p.loop_indices)
            cx = sum(uv[i].uv.x for i in li) / len(li)
            cy = sum(uv[i].uv.y for i in li) / len(li)
            for i in li:
                uv[i].uv = (cx + (uv[i].uv.x - cx) * 0.12, cy + (uv[i].uv.y - cy) * 0.12)
            n_oc += 1
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(margin=0.003, rotate=True, margin_method="FRACTION", shape_method="AABB")
    bpy.ops.object.mode_set(mode="OBJECT")
    return n_oc


# --------------------------------------------------------------------------------------------------------------
# Horneado
# --------------------------------------------------------------------------------------------------------------

def _img(nombre, color):
    im = bpy.data.images.new(nombre, TAM_ATLAS, TAM_ATLAS, alpha=False, float_buffer=False)
    im.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return im


def _destino(mats, im):
    for m in mats:
        nt = m.node_tree
        n = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "destino"
        n.image = im
        nt.nodes.active = n


def _emitir(mats, canal):
    """Conecta lo que entra en `canal` del Principled a una emisión, para hornearlo con EMIT."""
    for m in mats:
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        em = nt.nodes.get("em_h") or nt.nodes.new("ShaderNodeEmission")
        em.name = "em_h"
        for l in list(em.inputs["Color"].links):
            nt.links.remove(l)
        if canal == "_blanco":
            em.inputs["Color"].default_value = (1, 1, 1, 1)
        elif canal == "Emission Color" and b.inputs["Emission Strength"].default_value <= 0:
            em.inputs["Color"].default_value = (0, 0, 0, 1)
        else:
            s = b.inputs[canal]
            if s.is_linked:
                nt.links.new(s.links[0].from_socket, em.inputs["Color"])
            else:
                v = s.default_value
                em.inputs["Color"].default_value = (v, v, v, 1) if isinstance(v, float) else tuple(v)
        nt.links.new(em.outputs[0], out.inputs["Surface"])


def _restaurar(mats):
    for m in mats:
        nt = m.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        nt.links.new(nt.nodes["Principled BSDF"].outputs[0], out.inputs["Surface"])


def _hornear(objs, tipo, **kw):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.bake(type=tipo, margin=0, use_clear=False, **kw)


def _pix(im):
    a = np.empty(TAM_ATLAS * TAM_ATLAS * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    return a.reshape(TAM_ATLAS, TAM_ATLAS, 4)[::-1, :, :3].copy()  # fila 0 = arriba


def _dilatar(img, mascara, pasos=8):
    """Extiende el borde de cada isla hacia fuera (margen) sin pisar otras islas."""
    m = mascara.copy()
    out = img.copy()
    for _ in range(pasos):
        acc = np.zeros_like(out)
        cnt = np.zeros(m.shape, dtype=np.float32)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                ms = np.roll(np.roll(m, dy, 0), dx, 1)
                acc += np.roll(np.roll(out, dy, 0), dx, 1) * ms[..., None]
                cnt += ms
        nuevo = (~m) & (cnt > 0)
        out[nuevo] = acc[nuevo] / cnt[nuevo][..., None]
        m = m | nuevo
    return out, m


def hornear(objs, mats, carpeta, nombre, radio):
    """Hornea color (con oclusión), normal, rugosidad, metal y emisión. Devuelve {canal: ruta}."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 1
    scn.cycles.use_denoising = False
    scn.render.bake.use_pass_direct = False
    scn.render.bake.use_pass_indirect = False
    datos = {}

    def pase(clave, canal, color):
        im = _img(f"h_{clave}", color)
        _destino(mats, im)
        _emitir(mats, canal)
        _hornear(objs, "EMIT")
        datos[clave] = _pix(im)
        bpy.data.images.remove(im)

    pase("mascara", "_blanco", False)
    pase("color", "Base Color", True)
    pase("roughness", "Roughness", False)
    pase("metalness", "Metallic", False)
    pase("emision", "Emission Color", True)
    _restaurar(mats)

    # Normal en espacio tangente (incluye el relieve procedural de los materiales).
    im = _img("h_normal", False)
    px = np.empty(TAM_ATLAS * TAM_ATLAS * 4, dtype=np.float32)
    px[:] = np.tile(np.array([0.5, 0.5, 1.0, 1.0], dtype=np.float32), TAM_ATLAS * TAM_ATLAS)
    im.pixels.foreach_set(px)
    _destino(mats, im)
    _hornear(objs, "NORMAL", normal_space="TANGENT")
    datos["normal"] = _pix(im)
    bpy.data.images.remove(im)

    # Oclusión ambiental: solo las piezas opacas (el cristal y el agua no dan sombra).
    opacos = [o for o in objs if o["parte"] not in ("cristal", "agua") and "cristal" not in o["parte"]]
    ocultos = [o for o in objs if o not in opacos]
    for o in ocultos:
        o.hide_render = True
    im = _img("h_ao", False)
    px[:] = 1.0
    im.pixels.foreach_set(px)
    mats_op = list({s.material for o in opacos for s in o.material_slots})
    _destino(mats_op, im)
    scn.cycles.samples = 48
    try:
        scn.world.light_settings.distance = max(0.6, radio * 0.22)
    except Exception:
        pass
    if opacos:
        _hornear(opacos, "AO")
    ao = _pix(im)[..., :1]
    bpy.data.images.remove(im)
    for o in ocultos:
        o.hide_render = False

    mascara = datos.pop("mascara")[..., 0] > 0.5
    brilla = datos["emision"].max(axis=2, keepdims=True) > 0.02
    factor = 1.0 - 0.6 * (1.0 - np.clip(ao, 0, 1)) ** 1.2
    factor = np.where(brilla, 1.0, factor)
    datos["color"] = datos["color"] * factor

    rutas = {}
    tiene_emision = bool(brilla.any())
    for clave, arr in datos.items():
        if clave == "emision" and not tiene_emision:
            continue
        fondo = {"normal": (0.5, 0.5, 1.0), "roughness": (0.5,) * 3, "metalness": (0.0,) * 3}.get(clave)
        arr, m2 = _dilatar(arr, mascara)
        if fondo is not None:
            arr[~m2] = fondo
        b8 = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
        ruta = os.path.join(carpeta, f"{nombre}_{clave}.png")
        if clave in ("roughness", "metalness"):
            Image.fromarray(b8[..., 0], "L").save(ruta, optimize=True)
        else:
            Image.fromarray(b8, "RGB").save(ruta, optimize=True)
        rutas[clave] = ruta
    cobertura = float(mascara.mean())
    return rutas, cobertura


def materiales_finales(objs, rutas, nombre):
    """Sustituye los materiales procedurales por los del atlas (lo que verá Roblox)."""
    def cargar(clave, color):
        im = bpy.data.images.load(rutas[clave])
        im.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return im

    ims = {k: cargar(k, k in ("color", "emision")) for k in rutas}

    def nuevo(sufijo, alfa=1.0, emision=True):
        m = bpy.data.materials.new(f"{nombre}{sufijo}")
        m.use_nodes = True
        nt = m.node_tree
        b = nt.nodes["Principled BSDF"]

        def tex(clave):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = ims[clave]
            return n.outputs["Color"]

        nt.links.new(tex("color"), b.inputs["Base Color"])
        nt.links.new(tex("roughness"), b.inputs["Roughness"])
        nt.links.new(tex("metalness"), b.inputs["Metallic"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tex("normal"), nm.inputs["Color"])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])
        if emision and "emision" in ims:
            nt.links.new(tex("emision"), b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = 5.0
        if alfa < 1.0:
            b.inputs["Alpha"].default_value = alfa
        return m

    base = nuevo("_mat", emision=False)
    neon = nuevo("_mat_neon") if "emision" in ims else base
    cristal = nuevo("_mat_cristal", alfa=0.42, emision=False)
    agua = nuevo("_mat_agua", alfa=0.6, emision=False)
    for o in objs:
        parte = o["parte"]
        if "neon" in parte or "luz" in parte:
            m = neon
        elif "cristal" in parte:
            m = cristal
        elif "agua" in parte:
            m = agua
        else:
            m = base
        o.data.materials.clear()
        o.data.materials.append(m)
        for p in o.data.polygons:
            p.material_index = 0


# --------------------------------------------------------------------------------------------------------------
# Turnaround
# --------------------------------------------------------------------------------------------------------------

VISTAS = [("Frente", 0, 10), ("3/4", -38, 22), ("Lateral", -90, 8), ("3/4 Trasera", -142, 22), ("Arriba", 0, 89),
          ("Wireframe", -38, 22)]


def _fuente(tam):
    for r in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"):
        if os.path.exists(r):
            return ImageFont.truetype(r, tam)
    return ImageFont.load_default(tam)


def _mat_malla():
    m = bpy.data.materials.new("vista_malla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 1.0
    base = nt.nodes.new("ShaderNodeBsdfDiffuse")
    base.inputs["Color"].default_value = (0.42, 0.44, 0.48, 1)
    linea = nt.nodes.new("ShaderNodeEmission")
    linea.inputs["Color"].default_value = (0.05, 0.75, 0.9, 1)
    linea.inputs["Strength"].default_value = 1.2
    mz = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wire.outputs[0], mz.inputs[0])
    nt.links.new(base.outputs[0], mz.inputs[1])
    nt.links.new(linea.outputs[0], mz.inputs[2])
    nt.links.new(mz.outputs[0], salida.inputs["Surface"])
    return m


def turnaround(objs, ruta, titulo, subtitulo, tam=640, muestras=40):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = muestras
    scn.cycles.use_adaptive_sampling = True
    try:
        scn.cycles.use_denoising = True
    except Exception:
        pass
    scn.render.resolution_x = scn.render.resolution_y = tam
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = False
    scn.view_settings.view_transform = "Standard"
    scn.world = scn.world or bpy.data.worlds.new("mundo")
    scn.world.use_nodes = True
    bg = scn.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.16, 0.17, 0.19, 1)
    bg.inputs["Strength"].default_value = 0.55

    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    centro = (mn + mx) / 2
    radio = (mx - mn).length / 2

    mira = bpy.data.objects.new("mira", None)
    mira.location = centro
    scn.collection.objects.link(mira)
    extras = [mira]

    # Estudio de 3 luces: clave, relleno y contraluz.
    def luz(nombre, az, el, potencia, color, tam_rel):
        d = bpy.data.lights.new(nombre, "AREA")
        d.shape = "DISK"
        d.size = radio * tam_rel
        dist = radio * 3.2
        d.energy = potencia * dist * dist
        d.color = color
        o = bpy.data.objects.new(nombre, d)
        a, e = math.radians(az), math.radians(el)
        o.location = centro + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist
        scn.collection.objects.link(o)
        c = o.constraints.new("TRACK_TO")
        c.target = mira
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        extras.append(o)
        return o

    luces = [luz("clave", -45, 48, 34.0, (1.0, 0.97, 0.92), 1.6),
             luz("relleno", 60, 18, 12.0, (0.82, 0.9, 1.0), 2.6),
             luz("contra", 160, 40, 26.0, (0.9, 0.95, 1.0), 1.4)]

    bpy.ops.mesh.primitive_plane_add(size=radio * 60, location=(centro.x, centro.y, mn.z - 0.002))
    suelo = bpy.context.active_object
    ms = bpy.data.materials.new("suelo_estudio")
    ms.use_nodes = True
    bs = ms.node_tree.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = (0.09, 0.095, 0.105, 1)
    bs.inputs["Roughness"].default_value = 0.9
    suelo.data.materials.append(ms)
    extras.append(suelo)

    cd = bpy.data.cameras.new("cam")
    cd.lens = 70
    cd.clip_end = 100000
    cam = bpy.data.objects.new("cam", cd)
    scn.collection.objects.link(cam)
    scn.camera = cam
    extras.append(cam)
    fov = 2 * math.atan(18 / cd.lens)
    dist = radio * 1.08 / math.sin(fov / 2)
    malla = _mat_malla()

    tiles = []
    carpeta_tmp = os.path.join(os.path.dirname(ruta), "_tmp_vistas")
    os.makedirs(carpeta_tmp, exist_ok=True)
    for i, (nombre, az, el) in enumerate(VISTAS):
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = centro + d * dist
        cam.rotation_euler = (centro - cam.location).to_track_quat("-Z", "Y").to_euler()
        es_malla = nombre == "Wireframe"
        scn.view_layers[0].material_override = malla if es_malla else None
        suelo.hide_render = es_malla
        r = os.path.join(carpeta_tmp, f"v{i}.png")
        scn.render.filepath = r
        bpy.ops.render.render(write_still=True)
        tiles.append((nombre, Image.open(r).convert("RGB")))
    scn.view_layers[0].material_override = None

    cab = 70
    hoja = Image.new("RGB", (tam * 3, cab + tam * 2), (18, 20, 26))
    dr = ImageDraw.Draw(hoja)
    dr.text((16, 8), titulo, fill=(61, 242, 255), font=_fuente(30))
    dr.text((18, 44), subtitulo, fill=(205, 210, 220), font=_fuente(16))
    for i, (nombre, im) in enumerate(tiles):
        x, y = (i % 3) * tam, cab + (i // 3) * tam
        hoja.paste(im, (x, y))
        dr.rectangle((x, y, x + tam - 1, y + tam - 1), outline=(44, 48, 60))
        dr.text((x + 12, y + 10), nombre, fill=(255, 255, 255), font=_fuente(20))
    hoja.save(ruta, optimize=True)
    for f in os.listdir(carpeta_tmp):
        os.remove(os.path.join(carpeta_tmp, f))
    os.rmdir(carpeta_tmp)
    for o in extras:
        bpy.data.objects.remove(o)


# --------------------------------------------------------------------------------------------------------------
# Exportación, JSON y verificación
# --------------------------------------------------------------------------------------------------------------

def exportar(objs, ruta):
    giro = Matrix.Rotation(GIRO_IMPORTACION, 4, "Z")
    for o in objs:
        o.data.transform(giro)
        o.data.update()
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH"},
        global_scale=1.0, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", bake_space_transform=False,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=False,
        add_leaf_bones=False, bake_anim=False, embed_textures=False, path_mode="RELATIVE",
    )


def _tris(me):
    return sum(len(p.vertices) - 2 for p in me.polygons)


def _calidad_malla(me):
    """Aristas abiertas (pieza sin cerrar = sin grosor) y caras con la normal hacia dentro."""
    bm = bmesh.new()
    bm.from_mesh(me)
    abiertas = sum(1 for e in bm.edges if len(e.link_faces) < 2)
    antes = [f.normal.copy() for f in bm.faces]
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    invertidas = sum(1 for f, n in zip(bm.faces, antes) if f.normal.dot(n) < 0)
    # Volumen con signo: si es negativo, la pieza entera está del revés.
    vol = bm.calc_volume(signed=True)
    bm.free()
    return abiertas, invertidas, vol


def verificar(ruta_fbx, esperado):
    """Reimporta el FBX en una escena vacía y lo compara con lo que se exportó."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta_fbx)
    res = {"piezas": {}, "ok": True, "avisos": []}
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    total = 0
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        t = _tris(o.data)
        total += t
        ab, inv, vol = _calidad_malla(o.data)
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
        res["piezas"][o.name] = {"triangulos": t, "aristas_abiertas": ab, "normales_invertidas": inv,
                                 "uv": len(o.data.uv_layers)}
        if ab:
            res["avisos"].append(f"{o.name}: {ab} aristas abiertas")
        if inv:
            res["avisos"].append(f"{o.name}: {inv} caras con la normal invertida")
        if vol <= 0:
            res["avisos"].append(f"{o.name}: volumen con signo no positivo ({vol:.4f})")
        if not o.data.uv_layers:
            res["avisos"].append(f"{o.name}: sin UV")
    d = mx - mn
    res["triangulos"] = total
    res["tamano_reimportado"] = [round(d.x, 3), round(d.y, 3), round(d.z, 3)]
    if total != esperado["triangulos"]:
        res["avisos"].append(f"triángulos {total} != {esperado['triangulos']}")
    if set(res["piezas"]) != set(esperado["piezas"]):
        res["avisos"].append(f"piezas distintas: {sorted(res['piezas'])}")
    for a, b in zip(res["tamano_reimportado"], esperado["tamano"]):
        if abs(a - b) > 0.02 + 0.002 * b:
            res["avisos"].append(f"tamaño reimportado {res['tamano_reimportado']} != {esperado['tamano']}")
            break
    res["ok"] = not res["avisos"]
    return res


MATERIAL_ROBLOX = {
    "neon": ("Neon", "#3DF2FF"), "naranja_neon": ("Neon", "#FF7A1A"), "verde_neon": ("Neon", "#4DFF7A"),
    "rojo_neon": ("Neon", "#FF3B3B"), "azul_neon": ("Neon", "#3D7BFF"), "rosa_neon": ("Neon", "#FF4DD2"),
    "amarillo_neon": ("Neon", "#FFD23D"), "blanco_luz": ("Neon", "#F4FBFF"),
}


def construir(nombre, info, fn, con_render=True):
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)  # un modelo = una escena limpia
    scn = bpy.context.scene
    scn.unit_settings.system = "NONE"
    scn.world = bpy.data.worlds.new("mundo")
    carpeta = os.path.join(RAIZ, nombre)
    os.makedirs(carpeta, exist_ok=True)

    m = Modelo(nombre, info)
    fn(m)
    pares = m.objetos()
    objs = [o for o, _ in pares]
    mats = []
    for o, nombres in pares:
        for n in nombres:
            mt = crear_material(n, m.esc)
            o.data.materials.append(mt)
            if mt not in mats:
                mats.append(mt)

    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            mn = Vector(map(min, mn, Vector(c)))
            mx = Vector(map(max, mx, Vector(c)))
    dim = mx - mn
    radio = dim.length / 2

    desplegar(objs)
    rutas, cobertura = hornear(objs, mats, carpeta, nombre, radio)
    colores_parte = {}
    for o, nombres in pares:
        colores_parte[o.name] = spec(nombres[0])["color"]
    materiales_finales(objs, rutas, nombre)

    piezas = []
    total = 0
    for o in objs:
        t = _tris(o.data)
        total += t
        parte = o["parte"]
        if parte in MATERIAL_ROBLOX:
            mr, col = MATERIAL_ROBLOX[parte]
            extra = {"material_roblox": mr, "color": col}
        elif "neon" in parte or "luz" in parte:
            extra = {"material_roblox": "Neon", "color": colores_parte[o.name]}
        elif "cristal" in parte:
            extra = {"material_roblox": "Glass", "color": colores_parte[o.name], "transparencia": 0.45}
        elif "agua" in parte:
            extra = {"material_roblox": "Glass", "color": colores_parte[o.name], "transparencia": 0.35}
        else:
            extra = {"material_roblox": "SurfaceAppearance (atlas PBR)"}
        piezas.append({"nombre": o.name, "triangulos": t, **extra})

    ancho, fondo, alto = round(dim.x, 2), round(dim.y, 2), round(dim.z, 2)
    presupuesto = PRESUPUESTOS[info["categoria"]]
    if con_render:
        sub = (f"#{info['num']:03d} · {info['zona']} · {total} tris (máx. {presupuesto}) · "
               f"{ancho} × {fondo} × {alto} studs (ancho × fondo × alto) · {len(objs)} piezas")
        turnaround(objs, os.path.join(carpeta, f"{nombre}_turnaround.png"), nombre, sub)

    ruta_fbx = os.path.join(carpeta, f"{nombre}.fbx")
    exportar(objs, ruta_fbx)

    # Anclajes en coordenadas de Roblox (tras el giro de importación): X = -x, Y = z, Z = y.
    anclajes = {k: [round(-v[0], 3), round(v[2], 3), round(v[1], 3)] for k, v in m.anclajes.items()}
    ob = info["objetivo"]
    datos = {
        "nombre": nombre,
        "numero": info["num"],
        "zona": info["zona"],
        "categoria": info["categoria"],
        "triangulos": total,
        "presupuesto_triangulos": presupuesto,
        "dentro_de_presupuesto": total <= presupuesto,
        "tamano_studs": {"ancho_x": ancho, "alto_y": alto, "fondo_z": fondo},
        "tamano_objetivo_studs": {"ancho_x": ob[0], "alto_y": ob[2], "fondo_z": ob[1]},
        "piezas": piezas,
        "texturas": {k: os.path.basename(v) for k, v in rutas.items()},
        "atlas": f"{TAM_ATLAS}x{TAM_ATLAS}",
        "cobertura_atlas": round(cobertura, 3),
        "exportacion": {"escala": "1 unidad = 1 stud", "apply_scalings": "FBX_SCALE_ALL",
                        "giro_importacion": "180° en el eje Y (vertical de Roblox); el frente queda en -Z"},
        "anclajes_roblox": anclajes,
        "notas": m.notas,
    }
    ver = verificar(ruta_fbx, {"triangulos": total, "piezas": [o_["nombre"] for o_ in piezas],
                               "tamano": [ancho, fondo, alto]})
    datos["verificacion_fbx"] = ver
    with open(os.path.join(carpeta, f"{nombre}.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

    estado = "OK" if ver["ok"] and total <= presupuesto else "REVISAR"
    print(f"[{estado}] {nombre}: {total} tris (máx. {presupuesto}), {ancho}x{fondo}x{alto} "
          f"(objetivo {ob[0]}x{ob[1]}x{ob[2]}), atlas {cobertura:.0%}, {time.time() - t0:.0f}s "
          f"{'; '.join(ver['avisos'])}", flush=True)
    return datos
