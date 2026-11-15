"""Ronda 2: edificios de los monstruos (modelos 9-14). Orgánicos, oscuros, con cristales y vetas violeta."""

import math
import random

from comunes import colmillo, cristales, curva, radios, runa, seta


def _arco(g, mat, yy, r_ext, r_int, alto, ancho, n=10, ruido=0.5, semilla=0):
    """Arco con grosor (sección de túnel) deformado con ruido."""
    ext = [(r_ext * math.cos(math.pi * i / n), alto * r_ext / r_int * math.sin(math.pi * i / n)) for i in range(n + 1)]
    inte = [(r_int * math.cos(math.pi * i / n), alto * math.sin(math.pi * i / n)) for i in range(n + 1)]
    vs = g.prisma(mat, ext + inte[::-1], ancho, (0, yy, 0), plano="xz")
    g.ruido(vs, ruido, 0.25, semilla)
    return vs


def guarida_monstruo(g):
    rnd = random.Random(9)
    # Suelo de roca y la bóveda de la cueva: arcos que se van cerrando hacia el fondo.
    g.roca("m_roca", 15.0, (0, 2, 0), esc=(1.15, 1.2, 0.07), semilla=3, sub=2, amp=0.2)
    for i, (yy, re, ri, al) in enumerate(((-8.0, 10.5, 7.0, 9.0), (-4.5, 11.5, 7.4, 9.6), (-0.5, 11.5, 6.8, 8.6),
                                          (3.5, 10.0, 5.4, 6.6), (7.0, 8.4, 3.4, 4.2))):
        _arco(g, "m_roca_vetas", yy, re, ri, al, 4.6, n=9, ruido=0.9, semilla=i)
    g.roca("m_roca_vetas", 7.5, (0, 10.5, 2.0), esc=(1.1, 0.8, 0.95), semilla=5, sub=2, plano=-0.3)
    # Rocas que arropan los lados y el techo.
    for i, (px, py, pz, r) in enumerate(((-10.5, -3, 1.5, 4.6), (10.8, -1, 1.5, 5.0), (-9.5, 5, 1.5, 4.8), (9.5, 6, 1.2, 4.4),
                                        (-4.5, 2, 12.6, 3.8), (4.5, 4, 11.0, 3.6), (0.5, -3.5, 13.6, 3.0))):
        g.roca("m_roca" if i % 2 else "m_roca_vetas", r, (px, py, pz), esc=(1, 1.1, 0.9), rot=(0, 0, i * 40), semilla=20 + i,
               sub=2, plano=-0.4 if pz < 2 else None)
    # Fondo de la cueva: negro con un resplandor violeta.
    g.caja("m_negro_liso", (12.5, 0.6, 9.5), (0, 3.0, 4.2))
    g.esfera("m_neon", 1.8, (0, 2.4, 3.2), esc=(1.6, 0.3, 1.2), lados=8, anillos=4)
    # Colmillos de hueso en la boca y garras a los lados.
    for i in range(7):
        a = math.pi * (i + 0.5) / 7
        px, pz = 6.9 * math.cos(a), 8.9 * math.sin(a)
        if pz > 3.0:
            colmillo(g, "m_hueso", (px, -9.6, pz + 0.3), 2.6 - abs(i - 3) * 0.25, 0.5, rot=(180 + 8, math.degrees(a) - 90, 0),
                     curvo=0.15)
    for s in (-1, 1):
        for k in range(3):
            pts = curva((s * (7.5 + k * 1.3), -9.0 + k * 1.6, 0.2), -90 - s * (20 + k * 12), 4.5 + k, sube=5.0 + k * 1.2,
                        tuerce=s * -70, n=5, semilla=k)
            pts = [(p[0], p[1], p[2]) for p in pts]
            g.tubo("m_hueso", pts, radios(0.75, 0.0, 5), lados=6)
    # Cristales púrpura brotando de la roca.
    cristales(g, "m_cristal", (-5.5, -1.5, 13.6), n=5, r=1.1, h=6.5, semilla=1)
    cristales(g, "m_cristal", (6.5, 2.5, 12.0), n=4, r=0.9, h=5.0, semilla=2)
    cristales(g, "m_cristal", (-12.5, -7.0, 0.3), n=5, r=1.0, h=5.5, semilla=3)
    cristales(g, "m_cristal", (12.8, -6.0, 0.3), n=4, r=0.8, h=4.2, semilla=4)
    cristales(g, "m_cristal", (11.5, 9.5, 2.5), n=4, r=0.9, h=4.6, semilla=5)
    cristales(g, "m_cristal", (-11.0, 10.0, 2.8), n=3, r=0.7, h=3.6, semilla=6)
    cristales(g, "m_cristal", (1.5, 9.5, 9.0), n=3, r=0.7, h=3.4, semilla=7)
    # Raíces / tentáculos por el suelo.
    for i in range(7):
        a = rnd.uniform(0, 360)
        b = (13.0 * math.cos(math.radians(a)), 2 + 13.0 * math.sin(math.radians(a)), 0.3)
        if b[1] < -8 and abs(b[0]) < 7:
            continue
        g.tubo("m_negro", curva(b, a, 6.0, sube=1.4, cae=1.6, tuerce=rnd.uniform(-60, 60), n=5, semilla=i),
               radios(0.9, 0.0, 5), lados=6)
    g.ancla("Entrada", (0, -10.0, 0.5))
    g.ancla("LuzInterior", (0, 0, 3.0))


