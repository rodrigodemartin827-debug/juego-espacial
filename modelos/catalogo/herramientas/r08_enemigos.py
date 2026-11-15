"""Ronda 8: enemigos (modelos 45-50). Rig de piezas rígidas (estilo R6): cada pieza tiene su articulación (pivote) y su
padre; `montar_<nombre>.luau` crea los Motor6D en Studio. El frente mira a -Y. Ojos y brillos van en el atlas."""

import math
import random

from comunes import colmillo, cristales
from lib import anillo_y


def _rig(g, raiz, especie, humanoide=False, articulaciones=None):
    g.extra["rig"] = {"raiz": raiz, "especie": especie, "humanoide": humanoide, "articulaciones": articulaciones or {}}


def _pata(g, mat, base, lado, avance, largo, alto, r, garra=None, lados=5):
    """Pata de artrópodo: sube desde el cuerpo, se dobla y baja hasta el suelo."""
    x, y, z = base
    rod = (x + lado * largo * 0.55, y + avance * 0.5, z + alto)
    pie = (x + lado * largo, y + avance, 0.0)
    g.tubo(mat, [base, ((x + rod[0]) / 2, (y + rod[1]) / 2, z + alto * 0.75), rod], [r, r * 0.9, r * 0.75], lados=lados)
    g.esfera(mat, r * 1.05, rod, lados=6, anillos=4)
    g.tubo(garra or mat, [rod, ((rod[0] + pie[0]) / 2 + lado * largo * 0.08, (rod[1] + pie[1]) / 2, rod[2] * 0.5), pie],
           [r * 0.75, r * 0.55, 0.0], lados=lados)


def escarabajo_gigante(g):
    g.separar = False
    # Cuerpo: abdomen con élitros, tórax y cabeza con cuerno. Largo ≈ 8 studs.
    g.pieza("cuerpo")
    g.esfera("q_caparazon", 2.2, (0, 1.0, 2.5), esc=(1.0, 1.45, 0.8), lados=12, anillos=7)
    g.esfera("q_quitina", 2.0, (0, 0.8, 2.0), esc=(0.95, 1.4, 0.6), lados=10, anillos=5)
    g.prisma("q_quitina", [(-0.07, 2.6), (0.07, 2.6), (0.07, 4.25), (-0.07, 4.25)], 6.0, (0, 1.2, 0), (0, 0, 0), plano="xz") if False else None
    g.caja("q_quitina", (0.12, 5.6, 0.3), (0, 1.3, 4.05), rot=(-4, 0, 0))
    for s in (-1, 1):
        g.prisma("q_caparazon_raya", [(0.5, -1.2), (1.3, -0.9), (1.5, 1.6), (0.9, 3.2), (0.5, 3.0)], 0.1, (0, 0.6, 3.82), (0, s * 24, 0),
                 plano="xy", esc=(s, 1, 1))
    g.esfera("q_caparazon", 1.7, (0, -2.2, 2.3), esc=(1.05, 0.9, 0.8), lados=10, anillos=6)
    g.toro("q_quitina", 1.5, 0.2, (0, -1.35, 2.3), (90, 0, 0), seg=10, lados=4, esc=(1.05, 0.78, 1))
    g.pieza("cabeza", pivote=(0, -3.3, 2.0), padre="cuerpo")
    g.esfera("q_quitina", 1.05, (0, -3.9, 1.9), esc=(1.1, 1.0, 0.75), lados=10, anillos=6)
    g.tubo("q_caparazon_raya", [(0, -4.3, 2.4), (0, -5.3, 3.3), (0, -5.6, 4.6)], [0.42, 0.3, 0.14], lados=6)
    for s in (-1, 1):
        g.tubo("q_caparazon_raya", [(0, -5.6, 4.6), (s * 0.45, -5.9, 5.2)], [0.14, 0.0], lados=5)
        g.esfera("ojo_naranja", 0.24, (s * 0.72, -4.55, 2.15), lados=7, anillos=4)
        g.tubo("q_quitina", [(s * 0.4, -4.6, 2.5), (s * 1.0, -5.4, 3.2), (s * 1.6, -5.5, 3.0)], [0.07, 0.05, 0.03], lados=4)
    for s, nom in ((-1, "mandibula_izq"), (1, "mandibula_der")):
        g.pieza(nom, pivote=(s * 0.55, -4.6, 1.6), padre="cabeza")
        g.tubo("q_quitina", [(s * 0.55, -4.6, 1.6), (s * 1.05, -5.5, 1.5), (s * 0.7, -6.4, 1.45), (s * 0.15, -6.7, 1.45)],
               [0.3, 0.26, 0.18, 0.0], lados=6)
        g.cil("q_quitina", 0.1, 0.4, (s * 0.85, -5.9, 1.48), (0, -s * 90, 0), lados=4, r2=0.0)
    for i, (py, av) in enumerate(((-2.4, -1.3), (-0.3, 0.0), (1.8, 1.5))):
        for s, lado in ((-1, "izq"), (1, "der")):
            g.pieza(f"pata{i + 1}_{lado}", pivote=(s * 1.3, py, 1.7), padre="cuerpo")
            _pata(g, "q_quitina", (s * 1.3, py, 1.7), s, av, 3.0, 1.6, 0.26)
    _rig(g, "cuerpo", "Criatura_EscarabajoGigante")


