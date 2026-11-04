"""
Construye la escena de la región 1 (Valle del Alba) en Blender y la guarda en region1_valle_del_alba.blend:

  * Terreno de la cara YP (malla de ángulos iguales, como el planeta de prueba) con su textura pintada.
  * El resto del planeta (5 caras, baja resolución, con el relieve del planeta de prueba) y el mar: SOLO DE REFERENCIA
    para los renders, no son parte de la región.
  * Río, charca del manantial, puente, caminos (en la textura), mirador de la colina del atardecer.
  * Aurora, Pradoverde y Los Molinos con sus edificios (montados con el kit) y su mobiliario.
  * Campos de cultivo de Los Molinos.
  * Vegetación instanciada con Geometry Nodes (árboles, arbustos, rocas, matas de hierba y flores).

Uso:
    python modelos/region1_valle_del_alba/herramientas/region.py --salida modelos/region1_valle_del_alba
        [--cuadros 1024] [--textura 4096] [--rapido]
"""

import argparse
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix  # noqa: E402
from PIL import Image  # noqa: E402

import diseno as D  # noqa: E402
import escena as E  # noqa: E402
import geo  # noqa: E402
import kit as K  # noqa: E402
import materiales as MAT  # noqa: E402
import pueblos as PB  # noqa: E402
import relieve as RV  # noqa: E402
import textura as TX  # noqa: E402
from malla import Malla  # noqa: E402

R = geo.RADIO


# ==============================================================================================================
# Utilidades
# ==============================================================================================================


def coleccion(nombre, padre=None):
    c = bpy.data.collections.new(nombre)
    (padre or bpy.context.scene.collection).children.link(c)
    return c


def capa_coleccion(nombre, capa=None):
    capa = capa or bpy.context.view_layer.layer_collection
    if capa.name == nombre:
        return capa
    for h in capa.children:
        r = capa_coleccion(nombre, h)
        if r:
            return r
    return None


def malla_rejilla(nombre, P, uv, col, mat, liso=True):
    """P: (n+1, n+1, 3) posiciones; uv: (n+1, n+1, 2). Crea un objeto de cuadros."""
    n1 = P.shape[0]
    n = n1 - 1
    me = bpy.data.meshes.new(nombre)
    idx = np.arange(n1 * n1).reshape(n1, n1)
    # filas = norte -> sur en la rejilla (i), columnas = oeste -> este (j): orden antihorario visto desde fuera
    a, b, c_, d = idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:], idx[:-1, :-1]
    quads = np.stack([a, b, c_, d], -1).reshape(-1, 4)
    me.vertices.add(n1 * n1)
    me.vertices.foreach_set("co", P.reshape(-1, 3).astype(np.float32).ravel())
    me.loops.add(quads.size)
    me.loops.foreach_set("vertex_index", quads.ravel().astype(np.int32))
    me.polygons.add(len(quads))
    me.polygons.foreach_set("loop_start", np.arange(0, quads.size, 4, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.full(len(quads), liso))
    capa = me.uv_layers.new(name="UVMap")
    capa.data.foreach_set("uv", uv.reshape(-1, 2)[quads.ravel()].astype(np.float32).ravel())
    me.update(calc_edges=True)
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    return ob


def matriz_local(d, este, giro_grados, alto):
    """Matriz de un objeto apoyado en la dirección d, con su eje X girado `giro` desde el este local."""
    d = d / np.linalg.norm(d)
    e = este - np.dot(este, d) * d
    e /= np.linalg.norm(e)
    n = np.cross(d, e)
    a = math.radians(giro_grados)
    ex = math.cos(a) * e + math.sin(a) * n
    ey = -math.sin(a) * e + math.cos(a) * n
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2] = ex, ey, d
    m[:3, 3] = d * (R + alto)
    return Matrix(m.tolist())


