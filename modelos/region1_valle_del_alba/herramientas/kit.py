"""
Kit de construcción del Valle del Alba: las piezas con las que se montan los edificios y el mobiliario.

Estilo: pueblo europeo de cuento, limpio y luminoso. Paredes de yeso de colores claros, zócalo y esquinas de piedra,
tejados de teja roja por hiladas, contraventanas pintadas, jardineras con flores, farolas de hierro.

Todas las piezas son mallas low-poly (`malla.Malla`), en studs, con Z arriba. Escala: un personaje R6 mide 5 studs;
una puerta, 4 × 7,4; un piso, 10 (la planta baja, 11).

CONVENCIÓN DE LAS PIEZAS DE PARED: ocupan x ∈ [0, MODULO] a lo largo de la pared, y ∈ [0, GROSOR] hacia DENTRO del
edificio (la cara exterior está en y = 0 y mira a -Y) y z ∈ [0, altura del piso]. Los adornos (alféizares,
contraventanas, toldos) salen hacia -Y.

Las ranuras de material (PARED, TEJA, PINTURA, PUERTA, TOLDO_A, PIEDRA, MARCO...) las elige cada edificio.

Todo lo ajustable (medidas) está en MEDIDAS, arriba.
"""

import math

import numpy as np

from malla import Malla, Rx, Ry, Rz, S, T, compone

MEDIDAS = dict(
    modulo=8.0,  # ancho de un tramo de pared
    grosor=1.0,  # grosor de pared
    piso_bajo=11.0,
    piso=10.0,
    zocalo=0.6,  # losa de piedra sobre la que se asienta cada edificio (tapa los desniveles del suelo)
    puerta=(4.0, 7.4),
    ventana=(3.0, 4.2),
    alfeizar=3.2,  # altura del alféizar sobre el suelo del piso
    pendiente=0.62,  # subida del tejado por stud horizontal (~32°)
    alero=1.3,
    vuelo=0.9,  # lo que sale el tejado por el hastial
    hilada=1.35,  # alto de cada hilada de tejas (medido en la pendiente)
    teja=2.0,  # ancho de cada teja
)
M = MEDIDAS["modulo"]
G = MEDIDAS["grosor"]


def _rng(semilla):
    return np.random.default_rng(semilla)


# ==============================================================================================================
# Paredes
# ==============================================================================================================


def pared_lisa(alto=MEDIDAS["piso"]):
    return Malla().caja((0, 0, 0), (M, G, alto), "PARED")


def _pared_con_hueco(alto, x0, x1, z0, z1):
    m = Malla()
    m.caja((0, 0, 0), (x0, G, alto), "PARED")
    m.caja((x1, 0, 0), (M, G, alto), "PARED")
    if z0 > 0:
        m.caja((x0, 0, 0), (x1, G, z0), "PARED")
    if z1 < alto:
        m.caja((x0, 0, z1), (x1, G, alto), "PARED")
    return m


def ventana(ancho=MEDIDAS["ventana"][0], alto=MEDIDAS["ventana"][1], contraventanas=True, jardinera=False,
            semilla=0):
    """Ventana para un hueco de ancho × alto con la esquina inferior izquierda en el origen."""
    rng = _rng(semilla)
    m = Malla()
    w, h = ancho, alto
    # Vidrio y cruceta
    m.caja((0.1, 0.55, 0.1), (w - 0.1, 0.62, h - 0.1), "Vidrio", tinte=float(rng.uniform(0.85, 1.15)))
    m.caja((w / 2 - 0.11, 0.42, 0.1), (w / 2 + 0.11, 0.55, h - 0.1), "MARCO")
    m.caja((0.1, 0.42, h * 0.62 - 0.11), (w - 0.1, 0.55, h * 0.62 + 0.11), "MARCO")
    # Marco
    for a, b in (((0, 0.3, 0), (0.28, 0.7, h)), ((w - 0.28, 0.3, 0), (w, 0.7, h)), ((0, 0.3, h - 0.28), (w, 0.7, h)),
                 ((0, 0.3, 0), (w, 0.7, 0.28))):
        m.caja(a, b, "MARCO")
    # Recercado de piedra en la fachada, alféizar y dintel
    m.caja((-0.45, -0.14, 0), (0, 0.02, h), "PIEDRA", sin=("+y",))
    m.caja((w, -0.14, 0), (w + 0.45, 0.02, h), "PIEDRA", sin=("+y",))
    m.caja((-0.55, -0.5, -0.38), (w + 0.55, 0.32, 0.02), "PIEDRA")
    m.caja((-0.5, -0.22, h), (w + 0.5, 0.02, h + 0.55), "PIEDRA", sin=("+y",))
    m.caja((w / 2 - 0.35, -0.3, h - 0.05), (w / 2 + 0.35, 0.02, h + 0.62), "PIEDRA", tinte=0.93)  # clave
    if contraventanas:
        sw = w / 2 + 0.05
        for lado in (-1, 1):
            x0 = -0.5 - sw if lado < 0 else w + 0.5
            m.caja((x0, -0.32, 0.1), (x0 + sw, -0.12, h - 0.1), "PINTURA")
            for k in range(3):  # lamas
                z = 0.7 + k * (h - 1.4) / 2.6
                m.caja((x0 + 0.15, -0.42, z), (x0 + sw - 0.15, -0.3, z + 0.32), "PINTURA", tinte=0.88)
    if jardinera:
        m.caja((0.0, -1.15, -1.3), (w, -0.5, -0.38), "Madera_Media")
        colores = ["Flor_Roja", "Flor_Rosa", "Flor_Amarilla", "Flor_Blanca", "Flor_Lila"]
        c1 = colores[int(rng.integers(len(colores)))]
        c2 = colores[int(rng.integers(len(colores)))]
        for k in range(3):
            x = 0.45 + k * (w - 0.9) / 2
            m.esfera((x, -0.85, -0.3), 0.55, "Hoja_Verde", sub=0, jitter=0.2, rng=rng)
            m.esfera((x + rng.uniform(-0.15, 0.15), -0.95, 0.05 + rng.uniform(0, 0.2)), 0.3,
                     c1 if k % 2 else c2, sub=0)
    return m


def pared_ventana(alto=MEDIDAS["piso"], contraventanas=True, jardinera=False, semilla=0):
    w, h = MEDIDAS["ventana"]
    x0 = (M - w) / 2
    z0 = MEDIDAS["alfeizar"]
    m = _pared_con_hueco(alto, x0, x0 + w, z0, z0 + h)
    m.anadir(ventana(w, h, contraventanas, jardinera, semilla), T(x0, 0, z0))
    return m


def puerta(ancho=MEDIDAS["puerta"][0], alto=MEDIDAS["puerta"][1], semilla=0, farolillo=True):
    """Puerta de tablas con recercado de sillares, escalón y farolillo."""
    rng = _rng(semilla)
    m = Malla()
    w, h = ancho, alto
    n = 5
    for k in range(n):  # tablas
        x0 = 0.1 + k * (w - 0.2) / n
        m.caja((x0 + 0.03, 0.5, 0.0), (x0 + (w - 0.2) / n - 0.03, 0.72, h - 0.1), "PUERTA",
               tinte=float(rng.uniform(0.9, 1.08)))
    m.caja((0.1, 0.42, 1.4), (w - 0.1, 0.5, 1.9), "PUERTA", tinte=0.85)  # travesaños
    m.caja((0.1, 0.42, h - 2.2), (w - 0.1, 0.5, h - 1.7), "PUERTA", tinte=0.85)
    m.caja((w - 0.85, 0.3, 3.4), (w - 0.55, 0.42, 3.9), "Oro")  # tirador
    # Sillares de las jambas (alternos, como en las esquinas)
    z, k = 0.0, 0
    while z < h - 0.1:
        alto_s = min(1.25, h - z)
        ancho_s = 0.75 if k % 2 else 1.05
        t = float(rng.uniform(0.9, 1.06))
        m.caja((-ancho_s, -0.16, z), (0, 0.02, z + alto_s - 0.06), "PIEDRA", tinte=t, sin=("+y",))
        m.caja((w, -0.16, z), (w + ancho_s, 0.02, z + alto_s - 0.06), "PIEDRA", tinte=t, sin=("+y",))
        z += alto_s
        k += 1
    # Dintel con clave
    m.caja((-1.05, -0.2, h), (w + 1.05, 0.02, h + 0.8), "PIEDRA", sin=("+y",))
    m.prisma([(w / 2 - 0.45, -0.32), (w / 2 + 0.45, -0.32), (w / 2 + 0.45, 0.02), (w / 2 - 0.45, 0.02)],
             h - 0.1, h + 1.05, "PIEDRA", tinte=0.92)
    # Escalón (por debajo del suelo del piso: llega a la losa)
    m.caja((-0.8, -1.5, -MEDIDAS["zocalo"]), (w + 0.8, 0.3, 0.0), "Piedra_Media")
    if farolillo:
        m.anadir(farolillo_pared(), T(w + 1.5, 0, h - 0.6))
    return m


def farolillo_pared():
    m = Malla()
    m.caja((-0.15, -1.3, 1.35), (0.15, 0.0, 1.6), "Hierro")  # brazo
    m.caja((-0.13, -1.28, 0.2), (0.13, -1.02, 1.35), "Hierro")
    m.tronco((0, -1.15, -1.1), 0.42, 0.42, 1.2, 4, "Luz_Calida", giro=45)
    m.tronco((0, -1.15, 0.1), 0.62, 0.15, 0.55, 4, "Hierro", giro=45)
    m.tronco((0, -1.15, -1.3), 0.3, 0.55, 0.22, 4, "Hierro", giro=45)
    return m


