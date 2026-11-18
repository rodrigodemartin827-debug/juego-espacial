"""
Piezas de la casa del comerciante: tienda en la planta baja y vivienda arriba. Todo en STUDS, fachada a -Y.

Planta: muros de 11 × 8 studs (cara exterior del alma en x = ±5,5, y = ±4) sobre una base de medio stud con
porche delante (la tienda) y a la derecha (la puerta de casa, las cajas y la silla).

  fachada (-Y): escaparate azul con expositor, toldo a rayas, cartel «SUMINISTROS» con dos focos, puerta de la
                tienda acristalada («ABIERTO», campanilla), pizarra de precios, felpudo de rejilla y poste de amarre.
                Arriba: ventana con persiana a medio bajar y maceta, y un pretil con albardilla.
  lateral derecho (+X): puerta de casa (metálica, gastada), número 12, farol, medidor, silla plegable, cajas.
  lateral izquierdo (-X): ventana pequeña con cortina.
  detrás (+Y): bajante con su embudo.
  cubierta plana (cae hacia atrás): aire acondicionado y antena parabólica.

Reutiliza el constructor y las piezas genéricas de la casa del minero (casa_malla, casa_piezas).
"""

import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import casa_piezas as cp
from casa_malla import Pieza, base_de, rot
from casa_piezas import caja_plano, tornillo

# ======================================================================================================
# Medidas (studs)
# ======================================================================================================

BASE_Z = 0.5
ZOC_Z = 1.5
MX, MY = 5.5, 4.0
MURO = 0.3
PANEL = 0.06
JUNTA = 0.03
PB_TOP = 5.6                 # techo de la tienda (empieza la moldura del forjado)
MOLD = (5.6, 5.9)            # moldura del forjado
TECHO_F = 8.75               # cara de arriba de la cubierta junto al pretil
PEND_T = 0.035               # caída de la cubierta hacia atrás
LOSA = 0.25                  # grosor de la losa de cubierta
PRETIL = 9.25                # alto del pretil de la fachada
BASE = dict(x0=-5.85, x1=6.9, y0=-5.3, y1=4.35)

ESCAPARATE = dict(x0=-4.9, x1=1.5, z0=1.85, z1=4.35)   # hueco del cristal
MARCO_E = dict(x0=-5.2, x1=1.8, z0=1.5, z1=4.65)       # marco azul exterior
MAINELES = (-2.77, -0.63)
PUERTA_T = dict(x0=2.25, x1=4.15, z0=0.5, z1=4.6)
HOJA_T = dict(x0=2.3, x1=4.1, z0=0.6, z1=4.55, y0=-3.98, y1=-3.84)
EJE_T = Vector((2.27, -3.91, 0.0))
TIRADOR = Vector((3.55, -4.08, 2.4))
PUERTA_L = dict(u0=0.0, u1=1.6, v0=0.5, v1=4.5)          # en el plano del muro derecho (u = +y)
VENT_F = dict(x0=-3.0, x1=-0.4, z0=6.6, z1=8.0)
VENT_L = dict(u0=-0.6, u1=1.0, v0=6.5, v1=7.8)           # en el plano del muro izquierdo (u = -y)
CARTEL = dict(x0=-4.6, x1=1.2, z0=4.98, z1=5.52)


def z_techo(y):
    """Cara de arriba de la cubierta (cae hacia atrás)."""
    return TECHO_F - PEND_T * (y + MY)


def z_muro(y):
    return z_techo(y) - LOSA


FRENTE = cp.Plano((0, -MY, 0), (0, -1, 0))   # u = +x
FONDO = cp.Plano((0, MY, 0), (0, 1, 0))      # u = -x
IZQ = cp.Plano((-MX, 0, 0), (-1, 0, 0))      # u = -y
DER = cp.Plano((MX, 0, 0), (1, 0, 0))        # u = +y


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


# ======================================================================================================
# Texto en relieve (con la fuente de Blender)
# ======================================================================================================


def texto(c, cadena, origen, u, v, n, alto, grosor, mat, ancho_max=None, resolucion=1, alinear="CENTER"):
    """
    Letras de verdad: curva de texto de Blender convertida a malla, sin la tapa de atrás (va pegada a algo).
    `alto` es la altura de las mayúsculas en studs; el relieve sale en la dirección `n`.
    """
    cu = bpy.data.curves.new("texto_tmp", "FONT")
    cu.body = cadena
    cu.size = 1.0
    cu.align_x = alinear
    cu.align_y = "CENTER"
    cu.resolution_u = resolucion
    cu.extrude = 0.5
    ob = bpy.data.objects.new("texto_tmp", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    xs = [vv.co.x for vv in me.vertices]
    ys = [vv.co.y for vv in me.vertices]
    alto_mayus = max(ys) - min(ys) if ys else 1.0
    esc = alto / max(alto_mayus, 1e-6)
    ancho = (max(xs) - min(xs)) * esc
    if ancho_max and ancho > ancho_max:
        esc_x = esc * ancho_max / ancho
    else:
        esc_x = esc
    cy = (max(ys) + min(ys)) / 2
    cx = (max(xs) + min(xs)) / 2 if alinear == "CENTER" else 0.0
    o, u, v, n = Vector(origen), Vector(u), Vector(v), Vector(n)
    verts = []
    for vv in me.vertices:
        x, y, z = vv.co
        verts.append(c.v(o + u * ((x - cx) * esc_x) + v * ((y - cy) * esc) + n * ((z + 0.5) * grosor)))
    caras = []
    for pl in me.polygons:
        if all(me.vertices[i].co.z < -0.49 for i in pl.vertices):
            continue  # la tapa de atrás no se ve
        caras.append(c.cara([verts[i] for i in pl.vertices], mat))
    for vv in verts:
        if not vv.link_faces:
            c.bm.verts.remove(vv)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return caras


# ======================================================================================================
# Estructura
# ======================================================================================================


def base():
    p = Pieza("casa_base", peso_uv=0.8)
    p.baja.caja_de((BASE["x0"], BASE["y0"], 0), (BASE["x1"], BASE["y1"], BASE_Z), "hormigon", sin=("-z",))
    p.baja.caja_de((-5.2, 4.36, 0), (-4.6, 4.9, 0.07), "hormigon", sin=("-z",))  # donde cae el bajante
    return p


def _losa_gastada(nombre, x0, x1, y0, y1, z1, hund, centro_pisada, peso=1.6, semilla=3):
    p = Pieza(nombre, peso_uv=peso)
    rnd = random.Random(semilla)
    c = p.baja
    nx, ny = 6, 3
    arriba = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            fx, fy = i / nx, j / ny
            x, y = x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy
            h = 0.0
            if 0 < i < nx and 0 < j < ny:
                d = math.hypot((x - centro_pisada[0]) / ((x1 - x0) * 0.35), (y - centro_pisada[1]) / ((y1 - y0) * 0.6))
                h = hund * max(0.0, 1 - d * d)
            borde = 0.0 if (0 < i < nx and 0 < j < ny) else rnd.uniform(-0.01, 0.003)
            arriba[i, j] = c.v((x, y, z1 - h + borde))
    for i in range(nx):
        for j in range(ny):
            c.cara([arriba[i, j], arriba[i + 1, j], arriba[i + 1, j + 1], arriba[i, j + 1]], "losa")
    anillo = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)] + \
             [(i, ny) for i in range(nx, 0, -1)] + [(0, j) for j in range(ny, 0, -1)]
    abajo = {k: c.v((arriba[k].co.x, arriba[k].co.y, 0.0)) for k in anillo}
    for a in range(len(anillo)):
        k1, k2 = anillo[a], anillo[(a + 1) % len(anillo)]
        c.cara([abajo[k1], abajo[k2], arriba[k2], arriba[k1]], "losa")
    p.extra["centro"] = [centro_pisada[0], centro_pisada[1], z1]
    return p


def escalones():
    tienda = _losa_gastada("escalon_tienda", 1.75, 4.65, -6.08, -5.3, 0.27, 0.03, (3.2, -5.65), peso=1.6)
    lateral = _losa_gastada("escalon_lateral", 6.9, 7.65, -0.25, 1.85, 0.25, 0.022, (7.25, 0.8), peso=1.2,
                            semilla=8)
    return [tienda, lateral]


