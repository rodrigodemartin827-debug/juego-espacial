"""Ronda 6 · Zona industrial (modelos 51-60)."""

import math

from geometria import arco_pts
from registro import modelo

PERFIL_RAIL = [(-0.07, 0), (0.07, 0), (0.07, 0.03), (0.02, 0.05), (0.02, 0.12), (0.05, 0.14), (0.05, 0.18), (-0.05, 0.18),
               (-0.05, 0.14), (-0.02, 0.12), (-0.02, 0.05), (-0.07, 0.03)]


@modelo(51, "industrial", "vehiculo", (3, 2, 2))
def vagoneta_mina(m):
    R = m.rng
    # Tramo de vía, bastidor con cuatro ruedas de pestaña, cuba troncocónica con refuerzos y mineral 3D
    for k in range(5):
        m.caja((-1.2 + 0.6 * k, 0, 0.05), (0.22, 1.9, 0.1), "madera_oscura")
    for s in (-1, 1):
        m.prisma(PERFIL_RAIL, -1.5, 1.5, "hierro_viejo", "yz", c=(0, s * 0.6, 0.1))
    P = "vagoneta"
    m.caja((0, 0, 0.62), (2.3, 1.0, 0.14), "hierro", bisel=0.02, p=P)
    for sx in (-1, 1):
        m.cil((sx * 0.75, 0, 0.5), 0.05, 1.5, "acero", eje="y", seg=6, p=P)
        for sy in (-1, 1):
            m.cil((sx * 0.75, sy * 0.6, 0.5), 0.22, 0.1, "hierro_viejo", eje="y", seg=14, p=P)
            m.cil((sx * 0.75, sy * 0.53, 0.5), 0.27, 0.03, "hierro_viejo", eje="y", seg=14, p=P)
            m.cil((sx * 0.75, sy * 0.66, 0.5), 0.08, 0.04, "acero", eje="y", seg=8, p=P)
        m.caja((sx * 1.2, 0, 0.62), (0.14, 0.5, 0.2), "hierro", p=P)
        m.cil((sx * 1.32, 0, 0.62), 0.1, 0.12, "acero", eje="x", seg=8, p=P)                 # topes
    # Cuba: cuatro chapas inclinadas con grosor
    cu = [(-1.0, 0.7), (1.0, 0.7), (1.3, 1.75), (1.22, 1.75), (0.94, 0.78), (-0.94, 0.78), (-1.22, 1.75), (-1.3, 1.75)]
    for s in (-1, 1):
        m.prisma([(-1.0, 0.7), (1.0, 0.7), (1.3, 1.75), (-1.3, 1.75)], s * 0.62, s * 0.7, "hierro_viejo", "xz",
                 c=(0, 0, 0), rot=(s * -8, 0, 0), p=P)
    m.prisma(cu, -0.66, 0.66, "hierro_viejo", "xz", p=P)
    for sx in (-1, 1):
        m.barrido([(sx * 1.02, -0.72, 0.72), (sx * 1.31, -0.82, 1.74)], 0.04, "hierro", seg=4, p=P)
        m.barrido([(sx * 1.02, 0.72, 0.72), (sx * 1.31, 0.82, 1.74)], 0.04, "hierro", seg=4, p=P)
    m.barrido([(-1.31, -0.84, 1.76), (1.31, -0.84, 1.76), (1.31, 0.84, 1.76), (-1.31, 0.84, 1.76)], 0.045, "hierro", seg=5,
              cerrado=True, p=P)
    for x in (-0.5, 0.5):
        for s in (-1, 1):
            m.caja((x, s * 0.76, 1.2), (0.08, 0.04, 1.0), "hierro", rot=(s * -8, 0, 0), p=P)
    m.barrido([(1.3, -0.3, 1.5), (1.55, -0.3, 1.45), (1.55, 0.3, 1.45), (1.3, 0.3, 1.5)], 0.03, "acero", seg=5, p=P)
    # Carga: montón de piedras con vetas de mineral de colores y dos cristales luminosos
    m.bloque((-1.1, -0.6, 0.8), (1.1, 0.6, 1.5), "piedra_oscura", p=P)
    mats = ["piedra", "piedra_oscura", "cobre", m.color("#C8A53A", 0.4, 0.8), "hierro_viejo", m.color("#7A4FD0", 0.3, 0.2)]
    for i in range(20):
        x, y = R.uniform(-0.95, 0.95), R.uniform(-0.5, 0.5)
        z = 1.62 + 0.3 * (1 - (x / 1.1) ** 2) * (1 - (y / 0.7) ** 2) + R.uniform(-0.05, 0.06)
        s = R.uniform(0.36, 0.56)
        m.roca((x, y, z), (s, s * R.uniform(0.7, 1.0), s * 0.75), mats[i % 6], semilla=i * 1.9, sub=1, p=P,
               rot=(R.uniform(0, 90), R.uniform(0, 90), 0))
    for (x, y, a) in ((0.3, -0.2, 12), (-0.5, 0.2, -15)):
        m.torno((x, y, 1.9), [(0.07, 0), (0.1, 0.1), (0.07, 0.36), (0.0, 0.46)], "neon", seg=5, rot=(a, a, 0),
                p="mineral_neon")


