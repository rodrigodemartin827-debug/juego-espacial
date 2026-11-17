"""Ronda 7: zona de guerra y entrenamiento (61-70)."""

import math

import numpy as np

from formas import craneo, hueso_largo
from lib import VERDE, VIOLETA, curva, modelo


@modelo("guerra", "prop", (4, 1, 3), "Barricada defensiva: muro bajo de huesos cruzados y espinas.")
def barricada_espinas(M):
    rnd = M.rnd
    p = M.pieza("barricada", tris=1300, res=190, k=0.05, ruido=(0.02, 2.2), suelo=0.0)
    # Tres aspas de hueso y un tronco-espinazo que las cose.
    for x in (-1.5, 0.0, 1.5):
        p.tubo([(x - 0.15, -0.42, 0), (x, 0, 1.2), (x + 0.15, 0.42, 2.3)], [0.16, 0.13, 0.1], "hueso_viejo")
        p.tubo([(x + 0.15, 0.42, 0), (x, 0, 1.2), (x - 0.15, -0.42, 2.3)], [0.16, 0.13, 0.1], "hueso")
        p.esfera((x, 0, 1.2), 0.24, "tendon", k=0.05)
    p.tubo([(-1.95, 0.05, 1.35), (-0.7, -0.05, 1.3), (0.7, 0.05, 1.4), (1.95, -0.05, 1.3)], [0.2, 0.22, 0.22, 0.2], "corteza")
    p.tubo([(-1.9, -0.3, 0.3), (0, -0.36, 0.42), (1.9, -0.3, 0.3)], 0.12, "hueso_viejo", k=0.03)
    d = p.duro
    for i in range(12):  # espinas del tronco: hacia fuera y hacia arriba
        x = -1.75 + i * 0.32
        fuera = -1 if i % 2 else 1
        L = rnd.uniform(0.7, 1.2)
        d.cuerno([(x, 0.0, 1.38), (x + rnd.uniform(-0.1, 0.1), fuera * 0.3, 1.45 + L * 0.5), (x + rnd.uniform(-0.1, 0.1), fuera * 0.42, 1.5 + L)], 0.1, "garra", n=5, seg=3)
    for i in range(7):  # púas bajas hacia el enemigo (-Y)
        x = -1.8 + i * 0.6
        d.cono((x, -0.36, 0.42), (x + rnd.uniform(-0.1, 0.1), -0.5 - 0.0, 1.1), 0.07, "garra", n=4)
    for x in (-1.5, 0.0, 1.5):
        d.toro((x, 0, 1.32), 0.27, 0.035, "tendon", eje=(1, 0, 0), n=7, m=3)


@modelo("guerra", "prop", (4, 4, 2), "Foso trampa con estacas de hueso: se entierra hasta el borde.")
def trampa_foso(M):
    rnd = M.rnd
    p = M.pieza("foso", tris=1350, res=160, k=0.15, ruido=(0.06, 1.3), suelo=0.0)
    p.torno([(0, 0), (2.0, 0), (2.0, 1.55), (1.75, 2.0), (1.5, 1.9), (1.42, 0.3), (0, 0.22)], (0, 0, 0), "tierra")
    for j in range(9):  # terrones y piedras del borde
        a = math.tau * j / 9
        p.esfera((1.7 * math.cos(a), 1.7 * math.sin(a), 1.82), rnd.uniform(0.2, 0.36), "piedra" if j % 2 else "tierra")
    d = p.duro
    for j in range(13):  # estacas
        a, r = rnd.uniform(0, math.tau), 1.15 * math.sqrt(rnd.random())
        x, y = r * math.cos(a), r * math.sin(a)
        L = rnd.uniform(1.0, 1.6)
        d.cuerno([(x, y, 0.2), (x + rnd.uniform(-0.08, 0.08), y + rnd.uniform(-0.08, 0.08), 0.2 + L * 0.5), (x + rnd.uniform(-0.15, 0.15), y + rnd.uniform(-0.15, 0.15), 0.2 + L)],
                 0.09, "hueso" if j % 3 else "hueso_viejo", n=5, seg=3, potencia=0.7)
    d.esfera((0.3, -0.2, 0.26), 0.5, "sangre", sub=1, esc=(1, 0.8, 0.06))
    cr = M.pieza("craneo", tris=420, res=70, unir="foso")
    with cr.en((-0.55, 0.42, 0.25), rot=(15, 20, 130), esc=0.42):
        craneo(cr, rnd, mat="hueso_viejo", mandibula=False, dientes=False)


