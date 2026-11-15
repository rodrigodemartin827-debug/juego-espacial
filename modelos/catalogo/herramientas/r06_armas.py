"""Ronda 6: armas y herramientas (modelos 33-40). Verticales: empuñadura abajo, en el origen el punto de agarre.
Tamaño para un personaje R6 (5 studs de alto)."""

import math


def _mango(g, mat, z0, z1, r=0.13, curva=0.06, lados=7):
    g.tubo(mat, [(0, 0, z0), (curva, 0, (z0 + z1) * 0.4), (-curva * 0.5, 0, (z0 + z1) * 0.75), (0, 0, z1)],
           [r * 1.15, r, r * 0.95, r * 1.05], lados=lados)


def _cabeza_pico(g, mat, z, largo, r, pico2=True, lados=4):
    """Cabeza curva de pico: punta a +X y (si pico2) otra a -X; si no, azuela plana."""
    der = [(0, 0, z), (largo * 0.45, 0, z - 0.02), (largo * 0.8, 0, z - 0.22), (largo, 0, z - 0.55)]
    g.tubo(mat, der, [r, r * 0.8, r * 0.5, 0.0], lados=lados, suave=False, pot=1.0)
    if pico2:
        izq = [(0, 0, z), (-largo * 0.45, 0, z - 0.02), (-largo * 0.8, 0, z - 0.22), (-largo, 0, z - 0.55)]
        g.tubo(mat, izq, [r, r * 0.8, r * 0.5, 0.0], lados=lados, suave=False, pot=1.0)
    else:
        g.prisma(mat, [(0, -r * 0.8), (-largo * 0.55, -r * 0.7), (-largo * 0.8, -r * 1.7), (-largo * 0.8, r * 1.7), (-largo * 0.55, r * 0.7),
                       (0, r * 0.8)], r * 0.9, (0, 0, z - 0.06), (0, -10, 0), plano="xy", sup=0.9)


def pico_madera(g):
    _mango(g, "madera", -0.9, 3.5, r=0.14, curva=0.09)
    # Cabeza de piedra tallada atada con cuerda.
    _cabeza_pico(g, "piedra", 3.15, 1.55, 0.3)
    g.roca("piedra", 0.34, (0, 0, 3.15), esc=(1.0, 0.9, 0.9), semilla=3, sub=1, amp=0.2)
    for i, a in enumerate((35, -35, 0)):
        g.toro("cuerda", 0.26, 0.06, (0, 0, 3.12), (a, 90 if i == 2 else 0, 0), seg=8, lados=4)
    g.toro("cuerda", 0.17, 0.05, (0, 0, 2.7), seg=8, lados=4)
    g.toro("cuerda", 0.17, 0.05, (0, 0, -0.7), seg=8, lados=4)
    g.ancla("Agarre", (0, 0, 0))


def pico_hierro(g):
    _mango(g, "madera_osc", -1.0, 3.7, r=0.14, curva=0.05)
    _cabeza_pico(g, "hierro", 3.35, 1.8, 0.3)
    g.caja("hierro_osc", (0.62, 0.58, 0.62), (0, 0, 3.35), bisel=0.08)
    for s in (-1, 1):
        g.caja("hierro", (0.14, 0.62, 0.3), (s * 0.62, 0, 3.32))
    g.cil("hierro_osc", 0.19, 0.25, (0, 0, -1.1), lados=7, bisel=0.04)
    g.cil("hierro_osc", 0.17, 0.2, (0, 0, 2.7), lados=7)
    for z in (-0.5, -0.2, 0.1, 0.4):
        g.toro("cuero", 0.15, 0.045, (0, 0, z), seg=7, lados=4)
    g.ancla("Agarre", (0, 0, 0))


def pico_acero(g):
    _mango(g, "madera_osc", -1.1, 4.0, r=0.14, curva=0.0)
    # Acero pulido: pico a un lado y azuela al otro, con refuerzos dorados y núcleo de energía.
    _cabeza_pico(g, "acero", 3.6, 2.1, 0.32, pico2=False, lados=4)
    g.caja("acero", (0.7, 0.62, 0.74), (0, 0, 3.6), bisel=0.1)
    g.cil("oro", 0.36, 0.14, (0, 0, 3.98), lados=8)
    g.cil("oro", 0.2, 0.3, (0, 0, 4.1), lados=6, r2=0.0)
    for s in (-1, 1):
        g.caja("h_neon", (0.34, 0.06, 0.34), (0, s * 0.31, 3.6), rot=(0, 45, 0))
        g.caja("oro", (0.12, 0.66, 0.5), (s * 0.5, 0, 3.6))
    g.cil("oro", 0.18, 0.16, (0, 0, 2.9), lados=7)
    g.cil("cuero", 0.165, 1.5, (0, 0, -0.75), lados=7)
    for z in (-0.6, -0.3, 0.0, 0.3, 0.6):
        g.toro("hierro_osc", 0.17, 0.03, (0, 0, z), seg=7, lados=3)
    g.cil("acero", 0.22, 0.3, (0, 0, -1.25), lados=7, bisel=0.06)
    g.ancla("Agarre", (0, 0, 0))


