"""
Taller común de las bestias cósmicas (Blender sin pantalla, bpy).

Unidades: 1 unidad de Blender = 1 stud. La escena usa `scale_length = 0.28` (1 stud = 0,28 m, la conversión del
importador 3D de Roblox), así el FBX se escribe en metros con "Apply Scalings: FBX All" y llega a Studio con su
tamaño en studs.

Cada bestia se construye así:
  * Piezas rígidas del rig (`Pieza`): una malla "alta" (la superficie orgánica fina, con su detalle de relieve y sus
    materiales procedurales) y una "baja" (la que se exporta, dentro del presupuesto de triángulos).
  * La geometría de detalle (escamas, dientes, arnés...) va en las dos mallas, así el horneado de normales de alta a
    baja solo transporta el relieve fino de la piel.
  * Todas las bajas comparten un único atlas de 2048×2048 (color, normales, rugosidad, metal y emisión).
  * El origen de cada pieza está en su articulación (pivote del Motor6D) y su rotación es 0,0,0.
  * Antes de exportar se aplica GIRO_IMPORTACION: 180° alrededor del eje vertical (Y de Roblox, Z de Blender).
"""

import json
import math
import os

import bpy  # noqa: F401  (antes que bmesh y mathutils)
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree
from PIL import Image, ImageDraw, ImageFont

STUD_EN_METROS = 0.28
TAM_ATLAS = 2048
GIRO_IMPORTACION = math.pi  # 180° en el eje vertical antes de exportar
SEPARACION = 0.02  # studs entre piezas del rig
FUERZA_EMISION_RENDER = 6.0  # brillo de la emisión en los renders (cada bestia puede cambiarlo)

# --------------------------------------------------------------------------------------------------------------
# Escena y mallas
# --------------------------------------------------------------------------------------------------------------


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = STUD_EN_METROS
    scn.world = bpy.data.worlds.new("mundo")
    return scn


def coleccion(nombre):
    col = bpy.data.collections.get(nombre)
    if col is None:
        col = bpy.data.collections.new(nombre)
        bpy.context.scene.collection.children.link(col)
    return col


def malla_numpy(nombre, verts, caras, col=None):
    """Objeto de malla a partir de arrays numpy (vértices en studs, caras triangulares)."""
    me = bpy.data.meshes.new(nombre)
    nv, nf = len(verts), len(caras)
    me.vertices.add(nv)
    me.vertices.foreach_set("co", np.asarray(verts, dtype=np.float32).ravel())
    me.loops.add(nf * 3)
    me.loops.foreach_set("vertex_index", np.asarray(caras, dtype=np.int32).ravel())
    me.polygons.add(nf)
    me.polygons.foreach_set("loop_start", np.arange(0, nf * 3, 3, dtype=np.int32))
    me.update(calc_edges=True)
    me.validate(clean_customdata=False)
    obj = bpy.data.objects.new(nombre, me)
    (col or bpy.context.scene.collection).objects.link(obj)
    return obj


def activar(obj, solo=True):
    if solo:
        for o in bpy.context.selected_objects:
            o.select_set(False)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)


