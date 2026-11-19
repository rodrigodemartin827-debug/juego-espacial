"""Zona del hangar: hangar principal, plataforma, brazo, consola, rack, manguera, baliza, escalera, caja de
herramientas, pantalla de estado, extintor y contenedor grande."""

import math

import arq
from ph import NEON, V, Modelo

ZONA = "hangar"


def _letra_h(c, mat, cx, cy, z, alto, grosor=0.012):
    """H de helipuerto en relieve finísimo (pintura con grosor)."""
    w = alto * 0.7
    c.caja((cx - w / 2 + alto * 0.08, cy, z), (alto * 0.16, alto, grosor), mat, 0.0)
    c.caja((cx + w / 2 - alto * 0.08, cy, z), (alto * 0.16, alto, grosor), mat, 0.0)
    c.caja((cx, cy, z), (w, alto * 0.16, grosor), mat, 0.0)


# ==============================================================================================================
def hangar_principal():
    m = Modelo("hangar_principal", ZONA, (24, 20, 14), 18000,
               "Hangar principal, el edificio más grande: puerta gigante motorizada que sube por guías (pieza "
               "aparte, con motor y cadenas), dos grúas puente sobre raíl, marcas de aterrizaje, líneas amarillas, "
               "8 pantallas de luz, 4 columnas en H, panel de apertura y señalización BAHÍA 1.")
    c = m.parte()
    puerta = m.parte("puerta", pivote=(0, -9.6, 0.3), nota="Portón de hangar: sube 10,5 studs (Y de Roblox) por las "
                                                         "guías laterales. Ver anclaje PuertaAbierta.")
    grua1 = m.parte("grua_1", pivote=(0, -3.0, 11.6), nota="Grúa puente 1: se desplaza a lo largo del raíl (Z de Roblox).")
    grua2 = m.parte("grua_2", pivote=(0, 4.0, 11.6), nota="Grúa puente 2: se desplaza a lo largo del raíl (Z de Roblox).")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    pantallas = m.parte("lamparas_neon", tipo="neon", color="#F2FBFF", nota="Difusores de las 8 lámparas de techo.")
    cr = m.parte("cristal", tipo="cristal", color="#9CC2D2", transparencia=0.35)

    panel = m.mat("paneles", "#C3C8CD", tam_panel=(3.0, 2.0), desgaste=0.4, c_desgaste="#7A8087", lluvia=0.5)
    gris = m.mat("pintura", "#4A525C", desgaste=0.5)
    osc = m.mat("metal", "#2B3035", rug=0.5)
    acero = m.mat("metal", "#848A91")
    amar = m.mat("pintura", "#E3B22A", desgaste=0.55)
    negro = m.mat("pintura", "#1E2125", desgaste=0.3)
    suelo = m.mat("hormigon", "#7C7A76", suciedad=0.5, manchas=[(2.0, 2.0, 0.3, 2.5, "#1a1612", 0.6),
                                                              (-4.0, -2.0, 0.3, 1.2, "#0d0b09", 0.6),
                                                              (5.0, 5.0, 0.3, 1.0, "#14110e", 0.5)])
    pint_suelo = m.mat("pintura", "#E3B22A", desgaste=0.7, c_desgaste="#7C7A76", aranazos=0.0)
    blanco_s = m.mat("pintura", "#E8E6E0", desgaste=0.7, c_desgaste="#7C7A76", aranazos=0.0)
    rojo = m.mat("plastico", "#D02A22")
    verde = m.mat("plastico", "#2EA04E")
    cadena = m.mat("metal", "#5A5E63", rug=0.5, bump=0.7, patron="tejido")
    naranja = m.mat("pintura", "#E07A1F", desgaste=0.6)

    X0, X1, YF, YB, Z0, ZT = -12.0, 12.0, -9.4, 10.0, 0.3, 12.6

    m.seccion("solera, muros y cubierta")
    c.caja_de((X0 - 0.3, YF - 0.6, 0), (X1 + 0.3, YB + 0.3, Z0), suelo, 0.05)
    PUE = (-9.0, 9.0, Z0, 10.6)
    arq.muro_huecos(c, X0, X1, Z0, ZT, YF, YF + 0.5, [PUE], panel)
    for x in (X0, X1 - 0.5):
        c.caja_de((x, YF + 0.5, Z0), (x + 0.5, YB - 0.5, ZT), panel)
    c.caja_de((X0, YB - 0.5, Z0), (X1, YB, ZT), panel)
    # ventanales altos laterales
    for x, s in ((X0 - 0.02, -1), (X1 + 0.02, 1)):
        for y in (-4.0, 1.0, 6.0):
            c.caja((x, y, 10.2), (0.1, 3.4, 1.6), gris, 0.03)
            cr.caja((x + s * 0.04, y, 10.2), (0.06, 3.1, 1.3), None)
    # cubierta a dos aguas muy tendida con lucernario corrido
    cum = ZT + 1.3
    for s in (-1, 1):
        x_al = X0 - 0.4 if s < 0 else X1 + 0.4
        a = V((x_al, 0, ZT - 0.1))
        b = V((s * 1.5, 0, cum))
        d = b - a
        ang = math.degrees(math.atan2(d.z, abs(d.x)))
        with c.en(((a + b) / 2) + V((0, (YF + YB) / 2, 0.08)), (0, -s * ang, 0)):
            c.caja((0, 0, 0), (d.length, YB - YF + 0.8, 0.16), gris, 0.04)
            for k in range(9):
                c.caja((0, -(YB - YF) / 2 + k * (YB - YF) / 8, 0.12), (d.length, 0.08, 0.1), osc)
    cr.caja((0, (YF + YB) / 2, cum + 0.1), (3.0, YB - YF - 1.0, 0.12), None)
    for s in (-1, 1):
        c.extruir([(X0, ZT), (X1, ZT), (1.5, cum), (-1.5, cum)], 0.5, panel,
                  c=(0, YF + 0.25 if s < 0 else YB - 0.25, 0), rot=(90, 0, 0))
    # pilastras de la fachada
    for x in (X0 + 0.3, PUE[0] - 0.8, PUE[1] + 0.8, X1 - 0.3):
        arq.viga_h(c, (x, YF - 0.2, Z0), (x, YF - 0.2, ZT + 0.2), 0.5, 0.45, gris)

    m.seccion("portón motorizado")
    px0, px1, pz0, pz1 = PUE
    # guías laterales (perfil en U) que suben por encima del hueco y dintel con el motor
    for s, x in ((-1, px0 - 0.25), (1, px1 + 0.25)):
        c.caja((x, YF - 0.35, (pz0 + ZT) / 2), (0.5, 0.5, ZT - pz0), osc, 0.04)
        c.caja((x - s * 0.18, YF - 0.62, (pz0 + ZT) / 2), (0.14, 0.06, ZT - pz0), acero, 0.01)
    c.caja((0, YF - 0.55, pz1 + 0.6), (px1 - px0 + 1.0, 0.8, 0.9), gris, 0.06)
    # motor y reductora en el centro del dintel, con eje y piñones de cadena a los lados
    c.cil((-0.9, YF - 1.25, pz1 + 0.9), (0.9, YF - 1.25, pz1 + 0.9), 0.38, m.mat("pintura", "#2E5A8A", desgaste=0.4), n=16)
    for k in range(7):
        c.cil((-0.7 + k * 0.22, YF - 1.25, pz1 + 0.9), (-0.66 + k * 0.22, YF - 1.25, pz1 + 0.9), 0.43,
              m.mat("pintura", "#2E5A8A"), n=16)
    c.caja((1.3, YF - 1.25, pz1 + 0.9), (0.8, 0.7, 0.7), osc, 0.05)
    c.cil((px0 + 0.2, YF - 1.25, pz1 + 0.9), (px1 - 0.2, YF - 1.25, pz1 + 0.9), 0.08, acero, n=8)
    for x in (px0 + 0.4, px1 - 0.4):
        c.cil((x - 0.06, YF - 1.25, pz1 + 0.9), (x + 0.06, YF - 1.25, pz1 + 0.9), 0.3, osc, n=14)
        c.caja((x, YF - 1.2, pz1 + 0.6), (0.3, 0.4, 1.0), gris, 0.03)
        # cadena: cae del piñón hasta la puerta (eslabones alternos)
        for k in range(10):
            z = pz1 + 0.6 - k * 0.12
            c.toro((x, YF - 1.55, z), 0.05, 0.015, cadena, n=6, m=3, rot=(0, 90 * (k % 2), 0))
    # hoja del portón: paneles horizontales con nervios, ventanillas y franjas de aviso
    nfil = 7
    hz = (pz1 - pz0) / nfil
    for k in range(nfil):
        z = pz0 + k * hz
        puerta.caja_de((px0 + 0.05, YF - 0.75, z + 0.02), (px1 - 0.05, YF - 0.5, z + hz - 0.02), panel, 0.05)
        puerta.caja_de((px0 + 0.2, YF - 0.8, z + hz * 0.45), (px1 - 0.2, YF - 0.74, z + hz * 0.55), acero, 0.01)
        if k == 4:
            for j in range(6):
                x = px0 + 1.4 + j * (px1 - px0 - 2.8) / 5
                puerta.caja((x, YF - 0.76, z + hz / 2), (1.3, 0.06, 0.65), osc, 0.03)
                cr.caja((x, YF - 0.6, z + hz / 2), (1.1, 0.06, 0.5), None)
    for j in range(18):
        x = px0 + 0.5 + j * (px1 - px0 - 1.0) / 17
        puerta.caja((x, YF - 0.8, pz0 + 0.3), (0.5, 0.03, 0.36), amar if j % 2 else negro, 0.0, rot=(0, 30, 0))
    for x in (px0 + 0.4, px1 - 0.4):
        puerta.cil((x, YF - 0.62, pz1 - 0.3), (x, YF - 0.88, pz1 - 0.3), 0.12, osc, n=10)  # rodillos de guía
        puerta.cil((x, YF - 0.62, pz0 + 0.5), (x, YF - 0.88, pz0 + 0.5), 0.12, osc, n=10)
    puerta.caja_de((px0 + 0.05, YF - 0.75, pz0), (px1 - 0.05, YF - 0.5, pz0 + 0.06), m.mat("goma", "#151618"), 0.01)
    m.anclaje("PuertaAbierta", (0, YF - 0.6, pz0 + 10.5), "Pivote del portón subido del todo.")
    # panel de control junto a la puerta con botón grande de apertura
    cpx = px1 + 1.4
    c.caja((cpx, YF - 0.25, 3.0), (0.9, 0.3, 1.3), gris, 0.05)
    c.caja((cpx, YF - 0.41, 3.25), (0.7, 0.02, 0.6), osc, 0.0)
    luces.caja((cpx, YF - 0.43, 3.32), (0.5, 0.01, 0.35), None)
    c.cil((cpx - 0.15, YF - 0.4, 2.65), (cpx - 0.15, YF - 0.55, 2.65), 0.15, amar, n=14)
    c.cil((cpx - 0.15, YF - 0.55, 2.65), (cpx - 0.15, YF - 0.65, 2.65), 0.12, verde, n=14)
    c.cil((cpx + 0.25, YF - 0.4, 2.65), (cpx + 0.25, YF - 0.5, 2.65), 0.08, rojo, n=10)
    c.tubo([(cpx, YF - 0.15, 3.65), (cpx, YF - 0.15, 4.5), (cpx - 0.6, YF - 0.12, 5.0), (px1 + 0.5, YF - 0.12, 8.0)],
           0.05, m.mat("goma", "#151618"), n=5, seg=3)

    m.seccion("suelo: marcas")
    zs = Z0 + 0.006
    # círculo con H y anillo de aproximación
    c.toro((0, 1.0, zs), 5.2, 0.18, pint_suelo, n=40, m=3, rot=None)
    _letra_h(c, blanco_s, 0, 1.0, zs, 4.0)
    # líneas de seguridad amarillas y flechas de dirección
    for s in (-1, 1):
        c.caja((s * 8.6, 0.3, zs), (0.25, YB - YF - 2.0, 0.012), pint_suelo, 0.0)
    for k in range(3):
        y = YF + 1.2 + k * 1.4
        c.extruir([(-0.5, 0), (0.5, 0), (0.5, 0.6), (0.9, 0.6), (0.0, 1.3), (-0.9, 0.6), (-0.5, 0.6)], 0.012, blanco_s,
                  c=(0, y, zs))
    # franja de peligro bajo la puerta
    for j in range(24):
        x = px0 + 0.4 + j * (px1 - px0 - 0.8) / 23
        c.caja((x, YF + 0.75, zs), (0.35, 0.5, 0.012), pint_suelo if j % 2 else negro, 0.0, rot=(0, 0, 35))

    m.seccion("columnas, raíles y grúas")
    for x in (-6.0, 6.0):
        for y in (-2.5, 5.5):
            arq.viga_h(c, (x, y, Z0), (x, y, 11.2), 0.55, 0.5, amar)
            c.caja((x, y, Z0 + 0.05), (0.9, 0.9, 0.1), acero, 0.01)
            for dx in (-0.3, 0.3):
                for dy in (-0.3, 0.3):
                    c.perno((x + dx, y + dy, Z0 + 0.1), (0, 0, 1), acero, r=0.05)
    # raíles de rodadura longitudinales sobre ménsulas
    for x in (X0 + 0.9, X1 - 0.9):
        arq.viga_h(c, (x, YF + 0.6, 11.25), (x, YB - 0.6, 11.25), 0.5, 0.4, osc)
        for y in (-6.0, -1.0, 4.0, 8.5):
            c.extruir([(0, 0), (0.0, 0.8), (-0.4 if x < 0 else 0.4, 0.8)], 0.3, gris,
                      c=(x + (-0.25 if x < 0 else 0.25), y, 10.2), rot=(90, 0, 0))
    for grua, gy in ((grua1, -3.0), (grua2, 4.0)):
        # viga puente con testeros, carro y gancho
        arq.viga_h(grua, (X0 + 0.6, gy, 11.75), (X1 - 0.6, gy, 11.75), 0.7, 0.5, amar)
        for x in (X0 + 0.9, X1 - 0.9):
            grua.caja((x, gy, 11.6), (0.6, 1.8, 0.5), amar, 0.04)
            for dy in (-0.6, 0.6):
                grua.cil((x - 0.32, gy + dy, 11.45), (x + 0.32, gy + dy, 11.45), 0.18, osc, n=10)
        gx = 2.0 if gy < 0 else -3.5
        grua.caja((gx, gy, 11.2), (1.4, 1.0, 0.5), m.mat("pintura", "#2E5A8A", desgaste=0.5), 0.05)
        grua.cil((gx - 0.5, gy, 11.0), (gx + 0.5, gy, 11.0), 0.25, osc, n=12)
        grua.cil((gx, gy, 10.8), (gx, gy, 8.0 if gy < 0 else 9.0), 0.03, cadena, n=4)
        zg = 8.0 if gy < 0 else 9.0
        grua.caja((gx, gy, zg - 0.15), (0.35, 0.25, 0.4), osc, 0.04)
        grua.tubo([(gx, gy, zg - 0.35), (gx, gy, zg - 0.7), (gx + 0.12, gy, zg - 0.9), (gx + 0.32, gy, zg - 0.82),
                   (gx + 0.36, gy, zg - 0.6)], 0.07, acero, n=6, seg=2, r_fin=0.035)

    m.seccion("lámparas y señalización")
    for x in (-6.0, -2.0, 2.0, 6.0):
        for y in (-3.5, 5.0):
            c.cil((x, y, ZT - 0.05), (x, y, ZT - 1.0), 0.02, osc, n=4)
            c.torno([(0.0, 0.25), (0.15, 0.25), (0.55, -0.15), (0.6, -0.2), (0.56, -0.22), (0.14, 0.18), (0.0, 0.18)],
                    gris, n=14, c=(x, y, ZT - 1.25))
            pantallas.cil((x, y, ZT - 1.42), (x, y, ZT - 1.38), 0.5, None, n=14)
    # cartel BAHÍA 1 pintado en la pared del fondo
    c.caja((0, YB - 0.55, 9.0), (6.4, 0.08, 1.8), amar, 0.03)
    c.texto("BAHÍA 1", negro, alto=1.2, grosor=0.03, c=(0, YB - 0.6, 8.45), rot=(90, 0, 180), fuente="estrecha", resol=1)
    # pasarela de mantenimiento en la pared del fondo con escalera de gato
    c.caja((0, YB - 1.1, 6.0), (14.0, 1.0, 0.12), m.mat("grip", "#6E747A"), 0.02)
    arq.barandilla(c, [(-7.0, YB - 1.55, 6.06), (7.0, YB - 1.55, 6.06)], 1.0, amar, r=0.04, n=5, barrotes=0)
    for x in (-6.5, 0.0, 6.5):
        c.extruir([(0, 0), (0.9, 0), (0.0, -0.9)], 0.12, gris, c=(x, YB - 0.55, 5.95), rot=(90, 0, 90))
    for s in (-1, 1):
        c.cil((7.4 + s * 0.25, YB - 0.7, Z0), (7.4 + s * 0.25, YB - 0.7, 7.2), 0.04, amar, n=5)
    for k in range(18):
        c.cil((7.15, YB - 0.7, Z0 + 0.4 + k * 0.38), (7.65, YB - 0.7, Z0 + 0.4 + k * 0.38), 0.025, amar, n=4)
    m.terminar()