def zocalo():
    """Zócalo de sillería más regular que el del minero: dos hiladas, juntas a matacán, piedras casi iguales."""
    p = Pieza("casa_zocalo", peso_uv=1.0)
    rnd = random.Random(21)
    tramos = [(FRENTE, -MX - 0.13, PUERTA_T["x0"] - 0.05), (FRENTE, PUERTA_T["x1"] + 0.05, MX + 0.13),
              (FONDO, -MX - 0.13, MX + 0.13), (IZQ, -MY, MY), (DER, -MY, PUERTA_L["u0"] - 0.05),
              (DER, PUERTA_L["u1"] + 0.05, MY)]
    filas = [(BASE_Z, 0.975), (1.0, 1.45)]
    for pl, u0, u1 in tramos:
        caja_plano(p.baja, pl, u0, u1, BASE_Z, 1.46, 0.0, 0.075, "mortero", sin=("+y", "-z", "+z"), ocultas=("-y",))
        for k, (v0, v1) in enumerate(filas):
            u = u0 - (0.43 if k == 1 else 0.0)
            while u < u1 - 0.05:
                largo = rnd.uniform(0.78, 0.92)
                if u1 - (u + largo) < 0.3:
                    largo = u1 - u
                a, b = max(u, u0), min(u + largo, u1)
                if b - a > 0.1:
                    frente = rnd.uniform(0.115, 0.13)
                    giro = rot("Y", rnd.uniform(-0.5, 0.5)) @ rot("X", rnd.uniform(-0.4, 0.4))
                    sin = ("+y", "-z") if k == 0 else ("+y", "+z")
                    caja_plano(p.baja, pl, a + 0.014, b - 0.014, v0 + (0.012 if k else 0), v1 - 0.006, 0.05, frente,
                               "piedra", sin=sin, giro_extra=giro)
                u += largo
        perfil = [(0.035, 1.53), (0.18, 1.47), (0.18, 1.44), (0.165, 1.44), (0.165, 1.457), (0.035, 1.51)]
        ext = 0.12 if pl in (FRENTE, FONDO) else 0.0
        a, b = u0 - (ext if u0 < -MX else 0), u1 + (ext if u1 > MX else 0)
        p.baja.placa(perfil, pl.p(a, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, b - a, "metal_oscuro", atras=True)
    return p


def _panel(p, pl, u0, u1, v0, v1, mat, rnd, recortes=(), remaches=0.36):
    g = JUNTA / 2
    poly = rect(u0 + g, u1 - g, v0 + g, v1 - g)
    for a_, b_, c_ in recortes:
        poly = cp.recortar(poly, a_, b_, c_)
    if len(poly) < 3 or cp.area(poly) < 0.02:
        return
    grosor = PANEL + rnd.uniform(-0.002, 0.002)
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
                p.alta.cupula(pl.p(uu, vv, grosor), pl.n, 0.02, "acero", alto=0.01, lados=8)
    for t in range(1, nv):
        vv = va + (vb - va) * t / nv
        for uu in (ua, ub):
            if cp._dentro(poly, uu, vv):
                p.alta.cupula(pl.p(uu, vv, grosor), pl.n, 0.02, "acero", alto=0.01, lados=8)


def _celdas(cortes_u, cortes_v, huecos=()):
    """Rejilla de paneles: cada celda entre cortes, menos las que caen dentro de un hueco."""
    res = []
    for i in range(len(cortes_u) - 1):
        for j in range(len(cortes_v) - 1):
            u0, u1, v0, v1 = cortes_u[i], cortes_u[i + 1], cortes_v[j], cortes_v[j + 1]
            cu, cv = (u0 + u1) / 2, (v0 + v1) / 2
            if any(h[0] < cu < h[1] and h[2] < cv < h[3] for h in huecos):
                continue
            res.append((u0, u1, v0, v1))
    return res


def paredes():
    """Alma de los muros, paneles (más nuevos en la fachada), cantoneras, pretil y albardilla."""
    p = Pieza("casa_paredes", peso_uv=1.0)
    rnd = random.Random(5)
    b = p.baja
    E, T, VF, VL, PL = ESCAPARATE, PUERTA_T, VENT_F, VENT_L, PUERTA_L

    def alma(pl, ext, inte, huecos):
        b.cara_con_huecos([pl.p(u, v, 0) for u, v in ext], [[pl.p(u, v, 0) for u, v in h] for h in huecos],
                          "junta", pl.n, oculta=2)
        b.cara_con_huecos([pl.p(u, v, -MURO) for u, v in inte], [[pl.p(u, v, -MURO) for u, v in h] for h in huecos],
                          "interior", -pl.n, oculta=1)

    zt = z_muro(-MY)
    frente_ext = [(-MX, 1.45), (T["x0"], 1.45), (T["x0"], T["z1"]), (T["x1"], T["z1"]), (T["x1"], 1.45), (MX, 1.45),
                  (MX, PRETIL), (-MX, PRETIL)]
    frente_int = [(-MX + MURO, BASE_Z), (T["x0"], BASE_Z), (T["x0"], T["z1"]), (T["x1"], T["z1"]), (T["x1"], BASE_Z),
                  (MX - MURO, BASE_Z), (MX - MURO, zt), (-MX + MURO, zt)]
    huecos_f = [rect(E["x0"], E["x1"], E["z0"], E["z1"]), rect(VF["x0"], VF["x1"], VF["z0"], VF["z1"])]
    alma(FRENTE, frente_ext, frente_int, huecos_f)
    zb = z_muro(MY)
    alma(FONDO, rect(-MX, MX, 1.45, zb), rect(-MX + MURO, MX - MURO, BASE_Z, zb), [])

    def lateral(pl, signo):
        # u = +y (derecha) o u = -y (izquierda): la cubierta baja hacia +y.
        def top(u):
            return z_muro(signo * u)
        ext = [(-MY, 1.45), (MY, 1.45), (MY, top(MY)), (-MY, top(-MY))]
        inte = [(-MY + MURO, BASE_Z), (MY - MURO, BASE_Z), (MY - MURO, top(MY - MURO)), (-MY + MURO, top(-MY + MURO))]
        return ext, inte

    ext, inte = lateral(IZQ, -1)
    alma(IZQ, ext, inte, [rect(VL["u0"], VL["u1"], VL["v0"], VL["v1"])])
    ext, inte = lateral(DER, 1)
    ext = [(-MY, 1.45), (PL["u0"], 1.45), (PL["u0"], PL["v1"]), (PL["u1"], PL["v1"]), (PL["u1"], 1.45), (MY, 1.45),
           ext[2], ext[3]]
    inte = [inte[0], (PL["u0"], BASE_Z), (PL["u0"], PL["v1"]), (PL["u1"], PL["v1"]), (PL["u1"], BASE_Z)] + inte[1:]
    alma(DER, ext, inte, [])

    # ---- paneles ---------------------------------------------------------------------------------------------
    fach = "panel_fachada"
    # Planta baja de la fachada: tiras entre los marcos azules y franja de arriba (detrás del cartel).
    for u0, u1, v0, v1 in [(-MX, MARCO_E["x0"], 1.5, 3.55), (-MX, MARCO_E["x0"], 3.55, PB_TOP),
                           (MARCO_E["x1"], 2.0, 1.5, 3.55), (MARCO_E["x1"], 2.0, 3.55, PB_TOP),
                           (4.4, MX, 1.5, 3.55), (4.4, MX, 3.55, PB_TOP),
                           (-5.2, -3.0, MARCO_E["z1"], PB_TOP), (-3.0, -0.6, MARCO_E["z1"], PB_TOP),
                           (-0.6, 2.0, MARCO_E["z1"], PB_TOP), (2.0, 3.2, 4.85, PB_TOP), (3.2, 4.4, 4.85, PB_TOP)]:
        _panel(p, FRENTE, u0, u1, v0, v1, fach, rnd)
    for c in _celdas([-MX, -4.2, -3.0, -1.7, -0.4, 0.9, 2.2, 3.5, 4.5, MX], [MOLD[1], VF["z0"], VF["z1"], PRETIL],
                     [(VF["x0"], VF["x1"], VF["z0"], VF["z1"])]):
        _panel(p, FRENTE, *c, fach, rnd)
    lim = "panel_limpio"
    corte_b = [-MX, -4.1, -2.75, -1.4, 0.0, 1.4, 2.75, 4.1, MX]
    for c in _celdas(corte_b, [1.5, 3.55, PB_TOP]) + _celdas(corte_b, [MOLD[1], 7.2, 8.5]):
        _panel(p, FONDO, *c, lim, rnd, recortes=[(0, 1, zb)])
    # Laterales: la cubierta cae hacia atrás, así que el borde de arriba va inclinado.
    rec_i = [(-PEND_T, 1, z_muro(0))]   # izquierda: u = -y
    rec_d = [(PEND_T, 1, z_muro(0))]    # derecha: u = +y
    for c in _celdas([-MY, -2.7, -1.35, VL["u0"], VL["u1"], 2.4, MY], [1.5, 3.55, PB_TOP]):
        _panel(p, IZQ, *c, lim, rnd)
    for c in _celdas([-MY, -2.7, -1.35, VL["u0"], VL["u1"], 2.4, MY], [MOLD[1], VL["v0"], VL["v1"], 8.8],
                     [(VL["u0"], VL["u1"], VL["v0"], VL["v1"])]):
        _panel(p, IZQ, *c, lim, rnd, recortes=rec_i)
    hueco_l = (PL["u0"] - 0.2, PL["u1"] + 0.2, 0.0, PL["v1"] + 0.2)
    for c in _celdas([-MY, -2.8, -1.6, PL["u0"] - 0.2, PL["u1"] + 0.2, 2.9, MY], [1.5, 3.55, PL["v1"] + 0.2, PB_TOP],
                     [hueco_l]):
        _panel(p, DER, *c, lim, rnd)
    for c in _celdas([-MY, -2.7, -1.35, 0.0, 1.35, 2.7, MY], [MOLD[1], 7.3, 8.8]):
        _panel(p, DER, *c, lim, rnd, recortes=rec_d)

    # ---- pretil con albardilla (solo en la fachada) ---------------------------------------------------------
    caja_plano(b, FRENTE, -MX, MX, zt, PRETIL, -MURO, 0.0, "panel_limpio", sin=("-y", "+z", "-z"))
    caja_plano(b, FRENTE, -MX - 0.1, MX + 0.1, PRETIL, PRETIL + 0.07, -MURO - 0.06, PANEL + 0.08, "metal_oscuro")
    caja_plano(b, FRENTE, -MX - 0.1, MX + 0.1, PRETIL - 0.08, PRETIL, PANEL + 0.06, PANEL + 0.08, "metal_oscuro",
               sin=("+y", "+z"))
    for k in range(12):
        uu = -MX + 0.3 + k * (2 * MX - 0.6) / 11
        tornillo(p, FRENTE.p(uu, PRETIL - 0.04, PANEL + 0.08), FRENTE.n, 0.018, "acero", en_baja=False)

    # ---- cantoneras ---------------------------------------------------------------------------------------------
    for sx in (-1, 1):
        for sy in (-1, 1):
            z0 = 1.47
            z1 = PRETIL if sy < 0 else z_muro(sy * MY) + 0.02
            xa = sorted((sx * (MX - 0.15), sx * (MX + PANEL + 0.035)))
            ya = sorted((sy * (MY + PANEL), sy * (MY + PANEL + 0.03)))
            b.caja_de((xa[0], ya[0], z0), (xa[1], ya[1], z1), "metal_oscuro", sin=("+y" if sy < 0 else "-y",))
            xb = sorted((sx * (MX + PANEL), sx * (MX + PANEL + 0.03)))
            yb = sorted((sy * (MY - 0.15), sy * (MY + PANEL + 0.035)))
            b.caja_de((xb[0], yb[0], z0), (xb[1], yb[1], min(z1, z_muro(sy * MY) + 0.02)), "metal_oscuro",
                      sin=("+x" if sx < 0 else "-x",))
            for k in range(9):
                zz = z0 + 0.25 + k * (z1 - z0 - 0.5) / 8
                tornillo(p, (sx * (MX - 0.07), sy * (MY + PANEL + 0.03), zz), (0, sy, 0), 0.02, "acero", en_baja=False)
    return p


def moldura():
    """Moldura metálica del forjado: separa la tienda de la vivienda en las cuatro fachadas."""
    p = Pieza("moldura_forjado", peso_uv=1.1)
    perfil = [(0.035, MOLD[0]), (0.17, MOLD[0] + 0.02), (0.21, MOLD[0] + 0.07), (0.21, MOLD[1] - 0.07),
              (0.18, MOLD[1] - 0.02), (0.035, MOLD[1])]
    for pl, u0, u1 in ((FRENTE, -MX - 0.21, MX + 0.21), (FONDO, -MX - 0.21, MX + 0.21), (IZQ, -MY, MY),
                       (DER, -MY, MY)):
        p.baja.placa(perfil, pl.p(u0, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, u1 - u0, "metal_oscuro", atras=True)
        n = int((u1 - u0) / 0.45)
        for k in range(n + 1):
            uu = u0 + 0.15 + k * (u1 - u0 - 0.3) / n
            tornillo(p, pl.p(uu, (MOLD[0] + MOLD[1]) / 2, 0.21), pl.n, 0.022, "acero", en_baja=False)
    return p


def techo():
    """Cubierta plana con tela asfáltica, cayendo hacia atrás; remates metálicos y gárgola del bajante."""
    p = Pieza("casa_techo", peso_uv=0.8)
    b = p.baja
    x0, x1, y0, y1 = -MX - 0.15, MX + 0.15, -MY + MURO, MY + 0.15
    v = {}
    for i, x in enumerate((x0, x1)):
        for j, y in enumerate((y0, y1)):
            v[i, j, 1] = b.v((x, y, z_techo(y)))
            v[i, j, 0] = b.v((x, y, z_techo(y) - LOSA))
    b.cara([v[0, 0, 1], v[1, 0, 1], v[1, 1, 1], v[0, 1, 1]], "tela_asfaltica")
    b.cara([v[0, 0, 0], v[0, 1, 0], v[1, 1, 0], v[1, 0, 0]], "panel_limpio", oculta=True)
    b.cara([v[0, 1, 0], v[0, 1, 1], v[1, 1, 1], v[1, 1, 0]], "panel_limpio")
    b.cara([v[0, 0, 0], v[0, 0, 1], v[0, 1, 1], v[0, 1, 0]], "panel_limpio")
    b.cara([v[1, 0, 0], v[1, 1, 0], v[1, 1, 1], v[1, 0, 1]], "panel_limpio")
    ang = math.degrees(math.atan(PEND_T))
    # Remates (angulares) en los laterales y detrás.
    largo = (y1 - y0) / math.cos(math.radians(ang))
    for sx in (-1, 1):
        yc = (y0 + y1) / 2
        g = rot("X", -ang)
        b.caja((sx * (MX + 0.165), yc, z_techo(yc) - 0.1), (0.03, largo, 0.33), "metal_oscuro", giro=g)
        b.caja((sx * (MX + 0.08), yc, z_techo(yc) + 0.035), (0.2, largo, 0.025), "metal_oscuro", giro=g)
    b.caja_de((x0 - 0.03, y1, z_techo(y1) - LOSA - 0.08), (x1 + 0.03, y1 + 0.03, z_techo(y1) + 0.05), "metal_oscuro")
    b.caja_de((x0, y1 - 0.18, z_techo(y1)), (x1, y1, z_techo(y1) + 0.025), "metal_oscuro", sin=("-z",))
    # Gárgola: canalito que saca el agua por detrás hasta el embudo del bajante.
    b.caja_de((-4.98, y1 - 0.3, z_techo(y1) - 0.07), (-4.72, y1 + 0.28, z_techo(y1) + 0.02), "metal_oscuro",
              sin=("+z",))
    # Juntas soldadas de la tela asfáltica y algún parche (malla alta).
    for k in range(-5, 6):
        x = k * 0.95
        y = y0 + 0.1
        a = Vector((x, y, z_techo(y) + 0.004))
        bb = Vector((x, y1 - 0.2, z_techo(y1 - 0.2) + 0.004))
        p.alta.tubo([a, bb], 0.022, "tela_asfaltica", lados=4, tapa_ini=False, tapa_fin=False)
    for cx, cy, w, h in ((-1.8, 0.4, 0.9, 0.6), (3.6, -1.6, 0.6, 0.5)):
        p.alta.caja((cx, cy, z_techo(cy) + 0.006), (w, h, 0.012), "tela_asfaltica", giro=rot("X", -ang))
    p.extra["gargola"] = [-4.85, y1 + 0.28, z_techo(y1) - 0.05]
    return p


# ======================================================================================================
# Escaparate
# ======================================================================================================


def escaparate():
    pl = FRENTE
    E, M = ESCAPARATE, MARCO_E
    marco = Pieza("escaparate_marco", peso_uv=1.6)
    b = marco.baja
    dF = 0.2
    caja_plano(b, pl, M["x0"], E["x0"], M["z0"], M["z1"], PANEL, dF, "azul_tienda", sin=("+y", "-z"))
    caja_plano(b, pl, E["x1"], M["x1"], M["z0"], M["z1"], PANEL, dF, "azul_tienda", sin=("+y", "-z"))
    caja_plano(b, pl, E["x0"], E["x1"], E["z1"], M["z1"], PANEL, dF, "azul_tienda", sin=("+y", "-x", "+x"))
    caja_plano(b, pl, E["x0"], E["x1"], M["z0"], E["z0"], PANEL, dF, "azul_tienda", sin=("+y", "-x", "+x", "-z"))
    # Forro del hueco (la otra pata de la L) y junquillos.
    t = 0.04
    caja_plano(b, pl, E["x0"], E["x0"] + t, E["z0"], E["z1"], -MURO, PANEL, "azul_tienda", sin=("-x",))
    caja_plano(b, pl, E["x1"] - t, E["x1"], E["z0"], E["z1"], -MURO, PANEL, "azul_tienda", sin=("+x",))
    caja_plano(b, pl, E["x0"] + t, E["x1"] - t, E["z1"] - t, E["z1"], -MURO, PANEL, "azul_tienda",
               sin=("+z", "-x", "+x"))
    caja_plano(b, pl, E["x0"] + t, E["x1"] - t, E["z0"], E["z0"] + t, -MURO, PANEL, "azul_tienda",
               sin=("-z", "-x", "+x"))
    j = 0.045
    for (u0, u1, v0, v1) in ((E["x0"] + t, E["x0"] + t + j, E["z0"] + t, E["z1"] - t),
                             (E["x1"] - t - j, E["x1"] - t, E["z0"] + t, E["z1"] - t),
                             (E["x0"] + t + j, E["x1"] - t - j, E["z1"] - t - j, E["z1"] - t),
                             (E["x0"] + t + j, E["x1"] - t - j, E["z0"] + t, E["z0"] + t + j)):
        caja_plano(b, pl, u0, u1, v0, v1, -0.07, -0.02, "azul_tienda", sin=("+y",))
    # Dos maineles que parten el cristal en tres.
    for um in MAINELES:
        caja_plano(b, pl, um - 0.06, um + 0.06, E["z0"] + t, E["z1"] - t, -0.16, dF - 0.02, "azul_tienda")
    # Tornillos del marco (malla alta).
    for uu in (M["x0"] + 0.15, M["x1"] - 0.15):
        for k in range(6):
            tornillo(marco, pl.p(uu, M["z0"] + 0.2 + k * 0.55, dF), pl.n, 0.022, "acero", en_baja=False)
    for k in range(12):
        tornillo(marco, pl.p(E["x0"] + 0.2 + k * 0.54, M["z1"] - 0.15, dF), pl.n, 0.022, "acero", en_baja=False)

    cristal = Pieza("escaparate_cristal", peso_uv=0.5)
    bordes = [E["x0"] + t, MAINELES[0] - 0.06, MAINELES[0] + 0.06, MAINELES[1] - 0.06, MAINELES[1] + 0.06,
              E["x1"] - t]
    for k in range(3):
        caja_plano(cristal.baja, pl, bordes[2 * k], bordes[2 * k + 1], E["z0"] + t, E["z1"] - t, -0.12, -0.07,
                   "vidrio_limpio")

    expo = Pieza("escaparate_expositor", peso_uv=1.8)
    _expositor(expo)
    busca = Pieza("cartel_repartidor", peso_uv=3.0)
    _cartel_repartidor(busca)
    interior = Pieza("tienda_interior", peso_uv=0.5)
    _interior(interior)
    return [marco, cristal, expo, busca, interior]


def _expositor(p):
    """Tarima de madera detrás del cristal, panel perforado al fondo, estante y lo que está a la venta."""
    b, a = p.baja, p.alta
    E = ESCAPARATE
    yf, yb = -3.66, -2.9
    ztop = 1.82
    b.caja_de((E["x0"] + 0.05, yf, BASE_Z), (E["x1"] - 0.05, yb, ztop), "madera_puerta", sin=("-z", "-x", "+x"))
    b.caja_de((E["x0"] + 0.02, yb, BASE_Z), (E["x1"] - 0.02, yb + 0.05, 4.6), "pintura_gris", sin=("+y", "-z"))
    # Agujeros del panel perforado (malla alta).
    for i in range(30):
        for k in range(12):
            x = E["x0"] + 0.25 + i * 0.205
            z = 2.0 + k * 0.2
            if x < E["x1"] - 0.15:
                a.cilindro((x, yb - 0.001, z), (0, -1, 0), 0.018, 0.002, "negro_mate", lados=6, tapa_ini=False)
    # Estante con ménsulas y tres latas.
    b.caja_de((-4.6, -3.25, 3.15), (-1.3, yb, 3.21), "madera_oscura", sin=("+y",))
    for x in (-4.3, -1.6):
        b.placa([(0.0, 0.0), (0.0, -0.28), (0.04, -0.28), (0.3, -0.02), (0.3, 0.0)], Vector((x - 0.015, yb, 3.15)),
                Vector((0, -1, 0)), Vector((0, 0, 1)), Vector((1, 0, 0)), 0.03, "metal_oscuro", atras=True)
    for k, (x, mat) in enumerate(((-4.1, "pintura_roja"), (-3.75, "pintura_naranja"), (-3.4, "pintura_roja"))):
        b.revolucion([(0.095, 0), (0.1, 0.02), (0.1, 0.22), (0.095, 0.24), (0.07, 0.245)], (x, -3.08, 3.21), 8, mat,
                     tapa_ini=False, tapa_fin=True)
    # Rollo de cable colgado de un gancho.
    centro = Vector((0.6, -2.98, 3.3))
    anillo = [centro + Vector((math.cos(t) * 0.24, 0, math.sin(t) * 0.24)) for t in
              [math.tau * i / 10 for i in range(11)]]
    b.tubo(anillo, 0.045, "goma", lados=5, tapa_ini=False, tapa_fin=False)
    b.tubo([(0.6, yb, 3.62), (0.6, -3.0, 3.6), (0.6, -3.03, 3.52)], 0.012, "acero", lados=4, radio_curva=0.03)
    for k in range(5):  # vueltas del rollo (malla alta)
        r = 0.2 + k * 0.02
        an = [centro + Vector((math.cos(t) * r, -0.03 + k * 0.012, math.sin(t) * r)) for t in
              [math.tau * i / 16 for i in range(17)]]
        a.tubo(an, 0.02, "goma", lados=5, tapa_ini=False, tapa_fin=False)

    # Llave inglesa grande sobre un atril inclinado.
    atril = Vector((-3.85, -3.3, ztop))
    b.placa([(0.0, 0.0), (0.42, 0.0), (0.0, 0.3)], atril + Vector((-0.06, 0.2, 0)), Vector((0, -1, 0)),
            Vector((0, 0, 1)), Vector((1, 0, 0)), 0.12, "madera_oscura", atras=True)
    _llave_inglesa(b, a, Vector((-3.85, -3.38, ztop + 0.16)))
    # Pieza de motor: cilindro con aletas de refrigeración sobre su brida, con etiqueta de precio.
    c = Vector((-1.75, -3.25, ztop))
    b.revolucion([(0.34, 0), (0.34, 0.05), (0.2, 0.05)], c, 10, "aluminio", tapa_ini=False, tapa_fin=False)
    b.revolucion([(0.17, 0.05), (0.17, 0.72), (0.12, 0.76), (0.06, 0.76)], c, 10, "hierro", tapa_ini=False,
                 tapa_fin=True)
    for k in range(6):
        z = 0.14 + k * 0.1
        b.revolucion([(0.17, z), (0.3, z + 0.004), (0.3, z + 0.026), (0.17, z + 0.03)], c, 10, "aluminio",
                     tapa_ini=False, tapa_fin=False)
    b.cilindro(c + Vector((0, 0, 0.76)), (0, 0, 1), 0.045, 0.12, "acero", lados=6)
    for k in range(6):
        ang = math.tau * k / 6
        a.cupula(c + Vector((math.cos(ang) * 0.28, math.sin(ang) * 0.28, 0.05)), (0, 0, 1), 0.022, "acero",
                 alto=0.02, lados=6)
    _tarjeta_precio(p, c + Vector((0.35, -0.25, 0)), "45 c")
    # Cajas apiladas con etiqueta.
    x = 0.55
    b.caja_de((x - 0.3, -3.5, ztop), (x + 0.3, -3.0, ztop + 0.38), "carton", sin=("-z",))
    g = rot("Z", 12)
    b.caja(Vector((x + 0.03, -3.27, ztop + 0.38 + 0.15)), (0.46, 0.38, 0.3), "carton", giro=g, sin=("-z",))
    for (cx, cz, w, h) in ((x, ztop + 0.2, 0.36, 0.2),):
        b.caja_de((cx - w / 2, -3.505, cz - h / 2), (cx + w / 2, -3.5, cz + h / 2), "papel")
        texto(a, "JUNTAS", Vector((cx, -3.506, cz + 0.04)), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.06, 0.001,
              "tinta", ancho_max=0.3)
        texto(a, "TÓRICAS x50", Vector((cx, -3.506, cz - 0.05)), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.035, 0.001,
              "tinta", ancho_max=0.3)
    # Cinta de embalar (malla alta).
    a.caja(Vector((x, -3.25, ztop + 0.381)), (0.08, 0.5, 0.003), "pegatina")
    a.caja(Vector((x + 0.03, -3.27, ztop + 0.681)), (0.07, 0.38, 0.003), "pegatina", giro=g)


def _llave_inglesa(b, a, base):
    """Llave inglesa de verdad: mango con agujero, cabeza con la boca abierta y el tornillo sin fin."""
    u = Vector((1, 0, 0))
    v = (Vector((0, 0.55, 1))).normalized()
    n = u.cross(v).normalized() * -1 if u.cross(v).y > 0 else u.cross(v).normalized()
    mango = [(-0.42, -0.035), (0.05, -0.05), (0.05, 0.05), (-0.42, 0.035), (-0.45, 0.0)]
    cabeza = [(0.03, -0.075), (0.2, -0.085), (0.26, -0.04), (0.26, 0.11), (0.21, 0.15), (0.17, 0.15), (0.17, 0.05),
              (0.12, 0.05), (0.12, 0.13), (0.06, 0.13), (0.03, 0.07)]
    for poly in (mango, cabeza):
        b.placa(poly, base, u, v, n, 0.045, "acero", atras=True)
    b.cilindro(base + u * 0.15 + v * -0.035 + n * 0.0225 - u * 0.05, u, 0.028, 0.1, "acero", lados=8)
    a.cilindro(base + u * -0.38 + n * 0.046, n, 0.02, 0.002, "negro_mate", lados=10, tapa_ini=False)
    for k in range(6):  # rosca del sin fin
        a.revolucion([(0.03, 0), (0.031, 0.006), (0.03, 0.012)], base + u * (0.1 + k * 0.015) + v * -0.035 +
                     n * 0.0225, 8, "acero", eje=u, tapa_ini=False, tapa_fin=False)


def _tarjeta_precio(p, pos, precio):
    """Tarjeta de precio doblada en V (dos planos con grosor) y el precio escrito (malla alta)."""
    b = p.baja
    for s in (-1, 1):
        g = rot("X", s * 25)
        b.caja(pos + Vector((0, s * 0.03, 0.06)), (0.2, 0.004, 0.13), "papel", giro=g)
    texto(p.alta, precio, pos + Vector((0, -0.062, 0.065)), (1, 0, 0), Vector((0, -0.42, 0.9)).normalized(),
          Vector((0, -0.9, -0.42)).normalized(), 0.05, 0.001, "tinta", ancho_max=0.16)


def _cartel_repartidor(p):
    """«Se busca repartidor»: papel pegado por dentro del cristal, algo torcido, con celo en las esquinas."""
    E = ESCAPARATE
    yc = -3.868
    g = rot("Y", -6)
    centro = Vector((E["x1"] - 0.55, yc, 2.55))
    p.baja.caja(centro, (0.48, 0.006, 0.62), "papel", giro=g)
    a = p.alta
    gm = g.to_4x4()
    u = g @ Vector((1, 0, 0))
    v = g @ Vector((0, 0, 1))
    n = Vector((0, -1, 0))
    o = centro + n * 0.003
    texto(a, "SE BUSCA", o + v * 0.2, u, v, n, 0.075, 0.001, "tinta", ancho_max=0.4)
    texto(a, "REPARTIDOR", o + v * 0.08, u, v, n, 0.055, 0.001, "tinta_roja", ancho_max=0.42)
    texto(a, "con carro propio", o + v * -0.04, u, v, n, 0.03, 0.001, "tinta", ancho_max=0.38)
    texto(a, "pregunte dentro", o + v * -0.12, u, v, n, 0.03, 0.001, "tinta", ancho_max=0.38)
    for k in range(5):  # tiras para arrancar con el número
        a.caja(o + v * -0.25 + u * (-0.18 + k * 0.09), (0.004, 0.002, 0.1), "tinta", giro=g)
    for su, sv in ((-1, 1), (1, 1), (-1, -1), (1, -1)):
        a.caja(o + u * su * 0.22 + v * sv * 0.29 + n * 0.0005, (0.09, 0.001, 0.035), "vidrio_limpio",
               giro=g @ rot("Y", 40 * su * sv))


def _interior(p):
    """Lo que se ve de la tienda por la puerta: techo, mostrador y caja registradora."""
    b = p.baja
    b.caja_de((-MX + MURO, -MY + MURO, PB_TOP - 0.05), (MX - MURO, MY - MURO, PB_TOP), "interior",
              sin=("+z", "-x", "+x", "-y", "+y"))
    b.caja_de((1.9, -1.45, BASE_Z), (4.7, -0.85, 2.05), "madera_puerta", sin=("-z", "+y"))
    b.caja_de((1.85, -1.52, 2.05), (4.75, -0.8, 2.12), "madera_oscura")
    b.caja_de((3.6, -1.35, 2.12), (4.2, -0.95, 2.35), "pintura_gris", sin=("-z",))
    b.caja(Vector((3.9, -1.0, 2.5)), (0.5, 0.06, 0.3), "negro_mate", giro=rot("X", -20))


# ======================================================================================================
# Toldo
# ======================================================================================================


def toldo():
    pl = FRENTE
    u0, u1 = -5.15, 1.75
    caja = Pieza("toldo_caja", peso_uv=1.2)
    perfil = [(0.06, 4.67), (0.3, 4.67), (0.345, 4.71), (0.345, 4.89), (0.3, 4.935), (0.06, 4.935)]
    caja.baja.placa(perfil, pl.p(u0, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, u1 - u0, "aluminio", atras=True)
    for uu in (u0 + 0.35, (u0 + u1) / 2, u1 - 0.35):
        caja_plano(caja.baja, pl, uu - 0.1, uu + 0.1, 4.62, 4.98, PANEL, 0.09, "metal_oscuro", sin=("+y",))
        for vv in (4.68, 4.92):
            tornillo(caja, pl.p(uu, vv, 0.09), pl.n, 0.018, "acero", en_baja=False)

    # Tela: de la ranura de la caja a la barra de delante, con algo de comba; faldón ondulado.
    tela = Pieza("toldo_tela", peso_uv=1.7)
    d0, v0 = 0.3, 4.68
    d1, v1 = 1.62, 3.98
    secc = []
    for k in range(4):
        f = k / 3
        d = d0 + (d1 - d0) * f
        v = v0 + (v1 - v0) * f - 0.05 * math.sin(math.pi * f)
        secc.append((d, v))
    grosor = 0.015
    perfil = secc + [(d, v - grosor) for d, v in reversed(secc)]
    tela.baja.placa(perfil, pl.p(u0 + 0.12, 0, 0), pl.n, Vector((0, 0, 1)), pl.u, u1 - u0 - 0.24, "toldo",
                    atras=True)
    faldon = []
    n_ond = 11
    ancho = u1 - u0 - 0.24
    for k in range(n_ond):
        ua = u0 + 0.12 + ancho * k / n_ond
        ub = u0 + 0.12 + ancho * (k + 1) / n_ond
        for t in range(4):
            f = t / 4
            uu = ua + (ub - ua) * f
            faldon.append((uu, v1 - 0.3 - 0.07 * math.sin(math.pi * f)))
    faldon.append((u1 - 0.12, v1 - 0.3))
    # Faldón como tira de secciones (sin polígonos cóncavos grandes, que se triangulan mal).
    dd = d1 + 0.04
    secciones = [[pl.p(uu, v1 - 0.01, dd), pl.p(uu, vb, dd), pl.p(uu, vb, dd + 0.012), pl.p(uu, v1 - 0.01, dd + 0.012)]
                 for uu, vb in faldon]
    tela.baja.loft(secciones, "toldo", suave=False)
    tela.baja.recalcular(tela.baja.ultimas)

    # Estructura: barra de delante y dos brazos articulados (hombro, codo, muñeca).
    brazos = Pieza("toldo_brazos", peso_uv=1.5)
    bb = brazos.baja
    caja_plano(bb, pl, u0 + 0.05, u1 - 0.05, v1 - 0.06, v1 + 0.04, d1 - 0.04, d1 + 0.05, "aluminio")
    for uu in (u0 + 0.02, u1 - 0.02):
        caja_plano(bb, pl, uu - 0.03, uu + 0.03, v1 - 0.07, v1 + 0.05, d1 - 0.05, d1 + 0.06, "negro_mate")
    for ua, lado in ((-4.3, 1), (0.9, -1)):
        S = pl.p(ua, 4.1, 0.14)
        F = pl.p(ua + lado * 0.15, v1 - 0.06, d1 - 0.08)
        E_ = (S + F) / 2 + pl.u * lado * 0.42 + Vector((0, 0, -0.08))
        caja_plano(bb, pl, ua - 0.1, ua + 0.1, 3.95, 4.27, PANEL, 0.1, "metal_oscuro", sin=("+y",))
        for vv in (4.0, 4.22):
            tornillo(brazos, pl.p(ua, vv, 0.1), pl.n, 0.018, "acero")
        bb.tubo([S, E_], 0.035, "aluminio", lados=4, tapa_ini=False, tapa_fin=False)
        bb.tubo([E_, F], 0.03, "aluminio", lados=4, tapa_ini=False, tapa_fin=False)
        for P_, r in ((S, 0.05), (E_, 0.055), (F, 0.045)):
            bb.cilindro(P_ - Vector((0, 0, 0.05)), (0, 0, 1), r, 0.1, "metal_oscuro", lados=8)
            brazos.alta.cupula(P_ + Vector((0, 0, 0.05)), (0, 0, 1), r * 0.5, "acero", alto=0.01, lados=8)
        # Muelle del brazo (malla alta).
        hel = []
        eje = (E_ - S)
        uu_, _ = base_de(eje)
        ww = eje.normalized().cross(uu_)
        for k in range(60):
            f = 0.15 + 0.5 * k / 59
            ang = k * 1.2
            hel.append(S + eje * f + (uu_ * math.cos(ang) + ww * math.sin(ang)) * 0.042)
        brazos.alta.tubo(hel, 0.006, "acero", lados=4, tapa_ini=False, tapa_fin=False)
    return [caja, tela, brazos]


# ======================================================================================================
# Puerta de la tienda
# ======================================================================================================


def puerta_tienda():
    h, e = HOJA_T, EJE_T
    pu = Pieza("puerta_tienda", pivote=(e.x, e.y, h["z0"]), peso_uv=1.9)
    b, a = pu.baja, pu.alta
    y0, y1 = h["y0"], h["y1"]
    st = 0.16
    gx0, gx1, gz0, gz1 = h["x0"] + st, h["x1"] - st, 1.1, h["z1"] - st
    b.caja_de((h["x0"], y0, h["z0"]), (gx0, y1, h["z1"]), "azul_tienda", sin=("-z",))
    b.caja_de((gx1, y0, h["z0"]), (h["x1"], y1, h["z1"]), "azul_tienda", sin=("-z",))
    b.caja_de((gx0, y0, gz1), (gx1, y1, h["z1"]), "azul_tienda", sin=("-x", "+x"))
    b.caja_de((gx0, y0, h["z0"]), (gx1, y1, gz0), "azul_tienda", sin=("-x", "+x", "-z"))
    # Junquillos por los dos lados del cristal.
    for yy0, yy1 in ((y0 + 0.0, y0 + 0.035), (y1 - 0.035, y1)):
        j = 0.04
        b.caja_de((gx0, yy0, gz0), (gx0 + j, yy1, gz1), "azul_tienda", sin=("-x", "-z", "+z"))
        b.caja_de((gx1 - j, yy0, gz0), (gx1, yy1, gz1), "azul_tienda", sin=("+x", "-z", "+z"))
        b.caja_de((gx0 + j, yy0, gz1 - j), (gx1 - j, yy1, gz1), "azul_tienda", sin=("-x", "+x", "+z"))
        b.caja_de((gx0 + j, yy0, gz0), (gx1 - j, yy1, gz0 + j), "azul_tienda", sin=("-x", "+x", "-z"))
    # Chapa de patada (gastada de empujar con el pie).
    b.caja_de((h["x0"] + 0.04, y0 - 0.008, h["z0"] + 0.04), (h["x1"] - 0.04, y0, gz0 - 0.06), "acero", sin=("+y",))
    for x in (h["x0"] + 0.1, h["x1"] - 0.1):
        for z in (h["z0"] + 0.1, gz0 - 0.12):
            tornillo(pu, (x, y0 - 0.008, z), (0, -1, 0), 0.016, "acero", en_baja=False)
    # «ABIERTO»: letras por dentro del cristal, que se leen desde la calle.
    yv = (y0 + y1) / 2 + 0.025
    texto(b, "ABIERTO", Vector(((gx0 + gx1) / 2, yv + 0.006, 3.3)), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.19, 0.006,
          "rotulo", ancho_max=1.2)
    texto(a, "horario 8 - 20", Vector(((gx0 + gx1) / 2, yv + 0.006, 3.05)), (1, 0, 0), (0, 0, 1), (0, -1, 0),
          0.05, 0.004, "rotulo", ancho_max=0.7)
    # Tirador largo horizontal (por fuera y por dentro) con sus soportes.
    t = TIRADOR
    for lado in (-1, 1):
        yb = y0 if lado < 0 else y1
        ye = yb + lado * 0.1
        for x in (t.x - 0.28, t.x + 0.28):
            b.cilindro((x, yb, t.z), (0, lado, 0), 0.034, 0.012, "acero_pulido", lados=8, tapa_ini=False)
            b.cilindro((x, yb + lado * 0.012, t.z), (0, lado, 0), 0.02, 0.09, "acero_pulido", lados=6,
                       tapa_ini=False, tapa_fin=False)
        b.revolucion([(0.0, -0.33), (0.022, -0.322), (0.026, -0.3), (0.026, 0.3), (0.022, 0.322), (0.0, 0.33)],
                     (t.x, ye, t.z), 8, "acero_pulido", eje=(1, 0, 0))
    # Bisagras de muelle (vaivén): tambor con el muelle, collarines y palas.
    for zc in (1.17, 3.98):
        b.revolucion([(0.04, -0.24), (0.052, -0.22), (0.052, -0.17), (0.062, -0.15), (0.062, 0.15), (0.052, 0.17),
                      (0.052, 0.22), (0.04, 0.24)], (e.x, e.y, zc), 10, "acero", tapa_ini=True, tapa_fin=True)
        b.caja_de((e.x, y0 + 0.02, zc - 0.13), (h["x0"] + 0.13, y1 - 0.02, zc + 0.13), "acero", sin=("+x",))
        for k in range(4):  # agujeros de regulación del muelle (malla alta)
            ang = math.tau * k / 4
            dirv = Vector((math.cos(ang), math.sin(ang), 0))
            a.cilindro(Vector((e.x, e.y, zc - 0.19)) + dirv * 0.052, dirv, 0.009, 0.003, "negro_mate", lados=6)
            a.cilindro(Vector((e.x, e.y, zc + 0.19)) + dirv * 0.052, dirv, 0.009, 0.003, "negro_mate", lados=6)
        for z in (zc - 0.08, zc + 0.08):
            tornillo(pu, (h["x0"] + 0.08, y0, z), (0, -1, 0), 0.014, "acero", en_baja=False)

    cr = Pieza("puerta_tienda_cristal", pivote=(e.x, e.y, h["z0"]), peso_uv=0.5)
    cr.baja.caja_de((gx0 + 0.01, (y0 + y1) / 2 - 0.025, gz0 + 0.01), (gx1 - 0.01, (y0 + y1) / 2 + 0.025, gz1 - 0.01),
                    "vidrio_limpio")

    marco = Pieza("puerta_tienda_marco", peso_uv=1.4)
    _marco_puerta(marco, FRENTE, PUERTA_T["x0"], PUERTA_T["x1"], PUERTA_T["z1"], "azul_tienda", ancho=0.25)
    # Campanilla: fleje curvo desde el dintel por dentro, campana de latón y badajo.
    mb = marco.baja
    cx, cy = 3.65, -3.6
    mb.caja_de((cx - 0.06, -MY + MURO - 0.02, PUERTA_T["z1"] - 0.12), (cx + 0.06, -MY + MURO, PUERTA_T["z1"] - 0.02),
               "laton")
    mb.tubo([(cx, -MY + MURO - 0.02, PUERTA_T["z1"] - 0.07), (cx, cy + 0.05, PUERTA_T["z1"] - 0.07),
             (cx, cy, PUERTA_T["z1"] - 0.17)], 0.012, "laton", lados=4, radio_curva=0.06, pasos_curva=3)
    tope = Vector((cx, cy, PUERTA_T["z1"] - 0.17))
    mb.revolucion(list(reversed([(0.012, 0), (0.04, -0.015), (0.052, -0.06), (0.074, -0.13), (0.084, -0.155),
                                 (0.074, -0.155), (0.064, -0.13), (0.042, -0.065), (0.026, -0.03), (0.0, -0.03)])),
                  tope, 10, "laton", tapa_ini=False, tapa_fin=True)
    mb.tubo([tope + Vector((0, 0, -0.03)), tope + Vector((0, 0, -0.13))], 0.004, "acero", lados=4)
    mb.revolucion([(0.0, -0.16), (0.016, -0.15), (0.016, -0.13), (0.0, -0.12)], tope, 6, "laton")
    marco.extra["campanilla"] = list(tope)

    felpudo = Pieza("felpudo_rejilla", peso_uv=1.4)
    fb = felpudo.baja
    x0, x1, yy0, yy1 = 2.4, 4.0, -5.0, -4.2
    w = 0.05
    for (xa, ya, xb, yb2) in ((x0, yy0, x1, yy0 + w), (x0, yy1 - w, x1, yy1), (x0, yy0 + w, x0 + w, yy1 - w),
                              (x1 - w, yy0 + w, x1, yy1 - w)):
        fb.caja_de((xa, ya, BASE_Z), (xb, yb2, BASE_Z + 0.05), "hierro", sin=("-z",))
    for k in range(1, 10):
        y = yy0 + w + (yy1 - yy0 - 2 * w) * k / 10
        fb.caja_de((x0 + w, y - 0.016, BASE_Z), (x1 - w, y + 0.016, BASE_Z + 0.045), "hierro", sin=("-z", "-x", "+x"))
    for k in range(1, 6):
        x = x0 + w + (x1 - x0 - 2 * w) * k / 6
        felpudo.alta.caja_de((x - 0.008, yy0 + w, BASE_Z), (x + 0.008, yy1 - w, BASE_Z + 0.03), "hierro")
    return [pu, cr, marco, felpudo]


def _marco_puerta(p, pl, u0, u1, v1, mat, ancho=0.2, d_frente=0.2):
    """Marco de puerta en L: jambas y dintel en la fachada, forro del hueco y umbral metálico."""
    b = p.baja
    caja_plano(b, pl, u0 - ancho, u0, BASE_Z, v1 + ancho, PANEL, d_frente, mat, sin=("+y", "-z"))
    caja_plano(b, pl, u1, u1 + ancho, BASE_Z, v1 + ancho, PANEL, d_frente, mat, sin=("+y", "-z"))
    caja_plano(b, pl, u0, u1, v1, v1 + ancho, PANEL, d_frente, mat, sin=("+y", "-x", "+x"))
    caja_plano(b, pl, u0, u0 + 0.04, BASE_Z + 0.08, v1, -MURO, PANEL, mat, sin=("-x", "-z"))
    caja_plano(b, pl, u1 - 0.04, u1, BASE_Z + 0.08, v1, -MURO, PANEL, mat, sin=("+x", "-z"))
    caja_plano(b, pl, u0 + 0.04, u1 - 0.04, v1 - 0.04, v1, -MURO, PANEL, mat, sin=("+z", "-x", "+x"))
    caja_plano(b, pl, u0, u1, BASE_Z, BASE_Z + 0.08, -MURO, d_frente, "acero", sin=("-z",))
    for k in range(10):
        dd = -MURO + 0.03 + k * (MURO + d_frente - 0.06) / 9
        caja_plano(p.alta, pl, u0 + 0.06, u1 - 0.06, BASE_Z + 0.08, BASE_Z + 0.086, dd - 0.005, dd + 0.005, "acero")
    for uu in (u0 - ancho / 2, u1 + ancho / 2):
        for k in range(5):
            tornillo(p, pl.p(uu, 0.9 + k * (v1 - 1.1) / 4, d_frente), pl.n, 0.02, "acero", en_baja=False)


def pizarra():
    """Pizarra de precios colgada junto a la puerta de la tienda, con marcas de tiza."""
    p = Pieza("pizarra", peso_uv=3.2)
    pl = FRENTE
    b, a = p.baja, p.alta
    u0, u1, v0, v1 = 4.58, 5.32, 2.0, 3.12
    # Soporte: escuadra en la pared con un gancho.
    uc = (u0 + u1) / 2
    caja_plano(b, pl, uc - 0.08, uc + 0.08, 3.35, 3.6, PANEL, 0.09, "metal_oscuro", sin=("+y",))
    b.tubo([pl.p(uc, 3.45, 0.08), pl.p(uc, 3.45, 0.3), pl.p(uc, 3.36, 0.32)], 0.016, "metal_oscuro", lados=6,
           radio_curva=0.05)
    tornillo(p, pl.p(uc, 3.55, 0.09), pl.n, 0.016, "acero")
    tornillo(p, pl.p(uc, 3.4, 0.09), pl.n, 0.016, "acero")
    # Tablero inclinado: arriba casi tocando el gancho, abajo apoyado en la pared.
    g = rot("X", -7)
    centro = pl.p(uc, (v0 + v1) / 2, 0.18)
    M = pl.giro @ g

    def caja_local(cu, cv, cd, tu, tv, td, mat, **kw):
        b.caja(centro + M @ Vector((cu, -cd, cv)), (tu, td, tv), mat, giro=M, **kw)

    w, h = u1 - u0, v1 - v0
    m = 0.06
    caja_local(0, 0, 0.0, w - 2 * m, h - 2 * m, 0.03, "pizarra")
    caja_local(-w / 2 + m / 2, 0, 0.01, m, h, 0.05, "madera_oscura")
    caja_local(w / 2 - m / 2, 0, 0.01, m, h, 0.05, "madera_oscura")
    caja_local(0, h / 2 - m / 2, 0.01, w - 2 * m, m, 0.05, "madera_oscura", sin=("-x", "+x"))
    caja_local(0, -h / 2 + m / 2, 0.01, w - 2 * m, m, 0.05, "madera_oscura", sin=("-x", "+x"))
    # Cadenitas (malla alta) y tiza.
    for su in (-1, 1):
        top = centro + M @ Vector((su * (w / 2 - 0.08), 0.0, h / 2))
        a.tubo([pl.p(uc, 3.38, 0.32), top], 0.008, "acero", lados=4)
    o = centro + M @ Vector((0, -0.016, 0))
    uu = M @ Vector((1, 0, 0))
    vv = M @ Vector((0, 0, 1))
    nn = M @ Vector((0, -1, 0))
    lineas = [("HOY", 0.4, 0.11), ("Junta tórica  2c", 0.22, 0.05), ("Tubo 3m  6c", 0.11, 0.05),
              ("Pila larga  15c", 0.0, 0.05), ("Filtro aire  9c", -0.11, 0.05), ("¡HAY CAFÉ!", -0.32, 0.07)]
    for txt, dv, alto in lineas:
        texto(a, txt, o + vv * dv, uu, vv, nn, alto, 0.002, "tiza", ancho_max=w - 0.18)
    a.caja(o + vv * 0.3, (0.38, 0.002, 0.008), "tiza", giro=M)  # subrayado de «HOY»
    return p


# ======================================================================================================
# Puerta lateral (vivienda)
# ======================================================================================================


def puerta_lateral():
    pl = DER
    L = PUERTA_L
    piv = pl.p(L["u1"] + 0.05, L["v0"] + 0.08, 0.1)
    pu = Pieza("puerta_lateral", pivote=piv, peso_uv=1.8)
    b, a = pu.baja, pu.alta
    u0, u1, v0, v1 = L["u0"] + 0.05, L["u1"] - 0.05, L["v0"] + 0.08, L["v1"] - 0.05
    d0, d1 = -0.08, 0.05
    caja_plano(b, pl, u0, u1, v0, v1, d0, d1, "metal_lateral", sin=("-z",))
    # Cuarterones estampados (dos rectángulos en relieve) y chapa de patada.
    for vv0, vv1 in ((v0 + 0.45, 2.3), (2.7, v1 - 0.25)):
        caja_plano(b, pl, u0 + 0.2, u1 - 0.2, vv0, vv1, d1, d1 + 0.014, "metal_lateral", sin=("+y",))
    caja_plano(b, pl, u0 + 0.03, u1 - 0.03, v0 + 0.03, v0 + 0.36, d1, d1 + 0.006, "acero", sin=("+y",))
    for uu in (u0 + 0.08, u1 - 0.08):
        for vv in (v0 + 0.08, v0 + 0.31):
            tornillo(pu, pl.p(uu, vv, d1 + 0.006), pl.n, 0.015, "acero", en_baja=False)
    # Manija de palanca con roseta, cerradura y mirilla.
    hu, hv = u0 + 0.2, 2.55
    caja_plano(b, pl, hu - 0.07, hu + 0.07, hv - 0.42, hv + 0.12, d1, d1 + 0.025, "acero", sin=("+y",))
    for du in (-0.04, 0.04):
        for dv in (-0.38, 0.08):
            tornillo(pu, pl.p(hu + du, hv + dv, d1 + 0.025), pl.n, 0.016, "acero")
    b.cilindro(pl.p(hu, hv, d1 + 0.025), pl.n, 0.05, 0.04, "acero_pulido", lados=10, tapa_ini=False)
    b.tubo([pl.p(hu, hv, d1 + 0.05), pl.p(hu, hv, d1 + 0.13), pl.p(hu + 0.28, hv - 0.01, d1 + 0.15)], 0.028,
           "acero_pulido", lados=8, radio_curva=0.05, pasos_curva=3, tapa_ini=False)
    cp._cerradura(b, pl.p(hu, hv - 0.24, d1 + 0.025), u=pl.u, v=pl.v, n=pl.n, mat="acero")
    b.revolucion([(0.03, 0), (0.03, 0.015), (0.02, 0.02), (0.0, 0.02)], pl.p((u0 + u1) / 2, 3.9, d1), 8,
                 "laton", eje=pl.n, tapa_ini=False)
    # Bisagras: nudillo central en la hoja (los de arriba y abajo van en el marco).
    for vh in (1.1, 3.95):
        caja_plano(b, pl, u1 - 0.35, u1 + 0.02, vh - 0.09, vh + 0.09, d1, d1 + 0.02,
                   "hierro", sin=("+y",))
        b.cilindro((piv.x, piv.y, vh - 0.06), (0, 0, 1), 0.05, 0.12, "hierro", lados=8)
        for uu in (u1 - 0.28, u1 - 0.1):
            tornillo(pu, pl.p(uu, vh, d1 + 0.02), pl.n, 0.018, "acero")
    pu.extra["manija"] = list(pl.p(hu + 0.2, hv, d1 + 0.15))

    marco = Pieza("puerta_lateral_marco", peso_uv=1.3)
    _marco_puerta(marco, pl, L["u0"], L["u1"], L["v1"], "metal_oscuro", ancho=0.18, d_frente=0.17)
    for vh in (1.1, 3.95):
        for z0 in (vh - 0.19, vh + 0.065):
            marco.baja.cilindro((piv.x, piv.y, z0), (0, 0, 1), 0.05, 0.125, "hierro", lados=8)
        caja_plano(marco.baja, pl, L["u1"] + 0.03, L["u1"] + 0.17, vh - 0.12, vh + 0.12, 0.17, 0.19, "hierro",
                   sin=("+y",))
        marco.baja.revolucion([(0.02, 0), (0.02, 0.03), (0.03, 0.04), (0.0, 0.07)], (piv.x, piv.y, vh + 0.19), 8,
                              "hierro", tapa_ini=False)
    return [pu, marco]


# ======================================================================================================
# Ventanas de la vivienda
# ======================================================================================================


def ventanas():
    piezas = []
    V = VENT_F
    pl = FRENTE
    marco = Pieza("ventana_frontal_marco", peso_uv=1.2)
    t = cp._marco_ventana(marco, pl, V["x0"], V["x1"], V["z0"], V["z1"], ancho=0.15, con_inferior=False)
    caja_plano(marco.baja, pl, V["x0"] + t, V["x1"] - t, 7.28, 7.34, -0.08, -0.03, "metal_oscuro", sin=("+y",))
    cristal = Pieza("ventana_frontal_cristal", peso_uv=0.5)
    caja_plano(cristal.baja, pl, V["x0"] + t, V["x1"] - t, V["z0"] + t, V["z1"] - t, -0.13, -0.08, "vidrio")
    alfeizar = Pieza("ventana_frontal_alfeizar", peso_uv=1.2)
    caja_plano(alfeizar.baja, pl, V["x0"] - 0.22, V["x1"] + 0.22, V["z0"] - 0.14, V["z0"], -MURO + 0.05, 0.42,
               "losa", sin=("+y",), giro_extra=rot("X", -2.0))
    maceta = Pieza("maceta_pequena", peso_uv=2.0)
    cp._maceta_pequena(maceta, Vector((V["x0"] + 0.5, -MY - 0.28, V["z0"] - 0.012)))
    piezas += [marco, cristal, alfeizar, maceta]

    # Persiana enrollable a medio bajar: caja con la tapa de registro, rodillo visible, guías, lamas y cinta.
    caja = Pieza("persiana_caja", peso_uv=1.3)
    cb, ca = caja.baja, caja.alta
    u0, u1 = V["x0"] - 0.22, V["x1"] + 0.22
    vb, vt = V["z1"] + 0.16, V["z1"] + 0.56
    d0, d1 = PANEL, 0.4
    caja_plano(cb, pl, u0, u1, vb + 0.12, vt, d0, d1, "panel_limpio", sin=("+y",))
    caja_plano(cb, pl, u0, u0 + 0.03, vb, vb + 0.12, d0, d1, "panel_limpio", sin=("+y",))
    caja_plano(cb, pl, u1 - 0.03, u1, vb, vb + 0.12, d0, d1, "panel_limpio", sin=("+y",))
    caja_plano(cb, pl, u0 + 0.03, u1 - 0.03, vb, vb + 0.02, 0.3, d1, "panel_limpio", sin=("+y", "-x", "+x"))
    # Rodillo con la persiana enrollada, que se ve por la ranura de abajo.
    cb.cilindro(pl.p(u0 + 0.03, vb + 0.14, 0.21), pl.u, 0.13, u1 - u0 - 0.06, "aluminio", lados=10, tapa_ini=False,
                tapa_fin=False)
    cb.cilindro(pl.p(u0 + 0.031, vb + 0.14, 0.21), -pl.u, 0.03, 0.04, "acero", lados=6)
    for uu in (u0 + 0.1, u1 - 0.1):
        tornillo(caja, pl.p(uu, vt - 0.12, d1), pl.n, 0.018, "acero")
    caja_plano(ca, pl, u0 + 0.3, u1 - 0.3, vb + 0.18, vt - 0.06, d1, d1 + 0.004, "panel_limpio")  # tapa de registro
    for k in range(int((u1 - u0) / 0.13)):
        ca.caja(pl.p(u0 + 0.06 + k * 0.13, vb + 0.14, 0.21), (0.01, 0.27, 0.27), "aluminio", giro=pl.giro)
    # Guías en U a los lados.
    for ug in (V["x0"] - 0.1, V["x1"] + 0.1):
        caja_plano(cb, pl, ug - 0.06, ug + 0.06, V["z0"] - 0.02, vb + 0.02, PANEL, 0.2, "aluminio", sin=("+y",))
    # Cinta del recogedor: baja por el lado derecho hasta la caja de la cinta.
    cb.caja(pl.p(V["x1"] + 0.3, (vb + 7.05) / 2, 0.12), (0.035, 0.006, vb - 7.05), "lona_silla", giro=pl.giro)
    caja_plano(cb, pl, V["x1"] + 0.24, V["x1"] + 0.36, 6.85, 7.08, PANEL, 0.12, "pintura_gris", sin=("+y",))
    piezas.append(caja)

    persiana = Pieza("persiana", peso_uv=1.2)
    pb = persiana.baja
    abajo = 7.25
    n = int((vb - abajo) / 0.105)
    for k in range(n):
        vv = vb - 0.02 - k * 0.105
        caja_plano(pb, pl, V["x0"] - 0.06, V["x1"] + 0.06, vv - 0.095, vv, 0.11, 0.155, "aluminio")
        caja_plano(persiana.alta, pl, V["x0"] + 0.1, V["x1"] - 0.1, vv - 0.05, vv - 0.045, 0.155, 0.16, "aluminio")
    vbot = vb - 0.02 - n * 0.105
    caja_plano(pb, pl, V["x0"] - 0.06, V["x1"] + 0.06, vbot - 0.07, vbot, 0.1, 0.17, "metal_oscuro")
    for uu in (V["x0"] + 0.4, V["x1"] - 0.4):
        caja_plano(pb, pl, uu - 0.04, uu + 0.04, vbot - 0.11, vbot - 0.07, 0.12, 0.15, "goma")
    piezas.append(persiana)

    # Ventana lateral (izquierda), pequeña, con cortina.
    L = VENT_L
    pl = IZQ
    marco_l = Pieza("ventana_lateral_marco", peso_uv=1.2)
    t = cp._marco_ventana(marco_l, pl, L["u0"], L["u1"], L["v0"], L["v1"], ancho=0.13)
    cristal_l = Pieza("ventana_lateral_cristal", peso_uv=0.5)
    caja_plano(cristal_l.baja, pl, L["u0"] + t, L["u1"] - t, L["v0"] + t, L["v1"] - t, -0.13, -0.08, "vidrio")
    cortina = Pieza("ventana_lateral_cortina", peso_uv=0.9)
    _cortina(cortina, pl, L["u0"] + t + 0.02, L["u1"] - t - 0.02, L["v1"] - t - 0.03, L["v0"] + t + 0.04, -0.22)
    piezas += [marco_l, cristal_l, cortina]
    return piezas


def _cortina(p, pl, u0, u1, vt, vb, d):
    """Cortina recogida a un lado con su barra: tela ondulada con grosor, más ancha arriba que en el lazo."""
    b = p.baja
    b.cilindro(pl.p(u0 - 0.02, vt + 0.03, d), pl.u, 0.016, u1 - u0 + 0.04, "acero", lados=6, tapa_ini=False,
               tapa_fin=False)
    anillos = []
    lazo = vb + (vt - vb) * 0.38
    for v, ancho, amp in ((vt, (u1 - u0) * 0.78, 0.028), (lazo, (u1 - u0) * 0.3, 0.04), (vb, (u1 - u0) * 0.45, 0.03)):
        k = 10
        delante, detras = [], []
        for i in range(k + 1):
            f = i / k
            u = u1 - f * ancho
            y = amp * (1 if i % 2 else -1) * (0.6 if i in (0, k) else 1.0)
            delante.append(pl.p(u, v, d - 0.03 + y))
            detras.append(pl.p(u, v, d - 0.03 + y + 0.012))
        anillos.append(delante + list(reversed(detras)))
    b.loft(anillos, "tela", tapa_ini=False, tapa_fin=True, suave=True)
    b.recalcular(b.ultimas)
    p.alta.tubo([pl.p(u1, lazo + 0.02, d - 0.08), pl.p(u1 - (u1 - u0) * 0.2, lazo, d - 0.09),
                 pl.p(u1 - (u1 - u0) * 0.32, lazo, d - 0.04)], 0.018, "tela", lados=6)


# ======================================================================================================
# Cartel de la tienda
# ======================================================================================================


def cartel():
    pl = FRENTE
    C = CARTEL
    c = Pieza("cartel_tienda", peso_uv=2.2)
    b, a = c.baja, c.alta
    d0, d1 = 0.13, 0.17
    for uu in (C["x0"] + 0.4, (C["x0"] + C["x1"]) / 2, C["x1"] - 0.4):  # separadores
        b.cilindro(pl.p(uu, (C["z0"] + C["z1"]) / 2, PANEL), pl.n, 0.035, d0 - PANEL, "acero", lados=6,
                   tapa_ini=False, tapa_fin=False)
    caja_plano(b, pl, C["x0"], C["x1"], C["z0"], C["z1"], d0, d1, "azul_tienda")
    m = 0.05
    for (u0, u1, v0, v1) in ((C["x0"] - 0.02, C["x1"] + 0.02, C["z1"] - m, C["z1"] + 0.02),
                             (C["x0"] - 0.02, C["x1"] + 0.02, C["z0"] - 0.02, C["z0"] + m),
                             (C["x0"] - 0.02, C["x0"] + m, C["z0"] + m, C["z1"] - m),
                             (C["x1"] - m, C["x1"] + 0.02, C["z0"] + m, C["z1"] - m)):
        caja_plano(b, pl, u0, u1, v0, v1, d1, d1 + 0.02, "acero", sin=("+y",))
    # Ocho remaches en el borde.
    vc = (C["z0"] + C["z1"]) / 2
    for uu, vv in ((C["x0"] + 0.012, C["z1"] - 0.012), (C["x1"] - 0.012, C["z1"] - 0.012),
                   (C["x0"] + 0.012, C["z0"] + 0.012), (C["x1"] - 0.012, C["z0"] + 0.012),
                   ((C["x0"] + C["x1"]) / 2, C["z1"] - 0.012), ((C["x0"] + C["x1"]) / 2, C["z0"] + 0.012),
                   (C["x0"] + 0.012, vc), (C["x1"] - 0.012, vc)):
        c.baja.revolucion([(0.024, 0), (0.024, 0.006), (0.016, 0.014), (0.0, 0.017)], pl.p(uu, vv, d1 + 0.02), 6,
                          "acero", eje=pl.n, tapa_ini=False)
        a.cupula(pl.p(uu, vv, d1 + 0.02), pl.n, 0.025, "acero", alto=0.017, lados=12)
    texto(b, "SUMINISTROS", pl.p((C["x0"] + C["x1"]) / 2, vc + 0.05, d1), pl.u, pl.v, pl.n, 0.29, 0.025, "rotulo",
          ancho_max=C["x1"] - C["x0"] - 0.6)
    texto(a, "REPUESTOS  ·  HERRAMIENTAS  ·  COLONIA", pl.p((C["x0"] + C["x1"]) / 2, C["z0"] + 0.09, d1),
          pl.u, pl.v, pl.n, 0.05, 0.002, "rotulo", ancho_max=C["x1"] - C["x0"] - 1.2)

    focos = Pieza("cartel_focos", peso_uv=1.6)
    neon = Pieza("cartel_focos_neon", peso_uv=0.6)
    fb = focos.baja
    for uu in (-3.15, -0.25):
        caja_plano(fb, pl, uu - 0.09, uu + 0.09, 5.67, 5.83, 0.21, 0.24, "metal_oscuro", sin=("+y",))
        P0 = pl.p(uu, 5.75, 0.23)
        P1 = pl.p(uu, 5.86, 0.62)
        fb.tubo([P0, pl.p(uu, 5.8, 0.45), P1], 0.022, "metal_oscuro", lados=6, radio_curva=0.1, tapa_ini=False,
                tapa_fin=False)
        # Cabeza del foco: cilindro apuntando al cartel (hacia abajo y hacia la pared).
        apunta = (pl.p(uu, vc, d1) - P1).normalized()
        cabeza = P1 + apunta * 0.04
        fb.revolucion([(0.0, -0.05), (0.06, -0.045), (0.085, 0.0), (0.085, 0.16), (0.075, 0.16)], cabeza, 10,
                      "metal_oscuro", eje=apunta, tapa_ini=False, tapa_fin=False)
        neon.baja.cilindro(cabeza + apunta * 0.15, apunta, 0.074, 0.012, "neon", lados=10)
        for k in range(8):  # aletas de la carcasa (malla alta)
            focos.alta.revolucion([(0.085, 0), (0.095, 0.004), (0.085, 0.01)], cabeza + apunta * (0.02 + k * 0.015),
                                  10, "metal_oscuro", eje=apunta, tapa_ini=False, tapa_fin=False)
    focos.extra["luces"] = [list(pl.p(-3.15, 5.86, 0.62)), list(pl.p(-0.25, 5.86, 0.62))]
    return [c, focos, neon]


# ======================================================================================================
# Detalles de la fachada lateral y del entorno
# ======================================================================================================


def placa_numero():
    p = Pieza("placa_numero", peso_uv=2.5)
    pl = DER
    uc, vc = -0.62, 3.75
    w, h, ch = 0.46, 0.34, 0.05
    cont = [(-w / 2 + ch, -h / 2), (w / 2 - ch, -h / 2), (w / 2, -h / 2 + ch), (w / 2, h / 2 - ch), (w / 2 - ch, h / 2),
            (-w / 2 + ch, h / 2), (-w / 2, h / 2 - ch), (-w / 2, -h / 2 + ch)]
    p.baja.placa([(uc + x, vc + y) for x, y in cont], pl.p(0, 0, PANEL), pl.u, pl.v, pl.n, 0.025, "azul_tienda")
    texto(p.baja, "12", pl.p(uc, vc - 0.005, PANEL + 0.025), pl.u, pl.v, pl.n, 0.21, 0.02, "laton", resolucion=2)
    for x in (-w / 2 + 0.045, w / 2 - 0.045):
        for y in (-h / 2 + 0.045, h / 2 - 0.045):
            tornillo(p, pl.p(uc + x, vc + y, PANEL + 0.025), pl.n, 0.016, "laton")
    return p


def lampara_lateral():
    """Farol junto a la puerta de casa: placa, brazo, jaula de cuatro postes con su tejadillo y bombilla."""
    pl = DER
    uc, vp = PUERTA_L["u1"] + 0.55, 4.25
    c = Pieza("lampara_lateral", peso_uv=1.8)
    b = c.baja
    caja_plano(b, pl, uc - 0.11, uc + 0.11, vp - 0.15, vp + 0.15, PANEL, 0.1, "metal_oscuro", sin=("+y",))
    for vv in (vp - 0.1, vp + 0.1):
        tornillo(c, pl.p(uc, vv, 0.1), pl.n, 0.016, "acero")
    punta = pl.p(uc, vp + 0.02, 0.62)
    b.tubo([pl.p(uc, vp, 0.1), pl.p(uc, vp + 0.08, 0.38), punta], 0.026, "metal_oscuro", lados=6, radio_curva=0.12,
           tapa_ini=False, tapa_fin=True)
    centro = punta + Vector((0, 0, -0.12))
    b.tubo([punta, centro], 0.01, "metal_oscuro", lados=4)
    # Tejadillo (pirámide), aro de arriba, cuatro postes y base.
    zt = centro.z
    b.revolucion([(0.13, -0.04), (0.17, -0.04), (0.17, -0.02), (0.0, 0.08)], (centro.x, centro.y, zt), 4,
                 "metal_oscuro", giro=math.pi / 4, suave=False)
    for k in range(4):
        ang = math.pi / 4 + k * math.pi / 2
        dv = Vector((math.cos(ang), math.sin(ang), 0)) * 0.12
        b.caja(Vector((centro.x, centro.y, zt - 0.22)) + dv, (0.02, 0.02, 0.36), "metal_oscuro",
               giro=rot("Z", math.degrees(ang)))
    b.revolucion([(0.0, -0.48), (0.06, -0.47), (0.14, -0.43), (0.14, -0.4)], (centro.x, centro.y, zt), 4,
                 "metal_oscuro", giro=math.pi / 4, tapa_fin=True, suave=False)
    bombilla = Pieza("lampara_lateral_bombilla_neon", peso_uv=0.5)
    bombilla.baja.revolucion([(0.0, -0.36), (0.045, -0.33), (0.065, -0.26), (0.05, -0.18), (0.028, -0.13),
                              (0.028, -0.06)], (centro.x, centro.y, zt), 8, "neon", tapa_fin=True)
    c.extra["luz"] = [centro.x, centro.y, zt - 0.25]
    return [c, bombilla]


def _caja_plastico(c, alta, centro, tam, giro_z, mat, tapa=True, etiqueta=None, despegada=False, rnd=None):
    """Caja de plástico de las de reparto: paredes con grosor, nervios, asas y tapa con faldón."""
    sx, sy, sz = tam
    g = rot("Z", giro_z)
    u = g @ Vector((1, 0, 0))
    v = g @ Vector((0, 1, 0))
    o = Vector(centro)
    t = 0.035
    ext = [(-sx / 2, -sy / 2), (sx / 2, -sy / 2), (sx / 2, sy / 2), (-sx / 2, sy / 2)]
    inte = [(-sx / 2 + t, -sy / 2 + t), (sx / 2 - t, -sy / 2 + t), (sx / 2 - t, sy / 2 - t), (-sx / 2 + t, sy / 2 - t)]
    c.anillo_placa(ext, inte, o, u, v, Vector((0, 0, 1)), sz, mat, fondo=sz - 0.04, mat_fondo=mat, mat_hueco=mat)
    c.poligono([o + u * x + v * y for x, y in ext], mat, (0, 0, -1), oculta=True)
    # Nervios y asas (malla alta).
    for su in (-1, 1):
        for k in range(5):
            f = -0.4 + k * 0.2
            alta.caja(o + u * (su * (sx / 2 + 0.006)) + v * (f * sy) + Vector((0, 0, sz * 0.45)), (0.012, 0.03, sz * 0.8),
                      mat, giro=g)
        alta.caja(o + u * (su * (sx / 2 + 0.002)) + Vector((0, 0, sz - 0.12)), (0.01, sy * 0.35, 0.07), "negro_mate",
                  giro=g)
    if tapa:
        c.caja(o + Vector((0, 0, sz + 0.02)), (sx + 0.04, sy + 0.04, 0.04), mat, giro=g)
        c.caja(o + Vector((0, 0, sz - 0.02)), (sx + 0.05, sy + 0.05, 0.04), mat, giro=g, sin=("+z",))
    if etiqueta:
        # Etiqueta en el frente (-v): papel con una esquina que se levanta.
        f0 = o - v * (sy / 2 + 0.003) + Vector((0, 0, sz * 0.5))
        c.caja(f0, (0.3, 0.004, 0.18), "papel", giro=g)
        if despegada:
            bis = f0 + u * 0.15 + Vector((0, 0, 0.09))
            gg = g @ rot("Z", 35)
            c.caja(bis + (gg @ Vector((0.05, -0.0, 0))) - v * 0.02 + Vector((0, 0, -0.03)), (0.1, 0.004, 0.06),
                   "papel", giro=gg)
        texto(alta, etiqueta, f0 - v * 0.003 + Vector((0, 0, 0.03)), u, Vector((0, 0, 1)), -v, 0.045, 0.001,
              "tinta", ancho_max=0.26)
        texto(alta, "COLONIA · LOTE 7B", f0 - v * 0.003 + Vector((0, 0, -0.04)), u, Vector((0, 0, 1)), -v, 0.022,
              0.001, "tinta", ancho_max=0.26)


def cajas():
    """Tres cajas de mercancía: dos apiladas y una abierta (vacía: el comerciante las reutiliza)."""
    p = Pieza("cajas_mercancia", peso_uv=1.6)
    b, a = p.baja, p.alta
    rnd = random.Random(4)
    _caja_plastico(b, a, (6.2, 2.45, BASE_Z), (0.78, 0.92, 0.52), -90 + 3, "plastico_naranja", etiqueta="FRÁGIL",
                   rnd=rnd)
    _caja_plastico(b, a, (6.17, 2.42, BASE_Z + 0.56), (0.72, 0.84, 0.48), -90 - 6, "plastico_gris",
                   etiqueta="RECAMBIOS", despegada=True, rnd=rnd)
    _caja_plastico(b, a, (6.25, 3.4, BASE_Z), (0.72, 0.8, 0.46), -90 + 9, "plastico_naranja", tapa=False,
                   etiqueta="VACÍA", despegada=True, rnd=rnd)
    # La tapa de la caja abierta, apoyada contra la pared.
    g = rot("Z", -90) @ rot("Y", -12)
    b.caja(Vector((5.66, 3.85, BASE_Z + 0.42)), (0.8, 0.84, 0.04), "plastico_naranja", giro=rot("Y", -78))
    return p


def contenedor():
    """Contenedor de reciclaje con ruedas, en el suelo al lado del porche; tapa aparte (pivote en la bisagra)."""
    cx, cy = 7.45, 3.2
    w, d, h = 0.72, 0.82, 1.2
    p = Pieza("contenedor_reciclaje", peso_uv=1.5)
    b, a = p.baja, p.alta
    anillos = []
    for z, k in ((0.08, 0.88), (h - 0.05, 1.0)):
        anillos.append([Vector((cx + x * k, cy + y * k, z)) for x, y in
                        ((-w / 2, -d / 2), (w / 2, -d / 2), (w / 2, d / 2), (-w / 2, d / 2))])
    b.loft(anillos, "reciclaje", tapa_ini=True, tapa_fin=True, suave=False)
    b.caja_de((cx - w / 2 - 0.03, cy - d / 2 - 0.03, h - 0.08), (cx + w / 2 + 0.03, cy + d / 2 + 0.03, h - 0.03),
              "reciclaje")
    # Ruedas detrás (lado de la casa, -x) y su eje; asa.
    for sy in (-1, 1):
        b.cilindro((cx - w / 2 + 0.05, cy + sy * (d / 2 - 0.02), 0.1), (0, sy, 0), 0.1, 0.07, "goma", lados=10)
    b.cilindro((cx - w / 2 + 0.05, cy - d / 2 + 0.05, 0.1), (0, 1, 0), 0.02, d - 0.1, "acero", lados=6,
               tapa_ini=False, tapa_fin=False)
    b.tubo([(cx - w / 2 - 0.02, cy - 0.3, h - 0.1), (cx - w / 2 - 0.1, cy - 0.3, h - 0.1),
            (cx - w / 2 - 0.1, cy + 0.3, h - 0.1), (cx - w / 2 - 0.02, cy + 0.3, h - 0.1)], 0.018, "plastico_gris",
           lados=6, radio_curva=0.04)
    # Símbolo de reciclaje: tres flechas en triángulo (malla alta), en la cara de +x.
    o = Vector((cx + w / 2 * 0.95 + 0.004, cy, 0.62))
    for k in range(3):
        ang = math.radians(90 + k * 120)
        ang2 = math.radians(90 + (k + 1) * 120)
        p0 = Vector((0, math.cos(ang) * 0.17, math.sin(ang) * 0.17))
        p1 = Vector((0, math.cos(ang2) * 0.17, math.sin(ang2) * 0.17))
        d_ = (p1 - p0)
        mid = p0 + d_ * 0.42
        largo = d_.length * 0.62
        gg = rot("X", math.degrees(math.atan2(d_.z, d_.y)))
        a.caja(o + mid, (0.004, largo, 0.045), "rotulo", giro=gg)
        a.placa([(-0.06, 0.0), (0.06, 0.0), (0.0, 0.07)], o + p0 + d_ * 0.78, Vector((0, d_.y, d_.z)).normalized().cross(
            Vector((1, 0, 0))), Vector((0, d_.y, d_.z)).normalized(), Vector((1, 0, 0)), 0.004, "rotulo")
    texto(a, "RECICLAJE", o + Vector((0, 0, -0.3)), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.06, 0.002, "rotulo",
          ancho_max=0.6)

    tapa = Pieza("contenedor_tapa", pivote=(cx - w / 2 - 0.03, cy, h), peso_uv=1.5)
    tapa.baja.caja_de((cx - w / 2 - 0.04, cy - d / 2 - 0.04, h - 0.02), (cx + w / 2 + 0.06, cy + d / 2 + 0.04, h + 0.06),
                      "reciclaje")
    tapa.baja.caja_de((cx + w / 2 + 0.02, cy - 0.2, h - 0.06), (cx + w / 2 + 0.08, cy + 0.2, h + 0.0), "reciclaje",
                      sin=("+z",))
    tapa.baja.cilindro((cx - w / 2 - 0.04, cy - d / 2, h), (0, 1, 0), 0.03, d, "plastico_gris", lados=6)
    return [p, tapa]


def silla():
    """Silla plegable de tubo con el respaldo contra la pared: asiento y respaldo de lona gastada."""
    p = Pieza("silla_plegable", peso_uv=1.8)
    b, a = p.baja, p.alta
    x0 = MX + PANEL + 0.08
    yc = -1.85
    r = 0.032
    zs = BASE_Z + 1.55
    zr = BASE_Z + 3.15
    hw = 0.5

    def P(x, y, z):
        return Vector((x0 + x, yc + y, z))

    # Bastidor de atrás: U invertida (patas traseras + respaldo).
    b.tubo([P(0.18, -hw, BASE_Z), P(0.1, -hw, zs), P(0.0, -hw, zr), P(0.0, hw, zr), P(0.1, hw, zs),
            P(0.18, hw, BASE_Z)], r, "pintura_verde_silla", lados=6, radio_curva=0.15, pasos_curva=3)
    # Bastidor de delante: patas delanteras y travesaño bajo el asiento.
    b.tubo([P(1.05, -hw + 0.03, BASE_Z), P(0.9, -hw + 0.03, zs - 0.05), P(0.9, hw - 0.03, zs - 0.05),
            P(1.05, hw - 0.03, BASE_Z)], r, "pintura_verde_silla", lados=6, radio_curva=0.1, pasos_curva=2)
    for s in (-1, 1):  # largueros del asiento
        b.tubo([P(0.92, s * (hw - 0.01), zs), P(0.1, s * hw, zs)], r * 0.85, "pintura_verde_silla", lados=6,
               tapa_ini=False, tapa_fin=False)
        a.cupula(P(0.11, s * (hw + 0.03), zs), (0, s, 0), 0.02, "acero", alto=0.012)
        a.cupula(P(0.9, s * (hw + 0.0), zs - 0.05), (0, s, 0), 0.02, "acero", alto=0.012)
    b.tubo([P(0.14, -hw, BASE_Z + 0.4), P(0.14, hw, BASE_Z + 0.4)], r * 0.8, "pintura_verde_silla", lados=6)
    # Asiento: lona combada entre los largueros. Respaldo: lona algo curvada.
    secc = []
    for k in range(4):
        f = k / 3
        x = 0.12 + 0.78 * f
        secc.append((x, zs + 0.01 - 0.045 * math.sin(math.pi * f)))
    perfil = secc + [(x, z - 0.02) for x, z in reversed(secc)]
    b.placa(perfil, P(0, -hw + 0.02, 0) + Vector((0, 0, 0)) - Vector((x0, 0, 0)) + Vector((x0, 0, 0)),
            Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0)), 2 * hw - 0.04, "lona_silla", atras=True)
    perfil_r = [(0.02, zr - 0.6), (0.04, zr - 0.35), (0.02, zr - 0.08), (0.04, zr - 0.08), (0.06, zr - 0.35),
                (0.04, zr - 0.6)]
    b.placa(perfil_r, P(0, -hw + 0.03, 0), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0)), 2 * hw - 0.06,
            "lona_silla", atras=True)
    for x, y in ((0.18, -hw), (0.18, hw), (1.05, -hw + 0.03), (1.05, hw - 0.03)):  # tacos de goma
        b.cilindro(P(x, y, BASE_Z), (0, 0, 1), 0.042, 0.05, "goma", lados=6, tapa_ini=False)
    # Costuras de la lona (malla alta).
    for s in (-1, 1):
        a.tubo([P(0.14, s * (hw - 0.06), zs + 0.012), P(0.88, s * (hw - 0.06), zs + 0.012)], 0.004, "lona_silla",
               lados=4)
    p.extra["asiento"] = list(P(0.5, 0, zs))
    return p


