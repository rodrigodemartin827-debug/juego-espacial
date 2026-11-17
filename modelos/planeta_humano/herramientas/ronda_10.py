"""Ronda 10 · Fin de naturaleza (91-95) y edificios especiales (96-100)."""

import math

from geometria import arco_pts
from registro import modelo
from ronda_03 import _local, _frasco


@modelo(91, "naturaleza", "vegetacion", (0.5, 0.5, 1))
def flor_luminosa_b(m):
    # Tres campanillas cerradas que cuelgan de tallos en cayado, con el interior azul luminoso
    m.torno((0, 0, 0), [(0.07, 0), (0.05, 0.03), (0, 0.04)], "tierra", seg=7)
    datos = [(0, 0.98, 0.17, 1.0), (130, 0.74, 0.14, 0.82), (250, 0.56, 0.12, 0.7)]
    for ang, alto, vuelo, esc in datos:
        a = math.radians(ang)
        ca, sa = math.cos(a), math.sin(a)
        pts = [(0, 0, 0.02), (0.02 * ca, 0.02 * sa, alto * 0.5), (0.05 * ca, 0.05 * sa, alto * 0.86),
               (vuelo * 0.6 * ca, vuelo * 0.6 * sa, alto), (vuelo * ca, vuelo * sa, alto - 0.05)]
        m.barrido(pts, [0.024, 0.02, 0.016, 0.013, 0.011], "hoja2", seg=5)
        cx, cy, cz = vuelo * ca, vuelo * sa, alto - 0.05
        r = 0.085 * esc
        # campana con grosor (boca hacia abajo) y cáliz
        m.torno((cx, cy, cz), [(0.012, 0), (r * 0.5, -0.03 * esc), (r * 0.85, -0.1 * esc), (r, -0.2 * esc), (r * 1.12, -0.25 * esc),
                               (r * 0.96, -0.24 * esc), (r * 0.74, -0.1 * esc), (r * 0.36, -0.04 * esc)], "hoja_azul", seg=8,
                cerrar=True)
        m.torno((cx, cy, cz + 0.005), [(0.0, 0.01), (r * 0.5, 0.0), (r * 0.62, -0.05 * esc), (0.0, -0.03 * esc)], "hoja2", seg=6)
        m.torno((cx, cy, cz - 0.05 * esc), [(0.0, 0), (r * 0.66, -0.06 * esc), (r * 0.8, -0.17 * esc), (0.0, -0.19 * esc)],
                "neon_azul", seg=8)
        m.cil((cx, cy, cz - 0.24 * esc), 0.006, 0.08 * esc, "hoja_clara", seg=3)
        m.esfera((cx, cy, cz - 0.285 * esc), 0.018 * esc, "neon_azul", seg=5, anillos=3)
        for k in range(5):                                                         # picos del borde de la campana
            b = math.radians(72 * k)
            m.hoja((cx + r * 1.02 * math.cos(b), cy + r * 1.02 * math.sin(b), cz - 0.245 * esc), 0.05 * esc, 0.04 * esc,
                   "hoja_cyan", rot=(0, 35, 72 * k), grosor=0.008)
    m.hoja((0, 0, 0.1), 0.26, 0.11, "hoja", rot=(0, -45, 60))
    m.hoja((0, 0, 0.16), 0.22, 0.1, "hoja_clara", rot=(0, -50, 190))
    m.hoja((0, 0, 0.05), 0.2, 0.09, "hoja", rot=(0, -30, 310))


@modelo(92, "naturaleza", "vegetacion", (1, 1, 2))
def hongo_luminoso(m):
    R = m.rng
    # Seta grande: pie abombado con anillo, sombrero con grosor, laminillas, puntos brillantes y dos setas pequeñas
    m.torno((0, 0, 0), [(0.26, 0), (0.3, 0.1), (0.2, 0.4), (0.15, 0.9), (0.14, 1.35), (0.0, 1.4)],
            m.color("#E9E2D0", 0.7), seg=10)
    m.torno((0, 0, 1.0), [(0.15, 0.06), (0.3, -0.04), (0.32, -0.1), (0.16, 0.0)], m.color("#D8CDB4", 0.7), seg=10, cerrar=True)
    sombrero = m.color("#2F6FA8", 0.5)
    m.torno((0, 0, 1.3), [(0.5, 0.0), (0.47, 0.2), (0.36, 0.42), (0.18, 0.58), (0.0, 0.64), (0.0, 0.5), (0.2, 0.38), (0.34, 0.2),
                          (0.42, 0.04)], sombrero, seg=14, cerrar=False)
    m.torno((0, 0, 1.3), [(0.14, 0.0), (0.42, 0.04), (0.5, 0.0), (0.44, -0.03)], m.color("#D8CDB4", 0.7), seg=14, cerrar=True)
    for k in range(14):                                                            # laminillas
        a = math.radians(360 * k / 14)
        m.caja((0.29 * math.cos(a), 0.29 * math.sin(a), 1.295), (0.28, 0.012, 0.05), m.color("#8FD9E8", 0.5),
               rot=(0, 0, math.degrees(a)))
    m.tubo((0, 0, 1.3), 0.5, 0.025, 0.03, "neon", seg=14)
    for i in range(13):                                                            # puntos luminosos del sombrero
        a = R.uniform(0, 6.28)
        t = R.uniform(0.15, 0.95)
        r = 0.5 * math.cos(t * 1.35) * 0.97
        z = 1.3 + 0.64 * math.sin(t * 1.5) * 0.98
        m.esfera((r * math.cos(a), r * math.sin(a), z), R.uniform(0.035, 0.06), "neon", seg=6, anillos=4, esc=(1, 1, 0.6))
    for (x, y, h) in ((0.36, -0.2, 0.5), (-0.34, 0.24, 0.36)):
        m.torno((x, y, 0), [(0.07, 0), (0.05, h * 0.7), (0.0, h * 0.75)], m.color("#E9E2D0", 0.7), seg=7)
        m.torno((x, y, h * 0.66), [(0.17, 0), (0.13, h * 0.2), (0.0, h * 0.34)], sombrero, seg=8)
        m.esfera((x, y, h * 1.0), 0.03, "neon", seg=5, anillos=3)
    for k in range(6):
        a = k * 1.05
        m.brizna((0.42 * math.cos(a), 0.42 * math.sin(a), 0), 0.2, 0.03, "hoja", inclin=(0.05 * math.cos(a), 0.05 * math.sin(a)),
                 giro=a)


