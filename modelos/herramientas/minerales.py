"""
Los 100 minerales del juego (7 rarezas), generados con Blender sin pantalla.

Por cada mineral:
  1. Formas (`minerales_formas.py`): piezas cerradas en studs (1 unidad de Blender = 1 stud de Roblox).
  2. ALTA: cada pieza remallada por voxel + relieve + pintura PBR por vértice (`minerales_pintura.py`).
  3. BAJA (la del juego): la forma limpia (cristales) o la ALTA simplificada (rocas). Máximo 3.000 triángulos.
  4. Atlas UV común 1024x1024 y horneado ALTA -> BAJA de: color (con oclusión), normales, rugosidad, metal y
     emisión (si brilla).
  5. Turnaround de 6 vistas (Frente, 3/4, Lateral, 3/4 trasera, Arriba y Malla).
  6. GIRO_IMPORTACION (180° sobre el eje vertical, que es la Y de Roblox) y FBX con Apply Scalings = FBX All.
  7. JSON con triángulos, tamaño, rareza, valor y cómo montarlo en Studio.

Uso (con el bpy de herramientas/requirements.txt):
    python modelos/herramientas/minerales.py --ronda 1            # minerales 1-10
    python modelos/herramientas/minerales.py --solo pirita,basalto [--rapido]
    python modelos/herramientas/minerales.py --catalogo           # junta los JSON en catalogo.json + Luau
"""

import argparse
import json
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import comun as c  # noqa: E402
import minerales_datos as D  # noqa: E402
import minerales_formas as F  # noqa: E402
import minerales_pintura as P  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "minerales"))
LIMITE_TRIS = 3000
# Triángulos que se buscan por rareza (los comunes salen a montones: más ligeros para móvil). Límite duro: 3.000.
OBJETIVO_TRIS = {"Común": 1600, "Poco común": 2000, "Raro": 2400, "Épico": 2800, "Legendario": 2850,
                 "Mítico": 2900, "Celestial": 2900}
TAM_TEXTURA = 1024
GIRO_IMPORTACION = Matrix.Rotation(math.pi, 4, "Z")  # 180° sobre el vertical (Y de Roblox = Z de Blender)

VISTAS = [("Frente", 0, 10), ("3/4", -45, 24), ("Lateral", -90, 8), ("3/4 trasera", 135, 24), ("Arriba", 15, 78)]

# Aspecto de cada grupo en el render (lo más parecido a como se verá en Studio).
RENDER_GRUPO = {
    "": dict(transmision=0.0, emision=2.5),
    "orbita": dict(transmision=0.0, emision=3.0),
    "interior": dict(transmision=0.0, emision=3.0),
    "cristal": dict(transmision=0.82, emision=2.0),
    "neon": dict(transmision=0.0, emision=5.0),
}


# --------------------------------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------------------------------


def _obj_desde_bm(nombre, bm, coleccion=None):
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    obj = bpy.data.objects.new(nombre, malla)
    (coleccion or bpy.context.scene.collection).objects.link(obj)
    return obj


def _activar(obj, solo=True):
    if solo:
        bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def _area(bm):
    return sum(f.calc_area() for f in bm.faces)


