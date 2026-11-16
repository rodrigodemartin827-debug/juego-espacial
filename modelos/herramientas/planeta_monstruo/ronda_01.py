"""Ronda 1: guaridas y estructuras (1-10)."""

import math

import numpy as np

from formas import craneo
from lib import VERDE, VIOLETA, modelo


@modelo("guaridas", "grande", (20, 18, 14), "Guarida del líder: cueva orgánica con la entrada como las fauces "
        "abiertas de una bestia gigante, venas violeta, suelo de carne y estalactitas de hueso.")
def guarida_alfa(M):
    rnd = M.rnd
    p = M.pieza("guarida", tris=9800, res=175, k=0.7, ruido=(0.2, 0.42), suelo=0.0)
    # Cráneo-cúpula hueco: piel por fuera, carne viva por dentro.
    p.esfera((0, 1.5, 0), 1, "piel", esc=(9.0, 8.0, 12.2), cascara=1.3)
    p.esfera((0, 1.5, 0), 1, "carne", esc=(8.0, 7.0, 11.2), cascara=0.5)
    # Morro superior que sobresale (el «paladar») y arcos de las cejas.
    p.esfera((0, -6.2, 8.2), 1, "piel", esc=(6.2, 3.6, 2.6))
    p.tubo([(-6.5, -4.5, 8.5), (-3.5, -6.6, 11.0), (0, -7.0, 11.6), (3.5, -6.6, 11.0), (6.5, -4.5, 8.5)],
           [0.9, 1.3, 1.5, 1.3, 0.9], "quitina", suave=14)
    # La boca: se vacía el frente.
    p.esfera((0, -8.4, 2.6), 1, "carne_viva", esc=(5.6, 6.5, 5.4), resta=True, k=0.9)
    # Suelo de carne y lengua que sale por la entrada.
    p.esfera((0, 1.2, 0), 1, "carne", esc=(8.2, 7.2, 0.8))
    p.tubo([(0, 2, 0.2), (0.4, -3, 0.5), (-0.3, -6.5, 0.4), (0.3, -8.6, 0.1)], [2.2, 2.0, 1.6, 0.9],
           "carne_viva", suave=12)
    # Mandíbula inferior: dos ramas de hueso en el suelo que se juntan delante.
    p.tubo([(-7.4, -1.5, 0.3), (-6.4, -5.5, 0.9), (-3.6, -8.3, 1.3), (0, -9.0, 1.5)], [1.0, 1.1, 1.1, 1.2],
           "hueso_viejo", suave=12, sim=True)
    # Costillas de hueso que abrazan la cúpula.
    for y, alto in ((-0.5, 12.6), (3.0, 12.0), (6.2, 9.6)):
        esc = math.sqrt(max(0.0, 1 - ((y - 1.5) / 8.0) ** 2))
        pts = [(9.3 * esc * math.cos(a), y, alto * math.sin(a) * 1.03) for a in np.linspace(0.05, math.pi / 2, 7)]
        p.tubo(pts, [0.75, 0.7, 0.62, 0.55, 0.5, 0.42, 0.3], "hueso", suave=14, sim=True, k=0.25)
    # Cresta de vértebras por el lomo.
    for i in range(9):
        y = -4.5 + i * 1.55
        z = 12.2 * math.sqrt(max(0.05, 1 - ((y - 1.5) / 8.0) ** 2))
        p.esfera((0, y, z + 0.1), 0.72 - i * 0.03, "hueso", esc=(1.0, 0.8, 1.0), k=0.3)
    # Cuencas de los ojos (hundidas) a los lados del morro.
    for s in (-1, 1):
        p.esfera((s * 5.6, -4.6, 8.6), 1.25, "negro", resta=True, k=0.4)
    # Bultos de carne y tumores en la base.
    for i in range(14):
        a = rnd.uniform(0.25, math.tau - 0.25) + math.pi / 2 + 0.6
        if abs(math.cos(a - math.pi / 2)) < 0.0:
            continue
        r = rnd.uniform(0.9, 1.7)
        p.esfera((9.0 * math.cos(a), 1.5 + 8.0 * math.sin(a), rnd.uniform(0.2, 1.0)), r, "carne",
                 esc=(1, 1, rnd.uniform(0.6, 1.0)))

    d = p.duro
    # Colmillos de arriba (cuelgan del morro) y de abajo (salen de la mandíbula).
    for i in range(9):
        t = (i - 4) / 4
        x = 5.0 * t
        y = -8.6 + 2.4 * t * t
        z = 6.4 + 0.9 * t * t
        L = 2.6 - 1.2 * abs(t) + (0.9 if i in (2, 6) else 0)
        d.cuerno([(x, y, z + 0.6), (x * 1.02, y - 0.25, z - L * 0.5), (x * 0.98, y + 0.15, z - L)], 0.42, "diente",
                 n=6, seg=4)
    for i in range(8):
        t = (i - 3.5) / 3.5
        x = 4.6 * t
        y = -9.1 + 2.3 * t * t
        L = 2.0 - 0.7 * abs(t) + (0.8 if i in (1, 6) else 0)
        d.cuerno([(x, y, 1.3), (x * 1.03, y - 0.3, 1.5 + L * 0.5), (x, y + 0.1, 1.6 + L)], 0.4, "diente", n=6, seg=4)
    # Estalactitas de hueso dentro.
    for i in range(16):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.5, 5.6)
        x, y = r * math.cos(a), 2.0 + r * math.sin(a) * 0.9
        techo = 10.9 * math.sqrt(max(0.1, 1 - (x / 8.0) ** 2 - ((y - 1.5) / 7.0) ** 2))
        L = rnd.uniform(1.4, 3.4)
        d.cuerno([(x, y, techo + 0.4), (x + rnd.uniform(-0.2, 0.2), y, techo - L * 0.5),
                  (x + rnd.uniform(-0.3, 0.3), y + rnd.uniform(-0.3, 0.3), techo - L)], rnd.uniform(0.28, 0.5),
                 "hueso", n=6, seg=3)
    # Cuernos del cráneo.
    d.cuerno([(4.6, -1.5, 11.0), (7.4, -0.5, 13.2), (8.6, -3.2, 14.6)], 1.0, "garra", n=8, seg=6, sim=True)

    # Venas pulsantes: por dentro (paredes) y por fuera.
    v = M.pieza("venas_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    for i in range(11):
        a0 = rnd.uniform(0, math.tau)
        dentro = i < 7
        R = (7.55, 6.55, 10.75) if dentro else (9.25, 8.25, 12.5)
        pts = []
        a = a0
        for j in range(7):
            f = 0.08 + j * 0.13
            a += rnd.uniform(-0.3, 0.3)
            ce = math.cos(f * math.pi / 2)
            x, y, z = R[0] * math.cos(a) * ce, 1.5 + R[1] * math.sin(a) * ce, R[2] * math.sin(f * math.pi / 2)
            pts.append((x, y, z))
        if not dentro and any(q[1] < -4.5 for q in pts):
            continue
        v.duro.tubo(pts, [0.2, 0.19, 0.17, 0.15, 0.13, 0.1, 0.06], "neon_violeta", n=5, suave=12)
    # Ojos que arden en las cuencas.
    o = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    o.duro.esfera((5.3, -4.3, 8.6), 0.75, "neon_violeta", sub=2, sim=True)



def _domo(R, c=(0, 0, 0)):
    """Punto y normal de un domo elipsoidal: f(azimut, elevación) con elevación 0 = base, pi/2 = cima."""

    def f(az, el, extra=0.0):
        d = np.array([math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)])
        pt = np.array(c) + d * np.array(R)
        n = d / np.array(R)
        n /= np.linalg.norm(n)
        return pt + n * extra, n

    return f


