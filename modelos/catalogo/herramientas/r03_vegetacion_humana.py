"""Ronda 3: vegetación del planeta humano (modelos 15-19). Estilo cartoon de copas facetadas."""

import math
import random

from comunes import raices


def _copa(g, mat, bolas, semilla=0, sub=2, amp=0.2):
    for i, (x, y, z, r, *esc) in enumerate(bolas):
        e = esc[0] if esc else (1, 1, 0.85)
        g.roca(mat, r, (x, y, z), esc=e, rot=(0, 0, i * 47), semilla=semilla + i, sub=sub, amp=amp, frec=1.3)


def arbol_roble(g):
    rnd = random.Random(15)
    # Tronco grueso con panza, raíces y tres ramas maestras.
    g.tubo("corteza", [(0, 0, -0.3), (0.15, 0.1, 2.5), (-0.2, 0.15, 6.0), (0.1, -0.1, 9.5), (0.0, 0.0, 12.0)],
           [2.3, 1.75, 1.5, 1.45, 1.2], lados=9)
    raices(g, "corteza", (0, 0, 0), 6, 1.8, 2.6, rnd, lados=5)
    for a, inc, L in ((20, 55, 6.5), (140, 50, 6.0), (255, 58, 6.8)):
        ar = math.radians(a)
        d = (math.cos(ar) * math.sin(math.radians(inc)), math.sin(ar) * math.sin(math.radians(inc)), math.cos(math.radians(inc)))
        g.tubo("corteza", [(0, 0, 8.6), (d[0] * L * 0.5, d[1] * L * 0.5, 8.6 + d[2] * L * 0.6 + 0.6),
                           (d[0] * L, d[1] * L, 8.6 + d[2] * L + 1.5)], [1.0, 0.75, 0.45], lados=6)
    # Nudo y hueco en el tronco.
    g.esfera("corteza", 0.7, (1.35, -0.75, 5.2), esc=(0.6, 1, 1), lados=7, anillos=4)
    g.esfera("madera_osc", 0.45, (1.6, -0.9, 5.2), esc=(0.4, 1, 1.2), lados=6, anillos=4)
    # Copa redondeada: bolas facetadas, más claras arriba.
    _copa(g, "hoja", ((0, 0, 15.5, 6.2), (5.2, 1.5, 13.6, 4.6), (-4.8, 2.6, 13.8, 4.8), (-1.5, -5.0, 13.4, 4.6),
                      (3.0, -3.8, 15.0, 4.0), (0.5, 4.8, 15.2, 4.2), (-5.5, -2.2, 15.8, 3.4)), semilla=1)
    _copa(g, "hoja_clara", ((1.0, -1.0, 19.3, 4.2), (-2.6, 1.6, 18.6, 3.4), (3.8, 2.2, 17.6, 3.0)), semilla=20)
    # Mata de hierba y setas al pie.
    for i in range(5):
        a = rnd.uniform(0, 6.28)
        g.cristal("hierba", 0.22, rnd.uniform(1.0, 1.8), (3.3 * math.cos(a), 3.3 * math.sin(a), 0), (rnd.uniform(-15, 15), rnd.uniform(-15, 15), 0),
                  lados=3, punta=0.9, base=1.0)


def _pino(g, x, alto, capas, r_base, semilla):
    rnd = random.Random(semilla)
    rt = r_base * 0.16
    g.tubo("corteza", [(x, 0, -0.2), (x, 0, alto * 0.3), (x, 0, alto * 0.85)], [rt * 1.5, rt, rt * 0.4], lados=7)
    raices(g, "corteza", (x, 0, 0), 4, rt * 1.2, rt * 2.0, rnd, lados=4)
    z = alto * 0.2
    paso = (alto - z) / (capas + 0.35)
    for i in range(capas):
        t = i / (capas - 1)
        r = r_base * (1.0 - 0.72 * t)
        h = paso * 1.75
        # Cada capa: falda con vuelo, cara de abajo y punta.
        g.rev("hoja_pino" if i % 2 == 0 else "hoja", [(rt * 0.6, h * 0.28), (r, 0.0), (r * 0.94, h * 0.12), (r * 0.42, h * 0.62), (0.0, h)],
              (x, 0, z), (rnd.uniform(-3, 3), rnd.uniform(-3, 3), rnd.uniform(0, 45)), lados=8, suave=False)
        z += paso


def arbol_pino(g):
    # Tres alturas en un mismo archivo (tres piezas que comparten atlas).
    for nom, x, alto, capas, r in (("alto", 0.0, 26.0, 6, 5.4), ("medio", 11.0, 18.0, 5, 4.4), ("bajo", -9.5, 11.0, 4, 3.4)):
        g.pieza(nom, pivote=(x, 0, 0))
        _pino(g, x, alto, capas, r, int(alto))