def jabali_roca(g):
    g.separar = False
    rnd = random.Random(46)
    g.pieza("cuerpo")
    # Tronco de barril con lomo alto, y placas de piedra a lo largo del espinazo.
    g.loft("q_pelo", [[(0, 3.1, 2.6)]] + [anillo_y(y, rx, rz, 10, pot=2.4, cz=cz) for y, rx, rz, cz in
                                          ((2.7, 1.2, 1.3, 2.6), (1.4, 1.75, 1.75, 2.7), (-0.4, 1.9, 2.0, 2.95), (-1.9, 1.7, 1.8, 2.9),
                                           (-2.9, 1.25, 1.35, 2.7))] + [[(0, -3.3, 2.6)]])
    for i, (py, pz, r) in enumerate(((1.9, 4.2, 0.7), (0.7, 4.6, 0.95), (-0.6, 4.95, 1.1), (-1.8, 4.7, 0.95), (-2.7, 4.15, 0.65))):
        g.roca("piedra_musgo", r, (0, py, pz), esc=(1.3, 0.9, 0.8), rot=(rnd.uniform(-10, 10), 0, i * 30), semilla=i + 3, sub=1, amp=0.3)
        for s in (-1, 1):
            g.roca("piedra", r * 0.6, (s * 1.0, py + 0.2, pz - 0.55), esc=(1.0, 1.0, 0.7), rot=(0, s * 30, i * 50), semilla=i + 20, sub=1,
                   amp=0.3)
    g.tubo("q_pelo_osc", [(0, 2.9, 3.0), (0, 3.5, 3.3), (0, 3.9, 2.9)], [0.2, 0.13, 0.05], lados=5)
    g.esfera("q_pelo_osc", 0.24, (0, 3.95, 2.8), lados=5, anillos=3)
    g.pieza("cabeza", pivote=(0, -2.9, 2.7), padre="cuerpo")
    g.loft("q_pelo", [anillo_y(y, rx, rz, 9, pot=2.3, cz=cz) for y, rx, rz, cz in
                      ((-2.7, 1.25, 1.3, 2.65), (-3.6, 1.15, 1.15, 2.45), (-4.6, 0.75, 0.75, 2.1), (-5.3, 0.55, 0.5, 1.95))])
    g.cil("q_hocico", 0.52, 0.25, (0, -5.25, 1.95), (90, 0, 0), lados=8, esc=(1.05, 0.9, 1))
    for s in (-1, 1):
        g.esfera("ojo_negro", 0.11, (s * 0.2, -5.52, 1.98), lados=5, anillos=3)
        g.esfera("ojo_naranja", 0.16, (s * 0.78, -4.15, 2.75), lados=6, anillos=4)
        g.tubo("m_hueso", [(s * 0.5, -4.9, 1.75), (s * 1.0, -5.3, 1.8), (s * 1.15, -5.5, 2.5)], [0.2, 0.16, 0.0], lados=6)
        g.prisma("q_pelo_osc", [(-0.3, 0), (0.3, 0), (0.05, 0.85)], 0.12, (s * 0.85, -3.3, 3.45), (-10, s * 25, s * 20), plano="xz")
        g.roca("piedra", 0.42, (s * 0.45, -3.9, 3.35), esc=(1, 1.2, 0.6), semilla=40 + s, sub=1, amp=0.3)
    g.pieza("cola", pivote=(0, 3.2, 3.0), padre="cuerpo")
    g.tubo("q_pelo_osc", [(0, 3.2, 3.0), (0, 3.8, 3.4)], [0.16, 0.12], lados=5)
    for nom, sx, py in (("pata_del_izq", -1, -1.9), ("pata_del_der", 1, -1.9), ("pata_tras_izq", -1, 2.0), ("pata_tras_der", 1, 2.0)):
        g.pieza(nom, pivote=(sx * 1.0, py, 1.9), padre="cuerpo")
        g.tubo("q_pelo", [(sx * 1.0, py, 2.1), (sx * 1.1, py + 0.15, 1.1), (sx * 1.1, py - 0.05, 0.35)], [0.6, 0.42, 0.32], lados=7)
        g.cil("q_quitina", 0.36, 0.4, (sx * 1.1, py - 0.05, 0.0), lados=7, r2=0.32)
    _rig(g, "cuerpo", "Criatura_JabaliRoca")


