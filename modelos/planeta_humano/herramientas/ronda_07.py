"""Ronda 7 · Fin de la zona industrial (61-65) y comienzo del hangar (66-70)."""

import math

from geometria import arco_pts
from registro import modelo


@modelo(61, "industrial", "prop", (4, 3, 2))
def deposito_minerales(m):
    R = m.rng
    # Contenedor abierto de chapa reforzada (paredes con grosor), patines, nervios y montón de piedras 3D
    m.caja((0, 0, 0.22), (3.8, 2.8, 0.12), "hierro")
    for y in (-1.0, 1.0):
        m.caja((0, y, 0.08), (3.9, 0.3, 0.16), "oscuro", bisel=0.02)
    for s in (-1, 1):
        m.prisma([(-1.9, 0.28), (1.9, 0.28), (2.0, 1.5), (-2.0, 1.5)], s * 1.32, s * 1.42, "amarillo_p", "xz")
        m.prisma([(-1.4, 0.28), (1.4, 0.28), (1.45, 1.5), (-1.45, 1.5)], s * 1.9, s * 2.0, "amarillo_p", "yz")
        for x in (-1.2, 0, 1.2):
            m.caja((x, s * 1.44, 0.9), (0.14, 0.08, 1.2), "hierro")
        for y in (-0.7, 0.7):
            m.caja((s * 2.0, y, 0.9), (0.08, 0.14, 1.2), "hierro")
        m.caja((0, s * 1.4, 1.52), (4.1, 0.2, 0.1), "hierro", bisel=0.02)
        m.caja((s * 1.98, 0, 1.52), (0.2, 3.0, 0.1), "hierro", bisel=0.02)
        m.caja((0, s * 1.45, 0.5), (3.0, 0.02, 0.16), "rayas")
        m.barrido([(s * 2.04, -0.3, 1.2), (s * 2.2, -0.3, 1.1), (s * 2.2, 0.3, 1.1), (s * 2.04, 0.3, 1.2)], 0.035, "acero",
                  seg=5)
    m.bloque((-1.85, -1.3, 0.28), (1.85, 1.3, 1.1), "piedra_oscura")
    mats = ["piedra", "piedra_oscura", "piedra", "cobre", "hierro_viejo", "piedra_clara"]
    for i in range(34):
        x, y = R.uniform(-1.6, 1.6), R.uniform(-1.05, 1.05)
        z = 1.15 + 0.6 * (1 - (x / 1.9) ** 2) * (1 - (y / 1.35) ** 2) + R.uniform(-0.05, 0.05)
        s = R.uniform(0.4, 0.7)
        m.roca((x, y, z), (s, s * R.uniform(0.7, 1.0), s * 0.7), mats[i % 6], semilla=i * 1.3, sub=1,
               rot=(R.uniform(0, 60), R.uniform(0, 60), R.uniform(0, 180)))
    for (x, y) in ((0.6, -0.3), (-0.8, 0.4), (0.1, 0.6)):
        m.torno((x, y, 1.75), [(0.08, 0), (0.12, 0.1), (0.08, 0.4), (0, 0.5)], "neon", seg=5, rot=(x * 30, y * 40, 0),
                p="mineral_neon")
    m.caja((0, -1.46, 1.1), (0.9, 0.03, 0.4), "oscuro")
    m.texto("MINERAL", (0, -1.48, 1.1), 0.14, 0.02, "amarillo_p", res=1)


@modelo(62, "industrial", "vehiculo", (3, 2, 4))
def prensa_hidraulica(m):
    # Bancada, cuatro columnas cromadas, cabezal con cilindro, pistón vertical con plato (aparte) y mesa de prensado
    m.caja((0, 0, 0.25), (2.9, 1.9, 0.5), "oscuro", bisel=0.06)
    m.caja((0, 0, 0.52), (2.94, 1.94, 0.06), "rayas")
    m.caja((0, 0, 0.85), (2.2, 1.5, 0.6), "gris", bisel=0.05)
    m.caja((0, 0, 1.2), (1.9, 1.3, 0.12), "acero", bisel=0.02)                          # mesa de prensado
    for k in range(3):
        m.caja((-0.6 + 0.6 * k, 0, 1.265), (0.06, 1.3, 0.012), "negro")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cil((sx * 1.2, sy * 0.7, 2.2), 0.11, 2.8, "cromo", seg=10)
            m.cil((sx * 1.2, sy * 0.7, 0.62), 0.18, 0.14, "hierro", seg=8)
            m.cil((sx * 1.2, sy * 0.7, 3.7), 0.18, 0.14, "hierro", seg=8)
    m.caja((0, 0, 3.3), (2.9, 1.8, 0.7), "amarillo_p", bisel=0.07)                       # cabezal
    m.cil((0, 0, 3.8), 0.5, 0.4, "hierro", seg=14)
    m.cil((0, 0, 3.95), 0.3, 0.1, "acero", seg=10)
    m.cil((0, 0, 2.85), 0.42, 0.3, "hierro", seg=14)
    P = "piston"
    m.cil((0, 0, 2.35), 0.22, 0.9, "cromo", seg=12, p=P)
    m.caja((0, 0, 1.85), (1.5, 1.1, 0.2), "hierro", bisel=0.03, p=P)
    m.caja((0, 0, 1.74), (1.3, 0.9, 0.04), "acero", p=P)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.tubo((sx * 1.2, sy * 0.7, 1.9), 0.17, 0.2, 0.05, "acero", seg=10, p=P)
        m.caja((sx * 0.98, 0, 1.9), (0.5, 0.2, 0.12), "hierro", p=P)
    # Lingote aplastándose en la mesa
    m.caja((0, 0, 1.33), (0.8, 0.5, 0.14), "cobre", bisel=0.04)
    # Grupo hidráulico: depósito, bomba, manómetro, latiguillos y cuadro con pantalla
    m.caja((1.15, 0.72, 0.9), (0.5, 0.4, 0.7), "azul_p", bisel=0.04) if False else None
    m.barrido([(0.3, 0.5, 3.66), (0.6, 0.85, 3.5), (0.9, 1.0, 2.0), (0.9, 0.8, 0.75)], 0.045, "goma", seg=5)
    m.barrido([(-0.3, 0.5, 3.66), (-0.6, 0.85, 3.5), (-0.9, 1.0, 2.0), (-0.9, 0.8, 0.75)], 0.045, "goma", seg=5)
    m.cil((0.5, -0.5, 3.75), 0.03, 0.2, "cobre", seg=5)
    m.cil((0.5, -0.53, 3.9), 0.12, 0.06, "cromo", eje="y", seg=10)
    m.cil((0.5, -0.565, 3.9), 0.1, 0.015, "neon", eje="y", seg=10)
    m.caja((-1.5, -0.7, 1.5), (0.14, 0.5, 0.7), "gris_claro", bisel=0.03)
    m.barrido([(-1.2, -0.7, 1.2), (-1.5, -0.7, 1.15)], 0.03, "acero", seg=4)
    m.caja((-1.58, -0.7, 1.62), (0.02, 0.36, 0.22), "neon", p="pantalla_neon")
    for k, mat in enumerate(("neon_verde", "neon_rojo")):
        m.cil((-1.58, -0.8 + 0.2 * k, 1.32), 0.045, 0.03, mat, eje="x", seg=8)
    m.caja((0, -0.92, 3.3), (1.2, 0.03, 0.3), "oscuro")
    m.texto("50T", (0, -0.94, 3.3), 0.2, 0.03, "amarillo_p", res=1)


