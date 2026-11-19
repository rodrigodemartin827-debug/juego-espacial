"""Zona industrial (1): forja, yunque, horno, mesa de crafteo, mina (entrada, vagoneta, raíl, viga) y grúa."""

import math

import arq
from ph import NEON, V, Modelo

ZONA = "industrial"
NARANJA_FORJA = "#FF6B35"


def _yunque(c, x, y, z, acero_osc, cara, s=1.0):
    """Yunque de herrero: talón plano, cintura, pie ancho y cuerno cónico (a lo largo de X)."""
    with c.en((x, y, z), None, s):
        # pie y cintura (loft de secciones rectangulares redondeadas)
        secs = []
        for zz, w, d in ((0.0, 0.62, 0.42), (0.12, 0.6, 0.4), (0.22, 0.36, 0.24), (0.42, 0.3, 0.2), (0.55, 0.62, 0.3)):
            secs.append([(math.copysign(abs(math.cos(a)) ** 0.4, math.cos(a)) * w / 2,
                          math.copysign(abs(math.sin(a)) ** 0.4, math.sin(a)) * d / 2, zz)
                         for a in [i * math.tau / 12 for i in range(12)]])
        c.loft(secs, acero_osc)
        # cuerpo superior y cara de golpeo
        c.caja((-0.05, 0, 0.66), (0.9, 0.3, 0.22), acero_osc, 0.03)
        c.caja((-0.05, 0, 0.78), (0.88, 0.28, 0.03), cara, 0.01)
        # cuerno cónico
        c.loft([[(0.4, math.cos(a) * 0.14, 0.68 + math.sin(a) * 0.1) for a in [i * math.tau / 10 for i in range(10)]],
                [(0.65, math.cos(a) * 0.09, 0.71 + math.sin(a) * 0.07) for a in [i * math.tau / 10 for i in range(10)]],
                [(0.9, math.cos(a) * 0.012, 0.74 + math.sin(a) * 0.012) for a in [i * math.tau / 10 for i in range(10)]]],
               acero_osc)
        # talón con agujeros (hardy y pritchel)
        c.caja((-0.6, 0, 0.7), (0.25, 0.26, 0.15), acero_osc, 0.03)
        c.caja((-0.35, 0.0, 0.795), (0.07, 0.07, 0.01), acero_osc, 0.0)
        c.cil((-0.2, 0.0, 0.79), (-0.2, 0.0, 0.8), 0.025, acero_osc, n=6)


