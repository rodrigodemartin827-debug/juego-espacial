"""
Las dos pistolas de portales (después de la v1, ver CLAUDE.md «Descubrimiento y portales»):

  * CHATARRA (la normal): la fabrica el jugador con restos. Tubos y chapas oxidados y abollados, piezas desparejadas,
    soldaduras, tornillos, remaches, bridas, cinta americana, cables sueltos, un depósito de cristal con el combustible
    brillante, una rueda de válvula y una manivela.
  * VIP (gamepass): metal pulido oscuro, piezas encajadas, núcleo de energía a la vista en el centro (sin depósito),
    tres anillos que flotan alrededor del cañón y líneas de luz por el cuerpo.

Uso (con el bpy de herramientas/requirements.txt):
    python modelos/herramientas/pistola_portales.py --salida modelos/pistola_portales --ronda 5 [--rapido]

Unidades y ejes (la receta de la región 1, comprobada en Studio):
  * Se modela directamente en STUDS (1 unidad de Blender = 1 stud). En Studio: Scale Unit = Stud.
  * La pistola apunta a -Y en Blender. El FBX llega a Roblox como (x, z, -y), o sea, con el cañón hacia +Z: girado
    180° sobre su eje vertical (lo mismo que encontró el director con la región 1). `montar_*.luau` lo corrige con
    GIRO_IMPORTACION, y los JSON dan las posiciones ya en el marco bueno (-x, z, y): cañón hacia -Z.

Cada pistola sale con:
  * Un cuerpo con textura (atlas de 1024: color con oclusión, normales, metal y rugosidad) y, si las hay, piezas
    móviles con textura que comparten el mismo atlas (la rueda de la chatarra, los anillos de la VIP).
  * Las piezas que brillan como mallas aparte, sin textura (Material Neon en Roblox), y el cristal del depósito
    (Material Glass).
  * Dos Empty: «Boca» (de ahí sale el portal) y «Agarre» (donde va la mano: RightGripAttachment).
"""

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

import comun as c  # noqa: E402

# Todo en studs: se anula la conversión a metros de comun.
c.ESTUDIO = 1.0

AQUI = os.path.dirname(os.path.abspath(__file__))

# --------------------------------------------------------------------------------------------------------------
# Datos ajustables: colores (hex) de lo que no lleva textura, tamaño del atlas, límite de triángulos
# --------------------------------------------------------------------------------------------------------------

TAM_ATLAS = 1024
Z_SUELO = -0.40  # suelo del estudio (por debajo de las empuñaduras)
LIMITE_TRIANGULOS = 4000

NEON = {
    "Chatarra_Combustible": "#7DFF3A",  # verde ácido: el combustible de portal
    "Chatarra_Luces": "#7DFF3A",
    "VIP_Nucleo": "#A64BFF",  # morado
    "VIP_Luces": "#3FF0FF",  # cian
    "VIP_Anillo1_Luz": "#3FF0FF",
    "VIP_Anillo2_Luz": "#3FF0FF",
    "VIP_Anillo3_Luz": "#3FF0FF",
}
CRISTAL = {"Chatarra_Deposito": ("#B9E6D2", 0.55)}  # color, Transparency en Roblox


# --------------------------------------------------------------------------------------------------------------
# Geometría: una «Pieza» acumula sólidos cerrados en un bmesh, con un material por cara
# --------------------------------------------------------------------------------------------------------------


def marco(eje):
    """Matriz 3x3 que lleva Z al `eje` (vector o 'X', 'Y', 'Z')."""
    if isinstance(eje, str):
        return {"Z": Matrix.Identity(3), "X": Matrix.Rotation(math.pi / 2, 3, "Y"),
                "Y": Matrix.Rotation(-math.pi / 2, 3, "X"), "-Y": Matrix.Rotation(math.pi / 2, 3, "X")}[eje]
    return Vector(eje).normalized().to_track_quat("Z", "Y").to_matrix()


def circulo(radio, n, giro=0.0, rx=None, cuadratura=2.0):
    rx = radio if rx is None else rx
    pts = []
    for i in range(n):
        a = giro + math.tau * i / n
        ca, sa = math.cos(a), math.sin(a)
        pts.append(Vector((math.copysign(abs(ca) ** (2 / cuadratura), ca) * rx,
                           math.copysign(abs(sa) ** (2 / cuadratura), sa) * radio, 0)))
    return pts


class Pieza:
    def __init__(self, nombre, materiales):
        self.nombre = nombre
        self.materiales = materiales  # {nombre: función que crea el material}
        self.bm = bmesh.new()
        self.mats = []

    def m(self, nombre):
        if nombre not in self.mats:
            assert nombre in self.materiales, f"material sin definir: {nombre}"
            self.mats.append(nombre)
        return self.mats.index(nombre)

    def _pintar(self, caras, mat):
        i = self.m(mat)
        for f in caras:
            f.material_index = i
        verts = {v for f in caras for v in f.verts}
        return verts

    # ---- sólidos básicos (todos cerrados, con grosor) ---------------------------------------------------------

    def loft(self, anillos, mat, cerrado=True, tapas=True):
        bm = self.bm
        vs = [[bm.verts.new(p) for p in a] for a in anillos]
        n = len(anillos[0])
        caras = []
        for k in range(len(vs) - 1):
            for i in range(n if cerrado else n - 1):
                j = (i + 1) % n
                caras.append(bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i])))
        if tapas:
            caras.append(bm.faces.new(list(reversed(vs[0]))))
            caras.append(bm.faces.new(vs[-1]))
        return self._pintar(caras, mat)

    def caja(self, centro, tam, mat, giro=None):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        mtx = Matrix.Diagonal((*tam, 1.0))
        if giro is not None:
            mtx = giro.to_4x4() @ mtx
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(Vector(centro)) @ mtx, verts=r["verts"])
        caras = {f for v in r["verts"] for f in v.link_faces}
        return self._pintar(caras, mat)

    def cilindro(self, base, radio, largo, mat, lados=12, eje="Z", radio2=None, giro=0.0):
        r2 = radio if radio2 is None else radio2
        R = marco(eje)
        base = Vector(base)
        a = [base + R @ p for p in circulo(radio, lados, giro)]
        b = [base + R @ (p + Vector((0, 0, largo))) for p in circulo(r2, lados, giro)]
        return self.loft([a, b], mat)

    def perfil(self, base, eje, secciones, mat, lados=12, giro=0.0):
        """Sólido de revolución: secciones = [(distancia a lo largo del eje, radio)]."""
        R = marco(eje)
        base = Vector(base)
        anillos = [[base + R @ (p + Vector((0, 0, d))) for p in circulo(max(r, 1e-4), lados, giro)]
                   for d, r in secciones]
        return self.loft(anillos, mat)

    def tubo_hueco(self, base, eje, r_ext, r_int, largo, mat, lados=12, r_ext2=None, r_int2=None):
        """Tubo con pared de verdad (anillo extruido): para latas, bocas, abrazaderas, anillos."""
        R = marco(eje)
        base = Vector(base)
        re2 = r_ext if r_ext2 is None else r_ext2
        ri2 = r_int if r_int2 is None else r_int2
        oe0 = [base + R @ p for p in circulo(r_ext, lados)]
        oe1 = [base + R @ (p + Vector((0, 0, largo))) for p in circulo(re2, lados)]
        oi0 = [base + R @ p for p in circulo(r_int, lados)]
        oi1 = [base + R @ (p + Vector((0, 0, largo))) for p in circulo(ri2, lados)]
        bm = self.bm
        A, B, C, D = ([bm.verts.new(p) for p in a] for a in (oe0, oe1, oi1, oi0))
        caras = []
        for anillo1, anillo2 in ((A, B), (B, C), (C, D), (D, A)):
            for i in range(lados):
                j = (i + 1) % lados
                caras.append(bm.faces.new((anillo1[i], anillo1[j], anillo2[j], anillo2[i])))
        return self._pintar(caras, mat)

    def tubo(self, puntos, radio, mat, lados=6, radios=None):
        """Tubo cerrado a lo largo de una polilínea (cables, alambres, cordones de soldadura)."""
        puntos = [Vector(p) for p in puntos]
        n = len(puntos)
        tang = []
        for i in range(n):
            a = puntos[max(i - 1, 0)]
            b = puntos[min(i + 1, n - 1)]
            tang.append((b - a).normalized())
        # Marco que gira lo mínimo (sin retorcer el tubo).
        ref = Vector((0, 0, 1)) if abs(tang[0].z) < 0.9 else Vector((1, 0, 0))
        u = tang[0].cross(ref).normalized()
        anillos = []
        for i in range(n):
            if i:
                u = (u - tang[i] * u.dot(tang[i])).normalized()
            v = tang[i].cross(u)
            r = radios[i] if radios else radio
            anillos.append([puntos[i] + (u * math.cos(a) + v * math.sin(a)) * r
                            for a in (math.tau * k / lados for k in range(lados))])
        return self.loft(anillos, mat)

    def toro(self, centro, eje, R, r, mat, n_mayor=16, n_menor=6, arco=math.tau, sx=1.0):
        """Toro (o trozo de toro, que se cierra con tapas): aros, llantas, bridas."""
        M = marco(eje)
        centro = Vector(centro)
        completo = arco >= math.tau - 1e-6
        pasos = n_mayor if completo else n_mayor + 1
        anillos = []
        for i in range(pasos):
            t = arco * i / n_mayor
            d = Vector((math.cos(t), math.sin(t), 0))
            anillos.append([centro + M @ (d * (R + math.cos(a) * r * sx) + Vector((0, 0, math.sin(a) * r)))
                            for a in (math.tau * k / n_menor for k in range(n_menor))])
        if completo:
            anillos.append(anillos[0])
            bm = self.bm
            vs = [[bm.verts.new(p) for p in a] for a in anillos[:-1]]
            vs.append(vs[0])
            caras = []
            for k in range(n_mayor):
                for i in range(n_menor):
                    j = (i + 1) % n_menor
                    caras.append(bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i])))
            return self._pintar(caras, mat)
        return self.loft(anillos, mat)

    def esfera(self, centro, radio, mat, sub=1, escala=(1, 1, 1)):
        r = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=1.0)
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(Vector(centro)) @
                            Matrix.Diagonal((*(Vector(escala) * radio), 1)), verts=r["verts"])
        return self._pintar({f for v in r["verts"] for f in v.link_faces}, mat)

    def tornillo(self, pos, normal, mat, r=0.035, alto=0.025, lados=6):
        """Cabeza hexagonal (o remache si lados=5 y cúpula)."""
        n = Vector(normal).normalized()
        return self.cilindro(Vector(pos) - n * 0.01, r, alto + 0.01, mat, lados=lados, eje=n, giro=random.random())

    def remache(self, pos, normal, mat, r=0.022):
        n = Vector(normal).normalized()
        return self.perfil(Vector(pos) - n * 0.01, n, [(0, r), (0.012, r), (0.022, r * 0.6)], mat, lados=5)

    # ---- deformaciones -----------------------------------------------------------------------------------------

    def abollar(self, verts, amp, escala=3.0, semilla=0.0):
        """Desplaza los vértices con ruido suave: chapa abollada, tubo torcido."""
        for v in verts:
            p = v.co * escala + Vector((semilla, semilla * 1.7, semilla * 0.3))
            v.co += noise.noise_vector(p) * amp

    def transformar(self, verts, matriz):
        bmesh.ops.transform(self.bm, matrix=matriz, verts=list(verts))

    # ---- objeto ------------------------------------------------------------------------------------------------

    def objeto(self):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
        mats = [self.materiales[n]() for n in self.mats]
        malla = bpy.data.meshes.new(self.nombre)
        bm.to_mesh(malla)
        bm.free()
        ob = bpy.data.objects.new(self.nombre, malla)
        bpy.context.scene.collection.objects.link(ob)
        for m in mats:
            malla.materials.append(m)
        return ob