def pared_puerta(alto=MEDIDAS["piso_bajo"], semilla=0):
    w, h = MEDIDAS["puerta"]
    x0 = (M - w) / 2
    m = _pared_con_hueco(alto, x0, x0 + w, 0.0, h)
    m.anadir(puerta(w, h, semilla), T(x0, 0, 0))
    return m


def pared_escaparate(alto=MEDIDAS["piso_bajo"], semilla=0):
    """Escaparate de tienda: zócalo de madera, cristal grande con parteluces y montante."""
    x0, x1, z0, z1 = 0.9, M - 0.9, 1.3, 7.6
    m = _pared_con_hueco(alto, x0, x1, 0.0, z1)
    w = x1 - x0
    m.caja((x0, 0.2, 0), (x1, 0.9, z0), "MARCO")
    m.caja((x0 + 0.3, 0.1, 0.25), (x1 - 0.3, 0.2, z0 - 0.25), "MARCO", tinte=0.85)
    m.caja((x0, 0.55, z0), (x1, 0.62, z1), "Vidrio", tinte=1.1)
    for k in (1, 2):
        xm = x0 + w * k / 3
        m.caja((xm - 0.12, 0.4, z0), (xm + 0.12, 0.55, z1), "MARCO")
    m.caja((x0, 0.4, z1 - 1.5), (x1, 0.55, z1 - 1.3), "MARCO")
    for a, b in (((x0, 0.2, z1 - 0.3), (x1, 0.75, z1)), ((x0, 0.2, z0), (x0 + 0.3, 0.75, z1)),
                 ((x1 - 0.3, 0.2, z0), (x1, 0.75, z1))):
        m.caja(a, b, "MARCO")
    # Repisa de piedra bajo el cristal y friso para el rótulo
    m.caja((x0 - 0.3, -0.35, z0 - 0.2), (x1 + 0.3, 0.2, z0), "PIEDRA")
    m.caja((x0 - 0.5, -0.3, z1), (x1 + 0.5, 0.02, z1 + 1.3), "MARCO", sin=("+y",))
    return m


def toldo(ancho=M - 0.8, salida=3.0, alto=8.9, caida=1.3, franja=1.0):
    """Toldo a rayas, inclinado, con faldón festoneado. Ocupa x ∈ [0, ancho]."""
    m = Malla()
    n = max(2, int(round(ancho / franja)))
    fw = ancho / n
    for k in range(n):
        mat = "TOLDO_A" if k % 2 == 0 else "TOLDO_B"
        xa, xb = k * fw, (k + 1) * fw
        # lona inclinada (dos caras, para verse desde abajo)
        p = [(xa, 0.0, alto), (xb, 0.0, alto), (xb, -salida, alto - caida), (xa, -salida, alto - caida)]
        m.poligono(p, mat)  # Cycles pinta las dos caras: no se duplica (dos caras coincidentes salen negras)
        # festón: rectángulo + pico
        y = -salida
        z = alto - caida
        f = [(xa, y, z), (xa, y, z - 0.7), ((xa + xb) / 2, y, z - 1.1), (xb, y, z - 0.7), (xb, y, z)]
        m.poligono(f[::-1], mat)
    # barra de hierro y tirantes
    m.viga((0, -salida, alto - caida), (ancho, -salida, alto - caida), 0.18, "Hierro")
    m.viga((0.2, 0, alto - 1.8), (0.2, -salida, alto - caida), 0.14, "Hierro")
    m.viga((ancho - 0.2, 0, alto - 1.8), (ancho - 0.2, -salida, alto - caida), 0.14, "Hierro")
    return m


def entramado(alto=MEDIDAS["piso"], con_ventana=True):
    """Vigas de madera vistas sobre la fachada (estilo rústico de Pradoverde)."""
    m = Malla()
    y0, y1 = -0.16, 0.02
    m.caja((0, y0, 0.0), (M, y1, 0.55), "Madera_Oscura", sin=("+y",))
    m.caja((0, y0, alto - 0.55), (M, y1, alto), "Madera_Oscura", sin=("+y",))
    for x in (0.0, M - 0.55):  # los pies derechos sobresalen 2 centésimas: sin caras coincidentes con las soleras
        m.caja((x, y0 - 0.02, 0.0), (x + 0.55, y1, alto), "Madera_Oscura", sin=("+y",))
    if con_ventana:
        w, h = MEDIDAS["ventana"]
        z0 = MEDIDAS["alfeizar"]
        x0 = (M - w) / 2
        # diagonales en los paños de los lados de la ventana (sin pisar contraventanas: van por debajo)
        m.viga((0.5, y0 + 0.08, 0.5), (x0 - 1.9, y0 + 0.08, z0 - 0.4), 0.45, "Madera_Oscura")
        m.viga((M - 0.5, y0 + 0.08, 0.5), (x0 + w + 1.9, y0 + 0.08, z0 - 0.4), 0.45, "Madera_Oscura")
    else:
        m.viga((0.5, y0 + 0.08, 0.5), (M / 2, y0 + 0.08, alto - 0.5), 0.45, "Madera_Oscura")
        m.viga((M - 0.5, y0 + 0.08, 0.5), (M / 2, y0 + 0.08, alto - 0.5), 0.45, "Madera_Oscura")
        m.caja((M / 2 - 0.27, y0 - 0.02, 0.0), (M / 2 + 0.27, y1, alto), "Madera_Oscura", sin=("+y",))
    return m


def esquina(alto, semilla=0):
    """Sillares de esquina (alternos) para la esquina delantera izquierda: fachadas y = 0 (-Y) y x = 0 (-X)."""
    rng = _rng(semilla)
    m = Malla()
    z, k = 0.0, 0
    while z < alto - 0.05:
        h = min(1.3, alto - z)
        t = float(rng.uniform(0.9, 1.07))
        largo, corto = (1.9, 1.05) if k % 2 == 0 else (1.05, 1.9)
        # sillar en L (un solo prisma: dos cajas solapadas dejarían caras coincidentes, que salen negras)
        ele = [(-0.22, -0.22), (largo, -0.22), (largo, 0.3), (0.3, 0.3), (0.3, corto), (-0.22, corto)]
        m.prisma(ele, z + 0.04, z + h - 0.04, "PIEDRA", tinte=t)
        z += h
        k += 1
    return m


def cornisa(largo, alto=0.55, salida=0.38):
    m = Malla()
    m.caja((-salida, -salida, 0), (largo + salida, 0.3, alto), "PIEDRA")
    m.caja((-salida - 0.15, -salida - 0.15, alto), (largo + salida + 0.15, 0.3, alto + 0.22), "PIEDRA", tinte=0.95)
    return m


def zocalo(largo, alto=1.8, semilla=0):
    """Zócalo de sillares a lo largo de una fachada (desde la losa)."""
    rng = _rng(semilla)
    m = Malla()
    x = -0.25
    while x < largo + 0.25 - 0.05:
        l = min(float(rng.uniform(1.5, 2.6)), largo + 0.25 - x)
        m.caja((x + 0.03, -0.28, -MEDIDAS["zocalo"]), (x + l - 0.03, 0.4, alto), "Piedra_Media",
               tinte=float(rng.uniform(0.88, 1.08)))
        x += l
    return m


# ==============================================================================================================
# Tejados
# ==============================================================================================================


def faldon(m, A, B, C, Dd, rng, mat="TEJA", grosor=0.36, hilada=MEDIDAS["hilada"], teja=MEDIDAS["teja"],
           n_hiladas=None, desfase=0.0):
    """Faldón de tejas por hiladas, de la línea de alero A-B a la de cumbre Dd-C (C = Dd: triángulo).
    Cada hilada es un prisma con el borde de abajo grueso (goterón) y se parte en tejas de tono variable."""
    A, B, C, Dd = (np.asarray(p, float) for p in (A, B, C, Dd))
    nrm = np.cross(B - A, Dd - A)
    nrm /= np.linalg.norm(nrm)
    largo = np.linalg.norm((Dd + C) / 2 - (A + B) / 2)
    nh = n_hiladas or max(2, int(math.ceil(largo / hilada)))
    for k in range(nh):
        t0, t1 = k / nh, (k + 1) / nh
        L0, R0 = A + t0 * (Dd - A), B + t0 * (C - B)
        L1, R1 = A + t1 * (Dd - A), B + t1 * (C - B)
        ancho = np.linalg.norm(R0 - L0)
        nt = max(1, int(round(ancho / teja)))
        g0, g1 = nrm * grosor, nrm * 0.07
        for j in range(nt):
            s0, s1 = j / nt, (j + 1) / nt
            a0, b0 = L0 + s0 * (R0 - L0), L0 + s1 * (R0 - L0)
            a1, b1 = L1 + s0 * (R1 - L1), L1 + s1 * (R1 - L1)
            ti = float(rng.uniform(0.84, 1.1))
            m.poligono([a0 + g0, b0 + g0, b1 + g1, a1 + g1], mat, tinte=ti)  # cara de arriba
            m.poligono([a0, b0, b0 + g0, a0 + g0], mat, tinte=ti * 0.8)  # goterón
        # costados y panza
        m.poligono([L0, L0 + g0, L1 + g1, L1], mat, tinte=0.7)
        m.poligono([R0, R1, R1 + g1, R0 + g0], mat, tinte=0.7)
        m.poligono([L0, L1, R1, R0], "Madera_Oscura")


