"""
Dragón Leviatán (boss final): montaje en Blender, horneado del atlas 4096, renders, FBX y JSON.

Antes hay que mallar el cuerpo con dragon_mallas.py (genera la caché de mallas de alta y baja).

Uso:
    python modelos/herramientas/dragon_leviatan.py --cache bestias/dragon_leviatan/_cache \
        --salida bestias/dragon_leviatan [--fase previa|todo] [--ronda N] [--tex 4096]

  previa: monta las piezas con un material de arcilla y renderiza las vistas (rápido, para revisar formas).
  todo:   UV del atlas, horneado (color, normales, rugosidad, metal, emisión), turnaround de 8 vistas,
          prueba de silueta, exportación FBX (con GIRO_IMPORTACION), reimportación de control, JSON y script
          de montaje para Studio.

Coordenadas: se modela en studs (1 unidad = 1 stud), Z arriba y el dragón mirando a -Y. Al exportar se gira 180°
alrededor del eje vertical (GIRO_IMPORTACION, que es el eje Y de Roblox) y los ejes por defecto del FBX de Blender
(adelante -Z, arriba Y) lo dejan mirando a -Z en Roblox, que es su "delante".
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
import bmesh  # noqa: E402,F401
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import dragon_anatomia as A  # noqa: E402
import dragon_cuerpo as C  # noqa: E402
import dragon_items as it  # noqa: E402
import dragon_montaje as M  # noqa: E402
import dragon_sdf as s  # noqa: E402

NOMBRE = "dragon_leviatan"
GIRO_IMPORTACION = 180.0  # grados alrededor del eje vertical antes de exportar
ESTUDIO = 0.28  # metros por stud (conversión del importador de Roblox)
FUERZA_EMISION = 3.0  # el mapa de emisión va de 0 a 1; en el render se multiplica por esto

# Orden del encargo (25 piezas del rig)
PIEZAS = [
    "Torso", "Cuello_Base", "Cuello_Medio", "Cuello_Superior", "Cabeza", "Mandibula",
    "Ala_Izq_Hombro", "Ala_Izq_Antebrazo", "Ala_Izq_Mano", "Ala_Der_Hombro", "Ala_Der_Antebrazo", "Ala_Der_Mano",
    "Pata_Del_Izq_Muslo", "Pata_Del_Izq_Garra", "Pata_Del_Der_Muslo", "Pata_Del_Der_Garra",
    "Pata_Tras_Izq_Muslo", "Pata_Tras_Izq_Tibia", "Pata_Tras_Der_Muslo", "Pata_Tras_Der_Tibia",
    "Cola_Base", "Cola_Media", "Cola_Punta", "Cresta_Dorsal", "Cornamenta",
]
PADRES = {n: C.DEFS[n].padre for n in C.DEFS}
PADRES["Cresta_Dorsal"] = "Torso"
PADRES["Cornamenta"] = "Cabeza"

# Puntos de montaje (cubos de 0,3): solo para la cría domesticada (el boss no lleva jinetes)
MONTAJES = {
    "Montura_Cria_Piloto": ("Cuello_Medio", None),
    "Montura_Cria_Pasajero": ("Torso", None),
    "Agarre_Cuello_Izq": ("Cuello_Medio", None),
    "Agarre_Cuello_Der": ("Cuello_Medio", None),
    "Punto_Aliento": ("Cabeza", Vector((0.0, -27.2, 8.45))),
}

# Prioridad de resolución en el atlas (escala lineal de las islas UV)
PRIORIDAD = {
    "Cabeza": 1.75, "Mandibula": 1.7, "Cornamenta": 1.3, "Torso": 1.2, "Cola_Punta": 1.45,
    "Pata_Del_Izq_Garra": 1.3, "Pata_Del_Der_Garra": 1.3, "Pata_Tras_Izq_Tibia": 1.25, "Pata_Tras_Der_Tibia": 1.25,
    "Cuello_Base": 1.1, "Cuello_Medio": 1.05, "Cuello_Superior": 1.1, "Cresta_Dorsal": 1.0,
    "Ala_Izq_Mano": 0.8, "Ala_Der_Mano": 0.8, "Ala_Izq_Antebrazo": 0.8, "Ala_Der_Antebrazo": 0.8,
}

# --------------------------------------------------------------------------------------------------------------
# Utilidades de Blender
# --------------------------------------------------------------------------------------------------------------


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.world = bpy.data.worlds.new("mundo")
    return scn


def malla_obj(nombre, v, f, coleccion=None):
    v = np.asarray(v, dtype=np.float32)
    f = np.asarray(f, dtype=np.int32)
    me = bpy.data.meshes.new(nombre)
    me.vertices.add(len(v))
    me.vertices.foreach_set("co", v.ravel())
    me.loops.add(len(f) * 3)
    me.loops.foreach_set("vertex_index", f.ravel())
    me.polygons.add(len(f))
    me.polygons.foreach_set("loop_start", np.arange(0, len(f) * 3, 3, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)
    o = bpy.data.objects.new(nombre, me)
    (coleccion or bpy.context.scene.collection).objects.link(o)
    return o


def poner_atributos(o, col, rme, emi):
    me = o.data
    for nombre, datos in (("col", col), ("rme", rme), ("emi", emi)):
        a = me.color_attributes.new(nombre, "FLOAT_COLOR", "POINT")
        rgba = np.ones((len(datos), 4), dtype=np.float32)
        rgba[:, :3] = datos
        a.data.foreach_set("color", rgba.ravel())


def leer_malla(o):
    me = o.data
    v = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", v)
    me.calc_loop_triangles()
    t = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", t)
    return v.reshape(-1, 3).astype(np.float64), t.reshape(-1, 3)


def activar(o):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = o
    o.select_set(True)


def aplicar_mods(o):
    activar(o)
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)


def diezmar(o, objetivo):
    n = sum(len(p.vertices) - 2 for p in o.data.polygons)
    if n <= objetivo:
        return
    m = o.modifiers.new("diezmar", "DECIMATE")
    m.decimate_type = "COLLAPSE"
    m.ratio = objetivo / n
    m.use_collapse_triangulate = True
    aplicar_mods(o)


def sombreado(o, angulo=48):
    for p in o.data.polygons:
        p.use_smooth = True
    activar(o)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(angulo))
    aplicar_mods(o)


def triangulos(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def material_atributos(nombre):
    """Material de la malla alta: lee col/rme/emi de los atributos (para previsualizar y para hornear)."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.name = "PBR"
    ac = nt.nodes.new("ShaderNodeAttribute")
    ac.attribute_name = "col"
    ac.name = "a_col"
    ar = nt.nodes.new("ShaderNodeAttribute")
    ar.attribute_name = "rme"
    ar.name = "a_rme"
    ae = nt.nodes.new("ShaderNodeAttribute")
    ae.attribute_name = "emi"
    ae.name = "a_emi"
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    sep.name = "sep"
    nt.links.new(ar.outputs["Color"], sep.inputs["Color"])
    nt.links.new(ac.outputs["Color"], b.inputs["Base Color"])
    nt.links.new(sep.outputs["Red"], b.inputs["Roughness"])
    nt.links.new(sep.outputs["Green"], b.inputs["Metallic"])
    nt.links.new(ae.outputs["Color"], b.inputs["Emission Color"])
    nt.links.new(sep.outputs["Blue"], b.inputs["Emission Strength"])
    # para el horneado de la emisión normalizada: emi * clamp(fuerza / FUERZA)
    div = nt.nodes.new("ShaderNodeMath")
    div.operation = "DIVIDE"
    div.use_clamp = True
    div.inputs[1].default_value = FUERZA_EMISION
    div.name = "div"
    nt.links.new(sep.outputs["Blue"], div.inputs[0])
    mix = nt.nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    mix.name = "emi_norm"
    nt.links.new(ae.outputs["Color"], mix.inputs[6])
    comb = nt.nodes.new("ShaderNodeCombineColor")
    comb.name = "comb"
    for c in ("Red", "Green", "Blue"):
        nt.links.new(div.outputs[0], comb.inputs[c])
    nt.links.new(comb.outputs["Color"], mix.inputs[7])
    em = nt.nodes.new("ShaderNodeEmission")
    em.name = "hornear"
    return mat


