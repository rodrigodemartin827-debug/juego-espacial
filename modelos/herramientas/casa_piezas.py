"""
Piezas de la casa del minero. Todo en STUDS, con el frente de la casa mirando a -Y (el «delante» de Roblox).

Planta: muros de 9 × 7 studs (cara exterior del alma en x = ±4,5, y = ±3,5) sobre una base de hormigón de medio
stud, con un porche delante. Tejado a dos aguas con la cumbrera a lo largo de Y (hastial en la fachada).

  fachada (-Y), vista desde delante:   [contraventana] VENTANA [contraventana]  pico/botas  PUERTA  buzón/maceta
  lateral izquierdo (-X): ventana pequeña con rejilla debajo, bajante en la esquina delantera, canalón arriba
  lateral derecho (+X): medidor de luz y cable que sube al panel solar del faldón derecho
  faldón izquierdo: chimenea; faldón derecho: panel solar

Cada función crea una `Pieza` (malla baja del juego + detalles de la malla alta para hornear).
"""

import math
import random

from mathutils import Matrix, Vector, noise

from casa_malla import Pieza, base_de, rot

# ======================================================================================================
# Medidas (studs)
# ======================================================================================================

BASE_Z = 0.5          # alto de la base: la casa se eleva medio stud
ZOC_Z = 1.5           # alto del zócalo de piedra (1 stud sobre la base)
MX, MY = 4.5, 3.5     # cara exterior del alma de los muros
MURO = 0.3            # grosor del alma
PANEL = 0.06          # grosor de los paneles metálicos
JUNTA = 0.035         # separación entre paneles
CUMBRE = 7.3          # altura de las crestas en la cumbrera
ALERO_X = 5.05        # vuelo lateral del tejado
VUELO_Y = 4.05        # vuelo delante y detrás
ALERO_Z = 5.75        # altura de las crestas en el alero
PEND = (CUMBRE - ALERO_Z) / ALERO_X
ONDA = 0.09           # alto de los nervios de la chapa
CHAPA = 0.03          # grosor de la chapa
PASO = 0.76           # paso de los nervios
Y_REF = -4.22         # fase de los nervios (para que las chapas que se solapan encajen)

BASE = dict(x0=-4.85, x1=4.85, y0=-4.6, y1=3.85)
PUERTA = dict(x0=0.5, x1=2.8, z0=0.5, z1=5.0)
HOJA = dict(x0=0.65, x1=2.65, z0=0.62, z1=4.86, y0=-3.52, y1=-3.34)  # hoja de la puerta
EJE_PUERTA = Vector((0.6, -3.6, 0.0))  # eje de las bisagras (vertical)
BISAGRAS_Z = (1.25, 4.25)
VENTANA = dict(x0=-3.7, x1=-1.0, z0=2.3, z1=4.5)
VLAT = dict(u0=-1.4, u1=0.2, v0=2.9, v1=4.3)      # en el plano del muro izquierdo (u = -y)
REJILLA = dict(u0=-1.15, u1=-0.05, v0=1.72, v1=2.42)
MANIJA = Vector((2.43, -3.52, 2.82))
ANG_CONTRA_IZQ = 115.0   # contraventanas entreabiertas (grados)
ANG_CONTRA_DER = 95.0
ANG_TAPA_BUZON = 16.0


def z_cresta(x):
    return CUMBRE - PEND * abs(x)


def z_muro(x):
    """Altura de la parte de arriba de los muros hastiales (justo debajo de la chapa)."""
    return z_cresta(x) - ONDA - CHAPA - 0.005


Z_LAT = z_muro(MX)  # alto de los muros laterales


class Plano:
    """Plano de un muro: u horizontal, v = arriba, n hacia fuera; d = distancia desde la cara del alma."""

    def __init__(self, origen, n):
        self.o = Vector(origen)
        self.n = Vector(n)
        self.u, self.v = base_de(self.n)
        self.giro = Matrix((self.u, -self.n, self.v)).transposed()  # caja local: x=u, y=hacia dentro, z=v

    def p(self, u, v, d=0.0):
        return self.o + self.u * u + self.v * v + self.n * d


FRENTE = Plano((0, -MY, 0), (0, -1, 0))   # u = +x
FONDO = Plano((0, MY, 0), (0, 1, 0))      # u = -x
IZQ = Plano((-MX, 0, 0), (-1, 0, 0))      # u = -y
DER = Plano((MX, 0, 0), (1, 0, 0))        # u = +y


def caja_plano(c, pl, u0, u1, v0, v1, d0, d1, mat, sin=(), ocultas=(), giro_extra=None, mats=None):
    """Caja alineada con un muro. Nombres de caras: '-y' = la de fuera, '+y' = la de dentro (contra el muro)."""
    centro = pl.p((u0 + u1) / 2, (v0 + v1) / 2, (d0 + d1) / 2)
    g = pl.giro if giro_extra is None else pl.giro @ giro_extra
    return c.caja(centro, (u1 - u0, d1 - d0, v1 - v0), mat, giro=g, sin=sin, ocultas=ocultas, mats=mats)


def tornillo(p, centro, normal, radio, mat, lados_baja=6, en_baja=True):
    """Tornillo: prisma sencillo en la malla baja y cabeza redonda en la alta (para el mapa de normales)."""
    if en_baja:
        p.baja.solo_baja = True
        p.baja.revolucion([(radio, 0), (radio * 0.8, radio * 0.42)], centro, lados_baja, mat, eje=normal,
                          tapa_ini=False, giro=math.pi / lados_baja)
        p.baja.solo_baja = False
    p.alta.cupula(centro, normal, radio, mat, alto=radio * 0.5, lados=12)


def recortar(poly, a, b, c):
    """Sutherland-Hodgman: deja la parte de `poly` con a*u + b*v <= c."""
    res = []
    for i in range(len(poly)):
        p, q = poly[i], poly[(i + 1) % len(poly)]
        fp, fq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if fp <= 0:
            res.append(p)
        if (fp < 0) != (fq < 0) and abs(fp - fq) > 1e-9:
            t = fp / (fp - fq)
            res.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
    return res


def area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2


# ======================================================================================================
# Estructura
# ======================================================================================================


def base():
    p = Pieza("casa_base", peso_uv=0.8)
    p.baja.caja_de((BASE["x0"], BASE["y0"], 0), (BASE["x1"], BASE["y1"], BASE_Z), "hormigon", sin=("-z",))
    # Losa donde cae el agua del bajante.
    p.baja.caja_de((-5.42, -3.48, 0), (-4.86, -2.92, 0.07), "hormigon", sin=("-z",))
    return p


def escalon():
    """Losa de piedra delante de la puerta, hundida en el centro por los años de pisadas."""
    p = Pieza("escalon", peso_uv=1.6)
    rnd = random.Random(3)
    x0, x1, y0, y1, z0, z1 = 0.35, 2.95, -5.3, -4.6, 0.0, 0.27
    nx, ny = 6, 3
    c = p.baja
    arriba = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            fx, fy = i / nx, j / ny
            x, y = x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy
            hund = 0.0
            if 0 < i < nx and 0 < j < ny:
                hund = 0.028 * math.sin(math.pi * fx) ** 1.5 * math.sin(math.pi * fy) ** 1.2
            borde = 0.0 if (0 < i < nx and 0 < j < ny) else rnd.uniform(-0.012, 0.004)
            arriba[i, j] = c.v((x, y, z1 - hund + borde))
    for i in range(nx):
        for j in range(ny):
            c.cara([arriba[i, j], arriba[i + 1, j], arriba[i + 1, j + 1], arriba[i, j + 1]], "losa")
    # Contorno: lados hasta el suelo.
    anillo = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)] + \
             [(i, ny) for i in range(nx, 0, -1)] + [(0, j) for j in range(ny, 0, -1)]
    abajo = {k: c.v((arriba[k].co.x, arriba[k].co.y, z0)) for k in anillo}
    for a in range(len(anillo)):
        k1, k2 = anillo[a], anillo[(a + 1) % len(anillo)]
        c.cara([abajo[k1], abajo[k2], arriba[k2], arriba[k1]], "losa")
    p.extra["centro"] = [(x0 + x1) / 2, (y0 + y1) / 2, z1]
    return p


def zocalo():
    """Zócalo de piedra irregular de 1 stud, con mortero detrás y un vierteaguas metálico encima."""
    p = Pieza("casa_zocalo", peso_uv=1.0)
    rnd = random.Random(11)
    tramos = [
        (FRENTE, -4.63, PUERTA["x0"] - 0.05), (FRENTE, PUERTA["x1"] + 0.05, 4.63),
        (FONDO, -4.63, 4.63), (IZQ, -3.5, 3.5), (DER, -3.5, 3.5),
    ]
    zt = 1.45
    for pl, u0, u1 in tramos:
        # Mortero (lo que se ve entre piedra y piedra).
        caja_plano(p.baja, pl, u0, u1, BASE_Z, 1.46, 0.0, 0.075, "mortero", sin=("+y", "-z", "+z"),
                   ocultas=("-y",))
        # Mampostería irregular: cada columna es una piedra alta o dos piedras de alturas distintas, y la
        # de arriba no siempre empieza donde acaba la de abajo (se desplaza un poco a un lado).
        u = u0
        while u < u1 - 0.05:
            largo = rnd.uniform(0.42, 0.98)
            if u1 - (u + largo) < 0.3:
                largo = u1 - u
            piedras = []
            if rnd.random() < 0.22 and largo < 0.75:
                piedras.append((u, u + largo, BASE_Z, zt, ("+y", "-z", "+z")))
            else:
                corte = BASE_Z + (zt - BASE_Z) * rnd.uniform(0.36, 0.64)
                desv = rnd.uniform(-0.12, 0.12)
                piedras.append((u, u + largo, BASE_Z, corte, ("+y", "-z")))
                piedras.append((u + desv * 0.5, u + largo + desv * 0.5, corte, zt, ("+y", "+z")))
            for a, b, v0, v1, sin in piedras:
                a, b = max(a, u0), min(b, u1)
                if b - a < 0.1:
                    continue
                frente = rnd.uniform(0.1, 0.15)
                giro = rot("Y", rnd.uniform(-2.2, 2.2)) @ rot("X", rnd.uniform(-1.5, 1.5)) @ \
                    rot("Z", rnd.uniform(-1.5, 1.5))
                g0 = 0.0 if v0 <= BASE_Z else rnd.uniform(0.014, 0.03)
                g1 = 0.0 if v1 >= zt else rnd.uniform(0.0, 0.012)
                caja_plano(p.baja, pl, a + rnd.uniform(0.012, 0.025), b - rnd.uniform(0.012, 0.025), v0 + g0,
                           v1 - g1, 0.05, frente, "piedra", sin=sin, giro_extra=giro)
            u += largo
        # Vierteaguas: chapa inclinada sobre el zócalo.
        perfil = [(0.035, 1.53), (0.185, 1.468), (0.185, 1.435), (0.17, 1.435), (0.17, 1.455), (0.035, 1.508)]
        ext = 0.12 if pl in (FRENTE, FONDO) else 0.0
        a, b = u0 - ext, u1 + ext
        if pl is FRENTE and u1 < 1:
            b = u1 - 0.05
        if pl is FRENTE and u0 > 1:
            a = u0 + 0.05
        o = pl.p(a, 0, 0)
        p.baja.placa(perfil, o, pl.n, Vector((0, 0, 1)), pl.u, b - a, "metal_oscuro", atras=True)
    return p


