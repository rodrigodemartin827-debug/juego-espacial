"""
Casa del ingeniero de la colonia (Ing. Kowalski): la casa más técnica del pueblo, con un mini laboratorio adosado.

Uso:
    python pueblo/herramientas/casa_ingeniero.py --salida pueblo/casa_ingeniero [--rapido]

Sale en la carpeta:
    casa_ingeniero.fbx, casa_ingeniero_{color,normal,roughness,metalness,emision}.png (atlas 2048²),
    casa_ingeniero_turnaround.png (8 vistas), casa_ingeniero_detalles.png y casa_ingeniero.json.

Coordenadas en studs, en Blender: X a la derecha, -Y hacia delante (la calle), Z arriba. El origen es el centro
de la planta de la casa principal, a ras de suelo. El laboratorio queda a la derecha (+X).
Todas las medidas y posiciones están en las constantes de arriba de cada sección.
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import kit_casas as K  # noqa: E402
import letreros_ingeniero as L  # noqa: E402
import materiales_ingeniero as MI  # noqa: E402

V = Vector
M = MI.M
NOMBRE = "casa_ingeniero"

# --------------------------------------------------------------------------------------------------------------
# Medidas generales (studs)
# --------------------------------------------------------------------------------------------------------------

CASA = dict(x0=-5.5, x1=5.5, y0=-4.5, y1=4.5, z0=0.5, z1=6.3, g=0.45, losa=0.35, peto=0.4)
LAB = dict(x0=7.2, x1=11.2, y0=-1.6, y1=2.4, z0=0.35, z1=4.75, g=0.4, losa=0.3, peto=0.25)
PASILLO = dict(x0=5.5, x1=7.2, y0=-0.4, y1=1.8, z0=0.35, z1=3.9)

PUERTA = dict(x0=-3.4, x1=-0.8, z1=5.5)          # hueco de la puerta principal (en la fachada y = -4.5)
VENT_FRENTE = dict(x0=0.9, x1=4.1, z0=2.2, z1=4.8)
VENT_LADO = dict(y0=0.6, y1=3.0, z0=2.2, z1=4.6)  # pared izquierda (x = -5.5)
PUERTA_LAB = dict(x0=7.7, x1=9.7, z1=4.3)        # fachada del lab (y = -1.6)
VENT_LAB = dict(y0=-0.9, y1=1.7, z0=1.4, z1=3.9)  # pared derecha del lab (x = 11.2)
CLARABOYA = dict(x0=8.1, x1=9.6, y0=-0.8, y1=0.6)

Z_TECHO = CASA["z1"] + CASA["losa"]               # suelo del techo de la casa (6.65)
Z_TECHO_LAB = LAB["z1"] + LAB["losa"]             # 5.05

BISAGRA_PUERTA = V((-3.38, -4.47, 0.0))           # eje de giro de la puerta principal (vertical)
BISAGRA_LAB = V((7.72, -1.57, 0.0))
SILLA = dict(x=-4.85, y=-5.85, giro=18.0)
CAMARA = dict(x=12.7, y=-5.3, alto=2.9, objetivo=(8.7, -1.6, 2.3))
ESTACION = dict(x=-4.65, y=-3.6)
PARABOLICA = dict(x=-3.4, y=2.75, eje=(0.32, -0.42, 0.85))
DIPOLO = dict(x=4.1, y=3.0)

RECT = L.uv_rect


# ==============================================================================================================
# Ayudas de construcción
# ==============================================================================================================


def tornillo(e, centro, normal, r=0.028, alto=0.014, mat="acero"):
    """Tornillo de cabeza hexagonal (6 lados), con su volumen."""
    # sin tapa de abajo: queda pegada a la chapa y no se ve
    return e.cilindro(centro, r, alto, mat, lados=6, eje=normal, tapas=True, tapa_base=False)


def tornillos_rect(e, c, ancho, alto, normal, derecha, arriba, margen=0.06, r=0.024):
    for sx in (-1, 1):
        for sz in (-1, 1):
            p = V(c) + V(derecha) * (sx * (ancho / 2 - margen)) + V(arriba) * (sz * (alto / 2 - margen))
            tornillo(e, p, normal, r=r)


def letrero(e, centro, ancho, alto, normal, nombre, grosor=0.02, mat_canto="metal_oscuro"):
    """Placa con letrero de la hoja de letreros en la cara que mira hacia `normal` (eje ±X o ±Y)."""
    n = V(normal)
    d = {(-1, 0): "-x", (1, 0): "+x", (0, -1): "-y", (0, 1): "+y"}[(round(n.x), round(n.y))]
    if d in ("-y", "+y"):
        tam = (ancho, grosor, alto)
    else:
        tam = (grosor, ancho, alto)
    return e.caja(centro, tam, mat_canto, mats={d: "letrero"}, decal=d, rect=RECT(nombre))


def canaleta(e, a, b, n, ancho=0.26, fondo=0.13, clips=0.5, quitar_atras=True, tapa=True):
    """
    Canaleta metálica recta de `a` a `b` apoyada en una superficie de normal `n`: cuerpo galvanizado, tapa de
    aluminio y abrazaderas cada `clips` studs. a y b están sobre la superficie.
    """
    a, b, n = V(a), V(b), V(n).normalized()
    t = (b - a)
    largo = t.length
    t.normalize()
    w = n.cross(t)
    giro = Matrix((t, w, n)).transposed()
    c = (a + b) / 2 + n * (fondo / 2)
    e.caja(c, (largo, ancho, fondo), "galvanizado", giro=giro, quitar=("-z",) if quitar_atras else ())
    if tapa:
        e.caja(c + n * (fondo / 2 + 0.008), (largo, ancho + 0.02, 0.016), "aluminio", giro=giro, quitar=("-z",))
    if clips:
        k = clips / 2
        while k < largo - 0.05:
            p = a + t * k + n * (fondo / 2 + 0.006)
            e.caja(p, (0.05, ancho + 0.05, fondo + 0.04), "metal_oscuro", giro=giro, quitar=("-z",))
            k += clips
    return giro


def etiqueta_cable(e, p, n, w, nombre, ancho=0.3, alto=0.12):
    """Etiqueta pegada a la tapa de una canaleta (en el plano n, con el texto a lo largo de `w`)."""
    n, w = V(n).normalized(), V(w).normalized()
    arriba = n.cross(w)
    giro = Matrix((w, arriba, n)).transposed()
    e.caja(V(p) + n * 0.007, (ancho, alto, 0.012), "aluminio", giro=giro, mats={"+z": "letrero"}, decal="+z",
           rect=RECT(f"et_{nombre}"), quitar=("-z",))


def cable(e, puntos, color="cable_negro", r=0.035, lados=6):
    # los cables finos con 4 lados: a esa escala ya se ven redondos con el sombreado suave
    e.tubo(puntos, r, color, lados=4 if r <= 0.03 else lados)


# ==============================================================================================================
# Casa principal
# ==============================================================================================================


def casa(e, cr):
    C = CASA
    x0, x1, y0, y1, z0, z1, g = C["x0"], C["x1"], C["y0"], C["y1"], C["z0"], C["z1"], C["g"]

    # Cimentación de hormigón nivelado (se ve como un zócalo de 0,5 studs con chaflán)
    e.caja_de((x0 - 0.3, y0 - 0.3, 0.0), (x1 + 0.3, y1 + 0.3, z0), "hormigon", quitar=("-z",), bisel=True)
    # Suelo interior
    e.caja_de((x0 + g, y0 + g, z0), (x1 - g, y1 - g, z0 + 0.02), "interior_suelo", quitar=("-z",))

    P, VF, VL = PUERTA, VENT_FRENTE, VENT_LADO
    # Fachada (y0) con la puerta y la ventana
    e.placa("y", y0, y0 + g, (x0, x1), (z0, z1),
            [(P["x0"], P["x1"], z0, P["z1"]), (VF["x0"], VF["x1"], VF["z0"], VF["z1"])],
            "panel_casa", "interior", cantos=("u0", "u1"))
    # Trasera (y1), lisa
    e.placa("y", y1, y1 - g, (x0, x1), (z0, z1), [], "panel_casa", "interior", cantos=("u0", "u1"))
    # Izquierda (x0) con la ventana lateral, y derecha (x1) lisa (el pasillo al lab la tapa en parte)
    e.placa("x", x0, x0 + g, (y0 + g, y1 - g), (z0, z1), [(VL["y0"], VL["y1"], VL["z0"], VL["z1"])],
            "panel_casa", "interior", cantos=())
    e.placa("x", x1, x1 - g, (y0 + g, y1 - g), (z0, z1), [], "panel_casa", "interior", cantos=())

    # Losa del techo con su canto (remate oscuro) y vuelo de 0,15
    zl = z1 + C["losa"]
    e.caja_de((x0 - 0.15, y0 - 0.15, z1), (x1 + 0.15, y1 + 0.15, zl), "remate",
              mats={"+z": "techo", "-z": "interior"}, bisel=True)
    # Peto alrededor del techo + albardilla de aluminio
    pe = 0.25
    zp = zl + C["peto"]
    for a, b in (((x0 - 0.15, y0 - 0.15), (x1 + 0.15, y0 - 0.15 + pe)),
                 ((x0 - 0.15, y1 + 0.15 - pe), (x1 + 0.15, y1 + 0.15)),
                 ((x0 - 0.15, y0 - 0.15 + pe), (x0 - 0.15 + pe, y1 + 0.15 - pe)),
                 ((x1 + 0.15 - pe, y0 - 0.15 + pe), (x1 + 0.15, y1 + 0.15 - pe))):
        e.caja_de((a[0], a[1], zl), (b[0], b[1], zp), "remate", quitar=("-z", "+z"), bisel=False)
        e.caja_de((a[0] - 0.03, a[1] - 0.03, zp), (b[0] + 0.03, b[1] + 0.03, zp + 0.07), "aluminio", bisel=True)

    # Esquineros verticales
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        e.caja((x, y, (z0 + z1) / 2), (0.34, 0.34, z1 - z0), "remate", bisel=True, quitar=("-z", "+z"))
    # Zócalo metálico (banda oscura abajo) y remate superior, interrumpidos en la puerta
    for za, zb in ((z0, z0 + 0.32), (z1 - 0.32, z1)):
        tramos_frente = [(x0 + 0.17, P["x0"] - 0.2), (P["x1"] + 0.2, x1 - 0.17)] if za == z0 else \
            [(x0 + 0.17, x1 - 0.17)]
        for a, b in tramos_frente:
            e.caja_de((a, y0 - 0.05, za), (b, y0, zb), "remate", quitar=("+y",))
        e.caja_de((x0 + 0.17, y1, za), (x1 - 0.17, y1 + 0.05, zb), "remate", quitar=("-y",))
        e.caja_de((x0 - 0.05, y0 + 0.17, za), (x0, y1 - 0.17, zb), "remate", quitar=("+x",))
        e.caja_de((x1, y0 + 0.17, za), (x1 + 0.05, PASILLO["y0"], zb), "remate", quitar=("-x",))
        e.caja_de((x1, PASILLO["y1"], za), (x1 + 0.05, y1 - 0.17, zb), "remate", quitar=("-x",))

    # Rejillas de ventilación altas en los laterales
    for y in (-2.6, 2.6):
        e.caja((x1 + 0.03, y, 5.4), (0.06, 0.7, 0.32), "remate", mats={"+x": "rejilla"}, decal="+x", quitar=("-x",))
    e.caja((x0 - 0.03, -0.6, 5.4), (0.06, 0.7, 0.32), "remate", mats={"-x": "rejilla"}, decal="-x", quitar=("+x",))

    # Bajante de pluviales en la esquina trasera derecha (con gárgola y abrazaderas)
    bx, by = x1 - 0.55, y1 + 0.2
    e.caja((bx, y1 + 0.2, zl + 0.15), (0.3, 0.45, 0.2), "galvanizado", quitar=("-y",))
    e.cilindro((bx, by, z0 + 0.05), 0.11, zl - z0 - 0.05, "galvanizado", lados=8)
    e.cilindro((bx, by + 0.02, z0), 0.14, 0.12, "galvanizado", lados=8, radio2=0.11)
    for z in (1.6, 3.4, 5.2):
        e.caja((bx, by - 0.04, z), (0.3, 0.3, 0.06), "metal_oscuro", quitar=("-y",))

    trasera(e)
    puerta_principal_marco(e)
    ventana_frente(e, cr)
    ventana_lado(e, cr)
    interior_casa(e)


def trasera(e):
    """Fachada trasera: bomba de calor sobre ménsulas (rejilla de ventilador), con su tubo a la pared y rejillas."""
    y1 = CASA["y1"]
    c = V((-1.8, y1, 1.6))
    for dx in (-0.7, 0.7):
        e.caja(c + V((dx, 0.45, -0.55)), (0.08, 0.9, 0.08), "metal_oscuro")
        e.caja(c + V((dx, 0.03, -0.3)), (0.08, 0.06, 0.6), "metal_oscuro", quitar=("-y",))
    e.caja(c + V((0, 0.5, 0.0)), (1.8, 0.8, 1.05), "panel_lab", bisel=True, mats={"+y": "remate"})
    e.cilindro(c + V((-0.25, 0.9, 0.0)), 0.42, 0.03, "galvanizado", lados=14, eje=(0, 1, 0), mat_tapa="ventilador",
               decal_tapa=True, tapa_base=False)
    e.caja(c + V((0.62, 0.905, 0.0)), (0.36, 0.012, 0.8), "remate", mats={"+y": "rejilla"}, decal="+y",
           quitar=("-y",))
    letrero(e, c + V((0.62, 0.915, 0.47)), 0.3, 0.07, (0, 1), "et_CUADRO", 0.006, "aluminio")
    cable(e, [c + V((0.8, 0.3, -0.3)), c + V((1.05, 0.3, -0.3)), c + V((1.05, 0.04, -0.3))], "cable_gris", 0.05, 6)
    for x in (2.0, 3.6):
        e.caja((x, y1 + 0.03, 5.4), (0.7, 0.06, 0.32), "remate", mats={"+y": "rejilla"}, decal="+y",
               quitar=("-y",))


def puerta_principal_marco(e):
    """Cerco, tapajuntas, umbral, escalón de tramex y las mitades fijas de las bisagras."""
    P = PUERTA
    y0, yi = CASA["y0"], CASA["y0"] + CASA["g"]
    z0, z1 = CASA["z0"], P["z1"]
    # tapajuntas sobre la fachada
    e.caja_de((P["x0"] - 0.22, y0 - 0.06, z0), (P["x0"], y0, z1 + 0.2), "metal_oscuro", quitar=("+y",), bisel=True)
    e.caja_de((P["x1"], y0 - 0.06, z0), (P["x1"] + 0.22, y0, z1 + 0.2), "metal_oscuro", quitar=("+y",), bisel=True)
    e.caja_de((P["x0"], y0 - 0.06, z1), (P["x1"], y0, z1 + 0.2), "metal_oscuro", quitar=("+y",), bisel=True)
    # forro del hueco
    e.caja_de((P["x0"], y0, z0), (P["x0"] + 0.06, yi, z1), "metal_oscuro", quitar=("-x",))
    e.caja_de((P["x1"] - 0.06, y0, z0), (P["x1"], yi, z1), "metal_oscuro", quitar=("+x",))
    e.caja_de((P["x0"], y0, z1 - 0.06), (P["x1"], yi, z1), "metal_oscuro", quitar=("+z",))
    # umbral de aluminio
    e.caja_de((P["x0"], y0 - 0.08, z0), (P["x1"], yi, z0 + 0.035), "aluminio")
    # escalón de tramex con canto de aviso
    e.caja_de((P["x0"] - 0.35, y0 - 0.95, 0.06), (P["x1"] + 0.35, y0 - 0.3, 0.28), "metal_oscuro",
              mats={"+z": "rejilla_suelo"}, quitar=("-z",), bisel=True)
    e.caja_de((P["x0"] - 0.35, y0 - 0.3, 0.06), (P["x1"] + 0.35, y0, 0.5), "hormigon", quitar=("-z", "+y"))
    e.caja_de((P["x0"] - 0.35, y0 - 0.99, 0.2), (P["x1"] + 0.35, y0 - 0.95, 0.28), "aviso", quitar=("+y",))
    # Bisagras: placas fijas sobre el tapajuntas + nudillos de arriba y abajo
    bx, by = BISAGRA_PUERTA.x, BISAGRA_PUERTA.y
    for zc in (1.3, 4.7):
        e.caja((P["x0"] - 0.12, y0 - 0.075, zc), (0.2, 0.03, 0.62), "metal_oscuro", quitar=("+y",))
        for dz in (-0.235, 0.235):
            e.cilindro((bx, by, zc + dz - 0.115), 0.065, 0.23, "metal_oscuro", lados=8, bisel=False)
        e.cilindro((bx, by, zc + 0.35), 0.035, 0.03, "acero", lados=6)
        e.cilindro((bx, by, zc - 0.38), 0.035, 0.03, "acero", lados=6)
        for dz in (-0.2, 0.0, 0.2):
            tornillo(e, (P["x0"] - 0.16, y0 - 0.09, zc + dz), (0, -1, 0))


def ventana(e, cr, eje, a_ext, a_int, u0, u1, z0, z1, perfil=0.13, prof=0.3, vidrio_doble=False,
            montante=False):
    """Marco metálico preciso dentro del hueco y cristal con grosor (en la malla de cristal)."""
    s = 1.0 if a_int > a_ext else -1.0  # hacia dentro

    def caja(au, bu, az, bz, aa, ba, mat, **kw):
        if eje == "y":
            mn, mx = (au, min(aa, ba), az), (bu, max(aa, ba), bz)
        else:
            mn, mx = (min(aa, ba), au, az), (max(aa, ba), bu, bz)
        return e.caja_de(mn, mx, mat, **kw)

    def caja_c(au, bu, az, bz, aa, ba):
        if eje == "y":
            cr.caja_de((au, min(aa, ba), az), (bu, max(aa, ba), bz), "cristal")
        else:
            cr.caja_de((min(aa, ba), au, az), (max(aa, ba), bu, bz), "cristal")

    fa = a_ext + s * 0.06
    fb = fa + s * prof
    caja(u0, u0 + perfil, z0, z1, fa, fb, "metal_oscuro", bisel=True)
    caja(u1 - perfil, u1, z0, z1, fa, fb, "metal_oscuro", bisel=True)
    caja(u0 + perfil, u1 - perfil, z0, z0 + perfil, fa, fb, "metal_oscuro", bisel=True)
    caja(u0 + perfil, u1 - perfil, z1 - perfil, z1, fa, fb, "metal_oscuro", bisel=True)
    if montante:
        um = (u0 + u1) / 2
        caja(um - 0.035, um + 0.035, z0 + perfil, z1 - perfil, fa + s * 0.04, fb - s * 0.04, "metal_oscuro")
    # junquillos (el perfil que pisa el cristal) por fuera
    j = 0.035
    m = fa + s * prof * 0.45
    for au, bu, az, bz in ((u0 + perfil, u0 + perfil + j, z0 + perfil, z1 - perfil),
                           (u1 - perfil - j, u1 - perfil, z0 + perfil, z1 - perfil),
                           (u0 + perfil + j, u1 - perfil - j, z0 + perfil, z0 + perfil + j),
                           (u0 + perfil + j, u1 - perfil - j, z1 - perfil - j, z1 - perfil)):
        caja(au, bu, az, bz, m - s * 0.06, m, "goma")
    if vidrio_doble:
        for c in (m, m + s * 0.18):
            caja_c(u0 + perfil, u1 - perfil, z0 + perfil, z1 - perfil, c, c + s * 0.05)
        # separador oscuro entre los dos cristales
        for au, bu, az, bz in ((u0 + perfil, u0 + perfil + 0.03, z0 + perfil, z1 - perfil),
                               (u1 - perfil - 0.03, u1 - perfil, z0 + perfil, z1 - perfil),
                               (u0 + perfil, u1 - perfil, z0 + perfil, z0 + perfil + 0.03),
                               (u0 + perfil, u1 - perfil, z1 - perfil - 0.03, z1 - perfil)):
            caja(au, bu, az, bz, m + s * 0.05, m + s * 0.18, "remate")
    else:
        caja_c(u0 + perfil, u1 - perfil, z0 + perfil, z1 - perfil, m, m + s * 0.06)
    # vierteaguas de aluminio con goterón
    caja(u0 - 0.15, u1 + 0.15, z0 - 0.1, z0, a_ext - s * 0.24, a_ext + s * 0.1, "aluminio", bisel=True)
    caja(u0 - 0.15, u1 + 0.15, z0 - 0.16, z0 - 0.1, a_ext - s * 0.24, a_ext - s * 0.2, "aluminio")


def ventana_frente(e, cr):
    VF = VENT_FRENTE
    y0 = CASA["y0"]
    ventana(e, cr, "y", y0, y0 + CASA["g"], VF["x0"], VF["x1"], VF["z0"], VF["z1"], montante=True)
    # Persiana automática: guías y caja del mecanismo
    for x in (VF["x0"] + 0.06, VF["x1"] - 0.06):
        e.caja((x, y0 - 0.055, (VF["z0"] + VF["z1"]) / 2 + 0.3), (0.1, 0.11, VF["z1"] - VF["z0"] + 0.6),
               "aluminio", quitar=("+y",))
    e.caja_de((VF["x0"] - 0.1, y0 - 0.38, VF["z1"] + 0.05), (VF["x1"] + 0.1, y0, VF["z1"] + 0.62), "remate",
              quitar=("+y",), bisel=True)
    e.caja_de((VF["x0"] + 0.05, y0 - 0.3, VF["z1"] + 0.035), (VF["x1"] - 0.05, y0 - 0.06, VF["z1"] + 0.05),
              "goma")
    # motor: placa «AUTO» y LED de estado en el lateral de la caja
    letrero(e, (VF["x1"] - 0.35, y0 - 0.39, VF["z1"] + 0.33), 0.36, 0.14, (0, -1), "auto_persiana", 0.012)
    e.caja((VF["x1"] - 0.08, y0 - 0.39, VF["z1"] + 0.33), (0.05, 0.02, 0.05), "led_verde")
    for x in (VF["x0"] + 0.1, VF["x1"] - 0.1):
        tornillo(e, (x, y0 - 0.38, VF["z1"] + 0.33), (0, -1, 0))


def persiana(p):
    """Persiana bajada un 35 %: lamas de perfil ondulado (extruido) y barra final de aluminio."""
    VF = VENT_FRENTE
    y = CASA["y0"] - 0.055
    z_top, z_bot = VF["z1"] + 0.06, VF["z1"] - 0.86
    n = 10
    paso = (z_top - z_bot) / n
    frente, atras = [], []
    for i in range(n + 1):
        z = z_top - i * paso
        frente.append((y - 0.02, z))
        if i < n:
            frente.append((y - 0.045, z - paso * 0.5))
    for yy, z in reversed(frente):
        atras.append((yy + 0.022, z))
    poly = frente + atras
    mtx = K.marco((0, 0, 0), (1, 0, 0), (0, 1, 0))  # local x→y, y→z, z→x
    pol = [(yy, zz) for yy, zz in poly]
    p.extruir(pol, VF["x0"] + 0.11, VF["x1"] - 0.11, mtx, "aluminio")
    p.caja_de((VF["x0"] + 0.11, y - 0.05, z_bot - 0.08), (VF["x1"] - 0.11, y + 0.03, z_bot), "metal_oscuro",
              bisel=True)
    p.caja_de((VF["x0"] + 1.3, y - 0.09, z_bot - 0.06), (VF["x0"] + 1.9, y - 0.05, z_bot - 0.02), "goma")


def ventana_lado(e, cr):
    VL = VENT_LADO
    x0 = CASA["x0"]
    ventana(e, cr, "x", x0, x0 + CASA["g"], VL["y0"], VL["y1"], VL["z0"], VL["z1"])


def interior_casa(e):
    """Lo que se ve por las ventanas: mesa con monitor (frente) y estantería con archivadores (lateral)."""
    yi = CASA["y0"] + CASA["g"]
    # mesa
    e.caja_de((1.2, yi + 0.1, 1.85), (3.8, yi + 1.0, 1.95), "remate", bisel=True)
    for x in (1.3, 3.65):
        e.caja_de((x, yi + 0.2, 0.52), (x + 0.08, yi + 0.9, 1.85), "metal_oscuro")
    # monitor girado hacia la calle (de lado), con la pantalla encendida
    giro = K.rot(-58)
    c = V((2.9, yi + 0.55, 2.45))
    e.caja(c, (0.95, 0.06, 0.58), "remate", giro=giro)
    e.caja(c + giro @ V((0, -0.035, 0)), (0.88, 0.012, 0.5), "remate", giro=giro, mats={"-y": "letrero"},
           decal="-y", rect=RECT("monitor"))
    e.caja(c + V((0, 0, -0.38)), (0.08, 0.08, 0.2), "metal_oscuro")
    e.caja(c + V((0, 0, -0.49)), (0.35, 0.25, 0.03), "metal_oscuro")
    # luz del techo (panel LED: en el atlas de emisión)
    e.caja((0.0, -1.0, CASA["z1"] - 0.03), (2.2, 0.8, 0.04), "led_blanco", quitar=("+z",))
    # estantería con archivadores ordenados por color
    xi, yb = CASA["x0"] + CASA["g"], CASA["y1"] - CASA["g"]
    e.caja_de((xi + 0.3, yb - 0.45, 0.52), (xi + 0.36, yb, 3.9), "metal_oscuro")
    e.caja_de((xi + 2.4, yb - 0.45, 0.52), (xi + 2.46, yb, 3.9), "metal_oscuro")
    colores = ["cable_azul", "cable_azul", "cable_gris", "cable_gris", "cable_negro", "cable_rojo",
               "cable_amarillo"]
    for k, z in enumerate((1.2, 2.2, 3.2)):
        e.caja_de((xi + 0.36, yb - 0.45, z - 0.05), (xi + 2.4, yb, z), "galvanizado")
        x = xi + 0.42
        for i, colr in enumerate(colores[: 7 - k]):
            e.caja_de((x, yb - 0.4, z), (x + 0.24, yb - 0.05, z + 0.72), colr, quitar=("-z", "+y"))
            x += 0.27


# ==============================================================================================================
# Pasillo y laboratorio
# ==============================================================================================================


def pasillo(e, cr):
    Pa = PASILLO
    e.caja_de((Pa["x0"], Pa["y0"] - 0.15, 0.0), (LAB["x0"] - 0.3, Pa["y1"] + 0.15, Pa["z0"]), "hormigon",
              quitar=("-z",))
    e.caja_de((Pa["x0"], Pa["y0"], Pa["z0"]), (LAB["x0"], Pa["y1"], Pa["z1"]), "panel_pasillo",
              quitar=("-x", "+x", "-z"))
    e.caja_de((Pa["x0"], Pa["y0"] - 0.12, Pa["z1"]), (LAB["x0"], Pa["y1"] + 0.12, Pa["z1"] + 0.25), "remate",
              mats={"+z": "techo"}, quitar=("-x", "+x"), bisel=True)
    # costillas de unión en los dos extremos
    for x in (Pa["x0"] + 0.1, LAB["x0"] - 0.1):
        e.caja_de((x - 0.08, Pa["y0"] - 0.06, Pa["z0"]), (x + 0.08, Pa["y0"], Pa["z1"]), "remate", quitar=("+y",))
        e.caja_de((x - 0.08, Pa["y1"], Pa["z0"]), (x + 0.08, Pa["y1"] + 0.06, Pa["z1"]), "remate", quitar=("-y",))
    # ojo de buey en el pasillo
    c = V(((Pa["x0"] + LAB["x0"]) / 2, Pa["y0"], 2.4))
    e.toro(c + V((0, -0.035, 0)), 0.33, 0.06, "metal_oscuro", eje=(0, -1, 0), n1=14, n2=4)
    cr.cilindro(c + V((0, 0.02, 0)), 0.3, -0.06, "cristal", lados=14, eje=(0, 1, 0))
    for k in range(6):
        a = math.tau * k / 6
        tornillo(e, c + V((math.cos(a) * 0.33, -0.08, math.sin(a) * 0.33)), (0, -1, 0), r=0.02)


def laboratorio(e, cr):
    Lb = LAB
    x0, x1, y0, y1, z0, z1, g = Lb["x0"], Lb["x1"], Lb["y0"], Lb["y1"], Lb["z0"], Lb["z1"], Lb["g"]
    e.caja_de((x0 - 0.3, y0 - 0.3, 0.0), (x1 + 0.3, y1 + 0.3, z0), "hormigon", quitar=("-z",), bisel=True)
    e.caja_de((x0 + g, y0 + g, z0), (x1 - g, y1 - g, z0 + 0.02), "interior_suelo", quitar=("-z",))
    PL, VL = PUERTA_LAB, VENT_LAB
    e.placa("y", y0, y0 + g, (x0, x1), (z0, z1), [(PL["x0"], PL["x1"], z0, PL["z1"])], "panel_lab", "interior",
            cantos=("u0", "u1"))
    e.placa("y", y1, y1 - g, (x0, x1), (z0, z1), [], "panel_lab", "interior", cantos=("u0", "u1"))
    e.placa("x", x0, x0 + g, (y0 + g, y1 - g), (z0, z1), [], "panel_lab", "interior", cantos=())
    e.placa("x", x1, x1 - g, (y0 + g, y1 - g), (z0, z1), [(VL["y0"], VL["y1"], VL["z0"], VL["z1"])],
            "panel_lab", "interior", cantos=())
    # Losa con el hueco de la claraboya
    CB = CLARABOYA
    zl = z1 + Lb["losa"]
    e.placa("z", zl, z1, (x0 - 0.12, x1 + 0.12), (y0 - 0.12, y1 + 0.12),
            [(CB["x0"], CB["x1"], CB["y0"], CB["y1"])], "techo", "interior", mat_canto="remate", bisel=True)
    pe = 0.2
    zp = zl + Lb["peto"]
    for a, b in (((x0 - 0.12, y0 - 0.12), (x1 + 0.12, y0 - 0.12 + pe)),
                 ((x0 - 0.12, y1 + 0.12 - pe), (x1 + 0.12, y1 + 0.12)),
                 ((x0 - 0.12, y0 - 0.12 + pe), (x0 - 0.12 + pe, y1 + 0.12 - pe)),
                 ((x1 + 0.12 - pe, y0 - 0.12 + pe), (x1 + 0.12, y1 + 0.12 - pe))):
        e.caja_de((a[0], a[1], zl), (b[0], b[1], zp), "remate", quitar=("-z", "+z"))
        e.caja_de((a[0] - 0.03, a[1] - 0.03, zp), (b[0] + 0.03, b[1] + 0.03, zp + 0.06), "aluminio", bisel=True)
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        e.caja((x, y, (z0 + z1) / 2), (0.3, 0.3, z1 - z0), "remate", bisel=True, quitar=("-z", "+z"))
    # zócalo
    e.caja_de((x0 + 0.15, y0 - 0.05, z0), (PL["x0"] - 0.2, y0, z0 + 0.28), "remate", quitar=("+y",))
    e.caja_de((PL["x1"] + 0.2, y0 - 0.05, z0), (x1 - 0.15, y0, z0 + 0.28), "remate", quitar=("+y",))
    e.caja_de((x1, y0 + 0.15, z0), (x1 + 0.05, y1 - 0.15, z0 + 0.28), "remate", quitar=("-x",))
    e.caja_de((x0 + 0.15, y1, z0), (x1 - 0.15, y1 + 0.05, z0 + 0.28), "remate", quitar=("-y",))

    puerta_lab_marco(e)
    ventana_lab(e, cr)
    claraboya(e, cr)
    ventilacion_lab(e)
    interior_lab(e)


def puerta_lab_marco(e):
    PL = PUERTA_LAB
    y0, yi = LAB["y0"], LAB["y0"] + LAB["g"]
    z0, z1 = LAB["z0"], PL["z1"]
    e.caja_de((PL["x0"] - 0.18, y0 - 0.05, z0), (PL["x0"], y0, z1 + 0.16), "metal_oscuro", quitar=("+y",), bisel=True)
    e.caja_de((PL["x1"], y0 - 0.05, z0), (PL["x1"] + 0.18, y0, z1 + 0.16), "metal_oscuro", quitar=("+y",), bisel=True)
    e.caja_de((PL["x0"], y0 - 0.05, z1), (PL["x1"], y0, z1 + 0.16), "metal_oscuro", quitar=("+y",), bisel=True)
    e.caja_de((PL["x0"], y0, z0), (PL["x0"] + 0.05, yi, z1), "metal_oscuro", quitar=("-x",))
    e.caja_de((PL["x1"] - 0.05, y0, z0), (PL["x1"], yi, z1), "metal_oscuro", quitar=("+x",))
    e.caja_de((PL["x0"], y0, z1 - 0.05), (PL["x1"], yi, z1), "metal_oscuro", quitar=("+z",))
    e.caja_de((PL["x0"], y0 - 0.06, z0), (PL["x1"], yi, z0 + 0.03), "aluminio")
    # escalón
    e.caja_de((PL["x0"] - 0.2, y0 - 0.75, 0.06), (PL["x1"] + 0.2, y0 - 0.3, 0.2), "metal_oscuro",
              mats={"+z": "rejilla_suelo"}, quitar=("-z",), bisel=True)
    e.caja_de((PL["x0"] - 0.2, y0 - 0.79, 0.12), (PL["x1"] + 0.2, y0 - 0.75, 0.2), "aviso", quitar=("+y",))
    # bisagras fijas
    bx, by = BISAGRA_LAB.x, BISAGRA_LAB.y
    for zc in (1.05, 3.6):
        e.caja((PL["x0"] - 0.1, y0 - 0.065, zc), (0.16, 0.03, 0.54), "metal_oscuro", quitar=("+y",))
        for dz in (-0.2, 0.2):
            e.cilindro((bx, by, zc + dz - 0.1), 0.055, 0.2, "metal_oscuro", lados=8)
        for dz in (-0.17, 0.17):
            tornillo(e, (PL["x0"] - 0.12, y0 - 0.08, zc + dz), (0, -1, 0))
    # tira de mantenimiento junto al marco
    letrero(e, (PL["x1"] + 0.55, y0 - 0.012, 3.4), 0.6, 0.11, (0, -1), "mantenimiento", 0.012, "aluminio")


def ventana_lab(e, cr):
    """Ventana de observación grande: doble cristal grueso y marco reforzado atornillado."""
    VL = VENT_LAB
    x1 = LAB["x1"]
    ventana(e, cr, "x", x1, x1 - LAB["g"], VL["y0"], VL["y1"], VL["z0"], VL["z1"], perfil=0.16, prof=0.34,
            vidrio_doble=True)
    # marco exterior de refuerzo (pletina atornillada alrededor del hueco)
    a = 0.2
    for y0, y1, z0, z1 in ((VL["y0"] - a, VL["y0"], VL["z0"] - a, VL["z1"] + a),
                           (VL["y1"], VL["y1"] + a, VL["z0"] - a, VL["z1"] + a),
                           (VL["y0"], VL["y1"], VL["z1"], VL["z1"] + a),
                           (VL["y0"], VL["y1"], VL["z0"] - a, VL["z0"])):
        e.caja_de((x1, y0, z0), (x1 + 0.06, y1, z1), "metal_oscuro", quitar=("-x",), bisel=True)
    for y in (VL["y0"] - 0.1, VL["y1"] + 0.1):
        z = VL["z0"] - 0.1
        while z <= VL["z1"] + 0.11:
            tornillo(e, (x1 + 0.06, y, z), (1, 0, 0))
            z += 0.75
    for z in (VL["z0"] - 0.1, VL["z1"] + 0.1):
        y = VL["y0"] + 0.55
        while y < VL["y1"] - 0.3:
            tornillo(e, (x1 + 0.06, y, z), (1, 0, 0))
            y += 0.75


def claraboya(e, cr):
    CB = CLARABOYA
    zl = Z_TECHO_LAB
    # brocal de aluminio oscuro alrededor del hueco
    t = 0.1
    for a, b in (((CB["x0"] - t, CB["y0"] - t), (CB["x1"] + t, CB["y0"])),
                 ((CB["x0"] - t, CB["y1"]), (CB["x1"] + t, CB["y1"] + t)),
                 ((CB["x0"] - t, CB["y0"]), (CB["x0"], CB["y1"])),
                 ((CB["x1"], CB["y0"]), (CB["x1"] + t, CB["y1"]))):
        e.caja_de((a[0], a[1], LAB["z1"]), (b[0], b[1], zl + 0.32), "metal_oscuro", bisel=True)
    # cristal inclinado (vierte hacia delante) sobre el brocal, con su marco
    giro = K.rot(-6, "X")
    c = V(((CB["x0"] + CB["x1"]) / 2, (CB["y0"] + CB["y1"]) / 2, zl + 0.37))
    cr.caja(c, (CB["x1"] - CB["x0"] + 0.1, CB["y1"] - CB["y0"] + 0.1, 0.06), "cristal", giro=giro)
    for dx, dy, sx, sy in ((0, -1, 1, 0), (0, 1, 1, 0), (-1, 0, 0, 1), (1, 0, 0, 1)):
        w = (CB["x1"] - CB["x0"]) / 2 + 0.12
        h = (CB["y1"] - CB["y0"]) / 2 + 0.12
        p = c + giro @ V((dx * w, dy * h, 0.02))
        tam = (2 * w + 0.1, 0.08, 0.08) if sx else (0.08, 2 * h, 0.08)
        e.caja(p, tam, "aluminio", giro=giro)


def ventilacion_lab(e):
    """Unidad de ventilación con extractor en el techo del lab."""
    zl = Z_TECHO_LAB
    c = V((10.3, 1.45, zl))
    for dx in (-0.45, 0.45):
        e.caja(c + V((dx, 0, 0.06)), (0.1, 1.0, 0.12), "galvanizado")
    e.caja_de(c + V((-0.6, -0.5, 0.12)), c + V((0.6, 0.5, 0.78)), "panel_lab", bisel=True,
              mats={"-y": "remate"})
    e.caja(c + V((0, -0.505, 0.45)), (0.9, 0.02, 0.45), "remate", mats={"-y": "rejilla"}, decal="-y")
    e.caja(c + V((0.605, 0, 0.45)), (0.02, 0.7, 0.45), "remate", mats={"+x": "rejilla"}, decal="+x")
    # extractor: aro, rejilla redonda y cubo central
    e.cilindro(c + V((0, 0.05, 0.78)), 0.42, 0.1, "galvanizado", lados=16, mat_tapa="ventilador", decal_tapa=True)
    e.cilindro(c + V((0, 0.05, 0.88)), 0.09, 0.05, "metal_oscuro", lados=8)
    letrero(e, c + V((-0.35, -0.515, 0.22)), 0.4, 0.15, (0, -1), "et_LAB", 0.01)


def interior_lab(e):
    """Estantería con equipos electrónicos frente a la ventana de observación: se ve desde fuera."""
    xi = LAB["x0"] + LAB["g"]
    y0, y1 = -0.8, 1.6
    d = 0.75
    for y in (y0, y1):
        for x in (xi + 0.04, xi + d - 0.04):
            e.caja((x, y, 2.3), (0.06, 0.06, 3.9), "metal_oscuro")
    tablas = (1.3, 2.3, 3.3, 4.2)
    for z in tablas:
        e.caja_de((xi, y0 - 0.03, z - 0.05), (xi + d, y1 + 0.03, z), "galvanizado")
    z = tablas[0]
    # balda 1: osciloscopio y rack de LEDs
    e.caja_de((xi + 0.1, -0.7, z), (xi + 0.65, 0.2, z + 0.55), "remate", bisel=True)
    e.caja((xi + 0.66, -0.25, z + 0.3), (0.012, 0.5, 0.36), "remate", mats={"+x": "letrero"}, decal="+x",
           rect=RECT("osciloscopio"))
    for k in range(3):
        e.cilindro((xi + 0.65, 0.12, z + 0.12 + k * 0.13), 0.03, 0.04, "goma", lados=6, eje=(1, 0, 0))
    e.caja_de((xi + 0.05, 0.35, z), (xi + 0.6, 1.45, z + 0.42), "remate", mats={"+x": "leds_equipo"}, decal="+x")
    z = tablas[1]
    # balda 2: bobinas de cobre y placas de circuito en su soporte
    for y in (-0.5, 0.05):
        e.caja((xi + 0.35, y, z + 0.04), (0.42, 0.42, 0.08), "metal_oscuro")
        e.toro((xi + 0.35, y, z + 0.19), 0.15, 0.07, "cobre", eje=(0, 0, 1), n1=10, n2=4)
        e.cilindro((xi + 0.35, y, z + 0.08), 0.05, 0.3, "metal_oscuro", lados=6)
    e.caja((xi + 0.35, 0.95, z + 0.03), (0.5, 1.0, 0.06), "metal_oscuro")
    for k in range(4):
        yb = 0.55 + k * 0.26
        e.caja((xi + 0.35, yb, z + 0.25), (0.42, 0.02, 0.4), "remate", mats={"-y": "pcb", "+y": "pcb"},
               decal=("-y", "+y"))
        e.caja((xi + 0.4, yb - 0.02, z + 0.3), (0.1, 0.02, 0.08), "goma")
    z = tablas[2]
    # balda 3: segundo equipo de LEDs y una bobina alta (tipo Tesla, pequeña)
    e.caja_de((xi + 0.08, -0.7, z), (xi + 0.6, 0.35, z + 0.45), "remate", mats={"+x": "leds_equipo"}, decal="+x")
    e.cilindro((xi + 0.35, 1.0, z), 0.14, 0.06, "metal_oscuro", lados=10)
    e.cilindro((xi + 0.35, 1.0, z + 0.06), 0.08, 0.5, "cobre", lados=10)
    e.toro((xi + 0.35, 1.0, z + 0.62), 0.1, 0.04, "aluminio", n1=10, n2=5)
    # cable ordenado entre equipos
    cable(e, [(xi + 0.62, 1.3, tablas[0] + 0.42), (xi + 0.7, 1.3, tablas[0] + 0.5), (xi + 0.7, 1.3, tablas[1]),
              (xi + 0.6, 1.25, tablas[1] + 0.02)], "cable_azul", 0.02, 5)
    # panel de luz del techo del lab
    e.caja((9.2, 0.4 + 0.6, LAB["z1"] - 0.03), (1.4, 0.5, 0.04), "led_blanco")


# ==============================================================================================================
# Puertas (piezas separadas, con el pivote en las bisagras)
# ==============================================================================================================


def cerradura(p, x, y_cara, z_base, mirada=-1.0, con_lector=True):
    """Cerradura electrónica: cuerpo, teclado numérico, lector de tarjeta, LED y manilla."""
    s = mirada
    p.caja((x, y_cara + s * 0.04, z_base + 0.65), (0.4, 0.08, 1.3), "metal_oscuro", bisel=True)
    p.caja((x, y_cara + s * 0.09, z_base + 0.95), (0.3, 0.02, 0.46), "metal_oscuro", mats={"-y": "letrero"},
           decal="-y", rect=RECT("teclado"))
    if con_lector:
        p.caja((x, y_cara + s * 0.09, z_base + 0.55), (0.3, 0.02, 0.14), "metal_oscuro", mats={"-y": "letrero"},
               decal="-y", rect=RECT("lector"))
    p.caja((x + 0.14, y_cara + s * 0.085, z_base + 1.24), (0.04, 0.02, 0.04), "led_verde")
    # manilla de palanca
    zm = z_base + 0.28
    p.cilindro((x, y_cara + s * 0.08, zm), 0.075, 0.05, "acero", lados=10, eje=(0, s, 0))
    p.tubo([(x, y_cara + s * 0.12, zm), (x, y_cara + s * 0.2, zm), (x - 0.48, y_cara + s * 0.2, zm - 0.02)], 0.034,
           "acero", lados=6)


def puerta_principal(p):
    P = PUERTA
    y_cara = -4.40
    p.caja_de((P["x0"] + 0.07, y_cara, CASA["z0"] + 0.06), (P["x1"] - 0.07, y_cara + 0.18, P["z1"] - 0.07),
              "puerta", bisel=True)
    xm = (P["x0"] + P["x1"]) / 2
    # zócalo de acero cepillado y burlete
    p.caja_de((P["x0"] + 0.15, y_cara - 0.012, CASA["z0"] + 0.12), (P["x1"] - 0.15, y_cara, CASA["z0"] + 0.75),
              "aluminio")
    p.caja_de((P["x0"] + 0.1, y_cara + 0.02, CASA["z0"] + 0.03), (P["x1"] - 0.1, y_cara + 0.16, CASA["z0"] + 0.06),
              "goma")
    # cerradura electrónica en el lado contrario a las bisagras
    cerradura(p, P["x1"] - 0.42, y_cara, 2.4)
    # placa con el nombre y sus cuatro tornillos
    c = V((xm - 0.35, y_cara - 0.012, 4.32))
    letrero(p, c, 1.3, 0.36, (0, -1), "placa_nombre", 0.024, "acero")
    tornillos_rect(p, c + V((0, -0.012, 0)), 1.3, 0.36, (0, -1, 0), (1, 0, 0), (0, 0, 1), 0.07, 0.022)
    # bisagras: pletinas en la hoja y nudillo central
    bx, by = BISAGRA_PUERTA.x, BISAGRA_PUERTA.y
    for zc in (1.3, 4.7):
        p.caja_de((P["x0"] + 0.03, y_cara - 0.03, zc - 0.11), (P["x0"] + 0.85, y_cara, zc + 0.11), "metal_oscuro",
                  bisel=True)
        p.cilindro((bx, by, zc - 0.115), 0.065, 0.23, "metal_oscuro", lados=8)
        for dx in (0.3, 0.55, 0.78):
            tornillo(p, (P["x0"] + dx, y_cara - 0.03, zc), (0, -1, 0))
    # manilla interior
    p.tubo([(P["x1"] - 0.42, y_cara + 0.18, 2.68), (P["x1"] - 0.42, y_cara + 0.3, 2.68),
            (P["x1"] - 0.85, y_cara + 0.3, 2.66)], 0.03, "acero", lados=6)


def puerta_lab(p):
    PL = PUERTA_LAB
    y_cara = -1.50
    p.caja_de((PL["x0"] + 0.07, y_cara, LAB["z0"] + 0.05), (PL["x1"] - 0.07, y_cara + 0.16, PL["z1"] - 0.06),
              "puerta", bisel=True)
    xm = (PL["x0"] + PL["x1"]) / 2
    p.caja_de((PL["x0"] + 0.1, y_cara + 0.02, LAB["z0"] + 0.02), (PL["x1"] - 0.1, y_cara + 0.14, LAB["z0"] + 0.05),
              "goma")
    # ojo de buey: aro atornillado y cristal oscuro (opaco: la puerta se mueve entera)
    c = V((xm - 0.15, y_cara, 3.25))
    p.toro(c + V((0, -0.03, 0)), 0.36, 0.065, "metal_oscuro", eje=(0, -1, 0), n1=12, n2=4)
    p.cilindro(c + V((0, 0.0, 0)), 0.31, 0.035, "cristal_oscuro", lados=12, eje=(0, -1, 0), tapa_base=False)
    for k in range(8):
        a = math.tau * (k + 0.5) / 8
        tornillo(p, c + V((math.cos(a) * 0.36, -0.09, math.sin(a) * 0.36)), (0, -1, 0), r=0.02)
    # cartel
    letrero(p, (xm - 0.3, y_cara - 0.012, 2.4), 1.05, 0.36, (0, -1), "cartel_lab", 0.024, "aluminio")
    tornillos_rect(p, V((xm - 0.3, y_cara - 0.024, 2.4)), 1.05, 0.36, (0, -1, 0), (1, 0, 0), (0, 0, 1), 0.06, 0.02)
    cerradura(p, PL["x1"] - 0.35, y_cara, 1.7)
    bx, by = BISAGRA_LAB.x, BISAGRA_LAB.y
    for zc in (1.05, 3.6):
        p.caja_de((PL["x0"] + 0.03, y_cara - 0.03, zc - 0.09), (PL["x0"] + 0.7, y_cara, zc + 0.09), "metal_oscuro",
                  bisel=True)
        p.cilindro((bx, by, zc - 0.1), 0.055, 0.2, "metal_oscuro", lados=8)
        for dx in (0.3, 0.55):
            tornillo(p, (PL["x0"] + dx, y_cara - 0.03, zc), (0, -1, 0))


# ==============================================================================================================
# Techo de la casa: paneles solares, caja de distribución, bandejas de cables
# ==============================================================================================================


def panel_solar(e, c, ancho, largo, incl, mat_cel, altura_frente=0.25, z_apoyo=None, etiqueta=None):
    """
    Panel solar con células, marco de aluminio y soportes inclinados. `c` = centro del lado delantero del panel en
    el suelo (x, y, z_apoyo). Mira hacia -Y con la inclinación `incl` (grados).
    """
    t = math.radians(incl)
    R = K.rot(incl, "X")
    z_apoyo = c[2] if z_apoyo is None else z_apoyo
    # centro del panel
    centro = V((c[0], c[1], z_apoyo + altura_frente)) + R @ V((0, largo / 2, 0.06))
    e.caja(centro, (ancho - 0.1, largo - 0.1, 0.04), "panel_trasero", giro=R, mats={"+z": mat_cel}, decal="+z")
    for sy in (-1, 1):
        e.caja(centro + R @ V((0, sy * (largo / 2 - 0.035), -0.02)), (ancho, 0.07, 0.1), "aluminio", giro=R,
               bisel=True)
    for sx in (-1, 1):
        e.caja(centro + R @ V((sx * (ancho / 2 - 0.035), 0, -0.02)), (0.07, largo - 0.14, 0.1), "aluminio", giro=R,
               bisel=True)
    # caja de conexiones detrás
    cj = centro + R @ V((0, largo * 0.2, -0.1))
    e.caja(cj, (0.32, 0.22, 0.08), "goma", giro=R)
    # patas: delanteras cortas, traseras largas, sobre carriles
    y_front = c[1]
    y_back = c[1] + largo * math.cos(t)
    h_back = altura_frente + largo * math.sin(t)
    for sx in (-1, 1):
        x = c[0] + sx * (ancho / 2 - 0.35)
        e.caja_de((x - 0.04, y_front + 0.04, z_apoyo + 0.08), (x + 0.04, y_front + 0.12, z_apoyo + altura_frente + 0.02),
                  "aluminio")
        e.caja_de((x - 0.04, y_back - 0.2, z_apoyo + 0.08), (x + 0.04, y_back - 0.12, z_apoyo + h_back - 0.05),
                  "aluminio")
        e.tubo([(x, y_front + 0.12, z_apoyo + 0.12), (x, y_back - 0.2, z_apoyo + h_back * 0.6)], 0.025, "aluminio", 4)
        e.caja_de((x - 0.08, y_front - 0.05, z_apoyo), (x + 0.08, y_back + 0.05, z_apoyo + 0.08), "galvanizado",
                  quitar=("-z",))
    if etiqueta:
        etiqueta_cable(e, centro + R @ V((ancho / 2 - 0.3, -largo / 2 + 0.035, 0.035)), R @ V((0, 0, 1)),
                       R @ V((1, 0, 0)), etiqueta, 0.26, 0.06)
    return cj, R


def techo_casa(e):
    zt = Z_TECHO
    # tres paneles solares en fila
    juntas = []
    for i, xc in enumerate((-2.8, 0.0, 2.8)):
        cj, R = panel_solar(e, (xc, -2.75, zt), 2.5, 1.6, 22, "celulas", 0.3, etiqueta=f"FV-{i + 1}")
        juntas.append(cj)
    # bandeja principal de cables detrás de los paneles (sobre soportes)
    yb = 0.15
    zb = zt + 0.14
    for x in (-3.8, -2.0, 0.0, 2.0, 3.8):
        e.caja((x, yb, zt + 0.07), (0.1, 0.3, 0.14), "metal_oscuro", quitar=("-z",))
    canaleta(e, (-4.45, yb, zb), (4.4, yb, zb), (0, 0, 1), 0.3, 0.12)
    canaleta(e, (0.6, yb + 0.15, zb), (0.6, 2.55, zb), (0, 0, 1), 0.26, 0.11)
    for y in (1.2, 2.2):
        e.caja((0.6, y, zt + 0.07), (0.3, 0.1, 0.14), "metal_oscuro", quitar=("-z",))
    # cables de cada panel a la bandeja (rojo y negro, ordenados)
    for k, cj in enumerate(juntas):
        for dx, colr in ((-0.05, "cable_rojo"), (0.05, "cable_negro")):
            p0 = cj + V((dx, 0.0, -0.05))
            cable(e, [p0, V((p0.x, p0.y + 0.1, zt + 0.2)), V((p0.x, yb - 0.12, zt + 0.2)),
                      V((p0.x, yb - 0.12, zb + 0.1))], colr, 0.025, 5)
        etiqueta_cable(e, V((cj.x + 0.35, yb, zb + 0.137)), (0, 0, 1), (1, 0, 0), f"FV-{k + 1}")
    # caja de distribución de energía
    c = V((0.6, 3.25, zt))
    for dx in (-0.55, 0.55):
        e.caja(c + V((dx, 0, 0.08)), (0.12, 0.7, 0.16), "galvanizado", quitar=("-z",))
    e.caja_de(c + V((-0.7, -0.35, 0.16)), c + V((0.7, 0.35, 1.22)), "panel_lab", bisel=True)
    e.caja_de(c + V((-0.64, -0.38, 0.22)), c + V((0.64, -0.35, 1.16)), "panel_lab", bisel=True)  # puerta
    e.caja_de(c + V((-0.8, -0.45, 1.22)), c + V((0.8, 0.45, 1.3)), "remate", bisel=True)  # tejadillo
    letrero(e, c + V((0, -0.39, 1.0)), 0.8, 0.25, (0, -1), "distribucion", 0.01)
    letrero(e, c + V((-0.35, -0.39, 0.6)), 0.26, 0.29, (0, -1), "pegatina_voltaje", 0.008)
    e.caja(c + V((0.5, -0.41, 0.66)), (0.06, 0.06, 0.3), "metal_oscuro")  # manilla
    e.cilindro(c + V((0.5, -0.38, 0.9)), 0.04, 0.04, "acero", lados=8, eje=(0, -1, 0))
    for dx in (-0.45, -0.15, 0.15, 0.45):
        e.caja(c + V((0.66, 0, 0.0)) + V((0.06, 0, 0.3)) + V((0, dx * 0.5, 0)), (0.04, 0.04, 0.04), "led_verde")
    # prensaestopas abajo y cables a la bandeja
    for k, dx in enumerate((-0.45, -0.25, -0.05, 0.15, 0.35)):
        e.cilindro(c + V((dx, -0.1, 0.16)), 0.05, -0.08, "goma", lados=6)
    for dx in (-0.25, 0.0):
        cable(e, [c + V((dx, -0.1, 0.08)), c + V((dx, -0.1, 0.02)), V((0.6 + dx * 0.4, 2.65, zb + 0.06)),
                  V((0.6 + dx * 0.4, 2.45, zb + 0.06))], "cable_negro", 0.03, 5)
    # bandejas a las antenas
    canaleta(e, (-0.15, 3.25, zb), (-3.05, 3.25, zb), (0, 0, 1), 0.22, 0.1)
    canaleta(e, (1.35, 3.25, zb), (3.75, 3.25, zb), (0, 0, 1), 0.22, 0.1)
    for x in (-2.5, -1.2, 2.0, 3.2):
        e.caja((x, 3.25, zt + 0.07), (0.1, 0.26, 0.14), "metal_oscuro", quitar=("-z",))
    cable(e, [c + V((-0.45, -0.1, 0.08)), c + V((-0.6, 0.0, 0.08)), V((-0.2, 3.25, zb + 0.06))], "cable_gris",
          0.028, 5)
    cable(e, [c + V((0.35, -0.1, 0.08)), c + V((0.6, 0.0, 0.08)), V((1.4, 3.25, zb + 0.06))], "cable_gris",
          0.028, 5)
    etiqueta_cable(e, V((-2.2, 3.25, zb + 0.117)), (0, 0, 1), (1, 0, 0), "ANT-P")
    etiqueta_cable(e, V((2.6, 3.25, zb + 0.117)), (0, 0, 1), (1, 0, 0), "ANT-D")
    # acometida a la estación meteorológica
    canaleta(e, (-4.45, yb + 0.15, zb), (-4.45, -2.95, zb), (0, 0, 1), 0.2, 0.09)
    etiqueta_cable(e, V((-4.45, -1.5, zb + 0.107)), (0, 0, 1), (0, 1, 0), "METEO")
    etiqueta_cable(e, V((-3.3, yb, zb + 0.137)), (0, 0, 1), (1, 0, 0), "CUADRO")
    etiqueta_cable(e, V((3.9, yb, zb + 0.137)), (0, 0, 1), (1, 0, 0), "LAB")
    # bajada por encima del peto hasta el cuadro eléctrico (pared izquierda)
    x0 = CASA["x0"]
    zp = Z_TECHO + CASA["peto"] + 0.07
    canaleta(e, (-4.45, yb - 0.15, zb), (-4.45, -2.6, zb), (0, 0, 1), 0.001, 0.001, clips=0, tapa=False) if False \
        else None
    canaleta(e, (-4.6, yb, zb), (x0 - 0.15 + 0.25, yb, zb), (0, 0, 1), 0.3, 0.12, clips=0)
    canaleta(e, (x0 - 0.15 + 0.25, yb, zb), (x0 - 0.15 + 0.25, yb, zp), (1, 0, 0), 0.3, 0.12, clips=0)
    canaleta(e, (x0 - 0.15, yb, zp), (x0 - 0.15 + 0.25, yb, zp), (0, 0, 1), 0.3, 0.12, clips=0)
    canaleta(e, (x0 - 0.18, yb, zp + 0.12), (x0 - 0.18, yb, Z_TECHO), (-1, 0, 0), 0.3, 0.12, clips=0)
    canaleta(e, (x0, yb, CASA["z1"] - 0.32), (x0, yb, Z_TECHO), (-1, 0, 0), 0.3, 0.12, clips=0)
    # baja por la pared, gira y entra por arriba en el cuadro
    canaleta(e, (x0, yb, CASA["z1"] - 0.32), (x0, yb, 4.75), (-1, 0, 0), 0.3, 0.12)
    canaleta(e, (x0, yb + 0.15, 4.6), (x0, -2.3, 4.6), (-1, 0, 0), 0.3, 0.12)
    canaleta(e, (x0, -2.6 + 0.15 - 0.15, 4.6 - 0.15), (x0, -2.6 + 0.15 - 0.15, 4.42), (-1, 0, 0), 0.3, 0.12,
             clips=0)
    etiqueta_cable(e, V((x0 - 0.137, -1.2, 4.6)), (-1, 0, 0), (0, -1, 0), "TECHO")
    # bajada al lab por la pared derecha
    x1 = CASA["x1"]
    canaleta(e, (4.4, yb, zb), (x1 + 0.15 - 0.25, yb, zb), (0, 0, 1), 0.3, 0.12, clips=0)
    canaleta(e, (x1 + 0.15 - 0.25, yb, zb), (x1 + 0.15 - 0.25, yb, zp), (-1, 0, 0), 0.3, 0.12, clips=0)
    canaleta(e, (x1 + 0.15 - 0.25, yb, zp), (x1 + 0.15, yb, zp), (0, 0, 1), 0.3, 0.12, clips=0)
    canaleta(e, (x1 + 0.18, yb, zp + 0.12), (x1 + 0.18, yb, Z_TECHO), (1, 0, 0), 0.3, 0.12, clips=0)
    canaleta(e, (x1, yb, Z_TECHO), (x1, yb, PASILLO["z1"] + 0.25 + 0.12), (1, 0, 0), 0.3, 0.12)
    canaleta(e, (x1, yb, PASILLO["z1"] + 0.25), (LAB["x0"], yb, PASILLO["z1"] + 0.25), (0, 0, 1), 0.3, 0.12)
    etiqueta_cable(e, V((x1 + 0.137, yb, 5.2)), (1, 0, 0), (0, 0, 1), "LAB")


def cuadro_electrico(e):
    """Armario metálico grande en la pared izquierda: puerta, cerradura, pegatina de voltaje, rejillas."""
    x0 = CASA["x0"]
    y0, y1, z0, z1 = -3.6, -1.6, 1.2, 4.42
    xf = x0 - 0.7
    e.caja_de((xf, y0, z0), (x0, y1, z1), "panel_lab", bisel=True, quitar=("+x",))
    # puerta (algo saliente) con su junta, bisagras y cerradura
    e.caja_de((xf - 0.035, y0 + 0.08, z0 + 0.08), (xf, y1 - 0.08, z1 - 0.08), "panel_lab", bisel=True)
    for z in (z0 + 0.6, z1 - 0.6):
        e.cilindro((xf - 0.02, y1 - 0.06, z - 0.15), 0.04, 0.3, "metal_oscuro", lados=6)
    e.caja((xf - 0.07, y0 + 0.25, (z0 + z1) / 2), (0.06, 0.08, 0.5), "metal_oscuro", bisel=True)
    e.cilindro((xf - 0.035, y0 + 0.25, (z0 + z1) / 2 + 0.42), 0.055, -0.04, "acero", lados=8, eje=(1, 0, 0))
    letrero(e, (xf - 0.04, (y0 + y1) / 2, z1 - 0.38), 1.3, 0.3, (-1, 0), "cuadro_general", 0.012)
    letrero(e, (xf - 0.04, (y0 + y1) / 2 + 0.2, (z0 + z1) / 2 + 0.25), 0.4, 0.44, (-1, 0), "pegatina_voltaje",
            0.008)
    e.caja((xf - 0.04, (y0 + y1) / 2, z0 + 0.35), (0.012, 1.0, 0.3), "panel_lab", mats={"-x": "rejilla"},
           decal="-x")
    # tejadillo
    e.caja_de((xf - 0.15, y0 - 0.1, z1), (x0, y1 + 0.1, z1 + 0.1), "remate", bisel=True, quitar=("+x",))
    # canaleta de abajo (llega el cable del panel experimental del suelo)
    canaleta(e, (x0, -2.3, CASA["z0"]), (x0, -2.3, z0), (-1, 0, 0), 0.24, 0.12)
    canaleta(e, (x0 - 0.3, -2.3, CASA["z0"]), (x0, -2.3, CASA["z0"]), (0, 0, 1), 0.24, 0.12, clips=0)
    canaleta(e, (x0 - 0.3, -2.3, 0.06), (x0 - 0.3, -2.3, CASA["z0"] + 0.12), (-1, 0, 0), 0.24, 0.12, clips=0)
    etiqueta_cable(e, V((x0 - 0.127, -2.3, 0.95)), (-1, 0, 0), (0, -1, 0), "SOLAR-X", 0.36, 0.11)


def foco_led(e, neon):
    """Foco LED de precisión sobre la puerta (el cristal emisor va en la malla _neon) y sensor de movimiento."""
    y0 = CASA["y0"]
    xm = (PUERTA["x0"] + PUERTA["x1"]) / 2
    zf = 5.86
    e.caja((xm, y0 - 0.03, zf), (0.32, 0.06, 0.3), "metal_oscuro", bisel=True)
    e.caja((xm, y0 - 0.2, zf + 0.02), (0.1, 0.3, 0.08), "metal_oscuro")
    R = K.rot(22, "X")
    c = V((xm, y0 - 0.48, zf - 0.02))
    e.caja(c, (0.62, 0.36, 0.12), "metal_oscuro", giro=R, bisel=True)
    for k in range(6):
        e.caja(c + R @ V((-0.25 + k * 0.1, 0, 0.09)), (0.025, 0.32, 0.07), "metal_oscuro", giro=R)
    neon.caja(c + R @ V((0, 0, -0.065)), (0.52, 0.27, 0.02), "neon_blanco", giro=R)
    # sensor de movimiento (cúpula blanca) junto al foco
    s = V((xm + 0.62, y0 - 0.08, zf - 0.05))
    e.caja(s + V((0, 0.03, 0)), (0.18, 0.06, 0.18), "blanco_sensor", bisel=True)
    e.cilindro(s + V((0, -0.02, -0.02)), 0.07, -0.06, "blanco_sensor", lados=8, eje=(0, 1, 0))
    e.esfera(s + V((0, -0.09, -0.02)), 0.07, "blanco_sensor", lados=8, anillos=4, escala=(1, 0.8, 1))
    cable(e, [V((xm, y0 - 0.12, zf + 0.15)), V((xm, y0 - 0.12, zf + 0.25)), V((xm, y0 - 0.02, zf + 0.25))],
          "cable_gris", 0.02, 5)


# ==============================================================================================================
# Antenas y estación meteorológica (piezas separadas)
# ==============================================================================================================


def parabolica(p):
    zt = Z_TECHO
    b = V((PARABOLICA["x"], PARABOLICA["y"], zt))
    p.caja(b + V((0, 0, 0.03)), (0.6, 0.6, 0.06), "galvanizado", bisel=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tornillo(p, b + V((sx * 0.22, sy * 0.22, 0.06)), (0, 0, 1))
    p.cilindro(b + V((0, 0, 0.06)), 0.08, 1.0, "galvanizado", lados=10)
    eje = V(PARABOLICA["eje"]).normalized()
    top = b + V((0, 0, 1.06))
    # horquilla de elevación
    p.caja(top + V((0, 0, 0.05)), (0.36, 0.18, 0.1), "metal_oscuro", bisel=True)
    for sx in (-1, 1):
        p.caja(top + V((sx * 0.15, 0, 0.2)), (0.04, 0.2, 0.3), "metal_oscuro")
    # plato parabólico (con grosor) mirando a `eje`
    f = 0.48
    rmax = 0.8
    centro = top + V((0, 0, 0.3)) + eje * 0.05
    mtx = K.marco(centro, eje)
    lados = 14
    radios = [0.07, 0.3, 0.56, rmax]
    frente = [[mtx @ V((math.cos(math.tau * i / lados) * r, math.sin(math.tau * i / lados) * r, r * r / (4 * f)))
               for i in range(lados)] for r in radios]
    borde = [[mtx @ V((math.cos(math.tau * i / lados) * (rmax + 0.02), math.sin(math.tau * i / lados) * (rmax + 0.02),
                       rmax * rmax / (4 * f) - 0.03)) for i in range(lados)]]
    atras = [[mtx @ V((math.cos(math.tau * i / lados) * r, math.sin(math.tau * i / lados) * r,
                       r * r / (4 * f) - 0.05)) for i in range(lados)] for r in reversed(radios)]
    p.loft(frente + borde + atras, "blanco_sensor")
    p.cilindro(centro - eje * 0.2, 0.16, 0.18, "metal_oscuro", lados=10, eje=eje)
    # brazos del LNB (trípode) y LNB en el foco
    foco = centro + eje * f
    for k in range(3):
        a = math.tau * k / 3 - math.pi / 2
        pr = mtx @ V((math.cos(a) * 0.74, math.sin(a) * 0.74, 0.74 * 0.74 / (4 * f)))
        p.tubo([pr, foco - eje * 0.1], 0.022, "galvanizado", lados=5)
    p.cilindro(foco - eje * 0.12, 0.065, 0.2, "goma", lados=8, eje=eje)
    p.cilindro(foco + eje * 0.08, 0.08, 0.04, "goma", lados=8, eje=eje, radio2=0.06)
    # cable coaxial por el brazo y el mástil
    pr = mtx @ V((0, -0.74, 0.74 * 0.74 / (4 * f)))
    cable(p, [foco - eje * 0.08, pr + eje * -0.02, top + V((0.0, -0.1, 0.1)), b + V((0.1, -0.1, 0.4)),
              b + V((0.12, -0.12, 0.08))], "cable_negro", 0.018, 5)


def dipolo(p):
    zt = Z_TECHO
    b = V((DIPOLO["x"], DIPOLO["y"], zt))
    p.caja(b + V((0, 0, 0.03)), (0.5, 0.5, 0.06), "galvanizado", bisel=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tornillo(p, b + V((sx * 0.18, sy * 0.18, 0.06)), (0, 0, 1))
    alto = 3.4
    p.cilindro(b + V((0, 0, 0.06)), 0.065, alto, "galvanizado", lados=8)
    for z in (0.9, 2.0):
        p.cilindro(b + V((0, 0, z)), 0.085, 0.12, "metal_oscuro", lados=8)
    # tres pisos de dipolos (brazos con aislador blanco central)
    for z, L in ((2.15, 1.7), (2.75, 1.3), (3.3, 0.95)):
        c = b + V((0, 0, z))
        p.caja(c, (0.2, 0.16, 0.16), "blanco_sensor", bisel=True)
        for s in (-1, 1):
            p.cilindro(c + V((s * 0.1, 0, 0)), 0.022, L / 2, "aluminio", lados=6, eje=(s, 0, 0))
    p.cilindro(b + V((0, 0, 0.06 + alto)), 0.065, 0.12, "remate", lados=8, radio2=0.01)
    # coaxial bajando pegado al mástil con bridas
    cable(p, [b + V((0.09, 0, 3.3)), b + V((0.09, 0, 0.3)), b + V((0.09, -0.22, 0.12)), b + V((0.09, -0.32, 0.12))],
          "cable_negro", 0.02, 5)
    for z in (0.6, 1.7, 3.0):
        p.cilindro(b + V((0.045, 0, z)), 0.1, 0.03, "goma", lados=6)


def estacion(p, anem, vel):
    zt = Z_TECHO
    b = V((ESTACION["x"], ESTACION["y"], zt))
    p.caja(b + V((0, 0, 0.03)), (0.45, 0.45, 0.06), "galvanizado", bisel=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tornillo(p, b + V((sx * 0.16, sy * 0.16, 0.06)), (0, 0, 1))
    alto = 2.7
    p.cilindro(b + V((0, 0, 0.06)), 0.055, alto, "galvanizado", lados=8)
    zc = zt + alto - 0.15
    # cruceta
    p.caja(V((b.x, b.y, zc)), (1.5, 0.07, 0.07), "aluminio", bisel=True)
    p.caja(V((b.x, b.y, zc)), (0.16, 0.16, 0.14), "metal_oscuro", bisel=True)
    ejes = {}
    for nombre, dx in (("anem", -0.7), ("vel", 0.7)):
        s = V((b.x + dx, b.y, zc + 0.035))
        p.cilindro(s, 0.035, 0.22, "aluminio", lados=8)
        p.cilindro(s + V((0, 0, 0.22)), 0.05, 0.06, "metal_oscuro", lados=8)
        ejes[nombre] = s + V((0, 0, 0.28))
    # sensor de temperatura: escudo de platos blancos apilados
    t = V((b.x, b.y + 0.42, zt + 1.75))
    p.caja(V((b.x, b.y + 0.2, t.z)), (0.06, 0.4, 0.06), "aluminio")
    for k in range(6):
        p.cilindro(t + V((0, 0, k * 0.065)), 0.19 - k * 0.006, 0.03, "blanco_sensor", lados=8, radio2=0.17 - k * 0.006)
    p.cilindro(t + V((0, 0, 6 * 0.065)), 0.17, 0.07, "blanco_sensor", lados=12, radio2=0.06)
    p.cilindro(t + V((0, 0, -0.05)), 0.05, 0.4, "blanco_sensor", lados=8)
    # registrador de datos en el mástil, con LED
    r = V((b.x, b.y - 0.13, zt + 0.95))
    p.caja(r, (0.28, 0.14, 0.36), "blanco_sensor", bisel=True)
    p.caja(r + V((0.08, -0.075, 0.12)), (0.04, 0.02, 0.04), "led_verde")
    letrero(p, r + V((-0.03, -0.075, -0.06)), 0.22, 0.09, (0, -1), "et_METEO", 0.008, "blanco_sensor")
    cable(p, [r + V((0, 0.0, -0.18)), r + V((0, 0.0, -0.4)), b + V((0, -0.2, 0.14)), b + V((0, -0.32, 0.14))],
          "cable_gris", 0.02, 5)

    # anemómetro (gira sobre su eje)
    c = ejes["anem"]
    anem.cilindro(c, 0.05, 0.1, "metal_oscuro", lados=8)
    anem.cilindro(c + V((0, 0, 0.1)), 0.05, 0.04, "metal_oscuro", lados=8, radio2=0.02)
    for k in range(3):
        a = math.tau * k / 3
        d = V((math.cos(a), math.sin(a), 0))
        tang = V((-math.sin(a), math.cos(a), 0))
        anem.tubo([c + V((0, 0, 0.06)) + d * 0.04, c + V((0, 0, 0.06)) + d * 0.3], 0.013, "aluminio", lados=5)
        anem.casquete(c + V((0, 0, 0.06)) + d * 0.34, tang, 0.085, 0.012, "blanco_sensor", lados=8, anillos=2)
    # veleta (gira sobre su eje)
    c = ejes["vel"]
    vel.cilindro(c, 0.045, 0.1, "metal_oscuro", lados=8)
    vel.caja(c + V((0.1, 0, 0.08)), (0.9, 0.03, 0.03), "aluminio")
    flecha = [(0.0, 0.0), (0.16, 0.08), (0.16, -0.08)]
    mtx = K.marco(c + V((-0.5, 0, 0.08)), (0, 1, 0), (1, 0, 0))
    vel.extruir([(x, z) for x, z in flecha], -0.015, 0.015, mtx, "metal_oscuro")
    cola = [(0.0, -0.04), (0.32, -0.12), (0.32, 0.18), (0.0, 0.06)]
    mtx = K.marco(c + V((0.3, 0, 0.08)), (0, 1, 0), (1, 0, 0))
    vel.extruir(cola, -0.01, 0.01, mtx, "blanco_sensor")
    return ejes


# ==============================================================================================================
# Alrededores: generador, contenedor, silla, panel experimental, cámara, escoba, explanada
# ==============================================================================================================


def explanada(e):
    """Explanada de hormigón limpio delante de la casa y del lab (el ingeniero barre)."""
    e.caja_de((-10.0, -8.8, 0.0), (CASA["x1"] + 0.3, CASA["y0"] - 0.3, 0.06), "hormigon_limpio", quitar=("-z",),
              bisel=True)
    e.caja_de((CASA["x1"] + 0.3, -8.8, 0.0), (14.2, LAB["y0"] - 0.3, 0.06), "hormigon_limpio", quitar=("-z",),
              bisel=True)
    e.caja_de((CASA["x1"] + 0.3, LAB["y0"] - 0.3, 0.0), (LAB["x0"] - 0.3, PASILLO["y0"] - 0.15, 0.06),
              "hormigon_limpio", quitar=("-z",))
    e.caja_de((LAB["x1"] + 0.3, LAB["y0"] - 0.3, 0.0), (14.2, 4.2, 0.06), "hormigon_limpio", quitar=("-z",),
              bisel=True)


def generador(e):
    """Generador diésel de emergencia junto al lab: rejillas, escape, panel con pantalla y botón de arranque."""
    x0, x1, y0, y1 = 11.75, 13.55, 2.15, 3.45
    zb = 0.06
    # bancada con franjas de aviso
    e.caja_de((x0 - 0.05, y0 - 0.05, zb), (x1 + 0.05, y1 + 0.05, zb + 0.16), "aviso", bisel=True, quitar=("-z",))
    zc = zb + 0.16
    e.caja_de((x0, y0, zc), (x1, y1, zc + 1.35), "generador", bisel=True)
    e.caja_de((x0 - 0.04, y0 - 0.04, zc + 1.35), (x1 + 0.04, y1 + 0.04, zc + 1.43), "generador", bisel=True)
    # rejillas
    e.caja(((x0 + x1) / 2 + 0.35, y0 - 0.01, zc + 0.7), (0.9, 0.03, 0.9), "generador", mats={"-y": "rejilla_generador"},
           decal="-y")
    e.caja((x1 + 0.01, (y0 + y1) / 2, zc + 0.7), (0.03, 0.9, 0.9), "generador", mats={"+x": "rejilla_generador"},
           decal="+x")
    # panel de mando
    pc = V((x0 + 0.42, y0 - 0.02, zc + 0.8))
    e.caja(pc, (0.62, 0.04, 0.82), "metal_oscuro", bisel=True)
    e.caja(pc + V((0, -0.025, 0.22)), (0.36, 0.012, 0.19), "metal_oscuro", mats={"-y": "letrero"}, decal="-y",
           rect=RECT("lcd_generador"))
    e.cilindro(pc + V((-0.12, -0.02, -0.12)), 0.09, -0.06, "metal_oscuro", lados=10, eje=(0, 1, 0))
    e.cilindro(pc + V((-0.12, -0.08, -0.12)), 0.075, -0.06, "verde_boton", lados=12, eje=(0, 1, 0))
    letrero(e, pc + V((-0.12, -0.025, -0.3)), 0.24, 0.08, (0, -1), "arranque", 0.008)
    e.cilindro(pc + V((0.16, -0.02, -0.12)), 0.05, -0.04, "rojo_boton", lados=10, eje=(0, 1, 0))
    letrero(e, pc + V((0.16, -0.025, -0.28)), 0.2, 0.07, (0, -1), "parada", 0.008)
    e.caja(pc + V((0.24, -0.025, 0.36)), (0.04, 0.012, 0.04), "led_verde")
    letrero(e, V(((x0 + x1) / 2 + 0.35, y0 - 0.03, zc + 1.22)), 1.0, 0.24, (0, -1), "placa_generador", 0.01)
    # escape con codo y sombrerete
    ex = V((x1 - 0.3, y1 - 0.3, zc + 1.43))
    e.tubo([ex, ex + V((0, 0, 0.55)), ex + V((0.06, 0.06, 0.75))], 0.075, "escape", lados=8)
    e.cilindro(ex + V((0.06, 0.06, 0.74)), 0.09, 0.08, "escape", lados=8)
    e.caja(ex + V((0.06, 0.06, 0.85)), (0.22, 0.2, 0.025), "escape", giro=K.rot(-25, "X"))
    # tapón de combustible y cáncamos
    e.cilindro(V((x0 + 0.35, y1 - 0.3, zc + 1.43)), 0.09, 0.06, "metal_oscuro", lados=10)
    for x in (x0 + 0.15, x1 - 0.15):
        e.toro(V((x, (y0 + y1) / 2, zc + 1.49)), 0.07, 0.02, "acero", eje=(0, 1, 0), n1=8, n2=4)
    # cable al lab por canaleta en la pared del lab
    cable(e, [V((x0, y0 + 0.35, 0.45)), V((x0 - 0.2, y0 + 0.35, 0.45)), V((LAB["x1"] + 0.07, 2.05, 0.45))],
          "cable_negro", 0.045, 6)
    canaleta(e, (LAB["x1"], 2.05, LAB["z0"]), (LAB["x1"], 2.05, 1.3), (1, 0, 0), 0.24, 0.12)
    etiqueta_cable(e, V((LAB["x1"] + 0.127, 2.05, 1.0)), (1, 0, 0), (0, 1, 0), "GEN")


def contenedor_raee(e):
    """Contenedor de residuos electrónicos junto al lab (reciclaje + rayo)."""
    x0, x1, y0, y1 = 10.0, 11.35, -3.35, -2.25
    zb = 0.06
    h = 1.35
    k = 0.06  # se ensancha hacia arriba
    abajo = [V((x0 + k, y0 + k, zb + 0.08)), V((x1 - k, y0 + k, zb + 0.08)), V((x1 - k, y1 - k, zb + 0.08)),
             V((x0 + k, y1 - k, zb + 0.08))]
    arriba = [V((x0, y0, zb + h)), V((x1, y0, zb + h)), V((x1, y1, zb + h)), V((x0, y1, zb + h))]
    e.loft([abajo, arriba], "contenedor", bisel=True)
    # tapa con ranura para aparatos pequeños
    e.caja_de((x0 - 0.05, y0 - 0.06, zb + h), (x1 + 0.05, y1 + 0.03, zb + h + 0.09), "contenedor", bisel=True)
    e.caja(((x0 + x1) / 2, (y0 + y1) / 2, zb + h + 0.092), (0.7, 0.1, 0.012), "goma")
    e.tubo([(x0 + 0.25, y0 - 0.06, zb + h + 0.04), (x0 + 0.25, y0 - 0.14, zb + h + 0.04),
            (x1 - 0.25, y0 - 0.14, zb + h + 0.04), (x1 - 0.25, y0 - 0.06, zb + h + 0.04)], 0.025, "metal_oscuro", 6)
    # pegatina frontal (inclinada como la pared del contenedor)
    giro = K.rot(math.degrees(math.atan2(k, h)), "X")
    e.caja(V(((x0 + x1) / 2, y0 + k * 0.45 - 0.005, zb + 0.75)), (0.78, 0.01, 0.78), "contenedor", giro=giro,
           mats={"-y": "letrero"}, decal="-y", rect=RECT("reciclaje"))
    # ruedas traseras y patas delanteras
    for x in (x0 + 0.2, x1 - 0.2):
        e.cilindro(V((x - 0.06, y1 - 0.05, zb + 0.12)), 0.12, 0.12, "goma", lados=10, eje=(1, 0, 0))
        e.caja(V((x, y0 + 0.15, zb + 0.06)), (0.12, 0.12, 0.12), "goma")


def escoba(e):
    """Escoba apoyada en la pared del lab: el ingeniero barre la explanada."""
    base = V((9.95, -2.25, 0.06))
    top = V((9.88, LAB["y0"] - 0.04, 3.05))
    d = (top - base).normalized()
    e.cilindro(base + d * 0.15, 0.035, (top - base).length - 0.15, "madera_mango", lados=6, eje=d)
    e.cilindro(top, 0.042, 0.06, "goma", lados=6, eje=d)
    giro = Matrix((V((1, 0, 0)), V((0, 1, 0)).cross(d) * -1 if False else d.cross(V((1, 0, 0))), d)).transposed()
    e.caja(base + d * 0.16, (0.8, 0.1, 0.1), "madera_mango", giro=giro, bisel=True)
    e.caja(base + d * 0.06, (0.76, 0.12, 0.12), "escoba_cerdas", giro=giro)


def silla_y_cuaderno(e):
    """
    Silla plegable de pensar, de acero pintado y muy gastada, con un cuaderno cerrado y un lápiz encima.
    Tubos en X vistos de lado (patas delanteras que suben hasta el respaldo y patas traseras que sujetan el
    asiento), asiento y respaldo de chapa, tacos de goma.
    """
    vs = set()
    zs = 1.75  # altura del asiento
    for s in (-1, 1):
        x = s * 0.6
        vs |= set(e.tubo([(x, -0.5, 0.0), (x, -0.36, zs - 0.05), (x, 0.22, 3.0), (x, 0.26, 3.22)], 0.05, "silla", 6))
        xr = s * 0.5
        vs |= set(e.tubo([(xr, 0.62, 0.0), (xr, -0.18, zs - 0.08)], 0.045, "silla", 6))
        vs |= set(e.cilindro((x, -0.5, 0.0), 0.065, 0.1, "goma", lados=6))
        vs |= set(e.cilindro((xr, 0.62, 0.0), 0.06, 0.1, "goma", lados=6))
        vs |= set(e.cilindro((s * 0.66, 0.1, zs - 0.48), 0.04, 0.08, "metal_oscuro", lados=6, eje=(s, 0, 0)))
    vs |= set(e.tubo([(-0.6, -0.46, 0.38), (0.6, -0.46, 0.38)], 0.035, "silla", 6))
    vs |= set(e.tubo([(-0.5, 0.52, 0.38), (0.5, 0.52, 0.38)], 0.035, "silla", 6))
    # asiento con el borde doblado
    vs |= e.caja((0, 0.0, zs), (1.12, 1.02, 0.08), "silla", bisel=True)
    vs |= e.caja((0, -0.5, zs - 0.06), (1.12, 0.04, 0.12), "silla")
    # respaldo curvado (dos tramos)
    for ang, dy in ((-12, 0.0), (12, 0.0)):
        g = K.rot(-13, "X") @ K.rot(ang, "Z")
        vs |= e.caja(V((ang / 12 * 0.27, 0.18 + abs(ang) / 12 * 0.03, 2.82)), (0.56, 0.06, 0.48), "silla", giro=g,
                     bisel=True)
    # cuaderno cerrado (tapas, hojas, goma elástica, etiqueta) y lápiz encima
    cv = set()
    zc = zs + 0.04
    cv |= e.caja((0, 0, zc + 0.012), (0.62, 0.86, 0.024), "cuaderno_tapa", bisel=True)
    cv |= e.caja((0.01, 0, zc + 0.05), (0.59, 0.83, 0.052), "cuaderno_hojas")
    cv |= e.caja((0, 0, zc + 0.088), (0.62, 0.86, 0.024), "cuaderno_tapa", bisel=True)
    cv |= e.caja((-0.31, 0, zc + 0.05), (0.03, 0.86, 0.1), "cuaderno_tapa")
    cv |= e.caja((0.2, 0, zc + 0.05), (0.035, 0.88, 0.108), "goma")
    cv |= e.caja((-0.08, 0.18, zc + 0.101), (0.3, 0.16, 0.004), "cuaderno_hojas", mats={"+z": "letrero"}, decal="+z",
                 rect=RECT("cuaderno"))
    lp = V((-0.05, -0.12, zc + 0.125))
    dl = V((1, 0.25, 0)).normalized()
    cv |= set(e.cilindro(lp - dl * 0.3, 0.022, 0.5, "lapiz", lados=6, eje=dl))
    cv |= set(e.cilindro(lp + dl * 0.2, 0.022, 0.07, "madera_lapiz", lados=6, eje=dl, radio2=0.006))
    cv |= set(e.cilindro(lp + dl * 0.268, 0.007, 0.012, "grafito", lados=4, eje=dl, radio2=0.001))
    cv |= set(e.cilindro(lp - dl * 0.36, 0.024, 0.06, "acero", lados=6, eje=dl))
    cv |= set(e.cilindro(lp - dl * 0.4, 0.022, 0.04, "goma_borrar", lados=6, eje=dl))
    e.transformar(cv, Matrix.Translation(V((0.0, 0.05, 0.0))) @ K.rot(-24).to_4x4())
    vs |= cv
    m = Matrix.Translation(V((SILLA["x"], SILLA["y"], 0.06))) @ K.rot(SILLA["giro"]).to_4x4()
    e.transformar(vs, m)


def panel_experimental(e):
    """Panel solar experimental en el suelo, sobre soporte bajo, con su cable hasta el cuadro de la casa."""
    cj, R = panel_solar(e, (-8.2, -6.6, 0.06), 2.2, 1.3, 28, "celulas_suelo", 0.32, etiqueta="SOLAR-X")
    centro = V((-8.2, -6.6, 0.06 + 0.32)) + R @ V((0, 0.65, 0.06))
    # pegatina del prototipo y piranómetro (cúpula blanca) en el marco
    letrero(e, V((-8.2 + 0.55, -6.6 - 0.02, 0.06 + 0.3)), 0.6, 0.23, (0, -1), "prototipo", 0.01, "aluminio")
    s = centro + R @ V((-0.85, 0.66, 0.08))
    e.cilindro(s, 0.09, 0.06, "blanco_sensor", lados=10)
    e.esfera(s + V((0, 0, 0.07)), 0.06, "cristal_oscuro", lados=8, anillos=4)
    # registrador en la pata trasera con LED ámbar (midiendo)
    rg = V((-8.2 - 0.75, -6.6 + 1.3 * math.cos(math.radians(28)) - 0.05, 0.4))
    e.caja(rg, (0.26, 0.12, 0.3), "blanco_sensor", bisel=True)
    e.caja(rg + V((0.07, -0.065, 0.09)), (0.035, 0.02, 0.035), "led_ambar")
    # cable al suelo y canaleta pisable (con franjas) hasta la casa
    zc = 0.06
    ruta = [V((-8.2, -5.4, zc)), V((-6.5, -5.4, zc)), V((-6.5, -2.3, zc)), V((CASA["x0"] - 0.6, -2.3, zc))]
    cable(e, [cj + V((0, 0, -0.04)), V((cj.x, cj.y + 0.15, 0.2)), V((-8.2, -5.4, 0.1))], "cable_negro", 0.03, 5)
    for a, b in zip(ruta[:-1], ruta[1:]):
        d = (b - a)
        largo = d.length
        d.normalize()
        w = V((0, 0, 1)).cross(d)
        giro = Matrix((d, w, V((0, 0, 1)))).transposed()
        c = (a + b) / 2
        e.caja(c + V((0, 0, 0.04)), (largo + 0.3, 0.34, 0.08), "aviso", giro=giro, quitar=("-z",))
        for sw in (-1, 1):
            e.caja(c + w * sw * 0.21 + V((0, 0, 0.02)), (largo + 0.3, 0.08, 0.04), "goma", giro=giro, quitar=("-z",))


def camara(e, cam):
    """Poste bajo con cámara de seguridad apuntando a la puerta del lab (cabezal en pieza aparte)."""
    b = V((CAMARA["x"], CAMARA["y"], 0.06))
    e.caja(b + V((0, 0, 0.025)), (0.5, 0.5, 0.05), "galvanizado", bisel=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tornillo(e, b + V((sx * 0.18, sy * 0.18, 0.05)), (0, 0, 1))
    alto = CAMARA["alto"]
    e.cilindro(b + V((0, 0, 0.05)), 0.085, alto, "galvanizado", lados=10)
    e.cilindro(b + V((0, 0, 0.05 + alto)), 0.1, 0.06, "metal_oscuro", lados=10)
    # caja de conexiones y cartel
    e.caja(b + V((0, -0.14, 0.9)), (0.24, 0.1, 0.3), "blanco_sensor", bisel=True)
    letrero(e, b + V((0, -0.11, 1.75)), 0.7, 0.5, (0, -1), "zona_vigilada", 0.02, "aluminio")
    for z in (1.55, 1.95):
        e.caja(b + V((0, -0.06, z)), (0.22, 0.08, 0.05), "metal_oscuro")
    letrero(e, b + V((0.0, -0.195, 0.9 + 0.06)), 0.2, 0.08, (0, -1), "et_CAM", 0.006, "blanco_sensor")
    # brazo articulado hacia la puerta del lab
    obj = V(CAMARA["objetivo"])
    top = b + V((0, 0, 0.11 + alto))
    dxy = V((obj.x - top.x, obj.y - top.y, 0)).normalized()
    j = top + dxy * 0.38 + V((0, 0, 0.08))
    e.cilindro(top - V((0, 0, 0.02)), 0.06, 0.12, "metal_oscuro", lados=8)
    e.tubo([top + V((0, 0, 0.08)), j - dxy * 0.06], 0.035, "metal_oscuro", lados=6)
    e.esfera(j - dxy * 0.04, 0.06, "metal_oscuro", lados=8, anillos=4)
    # cabezal (pieza aparte, gira alrededor de j)
    ap = (obj - j).normalized()
    mtx = K.marco(j, ap, V((0, 0, 1)))  # z local = dirección de la cámara
    R = mtx.to_3x3()
    # en el marco, x local apunta hacia arriba (eje_x pedido = Z del mundo)
    cam.esfera(j, 0.055, "metal_oscuro", lados=8, anillos=4)
    cam.caja(mtx @ V((0, 0, 0.08)), (0.06, 0.06, 0.16), "metal_oscuro", giro=R)
    cuerpo = mtx @ V((0.0, 0, 0.42))
    cam.caja(cuerpo, (0.26, 0.26, 0.6), "blanco_sensor", giro=R, bisel=True)
    cam.caja(mtx @ V((0.16, 0, 0.5)), (0.03, 0.32, 0.72), "blanco_sensor", giro=R, bisel=True)  # visera
    lente = mtx @ V((0, 0, 0.72))
    cam.cilindro(lente, 0.095, 0.04, "metal_oscuro", lados=12, eje=ap)
    cam.cilindro(lente + ap * 0.04, 0.075, 0.02, "cristal_oscuro", lados=12, eje=ap)
    for k in range(6):
        a = math.tau * k / 6
        cam.caja(mtx @ V((math.cos(a) * 0.1, math.sin(a) * 0.1, 0.73)), (0.022, 0.022, 0.01), "led_rojo", giro=R)
    cam.caja(mtx @ V((-0.09, 0.09, 0.725)), (0.02, 0.02, 0.01), "led_rojo", giro=R)
    cam.cilindro(mtx @ V((0, 0, 0.12)), 0.03, -0.1, "goma", lados=6, eje=ap)
    return j, ap


# ==============================================================================================================
# Montaje, horneado, render y exportación
# ==============================================================================================================


def construir():
    piezas = {}

    def nueva(n):
        piezas[n] = K.Malla(f"{NOMBRE}_{n}")
        return piezas[n]

    e = nueva("estructura")
    cr = nueva("cristal")
    neon = nueva("neon")
    pp = nueva("puerta_principal")
    pl = nueva("puerta_lab")
    pers = nueva("persiana")
    par = nueva("antena_parabolica")
    dip = nueva("antena_dipolo")
    est = nueva("estacion_meteo")
    anem = nueva("anemometro")
    vel = nueva("veleta")
    cam = nueva("camara")

    explanada(e)
    casa(e, cr)
    pasillo(e, cr)
    laboratorio(e, cr)
    techo_casa(e)
    cuadro_electrico(e)
    foco_led(e, neon)
    generador(e)
    contenedor_raee(e)
    escoba(e)
    silla_y_cuaderno(e)
    panel_experimental(e)
    j_cam, dir_cam = camara(e, cam)
    puerta_principal(pp)
    puerta_lab(pl)
    persiana(pers)
    parabolica(par)
    dipolo(dip)
    ejes_meteo = estacion(est, anem, vel)
    extra = {"camara": (j_cam, dir_cam), "meteo": ejes_meteo}
    return piezas, extra


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--sin_render", action="store_true")
    a = ap.parse_args()
    salida = os.path.abspath(a.salida)
    os.makedirs(salida, exist_ok=True)
    tmp = os.path.join(salida, "_tmp")
    os.makedirs(tmp, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0
    scn.world = bpy.data.worlds.new("mundo")

    rc, rp = L.generar(tmp)
    MI.RUTAS_LETREROS["color"], MI.RUTAS_LETREROS["props"] = rc, rp
    MI.SILLA["centro_asiento"] = (SILLA["x"], SILLA["y"])

    piezas, extra = construir()
    tris_bm = {n: m.triangulos() for n, m in piezas.items()}
    objetos = {}
    for n, m in piezas.items():
        objetos[n] = m.objeto(M, bisel=0.04)
    tris = {n: K.triangulos(o) for n, o in objetos.items()}
    total = sum(tris.values())
    print("[tri]", tris, "TOTAL", total)

    atlas = [o for n, o in objetos.items() if n not in ("cristal", "neon")]
    mats_usados = {m for o in atlas for m in o.data.materials}
    K.desplegar_atlas(atlas, M)
    tam = 512 if a.rapido else K.TAM_ATLAS
    rutas = K.hornear_atlas(atlas, mats_usados, salida, NOMBRE, tam=tam, muestras=4 if a.rapido else 12,
                            muestras_ao=24 if a.rapido else 128)
    mat_final = K.material_atlas(f"{NOMBRE}_atlas", rutas)
    for o in atlas:
        o.data.materials.clear()
        o.data.materials.append(mat_final)
        # la capa «decal» solo servía para hornear
        if "decal" in o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers["decal"])
    for n in ("cristal", "neon"):
        o = objetos[n]
        if "decal" in o.data.uv_layers:
            o.data.uv_layers.remove(o.data.uv_layers["decal"])

    with open(os.path.join(salida, "_estado.json"), "w") as f:
        json.dump({"tris": tris, "total": total}, f)

    if not a.sin_render:
        import render_ingeniero as RI
        RI.renderizar_todo(objetos, salida, NOMBRE, a.rapido, total, tris)

    exportar(objetos, extra, salida, tris, total, rutas)
    # fuera los temporales (hoja de letreros, renders sueltos)
    import shutil
    shutil.rmtree(tmp, ignore_errors=True)
    os.remove(os.path.join(salida, "_estado.json"))


def exportar(objetos, extra, salida, tris, total, rutas):
    """Pivotes en las bisagras y ejes, GIRO_IMPORTACION, FBX y JSON con todo lo que hace falta en Studio."""
    pivotes = {
        "puerta_principal": V((BISAGRA_PUERTA.x, BISAGRA_PUERTA.y, CASA["z0"])),
        "puerta_lab": V((BISAGRA_LAB.x, BISAGRA_LAB.y, LAB["z0"])),
        "anemometro": extra["meteo"]["anem"],
        "veleta": extra["meteo"]["vel"],
        "camara": extra["camara"][0],
        "antena_parabolica": V((PARABOLICA["x"], PARABOLICA["y"], Z_TECHO)),
        "antena_dipolo": V((DIPOLO["x"], DIPOLO["y"], Z_TECHO)),
        "estacion_meteo": V((ESTACION["x"], ESTACION["y"], Z_TECHO)),
    }
    giro = Matrix.Rotation(math.radians(K.GIRO_IMPORTACION), 4, "Z")

    def a_roblox(v):
        """Blender (studs) → Roblox tras el giro y los ejes del FBX: (x, y, z) → (-x, z, y)."""
        w = giro @ V(v)
        return [round(w.x, 3), round(w.z, 3), round(-w.y, 3)]

    def dir_roblox(v):
        w = giro.to_3x3() @ V(v)
        return [round(w.x, 4), round(w.z, 4), round(-w.y, 4)]

    for n, o in objetos.items():
        piv = pivotes.get(n, V((0, 0, 0)))
        # origen del objeto en el pivote (la malla se desplaza al revés)
        o.data.transform(Matrix.Translation(-piv))
        o.location = piv
        # GIRO_IMPORTACION: 180° sobre el eje vertical, aplicado a la malla y a la posición
        o.data.transform(giro)
        o.location = giro @ o.location
        o.data.update()

    orden = ["estructura", "puerta_principal", "puerta_lab", "persiana", "antena_parabolica", "antena_dipolo",
             "estacion_meteo", "anemometro", "veleta", "camara", "cristal", "neon"]
    K.exportar_fbx(os.path.join(salida, f"{NOMBRE}.fbx"), [objetos[n] for n in orden])

    mn = V((1e9,) * 3)
    mx = V((-1e9,) * 3)
    for o in objetos.values():
        for c in o.bound_box:
            w = o.matrix_world @ V(c)
            mn = V(map(min, mn, w))
            mx = V(map(max, mx, w))
    tam = mx - mn

    VF = VENT_FRENTE
    j_cam, d_cam = extra["camara"]
    info = {
        "nombre": NOMBRE,
        "descripcion": "Casa del ingeniero de la colonia (Ing. Kowalski) con mini laboratorio adosado.",
        "escala": "1 unidad = 1 stud. FBX con Apply Scalings = FBX All y sin escala de unidades: en el importador "
                  "de Studio, Scale Unit = Stud.",
        "giro_importacion": "Las mallas llevan aplicado un giro de 180° sobre el eje vertical (Y de Roblox) antes "
                            "de exportar. Con los ejes del FBX (adelante -Z, arriba Y) la fachada mira a -Z.",
        "coordenadas": "Todas las posiciones de este archivo son de Roblox (X, Y arriba, Z), en studs, respecto al "
                       "origen del modelo: el centro de la planta de la casa principal a ras de suelo. La fachada "
                       "(puerta principal) mira a -Z; el laboratorio queda en -X.",
        "tamano_total_studs": [round(tam.x, 2), round(tam.z, 2), round(tam.y, 2)],
        "triangulos": {"total": total, "presupuesto": 14000, "por_pieza": tris},
        "texturas": {
            "tamano": K.TAM_ATLAS,
            "ColorMap": os.path.basename(rutas["color"]),
            "NormalMap": os.path.basename(rutas["normal"]),
            "RoughnessMap": os.path.basename(rutas["rugosidad"]),
            "MetalnessMap": os.path.basename(rutas["metal"]),
            "Emision": os.path.basename(rutas["emision"]),
            "nota": "Un solo atlas para todas las piezas salvo _cristal y _neon. SurfaceAppearance con ColorMap, "
                    "NormalMap, RoughnessMap y MetalnessMap en cada MeshPart del atlas. La emisión es la máscara de "
                    "los LEDs y pantallas (para SurfaceAppearance.EmissiveMaskContent si se usa, o de referencia).",
        },
        "piezas": {
            f"{NOMBRE}_estructura": {"material": "SurfaceAppearance (atlas)", "anclada": True,
                                     "que_es": "Casa, lab, pasillo, techo técnico, canaletas, cuadro, generador, "
                                               "contenedor, silla, panel del suelo, poste de la cámara, explanada."},
            f"{NOMBRE}_puerta_principal": {
                "material": "SurfaceAppearance (atlas)", "animable": True,
                "pivote": a_roblox(pivotes["puerta_principal"]), "eje_giro": [0, 1, 0],
                "abrir": "Gira hacia fuera (hacia la calle, -Z). Con la puerta cerrada, girar el pivote "
                         "+90° sobre Y abre hacia fuera sin chocar con la silla.",
                "grados_abierta": 95},
            f"{NOMBRE}_puerta_lab": {
                "material": "SurfaceAppearance (atlas)", "animable": True,
                "pivote": a_roblox(pivotes["puerta_lab"]), "eje_giro": [0, 1, 0],
                "abrir": "Igual que la principal: hacia fuera, bisagras en el lado de la casa.",
                "grados_abierta": 95},
            f"{NOMBRE}_persiana": {
                "material": "SurfaceAppearance (atlas)", "animable": True,
                "alto": 0.92, "alto_recogida": 0.12,
                "borde_superior": a_roblox(V(((VF["x0"] + VF["x1"]) / 2, CASA["y0"] - 0.055, VF["z1"] + 0.06))),
                "como_abrir": "Size.Y -> alto_recogida manteniendo fijo el borde superior (subir el CFrame "
                              "(alto - alto_recogida) / 2). Para bajarla del todo, Size.Y = 2,7."},
            f"{NOMBRE}_antena_parabolica": {"material": "SurfaceAppearance (atlas)",
                                            "pivote": a_roblox(pivotes["antena_parabolica"])},
            f"{NOMBRE}_antena_dipolo": {"material": "SurfaceAppearance (atlas)",
                                        "pivote": a_roblox(pivotes["antena_dipolo"])},
            f"{NOMBRE}_estacion_meteo": {"material": "SurfaceAppearance (atlas)",
                                         "pivote": a_roblox(pivotes["estacion_meteo"])},
            f"{NOMBRE}_anemometro": {"material": "SurfaceAppearance (atlas)", "animable": True,
                                     "pivote": a_roblox(pivotes["anemometro"]), "eje_giro": [0, 1, 0],
                                     "animacion": "Giro continuo sobre Y (1-3 vueltas por segundo según el viento)."},
            f"{NOMBRE}_veleta": {"material": "SurfaceAppearance (atlas)", "animable": True,
                                 "pivote": a_roblox(pivotes["veleta"]), "eje_giro": [0, 1, 0],
                                 "animacion": "Oscilación lenta de ±15° sobre Y."},
            f"{NOMBRE}_camara": {"material": "SurfaceAppearance (atlas)", "animable": True,
                                 "pivote": a_roblox(j_cam), "mira_hacia": dir_roblox(d_cam),
                                 "animacion": "Barrido lento de ±25° sobre Y alrededor del pivote (la rótula)."},
            f"{NOMBRE}_cristal": {"material": "Glass", "color": "#DCEEF5", "transparencia": 0.35,
                                  "que_es": "Cristales de las ventanas (el del lab es doble), claraboya y ojo de buey "
                                            "del pasillo."},
            f"{NOMBRE}_neon": {"material": "Neon", "color": "#DFF1FF",
                               "que_es": "Cristal emisor del foco LED de la puerta (blanco frío)."},
        },
        "luces": {
            "foco_puerta": {"posicion": a_roblox(V(((PUERTA["x0"] + PUERTA["x1"]) / 2, CASA["y0"] - 0.55, 5.78))),
                            "direccion": dir_roblox(V((0, -0.37, -0.93))), "tipo": "SpotLight",
                            "color": "#DFF1FF", "brillo": 2.5, "alcance": 16, "angulo": 70,
                            "nota": "Encender con el sensor de movimiento (ProximityPrompt o zona) de noche."},
            "lab_interior": {"posicion": a_roblox(V((9.2, 0.4, 4.2))), "tipo": "PointLight", "color": "#E8F4FF",
                             "brillo": 1.2, "alcance": 8, "nota": "Ilumina los equipos que se ven por la ventana."},
            "casa_interior": {"posicion": a_roblox(V((1.0, -1.5, 5.6))), "tipo": "PointLight", "color": "#FFEBCC",
                              "brillo": 1.0, "alcance": 12, "nota": "Para que se vea la mesa y el monitor por la "
                                                                    "ventana."},
        },
        "anclajes": {
            "puerta_principal_paso": a_roblox(V(((PUERTA["x0"] + PUERTA["x1"]) / 2, CASA["y0"] - 1.4, 0.3))),
            "puerta_lab_paso": a_roblox(V(((PUERTA_LAB["x0"] + PUERTA_LAB["x1"]) / 2, LAB["y0"] - 1.2, 0.1))),
            "silla_asiento": a_roblox(V((SILLA["x"], SILLA["y"], 1.85))),
            "generador_boton": a_roblox(V((12.05, 2.0, 0.85))),
        },
        "medidas_studs": {
            "casa": [CASA["x1"] - CASA["x0"], round(Z_TECHO + CASA["peto"] + 0.07, 2), CASA["y1"] - CASA["y0"]],
            "lab": [LAB["x1"] - LAB["x0"], round(Z_TECHO_LAB + LAB["peto"] + 0.06, 2), LAB["y1"] - LAB["y0"]],
            "puerta_principal_hueco": [PUERTA["x1"] - PUERTA["x0"], PUERTA["z1"] - CASA["z0"]],
            "puerta_lab_hueco": [PUERTA_LAB["x1"] - PUERTA_LAB["x0"], round(PUERTA_LAB["z1"] - LAB["z0"], 2)],
        },
    }
    with open(os.path.join(salida, f"{NOMBRE}.json"), "w", encoding="utf-8") as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    print("[ok] JSON")


if __name__ == "__main__":
    main()
