"""Ronda 10: props y decoración II (modelos 57-62). El cofre sale en dos archivos: cerrado y abierto."""

import math
import random

from comunes import bandera, cristales, raices, runa


def fuente_humana(g):
    N = 16
    g.cil("piedra_clara", 7.2, 0.5, (0, 0, 0), lados=N, bisel=0.1, suave=False)
    # Pilón: muro circular con borde, y lámina de agua (pieza aparte).
    g.rev("piedra_clara", [(6.4, 0.0), (6.6, 1.6), (6.7, 2.0), (5.5, 2.0), (5.4, 1.6), (5.4, 0.0)], (0, 0, 0.5), lados=N, suave=False,
          tapas=(True, False))
    g.cil("piedra", 5.4, 0.4, (0, 0, 0.5), lados=N)
    g.cil("agua", 5.4, 0.25, (0, 0, 1.75), lados=N)
    for i in range(8):
        a = 2 * math.pi * i / 8
        g.caja("piedra", (0.9, 0.5, 1.7), (6.55 * math.cos(a), 6.55 * math.sin(a), 0.5), rot=(0, 0, math.degrees(a) + 90), base=True, bisel=0.08)
        g.caja("h_neon", (0.4, 0.1, 0.9), (6.83 * math.cos(a), 6.83 * math.sin(a), 1.4), rot=(0, 0, math.degrees(a) + 90))
    # Columna central con dos tazas y remate.
    g.rev("piedra_clara", [(1.3, 0.0), (1.0, 0.6), (0.7, 1.4), (0.7, 3.4), (1.0, 4.0), (2.9, 4.6), (3.0, 4.9), (2.6, 4.9), (0.9, 4.5), (0.0, 4.5)],
          (0, 0, 0.9), lados=12)
    g.cil("agua", 2.6, 0.12, (0, 0, 5.62), lados=12)
    g.rev("piedra_clara", [(0.55, 0.0), (0.5, 1.6), (0.8, 2.0), (1.7, 2.4), (1.75, 2.65), (1.45, 2.65), (0.6, 2.3), (0.0, 2.3)], (0, 0, 5.4), lados=10)
    g.cil("agua", 1.45, 0.1, (0, 0, 7.9), lados=10)
    g.cil("h_metal", 0.22, 1.2, (0, 0, 7.7), lados=6)
    g.esfera("h_neon", 0.5, (0, 0, 9.3), lados=8, anillos=5)
    g.toro("h_naranja_liso", 0.75, 0.1, (0, 0, 4.3), seg=10, lados=4)
    # Chorros de agua (arcos finos) de la taza grande al pilón.
    for i in range(4):
        a = 2 * math.pi * i / 4 + 0.4
        g.tubo("agua", [(2.8 * math.cos(a), 2.8 * math.sin(a), 5.6), (3.5 * math.cos(a), 3.5 * math.sin(a), 5.0),
                        (3.9 * math.cos(a), 3.9 * math.sin(a), 1.9)], [0.12, 0.16, 0.22], lados=5)
    g.ancla("Agua", (0, 0, 1.9))
    g.ancla("Chorro", (0, 0, 9.3))


def antorcha_muro(g):
    # Se cuelga de una pared que queda detrás (+Y). La llama es una pieza de neón; el fuego real, un ParticleEmitter.
    g.caja("hierro_osc", (0.9, 0.16, 1.8), (0, -0.08, 0), bisel=0.04)
    for z in (-0.6, 0.6):
        g.esfera("hierro", 0.09, (0, -0.18, z), lados=5, anillos=3)
    g.tubo("hierro_osc", [(0, -0.1, -0.3), (0, -0.7, -0.5), (0, -1.1, -0.1)], 0.09, lados=5)
    g.toro("hierro_osc", 0.24, 0.07, (0, -1.15, 0.05), (-25, 0, 0), seg=8, lados=4)
    with g.grupo((0, -0.75, -0.75), (-25, 0, 0)):
        g.cil("madera", 0.13, 1.9, (0, 0, 0), lados=6, r2=0.19)
        g.cil("cuero", 0.2, 0.35, (0, 0, 0.5), lados=6)
        g.rev("hierro_osc", [(0.2, 0.0), (0.42, 0.5), (0.36, 0.5), (0.0, 0.2)], (0, 0, 1.8), lados=8)
        g.esfera("h_oscuro", 0.3, (0, 0, 2.2), esc=(1, 1, 0.6), lados=6, anillos=4)
        g.rev("llama", [(0.0, 0.0), (0.3, 0.2), (0.34, 0.5), (0.2, 0.95), (0.0, 1.5)], (0, 0, 2.2), lados=6, suave=False)
        g.ancla("Llama", (0, 0, 2.5))