# --------------------------------------------------------------------------------------------------------------
# Materiales procedurales (se hornean en el atlas): color, metal, rugosidad y relieve
# --------------------------------------------------------------------------------------------------------------

_cache = {}


def _nodo(nt, tipo, **entradas):
    n = nt.nodes.new(tipo)
    for k, v in entradas.items():
        n.inputs[k].default_value = v
    return n


def _mezcla(nt, fac, a, b, tipo="RGBA"):
    """Mezcla a/b (sockets o valores) con el factor `fac` (socket)."""
    m = nt.nodes.new("ShaderNodeMix")
    m.data_type = tipo
    nt.links.new(fac, m.inputs["Factor"])
    ia, ib = (m.inputs[6], m.inputs[7]) if tipo == "RGBA" else (m.inputs[2], m.inputs[3])
    for s, v in ((ia, a), (ib, b)):
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, s)
        else:
            s.default_value = (*v, 1) if tipo == "RGBA" else v
    return m.outputs[2] if tipo == "RGBA" else m.outputs[0]


def _mascara(nt, coords, escala, desde, hasta, detalle=6, semilla=0.0, estirar=None):
    """Ruido -> rampa [desde, hasta] (0..1). `estirar` deforma las coordenadas (rayas, chorretones)."""
    v = coords
    if estirar is not None or semilla:
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Location"].default_value = (semilla, semilla * 0.7, semilla * 1.3)
        if estirar is not None:
            mp.inputs["Scale"].default_value = estirar
        nt.links.new(coords, mp.inputs["Vector"])
        v = mp.outputs[0]
    r = _nodo(nt, "ShaderNodeTexNoise", Scale=escala, Detail=detalle, Roughness=0.62)
    nt.links.new(v, r.inputs["Vector"])
    rampa = nt.nodes.new("ShaderNodeMapRange")
    rampa.inputs["From Min"].default_value = desde
    rampa.inputs["From Max"].default_value = hasta
    nt.links.new(r.outputs["Fac"], rampa.inputs["Value"])
    return rampa.outputs[0]


def mat_chatarra(nombre, pintura, *, metal_pintura=0.0, rug_pintura=0.55, oxido=0.45, desgaste=0.35,
                 metal_desnudo="#8C8F93", abolladura=0.5, semilla=0.0):
    """
    Chapa de chatarra: pintura (o metal) con desconchones que dejan ver el metal, manchas de óxido y chorretones,
    y relieve de martillazos. `oxido` y `desgaste` (0..1) son cuánto se ve de cada cosa.
    """
    def crear():
        clave = nombre
        if clave in _cache:
            return _cache[clave]
        mat = bpy.data.materials.new(nombre)
        mat.use_nodes = True
        nt = mat.node_tree
        b = nt.nodes["Principled BSDF"]
        coords = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
        c_pint = c.srgb(pintura)
        c_metal = c.srgb(metal_desnudo)
        c_oxido1 = c.srgb("#7A3A17")
        c_oxido2 = c.srgb("#B0621F")
        # desconchones (metal desnudo) y óxido
        m_desg = _mascara(nt, coords, 9.0, 0.70 - desgaste * 0.25, 0.73 - desgaste * 0.25, semilla=semilla + 3)
        m_ox = _mascara(nt, coords, 4.5, 0.62 - oxido * 0.22, 0.70 - oxido * 0.22, semilla=semilla)
        m_chorro = _mascara(nt, coords, 6.0, 0.55, 0.75, semilla=semilla + 7, estirar=(1.0, 1.0, 0.18))
        m_tono = _mascara(nt, coords, 22.0, 0.3, 0.7, semilla=semilla + 11)
        # óxido = manchas + chorretones verticales (los que caen de los tornillos y las juntas)
        ox_total = nt.nodes.new("ShaderNodeMath")
        ox_total.operation = "MAXIMUM"
        nt.links.new(m_ox, ox_total.inputs[0])
        k = nt.nodes.new("ShaderNodeMath")
        k.operation = "MULTIPLY"
        k.inputs[1].default_value = oxido * 0.75
        nt.links.new(m_chorro, k.inputs[0])
        nt.links.new(k.outputs[0], ox_total.inputs[1])
        color_ox = _mezcla(nt, m_tono, c_oxido1, c_oxido2)
        # pintura con ligera variación de tono
        pint_var = _mezcla(nt, m_tono, tuple(x * 0.82 for x in c_pint), c_pint)
        col = _mezcla(nt, m_desg, pint_var, c_metal)
        col = _mezcla(nt, ox_total.outputs[0], col, color_ox)
        nt.links.new(col, b.inputs["Base Color"])
        met = _mezcla(nt, m_desg, metal_pintura, 0.85, tipo="FLOAT")
        met = _mezcla(nt, ox_total.outputs[0], met, 0.15, tipo="FLOAT")
        nt.links.new(met, b.inputs["Metallic"])
        rug = _mezcla(nt, m_desg, rug_pintura, 0.38, tipo="FLOAT")
        rug = _mezcla(nt, ox_total.outputs[0], rug, 0.9, tipo="FLOAT")
        nt.links.new(rug, b.inputs["Roughness"])
        # relieve: martillazos grandes + grano del óxido
        r1 = _nodo(nt, "ShaderNodeTexNoise", Scale=5.0, Detail=2, Roughness=0.4)
        nt.links.new(coords, r1.inputs["Vector"])
        r2 = _nodo(nt, "ShaderNodeTexNoise", Scale=70.0, Detail=4, Roughness=0.6)
        nt.links.new(coords, r2.inputs["Vector"])
        alt = nt.nodes.new("ShaderNodeMath")
        alt.operation = "MULTIPLY_ADD"
        nt.links.new(r2.outputs["Fac"], alt.inputs[0])
        nt.links.new(ox_total.outputs[0], alt.inputs[1])
        nt.links.new(r1.outputs["Fac"], alt.inputs[2])
        bump = _nodo(nt, "ShaderNodeBump", Strength=0.35 * abolladura + 0.1, Distance=0.02)
        nt.links.new(alt.outputs[0], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
        _cache[clave] = mat
        return mat

    return crear


def mat_liso(nombre, color, metal=0.0, rug=0.5, ruido=0.0, bump=0.0, escala_bump=40.0, lineas=None):
    """
    Material limpio (cinta, goma, cobre, metal pulido). `ruido` varía el tono, `bump` da grano.
    `lineas` = (separación, grosor, eje): ranuras de panel grabadas (para la VIP).
    """
    def crear():
        if nombre in _cache:
            return _cache[nombre]
        mat = bpy.data.materials.new(nombre)
        mat.use_nodes = True
        nt = mat.node_tree
        b = nt.nodes["Principled BSDF"]
        coords = nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]
        base = c.srgb(color)
        col = base
        if ruido:
            m = _mascara(nt, coords, 14.0, 0.3, 0.7, semilla=len(nombre))
            col = _mezcla(nt, m, tuple(x * (1 - ruido) for x in base), base)
        if isinstance(col, tuple):
            b.inputs["Base Color"].default_value = (*col, 1)
        else:
            nt.links.new(col, b.inputs["Base Color"])
        b.inputs["Metallic"].default_value = metal
        b.inputs["Roughness"].default_value = rug
        alturas = []
        if bump:
            r = _nodo(nt, "ShaderNodeTexNoise", Scale=escala_bump, Detail=5, Roughness=0.6)
            nt.links.new(coords, r.inputs["Vector"])
            alturas.append((r.outputs["Fac"], bump))
        if lineas:
            sep, grosor, eje = lineas
            xyz = nt.nodes.new("ShaderNodeSeparateXYZ")
            nt.links.new(coords, xyz.inputs[0])
            f = nt.nodes.new("ShaderNodeMath")
            f.operation = "PINGPONG"
            f.inputs[1].default_value = sep / 2
            nt.links.new(xyz.outputs[eje], f.inputs[0])
            ranura = nt.nodes.new("ShaderNodeMapRange")
            ranura.inputs["From Min"].default_value = grosor
            ranura.inputs["From Max"].default_value = grosor * 1.6
            nt.links.new(f.outputs[0], ranura.inputs["Value"])
            # ranura más oscura
            if isinstance(col, tuple):
                col_s = _mezcla(nt, ranura.outputs[0], tuple(x * 0.35 for x in base), base)
            else:
                col_s = _mezcla(nt, ranura.outputs[0], tuple(x * 0.35 for x in base), col)
            nt.links.new(col_s, b.inputs["Base Color"])
            alturas.append((ranura.outputs[0], 1.0))
        if alturas:
            h = alturas[0][0]
            for s, _ in alturas[1:]:
                mx = nt.nodes.new("ShaderNodeMath")
                mx.operation = "MULTIPLY"
                nt.links.new(h, mx.inputs[0])
                nt.links.new(s, mx.inputs[1])
                h = mx.outputs[0]
            bn = _nodo(nt, "ShaderNodeBump", Strength=max(a for _, a in alturas) * 0.5, Distance=0.01)
            nt.links.new(h, bn.inputs["Height"])
            nt.links.new(bn.outputs["Normal"], b.inputs["Normal"])
        _cache[nombre] = mat
        return mat

    return crear