# ==============================================================================================================
def forja_principal():
    m = Modelo("forja_principal", ZONA, (16, 14, 12), 18000,
               "La forja: el edificio de crafteo más importante. Piedra y ladrillo ennegrecidos, chimenea grande con "
               "hollín, puerta corredera de taller sobre raíl, horno con brillo naranja, yunque, lingotes, campana, "
               "herramientas colgadas y suelo manchado de metal fundido.")
    c = m.parte()
    fuego = m.parte("horno_neon", tipo="neon", color=NARANJA_FORJA, nota="Boca y resplandor del horno: Neon #FF6B35.")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    puerta = m.parte("puerta", nota="Puerta de taller corredera, modelada entreabierta. Corre por el raíl hacia la "
                                    "ventana: ver anclajes PuertaCerrada y PuertaAbierta (posición del pivote).")
    cr = m.parte("cristal", tipo="cristal", color="#8EA6AE", transparencia=0.4)

    piedra = m.mat("piedra", "#77706A")
    # hollín de la fachada: manchas sobre la puerta y la ventana (por donde sale el humo del taller)
    ladr = m.mat("ladrillo", "#7A3E2C", c2="#4D4642", manchas=[(2.1, -5.4, 6.4, 1.9, "#1A1612", 0.85),
                                                             (-4.9, -5.4, 5.3, 1.4, "#1A1612", 0.75)])
    madera = m.mat("madera", "#4A3020", eje="X", lluvia=0.7)
    madera_z = m.mat("madera", "#4A3020", eje="Z", lluvia=0.7)
    chapa = m.mat("oxido", "#5E4A3C")
    acero = m.mat("metal", "#6E747A", suciedad=0.7)
    osc = m.mat("metal", "#2A2D31", rug=0.55, suciedad=0.7)
    hierro = m.mat("metal", "#3A3634", rug=0.6, desgaste=0.0, hollin=(0.0, 0.0))
    cara = m.mat("metal", "#9AA0A6", rug=0.3, abolladuras=0.8)
    cobre = m.mat("metal", "#B56A3A", rug=0.35)
    oro = m.mat("metal", "#D6A938", rug=0.25)
    plata = m.mat("metal", "#BFC4C8", rug=0.22)
    tocon = m.mat("madera", "#5A3C24", eje="Z")
    suelo = m.mat("hormigon", "#6E6A64", manchas=[(1.6, -7.0, 0.1, 2.2, "#1A1612", 0.9),
                                                (2.6, -6.5, 0.1, 0.8, "#4A4440", 0.7),
                                                (-0.5, -7.6, 0.1, 0.6, "#0d0b09", 0.8),
                                                (5.6, -6.6, 0.1, 0.9, "#7A3A1E", 0.5)])
    goma = m.mat("goma", "#1C1D20")

    X0, X1, YF, YB, Z0, ZT = -7.6, 7.6, -5.4, 6.4, 0.4, 7.6

    m.seccion("solera y muros")
    c.caja_de((X0 - 0.4, YF - 3.1, 0), (X1 + 0.4, YB + 0.3, Z0), suelo, 0.05)
    # charcos de metal fundido solidificado (relieve irregular)
    for i, (x, y, r) in enumerate(((2.2, -6.8, 0.35), (0.9, -7.3, 0.22), (3.1, -7.5, 0.18), (1.6, -6.3, 0.15))):
        c.ico((x, y, Z0), r, plata if i % 2 else cobre, sub=1, esc=(1.4, 1.0, 0.12), ruido=0.3, semilla=i)
    PUE = (-0.2, 4.4, Z0, 5.8)  # hueco de la puerta del taller
    VEN = (-6.4, -3.4, 2.6, 4.8)
    HOR = (-2.8, -0.9)  # boca del horno que asoma por la fachada (x)
    arq.muro_huecos(c, X0, X1, Z0, 1.6, YF, YF + 0.6, [(PUE[0], PUE[1], Z0, 1.6)], piedra)
    arq.muro_huecos(c, X0, X1, 1.6, ZT, YF, YF + 0.6, [(PUE[0], PUE[1], 1.6, PUE[3]), VEN], ladr)
    for x in (X0, X1 - 0.6):
        c.caja_de((x, YF + 0.6, Z0), (x + 0.6, YB - 0.6, 1.6), piedra)
        c.caja_de((x, YF + 0.6, 1.6), (x + 0.6, YB - 0.6, ZT), ladr)
    c.caja_de((X0, YB - 0.6, Z0), (X1, YB, ZT), ladr)
    # esquinas de sillería
    for x in (X0, X1):
        for y in (YF, YB):
            for k in range(8):
                z = Z0 + 0.2 + k * 0.9
                largo = 0.9 if k % 2 else 0.6
                c.caja((x + (0.05 if x > 0 else -0.05), y + (0.05 if y > 0 else -0.05), z + 0.4),
                       (0.75 if k % 2 else 0.55, 0.75 if k % 2 == 0 else 0.55, 0.8), piedra, 0.06)
    # ventana alta con barrotes y cristal sucio
    vx0, vx1, vz0, vz1 = VEN
    arq.marco(c, vx0, vx1, vz0, vz1, YF, 0.2, 0.15, madera_z)
    cr.caja_de((vx0, YF + 0.2, vz0), (vx1, YF + 0.28, vz1), None)
    for k in range(6):
        x = vx0 + 0.3 + k * (vx1 - vx0 - 0.6) / 5
        c.cil((x, YF + 0.05, vz0), (x, YF + 0.05, vz1), 0.04, hierro, n=6)
    c.caja_de((vx0, YF + 0.0, (vz0 + vz1) / 2 - 0.04), (vx1, YF + 0.1, (vz0 + vz1) / 2 + 0.04), hierro, 0.01)
    luces.caja(((vx0 + vx1) / 2, YF + 0.8, vz1 - 0.2), (2.2, 0.1, 0.06), None)

    m.seccion("tejado")
    # tejado a dos aguas de chapa ondulada oxidada con caballete
    cum = ZT + 2.4
    for s in (-1, 1):
        y_al = YF - 0.6 if s < 0 else YB + 0.6
        p0 = V((0, y_al, ZT - 0.2))
        p1 = V((0, (YF + YB) / 2, cum))
        d = p1 - p0
        ang = math.degrees(math.atan2(d.z, d.y))
        with c.en((p0 + p1) / 2 + V((0, 0, 0.1)), (ang, 0, 0)):
            c.lamina(lambda u, v: (X0 - 0.5 + u * (X1 - X0 + 1.0), (v - 0.5) * d.length,
                                   0.06 * math.sin(u * (X1 - X0 + 1.0) / 0.5 * math.pi)), 64, 1, 0.05, chapa)
    c.cil((X0 - 0.5, (YF + YB) / 2, cum + 0.12), (X1 + 0.5, (YF + YB) / 2, cum + 0.12), 0.18, osc, n=8)
    for x in (X0 - 0.05, X1 + 0.05):
        c.extruir([(YF - 0.1, ZT), (YB + 0.1, ZT), ((YF + YB) / 2, cum)], 0.6, ladr, c=(x + (0.25 if x > 0 else -0.25),
                                                                                     0, 0), rot=(90, 0, 90))
    # lucernario de ventilación en la cumbrera
    c.caja((3.5, (YF + YB) / 2, cum + 0.45), (3.0, 1.2, 0.7), chapa, 0.04)
    for k in range(6):
        c.caja((2.2 + k * 0.5, (YF + YB) / 2 - 0.62, cum + 0.45), (0.06, 0.05, 0.6), osc)

    m.seccion("chimenea grande")
    chx, chy = -4.0, 2.2
    # ladrillo propio con hollín: negro en la boca y se va aclarando hacia abajo
    ladr_ch = m.mat("ladrillo", "#7A3E2C", c2="#4D4642", hollin=(8.0, 11.9))
    c.caja((chx, chy, (ZT + 11.8) / 2), (2.2, 2.2, 11.8 - ZT), ladr_ch, 0.06)
    c.caja((chx, chy, 11.85), (2.6, 2.6, 0.3), m.mat("piedra", "#77706A", hollin=(11.0, 12.2)), 0.05)
    for k in range(3):
        c.caja((chx, chy, ZT + 1.0 + k * 1.3), (2.32, 2.32, 0.14), hierro, 0.02)  # zunchos de hierro
    c.caja((chx, chy, 11.95), (1.5, 1.5, 0.12), m.mat("metal", "#0E0D0C", rug=0.9), 0.0)  # boca negra
    for (dx, dy) in ((-0.9, -0.9), (0.9, 0.9), (-0.9, 0.9), (0.9, -0.9)):
        c.caja((chx + dx, chy + dy, 12.1), (0.35, 0.35, 0.35), m.mat("piedra", "#77706A", hollin=(11.6, 12.3)), 0.04)

    m.seccion("puerta corredera")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.3, 0.25, madera_z, abajo=False)
    # raíl de carril en I con soportes y topes. Corre del hueco hacia el lado de la ventana (-X del modelo), donde
    # cabe la hoja entera cuando se abre del todo sin salirse de la fachada.
    RX0, RX1 = X0 + 0.25, px1 + 0.35
    c.caja_de((RX0, YF - 0.55, pz1 + 0.35), (RX1, YF - 0.25, pz1 + 0.6), osc, 0.03)
    for x in (RX0 + 0.3, (RX0 + px0) / 2, px0 - 0.1, px1 + 0.1):
        c.caja((x, YF - 0.12, pz1 + 0.48), (0.2, 0.3, 0.45), osc, 0.02)
        c.perno((x, YF - 0.29, pz1 + 0.55), (0, -1, 0), acero, r=0.05)
    for x in (RX0, RX1):
        c.caja((x, YF - 0.4, pz1 + 0.35), (0.12, 0.35, 0.25), hierro, 0.02)
    c.caja_de((RX0 + 0.1, YF - 0.6, Z0 - 0.02), (RX1, YF - 0.45, Z0 + 0.04), hierro)
    # hoja: tablones con travesaños en Z y herrajes, colgada de dos carros. Se deja ENTREABIERTA (corrida ABRE studs
    # hacia -X) para que se vea el horno encendido por la rendija.
    W = px1 - px0 + 0.4
    ABRE = 2.1
    hx0 = px0 - 0.2 - ABRE
    pyy = YF - 0.4
    puerta.pivote = V((hx0 + W / 2, pyy, pz0))
    for k in range(9):
        x = hx0 + k * W / 9
        puerta.caja_de((x + 0.02, pyy - 0.1, pz0 + 0.06), (x + W / 9 - 0.02, pyy + 0.04, pz1 + 0.15), madera_z, 0.02)
    for zz in (pz0 + 0.6, (pz0 + pz1) / 2, pz1 - 0.4):
        puerta.caja_de((hx0 + 0.1, pyy - 0.18, zz - 0.15), (hx0 + W - 0.1, pyy - 0.1, zz + 0.15), madera, 0.02)
        for k in range(6):
            puerta.perno((hx0 + 0.35 + k * (W - 0.7) / 5, pyy - 0.18, zz), (0, -1, 0), hierro, r=0.045)
    # diagonal en Z
    a = V((hx0 + 0.3, pyy - 0.15, pz0 + 0.75))
    b = V((hx0 + W - 0.3, pyy - 0.15, (pz0 + pz1) / 2 - 0.15))
    puerta.cil(a, b, 0.1, madera, n=4, giro=math.pi / 4)
    for x in (hx0 + 0.6, hx0 + W - 0.6):
        puerta.caja((x, pyy - 0.2, pz1 + 0.35), (0.12, 0.08, 0.5), hierro, 0.01)
        puerta.cil((x, pyy - 0.3, pz1 + 0.62), (x, pyy - 0.1, pz1 + 0.62), 0.14, hierro, n=10)
    puerta.tubo([(hx0 + W - 0.4, pyy - 0.12, 3.2), (hx0 + W - 0.4, pyy - 0.35, 3.2), (hx0 + W - 0.4, pyy - 0.35, 2.4),
                 (hx0 + W - 0.4, pyy - 0.12, 2.4)], 0.05, hierro, n=6, seg=2)
    m.anclaje("PuertaCerrada", (hx0 + ABRE + W / 2, pyy, pz0), "Pivote de la puerta cerrada (tapa el hueco entero).")
    m.anclaje("PuertaAbierta", (hx0 + ABRE + W / 2 - W, pyy, pz0), "Pivote de la puerta abierta del todo.")
    # interior visible tras la puerta: suelo, fondo y el horno grande
    YI = YF + 0.6
    c.caja_de((px0, YI, Z0), (px1, YB - 0.6, Z0 + 0.02), suelo)
    c.caja_de((px0 - 0.3, YI + 4.5, Z0), (px1 + 0.3, YI + 4.8, ZT), ladr)
    for x in (px0 - 0.3, px1):
        c.caja_de((x, YI, Z0), (x + 0.3, YI + 4.5, ZT), ladr)
    c.caja_de((px0, YI, pz1 + 0.8), (px1, YI + 4.5, pz1 + 1.0), madera)

    m.seccion("horno y campana")
    # horno: cuerpo de ladrillo refractario frente a la rendija de la puerta, con su puerta entreabierta y el brillo
    hx, hy = 3.2, YI + 3.0
    c.caja((hx, hy, Z0 + 1.4), (2.2, 2.4, 2.8), m.mat("ladrillo", "#9A6A4A", c2="#5A524C", tam_ladrillo=(0.35, 0.18),
                                                     hollin=(1.8, 3.2)), 0.05)
    c.caja((hx, hy - 1.22, Z0 + 1.4), (1.4, 0.1, 1.3), hierro, 0.04)  # marco de la boca
    fuego.caja((hx, hy - 1.18, Z0 + 1.4), (1.1, 0.06, 1.0), None)
    with c.en((hx - 0.7, hy - 1.3, Z0 + 1.4), (0, 0, -40)):  # puerta del horno entreabierta
        c.caja((0.6, 0, 0), (1.2, 0.1, 1.15), hierro, 0.03)
        c.cil((1.05, -0.1, 0.1), (1.05, -0.3, 0.1), 0.03, hierro, n=6)
    for zz in (Z0 + 1.0, Z0 + 1.8):
        c.cil((hx - 0.72, hy - 1.28, zz - 0.15), (hx - 0.72, hy - 1.28, zz + 0.15), 0.05, hierro, n=8)
    # campana extractora troncopiramidal sobre el horno y tubo al techo
    c.loft([[(hx + x, hy + y, Z0 + 3.4) for x, y in ((-1.3, -1.6), (1.3, -1.6), (1.3, 1.4), (-1.3, 1.4))],
            [(hx + x, hy + y, Z0 + 4.4) for x, y in ((-0.5, -0.5), (0.5, -0.5), (0.5, 0.5), (-0.5, 0.5))]], chapa)
    c.cil((hx, hy, Z0 + 4.4), (hx, hy, ZT + 0.1), 0.45, osc, n=10)
    # resplandor en el suelo del taller delante del horno y brasas en la bandeja
    fuego.caja((hx, hy - 1.7, Z0 + 0.03), (1.3, 0.6, 0.01), None)
    for k in range(5):
        fuego.ico((hx - 0.4 + k * 0.2, hy - 1.33, Z0 + 0.82), 0.07, None, sub=1, ruido=0.3, semilla=k)
    m.anclaje("LuzHorno", (hx, hy - 1.4, Z0 + 1.4), "PointLight naranja #FF6B35 (Brightness 2-3, Range 14): el "
              "resplandor que sale por la puerta entreabierta.")
    # la luz naranja asoma también por el ventanuco de la fachada
    fuego.caja(((vx0 + vx1) / 2, YF + 0.7, vz0 + 0.2), (2.6, 0.04, 0.4), None)

    m.seccion("tejadillo del yunque")
    # porche de madera a la derecha de la puerta: dos pies derechos, carrera y tablas inclinadas sobre el yunque
    for x in (5.1, 7.45):
        c.caja((x, YF - 2.75, (Z0 + 4.95) / 2), (0.26, 0.26, 4.95 - Z0), madera_z, 0.03)
        c.caja((x, YF - 2.75, Z0 + 0.1), (0.4, 0.4, 0.2), piedra, 0.03)
        c.cil((x, YF - 2.65, 4.3), (x, YF - 1.9, 5.25), 0.07, madera_z, n=6)  # tornapunta
    c.caja_de((4.95, YF - 2.9, 4.95), (7.6, YF - 2.6, 5.2), madera, 0.03)
    ang = math.degrees(math.atan2(6.05 - 5.1, 2.9))
    with c.en((6.28, YF - 1.45, 5.62), (-ang, 0, 0)):
        for k in range(7):
            c.caja((-1.2 + k * 0.4, 0, 0), (0.38, 3.15, 0.08), madera, 0.015)
        for k in range(3):
            c.caja((0, -1.2 + k * 1.2, -0.08), (2.7, 0.12, 0.1), madera_z, 0.01)
    c.caja_de((5.0, YF - 0.05, 5.95), (7.5, YF + 0.0, 6.15), madera, 0.02)  # durmiente contra el muro
    arq.foco_pared(c, luces, (6.3, YF, 4.4), osc, acero)

    m.seccion("yunque, lingotes y herramientas")
    tx, ty = 5.9, YF - 1.6
    c.torno([(0.0, 0.0), (0.55, 0.0), (0.6, 0.15), (0.52, 0.85), (0.5, 0.9), (0.0, 0.9)], tocon, n=12, c=(tx, ty, Z0))
    c.cil((tx, ty, Z0 + 0.9), (tx, ty, Z0 + 0.92), 0.47, m.mat("madera", "#9A7650", eje="Z", patron="vetas"), n=12)
    _yunque(c, tx, ty, Z0 + 0.92, hierro, cara, 1.0)
    # martillo apoyado en el yunque
    with c.en((tx - 0.3, ty + 0.05, Z0 + 1.72), (0, 0, 25)):
        c.cil((0.0, 0, 0.06), (0.7, 0, 0.06), 0.035, tocon, n=6)
        c.caja((0.0, 0, 0.1), (0.14, 0.3, 0.13), hierro, 0.02)
    # lingotes en pirámide (3 + 2 + 1), troncopiramidales
    def lingote(x, y, z, mat):
        c.loft([[(x + dx, y + dy, z) for dx, dy in ((-0.4, -0.15), (0.4, -0.15), (0.4, 0.15), (-0.4, 0.15))],
                [(x + dx, y + dy, z + 0.2) for dx, dy in ((-0.32, -0.1), (0.32, -0.1), (0.32, 0.1), (-0.32, 0.1))]], mat)
    lx, ly = -2.0, YF - 1.3
    c.caja((lx, ly, Z0 + 0.08), (1.4, 1.1, 0.16), madera, 0.02)  # palé
    filas = [[(-0.0, -0.33), (0.0, 0.0), (0.0, 0.33)], [(0.0, -0.17), (0.0, 0.17)], [(0.0, 0.0)]]
    mats = [[acero, cobre, acero], [oro, plata], [oro]]
    for k, fila in enumerate(filas):
        for j, (dx, dy) in enumerate(fila):
            lingote(lx + dx, ly + dy, Z0 + 0.16 + k * 0.2, mats[k][j])
    # ganchos con martillos y tenazas en la pared exterior (la puerta abierta pasa por delante sin tocarlos)
    for i, x in enumerate((-6.6, -5.9, -5.2, -4.5)):
        c.cil((x, YF, 2.15), (x, YF - 0.2, 2.15), 0.03, hierro, n=5)
        c.cil((x, YF - 0.2, 2.15), (x, YF - 0.2, 2.25), 0.03, hierro, n=5)
        if i % 2 == 0:
            c.cil((x, YF - 0.12, 2.1), (x, YF - 0.12, 1.25), 0.04, tocon, n=6)
            c.caja((x, YF - 0.12, 1.2), (0.36, 0.14, 0.14), hierro, 0.02)
        else:
            for s in (-1, 1):
                c.tubo([(x, YF - 0.12, 2.1), (x + s * 0.05, YF - 0.12, 1.5), (x + s * 0.03, YF - 0.12, 1.15),
                        (x + s * 0.01, YF - 0.12, 1.05)], 0.025, hierro, n=4, seg=2)
            c.cil((x - 0.04, YF - 0.12, 1.5), (x + 0.04, YF - 0.12, 1.5), 0.03, hierro, n=5)
    c.caja((-5.6, YF - 0.06, 2.2), (2.6, 0.08, 0.15), madera, 0.02)

    m.seccion("cartel colgante")
    # muestra de forja perpendicular a la fachada: brazo de hierro, tabla con yunque recortado y FORJA a ambos lados
    bx = -1.6
    c.caja((bx, YF - 0.04, 7.0), (0.3, 0.08, 0.5), hierro, 0.02)
    c.cil((bx, YF - 0.05, 7.05), (bx, YF - 1.45, 7.05), 0.04, hierro, n=6)
    c.cil((bx, YF - 0.05, 6.75), (bx, YF - 0.75, 7.05), 0.03, hierro, n=5)
    c.esfera((bx, YF - 1.48, 7.05), 0.05, hierro, seg=6, anillos=4)
    for yy in (YF - 0.55, YF - 1.3):
        c.cil((bx, yy, 7.03), (bx, yy, 6.88), 0.012, hierro, n=4)
        c.toro((bx, yy, 6.88), 0.03, 0.008, hierro, n=6, m=3, rot=(0, 90, 0))
    with c.en((bx, YF - 0.92, 6.45), None):
        c.caja((0, 0, 0), (0.08, 1.1, 0.8), madera_z, 0.02)
        for sx in (-1, 1):
            with c.en((sx * 0.045, 0, 0.08), (90, 0, 90 * sx)):
                c.extruir([(-0.28, 0.12), (0.22, 0.12), (0.34, 0.2), (0.34, 0.24), (-0.32, 0.24), (-0.4, 0.17),
                           (-0.12, 0.12), (-0.12, -0.02), (-0.22, -0.12), (0.18, -0.12), (0.08, -0.02), (0.08, 0.12)],
                          0.02, hierro)
            c.texto("FORJA", m.mat("metal", "#B9913F", rug=0.3), alto=0.16, grosor=0.012,
                    c=(sx * 0.045, 0, -0.32), rot=(90, 0, 90 * sx), fuente="serif", resol=1)

    m.seccion("canaleta de desagüe")
    # canal de piedra con manchas de óxido a lo largo de la fachada hasta una rejilla
    cy = YF - 0.9
    c.caja_de((-7.4, cy - 0.25, Z0 - 0.05), (-0.6, cy + 0.25, Z0 + 0.06), m.mat("piedra", "#6A625A", manchas=[
        (-4.0, cy, Z0, 1.8, "#7A3A1E", 0.8), (-6.2, cy, Z0, 0.9, "#8A4A22", 0.7)]), 0.02)
    c.caja_de((-7.3, cy - 0.12, Z0 + 0.06), (-0.7, cy + 0.12, Z0 + 0.065), m.mat("liquido", "#3A2A1A"))
    c.caja((-0.4, cy, Z0 + 0.04), (0.5, 0.5, 0.06), hierro, 0.01)
    for k in range(4):
        c.caja((-0.55 + k * 0.1, cy, Z0 + 0.08), (0.04, 0.45, 0.04), hierro)
    arq.bajante(c, -7.0, YF, ZT - 0.2, hierro, osc, r=0.12)
    # barril de agua de temple y montón de carbón
    c.torno([(0.0, 0.0), (0.45, 0.0), (0.52, 0.5), (0.45, 1.0), (0.0, 1.0)], madera_z, n=12, c=(4.9, YF - 2.0, Z0))
    for zz in (0.15, 0.85):
        c.toro((4.9, YF - 2.0, Z0 + zz), 0.47, 0.025, hierro, n=12, m=4)
    c.cil((4.9, YF - 2.0, Z0 + 0.85), (4.9, YF - 2.0, Z0 + 0.88), 0.44, m.mat("liquido", "#1E2A2E"), n=12)
    carbon = m.mat("piedra", "#1C1B1A", rug=0.7, suciedad=0.2)
    rnd = m.rnd
    for i in range(16):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0, 0.6)
        x, y = -6.2 + math.cos(a) * r, YF - 1.9 + math.sin(a) * r * 0.7
        c.roca((x, y, Z0 + 0.05 + (0.6 - r) * 0.55), rnd.uniform(0.12, 0.2), carbon, semilla=i)
    c.cil((-5.4, YF - 2.0, Z0), (-5.0, YF - 1.7, Z0 + 1.2), 0.03, tocon, n=5)  # pala
    c.caja((-5.43, YF - 2.02, Z0 + 0.1), (0.3, 0.05, 0.35), hierro, 0.01, rot=(0, -18, 0))
    m.terminar()


