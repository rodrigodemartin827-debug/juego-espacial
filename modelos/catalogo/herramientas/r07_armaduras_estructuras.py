"""Ronda 7: armaduras para R6 (modelos 41-44) y estructuras especiales (78-80).

Armaduras: el origen es el centro del Torso R6 (2 × 2 × 1 studs); los brazos R6 están en x = ±1,5.
Cascos: el origen es el centro de la cabeza R6 (≈1,2 studs de ancho)."""

import math

from comunes import antena, barandilla, tira
from lib import anillo


def _peto(g, metal, oscuro, borde):
    # Coraza: secciones redondeadas de cintura a hombros, con el pecho adelantado (frente = -Y).
    secciones = ((-1.08, 1.08, 0.60, 0.0), (-0.55, 1.10, 0.63, -0.02), (0.10, 1.16, 0.70, -0.06), (0.60, 1.14, 0.70, -0.06),
                 (0.95, 1.02, 0.62, -0.02), (1.08, 0.70, 0.5, 0.0))
    g.loft(metal, [anillo(rx, ry, 14, z, pot=3.2, c=(0, cy)) for z, rx, ry, cy in secciones])
    # Cinturón, gola y arista central.
    g.loft(oscuro, [anillo(1.13, 0.66, 14, -1.1, pot=3.2), anillo(1.15, 0.68, 14, -0.82, pot=3.2)])
    g.toro(borde, 0.52, 0.11, (0, 0, 1.1), seg=10, lados=5, esc=(1, 0.85, 1))
    g.prisma(metal, [(-0.12, -0.75), (0.12, -0.75), (0.2, 0.75), (-0.2, 0.75)], 0.14, (0, -0.74, 0.05), (4, 0, 0), plano="xz")


def _hombrera(g, s, metal, borde, lamas=2, pua=False):
    x = s * 1.5
    g.rev(metal, [(0.66, 0.0), (0.64, 0.14), (0.45, 0.32), (0.0, 0.4)], (x, 0, 0.82), (0, s * 16, 0), esc=(0.95, 0.9, 1), lados=10)
    g.toro(borde, 0.65, 0.06, (x, 0, 0.83), (0, s * 16, 0), seg=10, lados=4, esc=(0.95, 0.9, 1))
    for i in range(lamas):
        z = 0.62 - i * 0.26
        g.rev(metal, [(0.6 - i * 0.03, 0.0), (0.64 - i * 0.03, 0.22), (0.5, 0.26), (0.5, 0.0)], (x + s * (0.08 + i * 0.03), 0, z - 0.22),
              (0, s * (14 - i * 6), 0), esc=(0.9, 0.92, 1), lados=10)
        g.toro(borde, 0.61 - i * 0.03, 0.04, (x + s * (0.08 + i * 0.03), 0, z - 0.2), (0, s * (14 - i * 6), 0), seg=10, lados=3,
               esc=(0.9, 0.92, 1))
    if pua:
        g.cil(borde, 0.14, 0.45, (x + s * 0.2, 0, 1.12), (0, s * 30, 0), lados=6, r2=0.0)


def armadura_hierro(g):
    g.pieza("peto", pivote=(0, 0, 0))
    _peto(g, "hierro", "cuero", "hierro_osc")
    for px, pz in ((-0.7, 0.65), (0.7, 0.65), (-0.8, -0.45), (0.8, -0.45)):
        g.esfera("hierro_osc", 0.07, (px, -0.69 if pz < 0 else -0.74, pz), lados=5, anillos=3)
    g.caja("hierro_osc", (0.34, 0.1, 0.28), (0, -0.7, -0.96), bisel=0.03)
    for s in (-1, 1):
        g.caja("cuero", (0.2, 1.3, 0.14), (s * 0.72, 0, 1.06))
    for s, nom in ((-1, "hombrera_izq"), (1, "hombrera_der")):
        g.pieza(nom, pivote=(s * 1.5, 0, 0), padre="peto")
        _hombrera(g, s, "hierro", "hierro_osc", lamas=1)
    g.ancla("TorsoCentro", (0, 0, 0))