def paredes():
    """Alma de los muros (con los huecos), paneles metálicos con juntas, parches soldados y cantoneras."""
    p = Pieza("casa_paredes", peso_uv=1.0)
    rnd = random.Random(7)
    b, a = p.baja, p.alta
    zm0 = z_muro(0)
    hastial = [(-MX, BASE_Z), (MX, BASE_Z), (MX, z_muro(MX)), (0, zm0), (-MX, z_muro(MX))]

    # ---- alma: cara de fuera (oscura, se ve entre panel y panel) y cara de dentro --------------------------
    def alma(pl, contorno_ext, contorno_int, huecos, u_int):
        # La cara de fuera solo se ve en las juntas entre paneles: casi nada de sitio en el atlas (oculta=2).
        b.cara_con_huecos([pl.p(u, v, 0) for u, v in contorno_ext], [[pl.p(u, v, 0) for u, v in h] for h in huecos],
                          "junta", pl.n, oculta=2)
        b.cara_con_huecos([pl.p(u, v, -MURO) for u, v in contorno_int],
                          [[pl.p(u, v, -MURO) for u, v in h] for h in huecos], "interior", -pl.n, oculta=True)

    def rect(u0, u1, v0, v1):
        return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]

    vent = rect(VENTANA["x0"], VENTANA["x1"], VENTANA["z0"], VENTANA["z1"])
    frente_ext = [(-MX, 1.45), (PUERTA["x0"], 1.45), (PUERTA["x0"], PUERTA["z1"]), (PUERTA["x1"], PUERTA["z1"]),
                  (PUERTA["x1"], 1.45), (MX, 1.45), (MX, z_muro(MX)), (0, zm0), (-MX, z_muro(MX))]
    frente_int = [(-MX + MURO, BASE_Z), (PUERTA["x0"], BASE_Z), (PUERTA["x0"], PUERTA["z1"]),
                  (PUERTA["x1"], PUERTA["z1"]), (PUERTA["x1"], BASE_Z), (MX - MURO, BASE_Z),
                  (MX - MURO, z_muro(MX - MURO)), (0, zm0), (-MX + MURO, z_muro(MX - MURO))]
    alma(FRENTE, frente_ext, frente_int, [vent], None)
    fondo_ext = [(-MX, 1.45), (MX, 1.45), (MX, z_muro(MX)), (0, zm0), (-MX, z_muro(MX))]
    fondo_int = [(-MX + MURO, BASE_Z), (MX - MURO, BASE_Z), (MX - MURO, z_muro(MX - MURO)), (0, zm0),
                 (-MX + MURO, z_muro(MX - MURO))]
    alma(FONDO, fondo_ext, fondo_int, [], None)
    vl = rect(VLAT["u0"], VLAT["u1"], VLAT["v0"], VLAT["v1"])
    alma(IZQ, rect(-MY, MY, 1.45, Z_LAT), rect(-MY + MURO, MY - MURO, BASE_Z, Z_LAT), [vl], None)
    alma(DER, rect(-MY, MY, 1.45, Z_LAT), rect(-MY + MURO, MY - MURO, BASE_Z, Z_LAT), [], None)

    # ---- paneles ---------------------------------------------------------------------------------------------
    def panel(pl, u0, u1, v0, v1, gable, abollado=0.0):
        g = JUNTA / 2
        poly = rect(u0 + g, u1 - g, v0 + g, v1 - g)
        if gable:
            poly = recortar(poly, PEND, 1, zm0 - g)
            poly = recortar(poly, -PEND, 1, zm0 - g)
        else:
            poly = recortar(poly, 0, 1, Z_LAT)
        if len(poly) < 3 or area(poly) < 0.02:
            return
        grosor = PANEL + rnd.uniform(-0.006, 0.004)
        if abollado and len(poly) == 4:
            _panel_abollado(b, pl, poly, grosor, abollado)
        else:
            b.placa(poly, pl.p(0, 0, 0), pl.u, pl.v, pl.n, grosor, "pintura_panel")
        # Remaches a lo largo del borde (solo en la malla alta: se hornean).
        us = [q[0] for q in poly]
        vs = [q[1] for q in poly]
        ua, ub, va, vb = min(us) + 0.07, max(us) - 0.07, min(vs) + 0.07, max(vs) - 0.07
        for t in range(int((ub - ua) / 0.3) + 1):
            uu = ua + (ub - ua) * t / max(1, int((ub - ua) / 0.3))
            for vv in (va, vb):
                if _dentro(poly, uu, vv):
                    a.cupula(pl.p(uu, vv, grosor), pl.n, 0.022, "acero", alto=0.012, lados=8)
        for t in range(1, int((vb - va) / 0.3)):
            vv = va + (vb - va) * t / int((vb - va) / 0.3)
            for uu in (ua, ub):
                if _dentro(poly, uu, vv):
                    a.cupula(pl.p(uu, vv, grosor), pl.n, 0.022, "acero", alto=0.012, lados=8)

    abollados = {("F", 0, 1): 0.035, ("B", 2, 0): 0.05, ("D", 2, 1): 0.045}
    # Frente (u = x).
    cols_f = [(-4.5, -3.7), (-3.7, -2.35), (-2.35, -1.0), (-1.0, 0.5), (0.5, 1.65), (1.65, 2.8), (2.8, 4.5)]
    for i, (u0, u1) in enumerate(cols_f):
        if 1 <= i <= 2:
            filas = [(1.5, VENTANA["z0"]), (VENTANA["z1"], 5.75), (5.75, 7.6)]
        elif 4 <= i <= 5:
            filas = [(PUERTA["z1"], 5.75), (5.75, 7.6)]
        else:
            filas = [(1.5, 3.4), (3.4, 5.75), (5.75, 7.6)]
        for j, (v0, v1) in enumerate(filas):
            panel(FRENTE, u0, u1, v0, v1, True, abollados.get(("F", i, j), 0.0))
    cols_b = [(-4.5, -3.0), (-3.0, -1.5), (-1.5, 0.0), (0.0, 1.5), (1.5, 3.0), (3.0, 4.5)]
    for i, (u0, u1) in enumerate(cols_b):
        for j, (v0, v1) in enumerate([(1.5, 3.6), (3.6, 5.75), (5.75, 7.6)]):
            panel(FONDO, u0, u1, v0, v1, True, abollados.get(("B", i, j), 0.0))
    cols_i = [(-3.5, -2.45), (-2.45, VLAT["u0"]), (VLAT["u0"], VLAT["u1"]), (VLAT["u1"], 1.85), (1.85, 3.5)]
    for i, (u0, u1) in enumerate(cols_i):
        filas = [(1.5, VLAT["v0"]), (VLAT["v1"], 5.9)] if i == 2 else [(1.5, 3.6), (3.6, 5.9)]
        for j, (v0, v1) in enumerate(filas):
            panel(IZQ, u0, u1, v0, v1, False)
    for i, (u0, u1) in enumerate([(-3.5, -1.75), (-1.75, 0.0), (0.0, 1.75), (1.75, 3.5)]):
        for j, (v0, v1) in enumerate([(1.5, 3.6), (3.6, 5.9)]):
            panel(DER, u0, u1, v0, v1, False, abollados.get(("D", i, j), 0.0))

    # ---- parches soldados (el minero repara la casa él mismo) -----------------------------------------------
    for pl, uc, vc, w, h, ang in ((FRENTE, -4.1, 2.05, 0.5, 0.44, 4), (DER, 2.45, 2.35, 0.78, 0.52, -3),
                                  (FONDO, 0.85, 3.05, 0.9, 0.62, 2), (FONDO, -3.55, 4.55, 0.52, 0.4, -6),
                                  (IZQ, 2.6, 4.6, 0.6, 0.45, 5)):
        _parche(p, pl, uc, vc, w, h, ang, rnd)

    # ---- respiradero redondo en el hastial (delante y detrás) -------------------------------------------------
    for pl, uc in ((FRENTE, -0.9), (FONDO, 0.0)):
        vc = 6.45
        c0 = pl.p(uc, vc, PANEL)
        b.revolucion([(0.36, 0), (0.36, 0.04), (0.3, 0.06), (0.27, 0.06), (0.27, -0.04)], c0, 14, "metal_oscuro",
                      eje=pl.n, tapa_ini=False, tapa_fin=False)
        b.revolucion([(0.27, -0.04), (0.0, -0.04)], c0, 14, "negro_mate", eje=pl.n, tapa_ini=False,
                     tapa_fin=False)
        for k in range(-2, 3):
            vv = k * 0.1
            w = math.sqrt(max(0.0, 0.27 ** 2 - vv ** 2)) - 0.01
            caja_plano(b, pl, uc - w, uc + w, vc + vv - 0.022, vc + vv + 0.022, PANEL - 0.03, PANEL + 0.02,
                       "metal_oscuro", sin=("+y",), giro_extra=rot("X", 35))
        for k in range(8):
            ang = math.tau * k / 8
            tornillo(p, pl.p(uc + math.cos(ang) * 0.32, vc + math.sin(ang) * 0.32, PANEL + 0.04), pl.n, 0.016,
                     "acero", en_baja=False)

    # ---- cantoneras: angulares en las cuatro esquinas ----------------------------------------------------------
    for sx in (-1, 1):
        for sy in (-1, 1):
            z0, z1 = 1.47, Z_LAT + 0.02
            xa = sorted((sx * (MX - 0.15), sx * (MX + PANEL + 0.035)))
            ya = sorted((sy * (MY + PANEL), sy * (MY + PANEL + 0.03)))
            b.caja_de((xa[0], ya[0], z0), (xa[1], ya[1], z1), "metal_oscuro",
                      sin=("+y" if sy < 0 else "-y",))
            xb = sorted((sx * (MX + PANEL), sx * (MX + PANEL + 0.03)))
            yb = sorted((sy * (MY - 0.15), sy * (MY + PANEL + 0.035)))
            b.caja_de((xb[0], yb[0], z0), (xb[1], yb[1], z1), "metal_oscuro",
                      sin=("+x" if sx < 0 else "-x",))
            for k in range(7):
                zz = z0 + 0.25 + k * (z1 - z0 - 0.5) / 6
                tornillo(p, (sx * (MX - 0.07), sy * (MY + PANEL + 0.03), zz), (0, sy, 0), 0.022, "acero",
                         en_baja=False)
                tornillo(p, (sx * (MX + PANEL + 0.03), sy * (MY - 0.07), zz), (sx, 0, 0), 0.022, "acero",
                         en_baja=False)
    return p


def _dentro(poly, u, v):
    dentro = False
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > v) != (y2 > v) and u < (x2 - x1) * (v - y1) / (y2 - y1 + 1e-12) + x1:
            dentro = not dentro
    return dentro


def _panel_abollado(c, pl, poly, grosor, prof):
    """Panel con un bollo: la cara de delante es una rejilla 4x4 con el centro hundido."""
    us = sorted({q[0] for q in poly})
    vs = sorted({q[1] for q in poly})
    u0, u1, v0, v1 = us[0], us[-1], vs[0], vs[-1]
    n = 4
    frente = {}
    for i in range(n + 1):
        for j in range(n + 1):
            fu, fv = i / n, j / n
            # Bollo descentrado (golpe de una carretilla o de una roca).
            hund = prof * math.exp(-((fu - 0.42) ** 2 / 0.05 + (fv - 0.38) ** 2 / 0.07))
            if i in (0, n) or j in (0, n):
                hund = 0.0
            frente[i, j] = c.v(pl.p(u0 + (u1 - u0) * fu, v0 + (v1 - v0) * fv, grosor - hund))
    for i in range(n):
        for j in range(n):
            c.cara([frente[i, j], frente[i + 1, j], frente[i + 1, j + 1], frente[i, j + 1]], "pintura_panel")
    borde = [(i, 0) for i in range(n)] + [(n, j) for j in range(n)] + [(i, n) for i in range(n, 0, -1)] + \
            [(0, j) for j in range(n, 0, -1)]
    atras = {k: c.v(pl.p(frente[k].co.dot(pl.u) - pl.o.dot(pl.u), frente[k].co.z, 0.0)) for k in borde}
    for k in range(len(borde)):
        k1, k2 = borde[k], borde[(k + 1) % len(borde)]
        c.cara([atras[k1], atras[k2], frente[k2], frente[k1]], "pintura_panel")


