"""
Biblioteca del catálogo de modelos «Humanos vs Monstruos» (Blender sin pantalla, bpy).

Un modelo se describe con primitivas (clase G) y materiales de la paleta (paleta.py). Después `procesar`:
  1. junta todo en una malla, la despliega en UV (un atlas por modelo),
  2. hornea Base Color (+ oclusión), Normal, Roughness, Metalness y máscara de emisión a 1024 × 1024,
  3. separa las piezas (cuerpo, neon, cristal, piezas articuladas) que comparten ese atlas,
  4. renderiza el turnaround (frente, 3/4, lateral, 3/4 trasera, arriba y malla) con las texturas ya horneadas,
  5. aplica el GIRO_IMPORTACION (180° sobre la vertical) y exporta el FBX (1 unidad = 1 stud, FBX All).

Convenciones: Z arriba, suelo en z = 0, el modelo mira a -Y. Medidas en studs.
"""

import contextlib
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Euler, Matrix, Vector, noise
from PIL import Image, ImageDraw, ImageFont

from paleta import PAL

TAM_ATLAS = 1024
I4 = Matrix.Identity(4)


# ------------------------------------------------------------------------------------------------ utilidades

def lin(hexa):
    """Color '#RRGGBB' (sRGB) -> tupla lineal RGBA."""
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x / 12.92) if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4) for x in c) + (1.0,)


def trs(pos=(0, 0, 0), rot=(0, 0, 0), esc=1.0):
    if isinstance(esc, (int, float)):
        esc = (esc, esc, esc)
    r = Euler([math.radians(a) for a in rot], "XYZ").to_matrix().to_4x4()
    return Matrix.Translation(pos) @ r @ Matrix.Diagonal((*esc, 1.0))


def anillo(rx, ry, n, z=0.0, pot=2.0, c=(0.0, 0.0), giro=0.0):
    """Anillo horizontal (superelipse) de n puntos a la altura z."""
    pts = []
    for i in range(n):
        a = giro + 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        pts.append((c[0] + rx * math.copysign(abs(ca) ** (2 / pot), ca),
                    c[1] + ry * math.copysign(abs(sa) ** (2 / pot), sa), z))
    return pts


