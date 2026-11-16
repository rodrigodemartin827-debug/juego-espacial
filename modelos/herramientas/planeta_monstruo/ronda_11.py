"""Ronda 11: terreno y formaciones (101-105)."""

import math

import numpy as np

from formas import seta
from lib import VERDE, VIOLETA, curva, modelo

NEON_V = dict(material="Neon", color=VIOLETA)


@modelo("terreno", "mediana", (8, 4, 0.5), "Segmento de río de sangre: fluido rojo oscuro entre dos orillas.")
def rio_sangre_segmento(M):
    rnd = M.rnd
    p = M.pieza("orillas", tris=4300, res=250, k=0.12, ruido=(0.04, 1.4), suelo=0.0)
    for s in (-1, 1):
        for i in range(17):   # orilla: rocas y cuajarones a cada lado; el cauce va a lo largo de X y empalma con otro segmento
            x = -3.9 + i * 0.4875
            y = s * (1.62 + 0.14 * math.sin(i * 0.9 + s))
            p.esfera((x, y, 0.02), rnd.uniform(0.33, 0.48), "piedra" if i % 3 else "carne", esc=(1, 1, rnd.uniform(0.62, 0.95)))
        p.caja((0, s * 1.75, 0.07), (8.0, 0.5, 0.26), "piedra", red=0.06, k=0.08)
    for (x, y, r) in ((-1.6, 0.3, 0.36), (1.9, -0.4, 0.3), (0.3, 0.7, 0.2)):   # piedras en mitad de la corriente
        p.esfera((x, y, 0.05), r, "piedra", esc=(1.2, 1, 0.8))
    p.duro.cuerno([(2.6, 0.5, 0.1), (2.9, 0.6, 0.42), (3.3, 0.5, 0.36)], 0.07, "hueso", n=5, seg=3, potencia=0.5)   # una costilla que asoma
    s_ = M.pieza("sangre", tris=0, roblox=dict(material="SmoothPlastic", color="#5A0A12", reflectancia=0.25))
    filas = []
    for x in np.linspace(-4.0, 4.0, 17):
        filas.append([(x, y, 0.2 + 0.035 * math.sin(x * 2.2 + y * 1.7) + 0.02 * math.sin(x * 5.0)) for y in np.linspace(-1.45, 1.45, 7)])
    s_.duro.superficie(filas, 0.24, "sangre")
    for j in range(7):   # espumarajos y coágulos que arrastra
        x, y = rnd.uniform(-3.6, 3.6), rnd.uniform(-1.1, 1.1)
        s_.duro.esfera((x, y, 0.33), rnd.uniform(0.09, 0.18), "sangre", sub=1, esc=(1.6, 1, 0.5))


@modelo("terreno", "mediana", (4, 2, 6), "Cascada de ácido verde: el líquido cae por un risco hasta una poza.")
def cascada_acido(M):
    rnd = M.rnd
    p = M.pieza("risco", tris=4700, res=180, k=0.2, ruido=(0.12, 1.0, 4), suelo=0.0)
    p.caja((0, 0.55, 2.9), (3.6, 0.9, 5.8), "piedra", red=0.3)
    p.esfera((-1.4, 0.3, 2.0), 1, "piedra", esc=(0.75, 0.75, 2.2))
    p.esfera((1.45, 0.3, 2.6), 1, "piedra", esc=(0.7, 0.75, 2.9))
    p.esfera((0, 0.4, 5.4), 1, "piedra", esc=(1.7, 0.8, 0.62))
    p.capsula((0, 1.2, 5.75), (0, -0.2, 5.6), 0.5, "piedra_venas", resta=True, k=0.15)       # canal por donde sale
    p.torno([(0, 0), (1.7, 0), (1.85, 0.36), (1.5, 0.5), (1.3, 0.15), (0, 0.1)], (0, -0.2, 0), "piedra", esc=(1, 0.52, 1), k=0.1)   # poza
    for j in range(5):
        p.esfera((-1.5 + j * 0.75, -0.72, 0.15), rnd.uniform(0.22, 0.34), "piedra")
    n = M.pieza("acido_neon", tris=2200, res=180, k=0.12, ruido=(0.035, 1.6), suelo=0.0, roblox=dict(material="Neon", color=VERDE, transparencia=0.1))
    n.tubo([(0, 1.0, 5.6), (0, 0.1, 5.5), (0, -0.3, 5.0)], [0.36, 0.4, 0.36], "acido")
    for (x, r, z1) in ((-0.42, 0.24, 0.2), (0.0, 0.3, 0.2), (0.4, 0.22, 0.2), (0.72, 0.12, 2.6), (-0.75, 0.1, 3.3)):   # chorros
        n.tubo([(x * 0.5, -0.25, 5.2), (x * 0.9, -0.42, 3.6), (x, -0.45, 1.8), (x * 1.05, -0.42, z1)], [r, r * 0.85, r * 0.75, r * 1.1], "acido")
    n.esfera((0, -0.25, 0.25), 1, "acido", esc=(1.3, 0.52, 0.2))    # la poza
    for j in range(8):   # salpicaduras y burbujas
        x = rnd.uniform(-1.1, 1.1)
        n.duro.esfera((x, -0.3 + rnd.uniform(-0.25, 0.2), 0.45), rnd.uniform(0.07, 0.16), "acido", sub=1)
    n.duro.tubo([(-0.7, 0.05, 0.4), (-1.3, 0.0, 0.25), (-1.75, -0.3, 0.1)], [0.1, 0.07, 0.03], "acido", n=5)   # rebosa por un lado


