"""
Kit de construcción del Valle del Alba, versión optimizada para móvil.

El estilo es el de la primera versión: pueblo europeo de cuento, yeso claro, sillares, tejas rojas, contraventanas
pintadas, farolas de hierro. Pero ahora el detalle pequeño (tejas, juntas, sillares, marcos, lamas, tablas) va
PINTADO EN EL ATLAS (atlas.py) y la geometría solo conserva lo que da volumen de verdad: el hueco de ventanas y
puertas, alféizares, aleros, cornisas y esquinas.

Reglas para que en Roblox se reutilicen:
  * Cada pieza es una malla que se exporta UNA vez y se copia muchas (los edificios son listas de piezas).
  * Cada pieza tiene UN color de instancia (el que se ve a través de las zonas teñibles del atlas). Por eso las
    contraventanas, la puerta o el toldo son piezas aparte de la pared: cada una lleva su color.
  * Ninguna colocación usa espejo (un CFrame de Roblox no puede reflejar): el lado derecho de un tejado o de un
    hastial es la misma pieza girada 180°.
  * Cada pieza tiene una versión DETALLADA y una SIMPLE para lejos (ver PIEZAS al final).
  * Las caras que nunca se ven (bases enterradas, la cara de una pieza pegada a la pared) no se crean.
  * Las paredes y los hastiales TIENEN GROSOR (MEDIDAS["grosor_pared"]): cara interior y cantos. Probado en Roblox:
    una pared de una sola cara desaparece desde dentro del edificio y de canto (Roblox solo dibuja la cara delantera
    de cada triángulo). La puerta y las contraventanas también son cerradas. Las lonas (toldo) son de una sola capa y
    se marcan DOBLE_CARA (en Roblox, MeshPart.DoubleSided). Las versiones de lejos siguen siendo una cara: de lejos
    solo se ven desde fuera.

Convención de las paredes: x ∈ [0, 8] a lo largo de la pared, cara exterior en y = 0 mirando a -Y (+Y es hacia
dentro del edificio), z ∈ [0, 10]. Escala: un R6 mide 5 studs; una puerta, 4 × 7,4.
"""

import math

import numpy as np

import atlas as AT
from malla import Malla, Rx, Ry, Rz, T, _normal, compone, uv_plano

MEDIDAS = dict(
    modulo=8.0,
    piso=10.0,
    pendiente=0.62,  # subida del tejado por stud horizontal (~32°)
    alero=1.3,
    vuelo=0.9,  # lo que sale el tejado por el hastial
    hondo_ventana=0.55,  # profundidad del hueco de la ventana
    hondo_puerta=0.6,
    grosor_pared=0.6,  # grosor de paredes y hastiales (hacia dentro: +Y). Igual que el hueco de la puerta
)
M = MEDIDAS["modulo"]
H = MEDIDAS["piso"]
PEND = MEDIDAS["pendiente"]
ALERO = MEDIDAS["alero"]
VUELO = MEDIDAS["vuelo"]
UV_FACHADA = uv_plano((0, 0, 0), (1, 0, 0), (0, 0, 1), M, H)  # la casilla de pared cubre el módulo entero
VENTANA = (AT.VENTANA[0] * M, AT.VENTANA[1] * H, AT.VENTANA[2] * M, AT.VENTANA[3] * H)  # x0, z0, x1, z1
PUERTA = (AT.PUERTA[0] * M, 0.0, AT.PUERTA[2] * M, AT.PUERTA[3] * H)
ESCAPARATE = (AT.ESCAPARATE[0] * M, AT.ESCAPARATE[1] * H, AT.ESCAPARATE[2] * M, AT.ESCAPARATE[3] * H)


def cara(m, pts, normal, mat, uv=None, liso=False):
    """Añade un polígono con la orientación que dé la normal pedida."""
    p = np.asarray(pts, float)
    if np.dot(_normal(p), normal) < 0:
        p = p[::-1]
    return m.poligono(p, mat, uv, liso)


def uv_recorte(x0, x1, z0, z1, u0, u1, v0, v1):
    """Proyección plana (en X y Z) que lleva el rectángulo [x0, x1] × [z0, z1] al trozo [u0, u1] × [v0, v1] de la
    casilla. Sirve para enseñar solo una parte de una casilla (la ventana de una pared, por ejemplo)."""
    su = (x1 - x0) / (u1 - u0)
    sv = (z1 - z0) / (v1 - v0)
    return uv_plano((x0 - u0 * su, 0, z0 - v0 * sv), (1, 0, 0), (0, 0, 1), su, sv)


def _rng(s):
    return np.random.default_rng(s)


def _cuadro(m, mat, uv=UV_FACHADA):
    return cara(m, [(0, 0, 0), (M, 0, 0), (M, 0, H), (0, 0, H)], (0, -1, 0), mat, uv)


# ==============================================================================================================
# Paredes
# ==============================================================================================================


G = MEDIDAS["grosor_pared"]
MAT_INTERIOR = "pared_lisa"  # el interior de todas las paredes: yeso liso (teñible, toma el color de la copia)


def _paños(x0, z0, x1, z1):
    """Los paños de un módulo de pared alrededor de un hueco (x0, z0, x1, z1); sin hueco, el módulo entero."""
    if x0 is None:
        return [(0, 0, M, H)]
    trozos = [(0, 0, x0, H), (x1, 0, M, H), (x0, z1, x1, H)]
    if z0 > 0:
        trozos.append((x0, 0, x1, z0))
    return trozos


def _dorso_pared(m, hueco=(None, None, None, None)):
    """Grosor de un módulo de pared: cara interior en y = G (mirando a +Y, con el mismo hueco) y canto de arriba.
    Sin cantos de los lados: los módulos siempre se juntan con otro o con la pared perpendicular de la esquina (en la
    esquina, ese canto quedaría en el mismo plano que la fachada de al lado y parpadearía). Sin canto de abajo: la
    pared apoya en el suelo o en el muro de debajo."""
    for (a, b, c, d) in _paños(*hueco):
        cara(m, [(a, G, b), (c, G, b), (c, G, d), (a, G, d)], (0, 1, 0), MAT_INTERIOR, UV_FACHADA)
    cara(m, [(0, 0, H), (M, 0, H), (M, G, H), (0, G, H)], (0, 0, 1), MAT_INTERIOR)
    return m


def _fachada_con_hueco(m, mat, x0, z0, x1, z1, hondo, fondo_mat, mat_jambas="piedra_clara"):
    """Módulo de pared con un hueco: paños del frente, caras del hueco (de todo el grosor de la pared), el fondo (el
    cristal, a `hondo`) y el dorso."""
    Y = np.array([0, -1.0, 0])
    for (a, b, c, d) in _paños(x0, z0, x1, z1):
        cara(m, [(a, 0, b), (c, 0, b), (c, 0, d), (a, 0, d)], Y, mat, UV_FACHADA)
    hd = G  # las jambas atraviesan la pared entera (si no, quedaría una rendija hasta la cara interior)
    if z0 > 0:
        cara(m, [(x0, 0, z0), (x1, 0, z0), (x1, hd, z0), (x0, hd, z0)], (0, 0, 1), mat_jambas)
    cara(m, [(x0, 0, z1), (x1, 0, z1), (x1, hd, z1), (x0, hd, z1)], (0, 0, -1), mat_jambas)
    cara(m, [(x0, 0, z0), (x0, hd, z0), (x0, hd, z1), (x0, 0, z1)], (1, 0, 0), mat_jambas)
    cara(m, [(x1, 0, z0), (x1, hd, z0), (x1, hd, z1), (x1, 0, z1)], (-1, 0, 0), mat_jambas)
    if fondo_mat:
        # El cristal solo por fuera: desde dentro de la casa se ve el exterior por la ventana.
        cara(m, [(x0, hondo, z0), (x1, hondo, z0), (x1, hondo, z1), (x0, hondo, z1)], Y, fondo_mat)
    return _dorso_pared(m, (x0, z0, x1, z1))


def _alfeizar(m, x0, x1, z, salida=0.45, alto=0.35):
    return m.caja((x0 - 0.5, -salida, z - alto), (x1 + 0.5, 0.0, z), "piedra_clara", sin=("+y",))


def pared_lisa(baja=False, mat=None):
    return _dorso_pared(_cuadro(Malla(), mat or ("pared_lisa_baja" if baja else "pared_lisa")))


def pared_ventana(baja=False, entramado=False):
    x0, z0, x1, z1 = VENTANA
    mat = "entramado_ventana" if entramado else ("pared_ventana_baja" if baja else "pared_ventana")
    m = _fachada_con_hueco(Malla(), mat, x0, z0, x1, z1, MEDIDAS["hondo_ventana"], "ventana",
                           "madera_oscura" if entramado else "piedra_clara")
    return _alfeizar(m, x0, x1, z0)


