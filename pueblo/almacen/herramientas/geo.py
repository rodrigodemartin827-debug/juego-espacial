"""
Kit de geometría en studs (1 unidad de Blender = 1 stud de Roblox).

`Malla` acumula piezas cerradas (con volumen) en un bmesh, cada cara con su material por nombre. Todas las formas
son sólidos cerrados: al final `recalc_face_normals` deja todas las normales hacia fuera (ver `objeto()`).

Formas:
  caja / caja_de          prisma rectangular (con giro opcional)
  extruir                 polígono 2D (en un plano U-V) extruido a lo largo de W: perfiles en L, U, rampas...
  cilindro                cilindro o cono truncado a lo largo de cualquier eje
  tubo                    barrido de un círculo por una polilínea (abierta con tapas, o cerrada: eslabones, aros)
  placa_hueco             placa con un hueco rectangular (hojas de puerta, marcos)
  panel_ondulado          chapa grecada (perfil trapezoidal) con grosor, de alto variable (hastiales curvos)
"""

import math

import bpy  # noqa: F401  (antes que bmesh)
import bmesh
from mathutils import Matrix, Vector

X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def rot_z(grados):
    return Matrix.Rotation(math.radians(grados), 3, "Z")


def rot(grados, eje):
    return Matrix.Rotation(math.radians(grados), 3, eje)


