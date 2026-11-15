"""Ronda 9: props y decoración I (modelos 51-56)."""

import math
import random

from comunes import colmillo, cristales, raices, tira


def farola_humana(g):
    g.cil("h_gris", 0.9, 0.5, (0, 0, 0), lados=8, bisel=0.1, suave=False)
    g.cil("h_oscuro", 0.55, 1.4, (0, 0, 0.5), lados=8, r2=0.32, suave=False)
    g.cil("h_naranja_liso", 0.36, 0.3, (0, 0, 1.9), lados=8, suave=False)
    # Fuste y brazo curvo hacia el frente.
    g.tubo("h_metal", [(0, 0, 2.0), (0, 0, 9.5), (0, -0.4, 11.4), (0, -1.5, 12.4), (0, -3.0, 12.6)], [0.24, 0.2, 0.18, 0.16, 0.14], lados=8)
    g.cil("h_oscuro", 0.3, 0.5, (0, 0, 6.0), lados=8)
    tira(g, "h_neon", (0, -0.23, 2.6), (0, -0.23, 5.6), 0.1)
    # Cabezal con difusor de neón cian.
    g.caja("h_blanco_liso", (1.4, 2.6, 0.5), (0, -3.6, 12.6), sup=(0.7, 0.8), bisel=0.1)
    g.caja("h_neon", (1.0, 2.1, 0.18), (0, -3.6, 12.3))
    g.caja("h_naranja_liso", (1.44, 0.3, 0.3), (0, -2.4, 12.6))
    g.cil("h_metal", 0.05, 1.2, (0, -4.6, 12.85), lados=4)
    g.ancla("Luz", (0, -3.6, 12.1))


def farola_monstruo(g):
    rnd = random.Random(52)
    # Pilar orgánico retorcido con garra de hueso que sujeta un cristal luminoso.
    pts, rs = [], []
    for i in range(8):
        t = i / 7
        pts.append((0.5 * math.sin(t * 5), 0.5 * (math.cos(t * 5) - 1) * 0.8, -0.2 + t * 9.5))
        rs.append(0.95 - 0.5 * t + 0.1 * math.sin(t * 12))
    g.tubo("m_tronco", pts, rs, lados=7)
    raices(g, "m_tronco", (0, 0, 0), 5, 0.8, 1.6, rnd, lados=5)
    c = pts[-1]
    for i in range(4):
        a = math.radians(90 * i + 30)
        g.tubo("m_hueso", [(c[0] + 0.3 * math.cos(a), c[1] + 0.3 * math.sin(a), c[2] - 0.3),
                           (c[0] + 1.2 * math.cos(a), c[1] + 1.2 * math.sin(a), c[2] + 0.9),
                           (c[0] + 1.0 * math.cos(a), c[1] + 1.0 * math.sin(a), c[2] + 2.3),
                           (c[0] + 0.45 * math.cos(a), c[1] + 0.45 * math.sin(a), c[2] + 3.1)], [0.26, 0.2, 0.14, 0.0], lados=5)
    g.cristal("m_cristal", 0.7, 2.2, (c[0], c[1], c[2] + 1.3), lados=6, punta=0.6, base=1.0)
    g.cristal("m_cristal", 0.7, 1.2, (c[0], c[1], c[2] + 1.3), (180, 0, 0), lados=6, punta=1.0, base=1.0)
    cristales(g, "m_cristal", (0.9, 0.5, 0.0), n=3, r=0.25, h=1.2, semilla=2)
    g.esfera("m_neon", 0.22, (pts[3][0] + 0.75, pts[3][1], pts[3][2]), esc=(0.5, 1, 1.5), lados=6, anillos=4)
    g.ancla("Luz", (c[0], c[1], c[2] + 1.5))


def barril_madera(g):
    perfil = [(0.0, 0.0), (1.25, 0.0), (1.5, 0.9), (1.6, 2.0), (1.5, 3.1), (1.25, 4.0), (1.12, 4.0), (1.12, 3.8), (0.0, 3.8)]
    g.rev("tablas", perfil, (0, 0, 0), lados=14, suave=False)
    g.cil("madera_h", 1.12, 0.06, (0, 0, 3.76), lados=14)
    for z, r in ((0.55, 1.42), (1.45, 1.58), (2.55, 1.58), (3.45, 1.42)):
        g.toro("hierro_osc", r, 0.09, (0, 0, z), seg=14, lados=4, esc=(1, 1, 1.6))
    g.cil("madera_osc", 0.2, 0.25, (1.52, 0, 2.0), (0, 90, 0), lados=6)
    for i in range(14):
        a = 2 * math.pi * i / 14
        g.esfera("hierro", 0.05, (1.63 * math.cos(a), 1.63 * math.sin(a), 2.55), lados=4, anillos=3)


