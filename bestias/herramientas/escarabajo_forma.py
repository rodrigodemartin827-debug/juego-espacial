"""
Forma del Escarabajo Abisal: primitivas unidas con mezcla suave y repartidas entre las piezas del rig (como el dragón).
Los élitros no van aquí: son conchas geométricas que se apoyan sobre el cuerpo (escarabajo_abisal.py).

Coordenadas (studs): X = derecha, Y = delante, Z = arriba. Las patas apoyan en z = 0. De pie, mandíbulas abiertas 30°.
"""

import math

import numpy as np

import campos as C

G = 0.01


def esp(p):
    return (-p[0], p[1], p[2])


CUELLO = (0.0, 4.35, 2.85)          # unión cabeza-tórax
UNION_ABDOMEN = (0.0, -1.6, 2.7)
CUERNO = [(0, 6.05, 3.75), (0, 6.95, 4.55), (0, 7.4, 5.55), (0, 7.3, 6.45), (0, 6.9, 7.0)]
CUERNO_R = [0.62, 0.52, 0.4, 0.27, 0.16]
MANDIBULA = [(0.85, 6.85, 2.15), (1.2, 7.75, 2.1), (1.05, 8.65, 2.05), (0.5, 9.3, 2.0)]
MANDIBULA_R = [0.26, 0.2, 0.13, 0.05]
OJO = (1.22, 6.05, 3.05)

# Patas: cadera, rodilla, tobillo, punta del tarso (lado derecho; la izquierda es espejo)
PATAS = {
    "Del": [(2.35, 3.35, 2.1), (3.25, 4.25, 2.4), (3.55, 5.05, 0.8), (3.65, 5.6, 0.1)],
    "Med": [(2.65, 0.95, 2.0), (3.95, 1.2, 2.35), (4.45, 1.0, 0.8), (4.65, 0.9, 0.1)],
    "Tras": [(2.35, -1.55, 2.0), (3.75, -2.4, 2.45), (4.45, -3.8, 0.8), (4.65, -4.55, 0.1)],
}
GROSOR_PATA = {"Del": (0.48, 0.38, 0.22), "Med": (0.44, 0.34, 0.2), "Tras": (0.55, 0.4, 0.24)}


def primitivas():
    P = {}

    def el(c, r, rot=None):
        return lambda X, Y, Z: C.elipsoide(X, Y, Z, c, r, rot)

    def cap(a, b, ra, rb=None):
        return lambda X, Y, Z: C.capsula(X, Y, Z, a, b, ra, rb)

    P["Torso"] = [
        (el((0, 1.15, 2.7), (3.25, 3.25, 1.55)), 0.5),
        (el((0, 2.75, 3.35), (2.8, 1.9, 0.95)), 0.6),     # pronoto (escudo del tórax)
        (el((0, 0.9, 1.75), (2.3, 2.7, 0.75)), 0.5),      # vientre
    ]
    P["Cabeza"] = [
        (el((0, 5.55, 2.9), (1.5, 1.6, 1.2)), 0.4),
        (el((0, 6.55, 2.7), (1.25, 0.95, 0.85)), 0.4),    # cuña / pala
        (el((0, 6.45, 3.25), (1.15, 0.9, 0.35)), 0.3),    # placa frontal
        (el(OJO, (0.45, 0.62, 0.42)), 0.15),
        (el(esp(OJO), (0.45, 0.62, 0.42)), 0.15),
    ]
    P["Cuerno_Central"] = [(cap(CUERNO[i], CUERNO[i + 1], CUERNO_R[i], CUERNO_R[i + 1]), 0.2) for i in range(4)]
    for lado, nom in ((1, "Der"), (-1, "Izq")):
        s = (lambda p: p) if lado > 0 else esp
        m = [s(p) for p in MANDIBULA]
        P[f"Mandibula_{nom}"] = [(cap(m[i], m[i + 1], MANDIBULA_R[i], MANDIBULA_R[i + 1]), 0.12) for i in range(3)]
    P["Abdomen"] = [
        (el((0, -4.75, 2.6), (2.75, 3.85, 1.65)), 0.7),
        (cap((0.4, -8.4, 2.6), (0.65, -9.05, 2.85), 0.13, 0.05), 0.1),   # cercos
        (cap((-0.4, -8.4, 2.6), (-0.65, -9.05, 2.85), 0.13, 0.05), 0.1),
    ]
    for tipo, pts in PATAS.items():
        r = GROSOR_PATA[tipo]
        for lado, nom in ((1, "Der"), (-1, "Izq")):
            s = (lambda p: p) if lado > 0 else esp
            h, k, a, t = (s(p) for p in pts)
            P[f"Pata_{tipo}_{nom}"] = [
                (cap(h, k, r[0], r[0] * 0.85), 0.1),
                (el(k, (r[0] * 0.95,) * 3), 0.08),            # junta esférica
                (cap(k, a, r[1], r[1] * 0.75), 0.1),
                (el(a, (r[1] * 0.85,) * 3), 0.06),
                (cap(a, t, r[2], r[2] * 0.7), 0.08),
            ]
    return P


