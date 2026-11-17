"""Ronda 11 · Edificios especiales (modelos 101-105)."""

import math

from geometria import arco_pts
from registro import modelo


@modelo(101, "especiales", "edificio_mediano", (6, 6, 6))
def estacion_escudos(m):
    # Base octogonal, cúpula tecnológica con nervios y lucernas, emisor central con rayo vertical y cuatro pilones
    oct8 = [(3.0 * math.cos(math.radians(45 * k + 22.5)), 3.0 * math.sin(math.radians(45 * k + 22.5))) for k in range(8)]
    m.prisma(oct8, 0.0, 0.3, "oscuro", "xy")
    m.prisma([(x * 0.9, y * 0.9) for x, y in oct8], 0.3, 0.7, "gris", "xy")
    m.torno((0, 0, 0.66), [(2.72, 0), (2.72, 0.06)], "neon", seg=8, rot=(0, 0, 22.5))
    m.cupula((0, 0, 0.7), 2.3, "blanco_liso", grosor=0.14, seg=16, anillos=5, altura=0.8)
    for k in range(8):
        a = math.radians(45 * k)
        pts = [(2.34 * math.cos(a) * math.cos(math.radians(e)), 2.34 * math.sin(a) * math.cos(math.radians(e)),
                0.7 + 2.34 * 0.8 * math.sin(math.radians(e))) for e in (0, 20, 40, 60, 76)]
        m.barrido(pts, 0.08, "gris_liso", seg=4)
        b = math.radians(45 * k + 22.5)
        e = math.radians(34)
        m.caja((2.33 * math.cos(b) * math.cos(e), 2.33 * math.sin(b) * math.cos(e), 0.7 + 2.33 * 0.8 * math.sin(e)),
               (0.08, 0.6, 0.5), "neon", rot=(0, -50, 45 * k + 22.5))
    m.tubo((0, 0, 1.6), 2.2, 0.12, 0.08, "acento", seg=16) if False else None
    # Emisor: collar, bobinas y núcleo
    m.cil((0, 0, 2.6), 0.7, 0.3, "oscuro", seg=14)
    m.torno((0, 0, 2.7), [(0.6, 0), (0.42, 0.3), (0.3, 0.9), (0.36, 1.0), (0.36, 1.2), (0.2, 1.2), (0.2, 1.0), (0, 1.0)], "gris_liso",
            seg=12)
    for z in (3.0, 3.25, 3.5):
        m.tubo((0, 0, z), 0.5 - (z - 3.0) * 0.2, 0.1, 0.08, "cobre", seg=12)
    m.esfera((0, 0, 3.75), 0.2, "neon_blanco", seg=10, anillos=6)
    # Rayo de energía vertical y anillos que suben (piezas de neón aparte, para animarlas)
    m.torno((0, 0, 3.8), [(0.16, 0), (0.11, 1.2), (0.07, 2.2), (0.0, 2.2)], "neon", seg=8, p="rayo_neon")
    for i, z in enumerate((4.3, 4.9, 5.5)):
        m.toro((0, 0, z), 0.5 - 0.1 * i, 0.035, "neon", seg=18, seg2=5, p="anillos_neon")
    m.anclaje("rayo", (0, 0, 6.0))
    # Cuatro pilones con condensador y arco de energía hacia el emisor
    for k in range(4):
        a = math.radians(90 * k + 45)
        x, y = 2.35 * math.cos(a), 2.35 * math.sin(a)
        m.torno((x, y, 0.3), [(0.34, 0), (0.3, 0.3), (0.16, 0.6), (0.12, 2.6), (0.2, 2.75)], "gris_liso", seg=8)
        for z in (1.4, 1.75, 2.1):
            m.tubo((x, y, z), 0.2, 0.1, 0.06, "oscuro", seg=8)
        m.esfera((x, y, 3.2), 0.2, "neon", seg=8, anillos=5)
        pts = []
        for i in range(6):
            t = i / 5
            pts.append((x * (1 - t), y * (1 - t), 3.2 + 0.55 * t + 0.5 * math.sin(math.pi * t)))
        m.barrido(pts, 0.03, "neon", seg=4, p="arcos_neon")
    # Puerta de mantenimiento y consola
    m.prisma(arco_pts(0.75, 0.6, 0, 180, 6, 0, 1.2, 1.0, 1.0), -2.42, -2.2, "gris_liso", "xz")
    m.bloque((-0.75, -2.42, 0.7), (-0.6, -2.2, 1.2), "gris_liso")
    m.bloque((0.6, -2.42, 0.7), (0.75, -2.2, 1.2), "gris_liso")
    m.bloque((-0.6, -2.36, 0.7), (0.6, -2.24, 1.2), "oscuro_paneles", p="puerta")
    m.prisma([(0.6, 1.2)] + [(0.6 * math.cos(math.radians(a)), 1.2 + 0.6 * math.sin(math.radians(a))) for a in range(20, 180, 20)]
             + [(-0.6, 1.2)], -2.36, -2.24, "oscuro_paneles", "xz", p="puerta")
    m.caja((1.3, -2.45, 1.0), (0.4, 0.2, 0.6), "gris_claro", bisel=0.03)
    m.caja((1.3, -2.56, 1.08), (0.26, 0.02, 0.2), "neon", p="pantalla_neon")


