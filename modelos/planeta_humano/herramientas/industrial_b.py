"""Zona industrial (2): cinta, tanque, silo, tubería, chimenea, plataforma elevadora, depósito, prensa y almacén."""

import math

import arq
from ph import NEON, V, Modelo

ZONA = "industrial"


def _brida(c, p, eje, r, mat, pernos=8):
    """Brida de unión (disco) con N pernos alrededor, perpendicular al vector eje."""
    from ph import base_eje
    e = V(eje).normalized()
    c.cil(p - e * 0.05, p + e * 0.05, r, mat, n=16)
    B = base_eje(e)
    for k in range(pernos):
        a = k * math.tau / pernos
        q = p + B @ V((math.cos(a) * r * 0.78, math.sin(a) * r * 0.78, 0))
        c.cil(q - e * 0.09, q + e * 0.09, 0.03, mat, n=6)


# ==============================================================================================================
def cinta_transportadora():
    m = Modelo("cinta_transportadora", ZONA, (6, 2, 2), 4000,
               "Segmento modular de cinta transportadora: banda de goma con nervios en V, 4 rodillos, patas en A, "
               "protecciones laterales y motor eléctrico con cables en un extremo.")
    c = m.parte()
    banda = m.mat("goma", "#26282B", bump=0.6)
    acero = m.mat("metal", "#7E848A")
    verde = m.mat("pintura", "#3C6E4E", desgaste=0.65)
    osc = m.mat("metal", "#2D3136", rug=0.5)
    amar = m.mat("pintura", "#E2B030", desgaste=0.5)
    cable = m.mat("goma", "#161719")
    L, Z = 6.0, 1.3
    # bastidor lateral (perfil en C) y rodillos
    for s in (-1, 1):
        c.caja((0, s * 0.62, Z - 0.05), (L, 0.06, 0.3), verde, 0.02)
        c.caja((0, s * 0.56, Z - 0.18), (L, 0.18, 0.04), verde, 0.0)
        c.caja((0, s * 0.56, Z + 0.08), (L, 0.18, 0.04), verde, 0.0)
    for k in range(4):
        x = -L / 2 + 0.4 + k * (L - 0.8) / 3
        c.cil((x, -0.58, Z), (x, 0.58, Z), 0.13, acero, n=12)
        for s in (-1, 1):
            c.cil((x, s * 0.62, Z), (x, s * 0.68, Z), 0.06, osc, n=8)
    # banda: lámina cerrada alrededor de los rodillos extremos (arriba plana, abajo y vueltas)
    R = 0.15
    x0, x1 = -L / 2 + 0.4, L / 2 - 0.4
    pts = []
    for i in range(7):
        a = math.pi / 2 - math.pi * i / 6
        pts.append((x1 + math.cos(a) * R, Z + math.sin(a) * R))
    for i in range(7):
        a = -math.pi / 2 - math.pi * i / 6
        pts.append((x0 + math.cos(a) * R, Z + math.sin(a) * R))
    for (xa, za), (xb, zb) in zip(pts, pts[1:] + pts[:1]):
        L_ = math.hypot(xb - xa, zb - za)
        ang = math.degrees(math.atan2(zb - za, xb - xa))
        c.caja(((xa + xb) / 2, 0, (za + zb) / 2), (L_ + 0.01, 1.0, 0.04), banda, 0.0, rot=(0, -ang, 0))
    # nervios en V sobre la banda superior
    for k in range(10):
        x = x0 + 0.3 + k * (x1 - x0 - 0.6) / 9
        for s in (-1, 1):
            c.caja((x + 0.12, s * 0.22, Z + R + 0.03), (0.06, 0.5, 0.04), banda, 0.01, rot=(0, 0, s * 30))
    # protecciones laterales para que no caiga material
    for s in (-1, 1):
        c.caja((0, s * 0.64, Z + 0.3), (L - 0.2, 0.04, 0.24), amar, 0.01, rot=(s * 10, 0, 0))
        for k in range(4):
            x = -L / 2 + 0.6 + k * (L - 1.2) / 3
            c.caja((x, s * 0.65, Z + 0.17), (0.06, 0.06, 0.28), osc, 0.0)
    # patas en A con tirantes y pies
    for x in (-L / 2 + 0.7, L / 2 - 0.7):
        for s in (-1, 1):
            c.cil((x - 0.35, s * 0.6, 0.0), (x, s * 0.6, Z - 0.2), 0.05, osc, n=6)
            c.cil((x + 0.35, s * 0.6, 0.0), (x, s * 0.6, Z - 0.2), 0.05, osc, n=6)
            for dx in (-0.35, 0.35):
                c.caja((x + dx, s * 0.6, 0.02), (0.2, 0.2, 0.04), acero, 0.005)
            c.cil((x - 0.2, s * 0.6, 0.5), (x + 0.2, s * 0.6, 0.5), 0.03, osc, n=5)
        c.cil((x, -0.6, 0.5), (x, 0.6, 0.5), 0.03, osc, n=5)
    # motor en el extremo +X (lado izquierdo del modelo)
    mx = L / 2 - 0.4
    c.cil((mx, 0.72, Z), (mx, 1.35, Z), 0.24, m.mat("pintura", "#2E5A8A", desgaste=0.5), n=14)
    for k in range(6):
        c.cil((mx, 0.8 + k * 0.09, Z), (mx, 0.84 + k * 0.09, Z), 0.27, m.mat("pintura", "#2E5A8A"), n=14)  # aletas
    c.caja((mx, 1.05, Z + 0.32), (0.3, 0.25, 0.2), osc, 0.03)  # caja de bornes
    c.tubo([(mx + 0.1, 1.05, Z + 0.42), (mx + 0.4, 1.05, Z + 0.5), (mx + 0.6, 1.0, Z), (mx + 0.6, 0.9, 0.05),
            (mx + 0.9, 0.9, 0.03)], 0.035, cable, n=5, seg=3)
    c.caja((mx, 1.04, Z - 0.28), (0.4, 0.5, 0.08), osc, 0.01)  # bancada del motor
    m.notas.append("Segmento de 6 studs: se encadena en el eje X de Roblox. El motor puede quitarse en los tramos "
                   "intermedios (va en la misma malla: copia el segmento si no lo quieres en todos).")
    m.terminar()