def tejado_tramo(fondo, largo=M, semilla=0, pendiente=MEDIDAS["pendiente"], alero=MEDIDAS["alero"]):
    """Tramo de tejado a dos aguas de x = 0 a x = largo, sobre muros de y = 0 a y = fondo, con la base en z = 0
    (lo alto de los muros). La cumbrera va a lo largo de X."""
    rng = _rng(semilla)
    m = Malla()
    medio = fondo / 2
    sube = medio * pendiente
    za = -alero * pendiente
    faldon(m, (0, -alero, za), (largo, -alero, za), (largo, medio, sube), (0, medio, sube), rng)
    faldon(m, (largo, fondo + alero, za), (0, fondo + alero, za), (0, medio, sube), (largo, medio, sube), rng)
    # tabla de alero
    m.caja((0, -alero - 0.05, za - 0.5), (largo, -alero + 0.25, za + 0.05), "MARCO")
    m.caja((0, fondo + alero - 0.25, za - 0.5), (largo, fondo + alero + 0.05, za + 0.05), "MARCO")
    return m


def tejado_remate(fondo, lado=-1, semilla=0, pendiente=MEDIDAS["pendiente"], alero=MEDIDAS["alero"],
                  vuelo=MEDIDAS["vuelo"]):
    """Vuelo del tejado sobre el hastial (lado -1: x ∈ [-vuelo, 0]; lado +1: x ∈ [0, vuelo]) con su tabla de canto."""
    m = tejado_tramo(fondo, vuelo, semilla, pendiente, alero)
    medio = fondo / 2
    sube = medio * pendiente
    za = -alero * pendiente
    xb = 0.0 if lado < 0 else vuelo - 0.3
    m.viga((xb + 0.15, -alero, za + 0.1), (xb + 0.15, medio, sube + 0.25), 0.5, "MARCO")
    m.viga((xb + 0.15, fondo + alero, za + 0.1), (xb + 0.15, medio, sube + 0.25), 0.5, "MARCO")
    return m.transformada(T(-vuelo if lado < 0 else 0.0, 0, 0))


def hastial(fondo, pendiente=MEDIDAS["pendiente"], oculo=True):
    """Muro triangular del hastial, en x ∈ [0, G] (la cara exterior en x = 0, mirando a -X)."""
    m = Malla()
    medio = fondo / 2
    sube = medio * pendiente
    tri = [(0, 0), (fondo, 0), (medio, sube)]
    # prisma en el plano YZ: se construye en XY y se gira
    m.anadir(Malla().prisma(tri, 0, G, "PARED"), _yz_a_x())
    if oculo and sube > 4.0:
        o = Malla()
        o.tronco((0, 0, 0), 1.25, 1.25, 0.32, 8, "PIEDRA", giro=22.5)
        o.tronco((0, 0, 0.32), 0.85, 0.85, 0.05, 8, "Vidrio", giro=22.5)
        m.anadir(o, compone(T(0.02, medio, sube * 0.42), Ry(-90)))
    return m


def _yz_a_x():
    """Devuelve una matriz que lleva el prisma construido en XY (z = grosor) a un muro en YZ con grosor en X."""
    # (x, y, z) -> (z, x, y): la base del triángulo (x) va a Y, la altura (y) va a Z, la extrusión (z) va a X.
    m = np.eye(4)
    m[:3, :3] = [[0, 0, 1], [1, 0, 0], [0, 1, 0]]
    return m


def cumbrera(largo, fondo, pendiente=MEDIDAS["pendiente"], semilla=0):
    """Caballete de tejas redondas a lo largo de la cumbre, de x = 0 a x = largo."""
    rng = _rng(semilla)
    m = Malla()
    sube = fondo / 2 * pendiente
    n = max(1, int(round(largo / 1.6)))
    for k in range(n):
        x0, x1 = k * largo / n, (k + 1) * largo / n
        pieza = Malla().tronco((0, 0, 0), 0.5, 0.46, x1 - x0 + 0.05, 6, "TEJA_B", tinte=float(rng.uniform(0.85, 1.05)))
        m.anadir(pieza, compone(T(x0, fondo / 2, sube + 0.38), Ry(90)))
    return m


def tejado_cuatro_aguas(ancho, fondo, semilla=0, pendiente=MEDIDAS["pendiente"], alero=MEDIDAS["alero"],
                        remate=True):
    """Tejado a cuatro aguas sobre un rectángulo [0, ancho] × [0, fondo] (pirámide si es cuadrado)."""
    rng = _rng(semilla)
    m = Malla()
    a, f = ancho + 2 * alero, fondo + 2 * alero
    x0, y0 = -alero, -alero
    za = -alero * pendiente
    r = min(a, f) / 2
    sube = r * pendiente
    if a >= f:
        c0, c1 = (x0 + r, y0 + r, za + sube), (x0 + a - r, y0 + r, za + sube)
    else:
        c0, c1 = (x0 + r, y0 + r, za + sube), (x0 + r, y0 + f - r, za + sube)
    A, B, Cc, Dd = (x0, y0, za), (x0 + a, y0, za), (x0 + a, y0 + f, za), (x0, y0 + f, za)
    if a >= f:
        faldon(m, A, B, c1, c0, rng)
        faldon(m, Cc, Dd, c0, c1, rng)
        faldon(m, B, Cc, c1, c1, rng)
        faldon(m, Dd, A, c0, c0, rng)
    else:
        faldon(m, A, B, c0, c0, rng)
        faldon(m, B, Cc, c1, c0, rng)
        faldon(m, Cc, Dd, c1, c1, rng)
        faldon(m, Dd, A, c0, c1, rng)
    # limas (aristas) y cumbrera
    for esq, c in ((A, c0), (B, c1 if a >= f else c0), (Cc, c1), (Dd, c0 if a >= f else c1)):
        e = np.asarray(esq, float) + np.array([0, 0, 0.35])
        m.viga(e, np.asarray(c, float) + np.array([0, 0, 0.35]), 0.6, "TEJA_B")
    if np.linalg.norm(np.subtract(c1, c0)) > 0.1:
        m.viga(np.add(c0, (0, 0, 0.38)), np.add(c1, (0, 0, 0.38)), 0.8, "TEJA_B")
    if remate:
        for c in (c0, c1):
            m.tronco((c[0], c[1], c[2] + 0.2), 0.35, 0.1, 1.8, 6, "Oro")
    for (p, q) in ((A, B), (B, Cc), (Cc, Dd), (Dd, A)):
        m.viga(np.add(p, (0, 0, -0.25)), np.add(q, (0, 0, -0.25)), 0.5, "MARCO")
    return m


def chimenea(alto=6.0):
    m = Malla()
    m.caja((-1.1, -1.1, 0), (1.1, 1.1, alto), "Ladrillo")
    m.caja((-1.45, -1.45, alto), (1.45, 1.45, alto + 0.45), "Piedra_Clara")
    m.caja((-0.7, -0.7, alto + 0.45), (0.7, 0.7, alto + 0.9), "Ladrillo", tinte=0.8)
    m.caja((-0.45, -0.45, alto + 0.9), (0.45, 0.45, alto + 0.92), "Hierro")
    return m


# ==============================================================================================================
# Mobiliario urbano y de campo
# ==============================================================================================================


def farola(alto=12.0):
    """Farola de hierro: basa de piedra, fuste con anillos, farol de cuatro cristales y remate."""
    m = Malla()
    m.tronco((0, 0, 0), 0.95, 0.8, 1.2, 8, "Piedra_Clara", giro=22.5)
    m.tronco((0, 0, 1.2), 0.5, 0.4, 0.6, 8, "Hierro")
    m.tronco((0, 0, 1.8), 0.24, 0.2, alto - 3.8, 8, "Hierro")
    for z in (3.0, alto - 3.0):
        m.tronco((0, 0, z), 0.36, 0.36, 0.25, 8, "Hierro")
    zt = alto - 2.0
    m.tronco((0, 0, zt - 0.2), 0.35, 0.7, 0.3, 4, "Hierro", giro=45)
    m.tronco((0, 0, zt + 0.1), 0.62, 0.72, 1.4, 4, "Luz_Calida", giro=45)
    for k in range(4):  # montantes del farol
        a = math.radians(45 + 90 * k)
        m.caja_c((0.7 * math.cos(a), 0.7 * math.sin(a), zt + 0.8), (0.12, 0.12, 1.45), "Hierro")
    m.tronco((0, 0, zt + 1.5), 1.05, 0.2, 0.75, 4, "Hierro", giro=45)
    m.tronco((0, 0, zt + 2.25), 0.15, 0.0, 0.6, 6, "Hierro")
    return m


def valla_madera(largo=M, semilla=0):
    rng = _rng(semilla)
    m = Malla()
    n = max(1, int(round(largo / 4)))
    for k in range(n + 1):
        x = k * largo / n
        h = 3.9 + float(rng.uniform(-0.2, 0.2))
        t = float(rng.uniform(0.85, 1.08))
        m.caja((x - 0.28, -0.28, -0.6), (x + 0.28, 0.28, h), "Madera_Media", tinte=t)
        m.tronco((x, 0, h), 0.4, 0.0, 0.45, 4, "Madera_Media", giro=45, tinte=t)
    for z in (1.5, 3.0):
        m.caja((0, -0.42, z - 0.22), (largo, -0.28, z + 0.22), "Madera_Clara", tinte=float(rng.uniform(0.9, 1.05)))
    return m