def mat_neon(nombre, hexa):
    def crear():
        if nombre in _cache:
            return _cache[nombre]
        m = c.material(nombre, c.srgb(hexa), rugosidad=0.3, emision=c.srgb(hexa), fuerza_emision=2.6)
        _cache[nombre] = m
        return m
    return crear


def mat_cristal(nombre, hexa):
    def crear():
        if nombre in _cache:
            return _cache[nombre]
        m = c.material(nombre, c.srgb(hexa), rugosidad=0.04, transmision=1.0)
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["IOR"].default_value = 1.2
        _cache[nombre] = m
        return m
    return crear


# --------------------------------------------------------------------------------------------------------------
# PISTOLA DE CHATARRA
# --------------------------------------------------------------------------------------------------------------
# Ejes: cañón hacia -Y, arriba +Z. Mirando hacia -Y, la derecha del que dispara es -X (en Roblox, +X).

MAT_CHATARRA = {
    "acero": mat_chatarra("ch_acero", "#6E7176", metal_pintura=0.8, rug_pintura=0.45, oxido=0.55, desgaste=0.0,
                          semilla=1),
    "verde": mat_chatarra("ch_verde", "#4F6B3A", oxido=0.35, desgaste=0.45, semilla=2),
    "rojo": mat_chatarra("ch_rojo", "#A3332A", oxido=0.30, desgaste=0.55, semilla=3),
    "azul": mat_chatarra("ch_azul", "#2F5B86", oxido=0.40, desgaste=0.5, semilla=4),
    "amarillo": mat_chatarra("ch_amarillo", "#D9A520", oxido=0.25, desgaste=0.5, semilla=5),
    "galva": mat_chatarra("ch_galva", "#A7ADB2", metal_pintura=0.9, rug_pintura=0.5, oxido=0.30, desgaste=0.0,
                          semilla=6),
    "laton": mat_chatarra("ch_laton", "#C29A4A", metal_pintura=1.0, rug_pintura=0.35, oxido=0.12, desgaste=0.0,
                          abolladura=0.2, semilla=7),
    "cobre": mat_liso("ch_cobre", "#C8693A", metal=1.0, rug=0.3, ruido=0.25),
    "soldadura": mat_liso("ch_soldadura", "#4A4440", metal=0.7, rug=0.6, ruido=0.4, bump=1.0, escala_bump=90),
    "tornillo": mat_chatarra("ch_tornillo", "#9A9890", metal_pintura=0.9, rug_pintura=0.4, oxido=0.5, desgaste=0,
                             abolladura=0.1, semilla=8),
    "cinta": mat_liso("ch_cinta", "#9EA3A6", metal=0.0, rug=0.55, ruido=0.18, bump=0.5, escala_bump=60),
    "goma": mat_liso("ch_goma", "#1E1E20", rug=0.75, ruido=0.2),
    "cable_rojo": mat_liso("ch_cable_rojo", "#B5221B", rug=0.45, ruido=0.1),
    "cable_amarillo": mat_liso("ch_cable_amar", "#E3B21E", rug=0.45, ruido=0.1),
    "cable_negro": mat_liso("ch_cable_negro", "#222326", rug=0.5, ruido=0.1),
    "brida": mat_liso("ch_brida", "#141416", rug=0.6),
    "esfera": mat_liso("ch_esfera", "#EDE6CF", rug=0.4, ruido=0.12),
    "aguja": mat_liso("ch_aguja", "#C0201A", rug=0.4),
}


