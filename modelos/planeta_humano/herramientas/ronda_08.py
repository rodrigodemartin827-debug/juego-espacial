"""Ronda 8 · Zona del hangar (modelos 71-80)."""

import math

from geometria import arco_pts
from registro import modelo


@modelo(71, "hangar", "prop", (3, 1, 1))
def cable_combustible(m):
    # Manguera de repostaje enrollada en su soporte, con boquilla metálica de gatillo y acople rápido
    m.caja((-0.4, 0, 0.04), (1.6, 0.9, 0.08), "oscuro", bisel=0.02)
    m.cil((-0.4, 0, 0.5), 0.16, 0.7, "gris_liso", eje="y", seg=10)
    for s in (-1, 1):
        m.cil((-0.4, s * 0.36, 0.5), 0.5, 0.04, "amarillo_p", eje="y", seg=18)
        m.prisma([(-0.35, 0.08), (0.35, 0.08), (0.08, 0.5), (-0.08, 0.5)], -0.03, 0.03, "gris_liso", "xz",
                 c=(-0.4, s * 0.42, 0))
    # Espiras de manguera (dos capas) alrededor del tambor
    pts, rs = [], []
    n = 54
    for i in range(n):
        t = i / (n - 1)
        vuelta = t * 4.5
        a = 2 * math.pi * vuelta
        r = 0.26 if vuelta < 2.4 else 0.4
        y = -0.26 + 0.52 * ((vuelta % 2.4) / 2.4 if vuelta < 2.4 else (vuelta - 2.4) / 2.1)
        pts.append((-0.4 + r * math.cos(a), y, 0.5 + r * math.sin(a)))
    m.barrido(pts, 0.07, "goma", seg=6)
    # Tramo suelto por el suelo hasta la boquilla
    fin = pts[-1]
    suelta = [fin, (0.15, fin[1] + 0.02, 0.2), (0.6, 0.2, 0.09), (1.0, 0.3, 0.08), (1.35, 0.15, 0.08), (1.6, -0.05, 0.1)]
    m.barrido(suelta, 0.07, "goma", seg=6)
    m.barrido([(0.6, 0.2, 0.09), (0.62, 0.2, 0.09)], 0.09, "naranja_p", seg=6)
    # Boquilla: cuerpo, cañón, gatillo con guarda y anilla luminosa
    m.cil((1.72, -0.1, 0.12), 0.1, 0.3, "acero", eje="x", seg=10, rot=(0, 0, -22))
    m.cil((1.98, -0.2, 0.12), 0.06, 0.4, "cromo", eje="x", seg=8, rot=(0, 0, -22))
    m.cil((2.17, -0.28, 0.12), 0.08, 0.06, "acero", eje="x", seg=8, rot=(0, 0, -22))
    m.tubo((1.84, -0.15, 0.12), 0.11, 0.05, 0.03, "neon", eje="x", seg=10, rot=(0, 0, -22))
    m.barrido([(1.62, -0.06, 0.2), (1.7, -0.1, 0.36), (1.88, -0.17, 0.36), (1.9, -0.18, 0.2)], 0.022, "acero", seg=5)
    m.caja((1.76, -0.12, 0.26), (0.16, 0.04, 0.05), "rojo_p", rot=(0, 20, -22))
    # Acople de la toma en el soporte, con válvula y testigo
    m.caja((-1.1, 0, 0.3), (0.3, 0.5, 0.44), "gris_claro", bisel=0.03)
    m.cil((-1.1, -0.27, 0.34), 0.09, 0.08, "cobre", eje="y", seg=8)
    m.caja((-1.1, -0.255, 0.46), (0.16, 0.02, 0.06), "neon")
    m.barrido([(-1.0, 0, 0.5), (-0.8, 0, 0.62), (-0.55, 0, 0.6)], 0.05, "goma", seg=5)
    m.caja((-0.4, -0.385, 0.5), (0.3, 0.02, 0.12), "rayas")


