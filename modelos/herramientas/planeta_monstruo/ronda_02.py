"""Ronda 2: guaridas y estructuras (11-20)."""

import math

import numpy as np

from formas import craneo
from lib import VERDE, VIOLETA, modelo


@modelo("guaridas", "mediana", (6, 1, 5), "Segmento de muralla: pared de placas de quitina con espinas afiladas en "
        "la cima y venas que laten.")
def muralla_espinas(M):
    rnd = M.rnd
    p = M.pieza("muralla", tris=4600, res=200, k=0.12, ruido=(0.04, 1.3), suelo=0.0)
    p.caja((0, 0, 1.9), (5.7, 0.55, 3.8), "piel", red=0.2)
    p.caja((0, 0, 0.3), (6.0, 0.95, 0.6), "piedra", red=0.2)
    # Placas verticales solapadas por las dos caras.
    for cara in (-1, 1):
        for i in range(6):
            x = -2.5 + i * 1.0 + (0.25 if cara > 0 else 0)
            alto = rnd.uniform(3.3, 4.0)
            p.esfera((x, cara * 0.27, alto / 2 + 0.2), 1, "quitina", esc=(0.62, 0.2, alto / 2), rot=(0, rnd.uniform(-5, 5), 0),
                     k=0.06)
            p.esfera((x, cara * 0.33, alto * 0.42), 1, "quitina_negra", esc=(0.3, 0.16, alto * 0.3), k=0.05)
    for x in (-2.95, 2.95):  # pilares de hueso en los extremos (para encajar un segmento con el siguiente)
        p.tubo([(x, 0, 0), (x, 0, 2.2), (x, 0, 4.2)], [0.42, 0.34, 0.3], "hueso_viejo")
    d = p.duro
    for i in range(13):  # espinas de la cima
        x = -2.85 + i * 0.475
        L = rnd.uniform(0.8, 1.35)
        d.cuerno([(x, rnd.uniform(-0.1, 0.1), 3.75), (x + rnd.uniform(-0.1, 0.1), rnd.uniform(-0.25, 0.25), 3.9 + L * 0.5),
                  (x + rnd.uniform(-0.15, 0.15), rnd.uniform(-0.3, 0.3), 3.9 + L)], 0.17, "garra", n=5, seg=3)
    for cara in (-1, 1):  # púas que salen hacia fuera
        for i in range(5):
            x, z = rnd.uniform(-2.5, 2.5), rnd.uniform(1.2, 3.3)
            d.cono((x, cara * 0.3, z), (x, cara * 0.62, z + 0.3), 0.11, "garra", n=5)
    v = M.pieza("venas_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    for cara in (-1, 1):
        for i in range(4):
            x = -2.0 + i * 1.3 + rnd.uniform(-0.2, 0.2) + (0.5 if cara > 0 else 0)
            pts = [(x + rnd.uniform(-0.3, 0.3) * (j > 0), cara * 0.47 - cara * 0.05 * j * 0.3, 0.55 + j * 0.75) for j in range(5)]
            v.duro.tubo(pts, [0.085, 0.075, 0.065, 0.05, 0.03], "neon_violeta", n=5, suave=8)
            q = pts[2]
            v.duro.tubo([q, (q[0] + 0.45, q[1], q[2] + 0.3), (q[0] + 0.7, q[1], q[2] + 0.9)], [0.05, 0.04, 0.02], "neon_violeta", n=4)


@modelo("guaridas", "prop", (1, 1, 8), "Faro bioluminiscente (la farola de los monstruos): tallo orgánico con un "
        "bulbo violeta arriba.")
def faro_bioluminiscente(M):
    p = M.pieza("faro", tris=1350, res=230, k=0.05, ruido=(0.012, 3.0), suelo=0.0)
    tallo = [(0, 0, 0), (0.08, 0.02, 1.6), (-0.06, 0.06, 3.4), (0.07, -0.04, 5.2), (0.0, -0.1, 6.5), (0.0, -0.16, 6.95)]
    p.tubo(tallo, [0.3, 0.17, 0.14, 0.12, 0.11, 0.14], "raiz", suave=14)
    for j in range(5):  # raíces
        a = math.tau * j / 5 + 0.3
        p.tubo([(0, 0, 0.5), (0.25 * math.cos(a), 0.25 * math.sin(a), 0.15), (0.48 * math.cos(a), 0.48 * math.sin(a), 0.0)],
               [0.12, 0.1, 0.05], "raiz")
    for z, r in ((1.9, 0.2), (3.7, 0.17), (5.4, 0.15)):  # nudos
        p.esfera((0.02, 0.02, z), r, "piel", esc=(1, 1, 0.6), k=0.06)
    p.esfera((0, -0.16, 7.0), 0.22, "carne", k=0.05)  # cáliz
    d = p.duro
    for j in range(5):  # sépalos-garra que sujetan el bulbo
        a = math.tau * j / 5
        c, s = math.cos(a), math.sin(a)
        d.cuerno([(0.12 * c, -0.16 + 0.12 * s, 6.95), (0.47 * c, -0.16 + 0.47 * s, 7.3), (0.3 * c, -0.16 + 0.3 * s, 7.95)], 0.07,
                 "garra", n=5, seg=4)
    b = M.pieza("bulbo_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    b.duro.torno([(0, 7.08), (0.2, 7.14), (0.36, 7.4), (0.33, 7.68), (0.16, 7.9), (0, 8.0)], (0, -0.16, 0), "neon_violeta", n=10)
    for z in (2.6, 4.4):  # pústulas de luz en el tallo
        b.duro.esfera((0.12, -0.06, z), 0.07, "neon_violeta", sub=1)


@modelo("guaridas", "mediana", (5, 5, 3), "Fuente ácida: poza natural de ácido verde que burbujea, con bordes de roca "
        "orgánica.")
def fuente_acida(M):
    rnd = M.rnd
    p = M.pieza("fuente", tris=4300, res=170, k=0.25, ruido=(0.09, 1.0), suelo=0.0)
    for j in range(11):  # anillo de rocas
        a = math.tau * j / 11
        r = rnd.uniform(0.55, 0.85)
        p.esfera((2.0 * math.cos(a), 2.0 * math.sin(a), 0.3), r, "piedra", esc=(1, 1, rnd.uniform(0.8, 1.4)))
    p.esfera((0, 0, -0.2), 1, "piedra", esc=(2.3, 2.3, 0.55))
    p.esfera((0, 0, 0.75), 1, "piedra_venas", esc=(1.85, 1.85, 0.6), resta=True, k=0.15)
    # Surtidor central: aguja de roca retorcida con la boca arriba.
    p.tubo([(0, 0, 0), (0.15, 0.1, 0.9), (-0.1, 0.05, 1.8), (0.05, -0.05, 2.55)], [0.62, 0.42, 0.33, 0.3], "piedra_venas", suave=8)
    p.esfera((0.05, -0.05, 2.7), 0.26, None, resta=True, k=0.05)
    for j in range(3):  # colmillos de roca en el borde
        a = 0.6 + j * 2.1
        p.tubo([(2.1 * math.cos(a), 2.1 * math.sin(a), 0.4), (2.3 * math.cos(a), 2.3 * math.sin(a), 1.5),
                (2.0 * math.cos(a + 0.2), 2.0 * math.sin(a + 0.2), 2.2)], [0.42, 0.26, 0.06], "piedra", suave=6)
    n = M.pieza("acido_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    nd = n.duro
    nd.torno([(0.5, 0.2), (1.8, 0.2), (1.78, 0.42), (0.5, 0.44)], (0, 0, 0), "acido", n=18)
    nd.esfera((0.05, -0.05, 2.62), 0.25, "acido", sub=2, esc=(1, 1, 0.7))
    nd.tubo([(0.3, -0.05, 2.62), (0.5, -0.1, 1.6), (0.72, -0.12, 0.42)], [0.09, 0.06, 0.1], "acido", n=5, suave=5)
    nd.tubo([(-0.2, 0.05, 2.6), (-0.42, 0.2, 1.5), (-0.6, 0.3, 0.42)], [0.08, 0.05, 0.09], "acido", n=5, suave=5)
    for j in range(12):  # burbujas
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.75, 1.6)
        nd.esfera((r * math.cos(a), r * math.sin(a), 0.44), rnd.uniform(0.09, 0.22), "acido", sub=1)


@modelo("guaridas", "mediana", (4, 3, 5), "Trono del jefe: cráneo de una bestia gigante con la mandíbula abierta como "
        "asiento y los ojos encendidos.")
def trono_bestia(M):
    rnd = M.rnd
    p = M.pieza("trono", tris=5600, res=180, k=0.14, ruido=(0.03, 1.5), suelo=0.0)
    # Peana de huesos y roca.
    p.esfera((0, 0.1, 0), 1, "piedra", esc=(1.9, 1.3, 0.75))
    # Mandíbula inferior = asiento (plana, hacia delante).
    p.esfera((0, -0.25, 1.15), 1, "hueso", esc=(1.25, 1.2, 0.36))
    p.tubo([(1.2, 0.9, 1.5), (1.25, 0.0, 1.3), (0.9, -1.0, 1.25), (0, -1.42, 1.3)], [0.3, 0.27, 0.25, 0.26], "hueso", suave=10,
           sim=True)
    p.esfera((0, -0.2, 1.42), 1, "carne", esc=(0.95, 0.95, 0.16), k=0.05)  # lengua seca = cojín
    # Cráneo = respaldo (echado hacia atrás).
    with p.en((0, 0.75, 1.5), rot=(-7, 0, 0)):
        p.esfera((0, 0.25, 1.9), 1, "hueso", esc=(1.45, 1.0, 1.65))
        p.esfera((0, -0.1, 0.9), 1, "hueso", esc=(1.1, 0.6, 0.9))            # paladar/hocico hacia abajo
        p.esfera((0.95, 0.0, 1.6), 0.55, "hueso", esc=(0.8, 0.9, 1.1), sim=True)  # pómulos
        p.tubo([(0.2, -0.62, 2.55), (0.75, -0.6, 2.75), (1.3, -0.25, 2.5)], [0.2, 0.26, 0.18], "hueso", sim=True)  # cejas
        p.esfera((0.62, -0.75, 2.2), 0.42, "negro", esc=(1, 1, 1.15), sim=True, resta=True, k=0.06)   # cuencas
        p.esfera((0, -0.72, 1.5), 0.2, "negro", esc=(0.8, 1, 1.6), resta=True, k=0.04)                # nariz
        p.esfera((0, -0.55, 0.75), 1, "negro", esc=(0.7, 0.5, 0.55), resta=True, k=0.1)              # hueco del paladar
        d = p.duro
        d.cuerno([(1.05, 0.5, 2.9), (1.9, 0.9, 3.5), (1.75, 0.2, 4.6)], 0.38, "garra", n=8, seg=6, sim=True)
        d.cuerno([(0.5, 0.6, 3.3), (0.75, 1.1, 3.9), (0.6, 0.9, 4.5)], 0.2, "garra", n=6, seg=4, sim=True)
        for i in range(5):  # colmillos de arriba, sobre la cabeza del que se sienta
            x = -0.8 + i * 0.4
            L = 0.55 + (0.35 if i in (0, 4) else 0)
            d.cuerno([(x, -0.5, 0.35), (x, -0.62, 0.35 - L * 0.5), (x, -0.5, 0.35 - L)], 0.12, "diente", n=6, seg=3)
    d = p.duro
    for i in range(8):  # dientes del asiento, alrededor
        a = -0.25 + i * (math.pi + 0.5) / 7
        x, y = 1.12 * math.cos(a), -0.3 - 1.05 * math.sin(a)
        L = 0.42 + (0.3 if i in (2, 5) else 0)
        d.cuerno([(x, y, 1.4), (x * 1.08, y - 0.05, 1.4 + L * 0.6), (x, y, 1.4 + L)], 0.11, "diente", n=6, seg=3)
    for s in (-1, 1):  # reposabrazos: costillas
        d.cuerno([(s * 1.35, 0.9, 1.5), (s * 1.7, 0.0, 2.3), (s * 1.45, -0.9, 2.05)], 0.2, "hueso_viejo", n=6, seg=5)
    cr = M.pieza("craneos_base", tris=900, res=90, unir="trono")
    for x, y, g in ((-1.55, -1.0, -40), (1.6, -0.85, 35)):
        with cr.en((x, y, 0.3), rot=(rnd.uniform(-10, 10), 0, g), esc=0.6):
            craneo(cr, rnd, mat="hueso_viejo", mandibula=False)
    o = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    with o.en((0, 0.75, 1.5), rot=(-7, 0, 0)):
        o.duro.esfera((0.62, -0.5, 2.2), 0.3, "neon_violeta", sub=2, sim=True)


@modelo("guaridas", "mediana", (4, 4, 6), "Almacén: capullos de seda colgando como bolsas de un armazón de hueso.")
def almacen_capullo(M):
    rnd = M.rnd
    p = M.pieza("armazon", tris=2700, res=190, k=0.12, ruido=(0.035, 1.4), suelo=0.0)
    # Tres costillas gigantes que se juntan arriba.
    patas = []
    for j in range(3):
        a = math.tau * j / 3 + 0.5
        c, s = math.cos(a), math.sin(a)
        pts = [(1.8 * c, 1.8 * s, 0), (1.9 * c, 1.9 * s, 2.2), (1.4 * c, 1.4 * s, 4.4), (0.4 * c, 0.4 * s, 5.5), (0, 0, 5.75)]
        patas.append(pts)
        p.tubo(pts, [0.36, 0.28, 0.24, 0.2, 0.22], "hueso", suave=12)
        p.esfera((1.8 * c, 1.8 * s, 0), 0.5, "tierra", esc=(1, 1, 0.5))
    p.esfera((0, 0, 5.72), 0.36, "tendon")
    for j in range(3):  # tendones de arriostramiento
        a, b = patas[j][2], patas[(j + 1) % 3][2]
        p.tubo([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, a[2] - 0.5), b], 0.085, "tendon", suave=6, k=0.05)
    c = M.pieza("capullos", tris=3700, res=170, k=0.1, ruido=(0.03, 2.0))
    d = c.duro
    cuelga = [(0, 0, 5.5, 1.0), (0.85, 0.3, 4.9, 0.8), (-0.6, 0.75, 4.75, 0.85), (-0.35, -0.9, 4.95, 0.72), (1.25, -0.9, 4.0, 0.62),
              (-1.35, -0.1, 4.0, 0.66)]
    for x, y, z, s in cuelga:
        L = rnd.uniform(0.6, 1.2)
        zc = z - L - 0.95 * s
        d.tubo([(x * 0.5, y * 0.5, z + 0.1), (x, y, z - L + 0.1)], 0.045, "seda", n=5)
        with c.en((x, y, zc), rot=(rnd.uniform(-8, 8), rnd.uniform(-8, 8), rnd.uniform(0, 360)), esc=s):
            c.torno([(0, -1.0), (0.3, -0.9), (0.56, -0.4), (0.6, 0.1), (0.45, 0.6), (0.16, 0.95), (0.08, 1.05), (0, 1.08)],
                    (0, 0, 0), "seda")
            for v in range(3):  # vueltas de hilo gordo
                pts = [(0.6 * math.cos(t * 5 + v * 2.1) * (1 - abs(t - 0.45) * 1.1), 0.6 * math.sin(t * 5 + v * 2.1) * (1 - abs(t - 0.45) * 1.1),
                        -0.85 + 1.7 * t) for t in np.linspace(0.05, 0.95, 12)]
                c.tubo(pts, 0.06, "tendon", k=0.03)
            c.esfera((0.3, 0.2, -0.2), 0.3, "seda", k=0.15)   # bulto de lo que hay dentro
            c.esfera((-0.25, -0.15, 0.25), 0.26, "seda", k=0.15)
    for j in range(8):  # hilos sueltos entre capullos y costillas
        a = patas[j % 3][2 + j % 2]
        x, y, z, s = cuelga[j % 6]
        d.tubo([a, ((a[0] + x) / 2, (a[1] + y) / 2, (a[2] + z) / 2 - 0.5), (x, y, z - 1.0)], 0.02, "seda", n=4, suave=5)


@modelo("guaridas", "mediana", (4, 4, 3), "Entrada a túnel subterráneo: agujero redondo con bordes de carne y anillos "
        "musculares.")
def tunel_lombriz(M):
    rnd = M.rnd
    eje = np.array([0, -0.62, 0.78])
    eje /= np.linalg.norm(eje)
    p = M.pieza("tunel", tris=6000, res=170, k=0.25, ruido=(0.07, 1.1), suelo=0.0)
    p.esfera((0, 0.3, 0), 1, "tierra", esc=(2.0, 2.0, 2.0))
    for j in range(9):  # terrones levantados alrededor
        a = math.tau * j / 9
        p.esfera((1.75 * math.cos(a), 0.3 + 1.7 * math.sin(a), 0.1), rnd.uniform(0.35, 0.6), "piedra")
    boca = np.array([0, -0.55, 1.55])
    p.capsula(boca + eje * 1.2, boca - eje * 3.0, 1.12, "carne", resta=True, k=0.2)
    # Anillos musculares que se pierden hacia dentro.
    for i in range(5):
        c = boca - eje * (i * 0.52 - 0.15)
        p.toro(c, 1.2 - i * 0.05, 0.27 - i * 0.02, "musculo" if i % 2 == 0 else "carne_viva", eje=eje, k=0.1)
    p.toro(boca + eje * 0.25, 1.36, 0.3, "carne", eje=eje, k=0.2)
    d = p.duro
    u = np.cross(eje, [1, 0, 0])
    for j in range(14):  # corona de dientecillos hacia dentro
        a = math.tau * j / 14
        r = np.array([1, 0, 0]) * math.cos(a) + u * math.sin(a)
        b = boca + eje * 0.3 + r * 1.2
        d.cuerno([b, b - r * 0.3 + eje * 0.2, b - r * 0.62 - eje * 0.05], 0.1, "diente", n=5, seg=3)
    for j in range(6):  # venas gordas que salen del borde por el suelo
        a = math.tau * j / 6 + 0.4
        p.tubo([(1.2 * math.cos(a), 0.2 + 1.2 * math.sin(a), 1.3), (1.75 * math.cos(a), 0.3 + 1.75 * math.sin(a), 0.7),
                (2.1 * math.cos(a + 0.2), 0.3 + 2.0 * math.sin(a + 0.2), 0.05)], [0.16, 0.14, 0.07], "carne_viva", suave=6, k=0.1)


@modelo("guaridas", "prop", (2, 2, 8), "Pilar decorativo de coral alienígena oscuro, negro y púrpura, con puntos de luz.")
def pilar_coral_oscuro(M):
    rnd = M.rnd
    M.mat("coral", "obsidiana", a="#120C1C", b="#3A1C5A", rug=0.45, relieve=0.8, escamas=dict(esc=5.0, fuerza=0.6))
    p = M.pieza("coral", tris=1560, res=230, k=0.1, ruido=(0.03, 2.2), suelo=0.0)
    puntas = []

    def rama(a, dire, largo, r, nivel):
        dire = dire / np.linalg.norm(dire)
        m = a + dire * largo * 0.5 + np.array([rnd.uniform(-0.12, 0.12), rnd.uniform(-0.12, 0.12), 0])
        b = a + dire * largo
        p.tubo([a, m, b], [r, r * 0.85, r * 0.72], "coral")
        if nivel == 0 or r < 0.1:
            p.esfera(b, r * 1.05, "coral", k=0.05)
            puntas.append(b)
            return
        for j in range(2 if nivel > 1 else 3):
            giro = np.array([rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.9, 1.6)])
            rama(b, dire * 0.6 + giro * 0.5, largo * rnd.uniform(0.62, 0.8), r * 0.72, nivel - 1)

    p.esfera((0, 0, 0), 1, "coral", esc=(0.8, 0.8, 0.5))
    rama(np.array([0, 0, 0.0]), np.array([0.03, 0.02, 1.0]), 2.5, 0.42, 3)
    n = M.pieza("puntos_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    for b in puntas:
        n.duro.esfera(b + [0, 0, 0.05], 0.09, "neon_violeta", sub=1)


@modelo("guaridas", "mediana", (6, 6, 5), "Nido aéreo: cuelga de raíces, hecho de ramas y seda, como un avispero "
        "gigante.", ancla="techo")
def nido_aereo(M):
    rnd = M.rnd
    M.mat("papel", "seda", a="#8E7E8A", b="#4A3A52", rug=0.75, fibras=dict(esc=3.0, fuerza=1.0))
    p = M.pieza("nido", tris=5200, res=170, k=0.12, ruido=(0.05, 1.2))
    # Capas de «papel» como faldones, de arriba (ancho) hacia abajo (estrecho).
    capas = [(4.0, 1.5), (3.4, 2.2), (2.75, 2.6), (2.05, 2.75), (1.35, 2.5), (0.7, 2.0), (0.15, 1.3)]
    for i, (z, r) in enumerate(capas):
        p.torno([(0, 0.55), (r * 0.6, 0.5), (r, 0.0), (r * 1.04, -0.42), (r * 0.9, -0.5), (r * 0.82, -0.1), (0, 0.1)],
                (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), z), "papel" if i % 2 else "seda", rot=(rnd.uniform(-4, 4), rnd.uniform(-4, 4), 0))
    p.esfera((0, 0, 2.2), 1, "papel", esc=(2.0, 2.0, 2.1))
    # Entradas: abajo y una lateral.
    p.capsula((0, 0, -0.6), (0, 0, 1.6), 0.5, "negro", resta=True, k=0.1)
    p.capsula((0, -3.2, 2.3), (0, -1.0, 2.5), 0.48, "negro", resta=True, k=0.1)
    p.toro((0, -2.62, 2.35), 0.56, 0.16, "papel", eje=(0, -1, 0.1), k=0.08)
    # Raíces de las que cuelga.
    for j in range(5):
        a = math.tau * j / 5 + 0.3
        c, s = math.cos(a), math.sin(a)
        p.tubo([(1.2 * c, 1.2 * s, 3.6), (0.75 * c, 0.75 * s, 4.4), (0.4 * c + 0.1, 0.4 * s, 4.75), (1.6 * c, 1.6 * s, 5.0)],
               [0.2, 0.24, 0.26, 0.2], "raiz", suave=8)
    p.esfera((0, 0, 4.7), 0.6, "raiz", esc=(1, 1, 0.6))
    d = p.duro
    # Ramas clavadas en el nido.
    for j in range(16):
        a, z = rnd.uniform(0, math.tau), rnd.uniform(0.9, 3.6)
        r = 1.2 + 1.5 * math.sin(max(0.0, min(1.0, (z - 0.1) / 3.4)) * math.pi * 0.62)
        b = np.array([r * math.cos(a), r * math.sin(a), z])
        t = np.array([-math.sin(a), math.cos(a), rnd.uniform(-0.5, 0.5)])
        L = rnd.uniform(0.8, 1.5)
        d.tubo([b * [0.8, 0.8, 1] - t * L * 0.4, b * [1.08, 1.08, 1], b * [1.1, 1.1, 1] + t * L], [0.07, 0.06, 0.02], "corteza", n=5)
    for j in range(7):  # jirones de seda que cuelgan
        a = math.tau * j / 7
        r = 1.5 + 0.8 * (j % 2)
        z = 1.2 + 0.9 * (j % 2)
        L = rnd.uniform(0.7, 1.4)
        d.tubo([(r * math.cos(a), r * math.sin(a), z), (r * math.cos(a) * 1.05, r * math.sin(a) * 1.05, z - L * 0.6),
                (r * math.cos(a), r * math.sin(a), z - L)], [0.05, 0.025, 0.06], "seda", n=5)