@modelo("guaridas", "mediana", (8, 8, 6), "Nido básico: cúpula de piel curtida con placas de quitina, entrada "
        "ovalada sin puerta e interior oscuro con bulbos bioluminiscentes.")
def nido_comun(M):
    rnd = M.rnd
    p = M.pieza("nido", tris=6200, res=150, k=0.3, ruido=(0.09, 0.9), suelo=0.0)
    f = _domo((3.6, 3.6, 5.3))
    p.esfera((0, 0, 0), 1, "piel", esc=(3.6, 3.6, 5.3), cascara=0.55)
    p.esfera((0, 0, 0), 1, "carne", esc=(3.1, 3.1, 4.8), cascara=0.3)
    # Placas de quitina solapadas, como tejas, en tres hileras.
    for fila, (el, n) in enumerate(((0.28, 9), (0.72, 7), (1.12, 4))):
        for j in range(n):
            az = math.tau * (j + 0.5 * fila) / n + 0.2
            if fila < 2 and abs(((az + math.pi / 2 + math.pi) % math.tau) - math.pi) < 0.62:
                continue  # hueco de la entrada
            pt, nrm = f(az, el, 0.05)
            p.esfera(pt, 1, "quitina", esc=(rnd.uniform(1.0, 1.25), rnd.uniform(1.15, 1.4), 0.3), eje=nrm, k=0.12)
    # Entrada ovalada con labio de carne.
    p.esfera((0, -3.5, 1.75), 1, "carne_viva", esc=(1.25, 1.7, 1.85), resta=True, k=0.25)
    p.toro((0, -3.42, 1.8), 1.42, 0.3, "carne_viva", eje=(0, -1, 0.22), esc=(1.0, 1.32, 1.0), k=0.2)
    # Chimenea arriba.
    p.toro((0, 0, 5.2), 0.75, 0.3, "quitina", k=0.2)
    p.cilindro((0, 0, 4.2), (0, 0, 6.5), 0.5, None, resta=True, k=0.15)
    # Tendones que lo anclan al suelo.
    for j in range(8):
        az = math.tau * j / 8 + 0.35
        if abs(((az + math.pi / 2 + math.pi) % math.tau) - math.pi) < 0.5:
            continue
        a, _ = f(az, 0.5)
        b, _ = f(az + rnd.uniform(-0.2, 0.2), 0.0)
        p.tubo([a, a * [1.12, 1.12, 0.55], b * 1.18 + [0, 0, 0.15], b * 1.42 + [0, 0, 0.05]], [0.26, 0.3, 0.26, 0.12],
               "raiz", suave=8)
    d = p.duro
    for j in range(7):  # púas cortas en la cima
        az = math.tau * j / 7
        a, nrm = f(az, 1.28, -0.1)
        d.cuerno([a, a + nrm * 0.5 + [0, 0, 0.2], a + nrm * 0.7 + [0, 0, 0.75]], 0.15, "garra", n=5, seg=3)
    b = M.pieza("bulbos_biolum", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    g = _domo((2.95, 2.95, 4.6))
    for j in range(7):  # bulbos colgando del techo, dentro
        az, el = rnd.uniform(0, math.tau), rnd.uniform(0.75, 1.35)
        a, _ = g(az, el)
        L = rnd.uniform(0.6, 1.3)
        b.duro.tubo([a + [0, 0, 0.2], a - [0, 0, L]], [0.05, 0.035], "neon_violeta", n=4)
        b.duro.esfera(a - [0, 0, L + 0.16], rnd.uniform(0.16, 0.26), "neon_violeta", sub=1, esc=(1, 1, 1.35))
    for j in range(9):  # pústulas alrededor de la entrada
        a = math.tau * j / 9 + 0.3
        dz = 1.9 * math.sin(a)
        b.duro.esfera((1.45 * math.cos(a), -3.72 + 0.22 * dz, 1.8 + dz), rnd.uniform(0.09, 0.15), "neon_violeta", sub=1)


@modelo("guaridas", "mediana", (10, 8, 7), "Nido de guerrero: blindado con bandas de quitina, espinas por fuera y "
        "trofeos de hueso colgados en la entrada.")
def nido_guerrero(M):
    rnd = M.rnd
    R = (4.5, 3.6, 6.3)
    f = _domo(R)
    p = M.pieza("nido", tris=5200, res=160, k=0.3, ruido=(0.08, 0.9), suelo=0.0)
    p.esfera((0, 0, 0), 1, "quitina_negra", esc=R, cascara=0.7)
    p.esfera((0, 0, 0), 1, "carne", esc=(3.9, 3.0, 5.7), cascara=0.3)
    # Bandas de blindaje de lado a lado.
    for y, gr in ((-1.5, 0.5), (0.2, 0.55), (1.9, 0.5)):
        e = math.sqrt(1 - (y / R[1]) ** 2)
        pts = [(R[0] * e * 1.03 * math.cos(a), y, R[2] * e * 1.03 * math.sin(a)) for a in np.linspace(0, math.pi, 13)]
        p.tubo(pts, gr, "quitina", k=0.15)
    # Placas-escudo (escápulas de bestia) a los lados.
    for s in (-1, 1):
        pt, nrm = f(math.pi / 2 - s * math.pi / 2 + s * 0.25, 0.42, 0.1)
        p.esfera(pt, 1, "hueso_viejo", esc=(1.5, 1.9, 0.28), eje=nrm, k=0.1)
    p.esfera((0, -3.6, 1.7), 1, "carne_viva", esc=(1.5, 1.6, 2.1), resta=True, k=0.25)
    p.toro((0, -3.35, 1.7), 1.65, 0.34, "quitina", eje=(0, -1, 0.2), esc=(1.0, 1.3, 1.0), k=0.15)
    d = p.duro
    # Colmillos enormes que enmarcan la entrada.
    for s in (-1, 1):
        d.cuerno([(s * 1.9, -3.3, 0.0), (s * 2.5, -4.3, 2.2), (s * 1.3, -4.5, 4.6)], 0.48, "hueso", n=8, seg=6)
    # Espinas por todo el exterior.
    for j in range(30):
        az, el = rnd.uniform(0, math.tau), rnd.uniform(0.2, 1.45)
        if abs(((az + math.pi / 2 + math.pi) % math.tau) - math.pi) < 0.7 and el < 0.9:
            continue
        a, nrm = f(az, el, -0.15)
        L = rnd.uniform(0.9, 1.8)
        dobla = np.array([rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0.35])
        d.cuerno([a, a + nrm * L * 0.55, a + nrm * L + dobla * L * 0.4], rnd.uniform(0.2, 0.3), "garra", n=5, seg=3)
    # Trofeos: cráneos colgados con tendones a los lados de la entrada.
    t = M.pieza("trofeos", tris=1500, res=120, unir="nido")
    for (x, z, giro, tam) in ((-2.6, 2.3, 25, 0.8), (2.7, 1.9, -30, 0.7), (0.0, 4.55, 0, 0.72)):
        y = -4.25 if x else -3.95
        with t.en((x, y, z), rot=(rnd.uniform(-12, 8), rnd.uniform(-10, 10), giro), esc=tam):
            craneo(t, rnd, mat="hueso", cuernos=2 if x == 0 else 0, largo=rnd.uniform(1.0, 1.3))
        d.tubo([(x, y + 0.15, z + tam * 0.9), (x * 0.96, y + 0.6, z + tam * 0.9 + 0.9)], 0.045, "tendon", n=4)
    # Ristra de huesos colgando en el dintel.
    for j in range(5):
        x = -1.3 + j * 0.65
        z = 3.75 - abs(x) * 0.5
        L = rnd.uniform(0.5, 0.9)
        d.tubo([(x, -4.0, z + 0.3), (x, -4.05, z - L * 0.2)], 0.025, "tendon", n=4)
        d.tubo([(x, -4.05, z - L * 0.2), (x + 0.02, -4.07, z - L)], [0.07, 0.05, 0.08], "hueso", n=5, suave=2)


@modelo("guaridas", "mediana", (10, 10, 8), "Nido del chamán: cúpula cubierta de hongos luminosos, cristales "
        "púrpura que crecen del techo y humo verde que sale por arriba.")
def nido_chaman(M):
    rnd = M.rnd
    R = (4.6, 4.6, 5.4)
    f = _domo(R)
    M.mat("corteza_nido", "piel_purpura", a="#3A2452", b="#191024", rug=0.7)
    p = M.pieza("nido", tris=4300, res=150, k=0.4, ruido=(0.12, 0.7), suelo=0.0)
    p.esfera((0, 0, 0), 1, "corteza_nido", esc=R, cascara=0.6)
    p.esfera((0, 0, 0), 1, "carne", esc=(4.1, 4.1, 4.9), cascara=0.3)
    p.esfera((0, -4.5, 1.6), 1, "carne_viva", esc=(1.3, 1.6, 2.0), resta=True, k=0.3)
    # Raíces gordas que suben por la cúpula como nervios.
    for j in range(7):
        az = math.tau * j / 7 + 0.9
        if abs(((az + math.pi / 2 + math.pi) % math.tau) - math.pi) < 0.45:
            az += 0.6
        pts = []
        for el in np.linspace(-0.05, 1.25, 6):
            az += rnd.uniform(-0.18, 0.18)
            pts.append(f(az, max(el, 0.0), 0.05)[0] * (1.25 if el < 0 else 1.0))
        p.tubo(pts, [0.42, 0.36, 0.3, 0.25, 0.2, 0.14], "raiz", suave=12, k=0.25)
    # Boca de la chimenea.
    p.toro((0, 0, 5.3), 0.85, 0.36, "raiz", k=0.25)
    p.cilindro((0, 0, 4.2), (0, 0, 6.6), 0.55, None, resta=True, k=0.15)
    d = p.duro
    h = M.pieza("hongos_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    # Hongos por toda la cúpula: pie y sombrero con volumen, y un botón de luz en cada sombrero.
    for j in range(22):
        az, el = rnd.uniform(0, math.tau), rnd.uniform(0.12, 1.2)
        if abs(((az + math.pi / 2 + math.pi) % math.tau) - math.pi) < 0.5 and el < 0.75:
            continue
        a, nrm = f(az, el, -0.1)
        arriba = nrm * 0.55 + np.array([0, 0, 0.45])
        arriba /= np.linalg.norm(arriba)
        alto, r = rnd.uniform(0.6, 1.3), rnd.uniform(0.35, 0.65)
        tope = a + arriba * alto
        d.tubo([a, a + nrm * alto * 0.4 + arriba * alto * 0.2, tope], [0.13, 0.09, 0.08], "hongo_tallo", n=5)
        d.torno([(0, -0.02), (r * 0.8, -0.08), (r, 0.0), (r * 0.8, r * 0.36), (r * 0.35, r * 0.62), (0, r * 0.7)], tope,
                "hongo_sombrero", n=8, eje=arriba)
        h.duro.esfera(tope + arriba * r * 0.66, r * 0.2, "neon_verde", sub=1)
    # Amuletos de hueso colgando sobre la entrada.
    for j in range(4):
        x = -0.9 + j * 0.6
        L = rnd.uniform(0.5, 1.0)
        d.tubo([(x, -4.55, 3.55 - abs(x) * 0.3), (x, -4.65, 3.4 - abs(x) * 0.3 - L)], 0.025, "tendon", n=4)
        d.cuerno([(x, -4.65, 3.4 - abs(x) * 0.3 - L), (x + 0.06, -4.7, 3.1 - abs(x) * 0.3 - L),
                  (x, -4.6, 2.85 - abs(x) * 0.3 - L)], 0.08, "diente", n=5, seg=3)
    c = M.pieza("cristales_cristal", tris=0, angulo=25, roblox=dict(material="Glass", color=VIOLETA, transparencia=0.2))
    for j in range(9):
        az = math.tau * j / 9 + rnd.uniform(-0.2, 0.2)
        a, nrm = f(az, rnd.uniform(1.0, 1.3), -0.2)
        dire = nrm + np.array([0, 0, rnd.uniform(0.6, 1.3)])
        dire /= np.linalg.norm(dire)
        L = rnd.uniform(1.0, 2.4)
        c.duro.prisma(a, a + dire * L, rnd.uniform(0.16, 0.3), "cristal", n=6, punta=0.3, giro=rnd.uniform(0, 1))
    s = M.pieza("humo_neon", tris=900, res=70, k=0.5, ruido=(0.12, 1.2),
                roblox=dict(material="Neon", color=VERDE, transparencia=0.55))
    M.mat("humo", "neon_verde", a="#39FF14", b="#0F8A2A", emis=(VERDE, 0.7))
    x = y = 0.0
    for j in range(7):
        z = 5.6 + j * 0.42
        x += rnd.uniform(-0.25, 0.3)
        y += rnd.uniform(-0.25, 0.25)
        s.esfera((x, y, z), 0.42 + 0.1 * math.sin(j * 1.3) + j * 0.045, "humo")


@modelo("guaridas", "grande", (16, 14, 12), "Colmena comunal: panal orgánico gigante de celdas hexagonales, con "
        "varias entradas y resina brillante.")
def colmena_comunal(M):
    rnd = M.rnd
    M.mat("cera", "piel", a="#3B2548", b="#1A1024", rug=0.6, escamas=dict(esc=3.0, fuerza=0.3))
    lob = [((0, 0, 3.6), (7.6, 6.6, 4.6)), ((0.3, 0.2, 7.2), (6.1, 5.4, 3.9)), ((-0.2, 0.1, 10.0), (3.9, 3.6, 2.6))]

    def radio(az, z):
        best = 0.0
        for c, r in lob:
            t = (z - c[2]) / r[2]
            if abs(t) < 1:
                e = math.sqrt(1 - t * t)
                best = max(best, e / math.sqrt((math.cos(az) / r[0]) ** 2 + (math.sin(az) / r[1]) ** 2))
        return best

    p = M.pieza("colmena", tris=10800, res=185, k=1.1, ruido=(0.12, 0.5), suelo=0.0)
    for c, r in lob:
        p.esfera(c, 1, "cera", esc=r)
    # Nervios de quitina entre los pisos y contrafuertes en la base.
    for z, k in ((5.9, 1.0), (9.0, 1.0)):
        pts = [(radio(a, z) * 1.02 * math.cos(a), radio(a, z) * 1.02 * math.sin(a), z + 0.25 * math.sin(3 * a))
               for a in np.linspace(0, math.tau, 25)]
        p.tubo(pts, 0.42, "quitina", k=0.3)
    for j in range(9):
        az = math.tau * j / 9 + 0.2
        r0 = radio(az, 2.2)
        p.tubo([(r0 * 0.9 * math.cos(az), r0 * 0.9 * math.sin(az), 3.2), (r0 * 1.08 * math.cos(az), r0 * 1.08 * math.sin(az), 1.2),
                (r0 * 1.3 * math.cos(az + 0.15), r0 * 1.3 * math.sin(az + 0.15), 0.1)], [0.5, 0.6, 0.3], "raiz", suave=8,
               k=0.4)
    # Entradas grandes (túneles) en distintos pisos.
    entradas = [(-math.pi / 2, 1.9, 1.5), (-math.pi / 2 + 0.95, 6.9, 1.0), (-math.pi / 2 - 1.2, 6.4, 1.0),
                (math.pi / 2 + 0.3, 2.2, 1.2), (-math.pi / 2 - 0.1, 9.9, 0.8)]
    for az, z, r in entradas:
        r0 = radio(az, z)
        u = np.array([math.cos(az), math.sin(az), 0])
        p.toro(u * (r0 + 0.05) + [0, 0, z], r * 1.08, r * 0.3, "quitina", eje=u, k=0.3)
        p.capsula(u * (r0 + 1.0) + [0, 0, z], u * (r0 - 3.2) + [0, 0, z - 0.4], r, "carne", resta=True, k=0.2)
    # Celdas hexagonales: panal por toda la superficie.
    hexa = [(0.62 * math.cos(math.tau * i / 6), 0.62 * math.sin(math.tau * i / 6)) for i in range(6)]
    celdas = []
    fila = 0
    z = 1.3
    while z < 11.2:
        r_med = radio(0.7, z)
        n = max(6, int(math.tau * r_med / 1.42))
        for j in range(n):
            az = math.tau * (j + 0.5 * (fila % 2)) / n
            r0 = radio(az, z)
            if r0 < 1.2:
                continue
            if any(abs(((az - ea + math.pi) % math.tau) - math.pi) * r0 < er + 0.95 and abs(z - ez) < er + 0.95
                   for ea, ez, er in entradas):
                continue
            if rnd.random() < 0.3:
                continue
            u = np.array([math.cos(az), math.sin(az), 0])
            # normal aproximada: radial, inclinada según cambia el radio con la altura
            dr = (radio(az, z + 0.2) - radio(az, z - 0.2)) / 0.4 if radio(az, z + 0.2) and radio(az, z - 0.2) else 0.0
            nrm = u + np.array([0, 0, -max(-1.2, min(1.2, dr))])
            nrm /= np.linalg.norm(nrm)
            pt = u * r0 + [0, 0, z]
            p.extrusion(hexa, 1.7, pt, "carne", eje=nrm, resta=True, k=0.06)
            celdas.append((pt, nrm))
        z += 1.2
        fila += 1
    # Resina: tapones brillantes en parte de las celdas y goterones que cuelgan.
    r = M.pieza("resina_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA, transparencia=0.15))
    for pt, nrm in celdas:
        if rnd.random() < 0.38:
            r.duro.tubo([pt - nrm * 0.75, pt - nrm * 0.3, pt - nrm * 0.16], [0.58, 0.58, 0.4], "resina", n=6)
            if rnd.random() < 0.4 and pt[2] > 2.5:
                L = rnd.uniform(0.5, 1.4)
                q = pt - nrm * 0.1 - [0, 0, 0.45]
                r.duro.tubo([q, q - [0, 0, L * 0.6], q - [0, 0, L]], [0.1, 0.05, 0.11], "resina", n=5)
    d = p.duro
    for j in range(8):  # corona de espinas
        az = math.tau * j / 8
        a = np.array([2.6 * math.cos(az) - 0.2, 2.4 * math.sin(az) + 0.1, 11.3])
        d.cuerno([a, a * [1.25, 1.25, 1] + [0, 0, 0.9], a * [1.1, 1.1, 1] + [0, 0, 2.0]], 0.3, "garra", n=6, seg=4)


@modelo("guaridas", "mediana", (4, 4, 16), "Torre vigía: columna vertebral gigante con costillas como escalones, "
        "plataforma arriba y un ojo vigilante.")
def torre_hueso(M):
    rnd = M.rnd
    p = M.pieza("torre", tris=6300, res=215, k=0.1, ruido=(0.035, 1.6), suelo=0.0)
    # Base: montón de tierra y contrafuertes de hueso.
    p.esfera((0, 0, 0), 1, "tierra", esc=(1.9, 1.9, 0.7), k=0.3)
    for j in range(5):
        az = math.tau * j / 5 + 0.4
        p.tubo([(0.5 * math.cos(az), 0.5 * math.sin(az), 1.7), (1.3 * math.cos(az), 1.3 * math.sin(az), 0.8),
                (1.85 * math.cos(az), 1.85 * math.sin(az), 0.05)], [0.3, 0.26, 0.2], "hueso_viejo", suave=6, k=0.15)
    n = 9
    for i in range(n):
        z = 1.1 + i * 1.36
        s = 1.2 - 0.045 * i
        with p.en((0.06 * math.sin(i * 1.7), 0.06 * math.cos(i * 1.3), z), rot=(rnd.uniform(-3, 3), rnd.uniform(-3, 3), i * 14)):
            p.cilindro((0, 0, -0.46), (0, 0, 0.46), 0.6 * s, "hueso", red=0.14)
            p.toro((0, 0, 0), 0.74 * s, 0.2, None, resta=True, k=0.1)  # cintura de la vértebra
            p.tubo([(0, 0.5 * s, 0), (0, 1.15 * s, 0.25), (0, 1.5 * s, 0.75)], [0.3, 0.22, 0.13], "hueso", k=0.12)
            p.tubo([(0.5 * s, 0.1, 0), (1.05 * s, 0.25, 0.12), (1.35 * s, 0.2, 0.4)], [0.26, 0.18, 0.1], "hueso", sim=True,
                   k=0.12)
            p.esfera((0, 0, 0.66), 0.48 * s, "tendon", esc=(1, 1, 0.42), k=0.05)  # disco de cartílago
            # Costilla-escalón: sale hacia delante y se curva, plana por arriba.
            lado = 1 if i % 2 == 0 else -1
            p.tubo([(lado * 0.3, -0.5 * s, 0.1), (lado * 0.9, -1.25, 0.2), (lado * 1.6, -1.5, 0.15), (lado * 1.95, -1.1, 0.05)],
                   [0.24, 0.22, 0.19, 0.11], "hueso_viejo", suave=8, k=0.1)
    # Plataforma de vigía.
    zp = 1.1 + n * 1.36 - 0.25
    p.torno([(0, -0.5), (0.9, -0.42), (1.8, -0.1), (1.95, 0.12), (1.75, 0.3), (0, 0.22)], (0, 0, zp), "piel", k=0.15)
    p.torno([(0, 0.2), (1.6, 0.26), (1.6, 0.36), (0, 0.34)], (0, 0, zp), "carne", k=0.05)
    # Ojo centinela: párpados de carne sobre un tallo.
    zo = zp + 1.75
    p.tubo([(0, 0.25, zp + 0.2), (0.1, 0.4, zp + 0.9), (0, 0.2, zo - 0.3)], [0.42, 0.3, 0.4], "carne_viva", suave=6, k=0.2)
    p.esfera((0, 0.12, zo), 0.86, "carne_viva", k=0.2)
    p.esfera((0, -0.5, zo), 0.7, "negro", resta=True, k=0.08)
    p.toro((0, -0.42, zo), 0.66, 0.16, "piel", eje=(0, -1, 0), k=0.08)
    d = p.duro
    for j in range(7):  # costillas-barandilla
        az = math.tau * (j + 0.5) / 7 + math.pi / 2
        if abs(((az + math.pi / 2 + math.pi) % math.tau) - math.pi) < 0.4:
            continue
        a = np.array([1.75 * math.cos(az), 1.75 * math.sin(az), zp + 0.1])
        d.cuerno([a, a * [1.18, 1.18, 1] + [0, 0, 0.8], a * [0.95, 0.95, 1] + [0, 0, 1.7]], 0.17, "hueso", n=6, seg=5)
    d.esfera((0, -0.47, zo), 0.1, "pupila", sub=1, esc=(0.75, 0.5, 4.2))
    o = M.pieza("ojo_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    o.duro.esfera((0, -0.12, zo), 0.6, "neon_violeta", sub=2)


@modelo("guaridas", "mediana", (6, 6, 3), "Altar ceremonial: losa de piedra oscura con canales por donde corre "
        "líquido púrpura brillante, cráneos y velas bioluminiscentes.")
def altar_sangre(M):
    rnd = M.rnd
    p = M.pieza("altar", tris=3900, res=170, k=0.06, ruido=(0.035, 1.6), suelo=0.0)
    octo = lambda r: [(r * math.cos(math.tau * (i + 0.5) / 8), r * math.sin(math.tau * (i + 0.5) / 8)) for i in range(8)]
    p.extrusion(octo(3.0), 0.5, (0, 0, 0.25), "piedra", red=0.06)
    p.extrusion(octo(2.3), 0.5, (0, 0, 0.7), "piedra", red=0.06)
    p.cilindro((0, 0, 0.9), (0, 0, 1.75), 1.35, "piedra_venas", r2=1.1, red=0.08)
    p.caja((0, 0, 1.98), (4.5, 2.9, 0.5), "obsidiana", red=0.1)
    # Cuenco central y canales tallados que llevan el líquido a las esquinas.
    zt = 2.23
    p.esfera((0, 0, zt + 0.05), 0.62, None, esc=(1, 1, 0.45), resta=True, k=0.03)
    canales = []
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        c = [(0.4 * sx, 0.3 * sy, zt), (1.0 * sx, 0.95 * sy, zt), (1.75 * sx, 0.7 * sy, zt), (2.25 * sx, 1.2 * sy, zt),
             (2.3 * sx, 1.47 * sy, zt - 0.04)]
        canales.append(c)
        p.tubo(c, 0.1, None, resta=True, k=0.02)
    for s in (-1, 1):  # runas talladas: anillo partido alrededor del cuenco
        aro = [(1.25 * math.cos(a) * 1.25, 0.85 * math.sin(a), zt) for a in np.linspace(-1.0, 1.0, 9) + (0 if s > 0 else math.pi)]
        canales.append(aro)
        p.tubo(aro, 0.07, None, resta=True, k=0.02)
    n = M.pieza("canales_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    nd = n.duro
    nd.esfera((0, 0, zt - 0.1), 0.56, "liquido_violeta", sub=2, esc=(1, 1, 0.2))
    for c in canales:
        nd.tubo([(x, y, z - 0.07) for x, y, z in c], 0.085, "liquido_violeta", n=5, suave=10)
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):  # chorros que caen de las esquinas y charcos
        x, y = 2.3 * sx, 1.5 * sy
        nd.tubo([(x, y, zt - 0.08), (x * 1.01, y * 1.03, 1.4), (x * 1.02, y * 1.05, 0.97)], [0.07, 0.045, 0.06],
                "liquido_violeta", n=5)
        nd.esfera((x * 1.02, y * 1.05, 0.955), 0.32, "liquido_violeta", sub=2, esc=(1.1, 0.8, 0.1))
    # Cráneos en las esquinas del primer escalón.
    cr = M.pieza("craneos", tris=1700, res=110, k=0.02, unir="altar")
    for j, az in enumerate((0.55, math.pi - 0.55, math.pi + 0.55, -0.55)):
        with cr.en((2.4 * math.cos(az), 2.4 * math.sin(az), 0.5), rot=(0, 0, math.degrees(az) + 90 + rnd.uniform(-15, 15)),
                   esc=0.72):
            craneo(cr, rnd, mat="hueso_viejo", cuernos=2 if j % 2 == 0 else 0, largo=rnd.uniform(0.95, 1.25))
    # Velas bioluminiscentes: tallos con una llama-bulbo.
    v = M.pieza("velas_biolum", tris=0, roblox=dict(material="Neon", color=VERDE))
    for j in range(8):
        az = math.tau * j / 8 + 0.05
        r = 1.95 if j % 2 else 2.7
        z0 = 0.95 if j % 2 else 0.5
        alto = rnd.uniform(0.55, 1.1)
        x, y = r * math.cos(az), r * math.sin(az)
        p.duro.tubo([(x, y, z0 - 0.05), (x + 0.02, y, z0 + alto * 0.5), (x, y + 0.02, z0 + alto)], [0.13, 0.085, 0.1],
                    "hongo_tallo", n=6)
        v.duro.torno([(0, -0.03), (0.1, 0.03), (0.12, 0.12), (0.06, 0.26), (0, 0.4)], (x, y + 0.02, z0 + alto), "neon_verde",
                     n=6)


@modelo("guaridas", "mediana", (10, 8, 6), "Cueva incubadora: suelo pegajoso, huevos translúcidos con embriones que "
        "brillan en verde y paredes con mucosidad.")
def cueva_incubadora(M):
    rnd = M.rnd
    M.mat("pared_mucosa", "carne_palida", a="#8A7A6A", b="#4A5A32", rug=0.2)
    M.mat("cascara", "mucosa", a="#9AC27A", b="#3E6A3A", rug=0.18, emis=(VERDE, 0.12),
          venas=dict(color="#1E4A1E", esc=3.0, ancho=0.05, hondo=0.4))
    p = M.pieza("cueva", tris=5300, res=165, k=0.5, ruido=(0.17, 0.6), suelo=0.0)
    p.esfera((0, 0.6, 0), 1, "piedra", esc=(4.9, 4.1, 5.8), cascara=0.85)
    p.esfera((0, 0.6, 0), 1, "pared_mucosa", esc=(4.2, 3.4, 5.1), cascara=0.3)
    p.esfera((0, -4.4, 1.2), 1, "pared_mucosa", esc=(3.9, 3.4, 4.3), resta=True, k=0.6)
    M.mat("baba_suelo", "mucosa", a="#2E5A1E", b="#16301A", emis=(VERDE, 0.04))
    p.esfera((0, 0.2, 0), 1, "baba_suelo", esc=(4.4, 3.9, 0.45))
    for j in range(5):  # colmillos de roca en el borde de la boca
        a = 0.5 + j * 0.53
        p.tubo([(4.0 * math.cos(a), -2.3 - 0.9 * math.sin(a), 4.4 * math.sin(a) + 0.2),
                (3.7 * math.cos(a), -3.2 - 0.9 * math.sin(a), 4.0 * math.sin(a) - 0.5)], [0.5, 0.12], "piedra", k=0.3)
    huevos = [(-2.4, -0.6, 1.0), (-1.0, 0.9, 1.25), (0.5, -0.4, 1.1), (1.9, 0.8, 1.0), (2.7, -1.2, 0.85), (-0.7, -2.0, 0.9),
              (1.2, -2.4, 0.8), (-2.9, -2.3, 0.75), (0.2, 2.2, 0.9)]
    for x, y, s in huevos:  # cuna de carne bajo cada huevo
        p.toro((x, y, 0.3), 0.42 * s, 0.2 * s, "carne_viva", k=0.2)
    d = p.duro
    for j in range(9):  # hilos de baba del techo al suelo
        x = rnd.uniform(-3.4, 3.4)
        y = rnd.uniform(-2.6, -1.2)
        techo = 4.6 * math.sqrt(max(0.05, 1 - (x / 4.3) ** 2 - ((y - 0.6) / 3.5) ** 2))
        fin = rnd.choice([0.2, 0.2, techo * 0.45])
        d.tubo([(x, y, techo + 0.3), (x + 0.05, y, (techo + fin) / 2), (x, y + 0.05, fin)], [0.1, 0.03, 0.09 if fin < 1 else 0.06],
               "mucosa", n=5, suave=4)
    c = M.pieza("huevos_cristal", tris=0, roblox=dict(material="Glass", color="#9AC27A", transparencia=0.45))
    e = M.pieza("embriones_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    for x, y, s in huevos:
        inc = (rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(0, 360))
        with c.en((x, y, 0.22), rot=inc, esc=s):
            c.duro.torno([(0, 0), (0.3, 0.07), (0.5, 0.36), (0.5, 0.7), (0.36, 1.05), (0.16, 1.26), (0, 1.32)], (0, 0, 0),
                         "cascara", n=10)
        with e.en((x, y, 0.22), rot=inc, esc=s):
            e.duro.esfera((0, 0.03, 0.55), 0.2, "neon_verde", sub=2, esc=(1, 0.9, 1.25))
            e.duro.tubo([(0, 0.1, 0.42), (0.12, 0.16, 0.3), (0.2, 0.02, 0.36), (0.14, -0.12, 0.5)], [0.09, 0.07, 0.05, 0.0],
                        "neon_verde", n=5)


@modelo("guaridas", "mediana", (12, 3, 1), "Puente orgánico: tentáculos entrelazados y endurecidos, con ventosas "
        "visibles, que salvan un hueco.")
def puente_tentaculo(M):
    rnd = M.rnd
    M.mat("tentaculo", "piel_purpura", a="#4E2A6A", b="#241232", rug=0.5)
    p = M.pieza("puente", tris=5600, res=230, k=0.1, ruido=(0.03, 1.8))
    hebras = []
    for j in range(5):
        fase = j * 1.9
        pts = []
        for x in np.linspace(-6, 6, 25):
            t = x / 6
            borde = max(0.0, abs(t) - 0.78) / 0.22
            y = (j - 2) * 0.52 * (1 + 0.5 * borde) + 0.2 * math.sin(1.1 * x + fase)
            z = 0.52 + 0.15 * math.cos(1.1 * x + fase) + 0.12 * (1 - t * t) - 0.25 * borde
            pts.append((x, y, z))
        hebras.append(pts)
        r = [0.16, 0.3, 0.36, 0.38, 0.38, 0.38, 0.36, 0.3, 0.16] if j % 2 == 0 else [0.2, 0.3, 0.33, 0.34, 0.33, 0.3, 0.2]
        p.tubo(pts, r, "tentaculo")
    # Tentáculos finos que cosen los gordos por encima.
    for j in range(4):
        x0 = -4.2 + j * 2.8
        p.tubo([(x0 - 0.5, -1.4, 0.3), (x0 - 0.2, -0.7, 0.92), (x0 + 0.1, 0.0, 0.98), (x0 + 0.4, 0.7, 0.92), (x0 + 0.7, 1.4, 0.3)],
               [0.08, 0.15, 0.16, 0.15, 0.08], "carne", suave=10, k=0.06)
    d = p.duro
    # Ventosas en los dos tentáculos de los bordes, mirando hacia fuera y hacia abajo.
    for j, s in ((0, -1), (4, 1)):
        for i in range(2, 23):
            if i % 1 != 0:
                continue
            x, y, z = hebras[j][i]
            n = np.array([0.0, s * 0.85, -0.5])
            n /= np.linalg.norm(n)
            c = np.array([x, y, z]) + n * 0.36
            R = 0.13 + 0.03 * math.sin(i * 2.1)
            d.toro(c, R, 0.05, "carne_palida", eje=n, n=8, m=4)
            d.esfera(c - n * 0.03, R * 0.75, "carne_viva", sub=1, esc=(1, 1, 0.4), eje=n)


@modelo("guaridas", "mediana", (6, 2, 8), "Puerta de mandíbulas: dos mandíbulas de bestia con los colmillos "
        "entrelazados, que se abren y cierran girando sobre sus postes.")
def puerta_mandibula(M):
    rnd = M.rnd
    m = M.pieza("marco", tris=2300, res=190, k=0.2, ruido=(0.06, 1.0), suelo=0.0)
    for s in (-1, 1):
        m.tubo([(s * 2.75, 0, 0), (s * 2.85, 0.05, 2.6), (s * 2.8, -0.05, 5.4), (s * 2.7, 0, 7.4)], [0.5, 0.36, 0.32, 0.24],
               "piel", suave=10)
        m.esfera((s * 2.8, 0, 0), 1, "tierra", esc=(0.75, 0.9, 0.5))
        for z in (1.6, 4.0, 6.3):  # nudillos de la bisagra
            m.esfera((s * 2.72, 0, z), 0.5, "tendon", esc=(1, 1, 0.75), k=0.12)
        m.duro.cuerno([(s * 2.7, 0, 7.2), (s * 3.0, 0.1, 7.8), (s * 2.6, 0, 8.6)], 0.24, "garra", n=6, seg=4)
    for s, nombre in ((-1, "mandibula_izq"), (1, "mandibula_der")):
        p = M.pieza(nombre, tris=1600, res=190, k=0.18, ruido=(0.05, 1.1))
        # Rama de hueso (el canto de la bisagra) y encía de carne hacia el centro.
        p.tubo([(s * 2.25, 0, 0.45), (s * 2.4, 0, 2.3), (s * 2.42, 0, 5.0), (s * 2.2, 0, 7.3)], [0.42, 0.5, 0.5, 0.36],
               "hueso", suave=10)
        p.esfera((s * 1.75, 0, 3.9), 1, "carne", esc=(0.85, 0.42, 3.5))
        p.esfera((s * 1.25, 0, 3.9), 1, "carne_viva", esc=(0.42, 0.36, 3.2))
        p.tubo([(s * 2.3, 0, 7.2), (s * 1.5, 0, 7.75), (s * 0.5, 0, 7.6)], [0.36, 0.3, 0.2], "hueso", suave=6)
        p.tubo([(s * 2.3, 0, 0.5), (s * 1.5, 0, 0.3), (s * 0.5, 0, 0.42)], [0.36, 0.3, 0.2], "hueso", suave=6)
        n = 7
        for i in range(n):
            z = 1.1 + (i + (0.5 if s > 0 else 0.0)) * 0.88
            if z > 7.0:
                continue
            L = 1.25 + 0.5 * math.sin(i * 1.9 + s) + (0.5 if i in (2, 4) else 0)
            cae = 0.25 if z > 4 else -0.25
            p.duro.cuerno([(s * 1.15, 0, z), (s * (1.0 - L * 0.5), rnd.uniform(-0.06, 0.06), z + cae * 0.3),
                           (s * (1.0 - L), 0, z + cae)], 0.25, "diente", n=6, seg=4)
        M.articulacion(nombre, "marco", (s * 2.72, 0, 4.0))
    M.notas["animacion"] = "Cada mandíbula gira sobre el eje vertical de su poste (pivote en `articulaciones`)."