def aplicar_modificadores(obj):
    activar(obj)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def normales_fuera(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()


def suave(obj, angulo=None):
    """Sombreado suave (con corte por ángulo si se da)."""
    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    if angulo is not None:
        activar(obj)
        bpy.ops.object.shade_auto_smooth(angle=math.radians(angulo))
        aplicar_modificadores(obj)
    obj.data.update()


def triangulos(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def suavizar_laplace(obj, factor=0.5, repes=2):
    mod = obj.modifiers.new("suave", "SMOOTH")
    mod.factor = factor
    mod.iterations = repes
    aplicar_modificadores(obj)


def diezmar(obj, tris_objetivo, nombre=None, triangular=True):
    """Copia diezmada de `obj` hasta ~tris_objetivo triángulos (colapso de aristas, conserva la silueta)."""
    nuevo = obj.copy()
    nuevo.data = obj.data.copy()
    nuevo.name = nombre or obj.name + "_baja"
    for c in obj.users_collection:
        c.objects.link(nuevo)
    actual = triangulos(nuevo)
    if actual > tris_objetivo:
        mod = nuevo.modifiers.new("diezmar", "DECIMATE")
        mod.decimate_type = "COLLAPSE"
        mod.ratio = tris_objetivo / actual
        mod.use_collapse_triangulate = triangular
        aplicar_modificadores(nuevo)
    limpiar_degeneradas(nuevo)
    return nuevo


def limpiar_degeneradas(obj, dist=2e-4):
    """Quita caras de área ~0 (el FBX las descarta y el recuento dejaría de cuadrar)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=dist)
    bmesh.ops.dissolve_degenerate(bm, dist=dist, edges=bm.edges[:])
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    malas = [f for f in bm.faces if f.calc_area() < 1e-9]
    if malas:
        bmesh.ops.delete(bm, geom=malas, context="FACES")
    bm.to_mesh(obj.data)
    bm.free()


def unir(objetos, nombre):
    """Une varios objetos en uno (el primero recibe la geometría)."""
    objetos = [o for o in objetos if o is not None]
    base = objetos[0]
    if len(objetos) > 1:
        for o in bpy.context.selected_objects:
            o.select_set(False)
        for o in objetos:
            o.select_set(True)
        bpy.context.view_layer.objects.active = base
        bpy.ops.object.join()
    base.name = nombre
    base.data.name = nombre
    return base


def copiar(obj, nombre):
    nuevo = obj.copy()
    nuevo.data = obj.data.copy()
    nuevo.name = nombre
    for c in obj.users_collection:
        c.objects.link(nuevo)
    return nuevo


def poner_origen(obj, punto):
    """Mueve el origen del objeto al punto (studs, mundo) sin mover la geometría. Rotación 0."""
    p = Vector(punto)
    mw = obj.matrix_world.copy()
    obj.data.transform(Matrix.Translation(mw.translation - p))
    obj.matrix_world = Matrix.Translation(p)


def bvh_de(objetos):
    """Árbol BVH en coordenadas de mundo de varios objetos (para proyectar detalles sobre la piel)."""
    verts, polys = [], []
    for o in objetos:
        base = len(verts)
        mw = o.matrix_world
        verts.extend(mw @ v.co for v in o.data.vertices)
        polys.extend([base + i for i in p.vertices] for p in o.data.polygons)
    return BVHTree.FromPolygons(verts, polys)


# --------------------------------------------------------------------------------------------------------------
# Geometría de detalle (bmesh en studs con materiales por nombre)
# --------------------------------------------------------------------------------------------------------------


class Geo:
    """Acumula geometría en un bmesh. Cada cara lleva un material por nombre y cada vértice un atributo `aux`
    (vector 3D libre: coordenadas locales para que los materiales procedurales dibujen costuras, espirales...)."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.aux = self.bm.verts.layers.float_vector.new("aux")
        self.mats = []

    def m(self, nombre):
        if nombre not in self.mats:
            self.mats.append(nombre)
        return self.mats.index(nombre)

    def v(self, p, aux=(0, 0, 0)):
        vv = self.bm.verts.new(Vector(p))
        vv[self.aux] = Vector(aux)
        return vv

    def cara(self, verts, mat):
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return None
        f.material_index = self.m(mat)
        return f

    def loft(self, anillos, mat, tapar_inicio=True, tapar_fin=True, cerrado=True, auxs=None, punta_inicio=None,
             punta_fin=None):
        """Une anillos de puntos (todos con el mismo número). `auxs`: lista paralela con el aux de cada punto.
        `punta_*`: en vez de tapa plana, un vértice (abanico) en ese punto."""
        vs = []
        for k, a in enumerate(anillos):
            fila = []
            for i, p in enumerate(a):
                fila.append(self.v(p, auxs[k][i] if auxs else (0, 0, 0)))
            vs.append(fila)
        n = len(anillos[0])
        tramos = n if cerrado else n - 1
        for k in range(len(vs) - 1):
            for i in range(tramos):
                j = (i + 1) % n
                self.cara((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]), mat)
        if cerrado:
            if punta_inicio is not None:
                c = self.v(punta_inicio[0], punta_inicio[1])
                for i in range(n):
                    self.cara((vs[0][(i + 1) % n], vs[0][i], c), mat)
            elif tapar_inicio:
                self.cara(list(reversed(vs[0])), mat)
            if punta_fin is not None:
                c = self.v(punta_fin[0], punta_fin[1])
                for i in range(n):
                    self.cara((vs[-1][i], vs[-1][(i + 1) % n], c), mat)
            elif tapar_fin:
                self.cara(vs[-1], mat)
        return vs

    def tubo(self, puntos, radios, mat, lados=8, achatado=1.0, arriba=(0, 0, 1), tapas=True, punta=False,
             aux_fn=None, giro=0.0, perfil=None):
        """Tubo por una curva (lista de Vector) con radio variable. `perfil(i, a)` -> factor de radio opcional.
        `aux_fn(t, a)` -> aux de cada vértice (t: 0..1 a lo largo, a: ángulo)."""
        puntos = [Vector(p) for p in puntos]
        n = len(puntos)
        largo = [0.0]
        for i in range(1, n):
            largo.append(largo[-1] + (puntos[i] - puntos[i - 1]).length)
        total = max(largo[-1], 1e-6)
        anillos, auxs = [], []
        ref = Vector(arriba).normalized()
        for i, p in enumerate(puntos):
            if i == 0:
                t = (puntos[1] - puntos[0]).normalized()
            elif i == n - 1:
                t = (puntos[-1] - puntos[-2]).normalized()
            else:
                t = (puntos[i + 1] - puntos[i - 1]).normalized()
            lado = t.cross(ref)
            if lado.length < 1e-4:
                lado = t.cross(Vector((1, 0, 0)))
            lado.normalize()
            arr = lado.cross(t).normalized()
            anillo, aux = [], []
            for k in range(lados):
                a = giro + math.tau * k / lados
                f = perfil(i, a) if perfil else 1.0
                r = radios[i] * f
                anillo.append(p + lado * math.cos(a) * r + arr * math.sin(a) * r * achatado)
                aux.append(aux_fn(largo[i] / total, a) if aux_fn else (largo[i] / total, a / math.tau, 0))
            anillos.append(anillo)
            auxs.append(aux)
        pf = None
        if punta:
            d = (puntos[-1] - puntos[-2]).normalized()
            pf = (puntos[-1] + d * radios[-1] * 0.9, aux_fn(1.0, 0) if aux_fn else (1.0, 0, 0))
        return self.loft(anillos, mat, tapar_inicio=tapas, tapar_fin=tapas and not punta, auxs=auxs, punta_fin=pf)

    def elipsoide(self, c, r, mat, seg=12, anillos=8, rot=None, aux=(0, 0, 0)):
        """Elipsoide UV (rot: Matrix 3x3 opcional)."""
        c = Vector(c)
        rot = rot or Matrix.Identity(3)
        filas = []
        for j in range(1, anillos):
            th = math.pi * j / anillos
            fila = []
            for i in range(seg):
                ph = math.tau * i / seg
                p = Vector((math.sin(th) * math.cos(ph) * r[0], math.sin(th) * math.sin(ph) * r[1],
                            math.cos(th) * r[2]))
                fila.append(c + rot @ p)
            filas.append(fila)
        polo_n = (c + rot @ Vector((0, 0, r[2])), aux)
        polo_s = (c + rot @ Vector((0, 0, -r[2])), aux)
        auxs = [[aux] * seg for _ in filas]
        # El loft "empieza" arriba: la punta de inicio va en el polo norte con orientación invertida.
        vs = self.loft(filas, mat, auxs=auxs, punta_inicio=polo_n, punta_fin=polo_s)
        return vs

    def caja_redonda(self, c, tam, mat, rot=None, seg=2, aux=(0, 0, 0), redondeo=0.4):
        """Caja con aristas suavizadas (cubo subdividido y empujado hacia una superelipse)."""
        c = Vector(c)
        rot = rot or Matrix.Identity(3)
        bm2 = bmesh.new()
        bmesh.ops.create_cube(bm2, size=2.0)
        bmesh.ops.subdivide_edges(bm2, edges=bm2.edges[:], cuts=seg, use_grid_fill=True)
        mapa = {}
        for v in bm2.verts:
            p = v.co.copy() / 2.0 * 2.0
            # Cojín: las caras quedan en su sitio y las esquinas se recogen hacia la esfera.
            q = p * (1 - redondeo) + p.normalized() * redondeo
            p2 = Vector((q.x * tam[0] / 2, q.y * tam[1] / 2, q.z * tam[2] / 2))
            mapa[v] = self.v(c + rot @ p2, aux)
        for f in bm2.faces:
            self.cara([mapa[v] for v in f.verts], mat)
        bm2.free()

    def transformar(self, verts, matriz):
        bmesh.ops.transform(self.bm, matrix=matriz, verts=list(verts))

    def objeto(self, materiales, col=None):
        """Crea el objeto (studs). `materiales`: dict nombre -> material de Blender."""
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        ngons = [f for f in self.bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(self.bm, faces=ngons)
        me = bpy.data.meshes.new(self.nombre)
        self.bm.to_mesh(me)
        self.bm.free()
        obj = bpy.data.objects.new(self.nombre, me)
        (col or bpy.context.scene.collection).objects.link(obj)
        for n in self.mats:
            me.materials.append(materiales[n])
        return obj


def asignar_material(obj, mat):
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    for p in obj.data.polygons:
        p.material_index = 0


def unir_materiales(objetos):
    """Tras unir objetos con materiales distintos, Blender ya mantiene los índices. Esto deja una lista única."""
    return objetos


# --------------------------------------------------------------------------------------------------------------
# Materiales procedurales (para hornear)
# --------------------------------------------------------------------------------------------------------------


def srgb(hexa):
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


class Nodos:
    """Ayuda para escribir árboles de nodos de material con menos ruido."""

    def __init__(self, mat):
        self.mat = mat
        mat.use_nodes = True
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self.salida = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.bsdf = self.nt.nodes.new("ShaderNodeBsdfPrincipled")
        self.nt.links.new(self.bsdf.outputs["BSDF"], self.salida.inputs["Surface"])
        self._geo = None
        self._attr = {}

    def n(self, tipo, **props):
        nodo = self.nt.nodes.new(tipo)
        for k, v in props.items():
            setattr(nodo, k, v)
        return nodo

    def enlazar(self, salida, entrada):
        self.nt.links.new(salida, entrada)

    def geo(self):
        if self._geo is None:
            self._geo = self.n("ShaderNodeNewGeometry")
        return self._geo

    def pos(self):
        return self.geo().outputs["Position"]

    def normal(self):
        return self.geo().outputs["Normal"]

    def atributo(self, nombre):
        if nombre not in self._attr:
            a = self.n("ShaderNodeAttribute")
            a.attribute_type = "GEOMETRY"
            a.attribute_name = nombre
            self._attr[nombre] = a
        return self._attr[nombre]

    def sep(self, vec):
        s = self.n("ShaderNodeSeparateXYZ")
        self.enlazar(vec, s.inputs[0])
        return s.outputs

    def mate(self, op, a, b=None, c=None, clamp=False):
        m = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                m.inputs[i].default_value = x
            else:
                self.enlazar(x, m.inputs[i])
        return m.outputs[0]

    def vmate(self, op, a, b=None, escala=None):
        m = self.n("ShaderNodeVectorMath", operation=op)
        for i, x in enumerate((a, b)):
            if x is None:
                continue
            if isinstance(x, (tuple, list)):
                m.inputs[i].default_value = x
            else:
                self.enlazar(x, m.inputs[i])
        if escala is not None:
            m.inputs["Scale"].default_value = escala
        return m.outputs[0] if op not in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else m.outputs["Value"]

    def mezcla(self, fac, a, b, modo="MIX"):
        m = self.n("ShaderNodeMix", data_type="RGBA", blend_type=modo)
        for i, (sock, x) in enumerate(((m.inputs["Factor"], fac), (m.inputs["A"], a), (m.inputs["B"], b))):
            if isinstance(x, (int, float)):
                sock.default_value = x if i == 0 else (x, x, x, 1.0)
            elif isinstance(x, tuple):
                sock.default_value = (*x[:3], 1.0) if len(x) >= 3 else x
            else:
                self.enlazar(x, sock)
        return m.outputs["Result"]

    def rampa(self, fac, puntos):
        """puntos: [(pos, (r,g,b))] o [(pos, valor)]."""
        r = self.n("ShaderNodeValToRGB")
        if isinstance(fac, (int, float)):
            r.inputs[0].default_value = fac
        else:
            self.enlazar(fac, r.inputs[0])
        els = r.color_ramp.elements
        while len(els) < len(puntos):
            els.new(0.5)
        for e, (p, col) in zip(els, puntos):
            e.position = p
            if isinstance(col, (int, float)):
                e.color = (col, col, col, 1)
            else:
                e.color = (*col[:3], 1)
        return r.outputs["Color"]

    def ruido(self, vec, escala, detalle=4.0, rugosidad=0.55, dim="3D"):
        r = self.n("ShaderNodeTexNoise")
        r.noise_dimensions = dim
        r.inputs["Scale"].default_value = escala
        r.inputs["Detail"].default_value = detalle
        r.inputs["Roughness"].default_value = rugosidad
        if vec is not None:
            self.enlazar(vec, r.inputs["Vector"])
        return r.outputs["Fac"]

    def voronoi(self, vec, escala, rasgo="F1", salida="Distance", aleatorio=1.0, metrica="EUCLIDEAN"):
        r = self.n("ShaderNodeTexVoronoi")
        r.feature = rasgo
        r.distance = metrica
        r.inputs["Scale"].default_value = escala
        if "Randomness" in r.inputs:
            r.inputs["Randomness"].default_value = aleatorio
        if vec is not None:
            self.enlazar(vec, r.inputs["Vector"])
        return r.outputs[salida]

    def imagen(self, img, vec, cerca=False):
        t = self.n("ShaderNodeTexImage")
        t.image = img
        t.interpolation = "Closest" if cerca else "Linear"
        t.extension = "CLIP"
        self.enlazar(vec, t.inputs["Vector"])
        return t.outputs["Color"]

    def combinar(self, x, y, z):
        c = self.n("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            if isinstance(v, (int, float)):
                c.inputs[i].default_value = v
            else:
                self.enlazar(v, c.inputs[i])
        return c.outputs[0]

    def relieve(self, altura, fuerza=1.0, distancia=0.05, normal=None):
        b = self.n("ShaderNodeBump")
        b.inputs["Strength"].default_value = fuerza
        b.inputs["Distance"].default_value = distancia
        self.enlazar(altura, b.inputs["Height"])
        if normal is not None:
            self.enlazar(normal, b.inputs["Normal"])
        return b.outputs["Normal"]

    def poner(self, nombre, valor):
        """Conecta (o fija) una entrada del Principled."""
        sock = self.bsdf.inputs[nombre]
        if isinstance(valor, (int, float)):
            sock.default_value = valor
        elif isinstance(valor, tuple):
            sock.default_value = (*valor[:3], 1.0) if len(sock.default_value) == 4 else valor
        else:
            self.enlazar(valor, sock)


def material_simple(nombre, color, rug=0.5, metal=0.0, emision=None, fuerza=0.0, relieve=None):
    """Material sencillo; `relieve` = (escala_ruido, fuerza) añade un bump de ruido."""
    mat = bpy.data.materials.new(nombre)
    N = Nodos(mat)
    N.poner("Base Color", color)
    N.poner("Roughness", rug)
    N.poner("Metallic", metal)
    if emision is not None:
        N.poner("Emission Color", emision)
        N.poner("Emission Strength", fuerza)
    if relieve:
        N.poner("Normal", N.relieve(N.ruido(N.pos(), relieve[0], 6), fuerza=relieve[1], distancia=0.02))
    mat.diffuse_color = (*color, 1)
    return mat, N


# --------------------------------------------------------------------------------------------------------------
# UV del atlas y horneado
# --------------------------------------------------------------------------------------------------------------


def uv_proyeccion_superior(obj, caras_idx=None, nombre_uv="UVMap"):
    """UV por proyección cenital: caras que miran arriba en una isla (XY) y las que miran abajo en otra (espejada
    para que no salga invertida). Ideal para discos y membranas: islas grandes, sin costuras en el lomo."""
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name=nombre_uv)
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.active
    mw = obj.matrix_world
    sel = set(caras_idx) if caras_idx is not None else None
    for f in bm.faces:
        if sel is not None and f.index not in sel:
            continue
        nz = (mw.to_3x3() @ f.normal).z
        for lo in f.loops:
            p = mw @ lo.vert.co
            if nz >= 0:
                lo[uv].uv = (p.x, p.y)
            else:
                lo[uv].uv = (-p.x + 1000.0, p.y)  # isla aparte (se recoloca al empaquetar)
    bm.to_mesh(me)
    bm.free()


def desplegar_piezas(piezas, prioridad=None, margen=0.004):
    """
    UV de todas las piezas en un único atlas:
      1) Cada pieza: las caras marcadas como "planas" (atributo de cara 'uv_plano' = 1) por proyección cenital y
         el resto con Smart UV Project.
      2) Se iguala la densidad de píxeles de todas las islas, se agrandan las de las zonas prioritarias
         (`prioridad`: dict nombre_pieza -> factor) y se empaquetan todas juntas.
    """
    for o in piezas:
        me = o.data
        if not me.uv_layers:
            me.uv_layers.new(name="UVMap")
        plano = me.attributes.get("uv_plano")
        planas = [i for i, v in enumerate(plano.data) if v.value > 0.5] if plano else []
        resto = set(range(len(me.polygons))) - set(planas)
        if resto:
            activar(o)
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="DESELECT")
            bpy.ops.object.mode_set(mode="OBJECT")
            for i in resto:
                me.polygons[i].select = True
            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, scale_to_bounds=False,
                                     area_weight=0.0)
            bpy.ops.object.mode_set(mode="OBJECT")
        if planas:
            uv_proyeccion_superior(o, planas)

    # Todas a la vez en modo edición multiobjeto.
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for o in piezas:
        o.select_set(True)
    bpy.context.view_layer.objects.active = piezas[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    bpy.ops.object.mode_set(mode="OBJECT")
    if prioridad:
        for o in piezas:
            f = prioridad.get(o.name, 1.0)
            fac = o.data.attributes.get("uv_prioridad")
            uvl = o.data.uv_layers.active.data
            for p in o.data.polygons:
                k = f * (fac.data[p.index].value if fac else 1.0)
                if k == 1.0:
                    continue
                for li in p.loop_indices:
                    uvl[li].uv = uvl[li].uv * k
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, margin_method="FRACTION", margin=margen,
                            shape_method="CONCAVE", scale=True)
    bpy.ops.object.mode_set(mode="OBJECT")


