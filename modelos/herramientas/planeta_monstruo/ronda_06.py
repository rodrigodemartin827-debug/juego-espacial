"""Ronda 6: crías y bestias raras (51-55) y zona de guerra (56-60)."""

import math

import numpy as np

from formas import craneo, hueso_largo, silla
from lib import ROJO, VERDE, VIOLETA, curva, modelo

NEON_V = dict(material="Neon", color=VIOLETA)


@modelo("bestias", "bestia_menor", (8, 10, 3), "Cría de mantarraya: versión pequeña y rechoncha, para principiantes. 1 asiento.")
def bestia_cria_mantarraya(M):
    M.mat("piel_cria", "piel_purpura", a="#5A2E82", b="#2A1444", rug=0.45)
    M.mat("panza", "carne_palida", a="#B09AC0", b="#6A4A82")
    Z = 1.2

    def cuerpo(p, mat, infla=0.0):
        p.esfera((0, 0, Z), 1, mat, esc=(1.5, 2.5, 0.8), infla=infla)
        p.esfera((0, -1.9, Z), 1, mat, esc=(1.25, 1.2, 0.68), infla=infla)

    def ala(p, s, mat, infla=0.0):
        p.esfera((s * 2.2, 0.2, Z + 0.05), 1, mat, esc=(1.7, 2.1, 0.32), rot=(0, -s * 6, s * 10), infla=infla)
        p.esfera((s * 3.5, 0.7, Z + 0.3), 1, mat, esc=(0.9, 1.1, 0.2), rot=(0, -s * 18, s * 20), infla=infla)

    c = M.pieza("cuerpo", tris=2300, res=150, k=0.3, ruido=(0.015, 1.8))
    cuerpo(c, "piel_cria")
    c.esfera((0, -0.5, Z - 0.42), 1, "panza", esc=(1.2, 2.1, 0.4))
    for s in (-1, 1):
        c.tubo([(s * 0.85, -2.6, Z - 0.05), (s * 1.05, -3.3, Z - 0.15), (s * 0.7, -3.75, Z - 0.3)], [0.32, 0.24, 0.1], "piel_cria", k=0.15)
        c.esfera((s * 1.1, -2.1, Z + 0.25), 0.36, "piel_cria", k=0.12)     # ojos saltones de cría
        c.esfera((s * 1.3, -2.25, Z + 0.3), 0.24, "negro", resta=True, k=0.03)
    c.esfera((0, -2.95, Z - 0.2), 1, "carne_viva", esc=(0.6, 0.4, 0.14), resta=True, k=0.05)
    silla(M, c, (0, -0.2, Z + 0.82), s=0.72)
    n = M.pieza("manchas_neon", tris=700, res=190, roblox=NEON_V)
    cuerpo(n, "neon_violeta", infla=0.04)
    for s in (-1, 1):
        ala(n, s, "neon_violeta", infla=0.04)
    with n.mascara():
        for i in range(5):
            n.capsula((0, 0.9 + i * 0.5, Z), (0, 0.9 + i * 0.5, Z + 2), 0.2 - 0.015 * i, "neon_violeta")
        for s in (-1, 1):
            for i in range(5):
                x, y = s * (1.5 + 0.5 * i), -0.6 + 0.35 * i + 0.5 * math.sin(i * 2.0)
                n.capsula((x, y, Z), (x, y, Z + 2), 0.27 - 0.02 * i, "neon_violeta")
    n.duro.esfera((1.25, -2.22, Z + 0.3), 0.19, "neon_violeta", sub=1, sim=True)
    M.articulacion("manchas_neon", "cuerpo", (0, 0, Z))
    for s, lado in ((-1, "izq"), (1, "der")):
        a = M.pieza(f"ala_{lado}", tris=1500, res=140, k=0.5, ruido=(0.015, 1.8))
        ala(a, s, "piel_cria")
        M.articulacion(f"ala_{lado}", "cuerpo", (s * 1.1, 0.1, Z))
    t = M.pieza("cola", tris=800, res=130, k=0.1, ruido=(0.012, 2.0))
    t.tubo(curva([(0, 2.3, Z), (0, 3.8, Z + 0.1), (0, 5.2, Z + 0.7), (0, 6.0, Z + 1.5)], 8), [0.36, 0.24, 0.14, 0.07], "piel_cria")
    t.duro.cuerno([(0, 6.0, Z + 1.5), (0, 6.3, Z + 1.75), (0, 6.25, Z + 1.3)], 0.12, "garra", n=5, seg=3)
    M.articulacion("cola", "cuerpo", (0, 2.4, Z))


