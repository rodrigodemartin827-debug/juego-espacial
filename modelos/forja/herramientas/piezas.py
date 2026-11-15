"""
Las seis piezas de la forja del planeta humano. Medidas en studs (un personaje R6 mide 5 de alto).
Ejes de Blender: X a la derecha, Z arriba, y el frente de cada pieza mira a -Y.
Cada función devuelve (Pieza, cfg). cfg: datos para los materiales (focos de hollín, quemaduras...) y notas.
"""

import math
import random

from mathutils import Matrix, Vector

from malla import Pieza, circulo, rect_redondo, rot, tras

TAU = math.tau


def _anillo_banda(p, r_de_z, z0, z1, n, mat, grosor=0.04, fase=0.0, radios=None):
    """Aro de hierro alrededor de un cuerpo de revolución: labio de abajo, cara exterior y labio de arriba."""
    vs, cs = [], []
    for i in range(n):
        a = fase + TAU * i / n
        k = radios[i] if radios else 1.0
        for r, z in ((r_de_z(z0) * k - 0.02, z0), (r_de_z(z0) * k + grosor, z0), (r_de_z(z1) * k + grosor, z1),
                     (r_de_z(z1) * k - 0.02, z1)):
            vs.append((math.cos(a) * r, math.sin(a) * r, z))
    for i in range(n):
        j = (i + 1) % n
        for s in range(3):
            cs.append((i * 4 + s, j * 4 + s, j * 4 + s + 1, i * 4 + s + 1))
    # el orden anterior da: labio de abajo hacia abajo, exterior hacia fuera, labio de arriba hacia arriba
    p.libre(vs, cs, mat, tex=None, recalcular=False)


# ==================================================================================================================
# Barril de temple
# ==================================================================================================================


def barril():
    p = Pieza("forja_barril", 4)
    rnd = p.rnd
    N, H = 16, 3.1

    def r(z):
        return 1.1 + 0.27 * math.sin(math.pi * (z + 0.15) / (H + 0.3))

    niveles = [0.0, 0.55, 1.2, 1.9, 2.6, H]
    z_agua = 2.66
    for i in range(N):
        a0, a1 = TAU * i / N, TAU * (i + 1) / N
        dr = rnd.uniform(-0.018, 0.028)
        dh = rnd.uniform(-0.03, 0.025)
        vs, cs = [], []
        zs = niveles[:-1] + [H + dh]
        for z in zs:
            rr = r(min(z, H)) + dr
            vs.append((math.cos(a0) * rr, math.sin(a0) * rr, z))
            vs.append((math.cos(a1) * rr, math.sin(a1) * rr, z))
        k = len(zs)
        for j in range(k - 1):
            cs.append((2 * j, 2 * j + 1, 2 * j + 3, 2 * j + 2))
        # canto de arriba y cara interior hasta debajo del agua
        ri = r(H) + dr - 0.13
        ri2 = r(z_agua - 0.2) - 0.1
        b = len(vs)
        vs += [(math.cos(a0) * ri, math.sin(a0) * ri, H + dh), (math.cos(a1) * ri, math.sin(a1) * ri, H + dh),
               (math.cos(a0) * ri2, math.sin(a0) * ri2, z_agua - 0.2),
               (math.cos(a1) * ri2, math.sin(a1) * ri2, z_agua - 0.2)]
        cs.append((2 * k - 2, 2 * k - 1, b + 1, b))
        cs.append((b, b + 1, b + 3, b + 2))
        # cantos laterales de la duela (se ven en las juntas, porque cada duela sobresale distinto)
        c0 = len(vs)
        for z in zs:
            rr = r(min(z, H)) + dr - 0.07
            vs.append((math.cos(a0) * rr, math.sin(a0) * rr, z))
            vs.append((math.cos(a1) * rr, math.sin(a1) * rr, z))
        for j in range(k - 1):
            cs.append((2 * j + 1, c0 + 2 * j + 1, c0 + 2 * j + 3, 2 * j + 3))
            cs.append((2 * j, 2 * j + 2, c0 + 2 * j + 2, c0 + 2 * j))
        p.libre(vs, cs, "madera", tex=("veta", "Z"), recalcular=False)
    # Fondo
    p.libre([(x, y, 0.0) for x, y in circulo(N, r(0) + 0.01)], [tuple(reversed(range(N)))], "madera",
            tex=("veta", "X"), recalcular=False)
    # Aros
    for z0, alto in ((0.22, 0.24), (0.95, 0.2), (2.0, 0.2), (2.68, 0.24)):
        _anillo_banda(p, r, z0, z0 + alto, N, "hierro", grosor=0.05)
        a = rnd.uniform(0, TAU)
        for da in (-0.09, 0.09):
            zc = z0 + alto / 2
            n = Vector((math.cos(a + da), math.sin(a + da), 0))
            p.remache(n * (r(zc) + 0.05) + Vector((0, 0, zc)), n, 0.05, "hierro")
    # Agua
    ra = r(z_agua) - 0.1
    vs = [(0, 0, z_agua)] + [(x, y, z_agua) for x, y in circulo(N, ra)]
    p.libre(vs, [(0, 1 + i, 1 + (i + 1) % N) for i in range(N)], "agua", tex=None, recalcular=False)
    # Asas: argolla que cuelga de una grapa, a los dos lados
    for lado in (1, -1):
        with p.grupo(rot("Z", 90 if lado > 0 else -90) @ tras(0, -(r(2.25) + 0.1), 2.25)):
            p.caja((-0.07, -0.02, -0.06), (0.07, 0.07, 0.1), "hierro", bisel=0.015)
            aro = [(math.cos(t) * 0.2, -0.04 - 0.02 * math.sin(t), -0.2 + math.sin(t) * 0.2)
                   for t in [TAU * k / 8 for k in range(9)]]
            p.tubo(aro, 0.03, "hierro", n=4)
    # Una hoja a medio forjar metida en el agua, apoyada en el borde
    with p.grupo(tras(0.35, -0.25, 1.75) @ rot("Z", 35) @ rot("Y", 20)):
        p.prisma([(-0.13, 0.0), (0.13, 0.0), (0.11, 1.9), (0.045, 2.0), (0.045, 2.5), (-0.045, 2.5), (-0.045, 2.0),
                  (-0.11, 1.9)], -0.03, 0.03, "hierro_herr", eje="Y", tex=("veta", "Z"))
    cfg = {"hollin_base": 0.3,
           "nota": "Barril de temple. Vapor: ParticleEmitter sobre el agua (Attachment «Vapor»)."}
    cfg["anclajes"] = {"Vapor": (0, 0, z_agua + 0.1)}
    return p, cfg




# ==================================================================================================================
# Herramientas sueltas (se usan en varias piezas)
# ==================================================================================================================


def _martillo(p, largo=2.4, k=1.0, mango="madera_mango"):
    """Martillo de forja: la cabeza en el origen con su eje en Y; el mango sale hacia -X."""
    an = []
    for y, lx, lz in ((-0.45, 0.3, 0.3), (-0.4, 0.38, 0.38), (-0.12, 0.36, 0.36), (0.12, 0.36, 0.36),
                      (0.3, 0.28, 0.36), (0.5, 0.07, 0.36)):
        an.append([(x * k, y * k, z * k) for x, z in rect_redondo(lx, lz, 0.06, 2)])
    p.loft(an, "hierro_herr", tex=None)
    p.tubo([(-largo, 0, 0), (-largo * 0.66, 0, 0), (-largo * 0.33, 0, 0), (0.23 * k, 0, 0)],
           [0.085 * k, 0.074 * k, 0.068 * k, 0.078 * k], mango, n=8, achatado=1.25)