@modelo(63, "industrial", "prop", (2, 2, 3))
def soldador_arco(m):
    # Mesa de soldadura con rejilla, equipo de arco, cable hasta la antorcha, pantalla protectora y chispas
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.caja((sx * 0.8, sy * 0.55, 0.5), (0.1, 0.1, 1.0), "oscuro")
    m.caja((0, 0, 0.3), (1.6, 1.1, 0.05), "gris_liso")
    m.caja((0, 0, 1.03), (1.9, 1.3, 0.1), "hierro", bisel=0.02)
    for k in range(7):
        m.caja((-0.75 + 0.25 * k, 0, 1.09), (0.05, 1.2, 0.03), "acero")
    # Piezas a soldar en ángulo, con el cordón incandescente
    m.caja((0.05, -0.1, 1.15), (0.9, 0.5, 0.06), "acero")
    m.caja((0.05, 0.12, 1.4), (0.9, 0.06, 0.5), "acero")
    m.barrido([(-0.38, 0.08, 1.19), (0.1, 0.08, 1.19)], 0.03, "hierro_viejo", seg=5)
    m.barrido([(0.1, 0.08, 1.19), (0.3, 0.08, 1.19)], 0.035, "neon_naranja", seg=5)
    # Chispas: estrella de esquirlas luminosas en el punto de soldadura
    R = m.rng
    for i in range(14):
        a, e = R.uniform(0, 6.28), R.uniform(0.2, 1.4)
        d = (math.cos(a) * math.cos(e), -abs(math.sin(a)) * math.cos(e), math.sin(e))
        l = R.uniform(0.15, 0.45)
        p0 = (0.3 + d[0] * 0.05, 0.06 + d[1] * 0.05, 1.21 + d[2] * 0.05)
        p1 = (0.3 + d[0] * l, 0.06 + d[1] * l, 1.21 + d[2] * l)
        m.barrido([p0, p1], [0.018, 0.004], "neon", seg=3, p="chispas_neon")
    m.esfera((0.3, 0.06, 1.22), 0.07, "neon_blanco", seg=6, anillos=4)
    m.anclaje("chispas", (0.3, 0.06, 1.22))
    # Antorcha con mango y cable que baja al equipo
    m.cil((0.52, -0.2, 1.42), 0.03, 0.5, "cobre", seg=6, rot=(35, -35, 0))
    m.cil((0.68, -0.38, 1.66), 0.05, 0.36, "goma", seg=8, rot=(35, -35, 0))
    m.barrido([(0.76, -0.47, 1.78), (0.95, -0.7, 1.7), (1.02, -0.72, 1.0), (0.9, -0.75, 0.4), (0.6, -0.9, 0.3)], 0.035,
              "goma", seg=6)
    # Equipo de soldadura bajo la mesa: carcasa, mandos, asa y pinza de masa
    m.caja((0.3, -0.25, 0.62), (0.8, 0.6, 0.56), "rojo_p", bisel=0.05)
    m.caja((0.3, -0.56, 0.7), (0.6, 0.03, 0.3), "oscuro")
    m.caja((0.15, -0.58, 0.76), (0.22, 0.02, 0.1), "neon", p="pantalla_neon")
    for k in range(2):
        m.cil((0.42 + 0.14 * k, -0.585, 0.72), 0.05, 0.05, "plastico_negro", eje="y", seg=8)
    m.barrido([(0.05, -0.25, 0.9), (0.05, -0.25, 1.0 - 0.02), (0.55, -0.25, 0.98), (0.55, -0.25, 0.9)], 0.025, "acero",
              seg=5)
    m.barrido([(0.0, -0.55, 0.5), (-0.5, -0.7, 0.34), (-0.7, -0.3, 0.9), (-0.6, -0.2, 1.12)], 0.025, "goma", seg=5)
    m.caja((-0.58, -0.2, 1.14), (0.1, 0.2, 0.06), "cobre")
    # Pantalla protectora trasera con ventana oscura y botella de gas con manorreductor
    m.caja((0, 0.75, 1.8), (1.9, 0.06, 1.5), "oscuro", bisel=0.02)
    for sx in (-0.9, 0.9):
        m.caja((sx, 0.75, 1.3), (0.08, 0.1, 2.6), "gris_liso")
    m.caja((0, 0.71, 2.0), (1.0, 0.03, 0.5), "cristal_oscuro")
    m.caja((0, 0.72, 2.75), (1.6, 0.04, 0.12), "rayas")
    m.caja((0, 0.74, 2.9), (1.2, 0.1, 0.12), "oscuro")
    m.caja((0, 0.69, 2.88), (1.0, 0.03, 0.05), "neon_blanco")
    m.torno((-0.75, -0.8, 0.0), [(0.18, 0), (0.2, 0.05), (0.2, 1.3), (0.1, 1.5), (0.07, 1.52), (0.07, 1.62), (0, 1.62)],
            "azul_p", seg=10)
    m.cil((-0.75, -0.8, 1.68), 0.05, 0.12, "cobre", seg=6)
    m.cil((-0.75, -0.87, 1.72), 0.06, 0.04, "cromo", eje="y", seg=8)
    m.barrido([(-0.75, -0.8, 1.72), (-0.4, -0.75, 1.5), (-0.1, -0.5, 0.95)], 0.02, "goma", seg=4)
    # Careta de soldador colgada
    m.torno((0.75, 0.66, 2.3), [(0.16, 0), (0.2, 0.12), (0.18, 0.34), (0.0, 0.4)], "plastico_negro", seg=8)
    m.caja((0.75, 0.48, 2.5), (0.2, 0.04, 0.08), "cristal_oscuro")


