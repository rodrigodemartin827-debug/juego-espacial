"""
Piezas de la taberna «La Última Órbita». Todo en STUDS, fachada a -Y.

Edificio de una planta con techo alto (12,5 × 6,5 studs de muros) elevado un stud sobre un cimiento de piedra, con
un porche cubierto de 2 studs a todo lo ancho de la fachada.

  muros: piedra abajo (1,0-1,9), banda de chapa remachada (1,9-2,6) y tablas horizontales solapadas y clavadas
         hasta el alero (5,8); parches soldados de alguna pelea.
  tejado: a dos aguas (36°), cumbrera a lo ancho, chimenea ancha de la cocina, dos aspiradores giratorios y la jarra
          de neón en la cumbrera.
  porche: tres postes de tronco con corteza (placas con 4 tornillos), tablas con separación (más gastadas en el
          centro), barandillas laterales con remates de bola, banco bajo la ventana, medio barril con una planta,
          cenicero de pie, campana en el poste del centro y dos faroles. Cartel tallado colgado sobre el porche.
  fachada: puertas de saloon (dos hojas, 4 bisagras de vaivén cada una), ventanal con cruceta y jarras detrás,
           pizarra del menú y tablón de anuncios.
  laterales: ventana de la cocina con rejilla (derecha) y ventana con contraventana (izquierda); medidor grande.
  detrás: muelle de carga, puerta metálica ancha con cruces, cerrojo y candado, barriles y bajante grueso.
  entorno: dos escalones de piedra, farola y una speeder bike aparcada.
"""

import math
import random

from mathutils import Matrix, Vector, noise

import casa_piezas as cp
import comerciante_piezas as cm2
from casa_malla import Pieza, base_de, rot
from casa_piezas import caja_plano, tornillo
from comerciante_piezas import texto

# ======================================================================================================
# Medidas (studs)
# ======================================================================================================

SUELO = 1.0            # el edificio se eleva un stud
MX = 6.25              # cara exterior de los muros laterales
Y0, Y1 = -3.0, 3.5     # cara exterior de la fachada y del muro de atrás
YC = (Y0 + Y1) / 2     # cumbrera
MURO = 0.3
PANEL = 0.06
PIEDRA_Z = 1.9         # fin de la piedra
CHAPA_Z = 2.6          # fin de la banda de chapa
ALERO_Z = 5.8
CUMBRE = 8.2
PEND = (CUMBRE - ALERO_Z) / (YC - Y0)
VUELO_X = 0.35
VUELO_Y = 0.35
ONDA, CHAPA, PASO = 0.08, 0.025, 0.7
# Porche
PORCHE_Y = -5.0
PORCHE_TECHO = (5.38, 4.96)    # alto de la chapa del porche junto a la pared y en el borde
VIGA_Y = -4.95
POSTES_X = (-6.05, 0.0, 6.05)
# Huecos de la fachada (u = x)
VENTANA = dict(x0=-5.0, x1=-1.9, z0=2.75, z1=4.75)
PUERTA = dict(x0=0.5, x1=2.7, z0=SUELO, z1=5.0)
HOJAS_Z = (1.95, 4.45)        # las hojas de saloon van a 3/4 de alto
VLAT = dict(u0=-0.45, u1=0.45, v0=2.85, v1=5.05)   # ventanas laterales, en el plano de cada muro
PUERTA_T = dict(u0=-3.95, u1=-1.35, v0=SUELO, v1=4.6)  # puerta de atrás (plano de atrás: u = -x)


def z_tejado(y):
    return CUMBRE - PEND * abs(y - YC)


def z_muro(y):
    return z_tejado(y) - ONDA - CHAPA - 0.005


def z_porche(y):
    """Cara de arriba de la chapa del porche (cae hacia la calle)."""
    a, b = PORCHE_TECHO
    f = (Y0 - y) / (Y0 - (PORCHE_Y - 0.25))
    return a + (b - a) * f


FRENTE = cp.Plano((0, Y0, 0), (0, -1, 0))   # u = +x
FONDO = cp.Plano((0, Y1, 0), (0, 1, 0))     # u = -x
IZQ = cp.Plano((-MX, YC, 0), (-1, 0, 0))    # u = -(y - YC)
DER = cp.Plano((MX, YC, 0), (1, 0, 0))      # u = +(y - YC)
HY = (Y1 - Y0) / 2


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def _restar(intervalos, a, b):
    """Quita [a, b] de una lista de intervalos."""
    res = []
    for x0, x1 in intervalos:
        if b <= x0 or a >= x1:
            res.append((x0, x1))
            continue
        if a > x0:
            res.append((x0, a))
        if b < x1:
            res.append((b, x1))
    return res


def _parche(p, pl, uc, vc, w, h, ang, rnd, d0, mat=None):
    """Chapa soldada con su cordón (malla alta), como las del minero pero a la altura `d0` que se pida."""
    pts = []
    esquinas = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    for k, (x, y) in enumerate(esquinas):
        nx, ny = esquinas[(k + 1) % 4]
        px, py = esquinas[k - 1]
        d1 = Vector((px - x, py - y)).normalized() * rnd.uniform(0.03, 0.08)
        d2 = Vector((nx - x, ny - y)).normalized() * rnd.uniform(0.03, 0.08)
        pts += [(x + d1.x, y + d1.y), (x + d2.x, y + d2.y)]
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))
    pts = [(uc + x * ca - y * sa, vc + x * sa + y * ca) for x, y in pts]
    mat = mat or ("parche_minio" if rnd.random() < 0.4 else "parche")
    p.baja.placa(pts, pl.p(0, 0, d0), pl.u, pl.v, pl.n, 0.02, mat)
    cx = sum(q[0] for q in pts) / len(pts)
    cy = sum(q[1] for q in pts) / len(pts)
    lazo = []
    for q in pts + [pts[0]]:
        dv = Vector((q[0] - cx, q[1] - cy))
        dv = dv.normalized() * (dv.length + 0.008)
        lazo.append(pl.p(cx + dv.x, cy + dv.y, d0 + 0.006))
    fino = []
    for i in range(len(lazo) - 1):
        for k in range(6):
            fino.append(lazo[i].lerp(lazo[i + 1], k / 6))
    fino.append(lazo[-1])
    p.alta.tubo(fino, 0.016, "soldadura", lados=6, tapa_ini=False, tapa_fin=False)


# ======================================================================================================
# Cimiento, muros y tejado
# ======================================================================================================


def cimiento():
    """Cimiento de sillares grandes bajo el edificio, reforzado con pletinas y escuadras atornilladas."""
    p = Pieza("cimiento", peso_uv=0.9)
    b = p.baja
    rnd = random.Random(2)
    b.caja_de((-MX - 0.2, Y0 - 0.05, 0), (MX + 0.2, Y1 + 0.2, SUELO), "mortero", sin=("-z",), ocultas=("+z",))
    # Sillares (dos hiladas) en las cuatro caras.
    for pl, u0, u1 in ((FONDO, -MX - 0.2, MX + 0.2), (IZQ, -HY - 0.05, HY + 0.2), (DER, -HY - 0.05, HY + 0.2)):
        for k, (v0, v1) in enumerate(((0.0, 0.48), (0.51, SUELO - 0.02))):
            u = u0 - (0.5 if k else 0)
            while u < u1 - 0.05:
                largo = rnd.uniform(1.5, 2.3)
                if u1 - (u + largo) < 0.6:
                    largo = u1 - u
                a, bb = max(u, u0), min(u + largo, u1)
                if bb - a > 0.12:
                    giro = rot("Y", rnd.uniform(-1.2, 1.2)) @ rot("X", rnd.uniform(-1, 1))
                    caja_plano(b, pl, a + 0.018, bb - 0.018, v0 + 0.01, v1, 0.18, 0.18 + rnd.uniform(0.07, 0.11),
                               "piedra", sin=("+y", "-z"), giro_extra=giro)
                u += largo
    # Refuerzo: viga de acero (perfil en L) corrida y escuadras atornilladas cada poco.
    for pl, u0, u1 in ((FONDO, -MX - 0.2, MX + 0.2), (IZQ, -HY, HY + 0.2), (DER, -HY, HY + 0.2)):
        caja_plano(b, pl, u0, u1, SUELO - 0.16, SUELO, 0.18, 0.32, "hierro", sin=("+y",))
        n = int((u1 - u0) / 2.4)
        for k in range(n + 1):
            uu = u0 + 0.3 + k * (u1 - u0 - 0.6) / max(1, n)
            caja_plano(b, pl, uu - 0.07, uu + 0.07, 0.35, SUELO - 0.16, 0.18, 0.3, "hierro", sin=("+y",))
            for vv in (0.5, 0.72):
                tornillo(p, pl.p(uu, vv, 0.3), pl.n, 0.026, "hierro", en_baja=False)
    return p


