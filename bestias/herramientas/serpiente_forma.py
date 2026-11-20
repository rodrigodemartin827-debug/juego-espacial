"""
Forma orgánica de la Serpiente Cósmica: un tubo de sección ovalada (3 × 2 studs) de 30 studs con anillos musculares
cada 2 studs, cabeza de serpiente aplanada con mandíbula, y cola aplanada en remo. Se corta en planos (y constante)
entre segmentos, con 0,02 de separación.

Coordenadas (studs): X = derecha, Y = delante, Z = arriba. El vientre apoya en z = 0. Todo en línea recta.
"""

import math

import numpy as np

import campos as C

G = 0.01
ZC = 1.0                      # altura del eje del cuerpo
CORTES = [12.0, 8.0, 4.0, 0.0, -4.0, -8.0, -12.0]   # Cabeza | S1 | S2 | S3 | S4 | S5 | S6 | Cola_Punta
PUNTA_HOCICO = 15.15
FIN_COLA = -14.3

# Perfil de la sección a lo largo del cuerpo: (y, semiancho, semialto)
PERFIL = [(12.6, 0.78, 0.66), (11.6, 0.9, 0.72), (10.0, 1.25, 0.88), (8.0, 1.5, 1.0), (2.0, 1.55, 1.0), (-4.0, 1.48, 0.95),
          (-8.0, 1.3, 0.82), (-11.5, 1.05, 0.62), (-12.6, 0.98, 0.46), (-13.6, 1.08, 0.2), (-14.3, 0.9, 0.12)]

OJO = (0.80, 13.6, 1.36)
OJO_R = 0.5
BOCA_Z = 0.98                 # línea de la boca
BISAGRA = (0.0, 12.35, 0.95)
CAVIDAD = ((0.0, 13.75, 0.98), (0.72, 1.2, 0.12))


def perfil(y):
    ys = np.array([p[0] for p in PERFIL])[::-1]
    rx = np.interp(y, ys, np.array([p[1] for p in PERFIL])[::-1])
    rz = np.interp(y, ys, np.array([p[2] for p in PERFIL])[::-1])
    return rx, rz


def campo_total(X, Y, Z):
    rx, rz = perfil(Y)
    # Anillos musculares: un surco cada 2 studs.
    d = ((Y + 1000.0) % 2.0)
    d = np.minimum(d, 2.0 - d)
    surco = 1 - 0.03 * np.exp(-(d / 0.09) ** 2)
    rx = rx * surco
    rz = rz * surco
    # Cola: el centro baja al aplanarse para que el remo quede a la altura del eje.
    cz = ZC
    k = np.sqrt((X / rx) ** 2 + ((Z - cz) / rz) ** 2)
    f = (k - 1.0) * np.minimum(rx, rz)
    f = C.smax(f, Y - 12.9, 0.4)                     # el tubo termina en el cuello
    f = C.smax(f, FIN_COLA - Y, 0.5)                 # punta redondeada del remo
    # Cabeza: cráneo aplanado y hocico redondeado, mandíbula debajo.
    # Cabeza de víbora: ancha atrás (músculos de la mandíbula), plana arriba, hocico más estrecho y redondeado.
    cab = C.elipsoide(X, Y, Z, (0, 13.15, 1.2), (0.95, 1.35, 0.46))
    cab = C.smin(cab, C.elipsoide(X, Y, Z, (0, 14.45, 1.12), (0.62, 0.78, 0.34)), 0.5)
    for lado in (1, -1):
        cab = C.smin(cab, C.elipsoide(X, Y, Z, (lado * 0.66, 12.85, 1.02), (0.42, 0.72, 0.42)), 0.35)
    cab = C.smin(cab, C.elipsoide(X, Y, Z, (0, 13.35, 0.74), (0.88, 1.5, 0.3)), 0.3)      # mandíbula
    for lado in (1, -1):  # crestas protectoras sobre los ojos (planas, pegadas al cráneo)
        cab = C.smin(cab, C.elipsoide(X, Y, Z, (lado * 0.6, 13.6, 1.62), (0.34, 0.66, 0.1),
                                      C.matriz_giro((0, 1, 0), -lado * 0.22)), 0.18)
    f = C.smin(f, cab, 0.6)
    # Cavidades: boca, ojos, fosas sensoriales y fosas nasales.
    f = C.smax(f, -C.elipsoide(X, Y, Z, *CAVIDAD), 0.03)
    for lado in (1, -1):
        ojo = np.sqrt((X - lado * OJO[0]) ** 2 + (Y - OJO[1]) ** 2 + (Z - OJO[2]) ** 2) - (OJO_R + 0.02)
        f = C.smax(f, -ojo, 0.06)
        fosa = C.elipsoide(X, Y, Z, (lado * 0.48, 14.45, 1.3), (0.08, 0.11, 0.08))
        f = C.smax(f, -fosa, 0.03)
        nariz = C.elipsoide(X, Y, Z, (lado * 0.28, 15.05, 1.22), (0.07, 0.1, 0.05))
        f = C.smax(f, -nariz, 0.02)
    return f