@modelo(64, "industrial", "edificio_grande", (16, 12, 8))
def almacen_industrial(m):
    R = m.rng
    m.caja((0, 0, 0.15), (16, 12, 0.3), "hormigon", bisel=0.05)
    # Nave abierta por el frente (portón corredero aparte), muros con grosor y cubierta curva de chapa
    x0, x1, yf, yb = -7.6, 7.6, -5.6, 5.6
    for s in (-1, 1):
        m.bloque((s * 7.2, yf, 0.3), (s * 7.6, yb, 5.0), "gris")
        m.bloque((s * 7.15, yf - 0.05, 0.3), (s * 7.65, yb + 0.05, 1.0), "oscuro_paneles")
    m.bloque((x0, yb - 0.4, 0.3), (x1, yb, 5.0), "gris")
    m.bloque((x0, yf, 0.3), (-3.6, yf + 0.4, 5.0), "gris")
    m.bloque((3.6, yf, 0.3), (x1, yf + 0.4, 5.0), "gris")
    m.bloque((-3.6, yf, 4.2), (3.6, yf + 0.4, 5.0), "gris")
    m.bloque((-7.2, yf + 0.4, 0.3), (7.2, yb - 0.4, 0.36), "hormigon")
    arco = arco_pts(7.9, 7.7, 0, 180, 14, 0, 5.0, 1.0, 0.36)
    m.prisma(arco, yf - 0.3, yb + 0.3, "chapa", "xz")
    for y in (yf + 0.2, yb - 0.2):                                                    # testeros (tímpano macizo)
        tim = [(-7.6, 5.0)] + [(7.6 * math.cos(math.radians(a)), 5.0 + 7.6 * 0.36 * math.sin(math.radians(a)))
                               for a in range(180, -1, -15)][1:-1] + [(7.6, 5.0)]
        tim = [(7.6, 5.0)] + [(7.7 * math.cos(math.radians(a)), 5.0 + 7.7 * 0.36 * math.sin(math.radians(a)))
                              for a in range(15, 180, 15)] + [(-7.6, 5.0)]
        m.prisma(tim, y - 0.2, y + 0.2, "gris", "xz")
    for y in (-3.5, -1.2, 1.2, 3.5):
        m.prisma(arco_pts(7.7, 7.45, 0, 180, 14, 0, 5.0, 1.0, 0.36), y - 0.08, y + 0.08, "hierro", "xz")
    m.caja((0, 0, 7.82), (0.6, 10.5, 0.2), "gris_liso")                               # lucernario de cumbrera
    m.caja((0, 0, 7.93), (0.36, 9.8, 0.05), "neon_blanco")
    # Portón corredero grande de dos hojas (una entreabierta), guía y bolardos
    m.bloque((-7.4, yf - 0.24, 4.3), (7.4, yf - 0.06, 4.5), "hierro")
    for nom, xa, xb in (("porton_izq", -6.9, -3.3), ("porton_der", 0.4, 4.0)):
        m.bloque((xa, yf - 0.22, 0.36), (xb, yf - 0.08, 4.28), "chapa", p=nom)
        m.marco(((xa + xb) / 2, yf - 0.24, 2.32), xb - xa, 3.92, 0.16, 0.08, "hierro", p=nom)
        m.barrido([(xa + 0.1, yf - 0.26, 0.5), (xb - 0.1, yf - 0.26, 4.1)], 0.05, "hierro", seg=4, p=nom)
        m.caja((xb - 0.3, yf - 0.3, 2.2), (0.1, 0.08, 0.7), "acero", p=nom)
    for x in (-3.9, 3.9):
        m.cil((x, yf - 0.8, 0.75), 0.14, 0.9, "rayas", seg=10)
    m.caja((0, yf - 0.1, 5.5), (5.0, 0.16, 0.9), "oscuro", bisel=0.04)
    m.texto("ALMACEN", (0, yf - 0.2, 5.5), 0.5, 0.08, "neon")
    # Dentro: estantería de paletización con cajas, pilas de cajas y bidones
    for x in (-6.0, -3.2):
        for y in (2.2, 4.8):
            m.caja((x, y, 2.3), (0.12, 0.12, 4.0), "naranja_p")
    for z in (0.5, 1.9, 3.3):
        m.caja((-4.6, 3.5, z), (3.0, 2.7, 0.1), "azul_p")
        for i in range(3):
            if (i + int(z * 2)) % 4 == 3:
                continue
            s = R.uniform(0.75, 1.0)
            m.caja((-5.5 + 0.9 * i, 3.4 + R.uniform(-0.3, 0.3), z + 0.05 + s / 2), (0.8, 0.8 * s + 0.3, s),
                   ("madera_clara", "gris", "madera")[i], bisel=0.03)
    cajas = [((-1.2, -1.5, 0.9), 1.2, "madera_clara"), ((-1.1, -1.4, 1.95), 0.9, "madera"), ((0.3, -1.8, 0.8), 1.0, "gris"),
             ((-2.6, -2.2, 0.85), 1.1, "madera"), ((1.6, -0.6, 0.9), 1.2, "madera_clara"), ((1.5, -0.7, 1.95), 0.9, "gris"),
             ((5.2, 3.6, 0.95), 1.3, "gris"), ((3.6, 3.9, 0.85), 1.1, "madera"), ((5.0, 3.7, 2.1), 1.0, "madera_clara")]
    for i, (c, s, mat) in enumerate(cajas):
        m.caja(c, (s, s, s), mat, bisel=0.04, rot=(0, 0, R.uniform(-12, 12)))
        if mat != "gris":
            m.caja(c, (s + 0.02, 0.12, s + 0.02), "madera_oscura", rot=(0, 0, 0))
    for (x, y) in ((5.6, -1.0), (4.7, -1.4), (5.3, -2.0)):
        m.torno((x, y, 0.36), [(0.36, 0), (0.4, 0.05), (0.4, 1.0), (0.36, 1.05), (0, 1.05)],
                ("azul_p", "rojo_p", "naranja_p")[int(x * 3) % 3], seg=12)
    # Ventanas altas, extractores y luces laterales
    for sx in (-1, 1):
        for y in (-2.5, 2.5):
            m.ventana((sx * 7.62, y, 3.6), 3.0, 1.2, normal="x", sentido=sx, marco="hierro")
        m.caja((sx * 5.5, yf - 0.02, 3.4), (0.5, 0.14, 0.3), "oscuro")
        m.caja((sx * 5.5, yf - 0.11, 3.36), (0.36, 0.05, 0.16), "neon")
    for x in (-4.0, 4.0):
        m.cil((x, 2.0, 7.25), 0.5, 0.6, "acero", seg=12)
        m.torno((x, 2.0, 7.55), [(0.6, 0), (0.5, 0.2), (0, 0.32)], "gris_liso", seg=12)


