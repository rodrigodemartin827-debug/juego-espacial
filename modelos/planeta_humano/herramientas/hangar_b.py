"""Zona del hangar (2): montacargas hover y torre de control."""

import math

import arq
from ph import NEON, V, Modelo

ZONA = "hangar"
NARANJA_BALIZA = "#FF8C1A"
ROJO_POSICION = "#FF2A2A"


# ==============================================================================================================
def montacargas():
    m = Modelo("montacargas", ZONA, (3, 2, 3), 6000,
               "Carretilla elevadora hover: horquilla de dos brazos en un mástil con cilindro hidráulico, 4 discos de "
               "levitación, volante y asiento, contrapeso trasero, panel con medidor de carga y baliza naranja.")
    c = m.parte()
    horq = m.parte("horquilla", pivote=(0, -1.05, 0.35), nota="Carro y horquilla: suben por el mástil hasta 2 studs "
                                                              "(mover en Y de Roblox).")
    disc = m.parte("discos_neon", tipo="neon", color=NEON, transparencia=0.3)
    baliza = m.parte("baliza_neon", tipo="neon", color=NARANJA_BALIZA, nota="Baliza giratoria: Neon naranja; se puede "
                                                                            "girar sobre su eje vertical.")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    cr = m.parte("cristal", tipo="cristal", color="#D9F1F6", transparencia=0.4)
    amar = m.mat("pintura", "#E3A21E", desgaste=0.65, abolladuras=0.3)
    osc = m.mat("metal", "#2B2F34", rug=0.5)
    acero = m.mat("metal", "#848A91")
    cromo = m.mat("cromo", "#D2D6DA")
    contrapeso = m.mat("pintura", "#2E3238", desgaste=0.5, abolladuras=0.5)
    goma = m.mat("goma", "#151618")
    asiento = m.mat("cuero", "#26282C")
    blanco = m.mat("plastico", "#F0EEE6")
    rojo = m.mat("pintura", "#C0201C", desgaste=0.0)
    tinta = m.mat("pintura", "#16181A", desgaste=0.0)
    cadena = m.mat("metal", "#5A5E63", rug=0.5, bump=0.7, patron="tejido")
    Z = 0.45  # bajo del chasis (flota)

    m.seccion("chasis y discos")
    c.caja((0, 0.05, Z + 0.32), (1.7, 2.0, 0.64), amar, 0.12)
    c.caja((0, 0.05, Z + 0.06), (1.76, 2.06, 0.12), osc, 0.04)  # faldón
    for s in (-1, 1):
        c.caja((s * 0.88, 0.05, Z + 0.4), (0.04, 1.6, 0.12), osc, 0.0)  # franja lateral
        for k in range(6):
            c.caja((s * 0.9, -0.55 + k * 0.22, Z + 0.32), (0.02, 0.1, 0.03), tinta, 0.0, rot=(0, 0, 45))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = V((sx * 0.58, 0.05 + sy * 0.7, Z))
            c.cil(p, p - V((0, 0, 0.1)), 0.34, osc, n=16)
            c.toro(p - V((0, 0, 0.1)), 0.34, 0.035, acero, n=16, m=4)
            disc.cil(p - V((0, 0, 0.1)), p - V((0, 0, 0.14)), 0.26, None, n=16)
    m.seccion("contrapeso")
    c.loft([[(x, y, Z + 0.62) for x, y in ((-0.8, 0.55), (0.8, 0.55), (0.8, 1.08), (-0.8, 1.08))],
            [(x, y, Z + 1.45) for x, y in ((-0.72, 0.6), (0.72, 0.6), (0.72, 1.0), (-0.72, 1.0))]], contrapeso)
    for k in range(4):
        c.caja((0, 1.06, Z + 0.75 + k * 0.17), (1.5, 0.06, 0.06), osc, 0.0)
    for s in (-1, 1):
        luces.caja((s * 0.6, 1.1, Z + 1.3), (0.2, 0.02, 0.08), None)  # pilotos
    m.seccion("asiento, volante y panel")
    c.caja((0, 0.3, Z + 0.78), (0.7, 0.62, 0.18), asiento, 0.06)
    c.caja((0, 0.58, Z + 1.15), (0.66, 0.14, 0.62), asiento, 0.06, rot=(-10, 0, 0))
    c.caja((0, 0.3, Z + 0.68), (0.5, 0.5, 0.06), osc, 0.0)
    # columna de dirección, volante y panel de instrumentos con medidor de carga
    c.caja((0, -0.55, Z + 0.85), (1.0, 0.4, 0.42), osc, 0.06)
    c.cil((0, -0.42, Z + 1.02), (0, -0.25, Z + 1.45), 0.04, acero, n=6)
    with c.en((0, -0.25, Z + 1.47), (-35, 0, 0)):
        c.toro((0, 0, 0), 0.2, 0.03, goma, n=14, m=4)
        for k in range(3):
            a = k * math.tau / 3 + 0.5
            c.cil((0, 0, 0), (math.cos(a) * 0.19, math.sin(a) * 0.19, 0), 0.015, osc, n=4)
        c.cil((0, 0, -0.02), (0, 0, 0.02), 0.05, osc, n=8)
        c.cil((0.14, 0.1, 0), (0.14, 0.1, 0.08), 0.02, rojo, n=6)  # pomo
    with c.en((0.28, -0.73, Z + 1.0), (-20, 0, 0)):
        c.cil((0, 0, 0), (0, -0.04, 0), 0.11, acero, n=14)
        c.cil((0, -0.04, 0), (0, -0.045, 0), 0.095, blanco, n=14)
        for k in range(6):
            a = math.radians(-120 + k * 48)
            c.caja((math.cos(a) * 0.075, -0.048, math.sin(a) * 0.075), (0.008, 0.004, 0.02), tinta, 0.0,
                   rot=(0, -math.degrees(a) + 90, 0))
        c.caja((0.01, -0.05, 0.03), (0.006, 0.004, 0.075), rojo, 0.0, rot=(0, 30, 0))
    luces.caja((-0.25, -0.76, Z + 1.0), (0.3, 0.02, 0.14), None)  # pantallita
    for k, col in enumerate((m.mat("plastico", "#2EA04E"), rojo)):
        c.cil((-0.05 + k * 0.1, -0.76, Z + 0.88), (-0.05 + k * 0.1, -0.79, Z + 0.88), 0.03, col, n=8)
    m.seccion("protector y baliza")
    for sx in (-1, 1):
        for y in (-0.62, 0.62):
            c.cil((sx * 0.68, y, Z + 0.62), (sx * 0.62, y, Z + 2.2), 0.045, osc, n=6)
    for sx in (-1, 1):
        c.cil((sx * 0.62, -0.62, Z + 2.2), (sx * 0.62, 0.62, Z + 2.2), 0.045, osc, n=6)
    for y in (-0.62, 0.62):
        c.cil((-0.62, y, Z + 2.2), (0.62, y, Z + 2.2), 0.045, osc, n=6)
    for k in range(4):
        c.cil((-0.6, -0.42 + k * 0.28, Z + 2.22), (0.6, -0.42 + k * 0.28, Z + 2.22), 0.025, osc, n=4)
    c.cil((0, 0.3, Z + 2.25), (0, 0.3, Z + 2.33), 0.1, osc, n=10)
    baliza.esfera((0, 0.3, Z + 2.38), 0.09, None, seg=10, anillos=6, esc=(1, 1, 1.2))
    cr.esfera((0, 0.3, Z + 2.38), 0.12, None, seg=10, anillos=6, esc=(1, 1, 1.25))
    m.seccion("mástil, cilindro y horquilla")
    for s in (-1, 1):
        arq.viga_h(c, (s * 0.45, -0.98, Z - 0.05), (s * 0.45, -0.98, 2.75), 0.22, 0.18, osc)
    c.cil((-0.45, -0.98, 2.75), (0.45, -0.98, 2.75), 0.05, osc, n=6)
    c.cil((0, -0.92, Z), (0, -0.92, 1.9), 0.09, osc, n=10)  # cilindro hidráulico
    c.cil((0, -0.92, 1.9), (0, -0.92, 2.55), 0.045, cromo, n=10)
    c.cil((-0.12, -0.92, 2.58), (0.12, -0.92, 2.58), 0.07, acero, n=10)  # polea de cadena
    for s in (-1, 1):
        for k in range(10):
            z = 0.9 + k * 0.17
            c.toro((s * 0.12, -0.88, z), 0.04, 0.012, cadena, n=6, m=3, rot=(0, 90 * (k % 2), 0))
    # carro con respaldo de rejilla y dos brazos en L
    horq.caja((0, -1.1, 0.75), (1.1, 0.08, 0.5), amar, 0.03)
    for k in range(5):
        horq.cil((-0.5 + k * 0.25, -1.12, 1.0), (-0.5 + k * 0.25, -1.12, 1.65), 0.025, osc, n=5)
    horq.cil((-0.55, -1.12, 1.65), (0.55, -1.12, 1.65), 0.03, osc, n=5)
    for s in (-1, 1):
        x = s * 0.32
        horq.caja((x, -1.17, 0.55), (0.14, 0.06, 0.6), acero, 0.01)
        horq.caja((x, -1.68, 0.29), (0.14, 1.05, 0.06), acero, 0.01)
        horq.caja((x, -2.2, 0.28), (0.14, 0.06, 0.04), acero, 0.0, rot=(30, 0, 0))  # punta biselada
    m.terminar()


