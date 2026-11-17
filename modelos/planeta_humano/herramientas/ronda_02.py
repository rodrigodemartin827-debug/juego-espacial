"""Ronda 2 · Zona residencial (modelos 11-20)."""

import math

from geometria import arco_pts
from registro import modelo


def _esparcir_hojas(m, n, punto, largo, ancho, mat, p=None, subir=35):
    """Reparte hojas sobre una superficie. `punto(u, v)` devuelve (posición, acimut en radianes)."""
    R = m.rng
    for _ in range(n):
        pos, az = punto(R.random(), R.random())
        m.hoja(pos, largo * R.uniform(0.75, 1.25), ancho * R.uniform(0.8, 1.2), mat,
               rot=(R.uniform(-35, 35), -R.uniform(subir - 25, subir + 25), math.degrees(az) + R.uniform(-30, 30)), p=p)


@modelo(11, "residencial", "vegetacion", (3, 3, 12))
def arbol_cipreses_espacial(m):
    R = m.rng
    # Tronco metálico-orgánico: fuste con anillos y raíces que se abren
    m.torno((0, 0, 0), [(0.62, 0), (0.5, 0.25), (0.36, 0.9), (0.3, 2.2), (0.24, 4.5), (0.12, 8.0), (0.0, 9.0)],
            "corteza_gris", seg=10)
    for k in range(5):
        a = math.radians(72 * k + 10)
        m.barrido([(0.28 * math.cos(a), 0.28 * math.sin(a), 0.9), (0.6 * math.cos(a), 0.6 * math.sin(a), 0.25),
                   (1.05 * math.cos(a), 1.05 * math.sin(a), 0.03)], [0.14, 0.13, 0.05], "corteza_gris", seg=5)
    for z, r in ((1.3, 0.37), (1.75, 0.35)):
        m.tubo((0, 0, z), r + 0.03, 0.12, 0.06, "acero", seg=10)
    m.tubo((0, 0, 1.52), 0.37, 0.1, 0.04, "neon", seg=10)
    # Copa en huso: masas de follaje apiladas
    def radio(t):
        return 1.32 * math.sin(math.pi * min(1.0, t * 0.93 + 0.07)) ** 0.75
    z0, z1 = 2.3, 11.7
    for i in range(5):
        t = (i + 0.5) / 5
        z = z0 + (z1 - z0) * t
        r = radio(t) * 0.9
        m.ico((R.uniform(-0.06, 0.06), R.uniform(-0.06, 0.06), z), 1.0, "hoja2", sub=2,
              esc=(r, r, 1.25), ruido=0.22, frec=1.6, semilla=i * 1.7, rot=(0, 0, i * 37))
    m.torno((0, 0, 11.2), [(0.42, 0), (0.25, 0.45), (0.0, 0.8)], "hoja2", seg=6)
    # Hojas con volumen: verdes azuladas, y algunas luminosas (pieza de neón tenue)
    def punto(u, v):
        t = 0.03 + 0.94 * u
        a = 2 * math.pi * v
        r = radio(t) * 0.92
        return (r * math.cos(a), r * math.sin(a), z0 + (z1 - z0) * t), a
    _esparcir_hojas(m, 130, punto, 0.62, 0.26, "hoja_azul", subir=58)
    _esparcir_hojas(m, 50, punto, 0.6, 0.24, "hoja_cyan", subir=62)
    _esparcir_hojas(m, 34, punto, 0.5, 0.18, "neon", subir=66)


