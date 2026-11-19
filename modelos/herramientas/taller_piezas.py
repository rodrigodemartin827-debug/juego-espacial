"""
Piezas del taller de reparaciones del pueblo. Todo en STUDS, con la fachada mirando a -Y (el «delante» de Roblox).

Nave de chapa ancha y baja (12 × 9 studs de muros) con techo curvo de hangar, sobre una losa de hormigón a ras de
suelo (los vehículos entran sin escalón). Lo lleva un mecánico veterano: dentro y fuera hay caos, pero ordenado.

  fachada (-Y), de izquierda a derecha vista desde delante:
      soldadora en el suelo | PORTÓN corredero (se abre hacia la izquierda) con la rampa de chapa estriada delante,
      dos focos cian y la pluma con la cadena encima | banco de trabajo con el tornillo de banco y, encima, el panel
      perforado de herramientas con sus siluetas pintadas | cuadro eléctrico abierto, cartel de ALTO VOLTAJE y el
      medidor de energía. En el arco, el letrero «TALLER».
  lateral derecho (+X): compresor con la manguera en su gancho, puerta del mecánico con el cartel del horario y la
      carretilla apoyada.
  lateral izquierdo (-X): bidones de aceite, combustible y refrigerante; ventana de cristal armado; piezas que
      esperan reparación (tubos, una chapa curva y una turbina rota).
  detrás (+Y): ventana pequeña y el extractor de aire redondo, con hollín alrededor.
  techo: bóveda de chapa con nervios, dos lucernarios y el extractor industrial con sus aspas.

Cada función crea una o varias `Pieza` (malla baja del juego + detalles de la malla alta para hornear). Lo que se
anima va aparte con el pivote donde se mueve: el portón (desliza), la puerta lateral (bisagras), la puerta del
cuadro eléctrico (bisagras) y las aspas de los dos extractores (giran).
"""

import math
import random

from mathutils import Matrix, Vector

import casa_piezas as cp
from casa_malla import Pieza, base_de, rot
from casa_piezas import caja_plano, tornillo
from comerciante_piezas import texto

# ======================================================================================================
# Medidas (studs)
# ======================================================================================================

MX = 6.0                 # cara exterior del alma de los muros laterales
Y0, Y1 = -4.5, 4.5       # cara exterior de la fachada y del muro de atrás
MURO = 0.3               # grosor del alma
ZOC = 1.5                # alto del zócalo de hormigón
ZOC_D = 0.12             # lo que sale el zócalo del alma (poco: el portón pasa por delante)
LOSA_Z = 0.08            # cara de arriba de la losa (el suelo de dentro es la misma losa: sin escalón)
LOSA = dict(x0=-7.2, x1=7.2, y0=-6.8, y1=5.1)
EAVE = 4.35              # alto del techo en la cara de los muros laterales
CUMBRE = 6.3             # alto del techo en el centro
RADIO = (MX ** 2 + (CUMBRE - EAVE) ** 2) / (2 * (CUMBRE - EAVE))
TG = 0.08                # grosor de la chapa del techo
VUELO_X, VUELO_Y = 0.35, 0.32
XE = MX + VUELO_X
YE0, YE1 = Y0 - VUELO_Y, Y1 + VUELO_Y
# Chapa grecada de los muros (nervios verticales): valle y cresta (distancia al alma) y paso.
ONDA_V, ONDA_C, PASO = 0.02, 0.10, 0.6
# Portón corredero.
HUECO = dict(x0=-3.1, x1=-0.1, z1=4.0)
HOJA = dict(x0=-3.25, x1=0.05, z0=0.2, z1=4.15, d0=0.18, d1=0.32)   # d: distancia a la cara del alma
CORRIDA = 3.05           # lo que se desliza hacia -X para abrirse
RAIL = dict(x0=-6.2, x1=0.3, z=4.42, d=0.25)                         # z: cara de arriba del raíl
RUEDA_R = 0.13
# Puerta lateral (muro derecho, u = +y), ventanas y extractor de atrás.
PUERTA_L = dict(u0=-0.2, u1=1.5, v1=3.75)
HOJA_L = dict(u0=-0.14, u1=1.44, v0=LOSA_Z + 0.06, v1=3.7)
VENT_L = dict(u0=-0.9, u1=0.9, v0=2.15, v1=3.35)      # muro izquierdo (u = -y)
VENT_T = dict(u0=1.45, u1=2.45, v0=2.6, v1=3.4)       # muro de atrás (u = -x)
VENTI = dict(u0=-2.5, u1=-1.2, v0=2.25, v1=3.55)      # placa del extractor de atrás (u = -x)
VENTI_C = ((VENTI["u0"] + VENTI["u1"]) / 2, (VENTI["v0"] + VENTI["v1"]) / 2)
# Techo: costuras (nervios) y lucernarios entre ellas; extractor.
COSTURAS = (-4.0, -2.4, -0.8, 0.8, 2.4, 4.0)
LUCERNARIOS = [(-3.3, -0.9, -2.25, -0.95), (-3.3, -0.9, 0.95, 2.25)]  # x0, x1, y0, y1 del hueco
EXTRACTOR = Vector((2.7, 3.2, 0.0))
# Fachada derecha.
BANCO = dict(x0=0.6, x1=3.3, y0=Y0 - ONDA_C - 1.0, z=1.75)
PANEL_H = dict(x0=0.62, x1=3.28, z0=2.15, z1=3.75, d=0.14)
CUADRO = dict(x0=3.75, x1=4.85, z0=1.9, z1=3.4, d0=0.12, d1=0.5)
MEDIDOR = dict(x0=5.1, x1=5.75, z0=2.3, z1=3.2)


def z_arco(x):
    """Cara de arriba de la chapa del techo (bóveda: arco de circunferencia a lo ancho)."""
    return CUMBRE - RADIO + math.sqrt(max(RADIO ** 2 - x ** 2, 0.0))


def z_muro(x):
    """Alto de los muros (justo debajo de la chapa del techo)."""
    return z_arco(x) - TG - 0.01


def normal_arco(x):
    """Normal de la bóveda en x (en el plano XZ)."""
    return Vector((x, 0.0, z_arco(x) - (CUMBRE - RADIO))).normalized()


