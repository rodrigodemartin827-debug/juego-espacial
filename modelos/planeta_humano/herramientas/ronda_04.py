"""Ronda 4 · Zona comercial (modelos 31-40): puestos, banco, restaurante, cantina, clínica y mobiliario de mercado."""

import math

from geometria import arco_pts
from registro import modelo
from ronda_03 import _local, _frasco


def _puesto(m, lona, lona2=None, ancho=4.0, fondo=3.0):
    """Estructura de puesto: tarima, mostrador de madera, cuatro pies derechos y toldo inclinado con faldón."""
    a, f = ancho / 2, fondo / 2
    m.caja((0, 0, 0.06), (ancho, fondo, 0.12), "madera_oscura", bisel=0.02)
    for x in (-a + 0.12, a - 0.12):
        m.caja((x, -f + 0.5, 1.5), (0.14, 0.14, 2.8), "madera", bisel=0.02)
        m.caja((x, f - 0.15, 1.85), (0.14, 0.14, 3.5), "madera", bisel=0.02)
        m.caja((x, 0.15, 3.3), (0.1, fondo - 0.5, 0.1), "madera", rot=(-17, 0, 0))
    m.caja((0, f - 0.15, 3.55), (ancho - 0.2, 0.1, 0.1), "madera")
    m.caja((0, -f + 0.5, 2.9), (ancho - 0.2, 0.1, 0.1), "madera")
    # Toldo con grosor (baja hacia el frente) y faldón de picos
    lona2 = lona2 or lona
    n = 8
    for i in range(n):
        x0 = -a - 0.1 + (ancho + 0.2) * i / n
        x1 = x0 + (ancho + 0.2) / n
        mat = lona if i % 2 == 0 else lona2
        m.prisma([(-f - 0.05, 2.92), (f + 0.05, 3.9), (f + 0.05, 3.97), (-f - 0.05, 2.99)], x0, x1, mat, "yz")
        m.prisma([(x0, 2.99), (x1, 2.99), ((x0 + x1) / 2, 2.62)], -f - 0.09, -f - 0.03, mat, "xz")
    # Mostrador
    m.bloque((-a + 0.2, -f + 0.25, 0.12), (a - 0.2, -f + 1.25, 1.15), "madera_clara")
    m.bloque((-a + 0.12, -f + 0.15, 1.15), (a - 0.12, -f + 1.35, 1.25), "madera", bisel=0.02)
    for i in range(7):
        x = -a + 0.45 + (ancho - 0.9) * i / 6
        m.caja((x, -f + 0.235, 0.63), (0.05, 0.03, 1.0), "madera_oscura")
    return dict(zm=1.25, ym=-f + 0.75)


def _caja_madera(m, c, t, rot=(0, 0, 0), mat="madera_clara"):
    """Caja de fruta: fondo y cuatro paredes de listones con grosor."""
    x, y, z = c
    sx, sy, sz = t
    from mathutils import Euler, Vector
    E = Euler([math.radians(a) for a in rot], "XYZ").to_matrix()
    def pos(dx, dy, dz):
        v = E @ Vector((dx, dy, dz))
        return (x + v.x, y + v.y, z + v.z)
    m.caja(pos(0, 0, 0.03), (sx, sy, 0.06), mat, rot=rot)
    for s in (-1, 1):
        for k in range(2):
            h = 0.14 + k * (sz - 0.22)
            m.caja(pos(0, s * (sy / 2 - 0.03), h), (sx, 0.05, 0.16), mat, rot=rot)
            m.caja(pos(s * (sx / 2 - 0.03), 0, h), (0.05, sy - 0.1, 0.16), mat, rot=rot)
        for s2 in (-1, 1):
            m.caja(pos(s * (sx / 2 - 0.05), s2 * (sy / 2 - 0.05), sz / 2), (0.07, 0.07, sz), "madera", rot=rot)
    return pos


@modelo(31, "comercial", "edificio_mediano", (4, 3, 4))
def puesto_fruta(m):
    R = m.rng
    P = _puesto(m, "tela_roja", "tela_blanca")
    zm, ym = P["zm"], P["ym"]
    naranja, manzana, uva = m.color("#F28C1E", 0.5), m.color("#C4261E", 0.3), m.color("#6B2D8F", 0.35)
    verde = m.color("#8DBF3A", 0.4)
    # Tres cajas inclinadas hacia el cliente, llenas de fruta esférica (dos capas)
    for (cx, mat, r) in ((-1.25, naranja, 0.15), (0.0, manzana, 0.14), (1.25, verde, 0.13)):
        pos = _caja_madera(m, (cx, ym, zm + 0.12), (1.1, 0.9, 0.42), rot=(-16, 0, 0))
        n = 0
        for capa in range(2):
            paso = r * 1.95
            nx, ny = int(0.95 / paso), int(0.75 / paso)
            for i in range(nx):
                for j in range(ny):
                    if capa == 1 and (i + j) % 2 == 0:
                        continue
                    dx = (i - (nx - 1) / 2) * paso + (paso / 2 if capa else 0) * 0.6
                    dy = (j - (ny - 1) / 2) * paso
                    m.esfera(pos(dx + R.uniform(-0.01, 0.01), dy, 0.2 + capa * r * 1.45), r, mat, seg=8, anillos=5,
                             esc=(1, 1, 0.92), rot=(R.uniform(-20, 20), R.uniform(-20, 20), 0))
                    if capa == 1:
                        p = pos(dx, dy, 0.2 + capa * r * 1.45 + r * 0.9)
                        m.cil(p, 0.015, 0.05, "corteza", seg=4)
    # Racimos de uvas colgando del travesaño delantero y un cesto con más uvas
    for cx in (-1.4, -0.5, 0.6, 1.5):
        m.cil((cx, -1.0, 2.75), 0.012, 0.25, "corteza", seg=4)
        for k in range(14):
            fila = k // 4
            a = k * 1.9
            rr = 0.11 - fila * 0.022
            m.esfera((cx + rr * math.cos(a), -1.0 + rr * math.sin(a), 2.58 - 0.085 * fila - 0.02 * (k % 2)), 0.055,
                     uva if cx != 0.6 else verde, seg=6, anillos=4)
        m.hoja((cx, -1.0, 2.66), 0.2, 0.16, "hoja", rot=(0, 20, cx * 80))
    # Balanza, cartel de precio y cajas vacías apiladas detrás
    m.caja((1.65, ym - 0.3, zm + 0.06), (0.3, 0.3, 0.12), "acero", bisel=0.02)
    m.cil((1.65, ym - 0.3, zm + 0.2), 0.03, 0.2, "acero", seg=6)
    m.torno((1.65, ym - 0.3, zm + 0.3), [(0.04, 0), (0.2, 0.05), (0.21, 0.08), (0.04, 0.03)], "cobre", seg=10, cerrar=True)
    m.caja((-1.75, ym - 0.42, zm + 0.2), (0.3, 0.03, 0.22), "plastico_negro")
    m.caja((-1.75, ym - 0.44, zm + 0.22), (0.2, 0.02, 0.05), "neon")
    _caja_madera(m, (-1.2, 0.9, 0.12), (1.0, 0.8, 0.4))
    pos = _caja_madera(m, (-1.15, 0.92, 0.54), (1.0, 0.8, 0.4), rot=(0, 0, 12))
    for i in range(3):
        for j in range(2):
            m.esfera(pos(-0.3 + 0.3 * i, -0.15 + 0.3 * j, 0.2), 0.14, naranja, seg=8, anillos=5)
    m.caja((1.1, 0.9, 0.42), (0.9, 0.9, 0.6), "madera", bisel=0.02)


