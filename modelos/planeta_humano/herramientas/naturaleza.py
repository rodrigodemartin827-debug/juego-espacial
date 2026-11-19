"""Zona naturaleza (1): árboles del planeta humano, con su toque bioluminiscente."""

import math
import random

from mathutils import Matrix

from ph import NEON, V, Modelo, base_eje

ZONA = "naturaleza"


def _rama(c, a, b, r0, r1, mat, rnd, curva=0.25, n=7, surcos=4, prof=0.12):
    """Rama curvada de a a b (tubo con corteza), con un punto intermedio desviado."""
    a, b = V(a), V(b)
    d = b - a
    lado = d.cross(V((0, 0, 1)))
    if lado.length < 1e-4:
        lado = V((1, 0, 0))
    lado.normalize()
    m1 = a.lerp(b, 0.4) + lado * d.length * curva * rnd.uniform(-1, 1) + V((0, 0, d.length * 0.08))
    m2 = a.lerp(b, 0.75) + lado * d.length * curva * rnd.uniform(-0.6, 0.6)
    c.tubo([a, m1, m2, b], r0, mat, n=n, seg=2, r_fin=r1, surcos=surcos, prof=prof, semilla=rnd.randrange(999))
    return b


def _mata(c, p, r, mats, rnd, esc=(1, 1, 0.75), sub=1):
    """Masa de hojas: icosfera deformada (volumen real, sin planos con alfa)."""
    c.ico(p, r, mats[rnd.randrange(len(mats))], sub=sub, esc=esc, ruido=0.32, semilla=rnd.randrange(9999))


