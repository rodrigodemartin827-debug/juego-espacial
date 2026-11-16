"""Ronda 5: bestias cósmicas (41-50). Todas miran a -Y y van por piezas rígidas con sus articulaciones."""

import math

import numpy as np

from formas import silla
from lib import AMARILLO, ROJO, VERDE, VIOLETA, curva, modelo

NEON_V = dict(material="Neon", color=VIOLETA)


@modelo("bestias", "bestia", (20, 24, 6), "Mantarraya cósmica gigante: cuerpo plano de alas enormes, piel púrpura "
        "oscura con dibujos bioluminiscentes violeta y cola larga con aguijón. La bestia más común. 3 asientos.")
def bestia_mantarraya(M):
    M.mat("piel_manta", "piel_purpura", a="#3A1C58", b="#150A22", rug=0.42)
    M.mat("panza", "carne_palida", a="#8A6A9A", b="#4A2A5A")
    Z = 2.4

    def cuerpo(p, mat, infla=0.0):
        p.esfera((0, 0, Z), 1, mat, esc=(2.9, 5.6, 1.25), infla=infla)
        p.esfera((0, -4.2, Z - 0.1), 1, mat, esc=(2.3, 2.4, 0.95), infla=infla)
        p.esfera((0, 4.2, Z), 1, mat, esc=(1.5, 2.6, 0.8), infla=infla)

    def ala(p, s, mat, infla=0.0):
        p.esfera((s * 4.4, 0.4, Z + 0.1), 1, mat, esc=(3.6, 4.7, 0.55), rot=(0, -s * 7, s * 8), infla=infla)
        p.esfera((s * 7.4, 1.3, Z + 0.8), 1, mat, esc=(2.7, 3.1, 0.38), rot=(0, -s * 20, s * 16), infla=infla)
        p.esfera((s * 9.3, 2.3, Z + 1.75), 1, mat, esc=(1.4, 1.7, 0.24), rot=(0, -s * 38, s * 22), infla=infla)

    c = M.pieza("cuerpo", tris=4600, res=190, k=0.5, ruido=(0.035, 0.9))
    cuerpo(c, "piel_manta")
    c.esfera((0, -1.0, Z - 0.75), 1, "panza", esc=(2.2, 4.6, 0.6))
    for s in (-1, 1):  # aletas cefálicas (los «cuernos» de la manta)
        c.tubo([(s * 1.5, -5.4, Z - 0.1), (s * 2.0, -7.0, Z - 0.3), (s * 1.5, -8.2, Z - 0.6), (s * 0.8, -8.5, Z - 0.9)],
               [0.62, 0.5, 0.36, 0.16], "piel_manta", suave=8, k=0.3)
        c.esfera((s * 2.25, -4.6, Z + 0.25), 0.42, "piel_manta", k=0.2)       # bulto del ojo
        c.esfera((s * 2.5, -4.75, Z + 0.3), 0.26, "negro", resta=True, k=0.05)
    c.esfera((0, -6.3, Z - 0.45), 1, "carne_viva", esc=(1.35, 0.9, 0.3), resta=True, k=0.1)  # boca
    for i in range(5):  # branquias por debajo
        c.caja((0, -3.2 + i * 0.5, Z - 1.25), (2.2 - i * 0.2, 0.12, 0.4), "carne_viva", red=0.05, resta=True, k=0.03)
    for i in range(9):  # cresta de vértebras
        y = -3.6 + i * 1.0
        if abs(y + 1.9) < 0.6 or abs(y - 0.3) < 0.6 or abs(y - 2.5) < 0.6:
            continue
        c.esfera((0, y, Z + 1.22 - 0.012 * y * y), 0.26, "hueso", esc=(0.8, 1.2, 1), k=0.1)
    for y in (-1.9, 0.3, 2.5):
        silla(M, c, (0, y, Z + 1.3 - 0.012 * y * y), s=0.95)
    cn = M.pieza("cuerpo_neon", tris=1100, res=150, roblox=NEON_V)
    cuerpo(cn, "neon_violeta", infla=0.07)
    with cn.mascara():
        for s in (-1, 1):
            cn.tubo([(s * 1.5, y, Z + 0.4 + 0.25 * math.sin(i)) for i, y in enumerate(np.linspace(-4.5, 5.5, 10))], 0.13, "neon_violeta")
            cn.tubo([(s * 1.5, y, Z + 1.6) for y in np.linspace(-4.5, 5.5, 10)], 0.13, "neon_violeta")
            for i in range(6):
                cn.capsula((s * (0.75 + 0.1 * (i % 2)), -3.3 + i * 1.5, Z), (s * 0.75, -3.3 + i * 1.5, Z + 2), 0.16, "neon_violeta")
    cn.duro.esfera((2.42, -4.72, Z + 0.3), 0.2, "neon_violeta", sub=1, sim=True)  # ojos
    for s, nombre in ((-1, "ala_izq"), (1, "ala_der")):
        a = M.pieza(nombre, tris=3000, res=170, k=0.9, ruido=(0.03, 0.9))
        ala(a, s, "piel_manta")
        for j in range(4):  # radios cartilaginosos que se marcan en la piel
            a.tubo([(s * 2.6, -2.5 + j * 1.8, Z + 0.35), (s * 6.3, -1.0 + j * 1.5, Z + 0.95), (s * 9.2, 1.4 + j * 0.7, Z + 1.9)], [0.2, 0.15, 0.07],
                   "piel_manta", k=0.25)
        an = M.pieza(nombre + "_neon", tris=1000, res=140, roblox=NEON_V)
        ala(an, s, "neon_violeta", infla=0.07)
        with an.mascara():
            for j in range(3):  # arcos de luz que siguen la curva del ala
                R = 3.0 + j * 2.2
                pts = [(s * (2.0 + R * math.cos(t)), -0.5 + 1.2 * R * math.sin(t) * 0.55 + j * 0.5, Z + 0.3 + j * 0.5) for t in np.linspace(-1.0, 1.0, 9)]
                an.tubo(pts, 0.5, "neon_violeta")
                an.tubo(pts, 0.34, "neon_violeta", resta=True)
            for j in range(7):  # lunares
                x, y = s * (3.2 + j * 0.95), -2.2 + 0.55 * j + 1.6 * math.sin(j * 2.2)
                an.capsula((x, y, Z - 0.2), (x, y, Z + 3.4), 0.2 + 0.08 * (j % 2), "neon_violeta")
            an.caja((s * 6, 0, Z - 2.0 + 0.3), (12, 16, 4.0), None, resta=True)  # solo por arriba
        M.articulacion(nombre, "cuerpo", (s * 2.3, 0.2, Z))
        M.articulacion(nombre + "_neon", nombre, (s * 2.3, 0.2, Z))
    t = M.pieza("cola", tris=1500, res=170, k=0.2, ruido=(0.02, 1.5))
    cola = curva([(0, 5.6, Z), (0, 9.0, Z + 0.2), (0, 12.5, Z + 1.3), (0, 15.2, Z + 3.0)], 14)
    t.tubo(cola, [0.75, 0.5, 0.3, 0.16], "piel_manta")
    for i in range(2, 13, 2):
        q = cola[i]
        t.duro.cono((0, q[1], q[2] + 0.3), (0, q[1] + 0.4, q[2] + 0.95 - i * 0.035), 0.14, "garra", n=5)
    t.duro.cuerno([cola[-1], (0, 15.9, Z + 3.5), (0, 16.3, Z + 2.9), (0, 16.0, Z + 2.0)], 0.3, "garra", n=6, seg=6, aplastar=0.5)
    M.articulacion("cola", "cuerpo", (0, 5.8, Z))
    M.articulacion("cuerpo_neon", "cuerpo", (0, 0, Z))


@modelo("bestias", "bestia", (6, 30, 6), "Gusano espacial enorme: cuerpo largo segmentado, boca con anillos de dientes y "
        "patas cortas en cada segmento. Transporte de tropas: 5 asientos y bahía de carga.")