def material_terreno(ruta_imagen):
    mat = bpy.data.materials.new("Terreno_Valle")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    n, l = nt.nodes, nt.links
    tex = n.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(ruta_imagen)
    tex.interpolation = "Cubic"
    tex.extension = "EXTEND"
    uv = n.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    l.new(uv.outputs[0], tex.inputs[0])
    # detalle fino que la textura (≈1 stud por píxel) no tiene: ruido en coordenadas del objeto
    tc = n.new("ShaderNodeTexCoord")
    ruido = n.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 0.35
    ruido.inputs["Detail"].default_value = 3.0
    l.new(tc.outputs["Object"], ruido.inputs["Vector"])
    mr = n.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value = 0.88
    mr.inputs["To Max"].default_value = 1.1
    l.new(ruido.outputs["Fac"], mr.inputs["Value"])
    mul = n.new("ShaderNodeVectorMath")
    mul.operation = "SCALE"
    l.new(tex.outputs["Color"], mul.inputs[0])
    l.new(mr.outputs[0], mul.inputs["Scale"])
    bsdf = n.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    bsdf.inputs["Specular IOR Level"].default_value = 0.3
    l.new(mul.outputs[0], bsdf.inputs["Base Color"])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    bump.inputs["Distance"].default_value = 0.3
    l.new(ruido.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    MAT.salida_con_niebla(mat, bsdf.outputs[0])
    return mat


def material_color_vertice(nombre):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    at = nt.nodes.new("ShaderNodeAttribute")
    at.attribute_name = "Col"
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.95
    nt.links.new(at.outputs["Color"], bsdf.inputs["Base Color"])
    MAT.salida_con_niebla(mat, bsdf.outputs[0])
    return mat


# ==============================================================================================================
# Partes de la escena
# ==============================================================================================================


def terreno(V, n, ruta_tex, col):
    t0 = time.time()
    g = np.linspace(-geo.L, geo.L, n + 1)
    X, Y = np.meshgrid(g, g[::-1])
    H = V.altura(X, Y)
    d = geo.direccion(X, Y)
    P = d * (R + H)[..., None]
    uv = np.stack([(X + geo.L) / (2 * geo.L), (Y + geo.L) / (2 * geo.L)], -1)
    ob = malla_rejilla("Terreno_Valle_del_Alba", P, uv, col, material_terreno(ruta_tex))
    ob["region"] = "Valle del Alba (cara YP)"
    print(f"terreno: {n}x{n} cuadros, {2 * n * n} triángulos, {time.time() - t0:.1f} s")
    return ob, H


def resto_planeta(V, col, n=96):
    """Las otras cinco caras con el relieve del planeta de prueba (referencia visual)."""
    mat = material_color_vertice("Planeta_Resto")
    caras = {  # (normal, a, b) en ejes de Blender, con a × b = normal
        "XP": ((1, 0, 0), (0, 1, 0), (0, 0, 1)), "XN": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
        "YP": ((0, 1, 0), (0, 0, 1), (1, 0, 0)), "YN": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
        "ZN": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
    }
    base = V.base
    for nombre, (nn, a, b) in caras.items():
        nn, a, b = (np.array(v, float) for v in (nn, a, b))
        al = np.tan(np.linspace(-math.pi / 4, math.pi / 4, n + 1))
        p = nn + al[:, None, None] * a + al[None, :, None] * b
        d = p / np.linalg.norm(p, axis=-1, keepdims=True)
        h = base.altura(geo.blender_a_roblox(d).reshape(-1, 3)).reshape(n + 1, n + 1)
        P = d * (R + h)[..., None]
        uv = np.zeros((n + 1, n + 1, 2))
        ob = malla_rejilla(f"Planeta_Resto_{nombre}", P, uv, col, mat)
        me = ob.data
        colr = np.interp(h, [-90, -5, 0, 3, 30, 80, 140], [0.13, 0.3, 0.75, 0.42, 0.36, 0.42, 0.6])
        colg = np.interp(h, [-90, -5, 0, 3, 30, 80, 140], [0.22, 0.4, 0.7, 0.62, 0.56, 0.5, 0.58])
        colb = np.interp(h, [-90, -5, 0, 3, 30, 80, 140], [0.3, 0.42, 0.5, 0.3, 0.27, 0.3, 0.5])
        rgb = np.stack([colr, colg, colb, np.ones_like(colr)], -1).reshape(-1, 4) ** 2.2
        at = me.color_attributes.new("Col", "FLOAT_COLOR", "POINT")
        at.data.foreach_set("color", rgb.astype(np.float32).ravel())
        # (la orientación de las caras no importa en Cycles; se deja como sale)


def mar(col):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=384, ring_count=192, radius=R)
    ob = bpy.context.active_object
    ob.name = "Mar_referencia"
    for c in ob.users_collection:
        c.objects.unlink(ob)
    col.objects.link(ob)
    for p in ob.data.polygons:
        p.use_smooth = True
    ob.data.materials.append(MAT.crear_material("Mar"))
    return ob