def canal_horneado(mat, canal):
    """Conecta el canal pedido a una emisión pura (truco para hornear valores exactos) o vuelve al PBR."""
    nt = mat.node_tree
    out = nt.nodes["Material Output"]
    em = nt.nodes["hornear"]
    for l in list(out.inputs["Surface"].links):
        nt.links.remove(l)
    for l in list(em.inputs["Color"].links):
        nt.links.remove(l)
    if canal is None:
        nt.links.new(nt.nodes["PBR"].outputs["BSDF"], out.inputs["Surface"])
        return
    fuente = {"col": nt.nodes["a_col"].outputs["Color"], "rme": nt.nodes["a_rme"].outputs["Color"],
              "emi": nt.nodes["emi_norm"].outputs[2]}[canal]
    nt.links.new(fuente, em.inputs["Color"])
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])


def material_arcilla():
    m = bpy.data.materials.get("arcilla")
    if m:
        return m
    m = bpy.data.materials.new("arcilla")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.18, 0.17, 0.17, 1)
    b.inputs["Roughness"].default_value = 0.55
    return m


# --------------------------------------------------------------------------------------------------------------
# Construcción de las piezas
# --------------------------------------------------------------------------------------------------------------


def construir(cache, rapido=False):
    """Crea, para cada pieza del rig, el objeto bajo (juego) y el alto (horneado). Devuelve dos dicts."""
    C.calcular_envolventes()
    print("[..] detalle duro (bajo)", flush=True)
    t = time.time()
    items_b = M.detalles(False)
    print(f"[..] detalle duro (alto) {time.time() - t:.0f} s", flush=True)
    items_a = M.detalles(True)
    print(f"[ok] detalle {time.time() - t:.0f} s", flush=True)
    bajos, altos = {}, {}
    col_b = bpy.data.collections.new("Dragon_bajo")
    col_a = bpy.data.collections.new("Dragon_alto")
    bpy.context.scene.collection.children.link(col_b)
    bpy.context.scene.collection.children.link(col_a)
    for nombre in PIEZAS:
        partes_b = []
        partes_a = []
        if nombre in C.DEFS:
            db = np.load(os.path.join(cache, f"{nombre}_baja.npz"))
            ob = malla_obj(f"{nombre}_sdf", db["v"], db["f"], col_b)
            ib = items_b.get(nombre, it.Malla())
            objetivo = max(300, C.DEFS[nombre].tris)
            diezmar(ob, objetivo)
            devolver_a_region(ob, nombre)
            partes_b.append(ob)
            da = np.load(os.path.join(cache, f"{nombre}_alta.npz"))
            oa = malla_obj(f"{nombre}_alta_sdf", da["v"], da["f"], col_a)
            poner_atributos(oa, da["col"], da["rme"], da["emi"])
            partes_a.append(oa)
        ib = items_b.get(nombre)
        if ib is not None and len(ib.f):
            partes_b.append(malla_obj(f"{nombre}_items", ib.v, ib.f, col_b))
        ia = items_a.get(nombre)
        if ia is not None and len(ia.f):
            oi = malla_obj(f"{nombre}_items_alta", ia.v, ia.f, col_a)
            poner_atributos(oi, ia.col, ia.rme, ia.emi)
            partes_a.append(oi)
        ob = unir_objs(partes_b, nombre)
        oa = unir_objs(partes_a, f"{nombre}_alta")
        bajos[nombre] = ob
        altos[nombre] = oa
    agujero_ala(bajos["Ala_Der_Mano"], altos["Ala_Der_Mano"])
    # pivotes: el origen de cada pieza en su articulación
    for nombre in PIEZAS:
        p = pivote(nombre, bajos[nombre])
        for o in (bajos[nombre], altos[nombre]):
            o.data.transform(Matrix.Translation(-p))
            o.location = p
    for n, o in bajos.items():
        sacar_de_otras(o, n)
    for o in bajos.values():
        sombreado(o)
    return bajos, altos