@modelo(102, "especiales", "edificio_mediano", (4, 4, 12))
def deposito_agua(m):
    # Torre de agua: esfera metálica con cinturones, seis patas con arriostrado, tubo central, pasarela y escalerilla
    m.cil((0, 0, 0.12), 2.0, 0.24, "hormigon", seg=20)
    zc, R = 9.6, 1.95
    m.esfera((0, 0, zc), R, "blanco_liso", seg=22, anillos=14)
    m.tubo((0, 0, zc), R + 0.04, 0.3, 0.06, "acento", seg=22)
    for dz in (-1.0, 1.0):
        r = math.sqrt(R * R - dz * dz)
        m.tubo((0, 0, zc + dz), r + 0.03, 0.08, 0.05, "gris_liso", seg=22)
    m.torno((0, 0, zc + R - 0.12), [(0.7, 0), (0.6, 0.12), (0.25, 0.22), (0.25, 0.36), (0, 0.36)], "gris_liso", seg=12)
    m.cil((0, 0, zc + R + 0.45), 0.03, 0.5, "acero", seg=4)
    m.esfera((0, 0, zc + R + 0.72), 0.08, "neon_rojo", seg=6, anillos=4)
    m.texto("AGUA", (0, -R - 0.02, zc + 0.55), 0.4, 0.05, "acento") if False else None
    for k in range(6):
        a = math.radians(60 * k + 30)
        ca, sa = math.cos(a), math.sin(a)
        m.barrido([(1.75 * ca, 1.75 * sa, 0.24), (1.25 * ca, 1.25 * sa, zc - 1.45)], 0.1, "gris_liso", seg=6)
        m.caja((1.75 * ca, 1.75 * sa, 0.3), (0.4, 0.4, 0.14), "oscuro", rot=(0, 0, 60 * k + 30))
        b = math.radians(60 * (k + 1) + 30)
        for (z0, z1) in ((0.6, 3.0), (3.0, 5.6), (5.6, 8.0)):
            def P(ang, z):
                rr = 1.75 - 0.5 * (z - 0.24) / (zc - 1.69)
                return (rr * math.cos(ang), rr * math.sin(ang), z)
            m.barrido([P(a, z1), P(b, z1)], 0.04, "gris_liso", seg=4)
            m.barrido([P(a, z0), P(b, z1)] if (k + int(z0)) % 2 else [P(b, z0), P(a, z1)], 0.03, "acero", seg=4)
    # Tubo central de subida con bridas, válvula y codo
    m.cil((0, 0, 4.1), 0.26, 7.6, "acero", seg=12)
    for z in (1.2, 3.4, 5.6, 7.6):
        m.tubo((0, 0, z), 0.33, 0.1, 0.07, "hierro", seg=12)
    m.caja((0, 0, 1.9), (0.7, 0.7, 0.5), "azul_p", bisel=0.06)
    m.cil((0, -0.5, 1.9), 0.04, 0.3, "acero", eje="y", seg=5)
    m.tubo((0, -0.66, 1.9), 0.22, 0.05, 0.04, "rojo_p", eje="y", seg=12)
    m.barrido([(0, 0, 0.7), (0.5, 0, 0.5), (1.2, 0, 0.45), (1.9, 0, 0.45)], 0.16, "acero", seg=8)
    m.cil((1.95, 0, 0.45), 0.24, 0.08, "hierro", eje="x", seg=10)
    # Pasarela anular bajo la esfera con barandilla
    zp = zc - 1.75
    m.tubo((0, 0, zp), 2.0, 0.06, 0.7, "rejilla", seg=18)
    for k in range(12):
        a = math.radians(30 * k)
        m.cil((1.95 * math.cos(a), 1.95 * math.sin(a), zp + 0.5), 0.03, 1.0, "acero", seg=5)
    m.tubo((0, 0, zp + 1.0), 1.98, 0.06, 0.06, "acero", seg=18)
    m.tubo((0, 0, zp + 0.5), 1.97, 0.04, 0.04, "acero", seg=18)
    m.tubo((0, 0, zp - 0.05), 2.02, 0.05, 0.03, "neon", seg=18)
    # Escalerilla con aros desde el suelo hasta la pasarela
    for s in (-1, 1):
        m.barrido([(s * 0.25, -1.85, 0.24), (s * 0.25, -1.98, zp + 1.0)], 0.035, "acero", seg=5)
    for k in range(20):
        z = 0.6 + 0.385 * k
        m.cil((0, -1.85 - 0.13 * (z / zp), z), 0.022, 0.5, "acero", eje="x", seg=4)
    for k in range(5):
        z = 2.6 + 1.2 * k
        y0 = -1.85 - 0.13 * (z / zp)
        m.barrido([(-0.25, y0, z), (-0.36, y0 - 0.3, z), (-0.2, y0 - 0.6, z), (0.2, y0 - 0.6, z), (0.36, y0 - 0.3, z), (0.25, y0, z)],
                  0.018, "amarillo_p", seg=4)
    # Indicador de nivel luminoso en la esfera
    m.caja((0, -R - 0.02, zc - 0.2), (0.16, 0.06, 1.6), "oscuro")
    m.caja((0, -R - 0.06, zc - 0.4), (0.08, 0.03, 1.0), "neon")


