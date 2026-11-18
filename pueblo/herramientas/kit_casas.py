"""
Kit para modelar las casas del pueblo con Blender sin pantalla (bpy).

Convenciones (las de las casas del pueblo, distintas de las de `modelos/`):
  * 1 unidad de Blender = 1 stud de Roblox. Se modela directamente en studs.
  * El frente de la casa mira a -Y en Blender. Antes de exportar se gira 180° sobre el eje vertical
    (GIRO_IMPORTACION, el eje Y de Roblox) y el FBX sale con los ejes por defecto de Blender: el frente llega
    a Studio mirando a -Z, que es el «delante» de Roblox.
  * Todas las piezas comparten UN atlas de 2048 × 2048 con cinco mapas horneados: color, normal, rugosidad,
    metalicidad y emisión. Los materiales se escriben como sombreadores procedurales (nodos) y se hornean.

Qué hay aquí:
  * `Malla`: acumula geometría en un bmesh con material por cara, segundo mapa UV «decal» (para letreros,
    teclados, células solares...), y marca qué aristas llevan bisel.
  * `Nodos`: escribir sombreadores con operadores de Python (a + b * c) en lugar de cablear nodos a mano.
  * Atlas: despliegue UV común con densidad por material, horneado de los cinco mapas y material final.
  * Render: estudio con cielo, vistas de giro y hoja de contactos.
  * Exportación FBX (Apply Scalings: FBX All).
"""

import math
import os

import bpy  # noqa: F401  (antes que bmesh)
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from PIL import Image, ImageDraw, ImageFont

GIRO_IMPORTACION = 180.0  # grados sobre el eje vertical (Y de Roblox, Z de Blender), justo antes de exportar
TAM_ATLAS = 2048

DIRS = {
    "-x": Vector((-1, 0, 0)), "+x": Vector((1, 0, 0)),
    "-y": Vector((0, -1, 0)), "+y": Vector((0, 1, 0)),
    "-z": Vector((0, 0, -1)), "+z": Vector((0, 0, 1)),
}


# ==============================================================================================================
# Utilidades de matrices
# ==============================================================================================================


def marco(origen, eje_z, eje_x=None):
    """Matriz 4x4 con el origen y el eje Z local dados (eje X aproximado opcional)."""
    z = Vector(eje_z).normalized()
    if eje_x is None:
        eje_x = Vector((1, 0, 0)) if abs(z.x) < 0.9 else Vector((0, 1, 0))
    x = Vector(eje_x)
    x = (x - z * x.dot(z)).normalized()
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = Vector(origen)
    return m


def rot(grados, eje="Z"):
    return Matrix.Rotation(math.radians(grados), 3, eje)


# ==============================================================================================================
# Malla: geometría con materiales por cara
# ==============================================================================================================