@modelo(72, "hangar", "prop", (0.5, 0.5, 0.5))
def luz_baliza_hangar(m):
    # Baliza de suelo: base atornillada, aro, jaula protectora y dos ópticas (cyan y naranja) para el parpadeo
    m.cil((0, 0, 0.03), 0.25, 0.06, "oscuro", seg=14)
    for k in range(4):
        a = math.radians(90 * k + 45)
        m.cil((0.2 * math.cos(a), 0.2 * math.sin(a), 0.065), 0.025, 0.02, "acero", seg=6)
    m.torno((0, 0, 0.06), [(0.2, 0), (0.18, 0.08), (0.14, 0.1), (0, 0.1)], "amarillo_p", seg=14)
    m.tubo((0, 0, 0.16), 0.15, 0.04, 0.03, "acero", seg=14)
    m.torno((0, 0, 0.16), [(0.12, 0), (0.12, 0.12), (0.09, 0.2), (0.0, 0.24)], "neon", seg=12)
    m.tubo((0, 0, 0.2), 0.125, 0.035, 0.012, "neon_naranja", seg=12)
    for k in range(4):
        a = math.radians(90 * k)
        pts = [(0.15 * math.cos(a), 0.15 * math.sin(a), 0.17), (0.155 * math.cos(a), 0.155 * math.sin(a), 0.32),
               (0.1 * math.cos(a), 0.1 * math.sin(a), 0.42), (0, 0, 0.46)]
        m.barrido(pts, 0.012, "acero", seg=4)
    m.tubo((0, 0, 0.32), 0.158, 0.02, 0.012, "acero", seg=14)
    m.cil((0, 0, 0.465), 0.035, 0.03, "acero", seg=8)
    m.caja((0, -0.2, 0.1), (0.1, 0.03, 0.05), "oscuro")


@modelo(73, "hangar", "vehiculo", (3, 1, 4))
def escalera_nave(m):
    # Escalera rodante de embarque: chasis con cuatro ruedas y frenos, nueve peldaños, plataforma y pasamanos
    for s in (-1, 1):
        m.caja((0.1, s * 0.45, 0.3), (2.7, 0.08, 0.1), "amarillo_p")
        for x in (-1.1, 1.3):
            m.caja((x, s * 0.45, 0.2), (0.1, 0.1, 0.2), "acero")
            m.cil((x, s * 0.45, 0.13), 0.13, 0.08, "goma", eje="y", seg=12)
            m.cil((x, s * 0.45, 0.13), 0.05, 0.1, "acero", eje="y", seg=6)
        m.caja((1.3, s * 0.45, 0.3), (0.2, 0.14, 0.06), "rojo_p")
    for x in (-1.1, 1.3):
        m.caja((x, 0, 0.3), (0.08, 0.9, 0.08), "amarillo_p")
    n = 9
    x0, x1, z0, z1 = -1.25, 0.75, 0.35, 3.05
    dx, dz = (x1 - x0) / n, (z1 - z0) / n
    for s in (-1, 1):
        m.prisma([(x0, z0 - 0.05), (x1, z1 - 0.05), (x1, z1 - 0.3), (x0, z0 - 0.3)], s * 0.45 - 0.03, s * 0.45 + 0.03,
                 "gris_liso", "xz")
    for i in range(n):
        m.bloque((x0 + dx * i, -0.42, z0 + dz * (i + 1) - 0.06), (x0 + dx * (i + 1) + 0.03, 0.42, z0 + dz * (i + 1)),
                 "rejilla")
    # Plataforma superior con rodapié
    m.bloque((0.75, -0.46, 2.97), (1.45, 0.46, 3.05), "rejilla")
    m.bloque((0.75, -0.48, 2.85), (1.45, 0.48, 2.97), "gris_liso")
    m.caja((1.46, 0, 3.0), (0.04, 0.96, 0.14), "rayas")
    for s in (-1, 1):
        for x in (0.8, 1.42):
            m.cil((x, s * 0.45, 1.6), 0.04, 2.6, "acero", seg=6)
        m.barrido([(0.8, s * 0.45, 0.4), (1.42, s * 0.45, 1.7)], 0.025, "acero", seg=4)
        m.barrido([(1.42, s * 0.45, 0.4), (0.8, s * 0.45, 1.7)], 0.025, "acero", seg=4)
        # Pasamanos de la rampa y barandilla de la plataforma
        m.barrido([(x0, s * 0.45, z0 + 1.0), (x1, s * 0.45, z1 + 1.0), (1.44, s * 0.45, z1 + 1.0)], 0.04, "amarillo_p",
                  seg=6)
        m.barrido([(x0, s * 0.45, z0 + 0.55), (x1, s * 0.45, z1 + 0.55), (1.44, s * 0.45, z1 + 0.55)], 0.025, "acero", seg=5)
        for i in (0, 3, 6, 9):
            m.cil((x0 + dx * i, s * 0.45, z0 + dz * i + 0.5), 0.03, 1.0, "acero", seg=5)
        m.cil((1.44, s * 0.45, z1 + 0.5), 0.03, 1.0, "acero", seg=5)
        m.caja((x1 + 0.3, s * 0.47, z1 + 0.12), (0.5, 0.02, 0.06), "neon")
    # Tirador de arrastre delantero
    m.barrido([(-1.2, -0.2, 0.3), (-1.5, -0.2, 0.5), (-1.5, 0.2, 0.5), (-1.2, 0.2, 0.3)], 0.03, "acero", seg=5)


