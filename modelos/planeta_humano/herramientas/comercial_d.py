"""Zona comercial (4): puestos del mercado y atrezo (mesa, toldo, cartel holográfico, caja, barril, carro)."""

import math

import arq
from mathutils import Matrix

from ph import NEON, V, Modelo

ZONA = "comercial"


def _estructura_puesto(c, m, ancho, fondo, alto, tubo, lona, lona2, arcos=3, rayas=True, parche=None):
    """Mesa de puesto con 3 arcos de tubo y toldo de lona tensada que cae entre los arcos."""
    for i in range(arcos):
        y = -fondo / 2 + 0.1 + i * (fondo - 0.2) / (arcos - 1)
        pts = [(-ancho / 2, y, 0.0), (-ancho / 2, y, alto - 0.6)]
        for k in range(1, 8):
            a = math.pi * k / 8
            pts.append((-math.cos(a) * ancho / 2, y, alto - 0.6 + math.sin(a) * 0.6))
        pts += [(ancho / 2, y, alto - 0.6), (ancho / 2, y, 0.0)]
        c.tubo(pts, 0.045, tubo, n=5, suave=False)
        for s in (-1, 1):
            c.cil((s * ancho / 2, y, 0), (s * ancho / 2, y, 0.05), 0.09, tubo, n=8)
    # lona: superficie que sigue el arco a lo largo de Y, con caída entre arcos
    def f(u, v):
        a = math.pi * (1 - u)
        x = math.cos(a) * (ancho / 2 + 0.06)
        z = alto - 0.6 + math.sin(a) * 0.66
        if abs(x) > ancho / 2 - 0.05:
            z = alto - 0.6 + math.sin(a) * 0.66
        y = -fondo / 2 - 0.05 + v * (fondo + 0.1)
        caida = 0.06 * abs(math.sin(v * (arcos - 1) * math.pi))
        return (x * (1 - 0.02 * caida), y, z - caida + 0.0)
    c.lamina(f, 12, 2 * (arcos - 1), 0.035, lona)
    # faldones laterales y delantero rayados
    if rayas:
        n = int(ancho / 0.4)
        for i in range(n):
            xa = -ancho / 2 + i * ancho / n
            xb = xa + ancho / n
            c.extruir([(xa, 0), (xb, 0), (xb, -0.25), ((xa + xb) / 2, -0.35), (xa, -0.25)], 0.025, [lona, lona2][i % 2],
                      c=(0, -fondo / 2 - 0.07, alto - 0.55), rot=(90, 0, 0))
    if parche:
        c.caja(parche, (0.35, 0.3, 0.05), lona2, 0.01, rot=(0, 30, 0))


def _mesa_puesto(c, ancho, fondo, alto, tabla, tubo, frente=None):
    c.caja((0, 0, alto - 0.05), (ancho - 0.1, fondo - 0.1, 0.1), tabla, 0.02)
    for k in range(5):
        x = -ancho / 2 + 0.05 + (k + 0.5) * (ancho - 0.1) / 5
        c.caja((x, 0, alto + 0.005), ((ancho - 0.1) / 5 - 0.02, fondo - 0.12, 0.02), tabla)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c.cil((sx * (ancho / 2 - 0.15), sy * (fondo / 2 - 0.15), 0), (sx * (ancho / 2 - 0.15), sy * (fondo / 2 - 0.15),
                                                                            alto - 0.1), 0.04, tubo, n=6)
    c.caja((0, -fondo / 2 + 0.06, alto - 0.35), (ancho - 0.2, 0.05, 0.4), frente or tabla, 0.01)