def valla_piedra(largo=M, semilla=0):
    """Muro bajo de piedra seca con albardilla."""
    rng = _rng(semilla)
    m = Malla()
    x = 0.0
    while x < largo - 0.1:
        l = min(float(rng.uniform(1.3, 2.3)), largo - x)
        for z0, z1 in ((-0.4, 1.1), (1.1, 2.1)):
            xa = x + (0.6 if z0 > 0 else 0) * (rng.uniform() > 0.5)
            pts = []
            for px in (xa, min(xa + l, largo)):
                for py in (-0.8, 0.8):
                    for pz in (z0, z1):
                        pts.append((px + rng.uniform(-0.12, 0.12), py + rng.uniform(-0.12, 0.12),
                                    pz + rng.uniform(-0.1, 0.1)))
            m.convexo(pts, "Piedra_Media", tinte=float(rng.uniform(0.82, 1.1)))
        x += l
    m.caja((-0.1, -0.95, 2.1), (largo + 0.1, 0.95, 2.55), "Piedra_Clara")
    return m


def banco():
    m = Malla()
    for x in (0.4, 4.6):
        m.caja((x - 0.2, -0.9, 0), (x + 0.2, 0.9, 1.6), "Hierro")
        m.caja((x - 0.2, 0.7, 1.6), (x + 0.2, 0.95, 3.2), "Hierro")
    for k in range(3):
        m.caja((0, -0.9 + k * 0.6, 1.6), (5, -0.4 + k * 0.6, 1.85), "Madera_Clara", tinte=1 - 0.04 * k)
    for k in range(2):
        m.caja((0, 0.75, 2.2 + k * 0.6), (5, 0.95, 2.6 + k * 0.6), "Madera_Clara")
    return m


def barril(semilla=0):
    m = Malla()
    m.torno([(1.0, 0), (1.18, 0.8), (1.22, 1.5), (1.18, 2.2), (1.0, 3.0)], 10, "Madera_Media", liso=True)
    for z in (0.35, 2.65):
        m.tronco((0, 0, z - 0.15), 1.17, 1.17, 0.3, 10, "Hierro", tapa_abajo=False, tapa_arriba=False)
    return m


def caja_madera(lado=2.4, semilla=0):
    rng = _rng(semilla)
    m = Malla()
    t = float(rng.uniform(0.9, 1.1))
    m.caja((0.1, 0.1, 0.1), (lado - 0.1, lado - 0.1, lado - 0.1), "Madera_Clara", tinte=t)
    e = 0.3
    for y0, y1 in ((-0.02, e), (lado - e, lado + 0.02)):  # marcos delantero y trasero
        m.caja((e, y0, 0), (lado - e, y1, e), "Madera_Media", tinte=t)
        m.caja((e, y0, lado - e), (lado - e, y1, lado), "Madera_Media", tinte=t)
        m.caja((-0.02, y0 - 0.01, -0.01), (e, y1 + 0.01, lado + 0.01), "Madera_Media", tinte=t)
        m.caja((lado - e, y0 - 0.01, -0.01), (lado + 0.02, y1 + 0.01, lado + 0.01), "Madera_Media", tinte=t)
    return m


def maceta(semilla=0):
    rng = _rng(semilla)
    m = Malla()
    m.tronco((0, 0, 0), 1.3, 1.6, 1.8, 8, "Piedra_Clara", giro=22.5)
    m.tronco((0, 0, 1.8), 1.7, 1.7, 0.3, 8, "Piedra_Clara", giro=22.5, tinte=0.95)
    m.esfera((0, 0, 2.6), 1.5, "Hoja_Verde", sub=1, jitter=0.15, rng=rng, escala=(1, 1, 0.8))
    flores = ["Flor_Roja", "Flor_Rosa", "Flor_Amarilla", "Flor_Lila", "Flor_Blanca"]
    c = flores[int(rng.integers(len(flores)))]
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        rr = rng.uniform(0.4, 1.2)
        m.esfera((rr * math.cos(a), rr * math.sin(a), 3.2 + rng.uniform(-0.2, 0.2)), 0.32, c, sub=0)
    return m


def puesto(semilla=0, ancho=8.0, fondo=5.0):
    """Puesto de mercado: estructura de madera, mostrador con género y toldo a rayas."""
    rng = _rng(semilla)
    m = Malla()
    for x in (0.3, ancho - 0.3):
        for y, h in ((0.3, 7.0), (fondo - 0.3, 8.4)):
            m.caja((x - 0.3, y - 0.3, 0), (x + 0.3, y + 0.3, h), "Madera_Media")
    m.caja((0, -0.2, 0), (ancho, 1.6, 3.2), "Madera_Clara")  # mostrador
    m.caja((-0.2, -0.4, 3.2), (ancho + 0.2, 1.8, 3.55), "Madera_Media")
    for k in range(4):
        m.caja((0.3 + k * ancho / 4, -0.25, 0.4), (ancho / 4 + k * ancho / 4 - 0.3, -0.2, 2.8), "Madera_Media",
               tinte=0.85)
    # género
    frutas = ["Fruta_Roja", "Fruta_Naranja", "Col", "Calabaza", "Flor_Amarilla"]
    for k in range(3):
        x0 = 0.6 + k * (ancho - 1.2) / 3
        m.anadir(caja_madera(2.0, semilla + k), compone(T(x0, -0.1, 3.55), S(1.0, 0.85, 0.5)))
        f = frutas[int(rng.integers(len(frutas)))]
        for j in range(5):
            m.esfera((x0 + 0.5 + rng.uniform(0, 1.0), 0.75 + rng.uniform(-0.3, 0.3), 4.7 + rng.uniform(0, 0.3)), 0.42,
                     f, sub=0)
    # toldo inclinado hacia delante
    n = 8
    for k in range(n):
        mat = "TOLDO_A" if k % 2 == 0 else "TOLDO_B"
        xa, xb = -0.4 + k * (ancho + 0.8) / n, -0.4 + (k + 1) * (ancho + 0.8) / n
        p = [(xa, fondo + 0.3, 8.9), (xb, fondo + 0.3, 8.9), (xb, -1.6, 6.8), (xa, -1.6, 6.8)]
        m.poligono(p, mat)
        f = [(xa, -1.6, 6.8), (xa, -1.6, 6.1), ((xa + xb) / 2, -1.6, 5.7), (xb, -1.6, 6.1), (xb, -1.6, 6.8)]
        m.poligono(f[::-1], mat)
    return m


def cartel(emblema="bolsa", semilla=0):
    """Cartel colgante de tienda con un emblema sencillo (bolsa, espada, gema, yunque, pan, pocion)."""
    m = Malla()
    m.caja((-0.15, -3.0, 2.6), (0.15, 0.0, 2.9), "Hierro")
    m.viga((0, -0.1, 1.2), (0, -1.6, 2.7), 0.2, "Hierro")
    m.caja((-0.12, -2.8, 2.3), (0.12, -2.7, 2.6), "Hierro")
    m.caja((-0.12, -1.0, 2.3), (0.12, -0.9, 2.6), "Hierro")
    m.caja((-0.18, -3.0, -0.2), (0.18, -0.7, 2.3), "Madera_Media")
    m.caja((-0.25, -2.95, -0.1), (0.25, -0.75, 2.2), "Pintura_Crema")
    e = Malla()
    if emblema == "bolsa":
        e.esfera((0, 0, 0), 0.7, "Madera_Clara", sub=1, escala=(1, 1, 0.9))
        e.tronco((0, 0, 0.5), 0.3, 0.45, 0.5, 6, "Madera_Clara")
    elif emblema == "espada":
        e.caja((-0.12, -0.12, -0.6), (0.12, 0.12, 1.0), "Hierro", tinte=2.2)
        e.caja((-0.12, -0.5, -0.4), (0.12, 0.5, -0.25), "Oro")
        e.caja((-0.12, -0.1, -1.0), (0.12, 0.1, -0.4), "Madera_Oscura")
    elif emblema == "gema":
        e.esfera((0, 0, 0), 0.75, "Toldo_Azul", sub=0, escala=(0.6, 1, 1.2))
    elif emblema == "yunque":
        e.caja((-0.2, -0.7, 0.1), (0.2, 0.7, 0.45), "Hierro", tinte=1.6)
        e.caja((-0.2, -0.3, -0.5), (0.2, 0.3, 0.1), "Hierro", tinte=1.6)
    elif emblema == "pan":
        e.esfera((0, 0, 0), 0.7, "Madera_Clara", sub=1, escala=(0.5, 1.3, 0.7))
    elif emblema == "pocion":
        e.esfera((0, 0, -0.2), 0.6, "Fruta_Roja", sub=1)
        e.tronco((0, 0, 0.3), 0.22, 0.22, 0.6, 6, "Vidrio")
    for lado in (-1, 1):
        m.anadir(e, T(0.3 * lado, -1.85, 1.05))
    return m