def armadura_acero(g):
    g.pieza("peto", pivote=(0, 0, 0))
    _peto(g, "acero", "h_oscuro", "oro")
    # Pectorales marcados, ribetes dorados, núcleo de energía y faldón naranja.
    for s in (-1, 1):
        g.esfera("acero", 0.52, (s * 0.52, -0.52, 0.42), esc=(1, 0.5, 0.85), lados=8, anillos=5)
        g.prisma("oro", [(s * 0.1, -0.1), (s * 0.95, 0.05), (s * 1.0, 0.18), (s * 0.1, 0.05)], 0.1, (0, -0.76, -0.12), plano="xz")
        g.prisma("acero", [(s * 0.15, -0.95), (s * 1.0, -0.85), (s * 1.05, -0.2), (s * 0.15, -0.35)], 0.1, (0, -0.68, 0.02), plano="xz")
        g.caja("h_oscuro", (0.22, 1.36, 0.16), (s * 0.72, 0, 1.06))
    g.cil("oro", 0.26, 0.12, (0, -0.74, 0.5), (90, 0, 0), lados=6)
    g.cil("h_neon", 0.17, 0.14, (0, -0.76, 0.5), (90, 0, 0), lados=6)
    g.prisma("tela_naranja", [(-0.45, 0.0), (0.45, 0.0), (0.35, -0.75), (0, -0.95), (-0.35, -0.75)], 0.07, (0, -0.72, -1.05), plano="xz")
    g.prisma("oro", [(-0.14, -0.2), (0.14, -0.2), (0, -0.5)], 0.09, (0, -0.76, -1.15), plano="xz")
    g.toro("oro", 1.14, 0.06, (0, 0, -0.8), seg=14, lados=4, esc=(1, 0.6, 1), pot=3.2)
    g.caja("h_neon", (0.5, 0.06, 0.12), (0, 0.72, 0.4))
    g.prisma("acero", [(-0.5, 0.9), (0.5, 0.9), (0.3, -0.6), (-0.3, -0.6)], 0.12, (0, 0.7, 0.0), plano="xz")
    for s, nom in ((-1, "hombrera_izq"), (1, "hombrera_der")):
        g.pieza(nom, pivote=(s * 1.5, 0, 0), padre="peto")
        _hombrera(g, s, "acero", "oro", lamas=2, pua=True)
        g.caja("h_neon", (0.08, 0.4, 0.08), (s * 2.14, 0, 0.5))
    g.ancla("TorsoCentro", (0, 0, 0))


def casco_hierro(g):
    # Casco medieval sencillo: bacinete con cerco, protector nasal y remaches.
    g.rev("hierro", [(0.80, -0.12), (0.82, 0.1), (0.76, 0.42), (0.55, 0.7), (0.25, 0.84), (0.0, 0.88)], (0, 0, 0), lados=12)
    g.toro("hierro_osc", 0.82, 0.08, (0, 0, -0.08), seg=12, lados=5)
    g.prisma("hierro_osc", [(-0.1, 0.05), (0.1, 0.05), (0.13, -0.62), (-0.13, -0.62)], 0.1, (0, -0.84, 0), plano="xz")
    g.tubo("hierro_osc", [(0, -0.8, 0.0), (0, -0.62, 0.55), (0, 0.0, 0.92), (0, 0.62, 0.55), (0, 0.8, 0.0)], 0.07, lados=4, suave=False)
    for i in range(10):
        a = 2 * math.pi * (i + 0.5) / 10
        g.esfera("hierro_osc", 0.055, (0.83 * math.cos(a), 0.83 * math.sin(a), 0.1), lados=5, anillos=3)
    # Carrilleras y cubrenuca de placas.
    for sx in (-1, 1):
        g.prisma("hierro", [(-0.32, 0.0), (0.3, 0.0), (0.22, -0.55), (-0.05, -0.7), (-0.3, -0.45)], 0.09, (sx * 0.8, -0.1, -0.1), plano="yz")
        g.esfera("hierro_osc", 0.06, (sx * 0.86, -0.1, -0.3), lados=5, anillos=3)
    for k, a in enumerate((50, 90, 130)):
        ar = math.radians(a)
        g.caja("hierro", (0.62, 0.09, 0.5), (0.8 * math.cos(ar), 0.8 * math.sin(ar), -0.35), rot=(-8, 0, a - 90))
    g.ancla("CabezaCentro", (0, 0, 0))