# ==============================================================================================================
def puesto_fruta():
    m = Modelo("puesto_fruta", ZONA, (4, 3, 4), 6000,
               "Puesto de fruta: toldo de lona sobre tres arcos de tubo, cajas de tablas con naranjas, manzanas con "
               "rabito y hoja, racimos de uvas, báscula colgante y pizarra de precios.")
    c = m.parte()
    tubo = m.mat("pintura", "#2E6A5A", desgaste=0.6)
    lona = m.mat("tela", "#E9DDBF", lluvia=0.4)
    lona2 = m.mat("tela", "#3E8A6E", lluvia=0.3)
    tabla = m.mat("madera", "#A27848", eje="X")
    tabla_c = m.mat("madera", "#B88F5C", eje="X", suciedad=0.3)
    clavo = m.mat("metal", "#5C5F63")
    naranja = m.mat("organico", "#E8821E")
    manzana = m.mat("organico", "#B8231E")
    manzana2 = m.mat("organico", "#7FAE2E")
    uva = m.mat("organico", "#5A2A6E", rug=0.25)
    hoja = m.mat("organico", "#3E7D2C")
    rabo = m.mat("madera", "#4A3220", eje="Z")
    laton = m.mat("metal", "#B48C42", rug=0.3)
    pizarra = m.mat("pizarra", "#1F2724")
    tiza = m.mat("tiza", "#EFEDE5")

    m.seccion("estructura")
    _estructura_puesto(c, m, 3.8, 2.6, 3.9, tubo, lona, lona2, parche=(1.0, 0.4, 3.75))
    _mesa_puesto(c, 3.4, 1.5, 1.5, tabla, tubo)
    rnd = m.rnd

    m.seccion("cajas con fruta")
    cajas = [(-1.05, -0.2, naranja, "naranja"), (0.0, -0.2, manzana, "manzana"), (1.05, -0.2, uva, "uva")]
    for (x, y, mat_f, tipo) in cajas:
        with c.en((x, y, 1.5), (-12, 0, 0)):
            arq.caja_madera(c, (0, 0, 0), (0.95, 0.75, 0.35), tabla_c, clavo, tablas=2)
            if tipo == "naranja":
                for i in range(4):
                    for j in range(3):
                        c.esfera((-0.33 + i * 0.22 + rnd.uniform(-0.02, 0.02), -0.22 + j * 0.22, 0.32 + rnd.uniform(0, 0.03)),
                                 0.1, naranja, seg=7, anillos=4)
                for i in range(2):
                    c.esfera((-0.11 + i * 0.22, -0.1 + (i % 2) * 0.2, 0.47), 0.1, naranja, seg=6, anillos=4)
            elif tipo == "manzana":
                for i in range(1, 4):
                    for j in range(3):
                        p = V((-0.44 + i * 0.22, -0.22 + j * 0.22, 0.33))
                        c.esfera(p, 0.1, manzana if (i + j) % 3 else manzana2, seg=7, anillos=4, esc=(1, 1, 0.9))
                        if (i + j) % 3 == 0:
                            c.cil(p + V((0, 0, 0.07)), p + V((0.02, 0, 0.15)), 0.01, rabo, n=4)
                            c.extruir([(0, 0), (0.05, 0.03), (0.09, 0), (0.05, -0.02)], 0.01, hoja,
                                      c=p + V((0.02, 0, 0.13)), rot=(0, -20, rnd.uniform(0, 180)))
            else:
                for i in range(2):
                    for j in range(2):
                        base = V((-0.2 + i * 0.4, -0.15 + j * 0.3, 0.42))
                        # racimo: esferas en capas que se estrechan
                        for capa in range(3):
                            nr = 4 - capa
                            for k in range(nr):
                                a = k * math.tau / nr + capa
                                r = 0.04 * nr
                                c.esfera(base + V((math.cos(a) * r, math.sin(a) * r * 0.8 - capa * 0.03, -capa * 0.05 + 0.02)),
                                         0.04, uva, seg=5, anillos=4)
                        c.cil(base + V((0, 0, 0.04)), base + V((0, -0.03, 0.12)), 0.008, rabo, n=4)
    # cajas apiladas en el suelo
    # saco de arpillera con naranjas en el suelo
    c.torno([(0.0, 0.0), (0.38, 0.02), (0.45, 0.25), (0.4, 0.55), (0.3, 0.62), (0.0, 0.6)], m.mat("tela", "#9A7E52"),
            n=10, c=(-1.2, 0.8, 0.0))

    m.seccion("báscula colgante")
    bx, by = 1.25, -0.9
    zt = 3.25
    c.cil((bx, by, zt), (bx, by, zt - 0.06), 0.03, laton, n=6)
    c.toro((bx, by, zt - 0.1), 0.05, 0.012, laton, n=8, m=4, rot=(90, 0, 0))
    c.cil((bx, by, zt - 0.15), (bx, by, zt - 0.3), 0.012, laton, n=4)
    c.cil((bx, by - 0.03, zt - 0.45), (bx, by + 0.03, zt - 0.45), 0.14, laton, n=10)  # esfera del dial
    c.cil((bx, by - 0.035, zt - 0.45), (bx, by - 0.04, zt - 0.45), 0.12, m.mat("plastico", "#F2EEE2"), n=10)
    c.caja((bx + 0.03, by - 0.045, zt - 0.42), (0.01, 0.004, 0.1), m.mat("pintura", "#B02020"), 0.0, rot=(0, 30, 0))
    c.cil((bx, by, zt - 0.6), (bx, by, zt - 0.7), 0.015, laton, n=4)
    for k in range(3):  # cadenas: eslabones
        a = k * math.tau / 3
        for e in range(3):
            t = e / 3
            p = V((bx + math.cos(a) * 0.2 * t, by + math.sin(a) * 0.2 * t, zt - 0.72 - t * 0.5))
            c.toro(p, 0.025, 0.006, laton, n=6, m=3, rot=(90 if e % 2 else 0, 0, math.degrees(a)))
    c.torno([(0.0, 0.0), (0.24, 0.03), (0.28, 0.1), (0.25, 0.1), (0.0, 0.04)], laton, n=10, c=(bx, by, zt - 1.3))
    for i in range(3):
        c.esfera((bx - 0.08 + i * 0.08, by, zt - 1.2), 0.08, naranja, seg=8, anillos=5)

    m.seccion("pizarra")
    with c.en((-1.3, -1.05, 1.2), (-6, 0, 0)):
        c.caja((0, 0, 0), (0.85, 0.05, 0.6), tabla, 0.015)
        c.caja((0, -0.03, 0), (0.75, 0.02, 0.5), pizarra, 0.0)
        tz = dict(alto=0.09, grosor=0.006, fuente="mono", resol=1)
        c.texto("FRUTA", tiza, c=(0, -0.045, 0.14), **tz)
        # dibujos de tiza (en relieve) de cada fruta con su precio
        for k, (precio, forma) in enumerate((("3c", "o"), ("4c", "a"), ("6c", "u"))):
            x = -0.25 + k * 0.25
            c.toro((x - 0.05, -0.04, -0.06), 0.035, 0.006, tiza, n=10, m=3, rot=(90, 0, 0))
            c.texto(precio, tiza, c=(x + 0.05, -0.045, -0.09), **dict(tz, alto=0.07))
    c.tubo([(-1.62, -1.06, 1.5), (-1.62, -1.06, 1.25)], 0.008, clavo, n=4, suave=False)
    m.terminar()