@modelo(93, "naturaleza", "vegetacion", (1, 1, 3))
def cristal_decorativo(m):
    # Racimo de cristales hexagonales que brota de una base de roca; todo el cristal es de neón
    m.roca((0, 0, 0.1), (1.0, 0.95, 0.36), "piedra_oscura", semilla=4.4, sub=2, ruido=0.3)
    for i, (x, y, s) in enumerate(((0.36, 0.2, 0.3), (-0.34, -0.26, 0.26), (-0.2, 0.36, 0.22))):
        m.roca((x, y, 0.07), (s, s * 0.8, s * 0.6), "piedra", semilla=i * 1.9, sub=1)
    cristales = [((0.0, 0.0), 0.2, 2.9, (4, -3)), ((0.2, -0.1), 0.14, 2.0, (-14, 22)), ((-0.2, 0.08), 0.15, 2.3, (10, -24)),
                 ((0.02, 0.22), 0.11, 1.5, (-30, 6)), ((-0.1, -0.24), 0.1, 1.2, (32, -10)), ((0.3, 0.16), 0.08, 0.9, (-22, 36)),
                 ((-0.33, -0.1), 0.07, 0.7, (14, -44))]
    for i, ((x, y), r, h, (rx, ry)) in enumerate(cristales):
        m.torno((x, y, 0.08), [(r * 0.8, 0), (r, h * 0.12), (r * 0.92, h * 0.78), (r * 0.3, h * 0.96), (0, h)], "neon", seg=6,
                rot=(rx, ry, i * 17), p="cristal_neon" if i == 0 else None)
    m.tubo((0, 0, 0.28), 0.34, 0.03, 0.04, "piedra_oscura", seg=8)
    m.anclaje("luz", (0, 0, 1.6))


@modelo(94, "naturaleza", "vegetacion", (8, 8, 0.5))
def cesped_alien(m):
    R = m.rng
    # Placa con hierba alienígena azul-verde: briznas curvas de dos tramos, matas con punta luminosa y bulbos
    m.caja((0, 0, 0.07), (8, 8, 0.14), m.color("#2B3A4A", 0.95))
    m.caja((0, 0, 0.165), (7.96, 7.96, 0.05), "cesped_alien")
    for i in range(24):
        for j in range(24):
            if R.random() < 0.2:
                continue
            x = -3.85 + 7.7 * (i + R.uniform(0.15, 0.85)) / 24
            y = -3.85 + 7.7 * (j + R.uniform(0.15, 0.85)) / 24
            h = R.uniform(0.13, 0.26)
            mat = ("cesped_alien", "hoja_azul", "hoja_cyan")[R.choice((0, 0, 1, 2))]
            a = R.uniform(0, 6.28)
            m.brizna((x, y, 0.185), h, R.uniform(0.07, 0.1), mat, inclin=(0.12 * math.cos(a), 0.12 * math.sin(a)), giro=a)
    for k in range(20):                                                            # matas rizadas con punta de luz
        x, y = R.uniform(-3.5, 3.5), R.uniform(-3.5, 3.5)
        for q in range(3):
            a = q * 2.1 + k
            pts = [(x, y, 0.18), (x + 0.07 * math.cos(a), y + 0.07 * math.sin(a), 0.33),
                   (x + 0.2 * math.cos(a), y + 0.2 * math.sin(a), 0.4), (x + 0.26 * math.cos(a), y + 0.26 * math.sin(a), 0.34)]
            m.barrido(pts, [0.028, 0.022, 0.016, 0.008], "hoja_azul", seg=3)
        if k % 2 == 0:
            m.esfera((x, y, 0.44), 0.035, "neon", seg=5, anillos=3)
            m.cil((x, y, 0.31), 0.008, 0.24, "hoja_cyan", seg=3)
    for k in range(7):                                                             # bulbos
        x, y = R.uniform(-3.4, 3.4), R.uniform(-3.4, 3.4)
        m.esfera((x, y, 0.25), 0.11, m.color("#6B4FC0", 0.4), seg=7, anillos=5, esc=(1, 1, 0.8))
        m.esfera((x, y, 0.34), 0.04, "neon", seg=5, anillos=3)
    for (x, y, s) in ((-2.6, 1.9, 0.5), (2.7, -2.4, 0.4)):
        m.roca((x, y, 0.22), (s, s * 0.8, s * 0.5), "piedra_oscura", semilla=x, sub=1)


@modelo(95, "naturaleza", "vegetacion", (2, 2, 0.3))
def nenufar_espacial(m):
    # Hoja flotante con muesca y borde levantado, nervios en relieve, flor de loto luminosa y capullo
    n = 26
    borde = [(0, 0)] + [(0.98 * math.cos(math.radians(14 + 332 * i / n)), 0.98 * math.sin(math.radians(14 + 332 * i / n)))
                        for i in range(n + 1)]
    m.prisma(borde, 0.0, 0.05, "hoja2", "xy")
    for i in range(n):
        a0, a1 = math.radians(14 + 332 * i / n), math.radians(14 + 332 * (i + 1) / n)
        am = (a0 + a1) / 2
        L = 2 * 0.98 * math.sin((a1 - a0) / 2) + 0.01
        m.caja((0.97 * math.cos(am), 0.97 * math.sin(am), 0.07), (0.05, L, 0.08), "hoja", rot=(0, -18, math.degrees(am)))
    for k in range(9):                                                             # nervios radiales
        a = math.radians(30 + 300 * k / 8)
        m.barrido([(0.05 * math.cos(a), 0.05 * math.sin(a), 0.055), (0.9 * math.cos(a), 0.9 * math.sin(a), 0.058)],
                  [0.022, 0.008], "hoja_cyan", seg=3)
    m.tubo((0, 0, 0.052), 0.6, 0.012, 0.02, "neon", seg=22) if False else None
    # Flor de loto: dos coronas de pétalos con grosor y núcleo brillante
    fx, fy = -0.3, 0.2
    m.cil((fx, fy, 0.06), 0.1, 0.03, "hoja", seg=8)
    for k in range(8):
        m.hoja((fx, fy, 0.07), 0.3, 0.14, m.color("#BFF6FA", 0.4), rot=(0, -25, 45 * k), grosor=0.02)
    for k in range(6):
        m.hoja((fx, fy, 0.09), 0.2, 0.1, "neon", rot=(0, -55, 60 * k + 30), grosor=0.018, p="petalos_neon")
    m.esfera((fx, fy, 0.14), 0.055, "neon_blanco", seg=7, anillos=4)
    # Capullo, gotas de agua y raíces colgantes
    m.barrido([(0.45, -0.3, 0.05), (0.5, -0.33, 0.16), (0.52, -0.36, 0.22)], 0.014, "hoja", seg=4)
    m.torno((0.52, -0.36, 0.2), [(0.0, 0), (0.05, 0.03), (0.035, 0.08), (0.0, 0.1)], "neon", seg=6)
    for (x, y, r) in ((0.3, 0.45, 0.04), (-0.55, -0.35, 0.03), (0.1, -0.6, 0.035)):
        m.esfera((x, y, 0.06), r, "agua", seg=6, anillos=4, esc=(1, 1, 0.6))
    for k in range(4):
        a = k * 1.6
        m.barrido([(0.2 * math.cos(a), 0.2 * math.sin(a), 0.0), (0.24 * math.cos(a), 0.24 * math.sin(a), -0.01),
                   (0.26 * math.cos(a), 0.26 * math.sin(a), 0.0)], 0.012, "hoja2", seg=3) if False else None
    m.tubo((0, 0, 0.025), 0.99, 0.02, 0.015, "neon", seg=26, p="halo_neon")


