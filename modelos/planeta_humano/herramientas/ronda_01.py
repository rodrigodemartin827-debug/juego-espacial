"""Ronda 1 · Zona residencial (modelos 1-10)."""

import math

from geometria import arco_pts, circulo
from registro import modelo


@modelo(1, "residencial", "edificio_mediano", (8, 8, 6))
def casa_pequena_a(m):
    # Losa y escalón de entrada
    m.caja((0, 0, 0.2), (8, 8, 0.4), "hormigon", bisel=0.06)
    m.caja((-1.4, -3.75, 0.47), (2.6, 0.5, 0.14), "rejilla")
    # Cuerpo: paredes blancas con zócalo oscuro y pilares de esquina
    m.caja((0, 0, 2.5), (7.2, 7.2, 4.2), "blanco")
    m.caja((0, 0, 0.75), (7.3, 7.3, 0.7), "oscuro_paneles")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.caja((sx * 3.6, sy * 3.6, 2.5), (0.5, 0.5, 4.3), "gris_liso", bisel=0.08)
    # Banda de acento y tira de neón bajo el alero
    m.caja((0, 0, 4.2), (7.26, 7.26, 0.22), "acento")
    m.caja((0, -3.64, 4.47), (6.6, 0.06, 0.07), "neon")
    m.caja((0, 3.64, 4.47), (6.6, 0.06, 0.07), "neon")
    # Tejado plano con alero y peto
    m.caja((0, 0, 4.78), (8, 8, 0.36), "gris", bisel=0.08)
    for sx in (-1, 1):
        m.caja((sx * 3.7, 0, 5.06), (0.2, 7.6, 0.2), "blanco_liso")
        m.caja((0, sx * 3.7, 5.06), (7.2, 0.2, 0.2), "blanco_liso")
    # Panel solar inclinado sobre soportes
    m.caja((0.9, 0.5, 5.52), (4.2, 3.4, 0.14), "panel_solar", rot=(14, 0, 0))
    m.caja((0.9, 0.5, 5.44), (4.4, 3.6, 0.1), "acero", rot=(14, 0, 0))
    for sx in (-1, 1):
        m.caja((0.9 + sx * 1.8, 1.9, 5.45), (0.14, 0.14, 0.95), "acero")
        m.caja((0.9 + sx * 1.8, -0.9, 5.15), (0.14, 0.14, 0.3), "acero")
    # Unidad de ventilación en el tejado
    m.caja((-2.6, 2.3, 5.3), (1.3, 1.3, 0.7), "gris_claro", bisel=0.06)
    m.cil((-2.6, 2.3, 5.68), 0.45, 0.1, "oscuro", seg=12)
    m.tubo((-2.6, 2.3, 5.72), 0.52, 0.12, 0.08, "acero", seg=12)
    # Puerta corredera (pieza aparte) con guía, marco y ventanuco
    m.marco((-1.4, -3.66, 1.95), 2.3, 3.0, 0.22, 0.3, "gris_liso")
    m.caja((-1.4, -3.6, 1.93), (1.86, 0.14, 2.56), "gris_claro", p="puerta")
    m.caja((-1.4, -3.69, 2.5), (1.0, 0.06, 0.9), "cristal")
    m.caja((-1.4, -3.68, 1.0), (1.5, 0.05, 0.08), "acento", p="puerta")
    m.caja((-0.6, -3.72, 3.56), (4.0, 0.14, 0.14), "acero")           # guía superior
    m.caja((-0.05, -3.74, 2.0), (0.12, 0.08, 0.5), "neon")              # indicador de la puerta
    # Marquesina sobre la puerta
    m.caja((-1.4, -4.0, 3.8), (2.9, 0.7, 0.1), "gris", rot=(-8, 0, 0))
    for sx in (-1, 1):
        m.barrido([(-1.4 + sx * 1.3, -3.62, 3.45), (-1.4 + sx * 1.3, -4.25, 3.78)], 0.04, "acero")
    # Ventanas con cristal cyan
    m.ventana((2.0, -3.62, 2.5), 2.2, 1.7, cruz=True)
    m.caja((2.0, -3.75, 1.6), (2.4, 0.3, 0.1), "gris_liso")              # alféizar
    for sx in (-1, 1):
        m.ventana((sx * 3.62, -1.4, 2.6), 1.8, 1.5, normal="x", sentido=sx)
        m.ventana((sx * 3.62, 1.6, 2.6), 1.8, 1.5, normal="x", sentido=sx)
    m.ventana((0, 3.62, 2.6), 3.0, 1.5, sentido=1, cruz=True)
    # Aplique junto a la puerta y bajante
    m.caja((0.35, -3.68, 3.1), (0.3, 0.14, 0.4), "oscuro")
    m.caja((0.35, -3.77, 3.05), (0.2, 0.06, 0.22), "neon")
    m.barrido([(3.45, -3.72, 4.6), (3.45, -3.72, 0.5), (3.45, -3.9, 0.42)], 0.07, "acero")


def _chaflan(a, b, c):
    """Rectángulo de semilados a, b con las esquinas a chaflán c."""
    return [(-a + c, -b), (a - c, -b), (a, -b + c), (a, b - c), (a - c, b), (-a + c, b), (-a, b - c), (-a, -b + c)]


