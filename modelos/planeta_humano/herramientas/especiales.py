"""Edificios especiales (1): centro de mando, laboratorio y academia de entrenamiento."""

import math
import random

import arq
from ph import NEON, V, Modelo

ZONA = "especiales"
VERDE_DESCONTAMINACION = "#39FF14"
TEXTO_HOLO = "#E8FEFF"


def _bandera(parte, mx, my, z0, mats, ancho=1.6, alto=1.0):
    """Bandera de la colonia: tela ondulada con grosor (azul) y emblema (anillo cyan y estrella blanca) a ambos lados."""
    azul, cyan, blanco = mats
    parte.lamina(lambda u, v: (mx - 0.05 - u * ancho, my + 0.14 * math.sin(u * 4.5 + 0.5) * u, z0 + v * alto - 0.08 * u),
                 10, 2, 0.03, azul)
    u = 0.5
    cx = mx - 0.05 - u * ancho
    cy = my + 0.14 * math.sin(u * 4.5 + 0.5) * u
    with parte.en((cx, cy, z0 + alto / 2 - 0.04), (90, 0, 0)):
        parte.toro((0, 0, 0), alto * 0.25, 0.025, cyan, n=14, m=3)
        estrella = []
        for k in range(10):
            a = math.pi / 2 + k * math.pi / 5
            r = alto * 0.16 if k % 2 == 0 else alto * 0.07
            estrella.append((math.cos(a) * r, math.sin(a) * r))
        parte.extruir(estrella, 0.08, blanco)


def _emblema(c, mat, centro, r, rot=(90, 0, 0), grosor=0.05):
    """Emblema de la colonia en relieve: anillo, estrella de 5 puntas y órbita inclinada."""
    with c.en(centro, rot):
        c.toro((0, 0, 0), r, r * 0.09, mat, n=20, m=4)
        estrella = [(math.cos(math.pi / 2 + k * math.pi / 5) * (r * 0.62 if k % 2 == 0 else r * 0.26),
                     math.sin(math.pi / 2 + k * math.pi / 5) * (r * 0.62 if k % 2 == 0 else r * 0.26)) for k in range(10)]
        c.extruir(estrella, grosor, mat)
        with c.en((0, 0, 0), (0, 0, 25)):
            c.toro((0, 0, 0.0), r * 0.82, r * 0.035, mat, n=20, m=3, rot=(65, 0, 0))