@modelo("guaridas", "prop", (3, 3, 2), "Pozo de líquido rojo púrpura brillante, con brocal de piedra orgánica.")
def pozo_sangre(M):
    rnd = M.rnd
    p = M.pieza("pozo", tris=1500, res=150, k=0.14, ruido=(0.05, 1.5), suelo=0.0)
    for capa, (z, n_, r) in enumerate(((0.3, 9, 0.44), (0.9, 8, 0.4), (1.42, 8, 0.34))):
        for j in range(n_):
            a = math.tau * (j + 0.5 * capa) / n_
            p.esfera((1.08 * math.cos(a), 1.08 * math.sin(a), z), r, "piedra", esc=(1.15, 0.9, rnd.uniform(0.8, 1.0)), rot=(0, 0, math.degrees(a) + 90))
    p.cilindro((0, 0, -0.5), (0, 0, 1.55), 1.02, "piedra", k=0.05)
    p.cilindro((0, 0, 0.5), (0, 0, 2.5), 0.86, "piedra_venas", resta=True, k=0.08)
    for j in range(4):  # venas que trepan por el brocal
        a = math.tau * j / 4 + 0.6
        p.tubo([(1.75 * math.cos(a), 1.75 * math.sin(a), 0), (1.45 * math.cos(a + 0.2), 1.45 * math.sin(a + 0.2), 0.8),
                (1.15 * math.cos(a + 0.5), 1.15 * math.sin(a + 0.5), 1.72), (0.8 * math.cos(a + 0.6), 0.8 * math.sin(a + 0.6), 1.5)],
               [0.13, 0.11, 0.09, 0.05], "carne_viva", suave=8, k=0.06)
    d = p.duro
    for j in range(3):
        a = 0.2 + j * 2.2
        d.cuerno([(1.2 * math.cos(a), 1.2 * math.sin(a), 1.5), (1.4 * math.cos(a), 1.4 * math.sin(a), 1.85),
                  (1.15 * math.cos(a), 1.15 * math.sin(a), 2.15)], 0.11, "hueso", n=5, seg=3)
    n = M.pieza("liquido_neon", tris=0, roblox=dict(material="Neon", color="#D0245A"))
    n.duro.torno([(0, 1.0), (0.9, 1.0), (0.9, 1.3), (0.4, 1.34), (0, 1.36)], (0, 0, 0), "sangre_neon", n=14)
    for j in range(5):
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.1, 0.6)
        n.duro.esfera((r * math.cos(a), r * math.sin(a), 1.33), rnd.uniform(0.07, 0.14), "sangre_neon", sub=1)