def pared_ventana_simple(baja=False, entramado=False):
    mat = "entramado_ventana_lejos" if entramado else ("pared_ventana_baja_lejos" if baja else "pared_ventana_lejos")
    return _cuadro(Malla(), mat)


def pared_puerta():
    x0, z0, x1, z1 = PUERTA
    m = _fachada_con_hueco(Malla(), "pared_puerta", x0, z0, x1, z1, MEDIDAS["hondo_puerta"], None)
    return m.caja((x0 - 0.8, -1.5, -0.6), (x1 + 0.8, 0.0, 0.0), "piedra_media", sin=("+y", "-z"))  # escalón


def puerta():
    """La hoja de la puerta (teñible), al fondo del hueco de pared_puerta: una tabla cerrada (se ve también desde
    dentro de la casa). Sin canto de abajo: apoya en el suelo."""
    x0, z0, x1, z1 = PUERTA
    y0 = MEDIDAS["hondo_puerta"] - 0.05  # la cara de fuera, donde estaba
    y1 = G - 0.02  # la de dentro, casi a ras de la cara interior de la pared
    return Malla().caja((x0, y0, 0.0), (x1, y1, z1), "puerta", sin=("-z",))


def pared_escaparate():
    x0, z0, x1, z1 = ESCAPARATE
    m = _fachada_con_hueco(Malla(), "pared_escaparate", x0, z0, x1, z1, 0.5, "escaparate", "madera_oscura")
    return _alfeizar(m, x0 + 0.3, x1 - 0.3, z0, 0.35, 0.3)


def contraventanas():
    """Las dos contraventanas abiertas contra la fachada, a los lados de la ventana (teñibles)."""
    x0, z0, x1, z1 = VENTANA
    w = (x1 - x0) / 2 + 0.05
    m = Malla()
    y = -0.14
    for a in (x0 - 0.5 - w, x1 + 0.5):
        cara(m, [(a, y, z0 + 0.1), (a + w, y, z0 + 0.1), (a + w, y, z1 - 0.1), (a, y, z1 - 0.1)], (0, -1, 0),
             "contraventana")
        za, zb = z0 + 0.1, z1 - 0.1
        # Cantos: los dos de los lados y el de arriba y el de abajo (sin ellos, de lado o desde abajo es una lámina).
        # La cara de atrás no hace falta: está pegada a la fachada.
        for xc, nx in ((a, -1), (a + w, 1)):
            cara(m, [(xc, y, za), (xc, 0, za), (xc, 0, zb), (xc, y, zb)], (nx, 0, 0), "contraventana")
        for zc, nz in ((za, -1), (zb, 1)):
            cara(m, [(a, y, zc), (a + w, y, zc), (a + w, 0, zc), (a, 0, zc)], (0, 0, nz), "contraventana")
    return m


def jardinera():
    x0, z0, x1, z1 = VENTANA
    m = Malla()
    m.caja((x0, -1.1, z0 - 1.25), (x1, -0.45, z0 - 0.35), "jardinera", sin=("+y", "+z"))
    a, b = -1.1, -0.45
    zt = z0 - 0.35
    mid = (a + b) / 2
    cara(m, [(x0, a, zt), (x1, a, zt), (x1, mid, zt + 0.7), (x0, mid, zt + 0.7)], (0, -1, 1), "flores")
    cara(m, [(x0, b, zt), (x1, b, zt), (x1, mid, zt + 0.7), (x0, mid, zt + 0.7)], (0, 1, 1), "flores")
    return m


def farolillo():
    """Farolillo de pared: brazo de hierro y farol de cristal cálido."""
    m = Malla()
    m.caja((-0.13, -1.3, 1.35), (0.13, 0.0, 1.6), "hierro", sin=("+y",))
    m.caja((-0.4, -1.55, -1.0), (0.4, -0.75, 0.2), "luz", sin=("+z",))
    m.tronco((0, -1.15, 0.2), 0.62, 0.12, 0.6, 4, "hierro", giro=45, tapa_abajo=False)
    m.caja((-0.1, -1.25, 0.75), (0.1, -1.05, 1.36), "hierro", solo=("-x", "+x", "-y", "+y"))  # colgador
    return m


def toldo():
    """Toldo a rayas (teñible) sobre un escaparate: lona inclinada, faldón festoneado y costados."""
    m = Malla()
    x0, x1 = 0.4, M - 0.4
    zs, zi, sal = 8.9, 7.6, 3.0
    cara(m, [(x0, 0, zs), (x1, 0, zs), (x1, -sal, zi), (x0, -sal, zi)], (0, -1, 1), "toldo")
    picos = 8
    p = [(x0, -sal, zi)]
    for k in range(picos):
        xa = x0 + (x1 - x0) * k / picos
        xb = x0 + (x1 - x0) * (k + 1) / picos
        p += [(xa, -sal, zi - 0.6), ((xa + xb) / 2, -sal, zi - 1.0)]
    p += [(x1, -sal, zi - 0.6), (x1, -sal, zi)]
    cara(m, p, (0, -1, 0), "toldo", uv_plano((x0, -sal, zi - 1.0), (1, 0, 0), (0, 0, 1), x1 - x0, 1.0))
    for x, nx in ((x0, -1), (x1, 1)):
        cara(m, [(x, 0, zs), (x, -sal, zi), (x, 0, zi)], (nx, 0, 0), "toldo")
    return m


def cartel(emblema):
    """Cartel colgante con el emblema de la tienda (en las dos caras)."""
    m = Malla()
    m.caja((-0.13, -3.0, 2.6), (0.13, 0.0, 2.85), "hierro", sin=("+y",))
    m.caja((-0.15, -2.9, -0.1), (0.15, -0.8, 2.3), "madera_media",
           mats={"-x": "cartel_" + emblema, "+x": "cartel_" + emblema})
    return m


def esquina(lejos=False):
    """Sillares de esquina de un piso para la esquina delantera izquierda (fachadas y = 0 y x = 0). Sobresale 0,2.
    Teñible: el yeso entre sillares toma el color de la pared."""
    m = Malla()
    s, w = 0.2, 1.9
    mat = "sillares"
    cara(m, [(-s, -s, 0), (w, -s, 0), (w, -s, H), (-s, -s, H)], (0, -1, 0), mat,
         uv_plano((-s, 0, 0), (1, 0, 0), (0, 0, 1), w + s, H))
    cara(m, [(-s, -s, 0), (-s, w, 0), (-s, w, H), (-s, -s, H)], (-1, 0, 0), mat,
         uv_plano((0, w, 0), (0, -1, 0), (0, 0, 1), w + s, H))
    if not lejos:
        cara(m, [(w, -s, 0), (w, 0, 0), (w, 0, H), (w, -s, H)], (1, 0, 0), "piedra_clara")
        cara(m, [(-s, w, 0), (0, w, 0), (0, w, H), (-s, w, H)], (0, 1, 0), "piedra_clara")
    return m


def cornisa(lejos=False):
    """Cornisa de un módulo (8 studs) en lo alto de la fachada."""
    m = Malla()
    if lejos:
        return cara(m, [(0, -0.45, 0), (M, -0.45, 0), (M, -0.45, 0.85), (0, -0.45, 0.85)], (0, -1, 0),
                    "piedra_clara")
    m.caja((0, -0.45, 0), (M, 0.0, 0.6), "piedra_clara", solo=("-y", "-z"))
    m.caja((0, -0.6, 0.6), (M, 0.0, 0.85), "piedra_clara", solo=("-y", "+z", "-z"))
    return m


def cornisa_esquina():
    m = Malla()
    m.caja((-0.45, -0.45, 0), (0.0, 0.0, 0.6), "piedra_clara", solo=("-y", "-x", "-z"))
    m.caja((-0.6, -0.6, 0.6), (0.0, 0.0, 0.85), "piedra_clara", solo=("-y", "-x", "+z", "-z"))
    return m


def losa(nx, ny):
    """Losa de piedra bajo un edificio de nx × ny módulos (baja a z = -4 para tapar desniveles)."""
    W, D = nx * M, ny * M
    return Malla().caja((-1.0, -1.0, -4.0), (W + 1.0, D + 1.0, 0.0), "piedra_media", sin=("-z",))


# ==============================================================================================================
# Tejados (cumbrera a lo largo de X; muros de y = 0 a y = fondo; z = 0 es lo alto de los muros)
# ==============================================================================================================