def bandera_humana(g):
    g.cil("h_hormigon", 1.4, 0.4, (0, 0, 0), lados=8, bisel=0.08, suave=False)
    g.cil("h_gris", 0.8, 0.6, (0, 0, 0.4), lados=8, r2=0.5, suave=False)
    g.cil("h_naranja_liso", 0.42, 0.4, (0, 0, 1.0), lados=8)
    bandera(g, (0, 0, 1.0), alto=15.0, ancho=7.0, caida=4.2)
    g.toro("h_neon", 0.62, 0.07, (0, 0, 1.02), seg=8, lados=4)
    g.ancla("Tela", (3.5, 0, 14.0))


def bandera_monstruo(g):
    rnd = random.Random(60)
    # Mástil retorcido con remate de hueso y bandera rasgada púrpura y negra.
    pts, rs = [], []
    for i in range(10):
        t = i / 9
        pts.append((0.35 * math.sin(t * 7), 0.35 * (math.cos(t * 7) - 1), -0.2 + t * 16.0))
        rs.append(0.5 - 0.32 * t)
    g.tubo("m_tronco", pts, rs, lados=6)
    raices(g, "m_tronco", (0, 0, 0), 5, 0.5, 1.3, rnd, lados=4)
    c = pts[-1]
    g.esfera("m_hueso", 0.42, (c[0], c[1], c[2] + 0.3), esc=(0.9, 1.05, 1), lados=7, anillos=5)
    for s in (-1, 1):
        g.tubo("m_hueso", [(c[0] + s * 0.25, c[1], c[2] + 0.5), (c[0] + s * 0.8, c[1], c[2] + 0.9), (c[0] + s * 0.7, c[1], c[2] + 1.6)],
               [0.16, 0.12, 0.0], lados=5)
        g.esfera("m_magenta", 0.09, (c[0] + s * 0.16, c[1] - 0.36, c[2] + 0.36), lados=5, anillos=3)
    # Tela: tiras desiguales que cuelgan de un travesaño de hueso.
    g.tubo("m_hueso", [(c[0] - 0.4, c[1], c[2] - 1.0), (c[0] + 5.6, c[1], c[2] - 1.3)], [0.16, 0.09], lados=5)
    n = 8
    secciones = []
    for i in range(n + 1):
        t = i / n
        px = c[0] + 0.2 + 5.2 * t
        py = c[1] + 0.3 * math.sin(t * 8) * t
        zt = c[2] - 1.15 - 0.3 * t
        largo = (5.5, 7.0, 4.8, 6.6, 7.6, 5.0, 6.2, 4.2, 5.4)[i]
        secciones.append([(px, py - 0.05, zt - largo), (px, py + 0.05, zt - largo), (px, py + 0.05, zt), (px, py - 0.05, zt)])
    g.loft("m_tela", secciones, suave=False)
    runa(g, "m_magenta", (c[0] + 2.8, c[1] - 0.14, c[2] - 3.4), (0, 0, 0), 1.8, semilla=4, grosor=0.14)
    cristales(g, "m_cristal", (0.9, -0.5, 0.0), n=3, r=0.22, h=1.1, semilla=3)
    g.ancla("Tela", (c[0] + 2.8, c[1], c[2] - 4.0))