# ==============================================================================================================
def arbol_roble_espacial():
    m = Modelo("arbol_roble_espacial", ZONA, (6, 6, 14), 8000,
               "Roble espacial: tronco grueso con corteza agrietada modelada, raíces expuestas, 4 ramas principales que "
               "se bifurcan, copa de masas de hojas con puntas bioluminiscentes cyan y musgo en la cara norte (+Z de "
               "Roblox, la trasera del modelo).")
    c = m.parte()
    brillo = m.parte("puntas_neon", tipo="neon", color=NEON, transparencia=0.2, nota="Puntas de hojas luminosas.")
    rnd = random.Random(7)
    # el musgo va en la cara +Y (norte del modelo): manchas verdes en la corteza de ese lado
    corteza = m.mat("madera", "#5A4232", eje="Z", bump=1.0, patron="piedra", escala=1.6,
                    manchas=[(0.0, 1.0, 1.0, 1.6, "#4E6B2A", 0.9), (0.2, 0.9, 3.5, 1.2, "#5A7A30", 0.7)])
    hojas = [m.mat("organico", "#3E7A34", rug=0.6, bump=0.6), m.mat("organico", "#2F6430", rug=0.6, bump=0.6),
             m.mat("organico", "#4E8C3A", rug=0.6, bump=0.6), m.mat("organico", "#3A7A5C", rug=0.6, bump=0.6)]
    tierra = m.mat("piedra", "#4E3E2E", bump=0.6, escala=1.5)

    m.seccion("tronco y raíces")
    c.cil((0, 0, -0.05), (0, 0, 0.05), 1.5, tierra, n=14, r1=1.2)  # montículo de tierra
    c.tubo([(0, 0, 0.0), (0.05, 0.02, 1.5), (0.15, 0.05, 3.5), (0.25, 0.1, 5.4)], 0.95, corteza, n=16, seg=3,
           r_fin=0.55, surcos=7, prof=0.16, semilla=3)
    for k in range(6):
        a = k * math.tau / 6 + rnd.uniform(-0.3, 0.3)
        L = rnd.uniform(1.3, 1.8)
        pts = [(math.cos(a) * 0.55, math.sin(a) * 0.55, 0.9), (math.cos(a) * 1.0, math.sin(a) * 1.0, 0.35),
               (math.cos(a) * L, math.sin(a) * L, 0.02), (math.cos(a) * (L + 0.5), math.sin(a) * (L + 0.5), -0.1)]
        c.tubo(pts, 0.32, corteza, n=8, seg=2, r_fin=0.06, surcos=3, prof=0.15, semilla=k)

    m.seccion("ramas")
    puntas = []
    base = V((0.25, 0.1, 5.2))
    for k in range(4):
        a = k * math.tau / 4 + 0.4 + rnd.uniform(-0.2, 0.2)
        fin = base + V((math.cos(a) * 1.5, math.sin(a) * 1.5, rnd.uniform(2.2, 3.0)))
        _rama(c, base + V((0, 0, rnd.uniform(-0.3, 0.6))), fin, 0.42, 0.2, corteza, rnd)
        for j in (-1, 1):
            b = a + j * rnd.uniform(0.35, 0.6)
            f2 = fin + V((math.cos(b) * rnd.uniform(0.5, 0.8), math.sin(b) * rnd.uniform(0.5, 0.8), rnd.uniform(1.0, 1.8)))
            _rama(c, fin, f2, 0.2, 0.07, corteza, rnd, curva=0.15, n=6, surcos=3, prof=0.1)
            puntas.append(f2)
        puntas.append(fin)
    # guía central
    top = _rama(c, base, base + V((0.0, -0.1, 3.8)), 0.4, 0.12, corteza, rnd, curva=0.1)
    puntas.append(top)

    m.seccion("copa")
    # masas de hojas: grandes y redondeadas (icosfera de 2 subdivisiones) formando la corona, y otras más pequeñas
    # alrededor de las puntas de las ramas para romper la silueta
    for i in range(13):
        a = i * 2.4 + rnd.uniform(-0.3, 0.3)
        t = (i + 0.5) / 13
        rr = 2.0 * math.sqrt(max(0.05, 1 - (2 * t - 1) ** 2))
        q = V((0.2 + math.cos(a) * rr, 0.1 + math.sin(a) * rr, 7.6 + t * 4.6))
        c.ico(q, rnd.uniform(1.3, 1.6), hojas[i % 4], sub=3, esc=(1, 1, 0.8), ruido=0.12, semilla=i)
    for p in puntas:
        q = V(p) + V((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), 0.3))
        _mata(c, q, rnd.uniform(0.7, 0.95), hojas, rnd, sub=2)
    # puntas luminosas en la superficie de la copa
    for i in range(18):
        a = rnd.uniform(0, math.tau)
        t = rnd.uniform(0.15, 0.95)
        rr = 2.85 * math.sqrt(1 - (2 * t - 1) ** 2) + 0.1
        q = V((0.2 + math.cos(a) * rr, 0.1 + math.sin(a) * rr, 7.0 + t * 6.2))
        brillo.ico(q, rnd.uniform(0.12, 0.2), None, sub=0, ruido=0.3, semilla=i, esc=(1, 1, 0.6))
    m.terminar()


