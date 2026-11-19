"""
Kit del Planeta Humano: todo lo que comparten los modelos (geometría, materiales, horneado, render, exportación).

Reglas (las del encargo):
  * 1 unidad de Blender = 1 stud. El modelo se escribe en studs, con el suelo en z = 0 y centrado en x/y.
  * Delante del modelo = -Y en Blender. Antes de exportar se gira 180° sobre el eje vertical (GIRO_IMPORTACION,
    el eje Y de Roblox) y se exporta con los ejes por defecto del FBX (-Z delante, Y arriba): en Studio mira a -Z.
  * Todo es geometría cerrada con grosor y normales hacia fuera. Nada de planos con textura pegada.
  * Las piezas con textura comparten UN atlas de 2048 × 2048 horneado: color, normales, rugosidad y metal
    (y emisión si alguna pieza con textura brilla). Lo que brilla va en mallas aparte con sufijo _neon
    (Material Neon en Roblox) y lo transparente en mallas _cristal (Material Glass).
  * Cada modelo: escena limpia (read_factory_settings), modelado desde cero, UV, horneado, turnaround de 8 vistas,
    FBX, JSON y verificación reimportando el FBX.

Uso:
    m = Modelo("tienda_armas", zona="comercial", tam=(12, 10, 8), presupuesto=14000)
    cuerpo = m.parte("tienda_armas")                       # la pieza principal (con textura)
    neon = m.parte("tienda_armas_cartel_neon", tipo="neon", color=NEON)
    cuerpo.caja((0, 0, 1), (4, 2, 2), m.mat("pintura", "#2F3B4A"), b=0.05)
    m.terminar()
"""

import json
import math
import os
import random
import shutil
import tempfile
import time
import zlib
from contextlib import contextmanager

import bpy  # bpy antes que bmesh
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector
from PIL import Image, ImageDraw, ImageFont

V = Vector
GIRO_IMPORTACION = math.pi  # 180° sobre el eje vertical (Y de Roblox) antes de exportar
NEON = "#3DF2FF"  # cyan humano estándar
# 1 unidad = 1 stud. El FBX declara además que su unidad mide 0,28 m (lo que mide un stud en Roblox): así llega con su
# tamaño tanto si el importador lee la unidad del archivo como si toma las coordenadas tal cual.
METROS_POR_STUD = 0.28
NEON_CLINICA = "#FFFFFF"
TAM_ATLAS = 2048

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
FUENTES = {
    "negrita": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "normal": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "estrecha": "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "serif": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "mano": "/usr/share/fonts/truetype/freefont/FreeSerifBoldItalic.ttf",
    "mono": "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf",
}