@modelo(52, "industrial", "prop", (4, 1, 0.3))
def rail_mina(m):
    # Dos rieles de perfil real, seis traviesas de madera, placas de asiento con clavos y balasto
    m.caja((0, 0, 0.03), (4.0, 1.0, 0.06), "tierra")
    R = m.rng
    for i in range(14):
        m.roca((R.uniform(-1.9, 1.9), R.uniform(-0.42, 0.42), 0.07), (0.16, 0.14, 0.08), "piedra", semilla=i, sub=1)
    for k in range(6):
        x = -1.67 + 0.667 * k
        m.caja((x, 0, 0.1), (0.24, 0.98, 0.1), "madera_oscura", bisel=0.015)
        for s in (-1, 1):
            m.caja((x, s * 0.3, 0.155), (0.2, 0.2, 0.012), "hierro_viejo")
            for d in (-1, 1):
                m.cil((x + d * 0.06, s * 0.3 + d * 0.085, 0.17), 0.018, 0.03, "acero", seg=5)
    for s in (-1, 1):
        m.prisma(PERFIL_RAIL, -2.0, 2.0, "hierro_viejo", "yz", c=(0, s * 0.3, 0.12))
        m.caja((0, s * 0.3, 0.301), (4.0, 0.06, 0.004), "acero")
        for x in (-1.99, 1.99):
            m.caja((x, s * 0.3, 0.2), (0.02, 0.03, 0.1), "hierro")


@modelo(53, "industrial", "prop", (4, 0.5, 5))
def viga_mina(m):
    # Cuadro de entibación en H: dos pies derechos de madera gruesa, travesaño arriba, jabalcones y herrajes
    for s in (-1, 1):
        x = s * 1.7
        m.caja((x, 0, 2.3), (0.46, 0.46, 4.6), "madera", bisel=0.04)
        m.caja((x, 0, 0.12), (0.6, 0.6, 0.24), "hierro_viejo", bisel=0.03)
        m.caja((x, 0, 4.3), (0.52, 0.52, 0.3), "hierro_viejo")
        for z in (1.4, 2.9):
            m.caja((x, 0, z), (0.5, 0.5, 0.1), "hierro")
            m.cil((x, -0.26, z), 0.04, 0.04, "acero", eje="y", seg=6)
        m.barrido([(x - s * 0.2, 0, 3.3), (x - s * 1.0, 0, 4.55)], 0.11, "madera_oscura", seg=4)
        m.caja((x - s * 0.24, -0.02, 3.3), (0.3, 0.42, 0.3), "hierro_viejo", bisel=0.03)
    m.caja((0, 0, 4.78), (4.0, 0.5, 0.44), "madera", bisel=0.04)
    for x in (-1.7, 0, 1.7):
        m.caja((x, 0, 4.78), (0.14, 0.54, 0.48), "hierro")
        for sz in (-0.12, 0.12):
            m.cil((x, -0.28, 4.78 + sz), 0.035, 0.04, "acero", eje="y", seg=6)
    for x in (-0.7, 0.7):
        m.caja((x, -0.02, 4.57), (0.3, 0.42, 0.14), "hierro_viejo")
    # Cuñas de apriete, farol de mina y cable
    for s in (-1, 1):
        m.prisma([(0, 0), (0.3, 0), (0, 0.12)], -0.2, 0.2, "madera_clara", "xz", c=(s * 1.7 - 0.15, 0, 4.47))
    m.barrido([(0, -0.26, 4.6), (0, -0.4, 4.5), (0, -0.4, 4.3)], 0.02, "hierro", seg=4)
    m.torno((0, -0.4, 3.98), [(0.06, 0), (0.12, 0.04), (0.12, 0.26), (0.04, 0.32)], "hierro", seg=8)
    m.cil((0, -0.4, 4.13), 0.085, 0.18, "neon_amarillo", seg=8)
    m.barrido([(-1.9, -0.2, 4.95), (-0.9, -0.24, 4.85), (0, -0.26, 4.92), (0.9, -0.24, 4.85), (1.9, -0.2, 4.95)], 0.02,
              "goma", seg=4)


