"""Ronda 8: props y decoración (71-80)."""

import math

import numpy as np

from lib import VERDE, VIOLETA, curva, modelo


@modelo("props", "mediana", (6, 4, 4), "Cráneo enorme de una bestia muerta, decorativo: cuernos, dientes y hueco por dentro.")
def craneo_gigante(M):
    rnd = M.rnd
    p = M.pieza("craneo", tris=5600, res=190, k=0.18, ruido=(0.035, 1.5), suelo=0.0)
    with p.en((0, 0.3, 0), rot=(0, 0, 0)):
        p.esfera((0, 1.0, 1.9), 1, "hueso_viejo", esc=(1.55, 1.6, 1.5), cascara=0.22)        # bóveda hueca
        p.esfera((0, -0.9, 1.3), 1, "hueso_viejo", esc=(1.0, 1.7, 0.85), cascara=0.2)        # hocico hueco
        p.tubo([(0, -2.4, 1.7), (0, -0.8, 2.25), (0, 0.9, 3.35), (0, 2.2, 2.9)], [0.2, 0.26, 0.3, 0.2], "hueso", suave=10)  # cresta sagital
        p.tubo([(0.4, -0.6, 2.0), (1.3, -0.1, 2.5), (1.75, 1.0, 2.2)], [0.26, 0.36, 0.26], "hueso", sim=True)                 # cejas
        p.tubo([(1.5, 0.9, 1.6), (1.75, -0.2, 1.15), (1.1, -1.3, 0.95)], [0.24, 0.26, 0.2], "hueso", sim=True)                # arco cigomático
        p.esfera((1.1, -0.3, 1.85), 0.58, "negro", esc=(1, 1.2, 1), sim=True, resta=True, k=0.08)                             # cuencas
        p.esfera((0, -2.45, 1.45), 0.36, "negro", esc=(0.9, 1, 1.2), resta=True, k=0.05)                                      # nariz
        p.esfera((0.9, 1.6, 2.6), 0.36, "negro", resta=True, k=0.04)                                                           # agujero de un golpe
        p.tubo([(0.3, -1.2, 2.1), (0.5, -0.2, 2.9), (0.2, 0.9, 3.25)], 0.035, None, resta=True)                               # grieta
        # Mandíbula suelta, caída a un lado.
        p.tubo([(1.5, 1.2, 0.5), (1.35, -0.6, 0.28), (0.75, -2.5, 0.3), (0, -2.95, 0.36)], [0.3, 0.3, 0.26, 0.28], "hueso", suave=10, sim=True)
        p.tubo([(1.5, 1.2, 0.5), (1.6, 1.6, 1.3)], [0.3, 0.2], "hueso", sim=True)
        d = p.duro
        d.cuerno([(1.3, 1.4, 2.6), (2.5, 1.9, 3.0), (3.0, 0.9, 3.9), (2.6, -0.2, 4.3)], 0.42, "garra", n=8, seg=8, sim=True)
        d.cuerno([(0, -2.2, 1.85), (0, -2.7, 2.5), (0, -2.3, 3.0)], 0.2, "garra", n=6, seg=4)
        for i in range(6):
            x = 0.92 - 0.1 * i
            y = -0.6 - i * 0.36
            L = 0.75 if i in (4,) else 0.4
            d.cuerno([(x, y, 0.75), (x * 1.04, y - 0.05, 0.75 - L * 0.5), (x * 0.98, y, 0.75 - L)], 0.11, "diente", n=5, seg=3, sim=True)
            d.cono((x * 1.25 + 0.1, y, 0.5), (x * 1.25 + 0.1, y - 0.03, 0.9 + (0.25 if i == 5 else 0)), 0.09, "diente", n=5, sim=True)