@modelo("bestias", "bestia_menor", (3, 12, 3), "Cría de gusano: rápida pero frágil. 1 asiento.")
def bestia_cria_gusano(M):
    M.mat("piel_cria", "carne_palida", a="#C09AA0", b="#7A4A62", rug=0.4)
    Z = 1.55

    def tramo(p, ys, r0, r1):
        for i, y in enumerate(ys):
            r = r0 + (r1 - r0) * i / max(1, len(ys) - 1)
            p.esfera((0, y, Z), 1, "piel_cria", esc=(r, 0.85, r * 0.92))
            p.esfera((0, y, Z + r * 0.5), 1, "quitina", esc=(r * 0.62, 0.62, r * 0.5), k=0.1)
            for s in (-1, 1):
                p.tubo([(s * r * 0.7, y, Z - r * 0.5), (s * r * 1.0, y - 0.1, 0.12)], [0.2, 0.1], "quitina", k=0.08)

    h = M.pieza("cabeza", tris=1800, res=140, k=0.15, ruido=(0.02, 1.8))
    h.esfera((0, -4.9, Z), 1, "piel_cria", esc=(1.15, 1.2, 1.1))
    h.esfera((0, -4.6, Z + 0.5), 1, "quitina", esc=(0.9, 0.9, 0.7), k=0.1)
    h.esfera((0, -5.9, Z), 0.75, "carne_viva", esc=(1, 0.8, 1), resta=True, k=0.08)
    h.toro((0, -5.72, Z), 0.78, 0.13, "musculo", eje=(0, 1, 0), k=0.05)
    for j in range(10):
        a = math.tau * j / 10
        b = np.array([0.72 * math.cos(a), -5.72, Z + 0.72 * math.sin(a)])
        h.duro.cono(b, b * [0.5, 1, 1] + [0, -0.15, (Z - b[2]) * 0.5], 0.07, "diente", n=4)
    for s in (-1, 1):
        h.duro.cuerno([(s * 0.85, -5.5, Z - 0.3), (s * 1.3, -6.2, Z - 0.4), (s * 0.7, -6.7, Z - 0.35)], 0.15, "garra", n=5, seg=4)
        h.duro.tubo([(s * 0.5, -5.2, Z + 0.9), (s * 0.9, -5.7, Z + 1.5), (s * 1.1, -6.3, Z + 1.4)], [0.05, 0.04, 0.06], "quitina", n=4)  # antenas
    on = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    on.duro.esfera((0.9, -5.0, Z + 0.55), 0.17, "neon_verde", sub=1, sim=True)
    on.duro.esfera((0.75, -5.35, Z + 0.72), 0.1, "neon_verde", sub=1, sim=True)
    d = M.pieza("cuerpo_delantero", tris=2200, res=140, k=0.2, ruido=(0.02, 1.6))
    tramo(d, (-3.6, -2.35, -1.1), 1.2, 1.25)
    silla(M, d, (0, -2.4, Z + 1.28), s=0.7)
    t = M.pieza("cuerpo_trasero", tris=2200, res=140, k=0.2, ruido=(0.02, 1.6))
    tramo(t, (0.15, 1.4, 2.65, 3.8), 1.2, 0.9)
    c = M.pieza("cola", tris=700, res=110, k=0.15, ruido=(0.02, 1.6))
    c.tubo([(0, 4.7, Z), (0, 5.6, Z + 0.1), (0, 6.3, Z + 0.6)], [0.75, 0.45, 0.16], "piel_cria")
    c.duro.cuerno([(0, 6.3, Z + 0.6), (0, 6.75, Z + 1.0), (0, 6.6, Z + 1.5)], 0.14, "garra", n=5, seg=3)
    M.articulacion("cabeza", "cuerpo_delantero", (0, -4.1, Z))
    M.articulacion("ojos_neon", "cabeza", (0, -5.0, Z + 0.6))
    M.articulacion("cuerpo_trasero", "cuerpo_delantero", (0, -0.5, Z))
    M.articulacion("cola", "cuerpo_trasero", (0, 4.5, Z))
    M.raiz = "cuerpo_delantero"


@modelo("bestias", "bestia", (16, 14, 14), "Hidra de tres cabezas: tres cuellos largos y cada cabeza escupe un elemento "
        "distinto (verde, púrpura, rojo). Jefe raro: 1 asiento entre los cuellos y bahía de carga.")