@modelo(96, "especiales", "edificio_grande", (18, 16, 12))
def centro_mando(m):
    m.caja((0, 0, 0.2), (18, 16, 0.4), "piedra_clara", bisel=0.06)
    # Escalinata y pórtico de columnas
    for k in range(4):
        m.bloque((-5.2 + 0.3 * k, -7.9 + 0.5 * k, 0.4 + 0.22 * k), (5.2 - 0.3 * k, -5.0, 0.62 + 0.22 * k), "piedra_clara")
    m.bloque((-4.3, -6.0, 1.28), (4.3, -3.6, 1.4), "blanco_liso")
    for x in (-3.9, -2.34, -0.78, 0.78, 2.34, 3.9):
        m.torno((x, -5.5, 1.4), [(0.38, 0), (0.38, 0.15), (0.28, 0.3), (0.25, 4.4), (0.36, 4.55), (0.36, 4.75)], "blanco_liso",
                seg=12)
        m.tubo((x, -5.5, 2.2), 0.3, 0.1, 0.04, "neon", seg=12)
    m.bloque((-4.5, -6.0, 6.15), (4.5, -3.6, 6.9), "blanco")
    m.bloque((-4.6, -6.1, 6.9), (4.6, -3.6, 7.1), "acento")
    m.prisma([(-4.7, 7.1), (4.7, 7.1), (0, 8.9)], -6.15, -3.6, "blanco_liso", "xz")
    m.prisma([(-3.6, 7.25), (3.6, 7.25), (0, 8.6)], -6.22, -6.12, "oscuro", "xz")
    m.cil((0, -6.26, 7.7), 0.42, 0.06, "neon", eje="y", seg=16)                       # emblema: planeta con órbita
    m.toro((0, -6.26, 7.7), 0.62, 0.035, "neon_blanco", eje="y", seg=20, seg2=5, rot=(0, 25, 0))
    m.caja((0, -6.06, 6.52), (6.6, 0.12, 0.5), "oscuro")
    m.texto("CENTRO DE MANDO", (0, -6.15, 6.52), 0.3, 0.06, "neon")
    # Cuerpo central de dos alturas y alas laterales
    m.bloque((-5.2, -3.7, 0.4), (5.2, 6.6, 8.6), "blanco")
    m.bloque((-5.26, -3.76, 0.4), (5.26, 6.66, 1.4), "piedra_oscura")
    m.bloque((-5.4, -3.9, 8.6), (5.4, 6.8, 9.0), "gris", bisel=0.08)
    m.bloque((-5.24, -3.74, 7.9), (5.24, 6.64, 8.15), "acento")
    for sx in (-1, 1):
        m.bloque((sx * 5.2, -2.6, 0.4), (sx * 8.5, 6.0, 6.0), "blanco")
        m.bloque((sx * 5.2, -2.66, 0.4), (sx * 8.56, 6.06, 1.4), "piedra_oscura")
        m.bloque((sx * 5.1, -2.8, 6.0), (sx * 8.7, 6.2, 6.35), "gris", bisel=0.07)
        m.bloque((sx * 5.2, -2.64, 5.35), (sx * 8.54, 6.04, 5.55), "acento")
        # Pantallas holográficas en la fachada de las alas
        m.caja((sx * 6.85, -2.7, 3.6), (2.5, 0.16, 2.6), "oscuro", bisel=0.04)
        m.caja((sx * 6.85, -2.8, 3.6), (2.2, 0.03, 2.3), "neon", p="pantallas_neon")
        for k in range(4):
            m.caja((sx * 6.85 - 0.5 + 0.34 * k, -2.84, 3.0 + 0.1 * k), (0.2, 0.02, 0.5 + 0.2 * k), "neon_blanco")
        m.barrido([(sx * 6.85 + x, -2.84, 4.3 + z) for x, z in ((-0.9, -0.1), (-0.4, 0.2), (0.1, 0.0), (0.5, 0.35), (0.9, 0.2))],
                  0.03, "neon_blanco", seg=4)
        m.ventana((sx * 6.85, -2.62, 1.9), 2.4, 0.8, cruz=True)
        for y in (0.0, 3.6):
            m.ventana((sx * 8.52, y, 3.4), 2.2, 2.2, normal="x", sentido=sx, cruz=True)
        m.ventana((sx * 6.85, 6.02, 3.4), 2.2, 2.0, sentido=1, cruz=True)
        # Banderas: mástil y paño ondulado con grosor
        m.cil((sx * 8.0, -2.0, 8.2), 0.06, 3.8, "acero", seg=8)
        m.esfera((sx * 8.0, -2.0, 10.15), 0.1, "oro", seg=8, anillos=5)
        paño = [(0.0, 0.0), (0.5, 0.08), (1.0, -0.06), (1.5, 0.06), (1.9, 0.0), (1.9, 1.1), (1.5, 1.16), (1.0, 1.04), (0.5, 1.18),
                (0.0, 1.1)]
        m.prisma([(sx * u, v) for u, v in paño] if sx < 0 else paño, -0.02, 0.02, "tela_cyan" if sx < 0 else "tela_azul", "xz",
                 c=(sx * 8.06 if sx > 0 else sx * 8.06, -2.0, 8.9), p="bandera_izq" if sx < 0 else "bandera_der")
        m.caja((sx * 8.06 + (0.95 if sx > 0 else -0.95), -2.03, 9.45), (0.5, 0.02, 0.14), "blanco_liso",
               p="bandera_izq" if sx < 0 else "bandera_der")
    # Entrada: puerta doble alta con marco luminoso
    m.marco((0, -3.76, 3.1), 3.2, 3.6, 0.26, 0.3, "gris_liso")
    for s, nom in ((-1, "puerta_izq"), (1, "puerta_der")):
        m.caja((s * 0.67, -3.7, 3.05), (1.32, 0.14, 3.1), "gris_claro", p=nom)
        m.caja((s * 0.67, -3.79, 3.4), (0.8, 0.06, 1.8), "cristal")
    m.caja((0, -3.9, 4.98), (3.0, 0.06, 0.08), "neon")
    for x in (-3.6, 3.6):
        m.ventana((x, -3.72, 3.2), 1.6, 2.6, cruz=True)
    for x in (-3.4, 0, 3.4):
        m.ventana((x, -3.72, 7.0), 1.8, 1.2) if abs(x) > 4.6 else None
        m.ventana((x, 6.62, 4.6), 2.2, 2.4, sentido=1, cruz=True)
    # Cúpula acristalada con nervios sobre tambor, y linterna
    m.cil((0, 1.4, 9.3), 3.4, 0.6, "blanco_liso", seg=24)
    m.tubo((0, 1.4, 9.62), 3.45, 0.1, 0.08, "neon", seg=24)
    m.cupula((0, 1.4, 9.6), 3.2, "cristal", grosor=0.1, seg=24, anillos=5, altura=0.68)
    for k in range(8):
        a = math.radians(45 * k)
        pts = [(3.25 * math.cos(a) * math.cos(math.radians(e)), 1.4 + 3.25 * math.sin(a) * math.cos(math.radians(e)),
                9.6 + 3.25 * 0.68 * math.sin(math.radians(e))) for e in (0, 22, 45, 67, 86)]
        m.barrido(pts, 0.07, "blanco_liso", seg=4)
    m.cil((0, 1.4, 11.85), 0.5, 0.2, "gris_liso", seg=12)
    m.cil((0, 1.4, 12.1), 0.05, 0.5, "acero", seg=6)
    m.esfera((0, 1.4, 12.38), 0.1, "neon", seg=8, anillos=5)
    m.cil((0, 1.4, 9.8), 0.9, 0.3, "oscuro", seg=12)                                  # mesa táctica bajo la cúpula
    m.cil((0, 1.4, 10.0), 0.7, 0.06, "neon", seg=12, p="pantallas_neon")
    # Antenas y parabólica en la azotea
    m.cil((4.2, 5.2, 10.2), 0.07, 2.4, "acero", seg=6)
    for z, l in ((10.2, 1.2), (10.7, 0.9), (11.1, 0.6)):
        m.cil((4.2, 5.2, z), 0.025, l, "acero", eje="x", seg=4)
    m.esfera((4.2, 5.2, 11.45), 0.08, "neon_rojo", seg=6, anillos=4)
    m.cil((-4.0, 5.0, 9.3), 0.3, 0.6, "gris_liso", seg=10)
    m.cupula((-4.0, 4.7, 10.0), 0.9, "blanco_liso", grosor=0.06, seg=14, anillos=3, altura=0.38, rot=(120, 0, 0))
    m.barrido([(-4.0, 4.7, 10.0), (-4.0, 4.15, 10.35)], 0.025, "acero", seg=4)