@modelo("props", "mediana", (6, 1, 6), "Arco de entrada hecho con una columna vertebral gigante.")
def columna_vertebral_arco(M):
    p = M.pieza("arco", tris=6900, res=210, k=0.08, ruido=(0.025, 1.8), suelo=0.0)
    n = 15
    for i in range(n):
        a = math.pi * i / (n - 1)
        c, s = math.cos(a), math.sin(a)
        R = 2.45
        with p.en((R * c, 0, 0.2 + R * 1.95 * s), rot=(0, 90 - math.degrees(math.atan2(1.95 * s, c)), 0)):
            # Vértebra en local: el eje de la columna es Z, «fuera» del arco es +X.
            p.cilindro((0, 0, -0.26), (0, 0, 0.26), 0.36, "hueso", red=0.1)
            p.tubo([(0.3, 0, 0), (0.75, 0, 0.1), (1.05, 0, 0.36)], [0.2, 0.15, 0.08], "hueso", k=0.06)          # apófisis espinosa
            p.tubo([(0.1, 0.3, 0), (0.25, 0.66, 0.05)], [0.16, 0.08], "hueso", k=0.06)                            # transversas
            p.tubo([(0.1, -0.3, 0), (0.25, -0.66, 0.05)], [0.16, 0.08], "hueso", k=0.06)
            p.toro((0.42, 0, 0), 0.2, 0.07, "hueso_viejo", eje=(0, 0, 1), k=0.04)                                 # arco neural
            p.esfera((0, 0, 0.36), 0.28, "tendon", esc=(1, 1, 0.36), k=0.03)                                      # disco
    for s in (-1, 1):
        p.esfera((s * 2.45, 0, 0), 1, "tierra", esc=(0.75, 0.62, 0.42))
    d = p.duro
    for i in (5, 7, 9):   # costillas rotas que cuelgan de la clave
        a = math.pi * i / (n - 1)
        b = np.array([2.2 * math.cos(a), 0, 0.2 + 2.2 * 1.95 * math.sin(a)])
        d.cuerno([b, b + [0.1, 0.35, -0.6], b + [0, 0.15, -1.3]], 0.08, "hueso_viejo", n=5, seg=4)
        d.cuerno([b, b + [-0.1, -0.35, -0.5], b + [0, -0.15, -1.1]], 0.08, "hueso_viejo", n=5, seg=4)


@modelo("props", "prop", (3, 0.5, 0.5), "Fémur grande suelto: decoración o arma improvisada.")
def hueso_suelto_a(M):
    p = M.pieza("femur", tris=1900, res=230, k=0.05, ruido=(0.012, 3.0))
    p.tubo([(-1.15, 0, 0.25), (-0.5, 0.03, 0.26), (0.5, 0.03, 0.26), (1.1, 0, 0.25)], [0.15, 0.105, 0.1, 0.16], "hueso", suave=10)
    # Extremo proximal: cabeza esférica sobre su cuello y trocánter.
    p.tubo([(-1.15, 0, 0.25), (-1.32, -0.14, 0.3)], [0.12, 0.1], "hueso")
    p.esfera((-1.37, -0.16, 0.31), 0.155, "hueso")
    p.esfera((-1.3, 0.12, 0.27), 0.14, "hueso_viejo", esc=(1.2, 1, 1), k=0.06)
    # Extremo distal: dos cóndilos con el surco en medio.
    p.esfera((1.3, -0.11, 0.24), 0.17, "hueso", esc=(1.2, 1, 1.1))
    p.esfera((1.3, 0.11, 0.24), 0.16, "hueso", esc=(1.2, 1, 1.1))
    p.capsula((1.2, 0, 0.42), (1.5, 0, 0.3), 0.05, None, resta=True, k=0.03)
    p.tubo([(-0.6, 0.11, 0.27), (0.6, 0.11, 0.27)], 0.03, "hueso_viejo", k=0.03)   # línea áspera
    for (x, a) in ((-0.2, 0.3), (0.1, -0.5), (0.35, 0.2)):                          # marcas de mordisco
        p.capsula((x, -0.12, 0.32), (x + 0.12, -0.1, 0.36 + a * 0.05), 0.022, "hueso_viejo", resta=True, k=0.01)
    p.tubo([(-0.9, -0.02, 0.37), (-0.3, 0.02, 0.37), (0.2, -0.03, 0.365)], 0.012, None, resta=True)  # grieta


@modelo("props", "prop", (2, 0.3, 1.5), "Costilla grande y curvada, suelta.")
def hueso_suelto_b(M):
    p = M.pieza("costilla", tris=1700, res=230, k=0.04, ruido=(0.01, 3.5))
    arco = curva([(-0.95, 0, 0.12), (-0.8, 0, 0.9), (-0.2, 0, 1.4), (0.5, 0, 1.25), (0.92, 0, 0.6), (0.95, 0, 0.1)], 22)
    n = len(arco)
    radios = [0.085 + 0.03 * math.sin(math.pi * i / (n - 1)) for i in range(n)]
    p.tubo([q + [0, -0.05, 0] for q in arco], radios, "hueso")          # la costilla es aplanada: dos tubos pegados
    p.tubo([q + [0, 0.05, 0] for q in arco], [r * 0.9 for r in radios], "hueso")
    p.esfera((-0.97, 0, 0.1), 0.15, "hueso_viejo", esc=(1.1, 1, 0.9), k=0.05)      # cabeza articular
    p.esfera((-0.84, 0.03, 0.42), 0.1, "hueso_viejo", k=0.05)                       # tubérculo
    p.esfera((0.95, 0, 0.1), 0.1, "tendon", k=0.03)                                 # cartílago del extremo
    p.tubo([arco[i] + [0, -0.14, 0] for i in range(4, 18)], 0.014, None, resta=True)  # surco costal
    p.capsula((0.2, -0.1, 1.42), (0.3, 0.1, 1.38), 0.03, "hueso_viejo", resta=True, k=0.01)  # muesca