@modelo(103, "especiales", "edificio_mediano", (6, 6, 10))
def estacion_comunicaciones(m):
    # Caseta técnica, pedestal con horquilla y antena parabólica gigante con alimentador, contrapeso y antenas auxiliares
    m.caja((0, 0, 0.15), (6.0, 6.0, 0.3), "hormigon", bisel=0.05)
    m.bloque((-2.8, 0.2, 0.3), (1.0, 2.8, 2.9), "blanco")
    m.bloque((-2.86, 0.14, 0.3), (1.06, 2.86, 0.9), "oscuro_paneles")
    m.bloque((-3.0, 0.0, 2.9), (1.2, 3.0, 3.15), "gris", bisel=0.06)
    m.bloque((-2.84, 0.16, 2.4), (1.04, 2.84, 2.58), "acento")
    m.marco((-0.9, 0.14, 1.5), 1.3, 2.3, 0.14, 0.2, "gris_liso")
    m.caja((-0.9, 0.2, 1.47), (1.02, 0.1, 2.0), "gris_claro", p="puerta")
    m.caja((-0.9, 0.13, 1.9), (0.5, 0.05, 0.6), "cristal")
    m.ventana((-2.1, 0.16, 1.8), 0.9, 0.9)
    m.ventana((-2.82, 1.5, 1.8), 1.4, 1.0, normal="x", sentido=-1)
    m.caja((0.4, 0.1, 1.6), (0.5, 0.14, 0.8), "oscuro", bisel=0.02)
    m.caja((0.4, 0.02, 1.7), (0.36, 0.02, 0.3), "neon", p="pantalla_neon")
    m.caja((-0.9, 0.08, 2.75), (1.2, 0.05, 0.06), "neon")
    m.caja((-1.6, 1.6, 3.5), (1.4, 1.1, 0.7), "gris_claro", bisel=0.05)
    m.cil((-1.6, 1.6, 3.88), 0.4, 0.08, "oscuro", seg=10)
    # Pedestal y horquilla de la parabólica
    m.torno((0.4, -1.2, 0.3), [(1.3, 0), (1.3, 0.4), (0.9, 0.7), (0.7, 4.9), (0.9, 5.1), (0.9, 5.4), (0, 5.4)], "blanco_liso", seg=14)
    m.tubo((0.4, -1.2, 0.75), 1.32, 0.1, 0.05, "rayas", seg=14)
    m.tubo((0.4, -1.2, 5.6), 0.95, 0.14, 0.1, "neon", seg=14)
    G = "antena"
    m.cil((0.4, -1.2, 5.9), 0.85, 0.4, "gris_liso", seg=14, p=G)
    for s in (-1, 1):
        m.prisma([(-0.5, 0), (0.5, 0), (0.3, 1.7), (-0.3, 1.7)], -0.12, 0.12, "gris", "yz", c=(0.4 + s * 0.95, -1.2, 6.0), p=G)
    cx, cy, cz = 0.4, -1.2, 7.6
    m.cil((cx, cy, cz), 0.2, 2.2, "acero", eje="x", seg=10, p=G)
    inc = 48
    from mathutils import Euler, Vector
    E = Euler((math.radians(inc), 0, 0), "XYZ").to_matrix()
    def P(x, y, z):
        v = E @ Vector((x, y, z))
        return (cx + v.x, cy + v.y, cz + v.z)
    # Plato: casquete con grosor, aro, nervios traseros, trípode y alimentador
    m.cupula(P(0, 0, -0.2), 2.55, "blanco_liso", grosor=0.08, seg=24, anillos=5, altura=0.32, rot=(inc + 180, 0, 0), p=G)
    m.tubo(P(0, 0, -0.2), 2.58, 0.1, 0.07, "gris_liso", seg=24, rot=(inc, 0, 0), p=G)
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        m.barrido([P(0.3 * math.cos(a), 0.3 * math.sin(a), -1.2), P(1.4 * math.cos(a), 1.4 * math.sin(a), -0.9),
                   P(2.5 * math.cos(a), 2.5 * math.sin(a), -0.28)], 0.05, "gris_liso", seg=4, p=G)
    m.cil(P(0, 0, -1.05), 0.5, 0.5, "gris", seg=12, rot=(inc, 0, 0), p=G)
    for k in range(3):
        a = math.radians(120 * k + 90)
        m.barrido([P(1.9 * math.cos(a), 1.9 * math.sin(a), -0.62), P(0.12 * math.cos(a), 0.12 * math.sin(a), 1.75)], 0.04, "acero",
                  seg=4, p=G)
    m.cil(P(0, 0, 1.75), 0.2, 0.4, "oscuro", seg=10, rot=(inc, 0, 0), p=G)
    m.cil(P(0, 0, 1.52), 0.14, 0.06, "neon", seg=10, rot=(inc, 0, 0))
    m.caja(P(0, 0, -1.9), (1.0, 0.8, 0.9), "hierro", rot=(inc, 0, 0), bisel=0.06, p=G)             # contrapeso
    m.barrido([P(0, 0.3, -1.1), P(0.4, 0.4, -0.2), (cx + 0.7, cy + 0.3, 6.1)], 0.04, "goma", seg=5)
    # Mástil auxiliar con antenas de panel y baliza; pequeña parabólica en la caseta
    m.cil((-2.3, -2.2, 3.3), 0.09, 6.0, "acero", seg=8)
    m.caja((-2.3, -2.2, 0.4), (0.6, 0.6, 0.2), "oscuro", bisel=0.04)
    for k, z in enumerate((4.2, 5.2)):
        for a in (0, 120, 240):
            ra = math.radians(a + 40 * k)
            m.caja((-2.3 + 0.2 * math.cos(ra), -2.2 + 0.2 * math.sin(ra), z), (0.1, 0.3, 0.8), "blanco_liso", rot=(0, 0, a + 40 * k))
    m.esfera((-2.3, -2.2, 6.4), 0.1, "neon_rojo", seg=8, anillos=5)
    for (dx, dy) in ((1.4, 0), (-0.7, 1.2), (-0.7, -1.2)):
        m.barrido([(-2.3, -2.2, 5.6), (-2.3 + dx * 0.5, -2.2 + dy * 0.5, 0.32)], 0.012, "acero", seg=3)
    m.cupula((0.3, 2.0, 3.6), 0.6, "blanco_liso", grosor=0.05, seg=12, anillos=3, altura=0.36, rot=(-110, 0, 0))
    m.cil((0.3, 2.2, 3.4), 0.06, 0.5, "acero", seg=6)
    # Escalones de acceso
    for k in range(2):
        m.caja((-0.9, -0.2 - 0.3 * k, 0.5 - 0.1 * k), (1.5, 0.32, 0.1), "rejilla")


