"""Zona comercial (3): astillero de piezas, banco, restaurante, cantina y clínica."""

import math

import arq
from ph import NEON, NEON_CLINICA, V, Modelo

ZONA = "comercial"


def _silla_terraza(c, x, y, ang, pata, asiento):
    """Silla de terraza: patas de tubo curvado y asiento de plástico moldeado (lámina con grosor)."""
    with c.en((x, y, 0), (0, 0, ang)):
        for s in (-1, 1):
            c.tubo([(s * 0.38, -0.36, 0.0), (s * 0.36, -0.3, 0.95), (s * 0.36, 0.3, 0.95), (s * 0.38, 0.38, 0.0)], 0.035,
                   pata, n=6, seg=3)
            c.cil((s * 0.38, -0.36, 0.0), (s * 0.38, -0.36, 0.03), 0.045, pata, n=6)
            c.cil((s * 0.38, 0.38, 0.0), (s * 0.38, 0.38, 0.03), 0.045, pata, n=6)
        c.caja((0, 0, 0.92), (0.74, 0.05, 0.05), pata, 0.01)
        # asiento y respaldo de una pieza: superficie curvada
        def f(u, v):
            yy = -0.36 + u * 0.95
            if yy < 0.35:
                z = 1.0 + 0.04 * math.sin((yy + 0.36) / 0.7 * math.pi)
            else:
                t = (yy - 0.35) / 0.24
                yy = 0.35 + t * 0.08
                z = 1.0 + t * 0.95
            x_ = (v - 0.5) * 0.8 * (1.0 - 0.1 * max(0.0, yy - 0.35))
            return (x_, yy, z)
        c.lamina(f, 10, 4, 0.06, asiento)


# ==============================================================================================================
def tienda_naves():
    m = Modelo("tienda_naves", ZONA, (14, 12, 8), 14000,
               "Astillero Orbital, concesionario de piezas de nave: pórtico de acero con bóveda, ventanal, maqueta "
               "de nave colgada, motores en pedestales, puerta doble ancha con rampa y banderines.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#A3CFE0", transparencia=0.35)
    neon = m.parte("cartel_neon", tipo="neon", color=NEON)
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    cab = m.parte("maqueta_cristal", tipo="cristal", color="#2C4A66", transparencia=0.3)

    blanco = m.mat("paneles", "#C9CDD1", tam_panel=(2.5, 1.6), desgaste=0.4, c_desgaste="#80868C")
    gris = m.mat("pintura", "#3E4650", desgaste=0.45)
    naranja = m.mat("pintura", "#E07A1F", desgaste=0.6)
    acero = m.mat("metal", "#848A91")
    osc = m.mat("metal", "#2D3238", rug=0.5)
    cromo = m.mat("cromo", "#CDD2D8")
    horm = m.mat("hormigon", "#A09B92", manchas=[(4.6, -4.8, 0.2, 1.3, "#14110e", 0.6)])
    suelo_i = m.mat("grip", "#5A6068")
    goma = m.mat("goma", "#1C1D20")
    tela_c = m.mat("tela", "#22B8C8", suciedad=0.1)
    tela_n = m.mat("tela", "#E58A2A", suciedad=0.1)
    tela_b = m.mat("tela", "#E8E6E0", suciedad=0.1)
    nave_b = m.mat("pintura", "#E4E6E8", desgaste=0.3, c_desgaste="#8C9298")
    nave_r = m.mat("pintura", "#D9662A", desgaste=0.4)
    tobera = m.mat("metal", "#5B4E46", rug=0.38, hollin=(0.0, 0.0))

    X0, X1, YF, YB, Z0, ZT = -6.2, 6.2, -3.6, 5.4, 0.5, 6.4

    m.seccion("cuerpo")
    c.caja_de((X0 - 0.2, YF - 0.2, 0), (X1 + 0.2, YB + 0.2, Z0), horm, 0.05)
    VEN = (-5.6, 2.2, 0.9, 5.7)
    PUE = (2.8, 5.8, Z0, 5.7)
    arq.muro_huecos(c, X0, X1, Z0, ZT, YF, YF + 0.35, [(VEN[0], VEN[1], Z0 + 0.0, VEN[3]), PUE], blanco)
    c.caja_de((VEN[0], YF, Z0), (VEN[1], YF + 0.35, VEN[2]), gris, 0.03)
    for x in (X0, X1 - 0.35):
        c.caja_de((x, YF + 0.35, Z0), (x + 0.35, YB - 0.35, ZT), blanco)
    c.caja_de((X0, YB - 0.35, Z0), (X1, YB, ZT), blanco)
    # pórtico: pilares IPE en la fachada y arcos de la bóveda
    for x in (X0 - 0.1, VEN[1] + 0.3, X1 + 0.1):
        arq.viga_h(c, (x, YF - 0.2, 0.1), (x, YF - 0.2, ZT + 0.2), 0.4, 0.34, gris)
    # bóveda de chapa (lámina curvada a lo largo de Y)
    R = (X1 - X0) / 2 + 0.4
    flecha = 1.6
    def boveda(u, v):
        x = X0 - 0.4 + u * (X1 - X0 + 0.8)
        t = (x / R)
        return (x, YF - 0.5 + v * (YB - YF + 0.9), ZT + flecha * (1 - t * t))
    c.lamina(boveda, 18, 1, 0.12, m.mat("pintura", "#8A939C", desgaste=0.35, lluvia=0.5))
    for k in range(5):
        y = YF - 0.3 + k * (YB - YF + 0.5) / 4
        pts = [(X0 - 0.4 + i * (X1 - X0 + 0.8) / 12, y, ZT + 0.08 + flecha * (1 - ((X0 - 0.4 + i * (X1 - X0 + 0.8) / 12) / R) ** 2))
               for i in range(13)]
        c.tubo(pts, 0.08, gris, n=6, suave=False)
    # frente de la bóveda (tímpano) cerrado
    c.extruir([(X0, ZT)] + [(X0 + i * (X1 - X0) / 10, ZT + flecha * (1 - ((X0 + i * (X1 - X0) / 10) / R) ** 2) - 0.05)
                            for i in range(11)] + [(X1, ZT)], 0.3, blanco, c=(0, YF + 0.15, 0), rot=(90, 0, 0))
    c.extruir([(X0, ZT)] + [(X0 + i * (X1 - X0) / 10, ZT + flecha * (1 - ((X0 + i * (X1 - X0) / 10) / R) ** 2) - 0.05)
                            for i in range(11)] + [(X1, ZT)], 0.3, blanco, c=(0, YB - 0.15, 0), rot=(90, 0, 0))

    m.seccion("ventanal")
    x0, x1, z0, z1 = VEN
    arq.marco(c, x0, x1, z0, z1, YF, 0.15, 0.15, gris)
    for k in range(1, 4):
        x = x0 + k * (x1 - x0) / 4
        c.caja_de((x - 0.05, YF - 0.05, z0), (x + 0.05, YF + 0.12, z1), gris, 0.01)
    c.caja_de((x0, YF - 0.05, 4.2), (x1, YF + 0.12, 4.3), gris, 0.01)
    cr.caja_de((x0, YF + 0.05, z0), (x1, YF + 0.17, z1), None)
    # interior: suelo, fondo con logotipo y luces
    c.caja_de((X0 + 0.35, YF + 0.35, Z0), (X1 - 0.35, YB - 0.35, Z0 + 0.03), suelo_i)
    c.caja_de((X0 + 0.35, YF + 0.35, ZT - 0.05), (X1 - 0.35, YB - 0.35, ZT), gris)  # techo interior
    for k in range(3):
        luces.caja((-2.0, YF + 1.5 + k * 1.6, ZT - 0.1), (6.0, 0.15, 0.06), None)

    m.seccion("maqueta de nave")
    mx, my, mz = -1.7, YF + 2.8, 4.4
    with c.en((mx, my, mz), (0, 6, 30)):
        # fuselaje: loft de secciones redondeadas
        secs = [(-1.8, 0.05, 0.05), (-1.4, 0.32, 0.28), (-0.4, 0.42, 0.38), (0.6, 0.4, 0.34), (1.4, 0.3, 0.26)]
        an = []
        for x, w, h in secs:
            an.append([(x, math.cos(a) * w, math.sin(a) * h) for a in [i * math.tau / 10 for i in range(10)]])
        c.loft(an, nave_b)
        # alas en flecha (perfil extruido con grosor)
        for s in (-1, 1):
            c.extruir([(-0.6, s * 0.3), (0.8, s * 0.3), (1.25, s * 1.75), (0.85, s * 1.8)], 0.07, nave_b, c=(0, 0, -0.05))
            c.caja((1.0, s * 1.6, -0.05), (0.5, 0.12, 0.09), nave_r, 0.02)
            c.cil((-0.3, s * 0.9, -0.12), (0.9, s * 0.9, -0.12), 0.07, osc, n=8)  # cañones
        # motores
        for s in (-1, 1):
            c.cil((0.7, s * 0.42, 0.0), (1.75, s * 0.42, 0.0), 0.2, nave_b, n=12)
            c.cil((1.75, s * 0.42, 0.0), (1.95, s * 0.42, 0.0), 0.2, tobera, n=12, r1=0.16)
            luces.cil((1.94, s * 0.42, 0.0), (1.96, s * 0.42, 0.0), 0.13, None, n=10)
        c.extruir([(0.9, 0), (1.5, 0), (1.6, 0.7), (1.3, 0.72)], 0.06, nave_r, rot=(90, 0, 0), c=(0, 0, 0.1))  # deriva
        c.caja((-0.2, 0, 0.36), (1.4, 0.05, 0.06), nave_r, 0.01)
        cab.esfera((-0.85, 0, 0.22), 0.4, None, seg=12, anillos=6, esc=(1.4, 0.75, 0.55))
        # cables de suspensión (tres puntos)
    for (dx, dy) in ((-1.2, -0.7), (1.1, 0.6), (-1.0, 0.8)):
        p0 = V((mx + dx * 0.9, my + dy * 0.6, mz + 0.35))
        c.cil(p0, (p0.x, p0.y, ZT - 0.05), 0.012, acero, n=4)
        c.cil((p0.x, p0.y, ZT - 0.12), (p0.x, p0.y, ZT - 0.04), 0.06, osc, n=6)

    m.seccion("motores en pedestal")
    def pedestal(px, py, h):
        c.cil((px, py, Z0), (px, py, Z0 + h), 0.55, gris, n=12, b=0.03)
        c.cil((px, py, Z0 + h), (px, py, Z0 + h + 0.06), 0.62, cromo, n=12)
        luces.cil((px, py, Z0 + 0.15), (px, py, Z0 + 0.2), 0.57, None, n=12)
    pedestal(-4.3, YF + 1.6, 0.9)
    with c.en((-4.3, YF + 1.6, Z0 + 0.96 + 0.75), (90, 0, 25)):
        c.torno([(0.0, -0.75), (0.32, -0.75), (0.34, -0.55), (0.62, 0.3), (0.7, 0.75), (0.62, 0.75), (0.54, 0.32),
                 (0.26, -0.5), (0.0, -0.5)], tobera, n=18)
        c.toro((0, 0, -0.55), 0.36, 0.05, acero, n=14, m=5)
        for k in range(8):
            a = k * math.tau / 8
            c.caja((math.cos(a) * 0.5, math.sin(a) * 0.5, 0.05), (0.06, 0.04, 0.9), acero, 0.01,
                   rot=(0, 0, math.degrees(a)))
    pedestal(0.6, YF + 1.7, 0.7)
    with c.en((0.6, YF + 1.7, Z0 + 0.76 + 0.7), (90, 0, -20)):
        c.cil((0, 0, -0.45), (0, 0, 0.45), 0.66, nave_b, n=18)
        c.cil((0, 0, -0.47), (0, 0, -0.45), 0.6, osc, n=18)
        c.cil((0, 0, -0.5), (0, 0, 0.0), 0.16, acero, n=10)
        for k in range(12):
            a = k * math.tau / 12
            c.caja((math.cos(a) * 0.38, math.sin(a) * 0.38, -0.47), (0.42, 0.1, 0.03), acero, 0.005,
                   rot=(0, 25, math.degrees(a)))
        c.toro((0, 0, 0.46), 0.66, 0.06, naranja, n=18, m=5)

    m.seccion("puerta doble y rampa")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.2, 0.2, gris, abajo=False)
    c.caja_de((px0, YF - 0.4, pz1 + 0.2), (px1, YF - 0.2, pz1 + 0.35), acero, 0.02)  # raíl
    for lado, (hx0, s) in {"izq": (px0, 1), "der": (px1, -1)}.items():
        w = (px1 - px0) / 2
        pv = (hx0 + s * w / 2, YF - 0.3, pz0)
        h = m.parte(f"puerta_{lado}", pivote=pv, nota=f"Hoja corredera: abrir {w - 0.1:.2f} studs hacia fuera del hueco.")
        hc = m.parte(f"puerta_{lado}_cristal", tipo="cristal", color="#A3CFE0", pivote=pv, transparencia=0.4)
        xa, xb = sorted((hx0, hx0 + s * w))
        h.caja_de((xa, YF - 0.36, pz0 + 0.02), (xb, YF - 0.24, pz0 + 0.5), gris, 0.02)
        h.caja_de((xa, YF - 0.36, pz1 - 0.35), (xb, YF - 0.24, pz1 - 0.02), gris, 0.02)
        h.caja_de((xa, YF - 0.36, pz0 + 0.5), (xa + 0.15, YF - 0.24, pz1 - 0.35), gris, 0.02)
        h.caja_de((xb - 0.15, YF - 0.36, pz0 + 0.5), (xb, YF - 0.24, pz1 - 0.35), gris, 0.02)
        h.caja_de((xa + 0.15, YF - 0.38, pz0 + 0.25), (xb - 0.15, YF - 0.36, pz0 + 0.42), naranja, 0.003)
        xt = hx0 + s * (w - 0.3)
        h.cil((xt, YF - 0.48, pz0 + 1.5), (xt, YF - 0.48, pz0 + 3.5), 0.04, cromo, n=8)
        for zz in (pz0 + 1.6, pz0 + 3.4):
            h.cil((xt, YF - 0.48, zz), (xt, YF - 0.36, zz), 0.025, cromo, n=6)
        hc.caja_de((xa + 0.15, YF - 0.33, pz0 + 0.5), (xb - 0.15, YF - 0.27, pz1 - 0.35), None)
    # rampa de acceso de chapa antideslizante con bordillos y barandilla
    with c.en(((px0 + px1) / 2, YF - 1.3, Z0 / 2), (math.degrees(math.atan2(Z0, 2.4)), 0, 0)):
        c.caja((0, 0, -0.05), (px1 - px0, 2.5, 0.1), suelo_i, 0.02)
        for s in (-1, 1):
            c.caja((s * (px1 - px0) / 2, 0, 0.02), (0.15, 2.5, 0.2), naranja, 0.02)
    c.caja_de((px0 - 0.1, YF - 2.6, -0.02), (px1 + 0.1, YF - 0.05, 0.03), horm, 0.01)
    for s in (px0 - 0.15, px1 + 0.15):
        arq.barandilla(c, [(s, YF - 2.4, 0.02), (s, YF - 0.25, Z0)], 1.0, cromo, r=0.04, n=6)

    m.seccion("cartel")
    c.caja((0.0, YF - 0.25, 7.1), (10.6, 0.14, 1.1), gris, 0.04)
    neon.texto("ASTILLERO ORBITAL", None, alto=0.62, grosor=0.07, c=(0.0, YF - 0.36, 7.12), fuente="estrecha")
    neon.texto("Piezas y Reparaciones", None, alto=0.26, grosor=0.05, c=(0.0, YF - 0.36, 6.72), fuente="normal")
    c.caja((0, YF - 0.33, 6.62), (10.2, 0.04, 0.03), naranja, 0.0)

    m.seccion("banderines")
    poste = V((X0 - 0.5, YF - 2.4, 0))
    c.cil(poste, poste + V((0, 0, 7.0)), 0.09, gris, n=8)
    c.cil(poste, poste + V((0, 0, 0.2)), 0.3, horm, n=8)
    c.esfera(poste + V((0, 0, 7.05)), 0.12, cromo, seg=8, anillos=5)
    a = poste + V((0, 0, 6.8))
    b = V((X1 - 0.6, YF - 0.25, 7.7))
    pts = []
    N = 16
    for i in range(N + 1):
        t = i / N
        p = a.lerp(b, t)
        p.z -= 1.2 * 4 * t * (1 - t)
        pts.append(p)
    c.tubo(pts, 0.015, acero, n=4, suave=False)
    telas = [tela_c, tela_n, tela_b]
    for i in range(1, N, 1):
        p, q = pts[i], pts[i + 1] if i + 1 <= N else pts[i]
        d = (pts[i + 1] - pts[i - 1]).normalized()
        ang = math.degrees(math.atan2(d.y, d.x))
        with c.en(p, (0, 0, ang)):
            c.extruir([(-0.22, 0), (0.22, 0), (0.0, -0.6)], 0.02, telas[i % 3], rot=(90, 0, 0))

    m.seccion("detalles")
    arq.foco_pared(c, luces, (X1 - 0.2, YF - 0.2, 5.0), gris, acero)
    c.caja((X0 + 1.2, YB + 0.2, 1.4), (1.6, 0.4, 1.4), acero, 0.05)
    c.tubo([(X0 + 1.2, YB + 0.2, 2.1), (X0 + 1.2, YB + 0.1, 4.5)], 0.05, osc, n=6, suave=False)
    m.terminar()


