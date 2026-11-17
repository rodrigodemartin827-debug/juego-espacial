"""Ronda 10: terreno y formaciones (91-100)."""

import math

import numpy as np

from lib import VERDE, VIOLETA, curva, modelo

NEON_V = dict(material="Neon", color=VIOLETA)


@modelo("terreno", "prop", (4, 3, 3), "Roca negra y púrpura irregular, con venas de energía.")
def roca_alien_a(M):
    rnd = M.rnd

    def forma(p, mat, infla=0.0, **kw):
        p.esfera((0, 0, 0.9), 1, mat, esc=(1.6, 1.2, 1.5), rot=(0, 12, 20), infla=infla, **kw)
        p.esfera((-0.9, 0.2, 0.5), 1, mat, esc=(1.0, 0.9, 0.9), infla=infla, **kw)
        p.esfera((0.9, -0.3, 0.6), 1, mat, esc=(0.9, 0.8, 1.1), rot=(0, -20, 0), infla=infla, **kw)
        p.esfera((0.3, 0.5, 1.9), 1, mat, esc=(0.7, 0.6, 0.9), rot=(15, 10, 0), infla=infla, **kw)

    p = M.pieza("roca", tris=1500, res=150, k=0.25, ruido=(0.1, 1.1, 4), suelo=0.0)
    forma(p, "piedra")
    for (x, y, z, r) in ((1.3, 0.6, 1.3, 0.8), (-1.2, -0.7, 1.4, 0.9), (0.2, -1.2, 2.2, 0.8), (-0.5, 1.0, 2.3, 0.7)):   # tajos planos
        p.caja((x * 1.5, y * 1.5, z + 0.9), (1.6, 1.6, 1.6), None, rot=(rnd.uniform(-30, 30), rnd.uniform(20, 50), rnd.uniform(0, 90)), resta=True, k=0.05)
    # Venas: una cáscara fina pegada a la roca, recortada por láminas que la cruzan. Quedan líneas que rodean la piedra.
    n = M.pieza("venas_neon", tris=480, res=200, k=0.02, ruido=(0.03, 2.2), suelo=0.0, roblox=NEON_V)
    forma(n, "neon_violeta", infla=0.07)
    forma(n, None, infla=-0.02, resta=True)
    with n.mascara():
        for (c, rot) in (((0, 0, 1.0), (62, 18, 10)), ((0.2, 0.1, 1.2), (80, -35, 70)), ((-0.3, 0, 0.9), (20, 70, -30)), ((0.5, -0.2, 1.4), (-40, 50, 120))):
            n.caja(c, (7, 7, 0.05), "neon_violeta", rot=rot)
        n.caja((0, 0, 1.2), (7, 7, 0.04), "neon_violeta", rot=(8, -12, 0))
    M.notas["venas"] = "venas_neon sigue la superficie de la roca: asoma a trozos, donde la piedra no la tapa."


@modelo("terreno", "prop", (2, 2, 8), "Formación rocosa alta en aguja, de obsidiana, con cristales.")
def roca_alien_b(M):
    rnd = M.rnd
    b = M.pieza("pie", tris=500, res=90, k=0.15, ruido=(0.06, 1.6), suelo=0.0)
    for j in range(6):
        a = math.tau * j / 6
        b.esfera((0.55 * math.cos(a), 0.55 * math.sin(a), 0.1), rnd.uniform(0.3, 0.45), "piedra")
    p = M.pieza("aguja", tris=0, angulo=30)
    d = p.duro
    d.prisma((0, 0, 0), (0.12, 0.08, 8.0), 0.55, "obsidiana", n=5, punta=0.42, r2=0.36, giro=0.3)
    d.prisma((0.36, 0.1, 0), (0.6, 0.3, 4.6), 0.36, "obsidiana", n=5, punta=0.35, r2=0.22, giro=1.0)
    d.prisma((-0.3, -0.2, 0), (-0.55, -0.42, 3.3), 0.33, "obsidiana", n=4, punta=0.4, r2=0.2, giro=0.2)
    d.prisma((-0.1, 0.36, 0), (-0.2, 0.7, 2.2), 0.26, "obsidiana", n=4, punta=0.45, giro=0.7)
    d.prisma((0.2, -0.36, 0), (0.42, -0.72, 1.5), 0.22, "obsidiana", n=5, punta=0.5)
    c = M.pieza("cristales_neon", tris=0, angulo=25, roblox=NEON_V)
    for (z, a, L) in ((1.9, 0.5, 0.7), (3.0, 2.4, 0.9), (4.1, 4.4, 0.75), (5.0, 1.3, 0.6), (5.9, 3.5, 0.5), (2.5, 5.4, 0.6)):
        r0 = 0.48 - 0.035 * z
        base = np.array([r0 * math.cos(a) + 0.015 * z, r0 * math.sin(a) + 0.01 * z, z])
        dire = np.array([math.cos(a), math.sin(a), 0.7])
        c.duro.prisma(base - dire * 0.1, base + dire * L, 0.1, "cristal", n=5, punta=0.4, giro=z)
        c.duro.prisma(base - dire * 0.05, base + (dire + [0.3, -0.3, -0.5]) * L * 0.5, 0.06, "cristal", n=4, punta=0.5)


