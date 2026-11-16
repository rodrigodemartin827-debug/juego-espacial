"""
Formas paramétricas que aparecen en muchos modelos (cráneos, huesos largos, setas). No se copia geometría de un
modelo a otro: cada llamada genera la suya, con sus proporciones y su azar, dentro de la pieza que la pide.
Todas se modelan en local (mirando a -Y, apoyadas en z = 0) y se colocan con `with p.en(pos, rot, esc):`.
"""

import math


def craneo(p, rnd, mat="hueso", mandibula=True, cuernos=0, largo=1.0, dientes=True, mat_cuerno="garra", k=0.07):
    """Cráneo de monstruo de ~1 de ancho. `largo` estira el hocico; `cuernos` = 0, 2 o 3."""
    a = rnd.uniform(0.92, 1.08)
    h = rnd.uniform(0.9, 1.1)
    p.esfera((0, 0.1, 0.62 * h), 0.5, mat, esc=(a, 1.12, 0.9 * h), k=k)
    p.esfera((0, -0.36 * largo, 0.4), 0.3, mat, esc=(0.95, 1.0 + 0.5 * (largo - 1), 0.78), k=k * 1.6)
    p.esfera((0.34 * a, -0.2, 0.44), 0.17, mat, esc=(0.8, 1.2, 0.9), sim=True, k=k * 1.4)
    p.tubo([(0.1, -0.5 * largo, 0.72), (0.3 * a, -0.44, 0.78), (0.44 * a, -0.2, 0.66)], [0.07, 0.085, 0.06], mat,
           sim=True, k=k)  # arcos de las cejas
    ro = rnd.uniform(0.13, 0.17)
    p.esfera((0.21 * a, -0.47 - 0.1 * (largo - 1), 0.6), ro, "negro", esc=(1, 1.4, 1.1), sim=True, resta=True, k=0.03)
    p.esfera((0, -0.62 * largo, 0.43), 0.075, "negro", esc=(0.8, 1.2, 1.5), resta=True, k=0.02)
    if mandibula:
        p.tubo([(0.4 * a, 0.12, 0.34), (0.36 * a, -0.2, 0.1), (0.2, -0.56 * largo, 0.07), (0, -0.66 * largo, 0.08)],
               [0.085, 0.09, 0.08, 0.085], mat, sim=True, k=k * 0.6)
    if dientes:
        d = p.duro
        for i in range(4):
            t = (i + 0.5) / 4
            x = 0.25 * (1 - t * t) * 0.95 + 0.02
            y = -0.3 - 0.36 * largo * t
            d.cono((x, y, 0.3), (x * 1.05, y - 0.02, 0.14 - (0.08 if i == 1 else 0)), 0.04, "diente", n=5, sim=True)
            if mandibula:
                d.cono((x * 0.95, y + 0.03, 0.12), (x, y + 0.01, 0.27 + (0.07 if i == 2 else 0)), 0.035, "diente",
                       n=5, sim=True)
    if cuernos >= 2:
        L = rnd.uniform(0.7, 1.1)
        p.duro.cuerno([(0.36 * a, 0.2, 0.9 * h), (0.75, 0.3, 1.1 * h + 0.2 * L), (0.8, -0.1, 1.2 * h + 0.6 * L)], 0.14,
                      mat_cuerno, n=6, seg=5, sim=True)
    if cuernos == 3:
        p.duro.cuerno([(0, -0.3, 0.98 * h), (0, -0.55, 1.3 * h), (0, -0.4, 1.7 * h)], 0.11, mat_cuerno, n=6, seg=4)