@modelo("props", "prop", (6, 0.1, 6), "Telaraña gigante entre dos puntos, con hilos de grosor real.")
def telarana_gigante(M):
    rnd = M.rnd
    p = M.pieza("telarana", tris=0)
    d = p.duro
    C = np.array([0.2, 0, 3.1])
    n = 11
    anclas = []
    for j in range(n):
        a = math.tau * j / n + 0.15
        r = 3.0 * (1 + 0.12 * math.sin(3 * a))
        anclas.append(np.array([max(-3, min(3, r * math.cos(a) * 1.15)), 0.0, max(0, min(6, 3.0 + r * math.sin(a) * 1.15))]))
        d.tubo([C, anclas[-1]], 0.024, "seda", n=3)
    for k_ in range(1, 9):   # espiral: tramos con comba entre radio y radio
        f = k_ / 9
        for j in range(n):
            a = C + (anclas[j] - C) * (f + 0.012 * j)
            b = C + (anclas[(j + 1) % n] - C) * (f + 0.012 * (j + 1) if j < n - 1 else f + 0.012 * n)
            m = (a + b) / 2 + (C - (a + b) / 2) * 0.1 + [0, 0.012 * (1 if (j + k_) % 2 else -1), 0]
            d.tubo([a, m, b], 0.015, "seda", n=3)
    d.esfera(C, 0.09, "seda", sub=1, esc=(1, 0.5, 1))
    # Presa envuelta y gotas pegajosas.
    q = C + (anclas[2] - C) * 0.55
    d.torno([(0, -0.3), (0.1, -0.24), (0.15, 0.0), (0.11, 0.22), (0, 0.3)], q + [0, 0.02, 0], "seda", n=6, rot=(0, 30, 0))
    for j in range(8):
        a = C + (anclas[(j * 3) % n] - C) * rnd.uniform(0.3, 0.9)
        d.esfera(a + [0, 0, -0.03], 0.035, "mucosa", sub=1)