def hex_lineal(h):
    h = h.lstrip("#")
    c = [int(h[i: i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def rot_m(rot):
    """rot: grados (x, y, z) -> Matrix 4x4."""
    if rot is None:
        return Matrix.Identity(4)
    if isinstance(rot, Matrix):
        return rot.to_4x4()
    return Euler([math.radians(a) for a in rot], "XYZ").to_matrix().to_4x4()


def base_eje(d):
    """Matriz 3x3 cuyo eje Z apunta en la dirección d."""
    d = V(d).normalized()
    ref = V((0, 0, 1)) if abs(d.z) < 0.95 else V((1, 0, 0))
    x = ref.cross(d).normalized()
    y = d.cross(x).normalized()
    return Matrix((x, y, d)).transposed()


# ==============================================================================================================
# Materiales procedurales (se hornean al atlas)
# ==============================================================================================================

# Parámetros por tipo. Cada material los copia y los pisa con lo que se le pase.
TIPOS = {
    # metal pintado: la pintura se pela en los cantos y deja ver el metal
    "pintura": dict(rug=0.55, met=0.0, desgaste=0.55, c_desgaste="#9A9EA4", suciedad=0.55, aranazos=0.35,
                    bump=0.25, ruido=0.07, patron=None, lluvia=0.35),
    "metal": dict(rug=0.42, met=1.0, desgaste=0.0, suciedad=0.45, aranazos=0.55, bump=0.25, ruido=0.08),
    "cromo": dict(rug=0.16, met=1.0, desgaste=0.0, suciedad=0.15, aranazos=0.25, bump=0.08, ruido=0.03),
    "oxido": dict(rug=0.88, met=0.25, desgaste=0.0, suciedad=0.6, aranazos=0.0, bump=0.8, ruido=0.25,
                  patron="oxido"),
    "madera": dict(rug=0.78, met=0.0, desgaste=0.25, c_desgaste="#C9A57A", suciedad=0.55, lluvia=0.55, aranazos=0.15,
                   bump=0.6, ruido=0.1, patron="vetas", eje="X"),
    "piedra": dict(rug=0.88, met=0.0, desgaste=0.3, c_desgaste="#B8B2A6", suciedad=0.6, lluvia=0.35, bump=1.0,
                   ruido=0.16, patron="piedra"),
    "hormigon": dict(rug=0.92, met=0.0, desgaste=0.25, c_desgaste="#C4C0B8", suciedad=0.6, lluvia=0.3, bump=0.5,
                     ruido=0.1, patron="poros"),
    "ladrillo": dict(rug=0.9, met=0.0, suciedad=0.6, bump=1.0, ruido=0.14, patron="ladrillo", c2="#6B6460",
                     tam_ladrillo=(0.5, 0.25)),
    "goma": dict(rug=0.92, met=0.0, suciedad=0.35, bump=0.3, ruido=0.05, patron="poros"),
    "plastico": dict(rug=0.42, met=0.0, desgaste=0.15, c_desgaste="#D8D8D8", suciedad=0.35, aranazos=0.2, bump=0.1,
                     ruido=0.04),
    "tela": dict(rug=0.95, met=0.0, suciedad=0.45, lluvia=0.2, bump=0.35, ruido=0.1, patron="tejido"),
    "cuero": dict(rug=0.62, met=0.0, desgaste=0.3, c_desgaste="#8A6A4E", suciedad=0.4, bump=0.35, ruido=0.12,
                  patron="poros"),
    "grip": dict(rug=0.45, met=1.0, suciedad=0.6, aranazos=0.3, bump=1.0, ruido=0.08, patron="diamante"),
    "paneles": dict(rug=0.5, met=0.0, desgaste=0.45, c_desgaste="#A3A7AD", suciedad=0.55, aranazos=0.35, bump=0.35,
                    ruido=0.06, patron="paneles", tam_panel=(2.0, 1.5), lluvia=0.4),
    "organico": dict(rug=0.38, met=0.0, suciedad=0.0, bump=0.15, ruido=0.12, patron="poros"),
    "liquido": dict(rug=0.08, met=0.0, suciedad=0.0, bump=0.05, ruido=0.04),
    "tiza": dict(rug=1.0, met=0.0, suciedad=0.0, bump=0.1, ruido=0.18, patron="poros"),
    "ceramica": dict(rug=0.3, met=0.0, desgaste=0.2, c_desgaste="#E8E2D6", suciedad=0.3, bump=0.1, ruido=0.04),
    "papel": dict(rug=0.9, met=0.0, suciedad=0.3, bump=0.1, ruido=0.06),
    "pizarra": dict(rug=0.95, met=0.0, suciedad=0.2, bump=0.15, ruido=0.08, patron="poros"),
    "lisa": dict(rug=0.5, met=0.0, suciedad=0.0, bump=0.0, ruido=0.0),
}


class _NB:
    """Ayuda para montar árboles de nodos sin pelearse con los índices."""

    def __init__(self, nt):
        self.nt = nt

    def n(self, tipo, **props):
        nodo = self.nt.nodes.new(tipo)
        for k, v in props.items():
            setattr(nodo, k, v)
        return nodo

    def con(self, a, b):
        if isinstance(a, (int, float)):
            b.default_value = a
        elif isinstance(a, (tuple, list)):
            b.default_value = a
        else:
            self.nt.links.new(a, b)

    def m(self, op, a, b=0.0, c=None, clamp=False):
        n = self.n("ShaderNodeMath", operation=op, use_clamp=clamp)
        self.con(a, n.inputs[0])
        self.con(b, n.inputs[1])
        if c is not None:
            self.con(c, n.inputs[2])
        return n.outputs[0]

    def rango(self, x, a, b, c=0.0, d=1.0):
        n = self.n("ShaderNodeMapRange", clamp=True)
        self.con(x, n.inputs["Value"])
        n.inputs["From Min"].default_value = a
        n.inputs["From Max"].default_value = b
        n.inputs["To Min"].default_value = c
        n.inputs["To Max"].default_value = d
        return n.outputs["Result"]

    def mezcla(self, f, a, b, modo="MIX"):
        n = self.n("ShaderNodeMix", data_type="RGBA", blend_type=modo)
        self.con(f, n.inputs[0])
        self.con(a, n.inputs[6])
        self.con(b, n.inputs[7])
        return n.outputs[2]

    def lerp(self, f, a, b):
        n = self.n("ShaderNodeMix", data_type="FLOAT")
        self.con(f, n.inputs[0])
        self.con(a, n.inputs[2])
        self.con(b, n.inputs[3])
        return n.outputs[0]

    def ruido(self, vec, escala, detalle=3.0, rug=0.55, dist=0.0, escala_vec=None):
        if escala_vec is not None:
            vm = self.n("ShaderNodeVectorMath", operation="MULTIPLY")
            self.con(vec, vm.inputs[0])
            vm.inputs[1].default_value = escala_vec
            vec = vm.outputs[0]
        n = self.n("ShaderNodeTexNoise")
        self.con(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = escala
        n.inputs["Detail"].default_value = detalle
        n.inputs["Roughness"].default_value = rug
        n.inputs["Distortion"].default_value = dist
        return n.outputs["Fac"]

    def vmul(self, vec, k):
        vm = self.n("ShaderNodeVectorMath", operation="MULTIPLY")
        self.con(vec, vm.inputs[0])
        vm.inputs[1].default_value = k
        return vm.outputs[0]

    def vsum(self, vec, k):
        vm = self.n("ShaderNodeVectorMath", operation="ADD")
        self.con(vec, vm.inputs[0])
        vm.inputs[1].default_value = k
        return vm.outputs[0]


def _vector_triplanar(nb, pos, nrm):
    """Coordenadas 2D según la cara: muros de X usan (y, z), muros de Y usan (x, z), techos y suelos (x, y).
    Se devuelve un vector (u, v, w) para texturas 2D (ladrillo, paneles)."""
    sp = nb.n("ShaderNodeSeparateXYZ")
    nb.con(pos, sp.inputs[0])
    sn = nb.n("ShaderNodeSeparateXYZ")
    nb.con(nrm, sn.inputs[0])
    ax = nb.m("ABSOLUTE", sn.outputs[0])
    az = nb.m("ABSOLUTE", sn.outputs[2])
    es_x = nb.m("GREATER_THAN", ax, 0.6)
    es_z = nb.m("GREATER_THAN", az, 0.6)
    # u: x o y; v: z o y
    u = nb.lerp(es_x, sp.outputs[0], sp.outputs[1])
    v = nb.lerp(es_z, sp.outputs[2], sp.outputs[1])
    cb = nb.n("ShaderNodeCombineXYZ")
    nb.con(u, cb.inputs[0])
    nb.con(v, cb.inputs[1])
    nb.con(sp.outputs[2], cb.inputs[2])
    return cb.outputs[0]


def crear_material(nombre, tipo, color, p):
    """Material Principled con desgaste procedural. Expone tres nodos con nombre para el horneado:
    canal_color (RGBA), canal_rug (valor) y canal_met (valor)."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    nb = _NB(nt)
    out = nb.n("ShaderNodeOutputMaterial")
    bsdf = nb.n("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    geo = nb.n("ShaderNodeNewGeometry")
    tc = nb.n("ShaderNodeTexCoord")
    pos = tc.outputs["Object"]
    nrm = geo.outputs["Normal"]
    sem = p.get("semilla", 0.0)
    if sem:
        pos = nb.vsum(pos, (sem * 13.1, sem * 7.7, sem * 3.3))
    sn = nb.n("ShaderNodeSeparateXYZ")
    nb.con(geo.outputs["Position"], sn.inputs[0])
    z = sn.outputs[2]
    snn = nb.n("ShaderNodeSeparateXYZ")
    nb.con(nrm, snn.inputs[0])
    nz = snn.outputs[2]

    base = hex_lineal(color)
    c_base = (*base, 1.0)
    altura = None  # señal de relieve que se va sumando
    rug = p["rug"]
    met = p["met"]

    def sumar_altura(s, k):
        nonlocal altura
        t = nb.m("MULTIPLY", s, k)
        altura = t if altura is None else nb.m("ADD", altura, t)

    # --- variación de color y patrón ----------------------------------------------------------------------
    rv = nb.ruido(pos, 1.6 * p.get("escala", 1.0), 4.0, 0.6)
    var = nb.rango(rv, 0.25, 0.75, 1.0 - p["ruido"], 1.0 + p["ruido"])
    # var va de 1-r a 1+r: multiplica el color base
    mulc = nb.n("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY")
    mulc.inputs[0].default_value = 1.0
    nb.con(c_base, mulc.inputs[6])
    cv = nb.n("ShaderNodeCombineColor")
    for i in range(3):
        nb.con(var, cv.inputs[i])
    nb.con(cv.outputs[0], mulc.inputs[7])
    col = mulc.outputs[2]
    rug_s = nb.rango(rv, 0.3, 0.7, rug - 0.08, rug + 0.08)
    met_s = met

    patron = p.get("patron")
    if patron == "vetas":
        eje = p.get("eje", "X")
        k = {"X": (0.6, 6.0, 6.0), "Y": (6.0, 0.6, 6.0), "Z": (6.0, 6.0, 0.6)}[eje]
        w = nb.n("ShaderNodeTexWave", wave_type="RINGS")
        nb.con(nb.vmul(pos, k), w.inputs["Vector"])
        w.inputs["Scale"].default_value = 1.4
        w.inputs["Distortion"].default_value = 6.0
        w.inputs["Detail"].default_value = 3.0
        vet = w.outputs["Fac"]
        oscuro = tuple(x * 0.62 for x in base) + (1.0,)
        col = nb.mezcla(nb.rango(vet, 0.2, 0.9, 0, 0.7), col, oscuro)
        sumar_altura(vet, 0.15)
        # nudos
        nud = nb.ruido(nb.vmul(pos, k), 0.9, 2.0, 0.5)
        nm = nb.rango(nud, 0.68, 0.74)
        col = nb.mezcla(nm, col, tuple(x * 0.4 for x in base) + (1.0,))
        # grietas finas a lo largo de la veta
        gr = nb.ruido(nb.vmul(pos, k), 3.0, 1.0, 0.5)
        sumar_altura(nb.rango(gr, 0.49, 0.51, 0, 1), -0.25)
    elif patron == "ladrillo":
        tl = p.get("tam_ladrillo", (0.5, 0.25))
        uv = _vector_triplanar(nb, pos, nrm)
        br = nb.n("ShaderNodeTexBrick", offset=0.5, offset_frequency=2)
        nb.con(uv, br.inputs["Vector"])
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = tl[0]
        br.inputs["Row Height"].default_value = tl[1]
        br.inputs["Mortar Size"].default_value = 0.025
        br.inputs["Mortar Smooth"].default_value = 0.2
        br.inputs["Bias"].default_value = 0.0
        br.inputs["Color1"].default_value = c_base
        br.inputs["Color2"].default_value = tuple(x * 0.75 for x in base) + (1.0,)
        br.inputs["Mortar"].default_value = (*hex_lineal(p.get("c2", "#6B6460")), 1.0)
        col = nb.mezcla(1.0, col, br.outputs["Color"], "MULTIPLY")
        col = nb.mezcla(br.outputs["Fac"], col, (*hex_lineal(p.get("c2", "#6B6460")), 1.0))
        sumar_altura(nb.m("SUBTRACT", 1.0, br.outputs["Fac"]), 0.6)
        rug_s = nb.lerp(br.outputs["Fac"], rug_s, 0.98)
    elif patron == "paneles":
        tp = p.get("tam_panel", (2.0, 1.5))
        uv = _vector_triplanar(nb, pos, nrm)
        br = nb.n("ShaderNodeTexBrick", offset=0.0, offset_frequency=1)
        nb.con(uv, br.inputs["Vector"])
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = tp[0]
        br.inputs["Row Height"].default_value = tp[1]
        br.inputs["Mortar Size"].default_value = 0.025
        br.inputs["Mortar Smooth"].default_value = 0.1
        br.inputs["Color1"].default_value = (1, 1, 1, 1)
        br.inputs["Color2"].default_value = (0.9, 0.9, 0.9, 1)
        br.inputs["Mortar"].default_value = (0.25, 0.25, 0.25, 1)
        col = nb.mezcla(1.0, col, br.outputs["Color"], "MULTIPLY")
        sumar_altura(nb.m("SUBTRACT", 1.0, br.outputs["Fac"]), 0.5)
    elif patron == "diamante":
        sp = nb.n("ShaderNodeSeparateXYZ")
        nb.con(_vector_triplanar(nb, pos, nrm), sp.inputs[0])
        f = 2 * math.pi / 0.35
        a = nb.m("SINE", nb.m("MULTIPLY", nb.m("ADD", sp.outputs[0], sp.outputs[1]), f))
        b = nb.m("SINE", nb.m("MULTIPLY", nb.m("SUBTRACT", sp.outputs[0], sp.outputs[1]), f))
        d1 = nb.rango(nb.m("MULTIPLY", a, b), 0.55, 0.8)
        sumar_altura(d1, 0.6)
        rug_s = nb.lerp(d1, rug_s, rug - 0.15)
    elif patron == "tejido":
        sp = nb.n("ShaderNodeSeparateXYZ")
        nb.con(pos, sp.inputs[0])
        f = 2 * math.pi / 0.08
        a = nb.m("SINE", nb.m("MULTIPLY", nb.m("ADD", sp.outputs[0], sp.outputs[1]), f))
        b = nb.m("SINE", nb.m("MULTIPLY", sp.outputs[2], f))
        sumar_altura(nb.m("ADD", a, b), 0.04)
        col = nb.mezcla(nb.rango(nb.m("MULTIPLY", a, b), -1, 1, 0, 0.12), col, (0, 0, 0, 1))
    elif patron == "piedra":
        vo = nb.n("ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE")
        nb.con(pos, vo.inputs["Vector"])
        vo.inputs["Scale"].default_value = 5.0 * p.get("escala", 1.0)
        grieta = nb.rango(vo.outputs["Distance"], 0.0, 0.025, 1, 0)
        col = nb.mezcla(nb.m("MULTIPLY", grieta, 0.35), col, (0.08, 0.075, 0.07, 1))
        sumar_altura(nb.ruido(pos, 6.0, 6.0, 0.65), 0.6)
        sumar_altura(grieta, -0.5)
    elif patron == "poros":
        sumar_altura(nb.ruido(pos, 22.0 * p.get("escala", 1.0), 3.0, 0.6), 0.25)
    elif patron == "oxido":
        man = nb.ruido(pos, 3.0, 5.0, 0.7)
        col = nb.mezcla(nb.rango(man, 0.45, 0.6), col, (*hex_lineal("#3A2418"), 1))
        sumar_altura(nb.ruido(pos, 14.0, 5.0, 0.7), 0.6)

    # --- abolladuras / ruido fino en el relieve --------------------------------------------------------------
    if p.get("abolladuras", 0) > 0:
        ab = nb.ruido(pos, 2.5, 2.0, 0.5)
        sumar_altura(nb.rango(ab, 0.55, 0.75), -p["abolladuras"])
    sumar_altura(nb.ruido(pos, 40.0, 2.0, 0.5), 0.04)

    # --- desgaste de cantos -----------------------------------------------------------------------------------
    if p.get("desgaste", 0) > 0:
        bev = nb.n("ShaderNodeBevel", samples=6)
        bev.inputs["Radius"].default_value = p.get("radio_canto", 0.05)
        dot = nb.n("ShaderNodeVectorMath", operation="DOT_PRODUCT")
        nb.con(bev.outputs["Normal"], dot.inputs[0])
        nb.con(nrm, dot.inputs[1])
        canto = nb.rango(dot.outputs["Value"], 0.995, 0.86, 0.0, 1.0)
        ruido_c = nb.ruido(pos, 9.0, 6.0, 0.7)
        pelado = nb.rango(nb.m("MULTIPLY", canto, nb.m("ADD", ruido_c, 0.25)), 0.55 - 0.3 * p["desgaste"], 0.62 - 0.3 * p["desgaste"])
        # desconchones sueltos también en la cara
        sueltos = nb.rango(nb.ruido(pos, 4.0, 8.0, 0.75), 0.74 - 0.06 * p["desgaste"], 0.76 - 0.06 * p["desgaste"])
        pelado = nb.m("MAXIMUM", pelado, nb.m("MULTIPLY", sueltos, p["desgaste"]))
        cd = hex_lineal(p.get("c_desgaste", "#9A9EA4"))
        col = nb.mezcla(pelado, col, (*cd, 1.0))
        if p.get("tipo") == "pintura" or p.get("tipo") == "paneles":
            met_s = nb.lerp(pelado, met, 1.0)
            rug_s = nb.lerp(pelado, rug_s, 0.38)
        sumar_altura(pelado, -0.35)

    # --- arañazos (más a la altura de la mano) ----------------------------------------------------------------
    if p.get("aranazos", 0) > 0:
        ar = nb.ruido(pos, 3.0, 2.0, 0.5, escala_vec=(1.0, 1.0, 40.0))
        ar2 = nb.ruido(pos, 3.0, 2.0, 0.5, escala_vec=(30.0, 1.0, 1.0))
        lin = nb.m("MAXIMUM", nb.rango(ar, 0.71, 0.73), nb.m("MULTIPLY", nb.rango(ar2, 0.72, 0.735), 0.6))
        banda = nb.m("ADD", nb.m("MULTIPLY", nb.rango(z, 1.6, 2.6), nb.rango(z, 4.5, 3.6)), 0.3)
        lin = nb.m("MULTIPLY", nb.m("MULTIPLY", lin, banda), p["aranazos"])
        clara = tuple(min(1.0, x * 1.6 + 0.08) for x in base) + (1.0,)
        col = nb.mezcla(lin, col, clara)
        rug_s = nb.lerp(lin, rug_s, max(0.1, rug - 0.25))
        sumar_altura(lin, -0.1)

    # --- suciedad: oclusión, suelo, lluvia -----------------------------------------------------------------
    suc = p.get("suciedad", 0)
    if suc > 0:
        ao = nb.n("ShaderNodeAmbientOcclusion", samples=8, only_local=False)
        ao.inputs["Distance"].default_value = p.get("dist_ao", 0.6)
        hueco = nb.m("SUBTRACT", 1.0, ao.outputs["AO"])
        rs = nb.ruido(pos, 2.5, 5.0, 0.7)
        suelo = nb.m("MULTIPLY", nb.rango(z, 1.4, 0.0), nb.rango(rs, 0.3, 0.7, 0.4, 1.0))
        f = nb.m("MAXIMUM", nb.m("MULTIPLY", hueco, 0.85), nb.m("MULTIPLY", suelo, 0.55))
        f = nb.m("MULTIPLY", f, suc)
        mugre = (*hex_lineal(p.get("c_suciedad", "#2B2620")), 1.0)
        col = nb.mezcla(f, col, mugre)
        rug_s = nb.lerp(f, rug_s, 0.95)
        if p.get("lluvia", 0) > 0:
            ll = nb.ruido(pos, 2.0, 3.0, 0.6, escala_vec=(5.0, 5.0, 0.25))
            vert = nb.m("SUBTRACT", 1.0, nb.m("ABSOLUTE", nz))
            arriba = nb.rango(nz, 0.5, 0.9)
            fl = nb.m("MAXIMUM", nb.m("MULTIPLY", nb.rango(ll, 0.45, 0.75), vert), nb.m("MULTIPLY", arriba, 0.6))
            fl = nb.m("MULTIPLY", fl, p["lluvia"] * 0.45)
            col = nb.mezcla(fl, col, (0, 0, 0, 1), "MIX")

    # --- hollín por altura (chimeneas): más negro hacia z_fin ---------------------------------------------------
    if p.get("hollin"):
        z0, z1 = p["hollin"]
        rh = nb.ruido(pos, 3.0, 5.0, 0.7, escala_vec=(3.0, 3.0, 0.5))
        fh = nb.m("MULTIPLY", nb.rango(z, z0, z1), nb.rango(rh, 0.2, 0.7, 0.55, 1.0))
        col = nb.mezcla(fh, col, (0.012, 0.011, 0.01, 1))
        rug_s = nb.lerp(fh, rug_s, 0.97)

    # --- manchas puntuales: aceite, combustible, quemado, óxido -------------------------------------------------
    for (cx, cy, cz, radio, chex, fuerza) in p.get("manchas", []):
        d = nb.n("ShaderNodeVectorMath", operation="DISTANCE")
        nb.con(pos, d.inputs[0])
        d.inputs[1].default_value = (cx, cy, cz)
        rn = nb.ruido(pos, 2.5, 4.0, 0.6)
        dd = nb.m("ADD", d.outputs["Value"], nb.m("MULTIPLY", nb.m("SUBTRACT", rn, 0.5), radio * 0.8))
        fm = nb.m("MULTIPLY", nb.rango(dd, radio, radio * 0.35), fuerza)
        col = nb.mezcla(fm, col, (*hex_lineal(chex), 1.0))
        if chex.lower() in ("#0d0b09", "#14110e", "#1a1612"):  # aceite: brilla
            rug_s = nb.lerp(fm, rug_s, 0.22)

    # --- salida ---------------------------------------------------------------------------------------------
    nc = nb.n("ShaderNodeMix", data_type="RGBA")
    nc.name = "canal_color"
    nc.inputs[0].default_value = 0.0
    nb.con(col, nc.inputs[6])
    nr = nb.n("ShaderNodeMath", operation="ADD", use_clamp=True)
    nr.name = "canal_rug"
    nb.con(rug_s, nr.inputs[0])
    nr.inputs[1].default_value = 0.0
    nmt = nb.n("ShaderNodeMath", operation="ADD", use_clamp=True)
    nmt.name = "canal_met"
    nb.con(met_s, nmt.inputs[0])
    nmt.inputs[1].default_value = 0.0
    nb.con(nc.outputs[2], bsdf.inputs["Base Color"])
    nb.con(nr.outputs[0], bsdf.inputs["Roughness"])
    nb.con(nmt.outputs[0], bsdf.inputs["Metallic"])
    if altura is not None and p.get("bump", 0) > 0:
        bump = nb.n("ShaderNodeBump")
        bump.inputs["Strength"].default_value = min(1.0, p["bump"])
        bump.inputs["Distance"].default_value = 0.02
        nb.con(altura, bump.inputs["Height"])
        nb.con(bump.outputs["Normal"], bsdf.inputs["Normal"])
    if p.get("emision"):
        ce = hex_lineal(p["emision"])
        bsdf.inputs["Emission Color"].default_value = (*ce, 1)
        bsdf.inputs["Emission Strength"].default_value = p.get("fuerza_emision", 3.0)
        nem = nb.n("ShaderNodeRGB")
        nem.name = "canal_emi"
        nem.outputs[0].default_value = (*ce, 1)
    mat.diffuse_color = (*base, 1.0)
    mat["tipo"] = p.get("tipo", "")
    return mat


def material_simple(nombre, color, emision=0.0, cristal=False, alfa=1.0):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    c = hex_lineal(color)
    b.inputs["Base Color"].default_value = (*c, 1)
    if emision:
        b.inputs["Emission Color"].default_value = (*c, 1)
        b.inputs["Emission Strength"].default_value = emision
        b.inputs["Roughness"].default_value = 0.4
    if cristal:
        b.inputs["Transmission Weight"].default_value = 1.0
        b.inputs["Roughness"].default_value = 0.04
        b.inputs["IOR"].default_value = 1.45
    if alfa < 1:
        b.inputs["Alpha"].default_value = alfa
    mat.diffuse_color = (*c, 1.0)
    return mat


# ==============================================================================================================
# Geometría
# ==============================================================================================================


class Parte:
    """Una malla del modelo. Acumula geometría en un bmesh con un material por cara."""

    def __init__(self, modelo, nombre, tipo="textura", color=None, pivote=(0, 0, 0), material_roblox=None,
                 transparencia=None, nota=""):
        self.modelo = modelo
        self.nombre = nombre
        self.tipo = tipo  # textura | neon | cristal
        self.color = color
        self.pivote = V(pivote)
        self.material_roblox = material_roblox or {"textura": "SurfaceAppearance", "neon": "Neon",
                                                   "cristal": "Glass"}[tipo]
        self.transparencia = transparencia
        self.nota = nota
        self.bm = bmesh.new()
        self.mats = []
        if tipo == "neon":
            self.mat_unico = material_simple(f"{nombre}_m", color, emision=6.0, alfa=1.0 - (transparencia or 0.0))
        elif tipo == "cristal":
            self.mat_unico = material_simple(f"{nombre}_m", color or "#9FC4D8", cristal=True)
        else:
            self.mat_unico = None

    # ---- transformaciones -----------------------------------------------------------------------------------
    # La pila de transformaciones es UNA por modelo y la comparten todas las piezas: dentro de un
    # `with pieza.en(...)` también se mueven los neones, cristales y demás piezas que se modelen en el bloque.
    @property
    def pila(self):
        return self.modelo.pila

    @pila.setter
    def pila(self, valor):
        self.modelo.pila = valor

    @contextmanager
    def en(self, loc=(0, 0, 0), rot=None, esc=None):
        m = Matrix.Translation(V(loc)) @ rot_m(rot)
        if esc is not None:
            if isinstance(esc, (int, float)):
                esc = (esc, esc, esc)
            m = m @ Matrix.Diagonal((*esc, 1.0))
        self.pila.append(self.pila[-1] @ m)
        try:
            yield
        finally:
            self.pila.pop()

    def _idx(self, mat):
        if self.mat_unico is not None:
            mat = self.mat_unico
        if mat is None:
            raise ValueError(f"{self.nombre}: falta material")
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def _cerrar(self, verts, mat, local=Matrix.Identity(4), recalc=True):
        verts = list(verts)
        caras = list({f for v in verts for f in v.link_faces})
        if recalc and caras:
            bmesh.ops.recalc_face_normals(self.bm, faces=caras)
        mtx = self.pila[-1] @ local
        bmesh.ops.transform(self.bm, matrix=mtx, verts=verts)
        # Normales hacia fuera pase lo que pase (espejos, perfiles de torno al revés, polígonos cóncavos en los que
        # recalc_face_normals se equivoca): si el volumen con signo de la primitiva es negativo, se le da la vuelta.
        if caras:
            vol = 0.0
            for f in caras:
                vs = [v.co for v in f.verts]
                for k in range(1, len(vs) - 1):
                    vol += vs[0].dot(vs[k].cross(vs[k + 1]))
            if vol < 0:
                bmesh.ops.reverse_faces(self.bm, faces=caras)
        i = self._idx(mat)
        for f in caras:
            f.material_index = i
        return verts

    def _bisel(self, verts, b, segs=1):
        if b <= 0:
            return verts
        aristas = list({e for v in verts for e in v.link_edges})
        r = bmesh.ops.bevel(self.bm, geom=list(verts) + aristas, offset=b, offset_type="OFFSET", segments=segs,
                            profile=0.5, affect="EDGES", clamp_overlap=True)
        nuevos = set(verts)
        for f in r.get("faces", []):
            nuevos.update(f.verts)
        return [v for v in nuevos if v.is_valid]

    # ---- primitivas -----------------------------------------------------------------------------------------
    def caja(self, c, s, mat, b=0.0, rot=None):
        """Caja de tamaño s centrada en c. b = chaflán de las aristas."""
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        vs = r["verts"]
        bmesh.ops.scale(self.bm, vec=V(s), verts=vs)
        vs = self._bisel(vs, min(b, min(s) * 0.45), 1)
        return self._cerrar(vs, mat, Matrix.Translation(V(c)) @ rot_m(rot))

    def caja_de(self, a, b_, mat, b=0.0):
        a, b_ = V(a), V(b_)
        lo = V((min(a.x, b_.x), min(a.y, b_.y), min(a.z, b_.z)))
        hi = V((max(a.x, b_.x), max(a.y, b_.y), max(a.z, b_.z)))
        return self.caja((lo + hi) / 2, hi - lo, mat, b)

    def cil(self, p0, p1, r, mat, n=12, r1=None, b=0.0, tapas=True, giro=0.0):
        """Cilindro (o tronco de cono si r1) de p0 a p1."""
        p0, p1 = V(p0), V(p1)
        d = p1 - p0
        L = d.length
        r1 = r if r1 is None else r1
        anillos = [[V((math.cos(giro + math.tau * i / n) * rr, math.sin(giro + math.tau * i / n) * rr, z))
                    for i in range(n)] for rr, z in ((r, 0.0), (r1, L))]
        vs = self._loft(anillos, tapas, tapas)
        if b > 0 and tapas:
            aristas = [e for e in {e for v in vs for e in v.link_edges}
                       if len(e.link_faces) == 2 and abs(e.link_faces[0].normal.dot(e.link_faces[1].normal)) < 0.5]
            res = bmesh.ops.bevel(self.bm, geom=aristas, offset=min(b, r * 0.4, L * 0.4), segments=1,
                                  affect="EDGES", clamp_overlap=True)
            nv = set(vs)
            for f in res.get("faces", []):
                nv.update(f.verts)
            vs = [v for v in nv if v.is_valid]
        m = Matrix.Translation(p0) @ base_eje(d).to_4x4()
        return self._cerrar(vs, mat, m)

    def _loft(self, anillos, tapa0=True, tapa1=True, cerrado=True):
        bm = self.bm
        vs = [[bm.verts.new(p) for p in a] for a in anillos]
        n = len(anillos[0])
        t = n if cerrado else n - 1
        for k in range(len(vs) - 1):
            for i in range(t):
                j = (i + 1) % n
                bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]))
        if cerrado and tapa0:
            bm.faces.new(list(reversed(vs[0])))
        if cerrado and tapa1:
            bm.faces.new(vs[-1])
        return [v for a in vs for v in a]

    def loft(self, anillos, mat, tapas=True):
        vs = self._loft([[V(p) for p in a] for a in anillos], tapas, tapas)
        return self._cerrar(vs, mat)

    def torno(self, perfil, mat, n=16, c=(0, 0, 0), eje="Z"):
        """Sólido de revolución. perfil = [(radio, z), ...] de abajo arriba. Radio 0 en los extremos = polo."""
        bm = self.bm
        anillos = []
        polos = []
        for r, z in perfil:
            if r <= 1e-5:
                polos.append(bm.verts.new((0, 0, z)))
                anillos.append(None)
            else:
                anillos.append([bm.verts.new((math.cos(math.tau * i / n) * r, math.sin(math.tau * i / n) * r, z))
                                for i in range(n)])
        todos = []
        for k in range(len(perfil) - 1):
            a, b = anillos[k], anillos[k + 1]
            if a is None and b is None:
                continue
            if a is None:
                p = polos.pop(0) if k == 0 else polos[-1]
                todos.append(p)
                for i in range(n):
                    bm.faces.new((p, b[(i + 1) % n], b[i]))
            elif b is None:
                p = polos[-1]
                todos.append(p)
                for i in range(n):
                    bm.faces.new((a[i], a[(i + 1) % n], p))
            else:
                for i in range(n):
                    j = (i + 1) % n
                    bm.faces.new((a[i], a[j], b[j], b[i]))
        if anillos[0] is not None:
            bm.faces.new(list(reversed(anillos[0])))
        if anillos[-1] is not None:
            bm.faces.new(anillos[-1])
        for a in anillos:
            if a:
                todos.extend(a)
        m = Matrix.Translation(V(c))
        if eje != "Z":
            m = m @ base_eje({"X": (1, 0, 0), "Y": (0, 1, 0), "-Y": (0, -1, 0), "-X": (-1, 0, 0)}[eje]).to_4x4()
        return self._cerrar(set(todos), mat, m)

    def esfera(self, c, r, mat, seg=10, anillos=6, esc=(1, 1, 1)):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=anillos, radius=r)
        vs = res["verts"]
        bmesh.ops.scale(self.bm, vec=V(esc), verts=vs)
        return self._cerrar(vs, mat, Matrix.Translation(V(c)))

    def ico(self, c, r, mat, sub=1, esc=(1, 1, 1), ruido=0.0, semilla=0):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r)
        vs = res["verts"]
        rnd = random.Random(semilla)
        if ruido:
            for v in vs:
                v.co *= 1.0 + rnd.uniform(-ruido, ruido)
        bmesh.ops.scale(self.bm, vec=V(esc), verts=vs)
        return self._cerrar(vs, mat, Matrix.Translation(V(c)))

    def roca(self, c, r, mat, semilla=0, esc=(1, 1, 0.8), ruido=0.28, sub=1):
        """Piedra irregular (icosfera deformada y aplastada)."""
        return self.ico(c, r, mat, sub=sub, esc=esc, ruido=ruido, semilla=semilla)

    def tubo(self, puntos, r, mat, n=8, suave=True, seg=4, tapas=True, cerrado=False, r_fin=None, surcos=0,
             prof=0.0, semilla=0, radios=None):
        """surcos/prof: relieve de corteza (surcos longitudinales con algo de azar). radios: radio por punto."""
        """Tubo a lo largo de una polilínea (suavizada con Catmull-Rom). Para cables, mangueras, barandillas."""
        pts = [V(p) for p in puntos]
        if suave and len(pts) > 2:
            pts = _catmull(pts, seg, cerrado)
        if cerrado:
            pts = pts + [pts[0]]
        tangentes = []
        for i in range(len(pts)):
            a = pts[max(0, i - 1)]
            b = pts[min(len(pts) - 1, i + 1)]
            if cerrado and (i == 0 or i == len(pts) - 1):
                a, b = pts[-2], pts[1]
            tangentes.append((b - a).normalized())
        rnd_surco = random.Random(semilla)
        # marco por transporte paralelo
        t0 = tangentes[0]
        ref = V((0, 0, 1)) if abs(t0.z) < 0.9 else V((1, 0, 0))
        nrm = t0.cross(ref).normalized()
        anillos = []
        for i, (p, t) in enumerate(zip(pts, tangentes)):
            if i > 0:
                nrm = (nrm - t * nrm.dot(t)).normalized()
            bn = t.cross(nrm)
            tt = i / (len(pts) - 1)
            if radios is not None:
                rr = _interp(radios, tt)
            else:
                rr = r if r_fin is None else r + (r_fin - r) * tt
            anillo = []
            for k in range(n):
                f = 1.0
                if surcos and prof:
                    f -= prof * (0.5 + 0.5 * math.cos(math.tau * k * surcos / n + tt * 2.0)) * \
                        (0.6 + 0.8 * rnd_surco.random())
                anillo.append(p + (nrm * math.cos(math.tau * k / n) + bn * math.sin(math.tau * k / n)) * rr * f)
            anillos.append(anillo)
        vs = self._loft(anillos, tapas and not cerrado, tapas and not cerrado)
        if cerrado:
            bmesh.ops.remove_doubles(self.bm, verts=vs, dist=1e-5)
            vs = [v for v in vs if v.is_valid]
        return self._cerrar(vs, mat)

    def toro(self, c, R, r, mat, n=24, m=8, arco=360.0, rot=None):
        pts = [V((math.cos(math.radians(arco) * i / (n if arco < 360 else n)) * R,
                  math.sin(math.radians(arco) * i / n) * R, 0)) for i in range(n + (1 if arco < 360 else 0))]
        with self.en(c, rot):
            return self.tubo(pts, r, mat, n=m, suave=False, cerrado=arco >= 360)

    def extruir(self, pts2d, grosor, mat, c=(0, 0, 0), rot=None, b=0.0):
        """Polígono (x, y) extruido en z de -grosor/2 a +grosor/2. Con rot (90,0,0) queda vertical mirando a -Y."""
        bm = self.bm
        abajo = [bm.verts.new((x, y, -grosor / 2)) for x, y in pts2d]
        arriba = [bm.verts.new((x, y, grosor / 2)) for x, y in pts2d]
        n = len(pts2d)
        bm.faces.new(list(reversed(abajo)))
        bm.faces.new(arriba)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((abajo[i], abajo[j], arriba[j], arriba[i]))
        vs = abajo + arriba
        vs = self._bisel(vs, b) if b else vs
        return self._cerrar(vs, mat, Matrix.Translation(V(c)) @ rot_m(rot))

    def lamina(self, f, nu, nv, grosor, mat, cerrar_u=False):
        """Superficie paramétrica f(u, v) -> punto (u, v en 0..1) con grosor real (lonas, chapa ondulada, ropa)."""
        bm = self.bm
        P = [[V(f(i / nu, j / nv)) for j in range(nv + 1)] for i in range(nu + 1)]

        def normal(i, j):
            du = P[min(i + 1, nu)][j] - P[max(i - 1, 0)][j]
            dv = P[i][min(j + 1, nv)] - P[i][max(j - 1, 0)]
            nn = du.cross(dv)
            return nn.normalized() if nn.length > 1e-9 else V((0, 0, 1))

        A = [[bm.verts.new(P[i][j] + normal(i, j) * grosor / 2) for j in range(nv + 1)] for i in range(nu + 1)]
        B = [[bm.verts.new(P[i][j] - normal(i, j) * grosor / 2) for j in range(nv + 1)] for i in range(nu + 1)]
        iu = nu if not cerrar_u else nu
        for i in range(nu):
            for j in range(nv):
                bm.faces.new((A[i][j], A[i + 1][j], A[i + 1][j + 1], A[i][j + 1]))
                bm.faces.new((B[i][j], B[i][j + 1], B[i + 1][j + 1], B[i + 1][j]))
        # bordes
        for i in range(nu):
            bm.faces.new((A[i][0], B[i][0], B[i + 1][0], A[i + 1][0]))
            bm.faces.new((A[i][nv], A[i + 1][nv], B[i + 1][nv], B[i][nv]))
        for j in range(nv):
            bm.faces.new((A[0][j], A[0][j + 1], B[0][j + 1], B[0][j]))
            bm.faces.new((A[nu][j], B[nu][j], B[nu][j + 1], A[nu][j + 1]))
        vs = [v for fila in A for v in fila] + [v for fila in B for v in fila]
        return self._cerrar(vs, mat)

    def texto(self, cadena, mat, alto=0.5, grosor=0.05, c=(0, 0, 0), rot=(90, 0, 0), fuente="negrita",
              alinear="CENTER", espaciado=1.0, resol=2, biselado=0.0):
        """Letras 3D. Por defecto de pie, legibles desde -Y. c = centro de la línea (base de las letras en z)."""
        cu = bpy.data.curves.new("txt", "FONT")
        cu.body = cadena
        ruta = FUENTES.get(fuente, fuente)
        cu.font = bpy.data.fonts.load(ruta, check_existing=True)
        cu.size = 1.0
        cu.extrude = grosor / 2 / alto
        cu.bevel_depth = biselado / alto
        cu.resolution_u = resol
        cu.align_x = alinear
        cu.align_y = "BOTTOM_BASELINE"
        cu.space_character = espaciado
        ob = bpy.data.objects.new("txt", cu)
        bpy.context.scene.collection.objects.link(ob)
        dg = bpy.context.evaluated_depsgraph_get()
        me = ob.evaluated_get(dg).to_mesh()
        tmp = bmesh.new()
        tmp.from_mesh(me)
        ob.evaluated_get(dg).to_mesh_clear()
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)
        bmesh.ops.remove_doubles(tmp, verts=tmp.verts, dist=1e-5)
        bmesh.ops.scale(tmp, vec=V((alto, alto, alto)), verts=tmp.verts)
        me2 = bpy.data.meshes.new("txt_m")
        tmp.to_mesh(me2)
        tmp.free()
        antes = set(self.bm.verts)
        self.bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)
        nuevos = [v for v in self.bm.verts if v not in antes]
        return self._cerrar(nuevos, mat, Matrix.Translation(V(c)) @ rot_m(rot), recalc=True)

    # ---- detalles compuestos -----------------------------------------------------------------------------------
    def perno(self, p, d, mat, r=0.05, alto=None, arandela=False):
        """Tornillo de cabeza hexagonal sobre una superficie (p = punto en la superficie, d = normal)."""
        d = V(d).normalized()
        alto = alto or r * 0.7
        p = V(p)
        if arandela:
            self.cil(p - d * 0.005, p + d * r * 0.25, r * 1.45, mat, n=6, giro=0.5)
            p = p + d * r * 0.25
        self.cil(p - d * 0.003, p + d * alto, r, mat, n=6)

    def remache(self, p, d, mat, r=0.045):
        d = V(d).normalized()
        self.cil(V(p) - d * 0.004, V(p) + d * r * 0.55, r, mat, n=6, r1=r * 0.55)

    def tuerca_fila(self, a, b, n, d, mat, r=0.045, tipo="perno"):
        a, b = V(a), V(b)
        for i in range(n):
            p = a.lerp(b, i / max(1, n - 1))
            (self.perno if tipo == "perno" else self.remache)(p, d, mat, r)

    def arco_tubo(self, c, R, r, mat, a0, a1, plano="XZ", n=8, seg=10):
        """Arco de tubo (en grados) en el plano dado, centrado en c."""
        pts = []
        for i in range(seg + 1):
            a = math.radians(a0 + (a1 - a0) * i / seg)
            if plano == "XZ":
                pts.append(V(c) + V((math.cos(a) * R, 0, math.sin(a) * R)))
            elif plano == "YZ":
                pts.append(V(c) + V((0, math.cos(a) * R, math.sin(a) * R)))
            else:
                pts.append(V(c) + V((math.cos(a) * R, math.sin(a) * R, 0)))
        return self.tubo(pts, r, mat, n=n, suave=False)


def _interp(valores, t):
    """Interpolación lineal de una lista de valores en t (0..1)."""
    if len(valores) == 1:
        return valores[0]
    x = t * (len(valores) - 1)
    i = min(int(x), len(valores) - 2)
    return valores[i] + (valores[i + 1] - valores[i]) * (x - i)


def _catmull(p, seg, cerrado=False):
    out = []
    n = len(p)
    rng = range(n) if cerrado else range(n - 1)
    for i in rng:
        p0 = p[(i - 1) % n] if cerrado else p[max(i - 1, 0)]
        p1 = p[i]
        p2 = p[(i + 1) % n] if cerrado else p[i + 1]
        p3 = p[(i + 2) % n] if cerrado else p[min(i + 2, n - 1)]
        for k in range(seg):
            t = k / seg
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not cerrado:
        out.append(p[-1])
    return out


# ==============================================================================================================
# Modelo: partes, horneado, render, exportación, verificación
# ==============================================================================================================


class Modelo:
    def __init__(self, nombre, zona, tam, presupuesto, descripcion=""):
        t0 = time.time()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scn = bpy.context.scene
        scn.unit_settings.system = "METRIC"
        scn.unit_settings.scale_length = 1.0
        scn.world = bpy.data.worlds.new("mundo")
        self.t0 = t0
        self.nombre = nombre
        self.zona = zona
        self.tam = tam
        self.presupuesto = presupuesto
        self.descripcion = descripcion
        self.partes = []
        self._mats = {}
        self.anclajes = {}
        self.notas = []
        self._secc = [("inicio", 0)]
        self.pila = [Matrix.Identity(4)]  # transformaciones activas (compartidas por todas las piezas)
        # vistas añadidas al turnaround: (nombre, azimut, elevación, nombres de mallas que se ocultan)
        self.vistas_extra = []
        # Se genera en una carpeta temporal fuera del repositorio y solo se mueve a su sitio (RAIZ/zona/nombre)
        # cuando todo ha salido bien y el FBX está verificado: así nunca queda un modelo a medias en la rama.
        self.dir_final = os.path.join(RAIZ, zona, nombre)
        provisional = os.environ.get("PH_PROVISIONAL", os.path.join(tempfile.gettempdir(), "planeta_humano_provisional"))
        self.dir = os.path.join(provisional, zona, nombre)
        if not os.environ.get("PH_DEBUG"):
            shutil.rmtree(self.dir, ignore_errors=True)
            os.makedirs(os.path.join(self.dir, "texturas"), exist_ok=True)
        self.rnd = random.Random(zlib.crc32(nombre.encode()))  # semilla estable entre ejecuciones

    def parte(self, sufijo=None, tipo="textura", color=None, pivote=(0, 0, 0), **kw):
        nombre = self.nombre if not sufijo else f"{self.nombre}_{sufijo}"
        if tipo == "neon" and not nombre.endswith("_neon"):
            nombre += "_neon"
        if tipo == "cristal" and not nombre.endswith("_cristal"):
            nombre += "_cristal"
        p = Parte(self, nombre, tipo, color, pivote, **kw)
        self.partes.append(p)
        return p

    def mat(self, tipo, color, **kw):
        """Material procedural con caché por parámetros."""
        clave = (tipo, color, tuple(sorted((k, str(v)) for k, v in kw.items())))
        if clave not in self._mats:
            p = dict(TIPOS[tipo])
            p.update(kw)
            p["tipo"] = tipo
            self._mats[clave] = crear_material(f"{tipo}_{len(self._mats):02d}", tipo, color, p)
        return self._mats[clave]

    def seccion(self, nombre):
        """Marca para el informe de triángulos por sección (PH_DEBUG=1)."""
        t = sum(sum(len(f.verts) - 2 for f in p.bm.faces) for p in self.partes)
        self._secc.append((nombre, t))

    def anclaje(self, nombre, pos, nota=""):
        self.anclajes[nombre] = (V(pos), nota)

    # ---- construcción de objetos ---------------------------------------------------------------------------
    def _objetos(self):
        objs = []
        for p in self.partes:
            if not p.bm.verts:
                continue
            bm = p.bm
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
            bmesh.ops.dissolve_degenerate(bm, edges=bm.edges, dist=1e-6)
            bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="EAR_CLIP")
            # el origen (pivote) de cada pieza
            bmesh.ops.translate(bm, vec=-p.pivote, verts=bm.verts)
            me = bpy.data.meshes.new(p.nombre)
            bm.to_mesh(me)
            bm.free()
            ob = bpy.data.objects.new(p.nombre, me)
            ob.location = p.pivote
            bpy.context.scene.collection.objects.link(ob)
            for m in p.mats:
                me.materials.append(m)
            ob["tipo"] = p.tipo
            p.obj = ob
            objs.append(ob)
            # sombreado: suave con corte por ángulo
            for poly in me.polygons:
                poly.use_smooth = True
            bpy.ops.object.select_all(action="DESELECT")
            bpy.context.view_layer.objects.active = ob
            ob.select_set(True)
            bpy.ops.object.shade_smooth_by_angle(angle=math.radians(34))
        return objs

    def _uv(self, objs):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.0025, area_weight=0.0,
                                 correct_aspect=True, scale_to_bounds=False)
        bpy.ops.uv.pack_islands(udim_source="CLOSEST_UDIM", rotate=True, margin_method="FRACTION", margin=0.0025,
                                shape_method="CONCAVE")
        bpy.ops.object.mode_set(mode="OBJECT")

    def _hornear(self, objs, muestras=16):
        scn = bpy.context.scene
        scn.render.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.render.bake.margin = 6
        scn.render.bake.margin_type = "EXTEND"
        mats = {m for o in objs for m in o.data.materials}
        emite = any(m.node_tree.nodes.get("canal_emi") for m in mats)
        canales = [("color", "sRGB"), ("rugosidad", "Non-Color"), ("metal", "Non-Color"), ("normal", "Non-Color")]
        if emite:
            canales.append(("emision", "sRGB"))
        imgs = {}
        for canal, espacio in canales:
            img = bpy.data.images.new(f"{self.nombre}_{canal}", TAM_ATLAS, TAM_ATLAS, alpha=False)
            img.colorspace_settings.name = espacio
            imgs[canal] = img
            for m in mats:
                nt = m.node_tree
                dest = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
                dest.name = "destino"
                dest.image = img
                nt.nodes.active = dest
            bpy.ops.object.select_all(action="DESELECT")
            for o in objs:
                o.select_set(True)
            bpy.context.view_layer.objects.active = objs[0]
            t = time.time()
            if canal == "normal":
                scn.cycles.samples = 4
                bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT", margin=6, use_clear=True)
            else:
                guardado = []
                for m in mats:
                    nt = m.node_tree
                    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
                    em = nt.nodes.new("ShaderNodeEmission")
                    em.name = "em_tmp"
                    fuente = {"color": nt.nodes["canal_color"].outputs[2],
                              "rugosidad": nt.nodes["canal_rug"].outputs[0],
                              "metal": nt.nodes["canal_met"].outputs[0],
                              "emision": (nt.nodes["canal_emi"].outputs[0] if nt.nodes.get("canal_emi") else None)}[canal]
                    if fuente is None:
                        em.inputs["Color"].default_value = (0, 0, 0, 1)
                    else:
                        nt.links.new(fuente, em.inputs["Color"])
                    prev = out.inputs["Surface"].links[0].from_socket
                    nt.links.new(em.outputs[0], out.inputs["Surface"])
                    guardado.append((nt, out, prev, em))
                scn.cycles.samples = muestras if canal == "color" else max(4, muestras // 2)
                bpy.ops.object.bake(type="EMIT", margin=6, use_clear=True)
                for nt, out, prev, em in guardado:
                    nt.links.new(prev, out.inputs["Surface"])
                    nt.nodes.remove(em)
            print(f"   horneado {canal}: {time.time() - t:.0f} s", flush=True)
        rutas = {}
        for canal, img in imgs.items():
            ruta = os.path.join(self.dir, "texturas", f"{self.nombre}_{canal}.png")
            img.filepath_raw = ruta
            img.file_format = "PNG"
            img.save()
            im = Image.open(ruta)
            if canal in ("rugosidad", "metal"):
                im = im.convert("L")
            else:
                im = im.convert("RGB")
            im.save(ruta, optimize=True)
            img.reload()
            rutas[canal] = ruta
        # material final con el atlas (lo que se exporta y se renderiza)
        final = bpy.data.materials.new(f"{self.nombre}_atlas")
        final.use_nodes = True
        nt = final.node_tree
        b = nt.nodes["Principled BSDF"]
        def tex(canal, entrada, normal=False):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = imgs[canal]
            if normal:
                nm = nt.nodes.new("ShaderNodeNormalMap")
                nt.links.new(n.outputs[0], nm.inputs["Color"])
                nt.links.new(nm.outputs[0], b.inputs["Normal"])
            else:
                nt.links.new(n.outputs[0], b.inputs[entrada])
        tex("color", "Base Color")
        tex("rugosidad", "Roughness")
        tex("metal", "Metallic")
        tex("normal", None, normal=True)
        if emite:
            tex("emision", "Emission Color")
            b.inputs["Emission Strength"].default_value = 3.0
        for o in objs:
            o.data.materials.clear()
            o.data.materials.append(final)
            for poly in o.data.polygons:
                poly.material_index = 0
        return rutas

    # ---- render --------------------------------------------------------------------------------------------
    def _turnaround(self, objs, tam=560, muestras=40, vistas=None, salida=None, cols=4):
        scn = bpy.context.scene
        scn.render.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.cycles.samples = muestras
        scn.cycles.use_denoising = True
        scn.render.resolution_x = scn.render.resolution_y = tam
        scn.view_settings.view_transform = "AgX"
        scn.view_settings.look = "AgX - Medium High Contrast"
        scn.world.use_nodes = True
        bg = scn.world.node_tree.nodes["Background"]
        bg.inputs["Color"].default_value = (0.20, 0.22, 0.26, 1)
        bg.inputs["Strength"].default_value = 0.35
        mn, mx = _caja(objs)
        c = (mn + mx) / 2
        radio = max((mx - mn).length / 2, 0.5)
        # suelo de estudio
        bpy.ops.mesh.primitive_plane_add(size=radio * 60, location=(c.x, c.y, mn.z - 0.002))
        suelo = bpy.context.active_object
        ms = material_simple("suelo", "#3A3E46")
        ms.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
        suelo.data.materials.append(ms)
        mira = bpy.data.objects.new("mira", None)
        scn.collection.objects.link(mira)
        mira.location = c

        def luz(nombre, pos, energia, color, tam_l):
            d = bpy.data.lights.new(nombre, "AREA")
            d.energy = energia * radio * radio
            d.color = color
            d.size = tam_l * radio
            o = bpy.data.objects.new(nombre, d)
            o.location = c + V(pos) * radio
            o.visible_camera = False
            scn.collection.objects.link(o)
            tr = o.constraints.new("TRACK_TO")
            tr.target = mira
            tr.track_axis = "TRACK_NEGATIVE_Z"
            tr.up_axis = "UP_Y"

        # 3 luces de estudio: principal, relleno y contraluz
        luz("principal", (-2.2, -2.6, 2.6), 260, (1.0, 0.95, 0.88), 1.2)
        luz("relleno", (2.8, -1.6, 1.2), 90, (0.8, 0.88, 1.0), 2.0)
        luz("contraluz", (0.8, 3.2, 2.4), 200, (0.85, 0.92, 1.0), 1.0)

        cam_d = bpy.data.cameras.new("cam")
        cam_d.lens = 50
        cam_d.clip_end = 5000
        cam_d.clip_start = 0.01
        cam = bpy.data.objects.new("cam", cam_d)
        scn.collection.objects.link(cam)
        scn.camera = cam
        fov = 2 * math.atan(18 / 50)
        dist = radio * 1.08 / math.sin(fov / 2)
        # el frente es -Y; "Lateral Izq" es el lado izquierdo del modelo (+X)
        vistas = vistas or [("Frente", 0, 10), ("3/4 Frontal", -40, 22), ("Lateral Izq", 90, 8),
                            ("3/4 Trasera", 140, 24), ("Trasera", 180, 10), ("Lateral Der", -90, 8),
                            ("Arriba", 0, 89.5), ("Wireframe", -40, 22)]
        carpeta = os.path.join(self.dir, "_render")
        os.makedirs(carpeta, exist_ok=True)
        rutas = []
        lista = [(n, a_, e_, ()) for n, a_, e_ in vistas] + [tuple(v) for v in self.vistas_extra]
        for nombre, az, el, ocultar in lista:
            ocultos = [o for o in objs if o.name in ocultar]
            for o in ocultos:
                o.hide_render = True
            a, e = math.radians(az), math.radians(el)
            # azimut positivo = hacia +X
            dirc = V((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
            cam.location = c + dirc * dist
            up = "Y" if el < 89 else "Y"
            q = (c - cam.location).to_track_quat("-Z", "Y")
            cam.rotation_euler = q.to_euler()
            scn.view_layers[0].material_override = _material_malla() if nombre == "Wireframe" else None
            suelo.hide_render = nombre == "Wireframe"
            ruta = os.path.join(carpeta, nombre.replace("/", "-").replace(" ", "_") + ".png")
            scn.render.filepath = ruta
            bpy.ops.render.render(write_still=True)
            rutas.append((nombre, ruta))
            for o in ocultos:
                o.hide_render = False
        scn.view_layers[0].material_override = None
        # hoja
        filas = (len(rutas) + cols - 1) // cols
        hoja = Image.new("RGB", (cols * tam, filas * tam + 70), (18, 20, 26))
        d = ImageDraw.Draw(hoja)
        d.text((16, 10), f"{self.nombre}", fill=(255, 214, 102), font=_fuente(30))
        tris = sum(_tris(o) for o in objs)
        dims = mx - mn
        d.text((16, 46), f"{dims.x:.1f} x {dims.y:.1f} x {dims.z:.1f} studs  ·  {tris:,} triángulos "
                         f"(máx {self.presupuesto:,})  ·  {len(objs)} mallas", fill=(210, 214, 224),
               font=_fuente(16, False))
        for i, (nombre, ruta) in enumerate(rutas):
            x, y = (i % cols) * tam, 70 + (i // cols) * tam
            hoja.paste(Image.open(ruta).convert("RGB"), (x, y))
            d.rectangle((x, y, x + tam - 1, y + tam - 1), outline=(44, 48, 60))
            d.text((x + 10, y + 8), nombre, fill=(255, 255, 255), font=_fuente(17))
        salida = salida or os.path.join(self.dir, f"{self.nombre}_turnaround.png")
        hoja.save(salida, optimize=True)
        for o in (suelo, mira, cam):
            bpy.data.objects.remove(o)
        for o in list(scn.objects):
            if o.type == "LIGHT":
                bpy.data.objects.remove(o)
        return salida

    # ---- exportación ---------------------------------------------------------------------------------------
    def _exportar(self, objs):
        giro = Matrix.Rotation(GIRO_IMPORTACION, 4, "Z")
        for o in objs:
            o.matrix_world = giro @ o.matrix_world
        bpy.ops.object.select_all(action="DESELECT")
        for o in objs:
            o.select_set(True)
        bpy.context.view_layer.objects.active = objs[0]
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        ruta = os.path.join(self.dir, f"{self.nombre}.fbx")
        bpy.context.scene.unit_settings.scale_length = METROS_POR_STUD  # la unidad del FBX = 1 stud (0,28 m)
        bpy.ops.export_scene.fbx(filepath=ruta, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                                 apply_scale_options="FBX_SCALE_ALL", global_scale=1.0, axis_forward="-Z",
                                 axis_up="Y", use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True,
                                 bake_anim=False, embed_textures=False, path_mode="RELATIVE")
        bpy.context.scene.unit_settings.scale_length = 1.0
        # deshacer el giro para que la escena quede como se modeló
        inv = giro.inverted()
        for o in objs:
            o.matrix_world = inv @ o.matrix_world
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        return ruta

    def _verificar(self, ruta, esperado):
        """Reimporta el FBX en una escena vacía y comprueba piezas, triángulos, tamaño y normales."""
        bpy.ops.wm.read_factory_settings(use_empty=True)
        # escena de 0,28 m por unidad: el FBX entra 1:1 y los tamaños se comparan en studs
        bpy.context.scene.unit_settings.scale_length = METROS_POR_STUD
        bpy.ops.import_scene.fbx(filepath=ruta)
        objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
        res = {"piezas": len(objs), "ok": True, "problemas": [], "unidad_fbx_m": unidad_fbx(ruta)}
        nombres = {o.name for o in objs}
        if nombres != set(esperado["nombres"]):
            res["ok"] = False
            res["problemas"].append(f"nombres distintos: {sorted(nombres ^ set(esperado['nombres']))}")
        tris = sum(_tris(o) for o in objs)
        res["triangulos"] = tris
        if tris != esperado["tris"]:
            res["ok"] = False
            res["problemas"].append(f"triángulos {tris} != {esperado['tris']}")
        mn, mx = _caja(objs)
        dims = mx - mn
        # en Blender tras importar: X = X, Y = fondo, Z = alto (el importador deshace el cambio de ejes)
        res["tam_studs"] = [round(dims.x, 3), round(dims.y, 3), round(dims.z, 3)]
        for k in range(3):
            if abs(dims[k] - esperado["dims"][k]) > 0.02:
                res["ok"] = False
                res["problemas"].append(f"tamaño eje {k}: {dims[k]:.3f} != {esperado['dims'][k]:.3f}")
        # el frente debe haber quedado en +Y de Blender (= -Z del FBX), es decir, girado 180°
        cen = (mn + mx) / 2
        res["centro"] = [round(cen.x, 3), round(cen.y, 3), round(cen.z, 3)]
        malas = []
        for o in objs:
            vol = _volumen(o)
            inv = islas_invertidas(o)
            if vol <= 0 or inv:
                malas.append(f"{o.name} ({inv} piezas del revés)")
        if malas:
            res["ok"] = False
            res["problemas"].append("normales hacia dentro: " + ", ".join(malas))
        res["normales_fuera"] = not malas
        return res

    # ---- todo junto ----------------------------------------------------------------------------------------
    def terminar(self, muestras_horneado=16):
        print(f"== {self.nombre}", flush=True)
        self.seccion("fin")
        if os.environ.get("PH_PREVIEW"):
            # vista previa rápida para revisar la geometría: sin UV ni horneado, materiales procedurales tal cual
            objs = self._objetos()
            carpeta = os.environ["PH_PREVIEW"]
            os.makedirs(carpeta, exist_ok=True)
            self.dir = os.path.join(carpeta, "_tmp_" + self.nombre)
            os.makedirs(self.dir, exist_ok=True)
            ruta = self._turnaround(objs, tam=420, muestras=10, cols=2, salida=os.path.join(carpeta, self.nombre + ".png"),
                                    vistas=[("Frente", 0, 10), ("3/4 Frontal", -40, 22), ("3/4 Trasera", 140, 24),
                                            ("Lateral Izq", 90, 8)])
            shutil.rmtree(self.dir, ignore_errors=True)
            print("   vista previa:", ruta, flush=True)
            raise SystemExit
        if os.environ.get("PH_DEBUG"):
            for (a, ta), (b, tb) in zip(self._secc, self._secc[1:]):
                print(f"   {a:<28} {tb - ta:>7}")
            for p in self.partes:
                print(f"   parte {p.nombre:<40} {sum(len(f.verts) - 2 for f in p.bm.faces):>7}")
            raise SystemExit
        objs = self._objetos()
        tex = [o for o in objs if o["tipo"] == "textura"]
        tris = {o.name: _tris(o) for o in objs}
        total = sum(tris.values())
        print(f"   triángulos: {total} (máx {self.presupuesto})", flush=True)
        if total > self.presupuesto:
            raise SystemExit(f"{self.nombre}: {total} triángulos, por encima del presupuesto {self.presupuesto}")
        malas = [o.name for o in objs if _volumen(o) <= 0 or islas_invertidas(o)]
        if malas:
            raise SystemExit(f"{self.nombre}: normales hacia dentro en {malas}")
        mn, mx = _caja(objs)
        dims = mx - mn
        self._uv(tex)
        rutas = self._hornear(tex, muestras_horneado)
        hoja = self._turnaround(objs)
        info_piezas = []
        for p in self.partes:
            if not hasattr(p, "obj"):
                continue
            o = p.obj
            a, b = _caja([o])
            info_piezas.append({
                "nombre": o.name,
                "tipo": p.tipo,
                "material_roblox": p.material_roblox,
                "color": p.color,
                "transparencia": p.transparencia,
                "triangulos": tris[o.name],
                "tam_studs": _roblox_tam(b - a),
                "pivote_studs": _roblox_pos(p.pivote),
                "centro_studs": _roblox_pos((a + b) / 2),
                "nota": p.nota,
            })
        ruta = self._exportar(objs)
        esperado = {"nombres": [o.name for o in objs], "tris": total, "dims": [dims.x, dims.y, dims.z]}
        ver = self._verificar(ruta, esperado)
        datos = {
            "nombre": self.nombre,
            "zona": self.zona,
            "descripcion": self.descripcion,
            "tam_pedido_studs": list(self.tam),
            "tam_studs": {"ancho_x": round(dims.x, 2), "alto_y": round(dims.z, 2), "fondo_z": round(dims.y, 2)},
            "triangulos": total,
            "presupuesto": self.presupuesto,
            "escala": "1 unidad = 1 stud (FBX_SCALE_ALL); el FBX declara 0,28 m por unidad",
            "giro_importacion": "180° sobre el eje Y de Roblox antes de exportar: el frente mira a -Z en Studio",
            "coordenadas": "Roblox: X derecha del modelo, Y arriba, Z hacia atrás; origen en el suelo, en el centro",
            "atlas": {k: os.path.relpath(v, self.dir) for k, v in rutas.items()},
            "tam_atlas": TAM_ATLAS,
            "piezas": info_piezas,
            "anclajes": {k: {"pos_studs": _roblox_pos(v[0]), "nota": v[1]} for k, v in self.anclajes.items()},
            "notas": self.notas,
            "verificacion_fbx": ver,
            "turnaround": os.path.relpath(hoja, self.dir),
        }
        with open(os.path.join(self.dir, f"{self.nombre}.json"), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        estado = "OK" if ver["ok"] else "FALLO " + "; ".join(ver["problemas"])
        print(f"   {self.nombre}: {total} tris, {dims.x:.1f}x{dims.y:.1f}x{dims.z:.1f}, verificación {estado}, "
              f"{time.time() - self.t0:.0f} s", flush=True)
        if not ver["ok"]:
            raise SystemExit(f"{self.nombre}: verificación del FBX fallida: {ver['problemas']}")
        # todo bien: se mueve la carpeta completa a su sitio en el repositorio (rutas relativas, siguen valiendo)
        shutil.rmtree(self.dir_final, ignore_errors=True)
        os.makedirs(os.path.dirname(self.dir_final), exist_ok=True)
        shutil.move(self.dir, self.dir_final)
        print(f"   -> {os.path.relpath(self.dir_final, RAIZ)}", flush=True)
        return datos


# ---- utilidades ----------------------------------------------------------------------------------------------

def unidad_fbx(ruta):
    """Metros por unidad que declara un FBX binario (GlobalSettings > UnitScaleFactor, en cm)."""
    import struct
    datos = open(ruta, "rb").read()
    i = datos.find(b"UnitScaleFactor")
    for pos in range(i + 15, i + 120):
        if datos[pos:pos + 1] == b"D":
            return round(struct.unpack("<d", datos[pos + 1:pos + 9])[0] / 100.0, 6)
    return None


def _roblox_pos(p):
    # Blender (x, y, z) con el frente en -Y  ->  Roblox tras el giro de 180°: (-x, z, y)
    return [round(-p[0], 3), round(p[2], 3), round(p[1], 3)]


def _roblox_tam(d):
    return [round(d[0], 3), round(d[2], 3), round(d[1], 3)]


def _caja(objs):
    mn = V((1e9, 1e9, 1e9))
    mx = V((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = V(map(min, mn, w))
            mx = V(map(max, mx, w))
    return mn, mx


def islas_invertidas(o):
    """Cuenta las piezas sueltas (islas de caras conectadas) con el volumen negativo: normales hacia dentro."""
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.faces.ensure_lookup_table()
    vistas = set()
    malas = 0
    for f0 in bm.faces:
        if f0.index in vistas:
            continue
        pila, isla = [f0], []
        vistas.add(f0.index)
        while pila:
            f = pila.pop()
            isla.append(f)
            for e in f.edges:
                for g in e.link_faces:
                    if g.index not in vistas:
                        vistas.add(g.index)
                        pila.append(g)
        vol = 0.0
        for f in isla:
            vs = [v.co for v in f.verts]
            for k in range(1, len(vs) - 1):
                vol += vs[0].dot(vs[k].cross(vs[k + 1]))
        if vol < -1e-7:
            malas += 1
    bm.free()
    return malas


def _tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


def _volumen(o):
    me = o.data
    me.calc_loop_triangles()
    co = [v.co for v in me.vertices]
    s = 0.0
    for t in me.loop_triangles:
        a, b, c = (co[i] for i in t.vertices)
        s += a.dot(b.cross(c))
    return s / 6


def _fuente(tam, negrita=True):
    return ImageFont.truetype(FUENTES["negrita" if negrita else "normal"], tam)


def _material_malla():
    m = bpy.data.materials.get("vista_malla")
    if m:
        return m
    m = bpy.data.materials.new("vista_malla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 0.9
    base = nt.nodes.new("ShaderNodeBsdfDiffuse")
    base.inputs["Color"].default_value = (0.42, 0.44, 0.5, 1)
    linea = nt.nodes.new("ShaderNodeEmission")
    linea.inputs["Color"].default_value = (0.24, 0.95, 1.0, 1)
    linea.inputs["Strength"].default_value = 1.5
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wire.outputs["Fac"], mezcla.inputs["Fac"])
    nt.links.new(base.outputs["BSDF"], mezcla.inputs[1])
    nt.links.new(linea.outputs["Emission"], mezcla.inputs[2])
    nt.links.new(mezcla.outputs["Shader"], salida.inputs["Surface"])
    return m