@modelo(2, "residencial", "edificio_mediano", (8, 8, 6))
def casa_pequena_b(m):
    # Planta de esquinas achaflanadas, tejado a un agua y ventanas redondas tipo portillo de nave
    m.prisma(_chaflan(4.0, 4.0, 1.0), 0.0, 0.4, "hormigon", "xy")
    m.prisma(_chaflan(3.6, 3.6, 0.95), 0.4, 4.4, "blanco", "xy")
    m.prisma(_chaflan(3.68, 3.68, 0.97), 0.4, 1.1, "gris", "xy")
    m.prisma(_chaflan(3.66, 3.66, 0.96), 3.7, 3.95, "naranja_p", "xy")
    # Tejado inclinado (baja hacia el frente) con nervios y canalón
    m.prisma([(-4.1, 4.35), (4.1, 4.35), (4.1, 5.75), (4.1, 5.95), (-4.1, 4.75)], -4.0, 4.0, "gris", "yz")
    pend = math.degrees(math.atan2(1.2, 8.2))
    for x in (-2.7, -0.9, 0.9, 2.7):
        m.caja((x, 0, 5.4), (0.16, 8.1, 0.16), "blanco_liso", rot=(pend, 0, 0))
    m.barrido([(-4.0, -4.12, 4.62), (4.0, -4.12, 4.62)], 0.11, "acero", seg=8)
    m.barrido([(3.75, -4.12, 4.6), (3.75, -3.72, 4.3), (3.75, -3.72, 0.5)], 0.06, "acero")
    m.caja((0, -3.66, 4.22), (4.6, 0.06, 0.07), "neon")
    # Salida de ventilación curva
    m.barrido([(-2.3, 2.4, 5.5), (-2.3, 2.4, 5.95), (-2.3, 2.2, 6.0), (-2.3, 1.9, 5.95)], 0.22, "acero", seg=10)
    m.tubo((-2.3, 2.4, 5.62), 0.3, 0.12, 0.08, "gris_liso", seg=10)
    # Puerta de arco (pieza aparte) con marco
    arco = [(0.95 * math.cos(math.radians(a)), 2.45 + 0.95 * math.sin(math.radians(a))) for a in range(0, 181, 20)]
    hoja = [(0.95, 0.42)] + arco + [(-0.95, 0.42)]
    m.prisma(hoja, -3.72, -3.56, "gris_claro", "xz", c=(-1.6, 0, 0), p="puerta")
    m.prisma(arco_pts(1.2, 0.95, 0, 180, 9, 0, 2.45), -3.82, -3.5, "gris_liso", "xz", c=(-1.6, 0, 0))
    for sx in (-1, 1):
        m.caja((-1.6 + sx * 1.075, -3.66, 1.42), (0.25, 0.32, 2.06), "gris_liso")
    m.cil((-1.6, -3.74, 2.5), 0.42, 0.08, "cristal", eje="y", seg=16)
    m.tubo((-1.6, -3.75, 2.5), 0.5, 0.1, 0.09, "acero", eje="y", seg=16)
    m.caja((-1.6, -3.74, 1.5), (1.2, 0.05, 0.08), "naranja_p", p="puerta")
    m.caja((-1.6, -3.85, 0.47), (2.4, 0.6, 0.14), "rejilla")
    # Portillos: aro grueso, cristal, pernos y travesaño
    def portillo(c, r, eje, s):
        x, y, z = c
        m.tubo(c, r, 0.34, r * 0.2, "gris_liso", eje=eje, seg=20)
        d = (0, s * 0.05, 0) if eje == "y" else (s * 0.05, 0, 0)
        m.cil((x + d[0], y + d[1], z), r * 0.82, 0.08, "cristal", eje=eje, seg=20)
        for k in range(8):
            a = math.radians(22.5 + 45 * k)
            off = (r * 0.9 * math.cos(a), r * 0.9 * math.sin(a))
            if eje == "y":
                m.cil((x + off[0], y + s * 0.17, z + off[1]), 0.05, 0.06, "acero", eje="y", seg=6)
            else:
                m.cil((x + s * 0.17, y + off[0], z + off[1]), 0.05, 0.06, "acero", eje="x", seg=6)
    portillo((1.7, -3.6, 2.5), 1.0, "y", -1)
    for sx in (-1, 1):
        portillo((sx * 3.6, -0.6, 2.6), 0.8, "x", sx)
        portillo((sx * 3.6, 1.7, 2.6), 0.55, "x", sx)
    portillo((-1.5, 3.6, 2.6), 0.8, "y", 1)
    portillo((1.5, 3.6, 2.6), 0.8, "y", 1)
    # Aplique y jardinera junto a la puerta
    m.cil((-0.1, -3.68, 3.2), 0.16, 0.12, "oscuro", eje="y", seg=10)
    m.cil((-0.1, -3.76, 3.2), 0.1, 0.06, "neon", eje="y", seg=10)
    m.caja((3.0, -3.3, 0.72), (0.9, 0.9, 0.62), "gris_liso", rot=(0, 0, 45), bisel=0.05)
    m.cil((3.0, -3.3, 1.0), 0.36, 0.1, "tierra", seg=8)
    for k in range(9):
        a = k * 2.4
        m.hoja((3.0 + 0.12 * math.cos(a), -3.3 + 0.12 * math.sin(a), 1.02), 0.75, 0.24, "hoja",
               rot=(0, -50 - 5 * (k % 3), math.degrees(a)))


@modelo(3, "residencial", "edificio_mediano", (8, 8, 6))
def casa_pequena_c(m):
    # Casa con cuerpo trasero alto, cuerpo delantero bajo que hace de balcón, y antena en el tejado
    m.caja((0, 0, 0.2), (8, 8, 0.4), "hormigon", bisel=0.06)
    m.bloque((-3.6, -0.9, 0.4), (3.6, 3.6, 4.2), "blanco")
    m.bloque((-3.66, -0.96, 0.4), (3.66, 3.66, 1.0), "oscuro_paneles")
    m.bloque((-3.64, -0.94, 3.6), (3.64, 3.64, 3.8), "acento")
    m.bloque((-3.6, -3.6, 0.4), (0.4, -0.9, 2.3), "blanco")
    m.bloque((-3.66, -3.66, 0.4), (0.46, -0.9, 1.0), "oscuro_paneles")
    # Suelo del balcón y barandilla de cristal
    m.bloque((-3.8, -3.8, 2.3), (0.6, -0.9, 2.5), "gris", bisel=0.04)
    m.bloque((-3.4, -3.4, 2.5), (0.2, -1.0, 2.54), "rejilla")
    post = [(-3.7, -3.7), (-1.55, -3.7), (0.5, -3.7), (0.5, -2.3), (-3.7, -2.3)]
    for x, y in post:
        m.caja((x, y, 3.05), (0.12, 0.12, 1.1), "acero")
    m.barrido([(-3.7, -1.0, 3.6), (-3.7, -3.7, 3.6), (0.5, -3.7, 3.6), (0.5, -1.0, 3.6)], 0.07, "neon", seg=6)
    m.bloque((-3.6, -3.73, 2.62), (-1.65, -3.67, 3.48), "cristal")
    m.bloque((-1.45, -3.73, 2.62), (0.4, -3.67, 3.48), "cristal")
    m.bloque((-3.73, -3.6, 2.62), (-3.67, -1.05, 3.48), "cristal")
    m.bloque((0.47, -3.6, 2.62), (0.53, -1.05, 3.48), "cristal")
    # Puerta de cristal al balcón (arriba) y ventana del cuerpo bajo
    m.marco((-1.6, -0.94, 3.05), 2.4, 1.1, 0.14, 0.24, "gris_liso")
    m.caja((-1.6, -0.95, 3.05), (2.12, 0.07, 0.82), "cristal")
    m.caja((-1.6, -1.0, 3.05), (0.08, 0.1, 0.82), "gris_liso")
    m.ventana((-1.6, -3.62, 1.55), 2.6, 1.0, cruz=True)
    # Entrada a la derecha: escalones, puerta corredera y visera
    m.bloque((1.0, -1.9, 0.4), (3.3, -0.9, 0.52), "rejilla")
    m.bloque((1.2, -2.5, 0.4), (3.1, -1.9, 0.46), "hormigon")
    m.marco((2.15, -0.96, 1.85), 2.0, 2.9, 0.2, 0.28, "gris_liso")
    m.caja((2.15, -0.92, 1.83), (1.6, 0.12, 2.5), "gris_claro", p="puerta")
    m.caja((2.15, -1.0, 2.3), (0.5, 0.05, 1.2), "cristal")
    m.caja((2.75, -1.02, 1.9), (0.1, 0.07, 0.4), "neon")
    m.prisma([(-1.5, 3.3), (-0.9, 3.42), (-0.9, 3.52), (-1.5, 3.4)], 0.9, 3.4, "gris", "yz")
    # Ventanas laterales y trasera
    for sx in (-1, 1):
        m.ventana((sx * 3.62, 1.5, 2.3), 2.2, 1.5, normal="x", sentido=sx, cruz=True)
    m.ventana((-3.62, -2.2, 1.55), 1.4, 0.9, normal="x", sentido=-1)
    m.ventana((-1.4, 3.62, 2.3), 2.0, 1.5, sentido=1)
    m.ventana((1.8, 3.62, 2.3), 1.2, 1.5, sentido=1)
    # Tejado, peto y tira de luz
    m.bloque((-3.9, -1.2, 4.2), (3.9, 3.9, 4.5), "gris", bisel=0.07)
    m.caja((0, -1.22, 4.12), (6.6, 0.06, 0.07), "neon")
    m.bloque((-3.7, 3.5, 4.5), (3.7, 3.7, 4.7), "blanco_liso")
    # Antena: mástil arriostrado, travesaños, parábola pequeña y piloto
    m.cil((2.4, 2.2, 4.6), 0.3, 0.2, "gris_liso", seg=10)
    m.cil((2.4, 2.2, 5.25), 0.07, 1.3, "acero", seg=8)
    for k, (dx, dy) in enumerate(((0.9, 0), (-0.45, 0.78), (-0.45, -0.78))):
        m.barrido([(2.4 + dx, 2.2 + dy, 4.52), (2.4, 2.2, 5.4)], 0.02, "acero", seg=4)
    for z, l in ((5.25, 1.0), (5.5, 0.7), (5.75, 0.45)):
        m.cil((2.4, 2.2, z), 0.025, l, "acero", eje="x", seg=5)
    m.cupula((2.4, 2.0, 4.95), 0.42, "blanco_liso", grosor=0.05, seg=12, anillos=3, altura=0.4, rot=(110, 0, 0))
    m.barrido([(2.4, 2.0, 4.95), (2.4, 1.7, 5.06)], 0.02, "acero", seg=4)
    m.esfera((2.4, 1.68, 5.07), 0.05, "oscuro", seg=6, anillos=4)
    m.esfera((2.4, 2.2, 5.94), 0.06, "neon_rojo", seg=6, anillos=4)
    # Unidad de clima en el tejado
    m.caja((-2.2, 1.8, 4.8), (1.4, 1.0, 0.6), "gris_claro", bisel=0.05)
    for k in range(4):
        m.caja((-2.2, 1.29, 4.62 + 0.12 * k), (1.1, 0.04, 0.05), "oscuro")


