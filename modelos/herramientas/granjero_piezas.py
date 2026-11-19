"""
Piezas de la casa del granjero. Todo en STUDS, con la fachada mirando a -Y (el «delante» de Roblox).

Planta (vista desde arriba, delante abajo):

      x = -12 ............ -6   -5 ............... +5   +6
          [   INVERNADERO   ]=P=[       CASA        ]  (tanque detrás, a la derecha)
          [  8 x 6 x 5      ] A [   10 x 8 x 7      ]
      compostero, sacos     S   enredadera en la esquina delantera derecha
          mesa de trabajo delante del invernadero      escalón, gato, camino de piedras hasta la calle

  * Casa: muros de 10 × 8 (cara exterior del alma en x = ±5, y = ±4) sobre una base de medio stud y un zócalo de
    piedra de un stud. Tejado a dos aguas de chapa con la cumbrera a lo largo de Y (hastial en la fachada).
  * Fachada (-Y): ventana con alféizar y tres macetas de hierbas, gancho con el delantal, puerta de madera con
    lámpara cian encima, cartel tallado «Productos frescos», enredadera en la esquina, botas de agua y el gato.
  * Lateral derecho (+X): medidores de luz y de agua, grifo con la manguera enrollada en su soporte, ventana con
    rejilla debajo, canalón grande que baja al tanque de agua de lluvia (con grifo y manguera corta).
  * Lateral izquierdo (-X): puerta lateral metálica -> pasillo cubierto de 1 stud -> puerta del invernadero.
  * Invernadero: armazón de tubo cuadrado de aluminio con escuadras atornilladas, paños de cristal con
    condensación (alfa en el atlas), dos ventilas en el faldón izquierdo (una abierta con su brazo), estanterías de
    tres niveles con bandejas, lechugas y albahaca, bancal de tomateras, riego por goteo y lámpara UV morada.

Cada función crea una `Pieza` (malla baja del juego + detalles de la malla alta para hornear).
Reutiliza el constructor y las piezas genéricas de las otras casas (casa_malla, casa_piezas, comerciante_piezas).
"""

import math
import random

from mathutils import Matrix, Vector, noise

import casa_piezas as cp
import comerciante_piezas as cc
from casa_malla import Pieza, base_de, rot
from casa_piezas import caja_plano, tornillo

# ======================================================================================================
# Medidas (studs)
# ======================================================================================================

BASE_Z = 0.5          # la casa se eleva medio stud
ZOC_Z = 1.5           # zócalo de piedra hasta aquí
MX, MY = 5.0, 4.0     # cara exterior del alma de los muros
MURO = 0.3
PANEL = 0.06
JUNTA = 0.03
CUMBRE = 7.0          # crestas de la chapa en la cumbrera
PEND = 0.28           # pendiente del tejado (unos 15,6°)
ALERO_X = 5.55
VUELO_Y = 4.5
ONDA = 0.09
CHAPA = 0.03

BASE = dict(x0=-5.4, x1=5.4, y0=-5.0, y1=4.4)
PUERTA = dict(x0=0.3, x1=2.6, z0=0.5, z1=4.85)
HOJA = dict(x0=0.45, x1=2.45, z0=0.62, z1=4.71, y0=-MY - 0.02, y1=-MY + 0.16)
EJE_PUERTA = Vector((0.4, -MY - 0.1, 0.0))
BISAGRAS_Z = (1.25, 4.15)
MANIJA = Vector((2.23, -MY - 0.02, 2.82))
VENTANA = dict(x0=-3.9, x1=-1.3, z0=2.3, z1=4.4)
VLAT = dict(u0=-0.5, u1=1.1, v0=2.9, v1=4.3)            # muro derecho (u = +y)
REJILLA = dict(u0=-0.1, u1=0.7, v0=1.75, v1=2.4)
PUERTA_L = dict(u0=-0.75, u1=0.75, v0=0.5, v1=3.6)      # muro izquierdo (u = -y)

# Invernadero
GX0, GX1 = -12.0, -6.0      # caras exteriores del armazón (x)
GY0, GY1 = -4.0, 4.0
GZ0 = 0.5                   # pie del armazón (sobre el murete)
GE = 3.7                    # alero
GR = 5.0                    # cumbrera
GXC = (GX0 + GX1) / 2       # x de la cumbrera
S = 0.08                    # sección del tubo cuadrado
VID = 0.03                  # grosor del cristal
YP = [-4.0, -2.4, -0.8, 0.8, 2.4, 4.0]     # pórticos (montantes laterales y cabios)
XG = [-12.0, -10.5, -9.0, -7.5, -6.0]      # montantes de los hastiales
Z_MED = 1.9                                 # travesaño intermedio
PUERTA_I = dict(y0=-0.72, y1=0.72, z0=0.58, z1=2.92)
VENTILAS = {"cerrada": (-2.4, -0.8), "abierta": (0.8, 2.4)}
ANG_VENTILA = 32.0

# Tanque de agua de lluvia (detrás a la derecha)
TANQUE = Vector((6.05, 2.85, 0.2))   # centro de la base
TANQUE_R, TANQUE_H = 0.5, 1.5

rnd_global = random.Random(1)


def z_cresta(x):
    return CUMBRE - PEND * abs(x)


def z_muro(x):
    return z_cresta(x) - ONDA - CHAPA - 0.005


Z_LAT = z_muro(MX)

FRENTE = cp.Plano((0, -MY, 0), (0, -1, 0))   # u = +x
FONDO = cp.Plano((0, MY, 0), (0, 1, 0))      # u = -x
IZQ = cp.Plano((-MX, 0, 0), (-1, 0, 0))      # u = -y
DER = cp.Plano((MX, 0, 0), (1, 0, 0))        # u = +y


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def z_invernadero(x):
    """Altura de la línea del tejado del invernadero (línea de los cabios)."""
    return GE + (GR - GE) * (1 - abs(x - GXC) / (GXC - GX0))


# ======================================================================================================
# Utilidades
# ======================================================================================================