def bestia_hidra(M):
    M.mat("piel_hidra", "piel", a="#243A30", b="#1A1026", rug=0.5, escamas=dict(esc=3.0, fuerza=0.8))
    M.mat("panza", "carne_palida", a="#9A8A6A", b="#5A4A4A", escamas=dict(esc=2.0, fuerza=0.4))
    c = M.pieza("cuerpo", tris=3300, res=160, k=0.6, ruido=(0.04, 1.0))
    c.esfera((0, 1.0, 4.0), 1, "piel_hidra", esc=(3.0, 3.6, 2.4))
    c.esfera((0, -1.6, 4.6), 1, "piel_hidra", esc=(2.9, 2.2, 2.3))
    c.esfera((0, 0.6, 2.7), 1, "panza", esc=(2.3, 3.4, 1.2))
    for x in (-1.9, 0, 1.9):
        c.esfera((x, -2.8, 5.6), 1.15, "piel_hidra", k=0.4)   # arranque de cada cuello
    for i in range(5):
        y = 0.9 + i * 0.95
        c.duro.cuerno([(0, y, 6.3 - 0.08 * y * y), (0, y + 0.3, 7.2 - 0.09 * y * y), (0, y + 1.0, 7.5 - 0.1 * y * y)], 0.3, "garra", n=5, seg=3, aplastar=0.45)
    silla(M, c, (0, -0.9, 6.95), s=0.95)
    for s in (-1, 1):  # bahía de carga: alforjas en las caderas
        c.esfera((s * 2.5, 2.2, 5.0), 1, "cuero", esc=(0.8, 1.2, 0.9), k=0.12)
        c.tubo([(s * 1.4, 2.2, 6.0), (s * 3.0, 2.2, 5.6), (s * 3.2, 2.2, 4.4)], 0.09, "tendon", k=0.03)
    M.bahia((0, 2.2, 5.2), (6.0, 2.4, 1.8), "dos alforjas grandes, una en cada cadera")
    t = M.pieza("cola", tris=1300, res=140, k=0.2, ruido=(0.03, 1.2))
    cola = curva([(0, 4.2, 3.9), (0.8, 5.6, 2.6), (0, 6.9, 1.6), (-1.0, 7.8, 1.9)], 12)
    t.tubo(cola, [1.5, 1.0, 0.62, 0.28], "piel_hidra")
    t.duro.cuerno([cola[-1], cola[-1] + [-0.6, 0.8, 0.6], cola[-1] + [-0.5, 1.3, 1.6]], 0.3, "garra", n=6, seg=4)
    M.articulacion("cola", "cuerpo", (0, 4.2, 3.9))
    for s, lado in ((-1, "izq"), (1, "der")):
        for nombre, y0 in (("pata_del", -1.6), ("pata_tras", 2.6)):
            p = M.pieza(f"{nombre}_{lado}", tris=750, res=120, k=0.2, ruido=(0.025, 1.4))
            p.tubo([(s * 2.4, y0, 3.6), (s * 3.6, y0 + 0.3, 2.4), (s * 3.5, y0 - 0.3, 0.5)], [1.1, 0.85, 0.6], "piel_hidra", suave=6)
            p.esfera((s * 3.5, y0 - 0.6, 0.35), 1, "piel_hidra", esc=(0.75, 1.0, 0.36))
            for k_ in (-1, 0, 1):
                p.duro.cuerno([(s * 3.5 + k_ * 0.42, y0 - 1.3, 0.4), (s * 3.5 + k_ * 0.55, y0 - 1.9, 0.5), (s * 3.5 + k_ * 0.6, y0 - 2.2, 0.0)], 0.18, "garra", n=5, seg=3)
            M.articulacion(f"{nombre}_{lado}", "cuerpo", (s * 2.4, y0, 3.6))
    cabezas = [("verde", -1.9, [(-1.9, -2.9, 5.8), (-4.2, -3.6, 8.2), (-6.0, -4.2, 9.8), (-6.6, -5.2, 9.6)], VERDE, "fuego_verde"),
               ("violeta", 0.0, [(0, -3.0, 6.0), (0, -3.6, 9.4), (0, -4.4, 12.2), (0, -5.6, 12.6)], VIOLETA, "fuego_violeta"),
               ("roja", 1.9, [(1.9, -2.9, 5.8), (4.4, -3.8, 7.6), (6.2, -4.8, 7.8), (6.8, -5.8, 7.0)], ROJO, "fuego_rojo")]
    M.mat("fuego_rojo", "neon_rojo", a="#FF2A2A", b="#FFB08A")
    for nombre, x0, ruta, color, mat_f in cabezas:
        n = M.pieza(f"cuello_{nombre}", tris=1100, res=140, k=0.2, ruido=(0.03, 1.2))
        pts = curva(ruta, 12)
        n.tubo(pts, [1.05, 0.85, 0.7, 0.62], "piel_hidra")
        n.tubo([np.array(q) + [0, -0.35, -0.3] for q in pts], [0.62, 0.5, 0.42, 0.36], "panza", k=0.15)
        for i in range(2, 11, 2):
            q = np.array(pts[i])
            n.duro.cono(q + [0, 0.45, 0.5], q + [0, 1.0, 1.2], 0.17, "garra", n=5)
        M.articulacion(f"cuello_{nombre}", "cuerpo", tuple(ruta[0]))
        H = np.array(ruta[-1])
        dire = H - np.array(ruta[-2])
        giro = math.degrees(math.atan2(dire[0], -dire[1]))
        cabeceo = -math.degrees(math.atan2(dire[2], math.hypot(dire[0], dire[1])))
        h = M.pieza(f"cabeza_{nombre}", tris=1300, res=130, k=0.15, ruido=(0.02, 1.6))
        on = M.pieza(f"ojos_{nombre}_neon", tris=0, roblox=dict(material="Neon", color=color))
        j = M.pieza(f"mandibula_{nombre}", tris=450, res=90, k=0.1)
        f = M.pieza(f"aliento_{nombre}_neon", tris=420, res=70, k=0.2, ruido=(0.05, 1.8), roblox=dict(material="Neon", color=color, transparencia=0.15))
        rot = (cabeceo * 0.6, 0, -giro)
        with h.en(H, rot=rot):
            h.esfera((0, -0.4, 0), 1, "piel_hidra", esc=(0.85, 1.1, 0.75))
            h.esfera((0, -1.6, -0.05), 1, "piel_hidra", esc=(0.6, 1.2, 0.48))
            h.tubo([(0.2, -1.6, 0.36), (0.62, -0.8, 0.6), (0.82, 0.1, 0.5)], [0.14, 0.24, 0.16], "quitina", sim=True)
            h.esfera((0.62, -0.95, 0.3), 0.22, "negro", sim=True, resta=True, k=0.04)
            h.esfera((0, -1.5, -0.6), 1, "carne_viva", esc=(0.45, 1.2, 0.3), resta=True, k=0.06)
            h.duro.cuerno([(0.5, 0.2, 0.5), (0.9, 1.1, 1.0), (0.7, 2.0, 1.5)], 0.22, "garra", n=6, seg=4, sim=True)
            if nombre == "violeta":
                h.duro.cuerno([(0, -0.2, 0.7), (0, 0.4, 1.5), (0, 1.3, 1.9)], 0.2, "garra", n=6, seg=4)
            for i in range(5):
                h.duro.cono((0.48 - 0.03 * i, -0.8 - i * 0.42, -0.36), (0.48 - 0.03 * i, -0.85 - i * 0.42, -0.78), 0.08, "diente", n=4, sim=True)
        with on.en(H, rot=rot):
            on.duro.esfera((0.56, -0.92, 0.3), 0.15, {VERDE: "neon_verde", VIOLETA: "neon_violeta", ROJO: "neon_rojo"}[color], sub=1, sim=True)
        with j.en(H, rot=(rot[0] + 24, 0, rot[2])):
            j.tubo([(0.62, 0.2, -0.45), (0.5, -1.2, -0.8), (0, -2.5, -0.75)], [0.24, 0.2, 0.2], "piel_hidra", sim=True)
            j.esfera((0, -0.9, -0.9), 1, "panza", esc=(0.45, 1.2, 0.2))
            for i in range(4):
                j.duro.cono((0.42 - 0.04 * i, -1.0 - i * 0.4, -0.72), (0.42 - 0.04 * i, -1.0 - i * 0.4, -0.36), 0.07, "diente", n=4, sim=True)
        with f.en(H, rot=(rot[0] + 12, 0, rot[2])):
            f.esfera((0, -1.6, -0.55), 0.34, mat_f)
            f.tubo([(0, -1.8, -0.55), (0, -2.6, -0.5), (0.1, -3.4, -0.6)], [0.3, 0.42, 0.08], mat_f)
            f.tubo([(0, -2.5, -0.5), (-0.3, -3.1, -0.2)], [0.22, 0.05], mat_f)
        M.articulacion(f"cabeza_{nombre}", f"cuello_{nombre}", tuple(H + [0, 0.5, 0]))
        M.articulacion(f"mandibula_{nombre}", f"cabeza_{nombre}", tuple(H + [0, 0.2, -0.4]))
        M.articulacion(f"ojos_{nombre}_neon", f"cabeza_{nombre}", tuple(H))
        M.articulacion(f"aliento_{nombre}_neon", f"cabeza_{nombre}", tuple(H))