def anillo_y(y, rx, rz, n, pot=2.0, cz=0.0, cx=0.0, plano=None):
    """Anillo vertical (en el plano XZ) en la posición y: secciones de fuselajes. `plano` recorta por abajo."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ca, sa = math.cos(a), math.sin(a)
        z = cz + rz * math.copysign(abs(sa) ** (2 / pot), sa)
        if plano is not None:
            z = max(z, plano)
        pts.append((cx + rx * math.copysign(abs(ca) ** (2 / pot), ca), y, z))
    return pts


# ------------------------------------------------------------------------------------------------ geometría

class G:
    """Constructor de un modelo: primitivas con material, repartidas en piezas."""

    def __init__(self, nombre):
        self.nombre = nombre
        self.bm = bmesh.new()
        self.capa = self.bm.faces.layers.int.new("pieza")
        self.mats = []
        self.piezas = ["cuerpo"]
        self.pz = 0
        self.pila = [I4]
        self.pivotes = {}      # pieza -> (x, y, z) de su articulación
        self.padres = {}       # pieza -> pieza a la que se une
        self.anclas = {}       # puntos con nombre para Roblox (luces, efectos, acoples)
        self.separar = True    # neón y cristal a piezas aparte (False en criaturas: van en el atlas)
        self.tipos = {}        # pieza -> 'neon' | 'cristal'
        self.nombres_exactos = False
        self.extra = {}        # datos extra para el JSON (rig, especie...)

    # --- piezas y grupos
    def pieza(self, nombre, pivote=None, padre=None):
        if nombre not in self.piezas:
            self.piezas.append(nombre)
        self.pz = self.piezas.index(nombre)
        if pivote is not None:
            self.pivotes[nombre] = tuple(self.pila[-1] @ Vector(pivote))
        if padre is not None:
            self.padres[nombre] = padre

    def ancla(self, nombre, pos):
        self.anclas[nombre] = tuple(round(v, 3) for v in (self.pila[-1] @ Vector(pos)))

    @contextlib.contextmanager
    def grupo(self, pos=(0, 0, 0), rot=(0, 0, 0), esc=1.0):
        self.pila.append(self.pila[-1] @ trs(pos, rot, esc))
        try:
            yield
        finally:
            self.pila.pop()

    def _pieza_de(self, mat):
        tipo = PAL[mat].get("tipo")
        if self.separar and tipo in ("neon", "cristal"):
            pz = PAL[mat].get("pieza", tipo)
            if pz not in self.piezas:
                self.piezas.append(pz)
            self.tipos[pz] = tipo
            return self.piezas.index(pz)
        return self.pz

    def add(self, cos, caras, mat, suave=False, M=None, cerrado=True):
        if mat not in PAL:
            raise KeyError(f"material desconocido: {mat}")
        if mat not in self.mats:
            self.mats.append(mat)
        mi, pz = self.mats.index(mat), self._pieza_de(mat)
        Mt = self.pila[-1] @ M if M is not None else self.pila[-1]
        inv = Mt.determinant() < 0
        vs = [self.bm.verts.new(Mt @ Vector(c)) for c in cos]
        nuevas = []
        for c in caras:
            if len(set(c)) < 3:
                continue
            try:
                f = self.bm.faces.new([vs[i] for i in (c[::-1] if inv else c)])
            except ValueError:
                continue
            f.material_index, f.smooth, f[self.capa] = mi, suave, pz
            nuevas.append(f)
        if cerrado and nuevas:
            bmesh.ops.recalc_face_normals(self.bm, faces=nuevas)
        return vs

    # --- primitivas
    def bloque(self, mat, a, b, bisel=0.0):
        """Caja alineada con los ejes entre dos esquinas."""
        mn = [min(a[i], b[i]) for i in range(3)]
        mx = [max(a[i], b[i]) for i in range(3)]
        return self.caja(mat, [mx[i] - mn[i] for i in range(3)], [(mx[i] + mn[i]) / 2 for i in range(3)], bisel=bisel)

    def caja(self, mat, tam, pos=(0, 0, 0), rot=(0, 0, 0), sup=(1, 1), base=False, bisel=0.0, desv=(0, 0)):
        """Caja centrada en pos (o apoyada en pos si base=True). `sup` estrecha la cara de arriba; `desv` la desplaza."""
        x, y, z = tam[0] / 2, tam[1] / 2, tam[2] / 2
        cos = [(-x, -y, -z), (x, -y, -z), (x, y, -z), (-x, y, -z),
               (-x * sup[0] + desv[0], -y * sup[1] + desv[1], z), (x * sup[0] + desv[0], -y * sup[1] + desv[1], z),
               (x * sup[0] + desv[0], y * sup[1] + desv[1], z), (-x * sup[0] + desv[0], y * sup[1] + desv[1], z)]
        if base:
            cos = [(a, b, c + z) for a, b, c in cos]
        caras = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        vs = self.add(cos, caras, mat, M=trs(pos, rot))
        if bisel > 0:
            aristas = list({e for v in vs for e in v.link_edges})
            mi, pz = self.mats.index(mat), self._pieza_de(mat)
            r = bmesh.ops.bevel(self.bm, geom=aristas, offset=bisel, segments=1, affect="EDGES", profile=0.5)
            for f in r["faces"]:
                f.material_index, f[self.capa], f.smooth = mi, pz, False
        return vs

    def loft(self, mat, anillos, suave=True, tapas=(True, True), ciclo=False, M=None):
        """Une anillos consecutivos (listas de puntos; un solo punto = punta)."""
        cos, ini = [], []
        for a in anillos:
            ini.append(len(cos))
            cos.extend(a)
        caras = []
        pares = list(zip(range(len(anillos) - 1), range(1, len(anillos))))
        if ciclo:
            pares.append((len(anillos) - 1, 0))
        for k0, k1 in pares:
            a, b = anillos[k0], anillos[k1]
            na, nb = len(a), len(b)
            if na == 1 and nb == 1:
                continue
            n = max(na, nb)
            for j in range(n):
                j2 = (j + 1) % n
                if na == 1:
                    caras.append((ini[k0], ini[k1] + j2, ini[k1] + j))
                elif nb == 1:
                    caras.append((ini[k0] + j, ini[k0] + j2, ini[k1]))
                else:
                    caras.append((ini[k0] + j, ini[k0] + j2, ini[k1] + j2, ini[k1] + j))
        cerrado = ciclo
        if not ciclo:
            c0 = tapas[0] or len(anillos[0]) == 1
            c1 = tapas[1] or len(anillos[-1]) == 1
            if tapas[0] and len(anillos[0]) > 2:
                caras.append(tuple(range(ini[0] + len(anillos[0]) - 1, ini[0] - 1, -1)))
            if tapas[1] and len(anillos[-1]) > 2:
                caras.append(tuple(range(ini[-1], ini[-1] + len(anillos[-1]))))
            cerrado = c0 and c1
        return self.add(cos, caras, mat, suave=suave, M=M, cerrado=cerrado)

    def rev(self, mat, perfil, pos=(0, 0, 0), rot=(0, 0, 0), esc=1.0, lados=12, suave=True, tapas=(True, True)):
        """Sólido de revolución sobre Z a partir de un perfil [(radio, z), ...] de abajo arriba."""
        ans = []
        for r, z in perfil:
            if r <= 1e-6:
                ans.append([(0, 0, z)])
            else:
                ans.append([(r * math.cos(2 * math.pi * j / lados), r * math.sin(2 * math.pi * j / lados), z)
                            for j in range(lados)])
        return self.loft(mat, ans, suave=suave, tapas=tapas, M=trs(pos, rot, esc))

    def cil(self, mat, r, h, pos=(0, 0, 0), rot=(0, 0, 0), lados=12, r2=None, suave=True, bisel=0.0, tapas=(True, True),
            esc=1.0):
        """Cilindro o cono truncado apoyado en pos, eje +Z local."""
        r2 = r if r2 is None else r2
        if bisel > 0:
            perfil = [(max(r - bisel, 0), 0), (r, bisel), (r2, h - bisel), (max(r2 - bisel, 0), h)]
        else:
            perfil = [(r, 0), (r2, h)]
        return self.rev(mat, perfil, pos, rot, esc, lados, suave, tapas)

    def esfera(self, mat, r, pos=(0, 0, 0), esc=1.0, rot=(0, 0, 0), lados=12, anillos=6, semi=False, suave=True):
        f0 = math.pi / 2 if semi else 0.0
        perfil = []
        for i in range(anillos + 1):
            f = f0 + (math.pi - f0) * i / anillos
            perfil.append((r * math.sin(f) if 0 < i < anillos or (semi and i == 0) else 0.0, -r * math.cos(f)))
        return self.rev(mat, perfil, pos, rot, esc, lados, suave)

    def tubo(self, mat, pts, radios, lados=8, suave=True, tapas=(True, True), pot=2.0, aplastar=1.0):
        """Tubo a lo largo de una polilínea con un radio por punto (radio 0 = punta)."""
        pts = [Vector(p) for p in pts]
        if isinstance(radios, (int, float)):
            radios = [radios] * len(pts)
        tans = []
        for i in range(len(pts)):
            a = pts[max(i - 1, 0)]
            b = pts[min(i + 1, len(pts) - 1)]
            tans.append((b - a).normalized())
        n = tans[0].orthogonal().normalized()
        ans = []
        for i, (p, t, r) in enumerate(zip(pts, tans, radios)):
            n = (n - t * n.dot(t))
            n = n.normalized() if n.length > 1e-6 else t.orthogonal().normalized()
            b = t.cross(n)
            if r <= 1e-6:
                ans.append([tuple(p)])
            else:
                ring = []
                for j in range(lados):
                    a = 2 * math.pi * j / lados
                    ca, sa = math.cos(a), math.sin(a)
                    ca = math.copysign(abs(ca) ** (2 / pot), ca)
                    sa = math.copysign(abs(sa) ** (2 / pot), sa) * aplastar
                    ring.append(tuple(p + r * (ca * n + sa * b)))
                ans.append(ring)
        return self.loft(mat, ans, suave=suave, tapas=tapas)

    def prisma(self, mat, perfil, grosor, pos=(0, 0, 0), rot=(0, 0, 0), plano="xy", esc=1.0, sup=1.0):
        """Extruye un polígono 2D (cualquier sentido) un grosor centrado. plano: 'xy' (extruye Z), 'xz' (Y), 'yz' (X).
        `sup` < 1 encoge la cara del lado positivo (cuñas, hojas afiladas)."""
        g = grosor / 2
        cx = sum(p[0] for p in perfil) / len(perfil)
        cy = sum(p[1] for p in perfil) / len(perfil)

        def pt(a, b, w, k=1.0):
            a, b = cx + (a - cx) * k, cy + (b - cy) * k
            return {"xy": (a, b, w), "xz": (a, w, b), "yz": (w, a, b)}[plano]

        a0 = [pt(a, b, -g) for a, b in perfil]
        a1 = [pt(a, b, g, sup) for a, b in perfil]
        return self.loft(mat, [a0, a1], suave=False, M=trs(pos, rot, esc))

    def cristal(self, mat, r, h, pos=(0, 0, 0), rot=(0, 0, 0), lados=6, punta=0.3, base=0.7, esc=1.0):
        """Prisma de cristal facetado con punta."""
        return self.rev(mat, [(r * base, 0), (r, h * (1 - punta)), (0, h)], pos, rot, esc, lados, suave=False)

    def toro(self, mat, R, r, pos=(0, 0, 0), rot=(0, 0, 0), seg=16, lados=8, arco=360.0, suave=True, esc=1.0, pot=2.0):
        """Toro en el plano XY local. Con arco < 360 queda abierto y tapado."""
        completo = arco >= 359.9
        n = seg if completo else seg + 1
        ans = []
        for i in range(n):
            a = math.radians(arco) * i / seg
            ca, sa = math.cos(a), math.sin(a)
            ring = []
            for j in range(lados):
                b = 2 * math.pi * j / lados
                cb, sb = math.cos(b), math.sin(b)
                cb = math.copysign(abs(cb) ** (2 / pot), cb)
                sb = math.copysign(abs(sb) ** (2 / pot), sb)
                ring.append(((R + r * cb) * ca, (R + r * cb) * sa, r * sb))
            ans.append(ring)
        return self.loft(mat, ans, suave=suave, ciclo=completo, M=trs(pos, rot, esc))

    def roca(self, mat, r, pos=(0, 0, 0), esc=1.0, rot=(0, 0, 0), semilla=0, sub=2, amp=0.28, frec=0.9, plano=None,
             suave=False):
        """Roca: icosfera deformada con ruido. `plano` aplana la base a esa altura local (antes de escalar)."""
        tmp = bmesh.new()
        bmesh.ops.create_icosphere(tmp, subdivisions=sub, radius=1.0)
        tmp.verts.ensure_lookup_table()
        off = Vector((semilla * 7.31, semilla * 3.17, semilla * 5.71))
        cos = []
        for v in tmp.verts:
            d = v.co.normalized()
            k = 1 + amp * (noise.noise(d * frec + off) * 1.4 + 0.5 * noise.noise(d * frec * 2.3 + off))
            p = d * r * k
            if plano is not None and p.z < plano:
                p.z = plano
            cos.append(tuple(p))
        caras = [tuple(v.index for v in f.verts) for f in tmp.faces]
        tmp.free()
        return self.add(cos, caras, mat, suave=suave, M=trs(pos, rot, esc))

    def ruido(self, verts, amp, frec=0.5, semilla=0):
        """Desplaza vértices con ruido (para formas orgánicas)."""
        off = Vector((semilla * 3.3, semilla * 1.7, semilla * 9.1))
        for v in verts:
            v.co += noise.noise_vector(v.co * frec + off) * amp

    def triangulos(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)


# ------------------------------------------------------------------------------------------------ materiales

class Nodos:
    def __init__(self, nt):
        self.nt, self.n, self.l = nt, nt.nodes, nt.links

    def poner(self, entrada, x):
        if isinstance(x, bpy.types.NodeSocket):
            self.l.new(x, entrada)
        elif isinstance(x, (tuple, list)) and len(x) == 3 and entrada.type == "RGBA":
            entrada.default_value = (*x, 1.0)
        else:
            entrada.default_value = x

    def nodo(self, tipo, **props):
        n = self.n.new(tipo)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def m(self, op, a, b=0.0, c=0.0):
        n = self.nodo("ShaderNodeMath", operation=op)
        for i, x in enumerate((a, b, c)):
            self.poner(n.inputs[i], x)
        return n.outputs[0]

    def ruido(self, P, esc, det=2.0, color=False):
        n = self.nodo("ShaderNodeTexNoise")
        self.poner(n.inputs["Vector"], P)
        n.inputs["Scale"].default_value = esc
        n.inputs["Detail"].default_value = det
        return n.outputs[1 if color else 0]

    def voronoi(self, P, esc, borde=True):
        n = self.nodo("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE" if borde else "F1")
        self.poner(n.inputs["Vector"], P)
        n.inputs["Scale"].default_value = esc
        return n.outputs["Distance"]

    def rampa(self, x, a, b):
        n = self.nodo("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
        self.poner(n.inputs[0], x)
        n.inputs[1].default_value, n.inputs[2].default_value = a, b
        return n.outputs[0]

    def mezcla(self, f, a, b):
        n = self.nodo("ShaderNodeMix", data_type="RGBA")
        self.poner(n.inputs[0], f)
        self.poner(n.inputs[6], a)
        self.poner(n.inputs[7], b)
        return n.outputs[2]

    def escalar(self, P, vec):
        n = self.nodo("ShaderNodeMapping")
        self.poner(n.inputs["Vector"], P)
        n.inputs["Scale"].default_value = vec
        return n.outputs[0]

    def sep(self, P):
        n = self.nodo("ShaderNodeSeparateXYZ")
        self.poner(n.inputs[0], P)
        return n.outputs

    def vmat(self, op, a, b):
        n = self.nodo("ShaderNodeVectorMath", operation=op)
        self.poner(n.inputs[0], a)
        self.poner(n.inputs[1], b)
        return n.outputs[0]

    def distorsion(self, P, esc, fuerza):
        """P desplazado por ruido (para que vetas y grietas no salgan rectas)."""
        c = self.ruido(P, esc, 2.0, color=True)
        d = self.vmat("SUBTRACT", c, (0.5, 0.5, 0.5))
        d = self.vmat("SCALE", d, (0, 0, 0))
        d.node.inputs[3].default_value = fuerza
        return self.vmat("ADD", P, d)

    def maximo(self, xs):
        r = xs[0]
        for x in xs[1:]:
            r = self.m("MAXIMUM", r, x)
        return r


def _lineas(k, comp, normal, eje, frec, ancho):
    """Líneas de junta perpendiculares a un eje, cada 1/frec studs, sin pintar las caras que miran a ese eje."""
    t = k.m("FRACT", k.m("MULTIPLY_ADD", comp[eje], frec, 0.37))
    d = k.m("ABSOLUTE", k.m("SUBTRACT", t, 0.5))
    linea = k.m("GREATER_THAN", d, 0.5 - ancho * frec / 2)
    de_lado = k.m("LESS_THAN", k.m("ABSOLUTE", normal[eje]), 0.7)
    return k.m("MULTIPLY", linea, de_lado)


def _patron(k, P, d):
    """Devuelve dict con f (mezcla color->color2), osc (oscurecer), h (relieve), emis (máscara), lit (ventanas)."""
    p = d.get("patron")
    esc = d.get("esc", 1.0)
    comp = k.sep(P)
    normal = k.sep(k.nodo("ShaderNodeNewGeometry").outputs["Normal"])
    r = {"f": 0.0, "osc": 0.0, "h": k.ruido(P, 6.0 * esc, 2.0), "emis": 1.0}
    if p is None:
        return r
    if p == "ruido":
        r["f"] = k.rampa(k.ruido(P, esc, 3.0), 0.4, 0.65)
        r["h"] = r["f"]
        if d.get("emis_f"):
            r["emis"] = r["f"]
    elif p == "madera":
        v = [3.0, 3.0, 3.0]
        v[d.get("eje", 2)] = 0.25
        veta = k.ruido(k.escalar(P, v), 1.6 * esc, 3.0)
        r["f"] = k.rampa(veta, 0.35, 0.7)
        r["h"] = veta
        if d.get("tablas"):
            eje, ancho = d["tablas"]
            junta = _lineas(k, comp, normal, eje, 1.0 / ancho, 0.07)
            r["osc"] = junta
            r["h"] = k.m("SUBTRACT", k.m("MULTIPLY", veta, 0.5), junta)
    elif p == "paneles":
        js = [_lineas(k, comp, normal, e, f, d.get("junta", 0.06)) for e, f in enumerate(d["rejilla"]) if f > 0]
        junta = k.maximo(js)
        r["osc"] = junta
        r["h"] = k.m("SUBTRACT", k.m("MULTIPLY", r["h"], 0.15), junta)
    elif p == "rayas":
        t = k.m("FRACT", k.m("MULTIPLY_ADD", comp[d.get("eje", 0)], 0.5 / d.get("ancho", 1.0), d.get("fase", 0.0)))
        r["f"] = k.m("GREATER_THAN", t, 0.5)
    elif p == "ventanas":
        piso, ancho = d.get("piso", 4.0), d.get("ancho", 3.0)
        v0, v1 = d.get("vert", (0.25, 0.8))
        h0, h1 = d.get("horiz", (0.15, 0.85))
        cz = k.m("DIVIDE", k.m("SUBTRACT", comp[2], d.get("z0", 0.0)), piso)
        cu = k.m("MULTIPLY_ADD", k.m("ADD", comp[0], comp[1]), 1.0 / ancho, d.get("fase", 0.5))
        tz, tu = k.m("FRACT", cz), k.m("FRACT", cu)
        dentro = k.m("MULTIPLY", k.m("MULTIPLY", k.m("GREATER_THAN", tz, v0), k.m("LESS_THAN", tz, v1)),
                     k.m("MULTIPLY", k.m("GREATER_THAN", tu, h0), k.m("LESS_THAN", tu, h1)))
        pared = k.m("LESS_THAN", k.m("ABSOLUTE", normal[2]), 0.5)
        rango = k.m("MULTIPLY", k.m("GREATER_THAN", comp[2], d.get("z0", 0.0)),
                    k.m("LESS_THAN", comp[2], d.get("z1", 1e6)))
        r["f"] = k.m("MULTIPLY", dentro, k.m("MULTIPLY", pared, rango))
        celda = k.nodo("ShaderNodeCombineXYZ")
        k.poner(celda.inputs[0], k.m("FLOOR", cu))
        k.poner(celda.inputs[1], k.m("FLOOR", cz))
        az = k.nodo("ShaderNodeTexWhiteNoise", noise_dimensions="3D")
        k.poner(az.inputs["Vector"], celda.outputs[0])
        r["lit"] = k.m("GREATER_THAN", az.outputs["Value"], 1.0 - d.get("encendidas", 0.35))
        r["emis"] = k.m("MULTIPLY", r["f"], r["lit"])
        r["h"] = k.m("MULTIPLY", r["f"], -1.0)
    elif p == "piedra":
        n = k.ruido(P, esc, 3.0)
        grieta = k.m("SUBTRACT", 1.0, k.rampa(k.voronoi(k.distorsion(P, esc * 1.5, 0.5), esc * 0.55), 0.0,
                                               d.get("grieta", 0.05)))
        r["f"] = k.rampa(n, 0.35, 0.7)
        r["osc"] = k.m("MULTIPLY", grieta, d.get("grieta_osc", 0.8))
        r["h"] = k.m("SUBTRACT", k.m("MULTIPLY", n, 0.6), grieta)
    elif p == "musgo":
        n = k.ruido(P, esc, 3.0)
        u = d.get("umbral", 0.55)
        r["f"] = k.rampa(k.m("ADD", normal[2], k.m("MULTIPLY", k.m("SUBTRACT", n, 0.5), 1.4)), u - 0.12, u + 0.12)
        r["osc"] = k.m("MULTIPLY", k.rampa(k.ruido(P, esc * 2.5, 2.0), 0.55, 0.8), 0.5)
        r["h"] = k.ruido(P, esc * 2.0, 3.0)
    elif p == "vetas":
        dist = k.voronoi(k.distorsion(P, esc * 1.3, d.get("torcer", 0.7)), esc)
        veta = k.m("SUBTRACT", 1.0, k.rampa(dist, 0.0, d.get("grosor", 0.06)))
        r["f"] = veta
        r["emis"] = veta
        r["h"] = k.m("SUBTRACT", k.m("MULTIPLY", r["h"], 0.3), veta)
    elif p == "escamas":
        dist = k.voronoi(P, esc, borde=False)
        r["osc"] = k.m("MULTIPLY", k.rampa(dist, 0.3, 0.6), d.get("borde", 0.7))
        r["h"] = k.m("SUBTRACT", 1.0, dist)
        r["f"] = k.rampa(k.ruido(P, esc * 0.35, 2.0), 0.4, 0.62)
    elif p == "degradado":
        r["f"] = k.rampa(comp[d.get("eje", 2)], d.get("z0", 0.0), d.get("z1", 1.0))
        if d.get("emis_inv"):
            r["emis"] = k.m("SUBTRACT", 1.0, r["f"])
        else:
            r["emis"] = r["f"]
    else:
        raise ValueError(f"patrón desconocido: {p}")
    return r


def crear_material(nombre):
    """Material Principled procedural (coordenadas de objeto = studs). Guarda las salidas S_* para hornear."""
    d = PAL[nombre]
    mat = bpy.data.materials.new(nombre)
    nt = mat.node_tree
    if nt is None:
        mat.use_nodes = True
        nt = mat.node_tree
    nt.nodes.clear()
    k = Nodos(nt)
    P = k.nodo("ShaderNodeTexCoord").outputs["Object"]
    r = _patron(k, P, d)
    c1 = lin(d["color"])
    c2 = lin(d.get("color2", d["color"]))
    color = k.mezcla(r["f"], c1, c2) if not isinstance(r["f"], float) else c1
    if "lit" in r:
        color = k.mezcla(r["f"], c1, k.mezcla(r["lit"], c2, lin(d.get("color3", "#FFFFFF"))))
    if not isinstance(r["osc"], float):
        color = k.mezcla(r["osc"], color, k.mezcla(d.get("osc", 0.6), color, (0.0, 0.0, 0.0, 1.0)))
    var = d.get("var", 0.10)
    if var > 0:
        mancha = k.m("MULTIPLY", k.rampa(k.ruido(P, d.get("var_esc", 0.45), 2.0), 0.35, 0.7), var * 2)
        color = k.mezcla(mancha, color, (0.0, 0.0, 0.0, 1.0))
    s_color = k.nodo("ShaderNodeMix", data_type="RGBA", name="S_color")
    s_color.inputs[0].default_value = 0.0
    k.poner(s_color.inputs[6], color)

    def escalar(nom, v1, v2=None):
        if v2 is None or isinstance(r["f"], float):
            x = v1
        else:
            x = k.m("MULTIPLY_ADD", r["f"], v2 - v1, v1)
        n = k.nodo("ShaderNodeMath", operation="ADD", name=nom)
        k.poner(n.inputs[0], x)
        n.inputs[1].default_value = 0.0
        return n

    s_rug = escalar("S_rug", d.get("rug", 0.6), d.get("rug2"))
    s_metal = escalar("S_metal", d.get("metal", 0.0), d.get("metal2"))
    em = d.get("emision", 0.0)
    s_emis = k.nodo("ShaderNodeMath", operation="MULTIPLY", name="S_emis")
    k.poner(s_emis.inputs[0], r["emis"] if em > 0 else 0.0)
    s_emis.inputs[1].default_value = 1.0 if em > 0 else 0.0

    bsdf = k.nodo("ShaderNodeBsdfPrincipled", name="BSDF")
    k.l.new(s_color.outputs[2], bsdf.inputs["Base Color"])
    k.l.new(s_rug.outputs[0], bsdf.inputs["Roughness"])
    k.l.new(s_metal.outputs[0], bsdf.inputs["Metallic"])
    rel = d.get("relieve", 0.25)
    if rel > 0:
        bump = k.nodo("ShaderNodeBump")
        bump.inputs["Strength"].default_value = rel
        bump.inputs["Distance"].default_value = d.get("relieve_dist", 0.08)
        k.poner(bump.inputs["Height"], r["h"])
        k.l.new(bump.outputs[0], bsdf.inputs["Normal"])
    k.nodo("ShaderNodeEmission", name="E_horno")
    k.nodo("ShaderNodeOutputMaterial", name="SALIDA")
    k.l.new(bsdf.outputs[0], nt.nodes["SALIDA"].inputs[0])
    return mat


# ------------------------------------------------------------------------------------------------ horneado

def _cycles(muestras):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = muestras
    scn.cycles.use_denoising = False
    scn.cycles.use_adaptive_sampling = False


def _imagen(nombre, tam, color):
    img = bpy.data.images.new(nombre, tam, tam, alpha=False)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    return img


def _pix(img):
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)[::-1]


def hornear(obj, carpeta, nombre, tam=TAM_ATLAS, muestras_ao=24, ao=0.55):
    """Hornea el atlas del modelo. Devuelve {mapa: ruta}."""
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    scn = bpy.context.scene
    hb = scn.render.bake
    hb.margin = max(4, tam // 128)
    hb.use_selected_to_active = False
    hb.use_clear = True
    mats = [s.material for s in obj.material_slots]

    def destino(img):
        for m in mats:
            n = m.node_tree.nodes.get("DESTINO") or m.node_tree.nodes.new("ShaderNodeTexImage")
            n.name = "DESTINO"
            n.image = img
            for x in m.node_tree.nodes:
                x.select = False
            n.select = True
            m.node_tree.nodes.active = n

    def conectar(fuente):
        for m in mats:
            nt = m.node_tree
            sal = nt.nodes["SALIDA"].inputs[0]
            for l in list(sal.links):
                nt.links.remove(l)
            if fuente is None:
                nt.links.new(nt.nodes["BSDF"].outputs[0], sal)
            else:
                e = nt.nodes["E_horno"]
                for l in list(e.inputs[0].links):
                    nt.links.remove(l)
                s = nt.nodes[fuente]
                nt.links.new(s.outputs[2] if fuente == "S_color" else s.outputs[0], e.inputs[0])
                nt.links.new(e.outputs[0], sal)

    res = {}
    _cycles(1)
    for mapa, fuente in (("color", "S_color"), ("roughness", "S_rug"), ("metalness", "S_metal"), ("emision", "S_emis")):
        img = _imagen(f"{nombre}_{mapa}", tam, mapa == "color")
        destino(img)
        conectar(fuente)
        bpy.ops.object.bake(type="EMIT")
        res[mapa] = _pix(img)
        bpy.data.images.remove(img)
    conectar(None)
    img = _imagen(f"{nombre}_normal", tam, False)
    destino(img)
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
    res["normal"] = _pix(img)
    bpy.data.images.remove(img)
    if ao > 0:
        _cycles(muestras_ao)
        img = _imagen(f"{nombre}_ao", tam, False)
        destino(img)
        bpy.ops.object.bake(type="AO")
        oc = _pix(img)[..., :1]
        bpy.data.images.remove(img)
        em = res["emision"][..., :1]
        res["color"][..., :3] *= 1.0 - ao * (1.0 - oc) * (1.0 - np.clip(em, 0, 1))

    rutas = {}
    for mapa, a in res.items():
        if mapa == "emision" and a[..., 0].max() < 0.02:
            continue
        b = (np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8)
        im = Image.fromarray(b[..., :3], "RGB") if mapa in ("color", "normal") else Image.fromarray(b[..., 0], "L")
        ruta = os.path.join(carpeta, f"{nombre}_{mapa}.png")
        im.save(ruta, optimize=True)
        rutas[mapa] = ruta
    return rutas


def material_final(nombre, rutas, tipo=None):
    """Material con las texturas horneadas: el que se exporta y el que se ve en el turnaround."""
    mat = bpy.data.materials.new(nombre)
    nt = mat.node_tree
    if nt is None:
        mat.use_nodes = True
        nt = mat.node_tree
    nt.nodes.clear()
    k = Nodos(nt)
    bsdf = k.nodo("ShaderNodeBsdfPrincipled")
    sal = k.nodo("ShaderNodeOutputMaterial")
    k.l.new(bsdf.outputs[0], sal.inputs[0])

    def tex(mapa, color=False):
        n = k.nodo("ShaderNodeTexImage")
        n.image = bpy.data.images.load(rutas[mapa], check_existing=True)
        n.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return n

    tc = tex("color", True)
    k.l.new(tc.outputs[0], bsdf.inputs["Base Color"])
    k.l.new(tex("roughness").outputs[0], bsdf.inputs["Roughness"])
    k.l.new(tex("metalness").outputs[0], bsdf.inputs["Metallic"])
    nm = k.nodo("ShaderNodeNormalMap")
    k.l.new(tex("normal").outputs[0], nm.inputs["Color"])
    k.l.new(nm.outputs[0], bsdf.inputs["Normal"])
    if "emision" in rutas:
        k.l.new(tc.outputs[0], bsdf.inputs["Emission Color"])
        fuerza = k.m("MULTIPLY", tex("emision").outputs[0], {"neon": 4.0, "cristal": 1.3}.get(tipo, 2.5))
        k.l.new(fuerza, bsdf.inputs["Emission Strength"])
    if tipo == "cristal":
        bsdf.inputs["Alpha"].default_value = 0.55
    return mat


# ------------------------------------------------------------------------------------------------ render

VISTAS = (("Frente", 0, 8), ("3/4", 38, 22), ("Lateral", 90, 8), ("3/4 trasera", 142, 22), ("Arriba", 0, 89.5),
          ("Malla", 38, 22))


def _fuente(tam):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(ruta, tam) if os.path.exists(ruta) else ImageFont.load_default(tam)


def _mat_malla():
    mat = bpy.data.materials.new("malla")
    nt = mat.node_tree
    if nt is None:
        mat.use_nodes = True
        nt = mat.node_tree
    nt.nodes.clear()
    k = Nodos(nt)
    w = k.nodo("ShaderNodeWireframe", use_pixel_size=True)
    w.inputs[0].default_value = 1.7
    base = k.nodo("ShaderNodeBsdfDiffuse")
    base.inputs[0].default_value = (0.62, 0.66, 0.72, 1)
    linea = k.nodo("ShaderNodeEmission")
    linea.inputs[0].default_value = (0.01, 0.02, 0.05, 1)
    mz = k.nodo("ShaderNodeMixShader")
    k.l.new(w.outputs[0], mz.inputs[0])
    k.l.new(base.outputs[0], mz.inputs[1])
    k.l.new(linea.outputs[0], mz.inputs[2])
    k.l.new(mz.outputs[0], k.nodo("ShaderNodeOutputMaterial").inputs[0])
    return mat


def renderizar(objs, carpeta_tmp, nombre, tam=420, muestras=32):
    """Renderiza las 6 vistas y devuelve las rutas de las imágenes."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = muestras
    scn.cycles.use_denoising = True
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.max_bounces = 4
    scn.render.resolution_x = scn.render.resolution_y = tam
    scn.render.resolution_percentage = 100
    scn.render.film_transparent = False
    scn.view_settings.view_transform = "Standard"
    scn.render.image_settings.file_format = "PNG"
    mundo = bpy.data.worlds.new("mundo")
    scn.world = mundo
    nt = mundo.node_tree
    if nt is None:
        mundo.use_nodes = True
        nt = mundo.node_tree
    fondo = nt.nodes.get("Background") or nt.nodes.new("ShaderNodeBackground")
    if not fondo.outputs[0].links:
        sal = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
        nt.links.new(fondo.outputs[0], sal.inputs[0])
    fondo.inputs[0].default_value = (0.20, 0.22, 0.26, 1)
    fondo.inputs[1].default_value = 1.0

    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    centro = (mn + mx) / 2
    radio = max((mx - mn).length / 2, 0.05)

    suelo_m = bpy.data.materials.new("suelo")
    nts = suelo_m.node_tree
    if nts is None:
        suelo_m.use_nodes = True
        nts = suelo_m.node_tree
    b = nts.nodes.get("Principled BSDF")
    if b is None:
        nts.nodes.clear()
        b = nts.nodes.new("ShaderNodeBsdfPrincipled")
        nts.links.new(b.outputs[0], nts.nodes.new("ShaderNodeOutputMaterial").inputs[0])
    b.inputs["Base Color"].default_value = (0.20, 0.22, 0.26, 1)
    b.inputs["Roughness"].default_value = 0.9
    bpy.ops.mesh.primitive_plane_add(size=radio * 400, location=(centro.x, centro.y, mn.z - radio * 0.002))
    suelo = bpy.context.object
    suelo.data.materials.append(suelo_m)

    cam_d = bpy.data.cameras.new("cam")
    cam_d.lens = 85
    cam_d.clip_start, cam_d.clip_end = radio * 0.05, radio * 100
    cam = bpy.data.objects.new("cam", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    sol_d = bpy.data.lights.new("sol", "SUN")
    sol_d.energy, sol_d.angle = 3.2, math.radians(12)
    sol = bpy.data.objects.new("sol", sol_d)
    scn.collection.objects.link(sol)
    rel_d = bpy.data.lights.new("relleno", "SUN")
    rel_d.energy, rel_d.angle, rel_d.color = 1.1, math.radians(40), (0.8, 0.88, 1.0)
    rel = bpy.data.objects.new("relleno", rel_d)
    scn.collection.objects.link(rel)

    def direccion(az, el):
        a, e = math.radians(az), math.radians(el)
        return Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))

    def mirar(o, d):
        o.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()

    dist = radio / math.sin(math.atan(18 / 85)) * 1.04
    malla = _mat_malla()
    rutas = []
    originales = {o.name: [s.material for s in o.material_slots] for o in objs}
    for i, (titulo, az, el) in enumerate(VISTAS):
        d = direccion(az, el)
        cam.location = centro + d * dist
        mirar(cam, d)
        mirar(sol, direccion(az - 40, 48))
        mirar(rel, direccion(az + 70, 25))
        if titulo == "Malla":
            for o in objs:
                for s in o.material_slots:
                    s.material = malla
        ruta = os.path.join(carpeta_tmp, f"{nombre}_{i}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        rutas.append(ruta)
    for o in objs:
        for s, m in zip(o.material_slots, originales[o.name]):
            s.material = m
    for o in (suelo, cam, sol, rel):
        bpy.data.objects.remove(o, do_unlink=True)
    return rutas


def hoja_turnaround(rutas, salida, titulo, subtitulo):
    ims = [Image.open(r).convert("RGB") for r in rutas]
    t = ims[0].size[0]
    cab = 58
    hoja = Image.new("RGB", (t * 3 + 8, t * 2 + cab + 8), (22, 24, 30))
    dr = ImageDraw.Draw(hoja)
    dr.text((10, 6), titulo, font=_fuente(24), fill=(255, 255, 255))
    dr.text((10, 36), subtitulo, font=_fuente(13), fill=(170, 190, 210))
    for i, (im, (nom, _, _)) in enumerate(zip(ims, VISTAS)):
        x, y = 2 + (i % 3) * (t + 2), cab + (i // 3) * (t + 2)
        hoja.paste(im, (x, y))
        dr.text((x + 8, y + 6), nom, font=_fuente(15), fill=(255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0))
    hoja.save(salida, optimize=True)
    return ims[1]


# ------------------------------------------------------------------------------------------------ exportación

def exportar_fbx(ruta, objs):
    """FBX para Roblox: 1 unidad = 1 stud (FBX All con escala 0,01: los números del archivo son studs), arriba Y."""
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH", "ARMATURE", "EMPTY"},
        global_scale=0.01, apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z", axis_up="Y", bake_space_transform=True,
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True, use_triangles=True,
        add_leaf_bones=False, bake_anim=False, embed_textures=False, path_mode="STRIP")


def procesar(g, carpeta, limite=5000, rapido=False, tmp="/tmp", ao=0.55, uv_margen=0.004):
    """Del constructor G a los archivos del modelo. Devuelve (info, imagen 3/4)."""
    nombre = g.nombre
    os.makedirs(carpeta, exist_ok=True)
    bm = g.bm
    # Aristas vivas: entre caras suaves que forman más de 40°.
    for e in bm.edges:
        if len(e.link_faces) == 2 and e.calc_face_angle(0.0) > math.radians(40):
            e.smooth = False
    tris = g.triangulos()
    me = bpy.data.meshes.new("_union")
    bm.to_mesh(me)
    obj = bpy.data.objects.new("_union", me)
    bpy.context.scene.collection.objects.link(obj)
    for m in g.mats:
        me.materials.append(crear_material(m))
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=uv_margen, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    tam = 256 if rapido else TAM_ATLAS
    rutas = hornear(obj, carpeta, nombre, tam=tam, muestras_ao=6 if rapido else 24, ao=ao)

    # Separar piezas (comparten atlas).
    bm2 = bmesh.new()
    bm2.from_mesh(me)
    capa = bm2.faces.layers.int["pieza"]
    usadas = sorted({f[capa] for f in bm2.faces})
    bm2.free()
    objs, info_piezas = [], {}
    for pi in usadas:
        pz = g.piezas[pi]
        b = bmesh.new()
        b.from_mesh(me)
        c = b.faces.layers.int["pieza"]
        bmesh.ops.delete(b, geom=[f for f in b.faces if f[c] != pi], context="FACES")
        pivote = Vector(g.pivotes.get(pz, (0, 0, 0)))
        bmesh.ops.translate(b, verts=b.verts, vec=-pivote)
        if g.nombres_exactos or len(usadas) == 1:
            nom = pz if (g.nombres_exactos and pz != "cuerpo") else nombre
        else:
            nom = nombre if pz == "cuerpo" else f"{nombre}_{pz}"
        m2 = bpy.data.meshes.new(nom)
        b.to_mesh(m2)
        t = sum(len(f.verts) - 2 for f in b.faces)
        b.free()
        o = bpy.data.objects.new(nom, m2)
        o.location = pivote
        bpy.context.scene.collection.objects.link(o)
        tipo = g.tipos.get(pz)
        nm = f"{nombre}_mat" + (f"_{tipo}" if tipo else "")
        m2.materials.append(bpy.data.materials.get(nm) or material_final(nm, rutas, tipo))
        for poly in m2.polygons:
            poly.material_index = 0
        objs.append(o)
        info_piezas[nom] = {"triangulos": t, "tipo": tipo or "textura"}
        info_piezas[nom]["_pz"] = pz
    bpy.data.objects.remove(obj, do_unlink=True)
    bpy.context.view_layer.update()

    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    dim = [max(p[i] for p in pts) - min(p[i] for p in pts) for i in range(3)]
    sub = f"{tris} triángulos (límite {limite})   ·   {dim[0]:.1f} × {dim[1]:.1f} × {dim[2]:.1f} studs (ancho × fondo × alto)" \
          f"   ·   atlas {TAM_ATLAS}²   ·   piezas: {', '.join(info_piezas)}"
    vistas = renderizar(objs, tmp, nombre, tam=260 if rapido else 420, muestras=12 if rapido else 32)
    tres = hoja_turnaround(vistas, os.path.join(carpeta, f"{nombre}_turnaround.png"), nombre, sub)
    for r in vistas:
        os.remove(r)

    # GIRO_IMPORTACION: 180° sobre la vertical (Y de Roblox = Z de Blender), aplicado a la malla.
    giro = Matrix.Rotation(math.pi, 4, "Z")
    for o in objs:
        o.data.transform(giro)
        o.location = giro @ o.location
    bpy.context.view_layer.update()
    exportar_fbx(os.path.join(carpeta, f"{nombre}.fbx"), objs)

    def rbx(p):
        """Blender (x, y, z) del modelo original -> ejes de Roblox (x, z, -y), como el resto del proyecto."""
        return [round(p[0], 3), round(p[2], 3), round(-p[1], 3)]

    nombre_de = {d["_pz"]: nom for nom, d in info_piezas.items()}
    for o in objs:
        d = info_piezas[o.name]
        pz = d.pop("_pz")
        # Centro de la caja de la pieza (donde Roblox pone la Position del MeshPart), deshaciendo el giro.
        cs = [giro @ (o.matrix_world @ Vector(c)) for c in o.bound_box]
        d["centro"] = rbx([(max(c[i] for c in cs) + min(c[i] for c in cs)) / 2 for i in range(3)])
        if pz in g.pivotes:
            d["pivote"] = rbx(g.pivotes[pz])
        if pz in g.padres:
            d["padre"] = nombre_de.get(g.padres[pz], g.padres[pz])
    info = {"modelo": nombre, "triangulos": tris, "limite": limite,
            "tam_studs": {"ancho_x": round(dim[0], 2), "alto_y": round(dim[2], 2), "fondo_z": round(dim[1], 2)},
            "texturas": {k: os.path.basename(v) for k, v in rutas.items()}, "piezas": info_piezas,
            "anclas": {k: rbx(v) for k, v in g.anclas.items()},
            "nota": "Studs, ejes de Roblox (Y arriba) respecto al origen del modelo: Blender (x, y, z) -> Roblox (x, z, -y). "
                    "El FBX lleva aplicado el GIRO_IMPORTACION (180° sobre la vertical)."}
    info.update(g.extra)
    with open(os.path.join(carpeta, f"{nombre}.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)
    estado = "OK" if tris <= limite else "¡¡PASA DEL LÍMITE!!"
    print(f"[modelo] {nombre}: {tris} tri {estado} · {dim[0]:.1f}×{dim[1]:.1f}×{dim[2]:.1f} · piezas {list(info_piezas)}",
          flush=True)
    return info, tres
