"""Zona comercial (2): armaduras, suministros (pociones), ferretería y astillero de piezas de nave."""

import math

import arq
from ph import NEON, V, Modelo

ZONA = "comercial"


def _tejado_chapa(c, x0, x1, y0, y1, z_bajo, z_alto, mat, mat_junta, paso=0.6, voladizo=0.4):
    """Tejado a un agua de chapa con juntas alzadas (sube de y0 a y1)."""
    ang = math.atan2(z_alto - z_bajo, y1 - y0)
    L = math.hypot(z_alto - z_bajo, y1 - y0) + 2 * voladizo
    cy, cz = (y0 + y1) / 2, (z_bajo + z_alto) / 2
    with c.en((0, cy, cz), (math.degrees(ang), 0, 0)):
        c.caja((0.5 * (x0 + x1), 0, 0.06), (x1 - x0 + 2 * voladizo, L, 0.12), mat, 0.03)
        n = int((x1 - x0 + 2 * voladizo) / paso)
        for i in range(n + 1):
            x = x0 - voladizo + i * (x1 - x0 + 2 * voladizo) / n
            c.caja((x, 0, 0.16), (0.06, L, 0.1), mat_junta, 0.012)
    return ang


# ==============================================================================================================
def tienda_armaduras():
    m = Modelo("tienda_armaduras", ZONA, (12, 10, 8), 14000,
               "Armaduras: zócalo de ladrillo, paneles verde grisáceo, escaparate con dos maniquíes robóticos (pechera "
               "y hombreras), estante exterior con tres cascos y puerta batiente con sensor de proximidad.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#A8CEDA", transparencia=0.35)
    neon = m.parte("cartel_neon", tipo="neon", color=NEON)
    luces = m.parte("luces_neon", tipo="neon", color=NEON)

    panel = m.mat("paneles", "#5E6E66", tam_panel=(1.5, 2.2), desgaste=0.5)
    ladr = m.mat("ladrillo", "#8A4B36", c2="#77706A")
    horm = m.mat("hormigon", "#A39E94")
    acero = m.mat("metal", "#80868D")
    osc = m.mat("metal", "#363B42", rug=0.5)
    cromo = m.mat("cromo", "#C8CDD3")
    madera = m.mat("madera", "#7A5434", eje="X")
    madera_z = m.mat("madera", "#6A4528", eje="Z")
    chapa = m.mat("pintura", "#7C3A2C", desgaste=0.6)
    blanco = m.mat("plastico", "#DADDE0")
    gris = m.mat("pintura", "#4C545D", desgaste=0.35)
    armad = m.mat("pintura", "#3A6EA5", desgaste=0.65, c_desgaste="#B8BEC6")
    laton = m.mat("metal", "#B48C42", rug=0.32)
    goma = m.mat("goma", "#1D1E21")
    cuero = m.mat("cuero", "#5A3520")

    X0, X1, YF, YB, Z0, ZT, G = -6.0, 6.0, -4.0, 4.6, 0.4, 6.6, 0.4

    m.seccion("base y muros")
    c.caja_de((X0 - 0.1, YF - 0.1, 0), (X1 + 0.1, YB + 0.1, Z0), horm, 0.04)
    ESC = (-5.3, 0.6, 1.5, 5.6)
    PUE = (1.8, 4.6, Z0, 6.0)
    # zócalo de ladrillo con albardilla de piedra, muro de paneles encima
    arq.muro_huecos(c, X0, X1, Z0, 1.4, YF, YF + G, [(ESC[0], ESC[1], 1.4, 1.5), (PUE[0], PUE[1], Z0, 1.4)], ladr)
    c.caja_de((X0, YF - 0.06, 1.4), (ESC[0], YF + G, 1.52), horm, 0.03)
    c.caja_de((ESC[1], YF - 0.06, 1.4), (PUE[0], YF + G, 1.52), horm, 0.03)
    c.caja_de((PUE[1], YF - 0.06, 1.4), (X1, YF + G, 1.52), horm, 0.03)
    arq.muro_huecos(c, X0, X1, 1.52, ZT, YF, YF + G, [(ESC[0], ESC[1], 1.52, ESC[3]), (PUE[0], PUE[1], 1.52, PUE[3])],
                    panel)
    for x in (X0, X1 - G):
        c.caja_de((x, YF + G, Z0), (x + G, YB - G, 1.4), ladr)
        c.caja_de((x, YF + G, 1.4), (x + G, YB - G, ZT + 0.6), panel)
    c.caja_de((X0, YB - G, Z0), (X1, YB, 1.4), ladr)
    c.caja_de((X0, YB - G, 1.4), (X1, YB, ZT + 1.1), panel)
    # piñones laterales hasta el faldón del tejado
    for x in (X0, X1 - G):
        c.extruir([(YF + G, ZT), (YB - G, ZT), (YB - G, ZT + 1.1), (YF + G, ZT + 0.05)], G, panel,
                  c=(x + G / 2, 0, 0), rot=(90, 0, 90))
    # pilastras de acero
    for x in (X0 + 0.05, X1 - 0.05, ESC[1] + 0.6):
        c.caja((x, YF - 0.1, (Z0 + ZT) / 2), (0.3, 0.25, ZT - Z0), osc, 0.04)
        for zz in (1.0, 3.0, 5.0):
            c.perno((x, YF - 0.23, zz), (0, -1, 0), acero, r=0.04)

    m.seccion("tejado")
    _tejado_chapa(c, X0, X1, YF - 0.2, YB + 0.1, ZT + 0.05, ZT + 1.2, chapa, chapa, paso=0.75, voladizo=0.35)
    # canalón delantero con soportes
    c.caja_de((X0 - 0.4, YF - 0.75, ZT - 0.18), (X1 + 0.4, YF - 0.45, ZT - 0.02), acero, 0.03)
    for i in range(6):
        x = X0 + i * (X1 - X0) / 5
        c.caja((x, YF - 0.45, ZT - 0.1), (0.05, 0.5, 0.05), osc)
    arq.bajante(c, X0 + 0.5, YF - 0.3, ZT - 0.1, acero, osc, r=0.09)

    m.seccion("escaparate")
    x0, x1, z0, z1 = ESC
    arq.marco(c, x0, x1, z0, z1, YF, 0.16, 0.15, osc)
    c.caja_de(((x0 + x1) / 2 - 0.05, YF - 0.04, z0), ((x0 + x1) / 2 + 0.05, YF + 0.1, z1), osc, 0.01)
    cr.caja_de((x0 + 0.02, YF + 0.05, z0 + 0.02), (x1 - 0.02, YF + 0.18, z1 - 0.02), None)
    YN = YF + G
    c.caja_de((x0 - 0.1, YN, z0 - 0.5), (x1 + 0.1, YN + 2.4, z0), madera, 0.02)
    c.caja_de((x0 - 0.2, YN + 2.4, z0 - 0.5), (x1 + 0.2, YN + 2.6, z1 + 0.2), m.mat("madera", "#B08A60", eje="Z",
                                                                                   suciedad=0.2))
    for x in (x0 - 0.2, x1):
        c.caja_de((x, YN, z0), (x + 0.2, YN + 2.4, z1 + 0.2), gris)
    c.caja_de((x0 - 0.2, YN, z1), (x1 + 0.2, YN + 2.4, z1 + 0.2), gris)
    luces.cil((x0 + 0.2, YN + 0.4, z1 - 0.08), (x1 - 0.2, YN + 0.4, z1 - 0.08), 0.04, None, n=8)

    def maniqui(cx, cy, pieza):
        """Busto robótico: peana, mástil, torso, cuello articulado, cabeza con visor y hombros de rótula."""
        c.torno([(0.0, 0), (0.5, 0), (0.5, 0.06), (0.42, 0.12), (0.0, 0.12)], osc, n=14, c=(cx, cy, z0))
        c.cil((cx, cy, z0 + 0.12), (cx, cy, z0 + 1.0), 0.06, cromo, n=8)
        c.cil((cx, cy, z0 + 0.6), (cx, cy, z0 + 0.66), 0.1, osc, n=8)  # abrazadera de altura
        c.cil((cx + 0.1, cy, z0 + 0.63), (cx + 0.22, cy, z0 + 0.63), 0.025, cromo, n=6)
        zt = z0 + 1.0
        # torso (secciones elípticas)
        c.torno([(0.0, 0.0), (0.38, 0.0), (0.46, 0.25), (0.56, 0.75), (0.62, 1.1), (0.55, 1.3), (0.25, 1.42),
                 (0.0, 1.42)], blanco, n=14, c=(cx, cy, zt))
        # junta de cintura (anillos)
        c.cil((cx, cy, zt - 0.04), (cx, cy, zt + 0.06), 0.4, osc, n=14)
        # placa del pecho con ranuras (articulación tipo robot)
        for k in range(3):
            c.caja((cx, cy - 0.4 - 0.02 * k, zt + 0.35 + k * 0.12), (0.5 - k * 0.05, 0.04, 0.05), osc, 0.01)
        # hombros: rótulas
        for s in (-1, 1):
            c.esfera((cx + s * 0.66, cy, zt + 1.18), 0.17, osc, seg=10, anillos=6)
            c.cil((cx + s * 0.62, cy, zt + 1.18), (cx + s * 0.8, cy, zt + 1.12), 0.12, blanco, n=10)
            c.cil((cx + s * 0.8, cy, zt + 1.12), (cx + s * 0.86, cy, zt + 1.1), 0.13, osc, n=10)
        # cuello con anillos y cabeza
        c.cil((cx, cy, zt + 1.4), (cx, cy, zt + 1.62), 0.11, osc, n=10)
        for k in range(3):
            zz = zt + 1.44 + k * 0.06
            c.cil((cx, cy, zz), (cx, cy, zz + 0.025), 0.135, cromo, n=10)
        c.esfera((cx, cy, zt + 1.9), 0.3, blanco, seg=14, anillos=8, esc=(0.85, 0.95, 1.1))
        c.caja((cx, cy - 0.25, zt + 1.94), (0.42, 0.12, 0.1), osc, 0.04)  # visor
        luces.caja((cx, cy - 0.31, zt + 1.94), (0.34, 0.02, 0.035), None)
        for s in (-1, 1):
            c.cil((cx + s * 0.26, cy, zt + 1.9), (cx + s * 0.31, cy, zt + 1.9), 0.08, osc, n=10)
        if pieza == "pechera":
            c.torno([(0.0, 0.3), (0.5, 0.3), (0.6, 0.6), (0.68, 1.0), (0.72, 1.18), (0.6, 1.32), (0.32, 1.4),
                     (0.3, 1.32), (0.55, 1.22), (0.62, 1.0), (0.54, 0.62), (0.44, 0.34), (0.0, 0.34)], armad, n=16,
                    c=(cx, cy, zt))
            # nervio central y cinchas laterales con hebilla
            c.caja((cx, cy - 0.66, zt + 0.95), (0.08, 0.1, 0.7), armad, 0.03, rot=(-8, 0, 0))
            for s in (-1, 1):
                c.caja((cx + s * 0.62, cy, zt + 0.75), (0.06, 0.6, 0.12), cuero, 0.02)
                c.caja((cx + s * 0.66, cy - 0.25, zt + 0.75), (0.05, 0.1, 0.14), laton, 0.01)
            for s in (-1, 1):
                for zz in (0.55, 1.1):
                    c.remache((cx + s * 0.35, cy - 0.6 - (0.04 if zz > 1 else 0.0), zt + zz), (0, -1, 0), laton, 0.035)
        else:
            for s in (-1, 1):
                # hombrera de tres láminas superpuestas
                for k in range(3):
                    r = 0.42 - k * 0.04
                    with c.en((cx + s * (0.72 + k * 0.05), cy, zt + 1.25 - k * 0.17), (0, s * (25 + k * 12), 0)):
                        c.torno([(0.0, r * 0.45), (r * 0.6, r * 0.35), (r, 0.0), (r * 0.9, -0.04), (r * 0.55, 0.28),
                                 (0.0, r * 0.38)], armad, n=14)
                c.remache((cx + s * 0.78, cy - 0.32, zt + 1.36), (0, -1, 0.3), laton, 0.035)
                c.caja((cx + s * 0.5, cy, zt + 1.15), (0.25, 0.08, 0.06), cuero, 0.01, rot=(0, s * 35, 0))

    maniqui(x0 + 1.4, YN + 1.2, "pechera")
    maniqui(x1 - 1.5, YN + 1.2, "hombreras")

    m.seccion("puerta y sensor")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.2, 0.2, osc, abajo=False)
    W = px1 - px0 - 0.08
    piv = (px0 + 0.04, YF + 0.1, pz0)
    for lado, (hx0, sx) in {"izq": (px0 + 0.04, 1), "der": (px1 - 0.04, -1)}.items():
        w = W / 2
        pv = (hx0, YF + 0.1, pz0)
        h = m.parte(f"puerta_{lado}", pivote=pv, nota="Hoja batiente: gira sobre su bisagra (eje vertical del pivote). "
                                                  "Abre hacia dentro hasta 95°.")
        hc = m.parte(f"puerta_{lado}_cristal", tipo="cristal", color="#A8CEDA", pivote=pv, transparencia=0.4)
        xa, xb = sorted((hx0, hx0 + sx * w))
        y0, y1 = YF + 0.04, YF + 0.16
        h.caja_de((xa, y0, pz0 + 0.03), (xb, y1, pz0 + 1.6), madera_z, 0.03)  # panel bajo de madera
        h.caja_de((xa + 0.15, y0 - 0.02, pz0 + 0.3), (xb - 0.15, y0, pz0 + 1.4), madera_z, 0.02)  # cuarterón
        h.caja_de((xa, y0, pz1 - 0.35), (xb, y1, pz1 - 0.05), madera_z, 0.03)
        h.caja_de((xa, y0, pz0 + 1.6), (xa + 0.15, y1, pz1 - 0.35), madera_z, 0.02)
        h.caja_de((xb - 0.15, y0, pz0 + 1.6), (xb, y1, pz1 - 0.35), madera_z, 0.02)
        hc.caja_de((xa + 0.15, y0 + 0.03, pz0 + 1.6), (xb - 0.15, y1 - 0.03, pz1 - 0.35), None)
        # bisagras (3) en el canto del pivote, piezas separadas con su pasador
        for zz in (pz0 + 0.6, pz0 + 2.9, pz1 - 0.6):
            h.cil((hx0, YF + 0.1, zz - 0.18), (hx0, YF + 0.1, zz + 0.18), 0.05, laton, n=8)
            h.caja((hx0 + sx * 0.14, y0 - 0.005, zz), (0.24, 0.02, 0.3), laton, 0.005)
            h.cil((hx0, YF + 0.1, zz + 0.18), (hx0, YF + 0.1, zz + 0.22), 0.03, laton, n=6)
        # tirador horizontal
        xt = hx0 + sx * (w - 0.3)
        h.cil((xt - 0.25 * sx, y0 - 0.12, pz0 + 2.8), (xt + 0.05 * sx, y0 - 0.12, pz0 + 2.8), 0.03, cromo, n=8)
        for xx in (xt - 0.25 * sx, xt + 0.05 * sx):
            h.cil((xx, y0 - 0.12, pz0 + 2.8), (xx, y0, pz0 + 2.8), 0.022, cromo, n=6)
        h.caja((xt + 0.1 * sx, y0 - 0.02, pz0 + 2.55), (0.08, 0.04, 0.18), laton, 0.01)  # bocallave
    # sensor de proximidad sobre el marco
    sx_ = (px0 + px1) / 2
    c.caja((sx_, YF - 0.32, pz1 + 0.38), (0.7, 0.22, 0.2), osc, 0.04)
    c.caja((sx_, YF - 0.2, pz1 + 0.27), (0.5, 0.05, 0.05), acero, 0.01)
    luces.caja((sx_ - 0.12, YF - 0.44, pz1 + 0.36), (0.2, 0.02, 0.06), None)
    c.cil((sx_ + 0.2, YF - 0.43, pz1 + 0.36), (sx_ + 0.2, YF - 0.47, pz1 + 0.36), 0.05, goma, n=10)
    c.tubo([(sx_ + 0.35, YF - 0.25, pz1 + 0.38), (sx_ + 0.6, YF - 0.12, pz1 + 0.45), (sx_ + 0.7, YF - 0.04, pz1 + 0.8)],
           0.02, goma, n=5, seg=3)
    # marquesina de chapa sobre la puerta con tirantes
    c.caja(((px0 + px1) / 2, YF - 0.75, pz1 + 0.95), (px1 - px0 + 0.9, 1.5, 0.1), osc, 0.03, rot=(-8, 0, 0))
    for x in (px0 - 0.3, px1 + 0.3):
        c.tubo([(x, YF - 1.42, pz1 + 1.02), (x, YF - 0.02, pz1 + 2.05)], 0.025, acero, n=6, suave=False)
        c.caja((x, YF - 0.03, pz1 + 2.05), (0.12, 0.06, 0.2), acero, 0.01)
    # escalón
    c.caja_de((px0 - 0.3, YF - 0.6, 0), (px1 + 0.3, YF, Z0 - 0.02), horm, 0.04)

    m.seccion("cartel")
    neon.texto("ARMADURAS", None, alto=0.42, grosor=0.06, c=((px0 + px1) / 2, YF - 1.52, pz1 + 0.8),
               fuente="estrecha", rot=(90, 0, 0))
    c.caja(((px0 + px1) / 2, YF - 1.47, pz1 + 0.92), (3.4, 0.06, 0.6), gris, 0.02)

    m.seccion("estante de cascos")
    ex = X1 - 0.75
    for zz in (2.0, 3.2):
        c.caja((ex, YF - 0.35, zz), (1.1, 0.7, 0.08), madera, 0.02)
        for x in (ex - 0.4, ex + 0.4):
            c.extruir([(0, 0), (0.6, 0), (0, -0.5)], 0.06, osc, c=(x, YF - 0.0, zz - 0.04), rot=(90, 0, -90))
    # casco 1: cúpula con visera abatible
    c.esfera((ex, YF - 0.35, 2.04), 0.32, armad, seg=12, anillos=7, esc=(1, 1.1, 1.05))
    c.caja((ex, YF - 0.62, 2.24), (0.5, 0.1, 0.16), osc, 0.04)
    # casco 2: con cresta, apilado encima del primero
    c.esfera((ex - 0.05, YF - 0.33, 2.58), 0.28, gris, seg=12, anillos=7, esc=(1, 1.15, 0.9))
    c.extruir([(-0.3, 0), (0.3, 0), (0.22, 0.18), (-0.25, 0.1)], 0.05, chapa, c=(ex - 0.05, YF - 0.33, 2.72),
              rot=(90, 0, 90))
    # casco 3: casco técnico con ojos cilíndricos en la balda alta
    c.torno([(0.0, 0.0), (0.3, 0.0), (0.33, 0.25), (0.28, 0.48), (0.0, 0.55)], blanco, n=12, c=(ex, YF - 0.35, 3.24))
    for s in (-1, 1):
        c.cil((ex + s * 0.11, YF - 0.6, 3.48), (ex + s * 0.11, YF - 0.72, 3.48), 0.07, osc, n=10)
        luces.cil((ex + s * 0.11, YF - 0.72, 3.48), (ex + s * 0.11, YF - 0.735, 3.48), 0.05, None, n=8)

    m.seccion("detalles")
    arq.foco_pared(c, luces, (x0 - 0.0, YF, 6.15), osc, acero)
    c.caja((X1 - 1.6, YF - 0.12, 4.6), (0.5, 0.24, 0.7), acero, 0.04)
    c.tubo([(X1 - 1.6, YF - 0.1, 4.95), (X1 - 1.6, YF - 0.1, ZT - 0.1)], 0.035, osc, n=6, suave=False)
    # puerta trasera y unidad exterior de aire
    c.caja_de((-1.0, YB, Z0), (0.6, YB + 0.12, 5.4), osc, 0.04)
    c.caja((3.2, YB + 0.45, 1.0), (1.4, 0.8, 1.2), acero, 0.06)
    c.cil((3.2, YB + 0.86, 1.0), (3.2, YB + 0.9, 1.0), 0.45, osc, n=14)
    c.tubo([(2.6, YB + 0.3, 1.5), (2.4, YB + 0.1, 2.2), (2.4, YB + 0.05, 4.0)], 0.04, goma, n=6, seg=3)
    m.terminar()