def sacar_de_otras(o, nombre, hueco=0.015, iters=5):
    """
    Lo que de una pieza queda ENTERRADO en el cuerpo de otra (raíces de espinas junto a una junta, bordes de
    placas, la membrana pegada al flanco) se saca: hacia su propia región si la pieza tiene cuerpo, o fuera del
    cuerpo si es una pieza suelta (Cresta_Dorsal, Cornamenta). Solo se tocan vértices ya escondidos.
    """
    me = o.data
    v = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", v)
    v = v.reshape(-1, 3) + np.array(o.location)
    propio = nombre in C.DEFS

    def violacion(P):
        d, F = C.campo_cuerpo(P, con_detalle=False)
        if propio:
            return np.minimum(-d, C.region(P, F, nombre) + hueco)  # > 0: dentro del cuerpo y fuera de su región
        return -d + hueco

    for _ in range(iters):
        r = violacion(v)
        malos = r > 0
        if not malos.any():
            break
        P = v[malos]
        g = np.zeros_like(P)
        for i in range(3):
            e = np.zeros(3)
            e[i] = 0.02
            g[:, i] = (violacion(P + e) - violacion(P - e)) / 0.04
        g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
        v[malos] = P - g * (r[malos] + 0.005)[:, None]
    me.vertices.foreach_set("co", (v - np.array(o.location)).ravel())
    me.update()


def devolver_a_region(o, nombre, hueco=0.012, iters=4):
    """
    El diezmado mueve algunos vértices de la junta hacia la pieza vecina: los devolvemos a la región de su pieza
    (con su mitad del hueco) siguiendo el gradiente del campo de la región.
    """
    me = o.data
    v = np.empty(len(me.vertices) * 3)
    me.vertices.foreach_get("co", v)
    v = v.reshape(-1, 3)

    def reg(P):
        return C.region(P, C.campos_propios(P), nombre)

    for _ in range(iters):
        r = reg(v)
        malos = r > -hueco
        if not malos.any():
            break
        P = v[malos]
        g = np.zeros_like(P)
        for i in range(3):
            e = np.zeros(3)
            e[i] = 0.02
            g[:, i] = (reg(P + e) - reg(P - e)) / 0.04
        g /= np.maximum(np.linalg.norm(g, axis=1, keepdims=True), 1e-9)
        v[malos] = P - g * (r[malos] + hueco)[:, None]
    me.vertices.foreach_set("co", v.ravel())
    me.update()


def normales_fuera(o):
    """Normales hacia fuera en todas las islas (las piezas reflejadas al otro lado salen con el orden invertido)."""
    import bmesh as bm_

    b = bm_.new()
    b.from_mesh(o.data)
    bm_.ops.recalc_face_normals(b, faces=b.faces[:])
    b.to_mesh(o.data)
    b.free()
    o.data.update()


def unir_objs(objs, nombre):
    for o in objs:
        normales_fuera(o)
    if len(objs) == 1:
        objs[0].name = nombre
        objs[0].data.name = nombre
        return objs[0]
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = nombre
    o.data.name = nombre
    return o


def pivote(nombre, obj=None):
    if nombre in C.DEFS:
        return Vector(C.DEFS[nombre].pivote)
    if nombre == "Cornamenta":
        return Vector(M.CORNAMENTA_PIVOTE)
    # Cresta_Dorsal: pivote en su centro (sobre el lomo)
    v, _ = leer_malla(obj)
    mn, mx = v.min(0), v.max(0)
    c = (mn + mx) / 2
    return Vector((0.0, float(c[1]), float(mn[2])))


def agujero_ala(baja, alta):
    """Agujero sin reparar (0,5 studs, reciente) cerca de la punta del ala derecha: booleana con un cilindro."""
    _, sect = M.membranas_ala("Der", False)
    lado, sec, u, v, r = M.AGUJERO
    g = sect[sec]
    nu, nv = g.shape[0] - 1, g.shape[1] - 1
    a, c = int(u * nu), int(v * nv)
    p = g[a, c]
    n = s.normalizar(np.cross(g[a + 1, c] - g[a, c], g[a, c + 1] - g[a, c]))
    for o in (baja, alta):
        bpy.ops.mesh.primitive_cylinder_add(vertices=10 if o is baja else 24, radius=r, depth=1.5,
                                            location=tuple(p))
        cil = bpy.context.active_object
        cil.rotation_euler = Vector(n).to_track_quat("Z", "Y").to_euler()
        # bordes del agujero irregulares
        mod = o.modifiers.new("agujero", "BOOLEAN")
        mod.operation = "DIFFERENCE"
        mod.object = cil
        mod.solver = "EXACT"
        aplicar_mods(o)
        bpy.data.objects.remove(cil)


def puntos_montaje():
    tor = M.campo_de("Torso")
    cue = M.campo_de("Cuello_Medio")
    pos = {}
    # piloto de la cría: encima del cuello, al final del tramo medio (junto al superior)
    p = M.superficie(V3(0, -15.2, 14.0), V3(0, 0, 1), cue)
    pos["Montura_Cria_Piloto"] = p + V3(0, 0, 0.35)
    p = M.superficie(V3(0, -2.4, 12.0), V3(0, 0, 1), tor)
    pos["Montura_Cria_Pasajero"] = p + V3(0, 0, 0.6)
    for k, n in ((1, "Agarre_Cuello_Izq"), (-1, "Agarre_Cuello_Der")):
        p = M.superficie(V3(0, -14.2, 14.4), V3(k, 0, 0.1), cue)
        pos[n] = p + V3(k * 0.25, 0, 0)
    pos["Punto_Aliento"] = np.asarray(MONTAJES["Punto_Aliento"][1])
    return pos


def V3(x, y, z):
    return np.array([x, y, z], dtype=np.float64)


def crear_montajes(coleccion):
    objs = {}
    mat = bpy.data.materials.new("Montaje")
    mat.diffuse_color = (0.2, 1.0, 0.4, 1)
    for n, p in puntos_montaje().items():
        bpy.ops.mesh.primitive_cube_add(size=0.3, location=tuple(p))
        o = bpy.context.active_object
        o.name = n
        o.data.name = n
        o.data.materials.append(mat)
        for c in o.users_collection:
            c.objects.unlink(o)
        coleccion.objects.link(o)
        objs[n] = o
    return objs


# --------------------------------------------------------------------------------------------------------------
# UV del atlas y horneado
# --------------------------------------------------------------------------------------------------------------