def torre_cristal_oscuro(g):
    rnd = random.Random(10)
    g.roca("m_roca", 11.0, (0, 0, 0), esc=(1.0, 1.0, 0.16), semilla=2, sub=2, amp=0.22)
    for i in range(6):
        a = i * 60 + 15
        g.roca("m_roca_vetas", 3.2, (7.5 * math.cos(math.radians(a)), 7.5 * math.sin(math.radians(a)), 0.8), semilla=i,
               sub=1, esc=(1, 1, 0.8))
    # Fuste: tres tramos de cristal negro facetado, cada uno girado y más fino.
    tramos = ((6.0, 26.0, 0.0, 0), (4.6, 24.0, 22.0, 30), (3.3, 26.0, 42.0, 60))
    for r, h, z0, giro in tramos:
        g.rev("m_cristal_osc", [(r * 0.8, 0.0), (r, h * 0.25), (r * 0.82, h * 0.9), (r * 0.5, h)], (0, 0, z0), (0, 0, giro),
              lados=6, suave=False)
    g.cristal("m_cristal_osc", 2.6, 16.0, (0, 0, 64.0), (0, 0, 30), lados=6, punta=0.75, base=0.8)
    # Collares de esquirlas en cada unión y corona flotante en la punta.
    for z0, r, n in ((22.0, 5.4, 6), (42.0, 4.0, 6), (64.0, 2.8, 5)):
        for i in range(n):
            a = 2 * math.pi * i / n + z0
            inc = 38 + rnd.uniform(-8, 8)
            g.cristal("m_cristal_osc" if i % 2 else "m_cristal", r * 0.22, r * 1.3 * rnd.uniform(0.8, 1.2),
                      (r * 0.8 * math.cos(a), r * 0.8 * math.sin(a), z0 - 1.0),
                      (inc * math.sin(a), -inc * math.cos(a), 0), lados=5)
    for i in range(6):
        a = 2 * math.pi * i / 6
        g.cristal("m_cristal", 0.5, 3.2, (4.6 * math.cos(a), 4.6 * math.sin(a), 70.0 + (i % 2) * 2.0), (0, 0, i * 20), lados=4,
                  punta=0.5, base=0.0)
        g.cristal("m_cristal", 0.5, 1.6, (4.6 * math.cos(a), 4.6 * math.sin(a), 70.0 + (i % 2) * 2.0), (180, 0, i * 20), lados=4,
                  punta=1.0, base=1.0)
    g.cristal("m_neon", 0.9, 4.0, (0, 0, 79.0), lados=4, punta=0.5, base=0.0)
    g.cristal("m_neon", 0.9, 2.0, (0, 0, 79.0), (180, 0, 0), lados=4, punta=1.0, base=1.0)
    # Agujas secundarias inclinadas en la base.
    for i, (a, r, h, inc) in enumerate(((20, 2.6, 24, 16), (140, 2.2, 19, 20), (255, 2.8, 28, 13), (320, 1.6, 13, 26),
                                       (85, 1.4, 11, 28), (200, 1.5, 12, 24))):
        ar = math.radians(a)
        g.cristal("m_cristal_osc", r, h, (6.2 * math.cos(ar), 6.2 * math.sin(ar), 0.5), (inc * math.sin(ar), -inc * math.cos(ar), a),
                  lados=6, punta=0.35)
        g.cristal("m_cristal", r * 0.3, h * 0.35, (8.6 * math.cos(ar + 0.4), 8.6 * math.sin(ar + 0.4), 0.6),
                  (30 * math.sin(ar + 0.4), -30 * math.cos(ar + 0.4), 0), lados=5)
    # Puerta: arco de cristal con resplandor y runas.
    for s in (-1, 1):
        g.cristal("m_purpura_liso", 0.9, 8.5, (s * 2.4, -5.2, 0.5), (0, s * 10, 0), lados=5, punta=0.3)
    g.caja("m_neon", (3.4, 0.3, 6.0), (0, -5.0, 3.6), sup=(0.25, 1))
    for i in range(3):
        runa(g, "m_magenta", (0, -5.75 + i * 0.25, 9.0 + i * 2.2), (-8, 0, 0), 1.3 - i * 0.15, semilla=i + 1, grosor=0.2)
    g.ancla("Puerta", (0, -6.5, 0.5))
    g.ancla("Punta", (0, 0, 83.0))