@modelo(12, "residencial", "vegetacion", (6, 6, 8))
def arbol_frutal(m):
    R = m.rng
    # Tronco retorcido con corteza modelada: nervios en relieve a lo largo del fuste
    eje = [(0, 0, 0), (0.08, 0.02, 0.8), (-0.06, 0.1, 1.7), (0.1, -0.04, 2.6), (0.05, 0.05, 3.4)]
    m.barrido(eje, [0.55, 0.42, 0.36, 0.33, 0.3], "corteza", seg=10)
    for k in range(9):
        a = math.radians(40 * k + R.uniform(-8, 8))
        rs = [0.5, 0.4, 0.35, 0.31, 0.27]
        pts = [(x + rs[i] * math.cos(a + 0.25 * i), y + rs[i] * math.sin(a + 0.25 * i), z + (0.02 if i == 0 else 0))
               for i, (x, y, z) in enumerate(eje)]
        m.barrido(pts, [0.09, 0.075, 0.065, 0.06, 0.04], "corteza", seg=4)
    for k in range(5):
        a = math.radians(72 * k + 20)
        m.barrido([(0.3 * math.cos(a), 0.3 * math.sin(a), 0.55), (0.75 * math.cos(a), 0.75 * math.sin(a), 0.12),
                   (1.15 * math.cos(a), 1.15 * math.sin(a), 0.02)], [0.2, 0.14, 0.05], "corteza", seg=5)
    m.ico((0.34, -0.1, 1.5), 0.14, "corteza", sub=1, esc=(1, 0.8, 1.3), ruido=0.2)   # nudo
    # Ramas principales
    ramas = [((1.9, 0.3, 5.0), 0.0), ((-1.6, 1.0, 5.2), 2.0), ((-0.6, -1.8, 5.0), 4.0), ((0.9, 1.7, 5.5), 1.0),
             ((0.1, 0.1, 6.0), 3.0)]
    for (x, y, z), s in ramas:
        mid = (x * 0.45 + 0.05, y * 0.45, 3.4 + (z - 3.4) * 0.6)
        m.barrido([(0.05, 0.05, 3.2), mid, (x, y, z)], [0.24, 0.16, 0.07], "corteza", seg=6)
    # Copa: masas de follaje y hojas sueltas
    copas = [((1.9, 0.3, 5.6), 1.5), ((-1.6, 1.0, 5.8), 1.5), ((-0.6, -1.8, 5.5), 1.4), ((0.9, 1.7, 6.0), 1.3),
             ((0.1, 0.0, 6.7), 1.6)]
    for i, (c, r) in enumerate(copas):
        m.ico(c, r, "hoja", sub=2, esc=(1, 1, 0.8), ruido=0.28, semilla=i * 2.3)
    def punto(u, v):
        c, r = copas[int(u * len(copas)) % len(copas)]
        a = 2 * math.pi * v
        e = math.radians(R.uniform(-25, 80))
        return (c[0] + r * 0.98 * math.cos(a) * math.cos(e), c[1] + r * 0.98 * math.sin(a) * math.cos(e),
                c[2] + r * 0.8 * math.sin(e)), a
    _esparcir_hojas(m, 90, punto, 0.6, 0.3, "hoja_clara", subir=25)
    _esparcir_hojas(m, 45, punto, 0.55, 0.28, "hoja2", subir=20)
    # Frutas esféricas colgando de su rabito (naranjas y rojas)
    naranja, roja = m.color("#F28C1E", 0.45), m.color("#C4261E", 0.35)
    for i in range(16):
        c, r = copas[i % len(copas)]
        a = R.uniform(0, 6.28)
        d = r * R.uniform(0.55, 0.95)
        x, y = c[0] + d * math.cos(a), c[1] + d * math.sin(a)
        z = c[2] - r * 0.8 * math.sqrt(max(0.05, 1 - (d / r) ** 2)) - 0.05
        m.cil((x, y, z - 0.08), 0.02, 0.22, "corteza", seg=4)
        m.esfera((x, y, z - 0.36), 0.2, naranja if i % 2 else roja, seg=8, anillos=6, esc=(1, 1, 0.92))
        m.cil((x, y, z - 0.185), 0.035, 0.03, "hoja2", seg=5)


