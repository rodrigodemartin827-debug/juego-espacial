"""
BESTIA 2 — DRAGÓN DEL VACÍO (montura de combate de los Monstruos: piloto + artillero).

Pterosaurio cruzado con tiburón del tamaño de una camioneta: piel negra con reflejos rojizos, vientre gris carbón,
alas de murciélago rojo sangre plegadas como una capa, cuernos y placas de hueso oscuro, ojos de estrella moribunda
(#FF4500), marcas de guerra en el pecho, cicatriz de zarpazo en el cuello y un parche regenerado en el ala izquierda.

Rig (17 piezas): Torso (raíz), Cuello, Cabeza, Mandibula, Ala_{Izq,Der}_{Hombro,Antebrazo,Mano},
Pata_{Izq,Der}_{Muslo,Tibia}, Cola_Base, Cola_Media, Cola_Punta. Soldada a la Cabeza: Ojos_Cornea.
Puntos de montaje: Montura_Piloto, Montura_Artillero, Agarre_Cuello_Izq, Agarre_Cuello_Der, Punto_Ataque.

Uso: python bestias/herramientas/dragon_vacio.py --salida bestias/dragon_vacio --ronda 1 [--rapido]
"""

import argparse
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import bestia  # noqa: E402
import campos as C  # noqa: E402
import detalles as D  # noqa: E402
import dragon_forma as F  # noqa: E402
import taller as T  # noqa: E402

NOMBRE = "dragon_vacio"
PRESUPUESTO = 20000

COL = {
    "lomo": "#1A0A0A", "reflejo": "#2D1111", "vientre": "#2A2A2A", "membrana": "#8B0000", "hueso_os": "#3D2B1F",
    "neon": "#FF4500", "garra": "#1A1A1A", "punta": "#E8DCC8", "cuero": "#2A1A10", "hueso": "#D4C8B0",
    "madera": "#5A3A22", "hierro": "#2E2C2A", "costura": "#9C8A6A", "sangre": "#3A0D06", "boca": "#4A0A08",
    "cicatriz": "#5E3A36", "parche": "#6A3030",
}


def lin(h):
    return T.srgb(COL.get(h, h))


def smooth(N, a, b, x):
    m = N.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
    m.inputs["From Min"].default_value = a
    m.inputs["From Max"].default_value = b
    N.enlazar(x, m.inputs["Value"])
    return m.outputs["Result"]


# --------------------------------------------------------------------------------------------------------------
# Mapas de perfil (runas de los hombros, cicatriz del cuello, parche del ala) y de frente (marcas de guerra)
# --------------------------------------------------------------------------------------------------------------

LADO_DOM = (-9.5, -0.2, 7.8, 8.8)   # y0, z0, y1, z1
FRENTE_DOM = (-1.6, 1.4, 1.6, 4.4)  # x0, z0, x1, z1
PX = 90


def imagen_blender(nombre, datos):
    h, w = datos.shape[:2]
    im = bpy.data.images.new(nombre, w, h, alpha=True, float_buffer=True)
    im.colorspace_settings.name = "Non-Color"
    im.alpha_mode = "CHANNEL_PACKED"
    im.pixels.foreach_set(np.flipud(datos).astype(np.float32).ravel())
    im.pack()
    return im


def mapas():
    from scipy.ndimage import gaussian_filter

    y0, z0, y1, z1 = LADO_DOM
    W, H = int((y1 - y0) * PX), int((z1 - z0) * PX)

    def px(y, z):
        return ((y - y0) * PX, (z1 - z) * PX)

    def lienzo():
        return Image.new("L", (W, H), 0)

    def runas(d, cy, cz, semilla):
        r = random.Random(semilla)
        for k in range(3):  # tres runas angulares en columna, como nórdicas
            x = cy - 0.32 + k * 0.32
            alto = 0.42
            d.line([px(x, cz - alto / 2), px(x, cz + alto / 2)], fill=255, width=int(0.045 * PX))
            for _ in range(2):
                a = r.uniform(-0.45, 0.45)
                zz = cz + r.uniform(-0.12, 0.16)
                d.line([px(x, zz), px(x + 0.13 * math.copysign(1, a), zz + 0.16 * (1 if a > 0 else -1))], fill=255,
                       width=int(0.04 * PX))

    izq, der, cic, par = lienzo(), lienzo(), lienzo(), lienzo()
    runas(ImageDraw.Draw(izq), 2.25, 3.05, 1)
    runas(ImageDraw.Draw(der), 2.25, 3.05, 2)
    d = ImageDraw.Draw(cic)
    for k in range(3):  # zarpazo: 3 líneas paralelas en el lado izquierdo del cuello
        o = k * 0.17
        d.line([px(2.55 + o, 4.05 + o * 0.3), px(3.25 + o, 5.25 + o * 0.3)], fill=255, width=int(0.07 * PX))
    d = ImageDraw.Draw(par)
    pts = []
    for t in np.linspace(0, math.tau, 30, endpoint=False):
        rr = 1 + 0.22 * math.sin(3 * t) + 0.12 * math.sin(7 * t + 1)
        pts.append(px(0.9 + 0.55 * rr * math.cos(t), 2.6 + 0.38 * rr * math.sin(t)))
    d.polygon(pts, fill=255)
    lado = np.stack([gaussian_filter(np.asarray(i, np.float32) / 255, s) for i, s in
                     ((izq, 0.8), (der, 0.8), (cic, 1.4), (par, 3.0))], -1)

    x0, fz0, x1, fz1 = FRENTE_DOM
    W2, H2 = int((x1 - x0) * PX), int((fz1 - fz0) * PX)
    gue = Image.new("L", (W2, H2), 0)
    d = ImageDraw.Draw(gue)
    for k in range(3):  # tres rayas diagonales grabadas en el pecho
        o = -0.42 + k * 0.42
        d.line([((o - 0.25 - x0) * PX, (fz1 - 3.35) * PX), ((o + 0.25 - x0) * PX, (fz1 - 2.35) * PX)], fill=255,
               width=int(0.065 * PX))
    frente = gaussian_filter(np.asarray(gue, np.float32) / 255, 1.0)
    frente = np.stack([frente, frente, frente, np.ones_like(frente)], -1)
    return imagen_blender("dragon_lado", lado), imagen_blender("dragon_frente", frente)


# --------------------------------------------------------------------------------------------------------------
# Materiales
# --------------------------------------------------------------------------------------------------------------