def nido_monstruo(g):
    rnd = random.Random(11)
    g.roca("m_roca", 12.5, (0, 0, 0), esc=(1.0, 1.0, 0.1), semilla=4, sub=2, amp=0.2)
    # Cuenco de carne con borde grueso y cúpula abierta de costillas.
    vs = g.rev("m_carne", [(0.0, 0.3), (7.0, 0.3), (9.4, 1.6), (10.0, 4.0), (9.3, 6.2), (8.2, 6.6), (7.4, 5.8), (7.6, 4.0),
                           (6.0, 2.2), (0.0, 1.8)], (0, 0, 0), lados=14)
    g.ruido(vs, 0.45, 0.3, 2)
    for i in range(9):
        a = 360 * i / 9 + 10
        ar = math.radians(a)
        if 235 < a < 305:
            continue                                   # hueco de entrada al frente
        b = (9.0 * math.cos(ar), 9.0 * math.sin(ar), 5.6)
        pts = [b, (10.6 * math.cos(ar), 10.6 * math.sin(ar), 10.0), (8.6 * math.cos(ar), 8.6 * math.sin(ar), 14.5),
               (4.6 * math.cos(ar + 0.25), 4.6 * math.sin(ar + 0.25), 17.6), (1.6 * math.cos(ar + 0.5), 1.6 * math.sin(ar + 0.5), 18.6)]
        g.tubo("m_negro", pts, [1.25, 1.0, 0.75, 0.45, 0.0], lados=6)
        g.cristal("m_cristal", 0.4, 2.2, (10.2 * math.cos(ar), 10.2 * math.sin(ar), 9.6), (50 * math.sin(ar), -50 * math.cos(ar), 0),
                  lados=5)
    # Membranas entre costillas alternas (velo con grosor).
    for i in range(0, 9, 2):
        a0, a1 = math.radians(360 * i / 9 + 10), math.radians(360 * (i + 1) / 9 + 10)
        am = math.degrees((a0 + a1) / 2)
        if 235 < am < 305:
            continue
        g.loft("m_purpura_liso", [[(9.2 * math.cos(a0), 9.2 * math.sin(a0), 6.0), (9.2 * math.cos(a1), 9.2 * math.sin(a1), 6.0),
                                   (8.9 * math.cos(a1), 8.9 * math.sin(a1), 6.0), (8.9 * math.cos(a0), 8.9 * math.sin(a0), 6.0)],
                                  [(10.2 * math.cos(a0), 10.2 * math.sin(a0), 10.0), (10.2 * math.cos(a1), 10.2 * math.sin(a1), 10.0),
                                   (9.9 * math.cos(a1), 9.9 * math.sin(a1), 10.0), (9.9 * math.cos(a0), 9.9 * math.sin(a0), 10.0)],
                                  [(8.4 * math.cos(a0), 8.4 * math.sin(a0), 14.0), (8.4 * math.cos(a1), 8.4 * math.sin(a1), 14.0),
                                   (8.1 * math.cos(a1), 8.1 * math.sin(a1), 14.0), (8.1 * math.cos(a0), 8.1 * math.sin(a0), 14.0)]],
               suave=False)
    # Huevos con vetas luminosas, apiñados en el cuenco.
    for i, (px, py, r) in enumerate(((0, 0, 2.2), (3.4, 1.2, 1.7), (-3.0, 2.2, 1.8), (-1.6, -3.2, 1.6), (2.4, -2.8, 1.5),
                                    (0.8, 4.2, 1.4), (-4.8, -0.8, 1.3), (5.2, -0.8, 1.2))):
        g.esfera("m_huevo", r, (px, py, 2.0 + r * 1.15), esc=(1, 1, 1.35), rot=(rnd.uniform(-14, 14), rnd.uniform(-14, 14), 0),
                 lados=10, anillos=6)
    g.esfera("m_neon", 5.5, (0, 0, 2.2), esc=(1, 1, 0.12), lados=12, anillos=4)
    # Esporas: sacos brillantes en tallos alrededor, y huevos sueltos fuera.
    for i in range(8):
        a = rnd.uniform(0, 360)
        ar = math.radians(a)
        d = rnd.uniform(10.6, 12.0)
        h = rnd.uniform(2.5, 5.0)
        b = (d * math.cos(ar), d * math.sin(ar), 0.6)
        pts = [b, (b[0] * 1.03, b[1] * 1.03, 0.6 + h * 0.6), (b[0] * 1.08 + 0.3, b[1] * 1.08, 0.6 + h)]
        g.tubo("m_negro_liso", pts, [0.3, 0.2, 0.14], lados=5)
        g.esfera("m_magenta" if i % 2 else "m_neon", rnd.uniform(0.5, 0.85), pts[-1], esc=(1, 1, 1.25), lados=8, anillos=5)
    for i, a in enumerate((250, 290, 215)):
        ar = math.radians(a)
        g.esfera("m_huevo", 1.0, (11.6 * math.cos(ar), 11.6 * math.sin(ar), 1.4), esc=(1, 1, 1.35), rot=(20, 10 * i, 0), lados=8,
                 anillos=5)
    for i in range(6):
        a = rnd.uniform(0, 360)
        g.tubo("m_negro", curva((9.0 * math.cos(math.radians(a)), 9.0 * math.sin(math.radians(a)), 0.4), a, 5.5, sube=1.2, cae=1.4,
                                tuerce=rnd.uniform(-50, 50), n=5, semilla=i), radios(0.8, 0.0, 5), lados=6)
    g.ancla("Huevos", (0, 0, 4.0))