# ==============================================================================================================
def banco_galactico():
    m = Modelo("banco_galactico", ZONA, (12, 10, 8), 14000,
               "Banco Colonial: fachada blindada de paneles gruesos y pilastras de piedra, cajero empotrado con "
               "teclado de botones 3D, puerta reforzada con dos cerrojos, placa de latón y escalinata.")
    c = m.parte()
    neon = m.parte("cajero_neon", tipo="neon", color=NEON)
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    cr = m.parte("cristal", tipo="cristal", color="#8FB4C6", transparencia=0.3)

    blind = m.mat("paneles", "#4A5560", tam_panel=(1.2, 1.2), desgaste=0.35, bump=0.5)
    piedra = m.mat("piedra", "#B7AF9F")
    marmol = m.mat("piedra", "#D2CCC0", rug=0.55, escala=0.6)
    acero = m.mat("metal", "#80868D")
    osc = m.mat("metal", "#2B3036", rug=0.45)
    cromo = m.mat("cromo", "#D5DADF")
    laton = m.mat("metal", "#C99A3C", rug=0.25)
    plas = m.mat("plastico", "#2A2E33")
    tecla = m.mat("plastico", "#B9BEC4")
    rojo = m.mat("plastico", "#C23A2E")
    verde = m.mat("plastico", "#2FA052")
    amar = m.mat("plastico", "#D8B02A")

    X0, X1, YF, YB, ZT = -5.6, 5.6, -2.8, 4.8, 7.2
    ZS = 0.9  # suelo tras la escalinata

    m.seccion("escalinata y base")
    c.caja_de((X0 - 0.3, YF - 0.2, 0), (X1 + 0.3, YB + 0.2, ZS), piedra, 0.05)
    arq.escalones(c, -3.0, 3.0, YF - 2.0, 0.0, 3, 0.62, ZS / 3, marmol, mat_borde=acero, sentido=1)
    for x in (-3.0, 3.0):
        c.caja_de((x - 0.35 if x < 0 else x, YF - 2.05, 0), (x if x < 0 else x + 0.35, YF + 0.05, ZS + 0.35), piedra,
                  0.05)
        arq.barandilla(c, [(x + (-0.17 if x < 0 else 0.17), YF - 1.9, ZS + 0.35 - 0.2),
                           (x + (-0.17 if x < 0 else 0.17), YF - 0.2, ZS + 0.35)], 1.0, cromo, r=0.05, n=8)
    # pasamanos central pulido
    arq.barandilla(c, [(0, YF - 1.95, 0.0), (0, YF - 0.65, ZS * 0.66), (0, YF - 0.1, ZS)], 1.05, cromo, r=0.05, n=8)

    m.seccion("muros blindados")
    PUE = (-1.4, 1.4, ZS, 5.4)
    CAJ = (3.2, 4.6, ZS + 1.4, ZS + 3.8)
    arq.muro_huecos(c, X0, X1, ZS, ZT, YF, YF + 0.7, [PUE, CAJ], blind)
    for x in (X0, X1 - 0.7):
        c.caja_de((x, YF + 0.7, ZS), (x + 0.7, YB - 0.7, ZT), blind)
    c.caja_de((X0, YB - 0.7, ZS), (X1, YB, ZT), blind)
    # pilastras de piedra con capitel y basa
    for x in (-4.6, -2.2, 2.2, 5.3):
        c.caja((x, YF - 0.2, (ZS + ZT) / 2), (0.75, 0.5, ZT - ZS), piedra, 0.06)
        c.caja((x, YF - 0.25, ZS + 0.2), (0.95, 0.65, 0.4), marmol, 0.05)
        c.caja((x, YF - 0.25, ZT - 0.25), (0.95, 0.65, 0.5), marmol, 0.05)
    # cornisa y friso
    c.caja_de((X0 - 0.4, YF - 0.7, ZT), (X1 + 0.4, YB + 0.3, ZT + 0.35), marmol, 0.06)
    c.caja_de((X0 - 0.2, YF - 0.5, ZT + 0.35), (X1 + 0.2, YB + 0.1, ZT + 0.75), piedra, 0.04)
    # saeteras con barrotes
    for x in (-3.4,):
        c.caja_de((x - 0.35, YF - 0.05, 3.0), (x + 0.35, YF + 0.05, 5.8), osc, 0.03)
        cr.caja_de((x - 0.25, YF + 0.04, 3.1), (x + 0.25, YF + 0.1, 5.7), None)
        for k in range(3):
            c.cil((x - 0.18 + k * 0.18, YF - 0.12, 3.1), (x - 0.18 + k * 0.18, YF - 0.12, 5.7), 0.03, acero, n=6)
    for s in (-1, 1):
        for y in (-0.5, 2.0):
            xs = X0 - 0.02 if s < 0 else X1 + 0.02
            c.caja((xs, y, 4.3), (0.1, 0.7, 2.6), osc, 0.03)
            for k in range(3):
                c.cil((xs + s * 0.08, y - 0.2 + k * 0.2, 3.05), (xs + s * 0.08, y - 0.2 + k * 0.2, 5.55), 0.03, acero, n=6)

    m.seccion("puerta reforzada")
    px0, px1, pz0, pz1 = PUE
    # marco grueso de acero con remaches
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.4, 0.35, osc, abajo=False)
    for x in (px0 - 0.2, px1 + 0.2):
        for k in range(6):
            c.remache((x, YF - 0.35, pz0 + 0.4 + k * 0.75), (0, -1, 0), acero, 0.05)
    pv = (px0 + 0.05, YF + 0.3, pz0)
    pu = m.parte("puerta", pivote=pv, nota="Hoja blindada batiente sobre bisagras de pivote (eje vertical). Los dos "
                                           "cerrojos (pieza cerrojos) se descorren 0,5 studs a la derecha del modelo "
                                           "antes de abrir.")
    W = px1 - px0 - 0.1
    pu.caja_de((px0 + 0.05, YF + 0.05, pz0 + 0.02), (px1 - 0.05, YF + 0.55, pz1 - 0.03), acero, 0.05)
    for k in range(3):
        for j in range(2):
            pu.caja_de((px0 + 0.25 + j * (W / 2), YF + 0.0, pz0 + 0.3 + k * 1.45),
                       (px0 + 0.25 + (j + 1) * (W / 2) - 0.2, YF + 0.05, pz0 + 0.3 + (k + 1) * 1.45 - 0.2), osc, 0.04)
    pu.cil((0, YF - 0.05, pz0 + 2.3), (0, YF - 0.2, pz0 + 2.3), 0.38, cromo, n=16)  # volante
    for k in range(4):
        a = k * math.pi / 4
        pu.caja((0, YF - 0.22, pz0 + 2.3), (0.9, 0.05, 0.06), cromo, 0.01, rot=(0, math.degrees(a), 0))
    pu.toro((0, YF - 0.24, pz0 + 2.3), 0.45, 0.04, cromo, n=16, m=5, rot=(90, 0, 0))
    for zz in (pz0 + 0.6, pz0 + 1.8, pz1 - 0.8):
        pu.cil((px0 + 0.05, YF + 0.3, zz - 0.25), (px0 + 0.05, YF + 0.3, zz + 0.25), 0.1, osc, n=10)
    cerr = m.parte("cerrojos", pivote=(px1, YF - 0.15, pz0 + 2.3), nota="Dos cerrojos de barra: se descorren juntos.")
    for zz in (pz0 + 1.1, pz1 - 1.1):
        cerr.cil((px1 - 0.9, YF - 0.12, zz), (px1 + 0.35, YF - 0.12, zz), 0.09, cromo, n=10)
        cerr.caja((px1 - 0.5, YF - 0.12, zz + 0.2), (0.08, 0.08, 0.3), cromo, 0.02)
        c.caja((px1 + 0.45, YF - 0.12, zz), (0.3, 0.3, 0.36), osc, 0.04)  # cajetín fijo
        c.caja((px1 - 1.0, YF - 0.12, zz), (0.2, 0.3, 0.3), osc, 0.03)
    c.caja((0, YF - 0.5, pz1 + 0.6), (3.4, 0.2, 0.5), osc, 0.04)

    m.seccion("cajero")
    x0, x1, z0, z1 = CAJ
    c.caja_de((x0 - 0.15, YF - 0.25, z0 - 0.15), (x1 + 0.15, YF + 0.05, z1 + 0.35), cromo, 0.04)  # bisel
    c.caja_de((x0, YF + 0.05, z0), (x1, YF + 0.45, z1), plas)
    c.caja_de((x0 + 0.05, YF - 0.28, z1 + 0.05), (x1 - 0.05, YF + 0.0, z1 + 0.3), plas, 0.02)  # visera
    neon.caja(((x0 + x1) / 2, YF + 0.05, z1 - 0.65), (1.0, 0.03, 0.75), None)  # pantalla
    c.caja(((x0 + x1) / 2, YF + 0.03, z1 - 0.65), (1.12, 0.06, 0.87), osc, 0.01)
    # ranura de tarjeta y de billetes
    c.caja((x1 - 0.3, YF - 0.06, z1 - 1.4), (0.36, 0.14, 0.14), cromo, 0.03)
    c.caja((x1 - 0.3, YF - 0.14, z1 - 1.4), (0.24, 0.02, 0.03), osc, 0.0)
    neon.caja((x1 - 0.3, YF - 0.13, z1 - 1.33), (0.18, 0.01, 0.015), None)
    c.caja(((x0 + x1) / 2, YF - 0.04, z0 + 0.25), (0.8, 0.1, 0.12), cromo, 0.03)
    c.caja(((x0 + x1) / 2, YF - 0.1, z0 + 0.25), (0.7, 0.02, 0.03), osc, 0.0)
    # teclado inclinado con 12 teclas + 4 de función
    with c.en((x0 + 0.5, YF - 0.12, z1 - 1.55), (-30, 0, 0)):
        c.caja((0, 0, 0), (0.62, 0.3, 0.7), cromo, 0.03)
        for i in range(4):
            for j in range(3):
                c.caja((-0.18 + j * 0.13, -0.17, 0.24 - i * 0.14), (0.1, 0.05, 0.1), tecla, 0.015)
        for i, col in enumerate((rojo, amar, verde, tecla)):
            c.caja((0.25, -0.17, 0.24 - i * 0.14), (0.1, 0.05, 0.1), col, 0.015)
    c.texto("24 h", m.mat("pintura", "#E6E2D8", desgaste=0.1), alto=0.14, grosor=0.02, c=((x0 + x1) / 2, YF - 0.27, z1 + 0.12),
            fuente="negrita")

    m.seccion("placa y cámara")
    c.caja((0, YF - 0.45, pz1 + 1.15), (4.4, 0.08, 0.7), laton, 0.03)
    c.caja((0, YF - 0.5, pz1 + 1.15), (4.2, 0.02, 0.56), laton, 0.0)
    c.texto("BANCO COLONIAL", laton, alto=0.36, grosor=0.06, c=(0, YF - 0.52, pz1 + 0.99), fuente="serif")
    for x in (-2.05, 2.05):
        c.perno((x, YF - 0.5, pz1 + 1.15), (0, -1, 0), laton, r=0.04)
    arq.camara_seguridad(c, luces, (-1.9, YF - 0.45, pz1 + 0.3), m.mat("plastico", "#D5D8DB"), acero, plas)
    arq.foco_pared(c, luces, (-2.2, YF - 0.45, 4.2), osc, laton)
    arq.foco_pared(c, luces, (2.2, YF - 0.45, 4.2), osc, laton)
    # cúpula de vigilancia y antena en el tejado
    c.cil((3.5, 2.5, ZT + 0.75), (3.5, 2.5, ZT + 0.95), 0.4, acero, n=12)
    c.esfera((3.5, 2.5, ZT + 0.95), 0.32, osc, seg=12, anillos=6, esc=(1, 1, 0.7))
    c.cil((-3.8, 3.0, ZT + 0.75), (-3.8, 3.0, ZT + 2.2), 0.04, acero, n=6)
    m.terminar()


