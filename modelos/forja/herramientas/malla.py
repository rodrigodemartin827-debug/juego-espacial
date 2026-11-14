"""
Constructor de mallas low-poly para las piezas de la forja. Todo en STUDS (1 unidad de Blender = 1 stud).

`Pieza` acumula geometría en un bmesh con un material por cara y un atributo por esquina, `tex` (vector), que es
la coordenada con la que los materiales procedurales pintan cada cara:
  * "plano": proyección por la cara dominante (para ladrillo, sillares y adoquines: u a lo largo, v hacia arriba).
  * ("veta", eje): gira la pieza para que la veta de la madera (o el rayado del metal) vaya a lo largo de `eje`,
    con un desplazamiento al azar para que cada tabla sea distinta.
  * None: la posición tal cual.
`tex` se escribe al crear cada forma, en su espacio local: si después se inclina o se mueve con `grupo()`, la veta
gira con ella.

Cada forma se construye en un bmesh temporal (ahí se bisela y se orientan las normales hacia fuera) y se copia.
"""

import math
import random
from contextlib import contextmanager

import bpy  # noqa: F401  (antes que bmesh)
import bmesh
from mathutils import Matrix, Vector

EJES = {"X": Vector((1, 0, 0)), "Y": Vector((0, 1, 0)), "Z": Vector((0, 0, 1))}


def rot(eje, grados):
    return Matrix.Rotation(math.radians(grados), 4, eje)


def tras(x, y=0.0, z=0.0):
    return Matrix.Translation(Vector((x, y, z)))


def circulo(n, r=1.0, ry=None, fase=0.0):
    ry = r if ry is None else ry
    return [(math.cos(fase + math.tau * i / n) * r, math.sin(fase + math.tau * i / n) * ry) for i in range(n)]


def rect_redondo(lx, ly, radio, por_esquina=3):
    """Rectángulo de lx × ly con las esquinas redondeadas, en sentido antihorario."""
    pts = []
    radio = min(radio, lx / 2 - 1e-4, ly / 2 - 1e-4)
    for k, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        cx, cy = sx * (lx / 2 - radio), sy * (ly / 2 - radio)
        for i in range(por_esquina):
            a = math.pi / 2 * (k + i / (por_esquina - 1))
            pts.append((cx + math.cos(a) * radio, cy + math.sin(a) * radio))
    return pts