def uv_atlas(bajos, margen=0.0025):
    objs = [bajos[n] for n in PIEZAS]
    for o in objs:
        activar(o)
        o.data.uv_layers.new(name="UVMap")
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
    # misma densidad de texel en todas las piezas
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    # prioridad (cabeza, boca, garras, hacha con más resolución)
    for n in PIEZAS:
        f = PRIORIDAD.get(n, 1.0)
        uv = bajos[n].data.uv_layers.active.data
        a = np.empty(len(uv) * 2, dtype=np.float32)
        uv.foreach_get("uv", a)
        uv.foreach_set("uv", a * f)
    for o in objs:
        o.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=margen, shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def mascara_uv(o, tam):
    """Píxeles del atlas que cubre la pieza (rasterizando sus triángulos UV)."""
    me = o.data
    me.calc_loop_triangles()
    lt = np.empty(len(me.loop_triangles) * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("loops", lt)
    uv = np.empty(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers.active.data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2)[lt].reshape(-1, 3, 2)
    img = Image.new("L", (tam, tam), 0)
    d = ImageDraw.Draw(img)
    for tri in uv:
        pts = [(float(x * tam), float((1 - y) * tam)) for x, y in tri]
        d.polygon(pts, fill=255, outline=255)
    m = np.array(img)[::-1] > 0  # fila 0 = abajo (como los píxeles de Blender)
    return _dilatar(m, 3)


def _dilatar(m, n):
    m = m.copy()
    for _ in range(n):
        a = m.copy()
        a[1:] |= m[:-1]
        a[:-1] |= m[1:]
        a[:, 1:] |= m[:, :-1]
        a[:, :-1] |= m[:, 1:]
        m = a
    return m


def rellenar_margen(img, cubierto, n=24):
    """Extiende los bordes de las islas hacia los píxeles vacíos (evita costuras al reducir mipmaps)."""
    img = img.copy()
    cub = cubierto.copy()
    for _ in range(n):
        suma = np.zeros_like(img)
        cuenta = np.zeros(cub.shape, dtype=np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1), (1, -1), (-1, 1)):
            sh = np.roll(np.roll(img, dy, 0), dx, 1)
            ch = np.roll(np.roll(cub, dy, 0), dx, 1)
            suma += sh * ch[..., None]
            cuenta += ch
        nuevos = (~cub) & (cuenta > 0)
        img[nuevos] = suma[nuevos] / cuenta[nuevos][:, None]
        cub = cub | nuevos
    return img


def hornear_atlas(bajos, altos, carpeta, tam, muestras_ao=24):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 1
    scn.render.bake.margin = 6
    scn.render.bake.margin_type = "EXTEND"
    for o in list(bajos.values()) + list(altos.values()):
        o.hide_render = False
    mat_alto = material_atributos("alto")
    for o in altos.values():
        o.data.materials.clear()
        o.data.materials.append(mat_alto)
    destino = bpy.data.materials.new("destino")
    destino.use_nodes = True
    nodo = destino.node_tree.nodes.new("ShaderNodeTexImage")
    destino.node_tree.nodes.active = nodo
    for o in bajos.values():
        o.data.materials.clear()
        o.data.materials.append(destino)
    pases = [("col", "EMIT", "sRGB"), ("rme", "EMIT", "Non-Color"), ("emi", "EMIT", "sRGB"),
             ("normal", "NORMAL", "Non-Color"), ("ao", "AO", "Non-Color")]
    atlas = {p: np.zeros((tam, tam, 4), dtype=np.float32) for p, _, _ in pases}
    cubierto = np.zeros((tam, tam), dtype=bool)
    imgs = {}
    for p, tipo, cs in pases:
        img = bpy.data.images.new(f"tmp_{p}", tam, tam, alpha=False, float_buffer=False)
        img.colorspace_settings.name = cs
        imgs[p] = img
    buf = np.empty(tam * tam * 4, dtype=np.float32)
    mascaras = {n: mascara_uv(bajos[n], tam) for n in PIEZAS}
    for n in PIEZAS:
        cubierto |= mascaras[n]
    t0 = time.time()
    for p, tipo, cs in pases:
        nodo.image = imgs[p]
        if tipo == "EMIT":
            canal_horneado(mat_alto, p)
        else:
            canal_horneado(mat_alto, None)
        if tipo == "AO":
            # Oclusión a gran escala con las mallas de juego (unas piezas tapan a otras: vientre, axilas, boca)
            scn.cycles.samples = muestras_ao
            scn.world.light_settings.distance = 4.0
            for o in altos.values():
                o.hide_render = True
        for n in PIEZAS:
            baja, alta = bajos[n], altos[n]
            bpy.ops.object.select_all(action="DESELECT")
            if tipo == "AO":
                activar(baja)
                bpy.ops.object.bake(type="AO", use_clear=True, margin=6)
            else:
                # solo la pieza alta propia: ninguna otra pieza puede "robar" rayos (boca, articulaciones)
                for o in altos.values():
                    o.hide_render = o is not alta
                alta.select_set(True)
                baja.select_set(True)
                bpy.context.view_layer.objects.active = baja
                bpy.ops.object.bake(type=tipo, use_selected_to_active=True, cage_extrusion=0.22,
                                    max_ray_distance=0.7, use_clear=True, margin=6, normal_space="TANGENT")
            imgs[p].pixels.foreach_get(buf)
            px = buf.reshape(tam, tam, 4)
            msk = mascaras[n]
            atlas[p][msk] = px[msk]
        print(f"[ok] pase {p} ({time.time() - t0:.0f} s)", flush=True)
        if tipo == "AO":
            for o in altos.values():
                o.hide_render = False
    # Composición final
    col = atlas["col"][..., :3]
    ao = atlas["ao"][..., :1]
    # la oclusión se multiplica en el color (Roblox no tiene mapa de oclusión), sin apagar del todo
    col = col * (1 - 0.6 * (1 - np.clip(ao, 0, 1)) ** 1.2)
    rme = atlas["rme"][..., :3]
    salida = {
        "color": col,
        "normal": atlas["normal"][..., :3],
        "roughness": np.repeat(rme[..., 0:1], 3, 2),
        "metalness": np.repeat(rme[..., 1:2], 3, 2),
        "emision": atlas["emi"][..., :3],
    }
    rutas = {}
    for k, img in salida.items():
        img = rellenar_margen(img, cubierto, 20)
        # vacío restante: color neutro
        if k == "normal":
            img[~_dilatar(cubierto, 20)] = (0.5, 0.5, 1.0)
        ruta = os.path.join(carpeta, f"{NOMBRE}_{k}.png")
        arr = (np.clip(img[::-1], 0, 1) * 255 + 0.5).astype(np.uint8)
        Image.fromarray(arr, "RGB").save(ruta, optimize=True)
        rutas[k] = ruta
        print("[ok]", ruta, flush=True)
    return rutas