@modelo(32, "comercial", "edificio_mediano", (4, 3, 4))
def puesto_comida(m):
    P = _puesto(m, "tela_naranja", "tela_amarilla")
    zm, ym = P["zm"], P["ym"]
    # Plancha con dos fogones encendidos y dos ollas de pared gruesa con su guiso
    m.caja((-0.6, ym + 0.05, zm + 0.1), (2.2, 0.8, 0.2), "hierro", bisel=0.02)
    for cx, r, caldo in ((-1.15, 0.36, "#B5532A"), (-0.15, 0.3, "#D9B23C")):
        m.tubo((cx, ym + 0.05, zm + 0.22), r * 0.8, 0.05, 0.08, "neon_naranja", seg=12)
        m.torno((cx, ym + 0.05, zm + 0.26), [(r * 0.85, 0), (r, 0.06), (r, 0.5), (r + 0.04, 0.54), (r - 0.05, 0.54),
                                             (r - 0.05, 0.1), (0, 0.08)], "acero", seg=14)
        m.cil((cx, ym + 0.05, zm + 0.7), r - 0.05, 0.04, m.color(caldo, 0.4), seg=12)
        for s in (-1, 1):
            m.barrido([(cx + s * r, ym - 0.03, zm + 0.68), (cx + s * (r + 0.12), ym + 0.05, zm + 0.68),
                       (cx + s * r, ym + 0.13, zm + 0.68)], 0.022, "acero", seg=5)
        m.anclaje(f"vapor_olla_{'a' if cx < -0.5 else 'b'}", (cx, ym + 0.05, zm + 0.85))
    # Cucharón apoyado en la olla grande
    m.barrido([(-1.1, ym, zm + 0.72), (-0.85, ym - 0.2, zm + 1.2)], 0.018, "acero", seg=5)
    m.esfera((-1.1, ym, zm + 0.72), 0.08, "acero", seg=8, anillos=5, esc=(1, 1, 0.6))
    # Pila de platos, cuencos y servilletero
    for k in range(7):
        m.torno((0.85, ym - 0.1, zm + 0.03 * k), [(0.1, 0), (0.24, 0.025), (0.25, 0.04), (0.1, 0.02)],
                "plastico", seg=12, cerrar=True)
    for k in range(4):
        m.torno((1.45, ym - 0.1, zm + 0.05 * k), [(0.07, 0), (0.17, 0.1), (0.18, 0.12), (0.15, 0.1), (0.06, 0.02)],
                m.color("#2BB6C4", 0.35), seg=10, cerrar=True)
    m.caja((1.5, ym + 0.35, zm + 0.1), (0.3, 0.16, 0.2), "acero", bisel=0.02)
    m.caja((1.5, ym + 0.35, zm + 0.22), (0.24, 0.05, 0.1), "tela_blanca")
    # Botes de salsa y tabla con brochetas
    for i, col in enumerate(("#C8352B", "#E6B422", "#3E9B4F")):
        m.torno((0.3 + 0.16 * i, ym + 0.42, zm), [(0.06, 0), (0.06, 0.2), (0.02, 0.28), (0.0, 0.3)], m.color(col, 0.4),
                seg=8)
    m.caja((0.45, ym - 0.32, zm + 0.025), (0.6, 0.28, 0.05), "madera_clara", bisel=0.01)
    for i in range(4):
        m.cil((0.25 + 0.13 * i, ym - 0.32, zm + 0.08), 0.008, 0.5, "madera", eje="y", seg=4)
        for k in range(3):
            m.caja((0.25 + 0.13 * i, ym - 0.42 + 0.1 * k, zm + 0.08), (0.07, 0.07, 0.06),
                   m.color("#8A4A2A" if k % 2 else "#C8352B", 0.6), bisel=0.012)
    # Campana extractora con tubo y pizarra de menú luminosa
    m.prisma([(-0.6, 2.25), (0.6, 2.25), (0.3, 2.75), (-0.3, 2.75)], -1.6, 0.3, "acero", "yz", c=(0, ym + 0.05, 0))
    m.cil((-0.65, ym + 0.05, 3.3), 0.16, 1.2, "acero", seg=10)
    m.torno((-0.65, ym + 0.05, 3.9), [(0.24, 0), (0.24, 0.05), (0, 0.22)], "hierro", seg=10)
    m.anclaje("humo_chimenea", (-0.65, ym + 0.05, 4.15))
    m.caja((1.2, 1.3, 2.3), (1.2, 0.08, 0.9), "plastico_negro", bisel=0.02)
    m.texto("MENU", (1.2, 1.24, 2.5), 0.22, 0.03, "neon_naranja")
    for k in range(3):
        m.caja((1.15 - 0.05 * k, 1.245, 2.25 - 0.13 * k), (0.8 - 0.1 * k, 0.02, 0.04), "neon")
    m.bloque((0.8, 0.7, 0.12), (1.7, 1.3, 0.8), "gris_liso", bisel=0.03)   # bombona de gas en su cajón
    m.torno((-1.4, 1.0, 0.12), [(0.26, 0), (0.28, 0.1), (0.28, 0.8), (0.14, 0.98), (0.08, 1.0), (0.08, 1.1), (0, 1.1)],
            "naranja_p", seg=12)