def _escalera(m, x0, x1, y0, z0, y1, z1, n, mat="rejilla", baranda_x=None):
    """Escalera recta de zancas metálicas entre (y0, z0) y (y1, z1), ancho de x0 a x1."""
    dy, dz = (y1 - y0) / n, (z1 - z0) / n
    for i in range(n):
        m.bloque((x0 + 0.06, y0 + dy * i, z0 + dz * (i + 1) - 0.1), (x1 - 0.06, y0 + dy * (i + 1), z0 + dz * (i + 1)), mat)
    for x in (x0, x1):
        m.prisma([(y0, z0 - 0.05), (y1, z1 - 0.05), (y1, z1 - 0.45), (y0, z0 - 0.45)], x - 0.05, x + 0.05, "acero", "yz")
    if baranda_x is not None:
        x = baranda_x
        for i in range(0, n + 1, 3):
            m.cil((x, y0 + dy * i, z0 + dz * i + 0.55), 0.045, 1.1, "acero", seg=6)
        m.barrido([(x, y0, z0 + 1.1), (x, y1, z1 + 1.1)], 0.055, "acero", seg=6)
        m.barrido([(x, y0, z0 + 0.6), (x, y1, z1 + 0.6)], 0.035, "acero", seg=6)


@modelo(4, "residencial", "edificio_mediano", (10, 10, 10))
def casa_mediana_a(m):
    m.caja((0, 0, 0.2), (10, 10, 0.4), "hormigon", bisel=0.06)
    # Dos plantas con cinturón entre ellas
    m.bloque((-4.7, -3.5, 0.4), (3.0, 4.7, 4.6), "blanco")
    m.bloque((-4.76, -3.56, 0.4), (3.06, 4.76, 1.05), "oscuro_paneles")
    m.bloque((-4.8, -3.6, 4.6), (3.1, 4.8, 4.9), "gris", bisel=0.05)
    m.bloque((-4.7, -3.5, 4.9), (3.0, 4.7, 8.7), "blanco")
    m.bloque((-4.74, -3.54, 8.05), (3.04, 4.74, 8.3), "acento")
    for x in (-4.7, 3.0):
        for y in (-3.5, 4.7):
            m.caja((x, y, 4.55), (0.5, 0.5, 8.4), "gris_liso", bisel=0.08)
    # Tejado con peto, panel solar y depósito
    m.bloque((-5.0, -3.8, 8.7), (3.3, 5.0, 9.05), "gris", bisel=0.08)
    for a, b in (((-4.9, -3.7, 9.05), (3.2, -3.5, 9.3)), ((-4.9, 4.7, 9.05), (3.2, 4.9, 9.3)),
                 ((-4.9, -3.5, 9.05), (-4.7, 4.7, 9.3)), ((3.0, -3.5, 9.05), (3.2, 4.7, 9.3))):
        m.bloque(a, b, "blanco_liso")
    m.caja((-1.6, 1.6, 9.62), (4.2, 3.2, 0.12), "panel_solar", rot=(16, 0, 0))
    m.caja((-1.6, 1.6, 9.55), (4.4, 3.4, 0.08), "acero", rot=(16, 0, 0))
    for sx in (-1, 1):
        m.caja((-1.6 + sx * 1.9, 2.9, 9.5), (0.12, 0.12, 0.95), "acero")
    m.cil((1.7, -1.8, 9.55), 0.6, 1.0, "blanco_liso", seg=14)
    m.torno((1.7, -1.8, 10.05), [(0.6, 0), (0.5, 0.12), (0.0, 0.2)], "gris_liso", seg=14)
    m.barrido([(1.7, -1.2, 9.3), (1.7, -0.6, 9.3), (1.7, -0.6, 9.1)], 0.07, "acero")
    # Balcón del segundo piso en voladizo, con barandilla y ménsulas
    m.bloque((-4.5, -4.9, 4.62), (2.8, -3.5, 4.86), "gris", bisel=0.04)
    for x in (-4.2, -0.85, 2.5):
        m.prisma([(-4.8, 4.62), (-3.5, 4.62), (-3.5, 3.9)], x - 0.08, x + 0.08, "acero", "yz")
    m.barandilla((-4.4, -4.8, 4.86), (2.7, -4.8, 4.86), 1.1, postes=7, travesanos=2)
    m.barandilla((-4.4, -4.8, 4.86), (-4.4, -3.6, 4.86), 1.1, postes=2, travesanos=2)
    m.barandilla((2.7, -4.8, 4.86), (2.7, -3.6, 4.86), 1.1, postes=2, travesanos=2)
    m.caja((-0.85, -4.86, 4.72), (6.6, 0.06, 0.07), "neon")
    # Planta baja: puerta corredera, ventanas
    m.marco((-0.85, -3.58, 1.95), 2.4, 3.1, 0.22, 0.3, "gris_liso")
    m.caja((-0.85, -3.52, 1.93), (1.96, 0.14, 2.66), "gris_claro", p="puerta")
    m.caja((-0.85, -3.61, 2.5), (1.1, 0.06, 1.0), "cristal")
    m.caja((0.55, -3.64, 2.0), (0.12, 0.08, 0.5), "neon")
    m.caja((-0.85, -3.85, 0.47), (2.8, 0.6, 0.14), "rejilla")
    m.ventana((-3.2, -3.52, 2.5), 1.9, 1.8, cruz=True)
    m.ventana((1.6, -3.52, 2.5), 1.6, 1.8)
    # Segundo piso: puerta de cristal doble al balcón y ventanas
    m.marco((-0.85, -3.56, 6.25), 2.8, 2.7, 0.18, 0.26, "gris_liso")
    m.caja((-0.85, -3.55, 6.25), (2.44, 0.07, 2.34), "cristal")
    m.caja((-0.85, -3.62, 6.25), (0.1, 0.1, 2.34), "gris_liso")
    m.ventana((-3.4, -3.52, 6.6), 1.5, 1.6)
    m.ventana((1.7, -3.52, 6.6), 1.5, 1.6)
    for z in (2.5, 6.6):
        m.ventana((-4.72, -1.0, z), 2.0, 1.6, normal="x", sentido=-1, cruz=True)
        m.ventana((-4.72, 2.6, z), 2.0, 1.6, normal="x", sentido=-1, cruz=True)
        m.ventana((-2.6, 4.72, z), 2.2, 1.6, sentido=1, cruz=True)
        m.ventana((1.0, 4.72, z), 2.2, 1.6, sentido=1, cruz=True)
    m.ventana((3.02, -1.2, 2.5), 1.6, 1.6, normal="x", sentido=1)
    # Escalera exterior metálica por el lateral derecho hasta el rellano del segundo piso
    _escalera(m, 3.25, 4.75, -4.4, 0.4, 2.2, 4.9, 12, baranda_x=4.75)
    m.bloque((3.1, 2.2, 4.78), (4.8, 4.6, 4.9), "rejilla")
    m.bloque((3.1, 2.2, 4.62), (4.8, 4.6, 4.78), "acero")
    for y in (2.4, 4.4):
        m.cil((4.65, y, 2.5), 0.09, 4.3, "acero", seg=8)
    m.barandilla((4.75, 2.2, 4.9), (4.75, 4.6, 4.9), 1.1, postes=3, travesanos=2)
    m.barandilla((3.2, 4.55, 4.9), (4.75, 4.55, 4.9), 1.1, postes=2, travesanos=2)
    m.marco((3.04, 3.4, 6.35), 1.7, 2.9, 0.2, 0.26, "gris_liso", "x")
    m.caja((3.0, 3.4, 6.33), (0.14, 1.3, 2.5), "gris_claro", p="puerta_alta")
    m.caja((3.09, 3.4, 6.9), (0.06, 0.7, 0.8), "cristal")
    m.caja((3.1, 2.35, 7.3), (0.14, 0.3, 0.4), "oscuro")
    m.caja((3.19, 2.35, 7.25), (0.06, 0.2, 0.22), "neon")