# ==============================================================================================================
def yunque_forja():
    m = Modelo("yunque_forja", ZONA, (2, 1, 2), 3000,
               "Yunque grande de herrero sobre tocón con corteza y anillos, con tenazas apoyadas y martillo.")
    c = m.parte()
    hierro = m.mat("metal", "#33363A", rug=0.5, suciedad=0.5)
    cara = m.mat("metal", "#A3A9AF", rug=0.25, abolladuras=1.0, bump=0.8)
    corteza = m.mat("madera", "#4A3424", eje="Z", bump=1.0, patron="piedra", escala=2.0)
    anillos = m.mat("madera", "#B08A5C", eje="Z", suciedad=0.2)
    mango = m.mat("madera", "#8A5C34", eje="Z")
    # tocón: corteza irregular, raíces que se agarran al suelo y cara superior con anillos (diámetro ~0,9: cabe en el
    # fondo de 1 stud pedido y es algo más ancho que el pie del yunque)
    perfil = [(0.0, 0.0), (0.47, 0.0), (0.5, 0.08), (0.43, 0.3), (0.4, 0.8), (0.41, 1.02), (0.0, 1.02)]
    c.torno(perfil, corteza, n=14)
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        c.cil((math.cos(a) * 0.3, math.sin(a) * 0.3, 0.34), (math.cos(a) * 0.55, math.sin(a) * 0.55, 0.0), 0.12, corteza,
              n=6, r1=0.06)
    c.cil((0, 0, 1.02), (0, 0, 1.04), 0.39, anillos, n=14)
    for r in (0.1, 0.2, 0.3):
        c.toro((0, 0, 1.04), r, 0.008, m.mat("madera", "#6E4E30", eje="Z"), n=14, m=3)
    # el yunque
    k = 1.12
    _yunque(c, 0.0, 0.0, 1.04, hierro, cara, k)
    zc = 1.04 + 0.795 * k  # cara de golpeo
    # tenazas apoyadas contra el tocón
    with c.en((0.25, -0.4, 0.0), (10, -16, 15)):
        for s in (-1, 1):
            c.tubo([(s * 0.03, 0, 0.0), (s * 0.05, 0, 0.6), (s * 0.02, 0, 0.88), (-s * 0.04, 0, 1.08)], 0.025, hierro, n=5,
                   seg=2)
        c.cil((-0.05, -0.04, 0.88), (0.05, 0.04, 0.88), 0.035, hierro, n=6)
    # martillo tumbado sobre la cara de golpeo: el mango toca la cara y la cabeza apoya de lado
    with c.en((-0.3, 0.02, zc), (0, 0, 28)):
        c.cil((0.05, 0, 0.04), (0.72, 0, 0.04), 0.04, mango, n=8)
        c.caja((0.0, 0, 0.07), (0.16, 0.34, 0.14), hierro, 0.02)
        c.caja((0.0, 0.2, 0.07), (0.13, 0.06, 0.11), hierro, 0.01)
    m.terminar()