@modelo("terreno", "mediana", (10, 3, 2), "Puente natural de raíces gruesas entrelazadas.")
def puente_raices(M):
    rnd = M.rnd
    p = M.pieza("puente", tris=6900, res=240, k=0.1, ruido=(0.035, 1.6))

    def arco(x):
        return 1.15 * (1 - (x / 5.0) ** 2)

    for j in range(6):   # raíces maestras que forman el tablero
        y0 = -1.0 + j * 0.4
        fase = j * 1.7
        pts = [(x, y0 + 0.2 * math.sin(x * 0.9 + fase), arco(x) + 0.1 * math.cos(x * 1.1 + fase)) for x in np.linspace(-5, 5, 21)]
        p.tubo(pts, [0.2, 0.26, 0.28, 0.3, 0.28, 0.26, 0.2], "raiz")
    for s in (-1, 1):    # barandillas: una raíz alta a cada lado, con montantes
        pts = [(x, s * (1.25 + 0.08 * math.sin(x * 1.3)), arco(x) + 0.72 + 0.1 * math.sin(x * 2.0 + s)) for x in np.linspace(-4.7, 4.7, 17)]
        p.tubo(pts, [0.1, 0.15, 0.16, 0.15, 0.1], "raiz")
        for x in np.linspace(-4.2, 4.2, 8):
            p.tubo([(x, s * 1.05, arco(x) + 0.05), (x + 0.15, s * 1.3, arco(x) + 0.42), (x, s * 1.25, arco(x) + 0.75)], [0.1, 0.08, 0.08], "raiz", k=0.06)
        for xe in (-5, 5):   # los arranques se abren y se clavan en el suelo
            for k_ in range(2):
                p.tubo([(xe * 0.93, s * (0.5 + k_ * 0.5), arco(xe * 0.93)), (xe * 1.0, s * (0.8 + k_ * 0.5), -0.3), (xe * 1.0, s * (1.0 + k_ * 0.45), -0.75)], [0.22, 0.2, 0.1], "raiz", k=0.1)
    M.mat("vena", "carne_viva", a="#8A1E3A", b="#4A0E2A")
    for j in range(7):   # venas finas que atan las raíces
        x0 = -3.9 + j * 1.3
        p.tubo([(x0, -1.25, arco(x0) + 0.1), (x0 + 0.2, 0, arco(x0 + 0.2) + 0.36), (x0 + 0.4, 1.25, arco(x0 + 0.4) + 0.1)], 0.055, "vena", suave=8, k=0.03)
    d = p.duro
    for j in range(16):  # raicillas colgando por debajo
        x = rnd.uniform(-4.2, 4.2)
        y = rnd.uniform(-1.0, 1.0)
        L = rnd.uniform(0.3, 0.9)
        d.tubo([(x, y, arco(x) - 0.2), (x + rnd.uniform(-0.1, 0.1), y, arco(x) - 0.2 - L * 0.6), (x + rnd.uniform(-0.15, 0.15), y, arco(x) - 0.2 - L)], [0.04, 0.025, 0.0], "raiz", n=4)


@modelo("terreno", "mediana", (6, 6, 4), "Isla flotante pequeña con roca y vegetación monstruosa; flota con energía debajo.",
        ancla="centro")
