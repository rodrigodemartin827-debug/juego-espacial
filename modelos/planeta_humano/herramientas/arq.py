"""
Piezas de arquitectura y atrezo que se construyen con parámetros (cada modelo las llama con sus medidas y
materiales: la geometría sale distinta en cada uno, no se copia).
"""

import math

from ph import V


def muro_huecos(p, x0, x1, z0, z1, y0, y1, huecos, mat, b=0.03, eje="X"):
    """Muro macizo entre x0..x1, z0..z1, con grosor y0..y1, partido en cajas alrededor de los huecos
    [(hx0, hx1, hz0, hz1)]. Con eje="Y" el muro corre a lo largo de Y (x0..x1 son entonces y, y0..y1 son x)."""
    def caja(a0, a1, c0, c1):
        if a1 - a0 < 1e-4 or c1 - c0 < 1e-4:
            return
        if eje == "X":
            p.caja_de((a0, y0, c0), (a1, y1, c1), mat, b)
        else:
            p.caja_de((y0, a0, c0), (y1, a1, c1), mat, b)

    huecos = sorted(huecos)
    # columnas de muro entre huecos y franjas encima/debajo de cada hueco
    xs = [x0]
    for hx0, hx1, hz0, hz1 in huecos:
        caja(xs[-1], hx0, z0, z1)
        caja(hx0, hx1, z0, hz0)
        caja(hx0, hx1, hz1, z1)
        xs.append(hx1)
    caja(xs[-1], x1, z0, z1)


def marco(p, x0, x1, z0, z1, y, ancho, fondo, mat, b=0.02, eje="X", abajo=True):
    """Marco de 4 listones alrededor de un hueco, sobresaliendo `fondo` desde y hacia -Y (o hacia -X si eje Y)."""
    def caja(a0, a1, c0, c1):
        if eje == "X":
            p.caja_de((a0, y - fondo, c0), (a1, y, c1), mat, b)
        else:
            p.caja_de((y - fondo, a0, c0), (y, a1, c1), mat, b)
    caja(x0 - ancho, x0, z0 - (ancho if abajo else 0), z1 + ancho)
    caja(x1, x1 + ancho, z0 - (ancho if abajo else 0), z1 + ancho)
    caja(x0, x1, z1, z1 + ancho)
    if abajo:
        caja(x0, x1, z0 - ancho, z0)


def viga_h(p, a, b_, alto, ancho, mat, alma=0.12, ala=0.1):
    """Viga en H (perfil IPE) de a a b_ con el alma vertical respecto a 'arriba' = Z (o X si la viga es vertical)."""
    a, b_ = V(a), V(b_)
    d = (b_ - a)
    L = d.length
    u = d.normalized()
    # eje "alto" perpendicular
    arriba = V((0, 0, 1)) if abs(u.z) < 0.9 else V((1, 0, 0))
    lado = u.cross(arriba).normalized()
    arriba = lado.cross(u).normalized()
    c = (a + b_) / 2
    from mathutils import Matrix
    m = Matrix((u, lado, arriba)).transposed()
    with p.en(c, m):
        p.caja((0, 0, 0), (L, alma, alto - 2 * ala), mat, 0.01)
        p.caja((0, 0, alto / 2 - ala / 2), (L, ancho, ala), mat, 0.015)
        p.caja((0, 0, -alto / 2 + ala / 2), (L, ancho, ala), mat, 0.015)


def barandilla(p, puntos, alto, mat, r=0.05, postes=True, n=8, barrotes=0, r_b=0.03):
    """Pasamanos sobre postes a lo largo de una polilínea en el suelo (z del punto = base)."""
    pts = [V(q) for q in puntos]
    arriba = [q + V((0, 0, alto)) for q in pts]
    p.tubo(arriba, r, mat, n=n, suave=False)
    medio = [q + V((0, 0, alto * 0.5)) for q in pts]
    p.tubo(medio, r * 0.75, mat, n=6, suave=False)
    if postes:
        for q in pts:
            p.cil(q, q + V((0, 0, alto)), r * 1.1, mat, n=n)
            p.cil(q - V((0, 0, 0.0)), q + V((0, 0, 0.04)), r * 2.4, mat, n=8)
    if barrotes:
        for i in range(len(pts) - 1):
            for k in range(1, barrotes + 1):
                q = pts[i].lerp(pts[i + 1], k / (barrotes + 1))
                p.cil(q, q + V((0, 0, alto)), r_b, mat, n=5)