def bajante(gargola):
    p = Pieza("bajante", peso_uv=1.2)
    b, a = p.baja, p.alta
    xb = -4.85
    yw = MY + PANEL + 0.13
    gx, gy, gz = gargola
    # Embudo (cabeza de bajante) bajo la gárgola.
    zt = gz - 0.05
    b.revolucion([(0.08, -0.35), (0.08, -0.25), (0.2, -0.05), (0.2, 0.0), (0.17, 0.0), (0.17, -0.05), (0.07, -0.24)],
                 (xb, gy - 0.05, zt), 4, "metal_oscuro", giro=math.pi / 4, tapa_ini=False, tapa_fin=False, suave=False)
    camino = [(xb, gy - 0.05, zt - 0.3), (xb, gy - 0.05, zt - 0.55), (xb, yw, zt - 0.85), (xb, yw, 0.95),
              (xb, yw + 0.26, 0.66)]
    r = 0.1
    b.tubo(camino, r, "metal_oscuro", lados=8, radio_curva=0.2, pasos_curva=3, tapa_ini=False, tapa_fin=False)
    fin = Vector(camino[-1])
    dirv = (Vector(camino[-1]) - Vector(camino[-2])).normalized()
    b.revolucion([(r, 0), (r * 0.8, 0), (r * 0.8, -0.16), (0.0, -0.16)], fin, 8, "metal_oscuro", eje=dirv,
                 tapa_ini=False, tapa_fin=False, giro=math.pi / 8, mats_tramo=["metal_oscuro", "negro_mate",
                                                                               "negro_mate"])
    for z in (6.6, 4.1, 1.8):
        b.revolucion([(0.122, 0), (0.122, 0.075)], (xb, yw, z - 0.037), 8, "metal_oscuro", giro=math.pi / 8)
        b.caja_de((xb - 0.02, MY + PANEL, z - 0.03), (xb + 0.02, yw - 0.115, z + 0.03), "metal_oscuro")
        b.caja_de((xb - 0.09, MY + PANEL, z - 0.09), (xb + 0.09, MY + PANEL + 0.02, z + 0.09), "metal_oscuro",
                  sin=("-y",))
        for dx in (-0.055, 0.055):
            tornillo(p, (xb + dx, MY + PANEL + 0.02, z), (0, 1, 0), 0.018, "acero", en_baja=False)
    p.extra["pie"] = [xb, yw + 0.4, 0.0]
    return p