@modelo(54, "industrial", "vehiculo", (4, 3, 8))
def grua_carga(m):
    # Base con contrapesos y corona giratoria, columna, brazo articulado en dos tramos con pistones, cable y gancho
    m.caja((0, 0, 0.2), (3.0, 3.0, 0.4), "oscuro", bisel=0.06)
    m.caja((0, 0, 0.42), (3.04, 3.04, 0.06), "rayas")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.cil((sx * 1.2, sy * 1.2, 0.5), 0.1, 0.14, "acero", seg=8)
    m.cil((0, 0, 0.55), 1.0, 0.3, "hierro", seg=20)
    m.tubo((0, 0, 0.72), 1.02, 0.06, 0.08, "acero", seg=20)
    G = "torre_giratoria"
    m.cil((0, 0, 0.9), 0.9, 0.3, "amarillo_p", seg=20, p=G)
    m.caja((0, 0.75, 1.5), (1.5, 0.9, 1.0), "hierro", bisel=0.05, p=G)                    # contrapeso
    m.caja((0, 0.75, 1.5), (1.54, 0.5, 0.2), "rayas", p=G)
    m.caja((0, -0.05, 2.7), (0.7, 0.7, 3.4), "amarillo_p", bisel=0.06, p=G)               # columna
    m.caja((0, -0.05, 2.0), (0.76, 0.76, 0.12), "oscuro", p=G)
    # Cabina del operador
    m.caja((-0.75, -0.2, 1.75), (0.8, 1.0, 1.4), "blanco_liso", bisel=0.06, p=G)
    m.caja((-0.75, -0.72, 1.95), (0.6, 0.05, 0.7), "cristal")
    m.caja((-1.16, -0.2, 1.95), (0.05, 0.7, 0.7), "cristal")
    m.caja((-0.75, -0.2, 2.5), (0.86, 1.06, 0.1), "oscuro", p=G)
    m.esfera((-0.75, -0.2, 2.62), 0.1, "neon_naranja", seg=8, anillos=5)
    # Primer tramo del brazo (sube hacia el frente) y segundo tramo
    A, B, C = (0, -0.05, 4.3), (0, -1.6, 6.9), (0, -3.3, 7.3)
    B1 = "brazo_1"
    for sx in (-1, 1):
        m.barrido([(sx * 0.22, A[1], A[2]), (sx * 0.18, B[1], B[2])], 0.14, "amarillo_p", seg=4, p=B1)
    for k in range(5):
        t = (k + 0.5) / 5
        y, z = A[1] + (B[1] - A[1]) * t, A[2] + (B[2] - A[2]) * t
        m.cil((0, y, z), 0.05, 0.4, "hierro", eje="x", seg=5, p=B1)
    m.cil((0, A[1], A[2]), 0.24, 0.8, "acero", eje="x", seg=12)
    m.cil((0, B[1], B[2]), 0.2, 0.7, "acero", eje="x", seg=12)
    # pistón hidráulico de la columna al brazo
    m.barrido([(0, -0.42, 2.6), (0, -0.75, 4.3)], 0.11, "oscuro", seg=8, p=G)
    m.barrido([(0, -0.75, 4.3), (0, -1.05, 5.6)], 0.06, "cromo", seg=8, p=B1)
    B2 = "brazo_2"
    for sx in (-1, 1):
        m.barrido([(sx * 0.14, B[1], B[2]), (sx * 0.1, C[1], C[2])], 0.1, "amarillo_p", seg=4, p=B2)
    for k in range(3):
        t = (k + 0.5) / 3
        m.cil((0, B[1] + (C[1] - B[1]) * t, B[2] + (C[2] - B[2]) * t), 0.04, 0.26, "hierro", eje="x", seg=5, p=B2)
    m.barrido([(0, -1.0, 6.2), (0, -1.9, 6.75)], 0.07, "oscuro", seg=6, p=B1)
    m.barrido([(0, -1.9, 6.75), (0, -2.5, 6.98)], 0.04, "cromo", seg=6, p=B2)
    # Polea, cable de acero, pasteca y gancho
    m.cil((0, C[1], C[2]), 0.22, 0.12, "hierro", eje="x", seg=14, p=B2)
    m.cil((0, C[1], C[2]), 0.06, 0.34, "acero", eje="x", seg=6, p=B2)
    Gn = "gancho"
    m.cil((0, C[1] - 0.2, 5.6), 0.02, 3.2, "acero", seg=5, p=Gn)
    m.caja((0, C[1] - 0.2, 3.85), (0.3, 0.2, 0.4), "amarillo_p", bisel=0.04, p=Gn)
    m.cil((0, C[1] - 0.2, 3.85), 0.13, 0.24, "hierro", eje="y", seg=10, p=Gn)
    pts = [(0, C[1] - 0.2, 3.65)]
    for i in range(1, 9):
        a = math.radians(-90 + 250 * i / 8)
        pts.append((0.22 * math.cos(a) * 1.0 + 0.0, C[1] - 0.2, 3.28 + 0.22 * math.sin(a) + (0.15 if i == 0 else 0)))
    pts[1] = (0, C[1] - 0.2, 3.5)
    m.barrido(pts, [0.05, 0.05, 0.055, 0.06, 0.06, 0.055, 0.045, 0.035, 0.015], "hierro", seg=6, p=Gn)
    # Foco de trabajo y escalerilla
    m.caja((0, B[1] - 0.25, B[2] - 0.35), (0.4, 0.2, 0.2), "oscuro", bisel=0.03, p=B1)
    m.caja((0, B[1] - 0.36, B[2] - 0.4), (0.3, 0.03, 0.12), "neon_blanco")
    for sx in (0.25, 0.55):
        m.cil((sx + 0.05, 0.32, 2.7), 0.025, 3.2, "acero", seg=5, p=G)
    for k in range(9):
        m.cil((0.45, 0.32, 1.3 + 0.34 * k), 0.02, 0.3, "acero", eje="x", seg=4, p=G)