class Malla:
    """Geometría de una pieza (un MeshPart en Roblox). Todo en studs."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.uv_decal = self.bm.loops.layers.uv.new("decal")
        self.mats = []
        self.bisel = set()  # vértices de elementos con bisel

    # ---- materiales -------------------------------------------------------------------------------------

    def m(self, nombre):
        if nombre not in self.mats:
            self.mats.append(nombre)
        return self.mats.index(nombre)

    def _cara(self, verts, mat, normal=None):
        f = self.bm.faces.new(verts)
        f.material_index = self.m(mat)
        if normal is not None:
            f.normal_update()
            if f.normal.dot(normal) < 0:
                f.normal_flip()
        return f

    def _fin(self, verts, caras, bisel, cerrado=True):
        if cerrado and caras:
            bmesh.ops.recalc_face_normals(self.bm, faces=caras)
        if bisel:
            self.bisel.update(verts)
        return verts

    # ---- formas -----------------------------------------------------------------------------------------

    def caja(self, centro, tam, mat, giro=None, mats=None, decal=None, quitar=(), bisel=False, invertida=False,
             rect=None):
        """
        Caja de tamaño `tam` centrada en `centro`.
          giro: Matrix 3x3; mats: {"+z": "otro_material", ...}; decal: cara que lleva el mapa UV «decal»
          (o lista de caras); quitar: caras que no se crean (las que quedan pegadas a otra superficie);
          invertida: normales hacia dentro (huecos interiores).
        """
        tx, ty, tz = (t / 2 for t in tam)
        g = giro if giro is not None else Matrix.Identity(3)
        c = Vector(centro)
        v = {}
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    v[(sx, sy, sz)] = self.bm.verts.new(c + g @ Vector((sx * tx, sy * ty, sz * tz)))
        caras_def = {
            "-x": [(-1, -1, -1), (-1, 1, -1), (-1, 1, 1), (-1, -1, 1)],
            "+x": [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)],
            "-y": [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)],
            "+y": [(-1, 1, -1), (1, 1, -1), (1, 1, 1), (-1, 1, 1)],
            "-z": [(-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1)],
            "+z": [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
        }
        decales = (decal,) if isinstance(decal, str) else tuple(decal or ())
        caras = []
        for d, idx in caras_def.items():
            if d in quitar:
                continue
            n = g @ DIRS[d]
            if invertida:
                n = -n
            f = self._cara([v[k] for k in idx], (mats or {}).get(d, mat), n)
            caras.append(f)
            if d in decales:
                self._uv_decal_caja(f, d, g, c, (tx, ty, tz), rect)
        usados = {x for f in caras for x in f.verts}
        for k, x in v.items():
            if x not in usados:
                self.bm.verts.remove(x)
        if bisel:
            self.bisel.update(usados)
        return usados

    def caja_de(self, mn, mx, mat, **kw):
        mn, mx = Vector(mn), Vector(mx)
        return self.caja((mn + mx) / 2, mx - mn, mat, **kw)

    def _uv_decal_caja(self, f, d, g, c, medio, rect=None):
        """UV 0..1 en la cara `d`, derecha y arriba vistas desde fuera (o dentro de `rect` = (u0, v0, u1, v1))."""
        n = DIRS[d]
        arriba = Vector((0, 0, 1)) if abs(n.z) < 0.5 else Vector((0, 1, 0))
        derecha = arriba.cross(n)
        if n.z < -0.5:
            derecha = -derecha
        gi = g.inverted()
        for lp in f.loops:
            loc = gi @ (lp.vert.co - c)
            ext_d = sum(abs(derecha[i]) * medio[i] for i in range(3))
            ext_a = sum(abs(arriba[i]) * medio[i] for i in range(3))
            u, v = loc.dot(derecha) / (2 * ext_d) + 0.5, loc.dot(arriba) / (2 * ext_a) + 0.5
            if rect is not None:
                u, v = rect[0] + u * (rect[2] - rect[0]), rect[1] + v * (rect[3] - rect[1])
            lp[self.uv_decal].uv = (u, v)

    def loft(self, anillos, mat, tapar_inicio=True, tapar_fin=True, cerrado=True, bisel=False, mat_tapa=None,
             decal_tapa=False, recalcular=True):
        bm = self.bm
        vs = [[bm.verts.new(Vector(p)) for p in a] for a in anillos]
        n = len(anillos[0])
        tramos = n if cerrado else n - 1
        caras = []
        for k in range(len(vs) - 1):
            for i in range(tramos):
                j = (i + 1) % n
                caras.append(self._cara((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]), mat))
        tapas = []
        if tapar_inicio and cerrado:
            tapas.append(self._cara(list(reversed(vs[0])), mat_tapa or mat))
        if tapar_fin and cerrado:
            tapas.append(self._cara(vs[-1], mat_tapa or mat))
        caras += tapas
        todos = [v for a in vs for v in a]
        if recalcular:
            self._fin(todos, caras, bisel, cerrado=tapar_inicio and tapar_fin and cerrado)
        elif bisel:
            self.bisel.update(todos)
        if decal_tapa and tapas:
            self._uv_decal_plana(tapas[-1])
        return todos

    def _uv_decal_plana(self, f):
        """UV 0..1 por la caja de la cara (para tapas de cilindros y polígonos)."""
        f.normal_update()
        n = f.normal
        arriba = Vector((0, 0, 1)) if abs(n.z) < 0.7 else Vector((0, 1, 0))
        derecha = arriba.cross(n).normalized()
        arriba = n.cross(derecha).normalized()
        ps = [(lp.vert.co.dot(derecha), lp.vert.co.dot(arriba)) for lp in f.loops]
        u0, u1 = min(p[0] for p in ps), max(p[0] for p in ps)
        v0, v1 = min(p[1] for p in ps), max(p[1] for p in ps)
        for lp, (u, v) in zip(f.loops, ps):
            lp[self.uv_decal].uv = ((u - u0) / max(u1 - u0, 1e-6), (v - v0) / max(v1 - v0, 1e-6))

    def cilindro(self, base, radio, alto, mat, lados=8, eje=(0, 0, 1), radio2=None, tapas=True, mat_tapa=None,
                 decal_tapa=False, bisel=False, giro=0.0, eje_x=None, tapa_base=True):
        """Cilindro (o tronco de cono con `radio2`) desde `base` a lo largo de `eje`."""
        r2 = radio if radio2 is None else radio2
        mtx = marco(base, eje, eje_x)
        a0, a1 = [], []
        for i in range(lados):
            a = math.radians(giro) + math.tau * (i + 0.5) / lados
            a0.append(mtx @ Vector((math.cos(a) * radio, math.sin(a) * radio, 0)))
            a1.append(mtx @ Vector((math.cos(a) * r2, math.sin(a) * r2, alto)))
        return self.loft([a0, a1], mat, tapas and tapa_base, tapas, bisel=bisel, mat_tapa=mat_tapa,
                         decal_tapa=decal_tapa)

    def tubo(self, puntos, radio, mat, lados=6, tapas=True, bisel=False):
        """Tubo a lo largo de una polilínea, con inglete en cada codo (cables, barandillas, patas)."""
        pts = [Vector(p) for p in puntos]
        anillos = []
        ref = None
        for k, p in enumerate(pts):
            if k == 0:
                t = (pts[1] - p).normalized()
            elif k == len(pts) - 1:
                t = (p - pts[k - 1]).normalized()
            else:
                t = ((p - pts[k - 1]).normalized() + (pts[k + 1] - p).normalized()).normalized()
            if ref is None:
                ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            x = (ref - t * ref.dot(t)).normalized()
            y = t.cross(x)
            ref = x
            # Factor del inglete: el anillo del codo se estira para que el tubo no se estreche.
            esc = 1.0
            if 0 < k < len(pts) - 1:
                d1 = (p - pts[k - 1]).normalized()
                esc = 1.0 / max(0.35, abs(d1.dot(t)))
            anillo = []
            for i in range(lados):
                a = math.tau * (i + 0.5) / lados
                off = x * math.cos(a) + y * math.sin(a)
                # solo se estira la componente en el plano de giro
                if esc != 1.0:
                    d1 = (p - pts[k - 1]).normalized()
                    plano = (d1 - t * d1.dot(t))
                    if plano.length > 1e-6:
                        plano.normalize()
                        off = off + plano * off.dot(plano) * (esc - 1.0)
                anillo.append(p + off * radio)
            anillos.append(anillo)
        return self.loft(anillos, mat, tapas, tapas, bisel=bisel)

    def extruir(self, poligono, z0, z1, mtx, mat, mat_tapa=None, decal_tapa=False, bisel=False,
                mat_tapa_inf=None):
        """Polígono (lista de (x, y) en el plano local) extruido entre z0 y z1 y llevado con `mtx` (4x4)."""
        a = [mtx @ Vector((x, y, z0)) for x, y in poligono]
        b = [mtx @ Vector((x, y, z1)) for x, y in poligono]
        vs = self.loft([a, b], mat, True, True, bisel=bisel, mat_tapa=mat_tapa, decal_tapa=decal_tapa)
        if mat_tapa_inf:
            # la tapa inicial es la penúltima cara
            caras = list(self.bm.faces)
            caras[-2].material_index = self.m(mat_tapa_inf)
        return vs

    def toro(self, centro, R, r, mat, eje=(0, 0, 1), n1=12, n2=6, bisel=False):
        mtx = marco(centro, eje)
        anillos = []
        for i in range(n1 + 1):
            a = math.tau * i / n1
            ca, sa = math.cos(a), math.sin(a)
            anillo = []
            for j in range(n2):
                b = math.tau * j / n2
                rr = R + r * math.cos(b)
                anillo.append(mtx @ Vector((ca * rr, sa * rr, r * math.sin(b))))
            anillos.append(anillo)
        bm = self.bm
        vs = [[bm.verts.new(p) for p in a] for a in anillos[:-1]]
        caras = []
        for i in range(n1):
            k = (i + 1) % n1
            for j in range(n2):
                jj = (j + 1) % n2
                caras.append(self._cara((vs[i][j], vs[k][j], vs[k][jj], vs[i][jj]), mat))
        todos = [v for a in vs for v in a]
        return self._fin(todos, caras, bisel)

    def esfera(self, centro, radio, mat, lados=8, anillos=5, escala=(1, 1, 1)):
        bm = self.bm
        c = Vector(centro)
        polo_s = bm.verts.new(c + Vector((0, 0, -radio * escala[2])))
        polo_n = bm.verts.new(c + Vector((0, 0, radio * escala[2])))
        filas = []
        for k in range(1, anillos):
            t = math.pi * k / anillos - math.pi / 2
            fila = []
            for i in range(lados):
                a = math.tau * i / lados
                fila.append(bm.verts.new(c + Vector((math.cos(t) * math.cos(a) * radio * escala[0],
                                                     math.cos(t) * math.sin(a) * radio * escala[1],
                                                     math.sin(t) * radio * escala[2]))))
            filas.append(fila)
        caras = []
        for i in range(lados):
            j = (i + 1) % lados
            caras.append(self._cara((polo_s, filas[0][j], filas[0][i]), mat))
            caras.append(self._cara((polo_n, filas[-1][i], filas[-1][j]), mat))
            for k in range(len(filas) - 1):
                caras.append(self._cara((filas[k][i], filas[k][j], filas[k + 1][j], filas[k + 1][i]), mat))
        todos = [polo_s, polo_n] + [v for f in filas for v in f]
        return self._fin(todos, caras, False)

    def casquete(self, centro, eje, radio, grosor, mat, lados=8, anillos=3, mat_dentro=None):
        """Media esfera hueca con borde (cazoletas del anemómetro): grosor real."""
        mtx = marco(centro, eje)
        bm = self.bm

        def capa(r):
            polo = bm.verts.new(mtx @ Vector((0, 0, -r)))
            filas = []
            for k in range(1, anillos + 1):
                t = (math.pi / 2) * k / anillos
                fila = [bm.verts.new(mtx @ Vector((math.sin(t) * math.cos(math.tau * i / lados) * r,
                                                   math.sin(t) * math.sin(math.tau * i / lados) * r,
                                                   -math.cos(t) * r))) for i in range(lados)]
                filas.append(fila)
            return polo, filas

        po, fo = capa(radio)
        pi_, fi = capa(radio - grosor)
        caras = []
        md = mat_dentro or mat
        for i in range(lados):
            j = (i + 1) % lados
            caras.append(self._cara((po, fo[0][i], fo[0][j]), mat))
            caras.append(self._cara((pi_, fi[0][j], fi[0][i]), md))
            for k in range(anillos - 1):
                caras.append(self._cara((fo[k][i], fo[k + 1][i], fo[k + 1][j], fo[k][j]), mat))
                caras.append(self._cara((fi[k][j], fi[k + 1][j], fi[k + 1][i], fi[k][i]), md))
            caras.append(self._cara((fo[-1][i], fi[-1][i], fi[-1][j], fo[-1][j]), mat))
        todos = [po, pi_] + [v for f in fo + fi for v in f]
        return self._fin(todos, caras, False)

    def placa(self, eje, a_ext, a_int, u_rng, v_rng, huecos, mat_ext, mat_int, mat_canto=None,
              cantos=("u0", "u1", "v0", "v1"), bisel=False):
        """
        Placa (pared o losa) perpendicular a `eje` ('x', 'y' o 'z'), entre a_ext (cara de fuera) y a_int (cara de
        dentro), en el rectángulo u_rng × v_rng de los otros dos ejes (x→(y, z), y→(x, z), z→(x, y)), con huecos
        rectangulares pasantes (u0, u1, v0, v1). Los vértices se comparten: no quedan caras escondidas dentro.
        Los cantos de los huecos se crean siempre; los del borde, solo los de `cantos`.
        """
        i_n, i_u, i_v = {"x": (0, 1, 2), "y": (1, 0, 2), "z": (2, 0, 1)}[eje]
        sgn = 1.0 if a_ext > a_int else -1.0
        n_ext = Vector([0, 0, 0])
        n_ext[i_n] = sgn

        def p(a, u, v):
            c = [0.0, 0.0, 0.0]
            c[i_n], c[i_u], c[i_v] = a, u, v
            return Vector(c)

        us = sorted({u_rng[0], u_rng[1]} | {h[0] for h in huecos} | {h[1] for h in huecos})
        vs = sorted({v_rng[0], v_rng[1]} | {h[2] for h in huecos} | {h[3] for h in huecos})

        def solido(i, j):
            if i < 0 or j < 0 or i >= len(us) - 1 or j >= len(vs) - 1:
                return None
            cu, cv = (us[i] + us[i + 1]) / 2, (vs[j] + vs[j + 1]) / 2
            return not any(h[0] < cu < h[1] and h[2] < cv < h[3] for h in huecos)

        cache = {}

        def vert(i, j, lado):
            k = (i, j, lado)
            if k not in cache:
                cache[k] = self.bm.verts.new(p(a_ext if lado == 0 else a_int, us[i], vs[j]))
            return cache[k]

        mc = mat_canto or mat_ext
        for i in range(len(us) - 1):
            for j in range(len(vs) - 1):
                if not solido(i, j):
                    continue
                q = ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))
                self._cara([vert(a, b, 0) for a, b in q], mat_ext, n_ext)
                self._cara([vert(a, b, 1) for a, b in q], mat_int, -n_ext)
                for di, dj, borde, arista in ((-1, 0, "u0", ((i, j), (i, j + 1))),
                                              (1, 0, "u1", ((i + 1, j), (i + 1, j + 1))),
                                              (0, -1, "v0", ((i, j), (i + 1, j))),
                                              (0, 1, "v1", ((i, j + 1), (i + 1, j + 1)))):
                    vecino = solido(i + di, j + dj)
                    if vecino is True:
                        continue
                    if vecino is None and borde not in cantos:
                        continue
                    nrm = Vector([0, 0, 0])
                    nrm[i_u], nrm[i_v] = di, dj
                    (a1, b1), (a2, b2) = arista
                    self._cara([vert(a1, b1, 0), vert(a2, b2, 0), vert(a2, b2, 1), vert(a1, b1, 1)],
                               mc if vecino is False else mat_ext if borde in cantos else mc, nrm)
        if bisel:
            self.bisel.update(cache.values())
        return set(cache.values())

    def transformar(self, verts, mtx):
        bmesh.ops.transform(self.bm, matrix=mtx, verts=list(verts))

    def triangulos(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)

    # ---- objeto -----------------------------------------------------------------------------------------

    def objeto(self, materiales, bisel=0.045, coleccion=None):
        """Crea el objeto: triangula polígonos de más de 4 lados, marca las aristas del bisel y lo aplica."""
        bm = self.bm
        ngons = [f for f in bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(bm, faces=ngons, quad_method="BEAUTY", ngon_method="BEAUTY")
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        capa = bm.edges.layers.float.get("bevel_weight_edge") or bm.edges.layers.float.new("bevel_weight_edge")
        n_bisel = 0
        for e in bm.edges:
            if len(e.link_faces) == 2 and all(v in self.bisel for v in e.verts):
                # solo las aristas largas: en piezas diminutas el bisel no se ve y cuesta triángulos
                if e.calc_face_angle(0) > math.radians(32) and e.calc_length() >= 0.45:
                    e[capa] = 1.0
                    n_bisel += 1
        malla = bpy.data.meshes.new(self.nombre)
        bm.to_mesh(malla)
        bm.free()
        obj = bpy.data.objects.new(self.nombre, malla)
        (coleccion or bpy.context.scene.collection).objects.link(obj)
        for n in self.mats:
            malla.materials.append(materiales(n))
        if bisel and n_bisel:
            mod = obj.modifiers.new("bisel", "BEVEL")
            mod.width = bisel
            mod.segments = 1
            mod.limit_method = "WEIGHT"
            mod.miter_outer = "MITER_ARC"
            aplicar_modificadores(obj)
        sombreado(obj)
        return obj


def aplicar_modificadores(obj):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def sombreado(obj, angulo=33):
    """Normales suaves con corte por ángulo (las aristas vivas, vivas; los cilindros, redondos)."""
    for p in obj.data.polygons:
        p.use_smooth = True
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(angulo))
    aplicar_modificadores(obj)


def triangulos(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


# ==============================================================================================================
# Nodos: sombreadores escritos con operadores
# ==============================================================================================================


class S:
    """Un enchufe de salida de un nodo (escalar 'f' o vector/color 'v') con operadores que crean nodos."""

    def __init__(self, g, sock, tipo="f"):
        self.g, self.s, self.t = g, sock, tipo

    # escalares y vectores
    def _op(self, op, otro, inv=False):
        es_v = self.t == "v" or (isinstance(otro, S) and otro.t == "v") or isinstance(otro, tuple)
        a, b = (otro, self) if inv else (self, otro)
        if not es_v:
            return self.g.math(op, a, b)
        vop = {"ADD": "ADD", "SUBTRACT": "SUBTRACT", "MULTIPLY": "MULTIPLY", "DIVIDE": "DIVIDE"}[op]
        # escalar por vector -> SCALE
        if op == "MULTIPLY" and (not isinstance(b, S) or b.t == "f") and not isinstance(b, tuple):
            return self.g.vmath("SCALE", a, escala=b)
        if op == "MULTIPLY" and isinstance(a, S) and a.t == "f":
            return self.g.vmath("SCALE", b, escala=a)
        if op == "MULTIPLY" and not isinstance(a, (S, tuple)):
            return self.g.vmath("SCALE", b, escala=a)
        return self.g.vmath(vop, self.g.vec(a), self.g.vec(b))

    def __add__(self, o): return self._op("ADD", o)
    def __radd__(self, o): return self._op("ADD", o, True)
    def __sub__(self, o): return self._op("SUBTRACT", o)
    def __rsub__(self, o): return self._op("SUBTRACT", o, True)
    def __mul__(self, o): return self._op("MULTIPLY", o)
    def __rmul__(self, o): return self._op("MULTIPLY", o, True)
    def __truediv__(self, o): return self._op("DIVIDE", o)
    def __rtruediv__(self, o): return self._op("DIVIDE", o, True)
    def __neg__(self): return self * -1.0
    def __pow__(self, o): return self.g.math("POWER", self, o)

    def fract(self): return self.g.math("FRACT", self) if self.t == "f" else self.g.vmath("FRACTION", self)
    def floor(self): return self.g.math("FLOOR", self) if self.t == "f" else self.g.vmath("FLOOR", self)
    def abs(self): return self.g.math("ABSOLUTE", self) if self.t == "f" else self.g.vmath("ABSOLUTE", self)
    def sin(self): return self.g.math("SINE", self)
    def sqrt(self): return self.g.math("SQRT", self)
    def min(self, o): return self.g.math("MINIMUM", self, o)
    def max(self, o): return self.g.math("MAXIMUM", self, o)
    def clamp(self, a=0.0, b=1.0): return self.max(a).min(b)

    @property
    def x(self): return self.g.xyz(self)[0]
    @property
    def y(self): return self.g.xyz(self)[1]
    @property
    def z(self): return self.g.xyz(self)[2]

    def largo(self):
        n = self.g.n("ShaderNodeVectorMath", operation="LENGTH")
        self.g.enlazar(self, n.inputs[0])
        return S(self.g, n.outputs["Value"], "f")


class Nodos:
    def __init__(self, mat):
        self.mat = mat
        self.nt = mat.node_tree
        self._sep = {}
        self.cache = {}

    def n(self, tipo, **kw):
        nodo = self.nt.nodes.new(tipo)
        for k, v in kw.items():
            setattr(nodo, k, v)
        return nodo

    def enlazar(self, v, entrada):
        if isinstance(v, S):
            self.nt.links.new(v.s, entrada)
        elif isinstance(v, (tuple, list)):
            dv = entrada.default_value
            vals = tuple(v)
            if len(dv) == 4 and len(vals) == 3:
                vals = vals + (1.0,)
            entrada.default_value = vals
        else:
            entrada.default_value = v

    def math(self, op, a, b=None, c=None):
        n = self.n("ShaderNodeMath", operation=op)
        for i, v in enumerate((a, b, c)):
            if v is not None:
                self.enlazar(v, n.inputs[i])
        return S(self, n.outputs[0], "f")

    def vmath(self, op, a, b=None, escala=None):
        n = self.n("ShaderNodeVectorMath", operation=op)
        self.enlazar(self.vec(a), n.inputs[0])
        if b is not None:
            self.enlazar(self.vec(b), n.inputs[1])
        if escala is not None:
            self.enlazar(escala, n.inputs["Scale"])
        return S(self, n.outputs[0], "v")

    def vec(self, v):
        if isinstance(v, S) and v.t == "f":
            return self.comb(v, v, v)
        if isinstance(v, (int, float)):
            return (float(v),) * 3
        return v

    def comb(self, x, y, z):
        n = self.n("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self.enlazar(v, n.inputs[i])
        return S(self, n.outputs[0], "v")

    def xyz(self, v):
        clave = v.s.as_pointer() if isinstance(v, S) else id(v)
        if clave not in self._sep:
            n = self.n("ShaderNodeSeparateXYZ")
            self.enlazar(v, n.inputs[0])
            self._sep[clave] = tuple(S(self, n.outputs[i], "f") for i in range(3))
        return self._sep[clave]

    # ---- entradas ---------------------------------------------------------------------------------------

    def P(self):
        """Posición en studs (coordenadas del objeto: todos los objetos se hornean con el origen en 0)."""
        if "P" not in self.cache:
            self.cache["P"] = S(self, self.n("ShaderNodeTexCoord").outputs["Object"], "v")
        return self.cache["P"]

    def N(self):
        if "N" not in self.cache:
            self.cache["N"] = S(self, self.n("ShaderNodeNewGeometry").outputs["Normal"], "v")
        return self.cache["N"]

    def D(self):
        """UV del mapa «decal» (0..1 en la cara del letrero)."""
        if "D" not in self.cache:
            self.cache["D"] = S(self, self.n("ShaderNodeUVMap", uv_map="decal").outputs["UV"], "v")
        return self.cache["D"]

    def _rgb(self, hexa):
        n = self.n("ShaderNodeRGB")
        n.outputs[0].default_value = (*srgb(hexa), 1.0)
        return S(self, n.outputs[0], "v")

    # ---- funciones --------------------------------------------------------------------------------------

    def mezcla(self, a, b, t):
        """a si t = 0, b si t = 1 (escalares o colores; t se recorta a 0..1)."""
        es_v = any((isinstance(x, S) and x.t == "v") or isinstance(x, (tuple, str)) for x in (a, b))
        n = self.n("ShaderNodeMix", data_type="RGBA" if es_v else "FLOAT", clamp_factor=True)
        sufijo = "Color" if es_v else "Float"
        a = self._rgb(a) if isinstance(a, str) else a
        b = self._rgb(b) if isinstance(b, str) else b
        self.enlazar(t, next(i for i in n.inputs if i.identifier == "Factor_Float"))
        self.enlazar(a, next(i for i in n.inputs if i.identifier == f"A_{sufijo}"))
        self.enlazar(b, next(i for i in n.inputs if i.identifier == f"B_{sufijo}"))
        return S(self, next(o for o in n.outputs if o.identifier == f"Result_{sufijo}"), "v" if es_v else "f")

    def suave(self, e0, e1, x):
        """smoothstep(e0, e1, x) (vale también con e0 > e1, para invertir)."""
        n = self.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP", clamp=True)
        self.enlazar(x, n.inputs["Value"])
        self.enlazar(e0, n.inputs["From Min"])
        self.enlazar(e1, n.inputs["From Max"])
        return S(self, n.outputs["Result"], "f")

    def lineal(self, e0, e1, x):
        n = self.n("ShaderNodeMapRange", interpolation_type="LINEAR", clamp=True)
        self.enlazar(x, n.inputs["Value"])
        self.enlazar(e0, n.inputs["From Min"])
        self.enlazar(e1, n.inputs["From Max"])
        return S(self, n.outputs["Result"], "f")

    def ruido(self, v, escala=1.0, detalle=4.0, rugosidad=0.5, color=False):
        n = self.n("ShaderNodeTexNoise")
        self.enlazar(v, n.inputs["Vector"])
        self.enlazar(escala, n.inputs["Scale"])
        n.inputs["Detail"].default_value = detalle
        n.inputs["Roughness"].default_value = rugosidad
        return S(self, n.outputs["Color" if color else "Fac"], "v" if color else "f")

    def voronoi(self, v, escala=1.0, salida="Distance", aleatorio=1.0):
        n = self.n("ShaderNodeTexVoronoi")
        self.enlazar(v, n.inputs["Vector"])
        self.enlazar(escala, n.inputs["Scale"])
        n.inputs["Randomness"].default_value = aleatorio
        tipo = "f" if salida == "Distance" else "v"
        return S(self, n.outputs[salida], tipo)

    def azar(self, v):
        """Ruido blanco (0..1) de un vector (para variar el tono por panel)."""
        n = self.n("ShaderNodeTexWhiteNoise", noise_dimensions="3D")
        self.enlazar(v, n.inputs["Vector"])
        return S(self, n.outputs["Value"], "f")

    def imagen(self, ruta, uv=None, extension="CLIP", datos=False):
        """datos=True: imagen de datos (Non-Color) con el alfa como canal independiente."""
        img = bpy.data.images.load(ruta, check_existing=True)
        if datos:
            img.colorspace_settings.name = "Non-Color"
            img.alpha_mode = "CHANNEL_PACKED"
        n = self.n("ShaderNodeTexImage", image=img, extension=extension, interpolation="Cubic")
        self.enlazar(uv if uv is not None else self.D(), n.inputs["Vector"])
        return S(self, n.outputs["Color"], "v"), S(self, n.outputs["Alpha"], "f")

    def arista(self, radio=0.05):
        """1 en las aristas vivas, 0 en las caras planas (nodo Bevel de Cycles): desgaste y brillos de borde."""
        b = self.n("ShaderNodeBevel", samples=8)
        b.inputs["Radius"].default_value = radio
        nb = S(self, b.outputs["Normal"], "v")
        d = self.n("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        self.enlazar(nb, d.inputs[0])
        self.enlazar(self.N(), d.inputs[1])
        return self.lineal(0.995, 0.86, S(self, d.outputs["Value"], "f"))

    def lum(self, c):
        """Luminancia de un color (para usar una imagen como relieve)."""
        d = self.n("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        self.enlazar(c, d.inputs[0])
        d.inputs[1].default_value = (0.2126, 0.7152, 0.0722)
        return S(self, d.outputs["Value"], "f")


def srgb(hexa):
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ==============================================================================================================
# Materiales: registro y montaje
# ==============================================================================================================


class Materiales:
    """
    Registro de materiales procedurales. Cada definición es una función f(g) -> dict con:
      col (color), rug (rugosidad), met (metal), emi (color de emisión, opcional), h (relieve en studs, opcional),
      fuerza_relieve (opcional).
    Además `uv` (densidad relativa de textura en el atlas) y `especial` ('cristal' / 'neon') al registrar.
    """

    def __init__(self):
        self.defs = {}
        self.hechos = {}

    def definir(self, nombre, uv=1.0, especial=None):
        def deco(f):
            self.defs[nombre] = (f, uv, especial)
            return f
        return deco

    def uv(self, nombre):
        return self.defs[nombre][1]

    def especial(self, nombre):
        return self.defs[nombre][2]

    def __call__(self, nombre):
        if nombre in self.hechos:
            return self.hechos[nombre]
        f, _, especial = self.defs[nombre]
        mat = bpy.data.materials.new(nombre)
        mat.use_nodes = True
        g = Nodos(mat)
        d = f(g)
        for k in ("col", "emi"):
            if isinstance(d.get(k), str):
                d[k] = g._rgb(d[k])
        nt = mat.node_tree
        b = nt.nodes["Principled BSDF"]
        out = nt.nodes["Material Output"]
        if especial == "cristal":
            g.enlazar(d["col"], b.inputs["Base Color"])
            b.inputs["Roughness"].default_value = d.get("rug", 0.03)
            b.inputs["Transmission Weight"].default_value = 1.0
            b.inputs["IOR"].default_value = 1.45
            self.hechos[nombre] = mat
            return mat
        g.enlazar(d["col"], b.inputs["Base Color"])
        g.enlazar(d.get("rug", 0.5), b.inputs["Roughness"])
        g.enlazar(d.get("met", 0.0), b.inputs["Metallic"])
        emi = d.get("emi")
        if emi is not None:
            g.enlazar(emi, b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = d.get("fuerza_emi", 1.0)
        if d.get("h") is not None:
            bump = g.n("ShaderNodeBump")
            bump.inputs["Strength"].default_value = d.get("fuerza_relieve", 1.0)
            bump.inputs["Distance"].default_value = 1.0
            g.enlazar(d["h"], bump.inputs["Height"])
            nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        # Rama de horneado: un sombreador de emisión al que se conecta cada canal por turnos.
        e = g.n("ShaderNodeEmission")
        e.name = "hornear_emision"
        e.inputs["Strength"].default_value = 1.0
        canales = {
            "color": d["col"],
            "rugosidad": d.get("rug", 0.5),
            "metal": d.get("met", 0.0),
            "emision": emi if emi is not None else (0.0, 0.0, 0.0),
        }
        mat["canales"] = list(canales)
        for k, v in canales.items():
            # Un nodo «enrutador» por canal (Mix con factor 0) para poder conectarlo luego por nombre.
            r = g.n("ShaderNodeMix", data_type="RGBA")
            r.name = f"canal_{k}"
            next(i for i in r.inputs if i.identifier == "Factor_Float").default_value = 0.0
            g.enlazar(g.vec(v) if not isinstance(v, S) or v.t == "f" else v,
                      next(i for i in r.inputs if i.identifier == "A_Color"))
        mat["principled_out"] = True
        self.hechos[nombre] = mat
        return mat


def _canal_salida(mat, canal):
    n = mat.node_tree.nodes.get(f"canal_{canal}")
    return next(o for o in n.outputs if o.identifier == "Result_Color")


def conectar_horneado(mat, canal):
    """canal: 'color' | 'rugosidad' | 'metal' | 'emision' | None (vuelve al Principled)."""
    nt = mat.node_tree
    out = nt.nodes["Material Output"]
    if canal is None:
        nt.links.new(nt.nodes["Principled BSDF"].outputs[0], out.inputs["Surface"])
        return
    e = nt.nodes["hornear_emision"]
    nt.links.new(_canal_salida(mat, canal), e.inputs["Color"])
    nt.links.new(e.outputs[0], out.inputs["Surface"])


# ==============================================================================================================
# Letreros (imágenes para los decals)
# ==============================================================================================================


def fuente(tam, negrita=True, mono=False):
    nombre = ("DejaVuSansMono-Bold.ttf" if negrita else "DejaVuSansMono.ttf") if mono else \
        ("DejaVuSans-Bold.ttf" if negrita else "DejaVuSans.ttf")
    for base in ("/usr/share/fonts/truetype/dejavu/", "/usr/share/fonts/dejavu/"):
        if os.path.exists(base + nombre):
            return ImageFont.truetype(base + nombre, tam)
    return ImageFont.load_default(tam)


def texto_centrado(d, caja, texto, fnt, relleno):
    x0, y0, x1, y1 = caja
    bb = d.textbbox((0, 0), texto, font=fnt)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((x0 + x1 - w) / 2 - bb[0], (y0 + y1 - h) / 2 - bb[1]), texto, font=fnt, fill=relleno)


# ==============================================================================================================
# Atlas: UV común, horneado y material final
# ==============================================================================================================


def desplegar_atlas(objetos, mats, margen=0.0035):
    """
    UV de todas las piezas en el mismo atlas:
      1) smart project de todas a la vez (densidad uniforme),
      2) cada isla se escala por el `uv` de su material (letreros más grandes, interiores más pequeños),
      3) se empaquetan juntas.
    """
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
        if "UVMap" not in o.data.uv_layers:
            capa = o.data.uv_layers.new(name="UVMap")
        o.data.uv_layers["UVMap"].active = True
        # también activa para render: las tangentes del mapa de normales salen de esta capa, no de «decal»
        o.data.uv_layers["UVMap"].active_render = True
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(52), island_margin=margen, area_weight=0.0,
                             scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    for o in objetos:
        me = o.data
        bm = bmesh.new()
        bm.from_mesh(me)
        uv = bm.loops.layers.uv["UVMap"]
        factor = [mats.uv(m.name) for m in me.materials]
        # islas: caras unidas por aristas con la misma UV y el mismo factor
        padre = list(range(len(bm.faces)))

        def raiz(i):
            while padre[i] != i:
                padre[i] = padre[padre[i]]
                i = padre[i]
            return i

        bm.faces.ensure_lookup_table()
        for e in bm.edges:
            if len(e.link_faces) != 2:
                continue
            f1, f2 = e.link_faces
            if factor[f1.material_index] != factor[f2.material_index]:
                continue
            ok = True
            for v in e.verts:
                u1 = next(lp[uv].uv for lp in f1.loops if lp.vert == v)
                u2 = next(lp[uv].uv for lp in f2.loops if lp.vert == v)
                if (u1 - u2).length > 1e-6:
                    ok = False
            if ok:
                padre[raiz(f1.index)] = raiz(f2.index)
        grupos = {}
        for f in bm.faces:
            grupos.setdefault(raiz(f.index), []).append(f)
        for caras in grupos.values():
            k = factor[caras[0].material_index]
            if abs(k - 1.0) < 1e-6:
                continue
            pts = [lp[uv].uv.copy() for f in caras for lp in f.loops]
            cx = sum(p.x for p in pts) / len(pts)
            cy = sum(p.y for p in pts) / len(pts)
            for f in caras:
                for lp in f.loops:
                    p = lp[uv].uv
                    lp[uv].uv = (cx + (p.x - cx) * k + 10.0, cy + (p.y - cy) * k)  # +10: fuera, se separa
        bm.to_mesh(me)
        bm.free()

    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.select_all(action="SELECT")
    bpy.ops.uv.pack_islands(rotate=True, scale=True, margin_method="FRACTION", margin=margen,
                            shape_method="CONCAVE")
    bpy.ops.object.mode_set(mode="OBJECT")


def hornear_atlas(objetos, mats_usados, carpeta, nombre, tam=TAM_ATLAS, muestras=8, muestras_ao=96,
                  fuerza_ao=0.55, distancia_ao=1.6, suelo_ao=True):
    """Hornea color (con oclusión), normal, rugosidad, metal y emisión. Devuelve {canal: ruta}."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.render.bake.margin = 10
    scn.render.bake.margin_type = "EXTEND"

    def imagen(n, color):
        img = bpy.data.images.new(n, tam, tam, alpha=False, float_buffer=not color)
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return img

    def destino(img):
        for m in mats_usados:
            nt = m.node_tree
            n = nt.nodes.get("destino_horneado") or nt.nodes.new("ShaderNodeTexImage")
            n.name = "destino_horneado"
            n.image = img
            nt.nodes.active = n

    def ejecutar(tipo, **kw):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objetos:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objetos[0]
        bpy.ops.object.bake(type=tipo, margin=10, use_clear=False, **kw)

    # Solo se ven las piezas del atlas (y el suelo para la oclusión).
    estado = {o: o.hide_render for o in scn.objects}
    for o in scn.objects:
        if o.type == "MESH" and o not in objetos:
            o.hide_render = True
    suelo = None
    if suelo_ao:
        bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, -0.002))
        suelo = bpy.context.active_object
        suelo.name = "suelo_ao"
        suelo.data.materials.append(bpy.data.materials.new("suelo_ao"))

    rutas = {}
    imgs = {}
    for canal, es_color in (("color", True), ("rugosidad", False), ("metal", False), ("emision", True)):
        img = imagen(f"{nombre}_{canal}", es_color)
        destino(img)
        for m in mats_usados:
            conectar_horneado(m, canal)
        scn.cycles.samples = muestras
        ejecutar("EMIT")
        imgs[canal] = img
        print(f"[horneado] {canal}")

    for m in mats_usados:
        conectar_horneado(m, None)

    img_n = imagen(f"{nombre}_normal", False)
    destino(img_n)
    scn.cycles.samples = muestras
    ejecutar("NORMAL", normal_space="TANGENT")
    imgs["normal"] = img_n
    print("[horneado] normal")

    img_ao = imagen(f"{nombre}_ao", False)
    destino(img_ao)
    scn.cycles.samples = muestras_ao
    scn.world.light_settings.distance = distancia_ao
    ejecutar("AO")
    print("[horneado] oclusión")

    if suelo is not None:
        bpy.data.objects.remove(suelo)
    for o, h in estado.items():
        if o.name in bpy.data.objects:
            o.hide_render = h

    # color *= oclusión suave
    w = h = tam
    c = np.array(imgs["color"].pixels[:], dtype=np.float32).reshape(h, w, 4)
    a = np.array(img_ao.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :1]
    factor = 1.0 - fuerza_ao * (1.0 - np.clip(a, 0, 1)) ** 1.4
    c[..., :3] *= factor
    imgs["color"].pixels.foreach_set(c.ravel())
    imgs["color"].update()

    nombres = {"color": "color", "normal": "normal", "rugosidad": "roughness", "metal": "metalness",
               "emision": "emision"}
    for canal, img in imgs.items():
        ruta = os.path.join(carpeta, f"{nombre}_{nombres[canal]}.png")
        _guardar_png(img, ruta, color=canal in ("color", "emision"))
        img.filepath_raw = ruta
        img.file_format = "PNG"
        rutas[canal] = ruta
    return rutas