def medidor():
    """Contador de luz en el lateral derecho, cerca de la esquina de delante."""
    pl = DER
    u0, u1, v0, v1 = -3.42, -2.86, 2.6, 3.46
    d0, d1 = PANEL, 0.27
    caja = Pieza("medidor", peso_uv=1.6)
    b = caja.baja
    caja_plano(b, pl, u0, u1, v0, v1, d0, d1, "pintura_gris", sin=("+y",), mats={"-y": "negro_mate"})
    b.tubo([pl.p((u0 + u1) / 2, v0, 0.16), pl.p((u0 + u1) / 2, 1.53, 0.16)], 0.035, "metal_oscuro", lados=6,
           tapa_ini=False, tapa_fin=False)
    piv = pl.p(u0, v0, d1 + 0.012)
    puerta = Pieza("medidor_puerta", pivote=piv, peso_uv=1.8)
    pb = puerta.baja
    ext = rect(u0, u1, v0, v1)
    uc = (u0 + u1) / 2
    hueco = rect(uc - 0.13, uc + 0.13, 3.14, 3.3)
    pb.anillo_placa(ext, hueco, pl.p(0, 0, d1), pl.u, pl.v, pl.n, 0.024, "pintura_gris")
    pb.cara_con_huecos([pl.p(u, v, d1) for u, v in ext], [[pl.p(u, v, d1) for u, v in hueco]], "pintura_gris", -pl.n)
    caja_plano(pb, pl, u1 - 0.06, u1 - 0.02, 2.95, 3.12, d1 + 0.024, d1 + 0.05, "metal_oscuro", sin=("+y",))
    for vv in (v0 + 0.12, v1 - 0.12):
        pb.cilindro(pl.p(u0, vv - 0.06, d1 + 0.012), (0, 0, 1), 0.016, 0.12, "metal_oscuro", lados=6)
    tri = [(uc - 0.1, 2.76), (uc + 0.1, 2.76), (uc, 2.93)]
    puerta.alta.placa(tri, pl.p(0, 0, d1 + 0.024), pl.u, pl.v, pl.n, 0.002, "pegatina")
    pant = Pieza("medidor_pantalla_neon", peso_uv=0.6)
    caja_plano(pant.baja, pl, uc - 0.11, uc + 0.11, 3.16, 3.28, d1 - 0.02, d1 + 0.004, "neon", sin=("+y",))
    caja.extra["salida_cable"] = list(pl.p(uc, v1, 0.16))
    return [caja, puerta, pant]