@modelo(97, "especiales", "edificio_grande", (14, 12, 10))
def laboratorio(m):
    L = _local(m, 14, 12, 10, vanos=[(-6.3, -0.8), (3.6, 6.3)], puerta=(1.4, 2.8), hz=4.4, prof=2.2, acento="verde_p")
    yf, yb, zs, hz, zt = L["yf"], L["yb"], L["zs"], L["hz"], L["zt"]
    m.bloque((-6.2, yb - 0.08, 0.9), (-0.9, yb, hz - 0.1), "gris_claro")
    m.bloque((3.7, yb - 0.08, 0.9), (6.2, yb, hz - 0.1), "gris_claro")
    # Mesa de laboratorio con probetas en gradilla, matraces, mechero y microscopio
    m.bloque((-5.9, yf + 0.6, 0.9), (-1.2, yf + 1.5, 1.85), "blanco_liso")
    m.bloque((-6.0, yf + 0.5, 1.85), (-1.1, yf + 1.6, 1.95), "plastico_negro")
    cols = ["#57D95B", "#3DB8F2", "#E0403A", "#B455E0", "#F2C230"]
    m.caja((-5.2, yf + 1.0, 2.1), (1.2, 0.3, 0.06), "madera_clara")
    m.caja((-5.2, yf + 1.0, 2.3), (1.2, 0.3, 0.04), "madera_clara")
    for i in range(6):
        x = -5.7 + 0.2 * i
        m.cil((x, yf + 1.0, 2.25), 0.055, 0.52, "cristal", seg=8)
        m.cil((x, yf + 1.0, 2.14), 0.04, 0.26, m.color(cols[i % 5], 0.25), seg=6)
    _frasco(m, (-4.1, yf + 1.0, 1.95), 0.26, "#57D95B", tipo=2)
    _frasco(m, (-3.4, yf + 1.1, 1.95), 0.22, "#3DB8F2", tipo=0)
    _frasco(m, (-2.8, yf + 0.95, 1.95), 0.16, "#B455E0", tipo=1)
    m.torno((-2.1, yf + 1.0, 1.95), [(0.12, 0), (0.05, 0.06), (0.04, 0.3), (0, 0.3)], "acero", seg=8)       # mechero
    m.torno((-2.1, yf + 1.0, 2.25), [(0.03, 0), (0.05, 0.08), (0, 0.24)], "neon_azul", seg=6)
    m.caja((-1.6, yf + 1.1, 2.0), (0.3, 0.4, 0.08), "oscuro")                                             # microscopio
    m.barrido([(-1.6, yf + 1.25, 2.0), (-1.6, yf + 1.28, 2.5), (-1.6, yf + 1.05, 2.62)], 0.04, "blanco_liso", seg=6)
    m.cil((-1.6, yf + 1.02, 2.5), 0.045, 0.34, "acero", seg=6, rot=(20, 0, 0))
    # Serpentín de vidrio y columna de destilación al fondo
    esp = [(-4.6 + 0.16 * math.cos(i * 0.9), yb - 0.4 + 0.16 * math.sin(i * 0.9), 2.2 + 0.06 * i) for i in range(26)]
    m.barrido(esp, 0.035, "cristal", seg=5)
    m.cil((-4.6, yb - 0.4, 3.0), 0.03, 1.9, "acero", seg=5)
    m.cil((-2.6, yb - 0.45, 2.9), 0.22, 1.8, "cristal", seg=10)
    m.cil((-2.6, yb - 0.45, 2.6), 0.18, 1.1, "neon_verde", seg=8)
    for z in (1.98, 3.82):
        m.cil((-2.6, yb - 0.45, z), 0.26, 0.1, "acero", seg=10)
    # Escaparate derecho: tanque de espécimen con líquido verde y burbujas
    m.cil((4.95, yf + 1.2, 2.4), 0.75, 2.6, "cristal", seg=14)
    m.cil((4.95, yf + 1.2, 2.3), 0.68, 2.2, m.color("#3FD98A", 0.2), seg=12) if False else None
    m.ico((4.95, yf + 1.2, 2.3), 0.4, "neon_verde", sub=2, esc=(0.8, 0.8, 1.5), ruido=0.3, semilla=2.0)
    for z in (1.0, 3.75):
        m.cil((4.95, yf + 1.2, z), 0.82, 0.24, "acero", seg=14)
    for k in range(5):
        m.esfera((4.7 + 0.12 * k, yf + 1.0 + 0.08 * (k % 2), 1.5 + 0.45 * k), 0.05, "neon_blanco", seg=5, anillos=3)
    m.barrido([(5.6, yf + 1.2, 3.8), (6.0, yf + 1.4, 3.9), (6.1, yb - 0.1, 3.2)], 0.05, "goma", seg=5)
    # Segundo piso, rótulo, luces verdes y aviso de riesgo biológico
    m.bloque((L["x0"] - 0.06, yf - 0.06, 5.2), (L["x1"] + 0.06, 5.76, 5.45), "gris", bisel=0.04)
    for x in (-5.0, -2.6, -0.2, 2.2, 4.6):
        m.ventana((x, yf - 0.02, 6.9), 1.8, 1.7, cristal="cristal")
        m.caja((x, yf - 0.1, 5.9), (1.4, 0.05, 0.06), "neon_verde")
    m.caja((0, yf - 0.1, hz + 0.45), (6.0, 0.16, 0.6), "oscuro", bisel=0.03)
    m.texto("LABORATORIO", (0, yf - 0.2, hz + 0.45), 0.34, 0.06, "neon_verde")
    for sx in (-1, 1):
        for y in (-0.5, 3.2):
            for z in (2.8, 6.9):
                m.ventana((sx * 6.72, y, z), 2.2, 1.7, normal="x", sentido=sx, cruz=True)
        m.caja((sx * 6.74, -2.4, 4.8), (0.06, 1.6, 0.08), "neon_verde")
    for x in (-3.5, 0, 3.5):
        m.ventana((x, 5.72, 6.9), 2.2, 1.7, sentido=1, cruz=True)
    # Azotea: chimenea de ventilación con sombrerete, extractores, depósitos esféricos y tuberías
    m.cil((4.6, 3.6, zt + 1.5), 0.5, 2.6, "acero", seg=12)
    for z in (0.9, 1.9):
        m.tubo((4.6, 3.6, zt + z), 0.54, 0.1, 0.05, "gris_liso", seg=12)
    m.torno((4.6, 3.6, zt + 2.8), [(0.7, 0), (0.7, 0.08), (0, 0.4)], "gris", seg=12)
    for a in (0, 120, 240):
        m.cil((4.6 + 0.45 * math.cos(math.radians(a)), 3.6 + 0.45 * math.sin(math.radians(a)), zt + 2.7), 0.03, 0.3, "acero",
              seg=4)
    m.anclaje("vapor_ventilacion", (4.6, 3.6, zt + 3.3))
    for x in (-4.6, -2.8):
        m.esfera((x, 3.4, zt + 1.3), 0.85, "blanco_liso", seg=14, anillos=9)
        m.tubo((x, 3.4, zt + 1.3), 0.87, 0.1, 0.04, "verde_p", seg=14)
        for a in (45, 135, 225, 315):
            ra = math.radians(a)
            m.barrido([(x + 0.5 * math.cos(ra), 3.4 + 0.5 * math.sin(ra), zt + 0.75), (x + 0.75 * math.cos(ra),
                       3.4 + 0.75 * math.sin(ra), zt + 0.3)], 0.05, "acero", seg=4)
    m.barrido([(-4.6, 3.4, zt + 2.15), (-4.6, 3.4, zt + 2.4), (-2.8, 3.4, zt + 2.4), (-2.8, 3.4, zt + 2.15)], 0.07, "cobre", seg=6)
    m.barrido([(-2.0, 3.4, zt + 1.3), (0.5, 3.4, zt + 1.0), (0.5, 3.4, zt + 0.3)], 0.08, "cobre", seg=6)
    m.caja((1.5, 1.0, zt + 0.75), (2.2, 1.6, 0.9), "gris_claro", bisel=0.05)
    for x in (0.95, 2.05):
        m.cil((x, 1.0, zt + 1.22), 0.42, 0.08, "oscuro", seg=10)