FRENTE = cp.Plano((0, Y0, 0), (0, -1, 0))   # u = +x
FONDO = cp.Plano((0, Y1, 0), (0, 1, 0))     # u = -x
IZQ = cp.Plano((-MX, 0, 0), (-1, 0, 0))     # u = -y
DER = cp.Plano((MX, 0, 0), (1, 0, 0))       # u = +y
Z_LAT = z_muro(MX)


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def capsula(a, b, r, n=5):
    """Polígono 2D (u, v) de una cápsula entre a y b con radio r (para herramientas y sus siluetas)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    if d.length < 1e-6:
        return [(a.x + math.cos(t) * r, a.y + math.sin(t) * r) for t in [math.tau * k / (2 * n) for k in range(2 * n)]]
    ang = math.atan2(d.y, d.x)
    pts = []
    for k in range(n + 1):
        t = ang - math.pi / 2 + math.pi * k / n
        pts.append((b.x + math.cos(t) * r, b.y + math.sin(t) * r))
    for k in range(n + 1):
        t = ang + math.pi / 2 + math.pi * k / n
        pts.append((a.x + math.cos(t) * r, a.y + math.sin(t) * r))
    return pts


def _perfil_onda(u0, u1):
    """Puntos (u, d) de la chapa grecada entre u0 y u1, con la fase global (los tramos encajan entre sí)."""
    corte = [0.0, 0.22, 0.3, 0.52, 0.6]
    prof = [ONDA_V, ONDA_V, ONDA_C, ONDA_C, ONDA_V]

    def d(u):
        t = u % PASO
        for k in range(4):
            if corte[k] <= t <= corte[k + 1]:
                f = (t - corte[k]) / (corte[k + 1] - corte[k])
                return prof[k] + (prof[k + 1] - prof[k]) * f
        return ONDA_V

    us = [u0]
    for k in range(math.floor(u0 / PASO), math.ceil(u1 / PASO) + 1):
        for c in corte[1:5]:
            u = k * PASO + c
            if u0 + 1e-4 < u < u1 - 1e-4:
                us.append(u)
    us.append(u1)
    return [(u, d(u)) for u in us]


def _restar(intervalos, a, b):
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


def chapa_grecada(p, pl, u0, u1, v0, alto, huecos, mat, costuras=()):
    """
    Chapa de nervios verticales sobre el alma, de v0 hasta alto(u), dejando los huecos [(u0, u1, v0, v1)].
    En cada costura (u) pone un tapajuntas remachado. Devuelve las costuras usadas.
    """
    b, a = p.baja, p.alta
    cortes = sorted({u0, u1} | {h[0] for h in huecos if u0 < h[0] < u1} | {h[1] for h in huecos if u0 < h[1] < u1})
    for ca, cb in zip(cortes[:-1], cortes[1:]):
        um = (ca + cb) / 2
        tramos = [(v0, None)]
        for h in huecos:
            if h[0] < um < h[1]:
                nuevos = []
                for va, vb in tramos:
                    tope = 1e9 if vb is None else vb
                    if h[3] <= va or h[2] >= tope:
                        nuevos.append((va, vb))
                        continue
                    if h[2] > va:
                        nuevos.append((va, h[2]))
                    if h[3] < tope:
                        nuevos.append((h[3], vb))
                tramos = nuevos
        perfil = _perfil_onda(ca, cb)
        for va, vb in tramos:
            abajo = [pl.p(u, va, d) for u, d in perfil]
            arriba = [pl.p(u, alto(u) if vb is None else vb, d) for u, d in perfil]
            b.loft([abajo, arriba], mat, cerrado=False, suave=False)
    # Tapajuntas en las costuras (cubren el solape de dos chapas) con remaches (malla alta).
    for uc in costuras:
        tramos = [(v0, alto(uc))]
        for h in huecos:
            if h[0] - 0.08 < uc < h[1] + 0.08:
                tramos = _restar(tramos, h[2], h[3])
        for va, vb in tramos:
            if vb - va < 0.2:
                continue
            caja_plano(b, pl, uc - 0.07, uc + 0.07, va, vb, ONDA_C - 0.005, ONDA_C + 0.03, mat, sin=("+y", "-z", "+z"))
            n = max(1, int((vb - va) / 0.28))
            for k in range(n + 1):
                vv = va + 0.1 + (vb - va - 0.2) * k / n
                a.cupula(pl.p(uc, vv, ONDA_C + 0.03), pl.n, 0.026, "acero", alto=0.014, lados=8)
    return costuras


def remaches_linea(p, pl, u0, u1, v, mat="acero", paso=PASO):
    """Fila de remaches (malla alta) en las crestas de la chapa a la altura v (donde la chapa va a la correa)."""
    k0 = math.ceil((u0 - 0.41) / paso)
    k1 = math.floor((u1 - 0.41) / paso)
    for k in range(k0, k1 + 1):
        u = k * paso + 0.41
        p.alta.cupula(pl.p(u, v, ONDA_C), pl.n, 0.024, mat, alto=0.013, lados=8)


# ======================================================================================================
# Losa, zócalo y muros
# ======================================================================================================


def losa():
    """Losa de hormigón a ras de suelo: dentro es el suelo del taller y delante, la explanada de trabajo."""
    p = Pieza("losa", peso_uv=0.7)
    b = p.baja
    L = LOSA
    ch = 0.05
    # Canto achaflanado (los bordes de una losa vieja están rotos y redondeados).
    arriba = [(L["x0"] + ch, L["y0"] + ch), (L["x1"] - ch, L["y0"] + ch), (L["x1"] - ch, L["y1"] - ch),
              (L["x0"] + ch, L["y1"] - ch)]
    abajo = [(L["x0"], L["y0"]), (L["x1"], L["y0"]), (L["x1"], L["y1"]), (L["x0"], L["y1"])]
    # Arriba en rejilla: así las manchas, el polvo y la oclusión se reparten mejor (y el sombreado es plano).
    xs = [L["x0"] + ch + (L["x1"] - L["x0"] - 2 * ch) * i / 6 for i in range(7)]
    ys = [L["y0"] + ch + (L["y1"] - L["y0"] - 2 * ch) * j / 5 for j in range(6)]
    for i in range(6):
        for j in range(5):
            b.poligono([(xs[i], ys[j], LOSA_Z), (xs[i + 1], ys[j], LOSA_Z), (xs[i + 1], ys[j + 1], LOSA_Z),
                        (xs[i], ys[j + 1], LOSA_Z)], "losa_taller", (0, 0, 1))
    # Canto: del borde de arriba (con chaflán) al suelo, siguiendo los vértices de la rejilla.
    borde = [(x, ys[0]) for x in xs[:-1]] + [(xs[-1], y) for y in ys[:-1]] + \
            [(x, ys[-1]) for x in xs[:0:-1]] + [(xs[0], y) for y in ys[:0:-1]]
    for k in range(len(borde)):
        x1, y1 = borde[k]
        x2, y2 = borde[(k + 1) % len(borde)]

        def fuera(x, y):
            return (x + (-ch if x <= xs[0] + 1e-6 else ch if x >= xs[-1] - 1e-6 else 0),
                    y + (-ch if y <= ys[0] + 1e-6 else ch if y >= ys[-1] - 1e-6 else 0))

        f1, f2 = fuera(x1, y1), fuera(x2, y2)
        b.poligono([(x1, y1, LOSA_Z), (x2, y2, LOSA_Z), (f2[0], f2[1], LOSA_Z - ch), (f1[0], f1[1], LOSA_Z - ch)],
                   "losa_taller", (f1[0] + f2[0] - x1 - x2, f1[1] + f2[1] - y1 - y2, 0.7))
        b.poligono([(f1[0], f1[1], LOSA_Z - ch), (f2[0], f2[1], LOSA_Z - ch), (f2[0], f2[1], -0.02),
                    (f1[0], f1[1], -0.02)], "losa_taller", (f1[0] + f2[0] - x1 - x2, f1[1] + f2[1] - y1 - y2, 0))
    # Juntas de dilatación cortadas con radial (malla alta: ranura oscura).
    for x in (-3.5, 3.5):
        p.alta.caja((x, (L["y0"] + L["y1"]) / 2, LOSA_Z + 0.001), (0.025, L["y1"] - L["y0"] - 0.3, 0.004), "junta")
    p.alta.caja((0, -2.0, LOSA_Z + 0.001), (L["x1"] - L["x0"] - 0.3, 0.025, 0.004), "junta")
    p.alta.caja((0, Y0 - 1.15, LOSA_Z + 0.001), (L["x1"] - L["x0"] - 0.3, 0.025, 0.004), "junta")
    return p


def zocalo():
    """Zócalo de hormigón armado (1,5 studs) con chaflán arriba, vierteaguas y refuerzos de acero atornillados."""
    p = Pieza("zocalo", peso_uv=0.9)
    b, a = p.baja, p.alta
    perfil = [(0.0, LOSA_Z), (ZOC_D, LOSA_Z), (ZOC_D, ZOC - 0.1), (0.03, ZOC + 0.005), (0.0, ZOC + 0.005)]
    tramos = [(FRENTE, -MX - ZOC_D, HUECO["x0"]), (FRENTE, HUECO["x1"], MX + ZOC_D),
              (FONDO, -MX - ZOC_D, MX + ZOC_D), (IZQ, -Y1, -Y0), (DER, Y0, PUERTA_L["u0"]), (DER, PUERTA_L["u1"], Y1)]
    for pl, u0, u1 in tramos:
        b.placa(perfil, pl.p(u0, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, u1 - u0, "hormigon_zocalo", atras=True)
    # Vierteaguas: pletina doblada encima del chaflán, por debajo de la chapa.
    vt = [(-0.005, ZOC + 0.005), (ZOC_D + 0.045, ZOC - 0.05), (ZOC_D + 0.045, ZOC - 0.09), (ZOC_D + 0.03, ZOC - 0.09),
          (ZOC_D + 0.03, ZOC - 0.065), (-0.005, ZOC - 0.02)]
    for pl, u0, u1 in tramos:
        b.placa(vt, pl.p(u0, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, u1 - u0, "acero_galv", atras=True)
    # Refuerzos: angulares de acero en las esquinas y pletinas cada ~3 studs, con pernos de anclaje.
    for sx in (-1, 1):
        for y_esq, sy in ((Y0, -1), (Y1, 1)):
            x_ext, y_ext = sx * (MX + ZOC_D), y_esq + sy * ZOC_D
            xa = sorted((x_ext, x_ext - sx * 0.32))
            ya = sorted((y_ext, y_ext + sy * 0.03))
            b.caja_de((xa[0], ya[0], LOSA_Z), (xa[1], ya[1], ZOC - 0.1), "acero_zocalo", sin=("-z",))
            xb = sorted((x_ext, x_ext + sx * 0.03))
            yb = sorted((y_ext, y_ext - sy * 0.32))
            b.caja_de((xb[0], yb[0], LOSA_Z), (xb[1], yb[1], ZOC - 0.1), "acero_zocalo", sin=("-z",))
            for zz in (0.45, 1.05):
                a.cupula((x_ext - sx * 0.17, y_ext + sy * 0.03, zz), (0, sy, 0), 0.035, "acero", alto=0.02, lados=6)
                a.cupula((x_ext + sx * 0.03, y_ext - sy * 0.17, zz), (sx, 0, 0), 0.035, "acero", alto=0.02, lados=6)
    for pl, u0, u1 in tramos:
        n = int((u1 - u0) / 3.0)
        for k in range(1, n + 1):
            uu = u0 + k * (u1 - u0) / (n + 1)
            caja_plano(b, pl, uu - 0.11, uu + 0.11, 0.35, ZOC - 0.16, ZOC_D, ZOC_D + 0.025, "acero_zocalo",
                       sin=("+y",))
            for vv in (0.5, 1.2):
                tornillo(p, pl.p(uu, vv, ZOC_D + 0.025), pl.n, 0.034, "acero", en_baja=False)
    return p


def _alma(b, pl, ext, inte, huecos, mat_int="interior"):
    """Alma del muro: cara exterior (casi no se ve: la tapa la chapa) e interior, con sus huecos."""
    b.cara_con_huecos([pl.p(u, v, 0) for u, v in ext], [[pl.p(u, v, 0) for u, v in h] for h in huecos], "junta",
                      pl.n, oculta=2)
    b.cara_con_huecos([pl.p(u, v, -MURO) for u, v in inte], [[pl.p(u, v, -MURO) for u, v in h] for h in huecos],
                      mat_int, -pl.n, oculta=1)


def _revelado(b, pl, u0, u1, v0, v1, mat="interior", suelo=False):
    """Caras del hueco (el grosor del muro) para que no se vea a través."""
    esquinas = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    lados = [(0, 1), (1, 2), (2, 3), (3, 0)]
    if suelo:
        lados = [(1, 2), (2, 3), (3, 0)]
    centro = ((u0 + u1) / 2, (v0 + v1) / 2)
    for i, j in lados:
        (ua, va), (ub, vb) = esquinas[i], esquinas[j]
        normal = pl.u * (centro[0] - (ua + ub) / 2) + pl.v * (centro[1] - (va + vb) / 2)
        b.poligono([pl.p(ua, va, 0), pl.p(ub, vb, 0), pl.p(ub, vb, -MURO), pl.p(ua, va, -MURO)], mat, normal,
                   oculta=1)


def muros():
    """Alma de los cuatro muros, chapa grecada gris oscuro con tapajuntas remachados y remates de esquina."""
    p = Pieza("muros", peso_uv=1.0)
    b, a = p.baja, p.alta
    H, D, VL, VT, VI = HUECO, PUERTA_L, VENT_L, VENT_T, VENTI

    def arco(u_min, u_max, x_de_u, base):
        pts = [(u_min, base), (u_max, base)]
        for k in range(17):
            u = u_max - (u_max - u_min) * k / 16
            pts.append((u, z_muro(x_de_u(u))))
        return pts

    # Fachada: el hueco del portón llega al suelo.
    ext = [(-MX, LOSA_Z), (H["x0"], LOSA_Z), (H["x0"], H["z1"]), (H["x1"], H["z1"]), (H["x1"], LOSA_Z), (MX, LOSA_Z)]
    ext += [(u, z_muro(u)) for u in [MX - 2 * MX * k / 16 for k in range(17)]]
    inte = [(-MX + MURO, LOSA_Z), (H["x0"], LOSA_Z), (H["x0"], H["z1"]), (H["x1"], H["z1"]), (H["x1"], LOSA_Z),
            (MX - MURO, LOSA_Z)]
    inte += [(u, z_muro(u)) for u in [(MX - MURO) - 2 * (MX - MURO) * k / 16 for k in range(17)]]
    _alma(b, FRENTE, ext, inte, [])
    _revelado(b, FRENTE, H["x0"], H["x1"], LOSA_Z, H["z1"], suelo=True)
    # Atrás: ventana pequeña y placa del extractor.
    ext = arco(-MX, MX, lambda u: -u, LOSA_Z)
    inte = arco(-MX + MURO, MX - MURO, lambda u: -u, LOSA_Z)
    huecos_t = [rect(VT["u0"], VT["u1"], VT["v0"], VT["v1"]), rect(VI["u0"] + 0.1, VI["u1"] - 0.1, VI["v0"] + 0.1,
                                                                   VI["v1"] - 0.1)]
    _alma(b, FONDO, ext, inte, huecos_t)
    _revelado(b, FONDO, VT["u0"], VT["u1"], VT["v0"], VT["v1"])
    _revelado(b, FONDO, VI["u0"] + 0.1, VI["u1"] - 0.1, VI["v0"] + 0.1, VI["v1"] - 0.1, mat="negro_mate")
    # Laterales: ventana a la izquierda; puerta a la derecha.
    _alma(b, IZQ, rect(-Y1, -Y0, LOSA_Z, Z_LAT), rect(-Y1 + MURO, -Y0 - MURO, LOSA_Z, Z_LAT),
          [rect(VL["u0"], VL["u1"], VL["v0"], VL["v1"])])
    _revelado(b, IZQ, VL["u0"], VL["u1"], VL["v0"], VL["v1"])
    ext = [(Y0, LOSA_Z), (D["u0"], LOSA_Z), (D["u0"], D["v1"]), (D["u1"], D["v1"]), (D["u1"], LOSA_Z), (Y1, LOSA_Z),
           (Y1, Z_LAT), (Y0, Z_LAT)]
    inte = [(Y0 + MURO, LOSA_Z), (D["u0"], LOSA_Z), (D["u0"], D["v1"]), (D["u1"], D["v1"]), (D["u1"], LOSA_Z),
            (Y1 - MURO, LOSA_Z), (Y1 - MURO, Z_LAT), (Y0 + MURO, Z_LAT)]
    _alma(b, DER, ext, inte, [])
    _revelado(b, DER, D["u0"], D["u1"], LOSA_Z, D["v1"], suelo=True)

    # ---- chapa grecada -------------------------------------------------------------------------------------
    f_alto = lambda u: z_muro(u) - 0.005             # noqa: E731  (fachada, u = x)
    t_alto = lambda u: z_muro(-u) - 0.005            # noqa: E731  (atrás, u = -x)
    l_alto = lambda u: Z_LAT - 0.005                 # noqa: E731
    marco = 0.04  # la chapa se mete un poco bajo los marcos
    chapa_grecada(p, FRENTE, -MX, MX, ZOC, f_alto, [(H["x0"] - marco, H["x1"] + marco, 0.0, H["z1"] + marco)],
                  "chapa_muro", costuras=(-4.6, -1.6, 1.55, 4.55))
    chapa_grecada(p, FONDO, -MX, MX, ZOC, t_alto,
                  [(VT["u0"] - marco, VT["u1"] + marco, VT["v0"] - marco, VT["v1"] + marco),
                   (VI["u0"] + 0.05, VI["u1"] - 0.05, VI["v0"] + 0.05, VI["v1"] - 0.05)],
                  "chapa_muro", costuras=(-4.4, -0.4, 3.5))
    chapa_grecada(p, IZQ, -Y1, -Y0, ZOC, l_alto, [(VL["u0"] - marco, VL["u1"] + marco, VL["v0"] - marco,
                                                    VL["v1"] + marco)], "chapa_muro", costuras=(-2.6, 2.3))
    chapa_grecada(p, DER, Y0, Y1, ZOC, l_alto, [(D["u0"] - marco, D["u1"] + marco, 0.0, D["v1"] + marco)],
                  "chapa_muro", costuras=(-2.5, 3.0))
    # Fila de remaches a media altura (la correa) y abajo, sobre el vierteaguas.
    for pl, u0, u1, huecos in ((FRENTE, -MX, MX, [(H["x0"] - 0.2, H["x1"] + 0.2)]), (FONDO, -MX, MX, []),
                               (IZQ, -Y1, -Y0, []), (DER, Y0, Y1, [(D["u0"] - 0.2, D["u1"] + 0.2)])):
        for v in (ZOC + 0.12, 3.05):
            tramos = [(u0 + 0.15, u1 - 0.15)]
            for h0, h1 in huecos:
                tramos = _restar(tramos, h0, h1)
            for t0, t1 in tramos:
                remaches_linea(p, pl, t0, t1, v)
    # ---- remates de esquina (angular doblado) ---------------------------------------------------------------
    for sx in (-1, 1):
        for y_esq, sy in ((Y0, -1), (Y1, 1)):
            z1 = Z_LAT - 0.01
            xa = sorted((sx * (MX - 0.25), sx * (MX + ONDA_C + 0.035)))
            ya = sorted((y_esq + sy * ONDA_C, y_esq + sy * (ONDA_C + 0.035)))
            b.caja_de((xa[0], ya[0], ZOC - 0.02), (xa[1], ya[1], z1), "chapa_remate", sin=("-z",))
            xb = sorted((sx * (MX + ONDA_C), sx * (MX + ONDA_C + 0.035)))
            yb = sorted((y_esq - sy * 0.25, y_esq + sy * (ONDA_C + 0.035)))
            b.caja_de((xb[0], yb[0], ZOC - 0.02), (xb[1], yb[1], z1), "chapa_remate", sin=("-z",))
            for k in range(9):
                zz = ZOC + 0.15 + k * (z1 - ZOC - 0.3) / 8
                a.cupula((sx * (MX - 0.12), y_esq + sy * (ONDA_C + 0.035), zz), (0, sy, 0), 0.022, "acero", alto=0.012)
                a.cupula((sx * (MX + ONDA_C + 0.035), y_esq - sy * 0.12, zz), (sx, 0, 0), 0.022, "acero", alto=0.012)
    return p


def marcos_huecos():
    """Marcos de acero del hueco del portón y de la puerta lateral (tapan el canto de la chapa)."""
    p = Pieza("marcos_huecos", peso_uv=1.1)
    b, a = p.baja, p.alta
    H = HUECO
    w, d1 = 0.16, ONDA_C + 0.05
    for x0, x1 in ((H["x0"] - w, H["x0"]), (H["x1"], H["x1"] + w)):
        caja_plano(b, FRENTE, x0, x1, LOSA_Z, H["z1"] + w, -MURO, d1, "metal_marco", sin=("-z",),
                   ocultas=("+y",))
    caja_plano(b, FRENTE, H["x0"] - w, H["x1"] + w, H["z1"], H["z1"] + w, -MURO, d1, "metal_marco",
               ocultas=("+y",))
    for x in (H["x0"] - w / 2, H["x1"] + w / 2):
        for k in range(6):
            a.cupula(FRENTE.p(x, 0.5 + k * 0.62, d1), FRENTE.n, 0.026, "acero", alto=0.014)
    # Umbral: angular de acero en el suelo del hueco (el carril de las ruedas de los carros).
    b.caja_de((H["x0"], Y0 - 0.02, LOSA_Z), (H["x1"], Y0 + MURO, LOSA_Z + 0.025), "acero_gastado", sin=("-z",))
    # Puerta lateral.
    D = PUERTA_L
    for u0, u1 in ((D["u0"] - w, D["u0"]), (D["u1"], D["u1"] + w)):
        caja_plano(b, DER, u0, u1, LOSA_Z, D["v1"] + w, -MURO, d1, "metal_marco", sin=("-z",), ocultas=("+y",))
    caja_plano(b, DER, D["u0"] - w, D["u1"] + w, D["v1"], D["v1"] + w, -MURO, d1, "metal_marco", ocultas=("+y",))
    b.caja_de((MX - MURO, D["u0"], LOSA_Z), (MX + 0.05, D["u1"], LOSA_Z + 0.03), "acero_gastado", sin=("-z",))
    # Guardacantos amarillo y negro en la jamba derecha del portón (los golpes de los vehículos).
    caja_plano(b, FRENTE, H["x1"] + w + 0.02, H["x1"] + w + 0.24, LOSA_Z, 1.25, ZOC_D, ZOC_D + 0.18,
               "seguridad", sin=("-z", "+y"))
    for vv in (0.4, 1.0):
        tornillo(p, FRENTE.p(H["x1"] + w + 0.13, vv, ZOC_D + 0.18), FRENTE.n, 0.03, "acero", en_baja=False)
    return p


# ======================================================================================================
# Techo de bóveda, lucernarios, extractor y canalones
# ======================================================================================================


def _xs_techo(x0=-XE, x1=XE, n=18, extra=()):
    xs = {round(x0 + (x1 - x0) * k / n, 5) for k in range(n + 1)}
    xs |= {round(x, 5) for x in extra if x0 <= x <= x1}
    return sorted(xs)


def p_techo(x, y, fuera=0.0):
    """Punto de la bóveda en (x, y), desplazado `fuera` studs por la normal."""
    n = normal_arco(x)
    return Vector((x, y, z_arco(x))) + n * fuera


def _en_lucernario(x, y, margen=0.0):
    return any(L[0] - margen < x < L[1] + margen and L[2] - margen < y < L[3] + margen for L in LUCERNARIOS)


def techo():
    """Bóveda de chapa: piel con grosor, nervios de costura remachados, frontis curvos y huecos de los lucernarios."""
    p = Pieza("techo", peso_uv=0.95)
    b, a = p.baja, p.alta
    xs = _xs_techo(extra=[x for L in LUCERNARIOS for x in (L[0], L[1])])
    ys = sorted({YE0, YE1} | {y for L in LUCERNARIOS for y in (L[2], L[3])})
    arriba, abajo = {}, {}
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            arriba[i, j] = b.v(p_techo(x, y))
            abajo[i, j] = b.v(p_techo(x, y, -TG))
    for i in range(len(xs) - 1):
        for j in range(len(ys) - 1):
            if _en_lucernario((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2):
                continue
            b.cara([arriba[i, j], arriba[i + 1, j], arriba[i + 1, j + 1], arriba[i, j + 1]], "chapa_techo_taller",
                   suave=True)
            b.cara([abajo[i, j + 1], abajo[i + 1, j + 1], abajo[i + 1, j], abajo[i, j]], "interior_techo",
                   suave=True, oculta=1)
    # Cantos: delante, detrás y en los aleros.
    nj = len(ys) - 1
    for i in range(len(xs) - 1):
        b.cara([abajo[i, 0], abajo[i + 1, 0], arriba[i + 1, 0], arriba[i, 0]], "chapa_remate")
        b.cara([arriba[i, nj], arriba[i + 1, nj], abajo[i + 1, nj], abajo[i, nj]], "chapa_remate")
    for x in (xs[0], xs[-1]):
        for j in range(nj):
            b.poligono([p_techo(x, ys[j], -TG), p_techo(x, ys[j + 1], -TG), p_techo(x, ys[j + 1]), p_techo(x, ys[j])],
                       "chapa_remate", (math.copysign(1, x), 0, 0), oculta=1)

    # Nervios de costura a lo largo del arco (cubrejuntas de las chapas), con tornillos (malla alta).
    xr = _xs_techo(n=14)
    for yc in COSTURAS[1:-1]:
        anillos = []
        for x in xr:
            anillos.append([p_techo(x, yc - 0.06, -0.005), p_techo(x, yc - 0.045, 0.085), p_techo(x, yc + 0.045, 0.085),
                            p_techo(x, yc + 0.06, -0.005)])
        vs = []
        for an in anillos:
            vs.append([b.v(q) for q in an])
        for k in range(len(vs) - 1):
            A, B = vs[k], vs[k + 1]
            b.cara([A[0], B[0], B[1], A[1]], "chapa_remate", suave=True)
            b.cara([A[1], B[1], B[2], A[2]], "chapa_remate", suave=True)
            b.cara([A[2], B[2], B[3], A[3]], "chapa_remate", suave=True)
        for an, signo in ((vs[0], -1), (vs[-1], 1)):
            f = b.cara(an if signo < 0 else list(reversed(an)), "chapa_remate")
            f.normal_update()
            if f.normal.x * signo < 0:
                f.normal_flip()
        for x in xr[1:-1]:
            a.cupula(p_techo(x, yc, 0.085), normal_arco(x), 0.024, "acero", alto=0.012)
    # Grecas finas de la chapa (malla alta): costillas bajas cada 0,3 studs a lo largo del arco.
    yy = YE0 + 0.15
    while yy < YE1 - 0.1:
        if all(abs(yy - c) > 0.12 for c in COSTURAS):
            tramo = []
            for x in _xs_techo(n=36):
                if _en_lucernario(x, yy, margen=0.14):
                    if len(tramo) > 1:
                        a.tubo(tramo, 0.02, "chapa_techo_taller", lados=4, tapa_ini=False, tapa_fin=False)
                    tramo = []
                    continue
                tramo.append(p_techo(x, yy, -0.008))
            if len(tramo) > 1:
                a.tubo(tramo, 0.02, "chapa_techo_taller", lados=4, tapa_ini=False, tapa_fin=False)
        yy += 0.3
    # Frontis curvos (tapan el canto del techo delante y detrás).
    for yb, s in ((YE0, -1), (YE1, 1)):
        vs = []
        for x in xr:
            n = normal_arco(x)
            base = Vector((x, yb, z_arco(x)))
            vs.append([b.v(base + n * 0.07 + Vector((0, 0.0, 0))),
                       b.v(base + n * 0.07 + Vector((0, s * 0.045, 0))),
                       b.v(base - n * (TG + 0.13) + Vector((0, s * 0.045, 0))),
                       b.v(base - n * (TG + 0.13))])
        for k in range(len(vs) - 1):
            A, B = vs[k], vs[k + 1]
            caras = [b.cara([A[0], B[0], B[1], A[1]], "chapa_remate", suave=True),
                     b.cara([A[1], B[1], B[2], A[2]], "chapa_remate", suave=True),
                     b.cara([A[2], B[2], B[3], A[3]], "chapa_remate", suave=True, oculta=1)]
            if s < 0:
                for f in caras:
                    f.normal_flip()
        dentro = [(b.v(Vector((x, yb, z_arco(x))) + normal_arco(x) * 0.07),
                   b.v(Vector((x, yb, z_arco(x))) - normal_arco(x) * 0.005)) for x in xr]
        for k in range(len(dentro) - 1):
            f = b.cara([dentro[k][0], dentro[k + 1][0], dentro[k + 1][1], dentro[k][1]], "chapa_remate")
            f.normal_update()
            if f.normal.y * s > 0:
                f.normal_flip()
        for an, sx in ((vs[0], -1), (vs[-1], 1)):
            f = b.cara(an, "chapa_remate")
            f.normal_update()
            if f.normal.x * sx < 0:
                f.normal_flip()
        for x in xr[1:-1]:
            a.cupula(p_techo(x, yb + s * 0.045, -0.03), Vector((0, s, 0)), 0.022, "acero", alto=0.012)
    p.extra["extractor_boca"] = [EXTRACTOR.x, EXTRACTOR.y, z_arco(EXTRACTOR.x) + 0.6]
    return p


def lucernarios():
    """Brocales de chapa alrededor de los huecos y la placa de policarbonato curvada encima (pieza aparte)."""
    marco = Pieza("lucernarios_marco", peso_uv=1.3)
    vidrio = Pieza("lucernarios_cristal", peso_uv=0.4)
    b, a = marco.baja, marco.alta
    alto, g = 0.13, 0.07
    for x0, x1, y0, y1 in LUCERNARIOS:
        xs = _xs_techo(x0, x1, n=3)

        def perimetro(off):
            pts = [(x, y0 - off) for x in xs]
            pts[0] = (xs[0] - off, y0 - off)
            pts[-1] = (xs[-1] + off, y0 - off)
            pts += [(xs[-1] + off, y1 + off)]
            pts += [(x, y1 + off) for x in xs[-2:0:-1]]
            pts += [(xs[0] - off, y1 + off)]
            return pts

        fuera = perimetro(g)
        dentro = perimetro(0.0)
        anillos = [[p_techo(x, y, -0.02) for x, y in fuera], [p_techo(x, y, alto) for x, y in fuera],
                   [p_techo(x, y, alto) for x, y in dentro], [p_techo(x, y, -TG - 0.005) for x, y in dentro]]
        b.loft(anillos, "chapa_remate", tapa_ini=False, tapa_fin=False, suave=False)
        # Policarbonato curvado: dos caras y canto, apoyado en el brocal.
        sup = [[p_techo(x, y0 - 0.03, alto + 0.005) for x in xs], [p_techo(x, y1 + 0.03, alto + 0.005) for x in xs]]
        inf = [[p_techo(x, y0 - 0.03, alto - 0.02) for x in xs], [p_techo(x, y1 + 0.03, alto - 0.02) for x in xs]]
        cv = vidrio.baja
        filas_s = [[cv.v(q) for q in fila] for fila in sup]
        filas_i = [[cv.v(q) for q in fila] for fila in inf]
        for k in range(len(xs) - 1):
            cv.cara([filas_s[0][k], filas_s[0][k + 1], filas_s[1][k + 1], filas_s[1][k]], "vidrio", suave=True)
            cv.cara([filas_i[1][k], filas_i[1][k + 1], filas_i[0][k + 1], filas_i[0][k]], "vidrio", suave=True)
        # Perfiles de aluminio que pisan el policarbonato (con tornillos) y nervio central.
        for y in (y0 - 0.03, y1 + 0.03):
            a_m = [p_techo(x, y, alto + 0.03) for x in _xs_techo(x0 - 0.05, x1 + 0.05, n=4)]
            b.tubo(a_m, 0.03, "aluminio", lados=3, tapa_ini=True, tapa_fin=True)
        for x in (x0 - 0.03, x1 + 0.03, (x0 + x1) / 2):
            b.tubo([p_techo(x, y0 - 0.06, alto + 0.03), p_techo(x, y1 + 0.06, alto + 0.03)], 0.026, "aluminio",
                   lados=3)
            for k in range(5):
                y = y0 + (y1 - y0) * k / 4
                a.cupula(p_techo(x, y, alto + 0.055), normal_arco(x), 0.016, "acero", alto=0.01, lados=6)
    return [marco, vidrio]


def extractor():
    """Extractor industrial del techo: zócalo que abraza la bóveda, motor, jaula con las aspas a la vista y sombrero."""
    p = Pieza("extractor", peso_uv=1.7)
    b, a = p.baja, p.alta
    cx, cy = EXTRACTOR.x, EXTRACTOR.y
    h = 0.62
    z_max = max(z_arco(cx - h), z_arco(cx + h))
    zb = z_max + 0.12
    # Zócalo de chapa: la parte de abajo sigue la curva del techo.
    pts = []
    for k in range(4):
        pts.append((cx - h + 2 * h * k / 4, cy - h))
    for k in range(4):
        pts.append((cx + h, cy - h + 2 * h * k / 4))
    for k in range(4):
        pts.append((cx + h - 2 * h * k / 4, cy + h))
    for k in range(4):
        pts.append((cx - h, cy + h - 2 * h * k / 4))
    abajo = [Vector((x, y, z_arco(x) - 0.03)) for x, y in pts]
    arriba = [Vector((x, y, zb)) for x, y in pts]
    b.loft([abajo, arriba], "metal_hollin_taller", tapa_ini=False, tapa_fin=True, suave=False)
    # Babero de chapa (se nota como un escalón más ancho apoyado en el techo).
    for x, y in pts[::2]:
        a.cupula((x, y, (zb + z_arco(x)) / 2), Vector((x - cx, y - cy, 0)).normalized(), 0.024, "acero", alto=0.012)
    # Cuerpo del motor, brida, jaula y sombrero.
    z1 = zb + 0.36
    b.revolucion([(0.6, 0.0), (0.6, 0.3), (0.64, 0.31), (0.64, 0.36), (0.0, 0.36)], (cx, cy, zb), 12,
                 "metal_hollin_taller", tapa_ini=False)
    zt = z1 + 0.3
    for k in range(12):
        ang = math.tau * k / 12
        b.caja((cx + math.cos(ang) * 0.6, cy + math.sin(ang) * 0.6, (z1 + zt) / 2), (0.045, 0.035, zt - z1),
               "metal_hollin_taller", giro=rot("Z", math.degrees(ang)))
    for zz in (z1 + 0.1, z1 + 0.2):
        a.tubo([Vector((cx + math.cos(t) * 0.605, cy + math.sin(t) * 0.605, zz))
                for t in [math.tau * k / 28 for k in range(29)]], 0.008, "acero", lados=4, tapa_ini=False,
               tapa_fin=False)
    b.revolucion([(0.0, 0.0), (0.66, 0.0), (0.68, 0.04), (0.42, 0.17), (0.12, 0.2), (0.0, 0.205)], (cx, cy, zt), 12,
                 "metal_hollin_taller", tapa_ini=False)
    for k in range(6):
        ang = math.tau * k / 6 + 0.3
        a.cupula((cx + math.cos(ang) * 0.62, cy + math.sin(ang) * 0.62, zb + 0.2),
                 (math.cos(ang), math.sin(ang), 0), 0.03, "acero", alto=0.016)
    # Caja de conexión y cable que baja por el techo.
    b.caja((cx + 0.66, cy - 0.15, zb + 0.15), (0.12, 0.22, 0.18), "metal_oscuro")
    asp = Pieza("extractor_aspas", pivote=(cx, cy, z1 + 0.15), peso_uv=1.4)
    c = asp.baja
    c.revolucion([(0.0, -0.07), (0.11, -0.06), (0.1, 0.06), (0.0, 0.07)], (cx, cy, z1 + 0.15), 8, "acero_hollin",
                 tapa_ini=False, tapa_fin=False)
    for k in range(5):
        ang = math.tau * k / 5
        g = rot("Z", math.degrees(ang)) @ rot("X", 28)
        c.caja(Vector((cx, cy, z1 + 0.15)) + rot("Z", math.degrees(ang)) @ Vector((0.33, 0, 0)), (0.46, 0.17, 0.018),
               "acero_hollin", giro=g)
    return [p, asp]


def canalones():
    """Canalones en los dos aleros con sus abrazaderas, y bajantes en las esquinas de atrás."""
    p = Pieza("canalones", peso_uv=1.0)
    b, a = p.baja, p.alta
    ze = z_arco(XE)
    for s in (-1, 1):
        xc = s * (XE + 0.11)
        ext = [(0.13, 0.05), (0.12, -0.08), (0.06, -0.16), (-0.06, -0.16), (-0.12, -0.08), (-0.13, 0.05)]
        inte = [(xx * 0.85, zz * 0.85 + 0.012) for xx, zz in ext]
        perfil = [(xc + s * xx, ze - 0.05 + zz) for xx, zz in ext] + \
            [(xc + s * xx, ze - 0.05 + zz) for xx, zz in reversed(inte)]
        anillos = [[Vector((x, y, z)) for x, z in perfil] for y in (YE0 - 0.02, YE1 + 0.02)]
        b.loft(anillos, "metal_oscuro", tapa_ini=False, tapa_fin=False, suave=False)
        b.recalcular(b.ultimas)
        for y, n in ((YE0 - 0.02, -1), (YE1 + 0.02, 1)):
            b.placa([(xc + s * xx, ze - 0.05 + zz) for xx, zz in ext], Vector((0, y, 0)), Vector((1, 0, 0)),
                    Vector((0, 0, 1)), Vector((0, n, 0)), 0.02, "metal_oscuro", atras=True)
        for y in (-3.2, -1.0, 1.2, 3.4):
            camino = [Vector((xc + s * xx, y, ze - 0.05 + zz)) for xx, zz in
                      ((-0.16, 0.08), (-0.135, 0.05), (-0.125, -0.09), (-0.065, -0.175), (0.065, -0.175),
                       (0.135, -0.09), (0.145, 0.06))]
            a.tubo(camino, 0.014, "metal_oscuro", lados=4, radio_curva=0.03, pasos_curva=1)
        # Bajante en la esquina de atrás: codo bajo el alero, pegado al muro, abrazaderas y zapata.
        yb = Y1 - 0.45
        xw = s * (MX + 0.3)
        camino = [(xc, yb, ze - 0.2), (xc, yb, ze - 0.45), (xw, yb, ze - 0.8), (xw, yb, 0.42), (s * (MX + 0.55), yb, 0.2)]
        b.tubo(camino, 0.1, "metal_oscuro", lados=6, radio_curva=0.2, pasos_curva=2, tapa_ini=False, tapa_fin=False)
        fin = Vector(camino[-1])
        dirv = (Vector(camino[-1]) - Vector(camino[-2])).normalized()
        b.revolucion([(0.1, 0), (0.08, 0), (0.08, -0.16), (0.0, -0.16)], fin, 6, "metal_oscuro", eje=dirv,
                     tapa_ini=False, tapa_fin=False, mats_tramo=["metal_oscuro", "negro_mate", "negro_mate"])
        for z in (3.1, 1.9, 0.75):
            b.revolucion([(0.12, 0), (0.12, 0.07)], (xw, yb, z - 0.035), 6, "metal_oscuro")
            xa, xb = sorted((xw - s * 0.1, s * (MX + ONDA_C)))
            b.caja_de((xa, yb - 0.02, z - 0.03), (xb, yb + 0.02, z + 0.03), "metal_oscuro")
            a.cupula((xw + s * 0.12, yb, z), (s, 0, 0), 0.02, "acero", alto=0.012)
        p.extra[f"pie_bajante_{'izq' if s < 0 else 'der'}"] = [s * (MX + 0.6), yb, 0.0]
    return p


# ======================================================================================================
# Portón corredero y su raíl
# ======================================================================================================


def _rueda(c, centro, eje, r, mat, lados=10):
    """Rueda de garganta (la del raíl): perfil con el surco en medio, cubo y tuerca del eje."""
    w = 0.06
    c.revolucion([(0.0, -w), (r, -w), (r * 0.82, 0.0), (r, w), (0.0, w)], centro, lados, mat, eje=eje,
                 tapa_ini=False, tapa_fin=False)


def porton():
    """
    Hoja del portón (pieza animable: desliza hacia -X). Bastidor de tubo, piel con nervios, travesaño, ventanilla
    arriba, tirador de tubo grueso, dos filas de remaches y dos carros de dos ruedas que cuelgan del raíl.
    El pivote queda en el centro de la base de la hoja, en el eje del raíl.
    """
    h = HOJA
    pl = FRENTE
    xc = (h["x0"] + h["x1"]) / 2
    p = Pieza("porton", pivote=pl.p(xc, h["z0"], RAIL["d"]), peso_uv=1.6)
    vid = Pieza("porton_cristal", pivote=pl.p(xc, h["z0"], RAIL["d"]), peso_uv=0.3)
    b, a = p.baja, p.alta
    x0, x1, z0, z1 = h["x0"], h["x1"], h["z0"], h["z1"]
    d0, dp, d1 = h["d0"], h["d0"] + 0.06, h["d1"]
    V = dict(x0=-2.05, x1=-1.15, z0=3.2, z1=3.72)   # ventanilla
    # Piel (chapa lisa) con el hueco de la ventanilla: caras delante y detrás, cantos y forro del hueco.
    ext = [pl.p(u, v, dp) for u, v in rect(x0, x1, z0, z1)]
    hueco = [pl.p(u, v, dp) for u, v in rect(V["x0"], V["x1"], V["z0"], V["z1"])]
    b.cara_con_huecos(ext, [hueco], "metal_porton", pl.n)
    b.cara_con_huecos([pl.p(u, v, d0) for u, v in rect(x0, x1, z0, z1)],
                      [[pl.p(u, v, d0) for u, v in rect(V["x0"], V["x1"], V["z0"], V["z1"])]], "metal_porton_dentro",
                      -pl.n, oculta=1)
    caja_plano(b, pl, x0, x1, z0, z1, d0, dp, "metal_porton", sin=("-y", "+y"))
    _revelado_d = [(V["x0"], V["z0"], V["x1"], V["z0"]), (V["x1"], V["z0"], V["x1"], V["z1"]),
                   (V["x1"], V["z1"], V["x0"], V["z1"]), (V["x0"], V["z1"], V["x0"], V["z0"])]
    vc = ((V["x0"] + V["x1"]) / 2, (V["z0"] + V["z1"]) / 2)
    for ua, va, ub, vb in _revelado_d:
        b.poligono([pl.p(ua, va, d0), pl.p(ub, vb, d0), pl.p(ub, vb, dp), pl.p(ua, va, dp)], "metal_oscuro",
                   pl.u * (vc[0] - (ua + ub) / 2) + pl.v * (vc[1] - (va + vb) / 2))
    # Bastidor de tubo cuadrado (delante de la piel) y travesaño.
    w = 0.14
    caja_plano(b, pl, x0, x1, z1 - w, z1, dp, d1, "metal_porton", sin=("+y",))
    caja_plano(b, pl, x0, x1, z0, z0 + w, dp, d1, "metal_porton", sin=("+y",))
    caja_plano(b, pl, x0, x0 + w, z0 + w, z1 - w, dp, d1, "metal_porton", sin=("+y", "-z", "+z"))
    caja_plano(b, pl, x1 - w, x1, z0 + w, z1 - w, dp, d1, "metal_porton", sin=("+y", "-z", "+z"))
    zr0, zr1 = 1.95, 2.07
    caja_plano(b, pl, x0 + w, x1 - w, zr0, zr1, dp, d1 - 0.01, "metal_porton", sin=("+y", "-x", "+x"))
    # Nervios verticales (omegas) en los dos paños.
    for xr in (-2.72, -2.17, -1.6, -1.03, -0.48):
        tramos = [(z0 + w, zr0), (zr1, z1 - w)]
        if V["x0"] - 0.08 < xr < V["x1"] + 0.08:
            tramos = [(z0 + w, zr0), (zr1, V["z0"] - 0.12)]
        for za, zb in tramos:
            caja_plano(b, pl, xr - 0.05, xr + 0.05, za, zb, dp, dp + 0.04, "metal_porton", sin=("+y", "-z", "+z"))
    # Marco de la ventanilla con su junta de goma.
    caja_plano(b, pl, V["x0"] - 0.09, V["x1"] + 0.09, V["z1"], V["z1"] + 0.09, dp, dp + 0.05, "metal_oscuro",
               sin=("+y",))
    caja_plano(b, pl, V["x0"] - 0.09, V["x1"] + 0.09, V["z0"] - 0.09, V["z0"], dp, dp + 0.05, "metal_oscuro",
               sin=("+y",))
    for xa, xb in ((V["x0"] - 0.09, V["x0"]), (V["x1"], V["x1"] + 0.09)):
        caja_plano(b, pl, xa, xb, V["z0"], V["z1"], dp, dp + 0.05, "metal_oscuro", sin=("+y", "-z", "+z"))
    for xx, zz in ((V["x0"] - 0.045, V["z0"] - 0.045), (V["x1"] + 0.045, V["z0"] - 0.045),
                   (V["x0"] - 0.045, V["z1"] + 0.045), (V["x1"] + 0.045, V["z1"] + 0.045)):
        a.cupula(pl.p(xx, zz, dp + 0.05), pl.n, 0.02, "acero", alto=0.012)
    caja_plano(vid.baja, pl, V["x0"] + 0.01, V["x1"] - 0.01, V["z0"] + 0.01, V["z1"] - 0.01, d0 + 0.02, dp - 0.015,
               "vidrio")
    # Remaches: fila arriba y abajo en el bastidor (de verdad, en la malla baja: es lo que más se ve).
    n = 10
    for zz in (z0 + w / 2, z1 - w / 2):
        for k in range(n + 1):
            xx = x0 + 0.12 + (x1 - x0 - 0.24) * k / n
            tornillo(p, pl.p(xx, zz, d1), pl.n, 0.03, "acero", lados_baja=5)
    for zz in (zr0 + 0.06,):
        for k in range(n + 1):
            xx = x0 + 0.12 + (x1 - x0 - 0.24) * k / n
            a.cupula(pl.p(xx, zz, d1 - 0.01), pl.n, 0.026, "acero", alto=0.014)
    # Tirador: barra horizontal de tubo grueso sobre dos patas con placa.
    zt = 2.38
    xa, xb = -0.95, -0.22
    for xx in (xa, xb):
        caja_plano(b, pl, xx - 0.07, xx + 0.07, zt - 0.11, zt + 0.11, d1, d1 + 0.02, "acero_gastado", sin=("+y",))
        b.cilindro(pl.p(xx, zt, d1 + 0.02), pl.n, 0.032, 0.11, "acero_gastado", lados=8, tapa_ini=False,
                   tapa_fin=False)
        for dz in (-0.075, 0.075):
            a.cupula(pl.p(xx, zt + dz, d1 + 0.02), pl.n, 0.016, "acero", alto=0.01, lados=6)
    b.tubo([pl.p(xa - 0.06, zt, d1 + 0.15), pl.p(xb + 0.06, zt, d1 + 0.15)], 0.048, "acero_pulido", lados=8)
    # Burlete de goma abajo (barre el suelo).
    caja_plano(b, pl, x0 + 0.02, x1 - 0.02, z0 - 0.07, z0, d0 + 0.03, dp + 0.02, "goma", sin=("+z",))
    # Carros con dos ruedas cada uno, colgados del raíl.
    zr = RAIL["z"] + RUEDA_R * 0.82
    for xcarro in (x0 + 0.62, x1 - 0.62):
        caja_plano(b, pl, xcarro - 0.36, xcarro + 0.36, z1 - 0.12, zr + 0.12, d1, d1 + 0.025, "metal_oscuro",
                   sin=("+y",))
        caja_plano(b, pl, xcarro - 0.32, xcarro + 0.32, zr - 0.05, zr + 0.05, RAIL["d"] - 0.13, d1, "metal_oscuro",
                   sin=("-y",))
        for xx in (xcarro - 0.22, xcarro + 0.22):
            _rueda(b, pl.p(xx, zr, RAIL["d"]), pl.n, RUEDA_R, "acero_rueda", lados=8)
            b.cilindro(pl.p(xx, zr, RAIL["d"] + 0.06), pl.n, 0.025, d1 - RAIL["d"] - 0.04, "acero", lados=6,
                       tapa_ini=False)
            tornillo(p, pl.p(xx, zr, d1 + 0.025), pl.n, 0.035, "acero", en_baja=False)
        for xx in (xcarro - 0.28, xcarro + 0.28):
            for zz in (z1 - 0.06, z1 + 0.06):
                a.cupula(pl.p(xx, zz, d1 + 0.025), pl.n, 0.02, "acero", alto=0.012)
    p.extra["tirador"] = list(pl.p((xa + xb) / 2, zt, d1 + 0.2))
    return [p, vid]


def riel_porton():
    """Raíl del portón con sus ménsulas, topes de goma en los extremos y la guía de suelo."""
    p = Pieza("riel_porton", peso_uv=1.2)
    b, a = p.baja, p.alta
    pl = FRENTE
    r = RAIL
    # Perfil del raíl: pletina vertical con cabeza redonda arriba (donde pisa la garganta de las ruedas).
    caja_plano(b, pl, r["x0"], r["x1"], r["z"] - 0.2, r["z"] - 0.03, r["d"] - 0.025, r["d"] + 0.025, "acero_galv")
    b.tubo([pl.p(r["x0"], r["z"] - 0.03, r["d"]), pl.p(r["x1"], r["z"] - 0.03, r["d"])], 0.035, "acero_gastado",
           lados=6)
    # Ménsulas atornilladas a la chapa.
    for xx in (-5.9, -4.55, -3.2, -1.85, -0.5, 0.15):
        caja_plano(b, pl, xx - 0.05, xx + 0.05, r["z"] - 0.22, r["z"] - 0.12, ONDA_C, r["d"] - 0.025, "metal_oscuro",
                   sin=("+y",))
        caja_plano(b, pl, xx - 0.1, xx + 0.1, r["z"] - 0.4, r["z"] - 0.02, ONDA_C, ONDA_C + 0.02, "metal_oscuro",
                   sin=("+y",))
        for zz in (r["z"] - 0.33, r["z"] - 0.09):
            a.cupula(pl.p(xx, zz, ONDA_C + 0.02), pl.n, 0.018, "acero", alto=0.011, lados=6)
    # Topes con taco de goma.
    for xx, s in ((r["x0"] + 0.05, 1), (r["x1"] - 0.05, -1)):
        caja_plano(b, pl, xx - 0.07, xx + 0.07, r["z"] - 0.08, r["z"] + 0.14, r["d"] - 0.06, r["d"] + 0.06,
                   "pintura_roja_gastada")
        b.cilindro(pl.p(xx + s * 0.07, r["z"] + 0.04, r["d"]), (s, 0, 0), 0.05, 0.06, "goma", lados=8)
    # Guía de suelo junto al hueco: placa atornillada a la losa y dos rodillos que abrazan la hoja.
    gx = HOJA["x0"] - 0.16
    b.caja_de((gx - 0.14, Y0 - 0.48, LOSA_Z), (gx + 0.14, Y0 - 0.02, LOSA_Z + 0.03), "acero_gastado", sin=("-z",))
    for dd in (HOJA["d0"] - 0.04, HOJA["d1"] + 0.04):
        b.cilindro(pl.p(gx, LOSA_Z + 0.03, dd), (0, 0, 1), 0.035, 0.32, "acero", lados=8)
    for xx in (gx - 0.09, gx + 0.09):
        for yy in (Y0 - 0.43, Y0 - 0.07):
            a.cupula((xx, yy, LOSA_Z + 0.03), (0, 0, 1), 0.02, "acero", alto=0.012, lados=6)
    return p


# ======================================================================================================
# Puerta lateral del mecánico
# ======================================================================================================


def puerta_lateral():
    """
    Puerta metálica muy usada: dos cuarterones en relieve, chapa de patada abollada, manija de palanca, cerradura
    de llavín y dos bisagras industriales gruesas. Pivote en el eje de las bisagras (canto de atrás).
    """
    h = HOJA_L
    pl = DER
    eje_u, eje_d = PUERTA_L["u1"] + 0.02, 0.13
    p = Pieza("puerta_lateral", pivote=pl.p(eje_u, h["v0"], eje_d), peso_uv=1.7)
    b, a = p.baja, p.alta
    u0, u1, v0, v1 = h["u0"], h["u1"], h["v0"], h["v1"]
    d0, d1 = -0.04, 0.08
    caja_plano(b, pl, u0, u1, v0, v1, d0, d1, "metal_puerta", mats={"+y": "metal_porton_dentro"},
               ocultas=("+y",))
    # Cuarterones: marcos en relieve (pletina) de dos paños.
    for va, vb in ((0.95, 2.05), (2.35, 3.45)):
        for (ua, ub, wa, wb) in ((u0 + 0.2, u1 - 0.2, va, va + 0.05), (u0 + 0.2, u1 - 0.2, vb - 0.05, vb),
                                 (u0 + 0.2, u0 + 0.25, va + 0.05, vb - 0.05), (u1 - 0.25, u1 - 0.2, va + 0.05, vb - 0.05)):
            caja_plano(b, pl, ua, ub, wa, wb, d1, d1 + 0.022, "metal_puerta", sin=("+y",))
    # Chapa de patada abajo, con tornillos.
    caja_plano(b, pl, u0 + 0.06, u1 - 0.06, v0 + 0.04, v0 + 0.62, d1, d1 + 0.012, "chapa_patada", sin=("+y",))
    for uu in (u0 + 0.14, (u0 + u1) / 2, u1 - 0.14):
        for vv in (v0 + 0.1, v0 + 0.56):
            a.cupula(pl.p(uu, vv, d1 + 0.012), pl.n, 0.016, "acero", alto=0.01, lados=6)
    # Bisagras industriales: hoja gruesa atornillada a la puerta + nudillo + pasador con cabeza.
    for vb in (v0 + 0.55, v1 - 0.55):
        caja_plano(b, pl, eje_u - 0.42, eje_u - 0.02, vb - 0.13, vb + 0.13, d1, d1 + 0.035, "hierro_bisagra",
                   sin=("+y",))
        b.cilindro(pl.p(eje_u, vb - 0.16, eje_d), (0, 0, 1), 0.065, 0.32, "hierro_bisagra", lados=8)
        b.cilindro(pl.p(eje_u, vb + 0.16, eje_d), (0, 0, 1), 0.04, 0.04, "acero", lados=6, tapa_ini=False)
        for uu in (eje_u - 0.33, eje_u - 0.15):
            for dv in (-0.07, 0.07):
                tornillo(p, pl.p(uu, vb + dv, d1 + 0.035), pl.n, 0.024, "acero", en_baja=False)
    # Manija de palanca industrial con su placa larga y la cerradura de llavín debajo.
    um, vm = u0 + 0.2, 1.95
    caja_plano(b, pl, um - 0.08, um + 0.08, vm - 0.5, vm + 0.14, d1, d1 + 0.025, "acero_gastado", sin=("+y",))
    b.cilindro(pl.p(um, vm, d1 + 0.025), pl.n, 0.05, 0.05, "acero_pulido", lados=8, tapa_ini=False)
    b.tubo([pl.p(um, vm, d1 + 0.07), pl.p(um, vm, d1 + 0.14), pl.p(um + 0.36, vm - 0.02, d1 + 0.16)], 0.03,
           "acero_pulido", lados=6, radio_curva=0.05, pasos_curva=2)
    b.revolucion([(0.04, 0), (0.036, 0.04), (0.0, 0.045)], pl.p(um, vm - 0.3, d1 + 0.025), 10, "laton", eje=pl.n)
    a.caja(pl.p(um, vm - 0.3, d1 + 0.07), (0.01, 0.01, 0.045), "negro_mate", giro=pl.giro)  # ranura de la llave
    for dv in (-0.44, 0.08):
        a.cupula(pl.p(um, vm + dv, d1 + 0.025), pl.n, 0.015, "acero", alto=0.009, lados=6)
    # Cierrapuertas hidráulico arriba (cuerpo y brazo hasta el marco).
    caja_plano(b, pl, u1 - 0.75, u1 - 0.25, v1 - 0.2, v1 - 0.05, d1, d1 + 0.09, "metal_oscuro", sin=("+y",))
    b.tubo([pl.p(u1 - 0.65, v1 - 0.1, d1 + 0.11), pl.p(u0 + 0.6, v1 - 0.04, d1 + 0.12),
            pl.p(u0 + 0.35, v1 + 0.08, ONDA_C + 0.08)], 0.018, "metal_oscuro", lados=4)
    p.extra["manija"] = list(pl.p(um + 0.25, vm, d1 + 0.16))
    return p


def cartel_horario():
    """Placa metálica junto a la puerta: «HORARIO: / Cuando estoy», grabado (letras oscuras en la malla alta)."""
    p = Pieza("cartel_horario", peso_uv=7.0)
    b, a = p.baja, p.alta
    pl = DER
    uc, vc = -0.92, 2.72
    w, hh = 0.86, 0.42
    giro = rot("X", 2.5)  # un pelín torcida
    base = pl.p(0, 0, ONDA_C + 0.03)
    contorno = [(-w / 2, -hh / 2), (w / 2, -hh / 2), (w / 2, hh / 2), (-w / 2, hh / 2)]
    ch = 0.04
    contorno = [(-w / 2 + ch, -hh / 2), (w / 2 - ch, -hh / 2), (w / 2, -hh / 2 + ch), (w / 2, hh / 2 - ch),
                (w / 2 - ch, hh / 2), (-w / 2 + ch, hh / 2), (-w / 2, hh / 2 - ch), (-w / 2, -hh / 2 + ch)]
    ang = math.radians(-2.5)
    pts = [(uc + x * math.cos(ang) - y * math.sin(ang), vc + x * math.sin(ang) + y * math.cos(ang)) for x, y in contorno]
    b.placa(pts, base, pl.u, pl.v, pl.n, 0.025, "placa_horario", atras=True)
    del giro

    def P(x, y, d=0.0):
        return pl.p(uc + x * math.cos(ang) - y * math.sin(ang), vc + x * math.sin(ang) + y * math.cos(ang),
                    ONDA_C + 0.055 + d)

    u = (pl.u * math.cos(ang) + pl.v * math.sin(ang)).normalized()
    v = (-pl.u * math.sin(ang) + pl.v * math.cos(ang)).normalized()
    texto(a, "HORARIO:", P(0, 0.075), u, v, pl.n, 0.105, 0.004, "grabado", ancho_max=0.7)
    texto(a, "Cuando estoy", P(0, -0.085), u, v, pl.n, 0.095, 0.004, "grabado", ancho_max=0.74)
    # Filete grabado alrededor y cuatro tornillos.
    marco = [P(x, y, 0.001) for x, y in [(-0.39, -0.17), (0.39, -0.17), (0.39, 0.17), (-0.39, 0.17), (-0.39, -0.17)]]
    a.tubo(marco, 0.005, "grabado", lados=4, tapa_ini=False, tapa_fin=False)
    for x in (-w / 2 + 0.05, w / 2 - 0.05):
        for y in (-hh / 2 + 0.05, hh / 2 - 0.05):
            tornillo(p, P(x, y), pl.n, 0.018, "acero", lados_baja=6)
    return p


# ======================================================================================================
# Ventanas y extractor de atrás
# ======================================================================================================


def ventana_lateral():
    """Ventana del lateral izquierdo: marco grueso de acero, cruceta, cristal armado (malla de alambre) y vierteaguas."""
    V = VENT_L
    pl = IZQ
    p = Pieza("ventana_lateral", peso_uv=1.5)
    vid = Pieza("ventana_lateral_cristal", peso_uv=0.3)
    b, a = p.baja, p.alta
    u0, u1, v0, v1 = V["u0"], V["u1"], V["v0"], V["v1"]
    w, df = 0.16, ONDA_C + 0.07
    caja_plano(b, pl, u0 - w, u1 + w, v1, v1 + w, -MURO, df, "metal_marco", ocultas=("+y",))
    caja_plano(b, pl, u0 - w, u1 + w, v0 - w, v0, -MURO, df, "metal_marco", ocultas=("+y",))
    for ua, ub in ((u0 - w, u0), (u1, u1 + w)):
        caja_plano(b, pl, ua, ub, v0, v1, -MURO, df, "metal_marco", sin=("-z", "+z"), ocultas=("+y",))
    # Vierteaguas inclinado.
    perfil = [(df, v0 - w), (df + 0.12, v0 - w - 0.02), (df + 0.12, v0 - w - 0.06), (df - 0.01, v0 - w - 0.05)]
    b.placa(perfil, pl.p(u0 - w - 0.06, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, u1 - u0 + 2 * w + 0.12, "metal_marco",
            atras=True)
    # Cruceta (perfiles en T) delante del cristal.
    dc = 0.0
    caja_plano(b, pl, -0.035, 0.035, v0, v1, dc, dc + 0.09, "metal_marco", sin=("-z", "+z", "+y"))
    vm = (v0 + v1) / 2
    for ua, ub in ((u0, -0.035), (0.035, u1)):
        caja_plano(b, pl, ua, ub, vm - 0.035, vm + 0.035, dc, dc + 0.09, "metal_marco", sin=("-x", "+x", "+y"))
    # Junquillos atornillados.
    for k in range(4):
        for uu, vv in ((u0 + 0.05, v0 + 0.1 + k * (v1 - v0 - 0.2) / 3), (u1 - 0.05, v0 + 0.1 + k * (v1 - v0 - 0.2) / 3)):
            a.cupula(pl.p(uu, vv, df), pl.n, 0.02, "acero", alto=0.012)
    # Cristal armado: la malla de alambre va dentro del vidrio (tiras finas por las dos caras).
    caja_plano(vid.baja, pl, u0, u1, v0, v1, -0.06, -0.025, "vidrio")
    paso = 0.13
    dm = -0.0425
    uu = u0 + paso / 2
    while uu < u1:
        for n_, dd in ((pl.n, dm + 0.0005), (-pl.n, dm - 0.0005)):
            b.poligono([pl.p(uu - 0.006, v0, dd), pl.p(uu + 0.006, v0, dd), pl.p(uu + 0.006, v1, dd),
                        pl.p(uu - 0.006, v1, dd)], "alambre", n_)
        uu += paso
    vv = v0 + paso / 2
    while vv < v1:
        for n_, dd in ((pl.n, dm + 0.0015), (-pl.n, dm - 0.0015)):
            b.poligono([pl.p(u0, vv - 0.006, dd), pl.p(u1, vv - 0.006, dd), pl.p(u1, vv + 0.006, dd),
                        pl.p(u0, vv + 0.006, dd)], "alambre", n_)
        vv += paso
    return [p, vid]


def ventana_trasera():
    """Ventana pequeña de atrás: marco de acero y cristal armado sin cruceta."""
    V = VENT_T
    pl = FONDO
    p = Pieza("ventana_trasera", peso_uv=1.4)
    vid = Pieza("ventana_trasera_cristal", peso_uv=0.3)
    b = p.baja
    u0, u1, v0, v1 = V["u0"], V["u1"], V["v0"], V["v1"]
    w, df = 0.14, ONDA_C + 0.06
    caja_plano(b, pl, u0 - w, u1 + w, v1, v1 + w, -MURO, df, "metal_marco", ocultas=("+y",))
    caja_plano(b, pl, u0 - w, u1 + w, v0 - w, v0, -MURO, df, "metal_marco", ocultas=("+y",))
    for ua, ub in ((u0 - w, u0), (u1, u1 + w)):
        caja_plano(b, pl, ua, ub, v0, v1, -MURO, df, "metal_marco", sin=("-z", "+z"), ocultas=("+y",))
    perfil = [(df, v0 - w), (df + 0.1, v0 - w - 0.02), (df + 0.1, v0 - w - 0.05), (df - 0.01, v0 - w - 0.045)]
    b.placa(perfil, pl.p(u0 - w - 0.05, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, u1 - u0 + 2 * w + 0.1, "metal_marco",
            atras=True)
    caja_plano(vid.baja, pl, u0, u1, v0, v1, -0.06, -0.025, "vidrio")
    paso = 0.13
    for k in range(1, int((u1 - u0) / paso) + 1):
        uu = u0 + k * paso - 0.03
        for n_, dd in ((pl.n, -0.042), (-pl.n, -0.043)):
            b.poligono([pl.p(uu - 0.006, v0, dd), pl.p(uu + 0.006, v0, dd), pl.p(uu + 0.006, v1, dd),
                        pl.p(uu - 0.006, v1, dd)], "alambre", n_)
    for k in range(1, int((v1 - v0) / paso) + 1):
        vv = v0 + k * paso - 0.03
        for n_, dd in ((pl.n, -0.041), (-pl.n, -0.044)):
            b.poligono([pl.p(u0, vv - 0.006, dd), pl.p(u1, vv - 0.006, dd), pl.p(u1, vv + 0.006, dd),
                        pl.p(u0, vv + 0.006, dd)], "alambre", n_)
    return [p, vid]


def ventilador_trasero():
    """Extractor de pared redondo: placa con el aro, rejilla protectora y aspas (pieza aparte, giran)."""
    V = VENTI
    pl = FONDO
    uc, vc = VENTI_C
    r = 0.5
    p = Pieza("ventilador_trasero", peso_uv=1.6)
    b, a = p.baja, p.alta
    dpl = ONDA_C + 0.01
    lados = 16
    ext = [(V["u0"], V["v0"]), (V["u1"], V["v0"]), (V["u1"], V["v1"]), (V["u0"], V["v1"])]
    # Placa cuadrada con el agujero redondo: se reparte el cuadrado en 16 puntos para unirlo con el círculo.
    cuad = []
    for k in range(lados):
        t = math.tau * k / lados + math.pi / 4
        dx, dy = math.cos(t), math.sin(t)
        s = 1 / max(abs(dx), abs(dy))
        cuad.append((uc + dx * s * (V["u1"] - V["u0"]) / 2, vc + dy * s * (V["v1"] - V["v0"]) / 2))
    circ = [(uc + math.cos(math.tau * k / lados + math.pi / 4) * r,
             vc + math.sin(math.tau * k / lados + math.pi / 4) * r) for k in range(lados)]
    b.anillo_placa(cuad, circ, pl.p(0, 0, dpl), pl.u, pl.v, pl.n, 0.04, "metal_hollin_taller")
    del ext
    # Aro (tobera) que entra en el muro, con borde enrollado.
    b.revolucion([(r, -MURO - 0.05), (r, 0.0), (r + 0.03, 0.03), (r + 0.06, 0.02)], pl.p(uc, vc, dpl + 0.04), lados,
                 "metal_hollin_taller", eje=pl.n, tapa_ini=False, tapa_fin=False)
    b.revolucion([(r + 0.06, 0.02), (r - 0.005, 0.0), (r - 0.005, -MURO - 0.05)], pl.p(uc, vc, dpl + 0.04), lados,
                 "negro_mate", eje=pl.n, tapa_ini=False, tapa_fin=False)
    # Motor con soporte en cruz (detrás de las aspas).
    b.revolucion([(0.0, -0.32), (0.15, -0.3), (0.16, -0.12), (0.12, -0.08), (0.0, -0.08)], pl.p(uc, vc, dpl), 10,
                 "metal_oscuro", eje=pl.n, tapa_ini=False, tapa_fin=False)
    for k in range(4):
        t = math.tau * k / 4 + math.pi / 4
        b.tubo([pl.p(uc + math.cos(t) * 0.14, vc + math.sin(t) * 0.14, dpl - 0.22),
                pl.p(uc + math.cos(t) * (r - 0.01), vc + math.sin(t) * (r - 0.01), dpl - 0.22)], 0.02,
               "metal_oscuro", lados=4)
    # Rejilla protectora delante: tres aros y ocho radios.
    dg = dpl + 0.13
    for rr in (0.24, 0.48):
        n = 10 if rr < 0.3 else 14
        b.tubo([pl.p(uc + math.cos(math.tau * k / n) * rr, vc + math.sin(math.tau * k / n) * rr,
                     dg - (0.5 - rr) * 0.12) for k in range(n + 1)], 0.012, "rejilla", lados=3, tapa_ini=False,
               tapa_fin=False)
    for k in range(8):
        t = math.tau * k / 8 + math.pi / 8
        b.tubo([pl.p(uc + math.cos(t) * 0.05, vc + math.sin(t) * 0.05, dg - 0.06),
                pl.p(uc + math.cos(t) * 0.5, vc + math.sin(t) * 0.5, dg - 0.06 + 0.12 * 0.0 - 0.0)], 0.012, "rejilla",
               lados=3)
    b.revolucion([(0.0, 0.0), (0.06, -0.01), (0.06, -0.04)], pl.p(uc, vc, dg - 0.02), 8, "rejilla", eje=pl.n,
                 tapa_ini=False, tapa_fin=False)
    for k in range(4):
        t = math.tau * k / 4 + math.pi / 4
        rr = 0.58
        tornillo(p, pl.p(uc + math.cos(t) * rr, vc + math.sin(t) * rr, dpl + 0.04), pl.n, 0.03, "acero", en_baja=False)
    asp = Pieza("ventilador_trasero_aspas", pivote=pl.p(uc, vc, dpl - 0.02), peso_uv=1.4)
    c = asp.baja
    c.revolucion([(0.0, -0.06), (0.09, -0.05), (0.09, 0.04), (0.0, 0.07)], pl.p(uc, vc, dpl - 0.02), 8,
                 "acero_hollin", eje=pl.n, tapa_ini=True, tapa_fin=False)
    for k in range(5):
        t = math.tau * k / 5
        cen = pl.p(uc + math.cos(t) * 0.27, vc + math.sin(t) * 0.27, dpl - 0.02)
        g = pl.giro @ rot("Y", -math.degrees(t)) @ rot("X", 25)
        c.caja(cen, (0.36, 0.015, 0.16), "acero_hollin", giro=g)
    p.extra["boca"] = list(pl.p(uc, vc, dpl + 0.2))
    return [p, asp]


# ======================================================================================================
# Panel de herramientas (con siluetas pintadas) y banco de trabajo
# ======================================================================================================

# Cada herramienta: lista de primitivas 2D (cápsulas) en su sistema local (u, v), con el material y el grosor.
# Con las mismas primitivas, agrandadas, se pinta su silueta en el panel (así se ve dónde va cada una).


def _forma_llave_inglesa():
    return [("cap", (0, -0.4), (0, 0.08), 0.042, "cromo", 0.03),
            ("cap", (0, 0.13), (0, 0.13), 0.085, "cromo", 0.034),
            ("cap", (-0.055, 0.17), (-0.06, 0.3), 0.032, "cromo", 0.034),
            ("cap", (0.05, 0.19), (0.055, 0.27), 0.03, "cromo", 0.034)]


def _forma_martillo():
    return [("cap", (0, -0.38), (0, 0.14), 0.04, "madera_mango", 0.07),
            ("cap", (-0.17, 0.2), (0.14, 0.2), 0.055, "acero_herramienta", 0.08),
            ("cap", (-0.17, 0.2), (-0.26, 0.12), 0.026, "acero_herramienta", 0.05),
            ("cap", (-0.17, 0.2), (-0.27, 0.26), 0.022, "acero_herramienta", 0.05)]


def _forma_destornillador():
    return [("cap", (0, 0.02), (0, 0.24), 0.05, "mango_amarillo", 0.09),
            ("cap", (0, -0.36), (0, 0.0), 0.014, "cromo", 0.028)]


def _forma_llave_tubo():
    return [("cap", (0, -0.3), (0, 0.24), 0.044, "cromo", 0.088),
            ("cap", (-0.2, 0.15), (0.2, 0.15), 0.016, "cromo", 0.032)]


def _forma_alicates():
    return [("cap", (-0.035, -0.06), (-0.085, -0.4), 0.032, "mango_rojo", 0.05),
            ("cap", (0.035, -0.06), (0.085, -0.4), 0.032, "mango_rojo", 0.05),
            ("cap", (0, -0.02), (0, -0.02), 0.055, "cromo", 0.034),
            ("cap", (-0.02, 0.0), (-0.012, 0.2), 0.03, "cromo", 0.03),
            ("cap", (0.02, 0.0), (0.012, 0.2), 0.03, "cromo", 0.03)]


def _forma_llave_combinada():
    return [("cap", (0, -0.3), (0, 0.28), 0.032, "cromo", 0.028),
            ("cap", (0, -0.32), (0, -0.32), 0.07, "cromo", 0.03),
            ("cap", (-0.04, 0.32), (-0.05, 0.38), 0.03, "cromo", 0.03),
            ("cap", (0.04, 0.32), (0.05, 0.38), 0.03, "cromo", 0.03)]


def _colocar(forma, uc, vc, ang=0.0):
    ca, sa = math.cos(math.radians(ang)), math.sin(math.radians(ang))

    def t(q):
        return (uc + q[0] * ca - q[1] * sa, vc + q[0] * sa + q[1] * ca)

    return [(k, t(a), t(b), r, m, g) for k, a, b, r, m, g in forma]


def _herramienta(c, pl, forma, d, giro_u=None):
    """Herramienta de verdad: cada cápsula extruida con su grosor, centrada en d + grosor/2."""
    for _, pa, pb, r, mat, g in forma:
        pts = capsula(pa, pb, r, n=3)
        c.placa(pts, pl.p(0, 0, d + 0.06 - g / 2), pl.u, pl.v, pl.n, g, mat, atras=False)


def panel_herramientas():
    """Panel perforado en la pared junto al portón, con cinco herramientas colgadas y sus siluetas pintadas."""
    p = Pieza("panel_herramientas", peso_uv=3.2)
    b, a = p.baja, p.alta
    pl = FRENTE
    P_ = PANEL_H
    d0, d1 = P_["d"], P_["d"] + 0.035
    # Listones de separación detrás y el tablero con un canto de aluminio.
    for zz in (P_["z0"] + 0.2, P_["z1"] - 0.2):
        caja_plano(b, pl, P_["x0"] + 0.05, P_["x1"] - 0.05, zz - 0.07, zz + 0.07, ONDA_C, d0, "metal_oscuro",
                   sin=("+y",))
    caja_plano(b, pl, P_["x0"], P_["x1"], P_["z0"], P_["z1"], d0, d1, "pegboard", sin=("+y",))
    for xx in (P_["x0"] + 0.06, P_["x1"] - 0.06):
        for zz in (P_["z0"] + 0.2, P_["z1"] - 0.2, (P_["z0"] + P_["z1"]) / 2):
            tornillo(p, pl.p(xx, zz, d1), pl.n, 0.022, "acero", en_baja=False)
    zc = 2.98
    sitio = [(_forma_llave_inglesa(), 0.93, zc, 0), (_forma_martillo(), 1.38, zc - 0.02, 0),
             (_forma_destornillador(), 1.79, zc + 0.05, 0), (_forma_llave_combinada(), 2.14, zc, 0),
             (_forma_llave_tubo(), 2.5, zc, 0), (_forma_alicates(), 2.95, zc + 0.04, 0)]
    for k, (forma, uc, vc, ang) in enumerate(sitio):
        colocada = _colocar(forma, uc, vc, ang)
        # Silueta pintada (malla alta, plana sobre el tablero): la forma engordada.
        for _, pa, pb, r, _, _ in colocada:
            a.placa(capsula(pa, pb, r + 0.032, n=5), pl.p(0, 0, d1), pl.u, pl.v, pl.n, 0.002, "silueta")
        if k == 3:
            continue  # la llave combinada no está: la tiene el mecánico en el banco
        _herramienta(b, pl, colocada, d1)
        # Ganchos del panel (varilla doblada) donde se apoya la herramienta.
        for du in (-0.07, 0.07):
            gu, gv = uc + du, vc + (0.04 if k != 0 else 0.1)
            b.tubo([pl.p(gu, gv + 0.03, d1), pl.p(gu, gv, d1 + 0.13), pl.p(gu, gv + 0.04, d1 + 0.15)], 0.011,
                   "acero", lados=3)
    # Detalles de las herramientas (malla alta): estrías de los mangos, tornillo de la inglesa, marca del martillo.
    for dz in range(5):
        a.caja(pl.p(1.79, zc + 0.08 + dz * 0.04, d1 + 0.105), (0.1, 0.012, 0.01), "mango_amarillo", giro=pl.giro)
    a.cilindro(pl.p(0.93 - 0.06, zc + 0.12, d1 + 0.06), (1, 0, 0), 0.022, 0.12, "cromo", lados=8)
    # Rótulo pintado arriba del panel.
    texto(a, "NO TOCAR", pl.p((P_["x0"] + P_["x1"]) / 2, P_["z1"] - 0.12, d1), pl.u, pl.v, pl.n, 0.07, 0.002,
          "silueta", ancho_max=0.7)
    return p


def banco_trabajo():
    """Banco de trabajo metálico contra la pared: tablero rayado, balda, tornillo de banco y lo que hay encima."""
    p = Pieza("banco_trabajo", peso_uv=1.5)
    b, a = p.baja, p.alta
    B = BANCO
    x0, x1, y0, zt = B["x0"], B["x1"], B["y0"], B["z"]
    y1 = Y0 - ONDA_C - 0.02
    e = 0.07
    # Tablero con canto doblado delante.
    b.caja_de((x0, y0, zt - e), (x1, y1, zt), "banco_tapa", ocultas=("+y",))
    b.caja_de((x0, y0 - 0.03, zt - 0.2), (x1, y0, zt), "metal_banco", sin=("+y",))
    # Patas de angular, travesaños y balda.
    for xx in (x0 + 0.06, x1 - 0.06):
        for yy in (y0 + 0.07, y1 - 0.07):
            b.caja((xx, yy, (LOSA_Z + zt - e) / 2), (0.1, 0.1, zt - e - LOSA_Z), "metal_banco", sin=("-z", "+z"))
            b.caja((xx, yy, LOSA_Z + 0.01), (0.16, 0.16, 0.02), "metal_banco", sin=("-z",))
    b.caja_de((x0 + 0.02, y0 + 0.05, 0.45), (x1 - 0.02, y1 - 0.05, 0.5), "metal_banco")
    for yy in (y0 + 0.07, y1 - 0.07):
        b.caja_de((x0 + 0.11, yy - 0.03, 1.2), (x1 - 0.11, yy + 0.03, 1.27), "metal_banco")
    # En la balda: una caja de herramientas y un rollo de cable.
    b.caja_de((x0 + 0.25, y0 + 0.25, 0.5), (x0 + 1.05, y1 - 0.15, 0.82), "pintura_roja_gastada")
    b.caja_de((x0 + 0.22, y0 + 0.22, 0.82), (x0 + 1.08, y1 - 0.12, 0.86), "pintura_roja_gastada")
    b.tubo([(x0 + 0.55, y0 + 0.2, 0.9), (x0 + 0.75, y0 + 0.2, 0.9)], 0.025, "metal_oscuro", lados=4)
    b.revolucion([(0.18, 0.0), (0.22, 0.03), (0.22, 0.13), (0.18, 0.16), (0.08, 0.16), (0.08, 0.0)],
                 (x1 - 0.55, (y0 + y1) / 2, 0.5), 8, "goma", tapa_ini=False, tapa_fin=False)
    # Tornillo de banco en la esquina delantera derecha (atornillado al tablero).
    vx, vy = x1 - 0.42, y0 + 0.28
    b.caja_de((vx - 0.24, vy - 0.2, zt), (vx + 0.24, vy + 0.22, zt + 0.05), "pintura_azul_tornillo")
    for dx in (-0.17, 0.17):
        for dy in (-0.13, 0.15):
            tornillo(p, (vx + dx, vy + dy, zt + 0.05), (0, 0, 1), 0.03, "acero", en_baja=False)
    b.caja_de((vx - 0.13, vy - 0.12, zt + 0.05), (vx + 0.13, vy + 0.36, zt + 0.32), "pintura_azul_tornillo")
    b.caja_de((vx - 0.16, vy + 0.3, zt + 0.12), (vx + 0.16, vy + 0.4, zt + 0.42), "pintura_azul_tornillo")
    b.caja_de((vx - 0.16, vy - 0.32, zt + 0.12), (vx + 0.16, vy - 0.22, zt + 0.42), "pintura_azul_tornillo")
    b.caja_de((vx - 0.11, vy - 0.22, zt + 0.12), (vx + 0.11, vy - 0.12, zt + 0.28), "pintura_azul_tornillo")
    for yy in (vy - 0.215, vy + 0.295):
        b.caja_de((vx - 0.16, yy - 0.006, zt + 0.32), (vx + 0.16, yy + 0.006, zt + 0.42), "acero_mordaza")
    b.cilindro((vx, vy - 0.32, zt + 0.22), (0, -1, 0), 0.035, 0.18, "acero", lados=8)
    b.cilindro((vx, vy - 0.5, zt + 0.22), (0, -1, 0), 0.06, 0.06, "acero", lados=8)
    b.tubo([(vx - 0.28, vy - 0.53, zt + 0.22), (vx + 0.28, vy - 0.53, zt + 0.22)], 0.018, "acero_pulido", lados=6)
    for xx in (vx - 0.29, vx + 0.29):
        b.revolucion([(0.0, -0.03), (0.035, 0.0), (0.0, 0.03)], (xx, vy - 0.53, zt + 0.22), 6, "acero", eje=(1, 0, 0))
    # Estrías de las mordazas (malla alta).
    for k in range(9):
        for yy in (vy - 0.222, vy + 0.302):
            a.caja((vx - 0.14 + k * 0.035, yy, zt + 0.37), (0.008, 0.004, 0.09), "acero_mordaza")
    # Encima: la llave combinada que falta en el panel, unas tuercas y la aceitera.
    llave = _colocar(_forma_llave_combinada(), 0, 0, 0)
    origen = Vector((x0 + 1.1, y0 + 0.45, zt))
    for _, pa, pb, r, mat, g in llave:
        pts = capsula(pa, pb, r, n=4)
        rz = rot("Z", 70)
        b.placa([(q[0], q[1]) for q in pts], origen, rz @ Vector((1, 0, 0)), rz @ Vector((0, 1, 0)), Vector((0, 0, 1)),
                g, mat, atras=False)
    for k, (xx, yy) in enumerate(((x0 + 1.55, y0 + 0.32), (x0 + 1.62, y0 + 0.5), (x0 + 1.47, y0 + 0.58))):
        b.revolucion([(0.045, 0.0), (0.045, 0.035), (0.0, 0.035)], (xx, yy, zt), 6, "acero", giro=k * 0.4,
                     tapa_ini=False)
    ax, ay = x0 + 0.45, y0 + 0.55
    b.revolucion([(0.13, 0.0), (0.13, 0.12), (0.1, 0.17), (0.05, 0.2), (0.03, 0.24), (0.0, 0.24)], (ax, ay, zt), 8,
                 "aceitera", tapa_ini=False)
    b.tubo([(ax, ay, zt + 0.2), (ax + 0.08, ay - 0.05, zt + 0.32), (ax + 0.24, ay - 0.15, zt + 0.42)], 0.015,
           "laton", lados=5, radio_curva=0.05, pasos_curva=2, radios=[0.022, 0.016, 0.009])
    return p


# ======================================================================================================
# Cuadro eléctrico, señal, medidor y cables
# ======================================================================================================


def cuadro_electrico():
    """Cuadro grande con la puerta abierta: dos filas de magnetotérmicos, diferencial e interruptor general."""
    C = CUADRO
    pl = FRENTE
    p = Pieza("cuadro_electrico", peso_uv=1.8)
    b, a = p.baja, p.alta
    x0, x1, z0, z1, d0, d1 = C["x0"], C["x1"], C["z0"], C["z1"], C["d0"], C["d1"]
    e = 0.04
    caja_plano(b, pl, x0, x1, z0, z1, d0, d0 + e, "pintura_gris_cuadro", sin=("+y",))   # fondo
    caja_plano(b, pl, x0, x1, z0, z0 + e, d0 + e, d1, "pintura_gris_cuadro", sin=("+y",))
    caja_plano(b, pl, x0, x1, z1 - e, z1, d0 + e, d1, "pintura_gris_cuadro", sin=("+y",))
    caja_plano(b, pl, x0, x0 + e, z0 + e, z1 - e, d0 + e, d1, "pintura_gris_cuadro", sin=("+y", "-z", "+z"))
    caja_plano(b, pl, x1 - e, x1, z0 + e, z1 - e, d0 + e, d1, "pintura_gris_cuadro", sin=("+y", "-z", "+z"))
    # Interior: placa de montaje naranja y dos carriles con los aparatos.
    caja_plano(b, pl, x0 + 0.07, x1 - 0.07, z0 + 0.07, z1 - 0.07, d0 + e, d0 + e + 0.015, "placa_montaje",
               sin=("+y",))
    dm = d0 + e + 0.015
    for zr in (2.95, 2.45):
        caja_plano(b, pl, x0 + 0.1, x1 - 0.1, zr - 0.03, zr + 0.03, dm, dm + 0.02, "acero_galv", sin=("+y",))
        n = 7 if zr > 2.7 else 5
        for k in range(n):
            xx = x0 + 0.17 + k * 0.118
            ancho = 0.1 if (zr < 2.7 and k == 0) else 0.1
            caja_plano(b, pl, xx - ancho / 2, xx + ancho / 2, zr - 0.17, zr + 0.17, dm + 0.02, dm + 0.13, "plastico_blanco",
                       sin=("+y",))
            caja_plano(a, pl, xx - 0.018, xx + 0.018, zr + (0.02 if k % 3 else -0.07), zr + (0.07 if k % 3 else -0.02),
                       dm + 0.13, dm + 0.15, "plastico_negro" if k % 4 else "plastico_rojo", sin=("+y",))
    # Interruptor general (palanca roja grande) abajo a la derecha.
    caja_plano(b, pl, x1 - 0.42, x1 - 0.12, z0 + 0.12, z0 + 0.5, dm, dm + 0.12, "plastico_negro", sin=("+y",))
    b.tubo([pl.p(x1 - 0.27, z0 + 0.31, dm + 0.12), pl.p(x1 - 0.27, z0 + 0.41, dm + 0.27)], 0.03, "plastico_rojo",
           lados=6)
    # Cables por dentro (peinados hacia abajo) y prensaestopas.
    for k in range(4):
        xx = x0 + 0.2 + k * 0.12
        b.tubo([pl.p(xx, 2.27, dm + 0.06), pl.p(xx, 2.12, dm + 0.05), pl.p(x0 + 0.35 + k * 0.05, z0 + 0.05, dm + 0.05)],
               0.018, ("cable_rojo", "cable_azul", "cable_negro", "cable_amarillo")[k], lados=4, radio_curva=0.05,
               pasos_curva=1)
    # Etiquetas de los circuitos (malla alta) y tornillos de la placa.
    for k in range(7):
        a.caja(pl.p(x0 + 0.17 + k * 0.118, 3.16, dm + 0.004), (0.09, 0.004, 0.04), "papel", giro=pl.giro)
    for xx in (x0 + 0.11, x1 - 0.11):
        for zz in (z0 + 0.11, z1 - 0.11):
            a.cupula(pl.p(xx, zz, dm), pl.n, 0.015, "acero", alto=0.009, lados=6)
    # Puerta (pieza aparte): bisagras en el canto izquierdo, abierta ~105°.
    eje = pl.p(x0 - 0.01, z0, d1 + 0.01)
    pu = Pieza("cuadro_puerta", pivote=eje, peso_uv=1.6)
    pb, pa = pu.baja, pu.alta
    g = rot("Z", -105)
    w = x1 - x0 + 0.02
    caras = pb.caja(Vector((0.0, 0.0, 0.0)), (w, 0.04, z1 - z0 + 0.02), "pintura_gris_cuadro")
    pb.transformar(pb.verts_de(caras), Matrix.Translation(eje + g @ Vector((w / 2, -0.02, (z1 - z0) / 2))) @ g.to_4x4())
    # Bolsillo de planos por dentro de la puerta, con papeles.
    dentro = Vector((0, 1, 0))
    for zz, hh, mat in ((2.6, 0.6, "pintura_gris_cuadro"),):
        caras = pb.caja(Vector((0.0, 0.0, 0.0)), (w - 0.3, 0.05, hh), mat)
        pb.transformar(pb.verts_de(caras), Matrix.Translation(eje + g @ Vector((w / 2, 0.025, zz - z0))) @ g.to_4x4())
    caras = pb.caja(Vector((0, 0, 0)), (w - 0.36, 0.01, 0.42), "papel")
    pb.transformar(pb.verts_de(caras), Matrix.Translation(eje + g @ Vector((w / 2 - 0.03, 0.06, 2.85 - z0))) @
                   (g @ rot("Y", 4)).to_4x4())
    # Maneta de cuarto de vuelta por fuera.
    m = eje + g @ Vector((w - 0.1, -0.04, (z1 - z0) / 2))
    pb.cilindro(m, g @ Vector((0, -1, 0)), 0.04, 0.05, "plastico_negro", lados=8)
    del dentro, pa
    p.extra["chispas_cuadro"] = list(pl.p((x0 + x1) / 2, 2.2, dm + 0.15))
    return [p, pu]


def senal_alto_voltaje():
    """Señal triangular de peligro eléctrico: chapa amarilla con canto negro, rayo y «ALTO VOLTAJE»."""
    p = Pieza("senal_alto_voltaje", peso_uv=6.0)
    b, a = p.baja, p.alta
    pl = FRENTE
    uc, vc = (CUADRO["x0"] + CUADRO["x1"]) / 2, 3.88
    lado = 0.78
    alto = lado * math.sqrt(3) / 2
    tri = [(uc - lado / 2, vc - alto / 3), (uc + lado / 2, vc - alto / 3), (uc, vc + 2 * alto / 3)]
    b.placa(tri, pl.p(0, 0, ONDA_C + 0.03), pl.u, pl.v, pl.n, 0.02, "senal_amarilla", atras=True)
    df = ONDA_C + 0.05
    # Canto negro (malla alta, banda pintada) y rayo.
    k = 0.06
    interior = [(uc - lado / 2 + k * 1.73, vc - alto / 3 + k), (uc + lado / 2 - k * 1.73, vc - alto / 3 + k),
                (uc, vc + 2 * alto / 3 - 2 * k)]
    a.anillo_placa(tri, interior, pl.p(0, 0, df), pl.u, pl.v, pl.n, 0.002, "pintura_negra")
    rayo = [(0.03, 0.2), (-0.07, 0.0), (-0.005, 0.0), (-0.05, -0.17), (0.07, 0.04), (0.005, 0.04)]
    a.placa([(uc + x, vc + 0.03 + y * 0.95) for x, y in rayo], pl.p(0, 0, df), pl.u, pl.v, pl.n, 0.002,
            "pintura_negra")
    texto(a, "ALTO VOLTAJE", pl.p(uc, vc - alto / 3 + 0.105, df), pl.u, pl.v, pl.n, 0.052, 0.002, "pintura_negra",
          ancho_max=0.42)
    for (x, y) in ((uc - lado / 2 + 0.12, vc - alto / 3 + 0.06), (uc + lado / 2 - 0.12, vc - alto / 3 + 0.06),
                   (uc, vc + 2 * alto / 3 - 0.13)):
        tornillo(p, pl.p(x, y, ONDA_C + 0.05), pl.n, 0.018, "acero", lados_baja=6)
    return p


def medidor_energia():
    """Medidor grande (el taller gasta mucho): caja con visor, pantallita de neón, ruedas contadoras y precinto."""
    M = MEDIDOR
    pl = FRENTE
    p = Pieza("medidor_energia", peso_uv=2.0)
    pant = Pieza("medidor_energia_neon", peso_uv=0.4)
    b, a = p.baja, p.alta
    x0, x1, z0, z1 = M["x0"], M["x1"], M["z0"], M["z1"]
    d0, d1 = ONDA_C, ONDA_C + 0.32
    caja_plano(b, pl, x0, x1, z0, z1, d0, d1, "pintura_gris_cuadro", sin=("+y",))
    # Visor con marco y la pantalla de neón (pieza aparte) y las ruedas del contador.
    caja_plano(b, pl, x0 + 0.08, x1 - 0.08, 2.72, 3.08, d1, d1 + 0.03, "plastico_negro", sin=("+y",))
    caja_plano(pant.baja, pl, x0 + 0.13, x1 - 0.13, 2.86, 3.02, d1 + 0.02, d1 + 0.035, "neon", sin=("+y",))
    for k in range(5):
        caja_plano(b, pl, x0 + 0.13 + k * 0.08, x0 + 0.2 + k * 0.08, 2.76, 2.83, d1 + 0.02, d1 + 0.035,
                   "plastico_blanco", sin=("+y",))
    # Rótulo, precinto con alambre y tornillos.
    texto(a, "kWh", pl.p(x1 - 0.15, 2.55, d1), pl.u, pl.v, pl.n, 0.06, 0.002, "pintura_negra", ancho_max=0.2)
    b.cilindro(pl.p(x0 + 0.14, 2.42, d1), pl.n, 0.035, 0.02, "plomo", lados=8)
    a.tubo([pl.p(x0 + 0.14, 2.45, d1 + 0.01), pl.p(x0 + 0.1, 2.55, d1 + 0.005), pl.p(x0 + 0.08, 2.65, d1)], 0.004,
           "acero", lados=3)
    for xx in (x0 + 0.06, x1 - 0.06):
        for zz in (z0 + 0.06, z1 - 0.06):
            a.cupula(pl.p(xx, zz, d1), pl.n, 0.016, "acero", alto=0.01, lados=6)
    return [p, pant]


def cables():
    """Tubos de los cables: del cuadro al zócalo, del medidor al cuadro y la acometida que sube al arco."""
    p = Pieza("cables", peso_uv=1.1)
    b = p.baja
    pl = FRENTE
    C, M = CUADRO, MEDIDOR
    d = ONDA_C + 0.06
    xc = (C["x0"] + C["x1"]) / 2
    # Del cuadro al suelo (tubo gris con abrazaderas).
    for xx in (xc - 0.2, xc + 0.15):
        b.tubo([pl.p(xx, C["z0"], d), pl.p(xx, ZOC + 0.1, d), pl.p(xx, ZOC - 0.08, d + 0.08), pl.p(xx, 0.6, d + 0.08),
                pl.p(xx, 0.45, d)], 0.04, "conducto", lados=5, radio_curva=0.08, pasos_curva=1, tapa_ini=False)
    # Del medidor al cuadro.
    b.tubo([pl.p(M["x0"] + 0.1, M["z0"], d + 0.04), pl.p(M["x0"] + 0.1, 2.05, d + 0.04), pl.p(C["x1"], 2.05, d + 0.04)],
           0.035, "conducto", lados=5, radio_curva=0.08, pasos_curva=1)
    # Acometida: cable grueso que sube del medidor por la esquina hasta un aislador en lo alto y sale del taller.
    xa = M["x1"] - 0.15
    za = z_muro(xa) - 0.25
    b.tubo([pl.p(xa, M["z1"], d + 0.04), pl.p(xa, za - 0.1, d + 0.04), pl.p(xa, za + 0.05, d + 0.2),
            pl.p(xa + 0.2, za - 0.15, d + 0.5), pl.p(xa + 0.6, za + 0.15, d + 1.3)], 0.05, "goma", lados=5,
           radio_curva=0.12, pasos_curva=2)
    b.caja_de((xa - 0.05, Y0 - d - 0.15, za + 0.0), (xa + 0.05, Y0 - ONDA_C, za + 0.1), "metal_oscuro")
    b.revolucion([(0.05, 0.0), (0.07, 0.03), (0.05, 0.06), (0.07, 0.09), (0.05, 0.12), (0.0, 0.12)],
                 pl.p(xa, za + 0.05, d + 0.12), 8, "ceramica", eje=pl.n, tapa_ini=False)
    for zz in (2.0, 2.7):
        b.caja_de((xa - 0.06, Y0 - d - 0.1, zz - 0.03), (xa + 0.06, Y0 - ONDA_C, zz + 0.03), "metal_oscuro")
    return p


# ======================================================================================================
# Focos, pluma con cadena, letrero y rampa
# ======================================================================================================


def focos():
    """Dos focos industriales sobre el portón, en brazos de tubo, con la cara de luz (neón cian) aparte."""
    p = Pieza("focos", peso_uv=1.5)
    neon = Pieza("focos_neon", peso_uv=0.4)
    b, a = p.baja, p.alta
    pl = FRENTE
    luces = []
    for xx in (-2.75, -0.45):
        zb = 4.98
        # Placa en la pared, brazo y rótula.
        caja_plano(b, pl, xx - 0.12, xx + 0.12, zb - 0.16, zb + 0.16, ONDA_C, ONDA_C + 0.03, "metal_oscuro",
                   sin=("+y",))
        for dz in (-0.1, 0.1):
            a.cupula(pl.p(xx, zb + dz, ONDA_C + 0.03), pl.n, 0.018, "acero", alto=0.011, lados=6)
        punta = pl.p(xx, zb + 0.25, 0.95)
        b.tubo([pl.p(xx, zb, ONDA_C + 0.03), pl.p(xx, zb + 0.12, 0.5), punta], 0.035, "metal_oscuro", lados=5,
               radio_curva=0.15, pasos_curva=1, tapa_ini=False)
        # Cuerpo del foco: carcasa troncocónica con aletas, mirando hacia abajo y afuera.
        dirv = (pl.n * 0.55 + Vector((0, 0, -1))).normalized()
        c = punta + Vector((0, 0, -0.04))
        b.revolucion([(0.0, -0.05), (0.14, -0.05), (0.2, 0.08), (0.26, 0.24), (0.27, 0.27), (0.22, 0.27)], c, 10,
                     "carcasa_foco", eje=dirv, tapa_ini=True, tapa_fin=False)
        for k in range(6):
            ang = math.tau * k / 6
            u, v = base_de(dirv)
            r = u * math.cos(ang) + v * math.sin(ang)
            b.caja(c + dirv * 0.06 + r * 0.17, (0.012, 0.012, 0.012), "carcasa_foco")
            a.caja(c + dirv * 0.09 + r * 0.16, (0.02, 0.02, 0.14), "carcasa_foco",
                   giro=dirv.to_track_quat("Z", "Y").to_matrix() @ rot("Z", math.degrees(ang)))
        neon.baja.revolucion([(0.235, 0.255), (0.0, 0.255)], c, 10, "neon", eje=dirv, tapa_ini=False, tapa_fin=False)
        # Rejilla del cristal (dos varillas).
        for ang in (0.0, math.pi / 2):
            u, v = base_de(dirv)
            r = u * math.cos(ang) + v * math.sin(ang)
            b.tubo([c + dirv * 0.27 - r * 0.24, c + dirv * 0.27 + r * 0.24], 0.01, "metal_oscuro", lados=3)
        luces.append(list(c + dirv * 0.35))
        # Cable del foco por la pared.
        b.tubo([pl.p(xx + 0.1, zb - 0.1, ONDA_C + 0.03), pl.p(xx + 0.2, zb - 0.3, ONDA_C + 0.04),
                pl.p(xx + 0.7, zb - 0.32, ONDA_C + 0.04)], 0.016, "goma", lados=4, radio_curva=0.08, pasos_curva=2)
    p.extra["luz_foco_izq"] = luces[0]
    p.extra["luz_foco_der"] = luces[1]
    return [p, neon]


def _eslabon(c, centro, eje_largo, normal, largo=0.2, ancho=0.12, r=0.026, lados=4, n=6):
    """Eslabón de cadena: anillo alargado (estadio) hecho con un tubo cerrado."""
    u = Vector(eje_largo).normalized()
    v = Vector(normal).normalized().cross(u).normalized()
    pts = []
    rr = ancho / 2 - r
    recto = largo / 2 - ancho / 2
    for k in range(n):
        t = math.tau * k / n
        x = math.cos(t) * rr
        y = math.sin(t) * rr
        y += recto if y > 1e-6 else (-recto if y < -1e-6 else 0)
        pts.append(Vector(centro) + v * x + u * y)
    pts.append(pts[0])
    c.tubo(pts, r, "cadena", lados=lados, tapa_ini=False, tapa_fin=False)


def pluma_cadena():
    """Pluma de perfil en I sobre el portón con su tornapunta, polea, cadena gruesa y el gancho en C."""
    p = Pieza("pluma_cadena", peso_uv=1.7)
    b, a = p.baja, p.alta
    pl = FRENTE
    xc, zb = -1.6, 5.45
    largo = 1.75
    # Perfil en I: alas y alma.
    for dz in (-0.12, 0.12):
        caja_plano(b, pl, xc - 0.1, xc + 0.1, zb + dz - 0.02, zb + dz + 0.02, ONDA_C, largo, "pintura_amarilla_pluma")
    caja_plano(b, pl, xc - 0.02, xc + 0.02, zb - 0.1, zb + 0.1, ONDA_C, largo, "pintura_amarilla_pluma",
               sin=("-z", "+z"))
    # Placa de anclaje con cuatro pernos y tornapunta en diagonal.
    caja_plano(b, pl, xc - 0.2, xc + 0.2, 4.7, zb + 0.22, ONDA_C, ONDA_C + 0.04, "pintura_amarilla_pluma", sin=("+y",))
    for dx in (-0.13, 0.13):
        for zz in (4.8, zb + 0.12):
            tornillo(p, pl.p(xc + dx, zz, ONDA_C + 0.04), pl.n, 0.03, "acero")
    pa, pb = pl.p(xc, 4.82, ONDA_C + 0.04), pl.p(xc, zb - 0.13, largo * 0.62)
    b.tubo([pa, pb], 0.04, "pintura_amarilla_pluma", lados=6)
    # Carro y polea en la punta.
    caja_plano(b, pl, xc - 0.14, xc + 0.14, zb - 0.32, zb - 0.12, largo - 0.42, largo - 0.12, "metal_oscuro")
    b.cilindro(pl.p(xc - 0.05, zb - 0.38, largo - 0.27), (1, 0, 0), 0.11, 0.1, "acero_rueda", lados=10)
    b.caja_de((xc - 0.12, Y0 - largo + 0.2, zb - 0.62), (xc + 0.12, Y0 - largo + 0.34, zb - 0.32), "metal_oscuro")
    # Cadena gruesa: eslabones alternos (uno de frente, otro de canto).
    ztop = zb - 0.62
    y = Y0 - largo + 0.27
    n = 9
    paso = 0.17
    for k in range(n):
        cz = ztop - 0.06 - k * paso
        normal = Vector((1, 0, 0)) if k % 2 == 0 else Vector((0, 1, 0))
        _eslabon(b, (xc, y, cz), (0, 0, 1), normal, largo=0.23, ancho=0.14, r=0.026)
    zg = ztop - 0.06 - (n - 1) * paso - 0.12
    # Gancho en C: anillo de suspensión, caña y la C con su punta (perfil de chapa gruesa extruido).
    b.revolucion([(0.0, -0.04), (0.075, -0.04), (0.075, 0.04), (0.0, 0.04)], (xc, y, zg + 0.03), 8,
                 "gancho_amarillo", eje=(1, 0, 0))
    perfil = []
    for k in range(13):
        t = math.radians(-90 + 300 * k / 12)
        perfil.append((math.cos(t) * 0.3, -0.3 + math.sin(t) * 0.3))
    exterior = [(0.06, 0.0), (-0.06, 0.0)] + [(x * 1.0, y_ - 0.02) for x, y_ in perfil[::-1]]
    # C hecha con un tubo grueso de sección rectangular (cuatro lados).
    camino = [Vector((xc, y + x, zg + z)) for x, z in [(0.0, 0.0)] +
              [(math.cos(math.radians(a_)) * 0.27 - 0.0, -0.45 + math.sin(math.radians(a_)) * 0.27)
               for a_ in range(90, -210, -30)]]
    b.tubo(camino, 0.055, "gancho_amarillo", lados=5, radio_curva=0.0, tapa_ini=False,
           radios=[0.045, 0.048, 0.054, 0.06, 0.064, 0.066, 0.066, 0.062, 0.056, 0.048, 0.04])
    del exterior
    texto(a, "1T", Vector((xc + 0.05, y + 0.27, zg - 0.45)), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.07, 0.004,
          "pintura_negra")
    p.extra["gancho"] = [xc, y, zg - 0.72]
    return p


def cartel_taller():
    """Letrero «TALLER» en el arco de la fachada: tablero de chapa con borde y letras de chapa recortada."""
    p = Pieza("cartel_taller", peso_uv=2.2)
    b, a = p.baja, p.alta
    pl = FRENTE
    x0, x1, z0, z1 = 0.45, 3.35, 4.72, 5.42
    caja_plano(b, pl, x0, x1, z0, z1, ONDA_C + 0.04, ONDA_C + 0.08, "cartel_fondo", sin=("+y",))
    for (ua, ub, va, vb) in ((x0, x1, z0, z0 + 0.05), (x0, x1, z1 - 0.05, z1), (x0, x0 + 0.05, z0, z1),
                             (x1 - 0.05, x1, z0, z1)):
        caja_plano(b, pl, ua, ub, va, vb, ONDA_C + 0.08, ONDA_C + 0.1, "acero_gastado", sin=("+y",))
    for xx in (x0 + 0.2, x1 - 0.2):
        caja_plano(b, pl, xx - 0.04, xx + 0.04, z0 + 0.05, z1 - 0.05, ONDA_C, ONDA_C + 0.04, "metal_oscuro",
                   sin=("+y",))
    texto(b, "TALLER", pl.p((x0 + x1) / 2, (z0 + z1) / 2, ONDA_C + 0.08), pl.u, pl.v, pl.n, 0.42, 0.035,
          "letras_taller", ancho_max=2.5)
    for xx in (x0 + 0.1, x1 - 0.1):
        for zz in (z0 + 0.1, z1 - 0.1):
            a.cupula(pl.p(xx, zz, ONDA_C + 0.1), pl.n, 0.02, "acero", alto=0.012, lados=6)
    return p


def rampa():
    """Rampa de chapa estriada (patrón de diamante) delante del portón: de la explanada al umbral, muy suave."""
    p = Pieza("rampa", peso_uv=1.4)
    b, a = p.baja, p.alta
    x0, x1 = HUECO["x0"] - 0.15, HUECO["x1"] + 0.15
    ya, yb, yc = Y0 - 1.45, Y0 - 0.35, Y0 + 0.02
    za, zb = LOSA_Z + 0.008, LOSA_Z + 0.07
    perfil = [(ya, LOSA_Z), (ya, za), (yb, zb), (yc, zb), (yc, LOSA_Z)]
    b.placa([(y, z) for y, z in perfil], Vector((x0, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0)),
            x1 - x0, "rampa_diamante", atras=True)
    # Diamantes en relieve (malla alta), cruzados como en la chapa de verdad.
    y = ya + 0.08
    fila = 0
    while y < yc - 0.04:
        z = za + (zb - za) * min(1.0, (y - ya) / (yb - ya))
        pend = math.degrees(math.atan((zb - za) / (yb - ya))) if y < yb else 0.0
        x = x0 + 0.08 + (0.07 if fila % 2 else 0.0)
        while x < x1 - 0.06:
            ang = 45 if (int((x - x0) / 0.14) + fila) % 2 else -45
            a.caja((x, y, z + 0.006), (0.11, 0.028, 0.014), "rampa_diamante",
                   giro=rot("X", pend) @ rot("Z", ang))
            x += 0.14
        y += 0.1
        fila += 1
    # Pletinas de los bordes y tornillos a la losa.
    for xx in (x0 + 0.04, x1 - 0.04):
        for yy in (ya + 0.12, (ya + yb) / 2, yb + 0.1):
            zz = za + (zb - za) * min(1.0, (yy - ya) / (yb - ya))
            tornillo(p, (xx, yy, zz), (0, 0, 1), 0.03, "acero", en_baja=False)
    p.extra["centro"] = [(x0 + x1) / 2, (ya + yc) / 2, zb]
    return p


# ======================================================================================================
# Soldadora, compresor, bidones
# ======================================================================================================


def soldadora():
    """Soldadora portátil junto al portón: caja con asa de tubo, mandos, cables enrollados y la careta colgada."""
    p = Pieza("soldadora", peso_uv=2.0)
    b, a = p.baja, p.alta
    o = Vector((-4.75, Y0 - 1.0, LOSA_Z))
    g = rot("Z", 8)

    def P(x, y, z):
        return o + g @ Vector((x, y, z))

    w, d, h = 0.95, 0.6, 0.72
    caras = b.caja(Vector((0, 0, 0)), (w, d, h), "pintura_soldadora")
    b.transformar(b.verts_de(caras), Matrix.Translation(P(0, 0, 0.12 + h / 2)) @ g.to_4x4())
    # Patas de goma, ruedas atrás y asa de tubo.
    for x in (-w / 2 + 0.1, w / 2 - 0.1):
        caras = b.caja(Vector((0, 0, 0)), (0.12, 0.12, 0.12), "goma")
        b.transformar(b.verts_de(caras), Matrix.Translation(P(x, -d / 2 + 0.1, 0.06)) @ g.to_4x4())
        b.cilindro(P(x, d / 2 - 0.12, 0.12), g @ Vector((1, 0, 0)), 0.12, 0.06, "goma", lados=8)
    for x in (-w / 2 + 0.12, w / 2 - 0.12):
        b.tubo([P(x, -0.12, 0.12 + h), P(x, -0.12, 0.12 + h + 0.18), P(x, 0.12, 0.12 + h + 0.18),
                P(x, 0.12, 0.12 + h)], 0.025, "acero_pulido", lados=5, radio_curva=0.06, pasos_curva=1,
               tapa_ini=False, tapa_fin=False)
    b.tubo([P(-w / 2 + 0.12, 0.0, 0.12 + h + 0.18), P(w / 2 - 0.12, 0.0, 0.12 + h + 0.18)], 0.03, "acero_pulido",
           lados=6)
    for x in (-w / 2 + 0.12, w / 2 - 0.12):
        b.tubo([P(x, -0.12, 0.12 + h + 0.18), P(x, 0.12, 0.12 + h + 0.18)], 0.025, "acero_pulido", lados=6)
    # Panel de delante: mandos, pantalla (neón en el atlas de emisión), interruptor y bornes.
    fy = -d / 2
    n = g @ Vector((0, -1, 0))
    caras = b.caja(Vector((0, 0, 0)), (w - 0.12, 0.02, h - 0.14), "plastico_negro")
    b.transformar(b.verts_de(caras), Matrix.Translation(P(0, fy - 0.01, 0.12 + h / 2)) @ g.to_4x4())
    for x, z, r in ((-0.25, 0.62, 0.065), (0.0, 0.62, 0.065)):
        b.revolucion([(r, 0.0), (r * 0.9, 0.06), (0.0, 0.065)], P(x, fy - 0.02, z), 8, "plastico_negro", eje=n,
                      tapa_ini=False)
        a.caja(P(x, fy - 0.085, z + r * 0.5), (0.012, 0.004, 0.035), "plastico_blanco", giro=g)
    caras = b.caja(Vector((0, 0, 0)), (0.2, 0.015, 0.09), "neon")
    b.transformar(b.verts_de(caras), Matrix.Translation(P(0.27, fy - 0.025, 0.65)) @ g.to_4x4())
    for x in (-0.2, 0.05):
        b.revolucion([(0.05, 0.0), (0.05, 0.04), (0.035, 0.05), (0.0, 0.05)], P(x, fy - 0.02, 0.3), 8, "laton",
                     eje=n, tapa_ini=False)
    caras = b.caja(Vector((0, 0, 0)), (0.07, 0.04, 0.11), "plastico_rojo")
    b.transformar(b.verts_de(caras), Matrix.Translation(P(0.3, fy - 0.04, 0.32)) @ g.to_4x4())
    texto(a, "MIG 250", P(-0.1, fy - 0.021, 0.79), g @ Vector((1, 0, 0)), Vector((0, 0, 1)), n, 0.05, 0.002,
          "plastico_blanco", ancho_max=0.35)
    # Rejillas de ventilación en los costados (malla alta).
    for s in (-1, 1):
        for k in range(7):
            a.caja(P(s * (w / 2 + 0.002), -0.15 + k * 0.05, 0.45), (0.006, 0.025, 0.3), "negro_mate", giro=g)
    # Cables enrollados colgados de los costados del asa (dos rollos) y el que baja a la pinza de masa.
    for s, mat in ((-1, "goma"), (1, "cable_rojo_soldadura")):
        c = P(s * (w / 2 + 0.06), 0.0, 0.5)
        eje = g @ Vector((s, 0, 0))
        u, v = base_de(eje)
        pts = []
        for k in range(21):
            t = math.tau * k / 8
            pts.append(c + u * math.cos(t) * 0.24 + v * (math.sin(t) * 0.3) + eje * (0.03 * k / 8))
        b.tubo(pts, 0.027, mat, lados=4, tapa_ini=False, tapa_fin=False)
    # Cable de la pinza de masa hasta la rampa (la pinza agarrada a su borde) y la antorcha encima de la caja.
    pinza = Vector((HUECO["x0"] - 0.05, Y0 - 1.2, LOSA_Z + 0.03))
    b.tubo([P(0.05, fy - 0.05, 0.3), P(0.05, fy - 0.2, 0.15), P(0.6, fy - 0.45, 0.04), pinza + Vector((-0.4, 0.02, 0.0)),
            pinza + Vector((-0.12, 0.0, 0.0))], 0.026, "goma", lados=4, radio_curva=0.15, pasos_curva=1)
    for dz in (-0.02, 0.05):
        b.caja(pinza + Vector((0.0, 0.0, dz + 0.03)), (0.22, 0.06, 0.03), "cobre", giro=rot("Y", -10 if dz < 0 else 8))
    b.tubo([P(-0.2, fy - 0.05, 0.3), P(-0.25, fy - 0.2, 0.2), P(-0.45, -0.1, 0.12 + h + 0.05),
            P(-0.1, 0.05, 0.12 + h + 0.03)], 0.03, "cable_rojo_soldadura", lados=4, radio_curva=0.12, pasos_curva=1)
    b.tubo([P(-0.1, 0.05, 0.12 + h + 0.03), P(0.2, 0.08, 0.12 + h + 0.04), P(0.38, 0.12, 0.12 + h + 0.02)], 0.035,
           "plastico_negro", lados=6, radios=[0.035, 0.04, 0.018])
    # Careta de soldador colgada del asa por la cinta: casco curvo y visor oscuro.
    cc = P(w / 2 - 0.12, -0.24, 0.12 + h + 0.0)
    gm = g @ rot("X", 12)
    perfil = [(0.0, 0.0), (0.16, 0.01), (0.2, 0.09), (0.22, 0.2), (0.21, 0.32), (0.15, 0.4), (0.0, 0.42)]
    b.revolucion(perfil, cc + gm @ Vector((0, -0.05, -0.38)), 8, "mascara", eje=gm @ Vector((0, 0, 1)), tapa_ini=False,
                 tapa_fin=False, escala=(1.0, 0.55))
    caras = b.caja(Vector((0, 0, 0)), (0.17, 0.02, 0.08), "vidrio_oscuro")
    b.transformar(b.verts_de(caras), Matrix.Translation(cc + gm @ Vector((0, -0.17, -0.12))) @ gm.to_4x4())
    b.tubo([P(w / 2 - 0.12, -0.12, 0.12 + h + 0.18), cc + gm @ Vector((-0.12, 0.0, -0.05)),
            cc + gm @ Vector((-0.2, 0.02, -0.25))], 0.012, "goma", lados=4)
    p.extra["chispas"] = list(pinza + Vector((0, 0, 0.1)))
    return p


def compresor():
    """Compresor: calderín horizontal con patas y ruedas, motor y bomba con aletas, guardapoleas y manómetro."""
    p = Pieza("compresor", peso_uv=1.6)
    b, a = p.baja, p.alta
    xc = MX + ONDA_C + 0.6
    y0, y1 = -4.25, -2.05
    zc = LOSA_Z + 0.55
    r = 0.4
    # Calderín: cuerpo y fondos abombados.
    perfil = [(0.0, -0.17), (0.25, -0.13), (0.37, -0.05), (r, 0.03), (r, y1 - y0 - 0.03), (0.37, y1 - y0 + 0.05),
              (0.25, y1 - y0 + 0.13), (0.0, y1 - y0 + 0.17)]
    b.revolucion(perfil, (xc, y0, zc), 12, "pintura_compresor", eje=(0, 1, 0), tapa_ini=False, tapa_fin=False)
    for yy in (y0 + 0.3, y1 - 0.3):
        a.tubo([Vector((xc + math.cos(t) * (r + 0.004), yy, zc + math.sin(t) * (r + 0.004)))
                for t in [math.tau * k / 24 for k in range(25)]], 0.01, "soldadura", lados=4, tapa_ini=False,
               tapa_fin=False)
    # Patas y ruedas.
    for yy in (y0 + 0.25,):
        for sx in (-1, 1):
            b.tubo([(xc + sx * 0.18, yy, zc - 0.32), (xc + sx * 0.3, yy, LOSA_Z + 0.04)], 0.035, "metal_oscuro",
                   lados=5)
            b.caja((xc + sx * 0.3, yy, LOSA_Z + 0.02), (0.14, 0.14, 0.04), "goma")
    for sx in (-1, 1):
        b.cilindro((xc + sx * 0.36, y1 - 0.25, LOSA_Z + 0.16), (sx, 0, 0), 0.16, 0.08, "goma", lados=10)
        b.cilindro((xc + sx * 0.36, y1 - 0.25, LOSA_Z + 0.16), (sx, 0, 0), 0.07, 0.1, "acero", lados=6)
    # Placa encima, motor (cilindro con aletas) y bomba (bloque con aletas y cabeza).
    zt = zc + r + 0.02
    b.caja_de((xc - 0.3, y0 + 0.25, zc + r - 0.04), (xc + 0.3, y1 - 0.25, zt), "metal_oscuro")
    b.cilindro((xc, y0 + 0.4, zt + 0.22), (0, 1, 0), 0.2, 0.62, "pintura_motor", lados=10)
    for k in range(10):
        yy = y0 + 0.45 + k * 0.055
        a.tubo([Vector((xc + math.cos(t) * 0.205, yy, zt + 0.22 + math.sin(t) * 0.205)) for t in
                [math.tau * j / 16 for j in range(17)]], 0.012, "pintura_motor", lados=3, tapa_ini=False, tapa_fin=False)
    b.caja_de((xc - 0.06, y0 + 0.45, zt), (xc + 0.06, y0 + 0.95, zt + 0.06), "metal_oscuro")
    by = y0 + 1.45
    b.caja_de((xc - 0.22, by - 0.22, zt), (xc + 0.22, by + 0.22, zt + 0.32), "aluminio_fundido")
    b.caja_de((xc - 0.26, by - 0.26, zt + 0.32), (xc + 0.26, by + 0.26, zt + 0.42), "aluminio_fundido")
    for k in range(5):
        b.caja_de((xc - 0.27, by - 0.27, zt + 0.1 + k * 0.045), (xc + 0.27, by + 0.27, zt + 0.12 + k * 0.045),
                  "aluminio_fundido")
    b.cilindro((xc, by, zt + 0.42), (0, 0, 1), 0.08, 0.12, "acero_hollin", lados=8)
    # Guardapoleas (de la polea del motor a la de la bomba), pintado.
    b.caja_de((xc - 0.33, y0 + 1.0, zt + 0.02), (xc - 0.23, by + 0.15, zt + 0.42), "pintura_compresor")
    # Manómetro mirando hacia fuera (+x) con su cristal, y la válvula de seguridad.
    mc = Vector((xc + 0.32, by + 0.42, zt + 0.15))
    b.tubo([(xc + 0.15, by + 0.2, zt + 0.05), (xc + 0.2, by + 0.42, zt + 0.08), mc - Vector((0.07, 0, 0))], 0.02,
           "laton", lados=5, radio_curva=0.04, pasos_curva=1)
    b.revolucion([(0.0, -0.035), (0.13, -0.035), (0.13, 0.03), (0.11, 0.035), (0.11, 0.02)], mc, 14, "acero_pulido",
                 eje=(1, 0, 0), tapa_ini=True, tapa_fin=False)
    b.revolucion([(0.11, 0.02), (0.0, 0.02)], mc, 14, "esfera_manometro", eje=(1, 0, 0), tapa_ini=False,
                  tapa_fin=False)
    # Marcas y aguja del manómetro (malla alta).
    for k in range(11):
        t = math.radians(225 - 27 * k)
        dz, dy = math.sin(t), -math.cos(t)
        a.caja(mc + Vector((0.022, dy * 0.085, dz * 0.085)), (0.003, 0.006, 0.022), "pintura_negra",
               giro=rot("X", math.degrees(math.atan2(dy, dz))))
    a.placa([(-0.006, -0.01), (0.006, -0.01), (0.0, 0.09)], mc + Vector((0.021, 0, 0)), Vector((0, -1, 0)),
            Vector((0, 0, 1)), Vector((1, 0, 0)), 0.002, "plastico_rojo")
    a.anillo_placa([(math.cos(t) * 0.085, math.sin(t) * 0.085) for t in [math.radians(-45 + 2.5 * k) for k in range(20)]],
                   [(math.cos(t) * 0.07, math.sin(t) * 0.07) for t in [math.radians(-45 + 2.5 * k) for k in range(20)]],
                   mc + Vector((0.02, 0, 0)), Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0)), 0.002,
                   "plastico_rojo")
    b.cilindro((xc - 0.1, y1 - 0.4, zc + r), (0, 0, 1), 0.03, 0.14, "laton", lados=6)
    b.revolucion([(0.04, 0.0), (0.04, 0.03), (0.0, 0.04)], (xc - 0.1, y1 - 0.4, zc + r + 0.14), 6, "laton",
                 tapa_ini=False)
    # Grifo de purga abajo (con charco de aceite y agua debajo en la losa).
    b.cilindro((xc, y0 + 0.9, zc - r + 0.02), (0, 0, -1), 0.025, 0.08, "laton", lados=6)
    p.extra["salida_aire"] = [xc - 0.2, y1 - 0.2, zc + 0.1]
    p.extra["purga"] = [xc, y0 + 0.9, LOSA_Z]
    return p


def manguera(salida):
    """Manguera de aire: del compresor sube a un gancho de la pared donde está enrollada."""
    p = Pieza("manguera_compresor", peso_uv=1.5)
    b, a = p.baja, p.alta
    pl = DER
    gu, gv = -3.1, 2.75
    # Gancho de pared (placa + varilla doblada).
    caja_plano(b, pl, gu - 0.1, gu + 0.1, gv - 0.12, gv + 0.12, ONDA_C, ONDA_C + 0.03, "metal_oscuro", sin=("+y",))
    for dv in (-0.08, 0.08):
        a.cupula(pl.p(gu, gv + dv, ONDA_C + 0.03), pl.n, 0.016, "acero", alto=0.01, lados=6)
    b.tubo([pl.p(gu, gv, ONDA_C + 0.03), pl.p(gu, gv - 0.02, 0.45), pl.p(gu, gv + 0.08, 0.5)], 0.022, "metal_oscuro",
           lados=5, radio_curva=0.05, pasos_curva=2)
    # Rollo: espiras que cuelgan del gancho (se apoyan arriba y caen abajo).
    c = pl.p(gu, gv - 0.36, 0.3)
    pts = []
    for k in range(31):
        t = math.tau * k / 10 + math.pi / 2
        rr = 0.36 + 0.015 * math.sin(k * 0.9)
        pts.append(c + pl.u * (math.cos(t) * rr * 0.92) + pl.v * (math.sin(t) * rr) + pl.n * (-0.07 + 0.05 * k / 10))
    b.tubo(pts, 0.03, "manguera", lados=4, tapa_ini=False, tapa_fin=False)
    # Tramo que baja al compresor y racor rápido.
    ini = pts[0]
    b.tubo([ini, pl.p(gu + 0.15, gv - 0.85, 0.35), pl.p(gu + 0.4, 1.6, 0.6), Vector(salida)], 0.03, "manguera",
           lados=4, radio_curva=0.2, pasos_curva=2)
    fin = pts[-1]
    b.tubo([fin, fin - pl.v * 0.25 + pl.n * 0.02], 0.028, "manguera", lados=5)
    b.cilindro(fin - pl.v * 0.25 + pl.n * 0.02, -pl.v, 0.035, 0.12, "laton", lados=6)
    return p


def _bidon(c, a, centro, mat, giro=0.0, r=0.5, h=1.45):
    """Bidón de chapa: aros de rodadura, bordes engatillados y tapas con rosca."""
    perfil = [(r - 0.02, 0.0), (r, 0.06)]
    for z in (h * 0.33, h * 0.67):
        perfil += [(r - 0.012, z - 0.05), (r + 0.028, z), (r - 0.012, z + 0.05)]
    perfil += [(r, h - 0.04), (r - 0.03, h), (r - 0.05, h - 0.03), (0.0, h - 0.03)]
    c.revolucion(perfil, centro, 12, mat, giro=giro, tapa_ini=True, tapa_fin=False)
    # Tapón grande y pequeño (rosca en la malla alta).
    top = Vector(centro) + Vector((0, 0, h - 0.03))
    tapones = []
    for k, (dx, dy, rr) in enumerate(((r * 0.55, 0.0, 0.085), (-r * 0.6, 0.12, 0.05))):
        q = top + Vector((dx * math.cos(giro) - dy * math.sin(giro), dx * math.sin(giro) + dy * math.cos(giro), 0))
        c.revolucion([(rr, 0.0), (rr, 0.035), (0.0, 0.045)], q, 6, "acero", tapa_ini=False)
        for j in range(8):
            t = math.tau * j / 8
            a.caja(q + Vector((math.cos(t) * rr, math.sin(t) * rr, 0.02)), (0.012, 0.012, 0.03), "acero",
                   giro=rot("Z", math.degrees(t)))
        tapones.append(q)
    return tapones


def bidones():
    """Tres bidones contra el lateral izquierdo: aceite (azul, con embudo), combustible (rojo) y refrigerante (verde)."""
    p = Pieza("bidones", peso_uv=1.5)
    b, a = p.baja, p.alta
    xb = -MX - ONDA_C - 0.62
    azul = _bidon(b, a, (xb, -3.95, LOSA_Z), "bidon_azul", giro=0.3)
    _bidon(b, a, (xb + 0.05, -2.82, LOSA_Z), "bidon_rojo", giro=1.4)
    _bidon(b, a, (xb - 0.95, -3.45, LOSA_Z), "bidon_verde", giro=2.2, h=1.45)
    # Embudo metido en la boca del azul (el tapón grande quitado: se deja el pequeño).
    q = azul[0] + Vector((0, 0, 0.04))
    b.revolucion([(0.03, -0.05), (0.03, 0.12), (0.06, 0.15), (0.2, 0.32), (0.21, 0.34), (0.19, 0.34), (0.05, 0.16),
                  (0.0, 0.16)], q, 12, "embudo", tapa_ini=False, tapa_fin=False)
    # Chorretones y etiquetas pintadas (en el material); trapo sucio colgando del rojo.
    b.tubo([Vector((xb + 0.05 + 0.3, -2.82 - 0.4, LOSA_Z + 1.44)), Vector((xb + 0.05 + 0.4, -2.82 - 0.34, LOSA_Z + 1.4)),
            Vector((xb + 0.05 + 0.46, -2.82 - 0.3, LOSA_Z + 1.1))], 0.04, "trapo", lados=4, radios=[0.05, 0.06, 0.04])
    p.extra["embudo"] = list(q + Vector((0, 0, 0.3)))
    return p


# ======================================================================================================
# Entorno: piezas esperando reparación, carretilla e interior
# ======================================================================================================


def _tubo_hueco(c, a_, b_, r, grosor, mat, lados=8):
    """Tubo con grosor (se ve la boca por dentro)."""
    a_, b_ = Vector(a_), Vector(b_)
    eje = b_ - a_
    c.revolucion([(r - grosor, eje.length), (r - grosor, 0.0), (r, 0.0), (r, eje.length), (r - grosor, eje.length)],
                 a_, lados, mat, eje=eje, tapa_ini=False, tapa_fin=False)


def piezas_apiladas():
    """Al lado del taller, esperando turno: tres tubos sobre dos traviesas, una chapa curva y una turbina rota."""
    p = Pieza("piezas_apiladas", peso_uv=1.4)
    b, a = p.baja, p.alta
    xb = -MX - ONDA_C - 1.0
    # Traviesas de madera.
    for yy in (2.0, 3.6):
        b.caja_de((xb - 0.75, yy - 0.12, LOSA_Z), (xb + 0.55, yy + 0.12, LOSA_Z + 0.18), "madera_traviesa", sin=("-z",))
    # Tubos: dos abajo y uno encima (a lo largo de Y).
    r = 0.24
    z1 = LOSA_Z + 0.18 + r
    for x, z, mat in ((xb - 0.4, z1, "tubo_oxidado"), (xb + 0.1, z1, "tubo_oxidado"),
                      (xb - 0.15, z1 + 2 * r * 0.87, "tubo_pintado")):
        _tubo_hueco(b, (x, 1.6, z), (x, 4.05 if mat != "tubo_pintado" else 3.75, z), r, 0.04, mat, lados=8)
    # Calzos para que no rueden.
    for x in (xb - 0.7, xb + 0.4):
        b.caja((x, 2.0, LOSA_Z + 0.26), (0.1, 0.2, 0.14), "madera_traviesa", giro=rot("Y", 25 if x > xb else -25))
    # Chapa curva apoyada contra los tubos.
    curva = []
    for k in range(7):
        t = math.radians(-40 + 80 * k / 6)
        curva.append((math.sin(t) * 0.9, (1 - math.cos(t)) * 0.9))
    anillos = []
    o = Vector((xb - 0.95, 1.2, LOSA_Z))
    g = rot("Z", 15) @ rot("Y", 18)
    for yy, k in ((0.0, 0), (1.1, 1)):
        anillos.append([o + g @ Vector((-dz - (0.0 if k == 0 else 0.0), x, yy + 0.0)) for x, dz in curva])
    sup = [[o + g @ Vector((-dz, x, 0.05)) for x, dz in curva], [o + g @ Vector((-dz, x, 1.15)) for x, dz in curva]]
    inf = [[o + g @ Vector((-dz - 0.04, x, 0.05)) for x, dz in curva],
           [o + g @ Vector((-dz - 0.04, x, 1.15)) for x, dz in curva]]
    vs_s = [[b.v(q) for q in fila] for fila in sup]
    vs_i = [[b.v(q) for q in fila] for fila in inf]
    caras = []
    for k in range(len(curva) - 1):
        caras.append(b.cara([vs_s[0][k], vs_s[0][k + 1], vs_s[1][k + 1], vs_s[1][k]], "chapa_curva", suave=True))
        caras.append(b.cara([vs_i[1][k], vs_i[1][k + 1], vs_i[0][k + 1], vs_i[0][k]], "chapa_curva", suave=True))
        caras.append(b.cara([vs_i[0][k], vs_i[0][k + 1], vs_s[0][k + 1], vs_s[0][k]], "chapa_curva"))
        caras.append(b.cara([vs_s[1][k], vs_s[1][k + 1], vs_i[1][k + 1], vs_i[1][k]], "chapa_curva"))
    caras.append(b.cara([vs_s[0][0], vs_s[1][0], vs_i[1][0], vs_i[0][0]], "chapa_curva"))
    caras.append(b.cara([vs_i[0][-1], vs_i[1][-1], vs_s[1][-1], vs_s[0][-1]], "chapa_curva"))
    b.recalcular(caras)
    del anillos
    # Turbina rota: carcasa con un mordisco, cubo y álabes (algunos doblados o partidos).
    tc = Vector((xb + 0.1, 4.65, LOSA_Z + 0.55))
    eje = Vector((0.3, 1.0, 0.15)).normalized()
    u, v = base_de(eje)
    lados = 12
    rc, prof = 0.5, 0.45
    anillos = []
    for z in (-prof / 2, prof / 2):
        anillos.append([tc + eje * z + (u * math.cos(math.tau * k / lados) + v * math.sin(math.tau * k / lados)) * rc
                        for k in range(lados)])
    # Carcasa abierta (sin dos segmentos: el golpe que la partió) con grosor.
    rota = {2, 3}
    for k in range(lados):
        if k in rota:
            continue
        j = (k + 1) % lados
        for r1, r2, inv in ((rc, rc, False), (rc - 0.05, rc - 0.05, True)):
            q = [tc + eje * z + (u * math.cos(math.tau * i / lados) + v * math.sin(math.tau * i / lados)) * r1
                 for z in (-prof / 2, prof / 2) for i in (k, j)]
            cara = [q[0], q[1], q[3], q[2]]
            f = b.poligono(cara if not inv else cara[::-1], "turbina", (0, 0, 0.0001))
            dirr = (u * math.cos(math.tau * (k + 0.5) / lados) + v * math.sin(math.tau * (k + 0.5) / lados))
            if (f.normal.dot(dirr) < 0) != inv:
                f.normal_flip()
        for z in (-prof / 2, prof / 2):
            q = [tc + eje * z + (u * math.cos(math.tau * i / lados) + v * math.sin(math.tau * i / lados)) * rr
                 for i in (k, j) for rr in (rc, rc - 0.05)]
            f = b.poligono([q[0], q[2], q[3], q[1]], "turbina", eje * (1 if z > 0 else -1))
    del anillos
    b.revolucion([(0.0, -0.2), (0.12, -0.2), (0.14, 0.1), (0.08, 0.22), (0.0, 0.25)], tc, 10, "turbina_cubo",
                  eje=eje)
    rnd = random.Random(5)
    for k in range(11):
        t = math.tau * k / 11
        dirr = u * math.cos(t) + v * math.sin(t)
        largo = 0.33
        if k in (2, 7):
            largo = 0.14  # partidos
        g = Matrix((dirr, eje.cross(dirr), eje)).transposed() @ rot("X", 35 + rnd.uniform(-8, 8))
        if k == 5:
            g = g @ rot("Y", 30)  # doblado
        b.caja(tc + dirr * (0.13 + largo / 2), (largo, 0.12, 0.012), "turbina", giro=g)
    p.extra["turbina"] = list(tc)
    return p


def carretilla():
    """Carretilla de mano (diablo) apoyada contra el lateral derecho: bastidor de tubo, pala, ruedas y asa."""
    p = Pieza("carretilla", peso_uv=1.5)
    b, a = p.baja, p.alta
    yc = 2.55
    inclin = 14.0
    pie = Vector((MX + ONDA_C + 0.72, yc, LOSA_Z))
    g = rot("Y", -inclin)

    def P(x, y, z):
        return pie + g @ Vector((x, y, z))

    alto = 2.55
    for s in (-1, 1):
        b.tubo([P(0.0, s * 0.32, 0.1), P(0.0, s * 0.32, alto - 0.3), P(0.0, s * 0.26, alto - 0.12),
                P(0.0, s * 0.1, alto)], 0.035, "pintura_carretilla", lados=5, radio_curva=0.15, pasos_curva=1,
               tapa_ini=True, tapa_fin=False)
    b.tubo([P(0.0, -0.1, alto), P(0.0, 0.1, alto)], 0.035, "pintura_carretilla", lados=6)
    for z in (0.65, 1.25, 1.85):
        b.tubo([P(0.0, -0.32, z), P(0.0, 0.32, z)], 0.025, "pintura_carretilla", lados=5)
    # Pala de chapa abajo.
    caras = b.caja(Vector((0, 0, 0)), (0.42, 0.62, 0.025), "acero_gastado")
    b.transformar(b.verts_de(caras), Matrix.Translation(P(-0.2, 0.0, 0.0)) @ g.to_4x4())
    # Ruedas con neumático y llanta, eje y soportes.
    for s in (-1, 1):
        c = P(0.24, s * 0.46, 0.22)
        eje_r = Vector((0, s, 0))
        b.revolucion([(0.12, -0.06), (0.22, -0.06), (0.24, 0.0), (0.22, 0.06), (0.12, 0.06)], c, 10,
                     "goma_rueda", eje=eje_r, tapa_ini=False, tapa_fin=False)
        b.revolucion([(0.0, -0.06), (0.12, -0.06), (0.12, 0.06), (0.05, 0.08), (0.0, 0.08)], c, 8, "pintura_carretilla",
                      eje=eje_r, tapa_ini=False)
        b.tubo([P(0.0, s * 0.32, 0.35), c + Vector((0, -s * 0.06, 0.0))], 0.03, "pintura_carretilla", lados=5)
    b.tubo([P(0.24, -0.4, 0.22), P(0.24, 0.4, 0.22)], 0.02, "acero", lados=5)
    # Asa: puños de goma.
    for s in (-1, 1):
        a.tubo([P(0.0, s * 0.02, alto), P(0.0, s * 0.09, alto)], 0.04, "goma", lados=8)
    return p


def interior():
    """Lo que se ve dentro por el portón y las ventanas: estantería con cajas, bloque de motor y taladro de minería."""
    p = Pieza("interior", peso_uv=0.5)
    lamp = Pieza("lampara_interior_neon_calido", peso_uv=0.2)
    b, a = p.baja, p.alta
    yi = Y1 - MURO
    # Estantería al fondo (dos módulos) con cajas.
    for x0 in (-5.4,):
        for xx in (x0, x0 + 1.9):
            b.caja_de((xx, yi - 0.75, LOSA_Z), (xx + 0.06, yi - 0.05, 3.2), "metal_oscuro", sin=("-z",))
        for z in (0.5, 1.4, 2.3, 3.15):
            b.caja_de((x0, yi - 0.75, z), (x0 + 1.96, yi - 0.05, z + 0.05), "metal_oscuro")
        rnd = random.Random(int(x0 * 10))
        for z in (0.55, 1.45, 2.35):
            x = x0 + 0.1
            while x < x0 + 1.7:
                w = rnd.uniform(0.35, 0.6)
                hh = rnd.uniform(0.35, 0.7)
                mat = rnd.choice(("carton", "pintura_roja_gastada", "carton", "bidon_azul"))
                b.caja_de((x, yi - 0.65, z), (min(x + w, x0 + 1.85), yi - 0.15, z + hh), mat, sin=("-z",))
                x += w + 0.05
    # Bloque de motor sobre un caballete en el centro.
    mc = Vector((-1.6, 1.6, LOSA_Z))
    b.caja_de(mc + Vector((-0.5, -0.4, 0.0)), mc + Vector((0.5, 0.4, 0.08)), "metal_oscuro", sin=("-z",))
    b.cilindro(mc + Vector((0, 0, 0.08)), (0, 0, 1), 0.08, 0.9, "metal_oscuro", lados=6)
    b.caja_de(mc + Vector((-0.55, -0.35, 1.0)), mc + Vector((0.55, 0.35, 1.6)), "aluminio_fundido")
    b.caja_de(mc + Vector((-0.6, -0.4, 1.6)), mc + Vector((0.6, 0.4, 1.75)), "pintura_compresor")
    # Taladro de minería tumbado en la mesa de la derecha.
    b.caja_de((2.0, 2.2, LOSA_Z), (4.6, 3.9, 1.6), "metal_banco", sin=("-z",))
    b.cilindro((2.4, 3.05, 1.85), (1, 0, 0), 0.24, 1.0, "pintura_soldadora", lados=10)
    b.cilindro((3.4, 3.05, 1.85), (1, 0, 0), 0.08, 0.8, "acero", lados=6, radio2=0.03)
    # Lámpara colgada del techo (pantalla) con la luz cálida aparte.
    lc = Vector((-1.6, 0.4, CUMBRE - 1.6))
    b.tubo([Vector((lc.x, lc.y, CUMBRE - TG - 0.02)), lc + Vector((0, 0, 0.25))], 0.012, "goma", lados=4)
    b.revolucion([(0.05, 0.25), (0.08, 0.2), (0.38, 0.0), (0.4, -0.02)][::-1], lc, 12, "metal_oscuro", tapa_ini=False,
                  tapa_fin=True)
    lamp.baja.revolucion([(0.0, 0.02), (0.15, 0.02), (0.2, -0.0)], lc, 10, "neon_calido", tapa_ini=False,
                         tapa_fin=False)
    p.extra["luz_interior"] = list(lc - Vector((0, 0, 0.3)))
    return [p, lamp]


# ======================================================================================================
# Todo junto
# ======================================================================================================


def construir():
    tech = techo()
    piezas = [losa(), zocalo(), muros(), marcos_huecos(), tech] + lucernarios() + extractor() + [canalones()]
    port = porton()
    piezas += port + [riel_porton(), rampa()]
    piezas += [puerta_lateral(), cartel_horario()]
    piezas += ventana_lateral() + ventana_trasera() + ventilador_trasero()
    piezas += [panel_herramientas(), banco_trabajo()]
    piezas += cuadro_electrico() + [senal_alto_voltaje()] + medidor_energia() + [cables()]
    piezas += focos() + [pluma_cadena(), cartel_taller()]
    sold = soldadora()
    comp = compresor()
    piezas += [sold, comp, manguera(comp.extra["salida_aire"]), bidones(), piezas_apiladas(), carretilla()]
    piezas += interior()
    H = HUECO
    porton_c = ((H["x0"] + H["x1"]) / 2, Y0 - 0.2, 2.2)
    P = {
        # Las que piden los materiales de las casas (casa_materiales).
        "manija": (MX + 0.2, 0.15, 1.95),
        "manija_agarre": (MX + 0.25, 0.1, 1.95),
        "zocalo_z": ZOC,
        "chimenea_boca": z_arco(EXTRACTOR.x) + 0.6,
        "puerta_z0": LOSA_Z,
        "pico_agarre": (0.0, 0.1),
        "bajante_pie": (MX + 0.6, Y1 - 0.45, 0.0),
        "puerta_suelo": (MX + 0.5, 0.65, LOSA_Z),
        "escalon_centro": (porton_c[0], Y0 - 0.9, LOSA_Z),
        "felpudo_centro": (porton_c[0], Y0 - 0.9, LOSA_Z),
        # Las del taller.
        "porton_centro": porton_c,
        "porton_suelo": (porton_c[0], Y0 - 1.8, LOSA_Z),
        "porton_borde_x": H["x1"],
        "porton_quemaduras_z": 1.0,
        "banco": (sum((BANCO["x0"], BANCO["x1"])) / 2, Y0 - 0.2, BANCO["z"]),
        "extractor": (EXTRACTOR.x, EXTRACTOR.y, z_arco(EXTRACTOR.x) + 0.5),
        "ventilador": (-VENTI_C[0], Y1 + 0.1, VENTI_C[1]),
        "soldadora": tuple(sold.extra["chispas"]),
        "compresor_purga": tuple(comp.extra["purga"]),
        "puerta_lateral_manija": (MX + 0.25, PUERTA_L["u0"] + 0.2, 1.95),
        "panel_x": (PANEL_H["x0"], PANEL_H["x1"]),
    }
    return piezas, P