def _guardar_png(img, ruta, color):
    """Guarda con Pillow (8 bits). Las imágenes float de Blender están en lineal: se guardan tal cual (Non-Color)."""
    w, h = img.size
    p = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)[::-1, :, :3]
    if color and img.is_float:
        p = np.where(p <= 0.0031308, p * 12.92, 1.055 * np.power(np.clip(p, 0, None), 1 / 2.4) - 0.055)
    Image.fromarray((np.clip(p, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB").save(ruta, optimize=True)


def material_atlas(nombre, rutas):
    """Material final con las cinco texturas (lo que verá Roblox en la SurfaceAppearance)."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]

    def tex(canal, color):
        img = bpy.data.images.load(rutas[canal], check_existing=False)
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = img
        return n

    nt.links.new(tex("color", True).outputs["Color"], b.inputs["Base Color"])
    tr = tex("rugosidad", False)
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tr.outputs["Color"], sep.inputs[0])
    nt.links.new(sep.outputs[0], b.inputs["Roughness"])
    tm = tex("metal", False)
    sep2 = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tm.outputs["Color"], sep2.inputs[0])
    nt.links.new(sep2.outputs[0], b.inputs["Metallic"])
    tn = tex("normal", False)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.uv_map = "UVMap"
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    te = tex("emision", True)
    nt.links.new(te.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = 2.5
    return mat


# ==============================================================================================================
# Render: estudio con cielo y hoja de contactos
# ==============================================================================================================


def preparar_estudio(radio_suelo=60.0, color_suelo="#77736a", sol_altura=36, sol_azimut=-35, fuerza_cielo=0.17):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    if scn.world is None:
        scn.world = bpy.data.worlds.new("mundo")
    w = scn.world
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputWorld")
    fondo = nt.nodes.new("ShaderNodeBackground")
    cielo = nt.nodes.new("ShaderNodeTexSky")
    cielo.sky_type = "MULTIPLE_SCATTERING"
    cielo.sun_elevation = math.radians(sol_altura)
    cielo.sun_rotation = math.radians(sol_azimut)
    try:
        cielo.sun_disc = False
    except Exception:
        pass
    nt.links.new(cielo.outputs[0], fondo.inputs["Color"])
    fondo.inputs["Strength"].default_value = fuerza_cielo
    nt.links.new(fondo.outputs[0], out.inputs[0])

    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy = 4.2
    sol.angle = math.radians(2.0)
    sol.color = (1.0, 0.93, 0.84)
    o = bpy.data.objects.new("sol", sol)
    a, e = math.radians(sol_azimut), math.radians(sol_altura)
    o.rotation_euler = (math.pi / 2 - e, 0, a + math.pi)
    scn.collection.objects.link(o)
    o["estudio"] = True

    bpy.ops.mesh.primitive_circle_add(vertices=64, radius=radio_suelo, fill_type="NGON", location=(0, 0, -0.01))
    s = bpy.context.active_object
    s.name = "suelo_estudio"
    m = bpy.data.materials.new("suelo_estudio")
    m.use_nodes = True
    g = Nodos(m)
    P = g.P()
    r = g.ruido(P, 0.35, 6)
    r2 = g.ruido(P, 3.0, 4)
    col = g.mezcla(color_suelo, "#5a5850", r * 0.6 + r2 * 0.4)
    b = m.node_tree.nodes["Principled BSDF"]
    g.enlazar(col, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    s.data.materials.append(m)
    s["estudio"] = True
    return scn


def renderizar(objetos, vistas, carpeta, tam=(900, 700), muestras=96, centro=None, dist=None, lente=50,
               prefijo="", malla=False):
    """vistas: [(nombre, azimut, elevación[, distancia_relativa, centro_offset])]. Devuelve [(nombre, ruta)]."""
    scn = bpy.context.scene
    scn.cycles.samples = muestras
    scn.render.resolution_x, scn.render.resolution_y = tam
    scn.render.film_transparent = False
    os.makedirs(carpeta, exist_ok=True)
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in objetos:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    c0 = centro if centro is not None else (mn + mx) / 2
    radio = (mx - mn).length / 2
    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = lente
    cam_d.clip_end = 2000
    cam = bpy.data.objects.new("cam", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    fov = 2 * math.atan(18 / lente)
    d0 = dist or radio * 1.05 / math.sin(fov / 2) * (tam[1] / tam[0]) ** -0.0
    rutas = []
    for v in vistas:
        nombre, az, el = v[:3]
        k = v[3] if len(v) > 3 else 1.0
        c = c0 + Vector(v[4]) if len(v) > 4 else c0
        a, e = math.radians(az), math.radians(el)
        direc = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = c + direc * d0 * k
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        ruta = os.path.join(carpeta, f"{prefijo}{len(rutas):02d}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        rutas.append((nombre, ruta))
        print("[render]", nombre)
    bpy.data.objects.remove(cam)
    return rutas


def hoja(filas_cols, rutas, salida, titulo, notas=()):
    """Monta las imágenes en una rejilla con títulos."""
    cols = filas_cols
    im0 = Image.open(rutas[0][1])
    w, h = im0.size
    filas = math.ceil(len(rutas) / cols)
    cab = 70 + 22 * len(notas)
    out = Image.new("RGB", (cols * w, cab + filas * h), (16, 18, 24))
    d = ImageDraw.Draw(out)
    d.text((18, 14), titulo, fill=(255, 214, 102), font=fuente(30))
    for i, n in enumerate(notas):
        d.text((20, 56 + i * 22), n, fill=(210, 214, 224), font=fuente(17, False))
    for i, (nombre, ruta) in enumerate(rutas):
        x, y = (i % cols) * w, cab + (i // cols) * h
        out.paste(Image.open(ruta).convert("RGB"), (x, y))
        d.rectangle((x, y, x + w - 1, y + h - 1), outline=(40, 44, 56), width=2)
        d.rectangle((x + 8, y + 8, x + 16 + d.textlength(nombre, font=fuente(20)), y + 38), fill=(16, 18, 24))
        d.text((x + 12, y + 10), nombre, fill=(255, 255, 255), font=fuente(20))
    out.save(salida, optimize=True)
    print("[ok] hoja:", salida)
    return salida


# ==============================================================================================================
# Exportación
# ==============================================================================================================


def exportar_fbx(ruta, objetos):
    """
    FBX con «Apply Scalings: FBX All» y los ejes por defecto de Blender (adelante -Z, arriba Y).
    Las mallas ya llevan aplicado el GIRO_IMPORTACION. Sin escala de unidades: 1 unidad = 1 stud.
    """
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta,
        use_selection=True,
        object_types={"MESH"},
        global_scale=1.0,
        apply_unit_scale=False,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=False,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        use_custom_props=False,
        add_leaf_bones=False,
        bake_anim=False,
        embed_textures=True,
        path_mode="COPY",
    )
    print("[ok] FBX:", ruta)