@modelo("bestias", "bestia", (14, 14, 10), "Kraken pequeño del espacio: cuerpo central con 8 tentáculos, pico en el centro "
        "y ojos grandes. Control de zona: 1 asiento en la cabeza.")
def bestia_kraken(M):
    rnd = M.rnd
    M.mat("piel_kraken", "piel_purpura", a="#5A1E4A", b="#22102E", rug=0.38, manchas=dict(color="#8A3A6A", esc=1.6, radio=0.25))
    M.mat("ventosa", "carne_palida", a="#C8A0B0", b="#8A5A7A")
    c = M.pieza("manto", tris=4200, res=170, k=0.5, ruido=(0.05, 0.9))
    c.esfera((0, 0.6, 6.4), 1, "piel_kraken", esc=(2.6, 2.9, 3.6), rot=(-12, 0, 0))     # manto
    c.esfera((0, 0, 3.2), 1, "piel_kraken", esc=(2.5, 2.5, 1.7))                        # cabeza
    for s in (-1, 1):
        c.esfera((s * 1.9, -1.2, 3.6), 0.95, "piel_kraken", k=0.3)                      # órbitas
        c.esfera((s * 2.35, -1.6, 3.65), 0.62, "negro", resta=True, k=0.06)
        c.esfera((s * 2.4, 2.0, 8.0), 1, "piel_kraken", esc=(0.25, 1.3, 1.5), rot=(0, s * 20, 0), k=0.3)  # aletas del manto
    for i in range(6):
        c.duro.cuerno([(0, 1.6 + 0.2 * i, 7.0 + i * 0.5), (0, 2.4 + 0.2 * i, 7.5 + i * 0.5), (0, 3.2 + 0.25 * i, 7.3 + i * 0.5)], 0.22, "garra", n=5, seg=3)
    c.torno([(0, 0.6), (1.2, 0.3), (1.6, -0.3), (0, -0.2)], (0, 0, 1.9), "carne_viva", k=0.15)   # boca, abajo
    silla(M, c, (0, -0.5, 4.95), s=0.95)
    b = M.pieza("pico", tris=0)
    b.duro.cuerno([(0, 0.4, 1.7), (0, -0.2, 0.9), (0, 0.35, 0.35)], 0.5, "garra", n=7, seg=5, aplastar=0.7)
    b.duro.cuerno([(0, -0.5, 1.7), (0, -0.1, 1.1), (0, -0.35, 0.6)], 0.4, "garra", n=7, seg=4, aplastar=0.7)
    M.articulacion("pico", "manto", (0, 0, 1.7))
    on = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color="#FFD21F"))
    on.duro.esfera((2.15, -1.48, 3.65), 0.5, "neon_amarillo", sub=2, sim=True)
    c.duro.esfera((2.52, -1.78, 3.65), 0.13, "pupila", sub=1, esc=(0.6, 0.6, 3.0), sim=True)
    M.articulacion("ojos_neon", "manto", (0, -1.5, 3.65))
    for j in range(8):
        a = math.tau * (j + 0.5) / 8
        ca, sa = math.cos(a), math.sin(a)
        t = M.pieza(f"tentaculo_{j + 1}", tris=1250, res=150, k=0.1, ruido=(0.025, 1.4))
        giro = 0.5 if j % 2 else -0.45
        pts = []
        for i in range(9):
            f = i / 8
            r = 1.6 + 5.2 * f
            an = a + giro * f * f * 1.8
            z = 2.4 * (1 - f) ** 2 + 0.45 + (1.9 * max(0.0, f - 0.7) / 0.3 if j % 2 else 0.25 * math.sin(f * 7))
            pts.append((r * math.cos(an), r * math.sin(an), z))
        t.tubo(pts, [0.95, 0.8, 0.66, 0.52, 0.4, 0.3, 0.22, 0.15, 0.07], "piel_kraken", suave=16)
        for i in range(1, 8):  # ventosas por debajo: copa con su anillo
            q = np.array(pts[i])
            r = 0.26 - 0.026 * i
            lado = np.array([-sa, ca, 0]) * r * 1.2
            for sg in (-1, 1):
                p0 = q + lado * sg - [0, 0, (0.92 - 0.1 * i) * 0.8]
                t.duro.toro(p0, r, r * 0.36, "ventosa", eje=(0, 0, -1), n=7, m=3)
        M.articulacion(f"tentaculo_{j + 1}", "manto", (1.6 * ca, 1.6 * sa, 2.6))


@modelo("bestias", "bestia", (20, 16, 10), "Fénix oscuro: ave envuelta en llamas púrpura y negras, con alas enormes de "
        "fuego. La más rara: se regenera. 1 asiento en el lomo.")