@modelo(74, "hangar", "prop", (2, 1, 3))
def caja_herramientas_hangar(m):
    # Carro de herramientas: armario con cajones (piezas aparte), cofre superior con tapa abierta, llaves 3D y ruedas
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 0.8, sy * 0.36
            m.caja((x, y, 0.27), (0.1, 0.1, 0.12), "acero")
            m.cil((x, y, 0.13), 0.13, 0.08, "goma", eje="x", seg=12)
            m.cil((x, y, 0.13), 0.05, 0.1, "acero", eje="x", seg=6)
    m.caja((0, 0, 1.0), (1.9, 0.95, 1.4), "rojo_p", bisel=0.04)
    m.caja((0, 0, 0.36), (1.94, 0.99, 0.1), "oscuro")
    alturas = (0.55, 0.85, 1.12, 1.34, 1.54)
    altos = (0.3, 0.26, 0.22, 0.16, 0.16)
    for i, (z, h) in enumerate(zip(alturas, altos)):
        dy = -0.22 if i == 2 else 0.0                                                 # un cajón entreabierto
        m.caja((0, -0.47 + dy, z), (1.78, 0.06 + abs(dy) * 2, h - 0.03), "gris_claro", p=f"cajon_{i + 1}")
        m.caja((0, -0.52 + dy, z + h / 2 - 0.06), (1.5, 0.05, 0.04), "acero", p=f"cajon_{i + 1}")
    # Dentro del cajón abierto: vasos de llave ordenados
    for k in range(8):
        m.cil((-0.7 + 0.2 * k, -0.6, 1.2), 0.035 + 0.005 * (k % 4), 0.08, "cromo", seg=8, p="cajon_3")
    # Sobre de trabajo y cofre superior con tapa levantada
    m.caja((0, 0, 1.73), (1.96, 1.0, 0.06), "goma")
    m.caja((0, 0.12, 2.1), (1.8, 0.7, 0.66), "rojo_p", bisel=0.04)
    for i in range(2):
        m.caja((0, -0.24, 1.95 + 0.26 * i), (1.66, 0.04, 0.2), "gris_claro", p=f"cajon_cofre_{i + 1}")
        m.caja((0, -0.27, 2.0 + 0.26 * i), (1.3, 0.04, 0.035), "acero", p=f"cajon_cofre_{i + 1}")
    m.caja((0, 0.52, 2.72), (1.8, 0.06, 0.66), "rojo_p", rot=(-12, 0, 0), bisel=0.02, p="tapa")
    for sx in (-0.86, 0.86):
        m.barrido([(sx, 0.2, 2.44), (sx, 0.5, 2.8)], 0.015, "cromo", seg=4)
    m.caja((0, 0.1, 2.44), (1.7, 0.6, 0.03), "goma")
    # Llaves inglesas y fijas 3D en la bandeja superior, destornilladores y martillo
    for i, (x, l) in enumerate(((-0.65, 0.5), (-0.45, 0.44), (-0.25, 0.38), (-0.05, 0.32))):
        m.caja((x, 0.1, 2.47), (0.05, l, 0.025), "cromo")
        m.tubo((x, 0.1 + l / 2 + 0.04, 2.47), 0.07, 0.025, 0.03, "cromo", seg=8)
        m.prisma([(-0.07, 0), (-0.03, 0.09), (-0.03, 0.02), (0.03, 0.02), (0.03, 0.09), (0.07, 0), (0.04, -0.05), (-0.04, -0.05)],
                 2.4575, 2.4825, "cromo", "xy", c=(x, 0.1 - l / 2 - 0.02, 0), rot=(0, 0, 180))
    for i, col in enumerate(("amarillo_p", "azul_p", "naranja_p")):
        m.cil((0.3 + 0.15 * i, 0.22, 2.48), 0.035, 0.2, col, eje="y", seg=6)
        m.cil((0.3 + 0.15 * i, 0.0, 2.48), 0.015, 0.26, "cromo", eje="y", seg=5)
    m.cil((0.75, 0.05, 2.48), 0.025, 0.5, "madera", eje="y", seg=6)
    m.caja((0.75, 0.32, 2.49), (0.22, 0.1, 0.1), "acero", bisel=0.015)
    # Asa lateral, bandeja lateral con bote de espray y emblema luminoso
    m.barrido([(0.96, -0.3, 1.5), (1.1, -0.3, 1.55), (1.1, 0.3, 1.55), (0.96, 0.3, 1.5)], 0.03, "acero", seg=6)
    m.caja((-1.1, 0, 1.2), (0.26, 0.7, 0.04), "oscuro")
    m.caja((-1.22, 0, 1.3), (0.03, 0.7, 0.2), "oscuro")
    m.torno((-1.1, 0.1, 1.22), [(0.07, 0), (0.07, 0.26), (0.03, 0.3), (0.03, 0.36), (0, 0.36)], "azul_p", seg=8)
    m.torno((-1.1, -0.15, 1.22), [(0.08, 0), (0.08, 0.2), (0.04, 0.26), (0, 0.26)], "amarillo_p", seg=8)
    m.caja((0.6, -0.48, 2.36), (0.4, 0.02, 0.07), "neon")