@modelo(65, "industrial", "edificio_mediano", (3, 3, 12))
def torre_energia(m):
    # Pilón de celosía que se estrecha, crucetas con aisladores y cables de energía cyan entre ellas
    m.caja((0, 0, 0.15), (3.0, 3.0, 0.3), "hormigon", bisel=0.05)
    def l(z):
        return 1.2 - 0.95 * min(1.0, z / 10.0)
    esq = ((1, 1), (-1, 1), (-1, -1), (1, -1))
    for sx, sy in esq:
        m.barrido([(sx * l(0), sy * l(0), 0.3), (sx * l(5), sy * l(5), 5.0), (sx * l(10), sy * l(10), 10.0),
                   (sx * 0.2, sy * 0.2, 11.4)], 0.07, "gris_liso", seg=5)
        m.caja((sx * l(0), sy * l(0), 0.38), (0.4, 0.4, 0.16), "oscuro", bisel=0.03)
    niv = [0, 1.6, 3.2, 4.8, 6.2, 7.6, 8.8, 10.0]
    for i in range(len(niv) - 1):
        z0, z1 = niv[i] + 0.3 * (i == 0), niv[i + 1]
        for k in range(4):
            (ax, ay), (bx, by) = esq[k], esq[(k + 1) % 4]
            m.barrido([(ax * l(z1), ay * l(z1), z1), (bx * l(z1), by * l(z1), z1)], 0.035, "gris_liso", seg=4)
            if (i + k) % 2:
                m.barrido([(ax * l(z0), ay * l(z0), z0), (bx * l(z1), by * l(z1), z1)], 0.028, "acero", seg=4)
            else:
                m.barrido([(bx * l(z0), by * l(z0), z0), (ax * l(z1), ay * l(z1), z1)], 0.028, "acero", seg=4)
    # Núcleo de energía en la base y conducto central luminoso
    m.cil((0, 0, 0.8), 0.45, 1.0, "oscuro", seg=12)
    m.tubo((0, 0, 0.8), 0.47, 0.3, 0.03, "neon", seg=12)
    m.cil((0, 0, 5.8), 0.07, 9.2, "neon", seg=6, p="conducto_neon")
    for z in (2.5, 5.0, 7.5):
        m.tubo((0, 0, z), 0.14, 0.2, 0.06, "acero", seg=8)
    # Tres crucetas con aisladores de platos y remate con pararrayos
    for z, an in ((7.6, 1.5), (9.2, 1.3), (10.6, 1.05)):
        m.caja((0, 0, z), (an * 2, 0.16, 0.16), "gris_liso")
        for s in (-1, 1):
            m.barrido([(s * an, 0, z), (s * 0.3, 0, z + 0.7)], 0.03, "acero", seg=4)
            x = s * (an - 0.1)
            m.cil((x, 0, z - 0.42), 0.035, 0.7, "plastico_negro", seg=6)
            for k in range(4):
                m.torno((x, 0, z - 0.2 - 0.14 * k), [(0.04, 0), (0.13, -0.04), (0.14, -0.06), (0.04, -0.04)], "plastico",
                        seg=8, cerrar=True)
            m.esfera((x, 0, z - 0.8), 0.09, "neon", seg=8, anillos=5)
    for s in (-1, 1):                                                                 # cables de energía (catenarias)
        for (za, xa), (zb, xb) in (((7.6, 1.4), (9.2, 1.2)), ((9.2, 1.2), (10.6, 0.95))):
            pts = []
            for i in range(6):
                t = i / 5
                pts.append((s * (xa + (xb - xa) * t + 0.25 * math.sin(math.pi * t)), 0,
                            (za - 0.8) + (zb - za) * t))
            m.barrido(pts, 0.03, "neon", seg=4, p="cables_neon")
        m.barrido([(s * 1.4, 0, 6.8), (s * 1.42, 0, 5.0), (s * 0.9, 0, 1.4), (s * 0.45, 0, 1.0)], 0.03, "neon", seg=4,
                  p="cables_neon")
    m.torno((0, 0, 11.3), [(0.28, 0), (0.2, 0.2), (0.06, 0.3), (0.02, 0.75), (0, 0.78)], "acero", seg=8)
    m.esfera((0, 0, 11.72), 0.1, "neon", seg=8, anillos=5)
    m.caja((0, -1.2 + 0.0, 1.5), (0.5, 0.04, 0.5), "amarillo_p", rot=(-7, 0, 0))
    m.prisma([(-0.05, -0.16), (0.08, 0.0), (0.0, 0.0), (0.06, 0.16), (-0.08, 0.0), (0.0, 0.0)], -0.02, 0.02, "negro", "xz",
             c=(0, -1.225, 1.5), rot=(-7, 0, 0))


# --------------------------------------------------------------------------------------------------------------
# Zona del hangar
# --------------------------------------------------------------------------------------------------------------

