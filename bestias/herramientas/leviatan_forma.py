"""
Forma del Leviatán Estelar: ballena cósmica acorazada (cachalote + fortaleza). Primitivas con mezcla suave
repartidas entre las piezas del rig. La aleta caudal es HORIZONTAL (como una ballena), nunca vertical.

Coordenadas (studs): X = derecha, Y = delante, Z = arriba. El vientre queda en z ≈ 2.
"""

import math

import numpy as np

import campos as C

G = 0.01
ZC = 7.5                                    # eje del cuerpo
CUELLO = (0.0, 9.0, ZC + 0.6)               # unión cabeza-cuerpo
BISAGRA = (0.0, 9.6, 4.5)                   # mandíbula inferior
COLA = [(0, -11.8, ZC + 0.4), (0, -15.6, ZC + 0.9), (0, -18.4, ZC + 1.2), (0, -20.2, ZC + 1.3)]
HOMBRO = (5.6, 4.0, 5.2)                    # aleta pectoral derecha (la izquierda es espejo)
ALETA_DORSAL = (0.0, -3.5, 12.2)
OJO = (3.85, 13.4, 8.6)
APERTURA = (5.9, -1.0, 7.0)                 # centro de la apertura lateral derecha (3 × 5)


def esp(p):
    return (-p[0], p[1], p[2])


def caja_redondeada(X, Y, Z, c, medio, r):
    q = [np.abs(X - c[0]) - medio[0] + r, np.abs(Y - c[1]) - medio[1] + r, np.abs(Z - c[2]) - medio[2] + r]
    fuera = np.sqrt(np.maximum(q[0], 0) ** 2 + np.maximum(q[1], 0) ** 2 + np.maximum(q[2], 0) ** 2)
    dentro = np.minimum(np.maximum(q[0], np.maximum(q[1], q[2])), 0)
    return fuera + dentro - r


def primitivas():
    P = {}

    def el(c, r, rot=None):
        return lambda X, Y, Z: C.elipsoide(X, Y, Z, c, r, rot)

    def cap(a, b, ra, rb=None):
        return lambda X, Y, Z: C.capsula(X, Y, Z, a, b, ra, rb)

    P["Cuerpo_Principal"] = [
        (el((0, 0.5, ZC), (7.0, 11.5, 5.0)), 1.2),
        (el((0, -6.5, ZC + 0.3), (5.6, 7.0, 4.3)), 1.5),
        (el((0, 5.5, ZC - 0.6), (6.4, 5.0, 4.8)), 1.2),
        (el((0, 9.2, ZC + 0.4), (5.0, 3.2, 4.4)), 1.4),     # transición sin cuello hacia la cabeza
    ]
    # Cabeza de cachalote: bloque frontal (melón) con aristas muy redondeadas; algo más estrecha que el cuerpo.
    P["Cabeza"] = [
        (lambda X, Y, Z: caja_redondeada(X, Y, Z, (0, 14.6, ZC + 1.2), (3.9, 5.6, 3.4), 2.2), 1.2),
        (el((0, 18.6, ZC + 1.6), (3.5, 1.6, 3.0)), 0.8),       # melón acústico (frente cuadrado y liso)
        (el((0, 12.5, ZC + 3.9), (2.8, 3.5, 0.9)), 0.8),       # placa craneal
    ]
    P["Mandibula_Inf"] = [
        (cap((0, 10.0, 4.65), (0, 18.6, 4.35), 1.1, 0.75), 0.4),
        (el((0, 10.4, 4.9), (1.9, 1.6, 0.9)), 0.5),
    ]
    for lado, nom in ((1, "Der"), (-1, "Izq")):
        s = (lambda p: p) if lado > 0 else esp
        h = s(HOMBRO)
        pts = [h, s((8.6, 2.6, 4.3)), s((11.0, 0.9, 3.7)), s((12.9, -0.6, 3.3))]
        rad = [2.5, 2.2, 1.45, 0.45]

        def aleta(X, Y, Z, pts=pts, rad=rad):
            # Pala aplanada: tubo de cápsulas con la sección achatada (1 de grosor en la base, 0,2 en el borde).
            return C.tubo(X, Y, Z, pts, rad, escala_z=0.22, k=0.5)

        P[f"Aleta_Pectoral_{nom}"] = [(aleta, 0.6)]
    P["Aleta_Dorsal"] = [
        (cap((0, -0.4, 11.3), (0, -6.9, 11.1), 0.85, 0.7), 0.8),
        (el(ALETA_DORSAL, (0.85, 3.4, 2.0)), 0.6),
    ]
    P["Cola_Base"] = [(cap(COLA[0], COLA[1], 3.1, 2.1), 0.9)]
    P["Cola_Media"] = [(cap(COLA[1], COLA[2], 2.05, 1.35), 0.6)]

    def aleta_caudal(X, Y, Z):
        # Media luna HORIZONTAL de 10 × 5 × 1: forma en planta (x, y) extruida con grosor que se afila al borde.
        cx, cy, cz = COLA[3]
        u = np.abs(X - cx)
        y = Y - cy
        borde_ataque = 0.6 - 0.11 * u ** 1.6          # delante: se curva hacia atrás
        borde_fuga = -2.6 - 0.5 * u + 0.09 * u ** 2.2   # detrás: media luna con muesca central
        muesca = 0.9 * np.exp(-(u / 0.7) ** 2)
        borde_fuga = borde_fuga + muesca
        dentro = np.minimum(y - borde_fuga, borde_ataque - y)
        dentro = np.minimum(dentro, 5.0 - u)
        grosor = 0.5 * np.clip(dentro / 1.4, 0, 1) ** 0.6 * (1 - 0.6 * np.clip(u / 5.0, 0, 1)) + 0.1
        e = np.abs(Z - cz) - grosor
        d2 = -dentro
        return np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(e, 0) ** 2) + np.minimum(np.maximum(d2, e), 0)

    P["Cola_Punta"] = [(cap(COLA[2], COLA[3], 1.3, 0.8), 0.5), (aleta_caudal, 0.6)]
    return P


