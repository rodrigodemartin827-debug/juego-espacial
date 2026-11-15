"""Piezas que se repiten entre modelos: ventanas, tiras de neón, barandillas, torretas decorativas, banderas..."""

import math

GIRO_CARA = {"-y": 0, "+x": 90, "+y": 180, "-x": 270}


def ventana(g, x, y, z, w, h, cara="-y", marco="h_gris", cristal="h_cristal", fondo=0.25):
    """Ventana con marco que sobresale del muro. (x, y, z) = centro sobre la cara del muro."""
    with g.grupo((x, y, z), (0, 0, GIRO_CARA[cara])):
        g.caja(marco, (w + 0.5, fondo, h + 0.5), (0, -fondo / 2 + 0.02, 0))
        g.caja(cristal, (w, 0.12, h), (0, -fondo - 0.04, 0))


def tira(g, mat, a, b, grosor=0.18):
    """Tira (de neón normalmente) entre dos puntos alineados con un eje."""
    tam = [abs(b[i] - a[i]) + grosor for i in range(3)]
    g.caja(mat, tam, [(a[i] + b[i]) / 2 for i in range(3)])


def barandilla(g, a, b, alto=1.1, mat="h_metal", postes=4, r=0.07):
    """Barandilla de tubos entre dos puntos del suelo."""
    ax, ay, az = a
    bx, by, bz = b
    for i in range(postes):
        t = i / (postes - 1)
        p = (ax + (bx - ax) * t, ay + (by - ay) * t, az + (bz - az) * t)
        g.tubo(mat, [p, (p[0], p[1], p[2] + alto)], r, lados=5, suave=False)
    for k in (1.0, 0.5):
        g.tubo(mat, [(ax, ay, az + alto * k), (bx, by, bz + alto * k)], r, lados=5, suave=False)


def antena(g, pos, alto, mat="h_metal", luz="h_luz_roja", r=0.12):
    x, y, z = pos
    g.cil(mat, r * 2.2, alto * 0.08, (x, y, z), lados=8)
    g.cil(mat, r, alto * 0.6, (x, y, z), lados=6, r2=r * 0.6)
    g.cil(mat, r * 0.5, alto * 0.4, (x, y, z + alto * 0.6), lados=5, r2=r * 0.2)
    for k in (0.35, 0.55):
        g.caja(mat, (alto * 0.22, 0.06, 0.06), (x, y, z + alto * k))
    g.esfera(luz, r * 1.4, (x, y, z + alto), lados=6, anillos=4)


def torreta_deco(g, pos, esc=1.0, giro=0.0, base="h_gris", cuerpo="h_blanco_liso", acento="h_naranja_liso",
                 neon="h_neon"):
    """Torreta decorativa de dos cañones."""
    with g.grupo(pos, (0, 0, giro), esc):
        g.cil(base, 1.3, 0.5, (0, 0, 0), lados=10, bisel=0.1)
        g.cil("h_oscuro", 0.8, 0.5, (0, 0, 0.5), lados=10)
        g.caja(cuerpo, (2.0, 2.2, 1.2), (0, 0.1, 1.6), sup=(0.8, 0.8), bisel=0.12)
        g.caja(acento, (2.1, 0.5, 0.35), (0, 0.9, 1.5))
        for s in (-1, 1):
            g.cil("h_oscuro", 0.2, 2.2, (s * 0.5, -0.9, 1.55), (90, 0, 0), lados=8)
            g.cil("h_metal", 0.26, 0.4, (s * 0.5, -2.7, 1.55), (90, 0, 0), lados=8)
        g.caja(neon, (0.9, 0.1, 0.18), (0, -1.0, 2.0))


def bandera(g, pos, alto=10.0, ancho=4.2, caida=2.6, tela="h_bandera", mastil="h_metal", remate="h_naranja_liso",
            lado=1):
    """Mástil con bandera ondeando (tela con grosor). El paño sale hacia +X (lado=1) o -X."""
    x, y, z = pos
    g.cil(mastil, 0.32, 0.4, (x, y, z), lados=8, bisel=0.06)
    g.cil(mastil, 0.13, alto, (x, y, z), lados=6, r2=0.09)
    g.esfera(remate, 0.24, (x, y, z + alto + 0.1), lados=6, anillos=4)
    n = 7
    a0, a1 = [], []
    secciones = []
    for i in range(n + 1):
        t = i / n
        px = x + lado * (0.1 + ancho * t)
        py = y + 0.35 * math.sin(t * 7.0) * t
        cae = 0.25 * t * t
        zt = z + alto - 0.15 - cae
        zb = z + alto - 0.15 - caida + 0.3 * t * math.sin(t * 5) - cae
        secciones.append([(px, py - 0.04, zb), (px, py + 0.04, zb), (px, py + 0.04, zt), (px, py - 0.04, zt)])
    g.loft(tela, secciones, suave=True)