def region_mandibula(X, Y, Z):
    """Negativo dentro de la mandíbula: por debajo de la línea de la boca y por delante de la bisagra."""
    planta = (np.sqrt((X / 1.25) ** 2 + ((Y - 14.0) / 1.68) ** 2) - 1.0) * 1.2
    return np.maximum(Z - BOCA_Z, planta)


def campo_pieza(nombre):
    def campo(xs, ys, zs):
        X = xs[:, None, None]
        Y = ys[None, :, None]
        Z = zs[None, None, :]
        f = campo_total(X, Y, Z)
        if nombre == "Cabeza":
            f = C.smax(f, CORTES[0] + G - Y, 0.012)
            f = C.smax(f, G - region_mandibula(X, Y, Z), 0.012)
        elif nombre == "Mandibula":
            f = C.smax(f, region_mandibula(X, Y, Z) + G, 0.012)
            f = C.smax(f, CORTES[0] + G - Y, 0.012)
        elif nombre == "Cola_Punta":
            f = C.smax(f, Y - (CORTES[-1] - G), 0.012)
        else:
            i = int(nombre.split("_")[1])
            y_ini, y_fin = CORTES[i - 1], CORTES[i]
            f = C.smax(f, Y - (y_ini - G), 0.012)
            f = C.smax(f, (y_fin + G) - Y, 0.012)
        return f.astype(np.float32)

    return campo


PIEZAS = ["Cabeza", "Mandibula"] + [f"Segmento_{i}" for i in range(1, 7)] + ["Cola_Punta"]


def caja(nombre):
    if nombre in ("Cabeza", "Mandibula"):
        return (-1.7, 11.9, -0.1), (1.7, 15.4, 2.0)
    if nombre == "Cola_Punta":
        return (-1.3, -14.6, 0.3), (1.3, -11.9, 1.7)
    i = int(nombre.split("_")[1])
    return (-1.75, CORTES[i] - 0.1, -0.1), (1.75, CORTES[i - 1] + 0.1, 2.1)


def voxel(nombre):
    return {"Cabeza": 0.018, "Mandibula": 0.016, "Cola_Punta": 0.016}.get(nombre, 0.03)


def pivote(nombre):
    if nombre == "Cabeza":
        return (0.0, CORTES[0], ZC)
    if nombre == "Mandibula":
        return BISAGRA
    if nombre == "Cola_Punta":
        return (0.0, CORTES[-1], ZC)
    i = int(nombre.split("_")[1])
    return (0.0, CORTES[i - 1], ZC)  # Segmento_1: extremo delantero (raíz); el resto, unión con el anterior


def superficie_arriba(x, y):
    rx, rz = perfil(y)
    if abs(x) >= rx:
        return ZC
    return ZC + rz * math.sqrt(1 - (x / rx) ** 2)