# ==============================================================================================================
def torre_control():
    m = Modelo("torre_control", ZONA, (4, 4, 14), 14000,
               "Torre de control: fuste cilíndrico con puerta y una tronera alta por la que se ve la escalera de "
               "caracol, cabina octogonal con 8 paneles de cristal y consola con pantallas, antena con luz roja, "
               "parabólica lateral y bandera de la colonia.")
    c = m.parte()
    puerta = m.parte("puerta", pivote=(-0.45, -1.32, 0.35), nota="Puerta de la base: gira sobre su bisagra.")
    cr = m.parte("cristal", tipo="cristal", color="#9EC6D6", transparencia=0.35)
    pant = m.parte("pantallas_neon", tipo="neon", color=NEON)
    roja = m.parte("luz_posicion_neon", tipo="neon", color=ROJO_POSICION, nota="Luz de posición: Neon rojo.")
    bandera = m.parte("bandera", pivote=(1.85, -0.9, 6.9), nota="Bandera de la colonia: tela aparte (se puede agitar).")
    blanco = m.mat("paneles", "#DADDDF", tam_panel=(1.2, 1.5), desgaste=0.35, c_desgaste="#8A9097", lluvia=0.5)
    gris = m.mat("pintura", "#4A525C", desgaste=0.45)
    osc = m.mat("metal", "#2B2F34", rug=0.5)
    acero = m.mat("metal", "#848A91")
    horm = m.mat("hormigon", "#8E8A84")
    naranja = m.mat("pintura", "#E07A1F", desgaste=0.5)
    madera = m.mat("pintura", "#5A626C", desgaste=0.3)
    azul = m.mat("tela", "#1D3E7A", suciedad=0.1)
    blanco_t = m.mat("tela", "#F0EEE6", suciedad=0.1)
    cyan_t = m.mat("tela", "#3DC8D8", suciedad=0.1)
    R = 1.35  # radio exterior del fuste
    ZF = 10.4  # arranque de la cabina

    m.seccion("base y fuste")
    c.cil((0, 0, 0), (0, 0, 0.35), 1.75, horm, n=16, b=0.05)
    # fuste: tubo de pared gruesa abierto en una tronera vertical (lámina con grosor de 0,14)
    ab0, ab1 = math.radians(-90 + 9), math.radians(270 - 9)  # hueco de la tronera mirando a -Y... desplazado
    gap = math.radians(9)
    a_tr = math.radians(-50)  # la tronera mira de 3/4 al frente
    c.lamina(lambda u, v: (math.cos(a_tr + gap + u * (math.tau - 2 * gap)) * (R - 0.07),
                           math.sin(a_tr + gap + u * (math.tau - 2 * gap)) * (R - 0.07), 0.35 + v * (ZF - 0.35)),
             30, 1, 0.14, blanco)
    for z in (2.5, 5.0, 7.5, ZF - 0.15):
        c.toro((0, 0, z), R + 0.02, 0.05, gris, n=24, m=4)
    # marco y cristal de la tronera
    for s in (-1, 1):
        a = a_tr + s * gap
        c.caja((math.cos(a) * R, math.sin(a) * R, (2.0 + 9.0) / 2), (0.12, 0.12, 7.0), gris, 0.02,
               rot=(0, 0, math.degrees(a)))
    cr.caja((math.cos(a_tr) * (R - 0.07), math.sin(a_tr) * (R - 0.07), 5.5), (0.06, 0.36, 7.0), None,
            rot=(0, 0, math.degrees(a_tr)))
    # la tronera no llega abajo ni arriba: tapas de pared por debajo y por encima
    for (z0, z1) in ((0.35, 2.0), (9.0, ZF)):
        c.caja((math.cos(a_tr) * (R - 0.07), math.sin(a_tr) * (R - 0.07), (z0 + z1) / 2), (0.14, 0.5, z1 - z0), blanco,
               rot=(0, 0, math.degrees(a_tr)))
    m.seccion("escalera de caracol interior")
    c.cil((0, 0, 0.35), (0, 0, ZF), 0.16, acero, n=10)
    for k in range(34):
        a = a_tr - 1.2 + k * 0.5
        z = 0.6 + k * (ZF - 0.9) / 34
        c.caja((math.cos(a) * 0.65, math.sin(a) * 0.65, z), (0.95, 0.32, 0.06), m.mat("grip", "#6E747A"), 0.0,
               rot=(0, 0, math.degrees(a)))
        if k % 3 == 0:
            c.cil((math.cos(a) * 1.1, math.sin(a) * 1.1, z), (math.cos(a) * 1.1, math.sin(a) * 1.1, z + 0.9), 0.02,
                  naranja, n=4)
    luces_int = [(0, 0, z) for z in (3.0, 6.0, 9.0)]
    for p in luces_int:
        pant.cil(V(p) + V((0.5, 0.5, 0)), V(p) + V((0.5, 0.5, 0.1)), 0.06, None, n=6)
    m.seccion("puerta")
    a = -math.pi / 2
    c.caja((0, -R - 0.02, 1.45), (1.3, 0.16, 2.3), gris, 0.03)  # marco (la pared queda detrás)
    puerta.caja((0, -R - 0.12, 1.42), (0.9, 0.08, 2.05), m.mat("pintura", "#C24A26", desgaste=0.5), 0.02)
    puerta.caja((0, -R - 0.17, 1.95), (0.5, 0.02, 0.35), osc, 0.0)
    cr.caja((0, -R - 0.165, 1.95), (0.44, 0.01, 0.3), None)
    puerta.cil((0.3, -R - 0.17, 1.35), (0.3, -R - 0.26, 1.35), 0.025, acero, n=6)
    puerta.cil((0.3, -R - 0.26, 1.35), (0.12, -R - 0.26, 1.35), 0.025, acero, n=6)
    for zz in (0.75, 2.15):
        puerta.cil((-0.45, -R - 0.12, zz - 0.12), (-0.45, -R - 0.12, zz + 0.12), 0.04, acero, n=6)
    for k in range(2):
        c.caja((0, -R - 0.35 - k * 0.3, 0.35 - k * 0.12 - 0.06), (1.3, 0.3, 0.12), horm, 0.02)
    pant.caja((0, -R - 0.12, 2.65), (0.5, 0.06, 0.08), None)  # luz sobre la puerta

    m.seccion("cabina")
    # forjado, antepecho macizo, 8 montantes inclinados y 8 cristales, techo con voladizo
    c.cil((0, 0, ZF - 0.1), (0, 0, ZF + 0.15), 1.95, gris, n=16)
    c.torno([(1.6, ZF + 0.15), (1.95, ZF + 0.15), (1.95, ZF + 0.8), (1.6, ZF + 0.8)], blanco, n=16)
    zv0, zv1 = ZF + 0.8, ZF + 2.4
    for k in range(8):
        a = k * math.tau / 8 + math.pi / 8
        a2 = (k + 1) * math.tau / 8 + math.pi / 8
        p0 = V((math.cos(a) * 1.9, math.sin(a) * 1.9, zv0))
        p1 = V((math.cos(a) * 1.98, math.sin(a) * 1.98, zv1))
        c.cil(p0, p1, 0.06, osc, n=6)
        q = [V((math.cos(a) * 1.88, math.sin(a) * 1.88, zv0)), V((math.cos(a2) * 1.88, math.sin(a2) * 1.88, zv0)),
             V((math.cos(a2) * 1.96, math.sin(a2) * 1.96, zv1)), V((math.cos(a) * 1.96, math.sin(a) * 1.96, zv1))]
        nrm = (q[1] - q[0]).cross(q[3] - q[0]).normalized()
        cr.loft([q, [p - nrm * 0.05 for p in q]], None)
    c.torno([(0.0, zv1), (2.15, zv1), (2.15, zv1 + 0.25), (1.7, zv1 + 0.4), (0.0, zv1 + 0.42)], gris, n=16)
    # consola interior en arco con pantallas, y dos sillas
    for k in range(5):
        a = -math.pi / 2 - 0.9 + k * 0.45
        p = V((math.cos(a) * 1.35, math.sin(a) * 1.35, ZF + 0.15))
        c.caja(p + V((0, 0, 0.45)), (0.55, 0.5, 0.9), gris, 0.03, rot=(0, 0, math.degrees(a) + 90))
        pant.caja(p + V((math.cos(a) * -0.05, math.sin(a) * -0.05, 1.1)), (0.45, 0.04, 0.3), None,
                  rot=(-15, 0, math.degrees(a) + 90))
    for k in range(2):
        a = -math.pi / 2 - 0.45 + k * 0.9
        p = V((math.cos(a) * 0.7, math.sin(a) * 0.7, ZF + 0.15))
        c.cil(p, p + V((0, 0, 0.45)), 0.04, acero, n=6)
        c.caja(p + V((0, 0, 0.5)), (0.4, 0.4, 0.08), osc, 0.02)
        c.caja(p + V((math.cos(a) * -0.18, math.sin(a) * -0.18, 0.8)), (0.38, 0.06, 0.5), osc, 0.02,
               rot=(0, 0, math.degrees(a) + 90))

    m.seccion("antena, parabólica y bandera")
    zt = zv1 + 0.42
    c.cil((0.6, 0.4, zt), (0.6, 0.4, 13.6), 0.06, acero, n=6)
    for z, L in ((12.2, 0.7), (12.8, 0.5), (13.3, 0.35)):
        c.cil((0.6 - L / 2, 0.4, z), (0.6 + L / 2, 0.4, z), 0.025, acero, n=4)
    c.cil((0.6, 0.4, 13.6), (0.6, 0.4, 13.72), 0.07, osc, n=8)
    roja.esfera((0.6, 0.4, 13.82), 0.09, None, seg=10, anillos=6)
    c.caja((-0.8, 0.6, zt + 0.2), (0.6, 0.6, 0.4), acero, 0.04)  # caja de equipos
    # parabólica lateral sobre ménsula del fuste
    with c.en((-1.5, 0.6, 8.2), (0, -30, 150)):
        c.torno([(0.0, 0.0), (0.45, 0.08), (0.7, 0.22), (0.72, 0.26), (0.68, 0.26), (0.43, 0.13), (0.0, 0.05)],
                m.mat("pintura", "#E6E8EA", desgaste=0.3), n=16)
        for k in range(3):
            a = k * math.tau / 3
            c.cil((math.cos(a) * 0.6, math.sin(a) * 0.6, 0.22), (0, 0, 0.75), 0.015, acero, n=4)
        c.cil((0, 0, 0.7), (0, 0, 0.85), 0.06, osc, n=8)
        c.cil((0, 0, 0.0), (0, 0, -0.35), 0.06, acero, n=6)
    c.cil((-1.25, 0.45, 8.0), (-1.5, 0.6, 7.85), 0.05, acero, n=6)
    # mástil de la bandera junto a la base y bandera ondeando (tela con grosor)
    mx, my = 1.85, -0.9
    c.cil((mx, my, 0.35), (mx, my, 7.6), 0.05, acero, n=8)
    c.esfera((mx, my, 7.65), 0.08, m.mat("metal", "#C99A3C", rug=0.25), seg=8, anillos=5)
    c.cil((mx, my, 0.35), (mx, my, 0.5), 0.15, osc, n=8)
    bandera.lamina(lambda u, v: (mx - 0.05 - u * 1.4, my + 0.12 * math.sin(u * 5.0 + 0.5) * u,
                                 6.2 + v * 0.9 - 0.08 * u), 10, 2, 0.03, azul)
    with bandera.en((mx - 0.7, my + 0.12 * math.sin(0.5 * 5.0 + 0.5) * 0.5 - 0.0, 6.65 - 0.04), (90, 0, 0)):
        bandera.toro((0, 0, 0), 0.22, 0.025, cyan_t, n=14, m=3)
        bandera.extruir([(math.cos(a) * r, math.sin(a) * r) for k in range(10)
                         for a, r in [(math.pi / 2 + k * math.pi / 5, 0.14 if k % 2 == 0 else 0.06)]], 0.08, blanco_t)
    m.terminar()


MODELOS = {
    "montacargas": montacargas,
    "torre_control": torre_control,
}
