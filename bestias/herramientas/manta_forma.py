"""
Forma orgánica de la Manta Estelar: el campo de distancia de su cuerpo (planta, grosor, curvatura de las alas,
nervaduras, cresta dorsal, ojos, espiráculos, boca y cola) y los cortes del rig.

Coordenadas de modelado (studs): X = derecha de la bestia, Y = delante, Z = arriba. El centro del lomo está en el
origen. (El giro de importación se aplica solo al exportar.)
"""

import math

import numpy as np

import campos as C

# --------------------------------------------------------------------------------------------------------------
# Medidas (todo lo ajustable, arriba)
# --------------------------------------------------------------------------------------------------------------

# Planta (mitad derecha, de la punta de la cabeza a la parte trasera, en el sentido de las agujas del reloj).
CONTORNO_DER = [
    (0.0, 6.20), (0.80, 6.15), (1.35, 5.95), (1.62, 5.55), (1.72, 4.95), (1.80, 4.30), (2.15, 3.80),
    (3.50, 3.12), (5.00, 2.10), (6.50, 0.75), (7.80, -0.72), (8.55, -1.85), (9.00, -2.62),
    (8.62, -2.80), (7.60, -2.86), (6.00, -3.32), (4.60, -4.10), (3.40, -5.00), (2.50, -5.70),
    (2.00, -6.18), (1.40, -6.52), (0.70, -6.72), (0.0, -6.78),
]
# Borde de ataque y de fuga (para la cuerda del perfil alar).
BORDE_ATAQUE = [(2.15, 3.80), (3.50, 3.12), (5.00, 2.10), (6.50, 0.75), (7.80, -0.72), (8.55, -1.85),
                (9.00, -2.62)]
BORDE_FUGA = [(2.00, -6.18), (2.50, -5.70), (3.40, -5.00), (4.60, -4.10), (6.00, -3.32), (7.60, -2.86),
              (8.62, -2.80), (9.00, -2.62)]

GROSOR_CUERPO = 1.5      # alto del disco en el centro
ARRIBA_CUERPO = 0.86     # semigrosor superior en el centro (el vientre es más plano)
ABAJO_CUERPO = 0.52
RADIO_BORDE = 0.075      # semigrosor mínimo del borde (0,15 studs de grosor visible)
CURVA_PUNTAS = 0.62      # cuánto suben las puntas de las alas

# Nervaduras (5 por ala): raíz (y en x=2.3), final (x, y) y desvío del control (curvatura hacia atrás).
NERVADURAS = [
    (2.95, (8.55, -2.15), -0.35),
    (1.55, (7.70, -2.62), -0.45),
    (0.10, (6.35, -3.05), -0.45),
    (-1.55, (4.95, -3.80), -0.35),
    (-3.25, (3.55, -4.75), -0.25),
]
ALTO_NERVADURA = 0.10

# Ojos (1 stud de diámetro) a los lados de la cabeza.
OJO_CENTRO = (1.74, 4.86, 0.16)
OJO_RADIO = 0.5
# Espiráculos: (x, y, giro en grados).
ESPIRACULOS = [(1.25, 3.02, 18), (1.62, 2.40, 26)]

# Boca subterminal: la hendidura va de la punta de la cabeza (y, z) a la bisagra de la mandíbula, por debajo.
BOCA_PUNTA = (6.30, -0.08)
BOCA_BISAGRA = (4.95, -0.30)
BOCA_ANCHO = 1.12        # |x| de la mandíbula
BOCA_CENTRO = (0.0, 5.62, -0.19)
BOCA_RADIOS = (0.84, 0.55, 0.12)

# Cola: puntos (y, z) y radios.
COLA = [(-5.70, 0.02, 0.33), (-6.55, 0.0, 0.27), (-7.5, -0.04, 0.22), (-8.5, -0.06, 0.18), (-9.5, -0.05, 0.145),
        (-10.5, -0.02, 0.11), (-11.3, 0.02, 0.085), (-11.75, 0.05, 0.075)]
COLA_ACHATADO = 0.8

# Cortes del rig.
CORTE_ALA = 2.9          # |x| cuerpo / base del ala
CORTE_PUNTA = 5.8        # |x| base / punta del ala
CORTE_CABEZA = 4.0       # y cuerpo / cabeza
CORTE_COLA = -6.92       # y cuerpo / cola
CORTE_COLA_PUNTA = -9.9  # y cola / punta de la cola
G = 0.01                 # media separación (0,02 entre piezas)