# ==============================================================================================================
def tanque_combustible():
    m = Modelo("tanque_combustible", ZONA, (6, 4, 4), 8000,
               "Tanque de combustible horizontal sobre patas en Y: chapa curvada con soldaduras, válvula de llenado "
               "con tapa y cadena, grifo con manguera, nivel de cristal, cartel INFLAMABLE y manchas en la base.")
    c = m.parte()
    nivel = m.parte("nivel_cristal", tipo="cristal", color="#D5EEF2", transparencia=0.5)
    chapa = m.mat("pintura", "#C8C2B4", desgaste=0.45, c_desgaste="#7A6E62", lluvia=0.6,
                  manchas=[(0.0, -1.5, 1.2, 0.6, "#5A4A2A", 0.6)])
    acero = m.mat("metal", "#7E848A")
    osc = m.mat("metal", "#2E3236", rug=0.5)
    soldadura = m.mat("metal", "#5E5A56", rug=0.6, bump=1.0, patron="poros")
    rojo = m.mat("pintura", "#C02A22", desgaste=0.3)
    amar = m.mat("pintura", "#E8B52A", desgaste=0.4)
    tinta = m.mat("pintura", "#16181A", desgaste=0.0)
    goma = m.mat("goma", "#1A1B1D")
    horm = m.mat("hormigon", "#8A867E", manchas=[(0.8, -1.2, 0.0, 1.0, "#14110e", 0.85), (-1.6, 0.6, 0.0, 0.7, "#1a1612", 0.6)])
    combustible = m.mat("liquido", "#C9A23A")
    R, L, Zc = 1.5, 5.4, 2.3
    c.caja((0, 0, 0.1), (6.0, 3.8, 0.2), horm, 0.04)
    # cuerpo cilíndrico con fondos abombados (a lo largo de X)
    perfil = [(0.0, -L / 2 - 0.35), (R * 0.6, -L / 2 - 0.25), (R * 0.92, -L / 2 - 0.08), (R, -L / 2 + 0.05),
              (R, L / 2 - 0.05), (R * 0.92, L / 2 + 0.08), (R * 0.6, L / 2 + 0.25), (0.0, L / 2 + 0.35)]
    c.torno(perfil, chapa, n=24, c=(0, 0, Zc), eje="X")
    # cordones de soldadura (anillos y longitudinal)
    for x in (-L / 2 + 0.05, -0.9, 0.9, L / 2 - 0.05):
        c.toro((x, 0, Zc), R + 0.005, 0.03, soldadura, n=24, m=4, rot=(0, 90, 0))
    c.cil((-L / 2, -0.35, Zc + R - 0.04), (L / 2, -0.35, Zc + R - 0.04), 0.025, soldadura, n=4)
    # patas en Y: cuna curva + pata con dos brazos
    for x in (-1.6, 1.6):
        c.lamina(lambda u, v, x=x: (x + (v - 0.5) * 0.3, math.cos(math.pi * (1.15 + 0.7 * u)) * (R + 0.06),
                                    Zc + math.sin(math.pi * (1.15 + 0.7 * u)) * (R + 0.06)), 10, 1, 0.08, osc)
        c.cil((x, 0, 0.2), (x, 0, 0.75), 0.12, osc, n=8)
        for s in (-1, 1):
            c.cil((x, 0, 0.75), (x, s * 1.05, Zc - 1.05), 0.09, osc, n=8)
        c.caja((x, 0, 0.24), (0.5, 0.5, 0.08), acero, 0.01)
        for dy in (-0.18, 0.18):
            c.perno((x + 0.18, dy, 0.28), (0, 0, 1), acero, r=0.035)
    # escotilla / válvula de llenado superior con tapa y cadena
    vt = V((0.6, 0, Zc + R))
    c.cil(vt - V((0, 0, 0.1)), vt + V((0, 0, 0.25)), 0.2, acero, n=12)
    _brida(c, vt + V((0, 0, 0.25)), (0, 0, 1), 0.3, acero, pernos=8)
    with c.en(vt + V((0.35, 0, 0.32)), (0, -60, 0)):  # tapa abierta sobre su bisagra
        c.cil((0, 0, 0), (0, 0, 0.06), 0.26, rojo, n=12)
    pts = [vt + V((0.25, 0.2, 0.3)), vt + V((0.15, 0.32, 0.05)), vt + V((0.05, 0.3, 0.32))]
    for i in range(6):
        p = pts[0].lerp(pts[1], i / 6) if i < 3 else pts[1].lerp(pts[2], (i - 3) / 3)
        c.toro(p, 0.025, 0.007, acero, n=6, m=3, rot=(90 * (i % 2), 0, 0))
    # boca de hombre en un fondo
    c.cil((-L / 2 - 0.3, 0, Zc + 0.3), (-L / 2 - 0.42, 0, Zc + 0.3), 0.4, acero, n=16)
    for k in range(10):
        a = k * math.tau / 10
        c.perno((-L / 2 - 0.42, math.cos(a) * 0.33, Zc + 0.3 + math.sin(a) * 0.33), (-1, 0, 0), acero, r=0.03)
    # grifo de salida inferior con volante y manguera corta
    g = V((1.9, -0.6, Zc - R + 0.08))
    c.cil(g, g - V((0, 0, 0.35)), 0.07, acero, n=8)
    c.cil(g - V((0, 0, 0.35)), g - V((0, 0.35, 0.35)), 0.07, acero, n=8)
    c.cil(g - V((0, 0.1, 0.2)), g - V((0, 0.1, 0.05)), 0.02, acero, n=5)
    c.toro(g - V((0, 0.1, 0.03)), 0.12, 0.02, rojo, n=10, m=4)
    c.tubo([g - V((0, 0.35, 0.35)), g - V((0, 0.6, 0.4)), g - V((-0.3, 0.75, 0.75)), g - V((-0.7, 0.5, Zc - R - 0.1))],
           0.06, goma, n=6, seg=3)
    c.cil(g - V((-0.7, 0.5, Zc - R - 0.1)), g - V((-0.95, 0.5, Zc - R - 0.08)), 0.07, acero, n=8)
    # medidor de nivel lateral: tubo de cristal vertical con líquido y protector
    nx, ny = -1.0, -R - 0.18
    for zz in (Zc - 0.9, Zc + 0.9):
        c.cil((nx, -R * 0.6, zz), (nx, ny, zz), 0.04, acero, n=6)
    nivel.cil((nx, ny, Zc - 0.9), (nx, ny, Zc + 0.9), 0.06, None, n=10)
    c.cil((nx, ny, Zc - 0.88), (nx, ny, Zc + 0.2), 0.04, combustible, n=8)
    for s in (-1, 1):
        c.cil((nx + s * 0.09, ny, Zc - 0.95), (nx + s * 0.09, ny, Zc + 0.95), 0.015, acero, n=4)
    for k in range(5):
        c.caja((nx + 0.12, ny, Zc - 0.8 + k * 0.4), (0.08, 0.01, 0.015), tinta, 0.0)
    # cartel triangular INFLAMABLE pintado sobre la chapa (chapa fina curvada a la superficie)
    with c.en((0.4, -R - 0.005, Zc + 0.15), (90, 0, 0)):
        c.extruir([(-0.55, -0.42), (0.55, -0.42), (0.0, 0.52)], 0.012, amar)
        c.extruir([(-0.45, -0.36), (0.45, -0.36), (0.0, 0.42)], 0.016, tinta)
        c.extruir([(-0.38, -0.32), (0.38, -0.32), (0.0, 0.35)], 0.02, amar)
        c.extruir([(0.0, -0.22), (0.12, -0.05), (0.05, -0.02), (0.1, 0.18), (-0.06, -0.02), (0.0, -0.06), (-0.12, -0.1)],
                  0.024, tinta)  # llama
    c.texto("INFLAMABLE", tinta, alto=0.2, grosor=0.012, c=(0.4, -R + 0.04, Zc - 0.65), rot=(80, 0, 0), fuente="estrecha",
            resol=1)
    c.texto("DIESEL-H2", tinta, alto=0.22, grosor=0.01, c=(-1.6 + 3.2, -R + 0.1, Zc + 0.9), rot=(60, 0, 0), fuente="mono",
            resol=1)
    m.terminar()