def _parche(p, pl, uc, vc, w, h, ang, rnd):
    """Chapa soldada encima de un panel: polígono irregular, con su cordón de soldadura en la malla alta."""
    pts = []
    esquinas = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    for k, (x, y) in enumerate(esquinas):
        # Esquinas recortadas a ojo (con la radial), cada una distinta.
        c1 = rnd.uniform(0.03, 0.09)
        c2 = rnd.uniform(0.03, 0.09)
        nx, ny = esquinas[(k + 1) % 4]
        px, py = esquinas[k - 1]
        d1 = Vector((px - x, py - y)).normalized() * c1
        d2 = Vector((nx - x, ny - y)).normalized() * c2
        pts.append((x + d1.x, y + d1.y))
        pts.append((x + d2.x, y + d2.y))
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = [(uc + x * ca - y * sa, vc + x * sa + y * ca) for x, y in pts]
    d0 = PANEL - 0.002
    mat = "parche_minio" if rnd.random() < 0.45 else "parche"
    p.baja.placa(pts, pl.p(0, 0, d0), pl.u, pl.v, pl.n, 0.02, mat)
    # Cordón de soldadura alrededor (malla alta).
    lazo = []
    cx = sum(q[0] for q in pts) / len(pts)
    cy = sum(q[1] for q in pts) / len(pts)
    for q in pts + [pts[0]]:
        dvec = Vector((q[0] - cx, q[1] - cy))
        dvec = dvec.normalized() * (dvec.length + 0.008)
        lazo.append(pl.p(cx + dvec.x, cy + dvec.y, d0 + 0.006))
    fino = []
    for i in range(len(lazo) - 1):
        for k in range(6):
            fino.append(lazo[i].lerp(lazo[i + 1], k / 6))
    fino.append(lazo[-1])
    p.alta.tubo(fino, 0.016, "soldadura", lados=6, tapa_ini=False, tapa_fin=False)
    # Tornillos que sujetaban el parche antes de soldarlo.
    for x, y in ((-w / 2 + 0.08, -h / 2 + 0.08), (w / 2 - 0.08, h / 2 - 0.08)):
        u = uc + x * ca - y * sa
        v = vc + x * sa + y * ca
        p.alta.cupula(pl.p(u, v, d0 + 0.02), pl.n, 0.024, "acero", alto=0.014)


# ---- techo --------------------------------------------------------------------------------------------------


def _perfil_nervios(y0, y1):
    """Puntos (y, alto sobre el valle) del perfil de la chapa entre y0 e y1 (nervios trapezoidales)."""
    corte = [0.0, 0.34, 0.45, 0.65, 0.76]
    alto = [0.0, 0.0, ONDA, ONDA, 0.0]

    def h(y):
        t = (y - Y_REF) % PASO
        for k in range(4):
            if corte[k] <= t <= corte[k + 1]:
                f = (t - corte[k]) / (corte[k + 1] - corte[k])
                return alto[k] + (alto[k + 1] - alto[k]) * f
        return 0.0

    ys = [y0]
    k0 = math.floor((y0 - Y_REF) / PASO)
    k1 = math.ceil((y1 - Y_REF) / PASO)
    for k in range(k0, k1 + 1):
        for cte in corte[1:4]:
            y = Y_REF + k * PASO + cte
            if y0 + 1e-4 < y < y1 - 1e-4:
                ys.append(y)
    ys.append(y1)
    return [(y, h(y)) for y in ys]


def techo():
    """Chapa grecada a dos aguas (cuatro chapas que se solapan), cumbrera y remates de los bordes."""
    p = Pieza("casa_techo", peso_uv=0.85)
    b = p.baja
    phi = math.atan(PEND)
    chapas = [(-1, -VUELO_Y, 0.34, "chapa_techo", 0.0), (-1, -0.13, VUELO_Y, "chapa_techo", 0.0),
              (1, -VUELO_Y, 0.34, "chapa_techo", 0.0), (1, -0.13, VUELO_Y, "chapa_nueva", 0.0)]
    for s, y0, y1, mat, _ in chapas:
        elev = CHAPA + 0.002 if y0 > -1 else 0.0  # la segunda chapa monta sobre la primera
        perfil = _perfil_nervios(y0, y1)
        anillos = []
        for x in (0.0, s * ALERO_X):
            zb = z_cresta(x) - ONDA + elev
            arriba = [Vector((x, y, zb + hh)) for y, hh in perfil]
            abajo = [Vector((x, y, zb + hh - CHAPA)) for y, hh in reversed(perfil)]
            anillos.append(arriba + abajo)
        b.loft(anillos, mat, tapa_ini=False, tapa_fin=True, suave=False)
        b.recalcular(b.ultimas)
        # Tornillos con arandela en las crestas, en las líneas de las correas (malla alta).
        for k in range(-7, 12):
            yc = Y_REF + k * PASO + 0.55
            if y0 + 0.1 < yc < y1 - 0.1:
                for xc in (0.45, 2.1, 3.7, 4.82):
                    x = s * xc
                    z = z_cresta(x) + elev
                    nrm = Vector((s * math.sin(phi), 0, math.cos(phi)))
                    p.alta.cupula((x, yc, z - 0.002), nrm, 0.04, "goma", alto=0.008, lados=10)
                    p.alta.cupula((x, yc, z + 0.004), nrm, 0.024, "acero", alto=0.018, lados=6)
    # Cumbrera: dos chapas lisas a caballo.
    for s in (-1, 1):
        g = rot("Y", s * math.degrees(phi))
        largo = 0.5
        cx = s * largo / 2 * math.cos(phi)
        cz = CUMBRE + 0.004 + CHAPA + 0.015 - PEND * abs(cx)
        b.caja((cx, 0, cz), (largo, 2 * VUELO_Y + 0.08, 0.024), "metal_oscuro", giro=g)
    # Remates de los hastiales: angular que tapa el canto de la chapa.
    for s in (-1, 1):
        g = rot("Y", s * math.degrees(phi))
        largo = ALERO_X / math.cos(phi)
        cx = s * ALERO_X / 2
        for sy in (-1, 1):
            zc = z_cresta(cx) + CHAPA * 0.5
            yv = sy * (VUELO_Y + 0.013)
            b.caja((cx, yv, zc - 0.07), (largo + 0.02, 0.026, 0.26), "metal_oscuro", giro=g)
            yf = sy * (VUELO_Y - 0.055)
            b.caja((cx, yf, zc + 0.065), (largo + 0.02, 0.16, 0.022), "metal_oscuro", giro=g)
    return p


def panel_solar():
    p = Pieza("casa_panel_solar", peso_uv=1.3)
    b, a = p.baja, p.alta
    phi = math.atan(PEND)
    M = rot("Y", math.degrees(phi))  # x local = pendiente abajo, y = a lo ancho, z = normal del faldón
    xc, yc = 2.55, -0.55
    O = Vector((xc, yc, z_cresta(xc)))
    A, B = 1.8, 2.6

    def caja(ca, cb, cc, ta, tb, tc, mat, **kw):
        return b.caja(O + M @ Vector((ca, cb, cc)), (ta, tb, tc), mat, giro=M, **kw)

    # Patas y raíles.
    for ca in (-0.55, 0.55):
        for cb in (-1.05, 1.05):
            caja(ca, cb, 0.03, 0.12, 0.12, 0.06, "aluminio", sin=("-z",))
        caja(ca, 0, 0.09, 0.08, B + 0.1, 0.06, "aluminio")
    # Cuerpo (la lámina de atrás, blanca, se ve entre las células) y marco.
    caja(0, 0, 0.145, A - 0.1, B - 0.1, 0.05, "pintura_gris", sin=("-x", "+x", "-y", "+y"))
    w = 0.07
    caja(-A / 2 + w / 2, 0, 0.155, w, B, 0.09, "aluminio")
    caja(A / 2 - w / 2, 0, 0.155, w, B, 0.09, "aluminio")
    caja(0, -B / 2 + w / 2, 0.155, A - 2 * w, w, 0.09, "aluminio", sin=("-x", "+x"))
    caja(0, B / 2 - w / 2, 0.155, A - 2 * w, w, 0.09, "aluminio", sin=("-x", "+x"))
    # Células: 3 x 4, un poco levantadas.
    ia, ib, gap = A - 2 * w, B - 2 * w, 0.03
    na, nb = 3, 4
    ca_ = (ia - (na + 1) * gap) / na
    cb_ = (ib - (nb + 1) * gap) / nb
    for i in range(na):
        for j in range(nb):
            pa = -ia / 2 + gap + ca_ / 2 + i * (ca_ + gap)
            pb = -ib / 2 + gap + cb_ / 2 + j * (cb_ + gap)
            caja(pa, pb, 0.177, ca_, cb_, 0.014, "celda_solar", sin=("-z",))
            # Pistas de las células (malla alta).
            for t in (-0.25, 0.25):
                a.caja(O + M @ Vector((pa, pb + t * cb_, 0.1845)), (ca_ * 0.96, 0.012, 0.002), "aluminio", giro=M)
            for t in range(6):
                a.caja(O + M @ Vector((pa - ca_ * 0.45 + t * ca_ * 0.18, pb, 0.1843)), (0.004, cb_ * 0.96, 0.0015),
                       "aluminio", giro=M)
    # Caja de conexiones, debajo, donde llega el cable.
    caja(0.62, -0.95, 0.09, 0.22, 0.26, 0.07, "negro_mate")
    for ca in (-A / 2 + 0.035, A / 2 - 0.035):
        for cb in (-1.1, -0.4, 0.4, 1.1):
            a.cupula(O + M @ Vector((ca, cb, 0.2)), M @ Vector((0, 0, 1)), 0.014, "acero", alto=0.008, lados=8)
    p.extra["conexion"] = list(O + M @ Vector((0.62, -1.08, 0.09)))
    return p


def chimenea():
    p = Pieza("casa_chimenea", peso_uv=1.2)
    b, a = p.baja, p.alta
    xc, yc = -2.35, 1.75
    zc = z_cresta(xc)
    phi = math.atan(PEND)
    g = rot("Y", -math.degrees(phi))
    b.caja((xc, yc, zc + 0.012), (0.9, 0.9, 0.03), "metal_oscuro", giro=g)
    b.caja_de((xc - 0.29, yc - 0.29, zc - 0.25), (xc + 0.29, yc + 0.29, zc + 0.3), "metal_hollin", sin=("-z",))
    boca = 7.8
    b.revolucion([(0.21, zc + 0.3), (0.21, boca - 0.4), (0.205, boca)], (xc, yc, 0), 12, "metal_hollin",
                 tapa_ini=False, tapa_fin=True)
    for zb in (zc + 0.75, zc + 1.2):
        b.revolucion([(0.228, 0), (0.228, 0.06)], (xc, yc, zb), 12, "metal_hollin")
    # Sombrerete contra la lluvia, sobre tres patas.
    zs = boca + 0.13
    b.revolucion([(0.42, 0), (0.42, 0.03), (0.0, 0.25)], (xc, yc, zs), 12, "metal_hollin", tapa_ini=True)
    for k in range(3):
        ang = math.radians(90 + k * 120)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        p0 = Vector((xc, yc, boca - 0.08)) + d * 0.21
        p1 = Vector((xc, yc, zs + 0.01)) + d * 0.3
        mid = (p0 + p1) / 2
        dirv = (p1 - p0).normalized()
        q = dirv.to_track_quat("Z", "X").to_matrix()
        b.caja(mid, (0.05, 0.012, (p1 - p0).length), "metal_oscuro", giro=q)
    # Costura remachada del tubo (malla alta).
    for zr in (zc + 0.55, boca - 0.25):
        for k in range(10):
            ang = math.tau * k / 10
            d = Vector((math.cos(ang), math.sin(ang), 0))
            a.cupula(Vector((xc, yc, zr)) + d * 0.21, d, 0.016, "acero", alto=0.01, lados=8)
    p.extra["humo"] = [xc, yc, boca]
    return p


