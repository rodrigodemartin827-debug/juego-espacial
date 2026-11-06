"""
Mallas low-poly hechas a mano en Python: primitivas (cajas, prismas, troncos de cono, tornos, icosferas, cascos
convexos), transformaciones y unión. No depende de Blender: las piezas del kit se construyen aquí y `a_blender()` las
convierte en objetos.

Cada cara guarda:
  * su «material», que casi siempre es el nombre de una casilla del atlas (atlas.py): «pared_ventana», «teja_16»,
    «piedra_clara»... Los nombres que no son casillas del atlas («Agua», «Mar») son materiales propios.
  * cómo se le ponen las UV:
      - por defecto, «ajustada»: la cara entera ocupa su casilla (la v sigue la pendiente o la vertical de la cara);
      - «plana»: uv = A·p + b, una proyección fija que comparten varias caras (así el dibujo de una casilla continúa
        de una cara a otra, p. ej. una fachada con el hueco de la ventana).
  * si se sombrea liso o plano (casi todo es plano: estilo low-poly).

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


def uv_plano(origen, eu, ev, su, sv):
    """Proyección plana: u = (p - origen)·eu / su, v = (p - origen)·ev / sv."""
    o, eu, ev = (np.asarray(x, float) for x in (origen, eu, ev))
    A = np.stack([eu / su, ev / sv])
    return ("plano", A, -A @ o)


def _normal(p):
    """Normal de Newell (vale para polígonos no convexos)."""
    n = np.zeros(3)
    for a, b in zip(p, np.roll(p, -1, axis=0)):
        n += np.array([(a[1] - b[1]) * (a[2] + b[2]), (a[2] - b[2]) * (a[0] + b[0]), (a[0] - b[0]) * (a[1] + b[1])])
    L = np.linalg.norm(n)
    return n / L if L > 1e-12 else np.array([0, 0, 1.0])


def uv_ajustada(p):
    """UV de una cara que ocupa su casilla entera: v sube por la cara (o hacia +Y si es horizontal), u a la derecha
    vista desde fuera."""
    n = _normal(p)
    z = np.array([0, 0, 1.0])
    ev = z - np.dot(z, n) * n
    if np.linalg.norm(ev) < 1e-3:
        ev = np.array([0, 1.0, 0]) - n[1] * n
    ev /= np.linalg.norm(ev)
    eu = np.cross(ev, n)
    u = p @ eu
    v = p @ ev
    du, dv = max(u.max() - u.min(), 1e-9), max(v.max() - v.min(), 1e-9)
    return np.stack([(u - u.min()) / du, (v - v.min()) / dv], -1)


# --------------------------------------------------------------------------------------------------------------
# La malla
# --------------------------------------------------------------------------------------------------------------


class Malla:
    def __init__(self):
        self.v = []
        self.caras = []
        self.mat = []
        self.uv = []  # None (ajustada) o ("plano", A, b)
        self.liso = []
        self._n = 0

    def _vertices(self, pts):
        pts = np.asarray(pts, dtype=np.float64).reshape(-1, 3)
        base = self._n
        self.v.append(pts)
        self._n += len(pts)
        return base

    def poligono(self, pts, mat, uv=None, liso=False):
        b = self._vertices(pts)
        self.caras.append(tuple(range(b, b + len(pts))))
        self.mat.append(mat)
        self.uv.append(uv)
        self.liso.append(liso)
        return self

    def caras_indexadas(self, pts, caras, mat, uv=None, liso=False):
        b = self._vertices(pts)
        for k, c in enumerate(caras):
            self.caras.append(tuple(b + i for i in c))
            self.mat.append(mat if isinstance(mat, str) else mat[k])
            self.uv.append(uv)
            self.liso.append(liso)
        return self

    @property
    def n_triangulos(self):
        return sum(len(c) - 2 for c in self.caras)

    def todos_vertices(self):
        return np.concatenate(self.v) if self.v else np.zeros((0, 3))

    # -------------------------------------------------------------------------------- unión y transformación

    def anadir(self, otra, m=None):
        """Añade otra malla transformada por m (4x4, sin espejo). Las UV planas se transforman con ella."""
        if not otra.v:
            return self
        pts = otra.todos_vertices()
        if m is not None:
            pts = pts @ m[:3, :3].T + m[:3, 3]
            inv = np.linalg.inv(m)
        base = self._vertices(pts)
        for c, mt, uv, li in zip(otra.caras, otra.mat, otra.uv, otra.liso):
            self.caras.append(tuple(base + i for i in c))
            self.mat.append(mt)
            if uv is not None and m is not None:
                _, A, b = uv
                # uv = A·p_hijo + b, con p_hijo = inv·p  ->  A' = A·inv[:3,:3], b' = A·inv[:3,3] + b
                uv = ("plano", A @ inv[:3, :3], A @ inv[:3, 3] + b)
            self.uv.append(uv)
            self.liso.append(li)
        return self

    def transformada(self, m):
        return Malla().anadir(self, m)

    def limites(self):
        p = self.todos_vertices()
        return p.min(axis=0), p.max(axis=0)

    # -------------------------------------------------------------------------------- primitivas

    CARAS_CAJA = {"-z": (0, 3, 2, 1), "+z": (4, 5, 6, 7), "-y": (0, 1, 5, 4), "+y": (2, 3, 7, 6),
                  "-x": (3, 0, 4, 7), "+x": (1, 2, 6, 5)}

    def caja(self, a, b, mat, sin=(), solo=None, mats=None, uv=None):
        """Caja alineada de la esquina a a la b. `sin`: caras que no se crean; `solo`: las únicas que se crean;
        `mats`: material por cara ({'-y': 'pared_lisa'})."""
        (x0, y0, z0), (x1, y1, z1) = a, b
        p = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1),
             (x0, y1, z1)]
        for k, c in self.CARAS_CAJA.items():
            if k in sin or (solo is not None and k not in solo):
                continue
            self.poligono([p[i] for i in c], (mats or {}).get(k, mat), uv)
        return self

    def caja_c(self, centro, tam, mat, **kw):
        c, t = np.asarray(centro, float), np.asarray(tam, float) / 2
        return self.caja(c - t, c + t, mat, **kw)

    def convexo(self, pts, mat, liso=False):
        pts = np.asarray(pts, dtype=np.float64)
        h = ConvexHull(pts)
        centro = pts.mean(axis=0)
        caras = []
        for s in h.simplices:
            a, b, c = pts[s]
            if np.dot(np.cross(b - a, c - a), a - centro) < 0:
                s = s[::-1]
            caras.append(tuple(s))
        return self.caras_indexadas(pts, caras, mat, liso=liso)

    def prisma(self, poli, z0, z1, mat, tapas=True, mat_tapa=None, uv=None):
        """Extruye un polígono 2D (en XY, antihorario) de z0 a z1."""
        poli = np.asarray(poli, dtype=np.float64)
        n = len(poli)
        p = np.concatenate([np.c_[poli, np.full(n, z0)], np.c_[poli, np.full(n, z1)]])
        self.caras_indexadas(p, [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)], mat, uv)
        if tapas:
            self.caras_indexadas(p, [tuple(range(n - 1, -1, -1)), tuple(range(n, 2 * n))], mat_tapa or mat, uv)
        return self

    def tronco(self, c, r0, r1, h, n, mat, tapa_abajo=True, tapa_arriba=True, liso=False, giro=0.0, mat_tapa=None):
        cx, cy, cz = c
        ang = np.radians(giro) + 2 * np.pi * np.arange(n) / n
        aro0 = np.c_[cx + r0 * np.cos(ang), cy + r0 * np.sin(ang), np.full(n, cz)]
        if r1 <= 1e-6:
            p = np.concatenate([aro0, [[cx, cy, cz + h]]])
            self.caras_indexadas(p, [(i, (i + 1) % n, n) for i in range(n)], mat, liso=liso)
            if tapa_abajo:
                self.caras_indexadas(aro0, [tuple(range(n - 1, -1, -1))], mat_tapa or mat)
            return self
        aro1 = np.c_[cx + r1 * np.cos(ang), cy + r1 * np.sin(ang), np.full(n, cz + h)]
        p = np.concatenate([aro0, aro1])
        self.caras_indexadas(p, [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)], mat, liso=liso)
        if tapa_abajo:
            self.caras_indexadas(aro0, [tuple(range(n - 1, -1, -1))], mat_tapa or mat)
        if tapa_arriba:
            self.caras_indexadas(aro1, [tuple(range(n))], mat_tapa or mat)
        return self

    def torno(self, perfil, n, mat, c=(0, 0, 0), liso=False, giro=0.0, tapas=True):
        """Superficie de revolución: perfil = [(radio, z), ...] de abajo arriba. mat puede ser una lista (por tramo)."""
        cx, cy, cz = c
        ang = np.radians(giro) + 2 * np.pi * np.arange(n) / n
        pts = []
        for (r, z) in perfil:
            pts += [(cx + r * math.cos(a), cy + r * math.sin(a), cz + z) for a in ang]
        caras, mats = [], []
        for k in range(len(perfil) - 1):
            for i in range(n):
                a, b = k * n + i, k * n + (i + 1) % n
                caras.append((a, b, b + n, a + n))
                mats.append(mat if isinstance(mat, str) else mat[k])
        if tapas and perfil[0][0] > 1e-6:
            caras.append(tuple(range(n - 1, -1, -1)))
            mats.append(mat if isinstance(mat, str) else mat[0])
        if tapas and perfil[-1][0] > 1e-6:
            k = len(perfil) - 1
            caras.append(tuple(k * n + i for i in range(n)))
            mats.append(mat if isinstance(mat, str) else mat[-1])
        return self.caras_indexadas(pts, caras, mats, liso=liso)

    def esfera(self, c, r, mat, sub=0, liso=False, jitter=0.0, rng=None, escala=(1, 1, 1)):
        v, f = _icosfera(sub)
        if jitter and rng is not None:
            v = v * (1.0 + rng.uniform(-jitter, jitter, size=(len(v), 1)))
        v = v * np.asarray(escala) * r + np.asarray(c)
        return self.caras_indexadas(v, f, mat, liso=liso)

    def viga(self, a, b, grosor, mat, lados=4):
        """Viga entre dos puntos (cualquier dirección): sección cuadrada, sin tapas."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = b - a
        L = np.linalg.norm(d)
        ex = d / L
        ref = np.array([0, 0, 1.0]) if abs(ex[2]) < 0.9 else np.array([1.0, 0, 0])
        ey = np.cross(ref, ex)
        ey /= np.linalg.norm(ey)
        ez = np.cross(ex, ey)
        g = grosor / 2
        self.anadir(Malla().caja((0, -g, -g), (L, g, g), mat, sin=("-x", "+x")), marco_matriz(a, ex, ey, ez))
        return self

    # -------------------------------------------------------------------------------- UV y triángulos

    def uvs_atlas(self):
        """UV de cada esquina de cada cara, ya en el atlas. Devuelve una lista de arrays (k, 2)."""
        import atlas as AT

        pts = self.todos_vertices()
        salida = []
        for c, mt, uv in zip(self.caras, self.mat, self.uv):
            p = pts[list(c)]
            if mt not in AT.INDICE:
                salida.append(np.zeros((len(c), 2)))
                continue
            if uv is None:
                loc = uv_ajustada(p)
            else:
                _, A, b = uv
                loc = p @ A.T + b
            uu, vv = AT.a_atlas(mt, loc[:, 0], loc[:, 1])
            salida.append(np.stack([uu, vv], -1))
        return salida

    def triangulada(self):
        """Malla equivalente con las caras de más de 4 lados partidas en triángulos (sirve para polígonos cóncavos:
        el importador de Roblox no siempre los triangula bien)."""
        from mathutils import Vector
        from mathutils.geometry import tessellate_polygon

        pts = self.todos_vertices()
        m = Malla()
        m._vertices(pts)
        for c, mt, uv, li in zip(self.caras, self.mat, self.uv, self.liso):
            if len(c) <= 4:
                m.caras.append(c)
                m.mat.append(mt)
                m.uv.append(uv)
                m.liso.append(li)
                continue
            p = pts[list(c)]
            n = _normal(p)
            ref = np.array([0, 0, 1.0]) if abs(n[2]) < 0.9 else np.array([1.0, 0, 0])
            e1 = np.cross(ref, n)
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(n, e1)
            plano = [Vector((float(q @ e1), float(q @ e2), 0.0)) for q in p]
            tris = tessellate_polygon([plano])
            for t in tris:
                tri = [c[i] for i in t]
                # orientación igual que la cara original
                a, b, d = pts[tri[0]], pts[tri[1]], pts[tri[2]]
                if np.dot(np.cross(b - a, d - a), n) < 0:
                    tri = tri[::-1]
                m.caras.append(tuple(tri))
                m.mat.append(mt)
                # una cara «ajustada» partida en triángulos tiene que seguir ajustada a la cara ENTERA
                m.uv.append(uv if uv is not None else ("plano",) + _ajuste_como_plano(p))
                m.liso.append(li)
        return m

    def a_blender(self, nombre, materiales, coleccion=None):
        """Crea un objeto de Blender. `materiales`: {nombre: bpy.types.Material}; las casillas del atlas usan
        materiales['Atlas_Kit']. Devuelve el objeto."""
        import bpy

        import atlas as AT

        m = self.triangulada()
        pts = m.todos_vertices()
        me = bpy.data.meshes.new(nombre)
        nombres = sorted({("Atlas_Kit" if x in AT.INDICE else x) for x in m.mat})
        for n in nombres:
            me.materials.append(materiales[n])
        idx = {n: i for i, n in enumerate(nombres)}
        tam = np.array([len(c) for c in m.caras], dtype=np.int32)
        inicio = np.concatenate([[0], np.cumsum(tam)[:-1]]).astype(np.int32)
        bucles = np.fromiter((i for c in m.caras for i in c), dtype=np.int32, count=int(tam.sum()))
        me.vertices.add(len(pts))
        me.vertices.foreach_set("co", pts.astype(np.float32).ravel())
        me.loops.add(len(bucles))
        me.loops.foreach_set("vertex_index", bucles)
        me.polygons.add(len(m.caras))
        me.polygons.foreach_set("loop_start", inicio)
        me.polygons.foreach_set("material_index",
                                np.array([idx["Atlas_Kit" if x in AT.INDICE else x] for x in m.mat], dtype=np.int32))
        me.polygons.foreach_set("use_smooth", np.array(m.liso, dtype=bool))
        capa = me.uv_layers.new(name="UVMap")
        uvs = np.concatenate(m.uvs_atlas())
        capa.data.foreach_set("uv", uvs.astype(np.float32).ravel())
        me.update(calc_edges=True)
        me.validate(clean_customdata=False)
        ob = bpy.data.objects.new(nombre, me)
        if coleccion is not None:
            coleccion.objects.link(ob)
        ob["triangulos"] = m.n_triangulos
        return ob


def _ajuste_como_plano(p):
    """La proyección «ajustada» de una cara expresada como proyección plana (A, b)."""
    n = _normal(p)
    z = np.array([0, 0, 1.0])
    ev = z - np.dot(z, n) * n
    if np.linalg.norm(ev) < 1e-3:
        ev = np.array([0, 1.0, 0]) - n[1] * n
    ev /= np.linalg.norm(ev)
    eu = np.cross(ev, n)
    u, v = p @ eu, p @ ev
    du, dv = max(u.max() - u.min(), 1e-9), max(v.max() - v.min(), 1e-9)
    A = np.stack([eu / du, ev / dv])
    b = np.array([-u.min() / du, -v.min() / dv])
    return A, b


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