@modelo(5, "residencial", "edificio_mediano", (10, 10, 10))
def casa_mediana_b(m):
    # Estilo industrial: estructura de acero vista, chapa, garaje lateral con persiana enrollable
    m.caja((0, 0, 0.2), (10, 10, 0.4), "hormigon", bisel=0.06)
    m.bloque((-4.7, -3.9, 0.4), (1.1, 4.5, 8.4), "gris")
    m.bloque((-4.76, -3.96, 0.4), (1.16, 4.56, 1.2), "oscuro_paneles")
    m.bloque((-4.74, -3.94, 4.3), (1.14, 4.54, 4.7), "oscuro")
    # Pilares y vigas en I vistos
    for x in (-4.7, -1.8, 1.1):
        for y in (-3.9, 4.5):
            m.caja((x, y, 4.4), (0.34, 0.34, 8.0), "hierro")
            m.caja((x, y + (0.13 if y < 0 else -0.13) * 0, 4.4), (0.5, 0.12, 8.0), "hierro")
    for y in (-3.98, 4.58):
        m.caja((-1.8, y, 8.25), (6.2, 0.14, 0.4), "hierro")
        m.barrido([(-4.6, y, 4.8), (-1.9, y, 8.0)], 0.06, "hierro", seg=5)
        m.barrido([(-1.7, y, 8.0), (1.0, y, 4.8)], 0.06, "hierro", seg=5)
    # Cubierta de chapa a un agua (baja hacia la izquierda) y chimeneas de extracción
    m.prisma([(-5.0, 8.4), (1.4, 8.4), (1.4, 9.3), (1.4, 9.45), (-5.0, 8.7)], -4.2, 4.8, "chapa", "xz")
    for y, h in ((-1.5, 1.0), (0.0, 1.3)):
        m.cil((0.3, y, 9.2 + h / 2), 0.26, h + 0.5, "acero", seg=10)
        m.torno((0.3, y, 9.45 + h), [(0.42, 0), (0.42, 0.08), (0.0, 0.3)], "hierro", seg=10)
    # Garaje lateral: persiana por lamas (pieza aparte), bolardos y terraza técnica
    m.bloque((1.1, -3.7, 0.4), (4.8, 3.2, 4.4), "gris")
    m.bloque((1.1, -3.76, 0.4), (4.86, 3.26, 0.9), "oscuro_paneles")
    m.marco((2.95, -3.74, 2.2), 3.3, 3.6, 0.25, 0.3, "hierro")
    for k in range(9):
        m.caja((2.95, -3.68, 0.6 + 0.35 * k), (2.8, 0.1, 0.31), "chapa", rot=(8, 0, 0), p="puerta_garaje")
    m.caja((2.95, -3.72, 3.95), (3.0, 0.3, 0.34), "oscuro", bisel=0.05)
    m.caja((2.95, -3.9, 4.2), (3.2, 0.06, 0.12), "rayas")
    for x in (1.35, 4.55):
        m.cil((x, -4.3, 0.85), 0.14, 0.9, "rayas", seg=10)
        m.esfera((x, -4.3, 1.3), 0.14, "amarillo_p", seg=10, anillos=5)
    m.bloque((1.1, -3.9, 4.4), (5.0, 3.4, 4.62), "oscuro", bisel=0.04)
    m.barandilla((4.9, -3.8, 4.62), (4.9, 3.3, 4.62), 0.9, mat="hierro", postes=6)
    m.barandilla((1.2, -3.8, 4.62), (4.9, -3.8, 4.62), 0.9, mat="hierro", postes=4)
    m.caja((3.2, 1.6, 5.1), (1.8, 1.4, 0.95), "gris_claro", bisel=0.05)
    m.cil((3.2, 1.6, 5.6), 0.5, 0.08, "oscuro", seg=12)
    m.tubo((3.2, 1.6, 5.62), 0.58, 0.1, 0.08, "acero", seg=12)
    m.barrido([(2.4, 1.6, 4.9), (1.5, 1.6, 4.9), (1.25, 1.6, 5.1), (1.25, 1.6, 7.0), (1.12, 1.6, 7.2)], 0.09,
              "cobre", seg=6)
    m.barrido([(2.4, 1.3, 4.8), (1.5, 1.3, 4.8), (1.3, 1.3, 4.95), (1.3, 1.3, 6.2), (1.12, 1.3, 6.4)], 0.07,
              "acero", seg=6)
    # Puerta principal con visera de chapa y lámpara industrial
    m.marco((-3.0, -3.98, 2.0), 2.2, 3.2, 0.22, 0.3, "hierro")
    m.caja((-3.0, -3.92, 1.98), (1.76, 0.14, 2.76), "oscuro_paneles", p="puerta")
    m.caja((-3.0, -4.01, 2.6), (0.9, 0.06, 0.7), "cristal")
    m.caja((-3.0, -4.3, 0.47), (2.6, 0.7, 0.14), "rejilla")
    m.prisma([(-4.9, 3.75), (-3.9, 3.95), (-3.9, 4.05), (-4.9, 3.85)], -4.3, -1.7, "chapa", "yz")
    m.barrido([(-1.5, -3.96, 3.6), (-1.5, -4.35, 3.75), (-1.5, -4.5, 3.6)], 0.035, "hierro", seg=5)
    m.torno((-1.5, -4.5, 3.3), [(0.3, 0), (0.12, 0.25), (0.05, 0.3)], "hierro", seg=10)
    m.cil((-1.5, -4.5, 3.29), 0.2, 0.06, "neon_amarillo", seg=10)
    # Ventanales de cuadrícula
    def cuadricula(c, an, al, normal="y", s=-1):
        m.ventana(c, an, al, normal=normal, sentido=s, marco="hierro")
        x, y, z = c
        for i in (-1, 1):
            if normal == "y":
                m.caja((x + i * an / 6, y + s * 0.08, z), (0.07, 0.1, al - 0.3), "hierro")
                m.caja((x, y + s * 0.08, z + i * al / 6), (an - 0.3, 0.1, 0.07), "hierro")
            else:
                m.caja((x + s * 0.08, y + i * an / 6, z), (0.1, 0.07, al - 0.3), "hierro")
                m.caja((x + s * 0.08, y, z + i * al / 6), (0.1, an - 0.3, 0.07), "hierro")
    cuadricula((-0.5, -3.92, 2.5), 2.0, 2.0)
    cuadricula((-1.8, -3.92, 6.4), 4.4, 2.4)
    cuadricula((-4.72, 0.3, 6.4), 4.0, 2.2, "x", -1)
    cuadricula((-4.72, 0.3, 2.6), 2.4, 1.8, "x", -1)
    cuadricula((-1.8, 4.52, 6.4), 3.6, 2.0, "y", 1)
    cuadricula((1.12, -1.0, 6.5), 2.4, 1.8, "x", 1)
    m.caja((-1.8, -3.97, 4.5), (4.6, 0.06, 0.08), "neon")