def material_piel(img_lado, img_frente):
    mat = bpy.data.materials.new("piel")
    N = T.Nodos(mat)
    P = N.pos()
    px_, py_, pz_ = N.sep(P)
    nx_, ny_, nz_ = N.sep(N.normal())
    y0, z0, y1, z1 = LADO_DOM
    uv_l = N.combinar(N.mate("DIVIDE", N.mate("SUBTRACT", py_, y0), y1 - y0),
                      N.mate("DIVIDE", N.mate("SUBTRACT", pz_, z0), z1 - z0), 0.0)
    x0, fz0, x1, fz1 = FRENTE_DOM
    uv_f = N.combinar(N.mate("DIVIDE", N.mate("SUBTRACT", px_, x0), x1 - x0),
                      N.mate("DIVIDE", N.mate("SUBTRACT", pz_, fz0), fz1 - fz0), 0.0)

    def canales(img, uv):
        t = N.n("ShaderNodeTexImage")
        t.image = img
        t.extension = "CLIP"
        N.enlazar(uv, t.inputs["Vector"])
        s = N.n("ShaderNodeSeparateColor")
        N.enlazar(t.outputs["Color"], s.inputs["Color"])
        return s.outputs[0], s.outputs[1], s.outputs[2], t.outputs["Alpha"]

    r_izq, r_der, cic, _ = canales(img_lado, uv_l)
    guerra, _, _, _ = canales(img_frente, uv_f)
    izq = N.mate("LESS_THAN", px_, -0.2)
    der = N.mate("GREATER_THAN", px_, 0.2)
    runas = N.mate("MAXIMUM", N.mate("MULTIPLY", r_izq, izq), N.mate("MULTIPLY", r_der, der))
    cic = N.mate("MULTIPLY", cic, N.mate("MULTIPLY", izq, N.mate("LESS_THAN", nx_, -0.3)))
    guerra = N.mate("MULTIPLY", guerra, N.mate("MULTIPLY", N.mate("GREATER_THAN", ny_, 0.45),
                                                N.mate("GREATER_THAN", py_, 2.0)))
    guerra = N.mate("MULTIPLY", guerra, N.mate("LESS_THAN", py_, 3.0))
    guerra = N.mate("MULTIPLY", guerra, N.mate("LESS_THAN", N.mate("ABSOLUTE", px_), 0.85))

    vientre = N.mate("SUBTRACT", 1.0, smooth(N, -0.65, -0.2, nz_))
    patas = N.mate("SUBTRACT", 1.0, smooth(N, 1.4, 2.0, pz_))
    cara = smooth(N, 4.3, 4.9, py_)
    cara = N.mate("MULTIPLY", cara, smooth(N, 5.4, 5.9, pz_))

    # Escamas: tejas cerradas (cúpula de Voronoi), más pequeñas en la cara y más gruesas en las patas.
    v_cuerpo = N.voronoi(P, 4.8, rasgo="F1", aleatorio=0.6)
    v_cara = N.voronoi(P, 10.0, rasgo="F1", aleatorio=0.35)
    v_pata = N.voronoi(P, 3.4, rasgo="F1", aleatorio=0.5)
    esc = N.mezcla(cara, v_cuerpo, v_cara)
    esc = N.mezcla(patas, esc, v_pata)
    esc = N.sep(esc)[0]
    teja = N.mate("SUBTRACT", 1.0, smooth(N, 0.0, 0.62, esc))
    escudos = N.mate("ABSOLUTE", N.mate("SINE", N.mate("MULTIPLY", N.mate("ADD", py_, pz_), 9.0)))
    escudos = smooth(N, 0.0, 0.25, escudos)
    costillas = N.mate("SINE", N.mate("MULTIPLY", py_, 7.5))
    en_costado = N.mate("MULTIPLY", smooth(N, 0.45, 0.8, N.mate("ABSOLUTE", nx_)),
                        N.mate("MULTIPLY", smooth(N, -1.6, -1.0, py_), N.mate("SUBTRACT", 1.0, smooth(N, 1.4, 1.9, py_))))
    en_costado = N.mate("MULTIPLY", en_costado, N.mate("MULTIPLY", smooth(N, 2.0, 2.4, pz_),
                                                       N.mate("SUBTRACT", 1.0, smooth(N, 3.3, 3.6, pz_))))
    musculo = N.ruido(P, 0.9, 2.0, 0.4)

    # Color.
    refl = smooth(N, 0.4, 0.75, N.ruido(P, 1.4, 3.0))
    col = N.mezcla(refl, lin("lomo"), lin("reflejo"))
    col = N.mezcla(N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, teja), 0.6), col, (0.002, 0.0, 0.0))
    col = N.mezcla(vientre, col, N.mezcla(N.mate("MULTIPLY", escudos, 0.5), lin("vientre"), (0.01, 0.01, 0.01)))
    col = N.mezcla(cic, col, lin("cicatriz"))
    # Boca: interior rojo oscuro y garganta que brilla.
    bc, br = F.BOCA
    q = N.vmate("DIVIDE", N.vmate("SUBTRACT", P, bc), (br[0] * 1.25, br[1] * 1.08, br[2] * 2.6))
    boca = N.mate("SUBTRACT", 1.0, smooth(N, 0.9, 1.02, N.vmate("LENGTH", q)))
    garganta = N.mate("MULTIPLY", boca, N.mate("SUBTRACT", 1.0, smooth(N, 5.0, 5.6, py_)))
    col = N.mezcla(boca, col, lin("boca"))
    luz = N.mate("MAXIMUM", N.mate("MAXIMUM", runas, guerra), garganta)
    col = N.mezcla(N.mate("MULTIPLY", luz, 0.9), col, (1.0, 0.45, 0.12))
    N.poner("Base Color", col)
    rug = N.mezcla(vientre, 0.68, 0.55)
    rug = N.mezcla(N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, teja), 0.4), rug, 0.85)
    rug = N.mezcla(N.mate("MAXIMUM", boca, luz), rug, 0.3)
    N.poner("Roughness", N.sep(rug)[0])
    h = N.mate("MULTIPLY", teja, N.mate("SUBTRACT", 1.0, N.mate("MULTIPLY", vientre, 0.7)))
    h = N.mate("ADD", h, N.mate("MULTIPLY", N.mate("MULTIPLY", escudos, vientre), 0.7))
    h = N.mate("ADD", h, N.mate("MULTIPLY", costillas, N.mate("MULTIPLY", en_costado, 0.9)))
    h = N.mate("ADD", h, N.mate("MULTIPLY", musculo, 1.2))
    h = N.mate("ADD", h, N.mate("MULTIPLY", cic, 1.4))
    h = N.mate("SUBTRACT", h, N.mate("MULTIPLY", N.mate("MAXIMUM", runas, guerra), 0.8))
    N.poner("Normal", N.relieve(h, fuerza=0.6, distancia=0.03))
    N.poner("Emission Color", N.mezcla(luz, (0, 0, 0), lin("neon")))
    N.poner("Emission Strength", 1.0)
    return mat