@modelo(13, "residencial", "vegetacion", (2, 2, 1.5))
def arbusto_luminoso(m):
    R = m.rng
    # Ramas leñosas desde el suelo, masas de hojas y bayas luminosas en sus tallos
    for k in range(6):
        a = math.radians(60 * k + 15)
        m.barrido([(0.08 * math.cos(a), 0.08 * math.sin(a), 0), (0.3 * math.cos(a), 0.3 * math.sin(a), 0.45),
                   (0.55 * math.cos(a), 0.55 * math.sin(a), 0.9)], [0.06, 0.045, 0.02], "corteza", seg=5)
    masas = [((0, 0, 0.75), 0.62), ((0.42, 0.2, 0.6), 0.48), ((-0.4, 0.25, 0.62), 0.5), ((0.05, -0.45, 0.58), 0.48),
             ((-0.1, 0.1, 1.05), 0.42)]
    for i, (c, r) in enumerate(masas):
        m.ico(c, r, "hoja2", sub=2 if i < 4 else 1, esc=(1, 1, 0.82), ruido=0.25, semilla=i * 3.1)
    def punto(u, v):
        c, r = masas[int(u * len(masas)) % len(masas)]
        a = 2 * math.pi * v
        e = math.radians(R.uniform(-10, 85))
        return (c[0] + r * math.cos(a) * math.cos(e), c[1] + r * math.sin(a) * math.cos(e),
                c[2] + r * 0.82 * math.sin(e)), a
    _esparcir_hojas(m, 90, punto, 0.36, 0.17, "hoja", subir=30)
    _esparcir_hojas(m, 45, punto, 0.34, 0.16, "hoja_azul", subir=30)
    for i in range(16):
        c, r = masas[i % len(masas)]
        a = R.uniform(0, 6.28)
        e = math.radians(R.uniform(15, 80))
        d = (math.cos(a) * math.cos(e), math.sin(a) * math.cos(e), math.sin(e))
        p0 = (c[0] + r * 0.8 * d[0], c[1] + r * 0.8 * d[1], c[2] + r * 0.7 * d[2])
        p1 = (c[0] + r * 1.18 * d[0], c[1] + r * 1.18 * d[1], c[2] + r * 1.0 * d[2])
        m.barrido([p0, p1], 0.012, "corteza", seg=3)
        m.esfera(p1, 0.075, "neon", seg=6, anillos=4)


@modelo(14, "residencial", "vegetacion", (8, 8, 0.5))
def cesped_modular(m):
    R = m.rng
    # Placa de tierra con borde y capa de césped; encima, mechones de briznas con volumen
    m.caja((0, 0, 0.08), (8, 8, 0.16), "tierra")
    m.caja((0, 0, 0.19), (7.96, 7.96, 0.06), "cesped")
    for i in range(26):
        for j in range(26):
            if R.random() < 0.14:
                continue
            x = -3.85 + 7.7 * (i + R.uniform(0.15, 0.85)) / 26
            y = -3.85 + 7.7 * (j + R.uniform(0.15, 0.85)) / 26
            h = R.uniform(0.14, 0.28)
            mat = "cesped" if R.random() < 0.7 else "hoja_clara"
            m.brizna((x, y, 0.21), h, R.uniform(0.07, 0.11), mat, inclin=(R.uniform(-0.1, 0.1), R.uniform(-0.1, 0.1)),
                     giro=R.uniform(0, 6.28))
    # Matas más altas y un par de piedras
    for _ in range(26):
        x, y = R.uniform(-3.6, 3.6), R.uniform(-3.6, 3.6)
        for k in range(4):
            a = k * 1.57 + R.uniform(-0.4, 0.4)
            m.brizna((x + 0.06 * math.cos(a), y + 0.06 * math.sin(a), 0.21), R.uniform(0.22, 0.29), 0.06, "hoja",
                     inclin=(0.16 * math.cos(a), 0.16 * math.sin(a)), giro=a)
    for (x, y, s) in ((-2.4, 1.7, 0.5), (2.9, -2.2, 0.38), (0.6, 3.1, 0.3)):
        m.roca((x, y, 0.24), (s, s * 0.8, s * 0.45), "piedra", semilla=x, sub=1)