def bestia_fenix_oscuro(M):
    rnd = M.rnd
    M.mat("pluma_negra", "quitina_negra", a="#0C0A12", b="#2A1440", rug=0.4, escamas=dict(esc=4.0, fuerza=0.9))
    M.mat("brasa", "lava_purpura", a="#C04DFF", b="#3A0F5A")
    M.mat("llama", "fuego_violeta", a="#C04DFF", b="#F2D0FF")
    M.mat("llama_oscura", "fuego_violeta", a="#5A1E9A", b="#C04DFF", emis=(VIOLETA, 0.6))
    FUEGO = dict(material="Neon", color=VIOLETA, transparencia=0.2)
    Z = 4.6
    c = M.pieza("cuerpo", tris=3000, res=150, k=0.4, ruido=(0.03, 1.3))
    c.esfera((0, 0, Z), 1, "pluma_negra", esc=(1.5, 2.8, 1.4))
    c.esfera((0, -1.6, Z + 0.3), 1, "brasa", esc=(1.2, 1.2, 1.2))     # el pecho arde por dentro
    c.tubo([(0, -2.2, Z + 0.7), (0, -3.0, Z + 2.0), (0, -3.6, Z + 3.0)], [0.95, 0.66, 0.5], "pluma_negra", k=0.3)
    for s in (-1, 1):  # patas recogidas con garras
        c.tubo([(s * 0.8, 0.6, Z - 0.9), (s * 0.95, 0.0, Z - 2.0), (s * 0.95, 0.9, Z - 2.7)], [0.5, 0.28, 0.2], "pluma_negra", k=0.1)
        for k_ in (-1, 0, 1):
            c.duro.cuerno([(s * 0.95 + k_ * 0.1, 0.9, Z - 2.7), (s * 0.95 + k_ * 0.36, 0.5, Z - 3.3), (s * 0.95 + k_ * 0.4, -0.1, Z - 3.2)], 0.12, "garra", n=5, seg=3)
    silla(M, c, (0, 0.2, Z + 1.42), s=0.9)
    h = M.pieza("cabeza", tris=1500, res=130, k=0.12, ruido=(0.02, 1.8))
    H = np.array([0, -4.0, Z + 3.4])
    with h.en(H, rot=(12, 0, 0)):
        h.esfera((0, 0, 0), 1, "pluma_negra", esc=(0.68, 0.85, 0.66))
        h.tubo([(0, -0.6, 0.0), (0, -1.5, -0.15), (0, -2.0, -0.7)], [0.36, 0.24, 0.06], "garra", suave=6, k=0.06)
        h.tubo([(0, -0.5, -0.36), (0, -1.3, -0.5)], [0.22, 0.08], "garra", k=0.04)
        h.esfera((0.5, -0.4, 0.14), 0.18, "negro", sim=True, resta=True, k=0.03)
        h.tubo([(0.15, -0.7, 0.36), (0.5, -0.3, 0.42), (0.6, 0.3, 0.3)], [0.1, 0.14, 0.08], "pluma_negra", sim=True, k=0.05)
    on = M.pieza("ojos_neon", tris=0, roblox=NEON_V)
    with on.en(H, rot=(12, 0, 0)):
        on.duro.esfera((0.46, -0.4, 0.14), 0.14, "neon_violeta", sub=1, sim=True)
    cr = M.pieza("cresta_fuego_neon", tris=500, res=80, k=0.2, ruido=(0.07, 1.8), roblox=FUEGO)
    for i in range(4):
        cr.tubo([H + [0, 0.1 + 0.3 * i, 0.5], H + [0.15 * (i % 2 - 0.5), 0.8 + 0.5 * i, 1.4 + 0.2 * i], H + [0, 1.6 + 0.6 * i, 2.1 - 0.15 * i]], [0.3, 0.24, 0.05], "llama")
    M.articulacion("cabeza", "cuerpo", (0, -3.5, Z + 2.8))
    M.articulacion("ojos_neon", "cabeza", tuple(H))
    M.articulacion("cresta_fuego_neon", "cabeza", tuple(H))
    for s, lado in ((-1, "izq"), (1, "der")):
        w = M.pieza(f"ala_{lado}", tris=1900, res=140, k=0.2, ruido=(0.025, 1.4))
        hombro = np.array([s * 1.2, -1.0, Z + 0.9])
        codo = np.array([s * 4.4, -1.9, Z + 2.6])
        mano = np.array([s * 7.6, -0.7, Z + 3.3])
        w.tubo([hombro, codo, mano], [0.72, 0.5, 0.3], "pluma_negra")
        w.esfera(codo, 0.6, "pluma_negra", k=0.15)
        for i in range(9):  # plumas negras cortas: quedan como costillas carbonizadas bajo el fuego
            t = i / 8
            base = hombro + (codo - hombro) * min(1, t * 2) + (mano - codo) * max(0, t * 2 - 1)
            ang = math.radians(10 + 60 * t)
            dire = np.array([s * math.sin(ang), math.cos(ang), -0.25])
            L = 1.7 + 1.2 * t
            lado_ = np.cross(dire, [0, 0, 1.0]) * 0.3
            w.duro.lamina([base - lado_ * 0.5, base + dire * L * 0.5 - lado_, base + dire * L, base + dire * L * 0.5 + lado_, base + lado_ * 0.5], 0.08, "pluma_negra", bombeo=0.05)
        M.articulacion(f"ala_{lado}", "cuerpo", tuple(hombro))
        # El ala de fuego: lenguas de llama con volumen que salen del brazo hacia atrás y hacia fuera.
        f = M.pieza(f"ala_fuego_{lado}_neon", tris=2300, res=150, k=0.5, ruido=(0.12, 0.9), roblox=FUEGO)
        for i in range(11):
            t = i / 10
            base = hombro + (codo - hombro) * min(1, t * 2) + (mano - codo) * max(0, t * 2 - 1)
            ang = math.radians(4 + 78 * t ** 1.2)
            dire = np.array([s * math.sin(ang), math.cos(ang), 0.1 + 0.25 * t])
            L = 2.3 + 2.3 * t + rnd.uniform(-0.4, 0.4)
            onda = np.array([0, 0, 0.6 * math.sin(i * 1.7)])
            f.tubo([base + dire * 0.8, base + dire * L * 0.5 + onda, base + dire * L * 0.85 - onda * 0.5, base + dire * L],
                   [0.5, 0.62, 0.36, 0.06], "llama" if i % 3 else "llama_oscura", suave=8)
        M.articulacion(f"ala_fuego_{lado}_neon", f"ala_{lado}", tuple(hombro))
    t = M.pieza("cola_fuego_neon", tris=2000, res=150, k=0.4, ruido=(0.1, 0.9), roblox=FUEGO)
    for i in range(5):
        a = math.radians(-28 + 14 * i)
        L = 7.0 - 1.2 * abs(i - 2)
        pts = [(0.5 * math.sin(a), 2.4, Z), (2.2 * math.sin(a), 2.4 + L * 0.4, Z + 0.6 * math.sin(i * 2.0)), (4.0 * math.sin(a), 2.4 + L * 0.75, Z - 0.6),
               (5.0 * math.sin(a), 2.4 + L, Z - 0.2 + 0.5 * (i % 2))]
        t.tubo(pts, [0.5, 0.62, 0.42, 0.06], "llama" if i % 2 == 0 else "llama_oscura", suave=10)
    M.articulacion("cola_fuego_neon", "cuerpo", (0, 2.4, Z))
    M.notas["regeneracion"] = "Las piezas *_fuego_neon son las que el juego apaga y vuelve a encender cuando se regenera."