def _faldones(m, x0, x1, fondo, mat, detalle=True, uv_x0=None, uv_ancho=None):
    """Los dos faldones de un tramo de tejado de x0 a x1. La casilla de tejas cubre `uv_ancho` studs en X a partir
    de `uv_x0` (por defecto, el tramo entero)."""
    medio = fondo / 2
    sube = medio * PEND
    za = -ALERO * PEND
    g = 0.35  # grosor del faldón (el canto se ve en el alero)
    su = uv_ancho or (x1 - x0)
    ox = x0 if uv_x0 is None else uv_x0
    for lado in (-1, 1):
        ye = -ALERO if lado < 0 else fondo + ALERO
        A = np.array([x0, ye, za])
        B = np.array([x1, ye, za])
        C = np.array([x1, medio, sube])
        Dd = np.array([x0, medio, sube])
        n = _normal(np.array([A, B, C, Dd]))
        if n[2] < 0:
            n = -n
        up = n * g
        largo = np.linalg.norm(Dd - A)
        ev = (Dd - A) / largo
        # u hacia la derecha visto desde fuera: +X en el faldón delantero, -X en el trasero
        eu = np.array([1.0, 0, 0]) if lado < 0 else np.array([-1.0, 0, 0])
        u_cero = np.array([ox, 0, 0]) if lado < 0 else np.array([ox + su, 0, 0])
        Am = np.stack([eu / su, ev / largo])
        b = np.array([-(eu @ u_cero) / su, -(ev @ A) / largo])
        cara(m, [A + up, B + up, C + up, Dd + up], n, mat, ("plano", Am, b))
        if not detalle:
            cara(m, [A, B, C, Dd], -n, "madera_oscura")  # panza: desde abajo el vuelo del tejado no es transparente
        if detalle:
            cara(m, [A, B, B + up, A + up], -ev, "teja_lejos")  # canto del alero
            cara(m, [A, B, C, Dd], -n, "madera_oscura")  # panza (se ve desde abajo)
            cara(m, [(x0, ye, za - 0.5), (x1, ye, za - 0.5), (x1, ye, za + 0.05), (x0, ye, za + 0.05)],
                 (0, lado, 0), "madera_oscura")  # tabla de alero
    return m


def _mat_teja(fondo, lejos):
    return "teja_lejos" if lejos else ("teja_16" if fondo <= 16 else "teja_24")


def tejado_tramo(fondo, lejos=False):
    """Tramo de tejado a dos aguas de un módulo (x ∈ [0, 8]) sobre muros de fondo `fondo`."""
    return _faldones(Malla(), 0.0, M, fondo, _mat_teja(fondo, lejos), detalle=not lejos)


def tejado_remate(fondo, lejos=False):
    """Vuelo del tejado sobre el hastial izquierdo (x ∈ [-0,9, 0]) con sus tablas de canto. El derecho es esta misma
    pieza girada 180° alrededor del centro del edificio (sin espejo)."""
    m = _faldones(Malla(), -VUELO, 0.0, fondo, _mat_teja(fondo, lejos), detalle=not lejos, uv_x0=-VUELO, uv_ancho=M)
    medio = fondo / 2
    sube = medio * PEND
    za = -ALERO * PEND
    for y0 in (-ALERO, fondo + ALERO):
        p0 = np.array([-VUELO, y0, za - 0.3])
        p1 = np.array([-VUELO, medio, sube - 0.1])
        q0, q1 = p0 + (0, 0, 0.75), p1 + (0, 0, 0.75)
        cara(m, [p0, p1, q1, q0], (-1, 0, 0), "madera_oscura")
        if not lejos:
            cara(m, [q0, q1, q1 + (0.3, 0, 0), q0 + (0.3, 0, 0)], (0, 0, 1), "madera_oscura")
    return m


def hastial(fondo):
    """Muro triangular del hastial izquierdo (cara exterior en x = 0, mirando a -X). Teñible, con óculo pintado."""
    medio = fondo / 2
    top = medio * PEND
    m = cara(Malla(), [(0, 0, 0), (0, fondo, 0), (0, medio, top)], (-1, 0, 0), "hastial")
    # Grosor (hacia dentro, +X): cara interior. Los cantos inclinados quedan bajo el vuelo del tejado y el de abajo
    # apoya en el muro: no se ven.
    cara(m, [(G, 0, 0), (G, fondo, 0), (G, medio, top)], (1, 0, 0), MAT_INTERIOR)
    return m


def cumbrera(fondo, largo=M):
    """Caballete a lo largo de la cumbre, de x = 0 a x = largo (dos caras inclinadas)."""
    m = Malla()
    medio = fondo / 2
    z = medio * PEND + 0.35
    w, h = 0.55, 0.45
    for lado in (-1, 1):
        cara(m, [(0, medio + lado * w, z), (largo, medio + lado * w, z), (largo, medio, z + h), (0, medio, z + h)],
             (0, lado, 1), "cumbrera")
    # Tapas de los extremos (mirando a lo largo de la cumbre se veía el hueco).
    for x, nx in ((0, -1), (largo, 1)):
        cara(m, [(x, medio - w, z), (x, medio + w, z), (x, medio, z + h)], (nx, 0, 0), "cumbrera")
    return m


def chimenea(alto=6.0, lejos=False):
    m = Malla()
    m.caja((-1.1, -1.1, 0), (1.1, 1.1, alto), "ladrillo", solo=("-x", "+x", "-y", "+y") + (("+z",) if lejos else ()))
    if not lejos:
        m.caja((-1.45, -1.45, alto), (1.45, 1.45, alto + 0.45), "piedra_clara")
    return m


def tejado_piramide(lado, pendiente, alero=1.4, lejos=False):
    """Pirámide de cuatro faldones sobre el cuadrado [0, lado]²."""
    m = Malla()
    a = lado + 2 * alero
    x0 = -alero
    za = -alero * pendiente
    cima = np.array([lado / 2, lado / 2, za + a / 2 * pendiente])
    esq = [np.array(p, float) for p in ((x0, x0, za), (x0 + a, x0, za), (x0 + a, x0 + a, za), (x0, x0 + a, za))]
    for i in range(4):
        p, q = esq[i], esq[(i + 1) % 4]
        n = _normal(np.array([p, q, cima]))
        if n[2] < 0:
            n = -n
        cara(m, [p, q, cima], n, "teja_lejos" if lejos else "teja_24")
        if not lejos:
            cara(m, [p, q, q + (0, 0, -0.5), p + (0, 0, -0.5)], n * np.array([1, 1, 0]), "madera_oscura")
    return m


# ==============================================================================================================
# Mobiliario
# ==============================================================================================================


def farola(lejos=False, alto=12.0):
    m = Malla()
    zt = alto - 2.0
    if lejos:
        m.caja((-0.25, -0.25, 0), (0.25, 0.25, zt), "hierro", solo=("-x", "+x", "-y", "+y"))
        m.caja((-0.6, -0.6, zt), (0.6, 0.6, zt + 1.4), "luz", solo=("-x", "+x", "-y", "+y", "+z"))
        return m
    m.tronco((0, 0, 0), 0.95, 0.75, 1.2, 6, "piedra_clara", tapa_abajo=False)
    m.tronco((0, 0, 1.2), 0.24, 0.2, alto - 3.2, 6, "hierro", tapa_abajo=False, tapa_arriba=False)
    m.tronco((0, 0, zt - 0.2), 0.35, 0.7, 0.3, 4, "hierro", giro=45, tapa_arriba=False)
    m.tronco((0, 0, zt + 0.1), 0.62, 0.72, 1.4, 4, "luz", giro=45, tapa_abajo=False, tapa_arriba=False)
    m.tronco((0, 0, zt + 1.5), 1.05, 0.0, 0.85, 4, "hierro", giro=45)
    return m


def banco(lejos=False):
    m = Malla()
    m.caja((0, -0.9, 1.6), (5, 0.9, 1.9), "madera_clara", sin=("-z",) if lejos else ())
    m.caja((0, 0.6, 1.9), (5, 0.95, 3.4), "madera_clara", sin=("-z",))
    if not lejos:
        for x in (0.3, 4.3):
            m.caja((x, -0.8, 0), (x + 0.4, 0.8, 1.6), "hierro", sin=("+z", "-z"))
    return m


def barril(lejos=False):
    if lejos:
        return Malla().torno([(1.0, 0), (1.2, 1.5), (1.0, 3.0)], 6, "madera_media", tapas=True)
    return Malla().torno([(1.0, 0), (1.18, 0.8), (1.22, 1.5), (1.18, 2.2), (1.0, 3.0)], 8,
                         ["madera_media", "hierro", "madera_media", "madera_media"])


def caja_madera(lado=2.4):
    return Malla().caja((0, 0, 0), (lado, lado, lado), "madera_clara", sin=("-z",))


def maceta():
    m = Malla()
    m.tronco((0, 0, 0), 1.3, 1.65, 2.0, 6, "piedra_clara", tapa_abajo=False)
    m.esfera((0, 0, 2.6), 1.6, "flores", sub=0, jitter=0.12, rng=_rng(3), escala=(1, 1, 0.8))
    return m


def valla_madera(lejos=False):
    m = Malla()
    if not lejos:
        for x in (0.0, 4.0, 8.0):
            m.caja((x - 0.28, -0.28, -0.6), (x + 0.28, 0.28, 4.0), "madera_media", sin=("-z",))
    for z in (1.5, 3.0):
        m.caja((0, -0.42, z - 0.22), (M, -0.28, z + 0.22), "madera_clara", solo=("-y", "+y", "+z"))
    return m