# ==============================================================================================================
def horno_forja():
    m = Modelo("horno_forja", ZONA, (3, 3, 4), 5000,
               "Horno de fundición de ladrillo refractario: puerta de hierro con bisagras y lamas por las que se ve "
               "el fuego (pieza aparte), brillo naranja, arco de dovelas, chimenea trasera con hollín, fuelle de cuero "
               "con palanca de madera y bandeja de cenizas extraíble.")
    c = m.parte()
    fuego = m.parte("fuego_neon", tipo="neon", color=NARANJA_FORJA, nota="Fuego del horno: Neon #FF6B35. Queda bien con "
                                                                         "una PointLight naranja en el anclaje Fuego.")
    puerta = m.parte("puerta", pivote=(-0.62, -1.36, 1.27), nota="Puerta de hierro: gira sobre las bisagras (eje "
                                                                 "vertical del pivote) hasta 110°.")
    bandeja = m.parte("bandeja_cenizas", pivote=(0, -1.25, 0.25), nota="Bandeja de cenizas: se extrae 0,8 studs hacia "
                                                                       "delante.")
    ladr = m.mat("ladrillo", "#B06A44", c2="#5C534D", tam_ladrillo=(0.32, 0.16), manchas=[(0, -1.2, 1.9, 0.9, "#1A1612", 0.8)])
    ladr_ch = m.mat("ladrillo", "#A0603E", c2="#5C534D", tam_ladrillo=(0.32, 0.16), hollin=(3.0, 4.05))
    dovela = m.mat("piedra", "#9A8C7C", hollin=(1.7, 2.3))
    piedra = m.mat("piedra", "#6E6860")
    hierro = m.mat("metal", "#2E2C2B", rug=0.6, suciedad=0.6)
    hollin = m.mat("metal", "#0F0E0D", rug=0.9, suciedad=0.0)
    madera = m.mat("madera", "#6A4628", eje="X")
    madera_z = m.mat("madera", "#6A4628", eje="Z")
    madera_y = m.mat("madera", "#6A4628", eje="Y")
    cuero = m.mat("cuero", "#5E3A22", bump=0.6)
    ceniza = m.mat("piedra", "#3C3A38", rug=1.0)
    carbon = m.mat("piedra", "#1C1B1A", rug=0.7, suciedad=0.1)

    m.seccion("base y cuerpo")
    c.caja((0, 0, 0.25), (2.5, 2.5, 0.5), piedra, 0.06)
    c.caja((0, 0, 1.4), (2.2, 2.2, 1.8), ladr, 0.04)
    c.loft([[(math.cos(a) * 1.1, math.sin(a) * 1.1, 2.3) for a in [i * math.tau / 16 for i in range(16)]],
            [(math.cos(a) * 0.98, math.sin(a) * 0.98, 2.8) for a in [i * math.tau / 16 for i in range(16)]],
            [(math.cos(a) * 0.55, math.sin(a) * 0.55, 3.2) for a in [i * math.tau / 16 for i in range(16)]]], ladr)
    # zunchos de hierro y cantoneras en L remachadas en las cuatro esquinas
    for zz in (0.75, 2.2):
        c.caja((0, 0, zz), (2.28, 2.28, 0.1), hierro, 0.01)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c.caja((sx * 1.1, sy * 0.98, 1.45), (0.06, 0.28, 1.6), hierro, 0.01)
            c.caja((sx * 0.98, sy * 1.1, 1.45), (0.28, 0.06, 1.6), hierro, 0.01)
            for zz in (1.0, 1.9):
                c.remache((sx * 1.13, sy * 0.95, zz), (sx, 0, 0), hierro, 0.03)

    m.seccion("boca, arco y fuego")
    # marco de la boca (cuatro piezas: deja el hueco libre) y fuego al fondo
    yb = -1.1
    for (x, z, w, h) in ((0, 0.78, 1.36, 0.12), (0, 1.76, 1.36, 0.12), (-0.62, 1.27, 0.12, 1.1), (0.62, 1.27, 0.12, 1.1)):
        c.caja((x, yb - 0.17, z), (w, 0.14, h), hierro, 0.02)
    c.caja((0, yb - 0.04, 1.27), (1.12, 0.06, 0.88), hollin, 0.0)  # fondo de la cámara, ennegrecido
    fuego.caja((0, yb - 0.08, 1.27), (1.1, 0.04, 0.86), None)
    for k in range(7):  # brasas en el umbral
        fuego.ico((-0.45 + k * 0.15, yb - 0.16, 0.88), 0.06, None, sub=1, ruido=0.3, semilla=k)
    m.anclaje("Fuego", (0, yb - 0.3, 1.25), "PointLight naranja (Brightness 2, Range 12) delante de la boca.")
    # arco de dovelas sobre la boca (piezas individuales en abanico)
    for k in range(7):
        a = math.radians(160 - k * (140 / 6))
        r = 0.86
        c.caja((math.cos(a) * r, yb - 0.15, 1.6 + math.sin(a) * r * 0.55), (0.26, 0.12, 0.34), dovela, 0.02,
               rot=(0, -(math.degrees(a) - 90) * 0.8, 0))
    # puerta (pieza aparte) cerrada, con lamas: entre ellas se ve el fuego
    with puerta.en((0, 0, 0)):
        xa, xb = -0.6, 0.6
        y0, y1 = yb - 0.3, yb - 0.24
        puerta.caja_de((xa, y0, 0.76), (xb, y1, 0.86), hierro, 0.01)
        puerta.caja_de((xa, y0, 1.68), (xb, y1, 1.78), hierro, 0.01)
        puerta.caja_de((xa, y0, 0.86), (xa + 0.1, y1, 1.68), hierro, 0.01)
        puerta.caja_de((xb - 0.1, y0, 0.86), (xb, y1, 1.68), hierro, 0.01)
        puerta.caja_de((xa + 0.1, y0 + 0.01, 0.86), (xb - 0.1, y1 - 0.01, 1.18), hierro, 0.01)  # chapa inferior
        for k in range(4):
            puerta.caja((0, (y0 + y1) / 2, 1.27 + k * 0.11), (1.0, 0.04, 0.05), hierro, 0.0, rot=(35, 0, 0))
        for zz in (0.95, 1.6):
            puerta.cil((-0.62, yb - 0.26, zz - 0.1), (-0.62, yb - 0.26, zz + 0.1), 0.05, hierro, n=8)
            puerta.caja((-0.45, y0 - 0.01, zz), (0.32, 0.02, 0.08), hierro, 0.0)
        puerta.cil((0.45, y0, 1.1), (0.45, y0 - 0.22, 1.1), 0.03, hierro, n=6)
        puerta.cil((0.35, y0 - 0.22, 1.1), (0.62, y0 - 0.22, 1.1), 0.04, madera, n=6)

    m.seccion("chimenea")
    c.caja((0, 0.55, 3.45), (0.8, 0.8, 1.15), ladr_ch, 0.04)
    c.caja((0, 0.55, 4.03), (0.92, 0.92, 0.1), hierro, 0.01)
    c.caja((0, 0.55, 4.085), (0.5, 0.5, 0.02), hollin, 0.0)  # boca negra

    m.seccion("bandeja de cenizas")
    bandeja.caja((0, -1.0, 0.25), (1.2, 0.5, 0.12), hierro, 0.02)
    bandeja.caja((0, -1.0, 0.3), (1.05, 0.4, 0.04), ceniza, 0.0)
    bandeja.cil((-0.2, -1.32, 0.27), (0.2, -1.32, 0.27), 0.03, hierro, n=6)
    for s in (-1, 1):
        bandeja.cil((s * 0.2, -1.32, 0.27), (s * 0.2, -1.25, 0.27), 0.02, hierro, n=5)
    c.caja((0, -1.24, 0.25), (1.3, 0.04, 0.2), hierro, 0.01)  # boca de la bandeja en el zócalo

    m.seccion("fuelle y palanca")
    # caballete de madera en el lateral +X, fuelle horizontal (tablas en forma de gota, cuero con pliegues)
    fx = 1.45
    for y in (-0.55, 0.45):
        for s in (-1, 1):
            c.cil((fx + s * 0.2, y, 0.0), (fx + s * 0.08, y, 0.8), 0.045, madera_z, n=5)
        c.caja((fx, y, 0.82), (0.5, 0.08, 0.06), madera, 0.01)
    gota = [(0.0, -0.62), (0.16, -0.5), (0.24, -0.2), (0.24, 0.2), (0.16, 0.42), (0.0, 0.5), (-0.16, 0.42), (-0.24, 0.2),
            (-0.24, -0.2), (-0.16, -0.5)]
    c.extruir(gota, 0.05, madera_y, c=(fx, -0.05, 0.9))
    c.extruir(gota, 0.05, madera_y, c=(fx, -0.05, 1.25), rot=(-6, 0, 0))
    c.loft([[(fx + x * 0.95, -0.05 + y * 0.95, z) for x, y in gota] for z in (0.92, 1.0, 1.06, 1.14, 1.2)], cuero)
    for z in (0.99, 1.13):  # pliegues: aros de cuero algo más anchos
        c.loft([[(fx + x * 1.02, -0.05 + y * 1.02, z + dz) for x, y in gota] for dz in (0.0, 0.025)], cuero)
    # boquilla de hierro que entra en el lateral del horno
    c.cil((fx, -0.7, 1.05), (fx, -0.85, 1.05), 0.06, hierro, n=8)
    c.tubo([(fx, -0.85, 1.05), (fx - 0.1, -0.95, 1.05), (1.12, -0.6, 1.1)], 0.045, hierro, n=6, seg=2)
    # palanca: poste trasero, brazo con eje y biela al tablero superior
    c.caja((fx, 0.8, 1.1), (0.14, 0.14, 2.2), madera_z, 0.02)
    eje = V((fx, 0.8, 2.15))
    c.cil(eje + V((-0.1, 0, 0)), eje + V((0.1, 0, 0)), 0.035, hierro, n=6)
    brazo_fin = V((fx, -0.9, 1.75))
    c.cil(eje + V((0, 0.15, 0.06)), brazo_fin, 0.045, madera, n=6)
    c.cil(brazo_fin, brazo_fin + V((0, -0.12, -0.06)), 0.05, cuero, n=6)  # empuñadura
    c.cil(V((fx, 0.05, 1.98)), V((fx, 0.05, 1.3)), 0.02, hierro, n=4)  # biela
    c.caja((fx, 0.05, 1.3), (0.08, 0.08, 0.05), hierro, 0.005)

    m.seccion("atizadores y carbón")
    for k in range(2):
        x = -1.32 - k * 0.08
        c.cil((x, -0.4 + k * 0.25, 0.0), (x + 0.12, -0.35 + k * 0.25, 1.4), 0.025, hierro, n=5)
        c.toro((x + 0.13, -0.35 + k * 0.25, 1.47), 0.06, 0.015, hierro, n=8, m=3, rot=(90, 0, 0))
    # cubo de carbón con asa
    c.torno([(0.0, 0.0), (0.2, 0.0), (0.24, 0.35), (0.22, 0.35), (0.18, 0.04), (0.0, 0.04)], hierro, n=12,
            c=(-1.3, 0.75, 0.0))
    for i in range(6):
        c.roca((-1.3 + math.cos(i) * 0.1, 0.75 + math.sin(i) * 0.1, 0.33), 0.08, carbon, semilla=i)
    c.tubo([(-1.52, 0.75, 0.33), (-1.45, 0.75, 0.55), (-1.15, 0.75, 0.55), (-1.08, 0.75, 0.33)], 0.012, hierro, n=4,
           seg=2)
    m.terminar()