def tablon_misiones(semilla=0):
    """Tablón de misiones: dos postes, tejadillo, tablero con papeles clavados y un «!» dorado encima."""
    rng = _rng(semilla)
    m = Malla()
    for x in (-4.2, 4.2):
        m.caja((x - 0.45, -0.45, 0), (x + 0.45, 0.45, 10.2), "Madera_Oscura")
        m.caja((x - 0.8, -0.8, 0), (x + 0.8, 0.8, 0.8), "Piedra_Clara")
    m.caja((-3.8, -0.25, 2.6), (3.8, 0.25, 8.4), "Madera_Media")  # tablero
    m.caja((-4.0, -0.4, 8.4), (4.0, 0.4, 8.8), "Madera_Oscura")
    m.caja((-4.0, -0.4, 2.3), (4.0, 0.4, 2.7), "Madera_Oscura")
    m.caja((-3.4, -0.4, 2.7), (-3.0, 0.4, 8.4), "Madera_Oscura", tinte=0.9)
    m.caja((3.0, -0.4, 2.7), (3.4, 0.4, 8.4), "Madera_Oscura", tinte=0.9)
    # papeles en las dos caras
    for cara in (-1, 1):
        for k in range(7):
            x = rng.uniform(-2.5, 2.5)
            z = rng.uniform(3.2, 7.4)
            w, h = rng.uniform(0.9, 1.5), rng.uniform(1.0, 1.6)
            mat = "Papel" if rng.uniform() > 0.3 else "Papel_Amarillo"
            g = rng.uniform(-12, 12)
            hoja = Malla().caja((-w / 2, -0.04, -h / 2), (w / 2, 0.04, h / 2), mat)
            hoja.caja((-0.1, -0.1, h / 2 - 0.3), (0.1, 0.06, h / 2 - 0.1), "Fruta_Roja")
            m.anadir(hoja, compone(T(x, cara * 0.3, z), Rz(0 if cara > 0 else 180), Ry(g)))
    # tejadillo
    faldon(m, (-5.2, -2.2, 10.0), (5.2, -2.2, 10.0), (5.2, 0, 11.6), (-5.2, 0, 11.6), rng)
    faldon(m, (5.2, 2.2, 10.0), (-5.2, 2.2, 10.0), (-5.2, 0, 11.6), (5.2, 0, 11.6), rng)
    m.viga((-5.2, 0, 11.9), (5.2, 0, 11.9), 0.7, "TEJA_B")
    # «!» dorado
    m.caja((-0.45, -0.3, 12.8), (0.45, 0.3, 15.6), "Oro")
    m.caja((-0.45, -0.3, 11.9), (0.45, 0.3, 12.5), "Oro")
    return m


def pozo():
    m = Malla()
    m.tronco((0, 0, 0), 2.6, 2.6, 2.8, 10, "Piedra_Media")
    m.tronco((0, 0, 2.8), 2.85, 2.85, 0.4, 10, "Piedra_Clara")
    m.tronco((0, 0, 2.5), 1.9, 1.9, 0.33, 10, "Agua_Fuente", tapa_abajo=False)
    for y in (-2.3, 2.3):
        m.caja((-0.3, y - 0.3, 2.8), (0.3, y + 0.3, 8.0), "Madera_Oscura")
    m.viga((0, -2.6, 6.6), (0, 2.6, 6.6), 0.35, "Madera_Media")
    m.tronco((0, 0, 4.3), 0.45, 0.55, 0.9, 8, "Madera_Media")
    m.viga((0, 0, 5.2), (0, 0, 6.5), 0.08, "Paja")
    rng = _rng(4)
    faldon(m, (-3.5, 3.2, 7.4), (-3.5, -3.2, 7.4), (0, -3.2, 9.6), (0, 3.2, 9.6), rng)
    faldon(m, (3.5, -3.2, 7.4), (3.5, 3.2, 7.4), (0, 3.2, 9.6), (0, -3.2, 9.6), rng)
    return m


def carro():
    m = Malla()
    m.caja((-3.0, -1.8, 1.8), (3.0, 1.8, 2.3), "Madera_Media")
    for y in (-1.8, 1.8):
        m.caja((-3.0, y - 0.2, 2.3), (3.0, y + 0.2, 3.5), "Madera_Clara")
    m.caja((-3.0, -1.8, 2.3), (-2.6, 1.8, 3.5), "Madera_Clara")
    for y in (-2.1, 2.1):
        rueda = Malla().tronco((0, 0, -0.2), 1.6, 1.6, 0.4, 10, "Madera_Oscura")
        rueda.tronco((0, 0, -0.3), 0.4, 0.4, 0.6, 6, "Hierro")
        m.anadir(rueda, compone(T(0.6, y, 1.6), Rx(90)))
    m.viga((3.0, -0.6, 2.0), (7.0, -0.6, 1.0), 0.3, "Madera_Media")
    m.viga((3.0, 0.6, 2.0), (7.0, 0.6, 1.0), 0.3, "Madera_Media")
    for k in range(4):
        m.anadir(Malla().tronco((0, 0, 0), 0.9, 0.9, 2.2, 8, "Paja"), compone(T(-1.8 + k * 1.3, 0, 3.4), Rx(90)))
    return m


def pajar(semilla=0):
    rng = _rng(semilla)
    m = Malla()
    m.torno([(3.0, 0), (3.2, 1.6), (2.8, 3.4), (1.8, 4.8), (0.6, 5.7), (0.0, 6.0)], 9, "Paja", liso=False,
            giro=float(rng.uniform(0, 40)))
    m.viga((0, 0, 5.5), (0, 0, 7.0), 0.25, "Madera_Media")
    return m


def espantapajaros():
    m = Malla()
    m.caja((-0.2, -0.2, 0), (0.2, 0.2, 7.5), "Madera_Media")
    m.caja((-2.6, -0.15, 5.6), (2.6, 0.15, 5.9), "Madera_Media")
    m.tronco((0, 0, 3.4), 1.2, 1.5, 2.6, 6, "Pintura_Azul")
    m.caja((-2.2, -0.5, 5.3), (2.2, 0.5, 6.1), "Pintura_Roja")
    m.esfera((0, 0, 6.8), 0.8, "Paja", sub=1)
    m.tronco((0, 0, 7.3), 1.6, 1.6, 0.15, 10, "Paja")
    m.tronco((0, 0, 7.45), 0.75, 0.15, 1.4, 8, "Paja")
    return m


def portal(ancho=16.0):
    """Entrada de ciudad: dos pilares de sillería con farol encima y un tramo de muro bajo a cada lado."""
    m = Malla()
    for sgn in (-1, 1):
        x = sgn * (ancho / 2 + 1.8)
        m.caja((x - 1.8, -1.8, -1.0), (x + 1.8, 1.8, 1.2), "Piedra_Media")
        m.caja((x - 1.5, -1.5, 1.2), (x + 1.5, 1.5, 11.0), "Piedra_Clara")
        for z in (3.0, 6.0, 9.0):
            m.caja((x - 1.62, -1.62, z), (x + 1.62, 1.62, z + 0.25), "Piedra_Media")
        m.caja((x - 2.0, -2.0, 11.0), (x + 2.0, 2.0, 11.8), "Piedra_Clara")
        m.tronco((x, 0, 11.8), 1.4, 0.5, 1.2, 4, "Piedra_Clara", giro=45)
        m.anadir(farola(4.5).transformada(T(0, 0, 0)), T(x, 0, 12.4))
        m.anadir(valla_piedra(10.0, semilla=7 + sgn), T(x + (1.8 if sgn > 0 else -11.8), -0.2, 0))
    return m


def poste_indicador(rumbos=(0.0, 120.0, 230.0)):
    """Poste de cruce con tablillas en forma de flecha (una por rumbo, en grados desde +X)."""
    m = Malla()
    m.caja((-0.35, -0.35, -1.0), (0.35, 0.35, 9.0), "Madera_Oscura")
    m.tronco((0, 0, 9.0), 0.55, 0.0, 0.7, 4, "Madera_Oscura", giro=45)
    for k, r in enumerate(rumbos):
        f = Malla()
        f.prisma([(0.3, -0.5), (3.6, -0.5), (4.5, 0.0), (3.6, 0.5), (0.3, 0.5)], 0, 0.25, "Madera_Clara")
        f.prisma([(0.6, -0.3), (3.4, -0.3), (3.9, 0.0), (3.4, 0.3), (0.6, 0.3)], 0.25, 0.3, "Pintura_Crema")
        m.anadir(f, compone(T(0, 0, 7.8 - 1.25 * k), Rz(r), Rx(90)))
    return m


# ==============================================================================================================
# Vegetación y rocas (variantes por semilla; en la región se instancian por miles)
# ==============================================================================================================


def arbol_frondoso(semilla=0, alto=None):
    rng = _rng(semilla)
    h = alto or float(rng.uniform(17, 26))
    m = Malla()
    t = h * 0.42
    m.tronco((0, 0, -1.0), 1.15, 0.75, t + 1.0, 6, "Corteza", giro=float(rng.uniform(0, 60)))
    # dos ramas
    for k in range(2):
        a = rng.uniform(0, 2 * math.pi)
        m.viga((0, 0, t * 0.8), (math.cos(a) * h * 0.18, math.sin(a) * h * 0.18, t + h * 0.15), 0.7, "Corteza")
    hoja = ["Hoja_Verde", "Hoja_Clara", "Hoja_Oscura"][int(rng.integers(3))]
    r = h * 0.3
    m.esfera((0, 0, t + r * 0.95), r, hoja, sub=1, jitter=0.12, rng=rng, escala=(1, 1, 0.85))
    for k in range(int(rng.integers(3, 5))):
        a = rng.uniform(0, 2 * math.pi)
        d = r * rng.uniform(0.55, 0.8)
        rr = r * rng.uniform(0.55, 0.72)
        m.esfera((math.cos(a) * d, math.sin(a) * d, t + r * rng.uniform(0.5, 1.2)), rr, hoja, sub=1, jitter=0.14,
                 rng=rng, tinte=float(rng.uniform(0.88, 1.1)), escala=(1, 1, 0.85))
    return m