def isla_flotante(M):
    rnd = M.rnd
    p = M.pieza("isla", tris=5600, res=180, k=0.25, ruido=(0.12, 1.0, 4))
    p.esfera((0, 0, 2.4), 1, "piedra", esc=(2.8, 2.7, 0.7))
    p.tubo([(0.1, 0, 2.2), (-0.2, 0.1, 1.4), (0.1, -0.1, 0.5)], [1.9, 1.1, 0.3], "piedra")           # raigón de roca
    p.tubo([(-1.3, 0.6, 2.2), (-1.5, 0.8, 1.3)], [0.9, 0.2], "piedra")
    p.tubo([(1.2, -0.8, 2.2), (1.5, -1.0, 1.5)], [0.8, 0.2], "piedra")
    p.caja((0, 0, 3.55), (6.5, 6.5, 1.0), None, resta=True, k=0.08)                                  # cima plana
    M.mat("pasto", "membrana", a="#5A2A6A", b="#2A1238", rug=0.5)
    p.esfera((0, 0, 2.92), 1, "pasto", esc=(2.5, 2.4, 0.22), k=0.1)                                   # capa de carne-césped
    for j in range(9):   # raíces colgando por debajo
        a = math.tau * j / 9
        r = rnd.uniform(1.2, 2.3)
        L = rnd.uniform(0.8, 1.7)
        p.tubo([(r * math.cos(a), r * math.sin(a), 2.2), (r * 0.95 * math.cos(a + 0.2), r * 0.95 * math.sin(a + 0.2), 2.0 - L * 0.5), (r * 0.9 * math.cos(a), r * 0.9 * math.sin(a), 2.0 - L)],
               [0.13, 0.09, 0.03], "raiz", k=0.06)
    # Vegetación monstruosa arriba: tres setas, un arbolillo de hueso y un par de rocas.
    v = M.pieza("vegetacion", tris=1600, res=140, k=0.04, ruido=(0.015, 2.5), unir="isla")
    sups = []
    for (x, y, h, r) in ((-1.2, 0.5, 1.05, 0.42), (-0.6, 1.3, 0.66, 0.3), (1.4, 0.9, 0.5, 0.24)):
        with v.en((x, y, 3.0)):
            sup = seta(v, rnd, alto=h, radio=r, k=0.03)
            sups.append((np.array([x, y, 3.0]), sup))
    v.tubo(curva([(1.0, -0.9, 3.0), (1.1, -0.8, 3.5), (0.9, -1.0, 4.0)], 6), [0.13, 0.09, 0.06], "hueso")
    for (dx, dy) in ((0.5, 0.1), (-0.4, -0.3), (0.1, 0.5)):
        v.tubo([(1.05, -0.85, 3.6), (1.05 + dx, -0.85 + dy, 3.75), (1.05 + dx * 1.2, -0.85 + dy * 1.2, 4.2)], [0.06, 0.05, 0.02], "hueso", k=0.03)
    v.esfera((0.2, -1.6, 3.05), 0.3, "piedra")
    v.esfera((-1.9, -0.7, 3.05), 0.36, "piedra", esc=(1, 0.8, 1.2))
    n = M.pieza("energia_neon", tris=0, angulo=25, roblox=dict(material="Neon", color=VIOLETA, transparencia=0.1))
    d = n.duro
    d.prisma((0.1, -0.1, 0.9), (0.05, -0.05, -0.1), 0.22, "cristal", n=6, punta=0.45)          # cristal de empuje bajo el raigón
    d.prisma((0.1, -0.1, 0.5), (0.12, -0.12, 1.2), 0.2, "cristal", n=6, punta=0.5)
    for k_, (z, R) in enumerate(((0.75, 1.0), (0.42, 0.72), (0.12, 0.45))):
        d.toro((0.08, -0.08, z), R, 0.055, "neon_violeta", n=16, m=4, esc=(1, 1, 0.6))
    for base, sup in sups:   # esporas de luz en las setas
        for j in range(3):
            q = np.array(sup(0.3 + 0.2 * j, j * 2.1))
            d.esfera(base + q, 0.045, "neon_violeta", sub=1)


@modelo("terreno", "mediana", (8, 2, 10), "Portal orgánico: anillo de carne y hueso con energía púrpura en el centro. La "
        "entrada y salida del planeta monstruo.")