def cable(salida, destino):
    """Cable del medidor que sube por la pared, salva la moldura y el remate, y cruza la cubierta hasta el aire."""
    p = Pieza("cable_electrico", peso_uv=1.0)
    b = p.baja
    x, y, z = salida
    xw = MX + PANEL + 0.1
    sobre = lambda xx, yy: (xx, yy, z_techo(yy) + 0.03)
    puntos = [(xw, y, z), (xw, y, 5.4), (MX + 0.27, y, 5.55), (MX + 0.27, y, 5.95), (xw, y, 6.1), (xw, y, 7.3),
              (xw, y + 0.3, 8.05), (MX + 0.24, y + 0.35, z_techo(y + 0.35) - 0.08),
              (MX + 0.24, y + 0.35, z_techo(y + 0.35) + 0.08), sobre(MX - 0.2, y + 0.4), sobre(4.0, y + 1.2),
              sobre(destino[0] + 0.4, destino[1] - 0.6), tuple(destino)]
    b.tubo(puntos, 0.026, "goma", lados=5, radio_curva=0.1, pasos_curva=2)
    for zz in (4.6, 7.0):
        b.caja_de((MX + PANEL, y - 0.05, zz - 0.07), (MX + PANEL + 0.025, y + 0.05, zz + 0.07), "metal_oscuro",
                  sin=("-x",))
        b.tubo([(MX + PANEL + 0.02, y, zz - 0.03), (xw + 0.04, y, zz - 0.035), (xw + 0.07, y, zz + 0.03)], 0.012,
               "metal_oscuro", lados=4, radio_curva=0.03, pasos_curva=2)
    return p