def rio(V, col):
    m = V.rio.m
    xy = m[:, :2]
    dentro = (np.abs(xy[:, 0]) <= geo.L) & (np.abs(xy[:, 1]) <= geo.L)
    m = m[dentro][::2]
    t = np.gradient(m[:, :2], axis=0)
    t /= np.linalg.norm(t, axis=1, keepdims=True)
    nrm = np.stack([-t[:, 1], t[:, 0]], -1)
    k = np.array([-1.0, -0.5, 0.0, 0.5, 1.0])
    ancho = (m[:, 3] + 1.2)[:, None] * k[None, :]
    px = m[:, 0:1] + nrm[:, 0:1] * ancho
    py = m[:, 1:2] + nrm[:, 1:2] * ancho
    d = geo.direccion(px, py)
    P = d * (R + m[:, 2:3])[..., None]
    nf, nc = P.shape[:2]
    verts = P.reshape(-1, 3)
    caras = []
    for i in range(nf - 1):
        for j in range(nc - 1):
            caras.append((i * nc + j, i * nc + j + 1, (i + 1) * nc + j + 1, (i + 1) * nc + j))
    me = bpy.data.meshes.new("Rio_Agua")
    me.from_pydata(verts.tolist(), [], caras)
    for p in me.polygons:
        p.use_smooth = True
    me.materials.append(MAT.crear_material("Agua"))
    ob = bpy.data.objects.new("Rio_Agua", me)
    col.objects.link(ob)
    # charca del manantial
    cx, cy, rc = D.CHARCA_MANANTIAL
    a = np.linspace(0, 2 * np.pi, 48, endpoint=False)
    pts = [(cx, cy)] + [(cx + (rc + 1.0) * math.cos(t), cy + (rc + 1.0) * math.sin(t)) for t in a]
    P = geo.direccion(np.array([p[0] for p in pts]), np.array([p[1] for p in pts])) * (R + D.RIO[0][2])
    me = bpy.data.meshes.new("Charca_Agua")
    me.from_pydata(P.tolist(), [], [(0, i + 1, (i + 1) % 48 + 1) for i in range(48)])
    me.materials.append(MAT.crear_material("Agua"))
    ob = bpy.data.objects.new("Charca_Agua", me)
    col.objects.link(ob)


class Constructor:
    """Coloca las cosas de los sitios (edificios y piezas compartidas)."""

    def __init__(self, V, mats, col_raiz):
        self.V, self.mats = V, mats
        self.mallas_piezas = {}
        self.col_raiz = col_raiz

    def malla_pieza(self, nombre):
        if nombre not in self.mallas_piezas:
            fn = PB.PIEZAS.get(nombre)
            m = fn() if fn else getattr(K, nombre)()
            tmp = m.a_blender("tmp_" + nombre, self.mats)
            me = tmp.data
            me.name = "Pieza_" + nombre
            bpy.data.objects.remove(tmp)
            self.mallas_piezas[nombre] = me
        return self.mallas_piezas[nombre]

    def altura(self, d):
        x, y = geo.diseno(d)
        return float(self.V.altura(np.array([x]), np.array([y]))[0])

    def pieza(self, nombre, d, este, giro, dz=0.0, escala=1.0, col=None, nombre_obj=None, alto=None):
        ob = bpy.data.objects.new(nombre_obj or nombre, self.malla_pieza(nombre))
        h = self.altura(d) if alto is None else alto
        ob.matrix_world = matriz_local(d, este, giro, h + dz) @ Matrix.Scale(escala, 4)
        (col or self.col_raiz).objects.link(ob)
        return ob

    def sitio(self, nombre, t, col):
        s = self.V.sitios[nombre]
        h_sitio = self.V.alturas_sitio[nombre]
        col_ed = coleccion(f"{nombre}_Edificios", col)
        col_pz = coleccion(f"{nombre}_Mobiliario", col)
        n_ed = 0
        for cl in t.colocaciones:
            d = s.direccion(np.array(cl.u), np.array(cl.v))
            if cl.tipo == "edificio":
                ob = cl.malla.a_blender(cl.nombre, self.mats, col_ed)
                ob.matrix_world = matriz_local(d, s.este, cl.giro, h_sitio + 0.35)
                n_ed += 1
            else:
                self.pieza(cl.pieza, d, s.este, cl.giro, cl.dz - (0.4 if cl.pieza.startswith("Arb") else 0.0),
                           cl.escala, col_pz, nombre_obj=f"{nombre}_{cl.nombre}")
        print(f"{nombre}: {n_ed} edificios, {len(t.colocaciones) - n_ed} piezas")