@modelo(55, "industrial", "vehiculo", (6, 2, 2))
def cinta_transportadora(m):
    # Bastidor sobre patas, tambores en los extremos, rodillos 3D, banda con grosor, guardas laterales y motor
    for x in (-2.5, -0.85, 0.85, 2.5):
        for s in (-1, 1):
            m.caja((x, s * 0.75, 0.62), (0.12, 0.12, 1.24), "gris_liso")
            m.caja((x, s * 0.75, 0.04), (0.3, 0.3, 0.08), "oscuro")
        m.caja((x, 0, 0.45), (0.08, 1.5, 0.08), "gris_liso")
        m.barrido([(x, -0.72, 0.15), (x, 0.72, 1.0)], 0.025, "acero", seg=4)
    for s in (-1, 1):
        m.caja((0, s * 0.82, 1.3), (5.7, 0.08, 0.3), "amarillo_p", bisel=0.02)
        m.caja((0, s * 0.82, 1.56), (5.4, 0.05, 0.22), "gris_liso")
        m.caja((0, s * 0.87, 1.3), (5.0, 0.02, 0.1), "rayas")
    # Tambores y rodillos (giran: piezas aparte)
    for x in (-2.8, 2.8):
        m.cil((x, 0, 1.3), 0.24, 1.5, "hierro", eje="y", seg=14, p="rodillos")
        m.cil((x, 0, 1.3), 0.06, 1.8, "acero", eje="y", seg=6, p="rodillos")
    for k in range(10):
        x = -2.25 + 0.5 * k
        m.cil((x, 0, 1.42), 0.09, 1.46, "acero", eje="y", seg=8, p="rodillos")
    for k in range(4):
        m.cil((-1.8 + 1.2 * k, 0, 1.12), 0.07, 1.46, "acero", eje="y", seg=6, p="rodillos")
    # Banda sin fin con grosor: tramo superior, inferior y vueltas
    banda = [(-2.8, 1.56), (2.8, 1.56)] + [(2.8 + 0.26 * math.cos(math.radians(a)), 1.3 + 0.26 * math.sin(math.radians(a)))
                                           for a in range(60, -91, -30)] + [(-2.8, 1.04)] + \
            [(-2.8 + 0.26 * math.cos(math.radians(a)), 1.3 + 0.26 * math.sin(math.radians(a))) for a in range(240, 91, -30)]
    interior = [(2.8 * (x / abs(x)) * 0.985 if abs(x) > 2.9 else x, 1.3 + (z - 1.3) * 0.86) for x, z in banda]
    m.prisma(banda, -0.7, 0.7, "goma", "xz", p="banda")
    # Motor reductor con protección, cuadro eléctrico y seta de emergencia
    m.caja((2.3, 1.1, 1.15), (0.7, 0.5, 0.5), "azul_p", bisel=0.04)
    m.cil((2.3, 1.42, 1.15), 0.2, 0.16, "oscuro", eje="y", seg=10)
    for k in range(5):
        m.caja((2.06 + 0.12 * k, 1.1, 1.42), (0.03, 0.44, 0.05), "oscuro")
    m.caja((2.75, 0.95, 1.3), (0.4, 0.14, 0.5), "rejilla")
    m.caja((-1.5, -0.95, 1.5), (0.5, 0.16, 0.7), "gris_claro", bisel=0.03)
    m.caja((-1.5, -1.04, 1.65), (0.3, 0.02, 0.16), "neon", p="pantalla_neon")
    m.cil((-1.62, -1.05, 1.35), 0.06, 0.06, "rojo_p", eje="y", seg=8)
    m.cil((-1.4, -1.05, 1.35), 0.04, 0.04, "neon_verde", eje="y", seg=8)
    # Carga sobre la cinta: tres minerales y una caja
    R = m.rng
    for i, x in enumerate((-1.9, -0.6, 0.5)):
        m.roca((x, R.uniform(-0.25, 0.25), 1.72), (0.42, 0.38, 0.32), ("piedra", "cobre", "piedra_oscura")[i], semilla=i * 2.2,
               sub=1)
    m.caja((1.7, 0.05, 1.8), (0.6, 0.5, 0.44), "madera_clara", bisel=0.02, rot=(0, 0, 12))