def _remallar(obj, voxel):
    mod = obj.modifiers.new("remallado", "REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = voxel
    mod.adaptivity = 0.0
    c.aplicar_modificadores(obj)


def _hueco(obj, centro, radios):
    """Vacía el interior de la cáscara de una geoda con un booleano."""
    bm = F.icosfera(1.0, 4)
    bmesh.ops.scale(bm, vec=radios, verts=bm.verts)
    bmesh.ops.translate(bm, vec=centro, verts=bm.verts)
    cortador = _obj_desde_bm("cortador", bm)
    bm.free()
    mod = obj.modifiers.new("hueco", "BOOLEAN")
    mod.operation = "DIFFERENCE"
    mod.object = cortador
    mod.solver = "EXACT"
    c.aplicar_modificadores(obj)
    bpy.data.objects.remove(cortador)


def _decimar(obj, objetivo):
    actual = _tris(obj)
    if actual <= objetivo:
        return
    mod = obj.modifiers.new("simplificar", "DECIMATE")
    mod.ratio = objetivo / actual
    mod.use_collapse_triangulate = True
    c.aplicar_modificadores(obj)


def _triangular(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    bm.to_mesh(obj.data)
    bm.free()


def _material_grupo(grupo):
    nombre = f"grupo_{grupo or 'cuerpo'}"
    m = bpy.data.materials.get(nombre)
    if m is None:
        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
    return m


# --------------------------------------------------------------------------------------------------------------
# ALTA y BAJA de cada pieza
# --------------------------------------------------------------------------------------------------------------


def preparar_piezas(d, rapido):
    rnd = random.Random(d["semilla"])
    piezas = F.construir_piezas(d, rnd)
    # Tamaño y centro del conjunto (para escalar los ruidos y los patrones).
    mn = Vector((1e9, 1e9, 1e9))
    mx = -mn
    for pz in piezas:
        a, b = F.caja(pz.bm)
        mn = Vector(map(min, mn, a))
        mx = Vector(map(max, mx, b))
    S = max(mx - mn)
    centro = (mn + mx) / 2
    semilla = Vector((rnd.uniform(0, 100), rnd.uniform(0, 100), rnd.uniform(0, 100)))
    altas, bajas = [], []
    for i, pz in enumerate(piezas):
        nombre = f"{d['id']}_{i}_{pz.nombre}"
        alta = _obj_desde_bm(nombre + "_alta", pz.bm)
        if pz.relieve and pz.relieve.get("hueco"):
            _hueco(alta, pz.relieve["hueco_c"], [r * pz.relieve["hueco"] for r in pz.relieve["hueco_r"]])
        voxel = S / (60 if rapido else 120)
        if pz.voxel:
            voxel = min(voxel, pz.voxel)
        # Que la ALTA no pase de ~450.000 caras.
        voxel = max(voxel, math.sqrt(_area(pz.bm) / 450000.0), S / 600)
        _remallar(alta, voxel)
        bm = bmesh.new()
        bm.from_mesh(alta.data)
        cav = P.relieve(bm, pz.relieve, S, semilla, pz.base_plana)
        P.pintar(bm, pz.pint, S, semilla, centro, mn.z, mx.z, cav)
        bm.to_mesh(alta.data)
        bm.free()
        alta["grupo"] = pz.grupo
        altas.append(alta)
        if pz.baja == "limpia":
            baja = _obj_desde_bm(nombre, pz.bm)
            _triangular(baja)
        else:
            baja = alta.copy()
            baja.data = alta.data.copy()
            baja.name = nombre
            bpy.context.scene.collection.objects.link(baja)
        baja["grupo"] = pz.grupo
        baja["suave"] = pz.suave
        baja["modo"] = pz.baja
        baja["tris_fijos"] = pz.tris or 0
        bajas.append(baja)
        pz.bm.free()
    repartir_triangulos(bajas, OBJETIVO_TRIS[d["rareza"]])
    for b in bajas:
        for att in list(b.data.color_attributes):
            b.data.color_attributes.remove(att)
        for nombre_att in ("rug", "met"):
            if nombre_att in b.data.attributes:
                b.data.attributes.remove(b.data.attributes[nombre_att])
        sombrear(b)
    return altas, bajas, S


def repartir_triangulos(bajas, objetivo):
    """Las piezas limpias cuentan lo que tienen; el resto del presupuesto se reparte entre las rocas."""
    fijos = sum(_tris(b) for b in bajas if b["modo"] == "limpia")
    fijos_dec = sum(b["tris_fijos"] for b in bajas if b["modo"] == "decimar" and b["tris_fijos"])
    libres = [b for b in bajas if b["modo"] == "decimar" and not b["tris_fijos"]]
    resto = objetivo - fijos - fijos_dec
    if fijos + fijos_dec > LIMITE_TRIS - 150:
        raise RuntimeError(f"las piezas fijas ya suman {fijos + fijos_dec} triángulos")
    if libres and resto < 250 * len(libres):
        raise RuntimeError(f"solo quedan {resto} triángulos para {len(libres)} rocas")
    areas = []
    for b in libres:
        areas.append(sum(p.area for p in b.data.polygons))
    total_area = sum(areas) or 1.0
    for b in bajas:
        if b["modo"] != "decimar":
            continue
        if b["tris_fijos"]:
            _decimar(b, b["tris_fijos"])
    for b, a in zip(libres, areas):
        _decimar(b, int(resto * a / total_area))


def sombrear(b):
    if b["modo"] == "decimar":
        if b["suave"]:
            for p in b.data.polygons:
                p.use_smooth = True
        else:
            c.sombreado_suave(b, angulo=55)
    elif b["suave"]:
        for p in b.data.polygons:
            p.use_smooth = True
    else:
        for p in b.data.polygons:
            p.use_smooth = False


# --------------------------------------------------------------------------------------------------------------
# Atlas y horneado
# --------------------------------------------------------------------------------------------------------------


def unir_por_grupo(objetos, sufijo):
    grupos = {}
    for o in objetos:
        grupos.setdefault(o["grupo"], []).append(o)
    res = {}
    for g, lista in grupos.items():
        bpy.ops.object.select_all(action="DESELECT")
        for o in lista:
            o.select_set(True)
        bpy.context.view_layer.objects.active = lista[0]
        if len(lista) > 1:
            bpy.ops.object.join()
        obj = bpy.context.view_layer.objects.active
        obj.name = f"g{sufijo}_{g or 'cuerpo'}"
        obj["grupo"] = g
        res[g] = obj
    return res


def atlas(bajas_por_grupo, margen=0.004):
    """Un solo atlas UV para todas las piezas: se unen, se despliegan, se empaquetan y se vuelven a separar."""
    lista = list(bajas_por_grupo.values())
    for o in lista:
        o.data.materials.clear()
        o.data.materials.append(_material_grupo(o["grupo"]))
    bpy.ops.object.select_all(action="DESELECT")
    for o in lista:
        o.select_set(True)
    bpy.context.view_layer.objects.active = lista[0]
    if len(lista) > 1:
        bpy.ops.object.join()
    todo = bpy.context.view_layer.objects.active
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(62), island_margin=margen, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(rotate=True, margin=margen)
    bpy.ops.object.mode_set(mode="OBJECT")
    _activar(todo)
    if len(todo.data.materials) > 1:
        bpy.ops.mesh.separate(type="MATERIAL")
    res = {}
    for o in bpy.context.selected_objects:
        mat = o.data.materials[0] if len(o.data.materials) == 1 else None
        if mat is None:
            # tras separar, cada objeto conserva todas las ranuras; la que usa es la de sus caras
            idx = o.data.polygons[0].material_index
            mat = o.data.materials[idx]
        g = "" if mat.name == "grupo_cuerpo" else mat.name[len("grupo_"):]
        o["grupo"] = g
        res[g] = o
    return res


def _imagen(nombre, fondo, tam):
    img = bpy.data.images.new(nombre, tam, tam, alpha=True, float_buffer=True)
    img.colorspace_settings.name = "Non-Color"
    img.generated_color = (*fondo, 1.0)
    return img


def _destino(baja, img):
    for slot in baja.material_slots:
        nt = slot.material.node_tree
        n = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "destino"
        n.image = img
        nt.nodes.active = n


def _material_atributo():
    m = bpy.data.materials.get("hornear_atributo")
    if m:
        return m
    m = bpy.data.materials.new("hornear_atributo")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    att = nt.nodes.new("ShaderNodeAttribute")
    att.name = "att"
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = "em"
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    return m


def _atributo(nombre, salida):
    m = _material_atributo()
    nt = m.node_tree
    att = nt.nodes["att"]
    att.attribute_name = nombre
    att.attribute_type = "GEOMETRY"
    for l in list(nt.links):
        if l.to_node.name == "em":
            nt.links.remove(l)
    nt.links.new(att.outputs[salida], nt.nodes["em"].inputs["Color"])


def hornear_mapas(altas, bajas, S, tam, rapido):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.render.bake.use_clear = False
    scn.render.bake.margin = 6
    scn.render.bake.margin_type = "EXTEND"
    mat_att = _material_atributo()
    for a in altas.values():
        a.data.materials.clear()
        a.data.materials.append(mat_att)
    todos = list(altas.values()) + list(bajas.values())

    def bake(tipo, grupos, ocultar_cristal=False, **kw):
        for g in grupos:
            if g not in bajas:
                continue
            for o in todos:
                o.hide_render = True
            for a in altas.values():
                a.hide_render = ocultar_cristal and a["grupo"] == "cristal" and g != "cristal"
            altas[g].hide_render = False
            bajas[g].hide_render = False
            bpy.ops.object.select_all(action="DESELECT")
            altas[g].select_set(True)
            _activar(bajas[g], solo=False)
            bpy.ops.object.bake(type=tipo, use_selected_to_active=True, cage_extrusion=0.03 * S,
                                max_ray_distance=0.09 * S, margin=6, use_clear=False, **kw)

    mapas = {}
    grupos = list(bajas.keys())
    scn.cycles.samples = 1
    for nombre, att, salida, fondo in (("color", "col", "Color", (0.5, 0.5, 0.5)),
                                       ("rugosidad", "rug", "Fac", (0.8, 0.8, 0.8)),
                                       ("metal", "met", "Fac", (0.0, 0.0, 0.0)),
                                       ("emision", "emi", "Color", (0.0, 0.0, 0.0))):
        _atributo(att, salida)
        img = _imagen(f"tex_{nombre}", fondo, tam)
        for b in bajas.values():
            _destino(b, img)
        bake("EMIT", grupos)
        mapas[nombre] = img
    img = _imagen("tex_normal", (0.5, 0.5, 1.0), tam)
    for b in bajas.values():
        _destino(b, img)
    bake("NORMAL", grupos, normal_space="TANGENT")
    mapas["normal"] = img
    # Oclusión: solo en lo opaco (los cristales no se oscurecen ni hacen sombra a lo de dentro).
    scn.cycles.samples = 8 if rapido else 24
    scn.world.light_settings.distance = 0.12 * S
    img = _imagen("tex_ao", (1.0, 1.0, 1.0), tam)
    for b in bajas.values():
        _destino(b, img)
    bake("AO", [g for g in grupos if g in ("", "orbita", "interior")], ocultar_cristal=True)
    mapas["ao"] = img
    for o in todos:
        o.hide_render = False
    return mapas


def _pixeles(img):
    w, h = img.size
    buf = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(buf)
    return buf.reshape(h, w, 4)[::-1]  # Blender guarda de abajo arriba


def _a_srgb(x):
    x = np.clip(x, 0, 1)
    return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)


def guardar_mapas(mapas, carpeta, ident):
    """Guarda los PNG del atlas. Devuelve {mapa: ruta relativa} (sin emisión si no brilla nada)."""
    os.makedirs(os.path.join(carpeta, "texturas"), exist_ok=True)
    ao = _pixeles(mapas["ao"])[..., 0]
    color = _pixeles(mapas["color"])[..., :3] * (1.0 - 0.7 * (1.0 - np.clip(ao, 0, 1)) ** 1.3)[..., None]
    salida = {}

    def guardar(nombre, arr, modo):
        ruta = os.path.join("texturas", f"{ident}_{nombre}.png")
        arr8 = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)
        Image.fromarray(arr8, modo).save(os.path.join(carpeta, ruta), optimize=True)
        salida[nombre] = ruta

    guardar("color", _a_srgb(color), "RGB")
    guardar("normal", _pixeles(mapas["normal"])[..., :3], "RGB")
    guardar("rugosidad", _pixeles(mapas["rugosidad"])[..., 0], "L")
    guardar("metal", _pixeles(mapas["metal"])[..., 0], "L")
    emi = _pixeles(mapas["emision"])[..., :3]
    if emi.max() > 0.04:
        guardar("emision", _a_srgb(emi), "RGB")
    return salida