def casco_acero(g):
    # Yelmo cerrado con visera, ranura de visión iluminada, carrilleras y cresta naranja.
    g.rev("acero", [(0.78, -0.55), (0.84, -0.1), (0.84, 0.15), (0.76, 0.45), (0.55, 0.72), (0.25, 0.86), (0.0, 0.9)], (0, 0, 0), lados=12)
    g.toro("oro", 0.84, 0.06, (0, 0, 0.12), seg=12, lados=4)
    g.toro("oro", 0.79, 0.06, (0, 0, -0.55), seg=12, lados=4)
    # Visera en cuña (pico), con ranura de visión iluminada y respiraderos.
    g.prisma("acero", [(-0.66, -0.52), (0.0, -1.14), (0.66, -0.52)], 0.78, (0, 0, -0.14), plano="xy", sup=0.94)
    g.prisma("oro", [(-0.7, -0.5), (0.0, -1.2), (0.7, -0.5), (0.0, -1.0)], 0.1, (0, 0, 0.26), plano="xy")
    g.caja("oro", (0.1, 0.1, 0.8), (0, -1.12, -0.14), rot=(0, 0, 45))
    ang = math.degrees(math.atan2(0.62, 0.66))
    for s in (-1, 1):
        g.caja("h_oscuro", (0.62, 0.08, 0.16), (s * 0.34, -0.845, 0.02), rot=(0, 0, s * ang))
        g.caja("h_neon", (0.5, 0.1, 0.07), (s * 0.34, -0.85, 0.02), rot=(0, 0, s * ang))
        for k in range(3):
            g.caja("h_oscuro", (0.05, 0.1, 0.2), (s * (0.2 + k * 0.13), -0.975 + k * 0.122, -0.3), rot=(0, 0, s * ang))
        g.cil("oro", 0.13, 0.1, (s * 0.84, -0.1, 0.0), (0, 90, 0), lados=6)
    # Cresta / penacho naranja.
    cresta = [(-0.75, 0.3), (-0.55, 0.85), (-0.1, 1.2), (0.45, 1.15), (0.85, 0.75), (1.0, 0.1), (0.8, 0.3), (0.4, 0.75), (-0.1, 0.86),
              (-0.5, 0.62)]
    g.prisma("tela_naranja", cresta, 0.14, (0, 0, 0), plano="yz")
    g.prisma("oro", [(-0.78, 0.2), (-0.5, 0.66), (-0.1, 0.9), (0.4, 0.8), (0.8, 0.35), (0.86, 0.1), (0.4, 0.62), (-0.1, 0.78), (-0.5, 0.5)],
             0.2, (0, 0, 0), plano="yz")
    g.ancla("CabezaCentro", (0, 0, 0))


# ------------------------------------------------------------------------------------------------ estructuras