def construir_chatarra():
    random.seed(7)
    cu = Pieza("Chatarra_Cuerpo", MAT_CHATARRA)
    ru = Pieza("Chatarra_Rueda", MAT_CHATARRA)
    dm = Pieza("Chatarra_DepositoMarco", MAT_CHATARRA)  # tapones, abrazaderas y jaula: sube y baja con el depósito
    de = Pieza("Chatarra_Deposito", {"cristal": mat_cristal("ch_cristal", CRISTAL["Chatarra_Deposito"][0])})
    co = Pieza("Chatarra_Combustible", {"neon": mat_neon("ch_neon", NEON["Chatarra_Combustible"])})
    lu = Pieza("Chatarra_Luces", {"neon": mat_neon("ch_neon", NEON["Chatarra_Luces"])})

    # --- Cajón (cuerpo central): una caja de acero con dos chapas laterales desparejadas ---------------------------
    zc = 0.78  # altura del eje del cañón
    caja = cu.caja((0, 0.12, 0.70), (0.40, 1.00, 0.46), "acero")
    cu.abollar(caja, 0.018, 4.0, 1.0)
    # chapa verde (más corta) en el lado izquierdo del tirador (+X) y galvanizada en el derecho (-X)
    chapa_i = cu.caja((-0.215, 0.02, 0.69), (0.04, 0.70, 0.40), "verde", giro=Matrix.Rotation(0.04, 3, "X"))
    cu.abollar(chapa_i, 0.015, 6.0, 2.0)
    chapa_d = cu.caja((0.215, 0.26, 0.66), (0.04, 0.62, 0.34), "galva", giro=Matrix.Rotation(-0.05, 3, "X"))
    cu.abollar(chapa_d, 0.015, 6.0, 3.0)
    for (y, z) in ((-0.28, 0.85), (0.32, 0.86), (-0.28, 0.52), (0.32, 0.51)):
        cu.tornillo((-0.237, y, z), (-1, 0, 0), "tornillo")
    for (y, z) in ((0.0, 0.81), (0.52, 0.80), (0.0, 0.52), (0.52, 0.52)):
        cu.remache((0.237, y, z), (1, 0, 0), "tornillo")
    # tapa trasera: una lata azul tumbada, con brida de tornillos
    cu.perfil((0, 0.60, 0.70), "Y", [(0, 0.25), (0.04, 0.27), (0.08, 0.27), (0.09, 0.24), (0.30, 0.24),
                                     (0.32, 0.22), (0.33, 0.16)], "azul", lados=14)
    for k in range(6):
        a = math.tau * k / 6 + 0.3
        cu.tornillo((math.cos(a) * 0.21, 0.66, 0.70 + math.sin(a) * 0.21), (0, 1, 0), "tornillo", r=0.026)
    # cordón de soldadura entre la lata y el cajón
    pts = [(math.cos(a) * 0.255, 0.62, 0.70 + math.sin(a) * 0.235) for a in
           (math.tau * k / 22 for k in range(23))]
    cu.tubo(pts, 0.022, "soldadura", lados=4, radios=[0.018 + 0.01 * random.random() for _ in pts])

    # --- Manómetro encima, de latón, con esfera clara y aguja -----------------------------------------------------
    cu.perfil((0.04, 0.34, 0.93), "Z", [(0, 0.05), (0.06, 0.05), (0.06, 0.03)], "laton", lados=8)
    cu.perfil((0.04, 0.34, 1.05), "-Y", [(-0.06, 0.13), (0.0, 0.13), (0.035, 0.12)], "laton", lados=14)
    # esfera (cara hacia el que dispara, +Y)
    cu.cilindro((0.04, 0.37, 1.05), 0.105, 0.012, "esfera", lados=14, eje="Y")
    cu.caja((0.06, 0.385, 1.08), (0.012, 0.008, 0.085), "aguja", giro=Matrix.Rotation(-0.7, 3, "Y"))
    # bombilla verde al lado (indicador de combustible)
    cu.perfil((-0.13, 0.48, 0.93), "Z", [(0, 0.045), (0.05, 0.045)], "laton", lados=8)
    lu.esfera((-0.13, 0.48, 1.02), 0.05, "neon", sub=1)

    # --- Cañón: tubo galvanizado con manguito, bobina de cobre y boca de lata roja ---------------------------------
    cu.perfil((0, -0.38, zc), "-Y", [(0, 0.14), (0.95, 0.12)], "galva", lados=12)
    cu.perfil((0, -0.36, zc), "-Y", [(0, 0.16), (0.05, 0.18), (0.13, 0.18), (0.16, 0.16)], "laton", lados=6)
    # soldadura cañón-cajón
    pts = [(math.cos(a) * 0.16, -0.38, zc + math.sin(a) * 0.16) for a in (math.tau * k / 18 for k in range(19))]
    cu.tubo(pts, 0.02, "soldadura", lados=4, radios=[0.016 + 0.01 * random.random() for _ in pts])
    # bobina de cobre (4,5 vueltas)
    pts = []
    for k in range(4 * 10 + 6):
        t = k / 10 * math.tau
        y = -0.60 - 0.42 * k / 46
        pts.append((math.cos(t) * 0.152, y, zc + math.sin(t) * 0.152))
    cu.tubo(pts, 0.024, "cobre", lados=4)
    # boca: lata roja abierta, con pared de verdad, abollada
    boca = cu.tubo_hueco((0, -1.30, zc), "-Y", 0.15, 0.115, 0.30, "rojo", lados=14, r_ext2=0.22, r_int2=0.19)
    cu.abollar(boca, 0.012, 7.0, 4.0)
    cu.tubo_hueco((0, -1.58, zc), "-Y", 0.235, 0.185, 0.04, "galva", lados=14)  # borde de la lata
    cu.cilindro((0, -1.32, zc), 0.12, 0.04, "acero", lados=12, eje="-Y")  # fondo de la boca
    # tres púas (clavos doblados) que miran hacia delante
    for k in range(3):
        a = math.tau * k / 3 + math.pi / 2
        d = Vector((math.cos(a), 0, math.sin(a)))
        base = Vector((0, -1.50, zc)) + d * 0.21
        pts = [base, base + Vector((0, -0.10, 0)) + d * 0.04, base + Vector((0, -0.24, 0)) - d * 0.03]
        cu.tubo(pts, 0.024, "acero", lados=5, radios=[0.026, 0.02, 0.008])
    # brida negra que sujeta el cable al cañón
    cu.toro((0, -0.50, zc), "Y", 0.135, 0.012, "brida", n_mayor=12, n_menor=4, sx=1.0)
    cu.caja((0, -0.50, zc + 0.15), (0.05, 0.04, 0.04), "brida")

    # --- Depósito de combustible: cilindro de cristal bajo el cañón, con tapas y abrazaderas -----------------------
    zd, y0, y1, rd = 0.38, -0.36, -1.08, 0.15
    de.cilindro((0, y0 - 0.02, zd), rd, (y0 - y1) - 0.04 + 0.04, "cristal", lados=14, eje="-Y")
    # líquido (lleno a 3/4): sección de círculo recortada por arriba
    nivel = zd + rd * 0.45
    sec = []
    for k in range(16):
        a = math.tau * k / 16
        x, z = math.cos(a) * (rd - 0.02), zd + math.sin(a) * (rd - 0.02)
        sec.append((x, min(z, nivel)))
    co.loft([[Vector((x, y, z)) for x, z in sec] for y in (y0 - 0.04, y1 + 0.04)], "neon")
    # burbujas dentro (pequeñas, del mismo neón)
    for (y, x, z) in ((-0.55, 0.05, 0.46), (-0.78, -0.06, 0.43), (-0.92, 0.03, 0.47)):
        co.esfera((x, y, z + 0.035), 0.02, "neon", sub=1)
    # tapas: tapón trasero de latón y tapón delantero rojo con la manguera
    dm.perfil((0, y0 + 0.07, zd), "-Y", [(0, 0.12), (0.03, 0.17), (0.09, 0.17), (0.11, 0.16)], "laton", lados=8)
    dm.perfil((0, y1 + 0.02, zd), "-Y", [(0, 0.16), (0.02, 0.17), (0.08, 0.17), (0.10, 0.12), (0.14, 0.06),
                                         (0.16, 0.06)], "azul", lados=8)
    # dos abrazaderas de chapa con su tornillo, y las patas que las unen al cañón
    for y in (-0.52, -0.90):
        dm.tubo_hueco((0, y + 0.03, zd), "-Y", rd + 0.022, rd + 0.004, 0.06, "acero", lados=14)
        dm.caja((rd + 0.03, y, zd + 0.02), (0.05, 0.05, 0.07), "acero")
        dm.tornillo((rd + 0.055, y, zd + 0.02), (1, 0, 0), "tornillo", r=0.022)
        cu.caja((0, y, (zd + rd + zc - 0.12) / 2), (0.05, 0.06, (zc - 0.12) - (zd + rd) + 0.03), "verde")
    # tres varillas de jaula por fuera del cristal
    for a in (math.radians(200), math.radians(270), math.radians(340)):
        d = Vector((math.cos(a), 0, math.sin(a)))
        dm.tubo([Vector((0, y0 - 0.02, zd)) + d * (rd + 0.02), Vector((0, y1 + 0.02, zd)) + d * (rd + 0.02)],
                0.014, "acero", lados=4)
    # manguera de goma desde la tapa delantera hasta el cañón (el combustible sube a la bobina)
    pts = [(0, y1 - 0.13, zd), (0, y1 - 0.20, zd + 0.05), (0, y1 - 0.20, zd + 0.22), (0, -1.06, zc - 0.10),
           (0, -1.02, zc - 0.11)]
    cu.tubo(pts, 0.035, "goma", lados=6)
    cu.toro((0, y1 - 0.20, zd + 0.13), "Z", 0.045, 0.01, "tornillo", n_mayor=8, n_menor=4)  # abrazadera
    # soporte trasero del depósito al cajón (pletina doblada amarilla)
    cu.caja((0, -0.37, 0.45), (0.10, 0.06, 0.22), "amarillo", giro=Matrix.Rotation(0.15, 3, "X"))

    # --- Rueda de válvula (pieza aparte para que gire): a la derecha del tirador (-X) ------------------------------------
    eje_r = Vector((-0.29, 0.10, 0.66))
    cu.perfil(eje_r + Vector((0.07, 0, 0)), "X", [(0, 0.035), (0.0, 0.05), (-0.05, 0.05), (-0.05, 0.03),
                                                  (-0.09, 0.03)], "laton", lados=6)  # vástago
    ru.toro(eje_r + Vector((-0.04, 0, 0)), "X", 0.19, 0.026, "rojo", n_mayor=14, n_menor=5)
    ru.cilindro(eje_r + Vector((-0.02, 0, 0)), 0.05, -0.05, "rojo", lados=8, eje="X")
    for k in range(4):
        a = math.tau * k / 4 + 0.4
        d = Vector((0, math.cos(a), math.sin(a)))
        ru.tubo([eje_r + Vector((-0.045, 0, 0)) + d * 0.04, eje_r + Vector((-0.04, 0, 0)) + d * 0.18], 0.018,
                "rojo", lados=5)
    ru.tornillo(eje_r + Vector((-0.07, 0, 0)), (-1, 0, 0), "tornillo", r=0.03)

    # --- Manivela a la izquierda del tirador (+X), para cargar el disparo ------------------------------------------------------------
    piv = Vector((0.25, 0.42, 0.80))
    cu.cilindro(piv, 0.055, 0.04, "tornillo", lados=8, eje="X")
    brazo = [piv + Vector((0.04, 0, 0)), piv + Vector((0.05, -0.06, -0.10)), piv + Vector((0.06, -0.10, -0.22))]
    cu.tubo(brazo, 0.03, "acero", lados=6)
    cu.cilindro(brazo[-1] + Vector((0.0, 0, 0)), 0.035, 0.14, "amarillo", lados=8, eje="X")

    # --- Empuñadura: un trozo de tubo envuelto en cinta americana, inclinado hacia atrás --------------------------
    inc = Matrix.Rotation(0.30, 3, "X")  # gira la parte de abajo hacia atrás (+Y)
    base_e = Vector((0, 0.30, 0.48))

    def e(p):
        return base_e + inc @ Vector(p)

    secs = [(-0.0, 0.15), (-0.30, 0.155), (-0.55, 0.15), (-0.78, 0.16), (-0.80, 0.14)]
    cu.loft([[e((x * 1.0, y * 1.25, z)) for x, y, z in
              ((p.x, p.y, d) for p in circulo(r, 10, cuadratura=2.6))] for d, r in secs], "acero")
    # vendas de cinta (cada una un poco torcida y más gruesa)
    for k, (z0, z1) in enumerate(((-0.06, -0.24), (-0.20, -0.40), (-0.38, -0.56), (-0.55, -0.70))):
        g = Matrix.Rotation(random.uniform(-0.12, 0.12), 3, "Y") @ Matrix.Rotation(random.uniform(-0.1, 0.1), 3,
                                                                                    "X")
        anillos = []
        for d in (z0, z1):
            anillos.append([e(g @ Vector((p.x, p.y * 1.25, d))) for p in circulo(0.172, 10, cuadratura=2.6)])
        cu.loft(anillos, "cinta")
    # tapón de abajo: una tuerca grande
    cu.cilindro(e((0, 0, -0.80)), 0.13, -0.07, "tornillo", lados=6, eje=inc @ Vector((0, 0, 1)))
    # gatillo (pletina doblada) y guardamonte de alambre
    cu.tubo([(0, 0.04, 0.47), (0, -0.02, 0.36), (0, 0.03, 0.26)], 0.03, "amarillo", lados=4,
            radios=[0.035, 0.03, 0.025])
    cu.tubo([(0, 0.22, 0.30), (0, 0.10, 0.17), (0, -0.07, 0.17), (0, -0.18, 0.28), (0, -0.20, 0.47)], 0.018,
            "acero", lados=5)

    # --- Cables sueltos que van de una parte a otra ----------------------------------------------------------------
    def colgante(a, b, caida, n=9):
        a, b = Vector(a), Vector(b)
        return [a.lerp(b, t) + Vector((0, 0, -caida * 4 * t * (1 - t))) for t in (k / (n - 1) for k in range(n))]

    # rojo: de la lata trasera a la bobina, por la izquierda del tirador (+X)
    cu.tubo(colgante((0.20, 0.74, 0.82), (0.12, -0.62, zc + 0.10), 0.0, n=4)[:1] +
            [Vector((0.30, 0.55, 0.92)), Vector((0.29, 0.10, 0.99)), Vector((0.22, -0.30, 0.97)),
             Vector((0.13, -0.56, 0.92)), Vector((0.10, -0.66, 0.90))], 0.025, "cable_rojo", lados=5)
    # amarillo: del manómetro a la boca, colgando por la derecha del tirador (-X)
    cu.tubo([Vector((-0.06, 0.30, 1.0)), Vector((-0.22, 0.12, 1.02))] +
            colgante((-0.24, 0.0, 0.98), (-0.17, -1.30, zc + 0.10), 0.16, n=8) +
            [Vector((-0.12, -1.40, zc + 0.15))], 0.022, "cable_amarillo", lados=5)
    # negro: de la bombilla al tapón del depósito, por debajo
    cu.tubo([Vector((-0.13, 0.52, 0.94)), Vector((-0.24, 0.55, 0.80)), Vector((-0.26, 0.10, 0.44)),
             Vector((-0.20, -0.30, 0.33)), Vector((-0.12, -0.36, 0.30))], 0.02, "cable_negro", lados=5)
    # cinta que sujeta el cable rojo y el amarillo al cañón
    cu.tubo_hueco((0, -0.86, zc), "-Y", 0.19, 0.155, 0.07, "cinta", lados=12)

    # --- Luz en el fondo de la boca (lo que brilla antes de abrir el portal) --------------------------------------
    lu.cilindro((0, -1.36, zc), 0.10, 0.02, "neon", lados=12, eje="-Y")

    boca_pos = Vector((0, -1.66, zc))
    piezas = {"Chatarra_Cuerpo": cu, "Chatarra_Rueda": ru, "Chatarra_DepositoMarco": dm,
              "Chatarra_Deposito": de, "Chatarra_Combustible": co, "Chatarra_Luces": lu}
    pivotes = {"Chatarra_Rueda": eje_r + Vector((-0.04, 0, 0)),
               "Chatarra_DepositoMarco": Vector((0, (y0 + y1) / 2, zd))}
    # Puntos para los efectos: chispas de la bobina (tres, en la parte alta y los costados)
    puntos = {"Chispas_Bobina_1": Vector((0.0, -0.70, zc + 0.17)), "Chispas_Bobina_2": Vector((-0.16, -0.84, zc + 0.04)),
              "Chispas_Bobina_3": Vector((0.15, -0.96, zc + 0.08))}
    return piezas, boca_pos, ["Chatarra_Cuerpo", "Chatarra_Rueda", "Chatarra_DepositoMarco"], pivotes, puntos