# ==============================================================================================================
def puesto_comida():
    m = Modelo("puesto_comida", ZONA, (4, 3, 4), 6000,
               "Puesto de comida caliente: dos ollas con tapa (una abierta con guiso), hornillo con llama azul, "
               "platos apilados, cubiertos en vaso, servilletero y pizarra del menú del día.")
    c = m.parte()
    llama = m.parte("llama_neon", tipo="neon", color="#3D8BFF", nota="Llama del hornillo: Neon azul #3D8BFF.")
    tubo = m.mat("pintura", "#8A2E24", desgaste=0.6)
    lona = m.mat("tela", "#D8432E", lluvia=0.4)
    lona2 = m.mat("tela", "#F0E6D2", lluvia=0.3)
    tabla = m.mat("madera", "#8E6438", eje="X")
    acero = m.mat("metal", "#9CA2A8", rug=0.3)
    osc = m.mat("metal", "#2E3236", rug=0.5, hollin=(0.0, 0.0))
    olla = m.mat("metal", "#7F858B", rug=0.35, suciedad=0.6)
    guiso = m.mat("liquido", "#8A4A1E", rug=0.25, bump=0.4, patron="poros")
    trozo = m.mat("organico", "#C77B3A")
    verdura = m.mat("organico", "#4E8F2E")
    plato = m.mat("ceramica", "#ECE8DF")
    madera_m = m.mat("madera", "#6E4A2A", eje="Z")
    pizarra = m.mat("pizarra", "#1F2724")
    tiza = m.mat("tiza", "#EFEDE5")

    m.seccion("estructura")
    _estructura_puesto(c, m, 3.8, 2.6, 3.9, tubo, lona, lona2, parche=(-1.1, 0.6, 3.7))
    _mesa_puesto(c, 3.4, 1.5, 1.5, tabla, tubo, frente=m.mat("pintura", "#E6D9BC", desgaste=0.4))
    # chapa metálica sobre la mesa donde va el hornillo
    c.caja((0.6, 0.0, 1.53), (2.0, 1.3, 0.04), acero, 0.01)

    m.seccion("hornillo y ollas")
    for (ox, abierta) in ((0.1, False), (1.1, True)):
        # hornillo: cuerpo, parrilla y quemador
        c.caja((ox, 0.0, 1.62), (0.75, 0.75, 0.14), osc, 0.03)
        for k in range(4):
            a = k * math.pi / 2
            c.caja((ox + math.cos(a) * 0.2, math.sin(a) * 0.2, 1.71), (0.32, 0.04, 0.04), osc, 0.0,
                   rot=(0, 0, math.degrees(a)))
        c.cil((ox, 0, 1.69), (ox, 0, 1.72), 0.12, osc, n=10)
        for k in range(10):
            a = k * math.tau / 10
            llama.cil((ox + math.cos(a) * 0.12, math.sin(a) * 0.12, 1.71), (ox + math.cos(a) * 0.15, math.sin(a) * 0.15,
                                                                          1.79), 0.025, None, n=4, r1=0.0)
        c.cil((ox + 0.3, -0.38, 1.62), (ox + 0.3, -0.45, 1.62), 0.04, acero, n=8)  # mando
        # olla
        oz = 1.73
        c.torno([(0.0, 0.0), (0.3, 0.0), (0.33, 0.04), (0.33, 0.48), (0.35, 0.5), (0.3, 0.5), (0.3, 0.05), (0.0, 0.05)],
                olla, n=16, c=(ox, 0, oz))
        for s in (-1, 1):
            c.tubo([(ox + s * 0.33, 0, oz + 0.4), (ox + s * 0.42, 0, oz + 0.4), (ox + s * 0.42, 0, oz + 0.32),
                    (ox + s * 0.33, 0, oz + 0.32)], 0.02, osc, n=5, suave=False)
        if abierta:
            # guiso: superficie ondulada espesa con tropiezos
            c.lamina(lambda u, v: (ox + (u - 0.5) * 0.56 * math.sqrt(max(0.0, 1 - (2 * v - 1) ** 2)),
                                   (v - 0.5) * 0.56, oz + 0.38 + 0.015 * math.sin(u * 9) * math.cos(v * 7)), 6, 6, 0.04,
                     guiso)
            for k in range(6):
                a = k * 1.7
                c.ico((ox + math.cos(a) * 0.15, math.sin(a) * 0.12, oz + 0.41), 0.045, [trozo, verdura][k % 2], sub=1,
                      ruido=0.2, semilla=k)
            # tapa apoyada de lado y cucharón
            with c.en((ox + 0.55, 0.45, 1.58), (70, 0, 20)):
                c.torno([(0.0, 0.08), (0.18, 0.06), (0.33, 0.0), (0.34, -0.02), (0.0, 0.0)], olla, n=14)
                c.cil((0, 0, 0.08), (0, 0, 0.13), 0.04, osc, n=8)
            c.cil((ox + 0.1, 0.05, oz + 0.38), (ox + 0.25, 0.1, oz + 0.85), 0.018, acero, n=5)
            c.esfera((ox + 0.09, 0.05, oz + 0.38), 0.06, acero, seg=8, anillos=4, esc=(1, 1, 0.5))
        else:
            c.torno([(0.0, 0.1), (0.18, 0.08), (0.34, 0.01), (0.35, -0.01), (0.0, 0.0)], olla, n=16, c=(ox, 0, oz + 0.5))
            c.cil((ox, 0, oz + 0.6), (ox, 0, oz + 0.66), 0.05, osc, n=8)
            c.esfera((ox, 0, oz + 0.68), 0.05, osc, seg=8, anillos=4)

    m.seccion("platos, cubiertos y servilletero")
    for k in range(6):
        c.torno([(0.0, 0.0), (0.12, 0.0), (0.2, 0.025), (0.21, 0.035), (0.19, 0.035), (0.0, 0.015)], plato, n=14,
                c=(-1.0, -0.15, 1.55 + k * 0.03))
    for k in range(4):
        c.torno([(0.0, 0.0), (0.09, 0.0), (0.15, 0.08), (0.14, 0.09), (0.0, 0.03)], plato, n=12,
                c=(-1.0, 0.35, 1.55 + k * 0.06))
    # vaso con cubiertos
    c.torno([(0.0, 0.0), (0.08, 0.0), (0.09, 0.25), (0.08, 0.25), (0.07, 0.02), (0.0, 0.02)], acero, n=10,
            c=(-0.5, 0.3, 1.55))
    for k in range(5):
        a = k * math.tau / 5
        top = V((-0.5 + math.cos(a) * 0.05, 0.3 + math.sin(a) * 0.05, 1.95))
        c.cil((-0.5 + math.cos(a) * 0.02, 0.3 + math.sin(a) * 0.02, 1.58), top, 0.01, acero, n=4)
        if k % 2:
            c.esfera(top + V((0, 0, 0.03)), 0.03, acero, seg=6, anillos=4, esc=(1, 0.6, 1.4))
        else:
            c.caja(top + V((0, 0, 0.04)), (0.04, 0.01, 0.08), acero, 0.0)
    # servilletero metálico con servilletas
    c.caja((-0.45, -0.35, 1.6), (0.25, 0.12, 0.04), acero, 0.01)
    for s in (-1, 1):
        c.caja((-0.45 + s * 0.11, -0.35, 1.72), (0.02, 0.1, 0.22), acero, 0.005)
    c.caja((-0.45, -0.35, 1.72), (0.2, 0.08, 0.2), m.mat("papel", "#FAFAF5"), 0.005)

    m.seccion("pizarra")
    with c.en((-0.9, -1.4, 0), (0, 0, 10)):
        for s in (-1, 1):
            c.cil((s * 0.4, -0.2, 0), (s * 0.38, 0, 1.4), 0.03, madera_m, n=5)
            c.cil((s * 0.4, 0.25, 0), (s * 0.38, 0, 1.4), 0.03, madera_m, n=5)
        c.caja((0, -0.1, 0.85), (0.85, 0.05, 0.95), madera_m, 0.015, rot=(-8, 0, 0))
        with c.en((0, -0.13, 0.85), (-8, 0, 0)):
            c.caja((0, 0, 0), (0.75, 0.02, 0.85), pizarra, 0.0)
            tz = dict(alto=0.085, grosor=0.006, fuente="mono", resol=1)
            c.texto("MENÚ DEL DÍA", tiza, c=(0, -0.015, 0.25), **tz)
            c.texto("Guiso 5c", tiza, c=(0, -0.015, 0.0), **tz)
            for k in range(3):  # subrayado y líneas de tiza
                c.caja((0, -0.015, 0.2 - k * 0.0 - 0.0 if k == 0 else -0.15 - k * 0.08), (0.5 - k * 0.1, 0.006, 0.012), tiza)
    m.terminar()


