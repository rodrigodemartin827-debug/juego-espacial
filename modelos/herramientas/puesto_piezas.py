"""
Piezas del puesto de seguridad. Todo en STUDS, con la fachada principal (el ventanal) mirando a -Y.

Planta (vista desde arriba, -Y abajo):

          +Y (detrás: cable de la radio, gárgola)
     ┌───────────────┐
     │  tablón       │ puerta (+X), con el extintor entre la puerta y la ventana
 -X  │ ventana  silla│ ventana        │ calzada (x 4..7)
     └───────────────┘                │
       ventanal (-Y)     barrera ─────┤  brazo de 3 studs hacia +X, contrapeso hacia -X
                         interfono    │  cono
                         STOP         │
                                      ═══ banda reductora (los coches llegan desde -Y)

  estructura: losa de hormigón con isla (bordillo pintado en la punta), paredes de paneles de acero gruesos (0,35)
              gris oscuro con franja reflectante, angulares en las esquinas, pretil con albardilla.
  ventanal:   tres ventanas (frente y los dos lados: 270°) con marco reforzado, cristal grueso y malla de alambre.
  puerta:     acero reforzado, 3 bisagras, cerradura con teclado, cierre de varillas visible por fuera, barra
              antipánico por dentro, cartel «SEGURIDAD COLONIAL» y cierrapuertas.
  techo:      foco giratorio (neón cian), sirena, baliza naranja, antena con espiral, radio con su cable, panel
              solar y bandera de la colonia.
  fuera:      2 cámaras, tablón de avisos, extintor, papelera, taza de café en el alféizar.
  barrera:    poste con placa de 4 pernos, brazo con franjas y contrapeso, apoyo en el otro lado; interfono,
              cono, señal de STOP y banda reductora.
  dentro:     mostrador en L con monitores, la silla del guardia (hundida), sus cosas y la radio base.
"""

import math
import random

from mathutils import Matrix, Vector

from puesto_malla import Pieza, Plano, base_de, caja_plano, perno_hex, rot, texto, tornillo

# ======================================================================================================
# Medidas (studs)
# ======================================================================================================

SUELO = 0.25                 # cara de arriba de la losa
X0, X1 = -2.8, 2.8           # caras de fuera de los muros laterales
Y0, Y1 = -2.9, 3.1           # cara de fuera de la fachada y del muro de atrás
MURO = 0.35                  # más grueso que en las casas (0,3): está blindado
XI0, XI1 = X0 + MURO, X1 - MURO
YI0, YI1 = Y0 + MURO, Y1 - MURO
PISO = SUELO + 0.05          # suelo de goma de dentro
TECHO_INT = 5.0              # cara de abajo del techo (dentro)
CUBIERTA = 5.4               # cubierta (fuera, dentro del pretil)
PRETIL = 5.85                # arriba del pretil (debajo de la albardilla)
PRETIL_E = 0.25              # grosor del pretil
ALB = 5.93                   # arriba de la albardilla
PX0, PX1 = X0 + PRETIL_E, X1 - PRETIL_E   # cara de dentro del pretil
PY0, PY1 = Y0 + PRETIL_E, Y1 - PRETIL_E

VZ0, VZ1 = 2.0, 4.4          # ventanas: alféizar y dintel
VF = (-2.3, 2.3)             # ventanal de la fachada (x)
VL = (-2.45, -0.3)           # ventanas laterales (y), en los dos lados
MULLION = 0.0                # parteluz del ventanal de la fachada (x)
PUERTA_Y = (0.6, 2.5)        # hueco de la puerta en el muro +X
PUERTA_Z1 = 4.6
BISAGRA_Y = PUERTA_Y[0]      # las bisagras van en el canto delantero: abre hacia fuera y hacia la barrera
CINTA_Z = (1.45, 1.75)       # franja reflectante

# Isla de hormigón con la barrera (a la derecha de la caseta, junto a la calzada).
ISLA_X = (2.9, 3.95)
ISLA_Y0 = -5.7
LOSA = dict(x0=-3.15, x1=3.95, y0=-3.35, y1=3.4)
CALZADA_X = (3.95, 7.1)
BARRERA = Vector((3.42, -3.85, SUELO))     # centro de la base del poste
BRAZO_Z = 2.95                             # eje de giro del brazo (altura del cubo)
BRAZO_LARGO = 3.0
INTERFONO = Vector((3.62, -4.75, SUELO))
STOP = Vector((3.42, -5.3, SUELO))
BANDA_Y = -6.55
CONO = Vector((6.75, -4.75, 0.0))

FOCO = Vector((-0.95, -1.25, CUBIERTA))    # base del foco
FOCO_YAW = 24.0                            # grados: apunta hacia delante y un poco hacia la barrera
FOCO_TILT = -14.0

FRENTE = Plano((0, Y0, 0), (0, -1, 0))     # u = +x
FONDO = Plano((0, Y1, 0), (0, 1, 0))       # u = -x
IZQ = Plano((X0, 0, 0), (-1, 0, 0))        # u = -y
DER = Plano((X1, 0, 0), (1, 0, 0))         # u = +y

P = {}   # puntos que usan los materiales (desgaste junto a la manija, asiento hundido...)


def rect(u0, u1, v0, v1):
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


def _quad(c, a, b, cc, d, mat, normal, oculta=False):
    return c.poligono([a, b, cc, d], mat, normal, oculta=oculta)


def _tira_alta(p, puntos, radio, mat, lados=6):
    """Cordón de soldadura o junta (solo malla alta)."""
    p.alta.tubo(puntos, radio, mat, lados=lados, tapa_ini=False, tapa_fin=False)


# ======================================================================================================
# Losa e isla
# ======================================================================================================


def _contorno_losa():
    """Contorno de la losa (x, y) en sentido antihorario: caseta + isla con la punta redondeada."""
    L = LOSA
    pts = [(L["x0"], L["y0"]), (ISLA_X[0], L["y0"])]
    # Punta de la isla: media circunferencia hacia -Y.
    r = (ISLA_X[1] - ISLA_X[0]) / 2
    cx = (ISLA_X[0] + ISLA_X[1]) / 2
    cy = ISLA_Y0 + r
    pts.append((ISLA_X[0], cy))
    for k in range(1, 8):
        a = math.pi + k * math.pi / 8
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    pts.append((ISLA_X[1], cy))
    pts += [(L["x1"], L["y1"]), (L["x0"], L["y1"])]
    return pts


def losa():
    """Losa de hormigón con chaflán en el canto y la isla de la barrera (bordillo pintado en la punta)."""
    p = Pieza("losa", peso_uv=0.8)
    b = p.baja
    ch = 0.05
    pts = _contorno_losa()
    n = len(pts)
    # Contorno de arriba metido hacia dentro (chaflán) y el de abajo en el suelo.

    def desplazar(pts, d):
        res = []
        for i in range(n):
            a, c, bb = Vector(pts[i - 1]), Vector(pts[i]), Vector(pts[(i + 1) % n])
            d1 = (c - a).normalized()
            d2 = (bb - c).normalized()
            n1 = Vector((d1.y, -d1.x))
            n2 = Vector((d2.y, -d2.x))
            m = (n1 + n2).normalized()
            k = d / max(0.3, m.dot(n1))
            res.append(c - m * k)
        return res

    arriba = desplazar(pts, ch)
    anillo_suelo = [Vector((x, y, 0.0)) for x, y in pts]
    anillo_canto = [Vector((x, y, SUELO - ch)) for x, y in pts]
    anillo_top = [Vector((v.x, v.y, SUELO)) for v in arriba]
    b.loft([anillo_suelo, anillo_canto, anillo_top], "hormigon", tapa_ini=False, tapa_fin=False, suave=False)
    # Cara de arriba: debajo de la caseta no se ve (la tapa el suelo de dentro), así que se recorta el hueco.
    hueco = [Vector((X0 + 0.02, Y0 + 0.02, SUELO)), Vector((X1 - 0.02, Y0 + 0.02, SUELO)),
             Vector((X1 - 0.02, Y1 - 0.02, SUELO)), Vector((X0 + 0.02, Y1 - 0.02, SUELO))]
    b.cara_con_huecos(anillo_top, [hueco], "hormigon", (0, 0, 1))
    # Juntas de dilatación y marcas (malla alta): surcos en la cara de arriba.
    for y in (-4.6,):
        p.alta.caja((sum(ISLA_X) / 2, y, SUELO - 0.004), (ISLA_X[1] - ISLA_X[0] - 0.1, 0.03, 0.012), "junta")
    for x in (-1.5, 1.5):
        p.alta.caja((x, Y1 + 0.15, SUELO - 0.004), (0.03, 0.5, 0.012), "junta")
    P["isla_punta"] = Vector(((ISLA_X[0] + ISLA_X[1]) / 2, ISLA_Y0, SUELO))
    return p


# ======================================================================================================
# Paredes, angulares y zócalo
# ======================================================================================================


def _muro(c, contorno_ext, huecos_ext, contorno_int, huecos_int, normal, mat="pared", mat_int="interior_pared"):
    c.cara_con_huecos(contorno_ext, huecos_ext, mat, normal)
    c.cara_con_huecos(contorno_int, huecos_int, mat_int, tuple(-v for v in normal))


def _jamba(c, a_ext, b_ext, a_int, b_int, normal, mat="pared_canto"):
    """Cara del grueso del muro dentro de un hueco (de a a b, por fuera y por dentro)."""
    c.poligono([a_ext, b_ext, b_int, a_int], mat, normal)


def paredes():
    p = Pieza("paredes", peso_uv=1.0)
    b = p.baja
    # ---- fachada (-Y) ---------------------------------------------------------------------------------
    ext = [Vector((X0, Y0, SUELO)), Vector((X1, Y0, SUELO)), Vector((X1, Y0, PRETIL)), Vector((X0, Y0, PRETIL))]
    h_ext = [Vector((VF[0], Y0, VZ0)), Vector((VF[1], Y0, VZ0)), Vector((VF[1], Y0, VZ1)), Vector((VF[0], Y0, VZ1))]
    intr = [Vector((XI0, YI0, SUELO)), Vector((XI1, YI0, SUELO)), Vector((XI1, YI0, TECHO_INT)),
            Vector((XI0, YI0, TECHO_INT))]
    h_int = [Vector((v.x, YI0, v.z)) for v in h_ext]
    _muro(b, ext, [h_ext], intr, [h_int], (0, -1, 0))
    # ---- muro de atrás (+Y) ---------------------------------------------------------------------------------
    ext = [Vector((X0, Y1, SUELO)), Vector((X1, Y1, SUELO)), Vector((X1, Y1, PRETIL)), Vector((X0, Y1, PRETIL))]
    intr = [Vector((XI0, YI1, SUELO)), Vector((XI1, YI1, SUELO)), Vector((XI1, YI1, TECHO_INT)),
            Vector((XI0, YI1, TECHO_INT))]
    _muro(b, ext, [], intr, [], (0, 1, 0))
    # ---- lateral izquierdo (-X): ventana delante -----------------------------------------------------------
    ext = [Vector((X0, Y0, SUELO)), Vector((X0, Y1, SUELO)), Vector((X0, Y1, PRETIL)), Vector((X0, Y0, PRETIL))]
    h_ext = [Vector((X0, VL[0], VZ0)), Vector((X0, VL[1], VZ0)), Vector((X0, VL[1], VZ1)), Vector((X0, VL[0], VZ1))]
    intr = [Vector((XI0, YI0, SUELO)), Vector((XI0, YI1, SUELO)), Vector((XI0, YI1, TECHO_INT)),
            Vector((XI0, YI0, TECHO_INT))]
    h_int = [Vector((XI0, v.y, v.z)) for v in h_ext]
    _muro(b, ext, [h_ext], intr, [h_int], (-1, 0, 0))
    # ---- lateral derecho (+X): ventana delante y la puerta detrás ------------------------------------------
    py0, py1 = PUERTA_Y
    ext = [Vector((X1, Y0, SUELO)), Vector((X1, py0, SUELO)), Vector((X1, py0, PUERTA_Z1)),
           Vector((X1, py1, PUERTA_Z1)), Vector((X1, py1, SUELO)), Vector((X1, Y1, SUELO)), Vector((X1, Y1, PRETIL)),
           Vector((X1, Y0, PRETIL))]
    h_ext = [Vector((X1, VL[0], VZ0)), Vector((X1, VL[1], VZ0)), Vector((X1, VL[1], VZ1)), Vector((X1, VL[0], VZ1))]
    intr = [Vector((XI1, YI0, SUELO)), Vector((XI1, py0, SUELO)), Vector((XI1, py0, PUERTA_Z1)),
            Vector((XI1, py1, PUERTA_Z1)), Vector((XI1, py1, SUELO)), Vector((XI1, YI1, SUELO)),
            Vector((XI1, YI1, TECHO_INT)), Vector((XI1, YI0, TECHO_INT))]
    h_int = [Vector((XI1, v.y, v.z)) for v in h_ext]
    _muro(b, ext, [h_ext], intr, [h_int], (1, 0, 0))

    # ---- grueso del muro en los huecos ------------------------------------------------------------------
    def hueco_frontal(x0, x1, z0, z1, y_ext, y_int):
        _jamba(b, Vector((x0, y_ext, z0)), Vector((x1, y_ext, z0)), Vector((x0, y_int, z0)), Vector((x1, y_int, z0)),
               (0, 0, 1), "alfeizar_int")
        _jamba(b, Vector((x0, y_ext, z1)), Vector((x1, y_ext, z1)), Vector((x0, y_int, z1)), Vector((x1, y_int, z1)),
               (0, 0, -1))
        _jamba(b, Vector((x0, y_ext, z0)), Vector((x0, y_ext, z1)), Vector((x0, y_int, z0)), Vector((x0, y_int, z1)),
               (1, 0, 0))
        _jamba(b, Vector((x1, y_ext, z0)), Vector((x1, y_ext, z1)), Vector((x1, y_int, z0)), Vector((x1, y_int, z1)),
               (-1, 0, 0))

    hueco_frontal(VF[0], VF[1], VZ0, VZ1, Y0, YI0)
    for x_ext, x_int, s in ((X0, XI0, -1), (X1, XI1, 1)):
        y0, y1 = VL
        _jamba(b, Vector((x_ext, y0, VZ0)), Vector((x_ext, y1, VZ0)), Vector((x_int, y0, VZ0)),
               Vector((x_int, y1, VZ0)), (0, 0, 1), "alfeizar_int")
        _jamba(b, Vector((x_ext, y0, VZ1)), Vector((x_ext, y1, VZ1)), Vector((x_int, y0, VZ1)),
               Vector((x_int, y1, VZ1)), (0, 0, -1))
        _jamba(b, Vector((x_ext, y0, VZ0)), Vector((x_ext, y0, VZ1)), Vector((x_int, y0, VZ0)),
               Vector((x_int, y0, VZ1)), (0, 1, 0))
        _jamba(b, Vector((x_ext, y1, VZ0)), Vector((x_ext, y1, VZ1)), Vector((x_int, y1, VZ0)),
               Vector((x_int, y1, VZ1)), (0, -1, 0))
    py0, py1 = PUERTA_Y
    _jamba(b, Vector((X1, py0, SUELO)), Vector((X1, py0, PUERTA_Z1)), Vector((XI1, py0, SUELO)),
           Vector((XI1, py0, PUERTA_Z1)), (0, 1, 0))
    _jamba(b, Vector((X1, py1, SUELO)), Vector((X1, py1, PUERTA_Z1)), Vector((XI1, py1, SUELO)),
           Vector((XI1, py1, PUERTA_Z1)), (0, -1, 0))
    _jamba(b, Vector((X1, py0, PUERTA_Z1)), Vector((X1, py1, PUERTA_Z1)), Vector((XI1, py0, PUERTA_Z1)),
           Vector((XI1, py1, PUERTA_Z1)), (0, 0, -1))

    # ---- pretil: cara de dentro y canto de arriba (debajo de la albardilla) -----------------------------
    esq = [(PX0, PY0), (PX1, PY0), (PX1, PY1), (PX0, PY1)]
    normales = [(0, 1, 0), (-1, 0, 0), (0, -1, 0), (1, 0, 0)]
    for i in range(4):
        (xa, ya), (xb, yb) = esq[i], esq[(i + 1) % 4]
        b.poligono([Vector((xa, ya, CUBIERTA)), Vector((xb, yb, CUBIERTA)), Vector((xb, yb, PRETIL)),
                    Vector((xa, ya, PRETIL))], "pared", normales[i])
    b.cara_con_huecos([Vector((X0, Y0, PRETIL)), Vector((X1, Y0, PRETIL)), Vector((X1, Y1, PRETIL)),
                       Vector((X0, Y1, PRETIL))],
                      [[Vector((x, y, PRETIL)) for x, y in esq]], "pared", (0, 0, 1), oculta=True)

    # ---- montantes del muro de atrás (malla baja: dan silueta de blindaje) ---------------------------------
    for x in (-1.45, 1.45):
        caja_plano(b, FONDO, -x - 0.07, -x + 0.07, SUELO + 0.45, PRETIL - 0.08, 0.0, 0.05, "pared", sin=("+y",))
    # ---- detalles de la malla alta: juntas de paneles, costillas y tornillos ---------------------------------
    _paneles_alta(p)
    P["pared_bajo"] = SUELO
    return p