def canalon():
    p = Pieza("casa_canalon", peso_uv=1.0)
    b = p.baja
    exterior = [(-4.985, 5.62), (-4.995, 5.49), (-5.06, 5.425), (-5.2, 5.415), (-5.285, 5.465), (-5.33, 5.6),
                (-5.31, 5.625)]
    grosor = 0.02
    interior = [(-5.005, 5.62), (-5.012, 5.5), (-5.07, 5.445), (-5.195, 5.437), (-5.265, 5.475), (-5.305, 5.6),
                (-5.3, 5.61)]
    perfil = exterior + list(reversed(interior))
    anillos = [[Vector((x, y, z)) for x, z in perfil] for y in (-4.1, 4.1)]
    b.loft(anillos, "metal_oscuro", tapa_ini=False, tapa_fin=False, suave=False)
    b.recalcular(b.ultimas)
    # Tapas de los extremos.
    for y, n in ((-4.1, -1), (4.1, 1)):
        b.placa([(x, z) for x, z in exterior], Vector((0, y, 0)),
                Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, n, 0)), grosor, "metal_oscuro", atras=True)
    # Abrazaderas (ganchos que sujetan el canalón).
    for y in (-2.7, 0.0, 2.7):
        camino = [Vector((-4.93, y, 5.635)), Vector((-4.99, y, 5.5)), Vector((-5.06, y, 5.405)),
                  Vector((-5.2, y, 5.395)), Vector((-5.3, y, 5.455)), Vector((-5.35, y, 5.63))]
        b.tubo(camino, 0.014, "metal_oscuro", lados=4, radio_curva=0.03, pasos_curva=1)
    return p


def bajante():
    p = Pieza("casa_bajante", peso_uv=1.2)
    b, a = p.baja, p.alta
    yb = -3.2
    xg = -5.135
    xw = -4.78
    camino = [(xg, yb, 5.47), (xg, yb, 5.2), (xw, yb, 4.82), (xw, yb, 0.95), (-5.03, yb, 0.66)]
    r = 0.1
    b.tubo(camino, r, "metal_oscuro", lados=8, radio_curva=0.2, pasos_curva=3, tapa_ini=False, tapa_fin=False)
    # Boca del bajante: el tubo tiene grosor y se ve por dentro.
    fin = Vector(camino[-1])
    dirv = (Vector(camino[-1]) - Vector(camino[-2])).normalized()
    b.revolucion([(r, 0), (r * 0.8, 0), (r * 0.8, -0.16), (0.0, -0.16)], fin, 8, "metal_oscuro", eje=dirv,
                 tapa_ini=False, tapa_fin=False, giro=math.pi / 8, mats_tramo=["metal_oscuro", "negro_mate",
                                                                               "negro_mate"])
    # Tres abrazaderas a la pared.
    for z in (4.3, 2.95, 1.78):
        b.revolucion([(0.122, 0), (0.122, 0.075)], (xw, yb, z - 0.037), 8, "metal_oscuro", giro=math.pi / 8)
        b.caja_de((xw + 0.115, yb - 0.02, z - 0.03), (-4.555, yb + 0.02, z + 0.03), "metal_oscuro")
        b.caja_de((-4.575, yb - 0.09, z - 0.09), (-4.555, yb + 0.09, z + 0.09), "metal_oscuro", sin=("+x",))
        for dy in (-0.055, 0.055):
            tornillo(p, (-4.575, yb + dy, z), (-1, 0, 0), 0.02, "acero", en_baja=False)
        a.cupula((xw - 0.122, yb, z), (-1, 0, 0), 0.02, "acero", alto=0.012)
    p.extra["pie"] = [-5.1, yb, 0.0]
    return p


# ======================================================================================================
# Puerta
# ======================================================================================================


def puerta():
    """Hoja de madera de tablas con travesaños de hierro, bisagras, manija y cerradura. Pivote en las bisagras."""
    h = HOJA
    p = Pieza("puerta", pivote=(EJE_PUERTA.x, EJE_PUERTA.y, h["z0"]), peso_uv=1.7)
    b, a = p.baja, p.alta
    # Tablas verticales con su separación.
    n = 5
    gap = 0.025
    w = (h["x1"] - h["x0"] - (n - 1) * gap) / n
    centros = []
    for i in range(n):
        x0 = h["x0"] + i * (w + gap)
        centros.append(x0 + w / 2)
        b.caja_de((x0, h["y0"], h["z0"]), (x0 + w, h["y0"] + 0.12, h["z1"]), "madera_puerta", sin=("-z",))
    # Tablero de detrás (lo que se ve por las rendijas) y travesaños por dentro con la riostra en Z.
    b.caja_de((h["x0"] + 0.01, h["y0"] + 0.12, h["z0"] + 0.02), (h["x1"] - 0.01, h["y0"] + 0.15, h["z1"] - 0.02),
              "madera_oscura", sin=("-z", "+z", "-y"))
    yt0, yt1 = h["y0"] + 0.15, h["y0"] + 0.22
    for zt in (1.2, 4.28):
        b.caja_de((h["x0"] + 0.07, yt0, zt - 0.15), (h["x1"] - 0.07, yt1, zt + 0.15), "madera_oscura", sin=("-y",))
    pa, pb = Vector((h["x0"] + 0.2, (yt0 + yt1) / 2, 1.38)), Vector((h["x1"] - 0.2, (yt0 + yt1) / 2, 4.1))
    d = pb - pa
    ang = math.atan2(d.x, d.z)
    b.caja((pa + pb) / 2, (0.24, yt1 - yt0, d.length - 0.1), "madera_oscura", giro=rot("Y", math.degrees(ang)),
           sin=("-y",))
    # Clavos de los travesaños (malla alta, por dentro).
    for zt in (1.2, 4.28):
        for x in centros:
            for dz in (-0.08, 0.08):
                a.cupula((x, yt1, zt + dz), (0, 1, 0), 0.018, "hierro", alto=0.01, lados=8)
    # Dos barras de hierro por fuera, con un perno por tabla.
    yf = h["y0"]
    for zb in (1.78, 3.72):
        b.caja_de((h["x0"] + 0.06, yf - 0.025, zb - 0.075), (h["x1"] - 0.06, yf, zb + 0.075), "hierro",
                  sin=("+y",))
        for x in centros:
            tornillo(p, (x, yf - 0.025, zb), (0, -1, 0), 0.034, "hierro")
    # Bisagras: hoja en punta sobre la puerta + nudillo central (los de arriba y abajo son del marco).
    for zh in BISAGRAS_Z:
        hoja = [(EJE_PUERTA.x, -0.1), (h["x0"] + 0.45, -0.075), (h["x0"] + 0.6, 0.0), (h["x0"] + 0.45, 0.075),
                (EJE_PUERTA.x, 0.1)]
        b.placa([(x, zh + z) for x, z in hoja], Vector((0, yf, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)),
                Vector((0, -1, 0)), 0.025, "hierro")
        b.cilindro((EJE_PUERTA.x, EJE_PUERTA.y, zh - 0.062), (0, 0, 1), 0.06, 0.124, "hierro", lados=8)
        for x in (h["x0"] + 0.15, h["x0"] + 0.4):
            tornillo(p, (x, yf - 0.025, zh), (0, -1, 0), 0.026, "hierro")
    # Manija: placa con 4 tornillos, roseta y palanca.
    m = MANIJA
    b.caja_de((m.x - 0.09, yf - 0.03, m.z - 0.3), (m.x + 0.09, yf, m.z + 0.12), "acero", sin=("+y",))
    for dx in (-0.055, 0.055):
        for dz in (-0.26, 0.08):
            tornillo(p, (m.x + dx, yf - 0.03, m.z + dz), (0, -1, 0), 0.02, "acero")
    b.cilindro((m.x, yf - 0.03, m.z), (0, -1, 0), 0.055, 0.045, "acero_pulido", lados=10, tapa_ini=False)
    palanca = [(m.x, yf - 0.06, m.z), (m.x, yf - 0.15, m.z), (m.x - 0.3, yf - 0.17, m.z - 0.01)]
    b.tubo(palanca, 0.03, "acero_pulido", lados=8, radio_curva=0.06, pasos_curva=3, tapa_ini=False)
    # Cerradura: placa de latón con el ojo de la llave de verdad (agujero con fondo).
    _cerradura(b, Vector((m.x, yf - 0.03, m.z - 0.18)))
    for dz in (-0.1, 0.1):
        tornillo(p, (m.x, yf - 0.052, m.z - 0.18 + dz), (0, -1, 0), 0.014, "laton", lados_baja=5)
    p.extra["manija_agarre"] = [m.x - 0.22, yf - 0.17, m.z - 0.01]
    return p


def _cerradura(c, centro, u=Vector((1, 0, 0)), v=Vector((0, 0, 1)), n=Vector((0, -1, 0)), mat="laton"):
    """Placa de cerradura (0,13 x 0,2) con el ojo de la llave: círculo + ranura, hundido 2 centésimas."""
    lados = 16
    cx, cy = 0.0, 0.0

    def dentro_ojo(x, y):
        return (x ** 2 + (y - 0.022) ** 2 <= 0.022 ** 2) or (abs(x) <= 0.009 and -0.04 <= y <= 0.022)

    def rayo(ang, dentro):
        lo, hi = 0.0, 0.3
        for _ in range(30):
            mid = (lo + hi) / 2
            if dentro(cx + math.cos(ang) * mid, cy + math.sin(ang) * mid):
                lo = mid
            else:
                hi = mid
        return (cx + math.cos(ang) * lo, cy + math.sin(ang) * lo)

    angs = [math.tau * k / lados + math.pi / 2 for k in range(lados)]
    ext = [rayo(an, lambda x, y: abs(x) <= 0.065 and abs(y) <= 0.1) for an in angs]
    inte = [rayo(an, dentro_ojo) for an in angs]
    c.anillo_placa(ext, inte, centro, u, v, n, 0.022, mat, fondo=0.02, mat_fondo="negro_mate",
                   mat_hueco="negro_mate")


