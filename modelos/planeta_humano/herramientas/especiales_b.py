"""Edificios especiales (2): torre de vigilancia, portal, estación de escudos, depósito de agua y comunicaciones."""

import math
import random

import arq
from ph import NEON, V, Modelo, base_eje

ZONA = "especiales"
ROJO = "#FF2A2A"


def _parabolica(c, mat, mat_brazo, centro, rot, radio, profundo=0.3):
    with c.en(centro, rot):
        r = radio
        c.torno([(0.0, 0.0), (r * 0.6, profundo * 0.3), (r * 0.95, profundo * 0.9), (r, profundo), (r * 0.95, profundo),
                 (r * 0.58, profundo * 0.4), (0.0, profundo * 0.12)], mat, n=18)
        c.toro((0, 0, profundo), r, 0.03 * r, mat_brazo, n=18, m=3)
        for k in range(3):
            a = k * math.tau / 3
            c.cil((math.cos(a) * r * 0.85, math.sin(a) * r * 0.85, profundo * 0.85), (0, 0, r * 0.95), 0.012 * r * 2,
                  mat_brazo, n=4)
        c.cil((0, 0, r * 0.9), (0, 0, r * 1.05), 0.06 * r, mat_brazo, n=8)


# ==============================================================================================================
def torre_vigilancia():
    m = Modelo("torre_vigilancia", ZONA, (4, 4, 18), 12000,
               "Torre de vigilancia: fuste de hormigón con troneras cada 4 studs por las que se ve la escalera, "
               "puerta reforzada, plataforma con barandilla de tubo y malla, garita con 4 ventanas, foco giratorio "
               "cyan, antena, campana de alarma de bronce con badajo y sacos de arena.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#9EC6D6", transparencia=0.35)
    foco = m.parte("foco", pivote=(0, 0, 17.0), nota="Foco giratorio: gira sobre el eje vertical del pivote.")
    foco_n = m.parte("foco_neon", tipo="neon", color=NEON, pivote=(0, 0, 17.0), nota="Lente del foco: Neon cyan intenso.")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    puerta = m.parte("puerta", pivote=(-0.55, -1.42, 0.3), nota="Puerta reforzada: gira sobre su bisagra.")
    horm = m.mat("hormigon", "#8E8A82", lluvia=0.6)
    horm2 = m.mat("hormigon", "#7A766E")
    acero = m.mat("metal", "#7A8087")
    osc = m.mat("metal", "#2B2F34", rug=0.5)
    gris = m.mat("pintura", "#4A525C", desgaste=0.5)
    bronce = m.mat("metal", "#A8783A", rug=0.3)
    saco = m.mat("tela", "#9A8456", bump=0.8)
    grip = m.mat("grip", "#6E747A")
    S = 2.8  # lado del fuste
    G = 0.35
    ZP = 14.3  # plataforma

    m.seccion("fuste con troneras")
    c.caja((0, 0, 0.15), (3.6, 3.6, 0.3), horm2, 0.05)
    for cara in range(4):
        # cada cara es un muro con troneras estrechas alternadas en altura
        huecos = [(-0.15, 0.15, z, z + 1.3) for z in ((2.5, 6.5, 10.5) if cara % 2 == 0 else (4.5, 8.5, 12.5))]
        if cara == 0:
            huecos.append((-0.6, 0.6, 0.3, 2.3))
        with c.en((0, 0, 0), (0, 0, cara * 90)):
            arq.muro_huecos(c, -S / 2, S / 2, 0.3, ZP, -S / 2, -S / 2 + G, sorted(huecos), horm)
            for (x0, x1, z0, z1) in huecos:
                if z0 > 1:
                    cr.caja_de((x0, -S / 2 + 0.12, z0), (x1, -S / 2 + 0.2, z1), None)
                    c.caja_de((x0 - 0.08, -S / 2 - 0.05, z0 - 0.1), (x1 + 0.08, -S / 2 + 0.02, z0), horm2, 0.01)
    for z in (4.3, 8.3, 12.3):  # impostas
        c.caja((0, 0, z), (S + 0.16, S + 0.16, 0.18), horm2, 0.03)
    m.seccion("escalera interior")
    # tramos de escalera pegados a las paredes interiores, en espiral cuadrada
    inner = S / 2 - G - 0.35
    z = 0.4
    tramo = 0
    while z < ZP - 0.5:
        lado = tramo % 4
        for k in range(5):
            t = (k + 0.5) / 5
            pos = -inner + t * 2 * inner
            p = {0: (pos, -inner, z), 1: (inner, pos, z), 2: (-pos, inner, z), 3: (-inner, -pos, z)}[lado]
            c.caja(p, (0.5, 0.5, 0.08), grip, 0.0, rot=(0, 0, lado * 90))
            z += 0.2
        tramo += 1
    c.cil((0, 0, 0.3), (0, 0, ZP), 0.12, acero, n=6)
    m.seccion("puerta reforzada")
    c.caja((0, -S / 2 - 0.05, 1.35), (1.6, 0.14, 2.3), osc, 0.03)
    puerta.caja((0, -S / 2 - 0.1, 1.3), (1.1, 0.12, 2.0), acero, 0.03)
    for k in range(3):
        puerta.caja((0, -S / 2 - 0.17, 0.7 + k * 0.6), (1.0, 0.03, 0.08), osc, 0.0)
        for x in (-0.4, 0.4):
            puerta.remache((x, -S / 2 - 0.17, 0.55 + k * 0.6), (0, -1, 0), osc, 0.035)
    puerta.cil((0.35, -S / 2 - 0.17, 1.3), (0.35, -S / 2 - 0.3, 1.3), 0.03, acero, n=6)
    puerta.cil((0.2, -S / 2 - 0.3, 1.3), (0.5, -S / 2 - 0.3, 1.3), 0.03, acero, n=6)
    luces.caja((0, -S / 2 - 0.15, 2.6), (0.5, 0.06, 0.1), None)
    m.seccion("plataforma y barandilla")
    c.caja((0, 0, ZP + 0.12), (4.0, 4.0, 0.25), horm2, 0.05)
    for k in range(4):  # ménsulas
        with c.en((0, 0, 0), (0, 0, k * 90)):
            c.extruir([(0, 0), (0.0, -0.9), (-0.55, 0.0)], 0.2, horm2, c=(0.8, -S / 2, ZP), rot=(90, 0, 90))
    # barandilla: tubo arriba y en medio, postes y malla de varillas
    for k in range(4):
        with c.en((0, 0, ZP + 0.25), (0, 0, k * 90)):
            c.cil((-1.9, -1.9, 1.05), (1.9, -1.9, 1.05), 0.04, acero, n=6)
            c.cil((-1.9, -1.9, 0.5), (1.9, -1.9, 0.5), 0.03, acero, n=6)
            for j in range(5):
                x = -1.9 + j * 0.95
                c.cil((x, -1.9, 0), (x, -1.9, 1.05), 0.04, acero, n=6)
            for j in range(16):  # malla
                x = -1.85 + j * 0.245
                c.cil((x, -1.9, 0.05), (x, -1.9, 0.95), 0.008, acero, n=3)
            c.cil((-1.9, -1.9, 0.25), (1.9, -1.9, 0.25), 0.008, acero, n=3)
            c.cil((-1.9, -1.9, 0.75), (1.9, -1.9, 0.75), 0.008, acero, n=3)
    m.seccion("garita, foco y antena")
    zg = ZP + 0.25
    c.caja_de((-1.0, -1.0, zg), (1.0, 1.0, zg + 0.9), gris, 0.03)
    for k in range(4):
        with c.en((0, 0, 0), (0, 0, k * 90)):
            for x in (-0.95, 0.95):
                c.caja((x, -0.95, zg + 1.45), (0.1, 0.1, 1.1), osc, 0.01)
            cr.caja((0, -0.98, zg + 1.45), (1.8, 0.06, 1.05), None)
    c.caja((0, 0, zg + 2.05), (2.3, 2.3, 0.15), gris, 0.04)
    # foco giratorio sobre el techo (pieza aparte con su lente neón)
    foco.cil((0, 0, zg + 2.12), (0, 0, zg + 2.3), 0.3, osc, n=12)
    for s in (-1, 1):
        foco.caja((s * 0.32, 0, zg + 2.55), (0.06, 0.12, 0.5), osc, 0.01)
    foco.cil((0, 0.25, zg + 2.65), (0, -0.4, zg + 2.65), 0.27, acero, n=14)
    foco.cil((0, -0.4, zg + 2.65), (0, -0.45, zg + 2.65), 0.3, osc, n=14)
    foco_n.cil((0, -0.44, zg + 2.65), (0, -0.47, zg + 2.65), 0.24, None, n=14)
    foco.pivote = V((0, 0, zg + 2.1))
    foco_n.pivote = V((0, 0, zg + 2.1))
    c.cil((0.85, 0.85, zg + 2.12), (0.85, 0.85, 17.95), 0.035, acero, n=5)
    luces.esfera((0.85, 0.85, 17.98), 0.05, None, seg=6, anillos=4)
    m.seccion("campana y sacos")
    bx, by = 1.6, -1.6
    c.cil((bx, by, zg), (bx, by, zg + 1.9), 0.05, acero, n=6)
    c.cil((bx, by, zg + 1.9), (bx - 0.45, by, zg + 1.9), 0.04, acero, n=6)
    with c.en((bx - 0.45, by, zg + 1.85)):
        c.torno([(0.0, 0.0), (0.08, 0.0), (0.12, -0.1), (0.16, -0.32), (0.22, -0.42), (0.2, -0.44), (0.14, -0.34),
                 (0.1, -0.12), (0.0, -0.06)], bronce, n=14)
        c.cil((0, 0, -0.06), (0, 0, -0.35), 0.012, acero, n=4)
        c.esfera((0, 0, -0.38), 0.035, acero, seg=6, anillos=4)
    for k, (x, y, z, a) in enumerate(((-1.3, -1.5, 0.0, 0), (-0.7, -1.55, 0.0, 10), (-1.0, -1.5, 0.28, -5))):
        with c.en((x, y, zg + 0.15 + z), (0, 0, a)):
            c.ico((0, 0, 0), 0.32, saco, sub=2, esc=(1.0, 0.55, 0.42), suave=(0.08, 2.0), semilla=k)
    m.terminar()