# ==============================================================================================================
def mesa_crafting():
    m = Modelo("mesa_crafting", ZONA, (3, 2, 2.5), 4000,
               "Mesa de trabajo de crafteo: tablero grueso con cortes y quemaduras, panel trasero con herramientas, "
               "tornillo de banco con manivela, cajón, regla clavada y lupa de brazo articulado.")
    c = m.parte()
    cajon = m.parte("cajon", pivote=(0.85, -0.85, 1.1), nota="Cajón lateral: se abre 0,6 studs hacia delante.")
    luz = m.parte("lupa_neon", tipo="neon", color=NEON)
    lupa_cr = m.parte("lupa_cristal", tipo="cristal", color="#D9F1F6", transparencia=0.5)
    tablero = m.mat("madera", "#8A6038", eje="X", manchas=[(0.4, 0.1, 1.45, 0.18, "#1A1410", 0.9),
                                                         (-0.7, -0.3, 1.45, 0.12, "#2A1E14", 0.8)])
    pata = m.mat("madera", "#5E3E22", eje="Z")
    panel = m.mat("madera", "#B08A5E", eje="X", suciedad=0.35)
    acero = m.mat("metal", "#7E848A")
    osc = m.mat("metal", "#2E3236", rug=0.5)
    azul = m.mat("pintura", "#2F5A8A", desgaste=0.6)
    rojo = m.mat("plastico", "#B33A2A")
    mango = m.mat("madera", "#8A5C34", eje="Z")
    Z = 1.45
    c.caja((0, 0, Z - 0.1), (2.9, 1.4, 0.2), tablero, 0.03)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c.caja((sx * 1.3, sy * 0.55, (Z - 0.2) / 2), (0.16, 0.16, Z - 0.2), pata, 0.02)
    c.caja((0, 0.0, 0.35), (2.7, 1.2, 0.06), pata, 0.01)  # balda inferior
    # cortes en el tablero (ranuras finas en relieve)
    for k in range(4):
        c.caja((-0.3 + k * 0.17, 0.1, Z), (0.5, 0.01, 0.01), m.mat("madera", "#3A2616", eje="X"), 0.0,
               rot=(0, 0, 20 + k * 7))
    # panel trasero con marco y herramientas
    c.caja((0, 0.66, Z + 0.55), (2.9, 0.06, 1.1), panel, 0.02)
    for x in (-1.45, 1.45):
        c.caja((x, 0.66, Z + 0.25), (0.1, 0.1, 1.7), pata, 0.01)
    c.caja((0, 0.66, Z + 1.12), (3.0, 0.1, 0.08), pata, 0.01)
    def gancho(x, z):
        c.cil((x, 0.63, z), (x, 0.52, z), 0.012, acero, n=4)
    # llave inglesa
    gancho(-1.1, Z + 0.95)
    c.extruir([(-0.03, 0), (0.03, 0), (0.035, -0.5), (0.09, -0.56), (0.09, -0.66), (0.02, -0.66), (0.02, -0.58),
               (-0.02, -0.58), (-0.02, -0.66), (-0.09, -0.66), (-0.09, -0.56), (-0.035, -0.5)], 0.03, acero,
              c=(-1.1, 0.58, Z + 0.95), rot=(90, 0, 0))
    # destornillador
    gancho(-0.75, Z + 0.95)
    c.cil((-0.75, 0.58, Z + 0.92), (-0.75, 0.58, Z + 0.68), 0.04, rojo, n=8)
    c.cil((-0.75, 0.58, Z + 0.68), (-0.75, 0.58, Z + 0.35), 0.012, acero, n=5)
    # lima
    gancho(-0.45, Z + 0.95)
    c.cil((-0.45, 0.58, Z + 0.92), (-0.45, 0.58, Z + 0.72), 0.035, mango, n=6)
    c.caja((-0.45, 0.58, Z + 0.5), (0.05, 0.015, 0.42), osc, 0.003)
    # sierra de mano
    gancho(0.0, Z + 0.95)
    c.extruir([(0.0, 0.0), (0.1, 0.0), (0.7, -0.15), (0.7, -0.22), (0.1, -0.2)], 0.012, acero, c=(-0.05, 0.58, Z + 0.95),
              rot=(90, 0, 0))
    c.extruir([(-0.2, 0.05), (0.02, 0.05), (0.04, -0.25), (-0.2, -0.25)], 0.05, mango, c=(-0.05, 0.58, Z + 0.95),
              rot=(90, 0, 0))
    # siluetas pintadas detrás de cada herramienta (relieve finísimo)
    for x in (-1.1, -0.75, -0.45, 0.3):
        c.caja((x, 0.627, Z + 0.62), (0.16, 0.004, 0.6), m.mat("pintura", "#2B2B2B", desgaste=0.2), 0.0)
    # tornillo de banco en la esquina delantera derecha
    vx, vy = 1.0, -0.55
    c.caja((vx, vy, Z + 0.1), (0.4, 0.3, 0.2), azul, 0.03)
    c.caja((vx, vy - 0.18, Z + 0.25), (0.42, 0.12, 0.22), azul, 0.03)  # mandíbula fija
    c.caja((vx, vy - 0.45, Z + 0.25), (0.42, 0.12, 0.22), azul, 0.03)  # mandíbula móvil
    for yy in (vy - 0.25, vy - 0.38):
        c.caja((vx, yy, Z + 0.3), (0.4, 0.02, 0.12), osc, 0.0)  # mordazas estriadas
    c.cil((vx, vy - 0.51, Z + 0.2), (vx, vy - 0.2, Z + 0.2), 0.03, acero, n=6)
    for dx in (-0.13, 0.13):  # guías por las que corre la mandíbula móvil
        c.cil((vx + dx, vy - 0.5, Z + 0.17), (vx + dx, vy - 0.12, Z + 0.17), 0.028, acero, n=6)
    c.cil((vx - 0.25, vy - 0.56, Z + 0.2), (vx + 0.25, vy - 0.56, Z + 0.2), 0.022, acero, n=6)  # manivela
    for s in (-1, 1):
        c.esfera((vx + s * 0.26, vy - 0.56, Z + 0.2), 0.04, acero, seg=6, anillos=4)
    # cajón lateral (pieza aparte) con tirador
    cajon.caja((0.85, -0.2, 1.1), (0.9, 1.1, 0.04), pata, 0.01)
    for s in (-1, 1):
        cajon.caja((0.85 + s * 0.43, -0.2, 1.17), (0.04, 1.1, 0.14), pata, 0.01)
    cajon.caja((0.85, -0.74, 1.17), (1.0, 0.05, 0.22), pata, 0.02)
    cajon.cil((0.75, -0.8, 1.18), (0.95, -0.8, 1.18), 0.02, acero, n=6)
    for x in (0.75, 0.95):
        cajon.cil((x, -0.8, 1.18), (x, -0.76, 1.18), 0.015, acero, n=4)
    # regla metálica clavada al borde
    c.caja((-0.3, -0.71, Z - 0.05), (1.6, 0.012, 0.08), acero, 0.0)
    for k in range(16):
        c.caja((-1.05 + k * 0.1, -0.718, Z - 0.03 + (0.01 if k % 2 else 0)), (0.006, 0.004, 0.03), osc, 0.0)
    for x in (-1.0, 0.4):
        c.cil((x, -0.72, Z - 0.05), (x, -0.73, Z - 0.05), 0.012, acero, n=5)
    # lupa con brazo articulado (base, dos tramos, codo y anillo con luz)
    lx, ly = -1.2, -0.3
    c.cil((lx, ly, Z), (lx, ly, Z + 0.08), 0.12, osc, n=10)
    a = V((lx, ly, Z + 0.08))
    b = V((lx + 0.1, ly + 0.2, Z + 0.6))
    d = V((lx + 0.45, ly - 0.05, Z + 0.75))
    c.cil(a, b, 0.025, acero, n=6)
    c.esfera(b, 0.045, osc, seg=6, anillos=4)
    c.cil(b, d, 0.022, acero, n=6)
    c.tubo([(b.x - 0.02, b.y, b.z - 0.05), (b.x + 0.15, b.y, b.z - 0.25)], 0.008, m.mat("cromo", "#CCCCCC"), n=4,
           suave=False)  # muelle tensor
    with c.en(d + V((0.12, 0, -0.08)), (70, 0, 20)):
        c.toro((0, 0, 0), 0.13, 0.025, osc, n=14, m=4)
        luz.toro((0, 0, -0.02), 0.11, 0.008, None, n=14, m=3)
    lupa_cr.cil(d + V((0.12, 0, -0.08)), d + V((0.12, 0.01, -0.09)), 0.11, None, n=14)
    m.terminar()