def muros():
    """Alma de los muros con sus huecos y las tres bandas: piedra, chapa remachada y tablas clavadas."""
    p = Pieza("muros", peso_uv=1.0)
    b, a = p.baja, p.alta
    rnd = random.Random(9)
    V, D, L, T = VENTANA, PUERTA, VLAT, PUERTA_T

    def alma(pl, ext, inte, huecos):
        b.cara_con_huecos([pl.p(u, v, 0) for u, v in ext], [[pl.p(u, v, 0) for u, v in h] for h in huecos], "junta",
                          pl.n, oculta=2)
        b.cara_con_huecos([pl.p(u, v, -MURO) for u, v in inte], [[pl.p(u, v, -MURO) for u, v in h] for h in huecos],
                          "interior", -pl.n, oculta=1)

    def hastial(u_min, u_max, y_de_u, base=SUELO):
        pts = [(u_min, base), (u_max, base)]
        for k in range(9):
            u = u_max - (u_max - u_min) * k / 8
            pts.append((u, z_muro(y_de_u(u))))
        return pts

    alma(FRENTE, [(-MX, PIEDRA_Z - 0.05), (D["x0"], PIEDRA_Z - 0.05), (D["x0"], D["z1"]), (D["x1"], D["z1"]),
                  (D["x1"], PIEDRA_Z - 0.05), (MX, PIEDRA_Z - 0.05), (MX, ALERO_Z), (-MX, ALERO_Z)],
         [(-MX + MURO, SUELO), (D["x0"], SUELO), (D["x0"], D["z1"]), (D["x1"], D["z1"]), (D["x1"], SUELO),
          (MX - MURO, SUELO), (MX - MURO, ALERO_Z), (-MX + MURO, ALERO_Z)], [rect(V["x0"], V["x1"], V["z0"], V["z1"])])
    alma(FONDO, [(-MX, PIEDRA_Z - 0.05), (T["u0"], PIEDRA_Z - 0.05), (T["u0"], T["v1"]), (T["u1"], T["v1"]),
                 (T["u1"], PIEDRA_Z - 0.05), (MX, PIEDRA_Z - 0.05), (MX, ALERO_Z), (-MX, ALERO_Z)],
         [(-MX + MURO, SUELO), (T["u0"], SUELO), (T["u0"], T["v1"]), (T["u1"], T["v1"]), (T["u1"], SUELO),
          (MX - MURO, SUELO), (MX - MURO, ALERO_Z), (-MX + MURO, ALERO_Z)], [])
    for pl, signo in ((IZQ, -1), (DER, 1)):
        ext = hastial(-HY, HY, lambda u, s=signo: YC + s * u, PIEDRA_Z - 0.05)
        inte = hastial(-HY + MURO, HY - MURO, lambda u, s=signo: YC + s * u)
        alma(pl, ext, inte, [rect(L["u0"], L["u1"], L["v0"], L["v1"])])

    # ---- banda de piedra (sillarejo) ---------------------------------------------------------------------------
    tramos_piedra = [(FRENTE, [(-MX - 0.12, D["x0"] - 0.03), (D["x1"] + 0.03, MX + 0.12)]),
                     (FONDO, [(-MX - 0.12, T["u0"] - 0.03), (T["u1"] + 0.03, MX + 0.12)]),
                     (IZQ, [(-HY, HY)]), (DER, [(-HY, HY)])]
    for pl, intervalos in tramos_piedra:
        for u0, u1 in intervalos:
            caja_plano(b, pl, u0, u1, SUELO, PIEDRA_Z, 0.0, 0.07, "mortero", sin=("+y", "-z", "+z"), ocultas=("-y",))
            for k, (v0, v1) in enumerate(((SUELO, 1.44), (1.47, PIEDRA_Z - 0.02))):
                u = u0 - (0.35 if k else 0.0)
                while u < u1 - 0.05:
                    largo = rnd.uniform(0.85, 1.35)
                    if u1 - (u + largo) < 0.45:
                        largo = u1 - u
                    aa, bb = max(u, u0), min(u + largo, u1)
                    if bb - aa > 0.1:
                        giro = rot("Y", rnd.uniform(-2, 2)) @ rot("X", rnd.uniform(-1.5, 1.5))
                        caja_plano(b, pl, aa + 0.016, bb - 0.016, v0 + rnd.uniform(0, 0.015), v1 - rnd.uniform(0, 0.015),
                                   0.05, rnd.uniform(0.1, 0.14), "piedra", sin=("+y", "-z") if k == 0 else ("+y",),
                                   giro_extra=giro)
                    u += largo

    # ---- banda de chapa remachada -----------------------------------------------------------------------------
    for pl, intervalos in tramos_piedra:
        for u0, u1 in intervalos:
            cortes = [u0]
            while cortes[-1] < u1 - 0.1:
                cortes.append(min(u1, cortes[-1] + rnd.uniform(1.2, 1.7)))
            for i in range(len(cortes) - 1):
                cm2._panel(p, pl, cortes[i], cortes[i + 1], PIEDRA_Z, CHAPA_Z, "panel_viejo", rnd, remaches=0.3)
        # Remate de la piedra: vierteaguas metálico.
        for u0, u1 in intervalos:
            perfil = [(0.035, PIEDRA_Z + 0.03), (0.17, PIEDRA_Z - 0.03), (0.17, PIEDRA_Z - 0.06), (0.155, PIEDRA_Z - 0.06),
                      (0.155, PIEDRA_Z - 0.043), (0.035, PIEDRA_Z + 0.008)]
            b.placa(perfil, pl.p(u0, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, u1 - u0, "hierro", atras=True)

    # ---- tablas horizontales solapadas, clavadas ------------------------------------------------------------------
    alto_tabla = 0.32
    huecos = {
        "F": [(V["x0"] - 0.22, V["x1"] + 0.22, V["z0"] - 0.25, V["z1"] + 0.22),
              (D["x0"] - 0.24, D["x1"] + 0.24, 0, D["z1"] + 0.24)],
        "B": [(T["u0"] - 0.2, T["u1"] + 0.2, 0, T["v1"] + 0.2)],
        "I": [(L["u0"] - 0.15, L["u1"] + 0.15, L["v0"] - 0.15, L["v1"] + 0.15)],
        "D": [(L["u0"] - 0.15, L["u1"] + 0.15, L["v0"] - 0.15, L["v1"] + 0.15)],
    }
    for clave, pl, u_min, u_max, signo in (("F", FRENTE, -MX, MX, 0), ("B", FONDO, -MX, MX, 0),
                                           ("I", IZQ, -HY, HY, -1), ("D", DER, -HY, HY, 1)):
        v = CHAPA_Z
        fila = 0
        while True:
            v0, v1 = v, v + alto_tabla
            if signo == 0 and v0 >= ALERO_Z:
                break
            if signo != 0 and v0 >= z_muro(YC) - 0.05:
                break
            intervalos = [(u_min, u_max)]
            for h in huecos[clave]:
                if v1 > h[2] and v0 < h[3]:
                    intervalos = _restar(intervalos, h[0], h[1])
            for i0, i1 in intervalos:
                # Juntas a tope de tablas de 2-3,5 studs, distintas en cada fila.
                cortes = [i0]
                desfase = (fila * 1.37) % 2.0
                x = i0 + 1.8 + desfase * 1.5
                while x < i1 - 0.6:
                    cortes.append(x)
                    x += rnd.uniform(3.6, 5.2)
                cortes.append(i1)
                for k in range(len(cortes) - 1):
                    a0, a1 = cortes[k] + 0.012, cortes[k + 1] - 0.012
                    if a1 - a0 < 0.1:
                        continue
                    poly = rect(a0, a1, v0, v1 - 0.02)
                    if signo != 0:
                        # Hastial: la tabla se corta con las dos aguas del tejado.
                        poly = cm2_recortar(poly, 0, 0, z_muro(YC) - 0.02, 0)
                    else:
                        poly = cp.recortar(poly, 0, 1, ALERO_Z - 0.1)
                    if len(poly) < 3 or cp.area(poly) < 0.01:
                        continue
                    entera = abs(cp.area(poly) - (a1 - a0) * (v1 - 0.02 - v0)) < 1e-4
                    if entera:
                        # Tabla solapada: el canto de abajo sale más que el de arriba.
                        uc, vc = (a0 + a1) / 2, (v0 + v1 - 0.02) / 2
                        # (la cara de arriba queda tapada por la tabla de encima: no se crea)
                        caja_plano(b, pl, a0, a1, v0, v1 - 0.02, 0.07, 0.12, "madera_vieja", sin=("+y", "+z"),
                                   giro_extra=rot("X", -6))
                    else:
                        b.placa(poly, pl.p(0, 0, 0.07), pl.u, pl.v, pl.n, 0.05, "madera_vieja")
                    # Clavos: dos por tabla en cada extremo y cada 1,2 studs (malla alta).
                    us = [q[0] for q in poly]
                    vs = [q[1] for q in poly]
                    ua, ub = min(us) + 0.07, max(us) - 0.07
                    n = max(1, int((ub - ua) / 1.2))
                    for t in range(n + 1):
                        uu = ua + (ub - ua) * t / n
                        vv = (min(vs) + max(vs)) / 2
                        if cp._dentro(poly, uu, vv):
                            a.cupula(pl.p(uu, vv, 0.125), pl.n, 0.017, "hierro", alto=0.008, lados=6)
            v += alto_tabla
            fila += 1
    # ---- parches soldados (peleas) ---------------------------------------------------------------------------------
    for pl, uc, vc, w, h, ang in ((FRENTE, 4.6, 2.25, 0.6, 0.42, 5), (FRENTE, -3.6, 2.2, 0.5, 0.4, -4),
                                  (FONDO, 2.5, 3.6, 0.8, 0.55, 3), (IZQ, 1.9, 4.2, 0.7, 0.5, -6),
                                  (DER, -2.2, 3.3, 0.55, 0.45, 8)):
        d0 = PANEL - 0.002 if vc < CHAPA_Z else 0.125
        _parche(p, pl, uc, vc, w, h, ang, rnd, d0)

    # ---- cantoneras de madera en las esquinas -------------------------------------------------------------------------
    for sx in (-1, 1):
        for y_esq, sy in ((Y0, -1), (Y1, 1)):
            z1 = ALERO_Z
            xa = sorted((sx * (MX - 0.18), sx * (MX + 0.16)))
            ya = sorted((y_esq + sy * 0.12, y_esq + sy * 0.17))
            b.caja_de((xa[0], ya[0], CHAPA_Z), (xa[1], ya[1], z1), "madera_vieja", sin=("+y" if sy < 0 else "-y",))
            xb = sorted((sx * (MX + 0.12), sx * (MX + 0.17)))
            yb = sorted((y_esq - sy * 0.18, y_esq + sy * 0.16))
            b.caja_de((xb[0], yb[0], CHAPA_Z), (xb[1], yb[1], z1), "madera_vieja", sin=("+x" if sx < 0 else "-x",))
    return p


def cm2_recortar(poly, pend, b_, zc, signo):
    """Recorta una tabla del hastial con las dos aguas: v <= zc - PEND*|u|."""
    poly = cp.recortar(poly, PEND, 1.0, zc)
    poly = cp.recortar(poly, -PEND, 1.0, zc)
    return poly


def _perfil_x(x0, x1, fase=-6.9):
    """Puntos (x, alto) de la chapa grecada con los nervios a lo largo de Y."""
    corte = [0.0, 0.3, 0.4, 0.6, 0.7]
    alto = [0.0, 0.0, ONDA, ONDA, 0.0]

    def h(x):
        t = (x - fase) % PASO
        for k in range(4):
            if corte[k] <= t <= corte[k + 1]:
                f = (t - corte[k]) / (corte[k + 1] - corte[k])
                return alto[k] + (alto[k + 1] - alto[k]) * f
        return 0.0

    xs = [x0]
    k0 = math.floor((x0 - fase) / PASO)
    k1 = math.ceil((x1 - fase) / PASO)
    for k in range(k0, k1 + 1):
        for c in corte[1:4]:
            x = fase + k * PASO + c
            if x0 + 1e-4 < x < x1 - 1e-4:
                xs.append(x)
    xs.append(x1)
    return [(x, h(x)) for x in xs]


def _chapa(c, x0, x1, y_a, y_b, z_de_y, mat, elev=0.0, tapa_a=False, tapa_b=True):
    """Chapa grecada entre y_a e y_b (nervios a lo largo de Y), con la superficie z_de_y(y) en los valles."""
    perfil = _perfil_x(x0, x1)
    anillos = []
    for y in (y_a, y_b):
        zb = z_de_y(y) - ONDA + elev
        arriba = [Vector((x, y, zb + hh)) for x, hh in perfil]
        abajo = [Vector((x, y, zb + hh - CHAPA)) for x, hh in reversed(perfil)]
        anillos.append(arriba + abajo)
    c.loft(anillos, mat, tapa_ini=tapa_a, tapa_fin=tapa_b, suave=False)
    c.recalcular(c.ultimas)
    return perfil


def tejado():
    """Tejado a dos aguas: tres chapas por faldón (una cambiada), cumbrera, remates y canalón detrás."""
    p = Pieza("tejado", peso_uv=0.85)
    b, a = p.baja, p.alta
    xe = MX + VUELO_X
    chapas = [(-xe, -2.0, "chapa_taberna", 0.0), (-2.2, 2.3, "chapa_taberna", CHAPA + 0.002),
              (2.1, xe, "chapa_taberna", 0.0)]
    for lado, y_eave in ((-1, Y0 - VUELO_Y), (1, Y1 + VUELO_Y)):
        for x0, x1, mat, elev in chapas:
            if lado == 1 and x0 > -2.3 and x0 < 0:
                mat = "chapa_nueva"
            perfil = _chapa(b, x0, x1, YC, y_eave, z_tejado, mat, elev=elev)
            # Tornillos con arandela sobre las crestas (malla alta).
            k0 = math.ceil((x0 + 6.9) / PASO)
            for k in range(k0, k0 + int((x1 - x0) / PASO) + 1):
                xc = -6.9 + k * PASO + 0.5
                if x0 + 0.1 < xc < x1 - 0.1:
                    for f in (0.15, 0.5, 0.9):
                        y = YC + (y_eave - YC) * f
                        z = z_tejado(y) + elev
                        nrm = Vector((0, lado * PEND, 1)).normalized()
                        a.cupula((xc, y, z - 0.002), nrm, 0.035, "goma", alto=0.007, lados=8)
                        a.cupula((xc, y, z + 0.004), nrm, 0.022, "acero", alto=0.016, lados=6)
    # Cumbrera.
    phi = math.degrees(math.atan(PEND))
    for lado in (-1, 1):
        g = rot("X", -lado * phi)
        yc = YC + lado * 0.24 * math.cos(math.radians(phi))
        b.caja((0, yc, z_tejado(yc) + CHAPA + 0.03), (2 * xe + 0.08, 0.5, 0.025), "metal_oscuro", giro=g)
    # Remates de los hastiales.
    for sx in (-1, 1):
        for lado, y_eave in ((-1, Y0 - VUELO_Y), (1, Y1 + VUELO_Y)):
            g = rot("X", -lado * phi)
            ym = (YC + y_eave) / 2
            largo = abs(y_eave - YC) / math.cos(math.radians(phi))
            b.caja((sx * (xe + 0.013), ym, z_tejado(ym) - 0.07), (0.026, largo + 0.02, 0.26), "metal_oscuro", giro=g)
            b.caja((sx * (xe - 0.055), ym, z_tejado(ym) + 0.06), (0.16, largo + 0.02, 0.022), "metal_oscuro", giro=g)
    # Canalón de atrás (perfil en U con grosor) y sus tapas.
    ye = Y1 + VUELO_Y
    zc = z_tejado(ye) - 0.16
    ext = [(0.07, 0.11), (0.06, -0.02), (0.0, -0.09), (-0.14, -0.1), (-0.21, -0.05), (-0.26, 0.09), (-0.24, 0.11)]
    ext = [(-yy, zz) for yy, zz in ext]
    inte = [(yy * 0.9 + (0.0 if i == 0 else 0.0), zz + 0.02) for i, (yy, zz) in enumerate(ext)]
    perfil = [(ye + yy, zc + zz) for yy, zz in ext] + [(ye + yy, zc + zz) for yy, zz in reversed(inte)]
    anillos = [[Vector((x, yy, zz)) for yy, zz in perfil] for x in (-xe, xe)]
    b.loft(anillos, "metal_oscuro", tapa_ini=False, tapa_fin=False, suave=False)
    b.recalcular(b.ultimas)
    for x, n in ((-xe, -1), (xe, 1)):
        b.placa([(ye + yy, zc + zz) for yy, zz in ext], Vector((x, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)),
                Vector((n, 0, 0)), 0.02, "metal_oscuro", atras=True)
    p.extra["canalon_bajada"] = [-5.95, ye + 0.12, zc - 0.1]
    return p


def chimenea():
    """Chimenea ancha de la cocina: cuerpo rectangular de chapa remachada con sombrerete a cuatro aguas."""
    p = Pieza("chimenea", peso_uv=1.2)
    b, a = p.baja, p.alta
    xc, yc = 3.6, 2.1
    w, d = 0.95, 0.7
    zr = z_tejado(yc)
    top = zr + 1.45
    phi = math.degrees(math.atan(PEND))
    b.caja((xc, yc, zr + 0.015), (w + 0.4, d + 0.4, 0.03), "metal_oscuro", giro=rot("X", -phi))
    b.caja_de((xc - w / 2, yc - d / 2, zr - 0.4), (xc + w / 2, yc + d / 2, top), "metal_hollin", sin=("-z",))
    b.caja_de((xc - w / 2 - 0.04, yc - d / 2 - 0.04, top - 0.12), (xc + w / 2 + 0.04, yc + d / 2 + 0.04, top),
              "metal_hollin")
    # Sombrerete sobre cuatro patas.
    zs = top + 0.32
    b.revolucion([(0.0, 0.25), (0.82, 0.0), (0.82, -0.04), (0.7, -0.04)][::-1], (xc, yc, zs), 4, "metal_hollin",
                 giro=math.pi / 4, suave=False, tapa_ini=True, escala=(1.0, d / w))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b.caja((xc + sx * (w / 2 - 0.05), yc + sy * (d / 2 - 0.05), top + 0.14), (0.04, 0.04, 0.3), "metal_oscuro")
    for zz in (zr + 0.35, top - 0.3):
        for k in range(8):
            x = xc - w / 2 + 0.06 + k * (w - 0.12) / 7
            a.cupula((x, yc - d / 2, zz), (0, -1, 0), 0.018, "acero", alto=0.01, lados=6)
    p.extra["humo"] = [xc, yc, top]
    return p


def aspiradores():
    """Dos aspiradores giratorios (setas de ventilación): base, cuello y cabeza de álabes."""
    p = Pieza("aspiradores", peso_uv=1.3)
    b, a = p.baja, p.alta
    for xc, yc in ((-3.8, -1.25), (-0.6, 1.9)):
        zr = z_tejado(yc)
        phi = math.degrees(math.atan(PEND)) * (1 if yc < YC else -1)
        b.caja((xc, yc, zr + 0.012), (0.6, 0.6, 0.025), "metal_oscuro", giro=rot("X", phi))
        b.revolucion([(0.16, -0.2), (0.16, 0.4), (0.19, 0.43), (0.19, 0.47)], (xc, yc, zr), 10, "aluminio",
                     tapa_ini=False, tapa_fin=False)
        # Cabeza: esfera achatada de álabes curvos.
        perfil = [(0.19, 0.47)] + [(0.31 * math.sin(t), 0.62 + 0.2 * -math.cos(t)) for t in
                                   (math.radians(60), math.radians(95), math.radians(125), math.radians(150))] + [
            (0.06, 0.85), (0.0, 0.86)]
        b.revolucion(perfil, (xc, yc, zr), 10, "aluminio", tapa_ini=False)
        # Álabes (malla alta): cintas curvas en espiral.
        for k in range(16):
            ang = math.tau * k / 16
            pts = []
            for t in range(7):
                f = t / 6
                th = math.radians(55 + f * 95)
                r = 0.31 * math.sin(th) + 0.006
                aa = ang + f * 0.6
                pts.append(Vector((xc + math.cos(aa) * r, yc + math.sin(aa) * r, zr + 0.62 - 0.2 * math.cos(th))))
            a.tubo(pts, 0.012, "aluminio", lados=4, tapa_ini=False, tapa_fin=False)
        a.cupula((xc, yc, zr + 0.86), (0, 0, 1), 0.05, "acero", alto=0.02)
    return p


def cartel_techo():
    """Cartel de neón en la cumbrera: bastidor de tubo y la silueta de una jarra con espuma."""
    soporte = Pieza("cartel_jarra", peso_uv=1.2)
    neon = Pieza("cartel_jarra_neon", peso_uv=0.6)
    b = soporte.baja
    xc = 0.0
    zr = CUMBRE + 0.06
    y = YC
    for x in (xc - 0.75, xc + 0.75):
        b.caja((x, y, zr + 0.55), (0.06, 0.06, 1.1), "metal_oscuro")
        b.caja((x, y, zr + 0.02), (0.2, 0.36, 0.04), "metal_oscuro")
    b.caja((xc, y, zr + 0.42), (1.6, 0.05, 0.05), "metal_oscuro")
    b.caja((xc, y, zr + 1.1), (1.6, 0.05, 0.05), "metal_oscuro")
    # Jarra: cuerpo (rectángulo redondeado), asa, espuma con burbujas.
    c = neon.baja
    zb = zr + 0.5
    cuerpo = [(-0.3, zb), (0.25, zb), (0.25, zb + 0.75), (-0.3, zb + 0.75), (-0.3, zb)]
    c.tubo([Vector((xc + x, y - 0.06, z)) for x, z in cuerpo], 0.035, "neon", lados=5, radio_curva=0.06,
           pasos_curva=2, tapa_ini=False, tapa_fin=False)
    asa = [(0.25, zb + 0.6), (0.48, zb + 0.6), (0.48, zb + 0.18), (0.25, zb + 0.18)]
    c.tubo([Vector((xc + x, y - 0.06, z)) for x, z in asa], 0.03, "neon", lados=5, radio_curva=0.08,
           pasos_curva=2)
    espuma = [(-0.34, zb + 0.75)] + [(-0.3 + k * 0.11, zb + 0.84 + 0.05 * math.sin(k * 1.9)) for k in range(6)] + [
        (0.3, zb + 0.75)]
    c.tubo([Vector((xc + x, y - 0.06, z)) for x, z in espuma], 0.03, "neon", lados=5, radio_curva=0.04, pasos_curva=1)
    for x, z in ((-0.12, zb + 0.35), (0.05, zb + 0.5), (-0.05, zb + 0.18)):
        c.revolucion([(0.0, -0.035), (0.035, 0.0), (0.0, 0.035)], (xc + x, y - 0.06, z), 6, "neon", eje=(0, -1, 0))
    return [soporte, neon]


# ======================================================================================================
# Porche
# ======================================================================================================


def porche_suelo():
    """Tablas del porche con separación (se ve oscuro debajo), viguetas, zócalo y cabezal."""
    p = Pieza("porche_suelo", peso_uv=1.6)
    b, a = p.baja, p.alta
    rnd = random.Random(31)
    x0, x1 = -MX - 0.05, MX + 0.05
    # Fondo oscuro y viguetas que se ven entre las tablas.
    b.caja_de((x0, PORCHE_Y + 0.05, 0.0), (x1, Y0, 0.6), "piedra_oscura", sin=("-z", "+y"))
    for k in range(9):
        x = x0 + 0.15 + k * (x1 - x0 - 0.3) / 8
        b.caja_de((x - 0.07, PORCHE_Y + 0.06, 0.6), (x + 0.07, Y0, SUELO - 0.08), "madera_oscura", sin=("+y", "-z"))
    b.caja_de((x0, PORCHE_Y, 0.55), (x1, PORCHE_Y + 0.08, SUELO - 0.08), "madera_porche", sin=("+y",))
    for sx in (-1, 1):
        xs = sorted((sx * (MX + 0.05), sx * (MX - 0.03)))
        b.caja_de((xs[0], PORCHE_Y + 0.08, 0.55), (xs[1], Y0, SUELO - 0.08), "madera_porche", sin=("-y", "+y"))
    # Tablas: a lo largo de la fachada, juntas a tope escalonadas.
    ancho, sep = 0.27, 0.03
    n = int((Y0 - PORCHE_Y) / (ancho + sep))
    for i in range(n):
        ya = PORCHE_Y + 0.02 + i * (ancho + sep)
        yb = ya + ancho
        cortes = [x0]
        x = x0 + 1.5 + (i * 1.9) % 2.6
        while x < x1 - 1.0:
            cortes.append(x)
            x += rnd.uniform(3.0, 4.2)
        cortes.append(x1)
        for k in range(len(cortes) - 1):
            xa, xb = cortes[k] + 0.006, cortes[k + 1] - 0.006
            dz = rnd.uniform(-0.006, 0.004)
            b.caja_de((xa, ya, SUELO - 0.08), (xb, yb, SUELO + dz), "madera_porche", sin=("-z",))
            # Dos clavos en cada vigueta (malla alta).
            for j in range(9):
                xv = x0 + 0.15 + j * (x1 - x0 - 0.3) / 8
                if xa + 0.05 < xv < xb - 0.05:
                    for dy in (0.07, ancho - 0.07):
                        a.cupula((xv, ya + dy, SUELO + dz), (0, 0, 1), 0.016, "hierro", alto=0.006, lados=6)
    return p


def _tronco(c, base, alto, radio, semilla, mat="tronco"):
    """Poste de tronco: sección irregular, algo torcido, que adelgaza hacia arriba."""
    lados = 8
    anillos = []
    n = 5
    for k in range(n + 1):
        f = k / n
        z = alto * f
        desv = Vector((noise.noise(Vector((semilla, f * 2, 0))) * 0.06, noise.noise(Vector((f * 2, semilla, 1))) * 0.06,
                       0))
        r_med = radio * (1.08 - 0.12 * f) * (1.12 if k == 0 else 1.0)
        anillo = []
        for i in range(lados):
            ang = math.tau * i / lados
            r = r_med * (1 + 0.1 * noise.noise(Vector((math.cos(ang) * 2 + semilla, math.sin(ang) * 2, f * 3))))
            anillo.append(Vector(base) + desv + Vector((math.cos(ang) * r, math.sin(ang) * r, z)))
        anillos.append(anillo)
    c.loft(anillos, mat, tapa_ini=False, tapa_fin=False, suave=True)


def porche_estructura():
    """Postes de tronco con placas atornilladas, viga, durmiente en la pared y cabios."""
    p = Pieza("porche_postes", peso_uv=1.6)
    b, a = p.baja, p.alta
    zv = PORCHE_TECHO[1] - 0.36
    for k, x in enumerate(POSTES_X):
        _tronco(b, (x, VIGA_Y, SUELO), zv - SUELO + 0.02, 0.17, 3.1 * k + 1.7)
        # Placa de anclaje con 4 tornillos y otra arriba, contra la viga.
        b.caja_de((x - 0.24, VIGA_Y - 0.24, SUELO), (x + 0.24, VIGA_Y + 0.24, SUELO + 0.025), "hierro", sin=("-z",))
        for sx in (-1, 1):
            for sy in (-1, 1):
                tornillo(p, (x + sx * 0.17, VIGA_Y + sy * 0.17, SUELO + 0.025), (0, 0, 1), 0.028, "hierro")
        b.caja_de((x - 0.2, VIGA_Y - 0.03, SUELO + 0.025), (x + 0.2, VIGA_Y + 0.03, SUELO + 0.3), "hierro")
        # Corteza (malla alta): grietas verticales.
        for j in range(14):
            ang = math.tau * j / 14 + 0.2 * math.sin(j * 7.0)
            r = 0.175
            a.tubo([Vector((x + math.cos(ang) * r, VIGA_Y + math.sin(ang) * r, SUELO + 0.4 + 0.3 * (j % 3))),
                    Vector((x + math.cos(ang + 0.05) * (r - 0.01), VIGA_Y + math.sin(ang + 0.05) * (r - 0.01),
                            zv - 0.4 - 0.25 * (j % 2)))], 0.012, "madera_oscura", lados=4)
    # Viga sobre los postes y durmiente en la pared.
    b.caja_de((-MX - 0.2, VIGA_Y - 0.15, zv), (MX + 0.2, VIGA_Y + 0.15, zv + 0.3), "madera_vieja")
    zl = PORCHE_TECHO[0] - 0.34
    b.caja_de((-MX, Y0 - 0.18, zl), (MX, Y0 - 0.06, zl + 0.26), "madera_vieja", sin=("+y",))
    # Cabios del muro a la viga.
    for x in (-6.0, -4.05, -2.1, -0.15, 1.8, 3.75, 6.0):
        y0, y1 = Y0 - 0.18, VIGA_Y - 0.15
        z0 = z_porche(y0) - ONDA - CHAPA - 0.005
        z1 = z_porche(y1) - ONDA - CHAPA - 0.005
        largo = math.hypot(y1 - y0, z1 - z0)
        ang = math.degrees(math.atan2(z0 - z1, y0 - y1))
        b.caja(Vector((x, (y0 + y1) / 2, (z0 + z1) / 2 - 0.1)), (0.12, largo + 0.3, 0.2), "madera_vieja",
               giro=rot("X", ang))
        for yy in (y0 + 0.15, y1 - 0.1):
            a.cupula((x, yy, z_porche(yy) - ONDA - CHAPA - 0.2), (0, 0, -1), 0.02, "hierro", alto=0.01, lados=6)
    return p


def porche_tejado():
    p = Pieza("porche_tejado", peso_uv=1.0)
    b = p.baja
    ye = PORCHE_Y - 0.25
    _chapa(b, -MX - 0.25, 0.15, Y0 - 0.12, ye, z_porche, "chapa_taberna")
    _chapa(b, -0.05, MX + 0.25, Y0 - 0.12, ye, z_porche, "chapa_taberna", elev=CHAPA + 0.002)
    # Tapajuntas contra la pared y remates laterales.
    b.caja_de((-MX - 0.25, Y0 - 0.2, z_porche(Y0) - 0.02), (MX + 0.25, Y0 - 0.05, z_porche(Y0) + 0.06),
              "metal_oscuro", sin=("+y",))
    ang = math.degrees(math.atan2(PORCHE_TECHO[0] - PORCHE_TECHO[1], Y0 - ye))
    for sx in (-1, 1):
        ym = (Y0 + ye) / 2
        b.caja((sx * (MX + 0.265), ym, z_porche(ym) - 0.06), (0.025, Y0 - ye, 0.24), "metal_oscuro",
               giro=rot("X", ang))
    return p


def barandillas():
    """Barandillas bajas (0,7) a los lados del porche: postes con bola y pasamanos gastado."""
    p = Pieza("barandillas", peso_uv=1.5)
    b = p.baja
    alto = 0.7
    for sx in (-1, 1):
        x = sx * (MX - 0.08)
        ys = (Y0 - 0.15, (Y0 + PORCHE_Y) / 2 - 0.1, PORCHE_Y + 0.25)
        for y in ys:
            b.caja_de((x - 0.06, y - 0.06, SUELO), (x + 0.06, y + 0.06, SUELO + alto - 0.02), "madera_vieja",
                      sin=("-z",))
            b.revolucion([(0.04, 0.0), (0.08, 0.04), (0.085, 0.09), (0.06, 0.14), (0.0, 0.16)],
                         (x, y, SUELO + alto - 0.02), 6, "madera_vieja", tapa_ini=False)
        # Pasamanos (perfil redondeado por el desgaste) y travesaño bajo.
        perfil = [(-0.07, 0.0), (0.07, 0.0), (0.07, 0.03), (0.045, 0.06), (-0.045, 0.06), (-0.07, 0.03)]
        b.placa([(x + dx, SUELO + alto - 0.13 + dz) for dx, dz in perfil], Vector((0, ys[0] + 0.06, 0)),
                Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)), ys[0] - ys[2] + 0.12, "madera_vieja",
                atras=True)
        b.caja_de((x - 0.035, ys[2], SUELO + 0.18), (x + 0.035, ys[0], SUELO + 0.26), "madera_vieja",
                  sin=("-y", "+y"))
        for k in range(1, 7):  # balaustres
            y = ys[2] + (ys[0] - ys[2]) * k / 7
            b.caja_de((x - 0.025, y - 0.025, SUELO + 0.26), (x + 0.025, y + 0.025, SUELO + alto - 0.13),
                      "madera_vieja", sin=("-z", "+z"))
    return p