def valla_piedra(lejos=False):
    m = Malla()
    m.caja((0, -0.8, -0.4), (M, 0.8, 2.1), "sillar_muro", sin=("-z",) + (("+z",) if not lejos else ()))
    if not lejos:
        m.caja((-0.1, -0.95, 2.1), (M + 0.1, 0.95, 2.55), "piedra_clara", sin=("-z",))
    return m


def puesto(lejos=False, ancho=8.0, fondo=5.0):
    """Puesto de mercado: estructura de madera, mostrador con género y toldo (el color de la instancia es el toldo)."""
    m = Malla()
    if not lejos:
        for x in (0.3, ancho - 0.3):
            for y, h in ((0.3, 7.0), (fondo - 0.3, 8.6)):
                m.caja((x - 0.3, y - 0.3, 0), (x + 0.3, y + 0.3, h), "madera_media", solo=("-x", "+x", "-y", "+y"))
        for k in range(3):
            x0 = 0.6 + k * (ancho - 1.2) / 3
            m.caja((x0, -0.1, 3.4), (x0 + 2.0, 1.5, 4.4), "fruta", sin=("-z",))
    m.caja((0, -0.2, 0), (ancho, 1.6, 3.4), "madera_clara", sin=("-z",))
    cara(m, [(-0.4, fondo + 0.3, 8.9), (ancho + 0.4, fondo + 0.3, 8.9), (ancho + 0.4, -1.6, 6.8), (-0.4, -1.6, 6.8)],
         (0, -1, 1), "toldo")
    cara(m, [(-0.4, -1.6, 6.8), (ancho + 0.4, -1.6, 6.8), (ancho + 0.4, -1.6, 5.9), (-0.4, -1.6, 5.9)], (0, -1, 0),
         "toldo")
    return m


def tablon_misiones(lejos=False):
    """Tablón de misiones: dos postes, tablero con papeles en las dos caras, tejadillo (color de la instancia) y un
    «!» dorado encima."""
    m = Malla()
    for x in (-4.2, 4.2):
        m.caja((x - 0.45, -0.45, 0), (x + 0.45, 0.45, 10.2), "madera_oscura", solo=("-x", "+x", "-y", "+y"))
        if not lejos:
            m.caja((x - 0.8, -0.8, 0), (x + 0.8, 0.8, 0.8), "piedra_clara", sin=("-z",))
    m.caja((-3.9, -0.3, 2.4), (3.9, 0.3, 8.6), "madera_oscura", mats={"-y": "tablon", "+y": "tablon"})
    for lado in (-1, 1):
        cara(m, [(-5.2, 0, 11.6), (5.2, 0, 11.6), (5.2, lado * 2.2, 10.0), (-5.2, lado * 2.2, 10.0)], (0, lado, 1),
             "teja_lejos" if lejos else "teja_16")
    if lejos:
        m.caja((-0.45, -0.3, 11.9), (0.45, 0.3, 15.6), "oro", solo=("-y", "+y"))
    else:
        m.caja((-0.45, -0.3, 12.8), (0.45, 0.3, 15.6), "oro", sin=("-z",))
        m.caja((-0.45, -0.3, 11.9), (0.45, 0.3, 12.5), "oro", sin=("-z",))
    return m


def pozo(lejos=False):
    m = Malla()
    n = 6 if lejos else 8
    m.tronco((0, 0, 0), 2.6, 2.6, 2.8, n, "sillar_muro", tapa_abajo=False, tapa_arriba=False)
    m.tronco((0, 0, 2.8), 2.85, 2.85, 0.4, n, "piedra_clara", tapa_abajo=False)
    if not lejos:
        for y in (-2.3, 2.3):
            m.caja((-0.3, y - 0.3, 2.8), (0.3, y + 0.3, 8.0), "madera_oscura", solo=("-x", "+x", "-y", "+y"))
        m.viga((0, -2.6, 6.6), (0, 2.6, 6.6), 0.35, "madera_media")
    for lado in (-1, 1):
        cara(m, [(0, -3.2, 9.6), (0, 3.2, 9.6), (lado * 3.5, 3.2, 7.4), (lado * 3.5, -3.2, 7.4)], (lado, 0, 1),
             "teja_lejos" if lejos else "teja_16")
    return m


def carro(lejos=False):
    m = Malla()
    m.caja((-3.0, -1.8, 1.8), (3.0, 1.8, 3.4), "madera_media", sin=("+z",) if not lejos else ())
    if not lejos:
        m.caja((-2.8, -1.6, 2.3), (2.8, 1.6, 3.2), "paja", solo=("+z",))
        for y in (-2.1, 2.1):
            m.anadir(Malla().tronco((0, 0, -0.2), 1.6, 1.6, 0.4, 8, "madera_oscura"), compone(T(0.6, y, 1.6), Rx(90)))
        m.viga((3.0, -0.6, 2.0), (7.0, -0.6, 1.0), 0.3, "madera_media")
        m.viga((3.0, 0.6, 2.0), (7.0, 0.6, 1.0), 0.3, "madera_media")
    return m


def pajar(lejos=False):
    if lejos:
        return Malla().torno([(3.0, 0), (2.8, 3.4), (0.0, 6.0)], 6, "paja", tapas=False)
    return Malla().torno([(3.0, 0), (3.2, 1.6), (2.8, 3.4), (1.8, 4.8), (0.6, 5.7), (0.0, 6.0)], 9, "paja",
                         tapas=False)


def espantapajaros(lejos=False):
    m = Malla()
    m.caja((-0.2, -0.2, 0), (0.2, 0.2, 7.5), "madera_media", solo=("-x", "+x", "-y", "+y"))
    m.caja((-2.6, -0.15, 5.6), (2.6, 0.15, 5.9), "madera_media", solo=("-y", "+y", "+z", "-z"))
    m.tronco((0, 0, 3.4), 1.2, 1.5, 2.6, 4 if lejos else 6, "toldo", tapa_abajo=False)
    if not lejos:
        m.esfera((0, 0, 6.8), 0.8, "paja", sub=0)
        m.tronco((0, 0, 7.3), 1.6, 0.6, 0.4, 8, "paja")
        m.tronco((0, 0, 7.7), 0.7, 0.0, 1.2, 6, "paja", tapa_abajo=False)
    return m


def portal(lejos=False, ancho=16.0):
    """Entrada de ciudad: dos pilares de sillería (las farolas y los muretes son piezas aparte)."""
    m = Malla()
    for sgn in (-1, 1):
        x = sgn * (ancho / 2 + 1.8)
        m.caja((x - 1.5, -1.5, -1.0), (x + 1.5, 1.5, 11.0), "sillar_muro", solo=("-x", "+x", "-y", "+y"))
        m.caja((x - 2.0, -2.0, 11.0), (x + 2.0, 2.0, 11.8), "piedra_clara")
        if not lejos:
            m.caja((x - 1.8, -1.8, -1.0), (x + 1.8, 1.8, 1.2), "piedra_media", sin=("-z",))
            m.tronco((x, 0, 11.8), 1.4, 0.5, 1.2, 4, "piedra_clara", giro=45, tapa_abajo=False)
    return m


def poste_indicador(lejos=False, rumbos=(0.0, 120.0, 230.0)):
    m = Malla()
    m.caja((-0.35, -0.35, -1.0), (0.35, 0.35, 9.0), "madera_oscura", solo=("-x", "+x", "-y", "+y"))
    m.tronco((0, 0, 9.0), 0.55, 0.0, 0.7, 4, "madera_oscura", giro=45, tapa_abajo=False)
    for k, r in enumerate(rumbos if not lejos else rumbos[:1]):
        f = Malla().prisma([(0.3, -0.5), (3.6, -0.5), (4.5, 0.0), (3.6, 0.5), (0.3, 0.5)], 0, 0.25, "madera_clara")
        m.anadir(f, compone(T(0, 0, 7.8 - 1.25 * k), Rz(r), Rx(90)))
    return m


# ==============================================================================================================
# Piezas especiales
# ==============================================================================================================


