"""
Kit para modelar casas del pueblo con Blender sin pantalla (bpy).

  * Geometría en STUDS (1 unidad de Blender = 1 stud), Z arriba y la fachada mirando a -Y.
  * Cada pieza (`Pieza`) es una malla cerrada con grosor real; las primitivas devuelven listas de vértices y caras
    que se transforman y se añaden a la pieza. Al cerrar la pieza se recalculan las normales hacia fuera, se marca el
    sombreado suave por ángulo y se calcula la UV «fuente» (proyección en caja en studs, o planos normalizados para
    las calcomanías pintadas a mano).
  * Atlas: todas las piezas de un modelo se juntan en unos pocos objetos que comparten UNA textura de 2048². Se
    despliega la UV «atlas» con smart project, se escala cada isla según su importancia (la puerta y el dibujo
    reciben más píxeles; las caras de abajo, menos) y se empaqueta.
  * Horneado: color, rugosidad y metal pasan por un nodo de emisión (así salen exactos, sin luz), la emisión se
    hornea tal cual, las normales recogen el relieve de los nodos Bump, y la oclusión ambiental se multiplica en
    el color con suavidad.
  * Exportación FBX para Roblox: giro de importación (180° en el eje vertical), Apply Scalings = FBX All.
"""

import math
import os

import bpy
import bmesh
import numpy as np
from mathutils import Matrix, Vector

# ----------------------------------------------------------------------------------------------------------------
# Transformaciones
# ----------------------------------------------------------------------------------------------------------------


def T(x=0.0, y=0.0, z=0.0):
    return Matrix.Translation((x, y, z))


def R(eje, grados):
    return Matrix.Rotation(math.radians(grados), 4, eje)


def S(x, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    m = Matrix.Identity(4)
    m[0][0], m[1][1], m[2][2] = x, y, z
    return m


def mirar(origen, destino, arriba=(0, 0, 1)):
    """Matriz que lleva el eje Z local de origen a destino (para cilindros y tubos entre dos puntos)."""
    o, d = Vector(origen), Vector(destino)
    z = (d - o).normalized()
    a = Vector(arriba)
    if abs(z.dot(a)) > 0.98:
        a = Vector((1, 0, 0)) if abs(z.x) < 0.9 else Vector((0, 1, 0))
    x = a.cross(z).normalized()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = o
    return m


# ----------------------------------------------------------------------------------------------------------------
# Primitivas: devuelven (vértices, caras)
# ----------------------------------------------------------------------------------------------------------------


def g_caja(sx, sy, sz):
    """Caja centrada en el origen."""
    x, y, z = sx / 2, sy / 2, sz / 2
    v = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z), (-x, -y, z), (x, -y, z), (x, y, z), (-x, y, z)]
    f = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return v, f