# ==============================================================================================================
def silo_almacen():
    m = Modelo("silo_almacen", ZONA, (4, 4, 10), 8000,
               "Silo vertical de almacén: techo cónico con respiradero, escalerilla con jaula arriba, puerta de "
               "inspección con bisagras y volante, base de hormigón con cuatro patas y salida con válvula de mariposa.")
    c = m.parte()
    puerta = m.parte("puerta_inspeccion", pivote=(-0.55, -1.63, 5.0), nota="Puerta de inspección: gira sobre sus "
                                                                           "bisagras (eje vertical del pivote).")
    chapa = m.mat("metal", "#A7ADB2", rug=0.45, lluvia=0.7, suciedad=0.6, aranazos=0.2)
    acero = m.mat("metal", "#7A8086")
    osc = m.mat("metal", "#2E3236", rug=0.5)
    horm = m.mat("hormigon", "#9A958C")
    amar = m.mat("pintura", "#E0AE2A", desgaste=0.65)
    rojo = m.mat("pintura", "#B02A24", desgaste=0.4)
    R = 1.6
    Zb = 2.0  # arranque del cilindro
    Zt = 8.6
    # base de hormigón y 4 patas con cartelas
    c.caja((0, 0, 0.2), (4.0, 4.0, 0.4), horm, 0.06)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        p = V((math.cos(a) * 1.25, math.sin(a) * 1.25, 0.4))
        arq.viga_h(c, p, p + V((0, 0, Zb - 0.0)), 0.3, 0.28, osc)
        c.caja(p + V((0, 0, 0.04)), (0.5, 0.5, 0.08), acero, 0.01)
    # tolva cónica inferior y cilindro con anillos de chapa
    c.torno([(0.22, 0.6), (0.3, 0.6), (R, Zb), (R, Zt), (0.0, Zt)], chapa, n=24)
    for k in range(6):
        z = Zb + 0.1 + k * (Zt - Zb) / 6
        c.toro((0, 0, z), R + 0.01, 0.03, acero, n=24, m=4)
    # techo cónico con respiradero en la cima
    c.torno([(0.0, Zt), (R + 0.12, Zt), (R + 0.12, Zt + 0.08), (0.3, Zt + 1.0), (0.0, Zt + 1.0)], chapa, n=24)
    c.cil((0, 0, Zt + 0.95), (0, 0, Zt + 1.25), 0.18, acero, n=10)
    c.torno([(0.0, Zt + 1.25), (0.35, Zt + 1.25), (0.32, Zt + 1.32), (0.0, Zt + 1.45)], acero, n=10)
    for k in range(4):
        a = k * math.pi / 2
        c.cil((math.cos(a) * 0.12, math.sin(a) * 0.12, Zt + 1.0), (math.cos(a) * 0.3, math.sin(a) * 0.3, Zt + 1.25),
              0.02, acero, n=4)
    # barandilla perimetral del techo
    pts = [(math.cos(a) * (R + 0.05), math.sin(a) * (R + 0.05), Zt + 0.1) for a in
           [math.radians(-130 + i * 30) for i in range(9)]]
    arq.barandilla(c, pts, 0.9, amar, r=0.035, n=6)
    # escalerilla con jaula de seguridad (lado -Y... en el lateral +X para que se vea de 3/4)
    ex = R + 0.35
    for s in (-1, 1):
        c.cil((ex, s * 0.25, 0.4), (ex, s * 0.25, Zt + 0.9), 0.035, amar, n=6)
    for k in range(int((Zt + 0.4) / 0.35)):
        z = 0.6 + k * 0.35
        c.cil((ex, -0.25, z), (ex, 0.25, z), 0.02, amar, n=4)
    for z in (1.5, 4.0, 6.5, 8.0):
        for s in (-1, 1):
            c.cil((ex, s * 0.25, z), (R - 0.02, s * 0.25, z), 0.025, amar, n=4)
    for k in range(5):
        z = 5.4 + k * 0.85
        pts = [(ex, -0.25, z)] + [(ex + 0.38 + math.cos(a) * 0.38, math.sin(a) * 0.38, z) for a in
                                  [math.pi - math.pi * i / 6 for i in range(1, 6)]] + [(ex, 0.25, z)]
        pts = [(ex - 0.0, -0.3, z), (ex + 0.4, -0.38, z), (ex + 0.7, -0.2, z), (ex + 0.7, 0.2, z), (ex + 0.4, 0.38, z),
               (ex, 0.3, z)]
        c.tubo(pts, 0.022, amar, n=4, suave=False)
    for (dy) in (-0.38, 0.0, 0.38):
        c.cil((ex + (0.4 if dy else 0.7), dy, 5.4), (ex + (0.4 if dy else 0.7), dy, 8.8), 0.02, amar, n=4)
    # puerta de inspección a media altura (pieza aparte): marco fijo, hoja con volante de cierre
    py = -R
    c.caja((0, py - 0.02, 5.0), (1.3, 0.1, 1.3), acero, 0.04)
    for k in range(8):
        a = k * math.tau / 8
        c.perno((math.cos(a) * 0.55, py - 0.07, 5.0 + math.sin(a) * 0.55), (0, -1, 0), acero, r=0.03)
    puerta.caja((0, py - 0.12, 5.0), (1.05, 0.1, 1.05), chapa, 0.04)
    for zz in (4.7, 5.3):
        puerta.cil((-0.55, py - 0.12, zz - 0.1), (-0.55, py - 0.12, zz + 0.1), 0.05, osc, n=8)
    puerta.cil((0.15, py - 0.17, 5.0), (0.15, py - 0.3, 5.0), 0.03, acero, n=6)
    with puerta.en((0.15, py - 0.3, 5.0), (90, 0, 0)):
        puerta.toro((0, 0, 0), 0.22, 0.025, rojo, n=12, m=4)
        for k in range(3):
            a = k * math.tau / 3
            puerta.cil((0, 0, 0), (math.cos(a) * 0.22, math.sin(a) * 0.22, 0), 0.015, rojo, n=4)
    # tubería de salida inferior con válvula de mariposa
    c.cil((0, 0, 0.62), (0, 0, 0.9), 0.16, acero, n=10)
    _brida(c, V((0, 0, 0.62)), (0, 0, 1), 0.26, acero, pernos=6)
    c.tubo([(0, 0, 0.6), (0, 0, 0.75), (0, -0.2, 0.5), (0, -1.3, 0.5), (0, -1.9, 0.5)], 0.15, acero, n=10, seg=3)
    vp = V((0, -1.1, 0.5))
    c.cil(vp - V((0, 0.1, 0)), vp + V((0, 0.1, 0)), 0.24, osc, n=12)
    c.cil(vp + V((0, 0, 0.24)), vp + V((0, 0, 0.36)), 0.03, acero, n=6)
    c.caja(vp + V((0.2, 0, 0.38)), (0.5, 0.06, 0.05), rojo, 0.01)  # palanca de mariposa
    _brida(c, V((0, -1.9, 0.5)), (0, 1, 0), 0.24, acero, pernos=6)
    m.terminar()