def filtrar_parcelas(V, nombre, parcelas):
    s = V.sitios[nombre]
    buenas = []
    for p in parcelas:
        g = math.radians(p["giro"])
        cu, cv = p["centro"]
        w, l = p["ancho"] / 2 + 3, p["largo"] / 2 + 3
        aa, bb = np.meshgrid(np.linspace(-w, w, 7), np.linspace(-l, l, 9))
        u = cu + aa * math.cos(g) - bb * math.sin(g)
        v = cv + aa * math.sin(g) + bb * math.cos(g)
        x, y = s.diseno(u, v)
        ok = True
        for cn, cam in D.CAMINOS.items():
            dd, _ = V.caminos[cn].cercano(x, y)
            if dd.min() < cam["ancho"] / 2 + 5:
                ok = False
        dd, ii = V.rio.cercano(x, y)
        if (dd - V.rio.m[ii, 3]).min() < 14:
            ok = False
        H = V.altura(x, y)
        if H.max() - H.min() > 14:
            ok = False
        if ok:
            buenas.append(p)
    return buenas


def cultivos(V, nombre, parcelas, col, mats):
    """Hileras de cultivo apoyadas en el terreno (una malla para todo el campo)."""
    s = V.sitios[nombre]
    rng = np.random.default_rng(5)
    m = Malla()
    altos = {"trigo": (2.4, 2.6, "Trigo"), "col": (1.4, 2.2, "Col"), "lavanda": (1.9, 2.0, "Flor_Lila"),
             "calabaza": (0.9, 2.4, "Col"), "arado": (0.6, 2.4, "Tierra_Arada")}
    for p in parcelas:
        cult = p["cultivo"]
        if cult not in altos:
            continue
        alto, base, mat = altos[cult]
        g = math.radians(p["giro"])
        cu, cv = p["centro"]
        ea = np.array([math.cos(g), math.sin(g)])
        eb = np.array([-math.sin(g), math.cos(g)])
        filas = np.arange(-p["ancho"] / 2 + 1.6, p["ancho"] / 2 - 1.0, 3.2)
        bs = np.linspace(-p["largo"] / 2 + 1.5, p["largo"] / 2 - 1.5, 11)
        for a in filas:
            uvs = [(cu + a * ea[0] + b * eb[0], cv + a * ea[1] + b * eb[1]) for b in bs]
            u = np.array([q[0] for q in uvs])
            v = np.array([q[1] for q in uvs])
            dc = s.direccion(u, v)
            x, y = geo.diseno(dc)
            h = V.altura(x, y)
            ua = (s.direccion(u + ea[0], v + ea[1]) - dc)
            ua /= np.linalg.norm(ua, axis=1, keepdims=True)
            P0 = dc * (R + h - 0.3)[:, None]
            top = dc * (R + h + alto * rng.uniform(0.9, 1.05))[:, None]
            izq = P0 - ua * base / 2
            der = P0 + ua * base / 2
            for k in range(len(bs) - 1):
                ti = float(rng.uniform(0.9, 1.08))
                m.poligono([izq[k], izq[k + 1], top[k + 1], top[k]], mat, tinte=ti)
                m.poligono([der[k + 1], der[k], top[k], top[k + 1]], mat, tinte=ti * 0.92)
            if cult == "calabaza":
                for k in range(0, len(bs), 2):
                    if rng.uniform() < 0.6:
                        c3 = top[k] + ua[k] * rng.uniform(-0.8, 0.8)
                        m.esfera(c3, 0.95, "Calabaza", sub=1)
    ob = m.a_blender(f"{nombre}_Cultivos", mats, col)
    print(f"cultivos: {len(parcelas)} parcelas, {ob['triangulos']} triángulos")


# ==============================================================================================================
# Vegetación instanciada
# ==============================================================================================================