def puerta_marco():
    """Marco metálico de la puerta: jambas, dintel, forro del hueco, burlete de goma, umbral y bisagras fijas."""
    p = Pieza("puerta_marco", peso_uv=1.3)
    b, a = p.baja, p.alta
    x0, x1, z1 = PUERTA["x0"], PUERTA["x1"], PUERTA["z1"]
    yf = -MY - 0.16  # cara del marco
    t = 0.2
    b.caja_de((x0 - 0.12, yf, BASE_Z), (x0 + 0.08, -MY - PANEL, z1 + 0.18), "metal_oscuro", sin=("+y", "-z"))
    b.caja_de((x1 - 0.08, yf, BASE_Z), (x1 + 0.12, -MY - PANEL, z1 + 0.18), "metal_oscuro", sin=("+y", "-z"))
    b.caja_de((x0 + 0.08, yf, z1 - 0.02), (x1 - 0.08, -MY - PANEL, z1 + 0.18), "metal_oscuro", sin=("+y",))
    # Forro del hueco (la otra pata de la L), de la cara del marco hasta dentro.
    b.caja_de((x0 + 0.08, -MY - PANEL, 0.6), (x0 + 0.12, -MY + MURO, z1 - 0.02), "metal_oscuro", sin=("-x",))
    b.caja_de((x1 - 0.12, -MY - PANEL, 0.6), (x1 - 0.08, -MY + MURO, z1 - 0.02), "metal_oscuro", sin=("+x",))
    b.caja_de((x0 + 0.08, -MY - PANEL, z1 - 0.1), (x1 - 0.08, -MY + MURO, z1 - 0.02), "metal_oscuro",
              sin=("+z", "-x", "+x"))
    # Burlete de goma alrededor de la hoja (se ve como una línea negra).
    yg0, yg1 = HOJA["y0"] + 0.02, HOJA["y1"] - 0.02
    b.caja_de((x0 + 0.12, yg0, 0.6), (x0 + 0.145, yg1, z1 - 0.1), "goma", sin=("-x", "-z", "+z"))
    b.caja_de((x1 - 0.145, yg0, 0.6), (x1 - 0.12, yg1, z1 - 0.1), "goma", sin=("+x", "-z", "+z"))
    b.caja_de((x0 + 0.12, yg0, z1 - 0.125), (x1 - 0.12, yg1, z1 - 0.1), "goma", sin=("+z", "-x", "+x"))
    # Umbral con estrías antideslizantes (malla alta).
    b.caja_de((x0 + 0.08, yf, BASE_Z), (x1 - 0.08, -MY + MURO, 0.6), "acero", sin=("-z",))
    for k in range(14):
        y = yf + 0.03 + k * 0.034
        a.caja_de((x0 + 0.12, y, 0.6), (x1 - 0.12, y + 0.012, 0.606), "acero")
    # Parte fija de las bisagras: pala sobre la jamba, nudillos y pasador con remate.
    e = EJE_PUERTA
    for zh in BISAGRAS_Z:
        b.caja_de((x0 - 0.1, yf - 0.02, zh - 0.1), (e.x - 0.03, yf, zh + 0.1), "hierro", sin=("+y",))
        for z0 in (zh - 0.19, zh + 0.066):
            b.cilindro((e.x, e.y, z0), (0, 0, 1), 0.06, 0.124, "hierro", lados=8)
        b.revolucion([(0.025, 0), (0.025, 0.04), (0.035, 0.05), (0.0, 0.085)], (e.x, e.y, zh + 0.19), 8, "hierro",
                     tapa_ini=False)
        b.revolucion([(0.0, -0.085), (0.035, -0.05), (0.025, -0.04), (0.025, 0)], (e.x, e.y, zh - 0.19), 8, "hierro",
                     tapa_fin=False)
        for x in (x0 - 0.06, x0 + 0.02):
            tornillo(p, (x, yf - 0.02, zh), (0, -1, 0), 0.024, "hierro")
    # Tornillos del marco (malla alta).
    for z in (0.9, 1.9, 2.9, 3.9, 4.8):
        for x in (x0 - 0.02, x1 + 0.02):
            tornillo(p, (x, yf, z), (0, -1, 0), 0.022, "acero", en_baja=False)
    return p


# ======================================================================================================
# Ventanas
# ======================================================================================================


def _marco_ventana(p, pl, u0, u1, v0, v1, ancho=0.16, con_inferior=True, fondo_vidrio=-0.08):
    """Marco en L: tapajuntas en la fachada + forro del hueco. Devuelve la profundidad del vidrio."""
    b = p.baja
    dF = PANEL + 0.05
    caja_plano(b, pl, u0 - ancho, u0, v0 - (ancho if con_inferior else 0), v1 + ancho, PANEL, dF, "metal_oscuro",
               sin=("+y",))
    caja_plano(b, pl, u1, u1 + ancho, v0 - (ancho if con_inferior else 0), v1 + ancho, PANEL, dF, "metal_oscuro",
               sin=("+y",))
    caja_plano(b, pl, u0, u1, v1, v1 + ancho, PANEL, dF, "metal_oscuro", sin=("+y", "-x", "+x"))
    if con_inferior:
        caja_plano(b, pl, u0, u1, v0 - ancho, v0, PANEL, dF, "metal_oscuro", sin=("+y", "-x", "+x"))
    t = 0.04
    caja_plano(b, pl, u0, u0 + t, v0, v1, -MURO, dF, "metal_oscuro", sin=("-x",))
    caja_plano(b, pl, u1 - t, u1, v0, v1, -MURO, dF, "metal_oscuro", sin=("+x",))
    caja_plano(b, pl, u0 + t, u1 - t, v1 - t, v1, -MURO, dF, "metal_oscuro", sin=("+z", "-x", "+x"))
    caja_plano(b, pl, u0 + t, u1 - t, v0, v0 + t, -MURO, dF, "metal_oscuro", sin=("-z", "-x", "+x"))
    # Junquillos que sujetan el vidrio.
    j = 0.05
    d0, d1 = fondo_vidrio, fondo_vidrio + 0.04
    caja_plano(b, pl, u0 + t, u0 + t + j, v0 + t, v1 - t, d0, d1, "metal_oscuro", sin=("+y", "-x"))
    caja_plano(b, pl, u1 - t - j, u1 - t, v0 + t, v1 - t, d0, d1, "metal_oscuro", sin=("+y", "+x"))
    caja_plano(b, pl, u0 + t + j, u1 - t - j, v1 - t - j, v1 - t, d0, d1, "metal_oscuro", sin=("+y", "+z", "-x", "+x"))
    caja_plano(b, pl, u0 + t + j, u1 - t - j, v0 + t, v0 + t + j, d0, d1, "metal_oscuro",
               sin=("+y", "-z", "-x", "+x"))
    for uu in (u0 - ancho / 2, u1 + ancho / 2):
        for vv in (v0 + 0.15, (v0 + v1) / 2, v1 - 0.05):
            tornillo(p, pl.p(uu, vv, dF), pl.n, 0.02, "acero", en_baja=False)
    return t


def ventana_frontal():
    """Devuelve las piezas de la ventana grande: marco, cristal, contraventanas, alféizar, cortinas y maceta."""
    V = VENTANA
    pl = FRENTE
    marco = Pieza("ventana_frontal_marco", peso_uv=1.3)
    t = _marco_ventana(marco, pl, V["x0"], V["x1"], V["z0"], V["z1"], con_inferior=False)
    b = marco.baja
    # Parteluz y travesaño (cuatro cristales).
    um = (V["x0"] + V["x1"]) / 2
    vm = 3.45
    caja_plano(b, pl, um - 0.035, um + 0.035, V["z0"] + t, V["z1"] - t, -0.08, -0.025, "metal_oscuro", sin=("+y",))
    caja_plano(b, pl, V["x0"] + t, um - 0.035, vm - 0.035, vm + 0.035, -0.08, -0.025, "metal_oscuro",
               sin=("+y", "+x"))
    caja_plano(b, pl, um + 0.035, V["x1"] - t, vm - 0.035, vm + 0.035, -0.08, -0.025, "metal_oscuro",
               sin=("+y", "-x"))
    # Pernios de las contraventanas (fijos al marco).
    ejes = {"izq": (V["x0"] - 0.18, -MY - 0.16), "der": (V["x1"] + 0.18, -MY - 0.16)}
    for lado, (ex, ey) in ejes.items():
        xa, xb = (ex - 0.02, ex + 0.16) if lado == "izq" else (ex - 0.16, ex + 0.02)
        for zh in (2.32 + 0.22, 4.66 - 0.22):
            # Pernio: pletina sobre el tapajuntas y pasador vertical donde encaja el nudillo.
            b.caja_de((xa, ey, zh - 0.14), (xb, -MY - PANEL - 0.05, zh - 0.07), "hierro", sin=("+y",))
            b.cilindro((ex, ey, zh - 0.12), (0, 0, 1), 0.022, 0.21, "hierro", lados=6)

    cristal = Pieza("ventana_frontal_cristal", peso_uv=0.6)
    caja_plano(cristal.baja, pl, V["x0"] + t, V["x1"] - t, V["z0"] + t, V["z1"] - t, -0.13, -0.08, "vidrio")

    alfeizar = Pieza("ventana_frontal_alfeizar", peso_uv=1.2)
    ab = alfeizar.baja
    caja_plano(ab, pl, V["x0"] - 0.24, V["x1"] + 0.24, V["z0"] - 0.15, V["z0"], -MURO + 0.05, 0.44, "losa",
               sin=("+y",), giro_extra=rot("X", -2.0))
    # Goterón por debajo (malla alta) y dos ménsulas de hierro.
    caja_plano(alfeizar.alta, pl, V["x0"] - 0.2, V["x1"] + 0.2, V["z0"] - 0.16, V["z0"] - 0.145, 0.36, 0.38,
               "negro_mate")
    for uu in (V["x0"] + 0.25, V["x1"] - 0.25):
        mens = [(0.0, 0.0), (0.0, -0.32), (0.06, -0.32), (0.34, -0.02), (0.34, 0.0)]
        ab.placa([(dd, vv + V["z0"] - 0.15) for dd, vv in mens], pl.p(uu - 0.02, 0, PANEL), pl.n, Vector((0, 0, 1)),
                 pl.u, 0.04, "hierro", atras=True)

    contra_izq = _contraventana("ventana_frontal_contraventana_izq", ejes["izq"], +1, ANG_CONTRA_IZQ)
    contra_der = _contraventana("ventana_frontal_contraventana_der", ejes["der"], -1, ANG_CONTRA_DER)

    cortinas = Pieza("ventana_frontal_cortinas", peso_uv=0.9)
    _cortinas(cortinas, pl, V, t)

    maceta = Pieza("maceta_pequena", peso_uv=2.0)
    _maceta_pequena(maceta, Vector((V["x1"] - 0.5, -MY - 0.3, V["z0"] - 0.012)))
    return [marco, cristal, alfeizar, contra_izq, contra_der, cortinas, maceta]


def _contraventana(nombre, eje, sentido, angulo):
    """
    Contraventana de tablas con travesaños y riostra, con sus bisagras. Se construye cerrada (sentido = +1: se
    extiende hacia +x desde el eje) y luego se gira alrededor del eje de las bisagras (pivote del objeto).
    """
    ex, ey = eje
    z0, z1 = 2.32, 4.66
    p = Pieza(nombre, pivote=(ex, ey, z0), peso_uv=1.3)
    b, a = p.baja, p.alta
    ancho = 1.5
    yb = -MY - 0.17  # cara de atrás cuando está cerrada
    n = 4
    gap = 0.02
    w = (ancho - 0.02 - (n - 1) * gap) / n
    for i in range(n):
        xa = ex + sentido * (0.02 + i * (w + gap))
        xb = xa + sentido * w
        b.caja_de((min(xa, xb), yb - 0.07, z0), (max(xa, xb), yb, z1), "madera_pintada", sin=("-z",))
    xf = ex + sentido * ancho
    xin, xout = min(ex + sentido * 0.05, xf - sentido * 0.04), max(ex + sentido * 0.05, xf - sentido * 0.04)
    for zt in (z0 + 0.22, z1 - 0.22):
        b.caja_de((xin, yb - 0.12, zt - 0.09), (xout, yb - 0.07, zt + 0.09), "madera_pintada", sin=("+y",))
    # Riostra en diagonal (de abajo junto a las bisagras a arriba en el lado libre).
    pa = Vector((ex + sentido * 0.25, yb - 0.095, z0 + 0.35))
    pb = Vector((xf - sentido * 0.25, yb - 0.095, z1 - 0.35))
    d = pb - pa
    b.caja((pa + pb) / 2, (0.16, 0.05, d.length - 0.12), "madera_pintada",
           giro=rot("Y", math.degrees(math.atan2(d.x, d.z))), sin=("+y",))
    # Bisagras: pala en punta sobre el travesaño + nudillo en el eje.
    for zt in (z0 + 0.22, z1 - 0.22):
        hoja = [(0.0, -0.06), (0.55, -0.04), (0.65, 0.0), (0.55, 0.04), (0.0, 0.06)]
        pts = [(ex + sentido * x, zt + z) for x, z in hoja]
        b.placa(pts, Vector((0, yb - 0.12, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)), 0.018,
                "hierro")
        b.cilindro((ex, ey, zt - 0.06), (0, 0, 1), 0.04, 0.12, "hierro", lados=8)
        # Codo de la pala hasta el nudillo.
        b.caja_de((min(ex, ex + sentido * 0.07), yb - 0.135, zt - 0.05), (max(ex, ex + sentido * 0.07), ey - 0.02,
                                                                          zt + 0.05), "hierro")
        for x in (0.2, 0.45):
            tornillo(p, (ex + sentido * x, yb - 0.138, zt), (0, -1, 0), 0.02, "hierro", en_baja=False)
    # Gira la contraventana a su posición entreabierta.
    giro = Matrix.Translation((ex, ey, 0)) @ Matrix.Rotation(math.radians(-sentido * angulo), 4, "Z") @ \
        Matrix.Translation((-ex, -ey, 0))
    for c in (b, a):
        c.transformar(c.bm.verts, giro)
    p.extra["angulo_abierta"] = angulo
    return p