# --------------------------------------------------------------------------------------------------------------
# PISTOLA VIP
# --------------------------------------------------------------------------------------------------------------

MAT_VIP = {
    "grafito": mat_liso("vip_grafito", "#3E4555", metal=0.6, rug=0.3, ruido=0.06, lineas=(0.36, 0.006, "Y")),
    "negro": mat_liso("vip_negro", "#1D212B", metal=0.5, rug=0.4, ruido=0.04, bump=0.25, escala_bump=180),
    "blanco": mat_liso("vip_blanco", "#E3E7EE", metal=0.0, rug=0.25, ruido=0.03),
    "cromo": mat_liso("vip_cromo", "#E1E6EE", metal=1.0, rug=0.16),
    "violeta": mat_liso("vip_violeta", "#4B3480", metal=0.7, rug=0.3),
}


def seccion(y, tabla):
    """Interpola (ancho, alto, z centro) en una tabla [(y, ancho, alto, zc)] ordenada por y."""
    for (ya, *a), (yb, *b) in zip(tabla, tabla[1:]):
        if ya >= y >= yb or yb >= y >= ya:
            t = (y - ya) / (yb - ya) if yb != ya else 0
            return [u + (v - u) * t for u, v in zip(a, b)]
    return tabla[0][1:] if abs(y - tabla[0][0]) < abs(y - tabla[-1][0]) else tabla[-1][1:]


def anillo_seccion(y, ancho, alto, zc, n, cuad):
    return [Vector((p.x, y, zc + p.y)) for p in circulo(alto / 2, n, rx=ancho / 2, cuadratura=cuad)]