def poste():
    """Poste de amarre junto a la tienda, con su argolla gastada por las cuerdas."""
    p = Pieza("poste_amarre", peso_uv=1.8)
    c = Vector((-5.3, -4.95, BASE_Z))
    b = p.baja
    b.revolucion([(0.2, 0), (0.2, 0.05), (0.13, 0.08), (0.12, 0.9), (0.135, 0.93), (0.135, 0.98), (0.09, 1.06),
                  (0.0, 1.09)], c, 10, "metal_oscuro", tapa_ini=False)
    for k in range(4):
        ang = math.tau * k / 4 + math.pi / 4
        p.alta.cupula(c + Vector((math.cos(ang) * 0.17, math.sin(ang) * 0.17, 0.05)), (0, 0, 1), 0.025, "acero",
                      alto=0.02, lados=6)
    # Cáncamo y argolla (del lado de la calle).
    ojo = c + Vector((0.0, -0.13, 0.8))
    b.revolucion([(0.035, 0), (0.035, 0.05)], ojo, 6, "acero", eje=(0, -1, 0), tapa_ini=False)
    anillo = [ojo + Vector((0, -0.08, 0)) + Vector((0, math.sin(t) * 0.04, -0.13 + math.cos(t) * 0.13)) * 1.0
              for t in [math.tau * i / 10 for i in range(11)]]
    anillo = [ojo + Vector((math.sin(t) * 0.11, -0.07, -0.11 + math.cos(t) * 0.11)) for t in
              [math.tau * i / 10 for i in range(11)]]
    b.tubo(anillo, 0.018, "acero_pulido", lados=5, tapa_ini=False, tapa_fin=False)
    return p