def _diana(m, c, giro=0):
    x, y, z = c
    a = math.radians(giro)
    for s in (-1, 1):
        m.barrido([(x + s * 0.5 * math.cos(a), y + s * 0.5 * math.sin(a), z), (x + s * 0.1 * math.cos(a), y + s * 0.1 * math.sin(a),
                   z + 2.0)], 0.05, "madera_oscura", seg=4)
    m.barrido([(x - 0.7 * math.sin(a) * -1, y - 0.7 * math.cos(a) * 1 + 1.4 * math.cos(a), z), (x, y, z + 1.7)], 0.05,
              "madera_oscura", seg=4)
    cols = ["tela_blanca", "plastico_negro", "azul_p", "rojo_p", "amarillo_p"]
    for i, r in enumerate((0.75, 0.6, 0.45, 0.3, 0.14)):
        m.cil((x - 0.04 * i * math.sin(a) * -1 * -1, y - 0.03 * i * math.cos(a), z + 1.55), r, 0.12, cols[i], eje="y", seg=18,
              rot=(0, 0, giro))
    m.cil((x - 0.3 * 0, y - 0.3 * math.cos(a), z + 1.6), 0.015, 0.6, "madera", eje="y", seg=4, rot=(0, 0, giro))   # flecha clavada
    m.hoja((x, y - 0.62 * math.cos(a), z + 1.6), 0.14, 0.08, "rojo_p", rot=(90, 0, 90 + giro))


def _pelele(m, c, giro=0):
    """Maniquí de combate: poste, torso acolchado, brazos en cruz y cabeza con diana."""
    x, y, z = c
    m.cil((x, y, z + 0.06), 0.4, 0.12, "hierro", seg=10)
    m.cil((x, y, z + 1.0), 0.08, 1.9, "madera_oscura", seg=8)
    m.torno((x, y, z + 1.2), [(0.26, 0), (0.36, 0.3), (0.4, 0.9), (0.28, 1.15), (0.0, 1.2)], "tela_naranja", seg=10)
    for zz in (1.5, 1.95):
        m.tubo((x, y, z + zz), 0.39, 0.06, 0.03, "madera_oscura", seg=10)
    m.cil((x, y, z + 2.1), 0.07, 1.7, "madera_oscura", eje="x", seg=6, rot=(0, 0, giro))
    for s in (-1, 1):
        a = math.radians(giro)
        m.esfera((x + s * 0.85 * math.cos(a), y + s * 0.85 * math.sin(a), z + 2.1), 0.14, "tela_naranja", seg=8, anillos=5)
    m.esfera((x, y, z + 2.7), 0.26, "tela_blanca", seg=10, anillos=7)
    m.cil((x, y - 0.24, z + 2.7), 0.1, 0.05, "rojo_p", eje="y", seg=8, rot=(0, 0, giro))
    m.cil((x, y - 0.39, z + 1.75), 0.14, 0.04, "rojo_p", eje="y", seg=10)