# ==============================================================================================================
def centro_mando():
    m = Modelo("centro_mando", ZONA, (18, 16, 12), 18000,
               "Centro de mando de la colonia Nueva Esperanza: cúpula geodésica parcial con juntas metálicas, pórtico "
               "de 4 columnas estriadas, escalinata de 6 peldaños, puertas dobles con el emblema en relieve, pantallas "
               "holográficas con datos, 3 tipos de antena, mástil con bandera, 4 focos, placa de fundación y jardín "
               "formal con setos recortados.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#9EC6D6", transparencia=0.35)
    holo = m.parte("holo_neon", tipo="neon", color=NEON, transparencia=0.6, nota="Fondo de las pantallas holográficas.")
    datos = m.parte("datos_neon", tipo="neon", color=TEXTO_HOLO, nota="Datos de las pantallas (gráficas y barras).")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    bandera = m.parte("bandera", pivote=(8.2, -6.2, 9.4), nota="Bandera de la colonia: tela aparte.")
    blanco = m.mat("paneles", "#E4E6E8", tam_panel=(2.0, 1.6), desgaste=0.3, c_desgaste="#8A9097", lluvia=0.4)
    piedra = m.mat("piedra", "#C8C0B0", escala=0.7, rug=0.6)
    marmol = m.mat("piedra", "#DCD6CA", escala=0.5, rug=0.45)
    gris = m.mat("pintura", "#3E4650", desgaste=0.4)
    acero = m.mat("metal", "#8A9097")
    osc = m.mat("metal", "#2B3035", rug=0.45)
    cromo = m.mat("cromo", "#D2D6DA")
    oro = m.mat("metal", "#C9A040", rug=0.25)
    seto = m.mat("organico", "#3A6E34", rug=0.8, bump=1.0, patron="poros", escala=2.0)
    seto2 = m.mat("organico", "#2E5E2E", rug=0.8, bump=1.0, patron="poros", escala=2.0)
    tierra = m.mat("piedra", "#4E3E2E", bump=0.6, escala=1.6)
    flores = [m.mat("organico", h, rug=0.5) for h in ("#E8D24A", "#D84A5A", "#F0F0F0")]
    azul_t = m.mat("tela", "#1D3E7A", suciedad=0.1)
    cyan_t = m.mat("tela", "#3DC8D8", suciedad=0.1)
    blanco_t = m.mat("tela", "#F0EEE6", suciedad=0.1)

    X0, X1, YF, YB = -7.0, 7.0, -2.0, 7.4
    Z0 = 1.2  # basamento (6 peldaños de 0,2)
    ZT = Z0 + 7.0

    m.seccion("basamento y escalinata")
    c.caja_de((-9.0, YF - 3.0, 0), (9.0, YB + 0.4, 0.12), piedra, 0.03)  # explanada
    c.caja_de((X0 - 0.6, YF - 1.2, 0), (X1 + 0.6, YB + 0.3, Z0), piedra, 0.05)
    arq.escalones(c, X0 - 0.6, X1 + 0.6, YF - 4.6, 0.0, 6, 0.57, Z0 / 6, marmol, mat_borde=acero)
    m.seccion("cuerpo")
    PUE = (-1.8, 1.8, Z0, 5.6)
    arq.muro_huecos(c, X0, X1, Z0, ZT, YF, YF + 0.5, [PUE, (-6.2, -3.4, 2.6, 6.4), (3.4, 6.2, 2.6, 6.4)], blanco)
    for x in (X0, X1 - 0.5):
        c.caja_de((x, YF + 0.5, Z0), (x + 0.5, YB - 0.5, ZT), blanco)
    c.caja_de((X0, YB - 0.5, Z0), (X1, YB, ZT), blanco)
    for (x0, x1) in ((-6.2, -3.4), (3.4, 6.2)):  # ventanales con montantes
        arq.marco(c, x0, x1, 2.6, 6.4, YF, 0.15, 0.15, gris)
        cr.caja_de((x0, YF + 0.1, 2.6), (x1, YF + 0.2, 6.4), None)
        for k in (1, 2):
            x = x0 + k * (x1 - x0) / 3
            c.caja_de((x - 0.05, YF - 0.03, 2.6), (x + 0.05, YF + 0.12, 6.4), gris, 0.01)
    # cornisa y friso
    c.caja_de((X0 - 0.4, YF - 0.4, ZT), (X1 + 0.4, YB + 0.4, ZT + 0.35), marmol, 0.06)
    c.caja_de((X0 - 0.2, YF - 0.2, ZT + 0.35), (X1 + 0.2, YB + 0.2, ZT + 0.65), gris, 0.04)
    m.seccion("pórtico con columnas")
    c.caja_de((-4.2, YF - 2.6, ZT - 0.6), (4.2, YF, ZT - 0.05), marmol, 0.06)  # dintel del pórtico
    c.extruir([(-4.4, 0), (4.4, 0), (0, 1.3)], 0.5, marmol, c=(0, YF - 2.35, ZT - 0.05), rot=(90, 0, 0))  # frontón
    _emblema(c, oro, (0, YF - 2.62, ZT + 0.45), 0.42)
    for x in (-3.4, -1.2, 1.2, 3.4):
        y = YF - 2.1
        c.cil((x, y, Z0), (x, y, Z0 + 0.3), 0.55, marmol, n=12, b=0.03)  # basa
        c.tubo([(x, y, Z0 + 0.3), (x, y, ZT - 0.9)], 0.42, marmol, n=16, suave=False, surcos=8, prof=0.1, r_fin=0.38)
        c.cil((x, y, ZT - 0.9), (x, y, ZT - 0.6), 0.38, marmol, n=12, r1=0.55)  # capitel
    m.seccion("puertas con emblema")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF, 0.3, 0.25, gris, abajo=False)
    for lado, (hx0, s) in {"izq": (px0, 1), "der": (px1, -1)}.items():
        w = (px1 - px0) / 2
        pv = (hx0, YF + 0.15, pz0)
        h = m.parte(f"puerta_{lado}", pivote=pv, nota="Hoja de la puerta principal: gira hacia dentro sobre su bisagra.")
        xa, xb = sorted((hx0, hx0 + s * w))
        h.caja_de((xa, YF + 0.05, pz0), (xb, YF + 0.25, pz1), m.mat("metal", "#5A6A7A", rug=0.35, aranazos=0.3), 0.04)
        for zz in (pz0 + 0.5, pz1 - 0.5):
            h.caja_de((xa + 0.1, YF + 0.02, zz - 0.05), (xb - 0.1, YF + 0.05, zz + 0.05), oro, 0.01)
        h.cil((hx0 + s * (w - 0.25), YF - 0.05, pz0 + 1.6), (hx0 + s * (w - 0.25), YF - 0.05, pz0 + 2.9), 0.04, oro, n=8)
        # medio emblema en cada hoja (al cerrarse se ve entero)
        with h.en(((px0 + px1) / 2, YF + 0.03, pz0 + 2.9), (90, 0, 0)):
            h.toro((0, 0, 0), 0.7, 0.07, oro, n=20, m=4, arco=180 if lado == "der" else 180, rot=(0, 0, 90 if lado == "izq"
                                                                                                   else -90))
    _emblema(c, oro, ((px0 + px1) / 2, YF - 0.02, pz0 + 2.9), 0.55, grosor=0.06)
    m.seccion("pantallas holográficas")
    for x in (-4.8, 4.8):
        c.caja((x, YF - 0.1, ZT - 1.0), (2.3, 0.12, 1.1), osc, 0.03)
        holo.caja((x, YF - 0.2, ZT - 1.0), (2.1, 0.03, 0.95), None)
        for k in range(5):  # gráfica de barras
            hgt = (0.3, 0.55, 0.42, 0.7, 0.5)[k]
            datos.caja((x - 0.8 + k * 0.22, YF - 0.23, ZT - 1.4 + hgt / 2), (0.14, 0.02, hgt), None)
        datos.tubo([(x + 0.2, YF - 0.23, ZT - 1.2), (x + 0.45, YF - 0.23, ZT - 0.9), (x + 0.7, YF - 0.23, ZT - 1.05),
                    (x + 0.95, YF - 0.23, ZT - 0.7)], 0.015, None, n=3, suave=False)
        datos.caja((x + 0.55, YF - 0.23, ZT - 0.62), (0.7, 0.02, 0.05), None)
    m.seccion("cúpula geodésica")
    # media icosfera (2 subdivisiones): cada triángulo es un panel con grosor (cristal o metal) y cada arista, una junta
    import bmesh
    from mathutils import Matrix
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=3.4)
    cz = ZT + 0.65
    dc = V((0, 2.6, cz))
    aristas = set()
    for f in bm.faces:
        cen = f.calc_center_median()
        if cen.z < 0.25:
            continue
        pts = [V(v.co) for v in f.verts]
        n = f.normal
        inset = [cen + (p - cen) * 0.88 for p in pts]
        mat_panel = cr if (abs(int(cen.x * 3 + cen.y * 2)) % 3) else c
        if mat_panel is cr:
            cr.loft([[dc + p for p in inset], [dc + p - n * 0.06 for p in inset]], None)
        else:
            c.loft([[dc + p for p in inset], [dc + p - n * 0.08 for p in inset]], blanco)
        for e in f.edges:
            a, b = e.verts
            if a.co.z >= -0.05 and b.co.z >= -0.05:
                aristas.add(tuple(sorted((tuple(round(x, 4) for x in a.co), tuple(round(x, 4) for x in b.co)))))
    bm.free()
    for a, b in aristas:
        c.cil(dc + V(a), dc + V(b), 0.05, acero, n=4)
    c.cil(dc + V((0, 0, -0.05)), dc + V((0, 0, 0.12)), 3.5, gris, n=20)  # anillo de arranque
    m.seccion("antenas")
    # 1) mástil de celosía
    ax, ay = -5.2, 5.0
    for s in ((-0.2, -0.2), (0.2, -0.2), (0.0, 0.2)):
        c.cil((ax + s[0], ay + s[1], ZT + 0.65), (ax, ay, ZT + 3.5), 0.035, acero, n=4)
    for k in range(4):
        z = ZT + 1.0 + k * 0.6
        c.cil((ax - 0.15, ay, z), (ax + 0.15, ay, z), 0.02, acero, n=4)
    luces.esfera((ax, ay, ZT + 3.6), 0.07, None, seg=8, anillos=5)
    # 2) látigo con base
    c.cil((5.6, 5.2, ZT + 0.65), (5.6, 5.2, ZT + 1.0), 0.15, osc, n=8)
    c.cil((5.6, 5.2, ZT + 1.0), (5.6, 5.2, ZT + 3.2), 0.02, acero, n=4)
    # 3) parabólica pequeña
    with c.en((5.0, 1.5, ZT + 1.25), (0, 35, 30)):
        c.torno([(0.0, 0.0), (0.4, 0.07), (0.6, 0.18), (0.62, 0.21), (0.58, 0.21), (0.38, 0.11), (0.0, 0.04)], blanco, n=14)
        c.cil((0, 0, 0.0), (0, 0, 0.6), 0.02, acero, n=4)
    c.cil((5.0, 1.5, ZT + 0.65), (5.0, 1.5, ZT + 1.2), 0.06, acero, n=6)
    m.seccion("bandera, focos, placa")
    mx, my = 8.2, -6.2
    c.cil((mx, my, 0.12), (mx, my, 10.6), 0.07, acero, n=8)
    c.cil((mx, my, 0.12), (mx, my, 0.4), 0.25, piedra, n=8)
    c.esfera((mx, my, 10.68), 0.1, oro, seg=8, anillos=5)
    _bandera(bandera, mx, my, 9.4, (azul_t, cyan_t, blanco_t))
    for x in (-7.8, -4.8, 4.8, 7.8):  # focos al pie de la fachada apuntando arriba
        p = V((x, YF - 3.4, 0.12))
        c.caja(p + V((0, 0, 0.1)), (0.4, 0.3, 0.2), osc, 0.03)
        with c.en(p + V((0, 0, 0.35)), (-55, 0, 0)):
            c.cil((0, 0, -0.15), (0, 0, 0.15), 0.18, osc, n=10)
            luces.cil((0, 0, 0.15), (0, 0, 0.17), 0.14, None, n=10)
    # placa de fundación de bronce junto a la puerta
    c.caja((px1 + 1.0, YF - 0.06, 2.6), (1.6, 0.08, 0.95), oro, 0.03)
    tinta = m.mat("metal", "#5A4420", rug=0.4)
    c.texto("COLONIA NUEVA ESPERANZA", tinta, alto=0.12, grosor=0.02, c=(px1 + 1.0, YF - 0.1, 2.8), fuente="mono", resol=1)
    c.texto("Fundada año 2847", tinta, alto=0.12, grosor=0.02, c=(px1 + 1.0, YF - 0.1, 2.45), fuente="mono", resol=1)
    for dx in (-0.72, 0.72):
        c.perno((px1 + 1.0 + dx, YF - 0.1, 2.6), (0, -1, 0), oro, r=0.03)
    m.seccion("jardín formal")
    rnd = random.Random(91)
    for s in (-1, 1):
        xs = s * 6.5
        c.caja_de((xs - 2.0, YF - 4.6, 0.12), (xs + 2.0, YF - 1.4, 0.3), piedra, 0.04)  # parterre
        c.caja_de((xs - 1.85, YF - 4.45, 0.3), (xs + 1.85, YF - 1.55, 0.34), tierra)
        c.caja((xs, YF - 4.25, 0.62), (3.6, 0.4, 0.6), seto, 0.12)  # seto recortado delantero
        for x in (xs - 1.4, xs + 1.4):
            c.ico((x, YF - 2.4, 1.0), 0.6, seto2, sub=3, suave=(0.04, 2.0), semilla=int(x * 10))  # topiaria
            c.cil((x, YF - 2.4, 0.34), (x, YF - 2.4, 0.5), 0.12, m.mat("madera", "#5A3A22", eje="Z"), n=6)
        for k in range(10):
            p = V((xs + rnd.uniform(-0.8, 0.8), YF - 3.2 + rnd.uniform(-0.4, 0.4), 0.38))
            c.ico(p, 0.08, flores[k % 3], sub=1, esc=(1, 1, 0.6))
    m.terminar()