def pino(semilla=0, alto=None):
    rng = _rng(semilla)
    h = alto or float(rng.uniform(22, 34))
    m = Malla()
    m.tronco((0, 0, -1.0), 0.9, 0.5, h * 0.35, 6, "Corteza")
    n = 4
    for k in range(n):
        z0 = h * (0.18 + 0.19 * k)
        r = h * (0.27 - 0.05 * k)
        alto_c = h * (0.42 - 0.04 * k)
        cono = Malla().tronco((0, 0, 0), r, r * 0.08, alto_c, 7, "Hoja_Pino", giro=float(rng.uniform(0, 50)),
                              tinte=float(rng.uniform(0.9, 1.08)))
        # bajo de cada piso un poco más ancho y caído
        m.anadir(cono, T(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), z0))
    return m


def abedul(semilla=0, alto=None):
    rng = _rng(semilla)
    h = alto or float(rng.uniform(18, 26))
    m = Malla()
    m.tronco((0, 0, -1.0), 0.55, 0.35, h * 0.75, 6, "Corteza_Abedul")
    for k in range(4):  # manchas oscuras del tronco
        z = rng.uniform(1.5, h * 0.6)
        m.caja_c((0.45, 0, z), (0.25, 0.5, 0.25), "Madera_Oscura")
    hoja = ["Hoja_Clara", "Hoja_Verde"][int(rng.integers(2))]
    for k in range(4):
        a = rng.uniform(0, 2 * math.pi)
        m.esfera((math.cos(a) * 1.5, math.sin(a) * 1.5, h * (0.6 + 0.08 * k)), h * 0.16, hoja, sub=1, jitter=0.15,
                 rng=rng, escala=(1, 1, 1.35), tinte=float(rng.uniform(0.9, 1.1)))
    return m


def arbol_flor(semilla=0, alto=None):
    """Cerezo en flor: para los pueblos (rosa claro, el toque cálido del valle)."""
    m = arbol_frondoso(semilla, alto or float(_rng(semilla).uniform(13, 17)))
    for i, mt in enumerate(m.mat):
        if mt.startswith("Hoja"):
            m.mat[i] = "Flor_Rosa"
    return m


def arbusto(semilla=0):
    rng = _rng(semilla)
    m = Malla()
    hoja = ["Hoja_Verde", "Hoja_Oscura", "Hoja_Clara"][int(rng.integers(3))]
    for k in range(int(rng.integers(2, 4))):
        m.esfera((rng.uniform(-1.4, 1.4), rng.uniform(-1.4, 1.4), 1.4), rng.uniform(1.6, 2.4), hoja, sub=1,
                 jitter=0.18, rng=rng, escala=(1, 1, 0.75), tinte=float(rng.uniform(0.9, 1.1)))
    return m