@modelo("guerra", "grande", (16, 16, 4), "Arena de combate circular: suelo de hueso pulido, gradas de roca con espinas y "
        "manchas de sangre.")
def arena_combate(M):
    rnd = M.rnd
    M.mat("hueso_pulido", "hueso", a="#CFC4A6", b="#9A8A6E", rug=0.3, relieve=0.2, manchas=dict(color="#5A0A12", esc=0.9, radio=0.2))
    p = M.pieza("arena", tris=10500, res=200, k=0.15, ruido=(0.07, 0.7), suelo=0.0)
    p.cilindro((0, 0, -0.5), (0, 0, 0.5), 5.4, "hueso_pulido", k=0.0)
    puertas = [-math.pi / 2, math.pi / 2, 0.0, math.pi]

    def lejos(a, ancho):
        return all(abs(((a - g + math.pi) % math.tau) - math.pi) > ancho for g in puertas)

    # Gradas: dos anillos de bloques de roca, el de fuera más alto.
    for R, alto, n, tam in ((6.1, 1.3, 30, 0.82), (7.25, 2.4, 34, 0.9)):
        for j in range(n):
            a = math.tau * j / n
            if not lejos(a, 0.24 if R < 7 else 0.2):
                continue
            h = alto * rnd.uniform(0.85, 1.12)
            p.caja((R * math.cos(a), R * math.sin(a), h / 2), (1.25, tam * 1.55, h), "piedra", red=0.22, rot=(0, 0, math.degrees(a)), k=0.12)
    for g in puertas:  # jambas de hueso en cada puerta
        for lado in (-1, 1):
            a = g + lado * 0.215
            p.tubo([(6.0 * math.cos(a), 6.0 * math.sin(a), 0), (6.6 * math.cos(a), 6.6 * math.sin(a), 2.2), (7.0 * math.cos(g + lado * 0.1), 7.0 * math.sin(g + lado * 0.1), 3.5)],
                   [0.5, 0.4, 0.16], "hueso_viejo", suave=8)
    # Dibujo del suelo: anillo y radios tallados.
    p.toro((0, 0, 0.5), 2.2, 0.09, None, resta=True)
    p.toro((0, 0, 0.5), 4.6, 0.09, None, resta=True)
    for j in range(8):
        a = math.tau * j / 8 + 0.39
        p.capsula((2.3 * math.cos(a), 2.3 * math.sin(a), 0.5), (4.5 * math.cos(a), 4.5 * math.sin(a), 0.5), 0.07, None, resta=True)
    d = p.duro
    for j in range(34):  # espinas en lo alto de la grada exterior
        a = math.tau * j / 34
        if not lejos(a, 0.2):
            continue
        b = np.array([7.5 * math.cos(a), 7.5 * math.sin(a), 2.2])
        L = rnd.uniform(1.0, 1.7)
        d.cuerno([b, b * [1.05, 1.05, 1] + [0, 0, L * 0.6], b * [1.0, 1.0, 1] + [0, 0, L]], 0.2, "garra", n=5, seg=3)
    for j in range(7):  # charcos de sangre con grosor
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.6, 4.6)
        d.esfera((r * math.cos(a), r * math.sin(a), 0.5), rnd.uniform(0.3, 0.7), "sangre", sub=2, esc=(1, rnd.uniform(0.6, 1.0), 0.05), rot=(0, 0, rnd.uniform(0, 180)))
    cr = M.pieza("restos", tris=1200, res=100, unir="arena")
    for (x, y, g) in ((3.9, 2.8, 40), (-4.3, -1.5, 200)):
        with cr.en((x, y, 0.52), rot=(rnd.uniform(-20, 20), rnd.uniform(60, 100) if x > 0 else 0, g), esc=0.62):
            craneo(cr, rnd, mat="hueso_viejo", mandibula=x < 0)
    hueso_largo(cr, (-2.6, 3.3, 0.62), (-1.2, 3.9, 0.62), 0.11, mat="hueso_viejo")