def materiales_finales(bajas, carpeta, texturas):
    imgs = {}
    for k, ruta in texturas.items():
        img = bpy.data.images.load(os.path.join(carpeta, ruta), check_existing=False)
        img.colorspace_settings.name = "sRGB" if k in ("color", "emision") else "Non-Color"
        imgs[k] = img
    for g, b in bajas.items():
        cfg = RENDER_GRUPO.get(g, RENDER_GRUPO[""])
        mat = bpy.data.materials.new(f"{b.name}_mat")
        mat.use_nodes = True
        nt = mat.node_tree
        bs = nt.nodes["Principled BSDF"]

        def tex(k):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = imgs[k]
            return n

        nt.links.new(tex("color").outputs["Color"], bs.inputs["Base Color"])
        nt.links.new(tex("rugosidad").outputs["Color"], bs.inputs["Roughness"])
        nt.links.new(tex("metal").outputs["Color"], bs.inputs["Metallic"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tex("normal").outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
        if "emision" in imgs:
            nt.links.new(tex("emision").outputs["Color"], bs.inputs["Emission Color"])
            bs.inputs["Emission Strength"].default_value = cfg["emision"]
        if cfg["transmision"]:
            bs.inputs["Transmission Weight"].default_value = cfg["transmision"]
            bs.inputs["IOR"].default_value = 1.5
        b.data.materials.clear()
        b.data.materials.append(mat)


# --------------------------------------------------------------------------------------------------------------
# Render, exportación y JSON
# --------------------------------------------------------------------------------------------------------------


def luz_mineral(d, S, mn, mx):
    """PointLight del color del brillo (la misma que se recomienda en Studio)."""
    if not d.get("luz"):
        return None
    l = bpy.data.lights.new("luz_mineral", "POINT")
    l.color = c.srgb(d["luz"])
    l.energy = 60 * S * S * d.get("luz_fuerza", 1.0)
    l.shadow_soft_size = 0.2 * S
    o = bpy.data.objects.new("luz_mineral", l)
    o.location = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z + (mx.z - mn.z) * 0.55)
    bpy.context.scene.collection.objects.link(o)
    return o


def nombre_parte(ident, g):
    return ident if not g else f"{ident}_{g}"


def turnaround(d, rutas, salida, info):
    tam = Image.open(rutas[0][1]).size[0]
    cab = 104
    hoja = Image.new("RGB", (tam * 3, cab + tam * 2), (14, 16, 22))
    dr = ImageDraw.Draw(hoja)
    color = D.RAREZAS[d["rareza"]]["color_hud"]
    dr.rectangle((0, 0, tam * 3, 6), fill=color)
    dr.text((16, 16), d["titulo"], fill=color, font=c._fuente(30))
    dr.text((16, 56), f"#{d['n']:03d} {d['id']}  ·  {d['rareza']}  ·  valor {d['valor']}  ·  {info['tris']} triángulos"
            f"  ·  {info['tam'][0]:.1f} × {info['tam'][1]:.1f} × {info['tam'][2]:.1f} studs",
            fill=(215, 220, 230), font=c._fuente(17, negrita=False))
    dr.text((16, 80), "Partes: " + ", ".join(f"{p['nombre']} ({p['triangulos']})" for p in info["partes"]),
            fill=(150, 158, 175), font=c._fuente(14, negrita=False))
    for i, (nombre, ruta) in enumerate(rutas):
        x, y = (i % 3) * tam, cab + (i // 3) * tam
        hoja.paste(Image.open(ruta).convert("RGB"), (x, y))
        dr.rectangle((x, y, x + tam - 1, y + tam - 1), outline=(36, 40, 52))
        dr.text((x + 10, y + 8), "Malla (wireframe)" if nombre == "Malla" else nombre, fill=(255, 255, 255),
                font=c._fuente(16))
    hoja.save(salida, quality=92)
    return salida


def roblox_parte(d, g, b):
    """Cómo montar cada parte en Studio."""
    cfg = d.get("roblox", {}).get(g, {})
    if g == "cristal":
        base = dict(Material="Glass", Transparency=cfg.get("transparencia", 0.35), Color=cfg.get("color"),
                    SurfaceAppearance="opcional (ColorMap+NormalMap); sin ella se ve el cristal de Roblox")
    elif g == "neon":
        base = dict(Material="Neon", Color=cfg.get("color", d.get("luz")),
                    SurfaceAppearance="no (el Neon no la usa); el color de la emisión está en el atlas")
    else:
        base = dict(Material=cfg.get("material", d.get("material", "Rock")),
                    SurfaceAppearance="ColorMap, NormalMap, RoughnessMap, MetalnessMap")
    if g == "orbita":
        base["Animacion"] = cfg.get("anim", "girar en Y alrededor del centro del mineral (una vuelta cada ~10 s) "
                                            "y subir y bajar 0,2 studs, en el cliente")
    if cfg.get("anim") and g != "orbita":
        base["Animacion"] = cfg["anim"]
    return {k: v for k, v in base.items() if v is not None}


def construir(d, rapido=False, incrustar=False):
    t0 = time.time()
    ident = d["id"]
    carpeta = os.path.join(RAIZ, ident)
    os.makedirs(carpeta, exist_ok=True)
    c.escena_vacia()
    scn = bpy.context.scene
    hilos = int(os.environ.get("MIN_HILOS", "0"))
    if hilos:
        scn.render.threads_mode = "FIXED"
        scn.render.threads = hilos
    altas, bajas, S = preparar_piezas(d, rapido)

    # Centrar: base en z = 0 y centro en XY (como se colocan en Studio).
    mn, mx = c.caja_limite(bajas)
    T = Matrix.Translation((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))
    for o in altas + bajas:
        o.data.transform(T)

    altas_g = unir_por_grupo(altas, "A")
    bajas_g = unir_por_grupo(bajas, "B")
    bajas_g = atlas(bajas_g)
    tam = 256 if rapido else TAM_TEXTURA
    mapas = hornear_mapas(altas_g, bajas_g, S, tam, rapido)
    texturas = guardar_mapas(mapas, carpeta, ident)
    for a in altas_g.values():
        bpy.data.objects.remove(a)
    materiales_finales(bajas_g, carpeta, texturas)

    # Nombres finales de las MeshPart.
    orden = sorted(bajas_g.keys(), key=lambda g: ["", "cristal", "interior", "neon", "orbita"].index(g)
                   if g in ("", "cristal", "interior", "neon", "orbita") else 9)
    partes = []
    for g in orden:
        b = bajas_g[g]
        b.name = nombre_parte(ident, g)
        b.data.name = b.name
        partes.append(b)
    tris = sum(_tris(b) for b in partes)
    assert tris <= LIMITE_TRIS, f"{ident}: {tris} triángulos"
    mn, mx = c.caja_limite(partes)
    dim = mx - mn

    # Render.
    c.preparar_estudio(mundo=0.6)
    luz = luz_mineral(d, S, mn, mx)
    tmp = os.path.join(RAIZ, "_render_tmp", ident)
    rutas = c.renderizar_vistas(partes, tmp, VISTAS, tam=240 if rapido else 380, muestras=12 if rapido else 40,
                                margen=1.08, prefijo="")
    info = dict(tris=tris, tam=[round(dim.x, 2), round(dim.y, 2), round(dim.z, 2)],
                partes=[dict(nombre=b.name, triangulos=_tris(b)) for b in partes])
    turnaround(d, rutas, os.path.join(carpeta, "turnaround.jpg"), info)

    # GIRO_IMPORTACION y FBX.
    if luz:
        bpy.data.objects.remove(luz)
    c.eliminar_estudio()
    for b in partes:
        b.data.transform(GIRO_IMPORTACION)
    exportar(os.path.join(carpeta, f"{ident}.fbx"), partes, incrustar)

    rar = D.RAREZAS[d["rareza"]]
    datos = {
        "id": ident,
        "numero": d["n"],
        "nombre": d["titulo"],
        "descripcion": d["desc"],
        "rareza": d["rareza"],
        "color_hud": rar["color_hud"],
        "aparicion_rareza_pct": rar["pct"],
        "aparicion_pct": round(rar["pct"] / rar["cantidad"], 4),
        "valor": d["valor"],
        "triangulos": tris,
        "tamano_studs": info["tam"],
        "partes": [dict(nombre=b.name, triangulos=_tris(b), **roblox_parte(d, b.name[len(ident) + 1:]
                                                                           if b.name != ident else "", b))
                   for b in partes],
        "texturas": {k: v.replace(os.sep, "/") for k, v in texturas.items()},
        "atlas": f"{TAM_TEXTURA}x{TAM_TEXTURA}",
        "luz_recomendada": (f"PointLight {d['luz']}, Brightness {d.get('luz_brillo', 1.5)}, Range "
                            f"{round(max(8, S * 3.5))}" if d.get("luz") else None),
        "escala": "1 unidad de Blender = 1 stud (FBX con Apply Scalings = FBX All)",
        "giro_importacion": "180° en el eje vertical (Y de Roblox) aplicado antes de exportar",
    }
    with open(os.path.join(carpeta, f"{ident}.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    print(f"[ok] {d['n']:03d} {ident}: {tris} tri, {dim.x:.1f}x{dim.y:.1f}x{dim.z:.1f} st, "
          f"{time.time() - t0:.0f} s", flush=True)
    return rutas


def exportar(ruta, objetos, incrustar):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta,
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,
        axis_forward="Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        add_leaf_bones=False,
        bake_anim=False,
        embed_textures=incrustar,
        path_mode="COPY" if incrustar else "RELATIVE",
    )


# --------------------------------------------------------------------------------------------------------------
# Hoja de la ronda y catálogo
# --------------------------------------------------------------------------------------------------------------


def hoja_ronda(lista, ronda):
    tam = 380
    cab = 70
    filas = (len(lista) + 4) // 5
    hoja = Image.new("RGB", (tam * 5, cab + filas * (tam + 54)), (14, 16, 22))
    dr = ImageDraw.Draw(hoja)
    dr.text((16, 18), f"Minerales — ronda {ronda} ({lista[0]['n']}–{lista[-1]['n']})", fill=(255, 214, 102),
            font=c._fuente(28))
    for i, d in enumerate(lista):
        x, y = (i % 5) * tam, cab + (i // 5) * (tam + 54)
        ruta = os.path.join(RAIZ, "_render_tmp", d["id"], "3-4.png")
        if os.path.exists(ruta):
            hoja.paste(Image.open(ruta).convert("RGB").resize((tam, tam)), (x, y))
        color = D.RAREZAS[d["rareza"]]["color_hud"]
        js = os.path.join(RAIZ, d["id"], f"{d['id']}.json")
        tris = json.load(open(js))["triangulos"] if os.path.exists(js) else "?"
        dr.text((x + 10, y + tam + 4), f"{d['n']}. {d['titulo']}", fill=color, font=c._fuente(17))
        dr.text((x + 10, y + tam + 28), f"{d['rareza']} · {tris} tri · valor {d['valor']}", fill=(180, 186, 200),
                font=c._fuente(14, negrita=False))
    os.makedirs(os.path.join(RAIZ, "rondas"), exist_ok=True)
    ruta = os.path.join(RAIZ, "rondas", f"ronda_{ronda:02d}.jpg")
    hoja.save(ruta, quality=90)
    print("[ok] hoja:", ruta)


def catalogo():
    lista = []
    for d in D.MINERALES:
        js = os.path.join(RAIZ, d["id"], f"{d['id']}.json")
        if os.path.exists(js):
            lista.append(json.load(open(js, encoding="utf-8")))
    with open(os.path.join(RAIZ, "catalogo.json"), "w", encoding="utf-8") as f:
        json.dump(dict(rarezas=D.RAREZAS, minerales=lista), f, indent=2, ensure_ascii=False)
    print(f"[ok] catálogo: {len(lista)} minerales")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ronda", type=int, default=0)
    ap.add_argument("--solo", default="")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--incrustar", action="store_true", help="incrustar las texturas en el FBX")
    ap.add_argument("--catalogo", action="store_true")
    ap.add_argument("--hoja", action="store_true", help="solo montar la hoja de la ronda")
    a = ap.parse_args()
    if a.catalogo:
        catalogo()
        return
    if a.solo:
        ids = a.solo.split(",")
        lista = [d for d in D.MINERALES if d["id"] in ids]
    else:
        lista = [d for d in D.MINERALES if (d["n"] - 1) // 10 + 1 == a.ronda]
    fallos = []
    if not a.hoja:
        for d in lista:
            try:
                construir(d, a.rapido, a.incrustar)
            except Exception:  # se sigue con el resto y se informa al final
                import traceback
                traceback.print_exc()
                fallos.append(d["id"])
    if a.ronda:
        hoja_ronda(lista, a.ronda)
    if fallos:
        print("[FALLO]", ",".join(fallos))
        sys.exit(1)


if __name__ == "__main__":
    main()