def imagen_nueva(nombre, color=True, tam=TAM_ATLAS, fondo=(0, 0, 0, 1)):
    img = bpy.data.images.new(nombre, tam, tam, alpha=False, float_buffer=not color)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    img.generated_color = fondo
    return img


def _destino(baja, img):
    for slot in baja.material_slots:
        nt = slot.material.node_tree
        n = nt.nodes.get("destino_horneado") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "destino_horneado"
        n.image = img
        nt.nodes.active = n


def _con_emision_de(mats, fuente):
    """Cambia temporalmente la salida de los materiales por una emisión con el valor de `fuente`
    ('metal' o 'emision') para hornearlo con EMIT. Devuelve una función para deshacerlo."""
    deshacer = []
    for mat in mats:
        nt = mat.node_tree
        out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
        bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        enlace_antes = out.inputs["Surface"].links[0].from_socket if out.inputs["Surface"].links else None
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        if bsdf is not None:
            if fuente == "metal":
                s = bsdf.inputs["Metallic"]
            else:
                s = bsdf.inputs["Emission Color"]
            if s.links:
                nt.links.new(s.links[0].from_socket, em.inputs["Color"])
            else:
                v = s.default_value
                em.inputs["Color"].default_value = (v, v, v, 1) if fuente == "metal" else tuple(v)
            if fuente == "emision":
                st = bsdf.inputs["Emission Strength"]
                fuerza = st.default_value if not st.links else 1.0
                em.inputs["Strength"].default_value = max(fuerza, 0.0)
                if fuerza <= 0:
                    em.inputs["Color"].default_value = (0, 0, 0, 1)
                    for lk in list(em.inputs["Color"].links):
                        nt.links.remove(lk)
        else:
            em.inputs["Color"].default_value = (0, 0, 0, 1)
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
        deshacer.append((nt, out, enlace_antes, em))

    def restaurar():
        for nt, out, antes, em in deshacer:
            nt.nodes.remove(em)
            if antes is not None:
                nt.links.new(antes, out.inputs["Surface"])

    return restaurar