# ==============================================================================================================
def entrada_mina():
    m = Modelo("entrada_mina", ZONA, (6, 6, 5), 8000,
               "Entrada de la Mina Sector 7: frente de roca en estratos con el arco de vigas en H (marco de 4 vigas y 2 "
               "diagonales), túnel con entibado, raíles que salen de la boca, cartel de chapa con flecha, bombillas en "
               "el techo, pico y casco colgados, botiquín y cables por el techo del arco.")
    c = m.parte()
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    roca = m.mat("piedra", "#857A6C", escala=0.8)
    roca2 = m.mat("piedra", "#6E6458", escala=0.8)
    roca3 = m.mat("piedra", "#9A8E7C", escala=0.8)
    viga = m.mat("pintura", "#C79A2A", desgaste=0.8, c_desgaste="#5A5048")
    acero = m.mat("metal", "#6E747A", suciedad=0.7)
    madera = m.mat("madera", "#5A3C26", eje="X")
    madera_y = m.mat("madera", "#5A3C26", eje="Y")
    chapa = m.mat("pintura", "#D8CFB8", desgaste=0.7, c_desgaste="#6E4A32")
    tinta = m.mat("pintura", "#202428", desgaste=0.2)
    rojo = m.mat("pintura", "#B8282A", desgaste=0.5)
    cable = m.mat("goma", "#1B1C1E")
    mango = m.mat("madera", "#8A5C34", eje="Z")
    tierra = m.mat("piedra", "#5A4C3E", bump=0.6, escala=1.6, manchas=[(0.0, -2.0, 0.0, 1.4, "#3A3028", 0.5)])
    negro = m.mat("piedra", "#0E0D0C", rug=1.0, suciedad=0.0)
    rnd = m.rnd
    W, H = 3.4, 3.8  # hueco del túnel (ancho, alto)
    YP = -1.55  # cara del frente de roca
    YE = 2.7  # fondo del túnel

    def losa(cx, cy, cz, sx, sy, sz):
        """Losa de roca irregular: caja con chaflán, tamaño y giro algo aleatorios (estratos)."""
        mat = (roca, roca2, roca3)[rnd.randrange(3)]
        c.caja((cx + rnd.uniform(-0.05, 0.05), cy + rnd.uniform(-0.08, 0.08), cz),
               (sx * rnd.uniform(0.95, 1.08), sy * rnd.uniform(0.9, 1.1), sz * rnd.uniform(0.92, 1.0)), mat,
               b=min(0.14, sz * 0.25), rot=(rnd.uniform(-4, 4), rnd.uniform(-5, 5), rnd.uniform(-4, 4)))

    def fila(z0, alto, x0, x1, cy, fondo, hueco=None):
        x = x0
        while x < x1 - 0.05:
            w = min(rnd.uniform(0.9, 1.6), x1 - x)
            if hueco and x + w > hueco[0] and x < hueco[1]:
                # recorta la losa al borde del hueco
                if x < hueco[0]:
                    w = hueco[0] - x
                else:
                    x = hueco[1]
                    continue
            losa(x + w / 2, cy, z0 + alto / 2, w + 0.04, fondo, alto)
            x += w

    m.seccion("suelo y túnel")
    c.caja((0, 0, -0.05), (6.0, 6.0, 0.1), tierra, 0.02)
    c.caja((0, YE + 0.1, H / 2), (W + 0.2, 0.2, H), negro, 0.0)  # fondo oscuro del túnel
    for s in (-1, 1):
        c.caja((s * (W / 2 + 0.2), (YP + YE) / 2 + 0.3, H / 2 + 0.1), (0.4, YE - YP, H + 0.2), roca2, 0.05)
    c.caja((0, (YP + YE) / 2 + 0.3, H + 0.35), (W + 0.8, YE - YP, 0.5), roca2, 0.05)
    # entibado: tablas del techo del túnel
    for k in range(8):
        c.caja((0, YP + 0.35 + k * 0.5, H + 0.06), (W + 0.25, 0.42, 0.1), madera, 0.02)

    m.seccion("frente y ladera de roca")
    # frente en estratos alrededor del hueco
    alturas = [1.0, 1.0, 0.95, 0.95, 1.1]
    z = 0.0
    for k, a in enumerate(alturas):
        hueco = (-W / 2 - 0.3, W / 2 + 0.3) if z < H else None
        fila(z, a, -3.0, 3.0, YP + 0.45, 0.9, hueco)
        z += a
    # laterales de la ladera (losas a lo largo de Y)
    for sx in (-1, 1):
        z = 0.0
        for k, a in enumerate([1.3, 1.3, 1.3]):
            y = YP + 0.9
            while y < YE + 0.25:
                d = min(rnd.uniform(1.4, 2.1), YE + 0.3 - y)
                losa(sx * 2.62, y + d / 2, z + a / 2, 0.75, d + 0.04, a)
                y += d
            z += a
    # techo de la ladera, bajando hacia atrás, y espalda
    for k in range(4):
        y = YP + 0.9 + k * 1.05
        ztop = 4.95 - k * 0.32
        fila(ztop - 0.9, 0.9, -3.0, 3.0, y + 0.52, 1.1)
    z = 0.0
    for k, a in enumerate([1.0, 1.0, 1.05, 0.9]):
        fila(z, a, -3.0, 3.0, YE + 0.35, 0.6)
        z += a
    # piedras sueltas al pie del frente
    for i in range(3):
        x = rnd.choice((-1, 1)) * rnd.uniform(2.0, 2.8)
        c.roca((x, YP - rnd.uniform(0.2, 0.9), 0.12), rnd.uniform(0.15, 0.3), roca2, semilla=i, ruido=0.3)

    m.seccion("marcos en H")
    for k, y in enumerate((YP - 0.05, 0.9)):
        for s in (-1, 1):
            arq.viga_h(c, (s * W / 2, y, 0.0), (s * W / 2, y, H), 0.32, 0.3, viga)
            c.caja((s * W / 2, y, 0.06), (0.5, 0.5, 0.12), acero, 0.01)  # placa base
            for dx in (-0.18, 0.18):
                c.perno((s * W / 2 + dx, y + 0.18, 0.12), (0, 0, 1), acero, r=0.04)
        arq.viga_h(c, (-W / 2 - 0.15, y, H), (W / 2 + 0.15, y, H), 0.36, 0.3, viga)
        for s in (-1, 1):  # cartelas en las esquinas
            c.extruir([(0, 0), (s * -0.6, 0), (0, -0.6)], 0.04, acero, c=(s * W / 2, y - 0.0, H - 0.18), rot=(90, 0, 0))
    # el marco de la boca lleva una cuarta viga (cabecero) y dos diagonales de refuerzo
    arq.viga_h(c, (-W / 2 - 0.3, YP - 0.25, H + 0.55), (W / 2 + 0.3, YP - 0.25, H + 0.55), 0.36, 0.3, viga)
    for s in (-1, 1):
        c.caja((s * W / 2, YP - 0.2, H + 0.3), (0.3, 0.3, 0.5), viga, 0.02)
        c.cil((s * W / 2, YP - 0.2, 1.7), (s * (W / 2 - 1.05), YP - 0.2, H - 0.2), 0.08, viga, n=4, giro=math.pi / 4)

    m.seccion("raíles")
    for s in (-1, 1):
        c.caja((s * 0.6, (YE - 3.0) / 2, 0.1), (0.07, YE + 3.0, 0.06), acero, 0.005)  # hasta el borde del suelo
        c.caja((s * 0.6, (YE - 3.0) / 2, 0.05), (0.14, YE + 3.0, 0.03), acero, 0.0)
    for k in range(4):
        y = -2.8 + k * 1.4
        c.caja((0, y, 0.03), (1.8, 0.25, 0.1), madera, 0.02)
        for s in (-1, 1):
            c.perno((s * 0.6 + 0.1, y, 0.08), (0, 0, 1), acero, r=0.025, arandela=False)
    for k in range(3):
        c.caja((0, 0.4 + k * 1.0, 0.03), (1.8, 0.25, 0.1), madera, 0.02)

    m.seccion("cartel, luces y cables")
    # cartel MINA SECTOR 7 pintado en chapa con flecha, colgado del cabecero
    zc = H + 0.55
    c.caja((0, YP - 0.45, zc - 0.05), (2.7, 0.05, 0.62), chapa, 0.01)
    c.texto("MINA SECTOR 7", tinta, alto=0.24, grosor=0.01, c=(-0.25, YP - 0.48, zc - 0.13), fuente="estrecha", resol=1)
    c.extruir([(0, 0.06), (0.3, 0.06), (0.3, 0.14), (0.45, 0.0), (0.3, -0.14), (0.3, -0.06), (0, -0.06)], 0.01, rojo,
              c=(1.0, YP - 0.48, zc - 0.05), rot=(90, 0, 0))
    for x in (-1.15, 1.15):
        c.perno((x, YP - 0.48, zc + 0.14), (0, -1, 0), acero, r=0.03)
    # tres bombillas con rejilla protectora colgando del techo del túnel, unidas por un cable
    puntos = []
    for k in range(3):
        y = YP + 0.6 + k * 1.3
        c.cil((0.0, y, H - 0.02), (0.0, y, H - 0.3), 0.025, cable, n=5)
        c.cil((0.0, y, H - 0.3), (0.0, y, H - 0.42), 0.09, acero, n=8)
        luces.esfera((0.0, y, H - 0.58), 0.13, None, seg=10, anillos=6)
        for j in range(3):  # rejilla
            a = j * math.tau / 3
            c.tubo([(math.cos(a) * 0.09, y + math.sin(a) * 0.09, H - 0.42),
                    (math.cos(a) * 0.17, y + math.sin(a) * 0.17, H - 0.58), (0.0, y, H - 0.76)], 0.012, acero, n=4,
                   seg=2)
        puntos.append((0.0, y, H - 0.03))
    c.tubo([(0.0, YP - 0.1, H - 0.05)] + puntos + [(0.0, YE, H - 0.03)], 0.03, cable, n=5, suave=False)
    # cables por el techo del arco que bajan a una caja de conexiones
    c.tubo([(-W / 2 + 0.25, YP - 0.15, 0.9), (-W / 2 + 0.25, YP - 0.18, H - 0.35), (-W / 2 + 0.6, YP - 0.2, H - 0.12),
            (W / 2 - 0.6, YP - 0.2, H - 0.12), (W / 2 - 0.25, YP - 0.18, H - 0.35)], 0.035, cable, n=5, seg=3)
    for x in (-1.0, 0.0, 1.0):
        c.caja((x, YP - 0.2, H - 0.12), (0.06, 0.1, 0.1), acero, 0.0)  # grapas
    c.caja((-W / 2 + 0.25, YP - 0.2, 0.75), (0.3, 0.14, 0.4), acero, 0.02)

    m.seccion("pico, casco y botiquín")
    gx = -W / 2 - 0.45
    c.cil((gx, YP - 0.02, 2.4), (gx, YP - 0.22, 2.4), 0.025, acero, n=5)
    c.cil((gx, YP - 0.22, 2.4), (gx, YP - 0.22, 2.5), 0.025, acero, n=5)
    with c.en((gx, YP - 0.2, 1.75)):
        c.cil((0, 0, -1.0), (0, 0, 0.6), 0.04, mango, n=6)
        c.tubo([(-0.55, 0, 0.5), (-0.2, 0, 0.65), (0.2, 0, 0.65), (0.55, 0, 0.5)], 0.04, acero, n=6, seg=2, r_fin=0.01)
    c.cil((gx + 0.75, YP - 0.02, 3.05), (gx + 0.75, YP - 0.22, 3.05), 0.025, acero, n=5)
    with c.en((gx + 0.75, YP - 0.32, 2.88)):
        c.esfera((0, 0, 0), 0.24, m.mat("plastico", "#E5B82A"), seg=10, anillos=6, esc=(1, 1.1, 0.75))
        c.cil((0, 0, -0.04), (0, 0, 0.0), 0.3, m.mat("plastico", "#E5B82A"), n=12)  # ala
        c.cil((0, -0.22, 0.05), (0, -0.28, 0.05), 0.06, acero, n=8)
        luces.cil((0, -0.28, 0.05), (0, -0.29, 0.05), 0.05, None, n=8)
    # botiquín rojo en la roca, a la derecha de la boca
    bx = W / 2 + 0.75
    c.caja((bx, YP - 0.15, 1.8), (0.5, 0.3, 0.55), rojo, 0.03)
    c.caja((bx, YP - 0.31, 1.82), (0.3, 0.02, 0.08), m.mat("plastico", "#F2F2F2"), 0.0)
    c.caja((bx, YP - 0.31, 1.82), (0.08, 0.02, 0.3), m.mat("plastico", "#F2F2F2"), 0.0)
    c.caja((bx + 0.22, YP - 0.32, 1.8), (0.04, 0.03, 0.12), acero, 0.005)
    m.terminar()