# --------------------------------------------------------------------------------------------------------------
# Planta 2D
# --------------------------------------------------------------------------------------------------------------


def _contorno_completo():
    der = CONTORNO_DER
    izq = [(-x, y) for x, y in reversed(der[1:-1])]
    return C.catmull_rom(der + izq, por_tramo=14, cerrada=True)


CONTORNO = _contorno_completo()


def _muescas():
    """Muescas irregulares en el borde de fuga (desgaste). Distintas en cada ala: es una historia, no un espejo."""
    rnd = np.random.default_rng(7)
    fuga = C.remuestrear(np.array(BORDE_FUGA), 0.05)
    res = []
    for lado, cuantas in ((1, 5), (-1, 4)):
        ts = np.sort(rnd.uniform(0.12, 0.92, cuantas))
        for t in ts:
            i = int(t * (len(fuga) - 1))
            p = fuga[i]
            q = fuga[min(i + 1, len(fuga) - 1)] - fuga[max(i - 1, 0)]
            n = np.array([q[1], -q[0]])
            n = n / (np.linalg.norm(n) + 1e-9)
            if n[1] > 0:
                n = -n
            r = rnd.uniform(0.07, 0.17)
            c = p + n * r * rnd.uniform(0.25, 0.55)
            res.append((lado * c[0], c[1], r))
    # Un mordisco mayor y viejo en la punta izquierda (cicatriz de combate).
    res.append((-8.15, -2.92, 0.26))
    return res


MUESCAS = _muescas()


def _nervaduras_polilineas():
    lineas = []
    for yr, fin, desvio in NERVADURAS:
        a = np.array([2.3, yr])
        b = np.array(fin)
        m = (a + b) / 2 + np.array([0.0, desvio])
        ts = np.linspace(0, 1, 18)[:, None]
        lineas.append((1 - ts) ** 2 * a + 2 * (1 - ts) * ts * m + ts ** 2 * b)
    return lineas


NERVADURAS_POLI = _nervaduras_polilineas()


def _interp_borde(borde, ax):
    b = np.array(borde)
    orden = np.argsort(b[:, 0])
    return np.interp(ax, b[orden, 0], b[orden, 1])


def _suavizar(campo2d, X, Y, sigma_studs=0.45):
    if campo2d.ndim != 2 or campo2d.shape[0] < 4 or campo2d.shape[1] < 4:
        return campo2d
    from scipy.ndimage import gaussian_filter

    px = abs(X[1, 0] - X[0, 0]) or 1.0
    py = abs(Y[0, 1] - Y[0, 0]) or 1.0
    return gaussian_filter(campo2d, (sigma_studs / px, sigma_studs / py), mode="nearest")