def material_membrana():
    """Rojo sangre con venas ramificadas, bordes más claros (translúcidos) y el parche regenerado (ala izquierda)."""
    mat = bpy.data.materials.new("membrana")
    N = T.Nodos(mat)
    P = N.pos()
    a = N.sep(N.atributo("aux").outputs["Vector"])
    px_, py_, pz_ = N.sep(P)
    venas1 = smooth(N, 0.0, 0.05, N.voronoi(P, 2.2, rasgo="DISTANCE_TO_EDGE", aleatorio=0.9))
    venas2 = smooth(N, 0.0, 0.07, N.voronoi(P, 6.0, rasgo="DISTANCE_TO_EDGE", aleatorio=0.9))
    venas = N.mate("MINIMUM", venas1, N.mate("ADD", venas2, 0.35), clamp=True)
    borde = smooth(N, 0.72, 1.0, a[0])
    q = N.vmate("DIVIDE", N.vmate("SUBTRACT", P, (-2.2, 0.9, 2.6)), (1.0, 0.55, 0.4))
    parche = N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, smooth(N, 0.75, 1.1, N.vmate("LENGTH", q))),
                    N.mate("LESS_THAN", px_, 0.0))
    escamitas = N.voronoi(P, 18.0, rasgo="F1")
    col = N.mezcla(borde, lin("membrana"), (0.55, 0.06, 0.05))
    col = N.mezcla(N.mate("SUBTRACT", 1.0, venas), col, (0.12, 0.0, 0.0))
    col = N.mezcla(parche, col, N.mezcla(smooth(N, 0.1, 0.5, escamitas), lin("parche"), (0.3, 0.14, 0.12)))
    N.poner("Base Color", col)
    N.poner("Roughness", N.sep(N.mezcla(parche, 0.34, 0.7))[0])
    h = N.mate("ADD", N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, venas), 0.8),
               N.mate("MULTIPLY", parche, N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, escamitas), 0.8)))
    N.poner("Normal", N.relieve(h, fuerza=0.55, distancia=0.015))
    return mat


def material_degradado(nombre, base, punta, rug=0.25, manchas=False, anillos=0.0):
    """Hueso/garra/diente: color de la base a la punta (aux.x = 0..1 a lo largo), surcos de crecimiento y, en las
    garras de las patas, manchas de sangre seca y arañazos."""
    mat = bpy.data.materials.new(nombre)
    N = T.Nodos(mat)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    col = N.mezcla(smooth(N, 0.45, 1.0, a[0]), lin(base), lin(punta))
    h = N.mate("MULTIPLY", N.ruido(N.pos(), 40.0, 3.0), 0.3)
    if anillos:
        surco = N.mate("ABSOLUTE", N.mate("SINE", N.mate("MULTIPLY", a[0], anillos)))
        h = N.mate("ADD", h, N.mate("MULTIPLY", surco, 0.6))
        col = N.mezcla(N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, surco), 0.25), col, (0.0, 0.0, 0.0))
    if manchas:
        m = N.mate("MULTIPLY", smooth(N, 0.5, 0.62, N.ruido(N.pos(), 9.0, 4.0)), N.mate("SUBTRACT", 1.0, a[0]))
        col = N.mezcla(N.mate("MULTIPLY", m, 0.85), col, lin("sangre"))
        rayas = smooth(N, 0.0, 0.04, N.voronoi(N.vmate("MULTIPLY", N.pos(), (1, 1, 12)), 14.0, rasgo="DISTANCE_TO_EDGE"))
        h = N.mate("SUBTRACT", h, N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, rayas), 0.4))
    N.poner("Base Color", col)
    N.poner("Roughness", rug)
    N.poner("Normal", N.relieve(h, fuerza=0.5, distancia=0.008))
    return mat


def material_cuero(nombre, color):
    mat = bpy.data.materials.new(nombre)
    N = T.Nodos(mat)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    lado = N.mate("MINIMUM", N.mate("ABSOLUTE", N.mate("SUBTRACT", a[1], 0.15)),
                  N.mate("ABSOLUTE", N.mate("SUBTRACT", a[1], 0.85)))
    costura = N.mate("MULTIPLY", N.mate("LESS_THAN", lado, 0.04),
                     N.mate("LESS_THAN", N.mate("FRACT", N.mate("MULTIPLY", a[0], 12.0)), 0.5))
    costura = N.mate("MULTIPLY", costura, N.mate("GREATER_THAN", a[2], 0.5))
    gasto = smooth(N, 0.45, 0.8, N.ruido(N.pos(), 2.5, 4.0))
    col = N.mezcla(N.mate("MULTIPLY", gasto, 0.5), lin(color), (0.09, 0.06, 0.04))
    col = N.mezcla(costura, col, lin("costura"))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.62)
    h = N.mate("ADD", N.mate("MULTIPLY", N.ruido(N.pos(), 45.0, 4.0), 0.3), N.mate("MULTIPLY", costura, 0.5))
    N.poner("Normal", N.relieve(h, fuerza=0.5, distancia=0.01))
    return mat


def materiales():
    lado, frente = mapas()
    m = {"piel": material_piel(lado, frente), "membrana": material_membrana()}
    m["cuerno"] = material_degradado("cuerno", "hueso_os", "#5A4636", rug=0.16, anillos=55.0)
    m["placa"] = material_degradado("placa", "hueso_os", "#4A3828", rug=0.2)
    m["garra"] = material_degradado("garra", "garra", "punta", rug=0.3, manchas=True)
    m["diente"] = material_degradado("diente", "garra", "punta", rug=0.3)
    m["cuero"] = material_cuero("cuero", "cuero")
    m["hueso"], _ = T.material_simple("hueso", lin("hueso"), rug=0.45, relieve=(14.0, 0.35))
    m["hierro"], _ = T.material_simple("hierro", lin("hierro"), rug=0.5, metal=0.85, relieve=(60.0, 0.4))
    mad = bpy.data.materials.new("madera")
    N = T.Nodos(mad)
    vetas = N.ruido(N.vmate("MULTIPLY", N.pos(), (1, 14, 1)), 3.0, 4.0)
    N.poner("Base Color", N.mezcla(smooth(N, 0.35, 0.7, vetas), lin("madera"), (0.05, 0.025, 0.012)))
    N.poner("Roughness", 0.75)
    N.poner("Normal", N.relieve(vetas, fuerza=0.5, distancia=0.01))
    m["madera"] = mad
    m["pupila"], _ = T.material_simple("pupila", (0.003, 0.0, 0.0), rug=0.1)
    iris = bpy.data.materials.new("iris")
    N = T.Nodos(iris)
    p_ = N.sep(N.atributo("aux").outputs["Vector"])
    fib = N.ruido(N.combinar(N.mate("MULTIPLY", p_[1], 70.0), p_[0], 0.0), 2.0, 2.0, 0.4, dim="2D")
    col = N.mezcla(smooth(N, 0.1, 0.95, p_[0]), (1.0, 0.42, 0.05), (0.32, 0.02, 0.0))
    col = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.45, 0.75, fib), 0.4), col, (0.15, 0.0, 0.0))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.25)
    N.poner("Emission Color", col)
    N.poner("Emission Strength", 0.55)
    m["iris"] = iris
    m["lengua"], _ = T.material_simple("lengua", T.srgb("#5A1418"), rug=0.3, relieve=(50.0, 0.4))
    m["cornea"], _ = T.material_simple("cornea", T.srgb("#FF9A70"), rug=0.04)
    return m


# --------------------------------------------------------------------------------------------------------------
# Detalles
# --------------------------------------------------------------------------------------------------------------


def lomo(bvh, y, x=0.0):
    p, n = D.proyectar(bvh, x, y)
    return p, n