@modelo(33, "comercial", "edificio_mediano", (4, 3, 4))
def puesto_telas(m):
    R = m.rng
    P = _puesto(m, "tela_morada", "tela_cyan")
    zm, ym = P["zm"], P["ym"]
    telas = ["tela_roja", "tela_azul", "tela_verde", "tela_amarilla", "tela_morada", "tela_cyan", "tela_naranja",
             "tela_blanca"]
    # Rollos de tela en pirámide sobre el mostrador (cilindros con canutillo de cartón)
    k = 0
    for fila, n in enumerate((5, 4, 3)):
        for i in range(n):
            x = -0.72 + 0.36 * i + 0.18 * fila - 0.5
            z = zm + 0.17 + 0.3 * fila
            m.cil((x, ym, z), 0.17, 1.0, telas[k % 8], eje="y", seg=10)
            m.cil((x, ym, z), 0.05, 1.08, "madera_clara", eje="y", seg=6)
            k += 1
    # Dos rollos de pie en el suelo y telas dobladas
    for x, mat in ((1.75, "tela_roja"), (1.45, "tela_amarilla")):
        m.cil((x, -1.6 + 0.2 * (x < 1.6), 0.82), 0.16, 1.4, mat, seg=10, rot=(6, 0, 0))
        m.cil((x, -1.6 + 0.2 * (x < 1.6), 0.82), 0.05, 1.5, "madera_clara", seg=6, rot=(6, 0, 0))
    for i in range(5):
        m.caja((1.3, ym, zm + 0.045 + 0.09 * i), (0.7 - 0.02 * i, 0.6, 0.085), telas[(i + 3) % 8], bisel=0.025,
               rot=(0, 0, R.uniform(-6, 6)))
    # Barra con perchas y prendas colgadas (cada prenda con su grosor)
    m.cil((0, 0.9, 2.75), 0.035, 3.7, "acero", eje="x", seg=8)
    prendas = [(-1.4, "tela_azul", 0), (-0.75, "tela_roja", 1), (-0.1, "tela_verde", 0), (0.55, "tela_blanca", 1),
               (1.2, "tela_naranja", 0)]
    for x, mat, tipo in prendas:
        m.barrido([(x, 0.9, 2.79), (x, 0.9, 2.7), (x - 0.3, 0.9, 2.52), (x + 0.3, 0.9, 2.52), (x, 0.9, 2.7)], 0.015,
                  "acero", seg=4)
        if tipo == 0:   # camisa
            m.prisma([(-0.3, 2.55), (-0.1, 2.6), (0.1, 2.6), (0.3, 2.55), (0.52, 2.2), (0.4, 2.12), (0.28, 2.3),
                      (0.3, 1.6), (-0.3, 1.6), (-0.28, 2.3), (-0.4, 2.12), (-0.52, 2.2)], -0.05, 0.05, mat, "xz",
                     c=(x, 0.9, 0))
            m.caja((x, 0.845, 2.1), (0.03, 0.02, 0.9), "plastico")
        else:           # capa larga
            m.prisma([(-0.28, 2.55), (0.28, 2.55), (0.42, 1.35), (0.2, 1.3), (0, 1.38), (-0.2, 1.3), (-0.42, 1.35)],
                     -0.05, 0.05, mat, "xz", c=(x, 0.9, 0))
            m.tubo((x, 0.9, 2.55), 0.12, 0.08, 0.04, "oro", seg=8)
    # Maniquí de sastre y tijeras con cinta
    m.cil((-1.7, -0.1, 1.6), 0.03, 0.8, "acero", seg=6) if False else None
    m.torno((-1.55, ym + 0.1, zm), [(0.12, 0), (0.03, 0.04), (0.03, 0.3), (0.16, 0.34), (0.2, 0.6), (0.15, 0.82),
                                    (0.21, 1.05), (0.1, 1.16), (0.0, 1.18)], "tela_blanca", seg=10)
    m.tubo((-1.55, ym + 0.1, zm + 0.84), 0.165, 0.03, 0.02, "tela_amarilla", seg=10)
    m.caja((0.75, ym - 0.38, zm + 0.02), (0.07, 0.5, 0.02), "cromo", rot=(0, 0, 25))
    m.caja((0.75, ym - 0.38, zm + 0.03), (0.07, 0.5, 0.02), "cromo", rot=(0, 0, -5))
    m.tubo((0.62, ym - 0.14, zm + 0.02), 0.07, 0.03, 0.025, "rojo_p", seg=8)
    m.tubo((0.78, ym - 0.13, zm + 0.02), 0.07, 0.03, 0.025, "rojo_p", seg=8)