def hornear_atlas(parejas, carpeta, nombre, tam=TAM_ATLAS, muestras=16, extrusion=0.06, distancia=0.2,
                  ao=0.55, distancia_ao=0.6, margen_px=6):
    """
    parejas: [(alta, baja)]. Todas las bajas tienen UV en el mismo atlas. Hornea de cada alta a su baja:
    color (con oclusión suave), normales (espacio tangente), rugosidad, metal y emisión. Guarda los PNG y deja en
    cada baja un único material con el atlas. Devuelve dict de rutas.
    """
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = muestras
    scn.render.bake.use_clear = False
    scn.render.bake.margin = margen_px
    scn.render.bake.margin_type = "EXTEND"

    atlas_mat = bpy.data.materials.new(f"{nombre}_horneo")
    atlas_mat.use_nodes = True
    # Las bajas llevan el material de horneado (solo para indicar el destino).
    for _, baja in parejas:
        asignar_material(baja, atlas_mat)

    imgs = {
        "color": imagen_nueva(f"{nombre}_color", True, tam, (0.05, 0.05, 0.08, 1)),
        "normal": imagen_nueva(f"{nombre}_normal", False, tam, (0.5, 0.5, 1.0, 1)),
        "roughness": imagen_nueva(f"{nombre}_roughness", False, tam, (0.7, 0.7, 0.7, 1)),
        "metalness": imagen_nueva(f"{nombre}_metalness", False, tam, (0, 0, 0, 1)),
        "emision": imagen_nueva(f"{nombre}_emision", True, tam, (0, 0, 0, 1)),
        "ao": imagen_nueva(f"{nombre}_ao", False, tam, (1, 1, 1, 1)),
    }

    ocultas = {}
    for o in scn.objects:
        ocultas[o] = o.hide_render

    def ejecutar(tipo, alta, baja, **kw):
        for o in scn.objects:
            if o.type == "MESH":
                o.hide_render = o not in (alta, baja)
        for o in bpy.context.selected_objects:
            o.select_set(False)
        alta.select_set(True)
        baja.select_set(True)
        bpy.context.view_layer.objects.active = baja
        bpy.ops.object.bake(type=tipo, use_selected_to_active=True, cage_extrusion=extrusion,
                            max_ray_distance=distancia, margin=margen_px, use_clear=False, **kw)

    mats_altas = {s.material for a, _ in parejas for s in a.material_slots if s.material}

    pases = [
        ("color", "DIFFUSE", dict(pass_filter={"COLOR"})),
        ("normal", "NORMAL", dict(normal_space="TANGENT")),
        ("roughness", "ROUGHNESS", {}),
    ]
    for clave, tipo, kw in pases:
        _destino_todas(parejas, imgs[clave])
        for alta, baja in parejas:
            ejecutar(tipo, alta, baja, **kw)
        print(f"[horneo] {clave} listo")

    for clave in ("metalness", "emision"):
        restaurar = _con_emision_de(mats_altas, "metal" if clave == "metalness" else "emision")
        _destino_todas(parejas, imgs[clave])
        for alta, baja in parejas:
            ejecutar("EMIT", alta, baja)
        restaurar()
        print(f"[horneo] {clave} listo")

    if ao > 0:
        scn.world.light_settings.distance = distancia_ao
        _destino_todas(parejas, imgs["ao"])
        for alta, baja in parejas:
            ejecutar("AO", alta, baja)
        _multiplicar_ao(imgs["color"], imgs["ao"], ao)
        print("[horneo] oclusión aplicada al color")

    for o, h in ocultas.items():
        o.hide_render = h

    rutas = {}
    for clave in ("color", "normal", "roughness", "metalness", "emision"):
        img = imgs[clave]
        ruta = os.path.join(carpeta, f"{nombre}_{clave}.png")
        _guardar_png(img, ruta, color=clave in ("color", "emision"))
        rutas[clave] = ruta

    final = material_atlas(nombre, rutas)
    for _, baja in parejas:
        asignar_material(baja, final)
    return rutas, final