# ==============================================================================================================
def vagoneta_mina():
    m = Modelo("vagoneta_mina", ZONA, (3, 2, 2), 4000,
               "Vagoneta de mina: caja de metal remachada, cuatro ruedas con pestaña y ejes, carga de minerales de "
               "colores, palanca de freno lateral y enganches delante y detrás.")
    c = m.parte()
    brillo = m.parte("minerales_neon", tipo="neon", color=NEON, nota="Las vetas de cristal azul brillante de la carga.")
    freno = m.parte("freno", pivote=(0.55, -0.82, 0.55), nota="Palanca de freno: gira 25° hacia delante.")
    chapa = m.mat("pintura", "#5E6A44", desgaste=0.75, abolladuras=0.5, c_desgaste="#6E5040")
    acero = m.mat("metal", "#5E6268", suciedad=0.6)
    oxido = m.mat("oxido", "#6A4430")
    rueda = m.mat("metal", "#3A3C40", rug=0.45)
    gris = m.mat("piedra", "#7A7672")
    ambar = m.mat("organico", "#D8902A", rug=0.3)
    verde = m.mat("piedra", "#5A7A4E")
    azul = m.mat("organico", "#3A7FC4", rug=0.2)
    madera = m.mat("madera", "#6A4628", eje="Z")
    Z = 0.55
    # caja troncopiramidal HUECA: fondo y cuatro paredes de chapa con grosor (cada una es un sólido cerrado)
    G = 0.08
    c.caja((0, 0, Z + G / 2), (2.3, 1.2, G), chapa, 0.01)

    def pared(q, hacia):
        """q: 4 esquinas (abajo-izq, abajo-der, arriba-der, arriba-izq) de la cara exterior; hacia: vector al interior."""
        d = V(hacia).normalized() * G
        c.loft([[V(p) for p in q], [V(p) + d for p in q]], chapa)

    for s in (-1, 1):
        pared([(-1.15, s * 0.6, Z), (1.15, s * 0.6, Z), (1.4, s * 0.82, Z + 1.0), (-1.4, s * 0.82, Z + 1.0)], (0, -s, 0))
        pared([(s * 1.15, -0.6, Z), (s * 1.15, 0.6, Z), (s * 1.4, 0.82, Z + 1.0), (s * 1.4, -0.82, Z + 1.0)], (-s, 0, 0))
    # capa de grava dentro (lo que asoma entre las piedras grandes)
    c.loft([[(x * 0.96, y * 0.96, Z + 0.78) for x, y in ((-1.33, -0.75), (1.33, -0.75), (1.33, 0.75), (-1.33, 0.75))],
            [(x * 0.96, y * 0.96, Z + 0.84) for x, y in ((-1.33, -0.75), (1.33, -0.75), (1.33, 0.75), (-1.33, 0.75))]],
           m.mat("piedra", "#4E4A46", bump=1.0, escala=3.0))
    for s in (-1, 1):
        c.caja((0, s * 0.83, Z + 1.02), (2.9, 0.08, 0.08), acero, 0.01)
        c.caja((s * 1.42, 0, Z + 1.02), (0.08, 1.7, 0.08), acero, 0.01)
    # junta central y remaches
    for s in (-1, 1):
        ang = math.degrees(math.atan2(0.22, 1.0))
        c.caja((0, s * 0.72, Z + 0.5), (0.12, 0.04, 1.02), acero, 0.005, rot=(s * ang, 0, 0))
        for k in range(5):
            z = Z + 0.1 + k * 0.2
            y = s * (0.6 + 0.22 * (z - Z))
            for x in (-0.08, 0.08):
                c.remache((x, y + s * 0.02, z), (0, s, 0.2), acero, 0.03)
            for x in (-1.15 - 0.25 * (z - Z), 1.15 + 0.25 * (z - Z)):
                c.remache((x * 0.97, y + s * 0.01, z), (0, s, 0.2), acero, 0.03)
    # bastidor, ejes y ruedas con pestaña
    for s in (-1, 1):
        c.caja((0, s * 0.42, Z - 0.08), (2.3, 0.12, 0.16), acero, 0.02)
    for x in (-0.75, 0.75):
        c.cil((x, -0.75, 0.3), (x, 0.75, 0.3), 0.05, acero, n=8)
        for s in (-1, 1):
            c.cil((x, s * 0.5, 0.3), (x, s * 0.6, 0.3), 0.3, rueda, n=14)
            c.cil((x, s * 0.47, 0.3), (x, s * 0.5, 0.3), 0.35, rueda, n=14)  # pestaña
            c.cil((x, s * 0.6, 0.3), (x, s * 0.66, 0.3), 0.08, acero, n=8)
            c.caja((x, s * 0.43, 0.48), (0.3, 0.06, 0.25), acero, 0.01)  # cojinete
    # enganches
    for s in (-1, 1):
        c.caja((s * 1.25, 0, Z - 0.05), (0.3, 0.2, 0.12), acero, 0.02)
        c.toro((s * 1.48, 0, Z - 0.05), 0.09, 0.025, acero, n=8, m=4)
    # carga: piedras de colores y cristales
    rnd = m.rnd
    mats = [gris, gris, ambar, verde, gris]
    for i in range(20):
        x = rnd.uniform(-1.05, 1.05)
        y = rnd.uniform(-0.55, 0.55)
        r = rnd.uniform(0.17, 0.3)
        z = Z + 0.85 + rnd.uniform(0, 0.25) - abs(x) * 0.1
        c.roca((x, y, z), r, mats[i % 5], semilla=i, ruido=0.3)
    for i in range(4):
        x = -0.7 + i * 0.45
        c.cil((x, 0.1 * (-1) ** i, Z + 0.95), (x + 0.1, 0.15 * (-1) ** i, Z + 1.45), 0.09, azul, n=6, r1=0.0)
        brillo.cil((x, 0.1 * (-1) ** i, Z + 0.97), (x + 0.07, 0.13 * (-1) ** i, Z + 1.32), 0.04, None, n=5, r1=0.0)
    # palanca de freno (pieza aparte) con zapata
    freno.cil((0.55, -0.82, 0.55), (0.75, -0.86, 1.5), 0.035, acero, n=6)
    freno.esfera((0.75, -0.86, 1.52), 0.06, madera, seg=6, anillos=4, esc=(1, 1, 1.6))
    freno.caja((0.62, -0.62, 0.3), (0.3, 0.08, 0.12), madera, 0.02)
    c.cil((0.55, -0.9, 0.55), (0.55, -0.7, 0.55), 0.05, acero, n=8)
    m.terminar()


# ==============================================================================================================
def rail_mina():
    m = Modelo("rail_mina", ZONA, (4, 1, 0.3), 1000,
               "Segmento modular de raíl de mina: dos rieles con perfil en T sobre tres traviesas de madera con "
               "clavos y placas de fijación. Se encadena extremo con extremo (4 studs).")
    c = m.parte()
    acero = m.mat("metal", "#6A6E74", aranazos=0.8)
    madera = m.mat("madera", "#5A3E28", eje="Y", lluvia=0.6)
    clavo = m.mat("metal", "#3A3634", rug=0.6)
    L = 4.0
    for k in range(3):
        x = -L / 2 + 0.6 + k * (L - 1.2) / 2
        c.caja((x, 0, 0.06), (0.28, 1.0, 0.12), madera, 0.02)
    for s in (-1, 1):
        y = s * 0.3
        c.extruir([(-0.06, 0.12), (0.06, 0.12), (0.06, 0.15), (0.02, 0.17), (0.02, 0.26), (0.045, 0.27), (0.045, 0.3),
                   (-0.045, 0.3), (-0.045, 0.27), (-0.02, 0.26), (-0.02, 0.17), (-0.06, 0.15)], L, acero,
                  c=(0, y, 0), rot=(90, 0, 90))
        for k in range(3):
            x = -L / 2 + 0.6 + k * (L - 1.2) / 2
            c.caja((x, y, 0.13), (0.22, 0.24, 0.025), clavo, 0.005)
            for dy in (-0.08, 0.08):
                c.cil((x, y + dy, 0.12), (x, y + dy, 0.17), 0.018, clavo, n=4)
                c.caja((x, y + dy - 0.01 * (1 if dy > 0 else -1), 0.17), (0.05, 0.04, 0.012), clavo, 0.0)
    m.notas.append("Los rieles van de x=-2 a x=+2 exactos: coloca los segmentos cada 4 studs en el eje X de Roblox.")
    m.terminar()