@modelo(34, "comercial", "edificio_mediano", (12, 10, 8))
def banco_galactico(m):
    # Fachada seria: zócalo de piedra, pilastras, cornisa pesada, puerta acorazada, cajero y pantallas
    m.caja((0, 0, 0.2), (12, 10, 0.4), "piedra_oscura", bisel=0.06)
    for k in range(3):
        m.bloque((-2.6 + 0.3 * k, -4.9 + 0.35 * k, 0.4 + 0.18 * k), (2.6 - 0.3 * k, -3.6, 0.58 + 0.18 * k), "piedra_clara")
    m.bloque((-5.6, -3.7, 0.4), (5.6, 4.7, 6.6), "blanco")
    m.bloque((-5.68, -3.78, 0.4), (5.68, 4.78, 1.5), "piedra_oscura")
    for x in (-5.4, -3.2, 3.2, 5.4):
        m.caja((x, -3.8, 3.85), (0.7, 0.5, 5.3), "gris_claro", bisel=0.06)
        m.caja((x, -3.84, 1.35), (0.9, 0.6, 0.3), "piedra_oscura", bisel=0.04)
        m.caja((x, -3.84, 6.4), (0.9, 0.6, 0.3), "oro", bisel=0.04)
        m.caja((x, -4.06, 3.9), (0.12, 0.03, 4.4), "neon")
    m.bloque((-6.0, -4.2, 6.6), (6.0, 5.0, 7.2), "gris", bisel=0.1)
    m.bloque((-5.8, -4.0, 7.2), (5.8, 4.8, 7.45), "oscuro", bisel=0.05)
    m.prisma([(-3.4, 7.2), (3.4, 7.2), (0, 8.0)], -4.25, -3.7, "blanco_liso", "xz")
    m.prisma([(-2.6, 7.3), (2.6, 7.3), (0, 7.86)], -4.3, -4.2, "oscuro", "xz")
    m.cil((0, -4.32, 7.5), 0.2, 0.06, "oro", eje="y", seg=12)
    m.texto("BANCO", (0, -4.14, 6.02), 0.6, 0.1, "oro")
    m.caja((0, -3.98, 6.02), (4.2, 0.2, 0.95), "oscuro", bisel=0.04)
    # Puerta acorazada circular (pieza aparte) con volante y cerrojos
    m.tubo((0, -3.8, 2.9), 2.0, 0.5, 0.3, "acero", eje="y", seg=24)
    m.cil((0, -3.78, 2.9), 1.72, 0.3, "oscuro", eje="y", seg=24, p="puerta_acorazada")
    m.tubo((0, -3.95, 2.9), 1.3, 0.08, 0.1, "acero", eje="y", seg=20, p="puerta_acorazada")
    for k in range(8):
        a = math.radians(45 * k)
        m.cil((1.52 * math.cos(a), -3.95, 2.9 + 1.52 * math.sin(a)), 0.1, 0.1, "cromo", eje="y", seg=8, p="puerta_acorazada")
        m.caja((1.86 * math.cos(a), -3.86, 2.9 + 1.86 * math.sin(a)), (0.3, 0.22, 0.16), "acero", rot=(0, -45 * k, 0))
    m.tubo((0, -4.1, 2.9), 0.55, 0.07, 0.07, "cromo", eje="y", seg=16, p="puerta_acorazada")
    for k in range(3):
        m.caja((0, -4.1, 2.9), (1.0, 0.05, 0.07), "cromo", rot=(0, 60 * k, 0), p="puerta_acorazada")
    m.cil((0, -4.05, 2.9), 0.16, 0.24, "oro", eje="y", seg=10, p="puerta_acorazada")
    m.tubo((0, -3.93, 2.9), 1.72, 0.05, 0.04, "neon", eje="y", seg=24)
    m.bloque((-2.0, -4.0, 0.4), (2.0, -3.7, 0.95), "piedra_oscura")
    # Cajero automático empotrado
    m.caja((4.3, -3.82, 2.5), (1.5, 0.4, 2.3), "oscuro", bisel=0.04)
    m.caja((4.3, -4.03, 2.95), (1.1, 0.04, 0.8), "pantalla")
    m.caja((4.3, -4.05, 2.95), (0.96, 0.02, 0.66), "neon", p="pantalla_neon")
    m.caja((4.3, -4.1, 2.2), (0.9, 0.22, 0.08), "acero", rot=(20, 0, 0))
    for i in range(3):
        for j in range(3):
            m.caja((4.1 + 0.2 * i, -4.16 - 0.035 * j, 2.2 + 0.013 - 0.085 * j + 0.1), (0.14, 0.05, 0.05), "gris_claro",
                   rot=(20, 0, 0))
    m.caja((4.3, -4.03, 1.75), (0.7, 0.04, 0.08), "negro")
    m.caja((4.75, -4.03, 2.3), (0.12, 0.04, 0.3), "neon_verde")
    # Pantallas holográficas de cotizaciones
    m.caja((-4.3, -3.95, 3.0), (1.6, 0.14, 2.4), "oscuro", bisel=0.03)
    m.caja((-4.3, -4.04, 3.0), (1.4, 0.03, 2.2), "neon", p="pantalla_neon")
    pts = [(-0.6, -0.5), (-0.3, -0.1), (-0.05, -0.3), (0.25, 0.4), (0.6, 0.7)]
    m.barrido([(-4.3 + x, -4.08, 3.2 + z) for x, z in pts], 0.035, "neon_blanco", seg=4)
    for i in range(4):
        m.caja((-4.75 + 0.3 * i, -4.07, 2.15 + 0.05 * i), (0.16, 0.02, 0.2 + 0.1 * i), "neon_verde")
    # Cámaras de seguridad, ventanas enrejadas y azotea
    for sx in (-1, 1):
        m.barrido([(sx * 2.4, -3.8, 5.3), (sx * 2.4, -4.2, 5.3)], 0.04, "acero", seg=5)
        m.caja((sx * 2.4, -4.3, 5.22), (0.2, 0.4, 0.2), "blanco_liso", rot=(20, 0, sx * 20), bisel=0.03)
        m.cil((sx * 2.47, -4.5, 5.15), 0.05, 0.04, "neon_rojo", eje="y", seg=6)
        for y in (-1.0, 2.2):
            m.ventana((sx * 5.62, y, 3.6), 1.6, 2.2, normal="x", sentido=sx, marco="gris_claro")
            for k in range(4):
                m.cil((sx * 5.72, y - 0.5 + 0.33 * k, 3.6), 0.03, 2.0, "hierro", seg=5)
    m.ventana((0, 4.72, 3.6), 3.0, 1.6, sentido=1, marco="gris_claro")
    m.caja((3.0, 2.0, 7.9), (2.0, 1.6, 0.9), "gris_claro", bisel=0.05)
    m.cupula((-2.5, 1.5, 7.45), 1.3, "cristal_oscuro", grosor=0.1, seg=16, anillos=4, altura=0.5)
    m.tubo((-2.5, 1.5, 7.5), 1.38, 0.14, 0.12, "acero", seg=16)


def _silla(m, c, giro, mat="blanco_liso"):
    x, y, z = c
    a = math.radians(giro)
    ca, sa = math.cos(a), math.sin(a)
    for dx, dy in ((0.22, 0.22), (-0.22, 0.22), (-0.22, -0.22), (0.22, -0.22)):
        m.cil((x + dx * ca - dy * sa, y + dx * sa + dy * ca, z + 0.3), 0.03, 0.6, "acero", seg=5)
    m.caja((x, y, z + 0.63), (0.56, 0.56, 0.07), mat, rot=(0, 0, giro), bisel=0.02)
    m.caja((x + 0.26 * sa * -1 * -1 * 0 - 0.26 * sa, y + 0.26 * ca, z + 1.05), (0.54, 0.05, 0.5), mat,
           rot=(-8, 0, giro), bisel=0.02)
    for s in (-1, 1):
        m.cil((x + s * 0.24 * ca - 0.26 * sa, y + s * 0.24 * sa + 0.26 * ca, z + 0.85), 0.025, 0.5, "acero", seg=5)


def _mesa_redonda(m, c, r=0.75, mat="blanco_liso"):
    x, y, z = c
    m.cil((x, y, z + 0.03), r * 0.55, 0.06, "oscuro", seg=12)
    m.torno((x, y, z + 0.06), [(0.12, 0), (0.06, 0.1), (0.06, 0.95), (0.2, 1.0)], "acero", seg=8)
    m.cil((x, y, z + 1.1), r, 0.08, mat, seg=18)
    m.tubo((x, y, z + 1.1), r + 0.01, 0.06, 0.03, "acento", seg=18)