# ==============================================================================================================
def puesto_telas():
    m = Modelo("puesto_telas", ZONA, (4, 3, 4), 6000,
               "Puesto de telas: rollos de tela de colores apoyados en diagonal, tres prendas en perchas colgadas "
               "de una barra, cinta métrica enrollada y tijeras.")
    c = m.parte()
    tubo = m.mat("pintura", "#3B4D7A", desgaste=0.6)
    lona = m.mat("tela", "#7A4E9A", lluvia=0.4)
    lona2 = m.mat("tela", "#E9D7A8", lluvia=0.3)
    tabla = m.mat("madera", "#946A40", eje="X")
    colores = ["#C2332B", "#2E7DB0", "#E3B23C", "#3E8E4E", "#8E3E8A", "#E8E2D2"]
    telas = [m.mat("tela", h, suciedad=0.1) for h in colores]
    acero = m.mat("metal", "#8E949A", rug=0.3)
    laton = m.mat("metal", "#B48C42", rug=0.3)
    madera_p = m.mat("madera", "#C49A64", eje="X")
    cinta = m.mat("plastico", "#E2C43A")
    roja = m.mat("plastico", "#B42C2C")

    m.seccion("estructura")
    _estructura_puesto(c, m, 3.8, 2.6, 3.9, tubo, lona, lona2)
    _mesa_puesto(c, 3.4, 1.5, 1.5, tabla, tubo)

    m.seccion("rollos de tela")
    # rollos apoyados en diagonal contra un listón trasero, con el extremo de tela desenrollado
    c.caja((-0.4, 0.6, 2.1), (2.4, 0.08, 0.08), tabla, 0.01)
    for i in range(5):
        x = -1.45 + i * 0.5
        a = V((x, -0.45, 1.6))
        b = V((x + 0.1, 0.62, 2.2))
        c.cil(a, b, 0.17, telas[i], n=12)
        c.cil(a - (b - a).normalized() * 0.03, a, 0.06, madera_p, n=8)  # alma de cartón
        c.toro(a.lerp(b, 0.15), 0.172, 0.015, telas[(i + 2) % 6], n=12, m=3,
               rot=(math.degrees(math.atan2((b - a).length, 0)) * 0 + 61, 0, 0))
    # rollos tumbados en primer plano y una pieza desplegada sobre la mesa
    for i in range(3):
        c.cil((-1.4 + i * 0.45, -0.55, 1.68), (-1.4 + i * 0.45, 0.2, 1.68), 0.15, telas[(i + 3) % 6], n=12)
    c.lamina(lambda u, v: (0.2 + u * 1.2, -0.6 + v * 0.9, 1.565 + 0.02 * math.sin(u * 11) * math.sin(v * 5)), 8, 4, 0.02,
             telas[1])

    m.seccion("barra de ropa con perchas")
    bz = 3.05
    c.cil((-1.8, -1.0, bz), (1.8, -1.0, bz), 0.035, acero, n=8)
    for s in (-1, 1):
        c.tubo([(s * 1.8, -1.0, bz), (s * 1.85, -1.0, bz - 0.05), (s * 1.9, -1.0, bz - 0.4)], 0.03, acero, n=6, seg=2)
    def camisa(x, color):
        # gancho y percha
        c.tubo([(x, -1.0, bz + 0.03), (x + 0.06, -1.0, bz + 0.05), (x + 0.05, -1.0, bz - 0.06), (x, -1.0, bz - 0.1)],
               0.008, laton, n=4, seg=2)
        c.tubo([(x - 0.3, -1.0, bz - 0.3), (x, -1.0, bz - 0.12), (x + 0.3, -1.0, bz - 0.3)], 0.015, madera_p, n=5,
               suave=False)
        # camisa: silueta extruida con grosor y un poco de vuelo (lámina)
        sil = [(-0.12, 0.0), (-0.32, -0.1), (-0.5, -0.45), (-0.38, -0.52), (-0.28, -0.32), (-0.27, -1.05), (0.27, -1.05),
               (0.28, -0.32), (0.38, -0.52), (0.5, -0.45), (0.32, -0.1), (0.12, 0.0), (0.0, -0.1)]
        c.extruir(sil, 0.08, color, c=(x, -1.0, bz - 0.13), rot=(90, 0, 0), b=0.015)
        # cuello y botones
        c.extruir([(-0.12, 0.0), (0.0, -0.14), (0.12, 0.0), (0.0, -0.06)], 0.1, color, c=(x, -1.0, bz - 0.12),
                  rot=(90, 0, 0))
        for k in range(4):
            c.cil((x, -1.04, bz - 0.35 - k * 0.17), (x, -1.06, bz - 0.35 - k * 0.17), 0.018, acero, n=6)
    camisa(-1.0, telas[1])
    camisa(0.05, telas[5])
    camisa(1.05, telas[3])

    m.seccion("cinta métrica y tijeras")
    with c.en((1.05, 0.05, 1.55)):
        c.cil((0, 0, 0), (0, 0, 0.04), 0.14, cinta, n=14)
        c.toro((0, 0, 0.02), 0.14, 0.02, cinta, n=14, m=4)
        c.cil((0, 0, 0.04), (0, 0, 0.05), 0.06, acero, n=10)
        c.lamina(lambda u, v: (0.14 + u * 0.55, -0.02 + v * 0.03, 0.005 + 0.01 * math.sin(u * 6)), 6, 1, 0.006, cinta)
    with c.en((0.5, -0.3, 1.56), (0, 0, 25)):
        for s in (-1, 1):
            with c.en((0, 0, 0.01 * s), (0, 0, s * 10)):
                c.extruir([(0, -0.02), (0.38, -0.005), (0.38, 0.005), (0, 0.02)], 0.012, acero)
                c.toro((-0.12, s * 0.06, 0), 0.055, 0.016, roja, n=10, m=4)
                c.cil((-0.02, 0, 0), (-0.07, s * 0.04, 0), 0.016, roja, n=5)
        c.cil((0, 0, -0.02), (0, 0, 0.02), 0.012, laton, n=6)
    # alfiletero (esfera roja con alfileres)
    c.esfera((-0.1, 0.35, 1.62), 0.08, roja, seg=8, anillos=5)
    for k in range(5):
        a = k * 1.3
        c.cil((-0.1 + math.cos(a) * 0.05, 0.35 + math.sin(a) * 0.05, 1.66), (-0.1 + math.cos(a) * 0.1,
                                                                             0.35 + math.sin(a) * 0.1, 1.72),
              0.004, acero, n=3)
    m.terminar()