@modelo(15, "residencial", "prop", (4, 1, 1.5))
def jardinera(m):
    R = m.rng
    # Cubeta metálica con paredes de grosor, patas, tierra y plantas
    m.bloque((-2.0, -0.5, 0.12), (2.0, 0.5, 0.2), "gris_liso")
    for y in (-0.46, 0.46):
        m.caja((0, y, 0.46), (4.0, 0.08, 0.6), "blanco_liso", bisel=0.015)
    for x in (-1.96, 1.96):
        m.caja((x, 0, 0.46), (0.08, 0.84, 0.6), "blanco_liso", bisel=0.015)
    m.bloque((-2.03, -0.53, 0.72), (2.03, -0.41, 0.8), "gris_liso")
    m.bloque((-2.03, 0.41, 0.72), (2.03, 0.53, 0.8), "gris_liso")
    m.bloque((-2.03, -0.41, 0.72), (-1.91, 0.41, 0.8), "gris_liso")
    m.bloque((1.91, -0.41, 0.72), (2.03, 0.41, 0.8), "gris_liso")
    for x in (-1.7, 1.7):
        for y in (-0.36, 0.36):
            m.caja((x, y, 0.06), (0.2, 0.14, 0.12), "oscuro")
    m.caja((0, -0.505, 0.4), (3.4, 0.03, 0.06), "neon")
    m.caja((0, -0.5, 0.56), (3.6, 0.03, 0.05), "acento")
    m.bloque((-1.92, -0.42, 0.2), (1.92, 0.42, 0.68), "tierra")
    # Plantas: matas de hojas largas, dos arbustitos y flores
    for i, x in enumerate((-1.55, -0.5, 0.55, 1.5)):
        y = R.uniform(-0.1, 0.1)
        for k in range(9):
            a = k * 0.7 + i
            m.hoja((x + 0.05 * math.cos(a), y + 0.05 * math.sin(a), 0.68), R.uniform(0.5, 0.8), 0.16,
                   "hoja" if k % 3 else "hoja_clara", rot=(R.uniform(-20, 20), -R.uniform(45, 75), math.degrees(a)))
    for x in (-1.05, 1.05):
        m.ico((x, 0.05, 0.9), 0.3, "hoja2", sub=1, esc=(1, 0.9, 0.85), ruido=0.3, semilla=x)
        for k in range(12):
            a, e = R.uniform(0, 6.28), R.uniform(0.1, 1.4)
            m.hoja((x + 0.28 * math.cos(a) * math.cos(e), 0.05 + 0.25 * math.sin(a) * math.cos(e), 0.9 + 0.25 * math.sin(e)),
                   0.22, 0.11, "hoja_clara", rot=(0, -40, math.degrees(a)))
    petalo = m.color("#F3F0E8", 0.6)
    for x, y, h in ((0.0, 0.12, 1.42), (0.22, -0.15, 1.25), (-0.22, -0.08, 1.33)):
        m.barrido([(x, y, 0.68), (x + 0.03, y, (0.68 + h) / 2), (x, y, h)], 0.018, "hoja", seg=4)
        m.esfera((x, y, h + 0.02), 0.055, m.color("#F2C230", 0.6), seg=6, anillos=4)
        for k in range(6):
            m.hoja((x, y, h), 0.15, 0.08, petalo, rot=(0, -15, 60 * k))


@modelo(16, "residencial", "prop", (4, 0.3, 3))
def valla_residencial(m):
    # Dos postes con capitel luminoso, zócalo, largueros y lamas verticales
    for x in (-1.85, 1.85):
        m.caja((x, 0, 1.4), (0.3, 0.3, 2.8), "blanco_liso", bisel=0.04)
        m.caja((x, 0, 0.12), (0.3, 0.3, 0.24), "oscuro")
        m.caja((x, 0, 2.8), (0.3, 0.3, 0.08), "gris_liso")
        m.caja((x, 0, 2.88), (0.2, 0.2, 0.1), "neon")
        m.caja((x, 0, 2.96), (0.26, 0.26, 0.06), "gris_liso", bisel=0.02)
        m.caja((x, -0.152, 1.8), (0.1, 0.02, 0.9), "acento")
    m.caja((0, 0, 0.16), (3.4, 0.2, 0.22), "gris_liso")
    for z in (0.5, 1.5, 2.45):
        m.caja((0, 0, z), (3.4, 0.14, 0.12), "blanco_liso", bisel=0.02)
    for i in range(11):
        x = -1.5 + 0.3 * i
        m.caja((x, 0, 1.5), (0.14, 0.06, 2.1), "blanco_liso")
        m.prisma([(-0.07, 0), (0.07, 0), (0, 0.12)], -0.03, 0.03, "blanco_liso", "xz", c=(x, 0, 2.55))
    for x in (-1.6, 1.6):
        for z in (0.5, 1.5, 2.45):
            m.cil((x, -0.08, z), 0.035, 0.03, "acero", eje="y", seg=6)


