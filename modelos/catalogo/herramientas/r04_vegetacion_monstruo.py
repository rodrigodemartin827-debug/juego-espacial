"""Ronda 4: vegetación del planeta de los monstruos (modelos 20-24). Negra, retorcida y bioluminiscente."""

import math
import random

from comunes import cristales, curva, radios, raices, ramas, seta


def arbol_alienigena_01(g):
    rnd = random.Random(20)
    # Tronco negro retorcido en espiral.
    pts, rs = [], []
    for i in range(9):
        t = i / 8
        a = t * 4.4
        pts.append((1.2 * math.sin(a) * (1 - t * 0.3), 1.2 * (math.cos(a) - 1) * (1 - t * 0.3), -0.3 + t * 12.3))
        rs.append(1.9 - 1.0 * t + 0.25 * math.sin(t * 9))
    g.tubo("m_tronco", pts, rs, lados=8)
    raices(g, "m_tronco", (0, 0, 0), 6, 1.5, 3.0, rnd, lados=5)
    # Ramas con vetas luminosas, que se abren como dedos; yemas brillantes en las puntas.
    puntas = []
    cima = pts[-1]
    for a, inc in ((10, 50), (130, 55), (245, 48), (70, 20)):
        ar, ir = math.radians(a), math.radians(inc)
        ramas(g, "m_tronco", cima, (math.cos(ar) * math.sin(ir), math.sin(ar) * math.sin(ir), math.cos(ir)), 5.2, 0.85, 3, rnd,
              abrir=38, hijos=2, encoge=0.7, lados=6, tuerce=0.3, puntas=puntas)
    for i, (p, d) in enumerate(puntas):
        g.esfera("m_neon" if i % 3 else "m_magenta", 0.3, p, esc=(1, 1, 1.4), lados=6, anillos=4)
    # Bultos / nudos con ojo de luz en el tronco.
    g.esfera("m_tronco", 0.9, (pts[3][0] + 1.2, pts[3][1] - 0.6, pts[3][2]), lados=7, anillos=4)
    g.esfera("m_neon", 0.35, (pts[3][0] + 1.95, pts[3][1] - 0.95, pts[3][2]), esc=(0.5, 1, 1.5), lados=6, anillos=4)
    cristales(g, "m_cristal", (2.6, 1.6, 0.0), n=3, r=0.4, h=1.8, semilla=3)


def arbol_alienigena_02(g):
    rnd = random.Random(21)
    # Variante alta y delgada: fuste sinuoso y ramas caídas de las que cuelgan cristales.
    pts, rs = [], []
    for i in range(11):
        t = i / 10
        pts.append((0.9 * math.sin(t * 5.0), 0.6 * math.sin(t * 3.1 + 1), -0.3 + t * 30.0))
        rs.append(1.25 - 0.85 * t)
    g.tubo("m_tronco", pts, rs, lados=7)
    raices(g, "m_tronco", (0, 0, 0), 5, 1.0, 2.4, rnd, lados=5)
    n = 0
    for k, i in enumerate((4, 5, 6, 7, 8, 9, 10)):
        base = pts[i]
        for j in range(2 if i < 10 else 3):
            a = k * 2.4 + j * (3.14 if i < 10 else 2.09) + rnd.uniform(-0.3, 0.3)
            L = 7.5 - k * 0.55
            rama = [base, (base[0] + math.cos(a) * L * 0.45, base[1] + math.sin(a) * L * 0.45, base[2] + 2.0),
                    (base[0] + math.cos(a) * L * 0.85, base[1] + math.sin(a) * L * 0.85, base[2] + 1.4),
                    (base[0] + math.cos(a) * L, base[1] + math.sin(a) * L, base[2] - 1.2)]
            r0 = rs[i] * 0.7
            g.tubo("m_tronco", rama, [r0, r0 * 0.7, r0 * 0.45, 0.08], lados=5)
            # Cristales colgando de hilos.
            for q, (t, largo) in enumerate(((1.0, 2.2), (0.75, 1.4))):
                if q == 1 and n % 2:
                    continue
                px = base[0] + math.cos(a) * L * t
                py = base[1] + math.sin(a) * L * t
                pz = rama[3][2] if t == 1.0 else base[2] + 1.6
                g.tubo("m_negro_liso", [(px, py, pz), (px, py, pz - largo)], 0.045, lados=3, suave=False)
                g.cristal("m_cristal", 0.38, 1.7, (px, py, pz - largo), (180, 0, n * 31), lados=5, punta=0.65, base=0.55)
            n += 1
    g.cristal("m_cristal", 0.5, 2.6, (pts[-1][0], pts[-1][1], pts[-1][2] - 0.2), lados=5)