def fuente(lejos=False, radio=9.0):
    """Fuente de la plaza: pilón octogonal, dos tazas, surtidor y chorros."""
    m = Malla()
    n, g = 8, 22.5
    if lejos:
        m.tronco((0, 0, 0), radio, radio, 3.0, n, "piedra_clara", giro=g, tapa_abajo=False, tapa_arriba=False)
        m.tronco((0, 0, 2.2), radio - 0.3, radio - 0.3, 0.1, n, "agua", giro=g, tapa_abajo=False)
        m.torno([(1.6, 2.0), (1.2, 7.0), (4.6, 8.6), (0.6, 9.0), (0.3, 13.6)], 6, "piedra_clara", tapas=False)
        return m
    m.tronco((0, 0, -0.6), radio + 1.2, radio + 1.2, 0.8, n, "piedra_media", giro=g, tapa_abajo=False)
    m.tronco((0, 0, 0.2), radio, radio, 2.4, n, "piedra_clara", giro=g, tapa_abajo=False, tapa_arriba=False)
    m.torno([(radio + 0.35, 2.6), (radio + 0.35, 3.1), (radio - 1.3, 3.1), (radio - 1.3, 2.4)], n, "piedra_clara",
            giro=g, tapas=False)
    m.tronco((0, 0, 2.0), radio - 1.3, radio - 1.3, 0.05, n, "agua", giro=g, tapa_abajo=False)
    m.torno([(1.9, 2.0), (1.3, 3.0), (1.2, 6.2), (1.5, 7.0)], 8, "piedra_clara", tapas=False)
    m.torno([(1.4, 6.8), (3.4, 7.6), (4.7, 8.6), (4.8, 9.0), (4.2, 9.0)], 10, "piedra_clara", tapas=False)
    m.tronco((0, 0, 8.7), 4.3, 4.3, 0.05, 10, "agua", tapa_abajo=False)
    m.torno([(0.9, 8.6), (0.7, 10.0), (0.9, 11.2), (2.0, 11.6), (2.4, 12.2), (2.0, 12.3)], 8, "piedra_clara",
            tapas=False)
    m.tronco((0, 0, 12.0), 2.0, 2.0, 0.05, 8, "agua", tapa_abajo=False)
    m.torno([(0.45, 12.0), (0.3, 13.2), (0.55, 13.6), (0.0, 14.4)], 6, "oro", tapas=False)
    for k in range(8):  # chorros: cintas de agua con sus dos caras
        a = 2 * math.pi * k / 8
        e = np.array([math.cos(a), math.sin(a), 0])
        t = np.array([-math.sin(a), math.cos(a), 0]) * 0.18
        for (r0, z0, r1, z1, r2, z2) in ((2.3, 12.1, 3.4, 10.6, 3.8, 9.0), (4.7, 8.8, 6.0, 5.8, 6.4, 2.0)):
            p0, p1, p2 = e * r0 + (0, 0, z0), e * r1 + (0, 0, z1), e * r2 + (0, 0, z2)
            for (a_, b_) in ((p0, p1), (p1, p2)):
                cara(m, [a_ - t, a_ + t, b_ + t, b_ - t], e, "agua")
                cara(m, [a_ - t, a_ + t, b_ + t, b_ - t], -e, "agua")
    return m


def torre_reloj(lejos=False):
    """Torre del reloj de Aurora (~92 studs con el chapitel): basa de sillería, fuste con ventanas, cuerpo del reloj
    y campanario. El color de la instancia es el del yeso; el chapitel es otra pieza (color de las tejas)."""
    m = Malla()
    a = 14.0
    h2 = a / 2
    m.caja((-h2 - 1, -h2 - 1, -1.0), (h2 + 1, h2 + 1, 6.6), "sillar_muro", sin=("-z",))
    z0, z1 = 55.5, 66.0
    for r in (0, 90, 180, 270):
        f = Malla()
        if lejos:
            cara(f, [(-h2, -h2, 6.6), (h2, -h2, 6.6), (h2, -h2, 41), (-h2, -h2, 41)], (0, -1, 0), "pared_lisa")
        else:
            for zb in (6.6, 16.6, 26.6):
                for (xa, xb) in ((-h2, -1.5), (1.5, h2)):
                    cara(f, [(xa, -h2, zb), (xb, -h2, zb), (xb, -h2, zb + 10), (xa, -h2, zb + 10)], (0, -1, 0),
                         "pared_lisa", uv_plano((xa, -h2, zb), (1, 0, 0), (0, 0, 1), 8, 10))
                # tira central: la ventana de la casilla lejana (3 studs de ancho = el hueco de la casilla)
                cara(f, [(-1.5, -h2, zb), (1.5, -h2, zb), (1.5, -h2, zb + 10), (-1.5, -h2, zb + 10)], (0, -1, 0),
                     "pared_ventana_lejos", uv_plano((-4.0, -h2, zb), (1, 0, 0), (0, 0, 1), 8, 10))
            cara(f, [(-h2, -h2, 36.6), (h2, -h2, 36.6), (h2, -h2, 41), (-h2, -h2, 41)], (0, -1, 0), "pared_lisa")
        b = h2 + 0.8
        cara(f, [(-b, -b, 41), (b, -b, 41), (b, -b, 54), (-b, -b, 54)], (0, -1, 0), "piedra_clara")
        cara(f, [(-4.6, -b - 0.1, 43), (4.6, -b - 0.1, 43), (4.6, -b - 0.1, 52.2), (-4.6, -b - 0.1, 52.2)],
             (0, -1, 0), "reloj")
        if lejos:
            cara(f, [(-h2, -h2, 54), (h2, -h2, 54), (h2, -h2, z1 + 1), (-h2, -h2, z1 + 1)], (0, -1, 0), "pared_lisa")
        else:
            cara(f, [(-b, -b, 41), (b, -b, 41), (h2, -h2, 41), (-h2, -h2, 41)], (0, 0, -1), "piedra_clara")
            f.caja((-b - 0.4, -b - 0.4, 54), (b + 0.4, -b, 54.9), "piedra_clara", solo=("-y", "+z", "-z"))
            # campanario: parteluz, antepecho y dos vanos de medio punto
            f.caja((-1.0, -h2, z0), (1.0, -h2 + 1.2, z1), "pared_lisa", solo=("-y", "-x", "+x", "+y"))
            f.caja((-h2 + 1.8, -h2 + 0.2, z0), (h2 - 1.8, -h2 + 0.5, z0 + 1.6), "piedra_clara",
                   solo=("-y", "+z", "+y"))
            for cx in (-3.0, 3.0):
                w = 2.0
                zc = z1 - 3.0
                nseg = 6
                arco = [(cx + w * math.cos(math.pi * k / nseg), zc + w * math.sin(math.pi * k / nseg))
                        for k in range(nseg, -1, -1)]
                contorno = arco + [(cx + w, z1), (cx - w, z1)]
                for yy, nn in ((-h2, -1), (-h2 + 1.2, 1)):
                    cara(f, [(x, yy, z) for (x, z) in contorno], (0, nn, 0), "pared_lisa")
                for k in range(len(arco) - 1):  # intradós
                    (xa, za), (xb, zb) = arco[k], arco[k + 1]
                    cara(f, [(xa, -h2, za), (xb, -h2, zb), (xb, -h2 + 1.2, zb), (xa, -h2 + 1.2, za)],
                         (cx - (xa + xb) / 2, 0, zc - (za + zb) / 2), "piedra_clara")
            f.caja((-b - 0.4, -b - 0.4, z1), (b + 0.4, -b, z1 + 1.1), "piedra_clara", solo=("-y", "+z", "-z"))
        m.anadir(f, Rz(r))
    if not lejos:
        for r in (0, 90, 180, 270):
            for k in range(3):
                m.anadir(esquina(), compone(Rz(r), T(-h2, -h2, 6.6 + k * H)))
        for sx in (-1, 1):
            for sy in (-1, 1):
                xa, xb = (h2 - 1.8, h2) if sx > 0 else (-h2, -h2 + 1.8)
                ya, yb = (h2 - 1.8, h2) if sy > 0 else (-h2, -h2 + 1.8)
                m.caja((xa, ya, z0), (xb, yb, z1), "pared_lisa", solo=("-x", "+x", "-y", "+y"))
        m.torno([(0.0, 0.0), (2.3, 0.0), (1.5, 2.6), (0.8, 4.2), (0.0, 4.3)], 8, "oro", c=(0, 0, z0 + 2.6),
                tapas=False)
    return m


def chapitel(lejos=False):
    """Chapitel de la torre del reloj (color de las tejas), con remate dorado. Origen: centro de la torre."""
    a = 14.0
    m = tejado_piramide(a, 2.6, 1.4, lejos).transformada(T(-a / 2, -a / 2, 0))
    zt = a / 2 * 2.6
    if not lejos:
        m.tronco((0, 0, zt - 0.5), 0.9, 0.5, 2.0, 6, "oro", tapa_abajo=False)
        m.esfera((0, 0, zt + 2.0), 0.8, "oro", sub=0)
        m.viga((0, 0, zt + 2.5), (0, 0, zt + 7.5), 0.25, "hierro")
    return m