@modelo(17, "residencial", "prop", (1, 1, 3))
def buzon(m):
    # Pedestal, cuerpo de tapa curva con ranura, portezuela (pieza aparte), bandera y pantalla holográfica
    m.cil((0, 0, 0.05), 0.4, 0.1, "oscuro", seg=12)
    m.torno((0, 0, 0.1), [(0.22, 0), (0.12, 0.15), (0.1, 1.1), (0.16, 1.25)], "gris_liso", seg=10)
    m.caja((0, 0, 1.31), (0.7, 0.8, 0.1), "gris_liso", bisel=0.02)
    cuerpo = [(-0.38, 1.36), (0.38, 1.36), (0.38, 1.85)] + \
             [(0.38 * math.cos(math.radians(a)), 1.85 + 0.3 * math.sin(math.radians(a))) for a in range(15, 180, 15)] + \
             [(-0.38, 1.85)]
    m.prisma(cuerpo, -0.44, 0.44, "blanco_liso", "xz")
    m.prisma(arco_pts(0.41, 0.36, 0, 180, 8, 0, 1.85, 1.0, 0.8), -0.47, -0.4, "acento", "xz")
    m.caja((0, -0.445, 1.98), (0.5, 0.03, 0.06), "negro")                      # ranura
    m.caja((0, -0.46, 2.03), (0.56, 0.06, 0.03), "gris_liso")                  # visera de la ranura
    m.caja((0, -0.455, 1.62), (0.6, 0.04, 0.42), "gris_claro", bisel=0.01, p="portezuela")
    m.cil((0.2, -0.49, 1.62), 0.035, 0.05, "acero", eje="y", seg=8, p="portezuela")
    m.caja((0, -0.48, 1.45), (0.3, 0.02, 0.04), "neon")
    # Bandera lateral
    m.cil((0.4, 0.1, 1.7), 0.04, 0.06, "acero", eje="x", seg=8)
    m.caja((0.43, 0.1, 1.95), (0.03, 0.06, 0.5), "acero", p="bandera")
    m.prisma([(-0.03, 2.05), (0.3, 2.13), (-0.03, 2.22)], 0.415, 0.445, "rojo_p", "yz", c=(0, 0.13, 0), p="bandera")
    # Proyector y pantalla holográfica flotante con icono de sobre
    m.cil((0, 0.1, 2.2), 0.14, 0.1, "oscuro", seg=10)
    m.cil((0, 0.1, 2.27), 0.09, 0.04, "neon", seg=10)
    m.caja((0, 0.1, 2.72), (0.72, 0.03, 0.5), "neon", p="pantalla_neon")
    m.marco((0, 0.08, 2.72), 0.8, 0.58, 0.03, 0.04, "neon", p="pantalla_neon")
    m.prisma([(-0.2, 2.62), (0.2, 2.62), (0.2, 2.84), (0, 2.71), (-0.2, 2.84)], 0.045, 0.075, "neon_blanco", "xz")
    m.prisma([(-0.2, 2.86), (0, 2.74), (0.2, 2.86), (0.2, 2.88), (-0.2, 2.88)], 0.045, 0.075, "neon_blanco", "xz")