@modelo(35, "comercial", "edificio_mediano", (14, 10, 8))
def restaurante(m):
    m.caja((0, 0, 0.2), (14, 10, 0.4), "hormigon", bisel=0.06)
    # Local al fondo con gran ventanal y cocina
    m.bloque((-6.6, 0.2, 0.4), (6.6, 4.7, 6.6), "blanco")
    m.bloque((-6.66, 0.14, 0.4), (6.66, 4.76, 1.0), "oscuro_paneles")
    m.bloque((-6.64, 0.16, 5.6), (6.64, 4.74, 5.85), "naranja_p")
    m.bloque((-6.9, -0.1, 6.6), (6.9, 5.0, 6.95), "gris", bisel=0.08)
    m.bloque((-6.7, 4.6, 6.95), (6.7, 4.8, 7.2), "blanco_liso")
    m.ventana((-2.8, 0.16, 2.7), 6.4, 3.0, marco="gris_liso")
    for x in (-4.4, -2.8, -1.2):
        m.caja((x, 0.1, 2.7), (0.1, 0.14, 2.7), "gris_liso")
    m.marco((3.6, 0.14, 2.3), 2.6, 3.6, 0.2, 0.3, "gris_liso")
    for s, nom in ((-1, "puerta_izq"), (1, "puerta_der")):
        m.caja((3.6 + s * 0.56, 0.2, 2.25), (1.08, 0.1, 3.3), "gris_claro", p=nom)
        m.caja((3.6 + s * 0.56, 0.14, 2.6), (0.7, 0.05, 2.0), "cristal")
    # Terraza: tarima, tres mesas con sillas, jardineras y toldo de rayas
    m.bloque((-6.6, -4.7, 0.4), (6.6, 0.2, 0.55), "madera_clara")
    for i, cx in enumerate((-4.4, -0.6, 3.2)):
        cy = -2.4 + 0.3 * (i % 2)
        _mesa_redonda(m, (cx, cy, 0.55))
        for k, g in enumerate((90, 270) if i != 1 else (0, 180, 90)):
            a = math.radians(g)
            _silla(m, (cx - 1.15 * math.sin(a), cy + 1.15 * math.cos(a), 0.55), g)
        m.torno((cx, cy, 1.69), [(0.08, 0), (0.1, 0.12), (0.05, 0.2), (0.0, 0.2)], "cristal", seg=8)
        m.cil((cx, cy, 1.76), 0.035, 0.1, "neon_naranja", seg=6)
        for s in (-1, 1):
            m.torno((cx + s * 0.38, cy - 0.1, 1.69), [(0.05, 0), (0.2, 0.02), (0.21, 0.04), (0.05, 0.02)], "plastico",
                    seg=10, cerrar=True)
    for x in (-6.2, 6.2):
        m.caja((x, -2.3, 0.9), (0.6, 4.4, 0.7), "gris_liso", bisel=0.04)
        m.bloque((x - 0.24, -4.4, 1.2), (x + 0.24, -0.2, 1.27), "tierra")
        for k in range(6):
            m.ico((x, -4.0 + 0.72 * k, 1.5), 0.32, "hoja" if k % 2 else "hoja2", sub=1, esc=(0.9, 1, 0.9), ruido=0.3,
                  semilla=k + x)
    for i in range(12):
        x0 = -6.7 + 13.4 * i / 12
        x1 = x0 + 13.4 / 12
        mat = "tela_naranja" if i % 2 == 0 else "tela_blanca"
        m.prisma([(-4.6, 4.3), (0.2, 5.3), (0.2, 5.38), (-4.6, 4.38)], x0, x1, mat, "yz")
        m.prisma([(x0, 4.38), (x1, 4.38), ((x0 + x1) / 2, 4.0)], -4.64, -4.58, mat, "xz")
    for x in (-6.5, -2.2, 2.2, 6.5):
        m.cil((x, -4.5, 2.4), 0.06, 3.9, "acero", seg=8)
        m.barrido([(x, -4.5, 4.3), (x, 0.2, 5.28)], 0.04, "acero", seg=5)
    m.barrido([(-6.5, -4.5, 4.3), (6.5, -4.5, 4.3)], 0.04, "acero", seg=5)
    # Menú holográfico en atril y rótulo
    m.cil((5.3, -4.3, 0.6), 0.3, 0.1, "oscuro", seg=12)
    m.cil((5.3, -4.3, 1.15), 0.04, 1.1, "acero", seg=6)
    m.cil((5.3, -4.3, 1.72), 0.12, 0.06, "neon", seg=10)
    m.caja((5.3, -4.3, 2.5), (0.9, 0.03, 1.3), "neon", p="menu_neon")
    m.texto("MENU", (5.3, -4.33, 2.9), 0.2, 0.03, "neon_blanco")
    for k in range(4):
        m.caja((5.25, -4.33, 2.6 - 0.16 * k), (0.6 - 0.08 * (k % 2), 0.02, 0.05), "neon_blanco")
    m.caja((0, 0.0, 6.0), (6.4, 0.2, 1.0), "oscuro", bisel=0.04)
    m.texto("RESTAURANTE", (0, -0.13, 6.0), 0.5, 0.1, "neon_naranja")
    # Azotea: chimenea de cocina y extractor
    m.cil((4.8, 3.2, 7.6), 0.3, 1.5, "acero", seg=10)
    m.torno((4.8, 3.2, 8.35), [(0.42, 0), (0.42, 0.06), (0, 0.3)], "hierro", seg=10)
    m.anclaje("humo_cocina", (4.8, 3.2, 8.7))
    m.caja((-3.5, 2.8, 7.4), (2.2, 1.6, 0.9), "gris_claro", bisel=0.05)
    for sx in (-1, 1):
        m.ventana((sx * 6.62, 2.5, 3.0), 2.6, 1.8, normal="x", sentido=sx, cruz=True)
    m.ventana((0, 4.72, 3.0), 3.0, 1.6, sentido=1)