@modelo(104, "especiales", "edificio_mediano", (3, 3, 8))
def monumento_fundadores(m):
    # Pedestal escalonado de piedra con placa, y figura heroica de bronce que alza un astro luminoso
    for k, (l, h) in enumerate(((3.0, 0.3), (2.6, 0.3), (2.2, 0.3))):
        m.caja((0, 0, 0.15 + 0.3 * k), (l, l, h), "piedra_clara", bisel=0.04)
    m.caja((0, 0, 2.0), (1.6, 1.6, 2.2), "piedra", bisel=0.06)
    m.caja((0, 0, 1.0), (1.84, 1.84, 0.24), "piedra_clara", bisel=0.04)
    m.caja((0, 0, 3.15), (1.9, 1.9, 0.2), "piedra_clara", bisel=0.05)
    m.caja((0, -0.82, 2.1), (1.1, 0.06, 1.2), "bronce", bisel=0.02)
    m.texto("FUNDADORES", (0, -0.86, 2.5), 0.11, 0.02, "oro", res=2)
    for k in range(4):
        m.caja((0, -0.86, 2.25 - 0.12 * k), (0.8 - 0.1 * (k % 2), 0.02, 0.04), "oro")
    m.caja((0, -0.86, 1.62), (0.9, 0.02, 0.04), "neon")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.torno((sx * 1.2, sy * 1.2, 0.6), [(0.14, 0), (0.1, 0.05), (0.08, 0.3), (0.13, 0.36)], "bronce", seg=8)
            m.esfera((sx * 1.2, sy * 1.2, 1.04), 0.1, "neon", seg=8, anillos=5)
    B = "bronce"
    z0 = 3.25
    m.caja((0, 0, z0 + 0.06), (1.3, 1.1, 0.12), B, bisel=0.03)
    # Piernas (una adelantada), botas
    for s, ady in ((-1, -0.12), (1, 0.14)):
        x = s * 0.24
        m.caja((x, ady - 0.08, z0 + 0.22), (0.26, 0.5, 0.2), B, bisel=0.05)
        m.barrido([(x, ady, z0 + 0.3), (x * 0.95, ady * 0.6, z0 + 1.1), (x * 0.8, 0.02, z0 + 2.0)], [0.15, 0.17, 0.2], B, seg=8)
        m.esfera((x * 0.95, ady * 0.6 - 0.04, z0 + 1.12), 0.17, B, seg=8, anillos=5)
    # Cadera, cinturón, torso, hombros
    m.torno((0, 0.02, z0 + 1.9), [(0.3, 0), (0.36, 0.2), (0.32, 0.45), (0.0, 0.45)], B, seg=10)
    m.tubo((0, 0.02, z0 + 2.3), 0.35, 0.12, 0.05, "oro", seg=10)
    m.torno((0, 0.02, z0 + 2.35), [(0.3, 0), (0.34, 0.3), (0.46, 0.8), (0.4, 1.02), (0.16, 1.12), (0.0, 1.12)], B, seg=10)
    m.caja((0, -0.34, z0 + 3.05), (0.5, 0.1, 0.4), B, bisel=0.04)
    m.cil((0, -0.4, z0 + 3.08), 0.1, 0.04, "neon", eje="y", seg=10)
    # Brazo derecho alzado con el astro; brazo izquierdo sujeta el casco contra la cadera
    hd, hi = (0.52, 0.02, z0 + 3.3), (-0.52, 0.02, z0 + 3.3)
    m.esfera(hd, 0.2, B, seg=8, anillos=5)
    m.esfera(hi, 0.2, B, seg=8, anillos=5)
    m.barrido([hd, (0.78, -0.06, z0 + 3.85), (0.7, -0.14, z0 + 4.45)], [0.14, 0.12, 0.09], B, seg=7)
    m.esfera((0.7, -0.14, z0 + 4.52), 0.11, B, seg=7, anillos=5)
    m.esfera((0.7, -0.14, z0 + 4.78), 0.2, "neon", seg=12, anillos=8, p="astro_neon")
    m.toro((0.7, -0.14, z0 + 4.78), 0.32, 0.02, "oro", seg=18, seg2=4, rot=(25, 15, 0))
    m.barrido([hi, (-0.68, -0.08, z0 + 2.75), (-0.5, -0.26, z0 + 2.3)], [0.14, 0.12, 0.09], B, seg=7)
    m.torno((-0.42, -0.36, z0 + 2.12), [(0.17, 0), (0.22, 0.14), (0.2, 0.32), (0.0, 0.42)], B, seg=8, rot=(20, 0, 0))
    m.caja((-0.42, -0.56, z0 + 2.3), (0.26, 0.04, 0.08), "cristal_oscuro")
    # Cuello y cabeza mirando al astro; capa con vuelo
    m.cil((0, 0.02, z0 + 3.55), 0.09, 0.2, B, seg=7)
    m.esfera((0.02, 0.0, z0 + 3.82), 0.22, B, seg=10, anillos=7, esc=(0.92, 1.0, 1.1))
    m.caja((0.02, -0.2, z0 + 3.8), (0.1, 0.08, 0.12), B, bisel=0.02)
    m.torno((0.02, 0.03, z0 + 3.9), [(0.23, 0), (0.2, 0.12), (0.0, 0.18)], B, seg=10)
    capa = [(-0.5, 3.4), (0.5, 3.4), (0.66, 2.4), (0.8, 1.2), (0.5, 0.75), (0.1, 0.95), (-0.3, 0.7), (-0.75, 1.1), (-0.62, 2.4)]
    m.prisma([(u, z0 + v) for u, v in capa], 0.2, 0.3, B, "xz", rot=(-10, 0, 0), c=(0, 0, 0))