@modelo(98, "especiales", "edificio_grande", (16, 16, 8))
def academia_entrenamiento(m):
    # Arena abierta: murete perimetral, suelo de arena, arco de entrada, gradas, dianas, peleles y armeros
    m.caja((0, 0, 0.15), (16, 16, 0.3), "hormigon", bisel=0.05)
    m.bloque((-7.0, -7.0, 0.3), (7.0, 4.2, 0.4), m.color("#C9B58A", 0.95))
    for (a, b) in (((-7.6, -7.6, 0.3), (-2.6, -7.0, 1.6)), ((2.6, -7.6, 0.3), (7.6, -7.0, 1.6)),
                   ((-7.6, -7.0, 0.3), (-7.0, 7.6, 1.6)), ((7.0, -7.0, 0.3), (7.6, 7.6, 1.6)), ((-7.0, 7.0, 0.3), (7.0, 7.6, 1.6))):
        m.bloque(a, b, "blanco")
        m.bloque((a[0] - 0.05, a[1] - 0.05, 1.6), (b[0] + 0.05, b[1] + 0.05, 1.78), "gris_liso")
    for (x, y) in ((-7.3, -7.3), (7.3, -7.3), (-7.3, 7.3), (7.3, 7.3)):
        m.caja((x, y, 1.5), (0.9, 0.9, 2.4), "gris", bisel=0.06)
        m.torno((x, y, 2.7), [(0.3, 0), (0.42, 0.2), (0.42, 0.4), (0.32, 0.4), (0.3, 0.25), (0, 0.2)], "hierro", seg=8)
        m.torno((x, y, 2.95), [(0.26, 0), (0.18, 0.3), (0, 0.6)], "neon_naranja", seg=6)                 # pebeteros
    # Arco de entrada con rótulo y estandartes
    for s in (-1, 1):
        m.caja((s * 2.9, -7.3, 2.8), (0.9, 0.9, 5.0), "blanco", bisel=0.06)
        m.caja((s * 2.9, -7.78, 3.2), (0.14, 0.04, 3.2), "neon")
        m.prisma([(-0.4, 0), (0.4, 0), (0.4, -2.0), (0, -2.4), (-0.4, -2.0)], -0.02, 0.02, "tela_cyan", "xz",
                 c=(s * 4.2, -7.66, 5.0), p="estandartes")
        m.cil((s * 4.2, -7.62, 5.05), 0.03, 1.0, "acero", eje="x", seg=5)
    m.prisma(arco_pts(3.35, 2.45, 0, 180, 10, 0, 5.3, 1.0, 0.75), -7.75, -6.85, "blanco", "xz")
    m.prisma(arco_pts(3.42, 3.3, 0, 180, 10, 0, 5.3, 1.0, 0.75), -7.8, -6.8, "acento", "xz")
    m.caja((0, -7.8, 6.6), (3.6, 0.14, 0.7), "oscuro", bisel=0.03)
    m.texto("ACADEMIA", (0, -7.9, 6.6), 0.36, 0.06, "neon")
    # Gradas al fondo (cuatro filas) con asientos y barandilla
    for k in range(4):
        m.bloque((-6.6, 4.2 + 0.72 * k, 0.3), (6.6, 7.0, 1.0 + 0.6 * k), "gris")
        m.bloque((-6.5, 4.25 + 0.72 * k, 1.0 + 0.6 * k), (6.5, 4.75 + 0.72 * k, 1.08 + 0.6 * k), "madera_clara")
    for x in (-6.6, -2.2, 2.2, 6.6):
        m.bloque((x - 0.25, 4.2, 0.3), (x + 0.25, 7.0, 0.5), "rayas") if False else None
        for k in range(4):
            m.bloque((x - 0.3, 4.2 + 0.72 * k, 1.0 + 0.6 * k - 0.3), (x + 0.3, 4.2 + 0.72 * k + 0.36, 1.0 + 0.6 * k - 0.0), "gris_liso") \
                if abs(x) < 3 else None
    m.barandilla((-6.6, 4.3, 1.0), (-2.6, 4.3, 1.0), 0.9, postes=4)
    m.barandilla((2.6, 4.3, 1.0), (6.6, 4.3, 1.0), 0.9, postes=4)
    # Cubierta ligera de las gradas
    for x in (-6.4, 0, 6.4):
        m.cil((x, 6.8, 3.9), 0.1, 5.0, "acero", seg=8)
        m.barrido([(x, 6.8, 6.3), (x, 4.0, 5.7)], 0.07, "acero", seg=5)
    m.prisma([(3.8, 5.62), (7.1, 6.32), (7.1, 6.44), (3.8, 5.74)], -6.8, 6.8, "chapa", "yz")
    m.caja((0, 3.86, 5.62), (13.0, 0.06, 0.07), "neon")
    # Campo de tiro (izquierda): tres dianas; zona de combate (derecha): tres peleles en círculo marcado
    for i, x in enumerate((-5.6, -3.9, -2.2)):
        _diana(m, (x, 2.6, 0.4))
        m.caja((x, -3.6, 0.42), (1.2, 0.2, 0.04), "blanco_liso")
    m.tubo((3.6, -1.0, 0.41), 2.7, 0.03, 0.18, "blanco_liso", seg=28)
    _pelele(m, (3.6, 0.4, 0.4))
    _pelele(m, (2.2, -1.8, 0.4), 30)
    _pelele(m, (5.0, -1.8, 0.4), -30)
    # Armeros con espadas de entrenamiento y escudos, banco y baúl
    for sx in (-6.6, 6.6):
        m.caja((sx, -4.6, 1.3), (0.2, 2.4, 0.12), "madera_oscura")
        m.caja((sx, -4.6, 0.55), (0.3, 2.4, 0.12), "madera_oscura")
        for y in (-5.7, -3.5):
            m.caja((sx, y, 1.0), (0.14, 0.14, 1.4), "madera_oscura")
        for k in range(5):
            y = -5.4 + 0.4 * k
            s = -1 if sx > 0 else 1
            m.prisma([(-0.06, 0), (0.06, 0), (0.05, 1.3), (0, 1.5), (-0.05, 1.3)], -0.02, 0.02, "madera_clara" if k % 2 else "acero",
                     "yz", c=(sx + s * 0.18, y, 0.62), rot=(0, s * 10, 0))
            m.caja((sx + s * 0.14, y, 0.9), (0.06, 0.3, 0.05), "bronce")
    m.torno((6.5, -2.4, 1.2), [(0.0, 0.1), (0.3, 0.06), (0.55, 0.0), (0.5, -0.04), (0.0, 0.0)], m.color("#2D5FA8", 0.5, 0.3), seg=12,
            eje="x", rot=(0, 0, 180))
    m.caja((-6.4, 0.2, 0.75), (0.6, 2.0, 0.1), "madera_clara", bisel=0.02)
    for y in (-0.6, 1.0):
        m.caja((-6.4, y, 0.55), (0.5, 0.12, 0.3), "hierro")
    m.caja((-6.3, -2.2, 0.75), (0.8, 1.2, 0.7), "madera", bisel=0.03)
    m.caja((-6.3, -2.2, 0.75), (0.84, 0.14, 0.74), "hierro")
    # Marcador luminoso de puntuación
    m.cil((6.3, 2.6, 1.9), 0.06, 3.0, "acero", seg=6)
    m.caja((6.3, 2.55, 3.6), (1.4, 0.14, 0.9), "oscuro", bisel=0.03)
    m.texto("12:07", (6.3, 2.46, 3.6), 0.34, 0.03, "neon_naranja", res=1)