def hongo_gigante(g):
    rnd = random.Random(22)
    g.roca("m_roca", 6.5, (0, 0, 0), esc=(1, 1, 0.08), semilla=2, sub=2, amp=0.2)
    seta(g, (0, 0, 0.2), 17.0, 9.0, inclina=(1.2, -0.8), lados=14, semilla=5, r_tallo=1.6)
    # Anillo (velo) en el tallo y bulbo en la base.
    g.rev("m_purpura_liso", [(1.5, 0.0), (3.2, -1.3), (3.0, -1.5), (1.5, -0.5)], (0.75, -0.5, 11.5), (4, 3, 0), lados=10, suave=False,
          tapas=(False, False))
    g.esfera("m_hueso", 2.6, (0, 0, 0.6), esc=(1, 1, 0.6), lados=10, anillos=5)
    seta(g, (5.2, 2.2, 0.3), 7.5, 3.6, inclina=(1.0, 0.8), lados=10, semilla=6)
    seta(g, (-4.6, -2.6, 0.3), 5.0, 2.6, inclina=(-0.8, -0.5), lados=9, semilla=7)
    seta(g, (-3.0, 4.4, 0.3), 3.0, 1.6, inclina=(-0.3, 0.4), lados=8, semilla=8, puntos=None)
    # Esporas flotando bajo el sombrero y raíces.
    for i in range(7):
        a = rnd.uniform(0, 6.28)
        d = rnd.uniform(3.0, 7.5)
        g.esfera("m_magenta" if i % 2 else "m_neon", rnd.uniform(0.16, 0.3), (1.2 + d * math.cos(a), -0.8 + d * math.sin(a), rnd.uniform(9.0, 14.0)),
                 lados=5, anillos=3)
    for i in range(5):
        a = rnd.uniform(0, 360)
        g.tubo("m_negro", curva((2.0 * math.cos(math.radians(a)), 2.0 * math.sin(math.radians(a)), 0.5), a, 4.5, sube=0.8, cae=1.0,
                                tuerce=rnd.uniform(-50, 50), n=4, semilla=i), radios(0.6, 0.0, 4), lados=5)


