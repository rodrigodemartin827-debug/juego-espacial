"""
Forma orgánica del Dragón del Vacío: primitivas (elipsoides y cápsulas) unidas con mezcla suave, repartidas entre
las 17 piezas del rig. Cada pieza es la parte de la superficie total que está más cerca de sus primitivas que de las
de las demás (con 0,02 de separación): así las uniones (cuello-torso, muslo-cadera, cola) siguen la anatomía.

Coordenadas de modelado (studs): X = derecha, Y = delante, Z = arriba. Los pies apoyan en z = 0.
Pose de reposo: alas plegadas a los lados, cuello en S, cola recta.
"""

import math

import numpy as np

import campos as C

G = 0.01  # media separación entre piezas


def esp(p):
    """Espejo en X."""
    return (-p[0], p[1], p[2])


# --------------------------------------------------------------------------------------------------------------
# Esqueleto (puntos de articulación) — todo lo ajustable aquí
# --------------------------------------------------------------------------------------------------------------

CUELLO = [(0, 1.95, 3.45), (0, 2.80, 4.35), (0, 3.08, 5.22), (0, 3.55, 5.95), (0, 4.25, 6.28)]
CUELLO_R = [0.86, 0.70, 0.60, 0.53, 0.50]
DZ = 0.44  # cabeza levantada (cuello erguido)
ARTIC_CABEZA = (0.0, 4.30, 5.88 + DZ)
BISAGRA = (0.0, 4.72, 5.58 + DZ)

HOMBRO = (1.30, 1.70, 3.40)
CODO = (1.88, 0.70, 4.08)
MUNECA = (2.00, 2.55, 3.60)
DEDOS = [(2.18, -0.20, 3.95), (2.30, -0.35, 2.90), (2.08, 0.10, 2.02)]

CADERA = (1.00, -2.20, 2.35)
RODILLA = (1.20, -1.22, 1.25)
TOBILLO = (1.24, -2.42, 0.56)
PIE = (1.24, -1.95, 0.17)

COLA = [(0, -3.30, 2.95), (0, -5.00, 2.78), (0, -6.65, 2.58), (0, -8.10, 2.40)]
COLA_R = [0.52, 0.42, 0.31, 0.23]
MAZA = (0.0, -8.15, 2.40)

OJO = (0.47, 5.12, 6.12 + DZ)
OJO_R = 0.30
BOCA = ((0.0, 5.80, 5.66 + DZ), (0.27, 1.05, 0.09))


# --------------------------------------------------------------------------------------------------------------
# Primitivas por pieza: (función de campo, k de mezcla con el resto)
# --------------------------------------------------------------------------------------------------------------