def _paneles_alta(p):
    """Juntas entre paneles (surcos), costilla horizontal y tornillos de los paneles (solo para hornear)."""
    a = p.alta
    rnd = random.Random(5)

    def junta_v(pl, u, v0, v1):
        caja_plano(a, pl, u - 0.018, u + 0.018, v0, v1, -0.006, 0.004, "junta", sin=("+y",))

    def junta_h(pl, u0, u1, v):
        caja_plano(a, pl, u0, u1, v - 0.018, v + 0.018, -0.006, 0.004, "junta", sin=("+y",))

    def tornillos(pl, u0, u1, v, paso=0.42):
        n = max(2, int((u1 - u0) / paso) + 1)
        for k in range(n):
            u = u0 + (u1 - u0) * k / (n - 1)
            a.cupula(pl.p(u, v, 0.0), pl.n, 0.03, "tornilleria", alto=0.016, lados=10)

    # Fachada: paneles bajo y sobre el ventanal.
    for u in (-1.4, 1.4):
        junta_v(FRENTE, u, SUELO + 0.42, VZ0 - 0.1)
        junta_v(FRENTE, u, VZ1 + 0.1, PRETIL - 0.02)
    for pl, ancho in ((FONDO, 2.8), (IZQ, 3.0), (DER, 3.0)):
        pass
    # Muro de atrás: 4 paneles verticales.
    for u in (-0.7, 0.7):
        junta_v(FONDO, u, SUELO + 0.42, PRETIL - 0.02)
    # Laterales.
    for pl in (IZQ, DER):
        sgn = 1 if pl is DER else -1
        for y in (-1.4, 1.5):
            if pl is DER and PUERTA_Y[0] - 0.2 < y < PUERTA_Y[1] + 0.2:
                continue
            u = y * sgn
            junta_v(pl, u, SUELO + 0.42, VZ0 - 0.1 if y < 0 else PRETIL - 0.02)
    # Costilla horizontal bajo la cubierta (todo alrededor) y otra a la altura del forjado.
    for pl, u0, u1 in ((FRENTE, X0, X1), (FONDO, -X1, -X0), (IZQ, -Y1, -Y0), (DER, Y0, Y1)):
        junta_h(pl, u0 + 0.05, u1 - 0.05, TECHO_INT + 0.2)
        tornillos(pl, u0 + 0.35, u1 - 0.35, TECHO_INT + 0.08)
        tornillos(pl, u0 + 0.35, u1 - 0.35, SUELO + 0.52, paso=0.55)
    # Tornillos a los lados de las juntas verticales.
    for pl, us in ((FRENTE, (-1.4, 1.4)), (FONDO, (-0.7, 0.7))):
        for u in us:
            for v in (0.95, 2.6, 4.7):
                if pl is FRENTE and VZ0 - 0.1 < v < VZ1 + 0.1:
                    continue
                for du in (-0.07, 0.07):
                    a.cupula(pl.p(u + du, v, 0.0), pl.n, 0.026, "tornilleria", alto=0.014, lados=8)
    # Franja reflectante: cinta pegada (malla alta) todo alrededor menos en la puerta.
    z0, z1 = CINTA_Z
    for pl, tramos in ((FRENTE, [(X0 + 0.34, X1 - 0.34)]), (FONDO, [(-X1 + 0.34, -X0 - 0.34)]),
                       (IZQ, [(-Y1 + 0.34, -Y0 - 0.34)]),
                       (DER, [(Y0 + 0.34, PUERTA_Y[0] - 0.16), (PUERTA_Y[1] + 0.16, Y1 - 0.34)])):
        for u0, u1 in tramos:
            caja_plano(a, pl, u0, u1, z0, z1, 0.0, 0.006, "cinta", sin=("+y",))
    _ = rnd


def zocalo():
    """Chapa galvanizada de protección al pie de los muros (las patadas y la lluvia)."""
    p = Pieza("zocalo", peso_uv=0.6)
    b = p.baja
    z1 = SUELO + 0.42
    e = 0.035
    py0, py1 = PUERTA_Y
    tramos = [(FRENTE, X0 - e, X1 + e), (FONDO, -X1 - e, -X0 + e), (IZQ, -Y1, -Y0), (DER, Y0, py0 - 0.15),
              (DER, py1 + 0.15, Y1)]
    for pl, u0, u1 in tramos:
        caja_plano(b, pl, u0, u1, SUELO, z1, 0.0, e, "galvanizado", sin=("+y", "-z"))
        for k in range(int((u1 - u0) / 0.5) + 1):
            u = u0 + 0.12 + k * 0.5
            if u < u1 - 0.08:
                p.alta.cupula(pl.p(u, z1 - 0.07, e), pl.n, 0.022, "tornilleria", alto=0.012, lados=8)
    return p


def angulares():
    """Angulares de acero en las cuatro esquinas, atornillados a los dos muros."""
    p = Pieza("angulares", peso_uv=0.8)
    b = p.baja
    ala, e = 0.34, 0.05
    z0, z1 = SUELO + 0.02, PRETIL
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        xc = X1 if sx > 0 else X0
        yc = Y1 if sy > 0 else Y0
        # Ala sobre el muro X (cara que mira a ±X) y ala sobre el muro Y (cara que mira a ±Y).
        b.caja_de((min(xc, xc + sx * e), min(yc + sy * e, yc - sy * (ala - e)), z0),
                  (max(xc, xc + sx * e), max(yc + sy * e, yc - sy * (ala - e)), z1), "acero_angular",
                  sin=("-z",))
        b.caja_de((min(xc - sx * (ala - e), xc), min(yc, yc + sy * e), z0),
                  (max(xc - sx * (ala - e), xc), max(yc, yc + sy * e), z1), "acero_angular", sin=("-z",))
        # Tornillos (malla alta), en las dos alas.
        for z in [z0 + 0.25 + k * 0.62 for k in range(9)]:
            if z > z1 - 0.1:
                break
            p.alta.cupula(Vector((xc + sx * e, yc - sy * (ala * 0.55), z)), (sx, 0, 0), 0.035, "tornilleria",
                          alto=0.02, lados=10)
            p.alta.cupula(Vector((xc - sx * (ala * 0.55), yc + sy * e, z)), (0, sy, 0), 0.035, "tornilleria",
                          alto=0.02, lados=10)
        # Cordón de soldadura en la arista (malla alta).
        _tira_alta(p, [Vector((xc + sx * e, yc + sy * e, z0)), Vector((xc + sx * e, yc + sy * e, z1))], 0.016,
                   "soldadura")
    return p


# ======================================================================================================
# Ventanal, alféizar, malla y cristal
# ======================================================================================================


def _marco_hueco(c, pl, u0, u1, v0, v1, ancho, saliente, mat, fondo):
    """Marco reforzado: pletina alrededor del hueco por fuera + perfil dentro del grueso del muro."""
    # Pletina exterior (4 tiras).
    caja_plano(c, pl, u0 - ancho, u1 + ancho, v1, v1 + ancho, 0.0, saliente, mat, sin=("+y",))
    caja_plano(c, pl, u0 - ancho, u1 + ancho, v0 - ancho, v0, 0.0, saliente, mat, sin=("+y",))
    caja_plano(c, pl, u0 - ancho, u0, v0, v1, 0.0, saliente, mat, sin=("+y", "+z", "-z"))
    caja_plano(c, pl, u1, u1 + ancho, v0, v1, 0.0, saliente, mat, sin=("+y", "+z", "-z"))
    # Perfil en el grueso (calzos del cristal): marco interior de 0,07.
    k = 0.07
    caja_plano(c, pl, u0, u1, v1 - k, v1, -fondo, 0.0, mat, sin=("+z",))
    caja_plano(c, pl, u0, u1, v0, v0 + k, -fondo, 0.0, mat, sin=("-z",))
    caja_plano(c, pl, u0, u0 + k, v0 + k, v1 - k, -fondo, 0.0, mat, sin=("-x", "+z", "-z"))
    caja_plano(c, pl, u1 - k, u1, v0 + k, v1 - k, -fondo, 0.0, mat, sin=("+x", "+z", "-z"))


def ventanal_marcos():
    p = Pieza("ventanal_marcos", peso_uv=1.0)
    b = p.baja
    prof = 0.17
    _marco_hueco(b, FRENTE, VF[0], VF[1], VZ0, VZ1, 0.12, 0.05, "marco", prof)
    _marco_hueco(b, IZQ, -VL[1], -VL[0], VZ0, VZ1, 0.12, 0.05, "marco", prof)
    _marco_hueco(b, DER, VL[0], VL[1], VZ0, VZ1, 0.12, 0.05, "marco", prof)
    # Parteluz del ventanal de la fachada.
    caja_plano(b, FRENTE, MULLION - 0.07, MULLION + 0.07, VZ0 + 0.07, VZ1 - 0.07, -prof, 0.03, "marco",
               sin=("+z", "-z"))
    # Junquillos de goma y tornillos de los marcos (malla alta).
    for pl, u0, u1 in ((FRENTE, VF[0], VF[1]), (IZQ, -VL[1], -VL[0]), (DER, VL[0], VL[1])):
        for v in (VZ0 - 0.06, VZ1 + 0.06):
            for k in range(7):
                u = u0 - 0.06 + (u1 - u0 + 0.12) * k / 6
                p.alta.cupula(pl.p(u, v, 0.05), pl.n, 0.026, "tornilleria", alto=0.014, lados=8)
        for u in (u0 - 0.06, u1 + 0.06):
            for k in range(1, 4):
                v = VZ0 + (VZ1 - VZ0) * k / 4
                p.alta.cupula(pl.p(u, v, 0.05), pl.n, 0.026, "tornilleria", alto=0.014, lados=8)
        # Burlete negro alrededor del cristal.
        g = 0.07
        caja_plano(p.alta, pl, u0 + g, u1 - g, VZ0 + g, VZ0 + g + 0.025, -0.12, -0.075, "goma", sin=("+y",))
        caja_plano(p.alta, pl, u0 + g, u1 - g, VZ1 - g - 0.025, VZ1 - g, -0.12, -0.075, "goma", sin=("+y",))
    return p


def ventanal_cristal():
    """Cristal de seguridad grueso (0,08): Glass en Studio. Cuatro hojas."""
    p = Pieza("ventanal_cristal", peso_uv=0.0)
    p.tipo = "vidrio"
    b = p.baja
    g = 0.07
    e = 0.08
    d = -0.13  # centro del cristal, dentro del grueso del muro
    for u0, u1 in ((VF[0] + g, MULLION - 0.07), (MULLION + 0.07, VF[1] - g)):
        caja_plano(b, FRENTE, u0, u1, VZ0 + g, VZ1 - g, d - e / 2, d + e / 2, "vidrio")
    caja_plano(b, IZQ, -VL[1] + g, -VL[0] - g, VZ0 + g, VZ1 - g, d - e / 2, d + e / 2, "vidrio")
    caja_plano(b, DER, VL[0] + g, VL[1] - g, VZ0 + g, VZ1 - g, d - e / 2, d + e / 2, "vidrio")
    return p


def ventanal_malla():
    """Malla de alambre dentro del cristal (vidrio armado): cintas finas de las dos caras, cuadrícula de 0,3."""
    p = Pieza("ventanal_malla", peso_uv=0.35)
    b = p.baja
    g = 0.07
    d = -0.13
    paso = 0.45
    w = 0.008

    def malla(pl, u0, u1, v0, v1):
        nu = max(1, round((u1 - u0) / paso))
        nv = max(1, round((v1 - v0) / paso))
        for k in range(1, nu):
            u = u0 + (u1 - u0) * k / nu
            caja_plano(b, pl, u - w, u + w, v0, v1, d - 0.006, d + 0.006, "alambre", sin=("-z", "+z", "-x", "+x"))
        for k in range(1, nv):
            v = v0 + (v1 - v0) * k / nv
            caja_plano(b, pl, u0, u1, v - w, v + w, d - 0.006, d + 0.006, "alambre", sin=("-x", "+x", "-z", "+z"))

    malla(FRENTE, VF[0] + g, MULLION - 0.07, VZ0 + g, VZ1 - g)
    malla(FRENTE, MULLION + 0.07, VF[1] - g, VZ0 + g, VZ1 - g)
    malla(IZQ, -VL[1] + g, -VL[0] - g, VZ0 + g, VZ1 - g)
    malla(DER, VL[0] + g, VL[1] - g, VZ0 + g, VZ1 - g)
    return p


def alfeizares():
    """Alféizar ancho bajo el ventanal (hace de repisa: ahí deja el guardia el café) y dos estrechos."""
    p = Pieza("alfeizares", peso_uv=0.8)
    b = p.baja
    z = VZ0 - 0.12
    # Fachada: repisa de chapa plegada con goterón.
    caja_plano(b, FRENTE, VF[0] - 0.16, VF[1] + 0.16, z - 0.07, z, 0.0, 0.42, "alfeizar", sin=("+y",))
    caja_plano(b, FRENTE, VF[0] - 0.16, VF[1] + 0.16, z - 0.15, z - 0.07, 0.37, 0.42, "alfeizar",
               sin=("+y", "+z"))
    # Escuadras debajo (3).
    for u in (VF[0] + 0.25, 0.0, VF[1] - 0.25):
        pts = [(0.0, 0.0), (0.33, 0.0), (0.0, -0.32)]
        p.baja.placa(pts, FRENTE.p(u - 0.02, z - 0.07, 0.0), FRENTE.n, FRENTE.v, FRENTE.u, 0.04, "acero_oscuro")
    for pl, u0, u1 in ((IZQ, -VL[1], -VL[0]), (DER, VL[0], VL[1])):
        caja_plano(b, pl, u0 - 0.16, u1 + 0.16, z - 0.05, z, 0.0, 0.2, "alfeizar", sin=("+y",))
    P["taza"] = FRENTE.p(1.55, z, 0.2)
    P["repisa_z"] = z
    return p


# ======================================================================================================
# Techo y albardilla
# ======================================================================================================


def techo():
    p = Pieza("techo", peso_uv=0.8)
    b = p.baja
    # Cubierta (membrana) con una pendiente mínima hacia la gárgola de atrás.
    b.poligono([Vector((PX0, PY0, CUBIERTA + 0.02)), Vector((PX1, PY0, CUBIERTA + 0.02)),
                Vector((PX1, PY1, CUBIERTA)), Vector((PX0, PY1, CUBIERTA))], "membrana", (0, 0, 1))
    # Techo de dentro.
    b.poligono([Vector((XI0, YI0, TECHO_INT)), Vector((XI1, YI0, TECHO_INT)), Vector((XI1, YI1, TECHO_INT)),
                Vector((XI0, YI1, TECHO_INT))], "techo_int", (0, 0, -1))
    # Media caña de la membrana contra el pretil y sumidero (malla alta).
    for (xa, ya), (xb, yb) in (((PX0, PY0), (PX1, PY0)), ((PX1, PY0), (PX1, PY1)), ((PX1, PY1), (PX0, PY1)),
                               ((PX0, PY1), (PX0, PY0))):
        _tira_alta(p, [Vector((xa, ya, CUBIERTA + 0.01)), Vector((xb, yb, CUBIERTA + 0.01))], 0.05, "membrana")
    p.alta.revolucion([(0.16, 0), (0.12, 0.02), (0.1, -0.02)], Vector((-1.6, PY1 - 0.2, CUBIERTA)), 12, "acero_oscuro",
                      tapa_ini=False)
    for k in range(8):  # parches de membrana soldados
        rnd = random.Random(k)
        x, y = rnd.uniform(PX0 + 0.4, PX1 - 0.4), rnd.uniform(PY0 + 0.4, PY1 - 0.4)
        p.alta.caja((x, y, CUBIERTA + 0.022), (rnd.uniform(0.3, 0.6), rnd.uniform(0.25, 0.5), 0.006), "membrana")
    # Gárgola (desagüe) que atraviesa el pretil de atrás.
    gx = -1.6
    b.caja_de((gx - 0.1, Y1 - 0.02, CUBIERTA - 0.02), (gx + 0.1, Y1 + 0.32, CUBIERTA + 0.07), "galvanizado",
              sin=("-y", "+y"))
    b.poligono([Vector((gx - 0.07, Y1 + 0.32, CUBIERTA + 0.01)), Vector((gx + 0.07, Y1 + 0.32, CUBIERTA + 0.01)),
                Vector((gx + 0.07, Y1 + 0.32, CUBIERTA + 0.06)), Vector((gx - 0.07, Y1 + 0.32, CUBIERTA + 0.06))],
               "negro_mate", (0, 1, 0))
    P["gargola"] = Vector((gx, Y1, CUBIERTA))
    return p