@modelo(105, "especiales", "edificio_mediano", (6, 1, 5))
def muro_perimetral(m):
    # Tramo de muro blindado: zócalo, placas, contrafuertes, adarve con parapeto, luces y dos torretas automáticas
    m.caja((0, 0, 0.25), (6.0, 1.0, 0.5), "oscuro", bisel=0.05)
    m.caja((0, 0, 2.05), (6.0, 0.7, 3.2), "gris")
    for k in range(3):
        x = -2.0 + 2.0 * k
        for s in (-1, 1):
            m.caja((x, s * 0.37, 2.1), (1.8, 0.08, 2.6), "blanco_liso", bisel=0.05)
            for (dx, dz) in ((-0.75, 1.1), (0.75, 1.1), (-0.75, -1.1), (0.75, -1.1)):
                m.cil((x + dx, s * 0.42, 2.1 + dz), 0.05, 0.03, "acero", eje="y", seg=6)
            m.caja((x, s * 0.42, 2.9), (1.2, 0.02, 0.07), "neon")
            m.caja((x, s * 0.42, 0.9), (1.5, 0.03, 0.2), "rayas")
    for x in (-3.0, -1.0, 1.0, 3.0):
        for s in (-1, 1):
            m.prisma([(s * 0.35, 0.5), (s * 0.5, 0.5), (s * 0.5, 2.6), (s * 0.35, 3.6)], x - 0.14, x + 0.14, "gris_liso", "yz") \
                if abs(x) < 3 else None
        m.caja((x if abs(x) < 3 else x * 0.96, 0, 2.3), (0.24, 0.84, 3.6), "oscuro_paneles") if abs(x) == 3.0 else None
    # Adarve y parapeto almenado
    m.caja((0, 0, 3.75), (6.0, 1.0, 0.2), "gris", bisel=0.03)
    m.caja((0, 0, 3.86), (5.8, 0.7, 0.03), "rejilla")
    for k in range(6):
        x = -2.5 + 1.0 * k
        m.caja((x, -0.42, 4.2), (0.66, 0.16, 0.7), "blanco_liso", bisel=0.03)
        m.caja((x, -0.51, 4.2), (0.4, 0.02, 0.08), "neon")
    m.caja((0, -0.42, 3.95), (6.0, 0.16, 0.2), "blanco_liso")
    m.barandilla((-2.9, 0.44, 3.85), (2.9, 0.44, 3.85), 0.8, postes=6, travesanos=1, r=0.03)
    # Torretas automáticas (base fija; cabeza y cañones como piezas aparte para que giren)
    for i, x in enumerate((-1.5, 1.5)):
        T = f"torreta_{i + 1}"
        m.cil((x, 0.0, 4.0), 0.36, 0.24, "oscuro", seg=12)
        m.tubo((x, 0.0, 4.1), 0.38, 0.06, 0.04, "neon", seg=12)
        m.cil((x, 0.0, 4.25), 0.26, 0.26, "gris_liso", seg=12, p=T)
        m.caja((x, -0.02, 4.58), (0.6, 0.7, 0.4), "blanco_liso", bisel=0.08, p=T)
        m.caja((x, -0.02, 4.8), (0.3, 0.4, 0.08), "oscuro", p=T)
        for s in (-1, 1):
            m.cil((x + s * 0.16, -0.62, 4.6), 0.055, 0.7, "oscuro", eje="y", seg=8, p=T)
            m.cil((x + s * 0.16, -0.95, 4.6), 0.075, 0.12, "acero", eje="y", seg=8, p=T)
            m.cil((x + s * 0.16, -1.01, 4.6), 0.04, 0.02, "neon_naranja", eje="y", seg=6)
            m.caja((x + s * 0.34, 0.0, 4.55), (0.1, 0.4, 0.26), "gris_liso", p=T)
        m.cil((x, -0.38, 4.74), 0.07, 0.06, "neon_rojo", eje="y", seg=8)                              # sensor
        m.cil((x + 0.22, 0.2, 4.95), 0.015, 0.4, "acero", seg=4, p=T)
        m.anclaje(f"boca_torreta_{i + 1}", (x, -1.02, 4.6))
    # Foco central y caja de conexiones
    m.caja((0, -0.3, 4.75), (0.4, 0.3, 0.3), "oscuro", bisel=0.04)
    m.caja((0, -0.46, 4.75), (0.3, 0.03, 0.2), "neon_blanco")
    m.cil((0, -0.2, 4.3), 0.04, 0.7, "acero", seg=5)
    m.caja((2.6, 0.38, 1.3), (0.5, 0.14, 0.7), "gris_claro", bisel=0.03)
    m.barrido([(2.6, 0.42, 1.65), (2.6, 0.46, 2.6), (2.2, 0.46, 3.6)], 0.03, "goma", seg=4)