@modelo("guerra", "prop", (2, 1, 5), "Maniquí de entrenamiento de huesos y carne, para practicar ataques.")
def muneco_entrenamiento(M):
    rnd = M.rnd
    M.mat("saco", "cuero", a="#6A3A3A", b="#3A1E24")
    p = M.pieza("muneco", tris=1250, res=190, k=0.07, ruido=(0.025, 2.0), suelo=0.0)
    p.tubo([(0, 0, 0), (0.03, 0, 2.2), (0, 0, 4.1)], [0.2, 0.15, 0.13], "hueso_viejo")
    p.esfera((0, 0, 0), 1, "piedra", esc=(0.62, 0.5, 0.32))
    p.esfera((0, 0, 2.7), 1, "saco", esc=(0.6, 0.42, 0.95))                 # torso: saco de carne cosido
    p.esfera((0, -0.05, 2.0), 1, "saco", esc=(0.48, 0.38, 0.5))
    p.tubo([(-0.95, 0, 3.3), (0.95, 0, 3.3)], 0.11, "hueso", k=0.04)           # travesaño = hombros
    for s in (-1, 1):
        p.esfera((s * 0.95, 0, 3.3), 0.17, "hueso", k=0.03)
        p.tubo([(s * 0.95, 0, 3.25), (s * 1.0, -0.1, 2.5)], [0.09, 0.075], "hueso", k=0.03)   # brazo colgando
    for i in range(3):  # tajos de garra en el pecho
        p.capsula((-0.3 + i * 0.22, -0.42, 3.2), (-0.1 + i * 0.22, -0.4, 2.4), 0.045, "carne_viva", resta=True, k=0.02)
    d = p.duro
    for z in (2.2, 2.75, 3.15):  # cuerdas de tendón
        d.toro((0, 0, z), 0.56 if z < 3 else 0.5, 0.03, "tendon", n=10, m=3, esc=(1, 0.72, 1))
    for s in (-1, 1):
        d.cuerno([(s * 1.0, -0.1, 2.5), (s * 1.05, -0.3, 2.2), (s * 0.9, -0.4, 2.0)], 0.07, "garra", n=4, seg=2)
    cr = M.pieza("cabeza", tris=600, res=80, unir="muneco")
    with cr.en((0, -0.05, 4.0), rot=(8, 0, rnd.uniform(-12, 12)), esc=0.8):
        craneo(cr, rnd, mat="hueso", cuernos=2)


@modelo("guerra", "prop", (4, 1, 4), "Estantería de armas orgánicas: garras, lanzas de hueso y hachas de colmillo colgadas.")
def rack_armas_organicas(M):
    p = M.pieza("rack", tris=1050, res=190, k=0.05, ruido=(0.018, 2.2), suelo=0.0)
    for s in (-1, 1):
        p.tubo([(s * 1.75, 0.25, 0), (s * 1.8, 0.0, 1.8), (s * 1.7, -0.1, 3.3)], [0.17, 0.13, 0.1], "hueso_viejo")
        p.tubo([(s * 1.8, 0.0, 1.5), (s * 1.75, 0.42, 0)], [0.09, 0.11], "hueso_viejo", k=0.03)   # tornapunta
        p.esfera((s * 1.75, 0.3, 0), 0.26, "piedra", esc=(1, 1.4, 0.5))
    for z in (1.15, 2.9):
        p.tubo([(-1.95, -0.03, z), (0, -0.1, z + 0.05), (1.95, -0.03, z)], 0.085, "hueso", k=0.03)
    d = p.duro
    for s in (-1, 1):
        for z in (1.15, 2.9):
            d.toro((s * 1.78, -0.03, z), 0.15, 0.03, "tendon", eje=(0, 1, 0), n=6, m=3)
    # Lanzas de hueso (dos, largas).
    for x in (-1.3, -0.95):
        d.tubo([(x, -0.22, 0.15), (x, -0.2, 3.1)], 0.04, "corteza", n=5)
        d.prisma((x, -0.2, 3.05), (x, -0.2, 3.95), 0.11, "hueso", n=4, punta=0.75)
        d.toro((x, -0.2, 3.02), 0.06, 0.025, "tendon", n=5, m=3)
    # Hachas de colmillo: mango y hoja curva (dos colmillos atados).
    for x in (-0.35, 0.3):
        d.tubo([(x, -0.22, 0.6), (x + 0.03, -0.2, 2.6)], 0.045, "corteza", n=5)
        d.cuerno([(x - 0.05, -0.2, 2.5), (x + 0.42, -0.2, 2.75), (x + 0.5, -0.2, 2.05)], 0.14, "diente", n=6, seg=5, aplastar=0.4)
        d.cuerno([(x + 0.05, -0.2, 2.5), (x - 0.3, -0.2, 2.68), (x - 0.36, -0.2, 2.3)], 0.09, "diente", n=5, seg=4, aplastar=0.4)
        d.toro((x + 0.02, -0.2, 2.5), 0.07, 0.03, "tendon", n=5, m=3)
    # Guantelete de garras (cuelga del travesaño de arriba).
    d.tubo([(0.95, -0.12, 2.9), (0.95, -0.2, 2.55)], 0.02, "tendon", n=3)
    d.esfera((0.95, -0.22, 2.3), 0.2, "cuero", sub=1, esc=(1, 0.6, 1.2))
    for i in range(4):
        x = 0.8 + i * 0.1
        d.cuerno([(x, -0.24, 2.12), (x - 0.03, -0.36, 1.75), (x, -0.22, 1.4)], 0.045, "garra", n=4, seg=3)
    # Espada-mandíbula: media mandíbula con los dientes como filo.
    d.cuerno([(1.4, -0.22, 0.5), (1.5, -0.2, 1.6), (1.35, -0.2, 2.7)], 0.1, "hueso", n=5, seg=5, aplastar=0.5, potencia=0.5)
    for i in range(6):
        z = 1.2 + i * 0.22
        d.cono((1.42 - 0.01 * i, -0.2, z), (1.25 - 0.01 * i, -0.2, z + 0.06), 0.045, "diente", n=4)
    d.toro((1.41, -0.21, 0.75), 0.07, 0.03, "tendon", n=5, m=3)