def albardilla():
    """Albardilla de acero sobre el pretil, con goterón por fuera."""
    p = Pieza("albardilla", peso_uv=0.7)
    b = p.baja
    vu = 0.05  # vuelo por fuera
    zb = PRETIL
    # Cuatro tramos: delante y detrás de esquina a esquina; los laterales entre medias.
    tramos = [((X0 - vu, Y0 - vu), (X1 + vu, PY0 + 0.03)), ((X0 - vu, PY1 - 0.03), (X1 + vu, Y1 + vu)),
              ((X0 - vu, PY0 + 0.03), (PX0 + 0.03, PY1 - 0.03)), ((PX1 - 0.03, PY0 + 0.03), (X1 + vu, PY1 - 0.03))]
    for (x0, y0), (x1, y1) in tramos:
        b.caja_de((x0, y0, zb), (x1, y1, ALB), "albardilla", ocultas=("-z",))
    # Goterón: faldón por fuera bajando 0,1.
    for pl, u0, u1 in ((FRENTE, X0 - vu, X1 + vu), (FONDO, -X1 - vu, -X0 + vu), (IZQ, -Y1 - vu, -Y0 + vu),
                       (DER, Y0 - vu, Y1 + vu)):
        caja_plano(b, pl, u0, u1, zb - 0.1, zb, vu - 0.02, vu, "albardilla", sin=("+z",))
        for k in range(1, 6):
            u = u0 + (u1 - u0) * k / 6
            p.alta.cupula(pl.p(u, zb - 0.05, vu), pl.n, 0.022, "tornilleria", alto=0.012, lados=8)
    return p


def letrero_frontal():
    """Letras «SEGURIDAD» reflectantes en el pretil de la fachada (se leen desde la calle)."""
    p = Pieza("letrero_frontal", peso_uv=1.6)
    b = p.baja
    v0, v1 = VZ1 + 0.28, PRETIL - 0.12
    caja_plano(b, FRENTE, -1.7, 1.7, v0, v1, 0.0, 0.03, "placa_azul", sin=("+y",))
    vc = (v0 + v1) / 2
    texto(p.alta, "SEGURIDAD", FRENTE.p(0, vc, 0.03), FRENTE.u, FRENTE.v, FRENTE.n, 0.46, 0.02, "letras",
          ancho_max=3.0)
    for u in (-1.6, 1.6):
        for v in (v0 + 0.08, v1 - 0.08):
            p.alta.cupula(FRENTE.p(u, v, 0.03), FRENTE.n, 0.028, "tornilleria", alto=0.014)
    return p


# ======================================================================================================
# Puerta (pieza animable) y su marco
# ======================================================================================================

PUERTA_E = 0.16               # grosor de la hoja
PUERTA_X_EXT = X1 - 0.03      # cara de fuera de la hoja (un poco metida en el marco)
BIS_Z = (0.8, 2.45, 4.1)      # tres bisagras (una más de lo normal)
BIS_EJE = Vector((X1 + 0.045, BISAGRA_Y - 0.02, 0.0))   # eje vertical de giro (por fuera, en el canto)
PLANO_PUERTA = Plano((PUERTA_X_EXT, 0, 0), (1, 0, 0))   # u = +y


def puerta():
    py0, py1 = PUERTA_Y
    y0, y1 = py0 + 0.02, py1 - 0.02
    z0, z1 = SUELO + 0.03, PUERTA_Z1 - 0.02
    p = Pieza("puerta", pivote=(BIS_EJE.x, BIS_EJE.y, SUELO), peso_uv=1.4)
    b = p.baja
    pl = PLANO_PUERTA
    xe, xi = PUERTA_X_EXT, PUERTA_X_EXT - PUERTA_E
    # Hoja: caja maciza.
    b.caja_de((xi, y0, z0), (xe, y1, z1), "puerta_acero", mats={"-x": "puerta_int"})
    # Bastidor de refuerzo por fuera (marco perimetral en relieve) y travesaño.
    m = 0.13
    caja_plano(b, pl, y0, y1, z1 - m, z1, 0.0, 0.035, "puerta_acero", sin=("+y",))
    caja_plano(b, pl, y0, y1, z0, z0 + m, 0.0, 0.035, "puerta_acero", sin=("+y",))
    caja_plano(b, pl, y0, y0 + m, z0 + m, z1 - m, 0.0, 0.035, "puerta_acero", sin=("+y", "+z", "-z"))
    caja_plano(b, pl, y1 - m, y1, z0 + m, z1 - m, 0.0, 0.035, "puerta_acero", sin=("+y", "+z", "-z"))
    caja_plano(b, pl, y0 + m, y1 - m, 2.95, 3.07, 0.0, 0.035, "puerta_acero", sin=("+y", "-x", "+x"))
    # Chapa de patada abajo (acero inoxidable, rayada por las botas).
    caja_plano(b, pl, y0 + m, y1 - m, z0 + m, z0 + m + 0.5, 0.0, 0.012, "inox", sin=("+y", "-x", "+x"))
    P["puerta_patada"] = pl.p((y0 + y1) / 2, z0 + 0.4, 0.0)
    # Franja reflectante también en la puerta (sigue la de la pared).
    caja_plano(p.alta, pl, y0 + 0.02, y1 - 0.02, CINTA_Z[0], CINTA_Z[1], 0.035, 0.041, "cinta", sin=("+y",))
    caja_plano(p.alta, pl, y0 + m, y1 - m, CINTA_Z[0], CINTA_Z[1], 0.0, 0.006, "cinta", sin=("+y",))
    # Paneles embutidos (malla alta): dos cuarterones con pliegue en diagonal (puerta blindada).
    for v0, v1 in ((z0 + m + 0.55, 2.9), (3.12, z1 - m - 0.05)):
        caja_plano(p.alta, pl, y0 + m + 0.08, y1 - m - 0.08, v0, v1, -0.004, 0.006, "puerta_acero", sin=("+y",))
        p.alta.tubo([pl.p(y0 + m + 0.1, v0 + 0.02, 0.006), pl.p(y1 - m - 0.1, v1 - 0.02, 0.006)], 0.012,
                    "puerta_acero", lados=4)
        p.alta.tubo([pl.p(y1 - m - 0.1, v0 + 0.02, 0.006), pl.p(y0 + m + 0.1, v1 - 0.02, 0.006)], 0.012,
                    "puerta_acero", lados=4)
    # Remaches del bastidor.
    for k in range(9):
        z = z0 + 0.07 + (z1 - z0 - 0.14) * k / 8
        for y in (y0 + 0.065, y1 - 0.065):
            p.alta.cupula(pl.p(y, z, 0.035), pl.n, 0.024, "tornilleria", alto=0.013)

    # ---- bisagras (parte de la hoja: pala y nudo del centro) -----------------------------------------
    for zb in BIS_Z:
        caja_plano(b, pl, y0 - 0.005, y0 + 0.34, zb - 0.16, zb + 0.16, 0.035, 0.065, "bisagra", sin=("+y",))
        b.cilindro(Vector((BIS_EJE.x, BIS_EJE.y, zb - 0.07)), (0, 0, 1), 0.06, 0.14, "bisagra", lados=8)
        b.caja_de((BIS_EJE.x - 0.03, BIS_EJE.y, zb - 0.07), (xe + 0.065, y0 + 0.02, zb + 0.07), "bisagra",
                  sin=("+x", "-x"))
        for dy in (0.12, 0.26):
            for dz in (-0.09, 0.09):
                tornillo(p, pl.p(y0 + dy, zb + dz, 0.065), pl.n, 0.028, "tornilleria", en_baja=False)
        P.setdefault("bisagras", []).append(Vector((BIS_EJE.x, BIS_EJE.y, zb)))

    # ---- cerradura: teclado, manilla y cierre de varillas -------------------------------------------------
    yc = y1 - 0.3  # lado de la cerradura (canto de atrás)
    # Teclado numérico.
    tz = 3.32
    caja_plano(b, pl, yc - 0.15, yc + 0.15, tz - 0.22, tz + 0.22, 0.035, 0.1, "teclado_caja", sin=("+y",))
    caja_plano(b, pl, yc - 0.17, yc + 0.17, tz + 0.2, tz + 0.25, 0.035, 0.13, "teclado_caja", sin=("+y",))  # visera
    for i in range(12):
        c, f = i % 3, i // 3
        u = yc - 0.09 + c * 0.09
        v = tz + 0.1 - f * 0.075
        caja_plano(p.alta, pl, u - 0.035, u + 0.035, v - 0.028, v + 0.028, 0.1, 0.118, "tecla", sin=("+y",))
    caja_plano(p.alta, pl, yc - 0.11, yc + 0.11, tz - 0.205, tz - 0.165, 0.1, 0.104, "led", sin=("+y",))
    P["teclado"] = dict(origen=pl.p(yc - 0.135, tz - 0.1726, 0.0), u=pl.u, v=pl.v, ancho=0.27, alto=0.321)
    # Escudo y manilla.
    hz = 2.42
    caja_plano(b, pl, yc - 0.07, yc + 0.07, hz - 0.3, hz + 0.12, 0.035, 0.06, "acero_pulido", sin=("+y",))
    b.cilindro(pl.p(yc, hz, 0.06), pl.n, 0.045, 0.05, "acero_pulido", lados=10)
    b.tubo([pl.p(yc, hz, 0.11), pl.p(yc, hz, 0.17), pl.p(yc - 0.36, hz - 0.02, 0.18)], 0.026, "acero_pulido",
           lados=6, radio_curva=0.05, pasos_curva=2)
    b.cilindro(pl.p(yc, hz - 0.2, 0.06), pl.n, 0.03, 0.025, "laton", lados=10)  # bombín
    p.alta.caja(pl.p(yc, hz - 0.2, 0.087), (0.006, 0.006, 0.03), "negro_mate", giro=pl.giro)
    P["manija"] = pl.p(yc - 0.2, hz, 0.18)
    # Cierre de varillas (se ve el mecanismo por fuera): caja central, varillas con guías y pestillos.
    caja_plano(b, pl, yc - 0.06, yc + 0.06, 2.62, 2.92, 0.035, 0.085, "acero_oscuro", sin=("+y",))
    for zv0, zv1 in ((2.92, z1 - 0.02), (z0 + 0.03, 2.12)):
        b.cilindro(pl.p(yc, zv0, 0.065), (0, 0, 1), 0.017, zv1 - zv0, "acero_pulido", lados=6, tapa_ini=False)
        for zg in (zv0 + 0.35, (zv0 + zv1) / 2, zv1 - 0.28):
            caja_plano(b, pl, yc - 0.045, yc + 0.045, zg - 0.04, zg + 0.04, 0.035, 0.09, "acero_oscuro", sin=("+y",))
    caja_plano(b, pl, yc - 0.05, yc + 0.05, z1 - 0.07, z1, 0.035, 0.08, "acero_oscuro", sin=("+y",))  # pestillo
    caja_plano(b, pl, yc - 0.05, yc + 0.05, z0, z0 + 0.07, 0.035, 0.08, "acero_oscuro", sin=("+y",))
    # Cartel «SEGURIDAD COLONIAL» con escudo.
    cu0, cu1, cv0, cv1 = y0 + 0.2, y1 - 0.2, 3.62, 4.22
    caja_plano(b, pl, cu0, cu1, cv0, cv1, 0.035, 0.06, "placa_azul", sin=("+y",))
    ucen = (cu0 + cu1) / 2 + 0.16
    texto(p.alta, "SEGURIDAD", pl.p(ucen, 4.02, 0.06), pl.u, pl.v, pl.n, 0.13, 0.008, "letras", ancho_max=1.05)
    texto(p.alta, "COLONIAL", pl.p(ucen, 3.8, 0.06), pl.u, pl.v, pl.n, 0.13, 0.008, "letras_oro", ancho_max=1.05)
    # Escudo con estrella.
    us, vs = cu0 + 0.2, (cv0 + cv1) / 2
    esc = [(-0.13, 0.2), (0.13, 0.2), (0.13, 0.0), (0.0, -0.21), (-0.13, 0.0)]
    p.alta.placa([(us + a, vs + c) for a, c in esc], pl.p(0, 0, 0.06), pl.u, pl.v, pl.n, 0.01, "letras_oro")
    est = []
    for k in range(10):
        a = math.pi / 2 + k * math.pi / 5
        r = 0.085 if k % 2 == 0 else 0.035
        est.append((us + math.cos(a) * r, vs + 0.02 + math.sin(a) * r))
    p.alta.placa(est, pl.p(0, 0, 0.07), pl.u, pl.v, pl.n, 0.008, "placa_azul")
    for u in (cu0 + 0.04, cu1 - 0.04):
        for v in (cv0 + 0.04, cv1 - 0.04):
            p.alta.cupula(pl.p(u, v, 0.06), pl.n, 0.018, "acero_pulido", alto=0.01)
    P["pegatina"] = dict(origen=pl.p((y0 + y1) / 2 - 0.4, 3.13, 0.035), u=pl.u, v=pl.v, ancho=0.8, alto=0.325)
    # Mirilla gran angular.
    b.cilindro(pl.p((y0 + y1) / 2, 3.42, 0.035), pl.n, 0.035, 0.03, "laton", lados=10)
    p.alta.cilindro(pl.p((y0 + y1) / 2, 3.42, 0.062), pl.n, 0.018, 0.006, "lente", lados=12)

    # ---- por dentro: barra antipánico con sus dos cajas ------------------------------------------------
    pi = Plano((xi, 0, 0), (-1, 0, 0))   # u = -y
    zb = 2.6
    caja_plano(b, pi, -(y1 - 0.08), -(y1 - 0.34), zb - 0.1, zb + 0.1, 0.0, 0.12, "acero_oscuro", sin=("+y",))
    caja_plano(b, pi, -(y0 + 0.34), -(y0 + 0.12), zb - 0.08, zb + 0.08, 0.0, 0.1, "acero_oscuro", sin=("+y",))
    b.cilindro(Vector((xi - 0.09, y0 + 0.34, zb)), (0, 1, 0), 0.04, (y1 - 0.34) - (y0 + 0.34), "barra_roja",
               lados=8)
    b.cilindro(Vector((xi, (y0 + y1) / 2, 4.1)), (-1, 0, 0), 0.03, 0.05, "acero_oscuro", lados=8)
    P["puerta_y"] = (y0, y1)
    return p


def marco_puerta():
    """Marco de acero de la puerta, umbral, la otra pala de las bisagras y el cierrapuertas."""
    py0, py1 = PUERTA_Y
    p = Pieza("marco_puerta", peso_uv=1.0)
    b = p.baja
    pl = DER
    a, s = 0.14, 0.06
    caja_plano(b, pl, py0 - a, py1 + a, PUERTA_Z1, PUERTA_Z1 + a, 0.0, s, "marco", sin=("+y",))
    caja_plano(b, pl, py0 - a, py0, SUELO, PUERTA_Z1, 0.0, s, "marco", sin=("+y", "+z"))
    caja_plano(b, pl, py1, py1 + a, SUELO, PUERTA_Z1, 0.0, s, "marco", sin=("+y", "+z"))
    # Tope de la hoja dentro del hueco y umbral.
    caja_plano(b, pl, py0, py1, PUERTA_Z1 - 0.05, PUERTA_Z1, -0.25, -0.19, "marco", sin=("+z",))
    b.caja_de((X1 - MURO, py0, SUELO), (X1 + 0.12, py1, SUELO + 0.035), "inox", sin=("-z",))
    for k in range(6):
        p.alta.caja((X1 - 0.1, py0 + 0.15 + k * 0.32, SUELO + 0.036), (0.36, 0.03, 0.004), "goma")
    # Bisagras: pala en el marco y dos nudos (arriba y abajo del de la hoja) con el pasador.
    for zb in BIS_Z:
        caja_plano(b, pl, py0 - 0.13, py0 - 0.005, zb - 0.16, zb + 0.16, s, s + 0.025, "bisagra", sin=("+y",))
        for z0 in (zb - 0.21, zb + 0.07):
            b.cilindro(Vector((BIS_EJE.x, BIS_EJE.y, z0)), (0, 0, 1), 0.06, 0.14, "bisagra", lados=8)
        b.cilindro(Vector((BIS_EJE.x, BIS_EJE.y, zb + 0.21)), (0, 0, 1), 0.035, 0.03, "acero_pulido", lados=6)
        b.caja_de((X1 + s, py0 - 0.06, zb - 0.21), (BIS_EJE.x, BIS_EJE.y + 0.02, zb + 0.21), "bisagra",
                  sin=("-x", "+x", "-z", "+z"))
        for dz in (-0.11, 0.11):
            tornillo(p, pl.p(py0 - 0.07, zb + dz, s + 0.025), pl.n, 0.026, "tornilleria", en_baja=False)
        # Engrasador.
        p.alta.cilindro(Vector((BIS_EJE.x + 0.055, BIS_EJE.y, zb + 0.13)), (1, 0, 0), 0.012, 0.03, "laton", lados=6)
    # Cierrapuertas hidráulico en el dintel (cuerpo en el marco, brazo hasta la hoja).
    cz = PUERTA_Z1 + 0.07
    caja_plano(b, pl, py0 + 0.1, py0 + 0.62, cz - 0.08, cz + 0.08, s, s + 0.12, "acero_oscuro", sin=("+y",))
    b.cilindro(pl.p(py0 + 0.55, cz, s + 0.12), pl.n, 0.03, 0.03, "acero_pulido", lados=8)
    b.tubo([pl.p(py0 + 0.55, cz, s + 0.15), pl.p(py0 + 0.9, cz - 0.05, s + 0.15),
            pl.p(py0 + 1.12, cz - 0.11, 0.02)], 0.022, "acero_oscuro", lados=6)
    # Sellado de silicona entre marco y muro (malla alta).
    for v in (SUELO + 0.02, PUERTA_Z1 + a):
        pass
    return p