def _destino_todas(parejas, img):
    for _, baja in parejas:
        _destino(baja, img)


def _guardar_png(img, ruta, color=True):
    """Guarda en PNG de 8 bits (las imágenes no-color se hornean en float y se convierten aquí)."""
    w, h = img.size
    px = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    rgb = np.clip(px[..., :3], 0, 1)
    if color and img.is_float:
        rgb = np.where(rgb <= 0.0031308, rgb * 12.92, 1.055 * np.power(rgb, 1 / 2.4) - 0.055)
    arr = (np.flipud(rgb) * 255 + 0.5).astype(np.uint8)
    Image.fromarray(arr, "RGB").save(ruta)


def _multiplicar_ao(img_color, img_ao, fuerza):
    w, h = img_color.size
    c = np.array(img_color.pixels[:], dtype=np.float32).reshape(h, w, 4)
    a = np.array(img_ao.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :1]
    factor = 1.0 - fuerza * (1.0 - np.clip(a, 0, 1)) ** 1.4
    c[..., :3] *= factor
    img_color.pixels.foreach_set(c.ravel())
    img_color.update()


def material_atlas(nombre, rutas, fuerza_emision=None):
    fuerza_emision = FUERZA_EMISION_RENDER if fuerza_emision is None else fuerza_emision
    """Material final con las 5 texturas del atlas (lo que se ve en el render y lo que lleva el FBX)."""
    mat = bpy.data.materials.new(f"{nombre}_atlas")
    N = Nodos(mat)
    uv = N.n("ShaderNodeUVMap")

    def tex(clave, color=True):
        img = bpy.data.images.load(rutas[clave], check_existing=False)
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        t = N.n("ShaderNodeTexImage")
        t.image = img
        N.enlazar(uv.outputs["UV"], t.inputs["Vector"])
        return t

    tc = tex("color")
    N.enlazar(tc.outputs["Color"], N.bsdf.inputs["Base Color"])
    tr = tex("roughness", False)
    N.enlazar(tr.outputs["Color"], N.bsdf.inputs["Roughness"])
    tm = tex("metalness", False)
    N.enlazar(tm.outputs["Color"], N.bsdf.inputs["Metallic"])
    tn = tex("normal", False)
    nm = N.n("ShaderNodeNormalMap")
    N.enlazar(tn.outputs["Color"], nm.inputs["Color"])
    N.enlazar(nm.outputs["Normal"], N.bsdf.inputs["Normal"])
    te = tex("emision")
    N.enlazar(te.outputs["Color"], N.bsdf.inputs["Emission Color"])
    N.poner("Emission Strength", fuerza_emision)
    return mat