def banco():
    """Banco largo contra la pared bajo la ventana: tres tablas de asiento sobre escuadras de hierro."""
    p = Pieza("banco_porche", peso_uv=1.6)
    b, a = p.baja, p.alta
    x0, x1 = -5.15, -1.75
    zs = SUELO + 1.35
    for k in range(3):
        y = Y0 - 0.12 - k * 0.2
        b.caja_de((x0, y - 0.18, zs - 0.06), (x1, y, zs), "madera_banco", sin=())
    for x in (x0 + 0.3, (x0 + x1) / 2, x1 - 0.3):
        # Escuadra en L: pata contra la pared y brazo bajo el asiento.
        perfil = [(0.0, 0.0), (0.05, 0.0), (0.05, 0.56), (0.62, 0.56), (0.62, 0.6), (0.0, 0.6)]
        b.placa([(dy, zs - 0.66 + dz) for dy, dz in perfil], Vector((x - 0.025, Y0 - 0.06, 0)),
                Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0)), 0.05, "hierro", atras=True)
        b.caja_de((x - 0.04, Y0 - 0.66, SUELO), (x + 0.04, Y0 - 0.58, zs - 0.06), "hierro", sin=("-z",))
        for dz in (0.15, 0.45):
            tornillo(p, (x, Y0 - 0.11, zs - 0.66 + dz), (0, -1, 0), 0.02, "hierro", en_baja=False)
    p.extra["asiento"] = [(x0 + x1) / 2, Y0 - 0.32, zs]
    return p