# ==============================================================================================================
def arbol_pino_espacial():
    m = Modelo("arbol_pino_espacial", ZONA, (3, 3, 16), 6000,
               "Pino espacial: tronco recto de corteza escamosa, 8 niveles de ramas en espiral (más largas abajo, "
               "silueta cónica), 4 piñas 3D colgando y escarcha alienígena de cristales cyan en las puntas.")
    c = m.parte()
    escarcha = m.parte("escarcha_neon", tipo="neon", color=NEON, transparencia=0.25, nota="Cristales de escarcha.")
    rnd = random.Random(11)
    corteza = m.mat("madera", "#5E4432", eje="Z", bump=1.0, patron="piedra", escala=3.0)
    agujas = [m.mat("organico", "#24503A", rug=0.7, bump=0.8), m.mat("organico", "#2C5E40", rug=0.7, bump=0.8),
              m.mat("organico", "#1E4434", rug=0.7, bump=0.8)]
    pina = m.mat("madera", "#7A5434", eje="Z", bump=0.8)
    tierra = m.mat("piedra", "#4E3E2E", bump=0.6, escala=1.5)

    m.seccion("tronco")
    c.cil((0, 0, -0.05), (0, 0, 0.05), 1.0, tierra, n=12, r1=0.8)
    c.tubo([(0, 0, 0.0), (0.03, 0.0, 5.0), (0.0, 0.04, 10.0), (0.02, 0.0, 15.6)], 0.38, corteza, n=12, seg=3,
           r_fin=0.05, surcos=9, prof=0.14, semilla=5)
    for k in range(4):  # contrafuertes de raíz
        a = k * math.pi / 2 + 0.4
        c.tubo([(math.cos(a) * 0.2, math.sin(a) * 0.2, 0.6), (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.1),
                (math.cos(a) * 0.8, math.sin(a) * 0.8, -0.05)], 0.16, corteza, n=6, seg=2, r_fin=0.04)

    m.seccion("ramas en espiral")
    niveles = 9
    for i in range(niveles):
        z = 2.7 + i * 1.36
        L = 1.25 * (1 - i / niveles) + 0.35
        nr = 6
        for k in range(nr):
            a = k * math.tau / nr + i * 0.52
            d = V((math.cos(a), math.sin(a), -0.5)).normalized()
            centro = V((0, 0, z)) + d * (L / 2 + 0.05)
            # rama: masa de agujas alargada, ancha y caída hacia fuera; las de un nivel tapan el arranque del de abajo
            m_rot = base_eje(d) @ Matrix.Rotation(math.pi / 2, 3, "Y")
            with c.en(centro, m_rot):
                f = 1.0 - 0.5 * i / niveles  # más finas arriba: silueta cónica
                c.ico((0, 0, 0), 1.0, agujas[(i + k) % 3], sub=2, esc=(0.42 * f, 0.6 * f, L / 2 + 0.25), ruido=0.2,
                      semilla=i * 10 + k)
            if i < 4:  # arranque leñoso visible solo en las ramas bajas
                c.cil(V((0, 0, z + 0.1)), V((0, 0, z)) + d * (L * 0.7), 0.04, corteza, n=4)
            if (i + k) % 2 == 0:
                tip = V((0, 0, z)) + d * (L + 0.2)
                escarcha.cil(tip, tip + V((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.16)), 0.035, None, n=3, r1=0.0)
    c.ico((0.02, 0.0, 15.3), 0.45, agujas[0], sub=1, esc=(0.6, 0.6, 1.4), ruido=0.2, semilla=3)  # copa

    m.seccion("piñas")
    for k, (a, z) in enumerate(((0.6, 4.6), (2.4, 6.0), (4.1, 3.9), (5.5, 7.3))):
        p = V((math.cos(a) * 0.9, math.sin(a) * 0.9, z - 0.55))
        c.cil(p + V((0, 0, 0.32)), p + V((0, 0, 0.18)), 0.02, corteza, n=4)
        c.torno([(0.0, -0.22), (0.07, -0.18), (0.11, -0.06), (0.12, 0.04), (0.09, 0.14), (0.0, 0.19)], pina, n=7, c=p)
        for j in range(2):  # escamas en anillos
            c.toro(p + V((0, 0, -0.08 + j * 0.12)), 0.11, 0.025, pina, n=7, m=3)
    m.terminar()