@modelo(75, "hangar", "prop", (3, 0.3, 2))
def pantalla_estado_nave(m):
    # Pantalla de pared: soporte con bisagra y el panel entero de neón, con el esquema de la nave en relieve
    m.caja((0, 0.11, 1.0), (1.2, 0.08, 0.8), "oscuro", bisel=0.02)
    for s in (-1, 1):
        m.cil((s * 0.4, 0.06, 1.0), 0.05, 0.1, "acero", eje="y", seg=8)
    P = "panel_neon"
    m.caja((0, -0.02, 1.0), (2.84, 0.05, 1.84), "neon", p=P)
    m.marco((0, -0.03, 1.0), 3.0, 2.0, 0.08, 0.12, "neon_blanco", p="marco_neon")
    y = -0.06
    T = "esquema_neon"
    # Nave vista en planta: fuselaje, alas, motores
    m.prisma([(-0.9, 0.0), (-0.5, 0.16), (0.5, 0.2), (0.75, 0.1), (0.75, -0.1), (0.5, -0.2), (-0.5, -0.16)], y - 0.02, y,
             "neon_blanco", "xz", c=(-0.6, 0, 1.15), p=T)
    for s in (-1, 1):
        m.prisma([(0.2, s * 0.2), (-0.1, s * 0.2), (0.3, s * 0.62), (0.5, s * 0.62)], y - 0.02, y, "neon_blanco", "xz",
                 c=(-0.6, 0, 1.15), p=T)
        m.caja((0.22, y - 0.01, 1.15 + s * 0.14), (0.16, 0.02, 0.1), "neon_naranja")
    # Barras de estado (casco, escudo, motor, armas) y cifras
    for k, (larg, mat) in enumerate(((0.9, "neon_verde"), (0.7, "neon_verde"), (0.45, "neon_amarillo"), (0.25, "neon_rojo"))):
        z = 1.62 - 0.22 * k
        m.caja((0.95, y - 0.005, z), (0.94, 0.012, 0.1), "neon_blanco", p="marco_neon")
        m.caja((0.52 + larg / 2, y - 0.015, z), (larg, 0.02, 0.07), mat)
    m.texto("ESTADO", (-0.75, y - 0.01, 1.72), 0.15, 0.02, "neon_blanco", p=T, res=1)
    m.texto("72%", (0.95, y - 0.01, 0.55), 0.26, 0.02, "neon_blanco", p=T, res=1)
    for k in range(6):
        m.caja((-1.2 + 0.2 * k, y - 0.01, 0.4 + 0.05 * (k % 3)), (0.12, 0.02, 0.14 + 0.1 * (k % 3)), "neon_blanco", p=T)
    m.tubo((0.0, y - 0.01, 0.5), 0.2, 0.02, 0.04, "neon_blanco", eje="y", seg=14, p=T)
    m.caja((0.07, y - 0.012, 0.56), (0.03, 0.02, 0.2), "neon_naranja", rot=(0, 35, 0))


@modelo(76, "hangar", "prop", (0.5, 0.5, 1.5))
def extintor(m):
    # Soporte de pared con abrazadera, cilindro rojo, cabezal con palancas, manómetro y manguera con boquilla
    m.caja((0, 0.22, 0.75), (0.4, 0.04, 1.4), "gris_liso", bisel=0.01)
    m.caja((0, 0.19, 0.08), (0.3, 0.1, 0.04), "gris_liso")
    m.torno((0, 0, 0.1), [(0.15, 0), (0.17, 0.03), (0.17, 0.8), (0.14, 0.92), (0.07, 1.0), (0.06, 1.06), (0, 1.06)],
            "rojo_p", seg=14)
    m.cil((0, 0, 0.1), 0.16, 0.05, "oscuro", seg=14)
    m.tubo((0, 0.02, 0.62), 0.185, 0.08, 0.02, "acero", seg=14)
    m.caja((0, 0.19, 0.62), (0.1, 0.06, 0.08), "acero")
    m.tubo((0, 0, 0.45), 0.172, 0.22, 0.005, "plastico", seg=14)
    m.caja((0, -0.172, 0.45), (0.14, 0.01, 0.1), "neon")
    # Cabezal: válvula, palancas, pasador con anilla y manómetro
    m.cil((0, 0, 1.2), 0.07, 0.1, "acero", seg=8)
    m.caja((0, -0.08, 1.3), (0.06, 0.34, 0.03), "plastico_negro", rot=(12, 0, 0))
    m.caja((0, -0.08, 1.2), (0.06, 0.3, 0.03), "plastico_negro", rot=(-8, 0, 0))
    m.tubo((0.07, 0, 1.24), 0.04, 0.012, 0.012, "amarillo_p", eje="x", seg=8)
    m.cil((-0.09, 0, 1.2), 0.045, 0.03, "cromo", eje="x", seg=8)
    m.cil((-0.108, 0, 1.2), 0.035, 0.01, "neon_verde", eje="x", seg=8)
    # Manguera que baja y se sujeta al cuerpo, con boquilla cónica
    m.barrido([(0, 0.07, 1.2), (0.12, 0.14, 1.15), (0.2, 0.1, 0.95), (0.2, 0.05, 0.6), (0.2, 0.02, 0.42)], 0.025,
              "goma", seg=6)
    m.torno((0.2, 0.02, 0.24), [(0.05, 0), (0.035, 0.12), (0.03, 0.2), (0, 0.2)], "plastico_negro", seg=8)
    m.caja((0.19, 0.02, 0.52), (0.04, 0.08, 0.04), "acero")