# ==============================================================================================================
def restaurante():
    m = Modelo("restaurante", ZONA, (14, 10, 8), 14000,
               "La Nebulosa: restaurante con terraza (3 mesas redondas, 6 sillas), toldo retráctil de brazos "
               "articulados, menú holográfico, macetas y ventanal con la barra a la vista.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#B2D4E0", transparencia=0.35)
    neon = m.parte("menu_neon", tipo="neon", color=NEON)
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    toldo = m.parte("toldo", pivote=(0, -0.95, 5.9), nota="Toldo extendido. Se recoge girando/encogiendo hacia el "
                                                        "cajón (pivote): en Studio, escalar en Z de Roblox hasta 0,1.")

    fach = m.mat("pintura", "#E8DCC4", desgaste=0.35, c_desgaste="#A08C70", lluvia=0.5)
    ladr = m.mat("ladrillo", "#9A5A3F", c2="#8A817A", tam_ladrillo=(0.45, 0.22))
    madera = m.mat("madera", "#5E3B22", eje="X")
    madera_z = m.mat("madera", "#5E3B22", eje="Z")
    suelo = m.mat("piedra", "#9C9284", escala=0.7)
    acero = m.mat("metal", "#858B92")
    osc = m.mat("metal", "#2E3338", rug=0.45)
    cromo = m.mat("cromo", "#D0D5DA")
    lona = m.mat("tela", "#2C6E7A", lluvia=0.4)
    lona2 = m.mat("tela", "#E9E2D2", lluvia=0.3)
    asiento = m.mat("plastico", "#E36B2C")
    asiento2 = m.mat("plastico", "#2BA6B5")
    mesa = m.mat("plastico", "#F1EEE8")
    tierra = m.mat("piedra", "#3D2D20", bump=0.6)
    hoja = m.mat("organico", "#3E8A3A")
    hoja2 = m.mat("organico", "#5BA94A")
    maceta = m.mat("ceramica", "#B5603A")
    botella = m.mat("liquido", "#2F6B3A")
    botella2 = m.mat("liquido", "#8A3B1E")

    X0, X1, YF, YB, Z0, ZT = -6.4, 6.4, -1.0, 4.8, 0.3, 6.8

    m.seccion("terraza y edificio")
    c.caja_de((X0 - 0.2, -5.0, 0), (X1 + 0.2, YB + 0.2, Z0), suelo, 0.04)
    VEN = (-5.6, 1.0, 1.2, 5.0)
    PUE = (2.4, 4.6, Z0, 5.0)
    arq.muro_huecos(c, X0, X1, Z0, 1.2, YF, YF + 0.35, [(PUE[0], PUE[1], Z0, 1.2)], ladr)
    arq.muro_huecos(c, X0, X1, 1.2, ZT, YF, YF + 0.35, [VEN, (PUE[0], PUE[1], 1.2, PUE[3])], fach)
    for x in (X0, X1 - 0.35):
        c.caja_de((x, YF + 0.35, Z0), (x + 0.35, YB - 0.35, ZT), fach)
    c.caja_de((X0, YB - 0.35, Z0), (X1, YB, ZT), fach)
    c.caja_de((X0 - 0.2, YF - 0.3, ZT), (X1 + 0.2, YB + 0.2, ZT + 0.3), madera, 0.05)
    c.caja_de((X0 - 0.1, YF - 0.2, ZT + 0.3), (X1 + 0.1, YB + 0.1, ZT + 0.55), fach, 0.03)
    for x in (X0 + 0.1, X1 - 0.1):
        c.caja((x, YF - 0.05, (Z0 + ZT) / 2), (0.3, 0.2, ZT - Z0), ladr, 0.03)
    m.seccion("ventanal y barra interior")
    x0, x1, z0, z1 = VEN
    arq.marco(c, x0, x1, z0, z1, YF, 0.14, 0.12, madera_z)
    for k in (1, 2):
        x = x0 + k * (x1 - x0) / 3
        c.caja_de((x - 0.05, YF - 0.03, z0), (x + 0.05, YF + 0.1, z1), madera_z, 0.01)
    cr.caja_de((x0, YF + 0.04, z0), (x1, YF + 0.14, z1), None)
    YI = YF + 0.35
    c.caja_de((x0 - 0.2, YI, Z0), (x1 + 0.2, YI + 3.4, Z0 + 0.05), madera)
    c.caja_de((x0 - 0.2, YI + 3.4, Z0), (x1 + 0.2, YI + 3.6, ZT), ladr)
    c.caja_de((x0 - 0.2, YI, z1 + 0.2), (x1 + 0.2, YI + 3.6, z1 + 0.4), fach)
    c.caja_de((x1 + 0.2, YI, Z0), (x1 + 0.4, YI + 3.6, ZT), fach)
    # barra con frente de madera y encimera, taburetes y botellero
    c.caja_de((x0 + 0.3, YI + 1.6, Z0), (x1 - 0.3, YI + 2.2, Z0 + 1.9), madera_z, 0.04)
    c.caja_de((x0 + 0.2, YI + 1.5, Z0 + 1.9), (x1 - 0.2, YI + 2.3, Z0 + 2.02), cromo, 0.02)
    for i in range(4):
        x = x0 + 1.0 + i * (x1 - x0 - 2.0) / 3
        c.cil((x, YI + 1.15, Z0), (x, YI + 1.15, Z0 + 1.3), 0.05, cromo, n=6)
        c.cil((x, YI + 1.15, Z0 + 1.3), (x, YI + 1.15, Z0 + 1.42), 0.32, asiento, n=12)
        c.cil((x, YI + 1.15, Z0 + 0.02), (x, YI + 1.15, Z0 + 0.06), 0.25, cromo, n=10)
    for zz in (3.0, 3.8):
        c.caja_de((x0 + 0.3, YI + 3.0, zz - 0.06), (x1 - 0.3, YI + 3.4, zz), madera, 0.01)
        for i in range(12):
            x = x0 + 0.5 + i * (x1 - x0 - 1.0) / 11
            c.torno([(0.0, 0.0), (0.09, 0.0), (0.09, 0.32), (0.035, 0.45), (0.035, 0.58), (0.0, 0.58)],
                    [botella, botella2][i % 2], n=8, c=(x, YI + 3.2, zz))
    luces.caja(((x0 + x1) / 2, YI + 1.9, z1 + 0.1), (x1 - x0 - 1.0, 0.1, 0.05), None)

    m.seccion("puerta")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.15, 0.14, madera_z, abajo=False)
    for lado, (hx0, s) in {"izq": (px0, 1), "der": (px1, -1)}.items():
        w = (px1 - px0) / 2
        pv = (hx0, YF + 0.2, pz0)
        h = m.parte(f"puerta_{lado}", pivote=pv, nota="Hoja batiente acristalada: gira sobre su bisagra.")
        hc = m.parte(f"puerta_{lado}_cristal", tipo="cristal", color="#B2D4E0", pivote=pv, transparencia=0.4)
        xa, xb = sorted((hx0, hx0 + s * w))
        for (a, b_) in (((xa, pz0), (xb, pz0 + 0.8)), ((xa, pz1 - 0.3), (xb, pz1))):
            h.caja_de((a[0], YF + 0.12, a[1]), (b_[0], YF + 0.26, b_[1]), madera_z, 0.03)
        h.caja_de((xa, YF + 0.12, pz0 + 0.8), (xa + 0.14, YF + 0.26, pz1 - 0.3), madera_z, 0.02)
        h.caja_de((xb - 0.14, YF + 0.12, pz0 + 0.8), (xb, YF + 0.26, pz1 - 0.3), madera_z, 0.02)
        hc.caja_de((xa + 0.14, YF + 0.16, pz0 + 0.8), (xb - 0.14, YF + 0.22, pz1 - 0.3), None)
        xt = hx0 + s * (w - 0.22)
        h.cil((xt, YF + 0.05, pz0 + 1.7), (xt, YF + 0.05, pz0 + 2.7), 0.03, cromo, n=6)
        for zz in (pz0 + 1.75, pz0 + 2.65):
            h.cil((xt, YF + 0.05, zz), (xt, YF + 0.12, zz), 0.02, cromo, n=6)
        for zz in (pz0 + 0.5, pz1 - 0.5):
            h.cil((hx0, YF + 0.2, zz - 0.15), (hx0, YF + 0.2, zz + 0.15), 0.04, cromo, n=8)

    m.seccion("cartel LA NEBULOSA")
    sx, sz = -2.2, ZT - 0.55
    c.caja((sx, YF - 0.12, sz), (5.6, 0.12, 0.85), osc, 0.03)
    c.texto("LA NEBULOSA", m.mat("metal", "#D7B45A", rug=0.3), alto=0.46, grosor=0.08, c=(sx + 0.5, YF - 0.2, sz - 0.2),
            fuente="serif")
    # logotipo: galaxia espiral en relieve (dos brazos logarítmicos de tubo y núcleo)
    gx = sx - 2.15
    with c.en((gx, YF - 0.2, sz), (90, 0, 0)):
        c.esfera((0, 0, 0), 0.1, m.mat("metal", "#D7B45A", rug=0.3), seg=8, anillos=5)
        for brazo in (0, math.pi):
            pts = []
            for i in range(12):
                t = i / 11 * 2.6
                r = 0.06 * math.exp(0.62 * t)
                pts.append((math.cos(t + brazo) * r, math.sin(t + brazo) * r * 0.8, 0))
            c.tubo(pts, 0.03, m.mat("metal", "#D7B45A", rug=0.3), n=5, seg=2, r_fin=0.012)
        luces.toro((0, 0, -0.03), 0.36, 0.015, None, n=16, m=4)

    m.seccion("toldo retráctil")
    # cajón del toldo y brazos articulados (dos tramos y codo)
    tx0, tx1 = X0 + 0.3, X1 - 0.3
    c.caja(((tx0 + tx1) / 2, YF - 0.25, 5.9), (tx1 - tx0, 0.42, 0.42), acero, 0.08)
    c.cil((tx0, YF - 0.25, 5.9), (tx1, YF - 0.25, 5.9), 0.17, osc, n=10)
    sal = 3.6
    caida = 1.1
    def lona_f(u, v):
        x = tx0 + 0.1 + u * (tx1 - tx0 - 0.2)
        y = YF - 0.3 - v * sal
        z = 5.85 - v * caida - 0.06 * math.sin(v * math.pi) - 0.04 * math.sin(u * math.pi * 10) * v
        return (x, y, z)
    toldo.lamina(lona_f, 30, 4, 0.04, lona)
    # faldón ondulado con rayas
    for i in range(12):
        xa = tx0 + 0.1 + i * (tx1 - tx0 - 0.2) / 12
        xb = xa + (tx1 - tx0 - 0.2) / 12
        toldo.extruir([(xa, 0), (xb, 0), (xb, -0.3), ((xa + xb) / 2, -0.45), (xa, -0.3)], 0.03,
                      [lona, lona2][i % 2], c=(0, YF - 0.3 - sal - 0.03, 5.85 - caida), rot=(90, 0, 0))
    toldo.cil((tx0 + 0.05, YF - 0.3 - sal, 5.85 - caida), (tx1 - 0.05, YF - 0.3 - sal, 5.85 - caida), 0.07, acero, n=8)
    for x in (tx0 + 0.5, (tx0 + tx1) / 2 - 1.5, (tx0 + tx1) / 2 + 1.5, tx1 - 0.5):
        hombro = V((x, YF - 0.05, 4.9))
        punta = V((x, YF - 0.3 - sal, 5.85 - caida - 0.05))
        codo = (hombro + punta) / 2 + V((0.0, 0.0, -0.75))
        toldo.caja(hombro + V((0, 0.05, 0)), (0.2, 0.12, 0.3), osc, 0.02)
        toldo.cil(hombro, codo, 0.05, acero, n=8)
        toldo.cil(codo, punta, 0.045, acero, n=8)
        toldo.esfera(codo, 0.08, osc, seg=8, anillos=5)
        toldo.cil(codo + V((-0.08, 0, 0)), codo + V((0.08, 0, 0)), 0.04, cromo, n=6)  # pasador

    m.seccion("terraza: mesas y sillas")
    mesas = [(-4.2, -3.2), (0.0, -3.6), (4.2, -3.2)]
    for i, (mx, my) in enumerate(mesas):
        c.cil((mx, my, Z0), (mx, my, Z0 + 0.04), 0.42, osc, n=12)
        for k in range(4):
            a = k * math.pi / 2 + math.pi / 4
            c.cil((mx, my, Z0 + 0.04), (mx + math.cos(a) * 0.42, my + math.sin(a) * 0.42, Z0 + 0.02), 0.035, osc, n=5)
        c.cil((mx, my, Z0 + 0.04), (mx, my, Z0 + 1.55), 0.06, cromo, n=8)
        c.cil((mx, my, Z0 + 1.55), (mx, my, Z0 + 1.62), 0.85, mesa, n=20, b=0.02)
        c.toro((mx, my, Z0 + 1.585), 0.85, 0.035, cromo, n=20, m=4)
        # servilletero y vaso
        c.caja((mx + 0.2, my, Z0 + 1.72), (0.18, 0.1, 0.18), cromo, 0.01)
        c.cil((mx - 0.3, my + 0.15, Z0 + 1.62), (mx - 0.3, my + 0.15, Z0 + 1.88), 0.07, m.mat("liquido", "#E8C060"), n=8,
              r1=0.08)
        for j, s in enumerate((-1, 1)):
            with c.en((0, 0, Z0)):
                _silla_terraza(c, mx + s * 1.35, my, 90 * s, cromo, asiento if (i + j) % 2 == 0 else asiento2)

    m.seccion("macetas y menú")
    def maceta_planta(x, y, r, h, semilla):
        c.torno([(0.0, 0.0), (r * 0.75, 0.0), (r, h), (r * 1.08, h), (r * 1.08, h + 0.08), (r * 0.92, h + 0.08),
                 (0.0, h - 0.1)], maceta, n=12, c=(x, y, Z0))
        c.cil((x, y, Z0 + h - 0.12), (x, y, Z0 + h - 0.04), r * 0.95, tierra, n=10)
        rnd = m.rnd
        for k in range(7):
            a = k * math.tau / 7 + semilla
            rr = r * 0.45
            base = V((x + math.cos(a) * rr * 0.4, y + math.sin(a) * rr * 0.4, Z0 + h - 0.05))
            top = base + V((math.cos(a) * 0.35, math.sin(a) * 0.35, 0.7 + rnd.uniform(0, 0.5)))
            c.cil(base, top, 0.025, hoja, n=4)
            c.ico(top, 0.28 + rnd.uniform(0, 0.1), [hoja, hoja2][k % 2], sub=1, ruido=0.25, semilla=k + int(semilla * 10),
                  esc=(1, 1, 0.75))
    maceta_planta(PUE[0] - 0.55, YF - 0.6, 0.38, 0.8, 0.3)
    maceta_planta(PUE[1] + 0.55, YF - 0.6, 0.38, 0.8, 1.1)
    # menú holográfico: poste, base emisora y panel de luz con líneas de texto
    hx, hy = PUE[1] + 1.25, YF - 0.9
    c.cil((hx, hy, Z0), (hx, hy, Z0 + 0.06), 0.3, osc, n=10)
    c.cil((hx, hy, Z0 + 0.06), (hx, hy, Z0 + 2.0), 0.06, acero, n=8)
    c.caja((hx, hy, Z0 + 2.05), (0.5, 0.25, 0.12), osc, 0.03)
    for s in (-1, 1):
        c.cil((hx + s * 0.18, hy - 0.12, Z0 + 2.1), (hx + s * 0.18, hy - 0.12, Z0 + 2.16), 0.04, cromo, n=8)
    neon.caja((hx, hy, Z0 + 2.95), (1.0, 0.02, 1.4), None)
    for k in range(6):
        neon.caja((hx - 0.15 + (k % 2) * 0.08, hy - 0.025, Z0 + 3.45 - k * 0.18), (0.6 - (k % 3) * 0.1, 0.02, 0.06), None)
    neon.texto("MENÚ", None, alto=0.16, grosor=0.02, c=(hx, hy - 0.03, Z0 + 3.5), fuente="negrita")
    m.notas.append("El menú holográfico es un panel Neon: para que parezca holograma, Transparency 0,4 en Studio.")
    m.terminar()