def _hoja(g, mat, z0, largo, ancho, grosor, punta=0.22, estrecha=0.8):
    """Hoja de sección de rombo que se estrecha hasta la punta."""
    def rombo(z, w, t):
        return [(w, 0, z), (0, t, z), (-w, 0, z), (0, -t, z)]
    g.loft(mat, [rombo(z0, ancho, grosor), rombo(z0 + largo * 0.5, ancho * (1 + estrecha) / 2, grosor * 0.9),
                 rombo(z0 + largo * (1 - punta), ancho * estrecha, grosor * 0.8), [(0, 0, z0 + largo)]], suave=False)


def espada_hierro(g):
    _hoja(g, "hierro", 0.75, 3.6, 0.3, 0.085)
    g.caja("hierro_osc", (1.5, 0.3, 0.24), (0, 0, 0.68), bisel=0.05)
    for s in (-1, 1):
        g.caja("hierro_osc", (0.26, 0.34, 0.34), (s * 0.75, 0, 0.68), bisel=0.05)
    g.cil("cuero", 0.13, 1.1, (0, 0, -0.5), lados=7)
    for z in (-0.3, -0.05, 0.2, 0.45):
        g.toro("madera_osc", 0.135, 0.035, (0, 0, z), seg=7, lados=3)
    g.esfera("hierro_osc", 0.21, (0, 0, -0.62), esc=(1, 1, 0.85), lados=8, anillos=5)
    g.ancla("Agarre", (0, 0, 0))
    g.ancla("Punta", (0, 0, 4.35))


def espada_acero(g):
    # Más grande y brillante: hoja ancha con canal, guarda curva dorada y gema.
    _hoja(g, "acero", 0.95, 4.9, 0.42, 0.1, punta=0.18, estrecha=0.85)
    for s in (-1, 1):
        g.caja("hierro", (0.16, 0.05, 3.2), (0, s * 0.085, 2.9))
    g.prisma("acero", [(-0.5, 0.0), (0.5, 0.0), (0.3, 0.55), (-0.3, 0.55)], 0.26, (0, 0, 0.92), plano="xz")
    for s in (-1, 1):
        g.tubo("oro", [(0, 0, 0.86), (s * 0.6, 0, 0.84), (s * 1.0, 0, 1.0), (s * 1.25, 0, 1.35)], [0.19, 0.16, 0.13, 0.0], lados=6)
    g.caja("oro", (0.5, 0.36, 0.34), (0, 0, 0.86), bisel=0.06)
    g.esfera("gema_azul", 0.14, (0, -0.2, 0.86), esc=(1, 0.6, 1), lados=6, anillos=4)
    g.esfera("gema_azul", 0.14, (0, 0.2, 0.86), esc=(1, 0.6, 1), lados=6, anillos=4)
    g.cil("cuero", 0.14, 1.35, (0, 0, -0.7), lados=8)
    for i in range(6):
        g.toro("oro", 0.145, 0.028, (0, 0, -0.55 + i * 0.22), seg=8, lados=3)
    g.cil("oro", 0.2, 0.14, (0, 0, -0.82), lados=8)
    g.rev("oro", [(0.0, -0.4), (0.2, -0.3), (0.27, -0.12), (0.2, 0.05), (0.0, 0.1)], (0, 0, -0.95), lados=8)
    g.esfera("gema_azul", 0.1, (0, 0, -1.37), lados=6, anillos=4)
    g.ancla("Agarre", (0, 0, 0))
    g.ancla("Punta", (0, 0, 5.85))


def hacha_hierro(g):
    _mango(g, "madera_osc", -1.3, 4.3, r=0.15, curva=0.07)
    # Hoja barbada con filo de acero y pico trasero.
    hoja = [(0.12, 3.05), (0.9, 2.75), (1.65, 2.2), (1.85, 3.3), (1.65, 4.45), (0.9, 4.2), (0.12, 3.95)]
    g.prisma("hierro", hoja, 0.24, (0, 0, 0), plano="xz")
    filo = [(1.6, 2.1), (1.95, 3.3), (1.6, 4.55), (2.12, 3.9), (2.22, 3.3), (2.1, 2.6)]
    g.prisma("acero", filo, 0.08, (0, 0, 0), plano="xz")
    g.caja("hierro_osc", (0.5, 0.46, 1.15), (0, 0, 3.5), bisel=0.07)
    g.tubo("hierro", [(-0.2, 0, 3.5), (-0.7, 0, 3.55), (-1.15, 0, 3.3)], [0.2, 0.14, 0.0], lados=4, suave=False, pot=1.0)
    g.cil("hierro_osc", 0.2, 0.22, (0, 0, 4.2), lados=6, r2=0.0)
    for z in (2.2, 2.45):
        g.toro("hierro_osc", 0.16, 0.04, (0, 0, z), seg=7, lados=3)
    g.cil("cuero", 0.17, 1.4, (0, 0, -0.9), lados=7)
    for z in (-0.7, -0.4, -0.1, 0.2):
        g.toro("madera_osc", 0.175, 0.03, (0, 0, z), seg=7, lados=3)
    g.cil("hierro_osc", 0.21, 0.24, (0, 0, -1.45), lados=7, bisel=0.05)
    g.ancla("Agarre", (0, 0, 0))