def plataforma_lanzamiento(g):
    R, H = 24.0, 2.6
    N = 8
    g.cil("h_hormigon", R + 3.5, H, (0, 0, 0), (0, 0, 22.5), lados=N, r2=R, suave=False)
    g.cil("h_suelo", R - 0.6, 0.15, (0, 0, H), (0, 0, 22.5), lados=N, suave=False)
    # Anillo de peligro, diana de aterrizaje y luces.
    g.toro("h_peligro", R - 2.2, 0.9, (0, 0, H + 0.08), (0, 0, 22.5), seg=N, lados=4, esc=(1, 1, 0.12), suave=False)
    g.toro("h_neon", 12.0, 0.16, (0, 0, H + 0.2), seg=24, lados=4)
    g.toro("h_naranja_liso", 8.0, 0.5, (0, 0, H + 0.16), seg=24, lados=4, esc=(1, 1, 0.15))
    for a in range(0, 360, 90):
        g.caja("h_naranja_liso", (0.8, 5.0, 0.08), (5.2 * math.cos(math.radians(a + 90)) * 0 + 0, 0, H + 0.2), rot=(0, 0, a)) if False else None
        with g.grupo((0, 0, H + 0.15), (0, 0, a)):
            g.caja("h_blanco_liso", (0.7, 4.5, 0.08), (0, 3.6, 0.03))
            g.prisma("h_blanco_liso", [(-1.2, 5.6), (1.2, 5.6), (0, 7.4)], 0.08, (0, 0, 0.03), plano="xy")
    for i in range(N):
        a = math.radians(360 * i / N + 22.5)
        px, py = (R - 0.9) * math.cos(a) * 0.92, (R - 0.9) * math.sin(a) * 0.92
        g.cil("h_gris", 0.5, 0.5, (px, py, H), lados=8)
        g.cil("h_neon", 0.36, 0.3, (px, py, H + 0.5), lados=8)
    # Rampa de acceso al frente con barandillas y franja naranja.
    g.prisma("h_hormigon", [(-R + 1.0, H), (-R - 12.0, 0.0), (-R + 1.0, 0.0)], 9.0, (0, 0, 0), (0, 0, 90), plano="xz")
    g.prisma("h_naranja_liso", [(-R + 1.0, H + 0.06), (-R - 12.0, 0.06), (-R - 12.0, 0.0), (-R + 1.0, H)], 1.2, (0, 0, 0), (0, 0, 90),
             plano="xz")
    for s in (-1, 1):
        barandilla(g, (s * 4.5, -R + 1.0, H), (s * 4.5, -R - 11.0, 0.25), 1.6, postes=5, r=0.1)
    # Cuatro mordazas de sujeción alrededor de la diana.
    for i, a in enumerate((45, 135, 225, 315)):
        with g.grupo((0, 0, H), (0, 0, a)):
            g.caja("h_gris", (2.6, 2.2, 1.0), (14.5, 0, 0.15), base=True, bisel=0.12)
            g.caja("h_naranja_liso", (4.5, 1.2, 0.8), (12.6, 0, 1.6), rot=(0, -22, 0), bisel=0.1)
            g.caja("h_oscuro", (1.2, 1.6, 1.2), (10.4, 0, 2.6), rot=(0, -22, 0), bisel=0.1)
            g.cil("h_metal", 0.3, 2.4, (14.5, -1.2, 1.2), (-90, 0, 0), lados=6)
    # Torre de servicio con brazo, focos y depósitos.
    tx, ty = 17.0, 15.5
    g.caja("h_gris", (6.0, 6.0, 1.0), (tx, ty, H), base=True, bisel=0.12)
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.caja("h_naranja_liso", (0.6, 0.6, 30.0), (tx + sx * 2.2, ty + sy * 2.2, H + 1.0), base=True)
    for k in range(5):
        z = H + 4.0 + k * 6.0
        g.caja("h_gris", (5.2, 5.2, 0.4), (tx, ty, z))
        if k < 4:
            for sx, sy, rz in ((0, -2.2, 0), (0, 2.2, 0), (-2.2, 0, 90), (2.2, 0, 90)):
                g.caja("h_metal", (7.4, 0.25, 0.25), (tx + sx, ty + sy, z + 3.0), rot=(0, 52 if (k % 2) else -52, rz))
    g.caja("h_blanco_liso", (5.6, 5.6, 3.4), (tx, ty, H + 31.0), base=True, bisel=0.15)
    g.caja("h_cristal", (4.2, 0.2, 1.6), (tx, ty - 2.85, H + 33.0))
    g.caja("h_cristal", (0.2, 4.2, 1.6), (tx - 2.85, ty, H + 33.0))
    antena(g, (tx, ty, H + 34.4), 7.0, r=0.2)
    g.caja("h_gris", (12.0, 1.6, 1.6), (tx - 7.0, ty - 5.0, H + 22.0), rot=(0, 0, 38), bisel=0.12)
    g.caja("h_naranja_liso", (2.4, 2.4, 2.0), (tx - 11.6, ty - 8.6, H + 22.0), rot=(0, 0, 38), bisel=0.12)
    tira(g, "h_neon", (tx - 2.56, ty - 2.56, H + 2.0), (tx - 2.56, ty - 2.56, H + 30.0), 0.2)
    for i in range(2):
        g.cil("h_blanco_liso", 2.4, 8.0, (-17.0 - i * 0.0, 12.0 + i * 5.6, H), lados=12, bisel=0.4)
        g.cil("h_naranja_liso", 2.5, 0.8, (-17.0, 12.0 + i * 5.6, H + 3.6), lados=12)
        g.tubo("h_metal", [(-17.0, 12.0 + i * 5.6, H + 8.0), (-17.0, 12.0 + i * 5.6, H + 9.6), (-12.0, 9.0 + i * 3.0, H + 9.6),
                           (-12.0, 9.0 + i * 3.0, H)], 0.3, lados=6)
    # Deflector de llamas al fondo y consola.
    g.prisma("h_oscuro", [(0, 0), (4.0, 0), (4.0, 0.6), (1.0, 5.0), (0, 5.0)], 16.0, (0, R - 6.0, H), (0, 0, 90), plano="xz")
    g.caja("h_gris", (2.0, 1.4, 2.4), (-9.0, -R + 3.2, H), base=True, sup=(1, 0.6), bisel=0.08)
    g.caja("h_neon", (1.6, 0.08, 0.9), (-9.0, -R + 2.7, H + 2.2), rot=(-25, 0, 0))
    g.ancla("Nave", (0, 0, H + 0.2))
    g.ancla("Consola", (-9.0, -R + 2.2, H))