# ==============================================================================================================
def bar_cantina():
    m = Modelo("bar_cantina", ZONA, (10, 10, 7), 12000,
               "Cantina: más oscura y acogedora, de madera ennegrecida, con barra exterior y tres taburetes, "
               "estantería de botellas, letrero de jarra en neón ámbar, puertas batientes tipo saloon y pizarra.")
    c = m.parte()
    neon = m.parte("jarra_neon", tipo="neon", color="#FFB347")
    luces = m.parte("luces_neon", tipo="neon", color="#FFB347", nota="Luz cálida de la cantina (ámbar).")
    cr = m.parte("botellas_cristal", tipo="cristal", color="#5E8A55", transparencia=0.25)

    tabla = m.mat("madera", "#4A3020", eje="X", lluvia=0.7)
    tabla_z = m.mat("madera", "#3E2818", eje="Z", lluvia=0.7)
    piedra = m.mat("piedra", "#6E665C")
    acero = m.mat("metal", "#7A7F86")
    osc = m.mat("metal", "#24272B", rug=0.5)
    laton = m.mat("metal", "#A88038", rug=0.35)
    chapa = m.mat("oxido", "#7B4A2E")
    cuero = m.mat("cuero", "#5B2E1A")
    pizarra = m.mat("pizarra", "#1E2622")
    tiza = m.mat("tiza", "#ECEBE4")
    liq = [m.mat("liquido", h) for h in ("#5A2410", "#C08A2A", "#2B5A2E", "#7A1E2A", "#D8C9A0")]

    X0, X1, YF, YB, Z0, ZT = -4.6, 4.6, -1.2, 4.4, 0.35, 5.6

    m.seccion("cuerpo")
    c.caja_de((X0 - 0.2, -4.6, 0), (X1 + 0.2, YB + 0.2, Z0), piedra, 0.05)
    PUE = (1.6, 3.6, Z0, 4.4)
    BAR = (-4.0, 0.9, 1.6, 4.4)  # ventana de despacho de la barra
    arq.muro_huecos(c, X0, X1, Z0, ZT, YF, YF + 0.35, [PUE, BAR], tabla_z)
    for x in (X0, X1 - 0.35):
        c.caja_de((x, YF + 0.35, Z0), (x + 0.35, YB - 0.35, ZT), tabla_z)
    c.caja_de((X0, YB - 0.35, Z0), (X1, YB, ZT), tabla_z)
    # tablas de la fachada (relieve real: listones superpuestos)
    for k in range(13):
        z = Z0 + 0.2 + k * 0.4
        if z > ZT - 0.2:
            break
        for (xa, xb) in ((X0, BAR[0]), (BAR[1], PUE[0]), (PUE[1], X1)):
            c.caja_de((xa, YF - 0.06, z - 0.02), (xb, YF + 0.0, z + 0.1), tabla)
    for x in (X0 + 0.1, X1 - 0.1):
        c.caja((x, YF - 0.08, (Z0 + ZT) / 2), (0.28, 0.28, ZT - Z0), tabla_z, 0.04)
    # porche: tejadillo de chapa oxidada sobre postes, que cubre la barra exterior
    for x in (X0 + 0.2, -1.6, 0.9, X1 - 0.2):
        c.caja((x, -4.0, (Z0 + 4.7) / 2), (0.25, 0.25, 4.7 - Z0), tabla_z, 0.03)
        c.caja((x, -4.0, Z0 + 0.1), (0.35, 0.35, 0.2), piedra, 0.03)
    c.caja_de((X0, -4.15, 4.6), (X1, -3.85, 4.85), tabla, 0.03)
    with c.en((0, -2.55, 5.05), (math.degrees(math.atan2(0.7, 3.2)), 0, 0)):
        c.lamina(lambda u, v: (X0 - 0.3 + u * (X1 - X0 + 0.6), -1.75 + v * 3.5, 0.05 * math.sin(u * 30 * math.pi)), 60, 1,
                 0.04, chapa)
    for x in (X0 + 0.2, X1 - 0.2):
        c.cil((x, -3.95, 3.8), (x + (0.6 if x < 0 else -0.6), -3.95, 4.6), 0.06, tabla_z, n=6)  # jabalcones
    # tejado del edificio a un agua
    with c.en((0, (YF + YB) / 2, ZT + 0.35), (-math.degrees(math.atan2(0.7, YB - YF)), 0, 0)):
        c.lamina(lambda u, v: (X0 - 0.4 + u * (X1 - X0 + 0.8), -(YB - YF) / 2 - 0.4 + v * (YB - YF + 0.8),
                               0.05 * math.sin(u * 32 * math.pi)), 64, 1, 0.04, chapa)
    c.caja_de((X0, YF, ZT), (X1, YB, ZT + 0.2), tabla, 0.03)
    c.cil((3.0, 3.0, ZT), (3.0, 3.0, ZT + 1.9), 0.22, osc, n=10)  # chimenea de estufa
    c.cil((3.0, 3.0, ZT + 1.9), (3.0, 3.0, ZT + 2.05), 0.35, osc, n=10, r1=0.1)

    m.seccion("barra exterior y taburetes")
    bx0, bx1, bz0, bz1 = BAR
    c.caja_de((bx0 - 0.2, YF - 0.95, Z0), (bx1 + 0.2, YF - 0.25, Z0 + 1.65), tabla_z, 0.04)
    c.caja_de((bx0 - 0.3, YF - 1.15, Z0 + 1.65), (bx1 + 0.3, YF - 0.15, Z0 + 1.8), tabla, 0.04)
    c.caja_de((bx0 - 0.2, YF - 1.0, Z0 + 0.25), (bx1 + 0.2, YF - 0.9, Z0 + 0.32), laton, 0.01)  # reposapiés
    for i in range(3):
        x = bx0 + 0.8 + i * (bx1 - bx0 - 1.6) / 2
        y = YF - 1.75
        c.cil((x, y, Z0), (x, y, Z0 + 0.04), 0.3, osc, n=10)
        c.cil((x, y, Z0 + 0.04), (x, y, Z0 + 1.25), 0.05, acero, n=8)
        c.toro((x, y, Z0 + 0.5), 0.25, 0.025, acero, n=10, m=4)
        c.cil((x, y, Z0 + 1.25), (x, y, Z0 + 1.32), 0.12, osc, n=8)
        c.cil((x, y, Z0 + 1.32), (x, y, Z0 + 1.45), 0.36, cuero, n=14, b=0.03)
        for k in range(8):
            a = k * math.tau / 8
            c.remache((x + math.cos(a) * 0.36, y + math.sin(a) * 0.36, Z0 + 1.39), (math.cos(a), math.sin(a), 0), laton,
                      0.02)
    # jarras sobre la barra
    for i, x in enumerate((bx0 + 0.6, bx0 + 2.4)):
        c.cil((x, YF - 0.6, Z0 + 1.8), (x, YF - 0.6, Z0 + 2.15), 0.11, laton, n=10)
        c.cil((x, YF - 0.6, Z0 + 2.12), (x, YF - 0.6, Z0 + 2.2), 0.1, m.mat("tiza", "#F2EAD8"), n=10)
        c.tubo([(x + 0.1, YF - 0.6, Z0 + 2.08), (x + 0.22, YF - 0.6, Z0 + 2.05), (x + 0.22, YF - 0.6, Z0 + 1.9),
                (x + 0.1, YF - 0.6, Z0 + 1.87)], 0.022, laton, n=5, seg=2)

    m.seccion("botellero")
    YI = YF + 0.35
    c.caja_de((bx0, YI, Z0), (bx1, YI + 1.4, Z0 + 0.05), tabla)
    c.caja_de((bx0 - 0.2, YI + 1.4, Z0), (bx1 + 0.2, YI + 1.6, ZT - 0.2), tabla_z)
    c.caja_de((bx0 - 0.2, YI, bz1 + 0.2), (bx1 + 0.2, YI + 1.6, bz1 + 0.4), tabla)
    for zz in (2.25, 3.25):
        c.caja_de((bx0 + 0.1, YI + 1.0, zz - 0.07), (bx1 - 0.1, YI + 1.4, zz), tabla, 0.015)
    perfiles = [
        [(0.0, 0.0), (0.12, 0.0), (0.12, 0.42), (0.05, 0.55), (0.04, 0.72), (0.0, 0.72)],  # cilíndrica
        [(0.0, 0.0), (0.16, 0.0), (0.19, 0.18), (0.14, 0.34), (0.045, 0.42), (0.04, 0.58), (0.0, 0.58)],  # redonda
        [(0.0, 0.0), (0.1, 0.0), (0.1, 0.5), (0.03, 0.62), (0.03, 0.8), (0.0, 0.8)],  # alta
    ]
    k = 0
    for zz in (2.25, 3.25):
        x = bx0 + 0.4
        while x < bx1 - 0.3:
            forma = k % 4
            col = liq[k % 5]
            if forma == 3:  # cuadrada
                cr.caja((x, YI + 1.2, zz + 0.25), (0.22, 0.22, 0.5), None, 0.03)
                c.caja((x, YI + 1.2, zz + 0.16), (0.18, 0.18, 0.3), col, 0.02)
                c.cil((x, YI + 1.2, zz + 0.5), (x, YI + 1.2, zz + 0.62), 0.04, laton, n=6)
                x += 0.36
            else:
                p = perfiles[forma]
                cr.torno(p, None, n=8, c=(x, YI + 1.2, zz))
                h = p[-1][1]
                c.torno([(0.0, 0.02), (p[1][0] * 0.85, 0.02), (p[1][0] * 0.85, h * 0.45), (0.0, h * 0.45)], col, n=8,
                        c=(x, YI + 1.2, zz))
                c.cil((x, YI + 1.2, zz + h - 0.04), (x, YI + 1.2, zz + h + 0.06), 0.05, laton if k % 2 else cuero, n=6)
                x += p[1][0] * 2 + 0.14
            k += 1
    luces.caja(((bx0 + bx1) / 2, YI + 0.8, bz1 + 0.15), (bx1 - bx0 - 0.4, 0.08, 0.05), None)

    m.seccion("puertas saloon")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.16, 0.14, tabla_z, abajo=False)
    c.caja_de((px0, YF + 0.3, pz0), (px1, YF + 0.35, pz1), m.mat("madera", "#2A1A10", eje="Z", suciedad=0.3))  # fondo
    for lado, (hx, s) in {"izq": (px0 + 0.05, 1), "der": (px1 - 0.05, -1)}.items():
        w = (px1 - px0) / 2 - 0.08
        pv = (hx, YF - 0.05, pz0 + 1.0)
        h = m.parte(f"puerta_{lado}", pivote=pv, nota="Hoja batiente de saloon: gira sobre el eje vertical del pivote "
                                                       "en los dos sentidos (±80°) y vuelve sola.")
        xa, xb = sorted((hx, hx + s * w))
        h.caja_de((xa, YF - 0.09, pz0 + 1.0), (xb, YF - 0.01, pz0 + 1.18), tabla, 0.02)
        h.caja_de((xa, YF - 0.09, pz0 + 2.8), (xb, YF - 0.01, pz0 + 3.0), tabla, 0.02)
        h.caja_de((xa, YF - 0.09, pz0 + 1.18), (xa + 0.12, YF - 0.01, pz0 + 2.8), tabla, 0.01)
        h.caja_de((xb - 0.12, YF - 0.09, pz0 + 1.18), (xb, YF - 0.01, pz0 + 2.8), tabla, 0.01)
        for j in range(8):  # lamas
            h.caja(((xa + xb) / 2, YF - 0.05, pz0 + 1.3 + j * 0.19), (w - 0.24, 0.02, 0.15), tabla, 0.0, rot=(35, 0, 0))
        # remate curvo superior
        h.extruir([(xa, 0), (xb, 0)] + [(xb - (xb - xa) * t, 0.12 + 0.2 * math.sin(t * math.pi) * (1 if s > 0 else 1))
                                        for t in [i / 6 for i in range(7)]], 0.06, tabla,
                  c=(0, YF - 0.05, pz0 + 3.0), rot=(90, 0, 0))
        for zz in (pz0 + 1.25, pz0 + 2.7):
            h.cil((hx, YF - 0.05, zz - 0.1), (hx, YF - 0.05, zz + 0.1), 0.04, laton, n=8)

    m.seccion("cartel jarra y pizarra")
    # jarra de cerveza en tubo de neón ámbar sobre un soporte
    jx, jz = -1.6, ZT - 0.3
    c.caja((jx, YF - 0.12, jz - 0.3), (1.6, 0.08, 1.5), osc, 0.03)
    for (dx, dz) in ((-0.7, 0.4), (0.7, 0.4), (-0.7, -0.95), (0.7, -0.95)):
        c.perno((jx + dx, YF - 0.17, jz + dz), (0, -1, 0), acero, r=0.03)
    def tubo_neon(pts):
        neon.tubo([(jx + x, YF - 0.25, jz + z) for x, z in pts], 0.035, None, n=6, seg=3)
        for x, z in pts[:: max(1, len(pts) // 2)]:
            c.cil((jx + x, YF - 0.16, jz + z), (jx + x, YF - 0.23, jz + z), 0.02, acero, n=4)
    tubo_neon([(-0.45, 0.25), (-0.4, -0.85), (0.35, -0.85), (0.4, 0.25)])
    tubo_neon([(0.42, 0.05), (0.7, 0.0), (0.72, -0.45), (0.4, -0.6)])
    tubo_neon([(-0.5, 0.25), (-0.3, 0.45), (0.0, 0.38), (0.25, 0.5), (0.48, 0.28)])
    tubo_neon([(-0.2, -0.15), (-0.2, -0.7)])
    tubo_neon([(0.15, -0.15), (0.15, -0.7)])
    # pizarra de pie junto a la puerta
    with c.en((PUE[1] + 0.55, YF - 0.8, Z0), (0, 0, -15)):
        for s in (-1, 1):
            c.cil((s * 0.5, -0.25, 0), (s * 0.48, 0.0, 1.9), 0.04, tabla_z, n=5)
            c.cil((s * 0.5, 0.35, 0), (s * 0.48, 0.0, 1.9), 0.035, tabla_z, n=5)
        c.caja((0, -0.13, 1.1), (1.05, 0.06, 1.3), tabla, 0.02, rot=(-8, 0, 0))
        c.caja((0, -0.17, 1.1), (0.92, 0.02, 1.15), pizarra, 0.0, rot=(-8, 0, 0))
        with c.en((0, -0.19, 1.1), (-8, 0, 0)):
            c.texto("HAPPY HOUR", tiza, alto=0.15, grosor=0.008, c=(0, 0, 0.25), fuente="mano", resol=1)
            c.texto("18-20h", tiza, alto=0.24, grosor=0.008, c=(0, 0, -0.15), fuente="mano", resol=1)
    # farolillos ámbar del porche
    for x in (-3.0, 3.0):
        c.cil((x, -3.9, 4.6), (x, -3.9, 4.2), 0.012, osc, n=4)
        c.cil((x, -3.9, 4.2), (x, -3.9, 4.12), 0.12, osc, n=8)
        luces.esfera((x, -3.9, 4.0), 0.1, None, seg=8, anillos=5)
    # barriles junto a la entrada
    for (x, y) in ((X1 - 0.5, -2.0), (X1 - 0.5, -2.8)):
        c.torno([(0.0, 0.0), (0.34, 0.0), (0.4, 0.45), (0.34, 0.9), (0.0, 0.9)], tabla_z, n=12, c=(x, y, Z0))
        for zz in (0.12, 0.78):
            c.toro((x, y, Z0 + zz), 0.36, 0.02, osc, n=12, m=4)
    m.terminar()


# ==============================================================================================================
def hospital_clinica():
    m = Modelo("hospital_clinica", ZONA, (14, 12, 10), 16000,
               "Clínica Colonial: el edificio más limpio, paneles blancos, cruz médica blanca luminosa, rampa con "
               "barandillas, puerta doble corredera esmerilada, camilla tras la ventana, botiquín y ambulancia hover.")
    c = m.parte()
    cruz = m.parte("cruz_neon", tipo="neon", color=NEON_CLINICA)
    luces = m.parte("luces_neon", tipo="neon", color=NEON_CLINICA)
    cr = m.parte("cristal", tipo="cristal", color="#B9DCE8", transparencia=0.3)
    amb = m.parte("ambulancia", pivote=(-5.6, -1.0, 0.0), nota="Ambulancia hover (3 × 2 × 2): pieza aparte para "
                                                              "poder moverla; flota a 0,35 studs del suelo.")
    amb_n = m.parte("ambulancia_neon", tipo="neon", color=NEON_CLINICA, pivote=(-5.6, -1.0, 0.0))
    amb_cr = m.parte("ambulancia_cristal", tipo="cristal", color="#2E4A60", pivote=(-5.6, -1.0, 0.0), transparencia=0.3)

    blanco = m.mat("paneles", "#F1F2F2", tam_panel=(1.6, 1.6), desgaste=0.15, c_desgaste="#B8BCC0", suciedad=0.3,
                   lluvia=0.2)
    gris = m.mat("pintura", "#A9B0B6", desgaste=0.2)
    acero = m.mat("metal", "#9AA0A6", rug=0.35)
    cromo = m.mat("cromo", "#DADFE3")
    horm = m.mat("hormigon", "#C9C6C0", suciedad=0.3)
    rojo = m.mat("pintura", "#C9252B", desgaste=0.25)
    azul = m.mat("plastico", "#3C86C4")
    colchon = m.mat("cuero", "#5AA6C9", desgaste=0.0)
    goma = m.mat("goma", "#202225")
    sab = m.mat("tela", "#F4F4F0", suciedad=0.1)

    X0, X1, YF, YB, Z0, ZT = -3.4, 6.6, -2.4, 4.6, 0.5, 8.0
    D_DESC = 1.6  # fondo del descansillo de entrada
    L = 3.0  # largo de la rampa (pendiente 1:6)

    m.seccion("cuerpo")
    c.caja_de((X0 - 0.2, YF - 0.2, 0), (X1 + 0.2, YB + 0.2, Z0), horm, 0.05)
    PUE = (1.0, 4.4, Z0, 5.6)
    VEN = (-2.7, 0.2, 1.9, 5.3)
    arq.muro_huecos(c, X0, X1, Z0, ZT, YF, YF + 0.4, [PUE, VEN], blanco)
    for x in (X0, X1 - 0.4):
        c.caja_de((x, YF + 0.4, Z0), (x + 0.4, YB - 0.4, ZT), blanco)
    c.caja_de((X0, YB - 0.4, Z0), (X1, YB, ZT), blanco)
    # franja gris y cornisa
    c.caja_de((X0 - 0.05, YF - 0.05, Z0), (X1 + 0.05, YB + 0.05, Z0 + 0.4), gris, 0.03)
    c.caja_de((X0 - 0.25, YF - 0.25, ZT), (X1 + 0.25, YB + 0.25, ZT + 0.3), gris, 0.05)
    c.caja_de((X0 - 0.1, YF - 0.1, ZT + 0.3), (X1 + 0.1, YB + 0.1, ZT + 0.6), blanco, 0.03)
    # ventanas altas del piso superior (fachada y laterales), con alféizar
    for x in (-1.6, 5.5):
        c.caja_de((x - 0.7, YF - 0.06, 6.2), (x + 0.7, YF + 0.05, 7.4), gris, 0.03)
        cr.caja_de((x - 0.6, YF - 0.08, 6.3), (x + 0.6, YF - 0.04, 7.3), None)
        c.caja_de((x - 0.8, YF - 0.2, 6.08), (x + 0.8, YF + 0.02, 6.2), gris, 0.02)
    for xs, sx in ((X0, -1), (X1, 1)):
        for y in (-0.3, 2.6):
            c.caja((xs + sx * 0.02, y, 6.8), (0.1, 1.5, 1.3), gris, 0.03)
            cr.caja((xs + sx * 0.06, y, 6.8), (0.04, 1.3, 1.1), None)
    # marquesina de entrada sobre dos columnas
    c.caja_de((PUE[0] - 0.8, YF - D_DESC - 0.1, 5.75), (PUE[1] + 0.8, YF, 6.0), blanco, 0.05)
    for x in (PUE[0] - 0.6, PUE[1] + 0.6):
        c.cil((x, YF - D_DESC + 0.1, Z0), (x, YF - D_DESC + 0.1, 5.75), 0.1, cromo, n=10)
    luces.caja(((PUE[0] + PUE[1]) / 2, YF - D_DESC / 2, 5.73), (2.6, 0.5, 0.04), None)
    # equipos del tejado (no asoman por encima de los 10 studs)
    c.caja((-1.2, 2.0, ZT + 0.95), (2.0, 1.4, 0.7), gris, 0.06)
    c.cil((-1.2, 2.0, ZT + 1.3), (-1.2, 2.0, ZT + 1.36), 0.5, acero, n=14)
    for k in range(4):
        a = k * math.pi / 2
        c.caja((-1.2 + math.cos(a) * 0.22, 2.0 + math.sin(a) * 0.22, ZT + 1.38), (0.4, 0.07, 0.02), acero, 0.0,
               rot=(0, 15, math.degrees(a)))
    c.tubo([(-0.2, 2.0, ZT + 0.8), (0.4, 2.0, ZT + 0.75), (0.6, 2.0, ZT + 0.62)], 0.08, acero, n=6, seg=2)
    for (x, y) in ((2.5, 3.2), (4.6, 0.4)):
        c.cil((x, y, ZT + 0.6), (x, y, ZT + 0.95), 0.14, acero, n=8)
        c.cil((x, y, ZT + 0.95), (x, y, ZT + 1.03), 0.24, acero, n=8, r1=0.06)

    m.seccion("rampa con barandillas")
    # descansillo ante la puerta y rampa accesible (1:6) que baja hacia delante, con barandilla a los dos lados
    rx0, rx1 = PUE[0] - 0.5, PUE[1] + 0.5
    c.caja_de((rx0, YF - D_DESC, 0), (rx1, YF, Z0), horm, 0.04)  # descansillo
    ang = math.degrees(math.atan2(Z0, L))
    with c.en(((rx0 + rx1) / 2, YF - D_DESC - L / 2, Z0 / 2), (ang, 0, 0)):
        c.caja((0, 0, -0.08), (2.2, L + 0.1, 0.16), horm, 0.03)
        for s in (-1, 1):
            c.caja((s * 1.15, 0, 0.0), (0.12, L, 0.25), gris, 0.02)
        # bandas antideslizantes
        for k in range(5):
            c.caja((0, -L / 2 + 0.35 + k * 0.58, 0.005), (2.0, 0.08, 0.02), m.mat("goma", "#2A2C30"), 0.0)
    for s in (-1.15, 1.15):
        x = (rx0 + rx1) / 2 + s
        arq.barandilla(c, [(x, YF - D_DESC - L, 0.0), (x, YF - D_DESC, Z0)], 1.0, cromo, r=0.045, n=8, barrotes=3)
    arq.barandilla(c, [(rx0, YF - D_DESC + 0.2, Z0), (rx0, YF - 0.2, Z0)], 1.0, cromo, r=0.045, n=8)

    m.seccion("puerta doble esmerilada")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.2, 0.18, gris, abajo=False)
    c.caja(((px0 + px1) / 2, YF - 0.25, pz1 + 0.25), (px1 - px0 + 0.4, 0.3, 0.35), gris, 0.04)  # cajón del mecanismo
    luces.caja(((px0 + px1) / 2 - 1.2, YF - 0.41, pz1 + 0.25), (0.25, 0.02, 0.08), None)
    for lado, (hx0, s) in {"izq": (px0, 1), "der": (px1, -1)}.items():
        w = (px1 - px0) / 2
        pv = (hx0 + s * w / 2, YF - 0.2, pz0)
        h = m.parte(f"puerta_{lado}", pivote=pv, nota=f"Hoja corredera: abrir {w - 0.1:.2f} studs hacia fuera del hueco.")
        hc = m.parte(f"puerta_{lado}_cristal", tipo="cristal", color="#E9F1F3", pivote=pv, transparencia=0.15,
                     nota="Cristal esmerilado: Glass blanco con poca transparencia.")
        xa, xb = sorted((hx0, hx0 + s * w))
        h.caja_de((xa, YF - 0.26, pz0), (xb, YF - 0.14, pz0 + 0.12), cromo, 0.01)
        h.caja_de((xa, YF - 0.26, pz1 - 0.12), (xb, YF - 0.14, pz1), cromo, 0.01)
        h.caja_de((xa, YF - 0.26, pz0), (xa + 0.1, YF - 0.14, pz1), cromo, 0.01)
        h.caja_de((xb - 0.1, YF - 0.26, pz0), (xb, YF - 0.14, pz1), cromo, 0.01)
        hc.caja_de((xa + 0.1, YF - 0.23, pz0 + 0.12), (xb - 0.1, YF - 0.17, pz1 - 0.12), None)
        # franja blanca de señalización (cruz pequeña) en el cristal
        h.caja(((xa + xb) / 2, YF - 0.27, pz0 + 2.6), (w - 0.4, 0.01, 0.12), azul, 0.0)

    m.seccion("ventana con camilla")
    x0, x1, z0, z1 = VEN
    arq.marco(c, x0, x1, z0, z1, YF, 0.14, 0.14, gris)
    cr.caja_de((x0, YF + 0.05, z0), (x1, YF + 0.15, z1), None)
    YI = YF + 0.4
    c.caja_de((x0 - 0.2, YI, z0 - 1.4), (x1 + 0.2, YI + 3.0, z0 - 1.35), m.mat("plastico", "#D6E2E6"))
    c.caja_de((x0 - 0.2, YI + 3.0, z0 - 1.4), (x1 + 0.2, YI + 3.2, z1 + 0.6), m.mat("plastico", "#E6F0F2"))
    c.caja_de((x0 - 0.2, YI, z1 + 0.4), (x1 + 0.2, YI + 3.2, z1 + 0.6), m.mat("plastico", "#E6F0F2"))
    for x in (x0 - 0.2, x1):
        c.caja_de((x, YI, z0 - 1.4), (x + 0.2, YI + 3.2, z1 + 0.6), m.mat("plastico", "#E6F0F2"))
    luces.caja(((x0 + x1) / 2, YI + 1.5, z1 + 0.35), (2.0, 0.6, 0.04), None)
    # camilla: chasis de tubo, colchón, almohada, sábana, barandillas abatibles y ruedas
    cxm, cym, zf = (x0 + x1) / 2, YI + 1.5, z0 - 1.35
    with c.en((cxm, cym, zf), (0, 0, 90)):
        for s in (-1, 1):
            for e in (-1, 1):
                c.cil((e * 0.9, s * 0.35, 0.25), (e * 0.9, s * 0.35, 1.0), 0.04, cromo, n=6)
                c.cil((e * 0.9, s * 0.35 - 0.05, 0.12), (e * 0.9, s * 0.35 + 0.05, 0.12), 0.11, goma, n=10)
                c.caja((e * 0.9, s * 0.35, 0.24), (0.12, 0.08, 0.06), acero, 0.01)
            c.cil((-1.0, s * 0.38, 1.0), (1.0, s * 0.38, 1.0), 0.04, cromo, n=6)
            c.cil((-0.6, s * 0.45, 1.35), (0.6, s * 0.45, 1.35), 0.025, cromo, n=6)  # barandilla
            for xx in (-0.6, 0.6):
                c.cil((xx, s * 0.45, 1.0), (xx, s * 0.45, 1.35), 0.02, cromo, n=5)
        c.caja((0, 0, 1.12), (2.0, 0.8, 0.2), colchon, 0.06)
        c.caja((-0.75, 0, 1.3), (0.4, 0.62, 0.16), sab, 0.06)
        c.lamina(lambda u, v: (-0.45 + u * 1.45, -0.42 + v * 0.84, 1.24 + 0.02 * math.sin(u * 12)), 8, 3, 0.03, sab)
        c.cil((1.0, 0.0, 1.0), (1.0, 0, 2.0), 0.025, cromo, n=6)  # gotero
        c.caja((1.0, 0.0, 1.95), (0.08, 0.2, 0.28), m.mat("liquido", "#D8EEF3"), 0.03)

    m.seccion("cruz, placa y botiquín")
    # cruz luminosa blanca en la fachada (neón dentro de un marco gris)
    cx_, cz_ = (px0 + px1) / 2, 6.95
    c.caja((cx_, YF - 0.12, cz_), (1.55, 0.18, 1.55), gris, 0.06)
    cruz.caja((cx_, YF - 0.24, cz_), (1.25, 0.08, 0.4), None, 0.02)
    cruz.caja((cx_, YF - 0.24, cz_), (0.4, 0.08, 1.25), None, 0.02)
    # cruz en el tejado sobre un pie corto (arriba del todo: 9,95 studs)
    c.caja((X1 - 1.2, 2.0, ZT + 0.6 + 0.12), (0.5, 0.5, 0.24), gris, 0.03)
    c.caja((X1 - 1.2, 2.0, ZT + 0.6 + 0.35), (0.25, 0.25, 0.3), gris, 0.02)
    with c.en((X1 - 1.2, 2.0, ZT + 0.6 + 1.08), (0, 0, 0)):
        c.caja((0, 0, 0), (0.2, 1.25, 1.25), gris, 0.04)
        cruz.caja((0.0, 0, 0), (0.28, 1.05, 0.34), None, 0.02)
        cruz.caja((0.0, 0, 0), (0.28, 0.34, 1.05), None, 0.02)
    # placa metálica con el nombre
    c.caja((px1 + 1.05, YF - 0.05, 3.6), (1.4, 0.08, 0.9), cromo, 0.02)
    tinta = m.mat("pintura", "#22323F", desgaste=0.05)
    c.texto("CLÍNICA COLONIAL", tinta, alto=0.13, grosor=0.02, c=(px1 + 1.05, YF - 0.1, 3.75), fuente="negrita")
    c.texto("Dra. Voss", tinta, alto=0.15, grosor=0.02, c=(px1 + 1.05, YF - 0.1, 3.42), fuente="serif")
    for dx in (-0.6, 0.6):
        for dz in (-0.35, 0.35):
            c.perno((px1 + 1.05 + dx, YF - 0.1, 3.6 + dz), (0, -1, 0), acero, r=0.025, arandela=False)
    # kit de emergencia: caja roja con tapa, bisagras, cierre y cruz blanca en relieve
    kx = X1 - 0.6
    c.caja((kx, YF - 0.15, 2.6), (0.9, 0.3, 1.0), rojo, 0.04)
    c.caja((kx, YF - 0.31, 2.6), (0.8, 0.03, 0.9), rojo, 0.02)
    c.caja((kx, YF - 0.34, 2.65), (0.38, 0.02, 0.12), m.mat("plastico", "#F6F6F6"), 0.0)
    c.caja((kx, YF - 0.34, 2.65), (0.12, 0.02, 0.38), m.mat("plastico", "#F6F6F6"), 0.0)
    for zz in (2.25, 2.95):
        c.cil((kx - 0.42, YF - 0.33, zz - 0.06), (kx - 0.42, YF - 0.33, zz + 0.06), 0.03, cromo, n=6)
    c.caja((kx + 0.38, YF - 0.35, 2.6), (0.06, 0.04, 0.16), cromo, 0.01)

    m.seccion("ambulancia hover")
    ax, ay = -5.6, -1.0
    with amb.en((ax, ay, 0.35)):
        # carrocería de una pieza (loft de secciones redondeadas a lo largo de Y)
        secs = []
        for y, w, h, z in ((-1.5, 1.7, 0.9, 0.55), (-1.25, 1.9, 1.35, 0.72), (-0.55, 2.0, 1.6, 0.82),
                           (1.3, 2.0, 1.62, 0.83), (1.5, 1.9, 1.5, 0.8)):
            secs.append([(math.copysign(abs(math.cos(a)) ** 0.5, math.cos(a)) * w / 2 * 0.95, y,
                          z + math.copysign(abs(math.sin(a)) ** 0.5, math.sin(a)) * h / 2) for a in
                         [i * math.tau / 14 for i in range(14)]])
        amb.loft(secs, m.mat("pintura", "#F3F3F1", desgaste=0.25, c_desgaste="#9AA0A6"))
        # cruz roja en los dos lados y en el techo (relieve)
        for s in (-1, 1):
            amb.caja((s * 0.97, 0.3, 0.95), (0.03, 0.6, 0.2), rojo, 0.0)
            amb.caja((s * 0.97, 0.3, 0.95), (0.03, 0.2, 0.6), rojo, 0.0)
            amb.caja((s * 0.96, 0.3, 0.45), (0.03, 2.6, 0.12), rojo, 0.0)  # franja
        amb.caja((0, 0.4, 1.65), (0.6, 0.2, 0.03), rojo, 0.0)
        amb.caja((0, 0.4, 1.65), (0.2, 0.6, 0.03), rojo, 0.0)
        amb_cr.loft([[(x * 0.85, -1.36, 0.95 + z) for x, z in ((-0.8, 0), (0.8, 0), (0.7, 0.4), (-0.7, 0.4))],
                     [(x * 0.85, -1.05, 0.95 + z) for x, z in ((-0.85, 0), (0.85, 0), (0.75, 0.62), (-0.75, 0.62))]], None)
        # patines de levitación y emisores
        for s in (-1, 1):
            amb.caja((s * 0.7, 0, 0.12), (0.35, 2.9, 0.18), gris, 0.05)
            for y in (-1.0, 1.0):
                amb.cil((s * 0.7, y, -0.02), (s * 0.7, y, 0.05), 0.2, acero, n=10)
                amb_n.cil((s * 0.7, y, -0.05), (s * 0.7, y, -0.02), 0.15, None, n=10)
        # rotativos y faros
        for s in (-1, 1):
            amb.cil((s * 0.55, -0.6, 1.62), (s * 0.55, -0.6, 1.7), 0.14, gris, n=8)
            amb_n.cil((s * 0.55, -0.6, 1.7), (s * 0.55, -0.6, 1.82), 0.11, None, n=8)
            amb_n.caja((s * 0.62, -1.52, 0.62), (0.3, 0.04, 0.12), None, 0.01)
        amb.caja((0, 1.52, 0.9), (1.2, 0.04, 1.0), gris, 0.02)  # portón trasero
        amb.caja((0.45, 1.56, 0.9), (0.06, 0.05, 0.3), cromo, 0.01)
    m.terminar()


MODELOS = {
    "tienda_naves": tienda_naves,
    "banco_galactico": banco_galactico,
    "restaurante": restaurante,
    "bar_cantina": bar_cantina,
    "hospital_clinica": hospital_clinica,
}