@modelo(77, "hangar", "prop", (3, 0.3, 2))
def barrera_seguridad(m):
    # Dos postes con base lastrada y cabezal retráctil; la cinta extensible va como pieza aparte
    for s in (-1, 1):
        x = s * 1.35
        m.torno((x, 0, 0), [(0.15, 0), (0.15, 0.04), (0.1, 0.1), (0.04, 0.14), (0, 0.14)], "oscuro", seg=14)
        m.tubo((x, 0, 0.04), 0.15, 0.03, 0.02, "goma", seg=14)
        m.cil((x, 0, 0.95), 0.04, 1.65, "cromo", seg=10)
        m.tubo((x, 0, 0.6), 0.045, 0.3, 0.008, "rayas", seg=10)
        m.cil((x, 0, 1.82), 0.075, 0.2, "oscuro", seg=12)
        m.torno((x, 0, 1.92), [(0.075, 0), (0.06, 0.04), (0, 0.06)], "oscuro", seg=12)
        m.cil((x, 0, 1.985), 0.035, 0.02, "neon", seg=8)
        m.caja((x - s * 0.08, 0, 1.82), (0.04, 0.03, 0.12), "acero")
    P = "cinta"
    m.caja((0, 0, 1.82), (2.56, 0.012, 0.11), "rayas", p=P)
    m.caja((-1.22, 0, 1.82), (0.08, 0.03, 0.13), "plastico_negro", p=P)
    m.caja((1.22, 0, 1.82), (0.08, 0.03, 0.13), "plastico_negro", p=P)
    m.caja((0, -0.012, 1.82), (0.7, 0.012, 0.07), "amarillo_p", p=P)
    m.texto("NO PASAR", (0, -0.02, 1.82), 0.045, 0.006, "negro", p=P, res=1)