def bestia_gusano(M):
    rnd = M.rnd
    M.mat("piel_gusano", "carne_palida", a="#9A6A7A", b="#5A2A4A", rug=0.45)
    Z = 3.3

    def tramo(p, y0, n, r0, r1, sillas=()):
        for i in range(n):
            t = i / max(1, n - 1)
            y = y0 + i * 2.15
            r = r0 + (r1 - r0) * t
            p.esfera((0, y, Z), 1, "piel_gusano", esc=(r, 1.45, r * 0.95))
            p.esfera((0, y, Z + r * 0.42), 1, "quitina", esc=(r * 0.8, 1.2, r * 0.62), k=0.15)   # placa dorsal
            for s in (-1, 1):  # pata corta con garra
                p.tubo([(s * r * 0.75, y, Z - r * 0.5), (s * r * 1.12, y - 0.1, Z - r * 0.95), (s * r * 1.0, y - 0.3, 0.25)], [0.42, 0.34, 0.2], "quitina", k=0.15)
                p.duro.cuerno([(s * r * 1.0, y - 0.3, 0.4), (s * r * 1.08, y - 0.6, 0.15), (s * r * 0.95, y - 0.85, 0.0)], 0.17, "garra", n=5, seg=3)
                p.duro.cono((s * r * 0.82, y, Z + r * 0.55), (s * r * 1.15, y + 0.2, Z + r * 1.0), 0.16, "garra", n=5)  # púa lateral
        for y in sillas:
            silla(M, p, (0, y, Z + r0 * 1.04 + 0.05), s=0.95)

    cab = M.pieza("cabeza", tris=3200, res=160, k=0.3, ruido=(0.04, 1.0))
    cab.esfera((0, -12.6, Z), 1, "piel_gusano", esc=(2.45, 2.3, 2.35))
    cab.esfera((0, -12.0, Z + 1.0), 1, "quitina", esc=(2.0, 1.9, 1.5), k=0.2)
    cab.torno([(0, -1.2), (1.2, -0.6), (1.9, 0.9), (2.0, 1.6), (0, 1.6)], (0, -13.2, Z), "carne_viva", eje=(0, -1, 0), resta=True, k=0.15)
    for i, (y, R) in enumerate(((-14.55, 2.05), (-13.9, 1.72), (-13.3, 1.36))):  # anillos de encía
        cab.toro((0, y, Z), R, 0.2, "carne" if i % 2 else "musculo", eje=(0, 1, 0), k=0.08)
        n = 16 - i * 3
        for j in range(n):  # anillo de dientes hacia dentro
            a = math.tau * (j + 0.5 * i) / n
            b = np.array([R * math.cos(a), y, Z + R * math.sin(a)])
            cab.duro.cono(b, b * [0.62, 1, 1] + [0, -0.25, (Z - b[2]) * 0.38], 0.15 - 0.02 * i, "diente", n=5)
    for j in range(4):  # ganchos mandibulares por fuera
        a = math.pi / 4 + j * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        cab.duro.cuerno([(2.0 * c, -13.4, Z + 2.0 * s), (2.9 * c, -15.2, Z + 2.9 * s), (1.5 * c, -16.4, Z + 1.5 * s)], 0.4, "garra", n=7, seg=6)
    on = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    for s in (-1, 1):
        for i in range(3):
            on.duro.esfera((s * (1.75 + 0.2 * i), -12.6 + i * 0.6, Z + 1.35 - 0.25 * i), 0.2 - 0.03 * i, "neon_verde", sub=1)
    M.articulacion("cabeza", "cuerpo_delantero", (0, -11.0, Z))
    M.articulacion("ojos_neon", "cabeza", (0, -12.6, Z))
    d = M.pieza("cuerpo_delantero", tris=3300, res=150, k=0.3, ruido=(0.04, 1.0))
    tramo(d, -10.2, 4, 2.4, 2.5, sillas=(-9.1, -4.8))
    m = M.pieza("cuerpo_medio", tris=3800, res=150, k=0.3, ruido=(0.04, 1.0))
    tramo(m, -1.6, 4, 2.5, 2.45, sillas=(-0.5,))
    # Bahía de carga: alforjas de cuero atadas con tendones al lomo del tramo medio.
    for s in (-1, 1):
        for y in (2.6, 4.6):
            m.esfera((s * 1.85, y, Z + 1.75), 1, "cuero", esc=(0.75, 0.95, 0.8), k=0.1)
            m.tubo([(s * 1.2, y, Z + 2.5), (s * 2.5, y, Z + 2.2), (s * 2.7, y, Z + 1.2)], 0.09, "tendon", k=0.03)
    m.caja((0, 3.6, Z + 2.55), (2.6, 3.4, 0.3), "hueso_viejo", red=0.1, k=0.1)
    M.bahia((0, 3.6, Z + 3.4), (2.6, 3.4, 1.4), "plataforma de hueso y cuatro alforjas en el tramo medio")
    t = M.pieza("cuerpo_trasero", tris=3300, res=150, k=0.3, ruido=(0.04, 1.0))
    tramo(t, 7.0, 3, 2.35, 1.9, sillas=(8.1, 10.2))
    c = M.pieza("cola", tris=1500, res=140, k=0.3, ruido=(0.04, 1.0))
    c.tubo([(0, 12.6, Z), (0, 14.4, Z - 0.2), (0, 16.0, Z + 0.3), (0, 16.9, Z + 1.2)], [1.75, 1.3, 0.8, 0.35], "piel_gusano", suave=8)
    c.tubo([(0, 12.8, Z + 0.9), (0, 14.4, Z + 0.55), (0, 15.8, Z + 0.9)], [1.2, 0.9, 0.5], "quitina", k=0.2)
    c.duro.cuerno([(0.5, 16.2, Z + 0.5), (1.4, 17.2, Z + 1.3), (0.9, 17.6, Z + 2.6)], 0.3, "garra", n=6, seg=5, sim=True)
    M.articulacion("cuerpo_medio", "cuerpo_delantero", (0, -2.7, Z))
    M.articulacion("cuerpo_trasero", "cuerpo_medio", (0, 5.9, Z))
    M.articulacion("cola", "cuerpo_trasero", (0, 12.3, Z))
    M.raiz = "cuerpo_delantero"


@modelo("bestias", "bestia", (18, 20, 14), "Dragón de asteroides: cuatro alas membranosas, cuerpo musculoso, cabeza con "
        "cuernos y boca que escupe energía verde. La bestia de combate de élite. 2 asientos (cuello y lomo).")
