"""Ronda 4: vegetación alienígena (31-40)."""

import math

import numpy as np

from lib import VERDE, VIOLETA, curva, modelo


def _flor(d, c, eje, r, mat_petalo, mat_centro, n=5, fase=0.0):
    """Flor de pétalos con grosor (láminas abombadas) alrededor de un botón."""
    eje = np.asarray(eje, float) / np.linalg.norm(eje)
    u = np.cross(eje, [0, 0, 1.0])
    if np.linalg.norm(u) < 0.2:
        u = np.cross(eje, [1.0, 0, 0])
    u /= np.linalg.norm(u)
    v = np.cross(eje, u)
    c = np.asarray(c, float)
    for i in range(n):
        a = fase + math.tau * i / n
        rad = u * math.cos(a) + v * math.sin(a)
        tan = np.cross(eje, rad)
        cont = [c + rad * r * 0.15 - tan * r * 0.1, c + rad * r * 0.6 - tan * r * 0.3 + eje * r * 0.12, c + rad * r + eje * r * 0.3,
                c + rad * r * 0.6 + tan * r * 0.3 + eje * r * 0.12, c + rad * r * 0.15 + tan * r * 0.1]
        d.lamina(cont, r * 0.09, mat_petalo, bombeo=r * 0.06)
    d.esfera(c + eje * r * 0.08, r * 0.24, mat_centro, sub=1)


@modelo("vegetacion", "vegetacion", (1, 1, 6), "Enredadera venenosa que cuelga: tallos con espinas y flores púrpura.",
        ancla="techo")
def enredadera_venenosa(M):
    rnd = M.rnd
    M.mat("petalo", "membrana", a="#8A2FC0", b="#4A1470", rug=0.45)
    M.mat("tallo", "raiz", a="#243A22", b="#1A1024")
    p = M.pieza("enredadera", tris=1700, res=240, k=0.04, ruido=(0.012, 3.0))
    hebras = []
    for j in range(3):
        pts = []
        for z in np.linspace(6, 0.2 + j * 0.9, 16):
            a = z * 1.5 + j * 2.1
            r = 0.2 + 0.1 * math.sin(z * 0.9 + j)
            pts.append((r * math.cos(a), r * math.sin(a), z))
        hebras.append(pts)
        p.tubo(pts, [0.1, 0.085, 0.07, 0.05, 0.025], "tallo")
    p.esfera((0, 0, 5.95), 0.3, "tallo", esc=(1, 1, 0.45))
    d = p.duro
    for pts in hebras:
        for i in range(1, 15):
            x, y, z = pts[i]
            fuera = np.array([x, y, 0]) / max(0.05, math.hypot(x, y))
            d.cono((x, y, z), (x + fuera[0] * 0.22, y + fuera[1] * 0.22, z - 0.1), 0.035, "garra", n=4)
    for j in range(7):  # flores y capullos
        pts = hebras[j % 3]
        x, y, z = pts[2 + (j * 5) % 12]
        fuera = np.array([x, y, 0]) / max(0.05, math.hypot(x, y))
        c = np.array([x, y, z]) + fuera * 0.2 + [0, 0, -0.08]
        d.tubo([(x, y, z), c], 0.022, "tallo", n=4)
        _flor(d, c, fuera + [0, 0, -0.35], rnd.uniform(0.17, 0.24), "petalo", "neon_verde", n=5, fase=j)
    for j in range(5):  # hojas-daga
        pts = hebras[(j + 1) % 3]
        x, y, z = pts[3 + (j * 4) % 11]
        fuera = np.array([x, y, 0]) / max(0.05, math.hypot(x, y))
        b = np.array([x, y, z])
        lado = np.cross(fuera, [0, 0, 1.0])
        d.lamina([b, b + fuera * 0.18 + lado * 0.09 - [0, 0, 0.1], b + fuera * 0.42 - [0, 0, 0.36], b + fuera * 0.18 - lado * 0.09 - [0, 0, 0.1]],
                 0.025, "tallo", bombeo=0.02)


