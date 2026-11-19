"""
Zona comercial del Planeta Humano. Un modelo por función; cada una empieza con una escena limpia (Modelo()).

    python comercial.py tienda_armas [otro ...]
    python comercial.py todos
"""

import math
import sys

import arq
from ph import NEON, NEON_CLINICA, V, Modelo

ZONA = "comercial"


# ==============================================================================================================
def tienda_armas():
    m = Modelo("tienda_armas", ZONA, (12, 10, 8), 14000,
               "Armería de la colonia: fachada de paneles blindados sobre zócalo de piedra, escaparate de cristal "
               "grueso con armas expuestas, puerta automática corredera y cartel ARMAS en neón.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#9CC8DC", transparencia=0.35)
    neon = m.parte("cartel_neon", tipo="neon", color=NEON)
    luces = m.parte("luces_neon", tipo="neon", color=NEON)

    panel = m.mat("paneles", "#34465A", tam_panel=(2.0, 1.75), desgaste=0.5)
    panel_osc = m.mat("paneles", "#252F3B", tam_panel=(1.0, 1.0), desgaste=0.35)
    piedra = m.mat("piedra", "#8D877C")
    hormigon = m.mat("hormigon", "#9C978E")
    acero = m.mat("metal", "#7E848C")
    acero_osc = m.mat("metal", "#3C4148", rug=0.5)
    cromo = m.mat("cromo", "#C9CED4")
    naranja = m.mat("pintura", "#D9822B", desgaste=0.7)
    madera = m.mat("madera", "#6E4A2E", eje="X")
    madera_v = m.mat("madera", "#5A3A22", eje="Z")
    grip = m.mat("grip", "#6F757D")
    goma = m.mat("goma", "#1E1F22")
    cuero = m.mat("cuero", "#4A2C1A")
    laton = m.mat("metal", "#B08A3E", rug=0.35)
    hoja = m.mat("cromo", "#D7DCE2", rug=0.12)
    fondo = m.mat("madera", "#8A6440", eje="Z", suciedad=0.25)
    textil = m.mat("tela", "#9A2E26", suciedad=0.1)
    pint_roja = m.mat("pintura", "#8E2A22", desgaste=0.6)

    X0, X1 = -6.0, 6.0
    YF, YB = -4.2, 4.85  # cara exterior del muro delantero y trasero
    G = 0.4  # grosor del muro
    Z0 = 0.45  # suelo interior (encima del zócalo)
    ZT = 7.2  # alto del muro

    m.seccion("zócalo, acera y escalón")
    # ---- zócalo, acera y escalón ----
    c.caja_de((X0 - 0.15, YF - 0.15, 0), (X1 + 0.15, YB + 0.15, Z0), hormigon, 0.05)
    # piedra del zócalo (sillares con juntas: cada uno es una pieza)
    xs = [X0, -4.6, -3.0, -1.5, 0.6]
    for i in range(len(xs) - 1):
        c.caja_de((xs[i] + 0.03, YF - 0.12, Z0), (xs[i + 1] - 0.03, YF + 0.1, 1.15), piedra, 0.06)
    c.caja_de((4.6 + 0.03, YF - 0.12, Z0), (X1 - 0.03, YF + 0.1, 1.15), piedra, 0.06)
    for x_lado in (X0, X1):
        for k, (ya, yb) in enumerate([(YF, -1.6), (-1.6, 1.6), (1.6, YB)]):
            sx = -1 if x_lado < 0 else 1
            c.caja_de((x_lado - sx * 0.1 if sx > 0 else x_lado - 0.12, ya + 0.03, Z0),
                      (x_lado + 0.12 if sx > 0 else x_lado + 0.1, yb - 0.03, 1.15), piedra, 0.06)
    # escalón con alfombra antideslizante
    c.caja_de((-0.65, YF - 0.8, 0), (6.05, YF + 0.02, Z0 - 0.02), hormigon, 0.04)
    c.caja_de((0.45, YF - 0.7, Z0 - 0.03), (4.55, YF - 0.05, Z0 + 0.01), grip, 0.01)
    for x in (0.55, 4.45):
        for y in (YF - 0.6, YF - 0.15):
            c.perno((x, y, Z0 + 0.01), (0, 0, 1), acero, r=0.03, arandela=False)

    m.seccion("muros")
    # ---- muros ----
    ESC = (-5.2, -0.7, 1.4, 5.6)  # escaparate x0, x1, z0, z1
    PUE = (1.0, 4.4, Z0, 6.2)  # puerta
    arq.muro_huecos(c, X0, X1, 1.15, ZT, YF, YF + G, [ESC, PUE], panel)
    c.caja_de((PUE[0], YF, Z0), (PUE[1], YF + G, 1.15), hormigon, 0.02)  # umbral bajo la puerta (hueco hasta suelo)
    # (el muro arranca a 1,15: bajo la puerta se rellena el zócalo como umbral)
    c.caja_de((X0, YB - G, 1.15), (X1, YB, ZT), panel)  # trasero
    for x in (X0, X1 - G):
        c.caja_de((x, YF + G, 1.15), (x + G, YB - G, ZT), panel)
    # pilares de esquina reforzados con pernos
    for x in (X0 - 0.12, X1 + 0.12):
        for y in (YF - 0.12, YB + 0.12):
            c.caja((x, y, (1.15 + ZT + 0.3) / 2), (0.55, 0.55, ZT + 0.3 - 1.15), acero_osc, 0.06)
            for zz in (2.0, 4.0, 6.0):
                for sgn in (-1, 1):
                    c.perno((x + sgn * 0.15, y - 0.28 if y < 0 else y + 0.28, zz), (0, -1 if y < 0 else 1, 0), acero,
                            r=0.04)
    # cornisa de madera con vigas que asoman (el toque de pueblo)
    c.caja_de((X0 - 0.3, YF - 0.35, ZT), (X1 + 0.3, YB + 0.3, ZT + 0.3), madera, 0.05)
    for i in range(9):
        x = X0 + 0.4 + i * (X1 - X0 - 0.8) / 8
        c.caja_de((x - 0.13, YF - 0.6, ZT - 0.25), (x + 0.13, YF + 0.2, ZT), madera_v, 0.04)
    # pretil y tejado
    c.caja_de((X0 - 0.2, YF - 0.25, ZT + 0.3), (X1 + 0.2, YB + 0.2, ZT + 0.45), hormigon, 0.04)
    for (a, b) in [((X0 - 0.2, YF - 0.25), (X1 + 0.2, YF + 0.05)), ((X0 - 0.2, YB - 0.1), (X1 + 0.2, YB + 0.2)),
                   ((X0 - 0.2, YF + 0.05), (X0 + 0.1, YB - 0.1)), ((X1 - 0.1, YF + 0.05), (X1 + 0.2, YB - 0.1))]:
        c.caja_de((a[0], a[1], ZT + 0.45), (b[0], b[1], 7.95), panel_osc, 0.03)
    # tejado: lámina impermeable con solapes, sumidero y respiraderos bajos (no asoman del pretil)
    c.caja_de((X0 + 0.1, YF + 0.05, ZT + 0.45), (X1 - 0.1, YB - 0.1, ZT + 0.5), m.mat("goma", "#2A2C30", lluvia=0.4))
    for k in range(1, 6):
        y = YF + 0.05 + k * (YB - YF - 0.15) / 6
        c.caja_de((X0 + 0.1, y - 0.06, ZT + 0.5), (X1 - 0.1, y + 0.06, ZT + 0.52), m.mat("goma", "#232528"))
    for (x, y) in ((-3.5, 2.5), (3.0, 2.8)):
        c.cil((x, y, ZT + 0.5), (x, y, ZT + 0.85), 0.16, acero, n=8)
        c.cil((x, y, ZT + 0.85), (x, y, ZT + 0.95), 0.28, acero_osc, n=8, r1=0.05)
    c.cil((4.8, YB - 0.6, ZT + 0.46), (4.8, YB - 0.6, ZT + 0.55), 0.25, acero_osc, n=10)
    m.seccion("escaparate")
    # ---- escaparate ----
    x0, x1, z0, z1 = ESC
    arq.marco(c, x0, x1, z0, z1, YF, 0.18, 0.16, acero_osc)
    c.caja_de((x0 - 0.3, YF - 0.42, z0 - 0.22), (x1 + 0.3, YF + 0.05, z0 - 0.06), piedra, 0.05)  # alféizar
    # parteluz
    c.caja_de(((x0 + x1) / 2 - 0.06, YF - 0.05, z0), ((x0 + x1) / 2 + 0.06, YF + 0.12, z1), acero_osc, 0.015)
    cr.caja_de((x0 + 0.02, YF + 0.04, z0 + 0.02), (x1 - 0.02, YF + 0.19, z1 - 0.02), None)  # cristal de 0,15
    # tornillería del marco
    for k in range(5):
        x = x0 + (x1 - x0) * k / 4
        for zz in (z0 - 0.09, z1 + 0.09):
            c.perno((x, YF - 0.16, zz), (0, -1, 0), cromo, r=0.03, arandela=False)
    # nicho de exposición detrás del escaparate
    YN = YF + G
    c.caja_de((x0 - 0.1, YN, z0 - 0.4), (x1 + 0.1, YN + 2.2, z0), madera, 0.02)  # tarima
    c.caja_de((x0 - 0.2, YN + 2.2, z0 - 0.4), (x1 + 0.2, YN + 2.4, z1 + 0.3), fondo, 0.02)  # fondo
    for x in (x0 - 0.2, x1):
        c.caja_de((x, YN, z0 - 0.4), (x + 0.2, YN + 2.4, z1 + 0.3), fondo)
    c.caja_de((x0 - 0.2, YN, z1), (x1 + 0.2, YN + 2.4, z1 + 0.3), fondo)
    # tela roja de fondo (lienzo colgado con pliegues)
    c.lamina(lambda u, v: (x0 + 0.4 + u * (x1 - x0 - 0.8), YN + 2.12 + 0.05 * math.sin(u * 18),
                           z0 + 0.6 + v * (z1 - z0 - 0.9)), 16, 2, 0.03, textil)
    c.cil((x0 + 0.3, YN + 2.1, z1 - 0.25), (x1 - 0.3, YN + 2.1, z1 - 0.25), 0.04, laton, n=8)
    # 2 espadas cruzadas sobre una placa de madera (pared del fondo)
    cxs = x0 + 1.25
    with c.en((cxs, YN + 2.0, 3.55)):
        c.extruir([(math.cos(a) * 0.85, math.sin(a) * 1.05) for a in
                   [math.radians(d) for d in range(0, 360, 30)]], 0.08, madera, rot=(90, 0, 0), b=0.02)
        for ang in (38, -38):
            with c.en((0, -0.12, 0), (0, ang, 0)):
                with c.en((0, 0, -1.25), None):
                    arq.espada(c, hoja, laton, laton, cuero, largo=2.5, ancho=0.2)
        for ang in (0, 120, 240):
            a = math.radians(ang + 90)
            c.perno((math.cos(a) * 0.65, -0.05, math.sin(a) * 0.8), (0, -1, 0), laton, r=0.035)
    # escudo redondo sobre pedestal
    cxp = x1 - 1.35
    c.torno([(0.0, 0), (0.42, 0), (0.42, 0.08), (0.3, 0.12), (0.22, 0.18), (0.18, 1.3), (0.26, 1.36),
             (0.3, 1.42), (0.0, 1.42)], piedra, n=12, c=(cxp, YN + 1.1, z0))
    with c.en((cxp, YN + 1.05, z0 + 1.42 + 0.95), (90, 0, 0)):
        c.torno([(0.0, 0.16), (0.32, 0.13), (0.78, 0.04), (0.88, 0.0), (0.88, -0.07), (0.8, -0.05), (0.32, 0.04),
                 (0.0, 0.07)], pint_roja, n=16)
        c.toro((0, 0, -0.01), 0.88, 0.05, acero, n=16, m=5)
        c.esfera((0, 0, 0.16), 0.18, acero, seg=12, anillos=6, esc=(1, 1, 0.7))
        for k in range(10):
            a = math.tau * k / 10
            c.remache((math.cos(a) * 0.76, math.sin(a) * 0.76, 0.05), (0, 0, 1), laton, r=0.04)
        # franja diagonal
        c.caja((0, 0, 0.1), (1.6, 0.18, 0.03), naranja, 0.01, rot=(0, 0, 40))
    # soporte del escudo
    c.caja((cxp, YN + 1.12, z0 + 1.6), (0.5, 0.18, 0.4), acero_osc, 0.03)
    # rifle colgado de un gancho en el lateral del nicho
    gx = x0 + 2.55
    c.tubo([(gx, YN + 2.2, 4.9), (gx, YN + 1.95, 4.9), (gx, YN + 1.85, 4.75), (gx, YN + 1.92, 4.62)], 0.035, acero,
           n=6, seg=3)
    with c.en((gx, YN + 1.9, 4.05), (0, 72, 0)):
        c.caja((0.0, 0, 0), (1.3, 0.12, 0.22), acero_osc, 0.03)  # cajón
        c.caja((-0.85, 0, -0.05), (0.6, 0.1, 0.26), madera, 0.04)  # culata
        c.caja((0.25, 0, -0.22), (0.14, 0.09, 0.32), acero_osc, 0.02, rot=(0, -12, 0))  # cargador
        c.caja((-0.25, 0, -0.18), (0.12, 0.09, 0.22), cuero, 0.02, rot=(0, 15, 0))  # empuñadura
        c.cil((0.65, 0, 0.04), (1.25, 0, 0.04), 0.045, acero_osc, n=8)  # cañón
        c.cil((1.25, 0, 0.04), (1.35, 0, 0.04), 0.06, acero, n=8)  # bocacha
        c.cil((-0.2, 0, 0.18), (0.35, 0, 0.18), 0.05, acero_osc, n=8)  # mira
        c.cil((-0.2, 0, 0.18), (-0.24, 0, 0.18), 0.06, cromo, n=8)
        luces.caja((0.2, -0.065, 0.02), (0.5, 0.01, 0.04), None)  # celda de energía
    # luz del nicho (tubo neón bajo el dintel)
    luces.cil((x0 + 0.2, YN + 0.3, z1 + 0.18), (x1 - 0.2, YN + 0.3, z1 + 0.18), 0.04, None, n=8)

    m.seccion("puerta corredera automática")
    # ---- puerta corredera automática ----
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.2, 0.18, acero_osc, abajo=False)
    # raíl visible sobre la puerta (perfil en U) de lado a lado: las dos hojas se abren hacia fuera
    RX0, RX1 = -0.55, 5.95
    c.caja_de((RX0, YF - 0.42, pz1 + 0.2), (RX1, YF - 0.18, pz1 + 0.32), acero, 0.02)
    c.caja_de((RX0, YF - 0.42, pz1 + 0.32), (RX1, YF - 0.18, pz1 + 0.36), acero_osc, 0.01)
    for x in (RX0 + 0.06, RX1 - 0.06):
        c.caja((x, YF - 0.3, pz1 + 0.26), (0.08, 0.26, 0.2), acero_osc, 0.01)
    for x in (RX0 + 0.5, (px0 + px1) / 2, RX1 - 0.5):
        c.caja((x, YF - 0.2, pz1 + 0.26), (0.12, 0.2, 0.26), acero, 0.01)
        c.perno((x, YF - 0.43, pz1 + 0.26), (0, -1, 0), acero, r=0.03)
    # guía del suelo
    c.caja_de((RX0, YF - 0.36, Z0 - 0.02), (RX1, YF - 0.24, Z0 + 0.03), acero, 0.008)
    # caja del motor con su manguera de cables
    c.caja(((px0 + px1) / 2, YF - 0.32, pz1 + 0.58), (1.4, 0.4, 0.4), acero_osc, 0.05)
    c.caja(((px0 + px1) / 2 + 0.45, YF - 0.53, pz1 + 0.58), (0.3, 0.02, 0.12), naranja, 0.005)
    c.tubo([((px0 + px1) / 2 - 0.7, YF - 0.3, pz1 + 0.6), ((px0 + px1) / 2 - 0.95, YF - 0.25, pz1 + 0.55),
            ((px0 + px1) / 2 - 1.0, YF - 0.1, pz1 + 0.75), ((px0 + px1) / 2 - 1.0, YF - 0.04, ZT - 0.3)], 0.035, goma,
           n=6, seg=3)
    # dos hojas (piezas aparte): marco metálico, cristal, tirador y franja de aviso
    H = pz1 - pz0 - 0.05
    py = YF - 0.3
    W = (px1 - px0) / 2 + 0.02
    for lado, (hx0, sent) in {"izq": (px0, -1), "der": (px1 - W, 1)}.items():
        piv = (hx0 + W / 2, py, pz0)
        h = m.parte(f"puerta_{lado}", pivote=piv,
                    nota=f"Hoja corredera. Abrir: desplazar {W - 0.05:.2f} studs hacia el exterior del hueco.")
        hc = m.parte(f"puerta_{lado}_cristal", tipo="cristal", color="#A9CFE0", pivote=piv, transparencia=0.45)
        y0, y1 = (py - 0.06, py + 0.06) if lado == "izq" else (py - 0.02, py + 0.1)
        h.caja_de((hx0, y0, pz0 + 0.02), (hx0 + W, y1, pz0 + 0.45), acero_osc, 0.02)
        h.caja_de((hx0, y0, pz0 + H - 0.3), (hx0 + W, y1, pz0 + H), acero_osc, 0.02)
        h.caja_de((hx0, y0, pz0 + 0.45), (hx0 + 0.16, y1, pz0 + H - 0.3), acero_osc, 0.02)
        h.caja_de((hx0 + W - 0.16, y0, pz0 + 0.45), (hx0 + W, y1, pz0 + H - 0.3), acero_osc, 0.02)
        h.caja_de((hx0 + 0.16, y0 + 0.01, pz0 + 2.6), (hx0 + W - 0.16, y1 - 0.01, pz0 + 2.75), acero_osc, 0.01)
        h.caja_de((hx0 + 0.16, y0 - 0.015, pz0 + 0.2), (hx0 + W - 0.16, y0, pz0 + 0.38), naranja, 0.005)
        xt = hx0 + W - 0.32 if lado == "izq" else hx0 + 0.32
        h.cil((xt, y0 - 0.1, pz0 + 1.9), (xt, y0 - 0.1, pz0 + 3.4), 0.035, cromo, n=8)
        for zz in (pz0 + 2.0, pz0 + 3.3):
            h.cil((xt, y0 - 0.1, zz), (xt, y0, zz), 0.025, cromo, n=6)
        for x in (hx0 + 0.3, hx0 + W - 0.3):
            h.caja((x, (y0 + y1) / 2, pz0 + H + 0.12), (0.12, 0.08, 0.3), acero, 0.01)
            h.cil((x, (y0 + y1) / 2 - 0.08, pz0 + H + 0.26), (x, (y0 + y1) / 2 + 0.08, pz0 + H + 0.26), 0.08, goma,
                  n=10)
        hc.caja_de((hx0 + 0.16, (y0 + y1) / 2 - 0.03, pz0 + 0.45), (hx0 + W - 0.16, (y0 + y1) / 2 + 0.03,
                                                                     pz0 + H - 0.3), None)
        m.anclaje(f"PuertaAbierta_{lado}", (piv[0] + sent * (W - 0.05), py, pz0),
                  "Pivote de la hoja con la puerta abierta.")
    # vestíbulo detrás de la puerta: suelo, paredes y mostrador al fondo
    YV = YF + G
    c.caja_de((px0, YV, Z0 - 0.05), (px1, YV + 3.4, Z0), madera, 0.01)
    c.caja_de((px0 - 0.2, YV + 3.4, Z0), (px1 + 0.2, YV + 3.6, ZT), panel_osc)
    c.caja_de((px1, YV, Z0), (px1 + 0.2, YV + 3.4, ZT), panel_osc)
    c.caja_de((px0 - 0.2, YV, Z0), (px0, YV + 3.4, ZT), panel_osc)
    c.caja_de((px0 - 0.2, YV, pz1 + 0.6), (px1 + 0.2, YV + 3.4, pz1 + 0.8), panel_osc)
    c.caja_de((px0 + 0.2, YV + 2.2, Z0), (px1 - 0.2, YV + 3.0, Z0 + 1.9), madera, 0.05)  # mostrador
    c.caja_de((px0 + 0.1, YV + 2.1, Z0 + 1.9), (px1 - 0.1, YV + 3.1, Z0 + 2.05), acero_osc, 0.03)
    # armero de pared al fondo (soportes con lanzas)
    for k in range(4):
        x = px0 + 0.6 + k * 0.75
        c.cil((x, YV + 3.35, Z0 + 2.3), (x, YV + 3.35, Z0 + 5.4), 0.035, acero, n=6)
        c.cil((x, YV + 3.35, Z0 + 5.4), (x, YV + 3.35, Z0 + 5.75), 0.07, hoja, n=4, r1=0.0)
    c.caja_de((px0 + 0.3, YV + 3.25, Z0 + 3.0), (px1 - 0.3, YV + 3.4, Z0 + 3.15), madera, 0.02)
    luces.cil((px0 + 0.3, YV + 1.5, pz1 + 0.55), (px1 - 0.3, YV + 1.5, pz1 + 0.55), 0.04, None, n=8)

    # rejas de seguridad plegadas a los lados del escaparate y de la puerta
    arq.reja_plegada(c, x0 - 0.62, YF - 0.06, z0 - 0.1, z1 + 0.1, acero_osc, hojas=6, ancho=0.4)
    arq.reja_plegada(c, x1 + 0.6, YF - 0.06, z0 - 0.1, z1 + 0.1, acero_osc, hojas=6, ancho=0.4)
    arq.reja_plegada(c, px1 - 0.3, YF + 0.05, Z0 + 0.1, pz1 - 0.1, acero_osc, hojas=5, ancho=0.3, salida=1)

    m.seccion("cartel ARMAS")
    # ---- cartel ARMAS ----
    cx = (px0 + px1) / 2
    cz = pz1 + 0.75
    # caja de fondo con soportes, y las letras en neón sobre ella
    c.caja((cx, YF - 0.62, cz + 0.05), (4.2, 0.14, 1.05), panel_osc, 0.04)
    for x in (cx - 1.8, cx + 1.8):
        c.caja((x, YF - 0.35, cz + 0.05), (0.1, 0.45, 0.1), acero, 0.01)
        c.perno((x, YF - 0.7, cz + 0.35), (0, -1, 0), acero, r=0.03)
        c.perno((x, YF - 0.7, cz - 0.25), (0, -1, 0), acero, r=0.03)
    neon.texto("ARMAS", None, alto=0.8, grosor=0.08, c=(cx, YF - 0.73, cz - 0.33), fuente="estrecha",
               espaciado=1.08)
    # canal de los tubos detrás de las letras (soportes)
    c.caja((cx, YF - 0.7, cz - 0.36), (3.8, 0.05, 0.05), acero, 0.01)

    m.seccion("cámara de seguridad y focos")
    # ---- cámara de seguridad y focos ----
    arq.camara_seguridad(c, luces, (px1 + 0.55, YF, 6.0), m.mat("plastico", "#D9DCDF"), acero, goma)
    arq.foco_pared(c, luces, (px0 - 0.6, YF, 4.6), acero_osc, acero)
    arq.foco_pared(c, luces, (x0 - 0.6, YF, 5.0), acero_osc, acero)

    m.seccion("detalles de fachada")
    # ---- detalles de fachada ----
    arq.bajante(c, X1 - 0.6, YF, ZT + 0.2, acero, acero_osc)
    # caja eléctrica con conducto
    c.caja((X1 - 1.4, YF - 0.12, 2.2), (0.6, 0.24, 0.8), acero, 0.04)
    c.caja((X1 - 1.4, YF - 0.25, 2.2), (0.5, 0.02, 0.06), naranja, 0.005)
    c.tubo([(X1 - 1.4, YF - 0.1, 2.6), (X1 - 1.4, YF - 0.1, ZT - 0.2)], 0.04, acero_osc, n=6, suave=False)
    # placa de horario de latón junto a la puerta
    c.caja((px1 + 0.55, YF - 0.03, 3.4), (0.5, 0.06, 0.7), laton, 0.02)
    c.texto("ABIERTO", m.mat("pintura", "#20252B", desgaste=0.1), alto=0.08, grosor=0.02,
            c=(px1 + 0.55, YF - 0.07, 3.5), fuente="estrecha")
    # laterales: ventanuco enrejado y conductos
    for sx in (-1, 1):
        xw = X1 + 0.02 if sx > 0 else X0 - 0.02
        c.caja((xw, 1.0, 4.4), (0.06, 1.6, 1.0), acero_osc, 0.03)
        for k in range(5):
            c.cil((xw + sx * 0.06, 0.3 + k * 0.35, 4.0), (xw + sx * 0.06, 0.3 + k * 0.35, 4.8), 0.03, acero, n=6)
        c.caja((xw, -2.5, 6.0), (0.3, 0.8, 0.5), acero, 0.04)
        for k in range(4):
            c.caja((xw + sx * 0.16, -2.5, 5.82 + k * 0.12), (0.02, 0.7, 0.05), acero_osc, 0.005)
    # puerta trasera de servicio
    c.caja_de((-1.2, YB, Z0), (0.4, YB + 0.12, 5.6), acero_osc, 0.04)
    c.caja_de((-1.4, YB, 5.6), (0.6, YB + 0.18, 5.8), acero, 0.02)
    c.cil((0.2, YB + 0.12, 2.9), (0.2, YB + 0.24, 2.9), 0.05, cromo, n=8)
    c.caja_de((-1.0, YB + 0.12, 4.6), (0.2, YB + 0.14, 5.2), naranja, 0.005)

    m.notas += [
        "Puerta: pieza tienda_armas_puerta + tienda_armas_puerta_cristal con el mismo pivote. Para abrir, mover "
        "ambas hacia la izquierda del modelo (X de Roblox +) hasta el anclaje PuertaAbierta.",
        "Las letras ARMAS van en tienda_armas_cartel_neon; el resto de luces (nicho, vestíbulo, focos, cámara, "
        "celda del rifle) en tienda_armas_luces_neon.",
    ]
    m.terminar()


MODELOS = {
    "tienda_armas": tienda_armas,
}

if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    nombres = list(MODELOS) if args == ["todos"] else args
    for n in nombres:
        MODELOS[n]()