def construir_vip():
    random.seed(11)
    cu = Pieza("VIP_Cuerpo", MAT_VIP)
    nu = Pieza("VIP_Nucleo", {"neon": mat_neon("vip_neon_nucleo", NEON["VIP_Nucleo"])})
    lu = Pieza("VIP_Luces", {"neon": mat_neon("vip_neon", NEON["VIP_Luces"])})
    piezas_anillo = [Pieza(f"VIP_Anillo{i}", MAT_VIP) for i in (1, 2, 3)]
    luces_an = [Pieza(f"VIP_Anillo{i}_Luz", {"neon": mat_neon("vip_neon", NEON["VIP_Luces"])}) for i in (1, 2, 3)]
    zc = 0.80  # eje del cañón
    N, Q = 20, 3.2  # lados y «cuadratura» de las secciones del cuerpo (superelipse: cantos redondeados)

    # --- Bloque trasero: la culata. Loft de secciones que se afilan hacia atrás ------------------------------------
    tras = [(0.78, 0.22, 0.26, 0.80), (0.72, 0.34, 0.40, 0.78), (0.60, 0.40, 0.48, 0.75),
            (0.30, 0.42, 0.52, 0.74), (0.12, 0.42, 0.52, 0.74)]
    cu.loft([anillo_seccion(y, w, h, z, N, Q) for y, w, h, z in tras], "grafito")
    # --- Bloque delantero: la «cabeza» que sostiene el cañón ----------------------------------------------------
    dela = [(-0.30, 0.42, 0.50, 0.76), (-0.48, 0.40, 0.44, 0.78), (-0.58, 0.30, 0.34, zc), (-0.62, 0.24, 0.26, zc)]
    cu.loft([anillo_seccion(y, w, h, z, N, Q) for y, w, h, z in dela], "grafito")
    # --- Cámara del núcleo entre los dos bloques: dos raíles (arriba y abajo) y una jaula -----------------------
    for z, alto in ((1.00, 0.09), (0.505, 0.07)):
        cu.loft([anillo_seccion(y, 0.30, alto, z, 12, 3.0) for y in (0.14, -0.32)], "negro")
    # aros de la cámara (cromo) que abrazan el núcleo
    cnu = Vector((0, -0.09, 0.755))
    for y in (0.115, -0.295):
        cu.toro(Vector((0, y, 0.755)), "Y", 0.22, 0.03, "cromo", n_mayor=20, n_menor=6, sx=1.0)
    # garras que sujetan el núcleo (4, en cruz girada)
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        d = Vector((math.cos(a), 0, math.sin(a)))
        for y in (0.11, -0.29):
            p0 = Vector((0, y, 0.755)) + d * 0.21
            p1 = cnu + d * 0.15 + Vector((0, (y - cnu.y) * 0.35, 0))
            cu.tubo([p0, p0.lerp(p1, 0.5) + d * 0.03, p1], 0.022, "cromo", lados=5, radios=[0.026, 0.02, 0.012])
    # el núcleo: esfera de energía con un halo de cristal (dos mallas neón: núcleo y su anillo)
    nu.esfera(cnu, 0.13, "neon", sub=2)
    lu.toro(cnu, (0, 0, 1), 0.165, 0.008, "neon", n_mayor=20, n_menor=4)  # órbita horizontal del núcleo

    # --- Placas blancas encajadas en los costados (los detalles claros) --------------------------------------------
    for s in (-1, 1):
        for (ya, yb) in ((0.56, 0.30),):
            pts = []
            for y in (ya, (ya + yb) / 2, yb):
                w, h, z = seccion(y, tras)
                pts.append((y, w, h, z))
            # placa: misma curva del cuerpo, 0,02 más gruesa, solo en la franja central del costado
            anillos = []
            for y, w, h, z in pts:
                a0, a1 = -0.30, 0.22
                ring = []
                for k in range(7):
                    a = a0 + (a1 - a0) * k / 6
                    ca, sa = math.cos(a), math.sin(a)
                    x = math.copysign(abs(ca) ** (2 / Q), ca) * (w / 2 + 0.018)
                    zz = z + math.copysign(abs(sa) ** (2 / Q), sa) * (h / 2 + 0.018)
                    ring.append(Vector((s * x, y, zz)))
                inner = [Vector((s * (abs(p.x) - 0.03), p.y, p.z)) for p in reversed(ring)]
                anillos.append(ring + inner)
            cu.loft(anillos, "blanco")
    # la placa de cabeza (frente) con el emblema: una V de luz
    for s in (-1, 1):
        lu.caja((s * 0.212, -0.40, 0.82), (0.02, 0.13, 0.016), "neon", giro=Matrix.Rotation(s * 0.0, 3, "Z") @
                Matrix.Rotation(0.5, 3, "X"))
        lu.caja((s * 0.212, -0.40, 0.70), (0.02, 0.13, 0.016), "neon", giro=Matrix.Rotation(-0.5, 3, "X"))

    # --- Líneas de luz que recorren el cuerpo: tiras con grosor apoyadas en la superficie -------------------------
    def tira(ys, angulo, tabla, s=1, grosor=0.014, alto=0.02, mat="neon", pieza=lu):
        anillos = []
        for y in ys:
            w, h, z = seccion(y, tabla)
            ca, sa = math.cos(angulo), math.sin(angulo)
            x = math.copysign(abs(ca) ** (2 / Q), ca) * w / 2
            zz = z + math.copysign(abs(sa) ** (2 / Q), sa) * h / 2
            p = Vector((s * x, y, zz))
            nrm = Vector((s * ca, 0, sa)).normalized()
            t = Vector((0, 1, 0)).cross(nrm).normalized()
            anillos.append([p + nrm * (-0.01), p + t * grosor / 2 + nrm * (-0.01),
                            p + t * grosor / 2 + nrm * alto * 0.5, p - t * grosor / 2 + nrm * alto * 0.5,
                            p - t * grosor / 2 + nrm * (-0.01)])
        pieza.loft(anillos, mat)

    for s in (-1, 1):
        tira([0.74, 0.62, 0.40, 0.14], 0.62, tras, s)  # línea alta de la culata
        tira([-0.30, -0.45, -0.58], 0.45, dela, s)
    tira([0.76, 0.50, 0.14], math.pi / 2, tras, 1, grosor=0.02)  # espina de luz por arriba
    tira([-0.30, -0.56], math.pi / 2, dela, 1, grosor=0.02)
    # raíl de la cámara con luz en el canto
    lu.caja((0, -0.09, 1.048), (0.05, 0.40, 0.02), "neon")

    # --- Aletas de disipación encima de la culata -------------------------------------------------------------------
    for k, y in enumerate((0.62, 0.50, 0.38)):
        alto = 0.05 - k * 0.01
        cu.caja((0, y, 1.0 + alto / 2), (0.05 + 0.20 * 0, 0.045, alto + 0.04), "negro",
                giro=Matrix.Rotation(-0.35, 3, "X"))

    # --- Cañón: varilla central negra con punta de cromo y emisor -------------------------------------------------
    cu.perfil((0, -0.60, zc), "-Y", [(0, 0.10), (0.06, 0.085), (0.75, 0.075), (0.80, 0.09), (0.90, 0.09),
                                     (0.92, 0.065)], "negro", lados=12)
    cu.perfil((0, -1.50, zc), "-Y", [(0, 0.06), (0.02, 0.12), (0.07, 0.12), (0.10, 0.075)], "cromo", lados=12)
    lu.cilindro((0, -1.59, zc), 0.07, 0.02, "neon", lados=12, eje="-Y")  # disco del emisor
    # tres hojas de guía (en Y) a lo largo del cañón, sujetas solo por detrás (encajadas en la cabeza)
    for k in range(3):
        a = math.tau * k / 3 + math.pi / 2
        d = Vector((math.cos(a), 0, math.sin(a)))
        t = Vector((0, 1, 0)).cross(d)
        anillos_h = []
        for y, r0, r1 in ((-0.58, 0.10, 0.17), (-0.80, 0.085, 0.13), (-1.05, 0.08, 0.10)):
            p0, p1 = Vector((0, y, zc)) + d * r0, Vector((0, y, zc)) + d * r1
            anillos_h.append([p0 + t * 0.018, p1 + t * 0.012, p1 - t * 0.012, p0 - t * 0.018])
        cu.loft(anillos_h, "grafito")

    # --- Los tres anillos flotantes (piezas aparte, para que el juego los haga girar) -----------------------------
    centros_anillos = {}
    for i, (y, R) in enumerate(((-0.92, 0.27), (-1.15, 0.235), (-1.37, 0.20))):
        an = piezas_anillo[i]
        n = 20
        # anillo de sección rectangular redondeada: pared de verdad (tubo hueco corto) con un bisel por loft
        # sección octogonal (rectángulo con chaflanes) barrida alrededor del eje: un toro cerrado
        perfil_an = ((0.03, R - 0.015), (0.045, R + 0.01), (0.045, R + 0.04), (-0.045, R + 0.04),
                     (-0.045, R + 0.01), (-0.03, R - 0.015))
        secciones = [[Vector((0, y + dy, zc)) + Vector((math.cos(a) * r, 0, math.sin(a) * r))
                      for a in (math.tau * k / n for k in range(n))] for dy, r in perfil_an]
        an.loft(secciones + secciones[:1], "violeta" if i == 1 else "grafito", tapas=False)
        # 3 bloques de cromo en el canto exterior (para que se note el giro)
        for k in range(3):
            a = math.tau * k / 3 + i * 0.6
            d = Vector((math.cos(a), 0, math.sin(a)))
            an.caja(Vector((0, y, zc)) + d * (R + 0.055), (0.05, 0.10, 0.04), "cromo",
                    giro=Matrix.Rotation(-a, 3, "Y"))
        # luz: aro fino en la cara de delante y en la de atrás
        luces_an[i].toro(Vector((0, y - 0.047, zc)), "Y", R + 0.025, 0.01, "neon", n_mayor=20, n_menor=4)
        centros_anillos[f"VIP_Anillo{i + 1}"] = Vector((0, y, zc))

    # --- Empuñadura ergonómica (loft inclinado), con placa blanca y línea de luz ------------------------------------
    inc = Matrix.Rotation(0.28, 3, "X")
    base_e = Vector((0, 0.36, 0.55))

    def e(p):
        return base_e + inc @ Vector(p)

    secs = [(0.08, 0.30, 0.36), (-0.10, 0.28, 0.34), (-0.30, 0.27, 0.31), (-0.48, 0.28, 0.33),
            (-0.66, 0.29, 0.36), (-0.80, 0.30, 0.38), (-0.84, 0.26, 0.32)]
    cu.loft([[e((p.x, p.y, d)) for p in circulo(prof / 2, 16, rx=ancho / 2, cuadratura=2.6)]
             for d, ancho, prof in secs], "negro")
    # placa trasera (lomo) de grafito y tope de cromo
    cu.loft([[e((p.x, p.y + prof / 2 + 0.005, d)) for p in circulo(0.035, 8, rx=ancho / 2 - 0.03,
                                                                   cuadratura=2.6)]
             for d, ancho, prof in secs[1:-1]], "grafito")
    cu.cilindro(e((0, 0, -0.84)), 0.12, -0.05, "cromo", lados=12, eje=inc @ Vector((0, 0, 1)))
    for s_ in (-1, 1):
        cu.loft([[e((s_ * (ancho / 2 - 0.01 + 0.03 * (k in (1, 2))), (k in (0, 1)) * 0.10 - 0.02, d))
                  for k in range(4)] for d, ancho in ((-0.18, 0.27), (-0.62, 0.285))], "blanco")
    # línea de luz delante de la empuñadura (donde van los dedos)
    lu.tubo([e((0, -0.15, -0.12)), e((0, -0.165, -0.40)), e((0, -0.17, -0.70))], 0.016, "neon", lados=4)
    # guardamonte integrado y gatillo
    cu.tubo([(0, 0.24, 0.30), (0, 0.10, 0.17), (0, -0.10, 0.18), (0, -0.26, 0.32), (0, -0.30, 0.51)], 0.03,
            "grafito", lados=6)
    cu.tubo([(0, 0.08, 0.52), (0, 0.02, 0.42), (0, 0.06, 0.31)], 0.028, "cromo", lados=6,
            radios=[0.03, 0.026, 0.02])

    boca_pos = Vector((0, -1.62, zc))
    piezas = {"VIP_Cuerpo": cu, "VIP_Nucleo": nu, "VIP_Luces": lu}
    for i in range(3):
        piezas[piezas_anillo[i].nombre] = piezas_anillo[i]
        piezas[luces_an[i].nombre] = luces_an[i]
    puntos = {"Nucleo": cnu.copy()}  # centro del núcleo: aquí va el fogonazo y la luz
    return piezas, boca_pos, ["VIP_Cuerpo", "VIP_Anillo1", "VIP_Anillo2", "VIP_Anillo3"], centros_anillos, puntos


# --------------------------------------------------------------------------------------------------------------
# Atlas: las piezas con textura se unen, se despliegan y se hornean juntas; luego se vuelven a separar
# --------------------------------------------------------------------------------------------------------------


def _hornear_canal(ob, img, canal):
    """Hornea un canal del Principled (Base Color, Metallic, Roughness) con el truco de la emisión."""
    scn = bpy.context.scene
    restaurar = []
    for slot in ob.material_slots:
        nt = slot.material.node_tree
        b = nt.nodes["Principled BSDF"]
        out = nt.nodes["Material Output"]
        prev = out.inputs["Surface"].links[0].from_socket
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Strength"].default_value = 1.0
        entrada = b.inputs[canal]
        if entrada.is_linked:
            nt.links.new(entrada.links[0].from_socket, em.inputs["Color"])
        else:
            v = entrada.default_value
            em.inputs["Color"].default_value = tuple(v) if canal == "Base Color" else (v, v, v, 1)
        nt.links.new(em.outputs[0], out.inputs["Surface"])
        n = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "destino"
        n.image = img
        nt.nodes.active = n
        restaurar.append((nt, prev, em, out))
    bpy.ops.object.bake(type="EMIT", margin=6)
    for nt, prev, em, out in restaurar:
        nt.links.new(prev, out.inputs["Surface"])
        nt.nodes.remove(em)