FUENTES_VEG = [  # (nombre, función) — el orden fija el índice «tipo»
    ("V00_Frondoso_a", lambda: K.arbol_frondoso(101)), ("V01_Frondoso_b", lambda: K.arbol_frondoso(102)),
    ("V02_Frondoso_c", lambda: K.arbol_frondoso(103)), ("V03_Frondoso_d", lambda: K.arbol_frondoso(104)),
    ("V04_Pino_a", lambda: K.pino(201)), ("V05_Pino_b", lambda: K.pino(202)), ("V06_Pino_c", lambda: K.pino(203)),
    ("V07_Abedul_a", lambda: K.abedul(301)), ("V08_Abedul_b", lambda: K.abedul(302)),
    ("V09_Arbusto_a", lambda: K.arbusto(401)), ("V10_Arbusto_b", lambda: K.arbusto(402)),
    ("V11_Arbusto_c", lambda: K.arbusto(403)),
    ("V12_Roca_a", lambda: K.roca(501)), ("V13_Roca_b", lambda: K.roca(502)), ("V14_Roca_c", lambda: K.roca(503)),
    ("V15_Hierba_a", lambda: K.mata_hierba(601)), ("V16_Hierba_b", lambda: K.mata_hierba(602)),
    ("V17_Flores_a", lambda: K.mata_flores(701)), ("V18_Flores_b", lambda: K.mata_flores(702)),
    ("V19_Flores_c", lambda: K.mata_flores(703)), ("V20_Flor_Arbol", lambda: K.arbol_flor(801)),
]
TIPO = {n.split("_", 1)[1]: i for i, (n, _) in enumerate(FUENTES_VEG)}