def barril_maceta():
    """Medio barril de roble usado como maceta, con sus aros y una planta resistente."""
    p = Pieza("barril_maceta", peso_uv=1.6)
    b, a = p.baja, p.alta
    c = Vector((5.25, -4.3, SUELO))
    perfil = [(0.36, 0.0), (0.4, 0.2), (0.42, 0.42), (0.36, 0.42), (0.35, 0.36)]
    b.revolucion(perfil, c, 10, "madera_barril", tapa_ini=True, oculta_ini=True, tapa_fin=True, mat_fin="tierra")
    for z, r in ((0.08, 0.375), (0.32, 0.418)):
        b.revolucion([(r, z - 0.035), (r + 0.012, z - 0.03), (r + 0.012, z + 0.03), (r, z + 0.035)], c, 10, "hierro",
                     tapa_ini=False, tapa_fin=False)
    for k in range(16):  # duelas (malla alta)
        ang = math.tau * k / 16
        a.tubo([c + Vector((math.cos(ang) * 0.362, math.sin(ang) * 0.362, 0.01)),
                c + Vector((math.cos(ang) * 0.4, math.sin(ang) * 0.4, 0.21)),
                c + Vector((math.cos(ang) * 0.421, math.sin(ang) * 0.421, 0.41))], 0.006, "madera_oscura", lados=4)
    # Planta tipo agave: hojas carnosas hacia arriba y afuera.
    rnd = random.Random(12)
    for k in range(7):
        rumbo = math.tau * k / 7 + rnd.uniform(-0.2, 0.2)
        cp._hoja(b, c + Vector((0, 0, 0.38)), rumbo, rnd.uniform(0.35, 0.5), rnd.uniform(0.09, 0.12),
                 rnd.uniform(0.0, 0.08), subida=rnd.uniform(0.3, 0.45), secciones=4)
    return p


def cenicero():
    p = Pieza("cenicero", peso_uv=1.6)
    c = Vector((-5.55, -4.55, SUELO))
    p.baja.revolucion([(0.2, 0.0), (0.2, 0.03), (0.06, 0.06), (0.045, 0.1), (0.045, 0.95), (0.07, 0.98),
                       (0.17, 1.02), (0.17, 1.06), (0.14, 1.06), (0.12, 1.03)], c, 10, "hierro", tapa_ini=False,
                      tapa_fin=True, mat_fin="ceniza")
    for k in range(4):  # colillas (malla alta)
        ang = k * 1.7
        p.alta.cilindro(c + Vector((math.cos(ang) * 0.07, math.sin(ang) * 0.07, 1.04)),
                        (math.cos(ang + 1), math.sin(ang + 1), 0.15), 0.008, 0.05, "papel", lados=6)
    return p


def campana():
    """Campana en el poste del centro, con su brazo, el yugo y la cuerda."""
    p = Pieza("campana", peso_uv=1.8)
    b = p.baja
    x, y = POSTES_X[1], VIGA_Y
    z = SUELO + 2.8
    b.caja_de((x + 0.12, y - 0.05, z - 0.12), (x + 0.16, y + 0.05, z + 0.12), "hierro")
    b.tubo([(x + 0.16, y, z), (x + 0.42, y, z), (x + 0.5, y, z - 0.08)], 0.022, "hierro", lados=6, radio_curva=0.06)
    tope = Vector((x + 0.5, y, z - 0.1))
    b.caja(tope + Vector((0, 0, 0.0)), (0.08, 0.14, 0.05), "hierro")
    perfil = [(0.015, 0), (0.06, -0.02), (0.075, -0.08), (0.11, -0.2), (0.125, -0.235), (0.11, -0.235),
              (0.095, -0.2), (0.06, -0.09), (0.04, -0.04), (0.0, -0.04)]
    b.revolucion(list(reversed(perfil)), tope + Vector((0, 0, -0.03)), 8, "laton", tapa_ini=False, tapa_fin=True)
    b.tubo([tope + Vector((0, 0, -0.05)), tope + Vector((0, 0, -0.2))], 0.005, "hierro", lados=4)
    b.revolucion([(0.0, -0.24), (0.022, -0.225), (0.022, -0.2), (0.0, -0.19)], tope, 6, "hierro")
    cuerda = [tope + Vector((0, 0, -0.24)), tope + Vector((0.02, 0.01, -0.6)), tope + Vector((-0.01, 0.0, -1.0)),
              tope + Vector((0.0, 0.0, -1.18))]
    b.tubo(cuerda, 0.014, "cuerda", lados=5)
    b.revolucion([(0.0, -0.06), (0.03, -0.03), (0.03, 0.02), (0.0, 0.04)], cuerda[-1], 6, "cuerda")
    return p


def faroles():
    """Dos faroles hexagonales colgados de los cabios, a cada lado de la puerta."""
    cuerpo = Pieza("faroles", peso_uv=1.6)
    cristal = Pieza("faroles_cristal", peso_uv=0.5)
    bombillas = Pieza("faroles_bombilla_neon", peso_uv=0.5)
    b = cuerpo.baja
    for x in (-0.15, 3.75):
        y = -4.05
        ztop = z_porche(y) - ONDA - CHAPA - 0.3
        zc = ztop - 0.75
        b.tubo([(x, y, ztop + 0.05), (x, y, zc + 0.3)], 0.012, "hierro", lados=4)
        b.revolucion([(0.04, 0.38), (0.03, 0.42)], (x, y, zc), 6, "hierro", tapa_ini=False)
        # Tejadillo hexagonal, cuerpo con montantes y base.
        b.revolucion([(0.18, 0.18), (0.22, 0.17), (0.22, 0.19), (0.04, 0.38)], (x, y, zc), 6, "hierro",
                     tapa_ini=True, suave=False)
        b.revolucion([(0.0, -0.24), (0.06, -0.24), (0.16, -0.2), (0.16, -0.17)], (x, y, zc), 6, "hierro",
                     tapa_fin=True, suave=False)
        for k in range(6):
            ang = math.tau * k / 6
            b.caja(Vector((x + math.cos(ang) * 0.165, y + math.sin(ang) * 0.165, zc)), (0.025, 0.025, 0.36), "hierro",
                   giro=rot("Z", math.degrees(ang)))
        cristal.baja.revolucion([(0.15, -0.17), (0.15, 0.18), (0.14, 0.18), (0.14, -0.17)], (x, y, zc), 6,
                                "vidrio_ambar", tapa_ini=False, tapa_fin=False)
        bombillas.baja.revolucion([(0.0, -0.1), (0.05, -0.08), (0.07, -0.01), (0.05, 0.07), (0.025, 0.1),
                                   (0.025, 0.16)], (x, y, zc), 8, "neon", tapa_fin=True)
    cuerpo.extra["luces"] = [[-0.15, -4.05, z_porche(-4.05) - 1.05], [3.75, -4.05, z_porche(-4.05) - 1.05]]
    return [cuerpo, cristal, bombillas]


# ======================================================================================================
# Puertas
# ======================================================================================================


