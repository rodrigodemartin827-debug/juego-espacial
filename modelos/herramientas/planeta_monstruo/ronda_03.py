"""Ronda 3: vegetación alienígena (21-30)."""

import math

import numpy as np

from formas import seta
from lib import ROJO, VERDE, VIOLETA, curva, modelo


@modelo("vegetacion", "vegetacion", (5, 5, 14), "Árbol de carne y tendones: tronco de músculo, venas a la vista y "
        "«hojas» que son membranas de piel colgando.")
def arbol_carne(M):
    rnd = M.rnd
    p = M.pieza("arbol", tris=2500, res=230, k=0.18, ruido=(0.05, 1.2), suelo=0.0)
    tronco = curva([(0, 0, 0), (0.25, 0.1, 3.0), (-0.2, 0.2, 6.0), (0.15, -0.1, 8.6)], 12)
    p.tubo(tronco, [0.95, 0.7, 0.6, 0.5, 0.42], "musculo")
    for j in range(5):  # raíces de músculo
        a = math.tau * j / 5 + 0.2
        p.tubo([(0, 0, 1.3), (0.8 * math.cos(a), 0.8 * math.sin(a), 0.5), (1.6 * math.cos(a), 1.6 * math.sin(a), 0.0)],
               [0.4, 0.36, 0.16], "musculo", suave=6)
    for j in range(3):  # tendones que suben en espiral
        pts = []
        for i, q in enumerate(tronco):
            a = j * 2.1 + i * 0.55
            r = 0.92 - i * 0.04
            pts.append((q[0] + r * 0.75 * math.cos(a), q[1] + r * 0.75 * math.sin(a), q[2]))
        p.tubo(pts, 0.13, "tendon", k=0.08)
    ramas = []
    for j in range(6):
        a = math.tau * j / 6 + rnd.uniform(-0.2, 0.2)
        z0 = 6.4 + (j % 3) * 1.0
        c, s = math.cos(a), math.sin(a)
        L = rnd.uniform(1.6, 2.2)
        pts = curva([(0.1 * c, 0.1 * s, z0), (L * 0.55 * c, L * 0.55 * s, z0 + 1.6), (L * c, L * s, z0 + 2.9),
                     (L * 1.02 * c, L * 1.02 * s, z0 + 4.2)], 8)
        ramas.append(pts)
        p.tubo(pts, [0.36, 0.26, 0.18, 0.1], "musculo")
        p.esfera(pts[3], 0.3, "carne_viva", k=0.15)  # nudo tumoral
    p.esfera((0.3, -0.5, 4.2), 0.5, "carne_viva", k=0.25)
    p.esfera((-0.35, 0.4, 2.4), 0.45, "carne_viva", k=0.25)
    d = p.duro
    # Membranas de piel colgando de cada rama (rejilla con grosor: se ven por las dos caras).
    for pts in ramas:
        for (i0, i1) in ((2, 5), (5, 8)):
            a, b = np.array(pts[i0]), np.array(pts[i1])
            L = rnd.uniform(2.0, 3.6)
            filas = []
            for u in range(4):
                fila = []
                for v in range(4):
                    t = v / 3
                    q = a + (b - a) * t
                    cae = L * (u / 3) * (0.55 + 0.45 * math.sin(math.pi * (0.15 + 0.7 * t)))
                    ond = 0.22 * math.sin(u * 1.4 + v * 1.9 + a[0]) * (u / 3)
                    fila.append((q[0] * (1 - 0.05 * u) + ond * q[1] * 0.3, q[1] * (1 - 0.05 * u) - ond * q[0] * 0.3, q[2] - 0.05 - cae))
                filas.append(fila)
            d.superficie(filas, 0.07, "membrana")


@modelo("vegetacion", "vegetacion", (4, 4, 12), "Árbol de hueso blanco, muerto: tronco de hueso con ramas como "
        "costillas y sin hojas.")