# ==============================================================================================================
def mesa_mercado():
    m = Modelo("mesa_mercado", ZONA, (3, 2, 2), 2000,
               "Mesa de mercado vacía para NPCs: patas plegables de tubo con bisagras, tablero de tablones gastados "
               "y cajón con tirador.")
    # La mesa se modela a 1,7 de alto y se estira en vertical hasta los 2 studs pedidos.
    k = 2.0 / 1.675
    c = m.parte()
    cajon = m.parte("cajon", pivote=(0, -0.65, 1.15 * k), nota="Cajón: se abre deslizándolo 0,6 studs hacia delante (-Z).")
    for p in (c, cajon):
        p.pila = [Matrix.Diagonal((1.0, 1.0, k, 1.0))]
    tabla = m.mat("madera", "#9A7044", eje="X", desgaste=0.5, c_desgaste="#C9A57A")
    tubo = m.mat("pintura", "#3C5A66", desgaste=0.6)
    acero = m.mat("metal", "#8A9096")
    laton = m.mat("metal", "#B48C42", rug=0.3)
    # tablero de 6 tablones con juntas y travesaños debajo
    for k in range(6):
        y = -0.85 + k * 0.34
        c.caja((0, y + 0.0, 1.62), (2.9, 0.32, 0.1), tabla, 0.025)
    for x in (-1.2, 0.0, 1.2):
        c.caja((x, 0, 1.52), (0.12, 1.8, 0.1), tabla, 0.02)
        for k in range(6):
            c.cil((x, -0.85 + k * 0.34, 1.67), (x, -0.85 + k * 0.34, 1.675), 0.02, acero, n=5)
    # patas en X plegables con bisagra en el cruce y en el tablero
    for x in (-1.1, 1.1):
        for s in (-1, 1):
            c.cil((x, s * 0.75, 0.0), (x, -s * 0.75, 1.46), 0.04, tubo, n=6)
            c.cil((x, s * 0.75, 0.0), (x, s * 0.75, 0.04), 0.07, m.mat("goma", "#1E1F22"), n=6)
        c.cil((x - 0.07, 0, 0.73), (x + 0.07, 0, 0.73), 0.055, acero, n=8)  # bisagra del cruce
        for s in (-1, 1):
            c.caja((x, -s * 0.75, 1.48), (0.14, 0.12, 0.06), acero, 0.01)
            c.cil((x - 0.08, -s * 0.75, 1.46), (x + 0.08, -s * 0.75, 1.46), 0.03, acero, n=6)
        c.cil((x, -0.7, 0.2), (x, 0.7, 0.2), 0.025, tubo, n=6)  # tirante
    # guías y caja del cajón
    for s in (-1, 1):
        c.caja((s * 0.62, -0.1, 1.33), (0.05, 1.3, 0.25), tabla, 0.01)
    cajon.caja((0, -0.15, 1.3), (1.1, 1.2, 0.04), tabla, 0.01)
    for s in (-1, 1):
        cajon.caja((s * 0.53, -0.15, 1.38), (0.04, 1.2, 0.18), tabla, 0.01)
    cajon.caja((0, 0.43, 1.38), (1.1, 0.04, 0.18), tabla, 0.01)
    cajon.caja((0, -0.77, 1.38), (1.2, 0.05, 0.24), tabla, 0.02)
    cajon.tubo([(-0.2, -0.8, 1.4), (-0.2, -0.88, 1.4), (0.2, -0.88, 1.4), (0.2, -0.8, 1.4)], 0.018, laton, n=5, seg=2)
    m.terminar()


# ==============================================================================================================
def toldo_mercado():
    m = Modelo("toldo_mercado", ZONA, (5, 4, 3), 2000,
               "Toldo desmontable: cuatro postes de tubo, lona tensada con arrugas y un parche cosido, vientos de "
               "cuerda con nudos y estacas.")
    c = m.parte()
    tubo = m.mat("metal", "#8C9298")
    lona = m.mat("tela", "#C8B48A", lluvia=0.5)
    parche = m.mat("tela", "#6E8A5A")
    cuerda = m.mat("tela", "#B39A6E", bump=0.6)
    estaca = m.mat("metal", "#5D5246", rug=0.6)
    W, D, H = 4.4, 3.4, 2.7
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = V((sx * W / 2, sy * D / 2, 0))
            c.cil(p, p + V((0, 0, H + 0.1)), 0.05, tubo, n=6)
            c.cil(p, p + V((0, 0, 0.04)), 0.12, tubo, n=6)
            c.esfera(p + V((0, 0, H + 0.12)), 0.07, tubo, seg=6, anillos=4)
            # viento: cuerda con nudo y estaca
            q = p + V((sx * 0.5, sy * 0.5, 0))
            c.tubo([p + V((0, 0, H)), p.lerp(q, 0.5) + V((0, 0, H * 0.45)), q + V((0, 0, 0.12))], 0.015, cuerda, n=4,
                   suave=False)
            c.esfera(p + V((0, 0, H - 0.03)), 0.04, cuerda, seg=6, anillos=4)
            c.esfera(q + V((0, 0, 0.13)), 0.035, cuerda, seg=6, anillos=4)
            c.cil(q + V((0, 0, -0.1)), q + V((0, 0, 0.18)), 0.025, estaca, n=4)
    for sy in (-1, 1):
        c.cil((-W / 2, sy * D / 2, H), (W / 2, sy * D / 2, H), 0.04, tubo, n=6)
    for sx in (-1, 1):
        c.cil((sx * W / 2, -D / 2, H), (sx * W / 2, D / 2, H), 0.04, tubo, n=6)
    c.cil((0, -D / 2, H + 0.35), (0, D / 2, H + 0.35), 0.04, tubo, n=6)
    for sy in (-1, 1):
        c.cil((-W / 2, sy * D / 2, H), (0, sy * D / 2, H + 0.35), 0.03, tubo, n=5)
        c.cil((W / 2, sy * D / 2, H), (0, sy * D / 2, H + 0.35), 0.03, tubo, n=5)
    # lona a dos aguas con arrugas diagonales
    def f(u, v):
        x = -W / 2 - 0.12 + u * (W + 0.24)
        y = -D / 2 - 0.12 + v * (D + 0.24)
        z = H + 0.38 - abs(x) / (W / 2) * 0.35 + 0.025 * math.sin(u * 23 + v * 9) * math.sin(v * math.pi)
        return (x, y, z + 0.05)
    c.lamina(f, 16, 8, 0.03, lona)
    # parche cosido (con puntadas)
    with c.en((1.1, 0.5, H + 0.27), (0, math.degrees(math.atan2(0.35, W / 2)), 0)):
        c.caja((0, 0, 0), (0.5, 0.42, 0.012), parche, 0.004)
        for k in range(6):
            c.caja((-0.22 + k * 0.088, 0.22, 0.008), (0.04, 0.012, 0.006), cuerda)
            c.caja((-0.22 + k * 0.088, -0.22, 0.008), (0.04, 0.012, 0.006), cuerda)
    # faldones caídos en los aleros (lados largos de la lona, a lo largo de Y), cosidos al borde del tejado
    for sx in (-1, 1):
        c.lamina(lambda u, v, sx=sx: (sx * (W / 2 + 0.13 + 0.02 * math.sin(u * 30)), -D / 2 - 0.12 + u * (D + 0.24),
                                      H + 0.06 - v * 0.32), 12, 1, 0.025, lona)
    m.terminar()