def _cortinas(p, pl, V, t):
    b = p.baja
    d = -0.21
    zt, zb = V["z1"] - t - 0.06, V["z0"] + t + 0.04
    b.cilindro(pl.p(V["x0"] + t, zt + 0.03, d), (1, 0, 0), 0.018, V["x1"] - V["x0"] - 2 * t, "acero", lados=6,
               tapa_ini=False, tapa_fin=False)
    for lado in (0, 1):
        sg = 1 if lado == 0 else -1
        borde = V["x0"] + t + 0.02 if lado == 0 else V["x1"] - t - 0.02
        anillos = []
        for v, ancho, amp in ((zt, 0.95, 0.03), (3.15, 0.42, 0.045), (zb, 0.62, 0.035)):
            ondas = 5
            k = 2 * ondas
            delante, detras = [], []
            for i in range(k + 1):
                f = i / k
                x = borde + sg * f * ancho
                y = amp * (1 if i % 2 else -1) * (0.6 if i in (0, k) else 1.0)
                delante.append(pl.p(x, v, d - 0.035 + y))
                detras.append(pl.p(x, v, d - 0.035 + y + 0.012))
            anillos.append(delante + list(reversed(detras)))
        b.loft(anillos, "tela", tapa_ini=False, tapa_fin=True, suave=True)
        b.recalcular(b.ultimas)
        # Alzapaños (malla alta).
        p.alta.tubo([pl.p(borde, 3.17, d - 0.09), pl.p(borde + sg * 0.25, 3.15, d - 0.1),
                     pl.p(borde + sg * 0.45, 3.15, d - 0.05)], 0.02, "tela", lados=6)


def _maceta_pequena(p, base):
    """Maceta de barro con tierra y una planta de cuatro hojas."""
    b = p.baja
    perfil = [(0.11, 0.0), (0.15, 0.22), (0.175, 0.235), (0.175, 0.3), (0.152, 0.3), (0.142, 0.255)]
    b.revolucion(perfil, base, 10, "barro", tapa_ini=True, oculta_ini=True, tapa_fin=True, mat_fin="tierra")
    # Tallo y hojas.
    tallo_base = base + Vector((0, 0, 0.255))
    tallo = [tallo_base, tallo_base + Vector((0.01, 0.0, 0.12)), tallo_base + Vector((-0.01, 0.01, 0.24))]
    b.tubo(tallo, 0.012, "hoja", lados=5, tapa_ini=False)
    hojas = [(tallo[1], 30, 0.28, 0.1, 0.1), (tallo[1], 155, 0.26, 0.09, 0.12), (tallo[2], 250, 0.3, 0.11, 0.08),
             (tallo[2], 75, 0.24, 0.09, 0.06)]
    for origen, rumbo, largo, ancho, caida in hojas:
        _hoja(b, origen, math.radians(rumbo), largo, ancho, caida, subida=0.12)
    # Pequeñas piedras sobre la tierra (malla alta).
    rnd = random.Random(5)
    for _ in range(8):
        ang, r = rnd.uniform(0, math.tau), rnd.uniform(0.03, 0.12)
        p.alta.cupula(base + Vector((math.cos(ang) * r, math.sin(ang) * r, 0.255)), (0, 0, 1), 0.014, "losa",
                      alto=0.01, lados=6)


def _hoja(c, origen, rumbo, largo, ancho, caida, subida=0.1, secciones=5):
    """Hoja con volumen: sección en V (nervio central) y un poco de grosor, que se curva hacia abajo."""
    dirv = Vector((math.cos(rumbo), math.sin(rumbo), 0))
    lado = Vector((-dirv.y, dirv.x, 0))
    anillos = []
    for k in range(secciones + 1):
        f = k / secciones
        centro = origen + dirv * largo * f + Vector((0, 0, subida * math.sin(math.pi * f * 0.8) - caida * f * f))
        w = max(0.004, ancho / 2 * math.sin(math.pi * min(1.0, f * 1.05)) ** 0.7)
        grosor = 0.006
        anillos.append([centro - lado * w, centro + Vector((0, 0, 0.12 * w)), centro + lado * w,
                        centro + Vector((0, 0, 0.12 * w - grosor))])
    c.loft(anillos, "hoja", tapa_ini=True, tapa_fin=True, suave=True)
    c.recalcular(c.ultimas)


def ventana_lateral():
    pl = IZQ
    L = VLAT
    marco = Pieza("ventana_lateral_marco", peso_uv=1.2)
    t = _marco_ventana(marco, pl, L["u0"], L["u1"], L["v0"], L["v1"], ancho=0.14)
    caja_plano(marco.baja, pl, L["u0"] + t, L["u1"] - t, 3.62, 3.68, -0.08, -0.03, "metal_oscuro", sin=("+y",))
    cristal = Pieza("ventana_lateral_cristal", peso_uv=0.6)
    caja_plano(cristal.baja, pl, L["u0"] + t, L["u1"] - t, L["v0"] + t, L["v1"] - t, -0.13, -0.08, "vidrio")

    rej = Pieza("rejilla_ventilacion", peso_uv=1.6)
    R = REJILLA
    b = rej.baja
    dF = PANEL + 0.06
    caja_plano(b, pl, R["u0"], R["u1"], R["v0"], R["v1"], PANEL, PANEL + 0.01, "negro_mate", sin=("+y", "-x", "+x",
                                                                                                  "-z", "+z"))
    m = 0.06
    caja_plano(b, pl, R["u0"], R["u0"] + m, R["v0"], R["v1"], PANEL, dF, "metal_oscuro", sin=("+y",))
    caja_plano(b, pl, R["u1"] - m, R["u1"], R["v0"], R["v1"], PANEL, dF, "metal_oscuro", sin=("+y",))
    caja_plano(b, pl, R["u0"] + m, R["u1"] - m, R["v0"], R["v0"] + m, PANEL, dF, "metal_oscuro",
               sin=("+y", "-x", "+x"))
    caja_plano(b, pl, R["u0"] + m, R["u1"] - m, R["v1"] - m, R["v1"], PANEL, dF, "metal_oscuro",
               sin=("+y", "-x", "+x"))
    # Parrilla: barrotes que se cruzan y dejan huecos de verdad.
    nu, nv = 6, 3
    for i in range(1, nu):
        uu = R["u0"] + m + (R["u1"] - R["u0"] - 2 * m) * i / nu
        caja_plano(b, pl, uu - 0.012, uu + 0.012, R["v0"] + m, R["v1"] - m, PANEL + 0.01, dF - 0.012, "metal_oscuro",
                   sin=("+y", "-z", "+z"))
    for j in range(1, nv):
        vv = R["v0"] + m + (R["v1"] - R["v0"] - 2 * m) * j / nv
        caja_plano(b, pl, R["u0"] + m, R["u1"] - m, vv - 0.012, vv + 0.012, PANEL + 0.025, dF - 0.005,
                   "metal_oscuro", sin=("+y", "-x", "+x"))
    # Malla fina contra insectos detrás (malla alta).
    for i in range(1, 22):
        uu = R["u0"] + m + (R["u1"] - R["u0"] - 2 * m) * i / 22
        caja_plano(rej.alta, pl, uu - 0.003, uu + 0.003, R["v0"] + m, R["v1"] - m, PANEL + 0.01, PANEL + 0.016,
                   "acero")
    for uu in (R["u0"] + 0.03, R["u1"] - 0.03):
        for vv in (R["v0"] + 0.03, R["v1"] - 0.03):
            tornillo(rej, pl.p(uu, vv, dF), pl.n, 0.016, "acero", en_baja=False)
    return [marco, cristal, rej]


# ======================================================================================================
# Detalles de fachada
# ======================================================================================================


def placa_numero():
    p = Pieza("placa_numero", peso_uv=2.5)
    b = p.baja
    pl = FRENTE
    uc, vc = -0.25, 4.15
    w, h, ch = 0.4, 0.52, 0.05
    contorno = [(-w / 2 + ch, -h / 2), (w / 2 - ch, -h / 2), (w / 2, -h / 2 + ch), (w / 2, h / 2 - ch),
                (w / 2 - ch, h / 2), (-w / 2 + ch, h / 2), (-w / 2, h / 2 - ch), (-w / 2, -h / 2 + ch)]
    b.placa([(uc + x, vc + y) for x, y in contorno], pl.p(0, 0, PANEL), pl.u, pl.v, pl.n, 0.025, "metal_oscuro")
    # El «7» en relieve, de latón.
    siete = [(-0.11, 0.165), (0.115, 0.165), (0.115, 0.115), (-0.015, -0.17), (-0.085, -0.17), (0.035, 0.105),
             (-0.11, 0.105)]
    b.placa([(uc + x, vc + y - 0.01) for x, y in siete], pl.p(0, 0, PANEL + 0.025), pl.u, pl.v, pl.n, 0.022, "laton")
    for x in (-w / 2 + 0.05, w / 2 - 0.05):
        for y in (-h / 2 + 0.05, h / 2 - 0.05):
            tornillo(p, pl.p(uc + x, vc + y, PANEL + 0.025), pl.n, 0.018, "laton", lados_baja=6)
    # Filete en relieve alrededor (malla alta).
    filete = [pl.p(uc + x, vc + y, PANEL + 0.026) for x, y in [(-0.17, -0.235), (0.17, -0.235), (0.175, 0.235),
                                                                  (-0.175, 0.235), (-0.17, -0.235)]]
    p.alta.tubo(filete, 0.006, "laton", lados=4, tapa_ini=False, tapa_fin=False)
    return p