@modelo(6, "residencial", "edificio_mediano", (14, 12, 12))
def casa_grande(m):
    # Parcela con jardín delantero vallado
    m.caja((0, 0, 0.15), (14, 12, 0.3), "hormigon", bisel=0.05)
    m.bloque((-6.6, -5.6, 0.3), (-1.1, -2.5, 0.42), "cesped")
    m.bloque((1.1, -5.6, 0.3), (6.6, -2.5, 0.42), "cesped")
    for k in range(4):
        m.caja((0, -5.3 + 0.78 * k, 0.36), (1.7, 0.62, 0.12), "piedra_clara", bisel=0.03)
    R = m.rng
    for sx in (-1, 1):
        # Valla: postes, dos largueros y lamas
        xs = [sx * (1.25 + 1.07 * i) for i in range(6)]
        for x in xs:
            m.caja((x, -5.8, 0.95), (0.16, 0.16, 1.3), "blanco_liso", bisel=0.03)
            m.caja((x, -5.8, 1.63), (0.22, 0.22, 0.06), "gris_liso")
        m.caja((sx * 3.92, -5.8, 1.35), (5.4, 0.08, 0.1), "blanco_liso")
        m.caja((sx * 3.92, -5.8, 0.7), (5.4, 0.08, 0.1), "blanco_liso")
        for i in range(15):
            m.caja((sx * (1.5 + 0.345 * i), -5.8, 1.0), (0.1, 0.05, 0.9), "blanco_liso")
        for y in (-4.7, -3.6):
            m.caja((sx * 6.8, y, 0.95), (0.16, 0.16, 1.3), "blanco_liso", bisel=0.03)
        m.caja((sx * 6.8, -4.15, 1.35), (0.08, 3.3, 0.1), "blanco_liso")
        m.caja((sx * 6.8, -4.15, 0.7), (0.08, 3.3, 0.1), "blanco_liso")
        m.caja((sx * 1.25, -5.8, 1.72), (0.12, 0.12, 0.12), "neon")
        # Arbustos del jardín
        for (bx, by, br) in ((4.6, -4.2, 0.7), (2.6, -3.3, 0.5)):
            m.ico((sx * bx, by, 0.42 + br * 0.75), br, "hoja", sub=2, esc=(1, 1, 0.85), ruido=0.25,
                  semilla=bx + sx)
            for k in range(10):
                a, e = R.uniform(0, 6.28), R.uniform(0.2, 1.3)
                p = (sx * bx + br * math.cos(a) * math.cos(e), by + br * math.sin(a) * math.cos(e),
                     0.42 + br * 0.75 + br * 0.85 * math.sin(e))
                m.hoja(p, 0.4, 0.2, "hoja_clara", rot=(R.uniform(-30, 30), -math.degrees(e) * 0.6, math.degrees(a)))
    # Cuerpo principal de dos plantas y torreón central
    m.bloque((-6.4, -2.4, 0.3), (6.4, 5.6, 4.7), "blanco")
    m.bloque((-6.46, -2.46, 0.3), (6.46, 5.66, 1.0), "oscuro_paneles")
    m.bloque((-6.5, -2.5, 4.7), (6.5, 5.7, 5.0), "gris", bisel=0.05)
    m.bloque((-6.4, -2.4, 5.0), (6.4, 5.6, 8.9), "blanco")
    m.bloque((-6.44, -2.44, 8.3), (6.44, 5.64, 8.55), "acento")
    m.bloque((-6.7, -2.7, 8.9), (6.7, 5.9, 9.25), "gris", bisel=0.08)
    m.bloque((-2.2, -2.9, 0.3), (2.2, 2.0, 10.3), "blanco")
    m.bloque((-2.26, -2.96, 0.3), (2.26, -2.4, 1.0), "oscuro_paneles")
    m.bloque((-2.5, -3.2, 10.3), (2.5, 2.3, 10.6), "gris", bisel=0.08)
    m.bloque((-2.24, -2.94, 9.7), (2.24, 2.04, 9.9), "acento")
    for x in (-2.2, 2.2):
        m.caja((x, -2.9, 5.3), (0.4, 0.4, 10.0), "gris_liso", bisel=0.07)
    for x in (-6.4, 6.4):
        for y in (-2.4, 5.6):
            m.caja((x, y, 4.6), (0.5, 0.5, 8.6), "gris_liso", bisel=0.08)
    # Entrada: puerta doble corredera, visera con tira de luz
    m.marco((0, -2.98, 2.0), 3.0, 3.4, 0.24, 0.3, "gris_liso")
    for sx in (-1, 1):
        m.caja((sx * 0.64, -2.92, 1.98), (1.24, 0.14, 2.92), "gris_claro", p="puerta_izq" if sx < 0 else "puerta_der")
        m.caja((sx * 0.64, -3.01, 2.4), (0.7, 0.06, 1.4), "cristal")
    m.bloque((-2.0, -4.0, 3.85), (2.0, -2.9, 4.05), "gris", bisel=0.04)
    m.caja((0, -3.98, 3.82), (3.4, 0.06, 0.07), "neon")
    m.bloque((-1.7, -3.5, 0.3), (1.7, -2.9, 0.44), "rejilla")
    m.ventana((0, -2.92, 7.4), 2.6, 3.0, cruz=True)
    # Dos balcones en el segundo piso con barandilla de cristal
    for sx in (-1, 1):
        cx = sx * 4.3
        m.bloque((cx - 1.9, -3.7, 4.72), (cx + 1.9, -2.4, 4.95), "gris", bisel=0.04)
        for x in (cx - 1.8, cx, cx + 1.8):
            m.caja((x, -3.6, 5.5), (0.12, 0.12, 1.1), "acero")
        m.barrido([(cx - 1.8, -2.45, 6.05), (cx - 1.8, -3.6, 6.05), (cx + 1.8, -3.6, 6.05), (cx + 1.8, -2.45, 6.05)],
                  0.07, "acero", seg=6)
        m.bloque((cx - 1.72, -3.63, 5.05), (cx - 0.08, -3.57, 5.95), "cristal")
        m.bloque((cx + 0.08, -3.63, 5.05), (cx + 1.72, -3.57, 5.95), "cristal")
        m.bloque((cx - 1.83, -3.5, 5.05), (cx - 1.77, -2.5, 5.95), "cristal")
        m.bloque((cx + 1.77, -3.5, 5.05), (cx + 1.83, -2.5, 5.95), "cristal")
        m.caja((cx, -3.66, 4.8), (3.4, 0.06, 0.07), "neon")
        m.marco((cx, -2.44, 6.45), 2.6, 2.7, 0.18, 0.26, "gris_liso")
        m.caja((cx, -2.43, 6.45), (2.24, 0.07, 2.34), "cristal")
        m.caja((cx, -2.5, 6.45), (0.1, 0.1, 2.34), "gris_liso")
        m.ventana((cx, -2.42, 2.6), 2.8, 1.8, cruz=True)
        m.caja((cx, -2.56, 1.65), (3.0, 0.3, 0.1), "gris_liso")
        for z in (2.6, 6.6):
            m.ventana((sx * 6.42, 0.0, z), 2.0, 1.7, normal="x", sentido=sx, cruz=True)
            m.ventana((sx * 6.42, 3.4, z), 2.0, 1.7, normal="x", sentido=sx, cruz=True)
            m.ventana((cx, 5.62, z), 2.6, 1.7, sentido=1, cruz=True)
        m.ventana((0, 5.62, 2.6 if sx < 0 else 6.6), 2.2, 1.7, sentido=1)
    # Tejado: petos, paneles solares y antena parabólica sobre el torreón
    for a, b in (((-6.6, -2.6, 9.25), (-2.5, -2.4, 9.5)), ((2.5, -2.6, 9.25), (6.6, -2.4, 9.5)),
                 ((-6.6, 5.6, 9.25), (6.6, 5.8, 9.5)), ((-6.6, -2.4, 9.25), (-6.4, 5.6, 9.5)),
                 ((6.4, -2.4, 9.25), (6.6, 5.6, 9.5))):
        m.bloque(a, b, "blanco_liso")
    for sx in (-1, 1):
        m.caja((sx * 4.4, 2.2, 9.75), (3.2, 2.6, 0.12), "panel_solar", rot=(15, 0, 0))
        m.caja((sx * 4.4, 2.2, 9.68), (3.4, 2.8, 0.08), "acero", rot=(15, 0, 0))
        m.caja((sx * 4.4, 3.3, 9.7), (2.8, 0.12, 0.75), "acero")
    m.cil((0, -0.4, 10.75), 0.5, 0.3, "gris_liso", seg=12)
    m.cil((0, -0.4, 11.15), 0.12, 0.6, "acero", seg=8)
    m.caja((0, -0.4, 11.45), (0.3, 0.5, 0.3), "gris_liso", rot=(-35, 0, 0))
    m.cupula((0, -0.75, 11.55), 1.1, "blanco_liso", grosor=0.07, seg=18, anillos=4, altura=0.38, rot=(125, 0, 0))
    for a in (0, 120, 240):
        ra = math.radians(a)
        m.barrido([(0.9 * math.cos(ra), -0.95 - 0.5 * math.sin(ra) * 0.6, 11.95 + 0.75 * math.sin(ra)),
                   (0, -1.7, 12.25)], 0.025, "acero", seg=4)
    m.cil((0, -1.72, 12.26), 0.09, 0.22, "oscuro", seg=8, rot=(125, 0, 0))
    m.esfera((0, 1.2, 10.72), 0.09, "neon_rojo", seg=8, anillos=4)
    m.cil((0, 1.2, 10.63), 0.06, 0.1, "oscuro", seg=6)