@modelo("guaridas", "prop", (2, 2, 10), "Tótem ancestral tallado en un hueso gigante: caras de monstruos con ojos "
        "verdes que brillan.")
def totem_ancestral(M):
    rnd = M.rnd
    p = M.pieza("totem", tris=1500, res=240, k=0.08, ruido=(0.02, 2.5), suelo=0.0)
    p.tubo([(0, 0, 0), (0, 0, 4.5), (0, 0, 9.0)], [0.75, 0.62, 0.55], "hueso")
    p.esfera((0, 0, 0), 1, "piedra", esc=(1.0, 1.0, 0.5))
    p.esfera((0, 0, 9.2), 0.62, "hueso", esc=(1.15, 1.0, 0.8))  # cabeza del fémur arriba
    o = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    d = p.duro
    caras = [(1.3, 1.15, 0), (3.5, 1.05, 1), (5.6, 0.98, 2), (7.6, 0.9, 3)]
    for z, s, tipo in caras:
        with p.en((0, 0, z), esc=s):
            p.tubo([(-0.62, -0.5, 0.42), (0, -0.74, 0.3 if tipo % 2 else 0.5), (0.62, -0.5, 0.42)], [0.16, 0.2, 0.16], "hueso", suave=6)  # ceño
            p.esfera((0, -0.72, -0.05), 0.2, "hueso", esc=(0.7, 1, 1.5))                       # nariz
            p.esfera((0.3, -0.62, 0.14), 0.16, "negro", sim=True, resta=True, k=0.03)          # cuencas
            p.esfera((0, -0.62, -0.5), 1, "negro", esc=(0.42, 0.25, 0.14 + 0.05 * tipo), resta=True, k=0.03)  # boca
            p.tubo([(0.45, -0.5, -0.72), (0, -0.7, -0.8), (-0.45, -0.5, -0.72)], 0.11, "hueso", suave=4)      # labio
            for i in range(4):
                x = -0.27 + i * 0.18
                d.cono((x, -0.6, -0.36), (x, -0.63, -0.58 - (0.1 if i in (0, 3) else 0)), 0.06, "diente", n=4)
            if tipo in (0, 2):
                d.cuerno([(0.6, 0, 0.3), (1.0, -0.1, 0.5), (1.02, -0.2, 0.95)], 0.15, "garra", n=5, seg=4, sim=True)
            else:
                p.esfera((0.72, 0.0, 0.05), 1, "hueso_viejo", esc=(0.3, 0.1, 0.42), sim=True, k=0.05)  # orejas-aleta
        with o.en((0, 0, z), esc=s):
            o.duro.esfera((0.3, -0.56, 0.14), 0.11, "neon_verde", sub=1, sim=True)