@modelo("terreno", "prop", (3, 3, 3), "Roca que levita, con energía debajo.", ancla="centro")
def roca_flotante(M):
    rnd = M.rnd
    p = M.pieza("roca", tris=1350, res=140, k=0.2, ruido=(0.12, 1.2, 4))
    p.esfera((0, 0, 2.2), 1, "piedra", esc=(1.4, 1.3, 0.75))
    p.tubo([(0, 0, 2.1), (0.1, 0.05, 1.5), (-0.05, 0, 1.0)], [1.0, 0.6, 0.2], "piedra_venas")   # raigón de abajo
    p.esfera((0.6, 0.4, 2.7), 0.5, "piedra")
    p.esfera((-0.6, -0.3, 2.65), 0.42, "piedra")
    p.caja((0.2, 0.1, 3.42), (3.2, 3.2, 0.9), None, rot=(4, -5, 0), resta=True, k=0.05)   # cima aplanada
    f = M.pieza("fragmentos", tris=300, res=70, k=0.05, ruido=(0.04, 3.0), unir="roca")
    for (x, y, z, r) in ((0.9, -0.5, 1.2, 0.2), (-0.8, 0.6, 1.0, 0.16), (0.3, 0.9, 0.7, 0.13), (-0.5, -0.8, 0.62, 0.11)):
        f.esfera((x, y, z), r, "piedra", esc=(1, 0.8, 1.2))
    n = M.pieza("energia_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA, transparencia=0.15))
    d = n.duro
    d.torno([(0, 0.0), (0.12, 0.2), (0.3, 0.7), (0.2, 0.95), (0, 0.9)], (-0.03, 0, 0.0), "neon_violeta", n=8)   # dardo de energía bajo la roca
    for k_, (z, R) in enumerate(((0.85, 0.75), (0.5, 0.55), (0.2, 0.34))):   # anillos de empuje
        d.toro((0, 0, z), R, 0.05, "neon_violeta", n=14, m=4, esc=(1, 1, 0.6))
    for j in range(4):
        a = math.tau * j / 4 + 0.6
        d.tubo([(0.4 * math.cos(a), 0.4 * math.sin(a), 1.6), (0.6 * math.cos(a + 0.5), 0.6 * math.sin(a + 0.5), 1.2), (0.3 * math.cos(a + 1.1), 0.3 * math.sin(a + 1.1), 0.8)],
               [0.05, 0.04, 0.0], "neon_violeta", n=4, suave=5)


@modelo("terreno", "vegetacion", (8, 8, 0.6), "Placa de suelo orgánico: superficie de carne y membrana, visceral.")
def suelo_carne(M):
    rnd = M.rnd
    p = M.pieza("placa", tris=3900, res=250, k=0.14, ruido=(0.03, 1.5), suelo=0.0)
    p.caja((0, 0, 0.12), (8.0, 8.0, 0.36), "carne", red=0.05, k=0.0)
    # Haces de músculo en diagonal y circunvoluciones tipo intestino entre ellos.
    for i in range(7):
        o = -4.2 + i * 1.4
        pts = [(max(-3.8, min(3.8, o + t * 2.4 + 0.3 * math.sin(t * 3 + i))), max(-3.8, min(3.8, -3.8 + t * 7.6)), 0.3) for t in np.linspace(0, 1, 9)]
        p.tubo(pts, [0.3, 0.42, 0.36, 0.45, 0.3], "musculo")
    for j in range(5):
        x, y = rnd.uniform(-2.8, 2.8), rnd.uniform(-2.8, 2.8)
        pts = [(max(-3.75, min(3.75, x + 0.75 * math.sin(t * 5.0 + j) + 0.5 * t)), max(-3.75, min(3.75, y + 0.75 * math.cos(t * 4.0 + j * 2) - 0.5 * t)), 0.4) for t in np.linspace(0, 1.6, 12)]
        p.tubo(pts, 0.2, "carne_viva", suave=24, k=0.06)
    for j in range(10):   # poros/esfínteres
        x, y = rnd.uniform(-3.4, 3.4), rnd.uniform(-3.4, 3.4)
        r = rnd.uniform(0.18, 0.3)
        p.toro((x, y, 0.42), r, r * 0.42, "carne_palida", k=0.06)
        p.esfera((x, y, 0.5), r * 0.7, "negro", resta=True, k=0.03)


@modelo("terreno", "vegetacion", (8, 8, 0.5), "Placa de suelo de huesos: fragmentos de hueso compactados.")
def suelo_hueso(M):
    rnd = M.rnd
    p = M.pieza("placa", tris=3950, res=250, k=0.05, ruido=(0.025, 1.8), suelo=0.0)
    p.caja((0, 0, 0.1), (8.0, 8.0, 0.3), "tierra", red=0.04, k=0.0)
    for j in range(95):
        x, y = rnd.uniform(-3.7, 3.7), rnd.uniform(-3.7, 3.7)
        a = rnd.uniform(0, math.tau)
        mat = rnd.choice(("hueso", "hueso", "hueso_viejo"))
        tipo = rnd.random()
        L = rnd.uniform(0.4, 1.1)
        dx, dy = L * math.cos(a) / 2, L * math.sin(a) / 2
        cl = lambda v: max(-3.82, min(3.82, v))
        if tipo < 0.5:      # hueso largo con sus cabezas
            r = rnd.uniform(0.08, 0.14)
            p.tubo([(cl(x - dx), cl(y - dy), 0.27), (x, y, 0.3), (cl(x + dx), cl(y + dy), 0.27)], [r * 1.5, r, r * 1.4], mat)
        elif tipo < 0.75:   # costilla curvada
            p.tubo([(cl(x - dx), cl(y - dy), 0.26), (cl(x + dy * 0.6), cl(y - dx * 0.6), 0.3), (cl(x + dx), cl(y + dy), 0.26)], [0.07, 0.1, 0.05], mat, suave=6)
        elif tipo < 0.92:   # vértebra o esquirla
            p.esfera((x, y, 0.27), rnd.uniform(0.14, 0.22), mat, esc=(1, 0.8, 0.6), rot=(0, 0, math.degrees(a)))
        else:               # calota de cráneo medio enterrada
            p.esfera((cl(x * 0.9), cl(y * 0.9), 0.22), 0.36, mat, esc=(1, 1.15, 0.62), rot=(0, 0, math.degrees(a)))
            p.esfera((cl(x * 0.9) + 0.2 * math.cos(a), cl(y * 0.9) + 0.2 * math.sin(a), 0.36), 0.1, "negro", resta=True, k=0.02)


@modelo("terreno", "mediana", (10, 8, 0.5), "Lago de ácido: superficie verde brillante que burbujea, con orilla de roca.")
def lago_acido(M):
    rnd = M.rnd

    def orilla(a):
        return 4.3 * (1 + 0.1 * math.sin(3 * a + 1) + 0.06 * math.sin(5 * a)), 3.4 * (1 + 0.1 * math.cos(2 * a) + 0.05 * math.sin(7 * a))

    p = M.pieza("orilla", tris=4600, res=250, k=0.14, ruido=(0.05, 1.3), suelo=0.0)
    for j in range(40):
        a = math.tau * j / 40
        rx, ry = orilla(a)
        s = rnd.uniform(0.36, 0.62)
        p.esfera((rx * math.cos(a) * 1.04, ry * math.sin(a) * 1.04, 0.05), s, "piedra" if j % 4 else "piedra_venas", esc=(1.1, 1.1, rnd.uniform(0.5, 0.85)))
    for (x, y, r) in ((1.2, 0.6, 0.5), (-2.0, -0.9, 0.42), (2.6, -1.2, 0.3)):   # islotes
        p.esfera((x, y, 0.05), r, "piedra", esc=(1, 1, 0.75))
    for j in range(5):   # costras de mineral en la orilla
        a = j * 1.3 + 0.3
        rx, ry = orilla(a)
        p.duro.cuerno([(rx * math.cos(a) * 1.1, ry * math.sin(a) * 1.1, 0.2), (rx * math.cos(a) * 1.14, ry * math.sin(a) * 1.14, 0.42), (rx * math.cos(a) * 1.06, ry * math.sin(a) * 1.06, 0.52)], 0.12, "garra", n=5, seg=2)
    n = M.pieza("acido_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    d = n.duro
    cont = []
    for j in range(28):
        a = math.tau * j / 28
        rx, ry = orilla(a)
        cont.append((rx * math.cos(a), ry * math.sin(a), 0.16))
    d.lamina(cont, 0.2, "acido", bombeo=0.03)
    for j in range(22):   # burbujas
        a, r = rnd.uniform(0, math.tau), 0.85 * math.sqrt(rnd.random())
        rx, ry = orilla(a)
        d.esfera((rx * r * math.cos(a), ry * r * math.sin(a), 0.27), rnd.uniform(0.1, 0.24), "acido", sub=1, esc=(1, 1, 0.8))
    for j in range(4):    # ondas: anillos donde ha reventado una burbuja
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.2, 0.6)
        rx, ry = orilla(a)
        d.toro((rx * r * math.cos(a), ry * r * math.sin(a), 0.275), rnd.uniform(0.25, 0.4), 0.025, "acido", n=10, m=3)


@modelo("terreno", "prop", (2, 2, 3), "Géiser que escupe gas tóxico: agujero con vapor verde saliendo.")
def geyser_toxico(M):
    rnd = M.rnd
    M.mat("costra", "piedra", a="#3A3A22", b="#1E1A22", rug=0.8, manchas=dict(color="#8AA02A", esc=3.0, radio=0.25))
    p = M.pieza("geiser", tris=1150, res=150, k=0.08, ruido=(0.04, 2.0), suelo=0.0)
    p.torno([(0, 0), (1.0, 0), (0.85, 0.25), (0.55, 0.7), (0.4, 1.15), (0.32, 1.3), (0.2, 1.3), (0.16, 0.9), (0, 0.8)], (0, 0, 0), "costra")
    for (z, R) in ((0.26, 0.86), (0.62, 0.6), (1.0, 0.44), (1.28, 0.32)):   # terrazas de mineral
        p.toro((0, 0, z), R, 0.085, "costra", k=0.05)
    for j in range(6):
        a = math.tau * j / 6
        p.esfera((0.9 * math.cos(a), 0.9 * math.sin(a), 0.05), rnd.uniform(0.14, 0.22), "piedra")
    v = M.pieza("vapor_neon", tris=800, res=130, k=0.1, ruido=(0.05, 2.5), roblox=dict(material="Neon", color=VERDE, transparencia=0.5))
    M.mat("vapor", "neon_verde", a="#2AC81E", b="#0F7A2A", emis=(VERDE, 0.45))
    x = y = 0.0
    for i in range(8):
        z = 1.2 + i * 0.23
        v.esfera((x, y, z), 0.13 + 0.022 * i + 0.04 * math.sin(i * 2.0), "vapor", esc=(1, 1, 0.8))
        x += rnd.uniform(-0.14, 0.17)
        y += rnd.uniform(-0.15, 0.15)
    for (dx, dy, z, r) in ((0.42, 0.1, 2.75, 0.17), (-0.36, 0.25, 2.5, 0.14), (0.1, -0.4, 2.2, 0.11), (-0.3, -0.2, 2.9, 0.1), (0.36, -0.25, 1.75, 0.08)):
        v.esfera((x * 0.6 + dx, y * 0.6 + dy, z), r, "vapor", esc=(1.2, 1, 0.75))   # jirones sueltos


@modelo("terreno", "mediana", (6, 4, 5), "Entrada de cueva natural: arco de roca con estalactitas.")
def cueva_entrada_natural(M):
    rnd = M.rnd
    p = M.pieza("cueva", tris=6800, res=190, k=0.3, ruido=(0.16, 0.8, 4), suelo=0.0)
    p.esfera((0, 0.3, 0), 1, "piedra", esc=(3.0, 2.0, 4.9))
    p.esfera((-1.9, 0.5, 0), 1, "piedra", esc=(1.4, 1.6, 2.6))
    p.esfera((2.0, 0.4, 0), 1, "piedra", esc=(1.3, 1.5, 3.2))
    p.esfera((0.6, 0.9, 3.6), 1, "piedra", esc=(1.5, 1.1, 1.2))
    p.capsula((0, -3.0, 0.2), (0.3, 3.0, 0.6), 1.55, "piedra_venas", resta=True, k=0.4)       # el túnel
    p.esfera((0, -1.7, 1.2), 1, "piedra_venas", esc=(2.0, 1.2, 2.4), resta=True, k=0.4)    # boca abocinada
    d = p.duro
    for j in range(11):   # estalactitas en el dintel
        x = -1.5 + j * 0.3 + rnd.uniform(-0.08, 0.08)
        y = rnd.uniform(-1.5, -0.3)
        techo = 1.5 + 1.8 * math.sqrt(max(0.05, 1 - (x / 1.9) ** 2))
        L = rnd.uniform(0.4, 1.2)
        d.cuerno([(x, y, techo + 0.5), (x + rnd.uniform(-0.05, 0.05), y, techo - L * 0.4), (x, y, techo - L)], rnd.uniform(0.1, 0.19), "piedra", n=5, seg=3)
    for j in range(5):    # estalagmitas a los lados
        x = rnd.choice((-1, 1)) * rnd.uniform(1.0, 1.5)
        y = rnd.uniform(-1.9, 0.5)
        L = rnd.uniform(0.4, 1.0)
        d.cuerno([(x, y, -0.05), (x, y, L * 0.6), (x * 0.97, y, L)], rnd.uniform(0.12, 0.2), "piedra", n=5, seg=3)
    n = M.pieza("hongos_biolum", tris=0, roblox=NEON_V)
    for j in range(9):    # hongos de luz pegados a la pared del túnel, mirando hacia dentro
        a = 0.2 + j * 0.34
        y = -0.5 + 0.5 * (j % 3)
        cz = 0.2 + (y + 3.0) / 6.0 * 0.4
        cx = 0.3 * (y + 3.0) / 6.0
        dentro = np.array([-math.cos(a), 0, -math.sin(a)])
        b = np.array([cx + 1.62 * math.cos(a), y, cz + 1.62 * math.sin(a)])
        n.duro.torno([(0, -0.15), (0.1, 0.0), (0.17, 0.1), (0.09, 0.2), (0, 0.23)], b, "neon_violeta", n=6, eje=dentro)


@modelo("terreno", "mediana", (4, 4, 8), "Columnas de basalto hexagonales alienígenas, negras con vetas púrpura.")
def columna_basalto_alien(M):
    rnd = M.rnd
    M.mat("basalto", "piedra_venas", a="#121018", b="#221A2C", rug=0.6, relieve=0.5, venas=dict(color=VIOLETA, esc=0.5, ancho=0.03, hondo=-0.4, emis=0.9))
    p = M.pieza("columnas", tris=5600, res=210, k=0.02, ruido=(0.012, 2.5), suelo=0.0)
    R = 0.62
    hexa = [(R * math.cos(math.tau * i / 6), R * math.sin(math.tau * i / 6)) for i in range(6)]
    celdas = []
    for q in range(-3, 4):
        for r in range(-3, 4):
            x = R * 1.5 * q
            y = R * math.sqrt(3) * (r + q / 2)
            dist = math.hypot(x, y)
            if dist > 1.75:
                continue
            alto = max(0.6, 7.9 - dist * 2.6 + rnd.uniform(-1.3, 0.8)) if (q, r) != (0, 0) else 7.9
            celdas.append((x, y, alto))
    for x, y, alto in celdas:
        p.extrusion(hexa, alto + 0.5, (x, y, alto / 2 - 0.25), "basalto", red=0.035, rot=(0, 0, 0))
        if rnd.random() < 0.45:   # junta horizontal: la columna está partida en tambores
            zc = alto * rnd.uniform(0.35, 0.7)
            p.toro((x, y, zc), R * 0.98, 0.04, None, resta=True)
    p.esfera((0, 0, 0), 1, "piedra", esc=(1.9, 1.9, 0.36), k=0.1)
    c = M.pieza("cristales_neon", tris=0, angulo=25, roblox=NEON_V)
    for j in range(6):
        x, y, alto = celdas[(j * 5 + 2) % len(celdas)]
        if alto > 7:
            continue
        c.duro.prisma((x, y, alto - 0.05), (x + rnd.uniform(-0.2, 0.2), y + rnd.uniform(-0.2, 0.2), alto + rnd.uniform(0.3, 0.6)), 0.12, "cristal", n=5, punta=0.5)


@modelo("terreno", "mediana", (4, 4, 5), "Mini volcán que burbujea lava púrpura, con el cráter arriba.")
def volcan_pequeno(M):
    rnd = M.rnd

    def cono(p, mat, infla=0.0):
        p.torno([(0, 0), (2.0, 0), (1.6, 0.9), (1.05, 2.6), (0.72, 4.0), (0.6, 4.6), (0, 4.6)], (0, 0, 0), mat, infla=infla)

    p = M.pieza("volcan", tris=5200, res=170, k=0.15, ruido=(0.1, 1.2, 4), suelo=0.0)
    cono(p, "piedra")
    p.torno([(0, 3.5), (0.3, 3.7), (0.5, 4.4), (0.6, 5.0), (0, 5.0)], (0, 0, 0), "piedra_venas", resta=True, k=0.1)   # cráter
    for j in range(7):   # contrafuertes de lava vieja
        a = math.tau * j / 7 + 0.2
        p.tubo([(0.75 * math.cos(a), 0.75 * math.sin(a), 3.6), (1.3 * math.cos(a + 0.15), 1.3 * math.sin(a + 0.15), 1.8), (2.0 * math.cos(a + 0.3), 2.0 * math.sin(a + 0.3), 0.1)],
               [0.24, 0.36, 0.5], "piedra", k=0.25)
    for j in range(6):   # dientes del borde del cráter
        a = math.tau * j / 6 + 0.5
        p.tubo([(0.6 * math.cos(a), 0.6 * math.sin(a), 4.4), (0.7 * math.cos(a), 0.7 * math.sin(a), 4.95)], [0.2, 0.07], "piedra", k=0.08)
    n = M.pieza("lava_neon", tris=1900, res=160, k=0.05, ruido=(0.03, 2.0), suelo=0.0, roblox=NEON_V)
    cono(n, "lava_purpura", infla=0.13)
    with n.mascara():
        for (a, largo) in ((0.4, 1.0), (2.3, 0.7), (4.3, 0.85), (5.5, 0.45)):   # coladas que bajan por la ladera
            pts = []
            for t in np.linspace(0, largo, 8):
                r = 0.55 + 1.5 * t ** 1.2
                z = 4.7 - 4.7 * t
                an = a + 0.3 * math.sin(t * 5 + a)
                pts.append((r * math.cos(an), r * math.sin(an), z))
            n.tubo(pts, [0.32, 0.28, 0.24, 0.2, 0.26], "lava_purpura")
    n.torno([(0, 3.9), (0.42, 3.95), (0.5, 4.36), (0.3, 4.42), (0, 4.45)], (0, 0, 0), "lava_purpura")       # el lago del cráter
    for j in range(5):
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.05, 0.3)
        n.duro.esfera((r * math.cos(a), r * math.sin(a), 4.43), rnd.uniform(0.07, 0.14), "lava_purpura", sub=1)
    n.duro.tubo([(0.1, 0, 4.45), (0.2, 0.1, 4.9), (0.36, 0.2, 5.0)], [0.06, 0.04, 0.0], "lava_purpura", n=4)   # salpicadura
    n.duro.esfera((0.42, 0.24, 4.98), 0.05, "lava_purpura", sub=1)