# ==============================================================================================================
def tienda_pociones():
    m = Modelo("tienda_pociones", ZONA, (10, 8, 7), 12000,
               "Suministros (boticario): entramado de madera sobre piedra, mirador con estantes de frascos 3D, "
               "ventanilla con mostrador y balanza, rejilla de ventilación que echa vapor verde.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#B5DCE6", transparencia=0.4)
    frascos = m.parte("frascos_cristal", tipo="cristal", color="#DDF3F5", transparencia=0.55,
                      nota="Cristal de los frascos: el líquido opaco va dentro, en la malla con textura.")
    neon = m.parte("cartel_neon", tipo="neon", color=NEON)
    vapor = m.parte("vapor_neon", tipo="neon", color="#7CFFA8", transparencia=0.5,
                    nota="Vapor verde tenue: Neon #7CFFA8 con Transparency 0,5. Se puede animar subiendo y "
                         "encogiéndolo, o sustituir por un ParticleEmitter en el anclaje Vapor.")

    piedra = m.mat("piedra", "#8F887C")
    yeso = m.mat("pintura", "#D9D1BE", desgaste=0.4, c_desgaste="#9A8E78", lluvia=0.5)
    viga = m.mat("madera", "#4E3320", eje="Z")
    viga_x = m.mat("madera", "#4E3320", eje="X")
    tabla = m.mat("madera", "#7A5636", eje="X")
    teja = m.mat("pintura", "#2F5A55", desgaste=0.5, c_desgaste="#8C9A96")
    acero = m.mat("metal", "#7F858C")
    osc = m.mat("metal", "#30353B", rug=0.5)
    cobre = m.mat("metal", "#B26A3C", rug=0.35)
    laton = m.mat("metal", "#B9913F", rug=0.3)
    verde = m.mat("liquido", "#3FCB5A")
    azul = m.mat("liquido", "#2E7DE0")
    ambar = m.mat("liquido", "#E59A2A")
    rojo = m.mat("liquido", "#C8324A")
    corcho = m.mat("cuero", "#A57B4E")
    horm = m.mat("hormigon", "#A29C90")

    X0, X1, YF, YB, Z0, ZT, G = -5.0, 5.0, -3.1, 3.6, 0.3, 4.6, 0.35

    m.seccion("muros")
    c.caja_de((X0 - 0.1, YF - 0.1, 0), (X1 + 0.1, YB + 0.1, Z0), horm, 0.04)
    MIR = (-4.3, -0.5, 1.4, 4.0)
    PUE = (0.3, 2.3, Z0, 3.95)
    VEN = (2.9, 4.5, 1.5, 3.2)
    huecos = [(MIR[0], MIR[1], Z0, MIR[3]), (PUE[0], PUE[1], Z0, PUE[3]), VEN]
    # planta baja de piedra (sillarejo) y muro de yeso con entramado
    arq.muro_huecos(c, X0, X1, Z0, 1.3, YF, YF + G, [(MIR[0], MIR[1], Z0, 1.3), (PUE[0], PUE[1], Z0, 1.3)], piedra)
    arq.muro_huecos(c, X0, X1, 1.3, ZT, YF + 0.04, YF + G, [(MIR[0], MIR[1], 1.3, MIR[3]), (PUE[0], PUE[1], 1.3, PUE[3]),
                                                            VEN], yeso)
    for x in (X0, X1 - G):
        c.caja_de((x, YF + G, Z0), (x + G, YB - G, 1.3), piedra)
        c.caja_de((x, YF + G, 1.3), (x + G, YB - G, ZT), yeso)
    c.caja_de((X0, YB - G, Z0), (X1, YB, 1.3), piedra)
    c.caja_de((X0, YB - G, 1.3), (X1, YB, ZT), yeso)
    # entramado: postes, carreras y tornapuntas que sobresalen del yeso
    for x in (X0 + 0.15, -0.25, 2.55, 4.75, X1 - 0.15):
        if MIR[0] < x < MIR[1] or PUE[0] < x < PUE[1]:
            continue
        c.caja((x, YF - 0.02, (1.3 + ZT) / 2), (0.25, 0.14, ZT - 1.3), viga, 0.03)
    c.caja_de((X0, YF - 0.1, 1.25), (X1, YF + 0.06, 1.45), viga_x, 0.03)
    c.caja_de((X0, YF - 0.1, ZT - 0.25), (X1, YF + 0.06, ZT), viga_x, 0.03)
    for (xa, xb) in ((X0 + 0.25, -0.35), (2.65, 4.65)):
        if xb - xa > 2:
            pass
    c.caja(((2.55 + 4.75) / 2, YF - 0.02, 3.95), (2.3, 0.12, 0.18), viga_x, 0.02, rot=(0, 18, 0))
    for x in (X0, X1):
        for y in (-1.0, 1.4):
            c.caja((x + (0.02 if x < 0 else -0.02), y, (1.3 + ZT) / 2), (0.14, 0.25, ZT - 1.3), viga, 0.03)
        c.caja_de((x - 0.08, YF, ZT - 0.25), (x + 0.08, YB, ZT), viga_x, 0.02)

    m.seccion("tejado")
    # tejado a dos aguas con tejas de chapa en hileras (cada hilera es una pieza con grosor)
    cum = 6.8
    for s in (-1, 1):
        y_al = (YF - 0.6) if s < 0 else (YB + 0.6)
        ya, za = y_al, ZT - 0.1
        yb, zb = (YF + YB) / 2, cum
        filas = 6
        for k in range(filas):
            t0, t1 = k / filas, (k + 1.15) / filas
            p0 = V((0, ya + (yb - ya) * t0, za + (zb - za) * t0))
            p1 = V((0, ya + (yb - ya) * min(t1, 1), za + (zb - za) * min(t1, 1)))
            d = p1 - p0
            ang = math.degrees(math.atan2(d.z, d.y))
            with c.en(((p0 + p1) / 2) + V((0, 0, 0.08)), (ang, 0, 0)):
                c.caja((0, 0, 0), (X1 - X0 + 0.8, d.length, 0.1), teja, 0.025)
    c.cil((X0 - 0.45, (YF + YB) / 2, cum + 0.08), (X1 + 0.45, (YF + YB) / 2, cum + 0.08), 0.16, teja, n=10)
    # piñones de madera
    for x in (X0 - 0.05, X1 + 0.05):
        c.extruir([(YF, ZT), (YB, ZT), ((YF + YB) / 2, cum)], 0.12, tabla, c=(x, 0, 0), rot=(90, 0, 90))
    # chimenea del alambique: tubo de cobre que sale del tejado
    c.caja((-3.0, 1.6, 6.3), (0.8, 0.8, 1.6), piedra, 0.05)
    c.cil((-3.0, 1.6, 7.1), (-3.0, 1.6, 7.25), 0.45, piedra, n=8)
    c.tubo([(-3.0, 1.6, 7.25), (-3.0, 1.6, 7.6), (-2.7, 1.6, 7.85)], 0.12, cobre, n=8, seg=3)

    m.seccion("mirador con frascos")
    mx0, mx1, mz0, mz1 = MIR
    # mirador volado: base de madera, tres paños de cristal y tejadillo
    d = 0.9
    c.caja_de((mx0 - 0.15, YF - d, mz0 - 0.25), (mx1 + 0.15, YF, mz0), tabla, 0.04)
    for k in range(3):
        c.extruir([(0, 0), (0.5, 0), (0, 0.5)], 0.08, viga, c=(mx0 + 0.3 + k * (mx1 - mx0 - 0.6) / 2, YF - 0.0, mz0 - 0.25),
                  rot=(90, 90, 0))
    for x in (mx0 - 0.1, mx1 + 0.1, (mx0 + mx1) / 2):
        c.caja((x, YF - d + 0.06, (mz0 + mz1) / 2), (0.12, 0.12, mz1 - mz0), viga, 0.02)
    for x in (mx0 - 0.1, mx1 + 0.1):
        c.caja((x, YF - d / 2, (mz0 + mz1) / 2), (0.1, d - 0.1, 0.1), viga, 0.02)
    c.caja_de((mx0 - 0.2, YF - d - 0.1, mz1), (mx1 + 0.2, YF, mz1 + 0.15), tabla, 0.03)
    with c.en(((mx0 + mx1) / 2, YF - d / 2 - 0.05, mz1 + 0.3), (-22, 0, 0)):
        c.caja((0, 0, 0), (mx1 - mx0 + 0.6, d + 0.4, 0.08), teja, 0.02)
    cr.caja_de((mx0 - 0.04, YF - d + 0.02, mz0), (mx1 + 0.04, YF - d + 0.1, mz1), None)
    for x in (mx0 - 0.15, mx1 + 0.08):
        cr.caja_de((x, YF - d + 0.1, mz0), (x + 0.07, YF - 0.05, mz1), None)
    # nicho interior y tres baldas
    c.caja_de((mx0, YF + G, mz0 - 0.6), (mx1, YF + G + 0.9, mz0), tabla)
    c.caja_de((mx0 - 0.1, YF + G + 0.9, mz0 - 0.6), (mx1 + 0.1, YF + G + 1.05, mz1 + 0.3), m.mat("madera", "#3D2A1C", eje="Z",
                                                                                                 suciedad=0.2))
    for x in (mx0 - 0.1, mx1):
        c.caja_de((x, YF, mz0), (x + 0.1, YF + G + 0.9, mz1 + 0.3), yeso)
    c.caja_de((mx0, YF, mz1), (mx1, YF + G + 0.9, mz1 + 0.3), yeso)
    rnd = m.rnd
    baldas = [mz0 + 0.05, mz0 + 0.95, mz0 + 1.8]
    for zb in baldas:
        c.caja_de((mx0 - 0.0, YF - d + 0.15, zb - 0.06), (mx1, YF + G + 0.85, zb), tabla, 0.015)
        for x in (mx0 + 0.6, mx1 - 0.6):
            c.extruir([(0, 0), (0.25, 0), (0, -0.25)], 0.05, laton, c=(x, YF + G + 0.85, zb - 0.06), rot=(90, 0, -90))
    # frascos: cristal (malla _cristal) + líquido (opaco, con textura) + tapón
    def esferico(x, y, z, r, liq):
        frascos.esfera((x, y, z + r), r, None, seg=12, anillos=8)
        frascos.cil((x, y, z + r * 1.8), (x, y, z + r * 2.35), r * 0.32, None, n=10)
        c.esfera((x, y, z + r * 0.92), r * 0.84, liq, seg=10, anillos=6, esc=(1, 1, 0.82))
        c.cil((x, y, z + r * 2.3), (x, y, z + r * 2.55), r * 0.28, corcho, n=8, r1=r * 0.33)
        c.cil((x, y, z), (x, y, z + 0.03), r * 0.55, laton, n=10)  # aro de apoyo

    def cilindrico(x, y, z, r, h, liq):
        frascos.cil((x, y, z), (x, y, z + h), r, None, n=12)
        c.cil((x, y, z + 0.02), (x, y, z + h * 0.72), r * 0.86, liq, n=10)
        c.cil((x, y, z + h), (x, y, z + h + 0.07), r * 1.08, osc, n=10)  # tapa de rosca
        c.cil((x, y, z + h + 0.07), (x, y, z + h + 0.1), r * 0.5, osc, n=8)

    def botella(x, y, z, r, h, liq):
        frascos.torno([(0.0, 0.0), (r, 0.0), (r, h * 0.55), (r * 0.4, h * 0.78), (r * 0.36, h), (0.0, h)], None, n=12,
                      c=(x, y, z))
        c.torno([(0.0, 0.02), (r * 0.86, 0.02), (r * 0.86, h * 0.5), (0.0, h * 0.5)], liq, n=10, c=(x, y, z))
        c.cil((x, y, z + h * 0.95), (x, y, z + h * 1.12), r * 0.34, corcho, n=8, r1=r * 0.4)
        c.caja((x, y - r - 0.005, z + h * 0.3), (r * 1.2, 0.01, h * 0.25), m.mat("papel", "#E5DBC2"), 0.0)  # etiqueta

    liquidos = [verde, azul, ambar, rojo]
    for i, zb in enumerate(baldas):
        x = mx0 + 0.35
        k = 0
        while x < mx1 - 0.35:
            y = YF - d + 0.55 + rnd.uniform(-0.1, 0.2)
            tipo = (i + k) % 3
            liq = [verde, azul, liquidos[(i + k) % 4]][tipo]
            if tipo == 0:
                r = rnd.uniform(0.17, 0.24)
                esferico(x, y, zb, r, verde if rnd.random() < 0.7 else liq)
                x += 2 * r + 0.12
            elif tipo == 1:
                r = rnd.uniform(0.1, 0.14)
                cilindrico(x, y, zb, r, rnd.uniform(0.45, 0.65), azul)
                x += 2 * r + 0.14
            else:
                r = rnd.uniform(0.1, 0.13)
                botella(x, y, zb, r, rnd.uniform(0.5, 0.7), liq)
                x += 2 * r + 0.14
            k += 1
    neon.cil((mx0 + 0.1, YF - d + 0.3, mz1 - 0.12), (mx1 - 0.1, YF - d + 0.3, mz1 - 0.12), 0.035, None, n=8)

    m.seccion("puerta")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.18, 0.16, viga, abajo=False)
    pv = (px0 + 0.03, YF + 0.15, pz0)
    pu = m.parte("puerta", pivote=pv, nota="Puerta batiente de tablas: gira sobre las bisagras (eje vertical del pivote).")
    w = px1 - px0 - 0.06
    for k in range(5):
        pu.caja_de((px0 + 0.03 + k * w / 5 + 0.01, YF + 0.08, pz0 + 0.03), (px0 + 0.03 + (k + 1) * w / 5 - 0.01, YF + 0.2,
                                                                          pz1 - 0.04), tabla, 0.02)
    for zz in (pz0 + 0.5, pz1 - 0.6):
        pu.caja_de((px0 + 0.1, YF + 0.03, zz - 0.12), (px1 - 0.1, YF + 0.08, zz + 0.12), viga_x, 0.02)
        pu.caja_de((px0 + 0.03, YF + 0.02, zz - 0.07), (px0 + 1.0, YF + 0.05, zz + 0.07), osc, 0.01)  # pernio
        pu.cil((px0 + 0.03, YF + 0.15, zz - 0.15), (px0 + 0.03, YF + 0.15, zz + 0.15), 0.045, osc, n=8)
        for kx in range(3):
            pu.remache((px0 + 0.2 + kx * 0.35, YF + 0.02, zz), (0, -1, 0), osc, 0.03)
    pu.caja((px1 - 0.35, YF + 0.04, pz0 + 1.9), (0.14, 0.05, 0.3), laton, 0.02)
    pu.tubo([(px1 - 0.35, YF + 0.0, pz0 + 2.05), (px1 - 0.35, YF - 0.12, pz0 + 1.95), (px1 - 0.35, YF - 0.12, pz0 + 1.7),
             (px1 - 0.35, YF + 0.0, pz0 + 1.62)], 0.025, laton, n=6, seg=3)
    # ventanita redonda con cristal en la puerta
    with pu.en(((px0 + px1) / 2, YF + 0.02, pz1 - 1.2), (90, 0, 0)):
        pu.toro((0, 0, 0), 0.3, 0.05, laton, n=14, m=5)
    cr.cil(((px0 + px1) / 2, YF + 0.06, pz1 - 1.2), ((px0 + px1) / 2, YF + 0.16, pz1 - 1.2), 0.28, None, n=14)
    c.caja_de((px0 - 0.3, YF - 0.6, 0), (px1 + 0.3, YF, Z0 - 0.02), piedra, 0.05)

    m.seccion("ventanilla, mostrador y balanza")
    vx0, vx1, vz0, vz1 = VEN
    arq.marco(c, vx0, vx1, vz0, vz1, YF, 0.15, 0.12, viga)
    c.caja_de((vx0 - 0.25, YF - 0.75, vz0 - 0.1), (vx1 + 0.25, YF + 0.1, vz0 + 0.02), tabla, 0.03)  # mostrador
    for x in (vx0 - 0.1, vx1 + 0.1):
        c.extruir([(0, 0), (0.6, 0), (0, -0.6)], 0.07, viga, c=(x, YF, vz0 - 0.1), rot=(90, 0, -90))
    # contraventana abierta (pieza fija) y fondo del despacho
    c.caja_de((vx1 + 0.2, YF - 0.12, vz0), (vx1 + 1.0, YF - 0.05, vz1), tabla, 0.02)
    c.caja_de((vx0, YF + G, vz0 - 0.2), (vx1, YF + G + 0.8, vz1 + 0.2), m.mat("madera", "#3D2A1C", eje="Z", suciedad=0.2))
    # balanza antigua sci-fi: base, columna, cruz, dos platos colgados y una pantallita
    bx, by, bz = (vx0 + vx1) / 2 - 0.1, YF - 0.4, vz0 + 0.02
    c.caja((bx, by, bz + 0.04), (0.5, 0.25, 0.08), laton, 0.02)
    c.cil((bx, by, bz + 0.08), (bx, by, bz + 0.6), 0.03, laton, n=8)
    c.esfera((bx, by, bz + 0.62), 0.045, laton, seg=8, anillos=5)
    with c.en((bx, by, bz + 0.62), (0, -8, 0)):
        c.caja((0, 0, 0), (0.62, 0.03, 0.03), laton, 0.005)
        for s in (-1, 1):
            for dy in (-0.05, 0.05):
                c.cil((s * 0.3, 0, 0), (s * 0.3, dy, -0.28), 0.006, laton, n=4)
            c.cil((s * 0.3, 0, -0.29), (s * 0.3, 0, -0.27), 0.1, laton, n=12)
    c.caja((bx + 0.22, by - 0.13, bz + 0.06), (0.1, 0.02, 0.05), osc, 0.005)
    neon.caja((bx + 0.22, by - 0.141, bz + 0.06), (0.07, 0.004, 0.03), None)
    # mortero y una caja de viales sobre el mostrador
    c.torno([(0.0, 0.0), (0.12, 0.0), (0.14, 0.1), (0.12, 0.14), (0.08, 0.06), (0.0, 0.06)], m.mat("piedra", "#BDB6AA"),
            n=10, c=(vx1 - 0.15, YF - 0.4, vz0 + 0.02))
    c.cil((vx1 - 0.15, YF - 0.4, vz0 + 0.1), (vx1 - 0.25, YF - 0.45, vz0 + 0.3), 0.02, tabla, n=5)

    m.seccion("cartel")
    c.caja(((X0 + X1) / 2 - 1.3, YF - 0.2, ZT + 0.35), (3.6, 0.1, 0.62), viga_x, 0.03)
    neon.texto("SUMINISTROS", None, alto=0.36, grosor=0.05, c=((X0 + X1) / 2 - 1.3, YF - 0.28, ZT + 0.2),
               fuente="estrecha")
    for x in ((X0 + X1) / 2 - 2.9, (X0 + X1) / 2 + 0.3):
        c.perno((x, YF - 0.26, ZT + 0.35), (0, -1, 0), laton, r=0.03)
    # banderola colgante con un matraz recortado
    c.tubo([(X1 - 0.3, YF - 0.0, 3.9), (X1 - 0.3, YF - 0.9, 3.9)], 0.03, osc, n=6, suave=False)
    for x in (X1 - 0.3,):
        c.extruir([(-0.03, 0), (0.03, 0), (0.03, -0.2), (0.25, -0.65), (-0.25, -0.65), (-0.03, -0.2)], 0.05, laton,
                  c=(x, YF - 0.6, 3.85), rot=(90, 0, 90))

    m.seccion("rejilla de vapor")
    gy = 0.0
    c.caja((X1 + 0.06, gy, 2.6), (0.14, 1.0, 0.7), osc, 0.03)
    for k in range(5):
        c.caja((X1 + 0.15, gy, 2.35 + k * 0.12), (0.05, 0.86, 0.04), acero, 0.008, rot=(30, 0, 0))
    for (dx, dy, dz, r) in ((0.3, 0.0, 3.0, 0.22), (0.45, 0.15, 3.35, 0.3), (0.5, -0.1, 3.75, 0.36), (0.55, 0.1, 4.2, 0.3),
                            (0.6, -0.05, 4.6, 0.22)):
        vapor.ico((X1 + dx, gy + dy, dz), r, None, sub=1, ruido=0.25, semilla=int(dz * 10))
    m.anclaje("Vapor", (X1 + 0.3, gy, 2.9), "Salida del vapor: aquí puede ir un ParticleEmitter verde tenue.")
    # bidones de cobre junto a la fachada lateral
    for i, (x, y) in enumerate(((X1 + 0.5, 2.0), (X1 + 0.5, 2.85))):
        c.torno([(0.0, 0.0), (0.32, 0.0), (0.36, 0.1), (0.36, 0.9), (0.3, 1.0), (0.0, 1.0)], cobre, n=12, c=(x, y, 0))
        c.toro((x, y, 0.5), 0.37, 0.025, osc, n=12, m=4)
    m.terminar()