# ======================================================================================================
# Equipo del techo: foco, sirena, baliza, antena con radio, panel solar, bandera
# ======================================================================================================


def _rot_foco():
    return Matrix.Rotation(math.radians(FOCO_YAW), 3, "Z")


def foco_base():
    """Base motorizada del foco: placa con 4 pernos, carcasa del motor con aletas y cables al pretil."""
    p = Pieza("foco_base", peso_uv=1.1)
    b = p.baja
    c = FOCO
    b.caja_de(c + Vector((-0.42, -0.42, 0.0)), c + Vector((0.42, 0.42, 0.06)), "acero_oscuro", sin=("-z",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            perno_hex(p, c + Vector((sx * 0.33, sy * 0.33, 0.06)), (0, 0, 1), 0.04, "tornilleria")
    b.revolucion([(0.33, 0.06), (0.33, 0.3), (0.26, 0.36)], c, 12, "foco_carcasa", tapa_ini=False)
    for k in range(16):  # aletas de refrigeración (malla alta)
        a = k * math.tau / 16
        d = Vector((math.cos(a), math.sin(a), 0))
        p.alta.caja(c + d * 0.335 + Vector((0, 0, 0.19)), (0.03, 0.025, 0.2), "foco_carcasa",
                    giro=Matrix.Rotation(a, 3, "Z"))
    # Caja de bornas y cables (dos tubos flexibles hasta el pretil de la izquierda).
    b.caja_de(c + Vector((-0.5, -0.12, 0.06)), c + Vector((-0.3, 0.12, 0.26)), "acero_oscuro", sin=("-z",))
    for dy, r in ((-0.05, 0.03), (0.05, 0.025)):
        b.tubo([c + Vector((-0.5, dy, 0.14)), c + Vector((-0.75, dy, 0.08)), c + Vector((-0.95, dy, 0.04)),
                Vector((PX0 + 0.05, c.y + dy * 3 + 0.1, CUBIERTA + 0.04)),
                Vector((PX0 + 0.02, c.y + dy * 3 + 0.1, CUBIERTA + 0.3))], r, "cable", lados=4, radio_curva=0.15,
               pasos_curva=1)
    P["foco_base"] = c
    return p


def _cabezal_geo(b, alta, solo_lente=False):
    c = FOCO + Vector((0, 0, 0.36))
    R = _rot_foco()
    eje_tilt = R @ Vector((1, 0, 0))
    dirf = R @ (Matrix.Rotation(math.radians(FOCO_TILT), 3, "X") @ Vector((0, -1, 0)))
    centro = c + Vector((0, 0, 0.52))
    largo = 0.72
    r = 0.27
    trasera = centro - dirf * (largo * 0.45)
    frente = centro + dirf * (largo * 0.55)
    if solo_lente:
        b.cilindro(frente - dirf * 0.02, dirf, r - 0.035, 0.05, "neon", lados=16)
        return
    # Plato giratorio y horquilla.
    b.revolucion([(0.3, 0.0), (0.3, 0.06), (0.24, 0.08)], c, 16, "acero_oscuro", tapa_ini=False)
    b.caja(c + Vector((0, 0, 0.12)), (0.86, 0.22, 0.08), "foco_carcasa", giro=R)
    for s in (-1, 1):
        brazo = c + eje_tilt * (s * 0.4)
        b.caja(brazo + Vector((0, 0, 0.35)), (0.06, 0.2, 0.62), "foco_carcasa", giro=R)
        # Volante de ajuste de la inclinación.
        b.cilindro(centro + eje_tilt * (s * 0.43), eje_tilt * s, 0.09, 0.04, "acero_oscuro", lados=10)
        b.cilindro(centro + eje_tilt * (s * 0.47), eje_tilt * s, 0.035, 0.07, "acero_pulido", lados=6)
    # Cuerpo del foco: tambor con aros, tapa trasera con aletas y aro delantero grueso.
    q = dirf.to_track_quat("Z", "Y").to_matrix()

    def P_(x, y, z):
        return trasera + q @ Vector((x, y, z))

    perfil = [(0.0, 0.0), (r * 0.75, 0.0), (r, 0.1), (r, largo - 0.12), (r + 0.035, largo - 0.1),
              (r + 0.035, largo - 0.01), (r - 0.03, largo - 0.01), (r - 0.03, largo - 0.05)]
    b.revolucion(perfil, trasera, 16, "foco_carcasa", eje=dirf, tapa_ini=False, tapa_fin=True, mat_fin="reflector")
    for k in range(5):  # aletas traseras (malla alta)
        alta.revolucion([(r * 0.3, 0.02 + k * 0.025), (r * 0.95, 0.02 + k * 0.025), (r * 0.95, 0.032 + k * 0.025),
                         (r * 0.3, 0.032 + k * 0.025)], trasera, 24, "foco_carcasa", eje=dirf, tapa_ini=False,
                        tapa_fin=False)
    # Asa de arriba.
    arriba = q @ Vector((0, 1, 0))
    if arriba.z < 0:
        arriba = -arriba
    b.tubo([P_(0, 0, 0.2) + arriba * r, P_(0, 0, 0.2) + arriba * (r + 0.12), P_(0, 0, 0.5) + arriba * (r + 0.12),
            P_(0, 0, 0.5) + arriba * r], 0.02, "acero_pulido", lados=4, radio_curva=0.04, pasos_curva=2)
    # Rejilla de protección delante (dos barras en cruz).
    for ang in (45, -45):
        d = q @ Vector((math.cos(math.radians(ang)), math.sin(math.radians(ang)), 0))
        b.cilindro(frente + dirf * 0.02 - d * (r - 0.01), d, 0.012, 2 * (r - 0.01), "acero_oscuro", lados=5)
    # Cable en espiral del cabezal a la base.
    b.tubo([P_(0, 0, 0.1) - arriba * r, c + Vector((0, 0, 0.3)) - dirf * 0.2, c + Vector((0, 0, 0.14)) - dirf * 0.1],
           0.022, "cable", lados=4, radio_curva=0.1, pasos_curva=1)
    P["foco_frente"] = frente
    P["foco_dir"] = dirf


def foco_cabezal():
    """Cabezal giratorio del foco (gira sobre el eje vertical de la base)."""
    p = Pieza("foco_cabezal", pivote=FOCO + Vector((0, 0, 0.36)), peso_uv=1.2)
    _cabezal_geo(p.baja, p.alta)
    return p


def foco_lente():
    """Lente del foco: cristal grueso que brilla (Neon cian #3DF2FF). Va soldada al cabezal."""
    p = Pieza("foco_lente_neon", pivote=FOCO + Vector((0, 0, 0.36)), peso_uv=0.0)
    p.tipo = "neon"
    _cabezal_geo(p.baja, p.alta, solo_lente=True)
    return p


def sirena():
    """Sirena de alarma en la esquina delantera izquierda: bocina de chapa roja sobre un soporte."""
    p = Pieza("sirena", peso_uv=1.0)
    b = p.baja
    base = Vector((X0 + 0.02, Y0 + 0.02, ALB))
    # Brida abrazando la esquina de la albardilla y mástil corto.
    b.caja_de(base + Vector((-0.06, -0.06, 0.0)), base + Vector((0.3, 0.3, 0.05)), "acero_oscuro", sin=("-z",))
    for d in (Vector((0.06, 0.22, 0.05)), Vector((0.22, 0.06, 0.05)), Vector((0.22, 0.22, 0.05))):
        perno_hex(p, base + d, (0, 0, 1), 0.025, "tornilleria", arandela=False)
    m = base + Vector((0.1, 0.1, 0.05))
    b.cilindro(m, (0, 0, 1), 0.045, 0.32, "acero_oscuro", lados=8, tapa_ini=False)
    # Cuerpo del motor y bocina mirando hacia fuera (diagonal) y un poco abajo.
    d = Vector((-1, -1, -0.25)).normalized()
    centro = m + Vector((0, 0, 0.42))
    b.caja(centro, (0.12, 0.12, 0.14), "acero_oscuro")
    cuerpo = centro - d * 0.12
    b.revolucion([(0.0, 0.0), (0.11, 0.0), (0.15, 0.04), (0.15, 0.22), (0.12, 0.26), (0.0, 0.26)], cuerpo, 10,
                 "pintura_roja", eje=d, tapa_ini=False, tapa_fin=False)
    boca = cuerpo + d * 0.26
    # Bocina con grosor: por fuera se abre y por dentro vuelve (perfil antihorario: normales hacia fuera).
    perfil = [(0.07, 0.0), (0.12, 0.18), (0.22, 0.38), (0.31, 0.5), (0.33, 0.52), (0.31, 0.53), (0.2, 0.42),
              (0.1, 0.22), (0.05, 0.04)]
    b.revolucion(perfil, boca, 12, "pintura_roja", eje=d, tapa_ini=False, tapa_fin=True, mat_fin="negro_mate")
    # Rejilla del fondo de la bocina y tornillos del aro (malla alta).
    p.alta.cilindro(boca + d * 0.03, d, 0.06, 0.01, "rejilla", lados=12)
    for k in range(8):
        a = k * math.tau / 8
        u, v = base_de(d)
        p.alta.cupula(boca + d * 0.0 + (u * math.cos(a) + v * math.sin(a)) * 0.135, -d, 0.012, "tornilleria",
                      alto=0.008)
    # Cable hasta la albardilla.
    b.tubo([cuerpo + Vector((0.08, 0.08, -0.08)), m + Vector((0.08, 0.06, 0.15)), base + Vector((0.28, 0.12, 0.06))],
           0.018, "cable", lados=4, radio_curva=0.06, pasos_curva=1)
    P["sirena"] = boca
    return p


def baliza():
    """Baliza giratoria en la esquina delantera derecha: base metálica con la lámpara y el espejo dentro."""
    p = Pieza("baliza", peso_uv=1.0)
    b = p.baja
    c = Vector((X1 - 0.17, Y0 + 0.17, ALB))
    b.revolucion([(0.2, 0.0), (0.2, 0.04), (0.17, 0.05), (0.17, 0.15), (0.15, 0.16), (0.0, 0.16)], c, 12,
                 "acero_oscuro", tapa_ini=False)
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        perno_hex(p, c + Vector((math.cos(a) * 0.165, math.sin(a) * 0.165, 0.04)), (0, 0, 1), 0.016, "tornilleria",
                  arandela=False)
    # Junta de goma y, dentro, la lámpara y el espejo giratorio.
    b.revolucion([(0.152, 0.16), (0.152, 0.18), (0.0, 0.18)], c, 14, "goma", tapa_ini=False)
    b.cilindro(c + Vector((0, 0, 0.18)), (0, 0, 1), 0.03, 0.12, "acero_oscuro", lados=8, tapa_ini=False)
    b.revolucion([(0.045, 0.0), (0.05, 0.05), (0.0, 0.1)], c + Vector((0, 0, 0.28)), 10, "bombilla",
                 tapa_ini=False)
    esp = [Vector((0.02, -0.11, 0.2)), Vector((0.02, 0.0, 0.2)), Vector((0.02, 0.0, 0.42)), Vector((0.02, -0.11, 0.42))]
    b.poligono([c + Vector((v.x, v.y, v.z)) for v in esp], "espejo", (1, 0, 0))
    b.poligono([c + Vector((v.x - 0.01, v.y, v.z)) for v in esp], "acero_oscuro", (-1, 0, 0))
    P["baliza"] = c
    return p


def baliza_cristal():
    """Domo de cristal naranja de la baliza (Glass naranja en Studio)."""
    p = Pieza("baliza_cristal", peso_uv=0.0)
    p.tipo = "vidrio_naranja"
    c = Vector((X1 - 0.17, Y0 + 0.17, ALB))
    perfil = [(0.0, 0.18), (0.15, 0.18), (0.15, 0.38)]
    for k in range(1, 6):
        a = k * math.pi / 2 / 6
        perfil.append((0.15 * math.cos(a), 0.38 + 0.13 * math.sin(a)))
    perfil.append((0.0, 0.51))
    p.baja.revolucion(perfil, c, 12, "vidrio_naranja", tapa_ini=False, tapa_fin=False)
    # Estrías del cristal (malla alta, para nada: no se hornea).
    return p


def antena_radio():
    """Antena de radio: mástil con la espiral, radiales y la caja de la radio; cable por el muro hasta dentro."""
    p = Pieza("antena_radio", peso_uv=1.0)
    b = p.baja
    c = Vector((1.85, 2.25, CUBIERTA))
    # Placa y mástil.
    b.caja_de(c + Vector((-0.2, -0.2, 0.0)), c + Vector((0.2, 0.2, 0.05)), "galvanizado", sin=("-z",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            perno_hex(p, c + Vector((sx * 0.14, sy * 0.14, 0.05)), (0, 0, 1), 0.025, "tornilleria", arandela=False)
    b.cilindro(c + Vector((0, 0, 0.05)), (0, 0, 1), 0.06, 0.9, "galvanizado", lados=8, radio2=0.05, tapa_ini=False)
    b.cilindro(c + Vector((0, 0, 0.95)), (0, 0, 1), 0.075, 0.12, "plastico_negro", lados=8)  # conector
    b.cilindro(c + Vector((0, 0, 1.07)), (0, 0, 1), 0.03, 1.75, "antena", lados=6, radio2=0.018)
    b.revolucion([(0.03, 0.0), (0.045, 0.02), (0.0, 0.06)], c + Vector((0, 0, 2.82)), 8, "plastico_negro",
                 tapa_ini=False)
    # Radiales (3, inclinados hacia abajo).
    for k in range(3):
        a = k * math.tau / 3 + 0.4
        d = Vector((math.cos(a), math.sin(a), -0.55)).normalized()
        b.cilindro(c + Vector((0, 0, 1.0)), d, 0.012, 0.55, "antena", lados=4, tapa_ini=False)
    # Espiral (bobina de carga) alrededor del tramo de arriba.
    vueltas, pasos = 5.0, 36
    z0, z1, rr = 1.4, 2.45, 0.1
    pts = []
    for k in range(pasos + 1):
        f = k / pasos
        a = f * vueltas * math.tau
        pts.append(c + Vector((math.cos(a) * rr, math.sin(a) * rr, z0 + (z1 - z0) * f)))
    b.tubo(pts, 0.016, "cobre", lados=4)
    for zz in (z0 - 0.05, z1 + 0.05):  # abrazaderas de la espiral
        b.cilindro(c + Vector((0, 0, zz - 0.03)), (0, 0, 1), rr + 0.02, 0.06, "plastico_negro", lados=6)
    # Caja de la radio con disipador, asa y conectores.
    rc = Vector((0.95, 2.4, CUBIERTA))
    b.caja_de(rc + Vector((-0.32, -0.2, 0.0)), rc + Vector((0.32, 0.2, 0.42)), "radio_caja", sin=("-z",))
    b.caja_de(rc + Vector((-0.34, -0.22, 0.42)), rc + Vector((0.34, 0.22, 0.46)), "radio_caja")
    for k in range(9):  # aletas del disipador en la cara de delante (malla alta)
        x = -0.26 + k * 0.065
        p.alta.caja(rc + Vector((x, -0.21, 0.21)), (0.018, 0.03, 0.34), "radio_caja")
    b.tubo([rc + Vector((-0.2, -0.05, 0.46)), rc + Vector((-0.2, -0.05, 0.58)), rc + Vector((0.2, -0.05, 0.58)),
            rc + Vector((0.2, -0.05, 0.46))], 0.018, "plastico_negro", lados=4, radio_curva=0.05, pasos_curva=2)
    for dx in (0.2, 0.26):
        b.cilindro(rc + Vector((dx, 0.2, 0.2)), (0, 1, 0), 0.025, 0.05, "laton", lados=6)
    p.alta.caja(rc + Vector((-0.12, -0.205, 0.33)), (0.2, 0.012, 0.06), "etiqueta_radio")
    # Coaxial hasta la antena.
    b.tubo([rc + Vector((0.32, 0.0, 0.28)), rc + Vector((0.55, -0.1, 0.1)), c + Vector((-0.25, 0.0, 0.03)),
            c + Vector((-0.06, 0.0, 0.3)), c + Vector((-0.06, 0.0, 0.95))], 0.022, "cable", lados=4, radio_curva=0.12,
           pasos_curva=1)
    # Cable de la radio: sube por el pretil, pasa por encima de la albardilla y baja por el muro de atrás hasta
    # el pasamuros (y dentro llega a la radio base de la estantería).
    cx = 0.7
    ruta = [rc + Vector((-0.26, 0.2, 0.3)), Vector((cx, PY1 - 0.04, CUBIERTA + 0.35)),
            Vector((cx, PY1 - 0.04, ALB + 0.04)), Vector((cx, Y1 + 0.1, ALB + 0.05)),
            Vector((cx, Y1 + 0.07, PRETIL - 0.2)), Vector((cx, Y1 + 0.05, 4.55))]
    b.tubo(ruta, 0.026, "cable", lados=4, radio_curva=0.1, pasos_curva=1, tapa_fin=False)
    # Grapas del cable por el muro y pasamuros.
    for zz in (5.4, 5.0):
        caja_plano(b, FONDO, -cx - 0.06, -cx + 0.06, zz - 0.025, zz + 0.025, 0.0, 0.085, "acero_oscuro", sin=("+y",))
    b.revolucion([(0.07, 0.0), (0.07, 0.04), (0.05, 0.08), (0.03, 0.09)], Vector((cx, Y1, 4.5)), 8, "goma",
                 eje=(0, 1, 0), tapa_ini=False)
    b.tubo([Vector((cx, Y1 + 0.05, 4.6)), Vector((cx, Y1 + 0.05, 4.53)), Vector((cx, Y1 + 0.02, 4.5))], 0.026, "cable",
           lados=6, radio_curva=0.03, pasos_curva=2, tapa_ini=False, tapa_fin=False)
    P["radio_caja"] = rc
    P["pasamuros_x"] = cx
    return p


def panel_solar():
    """Panel solar pequeño en bastidor inclinado (alimenta la radio)."""
    p = Pieza("panel_solar", peso_uv=1.1)
    b = p.baja
    c = Vector((1.05, 0.3, CUBIERTA))
    inc = math.radians(28)
    R = Matrix.Rotation(-inc, 3, "X")   # mira hacia -Y (delante) y arriba
    w, h, e = 1.5, 1.0, 0.05
    centro = c + Vector((0, 0, 0.5))
    b.caja(centro, (w, h, e), "aluminio", giro=R, mats={"+z": "celda_solar"})
    # Marco (malla baja: canto en relieve) y bastidor con dos patas traseras.
    for s in (-1, 1):
        b.caja(centro + R @ Vector((s * (w / 2 - 0.02), 0, 0.03)), (0.04, h, 0.03), "aluminio", giro=R, sin=("-z",))
        b.caja(centro + R @ Vector((0, s * (h / 2 - 0.02), 0.03)), (w - 0.08, 0.04, 0.03), "aluminio", giro=R,
               sin=("-z",))
    for sx in (-0.6, 0.6):
        pie_d = centro + R @ Vector((sx, -h / 2 + 0.1, -e / 2))
        pie_t = centro + R @ Vector((sx, h / 2 - 0.1, -e / 2))
        b.tubo([Vector((pie_d.x, pie_d.y, CUBIERTA + 0.02)), pie_d], 0.025, "aluminio", lados=4)
        b.tubo([Vector((pie_t.x, pie_t.y, CUBIERTA + 0.02)), pie_t], 0.025, "aluminio", lados=4)
        b.caja_de(Vector((sx + c.x - 0.08, pie_d.y - 0.08, CUBIERTA)), Vector((sx + c.x + 0.08, pie_t.y + 0.08,
                                                                              CUBIERTA + 0.03)), "aluminio",
                  sin=("-z",))
    # Celdas: rejilla de 6 x 4 (malla alta, con las pistas plateadas).
    for i in range(6):
        for j in range(4):
            cc = centro + R @ Vector((-w / 2 + 0.1 + (w - 0.2) * (i + 0.5) / 6, -h / 2 + 0.09 + (h - 0.18) * (j + 0.5) / 4,
                                      e / 2 + 0.002))
            p.alta.caja(cc, ((w - 0.2) / 6 - 0.012, (h - 0.18) / 4 - 0.012, 0.004), "celda_solar", giro=R)
    # Cable hasta la radio.
    b.tubo([centro + R @ Vector((0.6, h / 2 - 0.1, -0.05)), Vector((1.4, 1.2, CUBIERTA + 0.05)),
            P.get("radio_caja", Vector((0.95, 2.4, CUBIERTA))) + Vector((0.3, -0.12, 0.08))], 0.018, "cable", lados=4,
           radio_curva=0.2, pasos_curva=1)
    return p


def _bandera_superficie(u, v):
    """Tela ondeando: u (0 en el mástil .. 1 en la punta), v (0 abajo .. 1 arriba) -> punto en studs."""
    L, H = 1.35, 0.85
    x0 = -2.0 + 0.06
    z0 = 7.05
    amp = 0.09 * u ** 0.8
    y = 2.3 + amp * math.sin(u * 7.0 - 0.6 + v * 0.8)
    caida = 0.06 * u * u  # la punta cae un poco
    return Vector((x0 + u * L, y, z0 + v * H - caida * (1 - v * 0.3)))


def bandera():
    """Mástil corto con la bandera de la colonia (tela con grosor, logo estrella en círculo)."""
    p = Pieza("bandera", peso_uv=1.6)
    b = p.baja
    m = Vector((-2.0, 2.3, CUBIERTA))
    b.revolucion([(0.12, 0.0), (0.12, 0.04), (0.06, 0.07), (0.0, 0.07)], m, 10, "galvanizado", tapa_ini=False)
    for k in range(4):
        a = k * math.tau / 4 + math.pi / 4
        perno_hex(p, m + Vector((math.cos(a) * 0.09, math.sin(a) * 0.09, 0.04)), (0, 0, 1), 0.016, "tornilleria",
                  arandela=False)
    b.cilindro(m + Vector((0, 0, 0.07)), (0, 0, 1), 0.045, 2.6, "galvanizado", lados=8, radio2=0.035, tapa_ini=False)
    b.revolucion([(0.0, 0.0), (0.05, 0.02), (0.075, 0.08), (0.05, 0.14), (0.0, 0.16)], m + Vector((0, 0, 2.67)), 8,
                 "laton", tapa_ini=False, tapa_fin=False)
    # Driza (cuerda) y cornamusa.
    b.tubo([m + Vector((0.05, -0.02, 2.62)), m + Vector((0.06, -0.03, 1.4)), m + Vector((0.07, -0.05, 0.85))], 0.009,
           "cuerda", lados=4)
    b.caja(m + Vector((0.05, -0.04, 0.85)), (0.03, 0.03, 0.14), "acero_oscuro")
    # Tela: rejilla ondulada con las dos caras y el canto (tiene grosor de verdad).
    nu, nv = 8, 4
    e = 0.012
    capas = {}
    for lado in (-1, 1):
        vs = [[b.v(_bandera_superficie(i / nu, j / nv) + Vector((0, lado * e / 2, 0))) for i in range(nu + 1)]
              for j in range(nv + 1)]
        for j in range(nv):
            for i in range(nu):
                quad = [vs[j][i], vs[j][i + 1], vs[j + 1][i + 1], vs[j + 1][i]]
                if lado > 0:
                    quad.reverse()  # la cara de +Y mira a +Y
                b.cara(quad, "tela_bandera", suave=True)
        capas[lado] = vs
    vf, vb = capas[-1], capas[1]
    # Canto (une las dos caras por el borde).
    borde = [(j, 0) for j in range(nv, -1, -1)] + [(0, i) for i in range(1, nu + 1)] + \
            [(j, nu) for j in range(1, nv + 1)] + [(nv, i) for i in range(nu - 1, 0, -1)]
    for k in range(len(borde)):
        (j0, i0), (j1, i1) = borde[k], borde[(k + 1) % len(borde)]
        b.cara([vf[j0][i0], vf[j1][i1], vb[j1][i1], vb[j0][i0]], "tela_bandera", suave=True)
    b.recalcular([f for f in b.bm.faces if f.material_index == b.indice("tela_bandera")])
    # Anillas que sujetan la tela al mástil.
    for v in (0.1, 0.9):
        q = _bandera_superficie(0, v)
        b.revolucion([(0.06, -0.015), (0.06, 0.015), (0.045, 0.015), (0.045, -0.015)],
                     Vector((m.x, m.y, q.z)), 6, "acero_oscuro", tapa_ini=False, tapa_fin=False)
    P["bandera"] = dict(origen=_bandera_superficie(0, 0) - Vector((0.03, 0, 0.08)), u=Vector((1, 0, 0)),
                        v=Vector((0, 0, 1)), ancho=1.45, alto=0.93)
    return p


# ======================================================================================================
# Cámaras de vigilancia
# ======================================================================================================


def _camara(p, pl, u, v, objetivo, nombre_punto):
    """Cámara tipo bala: placa en el muro, brazo, rótula y carcasa con visera, lente y prensaestopas."""
    b = p.baja
    base = pl.p(u, v, 0.0)
    # Placa con 4 tornillos.
    caja_plano(b, pl, u - 0.13, u + 0.13, v - 0.16, v + 0.16, 0.0, 0.04, "plastico_blanco", sin=("+y",))
    for du in (-0.09, 0.09):
        for dv in (-0.115, 0.115):
            tornillo(p, pl.p(u + du, v + dv, 0.04), pl.n, 0.018, "tornilleria", en_baja=False)
    # Brazo hacia fuera con un codo, y rótula.
    codo = base + pl.n * 0.3 + Vector((0, 0, 0.06))
    b.tubo([base + pl.n * 0.04, base + pl.n * 0.22, codo], 0.04, "plastico_blanco", lados=6, radio_curva=0.06,
           pasos_curva=2, tapa_ini=False)
    b.revolucion([(0.0, -0.06), (0.04, -0.05), (0.06, 0.0), (0.04, 0.05), (0.0, 0.06)], codo, 8, "acero_oscuro",
                 tapa_ini=False, tapa_fin=False)
    # Carcasa apuntando al objetivo.
    d = (Vector(objetivo) - codo).normalized()
    centro = codo + d * 0.05 + Vector((0, 0, 0.12))
    q = d.to_track_quat("Y", "Z").to_matrix()
    b.tubo([codo + Vector((0, 0, 0.05)), centro - Vector((0, 0, 0.07))], 0.03, "acero_oscuro", lados=6)
    trasera = centro - d * 0.24
    b.revolucion([(0.09, 0.0), (0.11, 0.03), (0.11, 0.42), (0.07, 0.44), (0.07, 0.42)],
                 trasera, 10, "plastico_blanco", eje=d, tapa_ini=False, tapa_fin=True, mat_fin="lente")
    b.cilindro(trasera + d * 0.38, d, 0.05, 0.04, "lente", lados=10)
    # Visera (chapa curvada encima).
    arriba = q @ Vector((0, 0, 1))
    lado = q @ Vector((1, 0, 0))
    vis = []
    for k in range(5):
        a = math.radians(-70 + k * 140 / 4)
        vis.append(lado * math.sin(a) * 0.135 + arriba * math.cos(a) * 0.135)
    anillo0 = [trasera + d * 0.03 + w for w in vis]
    anillo1 = [trasera + d * 0.52 + w for w in vis]
    vs0 = [b.v(x) for x in anillo0]
    vs1 = [b.v(x) for x in anillo1]
    vs0i = [b.v(x - (x - (trasera + d * 0.03)).normalized() * 0.015) for x in anillo0]
    vs1i = [b.v(x - (x - (trasera + d * 0.52)).normalized() * 0.015) for x in anillo1]
    caras = []
    for i in range(4):
        caras.append(b.cara([vs0[i], vs1[i], vs1[i + 1], vs0[i + 1]], "plastico_blanco"))
        caras.append(b.cara([vs0i[i + 1], vs1i[i + 1], vs1i[i], vs0i[i]], "plastico_blanco"))
        caras.append(b.cara([vs1[i], vs1i[i], vs1i[i + 1], vs1[i + 1]], "plastico_blanco"))
        caras.append(b.cara([vs0[i + 1], vs0i[i + 1], vs0i[i], vs0[i]], "plastico_blanco"))
    for i in (0, 4):
        caras.append(b.cara([vs0[i], vs0i[i], vs1i[i], vs1[i]], "plastico_blanco"))
    b.recalcular(caras)
    # LEDs infrarrojos alrededor de la lente y prensaestopas detrás (malla alta).
    for k in range(8):
        a = k * math.tau / 8
        p.alta.cupula(trasera + d * 0.44 + (lado * math.cos(a) + arriba * math.sin(a)) * 0.08, d, 0.01, "led_ir",
                      alto=0.006, lados=6)
    b.tubo([trasera + d * 0.02, trasera - d * 0.08, codo + Vector((0, 0, -0.04)) - d * 0.05,
            base + pl.n * 0.12 + Vector((0, 0, -0.06))], 0.014, "cable", lados=4, radio_curva=0.05, pasos_curva=1)
    P[nombre_punto] = trasera + d * 0.45


def camaras():
    p = Pieza("camaras", peso_uv=1.4)
    # Una vigila la barrera (en el muro +X, junto a la esquina delantera) y otra la calle (muro -X).
    _camara(p, DER, Y0 + 0.5, 4.95, Vector((5.2, -5.2, 0.8)), "camara_barrera")
    _camara(p, IZQ, -(Y0 + 0.5), 4.95, Vector((-5.0, -9.0, 0.5)), "camara_calle")
    return p


# ======================================================================================================
# Muro: tablón de avisos, extintor, papelera y la taza de café
# ======================================================================================================

TABLON = dict(u0=-2.65, u1=-0.4, v0=1.95, v1=3.75)   # en el muro -X (u = -y)


def tablon():
    p = Pieza("tablon", peso_uv=2.4)
    b = p.baja
    pl = IZQ
    u0, u1, v0, v1 = TABLON["u0"], TABLON["u1"], TABLON["v0"], TABLON["v1"]
    # Fondo de corcho y marco de aluminio.
    caja_plano(b, pl, u0, u1, v0, v1, 0.0, 0.05, "corcho", sin=("+y",))
    m = 0.07
    for a0, a1, c0, c1 in ((u0 - m, u1 + m, v1, v1 + m), (u0 - m, u1 + m, v0 - m, v0), (u0 - m, u0, v0, v1),
                           (u1, u1 + m, v0, v1)):
        caja_plano(b, pl, a0, a1, c0, c1, 0.0, 0.08, "aluminio", sin=("+y",))
    # Tejadillo contra la lluvia.
    caja_plano(b, pl, u0 - 0.15, u1 + 0.15, v1 + m, v1 + m + 0.04, 0.0, 0.26, "galvanizado", sin=("+y",))
    for u in (u0 + 0.1, u1 - 0.1):
        p.baja.placa([(0.0, 0.0), (0.22, 0.0), (0.0, -0.2)], pl.p(u - 0.015, v1 + m, 0.0), pl.n, pl.v, pl.u, 0.03,
                     "galvanizado")
    # Papeles: (calco, u0, v0, ancho, alto, giro en grados).
    rnd = random.Random(3)
    papeles = [("se_busca_1", u0 + 0.12, v0 + 0.85, 0.56, 0.8, -3.0), ("se_busca_2", u0 + 0.78, v0 + 0.82, 0.56, 0.8, 2.0),
               ("se_busca_3", u0 + 1.42, v0 + 0.88, 0.5, 0.72, -1.5), ("horario", u0 + 0.14, v0 + 0.08, 0.6, 0.76, 1.0),
               ("toque_queda", u0 + 0.86, v0 + 0.16, 0.68, 0.49, -2.5)]
    P["papeles"] = []
    for k, (calco, pu, pv, w, h, g) in enumerate(papeles):
        ca, sa = math.cos(math.radians(g)), math.sin(math.radians(g))
        cu, cv = pu + w / 2, pv + h / 2
        esquinas = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        pts = [(cu + x * ca - y * sa, cv + x * sa + y * ca) for x, y in esquinas]
        d0 = 0.05 + 0.004 * k
        # El papel: lámina de 0,006 con la esquina de abajo un poco levantada.
        caras = b.placa(pts, pl.p(0, 0, d0), pl.u, pl.v, pl.n, 0.006, "papel_" + calco)
        esq = caras[0].verts[0]
        # Chinchetas de colores (cabeza en la malla baja: se ven desde lejos).
        for x, y in ((-w / 2 + 0.05, h / 2 - 0.05), (w / 2 - 0.05, h / 2 - 0.05)):
            uu, vv = cu + x * ca - y * sa, cv + x * sa + y * ca
            b.revolucion([(0.03, 0.0), (0.03, 0.02), (0.0, 0.035)],
                         pl.p(uu, vv, d0 + 0.006), 5, "chincheta", eje=pl.n, tapa_ini=False, tapa_fin=False)
        _ = esq
        # El calco sigue al papel girado: guardamos su sistema de referencia.
        ou = pl.u * ca + pl.v * sa
        ov = -pl.u * sa + pl.v * ca
        P["papeles"].append(dict(calco=calco, origen=pl.p(cu, cv, d0) - ou * (w / 2) - ov * (h / 2), u=ou, v=ov,
                                 ancho=w, alto=h))
    _ = rnd
    return p


def extintor():
    """Extintor de 6 kg en su soporte, en el machón entre la ventana y la puerta (muro +X)."""
    p = Pieza("extintor", peso_uv=1.6)
    b = p.baja
    pl = DER
    uc = (VL[1] + PUERTA_Y[0]) / 2 - 0.03
    r = 0.15
    c = pl.p(uc, 0.95, 0.03 + r + 0.02)
    # Soporte: pletina en el muro con abrazadera y cuna.
    caja_plano(b, pl, uc - 0.06, uc + 0.06, 0.9, 2.05, 0.0, 0.03, "acero_oscuro", sin=("+y",))
    for v in (0.98, 1.92):
        tornillo(p, pl.p(uc, v, 0.03), pl.n, 0.02, "tornilleria", en_baja=False)
    b.revolucion([(r + 0.015, -0.03), (r + 0.015, 0.03), (r + 0.003, 0.03), (r + 0.003, -0.03)], c + Vector((0, 0, 0.6)),
                 10, "acero_oscuro", tapa_ini=False, tapa_fin=False)
    caja_plano(b, pl, uc - 0.04, uc + 0.04, 1.52, 1.6, 0.03, 0.05, "acero_oscuro", sin=("+y",))
    b.caja(c + Vector((0, 0, -0.01)), (0.36, 0.36, 0.03), "acero_oscuro")
    # Cuerpo (perfil de botella).
    perfil = [(0.0, 0.0), (r - 0.02, 0.0), (r, 0.03), (r, 0.82), (r - 0.03, 0.9), (0.08, 0.95), (0.04, 0.97),
              (0.0, 0.97)]
    b.revolucion(perfil, c, 12, "extintor", tapa_ini=False, tapa_fin=False)
    # Válvula, palanca, manómetro, manguera y boquilla.
    t = c + Vector((0, 0, 0.97))
    b.cilindro(t, (0, 0, 1), 0.04, 0.1, "laton", lados=8)
    b.caja(t + Vector((0, 0, 0.13)), (0.1, 0.06, 0.06), "laton")
    afuera = pl.n
    lateral = pl.u
    b.tubo([t + Vector((0, 0, 0.12)) + lateral * 0.04, t + Vector((0, 0, 0.18)) + lateral * 0.2], 0.02, "negro_mate",
           lados=4)
    b.tubo([t + Vector((0, 0, 0.08)) + lateral * 0.02, t + Vector((0, 0, 0.12)) + lateral * 0.18], 0.016,
           "acero_pulido", lados=4)
    b.cilindro(t + Vector((0, 0, 0.11)) + afuera * 0.04, afuera, 0.04, 0.03, "acero_pulido", lados=10)
    p.alta.cilindro(t + Vector((0, 0, 0.11)) + afuera * 0.07, afuera, 0.032, 0.003, "manometro", lados=14)
    b.cilindro(t + Vector((0, 0, 0.11)) - lateral * 0.02, -lateral, 0.012, 0.06, "amarillo", lados=6)  # pasador
    ruta = [t + Vector((0, 0, 0.08)) - lateral * 0.05, t + Vector((0, 0, 0.02)) - lateral * 0.2 + afuera * 0.02,
            c + Vector((0, 0, 0.6)) - lateral * (r + 0.05) + afuera * 0.02,
            c + Vector((0, 0, 0.28)) - lateral * (r + 0.04) + afuera * 0.03]
    b.tubo(ruta, 0.022, "goma", lados=4, radio_curva=0.12, pasos_curva=2)
    b.cilindro(ruta[-1], (0, 0, -1), 0.026, 0.12, "negro_mate", lados=6, radio2=0.018)
    # Etiqueta (calco).
    P["extintor"] = dict(origen=c + Vector((0, 0, 0.3)) + afuera * r - lateral * 0.105, u=lateral, v=Vector((0, 0, 1)),
                         ancho=0.21, alto=0.29, normal=afuera)
    # Cartel de señalización encima.
    caja_plano(b, pl, uc - 0.16, uc + 0.16, 2.12, 2.44, 0.0, 0.015, "senal_extintor", sin=("+y",))
    P["senal_extintor"] = dict(origen=pl.p(uc - 0.16, 2.12, 0.015), u=pl.u, v=pl.v, ancho=0.32, alto=0.32)
    return p


def papelera():
    """Papelera metálica junto a la puerta, con tapa basculante y anclada al suelo."""
    p = Pieza("papelera", peso_uv=1.2)
    b = p.baja
    c = Vector((3.35, 2.95, SUELO))
    r = 0.3
    b.revolucion([(r - 0.02, 0.0), (r, 0.05), (r, 0.82), (r + 0.02, 0.86), (r - 0.02, 0.9),
                  (r - 0.02, 0.86)], c, 12, "papelera", tapa_ini=False, tapa_fin=False)
    # Tapa abovedada con la boca.
    b.revolucion([(r + 0.025, 0.9), (r + 0.025, 0.95), (0.2, 1.06), (0.0, 1.11)], c, 12,
                 "papelera_tapa", tapa_ini=False)
    caja_plano(b, Plano(c, (-1, 0, 0)), -0.14, 0.14, 0.97 + SUELO - SUELO, 1.05, r - 0.05, r - 0.02, "negro_mate",
               sin=("+y",))
    # Bolsa asomando y franja de chapa perforada (malla alta: agujeros).
    b.revolucion([(r - 0.03, 0.86), (r - 0.01, 0.9), (r - 0.06, 0.9)], c, 12, "bolsa", tapa_ini=False, tapa_fin=False)
    for k in range(24):
        a = k * math.tau / 24
        for z in (0.25, 0.4, 0.55, 0.7):
            p.alta.cilindro(c + Vector((math.cos(a) * (r + 0.004), math.sin(a) * (r + 0.004), z)),
                            Vector((-math.cos(a), -math.sin(a), 0)), 0.022, 0.012, "negro_mate", lados=8)
    # Anclajes al suelo.
    for a in (0.5, 2.6, 4.7):
        perno_hex(p, c + Vector((math.cos(a) * (r + 0.06), math.sin(a) * (r + 0.06), 0.0)), (0, 0, 1), 0.025,
                  "tornilleria", arandela=False)
        b.caja(c + Vector((math.cos(a) * (r + 0.03), math.sin(a) * (r + 0.03), 0.06)), (0.08, 0.08, 0.12),
               "papelera", giro=Matrix.Rotation(a, 3, "Z"), sin=("-z",))
    P["papelera"] = c
    return p


def taza():
    """Taza de café en la repisa del ventanal: cerámica con grosor, asa y café dentro."""
    p = Pieza("taza", peso_uv=1.8)
    b = p.baja
    c = P["taza"] + Vector((0, 0, 0.0))
    r, h, e = 0.11, 0.24, 0.016
    # Perfil antihorario: base, pared de fuera, borde, pared de dentro, fondo.
    perfil = [(0.0, 0.0), (r - 0.015, 0.0), (r, 0.015), (r, h), (r - e, h), (r - e, e + 0.01), (0.0, e + 0.01)]
    b.revolucion(perfil, c, 12, "ceramica", tapa_ini=False, tapa_fin=False)
    b.revolucion([(r - e - 0.001, h - 0.05), (0.0, h - 0.05)], c, 12, "cafe", tapa_ini=False, tapa_fin=False)
    # Asa (tubo cerrado) mirando hacia +X.
    lado = Vector((1, 0, 0))
    b.tubo([c + lado * (r - 0.005) + Vector((0, 0, h - 0.05)), c + lado * (r + 0.07) + Vector((0, 0, h - 0.06)),
            c + lado * (r + 0.08) + Vector((0, 0, 0.08)), c + lado * (r - 0.005) + Vector((0, 0, 0.06))], 0.016,
           "ceramica", lados=6, radio_curva=0.04, pasos_curva=2)
    # Mancha de café en la repisa (malla alta) y cucharilla dentro.
    p.alta.cilindro(c + Vector((0.07, -0.13, -0.002)), (0, 0, 1), 0.06, 0.003, "cafe_mancha", lados=12)
    P["taza_c"] = c
    return p


# ======================================================================================================
# Barrera de acceso
# ======================================================================================================

MEJILLA_Y = 0.12   # media separación de las dos mejillas de la horquilla del poste


def barrera_poste():
    """Poste de la barrera: placa con 4 pernos grandes, cilindro de acero y horquilla con el eje del brazo."""
    p = Pieza("barrera_poste", peso_uv=1.3)
    b = p.baja
    c = BARRERA
    # Placa base atornillada (4 pernos grandes) con cartelas soldadas.
    b.caja_de(c + Vector((-0.36, -0.36, 0.0)), c + Vector((0.36, 0.36, 0.07)), "barrera_gris", sin=("-z",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            perno_hex(p, c + Vector((sx * 0.26, sy * 0.26, 0.07)), (0, 0, 1), 0.06, "tornilleria", arandela=True)
    for a in range(4):
        R = Matrix.Rotation(a * math.pi / 2, 3, "Z")
        p.baja.placa([(0.0, 0.0), (0.14, 0.0), (0.0, 0.3)], c + R @ Vector((0.19, -0.015, 0.07)), R @ Vector((1, 0, 0)),
                     Vector((0, 0, 1)), R @ Vector((0, 1, 0)), 0.03, "barrera_gris")
    # Fuste.
    perfil = [(0.2, 0.07), (0.2, 0.16), (0.17, 0.2), (0.17, 2.4), (0.19, 2.42), (0.19, 2.52), (0.0, 2.52)]
    b.revolucion(perfil, c, 12, "barrera_gris", tapa_ini=False, tapa_fin=False)
    _tira_alta(p, [c + Vector((0.2 * math.cos(a), 0.2 * math.sin(a), 0.165)) for a in
                   [k * math.tau / 24 for k in range(25)]], 0.014, "soldadura")
    # Tapa de registro con 4 tornillos y pegatina de peligro.
    caja_plano(b, Plano(c + Vector((0.165, 0, 0)), (1, 0, 0)), -0.08, 0.08, 0.6 + SUELO, 1.05 + SUELO, 0.0, 0.02,
               "barrera_gris", sin=("+y",))
    for dv in (0.65, 1.0):
        for du in (-0.05, 0.05):
            p.alta.cupula(c + Vector((0.185, du, dv + SUELO - SUELO)), (1, 0, 0), 0.012, "tornilleria", alto=0.007)
    # Horquilla: dos mejillas, eje con tuercas y tapa del engranaje.
    zc = BRAZO_Z
    for s in (-1, 1):
        y = c.y + s * (MEJILLA_Y + 0.025)
        b.caja_de(Vector((c.x - 0.17, y - 0.025, c.z + 2.45)), Vector((c.x + 0.17, y + 0.025, zc + 0.16)), "barrera_gris")
        b.cilindro(Vector((c.x, y + s * 0.025, zc)), (0, s, 0), 0.07, 0.04, "acero_pulido", lados=6)
        p.alta.cilindro(Vector((c.x, y + s * 0.065, zc)), (0, s, 0), 0.035, 0.03, "acero_pulido", lados=10)
    b.revolucion([(0.0, 0.0), (0.2, 0.0), (0.2, 0.05), (0.17, 0.08), (0.0, 0.08)],
                 Vector((c.x, c.y - MEJILLA_Y - 0.05, zc)), 10, "barrera_gris", eje=(0, -1, 0), tapa_ini=False)
    for k in range(6):
        a = k * math.tau / 6
        p.alta.cupula(Vector((c.x + math.cos(a) * 0.16, c.y - MEJILLA_Y - 0.13, zc + math.sin(a) * 0.16)), (0, -1, 0),
                      0.014, "tornilleria", alto=0.008)
    b.cilindro(Vector((c.x, c.y - MEJILLA_Y - 0.06, zc)), (0, 1, 0), 0.045, 2 * MEJILLA_Y + 0.12, "acero_pulido",
               lados=8)
    # Tope de goma donde descansa el brazo bajado (lado del contrapeso).
    b.caja_de(Vector((c.x - 0.17, c.y - 0.08, c.z + 2.45)), Vector((c.x - 0.05, c.y + 0.08, c.z + 2.5)), "goma")
    # Pilotos de la barrera: banda reflectante en el fuste (malla alta).
    p.alta.revolucion([(0.172, 1.6), (0.172, 1.8)], c, 24, "cinta", tapa_ini=False, tapa_fin=False)
    P["barrera_eje"] = Vector((c.x, c.y, zc))
    return p


def barrera_brazo():
    """Brazo levadizo: cubo en la horquilla, tubo de 3 studs con franjas rojas y blancas y contrapeso."""
    eje = Vector((BARRERA.x, BARRERA.y, BRAZO_Z))
    p = Pieza("barrera_brazo", pivote=eje, peso_uv=1.6)
    b = p.baja
    # Cubo que gira en el eje.
    b.cilindro(eje - Vector((0, MEJILLA_Y - 0.005, 0)), (0, 1, 0), 0.13, 2 * (MEJILLA_Y - 0.005), "barrera_gris", lados=12)
    # Abrazadera del tubo (dos bridas con 4 tornillos).
    b.caja_de(eje + Vector((-0.25, -0.1, -0.11)), eje + Vector((0.32, 0.1, 0.11)), "barrera_gris")
    for x in (-0.18, 0.25):
        for s in (-1, 1):
            p.alta.cilindro(eje + Vector((x, s * 0.1, 0.0)), (0, s, 0), 0.03, 0.025, "tornilleria", lados=6)
    # Tubo: 3 studs desde el eje hacia +X, y el lado corto hacia -X.
    r = 0.08
    b.revolucion([(0.0, 0.0), (r * 0.8, 0.0), (r, 0.02), (r, 3.0 + 0.45 - 0.02), (r * 0.8, 3.0 + 0.45),
                  (0.0, 3.0 + 0.45)], eje + Vector((-0.45, 0, 0)), 12, "brazo_franjas", eje=(1, 0, 0), tapa_ini=False,
                 tapa_fin=False)
    # Contera de goma en la punta.
    b.revolucion([(r + 0.01, 0.0), (r + 0.015, 0.1), (0.0, 0.17)],
                 eje + Vector((3.0, 0, 0)), 12, "goma", eje=(1, 0, 0), tapa_ini=False, tapa_fin=False)
    # Contrapeso cilíndrico en el lado corto, con su tuerca.
    cw = eje + Vector((-0.42, 0, 0))
    b.revolucion([(0.18, 0.0), (0.21, 0.03), (0.21, 0.31), (0.18, 0.34), (0.0, 0.34)], cw, 12,
                 "contrapeso", eje=(-1, 0, 0), tapa_ini=False, tapa_fin=False)
    b.cilindro(cw + Vector((-0.34, 0, 0)), (-1, 0, 0), 0.06, 0.06, "acero_pulido", lados=6)
    # Faldón de goma bajo el tubo (amortigua si toca un coche) y catadióptricos (malla alta).
    b.caja_de(eje + Vector((0.4, -0.012, -r - 0.12)), eje + Vector((2.95, 0.012, -r + 0.01)), "goma")
    for k in range(5):
        x = 0.7 + k * 0.55
        for s in (-1, 1):
            p.alta.caja(eje + Vector((x, s * (r - 0.004), 0.0)), (0.08, 0.01, 0.06), "catadioptrico")
    P["brazo_x0"] = eje.x
    return p


def barrera_apoyo():
    """Horquilla de apoyo al otro lado de la calzada, donde descansa la punta del brazo."""
    p = Pieza("barrera_apoyo", peso_uv=1.0)
    b = p.baja
    c = Vector((BARRERA.x + 2.88, BARRERA.y, 0.0))
    b.caja_de(c + Vector((-0.2, -0.2, 0.0)), c + Vector((0.2, 0.2, 0.05)), "barrera_gris", sin=("-z",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            perno_hex(p, c + Vector((sx * 0.14, sy * 0.14, 0.05)), (0, 0, 1), 0.035, "tornilleria", arandela=False)
    zt = BRAZO_Z - 0.09
    b.cilindro(c + Vector((0, 0, 0.05)), (0, 0, 1), 0.06, zt - 0.2, "apoyo_franjas", lados=10, tapa_ini=False)
    # Horquilla en U.
    b.caja_de(c + Vector((-0.06, -0.14, zt - 0.17)), c + Vector((0.06, 0.14, zt - 0.12)), "barrera_gris")
    for s in (-1, 1):
        b.caja_de(c + Vector((-0.06, s * 0.14 - 0.025, zt - 0.12)), c + Vector((0.06, s * 0.14 + 0.025, zt + 0.12)),
                  "barrera_gris")
    b.caja_de(c + Vector((-0.06, -0.115, zt - 0.12)), c + Vector((0.06, 0.115, zt - 0.1)), "goma", sin=("-z",))
    return p


# ======================================================================================================
# Entorno: interfono, cono, STOP y banda reductora
# ======================================================================================================


def interfono():
    """Interfono para los conductores: poste fino, caja con visera, altavoz, botón y pantallita."""
    p = Pieza("interfono", peso_uv=1.8)
    b = p.baja
    c = INTERFONO
    b.caja_de(c + Vector((-0.15, -0.15, 0.0)), c + Vector((0.15, 0.15, 0.04)), "barrera_gris", sin=("-z",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            perno_hex(p, c + Vector((sx * 0.1, sy * 0.1, 0.04)), (0, 0, 1), 0.02, "tornilleria", arandela=False)
    b.caja_de(c + Vector((-0.05, -0.05, 0.04)), c + Vector((0.05, 0.05, 1.75)), "barrera_gris", sin=("-z", "+z"))
    # Caja (frente hacia +X, hacia la calzada) ligeramente inclinada hacia el conductor.
    z0, z1 = 1.72, 2.36
    cx = c.x + 0.02
    b.caja_de(Vector((cx - 0.12, c.y - 0.19, c.z + z0)), Vector((cx + 0.12, c.y + 0.19, c.z + z1)), "interfono_caja")
    b.caja_de(Vector((cx - 0.14, c.y - 0.22, c.z + z1)), Vector((cx + 0.2, c.y + 0.22, c.z + z1 + 0.035)),
              "interfono_caja")
    pl = Plano((cx + 0.12, c.y, 0), (1, 0, 0))   # u = +y
    # Marco de la pantallita y altavoz.
    caja_plano(b, pl, -0.11, 0.11, c.z + 2.11, c.z + 2.29, 0.0, 0.02, "negro_mate", sin=("+y",))
    caja_plano(b, pl, -0.13, 0.13, c.z + 1.88, c.z + 2.06, 0.0, 0.012, "rejilla", sin=("+y",))
    for k in range(7):  # ranuras del altavoz (malla alta)
        v = c.z + 1.9 + k * 0.022
        caja_plano(p.alta, pl, -0.11, 0.11, v, v + 0.009, 0.012, 0.016, "negro_mate", sin=("+y",))
    # Botón de llamada con aro y su etiqueta.
    b.cilindro(pl.p(0, c.z + 1.8, 0.0), pl.n, 0.055, 0.02, "acero_pulido", lados=12)
    b.cilindro(pl.p(0, c.z + 1.8, 0.02), pl.n, 0.04, 0.02, "boton", lados=12)
    P["interfono_etiqueta"] = dict(origen=pl.p(-0.1, c.z + 1.725, 0.0), u=pl.u, v=pl.v, ancho=0.2, alto=0.05)
    # Cámara del interfono (puntito) y cable bajando por el poste.
    p.alta.cilindro(pl.p(0.08, c.z + 2.32, 0.0), pl.n, 0.012, 0.005, "lente", lados=10)
    b.tubo([Vector((c.x - 0.05, c.y + 0.03, c.z + z0)), Vector((c.x - 0.065, c.y + 0.03, c.z + 1.0)),
            Vector((c.x - 0.065, c.y + 0.03, c.z + 0.1)), Vector((c.x - 0.03, c.y + 0.1, c.z + 0.04))], 0.014, "cable",
           lados=5, radio_curva=0.05, pasos_curva=2)
    P["interfono_pl"] = pl
    return p


def interfono_pantalla():
    """Pantallita del interfono (Neon cian)."""
    p = Pieza("interfono_pantalla_neon", peso_uv=0.0)
    p.tipo = "neon"
    c = INTERFONO
    pl = Plano((c.x + 0.02 + 0.12, c.y, 0), (1, 0, 0))
    caja_plano(p.baja, pl, -0.09, 0.09, c.z + 2.13, c.z + 2.27, 0.0, 0.025, "neon", sin=("+y",))
    return p


def cono():
    """Cono de tráfico naranja con base cuadrada y dos franjas reflectantes."""
    p = Pieza("cono", peso_uv=1.2)
    b = p.baja
    c = CONO
    # Base cuadrada con chaflán.
    b.revolucion([(0.0, 0.0), (0.42, 0.0), (0.42, 0.04), (0.38, 0.07)], c, 4, "cono_base",
                 giro=math.pi / 4, tapa_ini=False, tapa_fin=True, suave=False, escala=(1.414, 1.414))
    perfil = [(0.3, 0.07), (0.27, 0.12), (0.08, 1.38), (0.065, 1.42), (0.0, 1.42)]
    b.revolucion(perfil, c, 14, "cono", tapa_ini=False, tapa_fin=False)
    return p


def stop():
    """Señal de STOP en su poste, frente a la barrera (mira a los coches que llegan desde -Y)."""
    p = Pieza("stop", peso_uv=1.8)
    b = p.baja
    c = STOP
    b.caja_de(c + Vector((-0.15, -0.15, 0.0)), c + Vector((0.15, 0.15, 0.04)), "galvanizado", sin=("-z",))
    for sx in (-1, 1):
        for sy in (-1, 1):
            perno_hex(p, c + Vector((sx * 0.1, sy * 0.1, 0.04)), (0, 0, 1), 0.022, "tornilleria", arandela=False)
    b.cilindro(c + Vector((0, 0, 0.04)), (0, 0, 1), 0.045, 3.25, "galvanizado", lados=8, tapa_ini=False)
    b.revolucion([(0.0, 0.0), (0.05, 0.0), (0.04, 0.03), (0.0, 0.035)], c + Vector((0, 0, 3.29)), 8, "plastico_negro",
                 tapa_ini=False)
    # Octógono (placa con grosor), 1,1 de ancho.
    zc = c.z + 2.75
    R = 0.58
    pts = [(math.cos(math.pi / 8 + k * math.pi / 4) * R, math.sin(math.pi / 8 + k * math.pi / 4) * R) for k in range(8)]
    pl = Plano((c.x, c.y - 0.07, 0), (0, -1, 0))   # u = +x
    b.placa([(c.x + x, zc + y) for x, y in pts], Vector((0, c.y - 0.07, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)),
            Vector((0, -1, 0)), 0.03, "senal_stop", mat_canto="galvanizado", atras=True)
    # Cara de atrás galvanizada (la de la placa es la misma; la malla alta añade el refuerzo).
    # Borde blanco reflectante y letras (malla alta).
    Ri = R - 0.05
    anillo_e = [(c.x + math.cos(math.pi / 8 + k * math.pi / 4) * (R - 0.02), zc + math.sin(math.pi / 8 + k * math.pi / 4)
                 * (R - 0.02)) for k in range(8)]
    anillo_i = [(c.x + math.cos(math.pi / 8 + k * math.pi / 4) * Ri, zc + math.sin(math.pi / 8 + k * math.pi / 4) * Ri)
                for k in range(8)]
    p.alta.anillo_placa(anillo_e, anillo_i, Vector((0, c.y - 0.1, 0)), Vector((1, 0, 0)), Vector((0, 0, 1)),
                        Vector((0, -1, 0)), 0.004, "reflectante_blanco")
    texto(p.alta, "STOP", Vector((c.x, c.y - 0.1, zc)), Vector((1, 0, 0)), Vector((0, 0, 1)), Vector((0, -1, 0)), 0.34,
          0.006, "reflectante_blanco", ancho_max=0.86)
    # Abrazaderas en U detrás.
    for dz in (-0.3, 0.3):
        b.caja_de(Vector((c.x - 0.12, c.y - 0.07 + 0.0, zc + dz - 0.03)), Vector((c.x + 0.12, c.y - 0.04, zc + dz + 0.03)),
                  "galvanizado", sin=("-y",))
        b.tubo([Vector((c.x - 0.07, c.y - 0.05, zc + dz)), Vector((c.x - 0.07, c.y + 0.06, zc + dz)),
                Vector((c.x + 0.07, c.y + 0.06, zc + dz)), Vector((c.x + 0.07, c.y - 0.05, zc + dz))], 0.012,
               "galvanizado", lados=4, radio_curva=0.03, pasos_curva=2)
    _ = pl
    return p


def banda_reductora():
    """Banda reductora de goma (módulos negros y amarillos) atornillada a la calzada, antes de la barrera."""
    p = Pieza("banda_reductora", peso_uv=1.0)
    b = p.baja
    x0, x1 = CALZADA_X[0] + 0.1, CALZADA_X[1] - 0.1
    yc = BANDA_Y
    perfil = [(-0.45, 0.0), (-0.32, 0.07), (-0.14, 0.14), (0.0, 0.155), (0.14, 0.14), (0.32, 0.07), (0.45, 0.0)]
    rings = []
    for x, esc in ((x0 - 0.22, 0.12), (x0, 1.0), (x1, 1.0), (x1 + 0.22, 0.12)):
        rings.append([Vector((x, yc + y * (0.6 + 0.4 * esc), z * esc)) for y, z in perfil])
    # Loft abierto (no se cierra el perfil: va pegado al suelo).
    vs = [[b.v(q) for q in r] for r in rings]
    for k in range(len(vs) - 1):
        for i in range(len(perfil) - 1):
            b.cara([vs[k][i], vs[k][i + 1], vs[k + 1][i + 1], vs[k + 1][i]], "banda", suave=True)
    b.recalcular([f for f in b.bm.faces])
    for f in b.bm.faces:
        f.normal_update()
        if f.normal.z < 0:
            f.normal_flip()
    # Tornillos de anclaje y ojos de gato (malla alta).
    n = 6
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        for y in (-0.3, 0.3):
            p.alta.cupula(Vector((x, yc + y, 0.085)), Vector((0, -y, 0.45)).normalized(), 0.03, "tornilleria",
                          alto=0.015)
        p.alta.caja(Vector((x, yc - 0.15, 0.135)), (0.12, 0.05, 0.02), "catadioptrico",
                    giro=Matrix.Rotation(math.radians(-22), 3, "X"))
    P["banda"] = (x0, x1, yc)
    return p


# ======================================================================================================
# Interior (se ve por el ventanal)
# ======================================================================================================

MESA_Z = 1.95                 # encimera del mostrador
MESA_F = YI0 + 0.78           # canto del mostrador de la fachada
SILLA = Vector((0.35, -0.95, PISO))
SILLA_GIRO = 14.0


def interior_suelo():
    p = Pieza("interior_suelo", peso_uv=0.6)
    b = p.baja
    b.poligono([Vector((XI0, YI0, PISO)), Vector((XI1, YI0, PISO)), Vector((XI1, YI1, PISO)), Vector((XI0, YI1, PISO))],
               "suelo_goma", (0, 0, 1))
    # Rodapié.
    for pl, u0, u1 in ((Plano((0, YI1, 0), (0, -1, 0)), XI0, XI1), (Plano((XI0, 0, 0), (1, 0, 0)), YI0, YI1),
                       (Plano((XI1, 0, 0), (-1, 0, 0)), -YI1, -PUERTA_Y[1]), (Plano((XI1, 0, 0), (-1, 0, 0)),
                                                                              -PUERTA_Y[0], -YI0)):
        caja_plano(b, pl, u0, u1, PISO, PISO + 0.16, 0.0, 0.025, "rodapie", sin=("+y", "-z", "-x", "+x"))
    return p


def mostrador():
    """Mostrador en L bajo el ventanal: encimera de laminado, frentes y cajonera."""
    p = Pieza("mostrador", peso_uv=0.9)
    b = p.baja
    e = 0.06
    # Tramo de la fachada.
    b.caja_de((XI0, YI0, MESA_Z - e), (XI1, MESA_F, MESA_Z), "encimera", sin=("-y",), ocultas=("-z",))
    b.caja_de((XI0 + 0.05, MESA_F - 0.08, PISO), (XI1 - 0.75, MESA_F - 0.04, MESA_Z - e), "mueble",
              sin=("-z", "+z"))
    # Tramo del lateral derecho (bajo la ventana de la barrera).
    yd1 = VL[1] + 0.05
    b.caja_de((XI1 - 0.72, MESA_F, MESA_Z - e), (XI1, yd1, MESA_Z), "encimera", sin=("+x",), ocultas=("-z",))
    # Cajonera bajo la esquina.
    b.caja_de((XI1 - 0.7, MESA_F - 0.7, PISO), (XI1 - 0.05, MESA_F + 0.55, MESA_Z - e), "mueble", sin=("-z", "+z"))
    for k in range(3):
        z0 = PISO + 0.12 + k * 0.5
        p.alta.caja((XI1 - 0.72, MESA_F - 0.08, z0 + 0.2), (0.012, 1.15, 0.43), "mueble")
        b.caja((XI1 - 0.73, MESA_F - 0.08, z0 + 0.36), (0.03, 0.3, 0.035), "acero_pulido")
    # Faldón del tramo derecho.
    b.caja_de((XI1 - 0.69, MESA_F + 0.55, PISO), (XI1 - 0.65, yd1 - 0.05, MESA_Z - e), "mueble", sin=("-z", "+z"))
    P["mesa_z"] = MESA_Z
    return p


def monitores():
    """Dos monitores con lo que ven las cámaras (la barrera y la calle), teclado y walkie en su cargador."""
    p = Pieza("monitores", peso_uv=1.6)
    b = p.baja
    posiciones = [(Vector((-1.55, YI0 + 0.32, MESA_Z)), 22.0, "pantalla_1"),
                  (Vector((-0.55, YI0 + 0.28, MESA_Z)), 8.0, "pantalla_2")]
    P["pantallas"] = []
    for base, giro, mat in posiciones:
        R = Matrix.Rotation(math.radians(giro), 3, "Z")
        b.revolucion([(0.0, 0.0), (0.16, 0.0), (0.15, 0.025), (0.0, 0.03)], base, 10, "plastico_negro", tapa_ini=False,
                     escala=(1.3, 0.8))
        b.caja(base + R @ Vector((0, 0.02, 0.22)), (0.07, 0.04, 0.4), "plastico_negro", giro=R)
        centro = base + R @ Vector((0, -0.01, 0.5))
        b.caja(centro, (0.78, 0.06, 0.48), "plastico_negro", giro=R, mats={"+y": "plastico_negro"})
        # Pantalla: cara de delante (mira a +Y, al guardia).
        sc = centro + R @ Vector((0, 0.031, 0.01))
        u = R @ Vector((-1, 0, 0))
        v = Vector((0, 0, 1))
        caja = [sc - u * 0.36 - v * 0.21, sc + u * 0.36 - v * 0.21, sc + u * 0.36 + v * 0.21, sc - u * 0.36 + v * 0.21]
        b.poligono(caja, mat, R @ Vector((0, 1, 0)))
        P["pantallas"].append(dict(calco=mat, origen=caja[0], u=u, v=v, ancho=0.72, alto=0.42))
    # Teclado.
    kb = Vector((-1.0, YI0 + 0.62, MESA_Z))
    b.caja_de(kb + Vector((-0.32, -0.1, 0.0)), kb + Vector((0.32, 0.1, 0.03)), "plastico_negro", sin=("-z",))
    for i in range(14):
        for j in range(4):
            p.alta.caja(kb + Vector((-0.28 + i * 0.043, -0.065 + j * 0.043, 0.033)), (0.034, 0.034, 0.008), "tecla")
    # Walkie en su cargador.
    w = Vector((1.45, YI0 + 0.3, MESA_Z))
    b.caja_de(w + Vector((-0.09, -0.09, 0.0)), w + Vector((0.09, 0.09, 0.06)), "plastico_negro", sin=("-z",))
    b.caja_de(w + Vector((-0.055, -0.04, 0.06)), w + Vector((0.055, 0.04, 0.36)), "walkie")
    b.cilindro(w + Vector((0.03, 0.0, 0.36)), (0, 0, 1), 0.012, 0.22, "plastico_negro", lados=5)
    p.alta.caja(w + Vector((-0.04, -0.091, 0.03)), (0.02, 0.004, 0.012), "led")
    return p


def silla():
    """La silla del guardia: de oficina, con el asiento hundido de tantas horas y el respaldo vencido."""
    p = Pieza("silla", peso_uv=1.3)
    b = p.baja
    c = SILLA
    R = Matrix.Rotation(math.radians(SILLA_GIRO), 3, "Z")
    # Estrella de 5 patas con ruedas.
    for k in range(5):
        a = k * math.tau / 5 + 0.3
        d = Vector((math.cos(a), math.sin(a), 0))
        b.tubo([c + Vector((0, 0, 0.2)), c + d * 0.5 + Vector((0, 0, 0.14))], 0.035, "plastico_negro", lados=4)
        rueda = c + d * 0.5 + Vector((0, 0, 0.06))
        b.cilindro(rueda - d.cross(Vector((0, 0, 1))) * 0.03, d.cross(Vector((0, 0, 1))), 0.06, 0.06, "goma", lados=5)
    b.cilindro(c + Vector((0, 0, 0.16)), (0, 0, 1), 0.09, 0.1, "plastico_negro", lados=10)
    b.cilindro(c + Vector((0, 0, 0.26)), (0, 0, 1), 0.045, 0.85, "acero_pulido", lados=8)   # pistón
    b.cilindro(c + Vector((0, 0, 0.26)), (0, 0, 1), 0.065, 0.4, "plastico_negro", lados=8)  # funda
    # Asiento: cojín con la cara de arriba hundida en el centro y un poco hacia atrás.
    zs = c.z + 1.18
    nx, ny = 5, 5
    w, d = 0.95, 0.9
    hundir = []

    def hundido(x, y):
        # x, y en [-1, 1]; hueco de 0,09 donde se sienta (un poco detrás del centro).
        r2 = (x / 0.85) ** 2 + ((y - 0.15) / 0.8) ** 2
        return -0.09 * max(0.0, 1 - r2) ** 1.4

    arriba = []
    for j in range(ny + 1):
        fila = []
        for i in range(nx + 1):
            x, y = -1 + 2 * i / nx, -1 + 2 * j / ny
            borde = max(abs(x), abs(y))
            redondeo = -0.05 * max(0.0, borde - 0.75) / 0.25
            fila.append(c + R @ Vector((x * w / 2, y * d / 2, 0)) + Vector((0, 0, zs - c.z + 0.18 + hundido(x, y)
                                                                         + redondeo)))
        arriba.append(fila)
    va = [[b.v(q) for q in fila] for fila in arriba]
    for j in range(ny):
        for i in range(nx):
            hundir.append(b.cara([va[j][i], va[j][i + 1], va[j + 1][i + 1], va[j + 1][i]], "tela_silla", suave=True))
    # Laterales del cojín hasta la base del asiento.
    contorno = [(j, 0) for j in range(ny, -1, -1)] + [(0, i) for i in range(1, nx + 1)] + \
               [(j, nx) for j in range(1, ny + 1)] + [(ny, i) for i in range(nx - 1, 0, -1)]
    abajo = {}
    for (j, i) in contorno:
        q = arriba[j][i]
        abajo[(j, i)] = b.v(Vector((q.x, q.y, zs)))
    for k in range(len(contorno)):
        a0, a1 = contorno[k], contorno[(k + 1) % len(contorno)]
        hundir.append(b.cara([va[a0[0]][a0[1]], va[a1[0]][a1[1]], abajo[a1], abajo[a0]], "tela_silla", suave=True))
    hundir.append(b.cara([abajo[k] for k in contorno], "plastico_negro"))
    b.recalcular(hundir)
    # Respaldo: un poco vencido hacia atrás, curvado.
    capas = []
    inclin = math.radians(16)
    for lado in (-1, 1):
        filas = []
        for j in range(5):
            f = j / 4
            fila = []
            for i in range(5):
                g = -1 + 2 * i / 4
                x = g * 0.44 * (1 - 0.12 * f)
                curva = 0.07 * g * g
                yy = d / 2 + 0.05 + f * 1.05 * math.sin(inclin) + curva + lado * 0.05
                zz = zs + 0.3 + f * 1.05 * math.cos(inclin)
                fila.append(b.v(c + R @ Vector((x, yy, 0)) + Vector((0, 0, zz - c.z))))
            filas.append(fila)
        capas.append(filas)
    resp = []
    fr, at = capas[0], capas[1]
    for j in range(4):
        for i in range(4):
            resp.append(b.cara([fr[j][i], fr[j][i + 1], fr[j + 1][i + 1], fr[j + 1][i]], "tela_silla", suave=True))
            resp.append(b.cara([at[j][i + 1], at[j][i], at[j + 1][i], at[j + 1][i + 1]], "plastico_negro", suave=True))
    bordes = [(j, 0) for j in range(4, -1, -1)] + [(0, i) for i in range(1, 5)] + [(j, 4) for j in range(1, 5)] + \
             [(4, i) for i in range(3, 0, -1)]
    for k in range(len(bordes)):
        (j0, i0), (j1, i1) = bordes[k], bordes[(k + 1) % len(bordes)]
        resp.append(b.cara([fr[j0][i0], fr[j1][i1], at[j1][i1], at[j0][i0]], "plastico_negro", suave=True))
    b.recalcular(resp)
    # Pletina del respaldo y reposabrazos.
    b.tubo([c + R @ Vector((0, 0.1, 0)) + Vector((0, 0, 1.15)), c + R @ Vector((0, d / 2 + 0.12, 0)) +
            Vector((0, 0, 1.15)), c + R @ Vector((0, d / 2 + 0.14, 0)) + Vector((0, 0, 1.55))], 0.035, "acero_oscuro",
           lados=4, radio_curva=0.08, pasos_curva=2)
    for s in (-1, 1):
        b.tubo([c + R @ Vector((s * 0.4, 0.05, 0)) + Vector((0, 0, 1.15)),
                c + R @ Vector((s * 0.52, 0.05, 0)) + Vector((0, 0, 1.2)),
                c + R @ Vector((s * 0.52, 0.0, 0)) + Vector((0, 0, 1.55))], 0.03, "plastico_negro", lados=4,
               radio_curva=0.05, pasos_curva=2)
        b.caja(c + R @ Vector((s * 0.52, -0.02, 0)) + Vector((0, 0, 1.58)), (0.1, 0.42, 0.06), "goma", giro=R)
    # Costuras y arrugas del cojín (malla alta) y parche de cinta americana en una esquina.
    p.alta.caja(c + R @ Vector((0.3, -0.33, 0)) + Vector((0, 0, zs - c.z + 0.135)), (0.18, 0.12, 0.006), "cinta_americana",
                giro=R @ Matrix.Rotation(0.4, 3, "Z"))
    P["silla_hueco"] = c + R @ Vector((0, 0.07, 0)) + Vector((0, 0, zs - c.z + 0.1))
    return p


def cosas_guardia():
    """Lo personal: foto familiar, termo, cactus en su maceta, portapapeles y la gorra colgada."""
    p = Pieza("cosas_guardia", peso_uv=2.0)
    b = p.baja
    z = MESA_Z
    # Marco de foto (mira al guardia, con su pata).
    f = Vector((0.55, YI0 + 0.25, z))
    R = Matrix.Rotation(math.radians(-15), 3, "Z") @ Matrix.Rotation(math.radians(-12), 3, "X")
    b.caja(f + R @ Vector((0, 0, 0.15)), (0.34, 0.03, 0.27), "marco_foto", giro=R)
    b.caja(f + Vector((0, -0.07, 0.1)), (0.04, 0.12, 0.012), "marco_foto", giro=Matrix.Rotation(-0.9, 3, "X"))
    u = R @ Vector((-1, 0, 0))
    v = R @ Vector((0, 0, 1))
    n = R @ Vector((0, 1, 0))
    o = f + R @ Vector((0.13, 0.016, 0.045))
    b.poligono([o, o + u * 0.26, o + u * 0.26 + v * 0.2, o + v * 0.2], "foto", n)
    P["foto"] = dict(origen=o, u=u, v=v, ancho=0.26, alto=0.2)
    # Termo.
    t = Vector((1.05, YI0 + 0.22, z))
    b.revolucion([(0.075, 0.0), (0.08, 0.03), (0.08, 0.42), (0.06, 0.47), (0.07, 0.5), (0.07, 0.6), (0.0, 0.6)], t, 8,
                 "termo", tapa_ini=False, tapa_fin=False)
    # Cactus en su maceta (junto a la ventana de la barrera, se ve desde fuera).
    m = Vector((XI1 - 0.3, -1.25, z))
    b.revolucion([(0.0, 0.0), (0.09, 0.0), (0.12, 0.2), (0.135, 0.21), (0.135, 0.24), (0.115, 0.24), (0.11, 0.21),
                  (0.0, 0.21)], m, 8, "maceta", tapa_ini=False, tapa_fin=False)
    b.revolucion([(0.0, 0.2), (0.07, 0.21), (0.085, 0.3), (0.075, 0.45), (0.04, 0.52), (0.0, 0.53)], m, 8, "cactus",
                 tapa_ini=False, tapa_fin=False)
    b.revolucion([(0.0, 0.0), (0.035, 0.02), (0.04, 0.12), (0.0, 0.16)], m + Vector((0.07, 0.0, 0.33)), 6, "cactus",
                 eje=Vector((1, 0, 1.2)).normalized(), tapa_ini=False, tapa_fin=False)
    b.revolucion([(0.0, 0.0), (0.02, 0.01), (0.0, 0.03)], m + Vector((0.0, 0.0, 0.53)), 6, "flor", tapa_ini=False,
                 tapa_fin=False)
    for k in range(30):  # espinas (malla alta)
        a = k * 2.4
        zz = 0.25 + (k % 10) * 0.025
        d = Vector((math.cos(a), math.sin(a), 0.2)).normalized()
        p.alta.cilindro(m + Vector((math.cos(a) * 0.075, math.sin(a) * 0.075, zz)), d, 0.004, 0.03, "espina", lados=3)
    # Portapapeles con hojas y un boli.
    cp = Vector((0.1, YI0 + 0.5, z))
    G = Matrix.Rotation(0.25, 3, "Z")
    b.caja(cp + Vector((0, 0, 0.008)), (0.3, 0.42, 0.016), "carton", giro=G)
    b.caja(cp + G @ Vector((0, 0.17, 0.025)), (0.12, 0.05, 0.02), "acero_pulido", giro=G)
    b.caja(cp + Vector((0, -0.01, 0.019)), (0.27, 0.37, 0.006), "papel_hoja", giro=G)
    b.cilindro(cp + Vector((0.2, 0.1, 0.012)), Vector((0.3, -1, 0)).normalized(), 0.012, 0.2, "boli", lados=6)
    # Gorra colgada en un gancho del muro de atrás.
    g = Vector((-1.75, YI1, 3.55))
    b.caja_de(g + Vector((-0.04, -0.03, -0.06)), g + Vector((0.04, 0.0, 0.06)), "acero_oscuro", sin=("+y",))
    b.tubo([g + Vector((0, -0.02, 0)), g + Vector((0, -0.12, 0.02)), g + Vector((0, -0.14, 0.07))], 0.012,
           "acero_oscuro", lados=4)
    gorra = g + Vector((0, -0.14, -0.08))
    b.revolucion([(0.0, 0.18), (0.08, 0.17), (0.14, 0.12), (0.16, 0.04), (0.16, 0.0), (0.145, 0.0), (0.145, 0.04),
                  (0.13, 0.1), (0.0, 0.14)], gorra, 8, "gorra", tapa_ini=False, tapa_fin=False,
                 eje=Vector((0, -0.25, 1)).normalized())
    b.caja(gorra + Vector((0, -0.2, -0.05)), (0.26, 0.16, 0.015), "gorra",
           giro=Matrix.Rotation(math.radians(-55), 3, "X"))
    p.alta.caja(gorra + Vector((0, -0.11, 0.06)), (0.08, 0.004, 0.05), "letras_oro",
                giro=Matrix.Rotation(math.radians(-60), 3, "X"))
    return p


def pared_interior():
    """Lo que se ve al fondo por el ventanal: estantería con la radio base, calendario, llavero y la luz."""
    p = Pieza("pared_interior", peso_uv=1.2)
    b = p.baja
    pl = Plano((0, YI1, 0), (0, -1, 0))   # muro de atrás por dentro: u = +x, n = -y
    cx = P.get("pasamuros_x", 0.7)
    # Estantería con escuadras.
    caja_plano(b, pl, cx - 0.55, cx + 0.55, 3.3, 3.35, 0.0, 0.4, "encimera", sin=("+y",))
    for u in (cx - 0.45, cx + 0.45):
        b.placa([(0.0, 0.0), (0.32, 0.0), (0.0, -0.3)], pl.p(u - 0.015, 3.3, 0.0), pl.n, pl.v, pl.u, 0.03,
                "acero_oscuro")
    # Radio base: caja con frontal, mando, altavoz y micrófono de mano colgado.
    r0 = pl.p(cx - 0.05, 3.35, 0.06)
    b.caja_de(r0 + Vector((-0.28, -0.26, 0.0)), r0 + Vector((0.28, 0.0, 0.2)), "radio_caja")
    b.cilindro(r0 + Vector((0.18, -0.26, 0.1)), (0, -1, 0), 0.04, 0.03, "plastico_negro", lados=10)
    caja_plano(b, pl, cx - 0.3, cx - 0.06, 3.43, 3.51, 0.265, 0.27, "radio_display", sin=("+y",))
    for k in range(6):
        p.alta.caja(r0 + Vector((-0.2 + k * 0.025, -0.262, 0.06)), (0.012, 0.004, 0.06), "negro_mate")
    b.tubo([r0 + Vector((-0.28, -0.12, 0.12)), r0 + Vector((-0.4, -0.2, 0.0)), r0 + Vector((-0.42, -0.26, -0.25))],
           0.012, "cable", lados=4, radio_curva=0.06, pasos_curva=1)
    b.caja(r0 + Vector((-0.42, -0.28, -0.32)), (0.07, 0.04, 0.13), "plastico_negro")
    # Cable de la antena: entra por el pasamuros (x = cx, z = 4.5) y baja hasta la radio.
    b.tubo([Vector((cx, YI1, 4.5)), Vector((cx, YI1 - 0.04, 4.45)), Vector((cx, YI1 - 0.04, 3.75)),
            r0 + Vector((0.12, -0.04, 0.2))], 0.022, "cable", lados=4, radio_curva=0.08, pasos_curva=1, tapa_ini=False)
    # Calendario y caja de llaves.
    caja_plano(b, pl, -0.55, -0.05, 2.75, 3.45, 0.0, 0.006, "calendario", sin=("+y",))
    P["calendario"] = dict(origen=pl.p(-0.55, 2.75, 0.006), u=pl.u, v=pl.v, ancho=0.5, alto=0.7)
    caja_plano(b, pl, -1.2, -0.8, 2.4, 2.95, 0.0, 0.1, "caja_llaves", sin=("+y",))
    for k in range(3):
        p.alta.cilindro(pl.p(-1.12 + k * 0.12, 2.82, 0.1), pl.n, 0.008, 0.03, "acero_pulido", lados=5)
    # Reloj de pared.
    b.cilindro(pl.p(0.2, 4.4, 0.0), pl.n, 0.17, 0.04, "reloj", lados=10)
    # Luz del techo (panel que brilla: emisión en el atlas).
    b.caja_de((-0.6, -0.6, TECHO_INT - 0.05), (0.6, 0.3, TECHO_INT), "luz_techo", sin=("+z",),
              mats={"-x": "aluminio", "+x": "aluminio", "-y": "aluminio", "+y": "aluminio"})
    P["luz_interior"] = Vector((0.0, -0.15, TECHO_INT - 0.3))
    return p


# ======================================================================================================
# Montaje
# ======================================================================================================


def construir():
    """Crea todas las piezas en orden (algunas usan puntos de otras). Devuelve (piezas, P)."""
    P.clear()
    piezas = [losa(), paredes(), zocalo(), angulares(), ventanal_marcos(), ventanal_cristal(), ventanal_malla(),
              alfeizares(), techo(), albardilla(), letrero_frontal(), marco_puerta(), puerta(), foco_base(),
              foco_cabezal(), foco_lente(), sirena(), baliza(), baliza_cristal(), antena_radio(), panel_solar(),
              bandera(), camaras(), tablon(), extintor(), papelera(), taza(), barrera_poste(), barrera_brazo(),
              barrera_apoyo(), interfono(), interfono_pantalla(), cono(), stop(), banda_reductora(),
              interior_suelo(), mostrador(), monitores(), silla(), cosas_guardia(), pared_interior()]
    return piezas, P