def _tenazas(p, largo=3.6, boca=0.5, k=1.0, abre=0.1):
    """Tenazas tumbadas en el plano XY: el eje (remache) en el origen, las bocas hacia -X y los mangos hacia +X."""
    for s in (1, -1):
        pts = [(-boca, s * abre * 0.6, 0.02 * s), (-boca * 0.55, s * abre * 1.2, 0.02 * s),
               (-0.08, s * 0.05, 0.02 * s), (0.12, -s * 0.05, 0.02 * s),
               (largo * 0.45, -s * (0.1 + abre * 0.5), 0.02 * s), (largo, -s * (0.16 + abre), 0.02 * s)]
        p.tubo(pts, [0.05 * k, 0.055 * k, 0.065 * k, 0.06 * k, 0.045 * k, 0.04 * k], "hierro_herr", n=4,
               fase=math.pi / 4)
    p.cilindro((0, 0, -0.08 * k), (0, 0, 0.08 * k), 0.05 * k, "hierro_herr", n=6)


def _lingote(p, centro, mat, giro=0.0, k=1.0, rnd=None):
    j = rnd.uniform(-4, 4) if rnd else 0
    p.caja((-0.34 * k, -0.15 * k, 0), (0.34 * k, 0.15 * k, 0.17 * k), mat, tex=None, cono=(0.8, 0.6), bisel=0.02,
           matriz=tras(*centro) @ rot("Z", giro + j))


# ==================================================================================================================
# Yunque
# ==================================================================================================================


def yunque():
    p = Pieza("forja_yunque", 7)
    rnd = p.rnd
    N = 28
    radios = [1 + 0.05 * math.sin(3 * TAU * i / N + 1) + 0.035 * math.sin(5 * TAU * i / N) + rnd.uniform(-0.015, 0.015)
              for i in range(N)]
    perfil = [(1.41, 0.0), (1.38, 0.14), (1.35, 0.5), (1.33, 1.0), (1.33, 1.43), (1.27, 1.5)]

    def r_tocon(z):
        for (r0, z0), (r1, z1) in zip(perfil, perfil[1:]):
            if z0 <= z <= z1:
                return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
        return perfil[-1][0]

    # Tocón: tronco grueso sin corteza, con los anillos centrados en la cara de arriba
    p.torno(perfil, "madera", n=N, radios=radios, tex=("veta", "Z", (0, 0, 0)))
    for z0, z1 in ((1.08, 1.28),):
        _anillo_banda(p, r_tocon, z0, z1, N, "hierro", grosor=0.045, radios=radios)
        for k in range(5):
            a = TAU * (k + rnd.uniform(-0.15, 0.15)) / 5
            i = int(round(a / TAU * N)) % N
            a = TAU * i / N
            n = Vector((math.cos(a), math.sin(a), 0))
            p.remache(n * (r_tocon((z0 + z1) / 2) * radios[i] + 0.045) + Vector((0, 0, (z0 + z1) / 2)), n, 0.055,
                      "hierro")

    # Cuerpo del yunque: pies, cintura y arranque de la mesa
    an = []
    for lx, ly, z in ((2.1, 1.2, 1.5), (2.1, 1.2, 1.6), (1.82, 1.02, 1.72), (1.15, 0.62, 1.93), (1.0, 0.56, 2.1),
                      (1.06, 0.6, 2.22), (1.5, 0.76, 2.34)):
        an.append([(x, y, z) for x, y in rect_redondo(lx, ly, min(lx, ly) * 0.22, 5)])
    p.loft(an, "hierro", tex=None)
    # Mesa, talón y escalón: perfil lateral extruido a lo ancho
    p.prisma([(-1.6, 2.78), (0.85, 2.78), (0.85, 2.68), (1.06, 2.68), (1.06, 2.42), (0.75, 2.32), (-0.75, 2.32),
              (-1.0, 2.45), (-1.6, 2.6)], -0.41, 0.41, "hierro", eje="Y", tex=None, bisel=0.022)
    # Cuerno
    an = []
    for x, r in ((1.02, 0.37), (1.2, 0.34), (1.4, 0.3), (1.6, 0.25), (1.8, 0.2), (2.0, 0.14), (2.18, 0.08),
                 (2.32, 0.02)):
        cz = 2.68 - r + (x - 1.02) * 0.03
        an.append([(x, math.cos(t) * r * 1.04, cz + math.sin(t) * r) for t in [TAU * k / 14 for k in range(14)]])
    p.loft(an, "hierro", tex=None)
    # Grapas que sujetan los pies al tocón
    for sx in (1, -1):
        for sy in (0.33, -0.33):
            p.tubo([(sx * 1.2, sy, 1.42), (sx * 1.2, sy, 1.68), (sx * 0.93, sy, 1.68), (sx * 0.93, sy, 1.62)], 0.055,
                   "hierro", n=4, fase=math.pi / 4)
    # Martillo grande apoyado en la mesa, con el mango saliendo hacia el talón
    with p.grupo(tras(0.12, 0.0, 2.78 + 0.185) @ rot("Z", 24) @ rot("Y", -4.0)):
        _martillo(p, 2.5)
    # Martillo pequeño colgado de una tira de cuero clavada al tocón
    R = r_tocon(1.1) * radios[int(N * 0.75)]
    p.tubo([(-0.24, -R + 0.03, 1.02), (-0.26, -R - 0.3, 1.02), (0.26, -R - 0.3, 1.02), (0.24, -R + 0.03, 1.02)],
           0.028, "cuero", n=4, achatado=4.0, fase=math.pi / 4)
    for sx in (-0.24, 0.24):
        p.remache((sx, -R - 0.02, 1.02), (0, -1, 0), 0.04, "hierro")
    with p.grupo(tras(0.0, -R - 0.16, 1.27) @ rot("Z", 90) @ rot("Y", -90)):
        _martillo(p, 1.15, k=0.62)
    # Punzón olvidado encima del tocón
    p.tubo([(0.35, 1.02, 1.56), (0.7, 0.93, 1.56), (1.0, 0.85, 1.555)], [0.06, 0.05, 0.02], "hierro_herr", n=6)
    cfg = {"hollin_base": 0.35, "pulido": 2.775,
           "huecos": [((-1.28, 0.0, 2.78), (0.1, 0.1, 1.0)), ((-1.0, 0.2, 2.78), (0.05, 0.05, 1.0))],
           "anclajes": {"Golpe": (0.1, 0.0, 2.8)},
           "nota": "Yunque sobre tocón, con dos martillos. Chispas del golpe: Attachment «Golpe» (centro de la mesa)."}
    return p, cfg


# ==================================================================================================================
# Mesa de trabajo
# ==================================================================================================================