def g_hull(puntos, limpiar=True):
    """Envolvente convexa (con las caras coplanarias fundidas)."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in puntos]
    bmesh.ops.convex_hull(bm, input=vs)
    sueltos = [v for v in bm.verts if not v.link_faces]
    if sueltos:
        bmesh.ops.delete(bm, geom=sueltos, context="VERTS")
    if limpiar:
        bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=bm.verts[:], edges=bm.edges[:])
    bm.verts.index_update()
    v = [tuple(x.co) for x in bm.verts]
    f = [tuple(x.index for x in c.verts) for c in bm.faces]
    bm.free()
    return v, f


def g_caja_bisel(sx, sy, sz, e):
    """Caja con las aristas achaflanadas (un solo segmento: brillo en los cantos, pocos triángulos)."""
    x, y, z = sx / 2, sy / 2, sz / 2
    e = min(e, x * 0.9, y * 0.9, z * 0.9)
    pts = []
    for a in (-1, 1):
        for b in (-1, 1):
            for c in (-1, 1):
                pts += [(a * (x - e), b * y, c * z), (a * x, b * (y - e), c * z), (a * x, b * y, c * (z - e))]
    return g_hull(pts)


def g_cilindro(r, h, lados=12, r2=None, z0=0.0):
    """Cilindro (o tronco de cono) a lo largo de Z, de z0 a z0+h."""
    r2 = r if r2 is None else r2
    v, f = [], []
    for k, (rr, zz) in enumerate(((r, z0), (r2, z0 + h))):
        for i in range(lados):
            a = 2 * math.pi * i / lados
            v.append((rr * math.cos(a), rr * math.sin(a), zz))
    for i in range(lados):
        j = (i + 1) % lados
        f.append((i, j, lados + j, lados + i))
    f.append(tuple(reversed(range(lados))))
    f.append(tuple(range(lados, 2 * lados)))
    return v, f


def g_torno(perfil, lados=12, giro=0.0):
    """
    Sólido de revolución alrededor de Z. `perfil` = [(r, z), ...] empezando y acabando en el eje (r = 0): los
    extremos son polos. Sirve para macetas con grosor, el balón, la parábola de la antena, la lámpara...
    """
    v, f = [], []
    anillos = []
    for (r, z) in perfil:
        if r <= 1e-6:
            v.append((0.0, 0.0, z))
            anillos.append([len(v) - 1])
        else:
            ids = []
            for i in range(lados):
                a = giro + 2 * math.pi * i / lados
                v.append((r * math.cos(a), r * math.sin(a), z))
                ids.append(len(v) - 1)
            anillos.append(ids)
    for a, b in zip(anillos[:-1], anillos[1:]):
        if len(a) == 1 and len(b) == 1:
            continue
        if len(a) == 1:
            for i in range(lados):
                f.append((a[0], b[(i + 1) % lados], b[i]))
        elif len(b) == 1:
            for i in range(lados):
                f.append((a[i], a[(i + 1) % lados], b[0]))
        else:
            for i in range(lados):
                j = (i + 1) % lados
                f.append((a[i], a[j], b[j], b[i]))
    return v, f


def g_toro(perfil, lados=14):
    """Revolución de un perfil CERRADO (lista de (r, z) que no toca el eje): neumáticos, aros."""
    v, f = [], []
    n = len(perfil)
    for i in range(lados):
        a = 2 * math.pi * i / lados
        for (r, z) in perfil:
            v.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(lados):
        i2 = (i + 1) % lados
        for k in range(n):
            k2 = (k + 1) % n
            f.append((i * n + k, i2 * n + k, i2 * n + k2, i * n + k2))
    return v, f


def g_prisma(poligono, z0, z1):
    """Extruye un polígono 2D (XY, puede ser cóncavo) de z0 a z1."""
    n = len(poligono)
    v = [(x, y, z0) for x, y in poligono] + [(x, y, z1) for x, y in poligono]
    f = [tuple(reversed(range(n))), tuple(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        f.append((i, j, n + j, n + i))
    return v, f


def g_tubo(puntos, radio, lados=6, radios=None):
    """Tubo cerrado a lo largo de una polilínea 3D (con marcos que no se retuercen). `radios` opcional por punto."""
    pts = [Vector(p) for p in puntos]
    n = len(pts)
    tang = []
    for i in range(n):
        if i == 0:
            t = pts[1] - pts[0]
        elif i == n - 1:
            t = pts[-1] - pts[-2]
        else:
            t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
        tang.append(t.normalized())
    ref = Vector((0, 0, 1)) if abs(tang[0].z) < 0.9 else Vector((1, 0, 0))
    x = ref.cross(tang[0]).normalized()
    v, f = [], []
    for i in range(n):
        if i > 0:  # transporte paralelo
            x = (x - tang[i] * x.dot(tang[i])).normalized()
        y = tang[i].cross(x)
        r = radios[i] if radios else radio
        # en los codos el anillo se agranda un poco para que el tubo no se estreche
        if 0 < i < n - 1:
            c = (pts[i + 1] - pts[i]).normalized().dot((pts[i] - pts[i - 1]).normalized())
            r = r / max(0.6, math.sqrt((1 + c) / 2))
        for k in range(lados):
            a = 2 * math.pi * k / lados
            v.append(tuple(pts[i] + (x * math.cos(a) + y * math.sin(a)) * r))
    for i in range(n - 1):
        for k in range(lados):
            k2 = (k + 1) % lados
            f.append((i * lados + k, i * lados + k2, (i + 1) * lados + k2, (i + 1) * lados + k))
    f.append(tuple(reversed(range(lados))))
    f.append(tuple(range((n - 1) * lados, n * lados)))
    return v, f


def g_pared(largo, alto, grosor, huecos=(), cortes_u=(), cortes_v=()):
    """
    Pared maciza con huecos rectangulares. Local: u = X (0..largo), v = Z (0..alto); la cara exterior está en y = 0
    y la interior en y = +grosor. Devuelve (vértices, caras, etiquetas) con etiquetas 'ext', 'int', 'borde' o
    'hueco' (los derrames de puertas y ventanas). Es una malla cerrada sin uniones en T.
    """
    us = sorted({0.0, largo, *[h[0] for h in huecos], *[h[2] for h in huecos], *cortes_u})
    vs = sorted({0.0, alto, *[h[1] for h in huecos], *[h[3] for h in huecos], *cortes_v})

    def macizo(i, j):
        if i < 0 or j < 0 or i >= len(us) - 1 or j >= len(vs) - 1:
            return None  # fuera
        cu, cv = (us[i] + us[i + 1]) / 2, (vs[j] + vs[j + 1]) / 2
        return not any(h[0] < cu < h[2] and h[1] < cv < h[3] for h in huecos)

    ids = {}
    v = []

    def vid(i, j, lado):
        k = (i, j, lado)
        if k not in ids:
            ids[k] = len(v)
            v.append((us[i], grosor * lado, vs[j]))
        return ids[k]

    f, tags = [], []
    for i in range(len(us) - 1):
        for j in range(len(vs) - 1):
            if not macizo(i, j):
                continue
            f.append((vid(i, j, 0), vid(i + 1, j, 0), vid(i + 1, j + 1, 0), vid(i, j + 1, 0)))
            tags.append("ext")
            f.append((vid(i, j + 1, 1), vid(i + 1, j + 1, 1), vid(i + 1, j, 1), vid(i, j, 1)))
            tags.append("int")
    # Aristas verticales (entre celdas i-1 e i) y horizontales (entre j-1 y j).
    for i in range(len(us)):
        for j in range(len(vs) - 1):
            a, b = macizo(i - 1, j), macizo(i, j)
            if bool(a) != bool(b):
                hueco = (a is False) or (b is False)
                f.append((vid(i, j, 0), vid(i, j + 1, 0), vid(i, j + 1, 1), vid(i, j, 1)))
                tags.append("hueco" if hueco else "borde")
    for j in range(len(vs)):
        for i in range(len(us) - 1):
            a, b = macizo(i, j - 1), macizo(i, j)
            if bool(a) != bool(b):
                hueco = (a is False) or (b is False)
                f.append((vid(i, j, 0), vid(i + 1, j, 0), vid(i + 1, j, 1), vid(i, j, 1)))
                tags.append("hueco" if hueco else "borde")
    return v, f, tags


def g_estrella(r_ext, r_int, grosor, puntas=5, giro=0.0):
    pol = []
    for i in range(puntas * 2):
        a = giro + math.pi / 2 + i * math.pi / puntas
        r = r_ext if i % 2 == 0 else r_int
        pol.append((math.cos(a) * r, math.sin(a) * r))
    return g_prisma(pol, 0, grosor)


# ----------------------------------------------------------------------------------------------------------------
# Piezas
# ----------------------------------------------------------------------------------------------------------------

PIEZAS = []


class Pieza:
    """
    Una malla cerrada del modelo. `grupo` decide en qué objeto final acaba (casa, puerta, cristal, neon).
    `densidad` multiplica los píxeles que recibe en el atlas. `suave` = ángulo de sombreado suave (None = plano).
    `planos` = {nombre_material: (eje_u, eje_v, origen, tam_u, tam_v)} para las calcomanías: UV fuente normalizada.
    """

    def __init__(self, nombre, grupo="casa", densidad=1.0, suave=None, planos=None):
        self.nombre = nombre
        self.grupo = grupo
        self.densidad = densidad
        self.suave = suave
        self.planos = planos or {}
        self.bm = bmesh.new()
        self.capa_dens = self.bm.faces.layers.float.new("densidad")
        self.mats = []
        self.cerrada = False
        PIEZAS.append(self)

    def idx(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def add(self, geo, mat, M=None, mats_por_cara=None):
        """Añade (vértices, caras[, etiquetas]). `mats_por_cara(i, etiqueta)` permite un material por cara."""
        M = M or Matrix.Identity(4)
        verts, caras = geo[0], geo[1]
        tags = geo[2] if len(geo) > 2 else [None] * len(caras)
        bv = [self.bm.verts.new(M @ Vector(p)) for p in verts]
        nuevas = []
        for i, (c, t) in enumerate(zip(caras, tags)):
            try:
                cara = self.bm.faces.new([bv[k] for k in c])
            except ValueError:
                continue
            m = mats_por_cara(i, t) if mats_por_cara else mat
            cara.material_index = self.idx(m)
            cara[self.capa_dens] = self.densidad
            nuevas.append(cara)
        return nuevas

    def densidad_caras(self, caras, valor):
        """Menos (o más) píxeles para estas caras: p. ej. la cara de arriba del zócalo, tapada por las paredes."""
        for f in caras:
            f[self.capa_dens] = valor

    def cerrar(self):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if self.suave is not None:
            lim = math.radians(self.suave)
            for f in bm.faces:
                f.smooth = True
            for e in bm.edges:
                if len(e.link_faces) == 2:
                    e.smooth = e.calc_face_angle(0) < lim
                else:
                    e.smooth = False
        me = bpy.data.meshes.new(self.nombre)
        bm.to_mesh(me)
        bm.free()
        for m in self.mats:
            me.materials.append(m)
        ob = bpy.data.objects.new(self.nombre, me)
        bpy.context.scene.collection.objects.link(ob)
        ob["grupo"] = self.grupo
        # la densidad por cara (capa «densidad» del bmesh) queda como atributo y sobrevive al unir objetos
        _uv_fuente(ob, self.planos)
        self.obj = ob
        self.cerrada = True
        return ob


def _uv_fuente(ob, planos):
    me = ob.data
    uv = me.uv_layers.new(name="fuente")
    nombres = [m.name for m in me.materials]
    for p in me.polygons:
        n = p.normal
        mat = nombres[p.material_index] if nombres else ""
        plano = planos.get(mat)
        for li in p.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            if plano:
                eu, ev, o, su, sv = plano
                d = co - Vector(o)
                uv.data[li].uv = (d.dot(Vector(eu)) / su, d.dot(Vector(ev)) / sv)
            else:
                ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                if az >= ax and az >= ay:
                    uv.data[li].uv = (co.x, co.y)
                elif ax >= ay:
                    uv.data[li].uv = (co.y * (1 if n.x > 0 else -1), co.z)
                else:
                    uv.data[li].uv = (co.x * (-1 if n.y > 0 else 1), co.z)


def cerrar_todas():
    for p in PIEZAS:
        if not p.cerrada:
            p.cerrar()
    return [p.obj for p in PIEZAS]


def unir(objetos, nombre):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.object.join()
    ob = bpy.context.view_layer.objects.active
    ob.name = nombre
    ob.data.name = nombre
    return ob


def triangulos(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def triangular(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
    bm.to_mesh(ob.data)
    bm.free()


def comprobar_cerradas(ob):
    """Aristas que no tienen exactamente 2 caras (debe ser 0: todo con grosor real)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    malas = sum(1 for e in bm.edges if len(e.link_faces) != 2)
    bm.free()
    return malas