@modelo(7, "residencial", "edificio_grande", (16, 10, 16))
def apartamento_bloque(m):
    m.caja((0, 0, 0.2), (16, 10, 0.4), "hormigon", bisel=0.06)
    H = 4.6  # altura de planta
    # Bloque de tres plantas
    m.bloque((-7.4, -2.8, 0.4), (6.0, 4.8, 14.2), "blanco")
    m.bloque((-7.46, -2.86, 0.4), (6.06, 4.86, 1.1), "oscuro_paneles")
    for x in (-7.4, -2.93, 1.53, 6.0):
        m.caja((x, -2.8, 7.3), (0.45, 0.45, 13.8), "gris_liso", bisel=0.07)
        m.caja((x, 4.8, 7.3), (0.45, 0.45, 13.8), "gris_liso", bisel=0.07)
    m.bloque((-7.7, -3.1, 14.2), (6.3, 5.1, 14.6), "gris", bisel=0.08)
    for a, b in (((-7.6, -3.0, 14.6), (6.2, -2.8, 14.9)), ((-7.6, 4.8, 14.6), (6.2, 5.0, 14.9)),
                 ((-7.6, -2.8, 14.6), (-7.4, 4.8, 14.9)), ((6.0, -2.8, 14.6), (6.2, 4.8, 14.9))):
        m.bloque(a, b, "blanco_liso")
    # Azotea: caseta de escalera, depósitos y climatización
    m.bloque((2.6, 1.6, 14.6), (5.4, 4.2, 15.9), "gris")
    m.bloque((2.4, 1.4, 15.82), (5.6, 4.4, 16.0), "oscuro", bisel=0.04)
    m.caja((2.56, 2.9, 15.2), (0.1, 1.0, 1.1), "gris_claro", p="puerta_azotea")
    for x in (-5.6, -3.9):
        m.cil((x, 2.6, 15.25), 0.7, 1.2, "blanco_liso", seg=14)
        m.torno((x, 2.6, 15.85), [(0.7, 0), (0.55, 0.12), (0, 0.2)], "gris_liso", seg=14)
    m.barrido([(-5.6, 1.9, 14.9), (-5.6, 1.5, 14.9), (-3.9, 1.5, 14.9), (-3.9, 1.9, 14.9)], 0.07, "acero")
    m.caja((-0.6, 2.4, 15.0), (2.2, 1.4, 0.8), "gris_claro", bisel=0.05)
    for x in (-1.1, -0.1):
        m.cil((x, 2.4, 15.42), 0.4, 0.08, "oscuro", seg=10)
    # Fachada: tres viviendas por planta; balcones corridos con separadores, barandilla y luz en cada piso
    centros = (-5.17, -0.7, 3.77)
    for piso in range(3):
        z0 = 0.4 + H * piso
        if piso > 0:
            m.bloque((-7.5, -4.5, z0 - 0.26), (6.1, -2.8, z0), "gris", bisel=0.04)
            m.caja((-0.7, -4.46, z0 - 0.3), (13.0, 0.06, 0.08), "neon")
            m.barandilla((-7.4, -4.4, z0), (6.0, -4.4, z0), 1.1, postes=13, travesanos=2)
            m.barandilla((-7.4, -4.4, z0), (-7.4, -2.9, z0), 1.1, postes=2, travesanos=2)
            m.barandilla((6.0, -4.4, z0), (6.0, -2.9, z0), 1.1, postes=2, travesanos=2)
            for x in (-2.93, 1.53):
                m.bloque((x - 0.05, -4.4, z0), (x + 0.05, -2.8, z0 + 2.2), "gris_claro")
        else:
            m.caja((-0.7, -2.84, 4.25), (13.0, 0.06, 0.08), "neon")
        for i, cx in enumerate(centros):
            if piso == 0 and i == 1:
                continue
            # puerta de cristal + ventana + aplique
            m.marco((cx - 0.9, -2.84, z0 + 1.55), 1.6, 2.9, 0.16, 0.24, "gris_liso")
            m.caja((cx - 0.9, -2.83, z0 + 1.55), (1.28, 0.07, 2.58), "cristal")
            m.ventana((cx + 1.0, -2.82, z0 + 2.0), 1.7, 1.6, cruz=True)
            m.caja((cx + 0.02, -2.86, z0 + 3.3), (0.22, 0.1, 0.3), "oscuro")
            m.caja((cx + 0.02, -2.93, z0 + 3.26), (0.14, 0.05, 0.16), "neon")
        # traseras y lateral izquierdo
        for cx in centros:
            m.ventana((cx, 4.82, z0 + 2.2), 2.4, 1.6, sentido=1, cruz=True)
        m.ventana((-7.42, 1.0, z0 + 2.2), 2.4, 1.6, normal="x", sentido=-1, cruz=True)
    # Portal central con visera, puerta doble y buzones
    m.marco((-0.7, -2.86, 2.1), 3.0, 3.4, 0.24, 0.3, "gris_liso")
    for sx in (-1, 1):
        m.caja((-0.7 + sx * 0.64, -2.8, 2.08), (1.24, 0.14, 2.92), "gris_claro", p="puerta_izq" if sx < 0 else "puerta_der")
        m.caja((-0.7 + sx * 0.64, -2.89, 2.4), (0.8, 0.06, 1.6), "cristal")
    m.bloque((-2.6, -3.7, 3.95), (1.2, -2.8, 4.1), "oscuro", bisel=0.03)
    m.bloque((-2.2, -3.4, 0.4), (0.8, -2.8, 0.52), "rejilla")
    m.caja((1.6, -2.9, 1.9), (1.0, 0.24, 1.2), "gris_liso", bisel=0.03)
    for i in range(3):
        for j in range(3):
            m.caja((1.3 + 0.3 * i, -3.04, 1.55 + 0.35 * j), (0.24, 0.04, 0.28), "oscuro")
    # Escalera de emergencia lateral (derecha): rellanos, tramos en zigzag y escala final
    for piso in (1, 2):
        z0 = 0.4 + H * piso
        m.bloque((6.1, -2.4, z0 - 0.12), (7.9, 4.4, z0), "rejilla")
        m.bloque((6.1, -2.4, z0 - 0.28), (7.9, 4.4, z0 - 0.12), "acero")
        m.barandilla((7.85, -2.4, z0), (7.85, 4.4, z0), 1.1, postes=6, travesanos=2)
        m.barandilla((6.2, -2.35, z0), (7.85, -2.35, z0), 1.1, postes=2, travesanos=2)
        m.barandilla((6.2, 4.35, z0), (7.85, 4.35, z0), 1.1, postes=2, travesanos=2)
        m.marco((6.04, 3.3, z0 + 1.5), 1.5, 2.8, 0.18, 0.24, "gris_liso", "x")
        m.caja((6.0, 3.3, z0 + 1.48), (0.14, 1.14, 2.44), "rojo_p", p=f"puerta_emergencia_{piso}")
        m.caja((6.1, 3.3, z0 + 3.15), (0.1, 0.9, 0.24), "neon_verde")
    _escalera(m, 6.9, 7.8, -1.9, 5.0, 2.6, 9.6, 12)
    for y in (-2.3, 4.3):
        m.cil((7.8, y, 4.9 + 2.3), 0.07, 4.6 + 4.2, "acero", seg=6)
    # Escala retráctil hasta el suelo
    for x in (6.35, 6.85):
        m.cil((x, -2.2, 2.7), 0.05, 4.4, "acero", seg=6)
    for k in range(11):
        m.cil((6.6, -2.2, 0.8 + 0.4 * k), 0.035, 0.5, "acero", eje="x", seg=5)