@modelo(78, "hangar", "vehiculo", (6, 3, 3))
def contenedor_envio_grande(m):
    # Contenedor de chapa nervada con bastidor, esquineras, bolsillos para horquillas y puertas dobles con candado
    m.caja((0, 0, 1.5), (5.8, 2.8, 2.8), "azul_p")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.caja((sx * 2.9, sy * 1.4, 1.5), (0.2, 0.2, 3.0), "oscuro")
            for z in (0.12, 2.88):
                m.caja((sx * 2.88, sy * 1.38, z), (0.3, 0.3, 0.24), "acero", bisel=0.03)
    for z in (0.08, 2.92):
        for s in (-1, 1):
            m.caja((0, s * 1.4, z), (5.6, 0.18, 0.16), "oscuro")
            m.caja((s * 2.9, 0, z), (0.18, 2.6, 0.16), "oscuro")
    # Nervaduras de las paredes largas y del techo
    for k in range(19):
        x = -2.6 + 0.29 * k
        for s in (-1, 1):
            m.prisma([(-0.09, 0), (0.09, 0), (0.05, 0.07), (-0.05, 0.07)], 0.22, 2.78, "azul_p", "xy",
                     c=(x, s * 1.4, 0), rot=(0, 0, 0 if s > 0 else 180))
    for k in range(9):
        m.caja((-2.4 + 0.6 * k, 0, 2.93), (0.3, 2.5, 0.06), "azul_p")
    for x in (-1.2, 1.2):
        m.caja((x, 0, 0.1), (0.7, 2.84, 0.2), "negro")
        m.marco((x, -1.42, 0.12), 0.8, 0.26, 0.04, 0.03, "amarillo_p")
    # Puertas dobles en el extremo +X: hojas, barras de cierre con levas, manetas, bisagras y candado
    for s, nom in ((-1, "puerta_izq"), (1, "puerta_der")):
        m.caja((2.93, s * 0.66, 1.5), (0.08, 1.28, 2.66), "azul_p", p=nom)
        for z in (0.7, 1.5, 2.3):
            m.caja((2.98, s * 0.66, z), (0.04, 1.2, 0.3), "azul_p", bisel=0.0, p=nom)
        for dy in (0.3, 0.9):
            m.cil((3.02, s * dy, 1.5), 0.03, 2.7, "acero", seg=6, p=nom)
            for z in (0.2, 2.8):
                m.caja((3.02, s * dy, z), (0.08, 0.14, 0.08), "acero", p=nom)
            m.caja((3.05, s * dy + 0.1 * s, 1.2), (0.03, 0.3, 0.05), "acero", p=nom)
        for z in (0.5, 1.5, 2.5):
            m.cil((2.96, s * 1.32, z), 0.04, 0.2, "acero", seg=6)
    m.caja((3.07, 0.0, 1.25), (0.06, 0.2, 0.14), "acero")
    m.caja((3.1, 0, 1.1), (0.08, 0.18, 0.16), "oro", bisel=0.02, p="candado")
    m.tubo((3.1, 0, 1.2), 0.06, 0.03, 0.02, "cromo", eje="x", seg=10, p="candado")
    # Marcas: código en relieve, banda de la compañía, placa de datos y testigo de seguimiento
    m.caja((0, -1.44, 1.9), (3.4, 0.02, 0.5), "blanco_liso")
    m.texto("ALBA 0417", (0, -1.46, 1.9), 0.3, 0.02, "negro", res=1)
    m.caja((-2.2, -1.44, 0.8), (0.7, 0.02, 0.5), "plastico")
    for k in range(4):
        m.caja((-2.25 + 0.02 * k, -1.455, 0.95 - 0.09 * k), (0.5 - 0.06 * k, 0.01, 0.035), "negro")
    m.caja((2.3, -1.44, 2.5), (0.3, 0.03, 0.14), "oscuro")
    m.caja((2.3, -1.46, 2.5), (0.2, 0.02, 0.06), "neon")
    m.prisma([(-0.3, -0.25), (0.3, -0.25), (0, 0.3)], -0.012, 0.012, "amarillo_p", "xz", c=(2.0, -1.45, 1.0))