@modelo(99, "especiales", "edificio_mediano", (4, 4, 18))
def torre_vigilancia(m):
    # Zócalo, fuste de cuatro pies con arriostrado y escalera con descansillos, garita con barandilla y foco giratorio
    m.caja((0, 0, 0.25), (4.0, 4.0, 0.5), "hormigon", bisel=0.06)
    def l(z):
        return 1.5 - 0.5 * (z / 13.5)
    esq = ((1, 1), (-1, 1), (-1, -1), (1, -1))
    for sx, sy in esq:
        m.barrido([(sx * l(0), sy * l(0), 0.5), (sx * l(13.5), sy * l(13.5), 13.6)], 0.13, "blanco_liso", seg=6)
        m.caja((sx * l(0), sy * l(0), 0.6), (0.5, 0.5, 0.2), "oscuro", bisel=0.04)
    niv = [0.5, 2.7, 4.9, 7.1, 9.3, 11.5, 13.6]
    for i in range(len(niv) - 1):
        z0, z1 = niv[i], niv[i + 1]
        for k in range(4):
            (ax, ay), (bx, by) = esq[k], esq[(k + 1) % 4]
            m.barrido([(ax * l(z1), ay * l(z1), z1), (bx * l(z1), by * l(z1), z1)], 0.06, "gris_liso", seg=4)
            if k == 2:
                continue                                                           # el frente queda libre para la escalera
            if (i + k) % 2:
                m.barrido([(ax * l(z0), ay * l(z0), z0), (bx * l(z1), by * l(z1), z1)], 0.04, "acero", seg=4)
            else:
                m.barrido([(bx * l(z0), by * l(z0), z0), (ax * l(z1), ay * l(z1), z1)], 0.04, "acero", seg=4)
        m.tubo((0, 0, z1), 0.3, 0.06, 0.05, "neon", seg=8) if i in (1, 3) else None
    # Escalera de gato frontal con aros y descansillos cada dos tramos
    for s in (-1, 1):
        m.barrido([(s * 0.25, -l(0) - 0.05, 0.5), (s * 0.25, -l(13.5) - 0.05, 13.8)], 0.035, "acero", seg=5)
    for k in range(34):
        z = 0.8 + 0.385 * k
        m.cil((0, -l(z) - 0.05, z), 0.022, 0.5, "acero", eje="x", seg=4)
    for k in range(9):
        z = 3.0 + 1.2 * k
        y0 = -l(z) - 0.05
        m.barrido([(-0.25, y0, z)] + [(0.36 * math.sin(math.radians(a)) * -1, y0 - 0.3 - 0.34 * math.cos(math.radians(a)), z)
                                      for a in (-120, -60, 0, 60, 120)][::-1] + [(0.25, y0, z)], 0.018, "amarillo_p", seg=4) \
            if False else m.barrido([(-0.25, y0, z), (-0.36, y0 - 0.3, z), (-0.2, y0 - 0.6, z), (0.2, y0 - 0.6, z), (0.36, y0 - 0.3, z),
                                     (0.25, y0, z)], 0.018, "amarillo_p", seg=4)
    for z in (4.9, 9.3):
        m.caja((0, 0, z + 0.04), (2 * l(z) + 0.1, 2 * l(z) + 0.1, 0.06), "rejilla")
    # Plataforma superior con barandilla, garita acristalada y cubierta
    zp = 13.7
    m.caja((0, 0, zp), (4.0, 4.0, 0.2), "gris", bisel=0.04)
    m.caja((0, 0, zp + 0.11), (3.7, 3.7, 0.03), "rejilla")
    for sx, sy in esq:
        m.prisma([(0, 0), (0.9, 0), (0, -0.9)], -0.05, 0.05, "acero", "xz", c=(sx * 1.0, sy * 1.0, zp - 0.1),
                 rot=(0, 0, math.degrees(math.atan2(sy, sx))))
    P = [(-1.9, -1.9), (1.9, -1.9), (1.9, 1.9), (-1.9, 1.9)]
    for k in range(4):
        (ax, ay), (bx, by) = P[k], P[(k + 1) % 4]
        m.barandilla((ax, ay, zp + 0.1), (bx, by, zp + 0.1), 1.1, postes=4, travesanos=2, neon="neon" if k == 0 else None)
    m.caja((0, 0.2, zp + 0.55), (2.2, 2.2, 0.9), "blanco", bisel=0.04)
    for s in (-1, 1):
        m.caja((s * 1.1, 0.2, zp + 1.6), (0.05, 2.0, 1.2), "cristal")
        m.caja((0, 0.2 + s * 1.1, zp + 1.6), (2.0, 0.05, 1.2), "cristal")
        for t in (-1, 1):
            m.caja((s * 1.08, 0.2 + t * 1.08, zp + 1.6), (0.14, 0.14, 1.24), "blanco_liso")
    m.torno((0, 0.2, zp + 2.2), [(1.75, 0), (1.75, 0.12), (0.5, 0.6), (0, 0.66)], "gris", seg=4, rot=(0, 0, 45))
    m.torno((0, 0.2, zp + 2.16), [(1.78, 0), (1.78, 0.05)], "neon", seg=4, rot=(0, 0, 45))
    # Foco giratorio sobre la cubierta (pieza aparte) con haz de luz
    F = "foco"
    zf = zp + 2.9
    m.cil((0, 0.2, zf), 0.2, 0.3, "oscuro", seg=10)
    for s in (-1, 1):
        m.caja((s * 0.36, 0.2, zf + 0.5), (0.06, 0.16, 0.8), "acero", p=F)
    m.caja((0, 0.2, zf + 0.14), (0.8, 0.2, 0.08), "acero", p=F)
    m.cil((0, 0.1, zf + 0.6), 0.32, 0.6, "gris_liso", eje="y", seg=14, rot=(-12, 0, 0), p=F)
    m.torno((0, -0.2, zf + 0.54), [(0.32, 0), (0.38, 0.1), (0.36, 0.12)], "acero", seg=14, eje="y", rot=(168, 0, 0), p=F) \
        if False else None
    m.cil((0, -0.21, zf + 0.535), 0.28, 0.04, "neon_blanco", eje="y", seg=14, rot=(-12, 0, 0), p="foco_neon")
    m.tubo((0, -0.2, zf + 0.535), 0.34, 0.08, 0.05, "acero", eje="y", seg=14, rot=(-12, 0, 0), p=F)
    m.anclaje("haz_foco", (0, -0.25, zf + 0.53))
    m.cil((1.3, 1.5, zp + 2.6), 0.03, 1.6, "acero", seg=5)
    m.esfera((1.3, 1.5, zp + 3.42), 0.08, "neon_rojo", seg=6, anillos=4)


