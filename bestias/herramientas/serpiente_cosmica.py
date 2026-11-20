"""
BESTIA 3 — SERPIENTE CÓSMICA (transporte / asedio, 4-6 jinetes).

Anaconda cruzada con anguila eléctrica, de 30 studs: lomo verde oscuro iridiscente con escamas grandes en teja,
vientre beige con placas ventrales, 15 anillos musculares, cresta dorsal púrpura que brilla, 4 aletas laterales con
radios óseos, cola en remo. Es ANTIGUA: parásitos fosilizados en las escamas traseras, cicatrices de arpón y las
runas de la veneración en su escudo frontal.

Rig (14 piezas): Segmento_1 (raíz, pivote en su extremo delantero), Cabeza, Mandibula, Segmento_2..6, Cola_Punta,
Aleta_{Izq,Der}_{1,2}, Cresta_Dorsal. Soldada a la Cabeza: Ojos_Cornea.
Montaje: Montura_1..6 y Punto_Carga.

Uso: python bestias/herramientas/serpiente_cosmica.py --salida bestias/serpiente_cosmica --ronda 1 [--rapido]
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

import bestia  # noqa: E402
import campos as C  # noqa: E402
import detalles as D  # noqa: E402
import serpiente_forma as F  # noqa: E402
import taller as T  # noqa: E402

NOMBRE = "serpiente_cosmica"
PRESUPUESTO = 20000
COL = {
    "lomo": "#0A2E1A", "reflejo": "#1A4A2E", "lateral": "#0D3B2E", "vientre": "#D4C8A0", "cresta": "#9B59B6",
    "aleta": "#4A1A6B", "ojo": "#39FF14", "cuero": "#3E3022", "hueso": "#E8DCC8", "fibra": "#8A7A4A",
    "tela": "#8A7560", "costura": "#B8A27A", "cicatriz": "#5E6A4E", "boca": "#6A3040",
}
ASIENTOS = [6.0, 3.0, 1.0, -1.0, -3.0, -6.0]       # Montura_1..6
SEGMENTO_DE_ASIENTO = [2, 3, 3, 4, 4, 5]
CINCHAS = [6.0, 2.0, -2.0]                          # en los segmentos 2, 3 y 4
ALETAS = {"1": 6.0, "2": -2.0}                      # Aleta_*_1 en Segmento_2; Aleta_*_2 en Segmento_4
CRESTA = (11.4, -11.2)


def lin(h):
    return T.srgb(COL.get(h, h))


def smooth(N, a, b, x):
    m = N.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
    m.inputs["From Min"].default_value = a
    m.inputs["From Max"].default_value = b
    N.enlazar(x, m.inputs["Value"])
    return m.outputs["Result"]


def segmento(y):
    """Pieza del cuerpo que contiene la coordenada y."""
    if y >= F.CORTES[0]:
        return "Cabeza"
    for i in range(1, 7):
        if y >= F.CORTES[i]:
            return f"Segmento_{i}"
    return "Cola_Punta"


# --------------------------------------------------------------------------------------------------------------
# Materiales
# --------------------------------------------------------------------------------------------------------------


def material_piel():
    mat = bpy.data.materials.new("piel")
    N = T.Nodos(mat)
    P = N.pos()
    px_, py_, pz_ = N.sep(P)
    nx_, ny_, nz_ = N.sep(N.normal())
    vientre = N.mate("SUBTRACT", 1.0, smooth(N, -0.55, -0.1, nz_))
    lateral = smooth(N, 0.55, 0.9, N.mate("ABSOLUTE", nx_))
    # Escamas grandes en teja (0,3): cúpulas de Voronoi en coordenadas estiradas a lo largo del cuerpo.
    esc = N.voronoi(N.vmate("MULTIPLY", P, (1.0, 0.8, 1.0)), 3.4, rasgo="F1", aleatorio=0.25)
    teja = N.mate("SUBTRACT", 1.0, smooth(N, 0.0, 0.62, esc))
    # Placas ventrales anchas y anillos musculares cada 2 studs.
    placas = smooth(N, 0.0, 0.18, N.mate("ABSOLUTE", N.mate("SINE", N.mate("MULTIPLY", py_, 9.0))))
    d = N.mate("PINGPONG", N.mate("ADD", py_, 1000.0), 1.0)
    anillo = N.mate("SUBTRACT", 1.0, smooth(N, 0.0, 0.12, d))
    # Línea lateral luminosa (puntos púrpura a media altura) y los bordes del remo de la cola.
    altura = N.mate("ABSOLUTE", N.mate("SUBTRACT", pz_, F.ZC + 0.05))
    linea = N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, smooth(N, 0.03, 0.09, altura)), lateral)
    puntos = N.mate("LESS_THAN", N.mate("PINGPONG", N.mate("MULTIPLY", py_, 1.0), 0.5), 0.12)
    luz = N.mate("MULTIPLY", linea, puntos)
    luz = N.mate("MULTIPLY", luz, N.mate("LESS_THAN", py_, 11.5))
    remo = N.mate("MULTIPLY", N.mate("LESS_THAN", py_, -12.4),
                  smooth(N, 0.62, 0.86, N.mate("ABSOLUTE", px_)))
    remo = N.mate("MULTIPLY", remo, N.mate("LESS_THAN", N.mate("PINGPONG", py_, 0.3), 0.16))
    luz = N.mate("MAXIMUM", luz, remo)
    # Cicatrices de arpón en el flanco izquierdo (segmentos 4 y 5).
    q = N.mate("ADD", N.mate("MULTIPLY", py_, 0.8), pz_)
    cic = N.mate("MULTIPLY", N.mate("LESS_THAN", N.mate("PINGPONG", N.mate("ADD", q, 0.0), 0.7), 0.05),
                 N.mate("MULTIPLY", N.mate("LESS_THAN", px_, -0.9),
                        N.mate("MULTIPLY", smooth(N, -7.2, -6.8, py_), N.mate("LESS_THAN", py_, -3.2))))
    cic = N.mate("MULTIPLY", cic, N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("SUBTRACT", pz_, 1.35)), 0.35))
    # Boca.
    bc, br = F.CAVIDAD
    qq = N.vmate("DIVIDE", N.vmate("SUBTRACT", P, bc), (br[0] * 1.1, br[1] * 1.05, br[2] * 2.2))
    boca = N.mate("SUBTRACT", 1.0, smooth(N, 0.9, 1.02, N.vmate("LENGTH", qq)))
    irid = smooth(N, 0.3, 0.75, N.ruido(P, 0.6, 3.0))
    col = N.mezcla(irid, lin("lomo"), lin("reflejo"))
    col = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.55, 0.7, N.ruido(P, 2.5, 2.0)), 0.5), col, (0.02, 0.06, 0.09))
    col = N.mezcla(lateral, col, lin("lateral"))
    col = N.mezcla(N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, teja), 0.55), col, (0.0, 0.004, 0.002))
    vcol = N.mezcla(N.mate("MULTIPLY", placas, 0.35), lin("vientre"), (0.25, 0.2, 0.1))
    col = N.mezcla(vientre, col, vcol)
    col = N.mezcla(N.mate("MULTIPLY", anillo, 0.6), col, (0.0, 0.01, 0.005))
    col = N.mezcla(cic, col, lin("cicatriz"))
    col = N.mezcla(boca, col, lin("boca"))
    col = N.mezcla(N.mate("MULTIPLY", luz, 0.9), col, (0.85, 0.55, 1.0))
    N.poner("Base Color", col)
    N.poner("Roughness", N.sep(N.mezcla(vientre, N.mezcla(teja, 0.62, 0.45), 0.5))[0])
    h = N.mate("MULTIPLY", teja, N.mate("SUBTRACT", 1.0, vientre))
    h = N.mate("ADD", h, N.mate("MULTIPLY", placas, N.mate("MULTIPLY", vientre, 0.6)))
    h = N.mate("SUBTRACT", h, N.mate("MULTIPLY", anillo, 0.9))
    h = N.mate("ADD", h, N.mate("MULTIPLY", cic, 1.2))
    N.poner("Normal", N.relieve(h, fuerza=0.6, distancia=0.035))
    N.poner("Emission Color", N.mezcla(luz, (0, 0, 0), lin("cresta")))
    N.poner("Emission Strength", 1.0)
    return mat


def material_membrana(nombre, color, brillo):
    """Membrana púrpura semitranslúcida con nervios radiales (aux.y = posición entre radios)."""
    mat = bpy.data.materials.new(nombre)
    N = T.Nodos(mat)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    nervios = smooth(N, 0.0, 0.05, N.mate("PINGPONG", N.mate("MULTIPLY", a[1], 12.0), 0.5))
    borde = smooth(N, 0.7, 1.0, a[0])
    col = N.mezcla(N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, nervios), 0.5), lin(color), (0.12, 0.03, 0.2))
    col = N.mezcla(N.mate("MULTIPLY", borde, 0.7), col, lin("cresta"))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.3)
    N.poner("Normal", N.relieve(N.mate("SUBTRACT", 1.0, nervios), fuerza=0.5, distancia=0.01))
    if brillo:
        N.poner("Emission Color", N.mezcla(N.mate("ADD", N.mate("MULTIPLY", borde, 0.7), 0.15), (0, 0, 0),
                                           lin("cresta")))
        N.poner("Emission Strength", brillo)
    return mat


def material_escudo():
    """Escama frontal: escudo con grabado fractal y 3 runas concéntricas que brillan (aux = radio, ángulo)."""
    mat = bpy.data.materials.new("escudo")
    N = T.Nodos(mat)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    anillos = N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("SUBTRACT", N.mate("PINGPONG", a[0], 0.14), 0.07)), 0.018)
    anillos = N.mate("MULTIPLY", anillos, N.mate("LESS_THAN", a[0], 0.84))
    marcas = N.mate("LESS_THAN", N.mate("PINGPONG", N.mate("MULTIPLY", a[1], 18.0), 0.5), 0.12)
    runas = N.mate("MAXIMUM", anillos, N.mate("MULTIPLY", marcas, N.mate("MULTIPLY", smooth(N, 0.15, 0.2, a[0]),
                                                                       N.mate("LESS_THAN", a[0], 0.62))))
    fractal = N.ruido(N.pos(), 18.0, 8.0, 0.75)
    col = N.mezcla(smooth(N, 0.4, 0.7, fractal), (0.04, 0.12, 0.08), (0.12, 0.22, 0.14))
    col = N.mezcla(runas, col, (0.85, 0.6, 1.0))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.35)
    N.poner("Normal", N.relieve(N.mate("ADD", fractal, N.mate("MULTIPLY", runas, -0.6)), fuerza=0.5, distancia=0.01))
    N.poner("Emission Color", N.mezcla(runas, (0, 0, 0), lin("cresta")))
    N.poner("Emission Strength", 1.0)
    return mat


def material_tela():
    """Estandarte de piel curtida con el símbolo tribal: un ojo con tentáculos (aux = u, v de la tela)."""
    mat = bpy.data.materials.new("tela")
    N = T.Nodos(mat)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    u = N.mate("SUBTRACT", a[1], 0.5)
    v = N.mate("SUBTRACT", a[0], 0.38)
    r = N.vmate("LENGTH", N.combinar(N.mate("MULTIPLY", u, 1.6), v, 0.0))
    ojo = N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("SUBTRACT", r, 0.2)), 0.04)
    pupila = N.mate("LESS_THAN", r, 0.08)
    onda = N.mate("ADD", N.mate("MULTIPLY", N.mate("SINE", N.mate("MULTIPLY", a[0], 22.0)), 0.04), u)
    tent = N.mate("MULTIPLY", N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("PINGPONG", N.mate("ADD", onda, 1.0), 0.13)),
                                     0.022), N.mate("GREATER_THAN", a[0], 0.58))
    tent = N.mate("MULTIPLY", tent, N.mate("LESS_THAN", N.mate("ABSOLUTE", u), 0.3))
    marca = N.mate("MAXIMUM", N.mate("MAXIMUM", ojo, pupila), tent)
    cuero = N.mezcla(smooth(N, 0.4, 0.75, N.ruido(N.pos(), 6.0, 4.0)), lin("tela"), (0.35, 0.27, 0.19))
    col = N.mezcla(marca, cuero, (0.03, 0.02, 0.02))
    col = N.mezcla(N.mate("MULTIPLY", ojo, 0.0), col, (0.4, 0.02, 0.02))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.8)
    N.poner("Normal", N.relieve(N.ruido(N.pos(), 30.0, 4.0), fuerza=0.3, distancia=0.01))
    return mat


def material_cuero():
    mat = bpy.data.materials.new("cuero")
    N = T.Nodos(mat)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    lado = N.mate("MINIMUM", N.mate("ABSOLUTE", N.mate("SUBTRACT", a[1], 0.15)),
                  N.mate("ABSOLUTE", N.mate("SUBTRACT", a[1], 0.85)))
    costura = N.mate("MULTIPLY", N.mate("LESS_THAN", lado, 0.04),
                     N.mate("LESS_THAN", N.mate("FRACT", N.mate("MULTIPLY", a[0], 12.0)), 0.5))
    costura = N.mate("MULTIPLY", costura, N.mate("GREATER_THAN", a[2], 0.5))
    col = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.45, 0.8, N.ruido(N.pos(), 2.5, 4.0)), 0.5), lin("cuero"),
                   (0.12, 0.1, 0.06))
    col = N.mezcla(costura, col, lin("costura"))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.65)
    N.poner("Normal", N.relieve(N.mate("ADD", N.mate("MULTIPLY", N.ruido(N.pos(), 45.0, 4.0), 0.3),
                                       N.mate("MULTIPLY", costura, 0.5)), fuerza=0.5, distancia=0.01))
    return mat


def materiales():
    m = {"piel": material_piel(), "cresta": material_membrana("cresta", "#5B2C87", 0.8),
         "aleta": material_membrana("aleta", "aleta", 0.0), "escudo": material_escudo(), "tela": material_tela(),
         "cuero": material_cuero()}
    m["hueso"], _ = T.material_simple("hueso", lin("hueso"), rug=0.45, relieve=(14.0, 0.35))
    m["fibra"], _ = T.material_simple("fibra", lin("fibra"), rug=0.85, relieve=(80.0, 0.6))
    m["diente"], _ = T.material_simple("diente", T.srgb("#E6DCC0"), rug=0.3)
    m["lengua"], _ = T.material_simple("lengua", T.srgb("#3A1030"), rug=0.3)
    m["esclera"], _ = T.material_simple("esclera", T.srgb("#0E1A0E"), rug=0.25)
    m["pupila"], _ = T.material_simple("pupila", (0.002, 0.003, 0.002), rug=0.1)
    m["membrana_ojo"], _ = T.material_simple("membrana_ojo", T.srgb("#8AA08A"), rug=0.3)
    m["cornea"], _ = T.material_simple("cornea", T.srgb("#C8FFC0"), rug=0.04)
    m["fosil"], _ = T.material_simple("fosil", T.srgb("#6E6A58"), rug=0.9, relieve=(40.0, 0.9))
    iris = bpy.data.materials.new("iris")
    N = T.Nodos(iris)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    fib = N.ruido(N.combinar(N.mate("MULTIPLY", a[1], 70.0), a[0], 0.0), 2.0, 2.0, 0.4, dim="2D")
    col = N.mezcla(smooth(N, 0.1, 0.95, a[0]), (0.55, 1.0, 0.3), (0.03, 0.25, 0.02))
    col = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.45, 0.75, fib), 0.4), col, (0.0, 0.08, 0.0))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.25)
    N.poner("Emission Color", col)
    N.poner("Emission Strength", 0.6)
    m["iris"] = iris
    return m


# --------------------------------------------------------------------------------------------------------------
# Detalles
# --------------------------------------------------------------------------------------------------------------


def contorno(bvh, y, n=52):
    ps, ns = [], []
    centro = Vector((0, y, F.ZC))
    for t in np.linspace(0, math.tau, n, endpoint=False):
        d = Vector((math.cos(t), 0, math.sin(t)))
        p, nn = D.proyectar_hacia(bvh, centro + d * 4.0, -d, 8.0)
        if p is not None:
            ps.append(p)
            ns.append(nn)
    return ps, ns


def hebilla_espiral(g, c, n, escala=0.12):
    """Hebilla de hueso en espiral (como una concha)."""
    t1, t2, n = D.marco(n)
    pts, rad = [], []
    for k in range(18):
        a = k * 0.62
        r = escala * (1 - k / 22)
        pts.append(c + t1 * math.cos(a) * r + t2 * math.sin(a) * r + n * (0.03 + 0.012 * k / 18))
        rad.append(0.028 * (1 - k / 26))
    g.tubo(pts, rad, "hueso", lados=4, punta=True)


def parasito_fosil(g, p, n, rnd):
    t1, t2, n = D.marco(n)
    s = rnd.uniform(0.8, 1.3)
    filas = []
    for (r, h) in ((0.08, -0.03), (0.075, 0.015), (0.05, 0.06), (0.03, 0.05), (0.012, 0.02)):
        filas.append([p + (t1 * math.cos(math.tau * k / 6) + t2 * math.sin(math.tau * k / 6)) * r * s * rnd.uniform(0.85, 1.1)
                      + n * h * s for k in range(6)])
    g.loft(filas, "fosil")


def aleta(g, bvh, y, lado, rnd):
    """Aleta lateral triangular redondeada (2 × 1,5) con 3 radios óseos y borde ondulado. Devuelve el pivote."""
    base = []
    for t in np.linspace(0, 1, 6):
        yy = y + 0.75 - 1.5 * t
        p, n = D.proyectar_hacia(bvh, (lado * 4.0, yy, F.ZC - 0.25), (-lado, 0, 0), 6.0)
        base.append(p + n * 0.03)
    fuera = Vector((lado * math.cos(math.radians(22)), -0.25, -math.sin(math.radians(22)))).normalized()
    rej = []
    for i, u in enumerate(np.linspace(0, 1, 5)):
        fila = []
        for j, t in enumerate(np.linspace(0, 1, 6)):
            largo = 2.0 * (math.sin(math.pi * (0.15 + 0.85 * t)) ** 0.7) * (1 - 0.35 * t)
            onda = 0.07 * math.sin(t * 9.0) * u ** 2
            fila.append(base[j] + fuera * largo * u + Vector((0, -0.35 * u * u, onda)))
        rej.append(fila)
    D.lamina(g, rej, 0.05, 0.08, "aleta", Vector((0, 0, 1)),
             aux_fn=lambda i, j: (i / 4, j / 5, 6.0))
    for t_idx in (1, 3, 4):  # 3 radios óseos de la base al borde
        pts = [rej[i][t_idx] + Vector((0, 0, 0.03)) for i in range(5)]
        g.tubo(pts, [0.06, 0.05, 0.04, 0.03, 0.02], "hueso", lados=5, punta=True)
    return base[2] - Vector((lado * 0.03, 0, 0))


def cresta(g, rnd):
    """Cresta dorsal continua: 0,8 de alto en el centro y decreciendo a los extremos. Se pliega bajo cada asiento
    (los jinetes van a horcajadas) y se eleva sobre las cinchas."""
    ys = np.linspace(CRESTA[0], CRESTA[1], 72)
    rej = [[], [], [], []]
    for y in ys:
        t = (CRESTA[0] - y) / (CRESTA[0] - CRESTA[1])
        h = 0.12 + 0.68 * math.sin(math.pi * t) ** 0.8
        for s in ASIENTOS:
            h = h - (h - 0.18) * math.exp(-((y - s) / 0.42) ** 2)
        base = F.superficie_arriba(0.0, y) + 0.02
        for c in CINCHAS:
            base += 0.09 * math.exp(-((y - c) / 0.25) ** 2)
        festón = 0.05 * math.sin(y * 5.7)  # borde con festones entre radios
        for i, u in enumerate((0.0, 0.35, 0.72, 1.0)):
            rej[i].append(Vector((0.0, y, base + (h + festón * u) * u)))
    D.lamina(g, rej, 0.05, 0.07, "cresta", Vector((1, 0, 0)),
             aux_fn=lambda i, j: (i / 3, j / 6.0 % 1.0 * 0 + j / 71 * 6.0, 6.0))
    for j in range(0, 72, 4):  # radios (nervios) cada ~1,2 studs
        pts = [rej[i][j] for i in range(4)]
        if pts[-1].z - pts[0].z < 0.3:
            continue
        g.tubo(pts, [0.04, 0.035, 0.028, 0.02], "cresta", lados=4, punta=True)


def ojo_y_cabeza(g, cor, bvh, rnd):
    for lado in (1, -1):
        c = Vector((lado * F.OJO[0], F.OJO[1], F.OJO[2]))
        D.ojo_completo(g, cor, c, Vector((lado, 0.3, 0.35)), F.OJO_R, alfa=0.95, pupila="vertical")
    # Escama frontal: escudo con grabado fractal y runas concéntricas.
    p, n = D.proyectar(bvh, 0.0, 13.75)
    t1, t2, n = D.marco(n, Vector((0, 1, 0)))
    filas = []
    for j, f in enumerate((0.33, 0.66, 1.0)):
        filas.append([p + n * (0.07 * (1 - f * f) + 0.02) + (t1 * math.cos(math.tau * k / 14) * 0.62 +
                                                             t2 * math.sin(math.tau * k / 14) * 0.5) * f
                      for k in range(14)])
    falda = [p - n * 0.04 + (t1 * math.cos(math.tau * k / 14) * 0.64 + t2 * math.sin(math.tau * k / 14) * 0.52)
             for k in range(14)]
    auxs = [[(f, k / 14, 7.0) for k in range(14)] for f in (0.33, 0.66, 1.0)] + [[(1.0, k / 14, 7.0)] * 1 * 0 +
                                                                              [(1.0, k / 14, 7.0)] for k in range(1)]
    vs = g.loft(filas + [falda], "escudo", auxs=[[(f, k / 14, 7.0) for k in range(14)] for f in (0.33, 0.66, 1.0, 1.0)],
                punta_inicio=(p + n * 0.09, (0.0, 0.0, 7.0)), tapar_fin=True)
    del auxs, vs
    # Colmillos retráctiles plegados contra el paladar y dientes curvos.
    cb, rb = F.CAVIDAD
    for lado in (1, -1):
        pts = [Vector((lado * 0.32, 14.85, cb[2] + 0.06)), Vector((lado * 0.34, 14.45, cb[2] + 0.045)),
               Vector((lado * 0.33, 14.0, cb[2] + 0.03)), Vector((lado * 0.3, 13.85, cb[2] + 0.0))]
        g.tubo(pts, [0.06, 0.05, 0.03, 0.008], "diente", lados=5, punta=True)
        for k in range(5):
            y = 14.55 - 0.32 * k
            x = lado * (0.5 + 0.06 * k)
            p, n = D.proyectar_hacia(bvh, (x, y, cb[2]), (0, 0, 1), 1.0)
            if p is not None:
                D.cono(g, p + Vector((0, 0, 0.015)), Vector((0, -0.4, -1)), 0.09, 0.03, "diente", lados=4,
                       curva=Vector((0, -0.03, 0)))


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
        altas[nombre] = ob
        print(f"[forma] {nombre}: {len(c)} tri ({time.time() - t:.1f}s)", flush=True)
    bvh = {n: T.bvh_de([o]) for n, o in altas.items()}
    todo = T.bvh_de(list(altas.values()))
    rnd = random.Random(33)
    geos = {n: T.Geo(n + "_det") for n in F.PIEZAS}

    # Cabeza, mandíbula.
    cor = T.Geo("Ojos_Cornea")
    ojo_y_cabeza(geos["Cabeza"], cor, bvh["Cabeza"], rnd)
    gm = geos["Mandibula"]
    cb, rb = F.CAVIDAD
    for lado in (1, -1):
        for k in range(5):
            y = 14.45 - 0.32 * k
            p, n = D.proyectar_hacia(bvh["Mandibula"], (lado * (0.46 + 0.06 * k), y, cb[2]), (0, 0, -1), 1.0)
            if p is not None:
                D.cono(gm, p - Vector((0, 0, 0.015)), Vector((0, -0.4, 1)), 0.08, 0.028, "diente", lados=4,
                       curva=Vector((0, -0.03, 0)))
    # Lengua bífida (2 studs) enrollada en el suelo de la boca.
    p, n = D.proyectar_hacia(bvh["Mandibula"], (0, 13.7, cb[2]), (0, 0, -1), 1.0)
    pts = []
    for k in range(34):
        a = k * 0.36
        r = 0.42 - 0.3 * k / 34
        pts.append(p + Vector((math.cos(a) * r, math.sin(a) * r * 0.9, 0.035)))
    gm.tubo(pts, [0.05 - 0.02 * k / 34 for k in range(34)], "lengua", lados=4, achatado=0.5)
    for lado in (1, -1):
        gm.tubo([pts[0], pts[0] + Vector((0.1 * lado, 0.22, 0.0))], [0.03, 0.01], "lengua", lados=4, punta=True)
    # Barbillones: 4 tentáculos sensoriales bajo la mandíbula.
    for (x, y) in ((0.25, 14.25), (0.58, 13.6)):
        for lado in (1, -1):
            p, n = D.proyectar(bvh["Mandibula"], lado * x, y, abajo=True)
            base = p + n * -0.04
            q = [base + Vector((0, -0.15 * k * k, -0.3 * k)) + Vector((lado * 0.06 * math.sin(k), 0, 0))
                 for k in range(5)]
            gm.tubo(q, [0.07, 0.055, 0.04, 0.025, 0.012], "piel", lados=5, punta=True,
                    aux_fn=lambda t, a: (0, 0, 0))

    # Arnés: cinchas, hebillas, correas longitudinales, asientos, estribos, barandilla, red de carga, estandarte.
    for y in CINCHAS:
        seg = segmento(y)
        g = geos[seg]
        ps, ns = contorno(bvh[seg], y)
        D.cinta(g, ps, ns, 0.34, 0.07, "cuero", cerrada=True, lateral=[Vector((0, 1, 0))] * len(ps), separacion=0.012)
        for lado in (1, -1):
            p, n = D.proyectar(bvh[seg], lado * 0.92, y)
            hebilla_espiral(g, p + n * 0.08, n)
    for lado in (1, -1):  # correas longitudinales entre cinchas
        for (ya, yb) in ((CINCHAS[0], CINCHAS[1]), (CINCHAS[1], CINCHAS[2])):
            for tramo_a, tramo_b in ((ya, max(yb, F.CORTES[2] if ya > 4 else F.CORTES[3])), ):
                pass
            ys = np.linspace(ya, yb, 18)
            trozos = {}
            for y in ys:
                trozos.setdefault(segmento(y), []).append(y)
            for seg, lista in trozos.items():
                if len(lista) < 2:
                    continue
                ps, ns = [], []
                for y in lista:
                    p, n = D.proyectar(bvh[seg], lado * 0.78, y)
                    ps.append(p)
                    ns.append(n)
                D.cinta(geos[seg], ps, ns, 0.12, 0.04, "cuero", separacion=0.012)
    datos_asientos = []
    for i, y in enumerate(ASIENTOS):
        seg = segmento(y)
        g = geos[seg]
        for lado in (1, -1):  # almohadillas a ambos lados de la cresta
            p, n = D.proyectar(bvh[seg], lado * 0.36, y)
            ex = Vector((1, 0, 0))
            ex = (ex - n * ex.dot(n)).normalized()
            ey = n.cross(ex).normalized()
            g.caja_redonda(p + n * 0.07, (0.46, 0.74, 0.13), "cuero", rot=D.matriz((ex, ey, n)), seg=1,
                           aux=(0, 0.5, 1.0), redondeo=0.5)
            # asa de hueso delante
            g.tubo([p + n * 0.05 + Vector((0, 0.4, 0)), p + n * 0.3 + Vector((0, 0.46, 0)),
                    p + n * 0.34 + Vector((0, 0.38, 0))], [0.035, 0.03, 0.03], "hueso", lados=5)
            # estribo
            q, m = D.proyectar_hacia(bvh[seg], (lado * 4.0, y - 0.1, F.ZC + 0.5), (-lado, 0, -0.2), 6.0)
            g.tubo([p + n * 0.02 + Vector((lado * 0.2, 0, 0)), q + m * 0.05], [0.025, 0.025], "cuero", lados=4)
            D.toro(g, q + m * 0.14 + Vector((0, 0, -0.1)), Vector((0, 1, 0)), 0.1, 0.025, "hueso", seg=8, lados=4)
        p, n = D.proyectar(bvh[seg], 0.0, y)
        datos_asientos.append((f"Montura_{i + 1}", p + n * 0.3, seg))
    # Barandilla de hueso pulido a ambos lados (0,5 de alto), por tramos dentro de cada segmento.
    for lado in (1, -1):
        postes = {}
        for y in np.arange(7.4, -6.9, -1.1):
            seg = segmento(y)
            p, n = D.proyectar(bvh[seg], lado * 1.12, y)
            arriba = p + Vector((0, 0, 0.5))
            geos[seg].tubo([p - n * 0.03, arriba], [0.045, 0.035], "hueso", lados=5)
            geos[seg].elipsoide(arriba, (0.05, 0.05, 0.05), "hueso", seg=5, anillos=3)
            postes.setdefault(seg, []).append(arriba)
        for seg, lista in postes.items():
            if len(lista) >= 2:
                geos[seg].tubo(lista, [0.03] * len(lista), "hueso", lados=5)
    # Red de carga bajo el vientre (segmentos 3 y 4) con ganchos de colmillo.
    for seg, (ya, yb) in (("Segmento_3", (2.4, 0.06)), ("Segmento_4", (-0.06, -2.4))):
        g = geos[seg]
        for x in np.linspace(-1.2, 1.2, 5):
            pts = []
            for y in np.linspace(ya, yb, 6):
                p, n = D.proyectar(bvh[seg], x, y, abajo=True)
                pts.append(p + Vector((0, 0, -0.08 - 0.22 * (1 - (x / 1.3) ** 2))))
            g.tubo(pts, [0.022] * len(pts), "fibra", lados=3)
        for y in np.linspace(ya, yb, 4):
            pts = []
            for x in np.linspace(-1.35, 1.35, 7):
                p, n = D.proyectar(bvh[seg], x, y, abajo=True)
                pts.append(p + Vector((0, 0, -0.08 - 0.22 * (1 - (x / 1.3) ** 2))))
            g.tubo(pts, [0.022] * len(pts), "fibra", lados=3)
            for lado in (1, -1):
                q = pts[0] if lado < 0 else pts[-1]
                D.cono(g, q, Vector((lado * 0.3, 0, 1)), 0.18, 0.035, "diente", lados=4,
                       curva=Vector((-lado * 0.05, 0, 0)))
    # Estandarte en el Segmento_2: palo de hueso y bandera ondulada con el ojo con tentáculos.
    g = geos["Segmento_2"]
    p, n = D.proyectar(bvh["Segmento_2"], 0.95, 7.45)
    pie, tope = p - n * 0.05, p + Vector((0, 0, 2.3))
    g.tubo([pie, tope], [0.055, 0.04], "hueso", lados=6)
    D.cono(g, tope, Vector((0, 0, 1)), 0.25, 0.06, "diente", lados=5)
    rej = []
    for i, v in enumerate(np.linspace(0, 1, 6)):
        fila = []
        for j, u in enumerate(np.linspace(0, 1, 9)):
            onda = 0.12 * math.sin(u * 5.5 + v * 1.5) * u
            fila.append(tope + Vector((0.04 + onda, -0.06 - 1.15 * u, -0.08 - 0.78 * v)))
        rej.append(fila)
    D.lamina(g, rej, 0.03, 0.04, "tela", Vector((1, 0, 0)), aux_fn=lambda i, j: (i / 5, j / 8, 0.0))
    # Parásitos fosilizados en las escamas traseras.
    for (x, y) in ((0.7, -7.0), (0.95, -7.4), (0.55, -8.6), (-0.8, -8.9), (-0.6, -9.4), (1.0, -9.8), (0.2, -10.6),
                   (-0.95, -10.2)):
        seg = segmento(y)
        p, n = D.proyectar(bvh[seg], x, y)
        parasito_fosil(geos[seg], p, n, rnd)

    # Aletas y cresta (piezas solo de geometría).
    geometricas, piv_aletas = {}, {}
    for num, y in ALETAS.items():
        seg = segmento(y)
        for lado, nom in ((-1, "Izq"), (1, "Der")):
            g = T.Geo(f"Aleta_{nom}_{num}")
            piv_aletas[f"Aleta_{nom}_{num}"] = aleta(g, bvh[seg], y, lado, rnd)
            geometricas[f"Aleta_{nom}_{num}"] = g.objeto(mats)
    g = T.Geo("Cresta_Dorsal")
    cresta(g, rnd)
    geometricas["Cresta_Dorsal"] = g.objeto(mats)

    det = {n: [g.objeto(mats)] for n, g in geos.items() if len(g.bm.faces)}
    return altas, det, geometricas, piv_aletas, cor.objeto(mats), datos_asientos, todo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="1")
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    altas, det, geometricas, piv_aletas, cornea, asientos, todo = construir(args)
    pivotes = {n: F.pivote(n) for n in F.PIEZAS}
    pivotes.update(piv_aletas)
    pivotes["Cresta_Dorsal"] = (0.0, sum(CRESTA) / 2, F.superficie_arriba(0, sum(CRESTA) / 2) + 0.4)
    pivotes["Ojos_Cornea"] = pivotes["Cabeza"]
    padre = {"Segmento_1": None, "Cabeza": "Segmento_1", "Mandibula": "Cabeza", "Cola_Punta": "Segmento_6",
             "Aleta_Izq_1": "Segmento_2", "Aleta_Der_1": "Segmento_2", "Aleta_Izq_2": "Segmento_4",
             "Aleta_Der_2": "Segmento_4", "Cresta_Dorsal": "Segmento_3", "Ojos_Cornea": "Cabeza"}
    for i in range(2, 7):
        padre[f"Segmento_{i}"] = f"Segmento_{i - 1}"
    montajes = {nom: (p, seg) for nom, p, seg in asientos}
    p, n = D.proyectar(todo, 0.0, 2.0, abajo=True)
    montajes["Punto_Carga"] = (p - Vector((0, 0, 0.45)), "Segmento_3")
    vidrio = bpy.data.materials.new("cornea_render")
    N = T.Nodos(vidrio)
    N.poner("Base Color", T.srgb("#E0FFD8"))
    N.poner("Roughness", 0.02)
    N.poner("Transmission Weight", 1.0)
    orden = ["Segmento_1", "Cabeza", "Mandibula"] + [f"Segmento_{i}" for i in range(2, 7)] + \
            ["Cola_Punta", "Aleta_Izq_1", "Aleta_Izq_2", "Aleta_Der_1", "Aleta_Der_2", "Cresta_Dorsal"]
    peso = {"Cabeza": 1.6, "Mandibula": 0.6, "Cola_Punta": 0.5}
    peso.update({f"Segmento_{i}": 0.9 for i in range(1, 7)})
    cfg = dict(
        nombre=NOMBRE, titulo="SERPIENTE CÓSMICA", rol="Transporte / asedio", jinetes="4-6",
        neon=["#9B59B6", "#39FF14"], presupuesto=PRESUPUESTO, salida=args.salida, ronda=args.ronda,
        rapido=args.rapido, altas=altas, detalles=det, geometricas=geometricas,
        soldadas={"Ojos_Cornea": (cornea, "Cabeza")}, peso_tris=peso, pivotes=pivotes, padre=padre, orden=orden,
        montajes=montajes, prioridad_uv={"Cabeza": 1.5, "Mandibula": 1.2, "Ojos_Cornea": 1.5, "Cresta_Dorsal": 0.8},
        render_material={cornea: vidrio}, radio_estudio=15.0, exposicion=0.9, emision_render=3.0,
        cerca=[("Cabeza 3/4", 40, 18, (0, 13.6, 1.2), 2.2), ("Ojo y escudo", 70, 25, (0.6, 13.6, 1.5), 1.0),
               ("Boca y barbillones", 20, -20, (0, 14.0, 0.6), 1.6), ("Asientos y cresta", 35, 35, (0, 2.0, 2.0), 3.2),
               ("Aleta y red", 60, -15, (1.6, 2.0, 0.6), 3.4), ("Cola en remo", 150, 30, (0, -12.6, 1.0), 2.4)],
        notas_json=["Ojos_Cornea va soldada a la Cabeza: en Roblox, material Glass o Transparency 0,35.",
                    "La cresta se pliega bajo cada asiento (los jinetes van a horcajadas) para no chocar con ellos."],
    )
    bestia.terminar(cfg)


if __name__ == "__main__":
    main()