def material_final(rutas):
    mat = bpy.data.materials.new(NOMBRE)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]

    def tex(clave, cs):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(rutas[clave], check_existing=True)
        n.image.colorspace_settings.name = cs
        return n

    nt.links.new(tex("color", "sRGB").outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex("roughness", "Non-Color").outputs["Color"], b.inputs["Roughness"])
    nt.links.new(tex("metalness", "Non-Color").outputs["Color"], b.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal", "Non-Color").outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(tex("emision", "sRGB").outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = FUERZA_EMISION
    return mat


# --------------------------------------------------------------------------------------------------------------
# Render: estudio de 3 puntos, turnaround de 8 vistas, silueta
# --------------------------------------------------------------------------------------------------------------

VISTAS = [
    ("Frente", 0, 6), ("3/4 Frontal", -38, 16), ("Lateral Izq", 90, 4), ("3/4 Trasera", 140, 22),
    ("Trasera", 180, 8), ("Lateral Der", -90, 4), ("Arriba", 0, 89.5), ("Abajo", 0, -89.5),
]


def figura_r6(coleccion, pos=(13.5, -16.0, 0.0)):
    """Jugador R6 de referencia (5 studs de alto) para ver la escala."""
    mat = bpy.data.materials.new("r6")
    mat.use_nodes = True
    mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.6, 0.7, 1)
    piezas = [((0, 0, 4.5), (1.2, 1.2, 1.0)), ((0, 0, 3.0), (2, 1, 2)), ((-1.5, 0, 3.0), (1, 1, 2)),
              ((1.5, 0, 3.0), (1, 1, 2)), ((-0.5, 0, 1.0), (1, 1, 2)), ((0.5, 0, 1.0), (1, 1, 2))]
    objs = []
    for c, t in piezas:
        bpy.ops.mesh.primitive_cube_add(size=1, location=(pos[0] + c[0], pos[1] + c[1], pos[2] + c[2]))
        o = bpy.context.active_object
        o.scale = t
        o.data.materials.append(mat)
        for cc in o.users_collection:
            cc.objects.unlink(o)
        coleccion.objects.link(o)
        o["r6"] = True
        objs.append(o)
    return objs


def estudio():
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.world.use_nodes = True
    nt = scn.world.node_tree
    bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (0.05, 0.055, 0.075, 1)
    bg.inputs["Strength"].default_value = 0.6
    mira = bpy.data.objects.new("mira", None)
    scn.collection.objects.link(mira)
    mira.location = (0, 0, 12)

    def luz(nombre, energia, pos, color, tam):
        d = bpy.data.lights.new(nombre, "AREA")
        d.energy = energia
        d.color = color
        d.size = tam
        o = bpy.data.objects.new(nombre, d)
        o.location = pos
        scn.collection.objects.link(o)
        c = o.constraints.new("TRACK_TO")
        c.target = mira
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        o["luz"] = True
        return o

    # 3 puntos: clave cálida arriba-delante-izquierda, relleno frío, contraluz fuerte que recorta la silueta
    luz("clave", 260000, (-45, -60, 70), (1.0, 0.92, 0.82), 25)
    luz("relleno", 70000, (60, -40, 25), (0.65, 0.75, 1.0), 30)
    luz("contra", 330000, (20, 75, 55), (0.85, 0.9, 1.0), 20)
    luz("contra2", 160000, (-50, 60, 20), (1.0, 0.55, 0.4), 20)
    luz("abajo", 30000, (0, -10, -40), (0.8, 0.8, 0.9), 40)
    bpy.ops.mesh.primitive_plane_add(size=900, location=(0, 0, -0.02))
    suelo = bpy.context.active_object
    suelo.name = "suelo"
    m = bpy.data.materials.new("suelo")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.04, 0.042, 0.05, 1)
    b.inputs["Roughness"].default_value = 0.9
    suelo.data.materials.append(m)
    return mira, suelo