@modelo("guerra", "prop", (4, 4, 0.3), "Red de tendones para capturar bestias, a medio enrollar, con pesas de hueso.")
def red_captura(M):
    rnd = M.rnd
    p = M.pieza("red", tris=0)
    d = p.duro
    n = 8

    def z(x, y):
        return 0.07 + 0.035 * math.sin(x * 2.3) * math.cos(y * 1.9)

    xs = np.linspace(-1.9, 1.3, n)
    ys = np.linspace(-1.9, 1.9, n)
    for i, x in enumerate(xs):   # hilos en una dirección y en la otra, con algo de comba
        d.tubo([(x + 0.05 * math.sin(y * 3 + i), y, z(x, y)) for y in np.linspace(-1.9, 1.9, 9)], 0.028, "tendon", n=3)
    for j, y in enumerate(ys):
        d.tubo([(x, y + 0.05 * math.sin(x * 3 + j), z(x, y) + 0.03) for x in np.linspace(-1.9, 1.3, 8)], 0.028, "tendon", n=3)
    # El borde de la derecha está enrollado: espiral de red.
    for y in ys:
        d.tubo([(1.55 + 0.26 * (1 - t * 0.45) * math.cos(t * 9), y, 0.16 + 0.15 * (1 - t * 0.45) * math.sin(t * 9)) for t in np.linspace(0, 1, 12)], 0.026, "tendon", n=3)
    for k_ in range(3):
        r = 0.26 - 0.05 * k_
        d.tubo([(1.55 + r * math.cos(1.5 + k_ * 2.2), y, 0.16 + r * 0.58 * math.sin(1.5 + k_ * 2.2)) for y in np.linspace(-1.9, 1.9, 6)], 0.026, "tendon", n=3)
    # Cuerda gorda del perímetro y pesas (vértebras) en las esquinas y los lados.
    d.tubo([(-1.95, -1.95, 0.08), (-1.95, 1.95, 0.08)], 0.05, "cuero", n=5)
    d.tubo([(-1.95, -1.95, 0.08), (1.4, -1.95, 0.08)], 0.05, "cuero", n=5)
    d.tubo([(-1.95, 1.95, 0.08), (1.4, 1.95, 0.08)], 0.05, "cuero", n=5)
    for (x, y) in ((-1.95, -1.95), (-1.95, 1.95), (-1.95, 0), (-0.4, -1.95), (-0.4, 1.95), (1.4, -1.95), (1.4, 1.95)):
        d.torno([(0.05, -0.1), (0.14, -0.06), (0.1, 0.0), (0.14, 0.06), (0.05, 0.1)], (x, y, 0.1), "hueso", n=6, eje=(1, 0, 0) if abs(y) > 1.9 else (0, 1, 0))