# ==============================================================================================================
def portal_espacial():
    m = Modelo("portal_espacial", ZONA, (8, 2, 10), 14000,
               "Portal interdimensional: arco tecnológico con dos pilares de circuitos y tubos de energía, anillo "
               "central de energía cyan intenso, disco de distorsión transparente, plataforma de embarque con rampa, "
               "panel con palanca de activación, cables gruesos al suelo y marcas NO CRUZAR.")
    c = m.parte()
    anillo = m.parte("anillo_neon", tipo="neon", color=NEON, nota="Anillo de energía: Neon cyan, el elemento más brillante "
                                                                   "del planeta (añadir PointLight cyan Brightness 4).")
    circuitos = m.parte("circuitos_neon", tipo="neon", color=NEON, transparencia=0.2)
    disco = m.parte("distorsion_cristal", tipo="cristal", color="#BFF6FF", transparencia=0.6,
                    nota="Disco de distorsión: Glass, Transparency 0,6 (con Reflectance 0,3 parece que refracta).")
    palanca = m.parte("palanca", pivote=(3.7, -1.55, 1.55), nota="Palanca de activación: gira 60° sobre el eje X de Roblox.")
    metal = m.mat("paneles", "#3A424C", tam_panel=(0.8, 1.2), desgaste=0.35)
    acero = m.mat("metal", "#848A91")
    osc = m.mat("metal", "#24282C", rug=0.4)
    cromo = m.mat("cromo", "#D2D6DA")
    goma = m.mat("goma", "#151618")
    grip = m.mat("grip", "#6E747A")
    amarillo = m.mat("pintura", "#E8C21E", desgaste=0.5, aranazos=0.0)
    negro = m.mat("pintura", "#1A1C1E", desgaste=0.3)
    rojo = m.mat("plastico", "#D42A22")
    ZB = 0.6  # plataforma de embarque
    RC, ZC = 2.75, 5.3  # radio y altura del anillo

    m.seccion("plataforma y rampa")
    c.caja((0, 0, ZB / 2), (5.4, 1.8, ZB), metal, 0.05)
    c.caja((0, 0, ZB + 0.01), (5.0, 1.5, 0.02), grip, 0.0)
    with c.en((0, -1.9, ZB / 2), (math.degrees(math.atan2(ZB, 2.0)), 0, 0)):
        c.caja((0, 0, 0), (2.4, 2.05, 0.1), grip, 0.02)
        for s in (-1, 1):
            c.caja((s * 1.22, 0, 0.05), (0.08, 2.05, 0.2), amarillo, 0.01)
    m.seccion("pilares")
    for s in (-1, 1):
        x = s * 3.35
        c.caja((x, 0, 4.6), (1.1, 1.5, 9.2), metal, 0.08)
        c.caja((x, 0, 9.3), (1.3, 1.7, 0.3), osc, 0.05)
        c.caja((x, 0, 0.25), (1.4, 1.8, 0.5), osc, 0.05)
        # trazas de circuito en relieve con nodos luminosos (cara frontal y trasera)
        for cara in (-1, 1):
            y = cara * 0.76
            for k in range(7):
                z = 1.2 + k * 1.1
                circuitos.caja((x - 0.2 * s, y, z), (0.5, 0.02, 0.04), None)
                circuitos.caja((x + 0.1 * s, y, z + 0.25), (0.04, 0.02, 0.5), None)
                c.caja((x - 0.42 * s, y, z), (0.12, 0.05, 0.12), osc, 0.01)
        # tubos de energía verticales con núcleo luminoso y abrazaderas
        for dy in (-0.45, 0.45):
            p0 = V((x + s * 0.62, dy, 0.6))
            p1 = V((x + s * 0.62, dy, 8.9))
            c.cil(p0, p1, 0.11, acero, n=10)
            for k in range(6):
                zz = 1.4 + k * 1.4
                c.cil(p0 + V((0, 0, zz - 0.6 - 0.08)), p0 + V((0, 0, zz - 0.6 + 0.08)), 0.15, osc, n=10)
                circuitos.cil(p0 + V((s * 0.0, 0, zz - 0.6 + 0.12)), p0 + V((0, 0, zz - 0.6 + 0.6)), 0.115, None, n=10)
    m.seccion("anillo central")
    with c.en((0, 0, ZC), (90, 0, 0)):
        c.toro((0, 0, 0), RC, 0.32, metal, n=40, m=10)
        anillo.toro((0, 0, 0), RC - 0.33, 0.12, None, n=40, m=8)
        for k in range(8):  # abrazaderas del anillo
            a = k * math.tau / 8
            c.caja((math.cos(a) * RC, math.sin(a) * RC, 0), (0.5, 0.9, 0.85), osc, 0.06,
                   rot=(0, 0, math.degrees(a)))
        disco.cil((0, 0, -0.04), (0, 0, 0.04), RC - 0.4, None, n=40)
    for s in (-1, 1):  # brazos que unen el anillo a los pilares
        c.caja((s * (RC + 0.45), 0, ZC), (0.9, 0.7, 0.6), osc, 0.05)
        c.cil((s * 2.6, 0, ZC + 1.2), (s * 2.9, 0, ZC + 2.4), 0.1, acero, n=8)
    m.seccion("cables y panel")
    for s in (-1, 1):
        for k, dy in enumerate((-0.5, 0.0, 0.5)):
            p = V((s * 3.9, dy, 0.8 + k * 0.25))
            c.tubo([p, p + V((s * 0.35, 0, -0.35)), p + V((s * 0.5, dy * 0.4, -0.75 - k * 0.1)), V((s * 3.95, dy * 1.6, 0.02))],
                   0.1, goma, n=6, seg=3)
    # panel de control con palanca grande de activación
    pc = V((3.7, -1.3, 0.0))
    c.caja(pc + V((0, 0, 0.6)), (0.8, 0.5, 1.2), osc, 0.05)
    with c.en(pc + V((0, -0.1, 1.25)), (-30, 0, 0)):
        c.caja((0, 0, 0), (0.8, 0.5, 0.12), metal, 0.03)
        circuitos.caja((-0.15, -0.05, 0.07), (0.35, 0.3, 0.01), None)
        for k, col in enumerate((rojo, m.mat("plastico", "#2EA04E"))):
            c.cil((0.25, -0.12 + k * 0.2, 0.06), (0.25, -0.12 + k * 0.2, 0.1), 0.05, col, n=10)
    palanca.caja((3.7, -1.55, 1.45), (0.3, 0.2, 0.12), osc, 0.02)
    palanca.cil((3.7, -1.55, 1.5), (3.7, -1.9, 2.05), 0.05, cromo, n=8)
    palanca.esfera((3.7, -1.92, 2.1), 0.1, rojo, seg=10, anillos=6)
    m.seccion("marcas de seguridad")
    for k in range(10):
        x = -2.4 + k * 0.53
        c.caja((x, -0.92, ZB + 0.012), (0.3, 0.12, 0.02), amarillo if k % 2 else negro, 0.0, rot=(0, 0, 35))
    c.caja((0, -0.78, ZB + 0.012), (4.8, 0.06, 0.02), amarillo, 0.0)
    c.texto("NO CRUZAR", amarillo, alto=0.22, grosor=0.012, c=(0, -0.55, ZB + 0.02), rot=(0, 0, 0), fuente="mono", resol=1)
    m.anclaje("CentroPortal", (0, 0, ZC), "Centro del anillo: aquí va el efecto del portal y la PointLight cyan.")
    m.terminar()


