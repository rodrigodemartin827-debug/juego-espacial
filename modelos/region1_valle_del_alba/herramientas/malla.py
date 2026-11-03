"""
Mallas low-poly hechas a mano en Python: primitivas (cajas, prismas, cilindros, conos, cascos convexos...),
transformaciones y unión. No depende de Blender: las piezas del kit se construyen aquí y luego `a_blender()` las
convierte en objetos.

Cada cara guarda:
  * su material (un nombre: "PARED", "TEJA", "MADERA"... Los nombres en MAYÚSCULAS son «ranuras» que el edificio
    sustituye por una variante concreta, p. ej. PARED -> Yeso_Crema);
  * un «tinte» (un número cerca de 1) que multiplica el color en el material: así cada teja, piedra o tabla tiene un
    tono un poco distinto sin texturas;
  * si se sombrea liso o plano (casi todo es plano: el estilo low-poly).

Unidades: studs. Ejes de Blender: Z arriba.
"""

import math

import numpy as np
from scipy.spatial import ConvexHull


# --------------------------------------------------------------------------------------------------------------
# Matrices 4x4
# --------------------------------------------------------------------------------------------------------------


def T(x=0.0, y=0.0, z=0.0):
    m = np.eye(4)
    m[:3, 3] = (x, y, z)
    return m


def S(x=1.0, y=None, z=None):
    y = x if y is None else y
    z = x if z is None else z
    return np.diag([x, y, z, 1.0])


def Rz(grados):
    a = math.radians(grados)
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[:2, :2] = [[c, -s], [s, c]]
    return m


def Rx(grados):
    a = math.radians(grados)
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[1:3, 1:3] = [[c, -s], [s, c]]
    return m


def Ry(grados):
    a = math.radians(grados)
    c, s = math.cos(a), math.sin(a)
    m = np.eye(4)
    m[0, 0], m[0, 2], m[2, 0], m[2, 2] = c, s, -s, c
    return m


def compone(*ms):
    r = np.eye(4)
    for m in ms:
        r = r @ m
    return r


def marco_matriz(origen, ex, ey, ez):
    m = np.eye(4)
    m[:3, 0], m[:3, 1], m[:3, 2], m[:3, 3] = ex, ey, ez, origen
    return m


# --------------------------------------------------------------------------------------------------------------
# La malla
# --------------------------------------------------------------------------------------------------------------