# ==============================================================================================================
def plataforma_aterrizaje():
    m = Modelo("plataforma_aterrizaje", ZONA, (12, 12, 0.5), 4000,
               "Plataforma de aterrizaje: chapa antideslizante, H central con círculo y flechas de aproximación, 12 "
               "luces perimetrales empotradas, 4 anclajes plegados, 4 desagües y quemaduras de propulsores.")
    c = m.parte()
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    chapa = m.mat("grip", "#6A7078", manchas=[(5.0, 5.0, 0.5, 1.6, "#0E0D0C", 0.85), (-5.0, 5.0, 0.5, 1.4, "#12100E", 0.8),
                                             (5.0, -5.0, 0.5, 1.5, "#0E0D0C", 0.8), (-5.0, -5.0, 0.5, 1.7, "#12100E", 0.85),
                                             (0.0, 0.0, 0.5, 3.0, "#2A2826", 0.4)])
    borde = m.mat("pintura", "#3A4048", desgaste=0.6)
    amar = m.mat("pintura", "#E3B22A", desgaste=0.65, c_desgaste="#6A7078", aranazos=0.0)
    blanco = m.mat("pintura", "#ECEAE4", desgaste=0.6, c_desgaste="#6A7078", aranazos=0.0)
    acero = m.mat("metal", "#8A9097")
    osc = m.mat("metal", "#24282C", rug=0.5)
    S = 12.0
    c.caja((0, 0, 0.2), (S, S, 0.4), chapa, 0.06)
    # biselado del borde (rampa perimetral) y faldón
    for s in (-1, 1):
        c.caja((0, s * (S / 2 - 0.15), 0.25), (S, 0.3, 0.42), borde, 0.06)
        c.caja((s * (S / 2 - 0.15), 0, 0.25), (0.3, S, 0.42), borde, 0.06)
    z = 0.405
    # círculo, H y flechas
    c.toro((0, 0, z), 4.3, 0.16, amar, n=40, m=3)
    _letra_h(c, blanco, 0, 0, z, 3.6, 0.015)
    for k in range(4):
        a = k * math.pi / 2
        with c.en((math.cos(a) * 5.0, math.sin(a) * 5.0, z), (0, 0, math.degrees(a) + 90)):
            c.extruir([(-0.25, 0.0), (0.25, 0.0), (0.25, -0.5), (0.6, -0.5), (0.0, -1.1), (-0.6, -0.5), (-0.25, -0.5)],
                      0.015, amar)
    # 12 luces perimetrales empotradas (marco biselado + lente neón)
    for k in range(12):
        lado, i = divmod(k, 3)
        t = -3.6 + i * 3.6
        p = {0: (t, -S / 2 + 0.55), 1: (S / 2 - 0.55, t), 2: (-t, S / 2 - 0.55), 3: (-S / 2 + 0.55, -t)}[lado]
        c.cil((p[0], p[1], 0.38), (p[0], p[1], 0.43), 0.22, acero, n=12, r1=0.18)
        luces.cil((p[0], p[1], 0.4), (p[0], p[1], 0.44), 0.13, None, n=10)
    # 4 anclajes de sujeción: placa base, bisagra y gancho plegado contra el suelo
    for (x, y, ang) in ((2.8, 2.8, 45), (-2.8, 2.8, 135), (-2.8, -2.8, 225), (2.8, -2.8, 315)):
        with c.en((x, y, z), (0, 0, ang)):
            c.caja((0, 0, 0.015), (0.6, 0.45, 0.04), osc, 0.01)
            c.cil((-0.2, -0.15, 0.06), (-0.2, 0.15, 0.06), 0.05, acero, n=8)
            c.tubo([(-0.2, 0, 0.06), (0.25, 0, 0.06), (0.45, 0, 0.08), (0.48, 0, 0.16), (0.38, 0, 0.18)], 0.035, acero,
                   n=6, seg=2)
            for dx in (-0.22, 0.22):
                c.perno((dx, 0.17, 0.035), (0, 0, 1), acero, r=0.03, arandela=False)
    # 4 desagües con rejilla
    for (x, y) in ((4.0, 0.0), (-4.0, 0.0), (0.0, 4.0), (0.0, -4.0)):
        c.caja((x, y, 0.395), (0.7, 0.5, 0.02), osc, 0.0)
        for k in range(5):
            c.caja((x - 0.28 + k * 0.14, y, 0.405), (0.05, 0.44, 0.02), acero, 0.0)
    m.terminar()