def altar_monstruo(g):
    # Plataforma ritual hexagonal de tres escalones.
    for i, (r, z, h, m) in enumerate(((12.0, 0.0, 1.2, "m_roca"), (9.6, 1.2, 1.1, "m_roca_vetas"), (7.2, 2.3, 1.0, "m_roca"))):
        g.cil(m, r, h, (0, 0, z), (0, 0, 30), lados=6, r2=r - 0.4, suave=False)
    Z = 3.3
    # Círculo de runas brillantes: anillo, radios y glifos tumbados en la losa.
    g.toro("m_neon", 5.6, 0.12, (0, 0, Z + 0.03), seg=24, lados=4)
    g.toro("m_neon", 2.6, 0.1, (0, 0, Z + 0.03), seg=16, lados=4)
    for i in range(6):
        a = 60 * i
        ar = math.radians(a)
        g.caja("m_neon", (2.7, 0.14, 0.1), (4.1 * math.cos(ar), 4.1 * math.sin(ar), Z + 0.03), rot=(0, 0, a))
        ar2 = math.radians(a + 30)
        runa(g, "m_magenta", (4.2 * math.cos(ar2), 4.2 * math.sin(ar2), Z + 0.05), (90, 0, a + 30 + 90), 1.5, semilla=i + 3,
             grosor=0.12)
        # Runas en la cara de los escalones.
        runa(g, "m_magenta", (10.05 * math.cos(ar), 10.05 * math.sin(ar), 0.6), (0, 0, a + 90), 0.9, semilla=i + 11, grosor=0.2)
        runa(g, "m_neon", (7.95 * math.cos(ar), 7.95 * math.sin(ar), 1.75), (0, 0, a + 90), 0.8, semilla=i + 21, grosor=0.2)
    # Pedestal con garras de hueso que sostienen el cristal central flotante.
    g.cil("m_roca_vetas", 1.9, 1.6, (0, 0, Z), lados=6, r2=1.4, suave=False)
    for i in range(4):
        a = 90 * i + 45
        ar = math.radians(a)
        pts = [(1.5 * math.cos(ar), 1.5 * math.sin(ar), Z + 1.2), (2.9 * math.cos(ar), 2.9 * math.sin(ar), Z + 3.6),
               (2.6 * math.cos(ar), 2.6 * math.sin(ar), Z + 6.2), (1.5 * math.cos(ar), 1.5 * math.sin(ar), Z + 7.8)]
        g.tubo("m_hueso", pts, [0.6, 0.48, 0.34, 0.0], lados=6)
    g.pieza("cristal_central", pivote=(0, 0, Z + 5.2))
    g.cristal("m_cristal", 1.5, 3.6, (0, 0, Z + 5.2), lados=6, punta=0.7, base=1.0)
    g.cristal("m_cristal", 1.5, 2.6, (0, 0, Z + 5.2), (180, 0, 0), lados=6, punta=1.0, base=1.0)
    g.pieza("cuerpo")
    # Seis obeliscos de cristal oscuro en las esquinas, con punta luminosa.
    for i in range(6):
        a = 60 * i + 30
        ar = math.radians(a)
        px, py = 9.9 * math.cos(ar), 9.9 * math.sin(ar)
        h = 9.0 if i % 2 else 12.0
        g.cristal("m_cristal_osc", 1.15, h, (px, py, 1.0), (4 * math.sin(ar), -4 * math.cos(ar), a), lados=5, punta=0.25)
        g.cristal("m_cristal", 0.45, 1.8, (px * 0.985, py * 0.985, h + 1.3), lados=4, punta=0.5, base=0.0)
        cristales(g, "m_cristal", (px * 1.12, py * 1.12, 0.6), n=3, r=0.45, h=2.2, semilla=i, centro=False)
    # Escalera al frente y cuencos de fuego violeta.
    for i in range(3):
        g.bloque("m_roca", (-2.6, -12.4 + i * 1.3, 0), (2.6, -9.0 + i * 0.4, 0.8 + i * 1.05))
    for s in (-1, 1):
        g.rev("m_hueso", [(0.0, 0.0), (0.7, 0.0), (0.35, 0.5), (0.35, 2.2), (1.1, 3.0), (0.9, 3.0), (0.0, 2.6)], (s * 4.0, -10.6, 0.9),
              lados=8)
        g.rev("m_lava", [(0.0, 0.0), (0.85, 0.0), (0.55, 0.7), (0.0, 1.6)], (s * 4.0, -10.6, 3.7), lados=6, suave=False)
    g.ancla("Cristal", (0, 0, Z + 5.2))
    g.ancla("Centro", (0, 0, Z))