# --------------------------------------------------------------------------------------------------------------
# Estudio y turnaround de 8 vistas
# --------------------------------------------------------------------------------------------------------------

VISTAS_TURNAROUND = [
    ("Frente", 0, 6),
    ("3/4 Frontal", 45, 20),
    ("Lateral Izq", 90, 5),
    ("3/4 Trasera", 135, 22),
    ("Trasera", 180, 8),
    ("Lateral Der", -90, 5),
    ("Arriba", 0, 89.5),
    ("Abajo", 0, -89.5),
]


def _fuente(tam, negrita=True):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrita else \
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(ruta):
        return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default(tam)


def preparar_estudio(radio_modelo, fondo=(0.02, 0.022, 0.035)):
    """Iluminación de estudio de 3 puntos (clave, relleno y contraluz) más un rebote suave desde abajo."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.world.use_nodes = True
    bg = scn.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (*fondo, 1)
    bg.inputs["Strength"].default_value = 0.6
    k = radio_modelo
    mira = bpy.data.objects.new("Mira_estudio", None)
    scn.collection.objects.link(mira)
    mira["estudio"] = True

    def luz(nombre, energia, pos, color, tam):
        d = bpy.data.lights.new(nombre, "AREA")
        d.energy = energia * k * k
        d.color = color
        d.size = tam * k
        o = bpy.data.objects.new(nombre, d)
        o.location = Vector(pos) * k
        scn.collection.objects.link(o)
        c = o.constraints.new("TRACK_TO")
        c.target = mira
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        o["estudio"] = True
        return o

    # Las luces se mueven con la cámara en cada vista (ver renderizar_turnaround): posiciones en el marco de cámara.
    luz("Luz_Clave", 80, (-1.6, -2.2, 2.0), (1.0, 0.95, 0.88), 1.2)
    luz("Luz_Relleno", 28, (2.4, -1.6, 0.4), (0.72, 0.82, 1.0), 2.0)
    luz("Luz_Contra", 100, (0.6, 2.6, 1.6), (0.75, 0.9, 1.0), 1.0)
    return mira


def renderizar_vistas(objetos, carpeta, vistas, tam=720, muestras=64, prefijo="", margen=1.08, lente=60,
                      centro=None, radio=None):
    scn = bpy.context.scene
    scn.cycles.samples = muestras
    scn.render.resolution_x = scn.render.resolution_y = tam
    scn.render.film_transparent = False
    os.makedirs(carpeta, exist_ok=True)
    estado = {}
    for o in scn.objects:
        if o.type == "MESH":
            estado[o] = o.hide_render
            o.hide_render = o not in objetos
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objetos:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    c = Vector(centro) if centro is not None else (mn + mx) / 2
    r = radio or (mx - mn).length / 2
    mira = bpy.data.objects["Mira_estudio"]
    mira.location = c
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = lente
    cam_d.clip_start = 0.05
    cam_d.clip_end = 5000
    cam = bpy.data.objects.new("cam", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    fov = 2 * math.atan(18 / lente)
    dist = r * margen / math.sin(fov / 2)
    luces = [o for o in scn.objects if o.type == "LIGHT" and o.get("estudio")]
    base = {o.name: o.get("pos_cam") or list(o.location) for o in luces}
    for o in luces:
        o["pos_cam"] = base[o.name]
    rutas = []
    for nombre, az, el in vistas:
        # az: 0 = mirando el frente de la bestia (+Y de modelado), 90 = su lado izquierdo (-X).
        a, e = math.radians(az), math.radians(el)
        d = Vector((-math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = c + d * dist
        arriba = Vector((0, 0, 1)) if abs(el) < 80 else Vector((0, 1 if el > 0 else -1, 0)) * (1 if el > 0 else -1)
        if abs(el) >= 80:
            arriba = Vector((0, 1, 0))
        q = (c - cam.location).to_track_quat("-Z", "Y")
        cam.rotation_euler = q.to_euler()
        if abs(el) >= 80:
            # Vista cenital/nadir: la cabeza hacia arriba de la imagen.
            fwd = (c - cam.location).normalized()
            derecha = fwd.cross(arriba).normalized()
            up = derecha.cross(fwd).normalized()
            m = Matrix((derecha, up, -fwd)).transposed()
            cam.rotation_euler = m.to_euler()
        # Luces en el marco de la cámara: siempre clave arriba-izquierda, contra detrás.
        rot = cam.rotation_euler.to_matrix()
        for o in luces:
            p = Vector(o["pos_cam"])  # x: derecha cámara, y: hacia el modelo, z: arriba cámara
            o.location = c + rot @ Vector((p.x, p.z, -p.y)) * 1.0 + (cam.location - c) * 0.0
        ruta = os.path.join(carpeta, f"{prefijo}{nombre.replace('/', '-').replace(' ', '_')}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        rutas.append((nombre, ruta))
    bpy.data.objects.remove(cam)
    for o, h in estado.items():
        o.hide_render = h
    return rutas


def montar_turnaround(rutas, salida, titulo, notas=(), columnas=4):
    tam = Image.open(rutas[0][1]).size[0]
    filas = math.ceil(len(rutas) / columnas)
    cab = 70 + 22 * len(notas)
    hoja = Image.new("RGB", (columnas * tam, cab + filas * tam), (12, 13, 20))
    d = ImageDraw.Draw(hoja)
    d.text((16, 12), titulo, fill=(61, 242, 255), font=_fuente(30))
    for i, n in enumerate(notas):
        d.text((18, 54 + i * 22), n, fill=(210, 214, 224), font=_fuente(16, False))
    for i, (nombre, ruta) in enumerate(rutas):
        x, y = (i % columnas) * tam, cab + (i // columnas) * tam
        hoja.paste(Image.open(ruta).convert("RGB"), (x, y))
        d.rectangle((x, y, x + tam - 1, y + tam - 1), outline=(40, 44, 60))
        d.text((x + 12, y + 10), nombre, fill=(255, 255, 255), font=_fuente(20))
    hoja.save(salida)
    print("[ok] turnaround:", salida)
    return salida


# --------------------------------------------------------------------------------------------------------------
# Exportación, reimportación y JSON
# --------------------------------------------------------------------------------------------------------------


def a_roblox(p):
    """Coordenadas de modelado (X derecha, Y delante, Z arriba; studs) -> Roblox tras el giro y la exportación:
    la bestia mira a -Z (LookVector de Roblox), arriba es +Y y su derecha es +X."""
    return [round(p[0], 4), round(p[2], 4), round(-p[1], 4)]


def exportar_fbx(ruta, objetos):
    """
    Exporta con GIRO_IMPORTACION (180° en el eje vertical) aplicado a copias de las piezas: se gira la posición
    del origen y la malla, y la rotación queda en 0,0,0. Ejes: arriba = Y, delante = Z; "Apply Scalings: FBX All".
    """
    copias = []
    giro = Matrix.Rotation(GIRO_IMPORTACION, 4, "Z")
    for o in objetos:
        c = o.copy()
        c.data = o.data.copy()
        bpy.context.scene.collection.objects.link(c)
        c.name = o.name  # el original se renombra temporalmente
        copias.append((o, c))
    nombres = {}
    for o, c in copias:
        nombres[o] = o.name
        o.name = o.name + "__orig"
        c.name = nombres[o]
        loc = giro @ o.matrix_world.translation
        c.data.transform(giro.to_3x3().to_4x4())
        c.matrix_world = Matrix.Translation(loc)
    for o in bpy.context.selected_objects:
        o.select_set(False)
    for _, c in copias:
        c.select_set(True)
    bpy.context.view_layer.objects.active = copias[0][1]
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
        embed_textures=True,
        path_mode="COPY",
    )
    for o, c in copias:
        bpy.data.objects.remove(c)
        o.name = nombres[o]
    print("[ok] FBX:", ruta)


def reimportar_y_verificar(ruta_fbx, esperado, tol=0.01):
    """
    Abre el FBX en una escena limpia y comprueba nombres, triángulos y pivotes (deshaciendo escala y giro).
    `esperado`: {nombre: {"pivote": [x,y,z] modelado, "tris": n}}. Devuelve (ok, informe).
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.scale_length = 1.0
    bpy.ops.import_scene.fbx(filepath=ruta_fbx, axis_forward="Z", axis_up="Y", use_custom_normals=True)
    informe = []
    ok = True
    vistos = {o.name: o for o in scn.objects if o.type == "MESH"}
    giro = Matrix.Rotation(-GIRO_IMPORTACION, 4, "Z")
    for nombre, dato in esperado.items():
        o = vistos.get(nombre)
        if o is None:
            ok = False
            informe.append(f"FALTA {nombre}")
            continue
        # Lo importado viene en metros (1 stud = 0,28 m) y con el giro aplicado.
        mw = o.matrix_world
        loc = giro @ (mw.translation / STUD_EN_METROS)
        rot = mw.to_euler()
        esc = mw.to_scale()
        err = (loc - Vector(dato["pivote"])).length
        tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
        rot_ok = all(abs(a) < 1e-3 for a in rot)
        # La escala de objeto puede venir en el objeto o aplicada a la malla: medimos el tamaño real.
        dims = Vector([d for d in o.dimensions]) / STUD_EN_METROS
        linea = (f"{nombre}: pivote err {err:.4f} st, rot {tuple(round(math.degrees(a), 2) for a in rot)}, "
                 f"escala {tuple(round(s, 4) for s in esc)}, tris {tris} (esperado {dato['tris']}), "
                 f"tamaño {dims.x:.2f}×{dims.y:.2f}×{dims.z:.2f} st")
        if err > tol or tris != dato["tris"] or not rot_ok:
            ok = False
            linea = "ERROR " + linea
        informe.append(linea)
    for n in vistos:
        if n not in esperado:
            informe.append(f"(extra en el FBX: {n})")
    return ok, informe


def escribir_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    print("[ok] JSON:", ruta)