def arbol_hueso(M):
    rnd = M.rnd
    p = M.pieza("arbol", tris=3700, res=240, k=0.1, ruido=(0.03, 1.8), suelo=0.0)
    tronco = curva([(0, 0, 0), (0.15, 0.1, 3.0), (-0.1, -0.05, 6.5), (0.1, 0.05, 9.6)], 12)
    p.tubo(tronco, [0.6, 0.45, 0.36, 0.3, 0.22], "hueso")
    p.esfera((0, 0, 0), 1, "hueso_viejo", esc=(1.0, 0.9, 0.55))
    for j in range(4):
        a = math.tau * j / 4 + 0.5
        p.tubo([(0.2 * math.cos(a), 0.2 * math.sin(a), 0.9), (0.9 * math.cos(a), 0.9 * math.sin(a), 0.3),
                (1.35 * math.cos(a), 1.35 * math.sin(a), 0)], [0.3, 0.22, 0.12], "hueso_viejo", suave=5)
    # Nudos-vértebra y pares de costillas que se curvan hacia arriba.
    for i in range(7):
        z = 2.4 + i * 1.05
        q = tronco[min(12, int(z / 9.6 * 12))]
        p.esfera((q[0], q[1], z), 0.5 - i * 0.03, "hueso", esc=(1, 1, 0.55), k=0.08)
        giro = i * 1.15
        for s in (-1, 1):
            a = giro + (0 if s > 0 else math.pi) + rnd.uniform(-0.25, 0.25)
            c, sn = math.cos(a), math.sin(a)
            L = (1.9 - i * 0.12) * rnd.uniform(0.85, 1.1)
            p.tubo([(q[0] + 0.25 * c, q[1] + 0.25 * sn, z), (q[0] + L * 0.7 * c, q[1] + L * 0.7 * sn, z + 0.25),
                    (q[0] + L * c, q[1] + L * sn, z + 1.1), (q[0] + L * 0.72 * c, q[1] + L * 0.72 * sn, z + 2.2)],
                   [0.2, 0.16, 0.12, 0.05], "hueso", suave=8, k=0.06)
    # Copa: dedos de hueso articulados.
    q = tronco[-1]
    for j in range(4):
        a = math.tau * j / 4 + 0.3
        c, s = math.cos(a), math.sin(a)
        pts = [(q[0], q[1], 9.5), (q[0] + 0.5 * c, q[1] + 0.5 * s, 10.5), (q[0] + 0.85 * c, q[1] + 0.85 * s, 11.3), (q[0] + 0.7 * c, q[1] + 0.7 * s, 12.0)]
        p.tubo(pts, [0.2, 0.15, 0.11, 0.04], "hueso", k=0.05)
        for k_ in (1, 2):
            p.esfera(pts[k_], 0.19 - 0.03 * k_, "hueso_viejo", k=0.04)
    d = p.duro
    for j in range(3):  # jirones secos colgando de alguna costilla
        a = j * 2.3
        x, y, z = 1.2 * math.cos(a), 1.2 * math.sin(a), 5.0 + j * 1.3
        d.tubo([(x, y, z), (x * 1.02, y * 1.02, z - 0.7), (x, y, z - 1.5)], [0.03, 0.05, 0.015], "tendon", n=4)


@modelo("vegetacion", "vegetacion", (6, 6, 10), "Hongo gigante como árbol: tallo grueso y pálido y un sombrero enorme "
        "púrpura con esporas verdes luminosas.")