PRIM = primitivas()
PIEZAS = list(PRIM.keys())

# Cráteres de impacto en el pronoto y el abdomen (centro, radio): depresiones reales con borde.
CRATERES = [((0.9, 3.4, 4.25), 0.38), ((-1.35, 2.2, 4.15), 0.48), ((1.7, 1.6, 3.95), 0.3), ((-0.4, -7.4, 3.55), 0.36),
            ((1.2, -6.2, 3.85), 0.3)]


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
    # Seis estrías longitudinales en el cuerno (canales estructurales).
    for k in range(6):
        a = math.tau * k / 6 + 0.3
        surco = None
        for i in range(4):
            p0, p1 = np.array(CUERNO[i]), np.array(CUERNO[i + 1])
            d = p1 - p0
            lado = np.array([math.cos(a), 0.0, 0.0]) + np.cross(d / np.linalg.norm(d), [1, 0, 0]) * math.sin(a)
            lado /= np.linalg.norm(lado)
            q0 = p0 + lado * CUERNO_R[i] * 0.98
            q1 = p1 + lado * CUERNO_R[i + 1] * 0.98
            c = C.capsula(X, Y, Z, q0, q1, 0.05 * (1 - i / 5), 0.04 * (1 - i / 5))
            surco = c if surco is None else np.minimum(surco, c)
        f = C.smax(f, -surco, 0.03)
    # Muesca lateral del cuerno (fragmento roto).
    f = C.smax(f, -C.elipsoide(X, Y, Z, (0.3, 7.5, 5.85), (0.18, 0.22, 0.16)), 0.03)
    # Cráteres.
    for (c, r) in CRATERES:
        hoyo = C.elipsoide(X, Y, Z, (c[0], c[1], c[2] + r * 0.45), (r, r, r * 0.6))
        f = C.smax(f, -hoyo, 0.05)
        borde = C.elipsoide(X, Y, Z, c, (r * 1.25, r * 1.25, r * 0.32))
        f = C.smin(f, C.smax(borde, -C.elipsoide(X, Y, Z, c, (r * 1.05, r * 1.05, r)), 0.03), 0.06)
    # Segmentos del abdomen (4 surcos) y suturas del tórax.
    for y in (-3.9, -5.2, -6.5, -7.6):
        ranura = np.abs(Y - y) - 0.035  # surco de 0,07 de ancho y ~0,06 de hondo
        f = np.where((Y < -2.5) & (Y > -8.5), C.smax(f, -np.maximum(ranura, f - 0.06), 0.02), f)
    # Espiráculos: 4 pares de ranuras laterales en el tórax y el abdomen.
    for y in (2.0, 0.3, -3.6, -5.6):
        for lado in (1, -1):
            x = lado * (3.05 if y > -2 else 2.35)
            f = C.smax(f, -C.elipsoide(X, Y, Z, (x, y, 2.45), (0.08, 0.15, 0.05)), 0.02)
    # Glándula de alquitrán: abertura ventral con bordes endurecidos.
    f = C.smax(f, -C.elipsoide(X, Y, Z, (0, -7.4, 1.05), (0.32, 0.45, 0.2)), 0.04)
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
        f = C.smax(f, propio - ajeno + 2 * G, 0.02)
        return f.astype(np.float32)

    return campo


def caja(nombre, margen=0.3):
    xs = np.linspace(-5.4, 5.4, 109)
    ys = np.linspace(-9.6, 9.8, 195)
    zs = np.linspace(-0.2, 7.6, 79)
    X, Y, Z = np.meshgrid(xs, ys, zs, indexing="ij")
    d = _d(nombre, X, Y, Z)
    idx = np.argwhere(d < 0.15)
    mn = np.array([xs[idx[:, 0].min()], ys[idx[:, 1].min()], zs[idx[:, 2].min()]]) - margen
    mx = np.array([xs[idx[:, 0].max()], ys[idx[:, 1].max()], zs[idx[:, 2].max()]]) + margen
    return mn, mx


def voxel(nombre):
    if nombre in ("Torso", "Abdomen"):
        return 0.032
    if nombre == "Cabeza":
        return 0.022
    if nombre.startswith("Mandibula") or nombre == "Cuerno_Central":
        return 0.016
    return 0.022


def pivote(nombre):
    if nombre == "Cabeza":
        return CUELLO
    if nombre == "Abdomen":
        return UNION_ABDOMEN
    if nombre == "Cuerno_Central":
        return CUERNO[0]
    if nombre.startswith("Mandibula"):
        return MANDIBULA[0] if nombre.endswith("Der") else esp(MANDIBULA[0])
    if nombre.startswith("Pata"):
        _, tipo, lado = nombre.split("_")
        h = PATAS[tipo][0]
        return h if lado == "Der" else esp(h)
    return None