def barra(c, a, b, ancho, alto, mat, arriba=(0, 0, 1), sin=()):
    """Caja de sección ancho × alto entre los puntos a y b (perfiles, cabios, listones...)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    z = d.normalized()
    up = Vector(arriba)
    if abs(up.normalized().dot(z)) > 0.98:
        up = Vector((1, 0, 0)) if abs(z.x) < 0.9 else Vector((0, 1, 0))
    x = up.cross(z).normalized()
    y = z.cross(x).normalized()
    giro = Matrix((x, y, z)).transposed()
    return c.caja((a + b) / 2, (ancho, alto, d.length), mat, giro=giro, sin=sin)


def hoja3d(c, origen, rumbo, largo, ancho, caida, mat, subida=0.1, secciones=4, alabeo=0.0, corazon=False):
    """Hoja con volumen (sección en V y grosor), curvada hacia abajo. `corazon`: base ancha (enredadera)."""
    dirv = Vector((math.cos(rumbo), math.sin(rumbo), 0))
    lado = Vector((-dirv.y, dirv.x, 0))
    anillos = []
    for k in range(secciones + 1):
        f = k / secciones
        centro = origen + dirv * largo * f + Vector((0, 0, subida * math.sin(math.pi * f * 0.8) - caida * f * f))
        if corazon:
            w = ancho / 2 * (math.sin(math.pi * min(1.0, 0.25 + f * 0.8)) ** 0.6) * (1.0 if f > 0 else 0.6)
        else:
            w = ancho / 2 * math.sin(math.pi * min(1.0, f * 1.05)) ** 0.7
        w = max(0.004, w)
        tor = alabeo * f
        l2 = lado * math.cos(tor) + Vector((0, 0, math.sin(tor)))
        grosor = 0.006
        anillos.append([centro - l2 * w, centro + Vector((0, 0, 0.14 * w)), centro + l2 * w,
                        centro + Vector((0, 0, 0.14 * w - grosor))])
    c.loft(anillos, mat, tapa_ini=True, tapa_fin=True, suave=True)
    c.recalcular(c.ultimas)


def bulto(c, centro, radio, alto, mat, lados=7, semilla=0, aplastar=1.0, base_r=0.55, rugoso=0.18):
    """Mata redondeada (lechuga, albahaca) de pocos triángulos: el detalle de las hojas va en la alta."""
    perfil = [(radio * base_r, 0.0), (radio, alto * 0.42), (radio * 0.78, alto * 0.82), (0.0, alto)]
    vs = c.revolucion(perfil, centro, lados, mat, tapa_ini=False, giro=semilla * 0.7)
    for anillo in vs[1:3]:
        for v in anillo:
            d = v.co - Vector(centro)
            n = noise.noise(v.co * 6.0 + Vector((semilla, semilla * 0.3, 0)))
            v.co = Vector(centro) + Vector((d.x * (1 + rugoso * n), d.y * (1 + rugoso * n), d.z * aplastar))


def esfera(c, centro, r, mat, lados=6, aplastar=1.0):
    """Bola barata (tomate, cabeza): punta abajo, dos anillos y punta arriba."""
    perfil = [(0.0, -r * aplastar), (r * 0.92, -r * 0.35 * aplastar), (r * 0.9, r * 0.4 * aplastar),
              (0.0, r * 0.9 * aplastar)]
    return c.revolucion(perfil, centro, lados, mat)


# ======================================================================================================
# Casa: estructura
# ======================================================================================================


def base():
    p = Pieza("casa_base", peso_uv=0.7)
    b = p.baja
    b.caja_de((BASE["x0"], BASE["y0"], 0), (BASE["x1"], BASE["y1"], BASE_Z), "hormigon", sin=("-z",))
    # Losa del tanque (algo más baja: el tanque se apoya en el suelo, junto a la casa).
    b.caja_de((5.42, 2.2, 0), (6.7, 3.5, 0.2), "hormigon", sin=("-z", "-x"))
    return p


def escalon():
    return cc._losa_gastada("escalon", 0.15, 2.75, -5.75, -5.0, 0.27, 0.03, (1.45, -5.4), peso=1.6)


def zocalo():
    """Zócalo de piedra: dos hiladas irregulares con mortero detrás y vierteaguas de chapa encima."""
    p = Pieza("casa_zocalo", peso_uv=0.95)
    rnd = random.Random(31)
    tramos = [(FRENTE, -MX - 0.13, PUERTA["x0"] - 0.05), (FRENTE, PUERTA["x1"] + 0.05, MX + 0.13),
              (FONDO, -MX - 0.13, MX + 0.13), (IZQ, -MY, PUERTA_L["u0"] - 0.08), (IZQ, PUERTA_L["u1"] + 0.08, MY),
              (DER, -MY, MY)]
    for pl, u0, u1 in tramos:
        caja_plano(p.baja, pl, u0, u1, BASE_Z, 1.46, 0.0, 0.075, "mortero", sin=("+y", "-z", "+z"),
                   ocultas=("-y",))
        hiladas = [(BASE_Z, 1.45)] if pl is FONDO else [(BASE_Z, 0.95 + rnd.uniform(-0.05, 0.05)), (None, 1.45)]
        for k, (v0, v1) in enumerate(hiladas):
            u = u0 - (rnd.uniform(0.25, 0.45) if k == 1 else 0.0)
            while u < u1 - 0.05:
                largo = rnd.uniform(1.0, 1.55)
                if u1 - (u + largo) < 0.3:
                    largo = u1 - u
                a, bb = max(u, u0), min(u + largo, u1)
                vv0 = v0 if v0 is not None else 0.97 + rnd.uniform(-0.04, 0.04)
                if bb - a > 0.1:
                    giro = rot("Y", rnd.uniform(-1.6, 1.6)) @ rot("X", rnd.uniform(-1.0, 1.0)) @ \
                        rot("Z", rnd.uniform(-1.0, 1.0))
                    sin = ("+y", "-z", "+z") if len(hiladas) == 1 else (("+y", "-z") if k == 0 else ("+y", "+z"))
                    caja_plano(p.baja, pl, a + rnd.uniform(0.012, 0.025), bb - rnd.uniform(0.012, 0.025),
                               vv0 + (rnd.uniform(0.01, 0.03) if k else 0), v1 - rnd.uniform(0.0, 0.012), 0.05,
                               rnd.uniform(0.1, 0.15), "piedra", sin=sin, giro_extra=giro)
                u += largo
        perfil = [(0.035, 1.53), (0.185, 1.468), (0.185, 1.435), (0.17, 1.435), (0.17, 1.455), (0.035, 1.508)]
        ext = 0.12 if pl in (FRENTE, FONDO) else 0.0
        a, bb = u0 - (ext if u0 < -MX else 0), u1 + (ext if u1 > MX else 0)
        p.baja.placa(perfil, pl.p(a, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, bb - a, "metal_oscuro", atras=True)
    return p


def _panel(p, pl, u0, u1, v0, v1, rnd, recortes=(), remaches=0.33, mat="panel_granjero"):
    g = JUNTA / 2
    poly = rect(u0 + g, u1 - g, v0 + g, v1 - g)
    for a_, b_, c_ in recortes:
        poly = cp.recortar(poly, a_, b_, c_)
    if len(poly) < 3 or cp.area(poly) < 0.02:
        return
    grosor = PANEL + rnd.uniform(-0.004, 0.003)
    p.baja.placa(poly, pl.p(0, 0, 0), pl.u, pl.v, pl.n, grosor, mat)
    us = [q[0] for q in poly]
    vs = [q[1] for q in poly]
    ua, ub, va, vb = min(us) + 0.06, max(us) - 0.06, min(vs) + 0.06, max(vs) - 0.06
    nu = max(1, int((ub - ua) / remaches))
    nv = max(1, int((vb - va) / remaches))
    for t in range(nu + 1):
        uu = ua + (ub - ua) * t / nu
        for vv in (va, vb):
            if cp._dentro(poly, uu, vv):
                p.alta.cupula(pl.p(uu, vv, grosor), pl.n, 0.021, "acero", alto=0.011, lados=8)
    for t in range(1, nv):
        vv = va + (vb - va) * t / nv
        for uu in (ua, ub):
            if cp._dentro(poly, uu, vv):
                p.alta.cupula(pl.p(uu, vv, grosor), pl.n, 0.021, "acero", alto=0.011, lados=8)


def paredes():
    """Alma de los muros con los huecos, paneles metálicos con remaches y cantoneras."""
    p = Pieza("casa_paredes", peso_uv=1.0)
    rnd = random.Random(9)
    b = p.baja
    zm0 = z_muro(0)

    def alma(pl, ext, inte, huecos):
        b.cara_con_huecos([pl.p(u, v, 0) for u, v in ext], [[pl.p(u, v, 0) for u, v in h] for h in huecos],
                          "junta", pl.n, oculta=2)
        b.cara_con_huecos([pl.p(u, v, -MURO) for u, v in inte], [[pl.p(u, v, -MURO) for u, v in h] for h in huecos],
                          "interior", -pl.n, oculta=1)

    P_, V = PUERTA, VENTANA
    frente_ext = [(-MX, 1.45), (P_["x0"], 1.45), (P_["x0"], P_["z1"]), (P_["x1"], P_["z1"]), (P_["x1"], 1.45),
                  (MX, 1.45), (MX, z_muro(MX)), (0, zm0), (-MX, z_muro(MX))]
    frente_int = [(-MX + MURO, BASE_Z), (P_["x0"], BASE_Z), (P_["x0"], P_["z1"]), (P_["x1"], P_["z1"]),
                  (P_["x1"], BASE_Z), (MX - MURO, BASE_Z), (MX - MURO, z_muro(MX - MURO)), (0, zm0),
                  (-MX + MURO, z_muro(MX - MURO))]
    alma(FRENTE, frente_ext, frente_int, [rect(V["x0"], V["x1"], V["z0"], V["z1"])])
    fondo_ext = [(-MX, 1.45), (MX, 1.45), (MX, z_muro(MX)), (0, zm0), (-MX, z_muro(MX))]
    fondo_int = [(-MX + MURO, BASE_Z), (MX - MURO, BASE_Z), (MX - MURO, z_muro(MX - MURO)), (0, zm0),
                 (-MX + MURO, z_muro(MX - MURO))]
    alma(FONDO, fondo_ext, fondo_int, [])
    L = PUERTA_L
    izq_ext = [(-MY, 1.45), (L["u0"], 1.45), (L["u0"], L["v1"]), (L["u1"], L["v1"]), (L["u1"], 1.45), (MY, 1.45),
               (MY, Z_LAT), (-MY, Z_LAT)]
    izq_int = [(-MY + MURO, BASE_Z), (L["u0"], BASE_Z), (L["u0"], L["v1"]), (L["u1"], L["v1"]), (L["u1"], BASE_Z),
               (MY - MURO, BASE_Z), (MY - MURO, Z_LAT), (-MY + MURO, Z_LAT)]
    alma(IZQ, izq_ext, izq_int, [])
    VL = VLAT
    alma(DER, rect(-MY, MY, 1.45, Z_LAT), rect(-MY + MURO, MY - MURO, BASE_Z, Z_LAT),
         [rect(VL["u0"], VL["u1"], VL["v0"], VL["v1"])])

    # ---- paneles ---------------------------------------------------------------------------------------------
    gable = [(PEND, 1, zm0), (-PEND, 1, zm0)]
    cols_f = [(-MX, -3.9), (-3.9, -2.6), (-2.6, -1.3), (-1.3, 0.3), (0.3, 1.45), (1.45, 2.6), (2.6, 3.8), (3.8, MX)]
    for i, (u0, u1) in enumerate(cols_f):
        if 1 <= i <= 2:
            filas = [(1.5, V["z0"]), (V["z1"], 5.6), (5.6, 7.1)]
        elif 4 <= i <= 5:
            filas = [(P_["z1"], 5.6), (5.6, 7.1)]
        else:
            filas = [(1.5, 3.4), (3.4, 5.6), (5.6, 7.1)]
        for v0, v1 in filas:
            _panel(p, FRENTE, u0, u1, v0, v1, rnd, recortes=gable)
    for c in cc._celdas([-MX, -2.5, 0.0, 2.5, MX], [1.5, 3.5, 5.6, 7.1]):
        _panel(p, FONDO, *c, rnd, recortes=gable)
    for c in cc._celdas([-MY, -2.7, -1.4, L["u0"], L["u1"], 1.4, 2.7, MY], [1.5, L["v1"], Z_LAT],
                        [(L["u0"], L["u1"], 0.0, L["v1"])]):
        _panel(p, IZQ, *c, rnd)
    for c in cc._celdas([-MY, -2.6, -1.3, VL["u0"], VL["u1"], 2.5, MY], [1.5, VL["v0"], VL["v1"], Z_LAT],
                        [(VL["u0"], VL["u1"], VL["v0"], VL["v1"])]):
        _panel(p, DER, *c, rnd)

    # ---- respiradero redondo en el hastial de delante y de detrás ----------------------------------------------
    for pl, uc in ((FRENTE, -0.9),):
        vc = 6.1
        c0 = pl.p(uc, vc, PANEL)
        b.revolucion([(0.32, 0), (0.32, 0.04), (0.27, 0.06), (0.24, 0.06), (0.24, -0.04)], c0, 10, "metal_oscuro",
                     eje=pl.n, tapa_ini=False, tapa_fin=False)
        b.revolucion([(0.24, -0.04), (0.0, -0.04)], c0, 10, "negro_mate", eje=pl.n, tapa_ini=False, tapa_fin=False)
        for k in range(-2, 3):
            vv = k * 0.09
            w = math.sqrt(max(0.0, 0.24 ** 2 - vv ** 2)) - 0.01
            caja_plano(b, pl, uc - w, uc + w, vc + vv - 0.02, vc + vv + 0.02, PANEL - 0.03, PANEL + 0.02,
                       "metal_oscuro", sin=("+y",), giro_extra=rot("X", 35))
        for k in range(8):
            ang = math.tau * k / 8
            tornillo(p, pl.p(uc + math.cos(ang) * 0.29, vc + math.sin(ang) * 0.29, PANEL + 0.04), pl.n, 0.015,
                     "acero", en_baja=False)

    # ---- cantoneras ---------------------------------------------------------------------------------------------
    for sx in (-1, 1):
        for sy in (-1, 1):
            z0, z1 = 1.47, Z_LAT + 0.02
            xa = sorted((sx * (MX - 0.15), sx * (MX + PANEL + 0.035)))
            ya = sorted((sy * (MY + PANEL), sy * (MY + PANEL + 0.03)))
            b.caja_de((xa[0], ya[0], z0), (xa[1], ya[1], z1), "metal_oscuro", sin=("+y" if sy < 0 else "-y",))
            xb = sorted((sx * (MX + PANEL), sx * (MX + PANEL + 0.03)))
            yb = sorted((sy * (MY - 0.15), sy * (MY + PANEL + 0.035)))
            b.caja_de((xb[0], yb[0], z0), (xb[1], yb[1], z1), "metal_oscuro", sin=("+x" if sx < 0 else "-x",))
            for k in range(7):
                zz = z0 + 0.25 + k * (z1 - z0 - 0.5) / 6
                tornillo(p, (sx * (MX - 0.07), sy * (MY + PANEL + 0.03), zz), (0, sy, 0), 0.021, "acero",
                         en_baja=False)
                tornillo(p, (sx * (MX + PANEL + 0.03), sy * (MY - 0.07), zz), (sx, 0, 0), 0.021, "acero",
                         en_baja=False)
    return p


def techo():
    """Chapa grecada a dos aguas (dos chapas por faldón que se solapan), cumbrera y remates."""
    p = Pieza("casa_techo", peso_uv=0.85)
    b = p.baja
    phi = math.atan(PEND)
    for s, y0, y1, mat in ((-1, -VUELO_Y, 0.4, "chapa_techo"), (-1, -0.1, VUELO_Y, "chapa_techo"),
                           (1, -VUELO_Y, 0.4, "chapa_nueva"), (1, -0.1, VUELO_Y, "chapa_techo")):
        elev = CHAPA + 0.002 if y0 > -1 else 0.0
        perfil = cp._perfil_nervios(y0, y1)
        anillos = []
        for x in (0.0, s * ALERO_X):
            zb = z_cresta(x) - ONDA + elev
            arriba = [Vector((x, y, zb + hh)) for y, hh in perfil]
            abajo = [Vector((x, y, zb + hh - CHAPA)) for y, hh in reversed(perfil)]
            anillos.append(arriba + abajo)
        b.loft(anillos, mat, tapa_ini=False, tapa_fin=True, suave=False)
        b.recalcular(b.ultimas)
        for k in range(-8, 12):
            yc = cp.Y_REF + k * cp.PASO + 0.55
            if y0 + 0.1 < yc < y1 - 0.1:
                for xc in (0.45, 2.0, 3.6, 5.3):
                    x = s * xc
                    z = z_cresta(x) + elev
                    nrm = Vector((s * math.sin(phi), 0, math.cos(phi)))
                    p.alta.cupula((x, yc, z - 0.002), nrm, 0.04, "goma", alto=0.008, lados=10)
                    p.alta.cupula((x, yc, z + 0.004), nrm, 0.024, "acero", alto=0.018, lados=6)
    for s in (-1, 1):
        g = rot("Y", s * math.degrees(phi))
        cx = s * 0.25 * math.cos(phi)
        cz = CUMBRE + 0.004 + CHAPA + 0.015 - PEND * abs(cx)
        b.caja((cx, 0, cz), (0.5, 2 * VUELO_Y + 0.08, 0.024), "metal_oscuro", giro=g)
    for s in (-1, 1):
        g = rot("Y", s * math.degrees(phi))
        largo = ALERO_X / math.cos(phi)
        cx = s * ALERO_X / 2
        for sy in (-1, 1):
            zc = z_cresta(cx) + CHAPA * 0.5
            b.caja((cx, sy * (VUELO_Y + 0.013), zc - 0.07), (largo + 0.02, 0.026, 0.26), "metal_oscuro", giro=g)
            b.caja((cx, sy * (VUELO_Y - 0.055), zc + 0.065), (largo + 0.02, 0.16, 0.022), "metal_oscuro", giro=g)
    return p


def panel_solar():
    p = Pieza("casa_panel_solar", peso_uv=1.3)
    b, a = p.baja, p.alta
    phi = math.atan(PEND)
    M = rot("Y", math.degrees(phi))
    xc, yc = 2.75, -2.1
    O = Vector((xc, yc, z_cresta(xc)))
    A, B = 1.8, 2.6

    def caja(ca, cb, ccz, ta, tb, tc, mat, **kw):
        return b.caja(O + M @ Vector((ca, cb, ccz)), (ta, tb, tc), mat, giro=M, **kw)

    for ca in (-0.55, 0.55):
        for cb in (-1.05, 1.05):
            caja(ca, cb, 0.03, 0.12, 0.12, 0.06, "aluminio", sin=("-z",))
        caja(ca, 0, 0.09, 0.08, B + 0.1, 0.06, "aluminio")
    caja(0, 0, 0.145, A - 0.1, B - 0.1, 0.05, "pintura_gris", sin=("-x", "+x", "-y", "+y"))
    w = 0.07
    caja(-A / 2 + w / 2, 0, 0.155, w, B, 0.09, "aluminio")
    caja(A / 2 - w / 2, 0, 0.155, w, B, 0.09, "aluminio")
    caja(0, -B / 2 + w / 2, 0.155, A - 2 * w, w, 0.09, "aluminio", sin=("-x", "+x"))
    caja(0, B / 2 - w / 2, 0.155, A - 2 * w, w, 0.09, "aluminio", sin=("-x", "+x"))
    ia, ib, gap = A - 2 * w, B - 2 * w, 0.03
    na, nb = 3, 4
    ca_ = (ia - (na + 1) * gap) / na
    cb_ = (ib - (nb + 1) * gap) / nb
    for i in range(na):
        for j in range(nb):
            pa = -ia / 2 + gap + ca_ / 2 + i * (ca_ + gap)
            pb = -ib / 2 + gap + cb_ / 2 + j * (cb_ + gap)
            caja(pa, pb, 0.177, ca_, cb_, 0.014, "celda_solar", sin=("-z",))
            for t in (-0.25, 0.25):
                a.caja(O + M @ Vector((pa, pb + t * cb_, 0.1845)), (ca_ * 0.96, 0.012, 0.002), "aluminio", giro=M)
            for t in range(6):
                a.caja(O + M @ Vector((pa - ca_ * 0.45 + t * ca_ * 0.18, pb, 0.1843)), (0.004, cb_ * 0.96, 0.0015),
                       "aluminio", giro=M)
    caja(0.62, -0.95, 0.09, 0.22, 0.26, 0.07, "negro_mate")
    for ca in (-A / 2 + 0.035, A / 2 - 0.035):
        for cb in (-1.1, -0.4, 0.4, 1.1):
            a.cupula(O + M @ Vector((ca, cb, 0.2)), M @ Vector((0, 0, 1)), 0.014, "acero", alto=0.008, lados=8)
    p.extra["conexion"] = list(O + M @ Vector((0.62, -1.08, 0.09)))
    return p


def canalon():
    """Canalón extra grande en el alero derecho: recoge toda el agua del faldón para el tanque."""
    p = Pieza("canalon_grande", peso_uv=1.0)
    b, a = p.baja, p.alta
    ext = [(5.4, 5.33), (5.41, 5.1), (5.47, 4.99), (5.62, 4.94), (5.86, 4.95), (5.98, 5.03), (6.04, 5.18),
           (6.05, 5.35), (6.0, 5.37)]
    t = 0.022
    inte = [(5.42, 5.33), (5.432, 5.11), (5.485, 5.015), (5.625, 4.968), (5.85, 4.975), (5.96, 5.045),
            (6.017, 5.185), (6.027, 5.345), (6.005, 5.35)]
    perfil = ext + list(reversed(inte))
    y0, y1 = -VUELO_Y - 0.05, VUELO_Y + 0.05
    anillos = [[Vector((x, y, z)) for x, z in perfil] for y in (y0, y1)]
    b.loft(anillos, "metal_oscuro", tapa_ini=False, tapa_fin=False, suave=False)
    b.recalcular(b.ultimas)
    for y, n in ((y0, -1), (y1, 1)):
        b.placa(ext, Vector((0, y, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, n, 0)), t, "metal_oscuro",
                atras=True)
    # Abrazaderas de pletina, atornilladas al canto del alero.
    for y in (-3.3, 0.0, 3.3):
        camino = [Vector((5.38, y, 5.36)), Vector((5.39, y, 5.08)), Vector((5.47, y, 4.965)), Vector((5.62, y, 4.92)),
                  Vector((5.87, y, 4.93)), Vector((6.0, y, 5.02)), Vector((6.07, y, 5.18)), Vector((6.07, y, 5.38))]
        b.tubo(camino, 0.016, "metal_oscuro", lados=4)
        a.cupula((5.38, y, 5.37), (0, 0, 1), 0.02, "acero", alto=0.01)
    # Boca de salida hacia el tanque, con el manguito.
    yb = TANQUE.y
    b.revolucion([(0.12, 4.97), (0.1, 4.86), (0.1, 4.78)], (5.72, yb, 0), 8, "metal_oscuro", tapa_ini=False,
                 tapa_fin=False)
    # Hojas secas y verdín en el fondo (malla alta): se ven desde arriba.
    rnd = random.Random(4)
    for _ in range(14):
        y = rnd.uniform(y0 + 0.3, y1 - 0.3)
        hoja3d(a, Vector((rnd.uniform(5.6, 5.85), y, 4.99)), rnd.uniform(0, math.tau), rnd.uniform(0.1, 0.16),
               0.06, 0.0, "hoja_enredadera", subida=0.01, secciones=3)
    p.extra["boca"] = [5.72, yb, 4.78]
    return p


def tanque():
    """Tanque de agua de lluvia: cilindro de plástico con nervios, tapa con filtro, nivel, grifo y manguera corta."""
    c0 = TANQUE
    r, h = TANQUE_R, TANQUE_H
    p = Pieza("tanque_agua", peso_uv=1.2)
    b, a = p.baja, p.alta
    perfil = [(r - 0.03, 0.0), (r, 0.04), (r, 0.33), (r + 0.025, 0.36), (r, 0.4), (r, 1.08), (r + 0.025, 1.11),
              (r, 1.15), (r, h - 0.05), (r - 0.06, h), (0.42, h)]
    b.revolucion(perfil, c0, 12, "plastico_tanque", tapa_ini=True, oculta_ini=True, tapa_fin=False)
    # Tapa a rosca con asas, y el filtro de hojas donde entra el bajante.
    zt = c0.z + h
    b.revolucion([(0.42, -0.005), (0.43, 0.05), (0.36, 0.08), (0.17, 0.08)], c0 + Vector((0, 0, h)), 12,
                 "plastico_tanque", tapa_ini=False, tapa_fin=False)
    b.revolucion([(0.17, 0.08), (0.17, 0.2), (0.15, 0.2), (0.12, 0.06), (0.0, 0.06)],
                 c0 + Vector((0, 0, h)), 8, "plastico_negro", tapa_ini=False, tapa_fin=False)
    for k in range(2):
        ang = math.tau * k / 2 + math.pi / 4
        d = Vector((math.cos(ang), math.sin(ang), 0))
        b.caja(c0 + Vector((0, 0, h + 0.09)) + d * 0.29, (0.16, 0.035, 0.03), "plastico_tanque",
               giro=rot("Z", math.degrees(ang) + 90))
    # Rejilla del filtro (malla alta).
    for k in range(-3, 4):
        a.caja(c0 + Vector((k * 0.035, 0, h + 0.065)), (0.008, 0.24, 0.004), "acero")
    # Tubo de nivel transparente con su escala (se ve el agua por dentro).
    yn = c0.y - r - 0.03
    b.cilindro((c0.x + 0.18, yn + 0.01, c0.z + 0.16), (0, 0, 1), 0.018, 1.2, "vidrio", lados=5)
    for k in range(7):
        a.caja((c0.x + 0.24, yn + 0.03, c0.z + 0.25 + k * 0.16), (0.04, 0.004, 0.008), "negro_mate")
    # Grifo de latón abajo, mirando hacia delante.
    gz = c0.z + 0.2
    gy = c0.y - r
    b.cilindro((c0.x, gy + 0.03, gz), (0, -1, 0), 0.05, 0.05, "plastico_negro", lados=8)
    b.cilindro((c0.x, gy - 0.02, gz), (0, -1, 0), 0.03, 0.11, "laton", lados=6)
    b.revolucion([(0.034, 0.0), (0.034, 0.06), (0.026, 0.12)], (c0.x, gy - 0.12, gz), 6, "laton",
                 eje=(0, 0, -1), tapa_ini=True, tapa_fin=False)
    b.caja((c0.x, gy - 0.12, gz + 0.06), (0.16, 0.03, 0.025), "pintura_roja")  # maneta (cerrada)
    # Manguera corta: del grifo al suelo, haciendo una vuelta floja.
    p.extra["grifo"] = [c0.x, gy - 0.14, gz - 0.08]
    p.extra["nivel"] = c0.z + 0.95
    p.extra["pie"] = c0.z
    return p


def manguera_tanque(grifo):
    p = Pieza("tanque_manguera", peso_uv=1.2)
    g = Vector(grifo)
    cam = [g, g + Vector((0, -0.02, -0.12)), Vector((g.x + 0.08, g.y - 0.15, 0.04)), Vector((g.x + 0.4, g.y - 0.2, 0.035)),
           Vector((g.x + 0.55, g.y - 0.48, 0.035)), Vector((g.x + 0.3, g.y - 0.7, 0.035)),
           Vector((g.x - 0.05, g.y - 0.6, 0.035)), Vector((g.x - 0.15, g.y - 0.35, 0.035)),
           Vector((g.x + 0.05, g.y - 0.22, 0.07)), Vector((g.x + 0.35, g.y - 0.3, 0.075)),
           Vector((g.x + 0.5, g.y - 0.55, 0.075))]
    p.baja.tubo(cam, 0.032, "manguera", lados=4, radio_curva=0.12, pasos_curva=1)
    # Boquilla de latón en la punta.
    fin, prev = cam[-1], cam[-2]
    p.baja.cilindro(fin, (fin - prev).normalized(), 0.04, 0.09, "laton", lados=6)
    return p


def bajante():
    """Bajante grueso del canalón al filtro del tanque."""
    p = Pieza("bajante_tanque", peso_uv=1.2)
    b, a = p.baja, p.alta
    yb = TANQUE.y
    zt = TANQUE.z + TANQUE_H
    camino = [(5.72, yb, 4.8), (5.72, yb, 2.75), (6.05, yb, 2.35), (6.05, yb, zt + 0.32)]
    r = 0.09
    b.tubo(camino, r, "metal_oscuro", lados=7, radio_curva=0.25, pasos_curva=2, tapa_ini=False, tapa_fin=False)
    fin = Vector(camino[-1])
    b.revolucion([(r, 0), (r * 0.8, 0), (r * 0.8, 0.12), (0.0, 0.12)], fin, 8, "metal_oscuro", eje=(0, 0, 1),
                 tapa_ini=False, tapa_fin=False, giro=math.pi / 8, mats_tramo=["metal_oscuro", "negro_mate",
                                                                               "negro_mate"])
    for z in (4.2, 3.2):
        b.revolucion([(r + 0.02, 0), (r + 0.02, 0.07)], (5.72, yb, z - 0.035), 8, "metal_oscuro", giro=math.pi / 8)
        b.caja_de((MX + PANEL, yb - 0.02, z - 0.03), (5.72 - r - 0.01, yb + 0.02, z + 0.03), "metal_oscuro")
        b.caja_de((MX + PANEL, yb - 0.09, z - 0.09), (MX + PANEL + 0.02, yb + 0.09, z + 0.09), "metal_oscuro",
                  sin=("-x",))
        for dy in (-0.055, 0.055):
            tornillo(p, (MX + PANEL + 0.02, yb + dy, z), (1, 0, 0), 0.018, "acero", en_baja=False)
    return p


# ======================================================================================================
# Puertas
# ======================================================================================================


def puerta():
    """Puerta de tablas como la del minero, de madera húmeda con verdín. Pivote en las bisagras."""
    h = HOJA
    p = Pieza("puerta", pivote=(EJE_PUERTA.x, EJE_PUERTA.y, h["z0"]), peso_uv=1.7)
    b, a = p.baja, p.alta
    n = 5
    gap = 0.025
    w = (h["x1"] - h["x0"] - (n - 1) * gap) / n
    centros = []
    rnd = random.Random(12)
    for i in range(n):
        x0 = h["x0"] + i * (w + gap)
        centros.append(x0 + w / 2)
        # Tablas algo hinchadas por la humedad: cada una sobresale un poco distinto.
        hinchada = rnd.uniform(-0.006, 0.006)
        b.caja_de((x0, h["y0"] + hinchada, h["z0"]), (x0 + w, h["y0"] + 0.12, h["z1"]), "madera_humeda", sin=("-z",))
    b.caja_de((h["x0"] + 0.01, h["y0"] + 0.12, h["z0"] + 0.02), (h["x1"] - 0.01, h["y0"] + 0.15, h["z1"] - 0.02),
              "madera_oscura", sin=("-z", "+z", "-y"))
    yt0, yt1 = h["y0"] + 0.15, h["y0"] + 0.22
    for zt in (1.2, 4.18):
        b.caja_de((h["x0"] + 0.07, yt0, zt - 0.15), (h["x1"] - 0.07, yt1, zt + 0.15), "madera_oscura", sin=("-y",))
    pa, pb = Vector((h["x0"] + 0.2, (yt0 + yt1) / 2, 1.38)), Vector((h["x1"] - 0.2, (yt0 + yt1) / 2, 4.0))
    d = pb - pa
    b.caja((pa + pb) / 2, (0.24, yt1 - yt0, d.length - 0.1), "madera_oscura",
           giro=rot("Y", math.degrees(math.atan2(d.x, d.z))), sin=("-y",))
    for zt in (1.2, 4.18):
        for x in centros:
            for dz in (-0.08, 0.08):
                a.cupula((x, yt1, zt + dz), (0, 1, 0), 0.018, "hierro", alto=0.01, lados=8)
    yf = h["y0"]
    for zb in (1.78, 3.65):
        b.caja_de((h["x0"] + 0.06, yf - 0.025, zb - 0.075), (h["x1"] - 0.06, yf, zb + 0.075), "hierro", sin=("+y",))
        for x in centros:
            tornillo(p, (x, yf - 0.025, zb), (0, -1, 0), 0.034, "hierro", en_baja=False)
    for zh in BISAGRAS_Z:
        hoja = [(EJE_PUERTA.x, -0.1), (h["x0"] + 0.45, -0.075), (h["x0"] + 0.6, 0.0), (h["x0"] + 0.45, 0.075),
                (EJE_PUERTA.x, 0.1)]
        b.placa([(x, zh + z) for x, z in hoja], Vector((0, yf, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)),
                Vector((0, -1, 0)), 0.025, "hierro")
        b.cilindro((EJE_PUERTA.x, EJE_PUERTA.y, zh - 0.062), (0, 0, 1), 0.06, 0.124, "hierro", lados=8)
        for x in (h["x0"] + 0.15, h["x0"] + 0.4):
            tornillo(p, (x, yf - 0.025, zh), (0, -1, 0), 0.026, "hierro")
    m = MANIJA
    b.caja_de((m.x - 0.09, yf - 0.03, m.z - 0.3), (m.x + 0.09, yf, m.z + 0.12), "acero", sin=("+y",))
    for dx in (-0.055, 0.055):
        for dz in (-0.26, 0.08):
            tornillo(p, (m.x + dx, yf - 0.03, m.z + dz), (0, -1, 0), 0.02, "acero", en_baja=False)
    b.cilindro((m.x, yf - 0.03, m.z), (0, -1, 0), 0.055, 0.045, "acero_pulido", lados=10, tapa_ini=False)
    palanca = [(m.x, yf - 0.06, m.z), (m.x, yf - 0.15, m.z), (m.x - 0.3, yf - 0.17, m.z - 0.01)]
    b.tubo(palanca, 0.03, "acero_pulido", lados=6, radio_curva=0.06, pasos_curva=2, tapa_ini=False)
    cp._cerradura(b, Vector((m.x, yf - 0.03, m.z - 0.18)))
    for dz in (-0.1, 0.1):
        tornillo(p, (m.x, yf - 0.052, m.z - 0.18 + dz), (0, -1, 0), 0.014, "laton", lados_baja=5)
    p.extra["manija_agarre"] = [m.x - 0.22, yf - 0.17, m.z - 0.01]
    return p


def puerta_marco():
    p = Pieza("puerta_marco", peso_uv=1.3)
    b, a = p.baja, p.alta
    x0, x1, z1 = PUERTA["x0"], PUERTA["x1"], PUERTA["z1"]
    yf = -MY - 0.16
    b.caja_de((x0 - 0.12, yf, BASE_Z), (x0 + 0.08, -MY - PANEL, z1 + 0.18), "metal_oscuro", sin=("+y", "-z"))
    b.caja_de((x1 - 0.08, yf, BASE_Z), (x1 + 0.12, -MY - PANEL, z1 + 0.18), "metal_oscuro", sin=("+y", "-z"))
    b.caja_de((x0 + 0.08, yf, z1 - 0.02), (x1 - 0.08, -MY - PANEL, z1 + 0.18), "metal_oscuro", sin=("+y",))
    b.caja_de((x0 + 0.08, -MY - PANEL, 0.6), (x0 + 0.12, -MY + MURO, z1 - 0.02), "metal_oscuro", sin=("-x",))
    b.caja_de((x1 - 0.12, -MY - PANEL, 0.6), (x1 - 0.08, -MY + MURO, z1 - 0.02), "metal_oscuro", sin=("+x",))
    b.caja_de((x0 + 0.08, -MY - PANEL, z1 - 0.1), (x1 - 0.08, -MY + MURO, z1 - 0.02), "metal_oscuro",
              sin=("+z", "-x", "+x"))
    yg0, yg1 = HOJA["y0"] + 0.02, HOJA["y1"] - 0.02
    b.caja_de((x0 + 0.12, yg0, 0.6), (x0 + 0.145, yg1, z1 - 0.1), "goma", sin=("-x", "-z", "+z"))
    b.caja_de((x1 - 0.145, yg0, 0.6), (x1 - 0.12, yg1, z1 - 0.1), "goma", sin=("+x", "-z", "+z"))
    b.caja_de((x0 + 0.12, yg0, z1 - 0.125), (x1 - 0.12, yg1, z1 - 0.1), "goma", sin=("+z", "-x", "+x"))
    b.caja_de((x0 + 0.08, yf, BASE_Z), (x1 - 0.08, -MY + MURO, 0.6), "acero", sin=("-z",))
    for k in range(14):
        y = yf + 0.03 + k * 0.034
        a.caja_de((x0 + 0.12, y, 0.6), (x1 - 0.12, y + 0.012, 0.606), "acero")
    e = EJE_PUERTA
    for zh in BISAGRAS_Z:
        b.caja_de((x0 - 0.1, yf - 0.02, zh - 0.1), (e.x - 0.03, yf, zh + 0.1), "hierro", sin=("+y",))
        for z0 in (zh - 0.19, zh + 0.066):
            b.cilindro((e.x, e.y, z0), (0, 0, 1), 0.06, 0.124, "hierro", lados=8)
        b.revolucion([(0.025, 0), (0.035, 0.05), (0.0, 0.085)], (e.x, e.y, zh + 0.19), 6, "hierro",
                     tapa_ini=False)
        b.revolucion([(0.0, -0.085), (0.035, -0.05), (0.025, 0)], (e.x, e.y, zh - 0.19), 6,
                     "hierro", tapa_fin=False)
        for x in (x0 - 0.06, x0 + 0.02):
            tornillo(p, (x, yf - 0.02, zh), (0, -1, 0), 0.024, "hierro", en_baja=False)
    for z in (0.9, 1.9, 2.9, 3.9, 4.8):
        for x in (x0 - 0.02, x1 + 0.02):
            tornillo(p, (x, yf, z), (0, -1, 0), 0.022, "acero", en_baja=False)
    return p


def puerta_lateral():
    """Puerta metálica del lateral izquierdo (da al pasillo del invernadero), con su marco y burlete."""
    pl = IZQ
    L = PUERTA_L
    marco = Pieza("puerta_lateral_marco", peso_uv=1.1)
    cc._marco_puerta(marco, pl, L["u0"], L["u1"], L["v1"], "metal_oscuro", ancho=0.15, d_frente=0.16)
    # Hoja: chapa con cuarterones estampados, cerradura y manilla. Bisagras en el lado de delante (u0).
    d0, d1 = -0.05, 0.02
    hu0, hu1, hv0, hv1 = L["u0"] + 0.04, L["u1"] - 0.04, L["v0"] + 0.1, L["v1"] - 0.04
    eje = pl.p(hu0 - 0.02, 0, d1 + 0.02)
    p = Pieza("puerta_lateral", pivote=(eje.x, eje.y, hv0), peso_uv=1.4)
    b, a = p.baja, p.alta
    caja_plano(b, pl, hu0, hu1, hv0, hv1, d0, d1, "pintura_gris", sin=("-z",))
    for v0, v1 in ((hv0 + 0.2, 1.85), (2.05, hv1 - 0.2)):
        caja_plano(b, pl, hu0 + 0.18, hu1 - 0.18, v0, v1, d1, d1 + 0.02, "pintura_gris", sin=("+y",))
    # Junta de goma alrededor (el pasillo guarda la humedad).
    for u0, u1, v0, v1 in ((hu0 - 0.025, hu0, hv0, hv1), (hu1, hu1 + 0.025, hv0, hv1),
                           (hu0 - 0.025, hu1 + 0.025, hv1, hv1 + 0.025)):
        caja_plano(b, pl, u0, u1, v0, v1, d0 + 0.01, d1 - 0.01, "goma", sin=("+y",))
    mu, mv = hu1 - 0.14, 1.95
    caja_plano(b, pl, mu - 0.05, mu + 0.05, mv - 0.2, mv + 0.08, d1, d1 + 0.02, "acero", sin=("+y",))
    b.tubo([pl.p(mu, mv, d1 + 0.02), pl.p(mu, mv, d1 + 0.1), pl.p(mu - 0.22, mv - 0.01, d1 + 0.11)], 0.026,
           "acero_pulido", lados=6, radio_curva=0.05, pasos_curva=2, tapa_ini=False)
    cp._cerradura(b, pl.p(mu, mv - 0.13, d1 + 0.02), u=pl.u, v=pl.v, n=pl.n, mat="acero")
    for vh in (hv0 + 0.4, hv1 - 0.4):
        b.cilindro(pl.p(hu0 - 0.02, vh - 0.12, d1 + 0.02), (0, 0, 1), 0.035, 0.24, "metal_oscuro", lados=6)
        caja_plano(b, pl, hu0, hu0 + 0.3, vh - 0.06, vh + 0.06, d1, d1 + 0.015, "metal_oscuro", sin=("+y",))
        for uu in (hu0 + 0.1, hu0 + 0.24):
            tornillo(p, pl.p(uu, vh, d1 + 0.015), pl.n, 0.016, "acero", en_baja=False)
    # Pegatina de una hoja (malla alta): la puerta del invernadero.
    caja_plano(a, pl, -0.12, 0.12, 2.9, 3.1, d1 + 0.02, d1 + 0.023, "papel")
    p.extra["manija"] = list(pl.p(mu - 0.1, mv, d1 + 0.11))
    return [marco, p]


# ======================================================================================================
# Ventanas
# ======================================================================================================


def ventana_frontal():
    V = VENTANA
    pl = FRENTE
    marco = Pieza("ventana_frontal_marco", peso_uv=1.3)
    t = cp._marco_ventana(marco, pl, V["x0"], V["x1"], V["z0"], V["z1"], con_inferior=False)
    b = marco.baja
    um = (V["x0"] + V["x1"]) / 2
    vm = 3.5
    caja_plano(b, pl, um - 0.035, um + 0.035, V["z0"] + t, V["z1"] - t, -0.08, -0.025, "metal_oscuro", sin=("+y",))
    caja_plano(b, pl, V["x0"] + t, um - 0.035, vm - 0.035, vm + 0.035, -0.08, -0.025, "metal_oscuro",
               sin=("+y", "+x"))
    caja_plano(b, pl, um + 0.035, V["x1"] - t, vm - 0.035, vm + 0.035, -0.08, -0.025, "metal_oscuro",
               sin=("+y", "-x"))
    cristal = Pieza("ventana_frontal_cristal", peso_uv=0.5)
    caja_plano(cristal.baja, pl, V["x0"] + t, V["x1"] - t, V["z0"] + t, V["z1"] - t, -0.13, -0.08, "vidrio")
    alfeizar = Pieza("ventana_frontal_alfeizar", peso_uv=1.2)
    ab = alfeizar.baja
    caja_plano(ab, pl, V["x0"] - 0.24, V["x1"] + 0.24, V["z0"] - 0.15, V["z0"], -MURO + 0.05, 0.5, "losa",
               sin=("+y",), giro_extra=rot("X", -2.0))
    caja_plano(alfeizar.alta, pl, V["x0"] - 0.2, V["x1"] + 0.2, V["z0"] - 0.16, V["z0"] - 0.145, 0.4, 0.42,
               "negro_mate")
    for uu in (V["x0"] + 0.25, V["x1"] - 0.25):
        mens = [(0.0, 0.0), (0.0, -0.32), (0.06, -0.32), (0.38, -0.02), (0.38, 0.0)]
        ab.placa([(dd, vv + V["z0"] - 0.15) for dd, vv in mens], pl.p(uu - 0.02, 0, PANEL), pl.n,
                 Vector((0, 0, 1)), pl.u, 0.04, "hierro", atras=True)
    # Cortina de lino recogida a un lado (se ve desde fuera).
    cortinas = Pieza("ventana_frontal_cortina", peso_uv=0.8)
    cb = cortinas.baja
    d = -0.21
    zt, zb = V["z1"] - t - 0.06, V["z0"] + t + 0.04
    cb.cilindro(pl.p(V["x0"] + t, zt + 0.03, d), (1, 0, 0), 0.018, V["x1"] - V["x0"] - 2 * t, "acero", lados=6,
                tapa_ini=False, tapa_fin=False)
    anillos = []
    borde = V["x1"] - t - 0.02
    for v, ancho, amp in ((zt, 0.85, 0.03), (3.2, 0.38, 0.045), (zb, 0.55, 0.035)):
        k = 8
        delante, detras = [], []
        for i in range(k + 1):
            x = borde - (i / k) * ancho
            y = amp * (1 if i % 2 else -1) * (0.6 if i in (0, k) else 1.0)
            delante.append(pl.p(x, v, d - 0.035 + y))
            detras.append(pl.p(x, v, d - 0.035 + y + 0.012))
        anillos.append(delante + list(reversed(detras)))
    cb.loft(anillos, "tela", tapa_ini=False, tapa_fin=True, suave=True)
    cb.recalcular(cb.ultimas)
    macetas = macetas_hierbas(Vector((0, -MY - 0.32, V["z0"] - 0.012)))
    return [marco, cristal, alfeizar, macetas]


def _maceta(c, base, r, alto, semilla):
    """Maceta de barro con su reborde y tierra."""
    perfil = [(r * 0.68, 0.0), (r * 0.92, alto * 0.78), (r, alto), (r * 0.86, alto), (r * 0.82, alto * 0.88)]
    c.revolucion(perfil, base, 8, "barro", tapa_ini=True, oculta_ini=True, tapa_fin=True, mat_fin="tierra",
                 giro=semilla)
    return base + Vector((0, 0, alto * 0.88))


def macetas_hierbas(y_base):
    """Tres macetas de barro en el alféizar: romero (alto), albahaca (frondosa) y lavanda (con flores)."""
    p = Pieza("macetas_hierbas", peso_uv=2.2)
    b, a = p.baja, p.alta
    rnd = random.Random(23)
    z = y_base.z
    yb = y_base.y
    # Romero: varas altas y finas.
    t1 = _maceta(b, Vector((-3.55, yb, z)), 0.15, 0.27, 0.2)
    for k in range(5):
        ang = math.tau * k / 5 + rnd.uniform(-0.2, 0.2)
        inc = rnd.uniform(0.12, 0.3)
        alto = rnd.uniform(0.45, 0.62)
        d = Vector((math.cos(ang) * inc, math.sin(ang) * inc, 1)).normalized()
        base_v = t1 + Vector((math.cos(ang) * 0.04, math.sin(ang) * 0.04, 0))
        pts = [base_v, base_v + d * alto * 0.5 + Vector((0, 0, 0.02)), base_v + d * alto]
        b.tubo(pts, 0.022, "hoja_romero", lados=3, radios=[0.02, 0.026, 0.008])
        # Agujas (malla alta).
        for j in range(16):
            f = 0.15 + 0.8 * j / 15
            q = base_v + d * alto * f
            rum = rnd.uniform(0, math.tau)
            hoja3d(a, q, rum, 0.06, 0.012, -0.03, "hoja_romero", subida=0.02, secciones=2)
    # Albahaca: mata frondosa y redonda.
    t2 = _maceta(b, Vector((-2.6, yb, z)), 0.18, 0.28, 0.9)
    bulto(b, t2 + Vector((0, 0, -0.02)), 0.24, 0.36, "hoja_albahaca", lados=8, semilla=3)
    for _ in range(70):
        ang = rnd.uniform(0, math.tau)
        el = rnd.uniform(0.1, 1.2)
        q = t2 + Vector((math.cos(ang) * math.cos(el) * 0.24, math.sin(ang) * math.cos(el) * 0.24,
                         0.05 + math.sin(el) * 0.3))
        hoja3d(a, q - Vector((math.cos(ang), math.sin(ang), 0)) * 0.05, ang + rnd.uniform(-0.6, 0.6),
               rnd.uniform(0.09, 0.13), rnd.uniform(0.06, 0.08), 0.03, "hoja_albahaca", subida=0.03, secciones=3)
    # Lavanda: matita gris verde con espigas moradas.
    t3 = _maceta(b, Vector((-1.68, yb, z)), 0.15, 0.25, 1.7)
    bulto(b, t3, 0.17, 0.17, "hoja_romero", lados=7, semilla=8)
    for k in range(5):
        ang = math.tau * k / 5 + 0.3
        base_v = t3 + Vector((math.cos(ang) * 0.06, math.sin(ang) * 0.06, 0.12))
        tope = base_v + Vector((math.cos(ang) * 0.1, math.sin(ang) * 0.1, rnd.uniform(0.28, 0.38)))
        b.tubo([base_v, tope], 0.008, "tallo", lados=3, tapa_ini=False)
        espiga = [tope - (tope - base_v).normalized() * 0.12, tope + (tope - base_v).normalized() * 0.01]
        b.tubo(espiga, 0.026, "flor", lados=4, radios=[0.022, 0.012])
        for j in range(8):
            q = espiga[0].lerp(espiga[1], j / 8)
            a.cupula(q + Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0)), (0, -1, 0.3), 0.014,
                     "flor", alto=0.012, lados=5)
    return p


def ventana_lateral():
    """Ventana estándar del muro derecho con la rejilla de ventilación debajo."""
    pl = DER
    L = VLAT
    marco = Pieza("ventana_lateral_marco", peso_uv=1.2)
    t = cp._marco_ventana(marco, pl, L["u0"], L["u1"], L["v0"], L["v1"], ancho=0.14)
    caja_plano(marco.baja, pl, L["u0"] + t, L["u1"] - t, 3.62, 3.68, -0.08, -0.03, "metal_oscuro", sin=("+y",))
    cristal = Pieza("ventana_lateral_cristal", peso_uv=0.5)
    caja_plano(cristal.baja, pl, L["u0"] + t, L["u1"] - t, L["v0"] + t, L["v1"] - t, -0.13, -0.08, "vidrio")
    rej = Pieza("rejilla_ventilacion", peso_uv=1.6)
    R = REJILLA
    b = rej.baja
    dF = PANEL + 0.06
    caja_plano(b, pl, R["u0"], R["u1"], R["v0"], R["v1"], PANEL, PANEL + 0.01, "negro_mate",
               sin=("+y", "-x", "+x", "-z", "+z"))
    m = 0.06
    caja_plano(b, pl, R["u0"], R["u0"] + m, R["v0"], R["v1"], PANEL, dF, "metal_oscuro", sin=("+y",))
    caja_plano(b, pl, R["u1"] - m, R["u1"], R["v0"], R["v1"], PANEL, dF, "metal_oscuro", sin=("+y",))
    caja_plano(b, pl, R["u0"] + m, R["u1"] - m, R["v0"], R["v0"] + m, PANEL, dF, "metal_oscuro",
               sin=("+y", "-x", "+x"))
    caja_plano(b, pl, R["u0"] + m, R["u1"] - m, R["v1"] - m, R["v1"], PANEL, dF, "metal_oscuro",
               sin=("+y", "-x", "+x"))
    # Lamas inclinadas (dejan pasar el aire, no la lluvia).
    for j in range(5):
        vv = R["v0"] + m + 0.04 + j * (R["v1"] - R["v0"] - 2 * m - 0.08) / 4
        caja_plano(b, pl, R["u0"] + m, R["u1"] - m, vv - 0.035, vv + 0.035, PANEL + 0.015, dF - 0.01,
                   "metal_oscuro", sin=("+y", "-x", "+x"), giro_extra=rot("X", -38))
    for uu in (R["u0"] + 0.03, R["u1"] - 0.03):
        for vv in (R["v0"] + 0.03, R["v1"] - 0.03):
            tornillo(rej, pl.p(uu, vv, dF), pl.n, 0.016, "acero", en_baja=False)
    return [marco, cristal, rej]


# ======================================================================================================
# Fachada: lámpara, cartel, gancho y delantal, enredadera
# ======================================================================================================


def lampara():
    pl = FRENTE
    xc = (PUERTA["x0"] + PUERTA["x1"]) / 2
    zp = 5.42
    cuerpo = Pieza("lampara", peso_uv=1.8)
    b = cuerpo.baja
    b.cilindro(pl.p(xc, zp, PANEL), pl.n, 0.16, 0.06, "metal_oscuro", lados=10, tapa_ini=False)
    cx, cy = xc, -MY - 0.7
    zt = 5.34
    brazo = [pl.p(xc, zp, PANEL + 0.04), (xc, -MY - 0.34, zp + 0.02), (xc, cy - 0.02, zp - 0.03), (cx, cy, zt + 0.02)]
    b.tubo(brazo, 0.03, "metal_oscuro", lados=6, radio_curva=0.12, pasos_curva=2, tapa_ini=False, tapa_fin=False)
    b.revolucion([(0.18, zt - 0.125), (0.23, zt - 0.135), (0.23, zt - 0.11), (0.04, zt + 0.015)], (cx, cy, 0), 10,
                 "metal_oscuro", tapa_ini=True, tapa_fin=True)
    zb = zt - 0.46
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        d = Vector((math.cos(ang), math.sin(ang), 0))
        c = Vector((cx, cy, (zb + zt - 0.12) / 2)) + d * 0.185
        b.caja(c, (0.016, 0.016, zt - 0.12 - zb), "metal_oscuro", giro=rot("Z", 45 + 90 * k))
    anillo = [Vector((cx, cy, zb)) + Vector((math.cos(a_), math.sin(a_), 0)) * 0.185
              for a_ in [math.tau * i / 8 for i in range(9)]]
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


CARTEL = dict(x0=3.0, x1=4.3, z0=2.85, z1=3.65)


def cartel():
    """Placa de madera tallada: «Productos frescos — pregunte dentro», con una hoja tallada y dos tirafondos."""
    pl = FRENTE
    C = CARTEL
    p = Pieza("cartel", peso_uv=3.2)
    b, a = p.baja, p.alta
    w, h, ch = C["x1"] - C["x0"], C["z1"] - C["z0"], 0.06
    uc, vc = (C["x0"] + C["x1"]) / 2, (C["z0"] + C["z1"]) / 2
    # Tablón con las esquinas achaflanadas y el canto biselado (dos placas: la de delante algo menor).
    contorno = [(-w / 2 + ch, -h / 2), (w / 2 - ch, -h / 2), (w / 2, -h / 2 + ch), (w / 2, h / 2 - ch),
                (w / 2 - ch, h / 2), (-w / 2 + ch, h / 2), (-w / 2, h / 2 - ch), (-w / 2, -h / 2 + ch)]
    d0 = PANEL + 0.02
    b.placa([(uc + x, vc + y) for x, y in contorno], pl.p(0, 0, d0), pl.u, pl.v, pl.n, 0.05, "madera_cartel",
            atras=True)
    k = 0.035
    interior = [(x - math.copysign(k, x) * 0.7, y - math.copysign(k, y) * 0.7) for x, y in contorno]
    b.placa([(uc + x, vc + y) for x, y in interior], pl.p(0, 0, d0 + 0.05), pl.u, pl.v, pl.n, 0.018,
            "madera_cartel")
    # Tacos que la separan de la pared.
    for x in (-w / 2 + 0.2, w / 2 - 0.2):
        caja_plano(b, pl, uc + x - 0.06, uc + x + 0.06, vc - 0.06, vc + 0.06, PANEL, d0, "madera_oscura", sin=("+y",))
    # Letras talladas en relieve (malla alta: se hornean al atlas) y una hoja tallada.
    df = d0 + 0.068
    cc.texto(a, "PRODUCTOS FRESCOS", pl.p(uc + 0.06, vc + 0.12, df), pl.u, pl.v, pl.n, 0.12, 0.012,
             "letras_cartel", ancho_max=w - 0.42)
    cc.texto(a, "pregunte dentro", pl.p(uc + 0.06, vc - 0.13, df), pl.u, pl.v, pl.n, 0.09, 0.01, "letras_cartel",
             ancho_max=w - 0.5)
    # Hoja tallada a la izquierda del texto.
    hoja = [(0.0, -0.17), (0.07, -0.09), (0.085, 0.02), (0.05, 0.12), (0.0, 0.17), (-0.05, 0.12), (-0.085, 0.02),
            (-0.07, -0.09)]
    ux = uc - w / 2 + 0.16
    a.placa([(ux + x * math.cos(0.4) - y * math.sin(0.4), vc + x * math.sin(0.4) + y * math.cos(0.4))
             for x, y in hoja], pl.p(0, 0, df), pl.u, pl.v, pl.n, 0.01, "hoja_lechuga")
    a.tubo([pl.p(ux + 0.06, vc - 0.15, df + 0.012), pl.p(ux - 0.05, vc + 0.1, df + 0.012)], 0.006, "madera_cartel",
           lados=4)
    # Marco tallado (filete) alrededor.
    fil = [pl.p(uc + x * 0.9, vc + y * 0.84, df) for x, y in interior + [interior[0]]]
    a.tubo(fil, 0.007, "letras_cartel", lados=4, tapa_ini=False, tapa_fin=False)
    for x in (-w / 2 + 0.2, w / 2 - 0.2):
        tornillo(p, pl.p(uc + x, vc, d0 + 0.068), pl.n, 0.025, "hierro", lados_baja=6)
    return p


GANCHO = Vector((-0.55, -MY - PANEL, 3.75))


def gancho_delantal():
    """Gancho de hierro en la pared junto a la puerta, con el delantal de trabajo colgado."""
    pl = FRENTE
    g = Pieza("gancho", peso_uv=2.0)
    b = g.baja
    caja_plano(b, pl, GANCHO.x - 0.07, GANCHO.x + 0.07, GANCHO.z - 0.14, GANCHO.z + 0.1, PANEL, PANEL + 0.025,
               "hierro", sin=("+y",))
    for dz in (-0.09, 0.06):
        tornillo(g, pl.p(GANCHO.x, GANCHO.z + dz, PANEL + 0.025), pl.n, 0.016, "hierro")
    yb = -MY - PANEL - 0.025
    b.tubo([(GANCHO.x, yb, GANCHO.z - 0.04), (GANCHO.x, yb - 0.2, GANCHO.z - 0.05), (GANCHO.x, yb - 0.27, GANCHO.z + 0.04),
            (GANCHO.x, yb - 0.24, GANCHO.z + 0.1)], 0.02, "hierro", lados=5, radio_curva=0.05, pasos_curva=1)
    d = Pieza("delantal", peso_uv=1.4)
    db = d.baja
    # Delantal de lona: cuelga del gancho por la cinta del cuello y cae con pliegues contra la pared.
    top = GANCHO.z - 0.02
    filas = [(top - 0.18, 0.16, 0.08), (top - 0.32, 0.22, 0.09), (top - 0.62, 0.26, 0.08), (top - 0.95, 0.3, 0.07),
             (top - 1.28, 0.31, 0.06)]
    anillos = []
    for k, (z, ancho, sep) in enumerate(filas):
        n = 5
        delante, detras = [], []
        for i in range(n + 1):
            f = i / n
            x = GANCHO.x + (f - 0.5) * 2 * ancho
            pl_y = yb - sep - 0.025 * math.sin(f * math.pi * 3 + k) * (k / 4)
            delante.append(Vector((x, pl_y, z)))
            detras.append(Vector((x, pl_y + 0.015, z)))
        anillos.append(delante + list(reversed(detras)))
    db.loft(anillos, "delantal", tapa_ini=True, tapa_fin=True, suave=True)
    db.recalcular(db.ultimas)
    # Cinta del cuello: del gancho a las dos esquinas de arriba.
    for s_ in (-1, 1):
        db.tubo([(GANCHO.x + s_ * 0.16, yb - 0.08, top - 0.18), (GANCHO.x + s_ * 0.06, yb - 0.2, top - 0.02),
                 (GANCHO.x, yb - 0.25, GANCHO.z + 0.03)], 0.012, "delantal", lados=4)
    # Bolsillo con unas tijeras asomando (malla alta y baja).
    zb = top - 0.85
    d.alta.caja((GANCHO.x, yb - 0.085 - 0.012, zb), (0.3, 0.008, 0.2), "delantal")
    db.tubo([(GANCHO.x + 0.06, yb - 0.1, zb + 0.06), (GANCHO.x + 0.09, yb - 0.1, zb + 0.18)], 0.012, "pintura_roja",
            lados=4)
    return [g, d]


def enredadera():
    """Enredadera que sube por la esquina delantera derecha desde una jardinera, con 10 hojas 3D."""
    p = Pieza("enredadera", peso_uv=2.0)
    b, a = p.baja, p.alta
    rnd = random.Random(41)
    # Jardinera de tablas en la esquina.
    jx0, jx1, jy0, jy1 = 4.45, 5.3, -4.62, -4.12
    for (x0, x1, y0, y1) in ((jx0, jx1, jy0, jy0 + 0.05), (jx0, jx1, jy1 - 0.05, jy1), (jx0, jx0 + 0.05, jy0, jy1),
                             (jx1 - 0.05, jx1, jy0, jy1)):
        b.caja_de((x0, y0, BASE_Z), (x1, y1, BASE_Z + 0.32), "madera_compost", sin=("-z",))
    b.caja_de((jx0 + 0.05, jy0 + 0.05, BASE_Z), (jx1 - 0.05, jy1 - 0.05, BASE_Z + 0.27), "tierra", sin=("-z",),
              ocultas=("-x", "+x", "-y", "+y"))
    # Tallo principal: sube pegado al panel de la fachada, serpenteando, y dobla la esquina arriba.
    yw = -MY - PANEL - 0.04
    puntos = [Vector((4.85, -4.35, BASE_Z + 0.27)), Vector((4.8, yw - 0.06, 1.0)), Vector((4.7, yw, 1.7)),
              Vector((4.82, yw, 2.4)), Vector((4.62, yw, 3.1)), Vector((4.78, yw, 3.8)), Vector((4.6, yw, 4.4)),
              Vector((4.75, yw, 4.95)), Vector((4.55, yw, 5.35))]
    radios = [0.045, 0.04, 0.036, 0.032, 0.028, 0.024, 0.02, 0.016, 0.01]
    b.tubo(puntos, 0.03, "tallo", lados=4, radios=radios)
    # Rama que dobla la esquina hacia el lateral derecho.
    rama = [Vector((4.8, yw, 2.6)), Vector((5.02, yw, 2.75)), Vector((MX + PANEL + 0.04, -3.85, 2.95)),
            Vector((MX + PANEL + 0.04, -3.55, 3.3))]
    b.tubo(rama, 0.02, "tallo", lados=4, radios=[0.022, 0.018, 0.014, 0.008])
    # Grapas de alambre que la sujetan a la pared (malla alta).
    for q in puntos[2:7:2]:
        a.tubo([q + Vector((-0.05, 0.03, 0)), q + Vector((-0.04, -0.03, 0)), q + Vector((0.04, -0.03, 0)),
                q + Vector((0.05, 0.03, 0))], 0.006, "acero", lados=4)
    # Diez hojas en forma de corazón, cada una con su peciolo.
    hojas = [(1, 0.3, 200, 0.34), (2, 0.6, 340, 0.33), (3, 0.2, 160, 0.31), (3, 0.8, 20, 0.34), (4, 0.4, 190, 0.3),
             (5, 0.3, 350, 0.3), (6, 0.5, 170, 0.27), (7, 0.4, 10, 0.25)]
    def hoja_pared(origen, ang, tam, normal):
        """Hoja plana contra la pared (como la hiedra): mira hacia fuera y cae un poco hacia abajo."""
        n = Vector(normal)
        u_pared = Vector((0, 0, 1)).cross(n).normalized()
        d = (u_pared * math.cos(ang) + Vector((0, 0, 1)) * (math.sin(ang) - 0.55)).normalized()
        l_ = n.cross(d).normalized()
        n2 = d.cross(l_).normalized()
        ini_h = set(b.bm.verts)
        hoja3d(b, Vector((0, 0, 0)), 0.0, tam, tam * 0.95, 0.0, "hoja_enredadera", subida=0.0,
               secciones=3, alabeo=rnd.uniform(-0.3, 0.3), corazon=True)
        M = Matrix.Translation(Vector(origen) + n * 0.03) @ Matrix((d, l_, n2)).transposed().to_4x4()
        b.transformar([v for v in b.bm.verts if v not in ini_h], M)

    for seg, f, rumbo, tam in hojas:
        q = puntos[seg].lerp(puntos[seg + 1], f)
        r = math.radians(rumbo)
        pec = q + Vector((math.cos(r) * 0.06, -0.035, -0.02))
        a.tubo([q, pec], 0.008, "tallo", lados=3, tapa_ini=False)
        hoja_pared(pec, r, tam, (0, -1, 0))
    for f, rumbo, tam in ((0.5, 250, 0.27), (0.95, 80, 0.25)):
        q = rama[1].lerp(rama[2], f) if f < 0.9 else rama[3]
        hoja_pared(q + Vector((0.035, 0, 0.0)), math.radians(rumbo), tam, (1, 0, 0))
    # Zarcillos (malla alta).
    for seg in range(1, 8):
        q = puntos[seg]
        a.tubo([q + Vector((0.02 * math.cos(t), -0.02, 0.02 * math.sin(t) + t * 0.01)) * 1.0 + Vector((0.04, 0, 0))
                for t in [i * 0.8 for i in range(10)]], 0.004, "tallo", lados=3)
    return p


# ======================================================================================================
# Lateral derecho: medidores, grifo y manguera
# ======================================================================================================


def medidores(conexion_solar):
    """Medidor de luz (cable al panel solar) y medidor de agua (tubería del suelo), los dos con pantallita neón."""
    pl = DER
    piezas = []
    # ---- luz ----
    u0, u1, v0, v1 = -3.35, -2.75, 2.7, 3.5
    d0, d1 = PANEL, 0.27
    luz = Pieza("medidor_luz", peso_uv=1.6)
    b = luz.baja
    caja_plano(b, pl, u0, u1, v0, v1, d0, d1, "pintura_gris", sin=("+y",))
    caja_plano(b, pl, u0 + 0.05, u1 - 0.05, v0 + 0.05, v1 - 0.05, d1, d1 + 0.012, "pintura_gris", sin=("+y",))
    hueco = (-3.18, -2.92, 3.17, 3.33)
    caja_plano(b, pl, hueco[0] - 0.03, hueco[1] + 0.03, hueco[2] - 0.03, hueco[3] + 0.03, d1 + 0.012, d1 + 0.03,
               "metal_oscuro", sin=("+y",))
    caja_plano(b, pl, u1 - 0.1, u1 - 0.06, 2.95, 3.12, d1 + 0.012, d1 + 0.04, "metal_oscuro", sin=("+y",))
    tri = [(-3.05 - 0.09, 2.82), (-3.05 + 0.09, 2.82), (-3.05, 2.97)]
    luz.alta.placa(tri, pl.p(0, 0, d1 + 0.012), pl.u, pl.v, pl.n, 0.002, "pegatina")
    for uu in (u0 + 0.04, u1 - 0.04):
        for vv in (v0 + 0.04, v1 - 0.04):
            luz.alta.cupula(pl.p(uu, vv, d1 + 0.012), pl.n, 0.012, "acero", alto=0.008, lados=6)
    pant = Pieza("medidor_luz_pantalla_neon", peso_uv=0.5)
    caja_plano(pant.baja, pl, hueco[0], hueco[1], hueco[2], hueco[3], d1 + 0.015, d1 + 0.034, "neon", sin=("+y",))
    piezas += [luz, pant]
    # Cable del panel solar: baja por el alero y la pared hasta el medidor.
    cable = Pieza("cable_electrico", peso_uv=1.0)
    x = MX + PANEL + 0.08
    cw = [Vector(conexion_solar), Vector((4.2, -3.03, z_cresta(4.2) + 0.03)), Vector((5.15, -3.05, z_cresta(5.15) + 0.03)),
          Vector((5.62, -3.05, z_cresta(5.55) - 0.05)), Vector((5.6, -3.05, 5.15)), Vector((x, -3.05, 4.95)),
          Vector((x, -3.05, 3.9)), Vector((x, -3.05, v1 + 0.02))]
    cable.baja.tubo(cw, 0.024, "goma", lados=4, radio_curva=0.1, pasos_curva=1)
    for z in (4.6, 4.15):
        caja_plano(cable.baja, pl, -3.11, -2.99, z - 0.03, z + 0.03, PANEL, PANEL + 0.13, "metal_oscuro", sin=("+y",))
    piezas.append(cable)
    # ---- agua ----
    agua = Pieza("medidor_agua", peso_uv=1.8)
    b = agua.baja
    uc, vc = -2.2, 1.95
    d = 0.2
    caja_plano(b, pl, uc - 0.28, uc + 0.28, vc - 0.3, vc + 0.3, PANEL, PANEL + 0.025, "pintura_gris", sin=("+y",))
    # Tubería: sale del suelo, sube al contador (cuerpo de latón con esfera) y entra en la pared.
    tubo = [pl.p(uc + 0.1, 0.0, d), pl.p(uc + 0.1, vc - 0.18, d)]
    b.tubo(tubo, 0.035, "acero", lados=6, tapa_ini=False)
    b.cilindro(pl.p(uc, vc - 0.18, d), pl.u, 0.05, 0.2, "laton", lados=6, giro=0)
    b.cilindro(pl.p(uc - 0.1, vc - 0.18, d), pl.u, 0.06, 0.02, "laton", lados=6)
    b.tubo([pl.p(uc - 0.1, vc - 0.18, d), pl.p(uc - 0.22, vc - 0.18, d), pl.p(uc - 0.22, vc + 0.2, d),
            pl.p(uc - 0.22, vc + 0.2, PANEL + 0.02)], 0.035, "acero", lados=6, radio_curva=0.06, pasos_curva=2,
           tapa_fin=False)
    caja_esfera = pl.p(uc, vc + 0.02, d)
    b.cilindro(caja_esfera - pl.n * 0.08, pl.n, 0.15, 0.13, "laton", lados=10, tapa_ini=False, tapa_fin=False)
    b.revolucion([(0.15, 0.0), (0.13, 0.01), (0.13, 0.0)], caja_esfera + pl.n * 0.05, 10, "laton", eje=pl.n,
                 tapa_ini=False, tapa_fin=False)
    b.cilindro(caja_esfera + pl.n * 0.04, pl.n, 0.13, 0.008, "papel", lados=10, tapa_ini=False)
    # Tapa abatible de la esfera (abierta, hacia arriba).
    b.revolucion([(0.15, 0.0), (0.15, 0.02), (0.0, 0.03)], caja_esfera + pl.n * 0.05 + Vector((0, 0, 0.15)), 8,
                 "laton", eje=(0, 0, 1), escala=(0.25, 1.0))
    # Agujas y números de la esfera (malla alta).
    for k in range(10):
        ang = math.tau * k / 10
        agua.alta.caja(caja_esfera + pl.n * 0.05 + pl.u * math.cos(ang) * 0.1 + pl.v * math.sin(ang) * 0.1,
                       (0.01, 0.004, 0.01), "negro_mate")
    agua.alta.caja(caja_esfera + pl.n * 0.052 + pl.u * 0.03 + pl.v * 0.02, (0.006, 0.07, 0.003), "pintura_roja",
                   giro=pl.giro @ rot("Y", 50))
    # Llave de paso con maneta azul.
    b.cilindro(pl.p(uc + 0.1, 0.95, d), (0, 0, 1), 0.05, 0.12, "laton", lados=6)
    b.caja(pl.p(uc + 0.1, 1.04, d + 0.05), (0.03, 0.18, 0.025), "pintura_gris", giro=pl.giro)
    pant = Pieza("medidor_agua_pantalla_neon", peso_uv=0.5)
    caja_plano(pant.baja, pl, uc - 0.07, uc + 0.07, vc + 0.04, vc + 0.1, 0.235, 0.242, "neon", sin=("+y",))
    piezas += [agua, pant]
    return piezas


GRIFO = (-1.35, 1.95)   # muro derecho (u, v)


def grifo_manguera():
    """Grifo de pared y manguera verde enrollada en su soporte, con el tramo que baja al grifo."""
    pl = DER
    u, v = GRIFO
    g = Pieza("grifo_pared", peso_uv=2.0)
    b = g.baja
    caja_plano(b, pl, u - 0.09, u + 0.09, v - 0.09, v + 0.09, PANEL, PANEL + 0.02, "laton", sin=("+y",))
    b.cilindro(pl.p(u, v, PANEL + 0.02), pl.n, 0.04, 0.1, "laton", lados=8, tapa_ini=False)
    b.tubo([pl.p(u, v, PANEL + 0.1), pl.p(u, v, PANEL + 0.16), pl.p(u, v - 0.1, PANEL + 0.18)], 0.035, "laton",
           lados=6, radio_curva=0.05, pasos_curva=2, tapa_ini=False)
    b.cilindro(pl.p(u, v + 0.03, PANEL + 0.12), (0, 0, 1), 0.015, 0.06, "laton", lados=4)
    b.revolucion([(0.05, 0.0), (0.06, 0.012), (0.0, 0.02)], pl.p(u, v + 0.09, PANEL + 0.12), 6, "pintura_roja")
    for uu in (u - 0.06, u + 0.06):
        tornillo(g, pl.p(uu, v - 0.06, PANEL + 0.02), pl.n, 0.012, "laton", en_baja=False)
    # Soporte de la manguera: placa, brazo en U y tope.
    sv = v + 1.0
    s = Pieza("soporte_manguera", peso_uv=1.6)
    sb = s.baja
    caja_plano(sb, pl, u - 0.12, u + 0.12, sv - 0.1, sv + 0.18, PANEL, PANEL + 0.025, "pintura_verde",
               sin=("+y",))
    sb.cilindro(pl.p(u, sv, PANEL + 0.025), pl.n, 0.06, 0.32, "pintura_verde", lados=8, tapa_ini=False)
    sb.revolucion([(0.06, 0.0), (0.06, 0.02), (0.14, 0.04), (0.14, 0.06), (0.0, 0.06)], pl.p(u, sv, PANEL + 0.345),
                  8, "pintura_verde", eje=pl.n, tapa_ini=False)
    for vv in (sv - 0.06, sv + 0.13):
        tornillo(s, pl.p(u, vv, PANEL + 0.025), pl.n, 0.014, "acero")
    # Manguera enrollada: dos capas de espiras alrededor del brazo.
    m = Pieza("manguera_enrollada", peso_uv=1.0)
    rh = 0.034
    pts = []
    vueltas = 4
    pasos = 8
    for k in range(vueltas * pasos + 1):
        f = k / (vueltas * pasos)
        ang = math.tau * f * vueltas + 0.5
        capa = 0 if k < 2 * pasos else 1
        r = 0.1 + rh + capa * 2 * rh * 0.95
        dd = PANEL + 0.06 + rh + (f * vueltas % 3) * 2 * rh * 0.95 if capa == 0 else \
            PANEL + 0.06 + rh + (2 - ((f * vueltas - 3) % 2) * 1.0) * 2 * rh * 0.95
        r += 0.008 * math.sin(k * 1.7)
        pts.append(pl.p(u + math.cos(ang) * r, sv + math.sin(ang) * r * 1.05 - 0.02, dd))
    # Tramo que cuelga hasta el grifo.
    ult = pts[-1]
    pts += [ult + Vector((0.05, 0, -0.25)), pl.p(u + 0.05, v + 0.25, PANEL + 0.25), pl.p(u, v - 0.12, PANEL + 0.2)]
    m.baja.tubo(pts, rh, "manguera", lados=4)
    return [g, s, m]


# ======================================================================================================
# Entorno: botas, gato, camino
# ======================================================================================================


def _bota_agua(c, alta, origen, rumbo, inclinada=0.0):
    """Bota de goma alta: suela con tacos, pie redondeado y caña con la boca abierta."""
    ini = set(c.bm.verts)
    ini_a = set(alta.bm.verts)
    planta = [(-0.16, 0.0), (-0.15, 0.06), (-0.1, 0.075), (0.05, 0.075), (0.18, 0.085), (0.27, 0.06), (0.3, 0.0),
              (0.27, -0.06), (0.18, -0.085), (0.05, -0.075), (-0.1, -0.075), (-0.15, -0.06)]
    c.placa(planta, Vector((0, 0, 0)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.05, "goma_suela",
            atras=True)
    secs = []
    for x, ancho, alto in ((0.29, 0.04, 0.05), (0.25, 0.075, 0.1), (0.15, 0.085, 0.15), (0.03, 0.08, 0.22)):
        secs.append([Vector((x, math.cos(math.pi * i / 6) * ancho, 0.045 + math.sin(math.pi * i / 6) * alto))
                     for i in range(7)])
    vs = c.loft(secs, "goma_verde", cerrado=False, tapa_ini=False, tapa_fin=False)
    tapa = c.cara(list(reversed(vs[0])), "goma_verde")
    c.recalcular(c.ultimas + [tapa])
    cx = -0.04
    anillos = []
    for esc, z in ((1.0, 0.045), (1.0, 0.25), (0.93, 0.5), (0.98, 0.78), (1.03, 0.82)):
        anillos.append([Vector((cx + math.cos(a_) * 0.1 * esc, math.sin(a_) * 0.085 * esc, z))
                        for a_ in [math.tau * i / 7 for i in range(7)]])
    interior = [[Vector((cx + math.cos(a_) * 0.085, math.sin(a_) * 0.07, z)) for a_ in [math.tau * i / 7 for i in range(7)]]
                for z in (0.82, 0.6)]
    c.loft(anillos + interior, "goma_verde", tapa_ini=False, tapa_fin=True,
           mats_tramo=["goma_verde"] * 4 + ["negro_mate", "negro_mate"], mat_fin="negro_mate")
    # Ribete de la boca y tacos de la suela (malla alta).
    alta.tubo([Vector((cx + math.cos(a_) * 0.104, math.sin(a_) * 0.089, 0.8)) for a_ in
               [math.tau * i / 16 for i in range(17)]], 0.01, "goma_verde", lados=4)
    for k in range(6):
        alta.caja(Vector((-0.12 + k * 0.075, 0, 0.004)), (0.03, 0.14, 0.012), "goma_suela")
    nuevos = [v for v in c.bm.verts if v not in ini]
    nuevos_a = [v for v in alta.bm.verts if v not in ini_a]
    M = Matrix.Translation(origen) @ Matrix.Rotation(math.radians(rumbo), 4, "Z") @ \
        Matrix.Rotation(math.radians(inclinada), 4, "X")
    c.transformar(nuevos, M)
    alta.transformar(nuevos_a, M)
    dz = origen.z - min(v.co.z for v in nuevos)
    c.transformar(nuevos, Matrix.Translation((0, 0, dz)))
    alta.transformar(nuevos_a, Matrix.Translation((0, 0, dz)))


def botas_agua():
    p = Pieza("botas_agua", peso_uv=1.8)
    _bota_agua(p.baja, p.alta, Vector((-0.15, -4.42, BASE_Z)), -80)
    # La otra, apoyada contra la pared y un poco caída.
    _bota_agua(p.baja, p.alta, Vector((-0.75, -4.4, BASE_Z)), -100, inclinada=-12)
    return p


GATO = Vector((2.25, -5.38, 0.27))


def gato():
    """
    Gato atigrado dormido en el escalón, hecho un ovillo: lomo curvo hacia la puerta, cabeza apoyada sobre las
    patas mirando a la calle, orejas de punta y la cola rodeándolo por delante. Se modela en local y se coloca.
    """
    p = Pieza("gato", peso_uv=2.4)
    b, a = p.baja, p.alta
    ini, ini_a = set(b.bm.verts), set(a.bm.verts)
    V = Vector
    # Cuerpo: lomo en C (se abre hacia -y, hacia donde mira la cara).
    lomo = [V((0.26, -0.04, 0)), V((0.2, 0.05, 0)), V((0.08, 0.1, 0)), V((-0.06, 0.095, 0)), V((-0.17, 0.04, 0)),
            V((-0.21, -0.02, 0))]
    radios = [0.09, 0.125, 0.14, 0.13, 0.11, 0.085]
    cam = [q + V((0, 0, r * 0.82)) for q, r in zip(lomo, radios)]
    b.tubo(cam, 0.12, "pelaje", lados=8, radios=radios)
    for v in [v for v in b.bm.verts if v not in ini]:
        v.co.z = max(v.co.z, 0.004)   # se desparrama sobre la piedra
    # Cabeza: ovalada, apoyada en las patas delanteras.
    hc = V((-0.25, -0.08, 0.115))
    mira = V((0.3, -1.0, -0.3)).normalized()
    b.revolucion([(0.0, -0.1), (0.08, -0.07), (0.1, 0.0), (0.085, 0.06), (0.045, 0.095), (0.0, 0.105)], hc, 8,
                 "pelaje", eje=mira, escala=(1.0, 0.86))
    lado = mira.cross(V((0, 0, 1))).normalized()
    # Orejas: pirámides triangulares de punta, con el interior rosado (malla alta).
    for sg in (-1, 1):
        o = hc + lado * sg * 0.055 + V((0, 0, 0.07)) - mira * 0.025
        punta = o + V((0, 0, 0.085)) + lado * sg * 0.025 - mira * 0.02
        tri = [o - mira * 0.04, o + lado * sg * 0.04, o + mira * 0.025, o - lado * sg * 0.025]
        b.loft([tri, [punta]], "pelaje", suave=False)
        a.loft([[q.lerp(punta, 0.2) + mira * 0.006 for q in (tri[3], tri[2], tri[1])], [punta.lerp(o, 0.2) + mira * 0.012]],
               "nariz_gato", cerrado=False, suave=False)
    # Ojos cerrados, nariz y bigotes (malla alta).
    a.cupula(hc + mira * 0.1 + V((0, 0, -0.012)), mira, 0.013, "nariz_gato", alto=0.006, lados=6)
    for sg in (-1, 1):
        q = hc + mira * 0.083 + lado * sg * 0.042 + V((0, 0, 0.03))
        a.tubo([q - lado * 0.02, q + V((0, 0, -0.007)), q + lado * 0.02], 0.004, "negro_mate", lados=3)
        for k in range(3):
            r0 = hc + mira * 0.095 + lado * sg * 0.025 + V((0, 0, -0.02))
            a.tubo([r0, r0 + lado * sg * 0.12 + V((0, 0, 0.012 * (k - 1))) + mira * 0.02], 0.002, "papel", lados=3)
    # Patas delanteras recogidas bajo la barbilla.
    for sg in (-1, 1):
        q = hc + V((0, 0, -0.085)) + lado * sg * 0.045 + mira * 0.04
        b.revolucion([(0.0, -0.035), (0.034, -0.015), (0.034, 0.05), (0.0, 0.07)], q, 6, "pelaje", eje=mira)
    # Cola: sale de las ancas, rodea al gato por delante y acaba junto al hocico.
    cola = [V((0.3, 0.02, 0.04)), V((0.36, -0.1, 0.04)), V((0.25, -0.22, 0.04)), V((0.05, -0.25, 0.04)),
            V((-0.13, -0.21, 0.045)), V((-0.21, -0.18, 0.05))]
    b.tubo(cola, 0.04, "pelaje", lados=5, radios=[0.045, 0.043, 0.041, 0.039, 0.035, 0.022],
           radio_curva=0.05, pasos_curva=1)
    nuevos = [v for v in b.bm.verts if v not in ini]
    nuevos_a = [v for v in a.bm.verts if v not in ini_a]
    M = Matrix.Translation(GATO) @ Matrix.Rotation(math.radians(-12), 4, "Z")
    b.transformar(nuevos, M)
    a.transformar(nuevos_a, M)
    return p


def camino():
    """Seis piedras planas e irregulares embutidas en el suelo, de la puerta a la calle."""
    p = Pieza("camino_piedras", peso_uv=1.2)
    rnd = random.Random(77)
    centros = [(1.6, -6.35, 0.0), (1.15, -7.15, 0.4), (1.7, -7.95, -0.3), (1.25, -8.8, 0.2), (1.85, -9.6, -0.5),
               (1.4, -10.4, 0.6)]
    for cx, cy, giro in centros:
        n = 9
        rx, ry = rnd.uniform(0.38, 0.46), rnd.uniform(0.3, 0.36)
        pts = []
        for k in range(n):
            ang = math.tau * k / n + giro
            r = 1 + rnd.uniform(-0.12, 0.1)
            pts.append((cx + math.cos(ang) * rx * r, cy + math.sin(ang) * ry * r))
        # Hundidas: la cara de arriba apenas asoma (0,04) y el canto se mete en la tierra.
        p.baja.placa(pts, Vector((0, 0, -0.08)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)),
                     0.08 + rnd.uniform(0.02, 0.05), "losa", suave_canto=False)
        # Tierra y hierbecillas alrededor (malla alta): se hornean en el canto.
        for _ in range(6):
            ang = rnd.uniform(0, math.tau)
            q = Vector((cx + math.cos(ang) * rx * 1.02, cy + math.sin(ang) * ry * 1.02, 0.0))
            hoja3d(p.alta, q, ang, 0.08, 0.02, -0.02, "hoja", subida=0.04, secciones=2)
    return p


# ======================================================================================================
# Invernadero: base, armazón y cristal
# ======================================================================================================


def invernadero_base():
    p = Pieza("invernadero_base", peso_uv=0.7)
    b = p.baja
    m = 0.12
    x0, x1, y0, y1 = GX0 - m, GX1 + m, GY0 - m, GY1 + m
    # Murete de hormigón (anillo) y suelo de grava dentro.
    for (a0, a1, c0, c1) in ((x0, x1, y0, GY0 + m), (x0, x1, GY1 - m, y1), (x0, GX0 + m, GY0 + m, GY1 - m),
                             (GX1 - m, x1, GY0 + m, GY1 - m)):
        b.caja_de((a0, c0, 0), (a1, c1, GZ0), "hormigon", sin=("-z",))
    b.caja_de((GX0 + m, GY0 + m, 0), (GX1 - m, GY1 - m, GZ0 - 0.04), "grava", sin=("-z", "-x", "+x", "-y", "+y"))
    # Losa del pasillo, entre el murete y la base de la casa.
    b.caja_de((GX1 + m, -1.12, 0), (BASE["x0"], 1.12, BASE_Z), "hormigon", sin=("-z", "+x"))
    # Pasos de losa en el pasillo central del invernadero (malla baja).
    for k in range(5):
        y = -3.0 + k * 1.45
        b.caja_de((-8.35, y - 0.3, GZ0 - 0.04), (-7.3, y + 0.3, GZ0 - 0.005), "losa", sin=("-z",))
    return p


def _plano_lado(x, signo):
    """Plano de un lado largo del invernadero (u = y, v = z, n = ±x)."""
    return Vector((x, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((signo, 0, 0))


def invernadero_marco():
    """Armazón de tubo cuadrado de aluminio: pórticos, travesaños, cabios, correas, escuadras y tapajuntas."""
    p = Pieza("invernadero_marco", peso_uv=1.5)
    b, a = p.baja, p.alta
    h = S / 2
    # ---- lados largos (x = GX0 y x = GX1) ---------------------------------------------------------------------
    for x_out, sg in ((GX0, -1), (GX1, 1)):
        xm = x_out - sg * h
        for y in YP:
            yc = max(min(y, GY1 - h), GY0 + h)
            b.caja((xm, yc, (GZ0 + GE) / 2), (S, S, GE - GZ0), "aluminio_perfil", sin=("-z",))
        # Durmiente, travesaño y viga del alero.
        tramos = [(GY0 + S, GY1 - S)]
        if sg > 0:
            tramos = [(GY0 + S, -0.8 - h), (0.8 + h, GY1 - S)]
        for z0, z1 in ((GZ0, GZ0 + S), (Z_MED - h, Z_MED + h)):
            for ya, yb in tramos:
                b.caja_de((xm - h, ya, z0), (xm + h, yb, z1), "aluminio_perfil", sin=("-y", "+y"))
        b.caja_de((xm - h, GY0 + S, GE - 0.1), (xm + h, GY1 - S, GE), "aluminio_perfil", sin=("-y", "+y"))
        if sg > 0:
            # Dintel de la puerta y umbral.
            b.caja_de((xm - h, -0.8 + h, PUERTA_I["z1"] + 0.02), (xm + h, 0.8 - h, PUERTA_I["z1"] + 0.02 + S),
                      "aluminio_perfil", sin=("-y", "+y"))
            b.caja_de((xm - h, -0.8 + h, GZ0), (xm + h + 0.04, 0.8 - h, GZ0 + 0.03), "acero", sin=("-y", "+y", "-z"))
    # ---- hastiales (y = GY0 y y = GY1) ------------------------------------------------------------------------
    for y_out, sg in ((GY0, -1), (GY1, 1)):
        ym = y_out - sg * h
        for x in XG[1:-1]:
            b.caja((x, ym, (GZ0 + GE) / 2), (S, S, GE - GZ0 - 0.1), "aluminio_perfil", sin=("-z", "+z"))
            zt = z_invernadero(x)
            b.caja((x, ym, (GE + zt) / 2), (S, S, zt - GE), "aluminio_perfil", sin=("-z", "+z"))
        for z0, z1 in ((GZ0, GZ0 + S), (Z_MED - h, Z_MED + h), (GE - 0.1, GE)):
            b.caja_de((GX0 + S, ym - h, z0), (GX1 - S, ym + h, z1), "aluminio_perfil", sin=("-x", "+x"))
    # ---- tejado: cabios, cumbrera, correas -------------------------------------------------------------------
    largo_f = math.hypot(GXC - GX0, GR - GE)
    nrm = {s: Vector((s * (GR - GE), 0, GXC - GX0)).normalized() for s in (-1, 1)}
    for y in YP:
        yc = max(min(y, GY1 - h), GY0 + h)
        for s in (-1, 1):
            xe = GX0 if s < 0 else GX1
            pa = Vector((xe, yc, GE)) + nrm[s] * h
            pb = Vector((GXC, yc, GR)) + nrm[s] * h
            barra(b, pa, pb, S, S, "aluminio_perfil", arriba=nrm[s])
    b.caja_de((GXC - 0.06, GY0, GR - 0.02), (GXC + 0.06, GY1, GR + 0.1), "aluminio_perfil")
    for s in (-1, 1):
        xe = GX0 if s < 0 else GX1
        xm_ = (xe + GXC) / 2
        zm_ = (GE + GR) / 2
        c0 = Vector((xm_, 0, zm_)) + nrm[s] * h * 0.4
        g = rot("Y", s * -math.degrees(math.atan((GR - GE) / (GXC - GX0))))
        b.caja(c0, (0.06, GY1 - GY0 - 0.16, 0.05), "aluminio_perfil", giro=g, sin=("-y", "+y"))
    # ---- escuadras atornilladas en los hastiales (se ven por fuera) ---------------------------------------------
    rnd = random.Random(5)
    for y_out, sg in ((GY0, -1), (GY1, 1)):
        yp = y_out + sg * 0.001
        u, v, n = Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, sg, 0))
        delante = sg < 0

        def escuadra(pts, tornillos):
            # Delante la escuadra es malla baja; detrás (casi no se ve) solo se hornea. Los tornillos, con
            # arandela, van siempre en la alta: el marco tiene mucha resolución en el atlas y se leen bien.
            (b if delante else a).placa(pts, Vector((0, yp, 0)), u, v, n, 0.014, "aluminio_perfil", atras=False)
            for tx, tz in tornillos:
                q = Vector((tx, yp + sg * 0.014, tz))
                a.cupula(q, n, 0.026, "acero", alto=0.004, lados=10)
                tornillo(p, q + n * 0.003, n, 0.016, "acero", en_baja=False)
        # Aleros: escuadra triangular entre montante, viga y cabio.
        for xe, s in ((GX0, 1), (GX1, -1)):
            pts = [(xe, GE - 0.45), (xe + s * 0.07, GE - 0.45), (xe + s * 0.42, GE - 0.02), (xe + s * 0.42, GE + 0.08),
                   (xe, GE + 0.08)]
            if s < 0:
                pts = list(reversed(pts))
            escuadra(pts, [(xe + s * 0.04, GE - 0.32), (xe + s * 0.04, GE - 0.1), (xe + s * 0.25, GE - 0.05)])
        # Cumbrera.
        escuadra([(GXC - 0.35, GR - 0.12), (GXC + 0.35, GR - 0.12), (GXC + 0.05, GR - 0.42), (GXC - 0.05, GR - 0.42)],
                 [(GXC - 0.2, GR - 0.17), (GXC + 0.2, GR - 0.17), (GXC, GR - 0.33)])
        # Travesaño intermedio con cada montante: placa cuadrada con dos tornillos.
        for x in XG[1:-1]:
            escuadra(rect(x - 0.1, x + 0.1, Z_MED - 0.1, Z_MED + 0.1), [(x - 0.05, Z_MED + 0.05), (x + 0.05, Z_MED - 0.05)])
    # Escuadras de los lados largos (solo en la malla alta: se hornean).
    for x_out, sg in ((GX0, -1), (GX1, 1)):
        for y in YP[1:-1]:
            for z in (Z_MED, GE - 0.05):
                q = Vector((x_out + sg * 0.002, y, z))
                a.caja(q, (0.004, 0.18, 0.18), "aluminio_perfil")
                for dy, dz in ((-0.05, 0.05), (0.05, -0.05)):
                    a.cupula(q + Vector((sg * 0.002, dy, dz)), (sg, 0, 0), 0.016, "acero", alto=0.01, lados=6)
    # ---- tapajuntas: perfiles que pisan el cristal por fuera en cada junta ---------------------------------------
    t0 = VID
    for x_out, sg in ((GX0, -1), (GX1, 1)):
        xc = x_out + sg * (t0 + 0.008)
        for y in YP[1:-1]:
            if sg > 0 and abs(y) < 1.0:
                continue
            b.caja((xc, y, (GZ0 + GE) / 2), (0.016, 0.05, GE - GZ0), "aluminio_perfil",
                   sin=("-z", "+z", "+x" if sg < 0 else "-x"))
        b.caja((xc, 0, Z_MED), (0.016, GY1 - GY0, 0.05), "aluminio_perfil", sin=("-y", "+y", "+x" if sg < 0 else "-x"))
    for y_out, sg in ((GY0, -1), (GY1, 1)):
        yc = y_out + sg * (t0 + 0.008)
        for x in XG[1:-1]:
            zt = z_invernadero(x)
            b.caja((x, yc, (GZ0 + zt) / 2), (0.05, 0.016, zt - GZ0), "aluminio_perfil",
                   sin=("-z", "+z", "+y" if sg < 0 else "-y"))
        for z in (Z_MED, GE - 0.05):
            b.caja((GXC, yc, z), (GX1 - GX0, 0.016, 0.05), "aluminio_perfil", sin=("-x", "+x", "+y" if sg < 0 else "-y"))
    # Tapajuntas del tejado (a lo largo de cada cabio) y caballete de la cumbrera.
    for y in YP:
        for s in (-1, 1):
            xe = GX0 if s < 0 else GX1
            pa = Vector((xe + (-0.06 if s < 0 else 0.06), y, GE - 0.03)) + nrm[s] * (S + t0 + 0.008)
            pb = Vector((GXC, y, GR)) + nrm[s] * (S + t0 + 0.008)
            barra(b, pa, pb, 0.05, 0.016, "aluminio_perfil", arriba=nrm[s], sin=("-z", "+z", "-y"))
    for s in (-1, 1):
        cx = GXC + s * 0.1
        g = rot("Y", s * -math.degrees(math.atan((GR - GE) / (GXC - GX0))))
        b.caja((cx, 0, GR + S + 0.06 - 0.03), (0.24, GY1 - GY0 + 0.1, 0.02), "aluminio_perfil", giro=g)
    p.extra["largo_faldon"] = largo_f
    return p


def _pano_tejado(c, s, y0, y1, f0, f1, mat="vidrio_invernadero", d=None):
    """Paño de cristal del faldón s (−1 izquierdo, +1 derecho) entre y0-y1 y las fracciones f0-f1 del faldón."""
    xe = GX0 if s < 0 else GX1
    pe = Vector((xe + (-0.07 if s < 0 else 0.07), 0, GE - 0.035))
    pr = Vector((GXC, 0, GR))
    nrm = Vector((s * (GR - GE), 0, GXC - GX0)).normalized()
    dirv = (pr - pe)
    largo = dirv.length
    dirv.normalize()
    off = S + 0.002 if d is None else d
    o = pe + nrm * off
    pts = [(y0, f0 * largo), (y1, f0 * largo), (y1, f1 * largo), (y0, f1 * largo)]
    return c.placa(pts, o, Vector((0, 1, 0)), dirv, nrm, VID, mat, atras=True, oculta_atras=False)


def invernadero_vidrio():
    """
    Paños de cristal (0,03 de grosor) por fuera del armazón. Cada fila es un paño seguido: las juntas quedan bajo
    los tapajuntas de aluminio, así que se ven igual que paños sueltos y gastan muchos menos triángulos.
    """
    p = Pieza("invernadero_vidrio", peso_uv=1.1)
    b = p.baja
    g = 0.012
    vid = "vidrio_invernadero"
    filas = [(GZ0 + 0.02, Z_MED), (Z_MED, GE)]
    for x_out, sg in ((GX0, -1), (GX1, 1)):
        o, u, v, n = _plano_lado(x_out, sg)
        trozos = [(GY0, GY1)] if sg < 0 else [(GY0, -0.8), (0.8, GY1)]
        for z0, z1 in filas:
            for y0, y1 in trozos:
                b.placa(rect(y0 + g, y1 - g, z0 + g, z1 - g), o, u, v, n, VID, vid, atras=True, oculta_atras=False)
        if sg > 0:  # montante encima de la puerta
            b.placa(rect(-0.8 + g, 0.8 - g, PUERTA_I["z1"] + 0.1, GE - g), o, u, v, n, VID, vid, atras=True,
                    oculta_atras=False)
    k = (GR - GE) / (GXC - GX0)
    for y_out, sg in ((GY0, -1), (GY1, 1)):
        o = Vector((0, y_out, 0))
        u, v, n = Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, sg, 0))
        for z0, z1 in filas + [(GE, GR + 0.1)]:
            poly = rect(GX0 + g, GX1 - g, z0 + g, z1 - g)
            poly = cp.recortar(poly, -k, 1, GE - k * GX0 + 0.05)     # faldón izquierdo
            poly = cp.recortar(poly, k, 1, GE + k * GX1 + 0.05)      # faldón derecho
            b.placa(poly, o, u, v, n, VID, vid, atras=True, oculta_atras=False)
    for s in (-1, 1):
        _pano_tejado(b, s, GY0 + g, GY1 - g, 0.0, 0.5 - 0.005)
        if s > 0:
            _pano_tejado(b, s, GY0 + g, GY1 - g, 0.5 + 0.005, 1.0)
        else:
            cortes = sorted([GY0, GY1] + [y for par in VENTILAS.values() for y in par])
            for a0, a1 in zip(cortes[0::2], cortes[1::2]):
                _pano_tejado(b, s, a0 + g, a1 - g, 0.5 + 0.005, 1.0)
    return p


def puerta_invernadero():
    """Puerta de cristal con marco de aluminio, junta de goma y tirador. Pivote en las bisagras (y = -0,72)."""
    D = PUERTA_I
    x0, x1 = GX1, GX1 + 0.06
    piv = (x1 + 0.02, D["y0"] - 0.03, D["z0"])
    p = Pieza("puerta_invernadero", pivote=piv, peso_uv=1.6)
    b, a = p.baja, p.alta
    t = 0.06
    xc = (x0 + x1) / 2
    for (ya, yb, za, zb) in ((D["y0"], D["y0"] + t, D["z0"], D["z1"]), (D["y1"] - t, D["y1"], D["z0"], D["z1"]),
                             (D["y0"] + t, D["y1"] - t, D["z0"], D["z0"] + 0.12),
                             (D["y0"] + t, D["y1"] - t, D["z1"] - t, D["z1"]),
                             (D["y0"] + t, D["y1"] - t, 1.62, 1.62 + t)):
        b.caja_de((x0, ya, za), (x1, yb, zb), "aluminio_perfil")
    # Junta de goma: labio negro alrededor de la hoja (cierra contra los montantes y el dintel).
    for (ya, yb, za, zb) in ((D["y0"] - 0.025, D["y0"], D["z0"], D["z1"] + 0.025),
                             (D["y1"], D["y1"] + 0.025, D["z0"], D["z1"] + 0.025),
                             (D["y0"], D["y1"], D["z1"], D["z1"] + 0.025),
                             (D["y0"] - 0.025, D["y1"] + 0.025, D["z0"] - 0.02, D["z0"])):
        b.caja_de((x0 + 0.012, ya, za), (x1 - 0.012, yb, zb), "goma")
    # Junquillos de goma que sujetan el cristal (malla alta).
    for z in (D["z0"] + 0.12, 1.62, 1.62 + t, D["z1"] - t):
        a.caja_de((x1 - 0.004, D["y0"] + t, z - 0.008), (x1 + 0.004, D["y1"] - t, z + 0.008), "goma")
    # Tirador: barra en D por fuera (hacia el pasillo) y pomo por dentro.
    yt = D["y1"] - 0.15
    b.tubo([(x1, yt, 1.3), (x1 + 0.09, yt, 1.33), (x1 + 0.09, yt, 1.87), (x1, yt, 1.9)], 0.018, "acero_pulido",
           lados=6, radio_curva=0.04, pasos_curva=2)
    b.cilindro((x0, yt, 1.6), (-1, 0, 0), 0.03, 0.06, "acero_pulido", lados=6)
    # Bisagras (dos) en el canto de y0.
    for z in (D["z0"] + 0.35, D["z1"] - 0.35):
        b.cilindro((piv[0], piv[1], z - 0.09), (0, 0, 1), 0.025, 0.18, "acero", lados=6)
        b.caja_de((x1, piv[1] - 0.01, z - 0.07), (x1 + 0.02, D["y0"] + 0.12, z + 0.07), "acero", sin=("-x",))
        for dz in (-0.04, 0.04):
            tornillo(p, (x1 + 0.02, D["y0"] + 0.06, z + dz), (1, 0, 0), 0.012, "acero", en_baja=False)
    # Pegatina de «cierre la puerta» (malla alta).
    a.caja_de((x1, -0.15, 1.95), (x1 + 0.003, 0.15, 2.07), "papel")
    v = Pieza("puerta_invernadero_vidrio", pivote=piv, peso_uv=1.1)
    for za, zb in ((D["z0"] + 0.12, 1.62), (1.62 + t, D["z1"] - t)):
        v.baja.caja_de((xc - VID / 2, D["y0"] + t - 0.01, za - 0.01), (xc + VID / 2, D["y1"] - t + 0.01, zb + 0.01),
                       "vidrio_invernadero")
    return [p, v]


def ventila(nombre, y0, y1, angulo):
    """Ventila del tejado: marco de aluminio con cristal, bisagras arriba (cumbrera) y brazo de apertura."""
    s = -1
    nrm = Vector((s * (GR - GE), 0, GXC - GX0)).normalized()
    pe = Vector((GX0 - 0.07, 0, GE - 0.035))
    pr = Vector((GXC, 0, GR))
    dirv = (pr - pe)
    largo = dirv.length
    dirv.normalize()
    f0, f1 = 0.5 + 0.005, 0.97
    off = S + 0.002 + VID + 0.004
    bis = pe + dirv * largo * f1 + nrm * (off + 0.03)
    piv = (bis.x, (y0 + y1) / 2, bis.z)
    p = Pieza(nombre, pivote=piv, peso_uv=1.6)
    v = Pieza(nombre + "_vidrio", pivote=piv, peso_uv=1.1)
    b, a = p.baja, p.alta
    o = pe + nrm * off
    u = Vector((0, 1, 0))
    t = 0.05
    g = 0.015
    for (ua, ub, fa, fb) in ((y0 + g, y0 + g + t, f0, f1), (y1 - g - t, y1 - g, f0, f1),
                             (y0 + g + t, y1 - g - t, f0, f0 + t / largo), (y0 + g + t, y1 - g - t, f1 - t / largo, f1)):
        pts = [(ua, fa * largo), (ub, fa * largo), (ub, fb * largo), (ua, fb * largo)]
        b.placa(pts, o, u, dirv, nrm, 0.045, "aluminio_perfil", atras=True)
    # Goma alrededor del cristal (malla alta) y el cristal.
    pts = [(y0 + g + t - 0.01, f0 * largo + t - 0.01), (y1 - g - t + 0.01, f0 * largo + t - 0.01),
           (y1 - g - t + 0.01, f1 * largo - t + 0.01), (y0 + g + t - 0.01, f1 * largo - t + 0.01)]
    v.baja.placa(pts, o + nrm * 0.008, u, dirv, nrm, VID, "vidrio_invernadero", atras=True, oculta_atras=False)
    a.tubo([o + nrm * 0.045 + u * q[0] + dirv * q[1] for q in pts + [pts[0]]], 0.008, "goma", lados=4)
    # Bisagras: dos piezas en el borde de arriba.
    for yy in (y0 + 0.3, y1 - 0.3):
        b.cilindro((bis.x, yy - 0.1, bis.z), (0, 1, 0), 0.025, 0.2, "acero", lados=6)
        c0 = o + u * yy + dirv * (f1 * largo - 0.08)
        b.caja(c0 + nrm * 0.05, (0.2, 0.08, 0.012), "acero", giro=Matrix((dirv, u, nrm)).transposed())
    # Brazo de apertura: barra perforada del borde de abajo de la ventila hasta la correa.
    abajo = o + u * ((y0 + y1) / 2) + dirv * (f0 * largo + 0.03) + nrm * 0.045
    p.extra["brazo_ventila"] = list(abajo)
    # Gira la ventila a su posición (abierta: el borde de abajo sube, girando sobre las bisagras).
    giro = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(angulo), 4, "Y") @ Matrix.Translation(-Vector(piv))
    for c in (b, a, v.baja, v.alta):
        c.transformar(c.bm.verts, giro)
    abajo_g = giro @ abajo
    # El brazo se ancla en el cabio de abajo (fijo) y sube hasta la ventila: va en la pieza de la ventila.
    ancla = o + u * ((y0 + y1) / 2 + 0.05) + dirv * (f0 * largo - 0.25) + nrm * 0.0
    barra(b, ancla, abajo_g, 0.035, 0.012, "acero", arriba=u)
    b.cilindro(ancla - u * 0.03, u, 0.02, 0.06, "acero", lados=6)
    b.cilindro(abajo_g - u * 0.03, u, 0.02, 0.06, "acero", lados=6)
    d = abajo_g - ancla
    for k in range(1, 6):
        a.cupula(ancla + d * (k / 6) + u * 0.006, u, 0.009, "negro_mate", alto=0.003, lados=6)
    p.extra["angulo"] = angulo
    return [p, v]


def pasillo():
    """Pasillo cubierto de 1 stud entre la puerta lateral de la casa y la del invernadero: suelo, postes, cristal
    a los lados y tejadillo de chapa."""
    p = Pieza("pasillo", peso_uv=1.2)
    b, a = p.baja, p.alta
    xa, xb = GX1 + 0.02, -MX - PANEL - 0.005   # de la cara del invernadero a la de la casa
    ys = 1.0
    zt0, zt1 = 3.82, 4.08    # tejadillo: más bajo en el invernadero
    for sy in (-1, 1):
        y = sy * ys
        for x in (xa + 0.04, -5.25):
            b.caja((x, y, (BASE_Z + 3.78) / 2), (S, S, 3.78 - BASE_Z), "aluminio_perfil", sin=("-z",))
        for z in (BASE_Z + 0.04, 3.74):
            b.caja_de((xa + 0.08, y - 0.04, z - 0.04), (-5.29, y + 0.04, z + 0.04), "aluminio_perfil",
                      sin=("-x", "+x"))
    # Tejadillo de chapa galvanizada con nervios, sobre dos correas.
    k = (zt1 - zt0) / (xb - (xa - 0.12))
    for sy in (-1, 1):
        barra(b, (xa - 0.1, sy * (ys + 0.02), zt0 - 0.05), (xb, sy * (ys + 0.02), zt1 - 0.05), 0.06, 0.06,
              "aluminio_perfil")
    ancho = 2 * ys + 0.3
    nerv = 6
    pts = []
    for i in range(nerv * 2 + 1):
        y = -ancho / 2 + ancho * i / (nerv * 2)
        pts.append((y, 0.03 if i % 2 else 0.0))
    ar = [Vector((xa - 0.14, y, zt0 + hh)) for y, hh in pts]
    br = [Vector((xb, y, zt1 + hh)) for y, hh in pts]
    ar2 = [q - Vector((0, 0, CHAPA)) for q in reversed(ar)]
    br2 = [q - Vector((0, 0, CHAPA)) for q in reversed(br)]
    b.loft([ar + ar2, br + br2], "chapa_nueva", tapa_ini=True, tapa_fin=True, suave=False)
    b.recalcular(b.ultimas)
    # Babero contra la pared de la casa.
    b.caja_de((xb - 0.02, -ancho / 2, zt1 - 0.02), (xb, ancho / 2, zt1 + 0.25), "metal_oscuro", sin=("+x",))
    b.caja_de((xb - 0.2, -ancho / 2, zt1 + 0.02), (xb, ancho / 2, zt1 + 0.05), "metal_oscuro", sin=("+x",))
    for yy in (-0.8, 0.0, 0.8):
        tornillo(p, (xb - 0.02, yy, zt1 + 0.18), (-1, 0, 0), 0.016, "acero", en_baja=False)
    # Felpudo de fibra para no meter barro en casa (malla baja + ribete en la alta).
    b.caja_de((-5.95, -0.6, BASE_Z), (-5.38, 0.6, BASE_Z + 0.035), "fibra", sin=("-z",))
    vid = Pieza("pasillo_vidrio", peso_uv=1.1)
    for sy in (-1, 1):
        o = Vector((0, sy * (ys + 0.04), 0))
        vid.baja.placa(rect(xa + 0.08, -5.29, BASE_Z + 0.08, 3.7), o, Vector((1, 0, 0)), Vector((0, 0, 1)),
                       Vector((0, sy, 0)), VID, "vidrio_invernadero", atras=True, oculta_atras=False)
    p.extra["felpudo"] = [-5.66, 0.0, BASE_Z]
    return [p, vid]


# ======================================================================================================
# Invernadero: dentro
# ======================================================================================================

NIVELES = (0.98, 1.78, 2.58)       # cara de arriba de cada balda
UNIDADES = [  # (x0, x1, y0, y1, montantes en y)
    (GX0 + 0.14, GX0 + 1.14, -3.75, 3.75, (-3.75, 0.0, 3.75)),
    (GX1 - 1.14, GX1 - 0.14, -3.75, -1.05, (-3.75, -1.05)),
    (GX1 - 1.14, GX1 - 0.14, 1.05, 3.75, (1.05, 3.75)),
]


def estanterias():
    p = Pieza("invernadero_estanterias", peso_uv=1.0)
    b, a = p.baja, p.alta
    for x0, x1, y0, y1, montantes in UNIDADES:
        for y in montantes:
            yc = min(max(y, y0 + 0.025), y1 - 0.025)
            for x in (x0 + 0.025, x1 - 0.025):
                b.caja((x, yc, (GZ0 + 2.62) / 2), (0.05, 0.05, 2.62 - GZ0), "galvanizado", sin=("-z",))
        for z in NIVELES:
            # Balda de rejilla: bastidor de angular y varillas (las varillas en la alta).
            a.caja_de((x0, y0, z - 0.05), (x1, y0 + 0.04, z), "galvanizado")
            a.caja_de((x0, y1 - 0.04, z - 0.05), (x1, y1, z), "galvanizado")
            b.caja_de((x0, y0 + 0.04, z - 0.05), (x0 + 0.04, y1 - 0.04, z), "galvanizado", sin=("-y", "+y", "-z"))
            b.caja_de((x1 - 0.04, y0 + 0.04, z - 0.05), (x1, y1 - 0.04, z), "galvanizado", sin=("-y", "+y", "-z"))
            n = int((x1 - x0) / 0.1)
            for k in range(1, n):
                x = x0 + (x1 - x0) * k / n
                a.caja_de((x - 0.006, y0 + 0.04, z - 0.012), (x + 0.006, y1 - 0.04, z), "galvanizado")
    return p


def _fila(c, o, eje_l, eje_a, largo, ancho, alto, cabezas, mat, semilla, filas=2, z_soporte=None):
    """
    Superficie de plantas sobre la tierra de una bandeja: `filas` filas de `cabezas` matas, muestreada en los
    centros de las matas y en los huecos (pocos triángulos; las hojas sueltas van en la malla alta).
    """
    rnd = random.Random(semilla)
    nl = cabezas * 2
    na = filas * 2
    vs = {}
    for i in range(nl + 1):
        for j in range(na + 1):
            fl, fa = i / nl, j / na
            cima = (i % 2 == 1) and (j % 2 == 1)
            borde = i in (0, nl) or j in (0, na)
            h = alto * rnd.uniform(0.8, 1.15) if cima else (0.0 if borde else alto * rnd.uniform(0.35, 0.55))
            q = o + eje_l * (fl * largo) + eje_a * (fa * ancho) + Vector((0, 0, h))
            if cima:
                q += (eje_l * rnd.uniform(-0.03, 0.03) + eje_a * rnd.uniform(-0.03, 0.03))
            vs[i, j] = c.v(q)
    caras = []
    for i in range(nl):
        for j in range(na):
            f = c.cara([vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]], mat, suave=True)
            caras.append(f)
    for f in caras:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    centros = []
    for i in range(1, nl, 2):
        for j in range(1, na, 2):
            centros.append(vs[i, j].co.copy())
    return centros


# Qué crece en cada balda: (unidad, nivel) -> (material, alto de la mata, matas por fila)
CULTIVOS = {
    (0, 0): ("hoja_lechuga", 0.24, 4), (0, 1): ("hoja_albahaca", 0.2, 5), (0, 2): (None, 0.0, 0),
    (1, 0): ("hoja_albahaca", 0.22, 4), (1, 1): ("hoja_lechuga", 0.2, 3), (1, 2): (None, 0.0, 0),
    (2, 0): ("hoja_lechuga", 0.24, 4), (2, 1): ("hoja_albahaca", 0.18, 3), (2, 2): (None, 0.0, 0),
}


def bandejas_plantas():
    """Bandejas negras con sustrato en cada balda y las plantas encima (lechugas, albahaca, plantones)."""
    band = Pieza("invernadero_bandejas", peso_uv=1.6)
    plantas = Pieza("invernadero_plantas", peso_uv=2.3)
    rnd = random.Random(8)
    goteros = []
    for iu, (x0, x1, y0, y1, montantes) in enumerate(UNIDADES):
        tramos = [(montantes[k], montantes[k + 1]) for k in range(len(montantes) - 1)]
        for iz, z in enumerate(NIVELES):
            mat, alto, cabezas = CULTIVOS[iu, iz]
            for ya, yb in tramos:
                ya, yb = ya + 0.06, yb - 0.06
                xa, xb = x0 + 0.06, x1 - 0.06
                hb = 0.13
                ext = [(xa, ya), (xb, ya), (xb, yb), (xa, yb)]
                inte = [(xa + 0.02, ya + 0.02), (xb - 0.02, ya + 0.02), (xb - 0.02, yb - 0.02), (xa + 0.02, yb - 0.02)]
                band.baja.anillo_placa(ext, inte, Vector((0, 0, z)), Vector((1, 0, 0)), Vector((0, 1, 0)),
                                       Vector((0, 0, 1)), hb, "plastico_negro", fondo=0.03, mat_fondo="sustrato")
                zs = z + hb - 0.03
                goteros.append((xa + 0.06, ya, yb, z + hb + 0.015))
                if mat is None:
                    # Plantones recién germinados: solo en la alta (la bandeja se ve verde punteada).
                    for k in range(int((yb - ya) / 0.12)):
                        for xx in (xa + 0.15, (xa + xb) / 2, xb - 0.15):
                            q = Vector((xx, ya + 0.08 + k * 0.12, zs))
                            for r_ in (0.6, 3.7):
                                hoja3d(plantas.alta, q + Vector((0, 0, 0.04)), r_ + rnd.uniform(-0.3, 0.3), 0.05,
                                       0.035, 0.0, "hoja_lechuga", subida=0.02, secciones=2)
                    continue
                o = Vector((xa + 0.03, ya + 0.03, zs))
                centros = _fila(plantas.baja, o, Vector((0, 1, 0)), Vector((1, 0, 0)), yb - ya - 0.06, xb - xa - 0.06,
                                alto, cabezas, mat, semilla=iu * 10 + iz)
                # Hojas sueltas sobre cada mata (malla alta): roseta de lechuga o ramillete de albahaca.
                for cpos in centros:
                    n_h = 14 if "lechuga" in mat else 11
                    for k in range(n_h):
                        ang = math.tau * k / n_h + rnd.uniform(-0.2, 0.2)
                        anillo = k % 2
                        r0 = 0.03 + anillo * 0.05
                        q = Vector((cpos.x, cpos.y, zs)) + Vector((math.cos(ang) * r0, math.sin(ang) * r0,
                                                                     (cpos.z - zs) * (0.55 if anillo else 0.85)))
                        if "lechuga" in mat:
                            hoja3d(plantas.alta, q, ang, rnd.uniform(0.11, 0.15), rnd.uniform(0.1, 0.13),
                                   rnd.uniform(0.03, 0.07), mat, subida=0.06, secciones=3, alabeo=rnd.uniform(-0.6, 0.6))
                        else:
                            hoja3d(plantas.alta, q, ang, rnd.uniform(0.07, 0.1), rnd.uniform(0.05, 0.07),
                                   0.02, mat, subida=0.03, secciones=3)
    return [band, plantas], goteros


def tomateras():
    """Bancal de madera en el centro con cuatro tomateras atadas a sus cañas, con tomates rojos y alguno verde."""
    bancal = Pieza("invernadero_bancal", peso_uv=1.0)
    tom = Pieza("invernadero_tomateras", peso_uv=1.9)
    b = bancal.baja
    x0, x1, y0, y1 = -9.55, -8.45, -2.7, 2.9
    zt = GZ0 + 0.45
    for (a0, a1, c0, c1) in ((x0, x1, y0, y0 + 0.06), (x0, x1, y1 - 0.06, y1), (x0, x0 + 0.06, y0 + 0.06, y1 - 0.06),
                             (x1 - 0.06, x1, y0 + 0.06, y1 - 0.06)):
        for k in range(3):
            za = GZ0 - 0.04 + k * 0.165
            b.caja_de((a0, c0, za), (a1, c1, za + 0.155), "madera_bancal", sin=("-z",) if k == 0 else ())
    for x in (x0 - 0.02, x1 + 0.02):
        for y in (y0 - 0.02, y1 + 0.02):
            b.caja((x, y, (GZ0 + zt + 0.05) / 2), (0.08, 0.08, zt + 0.05 - GZ0), "madera_bancal", sin=("-z",))
    b.caja_de((x0 + 0.06, y0 + 0.06, GZ0), (x1 - 0.06, y1 - 0.06, zt - 0.05), "sustrato", sin=("-z", "-x", "+x", "-y", "+y"))
    rnd = random.Random(19)
    tb, ta = tom.baja, tom.alta
    for k, y in enumerate((-1.75, 0.1, 1.95)):
        base_p = Vector((-9.0 + rnd.uniform(-0.05, 0.05), y, zt - 0.05))
        top = 3.3 + rnd.uniform(-0.15, 0.1)
        alto = top - base_p.z
        # Caña de bambú, cuerda que baja de la correa y tallo principal (zigzag suave, atado a la caña).
        tb.cilindro(base_p + Vector((0.1, 0, 0)), (0, 0, 1), 0.018, alto, "madera_mango", lados=4)
        tb.tubo([base_p + Vector((0.1, 0, alto)), Vector((-8.9, y, 4.38))], 0.008, "cuerda", lados=3)
        tallo = [base_p + Vector((0.04 * math.sin(f * 7 + k), 0.04 * math.cos(f * 5), alto * f))
                 for f in (0.0, 0.3, 0.6, 0.85)]
        tb.tubo(tallo, 0.025, "tallo", lados=4, radios=[0.03, 0.024, 0.018, 0.012])
        for f in (0.25, 0.5, 0.75):
            ta.tubo([base_p + Vector((0.03, -0.03, alto * f)), base_p + Vector((0.12, -0.03, alto * f + 0.02)),
                     base_p + Vector((0.12, 0.03, alto * f + 0.02)), base_p + Vector((0.03, 0.03, alto * f))],
                    0.006, "cuerda", lados=3)
        # Ramilletes de hojas a distintas alturas y hacia lados alternos (rompen la silueta).
        for j, (f, ang, r) in enumerate(((0.22, 0.4, 0.27), (0.45, 2.6, 0.3), (0.68, 4.6, 0.26), (0.9, 1.5, 0.19))):
            ang += k * 1.1
            c0 = base_p + Vector((math.cos(ang) * r * 0.55, math.sin(ang) * r * 0.55, alto * f - 0.08))
            bulto(tb, c0 - Vector((0, 0, r * 0.35)), r, r * 1.5, "hoja_tomate", lados=6, semilla=k * 4 + j,
                  aplastar=1.0, base_r=0.45, rugoso=0.3)
            # Rama del tallo al ramillete (alta) y hojas compuestas que asoman (alta).
            ta.tubo([base_p + Vector((0, 0, alto * f - 0.1)), c0], 0.012, "tallo", lados=4)
            for _ in range(22):
                a2 = rnd.uniform(0, math.tau)
                e2 = rnd.uniform(-0.2, 1.1)
                q = c0 + Vector((math.cos(a2) * math.cos(e2) * r, math.sin(a2) * math.cos(e2) * r,
                                 r * 0.35 + math.sin(e2) * r * 0.6))
                hoja3d(ta, q - Vector((math.cos(a2), math.sin(a2), 0)) * 0.06, a2 + rnd.uniform(-0.5, 0.5),
                       rnd.uniform(0.13, 0.2), rnd.uniform(0.08, 0.12), 0.06, "hoja_tomate", subida=0.03,
                       secciones=3, alabeo=rnd.uniform(-0.7, 0.7))
        # Racimos de tomates colgando por fuera, debajo de los ramilletes.
        for j, (f, ang) in enumerate(((0.34, 1.6), (0.56, 4.0), (0.78, 0.2))):
            ang += k * 1.1
            c0 = base_p + Vector((math.cos(ang) * 0.24, math.sin(ang) * 0.24, alto * f - 0.12))
            r = rnd.uniform(0.07, 0.085)
            esfera(tb, c0, r, "tomate", lados=6, aplastar=0.88)
            ta.cupula(c0 + Vector((0, 0, r * 0.75)), (0, 0, 1), r * 0.5, "hoja_tomate", alto=0.01, lados=5)
            ta.tubo([c0 + Vector((0, 0, r * 0.8)), base_p + Vector((0, 0, alto * f))], 0.006, "tallo", lados=3)
            for _ in range(2):
                a2 = rnd.uniform(0, math.tau)
                c1 = c0 + Vector((math.cos(a2) * 0.09, math.sin(a2) * 0.09, rnd.uniform(-0.1, 0.0)))
                ta.revolucion([(0.0, -0.05), (0.05, -0.02), (0.05, 0.02), (0.0, 0.045)], c1, 8, "tomate")
    return [bancal, tom]


def riego(goteros):
    """Tubería de riego: general gris por el suelo, subidas con llave en cada estantería y goteo por las bandejas."""
    p = Pieza("invernadero_riego", peso_uv=1.2)
    b, a = p.baja, p.alta
    # General: entra desde el pasillo (la casa) junto a la puerta y recorre el fondo.
    zg = GZ0 + 0.06
    b.tubo([(GX1 - 0.12, 0.9, zg), (GX1 - 0.12, 3.85, zg), (GX0 + 0.12, 3.85, zg), (GX0 + 0.12, -3.85, zg)], 0.035,
           "pintura_gris", lados=4, radio_curva=0.1, pasos_curva=1)
    b.tubo([(GX1 - 0.12, 3.85, zg), (GX1 - 0.12, -3.85, zg)], 0.035, "pintura_gris", lados=4, tapa_ini=False)
    b.tubo([(GX1 - 0.12, 3.85, zg), (-9.0, 3.85, zg), (-9.0, 2.95, zg + 0.4)], 0.025, "pintura_gris", lados=4,
           radio_curva=0.1, pasos_curva=1, tapa_ini=False)
    for x0, x1, y0, y1, _ in UNIDADES:
        xr = x0 + 0.08 if x0 < GXC else x1 - 0.08
        ys = y1 - 0.08
        b.tubo([(xr, ys, zg), (xr, ys, NIVELES[-1] + 0.2)], 0.025, "pintura_gris", lados=4, tapa_ini=False)
        b.cilindro((xr - 0.04, ys, 0.75), (1, 0, 0), 0.035, 0.08, "laton", lados=6)
        b.caja((xr, ys, 0.8), (0.03, 0.14, 0.02), "pintura_roja")
    # Goteo: tubo negro fino a lo largo de cada bandeja, con los goteros (malla alta).
    for xg, ya, yb, z in goteros:
        b.tubo([(xg, yb + 0.05, z), (xg, ya + 0.05, z)], 0.012, "plastico_negro", lados=3)
        n = int((yb - ya) / 0.2)
        for k in range(n):
            q = Vector((xg, ya + 0.12 + k * 0.2, z))
            a.cilindro(q + Vector((0.012, 0, 0)), (1, 0, 0), 0.01, 0.06, "plastico_negro", lados=6)
    return p


def lampara_uv():
    """Lámpara UV larga colgada de la cumbrera: carcasa blanca con reflector y el tubo morado (neón)."""
    p = Pieza("lampara_uv", peso_uv=1.2)
    b, a = p.baja, p.alta
    zc = 4.35
    y0, y1 = -3.3, 3.3
    perfil = [(-0.1, 0.0), (-0.1, 0.06), (0.1, 0.06), (0.1, 0.0), (0.085, -0.045), (0.07, -0.045), (0.08, -0.005),
              (-0.08, -0.005), (-0.07, -0.045), (-0.085, -0.045)]
    anillos = [[Vector((GXC + x, y, zc + z)) for x, z in perfil] for y in (y0, y1)]
    b.loft(anillos, "lampara_uv_carcasa", tapa_ini=True, tapa_fin=True, suave=False)
    b.recalcular(b.ultimas)
    for y in (y0 + 0.4, 0.0, y1 - 0.4):
        b.tubo([(GXC, y, zc + 0.06), (GXC, y, GR - 0.02)], 0.008, "acero", lados=4, tapa_ini=False, tapa_fin=False)
        b.caja((GXC, y, zc + 0.08), (0.06, 0.06, 0.04), "acero")
    b.tubo([(GXC + 0.05, y1, zc + 0.03), (GXC + 0.1, y1 + 0.3, zc + 0.2), (GXC + 0.06, y1 + 0.55, GR - 0.05)], 0.015,
           "goma", lados=4)
    for y in (y0 + 0.05, y1 - 0.05):
        b.caja((GXC, y, zc - 0.06), (0.1, 0.06, 0.07), "lampara_uv_carcasa")
    for k in range(18):
        a.caja((GXC, y0 + 0.2 + k * 0.36, zc + 0.062), (0.12, 0.08, 0.004), "acero")
    tubo = Pieza("lampara_uv_tubo_neon_morado", peso_uv=0.3)
    tubo.baja.cilindro((GXC, y0 + 0.08, zc - 0.06), (0, 1, 0), 0.035, y1 - y0 - 0.16, "neon_morado", lados=6)
    p.extra["luz"] = [GXC, 0.0, zc - 0.12]
    return [p, tubo]


# ======================================================================================================
# Fuera del invernadero: mesa, compostero, sacos, carretilla
# ======================================================================================================

MESA = dict(x0=-11.25, x1=-8.35, y0=-5.3, y1=-4.5, z=1.25)


def mesa_trabajo():
    p = Pieza("mesa_trabajo", peso_uv=1.2)
    b, a = p.baja, p.alta
    M = MESA
    rnd = random.Random(52)
    # Tablero de cuatro tablas irregulares.
    n = 4
    w = (M["y1"] - M["y0"]) / n
    for i in range(n):
        y0 = M["y0"] + i * w + 0.01
        dz = rnd.uniform(-0.008, 0.008)
        b.caja_de((M["x0"] + rnd.uniform(-0.03, 0.03), y0, M["z"] - 0.08 + dz),
                  (M["x1"] + rnd.uniform(-0.03, 0.03), y0 + w - 0.02, M["z"] + dz), "madera_rustica")
        for x in (M["x0"] + 0.15, M["x1"] - 0.15):
            a.cupula((x, y0 + w / 2, M["z"] + dz), (0, 0, 1), 0.016, "hierro", alto=0.006, lados=6)
    # Patas, travesaños y balda de abajo.
    for x in (M["x0"] + 0.12, M["x1"] - 0.12):
        for y in (M["y0"] + 0.1, M["y1"] - 0.1):
            b.caja((x, y, (M["z"] - 0.08) / 2), (0.1, 0.1, M["z"] - 0.08), "madera_rustica", sin=("-z",))
        b.caja_de((x - 0.04, M["y0"] + 0.15, 0.35), (x + 0.04, M["y1"] - 0.15, 0.43), "madera_rustica",
                  sin=("-y", "+y"))
    b.caja_de((M["x0"] + 0.17, M["y0"] + 0.08, M["z"] - 0.2), (M["x1"] - 0.17, M["y0"] + 0.12, M["z"] - 0.08),
              "madera_rustica", sin=("-x", "+x"))
    b.caja_de((M["x0"] + 0.17, M["y0"] + 0.1, 0.43), (M["x1"] - 0.17, M["y1"] - 0.1, 0.47), "madera_rustica")
    return p


def semillero():
    """Bandeja de semillero: caja con divisiones, tierra y los plantones asomando."""
    p = Pieza("semillero", peso_uv=2.0)
    b, a = p.baja, p.alta
    x0, x1, y0, y1 = -11.05, -10.35, -5.15, -4.72
    z = MESA["z"]
    hb = 0.1
    ext = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    inte = [(x0 + 0.015, y0 + 0.015), (x1 - 0.015, y0 + 0.015), (x1 - 0.015, y1 - 0.015), (x0 + 0.015, y1 - 0.015)]
    b.anillo_placa(ext, inte, Vector((0, 0, z)), Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), hb,
                   "plastico_negro", fondo=0.03, mat_fondo="sustrato")
    nx, ny = 6, 3
    for i in range(1, nx):
        x = x0 + (x1 - x0) * i / nx
        b.caja_de((x - 0.006, y0 + 0.015, z + 0.06), (x + 0.006, y1 - 0.015, z + hb - 0.005), "plastico_negro",
                  sin=("-z", "-y", "+y"))
    for j in range(1, ny):
        y = y0 + (y1 - y0) * j / ny
        b.caja_de((x0 + 0.015, y - 0.006, z + 0.06), (x1 - 0.015, y + 0.006, z + hb - 0.005), "plastico_negro",
                  sin=("-z", "-x", "+x"))
    rnd = random.Random(3)
    for i in range(nx):
        for j in range(ny):
            if rnd.random() < 0.15:
                continue  # alguna celda aún no ha germinado
            q = Vector((x0 + (x1 - x0) * (i + 0.5) / nx, y0 + (y1 - y0) * (j + 0.5) / ny, z + 0.07))
            alto = rnd.uniform(0.04, 0.08)
            a.tubo([q, q + Vector((0, 0, alto))], 0.006, "tallo", lados=3, tapa_ini=False)
            for r_ in (0.4, 3.5):
                hoja3d(a, q + Vector((0, 0, alto)), r_ + rnd.uniform(-0.4, 0.4), 0.05,
                       0.04, 0.005, "hoja_lechuga", subida=0.015, secciones=2)
    # Etiqueta clavada en la tierra.
    b.caja((x1 - 0.05, y0 + 0.06, z + 0.12), (0.04, 0.005, 0.1), "papel", giro=rot("Z", 10))
    return p


def regadera():
    """Regadera de chapa galvanizada: cuerpo ovalado, asa, pitorro largo y alcachofa."""
    p = Pieza("regadera", peso_uv=1.8)
    b, a = p.baja, p.alta
    c0 = Vector((-9.55, -4.9, MESA["z"]))
    rz = 0.22
    b.revolucion([(0.14, 0.0), (0.16, 0.02), (0.16, 0.3), (0.15, 0.33), (0.1, 0.36), (0.0, 0.37)], c0, 10,
                 "galvanizado", tapa_ini=True, oculta_ini=True, escala=(1.25, 1.0), giro=rz)
    # Boca de llenado con reborde.
    b.revolucion([(0.06, 0.0), (0.065, 0.05), (0.055, 0.05), (0.05, -0.01)], c0 + Vector((-0.06, 0, 0.35)), 8,
                 "galvanizado", tapa_ini=False, tapa_fin=False)
    # Asa: arco de arriba y asa de atrás.
    b.tubo([c0 + Vector((0.1, 0, 0.36)), c0 + Vector((0.0, 0, 0.5)), c0 + Vector((-0.17, 0, 0.36))], 0.018,
           "galvanizado", lados=6, radio_curva=0.1, pasos_curva=3)
    b.tubo([c0 + Vector((-0.2, 0, 0.3)), c0 + Vector((-0.27, 0, 0.22)), c0 + Vector((-0.2, 0, 0.08))], 0.016,
           "galvanizado", lados=6, radio_curva=0.05, pasos_curva=2)
    # Pitorro y alcachofa.
    pa, pb = c0 + Vector((0.18, 0, 0.06)), c0 + Vector((0.5, 0, 0.38))
    b.tubo([pa, pb], 0.03, "galvanizado", lados=6, radios=[0.035, 0.02])
    d = (pb - pa).normalized()
    b.revolucion([(0.02, 0.0), (0.06, 0.05), (0.065, 0.065), (0.0, 0.07)], pb, 8, "galvanizado", eje=d,
                 tapa_ini=False)
    u, v = base_de(d)
    for k in range(12):
        ang = math.tau * k / 12
        a.cupula(pb + d * 0.07 + (u * math.cos(ang) + v * math.sin(ang)) * 0.035, d, 0.006, "negro_mate", alto=0.002,
                 lados=4)
    # Remaches de la costura (malla alta).
    for k in range(6):
        a.cupula(c0 + Vector((-0.2, 0, 0.05 + k * 0.05)), (-1, 0, 0), 0.01, "acero", alto=0.006, lados=6)
    return p


def tijeras():
    """Tijeras de podar abiertas sobre la mesa: dos hojas de acero y mangos rojos."""
    p = Pieza("tijeras_podar", peso_uv=2.4)
    b = p.baja
    c0 = Vector((-8.85, -4.82, MESA["z"] + 0.012))
    for s, ang in ((1, 14), (-1, -14)):
        g = rot("Z", ang + 20)
        hoja = [(0.0, -0.025), (0.13, -0.02), (0.2, 0.0), (0.13, 0.025), (0.0, 0.03)]
        pts = [(g @ Vector((x, y, 0))) for x, y in hoja]
        b.placa([(q.x, q.y) for q in pts], Vector((c0.x, c0.y, c0.z + (0.012 if s > 0 else 0.0))),
                Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), 0.01, "acero_pulido", atras=True)
        mango = [g @ Vector((-0.02, 0, 0)), g @ Vector((-0.12, s * 0.03, 0)), g @ Vector((-0.26, s * 0.045, 0))]
        b.tubo([c0 + q + Vector((0, 0, 0.012)) for q in mango], 0.018, "pintura_roja", lados=5)
    b.cilindro(c0 + Vector((0, 0, -0.002)), (0, 0, 1), 0.018, 0.03, "acero", lados=6)
    p.baja.tubo([c0 + Vector((-0.05, 0.0, 0.02)), c0 + Vector((-0.08, 0.02, 0.03)), c0 + Vector((-0.05, 0.03, 0.02))],
                0.004, "acero", lados=3)
    return p


COMPOST = dict(x0=-13.5, x1=-12.45, y0=-3.55, y1=-2.5, z=0.95)


def compostero():
    """Compostero casero de listones separados, con el compost dentro y la tapa medio abierta (pieza aparte)."""
    C = COMPOST
    p = Pieza("compostero", peso_uv=1.2)
    b = p.baja
    # Postes en las esquinas.
    for x in (C["x0"] + 0.04, C["x1"] - 0.04):
        for y in (C["y0"] + 0.04, C["y1"] - 0.04):
            b.caja((x, y, C["z"] / 2), (0.08, 0.08, C["z"]), "madera_compost", sin=("-z",))
    # Listones con separación (se ve el compost por las rendijas).
    rnd = random.Random(61)
    for k in range(4):
        z0 = 0.05 + k * 0.23
        z1 = z0 + 0.17
        dz = rnd.uniform(-0.01, 0.01)
        b.caja_de((C["x0"] + 0.02, C["y0"] - 0.02, z0 + dz), (C["x1"] - 0.02, C["y0"] + 0.02, z1 + dz), "madera_compost")
        b.caja_de((C["x0"] + 0.02, C["y1"] - 0.02, z0 - dz), (C["x1"] - 0.02, C["y1"] + 0.02, z1 - dz), "madera_compost")
        b.caja_de((C["x0"] - 0.02, C["y0"] + 0.02, z0 + dz), (C["x0"] + 0.02, C["y1"] - 0.02, z1 + dz), "madera_compost")
        b.caja_de((C["x1"] - 0.02, C["y0"] + 0.02, z0 - dz), (C["x1"] + 0.02, C["y1"] - 0.02, z1 - dz), "madera_compost")
    # El montón: superficie irregular algo por debajo del borde, y lo que se ve detrás de los listones.
    nx = 4
    vs = {}
    for i in range(nx + 1):
        for j in range(nx + 1):
            x = C["x0"] + 0.03 + (C["x1"] - C["x0"] - 0.06) * i / nx
            y = C["y0"] + 0.03 + (C["y1"] - C["y0"] - 0.06) * j / nx
            hz = 0.72 + 0.1 * math.sin(math.pi * i / nx) * math.sin(math.pi * j / nx) + \
                0.04 * noise.noise(Vector((x * 3, y * 3, 0)))
            vs[i, j] = b.v((x, y, hz))
    for i in range(nx):
        for j in range(nx):
            b.cara([vs[i, j], vs[i + 1, j], vs[i + 1, j + 1], vs[i, j + 1]], "compost", suave=True)
    b.caja_de((C["x0"] + 0.03, C["y0"] + 0.03, 0.0), (C["x1"] - 0.03, C["y1"] - 0.03, 0.72), "compost",
              sin=("+z", "-z"), ocultas=("-x", "+x", "-y", "+y"))
    # Restos encima (malla alta): pieles, hojas y una mazorca.
    for _ in range(18):
        q = Vector((rnd.uniform(C["x0"] + 0.15, C["x1"] - 0.15), rnd.uniform(C["y0"] + 0.15, C["y1"] - 0.15), 0.8))
        hoja3d(p.alta, q, rnd.uniform(0, math.tau), rnd.uniform(0.08, 0.14), 0.06, 0.02, "hoja_lechuga",
               subida=0.02, secciones=3)
    # Tapa: tablas sobre dos travesaños, con bisagras detrás (eje horizontal a lo largo de y). Medio abierta.
    eje = Vector((C["x0"] - 0.03, 0, C["z"] + 0.02))
    t = Pieza("compostero_tapa", pivote=(eje.x, (C["y0"] + C["y1"]) / 2, eje.z), peso_uv=1.2)
    tb = t.baja
    for i in range(4):
        x0 = C["x0"] - 0.03 + i * 0.28
        tb.caja_de((x0, C["y0"] - 0.05, eje.z), (x0 + 0.26, C["y1"] + 0.05, eje.z + 0.04), "madera_compost")
    for y in (C["y0"] + 0.1, C["y1"] - 0.1):
        tb.caja_de((C["x0"], y - 0.04, eje.z - 0.04), (C["x1"] + 0.02, y + 0.04, eje.z), "madera_compost")
    for y in (C["y0"] + 0.2, C["y1"] - 0.2):
        tb.cilindro((eje.x, y - 0.06, eje.z), (0, 1, 0), 0.02, 0.12, "hierro", lados=6)
    tb.tubo([(C["x1"] - 0.02, (C["y0"] + C["y1"]) / 2 - 0.1, eje.z + 0.04),
             (C["x1"] - 0.02, (C["y0"] + C["y1"]) / 2 - 0.1, eje.z + 0.1),
             (C["x1"] - 0.02, (C["y0"] + C["y1"]) / 2 + 0.1, eje.z + 0.1),
             (C["x1"] - 0.02, (C["y0"] + C["y1"]) / 2 + 0.1, eje.z + 0.04)], 0.012, "hierro", lados=4,
            radio_curva=0.02, pasos_curva=1)
    ang = 38.0
    giro = Matrix.Translation(eje) @ Matrix.Rotation(math.radians(-ang), 4, "Y") @ Matrix.Translation(-eje)
    for c in (tb, t.alta):
        c.transformar(c.bm.verts, giro)
    t.extra["angulo_abierta"] = ang
    return [p, t]


def _saco(c, alta, base, rumbo, alto, inclinado, abierto, semilla):
    """Saco de sustrato con pliegues; abierto: el borde doblado hacia fuera y tierra dentro."""
    rnd = random.Random(semilla)
    ini = set(c.bm.verts)
    ini_a = set(alta.bm.verts)
    n = 8
    anillos = []
    secciones = [(0.0, 0.26, 0.15), (0.06, 0.3, 0.19), (0.3, 0.31, 0.2), (0.55, 0.3, 0.19), (0.75, 0.28, 0.15)]
    if not abierto:
        secciones += [(0.88, 0.27, 0.07), (0.94, 0.28, 0.02)]
    else:
        secciones += [(0.86, 0.29, 0.17)]
    for k, (fz, rx, ry) in enumerate(secciones):
        anillo = []
        for i in range(n):
            ang = math.tau * i / n
            pl = 1 + 0.06 * noise.noise(Vector((i * 0.7, k * 1.3, semilla)))
            anillo.append(Vector((math.cos(ang) * rx * pl, math.sin(ang) * ry * pl, fz * alto)))
        anillos.append(anillo)
    if abierto:
        # Borde del saco enrollado hacia fuera, y dentro la tierra.
        top = secciones[-1]
        borde = [Vector((math.cos(math.tau * i / n) * top[1] * 1.08, math.sin(math.tau * i / n) * top[2] * 1.12,
                         top[0] * alto - 0.04)) for i in range(n)]
        dentro = [Vector((math.cos(math.tau * i / n) * top[1] * 0.92, math.sin(math.tau * i / n) * top[2] * 0.9,
                          top[0] * alto - 0.03)) for i in range(n)]
        c.loft(anillos + [borde, dentro], "saco", tapa_ini=True, oculta_ini=True, tapa_fin=False)
        tierra = [Vector((math.cos(math.tau * i / n) * top[1] * 0.92, math.sin(math.tau * i / n) * top[2] * 0.9,
                          top[0] * alto - 0.08 + 0.04 * rnd.random())) for i in range(n)]
        c.loft([dentro, tierra, [Vector((0.02, 0, top[0] * alto - 0.02))]], "tierra_suelta", tapa_ini=False)
    else:
        c.loft(anillos, "saco", tapa_ini=True, oculta_ini=True, tapa_fin=True)
        # Costura de la boca (malla alta).
        z = secciones[-1][0] * alto
        alta.tubo([Vector((-0.27 + i * 0.054, 0, z + 0.005)) for i in range(11)], 0.01, "cuerda", lados=4)
    # Pliegues (malla alta) y etiqueta impresa.
    for _ in range(8):
        ang = rnd.uniform(0, math.tau)
        z0 = rnd.uniform(0.1, 0.7) * alto
        p0 = Vector((math.cos(ang) * 0.3, math.sin(ang) * 0.195, z0))
        alta.tubo([p0, p0 + Vector((0.03, 0.0, 0.12))], 0.008, "saco", lados=4)
    nuevos = [v for v in c.bm.verts if v not in ini]
    nuevos_a = [v for v in alta.bm.verts if v not in ini_a]
    M = Matrix.Translation(base) @ Matrix.Rotation(math.radians(rumbo), 4, "Z") @ \
        Matrix.Rotation(math.radians(inclinado), 4, "X")
    c.transformar(nuevos, M)
    alta.transformar(nuevos_a, M)


def sacos():
    p = Pieza("sacos_sustrato", peso_uv=1.2)
    _saco(p.baja, p.alta, Vector((-12.45, -0.75, 0.0)), 95, 0.95, -12, False, 1)
    _saco(p.baja, p.alta, Vector((-12.47, 0.0, 0.0)), 88, 0.9, -14, False, 2)
    _saco(p.baja, p.alta, Vector((-12.6, 0.95, 0.0)), 70, 0.78, -6, True, 3)
    return p


def carretilla():
    """Carretilla de jardín: balde galvanizado con tierra, rueda delante, bastidor verde y asas de madera."""
    p = Pieza("carretilla", peso_uv=1.2)
    b, a = p.baja, p.alta
    o = Vector((-13.4, 2.6, 0.0))
    rz = 70.0
    ini = set(b.bm.verts)
    ini_a = set(a.bm.verts)
    # Local: x hacia la rueda, y a lo ancho, z arriba.
    rueda_c = Vector((0.62, 0.0, 0.2))
    # Balde: tronco de pirámide redondeado, abierto arriba, con reborde.
    def anillo(cx, w, l, z, n=10):
        pts = []
        for i in range(n):
            ang = math.tau * i / n
            sx, sy = math.cos(ang), math.sin(ang)
            ex = 4.0
            rx = l * math.copysign(abs(sx) ** (2 / ex), sx)
            ry = w * math.copysign(abs(sy) ** (2 / ex), sy)
            pts.append(Vector((cx + rx, ry, z)))
        return pts
    fondo = anillo(0.05, 0.2, 0.25, 0.42)
    medio = anillo(0.08, 0.3, 0.38, 0.6)
    boca = anillo(0.1, 0.36, 0.5, 0.75)
    reborde = anillo(0.1, 0.38, 0.52, 0.76)
    dentro = anillo(0.1, 0.34, 0.48, 0.73)
    b.loft([fondo, medio, boca, reborde, dentro], "galvanizado", tapa_ini=True, tapa_fin=False,
           mats_tramo=["galvanizado"] * 4)
    # Tierra dentro (montón).
    tierra = anillo(0.1, 0.34, 0.48, 0.62)
    b.loft([dentro, tierra, [Vector((0.08, 0.02, 0.72))]], "tierra_suelta", tapa_ini=False)
    # Bastidor: dos tubos de las asas a la rueda, patas y la horquilla.
    for s in (-1, 1):
        b.tubo([Vector((-0.95, s * 0.27, 0.62)), Vector((-0.35, s * 0.24, 0.42)), Vector((0.4, s * 0.12, 0.36)),
                rueda_c + Vector((0, s * 0.07, 0))], 0.022, "pintura_carretilla", lados=5, radio_curva=0.1, pasos_curva=1)
        b.tubo([Vector((-0.3, s * 0.24, 0.42)), Vector((-0.35, s * 0.26, 0.0))], 0.02, "pintura_carretilla", lados=6)
        b.caja(Vector((-0.35, s * 0.26, 0.01)), (0.12, 0.05, 0.02), "pintura_carretilla")
        # Asa de madera con el puño gastado.
        b.tubo([Vector((-0.95, s * 0.27, 0.62)), Vector((-1.35, s * 0.29, 0.75))], 0.03, "madera_mango", lados=5)
    # Rueda: neumático (toro) y llanta.
    r_ext, r_tubo = 0.2, 0.055
    neum = []
    for i in range(10):
        ang = math.tau * i / 10
        cc_ = rueda_c + Vector((math.cos(ang) * (r_ext - r_tubo), 0, math.sin(ang) * (r_ext - r_tubo)))
        neum.append([cc_ + (Vector((math.cos(ang), 0, math.sin(ang))) * math.cos(t) + Vector((0, 1, 0)) * math.sin(t))
                     * r_tubo for t in [math.tau * j / 6 for j in range(6)]])
    vs = b.loft(neum + [neum[0]], "goma", tapa_ini=False, tapa_fin=False)
    b.recalcular(b.ultimas)
    b.cilindro(rueda_c - Vector((0, 0.05, 0)), (0, 1, 0), 0.09, 0.1, "galvanizado", lados=8)
    b.cilindro(rueda_c - Vector((0, 0.09, 0)), (0, 1, 0), 0.02, 0.18, "acero", lados=6)
    # Dibujo del neumático (malla alta).
    for i in range(24):
        ang = math.tau * i / 24
        q = rueda_c + Vector((math.cos(ang), 0, math.sin(ang))) * (r_ext - 0.002)
        a.caja(q, (0.025, 0.08, 0.01), "goma", giro=rot("Y", -math.degrees(ang)))
    nuevos = [v for v in b.bm.verts if v not in ini]
    nuevos_a = [v for v in a.bm.verts if v not in ini_a]
    M = Matrix.Translation(o) @ Matrix.Rotation(math.radians(rz), 4, "Z")
    b.transformar(nuevos, M)
    a.transformar(nuevos_a, M)
    return p


# ======================================================================================================
# Todo junto
# ======================================================================================================


def construir():
    """Crea todas las piezas. Devuelve (piezas, P) donde P son los puntos que usan los materiales."""
    piezas = [base(), escalon(), zocalo(), paredes(), techo()]
    solar = panel_solar()
    piezas += [solar, canalon(), bajante()]
    tq = tanque()
    piezas += [tq, manguera_tanque(tq.extra["grifo"])]
    pu = puerta()
    piezas += [pu, puerta_marco()]
    piezas += puerta_lateral()
    piezas += ventana_frontal()
    piezas += ventana_lateral()
    piezas += lampara()
    piezas.append(cartel())
    piezas += gancho_delantal()
    piezas.append(enredadera())
    piezas += medidores(solar.extra["conexion"])
    piezas += grifo_manguera()
    piezas += [botas_agua(), gato(), camino()]
    # Invernadero.
    piezas += [invernadero_base(), invernadero_marco(), invernadero_vidrio()]
    piezas += puerta_invernadero()
    for nombre, (y0, y1) in VENTILAS.items():
        piezas += ventila(f"ventila_{nombre}", y0, y1, ANG_VENTILA if nombre == "abierta" else 0.0)
    pas = pasillo()
    piezas += pas
    piezas.append(estanterias())
    bp, goteros = bandejas_plantas()
    piezas += bp
    piezas += tomateras()
    piezas.append(riego(goteros))
    piezas += lampara_uv()
    piezas += [mesa_trabajo(), semillero(), regadera(), tijeras()]
    piezas += compostero()
    piezas += [sacos(), carretilla()]

    esc = [p for p in piezas if p.nombre == "escalon"][0]
    gu, gv = GRIFO
    P = {
        "manija": tuple(MANIJA),
        "manija_agarre": tuple(pu.extra["manija_agarre"]),
        "zocalo_z": ZOC_Z,
        "puerta_z0": HOJA["z0"],
        "puerta_suelo": ((PUERTA["x0"] + PUERTA["x1"]) / 2, -4.5, BASE_Z),
        "escalon_centro": tuple(esc.extra["centro"]),
        "felpudo_centro": tuple(pas[0].extra["felpudo"]),
        "bajante_pie": (TANQUE.x, TANQUE.y - 0.6, 0.2),
        "chimenea_boca": 99.0,
        "pico_agarre": (0.0, 0.1),
        "bisagras_puerta": (EJE_PUERTA.x, EJE_PUERTA.y, 2.5),
        "grifo_pared": tuple(DER.p(gu, gv, 0.1)),
        "medidor_agua": tuple(DER.p(-2.2, 1.95, 0.1)),
        "tanque_nivel": tq.extra["nivel"],
        "tanque_pie": tq.extra["pie"],
        "botas_barro": BASE_Z + 0.42,
        "galv_tierra": 0.75,
        "delantal_manos": GANCHO.z - 0.85,
        "gato": tuple(GATO),
    }
    return piezas, P