def placa_dorsal(g, p, n, alto, largo, grueso):
    """Placa ósea triangular (como cuerno de rinoceronte): hoja con grosor, base hundida en la piel."""
    t1, t2, n = D.marco(n, Vector((0, 1, 0)))
    filas = []
    for s, (anc, ax) in enumerate(((1.0, 0.0), (0.7, 0.45), (0.35, 0.8))):
        h = alto * ax
        filas.append([p + n * (h - 0.06) + t1 * (largo / 2) * anc * math.cos(a) - t1 * 0.18 * ax * largo +
                      t2 * (grueso / 2) * anc * math.sin(a) for a in np.linspace(0, math.tau, 8, endpoint=False)])
    punta = p + n * alto - t1 * largo * 0.3
    g.loft(filas, "placa", auxs=[[(s / 3, 0, 0)] * 8 for s in range(3)], punta_fin=(punta, (1.0, 0, 0)))


def cuerno(g, base, pts, r0):
    pts = [Vector(base)] + [Vector(p) for p in pts]
    curva = C.remuestrear(C.catmull_rom([tuple(p) for p in pts], 6, cerrada=False), 0.09)
    n = len(curva)
    rad = [r0 * (1 - i / (n - 1)) ** 0.85 + 0.012 for i in range(n)]
    g.tubo([Vector(p) for p in curva], rad, "cuerno", lados=8, punta=True,
           aux_fn=lambda t, a: (t, a / math.tau, 0.0),
           perfil=lambda i, a: 1.0 - 0.06 * (i % 2))  # anillos de crecimiento en la geometría


def garra(g, base, dir_, largo, radio, curva, mat="garra"):
    D.cono(g, base, dir_, largo, radio, mat, lados=6, anillos=2, curva=curva,
           aux=(0.0, 0.0, 0.0))
    # aux a lo largo para el degradado negro -> hueso: se reescribe en los vértices recién creados
    return g


def aux_por_eje(g, verts_desde, base, dir_, largo):
    """Rellena aux.x (0 en la base, 1 en la punta) en los vértices añadidos desde el índice dado."""
    g.bm.verts.ensure_lookup_table()
    d = Vector(dir_).normalized()
    for v in g.bm.verts[verts_desde:]:
        t = max(0.0, min(1.0, (v.co - Vector(base)).dot(d) / max(largo, 1e-6)))
        v[g.aux] = Vector((t, 0, 0))


def pieza_puntiaguda(g, base, dir_, largo, radio, mat, curva=None, lados=6, anillos=2, romo=False, achatado=None):
    g.bm.verts.ensure_lookup_table()
    n0 = len(g.bm.verts)
    D.cono(g, base, dir_, largo, radio, mat, lados=lados, anillos=anillos, curva=curva, romo=romo)
    aux_por_eje(g, n0, base, dir_, largo + (Vector(curva).length if curva else 0))
    if achatado:  # hoja aplanada (dientes aserrados)
        g.bm.verts.ensure_lookup_table()
        eje = Vector(achatado).normalized()
        c = Vector(base)
        for v in g.bm.verts[n0:]:
            off = v.co - c
            v.co = c + off - eje * off.dot(eje) * 0.55


def ojo_reptil(g, cornea, c, d):
    """Ojo de 0,6: globo con iris rojo-naranja que brilla, pupila vertical de reptil y córnea convexa."""
    R = F.OJO_R
    t1, t2, d = D.marco(d, Vector((0, 0, 1)))
    alfa = 0.88
    filas = []
    for j in range(6):
        th = math.pi - (math.pi - alfa) * j / 5
        filas.append([c + (t1 * math.cos(math.tau * k / 12) + t2 * math.sin(math.tau * k / 12)) * R * math.sin(th) +
                      d * R * math.cos(th) for k in range(12)])
    vs = g.loft(filas[1:], "piel", tapar_inicio=False, tapar_fin=False, punta_inicio=(c - d * R, (0, 0, 0)))
    plano = c + d * R * math.cos(alfa)
    ri = R * math.sin(alfa)
    aro = [g.v(v.co, (1.0, k / 12, 5.0)) for k, v in enumerate(vs[-1])]
    filas = [aro]
    for f in (0.6, 0.25):
        filas.append([g.v(plano - d * 0.03 * (1 - f) + (t1 * math.cos(math.tau * k / 12) +
                                                        t2 * math.sin(math.tau * k / 12)) * ri * f,
                          (f, k / 12, 5.0)) for k in range(12)])
    for j in range(2):
        for k in range(12):
            k2 = (k + 1) % 12
            g.cara((filas[j][k], filas[j][k2], filas[j + 1][k2], filas[j + 1][k]), "iris")
    cen = g.v(plano - d * 0.03, (0.0, 0.0, 5.0))
    for k in range(12):
        g.cara((filas[-1][k], filas[-1][(k + 1) % 12], cen), "iris")
    # Pupila vertical (rendija en forma de huso), con grosor.
    base = plano - d * 0.02
    pts = [(math.sin(a) * 0.045, math.cos(a) * ri * 0.82) for a in np.linspace(0, math.tau, 10, endpoint=False)]
    sup = [g.v(base + t2 * x + t1 * y + d * (0.022 - 0.02 * abs(y) / ri)) for x, y in pts]
    inf = [g.v(base + t2 * x + t1 * y - d * 0.004) for x, y in pts]
    ca, cb = g.v(base + d * 0.024), g.v(base - d * 0.006)
    for k in range(10):
        k2 = (k + 1) % 10
        g.cara((sup[k], sup[k2], ca), "pupila")
        g.cara((inf[k2], inf[k], cb), "pupila")
        g.cara((inf[k], inf[k2], sup[k2], sup[k]), "pupila")
    # Córnea convexa.
    h0 = R * math.cos(alfa)
    A = R + 0.05
    k_ = (A * A - R * R) / (2 * (A - h0))
    rho = A - k_
    ac = math.acos(max(-1.0, min(1.0, (h0 - k_) / rho)))
    filas = [[c + d * (k_ + rho * math.cos(ac * j / 3)) + (t1 * math.cos(math.tau * k / 12) +
              t2 * math.sin(math.tau * k / 12)) * rho * math.sin(ac * j / 3) for k in range(12)] for j in range(3, 0, -1)]
    cornea.loft(filas, "cornea", punta_fin=(c + d * A, (0, 0, 0)), tapar_inicio=True)