def molino_torre(lejos=False):
    """Torre del molino (color de la instancia: el encalado). La caperuza y las aspas son piezas aparte."""
    m = Malla()
    n = 6 if lejos else 8
    giro = 30 if lejos else 0
    m.torno([(7.6, 1.4), (6.0, 26.0), (6.4, 26.6)], n, "pared_lisa", tapas=False, giro=giro)
    m.tronco((0, 0, -1.0), 8.7, 8.5, 2.6, n, "sillar_muro", tapa_abajo=False, giro=giro)
    if lejos:
        return m
    ap = math.cos(math.pi / n)

    def r_en(z):
        return (7.6 - 1.6 * (z - 1.4) / 24.6) * ap

    # puerta y ventanucos: paños con un trozo de casilla de pared lejana, pegados a la torre (8 caras: una mira a -Y
    # cuando el giro es múltiplo de 45° más 22,5°... con giro 0 las caras miran a 22,5° + 45°·k; se usan 247,5°...)
    huecos = ((1.6, 9.6, -3.0, 3.0, "pared_puerta_lejos", (0.125, 0.875, 0.0, 0.85)),
              (10.0, 15.0, -2.2, 2.2, "pared_ventana_lejos", (0.04, 0.96, 0.27, 0.79)),
              (16.0, 21.0, -2.2, 2.2, "pared_ventana_lejos", (0.04, 0.96, 0.27, 0.79)))
    for k, (z0, z1, x0, x1, mat, (u0, u1, v0, v1)) in enumerate(huecos):
        f = Malla()
        y0, y1 = -r_en(z0) - 0.06, -r_en(z1) - 0.06
        cara(f, [(x0, y0, z0), (x1, y0, z0), (x1, y1, z1), (x0, y1, z1)], (0, -1, 0), mat,
             uv_recorte(x0, x1, z0, z1, u0, u1, v0, v1))
        # con 8 lados y giro 0 hay una cara plana mirando a -Y girando 22,5°: se orienta cada hueco a una cara
        m.anadir(f, Rz(22.5 + 90 * k))
    return m


def molino_caperuza(lejos=False):
    """Caperuza cónica del molino (color de las tejas)."""
    n = 6 if lejos else 8
    perfil = [(6.9, 26.6), (0.0, 36.4)] if lejos else [(6.9, 26.6), (6.6, 28.4), (4.6, 32.6), (0.0, 36.4)]
    m = Malla().torno(perfil, n, "teja_lejos" if lejos else "teja_24", tapas=False)
    m.tronco((0, 0, 26.2), 6.9, 6.9, 0.4, n, "madera_oscura", tapa_arriba=False)
    return m


def molino_aspas(lejos=False):
    """Las cuatro aspas con su eje (miran a -Y; el centro del eje en el origen)."""
    m = Malla()
    largo = 25.0
    for k in range(4):
        a = Malla()
        if not lejos:
            a.caja((-0.45, -0.45, 0), (0.45, 0.45, largo), "madera_oscura", solo=("-x", "+x", "-y", "+y"))
        for yy, nn in ((-0.1, -1), (0.1, 1)):  # lona con la celosía pintada, dos caras
            cara(a, [(0.5, yy, 5.0), (4.6, yy, 5.0), (4.6, yy, largo), (0.5, yy, largo)], (0, nn, 0), "vela")
        m.anadir(a, Ry(90 * k))
    if not lejos:
        m.anadir(Malla().tronco((0, 0, 0), 1.2, 0.9, 3.5, 6, "madera_oscura", tapa_abajo=False), Rx(-90))
    return m


def puente(largo=64.0, ancho=13.0, alto=8.0, arcos=3, lejos=False):
    """Puente de piedra de `arcos` ojos a lo largo de X, centrado en el origen, con el tablero en z = 0."""
    m = Malla()
    L = largo
    w = ancho / 2
    luz = L / (arcos + 0.6 * (arcos - 1) + 0.6)
    pila = 0.6 * luz
    x = -L / 2 + 0.3 * luz
    centros = []
    for k in range(arcos):
        centros.append(x + luz / 2)
        x += luz + pila
    r = luz / 2
    kz = alto * 0.85 / r
    nseg = 4 if lejos else 8
    xs, zs = [-L / 2 - 2.0], [-12.0]
    for c in centros:  # contorno del paramento: abajo sigue los arcos; arriba, el tablero
        xs.append(c - r)
        zs.append(-12.0)
        for k in range(nseg + 1):
            ang = math.pi - math.pi * k / nseg
            xs.append(c + r * math.cos(ang))
            zs.append(-alto + r * math.sin(ang) * kz)
        xs.append(c + r)
        zs.append(-12.0)
    xs += [L / 2 + 2.0, L / 2 + 2.0, -L / 2 - 2.0]
    zs += [-12.0, 0.0, 0.0]
    for yy, nn in ((-w + 0.3, -1), (w - 0.3, 1)):
        cara(m, [(x_, yy, z_) for x_, z_ in zip(xs, zs)], (0, nn, 0), "sillar_muro",
             uv_plano((-L / 2, yy, -12), (1, 0, 0), (0, 0, 1), 12, 12))
    for c in centros:  # intradós
        for k in range(nseg):
            a0, a1 = math.pi - math.pi * k / nseg, math.pi - math.pi * (k + 1) / nseg
            p0 = (c + r * math.cos(a0), -alto + r * math.sin(a0) * kz)
            p1 = (c + r * math.cos(a1), -alto + r * math.sin(a1) * kz)
            cara(m, [(p0[0], -w + 0.3, p0[1]), (p1[0], -w + 0.3, p1[1]), (p1[0], w - 0.3, p1[1]),
                     (p0[0], w - 0.3, p0[1])], (c - (p0[0] + p1[0]) / 2, 0, -1), "piedra_media")
    cara(m, [(-L / 2 - 2, -w + 0.3, 0.0), (L / 2 + 2, -w + 0.3, 0.0), (L / 2 + 2, w - 0.3, 0.0),
             (-L / 2 - 2, w - 0.3, 0.0)], (0, 0, 1), "piedra_oscura")
    # Testeros: los extremos del puente cerrados (por ahí se veía el interior, sin caras, al llegar al puente).
    for xe, nx in ((-L / 2 - 2.0, -1), (L / 2 + 2.0, 1)):
        cara(m, [(xe, -w + 0.3, -12.0), (xe, w - 0.3, -12.0), (xe, w - 0.3, 0.0), (xe, -w + 0.3, 0.0)], (nx, 0, 0),
             "sillar_muro")
    for lado in (-1, 1):
        y0 = -w if lado < 0 else w - 1.4
        m.caja((-L / 2 - 2.0, y0, 0.0), (L / 2 + 2.0, y0 + 1.4, 3.2), "sillar_muro", sin=("-z",))  # pretil cerrado
        if not lejos:
            for xe in (-L / 2 - 1.5, L / 2 + 1.5):
                m.caja((xe - 1.2, y0 - 0.3, 0.0), (xe + 1.2, y0 + 1.7, 4.2), "piedra_clara", sin=("-z",))
    if not lejos:  # tajamares
        for k in range(arcos - 1):
            xp = (centros[k] + centros[k + 1]) / 2
            for lado in (-1, 1):
                tri = [(xp - pila / 2, lado * (w - 0.3)), (xp + pila / 2, lado * (w - 0.3)),
                       (xp, lado * (w + pila * 0.7))]
                if lado < 0:
                    tri = tri[::-1]
                m.prisma(tri, -12.0, -alto * 0.45, "sillar_muro", tapas=False)
                m.tronco((xp, lado * (w + pila * 0.2), -alto * 0.45), pila * 0.62, 0.0, 2.2, 3, "piedra_clara",
                         giro=90 if lado > 0 else -90, tapa_abajo=False)
    return m