class Malla:
    def __init__(self):
        self.v = []  # lista de arrays (k, 3)
        self.caras = []  # lista de tuplas de índices (globales)
        self.mat = []
        self.tinte = []
        self.liso = []
        self._n = 0

    # -------------------------------------------------------------------------------- básicos

    def _vertices(self, pts):
        pts = np.asarray(pts, dtype=np.float64).reshape(-1, 3)
        base = self._n
        self.v.append(pts)
        self._n += len(pts)
        return base

    def poligono(self, pts, mat, tinte=1.0, liso=False):
        b = self._vertices(pts)
        self.caras.append(tuple(range(b, b + len(pts))))
        self.mat.append(mat)
        self.tinte.append(tinte)
        self.liso.append(liso)

    def caras_indexadas(self, pts, caras, mat, tinte=1.0, liso=False):
        b = self._vertices(pts)
        for k, c in enumerate(caras):
            self.caras.append(tuple(b + i for i in c))
            self.mat.append(mat)
            self.tinte.append(float(tinte) if np.isscalar(tinte) else float(tinte[k]))
            self.liso.append(liso)

    @property
    def n_triangulos(self):
        return sum(len(c) - 2 for c in self.caras)

    def todos_vertices(self):
        return np.concatenate(self.v) if self.v else np.zeros((0, 3))

    # -------------------------------------------------------------------------------- unión y transformación

    def anadir(self, otra, m=None, remap=None, tinte=1.0):
        """Añade otra malla transformada por m (4x4). remap: {material: material} para cambiar ranuras."""
        if not otra.v:
            return self
        pts = otra.todos_vertices()
        if m is not None:
            pts = pts @ m[:3, :3].T + m[:3, 3]
            invertir = np.linalg.det(m[:3, :3]) < 0
        else:
            invertir = False
        base = self._vertices(pts)
        for c, mt, ti, li in zip(otra.caras, otra.mat, otra.tinte, otra.liso):
            c2 = tuple(base + i for i in c)
            if invertir:
                c2 = c2[::-1]
            self.caras.append(c2)
            self.mat.append(remap.get(mt, mt) if remap else mt)
            self.tinte.append(ti * tinte)
            self.liso.append(li)
        return self

    def transformada(self, m):
        return Malla().anadir(self, m)

    def limites(self):
        p = self.todos_vertices()
        return p.min(axis=0), p.max(axis=0)

    # -------------------------------------------------------------------------------- primitivas

    def caja(self, a, b, mat, tinte=1.0, sin=()):
        """Caja alineada de la esquina a a la b. `sin`: caras que no se crean ('-x','+x','-y','+y','-z','+z')."""
        (x0, y0, z0), (x1, y1, z1) = a, b
        p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1),
             (x0, y1, z1)]
        caras = {"-z": (0, 3, 2, 1), "+z": (4, 5, 6, 7), "-y": (0, 1, 5, 4), "+y": (2, 3, 7, 6),
                 "-x": (3, 0, 4, 7), "+x": (1, 2, 6, 5)}
        self.caras_indexadas(p, [c for k, c in caras.items() if k not in sin], mat, tinte)
        return self

    def caja_c(self, centro, tam, mat, tinte=1.0, sin=()):
        c, t = np.asarray(centro, float), np.asarray(tam, float) / 2
        return self.caja(c - t, c + t, mat, tinte, sin)

    def caja_biselada(self, a, b, bisel, mat, tinte=1.0):
        a, b = np.asarray(a, float), np.asarray(b, float)
        c, h = (a + b) / 2, (b - a) / 2
        e = np.minimum(bisel, h * 0.49)
        pts = []
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    s = np.array([sx, sy, sz])
                    pts += [c + s * (h - e * np.array(m)) for m in ((0, 1, 1), (1, 0, 1), (1, 1, 0))]
        return self.convexo(pts, mat, tinte)

    def convexo(self, pts, mat, tinte=1.0, liso=False):
        """Casco convexo de unos puntos (rocas, piezas biseladas). Une los triángulos coplanarios."""
        pts = np.asarray(pts, dtype=np.float64)
        h = ConvexHull(pts)
        centro = pts.mean(axis=0)
        caras = []
        for s in h.simplices:
            a, b, c = pts[s]
            if np.dot(np.cross(b - a, c - a), a - centro) < 0:
                s = s[::-1]
            caras.append(tuple(s))
        self.caras_indexadas(pts, caras, mat, tinte, liso)
        return self

    def prisma(self, poli, z0, z1, mat, tinte=1.0, tapas=True, mat_tapa=None):
        """Extruye un polígono 2D (en XY, antihorario) de z0 a z1."""
        poli = np.asarray(poli, dtype=np.float64)
        n = len(poli)
        p = np.concatenate([np.c_[poli, np.full(n, z0)], np.c_[poli, np.full(n, z1)]])
        caras = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self.caras_indexadas(p, caras, mat, tinte)
        if tapas:
            self.caras_indexadas(p, [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))], mat_tapa or mat, tinte)
        return self

    def tronco(self, c, r0, r1, h, n, mat, tinte=1.0, tapa_abajo=True, tapa_arriba=True, liso=False, giro=0.0,
               mat_tapa=None):
        """Cilindro o tronco de cono de n lados con la base en c (z hacia arriba). r1 = 0: cono."""
        cx, cy, cz = c
        ang = np.radians(giro) + 2 * np.pi * np.arange(n) / n
        aro0 = np.c_[cx + r0 * np.cos(ang), cy + r0 * np.sin(ang), np.full(n, cz)]
        if r1 <= 1e-6:
            p = np.concatenate([aro0, [[cx, cy, cz + h]]])
            caras = [(i, (i + 1) % n, n) for i in range(n)]
            self.caras_indexadas(p, caras, mat, tinte, liso)
            if tapa_abajo:
                self.caras_indexadas(aro0, [tuple(range(n - 1, -1, -1))], mat_tapa or mat, tinte)
            return self
        aro1 = np.c_[cx + r1 * np.cos(ang), cy + r1 * np.sin(ang), np.full(n, cz + h)]
        p = np.concatenate([aro0, aro1])
        caras = [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)]
        self.caras_indexadas(p, caras, mat, tinte, liso)
        if tapa_abajo:
            self.caras_indexadas(aro0, [tuple(range(n - 1, -1, -1))], mat_tapa or mat, tinte)
        if tapa_arriba:
            self.caras_indexadas(aro1, [tuple(range(n))], mat_tapa or mat, tinte)
        return self

    def torno(self, perfil, n, mat, c=(0, 0, 0), liso=True, tinte=1.0, giro=0.0):
        """Superficie de revolución: perfil = [(radio, z), ...] de abajo arriba."""
        cx, cy, cz = c
        ang = np.radians(giro) + 2 * np.pi * np.arange(n) / n
        pts, caras = [], []
        for (r, z) in perfil:
            pts += [(cx + r * math.cos(a), cy + r * math.sin(a), cz + z) for a in ang]
        for k in range(len(perfil) - 1):
            for i in range(n):
                a, b = k * n + i, k * n + (i + 1) % n
                caras.append((a, b, b + n, a + n))
        # tapas si el perfil empieza o acaba en radio > 0
        if perfil[0][0] > 1e-6:
            caras.append(tuple(range(n - 1, -1, -1)))
        if perfil[-1][0] > 1e-6:
            k = len(perfil) - 1
            caras.append(tuple(k * n + i for i in range(n)))
        self.caras_indexadas(pts, caras, mat, tinte, liso)
        return self

    def esfera(self, c, r, mat, sub=1, tinte=1.0, liso=False, jitter=0.0, rng=None, escala=(1, 1, 1)):
        """Icosfera low-poly (sub 0 = 20 caras, 1 = 80). jitter deforma los vértices (copas de árbol, rocas)."""
        v, f = _icosfera(sub)
        if jitter and rng is not None:
            v = v * (1.0 + rng.uniform(-jitter, jitter, size=(len(v), 1)))
        v = v * np.asarray(escala) * r + np.asarray(c)
        self.caras_indexadas(v, f, mat, tinte, liso)
        return self

    def tira(self, puntos, ancho, alto, mat, tinte=1.0, arriba=(0, 0, 1)):
        """Viga de sección rectangular a lo largo de una polilínea 3D."""
        P = np.asarray(puntos, float)
        up = np.asarray(arriba, float)
        for a, b in zip(P[:-1], P[1:]):
            d = b - a
            L = np.linalg.norm(d)
            if L < 1e-9:
                continue
            ex = d / L
            ey = np.cross(up, ex)
            if np.linalg.norm(ey) < 1e-6:
                ey = np.array([0, 1.0, 0])
            ey /= np.linalg.norm(ey)
            ez = np.cross(ex, ey)
            m = marco_matriz(a, ex, ey, ez)
            pieza = Malla().caja((0, -ancho / 2, -alto / 2), (L, ancho / 2, alto / 2), mat, tinte)
            self.anadir(pieza, m)
        return self

    def viga(self, a, b, grosor, mat, tinte=1.0):
        """Viga cuadrada entre dos puntos (cualquier dirección)."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = b - a
        L = np.linalg.norm(d)
        ex = d / L
        ref = np.array([0, 0, 1.0]) if abs(ex[2]) < 0.9 else np.array([1.0, 0, 0])
        ey = np.cross(ref, ex)
        ey /= np.linalg.norm(ey)
        ez = np.cross(ex, ey)
        g = grosor / 2
        self.anadir(Malla().caja((0, -g, -g), (L, g, g), mat, tinte), marco_matriz(a, ex, ey, ez))
        return self

    # -------------------------------------------------------------------------------- a Blender

    def a_blender(self, nombre, materiales, coleccion=None, suavizado_auto=None):
        """Crea un objeto de Blender. `materiales`: {nombre: bpy.types.Material}. Devuelve el objeto."""
        import bpy

        pts = self.todos_vertices()
        me = bpy.data.meshes.new(nombre)
        nombres = sorted(set(self.mat))
        for n in nombres:
            me.materials.append(materiales[n])
        idx = {n: i for i, n in enumerate(nombres)}
        tam = np.array([len(c) for c in self.caras], dtype=np.int32)
        inicio = np.concatenate([[0], np.cumsum(tam)[:-1]]).astype(np.int32)
        bucles = np.fromiter((i for c in self.caras for i in c), dtype=np.int32, count=int(tam.sum()))
        me.vertices.add(len(pts))
        me.vertices.foreach_set("co", pts.astype(np.float32).ravel())
        me.loops.add(len(bucles))
        me.loops.foreach_set("vertex_index", bucles)
        me.polygons.add(len(self.caras))
        me.polygons.foreach_set("loop_start", inicio)
        me.polygons.foreach_set("material_index", np.array([idx[m] for m in self.mat], dtype=np.int32))
        me.polygons.foreach_set("use_smooth", np.array(self.liso, dtype=bool))
        at = me.attributes.new("Tinte", "FLOAT", "FACE")
        at.data.foreach_set("value", np.array(self.tinte, dtype=np.float32))
        me.update(calc_edges=True)
        me.validate(clean_customdata=False)
        ob = bpy.data.objects.new(nombre, me)
        (coleccion or bpy.context.scene.collection).objects.link(ob)
        ob["triangulos"] = self.n_triangulos
        return ob


# --------------------------------------------------------------------------------------------------------------


_ICO_CACHE = {}


def _icosfera(sub):
    if sub in _ICO_CACHE:
        return _ICO_CACHE[sub]
    t = (1 + 5**0.5) / 2
    v = [(-1, t, 0), (1, t, 0), (-1, -t, 0), (1, -t, 0), (0, -1, t), (0, 1, t), (0, -1, -t), (0, 1, -t), (t, 0, -1),
         (t, 0, 1), (-t, 0, -1), (-t, 0, 1)]
    f = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11), (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6),
         (7, 1, 8), (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9), (4, 9, 5), (2, 4, 11), (6, 2, 10),
         (8, 6, 7), (9, 8, 1)]
    v = [np.array(p, float) / np.linalg.norm(p) for p in v]
    for _ in range(sub):
        cache = {}

        def medio(a, b):
            k = (min(a, b), max(a, b))
            if k not in cache:
                m = v[a] + v[b]
                v.append(m / np.linalg.norm(m))
                cache[k] = len(v) - 1
            return cache[k]

        nf = []
        for a, b, c in f:
            ab, bc, ca = medio(a, b), medio(b, c), medio(c, a)
            nf += [(a, ab, ca), (b, bc, ab), (c, ca, bc), (ab, bc, ca)]
        f = nf
    _ICO_CACHE[sub] = (np.array(v), f)
    return _ICO_CACHE[sub]