def campos_2d(X, Y):
    """Devuelve dict con d2 (distancia con signo a la planta), m (curvatura), arriba, abajo, radio."""
    ax = np.abs(X)
    d2 = C.sdf_poligono(X, Y, CONTORNO)
    for (mx, my, r) in MUESCAS:
        dc = np.sqrt((X - mx) ** 2 + (Y - my) ** 2) - r
        d2 = np.maximum(d2, -dc)
    dentro = -d2

    yle = _interp_borde(BORDE_ATAQUE, ax)
    yte = _interp_borde(BORDE_FUGA, ax)
    c = np.clip((yle - Y) / np.maximum(yle - yte, 0.3), 0.0, 1.0)
    perfil = (0.2969 * np.sqrt(c) - 0.126 * c - 0.3516 * c ** 2 + 0.2843 * c ** 3 - 0.1036 * c ** 4) / 0.1

    por_y = 1.0 - 0.30 * C.sstep(2.0, 6.4, Y) - 0.62 * C.sstep(-2.5, -6.8, Y)
    B = np.exp(-(ax / 2.15) ** 2) * por_y
    arriba_cuerpo = ARRIBA_CUERPO * B
    abajo_cuerpo = ABAJO_CUERPO * B
    caida = 1.0 - 0.72 * C.sstep(2.4, 9.0, ax)
    arriba_ala = 0.30 * caida * perfil
    abajo_ala = 0.16 * caida * perfil
    arriba = C.smax(arriba_cuerpo, arriba_ala, 0.35)
    abajo = C.smax(abajo_cuerpo, abajo_ala, 0.30)
    # Mentón: la parte baja de la cabeza es más llena (aloja la boca y la mandíbula).
    abajo = abajo + 0.22 * np.exp(-(X / 1.3) ** 2) * C.sstep(3.4, 5.0, Y)

    # Nervaduras: relieve arriba (0,1) y la mitad abajo, que se afinan hacia la punta.
    d_n = None
    for poli in NERVADURAS_POLI:
        d = C.distancia_segmentos(ax, Y, poli, cerrado=False)
        d_n = d if d_n is None else np.minimum(d_n, d)
    ancho = 0.20 - 0.09 * C.sstep(2.4, 9.0, ax)
    alto = ALTO_NERVADURA * (1 - 0.45 * C.sstep(2.4, 9.0, ax)) * (1 - np.exp(-np.maximum(dentro, 0) / 0.22))
    alto *= C.sstep(2.1, 2.9, ax)
    nerv = alto * np.exp(-(d_n / ancho) ** 2)
    arriba = arriba + nerv
    abajo = abajo + 0.45 * nerv

    # Cresta dorsal suave bajo la fila de escamas grandes.
    arriba = arriba + 0.06 * np.exp(-(X / 0.32) ** 2) * (1 - C.sstep(5.0, 6.1, Y))

    # Radio del borde: más grueso en el borde de ataque y en la cabeza.
    radio = RADIO_BORDE + 0.04 * (1 - C.sstep(0.0, 0.35, c)) * C.sstep(2.0, 3.0, ax) + 0.05 * B
    rampa = 0.22 + 0.9 * B
    # La distancia interior tiene aristas en el eje medial (se verían como un tejado): para el grosor se usa una
    # versión suavizada lejos del borde, y la exacta cerca de él (para que el borde no cambie).
    dentro_suave = _suavizar(dentro, X, Y)
    w = C.sstep(0.08, 0.6, dentro)
    dentro_g = dentro * (1 - w) + np.minimum(dentro_suave, dentro + 0.4) * w
    f = 1.0 - np.exp(-np.maximum(dentro_g - radio, 0.0) / rampa)
    extra_arriba = np.maximum(arriba - radio, 0.0) * f
    extra_abajo = np.maximum(abajo - radio, 0.0) * f

    m = CURVA_PUNTAS * C.sstep(4.0, 9.2, ax) ** 1.6 - 0.12 * C.sstep(4.3, 6.2, Y) * np.exp(-(X / 1.8) ** 2)
    return dict(d2=d2, m=m, arriba=extra_arriba, abajo=extra_abajo, radio=radio, c=c, B=B)


def superficie(x, y, lado=1):
    """Altura de la piel arriba (lado=1) o abajo (lado=-1) en (x, y), sin los detalles 3D."""
    X = np.atleast_1d(np.asarray(x, dtype=np.float64))
    Y = np.atleast_1d(np.asarray(y, dtype=np.float64))
    k = campos_2d(X, Y)
    if lado > 0:
        z = k["m"] + k["arriba"] + k["radio"]
    else:
        z = k["m"] - k["abajo"] - k["radio"]
    return z if z.size > 1 else float(z[0])


# --------------------------------------------------------------------------------------------------------------
# Campo 3D
# --------------------------------------------------------------------------------------------------------------