@modelo(79, "hangar", "vehiculo", (3, 2, 3))
def montacargas(m):
    # Carretilla elevadora flotante: chasis con contrapeso, repulsores, mástil, carro con horquillas, puesto y techo
    m.caja((0.35, 0, 0.75), (2.0, 1.5, 0.7), "amarillo_p", bisel=0.08)
    m.caja((1.15, 0, 0.95), (0.6, 1.56, 1.0), "oscuro", bisel=0.1)                       # contrapeso
    m.caja((0.35, 0, 0.42), (2.04, 1.54, 0.08), "rayas")
    for sx in (-0.4, 1.1):
        for sy in (-1, 1):
            m.torno((sx, sy * 0.6, 0.2), [(0.2, 0.2), (0.3, 0.12), (0.32, 0.0), (0.22, 0.0), (0.18, 0.08), (0, 0.1)],
                    "gris_liso", seg=12)
            m.cil((sx, sy * 0.6, 0.19), 0.2, 0.04, "neon", seg=12, p="repulsores_neon")
    # Puesto de conducción: asiento, volante, palancas y tablero
    m.caja((0.55, 0, 1.2), (0.6, 0.6, 0.14), "goma", bisel=0.04)
    m.caja((0.86, 0, 1.55), (0.12, 0.6, 0.7), "goma", rot=(0, 10, 0), bisel=0.04)
    m.caja((-0.25, 0, 1.3), (0.3, 1.2, 0.5), "oscuro", bisel=0.04)
    m.barrido([(-0.2, 0, 1.5), (0.0, 0, 1.8)], 0.03, "acero", seg=5)
    m.tubo((0.02, 0, 1.82), 0.2, 0.04, 0.035, "plastico_negro", eje="x", seg=14, rot=(0, -35, 0))
    for k in range(3):
        m.cil((-0.2, 0.3 + 0.1 * k, 1.68), 0.015, 0.26, "cromo", seg=4)
        m.esfera((-0.2, 0.3 + 0.1 * k, 1.82), 0.035, ("rojo_p", "amarillo_p", "azul_p")[k], seg=6, anillos=4)
    m.caja((-0.33, -0.3, 1.58), (0.03, 0.3, 0.16), "neon", rot=(0, -20, 0), p="pantalla_neon")
    # Techo protector tubular con rejilla y girofaro
    for sx, sy in ((-0.35, -0.68), (-0.35, 0.68), (1.25, -0.68), (1.25, 0.68)):
        m.barrido([(sx, sy, 1.1), (sx + (0.1 if sx < 0 else -0.1), sy, 2.75)], 0.045, "oscuro", seg=6)
    m.caja((0.45, 0, 2.78), (1.6, 1.46, 0.07), "oscuro", bisel=0.02)
    for k in range(6):
        m.caja((-0.2 + 0.26 * k, 0, 2.83), (0.05, 1.3, 0.03), "acero")
    m.cil((1.0, 0.5, 2.88), 0.09, 0.06, "oscuro", seg=8)
    m.esfera((1.0, 0.5, 2.95), 0.09, "neon_naranja", seg=8, anillos=5, esc=(1, 1, 0.9))
    # Mástil de dos perfiles con travesaños, cilindro de elevación y cadena
    for s in (-1, 1):
        m.caja((-0.8, s * 0.45, 1.6), (0.14, 0.12, 2.8), "gris_liso")
        m.caja((-0.72, s * 0.45, 1.6), (0.03, 0.16, 2.8), "gris_liso")
    for z in (0.4, 1.6, 2.9):
        m.caja((-0.8, 0, z), (0.12, 0.9, 0.12), "gris_liso")
    m.cil((-0.78, 0, 1.3), 0.08, 2.0, "cromo", seg=8)
    m.barrido([(-0.3, 0.3, 0.9), (-0.72, 0.3, 0.7)], 0.05, "oscuro", seg=6)
    # Carro portahorquillas (pieza aparte, sube y baja) con respaldo de carga y dos horquillas
    P = "horquilla"
    m.caja((-0.92, 0, 0.9), (0.08, 1.3, 0.5), "oscuro", p=P)
    for y in (-0.5, 0, 0.5):
        m.caja((-0.95, y, 1.5), (0.05, 0.05, 0.8), "oscuro", p=P)
    m.caja((-0.95, 0, 1.9), (0.05, 1.1, 0.05), "oscuro", p=P)
    for s in (-1, 1):
        m.prisma([(-0.98, 0.62), (-0.98, 1.1), (-1.06, 1.1), (-1.06, 0.7), (-1.95, 0.66), (-2.0, 0.62)], s * 0.38 - 0.07,
                 s * 0.38 + 0.07, "acero", "xz", p=P)
    # Carga: caja sobre las horquillas
    m.caja((-1.5, 0, 0.72), (0.9, 1.1, 0.1), "madera_clara", p="carga")
    for y in (-0.45, 0, 0.45):
        m.caja((-1.6, y, 0.64), (1.0, 0.12, 0.06), "madera", p="carga") if False else None
    m.caja((-1.5, 0, 1.2), (0.8, 0.9, 0.86), "gris", bisel=0.04, p="carga")
    m.caja((-1.5, 0, 1.2), (0.83, 0.14, 0.89), "tela_naranja", p="carga")
    # Faros delanteros y piloto trasero
    for s in (-1, 1):
        m.caja((-0.68, s * 0.62, 1.05), (0.06, 0.16, 0.1), "neon_blanco")
        m.caja((1.46, s * 0.55, 1.2), (0.03, 0.14, 0.08), "neon_rojo")