def torreta_defensa(g):
    # Base blindada fija; cabeza que gira (pieza «cabeza») y cañones que cabecean (pieza «canones»).
    g.cil("h_hormigon", 5.0, 0.6, (0, 0, 0), (0, 0, 30), lados=6, bisel=0.1, suave=False)
    g.cil("h_gris", 4.0, 3.0, (0, 0, 0.6), (0, 0, 30), lados=6, r2=3.0, suave=False)
    g.cil("h_naranja_liso", 3.1, 0.5, (0, 0, 3.6), (0, 0, 30), lados=6, suave=False)
    for i in range(6):
        a = math.radians(60 * i + 30)
        g.caja("h_oscuro", (1.2, 0.5, 2.4), (3.45 * math.cos(a), 3.45 * math.sin(a), 2.0), rot=(0, 0, math.degrees(a) + 90))
        g.caja("h_neon", (0.5, 0.12, 1.2), (3.74 * math.cos(a), 3.74 * math.sin(a), 2.1), rot=(0, 0, math.degrees(a) + 90))
    g.cil("h_oscuro", 2.2, 0.6, (0, 0, 4.1), lados=12)
    g.caja("h_gris", (2.2, 1.6, 1.8), (4.4, 2.6, 0.6), base=True, rot=(0, 0, 30), bisel=0.1)
    g.caja("h_peligro", (2.24, 1.64, 0.5), (4.4, 2.6, 1.9), rot=(0, 0, 30))
    Z = 4.7
    g.pieza("cabeza", pivote=(0, 0, Z))
    g.cil("h_gris", 2.5, 0.5, (0, 0, Z), lados=12, bisel=0.1)
    g.caja("h_blanco_liso", (4.6, 5.4, 3.0), (0, 0.5, Z + 0.5), base=True, sup=(0.78, 0.8), desv=(0, 0.3), bisel=0.18)
    g.caja("h_naranja_liso", (4.8, 1.2, 0.9), (0, 2.4, Z + 1.2), bisel=0.1)
    for s in (-1, 1):
        g.caja("h_gris", (0.9, 3.4, 2.6), (s * 2.6, 0.0, Z + 0.7), base=True, bisel=0.12)
        g.cil("h_oscuro", 0.9, 0.3, (s * 3.05, 0.0, Z + 2.0), (0, s * 90, 0), lados=10)
        tira(g, "h_neon", (s * 3.1, -1.2, Z + 2.9), (s * 3.1, 1.2, Z + 2.9), 0.16)
    g.caja("h_oscuro", (1.6, 1.2, 0.9), (0, 0.8, Z + 3.5), base=True, bisel=0.1)
    g.cil("h_neon", 0.4, 0.2, (0, 0.18, Z + 3.95), (90, 0, 0), lados=8)
    antena(g, (1.4, 2.4, Z + 3.4), 3.6, r=0.1)
    g.caja("h_cristal", (2.0, 0.2, 0.8), (0, -1.92, Z + 2.7), rot=(-18, 0, 0))
    g.pieza("canones", pivote=(0, -0.6, Z + 2.0), padre="cabeza")
    for s in (-1, 1):
        g.caja("h_gris", (1.3, 2.6, 1.3), (s * 1.05, -2.6, Z + 2.0), bisel=0.12)
        g.cil("h_oscuro", 0.36, 5.4, (s * 1.05, -3.6, Z + 2.0), (90, 0, 0), lados=8)
        g.cil("h_metal", 0.48, 1.3, (s * 1.05, -8.4, Z + 2.0), (90, 0, 0), lados=8, bisel=0.06)
        g.cil("h_naranja_liso", 0.44, 0.5, (s * 1.05, -5.6, Z + 2.0), (90, 0, 0), lados=8)
        g.cil("h_neon", 0.3, 0.1, (s * 1.05, -9.72, Z + 2.0), (90, 0, 0), lados=8)
        g.ancla("Boca" + ("Izq" if s < 0 else "Der"), (s * 1.05, -9.8, Z + 2.0))
    g.pieza("cuerpo")
    g.ancla("Giro", (0, 0, Z))