@modelo(36, "comercial", "edificio_mediano", (10, 10, 7))
def bar_cantina(m):
    R = m.rng
    # Local abierto al frente: suelo, paredes con grosor, barra, taburetes y botellero
    m.caja((0, 0, 0.2), (10, 10, 0.4), "hormigon", bisel=0.06)
    m.bloque((-4.7, -4.2, 0.4), (4.7, 4.7, 0.55), "madera_oscura")
    m.bloque((-4.7, 4.3, 0.55), (4.7, 4.7, 5.6), "oscuro_paneles")
    for sx in (-1, 1):
        m.bloque((sx * 4.3, -4.2, 0.55), (sx * 4.7, 4.3, 5.6), "oscuro_paneles")
        m.bloque((sx * 4.72, -4.25, 0.4), (sx * 4.25, -3.8, 5.6), "gris_liso")
        m.caja((sx * 4.5, -4.27, 3.0), (0.1, 0.03, 4.4), "neon_rosa")
    m.bloque((-4.9, -4.4, 5.6), (4.9, 4.9, 5.95), "gris", bisel=0.08)
    m.bloque((-4.7, -4.3, 4.6), (4.7, -3.9, 5.6), "oscuro")
    # Barra en L con sobre de madera, reposapiés y frente iluminado
    m.bloque((-3.6, -0.6, 0.55), (3.0, 0.3, 1.75), "madera_oscura")
    m.bloque((-3.75, -0.8, 1.75), (3.15, 0.45, 1.87), "madera", bisel=0.03)
    m.bloque((2.1, 0.3, 0.55), (3.0, 3.0, 1.75), "madera_oscura")
    m.bloque((1.95, 0.3, 1.75), (3.15, 3.1, 1.87), "madera", bisel=0.03)
    m.caja((-0.3, -0.62, 1.2), (6.2, 0.04, 0.08), "neon_azul")
    m.barrido([(-3.6, -0.85, 0.85), (3.0, -0.85, 0.85)], 0.04, "cobre", seg=6)
    for x in (-3.4, -0.3, 2.8):
        m.barrido([(x, -0.6, 0.85), (x, -0.85, 0.85)], 0.03, "cobre", seg=5)
    for i, x in enumerate((-3.0, -1.8, -0.6, 0.6, 1.8)):                # taburetes
        y = -1.55 + 0.1 * (i % 2)
        m.cil((x, y, 0.58), 0.26, 0.06, "acero", seg=12)
        m.cil((x, y, 1.0), 0.04, 0.8, "cromo", seg=6)
        m.tubo((x, y, 0.9), 0.2, 0.03, 0.03, "cromo", seg=12)
        m.torno((x, y, 1.4), [(0.1, 0), (0.28, 0.04), (0.3, 0.12), (0.26, 0.18), (0, 0.18)], "tela_roja", seg=12)
    # Botellero trasero: tres baldas con botellas 3D de colores y espejo
    m.bloque((-3.6, 4.1, 1.2), (3.6, 4.3, 4.6), "madera_oscura")
    m.bloque((-3.2, 4.07, 2.0), (3.2, 4.12, 4.3), "cristal_oscuro")
    cols = ["#2E8B57", "#B5651D", "#1C6EA4", "#7A1F2B", "#D9A441", "#3FD9C9", "#8A2BE2"]
    k = 0
    for z in (2.05, 2.95, 3.8):
        m.caja((0, 3.85, z), (6.8, 0.5, 0.06), "madera", bisel=0.015)
        m.caja((0, 3.62, z - 0.04), (6.6, 0.03, 0.03), "neon_amarillo")
        for i in range(13):
            x = -3.0 + 0.5 * i + R.uniform(-0.05, 0.05)
            h = R.uniform(0.38, 0.55)
            r = R.uniform(0.07, 0.1)
            if (i + k) % 4 == 3:
                m.torno((x, 3.85, z + 0.03), [(r * 1.3, 0), (r * 1.3, h * 0.45), (0.03, h * 0.7), (0.03, h), (0, h)],
                        m.color(cols[k % 7], 0.15), seg=8)
            else:
                m.torno((x, 3.85, z + 0.03), [(r, 0), (r, h * 0.6), (0.035, h * 0.8), (0.035, h), (0, h)],
                        m.color(cols[k % 7], 0.15), seg=8)
            m.cil((x, 3.85, z + 0.03 + h + 0.02), 0.04, 0.04, "oro" if k % 2 else "plastico_negro", seg=6)
            k += 1
    # Grifos de cerveza, vasos y coctelera sobre la barra
    m.caja((0.6, -0.1, 1.95), (0.8, 0.2, 0.16), "cromo", bisel=0.02)
    for i in range(3):
        m.cil((0.35 + 0.25 * i, -0.1, 2.2), 0.03, 0.4, "cromo", seg=6)
        m.caja((0.35 + 0.25 * i, -0.2, 2.42), (0.06, 0.06, 0.2), ("rojo_p", "amarillo_p", "azul_p")[i], rot=(25, 0, 0))
    for i in range(5):
        m.torno((-2.6 + 0.3 * i, -0.2, 1.87), [(0.07, 0), (0.09, 0.26), (0.075, 0.26), (0.06, 0.03)], "cristal", seg=8,
                cerrar=True)
    m.torno((-0.8, 0.0, 1.87), [(0.09, 0), (0.11, 0.3), (0.06, 0.42), (0.06, 0.5), (0, 0.5)], "cromo", seg=10)
    # Mesa alta con dos taburetes en la zona izquierda
    m.cil((-2.6, 2.2, 0.58), 0.4, 0.06, "acero", seg=12)
    m.cil((-2.6, 2.2, 1.15), 0.05, 1.1, "cromo", seg=6)
    m.cil((-2.6, 2.2, 1.74), 0.6, 0.08, "madera", seg=14)
    # Neones de colores: rótulo BAR, copa de cóctel y flecha
    m.texto("BAR", (-1.6, -4.33, 5.1), 0.7, 0.1, "neon_rosa")
    copa = [(1.2, 5.45), (2.2, 5.45), (1.7, 4.95), (1.7, 4.72), (1.45, 4.72), (1.95, 4.72)]
    m.barrido([(x, -4.33, z) for x, z in (copa[0], copa[1], copa[2], copa[0])], 0.035, "neon_azul", seg=5)
    m.barrido([(1.7, -4.33, 4.95), (1.7, -4.33, 4.72)], 0.035, "neon_azul", seg=5)
    m.barrido([(1.45, -4.33, 4.72), (1.95, -4.33, 4.72)], 0.035, "neon_azul", seg=5)
    m.esfera((1.9, -4.33, 5.3), 0.08, "neon_verde", seg=6, anillos=4)
    m.barrido([(2.7, -4.33, 5.1), (3.9, -4.33, 5.1)], 0.035, "neon_amarillo", seg=5)
    m.barrido([(3.6, -4.33, 5.35), (3.9, -4.33, 5.1), (3.6, -4.33, 4.85)], 0.035, "neon_amarillo", seg=5)
    m.tubo((0, 0, 5.5), 1.2, 0.06, 0.06, "neon_rosa", seg=20)             # aro de luz en el techo
    m.tubo((0, 0, 5.5), 0.7, 0.06, 0.06, "neon_azul", seg=16)
    # Azotea: barriles y extractor
    for x in (-3.0, -2.0):
        m.torno((x, 2.5, 5.95), [(0.38, 0), (0.46, 0.4), (0.46, 0.7), (0.38, 1.1), (0, 1.1)], "madera", seg=12)
        for z in (0.25, 0.85):
            m.tubo((x, 2.5, 5.95 + z), 0.455, 0.08, 0.03, "hierro", seg=12)
    m.caja((2.5, 2.5, 6.35), (1.8, 1.4, 0.8), "gris_claro", bisel=0.05)
    m.cil((2.5, 2.5, 6.78), 0.5, 0.08, "oscuro", seg=12)