def membrana(g, borde_a, borde_b, filas=6, cols=5, sag=0.12, grosor=0.06, rim=0.1, salida=Vector((1, 0, 0)),
             curva_borde=0.18):
    """Membrana con grosor entre dos huesos (listas de puntos desde la raíz a la punta). El borde libre (de punta a
    punta) se curva hacia dentro como en un murciélago. aux.x = 0 en la raíz -> 1 en el borde libre."""
    A = [Vector(p) for p in borde_a]
    B = [Vector(p) for p in borde_b]

    def en(lst, u):
        f = u * (len(lst) - 1)
        i = min(int(f), len(lst) - 2)
        return lst[i].lerp(lst[i + 1], f - i)

    sup, inf = [], []
    for i in range(filas + 1):
        u = i / filas
        fs, fi = [], []
        for j in range(cols + 1):
            v = j / cols
            pa, pb = en(A, u), en(B, u)
            p = pa.lerp(pb, v)
            # Borde libre: recogido hacia la raíz entre los dedos; abombado suave hacia fuera.
            raiz = A[0].lerp(B[0], v)
            p = p.lerp(raiz, curva_borde * math.sin(math.pi * v) * u ** 2)
            p = p + salida * sag * math.sin(math.pi * v) * math.sin(math.pi * u * 0.9)
            e = grosor / 2 + (rim - grosor) / 2 * max(0.0, (max(u, abs(2 * v - 1)) - 0.8) / 0.2)
            nrm = (pb - pa).cross(en(A, min(1, u + 0.05)) - en(A, max(0, u - 0.05)))
            if nrm.length < 1e-6:
                nrm = salida.copy()
            nrm.normalize()
            if nrm.dot(salida) < 0:
                nrm = -nrm
            aux = (max(u, 0.0) if 0 < j < cols else 0.0, v, 6.0)
            fs.append(g.v(p + nrm * e, aux))
            fi.append(g.v(p - nrm * e, aux))
        sup.append(fs)
        inf.append(fi)
    for i in range(filas):
        for j in range(cols):
            g.cara((sup[i][j], sup[i + 1][j], sup[i + 1][j + 1], sup[i][j + 1]), "membrana")
            g.cara((inf[i][j + 1], inf[i + 1][j + 1], inf[i + 1][j], inf[i][j]), "membrana")
    borde = [(i, 0) for i in range(filas + 1)] + [(filas, j) for j in range(1, cols + 1)] + \
            [(i, cols) for i in range(filas - 1, -1, -1)] + [(0, j) for j in range(cols - 1, 0, -1)]
    for k in range(len(borde)):
        (i1, j1), (i2, j2) = borde[k], borde[(k + 1) % len(borde)]
        g.cara((sup[i1][j1], sup[i2][j2], inf[i2][j2], inf[i1][j1]), "membrana")


def calavera(g, c, adelante, escala, cuernos=True):
    """Calavera de presa (trofeo / hebilla): cráneo, hocico, cuencas y cuernecillos."""
    t1, t2, a = D.marco(adelante, Vector((0, 0, 1)))
    s = escala
    g.elipsoide(c, (0.5 * s, 0.5 * s, 0.45 * s), "hueso", seg=8, anillos=5, rot=D.matriz((t1, t2, a)))
    D.caja(g, c + a * 0.45 * s - t2 * 0.12 * s, (t1, t2, a), (0.42 * s, 0.32 * s, 0.6 * s), "hueso")
    for lado in (1, -1):
        D.disco(g, c + a * 0.38 * s + t1 * 0.2 * s * lado + t2 * 0.08 * s, a + t1 * 0.6 * lado, 0.11 * s, "pupila",
                seg=6, anillos=1, abombado=-0.03 * s)
        if cuernos:
            D.cono(g, c + t1 * 0.38 * s * lado + t2 * 0.2 * s, t1 * lado + t2 * 0.6 - a * 0.4, 0.45 * s, 0.09 * s,
                   "hueso", lados=5, curva=(-a * 0.15 * s))


def cadena(g, puntos, eslabon=0.13):
    """Cadena de eslabones de hueso pulido a lo largo de una curva (eslabones alternos a 90°)."""
    curva = C.remuestrear(np.array([tuple(p) for p in puntos]), eslabon * 1.55)
    for i in range(len(curva) - 1):
        a, b = Vector(curva[i]), Vector(curva[i + 1])
        c = (a + b) / 2
        d = (b - a).normalized()
        ref = Vector((0, 0, 1)) if i % 2 else d.cross(Vector((0, 0, 1)))
        if ref.length < 1e-3:
            ref = Vector((1, 0, 0))
        eje = d.cross(ref).normalized()
        D.toro(g, c, eje, eslabon * 0.5, 0.022, "hueso", seg=6, lados=3, escala_r=(1.0, 1.0))


def contorno_seccion(bvh, y, zc, n=56):
    ps, ns = [], []
    centro = Vector((0, y, zc))
    for t in np.linspace(0, math.tau, n, endpoint=False):
        d = Vector((math.cos(t), 0, math.sin(t)))
        p, nn = D.proyectar_hacia(bvh, centro + d * 5.0, -d, 10.0)
        if p is not None:
            ps.append(p)
            ns.append(nn)
    return ps, ns