@modelo(56, "industrial", "vehiculo", (6, 4, 4))
def tanque_combustible_industrial(m):
    # Depósito cilíndrico horizontal con fondos bombeados, cunas con patas, boca de hombre, válvulas y pasarela
    m.cil((0, 0, 2.2), 1.7, 3.8, "blanco_liso", eje="x", seg=24)
    for s in (-1, 1):
        m.torno((s * 1.9, 0, 2.2), [(1.7, 0), (1.55, 0.3), (1.1, 0.6), (0.5, 0.76), (0, 0.8)], "blanco_liso", seg=24,
                eje="x", rot=(0, 0, 0 if s > 0 else 180))
        m.tubo((s * 1.9, 0, 2.2), 1.74, 0.12, 0.06, "acero", eje="x", seg=24)
    m.tubo((0, 0, 2.2), 1.73, 0.5, 0.04, "naranja_p", eje="x", seg=24)
    m.tubo((0, 0, 2.2), 1.74, 0.08, 0.05, "acero", eje="x", seg=24)
    # Cunas y patas
    for x in (-1.3, 1.3):
        cuna = [(-1.5, 0.0), (1.5, 0.0), (1.5, 0.3), (1.25, 1.1)] + \
               [(1.72 * math.sin(math.radians(a)), 2.2 - 1.72 * math.cos(math.radians(a))) for a in range(40, -41, -16)] + \
               [(-1.25, 1.1), (-1.5, 0.3)]
        m.prisma(cuna, x - 0.12, x + 0.12, "hierro", "yz")
        m.caja((x, 0, 0.06), (0.6, 3.3, 0.12), "oscuro")
        for s in (-1, 1):
            m.cil((x, s * 1.5, 0.15), 0.06, 0.08, "acero", seg=6)
    # Boca de hombre con pernos, respiradero y nivel luminoso
    m.cil((0.4, 0, 3.95), 0.5, 0.3, "gris_liso", seg=16)
    m.cil((0.4, 0, 4.12), 0.58, 0.08, "acero", seg=16)
    for k in range(8):
        a = math.radians(45 * k)
        m.cil((0.4 + 0.5 * math.cos(a), 0.5 * math.sin(a), 4.17), 0.04, 0.04, "hierro", seg=6)
    m.barrido([(0.1, 0, 4.16), (0.4, 0, 4.3), (0.7, 0, 4.16)], 0.03, "acero", seg=5)
    m.barrido([(-1.2, 0, 3.85), (-1.2, 0, 4.25), (-1.2, -0.25, 4.3), (-1.2, -0.3, 4.15)], 0.07, "acero", seg=6)
    m.caja((2.0, -1.2, 2.2), (0.12, 0.1, 1.8), "oscuro")
    m.caja((2.0, -1.26, 2.0), (0.06, 0.03, 1.2), "neon")
    for z in (1.4, 3.0):
        m.barrido([(2.0, -1.2, z), (2.0, -0.9, z)], 0.03, "acero", seg=4)
    # Tubería de descarga con válvula de volante y brida
    m.barrido([(-0.6, -1.3, 1.0), (-0.6, -1.9, 0.9), (-0.6, -1.95, 0.5), (-1.6, -1.95, 0.5)], 0.13, "acero", seg=8)
    m.cil((-0.6, -1.95, 0.72), 0.2, 0.14, "rojo_p", seg=8)
    m.cil((-0.6, -1.95, 1.1), 0.03, 0.5, "acero", seg=5)
    m.tubo((-0.6, -1.95, 1.36), 0.24, 0.05, 0.05, "rojo_p", seg=12)
    for a in (0, 90):
        m.caja((-0.6, -1.95, 1.36), (0.44, 0.04, 0.03), "rojo_p", rot=(0, 0, a))
    m.cil((-1.65, -1.95, 0.5), 0.2, 0.08, "hierro", eje="x", seg=10)
    # Pasarela superior con barandilla y escalera de gato
    m.caja((-0.6, 0.55, 3.98), (2.2, 0.7, 0.06), "rejilla")
    m.barandilla((-1.7, 0.9, 4.0), (0.5, 0.9, 4.0), 0.0 + 0.0 or 0.9, postes=4, travesanos=1)
    for y in (2.0, 2.4):
        m.barrido([(-1.5, 0.9, 4.0), (-1.5, y - 0.3, 3.9), (-1.5, y - 0.1, 0.1)], 0.03, "acero", seg=5) if y == 2.0 else \
            m.barrido([(-1.1, 0.9, 4.0), (-1.1, y - 0.7, 3.9), (-1.1, y - 0.5, 0.1)], 0.03, "acero", seg=5)
    for k in range(10):
        m.cil((-1.3, 1.9 - 0.0 * k, 0.4 + 0.36 * k), 0.022, 0.4, "acero", eje="x", seg=4)
    # Rótulo de peligro en relieve
    m.prisma([(-0.4, -0.3), (0.4, -0.3), (0, 0.4)], -0.03, 0.03, "amarillo_p", "xz", c=(1.0, -1.72, 2.25), rot=(-8, 0, 0))
    m.prisma([(-0.05, -0.15), (0.05, -0.15), (0.07, 0.18), (-0.07, 0.18)], -0.045, 0.045, "negro", "xz",
             c=(1.0, -1.74, 2.25), rot=(-8, 0, 0))