@modelo(66, "hangar", "edificio_grande", (24, 20, 14))
def hangar_principal(m):
    m.caja((0, 0, 0.15), (24, 20, 0.3), "hormigon", bisel=0.05)
    x0, x1, yf, yb, hm = -11.4, 11.4, -9.4, 9.4, 8.0
    # Muros con grosor (interior real): laterales, trasero y jambas del gran hueco delantero
    for s in (-1, 1):
        m.bloque((s * 10.8, yf, 0.3), (s * 11.4, yb, hm), "blanco")
        m.bloque((s * 10.75, yf - 0.05, 0.3), (s * 11.45, yb + 0.05, 1.3), "oscuro_paneles")
        m.bloque((s * 8.6, yf, 0.3), (s * 10.8, yf + 0.6, hm), "blanco")
        m.bloque((s * 10.78, yf - 0.03, 6.6), (s * 11.43, yb + 0.03, 6.9), "acento")
        for y in (-6.0, -2.0, 2.0, 6.0):
            m.caja((s * 11.42, y, 4.2), (0.3, 0.5, 7.6), "gris_liso", bisel=0.05)
    m.bloque((x0, yb - 0.6, 0.3), (x1, yb, hm), "blanco")
    m.bloque((x0, yb - 0.05, 0.3), (x1, yb + 0.05, 1.3), "oscuro_paneles")
    # Cubierta en bóveda rebajada con cerchas y lucernarios luminosos
    ez = 0.5
    m.prisma(arco_pts(11.9, 11.6, 0, 180, 16, 0, hm, 1.0, ez), yf - 0.4, yb + 0.4, "gris", "xz")
    for y in (yf + 0.3, yb - 0.3):
        tim = [(11.4, hm)] + [(11.6 * math.cos(math.radians(a)), hm + 11.6 * ez * math.sin(math.radians(a)))
                              for a in range(12, 180, 12)] + [(-11.4, hm)]
        m.prisma(tim, y - 0.3, y + 0.3, "blanco", "xz")
    for y in (-6.3, -3.2, 0, 3.2, 6.3):
        m.prisma(arco_pts(11.6, 11.2, 0, 180, 16, 0, hm, 1.0, ez), y - 0.12, y + 0.12, "gris_liso", "xz")
        for x in (-6.5, 0, 6.5):                                                    # luces de techo
            zt = hm + 11.2 * ez * math.sqrt(max(0, 1 - (x / 11.2) ** 2)) - 0.25
            m.caja((x, y, zt), (1.6, 0.5, 0.14), "oscuro")
            m.caja((x, y, zt - 0.09), (1.4, 0.34, 0.05), "neon_blanco")
    for x in (-4.5, 4.5):
        m.caja((x, 0, hm + 11.9 * ez * math.sqrt(1 - (x / 11.9) ** 2) + 0.02), (1.6, 15.0, 0.1), "cristal",
               rot=(0, math.degrees(math.atan(ez * x / math.sqrt(11.9 ** 2 - x * x))), 0))
    # Suelo interior con marcas de aterrizaje pintadas en relieve fino
    m.bloque((-10.8, yf + 0.0, 0.3), (10.8, yb - 0.6, 0.36), "gris_liso")
    m.tubo((0, 0.5, 0.37), 4.6, 0.02, 0.35, "amarillo_p", seg=32)
    m.tubo((0, 0.5, 0.37), 2.2, 0.02, 0.2, "blanco_liso", seg=24)
    for a in (0, 90):
        m.caja((0, 0.5, 0.37), (3.6, 0.3, 0.02), "blanco_liso", rot=(0, 0, a))
    for s in (-1, 1):
        m.caja((s * 6.5, -1.0, 0.37), (0.3, 15.0, 0.02), "rayas")
    for k in range(8):
        a = math.radians(45 * k)
        m.cil((5.2 * math.cos(a), 0.5 + 5.2 * math.sin(a), 0.38), 0.14, 0.05, "neon", seg=8)
    # Portón gigante de dos hojas correderas (piezas aparte, entreabiertas) con guía superior
    m.bloque((-11.0, yf - 0.3, 7.2), (11.0, yf - 0.05, 7.5), "hierro")
    m.bloque((-8.6, yf, 7.5), (8.6, yf + 0.6, hm), "blanco")
    for nom, xa, xb in (("porton_izq", -10.6, -3.0), ("porton_der", 3.0, 10.6)):
        m.bloque((xa, yf - 0.28, 0.36), (xb, yf - 0.08, 7.18), "gris", p=nom)
        m.marco(((xa + xb) / 2, yf - 0.3, 3.77), xb - xa, 6.82, 0.22, 0.08, "gris_liso", p=nom)
        for z in (2.0, 3.8, 5.6):
            m.caja(((xa + xb) / 2, yf - 0.3, z), (xb - xa - 0.4, 0.06, 0.16), "gris_liso", p=nom)
        m.caja(((xa + xb) / 2, yf - 0.3, 0.9), (xb - xa - 0.2, 0.05, 0.5), "rayas", p=nom)
        xc = xb - 1.2 if xa < 0 else xa + 1.2
        m.caja((xc, yf - 0.31, 4.6), (1.2, 0.05, 1.2), "cristal_oscuro")
        m.caja((xb - 0.25 if xa < 0 else xa + 0.25, yf - 0.31, 3.6), (0.1, 0.05, 3.0), "neon")
    # Puente grúa interior: carriles, viga, carro y gancho; y un brazo de montaje
    for s in (-1, 1):
        m.caja((s * 10.5, 0, 6.6), (0.5, 17.6, 0.4), "amarillo_p")
        for y in (-7.5, -2.5, 2.5, 7.5):
            m.prisma([(0, 0), (0.6, 0), (0, -0.9)], -0.1, 0.1, "hierro", "xz", c=(s * 10.8 - (0.6 if s > 0 else 0), y, 6.4)) \
                if s < 0 else m.prisma([(0, 0), (-0.6, 0), (0, -0.9)], -0.1, 0.1, "hierro", "xz", c=(10.8, y, 6.4))
    G = "puente_grua"
    m.caja((0, 3.0, 7.0), (21.4, 0.7, 0.6), "amarillo_p", bisel=0.05, p=G)
    m.caja((0, 3.0, 7.0), (21.44, 0.3, 0.2), "rayas", p=G)
    for s in (-1, 1):
        m.caja((s * 10.5, 3.0, 6.95), (0.7, 1.4, 0.5), "hierro", bisel=0.04, p=G)
    m.caja((-2.5, 3.0, 6.55), (1.2, 1.0, 0.5), "oscuro", bisel=0.05, p="carro_grua")
    m.cil((-2.5, 3.0, 5.2), 0.03, 2.3, "acero", seg=5, p="carro_grua")
    m.caja((-2.5, 3.0, 4.0), (0.4, 0.3, 0.4), "amarillo_p", bisel=0.05, p="carro_grua")
    m.barrido([(-2.5, 3.0, 3.8), (-2.5, 3.0, 3.55), (-2.3, 3.0, 3.4), (-2.5, 3.0, 3.25), (-2.72, 3.0, 3.42)],
              [0.05, 0.05, 0.055, 0.05, 0.02], "hierro", seg=6, p="carro_grua")
    # Mobiliario interior: banco de herramientas, bidones, cajas y cuadro de control
    m.bloque((6.5, 7.2, 0.36), (10.2, 8.6, 1.5), "gris")
    m.bloque((6.4, 7.1, 1.5), (10.3, 8.7, 1.62), "acero")
    m.bloque((6.5, 8.6, 1.62), (10.2, 8.76, 3.4), "oscuro_paneles")
    for i in range(5):
        m.caja((7.0 + 0.7 * i, 8.56, 2.5), (0.1, 0.05, 0.8 - 0.1 * (i % 2)), "cromo")
    for (x, y, mat) in ((-9.6, 7.6, "azul_p"), (-8.7, 7.9, "rojo_p"), (-9.3, 6.6, "naranja_p")):
        m.torno((x, y, 0.36), [(0.38, 0), (0.42, 0.05), (0.42, 1.1), (0.38, 1.15), (0, 1.15)], mat, seg=12)
    for (c, s) in (((-7.2, 7.8, 1.0), 1.3), ((-5.6, 8.0, 0.9), 1.1), ((-7.0, 7.9, 2.15), 0.95)):
        m.caja(c, (s, s, s), "gris", bisel=0.05)
        m.caja(c, (s + 0.03, 0.16, s + 0.03), "tela_naranja")
    m.caja((-10.5, -3.0, 2.2), (0.3, 1.6, 2.2), "oscuro", bisel=0.04)
    m.caja((-10.33, -3.0, 2.5), (0.03, 1.3, 1.0), "neon", p="pantalla_neon")
    # Exterior: rótulo, balizas de la entrada, torretas de ventilación y antena
    m.caja((0, yf - 0.1, hm + 3.4), (8.0, 0.2, 1.5), "oscuro", bisel=0.05)
    m.texto("HANGAR", (0, yf - 0.24, hm + 3.4), 0.95, 0.12, "neon")
    for s in (-1, 1):
        m.cil((s * 9.6, yf - 0.6, 1.1), 0.16, 1.6, "rayas", seg=10)
        m.esfera((s * 9.6, yf - 0.6, 2.0), 0.2, "neon_naranja", seg=10, anillos=6)
        for y in (-4.0, 4.0):
            zt = hm + 11.9 * ez * math.sqrt(1 - (8.5 / 11.9) ** 2)
            m.cil((s * 8.5, y, zt + 0.4), 0.6, 1.0, "gris_liso", seg=12)
            m.torno((s * 8.5, y, zt + 0.9), [(0.75, 0), (0.6, 0.2), (0, 0.36)], "gris", seg=12)
    m.cil((0, 7.0, hm + 5.7), 0.07, 1.6, "acero", seg=6)
    m.esfera((0, 7.0, hm + 6.55), 0.12, "neon_rojo", seg=8, anillos=5)
    for sx in (-1, 1):
        for y in (-4.0, 0, 4.0):
            m.ventana((sx * 11.42, y, 4.4), 2.6, 1.6, normal="x", sentido=sx)