def portada_ayuntamiento(lejos=False, ancho=48.0):
    """Portada del ayuntamiento: escalinata, columnas, entablamento, balcón, frontón con reloj y banderas (el color
    de la instancia es el de las banderas). Origen: esquina delantera izquierda del edificio (fachada en y = 0)."""
    m = Malla()
    cx = ancho / 2
    for k in range(3):
        m.caja((cx - 10 - 1.2 * (2 - k), -7.0 + 1.6 * k, -4.0), (cx + 10 + 1.2 * (2 - k), 0.0, -0.6 + 0.2 * k),
               "piedra_clara", sin=("-z", "+y"))
    for xc in (cx - 8.5, cx - 3.2, cx + 3.2, cx + 8.5):
        if lejos:
            m.caja((xc - 0.9, -5.1, 0), (xc + 0.9, -3.3, 10), "piedra_clara", solo=("-y", "-x", "+x"))
            continue
        m.tronco((xc, -4.2, -0.2), 1.3, 1.3, 0.9, 6, "piedra_clara", tapa_abajo=False)
        m.tronco((xc, -4.2, 0.7), 0.92, 0.85, 8.6, 8, "piedra_clara", tapa_abajo=False, tapa_arriba=False)
        m.tronco((xc, -4.2, 9.3), 1.0, 1.35, 0.8, 6, "piedra_clara", tapa_abajo=False)
    m.caja((cx - 10.5, -5.8, 10.1), (cx + 10.5, 0.0, 11.6), "piedra_clara", sin=("+y",))
    m.caja((cx - 10.5, -5.8, 11.6), (cx + 10.5, 0.0, 12.0), "piedra_media", sin=("+y", "-z"))
    if not lejos:  # barandilla del balcón: barandal y balaustres
        m.caja((cx - 10.4, -5.75, 14.5), (cx + 10.4, -5.25, 14.9), "hierro", sin=("+y",))
        for k in range(9):
            x = cx - 10.2 + k * 20.4 / 8
            m.caja((x - 0.12, -5.6, 12.0), (x + 0.12, -5.36, 14.5), "hierro", solo=("-y", "-x", "+x"))
    zt = H * 3
    cara(m, [(cx - 11.5, -1.6, zt - 0.6), (cx + 11.5, -1.6, zt - 0.6), (cx, -1.6, zt + 6.9)], (0, -1, 0),
         "piedra_clara")
    for sgn in (-1, 1):
        p0, p1 = np.array([cx + sgn * 12.3, -1.8, zt - 0.6]), np.array([cx, -1.8, zt + 7.2])
        cara(m, [p0, p1, p1 + (0, 0, 0.8), p0 + (0, 0, 0.8)], (0, -1, 0), "piedra_clara")
        if not lejos:
            cara(m, [p0 + (0, 0, 0.8), p1 + (0, 0, 0.8), p1 + (0, 1.8, 0.8), p0 + (0, 1.8, 0.8)], (0, 0, 1),
                 "piedra_clara")
    cara(m, [(cx - 2.6, -1.7, zt + 0.4), (cx + 2.6, -1.7, zt + 0.4), (cx + 2.6, -1.7, zt + 5.6),
             (cx - 2.6, -1.7, zt + 5.6)], (0, -1, 0), "reloj")
    if not lejos:
        for sgn in (-1, 1):
            x = cx + sgn * 16
            m.viga((x, -0.2, 11.0), (x, -5.0, 16.0), 0.25, "hierro")
            p0 = np.array([x, -5.0, 16.0])
            q = [p0, p0 + (0, 2.2, -2.2), p0 + (0, 2.2, -6.2), p0 + (0, 0, -4.0)]
            cara(m, q, (1, 0, 0), "toldo")
            cara(m, q, (-1, 0, 0), "toldo")
    return m


# ==============================================================================================================
# Vegetación y rocas
# ==============================================================================================================


def arbol_frondoso(semilla=0, alto=None, lejos=False, hoja=None):
    rng = _rng(semilla)
    h = alto or float(rng.uniform(17, 26))
    hoja = hoja or ["hoja_verde", "hoja_clara", "hoja_oscura"][int(rng.integers(3))]
    m = Malla()
    t = h * 0.42
    r = h * 0.3
    if lejos:
        m.tronco((0, 0, -1.0), 1.0, 0.7, t + 1.0, 3, "corteza", tapa_abajo=False, tapa_arriba=False)
        return m.esfera((0, 0, t + r * 0.9), r * 1.15, hoja, sub=0, escala=(1, 1, 0.85))
    m.tronco((0, 0, -1.0), 1.15, 0.75, t + 1.0, 5, "corteza", tapa_abajo=False, tapa_arriba=False)
    m.esfera((0, 0, t + r * 0.95), r, hoja, sub=1, jitter=0.12, rng=rng, escala=(1, 1, 0.85))
    for k in range(2):
        a = rng.uniform(0, 2 * math.pi)
        d = r * rng.uniform(0.6, 0.8)
        m.esfera((math.cos(a) * d, math.sin(a) * d, t + r * rng.uniform(0.6, 1.1)), r * rng.uniform(0.55, 0.7), hoja,
                 sub=0, jitter=0.12, rng=rng, escala=(1, 1, 0.85))
    return m


def arbol_flor(semilla=0, alto=None, lejos=False):
    return arbol_frondoso(semilla, alto or float(_rng(semilla).uniform(13, 17)), lejos, hoja="flor_rosa")


def pino(semilla=0, alto=None, lejos=False):
    rng = _rng(semilla)
    h = alto or float(rng.uniform(22, 34))
    m = Malla()
    m.tronco((0, 0, -1.0), 0.9, 0.5, h * 0.35, 4, "corteza", tapa_abajo=False, tapa_arriba=False)
    if lejos:
        return m.tronco((0, 0, h * 0.18), h * 0.3, 0.0, h * 0.82, 5, "hoja_pino", tapa_abajo=True)
    for k in range(3):
        m.tronco((0, 0, h * (0.18 + 0.25 * k)), h * (0.28 - 0.06 * k), 0.0, h * (0.5 - 0.06 * k), 6, "hoja_pino",
                 giro=float(rng.uniform(0, 60)), tapa_abajo=(k == 0))
    return m


def abedul(semilla=0, alto=None, lejos=False):
    rng = _rng(semilla)
    h = alto or float(rng.uniform(18, 26))
    hoja = ["hoja_clara", "hoja_verde"][int(rng.integers(2))]
    m = Malla()
    m.tronco((0, 0, -1.0), 0.55, 0.35, h * 0.75, 4 if lejos else 5, "abedul", tapa_abajo=False, tapa_arriba=False)
    if lejos:
        return m.esfera((0, 0, h * 0.68), h * 0.24, hoja, sub=0, escala=(1, 1, 1.35))
    for k in range(3):
        a = rng.uniform(0, 2 * math.pi)
        m.esfera((math.cos(a) * 1.5, math.sin(a) * 1.5, h * (0.62 + 0.1 * k)), h * 0.17, hoja, sub=0, jitter=0.15,
                 rng=rng, escala=(1, 1, 1.35))
    return m


def arbusto(semilla=0, lejos=False):
    rng = _rng(semilla)
    hoja = ["hoja_verde", "hoja_oscura", "hoja_clara"][int(rng.integers(3))]
    m = Malla()
    if lejos:
        return m.esfera((0, 0, 1.2), 2.6, hoja, sub=0, escala=(1.2, 1.2, 0.7))
    for k in range(2):
        m.esfera((rng.uniform(-1.4, 1.4), rng.uniform(-1.4, 1.4), 1.4), rng.uniform(1.8, 2.4), hoja, sub=0,
                 jitter=0.18, rng=rng, escala=(1, 1, 0.75))
    return m