# ==============================================================================================================
def cartel_holografico():
    m = Modelo("cartel_holografico", ZONA, (4, 0.3, 3), 2000,
               "Cartel publicitario holográfico de pared: marco metálico fino, cuatro proyectores en las esquinas, "
               "pantalla neón con logotipo y texto simulado, tornillos de montaje.")
    c = m.parte()
    pant = m.parte("pantalla_neon", tipo="neon", color=NEON, transparencia=0.25,
                   nota="Pantalla: Neon cyan, Transparency 0,25 para el efecto holograma.")
    acero = m.mat("metal", "#7C8288")
    osc = m.mat("metal", "#262A2F", rug=0.45)
    lente = m.mat("cromo", "#9FE8F0", rug=0.1)
    W, H = 4.0, 3.0
    # marco: perfil fino con esquineras
    for (cx, cz, w, h) in ((0, H - 0.06, W, 0.12), (0, 0.06, W, 0.12), (-W / 2 + 0.06, H / 2, 0.12, H),
                           (W / 2 - 0.06, H / 2, 0.12, H)):
        c.caja((cx, 0.06, cz), (w, 0.12, h), osc, 0.02)
    c.caja((0, 0.13, H / 2), (W - 0.1, 0.04, H - 0.1), osc, 0.0)  # trasera
    for sx in (-1, 1):
        for sz in (0, 1):
            x = sx * (W / 2 - 0.12)
            z = 0.12 if sz == 0 else H - 0.12
            c.caja((x, 0.0, z), (0.3, 0.16, 0.3), acero, 0.03)
            # proyector cilíndrico apuntando al centro
            d = V((-sx, -0.25, 1 if sz == 0 else -1)).normalized() * 0.2
            p = V((x, -0.1, z))
            c.cil(p, p + d, 0.07, osc, n=10)
            c.cil(p + d, p + d * 1.15, 0.055, lente, n=10)
            pant.cil(p + d * 1.15, p + d * 1.2, 0.04, None, n=8)
            for k in range(2):
                c.perno((x + sx * 0.1 * (-1 if k else 1), 0.0 - 0.08, z + (0.1 if k else -0.1)), (0, -1, 0), acero, r=0.025)
    # tornillos de montaje a pared con escuadras
    for x in (-1.2, 1.2):
        for z in (0.3, H - 0.3):
            c.caja((x, 0.2, z), (0.25, 0.08, 0.2), acero, 0.01)
            c.perno((x, 0.16, z), (0, -1, 0), acero, r=0.035)
    # pantalla: lámina fina + logotipo (anillo y planeta) + líneas de texto
    pant.caja((0, 0.03, H / 2), (W - 0.3, 0.02, H - 0.3), None, 0.0)
    with pant.en((-0.9, -0.02, H / 2 + 0.25), (90, 0, 0)):
        pant.toro((0, 0, 0), 0.5, 0.04, None, n=20, m=4)
        pant.esfera((0, 0, 0), 0.3, None, seg=10, anillos=6, esc=(1, 1, 0.3))
    pant.texto("NOVA", None, alto=0.42, grosor=0.04, c=(0.65, -0.02, H / 2 + 0.25), fuente="estrecha")
    for k in range(3):
        pant.caja((0, -0.01, 0.65 - k * 0.15 + 0.2), (2.6 - k * 0.6, 0.02, 0.06), None, 0.0)
    m.terminar()