def roca(semilla=0, tam=None):
    rng = _rng(semilla)
    s = tam or float(rng.uniform(2.5, 7))
    # puntos de un elipsoide deformado; la base queda enterrada
    d = rng.normal(size=(22, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    pts = d * np.array([1.0, rng.uniform(0.6, 0.9), rng.uniform(0.5, 0.75)]) * s * rng.uniform(0.8, 1.15, (22, 1))
    pts[:, 2] = np.maximum(pts[:, 2], -0.3 * s) + 0.15 * s
    m = Malla().convexo(pts, "Piedra_Media", tinte=float(rng.uniform(0.8, 1.1)))
    return m


def mata_hierba(semilla=0):
    rng = _rng(semilla)
    m = Malla()
    for k in range(7):
        a = rng.uniform(0, 2 * math.pi)
        h = rng.uniform(1.4, 2.6)
        b = np.array([math.cos(a), math.sin(a), 0]) * 0.25
        tip = np.array([math.cos(a) * rng.uniform(0.6, 1.2), math.sin(a) * rng.uniform(0.6, 1.2), h])
        lat = np.array([-math.sin(a), math.cos(a), 0]) * 0.28
        p = [b - lat, b + lat, tip]
        m.poligono(p, "Hierba", tinte=float(rng.uniform(0.85, 1.15)))
    return m


def mata_flores(semilla=0):
    rng = _rng(semilla)
    m = mata_hierba(semilla)
    c = ["Flor_Roja", "Flor_Amarilla", "Flor_Blanca", "Flor_Lila", "Flor_Rosa"][int(rng.integers(5))]
    for k in range(int(rng.integers(3, 6))):
        m.esfera((rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), rng.uniform(1.5, 2.4)), 0.28, c, sub=0)
    return m


# ==============================================================================================================
# Piezas especiales
# ==============================================================================================================


def fuente(radio=9.0):
    """Fuente de la plaza: pilón octogonal, dos tazas, surtidor y caños de agua."""
    m = Malla()
    n = 8
    g = 22.5
    m.tronco((0, 0, -0.6), radio + 1.2, radio + 1.2, 0.8, n, "Piedra_Media", giro=g)  # grada
    m.tronco((0, 0, 0.2), radio, radio, 2.4, n, "Piedra_Clara", giro=g, tapa_arriba=False)  # pretil exterior
    m.tronco((0, 0, 0.2), radio - 1.0, radio - 1.0, 2.4, n, "Piedra_Clara", giro=g, tapa_abajo=False,
             tapa_arriba=False)
    # albardilla del pretil (anillo)
    ang = np.radians(g) + 2 * np.pi * np.arange(n) / n
    for i in range(n):
        a0, a1 = ang[i], ang[(i + 1) % n]
        ro, ri = radio + 0.35, radio - 1.3
        p = [(ri * math.cos(a0), ri * math.sin(a0)), (ro * math.cos(a0), ro * math.sin(a0)),
             (ro * math.cos(a1), ro * math.sin(a1)), (ri * math.cos(a1), ri * math.sin(a1))]
        m.prisma(p, 2.6, 3.1, "Piedra_Clara", tinte=0.96 + 0.06 * (i % 2))
    m.tronco((0, 0, 0.2), radio - 1.0, radio - 1.0, 1.8, n, "Agua_Fuente", giro=g, tapa_abajo=False)  # agua
    # fuste y tazas (torneadas, sombreado liso)
    m.torno([(1.9, 2.0), (1.5, 3.0), (1.2, 6.0), (1.5, 7.0)], 12, "Piedra_Clara")
    m.torno([(1.4, 6.8), (3.0, 7.4), (4.6, 8.4), (4.8, 8.9), (4.4, 9.0), (1.0, 8.6)], 16, "Piedra_Clara")
    m.tronco((0, 0, 8.55), 4.3, 4.3, 0.25, 16, "Agua_Fuente", liso=True, tapa_abajo=False)
    m.torno([(0.9, 8.6), (0.7, 10.0), (0.9, 11.2)], 10, "Piedra_Clara")
    m.torno([(0.8, 11.0), (2.0, 11.5), (2.4, 12.2), (2.1, 12.3), (0.5, 12.0)], 12, "Piedra_Clara")
    m.tronco((0, 0, 11.95), 2.0, 2.0, 0.2, 12, "Agua_Fuente", liso=True, tapa_abajo=False)
    m.torno([(0.45, 12.0), (0.3, 13.2), (0.55, 13.6), (0.0, 14.4)], 8, "Oro")
    # surtidor y caños
    m.torno([(0.35, 14.0), (0.18, 15.6), (0.0, 16.2)], 6, "Agua_Chorro")
    for k in range(8):
        a = 2 * math.pi * k / 8
        p0 = np.array([2.3 * math.cos(a), 2.3 * math.sin(a), 12.1])
        p1 = np.array([3.3 * math.cos(a), 3.3 * math.sin(a), 10.8])
        p2 = np.array([3.8 * math.cos(a), 3.8 * math.sin(a), 9.0])
        m.viga(p0, p1, 0.13, "Agua_Chorro")
        m.viga(p1, p2, 0.13, "Agua_Chorro")
        q0 = np.array([4.7 * math.cos(a), 4.7 * math.sin(a), 8.8])
        q1 = np.array([5.9 * math.cos(a), 5.9 * math.sin(a), 6.0])
        q2 = np.array([6.4 * math.cos(a), 6.4 * math.sin(a), 2.0])
        m.viga(q0, q1, 0.16, "Agua_Chorro")
        m.viga(q1, q2, 0.16, "Agua_Chorro")
    return m


def reloj(radio=3.4):
    """Esfera de reloj en el plano XZ, mirando a -Y."""
    m = Malla()
    disco = Malla().tronco((0, 0, 0), radio + 0.5, radio + 0.5, 0.35, 16, "Oro", liso=False)
    disco.tronco((0, 0, 0.35), radio, radio, 0.12, 16, "Papel")
    for k in range(12):
        a = 2 * math.pi * k / 12
        largo = 0.9 if k % 3 == 0 else 0.5
        disco.caja_c(((radio - 0.6) * math.cos(a), (radio - 0.6) * math.sin(a), 0.5), (largo, 0.22, 0.1), "Hierro")
    disco.caja((-0.15, -0.15, 0.55), (0.15, radio * 0.55, 0.68), "Hierro")  # horaria
    disco.caja((-0.1, -0.1, 0.68), (radio * 0.82, 0.1, 0.8), "Hierro")  # minutero
    m.anadir(disco, Rx(90))
    return m


def torre_reloj(semilla=3):
    """Torre del reloj de Aurora (~92 studs): basa de piedra, fuste de yeso con esquinas de sillar, cuerpo del reloj,
    campanario con arcos y chapitel de teja roja."""
    rng = _rng(semilla)
    m = Malla()
    a = 14.0
    # basa
    m.caja((-a / 2 - 1, -a / 2 - 1, -1.0), (a / 2 + 1, a / 2 + 1, 6.0), "Piedra_Media")
    m.caja((-a / 2 - 1.3, -a / 2 - 1.3, 6.0), (a / 2 + 1.3, a / 2 + 1.3, 6.6), "Piedra_Clara")
    # puerta en la basa
    m.anadir(puerta(4.4, 5.8, semilla, farolillo=False), T(-2.2, -a / 2 - 1, 0))
    # fuste
    m.caja((-a / 2, -a / 2, 6.6), (a / 2, a / 2, 52.0), "Yeso_Crema")
    for (sx, sy, r) in ((-1, -1, 0), (1, -1, 90), (1, 1, 180), (-1, 1, 270)):
        m.anadir(esquina(52.0 - 6.6, semilla + r), compone(T(sx * a / 2, sy * a / 2, 6.6), Rz(r)))
    # ventanas estrechas del fuste en cada cara
    for r in (0, 90, 180, 270):
        for z in (16.0, 30.0):  # el fuste es macizo: la ventana se adelanta hasta que el cristal asoma
            m.anadir(ventana(2.2, 4.4, contraventanas=False), compone(Rz(r), T(-1.1, -a / 2 - 0.7, z)))
        m.anadir(cornisa(a, 0.8, 0.6), compone(Rz(r), T(-a / 2, -a / 2, 40.0)))
    # cuerpo del reloj
    m.caja((-a / 2 - 0.8, -a / 2 - 0.8, 41.0), (a / 2 + 0.8, a / 2 + 0.8, 54.0), "Piedra_Clara")
    for r in (0, 90, 180, 270):
        m.anadir(reloj(4.4), compone(Rz(r), T(0, -a / 2 - 0.8, 47.5)))
        m.anadir(cornisa(a + 1.6, 0.8, 0.7), compone(Rz(r), T(-a / 2 - 0.8, -a / 2 - 0.8, 54.0)))
    # campanario: pilares en las esquinas y arcos (dos por cara)
    z0, z1 = 55.5, 66.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            xa, xb = (a / 2 - 1.8, a / 2) if sx > 0 else (-a / 2, -a / 2 + 1.8)
            ya, yb = (a / 2 - 1.8, a / 2) if sy > 0 else (-a / 2, -a / 2 + 1.8)
            m.caja((xa, ya, z0), (xb, yb, z1), "Yeso_Crema")
    for r in (0, 90, 180, 270):
        cara = Malla()
        cara.caja((-1.0, 0, z0), (1.0, 1.2, z1), "Yeso_Crema")  # parteluz
        # dos vanos de medio punto por cara: enjutas macizas y dovelas que sobresalen
        for cx in (-3.0, 3.0):
            ancho = 2.0
            zc = z1 - 3.0
            n = 7
            arco = [(cx + ancho * math.cos(math.pi * k / n), zc + ancho * math.sin(math.pi * k / n))
                    for k in range(n, -1, -1)]
            # contorno: esquina izq. de abajo, arco de izquierda a derecha, esquina der., arriba der., arriba izq.
            contorno = arco + [(cx + ancho, z1), (cx - ancho, z1)]
            cara.anadir(Malla().prisma(contorno, 0.0, 1.2, "Yeso_Crema"), compone(T(0, 1.2, 0), Rx(90)))
            for k in range(n):
                a0 = math.pi * k / n
                a1 = math.pi * (k + 1) / n
                p = [(cx + ancho * math.cos(a0), zc + ancho * math.sin(a0)),
                     (cx + (ancho + 0.7) * math.cos(a0), zc + (ancho + 0.7) * math.sin(a0)),
                     (cx + (ancho + 0.7) * math.cos(a1), zc + (ancho + 0.7) * math.sin(a1)),
                     (cx + ancho * math.cos(a1), zc + ancho * math.sin(a1))]
                dov = Malla().prisma(p, -0.3, 1.2, "Piedra_Clara", tinte=float(rng.uniform(0.9, 1.05)))
                cara.anadir(dov, compone(T(0, 0.9, 0), Rx(90)))
        # tímpano macizo por encima de los arcos
        cara.caja((-a / 2, -0.2, z1 - 0.4), (a / 2, 1.2, z1), "Yeso_Crema")
        cara.caja((-a / 2, 0.2, z0), (a / 2, 0.5, z0 + 1.6), "Piedra_Clara")  # antepecho
        m.anadir(cara, compone(Rz(r), T(0, -a / 2, 0)))
    # campana
    m.torno([(0.0, 0.0), (2.3, 0.0), (2.0, 0.6), (1.5, 2.6), (1.4, 3.6), (0.8, 4.2), (0.0, 4.3)], 12, "Oro",
            c=(0, 0, z0 + 2.6))
    m.viga((-a / 2, 0, z0 + 7.2), (a / 2, 0, z0 + 7.2), 0.6, "Madera_Oscura")
    for r in (0, 90, 180, 270):
        m.anadir(cornisa(a, 0.9, 0.9), compone(Rz(r), T(-a / 2, -a / 2, z1)))
    # chapitel
    chap = tejado_cuatro_aguas(a, a, semilla, pendiente=2.6, alero=1.4, remate=False)
    m.anadir(chap, T(-a / 2, -a / 2, z1 + 1.1))
    zt = z1 + 1.1 + (a / 2 + 1.4) * 2.6 - 1.4 * 2.6
    m.tronco((0, 0, zt - 0.5), 0.9, 0.5, 2.0, 8, "Oro")
    m.esfera((0, 0, zt + 2.0), 0.8, "Oro", sub=1, liso=True)
    m.viga((0, 0, zt + 2.5), (0, 0, zt + 7.5), 0.25, "Hierro")
    m.poligono([(0, 0, zt + 7.3), (0, 0, zt + 5.4), (3.6, 0, zt + 6.35)], "Toldo_Rojo")  # banderola
    return m


def molino(semilla=0, angulo_aspas=20.0):
    """Molino de viento: torre de piedra troncocónica encalada, caperuza cónica roja y cuatro aspas de celosía."""
    rng = _rng(semilla)
    m = Malla()
    n = 10
    # torno de 10 lados con giro 0: hay una cara plana mirando a -Y (y a cada múltiplo de 36°)
    m.torno([(7.6, 1.4), (6.0, 26.0), (6.4, 26.2), (6.4, 27.0)], n, "Yeso_Blanco", liso=False, giro=0)
    m.tronco((0, 0, -1.0), 8.7, 8.5, 2.6, n, "Piedra_Media", giro=0)  # zócalo
    apotema = math.cos(math.pi / n)

    def radio_en(z):
        return (7.6 - 1.6 * (z - 1.4) / 24.6) * apotema

    inclinacion = math.degrees(math.atan(1.6 / 24.6 * apotema))
    # puerta y ventanucos (la torre es maciza: se adelantan lo justo para que asome la hoja y el cristal)
    m.anadir(puerta(3.4, 6.4, semilla, farolillo=False), compone(T(-1.7, -radio_en(1.6) - 0.75, 1.6),
                                                                  Rx(-inclinacion)))
    for z, r in ((11.0, 72), (18.0, 180), (14.0, 288)):
        m.anadir(ventana(1.8, 2.6, contraventanas=True),
                 compone(Rz(r), T(-0.9, -radio_en(z) - 0.7, z), Rx(-inclinacion)))
    # caperuza
    m.torno([(6.9, 26.6), (6.6, 28.4), (4.6, 32.6), (1.4, 35.6), (0.0, 36.4)], 12, "TEJA", liso=False)
    for k in range(12):  # tablas de la caperuza (relieve)
        a = 2 * math.pi * (k + 0.5) / 12
        m.viga((6.95 * math.cos(a), 6.95 * math.sin(a), 26.7), (1.2 * math.cos(a), 1.2 * math.sin(a), 35.8), 0.35,
               "TEJA_B")
    m.tronco((0, 0, 35.9), 0.4, 0.0, 2.0, 6, "Hierro")
    # eje y aspas (miran a -Y)
    eje = (0, -6.4, 30.0)
    m.anadir(Malla().tronco((0, 0, 0), 1.2, 0.9, 3.5, 8, "Madera_Oscura"), compone(T(*eje), Rx(90)))
    aspas = Malla()
    largo = 25.0
    for k in range(4):
        a = Malla()
        a.caja((-0.5, -0.5, 0), (0.5, 0.5, largo), "Madera_Oscura")  # palo
        # celosía: largueros y travesaños de un lado, con la tela
        a.caja((0.5, -0.25, 5.0), (4.6, 0.25, 5.3), "Madera_Media")
        a.caja((4.4, -0.25, 5.0), (4.7, 0.25, largo), "Madera_Media")
        for j in range(9):
            z = 5.0 + j * (largo - 5.0) / 8.5
            a.caja((0.5, -0.22, z), (4.6, 0.22, z + 0.22), "Madera_Media")
        a.caja((0.6, -0.08, 5.3), (4.4, 0.08, largo - 0.2), "Tela_Vela", tinte=float(rng.uniform(0.9, 1.05)))
        aspas.anadir(a, Ry(90 * k))
    m.anadir(aspas, compone(T(eje[0], eje[1] - 3.3, eje[2]), Ry(angulo_aspas), Rx(0)))
    return m


def puente(largo=64.0, ancho=13.0, alto=8.0, arcos=3, semilla=0):
    """Puente de piedra de `arcos` ojos a lo largo de X, centrado en el origen, con el tablero en z = 0.
    Pila con tajamares, dovelas marcadas, pretiles con albardilla y farolas en los extremos."""
    rng = _rng(semilla)
    m = Malla()
    L = largo
    w = ancho / 2
    luz = L / (arcos + 0.6 * (arcos - 1) + 0.6)
    pila = 0.6 * luz
    x = -L / 2 + 0.3 * luz
    centros = []
    for k in range(arcos):
        centros.append(x + luz / 2)
        x += luz + pila
    # tablero macizo por encima de los arcos: se construye por perfiles (de lado) con el intradós recortado
    n = 10
    perfil_bajo = []
    xs = np.linspace(-L / 2, L / 2, 120)
    for xv in xs:
        z = -12.0  # cimiento por defecto (pilas y estribos)
        for c in centros:
            if abs(xv - c) < luz / 2:
                r = luz / 2
                z = -alto + math.sqrt(max(r * r - (xv - c) ** 2, 0)) * (alto * 0.85 / r)
        perfil_bajo.append(z)
    perfil_bajo = np.array(perfil_bajo)
    # se hace como tiras verticales (prismas) de piedra con tinte por bloque
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        zb = min(perfil_bajo[i], perfil_bajo[i + 1])
        m.caja((x0, -w + 0.8, zb), (x1, w - 0.8, -0.6), "Piedra_Media", tinte=float(rng.uniform(0.92, 1.04)))
    # dovelas de cada arco en las dos caras
    for c in centros:
        r = luz / 2
        k_z = alto * 0.85 / r
        for j in range(n):
            a0, a1 = math.pi * j / n, math.pi * (j + 1) / n
            p = []
            for (aa, rr) in ((a0, r), (a0, r + 1.6), (a1, r + 1.6), (a1, r)):
                p.append((c + rr * math.cos(aa), -alto + rr * math.sin(aa) * k_z * (1 if rr == r else 0.92)))
            for lado in (-1, 1):
                dov = Malla().prisma(p, 0, 0.5, "Piedra_Clara", tinte=float(rng.uniform(0.88, 1.06)))
                yy = -w + 0.3 if lado < 0 else w - 0.8
                m.anadir(dov, compone(T(0, yy + 0.5, 0), Rx(90)))
    # tímpanos (paramentos) entre arcos: cajas de sillares
    for i in range(len(xs) - 1):
        x0, x1 = xs[i], xs[i + 1]
        zb = min(perfil_bajo[i], perfil_bajo[i + 1]) + 1.3
        for lado in (-1, 1):
            y0, y1 = (-w + 0.3, -w + 0.8) if lado < 0 else (w - 0.8, w - 0.3)
            if zb < -0.6:
                m.caja((x0, y0, zb), (x1, y1, -0.6), "Piedra_Media", tinte=float(rng.uniform(0.9, 1.05)))
    # tajamares en las pilas
    for k in range(arcos - 1):
        xp = (centros[k] + centros[k + 1]) / 2
        for lado in (-1, 1):
            tri = [(xp - pila / 2, lado * (w - 0.3)), (xp + pila / 2, lado * (w - 0.3)), (xp, lado * (w + pila * 0.7))]
            if lado < 0:
                tri = tri[::-1]
            m.prisma(tri, -12.0, -alto * 0.45, "Piedra_Media")
            # sombrerete del tajamar
            m.tronco((xp, lado * (w + pila * 0.2), -alto * 0.45), pila * 0.62, 0.0, 2.2, 3, "Piedra_Clara",
                     giro=90 if lado > 0 else -90)
    # calzada, imposta y pretiles
    m.caja((-L / 2 - 2, -w + 0.3, -0.6), (L / 2 + 2, w - 0.3, 0.0), "Piedra_Oscura")
    m.caja((-L / 2 - 2, -w, -1.2), (L / 2 + 2, -w + 0.6, -0.4), "Piedra_Clara")
    m.caja((-L / 2 - 2, w - 0.6, -1.2), (L / 2 + 2, w, -0.4), "Piedra_Clara")
    for lado in (-1, 1):
        y0 = -w if lado < 0 else w - 1.4
        x = -L / 2 - 2
        while x < L / 2 + 2 - 0.1:
            l = min(float(rng.uniform(1.8, 2.8)), L / 2 + 2 - x)
            m.caja((x + 0.04, y0, 0.0), (x + l - 0.04, y0 + 1.4, 2.8), "Piedra_Media", tinte=float(rng.uniform(0.88, 1.06)))
            x += l
        m.caja((-L / 2 - 2.1, y0 - 0.15, 2.8), (L / 2 + 2.1, y0 + 1.55, 3.3), "Piedra_Clara")
        for xe in (-L / 2 - 1.5, L / 2 + 1.5):
            m.caja((xe - 1.2, y0 - 0.3, 0.0), (xe + 1.2, y0 + 1.7, 4.2), "Piedra_Clara")
            m.anadir(farola(10.0), T(xe, y0 + 0.7, 4.2))
    return m


# ==============================================================================================================
# Catálogo (para el .blend del kit y la hoja de piezas)
# ==============================================================================================================

CATALOGO = [
    # (nombre del objeto, categoría, función sin argumentos)
    ("Pared_Lisa", "Paredes", lambda: pared_lisa()),
    ("Pared_Ventana", "Paredes", lambda: pared_ventana(semilla=1)),
    ("Pared_Ventana_Jardinera", "Paredes", lambda: pared_ventana(jardinera=True, semilla=2)),
    ("Pared_Puerta", "Paredes", lambda: pared_puerta(semilla=3)),
    ("Pared_Escaparate", "Paredes", lambda: pared_escaparate()),
    ("Entramado_Ventana", "Paredes", lambda: pared_ventana(semilla=4).anadir(entramado(con_ventana=True))),
    ("Entramado_Liso", "Paredes", lambda: pared_lisa().anadir(entramado(con_ventana=False))),
    ("Esquina_Sillares", "Paredes", lambda: esquina(11.0)),
    ("Cornisa", "Paredes", lambda: cornisa(M)),
    ("Zocalo", "Paredes", lambda: zocalo(M)),
    ("Toldo", "Paredes", lambda: toldo()),
    ("Ventana", "Puertas y ventanas", lambda: ventana()),
    ("Ventana_Jardinera", "Puertas y ventanas", lambda: ventana(jardinera=True, semilla=5)),
    ("Puerta", "Puertas y ventanas", lambda: puerta()),
    ("Farolillo_Pared", "Puertas y ventanas", lambda: farolillo_pared()),
    ("Tejado_Tramo", "Tejados", lambda: tejado_tramo(16.0)),
    ("Tejado_Remate", "Tejados", lambda: tejado_remate(16.0)),
    ("Hastial", "Tejados", lambda: hastial(16.0)),
    ("Cumbrera", "Tejados", lambda: cumbrera(M, 16.0)),
    ("Tejado_Cuatro_Aguas", "Tejados", lambda: tejado_cuatro_aguas(16.0, 16.0)),
    ("Chimenea", "Tejados", lambda: chimenea()),
    ("Farola", "Mobiliario", lambda: farola()),
    ("Valla_Madera", "Mobiliario", lambda: valla_madera()),
    ("Valla_Piedra", "Mobiliario", lambda: valla_piedra()),
    ("Puesto", "Mobiliario", lambda: puesto()),
    ("Banco", "Mobiliario", lambda: banco()),
    ("Barril", "Mobiliario", lambda: barril()),
    ("Caja", "Mobiliario", lambda: caja_madera()),
    ("Maceta", "Mobiliario", lambda: maceta()),
    ("Cartel_Tienda", "Mobiliario", lambda: cartel("bolsa")),
    ("Tablon_Misiones", "Mobiliario", lambda: tablon_misiones()),
    ("Pozo", "Mobiliario", lambda: pozo()),
    ("Portal_Ciudad", "Mobiliario", lambda: portal()),
    ("Poste_Indicador", "Mobiliario", lambda: poste_indicador()),
    ("Carro", "Mobiliario", lambda: carro()),
    ("Pajar", "Campo", lambda: pajar()),
    ("Espantapajaros", "Campo", lambda: espantapajaros()),
    ("Arbol_Frondoso", "Vegetacion", lambda: arbol_frondoso(1)),
    ("Pino", "Vegetacion", lambda: pino(1)),
    ("Abedul", "Vegetacion", lambda: abedul(1)),
    ("Arbol_Flor", "Vegetacion", lambda: arbol_flor(1)),
    ("Arbusto", "Vegetacion", lambda: arbusto(1)),
    ("Roca", "Vegetacion", lambda: roca(1, 4.0)),
    ("Mata_Hierba", "Vegetacion", lambda: mata_hierba(1)),
    ("Mata_Flores", "Vegetacion", lambda: mata_flores(1)),
    ("Fuente", "Especiales", lambda: fuente()),
    ("Torre_Reloj", "Especiales", lambda: torre_reloj()),
    ("Molino", "Especiales", lambda: molino()),
    ("Puente", "Especiales", lambda: puente()),
]