# ==============================================================================================================
def viga_mina():
    m = Modelo("viga_mina", ZONA, (3, 0.5, 5), 3000,
               "Marco de entibado en H: dos postes de 0,5 × 0,5 × 5 y travesaño de 3 × 0,5 × 0,5 de madera gruesa con "
               "nudos y vetas, placas de refuerzo con pernos en las uniones y cuñas en la base.")
    c = m.parte()
    madera = m.mat("madera", "#6A4A2E", eje="Z", bump=0.8)
    madera_x = m.mat("madera", "#6A4A2E", eje="X", bump=0.8)
    acero = m.mat("metal", "#55595E", rug=0.5, suciedad=0.6)
    oxido = m.mat("oxido", "#6A4430")
    cuna = m.mat("madera", "#8A6A44", eje="X")
    for s in (-1, 1):
        x = s * 1.25
        c.caja((x, 0, 2.5), (0.5, 0.5, 5.0), madera, 0.04)
        # cuñas en la base
        c.extruir([(0, 0), (0.35, 0), (0, 0.22)], 0.36, cuna, c=(x - s * 0.25, 0, 0.0), rot=(90, 0, 0 if s > 0 else 180))
    c.caja((0, 0, 4.35), (3.0, 0.5, 0.5), madera_x, 0.04)
    # placas en las uniones (delante y detrás), con 4 pernos cada una
    for s in (-1, 1):
        for cara in (-1, 1):
            y = cara * 0.27
            c.extruir([(-0.3, -0.5), (0.3, -0.5), (0.3, 0.3), (-0.3 + 0.0, 0.3)], 0.03, acero,
                      c=(s * 1.1, y, 4.3), rot=(90, 0, 0))
            for (dx, dz) in ((-0.15, -0.35), (0.15, -0.35), (-0.15, 0.15), (0.15, 0.15)):
                c.perno((s * 1.1 + dx, y + cara * 0.015, 4.3 + dz), (0, cara, 0), acero, r=0.045)
        # tornapunta diagonal
        c.caja((s * 0.8, 0, 3.8), (0.25, 0.4, 0.9), madera, 0.03, rot=(0, -s * 45, 0))
    m.terminar()


# ==============================================================================================================
def grua_carga():
    m = Modelo("grua_carga", ZONA, (4, 3, 8), 8000,
               "Grúa de carga: base giratoria con rodamiento, brazo articulado de dos secciones con pasador en el "
               "codo, tambor con cable y manivela, gancho con seguro, contrapeso y panel con dos palancas.")
    c = m.parte()
    giro = m.parte("giratoria", pivote=(0, 0, 1.0), nota="Todo lo que gira sobre la base (eje vertical del pivote).")
    gancho = m.parte("gancho", pivote=(1.95, 0, 7.6), nota="Gancho y cable: cuelga del pivote; para subir/bajar, "
                                                          "mover en Y de Roblox y escalar el cable.")
    amarillo = m.mat("pintura", "#E3A21E", desgaste=0.7)
    osc = m.mat("metal", "#2C3036", rug=0.5)
    acero = m.mat("metal", "#7A8087")
    horm = m.mat("hormigon", "#8E8A84")
    cable = m.mat("metal", "#4A4D52", rug=0.6, bump=0.6, patron="tejido")
    rojo = m.mat("plastico", "#C2302A")
    negro = m.mat("plastico", "#1F2125")
    # base fija: zapata de hormigón, pedestal y corona del rodamiento con pernos
    c.caja((0, 0, 0.2), (3.0, 2.8, 0.4), horm, 0.06)
    c.cil((0, 0, 0.4), (0, 0, 0.85), 0.75, amarillo, n=16)
    c.cil((0, 0, 0.85), (0, 0, 0.95), 0.95, osc, n=20)
    for k in range(12):
        a = k * math.tau / 12
        c.perno((math.cos(a) * 0.85, math.sin(a) * 0.85, 0.95), (0, 0, 1), acero, r=0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            c.perno((sx * 1.3, sy * 1.2, 0.4), (0, 0, 1), acero, r=0.06)
    # parte giratoria: corona dentada visible, plataforma, columna
    giro.cil((0, 0, 0.95), (0, 0, 1.08), 0.9, acero, n=20)
    for k in range(24):
        a = k * math.tau / 24
        giro.caja((math.cos(a) * 0.92, math.sin(a) * 0.92, 1.01), (0.08, 0.06, 0.12), acero, 0.0,
                  rot=(0, 0, math.degrees(a)))
    giro.caja((-0.2, 0, 1.25), (2.2, 1.4, 0.3), amarillo, 0.05)
    giro.caja((0, 0, 2.7), (0.55, 0.55, 2.6), amarillo, 0.05)
    # contrapeso trasero (bloques)
    for k in range(3):
        giro.caja((-1.1, 0, 1.55 + k * 0.32), (0.6, 1.2, 0.3), m.mat("hormigon", "#5A5854"), 0.04)
    giro.caja((-1.1, 0, 2.6), (0.7, 1.3, 0.08), osc, 0.01)
    # brazo: tramo 1 (columna -> codo) y tramo 2 (codo -> punta), en celosía con pasadores
    hombro = V((0, 0, 4.0))
    codo = V((0.5, 0, 6.8))
    punta = V((1.95, 0, 7.7))
    giro.cil((0, -0.35, 4.0), (0, 0.35, 4.0), 0.12, osc, n=10)
    for s in (-1, 1):
        giro.caja(hombro + V((0, s * 0.22, -0.1)), (0.4, 0.06, 0.6), amarillo, 0.02)
    def tramo(a, b, alto):
        d = b - a
        L = d.length
        u = d.normalized()
        lado = V((0, 1, 0))
        arriba = u.cross(lado)
        for sy in (-1, 1):
            for sz in (-1, 1):
                off = lado * sy * 0.15 + arriba * sz * alto / 2
                giro.cil(a + off, b + off, 0.04, amarillo, n=5)
        n = int(L / 0.45)
        for i in range(n):
            p = a + u * (L * i / n)
            q = a + u * (L * (i + 1) / n)
            for sy in (-1, 1):
                giro.cil(p + lado * sy * 0.15 + arriba * alto / 2, q + lado * sy * 0.15 - arriba * alto / 2, 0.022,
                         amarillo, n=4)
    tramo(hombro, codo, 0.3)
    tramo(codo, punta, 0.24)
    giro.cil(codo + V((0, -0.3, 0)), codo + V((0, 0.3, 0)), 0.1, osc, n=10)  # pasador del codo
    for s in (-1, 1):
        giro.cil(codo + V((0, s * 0.3, 0)), codo + V((0, s * 0.34, 0)), 0.14, acero, n=8)
        giro.caja(codo + V((0, s * 0.24, 0)), (0.32, 0.05, 0.32), osc, 0.02)
    # cilindro hidráulico del codo
    giro.cil(V((0.3, 0, 3.1)), V((0.42, 0, 5.6)), 0.07, osc, n=8)
    giro.cil(V((0.4, 0, 5.0)), V((0.5, 0, 6.6)), 0.04, m.mat("cromo", "#D0D4D8"), n=8)
    # polea de la punta
    giro.cil(punta + V((0, -0.1, 0)), punta + V((0, 0.1, 0)), 0.18, osc, n=12)
    # tambor con cable enrollado y manivela
    td = V((-0.3, 0.45, 2.0))
    giro.cil(td + V((0, 0, 0)), td + V((0, 0.4, 0)), 0.22, osc, n=12)
    for k in range(6):
        giro.toro(td + V((0, 0.05 + k * 0.06, 0)), 0.24, 0.03, cable, n=12, m=4, rot=(90, 0, 0))
    giro.cil(td + V((0, 0.4, 0)), td + V((0, 0.55, 0)), 0.03, acero, n=6)
    giro.cil(td + V((0, 0.55, 0)), td + V((0.3, 0.55, 0.2)), 0.025, acero, n=6)
    giro.cil(td + V((0.3, 0.55, 0.2)), td + V((0.3, 0.7, 0.2)), 0.035, negro, n=6)
    # cable del tambor a la polea
    giro.tubo([td + V((0.2, 0.25, 0.1)), V((0.25, 0, 3.7)), codo + V((0.1, 0, -0.05)), punta + V((0, 0, 0.18))], 0.02,
              cable, n=4, suave=False)
    # panel de control con dos palancas
    pc = V((0.6, -0.55, 1.7))
    giro.caja(pc, (0.5, 0.25, 0.6), osc, 0.04)
    giro.caja(pc + V((0, -0.13, 0.05)), (0.42, 0.02, 0.4), m.mat("plastico", "#3A4048"), 0.0)
    for k, col in enumerate((rojo, negro)):
        b = pc + V((-0.1 + k * 0.2, -0.14, 0.1))
        giro.cil(b, b + V((0, -0.05, 0.3)), 0.02, acero, n=5)
        giro.esfera(b + V((0, -0.05, 0.32)), 0.05, col, seg=8, anillos=4)
        giro.caja(b + V((0, 0, -0.1)), (0.06, 0.03, 0.2), negro, 0.0)
    # gancho con seguro (pieza aparte)
    gx = 1.95
    gancho.cil((gx, 0, 7.5), (gx, 0, 5.1), 0.02, cable, n=4)
    gancho.caja((gx, 0, 4.95), (0.25, 0.18, 0.35), osc, 0.04)  # motón
    gancho.cil((gx, -0.1, 4.9), (gx, 0.1, 4.9), 0.08, acero, n=8)
    gancho.cil((gx, 0, 4.76), (gx, 0, 4.6), 0.04, acero, n=6)
    gancho.tubo([(gx, 0, 4.6), (gx, 0, 4.3), (gx + 0.05, 0, 4.1), (gx + 0.25, 0, 4.05), (gx + 0.38, 0, 4.18),
                 (gx + 0.35, 0, 4.35)], 0.06, acero, n=8, seg=3, r_fin=0.03)
    gancho.cil((gx + 0.02, 0, 4.5), (gx + 0.34, 0, 4.34), 0.015, acero, n=4)  # pestillo de seguridad
    m.terminar()


MODELOS = {
    "forja_principal": forja_principal,
    "yunque_forja": yunque_forja,
    "horno_forja": horno_forja,
    "mesa_crafting": mesa_crafting,
    "entrada_mina": entrada_mina,
    "vagoneta_mina": vagoneta_mina,
    "rail_mina": rail_mina,
    "viga_mina": viga_mina,
    "grua_carga": grua_carga,
}