# ==============================================================================================================
def tuberia_modular():
    m = Modelo("tuberia_modular", ZONA, (4, 1, 1), 3000,
               "Tubería modular: tramo recto, codo de 90°, válvula de volante con radios, bridas con 8 pernos, "
               "soporte de pared con abrazadera y junta de expansión ondulada.")
    c = m.parte()
    tubo = m.mat("pintura", "#3A6E8E", desgaste=0.55, lluvia=0.4)
    acero = m.mat("metal", "#7E848A")
    rojo = m.mat("pintura", "#B8302A", desgaste=0.5)
    goma = m.mat("metal", "#55595E", rug=0.6)
    r = 0.22
    y0 = 0.0
    z0 = 0.5
    # recto desde x=-2 hasta la junta, junta de expansión, válvula y codo que sube
    c.cil((-2.0, y0, z0), (-1.1, y0, z0), r, tubo, n=12)
    _brida(c, V((-1.1, y0, z0)), (1, 0, 0), r * 1.6, acero)
    perfil = []
    for k in range(9):
        perfil.append((r * (1.15 if k % 2 else 1.0), -1.08 + k * 0.08))
    c.torno([(0.0, -1.08)] + perfil + [(0.0, -0.44)], goma, n=12, c=(0, y0, z0), eje="X")
    _brida(c, V((-0.42, y0, z0)), (1, 0, 0), r * 1.6, acero)
    c.cil((-0.42, y0, z0), (0.2, y0, z0), r, tubo, n=12)
    _brida(c, V((0.2, y0, z0)), (1, 0, 0), r * 1.6, acero)
    # cuerpo de la válvula y volante con radios
    c.esfera((0.55, y0, z0), r * 1.45, acero, seg=12, anillos=7)
    _brida(c, V((0.9, y0, z0)), (1, 0, 0), r * 1.6, acero)
    c.cil((0.55, y0, z0 + r * 1.2), (0.55, y0, z0 + 0.6), 0.06, acero, n=8)
    c.cil((0.55, y0, z0 + 0.42), (0.55, y0, z0 + 0.5), 0.1, acero, n=8)
    c.toro((0.55, y0, z0 + 0.62), 0.24, 0.025, rojo, n=16, m=4)
    for k in range(5):
        a = k * math.tau / 5
        c.cil((0.55, y0, z0 + 0.62), (0.55 + math.cos(a) * 0.24, y0 + math.sin(a) * 0.24, z0 + 0.62), 0.018, rojo, n=4)
    c.cil((0.55, y0, z0 + 0.6), (0.55, y0, z0 + 0.68), 0.05, rojo, n=8)
    # tramo y codo de 90° hacia arriba... hacia atrás (+Y del modelo) para quedarse en 1 de alto
    c.cil((0.9, y0, z0), (1.4, y0, z0), r, tubo, n=12)
    pts = [(1.4, y0, z0)] + [(1.4 + math.sin(a) * 0.45, y0 + (1 - math.cos(a)) * 0.45 - 0.0, z0)
                             for a in [math.pi / 2 * i / 6 for i in range(1, 7)]]
    c.tubo(pts, r, tubo, n=12, suave=False, tapas=False)
    _brida(c, V((1.85, y0 + 0.45, z0)), (0, 1, 0), r * 1.6, acero)
    # soporte de pared con abrazadera
    sx = -1.6
    c.caja((sx, 0.48, z0), (0.4, 0.06, 0.7), acero, 0.02)
    for dz in (-0.25, 0.25):
        c.perno((sx, 0.45, z0 + dz), (0, -1, 0), acero, r=0.035)
    c.caja((sx, 0.32, z0), (0.12, 0.3, 0.12), acero, 0.01)
    c.toro((sx, y0, z0), r + 0.03, 0.025, acero, n=14, m=4, rot=(0, 90, 0))
    for s in (-1, 1):
        c.caja((sx, s * (r + 0.06), z0), (0.06, 0.08, 0.06), acero, 0.005)
    # flecha de sentido pintada
    c.texto(">>", m.mat("pintura", "#E8E4D6", desgaste=0.3), alto=0.12, grosor=0.01, c=(-1.4, y0 - r - 0.002, z0 - 0.05),
            fuente="mono", resol=1)
    m.terminar()


# ==============================================================================================================
def chimenea_industrial():
    m = Modelo("chimenea_industrial", ZONA, (2, 2, 14), 8000,
               "Chimenea industrial de metal remachado: escalerilla de varillas con barandilla, plataforma de "
               "inspección a 2/3 con barandilla, sombrerete anti-lluvia, pararrayos y hollín bajando desde la boca.")
    c = m.parte()
    chapa = m.mat("metal", "#8E8A84", rug=0.55, hollin=(9.0, 13.4), lluvia=0.6, suciedad=0.6)
    acero = m.mat("metal", "#6E747A")
    osc = m.mat("metal", "#2A2D31", rug=0.6)
    amar = m.mat("pintura", "#D8A62A", desgaste=0.7)
    cobre = m.mat("metal", "#B26A3C", rug=0.4)
    horm = m.mat("hormigon", "#8E8A84")
    rojo = m.mat("pintura", "#B02A24", desgaste=0.5)
    blanco = m.mat("pintura", "#E6E4DC", desgaste=0.5)
    # pedestal y fuste (ligeramente cónico) con virolas remachadas
    c.caja((0, 0, 0.3), (2.0, 2.0, 0.6), horm, 0.06)
    c.torno([(0.0, 0.6), (0.82, 0.6), (0.82, 1.0), (0.72, 1.1), (0.6, 13.3), (0.0, 13.3)], chapa, n=20)
    for k in range(10):
        z = 1.6 + k * 1.2
        rr = 0.72 - (z - 1.1) / 12.2 * 0.12 + 0.012
        c.toro((0, 0, z), rr, 0.025, acero, n=20, m=4)
        for j in range(10):
            a = j * math.tau / 10 + (k % 2) * 0.3
            c.remache((math.cos(a) * rr, math.sin(a) * rr, z + 0.06), (math.cos(a), math.sin(a), 0), acero, 0.028)
    # franjas de señalización rojas y blancas arriba
    for k in range(2):
        z = 11.6 + k * 0.6
        c.cil((0, 0, z), (0, 0, z + 0.3), 0.63, rojo, n=20)
        c.cil((0, 0, z + 0.3), (0, 0, z + 0.6), 0.625, blanco, n=20)
    # boca y sombrerete anti-lluvia sobre 4 patas
    c.torno([(0.5, 13.3), (0.66, 13.3), (0.66, 13.45), (0.5, 13.45)], osc, n=20)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c.cil((math.cos(a) * 0.55, math.sin(a) * 0.55, 13.4), (math.cos(a) * 0.6, math.sin(a) * 0.6, 13.85), 0.03, osc, n=4)
    c.torno([(0.0, 14.05), (0.95, 13.8), (0.95, 13.75), (0.0, 13.95)], osc, n=16)
    # escalerilla lateral de varillas con barandilla (largueros que sobresalen)
    ex = 0.95
    for s in (-1, 1):
        c.cil((ex, s * 0.22, 0.6), (ex - 0.1, s * 0.22, 13.3), 0.03, amar, n=5)
    for k in range(int(12.4 / 0.33)):
        z = 0.9 + k * 0.33
        x = ex - 0.1 * (z - 0.6) / 12.7
        c.cil((x, -0.22, z), (x, 0.22, z), 0.016, amar, n=4)
    for z in (2.0, 5.0, 8.0, 11.0):
        x = ex - 0.1 * (z - 0.6) / 12.7
        for s in (-1, 1):
            c.cil((x, s * 0.22, z), (0.62, s * 0.22, z), 0.02, amar, n=4)
    # plataforma de inspección a 2/3 de altura con rejilla y barandilla
    zp = 9.4
    c.torno([(0.6, zp - 0.06), (1.25, zp - 0.06), (1.25, zp), (0.6, zp)], m.mat("grip", "#6E747A"), n=20)
    for k in range(6):
        a = k * math.tau / 6
        c.cil((math.cos(a) * 0.65, math.sin(a) * 0.65, zp - 0.6), (math.cos(a) * 1.2, math.sin(a) * 1.2, zp - 0.06), 0.03,
              amar, n=4)
    pts = [(math.cos(a) * 1.22, math.sin(a) * 1.22, zp) for a in [math.radians(20 + i * 32) for i in range(11)]]
    arq.barandilla(c, pts, 1.0, amar, r=0.03, n=5)
    # pararrayos: punta de cobre y bajante de cable con grapas
    c.cil((-0.45, 0.0, 13.0), (-0.45, 0.0, 15.0) if False else (-0.45, 0, 14.6), 0.02, cobre, n=5)
    c.cil((-0.45, 0, 14.6), (-0.45, 0, 14.9), 0.025, cobre, n=5, r1=0.0)
    pts = [(-0.45, 0, 13.0), (-0.62, 0.0, 12.8)] + [(-0.62 - (0.12 * (12.8 - z) / 12.2), 0.0, z) for z in (10.0, 5.0, 1.0)] + \
          [(-0.9, 0.0, 0.6), (-1.0, 0, 0.0)]
    c.tubo(pts, 0.015, cobre, n=4, seg=2)
    for z in (11.0, 8.0, 5.0, 2.0):
        c.caja((-0.62 - 0.12 * (12.8 - z) / 12.2, 0, z), (0.05, 0.05, 0.06), acero, 0.0)
    c.cil((-1.0, 0, -0.0), (-1.0, 0, 0.62), 0.02, cobre, n=4)
    m.terminar()