class Campo:
    """Campo 3D del cuerpo entero. Guarda en caché los campos 2D de la última rejilla XY."""

    def __init__(self):
        self._clave = None
        self._k = None
        self.espiraculos = []
        for (sx, sy, giro) in ESPIRACULOS:
            for lado in (1, -1):
                x = sx * lado
                z = superficie(x, sy)
                self.espiraculos.append((x, sy, z, math.radians(giro) * -lado))
        self.ojo_z = {}

    def _2d(self, xs, ys):
        clave = (xs[0], xs[-1], len(xs), ys[0], ys[-1], len(ys))
        if clave != self._clave:
            X, Y = np.meshgrid(xs, ys, indexing="ij")
            self._k = campos_2d(X, Y)
            self._XY = (X, Y)
            self._clave = clave
        return self._k

    def disco(self, xs, ys, zs):
        k = self._2d(xs, ys)
        Z = zs[None, None, :]
        m = k["m"][..., None]
        e = np.where(Z > m, Z - m - k["arriba"][..., None], m - Z - k["abajo"][..., None])
        d2s = k["d2"][..., None] + k["radio"][..., None]
        r = k["radio"][..., None]
        f = np.sqrt(np.maximum(d2s, 0) ** 2 + np.maximum(e, 0) ** 2) + np.minimum(np.maximum(d2s, e), 0) - r
        return f

    def __call__(self, xs, ys, zs):
        f = self.disco(xs, ys, zs)
        X = xs[:, None, None]
        Y = ys[None, :, None]
        Z = zs[None, None, :]
        f = self.detalles(f, X, Y, Z)
        return f.astype(np.float32)

    def detalles(self, f, X, Y, Z):
        # --- Cola (se funde con la parte trasera del disco) ---
        pts = [(0.0, y, z) for (y, z, _) in COLA]
        rad = [r for (_, _, r) in COLA]
        if Y.min() < -5.0:
            cola = C.tubo(X, Y, Z, pts, rad, escala_z=COLA_ACHATADO, k=0.08)
            f = C.smin(f, cola, 0.35)

        # --- Cabeza: bultos de los ojos, crestas y boca ---
        if Y.max() > 3.8:
            ox, oy, oz = OJO_CENTRO
            for lado in (1, -1):
                # Montículo de piel: el ojo asoma por su cima (párpado), no por un lateral (sin efecto "tubo").
                bulto = C.elipsoide(X, Y, Z, (lado * (ox - 0.30), oy, oz - 0.04), (0.40, 0.84, 0.66))
                f = C.smin(f, bulto, 0.3)
                rot = C.matriz_giro((0, 0, 1), lado * 0.35)
                cresta = C.elipsoide(X, Y, Z, (lado * 1.62, oy + 0.02, oz + 0.40), (0.30, 0.66, 0.17), rot=rot)
                f = C.smin(f, cresta, 0.16)
                # Cuenca del ojo: el globo (pieza aparte) se asienta con 0,02 de holgura.
                cuenca = np.sqrt((X - lado * ox) ** 2 + (Y - oy) ** 2 + (Z - oz) ** 2) - (OJO_RADIO + 0.02)
                f = C.smax(f, -cuenca, 0.07)
            # Boca: cavidad entre el paladar y la mandíbula, que se abre por la hendidura delantera.
            boca = C.elipsoide(X, Y, Z, BOCA_CENTRO, BOCA_RADIOS)
            f = C.smax(f, -boca, 0.04)

        # --- Espiráculos: hendidura ovalada con borde elevado y pliegues de branquias dentro ---
        if Y.max() > 1.5 and Y.min() < 3.6:
            for (sx, sy, sz, giro) in self.espiraculos:
                ca, sa = math.cos(giro), math.sin(giro)
                anillo = [(sx + ca * 0.19 * math.cos(t) - sa * 0.36 * math.sin(t),
                           sy + sa * 0.19 * math.cos(t) + ca * 0.36 * math.sin(t), sz - 0.005)
                          for t in np.linspace(0, math.tau, 17)]
                borde = C.tubo(X, Y, Z, anillo, [0.05] * 17)
                f = C.smin(f, borde, 0.06)
                rot = C.matriz_giro((0, 0, 1), -giro)
                hueco = C.elipsoide(X, Y, Z, (sx, sy, sz + 0.03), (0.12, 0.29, 0.17), rot=rot)
                f = C.smax(f, -hueco, 0.04)
                for dy in (-0.15, -0.05, 0.05, 0.15):
                    cx, cy = sx - sa * dy, sy + ca * dy
                    pl = C.capsula(X, Y, Z, (cx - ca * 0.08, cy - sa * 0.08, sz - 0.07),
                                   (cx + ca * 0.08, cy + sa * 0.08, sz - 0.07), 0.028)
                    f = C.smin(f, pl, 0.02)
        return f