def arbol_frutal(g):
    rnd = random.Random(17)
    g.tubo("corteza", [(0, 0, -0.2), (0.2, 0.0, 2.0), (-0.15, 0.2, 4.2), (0.1, 0.0, 6.0)], [1.0, 0.75, 0.62, 0.5], lados=8)
    raices(g, "corteza", (0, 0, 0), 5, 0.8, 1.4, rnd, lados=4)
    for a, L in ((30, 3.2), (150, 3.0), (270, 3.4)):
        ar = math.radians(a)
        g.tubo("corteza", [(0, 0, 5.0), (math.cos(ar) * L * 0.6, math.sin(ar) * L * 0.6, 6.4), (math.cos(ar) * L, math.sin(ar) * L, 7.6)],
               [0.45, 0.32, 0.2], lados=5)
    bolas = ((0, 0, 9.2, 3.6), (2.9, 1.0, 8.0, 2.7), (-2.7, 1.6, 8.2, 2.8), (-0.6, -3.0, 8.0, 2.7), (0.6, 0.6, 11.2, 2.5))
    _copa(g, "hoja_clara", bolas[:4], semilla=5)
    _copa(g, "hoja", bolas[4:], semilla=9)
    # Frutas naranjas y rojas sobre la copa (colocadas en la superficie de cada bola) y un par caídas.
    n = 0
    for bx, by, bz, br in bolas:
        for k in range(4):
            a = rnd.uniform(0, 6.28)
            el = rnd.uniform(-0.5, 0.7)
            px = bx + br * 0.98 * math.cos(a) * math.cos(el)
            py = by + br * 0.98 * math.sin(a) * math.cos(el)
            pz = bz + br * 0.85 * 0.98 * math.sin(el)
            if math.hypot(px, py) < 2.2:
                continue
            g.esfera("fruta" if n % 3 else "fruta_roja", 0.48, (px, py, pz), lados=8, anillos=5)
            g.cil("corteza", 0.05, 0.3, (px, py, pz + 0.42), lados=4)
            n += 1
    for px, py in ((2.4, -1.8), (-2.0, -2.6), (1.0, 2.8)):
        g.esfera("fruta", 0.46, (px, py, 0.42), lados=8, anillos=5)


def arbusto_01(g):
    rnd = random.Random(18)
    _copa(g, "hoja", ((0, 0, 1.5, 2.3, (1, 1, 0.8)), (2.0, 0.6, 1.1, 1.7, (1, 1, 0.8)), (-1.9, 0.8, 1.2, 1.8, (1, 1, 0.8)),
                      (-0.4, -1.8, 1.0, 1.6, (1, 1, 0.8))), semilla=3)
    _copa(g, "hoja_clara", ((0.5, 0.3, 2.6, 1.5, (1, 1, 0.8)), (-1.2, -0.5, 2.2, 1.2, (1, 1, 0.8))), semilla=8)
    # Ramitas que asoman y florecillas.
    for i in range(4):
        a = rnd.uniform(0, 6.28)
        g.tubo("corteza", [(0.6 * math.cos(a), 0.6 * math.sin(a), 0), (1.6 * math.cos(a), 1.6 * math.sin(a), 0.9)], [0.2, 0.1], lados=4)
    for i in range(9):
        a = rnd.uniform(0, 6.28)
        el = rnd.uniform(0.2, 1.1)
        r = 2.2
        px, py, pz = r * math.cos(a) * math.cos(el) * 1.05, r * math.sin(a) * math.cos(el) * 0.95, 1.4 + r * 0.8 * math.sin(el)
        g.esfera("flor_blanca" if i % 2 else "flor_amarilla", 0.24, (px, py, pz), lados=6, anillos=3)


def hierba_grupo(g):
    rnd = random.Random(19)
    # Briznas con grosor (sección triangular aplastada) que se curvan hacia fuera.
    for i in range(26):
        a = rnd.uniform(0, 6.28)
        d = rnd.uniform(0.0, 1.5) ** 1.0
        h = rnd.uniform(1.4, 3.0) * (1.15 - d * 0.3)
        bx, by = d * math.cos(a), d * math.sin(a)
        cae = rnd.uniform(0.3, 1.0) * (0.4 + d * 0.5)
        pts = [(bx, by, -0.1), (bx + math.cos(a) * cae * 0.25, by + math.sin(a) * cae * 0.25, h * 0.5),
               (bx + math.cos(a) * cae * 0.7, by + math.sin(a) * cae * 0.7, h * 0.85), (bx + math.cos(a) * cae * 1.2, by + math.sin(a) * cae * 1.2, h)]
        g.tubo("hierba", pts, [0.2, 0.17, 0.11, 0.0], lados=3, suave=False, aplastar=0.45)
    # Tres plantas de hoja ancha y flores.
    for i in range(3):
        a = 2.1 * i + 0.4
        bx, by = 1.7 * math.cos(a), 1.7 * math.sin(a)
        for k in range(5):
            b = a + k * 1.256
            g.prisma("hoja_clara", [(0, -0.05), (0.35, 0.35), (0.22, 1.0), (0, 1.35), (-0.22, 1.0), (-0.35, 0.35)], 0.07,
                     (bx, by, 0.05), (62, 0, math.degrees(b)), plano="xy")
    for i, (px, py, h, m) in enumerate(((0.9, -0.9, 2.6, "flor_blanca"), (-1.1, 0.4, 2.2, "flor_amarilla"), (0.2, 1.3, 2.9, "flor_blanca"))):
        g.tubo("hierba", [(px, py, 0), (px + 0.1, py, h * 0.6), (px + 0.2, py + 0.1, h)], 0.06, lados=4, suave=False)
        g.cil(m, 0.42, 0.1, (px + 0.2, py + 0.1, h), (12, 8, 0), lados=6, r2=0.3)
        g.esfera("flor_amarilla" if m == "flor_blanca" else "fruta", 0.17, (px + 0.2, py + 0.1, h + 0.12), lados=6, anillos=3)
    for i in range(3):
        g.roca("piedra", 0.35 + i * 0.1, (1.9 * math.cos(i * 2.2 + 2), 1.9 * math.sin(i * 2.2 + 2), 0.12), semilla=i, sub=1, esc=(1, 1, 0.7))


MODELOS = [
    ("arbol_roble", "vegetacion_humana", 5000, arbol_roble),
    ("arbol_pino", "vegetacion_humana", 5000, arbol_pino),
    ("arbol_frutal", "vegetacion_humana", 5000, arbol_frutal),
    ("arbusto_01", "vegetacion_humana", 5000, arbusto_01),
    ("hierba_grupo", "vegetacion_humana", 5000, hierba_grupo),
]