def aire_acondicionado():
    """Unidad exterior del aire en la cubierta: carcasa, ventilador visible tras su rejilla, rejillas y tubos."""
    p = Pieza("aire_acondicionado", peso_uv=1.5)
    b, a = p.baja, p.alta
    x0, x1, y0, y1 = 1.3, 2.9, 1.4, 2.3
    zr = z_techo(y1)
    z0, z1 = zr + 0.12, zr + 1.02
    for yy in (y0 + 0.12, y1 - 0.12):
        b.caja_de((x0 - 0.1, yy - 0.05, z_techo(yy) - 0.02), (x1 + 0.1, yy + 0.05, z0), "goma", sin=("-z",))
    b.caja_de((x0, y0, z0), (x1, y1, z1), "pintura_gris", sin=("-y",))
    # Frente con el hueco del ventilador (con fondo oscuro).
    cx, cz, r = x0 + 0.62, (z0 + z1) / 2, 0.36
    ext = []
    inte = []
    hw, hh = 0.62, (z1 - z0) / 2
    esquina = math.atan2(hh, hw)
    angs = sorted({0.0, esquina, math.pi / 2, math.pi - esquina, math.pi, math.pi + esquina, 1.5 * math.pi,
                   math.tau - esquina} | {math.tau * k / 16 + math.tau / 32 for k in range(16)})
    angs = [x for x in angs if all(abs(x - y) > 0.05 or x == y for y in (esquina, math.pi - esquina, math.pi + esquina,
                                                                          math.tau - esquina))]
    for ang in angs:
        ca, sa = math.cos(ang), math.sin(ang)
        t = min(abs(hw / ca) if abs(ca) > 1e-6 else 9, abs(hh / sa) if abs(sa) > 1e-6 else 9)
        ext.append((cx + ca * t, cz + sa * t))
        inte.append((cx + ca * r, cz + sa * r))
    b.anillo_placa(ext, inte, Vector((0, y0, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)), 0.02,
                   "pintura_gris", fondo=0.32, mat_fondo="negro_mate", mat_hueco="pintura_gris")
    b.poligono([Vector((cx + math.cos(t) * r, y0 + 0.3, cz + math.sin(t) * r)) for t in
                [math.tau * k / 12 for k in range(12)]], "negro_mate", (0, -1, 0))
    b.caja_de((x0 + 1.24, y0 - 0.02, z0), (x1, y0, z1), "pintura_gris", sin=("+y",))
    # Ventilador: buje y cuatro palas inclinadas.
    eje = Vector((cx, y0 + 0.18, cz))
    b.revolucion([(0.0, -0.1), (0.04, -0.09), (0.08, -0.05), (0.08, 0)], eje, 8, "negro_mate", eje=(0, 1, 0),
                 tapa_fin=True)
    for k in range(4):
        ang = math.radians(45 + 90 * k)
        dv = Vector((math.cos(ang), 0, math.sin(ang)))
        g = Matrix.Rotation(-ang, 3, "Y") @ rot("X", 28)
        b.caja(eje + dv * 0.2 + Vector((0, -0.02, 0)), (0.26, 0.012, 0.13), "acero", giro=g)
    # Rejilla delantera: dos aros y una cruz.
    for rr in (0.18, 0.33):
        aro = [Vector((cx + math.cos(t) * rr, y0 - 0.03, cz + math.sin(t) * rr)) for t in
               [math.tau * i / 12 for i in range(13)]]
        b.tubo(aro, 0.01, "metal_oscuro", lados=4, tapa_ini=False, tapa_fin=False)
    b.caja(Vector((cx, y0 - 0.03, cz)), (0.7, 0.014, 0.014), "metal_oscuro")
    b.caja(Vector((cx, y0 - 0.03, cz)), (0.014, 0.014, 0.7), "metal_oscuro")
    for k in range(10):  # rejilla de lamas del lateral y de arriba (malla alta)
        a.caja(Vector((x1 + 0.004, y0 + 0.1 + k * 0.07, cz)), (0.006, 0.02, 0.7), "metal_oscuro")
        a.caja(Vector((x0 + 0.15 + k * 0.13, (y0 + y1) / 2, z1 + 0.003)), (0.03, 0.75, 0.005), "metal_oscuro")
    texto(a, "COLONAIR", Vector((x0 + 1.42, y0 - 0.021, z1 - 0.12)), (1, 0, 0), (0, 0, 1), (0, -1, 0), 0.05, 0.002,
          "azul_tienda", ancho_max=0.3)
    # Tubos de cobre aislados que bajan a la cubierta.
    for dz, rr in ((0.18, 0.04), (0.32, 0.03)):
        b.tubo([(x1, y1 - 0.25, z0 + dz), (x1 + 0.25, y1 - 0.25, z0 + dz), (x1 + 0.3, y1 - 0.25, zr + 0.02)], rr,
               "goma", lados=6, radio_curva=0.08, pasos_curva=2, tapa_fin=False)
    p.extra["entrada_cable"] = [x0 + 1.5, y0, z0 + 0.3]
    return p