@modelo("vegetacion", "vegetacion", (4, 4, 0.2), "Placa de musgo bioluminiscente que brilla en verde tenue.")
def musgo_luminoso(M):
    rnd = M.rnd
    p = M.pieza("musgo", tris=3200, res=260, k=0.09, ruido=(0.035, 2.5), suelo=0.0)
    for j in range(46):  # mancha irregular hecha de almohadillas
        a, r = rnd.uniform(0, math.tau), 1.75 * math.sqrt(rnd.random())
        r *= 1 + 0.18 * math.sin(3 * a + 1)
        s = rnd.uniform(0.3, 0.55)
        p.esfera((r * math.cos(a), r * math.sin(a), 0.0), s, "musgo", esc=(1, 1, rnd.uniform(0.3, 0.42)))
    p.esfera((0, 0, -0.05), 1, "musgo", esc=(1.6, 1.5, 0.14))
    n = M.pieza("brotes_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    for j in range(26):  # brotes: tallito con cápsula de luz
        a, r = rnd.uniform(0, math.tau), 1.6 * math.sqrt(rnd.random())
        x, y = r * math.cos(a), r * math.sin(a)
        h = rnd.uniform(0.1, 0.19)
        n.duro.tubo([(x, y, 0.05), (x + rnd.uniform(-0.02, 0.02), y, h)], 0.012, "neon_verde", n=3)
        n.duro.esfera((x, y, h), rnd.uniform(0.022, 0.04), "neon_verde", sub=1)


@modelo("vegetacion", "prop", (0.5, 0.5, 1), "Flor roja como una gota de sangre: pétalos carnosos y un centro que gotea.")
def flor_sangre(M):
    M.mat("petalo", "carne_viva", a="#B01422", b="#5A0612", rug=0.3)
    M.mat("tallo", "raiz", a="#3A1420", b="#1C0C14")
    p = M.pieza("flor", tris=1600, res=170, k=0.02, ruido=(0.004, 9.0), suelo=0.0)
    p.tubo(curva([(0, 0, 0), (0.03, 0.02, 0.3), (-0.02, 0.0, 0.58), (0.0, -0.02, 0.72)], 8), [0.045, 0.03, 0.028, 0.04], "tallo")
    p.esfera((0, 0, 0), 0.07, "tallo", esc=(1, 1, 0.5))
    for j in range(5):  # pétalos carnosos en forma de lágrima, abiertos hacia arriba
        a = math.tau * j / 5
        c, s = math.cos(a), math.sin(a)
        p.tubo([(0.03 * c, 0.03 * s - 0.02, 0.72), (0.15 * c, 0.15 * s - 0.02, 0.8), (0.2 * c, 0.2 * s - 0.02, 0.93), (0.13 * c, 0.13 * s - 0.02, 1.0)],
               [0.04, 0.085, 0.07, 0.02], "petalo", k=0.015)
    for j in range(3):  # sépalos
        a = math.tau * j / 3 + 0.5
        p.tubo([(0, -0.02, 0.7), (0.1 * math.cos(a), 0.1 * math.sin(a), 0.64), (0.14 * math.cos(a), 0.14 * math.sin(a), 0.54)], [0.03, 0.025, 0.008], "tallo", k=0.01)
    for j in range(2):  # hojas
        a = 1.0 + j * 2.6
        p.esfera((0.1 * math.cos(a), 0.1 * math.sin(a), 0.22 + 0.12 * j), 1, "tallo", esc=(0.11, 0.05, 0.025), rot=(0, -25, math.degrees(a)), k=0.01)
    g = M.pieza("gota_neon", tris=0, roblox=dict(material="Neon", color="#FF2A4A"))
    g.duro.esfera((0, -0.02, 0.84), 0.07, "sangre_neon", sub=2)
    g.duro.torno([(0, -0.1), (0.035, -0.07), (0.03, -0.03), (0.01, 0.03), (0, 0.06)], (0.2, 0.0, 0.76), "sangre_neon", n=6)
    g.duro.tubo([(0.2, 0.0, 0.82), (0.2, 0.0, 0.93)], 0.008, "sangre_neon", n=3)


@modelo("vegetacion", "prop", (1, 1, 1), "Flor que parece un ojo: el centro es una pupila que mira y los pétalos, párpados.")
def flor_ojo(M):
    M.mat("parpado", "membrana", a="#6A2A5A", b="#2E1232")
    M.mat("tallo", "raiz", a="#2A3A22", b="#1A1024")
    M.mat("iris", "neon_verde", a="#0E5A1E", b="#39FF14", emis=(VERDE, 0.6))
    p = M.pieza("flor", tris=1450, res=170, k=0.03, ruido=(0.008, 6.0), suelo=0.0)
    p.tubo(curva([(0, 0.2, 0), (0.05, 0.28, 0.25), (0, 0.2, 0.45), (0, 0.08, 0.56)], 6), [0.07, 0.05, 0.05, 0.08], "tallo")
    p.esfera((0, 0.2, 0), 0.12, "tallo", esc=(1, 1, 0.5))
    c = np.array([0, -0.02, 0.66])
    p.esfera(c + [0, 0.05, 0], 0.27, "parpado")                       # cuenca
    p.esfera(c + [0, -0.12, 0], 0.22, "carne_viva", resta=True, k=0.02)
    # Párpados: dos pétalos gruesos, arriba y abajo.
    p.tubo([c + [-0.3, -0.05, 0.02], c + [0, -0.26, 0.2], c + [0.3, -0.05, 0.02]], [0.03, 0.075, 0.03], "parpado", suave=6, k=0.02)
    p.tubo([c + [-0.3, -0.05, -0.02], c + [0, -0.24, -0.19], c + [0.3, -0.05, -0.02]], [0.03, 0.065, 0.03], "parpado", suave=6, k=0.02)
    d = p.duro
    for j in range(9):  # pétalos-pestaña alrededor
        a = math.tau * j / 9 + 0.2
        r = np.array([math.cos(a), 0, math.sin(a)])
        b = c + r * 0.24 + [0, 0.04, 0]
        t = np.array([-math.sin(a), 0, math.cos(a)])
        d.lamina([b - t * 0.06, b + r * 0.14 - t * 0.07 + [0, -0.06, 0], b + r * 0.26 + [0, -0.14, 0], b + r * 0.14 + t * 0.07 + [0, -0.06, 0], b + t * 0.06],
                 0.03, "parpado", bombeo=0.02)
    for j in range(2):
        a = 0.6 + j * 2.9
        b = np.array([0.03, 0.26, 0.2 + 0.1 * j])
        r = np.array([math.cos(a), math.sin(a), 0])
        t = np.array([-math.sin(a), math.cos(a), 0])
        d.lamina([b, b + r * 0.15 + t * 0.07, b + r * 0.36 + [0, 0, 0.08], b + r * 0.15 - t * 0.07], 0.025, "tallo", bombeo=0.02)
    o = M.pieza("ojo", tris=0)
    o.duro.esfera(c + [0, -0.06, 0], 0.2, "ojo", sub=2)
    o.duro.esfera(c + [0, -0.215, 0], 0.085, "iris", sub=1, esc=(1, 0.42, 1))
    o.duro.esfera(c + [0, -0.245, 0], 0.03, "pupila", sub=1, esc=(0.6, 0.5, 2.3))


@modelo("vegetacion", "vegetacion", (3, 3, 3), "Grupo de esporas que flotan en el aire: esferas translúcidas con un "
        "núcleo verde que brilla.", ancla="centro")
def esporas_flotantes(M):
    rnd = M.rnd
    M.mat("velo", "mucosa", a="#6AD08A", b="#2A6A4A", rug=0.15, emis=(VERDE, 0.15))
    v = M.pieza("velos_cristal", tris=0, roblox=dict(material="Glass", color="#7AE09A", transparencia=0.6))
    n = M.pieza("nucleos_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    usados = []
    while len(usados) < 9:
        c = np.array([rnd.uniform(-1.1, 1.1), rnd.uniform(-1.1, 1.1), rnd.uniform(-1.1, 1.1)])
        r = rnd.uniform(0.2, 0.42)
        if all(np.linalg.norm(c - c2) > r + r2 + 0.12 for c2, r2 in usados):
            usados.append((c, r))
    for c, r in usados:
        v.duro.esfera(c, r, "velo", sub=2, esc=(1, 1, rnd.uniform(0.9, 1.15)))
        n.duro.esfera(c, r * 0.45, "neon_verde", sub=1)
        for j in range(5):  # filamentos: pelos con una gotita en la punta
            dire = np.array([rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 0.6)])
            dire /= np.linalg.norm(dire)
            fin = c + dire * r * rnd.uniform(1.5, 2.0)
            v.duro.tubo([c + dire * r * 0.9, fin], [0.022, 0.008], "velo", n=3)
            n.duro.esfera(fin, 0.028, "neon_verde", sub=1)


@modelo("vegetacion", "vegetacion", (6, 4, 1), "Raíces gruesas que salen del suelo y vuelven a entrar, como las venas "
        "del planeta.")
def raiz_superficial(M):
    rnd = M.rnd
    p = M.pieza("raices", tris=3900, res=250, k=0.06, ruido=(0.025, 2.0), suelo=0.0)
    # Raíz madre que cruza a lo largo, haciendo arcos.
    p.tubo(curva([(-3.0, -0.4, -0.2), (-1.8, 0.2, 0.62), (-0.6, -0.3, 0.2), (0.6, 0.3, 0.75), (1.9, -0.1, 0.25), (3.0, 0.4, -0.2)], 22),
           [0.2, 0.27, 0.25, 0.29, 0.24, 0.17], "raiz")
    ramas = [((-1.8, 0.2, 0.5), (-1.5, 1.3, 0.35), (-0.6, 1.95, -0.1), 0.17), ((0.6, 0.3, 0.6), (1.0, 1.4, 0.42), (2.0, 1.9, -0.1), 0.17),
             ((-0.6, -0.3, 0.2), (-0.9, -1.3, 0.4), (-2.0, -1.9, -0.1), 0.16), ((1.9, -0.1, 0.25), (1.6, -1.2, 0.36), (0.5, -1.95, -0.1), 0.16),
             ((-1.5, 1.3, 0.3), (-2.4, 1.2, 0.25), (-2.95, 1.7, -0.1), 0.1), ((1.6, -1.2, 0.3), (2.4, -1.4, 0.25), (2.9, -1.0, -0.1), 0.1),
             ((1.0, 1.4, 0.4), (0.2, 1.5, 0.3), (-0.2, 1.1, -0.05), 0.09), ((-0.9, -1.3, 0.35), (0.0, -1.2, 0.26), (0.3, -0.8, -0.05), 0.09)]
    for a, b, c, r in ramas:
        p.tubo(curva([a, b, c], 10), [r, r * 0.9, r * 0.55], "raiz")
    for (x, y, z, r) in ((-1.8, 0.2, 0.62, 0.32), (0.6, 0.3, 0.75, 0.34), (1.0, 1.4, 0.42, 0.2), (-0.9, -1.3, 0.4, 0.19)):  # nudos
        p.esfera((x, y, z), r, "raiz", k=0.1)
    M.mat("vena", "carne_viva", a="#8A1E3A", b="#4A0E2A")
    for j in range(4):  # venas finas enrolladas en la raíz madre
        x0 = -2.4 + j * 1.4
        p.tubo([(x0, -0.36, 0.05), (x0 + 0.3, 0.0, 0.72), (x0 + 0.6, 0.36, 0.1)], 0.05, "vena", suave=6, k=0.03)


@modelo("vegetacion", "vegetacion", (8, 8, 0.6), "Placa de suelo: no es césped, es carne y membrana púrpura con bultos "
        "y venas.")
def cesped_alien_monstruo(M):
    rnd = M.rnd
    M.mat("membrana_suelo", "membrana", a="#5A2A6A", b="#2A1238", rug=0.5)
    p = M.pieza("placa", tris=3900, res=250, k=0.18, ruido=(0.035, 1.4), suelo=0.0)
    p.caja((0, 0, 0.12), (8.0, 8.0, 0.36), "membrana_suelo", red=0.05, k=0.0)
    for j in range(34):  # bultos y ampollas
        x, y = rnd.uniform(-3.6, 3.6), rnd.uniform(-3.6, 3.6)
        r = rnd.uniform(0.3, 0.75)
        p.esfera((x, y, 0.22), r, "carne" if j % 3 else "carne_viva", esc=(1, 1, rnd.uniform(0.3, 0.5)))
    for j in range(7):  # venas gordas que serpentean por encima
        x, y = rnd.uniform(-3.5, 3.5), rnd.uniform(-3.5, 3.5)
        a = rnd.uniform(0, math.tau)
        pts = []
        for i in range(6):
            pts.append((max(-3.8, min(3.8, x)), max(-3.8, min(3.8, y)), 0.3))
            a += rnd.uniform(-0.8, 0.8)
            x += 1.0 * math.cos(a)
            y += 1.0 * math.sin(a)
        p.tubo(pts, [0.07, 0.13, 0.14, 0.12, 0.1, 0.05], "carne_viva", suave=14, k=0.08)
    d = p.duro
    for j in range(40):  # cilios: pelos gruesos de carne
        x, y = rnd.uniform(-3.7, 3.7), rnd.uniform(-3.7, 3.7)
        h = rnd.uniform(0.2, 0.36)
        d.cuerno([(x, y, 0.25), (x + rnd.uniform(-0.05, 0.05), y, 0.25 + h * 0.6), (x + rnd.uniform(-0.12, 0.12), y + rnd.uniform(-0.12, 0.12), 0.25 + h)],
                 0.04, "carne_palida", n=4, seg=2)


@modelo("vegetacion", "prop", (0.5, 0.5, 8), "Liana colgante: tallo orgánico con pequeñas flores tóxicas.", ancla="techo")
def liana_colgante(M):
    rnd = M.rnd
    M.mat("tallo", "raiz", a="#2A3A1E", b="#1A1420")
    M.mat("petalo", "hongo_verde", a="#9AD01E", b="#3A6A12")
    p = M.pieza("liana", tris=1100, res=300, k=0.03, ruido=(0.008, 4.0))
    pts = [(0.1 * math.sin(z * 1.3), 0.1 * math.cos(z * 1.7), z) for z in np.linspace(8, 0.1, 22)]
    p.tubo(pts, [0.075, 0.06, 0.055, 0.05, 0.04, 0.02], "tallo")
    p.tubo([(0.1 * math.sin(z * 1.3) + 0.07 * math.cos(z * 4), 0.1 * math.cos(z * 1.7) + 0.07 * math.sin(z * 4), z) for z in np.linspace(7.9, 2.5, 30)], 0.03, "tallo", k=0.01)
    for z in (7.95, 5.6, 3.3):
        p.esfera((0.1 * math.sin(z * 1.3), 0.1 * math.cos(z * 1.7), z), 0.1, "tallo", k=0.03)
    d = p.duro
    for j in range(8):
        z = 7.2 - j * 0.85
        a = j * 2.4
        b = np.array([0.1 * math.sin(z * 1.3), 0.1 * math.cos(z * 1.7), z])
        fuera = np.array([math.cos(a), math.sin(a), -0.3])
        c = b + fuera * 0.13
        d.tubo([b, c], 0.012, "tallo", n=3)
        _flor(d, c, fuera, 0.075, "petalo", "neon_verde", n=4, fase=j)
    for j in range(4):  # zarcillos
        z = 6.5 - j * 1.6
        b = np.array([0.1 * math.sin(z * 1.3), 0.1 * math.cos(z * 1.7), z])
        a = j * 1.9 + 1
        d.tubo([b, b + [0.14 * math.cos(a), 0.14 * math.sin(a), -0.15], b + [0.18 * math.cos(a + 0.8), 0.18 * math.sin(a + 0.8), -0.4],
                b + [0.08 * math.cos(a + 1.6), 0.08 * math.sin(a + 1.6), -0.5]], [0.016, 0.013, 0.01, 0.0], "tallo", n=3, suave=6)


@modelo("vegetacion", "vegetacion", (2, 2, 5), "Cactus alienígena negro y púrpura con espinas enormes y afiladas.")
def cactus_espina(M):
    rnd = M.rnd
    M.mat("cactus", "piel_purpura", a="#2A1640", b="#0E0A16", rug=0.5)
    p = M.pieza("cactus", tris=2500, res=190, k=0.07, ruido=(0.02, 2.0), suelo=0.0)
    d = p.duro

    def columna(base, punta, r, gajos=7):
        base, punta = np.array(base, float), np.array(punta, float)
        eje = (punta - base) / np.linalg.norm(punta - base)
        u = np.cross(eje, [0, 1.0, 0])
        u /= np.linalg.norm(u)
        v = np.cross(eje, u)
        p.tubo([base, (base + punta) / 2, punta], [r * 0.8, r * 0.9, r * 0.7], "cactus")
        for j in range(gajos):
            a = math.tau * j / gajos
            rad = u * math.cos(a) + v * math.sin(a)
            p.tubo([base + rad * r * 0.62, (base + punta) / 2 + rad * r * 0.75, punta + rad * r * 0.4 - eje * r * 0.2], [r * 0.34, r * 0.38, r * 0.26], "cactus", k=0.03)
            for t in (0.2, 0.5, 0.8):  # espinas en racimos de tres sobre cada costilla
                q = base + (punta - base) * t + rad * r * (0.95 + 0.1 * math.sin(t * 3))
                L = r * rnd.uniform(0.9, 1.4)
                d.cono(q, q + rad * L + eje * L * 0.25, r * 0.07, "garra", n=4)
                if rnd.random() < 0.45:
                    lado = np.cross(eje, rad)
                    d.cono(q, q + (rad * 0.7 + lado * 0.6) * L * 0.6, r * 0.05, "garra", n=3)

    columna((0, 0, 0), (0.05, 0, 3.9), 0.5)
    p.tubo([(0.3, 0, 1.6), (0.85, 0.05, 1.7), (0.95, 0.05, 2.1)], [0.26, 0.26, 0.26], "cactus")
    columna((0.95, 0.05, 2.0), (1.0, 0.1, 3.3), 0.26, gajos=5)
    p.tubo([(-0.3, 0.1, 2.3), (-0.75, 0.2, 2.45), (-0.8, 0.2, 2.8)], [0.22, 0.22, 0.22], "cactus")
    columna((-0.8, 0.2, 2.7), (-0.85, 0.25, 3.7), 0.22, gajos=5)
    n = M.pieza("flor_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    n.duro.esfera((0.05, 0, 4.25), 0.2, "neon_violeta", sub=1, esc=(1, 1, 0.8))
    for j in range(6):
        a = math.tau * j / 6
        d.cono((0.05 + 0.15 * math.cos(a), 0.15 * math.sin(a), 4.1), (0.05 + 0.42 * math.cos(a), 0.42 * math.sin(a), 4.75), 0.06, "garra", n=4)


@modelo("vegetacion", "vegetacion", (4, 4, 0.5), "Charco de pantano que burbujea: superficie verde oscura con burbujas "
        "en 3D.")
def pantano_burbuja(M):
    rnd = M.rnd
    M.mat("cieno", "mucosa", a="#2E5A1A", b="#122A12", rug=0.12, emis=(VERDE, 0.05))
    M.mat("barro", "tierra", a="#1E1A14", b="#2E2A1E", rug=0.6)
    p = M.pieza("pantano", tris=3600, res=250, k=0.1, ruido=(0.02, 2.0), suelo=0.0)
    for j in range(14):  # orilla de barro
        a = math.tau * j / 14
        r = 1.7 + 0.15 * math.sin(3 * a)
        p.esfera((r * math.cos(a), r * math.sin(a), 0.0), rnd.uniform(0.3, 0.42), "barro", esc=(1.2, 1.2, 0.5))
    p.esfera((0, 0, -0.02), 1, "cieno", esc=(1.75, 1.75, 0.14), k=0.05)
    for j in range(13):  # burbujas: unas enteras, otras a medio salir
        a, r = rnd.uniform(0, math.tau), 1.35 * math.sqrt(rnd.random())
        s = rnd.uniform(0.12, 0.34)
        p.esfera((r * math.cos(a), r * math.sin(a), 0.1 + s * rnd.uniform(-0.2, 0.4)), s, "cieno", k=0.05)
    for j in range(4):  # burbujas reventadas: un anillo
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.3, 1.2)
        p.toro((r * math.cos(a), r * math.sin(a), 0.12), rnd.uniform(0.16, 0.25), 0.035, "cieno", k=0.03)
    d = p.duro
    for j in range(5):  # juncos podridos
        a = math.tau * j / 5 + 0.4
        x, y = 1.62 * math.cos(a), 1.62 * math.sin(a)
        d.cuerno([(x, y, 0.1), (x * 1.03, y * 1.03, 0.32), (x * 1.1, y * 1.1, 0.5)], 0.04, "corteza", n=4, seg=2)