def caja_madera(g):
    L = 4.0
    h = L / 2
    g.caja("tablas", (L - 0.3, L - 0.3, L - 0.3), (0, 0, h))
    # Bastidor: listones en las 12 aristas y diagonales en las caras laterales.
    for a in (-1, 1):
        for b in (-1, 1):
            g.caja("madera_osc", (0.45, 0.45, L), (a * (h - 0.22), b * (h - 0.22), h))
            g.caja("madera_osc_h", (L, 0.45, 0.45), (0, a * (h - 0.22), h + b * (h - 0.22)))
            g.caja("madera_y", (0.45, L - 0.9, 0.45), (a * (h - 0.22), 0, h + b * (h - 0.22)))
    for s in (-1, 1):
        g.caja("madera_osc_h", (4.6, 0.2, 0.42), (0, s * (h - 0.1), h), rot=(0, s * 45, 0))
        g.caja("madera_y", (0.2, 4.6, 0.42), (s * (h - 0.1), 0, h), rot=(s * 45, 0, 0))
    for a in (-1, 1):
        for b in (-1, 1):
            for c in (-1, 1):
                g.caja("hierro_osc", (0.6, 0.6, 0.6), (a * (h - 0.18), b * (h - 0.18), h + c * (h - 0.18)), bisel=0.08)
    g.caja("h_naranja_liso", (1.2, 0.06, 0.8), (0, -h + 0.14, h + 0.9))


def letrero_madera(g):
    # Poste con travesaño del que cuelga el cartel (pieza aparte y en blanco: el texto se pone en Roblox).
    g.roca("piedra", 0.9, (0, 0, 0.1), esc=(1.2, 1.1, 0.4), semilla=3, sub=1, amp=0.25, plano=-0.3)
    g.tubo("madera", [(0, 0, -0.2), (0.05, 0, 3.5), (0, 0, 7.6)], [0.34, 0.3, 0.26], lados=7)
    g.cil("madera_osc", 0.34, 0.25, (0, 0, 7.6), lados=7, r2=0.0)
    g.caja("madera_osc_h", (4.4, 0.3, 0.34), (1.7, 0, 6.8))
    g.caja("madera_osc", (0.2, 0.2, 1.9), (1.0, 0, 6.0), rot=(0, 45, 0))
    for px in (1.2, 3.4):
        g.toro("hierro_osc", 0.16, 0.04, (px, 0, 6.5), (90, 0, 0), seg=6, lados=3)
        g.toro("hierro_osc", 0.16, 0.04, (px, 0, 6.24), (0, 90, 0), seg=6, lados=3)
    g.pieza("cartel", pivote=(2.3, 0, 6.1))
    g.caja("tablas_h", (3.6, 0.22, 2.6), (2.3, 0, 4.75), bisel=0.05)
    for s in (-1, 1):
        g.caja("madera_osc", (0.22, 0.3, 2.7), (2.3 + s * 1.75, 0, 4.75))
        g.caja("madera_osc_h", (3.7, 0.3, 0.22), (2.3, 0, 4.75 + s * 1.3))
    g.pieza("cuerpo")
    g.ancla("Texto", (2.3, -0.12, 4.75))


def banco_piedra(g):
    # Banco de piedra tallada con respaldo bajo; el asiento queda a 1,7 studs.
    g.caja("piedra_clara", (6.4, 2.2, 0.5), (0, 0, 1.45), base=True, bisel=0.1)
    for s in (-1, 1):
        g.prisma("piedra", [(-0.95, 0), (0.95, 0), (0.8, 0.5), (0.45, 0.8), (0.45, 1.45), (-0.45, 1.45), (-0.45, 0.8), (-0.8, 0.5)], 0.7,
                 (s * 2.4, 0, 0), plano="yz")
        g.prisma("piedra", [(0.7, 1.9), (1.1, 1.9), (1.3, 3.4), (1.0, 3.6), (0.8, 3.4)], 0.6, (s * 2.4, 0, 0), plano="yz")
    g.caja("piedra_clara", (6.0, 0.4, 1.1), (0, 1.05, 2.9), rot=(-8, 0, 0), bisel=0.08)
    g.caja("piedra", (5.4, 0.3, 0.3), (0, 0, 0.5))
    g.roca("hoja", 0.5, (-2.6, 0.7, 1.95), esc=(1.5, 1.2, 0.3), semilla=4, sub=1, amp=0.3)
    g.roca("hoja", 0.4, (2.9, -0.6, 0.2), esc=(1.3, 1.2, 0.4), semilla=5, sub=1, amp=0.3)
    g.ancla("Asiento", (0, 0, 1.95))


MODELOS = [
    ("farola_humana", "props", 5000, farola_humana),
    ("farola_monstruo", "props", 5000, farola_monstruo),
    ("barril_madera", "props", 5000, barril_madera),
    ("caja_madera", "props", 5000, caja_madera),
    ("letrero_madera", "props", 5000, letrero_madera),
    ("banco_piedra", "props", 5000, banco_piedra),
]