@modelo(67, "hangar", "edificio_mediano", (12, 12, 0.5))
def plataforma_aterrizaje(m):
    # Losa octogonal metálica con faldón, superficie con agarre, marcas pintadas en relieve y luces perimetrales
    def oct(r, c=0.293):
        k = r * (1 - c * 1.0)
        return [(-k, -r), (k, -r), (r, -k), (r, k), (k, r), (-k, r), (-r, k), (-r, -k)]
    m.prisma(oct(6.0, 0.45), 0.0, 0.22, "oscuro", "xy")
    m.prisma(oct(5.85, 0.45), 0.22, 0.4, "gris", "xy")
    m.prisma(oct(5.5, 0.45), 0.4, 0.43, "rejilla", "xy")
    # Marcas: círculo exterior, círculo interior, H central y flechas de aproximación
    m.tubo((0, 0, 0.44), 4.6, 0.02, 0.32, "amarillo_p", seg=40)
    m.tubo((0, 0, 0.44), 2.4, 0.02, 0.18, "blanco_liso", seg=28)
    for s in (-1, 1):
        m.caja((s * 0.9, 0, 0.44), (0.4, 2.6, 0.02), "blanco_liso")
    m.caja((0, 0, 0.44), (1.5, 0.4, 0.02), "blanco_liso")
    for k in range(4):
        a = 90 * k
        ra = math.radians(a)
        m.prisma([(-0.5, 0.0), (0.5, 0.0), (0, 0.7)], 0.43, 0.45, "amarillo_p", "xy",
                 c=(5.0 * math.sin(ra) * -1 * -1, -5.0 * math.cos(ra), 0), rot=(0, 0, a))
        m.caja((3.55 * math.cos(ra + 0.785), 3.55 * math.sin(ra + 0.785), 0.44), (1.6, 0.25, 0.02), "rayas",
               rot=(0, 0, a + 45))
    # Luces perimetrales empotradas (neón) con su carcasa y cuatro balizas de esquina
    pts = oct(5.72, 0.45)
    for i in range(8):
        (ax, ay), (bx, by) = pts[i], pts[(i + 1) % 8]
        L = math.hypot(bx - ax, by - ay)
        n = max(2, int(L / 1.2))
        ang = math.degrees(math.atan2(by - ay, bx - ax))
        for j in range(n):
            t = (j + 0.5) / n
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            m.caja((x, y, 0.43), (0.5, 0.2, 0.06), "acero", rot=(0, 0, ang))
            m.caja((x, y, 0.455), (0.4, 0.1, 0.03), "neon", rot=(0, 0, ang))
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 4.55, sy * 4.55
            m.cil((x, y, 0.5), 0.2, 0.16, "oscuro", seg=10)
            m.esfera((x, y, 0.62), 0.14, "neon_naranja", seg=8, anillos=5)
    # Rampa de acceso frontal, tomas de servicio y anclajes de amarre
    m.prisma([(-6.9, 0.0), (-5.9, 0.0), (-5.9, 0.4)], -1.5, 1.5, "rejilla", "yz")
    for (x, y) in ((3.0, -3.0), (-3.0, 3.0)):
        m.caja((x, y, 0.45), (0.6, 0.6, 0.05), "acero", bisel=0.015)
        m.cil((x, y, 0.49), 0.14, 0.05, "rojo_p", seg=8)
    for k in range(6):
        a = math.radians(60 * k + 30)
        m.tubo((3.4 * math.cos(a), 3.4 * math.sin(a), 0.46), 0.14, 0.05, 0.035, "acero", seg=8)
    m.anclaje("centro_aterrizaje", (0, 0, 0.45))