def bestia_dragon(M):
    rnd = M.rnd
    M.mat("piel_dragon", "piel", a="#2E1E3E", b="#120C1A", rug=0.55, escamas=dict(esc=3.2, fuerza=0.7))
    M.mat("panza", "carne", a="#6A2438", b="#3A1228")
    M.mat("ala_membrana", "membrana", a="#4A1E52", b="#1E0C2A")
    c = M.pieza("cuerpo", tris=3400, res=160, k=0.5, ruido=(0.04, 1.0))
    c.esfera((0, -1.4, 5.3), 1, "piel_dragon", esc=(2.3, 2.6, 2.3))     # pecho
    c.esfera((0, 1.6, 5.0), 1, "piel_dragon", esc=(1.9, 2.8, 1.9))
    c.esfera((0, 3.9, 4.8), 1, "piel_dragon", esc=(1.75, 1.9, 1.7))     # cadera
    c.esfera((0, 0.2, 3.9), 1, "panza", esc=(1.5, 3.6, 1.1))
    for s in (-1, 1):
        c.esfera((s * 1.7, -1.6, 5.9), 1.1, "piel_dragon", k=0.4)        # hombros
        c.esfera((s * 1.5, 3.9, 5.2), 1.0, "piel_dragon", k=0.4)
    for i in range(7):  # placas dorsales
        y = -2.6 + i * 1.15
        if abs(y - 0.4) < 0.9:
            continue
        c.duro.cuerno([(0, y, 7.2 - 0.07 * (y + 1) ** 2), (0, y + 0.3, 8.1 - 0.07 * (y + 1) ** 2), (0, y + 0.9, 8.4 - 0.08 * (y + 1) ** 2)], 0.3, "garra", n=5, seg=3, aplastar=0.45)
    silla(M, c, (0, 0.5, 7.25), s=1.0, nombre="asiento_lomo")
    # Cuello.
    n = M.pieza("cuello", tris=1500, res=140, k=0.3, ruido=(0.03, 1.2))
    cuello = curva([(0, -3.2, 6.3), (0, -4.6, 8.0), (0, -5.6, 9.4), (0, -6.6, 10.2)], 10)
    n.tubo(cuello, [1.5, 1.2, 1.0, 0.9], "piel_dragon")
    n.tubo([(0, -3.4, 5.4), (0, -4.6, 7.0), (0, -6.0, 9.3)], [0.9, 0.75, 0.6], "panza", k=0.3)
    for i in range(2, 10, 2):
        q = cuello[i]
        if i == 4:
            continue
        n.duro.cono((0, q[1] + 0.5, q[2] + 0.75), (0, q[1] + 1.2, q[2] + 1.6), 0.24, "garra", n=5)
    silla(M, n, (0, -4.25, 8.95), s=0.8, nombre="asiento_cuello")
    M.articulacion("cuello", "cuerpo", (0, -3.2, 6.2))
    # Cabeza.
    h = M.pieza("cabeza", tris=2300, res=160, k=0.2, ruido=(0.025, 1.6))
    H = np.array([0, -7.6, 10.5])
    with h.en(H, rot=(8, 0, 0)):
        h.esfera((0, 0, 0), 1, "piel_dragon", esc=(1.05, 1.3, 0.95))
        h.esfera((0, -1.5, -0.1), 1, "piel_dragon", esc=(0.75, 1.5, 0.6))       # hocico
        h.esfera((0, -2.7, 0.0), 0.5, "piel_dragon", esc=(1.1, 1, 0.8))        # punta
        h.tubo([(0.3, -1.6, 0.42), (0.8, -0.7, 0.75), (1.0, 0.2, 0.65)], [0.2, 0.3, 0.22], "quitina", sim=True)  # cejas
        h.esfera((0.78, -0.75, 0.38), 0.3, "negro", sim=True, resta=True, k=0.05)
        h.esfera((0.3, -2.95, 0.25), 0.12, "negro", sim=True, resta=True)
        h.esfera((0, -1.4, -0.75), 1, "carne_viva", esc=(0.55, 1.6, 0.4), resta=True, k=0.1)   # paladar
        d = h.duro
        d.cuerno([(0.6, 0.6, 0.6), (1.3, 1.6, 1.5), (1.1, 2.9, 2.6), (0.7, 3.2, 3.5)], 0.36, "garra", n=7, seg=7, sim=True)
        d.cuerno([(0.95, 0.3, 0.0), (1.6, 0.9, -0.1), (1.9, 1.9, 0.5)], 0.24, "garra", n=6, seg=5, sim=True)
        d.cuerno([(0, -2.6, 0.45), (0, -2.7, 0.9), (0, -2.3, 1.2)], 0.16, "garra", n=5, seg=3)
        for i in range(6):
            y = -0.5 - i * 0.42
            x = 0.62 - 0.03 * i
            d.cono((x, y, -0.45), (x * 1.02, y - 0.05, -0.95 - (0.25 if i in (4,) else 0)), 0.1, "diente", n=5, sim=True)
    on = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    with on.en(H, rot=(8, 0, 0)):
        on.duro.esfera((0.7, -0.72, 0.38), 0.2, "neon_verde", sub=1, sim=True)
    j = M.pieza("mandibula", tris=700, res=110, k=0.15, ruido=(0.02, 1.6))
    with j.en(H, rot=(26, 0, 0)):
        j.tubo([(0.8, 0.5, -0.5), (0.72, -0.8, -1.0), (0.4, -2.3, -1.0), (0, -2.75, -0.95)], [0.3, 0.28, 0.24, 0.26], "piel_dragon", sim=True)
        j.esfera((0, -1.1, -1.15), 1, "panza", esc=(0.6, 1.4, 0.25))
        for i in range(5):
            y = -0.9 - i * 0.42
            j.duro.cono((0.6 - 0.05 * i, y, -0.85), (0.6 - 0.05 * i, y - 0.03, -0.42 + (0.2 if i == 3 else 0)), 0.09, "diente", n=5, sim=True)
    M.articulacion("cabeza", "cuello", (0, -6.7, 10.2))
    M.articulacion("mandibula", "cabeza", (0, -7.0, 9.9))
    M.articulacion("ojos_neon", "cabeza", tuple(H))
    # Aliento: bola de energía en la garganta y lengua de llama.
    al = M.pieza("aliento_neon", tris=700, res=90, k=0.25, ruido=(0.06, 1.6), roblox=dict(material="Neon", color=VERDE, transparencia=0.15))
    al.esfera((0, -8.6, 9.75), 0.42, "fuego_verde")
    al.tubo([(0, -8.8, 9.7), (0, -10.2, 9.4), (0.1, -11.4, 9.2), (0, -12.6, 9.1)], [0.36, 0.5, 0.36, 0.1], "fuego_verde")
    al.tubo([(0, -10.0, 9.5), (-0.4, -11.0, 9.7), (-0.5, -11.8, 9.9)], [0.25, 0.2, 0.06], "fuego_verde")
    M.articulacion("aliento_neon", "cabeza", (0, -8.6, 9.75))
    # Cola.
    t = M.pieza("cola", tris=1500, res=150, k=0.2, ruido=(0.03, 1.2))
    cola = curva([(0, 5.0, 4.9), (0, 7.4, 4.0), (0, 9.6, 2.7), (0, 11.4, 2.4), (0, 12.6, 3.3)], 14)
    t.tubo(cola, [1.4, 1.0, 0.65, 0.42, 0.25], "piel_dragon")
    for i in range(1, 13, 2):
        q = cola[i]
        t.duro.cono((0, q[1], q[2] + 1.2 - i * 0.07), (0, q[1] + 0.6, q[2] + 1.9 - i * 0.1), 0.2, "garra", n=5)
    t.duro.lamina([(0, 12.4, 3.2), (0.7, 13.0, 3.9), (0, 14.3, 5.0), (-0.7, 13.0, 3.9)], 0.16, "garra", bombeo=0.1)
    M.articulacion("cola", "cuerpo", (0, 5.0, 4.9))
    # Patas.
    for s, lado in ((-1, "izq"), (1, "der")):
        for nombre, y0, alto in (("pata_del", -1.7, 4.6), ("pata_tras", 3.9, 4.4)):
            p = M.pieza(f"{nombre}_{lado}", tris=800, res=120, k=0.2, ruido=(0.025, 1.4))
            atras = 0.9 if "tras" in nombre else -0.3
            p.tubo([(s * 1.9, y0, alto), (s * 2.6, y0 + atras, 2.9), (s * 2.5, y0 - 0.4 + atras * 0.2, 1.3), (s * 2.6, y0 - 0.7, 0.4)],
                   [0.95, 0.75, 0.5, 0.45], "piel_dragon", suave=8)
            p.esfera((s * 2.6, y0 - 0.95, 0.3), 1, "piel_dragon", esc=(0.6, 0.85, 0.32))
            for k_ in (-1, 0, 1):
                p.duro.cuerno([(s * 2.6 + k_ * 0.36, y0 - 1.5, 0.35), (s * 2.6 + k_ * 0.45, y0 - 2.0, 0.42), (s * 2.6 + k_ * 0.5, y0 - 2.3, 0.0)], 0.16, "garra", n=5, seg=3)
            M.articulacion(f"{nombre}_{lado}", "cuerpo", (s * 1.8, y0, alto))
    # Cuatro alas: brazo y dedos de hueso con membrana de grosor real entre ellos.
    alas = [("ala_sup", (1.5, -0.8, 6.9), [(4.6, -0.6, 10.6), (8.6, 0.8, 13.6)], [(9.0, 3.4, 10.4), (7.2, 5.6, 8.4), (4.2, 5.6, 7.3)], (1.6, 2.6, 6.6)),
            ("ala_inf", (1.5, 2.6, 5.9), [(4.4, 3.2, 7.4), (7.9, 4.6, 8.3)], [(8.1, 7.2, 6.4), (6.2, 8.6, 5.3), (3.6, 7.6, 4.9)], (1.5, 4.6, 5.2))]
    for s, lado in ((-1, "izq"), (1, "der")):
        for nombre, raiz, brazo, dedos, cierre in alas:
            w = M.pieza(f"{nombre}_{lado}", tris=650, res=130, k=0.15, ruido=(0.02, 1.5))
            S = np.array([s, 1, 1])
            raiz_, codo, mano = np.array(raiz) * S, np.array(brazo[0]) * S, np.array(brazo[1]) * S
            w.tubo([raiz_, codo, mano], [0.55, 0.4, 0.26], "piel_dragon")
            w.esfera(codo, 0.5, "piel_dragon", k=0.15)
            w.duro.cuerno([mano, mano + [s * 0.5, -0.6, 0.7], mano + [s * 0.4, -1.3, 0.5]], 0.2, "garra", n=5, seg=3)  # garra del pulgar
            filas = [[raiz_ + (codo - raiz_) * min(1, t * 2) + (mano - codo) * max(0, t * 2 - 1) for t in np.linspace(0, 1, 6)]]
            for dd in dedos:
                dd = np.array(dd) * S
                w.tubo([mano, (mano + dd) / 2 + [0, 0, 0.3], dd], [0.2, 0.15, 0.06], "piel_dragon")
                # fila de la membrana: del arranque del ala a la punta del dedo, pasando cerca de la mano
                ini = raiz_ + (np.array(cierre) * S - raiz_) * (len(filas) / 4)
                filas.append([ini + (dd - ini) * (t ** 0.8) + np.array([0, 0, 1.0]) * math.sin(math.pi * t) * 0.5 for t in np.linspace(0, 1, 6)])
            filas.append([np.array(cierre) * S + (np.array(dedos[-1]) * S - np.array(cierre) * S) * t * 0.15 for t in np.linspace(0, 1, 6)])
            w.duro.superficie(filas, 0.09, "ala_membrana")
            M.articulacion(f"{nombre}_{lado}", "cuerpo", tuple(raiz_))


@modelo("bestias", "bestia", (12, 12, 18), "Medusa de nebulosa: campana translúcida con dibujos de luz púrpura y "
        "tentáculos largos que brillan. De exploración: 1 asiento dentro de la campana.")