@modelo(37, "comercial", "edificio_grande", (14, 12, 10))
def hospital_clinica(m):
    L = _local(m, 14, 12, 10, vanos=[(-6.3, -1.6)], puerta=(2.4, 3.6), hz=4.4, prof=3.0)
    yf, yb, zs, hz, zt = L["yf"], L["yb"], L["zs"], L["hz"], L["zt"]
    # Sala visible por la ventana: camilla con colchón, almohada, gotero y monitor
    m.bloque((-6.2, yb - 0.08, 0.9), (-1.7, yb, hz - 0.1), "gris_claro")
    cx, cy = -4.2, yf + 1.5
    for dx in (-1.1, 1.1):
        for dy in (-0.4, 0.4):
            m.cil((cx + dx, cy + dy, 1.25), 0.04, 0.7, "cromo", seg=6)
            m.cil((cx + dx, cy + dy, 0.97), 0.07, 0.06, "goma", eje="y", seg=8)
    m.caja((cx, cy, 1.64), (2.6, 1.0, 0.1), "acero", bisel=0.02)
    m.caja((cx - 0.2, cy, 1.8), (2.1, 0.9, 0.22), "tela_blanca", bisel=0.06)
    m.caja((cx + 1.0, cy, 1.98), (0.6, 0.9, 0.2), "tela_blanca", rot=(0, -28, 0), bisel=0.06)
    m.caja((cx + 0.95, cy, 2.16), (0.4, 0.6, 0.12), "tela_cyan", rot=(0, -28, 0), bisel=0.05)
    m.caja((cx - 0.5, cy, 1.93), (1.3, 0.94, 0.06), "tela_cyan", bisel=0.02)
    for dx in (-0.6, 0.6):
        m.barrido([(cx + dx - 0.4, cy - 0.52, 1.7), (cx + dx - 0.4, cy - 0.52, 2.05), (cx + dx + 0.4, cy - 0.52, 2.05),
                   (cx + dx + 0.4, cy - 0.52, 1.7)], 0.025, "cromo", seg=5)
    m.cil((cx + 1.7, cy + 0.6, 0.94), 0.25, 0.06, "acero", seg=10)          # gotero
    m.cil((cx + 1.7, cy + 0.6, 2.0), 0.03, 2.1, "cromo", seg=6)
    m.barrido([(cx + 1.5, cy + 0.6, 3.05), (cx + 1.9, cy + 0.6, 3.05)], 0.02, "cromo", seg=4)
    m.caja((cx + 1.5, cy + 0.6, 2.8), (0.2, 0.08, 0.34), "cristal", bisel=0.03)
    m.caja((cx + 1.5, cy + 0.6, 2.75), (0.16, 0.05, 0.2), m.color("#3DB8F2", 0.2))
    m.barrido([(cx + 1.5, cy + 0.6, 2.63), (cx + 1.4, cy + 0.4, 2.2), (cx + 1.1, cy + 0.2, 2.0)], 0.01, "plastico", seg=4)
    m.caja((cx - 1.7, yb - 0.4, 1.5), (0.6, 0.5, 1.2), "blanco_liso", bisel=0.03)    # monitor de constantes
    m.caja((cx - 1.7, yb - 0.5, 2.45), (0.8, 0.12, 0.6), "oscuro", bisel=0.02)
    m.caja((cx - 1.7, yb - 0.57, 2.45), (0.68, 0.02, 0.48), "pantalla")
    pulso = [(-0.3, 0), (-0.12, 0), (-0.06, 0.14), (0.0, -0.12), (0.06, 0.06), (0.12, 0), (0.3, 0)]
    m.barrido([(cx - 1.7 + x, yb - 0.59, 2.45 + z) for x, z in pulso], 0.015, "neon_verde", seg=4)
    # Segundo piso: cinturón, ventanas corridas y cruz médica luminosa
    m.bloque((L["x0"] - 0.06, yf - 0.06, 5.2), (L["x1"] + 0.06, 5.76, 5.5), "gris", bisel=0.04)
    for x in (-5.0, -2.6, 4.6):
        m.ventana((x, yf - 0.02, 7.2), 1.9, 1.9, cruz=True)
    for sx in (-1, 1):
        for y in (-0.5, 3.2):
            for z in (2.8, 7.2):
                m.ventana((sx * 6.72, y, z), 2.2, 1.8, normal="x", sentido=sx, cruz=True)
    for x in (-3.5, 0, 3.5):
        for z in (2.8, 7.2):
            m.ventana((x, 5.72, z), 2.2, 1.8, sentido=1, cruz=True)
    def cruz(c, t, g, mat, p=None):
        x, y, z = c
        m.caja((x, y, z), (t, g, t / 3), mat, p=p)
        m.caja((x, y, z), (t / 3, g, t), mat, p=p)
    m.cil((1.0, yf - 0.12, 7.2), 1.45, 0.2, "blanco_liso", eje="y", seg=24)
    m.tubo((1.0, yf - 0.16, 7.2), 1.5, 0.26, 0.12, "acento", eje="y", seg=24)
    cruz((1.0, yf - 0.26, 7.2), 1.9, 0.14, "neon")
    # Marquesina de urgencias con rótulo y luces
    m.bloque((0.2, yf - 2.2, hz + 0.1), (4.6, yf, hz + 0.4), "blanco_liso", bisel=0.05)
    m.bloque((0.25, yf - 2.24, hz + 0.16), (4.55, yf - 2.18, hz + 0.34), "rojo_p")
    for x in (0.5, 4.3):
        m.cil((x, yf - 2.0, 2.25), 0.1, 3.7, "acero", seg=8)
    m.texto("CLINICA", (2.4, yf - 2.27, hz + 0.25), 0.2, 0.04, "neon_blanco")
    m.caja((2.4, yf - 1.1, hz + 0.08), (3.6, 0.2, 0.05), "neon")
    # Azotea: helipuerto marcado, cruz y climatización
    m.cil((-2.6, 1.5, zt + 0.34), 2.6, 0.08, "oscuro", seg=24)
    m.tubo((-2.6, 1.5, zt + 0.36), 2.5, 0.06, 0.14, "amarillo_p", seg=24)
    for x in (-3.2, -2.0):
        m.caja((x, 1.5, zt + 0.39), (0.22, 1.8, 0.03), "blanco_liso")
    m.caja((-2.6, 1.5, zt + 0.39), (1.2, 0.22, 0.03), "blanco_liso")
    for k in range(6):
        a = math.radians(60 * k)
        m.cil((-2.6 + 2.5 * math.cos(a), 1.5 + 2.5 * math.sin(a), zt + 0.42), 0.09, 0.08, "neon", seg=8)
    m.caja((4.0, 3.0, zt + 0.9), (2.6, 2.0, 1.2), "gris_claro", bisel=0.06)
    cruz((4.0, 1.96, zt + 0.95), 0.8, 0.06, "neon_rojo")
    for x in (3.4, 4.6):
        m.cil((x, 3.0, zt + 1.53), 0.45, 0.08, "oscuro", seg=10)


@modelo(38, "comercial", "prop", (3, 2, 2))
def mesa_mercado(m):
    # Mesa de caballetes: tablero de tablones, patas en aspa con tirantes, balda inferior y mantel
    for i in range(4):
        m.caja((0, -0.75 + 0.5 * i, 1.84), (3.0, 0.47, 0.1), "madera" if i % 2 else "madera_clara", bisel=0.02)
    for y in (-0.82, 0.82):
        m.caja((0, y, 1.74), (2.8, 0.08, 0.14), "madera_oscura")
    for x in (-1.2, 1.2):
        for s in (-1, 1):
            m.caja((x, 0, 0.9), (0.12, 0.12, 2.2), "madera_oscura", rot=(s * 38, 0, 0), bisel=0.015)
        m.cil((x, 0, 0.92), 0.05, 0.2, "hierro", eje="x", seg=8)
        m.caja((x, 0, 1.7), (0.14, 1.5, 0.1), "madera_oscura")
    m.caja((0, 0, 0.5), (2.5, 0.7, 0.07), "madera", bisel=0.015)
    for x in (-1.2, 1.2):
        m.caja((x, 0, 0.44), (0.1, 0.9, 0.08), "madera_oscura")
    m.barrido([(-1.2, -0.6, 0.2), (1.2, 0.6, 1.65)], 0.025, "hierro", seg=5)
    m.barrido([(-1.2, 0.6, 0.2), (1.2, -0.6, 1.65)], 0.025, "hierro", seg=5)
    # Camino de mesa con caída, soporte de cartel y gancho con farolillo
    m.caja((0, 0, 1.905), (1.1, 2.04, 0.03), "tela_cyan")
    for s in (-1, 1):
        m.caja((0, s * 1.02, 1.74), (1.1, 0.03, 0.36), "tela_cyan")
        m.prisma([(-0.55, 1.56), (0.55, 1.56), (0, 1.36)], s * 1.02 - 0.015, s * 1.02 + 0.015, "tela_cyan", "xz")
    m.cil((1.3, 0.8, 2.2), 0.025, 0.7, "acero", seg=6)
    m.caja((1.3, 0.78, 2.45), (0.5, 0.03, 0.3), "plastico_negro", bisel=0.01)
    m.caja((1.3, 0.76, 2.45), (0.36, 0.02, 0.06), "neon")
    m.caja((-1.25, -0.7, 1.92), (0.3, 0.3, 0.06), "madera_clara", bisel=0.01)