def arbol_hongo_gigante(M):
    rnd = M.rnd
    p = M.pieza("hongo", tris=2900, res=220, k=0.15, ruido=(0.05, 1.0), suelo=0.0)
    sup = seta(p, rnd, alto=10.0, radio=3.0, curva_=0.03, k=0.15)
    p.torno([(0, 5.4), (1.25, 5.0), (1.4, 4.75), (1.0, 5.2), (0, 5.9)], (0.1, 0.1, 0), "hongo_laminas", k=0.1)  # faldón
    for j in range(5):  # contrafuertes del pie
        a = math.tau * j / 5
        p.tubo([(0.3 * math.cos(a), 0.3 * math.sin(a), 1.6), (1.0 * math.cos(a), 1.0 * math.sin(a), 0.5), (1.5 * math.cos(a), 1.5 * math.sin(a), 0)],
               [0.4, 0.34, 0.16], "hongo_tallo", suave=5)
    for (x, y, h, r) in ((1.9, 0.6, 1.6, 0.6), (-1.6, 1.2, 1.1, 0.45), (-0.9, -1.9, 1.9, 0.7)):  # hijos al pie
        with p.en((x, y, 0)):
            seta(p, rnd, alto=h, radio=r, k=0.05)
    n = M.pieza("esporas_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    for j in range(16):  # bulbos de esporas sobre el sombrero
        q = sup(rnd.uniform(0.08, 0.85), j * 2.4)
        n.duro.esfera(q, rnd.uniform(0.14, 0.3), "neon_verde", sub=1, esc=(1, 1, 0.7))
    for j in range(8):  # esporas que caen de las láminas, unidas por un hilo
        a, r = j * 0.8 + 0.3, rnd.uniform(1.0, 2.5)
        z = 7.2
        L = rnd.uniform(0.5, 1.6)
        n.duro.tubo([(r * math.cos(a), r * math.sin(a), z + 0.3), (r * math.cos(a), r * math.sin(a), z - L)], 0.02, "neon_verde", n=3)
        n.duro.esfera((r * math.cos(a), r * math.sin(a), z - L), 0.1, "neon_verde", sub=1)


@modelo("vegetacion", "vegetacion", (5, 5, 10), "Árbol con tentáculos en vez de ramas, con ventosas. Lleva tres poses "
        "de los tentáculos (a, b, c) para animarlo mostrando una cada vez.")
def arbol_tentaculo(M):
    rnd = M.rnd
    M.mat("tentaculo", "piel_purpura", a="#5A2A72", b="#2A1238", rug=0.42,
          manchas=dict(color="#C89AB0", esc=2.2, radio=0.2))
    p = M.pieza("tronco", tris=1150, res=180, k=0.2, ruido=(0.05, 1.2), suelo=0.0)
    p.tubo(curva([(0, 0, 0), (0.2, 0.1, 2.5), (-0.1, 0.0, 4.8), (0, 0, 6.2)], 8), [0.95, 0.7, 0.62, 0.75], "corteza")
    p.esfera((0, 0, 6.4), 0.95, "carne", esc=(1, 1, 0.8))
    p.esfera((0, 0, 7.1), 0.5, "carne_viva", esc=(1, 1, 0.6), resta=True, k=0.1)  # boca de arriba
    for j in range(5):
        a = math.tau * j / 5 + 0.4
        p.tubo([(0, 0, 1.2), (0.9 * math.cos(a), 0.9 * math.sin(a), 0.4), (1.7 * math.cos(a), 1.7 * math.sin(a), 0)], [0.4, 0.32, 0.14],
               "corteza", suave=5)
    for nombre, fase in (("tentaculos_pose_a", 0.0), ("tentaculos_pose_b", 1.3), ("tentaculos_pose_c", 2.6)):
        t = M.pieza(nombre, tris=930, res=150, k=0.05, ruido=(0.02, 2.0))
        for j in range(6):
            a = math.tau * j / 6 + 0.2
            c, s = math.cos(a), math.sin(a)
            bal = 0.5 * math.sin(fase + j * 1.7)       # balanceo lateral
            sube = 0.5 * math.cos(fase * 1.3 + j * 0.9)  # arriba/abajo
            ct, st = math.cos(a + bal), math.sin(a + bal)
            L = 2.1
            pts = [(0.5 * c, 0.5 * s, 6.5), (L * 0.6 * c, L * 0.6 * s, 7.9 + sube * 0.4), (L * ct, L * st, 7.6 + sube),
                   (L * 1.15 * ct, L * 1.15 * st, 5.6 + sube * 0.6), (L * (0.95 + 0.25 * bal) * ct, L * (0.95 + 0.25 * bal) * st, 3.6),
                   (L * (1.05 - 0.4 * bal) * math.cos(a + bal * 1.8), L * (1.05 - 0.4 * bal) * math.sin(a + bal * 1.8), 2.4 - sube * 0.5)]
            if j % 2:
                pts[1] = (pts[1][0], pts[1][1], pts[1][2] + 1.3)
                pts[2] = (pts[2][0] * 0.8, pts[2][1] * 0.8, pts[2][2] + 2.0)
                pts[3] = (pts[3][0], pts[3][1], pts[3][2] + 2.0)
                pts[4] = (pts[4][0] * 1.1, pts[4][1] * 1.1, pts[4][2] + 1.6)
                pts[5] = (pts[5][0], pts[5][1], pts[5][2] + 1.4)
            t.tubo(pts, [0.36, 0.3, 0.25, 0.2, 0.14, 0.05], "tentaculo", suave=14)
    M.notas["poses"] = ["tentaculos_pose_a", "tentaculos_pose_b", "tentaculos_pose_c"]
    M.notas["animacion"] = "Las tres piezas de tentáculos ocupan el mismo sitio: muestra una y oculta las otras dos."


@modelo("vegetacion", "vegetacion", (4, 4, 12), "Árbol cristalizado oscuro: tronco de cristal negro y púrpura con ramas "
        "de cristal que brillan en violeta.")
def arbol_cristal_oscuro(M):
    rnd = M.rnd
    b = M.pieza("base", tris=600, res=110, k=0.2, ruido=(0.08, 1.2), suelo=0.0)
    for j in range(6):
        a = math.tau * j / 6
        b.esfera((0.8 * math.cos(a), 0.8 * math.sin(a), 0.1), rnd.uniform(0.5, 0.75), "piedra")
    p = M.pieza("tronco", tris=0, angulo=28)
    n = M.pieza("ramas_neon", tris=0, angulo=28, roblox=dict(material="Neon", color=VIOLETA))
    d, nd = p.duro, n.duro
    # Tronco: prismas encadenados, cada uno un poco girado, como un cristal que ha crecido a tirones.
    q = np.array([0.0, 0.0, 0.0])
    nodos = []
    r = 0.62
    for i in range(6):
        nq = q + np.array([rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 1.75])
        d.prisma(q - [0, 0, 0.3], nq + [0, 0, 0.55], r, "cristal_oscuro", n=6, punta=0.18, r2=r * 0.86, giro=i * 0.5)
        nodos.append((nq, r))
        q = nq
        r *= 0.86
    d.prisma(q, q + [0.1, 0, 1.7], r, "cristal_oscuro", n=6, punta=0.5, giro=1.0)
    for j in range(5):  # esquirlas en el pie
        a = math.tau * j / 5 + 0.3
        d.prisma((0.5 * math.cos(a), 0.5 * math.sin(a), 0.1), (1.25 * math.cos(a), 1.25 * math.sin(a), rnd.uniform(1.0, 1.9)), 0.22,
                 "cristal_oscuro", n=5, punta=0.4)
    # Ramas: salen de los nodos, se bifurcan, y las puntas son cristal vivo que brilla.
    for i, (nq, r) in enumerate(nodos[1:], 1):
        for j in range(2 if i < 4 else 3):
            a = i * 1.3 + j * (math.tau / (2 if i < 4 else 3)) + rnd.uniform(-0.3, 0.3)
            dire = np.array([math.cos(a), math.sin(a), rnd.uniform(0.35, 0.8)])
            L = rnd.uniform(1.1, 1.8) * (1.15 - i * 0.07)
            m = nq + dire * L
            d.prisma(nq, m, r * 0.45, "cristal_oscuro", n=5, punta=0.15, r2=r * 0.34, giro=rnd.uniform(0, 1))
            nd.prisma(m - dire * 0.15, m + dire * L * 0.55 + [0, 0, L * 0.5], r * 0.3, "cristal", n=5, punta=0.45)
            lado = np.array([-dire[1], dire[0], 0.6])
            nd.prisma(m - dire * 0.1, m + lado * L * 0.5, r * 0.22, "cristal", n=4, punta=0.5)
    nd.prisma(q + [0.1, 0, 1.2], q + [0.2, 0.1, 2.9], 0.2, "cristal", n=5, punta=0.5)


@modelo("vegetacion", "prop", (1, 1, 1.5), "Seta venenosa pequeña, púrpura con puntos verdes que brillan.")
def hongo_pequeno_a(M):
    rnd = M.rnd
    p = M.pieza("hongo", tris=1150, res=130, k=0.03, ruido=(0.01, 5.0), suelo=0.0)
    sup = seta(p, rnd, alto=1.5, radio=0.5, curva_=0.06)
    p.toro((0, 0, 0.72), 0.17, 0.045, "hongo_laminas", k=0.03)  # anillo del pie
    p.esfera((0, 0, 0), 0.24, "hongo_tallo", esc=(1, 1, 0.6))
    with p.en((0.3, -0.2, 0), rot=(0, 15, 0)):
        seta(p, rnd, alto=0.5, radio=0.17, k=0.02)  # hija
    n = M.pieza("puntos_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    for i in range(10):
        q = sup(0.12 + 0.075 * i, i * 2.4)
        n.duro.esfera(q, 0.05 - 0.002 * i, "neon_verde", sub=1, esc=(1, 1, 0.55))


@modelo("vegetacion", "prop", (1.5, 1, 0.5), "Seta aplanada tipo oreja, verde tóxico: sale de las paredes (se pega por "
        "detrás).")
def hongo_pequeno_b(M):
    rnd = M.rnd
    p = M.pieza("hongo", tris=1700, res=150, k=0.03, ruido=(0.012, 5.0), planos=[((0, 0.5, 0), (0, 1, 0))])
    for (x, z, r, inc) in ((0.0, 0.0, 0.75, 0), (-0.32, 0.17, 0.5, 8), (0.36, -0.14, 0.45, -10)):
        with p.en((x, 0.5, z), rot=(0, inc, 0)):
            # Repisa: disco abombado con el borde ondulado y láminas por debajo.
            p.torno([(0, -0.04), (r * 0.9, -0.08), (r, -0.02), (r * 0.95, 0.05), (r * 0.5, 0.13), (0, 0.17)], (0, 0, 0), "hongo_verde",
                    esc=(1, 1.1, 1))
            p.torno([(0, -0.1), (r * 0.5, -0.1), (r * 0.88, -0.07), (0, 0.0)], (0, 0, 0), "hongo_laminas", esc=(1, 1.1, 1), k=0.01)
            for j in range(7):
                a = math.pi + 0.3 + j * 0.42
                p.esfera((r * 0.98 * math.cos(a), r * 1.07 * math.sin(a), 0.0), r * 0.13, "hongo_verde", esc=(1, 1, 0.5), k=0.04)
    p.esfera((0, 0.5, 0), 0.3, "hongo_tallo", esc=(1.6, 0.5, 0.7), k=0.08)  # pie pegado a la pared


@modelo("vegetacion", "vegetacion", (3, 3, 2), "Grupo de seis hongos de distintos tamaños y colores oscuros.")
def hongo_cluster(M):
    rnd = M.rnd
    M.mat("sombrero_rojo", "hongo_sombrero", a="#6A1626", b="#2E0A14", manchas=dict(color="#E0C8A0", esc=3.0, radio=0.2))
    M.mat("sombrero_negro", "hongo_sombrero", a="#1E1830", b="#0C0A14", manchas=dict(color=VIOLETA, esc=3.0, radio=0.16, emis=0.9))
    M.mat("sombrero_verde", "hongo_verde", a="#2E6A2A", b="#123018")
    p = M.pieza("hongos", tris=3700, res=190, k=0.04, ruido=(0.015, 3.0), suelo=0.0)
    p.esfera((0, 0, -0.1), 1, "tierra", esc=(1.4, 1.4, 0.3))
    p.esfera((0.5, -0.4, 0.0), 0.5, "musgo", esc=(1.2, 1, 0.3), k=0.1)
    p.esfera((-0.6, 0.5, 0.0), 0.45, "musgo", esc=(1, 1.2, 0.3), k=0.1)
    datos = [(0.0, 0.1, 2.0, 0.62, "hongo_sombrero"), (-0.75, -0.3, 1.35, 0.5, "sombrero_rojo"), (0.8, 0.45, 1.1, 0.48, "sombrero_negro"),
             (0.55, -0.75, 0.75, 0.36, "sombrero_verde"), (-0.5, 0.85, 0.6, 0.3, "sombrero_rojo"), (-1.05, 0.35, 0.42, 0.22, "sombrero_negro"),
             (1.1, -0.2, 0.36, 0.2, "hongo_sombrero")]
    for x, y, h, r, mat in datos:
        with p.en((x, y, 0), rot=(rnd.uniform(-12, 12), rnd.uniform(-12, 12), rnd.uniform(0, 360))):
            seta(p, rnd, alto=h, radio=r, sombrero=mat, curva_=0.07)


@modelo("vegetacion", "vegetacion", (2, 2, 3), "Planta carnívora: boca abierta con dientes, interior rojo brillante y "
        "saliva viscosa.")
def planta_carnivora(M):
    rnd = M.rnd
    M.mat("piel_planta", "piel_purpura", a="#2E4A2A", b="#3A1A4A", rug=0.5)
    M.mat("gula", "carne_viva", emis=(ROJO, 0.4))
    p = M.pieza("planta", tris=2700, res=190, k=0.07, ruido=(0.02, 2.5), suelo=0.0)
    tallo = curva([(0, 0.3, 0), (0.05, 0.42, 0.7), (0, 0.3, 1.3), (0, 0.05, 1.7)], 8)
    p.tubo(tallo, [0.26, 0.17, 0.16, 0.22], "piel_planta")
    p.esfera((0, 0.3, 0), 0.42, "piel_planta", esc=(1, 1, 0.5))
    # Cabeza: bulbo partido en dos mandíbulas abiertas hacia delante.
    with p.en((0, -0.05, 2.05), rot=(-25, 0, 0)):
        p.esfera((0, 0, 0), 1, "piel_planta", esc=(0.72, 0.9, 0.86))
        p.esfera((0, 0, 0), 1, "gula", esc=(0.6, 0.8, 0.74), k=0.02)
        # la cuña que abre la boca
        p.extrusion([(0.25, 0.0), (-1.3, 0.62), (-1.3, -0.5)], 2.0, (0, 0, 0), "gula", eje=(1, 0, 0), resta=True, k=0.05)
        p.esfera((0, 0.1, -0.12), 0.36, "gula", esc=(1, 1.3, 0.5), k=0.06)                   # garganta
        p.tubo([(0, 0.1, -0.2), (0, -0.4, -0.3), (0.05, -0.8, -0.42), (0, -1.0, -0.3)], [0.14, 0.12, 0.09, 0.05], "carne_viva", k=0.04)  # lengua
        d = p.duro
        for i in range(7):
            a = -1.15 + i * 0.383
            x = 0.62 * math.sin(a)
            y = -0.15 - 0.72 * math.cos(a)
            L = 0.3 + (0.12 if i % 2 == 0 else 0)
            zt = 0.36 + 0.33 * (1 - math.cos(a))
            zb = -0.3 - 0.27 * (1 - math.cos(a))
            d.cuerno([(x, y, zt), (x * 0.96, y - 0.04, zt - L * 0.6), (x * 0.9, y + 0.02, zt - L)], 0.055, "diente", n=5, seg=3)
            d.cuerno([(x, y, zb), (x * 0.96, y - 0.04, zb + L * 0.5), (x * 0.9, y + 0.02, zb + L * 0.85)], 0.05, "diente", n=5, seg=3)
        for x in (-0.3, 0.12, 0.36):  # hilos de saliva entre las mandíbulas
            d.tubo([(x, -0.62, 0.5), (x + 0.03, -0.66, 0.1), (x, -0.6, -0.42)], [0.035, 0.012, 0.03], "mucosa", n=4, suave=4)
        for i in range(5):  # cresta de púas
            y = -0.5 + i * 0.3
            d.cono((0, y, 0.82 - 0.08 * abs(i - 2)), (0, y + 0.12, 1.12 - 0.1 * abs(i - 2)), 0.06, "garra", n=4)
    d = p.duro
    for j in range(6):  # hojas-cuchilla en la base
        a = math.tau * j / 6 + 0.3
        c, s = math.cos(a), math.sin(a)
        filas = []
        for u in range(5):
            t = u / 4
            r = 0.2 + 0.78 * t
            w = 0.2 * math.sin(math.pi * min(1.0, t * 1.1)) + 0.01
            z = 0.12 + 0.75 * math.sin(t * 2.2) * (1 - 0.35 * t)
            filas.append([(r * c + s * w, 0.3 + r * s - c * w, z - 0.04), (r * c, 0.3 + r * s, z + 0.03), (r * c - s * w, 0.3 + r * s + c * w, z - 0.04)])
        d.superficie(filas, 0.04, "piel_planta")


@modelo("vegetacion", "vegetacion", (2, 2, 2), "Planta con base bulbosa de la que salen cuatro tentáculos cortos.")
def planta_tentaculo(M):
    rnd = M.rnd
    M.mat("bulbo", "piel_purpura", a="#5A2468", b="#1E3A2A", rug=0.45, manchas=dict(color=VERDE, esc=2.2, radio=0.16, emis=0.7))
    M.mat("tentaculo", "carne_palida", a="#9A5A8A", b="#4A2458")
    p = M.pieza("planta", tris=3300, res=180, k=0.08, ruido=(0.02, 2.5), suelo=0.0)
    p.esfera((0, 0, 0.5), 1, "bulbo", esc=(0.7, 0.7, 0.62))
    for j in range(7):  # gajos del bulbo
        a = math.tau * j / 7
        p.esfera((0.5 * math.cos(a), 0.5 * math.sin(a), 0.42), 0.34, "bulbo", esc=(0.8, 0.8, 1.3), k=0.1)
    p.toro((0, 0, 1.02), 0.3, 0.12, "carne_viva", k=0.06)
    p.esfera((0, 0, 1.1), 0.25, "negro", resta=True, k=0.04)
    for j in range(4):
        a = math.tau * j / 4 + 0.5
        c, s = math.cos(a), math.sin(a)
        giro = 0.5 if j % 2 else -0.5
        pts = [(0.12 * c, 0.12 * s, 0.95), (0.3 * c, 0.3 * s, 1.55), (0.72 * c, 0.72 * s, 1.85),
               (0.95 * math.cos(a + giro * 0.5), 0.95 * math.sin(a + giro * 0.5), 1.5), (0.8 * math.cos(a + giro), 0.8 * math.sin(a + giro), 1.15)]
        p.tubo(pts, [0.15, 0.14, 0.11, 0.08, 0.04], "tentaculo", suave=12, k=0.04)
    for j in range(5):  # raicillas
        a = math.tau * j / 5
        p.tubo([(0.5 * math.cos(a), 0.5 * math.sin(a), 0.2), (0.85 * math.cos(a), 0.85 * math.sin(a), 0.05), (1.0 * math.cos(a + 0.3), 1.0 * math.sin(a + 0.3), 0)],
               [0.1, 0.08, 0.04], "bulbo", k=0.05)
    d = p.duro
    for j in range(4):  # ventosas en la cara interior de cada tentáculo
        a = math.tau * j / 4 + 0.5
        c, s = math.cos(a), math.sin(a)
        for (r, z, rr) in ((0.2, 1.3, 0.05), (0.42, 1.62, 0.045)):
            d.toro((r * c - c * 0.12, r * s - s * 0.12, z + 0.02), rr, 0.02, "carne_palida", eje=(-c, -s, 0.4), n=6, m=3)