def generador_energia(g):
    g.cil("h_hormigon", 8.5, 0.6, (0, 0, 0), (0, 0, 22.5), lados=8, bisel=0.1, suave=False)
    g.cil("h_gris", 6.5, 2.2, (0, 0, 0.6), (0, 0, 22.5), lados=8, r2=5.4, suave=False)
    g.toro("h_peligro", 5.2, 0.5, (0, 0, 2.8), (0, 0, 22.5), seg=8, lados=4, esc=(1, 1, 0.3), suave=False)
    g.cil("h_oscuro", 3.4, 1.0, (0, 0, 2.8), lados=12, bisel=0.1)
    # Núcleo: columna de plasma dentro de un tubo de cristal, entre dos coronas.
    g.pieza("nucleo", pivote=(0, 0, 8.0))
    g.rev("h_neon", [(0.0, 0.0), (1.1, 0.6), (1.5, 3.0), (1.6, 4.4), (1.5, 5.8), (1.1, 8.2), (0.0, 8.8)], (0, 0, 3.8), lados=10)
    g.pieza("cuerpo")
    g.rev("h_cristal", [(2.5, 0.0), (2.5, 8.6), (2.3, 8.6), (2.3, 0.0)], (0, 0, 3.8), lados=12, tapas=(False, False))
    g.loft("h_cristal", [], suave=False) if False else None
    g.cil("h_gris", 3.2, 1.2, (0, 0, 12.2), lados=12, r2=2.6, bisel=0.1)
    g.cil("h_naranja_liso", 2.7, 0.6, (0, 0, 13.4), lados=12)
    g.cil("h_oscuro", 1.6, 1.4, (0, 0, 14.0), lados=10, r2=1.0)
    g.esfera("h_neon", 0.7, (0, 0, 15.9), lados=8, anillos=5)
    for z in (5.2, 8.1, 11.0):
        g.toro("h_metal", 2.65, 0.18, (0, 0, z), seg=12, lados=5)
    # Cuatro pilonos con bobinas de cobre y arcos que abrazan el núcleo.
    for i in range(4):
        with g.grupo((0, 0, 0), (0, 0, 45 + 90 * i)):
            g.caja("h_blanco_liso", (1.8, 1.6, 9.5), (4.9, 0, 2.6), base=True, sup=(0.7, 0.8), desv=(-0.5, 0), bisel=0.12)
            for k in range(4):
                g.toro("cobre", 1.1 - k * 0.07, 0.2, (4.75 - k * 0.14, 0, 5.0 + k * 1.3), seg=10, lados=5)
            g.tubo("h_gris", [(4.2, 0, 12.0), (3.8, 0, 13.6), (2.6, 0, 14.6)], 0.4, lados=6)
            g.caja("h_neon", (0.14, 0.5, 4.5), (5.72, 0, 6.2), rot=(0, 5, 0))
            g.caja("h_naranja_liso", (2.0, 1.8, 0.7), (5.0, 0, 2.7), base=True, bisel=0.08)
        with g.grupo((0, 0, 0), (0, 0, 90 * i)):
            # Aletas de refrigeración y tuberías entre pilonos.
            for k in range(3):
                g.caja("h_metal", (0.14, 2.2, 1.8), (5.6 + k * 0.42, 0, 1.0), base=True)
            g.tubo("h_metal", [(4.2, -2.2, 2.4), (5.0, 0, 3.6), (4.2, 2.2, 2.4)], 0.28, lados=6)
    # Consola de control.
    g.caja("h_gris", (2.6, 1.4, 2.6), (0, -7.4, 0.6), base=True, sup=(1, 0.55), desv=(0, 0.25), bisel=0.08)
    g.caja("h_neon", (2.0, 0.08, 1.0), (0, -7.72, 2.7), rot=(-22, 0, 0))
    g.caja("h_neon_naranja", (0.5, 0.08, 0.3), (0.6, -8.0, 1.7), rot=(-22, 0, 0))
    g.ancla("Nucleo", (0, 0, 8.0))
    g.ancla("Consola", (0, -8.4, 0.6))


MODELOS = [
    ("armadura_hierro", "armaduras", 5000, armadura_hierro),
    ("armadura_acero", "armaduras", 5000, armadura_acero),
    ("casco_hierro", "armaduras", 5000, casco_hierro),
    ("casco_acero", "armaduras", 5000, casco_acero),
    ("plataforma_lanzamiento", "estructuras", 10000, plataforma_lanzamiento),
    ("torreta_defensa", "estructuras", 5000, torreta_defensa),
    ("generador_energia", "estructuras", 5000, generador_energia),
]
