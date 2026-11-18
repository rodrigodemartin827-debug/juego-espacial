"""
Geometría de bajo nivel para la clínica (bpy + bmesh, sin pantalla).

Todo se escribe en studs (1 unidad de Blender = 1 stud) y en coordenadas de mundo, con Z hacia arriba y la fachada
mirando a -Y. Cada «Grupo» acaba siendo una malla (una MeshPart en Roblox). Las primitivas se crean en un bmesh
temporal (cerrado, con las normales hacia fuera) y se copian al grupo con su material y, si hace falta, con una UV
de calcomanía («deco») para los rótulos: esa UV solo sirve para hornear el texto y se borra antes de exportar.
"""

import math

import bpy  # noqa: F401  (bpy primero: bmesh y mathutils vienen con él)
import bmesh
from mathutils import Matrix, Vector

V = Vector


# ----------------------------------------------------------------------------------------------------------------
# Grupo = una malla final
# ----------------------------------------------------------------------------------------------------------------


class Grupo:
    def __init__(self, nombre):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new("UVMap")
        self.deco = self.bm.loops.layers.uv.new("deco")
        self.mats = []  # nombres de material, en orden de índice

    def indice(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def fusionar(self, src, mat, deco=None, mat_cara=None, suave=False):
        """
        Copia el bmesh `src` al grupo.
        mat: material de todas las caras, o
        mat_cara(centro, normal) -> material: para dar a cada cara el suyo (por ejemplo el rótulo solo delante).
        deco: (origen, eje_u, eje_v, ancho, alto) para proyectar la UV de calcomanía.
        """
        bmesh.ops.recalc_face_normals(src, faces=src.faces)
        mapa = {v: self.bm.verts.new(v.co) for v in src.verts}
        for f in src.faces:
            nf = self.bm.faces.new([mapa[v] for v in f.verts])
            m = mat_cara(f.calc_center_median(), f.normal) if mat_cara else mat
            nf.material_index = self.indice(m)
            nf.smooth = suave
            if deco:
                o, eu, ev, an, al = deco
                for lp in nf.loops:
                    d = lp.vert.co - o
                    lp[self.deco].uv = (d.dot(eu) / an + 0.5, d.dot(ev) / al + 0.5)
        src.free()

    def triangulos(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)


# ----------------------------------------------------------------------------------------------------------------
# Utilidades
# ----------------------------------------------------------------------------------------------------------------


def matriz_eje(p0, p1):
    """Matriz que lleva el eje Z local al segmento p0 -> p1 (origen en p0)."""
    p0, p1 = V(p0), V(p1)
    d = p1 - p0
    q = V((0, 0, 1)).rotation_difference(d.normalized())
    return Matrix.Translation(p0) @ q.to_matrix().to_4x4()


def _transformar(bm, m):
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)


def bm_caja(tam):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=V(tam), verts=bm.verts)
    return bm


# ----------------------------------------------------------------------------------------------------------------
# Primitivas
# ----------------------------------------------------------------------------------------------------------------


def caja(g, mn, mx, mat, mat_cara=None, deco=None, bisel=0.0, rot=None, pivote=None):
    """Caja de esquina mn a esquina mx. bisel > 0 achaflana las aristas (un segmento). rot: Matrix 3x3 sobre pivote."""
    mn, mx = V(mn), V(mx)
    bm = bm_caja(mx - mn)
    if bisel > 0:
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bisel, segments=1, affect="EDGES", profile=0.5)
    _transformar(bm, Matrix.Translation((mn + mx) / 2))
    if rot is not None:
        p = V(pivote) if pivote is not None else (mn + mx) / 2
        _transformar(bm, Matrix.Translation(p) @ rot.to_4x4() @ Matrix.Translation(-p))
    g.fusionar(bm, mat, deco=deco, mat_cara=mat_cara)


def caja_c(g, centro, tam, mat, **kw):
    c, t = V(centro), V(tam) / 2
    caja(g, c - t, c + t, mat, **kw)


def cilindro(g, p0, p1, r, segs, mat, r2=None, tapas=True, suave=True, giro=0.0, mat_cara=None):
    """Cilindro (o cono si r2) de p0 a p1."""
    p0, p1 = V(p0), V(p1)
    largo = (p1 - p0).length
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=tapas, cap_tris=False, segments=segs, radius1=r,
                          radius2=r if r2 is None else r2, depth=largo)
    if giro:
        bmesh.ops.rotate(bm, verts=bm.verts, cent=V(), matrix=Matrix.Rotation(giro, 3, "Z"))
    _transformar(bm, matriz_eje(p0, p1) @ Matrix.Translation((0, 0, largo / 2)))
    # Las tapas planas, sin suavizar: se marcan después con el corte por ángulo.
    g.fusionar(bm, mat, suave=suave, mat_cara=mat_cara)