# ==============================================================================================================
def caja_envio():
    m = Modelo("caja_envio", ZONA, (2, 2, 2), 2000,
               "Caja de transporte espacial: metal con cantoneras, 8 remaches, dos correas cruzadas con hebilla, "
               "etiqueta de envío y logo estampado.")
    c = m.parte()
    chapa = m.mat("pintura", "#5C7A8C", desgaste=0.6, abolladuras=0.4)
    acero = m.mat("metal", "#8B9097")
    correa = m.mat("tela", "#D88A2A", bump=0.5)
    papel = m.mat("papel", "#EDE6D2")
    tinta = m.mat("pintura", "#1E2328", desgaste=0.0)
    blanco = m.mat("pintura", "#E8E6DF", desgaste=0.5)
    L = 1.9
    c.caja((0, 0, L / 2), (L, L, L), chapa, 0.06)
    # cantoneras en las 8 esquinas (tres placas cada una) con su remache
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (0, 1):
                z = 0.12 if sz == 0 else L - 0.12
                p = V((sx * (L / 2 - 0.12), sy * (L / 2 - 0.12), z))
                c.caja(p + V((sx * 0.13, 0, 0)), (0.04, 0.3, 0.3), acero, 0.01)
                c.caja(p + V((0, sy * 0.13, 0)), (0.3, 0.04, 0.3), acero, 0.01)
                c.caja(p + V((0, 0, (0.13 if sz else -0.13))), (0.3, 0.3, 0.04), acero, 0.01)
                c.remache(p + V((0, sy * 0.15, 0)), (0, sy, 0), acero, 0.05)
    # correas cruzadas (dan la vuelta) con hebilla
    for eje in ("X", "Y"):
        w = 0.18
        if eje == "X":
            c.caja((0, 0, L + 0.012), (L + 0.04, w, 0.025), correa, 0.005)
            for s in (-1, 1):
                c.caja((s * (L / 2 + 0.012), 0, L / 2), (0.025, w, L), correa, 0.005)
        else:
            c.caja((0, 0, L + 0.03), (w, L + 0.04, 0.025), correa, 0.005)
            for s in (-1, 1):
                c.caja((0, s * (L / 2 + 0.012), L / 2), (w, 0.025, L), correa, 0.005)
    c.caja((0, -(L / 2 + 0.04), L * 0.62), (0.28, 0.04, 0.2), acero, 0.01)
    c.caja((0, -(L / 2 + 0.065), L * 0.62), (0.2, 0.02, 0.12), correa, 0.0)
    c.cil((0, -(L / 2 + 0.075), L * 0.56), (0, -(L / 2 + 0.075), L * 0.68), 0.015, acero, n=4)
    # etiqueta de envío pegada (fina, con texto en relieve)
    c.caja((0.5, -(L / 2 + 0.01), 0.55), (0.55, 0.012, 0.4), papel, 0.0)
    for k in range(4):
        c.caja((0.47, -(L / 2 + 0.018), 0.66 - k * 0.07), (0.42 - (k % 2) * 0.12, 0.006, 0.03), tinta, 0.0)
    for k in range(8):
        c.caja((0.33 + k * 0.045, -(L / 2 + 0.018), 0.4), (0.015 + (k % 3) * 0.008, 0.006, 0.08), tinta, 0.0)
    # logotipo de la empresa estampado (lateral): anillo, flecha y letras
    with c.en((L / 2 + 0.005, 0.0, 1.05), (90, 0, 90)):
        c.toro((0, 0, 0), 0.32, 0.03, blanco, n=16, m=3)
        c.extruir([(-0.2, -0.05), (0.08, -0.05), (0.08, -0.14), (0.25, 0.0), (0.08, 0.14), (0.08, 0.05), (-0.2, 0.05)],
                  0.012, blanco)
    c.texto("OT-7", blanco, alto=0.18, grosor=0.01, c=(L / 2 + 0.005, 0.0, 0.55), rot=(90, 0, 90), fuente="mono", resol=1)
    m.terminar()


# ==============================================================================================================
def barril_metal():
    m = Modelo("barril_metal", ZONA, (1.5, 1.5, 2), 2000,
               "Barril metálico sci-fi: cierre hermético con junta de goma, asa articulada, manómetro, etiqueta y "
               "abolladuras de uso.")
    c = m.parte()
    asa = m.parte("asa", pivote=(0, 0, 1.98), nota="Asa articulada: gira sobre el eje X de Roblox en el pivote.")
    chapa = m.mat("pintura", "#B4502A", desgaste=0.65, abolladuras=0.6)
    acero = m.mat("metal", "#8D9399")
    goma = m.mat("goma", "#151618")
    papel = m.mat("papel", "#E6DFC8")
    tinta = m.mat("pintura", "#1E2226", desgaste=0.0)
    cristal = m.mat("cromo", "#D0E4E8", rug=0.05)
    blanco = m.mat("plastico", "#F0EEE6")
    R = 0.68
    # cuerpo con dos aros de rodadura y abolladuras (perfil irregular)
    perfil = [(0.0, 0.0), (R - 0.05, 0.0), (R, 0.06), (R, 0.45), (R + 0.04, 0.48), (R + 0.04, 0.56), (R, 0.59),
              (R - 0.01, 1.0), (R, 1.35), (R + 0.04, 1.38), (R + 0.04, 1.46), (R, 1.49), (R, 1.82), (R - 0.05, 1.88),
              (0.0, 1.88)]
    c.torno(perfil, chapa, n=24)
    # tapa hermética: junta de goma, anillo de cierre con palanca y tornillos
    c.cil((0, 0, 1.86), (0, 0, 1.9), R - 0.02, goma, n=24)
    c.cil((0, 0, 1.9), (0, 0, 1.96), R - 0.06, acero, n=24)
    c.toro((0, 0, 1.92), R - 0.01, 0.035, acero, n=24, m=4)
    c.caja((R - 0.02, 0, 1.92), (0.2, 0.12, 0.08), acero, 0.02)
    c.cil((R + 0.06, 0, 1.92), (R + 0.06, 0, 1.75), 0.025, acero, n=6)  # palanca del aro
    for k in range(6):
        a = k * math.tau / 6
        c.perno((math.cos(a) * (R - 0.15), math.sin(a) * (R - 0.15), 1.96), (0, 0, 1), acero, r=0.03)
    c.cil((0.25, 0.15, 1.96), (0.25, 0.15, 2.0), 0.08, acero, n=10)  # tapón de llenado
    # asa articulada (pieza aparte)
    for s in (-1, 1):
        asa.cil((s * 0.42, 0, 1.96), (s * 0.42, 0, 2.06), 0.04, acero, n=8)
    asa.tubo([(-0.42, 0, 2.02), (-0.42, 0, 2.2), (-0.3, 0, 2.3), (0.3, 0, 2.3), (0.42, 0, 2.2), (0.42, 0, 2.02)], 0.025,
             acero, n=6, seg=2)
    asa.cil((-0.15, 0, 2.3), (0.15, 0, 2.3), 0.045, goma, n=8)
    # manómetro (esfera con aguja) sobre un racor
    mp = V((0, -R, 1.62))
    c.cil(mp, mp + V((0, -0.08, 0)), 0.03, acero, n=6)
    c.cil(mp + V((0, -0.08, 0)), mp + V((0, -0.16, 0)), 0.1, acero, n=14)
    c.cil(mp + V((0, -0.16, 0)), mp + V((0, -0.165, 0)), 0.085, blanco, n=14)
    c.caja(mp + V((0.02, -0.17, 0.02)), (0.012, 0.005, 0.07), tinta, 0.0, rot=(0, -40, 0))
    c.esfera(mp + V((0, -0.165, 0)), 0.085, cristal, seg=10, anillos=4, esc=(1, 0.25, 1))
    # etiqueta de contenido con rombo de peligro
    with c.en((0, 0, 0.95)):
        c.lamina(lambda u, v: (math.cos(-math.pi / 2 + (u - 0.5) * 1.1) * (R + 0.006),
                               math.sin(-math.pi / 2 + (u - 0.5) * 1.1) * (R + 0.006), (v - 0.5) * 0.55), 6, 1, 0.006, papel)
        c.extruir([(0, 0.13), (0.13, 0), (0, -0.13), (-0.13, 0)], 0.008, m.mat("pintura", "#E0B32A", desgaste=0.0),
                  c=(-0.12, -R - 0.012, 0.05), rot=(90, 0, 0))
        for k in range(3):
            c.caja((0.15, -R - 0.012, 0.12 - k * 0.09), (0.22, 0.004, 0.03), tinta, 0.0)
    m.terminar()