def hornear_atlas(objetos, nombre, carpeta, tam, rapido):
    """Une `objetos`, despliega UV y hornea color+AO, normales, metal y rugosidad. Devuelve los objetos separados."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 8 if rapido else 32
    nombres = [o.name for o in objetos]
    for i, o in enumerate(objetos):
        at = o.data.attributes.new("parte", "INT", "FACE")
        at.data.foreach_set("value", [i] * len(o.data.polygons))
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.object.join()
    ob = bpy.context.active_object
    ob.name = nombre + "_atlas"
    # UV: proyección inteligente y empaquetado con la misma densidad en todas las piezas
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.004, scale_to_bounds=False)
    bpy.ops.uv.average_islands_scale()
    bpy.ops.uv.pack_islands(margin=0.004, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")

    t = 256 if rapido else tam
    os.makedirs(os.path.join(carpeta, "texturas"), exist_ok=True)

    def imagen(sufijo, color):
        img = bpy.data.images.new(f"{nombre}_{sufijo}", t, t, alpha=False, float_buffer=False)
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return img

    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    # ocultar el resto al hornear (la oclusión solo entre piezas del atlas y sus vecinas de la misma pistola)
    img_c, img_m, img_r = imagen("color", True), imagen("metal", False), imagen("rugosidad", False)
    _hornear_canal(ob, img_c, "Base Color")
    _hornear_canal(ob, img_m, "Metallic")
    _hornear_canal(ob, img_r, "Roughness")
    img_ao = imagen("ao", False)
    for slot in ob.material_slots:
        nt = slot.material.node_tree
        n = nt.nodes["destino"]
        n.image = img_ao
        nt.nodes.active = n
    scn.world.light_settings.distance = 0.25
    bpy.ops.object.bake(type="AO", margin=6)
    c._multiplicar_ao(img_c, img_ao, fuerza=0.7)
    img_n = imagen("normal", False)
    for slot in ob.material_slots:
        nt = slot.material.node_tree
        n = nt.nodes["destino"]
        n.image = img_n
        nt.nodes.active = n
    bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", margin=6)

    rutas = {}
    for img, suf in ((img_c, "color"), (img_n, "normal"), (img_m, "metal"), (img_r, "rugosidad")):
        ruta = os.path.join(carpeta, "texturas", f"{nombre}_{suf}.png")
        img.filepath_raw = ruta
        img.file_format = "PNG"
        img.save()
        rutas[suf] = ruta

    # material final (lo que verá Roblox con una SurfaceAppearance)
    mat = bpy.data.materials.new(f"{nombre}_atlas")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    for img, entrada in ((img_c, "Base Color"), (img_m, "Metallic"), (img_r, "Roughness")):
        tx = nt.nodes.new("ShaderNodeTexImage")
        tx.image = img
        nt.links.new(tx.outputs["Color"], b.inputs[entrada])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img_n
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    ob.data.materials.clear()
    ob.data.materials.append(mat)

    # separar otra vez por pieza
    partes = [0] * len(ob.data.polygons)
    ob.data.attributes["parte"].data.foreach_get("value", partes)
    separados = []
    for i, n in enumerate(nombres):
        me = ob.data.copy()
        bm = bmesh.new()
        bm.from_mesh(me)
        capa = bm.faces.layers.int.get("parte")
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f[capa] != i], context="FACES")
        bm.to_mesh(me)
        bm.free()
        me.attributes.remove(me.attributes["parte"])
        nuevo = bpy.data.objects.new(n, me)
        me.name = n
        bpy.context.scene.collection.objects.link(nuevo)
        separados.append(nuevo)
    bpy.data.objects.remove(ob)
    return separados, rutas


# --------------------------------------------------------------------------------------------------------------
# Comprobaciones: aristas abiertas (láminas), normales hacia fuera, triángulos
# --------------------------------------------------------------------------------------------------------------


def revisar(ob):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    abiertas = sum(1 for e in bm.edges if len(e.link_faces) < 2)
    vol = bm.calc_volume(signed=True)
    tris = sum(len(f.verts) - 2 for f in bm.faces)
    bm.free()
    return {"triangulos": tris, "aristas_abiertas": abiertas, "volumen": round(vol, 4)}


# --------------------------------------------------------------------------------------------------------------
# Muñeco R6 para la vista «en la mano»
# --------------------------------------------------------------------------------------------------------------


def munieco_r6(desplazamiento=Vector((0, 0, 0))):
    """R6 de cajas (Torso 2x2x1, brazos y piernas 1x2x1, cabeza) con el brazo derecho levantado al frente
    (la pose de sostener una herramienta). Devuelve (objetos, punto de RightGripAttachment)."""
    mat = c.material("r6_gris", c.srgb("#A3A9B4"), rugosidad=0.6)
    mat_c = c.material("r6_cabeza", c.srgb("#F2C79E"), rugosidad=0.6)
    obs = []

    def caja(nombre, centro, tam, m, giro=None, bisel=0.06):
        bm = bmesh.new()
        r = bmesh.ops.create_cube(bm, size=1.0)
        mt = Matrix.Diagonal((*tam, 1))
        if giro is not None:
            mt = giro.to_4x4() @ mt
        bmesh.ops.transform(bm, matrix=Matrix.Translation(Vector(centro) + desplazamiento) @ mt, verts=r["verts"])
        bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bisel, segments=2, affect="EDGES")
        me = bpy.data.meshes.new(nombre)
        bm.to_mesh(me)
        bm.free()
        for p in me.polygons:
            p.use_smooth = True
        o = bpy.data.objects.new(nombre, me)
        bpy.context.scene.collection.objects.link(o)
        me.materials.append(m)
        obs.append(o)
        return o

    zt = 3.0  # centro del torso (piernas de 0 a 2)
    caja("R6_Torso", (0, 0, zt), (2, 1, 2), mat)
    caja("R6_Cabeza", (0, 0, zt + 1.6), (1.2, 1.2, 1.2), mat_c, bisel=0.25)
    # mirando hacia -Y, la derecha del muñeco es -X
    caja("R6_BrazoIzq", (1.5, 0, zt), (1, 1, 2), mat)
    caja("R6_PiernaIzq", (0.5, 0, 1), (1, 1, 2), mat)
    caja("R6_PiernaDer", (-0.5, 0, 1), (1, 1, 2), mat)
    # brazo derecho levantado 90° al frente: largo en -Y, desde el hombro
    caja("R6_BrazoDer", (-1.5, -0.5, zt + 0.5), (1, 2, 1), mat)
    agarre = Vector((-1.5, -1.5, zt + 0.5)) + desplazamiento  # centro de la cara del extremo = RightGripAttachment
    return obs, agarre


# --------------------------------------------------------------------------------------------------------------
# Construcción completa de una pistola
# --------------------------------------------------------------------------------------------------------------


def preparar(nombre, construir, carpeta, rapido):
    piezas, boca, con_textura, pivotes, puntos = construir()
    objetos = {n: p.objeto() for n, p in piezas.items()}
    for n in con_textura:
        c.sombreado_suave(objetos[n], angulo=38)
    for n, o in objetos.items():
        if n not in con_textura:
            c.sombreado_suave(o, angulo=50)
    texturizados, rutas = hornear_atlas([objetos[n] for n in con_textura], nombre, carpeta, TAM_ATLAS, rapido)
    for o in texturizados:
        objetos[o.name] = o
    # Agarre: delante del eje de la empuñadura (allí cae la cara del extremo del brazo R6), a la altura de la mano
    cuerpo = objetos[con_textura[0]]
    mn, mx = c.caja_limite([cuerpo])
    agarre = Vector((0, 0.12, 0.05)) if nombre == "Chatarra" else Vector((0, 0.16, 0.05))
    vacios = {}
    for n, p in (("Boca", boca), ("Agarre", agarre), *puntos.items()):
        e = bpy.data.objects.new(n, None)
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 0.3
        e.location = p
        bpy.context.scene.collection.objects.link(e)
        vacios[n] = e
    return objetos, vacios, rutas, pivotes


def a_roblox(v):
    """
    Blender -> marco del modelo en Roblox, con el cañón hacia -Z (delante) y la derecha en +X: (-x, z, y).
    El FBX en sí llega como (x, z, -y), es decir, girado 180° sobre Y respecto a este marco: es el giro que corrige
    GIRO_IMPORTACION en el script de montaje.
    """
    return [round(-v.x + 0.0, 4), round(v.z, 4), round(v.y + 0.0, 4)]


def datos_pistola(nombre, objetos, vacios, pivotes, cuerpo):
    d = {"cuerpo": cuerpo, "piezas": {}, "anclajes": {}, "pivotes_giro": {}}
    for n, o in objetos.items():
        mn, mx = c.caja_limite([o])
        r = revisar(o)
        d["piezas"][n] = {"centro": a_roblox((mn + mx) / 2), "tamano": [round(v, 3) for v in
                                                                        (mx.x - mn.x, mx.z - mn.z, mx.y - mn.y)],
                          **r}
    for n, e in vacios.items():
        d["anclajes"][n] = a_roblox(e.location)
    for n, p in pivotes.items():
        d["pivotes_giro"][n] = a_roblox(p)
    d["triangulos_total"] = sum(p["triangulos"] for p in d["piezas"].values())
    return d


def exportar(ruta, objetos, vacios):
    bpy.ops.object.select_all(action="DESELECT")
    for o in list(objetos) + list(vacios):
        o.hide_set(False)
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH", "EMPTY"}, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=True, axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False, bake_anim=False,
        embed_textures=True, path_mode="COPY")
    print("[ok] FBX:", ruta)


# --------------------------------------------------------------------------------------------------------------
# Script de montaje para la barra de comandos de Studio (con los números de este modelo)
# --------------------------------------------------------------------------------------------------------------

# Eje sobre el que gira cada pieza móvil, en coordenadas de Roblox: la rueda sobre X, los anillos sobre el cañón (Z).
EJES_GIRO = {"Chatarra_Rueda": "X", "Chatarra_DepositoMarco": "Y", "VIP_Anillo1": "Z", "VIP_Anillo2": "Z",
             "VIP_Anillo3": "Z"}
# Piezas que van soldadas a otra que gira (en lugar de al Handle)
SOLDAR_A = {"Chatarra_Deposito": "Chatarra_DepositoMarco", "Chatarra_Combustible": "Chatarra_DepositoMarco",
            "VIP_Anillo1_Luz": "VIP_Anillo1", "VIP_Anillo2_Luz": "VIP_Anillo2", "VIP_Anillo3_Luz": "VIP_Anillo3"}


def _v3(v):
    return f"Vector3.new({v[0]}, {v[1]}, {v[2]})"


def generar_montaje(ruta, nombre_tool, datos, con_textura):
    with open(os.path.join(AQUI, "plantilla_montar_pistola.luau"), encoding="utf-8") as f:
        plantilla = f.read()
    centros = "\n".join(f'\t["{n}"] = {_v3(p["centro"])},' for n, p in datos["piezas"].items())
    anclajes = "\n".join(f'\t{n} = {_v3(v)},' for n, v in datos["anclajes"].items())
    giros = "\n".join(f'\t["{n}"] = {{ pivote = {_v3(v)}, eje = "{EJES_GIRO[n]}" }},'
                      for n, v in datos["pivotes_giro"].items())
    neon = "\n".join(f'\t["{n}"] = Color3.fromHex("{h}"),' for n, h in datos["neon"].items())
    cristal = "\n".join(f'\t["{n}"] = {{ color = Color3.fromHex("{v["color"]}"), transparencia = {v["transparencia"]} }},'
                        for n, v in datos["cristal"].items())
    soldar = "\n".join(f'\t["{a}"] = "{b}",' for a, b in SOLDAR_A.items() if a in datos["piezas"])
    texturizadas = ", ".join(f'"{n}"' for n in con_textura)
    texto = (plantilla.replace("{{NOMBRE_TOOL}}", nombre_tool).replace("{{CUERPO}}", datos["cuerpo"])
             .replace("{{CENTROS}}", centros).replace("{{ANCLAJES}}", anclajes).replace("{{GIROS}}", giros)
             .replace("{{NEON}}", neon).replace("{{CRISTAL}}", cristal).replace("{{SOLDAR}}", soldar)
             .replace("{{TEXTURIZADAS}}", texturizadas))
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)
    print("[ok] montaje:", ruta)


# --------------------------------------------------------------------------------------------------------------
# Vistas y hojas
# --------------------------------------------------------------------------------------------------------------

VISTAS = [("Frente", 0, 6), ("Lado derecho", -90, 4), ("Lado izquierdo", 90, 4), ("Arriba", 0, 89),
          ("3/4 delantera", -42, 22), ("3/4 trasera", 145, 24)]


def mover(objs, d):
    for o in objs:
        o.location = o.location + d
    bpy.context.view_layer.update()


def renderizar_en_mano(objs_pistola, vacios, carpeta, prefijo, tam, muestras, az=-55, el=12, encuadre="cerca"):
    """Pone la pistola en la mano derecha de un muñeco R6 (Agarre = RightGripAttachment) y la fotografía."""
    munieco, punto = munieco_r6(Vector((0, 0, Z_SUELO)))
    d = punto - vacios["Agarre"].location
    mover(objs_pistola, d)
    todos = munieco + objs_pistola
    if encuadre == "cerca":
        centro = punto + Vector((0, -0.4, 0.2))
        vistas = [("En la mano (R6)", az, el)]
        r = c.renderizar_vistas(todos, carpeta, vistas, tam=tam, muestras=muestras, con_malla=False,
                                prefijo=prefijo, centro=centro, margen=0.55)
    else:
        vistas = [("En la mano (cuerpo entero)", az, el)]
        r = c.renderizar_vistas(todos, carpeta, vistas, tam=tam, muestras=muestras, con_malla=False,
                                prefijo=prefijo, margen=0.95)
    mover(objs_pistola, -d)
    for o in munieco:
        bpy.data.objects.remove(o)
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    sal = os.path.abspath(a.salida)
    tmp = os.path.join(sal, "_render_tmp")
    c.escena_vacia()
    c.preparar_estudio(mundo=0.9, luz_clave=850, z_suelo=Z_SUELO)
    # caja de luz cenital grande: da reflejos largos en el metal pulido (como el cielo en Roblox)
    caja_luz = bpy.data.lights.new("caja_cenital", "AREA")
    caja_luz.energy = 260
    caja_luz.size = 5.0
    caja_luz.color = (0.85, 0.9, 1.0)
    ob_luz = bpy.data.objects.new("caja_cenital", caja_luz)
    ob_luz.location = (0, 0, 4.5)
    bpy.context.scene.collection.objects.link(ob_luz)

    pistolas = {}
    for nombre, construir, carpeta in (("Chatarra", construir_chatarra, "chatarra"),
                                       ("VIP", construir_vip, "vip")):
        dest = os.path.join(sal, carpeta)
        os.makedirs(dest, exist_ok=True)
        objetos, vacios, rutas, pivotes = preparar(nombre, construir, dest, a.rapido)
        cuerpo = f"{nombre}_Cuerpo"
        datos = datos_pistola(nombre, objetos, vacios, pivotes, cuerpo)
        datos["texturas"] = {k: os.path.relpath(v, dest) for k, v in rutas.items()}
        datos["neon"] = {k: v for k, v in NEON.items() if k in objetos}
        datos["cristal"] = {k: {"color": v[0], "transparencia": v[1]} for k, v in CRISTAL.items() if k in objetos}
        orden = [objetos[cuerpo]] + [o for n, o in objetos.items() if n != cuerpo]
        exportar(os.path.join(dest, f"Pistola_{nombre}.fbx"), orden, list(vacios.values()))
        with open(os.path.join(dest, f"Pistola_{nombre}.json"), "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        generar_montaje(os.path.join(dest, f"montar_{carpeta}.luau"),
                        "PistolaPortales" if nombre == "Chatarra" else "PistolaPortalesVIP", datos,
                        [n for n in objetos if n in ("Chatarra_Cuerpo", "Chatarra_Rueda", "Chatarra_DepositoMarco",
                                                     "VIP_Cuerpo", "VIP_Anillo1", "VIP_Anillo2", "VIP_Anillo3")])
        print(f"[info] {nombre}: {datos['triangulos_total']} triángulos")
        for n, p in datos["piezas"].items():
            print(f"   {n}: {p}")
        pistolas[nombre] = (orden, vacios, datos)
        for o in orden:
            o.hide_render = True
        for n, e in vacios.items():  # que los Empty de la siguiente pistola se llamen «Boca» y «Agarre» sin .001
            e.name = f"{nombre}_{n}_exportado"

    tam = 300 if a.rapido else 460
    muestras = 16 if a.rapido else 64
    filas, etiquetas = [], []
    for nombre, (orden, vacios, datos) in pistolas.items():
        for o in orden:
            o.hide_render = False
        fila = c.renderizar_vistas(orden, tmp, VISTAS, tam=tam, muestras=muestras, prefijo=nombre, margen=1.0,
                                   lente=70)
        fila = fila[:-1] + renderizar_en_mano(orden, vacios, tmp, nombre, tam, muestras) + fila[-1:]
        filas.append(fila)
        mn, mx = c.caja_limite(orden)
        dim = mx - mn
        etiquetas.append(f"{'Normal (chatarra)' if nombre == 'Chatarra' else 'VIP'}\nPistola_{nombre}.fbx\n"
                         f"{datos['triangulos_total']} triángulos\n{dim.x:.2f}×{dim.y:.2f}×{dim.z:.2f} st\n"
                         f"atlas {TAM_ATLAS}")
        for o in orden:
            o.hide_render = True
    hoja = os.path.join(sal, f"hoja_contactos_{a.ronda}.png")
    c.montar_hoja(filas, hoja, f"Pistolas de portales — ronda {a.ronda}",
                  notas=["Arriba la normal (hecha con chatarra, gasta combustible); abajo la VIP (gamepass). "
                         "Tamaño real en studs; brazo R6 = 1×2×1."],
                  etiquetas_fila=etiquetas)

    # Comparación: las dos juntas en la misma foto (de lado y en 3/4) y dos muñecos R6, cada uno con la suya
    ch, vip = pistolas["Chatarra"][0], pistolas["VIP"][0]
    for o in ch + vip:
        o.hide_render = False
    comp = []
    for nombre_v, az, el, dch, dvip in (("Las dos, de lado", 90, 5, Vector((0, -1.55, 0)), Vector((0, 1.55, 0))),
                                        ("Las dos, 3/4", -35, 20, Vector((-0.8, 0, 0)), Vector((0.8, 0, 0)))):
        mover(ch, dch)
        mover(vip, dvip)
        comp += c.renderizar_vistas(ch + vip, tmp, [(nombre_v, az, el)], tam=tam + 200, muestras=muestras,
                                    con_malla=False, prefijo="comp", lente=60, margen=1.0)
        mover(ch, -dch)
        mover(vip, -dvip)
    # dos muñecos
    obs_m = []
    for nombre, dx in (("Chatarra", -2.1), ("VIP", 2.1)):
        orden, vacios, _ = pistolas[nombre]
        m, punto = munieco_r6(Vector((dx, 0, Z_SUELO)))
        obs_m += m
        mover(orden, punto - vacios["Agarre"].location)
    comp += c.renderizar_vistas(obs_m + ch + vip, tmp, [("Dos R6, cada uno con la suya", -28, 10)], tam=tam + 200,
                                muestras=muestras, con_malla=False, prefijo="comp", lente=50, margen=0.9)
    comp_hoja = os.path.join(sal, f"comparacion_{a.ronda}.png")
    c.montar_hoja([comp], comp_hoja, f"Normal frente a VIP — ronda {a.ronda}", columnas=3,
                  notas=["Misma luz y misma escala. La normal (chatarra) a la izquierda, la VIP a la derecha."])
    print("[ok] listo")


if __name__ == "__main__":
    main()