# ==============================================================================================================
def tienda_herramientas():
    m = Modelo("tienda_herramientas", ZONA, (10, 8, 7), 12000,
               "Ferretería Torres: fachada industrial de chapa ondulada oscura, persiana metálica a medias, panel "
               "perforado lateral con herramientas 3D, cajas de herramientas apiladas y cartel pintado a mano.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#9EC2D2", transparencia=0.35)
    luces = m.parte("luces_neon", tipo="neon", color=NEON)

    ondu = m.mat("pintura", "#2F363E", desgaste=0.55, c_desgaste="#8E949A")
    marco_m = m.mat("pintura", "#1F2429", desgaste=0.4)
    horm = m.mat("hormigon", "#8E8A82", manchas=[(1.5, -3.5, 0.3, 0.9, "#14110e", 0.8)])
    acero = m.mat("metal", "#80868C")
    galv = m.mat("metal", "#A3A9AE", rug=0.5)
    amarillo = m.mat("pintura", "#E0A82A", desgaste=0.7)
    rojo = m.mat("pintura", "#B3312A", desgaste=0.6)
    azul_c = m.mat("pintura", "#1B2F4E", desgaste=0.3, lluvia=0.2)
    blanco_p = m.mat("pintura", "#ECEBE6", desgaste=0.35, c_desgaste="#1B2F4E", aranazos=0.0)
    tablero = m.mat("madera", "#B08A5E", eje="X", suciedad=0.35)
    mango = m.mat("madera", "#8A5A32", eje="Z")
    goma = m.mat("goma", "#1F2023")

    X0, X1, YF, YB, Z0, ZT = -5.0, 5.0, -3.4, 3.6, 0.3, 6.4

    m.seccion("cuerpo")
    c.caja_de((X0 - 0.1, YF - 0.9, 0), (X1 + 0.1, YB + 0.1, Z0), horm, 0.04)
    PER = (-4.2, 1.0, Z0, 4.6)  # persiana
    PUE = (1.8, 3.6, Z0, 4.2)

    def chapa_ondulada(xa, xb, za, zb, y, sentido=-1):
        # chapa con grosor y ondas reales (la onda corre en X)
        c.lamina(lambda u, v: (xa + u * (xb - xa), y + sentido * 0.05 * math.sin(u * (xb - xa) / 0.35 * math.tau),
                               za + v * (zb - za)), max(4, int((xb - xa) / 0.35 * 4)), 1, 0.04, ondu)

    # estructura: pilares IPE y vigas, la chapa se pone entre ellos
    for x in (X0, X1):
        for y in (YF, YB):
            arq.viga_h(c, (x, y, Z0), (x, y, ZT), 0.35, 0.3, marco_m)
    for y in (YF, YB):
        arq.viga_h(c, (X0, y, ZT - 0.2), (X1, y, ZT - 0.2), 0.4, 0.3, marco_m)
    for x in (X0, X1):
        arq.viga_h(c, (x, YF, ZT - 0.2), (x, YB, ZT - 0.2), 0.4, 0.3, marco_m)
    # fachada: chapa por encima y a los lados de los huecos
    chapa_ondulada(X0 + 0.15, PER[0] - 0.1, Z0 + 0.6, ZT - 0.4, YF + 0.05)
    chapa_ondulada(PER[1] + 0.25, PUE[0] - 0.2, Z0 + 0.6, ZT - 0.4, YF + 0.05)
    chapa_ondulada(PUE[1] + 0.2, X1 - 0.15, Z0 + 0.6, ZT - 0.4, YF + 0.05)
    chapa_ondulada(PER[0] - 0.1, PUE[1] + 0.2, PER[3] + 0.5, ZT - 0.4, YF + 0.05)
    # zócalo de hormigón bajo la chapa
    c.caja_de((X0 + 0.1, YF - 0.05, Z0), (PER[0] - 0.1, YF + 0.25, Z0 + 0.6), horm, 0.03)
    c.caja_de((PER[1] + 0.25, YF - 0.05, Z0), (PUE[0] - 0.2, YF + 0.25, Z0 + 0.6), horm, 0.03)
    c.caja_de((PUE[1] + 0.2, YF - 0.05, Z0), (X1 - 0.1, YF + 0.25, Z0 + 0.6), horm, 0.03)
    # laterales y trasera (chapa por fuera)
    for x, s in ((X0 - 0.02, -1), (X1 + 0.02, 1)):
        c.lamina(lambda u, v, x=x, s=s: (x + s * 0.05 * math.sin(u * 7 / 0.35 * math.tau), YF + 0.15 + u * 6.9,
                                         Z0 + v * (ZT - 0.4 - Z0)), 80, 1, 0.04, ondu)
    c.lamina(lambda u, v: (X0 + 0.15 + u * 9.7, YB + 0.05 + 0.05 * math.sin(u * 9.7 / 0.35 * math.tau),
                           Z0 + v * (ZT - 0.4 - Z0)), 110, 1, 0.04, ondu)
    # cubierta plana con borde
    c.caja_de((X0 - 0.2, YF - 0.2, ZT), (X1 + 0.2, YB + 0.2, ZT + 0.2), marco_m, 0.04)
    c.caja_de((X0 - 0.25, YF - 0.25, ZT + 0.2), (X1 + 0.25, YB + 0.25, ZT + 0.32), galv, 0.02)
    # extractor de tejado
    c.cil((2.5, 1.5, ZT + 0.32), (2.5, 1.5, ZT + 0.62), 0.35, galv, n=10)
    c.cil((2.5, 1.5, ZT + 0.62), (2.5, 1.5, ZT + 0.72), 0.5, galv, n=10, r1=0.12)

    m.seccion("persiana a medias")
    px0, px1, pz0, pz1 = PER
    for x in (px0 - 0.05, px1 + 0.05):
        c.caja((x, YF - 0.05, (pz0 + pz1) / 2), (0.16, 0.22, pz1 - pz0), galv, 0.02)  # guías
    c.caja(((px0 + px1) / 2, YF - 0.2, pz1 + 0.3), (px1 - px0 + 0.5, 0.55, 0.6), galv, 0.05)  # cajón
    pers = m.parte("persiana", pivote=((px0 + px1) / 2, YF - 0.05, pz1),
                   nota="Persiana de lamas (a media altura). Para cerrarla, estirarla hacia abajo: alto cerrada = "
                        f"{pz1 - pz0:.2f} studs.")
    zb = 2.6
    n = int((pz1 - zb) / 0.22)
    for k in range(n):
        z = pz1 - 0.11 - k * 0.22
        pers.caja(((px0 + px1) / 2, YF - 0.05, z), (px1 - px0, 0.06, 0.18), galv, 0.03)
    pers.caja(((px0 + px1) / 2, YF - 0.05, zb + 0.02), (px1 - px0, 0.12, 0.08), marco_m, 0.02)
    for x in ((px0 + px1) / 2 - 0.4, (px0 + px1) / 2 + 0.4):
        pers.caja((x, YF - 0.13, zb + 0.06), (0.25, 0.06, 0.06), acero, 0.01)
    # tras la persiana: escaparate con cristal y estanterías
    arq.marco(c, px0, px1, pz0 + 0.6, pz1 - 0.05, YF + 0.15, 0.1, 0.1, marco_m)
    cr.caja_de((px0, YF + 0.12, pz0 + 0.6), (px1, YF + 0.2, pz1 - 0.05), None)
    c.caja_de((px0, YF + 0.2, pz0), (px1, YF + 1.8, pz0 + 0.6), marco_m)
    c.caja_de((px0, YF + 1.8, pz0), (px1, YF + 1.95, pz1), tablero)
    for zz in (1.5, 2.4):
        c.caja_de((px0 + 0.1, YF + 1.2, zz - 0.05), (px1 - 0.1, YF + 1.8, zz), galv, 0.01)
        for i in range(6):
            x = px0 + 0.5 + i * (px1 - px0 - 1.0) / 5
            col = [amarillo, rojo, galv][i % 3]
            c.caja((x, YF + 1.5, zz + 0.18), (0.5, 0.4, 0.35), col, 0.03)
    luces.cil((px0 + 0.2, YF + 0.8, pz1 - 0.2), (px1 - 0.2, YF + 0.8, pz1 - 0.2), 0.035, None, n=8)
    c.caja_de((px0, YF + 0.2, pz1 - 0.05), (px1, YF + 1.95, pz1 + 0.05), marco_m)
    for x in (px0, px1 - 0.1):
        c.caja_de((x, YF + 0.2, pz0), (x + 0.1, YF + 1.95, pz1), marco_m)

    m.seccion("puerta")
    qx0, qx1, qz0, qz1 = PUE
    arq.marco(c, qx0, qx1, qz0, qz1, YF + 0.1, 0.18, 0.16, marco_m, abajo=False)
    pv = (qx0, YF + 0.12, qz0)
    pu = m.parte("puerta", pivote=pv, nota="Puerta metálica batiente con ventanuco: gira sobre la bisagra.")
    pc = m.parte("puerta_cristal", tipo="cristal", color="#9EC2D2", pivote=pv, transparencia=0.35)
    pu.caja_de((qx0, YF + 0.06, qz0 + 0.02), (qx1, YF + 0.18, qz0 + 2.0), rojo, 0.03)
    pu.caja_de((qx0, YF + 0.06, qz1 - 0.4), (qx1, YF + 0.18, qz1 - 0.02), rojo, 0.03)
    pu.caja_de((qx0, YF + 0.06, qz0 + 2.0), (qx0 + 0.3, YF + 0.18, qz1 - 0.4), rojo, 0.02)
    pu.caja_de((qx1 - 0.3, YF + 0.06, qz0 + 2.0), (qx1, YF + 0.18, qz1 - 0.4), rojo, 0.02)
    pc.caja_de((qx0 + 0.3, YF + 0.09, qz0 + 2.0), (qx1 - 0.3, YF + 0.15, qz1 - 0.4), None)
    for zz in (qz0 + 0.5, qz1 - 0.6):
        pu.cil((qx0, YF + 0.12, zz - 0.15), (qx0, YF + 0.12, zz + 0.15), 0.045, acero, n=8)
    pu.caja((qx1 - 0.25, YF + 0.03, qz0 + 1.75), (0.1, 0.06, 0.4), acero, 0.02)
    pu.cil((qx1 - 0.25, YF + 0.0, qz0 + 1.65), (qx1 - 0.45, YF - 0.05, qz0 + 1.65), 0.025, acero, n=6)
    pu.caja_de((qx0 + 0.15, YF + 0.04, qz0 + 0.2), (qx1 - 0.15, YF + 0.06, qz0 + 0.6), galv, 0.01)  # chapa de patadas

    m.seccion("cartel pintado")
    sx, sz = -1.2, ZT - 0.9
    c.caja((sx, YF - 0.2, sz), (6.6, 0.12, 0.9), azul_c, 0.03)
    c.caja((sx, YF - 0.27, sz), (6.4, 0.02, 0.76), azul_c, 0.0)
    c.texto("FERRETERÍA TORRES", blanco_p, alto=0.42, grosor=0.02, c=(sx, YF - 0.28, sz - 0.18), fuente="serif",
            espaciado=1.02)
    for x in (sx - 3.1, sx + 3.1):
        c.perno((x, YF - 0.27, sz), (0, -1, 0), acero, r=0.035)
    arq.foco_pared(c, luces, (sx - 2.0, YF - 0.25, sz + 0.75), marco_m, acero, tam=0.3)
    arq.foco_pared(c, luces, (sx + 2.0, YF - 0.25, sz + 0.75), marco_m, acero, tam=0.3)

    m.seccion("cajas de herramientas")
    def caja_h(cx, cy, cz, w, d, h, col, asa=True):
        c.caja((cx, cy, cz + h / 2), (w, d, h), col, 0.04)
        c.caja((cx, cy, cz + h * 0.72), (w + 0.02, d + 0.02, 0.03), marco_m, 0.0)  # junta de tapa
        for s in (-1, 1):
            c.caja((cx + s * w * 0.3, cy - d / 2 - 0.02, cz + h * 0.72), (0.12, 0.04, 0.16), galv, 0.01)  # cierres
        if asa:
            c.tubo([(cx - w * 0.25, cy, cz + h), (cx - w * 0.25, cy, cz + h + 0.12), (cx + w * 0.25, cy, cz + h + 0.12),
                    (cx + w * 0.25, cy, cz + h)], 0.03, marco_m, n=6, seg=2)
    caja_h(4.25, YF - 0.45, Z0, 1.1, 0.55, 0.6, rojo, asa=False)
    caja_h(4.2, YF - 0.45, Z0 + 0.62, 0.9, 0.48, 0.45, amarillo, asa=False)
    caja_h(4.3, YF - 0.48, Z0 + 1.09, 0.7, 0.38, 0.32, rojo)
    caja_h(1.3, YF - 0.5, Z0, 0.8, 0.45, 0.45, galv)

    m.seccion("panel de herramientas lateral")
    # panel perforado con marco en el lateral izquierdo del modelo (+X)... se pone en el lateral X0 (visible)
    xp = X0 - 0.12
    c.caja((xp, 0.0, 3.2), (0.08, 4.2, 2.6), tablero, 0.02)
    for y in (-2.15, 2.15):
        c.caja((xp - 0.02, y, 3.2), (0.12, 0.1, 2.7), marco_m, 0.01)
    for z in (1.85, 4.55):
        c.caja((xp - 0.02, 0.0, z), (0.12, 4.4, 0.1), marco_m, 0.01)
    c.caja((xp - 0.3, 0.0, 4.75), (0.6, 4.6, 0.06), marco_m, 0.02, rot=(0, -10, 0))  # tejadillo
    def gancho(y, z):
        c.tubo([(xp - 0.04, y, z), (xp - 0.2, y, z), (xp - 0.24, y, z + 0.06)], 0.012, galv, n=4, suave=False)

    # llave inglesa (perfil extruido)
    def llave(y, z, L=0.9):
        gancho(y, z + 0.05)
        with c.en((xp - 0.12, y, z), (0, 0, 90)):
            c.extruir([(-0.04, 0), (0.04, 0), (0.05, -L + 0.2), (0.12, -L + 0.12), (0.12, -L), (0.03, -L), (0.03, -L + 0.12),
                       (-0.03, -L + 0.12), (-0.03, -L), (-0.12, -L), (-0.12, -L + 0.12), (-0.05, -L + 0.2)], 0.05, galv,
                      rot=(90, 0, 0), b=0.008)
            c.cil((0, 0, -L + 0.25), (0, 0, -L + 0.33), 0.03, acero, n=8, giro=0)
    # martillo
    def martillo(y, z):
        gancho(y, z + 0.05)
        c.cil((xp - 0.14, y, z - 0.95), (xp - 0.14, y, z), 0.04, mango, n=8)
        c.cil((xp - 0.14, y, z - 0.95), (xp - 0.14, y, z - 0.65), 0.05, goma, n=8)
        c.caja((xp - 0.14, y, z + 0.06), (0.1, 0.42, 0.12), acero, 0.02)
        c.cil((xp - 0.14, y - 0.21, z + 0.06), (xp - 0.14, y - 0.3, z + 0.06), 0.065, acero, n=8)
        c.extruir([(0.21, -0.05), (0.38, 0.03), (0.38, 0.08), (0.21, 0.05)], 0.08, acero, c=(xp - 0.14, y, z + 0.06),
                  rot=(90, 0, 90))
    # sierra de mano con dientes
    def sierra(y, z):
        gancho(y, z + 0.05)
        dientes = []
        L = 1.3
        for i in range(16):
            dientes += [(-0.1 - i * L / 16, -0.32), (-0.1 - (i + 0.5) * L / 16, -0.38)]
        perf = [(0.0, 0.0), (-0.1, 0.0), (-L - 0.1, -0.24), (-L - 0.1, -0.32)] + list(reversed(dientes))
        c.extruir([(x_, z_) for x_, z_ in perf], 0.015, galv, c=(xp - 0.12, y + 0.65, z), rot=(90, 0, 90))
        c.extruir([(0.0, 0.08), (0.3, 0.08), (0.34, -0.38), (0.0, -0.4), (-0.04, -0.1)], 0.06, mango,
                  c=(xp - 0.12, y + 0.68, z - 0.02), rot=(90, 0, 90))
        for zz in (-0.05, -0.25):
            c.cil((xp - 0.16, y + 0.62, z + zz), (xp - 0.08, y + 0.62, z + zz), 0.02, laton_(m), n=6)
    llave(-1.5, 4.25)
    llave(-1.15, 4.25, 0.7)
    martillo(-0.5, 4.2)
    sierra(0.2, 4.1)
    # destornilladores y alicates en la fila baja
    for i in range(4):
        y = -1.6 + i * 0.25
        gancho(y, 2.9)
        c.cil((xp - 0.14, y, 2.85), (xp - 0.14, y, 2.5), 0.05, [rojo, amarillo][i % 2], n=8)
        c.cil((xp - 0.14, y, 2.5), (xp - 0.14, y, 2.0), 0.015, acero, n=6)
    with c.en((xp - 0.14, 1.3, 2.7), (0, 0, 90)):
        for s in (-1, 1):
            c.extruir([(0, 0), (s * 0.05, -0.35), (s * 0.12, -0.75), (s * 0.06, -0.77), (s * 0.02, -0.35)], 0.04,
                      [rojo, rojo][0], rot=(90, 0, 0))
            c.extruir([(0, 0), (s * 0.04, 0.25), (s * 0.015, 0.25)], 0.05, acero, rot=(90, 0, 0))
        c.cil((0, -0.05, 0), (0, 0.05, 0), 0.04, acero, n=8)
    m.terminar()


def laton_(m):
    return m.mat("metal", "#B9913F", rug=0.3)


MODELOS = {
    "tienda_armaduras": tienda_armaduras,
    "tienda_pociones": tienda_pociones,
    "tienda_herramientas": tienda_herramientas,
}