@modelo("props", "prop", (1.5, 1.5, 2), "Huevo de monstruo: cáscara dura con venas y un brillo verdoso por dentro.")
def huevo_monstruo(M):
    rnd = M.rnd
    M.mat("cascara", "piel", a="#3E3048", b="#1E1626", rug=0.5, escamas=dict(esc=5.0, fuerza=0.3))
    p = M.pieza("huevo", tris=1400, res=170, k=0.04, ruido=(0.012, 3.0), suelo=0.0)
    perfil = [(0, 0.1), (0.45, 0.2), (0.7, 0.7), (0.66, 1.2), (0.45, 1.7), (0.2, 1.95), (0, 2.0)]
    p.torno(perfil, (0, 0, 0), "cascara", cascara=0.1)
    for j in range(7):   # venas en relieve que suben desde la base
        a = math.tau * j / 7 + rnd.uniform(-0.2, 0.2)
        pts = []
        for z in np.linspace(0.25, 1.75, 6):
            r = float(np.interp(z, [0.1, 0.2, 0.7, 1.2, 1.7, 1.95], [0, 0.45, 0.7, 0.66, 0.45, 0.2]))
            a += rnd.uniform(-0.2, 0.2)
            pts.append((r * math.cos(a), r * math.sin(a), z))
        p.tubo(pts, [0.06, 0.05, 0.04, 0.03, 0.02], "carne_viva", suave=10, k=0.03)
    # Grietas por las que se ve la luz de dentro.
    for (a, z, la) in ((0.4, 1.2, 0.5), (2.6, 0.9, 0.4), (4.4, 1.35, 0.45)):
        c, s = math.cos(a), math.sin(a)
        p.tubo([(0.75 * c, 0.75 * s, z - la), (0.8 * math.cos(a + 0.2), 0.8 * math.sin(a + 0.2), z - la * 0.3), (0.75 * math.cos(a - 0.1), 0.75 * math.sin(a - 0.1), z + la * 0.3),
                (0.6 * math.cos(a + 0.15), 0.6 * math.sin(a + 0.15), z + la)], [0.06, 0.13, 0.11, 0.04], None, resta=True)
    M.mat("baba_nido", "mucosa", a="#2E5A1E", b="#16301A", emis=(VERDE, 0.04))
    p.torno([(0, 0), (0.75, 0), (0.85, 0.12), (0.62, 0.26), (0, 0.2)], (0, 0, 0), "baba_nido", k=0.08)   # baba del nido
    n = M.pieza("interior_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    n.duro.torno([(0, 0.24), (0.36, 0.32), (0.58, 0.72), (0.55, 1.2), (0.36, 1.66), (0.14, 1.86), (0, 1.9)], (0, 0, 0), "neon_verde", n=10)


@modelo("props", "prop", (1, 1, 2), "Capullo de seda colgante: una pupa envuelta con una forma humanoide apenas visible dentro.",
        ancla="techo")
def capullo_seda(M):
    p = M.pieza("capullo", tris=1750, res=180, k=0.1, ruido=(0.012, 3.0))
    # La figura de dentro: cabeza, hombros, brazos cruzados, rodillas... tapada por la seda (unión muy suave).
    p.esfera((0, -0.04, 1.42), 0.19, "seda")
    p.esfera((0, 0, 1.08), 1, "seda", esc=(0.33, 0.22, 0.3))
    p.tubo([(-0.3, -0.05, 1.12), (-0.1, -0.2, 0.9), (0.14, -0.2, 1.0)], [0.09, 0.08, 0.07], "seda")
    p.tubo([(0.3, -0.05, 1.12), (0.1, -0.22, 0.82), (-0.14, -0.2, 0.92)], [0.09, 0.08, 0.07], "seda")
    p.esfera((0, 0, 0.72), 1, "seda", esc=(0.28, 0.2, 0.3))
    p.tubo([(-0.1, 0, 0.6), (-0.12, -0.14, 0.36), (-0.08, 0.02, 0.12)], [0.12, 0.1, 0.07], "seda")
    p.tubo([(0.1, 0, 0.6), (0.12, -0.16, 0.38), (0.08, 0.02, 0.12)], [0.12, 0.1, 0.07], "seda")
    p.torno([(0, 0.0), (0.16, 0.08), (0.26, 0.5), (0.29, 1.0), (0.2, 1.5), (0.1, 1.75), (0, 1.8)], (0, 0, 0), "seda", k=0.1)   # el envoltorio
    for v in range(4):   # vueltas de hilo gordo
        pts = [(0.34 * math.cos(t * 7 + v * 1.6) * math.sin(0.25 + t * 2.6), 0.3 * math.sin(t * 7 + v * 1.6) * math.sin(0.25 + t * 2.6), 0.1 + 1.55 * t) for t in np.linspace(0, 1, 16)]
        p.tubo(pts, 0.035, "tendon", k=0.02)
    p.tubo([(0, 0, 1.75), (0.02, 0, 1.9), (0, 0, 2.0)], [0.08, 0.04, 0.06], "seda", k=0.03)
    d = p.duro
    for j in range(4):   # hebras sueltas
        a = j * 1.7
        d.tubo([(0.3 * math.cos(a), 0.3 * math.sin(a), 0.6 + 0.2 * j), (0.4 * math.cos(a), 0.4 * math.sin(a), 0.3 + 0.2 * j), (0.36 * math.cos(a + 0.3), 0.36 * math.sin(a + 0.3), 0.05 + 0.15 * j)],
               [0.015, 0.012, 0.0], "seda", n=3)


@modelo("props", "prop", (1, 1, 3), "Cristal púrpura que crece del suelo y brilla.")
def cristal_oscuro_suelo(M):
    rnd = M.rnd
    b = M.pieza("base", tris=420, res=90, k=0.1, ruido=(0.03, 2.5), suelo=0.0)
    for j in range(5):
        a = math.tau * j / 5
        b.esfera((0.26 * math.cos(a), 0.26 * math.sin(a), 0.02), rnd.uniform(0.16, 0.24), "piedra")
    c = M.pieza("cristal_neon", tris=0, angulo=25, roblox=dict(material="Neon", color=VIOLETA, transparencia=0.1))
    d = c.duro
    d.prisma((0, 0, 0), (0.06, 0.03, 3.0), 0.21, "cristal", n=6, punta=0.22, r2=0.17)
    for j in range(6):
        a = math.tau * j / 6 + 0.4
        L = rnd.uniform(0.8, 1.9)
        inc = rnd.uniform(0.2, 0.42)
        d.prisma((0.14 * math.cos(a), 0.14 * math.sin(a), 0.0), (inc * L * math.cos(a) + 0.14 * math.cos(a), inc * L * math.sin(a) + 0.14 * math.sin(a), L), rnd.uniform(0.08, 0.13),
                 "cristal" if j % 2 else "cristal_oscuro", n=5, punta=0.3, giro=rnd.uniform(0, 1))
    for j in range(4):   # esquirlas
        a = math.tau * j / 4 + 1.0
        d.prisma((0.36 * math.cos(a), 0.36 * math.sin(a), 0.05), (0.46 * math.cos(a), 0.46 * math.sin(a), 0.42), 0.045, "cristal", n=4, punta=0.5)


@modelo("props", "prop", (0.5, 0.5, 2), "Baba colgante del techo: mucosidad verde translúcida.", ancla="techo")
def baba_colgante(M):
    p = M.pieza("baba_cristal", tris=1500, res=200, k=0.1, ruido=(0.01, 4.0), roblox=dict(material="Glass", color="#5FB81E", transparencia=0.35))
    p.esfera((0, 0, 2.0), 1, "mucosa", esc=(0.24, 0.24, 0.1))          # la mancha pegada al techo
    hilos = [((0, 0, 2.0), (0.02, 0.01, 1.0), (0, 0, 0.14), 0.085), ((0.12, 0.05, 2.0), (0.14, 0.07, 1.5), (0.13, 0.05, 0.95), 0.06), ((-0.12, -0.06, 2.0), (-0.14, -0.08, 1.7), (-0.13, -0.06, 1.35), 0.055),
             ((-0.03, 0.14, 2.0), (-0.03, 0.15, 1.8), (-0.03, 0.15, 1.62), 0.045)]
    for a, b, c, r in hilos:
        p.tubo([a, ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2), b, c], [r * 1.5, r * 0.5, r * 0.36, r * 0.6], "mucosa")
        p.esfera(c, r * 1.25, "mucosa", esc=(1, 1, 1.35))               # gota gorda en la punta
    p.esfera((0.02, 0.01, 1.05), 0.075, "mucosa", esc=(1, 1, 1.5))      # gota a medio bajar
    p.tubo([(0.0, 0, 1.6), (0.07, 0.03, 1.5), (0.13, 0.05, 1.45)], 0.022, "mucosa", k=0.03)   # puentecillo entre hilos