def escalones(p, x0, x1, y_frente, z0, n, huella, contrahuella, mat, mat_borde=None, b=0.03, sentido=1):
    """n peldaños macizos que suben hacia +Y (sentido 1) desde y_frente. Devuelve la y de llegada."""
    for i in range(n):
        y_a = y_frente + i * huella * sentido
        y_b = y_frente + n * huella * sentido
        p.caja_de((x0, min(y_a, y_b), z0), (x1, max(y_a, y_b), z0 + (i + 1) * contrahuella), mat, b)
        if mat_borde is not None:
            yb = y_a + 0.06 * sentido
            p.caja_de((x0 + 0.05, min(y_a - 0.01 * sentido, yb), z0 + (i + 1) * contrahuella - 0.02),
                      (x1 - 0.05, max(y_a - 0.01 * sentido, yb), z0 + (i + 1) * contrahuella + 0.025), mat_borde, 0.008)
    return y_frente + n * huella * sentido


def foco_pared(p, neon, pos, mat_carcasa, mat_metal, salida=-1, tam=0.35):
    """Aplique de pared: placa, brazo y pantalla con la bombilla en la parte neón."""
    x, y, z = pos
    s = salida
    p.caja((x, y + s * 0.03, z), (tam * 0.6, 0.06, tam * 0.9), mat_metal, 0.015)
    for dz in (-tam * 0.3, tam * 0.3):
        p.perno((x, y + s * 0.06, z + dz), (0, s, 0), mat_metal, r=0.028)
    p.tubo([(x, y + s * 0.05, z), (x, y + s * tam * 0.6, z + tam * 0.25), (x, y + s * tam * 0.9, z + tam * 0.3)],
           0.03, mat_metal, n=6, seg=3)
    c = V((x, y + s * tam * 0.95, z + tam * 0.12))
    p.torno([(0.0, 0.32 * tam), (0.2 * tam, 0.32 * tam), (0.42 * tam, 0.02 * tam), (0.48 * tam, -0.05 * tam),
             (0.44 * tam, -0.06 * tam), (0.36 * tam, 0.0), (0.16 * tam, 0.26 * tam), (0.0, 0.27 * tam)],
            mat_carcasa, n=12, c=c)
    neon.esfera(c + V((0, 0, -0.02 * tam)), 0.17 * tam, None, seg=10, anillos=6, esc=(1, 1, 0.7))


def camara_seguridad(p, neon, pos, mat_carcasa, mat_metal, mat_lente, salida=-1, giro_z=0.0):
    """Cámara de vigilancia en soporte de pared, mirando hacia fuera y algo hacia abajo."""
    x, y, z = pos
    s = salida
    p.caja((x, y + s * 0.03, z), (0.32, 0.06, 0.42), mat_metal, 0.015)
    for dx in (-0.1, 0.1):
        for dz in (-0.14, 0.14):
            p.perno((x + dx, y + s * 0.06, z + dz), (0, s, 0), mat_metal, r=0.022, arandela=False)
    p.cil((x, y + s * 0.06, z), (x, y + s * 0.42, z + 0.05), 0.045, mat_metal, n=8)
    p.esfera((x, y + s * 0.42, z + 0.05), 0.07, mat_metal, seg=8, anillos=5)
    with p.en((x, y + s * 0.55, z - 0.02), (-20 * s, 0, giro_z)):
        p.caja((0, 0, 0), (0.24, 0.5, 0.22), mat_carcasa, 0.05)
        p.caja((0, -0.04 * -s, 0.135), (0.3, 0.6, 0.03), mat_carcasa, 0.012)  # visera
        p.cil((0, s * 0.25, 0), (0, s * 0.3, 0), 0.08, mat_metal, n=12)
        p.cil((0, s * 0.3, 0), (0, s * 0.31, 0), 0.06, mat_lente, n=12)
        neon.esfera((0.08, s * 0.255, 0.07), 0.018, None, seg=6, anillos=4)
    # cable que baja a la pared
    p.tubo([(x + 0.1, y + s * 0.4, z), (x + 0.16, y + s * 0.2, z - 0.25), (x + 0.16, y + s * 0.04, z - 0.5),
            (x + 0.16, y + s * 0.03, z - 1.2)], 0.018, mat_lente, n=5, seg=3)


def reja_plegada(p, x, y, z0, z1, mat, hojas=7, ancho=0.5, salida=-1):
    """Reja de seguridad tipo acordeón recogida a un lado de un hueco: barras verticales y tijeras en zigzag."""
    s = salida
    # guías superior e inferior
    p.caja((x, y + s * 0.06, z1 + 0.05), (ancho + 0.1, 0.12, 0.1), mat, 0.015)
    p.caja((x, y + s * 0.06, z0 - 0.02), (ancho + 0.1, 0.12, 0.06), mat, 0.01)
    xs = [x - ancho / 2 + ancho * i / (hojas - 1) for i in range(hojas)]
    for i, xi in enumerate(xs):
        p.caja((xi, y + s * 0.06, (z0 + z1) / 2), (0.04, 0.08, z1 - z0), mat)
    # tijeras
    niveles = 3
    for k in range(niveles):
        za = z0 + (z1 - z0) * (k + 0.5) / niveles
        for i in range(hojas - 1):
            a, b = xs[i], xs[i + 1]
            for sgn in (1, -1):
                pa = V((a, y + s * 0.11, za - sgn * 0.45))
                pb = V((b, y + s * 0.11, za + sgn * 0.45))
                p.cil(pa, pb, 0.012, mat, n=4)
    p.caja((xs[-1], y + s * 0.12, z0 + (z1 - z0) * 0.5), (0.08, 0.06, 0.25), mat, 0.01)  # cerrojo