def construir(args):
    T.escena_vacia()
    mats = materiales()
    altas = {}
    for nombre in F.PIEZAS:
        t = time.time()
        mn, mx = F.caja(nombre)
        vol, o, p = C.volumen(F.campo_pieza(nombre), mn, mx, F.voxel(nombre) * (1.7 if args.rapido else 1.0))
        v, c = C.malla_de_volumen(vol, o, p)
        ob = T.malla_numpy(nombre + "_alta", v, c)
        T.normales_fuera(ob)
        T.suave(ob)
        T.asignar_material(ob, mats["piel"])
        ob["centro_masa"] = list(C.centro_de_masa(vol, o, p))
        altas[nombre] = ob
        print(f"[forma] {nombre}: {len(c)} tri ({time.time() - t:.1f}s)", flush=True)
    bvh = {n: T.bvh_de([o]) for n, o in altas.items()}
    rnd = random.Random(77)
    det = {}

    # ---------------- Torso: placas dorsales, cincha, sillas, artillero, trofeos ----------------
    g = T.Geo("Torso_det")
    for y, h in ((1.35, 0.5), (0.6, 0.47), (-0.15, 0.42), (-0.9, 0.36), (-1.65, 0.3), (-2.4, 0.24)):
        p, n = lomo(bvh["Torso"], y)
        placa_dorsal(g, p, n, h, 0.5 * (h / 0.5) ** 0.5 + 0.1, 0.13)
    # Cincha de guerra doble con remaches de colmillo.
    ycin = (1.0, 0.62)
    for y in ycin:
        ps, ns = contorno_seccion(bvh["Torso"], y, 2.75)
        lat = [Vector((0, 1, 0))] * len(ps)
        D.cinta(g, ps, ns, 0.24, 0.07, "cuero", cerrada=True, lateral=lat, separacion=0.012)
        for i in range(0, len(ps), 4):
            if ns[i].z > -0.2:
                pieza_puntiaguda(g, ps[i] + ns[i] * 0.07, ns[i], 0.07, 0.025, "diente", lados=4, anillos=1)
    # Hebillas con forma de calavera.
    for lado in (1, -1):
        p, n = D.proyectar(bvh["Torso"], 0.6 * lado, sum(ycin) / 2)
        calavera(g, p + n * 0.16, Vector((0, 0.3, 1)), 0.32, cuernos=False)
    # Silla de combate (piloto): base de hueso curvado, asiento de piel, respaldo bajo y barras de agarre.
    yp = 1.95
    p0, n0 = lomo(bvh["Torso"], yp)
    pr, nr = lomo(bvh["Torso"], yp - 0.55)
    base = p0 + Vector((0, 0, 0.18))
    for lado in (1, -1):  # costillas de hueso que sujetan el asiento
        pts = [base + Vector((0.5 * lado, 0.35, -0.22)), base + Vector((0.62 * lado, 0.0, 0.0)),
               base + Vector((0.55 * lado, -0.45, 0.05)), Vector(pr) + Vector((0.4 * lado, -0.1, 0.2))]
        g.tubo(pts, [0.06, 0.07, 0.07, 0.05], "hueso", lados=6)
    g.caja_redonda(base + Vector((0, -0.05, 0.05)), (1.05, 0.95, 0.2), "cuero", seg=2, aux=(0, 0.5, 1.0),
                   redondeo=0.6)
    g.caja_redonda(base + Vector((0, -0.55, 0.35)), (0.85, 0.16, 0.5), "cuero", seg=2, aux=(0, 0.5, 1.0),
                   redondeo=0.6)  # respaldo bajo
    for lado in (1, -1):  # barras de agarre (cuernos de hueso hacia delante)
        q = [base + Vector((0.36 * lado, 0.42, 0.05)), base + Vector((0.42 * lado, 0.62, 0.35)),
             base + Vector((0.32 * lado, 0.72, 0.52))]
        g.tubo(q, [0.05, 0.045, 0.035], "hueso", lados=6, punta=True)
        # estribos
        ps = [base + Vector((0.55 * lado, 0.0, -0.05)), base + Vector((0.95 * lado, 0.05, -0.55))]
        g.tubo(ps, [0.03, 0.03], "cuero", lados=4)
        D.toro(g, ps[-1] + Vector((0.03 * lado, 0, -0.1)), Vector((0, 1, 0)), 0.12, 0.03, "hueso", seg=10, lados=4)
    piloto = base + Vector((0, -0.05, 0.15 + 0.15))
    # Artillero: 3 studs detrás, disco de madera sobre eje de hueso y barra en U.
    ya = yp - 3.0
    pa, na = lomo(bvh["Torso"], ya)
    eje_base = pa - na * 0.05
    g.tubo([eje_base, eje_base + Vector((0, 0, 0.32))], [0.09, 0.08], "hueso", lados=8)
    disco_c = eje_base + Vector((0, 0, 0.36))
    D.disco(g, disco_c + Vector((0, 0, 0.05)), Vector((0, 0, 1)), 0.62, "madera", seg=16, anillos=2, abombado=0.02)
    D.disco(g, disco_c - Vector((0, 0, 0.0)), Vector((0, 0, -1)), 0.62, "madera", seg=16, anillos=1)
    filas = [[disco_c + Vector((0.62 * math.cos(a), 0.62 * math.sin(a), z)) for a in
              np.linspace(0, math.tau, 16, endpoint=False)] for z in (0.0, 0.05)]
    g.loft(filas, "madera", tapar_inicio=False, tapar_fin=False)
    u = [disco_c + Vector((0.45 * math.cos(a), 0.35 + 0.18 * math.sin(a), 0.05 + 0.55 * (1 - abs(math.cos(a))) * 0 + 0.0))
         for a in np.linspace(0, math.pi, 9)]
    barra = [u[0]] + [p + Vector((0, 0, 0.6)) for p in u] + [u[-1]]
    g.tubo(barra, [0.045] * len(barra), "hueso", lados=6)
    artillero = disco_c + Vector((0, 0, 0.07 + 0.15))
    # Correas que unen la plataforma con la cincha.
    for lado in (1, -1):
        pts, ns = [], []
        for t in np.linspace(0, 1, 8):
            pp, nn = D.proyectar(bvh["Torso"], lado * 0.45, ya + 0.4 + t * (ycin[1] - 0.15 - ya - 0.4))
            pts.append(pp)
            ns.append(nn)
        D.cinta(g, pts, ns, 0.14, 0.05, "cuero", separacion=0.01)
    # Trofeos: dos calaveras de presas atadas a los lados del artillero.
    for lado in (1, -1):
        p, n = D.proyectar_hacia(bvh["Torso"], (3.0 * lado, ya - 0.1, 3.1), (-lado, 0, -0.25), 6.0)
        calavera(g, p + n * 0.28, Vector((0.3 * lado, 0.2, -1)), 0.5)
        g.tubo([p + n * 0.05 + Vector((0, 0, 0.35)), p + n * 0.2 + Vector((0, 0, 0.18))], [0.025, 0.025], "cuero",
               lados=4)
    # Colmillo grande como pendiente, colgando del pecho bajo la cincha.
    p, n = D.proyectar_hacia(bvh["Torso"], (0, 4.0, 2.0), (0, -1, 0), 6.0)
    cuerda = [p + n * 0.03 + Vector((0, 0, 0.25)), p + n * 0.12, p + n * 0.1 + Vector((0, 0, -0.2))]
    g.tubo(cuerda, [0.02] * 3, "cuero", lados=4)
    pieza_puntiaguda(g, cuerda[-1], Vector((0, 0.25, -1)), 0.55, 0.08, "diente", curva=Vector((0, 0.12, 0)),
                     lados=6, anillos=2)
    det["Torso"] = [g.objeto(mats)]

    # ---------------- Cuello: espinas, anillos perforados, cadenas ----------------
    g = T.Geo("Cuello_det")
    anillos_c = []
    for i, t in enumerate((0.12, 0.3, 0.48, 0.66, 0.84)):
        k = t * (len(F.CUELLO) - 1)
        a, b = Vector(F.CUELLO[int(k)]), Vector(F.CUELLO[min(int(k) + 1, 4)])
        c = a.lerp(b, k - int(k))
        tang = (b - a).normalized()
        arriba = Vector((0, -tang.z, tang.y)).normalized()
        p, n = D.proyectar_hacia(bvh["Cuello"], c + arriba * 2.0, -arriba, 3.0)
        h = 0.42 - 0.05 * i
        pieza_puntiaguda(g, p - n * 0.03, n - tang * 0.6, h, 0.075, "placa", curva=-tang * 0.06, lados=5)
        if i in (1, 2, 3):
            centro = p + n * 0.14 - tang * 0.03
            D.toro(g, centro, Vector((1, 0, 0)), 0.09, 0.022, "hueso", seg=10, lados=4)
            anillos_c.append(centro)
    for lado in (1, -1):
        ini = piloto + Vector((0.32 * lado, 0.75, 0.55))
        fin = anillos_c[0] + Vector((0.07 * lado, 0, -0.05))
        medio = (ini + fin) / 2 + Vector((0.25 * lado, 0, -0.25))
        cadena(g, C.catmull_rom([tuple(ini), tuple(medio), tuple(fin)], 8, cerrada=False))
    det["Cuello"] = [g.objeto(mats)]

    # ---------------- Cabeza: cuernos, ojos, dientes superiores ----------------
    g = T.Geo("Cabeza_det")
    cor = T.Geo("Ojos_Cornea")
    dz = F.DZ
    for lado in (1, -1):
        cuerno(g, (0.32 * lado, 4.78, 6.33 + dz),
               [(0.42 * lado, 4.35, 6.72 + dz), (0.54 * lado, 3.92, 7.05 + dz), (0.6 * lado, 3.45, 7.22 + dz),
                (0.58 * lado, 3.05, 7.2 + dz)], 0.21)
        ojo_reptil(g, cor, Vector((lado * F.OJO[0], F.OJO[1], F.OJO[2])), Vector((lado, 0.42, 0.15)))
    for lado in (1, -1):  # borde de la visera irregular, como hueso roto
        for k, (y, l) in enumerate(((5.45, 0.16), (5.22, 0.22), (4.98, 0.13), (4.75, 0.19))):
            p, n = D.proyectar_hacia(bvh["Cabeza"], (lado * 1.5, y, 6.42 + dz), (-lado, 0, -0.15), 2.0)
            if p is not None and p.z > 6.3 + dz:
                pieza_puntiaguda(g, p - n * 0.03, n + Vector((0, -0.4, 0.2)), l, 0.05, "placa", lados=4, anillos=1)
    bc = Vector(F.BOCA[0])
    for lado in (1, -1):
        # Colmillo superior (visible con la boca cerrada: cae por fuera de la mandíbula).
        p, n = D.proyectar_hacia(bvh["Cabeza"], (0.24 * lado, 6.15, bc.z + 0.02), (0, 0, 1), 1.0)
        pieza_puntiaguda(g, p + Vector((0.035 * lado, 0, 0.03)), Vector((0.12 * lado, 0.12, -1)), 0.32, 0.055,
                         "diente", curva=Vector((0, -0.05, 0)), lados=6, anillos=2)
        for k in range(4):  # 4 aserrados arriba por lado
            y = 6.45 - 0.33 * (k + (1 if k >= 1 else 0)) * 0.7 - (0.0 if k == 0 else 0.25)
            p, n = D.proyectar_hacia(bvh["Cabeza"], (0.22 * lado, y, bc.z + 0.02), (0, 0, 1), 1.0)
            if p is None:
                continue
            pieza_puntiaguda(g, p + Vector((0, 0, 0.02)), Vector((0.05 * lado, 0.1, -1)), 0.13, 0.04, "diente",
                             lados=4, anillos=1, achatado=Vector((lado, 0, 0)))
    det["Cabeza"] = [g.objeto(mats)]
    cornea = cor.objeto(mats)

    # ---------------- Mandíbula: colmillos, dientes inferiores, lengua bífida, púas ----------------
    g = T.Geo("Mandibula_det")
    for lado in (1, -1):
        p, n = D.proyectar_hacia(bvh["Mandibula"], (0.22 * lado, 5.95, bc.z - 0.02), (0, 0, -1), 1.0)
        pieza_puntiaguda(g, p - Vector((-0.04 * lado, 0, 0.03)), Vector((0.1 * lado, 0.1, 1)), 0.3, 0.05, "diente",
                         curva=Vector((0, -0.05, 0)), lados=6, anillos=2)
        for k in range(4):
            y = 6.3 - 0.27 * k - (0.25 if k >= 1 else 0.0)
            p, n = D.proyectar_hacia(bvh["Mandibula"], (0.2 * lado, y, bc.z - 0.02), (0, 0, -1), 1.0)
            if p is None:
                continue
            pieza_puntiaguda(g, p - Vector((0, 0, 0.02)), Vector((0.05 * lado, 0.1, 1)), 0.12, 0.038, "diente",
                             lados=4, anillos=1, achatado=Vector((lado, 0, 0)))
        # Púas de la barbilla (como un lagarto cornudo).
        p, n = D.proyectar_hacia(bvh["Mandibula"], (0.13 * lado, 5.7, bc.z - 1.0), (0, 0, 1), 1.5)
        pieza_puntiaguda(g, p + n * -0.02, Vector((0.2 * lado, 0.35, -1)), 0.22, 0.05, "placa", lados=5)
    # Lengua bífida corta sobre el suelo de la boca.
    p, n = D.proyectar_hacia(bvh["Mandibula"], (0, 5.2, bc.z), (0, 0, -1), 1.0)
    base = p + Vector((0, 0, 0.025))
    g.tubo([base, base + Vector((0, 0.45, 0.0))], [0.07, 0.05], "lengua", lados=6, achatado=0.4)
    for lado in (1, -1):
        g.tubo([base + Vector((0, 0.44, 0)), base + Vector((0.07 * lado, 0.68, 0.0))], [0.035, 0.012], "lengua",
               lados=5, achatado=0.5, punta=True)
    det["Mandibula"] = [g.objeto(mats)]

    # ---------------- Alas: membranas, garra del pulgar ----------------
    for lado, nom in ((1, "Der"), (-1, "Izq")):
        s = (lambda p: Vector(p)) if lado > 0 else (lambda p: Vector(F.esp(p)))
        H, E, W = s(F.HOMBRO), s(F.CODO), s(F.MUNECA)
        dedos = [s(d) for d in F.DEDOS]
        sal = Vector((lado, 0, 0))
        g = T.Geo(f"Ala_{nom}_Mano_det")
        for a, b in ((0, 1), (1, 2)):
            membrana(g, [W, W.lerp(dedos[a], 0.5), dedos[a]], [W, W.lerp(dedos[b], 0.5), dedos[b]], sag=0.1,
                     salida=sal, grosor=0.05, rim=0.1, curva_borde=0.22)
        # Garra del pulgar: dedo libre en el nudillo de la muñeca.
        dp = (Vector((0.15 * lado, 0.7, 0.55))).normalized()
        g.tubo([W + dp * 0.12, W + dp * 0.4], [0.07, 0.055], "piel", lados=6)
        pieza_puntiaguda(g, W + dp * 0.38, dp + Vector((0, 0.3, -0.5)), 0.4, 0.06, "garra",
                         curva=Vector((0, 0.08, -0.15)), lados=6, anillos=2)
        det[f"Ala_{nom}_Mano"] = [g.objeto(mats)]
        g = T.Geo(f"Ala_{nom}_Antebrazo_det")
        # Membrana del brazo: del antebrazo al último dedo, plegada sobre el costado (no toca la piel).
        borde_b = [E.lerp(W, 0.15) + Vector((0, -0.25, -0.75)), dedos[2] + Vector((-0.05 * lado, -0.3, 0.12))]
        membrana(g, [E.lerp(W, 0.12), E.lerp(W, 0.85)], [borde_b[0], borde_b[1]], filas=4, cols=4, sag=0.08,
                 salida=sal, grosor=0.05, rim=0.09, curva_borde=0.05)
        det[f"Ala_{nom}_Antebrazo"] = [g.objeto(mats)]
        g = T.Geo(f"Ala_{nom}_Hombro_det")
        membrana(g, [H.lerp(E, 0.25), E], [H.lerp(E, 0.2) + Vector((0, 0.35, -0.05)), E + Vector((0.02 * lado, 0.55, -0.12))],
                 filas=3, cols=3, sag=0.05, salida=sal + Vector((0, 0, 0.3)), grosor=0.05, rim=0.08, curva_borde=0.1)
        det[f"Ala_{nom}_Hombro"] = [g.objeto(mats)]

        # ---------------- Patas: garras manchadas ----------------
        g = T.Geo(f"Pata_{nom}_Tibia_det")
        Fp = s(F.PIE)
        for dx, dy in ((-0.30, 0.82), (0.0, 0.98), (0.30, 0.80)):
            punta = Vector((Fp.x + dx * lado, Fp.y + dy, 0.11))
            pieza_puntiaguda(g, punta - Vector((0, 0.06, -0.02)), Vector((dx * lado * 0.3, 1, -0.35)), 0.3, 0.075,
                             "garra", curva=Vector((0, 0.02, -0.1)), lados=6, anillos=2)
        esp_p = Vector((Fp.x, Fp.y - 0.45, 0.13))
        pieza_puntiaguda(g, esp_p, Vector((0, -1, -0.2)), 0.26, 0.06, "garra", curva=Vector((0, -0.02, -0.08)),
                         lados=6, anillos=2)
        det[f"Pata_{nom}_Tibia"] = [g.objeto(mats)]

    # ---------------- Cola: escamas largas (normal map) y cresta ventral de 8 espinas ----------------
    tramos = {"Cola_Base": (-3.6, -4.9, 3), "Cola_Media": (-5.2, -6.5, 3), "Cola_Punta": (-6.85, -7.4, 2)}
    for pieza, (ya_, yb_, n_) in tramos.items():
        g = T.Geo(pieza + "_det")
        for y in np.linspace(ya_, yb_, n_):
            p, n = D.proyectar(bvh[pieza], 0.0, y, abajo=True)
            if p is None:
                continue
            pieza_puntiaguda(g, p + n * -0.03, n + Vector((0, -0.7, 0)), 0.42 + 0.03 * (y + 3.6), 0.085,
                             "placa", lados=5, curva=Vector((0, -0.06, 0)))
        det[pieza] = [g.objeto(mats)]

    return altas, det, cornea, mats, piloto, artillero


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="1")
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    altas, det, cornea, mats, piloto, artillero = construir(args)

    pivotes = {"Torso": (0.0,) + tuple(altas["Torso"]["centro_masa"])[1:], "Cuello": F.CUELLO[0],
               "Cabeza": F.ARTIC_CABEZA, "Mandibula": F.BISAGRA, "Cola_Base": F.COLA[0], "Cola_Media": F.COLA[1],
               "Cola_Punta": F.COLA[2], "Ojos_Cornea": F.ARTIC_CABEZA}
    padre = {"Torso": None, "Cuello": "Torso", "Cabeza": "Cuello", "Mandibula": "Cabeza", "Cola_Base": "Torso",
             "Cola_Media": "Cola_Base", "Cola_Punta": "Cola_Media", "Ojos_Cornea": "Cabeza"}
    for lado, nom in ((1, "Der"), (-1, "Izq")):
        s = (lambda p: p) if lado > 0 else F.esp
        pivotes[f"Ala_{nom}_Hombro"] = s(F.HOMBRO)
        pivotes[f"Ala_{nom}_Antebrazo"] = s(F.CODO)
        pivotes[f"Ala_{nom}_Mano"] = s(F.MUNECA)
        pivotes[f"Pata_{nom}_Muslo"] = s(F.CADERA)
        pivotes[f"Pata_{nom}_Tibia"] = s(F.RODILLA)
        padre.update({f"Ala_{nom}_Hombro": "Torso", f"Ala_{nom}_Antebrazo": f"Ala_{nom}_Hombro",
                      f"Ala_{nom}_Mano": f"Ala_{nom}_Antebrazo", f"Pata_{nom}_Muslo": "Torso",
                      f"Pata_{nom}_Tibia": f"Pata_{nom}_Muslo"})
    # Puntos de montaje.
    bc = T.bvh_de([altas["Cuello"]])
    montajes = {"Montura_Piloto": (piloto, "Torso"), "Montura_Artillero": (artillero, "Torso")}
    medio = Vector(F.CUELLO[2])
    for lado, nom in ((-1, "Agarre_Cuello_Izq"), (1, "Agarre_Cuello_Der")):
        p, n = D.proyectar_hacia(bc, medio + Vector((3.0 * lado, 0, 0)), (-lado, 0, 0), 5.0)
        montajes[nom] = (p + n * 0.15, "Cuello")
    montajes["Punto_Ataque"] = (Vector((0, 7.02, 5.80 + F.DZ)), "Cabeza")

    vidrio = bpy.data.materials.new("cornea_render")
    N = T.Nodos(vidrio)
    N.poner("Base Color", T.srgb("#FFD0B0"))
    N.poner("Roughness", 0.02)
    N.poner("Transmission Weight", 1.0)
    orden = ["Torso", "Cuello", "Cabeza", "Mandibula"] + [f"Ala_{l}_{p}" for l in ("Izq", "Der")
                                                          for p in ("Hombro", "Antebrazo", "Mano")] + \
            [f"Pata_{l}_{p}" for l in ("Izq", "Der") for p in ("Muslo", "Tibia")] + \
            ["Cola_Base", "Cola_Media", "Cola_Punta"]
    peso = {"Torso": 2.6, "Cuello": 1.0, "Cabeza": 1.7, "Mandibula": 0.6, "Cola_Base": 0.5, "Cola_Media": 0.4,
            "Cola_Punta": 0.7}
    for l in ("Izq", "Der"):
        peso.update({f"Ala_{l}_Hombro": 0.3, f"Ala_{l}_Antebrazo": 0.3, f"Ala_{l}_Mano": 0.45,
                     f"Pata_{l}_Muslo": 0.55, f"Pata_{l}_Tibia": 0.8})
    dz = F.DZ
    cfg = dict(
        nombre=NOMBRE, titulo="DRAGÓN DEL VACÍO", rol="Combate aéreo", jinetes="1 piloto + 1 artillero",
        neon=["#FF4500"], presupuesto=PRESUPUESTO, salida=args.salida, ronda=args.ronda, rapido=args.rapido,
        altas=altas, detalles=det, soldadas={"Ojos_Cornea": (cornea, "Cabeza")}, peso_tris=peso, pivotes=pivotes,
        padre=padre, orden=orden, montajes=montajes,
        prioridad_uv={"Cabeza": 1.5, "Mandibula": 1.3, "Torso": 1.1, "Cuello": 1.15, "Ojos_Cornea": 1.5,
                      "Ala_Izq_Mano": 0.8, "Ala_Der_Mano": 0.8, "Ala_Izq_Antebrazo": 0.8, "Ala_Der_Antebrazo": 0.8},
        render_material={cornea: vidrio}, radio_estudio=9.0, exposicion=1.3,
        cerca=[("Cabeza 3/4", 40, 15, (0, 5.4, 6.2), 1.9), ("Ojo y cuerno", 75, 10, (0.5, 4.6, 6.7), 1.0),
               ("Boca (dientes)", 20, -5, (0, 5.9, 6.1), 1.1), ("Silla y artillero", 140, 35, (0, 0.3, 3.9), 2.6),
               ("Garras", 30, 10, (1.2, -1.6, 0.4), 1.0), ("Maza de la cola", 150, 20, (0, -7.6, 2.5), 1.4)],
        notas_json=["Ojos_Cornea va soldada a la Cabeza: en Roblox, material Glass o Transparency 0,35.",
                    "Alas en reposo plegadas: las membranas son rígidas por pieza (Mano, Antebrazo, Hombro)."],
        json_extra={"envergadura_abierta_studs": 14.0},
    )
    bestia.terminar(cfg)


if __name__ == "__main__":
    main()