@modelo(57, "industrial", "edificio_mediano", (4, 4, 10))
def silo_almacen(m):
    # Silo vertical: virolas con nervios, tolva inferior sobre cuatro patas, techo cónico, escalera con quitamiedos
    m.cil((0, 0, 0.1), 2.0, 0.2, "hormigon", seg=20)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, y = 1.45 * math.cos(a), 1.45 * math.sin(a)
        m.caja((x, y, 1.5), (0.26, 0.26, 2.7), "hierro", rot=(0, 0, 45), bisel=0.03)
        m.caja((x, y, 0.26), (0.5, 0.5, 0.12), "oscuro", rot=(0, 0, 45))
        b = math.radians(45 + 90 * (k + 1))
        m.barrido([(x, y, 0.5), (1.45 * math.cos(b), 1.45 * math.sin(b), 2.4)], 0.05, "hierro", seg=4)
    m.torno((0, 0, 1.0), [(0.3, 0), (0.36, 0.0), (1.8, 1.9), (1.8, 2.0), (0.0, 2.0)], "gris_liso", seg=20)
    m.cil((0, 0, 0.85), 0.36, 0.34, "hierro", seg=12)
    m.caja((0.45, 0, 0.9), (0.5, 0.12, 0.12), "rojo_p")
    m.torno((0, 0, 2.9), [(1.8, 0), (1.8, 5.2)], "chapa", seg=20)
    for z in (2.95, 4.25, 5.55, 6.85, 8.05):
        m.tubo((0, 0, z), 1.85, 0.14, 0.07, "gris_liso", seg=20)
    m.torno((0, 0, 8.1), [(1.95, 0), (1.95, 0.1), (0.4, 1.3), (0.4, 1.5), (0, 1.5)], "gris", seg=20)
    m.cil((0, 0, 9.72), 0.5, 0.14, "acero", seg=12)
    m.esfera((0, 0, 9.86), 0.1, "neon_rojo", seg=8, anillos=5)
    m.tubo((0, 0, 8.16), 1.97, 0.06, 0.03, "neon", seg=20)
    # Banda de identificación con número en relieve
    m.tubo((0, 0, 6.2), 1.83, 0.9, 0.03, "acento", seg=20)
    m.texto("S-01", (0, -1.86, 6.2), 0.5, 0.05, "blanco_liso")
    # Escalera de gato con aros de seguridad y plataforma superior
    for s in (-1, 1):
        m.cil((1.95 + 0.0, s * 0.25, 4.6), 0.035, 8.8, "acero", seg=5)
    for k in range(22):
        m.cil((1.95, 0, 0.5 + 0.4 * k), 0.022, 0.5, "acero", eje="y", seg=4)
    for k in range(6):
        z = 3.2 + 1.0 * k
        pts = [(1.95, -0.25, z)] + [(2.3 + 0.38 * math.cos(math.radians(a)) * 1.0, 0.36 * math.sin(math.radians(a)) * -1.0, z)
                                    for a in (120, 60, 0, -60, -120)] + [(1.95, 0.25, z)]
        m.barrido(pts, 0.02, "amarillo_p", seg=4)
    for a in (-55, 0, 55):
        m.barrido([(2.3 + 0.38 * math.cos(math.radians(a)), 0.36 * math.sin(math.radians(a)), 3.2),
                   (2.3 + 0.38 * math.cos(math.radians(a)), 0.36 * math.sin(math.radians(a)), 8.2)], 0.015, "amarillo_p",
                  seg=4)
    for z in (2.0, 5.0, 8.0):
        m.barrido([(1.8, 0, z), (1.95, 0, z)], 0.03, "acero", seg=4)
    # Tubo de llenado neumático que sube por detrás hasta el techo
    m.barrido([(-0.4, 2.3, 0.2), (-0.4, 2.1, 1.0), (-0.4, 1.95, 8.6), (-0.3, 1.2, 9.3), (-0.15, 0.5, 9.5)], 0.13, "acero",
              seg=8)
    for z in (2.5, 5.0, 7.5):
        m.tubo((-0.4, 1.97, z), 0.17, 0.1, 0.04, "hierro", seg=8)