def golem_musgo(g):
    g.separar = False
    # Minijefe: ≈15 studs de alto. Torso de roca con musgo arriba, brazos enormes y cristales en la espalda.
    g.pieza("torso", pivote=(0, 0, 8.6))
    g.roca("piedra_musgo", 3.6, (0, 0, 9.2), esc=(1.3, 0.95, 1.0), semilla=3, sub=2, amp=0.25, frec=1.0)
    g.roca("piedra", 2.5, (0, 0.1, 6.2), esc=(1.15, 0.9, 0.9), semilla=5, sub=2, amp=0.25)
    g.roca("piedra_musgo", 1.7, (-3.2, 0.2, 11.2), esc=(1.2, 1, 0.8), semilla=7, sub=1, amp=0.3)
    g.roca("piedra_musgo", 1.7, (3.2, 0.2, 11.2), esc=(1.2, 1, 0.8), semilla=8, sub=1, amp=0.3)
    cristales(g, "cris_azul", (-1.2, 2.2, 10.6), n=4, r=0.6, h=3.4, semilla=2, abrir=30)
    cristales(g, "cris_azul", (1.6, 2.4, 9.2), n=3, r=0.45, h=2.4, semilla=3, abrir=35)
    g.esfera("ojo_cian", 0.7, (0, -3.2, 9.0), esc=(1, 0.35, 1), lados=8, anillos=5)
    for i in range(6):
        a = 2 * math.pi * i / 6
        g.caja("ojo_cian", (0.5, 0.12, 0.14), (1.25 * math.cos(a), -3.25, 9.0 + 1.25 * math.sin(a)), rot=(0, -math.degrees(a), 0))
    g.pieza("cabeza", pivote=(0, -0.6, 12.4), padre="torso")
    g.roca("piedra_musgo", 1.6, (0, -0.9, 13.4), esc=(1.1, 1.0, 0.95), semilla=11, sub=2, amp=0.22)
    g.caja("piedra", (1.9, 0.9, 0.5), (0, -1.9, 12.6), bisel=0.1)
    for s in (-1, 1):
        g.caja("ojo_cian", (0.5, 0.2, 0.22), (s * 0.6, -2.38, 13.5), rot=(0, s * 12, 0))
    g.roca("hoja", 0.9, (0.2, -0.6, 14.8), esc=(1.4, 1.2, 0.4), semilla=13, sub=1, amp=0.3)
    for s, lado in ((-1, "izq"), (1, "der")):
        g.pieza(f"brazo_{lado}", pivote=(s * 4.3, 0, 10.6), padre="torso")
        g.roca("piedra_musgo", 1.9, (s * 5.0, 0, 10.4), esc=(1.0, 1.0, 1.1), semilla=20 + s, sub=2, amp=0.28)
        g.roca("piedra", 1.45, (s * 5.5, -0.2, 7.6), esc=(0.9, 0.9, 1.4), semilla=24 + s, sub=1, amp=0.25)
        g.pieza(f"antebrazo_{lado}", pivote=(s * 5.6, -0.3, 6.0), padre=f"brazo_{lado}")
        g.roca("piedra", 1.9, (s * 5.8, -0.6, 4.2), esc=(1.0, 1.0, 1.35), semilla=28 + s, sub=2, amp=0.28)
        g.roca("piedra_musgo", 2.2, (s * 5.9, -0.9, 1.9), esc=(1.05, 1.1, 0.85), semilla=32 + s, sub=2, amp=0.25)
        for k in range(3):
            g.roca("piedra", 0.75, (s * 5.9 + (k - 1) * 1.2, -2.6, 1.0), esc=(0.8, 1.2, 1.0), semilla=40 + k + s, sub=1, amp=0.25)
        cristales(g, "cris_azul", (s * 6.3, 0.6, 5.2), n=2, r=0.35, h=1.7, semilla=6 + s, abrir=40)
        g.pieza(f"pierna_{lado}", pivote=(s * 1.6, 0, 5.2), padre="torso")
        g.roca("piedra", 1.6, (s * 1.8, 0, 3.6), esc=(1.0, 1.0, 1.25), semilla=50 + s, sub=1, amp=0.25)
        g.roca("piedra_musgo", 1.9, (s * 1.9, -0.3, 1.25), esc=(1.0, 1.3, 0.72), semilla=54 + s, sub=2, amp=0.25, plano=-1.7)
    _rig(g, "torso", "Criatura_GolemMusgo")