def region_mandibula(X, Y, Z):
    """Negativo dentro de la zona de la mandíbula: por debajo de la hendidura de la boca, |x| < BOCA_ANCHO y por
    delante de la bisagra."""
    (yp, zp), (yb, zb) = BOCA_PUNTA, BOCA_BISAGRA
    dy, dz = yp - yb, zp - zb
    L = math.hypot(dy, dz)
    ny, nz = -dz / L, dy / L  # normal "hacia arriba" de la línea de la boca
    plano = (Y - yb) * ny + (Z - zb) * nz
    # En planta, la mandíbula es una U (elipse) para que la costura de abajo sea curva y limpia.
    planta = (np.sqrt((X / BOCA_ANCHO) ** 2 + ((Y - 6.15) / (6.15 - yb)) ** 2) - 1.0) * BOCA_ANCHO * 0.8
    return np.maximum(plano, planta)


def lengua(X, Y, Z):
    """Paleta sensorial sobre el suelo de la boca."""
    suelo = BOCA_CENTRO[2] - BOCA_RADIOS[2]
    return C.elipsoide(X, Y, Z, (0.0, 5.52, suelo + 0.01), (0.30, 0.36, 0.055))


# --------------------------------------------------------------------------------------------------------------
# Piezas del rig: caja de evaluación, cortes y vóxel
# --------------------------------------------------------------------------------------------------------------


def cortes(nombre):
    """Lista de semiespacios (punto, normal hacia fuera) que recortan la pieza."""
    a, p, ch, co, cp = CORTE_ALA, CORTE_PUNTA, CORTE_CABEZA, CORTE_COLA, CORTE_COLA_PUNTA
    tabla = {
        "Cuerpo_Central": [((a - G, 0, 0), (1, 0, 0)), ((-a + G, 0, 0), (-1, 0, 0)),
                           ((0, ch - G, 0), (0, 1, 0)), ((0, co + G, 0), (0, -1, 0))],
        "Cabeza": [((0, ch + G, 0), (0, -1, 0))],
        "Mandibula": [],
        "Ala_Derecha_Base": [((a + G, 0, 0), (-1, 0, 0)), ((p - G, 0, 0), (1, 0, 0))],
        "Ala_Derecha_Punta": [((p + G, 0, 0), (-1, 0, 0))],
        "Ala_Izquierda_Base": [((-a - G, 0, 0), (1, 0, 0)), ((-p + G, 0, 0), (-1, 0, 0))],
        "Ala_Izquierda_Punta": [((-p - G, 0, 0), (1, 0, 0))],
        "Cola": [((0, co - G, 0), (0, 1, 0)), ((0, cp + G, 0), (0, -1, 0))],
        "Cola_Punta": [((0, cp - G, 0), (0, 1, 0))],
    }
    return tabla[nombre]


CAJAS = {
    "Cuerpo_Central": ((-2.95, -7.0, -1.0), (2.95, 4.05, 1.35), 0.022),
    "Cabeza": ((-2.75, 3.95, -1.0), (2.75, 6.45, 1.05), 0.016),
    "Mandibula": ((-1.25, 4.75, -0.85), (1.25, 6.45, 0.05), 0.012),
    "Ala_Derecha_Base": ((2.85, -4.55, -0.55), (5.85, 3.65, 0.85), 0.02),
    "Ala_Izquierda_Base": ((-5.85, -4.55, -0.55), (-2.85, 3.65, 0.85), 0.02),
    "Ala_Derecha_Punta": ((5.75, -3.30, -0.35), (9.25, 1.70, 1.10), 0.018),
    "Ala_Izquierda_Punta": ((-9.25, -3.30, -0.35), (-5.75, 1.70, 1.10), 0.018),
    "Cola": ((-0.6, -9.95, -0.6), (0.6, -6.85, 0.6), 0.012),
    "Cola_Punta": ((-0.4, -11.95, -0.4), (0.4, -9.85, 0.4), 0.010),
}


def campo_pieza(campo, nombre):
    planos = cortes(nombre)

    def f(xs, ys, zs):
        v = campo(xs, ys, zs).astype(np.float64)
        X = xs[:, None, None]
        Y = ys[None, :, None]
        Z = zs[None, None, :]
        for punto, normal in planos:
            v = C.smax(v, C.semiespacio(X, Y, Z, punto, normal), 0.012)
        if nombre == "Cabeza":
            v = C.smax(v, G - region_mandibula(X, Y, Z), 0.02)
        elif nombre == "Mandibula":
            v = C.smax(v, region_mandibula(X, Y, Z) + G, 0.02)
            v = C.smin(v, lengua(X, Y, Z), 0.05)
        return v.astype(np.float32)

    return f