def bestia_medusa(M):
    rnd = M.rnd
    M.mat("campana", "membrana", a="#6A3A9A", b="#2E1650", rug=0.2, venas=dict(color="#B07AE0", esc=1.2, ancho=0.03, hondo=0.3))
    M.mat("organo", "carne_viva", a="#A03A6A", b="#5A1A4A")
    ZC = 13.0
    perfil = [(0, 5.0), (2.4, 4.7), (4.4, 3.6), (5.6, 1.9), (6.0, 0.2), (5.7, -0.5), (5.3, -0.2), (5.1, 1.5), (4.0, 3.0), (2.2, 4.0), (0, 4.3)]

    def campana(p, mat, infla=0.0):
        p.torno(perfil, (0, 0, ZC), mat, infla=infla)

    b = M.pieza("campana_cristal", tris=4600, res=170, k=0.15, ruido=(0.03, 0.9),
                roblox=dict(material="Glass", color="#8A5AD0", transparencia=0.4))
    campana(b, "campana")
    for j in range(16):  # borde festoneado
        a = math.tau * j / 16
        b.esfera((5.75 * math.cos(a), 5.75 * math.sin(a), ZC - 0.45), 0.62, "campana", esc=(1, 1, 0.8), k=0.3)
    bn = M.pieza("patrones_neon", tris=1800, res=150, roblox=NEON_V)
    campana(bn, "neon_violeta", infla=0.06)
    with bn.mascara():
        for j in range(8):  # radios de luz y anillo de lunares
            a = math.tau * j / 8
            c, s = math.cos(a), math.sin(a)
            bn.tubo([(0.9 * c, 0.9 * s, ZC + 5.2), (3.0 * c, 3.0 * s, ZC + 4.6), (4.9 * c, 4.9 * s, ZC + 3.2), (5.9 * c, 5.9 * s, ZC + 1.0)], [0.16, 0.24, 0.2, 0.12], "neon_violeta")
            a2 = a + math.tau / 16
            bn.esfera((5.3 * math.cos(a2), 5.3 * math.sin(a2), ZC + 2.4), 0.5, "neon_violeta")
        bn.toro((0, 0, ZC + 4.9), 1.5, 0.22, "neon_violeta")
        bn.esfera((0, 0, ZC + 2.0), 1, None, esc=(5.2, 5.2, 3.3), resta=True)  # solo la cara de fuera
    M.articulacion("patrones_neon", "campana_cristal", (0, 0, ZC + 3))
    # Núcleo: estómago y gónadas dentro de la campana, con el asiento del jinete.
    n = M.pieza("nucleo", tris=2400, res=140, k=0.3, ruido=(0.04, 1.2))
    n.esfera((0, 0, ZC + 2.6), 1, "organo", esc=(2.0, 2.0, 1.5))
    for j in range(4):
        a = math.tau * j / 4 + math.pi / 4
        n.esfera((1.9 * math.cos(a), 1.9 * math.sin(a), ZC + 2.5), 1.0, "carne_palida", esc=(1, 1, 0.75))
    n.tubo([(0, 0, ZC + 1.6), (0, 0, ZC - 0.6), (0, 0, ZC - 2.0)], [1.3, 0.9, 1.1], "organo")   # manubrio
    n.torno([(0, -0.3), (1.5, -0.25), (1.75, 0.0), (1.5, 0.2), (0, 0.15)], (0, 0, ZC + 0.4), "carne", k=0.15)  # repisa
    silla(M, n, (0, -1.9, ZC + 0.75), s=0.8)
    M.articulacion("campana_cristal", "nucleo", (0, 0, ZC + 2.5))
    # Brazos orales: cuatro cintas gruesas y rizadas.
    o = M.pieza("brazos_orales", tris=3000, res=170, k=0.15, ruido=(0.03, 1.2))
    for j in range(4):
        a = math.tau * j / 4
        pts = []
        for i, z in enumerate(np.linspace(ZC - 1.6, 4.5 + j * 0.6, 12)):
            r = 0.7 + 0.5 * math.sin(i * 0.9 + j) + 0.04 * i
            pts.append((r * math.cos(a + i * 0.35), r * math.sin(a + i * 0.35), z))
        o.tubo(pts, [0.6, 0.55, 0.5, 0.42, 0.3, 0.12], "organo")
        for i in range(1, 11, 2):  # volantes
            q = pts[i]
            o.esfera((q[0] * 1.35, q[1] * 1.35, q[2]), 0.42, "carne_palida", esc=(1, 1, 0.5), k=0.2)
    M.articulacion("brazos_orales", "nucleo", (0, 0, ZC - 1.6))
    # Tentáculos largos que brillan, en dos grupos alternos para animarlos.
    for nombre, fase in (("tentaculos_a_neon", 0), ("tentaculos_b_neon", 1)):
        t = M.pieza(nombre, tris=0, roblox=NEON_V)
        for j in range(fase, 16, 2):
            a = math.tau * j / 16
            L = rnd.uniform(9.5, 12.6)
            pts = []
            for i in range(9):
                f = i / 8
                r = 5.6 - 1.6 * f + 0.5 * math.sin(f * 6 + j)
                pts.append((r * math.cos(a + 0.25 * math.sin(f * 5 + j)), r * math.sin(a + 0.25 * math.sin(f * 5 + j)), ZC - 0.6 - L * f))
            t.duro.tubo(pts, [0.16, 0.13, 0.11, 0.09, 0.03], "neon_violeta", n=5)
            for i in (2, 4, 6):
                t.duro.esfera(pts[i], 0.2, "neon_violeta", sub=1)
        M.articulacion(nombre, "campana_cristal", (0, 0, ZC - 0.5))
    M.raiz = "nucleo"


@modelo("bestias", "bestia", (10, 8, 6), "Escarabajo cósmico blindado: caparazón negro durísimo, cuernos frontales, 6 "
        "patas y alas que se abren del caparazón. Tanque viviente: 2 asientos bajo el caparazón.")
def bestia_escarabajo(M):
    M.mat("capa", "quitina_negra", a="#0E0C14", b="#2A1A44", rug=0.18, metal=0.4)
    M.mat("ala_fina", "membrana", a="#7A5AA0", b="#3A2460", rug=0.25)
    Z = 2.5
    c = M.pieza("cuerpo", tris=4200, res=170, k=0.3, ruido=(0.025, 1.2))
    c.esfera((0, -1.2, Z), 1, "capa", esc=(1.9, 1.3, 1.25))              # tórax (pronoto)
    c.esfera((0, 1.4, Z - 0.1), 1, "quitina", esc=(1.75, 2.4, 1.0))       # abdomen
    c.esfera((0, 0.6, Z - 0.75), 1, "piel", esc=(1.5, 2.6, 0.6))          # vientre
    for i in range(5):
        c.toro((0, 0.1 + i * 0.62, Z - 0.1), 1.62 - 0.12 * i, 0.12, "quitina_negra", eje=(0, 1, 0), esc=(1, 0.62, 1), k=0.08)  # segmentos
    c.tubo([(-1.6, -1.9, Z + 0.6), (0, -2.35, Z + 0.95), (1.6, -1.9, Z + 0.6)], 0.26, "capa", suave=6, k=0.15)  # reborde
    for s in (-1, 1):
        c.duro.cuerno([(s * 1.5, -1.6, Z + 0.7), (s * 2.3, -2.2, Z + 1.3), (s * 2.2, -3.1, Z + 1.9)], 0.3, "garra", n=6, seg=4)
    silla(M, c, (0, 0.7, Z + 0.95), s=0.85)
    silla(M, c, (0, 2.5, Z + 0.8), s=0.85)
    h = M.pieza("cabeza", tris=2000, res=140, k=0.15, ruido=(0.02, 1.5))
    h.esfera((0, -2.7, Z - 0.3), 1, "capa", esc=(1.0, 0.85, 0.75))
    h.tubo([(0, -3.0, Z), (0, -4.1, Z + 0.9), (0, -4.9, Z + 2.2)], [0.5, 0.38, 0.28], "capa", suave=6)       # cuerno mayor
    h.tubo([(0, -4.9, Z + 2.2), (0.65, -5.2, Z + 2.9)], [0.28, 0.1], "capa", sim=True)                        # horquilla
    h.tubo([(0, -1.7, Z + 1.0), (0, -2.9, Z + 1.9), (0, -4.0, Z + 2.2)], [0.42, 0.3, 0.1], "capa", suave=6)   # cuerno del tórax
    for s in (-1, 1):
        h.duro.cuerno([(s * 0.5, -3.3, Z - 0.6), (s * 1.0, -3.9, Z - 0.8), (s * 0.4, -4.3, Z - 0.75)], 0.15, "garra", n=5, seg=4)  # mandíbulas
        h.duro.tubo([(s * 0.6, -3.0, Z + 0.1), (s * 1.3, -3.6, Z + 0.6), (s * 1.9, -3.5, Z + 0.4)], [0.06, 0.05, 0.09], "quitina", n=5)  # antenas
    on = M.pieza("ojos_neon", tris=0, roblox=NEON_V)
    on.duro.esfera((0.8, -2.95, Z - 0.1), 0.2, "neon_violeta", sub=1, sim=True)
    M.articulacion("cabeza", "cuerpo", (0, -2.2, Z - 0.2))
    M.articulacion("ojos_neon", "cabeza", (0, -2.95, Z - 0.1))
    for s, lado in ((-1, "izq"), (1, "der")):
        # Élitro abierto: media cáscara levantada y girada hacia fuera.
        e = M.pieza(f"elitro_{lado}", tris=1300, res=120, k=0.1, ruido=(0.02, 1.2))
        with e.en((s * 0.25, -0.35, Z + 0.95), rot=(28, s * 30, s * 38)):
            e.esfera((s * 0.85, 1.9, -0.1), 1, "capa", esc=(1.0, 2.3, 0.85), cascara=0.2)
            e.caja((s * 0.85, 1.9, -1.0), (2.6, 5.2, 1.6), None, resta=True)
            for i in range(4):
                e.tubo([(s * (0.25 + i * 0.38), 0.3, 0.55 + 0.1 * i), (s * (0.3 + i * 0.4), 2.0, 0.72), (s * (0.4 + i * 0.3), 3.8, 0.3)], 0.07, "quitina", k=0.05)
        M.articulacion(f"elitro_{lado}", "cuerpo", (s * 0.3, -0.4, Z + 0.95))
        # Ala membranosa desplegada.
        w = M.pieza(f"ala_{lado}", tris=0)
        raiz = np.array([s * 0.5, -0.1, Z + 0.9])
        puntas = [np.array([s * 5.0, -0.8, Z + 2.4]), np.array([s * 5.2, 1.4, Z + 2.0]), np.array([s * 4.2, 3.3, Z + 1.5]), np.array([s * 2.4, 4.0, Z + 1.1])]
        filas = [[raiz + (q - raiz) * t + np.array([0, 0, 0.5]) * math.sin(math.pi * t) for t in np.linspace(0.02, 1, 6)] for q in puntas]
        w.duro.superficie(filas, 0.05, "ala_fina")
        for q in puntas:
            w.duro.tubo([raiz, (raiz + q) / 2 + [0, 0, 0.52], q], [0.07, 0.05, 0.02], "quitina", n=4)
        M.articulacion(f"ala_{lado}", "cuerpo", tuple(raiz))
        # Patas.
        for i, (y, ay) in enumerate(((-1.5, -1.5), (0.1, 0.0), (1.7, 1.6))):
            p = M.pieza(f"pata_{i + 1}_{lado}", tris=520, res=110, k=0.08, ruido=(0.015, 1.8))
            cadera = np.array([s * 1.3, y, Z - 0.7])
            rodilla = np.array([s * 3.0, y + ay * 0.6, Z + 0.5])
            tobillo = np.array([s * 3.9, y + ay * 1.0, 0.7])
            pie = np.array([s * 4.3, y + ay * 1.25, 0.05])
            p.tubo([cadera, rodilla], [0.38, 0.3], "capa")
            p.tubo([rodilla, tobillo], [0.28, 0.18], "capa")
            p.tubo([tobillo, pie], [0.16, 0.1], "quitina")
            p.esfera(rodilla, 0.36, "quitina", k=0.05)
            for k_ in range(3):
                q = rodilla + (tobillo - rodilla) * (0.25 + 0.25 * k_)
                p.duro.cono(q, q + [s * 0.4, 0, 0.3], 0.07, "garra", n=4)
            p.duro.cuerno([pie, pie + [s * 0.3, -0.25, 0.1], pie + [s * 0.45, -0.5, -0.05]], 0.08, "garra", n=4, seg=2)
            M.articulacion(f"pata_{i + 1}_{lado}", "cuerpo", tuple(cadera))