def tornillo(g, p, n, r=0.045, alto=0.03, mat="acero", segs=6):
    """Cabeza de tornillo hexagonal con la cúpula un poco levantada, hundida 0,01 en la superficie (normal n)."""
    n = V(n).normalized()
    p = V(p) - n * 0.01
    bm = bmesh.new()
    base = []
    arriba = []
    for i in range(segs):
        a = 2 * math.pi * i / segs + math.pi / segs
        base.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0)))
        arriba.append(bm.verts.new((r * 0.92 * math.cos(a), r * 0.92 * math.sin(a), alto + 0.01)))
    cima = bm.verts.new((0, 0, alto + 0.01 + r * 0.35))
    for i in range(segs):
        j = (i + 1) % segs
        bm.faces.new((base[i], base[j], arriba[j], arriba[i]))
        bm.faces.new((arriba[i], arriba[j], cima))
    bm.faces.new(list(reversed(base)))
    q = V((0, 0, 1)).rotation_difference(n)
    _transformar(bm, Matrix.Translation(p) @ q.to_matrix().to_4x4())
    g.fusionar(bm, mat, suave=True)


def prisma(g, perfil, origen, eu, ev, p0, p1, mat, mat_cara=None, deco=None, suave=False):
    """
    Extruye un polígono 2D (lista de (u, v), en sentido antihorario visto desde +n) entre las profundidades p0 y p1
    a lo largo de n = eu x ev. Sirve para cruces, placas redondeadas, sectores de anillo...
    """
    o, eu, ev = V(origen), V(eu).normalized(), V(ev).normalized()
    n = eu.cross(ev)
    bm = bmesh.new()
    abajo = [bm.verts.new(o + eu * u + ev * v + n * p0) for u, v in perfil]
    arriba = [bm.verts.new(o + eu * u + ev * v + n * p1) for u, v in perfil]
    k = len(perfil)
    bm.faces.new(list(reversed(abajo)))
    bm.faces.new(arriba)
    for i in range(k):
        j = (i + 1) % k
        bm.faces.new((abajo[i], abajo[j], arriba[j], arriba[i]))
    # Las tapas con muchos lados se dejan como n-gonos: el FBX las triangula.
    g.fusionar(bm, mat, mat_cara=mat_cara, deco=deco, suave=suave)


def rect_redondeado(w, h, r, segs=4, cu=0.0, cv=0.0):
    """Perfil 2D de un rectángulo w x h con esquinas de radio r, centrado en (cu, cv), en sentido antihorario."""
    pts = []
    esquinas = [(w / 2 - r, h / 2 - r, 0), (-w / 2 + r, h / 2 - r, 90), (-w / 2 + r, -h / 2 + r, 180),
                (w / 2 - r, -h / 2 + r, 270)]
    for x, y, a0 in esquinas:
        for i in range(segs + 1):
            a = math.radians(a0 + 90 * i / segs)
            pts.append((cu + x + r * math.cos(a), cv + y + r * math.sin(a)))
    return pts


def perfil_cruz(lado, brazo):
    """Cruz griega de lado total `lado` y brazos de ancho `brazo` (antihoraria)."""
    a, b = lado / 2, brazo / 2
    return [(b, -a), (b, -b), (a, -b), (a, b), (b, b), (b, a), (-b, a), (-b, b), (-a, b), (-a, -b), (-b, -b),
            (-b, -a)]


def sector_anillo(r_in, r_out, a0, a1, segs):
    """Perfil 2D de un sector de anillo (grados), antihorario."""
    fuera = [(r_out * math.cos(math.radians(a0 + (a1 - a0) * i / segs)),
              r_out * math.sin(math.radians(a0 + (a1 - a0) * i / segs))) for i in range(segs + 1)]
    if r_in <= 0:
        return [(0.0, 0.0)] + fuera
    dentro = [(r_in * math.cos(math.radians(a1 - (a1 - a0) * i / segs)),
               r_in * math.sin(math.radians(a1 - (a1 - a0) * i / segs))) for i in range(segs + 1)]
    return fuera + dentro


def _redondear_polilinea(pts, radio, pasos):
    """Sustituye cada esquina de la polilínea por un arco (filete) de radio `radio`."""
    if radio <= 0 or len(pts) < 3:
        return [V(p) for p in pts]
    pts = [V(p) for p in pts]
    out = [pts[0]]
    for i in range(1, len(pts) - 1):
        a, b, c = pts[i - 1], pts[i], pts[i + 1]
        d1 = (a - b).normalized()
        d2 = (c - b).normalized()
        ang = d1.angle(d2)
        if ang > math.pi - 1e-3:
            out.append(b)
            continue
        t = radio / math.tan(ang / 2)
        t = min(t, (a - b).length * 0.45, (c - b).length * 0.45)
        p1 = b + d1 * t
        p2 = b + d2 * t
        # Bézier cuadrática (b es el punto de control): para tubos queda igual que un arco.
        for k in range(pasos + 1):
            s = k / pasos
            out.append((1 - s) ** 2 * p1 + 2 * (1 - s) * s * b + s ** 2 * p2)
    out.append(pts[-1])
    return out