class Malla:
    def __init__(self, nombre):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.mats = []

    # ---- utilidades -----------------------------------------------------------------------------------------

    def mi(self, mat):
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _v(self, p):
        return self.bm.verts.new(Vector(p))

    def _f(self, vs, mat):
        f = self.bm.faces.new(vs)
        f.material_index = self.mi(mat)
        return f

    def unir(self, otra, matriz=None):
        """Copia otra Malla dentro de esta (con una matriz 4x4 opcional)."""
        mapa = {}
        for v in otra.bm.verts:
            co = v.co.copy()
            if matriz is not None:
                co = matriz @ co
            mapa[v] = self.bm.verts.new(co)
        for f in otra.bm.faces:
            self._f([mapa[v] for v in f.verts], otra.mats[f.material_index])
        return self

    # ---- formas -----------------------------------------------------------------------------------------------

    def caja(self, centro, tam, mat, giro=None, mats=None):
        """Caja de tamaño `tam` centrada en `centro`. `mats` = {'+z': 'otro', ...} cambia el material de una cara."""
        c = Vector(centro)
        hx, hy, hz = tam[0] / 2, tam[1] / 2, tam[2] / 2
        g = giro if giro is not None else Matrix.Identity(3)
        pts = [c + g @ Vector((sx * hx, sy * hy, sz * hz)) for sz in (-1, 1) for sy in (-1, 1) for sx in (-1, 1)]
        v = [self._v(p) for p in pts]
        caras = {"-z": (0, 2, 3, 1), "+z": (4, 5, 7, 6), "-y": (0, 1, 5, 4), "+y": (2, 6, 7, 3),
                 "-x": (0, 4, 6, 2), "+x": (1, 3, 7, 5)}
        out = []
        for k, idx in caras.items():
            m = (mats or {}).get(k, mat)
            out.append(self._f([v[i] for i in idx], m))
        return out

    def caja_de(self, mn, mx, mat, mats=None):
        mn, mx = Vector(mn), Vector(mx)
        return self.caja((mn + mx) / 2, mx - mn, mat, mats=mats)

    def extruir(self, perfil, origen, U, V, W, mat, mat_tapas=None, mats_lados=None):
        """
        Extruye el polígono `perfil` [(u, v), ...] situado en el plano (origen, U, V) a lo largo del vector W.
        `mats_lados[i]` = material del lado i (opcional).
        """
        o, U, V, W = Vector(origen), Vector(U), Vector(V), Vector(W)
        a = [self._v(o + U * u + V * v) for u, v in perfil]
        b = [self._v(o + U * u + V * v + W) for u, v in perfil]
        n = len(perfil)
        for i in range(n):
            j = (i + 1) % n
            m = mats_lados[i] if mats_lados else mat
            self._f((a[i], a[j], b[j], b[i]), m)
        self._f(list(reversed(a)), mat_tapas or mat)
        self._f(b, mat_tapas or mat)
        return a, b

    def loft(self, anillos, mat, tapas=True, cerrado_anillo=True, mat_tapas=None):
        vs = [[self._v(p) for p in a] for a in anillos]
        n = len(anillos[0])
        tramos = n if cerrado_anillo else n - 1
        for k in range(len(vs) - 1):
            for i in range(tramos):
                j = (i + 1) % n
                self._f((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]), mat)
        if tapas:
            self._f(list(reversed(vs[0])), mat_tapas or mat)
            self._f(vs[-1], mat_tapas or mat)
        return vs

    def cilindro(self, base, radio, alto, mat, lados=12, eje=Z, radio2=None, mat_tapas=None, giro=0.0):
        eje = Vector(eje).normalized()
        q = eje.to_track_quat("Z", "Y").to_matrix()
        base = Vector(base)
        r2 = radio if radio2 is None else radio2
        anillos = []
        for h, r in ((0.0, radio), (alto, r2)):
            anillos.append([base + q @ Vector((math.cos(giro + math.tau * i / lados) * r,
                                               math.sin(giro + math.tau * i / lados) * r, h)) for i in range(lados)])
        return self.loft(anillos, mat, mat_tapas=mat_tapas)

    def cilindro_anillos(self, base, eje, perfil, mat, lados=12, mat_tapas=None):
        """Sólido de revolución: perfil = [(altura, radio), ...] a lo largo de `eje` (bidones, extintor, focos)."""
        eje = Vector(eje).normalized()
        q = eje.to_track_quat("Z", "Y").to_matrix()
        base = Vector(base)
        anillos = [[base + q @ Vector((math.cos(math.tau * i / lados) * r, math.sin(math.tau * i / lados) * r, h))
                    for i in range(lados)] for h, r in perfil]
        return self.loft(anillos, mat, mat_tapas=mat_tapas)

    def tubo(self, puntos, radio, mat, lados=8, cerrado=False, tapas=True):
        """Barrido de un círculo por la polilínea `puntos` con marcos de rotación mínima."""
        P = [Vector(p) for p in puntos]
        n = len(P)
        tang = []
        for i in range(n):
            if cerrado:
                t = (P[(i + 1) % n] - P[i - 1])
            else:
                t = (P[min(i + 1, n - 1)] - P[max(i - 1, 0)])
            tang.append(t.normalized())
        # primer marco
        ref = Z if abs(tang[0].dot(Z)) < 0.9 else X
        nrm = tang[0].cross(ref).normalized()
        anillos = []
        for i in range(n):
            if i > 0:
                # transporte paralelo
                ejev = tang[i - 1].cross(tang[i])
                if ejev.length > 1e-6:
                    ang = tang[i - 1].angle(tang[i])
                    nrm = (Matrix.Rotation(ang, 3, ejev.normalized()) @ nrm).normalized()
            bi = tang[i].cross(nrm).normalized()
            # en las esquinas se ensancha la sección para que el tubo no se estrangule
            esc = 1.0
            if 0 < i < n - 1 or cerrado:
                a = (P[(i + 1) % n] - P[i]).normalized()
                b = (P[i] - P[i - 1]).normalized()
                cosm = max(0.5, math.cos(a.angle(b) / 2)) if a.length and b.length else 1.0
                esc = 1.0 / cosm
            anillos.append([P[i] + (nrm * math.cos(math.tau * k / lados) * esc + bi * math.sin(math.tau * k / lados))
                            * radio for k in range(lados)])
        if cerrado:
            vs = [[self._v(p) for p in a] for a in anillos]
            for k in range(n):
                k2 = (k + 1) % n
                for i in range(lados):
                    j = (i + 1) % lados
                    self._f((vs[k][i], vs[k][j], vs[k2][j], vs[k2][i]), mat)
            return vs
        return self.loft(anillos, mat, tapas=tapas)

    def placa_hueco(self, origen, U, V, W, ancho, alto, hueco, mat, mat_canto=None):
        """
        Placa de ancho x alto (en el plano U-V desde `origen`, esquina inferior izquierda) con grosor W y un hueco
        rectangular hueco = (u0, v0, u1, v1).
        """
        o, U, V, W = Vector(origen), Vector(U), Vector(V), Vector(W)
        u0, v0, u1, v1 = hueco
        ext = [(0, 0), (ancho, 0), (ancho, alto), (0, alto)]
        inn = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        cap = []
        for d in (Vector(), W):
            cap.append(([self._v(o + U * a + V * b + d) for a, b in ext],
                        [self._v(o + U * a + V * b + d) for a, b in inn]))
        (ea, ia), (eb, ib) = cap
        for i in range(4):
            j = (i + 1) % 4
            self._f((ea[i], ea[j], ia[j], ia[i]), mat)          # cara delantera (anillo)
            self._f((eb[i], ib[i], ib[j], eb[j]), mat)          # cara trasera
            self._f((ea[i], eb[i], eb[j], ea[j]), mat_canto or mat)  # canto exterior
            self._f((ia[i], ia[j], ib[j], ib[i]), mat_canto or mat)  # canto del hueco

    def panel_ondulado(self, origen, U, N, u0, u1, z_abajo, z_arriba, mat, periodo=0.7, fondo=0.07,
                       grosor=0.06, mat_dentro=None, fase=0.0):
        """
        Chapa grecada vertical: las ondas corren a lo largo de U (horizontal), N es la normal hacia fuera.
        z_abajo(u) y z_arriba(u): alto de la chapa en cada punto (para hastiales curvos).
        El perfil es trapezoidal (cresta y valle planos, flancos inclinados): 4 vértices por periodo.
        """
        o, U, N = Vector(origen), Vector(U).normalized(), Vector(N).normalized()
        # posiciones del perfil (fracción del periodo, salida hacia fuera)
        perfil = [(0.0, 0.0), (0.18, 1.0), (0.5, 1.0), (0.68, 0.0)]
        us = []
        k = math.floor((u0 - fase) / periodo) - 1
        while True:
            base = fase + k * periodo
            for f, s in perfil:
                u = base + f * periodo
                if u0 < u < u1:
                    us.append((u, s))
            if base > u1:
                break
            k += 1

        def salida(u):
            # interpola la salida del perfil en u (para los extremos)
            t = ((u - fase) / periodo) % 1.0
            pts = perfil + [(1.0, 0.0)]
            for (fa, sa), (fb, sb) in zip(pts, pts[1:]):
                if fa <= t <= fb:
                    return sa + (sb - sa) * (t - fa) / max(1e-9, fb - fa)
            return 0.0

        us = [(u0, salida(u0))] + us + [(u1, salida(u1))]
        n = len(us) - 1
        muestras = [u0 + (u1 - u0) * t / 8 for t in range(9)]
        abajo_plano = max(z_abajo(u) for u in muestras) - min(z_abajo(u) for u in muestras) < 1e-6
        arriba_plano = max(z_arriba(u) for u in muestras) - min(z_arriba(u) for u in muestras) < 1e-6
        ob, ot, ib, it = [], [], [], []
        for k_, (u, s) in enumerate(us):
            p = o + U * u
            za, zb = z_abajo(u), z_arriba(u)
            out = N * (fondo * s)
            ob.append(self._v(p + out + Z * za))
            ot.append(self._v(p + out + Z * zb))
            extremo = k_ in (0, n)
            ib.append(self._v(p - N * grosor + Z * za) if (extremo or not abajo_plano) else None)
            it.append(self._v(p - N * grosor + Z * zb) if (extremo or not arriba_plano) else None)
        md = mat_dentro or mat
        for i in range(n):
            j = i + 1
            self._f((ob[i], ob[j], ot[j], ot[i]), mat)
            if not arriba_plano:
                self._f((ot[i], ot[j], it[j], it[i]), mat)
            if not abajo_plano:
                self._f((ob[j], ob[i], ib[i], ib[j]), mat)
        if arriba_plano:
            self._f(ot + [it[n], it[0]], mat)
        if abajo_plano:
            self._f(list(reversed(ob)) + [ib[0], ib[n]], mat)
        # cara de dentro (plana): abajo y arriba con los vértices que existan
        ibs = [v for v in ib if v is not None]
        its = [v for v in it if v is not None]
        self._f(list(reversed(ibs)) + its, md)
        self._f((ob[0], ot[0], it[0], ib[0]), mat)
        self._f((ob[n], ib[n], it[n], ot[n]), mat)

    def transformar(self, matriz):
        bmesh.ops.transform(self.bm, matrix=matriz, verts=self.bm.verts)
        return self

    # ---- objeto -------------------------------------------------------------------------------------------------

    def objeto(self, materiales, coleccion=None, origen=None, quitar_apoyos=()):
        """
        Crea el objeto. Normales hacia fuera (cada pieza es un sólido cerrado) y sin polígonos de más de 4 lados.
        `materiales`: {nombre: bpy.types.Material}. `origen`: punto (studs) donde queda el origen del objeto.
        """
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        _corregir_cerradas(bm)
        if quitar_apoyos:
            # caras de abajo apoyadas en el suelo, el muelle o el suelo interior: no se ven nunca
            bm.normal_update()
            fuera = [f for f in bm.faces if f.normal.z < -0.995 and
                     any(abs(f.calc_center_median().z - z) < 0.004 for z in quitar_apoyos)]
            bmesh.ops.delete(bm, geom=fuera, context="FACES_ONLY")
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(bm, faces=ngons, ngon_method="BEAUTY")
        malla = bpy.data.meshes.new(self.nombre)
        bm.to_mesh(malla)
        bm.free()
        obj = bpy.data.objects.new(self.nombre, malla)
        (coleccion or bpy.context.scene.collection).objects.link(obj)
        for n in self.mats:
            malla.materials.append(materiales[n])
        if origen is not None:
            o = Vector(origen)
            malla.transform(Matrix.Translation(-o))
            obj.location = o
        return obj