@modelo("bestias", "bestia", (4, 24, 4), "Serpiente voladora del vacío: cuerpo largo y ondulante, escamas iridiscentes "
        "púrpura y verde y crestas dorsales. Rápida. 3 asientos a lo largo.")
def bestia_serpiente(M):
    M.mat("panza", "carne_palida", a="#9A8AB0", b="#5A3A7A", escamas=dict(esc=3.0, fuerza=0.4))
    M.mat("cresta", "membrana", a="#2AA06A", b="#4A1E7A", rug=0.3)

    def eje(y):  # la onda del cuerpo
        return np.array([1.15 * math.sin(y * 0.42), y, 2.0 + 0.55 * math.sin(y * 0.3 + 1.0)])

    def radio(y):
        return 1.0 * (1 - max(0.0, (y - 2) / 12.5) ** 1.6 * 0.86) * (0.8 + 0.2 * min(1.0, (y + 9.5) / 2))

    tramos = [("cuerpo_1", -9.0, -4.2, (-7.0,)), ("cuerpo_2", -4.2, 0.6, (-2.0,)), ("cuerpo_3", 0.6, 5.4, (3.0,)), ("cuerpo_4", 5.4, 10.0, ()),
              ("cola", 10.0, 14.4, ())]
    anterior = None
    for nombre, y0, y1, sillas in tramos:
        p = M.pieza(nombre, tris=2700 if nombre != "cola" else 1400, res=150, k=0.15, ruido=(0.02, 1.4))
        ys = np.linspace(y0 - 0.25, y1 + 0.25, 12)
        p.tubo([eje(y) for y in ys], [radio(y) for y in ys], "escamas")
        p.tubo([eje(y) - [0, 0, radio(y) * 0.45] for y in ys], [radio(y) * 0.7 for y in ys], "panza", k=0.1)
        for i in range(5):  # cresta dorsal: velas de membrana entre espinas
            ya = y0 + (y1 - y0) * (i + 0.15) / 5
            yb = y0 + (y1 - y0) * (i + 0.85) / 5
            if any(ya - 0.9 < s < yb + 0.9 for s in sillas):
                continue
            a, b = eje(ya) + [0, 0, radio(ya) * 0.9], eje(yb) + [0, 0, radio(yb) * 0.9]
            alto = 1.25 * radio((ya + yb) / 2) + 0.15
            p.duro.cuerno([a, a + [0, 0.15, alto * 0.6], a + [0, 0.5, alto]], 0.11, "garra", n=5, seg=3)
            p.duro.superficie([[a, a + [0, 0.1, alto * 0.45], a + [0, 0.42, alto * 0.9]], [(a + b) / 2, (a + b) / 2 + [0, 0.1, alto * 0.3], (a + b) / 2 + [0, 0.3, alto * 0.6]],
                               [b, b + [0, 0.05, alto * 0.1], b + [0, 0.1, alto * 0.22]]], 0.06, "cresta")
        for s in sillas:
            q = eje(s)
            silla(M, p, (q[0], s, q[2] + radio(s) * 0.98), s=0.8)
        if nombre == "cola":
            f = eje(14.4)
            p.duro.lamina([f, f + [0.9, 0.9, 0.3], f + [0, 2.2, 0.2], f + [-0.9, 0.9, 0.3]], 0.1, "cresta", bombeo=0.08)
            p.duro.lamina([f, f + [0, 0.9, 0.9], f + [0, 2.0, 0.1], f + [0, 0.9, -0.7]], 0.1, "cresta", bombeo=0.08)
        if anterior:
            M.articulacion(nombre, anterior, tuple(eje(y0)))
        anterior = nombre
    # Cabeza con capucha de membrana.
    C = eje(-9.0)
    h = M.pieza("cabeza", tris=2600, res=150, k=0.15, ruido=(0.02, 1.5))
    with h.en(C + [0, -1.2, 0.2], rot=(6, 0, -8)):
        h.esfera((0, 0, 0), 1, "escamas", esc=(0.95, 1.5, 0.72))
        h.esfera((0, -1.3, -0.1), 1, "escamas", esc=(0.66, 1.0, 0.45))
        h.tubo([(0.25, -1.5, 0.3), (0.7, -0.5, 0.55), (0.85, 0.5, 0.45)], [0.14, 0.24, 0.16], "quitina", sim=True)
        h.esfera((0.66, -0.75, 0.22), 0.24, "negro", sim=True, resta=True, k=0.04)
        h.esfera((0, -1.2, -0.52), 1, "carne_viva", esc=(0.5, 1.1, 0.25), resta=True, k=0.06)
        d = h.duro
        for s in (-1, 1):  # capucha: tres varillas y membrana
            raiz = np.array([s * 0.7, 0.6, 0.1])
            puntas = [np.array([s * 2.0, 0.3, 1.2]), np.array([s * 2.3, 1.2, 0.3]), np.array([s * 1.8, 1.9, -0.6])]
            for q in puntas:
                d.tubo([raiz, (raiz + q) / 2, q], [0.1, 0.07, 0.02], "garra", n=4)
            d.superficie([[raiz + (q - raiz) * t for t in np.linspace(0.05, 1, 4)] for q in puntas], 0.05, "cresta")
            d.cuerno([(s * 0.3, -1.95, -0.3), (s * 0.34, -2.0, -0.8), (s * 0.3, -1.8, -1.2)], 0.09, "diente", n=5, seg=3)  # colmillos
        d.cuerno([(0.5, 0.5, 0.5), (0.8, 1.5, 1.1), (0.6, 2.4, 1.2)], 0.2, "garra", n=6, seg=4, sim=True)
    on = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    with on.en(C + [0, -1.2, 0.2], rot=(6, 0, -8)):
        on.duro.esfera((0.6, -0.72, 0.22), 0.17, "neon_verde", sub=1, sim=True)
    j = M.pieza("mandibula", tris=600, res=100, k=0.1)
    with j.en(C + [0, -1.2, 0.2], rot=(22, 0, -8)):
        j.tubo([(0.7, 0.4, -0.4), (0.55, -0.9, -0.7), (0, -1.9, -0.66)], [0.24, 0.2, 0.2], "escamas", sim=True)
        j.esfera((0, -0.6, -0.78), 1, "panza", esc=(0.5, 1.1, 0.2))
        j.duro.tubo([(0, -1.5, -0.6), (0, -2.4, -0.75), (0.12, -2.9, -0.6)], [0.07, 0.05, 0.0], "carne_viva", n=4)  # lengua bífida
        j.duro.tubo([(0, -2.4, -0.75), (-0.14, -2.9, -0.62)], [0.05, 0.0], "carne_viva", n=4)
    M.articulacion("cabeza", "cuerpo_1", tuple(C))
    M.articulacion("mandibula", "cabeza", tuple(C + [0, -0.9, -0.2]))
    M.articulacion("ojos_neon", "cabeza", tuple(C + [0, -1.9, 0.4]))
    M.raiz = "cuerpo_1"


@modelo("bestias", "bestia", (14, 14, 8), "Araña estelar: 8 patas largas articuladas, cuerpo con muchos ojos rojos que "
        "brillan e hileras de seda en el abdomen. De emboscada: 2 asientos en el abdomen.")