# ------------------------------------------------------------------------------------------------ monstruos

import random  # noqa: E402


def cristales(g, mat, pos, n=5, r=0.8, h=4.0, semilla=0, abrir=35.0, lados=6, radio=None, centro=True):
    """Racimo de cristales que brotan de un punto: uno central y el resto inclinados alrededor."""
    rnd = random.Random(semilla * 977 + 13)
    x, y, z = pos
    radio = r * 0.9 if radio is None else radio
    if centro:
        g.cristal(mat, r, h, (x, y, z - h * 0.08), (rnd.uniform(-6, 6), rnd.uniform(-6, 6), rnd.uniform(0, 60)), lados=lados)
    for i in range(n):
        a = 2 * math.pi * (i + rnd.uniform(-0.25, 0.25)) / n
        k = rnd.uniform(0.35, 0.75)
        inc = abrir * rnd.uniform(0.6, 1.25)
        g.cristal(mat, r * k, h * k * rnd.uniform(0.8, 1.2),
                  (x + radio * math.cos(a), y + radio * math.sin(a), z - h * 0.06),
                  (inc * math.sin(a), -inc * math.cos(a), rnd.uniform(0, 60)), lados=lados - (i % 2))


def curva(base, direccion, largo, sube=0.0, cae=0.0, tuerce=0.0, n=6, semilla=0):
    """Puntos de una curva que sale de `base` hacia `direccion` (grados en planta): tentáculos, raíces, costillas."""
    rnd = random.Random(semilla * 131 + 7)
    a = math.radians(direccion)
    pts = []
    for i in range(n + 1):
        t = i / n
        aa = a + math.radians(tuerce) * t + (rnd.uniform(-0.12, 0.12) if 0 < i < n else 0)
        d = largo * t
        z = sube * math.sin(t * math.pi * 0.5) * 1.0 - cae * t * t
        pts.append((base[0] + d * math.cos(aa), base[1] + d * math.sin(aa), base[2] + z))
    return pts


def radios(r0, r1, n, panza=0.0):
    return [r0 + (r1 - r0) * (i / n) + panza * math.sin(math.pi * i / n) for i in range(n + 1)]


def colmillo(g, mat, pos, largo, r, rot=(180, 0, 0), curvo=0.25):
    with g.grupo(pos, rot):
        g.tubo(mat, [(0, 0, 0), (curvo * largo * 0.4, 0, largo * 0.5), (curvo * largo, 0, largo)], [r, r * 0.65, 0.0], lados=6)


def runa(g, mat, pos, rot=(0, 0, 0), esc=1.0, semilla=0, grosor=0.08):
    """Glifo original hecho de trazos (cajas finas) sobre el plano XZ local, mirando a -Y."""
    rnd = random.Random(semilla * 53 + 5)
    trazos = [((0, -0.5), (0, 0.5))]
    opciones = [((-0.3, 0.5), (0.3, 0.5)), ((-0.3, -0.5), (0.3, -0.5)), ((0, 0.1), (0.35, 0.45)), ((0, 0.1), (-0.35, 0.45)),
                ((0, -0.1), (0.35, -0.45)), ((0, -0.1), (-0.35, -0.45)), ((-0.35, 0), (0.35, 0)), ((0.35, -0.2), (0.35, 0.3)),
                ((-0.35, -0.3), (-0.35, 0.2))]
    rnd.shuffle(opciones)
    trazos += opciones[:rnd.randint(2, 3)]
    with g.grupo(pos, rot, esc):
        for (ax, az), (bx, bz) in trazos:
            largo = math.hypot(bx - ax, bz - az)
            ang = math.degrees(math.atan2(bz - az, bx - ax))
            g.caja(mat, (largo + 0.12, grosor, 0.13), ((ax + bx) / 2, 0, (az + bz) / 2), rot=(0, -ang, 0))