@modelo(8, "residencial", "prop", (1, 1, 8))
def farola_residencial(m):
    # Base atornillada, fuste cónico, brazo curvo y cabeza LED
    m.cil((0, 0, 0.06), 0.46, 0.12, "oscuro", seg=14)
    for k in range(6):
        a = math.radians(60 * k + 30)
        m.cil((0.36 * math.cos(a), 0.36 * math.sin(a), 0.15), 0.05, 0.08, "acero", seg=6)
    m.torno((0, 0, 0.12), [(0.3, 0), (0.3, 0.5), (0.24, 0.62), (0.17, 1.3), (0.15, 1.36), (0.11, 1.42)],
            "gris_liso", seg=14)
    m.caja((0, -0.27, 0.42), (0.2, 0.06, 0.34), "oscuro", bisel=0.01)
    m.cil((0, -0.305, 0.5), 0.02, 0.02, "neon", eje="y", seg=6)
    m.torno((0, 0, 1.5), [(0.11, 0), (0.085, 4.2), (0.075, 5.2)], "blanco_liso", seg=12)
    # Anillos: uno de acento luminoso y dos collarines
    m.tubo((0, 0, 3.0), 0.135, 0.12, 0.03, "neon", seg=12)
    for z in (2.9, 3.1, 5.6):
        m.tubo((0, 0, z), 0.14, 0.06, 0.04, "acero", seg=12)
    # Brazo curvo hacia el frente
    pts = [(0, 0, 6.7)]
    for i in range(1, 8):
        a = math.radians(90 * i / 7)
        pts.append((0, -0.42 * math.sin(a) * 0 - 0.36 * (1 - math.cos(a)), 6.7 + 0.75 * math.sin(a)))
    m.barrido(pts, [0.075, 0.072, 0.07, 0.068, 0.066, 0.064, 0.062, 0.06], "blanco_liso", seg=10)
    m.esfera((0, 0, 6.7), 0.1, "acero", seg=10, anillos=6)
    # Cabeza: carcasa aerodinámica con difusor LED por debajo y aletas de disipación
    m.prisma([(-0.5, 7.42), (0.42, 7.42), (0.5, 7.5), (0.5, 7.58), (0.36, 7.7), (-0.3, 7.7), (-0.5, 7.56)],
             -0.24, 0.24, "blanco_liso", "yz")
    m.caja((0, -0.02, 7.4), (0.36, 0.78, 0.07), "neon")
    m.caja((0, -0.02, 7.43), (0.44, 0.88, 0.04), "gris_liso")
    for k in range(5):
        m.caja((0, -0.28 + 0.14 * k, 7.74), (0.4, 0.04, 0.09), "gris_liso")
    m.cil((0, 0.36, 7.76), 0.05, 0.14, "oscuro", seg=8)
    m.esfera((0, 0.36, 7.86), 0.045, "neon", seg=8, anillos=4)