# ==============================================================================================================
def laboratorio():
    m = Modelo("laboratorio", ZONA, (14, 12, 10), 16000,
               "Laboratorio de investigación: fachada limpia y moderna, ventanales con gradilla de 6 tubos de ensayo, "
               "probetas y microscopio, chimenea con extractor, luces verdes de descontaminación sobre la puerta, "
               "señal de riesgo biológico, contenedor de residuos, 2 cámaras y lector de tarjetas.")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#B6DCE6", transparencia=0.3)
    vidrio = m.parte("vidrio_lab_cristal", tipo="cristal", color="#E6F6FA", transparencia=0.55,
                     nota="Tubos de ensayo y probetas: Glass casi transparente.")
    verde = m.parte("descontaminacion_neon", tipo="neon", color=VERDE_DESCONTAMINACION,
                    nota="Luces de descontaminación: Neon verde #39FF14.")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    blanco = m.mat("paneles", "#EEF0F1", tam_panel=(1.4, 1.4), desgaste=0.15, c_desgaste="#A0A6AC", suciedad=0.3,
                   lluvia=0.2)
    grafito = m.mat("paneles", "#2E353D", tam_panel=(1.4, 2.8), desgaste=0.25)
    gris = m.mat("pintura", "#8A9198", desgaste=0.2)
    acero = m.mat("metal", "#9AA0A6", rug=0.3)
    osc = m.mat("metal", "#24282C", rug=0.4)
    horm = m.mat("hormigon", "#B8B4AC")
    amarillo = m.mat("pintura", "#E8C21E", desgaste=0.35)
    negro = m.mat("pintura", "#16181A", desgaste=0.0)
    banco = m.mat("plastico", "#D8DEE2")
    liq = [m.mat("liquido", h) for h in ("#3FCB5A", "#2E7DE0", "#E5542A", "#C93AD8", "#E8C21E", "#2AD8C8")]
    X0, X1, YF, YB, Z0, ZT = -7.0, 7.0, -4.6, 5.4, 0.3, 7.6

    m.seccion("cuerpo")
    c.caja_de((X0 - 0.2, YF - 1.4, 0), (X1 + 0.2, YB + 0.2, Z0), horm, 0.04)
    PUE = (-1.1, 1.1, Z0, 4.2)
    V1 = (-6.2, -1.9, 1.6, 5.0)
    V2 = (1.9, 6.2, 1.6, 5.0)
    arq.muro_huecos(c, X0, X1, Z0, ZT, YF, YF + 0.4, [PUE, V1, V2], blanco)
    for x in (X0, X1 - 0.4):
        c.caja_de((x, YF + 0.4, Z0), (x + 0.4, YB - 0.4, ZT), blanco)
    c.caja_de((X0, YB - 0.4, Z0), (X1, YB, ZT), blanco)
    # franja de grafito vertical que enmarca la entrada y alero plano
    c.caja_de((-1.7, YF - 0.12, Z0), (1.7, YF + 0.02, ZT + 0.1), grafito, 0.03)
    c.caja_de((X0 - 0.3, YF - 0.6, ZT), (X1 + 0.3, YB + 0.3, ZT + 0.3), gris, 0.04)
    c.caja_de((X0 - 0.1, YF - 0.4, ZT + 0.3), (X1 + 0.1, YB + 0.1, ZT + 0.5), blanco, 0.03)
    for (x0, x1, z0, z1) in (V1, V2):
        arq.marco(c, x0, x1, z0, z1, YF, 0.1, 0.1, osc)
        cr.caja_de((x0, YF + 0.1, z0), (x1, YF + 0.18, z1), None)
        c.caja_de(((x0 + x1) / 2 - 0.04, YF - 0.02, z0), ((x0 + x1) / 2 + 0.04, YF + 0.12, z1), osc, 0.0)
        # interior del ventanal: sala blanca con su banco de laboratorio
        YI = YF + 0.4
        c.caja_de((x0 - 0.1, YI, Z0), (x1 + 0.1, YI + 2.4, Z0 + 0.05), m.mat("plastico", "#C8D0D4"))
        c.caja_de((x0 - 0.1, YI + 2.4, Z0), (x1 + 0.1, YI + 2.6, z1 + 0.4), m.mat("plastico", "#E6EEF0"))
        c.caja_de((x0 - 0.1, YI, z1 + 0.2), (x1 + 0.1, YI + 2.6, z1 + 0.4), m.mat("plastico", "#E6EEF0"))
        for x in (x0 - 0.1, x1):
            c.caja_de((x, YI, Z0), (x + 0.1, YI + 2.6, z1 + 0.4), m.mat("plastico", "#E6EEF0"))
        c.caja_de((x0 + 0.2, YI + 1.0, Z0), (x1 - 0.2, YI + 1.8, Z0 + 1.55), banco, 0.03)
        c.caja_de((x0 + 0.1, YI + 0.9, Z0 + 1.55), (x1 - 0.1, YI + 1.9, Z0 + 1.65), osc, 0.02)
        luces.caja(((x0 + x1) / 2, YI + 1.3, z1 + 0.15), (x1 - x0 - 0.6, 0.3, 0.04), None)
    zb = Z0 + 1.65
    YI = YF + 0.4
    # ventanal izquierdo: gradilla con 6 tubos de ensayo y probetas
    gx = -4.6
    c.caja((gx, YI + 1.2, zb + 0.05), (1.3, 0.3, 0.06), acero, 0.01)
    c.caja((gx, YI + 1.2, zb + 0.35), (1.3, 0.3, 0.04), acero, 0.01)
    for s in (-1, 1):
        c.caja((gx + s * 0.63, YI + 1.2, zb + 0.2), (0.04, 0.3, 0.32), acero, 0.0)
    for k in range(6):
        x = gx - 0.5 + k * 0.2
        vidrio.cil((x, YI + 1.2, zb + 0.1), (x, YI + 1.2, zb + 0.75), 0.05, None, n=8)
        c.cil((x, YI + 1.2, zb + 0.12), (x, YI + 1.2, zb + 0.12 + 0.15 + 0.05 * k), 0.042, liq[k], n=8)
        c.cil((x, YI + 1.2, zb + 0.75), (x, YI + 1.2, zb + 0.82), 0.055, liq[(k + 3) % 6], n=8)  # tapón
    for k, x in enumerate((-3.2, -2.6)):  # matraces Erlenmeyer
        vidrio.torno([(0.0, 0.0), (0.22, 0.0), (0.24, 0.05), (0.08, 0.4), (0.07, 0.55), (0.0, 0.55)], None, n=10,
                     c=(x, YI + 1.3, zb))
        c.torno([(0.0, 0.02), (0.2, 0.02), (0.13, 0.2), (0.0, 0.2)], liq[k + 1], n=10, c=(x, YI + 1.3, zb))
    # ventanal derecho: microscopio
    mx_ = 4.0
    c.caja((mx_, YI + 1.3, zb + 0.05), (0.5, 0.6, 0.1), osc, 0.02)
    c.tubo([(mx_, YI + 1.55, zb + 0.1), (mx_, YI + 1.6, zb + 0.6), (mx_, YI + 1.45, zb + 0.95)], 0.06, osc, n=6, seg=2)
    c.caja((mx_, YI + 1.25, zb + 0.4), (0.4, 0.35, 0.04), acero, 0.01)  # platina
    c.cil((mx_, YI + 1.3, zb + 0.95), (mx_, YI + 1.15, zb + 0.6), 0.06, acero, n=10)  # tubo óptico
    c.cil((mx_, YI + 1.3, zb + 0.95), (mx_, YI + 1.42, zb + 1.15), 0.035, osc, n=8)  # ocular
    for k in range(3):
        a = k * 2.1
        c.cil((mx_, YI + 1.15, zb + 0.6), (mx_ + math.cos(a) * 0.05, YI + 1.15 + math.sin(a) * 0.05, zb + 0.48), 0.02,
              cromo_m(m), n=6)
    c.cil((mx_ + 0.22, YI + 1.42, zb + 0.4), (mx_ + 0.3, YI + 1.42, zb + 0.4), 0.05, acero, n=8)  # tornillo de enfoque
    m.seccion("puerta, descontaminación, lector")
    px0, px1, pz0, pz1 = PUE
    arq.marco(c, px0, px1, pz0, pz1, YF - 0.12, 0.12, 0.12, osc, abajo=False)
    for lado, (hx0, s) in {"izq": (px0, 1), "der": (px1, -1)}.items():
        w = (px1 - px0) / 2
        pv = (hx0 + s * w / 2, YF - 0.2, pz0)
        h = m.parte(f"puerta_{lado}", pivote=pv, nota=f"Hoja corredera: abrir {w - 0.05:.2f} studs hacia fuera.")
        hc = m.parte(f"puerta_{lado}_cristal", tipo="cristal", color="#E9F1F3", pivote=pv, transparencia=0.15)
        xa, xb = sorted((hx0, hx0 + s * w))
        h.caja_de((xa, YF - 0.26, pz0), (xb, YF - 0.14, pz0 + 0.1), acero, 0.01)
        h.caja_de((xa, YF - 0.26, pz1 - 0.1), (xb, YF - 0.14, pz1), acero, 0.01)
        h.caja_de((xa, YF - 0.26, pz0), (xa + 0.08, YF - 0.14, pz1), acero, 0.01)
        h.caja_de((xb - 0.08, YF - 0.26, pz0), (xb, YF - 0.14, pz1), acero, 0.01)
        hc.caja_de((xa + 0.08, YF - 0.23, pz0 + 0.1), (xb - 0.08, YF - 0.17, pz1 - 0.1), None)
    # pórtico de descontaminación: marco de luces verdes alrededor de la puerta
    verde.caja(((px0 + px1) / 2, YF - 0.25, pz1 + 0.3), (px1 - px0 + 0.4, 0.06, 0.08), None)
    for x in (px0 - 0.22, px1 + 0.22):
        verde.caja((x, YF - 0.25, (pz0 + pz1) / 2 + 0.15), (0.08, 0.06, pz1 - pz0 + 0.3), None)
    for k in range(4):
        verde.esfera(((px0 + px1) / 2 - 0.75 + k * 0.5, YF - 0.3, pz1 + 0.5), 0.06, None, seg=8, anillos=5)
    # lector de tarjetas: caja con ranura y led
    lx = px1 + 0.55
    c.caja((lx, YF - 0.16, 2.3), (0.3, 0.12, 0.45), osc, 0.03)
    c.caja((lx, YF - 0.23, 2.2), (0.18, 0.02, 0.03), negro, 0.0)
    verde.cil((lx, YF - 0.22, 2.42), (lx, YF - 0.24, 2.42), 0.025, None, n=8)
    luces.caja((lx, YF - 0.225, 2.32), (0.16, 0.01, 0.06), None)
    m.seccion("señales, residuos y cámaras")
    # cartel LABORATORIO — ACCESO RESTRINGIDO sobre la puerta
    c.caja((0, YF - 0.16, ZT - 1.4), (5.0, 0.06, 0.95), osc, 0.02)
    c.texto("LABORATORIO", m.mat("pintura", "#F2F2F2", desgaste=0.0), alto=0.38, grosor=0.02, c=(0, YF - 0.2, ZT - 1.35),
            fuente="estrecha", resol=1)
    c.texto("ACCESO RESTRINGIDO", amarillo, alto=0.18, grosor=0.02, c=(0, YF - 0.2, ZT - 1.72), fuente="mono", resol=1)
    # señal de riesgo biológico: triángulo amarillo con el símbolo (tres medias lunas y anillo)
    def biohazard(centro, r, rot=(90, 0, 0)):
        with c.en(centro, rot):
            c.extruir([(-r * 1.3, -r * 0.95), (r * 1.3, -r * 0.95), (0, r * 1.45)], 0.02, amarillo)
            c.extruir([(-r * 1.12, -r * 0.83), (r * 1.12, -r * 0.83), (0, r * 1.25)], 0.03, negro)
            c.extruir([(-r * 1.0, -r * 0.76), (r * 1.0, -r * 0.76), (0, r * 1.12)], 0.04, amarillo)
            for k in range(3):
                a = math.pi / 2 + k * math.tau / 3
                c.toro((math.cos(a) * r * 0.22, math.sin(a) * r * 0.22, 0.02), r * 0.24, r * 0.04, negro, n=10, m=3)
            c.toro((0, 0, 0.02), r * 0.17, r * 0.035, negro, n=10, m=3)
    biohazard((px0 - 0.9, YF - 0.05, 3.2), 0.35)
    # contenedor de residuos especiales
    cx_ = X1 - 1.2
    c.caja((cx_, YF - 0.8, Z0 + 0.6), (1.2, 0.9, 1.2), amarillo, 0.06)
    c.caja((cx_, YF - 0.8, Z0 + 1.25), (1.25, 0.95, 0.1), amarillo, 0.03)
    for s in (-1, 1):
        c.cil((cx_ + s * 0.45, YF - 0.8, Z0 + 0.05), (cx_ + s * 0.45, YF - 0.8, Z0 + 0.1), 0.12, osc, n=8)
    biohazard((cx_, YF - 1.26, Z0 + 0.65), 0.25)
    arq.camara_seguridad(c, luces, (px0 - 0.5, YF - 0.12, 5.2), m.mat("plastico", "#D5D8DB"), acero, osc)
    arq.camara_seguridad(c, luces, (X1 - 0.5, YF, 6.4), m.mat("plastico", "#D5D8DB"), acero, osc)
    m.seccion("laterales y trasera")
    # ventanas corridas en los laterales, puerta de carga trasera con rampa, conductos y climatizadora de pared
    for xs, s in ((X0, -1), (X1, 1)):
        for k in range(3):
            y = YF + 1.6 + k * 3.0
            c.caja((xs + s * 0.03, y, 4.4), (0.1, 2.4, 1.1), osc, 0.02)
            cr.caja((xs + s * 0.08, y, 4.4), (0.04, 2.2, 0.9), None)
            c.caja((xs + s * 0.1, y, 3.8), (0.2, 2.5, 0.08), gris, 0.01)
        c.tubo([(xs + s * 0.15, YB - 1.0, Z0 + 0.2), (xs + s * 0.15, YB - 1.0, 6.0), (xs + s * 0.15, YB - 2.0, 6.6),
                (xs + s * 0.15, YF + 1.0, 6.6)], 0.09, acero, n=6, seg=2)
    c.caja((X1 + 0.35, 1.0, 2.0), (0.6, 1.4, 1.2), acero, 0.06)  # climatizadora de pared
    c.cil((X1 + 0.66, 1.0, 2.0), (X1 + 0.7, 1.0, 2.0), 0.5, osc, n=14)
    for k in range(4):
        c.caja((X1 + 0.72, 1.0, 1.65 + k * 0.23), (0.03, 0.9, 0.04), acero, 0.0)
    c.caja_de((-1.6, YB, Z0), (1.6, YB + 0.1, 4.0), gris, 0.03)  # puerta de carga
    for k in range(9):
        c.caja((0, YB + 0.12, Z0 + 0.3 + k * 0.4), (3.0, 0.04, 0.3), acero, 0.01)
    with c.en((0, YB + 1.0, Z0 / 2), (-math.degrees(math.atan2(Z0, 1.8)), 0, 0)):
        c.caja((0, 0, 0), (3.2, 1.9, 0.12), m.mat("grip", "#7A8087"), 0.02)
    luces.caja((0, YB + 0.15, 4.2), (1.0, 0.06, 0.1), None)
    m.seccion("chimenea con extractor")
    ch = V((-4.0, 2.5, ZT + 0.5))
    c.caja(ch + V((0, 0, 0.6)), (1.2, 1.2, 1.2), gris, 0.05)
    c.cil(ch + V((0, 0, 1.2)), ch + V((0, 0, 3.0)), 0.35, acero, n=12)
    c.cil(ch + V((0, 0, 3.0)), ch + V((0, 0, 3.15)), 0.45, osc, n=12)
    for k in range(6):
        a = k * math.pi / 3
        c.caja(ch + V((math.cos(a) * 0.2, math.sin(a) * 0.2, 3.18)), (0.34, 0.06, 0.02), acero, 0.0,
               rot=(0, 18, math.degrees(a)))
    c.caja((3.0, 2.0, ZT + 0.9), (2.0, 1.6, 0.8), acero, 0.06)  # climatizadora
    c.cil((3.0, 2.0, ZT + 1.3), (3.0, 2.0, ZT + 1.36), 0.55, osc, n=14)
    m.terminar()