def bestia_arana(M):
    rnd = M.rnd
    M.mat("pelo", "quitina_negra", a="#141018", b="#3A2048", rug=0.6, fibras=dict(esc=7.0, fuerza=1.0))
    Z = 3.4
    c = M.pieza("cuerpo", tris=3000, res=150, k=0.25, ruido=(0.03, 1.4))
    c.esfera((0, -1.4, Z), 1, "pelo", esc=(1.7, 1.9, 1.15))          # cefalotórax
    c.esfera((0, -2.7, Z - 0.1), 1, "quitina_negra", esc=(1.2, 0.9, 0.9))
    c.esfera((0, -0.2, Z - 0.1), 0.7, "carne", k=0.2)                 # pedicelo
    for s in (-1, 1):  # quelíceros con colmillo
        c.tubo([(s * 0.5, -3.2, Z - 0.3), (s * 0.55, -3.7, Z - 0.9)], [0.42, 0.32], "pelo", k=0.1)
        c.duro.cuerno([(s * 0.55, -3.75, Z - 1.1), (s * 0.5, -3.9, Z - 1.7), (s * 0.2, -3.6, Z - 2.2)], 0.2, "garra", n=6, seg=4)
        c.tubo([(s * 0.9, -3.0, Z - 0.2), (s * 1.5, -4.0, Z - 0.3), (s * 1.2, -4.7, Z - 1.0)], [0.26, 0.2, 0.14], "pelo", k=0.08)  # pedipalpos
    on = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=ROJO))
    for (x, y, z, r) in ((0.32, -3.45, 0.42, 0.24), (0.8, -3.2, 0.5, 0.17), (1.1, -2.7, 0.62, 0.13), (0.42, -3.0, 0.82, 0.12)):
        on.duro.esfera((x, y, Z + z), r, "neon_rojo", sub=1, sim=True)
    M.articulacion("ojos_neon", "cuerpo", (0, -3.2, Z + 0.5))
    a = M.pieza("abdomen", tris=3300, res=150, k=0.3, ruido=(0.04, 1.1))
    a.esfera((0, 2.6, Z + 0.7), 1, "pelo", esc=(2.5, 3.1, 2.2))
    M.mat("marca", "neon_rojo", a="#7A0A14", b="#C0141E", emis=(ROJO, 0.25))
    a.esfera((0, 3.2, Z + 2.65), 1, "marca", esc=(0.6, 1.5, 0.3), k=0.1)    # marca del lomo
    for i in range(5):
        a.toro((0, 1.0 + i * 0.95, Z + 0.7), 2.3 * math.sqrt(max(0.1, 1 - ((i * 0.95 - 1.6) / 3.1) ** 2)), 0.12, "quitina_negra", eje=(0, 1, 0), esc=(1, 0.88, 1), k=0.1)
    for j in range(3):  # hileras
        an = math.tau * j / 3 + 0.5
        a.tubo([(0.3 * math.cos(an), 5.3, Z + 0.2 + 0.3 * math.sin(an)), (0.42 * math.cos(an), 6.2, Z + 0.15 + 0.42 * math.sin(an))], [0.3, 0.16], "carne_palida", k=0.1)
        a.duro.tubo([(0.42 * math.cos(an), 6.2, Z + 0.15 + 0.42 * math.sin(an)), (0.2 * math.cos(an), 6.8, Z - 0.4), (0, 7.2, 0.4)], [0.05, 0.035, 0.02], "seda", n=4)
    silla(M, a, (0, 1.2, Z + 2.75), s=0.9)
    silla(M, a, (0, 3.5, Z + 2.85), s=0.9)
    M.articulacion("abdomen", "cuerpo", (0, -0.1, Z))
    for s, lado in ((-1, "izq"), (1, "der")):
        for i, ang in enumerate((-58, -22, 18, 52)):
            p = M.pieza(f"pata_{i + 1}_{lado}", tris=820, res=140, k=0.06, ruido=(0.015, 2.0))
            an = math.radians(ang)
            u = np.array([s * math.cos(an), math.sin(an), 0])
            cadera = np.array([0, -1.4, Z - 0.2]) + u * 1.45
            rodilla = np.array([0, -1.4, 7.4 - 0.25 * abs(i - 1.5)]) + u * 3.6
            tobillo = np.array([0, -1.4, 3.3]) + u * 5.9
            pie = np.array([0, -1.4, 0.0]) + u * 6.9
            p.tubo([cadera, cadera + (rodilla - cadera) * 0.5 + [0, 0, 0.5], rodilla], [0.42, 0.36, 0.26], "pelo")
            p.tubo([rodilla, tobillo], [0.26, 0.17], "quitina_negra")
            p.tubo([tobillo, pie], [0.16, 0.05], "quitina_negra")
            p.esfera(rodilla, 0.34, "quitina", k=0.05)
            p.esfera(tobillo, 0.22, "quitina", k=0.05)
            for k_ in range(4):  # cerdas
                q = rodilla + (tobillo - rodilla) * (0.15 + 0.2 * k_)
                p.duro.cono(q, q + u * 0.25 + [0, 0, 0.42], 0.05, "garra", n=3)
            M.articulacion(f"pata_{i + 1}_{lado}", "cuerpo", tuple(cadera))


@modelo("bestias", "bestia", (10, 28, 10), "Ballena del espacio profundo: enorme y lenta, boca gigante, piel gris púrpura "
        "con percebes luminosos. La nave nodriza de los monstruos: 8 asientos y bahía de carga.")
def bestia_ballena(M):
    rnd = M.rnd
    M.mat("panza", "carne_palida", a="#8A7A9A", b="#4A3A62", fibras=dict(esc=1.2, fuerza=0.6))
    Z = 5.0

    def lomo(y):
        return Z + 3.9 * math.sqrt(max(0.02, 1 - ((y + 1.5) / 11.5) ** 2))

    c = M.pieza("cuerpo", tris=6600, res=190, k=0.9, ruido=(0.06, 0.6))
    c.esfera((0, -2.0, Z), 1, "piel_gris", esc=(4.0, 9.0, 4.0))
    c.esfera((0, -7.5, Z + 0.6), 1, "piel_gris", esc=(3.6, 4.6, 3.3))     # frente
    c.esfera((0, 5.0, Z + 0.2), 1, "piel_gris", esc=(2.9, 6.0, 2.9))
    c.esfera((0, -2.0, Z - 2.2), 1, "panza", esc=(3.2, 7.5, 1.9))
    for i in range(7):  # surcos de la garganta
        x = -2.1 + i * 0.7
        c.tubo([(x, -9.5, Z - 2.9 + 0.12 * x * x), (x * 1.1, -4.0, Z - 3.9 + 0.1 * x * x), (x, 1.5, Z - 3.6 + 0.1 * x * x)], 0.16, None, resta=True, k=0.1)
    c.esfera((0, -11.2, Z - 0.6), 1, "carne_viva", esc=(2.9, 3.3, 1.5), resta=True, k=0.3)   # boca gigante
    for s in (-1, 1):
        c.esfera((s * 3.25, -7.4, Z + 0.3), 0.6, "piel_gris", k=0.3)
        c.esfera((s * 3.75, -7.5, Z + 0.3), 0.33, "negro", resta=True, k=0.05)
    c.tubo([(0, 3.5, lomo(3.5) - 0.3), (0, 5.5, lomo(5.5) + 1.2), (0, 7.0, lomo(7) + 0.2)], [0.6, 0.42, 0.2], "piel_gris", k=0.5)  # aleta dorsal
    # Howdah: barandilla de costillas y dos filas de cuatro sillas.
    for i, y in enumerate((-6.0, -3.6, -1.2, 1.2)):
        for s in (-1, 1):
            silla(M, c, (s * 1.0, y, lomo(y) - 0.12), s=0.9)
    for s in (-1, 1):
        for y in np.linspace(-7.2, 2.4, 6):
            c.duro.cuerno([(s * 2.2, y, lomo(y) - 0.6), (s * 2.7, y, lomo(y) + 0.6), (s * 2.0, y, lomo(y) + 1.4)], 0.17, "hueso", n=5, seg=4)
        c.duro.tubo([(s * 2.55, y, lomo(y) + 0.55) for y in np.linspace(-7.2, 2.4, 6)], 0.06, "tendon", n=4)
    # Bahía de carga: red de tendones con bultos detrás de las sillas.
    for (x, y) in ((-0.9, 3.4), (0.9, 3.5), (0, 4.9)):
        c.esfera((x, y, lomo(y) + 0.35), 1, "cuero", esc=(0.85, 0.8, 0.7), k=0.15)
    for x in (-1.7, 0, 1.7):
        c.tubo([(x, 2.5, lomo(2.5) - 0.2), (x * 0.7, 4.0, lomo(4.0) + 1.05), (x * 0.4, 5.8, lomo(5.8) - 0.2)], 0.08, "tendon", suave=6, k=0.03)
    M.bahia((0, 4.0, lomo(4.0) + 0.7), (3.4, 3.6, 1.6), "red de carga en el lomo, detrás de las sillas")
    j = M.pieza("mandibula", tris=2300, res=150, k=0.4, ruido=(0.05, 0.8))
    j.tubo([(3.0, -5.0, Z - 1.6), (2.9, -9.5, Z - 2.6), (1.6, -12.6, Z - 2.5), (0, -13.6, Z - 2.4)], [0.8, 0.85, 0.8, 0.85], "piel_gris", suave=10, sim=True)
    j.esfera((0, -8.6, Z - 3.2), 1, "panza", esc=(2.8, 4.6, 0.9))
    for i in range(11):  # barbas: láminas de quitina que cuelgan del paladar (van con la mandíbula por sencillez)
        a = -1.3 + i * 0.26
        x, y = 2.5 * math.sin(a), -9.6 - 3.2 * math.cos(a)
        j.duro.cuerno([(x, y, Z - 1.9), (x * 1.02, y, Z - 1.2), (x * 0.95, y + 0.2, Z - 0.3)], 0.2, "diente", n=5, seg=3, aplastar=0.5)
    M.articulacion("mandibula", "cuerpo", (0, -5.0, Z - 1.5))
    for s, lado in ((-1, "izq"), (1, "der")):
        f = M.pieza(f"aleta_{lado}", tris=1300, res=130, k=0.4, ruido=(0.04, 0.9))
        f.esfera((s * 4.0, -2.6, Z - 1.9), 1, "piel_gris", esc=(1.1, 1.2, 0.36), rot=(0, s * 22, s * 28))
        f.esfera((s * 4.6, -1.3, Z - 2.9), 1, "piel_gris", esc=(0.75, 0.95, 0.26), rot=(0, s * 30, s * 40))
        for k_ in range(4):
            f.esfera((s * (4.7 + 0.12 * k_), -2.0 + 0.62 * k_, Z - 3.3 - 0.1 * k_), 0.24, "piel_gris", esc=(1, 1, 0.5))
        M.articulacion(f"aleta_{lado}", "cuerpo", (s * 3.5, -3.0, Z - 1.5))
    t = M.pieza("cola", tris=2300, res=150, k=0.5, ruido=(0.05, 0.8))
    t.tubo([(0, 9.5, Z + 0.2), (0, 12.0, Z + 0.5), (0, 14.0, Z + 1.0)], [2.0, 1.2, 0.7], "piel_gris")
    for s in (-1, 1):
        t.esfera((s * 1.7, 15.0, Z + 1.2), 1, "piel_gris", esc=(1.8, 1.1, 0.3), rot=(0, 0, -s * 24))
        t.esfera((s * 3.3, 15.9, Z + 1.3), 1, "piel_gris", esc=(1.0, 0.7, 0.2), rot=(0, 0, -s * 40))
    M.articulacion("cola", "cuerpo", (0, 9.8, Z + 0.2))
    # Percebes luminosos: copas de cal con el interior encendido, en racimos.
    pn = M.pieza("percebes_neon", tris=0, roblox=NEON_V)
    for g in range(11):
        y0 = rnd.uniform(-9, 7)
        a0 = rnd.uniform(0.6, 2.5) * rnd.choice((-1, 1))
        for k_ in range(rnd.randint(3, 5)):
            y = y0 + rnd.uniform(-0.7, 0.7)
            a = a0 + rnd.uniform(-0.2, 0.2)
            e = math.sqrt(max(0.05, 1 - ((y + 2) / 9.0) ** 2))
            nrm = np.array([math.sin(a), 0, math.cos(a)])
            b = np.array([4.0 * e * math.sin(a), y, Z + 4.0 * e * math.cos(a)])
            r = rnd.uniform(0.16, 0.32)
            c.duro.torno([(r, -0.3), (r * 0.9, 0.2), (r * 0.6, 0.38), (r * 0.42, 0.2), (0, 0.15)], b, "hueso_viejo", n=6, eje=nrm)
            pn.duro.esfera(b + nrm * 0.22, r * 0.46, "neon_violeta", sub=1)
    M.articulacion("percebes_neon", "cuerpo", (0, 0, Z))