@modelo(18, "residencial", "prop", (2, 1.5, 2.5))
def contenedor_basura(m):
    # Cuerpo troncocónico con nervios, tapa abatible (pieza aparte), bisagra, asa, pedal y cuatro ruedas
    cuerpo = [(-0.55, 0.3), (0.55, 0.3), (0.7, 2.0), (-0.7, 2.0)]
    m.prisma(cuerpo, -0.95, 0.95, "gris", "yz")
    m.prisma([(-0.6, 0.34), (0.6, 0.34), (0.6, 0.22), (-0.6, 0.22)], -0.9, 0.9, "oscuro", "yz")
    for x in (-0.6, 0.0, 0.6):
        m.prisma([(-0.59, 0.5), (-0.56, 0.5), (-0.69, 1.9), (-0.74, 1.9)], x - 0.05, x + 0.05, "gris_liso", "yz")
    m.bloque((-1.0, -0.76, 1.94), (1.0, 0.76, 2.06), "oscuro", bisel=0.02)
    m.caja((0, -0.66, 1.25), (1.0, 0.03, 0.34), "acento")
    for k in range(3):   # flechas de reciclaje simplificadas
        m.prisma([(-0.12, -0.07), (0.12, -0.07), (0, 0.1)], -0.02, 0.02, "neon", "xz",
                 c=(-0.28 + 0.28 * k, -0.69, 1.25), rot=(-5, 0, 0))
    # Tapa curva
    tapa = [(-0.78, 2.06)] + [(0.78 * math.cos(math.radians(a)) * -1, 2.06 + 0.36 * math.sin(math.radians(a)))
                               for a in range(15, 180, 15)] + [(0.78, 2.06)]
    m.prisma(tapa, -1.02, 1.02, "acento", "yz", p="tapa")
    m.caja((0, -0.8, 2.12), (0.9, 0.08, 0.06), "oscuro", p="tapa")
    m.cil((0, 0.78, 2.08), 0.06, 2.0, "acero", eje="x", seg=8)
    for x in (-0.7, 0.7):
        m.caja((x, 0.8, 1.95), (0.14, 0.1, 0.24), "oscuro")
    # Asa trasera
    m.barrido([(-0.7, 0.72, 1.7), (-0.7, 0.92, 1.75), (0.7, 0.92, 1.75), (0.7, 0.72, 1.7)], 0.035, "acero", seg=6)
    # Pedal
    m.barrido([(0, -0.5, 0.26), (0, -0.78, 0.14)], 0.03, "acero", seg=5)
    m.caja((0, -0.86, 0.12), (0.5, 0.2, 0.05), "rejilla", rot=(12, 0, 0), p="pedal")
    # Ruedas con horquilla
    for x in (-0.72, 0.72):
        for y in (-0.42, 0.42):
            m.caja((x, y, 0.2), (0.08, 0.26, 0.1), "acero")
            m.cil((x, y, 0.13), 0.13, 0.1, "goma", eje="x", seg=12)
            m.cil((x, y, 0.13), 0.06, 0.12, "acero", eje="x", seg=8)


@modelo(19, "residencial", "prop", (1, 1, 5))
def poste_indicador(m):
    # Base, poste con collarines, tres flechas 3D orientadas a zonas distintas y remate luminoso
    m.cil((0, 0, 0.06), 0.34, 0.12, "oscuro", seg=12)
    m.torno((0, 0, 0.12), [(0.2, 0), (0.1, 0.25), (0.075, 0.4)], "gris_liso", seg=10)
    m.cil((0, 0, 2.65), 0.07, 4.4, "blanco_liso", seg=10)
    flecha = [(-0.42, -0.19), (0.3, -0.19), (0.52, 0.0), (0.3, 0.19), (-0.42, 0.19)]
    datos = [(4.2, 20, "acento", "HANGAR"), (3.6, 150, "naranja_p", "FORJA"), (3.0, -95, "verde_p", "MERCADO")]
    for z, ang, mat, txt in datos:
        m.tubo((0, 0, z), 0.11, 0.3, 0.04, "acero", seg=10)
        m.prisma(flecha, -0.16, -0.09, "blanco_liso", "xz", c=(0, 0, z), rot=(0, 0, ang))
        m.prisma([(-0.42, -0.19), (-0.3, -0.19), (-0.3, 0.19), (-0.42, 0.19)], -0.17, -0.085, mat, "xz", c=(0, 0, z),
                 rot=(0, 0, ang))
        m.prisma([(0.3, -0.19), (0.52, 0.0), (0.3, 0.19), (0.34, 0.0)], -0.168, -0.085, mat, "xz", c=(0, 0, z),
                 rot=(0, 0, ang))
        a = math.radians(ang)
        # letras en relieve en la cara vista (por detrás, banda de color)
        m.texto(txt, (0.17 * math.sin(a), -0.17 * math.cos(a), z), 0.13, 0.02, "negro", rot=(0, 0, ang), res=1)
        m.prisma([(-0.28, -0.03), (0.28, -0.03), (0.28, 0.03), (-0.28, 0.03)], -0.092, -0.075, mat, "xz", c=(0, 0, z),
                 rot=(0, 0, ang))
    m.torno((0, 0, 4.85), [(0.07, 0), (0.12, 0.04), (0.12, 0.08)], "gris_liso", seg=10)
    m.cil((0, 0, 4.97), 0.1, 0.08, "neon", seg=10)
    m.torno((0, 0, 5.01), [(0.12, 0), (0.08, 0.04), (0, 0.07)], "gris_liso", seg=10)