# ==============================================================================================================
def estacion_escudos():
    m = Modelo("estacion_escudos", ZONA, (6, 6, 6), 10000,
               "Generador de escudos planetario: cúpula de paneles hexagonales, rayo de energía cyan vertical desde la "
               "cima, 3 generadores periféricos (esferas sobre pedestales) unidos con cables de energía, panel de "
               "control con medidores y valla perimetral de campo eléctrico.")
    c = m.parte()
    rayo = m.parte("rayo_neon", tipo="neon", color=NEON, nota="Rayo de energía: Neon cyan; se puede alargar hacia arriba.")
    energia = m.parte("energia_neon", tipo="neon", color=NEON, transparencia=0.35, nota="Cables de energía y campo de la "
                                                                                       "valla: Neon translúcido.")
    rnd = random.Random(101)
    base = m.mat("hormigon", "#8E8A84")
    metal = m.mat("paneles", "#4A5560", tam_panel=(0.8, 0.8), desgaste=0.35)
    hexm = m.mat("pintura", "#B8C2CC", desgaste=0.3, c_desgaste="#5A626C")
    acero = m.mat("metal", "#848A91")
    osc = m.mat("metal", "#24282C", rug=0.4)
    blanco = m.mat("plastico", "#F0EEE6")
    tinta = m.mat("pintura", "#16181A", desgaste=0.0)
    R = 1.9
    m.seccion("base y cúpula hexagonal")
    c.cil((0, 0, 0), (0, 0, 0.35), 2.4, base, n=20, b=0.04)
    c.cil((0, 0, 0.35), (0, 0, 0.9), 2.05, metal, n=20)
    c.torno([(0.0, 0.9), (R, 0.9)] + [(R * math.cos(a), 0.9 + R * math.sin(a)) for a in
                                      [math.radians(10 + i * 10) for i in range(9)]] + [(0.0, 0.9 + R)], metal, n=20)
    # paneles hexagonales repartidos por la cúpula (espiral de Fibonacci), orientados a la normal
    npan = 46
    for i in range(npan):
        t = (i + 0.5) / npan
        el = math.asin(t * 0.92)
        az = i * 2.39996
        nrm = V((math.cos(az) * math.cos(el), math.sin(az) * math.cos(el), math.sin(el)))
        p = V((0, 0, 0.9)) + nrm * (R + 0.02)
        c.cil(p, p + nrm * 0.07, 0.28, hexm, n=6, giro=rnd.uniform(0, 1))
    # emisor en la cima y rayo vertical
    c.cil((0, 0, 0.9 + R - 0.05), (0, 0, 0.9 + R + 0.45), 0.42, osc, n=12)
    c.cil((0, 0, 0.9 + R + 0.45), (0, 0, 0.9 + R + 0.6), 0.3, acero, n=12)
    for k in range(4):
        a = k * math.pi / 2
        c.cil((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.9 + R + 0.3), (math.cos(a) * 0.15, math.sin(a) * 0.15, 0.9 + R + 1.1),
              0.04, acero, n=4)
    rayo.cil((0, 0, 0.9 + R + 0.6), (0, 0, 6.0), 0.12, None, n=10)
    rayo.toro((0, 0, 0.9 + R + 1.1), 0.22, 0.03, None, n=12, m=3)
    m.seccion("generadores periféricos")
    for k in range(3):
        a = k * math.tau / 3 + math.pi / 6
        p = V((math.cos(a) * 2.55, math.sin(a) * 2.55, 0))
        c.cil(p, p + V((0, 0, 0.25)), 0.45, base, n=10)
        c.cil(p + V((0, 0, 0.25)), p + V((0, 0, 1.1)), 0.2, osc, n=10, r1=0.14)
        c.esfera(p + V((0, 0, 1.45)), 0.4, acero, seg=14, anillos=8)
        c.toro(p + V((0, 0, 1.45)), 0.41, 0.04, osc, n=14, m=4)
        energia.toro(p + V((0, 0, 1.45)), 0.42, 0.02, None, n=14, m=3, rot=(90, 0, math.degrees(a)))
        # cable de energía hasta la cúpula
        q = V((math.cos(a) * 1.9, math.sin(a) * 1.9, 1.2))
        energia.tubo([p + V((0, 0, 1.2)), p.lerp(q, 0.5) + V((0, 0, 1.55)), q], 0.05, None, n=6, seg=3)
    m.seccion("panel de control")
    pc = V((0.0, -2.75, 0.0))
    c.caja(pc + V((0, 0, 0.55)), (1.2, 0.35, 1.1), osc, 0.04)
    with c.en(pc + V((0, -0.05, 1.12)), (-30, 0, 0)):
        c.caja((0, 0, 0), (1.2, 0.4, 0.08), metal, 0.02)
        for k in range(3):  # medidores de potencia
            x = -0.38 + k * 0.38
            c.cil((x, 0.0, 0.04), (x, 0.0, 0.08), 0.14, acero, n=12)
            c.cil((x, 0.0, 0.08), (x, 0.0, 0.085), 0.12, blanco, n=12)
            c.caja((x + 0.02, 0.02, 0.09), (0.01, 0.09, 0.004), tinta, 0.0, rot=(0, 0, -30 + k * 30))
    m.seccion("valla de campo eléctrico")
    npost = 10
    for k in range(npost):
        a = k * math.tau / npost
        a2 = (k + 1) * math.tau / npost
        p = V((math.cos(a) * 2.95, math.sin(a) * 2.95, 0))
        q = V((math.cos(a2) * 2.95, math.sin(a2) * 2.95, 0))
        c.cil(p, p + V((0, 0, 1.05)), 0.05, osc, n=6)
        c.cil(p + V((0, 0, 1.05)), p + V((0, 0, 1.15)), 0.08, acero, n=6)
        if not (240 < math.degrees((a + a2) / 2) < 300):  # hueco de acceso frente al panel
            for z in (0.35, 0.7, 1.0):
                energia.cil(p + V((0, 0, z)), q + V((0, 0, z)), 0.012, None, n=3)
    m.terminar()