@modelo("bestias", "bestia", (18, 14, 6), "Águila rapaz cósmica: alas afiladas, garras enormes, pico curvo, plumas que "
        "son escamas y ojos amarillos que brillan. Interceptor veloz: 1 asiento en el lomo.")
def bestia_aguila(M):
    M.mat("pluma", "escamas", a="#2A1A4A", b="#12301E", rug=0.35, escamas=dict(esc=3.5, fuerza=0.9))
    M.mat("pluma_clara", "escamas", a="#5A3A8A", b="#2A6A4A", rug=0.3)
    M.mat("pico", "garra", a="#2A2420", b="#B0902A")
    Z = 3.2
    c = M.pieza("cuerpo", tris=3600, res=160, k=0.4, ruido=(0.03, 1.2))
    c.esfera((0, 0, Z), 1, "pluma", esc=(1.5, 3.0, 1.35))
    c.esfera((0, -1.8, Z + 0.25), 1, "pluma_clara", esc=(1.3, 1.5, 1.3))     # pecho
    c.tubo([(0, -2.6, Z + 0.6), (0, -3.6, Z + 1.2)], [1.0, 0.75], "pluma", k=0.3)  # cuello
    for i in range(9):  # collar de plumas-escama erizadas
        a = -1.6 + i * 0.4
        b = np.array([0.95 * math.sin(a), -2.9, Z + 0.8 + 0.95 * math.cos(a)])
        c.duro.cuerno([b, b + [0.3 * math.sin(a), 0.5, 0.3 * math.cos(a)], b + [0.45 * math.sin(a), 1.2, 0.45 * math.cos(a)]], 0.16, "pluma_clara", n=4, seg=2, aplastar=0.4)
    silla(M, c, (0, 0.1, Z + 1.38), s=0.9)
    h = M.pieza("cabeza", tris=1800, res=140, k=0.15, ruido=(0.02, 1.6))
    with h.en((0, -4.2, Z + 1.5), rot=(10, 0, 0)):
        h.esfera((0, 0, 0), 1, "pluma_clara", esc=(0.78, 0.95, 0.75))
        h.tubo([(0, -0.7, 0.05), (0, -1.5, -0.1), (0, -1.95, -0.6)], [0.42, 0.3, 0.1], "pico", suave=6, k=0.08)   # pico curvo
        h.tubo([(0.2, -0.75, 0.42), (0.6, -0.3, 0.5), (0.72, 0.4, 0.35)], [0.12, 0.17, 0.1], "pluma", sim=True, k=0.06)  # ceño
        h.esfera((0.55, -0.42, 0.18), 0.2, "negro", sim=True, resta=True, k=0.03)
        h.tubo([(0, -0.6, -0.4), (0, -1.3, -0.5), (0, -1.6, -0.52)], [0.26, 0.18, 0.06], "pico", k=0.05)          # mandíbula
        h.duro.cuerno([(0, 0.3, 0.6), (0, 0.9, 1.2), (0, 1.7, 1.2)], 0.2, "pluma", n=5, seg=3, aplastar=0.4)
        h.duro.cuerno([(0.35, 0.3, 0.5), (0.55, 0.9, 0.95), (0.6, 1.5, 0.9)], 0.15, "pluma", n=5, seg=3, aplastar=0.4, sim=True)
    on = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=AMARILLO))
    with on.en((0, -4.2, Z + 1.5), rot=(10, 0, 0)):
        on.duro.esfera((0.5, -0.4, 0.18), 0.15, "neon_amarillo", sub=1, sim=True)
    M.articulacion("cabeza", "cuerpo", (0, -3.5, Z + 1.1))
    M.articulacion("ojos_neon", "cabeza", (0, -4.6, Z + 1.7))
    for s, lado in ((-1, "izq"), (1, "der")):
        w = M.pieza(f"ala_{lado}", tris=1500, res=130, k=0.2, ruido=(0.02, 1.4))
        hombro = np.array([s * 1.2, -1.2, Z + 0.9])
        codo = np.array([s * 4.2, -2.0, Z + 1.9])
        mano = np.array([s * 7.2, -0.9, Z + 1.5])
        w.tubo([hombro, codo, mano], [0.7, 0.5, 0.32], "pluma")
        w.esfera((hombro + codo) / 2 + [0, 0.6, -0.1], 1, "pluma", esc=(1.6, 0.9, 0.36), k=0.2)
        d = w.duro
        # Plumas-cuchilla: primarias largas en la mano y secundarias en el brazo, solapadas.
        n = 13
        for i in range(n):
            t = i / (n - 1)
            base = hombro + (codo - hombro) * min(1, t * 2) + (mano - codo) * max(0, t * 2 - 1)
            L = 2.6 + 2.6 * t ** 1.5
            ang = math.radians(8 + 62 * t ** 1.3)
            dire = np.array([s * math.sin(ang), math.cos(ang), -0.12])
            punta = base + dire * L
            lado_ = np.cross(dire, [0, 0, 1.0]) * (0.36 + 0.1 * (1 - t))
            d.lamina([base - lado_ * 0.5, base + dire * L * 0.5 - lado_ + [0, 0, 0.05], punta, base + dire * L * 0.6 + lado_ * 0.8 + [0, 0, 0.05], base + lado_ * 0.5],
                     0.07, "pluma" if i % 2 else "pluma_clara", bombeo=0.05)
        for i in range(7):  # coberteras
            t = i / 6
            base = hombro + (mano - hombro) * t + [0, 0, 0.25]
            d.lamina([base + [0, -0.35, 0], base + [s * 0.3, 0.5, 0.12], base + [0, 1.5 + 0.3 * t, 0.05], base + [-s * 0.3, 0.5, 0.12]], 0.08, "pluma_clara", bombeo=0.07)
        d.cuerno([mano, mano + [s * 0.5, -0.6, 0.1], mano + [s * 0.3, -1.2, -0.2]], 0.16, "garra", n=5, seg=3)
        M.articulacion(f"ala_{lado}", "cuerpo", tuple(hombro))
        g = M.pieza(f"garra_{lado}", tris=900, res=110, k=0.1, ruido=(0.015, 1.8))
        g.tubo([(s * 0.9, 0.8, Z - 0.6), (s * 1.1, 0.3, Z - 1.7), (s * 1.1, 0.0, Z - 2.5)], [0.6, 0.36, 0.3], "pluma", k=0.1)
        g.esfera((s * 1.1, -0.1, Z - 2.7), 0.4, "pico", esc=(1, 1.1, 0.7))
        for k_ in (-1, 0, 1):
            g.tubo([(s * 1.1, -0.2, Z - 2.75), (s * 1.1 + k_ * 0.42, -0.95, Z - 2.65)], [0.17, 0.13], "pico", k=0.05)
            g.duro.cuerno([(s * 1.1 + k_ * 0.42, -0.95, Z - 2.65), (s * 1.1 + k_ * 0.52, -1.5, Z - 2.75), (s * 1.1 + k_ * 0.5, -1.6, Z - 3.25)], 0.15, "garra", n=6, seg=4)
        g.duro.cuerno([(s * 1.1, 0.3, Z - 2.75), (s * 1.1, 0.8, Z - 2.8), (s * 1.1, 0.85, Z - 3.2)], 0.14, "garra", n=6, seg=3)
        M.articulacion(f"garra_{lado}", "cuerpo", (s * 0.9, 0.8, Z - 0.6))
    t = M.pieza("cola", tris=0)
    for i in range(7):
        a = math.radians(-36 + i * 12)
        base = np.array([0.5 * math.sin(a), 2.6, Z + 0.2])
        dire = np.array([math.sin(a), math.cos(a), -0.08])
        L = 3.6 - 0.6 * abs(i - 3) / 3
        lado_ = np.cross(dire, [0, 0, 1.0]) * 0.42
        t.duro.lamina([base - lado_ * 0.4, base + dire * L * 0.6 - lado_, base + dire * L, base + dire * L * 0.6 + lado_, base + lado_ * 0.4], 0.07,
                      "pluma" if i % 2 else "pluma_clara", bombeo=0.05)
    M.articulacion("cola", "cuerpo", (0, 2.6, Z + 0.2))