@modelo(20, "residencial", "edificio_mediano", (10, 4, 3))
def puente_peatonal(m):
    def z(x):
        return 0.3 + 1.4 * (1 - (x / 5.0) ** 2)
    xs = [-5 + i for i in range(11)]
    # Tablero en arco: estructura metálica con una franja central de cristal pisable
    sup = [(x, z(x)) for x in xs]
    tablero = sup + [(x, z(x) - 0.22) for x in reversed(xs)]
    m.prisma(tablero, -2.0, -0.7, "gris", "xz")
    m.prisma(tablero, 0.7, 2.0, "gris", "xz")
    m.prisma([(x, zz - 0.03) for x, zz in sup] + [(x, z(x) - 0.15) for x in reversed(xs)], -0.7, 0.7, "cristal", "xz")
    for x in xs:
        m.caja((x, 0, z(x) - 0.14), (0.14, 1.5, 0.14), "acero", rot=(0, math.degrees(math.atan(0.56 * x / 5.0)), 0))
    # Arcos portantes laterales bajo el tablero y estribos
    for y in (-1.9, 1.9):
        arco = [(x, z(x) - 0.22) for x in xs] + [(x, (z(x) - 0.3) * 0.74 - 0.05) for x in reversed(xs)]
        arco[0] = (-5, 0.08); arco[-1] = (-5, 0.0); arco[10] = (5, 0.08); arco[11] = (5, 0.0)
        m.prisma(arco, y - 0.1, y + 0.1, "blanco_liso", "xz")
    for sx in (-1, 1):
        m.caja((sx * 4.75, 0, 0.16), (0.5, 4.0, 0.32), "hormigon", bisel=0.03)
        m.caja((sx * 4.2, 0, z(4.2) + 0.02), (0.9, 2.6, 0.04), "rejilla", rot=(0, sx * 26, 0))
    # Barandillas: montantes, paños de cristal, larguero y pasamanos luminoso
    for y in (-1.9, 1.9):
        for x in xs:
            m.caja((x, y, z(x) + 0.55), (0.12, 0.12, 1.1), "blanco_liso", bisel=0.02)
        for i in range(10):
            x0, x1 = xs[i], xs[i + 1]
            xm = (x0 + x1) / 2
            ang = -math.degrees(math.atan2(z(x1) - z(x0), 1.0))
            m.caja((xm, y, (z(x0) + z(x1)) / 2 + 0.52), (0.86, 0.05, 0.72), "cristal", rot=(0, ang, 0))
        m.barrido([(x, y, z(x) + 1.12) for x in xs], 0.07, "neon", seg=6)
        m.barrido([(x, y, z(x) + 0.12) for x in xs], 0.04, "acero", seg=5)
        for sx in (-1, 1):
            m.caja((sx * 5.0, y, z(5) + 0.7), (0.2, 0.2, 1.4), "gris_liso", bisel=0.03)
            m.caja((sx * 5.0, y, z(5) + 1.44), (0.14, 0.14, 0.1), "neon")