def _cofre(g, abierto):
    W, D, H = 5.0, 3.2, 2.2
    g.caja("tablas_h", (W, D, H), (0, 0, 0), base=True)
    for s in (-1, 1):
        g.caja("hierro_osc", (0.45, D + 0.16, H + 0.08), (s * (W / 2 - 0.25), 0, 0), base=True)
        g.caja("hierro", (0.3, 0.3, 0.3), (s * (W / 2 - 0.25), -D / 2 - 0.06, 0.3), bisel=0.05)
        g.toro("hierro", 0.3, 0.07, (s * (W / 2 + 0.1), 0, 1.3), (0, 90, 0), seg=8, lados=4, arco=180)
    g.caja("hierro_osc", (W + 0.1, D + 0.12, 0.3), (0, 0, 0), base=True)
    g.caja("hierro_osc", (W + 0.1, D + 0.12, 0.25), (0, 0, H - 0.25), base=True)
    g.caja("oro", (0.8, 0.2, 0.9), (0, -D / 2 - 0.1, H - 0.5), bisel=0.05)
    g.caja("hierro_osc", (0.2, 0.08, 0.3), (0, -D / 2 - 0.21, H - 0.55))
    for k in range(4):
        g.caja("madera_osc", (0.3, 0.3, 0.3), ((-1) ** k * (W / 2 - 0.3), (1 if k < 2 else -1) * (D / 2 - 0.3), -0.0), base=False)
    if abierto:
        # Tesoro: montón de monedas, lingotes y gemas.
        g.esfera("oro", 2.1, (0, 0, H - 0.5), esc=(1.05, 0.62, 0.42), lados=10, anillos=5)
        rnd = random.Random(61)
        for i in range(14):
            g.cil("oro", 0.26, 0.07, (rnd.uniform(-1.9, 1.9), rnd.uniform(-1.0, 1.0), H + rnd.uniform(0.1, 0.42)),
                  (rnd.uniform(-40, 40), rnd.uniform(-40, 40), 0), lados=7)
        g.caja("oro", (1.0, 0.45, 0.3), (-1.0, 0.3, H + 0.38), rot=(10, -8, 25), sup=(0.8, 0.7))
        g.cristal("cris_azul", 0.3, 0.9, (1.0, -0.3, H + 0.2), (20, 15, 0), lados=6)
        g.cristal("cris_naranja", 0.24, 0.7, (0.2, 0.5, H + 0.3), (-25, 10, 0), lados=5)
        g.cristal("cris_purpura", 0.22, 0.7, (-0.3, -0.7, H + 0.25), (30, -20, 0), lados=5)
    # Tapa abombada (pieza aparte con la bisagra como pivote).
    g.pieza("tapa", pivote=(0, D / 2, H))
    with g.grupo((0, D / 2, H), (-105 if abierto else 0, 0, 0)):
        arco = [(-D, 0.0)] + [(-D / 2 + D / 2 * math.cos(math.pi * i / 6), 1.25 * math.sin(math.pi * i / 6)) for i in range(7)][::-1][1:]
        arco = [(-D / 2 - D / 2 * math.cos(math.pi * i / 6), 1.25 * math.sin(math.pi * i / 6)) for i in range(7)]
        g.prisma("tablas_h", arco, W, (0, 0, 0), plano="yz")
        for px in (-(W / 2 - 0.25), 0.0, W / 2 - 0.25):
            g.prisma("hierro_osc", [(a * 1.03 - D / 2 * 0.03, b * 1.06) for a, b in arco], 0.45, (px, 0, 0), plano="yz")
        g.caja("oro", (0.8, 0.2, 0.5), (0, -D - 0.1, 0.25), bisel=0.05)
    g.pieza("cuerpo")
    g.ancla("Tesoro", (0, 0, H))


def cofre_tesoro(g):
    _cofre(g, False)


def cofre_tesoro_abierto(g):
    _cofre(g, True)


def portal_base(g):
    R = 6.5
    # Escalinata y dos contrafuertes que sujetan el aro; el efecto del portal va en Roblox (ancla «Centro»).
    g.caja("portal_piedra", (14.0, 6.0, 0.7), (0, 0, 0), base=True, bisel=0.12)
    g.caja("portal_piedra", (10.5, 4.2, 0.7), (0, 0, 0.7), base=True, bisel=0.12)
    ZC = 1.4 + R + 0.2
    g.toro("portal_piedra", R, 1.0, (0, 0, ZC), (90, 0, 0), seg=24, lados=6, pot=3.0, suave=False)
    g.toro("portal_runa", R - 1.02, 0.1, (0, 0, ZC), (90, 0, 0), seg=24, lados=4)
    for s in (-1, 1):
        g.prisma("portal_piedra", [(s * 4.2, 1.4), (s * 7.2, 1.4), (s * 7.9, 5.6), (s * 6.6, 5.6)], 2.2, (0, 0, 0), plano="xz")
        g.cristal("portal_runa", 0.45, 1.6, (s * 7.4, 0, 5.6), lados=4, punta=0.6, base=0.9)
    # Doce segmentos tallados con una runa en cada cara, y cuatro claves que sobresalen.
    for i in range(12):
        a = math.radians(30 * i + 15)
        px, pz = R * math.cos(a), ZC + R * math.sin(a)
        if pz < 2.6:
            continue
        for s in (-1, 1):
            runa(g, "portal_runa", (px, s * -1.02, pz), (0, math.degrees(-a) + 90, 0 if s > 0 else 180), 1.05, semilla=i + 3, grosor=0.14)
    for i in range(4):
        a = math.radians(90 * i + 45)
        g.caja("portal_piedra", (1.3, 2.6, 2.4), (R * 1.02 * math.cos(a), 0, ZC + R * 1.02 * math.sin(a)), rot=(0, -math.degrees(a) + 90, 0),
               bisel=0.12)
    g.caja("portal_piedra", (1.6, 2.8, 2.6), (0, 0, ZC + R * 1.04), bisel=0.12)
    g.cristal("portal_runa", 0.5, 1.8, (0, 0, ZC + R + 1.2), lados=4, punta=0.6, base=0.0)
    g.ancla("Centro", (0, 0, ZC))
    g.extra["portal"] = {"radio_interior": R - 1.1}


MODELOS = [
    ("fuente_humana", "props", 5000, fuente_humana),
    ("antorcha_muro", "props", 5000, antorcha_muro),
    ("bandera_humana", "props", 5000, bandera_humana),
    ("bandera_monstruo", "props", 5000, bandera_monstruo),
    ("cofre_tesoro", "props", 5000, cofre_tesoro),
    ("cofre_tesoro_abierto", "props", 5000, cofre_tesoro_abierto),
    ("portal_base", "props", 5000, portal_base),
]