def _hoja_saloon(nombre, x_eje, sentido):
    """Hoja de saloon: dos largueros, tres tablas horizontales con refuerzo en cruz, remate curvo y barra de empuje."""
    D = PUERTA
    ancho = (D["x1"] - D["x0"]) / 2 - 0.05
    z0, z1 = HOJAS_Z
    ye = Y0 + 0.08               # eje de las bisagras (en el grosor de la hoja)
    p = Pieza(nombre, pivote=(x_eje, ye, z0), peso_uv=1.8)
    b, a = p.baja, p.alta
    y0, y1 = ye - 0.05, ye + 0.05
    xa = x_eje + sentido * 0.06
    xb = x_eje + sentido * ancho

    def cajax(u0, u1, z0_, z1_, mat, dy0=0.0, dy1=0.0, **kw):
        lo, hi = sorted((u0, u1))
        b.caja_de((lo, y0 + dy0, z0_), (hi, y1 + dy1, z1_), mat, **kw)

    cajax(xa, xa + sentido * 0.12, z0, z1 - 0.05, "madera_saloon")
    cajax(xb - sentido * 0.12, xb, z0, z1 - 0.3, "madera_saloon")
    # Tres tablas horizontales con separación.
    zs = (z0 + 0.12, z0 + 0.92, z0 + 1.72)
    for zt in zs:
        cajax(xa + sentido * 0.12, xb - sentido * 0.12, zt, zt + 0.62, "madera_saloon", dy0=0.015, dy1=-0.015,
              sin=("-x", "+x"))
    # Remate curvo arriba (más alto junto a la bisagra, como las de los western).
    pts = [(0.0, 0.0), (1.0, 0.0)] + [(1 - f, 0.22 * math.sin(math.pi * (1 - f) * 0.5) + 0.04) for f in
                                      (0.0, 0.25, 0.5, 0.75, 1.0)]
    pts = [(xa + sentido * 0.12 + sentido * f * (ancho - 0.3), z0 + 2.38 + h) for f, h in pts]
    if sentido < 0:
        pts = list(reversed(pts))
    b.placa(pts, Vector((0, y0 + 0.01, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0)), 0.08,
            "madera_saloon", atras=True)
    # Refuerzo en cruz por delante y barra de empuje (gastada).
    for zz0, zz1 in ((zs[0] + 0.08, zs[2] + 0.54), (zs[2] + 0.54, zs[0] + 0.08)):
        pa = Vector((xa + sentido * 0.2, y0 - 0.02, zz0))
        pb = Vector((xb - sentido * 0.2, y0 - 0.02, zz1))
        dv = pb - pa
        b.caja((pa + pb) / 2, (0.1, 0.03, dv.length), "madera_saloon",
               giro=rot("Y", math.degrees(math.atan2(dv.x, dv.z))))
    zb = (z0 + z1) / 2 - 0.1
    for lado in (-1, 1):
        yb = (y0 if lado < 0 else y1)
        for xx in (xa + sentido * 0.3, xb - sentido * 0.3):
            b.cilindro((xx, yb, zb), (0, lado, 0), 0.02, 0.08, "laton", lados=6, tapa_ini=False, tapa_fin=False)
        b.revolucion([(0.0, -0.02), (0.028, 0.0), (0.028, abs(xb - xa) - 0.48), (0.0, abs(xb - xa) - 0.46)],
                     (min(xa, xb) + 0.25 + (0.0 if sentido > 0 else 0.0), yb + lado * 0.08, zb), 8, "laton_gastado",
                     eje=(1, 0, 0))
    # Cuatro bisagras de vaivén: doble tambor con muelle visible y palas.
    for zh in (z0 + 0.22, z0 + 0.82, z0 + 1.6, z0 + 2.25):
        for dy in (-0.045, 0.045):
            b.revolucion([(0.03, -0.1), (0.03, 0.1)], (x_eje, ye + dy, zh), 6, "hierro", tapa_ini=True, tapa_fin=True)
            hel = []
            for k in range(30):
                ang = k * 1.1
                hel.append(Vector((x_eje + math.cos(ang) * 0.034, ye + dy + math.sin(ang) * 0.034, zh - 0.07 + k * 0.0048)))
            a.tubo(hel, 0.006, "hierro", lados=4, tapa_ini=False, tapa_fin=False)
        cajax(x_eje + sentido * 0.02, x_eje + sentido * 0.18, zh - 0.07, zh + 0.07, "hierro", dy0=-0.012, dy1=0.012)
        for xx in (x_eje + sentido * 0.12,):
            tornillo(p, (xx, y0 - 0.012, zh), (0, -1, 0), 0.016, "hierro", en_baja=False)
    return p


def puertas_saloon():
    D = PUERTA
    izq = _hoja_saloon("puerta_saloon_izq", D["x0"] + 0.02, 1)
    der = _hoja_saloon("puerta_saloon_der", D["x1"] - 0.02, -1)
    # Marco de la puerta (jambas, dintel con tablilla, umbral) y la parte fija de las bisagras.
    marco = Pieza("puerta_marco", peso_uv=1.4)
    cm2._marco_puerta(marco, FRENTE, D["x0"], D["x1"], D["z1"], "pintura_granate", ancho=0.22, d_frente=0.17, base=SUELO)
    for x in (D["x0"], D["x1"]):
        for zh in (HOJAS_Z[0] + 0.22, HOJAS_Z[0] + 0.82, HOJAS_Z[0] + 1.6, HOJAS_Z[0] + 2.25):
            lo, hi = sorted((x, x + (0.06 if x == D["x0"] else -0.06)))
            marco.baja.caja_de((lo, Y0 + 0.02, zh - 0.12), (hi, Y0 + 0.14, zh + 0.12), "hierro")
    return [izq, der, marco]


def puerta_trasera():
    """Puerta metálica ancha (entran barriles) con refuerzos en X, cerrojo grande y candado."""
    pl = FONDO
    T = PUERTA_T
    eje_u = T["u1"] + 0.05
    piv = pl.p(eje_u, T["v0"] + 0.05, 0.1)
    pu = Pieza("puerta_trasera", pivote=piv, peso_uv=1.6)
    b, a = pu.baja, pu.alta
    u0, u1, v0, v1 = T["u0"] + 0.05, T["u1"] - 0.05, T["v0"] + 0.06, T["v1"] - 0.05
    caja_plano(b, pl, u0, u1, v0, v1, -0.08, 0.05, "metal_trasera", sin=("-z",))
    # Bastidor y cruces en X por fuera.
    m = 0.1
    for (a0, a1, b0, b1) in ((u0, u0 + m, v0, v1), (u1 - m, u1, v0, v1), (u0 + m, u1 - m, v1 - m, v1),
                             (u0 + m, u1 - m, v0, v0 + m), (u0 + m, u1 - m, (v0 + v1) / 2 - m / 2, (v0 + v1) / 2 + m / 2)):
        caja_plano(b, pl, a0, a1, b0, b1, 0.05, 0.09, "metal_trasera", sin=("+y",))
    for vb0, vb1 in ((v0 + m, (v0 + v1) / 2 - m / 2), ((v0 + v1) / 2 + m / 2, v1 - m)):
        for s in (-1, 1):
            pa = pl.p(u0 + m, vb0 if s > 0 else vb1, 0.07)
            pb = pl.p(u1 - m, vb1 if s > 0 else vb0, 0.07)
            dv = pb - pa
            g = pl.giro @ rot("Y", -math.degrees(math.atan2((vb1 - vb0) * s, (u1 - u0 - 2 * m))))
            b.caja((pa + pb) / 2, (dv.length, 0.04, 0.09), "metal_trasera", giro=g)
    # Remaches del bastidor (malla alta).
    for k in range(9):
        for uu in (u0 + m / 2, u1 - m / 2):
            a.cupula(pl.p(uu, v0 + 0.2 + k * (v1 - v0 - 0.4) / 8, 0.09), pl.n, 0.02, "acero", alto=0.012, lados=6)
    # Cerrojo grande: dos guías, barra y manilla; candado colgando.
    vc = 2.75
    for uu in (u0 + 0.25, u0 + 0.6):
        caja_plano(b, pl, uu - 0.06, uu + 0.06, vc - 0.07, vc + 0.07, 0.09, 0.17, "hierro", sin=("+y",))
    b.cilindro(pl.p(u0 - 0.25, vc, 0.14), pl.u, 0.035, 1.05, "hierro_gastado", lados=8)
    b.tubo([pl.p(u0 + 0.75, vc, 0.14), pl.p(u0 + 0.75, vc, 0.3), pl.p(u0 + 0.75, vc - 0.14, 0.3)], 0.02, "hierro",
           lados=6, radio_curva=0.04)
    caja_plano(b, pl, u0 - 0.36, u0 - 0.1, vc - 0.1, vc + 0.1, 0.05, 0.19, "hierro", sin=("+y",))
    cuerpo = pl.p(u0 - 0.2, vc - 0.24, 0.19)
    b.caja(cuerpo, (0.13, 0.05, 0.12), "laton", giro=pl.giro)
    b.tubo([cuerpo + pl.v * 0.06 - pl.u * 0.04, cuerpo + pl.v * 0.16 - pl.u * 0.04, cuerpo + pl.v * 0.16 + pl.u * 0.04,
            cuerpo + pl.v * 0.06 + pl.u * 0.04], 0.012, "acero", lados=4, radio_curva=0.03)
    # Bisagras de pala larga.
    for vh in (1.5, 4.0):
        caja_plano(b, pl, u1 - 0.7, u1 + 0.02, vh - 0.08, vh + 0.08, 0.09, 0.11, "hierro", sin=("+y",))
        b.cilindro((piv.x, piv.y, vh - 0.1), (0, 0, 1), 0.05, 0.2, "hierro", lados=8)
    marco = Pieza("puerta_trasera_marco", peso_uv=1.2)
    cm2._marco_puerta(marco, pl, T["u0"], T["u1"], T["v1"], "metal_oscuro", ancho=0.2, d_frente=0.16, base=SUELO)
    for vh in (1.5, 4.0):
        for z0 in (vh - 0.3, vh + 0.1):
            marco.baja.cilindro((piv.x, piv.y, z0), (0, 0, 1), 0.05, 0.2, "hierro", lados=8)
    caja_plano(marco.baja, pl, T["u0"] - 0.4, T["u0"] - 0.2, vc - 0.07, vc + 0.07, 0.16, 0.24, "hierro", sin=("+y",))
    return [pu, marco]


def muelle_carga():
    """Muelle de hormigón en la puerta de atrás, con cantonera de acero y dos barriles metálicos apilados."""
    p = Pieza("muelle_carga", peso_uv=1.0)
    b = p.baja
    x0, x1 = 0.9, 5.9
    b.caja_de((x0, Y1 + 0.2, 0), (x1, Y1 + 1.4, SUELO), "hormigon", sin=("-z",))
    b.caja_de((x0, Y1 + 1.4, SUELO - 0.12), (x1, Y1 + 1.44, SUELO + 0.005), "hierro")
    b.caja_de((x0 - 0.02, Y1 + 1.33, SUELO - 0.03), (x1 + 0.02, Y1 + 1.44, SUELO + 0.005), "hierro", sin=("-z",))
    for x in (x0 + 0.5, x1 - 0.5):
        b.caja_de((x - 0.25, Y1 + 1.4, 0.15), (x + 0.25, Y1 + 1.55, 0.75), "goma")  # topes de goma
    barriles = Pieza("barriles", peso_uv=1.7)
    for k, z in enumerate((SUELO, SUELO + 1.22)):
        _barril(barriles, Vector((5.15, Y1 + 0.8, z)), con_grifo=k == 0, etiqueta=("CERVEZA", "LOTE 12")[k],
                giro=0.4 * k)
    return [p, barriles]


def _barril(p, base, con_grifo, etiqueta, giro=0.0):
    b, a = p.baja, p.alta
    r = 0.42
    perfil = [(r * 0.94, 0.0), (r, 0.3), (r * 1.02, 0.6), (r, 0.9), (r * 0.94, 1.2), (r * 0.82, 1.16)]
    b.revolucion(perfil, base, 10, "barril_metal", tapa_ini=True, oculta_ini=True, tapa_fin=True, giro=giro)
    for z in (0.3, 0.9):  # aros
        b.revolucion([(r * 1.0, z - 0.04), (r * 1.04, z - 0.025), (r * 1.04, z + 0.025), (r * 1.0, z + 0.04)], base, 8,
                     "hierro", tapa_ini=False, tapa_fin=False, giro=giro)
    b.cilindro(base + Vector((0.18, 0.05, 1.16)), (0, 0, 1), 0.06, 0.03, "acero", lados=8)  # tapón
    # Grifo y etiqueta en la cara que da a la calle (+y).
    if con_grifo:
        sal = base + Vector((0, r, 0.22))
        b.cilindro(sal, (0, 1, 0), 0.04, 0.12, "laton", lados=8)
        b.tubo([sal + Vector((0, 0.1, 0)), sal + Vector((0, 0.16, 0)), sal + Vector((0, 0.17, -0.1))], 0.022,
               "laton", lados=6, radio_curva=0.03, pasos_curva=2, tapa_ini=False)
        b.caja(sal + Vector((0, 0.12, 0.07)), (0.03, 0.03, 0.1), "negro_mate")
    pos = base + Vector((0.0, r * 1.01, 0.6))
    b.caja(pos, (0.34, 0.006, 0.22), "papel")
    b.caja(pos + Vector((-0.2, 0.04, 0.06)), (0.1, 0.006, 0.08), "papel", giro=rot("Z", 35))
    texto(a, etiqueta, pos + Vector((0, 0.004, 0.03)), (-1, 0, 0), (0, 0, 1), (0, 1, 0), 0.05, 0.001, "tinta",
          ancho_max=0.3)
    texto(a, "COLONIA · 50 L", pos + Vector((0, 0.004, -0.05)), (-1, 0, 0), (0, 0, 1), (0, 1, 0), 0.025, 0.001,
          "tinta", ancho_max=0.3)