@modelo(68, "hangar", "vehiculo", (2, 2, 8))
def brazo_mecanico_hangar(m):
    # Brazo robótico de seis ejes: base, hombro, dos tramos con actuadores, muñeca y pinza de tres dedos
    m.cil((0, 0, 0.1), 1.0, 0.2, "oscuro", seg=20)
    m.tubo((0, 0, 0.2), 0.98, 0.05, 0.1, "rayas", seg=20)
    for k in range(8):
        a = math.radians(45 * k)
        m.cil((0.85 * math.cos(a), 0.85 * math.sin(a), 0.23), 0.06, 0.08, "acero", seg=6)
    m.cil((0, 0, 0.45), 0.7, 0.5, "gris_liso", seg=18)
    m.tubo((0, 0, 0.5), 0.72, 0.08, 0.04, "neon", seg=18)
    G = "torreta"
    m.cil((0, 0, 0.95), 0.6, 0.5, "blanco_liso", seg=18, p=G)
    for s in (-1, 1):
        m.caja((s * 0.42, 0, 1.6), (0.18, 0.7, 1.0), "blanco_liso", bisel=0.05, p=G)
    A, B, C, D = (0, 0, 1.75), (0, 0.5, 4.5), (0, -0.4, 6.6), (0, -0.75, 7.2)
    m.cil(A, 0.34, 0.9, "acero", eje="x", seg=14, p=G)
    m.cil((0.47, 0, 1.75), 0.2, 0.06, "neon", eje="x", seg=12)
    B1 = "brazo_inferior"
    m.barrido([A, B], [0.3, 0.24], "blanco_liso", seg=8, p=B1)
    m.barrido([(0.0, 0.1, 2.3), (0, 0.42, 4.0)], [0.32, 0.27], "acento", seg=4, p=B1) if False else None
    m.caja((0, 0.25, 3.1), (0.5, 0.36, 1.2), "gris_liso", bisel=0.06, rot=(-10, 0, 0), p=B1)
    m.caja((0.26, 0.25, 3.1), (0.03, 0.2, 0.9), "neon", rot=(-10, 0, 0))
    m.barrido([(-0.2, -0.3, 1.3), (-0.2, -0.05, 2.6)], 0.09, "oscuro", seg=8, p=G)        # actuador
    m.barrido([(-0.2, -0.05, 2.6), (-0.2, 0.2, 3.7)], 0.05, "cromo", seg=8, p=B1)
    m.cil(B, 0.3, 0.8, "acero", eje="x", seg=14, p=B1)
    m.cil((0.42, B[1], B[2]), 0.16, 0.06, "neon", eje="x", seg=10)
    B2 = "brazo_superior"
    m.barrido([B, C], [0.22, 0.16], "blanco_liso", seg=8, p=B2)
    m.caja((0, 0.1, 5.45), (0.36, 0.3, 0.9), "gris_liso", bisel=0.05, rot=(23, 0, 0), p=B2)
    m.barrido([(0.18, 0.45, 4.7), (0.24, 0.3, 5.4), (0.16, -0.2, 6.3)], 0.035, "goma", seg=5, p=B2)
    m.cil(C, 0.2, 0.5, "acero", eje="x", seg=12, p=B2)
    Mn = "muneca"
    m.barrido([C, D], [0.13, 0.12], "gris_liso", seg=8, p=Mn)
    m.cil(D, 0.2, 0.16, "oscuro", seg=12, rot=(30, 0, 0), p=Mn)
    m.tubo(D, 0.21, 0.05, 0.03, "neon", seg=12, rot=(30, 0, 0))
    # Pinza de tres dedos articulados
    from mathutils import Euler, Vector
    E = Euler((math.radians(30), 0, 0), "XYZ").to_matrix()
    for k in range(3):
        a = math.radians(120 * k + 90)
        def P(r, h):
            v = E @ Vector((r * math.cos(a), r * math.sin(a), h))
            return (D[0] + v.x, D[1] + v.y, D[2] + v.z)
        m.barrido([P(0.14, 0.05), P(0.3, 0.3), P(0.28, 0.6), P(0.14, 0.82)], [0.05, 0.05, 0.04, 0.025], "acero", seg=5,
                  p="pinza")
        m.esfera(P(0.3, 0.3), 0.07, "oscuro", seg=6, anillos=4, p="pinza")
    m.anclaje("pinza", D)
    # Armario de control con pantalla y mazo de cables
    m.caja((-0.75, 0.6, 0.55), (0.4, 0.4, 0.7), "gris_claro", bisel=0.04)
    m.caja((-0.75, 0.39, 0.62), (0.26, 0.02, 0.2), "neon", p="pantalla_neon")
    m.barrido([(-0.6, 0.5, 0.3), (-0.3, 0.3, 0.24), (0, 0.4, 0.3)], 0.04, "goma", seg=5)