# ==============================================================================================================
def arbol_sauce_espacial():
    m = Modelo("arbol_sauce_espacial", ZONA, (5, 5, 10), 8000,
               "Sauce llorón espacial: tronco curvado con surcos verticales, ramas en arco de las que cuelgan "
               "cortinas de hojas alargadas casi hasta el suelo, bordes con bioluminiscencia cyan tenue y raíces "
               "aéreas.")
    c = m.parte()
    brillo = m.parte("bordes_neon", tipo="neon", color=NEON, transparencia=0.55,
                     nota="Bioluminiscencia tenue: Neon cyan con Transparency 0,55.")
    rnd = random.Random(23)
    corteza = m.mat("madera", "#4E3E30", eje="Z", bump=1.0)
    hojas = [m.mat("organico", "#5E8A3A", rug=0.65, bump=0.5), m.mat("organico", "#4E7A34", rug=0.65, bump=0.5),
             m.mat("organico", "#6E9A44", rug=0.65, bump=0.5)]
    tierra = m.mat("piedra", "#4A3C2E", bump=0.6, escala=1.5)

    m.seccion("tronco y raíces aéreas")
    c.cil((0, 0, -0.05), (0, 0, 0.05), 1.6, tierra, n=12, r1=1.3)
    c.tubo([(0, 0, 0.0), (0.3, 0.1, 1.8), (0.1, 0.25, 3.7), (-0.3, 0.2, 5.4)], 0.62, corteza, n=14, seg=3, r_fin=0.38,
           surcos=6, prof=0.22, semilla=2)
    for k in range(5):
        a = k * math.tau / 5 + 0.2
        c.tubo([(math.cos(a) * 0.3, math.sin(a) * 0.3, 0.7), (math.cos(a) * 0.75, math.sin(a) * 0.75, 0.2),
                (math.cos(a) * 1.15, math.sin(a) * 1.15, -0.05)], 0.22, corteza, n=6, seg=2, r_fin=0.05)
    m.seccion("ramas en arco")
    arcos = []
    base = V((-0.3, 0.2, 5.2))
    for k in range(6):
        a = k * math.tau / 6 + rnd.uniform(-0.25, 0.25)
        d = V((math.cos(a), math.sin(a), 0))
        p1 = base + d * 0.8 + V((0, 0, 1.7))
        p2 = base + d * 1.6 + V((0, 0, 2.6))
        p3 = base + d * 2.25 + V((0, 0, 2.15))
        c.tubo([base + V((0, 0, rnd.uniform(-0.4, 0.4))), p1, p2, p3], 0.24, corteza, n=6, seg=3, r_fin=0.06,
               surcos=3, prof=0.12, semilla=k)
        arcos.append((p1, p2, p3, d))
    # copa: masas de hojas sobre los arcos
    for (p1, p2, p3, d) in arcos:
        for q in (p1, p2):
            c.ico(q + V((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0.25)), rnd.uniform(0.75, 0.95),
                  hojas[rnd.randrange(3)], sub=2, esc=(1.1, 1.1, 0.55), ruido=0.15, semilla=rnd.randrange(999))
    c.ico(base + V((0, 0, 2.6)), 1.1, hojas[0], sub=2, esc=(1.2, 1.2, 0.55), ruido=0.15, semilla=4)

    m.seccion("cortinas colgantes")
    # tiras de hojas con grosor que cuelgan de los arcos (cada una es una lámina ondulada estrecha)
    for (p1, p2, p3, d) in arcos:
        lado = V((-d.y, d.x, 0))
        for j in range(12):
            t = j / 11
            q = p1.lerp(p2, t * 1.6) if t < 0.62 else p2.lerp(p3, (t - 0.62) / 0.38)
            q = q + lado * rnd.uniform(-0.45, 0.45) + d * rnd.uniform(0.0, 0.3)
            largo = rnd.uniform(q.z * 0.55, q.z - 0.3)
            ancho = rnd.uniform(0.1, 0.16)
            fase = rnd.uniform(0, 6)
            mat = hojas[rnd.randrange(3)]
            c.lamina(lambda u, v, q=q, largo=largo, ancho=ancho, fase=fase:
                     (q.x + lado.x * (u - 0.5) * ancho * (1 - 0.7 * v) + d.x * 0.06 * math.sin(v * 7 + fase),
                      q.y + lado.y * (u - 0.5) * ancho * (1 - 0.7 * v) + d.y * 0.06 * math.sin(v * 7 + fase),
                      q.z - v * largo), 1, 6, 0.035, mat)
            if j % 3 == 0:  # borde luminoso al final de la tira
                fz = q.z - largo
                brillo.lamina(lambda u, v, q=q, fz=fz, ancho=ancho:
                              (q.x + lado.x * (u - 0.5) * ancho * 0.32, q.y + lado.y * (u - 0.5) * ancho * 0.32,
                               fz + 0.32 - v * 0.3), 1, 1, 0.045, None)
    m.terminar()


MODELOS = {
    "arbol_roble_espacial": arbol_roble_espacial,
    "arbol_pino_espacial": arbol_pino_espacial,
    "arbol_sauce_espacial": arbol_sauce_espacial,
}