def escudo_hierro(g):
    # Redondo, de tablas con cerco y umbo de hierro; emblema naranja de los humanos. Mira a -Y; el origen es el agarre.
    with g.grupo((0, 0, 0), (90, 0, 0)):
        g.rev("tablas", [(0.0, 0.0), (1.65, 0.0), (1.65, 0.16), (1.0, 0.3), (0.0, 0.36)], (0, 0, 0.1), lados=16)
        g.toro("hierro", 1.65, 0.13, (0, 0, 0.2), seg=16, lados=5)
        g.rev("hierro", [(0.55, 0.0), (0.55, 0.12), (0.4, 0.34), (0.0, 0.46)], (0, 0, 0.42), lados=10)
        # Emblema: cuatro puntas naranjas alrededor del umbo y remaches.
        for i in range(4):
            with g.grupo((0, 0, 0.42), (0, 0, 45 + 90 * i)):
                g.prisma("h_naranja_liso", [(0.62, -0.2), (1.3, 0.0), (0.62, 0.2)], 0.1, (0, 0, 0), plano="xy")
        for i in range(8):
            a = 2 * math.pi * i / 8
            g.esfera("hierro_osc", 0.07, (1.65 * math.cos(a), 1.65 * math.sin(a), 0.32), lados=5, anillos=3)
    # Trasera: asa de cuero y travesaño.
    g.tubo("cuero", [(-0.55, 0.0, 0), (-0.3, 0.3, 0), (0.3, 0.3, 0), (0.55, 0.0, 0)], 0.09, lados=5)
    g.caja("madera_osc", (0.3, 0.1, 2.8), (0, -0.05, 0))
    g.ancla("Agarre", (0, 0.3, 0))


def escudo_acero(g):
    # Más grande y ornamentado: forma de cometa, bisel dorado, cruz naranja y gema central.
    forma = [(-1.45, 1.9), (-0.8, 2.25), (0.0, 2.05), (0.8, 2.25), (1.45, 1.9), (1.5, 0.4), (1.05, -1.1), (0.0, -2.4), (-1.05, -1.1),
             (-1.5, 0.4)]
    g.prisma("oro", forma, 0.16, (0, -0.1, 0), plano="xz")
    g.prisma("acero", [(a * 0.9, b * 0.91 + 0.02) for a, b in forma], 0.2, (0, -0.2, 0), plano="xz", sup=1.0)
    g.prisma("acero", [(a * 0.8, b * 0.82 + 0.03) for a, b in forma], 0.14, (0, -0.33, 0), plano="xz")
    # Cruz / franja naranja y alas doradas.
    g.caja("h_naranja_liso", (0.36, 0.08, 3.5), (0, -0.42, -0.1))
    g.caja("h_naranja_liso", (2.2, 0.08, 0.36), (0, -0.42, 0.9))
    for s in (-1, 1):
        g.prisma("oro", [(s * 0.3, 0.2), (s * 1.05, 0.55), (s * 0.95, -0.1), (s * 0.5, -0.55)], 0.07, (0, -0.42, -0.3), plano="xz")
    g.rev("oro", [(0.5, 0.0), (0.5, 0.08), (0.34, 0.2), (0.0, 0.24)], (0, -0.4, 0.9), (90, 0, 0), lados=8)
    g.esfera("gema_azul", 0.22, (0, -0.62, 0.9), esc=(1, 0.6, 1), lados=8, anillos=4)
    for px, pz in ((-1.2, 1.75), (1.2, 1.75), (-1.25, 0.4), (1.25, 0.4), (-0.85, -1.0), (0.85, -1.0), (0, -2.0)):
        g.esfera("oro", 0.08, (px, -0.42, pz), lados=5, anillos=3)
    g.tubo("cuero", [(-0.6, 0.0, 0.3), (-0.3, 0.32, 0.3), (0.3, 0.32, 0.3), (0.6, 0.0, 0.3)], 0.09, lados=5)
    g.tubo("cuero", [(-0.6, 0.0, -0.6), (-0.3, 0.22, -0.6), (0.3, 0.22, -0.6), (0.6, 0.0, -0.6)], 0.08, lados=5)
    g.ancla("Agarre", (0, 0.32, 0.3))


MODELOS = [
    ("pico_madera", "armas", 5000, pico_madera),
    ("pico_hierro", "armas", 5000, pico_hierro),
    ("pico_acero", "armas", 5000, pico_acero),
    ("espada_hierro", "armas", 5000, espada_hierro),
    ("espada_acero", "armas", 5000, espada_acero),
    ("hacha_hierro", "armas", 5000, hacha_hierro),
    ("escudo_hierro", "armas", 5000, escudo_hierro),
    ("escudo_acero", "armas", 5000, escudo_acero),
]