def arana_cristal(g):
    g.separar = False
    g.pieza("cuerpo")
    # Cefalotórax y abdomen oscuros con púas de cristal.
    g.esfera("m_carne", 1.5, (0, -0.6, 2.6), esc=(1.0, 1.15, 0.7), lados=10, anillos=6)
    g.esfera("q_escama", 2.3, (0, 2.7, 3.2), esc=(1.0, 1.25, 0.9), lados=12, anillos=7)
    cristales(g, "cris_purpura", (0, 2.9, 4.9), n=6, r=0.55, h=3.0, semilla=3, abrir=38, radio=0.9)
    for i in range(5):
        a = math.radians(40 + i * 25)
        g.cristal("cris_purpura", 0.26, 1.3, (1.9 * math.cos(a) * (1 if i % 2 else -1), 2.7 + 1.6 * math.sin(a) * 0.5, 4.4),
                  (0, (25 if i % 2 else -25), 0), lados=5)
    g.cristal("cris_purpura", 0.45, 2.0, (0, 5.3, 3.2), (-70, 0, 0), lados=5)
    # Ojos (ocho, magenta) y quelíceros.
    for i, (px, pz, r) in enumerate(((0.3, 3.05, 0.2), (0.75, 2.95, 0.16), (0.28, 2.65, 0.13), (1.05, 2.7, 0.12))):
        for s in (-1, 1):
            g.esfera("ojo_violeta", r, (s * px, -2.15 + abs(px) * 0.35, pz), lados=6, anillos=4)
    for s, lado in ((-1, "izq"), (1, "der")):
        g.pieza(f"colmillo_{lado}", pivote=(s * 0.4, -2.1, 2.2), padre="cuerpo")
        g.tubo("m_carne", [(s * 0.4, -2.0, 2.3), (s * 0.5, -2.6, 2.0)], [0.3, 0.24], lados=6)
        g.cristal("cris_purpura", 0.2, 1.3, (s * 0.5, -2.6, 2.05), (160, s * 8, 0), lados=5, punta=0.7)
    # Ocho patas de cristal: fémur hacia arriba y tibia afilada hasta el suelo.
    for i, (py, av, L) in enumerate(((-1.4, -3.0, 4.4), (-0.7, -1.0, 4.9), (0.0, 1.2, 4.9), (0.6, 3.2, 4.6))):
        for s, lado in ((-1, "izq"), (1, "der")):
            g.pieza(f"pata{i + 1}_{lado}", pivote=(s * 1.2, py, 2.6), padre="cuerpo")
            base = (s * 1.2, py, 2.6)
            rod = (s * (1.2 + L * 0.5), py + av * 0.45, 5.4)
            pie = (s * (1.2 + L), py + av, 0.0)
            g.tubo("m_carne", [base, ((base[0] + rod[0]) / 2, (base[1] + rod[1]) / 2, 4.6), rod], [0.32, 0.26, 0.2], lados=5)
            g.esfera("q_escama", 0.36, rod, lados=6, anillos=4)
            d = [pie[k] - rod[k] for k in range(3)]
            largo = math.sqrt(sum(v * v for v in d))
            rx = math.degrees(math.atan2(math.hypot(d[0], d[1]), d[2]))
            rz = math.degrees(math.atan2(d[1], d[0])) - 90
            with g.grupo(rod, (0, 0, rz)):
                with g.grupo((0, 0, 0), (-rx, 0, 0)):
                    g.cristal("cris_purpura", 0.3, largo, (0, 0, 0), lados=5, punta=0.55, base=0.6)
    _rig(g, "cuerpo", "Criatura_AranaCristal")