# ======================================================================================================
# Ventanas
# ======================================================================================================


def ventana_frontal():
    """Ventanal con cruceta de madera, marco grueso pintado y cristal ámbar; estante con dos jarras dentro."""
    pl = FRENTE
    V = VENTANA
    marco = Pieza("ventana_frontal_marco", peso_uv=1.6)
    b = marco.baja
    m = 0.2
    dF = 0.2
    caja_plano(b, pl, V["x0"] - m, V["x0"], V["z0"] - m, V["z1"] + m, 0.07, dF, "pintura_granate", sin=("+y",))
    caja_plano(b, pl, V["x1"], V["x1"] + m, V["z0"] - m, V["z1"] + m, 0.07, dF, "pintura_granate", sin=("+y",))
    caja_plano(b, pl, V["x0"], V["x1"], V["z1"], V["z1"] + m, 0.07, dF, "pintura_granate", sin=("+y", "-x", "+x"))
    caja_plano(b, pl, V["x0"], V["x1"], V["z0"] - m, V["z0"], 0.07, dF, "pintura_granate", sin=("+y", "-x", "+x"))
    t = 0.05
    for (u0, u1, v0, v1, sin) in ((V["x0"], V["x0"] + t, V["z0"], V["z1"], ("-x",)),
                                  (V["x1"] - t, V["x1"], V["z0"], V["z1"], ("+x",)),
                                  (V["x0"] + t, V["x1"] - t, V["z1"] - t, V["z1"], ("+z", "-x", "+x")),
                                  (V["x0"] + t, V["x1"] - t, V["z0"], V["z0"] + t, ("-z", "-x", "+x"))):
        caja_plano(b, pl, u0, u1, v0, v1, -MURO, 0.07, "pintura_granate", sin=sin)
    # Cruceta: cuatro paños.
    um, vm = (V["x0"] + V["x1"]) / 2, (V["z0"] + V["z1"]) / 2
    caja_plano(b, pl, um - 0.06, um + 0.06, V["z0"] + t, V["z1"] - t, -0.16, 0.0, "pintura_granate")
    caja_plano(b, pl, V["x0"] + t, um - 0.06, vm - 0.06, vm + 0.06, -0.16, 0.0, "pintura_granate", sin=("+x",))
    caja_plano(b, pl, um + 0.06, V["x1"] - t, vm - 0.06, vm + 0.06, -0.16, 0.0, "pintura_granate", sin=("-x",))
    # Alféizar exterior.
    caja_plano(b, pl, V["x0"] - 0.3, V["x1"] + 0.3, V["z0"] - m - 0.1, V["z0"] - m, 0.07, 0.42, "madera_vieja",
               sin=("+y",), giro_extra=rot("X", -3))
    for uu in (V["x0"] + 0.25, um, V["x1"] - 0.25):
        tornillo(marco, pl.p(uu, V["z1"] + m / 2, dF), pl.n, 0.018, "hierro", en_baja=False)
    cristal = Pieza("ventana_frontal_cristal", peso_uv=0.5)
    caja_plano(cristal.baja, pl, V["x0"] + t, V["x1"] - t, V["z0"] + t, V["z1"] - t, -0.13, -0.08, "vidrio_ambar")
    maceta = Pieza("maceta_pequena", peso_uv=2.0)
    cp._maceta_pequena(maceta, pl.p(V["x1"] - 0.45, V["z0"] - m + 0.0, 0.25))
    # Dentro: estante con dos jarras de cerveza y una botella.
    dentro = Pieza("ventana_jarras", peso_uv=1.8)
    db = dentro.baja
    yi = Y0 + MURO + 0.05
    zs = V["z0"] + 0.55
    db.caja_de((V["x0"] + 0.1, yi, zs - 0.05), (V["x1"] - 0.1, yi + 0.4, zs), "madera_oscura")
    for x in (V["x0"] + 0.9, V["x0"] + 1.5):
        c = Vector((x, yi + 0.18, zs))
        db.revolucion([(0.11, 0.0), (0.12, 0.02), (0.12, 0.34), (0.105, 0.34), (0.1, 0.06)], c, 8, "vidrio_jarra",
                      tapa_ini=True, oculta_ini=True, tapa_fin=True, mat_fin="cerveza")
        db.revolucion([(0.0, 0.33), (0.11, 0.33), (0.12, 0.37), (0.06, 0.4), (0.0, 0.405)], c, 8, "espuma",
                      tapa_ini=False)
        db.tubo([c + Vector((0.12, 0, 0.27)), c + Vector((0.22, 0, 0.25)), c + Vector((0.22, 0, 0.1)),
                 c + Vector((0.12, 0, 0.08))], 0.022, "vidrio_jarra", lados=5, radio_curva=0.05, pasos_curva=1)
    db.revolucion([(0.07, 0.0), (0.07, 0.3), (0.025, 0.4), (0.025, 0.5), (0.0, 0.5)], (V["x1"] - 0.6, yi + 0.2, zs),
                  8, "botella", tapa_ini=True, oculta_ini=True)
    luz = Pieza("ventana_frontal_luz_neon_calido", peso_uv=0.3)
    luz.baja.caja_de((V["x0"] + 0.1, -1.55, V["z0"] + 0.2), (V["x1"] - 0.1, -1.5, V["z1"] - 0.1), "neon_calido",
                     sin=("+y",))
    return [marco, cristal, maceta, dentro, luz]


def ventanas_laterales():
    piezas = []
    L = VLAT
    for nombre, pl, con_rejilla in (("ventana_cocina", DER, True), ("ventana_lateral", IZQ, False)):
        marco = Pieza(nombre + "_marco", peso_uv=1.2)
        t = cp._marco_ventana(marco, pl, L["u0"], L["u1"], L["v0"], L["v1"], ancho=0.13)
        caja_plano(marco.baja, pl, L["u0"] + t, L["u1"] - t, 3.95, 4.01, -0.08, -0.03, "metal_oscuro", sin=("+y",))
        cristal = Pieza(nombre + "_cristal", peso_uv=0.4)
        caja_plano(cristal.baja, pl, L["u0"] + t, L["u1"] - t, L["v0"] + t, L["v1"] - t, -0.13, -0.08,
                   "vidrio_ambar")
        luz = Pieza(nombre + "_luz_neon_calido", peso_uv=0.3)
        caja_plano(luz.baja, pl, L["u0"] + 0.1, L["u1"] - 0.1, L["v0"] + 0.4, L["v1"] - 0.3, -1.6, -1.55,
                   "neon_calido", sin=("+y",))
        piezas += [marco, cristal, luz]
        if con_rejilla:
            rej = Pieza("rejilla_cocina", peso_uv=1.5)
            rb = rej.baja
            u0, u1, v0, v1 = L["u0"] - 0.25, L["u1"] + 0.25, 1.98, 2.52
            caja_plano(rb, pl, u0, u1, v0, v1, PANEL, PANEL + 0.01, "hollin_rejilla",
                       sin=("+y", "-x", "+x", "-z", "+z"))
            m = 0.06
            for (a0, a1, b0, b1) in ((u0, u0 + m, v0, v1), (u1 - m, u1, v0, v1), (u0 + m, u1 - m, v0, v0 + m),
                                     (u0 + m, u1 - m, v1 - m, v1)):
                caja_plano(rb, pl, a0, a1, b0, b1, PANEL, PANEL + 0.07, "metal_oscuro", sin=("+y",))
            for k in range(5):
                vv = v0 + m + 0.03 + k * (v1 - v0 - 2 * m - 0.06) / 4
                caja_plano(rb, pl, u0 + m, u1 - m, vv - 0.035, vv + 0.035, PANEL + 0.02, PANEL + 0.05, "metal_oscuro",
                           sin=("+y", "-x", "+x"), giro_extra=rot("X", 35))
            piezas.append(rej)
        else:
            piezas.append(_contraventana_lateral(pl, L))
    return piezas


def _contraventana_lateral(pl, L):
    """Contraventana de tablas medio abierta (65°), con bisagras y pernios."""
    ue = L["u0"] - 0.17
    piv = pl.p(ue, L["v0"] - 0.12, 0.17)
    p = Pieza("ventana_lateral_contraventana", pivote=piv, peso_uv=1.5)
    b = p.baja
    ancho = L["u1"] - L["u0"] + 0.3
    v0, v1 = L["v0"] - 0.12, L["v1"] + 0.12
    for k in range(3):
        ua = ue + 0.02 + k * (ancho - 0.02) / 3
        caja_plano(b, pl, ua + 0.01, ua + (ancho - 0.02) / 3 - 0.01, v0, v1, 0.17, 0.24, "pintura_granate",
                   sin=("-z",))
    for vt in (v0 + 0.25, v1 - 0.25):
        caja_plano(b, pl, ue + 0.05, ue + ancho - 0.04, vt - 0.08, vt + 0.08, 0.24, 0.29, "pintura_granate",
                   sin=("+y",))
        caja_plano(b, pl, ue - 0.02, ue + 0.4, vt - 0.04, vt + 0.04, 0.29, 0.305, "hierro", sin=("+y",))
        b.cilindro(pl.p(ue, vt - 0.06, 0.2), (0, 0, 1), 0.035, 0.12, "hierro", lados=6)
    giro = Matrix.Translation(piv) @ Matrix.Rotation(math.radians(65), 4, "Z") @ Matrix.Translation(-piv)
    b.transformar(b.bm.verts, giro)
    p.alta.transformar(p.alta.bm.verts, giro)
    p.extra["angulo_abierta"] = 65
    return p


# ======================================================================================================
# Carteles, pizarras y tablón
# ======================================================================================================


def cartel():
    """Cartel tallado «LA ÚLTIMA ÓRBITA»: tablón grueso biselado colgado de cadenas de una horca sobre el porche."""
    tabla = Pieza("cartel", peso_uv=2.4)
    horca = Pieza("cartel_soporte", peso_uv=1.4)
    focos = Pieza("cartel_focos", peso_uv=1.4)
    neon = Pieza("cartel_focos_neon", peso_uv=0.4)
    xc = (PUERTA["x0"] + PUERTA["x1"]) / 2
    yc = -4.25
    w, h, t = 4.7, 1.05, 0.16
    zc = z_porche(yc) + 0.75
    # Tablón: anillos de detrás, del canto y de delante (con chaflán), en el plano XZ.
    def anillo(dy, ins):
        return [Vector((xc + x, yc + dy, zc + z)) for x, z in
                ((-w / 2 + ins, -h / 2 + ins), (w / 2 - ins, -h / 2 + ins), (w / 2 - ins, h / 2 - ins),
                 (-w / 2 + ins, h / 2 - ins))]
    tb = tabla.baja
    tb.loft([anillo(t / 2, 0.035), anillo(t / 2 - 0.035, 0.0), anillo(-t / 2 + 0.035, 0.0), anillo(-t / 2, 0.035)],
            "cartel_madera", suave=False, tapa_ini=True, tapa_fin=True)
    tb.recalcular(tb.ultimas)
    texto(tb, "LA ÚLTIMA ÓRBITA", Vector((xc, yc - t / 2, zc + 0.06)), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.4, 0.03,
          "dorado", ancho_max=w - 0.5)
    texto(tabla.alta, "DESDE EL AÑO 1 DE LA COLONIA", Vector((xc, yc - t / 2, zc - 0.36)), (1, 0, 0), (0, 0, 1),
          (0, -1, 0), 0.07, 0.004, "dorado", ancho_max=w - 1.5)
    for sx in (-1, 1):  # estrellas talladas a los lados (malla alta)
        cxs = xc + sx * (w / 2 - 0.22)
        pts = []
        for k in range(10):
            r = 0.1 if k % 2 == 0 else 0.045
            ang = math.pi / 2 + k * math.pi / 5
            pts.append((cxs + math.cos(ang) * r, zc + math.sin(ang) * r))
        tabla.alta.placa(pts, Vector((0, yc - t / 2, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)),
                         0.01, "dorado")
    # Horca de hierro sobre la chapa del porche: dos montantes y travesaño con ganchos.
    hb = horca.baja
    zt = zc + h / 2 + 0.45
    for sx in (-1, 1):
        x = xc + sx * (w / 2 + 0.25)
        y = yc + 0.25
        zr = z_porche(y)
        hb.caja(Vector((x, y, (zr + zt) / 2)), (0.07, 0.07, zt - zr), "hierro")
        hb.caja(Vector((x, y, zr + 0.015)), (0.22, 0.22, 0.03), "hierro")
        hb.tubo([Vector((x, y, zt - 0.5)), Vector((x, y - 0.25, zt - 0.02))], 0.018, "hierro", lados=4)
    hb.caja(Vector((xc, yc + 0.25, zt)), (w + 0.62, 0.08, 0.08), "hierro")
    hb.caja(Vector((xc, yc + 0.1, zt)), (w + 0.4, 0.3, 0.05), "hierro")
    # Cadenas: eslabones de verdad, alternando la orientación.
    for sx in (-1, 1):
        x = xc + sx * (w / 2 - 0.35)
        z = zt - 0.04
        hb.tubo([Vector((x, yc - 0.0, zt - 0.02)), Vector((x, yc, zt - 0.08)), Vector((x + 0.03, yc, zt - 0.1))], 0.014,
                "hierro", lados=4)
        k = 0
        while z - 0.09 > zc + h / 2 + 0.02:
            zz = z - 0.05
            if k % 2 == 0:
                lazo = [Vector((x + math.sin(a_) * 0.035, yc, zz + math.cos(a_) * 0.065)) for a_ in
                        [math.tau * i / 6 for i in range(7)]]
            else:
                lazo = [Vector((x, yc + math.sin(a_) * 0.035, zz + math.cos(a_) * 0.065)) for a_ in
                        [math.tau * i / 6 for i in range(7)]]
            hb.tubo(lazo, 0.011, "hierro", lados=3, tapa_ini=False, tapa_fin=False)
            z -= 0.11
            k += 1
        hb.cilindro(Vector((x, yc, zc + h / 2 - 0.02)), (0, 0, 1), 0.03, 0.05, "hierro", lados=6)
    # Focos en los extremos del travesaño apuntando al tablón.
    fb = focos.baja
    for sx in (-1, 1):
        P0 = Vector((xc + sx * 1.3, yc + 0.1, zt + 0.02))
        P1 = Vector((xc + sx * 1.3, yc - 0.45, zt + 0.12))
        fb.tubo([P0, P1], 0.018, "metal_oscuro", lados=6, tapa_ini=False)
        apunta = (Vector((xc + sx * 1.1, yc - t / 2, zc)) - P1).normalized()
        cab = P1 + apunta * 0.03
        fb.revolucion([(0.0, -0.04), (0.05, -0.035), (0.07, 0.0), (0.07, 0.13), (0.06, 0.13)], cab, 10, "metal_oscuro",
                      eje=apunta, tapa_ini=False, tapa_fin=False)
        neon.baja.cilindro(cab + apunta * 0.12, apunta, 0.06, 0.01, "neon", lados=10)
    focos.extra["luces"] = [[xc - 1.3, yc - 0.45, zt + 0.12], [xc + 1.3, yc - 0.45, zt + 0.12]]
    return [tabla, horca, focos, neon]