def seta(g, pos, alto, r_som, tallo="m_hueso", sombrero="m_hongo", puntos="m_magenta", inclina=(0, 0), lados=10,
         semilla=0, r_tallo=None, laminas="m_purpura_liso"):
    """Seta: tallo curvo, sombrero abombado con láminas por debajo y puntos luminosos."""
    rnd = random.Random(semilla * 71 + 3)
    x, y, z = pos
    rt = r_som * 0.22 if r_tallo is None else r_tallo
    cx, cy = x + inclina[0], y + inclina[1]
    g.tubo(tallo, [(x, y, z), (x + inclina[0] * 0.2, y + inclina[1] * 0.2, z + alto * 0.4),
                   (x + inclina[0] * 0.7, y + inclina[1] * 0.7, z + alto * 0.8), (cx, cy, z + alto)],
           [rt * 1.5, rt * 1.05, rt * 0.9, rt * 0.8], lados=max(6, lados - 2))
    h = r_som * 0.62
    g.rev(sombrero, [(r_som * 0.3, -h * 0.05), (r_som, 0.0), (r_som * 1.02, h * 0.12), (r_som * 0.86, h * 0.5),
                     (r_som * 0.55, h * 0.85), (0.0, h)], (cx, cy, z + alto - h * 0.1), lados=lados, tapas=(False, False))
    g.rev(laminas, [(0.0, -h * 0.02), (r_som * 0.3, -h * 0.05), (r_som * 0.99, 0.0), (r_som * 0.6, h * 0.18), (0.0, h * 0.2)],
          (cx, cy, z + alto - h * 0.1), lados=lados, suave=False)
    if puntos:
        for i in range(max(3, int(r_som * 1.6))):
            a = rnd.uniform(0, 6.28)
            d = rnd.uniform(0.2, 0.8)
            zz = h * (1 - d * d) * 0.92
            g.esfera(puntos, r_som * rnd.uniform(0.06, 0.11), (cx + r_som * d * math.cos(a), cy + r_som * d * math.sin(a),
                     z + alto - h * 0.1 + zz + 0.02), esc=(1, 1, 0.45), lados=6, anillos=4)


def ramas(g, mat, base, direccion, largo, r, niveles, rnd, abrir=35.0, hijos=2, encoge=0.72, lados=6, gravedad=0.0,
          tuerce=0.25, puntas=None, r_min=0.05):
    """Ramificación recursiva (árboles, corales). Añade a `puntas` (posición, dirección) de cada extremo."""
    from mathutils import Vector
    d = Vector(direccion).normalized()
    p0 = Vector(base)
    u = d.orthogonal().normalized()
    v = d.cross(u)
    a = rnd.uniform(0, 6.28)
    medio = p0 + d * largo * 0.5 + (u * math.cos(a) + v * math.sin(a)) * largo * tuerce * rnd.uniform(0.3, 1.0)
    p1 = p0 + d * largo + Vector((0, 0, -gravedad * largo))
    r1 = max(r * encoge, r_min)
    g.tubo(mat, [p0, medio, p1], [r, (r + r1) / 2, r1 if niveles > 0 else r1 * 0.55], lados=lados)
    if niveles <= 0:
        if puntas is not None:
            puntas.append((tuple(p1), tuple((p1 - medio).normalized())))
        return
    d1 = (p1 - medio).normalized()
    u = d1.orthogonal().normalized()
    v = d1.cross(u)
    fase = rnd.uniform(0, 6.28)
    for i in range(hijos):
        ang = math.radians(abrir * rnd.uniform(0.7, 1.3))
        az = fase + 2 * math.pi * (i + rnd.uniform(-0.2, 0.2)) / hijos
        nd = d1 * math.cos(ang) + (u * math.cos(az) + v * math.sin(az)) * math.sin(ang)
        ramas(g, mat, p1, nd, largo * encoge * rnd.uniform(0.85, 1.12), r1, niveles - 1, rnd, abrir, hijos, encoge,
              max(lados - 1, 4), gravedad, tuerce, puntas, r_min)


def raices(g, mat, pos, n, r, largo, rnd, lados=5, caida=0.6):
    """Raíces que salen del pie del tronco y se clavan en el suelo."""
    x, y, z = pos
    for i in range(n):
        a = 2 * math.pi * (i + rnd.uniform(-0.3, 0.3)) / n
        ca, sa = math.cos(a), math.sin(a)
        L = largo * rnd.uniform(0.75, 1.2)
        g.tubo(mat, [(x + ca * r * 0.3, y + sa * r * 0.3, z + r * 1.6), (x + ca * (r + L * 0.35), y + sa * (r + L * 0.35), z + r * 0.75),
                     (x + ca * (r + L), y + sa * (r + L), z - caida * 0.3)], [r * 0.55, r * 0.42, r * 0.12], lados=lados)