def grupo_instancias(col_fuentes):
    ng = bpy.data.node_groups.new("Instanciar_Vegetacion", "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    n, l = ng.nodes, ng.links
    gi, go = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    ci = n.new("GeometryNodeCollectionInfo")
    ci.inputs["Collection"].default_value = col_fuentes
    ci.inputs["Separate Children"].default_value = True
    ci.inputs["Reset Children"].default_value = True
    iop = n.new("GeometryNodeInstanceOnPoints")
    iop.inputs["Pick Instance"].default_value = True
    l.new(gi.outputs[0], iop.inputs["Points"])
    l.new(ci.outputs[0], iop.inputs["Instance"])
    for nombre, tipo, entrada in (("tipo", "INT", "Instance Index"), ("rot", "QUATERNION", "Rotation"),
                                  ("escala", "FLOAT_VECTOR", "Scale")):
        na = n.new("GeometryNodeInputNamedAttribute")
        na.data_type = tipo
        na.inputs["Name"].default_value = nombre
        l.new(na.outputs[0], iop.inputs[entrada])
    l.new(iop.outputs[0], go.inputs[0])
    return ng


def nube(nombre, P, tipo, quat, escala, col, ng):
    me = bpy.data.meshes.new(nombre)
    me.vertices.add(len(P))
    me.vertices.foreach_set("co", P.astype(np.float32).ravel())
    a = me.attributes.new("tipo", "INT", "POINT")
    a.data.foreach_set("value", tipo.astype(np.int32))
    a = me.attributes.new("rot", "QUATERNION", "POINT")
    a.data.foreach_set("value", quat.astype(np.float32).ravel())
    a = me.attributes.new("escala", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", escala.astype(np.float32).ravel())
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    mod = ob.modifiers.new("Instancias", "NODES")
    mod.node_group = ng
    return ob


def cuaterniones(d, giro, inclinacion, rng):
    """Cuaternión (w, x, y, z) que lleva Z al vector d (con una pequeña inclinación) y gira alrededor de él."""
    from mathutils import Euler, Vector

    out = np.zeros((len(d), 4))
    for i in range(len(d)):
        q = Vector(d[i]).to_track_quat("Z", "Y")
        q2 = q @ Euler((inclinacion[i, 0], inclinacion[i, 1], giro[i]), "XYZ").to_quaternion()
        out[i] = (q2.w, q2.x, q2.y, q2.z)
    return out


def vegetacion(V, col, mats, rapido=False):
    t0 = time.time()
    col_f = coleccion("Fuentes_Vegetacion", col)
    for nombre, fn in FUENTES_VEG:
        ob = fn().a_blender(nombre, mats, col_f)
    capa_coleccion(col_f.name).exclude = True  # las fuentes no se ven: solo sus instancias
    ng = grupo_instancias(col_f)
    rng = np.random.default_rng(99)

    # ------------------------------------------------ árboles, arbustos y rocas: rejilla con jitter de 8 studs
    paso = 12.0 if rapido else 8.0
    g = np.arange(-geo.L + paso / 2, geo.L, paso)
    X, Y = np.meshgrid(g, g)
    X = X + rng.uniform(-paso * 0.45, paso * 0.45, X.shape)
    Y = Y + rng.uniform(-paso * 0.45, paso * 0.45, Y.shape)
    x, y = X.ravel(), Y.ravel()
    H = V.altura(x, y)
    e = 1.5
    gx = (V.altura(x + e, y) - V.altura(x - e, y)) / (2 * e)
    gy = (V.altura(x, y + e) - V.altura(x, y - e)) / (2 * e)
    pend = np.degrees(np.arctan(np.hypot(gx, gy)))
    dens = V.densidad_bosque(x, y)
    lib = V.libre(x, y)
    campos = V.mascara_campos(x, y)
    for nombre in D.SITIOS:
        _, _, _, sd = V.peso_sitio(nombre, x, y)
        lib *= geo.suavizar(sd, 25.0, 60.0)
    dr, ir = V.rio.cercano(x, y)
    orilla = dr - V.rio.m[ir, 3]
    sotos = geo.suavizar(V.fbm2(x, y, 130.0, 2, capa=20), 0.5, 0.62)  # bosquetes sueltos
    ok = (H > 2.5) & (pend < 33) & (lib > 0.5)
    u = rng.uniform(size=x.size)
    p_arbol = (dens ** 1.2) * 0.62 + D.ARBOLES_SUELTOS * (1 - dens) + 0.06 * sotos * (1 - dens) + 0.08 * (
        (orilla > 5) & (orilla < 38))
    p_arbol *= (1 - 0.9 * campos)
    p_arbusto = 0.10 * geo.suavizar(dens, 0.08, 0.3) * geo.suavizar(dens, 0.7, 0.4) + 0.006 + 0.03 * ((orilla > 4) & (
        orilla < 30))
    p_roca = 0.035 * geo.suavizar(pend, 14, 24) + 0.0015 + 0.02 * ((orilla > 1) & (orilla < 10))
    sel_a = ok & (u < p_arbol)
    sel_b = ok & ~sel_a & (u < p_arbol + p_arbusto)
    sel_r = (H > 1.0) & (pend < 45) & (lib > 0.3) & ~sel_a & ~sel_b & (u < p_arbol + p_arbusto + p_roca)
    tipo = np.full(x.size, -1)
    alto_pino = H > 58
    r2 = rng.uniform(size=x.size)
    pinar = V.fbm2(x, y, 400.0, 2, capa=21) > 0.1
    es_pino = sel_a & ((alto_pino & (r2 < 0.75)) | (pinar & (r2 < 0.55)) | (r2 < 0.12))
    es_abedul = sel_a & ~es_pino & ((orilla < 45) & (r2 < 0.5) | (r2 > 0.85))
    es_frond = sel_a & ~es_pino & ~es_abedul
    k = rng.integers(0, 4, x.size)
    tipo[es_frond] = TIPO["Frondoso_a"] + k[es_frond]
    tipo[es_pino] = TIPO["Pino_a"] + (k[es_pino] % 3)
    tipo[es_abedul] = TIPO["Abedul_a"] + (k[es_abedul] % 2)
    tipo[sel_b] = TIPO["Arbusto_a"] + (k[sel_b] % 3)
    tipo[sel_r] = TIPO["Roca_a"] + (k[sel_r] % 3)
    m = tipo >= 0
    esc = rng.uniform(0.78, 1.28, x.size)
    esc[sel_r] = rng.uniform(0.5, 1.6, sel_r.sum())
    _colocar_nube("Vegetacion_Arboles", x[m], y[m], H[m] - 0.3, tipo[m], esc[m], col, ng, rng)
    print(f"vegetación: {int(sel_a.sum())} árboles, {int(sel_b.sum())} arbustos, {int(sel_r.sum())} rocas "
          f"({time.time() - t0:.1f} s)")
    return ng


def _colocar_nube(nombre, x, y, h, tipo, esc, col, ng, rng, inclinacion=0.05):
    d = geo.direccion(x, y)
    P = d * (R + h)[:, None]
    giro = rng.uniform(0, 2 * np.pi, len(x))
    incl = rng.normal(0, inclinacion, (len(x), 2))
    q = cuaterniones(d, giro, incl, rng)
    escala = np.repeat(esc[:, None], 3, axis=1)
    return nube(nombre, P, tipo, q, escala, col, ng)


def hierba(V, col, ng, centros, rapido=False):
    """Matas de hierba y flores alrededor de los sitios y del mirador (para las vistas a ras de suelo)."""
    rng = np.random.default_rng(123)
    xs, ys = [], []
    paso = 4.0 if rapido else 2.6
    for (cx, cy, r) in centros:
        g = np.arange(-r, r, paso)
        X, Y = np.meshgrid(g, g)
        X = X + rng.uniform(-paso / 2, paso / 2, X.shape)
        Y = Y + rng.uniform(-paso / 2, paso / 2, Y.shape)
        dentro = np.hypot(X, Y) < r * (0.75 + 0.25 * rng.uniform(size=X.shape))
        xs.append(cx + X[dentro])
        ys.append(cy + Y[dentro])
    x, y = np.concatenate(xs), np.concatenate(ys)
    H = V.altura(x, y)
    lib = V.libre(x, y)
    for nombre in D.SITIOS:
        _, _, _, sd = V.peso_sitio(nombre, x, y)
        lib *= geo.suavizar(sd, 1.0, 6.0)
    campos = V.mascara_campos(x, y)
    mancha = V.fbm2(x, y, 30.0, 2, capa=22)
    ok = (H > 2.5) & (lib > 0.6) & (campos < 0.3) & (rng.uniform(size=x.size) < 0.55 + 0.45 * mancha)
    x, y, H = x[ok], y[ok], H[ok]
    flores = V.fbm2(x, y, 60.0, 2, capa=23) > 0.2
    k = rng.integers(0, 3, x.size)
    tipo = np.where(flores & (rng.uniform(size=x.size) < 0.5), TIPO["Flores_a"] + k, TIPO["Hierba_a"] + (k % 2))
    esc = rng.uniform(0.7, 1.3, x.size)
    _colocar_nube("Vegetacion_Hierba", x, y, H - 0.15, tipo, esc, col, ng, rng, inclinacion=0.12)
    print(f"hierba: {x.size} matas")


# ==============================================================================================================
# Puente, mirador y cruce
# ==============================================================================================================


def puente_y_detalles(V, C, col, mats):
    nombre = "Aurora_Pradoverde"
    pl = V.caminos[nombre]
    _, i = pl.arbol.query([D.PUENTE["x"], D.PUENTE["y"]])
    # longitud: tramo del camino (medido sobre su curva) donde el terreno queda por debajo del perfil del camino
    j = np.arange(max(i - 80, 0), min(i + 80, len(pl.xy)))
    h = V.altura(pl.xy[j, 0].copy(), pl.xy[j, 1].copy())
    bajo = j[h < V.perfiles[nombre][j] - 0.8]
    sa, sb = pl.s[bajo.min()], pl.s[bajo.max()]
    largo = float(sb - sa) + 14.0
    k = int(np.argmin(np.abs(pl.s - (sa + sb) / 2)))
    cx, cy = pl.xy[k]
    tdir = pl.xy[min(k + 3, len(pl.xy) - 1)] - pl.xy[max(k - 3, 0)]
    tdir /= np.linalg.norm(tdir)
    alto_tablero = float(V.perfiles[nombre][k])
    nivel = float(V.rio.m[V.rio.arbol.query([cx, cy])[1], 2])
    alto_arco = alto_tablero - nivel + 1.5
    arcos = 3 if largo > 50 else 2
    m = K.puente(largo, 13.0, alto_arco, arcos)
    ob = m.a_blender("Puente_del_Alba", mats, col)
    d = geo.direccion(cx, cy)
    e, n, _ = geo.marco(d)
    giro = math.degrees(math.atan2(tdir[1], tdir[0]))
    ob.matrix_world = matriz_local(d, e, giro, alto_tablero)
    print(f"puente: {largo:.0f} studs, {arcos} ojos, tablero a {alto_tablero:.1f}, agua a {nivel:.1f}")

    # mirador de la colina del atardecer
    mx, my = D.MIRADOR
    dm = geo.direccion(mx, my)
    em, nm, _ = geo.marco(dm)

    def en(u, v):
        p = dm * R + u * em + v * nm
        return p / np.linalg.norm(p)

    C.pieza("Arbol_Grande", en(6.0, 10.0), em, 40.0, -0.5, col=col, nombre_obj="Mirador_Arbol")
    C.pieza("Banco", en(-6.0, 2.0), em, -90.0, col=col, nombre_obj="Mirador_Banco")  # mira al oeste
    C.pieza("Banco", en(-6.0, -6.0), em, -90.0, col=col, nombre_obj="Mirador_Banco_2")
    for k in range(5):  # murete a la espalda (este): el oeste queda abierto para ver el atardecer
        a = math.radians(-40 + k * 20)
        C.pieza("Valla_Piedra", en(16 * math.cos(a), 16 * math.sin(a)), em, math.degrees(a) + 90, col=col,
                nombre_obj=f"Mirador_Muro_{k}")
    C.pieza("Poste_Indicador", en(10.0, -6.0), em, 0.0, col=col, nombre_obj="Mirador_Poste")
    C.pieza("Farola", en(4.0, -10.0), em, 0.0, col=col, nombre_obj="Mirador_Farola")
    # cruce de caminos
    cx, cy = D.CRUCE
    dcr = geo.direccion(cx + 9, cy + 9)
    C.pieza("Poste_Indicador", dcr, geo.marco(dcr)[0], 20.0, col=col, nombre_obj="Cruce_Poste")


# ==============================================================================================================


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--cuadros", type=int, default=1024)
    ap.add_argument("--textura", type=int, default=4096)
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--reusar-textura", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    if a.rapido:
        a.cuadros, a.textura = 256, 1024
    t0 = time.time()
    E.limpiar()
    mats = MAT.todos()
    V = RV.Valle()
    print(f"alturas de los sitios: { {k: round(v, 1) for k, v in V.alturas_sitio.items()} }")
    T = PB.todos()
    T["LosMolinos"].parcelas = filtrar_parcelas(V, "LosMolinos", T["LosMolinos"].parcelas)
    print(f"trazados listos ({time.time() - t0:.0f} s)")

    ruta_tex = os.path.abspath(os.path.join(a.salida, "textura_terreno.png"))
    if not (a.reusar_textura and os.path.exists(ruta_tex)):
        img, _ = TX.pintar(V, T, a.textura)
        Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(ruta_tex, optimize=True)
        print(f"textura: {a.textura}² ({os.path.getsize(ruta_tex) / 1e6:.1f} MB, {time.time() - t0:.0f} s)")

    raiz = coleccion("Region1_Valle_del_Alba")
    c_ter = coleccion("Terreno", raiz)
    c_agua = coleccion("Agua", raiz)
    c_ref = coleccion("Referencia_no_exportar")
    terreno(V, a.cuadros, ruta_tex, c_ter)
    rio(V, c_agua)
    resto_planeta(V, c_ref, 48 if a.rapido else 96)
    mar(c_ref)
    C = Constructor(V, mats, raiz)
    for nombre, t in T.items():
        C.sitio(nombre, t, coleccion(nombre, raiz))
    cultivos(V, "LosMolinos", T["LosMolinos"].parcelas, coleccion("Campos", raiz), mats)
    c_det = coleccion("Caminos_Puente_Mirador", raiz)
    puente_y_detalles(V, C, c_det, mats)
    c_veg = coleccion("Vegetacion", raiz)
    ng = vegetacion(V, c_veg, mats, a.rapido)
    centros = [(s["x"], s["y"], 260.0 if n != "Aurora" else 330.0) for n, s in D.SITIOS.items()]
    centros += [(D.MIRADOR[0], D.MIRADOR[1], 160.0), (D.PUENTE["x"], D.PUENTE["y"], 120.0)]
    hierba(V, c_veg, ng, centros, a.rapido)
    ruta = os.path.abspath(os.path.join(a.salida, "region1_valle_del_alba.blend"))
    bpy.ops.wm.save_as_mainfile(filepath=ruta, compress=True)
    print(f"guardado {ruta} ({os.path.getsize(ruta) / 1e6:.1f} MB) en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