def buzon():
    """Buzón de pared con tapa abatible (entreabierta: hay una carta) y banderita levantada."""
    pl = FRENTE
    u0, u1, v0, v1 = 3.3, 4.08, 2.95, 3.55
    d0, d1 = 0.1, 0.5
    cuerpo = Pieza("buzon", peso_uv=1.8)
    b = cuerpo.baja
    # Soporte a la pared.
    caja_plano(b, pl, u0 + 0.06, u1 - 0.06, v0 - 0.12, v1 - 0.05, PANEL, d0, "metal_oscuro", sin=("+y",))
    # Caja abierta por arriba (con grosor de chapa): anillo extruido hacia arriba con fondo.
    t = 0.022
    ext = [(u0, d0), (u1, d0), (u1, d1), (u0, d1)]
    inte = [(u0 + t, d0 + t), (u1 - t, d0 + t), (u1 - t, d1 - t), (u0 + t, d1 - t)]
    origen = pl.p(0, v0, 0)
    b.anillo_placa(ext, inte, origen, pl.u, pl.n, Vector((0, 0, 1)), v1 - v0, "pintura_naranja", fondo=v1 - v0 - 0.03,
                   mat_fondo="negro_mate", mat_hueco="pintura_naranja")
    b.poligono([origen + pl.u * x + pl.n * y for x, y in ext], "pintura_naranja", (0, 0, -1))
    # La carta, asomando por delante bajo la tapa.
    carta = rot("X", -12) @ rot("Z", 4)
    centro = pl.p(3.62, 3.5, d1 - 0.05)
    b.caja(centro, (0.42, 0.012, 0.26), "papel", giro=pl.giro @ carta)
    # Remaches del frente (malla alta) y una etiqueta con el nombre.
    for uu in (u0 + 0.05, u1 - 0.05):
        for vv in (v0 + 0.06, v1 - 0.08):
            cuerpo.alta.cupula(pl.p(uu, vv, d1), pl.n, 0.016, "acero", alto=0.01, lados=8)
    caja_plano(cuerpo.alta, pl, 3.52, 3.86, 3.12, 3.24, d1, d1 + 0.004, "papel")

    # Tapa: pivote en la bisagra de atrás.
    eje_v, eje_d = v1 + 0.015, d0 - 0.005
    tapa = Pieza("buzon_tapa", pivote=pl.p((u0 + u1) / 2, eje_v, eje_d), peso_uv=1.8)
    tb = tapa.baja
    caja_plano(tb, pl, u0 - 0.03, u1 + 0.03, eje_v - 0.005, eje_v + 0.03, eje_d, d1 + 0.045, "pintura_naranja")
    caja_plano(tb, pl, u0 - 0.03, u1 + 0.03, eje_v - 0.08, eje_v - 0.005, d1 + 0.02, d1 + 0.045, "pintura_naranja")
    tb.cilindro(pl.p(u0 + 0.05, eje_v, eje_d), pl.u, 0.018, u1 - u0 - 0.1, "metal_oscuro", lados=6)
    giro = Matrix.Translation(pl.p(0, eje_v, eje_d)) @ Matrix.Rotation(math.radians(-ANG_TAPA_BUZON), 4, pl.u) @ \
        Matrix.Translation(-pl.p(0, eje_v, eje_d))
    for c in (tb, tapa.alta):
        c.transformar(c.bm.verts, giro)

    # Banderita: brazo y chapa roja, levantada (hay correo). Pivote en su remache.
    piv = pl.p(u1 + 0.012, v0 + 0.2, d1 - 0.12)
    band = Pieza("buzon_bandera", pivote=piv, peso_uv=1.8)
    bb = band.baja
    caja_plano(bb, pl, u1 + 0.004, u1 + 0.02, v0 + 0.16, v0 + 0.62, d1 - 0.14, d1 - 0.1, "pintura_roja")
    caja_plano(bb, pl, u1 + 0.004, u1 + 0.02, v0 + 0.5, v0 + 0.63, d1 - 0.14, d1 + 0.06, "pintura_roja")
    bb.cilindro(piv - pl.u * 0.012, pl.u, 0.028, 0.03, "metal_oscuro", lados=8)
    return [cuerpo, tapa, band]


def lampara():
    """Aplique sobre la puerta: placa, brazo curvo, sombrerete, jaula, pantalla de cristal y bombilla (neón)."""
    pl = FRENTE
    xc = (PUERTA["x0"] + PUERTA["x1"]) / 2
    zp = 5.5
    cuerpo = Pieza("lampara", peso_uv=1.8)
    b = cuerpo.baja
    b.cilindro(pl.p(xc, zp, PANEL), pl.n, 0.16, 0.06, "metal_oscuro", lados=10, tapa_ini=False)
    cx, cy = xc, -MY - 0.7
    zt = 5.42
    brazo = [pl.p(xc, zp, PANEL + 0.04), (xc, -MY - 0.34, zp + 0.02), (xc, cy - 0.02, zp - 0.03), (cx, cy, zt + 0.02)]
    b.tubo(brazo, 0.03, "metal_oscuro", lados=6, radio_curva=0.12, pasos_curva=3, tapa_ini=False, tapa_fin=False)
    b.revolucion([(0.18, zt - 0.125), (0.23, zt - 0.135), (0.23, zt - 0.11), (0.04, zt + 0.015)], (cx, cy, 0), 12,
                 "metal_oscuro", tapa_ini=True, tapa_fin=True)
    zb = zt - 0.46
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        c = Vector((cx, cy, (zb + zt - 0.12) / 2)) + d * 0.185
        b.caja(c, (0.016, 0.016, zt - 0.12 - zb), "metal_oscuro", giro=rot("Z", 45 + 90 * k))
    anillo = [Vector((cx, cy, zb)) + Vector((math.cos(a), math.sin(a), 0)) * 0.185
              for a in [math.tau * i / 8 for i in range(9)]]
    b.tubo(anillo, 0.012, "metal_oscuro", lados=4, tapa_ini=False, tapa_fin=False)
    for uu in (-0.08, 0.08):
        tornillo(cuerpo, pl.p(xc + uu, zp, PANEL + 0.05), pl.n, 0.016, "acero", en_baja=False)

    pantalla = Pieza("lampara_pantalla_neon", peso_uv=0.5)
    pantalla.baja.revolucion([(0.15, zt - 0.125), (0.15, zb + 0.01), (0.165, zb + 0.01), (0.165, zt - 0.125)],
                             (cx, cy, 0), 12, "neon", tapa_ini=False, tapa_fin=False)
    bombilla = Pieza("lampara_bombilla_neon", peso_uv=0.5)
    bombilla.baja.revolucion([(0.0, zb - 0.08), (0.055, zb - 0.06), (0.085, zb + 0.01), (0.07, zb + 0.1),
                              (0.038, zb + 0.15), (0.038, zt - 0.125)], (cx, cy, 0), 8, "neon", tapa_fin=False)
    cuerpo.extra["luz"] = [cx, cy, zb + 0.02]
    return [cuerpo, pantalla, bombilla]


def medidor():
    """Contador de luz en el lateral derecho: caja con puerta (ventanilla) y pantalla digital de neón."""
    pl = DER
    u0, u1, v0, v1 = -1.68, -1.12, 2.62, 3.48
    d0, d1 = PANEL, 0.27
    caja = Pieza("medidor", peso_uv=1.6)
    b = caja.baja
    caja_plano(b, pl, u0, u1, v0, v1, d0, d1, "pintura_gris", sin=("+y",), mats={"-y": "negro_mate"})
    # Tubo que baja al zócalo.
    b.tubo([pl.p(-1.4, v0, 0.16), pl.p(-1.4, 1.53, 0.16)], 0.035, "metal_oscuro", lados=6, tapa_ini=False,
           tapa_fin=False)
    for vv in (2.15,):
        b.revolucion([(0.05, 0), (0.05, 0.05)], pl.p(-1.4, vv, 0.16), 6, "metal_oscuro")
    # Puerta: pivote en el canto izquierdo (u0).
    piv = pl.p(u0, v0, d1 + 0.012)
    puerta_m = Pieza("medidor_puerta", pivote=piv, peso_uv=1.8)
    pb = puerta_m.baja
    ext = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    hueco = [(-1.53, 3.16), (-1.27, 3.16), (-1.27, 3.32), (-1.53, 3.32)]
    pb.anillo_placa(ext, hueco, pl.p(0, 0, d1), pl.u, pl.v, pl.n, 0.024, "pintura_gris")
    pb.cara_con_huecos([pl.p(u, v, d1) for u, v in ext], [[pl.p(u, v, d1) for u, v in hueco]], "pintura_gris", -pl.n)
    caja_plano(pb, pl, u1 - 0.06, u1 - 0.02, 2.95, 3.12, d1 + 0.024, d1 + 0.05, "metal_oscuro", sin=("+y",))
    for vv in (v0 + 0.12, v1 - 0.12):
        pb.cilindro(pl.p(u0, vv - 0.06, d1 + 0.012), (0, 0, 1), 0.016, 0.12, "metal_oscuro", lados=6)
    # Pegatina de peligro: triángulo amarillo con un rayo (malla alta).
    tri = [(-1.4 - 0.1, 2.78), (-1.4 + 0.1, 2.78), (-1.4, 2.95)]
    puerta_m.alta.placa(tri, pl.p(0, 0, d1 + 0.024), pl.u, pl.v, pl.n, 0.002, "pegatina")
    rayo = [(-1.39, 2.93), (-1.43, 2.85), (-1.405, 2.85), (-1.42, 2.80), (-1.37, 2.875), (-1.395, 2.875)]
    puerta_m.alta.placa(rayo, pl.p(0, 0, d1 + 0.026), pl.u, pl.v, pl.n, 0.001, "negro_mate")
    # Pantalla.
    pant = Pieza("medidor_pantalla_neon", peso_uv=0.6)
    caja_plano(pant.baja, pl, -1.51, -1.29, 3.18, 3.3, d1 - 0.02, d1 + 0.004, "neon", sin=("+y",))
    caja.extra["salida_cable"] = list(pl.p(-1.4, v1, 0.16))
    return [caja, puerta_m, pant]


def cable(conexion):
    """Cable del medidor al panel solar, con dos ganchos aislantes."""
    p = Pieza("cable_electrico", peso_uv=1.0)
    b = p.baja
    pl = DER
    y0 = -1.4
    g1 = (4.5 + PANEL + 0.1, y0, 4.62)
    g2 = (4.5 + PANEL + 0.1, -1.12, 5.5)
    sobre = lambda x, y: (x, y, z_cresta(x) + 0.03)
    puntos = [(4.5 + 0.16, y0, 3.48), (4.5 + 0.13, y0, 3.9), g1, (4.67, -1.3, 5.0), g2, (5.0, -1.1, 5.58),
              (5.14, -1.1, 5.66), (5.12, -1.12, 5.83), sobre(4.75, -1.16), sobre(4.0, -1.25), sobre(3.4, -1.32),
              tuple(conexion)]
    b.tubo(puntos, 0.026, "goma", lados=5, radio_curva=0.1, pasos_curva=2)
    for g in (g1, g2):
        x, y, z = g
        b.caja_de((4.5 + PANEL, y - 0.05, z - 0.07), (4.5 + PANEL + 0.025, y + 0.05, z + 0.07), "metal_oscuro",
                  sin=("-x",))
        b.tubo([(4.5 + PANEL + 0.02, y, z - 0.03), (x + 0.04, y, z - 0.035), (x + 0.07, y, z + 0.03)], 0.012,
               "metal_oscuro", lados=4, radio_curva=0.03, pasos_curva=2)
        b.revolucion([(0.032, -0.03), (0.032, 0.03)], (x, y, z - 0.035), 6, "goma", eje=(1, 0, 0))
    return p


# ======================================================================================================
# Entorno
# ======================================================================================================


def felpudo():
    p = Pieza("felpudo", peso_uv=1.6)
    x0, x1, y0, y1 = 0.9, 2.4, -4.38, -3.74
    p.baja.caja_de((x0, y0, BASE_Z), (x1, y1, BASE_Z + 0.04), "fibra", sin=("-z",))
    # Ribete de goma (malla alta).
    a = p.alta
    m = 0.05
    for (xa, ya, xb, yb) in ((x0, y0, x1, y0 + m), (x0, y1 - m, x1, y1), (x0, y0 + m, x0 + m, y1 - m),
                             (x1 - m, y0 + m, x1, y1 - m)):
        a.caja_de((xa, ya, BASE_Z + 0.03), (xb, yb, BASE_Z + 0.043), "goma")
    p.extra["centro"] = [(x0 + x1) / 2, (y0 + y1) / 2, BASE_Z]
    return p