def primitivas():
    P = {}

    def el(c, r, rot=None, dz=0.0):
        c = (c[0], c[1], c[2] + dz)
        return lambda X, Y, Z: C.elipsoide(X, Y, Z, c, r, rot)

    def cap(a, b, ra, rb=None, dz=0.0):
        a = (a[0], a[1], a[2] + dz)
        b = (b[0], b[1], b[2] + dz)
        return lambda X, Y, Z: C.capsula(X, Y, Z, a, b, ra, rb)

    P["Torso"] = [
        (el((0, 0.95, 2.78), (1.45, 1.85, 1.18)), 0.6),     # pecho ancho (3 studs)
        (el((0, -1.45, 2.66), (1.08, 2.05, 0.98)), 0.6),    # vientre y cadera, más estrecho
        (el((1.05, 1.62, 3.22), (0.62, 0.78, 0.55)), 0.4),  # musculatura del hombro del ala
        (el((-1.05, 1.62, 3.22), (0.62, 0.78, 0.55)), 0.4),
        (el((0.82, -2.25, 2.55), (0.62, 0.85, 0.7)), 0.4),  # caderas
        (el((-0.82, -2.25, 2.55), (0.62, 0.85, 0.7)), 0.4),
        (cap((0, 1.9, 3.65), (0, -3.1, 3.28), 0.36, 0.3), 0.45),  # columna
        (el((0, 2.05, 2.55), (0.95, 0.8, 0.9)), 0.5),       # quilla del pecho
    ]
    P["Cuello"] = [(cap(CUELLO[i], CUELLO[i + 1], CUELLO_R[i], CUELLO_R[i + 1]), 0.25) for i in range(4)]
    P["Cuello"].append((cap((0, 2.95, 3.95), (0, 3.38, 5.05), 0.30, 0.22), 0.35))   # papada
    # Cráneo en cuña (tiburón + pterosaurio): ancho atrás, hocico que se afila hasta una punta.
    P["Cabeza"] = [
        (el((0, 4.85, 6.02), (0.62, 0.78, 0.48), dz=DZ), 0.3),                          # cráneo
        (cap((0, 5.25, 5.92), (0, 6.95, 5.80), 0.40, 0.11, dz=DZ), 0.3),               # hocico afilado
        (el((0, 5.6, 5.86), (0.42, 0.9, 0.2), dz=DZ), 0.25),                            # maxilar ancho (labio)
        (el((0.46, 4.85, 5.80), (0.30, 0.55, 0.34), dz=DZ), 0.25),                     # mejillas (músculo de la mordida)
        (el((-0.46, 4.85, 5.80), (0.30, 0.55, 0.34), dz=DZ), 0.25),
        (el((0.36, 5.12, 6.36), (0.24, 0.58, 0.1), C.matriz_giro((0, 1, 0), -0.25), dz=DZ), 0.14),  # visera sobre el ojo
        (el((-0.36, 5.12, 6.36), (0.24, 0.58, 0.1), C.matriz_giro((0, 1, 0), 0.25), dz=DZ), 0.14),
        (cap((0, 4.95, 6.35), (0, 4.25, 6.55), 0.16, 0.1, dz=DZ), 0.2),                # cresta del cogote
    ]
    # Mandíbula profunda y fuerte, que también se afila.
    P["Mandibula"] = [
        (cap((0, 4.85, 5.52), (0, 6.75, 5.62), 0.36, 0.1, dz=DZ), 0.25),
        (el((0, 4.95, 5.5), (0.48, 0.55, 0.27), dz=DZ), 0.25),
        (el((0, 5.6, 5.42), (0.3, 0.6, 0.16), dz=DZ), 0.2),                              # barbilla
    ]
    for lado, nom in ((1, "Der"), (-1, "Izq")):
        s = (lambda p: p) if lado > 0 else esp
        H, E, W = s(HOMBRO), s(CODO), s(MUNECA)
        P[f"Ala_{nom}_Hombro"] = [(cap(H, E, 0.32, 0.22), 0.18), (el(E, (0.24, 0.24, 0.24)), 0.1)]
        P[f"Ala_{nom}_Antebrazo"] = [(cap(E, W, 0.19, 0.15), 0.12), (el(W, (0.2, 0.2, 0.2)), 0.08)]
        mano = []
        for d in DEDOS:
            D = s(d)
            m = tuple((np.array(W) * 0.55 + np.array(D) * 0.45).tolist())
            mano.append((cap(W, m, 0.14, 0.1), 0.06))
            mano.append((cap(m, D, 0.1, 0.06), 0.06))
            mano.append((el(m, (0.13, 0.13, 0.13)), 0.04))  # nudillo
        P[f"Ala_{nom}_Mano"] = mano
        Hc, K, A, F = s(CADERA), s(RODILLA), s(TOBILLO), s(PIE)
        P[f"Pata_{nom}_Muslo"] = [(cap(Hc, K, 0.78, 0.48), 0.3),
                                  (el(((Hc[0] + K[0]) / 2 + 0.06 * lado, (Hc[1] + K[1]) / 2 + 0.12, (Hc[2] + K[2]) / 2 + 0.1),
                                      (0.7, 0.8, 0.72)), 0.3)]
        dedos = [(F[0] - 0.30 * lado, F[1] + 0.82, 0.11), (F[0] + 0.0, F[1] + 0.98, 0.11),
                 (F[0] + 0.30 * lado, F[1] + 0.80, 0.11)]
        tib = [(cap(K, A, 0.46, 0.25), 0.2), (cap(A, F, 0.24, 0.2), 0.12),
               (cap((K[0], K[1] - 0.32, K[2] - 0.1), (A[0], A[1] - 0.2, A[2] + 0.12), 0.11, 0.07), 0.12),  # tendón
               (cap(F, (F[0], F[1] - 0.45, 0.13), 0.12, 0.08), 0.08)]  # espolón
        for t in dedos:
            tib.append((cap(F, t, 0.17, 0.1), 0.08))
        P[f"Pata_{nom}_Tibia"] = tib
    P["Cola_Base"] = [(cap(COLA[0], COLA[1], COLA_R[0], COLA_R[1]), 0.3)]
    P["Cola_Media"] = [(cap(COLA[1], COLA[2], COLA_R[1], COLA_R[2]), 0.2)]
    maza = [(cap(COLA[2], COLA[3], COLA_R[2], COLA_R[3]), 0.15),
            (el(MAZA, (0.6, 0.6, 0.46)), 0.35)]
    rnd = np.random.default_rng(21)
    for i in range(13):  # nudos óseos irregulares que sobresalen (garrote natural)
        d = rnd.normal(size=3)
        d[1] *= 0.6
        d /= np.linalg.norm(d)
        c = (MAZA[0] + d[0] * 0.56, MAZA[1] + d[1] * 0.5, MAZA[2] + d[2] * 0.42)
        r = rnd.uniform(0.13, 0.22)
        maza.append((el(c, (r, r * rnd.uniform(0.8, 1.3), r * 0.85)), 0.06))
    P["Cola_Punta"] = maza
    return P