def roca(semilla=0, tam=None, lejos=False):
    rng = _rng(semilla)
    s = tam or float(rng.uniform(2.5, 7))
    n = 6 if lejos else 11
    d = rng.normal(size=(n, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    pts = d * np.array([1.0, rng.uniform(0.6, 0.9), rng.uniform(0.5, 0.75)]) * s * rng.uniform(0.8, 1.15, (n, 1))
    pts[:, 2] = np.maximum(pts[:, 2], -0.3 * s) + 0.15 * s
    return Malla().convexo(pts, "piedra_media")


def mata_hierba(semilla=0):
    rng = _rng(semilla)
    m = Malla()
    for k in range(3):  # tres hojas, cada una con sus dos caras (Roblox no dibuja el dorso)
        a = rng.uniform(0, 2 * math.pi) + k * 2.1
        h = rng.uniform(1.6, 2.6)
        b = np.array([math.cos(a), math.sin(a), 0]) * 0.25
        tip = np.array([math.cos(a) * rng.uniform(0.6, 1.2), math.sin(a) * rng.uniform(0.6, 1.2), h])
        lat = np.array([-math.sin(a), math.cos(a), 0]) * 0.35
        p = [b - lat, b + lat, tip]
        m.poligono(p, "hierba")
        m.poligono(p[::-1], "hierba")
    return m


def mata_flores(semilla=0):
    m = mata_hierba(semilla)
    rng = _rng(semilla + 1)
    for k in range(3):
        m.tronco((rng.uniform(-0.9, 0.9), rng.uniform(-0.9, 0.9), rng.uniform(1.6, 2.3)), 0.4, 0.0, 0.3, 4, "flores")
    return m


# ==============================================================================================================
# Catálogo: nombre -> (detallada, simple, color de la instancia por defecto, categoría)
#   simple = None        -> de lejos se usa la misma malla (ya es mínima)
#   simple = SIN_LEJOS   -> de lejos no se dibuja (detalle pequeño: contraventanas, matas de hierba...)
# ==============================================================================================================

YESO = "#EFE2C6"
TEJA = "#B4452C"
BLANCO = "#F4F1EA"


def SIN_LEJOS():
    return None


# Piezas que en Roblox se dibujan por las dos caras (MeshPart.DoubleSided): solo las lonas y telas de una capa, que se
# ven desde los dos lados y a las que dar grosor no aporta nada. Todo lo demás es cerrado (o tiene la cara oculta
# pegada a otra pieza). DoubleSided dobla lo que cuesta dibujar esas piezas: usarlo lo menos posible.
DOBLE_CARA = {"Toldo"}

# Piezas con colisión de verdad en Roblox (CanCollide y CanQuery, con PreciseConvexDecomposition en la plantilla): las
# que se pisan y no son terreno. El resto de piezas no choca (cada edificio lleva una caja de colisión aparte).
COLISION = {"Puente"}


PIEZAS = {
    "Pared_Lisa": (lambda: pared_lisa(), lambda: _cuadro(Malla(), "pared_lisa"), YESO, "Paredes"),
    "Pared_Lisa_Baja": (lambda: pared_lisa(True), lambda: _cuadro(Malla(), "pared_lisa_baja"), YESO, "Paredes"),
    "Pared_Ventana": (lambda: pared_ventana(), lambda: pared_ventana_simple(), YESO, "Paredes"),
    "Pared_Ventana_Baja": (lambda: pared_ventana(True), lambda: pared_ventana_simple(True), YESO, "Paredes"),
    "Pared_Puerta": (pared_puerta, lambda: _cuadro(Malla(), "pared_puerta_lejos"), YESO, "Paredes"),
    "Pared_Escaparate": (pared_escaparate, lambda: _cuadro(Malla(), "pared_escaparate_lejos"), YESO, "Paredes"),
    "Entramado_Lisa": (lambda: pared_lisa(mat="entramado_lisa"), lambda: _cuadro(Malla(), "entramado_lisa"), YESO,
                       "Paredes"),
    "Entramado_Ventana": (lambda: pared_ventana(entramado=True), lambda: pared_ventana_simple(entramado=True), YESO,
                          "Paredes"),
    "Esquina": (lambda: esquina(), lambda: esquina(True), YESO, "Paredes"),
    "Cornisa": (lambda: cornisa(), lambda: cornisa(True), "#FFFFFF", "Paredes"),
    "Cornisa_Esquina": (cornisa_esquina, SIN_LEJOS, "#FFFFFF", "Paredes"),
    "Contraventanas": (contraventanas, SIN_LEJOS, "#4F7F5E", "Fachada"),
    "Jardinera": (jardinera, SIN_LEJOS, "#FFFFFF", "Fachada"),
    "Puerta": (puerta, SIN_LEJOS, "#8A6340", "Fachada"),
    "Farolillo": (farolillo, SIN_LEJOS, "#FFFFFF", "Fachada"),
    "Toldo": (toldo, None, "#C2413A", "Fachada"),
    **{f"Cartel_{e.capitalize()}": ((lambda e=e: cartel(e)), SIN_LEJOS, "#FFFFFF", "Fachada")
       for e in ("bolsa", "espada", "gema", "yunque", "pan", "pocion")},
    "Tejado_Tramo_16": (lambda: tejado_tramo(16), lambda: tejado_tramo(16, True), TEJA, "Tejados"),
    "Tejado_Tramo_24": (lambda: tejado_tramo(24), lambda: tejado_tramo(24, True), TEJA, "Tejados"),
    "Tejado_Remate_16": (lambda: tejado_remate(16), lambda: tejado_remate(16, True), TEJA, "Tejados"),
    "Tejado_Remate_24": (lambda: tejado_remate(24), lambda: tejado_remate(24, True), TEJA, "Tejados"),
    "Hastial_16": (lambda: hastial(16), None, YESO, "Tejados"),
    "Hastial_24": (lambda: hastial(24), None, YESO, "Tejados"),
    "Cumbrera_16": (lambda: cumbrera(16), None, TEJA, "Tejados"),
    "Cumbrera_24": (lambda: cumbrera(24), None, TEJA, "Tejados"),
    "Cumbrera_Remate_16": (lambda: cumbrera(16, VUELO), SIN_LEJOS, TEJA, "Tejados"),
    "Cumbrera_Remate_24": (lambda: cumbrera(24, VUELO), SIN_LEJOS, TEJA, "Tejados"),
    "Chimenea": (lambda: chimenea(), lambda: chimenea(lejos=True), "#FFFFFF", "Tejados"),
    "Farola": (farola, lambda: farola(True), "#FFFFFF", "Mobiliario"),
    "Banco": (banco, lambda: banco(True), "#FFFFFF", "Mobiliario"),
    "Barril": (barril, lambda: barril(True), "#FFFFFF", "Mobiliario"),
    "Caja": (caja_madera, None, "#FFFFFF", "Mobiliario"),
    "Maceta": (maceta, None, "#FFFFFF", "Mobiliario"),
    "Valla_Madera": (valla_madera, lambda: valla_madera(True), "#FFFFFF", "Mobiliario"),
    "Valla_Piedra": (valla_piedra, lambda: valla_piedra(True), "#FFFFFF", "Mobiliario"),
    "Puesto": (puesto, lambda: puesto(True), "#C2413A", "Mobiliario"),
    "Tablon_Misiones": (tablon_misiones, lambda: tablon_misiones(True), TEJA, "Mobiliario"),
    "Pozo": (pozo, lambda: pozo(True), TEJA, "Mobiliario"),
    "Carro": (carro, lambda: carro(True), "#FFFFFF", "Mobiliario"),
    "Pajar": (pajar, lambda: pajar(True), "#FFFFFF", "Campo"),
    "Espantapajaros": (espantapajaros, lambda: espantapajaros(True), "#4C6F94", "Campo"),
    "Portal_Ciudad": (portal, lambda: portal(True), "#FFFFFF", "Mobiliario"),
    "Poste_Indicador": (poste_indicador, lambda: poste_indicador(True), "#FFFFFF", "Mobiliario"),
    "Fuente": (fuente, lambda: fuente(True), "#FFFFFF", "Especiales"),
    "Torre_Reloj": (torre_reloj, lambda: torre_reloj(True), BLANCO, "Especiales"),
    "Chapitel": (chapitel, lambda: chapitel(True), TEJA, "Especiales"),
    "Molino_Torre": (molino_torre, lambda: molino_torre(True), BLANCO, "Especiales"),
    "Molino_Caperuza": (molino_caperuza, lambda: molino_caperuza(True), TEJA, "Especiales"),
    "Molino_Aspas": (molino_aspas, lambda: molino_aspas(True), "#FFFFFF", "Especiales"),
    "Portada_Ayuntamiento": (lambda: portada_ayuntamiento(ancho=56.0), lambda: portada_ayuntamiento(True, 56.0),
                             "#3F6FA8", "Especiales"),
    **{f"Frondoso_{c}": ((lambda s=s: arbol_frondoso(s)), (lambda s=s: arbol_frondoso(s, lejos=True)), "#FFFFFF",
                         "Vegetacion") for c, s in zip("abcd", (101, 102, 103, 104))},
    **{f"Pino_{c}": ((lambda s=s: pino(s)), (lambda s=s: pino(s, lejos=True)), "#FFFFFF", "Vegetacion")
       for c, s in zip("abc", (201, 202, 203))},
    **{f"Abedul_{c}": ((lambda s=s: abedul(s)), (lambda s=s: abedul(s, lejos=True)), "#FFFFFF", "Vegetacion")
       for c, s in zip("ab", (301, 302))},
    **{f"Arbusto_{c}": ((lambda s=s: arbusto(s)), (lambda s=s: arbusto(s, lejos=True)), "#FFFFFF", "Vegetacion")
       for c, s in zip("abc", (401, 402, 403))},
    **{f"Roca_{c}": ((lambda s=s: roca(s)), (lambda s=s: roca(s, lejos=True)), "#FFFFFF", "Vegetacion")
       for c, s in zip("abc", (501, 502, 503))},
    **{f"Hierba_{c}": ((lambda s=s: mata_hierba(s)), SIN_LEJOS, "#FFFFFF", "Vegetacion")
       for c, s in zip("ab", (601, 602))},
    **{f"Flores_{c}": ((lambda s=s: mata_flores(s)), SIN_LEJOS, "#FFFFFF", "Vegetacion")
       for c, s in zip("abc", (701, 702, 703))},
    "Arbol_Flor": (lambda: arbol_flor(801), lambda: arbol_flor(801, lejos=True), "#FFFFFF", "Vegetacion"),
    "Arbol_Flor_B": (lambda: arbol_flor(9), lambda: arbol_flor(9, lejos=True), "#FFFFFF", "Vegetacion"),
    "Arbol_Grande": (lambda: arbol_frondoso(33, alto=34.0), lambda: arbol_frondoso(33, alto=34.0, lejos=True),
                     "#FFFFFF", "Vegetacion"),
}


def losa_nombre(nx, ny):
    """Las losas dependen del tamaño del edificio: se registran a demanda."""
    nombre = f"Losa_{nx}x{ny}"
    if nombre not in PIEZAS:
        PIEZAS[nombre] = ((lambda: losa(nx, ny)), None, "#FFFFFF", "Paredes")
    return nombre


def registrar_puente(largo, alto, arcos):
    PIEZAS["Puente"] = ((lambda: puente(largo, 13.0, alto, arcos)), (lambda: puente(largo, 13.0, alto, arcos, True)),
                        "#FFFFFF", "Especiales")
    return "Puente"


def malla(nombre, lejos=False):
    """Malla de una pieza: la detallada o la simple (si no tiene simple propia, la detallada; si de lejos no se
    dibuja, None)."""
    det, sim, _, _ = PIEZAS[nombre]
    if not lejos or sim is None:
        return det()
    return sim()


def color_defecto(nombre):
    return PIEZAS[nombre][2]