def bajante(p, x, y, z_alto, mat, mat_abraz, salida=-1, r=0.1):
    """Bajante de pluviales con codo arriba y abajo y abrazaderas."""
    s = salida
    p.tubo([(x, y - s * 0.3, z_alto), (x, y + s * 0.18, z_alto - 0.15), (x, y + s * 0.2, z_alto - 0.5),
            (x, y + s * 0.2, 0.55), (x, y + s * 0.35, 0.2), (x, y + s * 0.5, 0.15)], r, mat, n=8, seg=3)
    for zz in (z_alto - 1.0, (z_alto + 0.6) / 2, 1.0):
        p.cil((x, y + s * 0.2, zz - 0.06), (x, y + s * 0.2, zz + 0.06), r * 1.25, mat_abraz, n=8)
        p.caja((x, y + s * 0.07, zz), (0.06, 0.14, 0.08), mat_abraz, 0.01)


def espada(p, mat_hoja, mat_guarda, mat_pomo, mat_puno, largo=3.0, ancho=0.22):
    """Espada a lo largo de +Z con la empuñadura en z=0. Hoja con sección de rombo y vaceo."""
    hoja = largo * 0.72
    z0 = largo * 0.28
    secc = lambda w, t, z: [(w / 2, 0, z), (w * 0.12, t / 2, z), (-w * 0.12, t / 2, z), (-w / 2, 0, z),
                            (-w * 0.12, -t / 2, z), (w * 0.12, -t / 2, z)]
    anillos = [secc(ancho, 0.06, z0), secc(ancho * 0.96, 0.055, z0 + hoja * 0.5), secc(ancho * 0.75, 0.05, z0 + hoja * 0.86),
               secc(0.02, 0.01, z0 + hoja)]
    p.loft(anillos, mat_hoja)
    # guarda curvada
    p.tubo([(-ancho * 1.6, 0, z0 + 0.08), (-ancho * 0.6, 0, z0 - 0.02), (0, 0, z0 - 0.03), (ancho * 0.6, 0, z0 - 0.02),
            (ancho * 1.6, 0, z0 + 0.08)], 0.045, mat_guarda, n=6, seg=3)
    p.caja((0, 0, z0 - 0.03), (ancho * 0.6, 0.11, 0.1), mat_guarda, 0.02)
    # empuñadura con anillos de cuero
    p.cil((0, 0, 0.12), (0, 0, z0 - 0.06), 0.05, mat_puno, n=8)
    n = 6
    for i in range(n):
        zz = 0.14 + (z0 - 0.22) * (i + 0.5) / n
        p.cil((0, 0, zz - 0.02), (0, 0, zz + 0.02), 0.058, mat_puno, n=8)
    p.esfera((0, 0, 0.07), 0.085, mat_pomo, seg=8, anillos=6)


def caja_madera(p, c, s, mat_tabla, mat_clavo, tablas=3, rot=None, abierta=True):
    """Caja de fruta de tablas con hueco entre tablas y clavos visibles."""
    w, d, h = s
    with p.en(c, rot):
        p.caja((0, 0, 0.03), (w, d, 0.06), mat_tabla, 0.01)
        for lado in (-1, 1):
            for k in range(tablas):
                zz = 0.06 + (h - 0.06) * (k + 0.5) / tablas
                ht = (h - 0.06) / tablas * 0.78
                p.caja((0, lado * (d / 2 - 0.025), zz), (w, 0.05, ht), mat_tabla)
                p.caja((lado * (w / 2 - 0.025), 0, zz), (0.05, d - 0.1, ht), mat_tabla)
                for sx in (-1, 1):
                    p.cil((sx * (w / 2 - 0.03), lado * (d / 2 + 0.0), zz), (sx * (w / 2 - 0.03), lado * (d / 2 + 0.012), zz),
                          0.012, mat_clavo, n=4)
            # listones de esquina
            for sx in (-1, 1):
                p.caja((sx * (w / 2 - 0.04), lado * (d / 2 - 0.04), h / 2), (0.08, 0.08, h), mat_tabla)