def _componentes(bm):
    visto, comps = set(), []
    bm.faces.ensure_lookup_table()
    for f0 in bm.faces:
        if f0.index in visto:
            continue
        pila, comp = [f0], []
        visto.add(f0.index)
        while pila:
            f = pila.pop()
            comp.append(f)
            for e in f.edges:
                for h in e.link_faces:
                    if h.index not in visto:
                        visto.add(h.index)
                        pila.append(h)
        comps.append(comp)
    return comps


def _corregir_cerradas(bm):
    """Red de seguridad: un sólido cerrado con volumen negativo (piezas muy finas) se da la vuelta."""
    bm.faces.index_update()
    for comp in _componentes(bm):
        if not all(len(e.link_faces) == 2 for f in comp for e in f.edges):
            continue
        vol = 0.0
        for f in comp:
            vs = [v.co for v in f.verts]
            for i in range(1, len(vs) - 1):
                vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6
        if vol < 0:
            bmesh.ops.reverse_faces(bm, faces=comp)


def triangulos(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def volumen_firmado(obj):
    """Volumen con signo de cada pieza conexa: negativo = normales hacia dentro."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    bm.normal_update()
    visto, malas, total = set(), 0, 0
    for f0 in bm.faces:
        if f0.index in visto:
            continue
        pila, comp = [f0], []
        visto.add(f0.index)
        while pila:
            f = pila.pop()
            comp.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in visto:
                        visto.add(g.index)
                        pila.append(g)
        # cara "hacia dentro" = su normal apunta hacia el centro de su pieza (vale para piezas abiertas por abajo)
        cen = sum((f.calc_center_median() * f.calc_area() for f in comp), Vector()) / max(1e-9, sum(f.calc_area() for f in comp))
        dentro = sum(f.calc_area() for f in comp if f.normal.dot(f.calc_center_median() - cen) < -1e-6)
        total += 1
        cerrada = all(len(e.link_faces) == 2 for f in comp for e in f.edges)
        if cerrada:
            vol = 0.0
            for f in comp:
                vs = [v.co for v in f.verts]
                for i in range(1, len(vs) - 1):
                    vol += vs[0].dot(vs[i].cross(vs[i + 1])) / 6
            mala = vol < -1e-9
        else:
            mala = dentro > 0.5 * sum(f.calc_area() for f in comp)
        if mala:
            malas += 1
            print("   [normales] pieza hacia dentro:", obj.name, obj.data.materials[comp[0].material_index].name,
                  tuple(round(v, 2) for v in cen), len(comp), "caras")
    bm.free()
    return total, malas