@modelo("guerra", "mediana", (4, 4, 5), "Jaula de prisioneros hecha de costillas gigantes curvadas como barrotes.")
def jaula_prisioneros(M):
    rnd = M.rnd
    p = M.pieza("jaula", tris=5600, res=190, k=0.08, ruido=(0.025, 1.8), suelo=0.0)
    p.torno([(0, 0), (1.95, 0), (2.0, 0.2), (1.8, 0.36), (0, 0.3)], (0, 0, 0), "piedra")
    p.torno([(0, 0.3), (1.6, 0.3), (1.6, 0.4), (0, 0.4)], (0, 0, 0), "paja", k=0.03)
    n = 12
    for j in range(n):
        a = math.tau * j / n
        if j in (0, 11):   # hueco de la puerta (delante: -Y es a = -90°; se gira la numeración)
            continue
        c, s = math.cos(a - math.pi / 2 + math.pi / n), math.sin(a - math.pi / 2 + math.pi / n)
        pts = [(1.75 * c, 1.75 * s, 0.2), (2.0 * c, 2.0 * s, 1.7), (1.75 * c, 1.75 * s, 3.2), (0.9 * c, 0.9 * s, 4.2), (0.2 * c, 0.2 * s, 4.5)]
        p.tubo(pts, [0.17, 0.15, 0.13, 0.11, 0.1], "hueso" if j % 2 else "hueso_viejo", suave=10)
    # Vértebra-clave arriba y aros de tendón que atan las costillas.
    p.cilindro((0, 0, 4.3), (0, 0, 4.75), 0.42, "hueso", red=0.1)
    p.tubo([(0, 0, 4.7), (0, 0.2, 5.0)], [0.16, 0.08], "hueso", k=0.05)
    for zr, R in ((1.7, 2.0), (3.2, 1.75)):
        pts = [(R * math.cos(a), R * math.sin(a), zr) for a in np.linspace(-math.pi / 2 + 0.6, 1.5 * math.pi - 0.6, 18)]
        p.tubo(pts, 0.06, "tendon", k=0.02)
    for s in (-1, 1):  # jambas
        p.tubo([(s * 0.62, -1.75, 0.2), (s * 0.66, -1.95, 2.0), (s * 0.5, -1.6, 3.6)], [0.19, 0.16, 0.12], "hueso_viejo", suave=6)
    p.tubo([(-0.5, -1.6, 3.6), (0, -1.7, 3.75), (0.5, -1.6, 3.6)], 0.1, "hueso_viejo", k=0.03)
    d = p.duro
    for j in range(8):  # púas hacia dentro, para que nadie se apoye
        a = math.tau * j / 8 + 0.9
        b = np.array([1.9 * math.cos(a), 1.9 * math.sin(a), 2.4])
        d.cono(b, b * [0.72, 0.72, 1] + [0, 0, 0.1], 0.06, "garra", n=4)
    d.toro((0, 0, 4.05), 0.14, 0.035, "hueso_viejo", eje=(1, 0, 0), n=7, m=3)   # argolla
    d.tubo([(0, 0, 3.9), (0, 0, 3.3)], 0.025, "tendon", n=4)
    d.cuerno([(0, 0, 3.3), (0.15, 0, 3.05), (0.05, 0, 2.85), (-0.1, 0, 3.0)], 0.05, "garra", n=5, seg=5, potencia=0.5)  # gancho
    g = M.pieza("puerta", tris=1200, res=150, k=0.05, ruido=(0.02, 1.8))
    for x in (-0.36, 0.0, 0.36):
        g.tubo([(x, -1.92, 0.42), (x * 1.05, -2.0, 1.9), (x, -1.85, 3.4)], [0.1, 0.09, 0.08], "hueso")
    for zb in (0.75, 2.0, 3.2):
        g.tubo([(-0.5, -1.95, zb), (0.5, -1.95, zb)], 0.07, "hueso_viejo", k=0.02)
    g.duro.toro((0.52, -2.0, 2.0), 0.12, 0.035, "garra", eje=(0, 1, 0), n=7, m=3)   # cerrojo
    M.articulacion("puerta", "jaula", (-0.6, -1.9, 2.0))
    M.notas["animacion"] = "La puerta gira sobre la jamba izquierda (articulación «puerta»)."


@modelo("guerra", "mediana", (3, 3, 14), "Torre de vigilancia orgánica: tronco de hueso con plataforma de carne y un ojo "
        "centinela arriba que brilla.")