def coral_alienigena(g):
    rnd = random.Random(23)
    g.roca("m_roca", 4.6, (0, 0, 0.2), esc=(1, 0.9, 0.28), semilla=4, sub=2, amp=0.25, plano=-0.6)
    # Ramas de coral que se bifurcan: oscuras abajo, magenta luminoso en las puntas (degradado en el atlas).
    puntas = []
    for i, (px, py, a, inc, L, r) in enumerate(((0, 0, 0, 4, 3.4, 0.95), (1.8, 0.6, 20, 28, 2.8, 0.75), (-1.7, 0.9, 150, 30, 2.7, 0.75),
                                               (-0.3, -1.8, 265, 32, 2.6, 0.7), (1.0, -1.4, 310, 40, 2.0, 0.55))):
        ar, ir = math.radians(a), math.radians(inc)
        ramas(g, "m_coral", (px, py, 0.6), (math.cos(ar) * math.sin(ir), math.sin(ar) * math.sin(ir), math.cos(ir)), L, r, 3, rnd,
              abrir=30, hijos=2, encoge=0.74, lados=6, tuerce=0.18, puntas=puntas, r_min=0.14)
    for i, (p, d) in enumerate(puntas):
        g.esfera("m_magenta", 0.26, (p[0] + d[0] * 0.1, p[1] + d[1] * 0.1, p[2] + d[2] * 0.1), lados=6, anillos=4)
    # Abanicos y tubos en la base, con pólipos brillantes.
    for i in range(5):
        a = rnd.uniform(0, 6.28)
        px, py = 3.2 * math.cos(a), 2.9 * math.sin(a)
        h = rnd.uniform(1.0, 2.0)
        g.rev("m_purpura_liso", [(0.3, 0.0), (0.42, h * 0.6), (0.6, h), (0.42, h), (0.3, h * 0.6), (0.0, h * 0.5)], (px, py, 0.5),
              (rnd.uniform(-12, 12), rnd.uniform(-12, 12), 0), lados=7, tapas=(True, False))
        g.esfera("m_neon", 0.3, (px, py, 0.5 + h * 0.8), esc=(1, 1, 0.5), lados=6, anillos=3)
    for i in range(6):
        a = rnd.uniform(0, 6.28)
        g.esfera("m_neon" if i % 2 else "m_magenta", 0.2, (3.9 * math.cos(a), 3.5 * math.sin(a), 0.75), lados=5, anillos=3)


def esporas_suelo(g):
    rnd = random.Random(24)
    g.roca("m_roca", 3.4, (0, 0, 0.05), esc=(1, 0.9, 0.09), semilla=5, sub=2, amp=0.2)
    # Setas pequeñas en corro.
    for i, (px, py, h, r) in enumerate(((0.2, 0.3, 2.6, 1.3), (1.6, -0.6, 1.7, 0.9), (-1.5, 0.2, 1.9, 1.0), (-0.4, 1.7, 1.3, 0.7),
                                       (0.6, -1.8, 1.1, 0.6), (-1.9, -1.4, 0.9, 0.5), (2.2, 1.2, 1.0, 0.55))):
        seta(g, (px, py, 0.2), h, r, inclina=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3)), lados=8, semilla=i,
             puntos="m_magenta" if i < 3 else None)
    # Vainas de esporas: bolas luminosas en tallos y un bejín abierto.
    for i in range(6):
        a = rnd.uniform(0, 6.28)
        d = rnd.uniform(1.8, 2.9)
        h = rnd.uniform(0.7, 1.6)
        px, py = d * math.cos(a), d * math.sin(a)
        g.tubo("m_negro_liso", [(px, py, 0.2), (px + 0.1, py, 0.2 + h * 0.6), (px + 0.25, py + 0.1, 0.2 + h)], [0.1, 0.07, 0.05], lados=4)
        g.esfera("m_neon" if i % 2 else "m_magenta", rnd.uniform(0.2, 0.34), (px + 0.25, py + 0.1, 0.3 + h), esc=(1, 1, 1.25), lados=6, anillos=4)
    g.rev("m_carne", [(0.0, 0.0), (0.6, 0.05), (0.85, 0.5), (0.7, 0.95), (0.4, 1.1), (0.3, 1.0), (0.45, 0.6), (0.0, 0.45)], (-0.6, -2.4, 0.2),
          lados=8)
    g.esfera("m_magenta", 0.3, (-0.6, -2.4, 0.85), lados=6, anillos=3)
    cristales(g, "m_cristal", (2.4, -1.8, 0.15), n=3, r=0.25, h=1.0, semilla=2)


MODELOS = [
    ("arbol_alienigena_01", "vegetacion_monstruo", 5000, arbol_alienigena_01),
    ("arbol_alienigena_02", "vegetacion_monstruo", 5000, arbol_alienigena_02),
    ("hongo_gigante", "vegetacion_monstruo", 5000, hongo_gigante),
    ("coral_alienigena", "vegetacion_monstruo", 5000, coral_alienigena),
    ("esporas_suelo", "vegetacion_monstruo", 5000, esporas_suelo),
]