@modelo(9, "residencial", "prop", (4, 2, 2))
def banco_parque(m):
    # Dos costados de fundición con reposabrazos, tablones con grosor y tornillería
    perfil = [(-0.78, 0), (-0.6, 0), (-0.52, 0.72), (0.38, 0.72), (0.5, 0), (0.7, 0), (0.6, 0.84), (0.72, 1.15),
              (0.86, 1.95), (0.72, 1.97), (0.56, 1.2), (0.44, 1.02), (-0.5, 0.9), (-0.55, 1.22), (-0.3, 1.25),
              (-0.3, 1.36), (-0.82, 1.34), (-0.74, 0.86)]
    for x in (-1.85, 1.85):
        m.prisma(perfil, x - 0.07, x + 0.07, "hierro", "yz")
        m.caja((x, -0.69, 0.03), (0.3, 0.3, 0.06), "oscuro")
        m.caja((x, 0.6, 0.03), (0.3, 0.3, 0.06), "oscuro")
        m.caja((x, -0.56, 1.38), (0.22, 0.56, 0.06), "madera_oscura", bisel=0.015)
    # Asiento: 4 tablones; respaldo: 3 tablones inclinados
    for i, y in enumerate((-0.42, -0.14, 0.14, 0.4)):
        m.caja((0, y, 0.96 + (0.02 if i == 3 else 0)), (3.96, 0.24, 0.1), "madera", bisel=0.02)
        for x in (-1.85, 1.85):
            m.cil((x, y, 1.015), 0.035, 0.03, "acero", seg=6)
    inc = math.degrees(math.atan2(0.14, 0.78))
    for i, (y, z) in enumerate(((0.62, 1.3), (0.685, 1.58), (0.75, 1.86))):
        m.caja((0, y, z), (3.96, 0.09, 0.22), "madera", rot=(-inc, 0, 0), bisel=0.02)
        for x in (-1.85, 1.85):
            m.cil((x, y - 0.05, z), 0.035, 0.03, "acero", eje="y", seg=6, rot=(-inc, 0, 0))
    # Tirantes de refuerzo bajo el asiento
    m.cil((0, 0.3, 0.6), 0.04, 3.7, "hierro", eje="x", seg=6)
    m.barrido([(-1.8, -0.5, 0.75), (0, 0.3, 0.6), (1.8, -0.5, 0.75)], 0.03, "hierro", seg=5)
    # Placa conmemorativa con piloto
    m.caja((0, 0.69, 1.86), (0.5, 0.03, 0.12), "acero", rot=(-inc, 0, 0))
    m.caja((1.85, -0.83, 1.3), (0.06, 0.03, 0.04), "neon")
    m.caja((-1.85, -0.83, 1.3), (0.06, 0.03, 0.04), "neon")


@modelo(10, "residencial", "prop", (6, 6, 3))
def fuente_plaza(m):
    # Vaso de piedra con grosor, pedestal torneado, taza superior, agua y chorros
    m.torno((0, 0, 0), [(3.0, 0), (3.0, 0.18), (2.9, 0.26), (2.9, 0.72), (3.0, 0.8), (3.0, 0.95), (2.62, 0.95),
                        (2.55, 0.3), (0, 0.3)], "piedra_clara", seg=20)
    m.cil((0, 0, 0.62), 2.57, 0.1, "agua", seg=20)
    for k in range(8):
        a = math.radians(360 * k / 8)
        m.caja((2.96 * math.cos(a), 2.96 * math.sin(a), 0.5), (0.1, 0.5, 0.34), "piedra", rot=(0, 0, math.degrees(a)))
    m.tubo((0, 0, 0.84), 3.02, 0.05, 0.05, "neon", seg=20)
    m.torno((0, 0, 0.3), [(0.75, 0), (0.75, 0.25), (0.5, 0.4), (0.34, 0.95), (0.3, 1.2), (0.42, 1.32),
                          (0.42, 1.4), (0.0, 1.4)], "piedra_clara", seg=14)
    m.torno((0, 0, 1.62), [(0.3, 0), (0.9, 0.12), (1.3, 0.36), (1.34, 0.5), (1.2, 0.5), (1.1, 0.34), (0.2, 0.22),
                           (0.0, 0.22)], "piedra_clara", seg=14)
    m.cil((0, 0, 2.02), 1.14, 0.08, "agua", seg=14)
    m.torno((0, 0, 1.84), [(0.2, 0), (0.16, 0.5), (0.24, 0.62), (0.12, 0.72), (0.0, 0.74)], "bronce", seg=10)
    m.tubo((0, 0, 1.66), 0.5, 0.05, 0.05, "neon", seg=12)
    # Chorro central y seis arcos de agua que caen de la taza al vaso
    m.barrido([(0, 0, 2.55), (0, 0, 2.8), (0, 0, 3.0)], [0.07, 0.05, 0.015], "agua", seg=6)
    m.esfera((0, 0, 2.93), 0.11, "agua", seg=8, anillos=5, esc=(1, 1, 0.6))
    for k in range(6):
        a = math.radians(60 * k + 30)
        ca, sa = math.cos(a), math.sin(a)
        pts, rs = [], []
        for i in range(6):
            t = i / 5
            r = 1.28 + 0.75 * t
            z = 2.1 + 0.25 * math.sin(t * 1.2) - 1.55 * t * t
            pts.append((r * ca, r * sa, z))
            rs.append(0.07 - 0.03 * t)
        m.barrido(pts, rs, "agua", seg=5)
        m.cil((1.3 * ca, 1.3 * sa, 2.1), 0.07, 0.14, "bronce", eje="x", seg=6, rot=(0, 0, math.degrees(a)))
        m.torno((2.03 * ca, 2.03 * sa, 0.66), [(0.0, 0), (0.22, 0.0), (0.26, 0.03), (0.0, 0.06)], "agua", seg=8)
    m.anclaje("particulas_agua", (0, 0, 3.0))