def torre_vigilia_organica(M):
    rnd = M.rnd
    p = M.pieza("torre", tris=6300, res=230, k=0.15, ruido=(0.04, 1.4), suelo=0.0)
    tronco = curva([(0, 0, 0), (0.2, 0.1, 3.5), (-0.15, -0.1, 7.5), (0.05, 0.05, 10.6)], 14)
    p.tubo(tronco, [0.85, 0.6, 0.5, 0.55], "hueso")
    for j in range(5):
        a = math.tau * j / 5 + 0.3
        p.tubo([(0.2 * math.cos(a), 0.2 * math.sin(a), 1.6), (0.9 * math.cos(a), 0.9 * math.sin(a), 0.6), (1.4 * math.cos(a), 1.4 * math.sin(a), 0)],
               [0.4, 0.32, 0.17], "hueso_viejo", suave=5)
    for j in range(3):  # músculos que trepan por el hueso
        pts = [(q[0] + 0.5 * math.cos(j * 2.1 + i * 0.5), q[1] + 0.5 * math.sin(j * 2.1 + i * 0.5), q[2]) for i, q in enumerate(tronco)]
        p.tubo(pts, [0.22, 0.2, 0.17, 0.2], "musculo", k=0.1)
    for i in range(9):  # peldaños: costillas cortas a un lado y a otro
        z = 1.4 + i * 1.0
        q = tronco[min(14, int(z / 10.6 * 14))]
        s = 1 if i % 2 else -1
        p.tubo([(q[0] + s * 0.3, q[1] - 0.3, z), (q[0] + s * 1.0, q[1] - 0.6, z + 0.1), (q[0] + s * 1.2, q[1] - 0.3, z + 0.3)], [0.15, 0.12, 0.06], "hueso_viejo", k=0.06)
    zp = 10.6
    p.torno([(0, -0.9), (0.6, -0.8), (1.4, -0.2), (1.5, 0.1), (1.35, 0.3), (0, 0.25)], (0.05, 0.05, zp), "carne", k=0.2)
    p.torno([(0.95, 0.2), (1.38, 0.25), (1.42, 0.62), (1.28, 0.66), (1.2, 0.36), (0.95, 0.32)], (0.05, 0.05, zp), "piel", cerrado=True, k=0.05)  # antepecho
    p.caja((0.05, -1.3, zp + 0.55), (0.9, 0.8, 0.5), None, resta=True, k=0.05)   # entrada a la plataforma
    # Ojo centinela en un tallo, con párpados.
    zo = zp + 2.5
    p.tubo([(0.05, 0.4, zp + 0.2), (0.2, 0.6, zp + 1.2), (0.05, 0.3, zo - 0.4)], [0.36, 0.26, 0.36], "musculo", suave=6, k=0.15)
    p.esfera((0.05, 0.2, zo), 0.78, "carne_viva", k=0.15)
    p.esfera((0.05, -0.35, zo), 0.62, "negro", resta=True, k=0.06)
    p.tubo([(-0.55, -0.2, zo + 0.1), (0.05, -0.55, zo + 0.52), (0.65, -0.2, zo + 0.1)], [0.08, 0.17, 0.08], "piel", suave=6, k=0.05)
    p.tubo([(-0.55, -0.2, zo - 0.1), (0.05, -0.52, zo - 0.5), (0.65, -0.2, zo - 0.1)], [0.08, 0.15, 0.08], "piel", suave=6, k=0.05)
    d = p.duro
    for j in range(6):  # membranas que cuelgan de la plataforma
        a = math.tau * j / 6 + 0.5
        c, s = math.cos(a), math.sin(a)
        L = rnd.uniform(0.9, 1.7)
        filas = [[(1.3 * math.cos(a + t) + 0.05, 1.3 * math.sin(a + t) + 0.05, zp - 0.15 - u * L * (1 - 0.6 * abs(t) / 0.3)) for t in (-0.3, 0, 0.3)] for u in (0, 0.5, 1.0)]
        d.superficie(filas, 0.05, "membrana")
    for j in range(5):  # cuernos-almena
        a = math.tau * j / 5 + 1.2
        b = np.array([1.38 * math.cos(a) + 0.05, 1.38 * math.sin(a) + 0.05, zp + 0.6])
        d.cuerno([b, b * [1.12, 1.12, 1] + [0, 0, 0.5], b * [1.0, 1.0, 1] + [0, 0, 1.1]], 0.12, "garra", n=5, seg=3)
    d.esfera((0.05, -0.33, zo), 0.09, "pupila", sub=1, esc=(0.7, 0.5, 4.0))
    o = M.pieza("ojo_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    o.duro.esfera((0.05, 0.0, zo), 0.55, "neon_violeta", sub=2)


@modelo("guerra", "prop", (2, 0.5, 6), "Estandarte de clan: poste con bandera de piel y un símbolo pintado en sangre.")
def emblema_clan(M):
    rnd = M.rnd
    p = M.pieza("estandarte", tris=700, res=200, k=0.04, ruido=(0.015, 2.5), suelo=0.0)
    p.tubo([(-0.7, 0, 0), (-0.68, 0.02, 3.0), (-0.7, 0, 5.6)], [0.13, 0.1, 0.08], "corteza")
    p.esfera((-0.7, 0, 0), 0.3, "piedra", esc=(1, 0.8, 0.5))
    p.tubo([(-0.85, 0, 5.2), (0.2, 0, 5.3), (1.0, 0, 5.2)], [0.07, 0.065, 0.05], "hueso", k=0.02)
    d = p.duro
    d.cuerno([(-0.7, 0, 5.55), (-0.75, 0, 5.85), (-0.6, 0, 6.05)], 0.08, "garra", n=5, seg=3)
    d.cuerno([(1.0, 0, 5.2), (1.15, 0, 5.3), (1.2, 0, 5.5)], 0.05, "garra", n=4, seg=2)

    def sup(u, v):   # u: 0..1 a lo ancho, v: 0..1 hacia abajo
        x = -0.5 + 1.4 * u
        yv = 0.1 * math.sin(v * 4.0 + u * 2.0) * v
        z = 5.2 - 3.1 * v * (1 - 0.1 * math.sin(u * math.pi)) - (0.45 * v * abs(u - 0.5) * 2 if v > 0.8 else 0)
        return np.array([x, yv, z])

    filas = [[sup(u, v) for v in np.linspace(0, 1, 9)] for u in np.linspace(0, 1, 6)]
    d.superficie(filas, 0.045, "cuero")
    for u in (0.1, 0.5, 0.9):   # presillas de tendón
        d.toro(sup(u, 0) + [0, 0, 0.06], 0.085, 0.022, "tendon", eje=(1, 0, 0), n=6, m=3)
    # Símbolo en relieve (pintado con los dedos): un ojo rasgado por tres zarpazos.
    for lado in (-1, 1):
        off = np.array([0, lado * 0.034, 0])
        aro = [sup(0.5 + 0.26 * math.cos(t), 0.4 + 0.11 * math.sin(t)) + off for t in np.linspace(0, math.tau, 13)]
        d.tubo(aro, 0.03, "pintura_sangre", n=4, aplastar=0.4)
        d.tubo([sup(0.5, 0.31) + off, sup(0.5, 0.49) + off], [0.035, 0.035], "pintura_sangre", n=4)
        for k_ in range(3):
            d.tubo([sup(0.2 + 0.2 * k_, 0.58) + off, sup(0.3 + 0.2 * k_, 0.86) + off], [0.035, 0.012], "pintura_sangre", n=4)
    for u in (0.0, 0.25, 0.5, 0.75, 1.0):   # dientes colgando del borde
        b = sup(u, 1.0)
        d.tubo([b, b - [0, 0, 0.14]], 0.01, "tendon", n=3)
        d.cono(b - [0, 0, 0.14], b - [0, 0, 0.36], 0.035, "diente", n=4)


@modelo("guerra", "prop", (3, 3, 3), "Tambor de guerra ceremonial: piel estirada sobre un casco de costillas.")
def tambor_guerra(M):
    p = M.pieza("tambor", tris=1250, res=170, k=0.06, ruido=(0.02, 1.8), suelo=0.0)
    M.mat("parche", "cuero", a="#9A6A4A", b="#5A3A2E", rug=0.5)
    p.torno([(0, 0.75), (0.95, 0.75), (1.2, 1.3), (1.3, 1.9), (1.22, 2.3), (0, 2.3)], (0, 0, 0), "cuero")
    p.torno([(0, 2.26), (1.2, 2.3), (1.24, 2.4), (0.6, 2.47), (0, 2.5)], (0, 0, 0), "parche", k=0.02)
    p.toro((0, 0, 2.34), 1.25, 0.08, "tendon", k=0.02)
    n = 10
    for j in range(n):   # costillas del casco
        a = math.tau * j / n
        c, s = math.cos(a), math.sin(a)
        p.tubo([(0.9 * c, 0.9 * s, 0.7), (1.27 * c, 1.27 * s, 1.35), (1.38 * c, 1.38 * s, 1.95), (1.28 * c, 1.28 * s, 2.42)], [0.1, 0.09, 0.08, 0.07], "hueso", k=0.03)
    for j in range(3):   # patas
        a = math.tau * j / 3 + 0.5
        c, s = math.cos(a), math.sin(a)
        p.tubo([(0.8 * c, 0.8 * s, 1.0), (1.2 * c, 1.2 * s, 0.5), (1.38 * c, 1.38 * s, 0)], [0.16, 0.13, 0.15], "hueso_viejo", k=0.05)
    d = p.duro
    for j in range(n):   # cordaje en zigzag
        a0, a1 = math.tau * j / n, math.tau * (j + 0.5) / n
        a2 = math.tau * (j + 1) / n
        d.tubo([(1.3 * math.cos(a0), 1.3 * math.sin(a0), 2.3), (1.17 * math.cos(a1), 1.17 * math.sin(a1), 1.05), (1.3 * math.cos(a2), 1.3 * math.sin(a2), 2.3)], 0.022, "tendon", n=3)
    b = M.pieza("baquetas", tris=420, res=110, k=0.03, unir="tambor")
    hueso_largo(b, (-0.7, -0.35, 2.58), (0.75, -0.1, 2.56), 0.065)
    hueso_largo(b, (-0.3, 0.55, 2.56), (0.8, 0.42, 2.72), 0.06, mat="hueso_viejo")


@modelo("guerra", "prop", (3, 3, 2), "Hoguera comunitaria de fuego verde y púrpura, rodeada de piedras y huesos.")
def hoguera_clan(M):
    rnd = M.rnd
    p = M.pieza("hoguera", tris=1050, res=160, k=0.08, ruido=(0.035, 1.8), suelo=0.0)
    for j in range(10):
        a = math.tau * j / 10
        p.esfera((1.2 * math.cos(a), 1.2 * math.sin(a), 0.1), rnd.uniform(0.24, 0.34), "piedra", esc=(1, 1, 0.8))
    p.esfera((0, 0, -0.05), 1, "tierra", esc=(1.1, 1.1, 0.2))
    for j in range(5):   # leños-hueso carbonizados en tipi
        a = math.tau * j / 5 + 0.2
        p.tubo([(0.85 * math.cos(a), 0.85 * math.sin(a), 0.05), (0.1 * math.cos(a + 2.5), 0.1 * math.sin(a + 2.5), 0.95)], [0.12, 0.08], "corteza" if j % 2 else "hueso_viejo", k=0.03)
    d = p.duro
    for j in range(3):
        a = 0.8 + j * 2.1
        d.cuerno([(1.45 * math.cos(a), 1.45 * math.sin(a), 0.05), (1.3 * math.cos(a + 0.3), 1.3 * math.sin(a + 0.3), 0.3), (1.5 * math.cos(a + 0.6), 1.5 * math.sin(a + 0.6), 0.1)], 0.07, "hueso", n=5, seg=3, potencia=0.5)
    M.mat("llama_v", "fuego_violeta", a="#7A1EC8", b="#B040F0", emis=(VIOLETA, 0.85))
    f = M.pieza("fuego_neon", tris=620, res=150, k=0.05, ruido=(0.025, 3.0), roblox=dict(material="Neon", color=VERDE, transparencia=0.15))
    f.esfera((0, 0, 0.45), 0.36, "fuego_verde", esc=(1.2, 1.2, 0.8), k=0.12)
    lenguas = [((0, 0, 0.5), (0.14, 0.05, 1.2), (-0.1, 0, 1.95), "fuego_verde", 0.26), ((0.3, -0.12, 0.4), (0.55, -0.26, 0.95), (0.4, -0.15, 1.5), "llama_v", 0.2),
               ((-0.3, 0.18, 0.4), (-0.56, 0.32, 0.9), (-0.4, 0.26, 1.4), "llama_v", 0.19), ((0.0, 0.36, 0.4), (0.08, 0.6, 0.85), (0.0, 0.45, 1.25), "fuego_verde", 0.17),
               ((-0.1, -0.36, 0.4), (-0.2, -0.56, 0.8), (-0.12, -0.45, 1.1), "llama_v", 0.15)]
    for a, b, c, mat, r in lenguas:
        f.tubo([a, b, c], [r, r * 0.85, 0.04], mat, suave=6)
    b = M.pieza("brasas_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    for j in range(9):
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.15, 0.8)
        b.duro.esfera((r * math.cos(a), r * math.sin(a), 0.14), rnd.uniform(0.06, 0.11), "neon_violeta", sub=1, esc=(1, 1, 0.6))


@modelo("guerra", "prop", (3, 2, 2), "Mesa de estrategia: mapa tallado en hueso, con marcas y fichas de piedra.")
def mesa_estrategia(M):
    rnd = M.rnd
    p = M.pieza("mesa", tris=1300, res=180, k=0.05, ruido=(0.018, 2.2), suelo=0.0)
    borde = [(1.45 * math.cos(a) * (1 + 0.08 * math.sin(3 * a)), 0.95 * math.sin(a) * (1 + 0.1 * math.cos(2 * a))) for a in np.linspace(0, math.tau, 15)[:-1]]
    p.extrusion(borde, 0.24, (0, 0, 1.5), "hueso", red=0.07)       # tablero: una escápula enorme
    for sx, sy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        p.tubo([(sx * 0.95, sy * 0.55, 1.45), (sx * 1.05, sy * 0.62, 0.7), (sx * 1.15, sy * 0.7, 0)], [0.14, 0.1, 0.13], "hueso_viejo", k=0.04)
    p.tubo([(-1.0, 0, 0.6), (1.0, 0, 0.6)], 0.07, "hueso_viejo", k=0.03)
    zt = 1.62
    # Mapa tallado: costa, río y dos fronteras.
    p.tubo([(-1.2, -0.3, zt), (-0.6, 0.1, zt), (-0.2, -0.25, zt), (0.4, 0.2, zt), (1.15, -0.1, zt)], 0.035, None, resta=True, suave=12)
    p.tubo([(-0.3, 0.75, zt), (-0.1, 0.3, zt), (-0.2, -0.25, zt), (0.1, -0.75, zt)], 0.028, None, resta=True, suave=8)
    p.toro((0.75, 0.42, zt), 0.26, 0.028, None, resta=True)
    p.toro((-0.85, -0.48, zt), 0.2, 0.028, None, resta=True)
    d = p.duro
    for (x, y, tipo) in ((0.75, 0.42, 0), (-0.85, -0.48, 1), (0.2, -0.3, 2), (-0.45, 0.4, 0), (1.0, -0.35, 1), (0.45, 0.6, 2), (-1.05, 0.15, 2)):
        if tipo == 0:    # fichas: menhir, colmillo y canto
            d.prisma((x, y, zt), (x, y, zt + 0.3), 0.07, "obsidiana", n=5, punta=0.4)
        elif tipo == 1:
            d.cuerno([(x, y, zt), (x + 0.03, y, zt + 0.14), (x, y, zt + 0.28)], 0.055, "diente", n=5, seg=2)
        else:
            d.esfera((x, y, zt + 0.045), 0.08, "piedra", sub=1, esc=(1, 1, 0.55))
    d.prisma((-0.2, -0.25, zt + 0.45), (-0.2, -0.25, zt - 0.05), 0.035, "garra", n=4, punta=0.6)   # puñal clavado en el cruce
    d.tubo([(-0.2, -0.25, zt + 0.45), (-0.2, -0.25, zt + 0.68)], 0.035, "cuero", n=5)
    d.tubo([(-0.32, -0.25, zt + 0.46), (-0.08, -0.25, zt + 0.46)], 0.022, "hueso", n=4)


@modelo("guerra", "grande", (10, 10, 4), "Corral para bestias domesticadas: cercado de hueso y espinas, con el suelo de "
        "paja y carne.")
def corral_bestias(M):
    rnd = M.rnd
    p = M.pieza("corral", tris=9300, res=200, k=0.1, ruido=(0.04, 1.2), suelo=0.0)
    p.torno([(0, 0), (4.9, 0), (4.8, 0.16), (0, 0.22)], (0, 0, 0), "paja")
    for j in range(7):   # montones de paja y restos de carne
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.5, 3.6)
        p.esfera((r * math.cos(a), r * math.sin(a), 0.2), rnd.uniform(0.5, 0.9), "paja" if j % 3 else "carne", esc=(1, 1, 0.36), k=0.2)
    n = 18
    postes = []
    for j in range(n):
        a = math.tau * (j + 0.5) / n - math.pi / 2
        puerta = j in (0, n - 1)
        R = 4.7
        alto = 3.6 if puerta else rnd.uniform(2.3, 2.9)
        c, s = math.cos(a), math.sin(a)
        postes.append((a, alto, puerta))
        p.tubo([(R * c, R * s, 0), (R * 1.01 * c, R * 1.01 * s, alto * 0.5), (R * 0.98 * c, R * 0.98 * s, alto)], [0.3 if puerta else 0.22, 0.2, 0.15], "hueso_viejo" if j % 2 else "hueso", suave=5)
        p.esfera((R * c, R * s, 0.1), 0.42, "tierra", esc=(1, 1, 0.6))
    for j in range(n):   # travesaños: costillas entre poste y poste (menos en la puerta)
        a0, h0, _ = postes[j]
        a1, h1, _ = postes[(j + 1) % n]
        if j == n - 1:
            continue
        for z in (0.9, 1.75):
            am = (a0 + a1) / 2 if j < n - 1 else a0 + math.pi / n
            p.tubo([(4.7 * math.cos(a0), 4.7 * math.sin(a0), z), (4.85 * math.cos(a0 + math.pi / n), 4.85 * math.sin(a0 + math.pi / n), z + 0.14),
                    (4.7 * math.cos(a0 + math.tau / n), 4.7 * math.sin(a0 + math.tau / n), z)], 0.12, "hueso", k=0.05)
    d = p.duro
    for a, alto, puerta in postes:   # espinas en cada poste y ataduras
        b = np.array([4.62 * math.cos(a), 4.62 * math.sin(a), alto])
        d.cuerno([b, b * [1.04, 1.04, 1] + [0, 0, 0.5], b * [1.1, 1.1, 1] + [0, 0, 1.0 if not puerta else 0.5]], 0.14, "garra", n=5, seg=3)
        fuera = np.array([math.cos(a), math.sin(a), 0])
        d.cono(b * [1.0, 1.0, 0] + [0, 0, 1.3] + fuera * 0.15, b * [1.0, 1.0, 0] + [0, 0, 1.5] + fuera * 0.85, 0.08, "garra", n=4)
        for z in (0.9, 1.75):
            d.toro((4.7 * math.cos(a), 4.7 * math.sin(a), z), 0.25, 0.04, "tendon", n=6, m=3)
    # Comedero: medio hueso hueco con carne, y abrevadero de ácido.
    p.capsula((-2.6, 2.2, 0.5), (-0.9, 3.2, 0.5), 0.5, "hueso", k=0.05)
    p.capsula((-2.6, 2.2, 0.72), (-0.9, 3.2, 0.72), 0.4, "carne_viva", resta=True, k=0.05)
    for t in (0.2, 0.5, 0.8):
        p.esfera((-2.6 + 1.7 * t, 2.2 + 1.0 * t, 0.5), 0.28, "carne_viva", k=0.05)
    p.torno([(0, 0), (0.9, 0), (1.0, 0.5), (0.8, 0.55), (0.7, 0.2), (0, 0.15)], (2.6, 2.4, 0.15), "piedra")
    ag = M.pieza("abrevadero_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    ag.duro.torno([(0, 0.3), (0.72, 0.3), (0.72, 0.52), (0, 0.55)], (2.6, 2.4, 0.15), "acido", n=10)
    cr = M.pieza("craneo_puerta", tris=900, res=90, unir="corral")
    a0 = postes[0][0]
    with cr.en((4.6 * math.cos(a0), 4.6 * math.sin(a0) - 0.25, 2.5), rot=(10, 0, 12), esc=0.8):
        craneo(cr, rnd, mat="hueso", cuernos=2, largo=1.3)
    # Hoja de la puerta: reja de costillas con bisagra.
    g = M.pieza("puerta", tris=1300, res=130, k=0.05, ruido=(0.02, 1.6))
    a1 = postes[-1][0]
    A = np.array([4.7 * math.cos(a1), 4.7 * math.sin(a1), 0])
    B = np.array([4.7 * math.cos(a0), 4.7 * math.sin(a0), 0])
    for z in (0.6, 1.4, 2.2):
        g.tubo([A * 0.99 + [0, 0, z], (A + B) / 2 * 1.01 + [0, 0, z + 0.1], B * 0.99 + [0.0, 0, z] + (A - B) * 0.08], 0.11, "hueso_viejo", k=0.03)
    for t in (0.25, 0.5, 0.75):
        q = A + (B - A) * t * 0.92
        g.tubo([q + [0, 0, 0.35], q * 1.01 + [0, 0, 1.5], q + [0, 0, 2.5]], [0.09, 0.085, 0.05], "hueso", k=0.03)
        g.duro.cono(q + [0, 0, 2.5], q + [0, -0.1, 3.0], 0.06, "garra", n=4)
    M.articulacion("puerta", "corral", tuple(A + [0, 0, 1.4]))
    M.notas["animacion"] = "La hoja de la puerta gira sobre el poste izquierdo (articulación «puerta»)."
