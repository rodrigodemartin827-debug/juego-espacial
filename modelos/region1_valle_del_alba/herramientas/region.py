"""
Construye la escena de la región 1 (Valle del Alba) en Blender y la guarda en region1_valle_del_alba.blend:

  * Terreno de la cara YP partido en 8 × 8 TROZOS, cada uno en versión detallada y simple (con un faldón que tapa
    las grietas entre trozos de distinto detalle) y con su textura (16 de 1024 para los detallados, una para los
    simples).
  * El resto del planeta (5 caras, baja resolución, con el relieve del planeta de prueba) y el mar: SOLO DE REFERENCIA
    para los renders, no son parte de la región.
  * Río, charca del manantial, puente, caminos (en la textura), mirador de la colina del atardecer.
  * Aurora, Pradoverde y Los Molinos: cada edificio es un grupo de COPIAS de las piezas del kit (colección
    Kit_Piezas, oculta), con su color de instancia; igual el mobiliario. Aurora tiene además su silueta (una malla).
  * Todo lo que tiene LOD lleva propiedades («lod», «pieza», «centro», «radio») que usa lod.py en cada render.
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
from malla import Malla, T  # noqa: E402
import atlas as AT  # noqa: E402

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


def material_terreno(ruta_imagen, nombre="Terreno_Valle"):
    mat = bpy.data.materials.new(nombre)
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


def _rejilla_trozo(P, uv, nombre, col, mat, faldon, normales):
    """Malla de un trozo de terreno: la rejilla P (n+1, n+1, 3) y un faldón que baja `faldon` studs por los cuatro
    bordes (tapa las grietas con los trozos vecinos cuando tienen otro nivel de detalle).

    Las normales de la superficie son las EXACTAS del relieve (`normales`, calculadas sobre la rejilla de toda la
    cara): así dos trozos vecinos tienen la misma normal en su borde y no se ve la junta. El faldón tiene sus propios
    vértices (no toca el sombreado de la superficie)."""
    n1 = P.shape[0]
    idx = np.arange(n1 * n1).reshape(n1, n1)
    a, b, c_, d = idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:], idx[:-1, :-1]
    quads = [np.stack([a, b, c_, d], -1).reshape(-1, 4)]
    verts = [P.reshape(-1, 3)]
    uvs = [uv.reshape(-1, 2)]
    borde = np.concatenate([idx[0, :], idx[1:, -1], idx[-1, -2::-1], idx[-2:0:-1, 0]])  # vuelta al trozo
    Pb = P.reshape(-1, 3)[borde]
    abajo = Pb - Pb / np.linalg.norm(Pb, axis=1, keepdims=True) * faldon
    nb = len(borde)
    arriba = n1 * n1  # copia de los vértices del borde, solo para el faldón
    base = arriba + nb
    verts += [Pb, abajo]
    uvs += [uv.reshape(-1, 2)[borde], uv.reshape(-1, 2)[borde]]
    k = np.arange(nb)
    k2 = (k + 1) % nb
    faldones = np.stack([arriba + k2, arriba + k, base + k, base + k2], -1)
    V = np.concatenate(verts)
    # el faldón mira hacia fuera del trozo (Roblox no dibuja el dorso de las caras)
    q = V[faldones[0]]
    nrm = np.cross(q[1] - q[0], q[2] - q[0])
    fuera = q[:2].mean(axis=0) - P.reshape(-1, 3).mean(axis=0)
    if np.dot(nrm, fuera) < 0:
        faldones = faldones[:, ::-1]
    quads.append(faldones)
    Q = np.concatenate(quads)
    me = bpy.data.meshes.new(nombre)
    me.vertices.add(len(V))
    me.vertices.foreach_set("co", V.astype(np.float32).ravel())
    me.loops.add(Q.size)
    me.loops.foreach_set("vertex_index", Q.ravel().astype(np.int32))
    me.polygons.add(len(Q))
    me.polygons.foreach_set("loop_start", np.arange(0, Q.size, 4, dtype=np.int32))
    me.polygons.foreach_set("use_smooth", np.full(len(Q), True))
    capa = me.uv_layers.new(name="UVMap")
    capa.data.foreach_set("uv", np.concatenate(uvs)[Q.ravel()].astype(np.float32).ravel())
    me.update(calc_edges=True)
    # normales exactas en la superficie; en el faldón, la normal hacia fuera
    nv = np.concatenate([normales.reshape(-1, 3), np.zeros((2 * nb, 3))])
    for kk in range(nb):
        q = V[faldones[kk]]
        nf = np.cross(q[1] - q[0], q[2] - q[0])
        nf /= max(np.linalg.norm(nf), 1e-9)
        nv[arriba + kk] += nf
        nv[arriba + (kk + 1) % nb] += nf
        nv[base + kk] += nf
        nv[base + (kk + 1) % nb] += nf
    nv[arriba:] /= np.maximum(np.linalg.norm(nv[arriba:], axis=1, keepdims=True), 1e-9)
    me.normals_split_custom_set_from_vertices(nv.tolist())
    me.materials.append(mat)
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    return ob


def texturas_terreno(ruta_4096, carpeta, k_tex=4):
    """Parte la textura de 4096 en k_tex × k_tex de 1024 (para los trozos detallados) y hace una de 1024 para toda la
    cara (para los simples). Devuelve las rutas."""
    os.makedirs(carpeta, exist_ok=True)
    img = Image.open(ruta_4096).convert("RGB")
    n = img.width // k_tex
    rutas = {}
    for i in range(k_tex):  # fila (norte -> sur)
        for j in range(k_tex):
            r = os.path.join(carpeta, f"terreno_{i}_{j}.png")
            img.crop((j * n, i * n, (j + 1) * n, (i + 1) * n)).save(r, optimize=True)
            rutas[(i, j)] = r
    r = os.path.join(carpeta, "terreno_lejos.png")
    img.resize((1024, 1024), Image.LANCZOS).save(r, optimize=True)
    rutas["lejos"] = r
    return rutas


def terreno(V, rutas_tex, col, rapido=False):
    """Los 64 trozos de terreno, detallados y simples."""
    t0 = time.time()
    cfg = D.TERRENO_TROZOS
    k = cfg["trozos"]
    nd = cfg["cuadros_detalle"] if not rapido else 24
    ns = cfg["cuadros_simple"]
    mats_d = {}
    k_tex = 4
    for key, ruta in rutas_tex.items():
        mats_d[key] = material_terreno(ruta, f"Terreno_{key[0]}_{key[1]}" if key != "lejos" else "Terreno_Lejos")
    alturas = {}
    for nivel, n in (("detalle", nd), ("lejos", ns)):
        N = k * n
        g = np.linspace(-geo.L, geo.L, N + 1)
        X, Y = np.meshgrid(g, g[::-1])  # fila 0 = norte
        H = V.altura(X, Y)
        alturas[nivel] = (X, Y, H)
        d = geo.direccion(X, Y)
        P = d * (R + H)[..., None]
        # normales exactas: producto vectorial de las tangentes de la rejilla de TODA la cara (diferencias
        # centradas; en los bordes de la cara, laterales). Iguales a los dos lados de cada junta entre trozos.
        tx = np.gradient(P, axis=1)
        ty = np.gradient(P, axis=0)
        Nrm = np.cross(tx, -ty)
        Nrm /= np.linalg.norm(Nrm, axis=-1, keepdims=True)
        Nrm *= np.sign(np.sum(Nrm * d, axis=-1))[..., None]
        for i in range(k):  # fila
            for j in range(k):  # columna
                sl = (slice(i * n, (i + 1) * n + 1), slice(j * n, (j + 1) * n + 1))
                Xs, Ys = X[sl], Y[sl]
                if nivel == "detalle":
                    ti, tj = i * k_tex // k, j * k_tex // k
                    lado = 2 * geo.L / k_tex
                    x0 = -geo.L + tj * lado
                    y0 = geo.L - (ti + 1) * lado
                    uv = np.stack([(Xs - x0) / lado, (Ys - y0) / lado], -1)
                    mat = mats_d[(ti, tj)]
                    nombre = f"Terreno_{i}_{j}"
                else:
                    uv = np.stack([(Xs + geo.L) / (2 * geo.L), (Ys + geo.L) / (2 * geo.L)], -1)
                    mat = mats_d["lejos"]
                    nombre = f"Terreno_{i}_{j}__lejos"
                ob = _rejilla_trozo(P[sl], uv, nombre, col, mat, cfg["faldon"], Nrm[sl])
                c = P[sl].reshape(-1, 3)
                centro = c.mean(axis=0)
                ob["lod"] = "terreno"
                ob["nivel"] = nivel
                ob["trozo"] = f"{i}_{j}"
                ob["centro"] = [float(v) for v in centro]
                ob["radio"] = float(np.linalg.norm(c - centro, axis=1).max())
                ob["triangulos"] = len(ob.data.polygons) * 2
    print(f"terreno: {k}x{k} trozos de {nd}² (detalle) y {ns}² (lejos) cuadros, {time.time() - t0:.1f} s")
    return alturas


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


class Biblioteca:
    """Las mallas del kit en Blender (detallada y simple de cada pieza), una vez cada una, y sus copias."""

    def __init__(self, mats, col):
        self.mats = mats
        self.col = col  # colección Kit_Piezas (oculta en el render): un objeto por malla, para tenerlas a mano
        self.mallas = {}

    def malla(self, nombre, lejos=False):
        k = (nombre, lejos)
        if k not in self.mallas:
            _, sim, _, _ = K.PIEZAS[nombre]
            if lejos and sim is None:
                self.mallas[k] = self.malla(nombre, False)
            elif lejos and sim is K.SIN_LEJOS:
                self.mallas[k] = None
            else:
                m = K.malla(nombre, lejos)
                ob = m.a_blender(f"K_{nombre}" + ("__lejos" if lejos else ""), self.mats, self.col)
                ob.data.name = ob.name
                ob["pieza"] = nombre
                self.mallas[k] = ob.data
        return self.mallas[k]

    def copia(self, nombre, matriz, color=None, padre=None, col=None, nombre_obj=None):
        """Una copia de la pieza: objeto que usa la malla compartida, con su color de instancia."""
        me = self.malla(nombre)
        self.malla(nombre, True)
        ob = bpy.data.objects.new(nombre_obj or nombre, me)
        c = MAT.srgb_a_lineal(color or K.color_defecto(nombre))
        ob.color = (*c, 1.0)
        ob["color"] = (color or K.color_defecto(nombre)).upper()  # el color exacto (sRGB), para exportar
        ob["pieza"] = nombre
        if K.PIEZAS[nombre][1] is K.SIN_LEJOS:
            ob["sin_lejos"] = True  # de lejos no se dibuja
        (col or self.col).objects.link(ob)
        if padre is not None:
            ob.parent = padre
            ob.matrix_parent_inverse = Matrix.Identity(4)
            ob.matrix_basis = Matrix(np.asarray(matriz).tolist())
        else:
            ob.matrix_world = Matrix(np.asarray(matriz).tolist())
        return ob


def _vacio(nombre, matriz, col, lod, centro_local, radio):
    e = bpy.data.objects.new(nombre, None)
    e.empty_display_size = 2.0
    e.matrix_world = matriz
    col.objects.link(e)
    e["lod"] = lod
    c = np.array(matriz) @ np.array([*centro_local, 1.0])
    e["centro"] = [float(v) for v in c[:3]]
    e["radio"] = float(radio)
    return e


def categoria_grupo(nombre):
    if nombre in ("Torre_Reloj", "Molino", "Molino_B", "Molino_C", "Fuente", "Portal_Ciudad"):
        return "edificios"
    if nombre.startswith(("Arbol", "Arbusto", "Frondoso")):
        return "vegetacion"
    return "mobiliario"


class Constructor:
    """Coloca las cosas de los sitios: edificios (grupos de piezas) y objetos de GRUPOS."""

    def __init__(self, V, bib, col_raiz):
        self.V, self.bib = V, bib
        self.col_raiz = col_raiz

    def altura(self, d):
        x, y = geo.diseno(d)
        return float(self.V.altura(np.array([x]), np.array([y]))[0])

    def grupo(self, nombre, d, este, giro, dz=0.0, escala=1.0, col=None, nombre_obj=None, alto=None, sitio=""):
        """Un objeto de GRUPOS (una o varias piezas) apoyado en el terreno en la dirección d."""
        h = self.altura(d) if alto is None else alto
        mw = matriz_local(d, este, giro, h + dz) @ Matrix.Scale(escala, 4)
        piezas = PB.GRUPOS[nombre]
        col = col or self.col_raiz
        lod = categoria_grupo(nombre)
        if len(piezas) == 1:
            p, ml, c = piezas[0]
            ob = self.bib.copia(p, np.array(mw) @ ml, c, col=col, nombre_obj=nombre_obj or nombre)
            ob["lod"] = lod
            me = self.bib.malla(p)
            cl = _centro_malla(me)
            c3 = np.array(ob.matrix_world) @ np.array([*cl[0], 1.0])
            ob["centro"] = [float(v) for v in c3[:3]]
            ob["radio"] = float(cl[1] * escala)
            ob["sitio"] = sitio
            return ob
        radio = 40.0 * escala if nombre.startswith(("Molino", "Torre")) else 15.0 * escala
        centro = (0, 0, 30.0) if nombre.startswith(("Molino", "Torre")) else (0, 0, 5.0)
        e = _vacio(nombre_obj or nombre, mw, col, lod, centro, radio)
        e["sitio"] = sitio
        for k, (p, ml, c) in enumerate(piezas):
            self.bib.copia(p, ml, c, padre=e, col=col, nombre_obj=f"{e.name}.{p}")
        return e

    def edificio(self, nombre, ed, mw, col, sitio):
        centro = (ed.ancho / 2, ed.fondo / 2, ed.alto / 2)
        radio = 0.5 * math.sqrt(ed.ancho ** 2 + ed.fondo ** 2 + ed.alto ** 2)
        e = _vacio(nombre, mw, col, "edificios", centro, radio)
        e["sitio"] = sitio
        e["ancho"], e["fondo"], e["alto"] = ed.ancho, ed.fondo, ed.alto
        for k, (p, ml, c) in enumerate(ed.piezas):
            self.bib.copia(p, ml, c, padre=e, col=col, nombre_obj=f"{nombre}.{k:03d}")
        return e

    def sitio(self, nombre, t, col):
        s = self.V.sitios[nombre]
        h_sitio = self.V.alturas_sitio[nombre]
        col_ed = coleccion(f"{nombre}_Edificios", col)
        col_pz = coleccion(f"{nombre}_Mobiliario", col)
        n_ed = n_p = 0
        for cl in t.colocaciones:
            d = s.direccion(np.array(cl.u), np.array(cl.v))
            if cl.tipo == "edificio":
                self.edificio(cl.nombre, cl.edificio, matriz_local(d, s.este, cl.giro, h_sitio + 0.35), col_ed,
                              nombre)
                n_ed += 1
            else:
                dz = cl.dz - (0.4 if cl.pieza.startswith("Arb") else 0.0)
                self.grupo(cl.pieza, d, s.este, cl.giro, dz, cl.escala, col_pz, nombre_obj=f"{nombre}_{cl.nombre}",
                           sitio=nombre)
                n_p += 1
        print(f"{nombre}: {n_ed} edificios, {n_p} objetos sueltos")


_CENTROS = {}


def _centro_malla(me):
    """(centro, radio) de la caja de una malla, en sus coordenadas locales."""
    if me.name not in _CENTROS:
        co = np.zeros(len(me.vertices) * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        lo, hi = co.min(axis=0), co.max(axis=0)
        _CENTROS[me.name] = ((lo + hi) / 2, float(np.linalg.norm(hi - lo) / 2))
    return _CENTROS[me.name]


def silueta_aurora(V, t, col, mats):
    """Silueta de Aurora para verla de lejos: cada edificio es una caja con fachada pintada y su tejado a dos aguas,
    y la torre del reloj una caja con chapitel. Una sola malla, con casillas opacas del atlas."""
    s = V.sitios["Aurora"]
    h = V.alturas_sitio["Aurora"]
    m_obj = np.array(matriz_local(s.centro, s.este, 0.0, h))
    inv = np.linalg.inv(m_obj)
    m = Malla()
    from kit import cara

    for cl in t.colocaciones:
        d = s.direccion(np.array(cl.u), np.array(cl.v))
        if cl.tipo == "edificio":
            ed = cl.edificio
            W, Dp = ed.ancho, ed.fondo
            zt = ed.ztop
            mw = inv @ np.array(matriz_local(d, s.este, cl.giro, h + 0.35))
            b = Malla()
            for (p0, p1, n) in (((0, 0), (W, 0), (0, -1, 0)), ((W, 0), (W, Dp), (1, 0, 0)), ((W, Dp), (0, Dp), (0, 1, 0)),
                                ((0, Dp), (0, 0), (-1, 0, 0))):
                cara(b, [(*p0, -1.0), (*p1, -1.0), (*p1, zt), (*p0, zt)], n, "silueta_fachada")
            sube = Dp / 2 * K.PEND
            for lado in (-1, 1):
                y0 = -1.0 if lado < 0 else Dp + 1.0
                cara(b, [(-0.8, y0, zt - 0.6), (W + 0.8, y0, zt - 0.6), (W + 0.8, Dp / 2, zt + sube),
                         (-0.8, Dp / 2, zt + sube)], (0, lado, 1), "silueta_teja")
            for x, nx in ((0.0, -1), (W, 1)):
                cara(b, [(x, 0, zt), (x, Dp, zt), (x, Dp / 2, zt + sube)], (nx, 0, 0), "silueta_fachada")
            m.anadir(b, mw)
        elif cl.pieza == "Torre_Reloj":
            mw = inv @ np.array(matriz_local(d, s.este, cl.giro, h))
            b = Malla()
            for r in (0, 90, 180, 270):
                f = Malla()
                cara(f, [(-7, -7, 0), (7, -7, 0), (7, -7, 67), (-7, -7, 67)], (0, -1, 0), "silueta_fachada")
                cara(f, [(-8.4, -8.4, 67), (8.4, -8.4, 67), (0, 0, 92)], (0, -1, 0.5), "silueta_teja")
                b.anadir(f, np.array(Matrix.Rotation(math.radians(r), 4, "Z")))
            m.anadir(b, mw)
    ob = m.a_blender("Aurora_Silueta", mats, col)
    ob.matrix_world = Matrix(m_obj.tolist())
    ob.color = (1, 1, 1, 1)
    ob["lod"] = "silueta"
    ob["sitio"] = "Aurora"
    c = s.centro * (R + h)
    ob["centro"] = [float(v) for v in c]
    ob["radio"] = 300.0
    print(f"silueta de Aurora: {ob['triangulos']} triángulos")
    return ob


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
    """Hileras de cultivo apoyadas en el terreno (una malla para todo el campo; el surco fino está en la textura)."""
    s = V.sitios[nombre]
    rng = np.random.default_rng(5)
    m = Malla()
    altos = {"trigo": (2.4, 2.6, "trigo"), "col": (1.4, 2.2, "col"), "lavanda": (1.9, 2.0, "flores"),
             "calabaza": (0.9, 2.4, "col"), "arado": (0.6, 2.4, "tierra_arada")}
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
        bs = np.linspace(-p["largo"] / 2 + 1.5, p["largo"] / 2 - 1.5, 6)
        for a in filas:
            u = cu + a * ea[0] + bs * eb[0]
            v = cv + a * ea[1] + bs * eb[1]
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
                m.poligono([izq[k], izq[k + 1], top[k + 1], top[k]], mat)
                m.poligono([der[k + 1], der[k], top[k], top[k + 1]], mat)
            if cult == "calabaza":
                for k in range(len(bs)):
                    if rng.uniform() < 0.6:
                        m.esfera(top[k] + ua[k] * rng.uniform(-0.8, 0.8), 0.95, "calabaza", sub=0)
    ob = m.a_blender(f"{nombre}_Cultivos", mats, col)
    ob.color = (1, 1, 1, 1)
    ob["lod"] = "campos"
    co = np.array([v.co for v in ob.data.vertices])
    c = co.mean(axis=0)
    ob["centro"] = [float(v) for v in c]
    ob["radio"] = float(np.linalg.norm(co - c, axis=1).max())
    print(f"cultivos: {len(parcelas)} parcelas, {ob['triangulos']} triángulos")


# ==============================================================================================================
# Vegetación instanciada
# ==============================================================================================================

# Piezas de vegetación instanciadas con Geometry Nodes (el orden fija el índice «tipo»). En la colección de fuentes
# van primero las detalladas (índices 0..n-1) y luego las simples (n..2n-1): el LOD cambia el índice.
FUENTES_VEG = ["Frondoso_a", "Frondoso_b", "Frondoso_c", "Frondoso_d", "Pino_a", "Pino_b", "Pino_c", "Abedul_a",
               "Abedul_b", "Arbusto_a", "Arbusto_b", "Arbusto_c", "Roca_a", "Roca_b", "Roca_c", "Hierba_a",
               "Hierba_b", "Flores_a", "Flores_b", "Flores_c", "Arbol_Flor"]
TIPO = {n: i for i, n in enumerate(FUENTES_VEG)}
NV = len(FUENTES_VEG)


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
    # se borran los puntos marcados como «oculto» (los que el LOD no dibuja)
    borrar = n.new("GeometryNodeDeleteGeometry")
    borrar.domain = "POINT"
    oc = n.new("GeometryNodeInputNamedAttribute")
    oc.data_type = "BOOLEAN"
    oc.inputs["Name"].default_value = "oculto"
    l.new(gi.outputs[0], borrar.inputs["Geometry"])
    l.new(oc.outputs[0], borrar.inputs["Selection"])
    iop = n.new("GeometryNodeInstanceOnPoints")
    iop.inputs["Pick Instance"].default_value = True
    l.new(borrar.outputs[0], iop.inputs["Points"])
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
    a = me.attributes.new("tipo_base", "INT", "POINT")
    a.data.foreach_set("value", tipo.astype(np.int32))
    a = me.attributes.new("oculto", "BOOLEAN", "POINT")
    a.data.foreach_set("value", np.zeros(len(P), bool))
    a = me.attributes.new("rot", "QUATERNION", "POINT")
    a.data.foreach_set("value", quat.astype(np.float32).ravel())
    a = me.attributes.new("escala", "FLOAT_VECTOR", "POINT")
    a.data.foreach_set("vector", escala.astype(np.float32).ravel())
    ob = bpy.data.objects.new(nombre, me)
    col.objects.link(ob)
    mod = ob.modifiers.new("Instancias", "NODES")
    mod.node_group = ng
    ob["lod"] = "nube"
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


def vegetacion(V, col, bib, rapido=False):
    t0 = time.time()
    col_f = coleccion("Fuentes_Vegetacion", col)
    vacia = bpy.data.meshes.new("Vacia")
    for lejos in (False, True):
        for i, nombre in enumerate(FUENTES_VEG):
            me = bib.malla(nombre, lejos) or vacia
            ob = bpy.data.objects.new(f"V{i + NV * lejos:02d}_{nombre}" + ("__lejos" if lejos else ""), me)
            col_f.objects.link(ob)
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
    p_roca = D.ROCAS_LADERA * geo.suavizar(pend, 16, 26) + 0.001 + 0.02 * ((orilla > 1) & (orilla < 10))
    lejos_mirador = np.hypot(x - D.MIRADOR[0], y - D.MIRADOR[1]) > D.MIRADOR_LIBRE
    lib = lib * lejos_mirador
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
    ob = _colocar_nube("Vegetacion_Arboles", x[m], y[m], H[m] - 0.3, tipo[m], esc[m], col, ng, rng)
    ob["categoria"] = "vegetacion"
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
    lib *= np.hypot(x - D.MIRADOR[0], y - D.MIRADOR[1]) > D.TERRAZA_MIRADOR["radio"] + 6  # la terraza, despejada
    mancha = V.fbm2(x, y, 30.0, 2, capa=22)
    ok = (H > 2.5) & (lib > 0.6) & (campos < 0.3) & (rng.uniform(size=x.size) < 0.55 + 0.45 * mancha)
    x, y, H = x[ok], y[ok], H[ok]
    flores = V.fbm2(x, y, 60.0, 2, capa=23) > 0.2
    k = rng.integers(0, 3, x.size)
    tipo = np.where(flores & (rng.uniform(size=x.size) < 0.5), TIPO["Flores_a"] + k, TIPO["Hierba_a"] + (k % 2))
    esc = rng.uniform(0.7, 1.3, x.size)
    ob = _colocar_nube("Vegetacion_Hierba", x, y, H - 0.15, tipo, esc, col, ng, rng, inclinacion=0.12)
    ob["categoria"] = "hierba"
    print(f"hierba: {x.size} matas")


# ==============================================================================================================
# Puente, mirador y cruce
# ==============================================================================================================


def puente_y_detalles(V, C, col):
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
    K.registrar_puente(largo, alto_arco, arcos)
    PB.GRUPOS["Puente"] = [("Puente", np.eye(4), None)] + [
        ("Farola", T(sx * (largo / 2 + 1.5), sy * (13.0 / 2 - 0.7), 4.2) @ np.diag([10 / 12] * 3 + [1]), None)
        for sx in (-1, 1) for sy in (-1, 1)]
    d = geo.direccion(cx, cy)
    e, n, _ = geo.marco(d)
    giro = math.degrees(math.atan2(tdir[1], tdir[0]))
    C.grupo("Puente", d, e, giro, alto=alto_tablero, col=col, nombre_obj="Puente_del_Alba")
    print(f"puente: {largo:.0f} studs, {arcos} ojos, tablero a {alto_tablero:.1f}, agua a {nivel:.1f}")

    # mirador de la colina del atardecer
    mx, my = D.MIRADOR
    dm = geo.direccion(mx, my)
    em, nm, _ = geo.marco(dm)

    def en(u, v):
        p = dm * R + u * em + v * nm
        return p / np.linalg.norm(p)

    C.grupo("Arbol_Grande", en(-6.0, 19.0), em, 40.0, -0.5, col=col, nombre_obj="Mirador_Arbol")
    C.grupo("Banco", en(-6.0, 2.0), em, -90.0, col=col, nombre_obj="Mirador_Banco")  # mira al oeste
    C.grupo("Banco", en(-6.0, -6.0), em, -90.0, col=col, nombre_obj="Mirador_Banco_2")
    for k in range(5):  # murete a la espalda (este): el oeste queda abierto para ver el atardecer
        a = math.radians(-40 + k * 20)
        C.grupo("Valla_Piedra", en(16 * math.cos(a), 16 * math.sin(a)), em, math.degrees(a) + 90, col=col,
                nombre_obj=f"Mirador_Muro_{k}")
    C.grupo("Poste_Indicador", en(8.0, -15.0), em, 0.0, col=col, nombre_obj="Mirador_Poste")
    C.grupo("Farola", en(4.0, -10.0), em, 0.0, col=col, nombre_obj="Mirador_Farola")
    cx, cy = D.CRUCE
    dcr = geo.direccion(cx + 9, cy + 9)
    C.grupo("Poste_Indicador", dcr, geo.marco(dcr)[0], 20.0, col=col, nombre_obj="Cruce_Poste")


# ==============================================================================================================


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--textura", type=int, default=4096)
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--reusar-textura", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    if a.rapido:
        a.textura = 1024
    t0 = time.time()
    E.limpiar()
    mats = MAT.todos()
    carpeta_tex = os.path.abspath(os.path.join(a.salida, "texturas"))
    ruta_atlas, ruta_datos = AT.generar(carpeta_tex)
    mats["Atlas_Kit"] = MAT.material_atlas(ruta_atlas, ruta_datos)
    V = RV.Valle()
    print(f"alturas de los sitios: { {k: round(v, 1) for k, v in V.alturas_sitio.items()} }")
    T = PB.todos()
    T["LosMolinos"].parcelas = filtrar_parcelas(V, "LosMolinos", T["LosMolinos"].parcelas)
    print(f"trazados listos ({time.time() - t0:.0f} s)")

    ruta_tex = os.path.join(carpeta_tex, "textura_terreno_4096.png")
    if not (a.reusar_textura and os.path.exists(ruta_tex)):
        img, _ = TX.pintar(V, T, a.textura)
        Image.fromarray((img * 255 + 0.5).astype(np.uint8)).save(ruta_tex, optimize=True)
        print(f"textura: {a.textura}² ({time.time() - t0:.0f} s)")
    rutas_tex = texturas_terreno(ruta_tex, carpeta_tex)

    raiz = coleccion("Region1_Valle_del_Alba")
    c_kit = coleccion("Kit_Piezas", raiz)
    capa_coleccion(c_kit.name).exclude = True
    bib = Biblioteca(mats, c_kit)
    c_ter = coleccion("Terreno", raiz)
    c_agua = coleccion("Agua", raiz)
    c_ref = coleccion("Referencia_no_exportar")
    terreno(V, rutas_tex, c_ter, a.rapido)
    rio(V, c_agua)
    resto_planeta(V, c_ref, 48 if a.rapido else 96)
    mar(c_ref)
    C = Constructor(V, bib, raiz)
    for nombre, t in T.items():
        C.sitio(nombre, t, coleccion(nombre, raiz))
    silueta_aurora(V, T["Aurora"], coleccion("Aurora_Silueta", raiz), mats)
    cultivos(V, "LosMolinos", T["LosMolinos"].parcelas, coleccion("Campos", raiz), mats)
    c_det = coleccion("Caminos_Puente_Mirador", raiz)
    puente_y_detalles(V, C, c_det)
    c_veg = coleccion("Vegetacion", raiz)
    ng = vegetacion(V, c_veg, bib, a.rapido)
    centros = [(s["x"], s["y"], 260.0 if n != "Aurora" else 330.0) for n, s in D.SITIOS.items()]
    centros += [(D.MIRADOR[0], D.MIRADOR[1], 160.0), (D.PUENTE["x"], D.PUENTE["y"], 120.0)]
    hierba(V, c_veg, ng, centros, a.rapido)
    txt = bpy.data.texts.new("LOD")  # marca: esta escena tiene niveles de detalle (render.py aplica lod.py)
    txt.write("Niveles de detalle: ver herramientas/lod.py y diseno.LOD")
    ruta = os.path.abspath(os.path.join(a.salida, "region1_valle_del_alba.blend"))
    for img in bpy.data.images:  # rutas relativas al .blend: la carpeta se puede mover o clonar
        if img.filepath:
            img.filepath = bpy.path.relpath(img.filepath, start=os.path.dirname(ruta))
    bpy.context.preferences.filepaths.save_version = 0  # sin copia .blend1
    bpy.ops.wm.save_as_mainfile(filepath=ruta, compress=True)
    print(f"guardado {ruta} ({os.path.getsize(ruta) / 1e6:.1f} MB) en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