def serpiente_sombra(g):
    g.separar = False
    # Serpiente larga en S con el cuello erguido. Cada tramo es una pieza encadenada a la anterior.
    camino = []
    n = 28
    for i in range(n + 1):
        t = i / n
        x = 3.2 * math.sin(t * 2.2 * math.pi) * (1 - 0.3 * t)
        y = 8.0 - 15.5 * t
        z = 0.75
        if t > 0.72:
            k = (t - 0.72) / 0.28
            z = 0.75 + 5.6 * math.sin(k * math.pi * 0.5) ** 1.5
            y = 8.0 - 15.5 * 0.72 - 1.6 * math.sin(k * math.pi) - 1.2 * k
            x = 3.2 * math.sin(0.72 * 2.2 * math.pi) * (1 - 0.3 * 0.72) * (1 - k)
        camino.append((x, y, z))

    def radio(t):
        if t < 0.25:
            return 0.15 + 0.85 * (t / 0.25)
        return 1.0 + 0.15 * math.sin((t - 0.25) / 0.75 * math.pi)

    tramos = ((0, 5, "cola2"), (5, 10, "cola1"), (10, 15, "cuerpo"), (15, 20, "cuello1"), (20, 24, "cuello2"), (24, 28, "cuello3"))
    padres = {"cola2": "cola1", "cola1": "cuerpo", "cuello1": "cuerpo", "cuello2": "cuello1", "cuello3": "cuello2"}
    pivotes = {"cola2": 5, "cola1": 10, "cuello1": 15, "cuello2": 20, "cuello3": 24}
    for a, b, nom in tramos:
        if nom == "cuerpo":
            g.pieza("cuerpo")
        else:
            g.pieza(nom, pivote=camino[pivotes[nom]], padre=padres[nom])
        pts = camino[a:b + 1]
        rs = [radio(i / n) for i in range(a, b + 1)]
        if a == 0:
            rs[0] = 0.0
        g.tubo("q_escama", pts, rs, lados=8)
        # Cresta dorsal de espinas y manchas luminosas en los costados.
        for i in range(a + 1, b, 2):
            p = camino[i]
            g.cil("m_cristal_osc", 0.16, 0.7, (p[0], p[1], p[2] + radio(i / n) * 0.8), lados=4, r2=0.0)
            for s in (-1, 1):
                g.esfera("ojo_violeta", 0.11, (p[0] + s * radio(i / n) * 0.93, p[1], p[2] + 0.1), lados=5, anillos=3)
    # Cabeza de cobra con capucha, ojos violeta, colmillos y lengua.
    c = camino[-1]
    g.pieza("cabeza", pivote=c, padre="cuello3")
    g.loft("q_escama", [[(c[0], c[1] + 0.5, c[2] - 0.1)]] + [anillo_y(c[1] - dy, rx, rz, 8, pot=2.2, cz=c[2] + dz, cx=c[0]) for dy, rx, rz, dz in
                                                           ((0.0, 1.05, 0.8, 0.1), (0.9, 1.3, 0.8, 0.05), (1.9, 1.0, 0.55, -0.1), (2.6, 0.5, 0.3, -0.2))] +
           [[(c[0], c[1] - 2.9, c[2] - 0.25)]])
    for s in (-1, 1):
        g.esfera("ojo_violeta", 0.3, (c[0] + s * 0.92, c[1] - 1.5, c[2] + 0.35), esc=(0.6, 1.3, 1), lados=6, anillos=4)
        g.tubo("m_cristal_osc", [(c[0] + s * 0.5, c[1] - 0.2, c[2] + 0.55), (c[0] + s * 0.8, c[1] + 0.7, c[2] + 1.1)], [0.18, 0.0], lados=5)
        colmillo(g, "m_hueso", (c[0] + s * 0.32, c[1] - 2.3, c[2] - 0.35), 0.6, 0.1, rot=(170, 0, 0), curvo=0.1)
        # Capucha (con grosor) a los lados del cuello.
        g.prisma("q_vientre", [(0.0, -2.2), (2.0, -0.8), (2.3, 0.8), (1.2, 1.9), (0.0, 1.5)], 0.22, (c[0] + s * 0.6, c[1] + 0.55, c[2] - 0.4),
                 (20, 0, 0), plano="xz", esc=(s, 1, 1))
    g.pieza("mandibula", pivote=(c[0], c[1] - 0.6, c[2] - 0.3), padre="cabeza")
    g.loft("q_vientre", [anillo_y(c[1] - dy, rx, 0.16, 6, cz=c[2] - 0.45 - dy * 0.14, cx=c[0]) for dy, rx in ((0.5, 0.7), (1.6, 0.65), (2.5, 0.3))])
    g.tubo("ojo_violeta", [(c[0], c[1] - 2.4, c[2] - 0.75), (c[0], c[1] - 3.2, c[2] - 0.9), (c[0] + 0.2, c[1] - 3.6, c[2] - 0.8)],
           [0.06, 0.05, 0.0], lados=4)
    _rig(g, "cuerpo", "Criatura_SerpienteSombra")