def mercado_monstruo(g):
    rnd = random.Random(13)
    g.roca("m_roca", 12.0, (0, 0, 0), esc=(1.0, 0.85, 0.08), semilla=6, sub=2, amp=0.18)
    # Tres setas gigantes hacen de techo.
    seta(g, (0, 2.5, 0.4), 15.5, 10.5, inclina=(0.6, -1.6), lados=14, semilla=1, r_tallo=1.5, puntos="m_magenta")
    seta(g, (-7.5, 0.5, 0.4), 10.0, 5.2, inclina=(-1.4, -0.8), lados=10, semilla=2, r_tallo=0.9)
    seta(g, (8.0, 1.5, 0.4), 8.0, 4.4, inclina=(1.2, -0.6), lados=10, semilla=3, r_tallo=0.8)
    # Mostrador curvo de roca negra con tapa de hueso.
    for i in range(7):
        a = math.radians(205 + i * 21.5)
        px, py = 6.8 * math.cos(a), 0.5 + 6.2 * math.sin(a)
        g.caja("m_roca_vetas", (2.7, 1.5, 3.0), (px, py, 0.4), rot=(0, 0, math.degrees(a) + 90), base=True, sup=(0.95, 0.8))
        g.caja("m_hueso", (2.8, 1.9, 0.3), (px, py, 3.4), rot=(0, 0, math.degrees(a) + 90), base=True, bisel=0.06)
    # Mercancía: frascos luminosos, cristales, cuencos y un cráneo con cuernos.
    for i in range(6):
        a = math.radians(212 + i * 23)
        px, py = 6.8 * math.cos(a), 0.5 + 6.2 * math.sin(a)
        if i % 3 == 0:
            g.rev("m_purpura_liso", [(0.0, 0.0), (0.4, 0.0), (0.55, 0.5), (0.3, 0.9), (0.3, 1.1), (0.0, 1.1)], (px, py, 3.7), lados=8)
            g.esfera("m_magenta", 0.3, (px, py, 4.05), lados=6, anillos=4)
        elif i % 3 == 1:
            cristales(g, "m_cristal", (px, py, 3.75), n=3, r=0.3, h=1.3, semilla=i)
        else:
            g.rev("m_hueso", [(0.0, 0.0), (0.35, 0.0), (0.75, 0.45), (0.65, 0.45), (0.0, 0.2)], (px, py, 3.7), lados=8)
            g.esfera("m_neon", 0.42, (px, py, 4.05), esc=(1, 1, 0.5), lados=6, anillos=4)
    g.esfera("m_hueso", 0.75, (0.5, -5.6, 4.35), esc=(1, 1.2, 0.9), lados=8, anillos=5)
    for s in (-1, 1):
        colmillo(g, "m_hueso", (0.5 + s * 0.5, -5.5, 4.7), 1.3, 0.2, rot=(0, s * 50, 0), curvo=0.4)
        g.esfera("m_magenta", 0.14, (0.5 + s * 0.3, -6.25, 4.45), lados=5, anillos=3)
    # Estantes de costillas al fondo con frascos.
    for s in (-1, 1):
        g.tubo("m_hueso", [(s * 3.6, 5.2, 0.4), (s * 3.9, 5.6, 4.0), (s * 3.2, 5.0, 7.6)], [0.4, 0.32, 0.2], lados=6)
    for z in (3.0, 5.4):
        g.caja("m_roca", (7.2, 1.3, 0.3), (0, 5.3, z))
        for i in range(5):
            px = -2.6 + i * 1.3
            m = ("m_magenta", "m_neon", "m_lava")[(i + int(z)) % 3]
            g.rev("m_negro_liso", [(0.0, 0.0), (0.35, 0.0), (0.45, 0.4), (0.22, 0.75), (0.0, 0.75)], (px, 5.3, z + 0.15), lados=6)
            g.esfera(m, 0.26, (px, 5.3, z + 1.15), lados=6, anillos=4)
    # Faroles de cristal colgando del sombrero grande y toldo de tela.
    for i, (px, py, largo) in enumerate(((-4.5, -5.0, 4.5), (5.5, -4.5, 5.5), (0.5, -8.0, 3.6), (-7.5, 4.5, 5.0), (7.0, 6.0, 4.4))):
        g.tubo("m_negro_liso", [(px, py, 15.0), (px, py, 15.0 - largo)], 0.07, lados=4, suave=False)
        g.cristal("m_cristal", 0.5, 1.5, (px, py, 15.0 - largo), (180, 0, i * 25), lados=5, punta=0.7, base=0.6)
    g.loft("m_tela", [[(-9.6, -6.6, 6.6), (-9.6, -6.4, 6.6), (-9.6, -6.4, 9.8), (-9.6, -6.6, 9.8)],
                      [(-8.0, -7.6, 6.0), (-8.0, -7.4, 6.0), (-8.0, -7.4, 9.4), (-8.0, -7.6, 9.4)],
                      [(-6.2, -7.2, 6.3), (-6.2, -7.0, 6.3), (-6.2, -7.0, 9.9), (-6.2, -7.2, 9.9)],
                      [(-4.6, -7.9, 6.1), (-4.6, -7.7, 6.1), (-4.6, -7.7, 10.2), (-4.6, -7.9, 10.2)]])
    for px in (-9.6, -4.6):
        g.tubo("m_hueso", [(px, -7.0 if px > -5 else -6.5, 0.4), (px, -7.8 if px > -5 else -6.5, 10.6)], [0.3, 0.16], lados=6)
    # Setas pequeñas y raíces alrededor.
    for i in range(5):
        a = rnd.uniform(0, 360)
        d = rnd.uniform(9.5, 11.0)
        seta(g, (d * math.cos(math.radians(a)), d * 0.85 * math.sin(math.radians(a)), 0.5), rnd.uniform(1.2, 2.6),
             rnd.uniform(0.7, 1.3), lados=7, semilla=10 + i, puntos=None, inclina=(rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3)))
    g.ancla("Mostrador", (0, -5.8, 3.7))