PRIM = primitivas()
PIEZAS = list(PRIM.keys())


def _d(nombre, X, Y, Z):
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
    # Cavidad interna (hueca) con dos aperturas laterales de 3 × 5 y labio de cartílago reforzado.
    hueco = C.elipsoide(X, Y, Z, (0, -0.5, ZC), (4.6, 7.0, 3.1))
    f = C.smax(f, -hueco, 0.4)
    for lado in (1, -1):
        ax, ay, az = APERTURA
        ventana = C.elipsoide(X, Y, Z, (lado * (ax + 0.3), ay, az), (2.2, 2.5, 1.5))
        labio = C.elipsoide(X, Y, Z, (lado * (ax - 0.15), ay, az), (0.9, 2.85, 1.85))
        f = C.smin(f, labio, 0.35)
        f = C.smax(f, -ventana, 0.25)
        # Ojos hundidos en sus cuencas con arco supraorbital.
        ox, oy, oz = OJO
        f = C.smin(f, C.elipsoide(X, Y, Z, (lado * (ox - 0.2), oy, oz + 0.75), (0.75, 1.25, 0.35)), 0.4)
        f = C.smax(f, -(np.sqrt((X - lado * ox) ** 2 + (Y - oy) ** 2 + (Z - oz) ** 2) - 0.52), 0.12)
    # Espiráculo dorsal (1 stud) desplazado a la izquierda.
    f = C.smax(f, -C.elipsoide(X, Y, Z, (-1.2, 14.6, ZC + 4.6), (0.42, 0.55, 0.6)), 0.12)
    f = C.smin(f, C.smax(C.elipsoide(X, Y, Z, (-1.2, 14.6, ZC + 4.45), (0.75, 0.85, 0.3)),
                         -C.elipsoide(X, Y, Z, (-1.2, 14.6, ZC + 4.6), (0.45, 0.58, 0.8)), 0.05), 0.15)
    # Boca: cavidad entre la cabeza y la mandíbula (el interior brilla en azul).
    f = C.smax(f, -C.elipsoide(X, Y, Z, (0, 14.4, 5.15), (1.25, 4.6, 0.32)), 0.08)
    # Cicatriz de arpón (diagonal, hundida 0,1) en el flanco izquierdo.
    f = C.smax(f, -C.capsula(X, Y, Z, (-7.0, 3.6, 9.4), (-6.2, 1.4, 7.6), 0.14), 0.05)
    # Surcos ventrales (14) como en una ballena: sólo bajo la cabeza y el pecho.
    for k in range(14):
        x = -3.4 + k * 0.52
        surco = C.capsula(X, Y, Z, (x, 15.5, 3.75), (x * 1.25, 3.0, 2.75), 0.09)
        f = C.smax(f, -surco, 0.06)
    return f


def campo_pieza(nombre):
    otros = [n for n in PIEZAS if n != nombre]

    def campo(xs, ys, zs):
        X = xs[:, None, None]
        Y = ys[None, :, None]
        Z = zs[None, None, :]
        f = campo_total(X, Y, Z)
        propio = _d(nombre, X, Y, Z)
        ajeno = None
        for n in otros:
            d = _d(n, X, Y, Z)
            ajeno = d if ajeno is None else np.minimum(ajeno, d)
        f = C.smax(f, propio - ajeno + 2 * G, 0.03)
        return f.astype(np.float32)

    return campo


def caja(nombre, margen=0.6):
    xs = np.linspace(-14, 14, 113)
    ys = np.linspace(-24, 22, 185)
    zs = np.linspace(-1, 16, 69)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    d = _d(nombre, X, Y, Z)
    idx = np.argwhere(d < 0.3)
    mn = np.array([xs[idx[:, 0].min()], ys[idx[:, 1].min()], zs[idx[:, 2].min()]]) - margen
    mx = np.array([xs[idx[:, 0].max()], ys[idx[:, 1].max()], zs[idx[:, 2].max()]]) + margen
    return mn, mx


def voxel(nombre):
    return {"Cuerpo_Principal": 0.075, "Cabeza": 0.06, "Mandibula_Inf": 0.04, "Aleta_Dorsal": 0.045,
            "Cola_Base": 0.06, "Cola_Media": 0.05, "Cola_Punta": 0.04}.get(nombre, 0.045)


def pivote(nombre):
    return {"Cabeza": CUELLO, "Mandibula_Inf": BISAGRA, "Aleta_Pectoral_Der": HOMBRO,
            "Aleta_Pectoral_Izq": esp(HOMBRO), "Aleta_Dorsal": (0.0, -3.5, 11.0), "Cola_Base": COLA[0],
            "Cola_Media": COLA[1], "Cola_Punta": COLA[2]}.get(nombre)