@modelo(58, "industrial", "prop", (4, 1, 1))
def tuberia_modular(m):
    # Tubo principal con bridas atornilladas, codo de bajada, derivación en T, válvula de volante y soportes
    m.cil((0, 0, 0.6), 0.22, 4.0, "acero", eje="x", seg=14)
    for x in (-1.97, 1.97, -0.6, 0.9):
        m.cil((x, 0, 0.6), 0.32, 0.06, "hierro", eje="x", seg=14)
        for k in range(6):
            a = math.radians(60 * k)
            m.cil((x, 0.27 * math.cos(a), 0.6 + 0.27 * math.sin(a)), 0.03, 0.1, "cromo", eje="x", seg=5)
    m.tubo((-1.3, 0, 0.6), 0.235, 0.3, 0.02, "amarillo_p", eje="x", seg=14)
    m.prisma([(-0.12, -0.06), (0.06, -0.06), (0.06, -0.12), (0.2, 0), (0.06, 0.12), (0.06, 0.06), (-0.12, 0.06)], -0.01,
             0.01, "negro", "xz", c=(-1.3, -0.245, 0.6))
    # Derivación en T hacia el frente con codo de 90° hacia abajo
    codo = [(0.15, -0.2, 0.6), (0.15, -0.32, 0.6), (0.15, -0.4, 0.56), (0.15, -0.44, 0.48), (0.15, -0.45, 0.38),
            (0.15, -0.45, 0.02)]
    m.barrido(codo, 0.13, "acero", seg=10)
    m.cil((0.15, -0.26, 0.6), 0.2, 0.05, "hierro", eje="y", seg=10)
    m.cil((0.15, -0.45, 0.05), 0.2, 0.06, "hierro", seg=10)
    # Válvula de compuerta con volante
    m.caja((1.45, 0, 0.6), (0.34, 0.5, 0.5), "rojo_p", bisel=0.05)
    m.cil((1.45, 0, 0.95), 0.07, 0.3, "acero", seg=6)
    m.tubo((1.45, 0, 1.0), 0.26, 0.05, 0.045, "rojo_p", seg=14, p="volante")
    for a in (0, 60, 120):
        m.caja((1.45, 0, 1.0), (0.48, 0.035, 0.03), "rojo_p", rot=(0, 0, a), p="volante")
    m.cil((1.45, 0, 1.03), 0.05, 0.05, "cromo", seg=6, p="volante")
    # Manómetro con esfera luminosa
    m.cil((-0.2, 0, 0.88), 0.03, 0.2, "cobre", seg=5)
    m.cil((-0.2, -0.02, 0.98), 0.11, 0.06, "cromo", eje="y", seg=12)
    m.cil((-0.2, -0.055, 0.98), 0.09, 0.015, "neon", eje="y", seg=12)
    m.caja((-0.17, -0.068, 1.0), (0.012, 0.01, 0.08), "negro", rot=(0, 30, 0))
    # Soportes en U al suelo
    for x in (-1.6, 0.55):
        m.caja((x, 0, 0.04), (0.2, 0.7, 0.08), "oscuro")
        for s in (-1, 1):
            m.caja((x, s * 0.26, 0.24), (0.1, 0.06, 0.4), "gris_liso")
        m.prisma(arco_pts(0.27, 0.23, 0, 180, 6, 0, 0.6, 1.0, 1.0), x - 0.05, x + 0.05, "gris_liso", "yz")
    # Línea auxiliar fina de cobre
    m.barrido([(-2.0, 0.3, 0.35), (-0.9, 0.3, 0.35), (-0.8, 0.3, 0.45), (0.6, 0.3, 0.45), (0.7, 0.3, 0.35), (2.0, 0.3, 0.35)],
              0.045, "cobre", seg=6)