# ==============================================================================================================
def plataforma_elevacion():
    m = Modelo("plataforma_elevacion", ZONA, (4, 4, 0.5), 6000,
               "Plataforma elevadora: base con 4 pistones hidráulicos telescópicos, superficie de chapa de diamante, "
               "barandilla abatible en 3 lados y botonera con subir, bajar y seta de emergencia.")
    c = m.parte()
    sup = m.parte("plataforma", pivote=(0, 0, 0.5), nota="Lo que sube: superficie, barandillas y vástagos superiores. "
                                                       "Mover en Y de Roblox (hasta +6 studs).")
    barras = [m.parte(f"barandilla_{n}", pivote=p, nota="Barandilla abatible: gira 90° hacia fuera sobre su eje.")
              for n, p in (("izq", (1.9, 0, 0.6)), ("der", (-1.9, 0, 0.6)), ("tras", (0, 1.9, 0.6)))]
    base = m.mat("pintura", "#3A4048", desgaste=0.5)
    grip = m.mat("grip", "#8A9096")
    amar = m.mat("pintura", "#E2B030", desgaste=0.7)
    negro = m.mat("pintura", "#1E2024", desgaste=0.3)
    cromo = m.mat("cromo", "#D0D4D8")
    osc = m.mat("metal", "#2B2F34", rug=0.5)
    rojo = m.mat("plastico", "#D42A22")
    verde = m.mat("plastico", "#2EA04E")
    amarillo = m.mat("plastico", "#E8C02A")
    # foso / base enrasada y 4 pistones (cilindros telescópicos con juntas)
    c.caja((0, 0, 0.1), (4.0, 4.0, 0.2), base, 0.04)
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = V((sx * 1.4, sy * 1.4, 0.2))
            c.cil(p, p + V((0, 0, 0.18)), 0.22, osc, n=12)
            c.toro(p + V((0, 0, 0.18)), 0.2, 0.025, m.mat("goma", "#151618"), n=12, m=4)
            sup.cil(p + V((0, 0, 0.12)), p + V((0, 0, 0.26)), 0.16, cromo, n=12)
            sup.cil(p + V((0, 0, 0.12)), p + V((0, 0, 0.2)), 0.18, osc, n=12)
    # rayas de peligro en el borde de la base
    for k in range(10):
        c.caja((-1.8 + k * 0.4, -1.98, 0.2), (0.2, 0.05, 0.02), amar, 0.0, rot=(0, 0, 45))
    # superficie con chapa de diamante y canto amarillo
    sup.caja((0, 0, 0.42), (3.8, 3.8, 0.16), grip, 0.03)
    for s in (-1, 1):
        sup.caja((0, s * 1.88, 0.42), (3.8, 0.06, 0.17), amar, 0.01)
        sup.caja((s * 1.88, 0, 0.42), (0.06, 3.8, 0.17), amar, 0.01)
    # barandillas abatibles (izquierda, derecha y trasera), con bisagras en la base
    for parte, (eje, s) in zip(barras, (("X", 1), ("X", -1), ("Y", 1))):
        if eje == "X":
            pts = [(s * 1.82, -1.7, 0.5), (s * 1.82, 1.7, 0.5)]
        else:
            pts = [(-1.7, 1.82, 0.5), (1.7, 1.82, 0.5)]
        a, b = V(pts[0]), V(pts[1])
        for t in (0.0, 0.5, 1.0):
            q = a.lerp(b, t)
            parte.cil(q, q + V((0, 0, 1.1)), 0.035, amar, n=6)
            parte.cil(q - V((0.06, 0, 0)) if eje == "Y" else q - V((0, 0.06, 0)),
                      q + V((0.06, 0, 0)) if eje == "Y" else q + V((0, 0.06, 0)), 0.04, osc, n=6)
        parte.cil(a + V((0, 0, 1.1)), b + V((0, 0, 1.1)), 0.035, amar, n=6)
        parte.cil(a + V((0, 0, 0.6)), b + V((0, 0, 0.6)), 0.025, amar, n=5)
    # botonera en poste en la esquina delantera
    bp = V((1.6, -1.6, 0.5))
    sup.cil(bp, bp + V((0, 0, 1.0)), 0.04, osc, n=6)
    sup.caja(bp + V((0, 0, 1.15)), (0.3, 0.18, 0.4), amar, 0.03)
    for k, col in enumerate((verde, negro)):
        sup.cil(bp + V((0, -0.09, 1.25 - k * 0.14)), bp + V((0, -0.12, 1.25 - k * 0.14)), 0.05, col, n=10)
    sup.cil(bp + V((0, -0.09, 1.03)), bp + V((0, -0.11, 1.03)), 0.08, amarillo, n=12)  # aro amarillo
    sup.cil(bp + V((0, -0.11, 1.03)), bp + V((0, -0.16, 1.03)), 0.07, rojo, n=12)  # seta
    sup.esfera(bp + V((0, -0.16, 1.03)), 0.07, rojo, seg=10, anillos=4, esc=(1, 0.5, 1))
    sup.texto("▲", m.mat("pintura", "#F2F2F2", desgaste=0.0), alto=0.06, grosor=0.006, c=bp + V((0.09, -0.095, 1.23)),
              fuente="normal", resol=1)
    sup.tubo([bp + V((0.0, 0.08, 1.0)), bp + V((0.0, 0.12, 0.6)), bp + V((0.0, 0.1, 0.12))], 0.02,
             m.mat("goma", "#151618"), n=4, seg=2)
    m.notas.append("Tamaño plegada: 4 × 4 × 0,5 studs de base; las barandillas levantadas llegan a 1,9 studs.")
    m.terminar()