# ==============================================================================================================
def deposito_agua():
    m = Modelo("deposito_agua", ZONA, (4, 4, 12), 8000,
               "Torre de agua: depósito esférico sobre 4 patas en A con arriostramiento, escalerilla con jaula, "
               "tubería principal con dos válvulas de volante en la base, medidor de nivel de cristal, placa AGUA "
               "POTABLE, rebosadero con canaleta y grifo de purga.")
    c = m.parte()
    nivel = m.parte("nivel_cristal", tipo="cristal", color="#D5EEF2", transparencia=0.5)
    blanco = m.mat("pintura", "#D8DEE2", desgaste=0.4, c_desgaste="#7A8087", lluvia=0.6)
    azul = m.mat("pintura", "#2E6A9A", desgaste=0.5)
    acero = m.mat("metal", "#848A91")
    osc = m.mat("metal", "#2B2F34", rug=0.5)
    rojo = m.mat("pintura", "#B8302A", desgaste=0.5)
    horm = m.mat("hormigon", "#8E8A84", manchas=[(1.3, -1.3, 0.0, 0.6, "#2E3A3A", 0.6)])
    agua = m.mat("liquido", "#5AAAC8")
    amarillo = m.mat("pintura", "#E3B22A", desgaste=0.6)
    tinta = m.mat("pintura", "#F2F2F2", desgaste=0.1)
    RT, ZT = 1.75, 9.4
    m.seccion("patas y arriostramiento")
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        pie = V((math.cos(a) * 1.75, math.sin(a) * 1.75, 0.3))
        cabeza = V((math.cos(a) * 1.05, math.sin(a) * 1.05, ZT - 1.4))
        c.caja(pie - V((0, 0, 0.15)), (0.6, 0.6, 0.3), horm, 0.04)
        arq.viga_h(c, pie, cabeza, 0.22, 0.2, azul)
        b = (k + 1) * math.pi / 2 + math.pi / 4
        for z0, z1 in ((0.6, 3.6), (3.6, 6.4)):  # cruces de San Andrés entre patas
            f0 = z0 / (ZT - 1.4)
            f1 = z1 / (ZT - 1.4)
            pa0 = pie.lerp(cabeza, f0)
            pa1 = pie.lerp(cabeza, f1)
            pieb = V((math.cos(b) * 1.75, math.sin(b) * 1.75, 0.3))
            cabb = V((math.cos(b) * 1.05, math.sin(b) * 1.05, ZT - 1.4))
            pb0 = pieb.lerp(cabb, f0)
            pb1 = pieb.lerp(cabb, f1)
            c.cil(pa0, pb1, 0.035, acero, n=4)
            c.cil(pb0, pa1, 0.035, acero, n=4)
    m.seccion("depósito esférico")
    c.esfera((0, 0, ZT), RT, blanco, seg=24, anillos=14)
    c.toro((0, 0, ZT), RT + 0.02, 0.06, azul, n=24, m=4)
    c.cil((0, 0, ZT - RT - 0.05), (0, 0, ZT - RT + 0.35), 1.0, azul, n=16)  # anillo de apoyo
    c.cil((0, 0, ZT + RT - 0.05), (0, 0, ZT + RT + 0.25), 0.35, acero, n=10)  # respiradero
    c.torno([(0.0, ZT + RT + 0.25), (0.55, ZT + RT + 0.22), (0.5, ZT + RT + 0.3), (0.0, ZT + RT + 0.5)], acero, n=10)
    c.texto("AGUA POTABLE", tinta, alto=0.32, grosor=0.02, c=(0, -RT - 0.005, ZT - 0.2), fuente="estrecha", resol=1)
    m.seccion("escalerilla con jaula")
    ex = 1.95
    for s in (-1, 1):
        c.cil((ex, s * 0.22, 0.3), (ex - 0.1, s * 0.22, ZT + 0.6), 0.03, amarillo, n=5)
    k = 0
    z = 0.6
    while z < ZT + 0.4:
        x = ex - 0.1 * (z - 0.3) / ZT
        c.cil((x, -0.22, z), (x, 0.22, z), 0.016, amarillo, n=4)
        z += 0.33
    for j in range(5):
        z = 3.5 + j * 1.3
        x = ex - 0.1 * (z - 0.3) / ZT
        c.tubo([(x, -0.25, z), (x + 0.4, -0.38, z), (x + 0.7, -0.2, z), (x + 0.7, 0.2, z), (x + 0.4, 0.38, z), (x, 0.25, z)],
               0.02, amarillo, n=4, suave=False)
    for dy in (-0.38, 0.0, 0.38):
        c.cil((ex + (0.3 if dy else 0.6), dy, 3.5), (ex + (0.3 if dy else 0.6), dy, 8.7), 0.018, amarillo, n=4)
    m.seccion("tuberías, válvulas y medidor")
    c.cil((0, 0, ZT - RT + 0.05), (0, 0, 0.9), 0.16, azul, n=10)
    c.tubo([(0, 0, 0.9), (0, 0, 0.55), (0.0, -0.35, 0.45), (0.0, -1.9, 0.45)], 0.16, azul, n=10, seg=2)
    for k, y in enumerate((-0.9, -1.5)):  # dos válvulas de volante
        c.cil((0, y - 0.12, 0.45), (0, y + 0.12, 0.45), 0.24, osc, n=12)
        c.cil((0, y, 0.6), (0, y, 0.85), 0.03, acero, n=6)
        c.toro((0, y, 0.88), 0.2, 0.025, rojo, n=12, m=4)
        for j in range(4):
            a = j * math.pi / 2
            c.cil((0, y, 0.88), (math.cos(a) * 0.2, y + math.sin(a) * 0.2, 0.88), 0.015, rojo, n=4)
    # medidor de nivel: tubo de cristal por fuera del depósito con el agua dentro
    nx, ny = -RT - 0.15, 0.0
    for z in (ZT - 1.1, ZT + 1.1):
        c.cil((-RT * 0.85, 0, z), (nx, ny, z), 0.04, acero, n=6)
    nivel.cil((nx, ny, ZT - 1.1), (nx, ny, ZT + 1.1), 0.07, None, n=10)
    c.cil((nx, ny, ZT - 1.08), (nx, ny, ZT + 0.45), 0.05, agua, n=8)
    for k in range(5):
        c.caja((nx - 0.09, ny, ZT - 0.9 + k * 0.45), (0.05, 0.01, 0.015), osc, 0.0)
    # rebosadero con canaleta y grifo de purga
    c.tubo([(RT * 0.7, -RT * 0.6, ZT + 0.3), (1.6, -1.3, ZT - 0.2), (1.6, -1.3, 0.7), (1.6, -1.6, 0.35)], 0.08, acero, n=6,
           seg=2)
    c.caja((1.6, -1.95, 0.08), (0.35, 0.9, 0.16), horm, 0.02)
    c.caja((1.6, -1.95, 0.15), (0.25, 0.8, 0.02), m.mat("liquido", "#3A5A6A"), 0.0)
    c.cil((0, -0.3, 0.45), (0.3, -0.3, 0.25), 0.04, acero, n=6)  # grifo de purga
    c.cil((0.3, -0.3, 0.25), (0.3, -0.3, 0.1), 0.035, acero, n=6)
    c.caja((0.3, -0.3, 0.34), (0.15, 0.03, 0.03), rojo, 0.005)
    c.caja((0, 0, 0.15), (2.4, 2.4, 0.3), horm, 0.04)
    m.terminar()