# ==============================================================================================================
def brazo_mecanico_hangar():
    m = Modelo("brazo_mecanico_hangar", ZONA, (2, 2, 8), 6000,
               "Brazo robótico de ensamblaje: base giratoria con rodamiento, 3 articulaciones con actuadores "
               "hidráulicos, pinza de 3 dedos articulados, cables y mangueras con abrazaderas y caja de control.")
    c = m.parte()
    gira = m.parte("giratoria", pivote=(0, 0, 0.9), nota="Todo el brazo gira sobre la base (eje vertical).")
    luz = m.parte("pantalla_neon", tipo="neon", color=NEON)
    nar = m.mat("pintura", "#E07A1F", desgaste=0.5, c_desgaste="#8A9097")
    blanco = m.mat("pintura", "#E6E8EA", desgaste=0.35)
    osc = m.mat("metal", "#2B2F34", rug=0.45)
    acero = m.mat("metal", "#8A9097")
    cromo = m.mat("cromo", "#D2D6DA")
    goma = m.mat("goma", "#151618")
    azul = m.mat("goma", "#1E4A7A")
    # base fija y caja de control
    c.cil((0, 0, 0), (0, 0, 0.5), 0.85, osc, n=18, b=0.04)
    c.cil((0, 0, 0.5), (0, 0, 0.7), 0.7, blanco, n=18)
    c.cil((0, 0, 0.7), (0, 0, 0.9), 0.62, acero, n=20)
    for k in range(10):
        a = k * math.tau / 10
        c.perno((math.cos(a) * 0.74, math.sin(a) * 0.74, 0.5), (0, 0, 1), acero, r=0.035)
    c.caja((0.75, -0.55, 0.45), (0.5, 0.35, 0.8), blanco, 0.04)
    c.caja((0.75, -0.73, 0.55), (0.38, 0.02, 0.3), osc, 0.0)
    luz.caja((0.75, -0.745, 0.57), (0.32, 0.01, 0.24), None)
    c.tubo([(0.75, -0.4, 0.85), (0.6, -0.2, 0.95), (0.3, 0.0, 0.92)], 0.04, goma, n=5, seg=2)
    # torreta giratoria y hombro
    gira.cil((0, 0, 0.9), (0, 0, 1.6), 0.55, nar, n=16)
    gira.caja((0, 0, 1.75), (0.9, 0.7, 0.5), nar, 0.08)
    J1 = V((0, 0, 2.0))
    J2 = V((0.6, 0, 4.6))
    J3 = V((-0.1, 0, 6.6))
    P = V((0.15, 0, 7.4))

    def articulacion(p, r):
        gira.cil(p + V((0, -0.42, 0)), p + V((0, 0.42, 0)), r, osc, n=14)
        gira.cil(p + V((0, -0.47, 0)), p + V((0, 0.47, 0)), r * 0.5, cromo, n=10)

    def segmento(a, b, w, d):
        u = (b - a).normalized()
        L = (b - a).length
        ang = math.degrees(math.atan2(u.x, u.z))
        with gira.en((a + b) / 2, (0, ang, 0)):
            gira.caja((0, 0, 0), (w, d, L - 0.2), nar, 0.1)
            gira.caja((0, -d / 2 - 0.01, 0), (w * 0.6, 0.02, L * 0.5), blanco, 0.0)

    def actuador(a, b):
        gira.cil(a, a.lerp(b, 0.55), 0.09, osc, n=8)
        gira.cil(a.lerp(b, 0.5), b, 0.05, cromo, n=8)
        for p in (a, b):
            gira.esfera(p, 0.1, osc, seg=8, anillos=5)

    articulacion(J1, 0.38)
    segmento(J1, J2, 0.55, 0.6)
    articulacion(J2, 0.32)
    segmento(J2, J3, 0.45, 0.5)
    articulacion(J3, 0.26)
    segmento(J3, P, 0.35, 0.4)
    # actuadores hidráulicos a un lado de cada tramo
    actuador(V((0.35, 0.42, 1.8)), V((0.6, 0.42, 3.5)))
    actuador(V((0.65, -0.38, 4.2)), V((0.1, -0.38, 5.8)))
    actuador(V((-0.2, 0.33, 6.2)), V((0.18, 0.33, 7.0)))
    # muñeca y pinza de tres dedos (cada dedo en dos falanges)
    gira.cil(P, P + V((0.05, 0, 0.3)), 0.2, osc, n=12)
    gira.cil(P + V((0.05, 0, 0.3)), P + V((0.06, 0, 0.42)), 0.24, acero, n=12)
    base = P + V((0.06, 0, 0.42))
    for k in range(3):
        a = k * math.tau / 3
        dirr = V((math.cos(a), math.sin(a), 0))
        f0 = base + dirr * 0.16
        f1 = f0 + dirr * 0.12 + V((0, 0, 0.25))
        f2 = f1 - dirr * 0.08 + V((0, 0, 0.2))
        gira.cil(f0, f1, 0.05, nar, n=6)
        gira.esfera(f1, 0.055, osc, seg=6, anillos=4)
        gira.cil(f1, f2, 0.04, nar, n=6, r1=0.025)
        gira.caja(f2 - dirr * 0.02, (0.05, 0.05, 0.06), goma, 0.01)
    # cables y mangueras con abrazaderas a lo largo del brazo
    for k, mat in enumerate((goma, azul)):
        off = V((-0.32 - 0.07 * k, 0.15 * (1 if k else -1), 0))
        pts = [J1 + off + V((0, 0, -0.5)), J1.lerp(J2, 0.3) + off, J1.lerp(J2, 0.7) + off, J2 + off + V((-0.15, 0, 0)),
               J2.lerp(J3, 0.5) + off + V((0, 0, 0)), J3 + off + V((-0.1, 0, 0)), P + off + V((0.1, 0, 0))]
        gira.tubo(pts, 0.035, mat, n=5, seg=3)
    for t, (a, b) in ((0.5, (J1, J2)), (0.5, (J2, J3))):
        p = a.lerp(b, t) + V((-0.36, 0, 0))
        gira.caja(p, (0.2, 0.45, 0.08), acero, 0.01)
    m.terminar()