@modelo(59, "industrial", "edificio_mediano", (2, 2, 14))
def chimenea_industrial(m):
    # Fuste metálico por virolas que se estrecha, zócalo, escalerilla con aros, plataforma, vientos y balizas
    m.caja((0, 0, 0.2), (2.0, 2.0, 0.4), "hormigon", bisel=0.05)
    m.torno((0, 0, 0.4), [(0.92, 0), (0.92, 0.5), (0.8, 0.9), (0.62, 6.0), (0.5, 12.6), (0.56, 12.8), (0.56, 13.5),
                          (0.44, 13.5), (0.44, 12.9), (0, 12.9)], "gris", seg=16)
    def r(z):
        return 0.8 - (z - 1.3) * 0.0353 if z < 6.4 else 0.62 - (z - 6.4) * 0.0182
    for z in (2.6, 4.6, 6.6, 8.6, 10.6):
        m.tubo((0, 0, z), r(z) + 0.05, 0.14, 0.05, "acero", seg=16)
    for z in (11.5, 12.3):
        m.tubo((0, 0, z), r(z) + 0.035, 0.35, 0.03, "rojo_p", seg=16)
    m.cil((0, 0, 13.82), 0.42, 0.05, "negro", seg=12)
    m.anclaje("humo", (0, 0, 14.1))
    # Portezuela de registro y cuadro de control en la base
    m.caja((0, -0.9, 0.9), (0.6, 0.12, 0.7), "oscuro", bisel=0.03)
    m.cil((0.2, -0.97, 0.9), 0.04, 0.04, "acero", eje="y", seg=6)
    m.caja((0.75, -0.75, 1.0), (0.3, 0.14, 0.4), "gris_claro", rot=(0, 0, 40))
    m.caja((0.8, -0.8, 1.05), (0.16, 0.03, 0.1), "neon", rot=(0, 0, 40))
    # Escalerilla lateral con aros quitamiedos
    def xe(z):
        return r(max(z, 1.3)) + 0.16
    for s in (-1, 1):
        m.barrido([(xe(0.6), s * 0.2, 0.6), (xe(6.4), s * 0.2, 6.4), (xe(12.2), s * 0.2, 12.2)], 0.03, "acero", seg=5)
    for k in range(30):
        z = 0.75 + 0.39 * k
        m.cil((xe(z), 0, z), 0.02, 0.4, "acero", eje="y", seg=4)
    for k in range(8):
        z = 3.0 + 1.2 * k
        x0 = xe(z)
        m.barrido([(x0, -0.2, z)] + [(x0 + 0.3 + 0.32 * math.cos(math.radians(a)), -0.32 * math.sin(math.radians(a)), z)
                                     for a in (120, 60, 0, -60, -120)] + [(x0, 0.2, z)], 0.018, "amarillo_p", seg=4)
    for z in (2.0, 5.0, 8.0, 11.0):
        m.barrido([(r(z), 0, z), (xe(z), 0, z)], 0.025, "acero", seg=4)
    # Plataforma anular de mantenimiento con barandilla
    zp = 12.2
    m.tubo((0, 0, zp), 1.1, 0.06, 0.55, "rejilla", seg=16)
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        m.cil((1.05 * math.cos(a), 1.05 * math.sin(a), zp + 0.45), 0.025, 0.9, "acero", seg=5)
        m.barrido([(0.56 * math.cos(a), 0.56 * math.sin(a), zp - 0.45), (1.05 * math.cos(a), 1.05 * math.sin(a), zp - 0.03)],
                  0.025, "acero", seg=4)
    m.tubo((0, 0, zp + 0.9), 1.08, 0.05, 0.05, "acero", seg=16)
    m.tubo((0, 0, zp + 0.45), 1.07, 0.03, 0.03, "acero", seg=16)
    # Balizas rojas y tres vientos de acero
    for k in range(3):
        a = math.radians(120 * k + 60)
        m.esfera((0.6 * math.cos(a), 0.6 * math.sin(a), 13.6), 0.07, "neon_rojo", seg=6, anillos=4)
        m.barrido([(r(9.0) * math.cos(a), r(9.0) * math.sin(a), 9.0), (0.95 * math.cos(a), 0.95 * math.sin(a), 0.42)], 0.015,
                  "acero", seg=4)
        m.caja((0.92 * math.cos(a), 0.92 * math.sin(a), 0.46), (0.14, 0.14, 0.12), "hierro")


@modelo(60, "industrial", "vehiculo", (4, 4, 0.5))
def plataforma_elevacion(m):
    # Bastidor de suelo, cuatro pistones hidráulicos telescópicos y tablero antideslizante (pieza aparte, sube)
    m.caja((0, 0, 0.04), (4.0, 4.0, 0.08), "oscuro", bisel=0.02)
    for s in (-1, 1):
        m.caja((s * 1.92, 0, 0.1), (0.14, 3.9, 0.06), "rayas")
        m.caja((0, s * 1.92, 0.1), (3.6, 0.14, 0.06), "rayas")
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 1.35, sy * 1.35
            m.cil((x, y, 0.16), 0.3, 0.16, "hierro", seg=14)
            m.cil((x, y, 0.27), 0.22, 0.14, "gris_liso", seg=12)
            m.cil((x, y, 0.33), 0.15, 0.1, "cromo", seg=10, p="pistones")
            m.tubo((x, y, 0.24), 0.31, 0.03, 0.03, "acero", seg=14)
            for k in range(4):
                a = math.radians(90 * k + 45)
                m.cil((x + 0.38 * math.cos(a), y + 0.38 * math.sin(a), 0.1), 0.04, 0.05, "acero", seg=6)
    # Central hidráulica y latiguillos
    m.caja((0, 0, 0.2), (0.9, 0.9, 0.24), "azul_p", bisel=0.04)
    m.cil((0, 0, 0.33), 0.2, 0.04, "oscuro", seg=10)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.barrido([(sx * 0.42, sy * 0.3, 0.14), (sx * 0.8, sy * 0.9, 0.11), (sx * 1.12, sy * 1.2, 0.13)], 0.03, "goma",
                      seg=5)
    P = "tablero"
    m.caja((0, 0, 0.43), (3.8, 3.8, 0.12), "gris", bisel=0.03, p=P)
    m.caja((0, 0, 0.493), (3.4, 3.4, 0.014), "rejilla", p=P)
    for s in (-1, 1):
        m.caja((s * 1.8, 0, 0.495), (0.14, 3.6, 0.012), "amarillo_p", p=P)
        m.caja((0, s * 1.8, 0.495), (3.46, 0.14, 0.012), "amarillo_p", p=P)
        m.caja((s * 1.905, 0, 0.43), (0.02, 3.0, 0.05), "neon")
        m.caja((0, s * 1.905, 0.43), (3.0, 0.02, 0.05), "neon")