def forja_monstruo(g):
    rnd = random.Random(14)
    g.roca("m_roca", 12.0, (0, 0, 0), esc=(1.0, 0.85, 0.08), semilla=8, sub=2, amp=0.18)
    # Horno: una boca de roca con colmillos y lava púrpura dentro.
    hx, hy = -4.0, 4.5
    g.roca("m_roca_vetas", 5.2, (hx, hy, 3.4), esc=(1.0, 0.9, 1.15), semilla=3, sub=2, plano=-3.0)
    g.roca("m_roca", 3.0, (hx, hy + 0.5, 9.2), esc=(0.8, 0.8, 1.4), semilla=4, sub=2)
    boca = [(-2.2, 0.8), (2.2, 0.8)] + [(2.2 * math.cos(math.pi * i / 6), 2.6 + 2.0 * math.sin(math.pi * i / 6)) for i in range(7)]
    g.prisma("m_negro_liso", boca, 0.8, (hx, hy - 4.5, 0.2), plano="xz")
    g.prisma("m_lava", [(a * 0.84, 1.0 + (b - 0.8) * 0.86) for a, b in boca], 0.5, (hx, hy - 4.75, 0.2), plano="xz")
    for i in range(5):
        px = hx - 1.6 + i * 0.8
        colmillo(g, "m_hueso", (px, hy - 5.0, 4.5 - abs(i - 2) * 0.35), 1.3, 0.26, rot=(180, 0, 0), curvo=0.1)
    for i in range(4):
        px = hx - 1.3 + i * 0.85
        colmillo(g, "m_hueso", (px, hy - 5.0, 1.0), 0.9, 0.22, rot=(0, 0, 0), curvo=0.1)
    # Chimeneas de cristal y humo luminoso.
    cristales(g, "m_cristal_osc", (hx, hy + 0.5, 11.5), n=4, r=1.0, h=5.5, semilla=2, abrir=22)
    g.cristal("m_cristal", 0.5, 2.6, (hx + 0.2, hy + 0.4, 16.2), lados=5)
    # Río de lava púrpura: del horno a la poza de temple.
    g.loft("m_lava", [[(hx - 1.3, hy - 5.0, 0.42), (hx + 1.3, hy - 5.0, 0.42), (hx + 1.3, hy - 5.0, 0.62), (hx - 1.3, hy - 5.0, 0.62)],
                      [(hx - 0.2, -3.0, 0.42), (hx + 1.6, -3.0, 0.42), (hx + 1.6, -3.0, 0.62), (hx - 0.2, -3.0, 0.62)],
                      [(hx + 1.6, -5.4, 0.42), (hx + 3.0, -5.0, 0.42), (hx + 3.0, -5.0, 0.62), (hx + 1.6, -5.4, 0.62)],
                      [(hx + 4.6, -6.8, 0.42), (hx + 5.2, -5.8, 0.42), (hx + 5.2, -5.8, 0.62), (hx + 4.6, -6.8, 0.62)]],
           suave=False)
    px, py = 2.2, -6.4
    g.toro("m_roca", 2.2, 0.75, (px, py, 0.6), seg=9, lados=5, suave=False)
    g.cil("m_lava", 2.0, 0.5, (px, py, 0.45), lados=9)
    # Yunque de hueso: un cráneo enorme con cuernos sobre una vértebra.
    ax, ay = 4.2, 1.2
    g.cil("m_hueso", 1.5, 1.4, (ax, ay, 0.4), lados=7, r2=1.0, suave=False)
    for i in range(4):
        a = math.radians(90 * i + 45)
        g.tubo("m_hueso", [(ax + 1.0 * math.cos(a), ay + 1.0 * math.sin(a), 1.2), (ax + 2.2 * math.cos(a), ay + 2.2 * math.sin(a), 0.9),
                           (ax + 2.6 * math.cos(a), ay + 2.6 * math.sin(a), 0.3)], [0.45, 0.3, 0.0], lados=5)
    vs = g.caja("m_hueso", (4.2, 2.2, 1.5), (ax, ay, 1.8), base=True, sup=(1.0, 0.9), bisel=0.2)
    g.caja("m_hueso", (4.4, 2.4, 0.4), (ax, ay, 3.3), base=True, bisel=0.1)
    g.tubo("m_hueso", [(ax + 2.0, ay, 3.0), (ax + 3.6, ay, 3.3), (ax + 4.8, ay, 4.2)], [0.75, 0.5, 0.0], lados=6)
    g.tubo("m_hueso", [(ax - 2.0, ay, 3.0), (ax - 3.0, ay, 2.6), (ax - 3.6, ay, 1.8)], [0.6, 0.4, 0.0], lados=6)
    for s in (-1, 1):
        g.esfera("m_negro_liso", 0.38, (ax + s * 0.9, ay - 1.12, 2.7), esc=(1, 0.4, 1.2), lados=6, anillos=4)
        g.esfera("m_magenta", 0.16, (ax + s * 0.9, ay - 1.22, 2.7), lados=5, anillos=3)
    # Hoja de cristal al rojo (violeta) sobre el yunque y martillo de hueso.
    g.prisma("m_neon", [(-1.2, -0.25), (0.9, -0.3), (1.6, 0.0), (0.9, 0.3), (-1.2, 0.25)], 0.14, (ax - 0.2, ay, 3.78), plano="xy")
    g.tubo("m_negro_liso", [(ax - 1.6, ay - 0.9, 3.8), (ax + 0.2, ay - 0.6, 3.8)], 0.11, lados=5, suave=False)
    g.caja("m_roca", (0.7, 1.2, 0.7), (ax + 0.2, ay - 0.6, 3.9), rot=(0, 0, 12))
    # Armero de costillas con hojas de cristal.
    for s in (-1, 1):
        g.tubo("m_hueso", [(7.0 + s * 2.2, 6.0, 0.4), (7.0 + s * 2.5, 6.2, 4.0), (7.0 + s * 1.6, 5.8, 7.4)], [0.42, 0.32, 0.0], lados=6)
    for z in (2.2, 5.2):
        g.tubo("m_hueso", [(4.4, 6.0, z), (9.6, 6.0, z)], 0.2, lados=5, suave=False)
    for i in range(4):
        bx = 5.4 + i * 1.1
        g.prisma("m_cristal_osc" if i % 2 else "m_cristal", [(-0.22, 0), (0.22, 0), (0.3, 2.6), (0, 3.6), (-0.3, 2.6)], 0.12,
                 (bx, 5.7, 2.6), plano="xz", rot=(-6, 0, 0))
        g.caja("m_hueso", (0.9, 0.22, 0.2), (bx, 5.7, 2.55))
        g.cil("m_negro_liso", 0.1, 0.9, (bx, 5.7, 1.6), lados=5)
    # Arcos de costillas sobre la forja y cristales alrededor.
    for i, yy in enumerate((-2.0, 2.5)):
        for s in (-1, 1):
            pts = [(s * 10.2, yy, 0.3), (s * 10.8, yy, 5.5), (s * 8.6, yy, 10.2), (s * 5.2, yy + 0.5, 12.8)]
            g.tubo("m_hueso", pts, [0.8, 0.62, 0.42, 0.0], lados=6)
    cristales(g, "m_cristal", (9.0, -5.5, 0.5), n=4, r=0.7, h=3.6, semilla=5)
    cristales(g, "m_cristal", (-9.5, -4.0, 0.5), n=4, r=0.8, h=4.2, semilla=6)
    cristales(g, "m_cristal", (-9.0, 7.0, 0.5), n=3, r=0.6, h=3.0, semilla=7)
    # Trozos de mineral oscuro apilados.
    for i in range(5):
        g.roca("m_roca_vetas", 0.8, (-0.5 + (i % 3) * 1.1, 3.6 + (i // 3) * 0.9, 0.9 + (i // 3) * 0.7), semilla=30 + i, sub=1)
    g.ancla("Yunque", (ax, ay, 3.8))
    g.ancla("Fuego", (hx, hy - 4.8, 2.4))


MODELOS = [
    ("guarida_monstruo", "edificios_monstruos", 10000, guarida_monstruo),
    ("torre_cristal_oscuro", "edificios_monstruos", 10000, torre_cristal_oscuro),
    ("nido_monstruo", "edificios_monstruos", 5000, nido_monstruo),
    ("altar_monstruo", "edificios_monstruos", 5000, altar_monstruo),
    ("mercado_monstruo", "edificios_monstruos", 5000, mercado_monstruo),
    ("forja_monstruo", "edificios_monstruos", 5000, forja_monstruo),
]