def cromo_m(m):
    return m.mat("cromo", "#D2D6DA")


# ==============================================================================================================
def academia_entrenamiento():
    m = Modelo("academia_entrenamiento", ZONA, (16, 16, 8), 16000,
               "Academia de entrenamiento: nave semiabierta (frente sin pared) con 3 dianas con impactos, 2 maniquíes "
               "de combate de brazos articulados, tatami, armero con palos y escudos de práctica, gradas de 3 filas, "
               "marcador holográfico y cartel ACADEMIA — HONOR Y DISCIPLINA.")
    c = m.parte()
    holo = m.parte("marcador_neon", tipo="neon", color=NEON, transparencia=0.55, nota="Fondo del marcador holográfico.")
    cifras = m.parte("cifras_neon", tipo="neon", color=TEXTO_HOLO, nota="Cifras del marcador.")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    rnd = random.Random(97)
    panel = m.mat("paneles", "#5A6472", tam_panel=(2.0, 2.0), desgaste=0.45)
    gris = m.mat("pintura", "#3A424C", desgaste=0.45)
    rojo = m.mat("pintura", "#A8282A", desgaste=0.5)
    acero = m.mat("metal", "#848A91")
    osc = m.mat("metal", "#2B2F34", rug=0.5)
    horm = m.mat("hormigon", "#9A968E")
    suelo = m.mat("madera", "#B08A5E", eje="X", suciedad=0.3)
    tatami = [m.mat("tela", h, bump=0.5) for h in ("#2E5A8A", "#A83A2A")]
    madera = m.mat("madera", "#8A5C34", eje="Z")
    cuero = m.mat("cuero", "#5E3A22")
    blanco = m.mat("pintura", "#ECEAE4", desgaste=0.3)
    negro = m.mat("pintura", "#1E2024", desgaste=0.2)
    oro = m.mat("metal", "#C9A040", rug=0.3)
    X0, X1, YF, YB, Z0, ZT = -8.0, 8.0, -6.0, 8.0, 0.3, 7.0

    m.seccion("nave")
    c.caja_de((X0, YF - 1.0, 0), (X1, YB, Z0), horm, 0.04)
    c.caja_de((X0 + 0.4, YF, Z0), (X1 - 0.4, YB - 0.4, Z0 + 0.05), suelo)
    for x in (X0, X1 - 0.4):  # muros laterales y del fondo
        c.caja_de((x, YF + 1.0, Z0), (x + 0.4, YB, ZT), panel)
    c.caja_de((X0, YB - 0.4, Z0), (X1, YB, ZT), panel)
    # pórtico del frente abierto: pilares y viga
    for x in (X0 + 0.2, -2.7, 2.7, X1 - 0.2):
        arq.viga_h(c, (x, YF + 0.2, Z0), (x, YF + 0.2, ZT), 0.45, 0.4, gris)
    arq.viga_h(c, (X0, YF + 0.2, ZT - 0.2), (X1, YF + 0.2, ZT - 0.2), 0.5, 0.4, gris)
    # cubierta en diente de sierra (tres faldones) con lucernarios
    for k in range(3):
        y0 = YF + k * (YB - YF) / 3
        y1 = y0 + (YB - YF) / 3
        ang = math.degrees(math.atan2(1.0, y1 - y0))
        with c.en((0, (y0 + y1) / 2, ZT + 0.55), (-ang, 0, 0)):
            c.caja((0, 0, 0), (X1 - X0 + 0.6, math.hypot(y1 - y0, 1.0), 0.14), gris, 0.04)
    for k in range(3):
        y1 = YF + (k + 1) * (YB - YF) / 3
        c.caja((0, y1 - 0.05, ZT + 0.55), (X1 - X0, 0.1, 1.1), acero, 0.01)
    luz_y = [YF + 2.0, YF + 6.5, YF + 11.0]
    for y in luz_y:
        for x in (-4.5, 0.0, 4.5):
            c.cil((x, y, ZT), (x, y, ZT - 0.6), 0.02, osc, n=4)
            c.caja((x, y, ZT - 0.65), (1.8, 0.3, 0.1), acero, 0.02)
            luces.caja((x, y, ZT - 0.72), (1.6, 0.2, 0.03), None)
    m.seccion("tatami")
    for i in range(6):
        for j in range(5):
            x = -4.5 + i * 1.5
            y = 0.0 + j * 1.0
            c.caja((x, y, Z0 + 0.12), (1.46, 0.96, 0.14), tatami[(i + j) % 2 if (i in (0, 5) or j in (0, 4)) else 0], 0.04)
    m.seccion("dianas")
    for k, x in enumerate((-4.5, 0.0, 4.5)):
        y = YB - 0.45
        with c.en((x, y, 3.4), (90, 0, 0)):
            c.cil((0, 0, 0.0), (0, 0, 0.08), 1.1, madera, n=20)
            for j, (r, mat) in enumerate(((1.0, blanco), (0.8, rojo), (0.6, blanco), (0.4, rojo), (0.2, oro))):
                c.cil((0, 0, 0.08 + j * 0.005), (0, 0, 0.085 + j * 0.005), r, mat, n=20)
            for h in range(5 + k):  # impactos
                a = rnd.uniform(0, math.tau)
                rr = rnd.uniform(0.05, 0.85)
                c.cil((math.cos(a) * rr, math.sin(a) * rr, 0.07), (math.cos(a) * rr, math.sin(a) * rr, 0.115), 0.035,
                      negro, n=6)
        c.caja((x, y + 0.02, 1.2), (0.12, 0.1, 2.4), madera, 0.02)  # pie de la diana
    m.seccion("maniquíes de combate")
    for k, x in enumerate((-2.5, 2.5)):
        y = 2.0
        c.cil((x, y, Z0 + 0.19), (x, y, Z0 + 0.25), 0.5, osc, n=12)
        c.cil((x, y, Z0 + 0.25), (x, y, Z0 + 3.0), 0.12, madera, n=10)
        c.cil((x, y, Z0 + 1.6), (x, y, Z0 + 2.8), 0.32, cuero, n=12, b=0.05)  # torso acolchado
        c.esfera((x, y, Z0 + 3.2), 0.26, cuero, seg=10, anillos=6)
        for s in (-1, 1):  # brazos articulados: hombro, codo y antebrazo
            hom = V((x + s * 0.34, y, Z0 + 2.55))
            codo = hom + V((s * 0.45, -0.25 + k * 0.2, -0.25 + k * 0.35))
            mano = codo + V((s * 0.15, -0.45, 0.1 - k * 0.2))
            c.esfera(hom, 0.1, acero, seg=8, anillos=5)
            c.cil(hom, codo, 0.06, madera, n=6)
            c.esfera(codo, 0.08, acero, seg=8, anillos=5)
            c.cil(codo, mano, 0.055, madera, n=6)
        c.cil((x - 0.12, y, Z0 + 1.0), (x + 0.12, y, Z0 + 1.0), 0.1, acero, n=8)  # muelle de la base
    m.seccion("armero")
    ax = X0 + 0.45
    c.caja((ax, 2.5, 2.8), (0.1, 4.5, 0.15), madera, 0.02)
    c.caja((ax, 2.5, 0.9), (0.1, 4.5, 0.15), madera, 0.02)
    for k in range(6):  # palos de entrenamiento
        y = 0.8 + k * 0.45
        c.cil((ax + 0.18, y, Z0 + 0.1), (ax + 0.28, y, 4.0), 0.05, madera, n=6)
    for k in range(2):  # escudos de práctica
        y = 4.0 + k * 0.95
        with c.en((ax + 0.15, y, 2.3), (0, 90, 0)):
            c.cil((0, 0, 0), (0, 0, 0.08), 0.42, madera, n=14)
            c.toro((0, 0, 0.08), 0.42, 0.03, acero, n=14, m=3)
            c.esfera((0, 0, 0.12), 0.1, acero, seg=8, anillos=4, esc=(1, 1, 0.6))
    m.seccion("gradas")
    gx = X1 - 2.4
    for k in range(3):
        z = Z0 + 0.5 + k * 0.6
        x = gx + k * 0.65
        c.caja((x, 2.0, z), (0.6, 8.0, 0.1), m.mat("metal", "#6E747A", rug=0.4), 0.02)
        for y in (-1.6, 2.0, 5.6):
            c.caja((x, y, (Z0 + z) / 2), (0.08, 0.08, z - Z0), osc)
    c.cil((gx + 1.7, -2.0, Z0 + 2.4), (gx + 1.7, 6.0, Z0 + 2.4), 0.04, acero, n=6)  # barandilla trasera
    m.seccion("marcador y cartel")
    c.caja((0, YB - 0.5, 5.9), (3.2, 0.15, 1.1), osc, 0.03)
    holo.caja((0, YB - 0.6, 5.9), (3.0, 0.03, 0.95), None)
    for k, txt in enumerate(("12", "09")):
        cifras.texto(txt, None, alto=0.55, grosor=0.03, c=(-0.8 + k * 1.6, YB - 0.64, 5.62), fuente="mono", resol=1)
    cifras.caja((0, YB - 0.64, 5.9), (0.1, 0.02, 0.1), None)
    c.caja((0, YF + 0.0, ZT - 0.9), (6.2, 0.12, 0.9), rojo, 0.03)
    c.texto("ACADEMIA", oro, alto=0.42, grosor=0.03, c=(0, YF - 0.08, ZT - 0.95), fuente="serif", resol=1)
    c.texto("HONOR Y DISCIPLINA", blanco, alto=0.16, grosor=0.02, c=(0, YF - 0.08, ZT - 1.25), fuente="mono", resol=1)
    m.terminar()


MODELOS = {
    "centro_mando": centro_mando,
    "laboratorio": laboratorio,
    "academia_entrenamiento": academia_entrenamiento,
}