@modelo(100, "especiales", "edificio_grande", (8, 2, 10))
def portal_espacial(m):
    # Plataforma de embarque con escalones, arco tecnológico en anillo, anillo de energía y velo luminoso (aparte)
    m.caja((0, 0, 0.2), (8.0, 2.0, 0.4), "oscuro", bisel=0.06)
    m.caja((0, 0, 0.5), (6.6, 1.8, 0.2), "gris", bisel=0.04)
    m.caja((0, 0, 0.61), (4.4, 1.5, 0.03), "rejilla")
    for s in (-1, 1):
        m.caja((0, s * 0.92, 0.5), (5.6, 0.04, 0.08), "neon")
        m.caja((s * 3.6, 0, 0.45), (0.6, 2.0, 0.5), "rayas")
    for k in range(2):
        m.caja((0, -1.0 - 0.0, 0.1 + 0.2 * k), (3.4 - 0.4 * k, 0.5 - 0.2 * k, 0.2), "gris_liso") if False else None
    cz, R = 5.3, 3.9
    # Anillo estructural por dovelas tecnológicas
    n = 20
    for k in range(n):
        a0, a1 = 360 * k / n - 90, 360 * (k + 1) / n - 90
        if -90 <= a0 < -72 or -108 <= a0 < -90 + 360 * 0 and False:
            pass
        d = arco_pts(R + 0.5, R - 0.25, a0 + 0.8, a1 - 0.8, 2, 0, cz)
        m.prisma(d, -0.42, 0.42, "blanco" if k % 2 else "gris", "xz")
        am = math.radians((a0 + a1) / 2)
        m.caja(((R + 0.52) * math.cos(am), 0, cz + (R + 0.52) * math.sin(am)), (0.5, 0.96, 0.16), "oscuro",
               rot=(0, 90 - (a0 + a1) / 2, 0), bisel=0.03)
        if k % 2 == 0:
            for s in (-1, 1):
                m.caja(((R + 0.12) * math.cos(am), s * 0.43, cz + (R + 0.12) * math.sin(am)), (0.14, 0.03, 0.5), "neon",
                       rot=(0, 90 - (a0 + a1) / 2, 0))
    # Anillo de energía (neón) por dentro y velo del portal
    m.toro((0, 0, cz), R - 0.38, 0.14, "neon", eje="y", seg=40, seg2=8, p="anillo_neon")
    m.toro((0, 0, cz), R - 0.7, 0.05, "neon_blanco", eje="y", seg=40, seg2=5)
    m.cil((0, 0, cz), R - 0.72, 0.05, "neon", eje="y", seg=40, p="velo_neon")
    for r in (1.0, 2.0, 2.8):
        m.toro((0, 0, cz), r, 0.03, "neon_blanco", eje="y", seg=32, seg2=4, esc=(1, 1.0, 1), p="ondas_neon")
    m.anclaje("centro_portal", (0, 0, cz))
    # Contrafuertes laterales con acumuladores y cables de alimentación
    for s in (-1, 1):
        m.prisma([(s * 2.6, 0.6), (s * 3.9, 0.6), (s * 3.9, 3.4), (s * 3.55, 4.4), (s * 3.3, 2.6)], -0.6, 0.6, "gris", "xz")
        m.prisma([(s * 3.92, 0.6), (s * 3.98, 0.6), (s * 3.98, 3.4), (s * 3.92, 3.4)], -0.5, 0.5, "acento", "xz")
        m.cil((s * 3.4, 0, 1.6), 0.36, 1.6, "cristal", eje="z", seg=10) if False else None
        for y in (-0.75, 0.75):
            m.cil((s * 3.3, y, 1.5), 0.2, 1.7, "oscuro", seg=10)
            m.cil((s * 3.3, y, 1.5), 0.215, 1.0, "neon", seg=10)
            m.torno((s * 3.3, y, 2.35), [(0.22, 0), (0.12, 0.14), (0, 0.16)], "acero", seg=10)
            m.barrido([(s * 3.3, y, 2.5), (s * 3.5, y * 0.9, 3.3), (s * 3.75, y * 0.6, 4.3)], 0.05, "goma", seg=5)
    # Remate superior con emisor y antenas
    m.caja((0, 0, cz + R + 0.75), (1.6, 1.0, 0.5), "oscuro", bisel=0.08)
    m.torno((0, 0, cz + R + 1.0), [(0.3, 0), (0.16, 0.2), (0.05, 0.3), (0, 0.6)], "acero", seg=8)
    m.esfera((0, 0, cz + R + 1.55), 0.12, "neon", seg=8, anillos=5)
    for s in (-1, 1):
        m.cil((s * 0.6, 0, cz + R + 1.2), 0.025, 0.6, "acero", seg=4)
    # Pedestal de control a un lado de la plataforma
    m.torno((2.6, -0.65, 0.6), [(0.2, 0), (0.1, 0.1), (0.08, 0.9), (0.16, 1.0)], "gris_liso", seg=8)
    m.caja((2.6, -0.7, 1.68), (0.5, 0.3, 0.06), "oscuro", rot=(25, 0, 0))
    m.caja((2.6, -0.71, 1.71), (0.4, 0.22, 0.02), "neon", rot=(25, 0, 0), p="pantalla_neon")