PRIM = primitivas()
PIEZAS = list(PRIM.keys())


def _d_pieza(nombre, X, Y, Z):
    d = None
    for f, _ in PRIM[nombre]:
        v = f(X, Y, Z)
        d = v if d is None else np.minimum(d, v)
    return d


def campo_total(X, Y, Z):
    f = None
    for nombre in PIEZAS:
        for g, k in PRIM[nombre]:
            v = g(X, Y, Z)
            f = v if f is None else C.smin(f, v, k)
    # Cavidad de la boca, cuencas de los ojos, fosas nasales y oídos.
    f = C.smax(f, -C.elipsoide(X, Y, Z, *BOCA), 0.03)
    for lado in (1, -1):
        ojo = np.sqrt((X - lado * OJO[0]) ** 2 + (Y - OJO[1]) ** 2 + (Z - OJO[2]) ** 2) - (OJO_R + 0.02)
        f = C.smax(f, -ojo, 0.05)
        nariz = C.elipsoide(X, Y, Z, (lado * 0.12, 6.72, 5.95 + DZ), (0.05, 0.13, 0.04), C.matriz_giro((0, 0, 1), lado * 0.4))
        f = C.smax(f, -nariz, 0.02)
        oido = C.elipsoide(X, Y, Z, (lado * 0.58, 4.62, 6.1 + DZ), (0.04, 0.16, 0.09))
        f = C.smax(f, -oido, 0.02)
    return f


def campo_pieza(nombre):
    otros = [n for n in PIEZAS if n != nombre]

    def campo(xs, ys, zs):
        X = xs[:, None, None]
        Y = ys[None, :, None]
        Z = zs[None, None, :]
        f = campo_total(X, Y, Z)
        propio = _d_pieza(nombre, X, Y, Z)
        ajeno = None
        for n in otros:
            d = _d_pieza(n, X, Y, Z)
            ajeno = d if ajeno is None else np.minimum(ajeno, d)
        f = C.smax(f, propio - ajeno + 2 * G, 0.02)
        return f.astype(np.float32)

    return campo


def caja(nombre, margen=0.35):
    """Caja de evaluación de la pieza a partir de sus primitivas (muestreo grueso)."""
    xs = np.linspace(-3.2, 3.2, 65)
    ys = np.linspace(-9.2, 7.4, 167)
    zs = np.linspace(-0.2, 8.0, 83)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    d = _d_pieza(nombre, X, Y, Z)
    idx = np.argwhere(d < 0.15)
    mn = np.array([xs[idx[:, 0].min()], ys[idx[:, 1].min()], zs[idx[:, 2].min()]]) - margen
    mx = np.array([xs[idx[:, 0].max()], ys[idx[:, 1].max()], zs[idx[:, 2].max()]]) + margen
    return mn, mx


VOXEL = {"Torso": 0.03, "Cuello": 0.024, "Cabeza": 0.016, "Mandibula": 0.014, "Cola_Base": 0.022,
         "Cola_Media": 0.02, "Cola_Punta": 0.016}


def voxel(nombre):
    if nombre in VOXEL:
        return VOXEL[nombre]
    if "Mano" in nombre or "Antebrazo" in nombre:
        return 0.014
    if "Hombro" in nombre:
        return 0.018
    if "Tibia" in nombre:
        return 0.018
    return 0.024