# ----------------------------------------------------------------------------------------------------------------
# Materiales con nodos
# ----------------------------------------------------------------------------------------------------------------


class Nodos:
    """Atajos para montar árboles de nodos de material."""

    def __init__(self, mat):
        self.nt = mat.node_tree
        self.b = self.nt.nodes["Principled BSDF"]
        self._uv = None

    def n(self, tipo, **props):
        nodo = self.nt.nodes.new(tipo)
        for k, v in props.items():
            setattr(nodo, k, v)
        return nodo

    def L(self, a, b):
        self.nt.links.new(a, b)

    def uv(self):
        if self._uv is None:
            self._uv = self.n("ShaderNodeUVMap", uv_map="fuente").outputs["UV"]
        return self._uv

    def coord(self, escala=1.0, desfase=(0, 0, 0)):
        """Vector UV fuente escalado (en studs: escala 0.5 = periodo de 2 studs)."""
        m = self.n("ShaderNodeMapping")
        m.inputs["Scale"].default_value = (escala, escala, escala) if not isinstance(escala, tuple) else escala
        m.inputs["Location"].default_value = desfase
        self.L(self.uv(), m.inputs["Vector"])
        return m.outputs["Vector"]

    def objeto(self):
        return self.n("ShaderNodeTexCoord").outputs["Object"]

    def imagen(self, img, vector=None, color=True, extension="REPEAT"):
        t = self.n("ShaderNodeTexImage", image=img, extension=extension)
        if not color:
            img.colorspace_settings.name = "Non-Color"
        self.L(vector or self.uv(), t.inputs["Vector"])
        return t

    def ruido(self, vector, escala=5.0, detalle=4.0, rug=0.55):
        t = self.n("ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = escala
        t.inputs["Detail"].default_value = detalle
        t.inputs["Roughness"].default_value = rug
        self.L(vector, t.inputs["Vector"])
        return t.outputs["Fac"]

    def mezcla(self, fac, a, b, modo="MIX"):
        m = self.n("ShaderNodeMix", data_type="RGBA", blend_type=modo)
        ent = [s for s in m.inputs if s.type == "RGBA"]
        self._val(fac, m.inputs[0])
        self._val(a, ent[0])
        self._val(b, ent[1])
        return [s for s in m.outputs if s.type == "RGBA"][0]

    def mate(self, op, a, b=0.0, c=0.0, clamp=False):
        m = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._val(a, m.inputs[0])
        self._val(b, m.inputs[1])
        self._val(c, m.inputs[2])
        return m.outputs[0]

    def rango(self, x, a0, a1, b0=0.0, b1=1.0):
        m = self.n("ShaderNodeMapRange", clamp=True)
        self._val(x, m.inputs["Value"])
        m.inputs["From Min"].default_value = a0
        m.inputs["From Max"].default_value = a1
        m.inputs["To Min"].default_value = b0
        m.inputs["To Max"].default_value = b1
        return m.outputs["Result"]

    def separar(self, vector):
        s = self.n("ShaderNodeSeparateXYZ")
        self.L(vector, s.inputs[0])
        return s.outputs

    def bump(self, altura, fuerza=0.5, distancia=0.02):
        bp = self.n("ShaderNodeBump")
        bp.inputs["Strength"].default_value = fuerza
        bp.inputs["Distance"].default_value = distancia
        self._val(altura, bp.inputs["Height"])
        self.L(bp.outputs["Normal"], self.b.inputs["Normal"])
        return bp

    def _val(self, x, sock):
        if hasattr(x, "is_linked") or isinstance(x, bpy.types.NodeSocket):
            self.L(x, sock)
        elif isinstance(x, (tuple, list)):
            sock.default_value = tuple(x) + ((1.0,) if len(x) == 3 and len(sock.default_value) == 4 else ())
        else:
            sock.default_value = x

    def set(self, entrada, valor):
        self._val(valor, self.b.inputs[entrada])


def srgb(hexa):
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def material(nombre, color=(0.8, 0.8, 0.8), rug=0.5, metal=0.0, emision=None, fuerza=0.0, nodos=None):
    """Material Principled. `color` admite '#RRGGBB'. `nodos(N)` puede enlazar texturas a las entradas."""
    if isinstance(color, str):
        color = srgb(color)
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    N = Nodos(m)
    N.set("Base Color", color)
    N.set("Roughness", rug)
    N.set("Metallic", metal)
    if emision is not None:
        N.set("Emission Color", srgb(emision) if isinstance(emision, str) else emision)
        N.set("Emission Strength", fuerza)
    if nodos:
        nodos(N)
    m.diffuse_color = (*color, 1.0)
    return m


def cargar_imagen(pil, nombre, carpeta, color=True):
    ruta = os.path.join(carpeta, nombre + ".png")
    pil.save(ruta)
    img = bpy.data.images.load(ruta)
    img.name = nombre
    if not color:
        img.colorspace_settings.name = "Non-Color"
    return img


# ----------------------------------------------------------------------------------------------------------------
# Atlas: UV, islas y empaquetado
# ----------------------------------------------------------------------------------------------------------------


def _modo(modo):
    if bpy.context.object and bpy.context.object.mode != modo:
        bpy.ops.object.mode_set(mode=modo)


def desplegar_atlas(objetos, factores_material=None, margen=0.0035):
    """UV 'atlas' compartida por varios objetos. factores_material = {nombre_material: multiplicador}."""
    factores_material = factores_material or {}
    for o in objetos:
        uv = o.data.uv_layers.get("atlas") or o.data.uv_layers.new(name="atlas")
        o.data.uv_layers.active = uv
        uv.active_render = True
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    _modo("EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.0, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.average_islands_scale()
    _modo("OBJECT")

    # Escala de cada isla según la importancia de sus caras.
    for o in objetos:
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        uvl = bm.loops.layers.uv["atlas"]
        dens = bm.faces.layers.float.get("densidad")
        nombres = [m.name for m in me.materials]
        islas = _islas(bm, uvl)
        for caras in islas:
            pesos, area = 0.0, 0.0
            for f in caras:
                a = f.calc_area()
                k = f[dens] if dens else 1.0
                k *= factores_material.get(nombres[f.material_index] if nombres else "", 1.0)
                if f.normal.z < -0.85:
                    k *= 0.35  # caras de abajo: casi nadie las ve
                pesos += k * a
                area += a
            k = pesos / max(area, 1e-9)
            if abs(k - 1) < 1e-3:
                continue
            c = Vector((0, 0))
            n = 0
            for f in caras:
                for l in f.loops:
                    c += l[uvl].uv
                    n += 1
            c /= n
            s = math.sqrt(k)  # k multiplica el área (los píxeles), la escala lineal es su raíz
            for f in caras:
                for l in f.loops:
                    l[uvl].uv = c + (l[uvl].uv - c) * s
        bm.to_mesh(me)
        bm.free()

    for o in objetos:
        o.select_set(True)
    _modo("EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, rotate_method="ANY", scale=True, margin_method="FRACTION", margin=margen,
                            shape_method="CONCAVE")
    _modo("OBJECT")


def _islas(bm, uvl, eps=1e-5):
    padre = {f.index: f.index for f in bm.faces}
    bm.faces.ensure_lookup_table()

    def raiz(i):
        while padre[i] != i:
            padre[i] = padre[padre[i]]
            i = padre[i]
        return i

    for e in bm.edges:
        if len(e.link_faces) != 2:
            continue
        f1, f2 = e.link_faces
        ok = True
        for v in e.verts:
            u1 = next(l[uvl].uv for l in f1.loops if l.vert == v)
            u2 = next(l[uvl].uv for l in f2.loops if l.vert == v)
            if (u1 - u2).length > eps:
                ok = False
                break
        if ok:
            padre[raiz(f1.index)] = raiz(f2.index)
    grupos = {}
    for f in bm.faces:
        grupos.setdefault(raiz(f.index), []).append(f)
    return list(grupos.values())


def densidad_texel(objetos, tam):
    """Píxeles por stud (mediana) en el atlas."""
    ratios = []
    for o in objetos:
        bm = bmesh.new()
        bm.from_mesh(o.data)
        uvl = bm.loops.layers.uv["atlas"]
        for f in bm.faces:
            a3 = f.calc_area()
            if a3 < 1e-4:
                continue
            uvs = [l[uvl].uv for l in f.loops]
            a2 = 0.0
            for i in range(1, len(uvs) - 1):
                a2 += abs((uvs[i] - uvs[0]).cross(uvs[i + 1] - uvs[0])) / 2
            ratios.append(math.sqrt(a2 / a3) * tam)
        bm.free()
    return float(np.median(ratios)) if ratios else 0.0


# ----------------------------------------------------------------------------------------------------------------
# Horneado
# ----------------------------------------------------------------------------------------------------------------


def _materiales(objetos):
    vistos = []
    for o in objetos:
        for s in o.material_slots:
            if s.material and s.material not in vistos:
                vistos.append(s.material)
    return vistos


def _destino(mats, img):
    for m in mats:
        nt = m.node_tree
        n = nt.nodes.get("destino_horneado") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "destino_horneado"
        n.image = img
        for x in nt.nodes:
            x.select = False
        n.select = True
        nt.nodes.active = n


def _cambiar_a_emision(mats, entrada):
    """Conecta la entrada del Principled (o su valor) a un shader de emisión en la salida. Devuelve cómo deshacer."""
    deshacer = []
    for m in mats:
        nt = m.node_tree
        b = nt.nodes.get("Principled BSDF")
        salida = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL" and n.is_active_output)
        enlace_viejo = salida.inputs["Surface"].links[0].from_socket if salida.inputs["Surface"].is_linked else None
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        s = b.inputs[entrada]
        if s.is_linked:
            nt.links.new(s.links[0].from_socket, em.inputs["Color"])
        else:
            v = s.default_value
            em.inputs["Color"].default_value = (v, v, v, 1) if isinstance(v, float) else tuple(v)
        nt.links.new(em.outputs["Emission"], salida.inputs["Surface"])
        deshacer.append((nt, em, salida, enlace_viejo))
    return deshacer


def _deshacer(deshacer):
    for nt, em, salida, viejo in deshacer:
        nt.nodes.remove(em)
        if viejo is not None:
            nt.links.new(viejo, salida.inputs["Surface"])


def hornear_atlas(objetos, tam, carpeta, prefijo, ao_fuerza=0.55, ao_distancia=1.2):
    """Hornea los 5 mapas del atlas (y la oclusión, que se multiplica en el color). Devuelve {canal: imagen}."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = False
    scn.render.bake.margin = 6
    scn.render.bake.margin_type = "EXTEND"
    mats = _materiales(objetos)

    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
        o.hide_render = False
        o.data.uv_layers.active = o.data.uv_layers["atlas"]
    bpy.context.view_layer.objects.active = objetos[0]

    def img(nombre, color):
        i = bpy.data.images.new(f"{prefijo}_{nombre}", tam, tam, alpha=False, float_buffer=not color)
        i.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return i

    imgs = {}
    for canal, entrada, color in (("color", "Base Color", True), ("roughness", "Roughness", False),
                                  ("metalness", "Metallic", False)):
        imgs[canal] = img(canal, color)
        _destino(mats, imgs[canal])
        d = _cambiar_a_emision(mats, entrada)
        scn.cycles.samples = 4
        bpy.ops.object.bake(type="EMIT", margin=6, use_clear=True)
        _deshacer(d)
        print("[horneado]", canal)

    imgs["emision"] = img("emision", True)
    _destino(mats, imgs["emision"])
    scn.cycles.samples = 4
    bpy.ops.object.bake(type="EMIT", margin=6, use_clear=True)
    print("[horneado] emision")

    imgs["normal"] = img("normal", False)
    _destino(mats, imgs["normal"])
    scn.cycles.samples = 8
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", margin=6, use_clear=True)
    print("[horneado] normal")

    ao = img("ao", False)
    _destino(mats, ao)
    scn.world.light_settings.distance = ao_distancia
    scn.cycles.samples = 64
    bpy.ops.object.bake(type="AO", margin=6, use_clear=True)
    print("[horneado] ao")

    c = np.array(imgs["color"].pixels[:], np.float32).reshape(tam, tam, 4)
    a = np.array(ao.pixels[:], np.float32).reshape(tam, tam, 4)[..., :1]
    factor = 1.0 - ao_fuerza * (1.0 - np.clip(a, 0, 1)) ** 1.4
    c[..., :3] *= factor
    imgs["color"].pixels.foreach_set(c.ravel())
    imgs["ao"] = ao

    for canal, i in imgs.items():
        if canal == "ao":
            continue
        ruta = os.path.join(carpeta, f"{prefijo}_{canal}.png")
        i.filepath_raw = ruta
        i.file_format = "PNG"
        if not i.is_float:
            i.save()
        else:
            # Las de datos se hornean en float y se guardan en 8 bits (Roblox no usa más).
            _guardar_8bits(i, ruta)
        print("[ok]", ruta)
    for m in mats:
        n = m.node_tree.nodes.get("destino_horneado")
        if n:
            m.node_tree.nodes.remove(n)
    return imgs


def _guardar_8bits(img, ruta):
    from PIL import Image as PImage

    w, h = img.size
    a = np.array(img.pixels[:], np.float32).reshape(h, w, 4)[::-1, :, :3]
    PImage.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8), "RGB").save(ruta)
    img.filepath_raw = ruta


def material_final(nombre, carpeta, prefijo, rug_defecto=0.5):
    """Material con los mapas horneados del atlas (lo que verá Roblox)."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    N = Nodos(m)
    uv = N.n("ShaderNodeUVMap", uv_map="atlas").outputs["UV"]

    def tex(canal, color):
        i = bpy.data.images.load(os.path.join(carpeta, f"{prefijo}_{canal}.png"), check_existing=False)
        i.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return N.imagen(i, uv, color, "EXTEND")

    N.L(tex("color", True).outputs["Color"], N.b.inputs["Base Color"])
    N.L(tex("roughness", False).outputs["Color"], N.b.inputs["Roughness"])
    N.L(tex("metalness", False).outputs["Color"], N.b.inputs["Metallic"])
    N.L(tex("emision", True).outputs["Color"], N.b.inputs["Emission Color"])
    N.b.inputs["Emission Strength"].default_value = 1.0
    nm = N.n("ShaderNodeNormalMap", uv_map="atlas")
    N.L(tex("normal", False).outputs["Color"], nm.inputs["Color"])
    N.L(nm.outputs["Normal"], N.b.inputs["Normal"])
    return m


def poner_material(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    for p in ob.data.polygons:
        p.material_index = 0


# ----------------------------------------------------------------------------------------------------------------
# Exportación
# ----------------------------------------------------------------------------------------------------------------


def exportar_fbx(ruta, objetos):
    """
    FBX para Roblox: 1 unidad = 1 stud, Apply Scalings = FBX All, ejes Y arriba / -Z delante, y el GIRO DE
    IMPORTACIÓN: los objetos se giran 180° sobre el eje vertical (Y de Roblox, Z de Blender) antes de exportar,
    porque el importador de Roblox los mete girados (visto en el valle del Alba, `MontarRegion.GIRO_IMPORTACION`).
    """
    giro = R("Z", 180)
    for o in objetos:
        o.matrix_world = giro @ o.matrix_world
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", bake_space_transform=False, axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False, bake_anim=False,
        embed_textures=True, path_mode="COPY")
    # Se deshace el giro para seguir trabajando (renders) con la fachada a -Y.
    for o in objetos:
        o.select_set(True)
        o.matrix_world = giro @ o.matrix_world
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    print("[ok] FBX:", ruta)