# ==============================================================================================================
def deposito_minerales():
    m = Modelo("deposito_minerales", ZONA, (4, 3, 2), 5000,
               "Contenedor abierto reforzado para minerales: chapa gruesa con 4 costillas exteriores, lleno de "
               "piedras 3D de colores y tamaños, asas de tubo a los lados y chapa de identificación.")
    c = m.parte()
    brillo = m.parte("cristales_neon", tipo="neon", color=NEON, nota="Cristales azules entre la carga.")
    chapa = m.mat("pintura", "#B4652A", desgaste=0.75, abolladuras=0.6, c_desgaste="#5E544C")
    acero = m.mat("metal", "#6E747A")
    placa = m.mat("metal", "#B8BCC0", rug=0.3)
    tinta = m.mat("pintura", "#1E2226", desgaste=0.0)
    mats = [m.mat("piedra", h) for h in ("#7A7672", "#5E5A56", "#8A7A62")] + [m.mat("organico", "#D8902A", rug=0.3),
                                                                            m.mat("piedra", "#4E6E58")]
    W, D, H, G = 4.0, 3.0, 1.7, 0.18
    # cuba de chapa gruesa (fondo + 4 paredes con grosor real)
    c.caja((0, 0, 0.18), (W, D, 0.2), chapa, 0.03)
    for s in (-1, 1):
        c.caja((0, s * (D / 2 - G / 2), H / 2 + 0.1), (W, G, H - 0.2), chapa, 0.03)
        c.caja((s * (W / 2 - G / 2), 0, H / 2 + 0.1), (G, D - 2 * G, H - 0.2), chapa, 0.03)
    for s in (-1, 1):
        c.caja((0, s * (D / 2 + 0.02), H - 0.06), (W + 0.06, 0.1, 0.12), acero, 0.02)
        c.caja((s * (W / 2 + 0.02), 0, H - 0.06), (0.1, D + 0.06, 0.12), acero, 0.02)
    # 4 costillas verticales en cada cara larga y patines de apoyo
    for s in (-1, 1):
        for k in range(4):
            x = -1.35 + k * 0.9
            c.caja((x, s * (D / 2 + 0.06), H / 2), (0.14, 0.12, H - 0.1), acero, 0.02)
        c.caja((s * 1.4, 0, 0.04), (0.3, D, 0.08), acero, 0.01)
    # asas de tubo curvado en los laterales cortos
    for s in (-1, 1):
        c.tubo([(s * (W / 2), -0.5, 1.2), (s * (W / 2 + 0.25), -0.45, 1.25), (s * (W / 2 + 0.3), 0, 1.3),
                (s * (W / 2 + 0.25), 0.45, 1.25), (s * (W / 2), 0.5, 1.2)], 0.05, acero, n=6, seg=3)
    # chapa de identificación remachada
    c.caja((-1.0, -D / 2 - 0.13, 1.05), (0.8, 0.02, 0.4), placa, 0.005)
    for (dx, dz) in ((-0.35, 0.15), (0.35, 0.15), (-0.35, -0.15), (0.35, -0.15)):
        c.remache((-1.0 + dx, -D / 2 - 0.14, 1.05 + dz), (0, -1, 0), acero, 0.025)
    c.texto("MIN-0732", tinta, alto=0.12, grosor=0.008, c=(-1.0, -D / 2 - 0.145, 0.98), fuente="mono", resol=1)
    # carga de piedras (rellena hasta formar un montón) y algunos cristales
    rnd = m.rnd
    for i in range(34):
        x = rnd.uniform(-1.6, 1.6)
        y = rnd.uniform(-1.1, 1.1)
        r = rnd.uniform(0.18, 0.38)
        z = H - 0.35 + 0.35 * (1 - (x / 1.8) ** 2) * (1 - (y / 1.3) ** 2) + rnd.uniform(-0.05, 0.1)
        c.roca((x, y, z), r, mats[i % 5], semilla=i, ruido=0.3)
    for i in range(5):
        x, y = rnd.uniform(-1.3, 1.3), rnd.uniform(-0.8, 0.8)
        z = H - 0.05
        d = V((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 1)).normalized()
        c.cil((x, y, z), V((x, y, z)) + d * 0.5, 0.1, m.mat("organico", "#3A7FC4", rug=0.2), n=6, r1=0.0)
        brillo.cil(V((x, y, z + 0.02)), V((x, y, z)) + d * 0.4, 0.05, None, n=5, r1=0.0)
    m.terminar()


# ==============================================================================================================
def prensa_hidraulica():
    m = Modelo("prensa_hidraulica", ZONA, (3, 2, 4), 5000,
               "Prensa hidráulica: marco en C de acero grueso, pistón vertical con cilindro, mesa con guías, dos "
               "mangueras hidráulicas, panel lateral con manómetro circular y pedal de accionamiento.")
    c = m.parte()
    piston = m.parte("piston", pivote=(0, 0, 2.6), nota="Vástago y cabezal: bajan hasta 0,9 studs (mover en Y de "
                                                       "Roblox).")
    pedal = m.parte("pedal", pivote=(0.9, -0.7, 0.1), nota="Pedal: gira 15° hacia abajo.")
    marco = m.mat("pintura", "#2E5A8A", desgaste=0.6, abolladuras=0.3)
    acero = m.mat("metal", "#80868C")
    cromo = m.mat("cromo", "#D2D6DA")
    osc = m.mat("metal", "#2A2E33", rug=0.5)
    goma = m.mat("goma", "#151618")
    amar = m.mat("pintura", "#E2B030", desgaste=0.6)
    blanco = m.mat("plastico", "#F2EFE6")
    tinta = m.mat("pintura", "#1A1C1E", desgaste=0.0)
    rojo = m.mat("pintura", "#C02A22", desgaste=0.0)
    # marco en C (perfil extruido de chapa gruesa, dos placas con separadores)
    perfil_c = [(-0.2, 0.0), (0.9, 0.0), (0.9, 0.35), (0.3, 0.4), (0.3, 3.0), (0.9, 3.0), (0.9, 3.9), (-0.6, 3.9),
                (-0.7, 3.5), (-0.7, 0.4)]
    for s in (-1, 1):
        c.extruir([(y, z) for y, z in perfil_c], 0.16, marco, c=(s * 0.4, 0.3, 0), rot=(90, 0, 90), b=0.03)
    c.caja((0, 0.9, 1.9), (0.64, 0.12, 3.0), marco, 0.03)
    c.caja((0, 0.3, 0.12), (1.6, 1.8, 0.24), osc, 0.04)  # bancada
    # mesa de prensado con guías en T
    c.caja((0, -0.25, 0.55), (1.0, 0.9, 0.3), acero, 0.03)
    for k in range(3):
        c.caja((-0.3 + k * 0.3, -0.25, 0.71), (0.06, 0.88, 0.03), osc, 0.0)
    for s in (-1, 1):
        c.cil((s * 0.42, -0.6, 0.7), (s * 0.42, -0.6, 3.1), 0.035, cromo, n=8)  # columnas guía
    # cilindro hidráulico en la cabeza del marco
    c.cil((0, -0.25, 3.0), (0, -0.25, 3.9), 0.3, osc, n=14)
    for zz in (3.05, 3.85):
        c.cil((0, -0.25, zz - 0.04), (0, -0.25, zz + 0.04), 0.35, osc, n=14)
        for k in range(6):
            a = k * math.tau / 6
            c.perno((math.cos(a) * 0.32, -0.25 + math.sin(a) * 0.32, zz + 0.04), (0, 0, 1), acero, r=0.03)
    # pistón (pieza aparte): vástago cromado, cabezal y placa
    piston.cil((0, -0.25, 3.0), (0, -0.25, 2.0), 0.12, cromo, n=12)
    piston.cil((0, -0.25, 2.0), (0, -0.25, 1.85), 0.34, acero, n=14)
    piston.caja((0, -0.25, 1.78), (0.8, 0.7, 0.1), acero, 0.02)
    for s in (-1, 1):
        piston.cil((s * 0.42, -0.6, 1.72), (s * 0.42, -0.6, 1.88), 0.07, osc, n=8)
    # mangueras hidráulicas con racores
    for k, dz in enumerate((3.25, 3.65)):
        a = V((0.3, -0.25, dz))
        c.cil(a, a + V((0.12, 0, 0)), 0.05, acero, n=6)
        c.tubo([a + V((0.12, 0, 0)), a + V((0.45, -0.05 * k, -0.2)), V((0.95, 0.1 + 0.15 * k, 2.4)), V((1.1, 0.2 + 0.15 * k, 1.6))],
               0.04, goma, n=6, seg=3)
    # panel de control lateral con manómetro
    pc = V((1.15, 0.2, 1.4))
    c.caja(pc, (0.25, 0.5, 0.9), amar, 0.04)
    c.cil((pc.x - 0.1, pc.y, 0.24), (pc.x - 0.1, pc.y, pc.z - 0.45), 0.05, osc, n=6)
    c.cil(pc + V((0.13, 0, 0.18)), pc + V((0.2, 0, 0.18)), 0.17, acero, n=16)
    c.cil(pc + V((0.2, 0, 0.18)), pc + V((0.21, 0, 0.18)), 0.15, blanco, n=16)
    for k in range(9):
        a = math.radians(-135 + k * 33.75)
        c.caja(pc + V((0.215, math.cos(a) * 0.12, 0.18 + math.sin(a) * 0.12)), (0.005, 0.01, 0.025), tinta, 0.0,
               rot=(math.degrees(a), 0, 0))
    c.caja(pc + V((0.215, 0.0, 0.18 + 0.05)), (0.006, 0.012, 0.11), rojo, 0.0, rot=(-35, 0, 0))  # aguja
    c.cil(pc + V((0.21, 0, 0.18)), pc + V((0.23, 0, 0.18)), 0.02, osc, n=6)
    for k, col in enumerate((m.mat("plastico", "#2EA04E"), m.mat("plastico", "#D42A22"))):
        c.cil(pc + V((0.13, -0.12 + k * 0.24, -0.2)), pc + V((0.17, -0.12 + k * 0.24, -0.2)), 0.05, col, n=10)
    # pedal de accionamiento con cable
    pedal.caja((0.9, -0.85, 0.1), (0.35, 0.45, 0.1), osc, 0.03)
    pedal.caja((0.9, -0.92, 0.16), (0.3, 0.3, 0.02), m.mat("grip", "#6E747A"), 0.0)
    c.caja((0.9, -0.55, 0.09), (0.4, 0.2, 0.18), osc, 0.02)
    c.tubo([(0.9, -0.45, 0.12), (1.0, -0.2, 0.05), (1.1, 0.1, 0.05), (1.15, 0.2, 0.95)], 0.025, goma, n=5, seg=3)
    m.terminar()