class Pieza:
    def __init__(self, nombre, semilla=1):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.capa_tex = self.bm.loops.layers.float_vector.new("tex")
        self.mats = []
        self.rnd = random.Random(semilla)

    # ---- interno ---------------------------------------------------------------------------------------------

    def _mat(self, nombre):
        if nombre not in self.mats:
            self.mats.append(nombre)
        return self.mats.index(nombre)

    def _volcar(self, t, mat, tex="plano", recalcular=True, invertir=False, matriz=None):
        """Copia el bmesh temporal `t` a la pieza: normales, material y atributo `tex`."""
        if recalcular:
            bmesh.ops.recalc_face_normals(t, faces=t.faces[:])
        if invertir:
            bmesh.ops.reverse_faces(t, faces=t.faces[:])
        t.normal_update()
        im = self._mat(mat)
        f_tex = self._funcion_tex(tex)
        nuevos = {}
        for v in t.verts:
            nuevos[v] = self.bm.verts.new(v.co)
        for f in t.faces:
            try:
                nf = self.bm.faces.new([nuevos[v] for v in f.verts])
            except ValueError:
                continue
            nf.material_index = im
            nf.smooth = True
            n = f.normal
            for lazo, v in zip(nf.loops, f.verts):
                lazo[self.capa_tex] = f_tex(v.co, n)
        t.free()
        vs = list(nuevos.values())
        if matriz is not None:
            bmesh.ops.transform(self.bm, matrix=matriz, verts=vs)
        return vs

    def _funcion_tex(self, tex):
        if tex is None:
            return lambda co, n: co.copy()
        if tex == "plano":
            d = Vector((self.rnd.uniform(0, 40), self.rnd.uniform(0, 40), 0))

            def plano(co, n):
                ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                if az >= ax and az >= ay:
                    return Vector((co.x, co.y, co.z)) + d
                if ax >= ay:
                    return Vector((co.y, co.z, co.x)) + d
                return Vector((co.x, co.z, co.y)) + d

            return plano
        if tex == "plano_fijo":  # como "plano" pero sin desplazamiento al azar (hiladas continuas entre formas)
            def plano_fijo(co, n):
                ax, ay, az = abs(n.x), abs(n.y), abs(n.z)
                if az >= ax and az >= ay:
                    return Vector((co.x, co.y, co.z))
                if ax >= ay:
                    return Vector((co.y, co.z, co.x))
                return Vector((co.x, co.z, co.y))

            return plano_fijo
        if isinstance(tex, tuple) and tex[0] == "veta":
            eje = EJES[tex[1]] if isinstance(tex[1], str) else Vector(tex[1]).normalized()
            q = eje.rotation_difference(Vector((1, 0, 0))).to_matrix()
            if len(tex) > 2:
                d = Vector(tex[2])
            else:
                d = Vector((self.rnd.uniform(0, 30), self.rnd.uniform(0.6, 2.5), self.rnd.uniform(0.6, 2.5)))
            return lambda co, n: q @ co + d
        if callable(tex):
            return tex
        raise ValueError(tex)

    @contextmanager
    def grupo(self, matriz):
        """Todo lo que se cree dentro se transforma con `matriz` al salir (para inclinar o colocar conjuntos)."""
        antes = set(self.bm.verts)
        yield
        vs = [v for v in self.bm.verts if v not in antes]
        bmesh.ops.transform(self.bm, matrix=matriz, verts=vs)

    # ---- formas ----------------------------------------------------------------------------------------------

    def caja(self, mn, mx, mat, tex="plano", bisel=0.0, quitar="", ruido=0.0, matriz=None, cono=None,
             invertir=False):
        """
        Caja entre dos esquinas. `quitar`: caras que no se crean, p. ej. "y+ z-" (las que quedan tapadas).
        `ruido`: desplaza cada esquina al azar. `cono`: (sx, sy) estrecha la cara de arriba.
        """
        mn, mx = Vector(mn), Vector(mx)
        t = bmesh.new()
        r = bmesh.ops.create_cube(t, size=1.0)
        c, tam = (mn + mx) / 2, mx - mn
        for v in r["verts"]:
            arriba = v.co.z > 0
            v.co = Vector((c.x + v.co.x * tam.x, c.y + v.co.y * tam.y, c.z + v.co.z * tam.z))
            if cono and arriba:
                v.co.x = c.x + (v.co.x - c.x) * cono[0]
                v.co.y = c.y + (v.co.y - c.y) * cono[1]
            if ruido:
                v.co += Vector([self.rnd.uniform(-ruido, ruido) for _ in range(3)])
        t.normal_update()
        if quitar:
            nombres = quitar.split()
            fuera = []
            for f in t.faces:
                n = f.normal
                eje = max(range(3), key=lambda i: abs(n[i]))
                clave = "xyz"[eje] + ("+" if n[eje] > 0 else "-")
                if clave in nombres:
                    fuera.append(f)
            bmesh.ops.delete(t, geom=fuera, context="FACES")
        if bisel > 0:
            aristas = [e for e in t.edges if len(e.link_faces) == 2]
            bmesh.ops.bevel(t, geom=aristas, offset=bisel, offset_type="OFFSET", segments=1, profile=0.5,
                            affect="EDGES", clamp_overlap=True)
        return self._volcar(t, mat, tex, recalcular=False, matriz=matriz, invertir=invertir)

    def tabla(self, mn, mx, mat, eje=None, bisel=0.0, ruido=0.012, quitar="", matriz=None):
        """Caja con la veta a lo largo de su lado más largo (o de `eje`)."""
        tam = Vector(mx) - Vector(mn)
        if eje is None:
            eje = "XYZ"[max(range(3), key=lambda i: tam[i])]
        return self.caja(mn, mx, mat, tex=("veta", eje), bisel=bisel, ruido=ruido, quitar=quitar, matriz=matriz)

    def loft(self, anillos, mat, tex=None, tapas=(True, True), cerrado=True, invertir=False, matriz=None,
             recalcular=None):
        """Une anillos de puntos 3D (todos con el mismo número de puntos)."""
        t = bmesh.new()
        vs = [[t.verts.new(Vector(p)) for p in a] for a in anillos]
        n = len(anillos[0])
        tramos = n if cerrado else n - 1
        for k in range(len(vs) - 1):
            for i in range(tramos):
                j = (i + 1) % n
                try:
                    t.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]))
                except ValueError:
                    pass
        if cerrado and tapas[0]:
            t.faces.new(list(reversed(vs[0])))
        if cerrado and tapas[1]:
            t.faces.new(vs[-1])
        bmesh.ops.remove_doubles(t, verts=t.verts[:], dist=1e-5)
        completo = cerrado and tapas[0] and tapas[1]
        if recalcular is None:
            recalcular = completo
        return self._volcar(t, mat, tex, recalcular=recalcular, invertir=invertir, matriz=matriz)

    def cilindro(self, a, b, r, mat, n=10, r2=None, tex=None, tapas=(True, True), matriz=None, achatado=1.0):
        """Cilindro o cono truncado entre los puntos a y b."""
        a, b = Vector(a), Vector(b)
        q = (b - a).normalized().to_track_quat("Z", "Y").to_matrix()
        r2 = r if r2 is None else r2
        an = [[a + q @ Vector((x, y * achatado, 0)) for x, y in circulo(n, rr)] + [] for rr in (r,)]
        an.append([b + q @ Vector((x, y * achatado, 0)) for x, y in circulo(n, r2)])
        if tex is None:
            tex = ("veta", tuple(b - a))
        return self.loft(an, mat, tex=tex, tapas=tapas, matriz=matriz, recalcular=False)

    def torno(self, perfil, mat, n=12, centro=(0, 0, 0), tex=None, tapas=(True, True), matriz=None, fase=0.0,
              radios=None, invertir=False):
        """Revolución alrededor de Z. perfil: [(radio, z)] de abajo arriba. `radios`: factor por ángulo (irregular)."""
        c = Vector(centro)
        an = []
        for r, z in perfil:
            an.append([c + Vector((x * (radios[i] if radios else 1), y * (radios[i] if radios else 1), z))
                       for i, (x, y) in enumerate(circulo(n, r, fase=fase))])
        if tex is None:
            tex = ("veta", "Z", (0, 0, 0))
        return self.loft(an, mat, tex=tex, tapas=tapas, matriz=matriz, recalcular=False, invertir=invertir)

    def tubo(self, puntos, radio, mat, n=6, tex=None, matriz=None, achatado=1.0, fase=0.0):
        """Barre una sección a lo largo de una polilínea. `radio`: número o lista (uno por punto)."""
        pts = [Vector(p) for p in puntos]
        radios = radio if isinstance(radio, (list, tuple)) else [radio] * len(pts)
        tang = []
        for i in range(len(pts)):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, len(pts) - 1)]
            tang.append((b - a).normalized())
        # Transporte paralelo del marco para que la sección no se retuerza.
        arriba = Vector((0, 0, 1)) if abs(tang[0].z) < 0.9 else Vector((1, 0, 0))
        u = tang[0].cross(arriba).normalized()
        an = []
        for i, p in enumerate(pts):
            if i > 0:
                q = tang[i - 1].rotation_difference(tang[i])
                u = (q @ u).normalized()
            w = tang[i].cross(u).normalized()
            an.append([p + (u * x + w * y * achatado) for x, y in circulo(n, radios[i], fase=fase)])
        if tex is None:
            tex = ("veta", tuple(pts[-1] - pts[0]))
        return self.loft(an, mat, tex=tex, matriz=matriz, recalcular=True)

    def prisma(self, poligono, a, b, mat, eje="Y", tex="plano", bisel=0.0, matriz=None, quitar_tapas=False):
        """
        Extruye un polígono 2D a lo largo de un eje, entre las cotas a y b.
        eje "Y": el polígono está en XZ; eje "Z": en XY; eje "X": en YZ.
        """
        def p3(u, v, w):
            return {"Y": (u, w, v), "Z": (u, v, w), "X": (w, u, v)}[eje]

        t = bmesh.new()
        va = [t.verts.new(p3(u, v, a)) for u, v in poligono]
        vb = [t.verts.new(p3(u, v, b)) for u, v in poligono]
        n = len(poligono)
        for i in range(n):
            j = (i + 1) % n
            t.faces.new((va[i], va[j], vb[j], vb[i]))
        if not quitar_tapas:
            t.faces.new(list(reversed(va)))
            t.faces.new(vb)
        bmesh.ops.recalc_face_normals(t, faces=t.faces[:])
        if bisel > 0:
            aristas = [e for e in t.edges if len(e.link_faces) == 2]
            bmesh.ops.bevel(t, geom=aristas, offset=bisel, offset_type="OFFSET", segments=1, profile=0.5,
                            affect="EDGES", clamp_overlap=True)
        return self._volcar(t, mat, tex, recalcular=not quitar_tapas, matriz=matriz)

    def hexaedro(self, frente, fondo, mat, tex="plano", bisel=0.0, sin_fondo=False, matriz=None):
        """Bloque de 8 esquinas. frente: 4 puntos en sentido antihorario vistos desde fuera; fondo: los de detrás."""
        t = bmesh.new()
        vs = [t.verts.new(Vector(q)) for q in list(frente) + list(fondo)]
        t.faces.new(vs[0:4])
        if not sin_fondo:
            t.faces.new((vs[7], vs[6], vs[5], vs[4]))
        for i in range(4):
            j = (i + 1) % 4
            t.faces.new((vs[i], vs[i + 4], vs[j + 4], vs[j]))
        if bisel > 0:
            aristas = [e for e in t.edges if len(e.link_faces) == 2]
            bmesh.ops.bevel(t, geom=aristas, offset=bisel, offset_type="OFFSET", segments=1, profile=0.5,
                            affect="EDGES", clamp_overlap=True)
        return self._volcar(t, mat, tex, recalcular=False, matriz=matriz)

    def viga(self, a, b, ancho, grosor, mat, bisel=0.0, ruido=0.01):
        """Tabla o barra de sección ancho × grosor entre los puntos a y b (veta a lo largo)."""
        a, b = Vector(a), Vector(b)
        m = Matrix.Translation(a) @ (b - a).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        return self.caja((-ancho / 2, -grosor / 2, 0), (ancho / 2, grosor / 2, (b - a).length), mat,
                         tex=("veta", "Z"), bisel=bisel, ruido=ruido, matriz=m)

    def libre(self, verts, caras, mat, tex="plano", recalcular=True, invertir=False, matriz=None):
        t = bmesh.new()
        vs = [t.verts.new(Vector(v)) for v in verts]
        for c in caras:
            try:
                t.faces.new([vs[i] for i in c])
            except ValueError:
                pass
        return self._volcar(t, mat, tex, recalcular=recalcular, invertir=invertir, matriz=matriz)

    def remache(self, pos, normal, radio, mat, alto=None):
        """Cabeza de clavo o remache: pirámide truncada de 5 lados."""
        pos, normal = Vector(pos), Vector(normal).normalized()
        alto = alto or radio * 0.6
        return self.cilindro(pos - normal * 0.01, pos + normal * alto, radio, mat, n=5, r2=radio * 0.55,
                             tapas=(False, True))

    # ---- final -----------------------------------------------------------------------------------------------

    def transformar(self, matriz):
        bmesh.ops.transform(self.bm, matrix=matriz, verts=self.bm.verts[:])

    def objeto(self, materiales, angulo=38.0):
        """Triangula, marca las aristas duras y crea el objeto. `materiales`: {nombre: bpy material}."""
        bm = self.bm
        bmesh.ops.triangulate(bm, faces=bm.faces[:], quad_method="BEAUTY", ngon_method="BEAUTY")
        bm.normal_update()
        lim = math.radians(angulo)
        for e in bm.edges:
            if len(e.link_faces) == 2:
                e.smooth = e.calc_face_angle(0.0) < lim
        malla = bpy.data.meshes.new(self.nombre)
        bm.to_mesh(malla)
        bm.free()
        for m in self.mats:
            malla.materials.append(materiales[m])
        ob = bpy.data.objects.new(self.nombre, malla)
        bpy.context.scene.collection.objects.link(ob)
        return ob