@modelo(39, "comercial", "prop", (5, 4, 3))
def toldo_mercado(m):
    # Cuatro pies con base lastrada, bastidor, lona a cuatro aguas con grosor y faldón, vientos y farol
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 2.35, sy * 1.85
            m.cil((x, y, 0.08), 0.26, 0.16, "hormigon", seg=10)
            m.cil((x, y, 1.15), 0.045, 2.2, "acero", seg=8)
            m.tubo((x, y, 1.3), 0.065, 0.12, 0.03, "oscuro", seg=8)
            m.barrido([(x, y, 2.2), (x * 0.5, y * 0.5, 2.62), (0, 0, 2.9)], 0.03, "acero", seg=5)
            m.barrido([(x, y, 2.0), (x + sx * 0.12, y + sy * 0.12, 0.2)], 0.012, "goma", seg=4)
    for sy in (-1, 1):
        m.cil((0, sy * 1.85, 2.22), 0.035, 4.7, "acero", eje="x", seg=6)
    for sx in (-1, 1):
        m.cil((sx * 2.35, 0, 2.22), 0.035, 3.7, "acero", eje="y", seg=6)
    cima = (0, 0, 2.95)
    esq = [(-2.5, -2.0), (2.5, -2.0), (2.5, 2.0), (-2.5, 2.0)]
    from mathutils import Vector
    for k in range(4):
        (ax, ay), (bx, by) = esq[k], esq[(k + 1) % 4]
        n = 5 if k % 2 == 0 else 4
        for i in range(n):
            t0, t1 = i / n, (i + 1) / n
            p0 = (ax + (bx - ax) * t0, ay + (by - ay) * t0)
            p1 = (ax + (bx - ax) * t1, ay + (by - ay) * t1)
            mat = "tela_rayas" if False else ("tela_cyan" if i % 2 == 0 else "tela_blanca")
            # paño triangular con grosor: sólido de 6 vértices
            bm_pts = [(p0[0], p0[1], 2.26), (p1[0], p1[1], 2.26), cima]
            nrm = (Vector(bm_pts[1]) - Vector(bm_pts[0])).cross(Vector(cima) - Vector(bm_pts[0])).normalized() * 0.05
            m.barrido([tuple(Vector(bm_pts[0]).lerp(Vector(bm_pts[1]), 0.5)), cima],
                      [((Vector(p1) - Vector(p0)).length) / 2 * 1.0, 0.01], mat, seg=4) if False else None
            dst, idx = m._dest(mat, None)
            import bmesh
            bm = bmesh.new()
            vs = [bm.verts.new(Vector(q) + nrm) for q in bm_pts] + [bm.verts.new(Vector(q) - nrm * 0.2) for q in bm_pts]
            bm.faces.new(vs[:3]); bm.faces.new(vs[3:][::-1])
            for a in range(3):
                b = (a + 1) % 3
                bm.faces.new((vs[a], vs[b], vs[b + 3], vs[a + 3]))
            m._fin(bm, dst, idx, None)
            # faldón
            d = (Vector((p1[0] - p0[0], p1[1] - p0[1], 0)))
            mid = Vector(((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, 2.08))
            ang = math.degrees(math.atan2(d.y, d.x))
            m.prisma([(-d.length / 2, 0.2), (d.length / 2, 0.2), (d.length / 2, -0.05), (0, -0.22), (-d.length / 2, -0.05)],
                     -0.025, 0.025, mat, "xz", c=tuple(mid), rot=(0, 0, ang))
    m.torno((0, 0, 2.93), [(0.12, 0), (0.06, 0.12), (0.0, 0.3)], "acero", seg=8)
    m.barrido([(0, 0, 2.7), (0, 0, 2.35)], 0.01, "acero", seg=4)
    m.torno((0, 0, 2.05), [(0.0, 0), (0.1, 0.02), (0.14, 0.14), (0.1, 0.28), (0.0, 0.3)], "neon", seg=8)
    m.tubo((0, 0, 2.2), 0.15, 0.03, 0.02, "acero", seg=8)


@modelo(40, "comercial", "prop", (4, 0.3, 3))
def cartel_holografico(m):
    # Emisor flotante (antigravedad) y panel holográfico: todo el cartel es de neón
    m.caja((0, 0, 0.16), (3.6, 0.28, 0.14), "oscuro", bisel=0.04)
    for x in (-1.5, 1.5):
        m.cil((x, 0, 0.06), 0.12, 0.08, "neon", seg=10)
        m.cil((x, 0, 0.11), 0.16, 0.04, "acero", seg=10)
    m.caja((0, 0, 0.245), (3.3, 0.1, 0.03), "neon")
    P = "panel_neon"
    m.caja((0, 0, 1.65), (3.8, 0.04, 2.5), "neon", p=P)
    m.marco((0, 0, 1.65), 4.0, 2.7, 0.06, 0.1, "neon_blanco", p="marco_neon")
    for sx in (-1, 1):
        for sz in (-1, 1):
            m.caja((sx * 1.85, 0, 1.65 + sz * 1.2), (0.3, 0.14, 0.3), "neon_blanco", p="marco_neon")
    for cara, giro in ((-1, 0), (1, 180)):
        y = cara * 0.05
        m.texto("COLONIA", (0, y, 2.35), 0.42, 0.04, "neon_blanco", rot=(0, 0, giro), p="texto_neon")
        m.texto("ALBA", (-0.6 * (1 if giro == 0 else -1), y, 1.6), 0.6, 0.04, "neon_naranja", rot=(0, 0, giro))
        # planeta con anillo
        px = 1.1 * (1 if giro == 0 else -1)
        m.cil((px, y, 1.55), 0.34, 0.04, "neon_blanco", eje="y", seg=16, p="texto_neon")
        m.toro((px, y, 1.55), 0.52, 0.03, "neon_naranja", eje="y", seg=18, seg2=5, rot=(0, 25, 0), esc=None)
        for k in range(6):
            m.caja((-1.5 + 0.6 * k if giro == 0 else 1.5 - 0.6 * k, y, 0.75 + 0.06 * (k % 3)), (0.4, 0.04, 0.06),
                   "neon_blanco", p="texto_neon")