def guardian_oscuro(g):
    g.separar = False
    g.nombres_exactos = True
    E = 2.4                      # escala respecto a un R6 estándar: ≈13 studs de alto
    ZT = 3.0 * E                 # centro del torso
    # --- Torso: caja torácica de hueso sobre carne oscura.
    g.pieza("Torso", pivote=(0, 0, ZT))
    g.caja("m_carne", (1.9 * E, 0.9 * E, 2.0 * E), (0, 0, ZT), sup=(1.15, 1.1), bisel=0.2)
    for i in range(4):
        z = ZT - 0.5 * E + i * 0.42 * E
        w = (0.95 + i * 0.08) * E
        for s in (-1, 1):
            g.tubo("m_hueso", [(s * 0.12 * E, -0.5 * E, z), (s * w * 0.6, -0.62 * E, z + 0.12 * E), (s * w, -0.2 * E, z + 0.05 * E),
                               (s * w * 0.95, 0.35 * E, z - 0.1 * E)], [0.2, 0.2, 0.17, 0.08], lados=5)
    g.caja("m_hueso", (0.3 * E, 0.16 * E, 1.7 * E), (0, -0.55 * E, ZT + 0.15 * E), bisel=0.08)
    g.cristal("m_cristal", 0.3 * E, 0.6 * E, (0, -0.62 * E, ZT + 0.5 * E), (90, 0, 0), lados=6, punta=0.6, base=0.9)
    for i in range(5):
        g.cil("m_hueso", 0.2 * E, 0.5 * E, (0, 0.5 * E, ZT - 0.7 * E + i * 0.4 * E), (-55, 0, 0), lados=5, r2=0.0)
    g.caja("m_hueso", (2.0 * E, 1.0 * E, 0.28 * E), (0, 0, ZT - 0.92 * E), bisel=0.1)
    g.prisma("m_tela", [(-0.5 * E, 0), (0.5 * E, 0), (0.35 * E, -1.3 * E), (0, -1.6 * E), (-0.35 * E, -1.3 * E)], 0.12, (0, -0.52 * E, ZT - E),
             plano="xz")
    # --- Cabeza: cráneo con cuernos y ojos violeta.
    g.pieza("Head", pivote=(0, 0, ZT + 1.0 * E), padre="Torso")
    ZH = ZT + 1.55 * E
    g.esfera("m_hueso", 0.62 * E, (0, -0.05 * E, ZH), esc=(0.95, 1.1, 1.05), lados=10, anillos=6)
    g.caja("m_hueso", (0.7 * E, 0.6 * E, 0.5 * E), (0, -0.42 * E, ZH - 0.48 * E), sup=(1.25, 1.2), bisel=0.1)
    for s in (-1, 1):
        g.esfera("ojo_negro", 0.17 * E, (s * 0.26 * E, -0.6 * E, ZH + 0.02 * E), esc=(1.2, 0.5, 1), lados=6, anillos=4)
        g.esfera("ojo_violeta", 0.09 * E, (s * 0.26 * E, -0.67 * E, ZH + 0.02 * E), lados=6, anillos=4)
        g.tubo("m_hueso", [(s * 0.45 * E, 0.05 * E, ZH + 0.3 * E), (s * 0.95 * E, 0.15 * E, ZH + 0.55 * E), (s * 1.15 * E, -0.1 * E, ZH + 1.1 * E),
                           (s * 0.85 * E, -0.45 * E, ZH + 1.5 * E)], [0.36, 0.3, 0.2, 0.0], lados=6)
    for i in range(5):
        g.cil("m_hueso", 0.07 * E, 0.2 * E, ((i - 2) * 0.13 * E, -0.7 * E, ZH - 0.72 * E), (180, 0, 0), lados=4, r2=0.0) if False else None
        g.cil("m_hueso", 0.06 * E, 0.22 * E, ((i - 2) * 0.13 * E, -0.7 * E, ZH - 0.74 * E), (0, 0, 0), lados=4, r2=0.0)
    g.cristal("m_cristal", 0.14 * E, 0.6 * E, (0, -0.3 * E, ZH + 0.5 * E), (-20, 0, 0), lados=5)
    # --- Brazos: hombrera de hueso con púas, antebrazo acorazado y garras.
    for s, nom in ((-1, "Left Arm"), (1, "Right Arm")):
        g.pieza(nom, pivote=(s * 1.5 * E, 0, ZT + 0.5 * E), padre="Torso")
        X = s * 1.5 * E
        g.caja("m_carne", (0.8 * E, 0.8 * E, 2.0 * E), (X, 0, ZT), sup=(0.85, 0.85), bisel=0.15)
        g.esfera("m_hueso", 0.78 * E, (X + s * 0.1 * E, 0, ZT + 0.75 * E), esc=(1.0, 1.0, 0.75), lados=9, anillos=5)
        for k in range(3):
            g.cil("m_hueso", 0.18 * E, 0.7 * E, (X + s * (0.2 + k * 0.22) * E, (k - 1) * 0.3 * E, ZT + 1.1 * E), (0, s * (15 + k * 20), 0), lados=5,
                  r2=0.0)
        g.caja("m_hueso", (0.95 * E, 0.95 * E, 0.8 * E), (X, 0, ZT - 0.45 * E), sup=(0.85, 0.85), bisel=0.12)
        g.cristal("m_cristal", 0.16 * E, 0.6 * E, (X + s * 0.45 * E, 0, ZT - 0.45 * E), (0, s * 70, 0), lados=5)
        for k in range(3):
            g.tubo("m_hueso", [(X + (k - 1) * 0.25 * E, -0.15 * E, ZT - 0.95 * E), (X + (k - 1) * 0.3 * E, -0.35 * E, ZT - 1.25 * E),
                               (X + (k - 1) * 0.3 * E, -0.2 * E, ZT - 1.5 * E)], [0.2, 0.15, 0.0], lados=4)
    # --- Piernas: grebas de hueso y pies con garras.
    for s, nom in ((-1, "Left Leg"), (1, "Right Leg")):
        g.pieza(nom, pivote=(s * 0.5 * E, 0, ZT - 1.0 * E), padre="Torso")
        X = s * 0.5 * E
        g.caja("m_carne", (0.85 * E, 0.85 * E, 2.0 * E), (X, 0, 1.0 * E), sup=(1.1, 1.1), bisel=0.15)
        g.caja("m_hueso", (0.95 * E, 0.5 * E, 1.0 * E), (X, -0.3 * E, 0.75 * E), sup=(0.8, 0.9), bisel=0.12)
        g.cil("m_hueso", 0.3 * E, 0.6 * E, (X, -0.5 * E, 1.2 * E), (-30, 0, 0), lados=5, r2=0.0)
        g.caja("m_carne", (0.95 * E, 1.3 * E, 0.4 * E), (X, -0.2 * E, 0.2 * E), bisel=0.1)
        for k in (-1, 0, 1):
            g.cil("m_hueso", 0.12 * E, 0.4 * E, (X + k * 0.28 * E, -0.8 * E, 0.12 * E), (100, 0, 0), lados=4, r2=0.0)
    # --- Arma de cristal: guja a dos manos, unida al brazo derecho.
    g.pieza("Arma", pivote=(1.5 * E, -0.3 * E, ZT - 1.1 * E), padre="Right Arm")
    ax, ay, az = 1.5 * E, -0.75 * E, ZT - 1.1 * E
    with g.grupo((ax, ay, az), (-12, 0, 0)):
        g.cil("m_negro_liso", 0.2, 11.0, (0, 0, -3.0), lados=6)
        for z in (-2.6, 0.6, 5.0):
            g.toro("m_hueso", 0.24, 0.1, (0, 0, z), seg=6, lados=4)
        g.prisma("m_cristal_osc", [(-0.5, 0), (0.5, 0), (1.3, 2.0), (0.9, 5.0), (0, 6.6), (-0.6, 4.0), (-0.3, 1.6)], 0.32, (0, 0, 7.6), plano="xz")
        g.prisma("m_cristal", [(1.3, 2.0), (0.9, 5.0), (0, 6.6), (0.25, 5.0), (0.6, 2.6)], 0.42, (0, 0, 7.6), plano="xz")
        g.cristal("m_cristal", 0.4, 1.4, (0, 0, -3.0), (180, 0, 0), lados=5, punta=0.7, base=0.8)
        g.tubo("m_hueso", [(0, 0, 7.4), (-0.7, 0, 7.9), (-1.1, 0, 8.9)], [0.3, 0.22, 0.0], lados=5)
    _rig(g, "Torso", "Criatura_GuardianOscuro", humanoide=True,
         articulaciones={"Head": "Neck", "Left Arm": "Left Shoulder", "Right Arm": "Right Shoulder", "Left Leg": "Left Hip",
                         "Right Leg": "Right Hip", "Arma": "Arma"})


MODELOS = [
    ("escarabajo_gigante", "enemigos", 5000, escarabajo_gigante),
    ("jabali_roca", "enemigos", 5000, jabali_roca),
    ("golem_musgo", "enemigos", 5000, golem_musgo),
    ("arana_cristal", "enemigos", 5000, arana_cristal),
    ("serpiente_sombra", "enemigos", 5000, serpiente_sombra),
    ("guardian_oscuro", "enemigos", 5000, guardian_oscuro),
]