def hueso_largo(p, a, b, r, mat="hueso", k=0.04):
    """Fémur entre dos puntos: caña fina y dos cabezas con cóndilos."""
    import numpy as np

    a, b = np.asarray(a, float), np.asarray(b, float)
    eje = (b - a) / np.linalg.norm(b - a)
    lado = np.cross(eje, [0, 0, 1.0])
    if np.linalg.norm(lado) < 0.2:
        lado = np.cross(eje, [1.0, 0, 0])
    lado /= np.linalg.norm(lado)
    p.tubo([a, a + (b - a) * 0.25, a + (b - a) * 0.75, b], [r * 1.25, r * 0.8, r * 0.8, r * 1.25], mat, k=k)
    for q, s in ((a, 1.0), (b, 0.9)):
        p.esfera(q + lado * r * 0.9, r * 1.25 * s, mat, k=k * 2)
        p.esfera(q - lado * r * 0.9, r * 1.15 * s, mat, k=k * 2)


def seta(p, rnd, alto=1.0, radio=0.5, tallo="hongo_tallo", sombrero="hongo_sombrero", laminas="hongo_laminas",
         curva_=0.1, k=0.03):
    """Seta en local, pie en el origen. Devuelve una función r(z) del sombrero para colocar cosas encima."""
    cx, cy = rnd.uniform(-curva_, curva_) * alto, rnd.uniform(-curva_, curva_) * alto
    rt = radio * rnd.uniform(0.2, 0.28)
    p.tubo([(0, 0, 0), (cx * 0.6, cy * 0.6, alto * 0.45), (cx, cy, alto * 0.85)], [rt * 1.5, rt, rt * 0.9], tallo,
           suave=6, k=k)
    z0 = alto * 0.72
    hs = alto * rnd.uniform(0.3, 0.4)
    perfil = [(0, z0 + hs * 0.12), (radio * 0.7, z0), (radio, z0 + hs * 0.1), (radio * 0.93, z0 + hs * 0.38),
              (radio * 0.62, z0 + hs * 0.78), (radio * 0.25, z0 + hs * 0.97), (0, z0 + hs)]
    p.torno(perfil, (cx, cy, 0), sombrero, k=k)
    p.torno([(0, z0 - hs * 0.02), (radio * 0.86, z0 + hs * 0.02), (radio * 0.9, z0 + hs * 0.1), (0, z0 + hs * 0.2)],
            (cx, cy, 0), laminas, k=k * 0.3)

    def sup(t, ang):
        """Punto de la cara de arriba del sombrero: t = 0 en el borde, 1 en la cima."""
        zs = [z0 + hs * 0.1, z0 + hs * 0.38, z0 + hs * 0.78, z0 + hs * 0.97, z0 + hs]
        rs = [radio, radio * 0.93, radio * 0.62, radio * 0.25, 0.0]
        u = t * 4
        i = min(int(u), 3)
        f = u - i
        r = rs[i] + (rs[i + 1] - rs[i]) * f
        z = zs[i] + (zs[i + 1] - zs[i]) * f
        return (cx + r * math.cos(ang), cy + r * math.sin(ang), z)

    return sup


def silla(M, p, pos, s=1.0, mat="cuero", mirando=(0, -1, 0), nombre=None):
    """Silla de montar (cojín de cuero, pomo de hueso y respaldo) y su punto de montura. Mira a -Y."""
    x, y, z = pos
    p.esfera((x, y, z), 1, mat, esc=(0.72 * s, 0.85 * s, 0.24 * s), k=0.08)
    p.esfera((x, y + 0.72 * s, z + 0.3 * s), 1, mat, esc=(0.6 * s, 0.2 * s, 0.42 * s), k=0.08)
    p.duro.cuerno([(x, y - 0.72 * s, z), (x, y - 0.86 * s, z + 0.35 * s), (x, y - 0.7 * s, z + 0.68 * s)], 0.11 * s, "hueso", n=5, seg=3)
    for lado in (-1, 1):  # estribos: tendón con un aro de hueso
        p.duro.tubo([(x + lado * 0.66 * s, y, z), (x + lado * 0.86 * s, y, z - 0.55 * s)], 0.035 * s, "tendon", n=4)
        p.duro.toro((x + lado * 0.86 * s, y, z - 0.7 * s), 0.15 * s, 0.035 * s, "hueso", eje=(0, 1, 0), n=6, m=3)
    M.montura((x, y, z + 0.26 * s), nombre=nombre, mirando=mirando)