@modelo("props", "prop", (2, 1, 3), "Piedra con runas monstruosas grabadas que brillan en púrpura.")
def piedra_runica(M):
    p = M.pieza("piedra", tris=1150, res=170, k=0.08, ruido=(0.05, 1.6), suelo=0.0)
    p.extrusion([(-0.85, 0), (-0.95, 1.2), (-0.7, 2.4), (-0.15, 2.95), (0.5, 2.7), (0.9, 1.7), (0.85, 0)], 0.6, (0, 0, 0), "piedra", rot=(90, 0, 0), red=0.12)
    p.esfera((0, 0, 0), 1, "tierra", esc=(1.0, 0.5, 0.3))
    p.esfera((-0.6, 0.15, 0.12), 0.26, "piedra")
    p.esfera((0.62, -0.2, 0.1), 0.22, "piedra")
    runas = [[(-0.3, 2.35), (0.0, 2.6), (0.3, 2.3)], [(0.0, 2.6), (0.0, 2.0)], [(-0.45, 1.7), (-0.1, 1.85), (-0.3, 1.4), (0.0, 1.25)], [(0.2, 1.8), (0.5, 1.55), (0.2, 1.3)],
             [(-0.5, 0.9), (-0.2, 0.55), (-0.5, 0.5)], [(-0.2, 1.0), (-0.2, 0.45)], [(0.1, 0.95), (0.45, 0.8), (0.15, 0.6), (0.5, 0.45)]]
    n = M.pieza("runas_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    for cara in (-1, 1):
        for r in runas:
            pts = [(x * cara * -1, cara * 0.3, z) for x, z in r]
            p.tubo(pts, 0.055, None, resta=True, k=0.02)
            n.duro.tubo([(x, y * 0.86, z) for x, y, z in pts], 0.042, "neon_violeta", n=4)