def _pizarra_pared(nombre, pl, u0, u1, v0, v1, lineas, peso=3.0):
    p = Pieza(nombre, peso_uv=peso)
    b, a = p.baja, p.alta
    d0 = 0.13
    m = 0.07
    caja_plano(b, pl, u0, u1, v0, v1, d0, d0 + 0.03, "pizarra", sin=("+y",))
    for (a0, a1, b0, b1) in ((u0 - 0.02, u1 + 0.02, v1 - 0.01, v1 + m), (u0 - 0.02, u1 + 0.02, v0 - m, v0 + 0.01),
                             (u0 - m, u0 + 0.01, v0, v1), (u1 - 0.01, u1 + m, v0, v1)):
        caja_plano(b, pl, a0, a1, b0, b1, d0, d0 + 0.07, "madera_oscura", sin=("+y",))
    caja_plano(b, pl, u0 + 0.1, u1 - 0.1, v0 - 0.1, v0 - 0.07, d0 + 0.03, d0 + 0.13, "madera_oscura")  # repisa tiza
    a.caja(pl.p((u0 + u1) / 2 - 0.2, v0 - 0.06, d0 + 0.08), (0.08, 0.025, 0.025), "tiza", giro=pl.giro)
    uc = (u0 + u1) / 2
    for txt, dv, alto in lineas:
        texto(a, txt, pl.p(uc, v1 - dv, d0 + 0.03), pl.u, pl.v, pl.n, alto, 0.002, "tiza", ancho_max=u1 - u0 - 0.16)
    for uu in (u0 - m / 2, u1 + m / 2):
        tornillo(p, pl.p(uu, (v0 + v1) / 2, d0 + 0.07), pl.n, 0.016, "hierro", en_baja=False)
    return p


def pizarra_menu():
    return _pizarra_pared("pizarra_menu", FRENTE, -1.55, -0.3, 2.45, 4.0,
                          [("HOY:", 0.2, 0.14), ("Estofado", 0.45, 0.09), ("del minero", 0.62, 0.09),
                           ("5 créditos", 0.86, 0.1), ("Cerveza  2c", 1.12, 0.07), ("Pan + queso  3c", 1.3, 0.06)])


def tablon():
    """Tablón de corcho con cuatro papeles clavados con chinchetas (una esquina levantada en alguno)."""
    p = Pieza("tablon_anuncios", peso_uv=2.4)
    pl = FRENTE
    b, a = p.baja, p.alta
    u0, u1, v0, v1 = 3.05, 4.55, 2.6, 4.05
    d0 = 0.13
    caja_plano(b, pl, u0, u1, v0, v1, d0, d0 + 0.04, "corcho", sin=("+y",))
    m = 0.08
    for (a0, a1, b0, b1) in ((u0 - m, u1 + m, v1, v1 + m), (u0 - m, u1 + m, v0 - m, v0), (u0 - m, u0, v0, v1),
                             (u1, u1 + m, v0, v1)):
        caja_plano(b, pl, a0, a1, b0, b1, d0, d0 + 0.07, "madera_vieja", sin=("+y",))
    papeles = [(3.42, 3.6, 0.5, 0.6, -5, "SE BUSCA", ["minero con", "experiencia", "turno de noche"]),
               (4.15, 3.7, 0.5, 0.45, 4, "VENDO", ["speeder bike", "pregunte en", "la barra"]),
               (3.5, 2.95, 0.55, 0.5, 3, "AVISO", ["toque de queda", "en la tormenta"]),
               (4.2, 3.0, 0.42, 0.5, -7, "TORNEO", ["de cartas", "sábado", "noche"])]
    for k, (uc, vc, w, h, ang, titulo, lineas) in enumerate(papeles):
        g = pl.giro @ rot("Y", -ang)
        centro = pl.p(uc, vc, d0 + 0.045)
        b.caja(centro, (w, 0.004, h), "papel", giro=g)
        u = g @ Vector((1, 0, 0))
        v = g @ Vector((0, 0, 1))
        n = pl.n
        o = centro + n * 0.003
        texto(a, titulo, o + v * (h / 2 - 0.1), u, v, n, 0.06, 0.001, "tinta_roja" if k % 2 == 0 else "tinta",
              ancho_max=w - 0.1)
        for j, ln in enumerate(lineas):
            texto(a, ln, o + v * (h / 2 - 0.2 - j * 0.07), u, v, n, 0.035, 0.001, "tinta", ancho_max=w - 0.1)
        # Chincheta: cabeza de colores y aguja.
        pin = centro + v * (h / 2 - 0.04) + n * 0.002
        p.baja.revolucion([(0.022, 0.0), (0.022, 0.01), (0.016, 0.016), (0.008, 0.035), (0.0, 0.037)], pin, 6,
                          ("pintura_roja", "pintura_naranja", "pintura_gris", "pintura_roja")[k], eje=n, tapa_ini=True)
        if k == 1:  # esquina levantada
            b.caja(centro + u * (w / 2 - 0.05) - v * (h / 2 - 0.05) + n * 0.02, (0.1, 0.004, 0.1), "papel",
                   giro=g @ rot("X", 35))
    return p


# ======================================================================================================
# Fontanería, electricidad e interior
# ======================================================================================================


def bajante(salida):
    """Bajante grueso (la cocina tira mucha agua) en la esquina de atrás a la izquierda, con tres abrazaderas."""
    p = Pieza("bajante", peso_uv=1.2)
    b, a = p.baja, p.alta
    x, y, z = salida
    xw = -MX + 0.4
    yw = Y1 + 0.3
    r = 0.13
    camino = [(x, y, z + 0.1), (x, y, z - 0.25), (xw, yw, z - 0.6), (xw, yw, 0.95), (xw, yw + 0.3, 0.55)]
    b.tubo(camino, r, "metal_oscuro", lados=8, radio_curva=0.22, pasos_curva=3, tapa_ini=False, tapa_fin=False)
    fin = Vector(camino[-1])
    dv = (Vector(camino[-1]) - Vector(camino[-2])).normalized()
    b.revolucion([(r, 0), (r * 0.8, 0), (r * 0.8, -0.16), (0.0, -0.16)], fin, 8, "metal_oscuro", eje=dv,
                 tapa_ini=False, tapa_fin=False, giro=math.pi / 8, mats_tramo=["metal_oscuro", "negro_mate",
                                                                               "negro_mate"])
    for zz in (4.6, 3.0, 1.45):
        b.revolucion([(r + 0.022, 0), (r + 0.022, 0.08)], (xw, yw, zz - 0.04), 8, "hierro", giro=math.pi / 8)
        b.caja_de((xw - 0.02, Y1 + 0.12, zz - 0.03), (xw + 0.02, yw - r, zz + 0.03), "hierro")
        b.caja_de((xw - 0.1, Y1 + 0.1, zz - 0.1), (xw + 0.1, Y1 + 0.13, zz + 0.1), "hierro", sin=("-y",))
        for dx in (-0.06, 0.06):
            tornillo(p, (xw + dx, Y1 + 0.13, zz), (0, 1, 0), 0.018, "acero", en_baja=False)
    p.extra["pie"] = [xw, yw + 0.4, 0.0]
    return p


def medidor():
    """Contador grande (la taberna gasta mucho) en el lateral derecho, cerca de atrás."""
    pl = DER
    u0, u1, v0, v1 = 1.55, 2.45, 2.7, 3.95
    d0, d1 = 0.13, 0.42
    caja = Pieza("medidor", peso_uv=1.6)
    b = caja.baja
    caja_plano(b, pl, u0, u1, v0, v1, d0, d1, "pintura_gris", sin=("+y",), mats={"-y": "negro_mate"})
    for uu in ((u0 + u1) / 2 - 0.2, (u0 + u1) / 2 + 0.2):
        b.tubo([pl.p(uu, v0, 0.27), pl.p(uu, 1.95, 0.27), pl.p(uu, 1.9, 0.12)], 0.04, "metal_oscuro", lados=6,
               radio_curva=0.05, tapa_ini=False, tapa_fin=False)
    piv = pl.p(u0, v0, d1 + 0.012)
    puerta = Pieza("medidor_puerta", pivote=piv, peso_uv=1.8)
    pb = puerta.baja
    ext = rect(u0, u1, v0, v1)
    uc = (u0 + u1) / 2
    hueco = rect(uc - 0.2, uc + 0.2, 3.5, 3.72)
    pb.anillo_placa(ext, hueco, pl.p(0, 0, d1), pl.u, pl.v, pl.n, 0.028, "pintura_gris")
    pb.cara_con_huecos([pl.p(u, v, d1) for u, v in ext], [[pl.p(u, v, d1) for u, v in hueco]], "pintura_gris", -pl.n)
    caja_plano(pb, pl, u1 - 0.08, u1 - 0.03, 3.1, 3.35, d1 + 0.028, d1 + 0.06, "metal_oscuro", sin=("+y",))
    for vv in (v0 + 0.15, v1 - 0.15):
        pb.cilindro(pl.p(u0, vv - 0.08, d1 + 0.012), (0, 0, 1), 0.018, 0.16, "metal_oscuro", lados=6)
    puerta.alta.placa([(uc - 0.12, 2.9), (uc + 0.12, 2.9), (uc, 3.1)], pl.p(0, 0, d1 + 0.028), pl.u, pl.v, pl.n,
                      0.002, "pegatina")
    pant = Pieza("medidor_pantalla_neon", peso_uv=0.6)
    caja_plano(pant.baja, pl, uc - 0.17, uc + 0.17, 3.53, 3.69, d1 - 0.02, d1 + 0.004, "neon", sin=("+y",))
    caja.extra["salida_cable"] = list(pl.p(uc, v1, 0.27))
    return [caja, puerta, pant]