@modelo(69, "hangar", "prop", (2, 1, 3))
def consola_control_hangar(m):
    # Pedestal, pupitre inclinado con teclado de teclas 3D, botones y palancas, y pantalla holográfica
    m.caja((0, 0.05, 0.06), (1.7, 0.9, 0.12), "oscuro", bisel=0.03)
    m.prisma([(-0.3, 0.12), (0.4, 0.12), (0.36, 1.1), (-0.2, 1.1)], -0.7, 0.7, "blanco_liso", "yz")
    m.caja((0, -0.26, 0.6), (1.0, 0.03, 0.6), "gris_liso")
    for k in range(5):
        m.caja((0, -0.285 + 0.004 * k, 0.4 + 0.1 * k), (0.8, 0.02, 0.04), "oscuro")
    m.caja((0, -0.27, 0.95), (1.2, 0.03, 0.06), "neon")
    # Pupitre inclinado
    m.prisma([(-0.5, 1.1), (0.45, 1.1), (0.45, 1.5), (-0.5, 1.22)], -0.95, 0.95, "gris", "yz")
    inc = math.degrees(math.atan2(0.28, 0.95))
    from mathutils import Euler, Vector
    E = Euler((math.radians(inc), 0, 0), "XYZ").to_matrix()
    def sobre(x, y, dz=0.0):
        """Punto sobre el plano inclinado del pupitre (y local de -0.45 a 0.4)."""
        z = 1.22 + (y + 0.5) * 0.28 / 0.95
        return (x, y, z + dz)
    for i in range(10):                                                              # teclado 10 × 3
        for j in range(3):
            m.caja(sobre(-0.52 + 0.085 * i, -0.38 + 0.085 * j, 0.012), (0.07, 0.07, 0.03), "plastico_negro",
                   rot=(inc, 0, 0))
    for i, mat in enumerate(("neon_rojo", "neon_amarillo", "neon_verde", "neon")):   # botones luminosos
        m.cil(sobre(0.5 + 0.11 * (i % 2), -0.36 + 0.12 * (i // 2), 0.02), 0.04, 0.04, mat, seg=8, rot=(inc, 0, 0))
    for i in range(2):                                                               # palancas
        p = sobre(-0.78 + 0.14 * i, -0.3, 0.0)
        m.caja(p, (0.1, 0.24, 0.02), "oscuro", rot=(inc, 0, 0))
        m.cil((p[0], p[1] + 0.03 * (1 - 2 * i), p[2] + 0.1), 0.018, 0.2, "cromo", seg=5, rot=(inc - 15 + 30 * i, 0, 0))
        m.esfera((p[0], p[1] + 0.06 * (1 - 2 * i), p[2] + 0.2), 0.04, "rojo_p", seg=6, anillos=4)
    for i in range(3):                                                               # diales
        p = sobre(-0.4 + 0.3 * i, 0.0, 0.015)
        m.cil(p, 0.06, 0.04, "cromo", seg=10, rot=(inc, 0, 0))
        m.caja((p[0], p[1], p[2] + 0.025), (0.012, 0.08, 0.01), "negro", rot=(inc, 0, 40 * i))
    m.caja(sobre(0.55, 0.05, 0.01), (0.5, 0.26, 0.02), "pantalla", rot=(inc, 0, 0))
    m.caja(sobre(0.55, 0.05, 0.022), (0.42, 0.18, 0.006), "neon", rot=(inc, 0, 0), p="pantalla_neon")
    # Proyector y pantalla holográfica principal con gráficos en relieve
    m.caja((0, 0.36, 1.56), (1.5, 0.14, 0.12), "oscuro", bisel=0.02)
    m.caja((0, 0.36, 1.63), (1.3, 0.05, 0.03), "neon")
    H = "holograma_neon"
    m.caja((0, 0.36, 2.35), (1.7, 0.03, 1.2), "neon", p=H)
    m.marco((0, 0.36, 2.35), 1.8, 1.3, 0.04, 0.06, "neon_blanco", p="holograma_marco_neon")
    m.prisma([(-0.45, -0.1), (0.5, 0.0), (-0.45, 0.1), (-0.3, 0.0)], 0.33, 0.35, "neon_blanco", "xz", c=(-0.25, 0, 2.5),
             p="holograma_marco_neon")                                              # silueta de nave
    for k in range(4):
        m.caja((0.5, 0.34, 2.75 - 0.14 * k), (0.5 - 0.08 * (k % 2), 0.02, 0.05), "neon_blanco", p="holograma_marco_neon")
        m.caja((-0.62 + 0.14 * k, 0.34, 1.95 + 0.04 * k), (0.09, 0.02, 0.16 + 0.08 * k), "neon_verde")
    m.tubo((0.5, 0.34, 2.05), 0.16, 0.02, 0.035, "neon_naranja", eje="y", seg=12)


@modelo(70, "hangar", "prop", (6, 2, 6))
def rack_piezas_nave(m):
    # Estantería pesada de tres niveles con piezas de nave apoyadas y colgadas
    for sx in (-2.85, 0, 2.85):
        for sy in (-0.85, 0.85):
            m.caja((sx, sy, 3.0), (0.2, 0.2, 6.0), "naranja_p", bisel=0.03)
            m.caja((sx, sy, 0.04), (0.4, 0.4, 0.08), "oscuro")
        m.caja((sx, 0, 5.9), (0.14, 1.7, 0.14), "naranja_p")
        m.barrido([(sx, -0.85, 0.3), (sx, 0.85, 1.9)], 0.03, "acero", seg=4)
        m.barrido([(sx, 0.85, 2.3), (sx, -0.85, 3.9)], 0.03, "acero", seg=4)
    niveles = (0.5, 2.3, 4.1)
    for z in niveles:
        for sy in (-0.85, 0.85):
            m.caja((0, sy, z), (5.9, 0.12, 0.22), "azul_p")
        m.caja((0, 0, z + 0.13), (5.7, 1.7, 0.05), "rejilla")
    m.barrido([(-2.85, 0.88, 0.5), (0, 0.88, 4.1)], 0.03, "acero", seg=4)
    m.barrido([(2.85, 0.88, 0.5), (0, 0.88, 4.1)], 0.03, "acero", seg=4)
    # Nivel 1: tobera de motor, tren de aterrizaje y bidón
    z = niveles[0] + 0.16
    m.torno((-1.8, 0, z), [(0.6, 0), (0.7, 0.12), (0.42, 0.9), (0.46, 1.25), (0.36, 1.25), (0.32, 0.9), (0.56, 0.14),
                           (0, 0.12)], "hierro", seg=14)
    m.tubo((-1.8, 0, z + 1.0), 0.47, 0.1, 0.05, "cobre", seg=14)
    m.cil((0.6, 0, z + 0.3), 0.3, 0.26, "goma", eje="y", seg=14)
    m.cil((0.6, 0, z + 0.3), 0.14, 0.3, "cromo", eje="y", seg=8)
    m.barrido([(0.6, 0, z + 0.3), (0.9, 0, z + 0.9), (1.5, 0, z + 1.2)], [0.07, 0.09, 0.11], "acero", seg=8)
    m.barrido([(0.8, 0.12, z + 0.5), (1.3, 0.12, z + 1.25)], 0.04, "cromo", seg=6)
    m.torno((2.3, 0.1, z), [(0.34, 0), (0.38, 0.05), (0.38, 0.9), (0.34, 0.95), (0, 0.95)], "rojo_p", seg=12)
    # Nivel 2: panel de ala, placas de casco apiladas y cúpula de cabina
    z = niveles[1] + 0.16
    m.prisma([(-1.6, 0), (1.4, 0), (0.9, 1.2), (-0.6, 1.2)], -0.07, 0.07, "blanco_liso", "xz", c=(-1.3, 0.35, z),
             rot=(14, 0, 0))
    m.prisma([(-1.4, 0.1), (1.2, 0.1), (1.12, 0.3), (-1.32, 0.3)], -0.085, 0.085, "acento", "xz", c=(-1.3, 0.35, z),
             rot=(14, 0, 0))
    for k in range(4):
        m.caja((1.0, -0.1, z + 0.06 + 0.11 * k), (1.3 - 0.06 * k, 1.0, 0.09), "gris" if k % 2 else "blanco_liso",
               bisel=0.02, rot=(0, 0, 3 * k))
    m.cupula((2.25, 0.0, z), 0.5, "cristal", grosor=0.05, seg=14, anillos=4, altura=1.0)
    m.tubo((2.25, 0, z + 0.04), 0.52, 0.08, 0.05, "acero", seg=14)
    # Nivel 3: célula de energía, caja de piezas y tubos
    z = niveles[2] + 0.16
    m.cil((-2.0, 0, z + 0.5), 0.36, 0.9, "cristal", seg=12)
    m.cil((-2.0, 0, z + 0.5), 0.16, 0.8, "neon", seg=8)
    for dz in (0.07, 0.93):
        m.cil((-2.0, 0, z + dz), 0.4, 0.14, "acero", seg=12)
    m.caja((0.1, 0, z + 0.4), (1.5, 1.1, 0.8), "gris", bisel=0.04)
    m.caja((0.1, 0, z + 0.4), (0.18, 1.13, 0.83), "tela_naranja")
    for k in range(3):
        m.cil((1.9, -0.3 + 0.3 * k, z + 0.14), 0.13, 1.6, "acero" if k != 1 else "cobre", eje="x", seg=8)
    m.cil((1.9, -0.15, z + 0.38), 0.13, 1.6, "acero", eje="x", seg=8)
    # Piezas colgadas en el frente: aleta, llaves de impacto y etiquetas luminosas
    m.cil((1.45, -1.0, 3.9), 0.02, 0.5, "acero", seg=4)
    m.prisma([(-0.3, 0), (0.3, 0), (0.1, -0.9), (-0.2, -0.9)], -0.03, 0.03, "blanco_liso", "xz", c=(1.45, -1.0, 3.65))
    for i, z in enumerate(niveles):
        m.caja((-2.3, -0.92, z), (0.6, 0.02, 0.14), "oscuro")
        m.caja((-2.3, -0.935, z), (0.44, 0.015, 0.06), "neon")