def renderizar(objetos, carpeta, prefijo, tam=900, muestras=48, vistas=VISTAS, lente=50, margen=0.8, sin_suelo=False,
               centro=None, radio=None):
    scn = bpy.context.scene
    scn.cycles.samples = muestras
    scn.render.resolution_x = scn.render.resolution_y = tam
    os.makedirs(carpeta, exist_ok=True)
    mn = np.array([1e9] * 3)
    mx = -mn
    for o in objetos:
        if o.get("r6"):
            continue
        for c in o.bound_box:
            w = np.array(o.matrix_world @ Vector(c))
            mn, mx = np.minimum(mn, w), np.maximum(mx, w)
    cen = Vector(((mn + mx) / 2).tolist()) if centro is None else Vector(centro)
    radio = float(np.linalg.norm(mx - mn) / 2) if radio is None else radio
    mira = bpy.data.objects["mira"]
    mira.location = cen
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = lente
    cam_d.clip_end = 2000
    cam = bpy.data.objects.new("cam", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    fov = 2 * math.atan(18 / lente)
    dist = radio * margen / math.sin(fov / 2)
    suelo = bpy.data.objects.get("suelo")
    rutas = []
    for nombre, az, el in vistas:
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = cen + d * dist
        arriba = "Y" if abs(el) < 80 else "Y"
        q = (cen - cam.location).to_track_quat("-Z", arriba)
        cam.rotation_euler = q.to_euler()
        if abs(el) > 80:
            # vista cenital / desde abajo: la cabeza hacia arriba de la imagen
            cam.rotation_euler = (0.0, 0.0, 0.0) if el > 0 else (math.pi, 0.0, 0.0)
        if suelo:
            suelo.hide_render = el < 0 or sin_suelo
        ruta = os.path.join(carpeta, f"{prefijo}{nombre.replace('/', '-').replace(' ', '_')}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        rutas.append((nombre, ruta))
        print("[ok] render", ruta, flush=True)
    bpy.data.objects.remove(cam)
    return rutas


PRIMEROS_PLANOS = [
    # nombre, centro, radio, azimut, elevación
    ("Cabeza 3/4", (0, -25.5, 10.0), 6.5, -35, 10),
    ("Boca perfil", (1.5, -25.5, 8.8), 5.5, 80, 2),
    ("Pecho (cicatriz X)", (0, -11.0, 8.5), 7.0, -55, -4),
    ("Lomo (ecosistema)", (0, 0.5, 13.5), 9.0, 30, 55),
    ("Cuello y cadenas", (1.5, -12.5, 12.0), 6.5, 55, 12),
    ("Pata trasera", (7.6, 6.0, 3.5), 5.0, 70, 10),
    ("Hacha de la cola", (3.4, 30.5, 9.0), 4.0, 120, 25),
    ("Ala (cara interior)", (17.0, 4.0, 22.0), 14.0, -20, 10),
]


def primeros_planos(objetos, carpeta, tam, muestras):
    out = []
    for nombre, c, r, az, el in PRIMEROS_PLANOS:
        out += renderizar(objetos, carpeta, "pp_", tam=tam, muestras=muestras, vistas=[(nombre, az, el)],
                          centro=c, radio=r, margen=1.0)
    return out


def _fuente(tam, negrita=True):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrita else \
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(ruta):
        return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default(tam)


def hoja(rutas, salida, titulo, notas=(), columnas=4):
    tam = Image.open(rutas[0][1]).size[0]
    filas = math.ceil(len(rutas) / columnas)
    cab = 70 + 22 * len(notas)
    h = Image.new("RGB", (columnas * tam, cab + filas * tam), (12, 12, 16))
    d = ImageDraw.Draw(h)
    d.text((16, 12), titulo, fill=(255, 120, 60), font=_fuente(30))
    for i, n in enumerate(notas):
        d.text((18, 54 + i * 22), n, fill=(210, 210, 220), font=_fuente(17, False))
    for i, (nombre, ruta) in enumerate(rutas):
        x, y = (i % columnas) * tam, cab + (i // columnas) * tam
        h.paste(Image.open(ruta).convert("RGB"), (x, y))
        d.rectangle((x, y, x + tam - 1, y + tam - 1), outline=(40, 40, 50))
        d.text((x + 12, y + 10), nombre, fill=(255, 255, 255), font=_fuente(22))
    h.save(salida)
    print("[ok] hoja", salida, flush=True)
    return salida


def silueta(objetos, carpeta, prefijo="silueta_"):
    """Prueba de silueta: todo negro plano sobre blanco."""
    scn = bpy.context.scene
    negro = bpy.data.materials.new("negro_plano")
    negro.use_nodes = True
    nt = negro.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    bg = scn.world.node_tree.nodes["Background"]
    viejo = (tuple(bg.inputs["Color"].default_value), bg.inputs["Strength"].default_value)
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = 1.0
    scn.view_layers[0].material_override = negro
    vt = scn.view_settings.view_transform
    scn.view_settings.view_transform = "Standard"
    scn.view_settings.look = "None"
    suelo = bpy.data.objects.get("suelo")
    if suelo:
        suelo.hide_viewport = True
        suelo.hide_render = True
    ocultos = [o for o in scn.objects if o.get("r6")]
    for o in ocultos:
        o.hide_render = True
    rutas = renderizar(objetos, carpeta, prefijo, tam=700, muestras=4, sin_suelo=True,
                       vistas=[("Frente", 0, 6), ("3/4 Frontal", -38, 16), ("Lateral Izq", 90, 4),
                               ("Arriba", 0, 89.5)])
    scn.view_layers[0].material_override = None
    bg.inputs["Color"].default_value = viejo[0]
    bg.inputs["Strength"].default_value = viejo[1]
    scn.view_settings.view_transform = vt
    scn.view_settings.look = "AgX - Medium High Contrast"
    if suelo:
        suelo.hide_render = False
    for o in ocultos:
        o.hide_render = False
    return rutas


# --------------------------------------------------------------------------------------------------------------
# Comprobaciones
# --------------------------------------------------------------------------------------------------------------


def comprobar_penetraciones(bajos):
    """
    Para cada pieza, ¿algún vértice queda DENTRO de otra pieza? (más de 0,01 studs). Se mira contra el campo de
    cada pieza del cuerpo tal como se malla; lo de dentro de la misma pieza (dientes en la encía) no cuenta.
    """
    informe = {}
    for n in PIEZAS:
        o = bajos[n]
        v, _ = leer_malla(o)
        v = v + np.array(o.location)
        peor = {}
        for q in C.DEFS:
            if q == n:
                continue
            c, r = C.DEFS[q].esfera
            cerca = np.linalg.norm(v - c, axis=1) < r + 0.5
            if not cerca.any():
                continue
            d = C.campo_pieza(v[cerca], q, con_detalle=False)
            mal = d < -0.06
            if mal.any():
                donde = v[cerca][mal].mean(0)
                peor[q] = (int(mal.sum()), round(float(-d.min()), 3), [round(float(x), 1) for x in donde])
        informe[n] = peor
    return informe


# --------------------------------------------------------------------------------------------------------------
# Exportación, reimportación, JSON y script de montaje
# --------------------------------------------------------------------------------------------------------------


def a_roblox(p):
    """Blender (studs) -> Roblox (studs) después del GIRO_IMPORTACION: (x, y, z) -> (-x, z, y)."""
    x, y, z = p
    return [round(-x, 3), round(z, 3), round(y, 3)]


def exportar(bajos, montajes, mat, ruta):
    objs = [bajos[n] for n in PIEZAS] + list(montajes.values())
    for n in PIEZAS:
        bajos[n].data.materials.clear()
        bajos[n].data.materials.append(mat)
    # GIRO_IMPORTACION: 180° alrededor del eje vertical, aplicado a la geometría y a la posición (la rotación de
    # cada objeto queda en 0,0,0 y el origen sigue en su articulación).
    R = Matrix.Rotation(math.radians(GIRO_IMPORTACION), 4, "Z")
    for o in objs:
        o.data.transform(R)
        o.location = R @ o.location
        o.rotation_euler = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta,
        use_selection=True,
        object_types={"MESH"},
        global_scale=ESTUDIO,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=False,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        add_leaf_bones=False,
        bake_anim=False,
        embed_textures=True,
        path_mode="COPY",
    )
    # deshacer el giro en la escena (para los renders y comprobaciones posteriores)
    Ri = R.inverted()
    for o in objs:
        o.data.transform(Ri)
        o.location = Ri @ o.location
    print("[ok] FBX", ruta, flush=True)


def reimportar(ruta, esperado):
    """Importa el FBX en una escena limpia y compara pivotes (en studs, ya girados) y triángulos."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta, global_scale=1.0 / ESTUDIO, axis_forward="-Z", axis_up="Y")
    bpy.context.view_layer.update()
    resultado = {}
    peor = 0.0
    for o in bpy.context.scene.objects:
        if o.type != "MESH":
            continue
        n = o.name.split(".")[0]
        loc = np.array(o.matrix_world.translation)
        rot = np.degrees(np.array(o.matrix_world.to_euler()))
        esc = np.array(o.matrix_world.to_scale())
        if n in esperado:
            err = float(np.linalg.norm(loc - esperado[n]["pos"]))
            peor = max(peor, err)
            resultado[n] = dict(err=round(err, 4), rot=[round(float(r), 3) for r in rot],
                                esc=[round(float(e), 4) for e in esc], tris=triangulos(o))
    faltan = [n for n in esperado if n not in resultado]
    return resultado, peor, faltan


def escribir_montar(ruta, datos):
    def v3(p):
        return f"Vector3.new({p[0]}, {p[1]}, {p[2]})"

    lineas = [
        "--[[",
        "\tMonta el Dragón Leviatán importado en Studio. Pégalo en la barra de comandos (View → Command Bar) con el",
        "\tmodelo importado SELECCIONADO y pulsa Enter.",
        "",
        "\tLo genera modelos/herramientas/dragon_leviatan.py: no lo edites a mano (los números salen de Blender).",
        "",
        "\t1. Junta las 25 piezas en un Model con el Torso como PrimaryPart.",
        "\t2. Une cada pieza a su padre con un Motor6D cuyo pivote es la articulación (cadena: Torso → Cuello_Base →",
        "\t   Cuello_Medio → Cuello_Superior → Cabeza → Mandibula; Torso → Ala_*_Hombro → Antebrazo → Mano; etc.).",
        "\t3. Convierte los 5 puntos de montaje en Attachments dentro de su pieza (y borra los cubos).",
        "\t4. Añade AnimationController + Animator (el dragón no es Humanoid).",
        "]]",
        "",
        'local RAIZ = "Torso"',
        "local PIVOTES = {",
    ]
    for n in PIEZAS:
        lineas.append(f'\t["{n}"] = {v3(datos["piezas"][n]["pivote_roblox"])},')
    lineas += ["}", "local CENTROS = {"]
    for n in PIEZAS:
        lineas.append(f'\t["{n}"] = {v3(datos["piezas"][n]["centro_roblox"])},')
    lineas += ["}", "local PADRES = {"]
    for n in PIEZAS:
        if datos["piezas"][n]["padre"]:
            lineas.append(f'\t["{n}"] = "{datos["piezas"][n]["padre"]}",')
    lineas += ["}", "local MONTAJES = {"]
    for n, d in datos["puntos_montaje"].items():
        lineas.append(f'\t["{n}"] = {{ pieza = "{d["pieza"]}", pos = {v3(d["pos_roblox"])} }},')
    lineas += ["}", ""]
    lineas += r"""local seleccion = game:GetService("Selection"):Get()[1]
assert(seleccion, "Selecciona el modelo importado antes de ejecutar el script")

local piezas = {}
local cubos = {}
for _, d in seleccion:GetDescendants() do
	if d:IsA("BasePart") then
		if CENTROS[d.Name] then
			piezas[d.Name] = d
		elseif MONTAJES[d.Name] then
			cubos[d.Name] = d
		end
	end
end
for nombre in CENTROS do
	assert(piezas[nombre], `Falta la pieza {nombre} en el modelo importado`)
end

local modelo = Instance.new("Model")
modelo.Name = "DragonLeviatan"
modelo.Parent = seleccion.Parent

local raiz = piezas[RAIZ]
local base = raiz.Position - CENTROS[RAIZ] -- dónde ha quedado el origen del modelo de Blender

for nombre, parte in piezas do
	parte.Anchored = nombre == RAIZ
	parte.CanCollide = nombre == RAIZ
	parte.Massless = nombre ~= RAIZ
	parte.CFrame = CFrame.new(base + CENTROS[nombre])
	parte.Parent = modelo
end
modelo.PrimaryPart = raiz

for nombre, padre in PADRES do
	local parte = piezas[nombre]
	local p0 = piezas[padre]
	local marco = CFrame.new(base + PIVOTES[nombre])
	local m = Instance.new("Motor6D")
	m.Name = nombre
	m.Part0 = p0
	m.Part1 = parte
	m.C0 = p0.CFrame:Inverse() * marco
	m.C1 = parte.CFrame:Inverse() * marco
	m.Parent = p0
end

for nombre, d in MONTAJES do
	local a = Instance.new("Attachment")
	a.Name = nombre
	a.WorldPosition = base + d.pos
	a.Parent = piezas[d.pieza]
	a.WorldPosition = base + d.pos
	if cubos[nombre] then
		cubos[nombre]:Destroy()
	end
end

local controlador = Instance.new("AnimationController")
controlador.Parent = modelo
Instance.new("Animator").Parent = controlador

seleccion:Destroy()
game:GetService("Selection"):Set({ modelo })
print(`[Dragón] {modelo.Name} montado: 25 piezas, 24 Motor6D, 5 puntos de montaje`)
""".split("\n")
    with open(ruta, "w", encoding="utf-8") as f:
        f.write("\n".join(lineas))
    print("[ok]", ruta, flush=True)


# --------------------------------------------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------------------------------------------


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--fase", default="previa")
    ap.add_argument("--ronda", default="0")
    ap.add_argument("--tex", type=int, default=4096)
    ap.add_argument("--muestras", type=int, default=48)
    ap.add_argument("--tam", type=int, default=900)
    a = ap.parse_args(argv)
    os.makedirs(a.salida, exist_ok=True)
    proceso = os.path.join(a.salida, "proceso", f"ronda{a.ronda}")
    os.makedirs(proceso, exist_ok=True)
    escena_vacia()
    t0 = time.time()
    bajos, altos = construir(a.cache)
    print(f"[ok] piezas construidas ({time.time() - t0:.0f} s)", flush=True)
    total = sum(triangulos(bajos[n]) for n in PIEZAS)
    for n in PIEZAS:
        print(f"    {n:22s} {triangulos(bajos[n]):6d} tris", flush=True)
    print(f"[ok] TOTAL {total} triángulos", flush=True)
    col_m = bpy.data.collections.new("Montajes")
    bpy.context.scene.collection.children.link(col_m)
    montajes = crear_montajes(col_m)
    pen = comprobar_penetraciones(bajos)
    malas = {k: v for k, v in pen.items() if v}
    print("[..] penetraciones:", json.dumps(malas, ensure_ascii=False), flush=True)

    if a.fase == "previa":
        for o in altos.values():
            o.hide_render = True
        arc = material_arcilla()
        for o in bajos.values():
            o.data.materials.clear()
            o.data.materials.append(arc)
        estudio()
        for o in montajes.values():
            o.hide_render = True
        figura_r6(bpy.context.scene.collection)
        rutas = renderizar(list(bajos.values()), proceso, "previa_", tam=a.tam, muestras=a.muestras)
        rutas += primeros_planos(list(bajos.values()), proceso, a.tam, a.muestras)
        hoja(rutas[:8], os.path.join(proceso, "hoja_previa.png"), f"Dragón Leviatán · ronda {a.ronda} · arcilla",
             [f"{total} triángulos · {len(PIEZAS)} piezas"])
        hoja(rutas[8:], os.path.join(proceso, "hoja_detalle.png"), f"Primeros planos · ronda {a.ronda}")
        sil = silueta(list(bajos.values()), proceso)
        hoja(sil, os.path.join(proceso, "hoja_silueta.png"), "Prueba de silueta", columnas=4)
        # una pieza de cada color: para ver los cortes del rig y si algo flota
        rnd = random.Random(0)
        for n in PIEZAS:
            m = bpy.data.materials.new(f"c_{n}")
            m.use_nodes = True
            import colorsys
            m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (
                *colorsys.hsv_to_rgb(rnd.random(), 0.6, 0.8), 1)
            bajos[n].data.materials.clear()
            bajos[n].data.materials.append(m)
        pz = renderizar(list(bajos.values()), proceso, "piezas_", tam=a.tam, muestras=16,
                        vistas=[("Frente", 0, 6), ("3/4 Frontal", -38, 16), ("Lateral Izq", 90, 4),
                                ("3/4 Trasera", 140, 22)])
        hoja(pz, os.path.join(proceso, "hoja_piezas.png"), "Piezas del rig (un color por pieza)")
        return

    # ---- fase completa ----
    uv_atlas(bajos)
    rutas_tex = hornear_atlas(bajos, altos, a.salida, a.tex)
    mat = material_final(rutas_tex)
    for o in altos.values():
        o.hide_render = True
        o.hide_viewport = True
    for n in PIEZAS:
        bajos[n].data.materials.clear()
        bajos[n].data.materials.append(mat)
    for o in montajes.values():
        o.hide_render = True
    estudio()
    figura_r6(bpy.context.scene.collection)
    objs = [bajos[n] for n in PIEZAS]
    rutas = renderizar(objs, proceso, "vista_", tam=a.tam, muestras=a.muestras)
    notas = [f"{total} triángulos · 25 piezas Motor6D · atlas {a.tex}×{a.tex} · figura gris = jugador R6 (5 studs)"]
    hoja(rutas, os.path.join(proceso, "turnaround.png"), f"Dragón Leviatán · ronda {a.ronda}", notas)
    sil = silueta(objs, proceso)
    hoja(sil, os.path.join(proceso, "hoja_silueta.png"), "Prueba de silueta", columnas=4)
    # datos para el JSON (antes de exportar, con la escena en coordenadas de Blender)
    datos = {"nombre": NOMBRE, "triangulos": total, "unidades": "studs (1 unidad de Blender = 1 stud)",
             "giro_importacion_grados": GIRO_IMPORTACION,
             "ejes": "Roblox: delante -Z, arriba +Y. Pivotes en coordenadas de Roblox relativas al origen del "
                     "modelo (centro en el suelo).",
             "fbx": {"archivo": f"{NOMBRE}.fbx", "escala": "metros (1 stud = 0,28 m); Apply Scalings: FBX All",
                     "importar_con": "Scale Unit: Meter"},
             "texturas": {k: os.path.basename(v) for k, v in rutas_tex.items()},
             "piezas": {}, "puntos_montaje": {}}
    vmin = np.array([1e9] * 3)
    vmax = -vmin
    esperado = {}
    for n in PIEZAS:
        o = bajos[n]
        v, _ = leer_malla(o)
        v = v + np.array(o.location)
        mn, mx = v.min(0), v.max(0)
        vmin, vmax = np.minimum(vmin, mn), np.maximum(vmax, mx)
        piv = np.array(o.location)
        datos["piezas"][n] = {
            "padre": PADRES[n], "triangulos": triangulos(o),
            "pivote_blender": [round(float(x), 3) for x in piv], "pivote_roblox": a_roblox(piv),
            "centro_roblox": a_roblox((mn + mx) / 2), "tam_roblox": [round(float(x), 3) for x in
                                                                       (mx - mn)[[0, 2, 1]]],
        }
        R = np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]])
        esperado[n] = {"pos": R @ piv}
    for n, o in montajes.items():
        p = np.array(o.location)
        datos["puntos_montaje"][n] = {"pieza": MONTAJES[n][0], "pos_blender": [round(float(x), 3) for x in p],
                                      "pos_roblox": a_roblox(p), "tam": 0.3}
        esperado[n] = {"pos": np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]]) @ p}
    tam_ = vmax - vmin
    datos["tamano_studs"] = {"envergadura_x": round(float(tam_[0]), 2), "largo_y": round(float(tam_[1]), 2),
                             "alto_z": round(float(tam_[2]), 2)}
    datos["penetraciones"] = {k: v for k, v in pen.items() if v}
    ruta_fbx = os.path.join(a.salida, f"{NOMBRE}.fbx")
    exportar(bajos, montajes, mat, ruta_fbx)
    escribir_montar(os.path.join(a.salida, "montar_dragon_leviatan.luau"), datos)
    # Turnaround final en la carpeta principal
    import shutil

    shutil.copy(os.path.join(proceso, "turnaround.png"), os.path.join(a.salida, f"{NOMBRE}_turnaround.png"))
    res, peor, faltan = reimportar(ruta_fbx, esperado)
    datos["verificacion_reimportacion"] = {"error_max_pivote_studs": round(peor, 4), "faltan": faltan,
                                           "piezas": res}
    with open(os.path.join(a.salida, f"{NOMBRE}.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=1, default=float)
    print(f"[ok] reimportación: error máximo de pivote {peor:.4f} studs, faltan {faltan}", flush=True)
    print(f"[ok] terminado en {time.time() - t0:.0f} s", flush=True)


if __name__ == "__main__":
    main()