# ==============================================================================================================
def consola_control_hangar():
    m = Modelo("consola_control_hangar", ZONA, (2, 1, 3), 4000,
               "Terminal de control: pantalla holográfica con marco, teclado de 24 teclas 3D, joystick, botones de "
               "emergencia, activar y espera, cable de alimentación y silla giratoria aparte.")
    c = m.parte()
    luz = m.parte("pantalla_neon", tipo="neon", color=NEON, nota="Interfaz de la pantalla: Neon cyan.")
    silla = m.parte("silla", pivote=(0, -1.0, 0), nota="Silla giratoria: pieza aparte (se puede mover y girar).")
    gris = m.mat("pintura", "#3E4650", desgaste=0.45)
    blanco = m.mat("pintura", "#D9DDE1", desgaste=0.35)
    osc = m.mat("metal", "#24282C", rug=0.45)
    acero = m.mat("metal", "#8A9097")
    tecla = m.mat("plastico", "#2E3238")
    tecla2 = m.mat("plastico", "#5A626C")
    rojo = m.mat("plastico", "#D42A22")
    verde = m.mat("plastico", "#2EA04E")
    amar = m.mat("plastico", "#E8B82A")
    goma = m.mat("goma", "#151618")
    tapiz = m.mat("cuero", "#2B3A4A")
    # pedestal y pupitre inclinado
    c.caja((0, 0.15, 0.6), (1.6, 0.7, 1.2), gris, 0.06)
    c.caja((0, 0.2, 0.06), (1.8, 0.8, 0.12), osc, 0.03)
    with c.en((0, -0.1, 1.32), (-18, 0, 0)):
        c.caja((0, 0, 0), (1.9, 0.9, 0.18), blanco, 0.05)
        # teclado: 4 filas × 6 teclas
        for i in range(4):
            for j in range(6):
                c.caja((-0.62 + j * 0.13, -0.18 + i * 0.12, 0.11), (0.1, 0.09, 0.05), tecla if (i + j) % 5 else tecla2,
                       0.015)
        c.caja((-0.3, -0.33, 0.11), (0.6, 0.08, 0.05), tecla, 0.015)  # barra espaciadora
        # joystick con fuelle y empuñadura
        c.cil((0.55, 0.05, 0.09), (0.55, 0.05, 0.14), 0.12, osc, n=12)
        c.cil((0.55, 0.05, 0.14), (0.55, 0.05, 0.22), 0.08, goma, n=10, r1=0.04)
        c.cil((0.55, 0.05, 0.22), (0.57, 0.05, 0.42), 0.035, osc, n=8)
        c.esfera((0.57, 0.05, 0.45), 0.06, tecla, seg=8, anillos=5, esc=(1, 1, 1.3))
        c.cil((0.55, 0.0, 0.47), (0.55, -0.02, 0.5), 0.015, rojo, n=6)
        # botones de colores con guardas
        for k, col in enumerate((rojo, verde, amar)):
            x = 0.25 + k * 0.17
            c.cil((x, -0.28, 0.09), (x, -0.28, 0.12), 0.07, osc, n=12)
            c.cil((x, -0.28, 0.12), (x, -0.28, 0.16), 0.055, col, n=12)
        c.toro((0.25, -0.28, 0.15), 0.075, 0.012, amar, n=12, m=3)
    # pantalla principal holográfica con marco y brazo
    c.caja((0, 0.45, 1.9), (0.2, 0.15, 0.5), osc, 0.03)
    with c.en((0, 0.45, 2.45), (8, 0, 0)):
        for (cx, cz, w, h) in ((0, 0.52, 1.8, 0.08), (0, -0.52, 1.8, 0.08), (-0.86, 0, 0.08, 1.1), (0.86, 0, 0.08, 1.1)):
            c.caja((cx, 0, cz), (w, 0.1, h), osc, 0.02)
        c.caja((0, 0.05, 0), (1.7, 0.04, 1.0), osc, 0.0)
        c.caja((0, -0.01, 0), (1.62, 0.02, 0.94), m.mat("plastico", "#0B2230", desgaste=0.0, aranazos=0.0,
                                                       suciedad=0.0), 0.0)
        # interfaz en relieve: radar con cruz, barras de estado y líneas de marco
        luz.toro((-0.45, -0.03, 0.02), 0.3, 0.012, None, n=20, m=3, rot=(90, 0, 0))
        luz.toro((-0.45, -0.03, 0.02), 0.16, 0.01, None, n=16, m=3, rot=(90, 0, 0))
        luz.caja((-0.45, -0.03, 0.02), (0.62, 0.008, 0.012), None)
        luz.caja((-0.45, -0.03, 0.02), (0.012, 0.008, 0.62), None)
        for k in range(5):
            luz.caja((0.38, -0.03, 0.28 - k * 0.14), (0.62 - (k % 3) * 0.14, 0.008, 0.05), None)
        for zz in (-0.42, 0.42):
            luz.caja((0, -0.03, zz), (1.5, 0.008, 0.015), None)
        for k in range(4):
            c.perno((-0.82 + 1.64 * (k % 2), -0.06, -0.48 + 0.96 * (k // 2)), (0, -1, 0), acero, r=0.02, arandela=False)
    # cable de alimentación por detrás hasta el suelo
    c.tubo([(0.5, 0.52, 0.6), (0.6, 0.7, 0.5), (0.7, 0.75, 0.05), (1.0, 0.9, 0.02)], 0.04, goma, n=5, seg=3)
    # silla giratoria: 5 radios con ruedas, pistón, asiento y respaldo
    with silla.en((0, -1.0, 0)):
        for k in range(5):
            a = k * math.tau / 5
            silla.cil((0, 0, 0.18), (math.cos(a) * 0.42, math.sin(a) * 0.42, 0.12), 0.04, osc, n=5)
            silla.cil((math.cos(a) * 0.42, math.sin(a) * 0.42 - 0.03, 0.06), (math.cos(a) * 0.42, math.sin(a) * 0.42 + 0.03,
                                                                              0.06), 0.06, goma, n=8)
        silla.cil((0, 0, 0.16), (0, 0, 0.75), 0.05, acero, n=8)
        silla.cil((0, 0, 0.16), (0, 0, 0.45), 0.07, osc, n=8)
        silla.caja((0, 0, 0.82), (0.75, 0.7, 0.14), tapiz, 0.06)
        silla.caja((0, 0.4, 1.25), (0.7, 0.12, 0.75), tapiz, 0.06, rot=(-8, 0, 0))
        silla.cil((0, 0.3, 0.82), (0, 0.38, 0.95), 0.04, acero, n=6)
        for s in (-1, 1):
            silla.tubo([(s * 0.36, 0.2, 0.88), (s * 0.38, 0.15, 1.1), (s * 0.38, -0.2, 1.1)], 0.03, osc, n=5, seg=2)
    m.terminar()


# ==============================================================================================================
def rack_piezas_nave():
    m = Modelo("rack_piezas_nave", ZONA, (6, 2, 6), 6000,
               "Estantería grande de tubo de 4 niveles con piezas de nave: panel de fuselaje curvado, boquilla de "
               "motor cónica, tramo de tubería, caja de electrónica; etiquetas por nivel y pernos de anclaje.")
    c = m.parte()
    luz = m.parte("electronica_neon", tipo="neon", color=NEON)
    amar = m.mat("pintura", "#E3B22A", desgaste=0.6)
    acero = m.mat("metal", "#8A9097")
    osc = m.mat("metal", "#2B2F34", rug=0.45)
    grip = m.mat("grip", "#6E747A")
    blanco = m.mat("pintura", "#E6E8EA", desgaste=0.4, c_desgaste="#8A9097")
    tobera = m.mat("metal", "#5B4E46", rug=0.38, hollin=(0.0, 0.0))
    cobre = m.mat("metal", "#B26A3C", rug=0.35)
    papel = m.mat("papel", "#ECE6D2")
    tinta = m.mat("pintura", "#1E2226", desgaste=0.0)
    verde = m.mat("plastico", "#2E6A3E")
    W, D = 5.8, 1.7
    niveles = [0.3, 1.7, 3.1, 4.5]
    # montantes de tubo con placas base y pernos de anclaje
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = V((sx * W / 2, sy * D / 2, 0))
            c.cil(p, p + V((0, 0, 5.9)), 0.07, amar, n=8)
            c.caja(p + V((0, 0, 0.02)), (0.3, 0.3, 0.04), acero, 0.01)
            for k in range(2):
                c.perno(p + V((0.1 * (1 - 2 * k), 0.1 * (1 - 2 * k), 0.04)), (0, 0, 1), acero, r=0.03)
    for sx in (-1, 0, 1):
        x = sx * W / 2
        if sx == 0:
            for sy in (-1, 1):
                c.cil((0, sy * D / 2, 0), (0, sy * D / 2, 5.9), 0.06, amar, n=8)
    # baldas con chapa de diamante y largueros; diagonales en los costados
    for z in niveles:
        c.caja((0, 0, z), (W + 0.1, D + 0.1, 0.06), grip, 0.01)
        for sy in (-1, 1):
            c.cil((-W / 2, sy * D / 2, z - 0.06), (W / 2, sy * D / 2, z - 0.06), 0.05, amar, n=6)
        # etiqueta del nivel
        c.caja((-W / 2 + 0.5, -D / 2 - 0.06, z - 0.06), (0.6, 0.02, 0.15), papel, 0.0)
        c.caja((-W / 2 + 0.45, -D / 2 - 0.072, z - 0.06), (0.4, 0.005, 0.04), tinta, 0.0)
    for sx in (-1, 1):
        c.cil((sx * W / 2, -D / 2, 0.3), (sx * W / 2, D / 2, 3.1), 0.03, amar, n=5)
        c.cil((sx * W / 2, D / 2, 3.1), (sx * W / 2, -D / 2, 5.9), 0.03, amar, n=5)
    # nivel 1: tramo de tubería con bridas y codo
    z = niveles[0] + 0.03
    c.cil((-2.4, 0, z + 0.3), (0.4, 0, z + 0.3), 0.26, cobre, n=14)
    for x in (-2.4, 0.4):
        c.cil((x - 0.05, 0, z + 0.3), (x + 0.05, 0, z + 0.3), 0.36, acero, n=14)
    for x in (-2.0, -0.2):
        c.caja((x, 0, z + 0.04), (0.2, 0.6, 0.08), m.mat("madera", "#9A7448", eje="Y"), 0.01)
    c.caja((1.8, 0, z + 0.3), (1.4, 1.2, 0.6), m.mat("papel", "#B08A5C"), 0.03)
    # nivel 2: boquilla de motor cónica sobre cuna
    z = niveles[1] + 0.03
    with c.en((-1.0, 0, z + 0.7), (0, 90, 0)):
        c.torno([(0.0, -1.0), (0.32, -1.0), (0.34, -0.85), (0.62, 0.5), (0.68, 0.9), (0.6, 0.9), (0.55, 0.52),
                 (0.28, -0.8), (0.0, -0.8)], tobera, n=18)
        for k in range(3):
            c.toro((0, 0, -0.6 + k * 0.45), 0.4 + k * 0.08, 0.03, acero, n=16, m=4)
    for x in (-1.6, -0.4):
        c.caja((x, 0, z + 0.1), (0.25, 1.0, 0.2), osc, 0.02)
    c.caja((1.6, 0, z + 0.25), (1.2, 0.9, 0.5), blanco, 0.04)
    # nivel 3: panel de fuselaje curvado apoyado de canto
    z = niveles[2] + 0.03
    c.lamina(lambda u, v: (-2.4 + u * 3.6, 0.55 * math.sin(u * math.pi) - 0.1, z + 0.05 + v * 1.15), 10, 2, 0.06, blanco)
    for k in range(4):
        c.remache((-2.0 + k * 0.9, 0.55 * math.sin((k * 0.9 + 0.4) / 3.6 * math.pi) - 0.14, z + 0.7), (0, -1, 0), acero,
                  0.03)
    c.caja((1.9, 0, z + 0.2), (1.2, 0.9, 0.4), osc, 0.03)
    # nivel 4: caja de electrónica con placa y LEDs, cables
    z = niveles[3] + 0.03
    c.caja((-0.5, 0, z + 0.4), (2.0, 1.2, 0.8), osc, 0.05)
    c.caja((-0.5, -0.61, z + 0.4), (1.7, 0.02, 0.6), verde, 0.0)
    for k in range(6):
        luz.caja((-1.2 + k * 0.28, -0.63, z + 0.6), (0.06, 0.01, 0.06), None)
        c.caja((-1.2 + k * 0.28, -0.625, z + 0.35), (0.2, 0.02, 0.12), acero, 0.0)
    c.tubo([(0.5, 0.0, z + 0.6), (1.0, -0.2, z + 0.4), (1.4, -0.3, z + 0.05), (2.0, 0.1, z + 0.05)], 0.04,
           m.mat("goma", "#151618"), n=5, seg=3)
    m.terminar()


# ==============================================================================================================
def cable_combustible():
    m = Modelo("cable_combustible", ZONA, (3, 1, 1), 2000,
               "Manguera de repostaje enrollada en carrete de pared, boquilla con seguro de bayoneta, manómetro en "
               "la conexión y cartel COMBUSTIBLE — NO FUMAR.")
    c = m.parte()
    carrete = m.parte("carrete", pivote=(-0.6, -0.4, 0.55), nota="Tambor del carrete: gira sobre el eje Y del modelo.")
    rojo = m.mat("pintura", "#B8302A", desgaste=0.55)
    acero = m.mat("metal", "#8A9097")
    osc = m.mat("metal", "#2B2F34", rug=0.45)
    goma = m.mat("goma", "#1E1F22", bump=0.4)
    laton = m.mat("metal", "#B9913F", rug=0.3)
    blanco = m.mat("plastico", "#F0EEE6")
    amar = m.mat("pintura", "#E3B22A", desgaste=0.4)
    tinta = m.mat("pintura", "#16181A", desgaste=0.0)
    # placa de pared y soportes del carrete
    c.caja((-0.6, 0.45, 0.55), (1.1, 0.08, 1.0), rojo)
    for (dx, dz) in ((-0.45, -0.4), (0.45, 0.4)):
        c.perno((-0.6 + dx, 0.4, 0.55 + dz), (0, -1, 0), acero, r=0.035)
    for s in (-1, 1):
        c.extruir([(-0.15, 0.0), (0.15, 0.0), (0.05, -0.9), (-0.05, -0.9)], 0.05, rojo, c=(-0.6 + s * 0.38, 0.42, 0.55),
                  rot=(90, 90, 0))
    # tambor con discos laterales y manguera enrollada
    carrete.cil((-0.6, 0.35, 0.55), (-0.6, -0.42, 0.55), 0.12, osc, n=8)
    for y in (0.3, -0.38):
        carrete.cil((-0.6, y, 0.55), (-0.6, y - 0.04, 0.55), 0.42, rojo, n=14)
    for k in range(3):
        carrete.toro((-0.6, 0.18 - k * 0.19, 0.55), 0.22, 0.09, goma, n=10, m=4, rot=(90, 0, 0))
    carrete.cil((-0.6, -0.45, 0.55), (-0.6, -0.5, 0.55), 0.06, acero, n=6)
    carrete.cil((-0.6, -0.5, 0.55), (-0.3, -0.5, 0.75), 0.02, acero, n=4)  # manivela
    carrete.cil((-0.3, -0.5, 0.75), (-0.3, -0.62, 0.75), 0.03, osc, n=4)
    # manguera que sale y cuelga hasta la boquilla en su soporte
    c.tubo([(-0.6, -0.05, 0.3), (-0.3, -0.2, 0.1), (0.2, -0.25, 0.08), (0.6, -0.2, 0.35), (0.75, -0.15, 0.6)], 0.05, goma,
           n=6, seg=3)
    # manómetro en la conexión
    mp = V((0.75, -0.15, 0.62))
    c.cil(mp, mp + V((0, 0, 0.1)), 0.06, laton, n=6)
    c.cil(mp + V((0, 0, 0.1)), mp + V((0, -0.08, 0.2)), 0.025, laton, n=5)
    c.cil(mp + V((0, -0.08, 0.2)), mp + V((0, -0.15, 0.2)), 0.1, acero, n=10)
    c.cil(mp + V((0, -0.15, 0.2)), mp + V((0, -0.155, 0.2)), 0.085, blanco, n=10)
    c.caja(mp + V((0.02, -0.16, 0.22)), (0.01, 0.004, 0.07), rojo, 0.0, rot=(0, -40, 0))
    # boquilla con gatillo y seguro de bayoneta, en un soporte de pared
    c.caja((0.95, 0.42, 0.75), (0.25, 0.1, 0.35), osc)
    with c.en((0.95, 0.15, 0.85), (0, 0, 0)):
        c.cil((-0.2, 0, -0.1), (0.0, 0, 0.0), 0.05, laton, n=6)
        c.caja((0.0, 0, 0.0), (0.12, 0.12, 0.35), osc, rot=(0, 20, 0))
        c.cil((0.05, 0, 0.15), (0.35, 0, 0.3), 0.04, acero, n=6)
        c.cil((0.35, 0, 0.3), (0.45, 0, 0.32), 0.05, acero, n=6)
        for k in range(2):  # pitones de bayoneta
            c.caja((0.42, 0.055 * (1 - 2 * k), 0.31), (0.04, 0.03, 0.03), acero, 0.0)
        c.tubo([(-0.02, 0, -0.08), (0.04, -0.0, -0.2), (0.15, 0, -0.18), (0.12, 0, -0.04)], 0.018, rojo, n=4, seg=2)
    # cartel COMBUSTIBLE — NO FUMAR
    c.caja((1.6 - 0.2, 0.45, 0.6), (1.0, 0.04, 0.7), amar)
    c.texto("COMBUSTIBLE", tinta, alto=0.11, grosor=0.01, c=(1.4, 0.425, 0.82), fuente="mono", resol=1)
    c.texto("NO FUMAR", m.mat("pintura", "#B8302A", desgaste=0.0), alto=0.13, grosor=0.01, c=(1.4, 0.425, 0.32),
            fuente="mono", resol=1)
    m.terminar()


# ==============================================================================================================
def luz_baliza_hangar():
    m = Modelo("luz_baliza_hangar", ZONA, (0.5, 0.5, 0.5), 500,
               "Baliza de suelo empotrada: cuerpo cilíndrico metálico, marco biselado antipisada, 4 tornillos y "
               "lente superior en neón cyan. Se colocan en línea para marcar caminos.")
    c = m.parte()
    lente = m.parte("lente_neon", tipo="neon", color=NEON)
    acero = m.mat("metal", "#8A9097", aranazos=0.8)
    osc = m.mat("metal", "#2B2F34", rug=0.45)
    # cuerpo que se empotra en el suelo (0,4 bajo la superficie) y marco biselado que sobresale
    c.cil((0, 0, 0.0), (0, 0, 0.42), 0.18, osc, n=12)
    c.cil((0, 0, 0.42), (0, 0, 0.5), 0.25, acero, n=12, r1=0.18)
    lente.cil((0, 0, 0.44), (0, 0, 0.51), 0.13, None, n=10, r1=0.11)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c.cil((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.45), (math.cos(a) * 0.2, math.sin(a) * 0.2, 0.48), 0.02, osc, n=6)
    m.notas.append("El suelo debe quedar a 0,42 studs de la base (enrasado con el marco): el cuerpo va empotrado.")
    m.terminar()


# ==============================================================================================================
def escalera_nave():
    m = Modelo("escalera_nave", ZONA, (3, 1, 4), 3000,
               "Escalera con ruedas para acceder a naves: 8 peldaños antideslizantes, barandilla a ambos lados, "
               "4 ruedas con freno, plataforma superior con barandilla y bisagras de plegado en la mitad.")
    c = m.parte()
    amar = m.mat("pintura", "#E3B22A", desgaste=0.6)
    grip = m.mat("grip", "#7A8087")
    acero = m.mat("metal", "#8A9097")
    osc = m.mat("metal", "#2B2F34", rug=0.45)
    goma = m.mat("goma", "#151618")
    rojo = m.mat("plastico", "#D42A22")
    W = 0.9
    H = 3.2
    L = 2.6
    # largueros inclinados (de x=-1.3,z=0.4 a x=1.0,z=3.2)
    a = V((-1.35, 0, 0.35))
    b = V((0.9, 0, H))
    for s in (-1, 1):
        c.cil(a + V((0, s * W / 2, 0)), b + V((0, s * W / 2, 0)), 0.05, amar, n=6)
        c.cil(V((-1.35, s * W / 2, 0.35)), V((1.35, s * W / 2, 0.35)), 0.05, amar, n=6)  # bastidor bajo
        c.cil(V((1.3, s * W / 2, 0.35)), V((1.3, s * W / 2, H)), 0.05, amar, n=6)  # pata trasera
    # 8 peldaños
    for k in range(8):
        t = (k + 1) / 9
        p = a.lerp(b, t)
        c.caja(p + V((0.05, 0, 0.02)), (0.32, W - 0.06, 0.05), grip, 0.01)
    # bisagras de plegado a media altura (cada lado): cartelas y pasador
    mid = a.lerp(b, 0.5)
    for s in (-1, 1):
        c.caja(mid + V((0, s * (W / 2 + 0.04), 0)), (0.22, 0.03, 0.2), acero, 0.01)
        c.cil(mid + V((0, s * (W / 2 + 0.02), 0)), mid + V((0, s * (W / 2 + 0.09), 0)), 0.04, osc, n=8)
    # plataforma superior y barandillas
    c.caja((1.1, 0, H + 0.02), (0.55, W + 0.05, 0.06), grip, 0.01)
    for s in (-1, 1):
        arq.barandilla(c, [(-1.1, s * W / 2, 0.75), (0.9, s * W / 2, H), (1.35, s * W / 2, H)], 0.95, amar, r=0.03, n=5)
    c.cil((1.35, -W / 2, H + 0.95), (1.35, W / 2, H + 0.95), 0.03, amar, n=5)
    c.cil((1.35, -W / 2, H + 0.5), (1.35, W / 2, H + 0.5), 0.025, amar, n=5)
    # 4 ruedas giratorias con freno (pedal rojo)
    for x in (-1.3, 1.3):
        for s in (-1, 1):
            p = V((x, s * W / 2, 0.35))
            c.caja(p - V((0, 0, 0.05)), (0.12, 0.12, 0.06), acero, 0.01)
            c.cil(p - V((0, 0, 0.08)), p - V((0, 0, 0.14)), 0.03, acero, n=6)
            c.cil(p + V((-0.04, -0.04, -0.23)), p + V((-0.04, 0.04, -0.23)), 0.11, goma, n=10)
            c.caja(p + V((-0.04, 0, -0.2)), (0.04, 0.12, 0.2), osc, 0.01)
            c.caja(p + V((0.08, 0, -0.14)), (0.1, 0.06, 0.03), rojo, 0.005)
    m.terminar()


# ==============================================================================================================
def caja_herramientas_hangar():
    m = Modelo("caja_herramientas_hangar", ZONA, (2, 1, 3), 4000,
               "Caja de herramientas rodante profesional: 5 cajones con tiradores y cerradura, 2 ruedas fijas y 2 "
               "giratorias, borde anti-caída, 3 llaves inglesas en el soporte lateral y un destornillador.")
    c = m.parte()
    cajones = [m.parte(f"cajon_{k + 1}", pivote=(0, -0.42, 0.55 + k * 0.32), nota="Cajón: se abre 0,5 studs hacia "
                                                                                   "delante.") for k in range(5)]
    rojo = m.mat("pintura", "#B8282A", desgaste=0.5, c_desgaste="#8A9097")
    osc = m.mat("metal", "#24282C", rug=0.45)
    acero = m.mat("metal", "#9AA0A6", rug=0.3)
    cromo = m.mat("cromo", "#D4D8DC")
    goma = m.mat("goma", "#151618")
    amar = m.mat("plastico", "#E8B82A")
    tapete = m.mat("goma", "#2A2C30", bump=0.6, patron="diamante")
    W, D = 1.6, 0.8
    # cuerpo
    c.caja((0, 0, 1.4), (W, D, 2.2), rojo, 0.05)
    c.caja((0, 0, 2.53), (W + 0.04, D + 0.04, 0.06), osc, 0.02)
    c.caja((0, 0, 2.565), (W - 0.1, D - 0.1, 0.01), tapete, 0.0)
    # borde anti-caída alrededor de la tapa
    for s in (-1, 1):
        c.caja((0, s * (D / 2 + 0.01), 2.62), (W + 0.04, 0.03, 0.12), osc, 0.01)
        c.caja((s * (W / 2 + 0.01), 0, 2.62), (0.03, D + 0.04, 0.12), osc, 0.01)
    # 5 cajones (piezas aparte) con tiradores de barra y etiqueta
    for k, cj in enumerate(cajones):
        z = 0.55 + k * 0.32 if k < 4 else 0.55 + 3 * 0.32 + 0.45
        h = 0.28 if k < 4 else 0.55
        z0 = 0.4 + k * 0.33 if k < 4 else 1.72
        cj.caja((0, -D / 2 - 0.015, z0 + h / 2), (W - 0.1, 0.03, h), rojo, 0.015)
        cj.cil((-0.45, -D / 2 - 0.08, z0 + h - 0.08), (0.45, -D / 2 - 0.08, z0 + h - 0.08), 0.022, cromo, n=6)
        for x in (-0.45, 0.45):
            cj.cil((x, -D / 2 - 0.08, z0 + h - 0.08), (x, -D / 2 - 0.03, z0 + h - 0.08), 0.015, cromo, n=4)
        cj.caja((-0.6, -D / 2 - 0.032, z0 + h / 2), (0.2, 0.004, 0.06), m.mat("papel", "#ECE6D2"), 0.0)
        cj.pivote = V((0, -D / 2, z0))
    # cerradura
    c.cil((0.65, -D / 2, 2.38), (0.65, -D / 2 - 0.04, 2.38), 0.04, cromo, n=10)
    c.caja((0.65, -D / 2 - 0.045, 2.38), (0.01, 0.005, 0.04), osc, 0.0)
    # ruedas: 2 fijas detrás, 2 giratorias delante con freno
    for x in (-0.65, 0.65):
        for y, gir in ((D / 2 - 0.12, False), (-D / 2 + 0.12, True)):
            c.caja((x, y, 0.27), (0.18, 0.18, 0.04), acero, 0.01)
            if gir:
                c.cil((x, y, 0.27), (x, y, 0.22), 0.04, acero, n=6)
            c.caja((x, y + (0.03 if gir else 0), 0.17), (0.04, 0.14, 0.14), osc, 0.01)
            c.cil((x - 0.03, y + (0.05 if gir else 0), 0.11), (x + 0.03, y + (0.05 if gir else 0), 0.11), 0.11, goma, n=10)
            if gir:
                c.caja((x, y - 0.1, 0.2), (0.06, 0.08, 0.02), amar, 0.005)
    # soporte lateral con 3 llaves inglesas y destornillador
    sx = W / 2 + 0.03
    c.caja((sx, 0, 2.2), (0.04, 0.6, 0.06), acero, 0.01)
    for k, L in enumerate((0.55, 0.45, 0.35)):
        y = -0.2 + k * 0.2
        with c.en((sx + 0.05, y, 2.2), (0, 0, 90)):
            c.extruir([(-0.025, 0), (0.025, 0), (0.03, -L + 0.12), (0.07, -L + 0.07), (0.07, -L), (0.02, -L),
                       (0.02, -L + 0.06), (-0.02, -L + 0.06), (-0.02, -L), (-0.07, -L), (-0.07, -L + 0.07),
                       (-0.03, -L + 0.12)], 0.025, cromo, rot=(90, 0, 90))
    c.caja((sx, 0.0, 1.5), (0.04, 0.3, 0.08), acero, 0.01)
    c.cil((sx + 0.05, 0.0, 1.62), (sx + 0.05, 0.0, 1.42), 0.035, amar, n=8)
    c.cil((sx + 0.05, 0.0, 1.42), (sx + 0.05, 0.0, 1.05), 0.012, cromo, n=5)
    # asa lateral
    c.tubo([(-W / 2, -0.25, 2.3), (-W / 2 - 0.12, -0.25, 2.3), (-W / 2 - 0.12, 0.25, 2.3), (-W / 2, 0.25, 2.3)], 0.025,
           cromo, n=6, seg=2)
    m.terminar()


# ==============================================================================================================
def pantalla_estado_nave():
    m = Modelo("pantalla_estado_nave", ZONA, (3, 0.3, 2), 2000,
               "Pantalla grande de pared: marco metálico con 4 tornillos de montaje, interfaz neón con la silueta de "
               "una nave e indicadores, y cableado bajando por la pared hasta una canaleta.")
    c = m.parte()
    pant = m.parte("pantalla_neon", tipo="neon", color=NEON)
    osc = m.mat("metal", "#24282C", rug=0.45)
    acero = m.mat("metal", "#8A9097")
    fondo = m.mat("pintura", "#0E1A22", desgaste=0.0, suciedad=0.0)
    goma = m.mat("goma", "#151618")
    gris = m.mat("pintura", "#5A626C", desgaste=0.4)
    W, H = 3.0, 1.7
    zc = 1.0
    c.caja((0, 0.05, zc), (W, 0.12, H), osc, 0.04)
    c.caja((0, -0.02, zc), (W - 0.2, 0.02, H - 0.2), fondo, 0.0)
    for k in range(4):
        c.perno((-W / 2 + 0.08 + (W - 0.16) * (k % 2), -0.02, zc - H / 2 + 0.08 + (H - 0.16) * (k // 2)), (0, -1, 0),
                acero, r=0.035)
    # interfaz en relieve neón: silueta de nave (fuselaje, alas, motores), barras y anillo
    with pant.en((-0.45, -0.035, zc + 0.05), (90, 0, 0)):
        pant.extruir([(0.0, 0.5), (0.12, 0.25), (0.15, -0.1), (0.6, -0.3), (0.6, -0.38), (0.15, -0.3), (0.1, -0.45),
                      (-0.1, -0.45), (-0.15, -0.3), (-0.6, -0.38), (-0.6, -0.3), (-0.15, -0.1), (-0.12, 0.25)], 0.012,
                     None)
    for k in range(5):
        largo = (0.9, 0.6, 0.75, 0.35, 0.8)[k]
        pant.caja((0.55 + largo / 2 - 0.45, -0.035, zc + 0.55 - k * 0.2), (largo, 0.012, 0.06), None, 0.0)
        c.caja((0.55, -0.03, zc + 0.55 - k * 0.2), (0.9, 0.008, 0.08), gris, 0.0)
    pant.toro((-0.45, -0.036, zc + 0.05), 0.68, 0.012, None, n=24, m=3, rot=(90, 0, 0))
    pant.caja((0.0, -0.035, zc - 0.68), (W - 0.4, 0.012, 0.03), None, 0.0)
    # cableado bajando hasta la canaleta
    c.caja((0.9, 0.08, zc - H / 2 - 0.08), (0.3, 0.1, 0.12), osc, 0.02)
    for k in range(3):
        c.tubo([(0.82 + k * 0.08, 0.06, zc - H / 2 - 0.14), (0.85 + k * 0.08, 0.05, zc - H / 2 - 0.4),
                (0.85 + k * 0.08, 0.06, 0.15)], 0.022, goma, n=4, seg=2)
    c.caja((0.9, 0.06, 0.08), (1.8, 0.12, 0.14), gris, 0.02)  # canaleta
    m.terminar()


# ==============================================================================================================
def extintor():
    m = Modelo("extintor", ZONA, (0.5, 0.5, 1.5), 1500,
               "Extintor: cilindro rojo con etiqueta, manguera con boquilla, palanca con seguro (anilla y precinto), "
               "manómetro y soporte de pared con abrazadera.")
    c = m.parte()
    rojo = m.mat("pintura", "#C0201C", desgaste=0.35, c_desgaste="#8A9097", rug=0.35)
    acero = m.mat("metal", "#9AA0A6", rug=0.3)
    negro = m.mat("plastico", "#1A1B1E")
    blanco = m.mat("plastico", "#F2F0E8")
    papel = m.mat("papel", "#ECE6D2")
    tinta = m.mat("pintura", "#16181A", desgaste=0.0)
    verde = m.mat("plastico", "#2EA04E")
    R = 0.17
    c.torno([(0.0, 0.0), (R - 0.02, 0.0), (R, 0.03), (R, 0.95), (R * 0.75, 1.08), (0.05, 1.12), (0.0, 1.12)], rojo,
            n=16, c=(0, -0.05, 0.05))
    c.cil((0, -0.05, 0.05), (0, -0.05, 0.1), R + 0.01, negro, n=16)
    # cabeza: válvula, palanca, asa y seguro
    c.cil((0, -0.05, 1.15), (0, -0.05, 1.25), 0.05, acero, n=8)
    c.caja((0, -0.05, 1.28), (0.08, 0.14, 0.08), acero, 0.01)
    c.caja((0.0, -0.12, 1.38), (0.05, 0.32, 0.03), acero, 0.005, rot=(-12, 0, 0))  # palanca
    c.caja((0.0, -0.1, 1.24), (0.05, 0.28, 0.025), acero, 0.005)  # asa
    c.cil((-0.06, -0.08, 1.31), (0.06, -0.08, 1.31), 0.01, acero, n=4)  # pasador
    c.toro((0.09, -0.08, 1.31), 0.03, 0.008, acero, n=8, m=3, rot=(0, 90, 0))  # anilla
    c.cil((0.03, -0.08, 1.31), (0.06, -0.04, 1.27), 0.006, verde, n=3)  # precinto
    # manómetro
    c.cil((0.0, -0.05 - 0.06, 1.28), (0.0, -0.05 - 0.09, 1.28), 0.045, acero, n=12)
    c.cil((0.0, -0.05 - 0.09, 1.28), (0.0, -0.05 - 0.092, 1.28), 0.038, blanco, n=12)
    c.caja((0.01, -0.143, 1.29), (0.004, 0.002, 0.03), tinta, 0.0, rot=(0, -30, 0))
    # manguera con boquilla sujeta al costado
    c.tubo([(0.04, 0.0, 1.27), (0.12, 0.05, 1.25), (0.2, 0.0, 1.05), (0.19, -0.05, 0.6), (0.17, -0.1, 0.35)], 0.022,
           negro, n=5, seg=3)
    c.cil((0.17, -0.1, 0.35), (0.16, -0.12, 0.25), 0.035, negro, n=8, r1=0.025)
    c.caja((0.18, -0.06, 0.45), (0.03, 0.06, 0.04), acero, 0.005)
    # etiqueta
    c.lamina(lambda u, v: (math.cos(-math.pi / 2 + (u - 0.5) * 1.4) * (R + 0.004),
                           -0.05 + math.sin(-math.pi / 2 + (u - 0.5) * 1.4) * (R + 0.004), 0.45 + v * 0.35), 6, 1, 0.004,
             papel)
    for k in range(4):
        c.caja((0, -0.05 - R - 0.006, 0.72 - k * 0.07), (0.16 - (k % 2) * 0.05, 0.003, 0.025), tinta, 0.0)
    # soporte de pared con abrazadera
    c.caja((0, 0.18, 0.85), (0.16, 0.04, 0.6), acero, 0.01)
    for z in (0.65, 1.05):
        c.perno((0, 0.16, z), (0, -1, 0), acero, r=0.02)
    c.toro((0, -0.05, 0.8), R + 0.015, 0.012, acero, n=16, m=3)
    c.caja((0, 0.13, 0.45), (0.12, 0.1, 0.03), acero, 0.005)
    m.terminar()


# ==============================================================================================================
def contenedor_envio_grande():
    m = Modelo("contenedor_envio_grande", ZONA, (6, 3, 3), 4000,
               "Contenedor de carga: chapa ondulada, puertas dobles traseras con barras de cierre y candado 3D, "
               "8 cantoneras de acero, rejillas de ventilación y huecos para horquilla de montacargas.")
    c = m.parte()
    puertas = [m.parte(f"puerta_{n}", pivote=(3.0, s * 1.45, 0.2), nota="Hoja de la puerta trasera: gira 270° sobre "
                                                                       "su bisagra.") for n, s in (("izq", 1), ("der", -1))]
    chapa = m.mat("pintura", "#2F6E8E", desgaste=0.6, c_desgaste="#7A4A32", lluvia=0.6, abolladuras=0.3)
    acero = m.mat("metal", "#7A8087")
    osc = m.mat("metal", "#2A2D31", rug=0.5)
    blanco = m.mat("pintura", "#E6E4DC", desgaste=0.5)
    laton = m.mat("metal", "#B9913F", rug=0.3)
    L, W, H = 6.0, 2.9, 2.9
    # bastidor: largueros, testeros y postes de esquina
    for s in (-1, 1):
        for z in (0.1, H - 0.1):
            c.caja((0, s * (W / 2 - 0.08), z), (L, 0.16, 0.2), osc, 0.02)
        for x in (-L / 2 + 0.08, L / 2 - 0.08):
            c.caja((x, s * (W / 2 - 0.08), H / 2), (0.16, 0.16, H), osc, 0.02)
    for x in (-L / 2 + 0.08, L / 2 - 0.08):
        for z in (0.1, H - 0.1):
            c.caja((x, 0, z), (0.16, W, 0.2), osc, 0.02)
    # paredes de chapa ondulada (ondas trapezoidales con grosor)
    # paredes de chapa ondulada: chapa con nervios verticales en relieve (por fuera)
    for s in (-1, 1):
        c.caja((0, s * (W / 2 - 0.1), H / 2), (L - 0.32, 0.03, H - 0.4), chapa)
        for k in range(26):
            x = -L / 2 + 0.3 + k * (L - 0.6) / 25
            c.caja((x, s * (W / 2 - 0.06), H / 2), (0.11, 0.06, H - 0.4), chapa)
    c.caja((-L / 2 + 0.1, 0, H / 2), (0.03, W - 0.32, H - 0.4), chapa)
    for k in range(11):
        y = -W / 2 + 0.3 + k * (W - 0.6) / 10
        c.caja((-L / 2 + 0.06, y, H / 2), (0.06, 0.11, H - 0.4), chapa)
    c.caja((0, 0, H - 0.06), (L - 0.3, W - 0.3, 0.06), chapa, 0.01)
    c.caja((0, 0, 0.16), (L - 0.3, W - 0.3, 0.08), m.mat("madera", "#7A5A3A", eje="X"), 0.0)
    # 8 cantoneras (bloques de esquina ISO con agujeros)
    for sx in (-1, 1):
        for sy in (-1, 1):
            for z in (0.1, H - 0.1):
                p = V((sx * (L / 2 - 0.1), sy * (W / 2 - 0.1), z))
                c.caja(p, (0.24, 0.24, 0.22), acero, 0.02)
                c.caja(p + V((sx * 0.121, 0, 0)), (0.01, 0.1, 0.06), osc, 0.0)
                c.caja(p + V((0, sy * 0.121, 0)), (0.12, 0.01, 0.06), osc, 0.0)
    # rejillas de ventilación en los laterales
    for s in (-1, 1):
        for x in (-2.2, 2.2):
            c.caja((x, s * (W / 2 + 0.0), H - 0.45), (0.4, 0.06, 0.25), osc, 0.01)
            for k in range(3):
                c.caja((x, s * (W / 2 + 0.03), H - 0.53 + k * 0.08), (0.34, 0.02, 0.03), acero, 0.0)
    # huecos para la horquilla (cajones en el larguero inferior)
    for s in (-1, 1):
        for x in (-1.0, 1.0):
            c.caja((x, s * (W / 2 - 0.02), 0.12), (0.6, 0.06, 0.16), m.mat("metal", "#111213", rug=0.9), 0.0)
            c.caja((x, s * (W / 2 + 0.0), 0.12), (0.7, 0.04, 0.22), acero, 0.01)
    # rótulos pintados en el lateral
    c.texto("ORBITRANS", blanco, alto=0.35, grosor=0.012, c=(-0.8, -W / 2 - 0.035, 1.8), fuente="mono", resol=1)
    c.caja((1.8, -W / 2 - 0.03, 2.45), (0.9, 0.01, 0.16), blanco)  # placa CSC
    # puertas dobles traseras (+X): hojas, barras de cierre con levas, manillas y candado
    for k, (hp, s) in enumerate(zip(puertas, (1, -1))):
        ya, yb = sorted((s * 1.45, s * 0.02))
        hp.caja_de((L / 2 - 0.02, ya, 0.22), (L / 2 + 0.04, yb, H - 0.22), chapa, 0.01)
        for z in (0.55, H / 2, H - 0.55):
            hp.caja(((L / 2) + 0.06, s * 1.3, z), (0.05, 0.2, 0.18), acero)  # bisagras
        for yy in (s * 0.4, s * 1.0):
            hp.cil((L / 2 + 0.11, yy, 0.25), (L / 2 + 0.11, yy, H - 0.25), 0.03, acero, n=6)
            for z in (0.25, H - 0.25):
                hp.caja((L / 2 + 0.1, yy, z), (0.08, 0.1, 0.12), acero)
            hp.caja((L / 2 + 0.14, yy + s * 0.15, 1.25), (0.04, 0.32, 0.05), acero, 0.005)  # manilla
            hp.caja((L / 2 + 0.11, yy, 1.25), (0.08, 0.1, 0.16), osc)
    # candado 3D con arco en la manilla central
    cp = V((L / 2 + 0.22, -0.45, 1.05))
    c.caja(cp, (0.06, 0.16, 0.2), laton, 0.02)
    c.toro(cp + V((0, 0, 0.12)), 0.06, 0.014, acero, n=10, m=3, arco=200, rot=(90, 0, 90))
    c.cil(cp + V((0.031, 0, -0.04)), cp + V((0.034, 0, -0.04)), 0.015, osc, n=6)
    m.terminar()


MODELOS = {
    "hangar_principal": hangar_principal,
    "plataforma_aterrizaje": plataforma_aterrizaje,
    "brazo_mecanico_hangar": brazo_mecanico_hangar,
    "consola_control_hangar": consola_control_hangar,
    "rack_piezas_nave": rack_piezas_nave,
    "cable_combustible": cable_combustible,
    "luz_baliza_hangar": luz_baliza_hangar,
    "escalera_nave": escalera_nave,
    "caja_herramientas_hangar": caja_herramientas_hangar,
    "pantalla_estado_nave": pantalla_estado_nave,
    "extintor": extintor,
    "contenedor_envio_grande": contenedor_envio_grande,
}