def mesa():
    p = Pieza("forja_mesa", 11)
    rnd = p.rnd
    ALTO = 2.95
    # Patas
    for sx in (-2.78, 2.78):
        for sy in (-1.0, 1.0):
            p.tabla((sx - 0.21, sy - 0.21, 0), (sx + 0.21, sy + 0.21, ALTO - 0.28), "madera_osc", eje="Z", bisel=0.03,
                    quitar="z+")
    # Tablero: cuatro tablones gruesos, desiguales en las puntas
    y = -1.36
    for i, ancho in enumerate((0.66, 0.7, 0.64, 0.7)):
        p.tabla((-3.2 + rnd.uniform(-0.08, 0.06), y, ALTO - 0.28 + rnd.uniform(-0.012, 0.012)),
                (3.2 + rnd.uniform(-0.06, 0.1), y + ancho - 0.018, ALTO + rnd.uniform(-0.012, 0.012)), "madera",
                eje="X", bisel=0.028, ruido=0.012)
        y += ancho
    # Faldones (el de delante solo en la mitad derecha: en la izquierda van los cajones)
    p.tabla((-0.1, -1.17, 2.25), (2.57, -1.03, 2.67), "madera_osc", eje="X")
    p.tabla((-2.57, 1.03, 2.25), (2.57, 1.17, 2.67), "madera_osc", eje="X")
    for sx in (-2.93, 2.79):
        p.tabla((sx, -0.79, 2.25), (sx + 0.14, 0.79, 2.67), "madera_osc", eje="Y")
    # Cajones: uno cerrado y otro a medio abrir
    for x0, saca in ((-2.55, 0.0), (-1.32, 0.34)):
        yf = -1.2 - saca
        p.tabla((x0, yf, 2.22), (x0 + 1.17, yf + 0.1, 2.65), "madera", eje="X", bisel=0.02)
        if saca:
            for xl in (x0 + 0.03, x0 + 1.06):
                p.tabla((xl, yf + 0.1, 2.26), (xl + 0.08, yf + 0.1 + saca + 0.2, 2.6), "madera_osc", eje="Y")
            p.tabla((x0 + 0.03, yf + 0.1, 2.26), (x0 + 1.14, yf + 0.1 + saca + 0.2, 2.32), "madera_osc", eje="X")
            for k in range(3):   # clavos y remaches dentro del cajón
                p.tubo([(x0 + 0.3 + 0.2 * k, yf + 0.16, 2.36), (x0 + 0.42 + 0.2 * k, yf + 0.36, 2.35)], 0.022,
                       "hierro_herr", n=4)
        # tirador: argolla
        xc = x0 + 0.585
        p.remache((xc, yf, 2.5), (0, -1, 0), 0.05, "hierro")
        p.tubo([(xc + math.cos(t) * 0.11, yf - 0.035, 2.4 + math.sin(t) * 0.11) for t in
                [TAU * k / 8 for k in range(9)]], 0.022, "hierro", n=4)
    # Balda de abajo con sus travesaños
    for sx in (-2.78, 2.78):
        p.tabla((sx - 0.1, -0.79, 0.5), (sx + 0.1, 0.79, 0.72), "madera_osc", eje="Y")
    y = -1.18
    for ancho in (0.8, 0.76, 0.8):
        p.tabla((-2.99 + rnd.uniform(-0.05, 0.05), y, 0.72), (2.99 + rnd.uniform(-0.05, 0.05), y + ancho - 0.02, 0.84),
                "madera", eje="X", ruido=0.012)
        y += ancho
    # --- Materiales en la balda ---
    zb = 0.84
    # Cajón de carbón
    cx, cy = -1.9, 0.0
    for (a, b) in (((cx - 0.7, cy - 0.55, zb), (cx + 0.7, cy - 0.47, zb + 0.62)),
                   ((cx - 0.7, cy + 0.47, zb), (cx + 0.7, cy + 0.55, zb + 0.62)),
                   ((cx - 0.7, cy - 0.47, zb), (cx - 0.62, cy + 0.47, zb + 0.62)),
                   ((cx + 0.62, cy - 0.47, zb), (cx + 0.7, cy + 0.47, zb + 0.62))):
        p.tabla(a, b, "madera_osc", bisel=0.015)
    vs, cs = [], []
    for j in range(5):
        for i in range(6):
            x, yy = cx - 0.62 + 1.24 * i / 5, cy - 0.47 + 0.94 * j / 4
            borde = min(i, 5 - i, j, 4 - j)
            vs.append((x, yy, zb + 0.4 + 0.13 * borde + rnd.uniform(-0.05, 0.07) * (borde > 0)))
    for j in range(4):
        for i in range(5):
            cs.append((j * 6 + i, j * 6 + i + 1, (j + 1) * 6 + i + 1, (j + 1) * 6 + i))
    p.libre(vs, cs, "carbon", tex=None, recalcular=False)
    # Barras de hierro en bruto
    for k in range(6):
        yy = -0.28 + 0.15 * (k % 3) + rnd.uniform(-0.02, 0.02)
        zz = zb + 0.07 + 0.13 * (k // 3)
        x0 = -0.75 + rnd.uniform(-0.15, 0.15)
        p.viga((x0, yy, zz), (x0 + 2.3 + rnd.uniform(-0.3, 0.2), yy + rnd.uniform(-0.05, 0.05), zz), 0.12, 0.12,
               "hierro_herr", ruido=0.004)
    # Lingotes de cobre en la balda
    for k, (dx, dy, dz) in enumerate(((0, 0, 0), (0.0, 0.34, 0), (0.0, 0.17, 0.17), (0.75, 0.1, 0))):
        _lingote(p, (2.0 + dx - 0.4, -0.2 + dy, zb + dz), "cobre", giro=0, rnd=rnd)
    # --- Encima de la mesa ---
    zt = ALTO + 0.012
    # Lingotes apilados (3-2-1)
    for dx, dy, dz in ((-0.72, 0, 0), (0, 0, 0), (0.72, 0, 0), (-0.36, 0, 0.17), (0.36, 0, 0.17), (0, 0, 0.34),
                       (-0.6, -0.5, 0), (0.25, -0.46, 0)):
        _lingote(p, (2.0 + dx, 0.75 + dy, zt + dz), "lingote", giro=90 if dy == 0 else 20, rnd=rnd)
    # Molde de lingotes: bloque de hierro con tres huecos, uno todavía lleno
    mx, my = 0.15, 0.72
    p.caja((mx - 0.75, my - 0.45, zt), (mx + 0.75, my + 0.45, zt + 0.1), "hierro", tex=None, quitar="z-")
    for xb in (-0.75, -0.29, 0.21, 0.67):
        p.caja((mx + xb, my - 0.45, zt + 0.1), (mx + xb + 0.08, my + 0.45, zt + 0.27), "hierro", tex=None,
               bisel=0.015, quitar="z-")
    for yb in (-0.45, 0.37):
        p.caja((mx - 0.75, my + yb, zt + 0.1), (mx + 0.75, my + yb + 0.08, zt + 0.27), "hierro", tex=None,
               bisel=0.015, quitar="z-")
    p.caja((mx - 0.67, my - 0.37, zt + 0.1), (mx - 0.29, my + 0.37, zt + 0.22), "cobre", tex=None, quitar="z-")
    for s in (-1, 1):   # asas del molde
        p.tubo([(mx + s * 0.75, my - 0.15, zt + 0.17), (mx + s * 0.95, my - 0.15, zt + 0.17),
                (mx + s * 0.95, my + 0.15, zt + 0.17), (mx + s * 0.75, my + 0.15, zt + 0.17)], 0.03, "hierro", n=4)
    # Tenazas, lima, martillo, cincel y herraduras
    with p.grupo(tras(-1.9, 0.55, zt + 0.06) @ rot("Z", 14)):
        _tenazas(p, largo=1.7, boca=0.36, k=0.75, abre=0.05)
    with p.grupo(tras(-1.6, -0.35, zt) @ rot("Z", -12)):
        p.caja((-0.75, -0.06, 0), (0.25, 0.06, 0.035), "acero", tex=("veta", "X"))
        p.tubo([(0.25, 0, 0.018), (0.45, 0, 0.03)], [0.03, 0.02], "acero", n=4)
        p.tubo([(0.4, 0, 0.06), (0.62, 0, 0.065), (0.84, 0, 0.065)], [0.05, 0.075, 0.06], "madera_mango", n=7)
    with p.grupo(tras(-0.25, -0.75, zt + 0.118) @ rot("Z", 200) @ rot("X", 90)):
        _martillo(p, 1.25, k=0.62)
    p.tubo([(0.7, -0.2, zt + 0.05), (1.0, -0.32, zt + 0.05), (1.3, -0.44, zt + 0.04)], [0.03, 0.055, 0.05],
           "hierro_herr", n=6)
    for k, (hx_, hy, g) in enumerate(((1.1, -0.95, 20), (1.22, -0.88, 65))):
        with p.grupo(tras(hx_, hy, zt + 0.03 + 0.05 * k) @ rot("Z", g) @ rot("X", 6 * k)):
            p.tubo([(math.cos(t) * 0.2, math.sin(t) * 0.24, 0) for t in
                    [math.radians(a) for a in (-50, -10, 30, 70, 110, 150, 190, 230)]], 0.035, "hierro_herr", n=4,
                   achatado=0.6, fase=math.pi / 4)
    # Tornillo de banco en la esquina derecha
    vx = 2.3
    p.caja((vx - 0.3, -1.42, ALTO - 0.3), (vx + 0.3, -1.3, ALTO + 0.42), "hierro", tex=None, bisel=0.025)
    p.caja((vx - 0.3, -1.62, ALTO - 0.3), (vx + 0.3, -1.5, ALTO + 0.42), "hierro", tex=None, bisel=0.025)
    p.caja((vx - 0.07, -1.61, 1.0), (vx + 0.07, -1.51, ALTO - 0.3), "hierro", tex=None)
    p.caja((vx - 0.1, -1.5, 1.0), (vx + 0.1, -1.2, 1.12), "hierro", tex=None)
    p.cilindro((vx, -1.95, ALTO - 0.02), (vx, -1.25, ALTO - 0.02), 0.075, "hierro", n=8)
    p.cilindro((vx, -2.0, ALTO - 0.02), (vx, -1.9, ALTO - 0.02), 0.11, "hierro", n=8)
    p.tubo([(vx + 0.05, -1.95, ALTO - 0.45), (vx + 0.02, -1.95, ALTO - 0.02), (vx - 0.02, -1.95, ALTO + 0.3)], 0.032,
           "hierro_herr", n=5)
    for zz in (ALTO - 0.47, ALTO + 0.32):
        p.cilindro((vx + 0.03, -1.95, zz - 0.04), (vx + 0.03, -1.95, zz + 0.04), 0.055, "hierro_herr", n=6)
    cfg = {"hollin_base": 0.3, "hollin": [((0.15, 0.72, ALTO), (1.5, 1.0, 0.5), 0.85),
                                          ((-0.3, -0.7, ALTO), (0.8, 0.6, 0.4), 0.6)],
           "nota": "Mesa de trabajo con tenazas, lima, molde, lingotes, tornillo de banco, cajones y balda con "
                   "carbón, barras y lingotes de cobre."}
    return p, cfg


# ==================================================================================================================
# Estantería de armas terminadas
# ==================================================================================================================


def _espada(p, largo, ancho, guarda=0.9, puno=0.62, pomo="laton", curva=False):
    """Espada colgada: guarda en z = 0, hoja hacia abajo, caras planas mirando a ±Y."""
    g = 0.04
    if curva:   # alfanje: un solo filo y la punta ancha
        pts = [(-ancho * 0.45, 0), (ancho * 0.45, 0), (ancho * 0.5, -largo * 0.5), (ancho * 0.72, -largo * 0.8),
               (ancho * 0.55, -largo * 0.95), (ancho * 0.1, -largo), (-ancho * 0.3, -largo * 0.86),
               (-ancho * 0.52, -largo * 0.5)]
        p.prisma(pts, -g, g, "acero", eje="Y", tex=("veta", "Z"), bisel=0.028)
    else:
        an = []
        for z, k in ((0.0, 1.0), (-largo * 0.55, 0.9), (-largo * 0.86, 0.72), (-largo * 0.96, 0.4), (-largo, 0.03)):
            w = ancho * k / 2
            an.append([(w, 0, z), (w * 0.22, g, z), (-w * 0.22, g, z), (-w, 0, z), (-w * 0.22, -g, z),
                       (w * 0.22, -g, z)])
        p.loft(an, "acero", tex=("veta", "Z"))
    p.caja((-guarda / 2, -0.075, 0.0), (guarda / 2, 0.075, 0.13), pomo if pomo == "laton" else "hierro_herr",
           tex=None, bisel=0.03)
    p.tubo([(0, 0, 0.13), (0, 0, 0.13 + puno * 0.5), (0, 0, 0.13 + puno)], [0.065, 0.07, 0.055], "cuero", n=6,
           achatado=0.75)
    z = 0.13 + puno
    p.torno([(0.04, 0.0), (0.11, 0.04), (0.125, 0.11), (0.08, 0.2), (0.02, 0.23)], pomo, n=8, centro=(0, 0, z),
            tex=None)


def estanteria():
    p = Pieza("forja_estanteria", 19)
    rnd = p.rnd
    XP, ALTO = 4.1, 7.3
    # Postes, con patín y tornapuntas
    for sx in (-XP, XP):
        p.tabla((sx - 0.19, -0.19, 0), (sx + 0.19, 0.19, ALTO), "madera_osc", eje="Z", bisel=0.03)
        p.tabla((sx - 0.24, -1.35, 0), (sx + 0.24, 1.35, 0.3), "madera_osc", eje="Y", bisel=0.03)
        for sy in (-1, 1):
            p.viga((sx, sy * 1.15, 0.28), (sx, sy * 0.12, 1.75), 0.2, 0.16, "madera_osc")
    # Travesaños (por delante de los postes) y remate de arriba
    for z0, z1 in ((6.75, 7.1), (5.85, 6.15), (3.45, 3.75), (1.2, 1.5)):
        p.tabla((-XP - 0.35 + rnd.uniform(-0.06, 0.06), -0.34, z0), (XP + 0.35 + rnd.uniform(-0.06, 0.06), -0.19, z1),
                "madera", eje="X", bisel=0.025)
        for sx in (-XP, XP):
            for dz in (0.08, z1 - z0 - 0.08):
                p.remache((sx + rnd.uniform(-0.05, 0.05), -0.34, z0 + dz), (0, -1, 0), 0.045, "hierro")
    p.tabla((-XP - 0.5, -0.5, ALTO), (XP + 0.5, 0.3, ALTO + 0.14), "madera", eje="X", bisel=0.03)
    for sx in (-1, 1):   # escuadras bajo el remate
        p.viga((sx * (XP - 0.2), 0.0, 6.0), (sx * (XP - 1.15), 0.0, 6.72), 0.16, 0.14, "madera_osc")
    # Balda baja
    for y0, y1 in ((-0.95, -0.36), (-0.34, 0.25)):
        p.tabla((-XP + 0.2 + rnd.uniform(-0.04, 0.04), y0, 1.5), (XP - 0.2 + rnd.uniform(-0.04, 0.04), y1, 1.62),
                "madera", eje="X", ruido=0.012)
    for sx in (-XP + 0.4, 0.0, XP - 0.4):
        p.tabla((sx - 0.08, -0.95, 1.32), (sx + 0.08, -0.19, 1.5), "madera_osc", eje="Y")
    # --- Espadas, colgadas de dos clavijas por la guarda ---
    zg = 6.0 + 0.045
    for x, largo, ancho, guarda, puno, pomo, curva in ((-3.25, 3.5, 0.3, 1.0, 0.75, "laton", False),
                                                       (-2.2, 2.7, 0.4, 0.8, 0.5, "hierro_herr", False),
                                                       (-1.2, 2.9, 0.42, 0.7, 0.55, "laton", True)):
        for s in (-1, 1):
            d = ancho * 0.5 + 0.09
            p.cilindro((x + s * d, -0.3, 6.0), (x + s * d, -0.68, 6.03), 0.04, "madera_osc", n=6)
        with p.grupo(tras(x, -0.5, zg) @ rot("Y", rnd.uniform(-1.5, 1.5))):
            _espada(p, largo, ancho, guarda, puno, pomo, curva)
    # --- Escudo redondo ---
    ex, ez = 0.55, 4.55
    with p.grupo(tras(ex, -0.37, ez) @ rot("Y", 8) @ rot("X", 90)):
        p.torno([(0.02, 0.0), (1.2, 0.0), (1.22, 0.05), (1.2, 0.1), (0.9, 0.17), (0.5, 0.22), (0.36, 0.235)],
                "escudo_rojo", n=20, tex=("veta", "Y", (0, 0, 0)))
        p.torno([(1.12, -0.018), (1.25, -0.012), (1.275, 0.05), (1.25, 0.115), (1.12, 0.125)], "hierro", n=20,
                tex=None, tapas=(False, False))
        p.torno([(0.52, 0.2), (0.52, 0.255), (0.4, 0.27), (0.37, 0.34), (0.27, 0.44), (0.12, 0.5), (0.015, 0.515)],
                "hierro", n=10, tex=None)
        for k in range(10):
            a = TAU * (k + 0.5) / 10
            p.remache((math.cos(a) * 1.19, math.sin(a) * 1.19, 0.12), (0, 0, 1), 0.045, "hierro")
        for k in range(4):
            a = TAU * (k + 0.5) / 4
            p.remache((math.cos(a) * 0.46, math.sin(a) * 0.46, 0.255), (0, 0, 1), 0.04, "hierro")
    # --- Escudo de lágrima, curvado ---
    hx_, hz = 2.9, 4.75
    with p.grupo(tras(hx_, -0.36, hz) @ rot("Y", -5) @ rot("X", 90)):
        A, cols = 0.9, 9
        an, borde_f = [], []
        for i in range(cols):
            x = -A + 2 * A * i / (cols - 1)
            u = abs(x) / A
            y_ab = -1.45 + 1.95 * u ** 2.3
            y_ar = 1.05 - 0.08 * u ** 2
            zc = -0.3 * x * x
            an.append([(x, y_ab, zc + 0.2), (x, y_ar, zc + 0.2), (x, y_ar, zc + 0.1), (x, y_ab, zc + 0.1)])
            borde_f.append(((x, y_ab, zc + 0.21), (x, y_ar, zc + 0.21)))
        p.loft(an, "escudo_azul", tex=("veta", "Y", (0, 0, 0)))
        contorno = [b[0] for b in borde_f] + [b[1] for b in reversed(borde_f)] + [borde_f[0][0]]
        p.tubo(contorno, 0.04, "hierro", n=4, fase=math.pi / 4)
        for x, y in ((-0.55, 0.7), (0.55, 0.7), (-0.5, -0.1), (0.5, -0.1), (0.0, -1.0), (0.0, 0.75)):
            p.remache((x, y, -0.3 * x * x + 0.2), (0, 0, 1), 0.045, "hierro")
    # Ganchos de hierro y correas de las que cuelgan los escudos
    for x, zt_ in ((ex, ez + 1.05), (hx_, hz + 0.95)):
        for s in (-0.22, 0.22):
            p.tubo([(x + s, -0.33, 6.95), (x + s, -0.5, 6.95), (x + s, -0.56, 6.86), (x + s, -0.5, 6.78)], 0.03,
                   "hierro", n=5)
            p.tubo([(x + s, -0.5, 6.84), (x + s * 1.6, -0.47, (6.84 + zt_) / 2), (x + s * 2.2, -0.42, zt_)], 0.022,
                   "cuero", n=4, achatado=3.0, fase=math.pi / 4)
    # --- En la balda: yelmo y hacha de mano ---
    with p.grupo(tras(-2.6, -0.35, 1.62)):
        p.torno([(0.5, 0.0), (0.52, 0.06), (0.5, 0.3), (0.42, 0.55), (0.27, 0.74), (0.1, 0.83), (0.015, 0.85)],
                "hierro", n=12, tex=None)
        p.torno([(0.54, 0.02), (0.56, 0.08), (0.53, 0.14)], "laton", n=12, tex=None, tapas=(False, False))
        p.caja((-0.06, -0.57, -0.02 + 0.05), (0.06, -0.5, 0.5), "laton", tex=None, bisel=0.015)
        p.tubo([(0, -0.5, 0.5), (0, -0.33, 0.73), (0, -0.1, 0.85), (0, 0.2, 0.82), (0, 0.42, 0.6)], 0.035, "laton",
               n=4, fase=math.pi / 4)
    with p.grupo(tras(0.9, -0.42, 1.62 + 0.06) @ rot("Z", 8)):
        p.tubo([(-0.2, 0, 0.02), (0.8, 0, 0.0), (1.9, 0, 0.0)], [0.065, 0.055, 0.06], "madera_mango", n=7,
               achatado=1.3)
        p.prisma([(-0.02, -0.1), (0.3, -0.08), (0.3, 0.1), (-0.02, 0.1), (-0.12, 0.6), (-0.3, 0.75), (-0.2, 0.3),
                  (-0.28, -0.25)], -0.05, 0.05, "acero", eje="Z", tex=("veta", "Y"), bisel=0.03,
                 matriz=rot("X", 0) @ tras(0, 0, 0.0))
    cfg = {"hollin_base": 0.3,
           "nota": "Estantería con 3 espadas, 2 escudos, un yelmo y un hacha de mano. Todo es una sola malla "
                   "decorativa (las armas no se pueden descolgar)."}
    return p, cfg


# ==================================================================================================================
# Suelo de la forja
# ==================================================================================================================

# Dónde va cada pieza sobre el suelo: (x, y, giro en grados sobre el eje vertical). El suelo mide ~27 × 20.
ALTO_SUELO = 0.62
MONTAJE = {
    "suelo": (0.0, 0.0, 0.0),
    "horno": (-2.6, 4.2, 0.0),
    "yunque": (-1.9, -4.1, 20.0),
    "barril": (2.6, -3.2, 0.0),
    "mesa": (9.6, -1.6, -90.0),
    "estanteria": (-11.2, -2.2, 90.0),
}


def suelo():
    p = Pieza("forja_suelo", 23)
    rnd = p.rnd
    N = 60
    A, B = 13.6, 9.9
    # Contorno: rectángulo redondeado con mordiscos del tamaño de un adoquín (el borde no es una línea recta)
    base, mord = [], []
    k = 0
    while k < N:
        paso = rnd.choice((1, 1, 2, 2, 3))
        d = rnd.uniform(-0.6, 0.3)
        for _ in range(paso):
            if k < N:
                mord.append(d)
                k += 1
    for i in range(N):
        a = TAU * i / N
        c, s_ = math.cos(a), math.sin(a)
        e = 2 / 5.0
        base.append(Vector((math.copysign(abs(c) ** e, c) * A, math.copysign(abs(s_) ** e, s_) * B, 0)))
    H = ALTO_SUELO
    vs, cs = [], []

    def anillo(escala, z, mordisco, ruido_z=0.0):
        ini = len(vs)
        for i in range(N):
            b = base[i]
            q = b * escala + b.normalized() * mord[i] * mordisco
            vs.append((q.x, q.y, z + rnd.uniform(-ruido_z, ruido_z)))
        return ini

    r0 = anillo(1.0, 0.0, 1.0)
    r1 = anillo(1.0, H - 0.12, 1.0)
    r2 = anillo(0.985, H, 1.0)
    r3 = anillo(0.8, H, 0.4, 0.035)
    r4 = anillo(0.56, H, 0.0, 0.035)
    r5 = anillo(0.3, H, 0.0, 0.03)
    centro = len(vs)
    vs.append((0, 0, H))
    for a, b in ((r0, r1), (r1, r2), (r2, r3), (r3, r4), (r4, r5)):
        for i in range(N):
            j = (i + 1) % N
            cs.append((a + i, a + j, b + j, b + i))
    for i in range(N):
        cs.append((r5 + i, r5 + (i + 1) % N, centro))
    cs.append(tuple(reversed(range(r0, r0 + N))))
    p.libre(vs, cs, "adoquin", tex="plano_fijo", recalcular=False)
    # Piedras sueltas del borde: bloques algo levantados y girados
    for k in range(26):
        i = int(N * k / 26 + rnd.uniform(-0.4, 0.4)) % N
        b = base[i] + base[i].normalized() * (mord[i] - rnd.uniform(0.15, 0.55))
        lx, ly, lz = rnd.uniform(0.9, 1.7), rnd.uniform(0.7, 1.15), H + rnd.uniform(-0.02, 0.1)
        m = tras(b.x, b.y, 0) @ rot("Z", math.degrees(math.atan2(b.y, b.x)) + 90 + rnd.uniform(-18, 18)) @ \
            rot("X", rnd.uniform(-3, 3)) @ rot("Y", rnd.uniform(-3, 3))
        p.caja((-lx / 2, -ly / 2, -0.05), (lx / 2, ly / 2, lz), "sillar", bisel=0.07, ruido=0.05, matriz=m,
               quitar="z-")
    q = []
    for clave, radio, fuerza in (("horno", (4.5, 3.6, 3), 1.0), ("yunque", (2.6, 2.4, 3), 0.75),
                                 ("barril", (1.8, 1.8, 3), 0.45)):
        x, y, _ = MONTAJE[clave]
        if clave == "horno":
            y -= 4.2    # delante de la boca
        q.append(((x, y, H), radio, fuerza))
    q += [((6.5, 5.5, H), (2.2, 1.8, 3), 0.55), ((-8.5, 4.5, H), (2.0, 2.4, 3), 0.5), ((5.0, -7.0, H), (1.6, 1.3, 3), 0.5)]
    cfg = {"quemaduras": q, "hollin": [((MONTAJE["horno"][0], MONTAJE["horno"][1] - 2.5, H), (9, 7.5, 4), 0.7)],
           "nota": "Plataforma de adoquín de borde irregular. La cara de arriba está a 0,62 studs."}
    return p, cfg


# ==================================================================================================================
# Horno / fundición
# ==================================================================================================================


def _apoyar(p0, p1, lado=(1, 0, 0)):
    """Matriz que lleva el eje X local a la dirección p0→p1 y el Y local hacia `lado`. Origen en p0."""
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    y = Vector(lado)
    y = (y - d * y.dot(d)).normalized()
    z = d.cross(y)
    m = Matrix((d, y, z)).transposed().to_4x4()
    m.translation = p0
    return m


def horno():
    p = Pieza("forja_horno", 31)
    rnd = p.rnd
    ZP, Z1 = 1.5, 6.2            # alto del zócalo de piedra y del cuerpo de ladrillo
    AB, ZS = 1.6, 2.9            # medio ancho de la boca y altura donde arranca el arco
    CX, YI, YB, ZC = 2.3, -2.05, 2.2, 4.9   # cámara interior

    def xs(z):
        return 3.55 - (z - ZP) / (Z1 - ZP) * 0.35

    def yf(z):
        return -2.75 + (z - ZP) / (Z1 - ZP) * 0.25

    # ---- Zócalo: núcleo y sillares por hiladas ----
    p.caja((-3.72, -2.87, 0), (3.72, 2.87, ZP), "sillar", quitar="z-")

    def tramos(a, b, mn=1.1, mx=1.9):
        cortes = [a]
        while b - cortes[-1] > mx + 0.6:
            cortes.append(cortes[-1] + rnd.uniform(mn, mx))
        cortes.append(b)
        return list(zip(cortes, cortes[1:]))

    for z0, z1 in ((0.0, 0.78), (0.78, ZP)):
        for x0, x1 in tramos(-3.92, 3.92):
            j = rnd.uniform(-0.03, 0.06)
            p.caja((x0 + 0.02, -3.02 - j, z0 + 0.02), (x1 - 0.02, -2.8, z1 - 0.02), "sillar", bisel=0.055,
                   quitar="y+", ruido=0.015)
            j = rnd.uniform(-0.03, 0.05)
            p.caja((x0 + 0.02, 2.8, z0 + 0.02), (x1 - 0.02, 3.0 + j, z1 - 0.02), "sillar", quitar="y-", ruido=0.015)
        for y0, y1 in tramos(-2.8, 2.8):
            for s in (-1, 1):
                j = rnd.uniform(-0.03, 0.06)
                a, b = sorted((s * 3.7, s * (3.92 + j)))
                p.caja((a, y0 + 0.02, z0 + 0.02), (b, y1 - 0.02, z1 - 0.02), "sillar", bisel=0.055,
                       quitar="x-" if s > 0 else "x+", ruido=0.015)
    # Repisa de piedra delante de la boca, sobre dos ménsulas
    p.caja((-2.25, -3.9, 1.2), (2.25, -2.95, 1.52), "sillar", bisel=0.06, ruido=0.02)
    for s in (-1, 1):
        p.caja((s * 1.6 - 0.25, -3.62, 0.62), (s * 1.6 + 0.25, -3.0, 1.2), "sillar", bisel=0.05, cono=(1.0, 1.0))

    # ---- Cuerpo de ladrillo con la boca en arco ----
    arco = [(AB * math.cos(t), ZS + AB * math.sin(t)) for t in [math.pi - math.pi * k / 10 for k in range(1, 10)]]
    boca = [(-AB, ZP), (-AB, ZS)] + arco + [(AB, ZS), (AB, ZP)]
    frente = [(-xs(ZP), ZP)] + boca + [(xs(ZP), ZP), (xs(Z1), Z1), (-xs(Z1), Z1)]
    vs = [(x, yf(z), z) for x, z in frente]
    n = len(vs)
    X0, X1, Y0, Y1 = xs(ZP), xs(Z1), -yf(ZP), -yf(Z1)
    vs += [(X0, Y0, ZP), (X1, Y1, Z1), (-X0, Y0, ZP), (-X1, Y1, Z1)]
    fi, fd = 0, n - 3          # abajo izquierda y abajo derecha del frente
    fdt, fit = n - 2, n - 1    # arriba derecha y arriba izquierda
    cs = [tuple(range(n)),
          (fd, n, n + 1, fdt),             # derecha
          (n + 2, fi, fit, n + 3),         # izquierda
          (n, n + 2, n + 3, n + 1)]        # detrás
    p.libre(vs, cs, "ladrillo", tex="plano_fijo", recalcular=False)
    # Túnel de la boca (el grosor del muro)
    vs, cs = [], []
    for x, z in boca:
        vs += [(x, yf(z), z), (x, YI, z)]
    for i in range(len(boca) - 1):
        cs.append((2 * i, 2 * i + 1, 2 * i + 3, 2 * i + 2))
    p.libre(vs, cs, "ladrillo_dentro", tex="plano_fijo", recalcular=False)
    # Cámara: paredes hacia dentro
    dentro = [(-CX, ZP)] + boca + [(CX, ZP), (CX, ZC), (-CX, ZC)]
    vs = [(x, YI, z) for x, z in dentro]
    n = len(vs)
    vs += [(CX, YB, ZP), (CX, YB, ZC), (-CX, YB, ZP), (-CX, YB, ZC)]
    cs = [tuple(reversed(range(n))),
          (n - 3, n - 2, n + 1, n),        # derecha (mira a -X)
          (0, n + 2, n + 3, n - 1),        # izquierda (mira a +X)
          (n + 2, n, n + 1, n + 3),        # fondo (mira a -Y)
          (n - 1, n + 3, n + 1, n - 2)]    # techo
    p.libre(vs, cs, "ladrillo_dentro", tex="plano_fijo", recalcular=False)

    # ---- Lecho de brasas ----
    def alto_lecho(x, y):
        return ZP + 0.1 + 0.6 * math.exp(-(x * x / 2.4 + (y - 0.2) ** 2 / 2.2))

    def rejilla(x0, x1, y0, y1, nx, ny, f, mat, ruido=0.06):
        vs, cs = [], []
        for j in range(ny):
            for i in range(nx):
                x, y = x0 + (x1 - x0) * i / (nx - 1), y0 + (y1 - y0) * j / (ny - 1)
                vs.append((x, y, f(x, y) + rnd.uniform(-ruido, ruido)))
        for j in range(ny - 1):
            for i in range(nx - 1):
                cs.append((j * nx + i, j * nx + i + 1, (j + 1) * nx + i + 1, (j + 1) * nx + i))
        p.libre(vs, cs, mat, tex=None, recalcular=False)

    rejilla(-CX, CX, YI, YB, 10, 8, alto_lecho, "brasa")
    rejilla(-AB, AB, -2.74, YI + 0.06, 6, 3, lambda x, y: ZP + 0.04 + 0.1 * (y + 2.74), "brasa", ruido=0.02)
    for k in range(18):
        x, y = rnd.uniform(-1.9, 1.9), rnd.uniform(-2.5, 1.6)
        if y < YI:
            x *= 0.7
        t = rnd.uniform(0.22, 0.42)
        m = tras(x, y, alto_lecho(x, y) + t * 0.2 if y > YI else ZP + 0.08) @ rot("Z", rnd.uniform(0, 360)) @ \
            rot("X", rnd.uniform(-25, 25))
        p.caja((-t / 2, -t * 0.4, -t * 0.3), (t / 2, t * 0.4, t * 0.3), "carbon" if (y < -1.9 and k % 2) else "brasa",
               tex=None, ruido=t * 0.18, matriz=m)
    # Barra de hierro calentándose, apoyada en la repisa
    p.viga((0.75, -3.75, 1.6), (0.3, -0.9, 2.0), 0.11, 0.11, "hierro_herr", ruido=0.004)

    # ---- Dovelas del arco y jambas ----
    ND = 9
    for k in range(ND):
        a0 = math.pi - math.pi * k / ND - 0.014
        a1 = math.pi - math.pi * (k + 1) / ND + 0.014
        clave = k == ND // 2
        ro = 2.45 if clave else (2.18 if k % 2 else 2.28)
        sale = 0.2 if clave else 0.13 + rnd.uniform(-0.02, 0.02)
        pts = [(1.57, a0), (1.57, a1), (ro, a1), (ro, a0)]
        fr = [(r * math.cos(a), yf(ZS + r * math.sin(a)) - sale, ZS + r * math.sin(a)) for r, a in pts]
        fo = [(x, y + sale + 0.12, z) for x, y, z in fr]
        p.hexaedro(fr, fo, "sillar", bisel=0.05, sin_fondo=True)
    for s in (-1, 1):
        for z0, z1, ancho in ((ZP, 2.2, 0.75), (2.2, ZS - 0.02, 0.6)):
            a, b = sorted((s * 1.57, s * (1.57 + ancho)))
            p.caja((a, yf(z0) - 0.13, z0 + 0.02), (b, yf(z0) + 0.12, z1 - 0.02), "sillar", bisel=0.05, quitar="y+",
                   ruido=0.012)
    # ---- Esquinas de sillería ----
    dz = (Z1 - ZP) / 6
    for sx in (-1, 1):
        for sy in (-1, 1):
            for k in range(6):
                z0 = ZP + dz * k
                a, b = ((1.0, 0.55), (0.55, 1.0))[(k + (sy > 0)) % 2]
                X, Y = xs(z0 + dz / 2), -yf(z0 + dz / 2)
                xa, xb = sorted((sx * (X - a), sx * (X + 0.07)))
                ya, yb_ = sorted((sy * (Y - b), sy * (Y + 0.07)))
                p.caja((xa, ya, z0 + 0.02), (xb, yb_, z0 + dz - 0.02), "sillar", bisel=0.05 if sy < 0 else 0.0,
                       quitar=("x-" if sx > 0 else "x+") + (" y+" if sy < 0 else " y-"), ruido=0.012)
    # ---- Cornisa ----
    zc0, zc1 = Z1, Z1 + 0.42
    for x0, x1 in tramos(-3.44, 3.44, 1.0, 1.7):
        p.caja((x0 + 0.015, -2.74, zc0), (x1 - 0.015, -2.1, zc1), "sillar", bisel=0.05, quitar="y+", ruido=0.012)
        p.caja((x0 + 0.015, 2.1, zc0), (x1 - 0.015, 2.74, zc1), "sillar", quitar="y-", ruido=0.012)
    for y0, y1 in tramos(-2.1, 2.1, 1.0, 1.6):
        for s in (-1, 1):
            a, b = sorted((s * 2.8, s * 3.44))
            p.caja((a, y0 + 0.015, zc0), (b, y1 - 0.015, zc1), "sillar", bisel=0.05, quitar="x-" if s > 0 else "x+",
                   ruido=0.012)
    p.caja((-3.26, -2.56, zc1), (3.26, 2.56, zc1 + 0.2), "sillar", bisel=0.05, quitar="z-")
    # ---- Campana y chimenea ----
    ZH0, ZH1, ZT = zc1 + 0.2, 9.2, 14.2

    def tronco(z0, hx0, hy0, z1, hx1, hy1, mat):
        vs = [(hx0, -hy0, z0), (hx0, hy0, z0), (-hx0, hy0, z0), (-hx0, -hy0, z0),
              (hx1, -hy1, z1), (hx1, hy1, z1), (-hx1, hy1, z1), (-hx1, -hy1, z1)]
        cs = [(0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        p.libre(vs, cs, mat, tex="plano_fijo", recalcular=False)

    tronco(ZH0, 3.1, 2.4, ZH1, 1.3, 1.3, "ladrillo")
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.viga((sx * 3.1, sy * 2.4, ZH0 - 0.05), (sx * 1.3, sy * 1.3, ZH1 + 0.05), 0.34, 0.34, "sillar", ruido=0.02)
    tronco(ZH1, 1.22, 1.22, ZT, 1.02, 1.02, "ladrillo")
    p.caja((-1.48, -1.48, ZH1 - 0.15), (1.48, 1.48, ZH1 + 0.22), "sillar", bisel=0.07, ruido=0.02)
    p.caja((-1.2, -1.2, 13.25), (1.2, 1.2, 13.55), "sillar", bisel=0.05, ruido=0.015)
    for (a, b) in (((-1.32, -1.32), (1.32, -0.74)), ((-1.32, 0.74), (1.32, 1.32)), ((-1.32, -0.74), (-0.74, 0.74)),
                   ((0.74, -0.74), (1.32, 0.74))):
        p.caja((a[0], a[1], ZT), (b[0], b[1], ZT + 0.32), "sillar", bisel=0.05, ruido=0.02)
    p.caja((-0.74, -0.74, 13.3), (0.74, 0.74, ZT + 0.3), "ladrillo_dentro", quitar="z+", invertir=True)
    for zb in (10.5, 12.1):
        h = 1.22 - (zb - ZH1) / (ZT - ZH1) * 0.2 + 0.045
        p.caja((-h, -h, zb), (h, h, zb + 0.24), "hierro", tex=None)
        for s in (-0.5, 0.5):
            p.remache((s * h, -h, zb + 0.12), (0, -1, 0), 0.06, "hierro")
            p.remache((h, s * h, zb + 0.12), (1, 0, 0), 0.06, "hierro")
            p.remache((-h, s * h, zb + 0.12), (-1, 0, 0), 0.06, "hierro")
    # Anclas de hierro en el muro
    for s in (-1, 1):
        x, z = s * 2.55, 5.25
        y = yf(z) - 0.035
        p.viga((x - 0.4, y, z - 0.4), (x + 0.4, y, z + 0.4), 0.07, 0.12, "hierro", ruido=0.0)
        p.viga((x - 0.4, y, z + 0.4), (x + 0.4, y, z - 0.4), 0.07, 0.12, "hierro", ruido=0.0)
        p.remache((x, y - 0.03, z), (0, -1, 0), 0.08, "hierro")

    # ---- Fuelle, a la derecha ----
    medio = [(0.0, 0.14), (0.5, 0.42), (1.1, 0.78), (1.8, 0.98), (2.4, 1.0), (2.85, 0.85), (3.1, 0.45)]
    contorno = [(u, -v) for u, v in medio] + [(u, v) for u, v in reversed(medio)]   # antihorario visto desde arriba
    M_tapa = tras(0, 0, 2.2) @ rot("Y", -13.0)
    with p.grupo(tras(4.45, 0.4, 0)):
        p.prisma(contorno, 2.0, 2.12, "madera_osc", eje="Z", tex=("veta", "X"), bisel=0.025)
        with p.grupo(M_tapa):
            p.prisma(contorno, 0.0, 0.12, "madera_osc", eje="Z", tex=("veta", "X"), bisel=0.025)
            p.caja((2.3, -0.1, 0.12), (4.0, 0.1, 0.3), "madera_mango", tex=("veta", "X"), bisel=0.03)
            for u, v in contorno:
                q = Vector((1.75 + (u - 1.75) * 0.9, v * 0.88, 0.12))
                p.remache(q, (0, 0, 1), 0.045, "hierro")
        # Cuero en acordeón entre las dos tablas
        an = []
        for t, k in ((0.0, 0.97), (0.25, 0.8), (0.5, 0.99), (0.75, 0.8), (1.0, 0.97)):
            anillo = []
            for u, v in contorno:
                uu, vv = 1.75 + (u - 1.75) * k if u > 0.3 else u, v * k
                a = Vector((uu, vv, 2.12))
                b = M_tapa @ Vector((uu, vv, 0.0))
                anillo.append(a.lerp(b, t))
            an.append(anillo)
        p.loft(an, "cuero", tex=None, tapas=(False, False), recalcular=False)
        # Tobera de hierro hacia el horno
        p.tubo([(0.25, 0, 2.16), (-0.2, 0, 2.18), (-1.0, 0, 2.3)], [0.24, 0.2, 0.11], "hierro", n=8)
        p.tubo([(-0.2, 0, 2.18), (-0.3, 0, 2.2)], 0.23, "hierro", n=8)
        # Caballetes
        for u in (0.75, 2.5):
            for v in (-0.72, 0.72):
                p.tabla((u - 0.11, v - 0.11, 0), (u + 0.11, v + 0.11, 1.8), "madera_osc", eje="Z", bisel=0.02)
            p.tabla((u - 0.13, -1.02, 1.8), (u + 0.13, 1.02, 2.0), "madera_osc", eje="Y", bisel=0.02)
            p.tabla((u - 0.07, -0.72, 0.5), (u + 0.07, 0.72, 0.68), "madera_osc", eje="Y")
        p.tabla((0.75, -0.07, 0.56), (2.5, 0.07, 0.72), "madera_osc", eje="X")

    # ---- Tenazas largas y atizador, apoyados en el muro ----
    for x, largo, boca_, abre in ((-3.0, 4.0, 0.55, 0.1), (-2.35, 3.5, 0.4, 0.04)):
        p0, p1 = Vector((x, -3.95, 0.04)), Vector((x + 0.1, -2.9, 0.04 + largo * 0.93))
        d = (p1 - p0).normalized()
        with p.grupo(_apoyar(p0 + d * boca_, p1)):
            _tenazas(p, largo=largo, boca=boca_, abre=abre)
    with p.grupo(_apoyar((2.6, -3.85, 0.03), (2.75, -2.88, 3.9))):
        p.tubo([(-0.02, 0.18, 0), (0.0, 0.0, 0), (0.6, 0, 0), (2.4, 0, 0), (4.0, 0, 0)], 0.04, "hierro_herr", n=5)
        p.tubo([(4.0 + 0.14 - 0.14 * math.cos(t), 0.14 * math.sin(t), 0) for t in [TAU * k / 8 for k in range(9)]],
               0.035, "hierro_herr", n=4)

    # ---- Carbonera a la izquierda, con su pala ----
    bx, by = -4.75, 0.4
    for (a, b) in (((bx - 0.78, by - 1.2, 0), (bx + 0.78, by - 1.08, 0.95)), ((bx - 0.78, by + 1.08, 0), (bx + 0.78, by + 1.2, 0.95)),
                   ((bx - 0.78, by - 1.08, 0), (bx - 0.66, by + 1.08, 0.95)), ((bx + 0.66, by - 1.08, 0), (bx + 0.78, by + 1.08, 0.82))):
        p.tabla(a, b, "madera_osc", bisel=0.02, ruido=0.015)
    for sx in (-0.84, 0.72):
        for sy in (-1.26, 1.14):
            p.tabla((bx + sx, by + sy, 0), (bx + sx + 0.12, by + sy + 0.12, 1.05), "madera_osc", eje="Z")
    rejilla(bx - 0.66, bx + 0.66, by - 1.08, by + 1.08, 5, 7,
            lambda x, y: 0.72 + 0.45 * math.exp(-((x - bx) ** 2 / 0.5 + (y - by) ** 2 / 1.2)), "carbon", ruido=0.07)
    with p.grupo(_apoyar((-4.6, -1.75, 0.03), (-3.7, -1.6, 3.9), lado=(0, 1, 0))):
        p.caja((-0.05, -0.3, -0.03), (0.75, 0.3, 0.03), "hierro_herr", tex=None, cono=(1.0, 1.0), ruido=0.02)
        p.tubo([(0.6, 0, 0.02), (2.4, 0, 0.0), (4.0, 0, 0.0)], [0.06, 0.055, 0.06], "madera_mango", n=7)

    cfg = {
        "hollin": [((0, -2.9, 5.3), (3.3, 2.2, 3.8), 1.3), ((0, 0, 14.6), (2.6, 2.6, 3.4), 1.3),
                   ((3.6, 0.4, 2.4), (1.2, 1.6, 1.3), 0.6), ((-4.75, 0.4, 0.8), (1.6, 2.0, 1.4), 0.8)],
        "hollin_base": 0.25, "resplandor": (1.5, 4.6),
        "anclajes": {"Humo": (0, 0, ZT + 0.4), "Fuego": (0, -0.8, 2.3), "Luz": (0, -2.3, 2.9)},
        "nota": "Horno de fundición con chimenea, fuelle, tenazas, atizador y carbonera. Las brasas van aparte "
                "(forja_horno_brasas) para ponerlas en Neon. Humo, fuego y luz: Attachments «Humo», «Fuego» y «Luz».",
    }
    return p, cfg


PIEZAS = {"horno": horno, "barril": barril, "yunque": yunque, "mesa": mesa, "estanteria": estanteria, "suelo": suelo}