@modelo("guerra", "prop", (1, 1, 6), "Poste con los cráneos de los enemigos derrotados.")
def poste_trofeos(M):
    rnd = M.rnd
    p = M.pieza("poste", tris=560, res=200, k=0.05, ruido=(0.02, 2.5), suelo=0.0)
    p.tubo([(0, 0, 0), (0.04, 0.02, 2.5), (-0.03, 0, 4.6), (0, 0, 5.2)], [0.15, 0.11, 0.09, 0.05], "corteza")
    p.esfera((0, 0, 0), 0.32, "piedra", esc=(1, 1, 0.5))
    p.tubo([(-0.42, 0, 3.3), (0.42, 0.05, 3.4)], 0.05, "hueso_viejo", k=0.02)
    p.tubo([(0.05, -0.36, 1.9), (0, 0.36, 2.0)], 0.045, "hueso_viejo", k=0.02)
    d = p.duro
    d.cono((0, 0, 5.2), (0, 0, 6.0), 0.07, "hueso", n=5)
    for (x, y, z, L) in ((-0.42, 0, 3.3, 0.5), (0.42, 0.05, 3.4, 0.7), (0.05, -0.36, 1.9, 0.4)):  # tiras de piel y dientes colgando
        d.tubo([(x, y, z), (x, y, z - L)], 0.012, "tendon", n=3)
        d.cuerno([(x, y, z - L), (x + 0.03, y, z - L - 0.15), (x, y, z - L - 0.3)], 0.045, "diente", n=4, seg=2)
    cr = M.pieza("craneos", tris=1100, res=120, unir="poste")
    for (z, g, s, cu, x) in ((4.5, 0, 0.62, 2, 0.0), (3.55, 150, 0.5, 0, 0.05), (2.5, -70, 0.56, 3, -0.03), (1.3, 40, 0.46, 0, 0.02)):
        with cr.en((x, 0, z), rot=(rnd.uniform(-10, 10), rnd.uniform(-8, 8), g), esc=s):
            with cr.en((0, 0.15, 0)):
                craneo(cr, rnd, mat="hueso" if cu else "hueso_viejo", cuernos=cu, mandibula=cu != 3, largo=rnd.uniform(0.95, 1.3))


@modelo("guerra", "prop", (4, 2, 3), "Catapulta de tendones y hueso, con brazo de lanzamiento elástico.")
def catapulta_organica(M):
    p = M.pieza("bastidor", tris=900, res=170, k=0.05, ruido=(0.02, 2.0), suelo=0.0)
    for s in (-1, 1):
        p.tubo([(-1.9, s * 0.75, 0.25), (0, s * 0.8, 0.2), (1.9, s * 0.75, 0.32)], [0.16, 0.14, 0.16], "hueso_viejo")       # patines
        p.tubo([(-0.4, s * 0.78, 0.25), (0.1, s * 0.7, 1.5)], [0.13, 0.1], "hueso", k=0.03)                                 # montantes
        p.tubo([(0.9, s * 0.76, 0.28), (0.1, s * 0.7, 1.5)], [0.1, 0.09], "hueso", k=0.03)
        for x in (-1.5, 1.5):  # ruedas de vértebra
            p.cilindro((x, s * 0.82, 0.38), (x, s * 1.0, 0.38), 0.36, "hueso", red=0.05)
    p.tubo([(0.1, -0.8, 1.5), (0.1, 0.8, 1.5)], 0.1, "hueso", k=0.03)             # eje
    p.tubo([(-1.8, -0.78, 0.28), (-1.8, 0.78, 0.28)], 0.1, "hueso_viejo", k=0.03)
    p.tubo([(1.8, -0.78, 0.32), (1.8, 0.78, 0.32)], 0.1, "hueso_viejo", k=0.03)
    p.tubo([(0.1, -0.5, 1.5), (0.1, 0.5, 1.5)], 0.22, "tendon", k=0.02)            # madeja de torsión
    b = M.pieza("brazo", tris=650, res=150, k=0.05, ruido=(0.02, 2.0))
    b.tubo([(0.3, 0, 1.3), (-0.6, 0, 1.9), (-1.6, 0, 2.5)], [0.14, 0.11, 0.09], "hueso")
    b.esfera((0.3, 0, 1.3), 0.19, "hueso", k=0.03)
    b.torno([(0, -0.1), (0.3, -0.05), (0.42, 0.14), (0.34, 0.16), (0.24, 0.02), (0, -0.02)], (-1.75, 0, 2.56), "cuero", rot=(0, 28, 0))  # cuchara
    d = b.duro
    for i in range(5):  # dedos de costilla que cierran la cuchara
        a = math.tau * i / 5
        d.cuerno([(-1.75 + 0.36 * math.cos(a), 0.36 * math.sin(a), 2.62), (-1.8 + 0.46 * math.cos(a), 0.46 * math.sin(a), 2.85), (-1.85 + 0.3 * math.cos(a), 0.3 * math.sin(a), 3.0)],
                 0.045, "hueso", n=4, seg=3)
    for s in (-1, 1):  # tendones elásticos del brazo al bastidor
        p.duro.tubo([(-0.6, s * 0.08, 1.9), (0.8, s * 0.5, 1.0), (1.8, s * 0.7, 0.4)], [0.04, 0.03, 0.045], "tendon", n=4, suave=4)
    M.articulacion("brazo", "bastidor", (0.1, 0, 1.5))
    n = M.pieza("proyectil_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    n.duro.esfera((-1.82, 0, 2.82), 0.26, "acido", sub=2)
    M.articulacion("proyectil_neon", "brazo", (-1.82, 0, 2.82))
    M.notas["animacion"] = "El brazo gira sobre el eje (articulación «brazo»); el proyectil va soldado al brazo hasta que se lanza."