# ==============================================================================================================
def almacen_industrial():
    m = Modelo("almacen_industrial", ZONA, (16, 12, 8), 14000,
               "Almacén industrial tipo quonset: chapa ondulada en bóveda, puerta corredera grande sobre raíl y "
               "ruedas, puerta peatonal con cerradura, estanterías y palé con cajas a la vista, canalón, ventilador "
               "de techo y tubos fluorescentes.")
    c = m.parte()
    puerta = m.parte("puerta", pivote=(-1.5, -6.15, 0.3), nota="Puerta corredera: abrir desplazándola 5,8 studs a la "
                                                               "derecha del modelo (-X de Roblox) sobre el raíl.")
    peatonal = m.parte("puerta_peatonal", pivote=(4.35, -5.95, 0.3), nota="Puerta peatonal batiente: gira sobre su "
                                                                          "bisagra.")
    luces = m.parte("fluorescentes_neon", tipo="neon", color="#E6F7FF", nota="Tubos fluorescentes: Neon blanco frío.")
    helice = m.parte("ventilador", pivote=(0, 1.0, 7.0), nota="Aspas del ventilador: girar sobre el eje vertical.")
    chapa = m.mat("metal", "#9AA1A6", rug=0.5, lluvia=0.7, suciedad=0.6, aranazos=0.2)
    chapa_p = m.mat("pintura", "#2F6A6E", desgaste=0.6, lluvia=0.6)
    horm = m.mat("hormigon", "#8E8A82", manchas=[(-3.0, -7.0, 0.2, 1.2, "#14110e", 0.6)])
    acero = m.mat("metal", "#6E747A")
    osc = m.mat("metal", "#2B2F34", rug=0.5)
    amar = m.mat("pintura", "#E2B030", desgaste=0.6)
    madera = m.mat("madera", "#A88050", eje="X")
    carton = m.mat("papel", "#B08A5C")
    cajas = [m.mat("pintura", h, desgaste=0.5) for h in ("#4E6E8A", "#8A4E3A", "#5E7A4E")]
    R = 6.0  # radio de la bóveda (ancho 12 en X... la bóveda corre a lo largo de Y)
    X0, X1 = -7.8, 7.8
    YF, YB = -5.9, 5.9
    Z0 = 0.3
    c.caja((0, -0.7, 0.15), (16.0, 13.4, 0.3), horm, 0.05)
    m.seccion("bóveda de chapa ondulada")
    # semicírculo achatado: ancho 15,6 (X), alto 7,4. La onda corre a lo largo del arco.
    def arco(u):
        a = math.pi * u
        return (-math.cos(a) * (X1 - 0.1), Z0 + math.sin(a) * 7.4)
    def boveda(u, v):
        x, z = arco(u)
        nx, nz = -math.cos(math.pi * u), math.sin(math.pi * u)
        onda = 0.07 * math.sin(v * (YB - YF) / 0.45 * math.tau)
        return (x + nx * onda, YF + v * (YB - YF), z + nz * onda)
    c.lamina(boveda, 22, 52, 0.05, chapa)
    # arcos de estructura en H (vistos desde dentro y en las cabezas)
    for y in (YF + 0.05, 0.0, YB - 0.05):
        pts = [(arco(i / 16)[0] * 0.985, y, arco(i / 16)[1] * 0.985 + 0.0) for i in range(17)]
        c.tubo(pts, 0.12, osc, n=6, suave=False)
    # muros frontal y trasero (hastiales) de chapa pintada con los huecos
    PUE = (-4.5, 1.5, Z0, 5.0)
    PEA = (3.2, 4.4, Z0, 3.6)
    def hastial(y, huecos):
        pts = [arco(i / 20) for i in range(21)]
        # se trocea en franjas verticales para dejar los huecos
        xs = sorted({X0 + 0.1, X1 - 0.1} | {h[0] for h in huecos} | {h[1] for h in huecos})
        for xa, xb in zip(xs, xs[1:]):
            def alto(x):
                t = math.acos(max(-1, min(1, -x / (X1 - 0.1)))) / math.pi
                return arco(t)[1] - 0.05
            hueco = next((h for h in huecos if h[0] <= xa and xb <= h[1]), None)
            zb = hueco[3] if hueco else Z0
            n = 3
            perfil = [(xa, zb), (xb, zb)] + [(xb - (xb - xa) * k / n, alto(xb - (xb - xa) * k / n)) for k in range(n + 1)]
            c.extruir(perfil, 0.12, chapa_p, c=(0, y, 0), rot=(90, 0, 0))
    hastial(YF + 0.06, [PUE, PEA])
    hastial(YB - 0.06, [])
    m.seccion("puerta corredera y peatonal")
    px0, px1, pz0, pz1 = PUE
    c.caja_de((px0 - 0.2, YF - 0.25, pz1), (px1 + 6.2, YF - 0.05, pz1 + 0.3), osc, 0.02)  # raíl
    for x in (px0, px1 + 3.0, px1 + 6.0):
        c.caja((x, YF - 0.1, pz1 + 0.15), (0.15, 0.15, 0.45), osc, 0.01)
    c.caja_de((px0 - 0.2, YF - 0.3, Z0 - 0.02), (px1 + 6.2, YF - 0.2, Z0 + 0.05), acero)
    hx0 = px0 - 0.1
    W = px1 - px0 + 0.2
    # hoja de chapa ondulada vertical en bastidor
    puerta.lamina(lambda u, v: (hx0 + 0.1 + u * (W - 0.2), YF - 0.28 + 0.05 * math.sin(u * (W - 0.2) / 0.4 * math.tau),
                                pz0 + 0.15 + v * (pz1 - pz0 - 0.2)), 60, 1, 0.04, chapa_p)
    for (a, b) in (((hx0, pz0 + 0.05), (hx0 + W, pz0 + 0.2)), ((hx0, pz1 - 0.15), (hx0 + W, pz1)),
                   ((hx0, pz0), (hx0 + 0.15, pz1)), ((hx0 + W - 0.15, pz0), (hx0 + W, pz1))):
        puerta.caja_de((a[0], YF - 0.36, a[1]), (b[0], YF - 0.2, b[1]), osc, 0.02)
    puerta.cil((hx0 + 0.15, YF - 0.37, pz0 + 0.2), (hx0 + W - 0.15, YF - 0.37, pz1 - 0.2), 0.04, osc, n=4)  # tirante
    for x in (hx0 + 0.6, hx0 + W - 0.6):
        puerta.cil((x, YF - 0.33, pz1 + 0.15), (x, YF - 0.17, pz1 + 0.15), 0.12, acero, n=10)  # ruedas al raíl
        puerta.caja((x, YF - 0.25, pz1 + 0.03), (0.1, 0.06, 0.25), acero, 0.01)
        puerta.cil((x, YF - 0.33, pz0 + 0.05), (x, YF - 0.17, pz0 + 0.05), 0.08, osc, n=8)
    puerta.tubo([(hx0 + W - 0.4, YF - 0.37, 2.9), (hx0 + W - 0.4, YF - 0.55, 2.9), (hx0 + W - 0.4, YF - 0.55, 2.1),
                 (hx0 + W - 0.4, YF - 0.37, 2.1)], 0.05, amar, n=6, seg=2)
    # puerta peatonal con cerradura y marco
    qx0, qx1, qz0, qz1 = PEA
    arq.marco(c, qx0, qx1, qz0, qz1, YF, 0.1, 0.1, osc, abajo=False)
    peatonal.caja_de((qx0 + 0.02, YF - 0.04, qz0), (qx1 - 0.02, YF + 0.04, qz1 - 0.02), amar, 0.03)
    peatonal.caja_de((qx0 + 0.25, YF - 0.06, qz0 + 1.8), (qx1 - 0.25, YF - 0.04, qz1 - 0.3), osc, 0.01)
    peatonal.caja((qx1 - 0.2, YF - 0.06, qz0 + 1.55), (0.1, 0.05, 0.35), acero, 0.01)  # escudo de la cerradura
    peatonal.cil((qx1 - 0.2, YF - 0.09, qz0 + 1.62), (qx1 - 0.4, YF - 0.13, qz0 + 1.62), 0.025, acero, n=6)
    peatonal.cil((qx1 - 0.2, YF - 0.09, qz0 + 1.47), (qx1 - 0.2, YF - 0.1, qz0 + 1.47), 0.02, osc, n=6)
    for zz in (qz0 + 0.4, qz1 - 0.5):
        peatonal.cil((qx1 - 0.02 - (qx1 - qx0) + 0.04, YF, zz - 0.1), (qx0 + 0.02, YF, zz + 0.1), 0.035, acero, n=6)
    m.seccion("interior")
    # estanterías metálicas con cajas al fondo y palé con cajas
    for k, x in enumerate((-5.0, -1.5)):
        for s in (-1, 1):
            for yy in (2.8, 4.0):
                c.caja((x + s * 1.45, yy, 2.0), (0.08, 0.08, 4.0), amar, 0.0)
        for z in (0.5, 1.7, 2.9):
            c.caja((x, 3.4, z), (3.0, 1.3, 0.06), acero, 0.0)
            for j in range(3):
                col = cajas[(j + k) % 3] if j % 2 else carton
                c.caja((x - 0.95 + j * 0.95, 3.4, z + 0.33), (0.8, 1.0, 0.6), col, 0.03)
    # palé con cajas atadas
    c.caja((-2.0, -1.8, Z0 + 0.06), (2.0, 1.6, 0.12), madera, 0.01)
    for k in range(3):
        c.caja((-2.0, -2.5 + k * 0.7, Z0 + 0.2), (2.0, 0.15, 0.16), madera, 0.01)
    for (dx, dy, dz) in ((-0.5, -0.4, 0), (0.5, -0.4, 0), (-0.5, 0.4, 0), (0.5, 0.4, 0), (0.0, 0.0, 0.8)):
        c.caja((-2.0 + dx, -1.8 + dy, Z0 + 0.72 + dz), (0.9, 0.75, 0.8), carton, 0.03)
    # fluorescentes colgados y ventilador de techo industrial
    for y in (-3.5, -0.5, 2.5):
        for x in (-3.0, 3.0):
            c.cil((x, y, 6.85), (x, y, 6.0), 0.01, osc, n=4)
            c.caja((x, y, 5.95), (2.0, 0.25, 0.1), acero, 0.02)
            luces.cil((x - 0.9, y, 5.87), (x + 0.9, y, 5.87), 0.035, None, n=6)
    c.cil((0, 1.0, 7.65), (0, 1.0, 7.05), 0.06, osc, n=6)
    c.cil((0, 1.0, 7.05), (0, 1.0, 6.85), 0.25, osc, n=12)
    for k in range(5):
        a = k * math.tau / 5
        helice.caja((math.cos(a) * 0.9, 1.0 + math.sin(a) * 0.9, 6.8), (1.4, 0.25, 0.03), acero, 0.01,
                    rot=(8, 0, math.degrees(a)))
    m.seccion("canalón y detalles")
    for s in (-1, 1):
        x = s * (X1 + 0.05)
    # canalón longitudinal a media caída (lado +X) y bajantes
    zc = Z0 + 2.6
    xc = (X1 - 0.1) * math.cos(math.asin((zc - Z0) / 7.4)) + 0.15
    c.caja_de((xc - 0.15, YF - 0.1, zc - 0.15), (xc + 0.15, YB + 0.1, zc + 0.05), acero, 0.02)
    for y in (YF + 0.4, YB - 0.4):
        c.tubo([(xc, y, zc - 0.15), (xc + 0.15, y, zc - 0.5), (xc + 0.15, y, 0.5), (xc + 0.4, y, 0.32)], 0.09, acero, n=6,
               seg=2)
    # cartel pintado y número de nave
    c.caja((-1.5, YF - 0.1, 5.6), (3.0, 0.06, 0.7), amar, 0.02)
    c.texto("NAVE 3", osc, alto=0.42, grosor=0.02, c=(-1.5, YF - 0.14, 5.4), fuente="estrecha", resol=1)
    arq.foco_pared(c, luces, (PEA[1] + 0.6, YF - 0.06, 4.0), osc, acero, tam=0.35)
    m.terminar()


MODELOS = {
    "cinta_transportadora": cinta_transportadora,
    "tanque_combustible": tanque_combustible,
    "silo_almacen": silo_almacen,
    "tuberia_modular": tuberia_modular,
    "chimenea_industrial": chimenea_industrial,
    "plataforma_elevacion": plataforma_elevacion,
    "deposito_minerales": deposito_minerales,
    "prensa_hidraulica": prensa_hidraulica,
    "almacen_industrial": almacen_industrial,
}