@modelo("bestias", "bestia", (14, 12, 6), "Cangrejo acorazado: pinzas enormes, caparazón con espinas y muchas patas. "
        "Lento pero indestructible: 2 asientos encima.")
def bestia_cangrejo(M):
    rnd = M.rnd
    M.mat("concha", "quitina", a="#3A1420", b="#1A0C1E", rug=0.4, metal=0.15, relieve=0.8, manchas=dict(color="#6A2A3A", esc=2.0, radio=0.25))
    M.mat("panza", "hueso_viejo", a="#8A7A72", b="#5A4652")
    Z = 2.6
    c = M.pieza("cuerpo", tris=4600, res=170, k=0.3, ruido=(0.04, 1.2))
    c.esfera((0, 0.5, Z), 1, "concha", esc=(3.6, 2.8, 1.35))
    c.esfera((0, 0.3, Z - 0.7), 1, "panza", esc=(3.1, 2.4, 0.9))
    c.tubo([(-3.5, 0.2, Z + 0.1), (-2.4, -2.0, Z + 0.2), (0, -2.55, Z + 0.25), (2.4, -2.0, Z + 0.2), (3.5, 0.2, Z + 0.1)], 0.3, "concha", suave=12, k=0.2)  # reborde
    for s in (-1, 1):  # ojos sobre pedúnculos
        c.tubo([(s * 0.8, -2.3, Z + 0.3), (s * 0.95, -2.8, Z + 1.0)], [0.2, 0.15], "panza", k=0.1)
        c.tubo([(s * 0.3, -2.5, Z - 0.3), (s * 0.4, -3.0, Z - 0.9)], [0.2, 0.1], "panza", k=0.08)   # maxilípedos
    for i in range(16):  # espinas del caparazón
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.35, 0.95)
        x, y = 3.4 * r * math.cos(a), 0.5 + 2.6 * r * math.sin(a)
        if abs(x) < 1.0 and -1.2 < y < 2.2:
            continue
        z = Z + 1.3 * math.sqrt(max(0.05, 1 - r * r))
        L = rnd.uniform(0.7, 1.4)
        c.duro.cuerno([(x, y, z - 0.1), (x * 1.05, y * 1.03, z + L * 0.6), (x * 1.12, y * 1.08, z + L)], 0.22, "garra", n=5, seg=3)
    for i in range(9):  # dientes del borde
        a = -1.2 + i * 0.3
        c.duro.cono((3.3 * math.sin(a), -2.3 * math.cos(a) + 0.1, Z + 0.3), (3.9 * math.sin(a), -2.95 * math.cos(a), Z + 0.45), 0.17, "garra", n=5)
    silla(M, c, (0, -0.3, Z + 1.38), s=0.9)
    silla(M, c, (0, 1.6, Z + 1.3), s=0.9)
    on = M.pieza("ojos_neon", tris=0, roblox=NEON_V)
    on.duro.esfera((0.97, -2.85, Z + 1.12), 0.22, "neon_violeta", sub=1, sim=True)
    M.articulacion("ojos_neon", "cuerpo", (0, -2.85, Z + 1.1))
    for s, lado in ((-1, "izq"), (1, "der")):
        gr = 1.25 if s > 0 else 0.95   # una pinza mayor que la otra, como en los cangrejos violinistas
        q = M.pieza(f"pinza_{lado}", tris=2100, res=150, k=0.2, ruido=(0.03, 1.4))
        hombro = np.array([s * 2.6, -1.6, Z - 0.2])
        codo = np.array([s * 4.6, -2.6, Z + 0.6])
        mun = np.array([s * 4.9, -4.2, Z + 0.3])
        q.tubo([hombro, codo], [0.6, 0.55], "concha")
        q.tubo([codo, mun], [0.55, 0.6 * gr], "concha")
        q.esfera(codo, 0.7, "concha", k=0.1)
        palma = mun + [-s * 0.3, -1.3 * gr, 0]
        q.esfera(palma, 1, "concha", esc=(1.0 * gr, 1.5 * gr, 0.85 * gr))
        q.tubo([palma + [-s * 0.3 * gr, -1.0 * gr, -0.3 * gr], palma + [-s * 0.6 * gr, -2.4 * gr, -0.3 * gr], palma + [-s * 0.5 * gr, -3.3 * gr, 0.0]], [0.55 * gr, 0.38 * gr, 0.1], "concha", k=0.15)  # dedo fijo
        for k_ in range(4):
            b = palma + [-s * 0.5 * gr, (-1.4 - 0.5 * k_) * gr, -0.05 * gr]
            q.duro.cono(b, b + [0, 0, 0.36 * gr], 0.11 * gr, "diente", n=5)
            q.duro.cono(palma + [s * 0.6 * gr, (0.6 - 0.6 * k_) * gr, 0.5 * gr], palma + [s * 1.1 * gr, (0.6 - 0.6 * k_) * gr, 0.95 * gr], 0.14 * gr, "garra", n=5)
        dd = M.pieza(f"dedo_{lado}", tris=700, res=110, k=0.12, ruido=(0.03, 1.4))
        bis = palma + [-s * 0.2 * gr, -0.9 * gr, 0.5 * gr]
        dd.tubo([bis, bis + [-s * 0.5 * gr, -1.4 * gr, 0.7 * gr], bis + [-s * 0.45 * gr, -2.6 * gr, 0.35 * gr]], [0.5 * gr, 0.36 * gr, 0.08], "concha")
        for k_ in range(3):
            b = bis + [-s * 0.45 * gr, (-0.9 - 0.5 * k_) * gr, 0.3 * gr]
            dd.duro.cono(b, b - [0, 0, 0.34 * gr], 0.1 * gr, "diente", n=5)
        M.articulacion(f"pinza_{lado}", "cuerpo", tuple(hombro))
        M.articulacion(f"dedo_{lado}", f"pinza_{lado}", tuple(bis))
        for i, ang in enumerate((-12, 14, 38, 62)):
            p = M.pieza(f"pata_{i + 1}_{lado}", tris=560, res=120, k=0.06, ruido=(0.015, 1.8))
            an = math.radians(ang)
            u = np.array([s * math.cos(an), math.sin(an), 0])
            cadera = np.array([0, 0.4, Z - 0.5]) + u * 2.7
            rodilla = np.array([0, 0.4, Z + 0.9]) + u * 4.6
            pie = np.array([0, 0.4, 0.0]) + u * 6.2
            p.tubo([cadera, rodilla], [0.42, 0.32], "concha")
            p.tubo([rodilla, rodilla + (pie - rodilla) * 0.6], [0.3, 0.2], "concha")
            p.esfera(rodilla, 0.38, "panza", k=0.05)
            p.duro.cuerno([rodilla + (pie - rodilla) * 0.55, rodilla + (pie - rodilla) * 0.8 + u * 0.15, pie], 0.2, "garra", n=5, seg=3)
            M.articulacion(f"pata_{i + 1}_{lado}", "cuerpo", tuple(cadera))