def maceta_grande():
    p = Pieza("maceta_grande", peso_uv=1.4)
    c = Vector((3.72, -4.02, BASE_Z))
    r2 = math.sqrt(2)
    perfil = [(0.33, 0.0), (0.33, 0.06), (0.3, 0.08), (0.335, 0.3), (0.322, 0.31), (0.326, 0.36), (0.345, 0.37),
              (0.37, 0.62), (0.405, 0.63), (0.405, 0.72), (0.325, 0.72), (0.325, 0.66)]
    p.baja.revolucion([(r * r2, z) for r, z in perfil], c, 4, "piedra_maceta", giro=math.pi / 4, suave=False,
                      tapa_ini=True, oculta_ini=True, tapa_fin=True, mat_fin="tierra")
    p.extra["tierra"] = [c.x, c.y, c.z + 0.66]
    return p


def arbusto(centro_tierra):
    """Arbusto: bultos de malla baja; las hojas sueltas se hornean desde la malla alta."""
    p = Pieza("arbusto", peso_uv=1.5)
    rnd = random.Random(17)
    import bmesh  # noqa: WPS433 (solo aquí)

    c = Vector(centro_tierra)
    bultos = [((0.0, 0.0, 0.32), 0.36), ((0.2, -0.12, 0.22), 0.26), ((-0.2, 0.08, 0.24), 0.27),
              ((0.05, 0.18, 0.5), 0.26), ((-0.1, -0.15, 0.55), 0.22)]
    for (dx, dy, dz), r in bultos:
        centro = c + Vector((dx, dy, dz))
        res = bmesh.ops.create_icosphere(p.baja.bm, subdivisions=2 if r > 0.3 else 1, radius=r)
        vs = res["verts"]
        for v in vs:
            dirv = v.co.normalized()
            n = noise.noise(dirv * 2.3 + Vector((dx, dy, dz)) * 7)
            v.co = centro + Vector((dirv.x, dirv.y, dirv.z * 0.85)) * r * (1 + 0.18 * n)
        caras = {f for v in vs for f in v.link_faces}
        for f in caras:
            f.material_index = p.baja.indice("hoja")
            f[p.baja.c_suave] = 1
        # Hojas sueltas sobre la superficie (malla alta).
        for _ in range(int(240 * r / 0.3)):
            dirv = Vector((rnd.gauss(0, 1), rnd.gauss(0, 1), abs(rnd.gauss(0, 1)) * 0.8 + 0.1)).normalized()
            pos = centro + Vector((dirv.x, dirv.y, dirv.z * 0.85)) * r * rnd.uniform(1.0, 1.12)
            if pos.z < c.z + 0.02:
                continue
            rumbo = math.atan2(dirv.y, dirv.x) + rnd.uniform(-0.8, 0.8)
            _hoja(p.alta, pos - Vector((math.cos(rumbo), math.sin(rumbo), 0)) * 0.05, rumbo,
                  rnd.uniform(0.09, 0.14), rnd.uniform(0.04, 0.06), rnd.uniform(0.0, 0.05), subida=0.03,
                  secciones=3)
    return p


def pico():
    """Pico de minero apoyado en la pared junto a la puerta: mango de madera y cabeza de hierro."""
    p = Pieza("pico", peso_uv=2.0)
    b, a = p.baja, p.alta
    pie = Vector((-0.08, -4.2, BASE_Z))
    T = Vector((-0.24, -MY - PANEL - 0.075, 3.12))  # centro de la cabeza, apoyada contra el panel
    eje = (T - pie).normalized()
    largo = (T - pie).length
    pts = [pie + eje * f * largo for f in (0.0, 0.03, 0.12, 0.45, 0.9, 1.0)] + [T + eje * 0.07]
    radios = [0.05, 0.056, 0.046, 0.05, 0.058, 0.06, 0.055]
    b.tubo(pts, 0.05, "madera_mango", lados=8, radios=radios)
    # Cinta del agarre (malla alta): espiral.
    hel = []
    u, _ = base_de(eje)
    w = eje.cross(u)
    for k in range(80):
        f = 0.08 + 0.2 * k / 79
        ang = k * 0.9
        hel.append(pie + eje * f * largo + (u * math.cos(ang) + w * math.sin(ang)) * 0.052)
    a.tubo(hel, 0.008, "cuero", lados=4, tapa_ini=False, tapa_fin=False)
    # Cabeza: punta a un lado y pala (azuela) al otro, curvadas hacia abajo.
    ladox = Vector((1, 0, 0))
    ladox = (ladox - eje * ladox.dot(eje)).normalized()
    prof = eje.cross(ladox).normalized()
    secciones = []
    for f in (-1.0, -0.8, -0.55, -0.3, -0.12, 0.0, 0.12, 0.3, 0.55, 0.8, 1.0):
        s = f * 0.62
        centro = T + ladox * s - eje * 0.17 * f * f
        tang = (ladox - eje * 0.34 * f).normalized()
        arriba = tang.cross(prof).normalized() * -1
        if f < 0:  # punta
            ah = 0.058 * (1 - abs(f)) ** 0.8 + 0.006
            ap = 0.048 * (1 - abs(f)) ** 0.8 + 0.005
        else:      # pala: se aplana y se ensancha
            ah = 0.058 * (1 - f) ** 1.2 + 0.006
            ap = 0.048 + 0.03 * f
        if abs(f) < 0.15:
            ah, ap = 0.075, 0.07  # ojo (donde entra el mango)
        anillo = [centro + arriba * ah, centro + prof * ap * 0.7 + arriba * ah * 0.4,
                  centro + prof * ap * 0.7 - arriba * ah * 0.6, centro - arriba * ah,
                  centro - prof * ap * 0.7 - arriba * ah * 0.6, centro - prof * ap * 0.7 + arriba * ah * 0.4]
        secciones.append(anillo)
    b.loft(secciones, "hierro", suave=True)
    b.recalcular(b.ultimas)
    # Cuña en el ojo (malla alta).
    a.caja(T + eje * 0.075, (0.02, 0.06, 0.01), "madera_mango", giro=eje.to_track_quat("Z", "Y").to_matrix())
    p.extra["agarre"] = [pie.z + 0.08 * largo * eje.z, pie.z + 0.3 * largo * eje.z]
    return p


def _bota(c, alta, origen, rumbo, tumbada=False):
    """Bota de trabajo tosca: suela gruesa, puntera, caña abierta con su hueco. Se construye en local y se coloca."""
    verts_ini = set(c.bm.verts)
    vini_alta = set(alta.bm.verts)
    # Suela (planta vista desde arriba), en local: x = hacia la puntera.
    planta = [(-0.2, 0.0), (-0.19, 0.065), (-0.14, 0.085), (-0.03, 0.08), (0.12, 0.1), (0.26, 0.095), (0.33, 0.05),
              (0.345, 0.0), (0.33, -0.05), (0.26, -0.092), (0.12, -0.095), (-0.03, -0.075), (-0.14, -0.08),
              (-0.19, -0.062)]
    c.placa(planta, Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.075, "goma_suela",
            atras=True)
    # Pie: lofts de secciones (media elipse sobre la suela).
    def seccion(x, ancho, alto, z0=0.07, n=8):
        pts = []
        for i in range(n + 1):
            a = math.pi * i / n
            pts.append(Vector((x, math.cos(a) * ancho, z0 + math.sin(a) * alto)))
        return pts
    secs = [seccion(0.335, 0.03, 0.05), seccion(0.31, 0.075, 0.1), seccion(0.22, 0.092, 0.13),
            seccion(0.1, 0.09, 0.18), seccion(-0.02, 0.085, 0.24), seccion(-0.17, 0.075, 0.2)]
    vs = c.loft(secs, "cuero", cerrado=False, tapa_ini=False, tapa_fin=False)
    tapas = [c.cara(list(reversed(vs[0])), "cuero"), c.cara(vs[-1], "cuero")]
    c.recalcular(c.ultimas + tapas)
    # Caña: tubo elíptico abierto arriba, con grosor y hueco oscuro.
    cx = -0.1
    perfil = [(1.0, 0.07), (1.0, 0.36), (1.06, 0.6), (0.86, 0.6), (0.82, 0.32)]
    anillos = []
    for k, (esc, z) in enumerate(perfil):
        anillos.append([Vector((cx + math.cos(a) * 0.105 * esc, math.sin(a) * 0.09 * esc, z))
                        for a in [math.tau * i / 10 for i in range(10)]])
    c.loft(anillos, "cuero", tapa_ini=False, tapa_fin=True, mats_tramo=["cuero", "cuero", "cuero", "negro_mate"],
           mat_fin="negro_mate")
    # Lengüeta y cordones (malla alta).
    for k in range(5):
        x = 0.05 - k * 0.045
        z = 0.2 + k * 0.07
        for s in (-1, 1):
            alta.cupula(Vector((x, s * 0.07, z)), Vector((0.2, s, 0.3)).normalized(), 0.012, "acero", alto=0.008,
                        lados=6)
        alta.tubo([Vector((x, -0.07, z + 0.01)), Vector((x + 0.02, 0, z + 0.03)), Vector((x, 0.07, z + 0.01))],
                  0.008, "goma", lados=4)
    # Tirador de atrás.
    c.caja(Vector((cx - 0.105, 0, 0.6)), (0.02, 0.05, 0.08), "cuero")
    nuevos = [v for v in c.bm.verts if v not in verts_ini]
    nuevos_alta = [v for v in alta.bm.verts if v not in vini_alta]
    M = Matrix.Translation(origen) @ Matrix.Rotation(math.radians(rumbo), 4, "Z")
    if tumbada:
        M = M @ Matrix.Translation((0, 0, 0.1)) @ Matrix.Rotation(math.radians(-88), 4, "X") @ \
            Matrix.Translation((0, 0, -0.1))
    c.transformar(nuevos, M)
    alta.transformar(nuevos_alta, M)
    # Apoyada en el suelo del porche.
    dz = BASE_Z - min(v.co.z for v in nuevos)
    c.transformar(nuevos, Matrix.Translation((0, 0, dz)))
    alta.transformar(nuevos_alta, Matrix.Translation((0, 0, dz)))


def botas():
    p = Pieza("botas", peso_uv=1.8)
    _bota(p.baja, p.alta, Vector((0.32, -4.12, BASE_Z)), -100)
    _bota(p.baja, p.alta, Vector((0.62, -4.38, BASE_Z)), -25, tumbada=True)
    return p


# ======================================================================================================
# Todo junto
# ======================================================================================================


def construir():
    """Crea todas las piezas. Devuelve (piezas, P) donde P son los puntos que usan los materiales."""
    piezas = [base(), escalon(), zocalo(), paredes(), techo()]
    solar = panel_solar()
    piezas += [solar, chimenea(), canalon()]
    baj = bajante()
    piezas.append(baj)
    pu = puerta()
    piezas += [pu, puerta_marco()]
    piezas += ventana_frontal()
    piezas += ventana_lateral()
    piezas.append(placa_numero())
    piezas += buzon()
    piezas += lampara()
    med = medidor()
    piezas += med
    piezas.append(cable(solar.extra["conexion"]))
    fel = felpudo()
    mg = maceta_grande()
    pi = pico()
    piezas += [fel, mg, arbusto(mg.extra["tierra"]), pi, botas()]
    esc = [p for p in piezas if p.nombre == "escalon"][0]
    P = {
        "manija": tuple(MANIJA),
        "manija_agarre": tuple(pu.extra["manija_agarre"]),
        "zocalo_z": ZOC_Z,
        "puerta_z0": HOJA["z0"],
        "puerta_suelo": ((PUERTA["x0"] + PUERTA["x1"]) / 2, -4.1, BASE_Z),
        "escalon_centro": tuple(esc.extra["centro"]),
        "felpudo_centro": tuple(fel.extra["centro"]),
        "bajante_pie": tuple(baj.extra["pie"]),
        "chimenea_boca": 7.8,
        "pico_agarre": tuple(pi.extra["agarre"]),
    }
    return piezas, P