def cable(salida):
    """Cable del medidor hasta el alero (va a la jarra de neón del tejado)."""
    p = Pieza("cable_electrico", peso_uv=1.0)
    b = p.baja
    x, y, z = salida
    xw = MX + 0.24
    ye = Y1 + VUELO_Y
    puntos = [(xw, y, z), (xw, y, 4.4), (xw, y + 0.5, 5.2), (xw, Y1 - 0.2, z_muro(Y1 - 0.2) - 0.1),
              (MX + VUELO_X + 0.06, Y1 + 0.1, z_tejado(Y1 + 0.1) - 0.1),
              (MX + VUELO_X + 0.06, Y1 + 0.1, z_tejado(Y1 + 0.1) + 0.12), (MX - 0.2, Y1 - 0.2, z_tejado(Y1 - 0.2) + 0.12),
              (0.9, YC + 0.4, z_tejado(YC + 0.4) + 0.1), (0.75, YC + 0.08, CUMBRE + 0.12)]
    b.tubo(puntos, 0.026, "goma", lados=5, radio_curva=0.12, pasos_curva=2)
    for zz in (4.0, 5.0):
        b.caja_de((MX + 0.12, y - 0.05, zz - 0.07), (MX + 0.15, y + 0.05, zz + 0.07), "metal_oscuro", sin=("-x",))
        b.tubo([(MX + 0.14, y, zz - 0.03), (xw + 0.04, y, zz - 0.035), (xw + 0.07, y, zz + 0.03)], 0.012,
               "metal_oscuro", lados=4, radio_curva=0.03, pasos_curva=2)
    return p


def interior():
    """Lo que se ve por las puertas de saloon: barra, botellero, taburetes, suelo y techo."""
    p = Pieza("interior", peso_uv=0.7)
    b = p.baja
    b.caja_de((-MX + MURO, Y0 + MURO, ALERO_Z - 0.05), (MX - MURO, Y1 - MURO, ALERO_Z), "interior",
              sin=("+z", "-x", "+x", "-y", "+y"))
    b.caja_de((-MX + MURO, Y0 + MURO, SUELO - 0.02), (MX - MURO, Y1 - MURO, SUELO), "madera_porche",
              sin=("-z", "-x", "+x", "-y", "+y"))
    # Barra al fondo.
    b.caja_de((-1.8, 1.4, SUELO), (3.6, 2.0, SUELO + 1.7), "madera_saloon", sin=("-z", "+y"))
    b.caja_de((-1.9, 1.3, SUELO + 1.7), (3.7, 2.05, SUELO + 1.8), "madera_oscura")
    b.caja_de((-1.8, 1.32, SUELO + 0.15), (3.6, 1.36, SUELO + 0.2), "laton")  # reposapiés
    # Botellero en la pared del fondo.
    for z in (SUELO + 2.4, SUELO + 3.2):
        b.caja_de((-1.5, Y1 - MURO - 0.35, z - 0.05), (3.3, Y1 - MURO, z), "madera_oscura", sin=("+y",))
    rnd = random.Random(14)
    for k in range(6):
        x = -1.2 + k * 0.8
        z = SUELO + 2.4 if k % 2 == 0 else SUELO + 3.2
        mat = ("botella", "vidrio_jarra", "botella")[k % 3]
        b.revolucion([(0.08, 0.0), (0.08, 0.32), (0.03, 0.42), (0.03, 0.55), (0.0, 0.55)],
                     (x + rnd.uniform(-0.08, 0.08), Y1 - MURO - 0.17, z), 6, mat, tapa_ini=False)
    # Taburetes.
    for x in (0.4, 2.2):
        c = Vector((x, 1.0, SUELO))
        b.revolucion([(0.03, 0.0), (0.03, 1.15), (0.2, 1.2), (0.2, 1.3), (0.0, 1.32)], c, 6, "madera_saloon",
                     tapa_ini=False)
        b.revolucion([(0.18, 0.0), (0.18, 0.03), (0.0, 0.04)], c, 8, "hierro", tapa_ini=False)
    return p


# ======================================================================================================
# Entorno
# ======================================================================================================


def escalones():
    """Dos escalones de piedra a todo lo ancho del porche, gastados en el centro, con musgo en las esquinas."""
    alto = cm2._losa_gastada("escalon_alto", -MX + 0.1, MX - 0.1, PORCHE_Y - 0.42, PORCHE_Y, 0.66, 0.02,
                             ((PUERTA["x0"] + PUERTA["x1"]) / 2, PORCHE_Y - 0.21), peso=1.4, semilla=4,
                             mat="losa_taberna")
    bajo = cm2._losa_gastada("escalon_bajo", -MX + 0.1, MX - 0.1, PORCHE_Y - 0.84, PORCHE_Y - 0.42, 0.33, 0.024,
                             ((PUERTA["x0"] + PUERTA["x1"]) / 2, PORCHE_Y - 0.63), peso=1.4, semilla=5,
                             mat="losa_taberna")
    return [alto, bajo]


def farola():
    """Farola frente a la taberna: basa, fuste de fundición con collarines, brazo y farol con bombilla."""
    p = Pieza("farola", peso_uv=1.5)
    neon = Pieza("farola_bombilla_neon", peso_uv=0.4)
    cristal = Pieza("farola_cristal", peso_uv=0.4)
    b = p.baja
    c = Vector((7.6, -5.9, 0.0))
    alto = 5.0
    b.revolucion([(0.3, 0.0), (0.3, 0.12), (0.22, 0.18), (0.13, 0.35), (0.09, 0.45), (0.075, alto - 0.5),
                  (0.1, alto - 0.45), (0.1, alto - 0.38), (0.06, alto - 0.33)], c, 8, "hierro", tapa_ini=False,
                 tapa_fin=True)
    for z in (1.2, 2.6):
        b.revolucion([(0.08, z - 0.04), (0.1, z - 0.02), (0.1, z + 0.02), (0.08, z + 0.04)], c, 10, "hierro",
                      tapa_ini=False, tapa_fin=False)
    # Farol arriba: tejadillo, montantes y base.
    zc = c.z + alto - 0.05
    b.revolucion([(0.17, 0.0), (0.24, -0.02), (0.24, 0.0), (0.0, 0.22)][::-1][::-1], (c.x, c.y, zc + 0.3), 6,
                 "hierro", suave=False, tapa_ini=True)
    b.revolucion([(0.0, -0.05), (0.14, -0.05), (0.18, 0.0)], (c.x, c.y, zc - 0.25), 6, "hierro", suave=False,
                 tapa_fin=True)
    for k in range(6):
        ang = math.tau * k / 6
        b.caja(Vector((c.x + math.cos(ang) * 0.17, c.y + math.sin(ang) * 0.17, zc + 0.03)), (0.025, 0.025, 0.56),
               "hierro", giro=rot("Z", math.degrees(ang)))
    cristal.baja.revolucion([(0.16, -0.25), (0.16, 0.3), (0.15, 0.3), (0.15, -0.25)], (c.x, c.y, zc), 6,
                            "vidrio_ambar", tapa_ini=False, tapa_fin=False)
    neon.baja.revolucion([(0.0, -0.12), (0.06, -0.09), (0.085, 0.0), (0.06, 0.1), (0.03, 0.14), (0.03, 0.22)],
                         (c.x, c.y, zc), 8, "neon", tapa_fin=True)
    p.extra["luz"] = [c.x, c.y, zc]
    return [p, neon, cristal]


def speeder():
    """Speeder bike aparcada junto al porche, apoyada en su pata: cuerpo, asiento, manillar y dos discos hover."""
    p = Pieza("speeder_bike", peso_uv=1.7)
    neon = Pieza("speeder_bike_neon", peso_uv=0.3)
    b, a = p.baja, p.alta
    o = Vector((-8.0, -4.2, 0.0))
    inclinacion = rot("Y", 0) @ rot("X", 9)   # apoyada en la pata (se inclina hacia -y)
    rumbo = rot("Z", 12)
    M = rumbo @ inclinacion

    def P(x, y, z):
        return o + M @ Vector((x, y, z))

    # Cuerpo: lofts de secciones a lo largo de x.
    secciones = [(-1.15, 0.12, 0.1, 0.95), (-0.9, 0.22, 0.17, 0.98), (-0.3, 0.27, 0.22, 1.0), (0.3, 0.25, 0.2, 1.02),
                 (0.85, 0.18, 0.15, 1.04), (1.2, 0.07, 0.07, 1.02)]
    anillos = []
    for x, ry, rz, zc in secciones:
        anillos.append([P(x, math.cos(t) * ry, zc + math.sin(t) * rz) for t in [math.tau * i / 8 for i in range(8)]])
    b.loft(anillos, "pintura_speeder", tapa_ini=True, tapa_fin=True)
    # Asiento.
    b.loft([[P(x, math.cos(t) * 0.16, 1.2 + math.sin(t) * 0.07 + 0.04) for t in [math.tau * i / 8 for i in range(8)]]
            for x in (-0.65, -0.1, 0.15)], "cuero", tapa_ini=True, tapa_fin=True)
    # Manillar y horquilla.
    b.tubo([P(0.75, 0.0, 1.2), P(0.85, 0.0, 1.5)], 0.04, "metal_oscuro", lados=6)
    b.tubo([P(0.8, -0.42, 1.55), P(0.86, -0.3, 1.5), P(0.86, 0.3, 1.5), P(0.8, 0.42, 1.55)], 0.025, "metal_oscuro",
           lados=6, radio_curva=0.06, pasos_curva=2)
    for s in (-1, 1):
        b.cilindro(P(0.8, s * 0.42, 1.55), M @ Vector((0, s, 0)), 0.035, 0.1, "goma", lados=6)
    # Dos discos hover horizontales debajo (delante y detrás), con la luz hacia el suelo y en el canto.
    for x in (-0.75, 0.75):
        cc = P(x, 0.0, 0.42)
        eje = M @ Vector((0, 0, 1))
        b.revolucion([(0.0, -0.05), (0.42, -0.05), (0.46, 0.0), (0.42, 0.05), (0.14, 0.08), (0.0, 0.08)], cc, 12,
                     "metal_speeder", eje=eje)
        neon.baja.revolucion([(0.28, -0.055), (0.38, -0.055)], cc, 12, "neon", eje=eje, tapa_ini=False,
                             tapa_fin=False)
        neon.baja.revolucion([(0.465, -0.015), (0.465, 0.015)], cc, 12, "neon", eje=eje, tapa_ini=False,
                             tapa_fin=False)
        b.tubo([P(x, 0.0, 0.5), P(x * 0.85, 0.0, 0.92)], 0.06, "metal_oscuro", lados=6)
    # Pata de cabra hasta el suelo.
    b.tubo([P(-0.1, -0.18, 0.88), Vector((o.x - 0.1, o.y - 0.45, 0.02))], 0.025, "metal_oscuro", lados=6)
    # Faro delantero y detalles (malla alta).
    b.revolucion([(0.0, 0.0), (0.07, 0.01), (0.08, 0.06), (0.0, 0.07)], P(1.18, 0, 1.02), 8, "aluminio",
                 eje=M @ Vector((1, 0, 0)))
    for k in range(6):
        a.caja(P(-0.6 + k * 0.2, 0.0, 1.2), (0.01, 0.45, 0.1), "metal_oscuro", giro=M)
    texto(a, "OB-7", P(0.2, -0.255, 0.98), M @ Vector((1, 0, 0)), M @ Vector((0, 0, 1)), M @ Vector((0, -1, 0)), 0.08,
          0.002, "rotulo", ancho_max=0.4)
    return [p, neon]


# ======================================================================================================
# Todo junto
# ======================================================================================================


def construir():
    tej = tejado()
    piezas = [cimiento(), muros(), tej, chimenea(), aspiradores()] + cartel_techo()
    piezas += [porche_suelo(), porche_estructura(), porche_tejado(), barandillas()]
    ban = banco()
    piezas += [ban, barril_maceta(), cenicero(), campana()] + faroles()
    piezas += puertas_saloon() + puerta_trasera() + muelle_carga()
    piezas += ventana_frontal() + ventanas_laterales()
    piezas += cartel() + [pizarra_menu(), tablon()]
    piezas.append(bajante(tej.extra["canalon_bajada"]))
    med = medidor()
    piezas += med + [cable(med[0].extra["salida_cable"]), interior()]
    piezas += escalones() + farola() + speeder()
    D = PUERTA
    puerta_c = ((D["x0"] + D["x1"]) / 2, Y0 - 0.1, 3.0)
    P = {
        "manija": puerta_c,
        "manija_agarre": puerta_c,
        "manija_lateral": puerta_c,
        "zocalo_z": PIEDRA_Z,
        "puerta_z0": HOJAS_Z[0],
        "puerta_suelo": (puerta_c[0], (Y0 + PORCHE_Y) / 2, SUELO),
        "escalon_centro": (puerta_c[0], PORCHE_Y - 0.4, 0.66),
        "felpudo_centro": (puerta_c[0], Y0 - 0.5, SUELO),
        "bajante_pie": (-MX + 0.4, Y1 + 0.7, 0.0),
        "chimenea_boca": 9.6,
        "pico_agarre": (0.0, 0.1),
        "toldo_frente_y": -99.0,
        "silla_asiento": tuple(ban.extra["asiento"]),
        "puerta_centro": puerta_c,
        "porche_y": (Y0, PORCHE_Y),
    }
    return piezas, P