@modelo(80, "hangar", "edificio_grande", (4, 4, 14))
def torre_control(m):
    # Fuste de estructura vista con cristaleras (se ve la escalera de caracol), cabina con cristalera de 360° y antenas
    m.prisma([(1.9 * math.cos(math.radians(45 * k + 22.5)), 1.9 * math.sin(math.radians(45 * k + 22.5))) for k in range(8)],
             0.0, 0.4, "hormigon", "xy")
    R, zf = 1.25, 9.4
    for k in range(4):
        a = math.radians(90 * k + 45)
        x, y = R * math.cos(a), R * math.sin(a)
        m.caja((x, y, (0.4 + zf) / 2), (0.34, 0.34, zf - 0.4), "blanco_liso", rot=(0, 0, 45), bisel=0.05)
        b = math.radians(90 * (k + 1) + 45)
        xm, ym = (x + R * math.cos(b)) / 2, (y + R * math.sin(b)) / 2
        ang = 90 * k + 90
        L = R * math.sqrt(2) - 0.3
        for z in (0.55, 3.4, 6.4, 9.25):
            m.caja((xm, ym, z), (L, 0.2, 0.3), "gris_liso", rot=(0, 0, ang))
        for z0, z1 in ((0.7, 3.25), (3.55, 6.25), (6.55, 9.1)):
            m.caja((xm, ym, (z0 + z1) / 2), (L, 0.06, z1 - z0), "cristal", rot=(0, 0, ang))
        m.caja((xm * 1.04, ym * 1.04, 4.9), (0.08, 0.1, 8.4), "neon", rot=(0, 0, ang)) if k == 0 else None
    # Escalera de caracol interior: eje central y peldaños en abanico (visibles a través del cristal)
    m.cil((0, 0, 4.9), 0.12, 9.0, "acero", seg=8)
    n = 44
    for i in range(n):
        a = math.radians(30 * i)
        z = 0.6 + 8.6 * i / n
        m.caja((0.48 * math.cos(a), 0.48 * math.sin(a), z), (0.75, 0.26, 0.05), "rejilla", rot=(0, 0, 30 * i))
    m.barrido([(0.84 * math.cos(math.radians(30 * i)), 0.84 * math.sin(math.radians(30 * i)), 1.5 + 8.6 * i / n)
               for i in range(0, n + 1, 1)], 0.025, "acero", seg=4)
    # Puerta de acceso en la base
    m.marco((0, -0.9, 1.55), 1.2, 2.3, 0.12, 0.16, "gris_liso")
    m.caja((0, -0.9, 1.5), (0.96, 0.08, 2.1), "gris_claro", p="puerta")
    m.caja((0, -0.95, 2.0), (0.4, 0.04, 0.6), "cristal")
    # Cuello y balcón anular con barandilla
    m.torno((0, 0, zf), [(1.0, 0), (1.0, 0.2), (1.9, 0.9), (1.95, 1.0), (0, 1.0)], "blanco_liso", seg=8, rot=(0, 0, 22.5))
    m.torno((0, 0, zf + 1.0), [(2.0, 0), (2.0, 0.12), (1.6, 0.12)], "rejilla", seg=8, rot=(0, 0, 22.5))
    for k in range(8):
        a, b = math.radians(45 * k + 22.5), math.radians(45 * (k + 1) + 22.5)
        pa = (1.95 * math.cos(a), 1.95 * math.sin(a), zf + 1.12)
        pb = (1.95 * math.cos(b), 1.95 * math.sin(b), zf + 1.12)
        m.barandilla(pa, pb, 0.75, postes=2, travesanos=1, r=0.03, seg=5)
    m.torno((0, 0, zf + 0.92), [(1.98, 0), (1.98, 0.06)], "neon", seg=8, rot=(0, 0, 22.5))
    # Cabina: antepecho, cristalera inclinada de 360° con montantes, y cubierta
    zc = zf + 1.12
    m.torno((0, 0, zc), [(1.45, 0), (1.5, 0.5), (0, 0.5)], "gris", seg=8, rot=(0, 0, 22.5))
    m.torno((0, 0, zc + 0.5), [(1.46, 0), (1.76, 1.3), (1.7, 1.3), (1.4, 0.0)], "cristal", seg=8, rot=(0, 0, 22.5), cerrar=True)
    for k in range(8):
        a = math.radians(45 * k + 22.5)
        m.barrido([(1.5 * math.cos(a), 1.5 * math.sin(a), zc + 0.5), (1.8 * math.cos(a), 1.8 * math.sin(a), zc + 1.8)], 0.05,
                  "blanco_liso", seg=4)
    m.cil((0, 0, zc + 0.55), 1.35, 0.1, "oscuro", seg=8, rot=(0, 0, 22.5))
    for k in range(3):                                                                  # consolas interiores
        a = math.radians(120 * k + 30)
        m.caja((0.9 * math.cos(a), 0.9 * math.sin(a), zc + 0.85), (0.7, 0.3, 0.5), "gris_claro", rot=(0, 0, 120 * k + 120))
        m.caja((0.9 * math.cos(a), 0.9 * math.sin(a), zc + 1.2), (0.5, 0.04, 0.3), "neon", rot=(0, 0, 120 * k + 120),
               p="pantallas_neon")
    m.torno((0, 0, zc + 1.8), [(1.9, 0), (1.9, 0.14), (1.2, 0.5), (0, 0.6)], "blanco_liso", seg=8, rot=(0, 0, 22.5))
    m.torno((0, 0, zc + 1.74), [(1.92, 0), (1.92, 0.06)], "neon", seg=8, rot=(0, 0, 22.5))
    # Antenas, radar giratorio y baliza
    zr = zc + 2.4
    m.cil((0, 0, zr + 0.2), 0.14, 0.4, "acero", seg=8)
    m.caja((0, 0, zr + 0.5), (1.5, 0.12, 0.3), "gris_liso", bisel=0.03, p="radar")
    m.prisma(arco_pts(0.8, 0.74, 200, 340, 6, 0, zr + 1.2, 1.0, 0.8), -0.2, 0.2, "blanco_liso", "xz", p="radar")
    m.cil((0.9, 0.7, zr + 0.4), 0.03, 1.4, "acero", seg=5)
    m.cil((-0.8, -0.6, zr + 0.2), 0.025, 1.0, "acero", seg=5)
    m.esfera((0.9, 0.7, zr + 1.12), 0.07, "neon_rojo", seg=6, anillos=4)
    m.cupula((-0.9, 0.7, zr - 0.12), 0.3, "blanco_liso", grosor=0.04, seg=10, anillos=3)