def tubo(g, pts, r, segs, mat, radio_codo=0.0, pasos_codo=3, tapas=True):
    """Barrido de un círculo por una polilínea (codos redondeados), con transporte paralelo del marco."""
    pts = _redondear_polilinea(pts, radio_codo, pasos_codo)
    bm = bmesh.new()
    anillos = []
    t0 = (pts[1] - pts[0]).normalized()
    ref = V((0, 0, 1)) if abs(t0.z) < 0.9 else V((1, 0, 0))
    nrm = t0.cross(ref).normalized()
    t_prev = t0
    for i, p in enumerate(pts):
        if i == 0:
            t = t0
        elif i == len(pts) - 1:
            t = (pts[i] - pts[i - 1]).normalized()
        else:
            t = ((pts[i] - pts[i - 1]).normalized() + (pts[i + 1] - pts[i]).normalized()).normalized()
        # transporte paralelo
        q = t_prev.rotation_difference(t)
        nrm = (q @ nrm).normalized()
        t_prev = t
        b = t.cross(nrm).normalized()
        # en los codos el anillo se ensancha (inglete) para que el tubo no se estreche
        esc, kdir = 1.0, None
        if 0 < i < len(pts) - 1:
            dprev = (pts[i] - pts[i - 1]).normalized()
            dnext = (pts[i + 1] - pts[i]).normalized()
            esc = 1.0 / max(0.5, dprev.dot(t))
            k = dnext - dprev
            k = k - t * k.dot(t)
            if k.length > 1e-6:
                kdir = k.normalized()
        anillo = []
        for k in range(segs):
            a = 2 * math.pi * k / segs
            off = nrm * math.cos(a) * r + b * math.sin(a) * r
            if kdir is not None:
                off = off + kdir * off.dot(kdir) * (esc - 1.0)
            anillo.append(bm.verts.new(p + off))
        anillos.append(anillo)
    for i in range(len(anillos) - 1):
        a1, a2 = anillos[i], anillos[i + 1]
        for k in range(segs):
            j = (k + 1) % segs
            bm.faces.new((a1[k], a1[j], a2[j], a2[k]))
    if tapas:
        bm.faces.new(list(reversed(anillos[0])))
        bm.faces.new(anillos[-1])
    g.fusionar(bm, mat, suave=True)


def placa_con_tornillos(g, centro, eu, ev, ancho, alto, grosor, mat, mat_frente=None, deco=None, tornillos=4,
                        margen=0.09, r_torn=0.04, bisel=0.0):
    """Placa rectangular apoyada en una pared (normal n = eu x ev) con tornillos en las esquinas."""
    c, eu, ev = V(centro), V(eu).normalized(), V(ev).normalized()
    n = eu.cross(ev)
    perfil = rect_redondeado(ancho, alto, min(0.04, ancho / 6, alto / 6), segs=1) if bisel == 0 else \
        rect_redondeado(ancho, alto, bisel, segs=2)

    def mc(cc, nn):
        return mat_frente if (mat_frente and nn.dot(n) > 0.9) else mat

    prisma(g, perfil, c, eu, ev, 0.0, grosor, mat, mat_cara=mc, deco=deco)
    if tornillos:
        pos = [(1, 1), (-1, 1), (-1, -1), (1, -1)] if tornillos == 4 else [(1, 0), (-1, 0)]
        for su, sv in pos:
            p = c + eu * su * (ancho / 2 - margen) + ev * sv * ((alto / 2 - margen) if tornillos == 4 else 0) \
                + n * grosor
            tornillo(g, p, n, r=r_torn, alto=0.02)


# ----------------------------------------------------------------------------------------------------------------
# Paso a Blender
# ----------------------------------------------------------------------------------------------------------------


def a_objeto(g, materiales, angulo_duro=35.0):
    """Crea el objeto de Blender del grupo: une vértices repetidos, marca aristas duras por ángulo y suaviza."""
    bm = g.bm
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
    lim = math.radians(angulo_duro)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) != 2:
            e.smooth = False
            continue
        a, b = e.link_faces
        ang = a.normal.angle(b.normal, 0.0)
        e.smooth = ang < lim and a.material_index == b.material_index
    malla = bpy.data.meshes.new(g.nombre)
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(g.nombre, malla)
    bpy.context.scene.collection.objects.link(obj)
    for m in g.mats:
        malla.materials.append(materiales[m])
    malla.uv_layers["UVMap"].active = True
    malla.uv_layers["UVMap"].active_render = True
    return obj