# ==============================================================================================================
def estacion_comunicaciones():
    m = Modelo("estacion_comunicaciones", ZONA, (6, 6, 10), 10000,
               "Estación de comunicaciones: parabólica grande de 3 studs sobre mástil giratorio, parabólica secundaria, "
               "tres antenas omnidireccionales, cabina de equipos con puerta y ventana, cables, luz estroboscópica roja "
               "en la cima y panel solar.")
    c = m.parte()
    plato = m.parte("parabolica", pivote=(1.2, 1.2, 6.2), nota="Parabólica grande: gira sobre el eje vertical del mástil.")
    roja = m.parte("estrobo_neon", tipo="neon", color=ROJO, nota="Luz estroboscópica de aviso: Neon rojo (parpadeo).")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    cr = m.parte("cristal", tipo="cristal", color="#9EC6D6", transparencia=0.35)
    puerta = m.parte("puerta", pivote=(-2.15, -1.62, 0.3), nota="Puerta de la cabina: gira sobre su bisagra.")
    cabina = m.mat("paneles", "#C8CDD1", tam_panel=(1.0, 1.2), desgaste=0.4)
    gris = m.mat("pintura", "#4A525C", desgaste=0.45)
    blanco = m.mat("pintura", "#E6E8EA", desgaste=0.3, c_desgaste="#8A9097")
    acero = m.mat("metal", "#848A91")
    osc = m.mat("metal", "#24282C", rug=0.45)
    horm = m.mat("hormigon", "#8E8A84")
    goma = m.mat("goma", "#151618")
    celda = m.mat("metal", "#1E2E5A", rug=0.15)
    m.seccion("cabina de equipos")
    c.caja((0, 0, 0.15), (6.0, 6.0, 0.3), horm, 0.05)
    cx0, cx1, cy0, cy1 = -2.6, 0.4, -1.5, 1.5
    arq.muro_huecos(c, cx0, cx1, 0.3, 2.9, cy0 - 0.15, cy0, [(-2.1, -1.1, 0.3, 2.3), (-0.6, 0.1, 1.3, 2.2)], cabina)
    c.caja_de((cx0, cy1, 0.3), (cx1, cy1 + 0.15, 2.9), cabina)
    for x in (cx0 - 0.15, cx1):
        c.caja_de((x, cy0 - 0.15, 0.3), (x + 0.15, cy1 + 0.15, 2.9), cabina)
    c.caja_de((cx0 - 0.35, cy0 - 0.4, 2.9), (cx1 + 0.35, cy1 + 0.35, 3.15), gris, 0.04)
    cr.caja_de((-0.6, cy0 - 0.1, 1.3), (0.1, cy0 - 0.05, 2.2), None)
    c.caja_de((-0.68, cy0 - 0.2, 1.22), (0.18, cy0, 1.3), gris, 0.01)
    puerta.caja_de((-2.1, cy0 - 0.22, 0.32), (-1.12, cy0 - 0.12, 2.28), gris, 0.02)
    puerta.cil((-1.3, cy0 - 0.25, 1.3), (-1.3, cy0 - 0.33, 1.3), 0.03, acero, n=6)
    luces.caja((-1.6, cy0 - 0.2, 2.5), (0.4, 0.05, 0.08), None)
    for k in range(3):  # rejillas de ventilación
        c.caja((cx0 - 0.17, -0.6 + k * 0.6, 1.9), (0.04, 0.45, 0.3), osc, 0.01)
    m.seccion("mástil y parabólica grande")
    mx, my = 1.2, 1.2
    # torre de celosía de 3 patas que se estrecha hacia arriba, con anillos y cruces de San Andrés
    c.cil((mx, my, 0.3), (mx, my, 0.45), 0.85, horm, n=10)
    secc = [0.45, 1.6, 2.75, 3.9, 5.05, 6.2]

    def pata(k, z):
        r = 0.62 - 0.36 * (z - 0.45) / 5.75
        a = math.radians(90 + k * 120)
        return V((mx + math.cos(a) * r, my + math.sin(a) * r, z))
    for k in range(3):
        c.cil(pata(k, 0.45), pata(k, 6.2), 0.045, gris, n=6)
        c.caja(pata(k, 0.47), (0.22, 0.22, 0.04), acero)  # placa de pie
        for i in range(len(secc) - 1):
            a0, a1 = pata(k, secc[i]), pata((k + 1) % 3, secc[i])
            b0, b1 = pata(k, secc[i + 1]), pata((k + 1) % 3, secc[i + 1])
            c.cil(a0, b1, 0.016, acero, n=4)
            c.cil(a1, b0, 0.016, acero, n=4)
    for z in secc[1:]:
        for k in range(3):
            c.cil(pata(k, z), pata((k + 1) % 3, z), 0.022, gris, n=4)
    c.cil((mx, my, 5.9), (mx, my, 6.2), 0.3, gris, n=10)  # plataforma del rotor
    for i in range(18):  # escalerilla de peldaños por dentro de una pata
        z = 0.7 + i * 0.3
        p = pata(0, z)
        c.cil(p + V((-0.12, -0.06, 0)), p + V((0.12, -0.06, 0)), 0.012, acero, n=4)
    plato.cil((mx, my, 6.2), (mx, my, 6.45), 0.32, osc, n=12)  # cabeza giratoria
    plato.caja((mx, my, 6.7), (0.3, 0.5, 0.5), osc, 0.04)
    _parabolica(plato, blanco, acero, V((mx, my - 0.3, 6.9)), (100, 0, 25), 1.5, profundo=0.45)
    m.seccion("parabólica secundaria y antenas")
    _parabolica(c, blanco, acero, V((-1.9, 0.8, 3.75)), (60, 0, 200), 0.6, profundo=0.2)
    c.cil((-1.9, 0.8, 3.15), (-1.9, 0.8, 3.55), 0.06, acero, n=6)
    for k in range(3):  # antenas omnidireccionales
        a = k * math.tau / 3
        p = V((-0.4 + math.cos(a) * 0.35, 0.3 + math.sin(a) * 0.35, 3.15))
        c.cil(p, p + V((0, 0, 0.25)), 0.06, osc, n=6)
        c.cil(p + V((0, 0, 0.25)), p + V((0, 0, 2.0)), 0.025, acero, n=5)
        c.esfera(p + V((0, 0, 2.03)), 0.04, osc, seg=6, anillos=4)
    # estroboscópica roja en lo alto del mástil (por encima del plato)
    c.cil((mx + 0.0, my + 0.4, 6.45), (mx, my + 0.4, 9.6), 0.04, acero, n=5)
    roja.esfera((mx, my + 0.4, 9.7), 0.1, None, seg=10, anillos=6)
    c.cil((mx, my + 0.4, 9.56), (mx, my + 0.4, 9.62), 0.08, osc, n=8)
    m.seccion("cables y panel solar")
    for k, (p0, p1) in enumerate((((mx, my, 6.0), (cx1, 0.8, 2.6)), ((-0.4, 0.3, 3.3), (-0.4, 0.3, 3.15)),
                                  ((-1.9, 0.8, 3.2), (-1.9, 0.6, 3.15)))):
        if k == 0:
            c.tubo([p0, (mx - 0.2, my - 0.2, 4.0), (cx1 + 0.3, 0.9, 2.9), p1], 0.04, goma, n=5, seg=3)
    # panel solar sobre bastidor inclinado
    sx, sy = 1.5, -1.6
    for x in (sx - 1.1, sx + 1.1):
        c.cil((x, sy + 0.4, 0.3), (x, sy + 0.4, 1.7), 0.05, acero, n=6)
        c.cil((x, sy - 0.5, 0.3), (x, sy - 0.5, 0.8), 0.05, acero, n=6)
    with c.en((sx, sy, 1.3), (-32, 0, 0)):
        c.caja((0, 0, 0), (2.6, 1.6, 0.08), acero, 0.02)
        for i in range(6):
            for j in range(4):
                c.caja((-1.08 + i * 0.43, -0.6 + j * 0.4, 0.045), (0.4, 0.37, 0.02), celda, 0.0)
    c.tubo([(sx - 1.1, sy + 0.4, 1.0), (cx1 + 0.2, -0.8, 1.0)], 0.03, goma, n=4, suave=False)
    m.seccion("bandeja de cables, climatizador y valla")
    for y in (0.65, 0.95):  # bandeja de escalera de la torre a la cabina
        c.cil((cx1 + 0.15, y, 2.6), (mx - 0.35, y, 2.6), 0.02, acero, n=4)
    for i in range(5):
        x = cx1 + 0.2 + i * (mx - 0.6 - cx1) / 4
        c.cil((x, 0.65, 2.6), (x, 0.95, 2.6), 0.012, acero, n=4)
    c.tubo([(cx1 + 0.15, 0.8, 2.64), (mx - 0.4, 0.8, 2.64), (mx - 0.25, 0.9, 3.4), (mx - 0.2, 0.95, 5.9)], 0.035, goma,
           n=4, seg=2)
    c.caja((cx0 - 0.45, -0.2, 1.0), (0.5, 1.2, 0.9), m.mat("paneles", "#B8BEC4", tam_panel=(0.6, 0.45)), 0.03)
    c.cil((cx0 - 0.71, -0.2, 1.05), (cx0 - 0.73, -0.2, 1.05), 0.34, osc, n=12)  # ventilador del climatizador
    for d in (-1, 1):
        c.cil((cx0 - 0.74, -0.2 - 0.3 * d, 1.05), (cx0 - 0.74, -0.2 + 0.3 * d, 1.05), 0.012, acero, n=4)
    # valla perimetral de malla con puerta delante de la cabina
    L = 2.85
    esquinas = [(-L, -L), (L, -L), (L, L), (-L, L)]
    for i in range(4):
        a, b = V((*esquinas[i], 0.3)), V((*esquinas[(i + 1) % 4], 0.3))
        n = 4
        for j in range(n):
            p = a.lerp(b, j / n)
            if i == 0 and -2.4 < p.x < -0.8:
                continue
            c.cil(p, p + V((0, 0, 1.6)), 0.035, acero, n=6)
        tramos = [(a, b)] if i else [(a, V((-2.3, -L, 0.3))), (V((-0.9, -L, 0.3)), b)]
        for p0, p1 in tramos:
            for z in (0.4, 1.0, 1.6):
                c.cil(p0 + V((0, 0, z - 0.3)), p1 + V((0, 0, z - 0.3)), 0.014, acero, n=4)
            for z in (0.7, 1.3):
                c.cil(p0 + V((0, 0, z - 0.3)), p1 + V((0, 0, z - 0.3)), 0.008, acero, n=3)
            # alambre de espino en zigzag sobre la valla
            d = p1 - p0
            k = max(2, int(d.length / 0.3))
            c.tubo([p0.lerp(p1, j / k) + V((0, 0, 1.38 + 0.06 * (j % 2))) for j in range(k + 1)], 0.008, acero, n=3,
                   suave=False)
    for x in (-2.3, -0.9):  # puerta de la valla (abierta hacia dentro)
        c.cil((x, -L, 0.3), (x, -L, 1.95), 0.05, gris, n=6)
    c.caja((-1.6, -L + 0.02, 1.0), (1.3, 0.04, 1.3), m.mat("pintura", "#4A525C", desgaste=0.5), 0.02, rot=(0, 0, 25))
    m.terminar()


MODELOS = {
    "torre_vigilancia": torre_vigilancia,
    "portal_espacial": portal_espacial,
    "estacion_escudos": estacion_escudos,
    "deposito_agua": deposito_agua,
    "estacion_comunicaciones": estacion_comunicaciones,
}