# ==============================================================================================================
def carro_carga():
    m = Modelo("carro_carga", ZONA, (3, 2, 2), 4000,
               "Carretilla de carga hover sin ruedas: plataforma con carga atada, 4 discos de levitación, barra de "
               "agarre curvada y freno de pie con muelle.")
    c = m.parte()
    disc = m.parte("discos_neon", tipo="neon", color=NEON, transparencia=0.3,
                   nota="Discos de levitación: Neon cyan tenue (Transparency 0,3).")
    pedal = m.parte("freno", pivote=(1.05, 0, 0.45), nota="Pedal de freno: gira hacia abajo 20° sobre su eje.")
    base = m.mat("pintura", "#E6B530", desgaste=0.7, abolladuras=0.3)
    grip = m.mat("grip", "#555B62")
    acero = m.mat("metal", "#848A91")
    osc = m.mat("metal", "#2B2F34", rug=0.5)
    goma = m.mat("goma", "#1C1D20")
    caja1 = m.mat("pintura", "#4F6B7A", desgaste=0.5)
    caja2 = m.mat("madera", "#9C7448", eje="X")
    cinta = m.mat("tela", "#C23A2A", bump=0.5)
    muelle = m.mat("cromo", "#BFC5CB")
    Z = 0.45
    # plataforma con borde y chapa antideslizante
    c.caja((0, 0, Z), (2.8, 1.7, 0.22), base, 0.05)
    c.caja((0, 0, Z + 0.12), (2.6, 1.5, 0.03), grip, 0.005)
    for s in (-1, 1):
        c.caja((0, s * 0.86, Z + 0.06), (2.8, 0.06, 0.3), osc, 0.02)
    # 4 discos de levitación bajo la plataforma
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = V((sx * 1.0, sy * 0.55, Z - 0.11))
            c.cil(p, p - V((0, 0, 0.1)), 0.3, osc, n=16)
            c.toro(p - V((0, 0, 0.1)), 0.3, 0.03, acero, n=16, m=4)
            disc.cil(p - V((0, 0, 0.1)), p - V((0, 0, 0.14)), 0.22, None, n=16)
    # barra de agarre curvada (en el extremo -X) con puños de goma
    c.tubo([(-1.35, -0.7, Z + 0.1), (-1.45, -0.7, Z + 0.9), (-1.55, -0.6, Z + 1.4), (-1.6, -0.3, Z + 1.5),
            (-1.6, 0.3, Z + 1.5), (-1.55, 0.6, Z + 1.4), (-1.45, 0.7, Z + 0.9), (-1.35, 0.7, Z + 0.1)], 0.045, acero, n=8,
           seg=3)
    for s in (-1, 1):
        c.cil((-1.6, s * 0.12, Z + 1.5), (-1.6, s * 0.4, Z + 1.5), 0.06, goma, n=8)
        c.caja((-1.38, s * 0.7, Z + 0.12), (0.15, 0.12, 0.12), osc, 0.02)
    c.caja((-1.55, 0, Z + 1.42), (0.12, 0.2, 0.1), osc, 0.02)  # mando
    disc.caja((-1.6, 0, Z + 1.42), (0.02, 0.1, 0.04), None)
    # freno de pie: pedal (pieza aparte) y muelle helicoidal real
    pedal.caja((1.25, 0, Z - 0.02), (0.35, 0.4, 0.06), grip, 0.02)
    pedal.caja((1.1, 0, Z - 0.02), (0.15, 0.1, 0.06), osc, 0.01)
    c.cil((1.05, -0.08, Z), (1.05, 0.08, Z), 0.04, acero, n=8)
    pts = [(1.25 + math.cos(t) * 0.06, math.sin(t) * 0.06, Z - 0.08 - t / (math.tau * 5) * 0.25)
           for t in [i * 0.5 for i in range(int(math.tau * 5 / 0.5))]]
    c.tubo(pts, 0.012, muelle, n=4, suave=False)
    # carga: caja metálica, caja de madera y bidón, atados con cinchas
    c.caja((0.2, -0.25, Z + 0.55), (1.2, 0.9, 0.8), caja1, 0.05)
    for sx in (-1, 1):
        for sz in (0, 1):
            c.remache((0.2 + sx * 0.5, -0.71, Z + 0.25 + sz * 0.6), (0, -1, 0), acero, 0.04)
    arq.caja_madera(c, (0.4, 0.45, Z + 0.14), (0.9, 0.55, 0.55), caja2, acero, tablas=2)
    c.torno([(0.0, 0.0), (0.28, 0.0), (0.3, 0.05), (0.3, 0.8), (0.26, 0.85), (0.0, 0.85)], m.mat("pintura", "#2E6A8A",
                                                                                                 desgaste=0.6),
            n=14, c=(-0.85, 0.2, Z + 0.14))
    for x in (-0.15, 0.6):
        c.lamina(lambda u, v, x=x: (x + (v - 0.5) * 0.12,
                                    -0.86 + u * 1.72,
                                    Z + 0.13 + 1.05 * math.sin(u * math.pi) ** 0.6), 12, 1, 0.02, cinta)
        for s in (-1, 1):
            c.caja((x, s * 0.88, Z + 0.15), (0.16, 0.05, 0.12), acero, 0.01)  # carraca
    m.terminar()


MODELOS = {
    "puesto_fruta": puesto_fruta,
    "puesto_comida": puesto_comida,
    "puesto_telas": puesto_telas,
    "mesa_mercado": mesa_mercado,
    "toldo_mercado": toldo_mercado,
    "cartel_holografico": cartel_holografico,
    "caja_envio": caja_envio,
    "barril_metal": barril_metal,
    "carro_carga": carro_carga,
}