def antena():
    """Mástil con antena parabólica (contacto con los proveedores) y sus vientos."""
    p = Pieza("antena", peso_uv=1.4)
    b, a = p.baja, p.alta
    cx, cy = -3.7, 2.6
    zr = z_techo(cy)
    b.caja_de((cx - 0.2, cy - 0.2, zr), (cx + 0.2, cy + 0.2, zr + 0.03), "metal_oscuro", sin=("-z",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            tornillo(p, (cx + sx * 0.14, cy + sy * 0.14, zr + 0.03), (0, 0, 1), 0.022, "acero")
    top = zr + 1.85
    b.cilindro((cx, cy, zr + 0.03), (0, 0, 1), 0.04, top - zr - 0.03, "aluminio", lados=8, tapa_ini=False)
    # Plato: paraboloide con grosor, mirando arriba y hacia delante-izquierda.
    mira = Vector((-0.55, -0.55, 0.62)).normalized()
    centro = Vector((cx, cy, top - 0.35)) + mira * 0.16
    perfil = list(reversed([(0.0, 0.0), (0.15, 0.013), (0.3, 0.05), (0.44, 0.11), (0.45, 0.1), (0.44, 0.095),
                            (0.3, 0.035), (0.15, -0.002), (0.0, -0.015)]))
    b.revolucion(perfil, centro, 14, "panel_limpio", eje=mira, tapa_ini=False, tapa_fin=False)
    b.tubo([Vector((cx, cy, top - 0.35)), centro - mira * 0.01], 0.03, "aluminio", lados=6)
    u, _ = base_de(mira)
    borde = centro + mira * 0.1 - mira.cross(u) * 0.44
    foco = centro + mira * 0.42
    b.tubo([borde, foco], 0.014, "aluminio", lados=4)
    b.revolucion([(0.035, -0.06), (0.04, -0.03), (0.04, 0.05), (0.03, 0.06)], foco, 8, "pintura_gris", eje=-mira)
    # Vientos y sus anclajes.
    for k in range(3):
        ang = math.radians(30 + k * 120)
        ancla = Vector((cx + math.cos(ang) * 0.95, cy + math.sin(ang) * 0.95, 0))
        ancla.z = z_techo(ancla.y)
        b.tubo([Vector((cx, cy, zr + 1.2)), ancla + Vector((0, 0, 0.04))], 0.006, "acero", lados=4)
        b.caja(ancla + Vector((0, 0, 0.02)), (0.1, 0.1, 0.04), "metal_oscuro", sin=("-z",))
    p.extra["plato"] = list(centro)
    return p


# ======================================================================================================
# Todo junto
# ======================================================================================================


def construir():
    piezas = [base()] + escalones() + [zocalo(), paredes(), moldura()]
    te = techo()
    piezas.append(te)
    piezas += escaparate()
    piezas += toldo()
    pt = puerta_tienda()
    piezas += pt
    piezas.append(pizarra())
    pl = puerta_lateral()
    piezas += pl
    piezas += ventanas()
    piezas += cartel()
    piezas.append(placa_numero())
    piezas += lampara_lateral()
    piezas.append(cajas())
    piezas += contenedor()
    si = silla()
    piezas.append(si)
    baj = bajante(te.extra["gargola"])
    piezas.append(baj)
    med = medidor()
    piezas += med
    aire = aire_acondicionado()
    piezas.append(cable(med[0].extra["salida_cable"], aire.extra["entrada_cable"]))
    piezas += [poste(), aire, antena()]
    esc = [p for p in piezas if p.nombre == "escalon_tienda"][0]
    P = {
        "manija": tuple(TIRADOR),
        "manija_agarre": tuple(TIRADOR),
        "manija_lateral": tuple(pl[0].extra["manija"]),
        "zocalo_z": ZOC_Z,
        "puerta_z0": HOJA_T["z0"],
        "puerta_suelo": ((PUERTA_T["x0"] + PUERTA_T["x1"]) / 2, -4.6, BASE_Z),
        "escalon_centro": tuple(esc.extra["centro"]),
        "felpudo_centro": (3.2, -4.6, BASE_Z),
        "bajante_pie": tuple(baj.extra["pie"]),
        "chimenea_boca": 99.0,
        "pico_agarre": (0.0, 0.1),
        "toldo_frente_y": -MY - 1.62,
        "silla_asiento": tuple(si.extra["asiento"]),
    }
    return piezas, P