def portal_monstruo(M):
    rnd = M.rnd
    ZC, RX, RZ = 5.2, 3.2, 4.3

    def aro(t, k=1.0):
        return np.array([RX * k * math.cos(t), 0.0, ZC + RZ * k * math.sin(t)])

    p = M.pieza("portal", tris=5300, res=200, k=0.2, ruido=(0.06, 1.0), suelo=0.0)
    p.toro((0, 0, ZC), 1.0, 0.16, "carne", eje=(0, 1, 0), esc=(RX, RZ, 4.4), k=0.1)                  # anillo de carne
    p.toro((0, 0, ZC), 1.0, 0.07, "carne_viva", eje=(0, 1, 0), esc=(RX * 0.86, RZ * 0.88, 3.4), k=0.1)   # labio interior
    for j in range(14):   # costillas de hueso que abrazan el anillo
        t = math.tau * (j + 0.5) / 14
        if 4.25 < t < 5.2:
            continue
        c = aro(t)
        rad = np.array([math.cos(t), 0, math.sin(t)])
        p.tubo([c - rad * 0.5 + [0, -0.75, 0], c + rad * 0.62 + [0, -0.5, 0], c + rad * 0.85, c + rad * 0.62 + [0, 0.5, 0], c - rad * 0.5 + [0, 0.75, 0]], [0.1, 0.16, 0.19, 0.16, 0.1],
               "hueso", suave=10, k=0.08)
    for j in range(9):    # tumores y nudos de músculo en el anillo
        t = rnd.uniform(0, math.tau)
        c = aro(t, 1.02)
        p.esfera(c + [0, rnd.choice((-1, 1)) * 0.5, 0], rnd.uniform(0.3, 0.5), "musculo", k=0.2)
    # Pie: raíces de carne que lo clavan al suelo y dos losas de roca.
    p.esfera((0, 0, 0.1), 1, "piedra", esc=(3.4, 0.95, 0.75), k=0.3)
    for s in (-1, 1):
        for k_, y in enumerate((-0.7, 0.0, 0.7)):
            p.tubo([aro(-math.pi / 2 + s * 0.45) + [0, y * 0.5, 0], (s * 2.6, y, 0.6), (s * 3.75, y * 1.25, 0.05)], [0.4, 0.36, 0.16], "raiz", suave=8, k=0.2)
    d = p.duro
    for j in range(22):   # dientes hacia el centro, a dos alturas
        t = math.tau * j / 22
        c = aro(t, 0.84)
        rad = np.array([math.cos(t), 0, math.sin(t)])
        y = 0.2 if j % 2 else -0.2
        L = 0.7 if j % 2 else 0.45
        d.cuerno([c + [0, y, 0], c - rad * L * 0.6 + [0, y * 1.3, 0], c - rad * L + [0, y * 0.5, 0]], 0.11, "diente", n=5, seg=3)
    for s in (-1, 1):     # dos cuernos arriba, como una corona
        c = aro(math.pi / 2 - s * 0.55, 1.1)
        d.cuerno([c, c + [s * 0.75, 0, 0.75], c + [s * 0.9, 0, 1.75], c + [s * 0.5, 0, 2.3]], 0.3, "garra", n=7, seg=6)
    # Ojos incrustados en el anillo que vigilan a quien cruza.
    ojos = M.pieza("ojos_neon", tris=0, roblox=NEON_V)
    for t in (0.5, 2.64, 1.2, 1.94, 3.6, 5.82):
        c = aro(t, 1.0)
        for y in (-0.66, 0.66):
            p.esfera(c + [0, y * 0.8, 0], 0.3, "negro", resta=True, k=0.05)
            ojos.duro.esfera(c + [0, y * 0.68, 0], 0.2, "neon_violeta", sub=1)
            d.esfera(c + [0, y * 0.98, 0], 0.05, "pupila", sub=1, esc=(0.6, 0.5, 2.6))
    # La energía: una lente con grosor y un remolino en relieve por las dos caras.
    e = M.pieza("energia_neon", tris=2300, res=190, k=0.1, roblox=dict(material="Neon", color=VIOLETA, transparencia=0.25))
    M.mat("vortice", "liquido_violeta", a="#C04DFF", b="#3A0F6A", emis=(VIOLETA, 0.9), venas=dict(color="#F0D0FF", esc=0.9, ancho=0.06, hondo=0.5, emis=1.0))
    e.esfera((0, 0, ZC), 1, "vortice", esc=(RX * 0.86, 0.16, RZ * 0.88))
    for brazo in range(4):
        pts = []
        for i in range(12):
            f = i / 11
            t = brazo * math.tau / 4 + f * 3.4
            pts.append((RX * 0.8 * f * math.cos(t), 0.0, ZC + RZ * 0.82 * f * math.sin(t)))
        e.tubo(pts, [0.24, 0.22, 0.18, 0.12, 0.06], "vortice")
    e.esfera((0, 0, ZC), 0.36, "vortice", esc=(1, 0.8, 1))
    M.notas["uso"] = "energia_neon es la superficie que se cruza: ponle CanCollide = false y úsala como disparador del viaje."
