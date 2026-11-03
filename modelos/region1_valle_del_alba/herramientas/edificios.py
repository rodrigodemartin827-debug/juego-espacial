"""
Montaje de edificios con las piezas del kit (kit.py). Un edificio se describe con pocos datos (módulos de ancho y de
fondo, pisos, tipo y una semilla) y sale una malla con su variedad: color de pared y de tejas, contraventanas,
jardineras, chimeneas, toldos...

Origen del edificio: esquina delantera izquierda de los muros, a la altura del suelo de la planta baja. La fachada
principal está en y = 0 y mira a -Y; el edificio ocupa x ∈ [0, ancho] e y ∈ [0, fondo]. La losa de piedra baja hasta
z = -4 para tapar cualquier desnivel del terreno.

Tipos:
  * casa       — vivienda de yeso con zócalo y esquinas de sillar (Aurora).
  * rustica    — como casa, pero con entramado de madera en los pisos altos (Pradoverde, Los Molinos).
  * tienda     — planta baja con escaparates, toldo y cartel con emblema.
  * ayuntamiento — fachada simétrica, portada con columnas y frontón, balcón y tejado a cuatro aguas.
"""

import numpy as np

import kit as K
from malla import Malla, Rz, S, T, compone

M = K.M
G = K.G
MED = K.MEDIDAS


class Edificio:
    def __init__(self, malla, ancho, fondo, alto, puerta, nombre=""):
        self.malla, self.ancho, self.fondo, self.alto = malla, ancho, fondo, alto
        self.puerta = puerta  # (x, y) de la puerta principal, en coordenadas del edificio
        self.nombre = nombre


def _lados(nx, ny):
    W, D = nx * M, ny * M
    return {
        "frente": (nx, T(0, 0, 0)),
        "derecha": (ny, compone(T(W, 0, 0), Rz(90))),
        "fondo": (nx, compone(T(W, D, 0), Rz(180))),
        "izquierda": (ny, compone(T(0, D, 0), Rz(270))),
    }


def elegir_materiales(rng, tipo):
    from materiales import VARIANTES

    def uno(r):
        v = VARIANTES[r]
        return v[int(rng.integers(len(v)))]

    remap = {r: uno(r) for r in VARIANTES}
    remap["TEJA_B"] = {"Teja_Roja": "Teja_Roja_Oscura", "Teja_Roja_Oscura": "Teja_Roja",
                       "Teja_Naranja": "Teja_Roja"}[remap["TEJA"]]
    remap["TOLDO_B"] = "Toldo_Blanco"
    if tipo == "rustica":
        remap["PARED"] = ["Yeso_Crema", "Yeso_Blanco", "Yeso_Amarillo"][int(rng.integers(3))]
        remap["MARCO"] = "Madera_Oscura"
    if remap["MARCO"] == "Yeso_Blanco" and remap["PARED"] == "Yeso_Blanco":
        remap["MARCO"] = "Madera_Oscura"
    return remap


def edificio(nx, ny, pisos, semilla, tipo="casa", puerta_en="frente", puerta_i=None, emblema="bolsa",
             tejado="dos_aguas", chimeneas=None, remap_extra=None):
    rng = np.random.default_rng(semilla)
    W, D = nx * M, ny * M
    alturas = [MED["piso_bajo"]] + [MED["piso"]] * (pisos - 1)
    zs = np.concatenate([[0.0], np.cumsum(alturas)])
    ztop = float(zs[-1])
    m = Malla()

    # Losa
    m.caja((-0.9, -0.9, -4.0), (W + 0.9, D + 0.9, 0.0), "Piedra_Media")
    m.caja((-1.0, -1.0, -0.25), (W + 1.0, D + 1.0, 0.0), "Piedra_Clara")

    lados = _lados(nx, ny)
    n_puerta = lados[puerta_en][0]
    if puerta_i is None:
        puerta_i = n_puerta // 2 if tipo != "rustica" else int(rng.integers(n_puerta))
    puerta_xy = None
    jardineras = rng.uniform() < (0.75 if tipo in ("rustica", "casa") else 0.4)

    for lado, (n, base) in lados.items():
        principal = lado == puerta_en
        trasero = lado == {"frente": "fondo", "fondo": "frente", "izquierda": "derecha", "derecha": "izquierda"}[
            puerta_en]
        for piso, (z0, h) in enumerate(zip(zs[:-1], alturas)):
            for i in range(n):
                s = int(rng.integers(1 << 30))
                mt = compone(base, T(i * M, 0, z0))
                if piso == 0:
                    if principal and i == puerta_i:
                        pieza = K.pared_puerta(h, semilla=s)
                        puerta_xy = (base @ np.array([i * M + M / 2, -1.5, 0, 1.0]))[:2]
                    elif tipo == "tienda" and principal:
                        pieza = K.pared_escaparate(h, semilla=s)
                        m.anadir(K.toldo(), compone(mt, T(0.4, 0, 0)))
                    elif trasero and i == n // 2 and tipo != "ayuntamiento" and rng.uniform() < 0.6:
                        pieza = K.pared_puerta(h, semilla=s)
                    else:
                        lisa = (not principal) and rng.uniform() < 0.35
                        pieza = K.pared_lisa(h) if lisa else K.pared_ventana(h, jardinera=jardineras and
                                                                              rng.uniform() < 0.5, semilla=s)
                else:
                    lisa = (lado in ("izquierda", "derecha")) and rng.uniform() < 0.4
                    if lisa:
                        pieza = K.pared_lisa(h)
                        if tipo == "rustica":
                            pieza.anadir(K.entramado(h, con_ventana=False))
                    else:
                        pieza = K.pared_ventana(h, jardinera=jardineras and rng.uniform() < 0.55, semilla=s)
                        if tipo == "rustica":
                            pieza.anadir(K.entramado(h, con_ventana=True))
                m.anadir(pieza, mt)
        L = n * M
        m.anadir(K.zocalo(L, semilla=int(rng.integers(1 << 30))), base)
        for z in zs[1:-1]:
            if tipo != "rustica":
                m.anadir(K.cornisa(L, 0.5, 0.3), compone(base, T(0, 0, z - 0.25)))
        m.anadir(K.cornisa(L, 0.6, 0.45), compone(base, T(0, 0, ztop - 0.6)))
        # esquina en el origen de cada lado (la delantera izquierda del lado)
        m.anadir(K.esquina(ztop - 0.6, semilla=int(rng.integers(1 << 30))), base)
        if tipo == "tienda" and principal:
            m.anadir(K.cartel(emblema), compone(base, T(-0.2 + (0.2 if puerta_i else 0), 0, MED["piso_bajo"] - 2.6),
                                                 Rz(0)))

    # Tejado
    if tejado == "dos_aguas":
        for i in range(nx):
            m.anadir(K.tejado_tramo(D, semilla=int(rng.integers(1 << 30))), T(i * M, 0, ztop))
        m.anadir(K.tejado_remate(D, -1, semilla=int(rng.integers(1 << 30))), T(0, 0, ztop))
        m.anadir(K.tejado_remate(D, +1, semilla=int(rng.integers(1 << 30))), T(W, 0, ztop))
        m.anadir(K.hastial(D, oculo=rng.uniform() < 0.6), T(0, 0, ztop))
        m.anadir(K.hastial(D, oculo=rng.uniform() < 0.6), compone(T(W, 0, ztop), S(-1, 1, 1)))
        m.anadir(K.cumbrera(W + 2 * MED["vuelo"], D, semilla=int(rng.integers(1 << 30))),
                 T(-MED["vuelo"], 0, ztop))
        alto_total = ztop + D / 2 * MED["pendiente"]
    else:
        m.anadir(K.tejado_cuatro_aguas(W, D, semilla=int(rng.integers(1 << 30))), T(0, 0, ztop))
        alto_total = ztop + min(W, D) / 2 * MED["pendiente"]
    # Chimeneas (sobre el faldón trasero, a 3/4 del fondo)
    nch = chimeneas if chimeneas is not None else int(rng.integers(0, 3)) if tejado == "dos_aguas" else 0
    for k in range(nch):
        x = float(rng.uniform(2.5, W - 2.5))
        y = D * 0.72
        zr = ztop + (D - y) * MED["pendiente"]
        m.anadir(K.chimenea(alto_total - zr + 1.5), T(x, y, zr - 1.2))

    remap = elegir_materiales(rng, tipo)
    if remap_extra:
        remap.update(remap_extra)
    final = Malla().anadir(m, remap=remap)
    return Edificio(final, W, D, alto_total, puerta_xy)


def ayuntamiento(semilla=7):
    """Ayuntamiento de Aurora: 6 × 3 módulos, 3 pisos, portada con columnas, frontón y balcón."""
    nx, ny, pisos = 6, 3, 3
    ed = edificio(nx, ny, pisos, semilla, tipo="ayuntamiento", tejado="cuatro_aguas", chimeneas=0,
                  remap_extra={"PARED": "Yeso_Blanco", "TEJA": "Teja_Roja", "TEJA_B": "Teja_Roja_Oscura",
                               "PINTURA": "Pintura_Azul", "PIEDRA": "Piedra_Clara", "MARCO": "Madera_Oscura",
                               "PUERTA": "Madera_Oscura"})
    m = ed.malla
    W = nx * M
    cx = W / 2
    # Portada: escalinata, 4 columnas, entablamento y frontón
    for k in range(3):  # escalones
        m.caja((cx - 10 - 1.2 * (2 - k), -7.0 + 1.6 * k, -4.0), (cx + 10 + 1.2 * (2 - k), 0.0, -0.6 + 0.2 * k),
               "Piedra_Clara", tinte=1.0 - 0.04 * k)
    for xc in (cx - 8.5, cx - 3.2, cx + 3.2, cx + 8.5):
        m.tronco((xc, -4.2, -0.2), 1.3, 1.3, 0.9, 8, "Piedra_Clara", giro=22.5)  # basa
        m.torno([(0.95, 0.7), (0.85, 9.0), (0.95, 9.3)], 12, "Yeso_Blanco", c=(xc, -4.2, 0.0))  # fuste
        m.tronco((xc, -4.2, 9.3), 1.0, 1.35, 0.8, 8, "Piedra_Clara", giro=22.5)  # capitel
    m.caja((cx - 10.5, -5.8, 10.1), (cx + 10.5, 0.2, 11.6), "Piedra_Clara")  # entablamento
    # balcón sobre la portada (barandilla de hierro)
    m.caja((cx - 10.5, -5.8, 11.6), (cx + 10.5, 0.2, 12.0), "Piedra_Media")
    for k in range(29):
        x = cx - 10.2 + k * 20.4 / 28
        m.caja((x - 0.1, -5.6, 12.0), (x + 0.1, -5.4, 14.6), "Hierro")
    m.caja((cx - 10.4, -5.75, 14.5), (cx + 10.4, -5.25, 14.9), "Hierro")
    # frontón en lo alto de la fachada central
    zt = MED["piso_bajo"] + 2 * MED["piso"]
    tri = Malla().prisma([(-11.5, 0.0), (11.5, 0.0), (0.0, 7.5)], 0, 1.5, "Yeso_Blanco")
    m.anadir(tri, compone(T(cx, -1.6, zt - 0.6), _xz()))
    for sgn in (-1, 1):
        m.viga((cx + sgn * 12.3, -1.3, zt - 0.6), (cx, -1.3, zt + 7.2), 0.9, "Piedra_Clara")
    m.caja((cx - 12.4, -1.8, zt - 1.0), (cx + 12.4, 0.2, zt - 0.4), "Piedra_Clara")
    m.anadir(K.reloj(2.6), T(cx, -1.4, zt + 2.8))
    # mástiles con banderas
    for sgn in (-1, 1):
        x = cx + sgn * 16
        m.viga((x, -1.2, MED["piso_bajo"] + 1.0), (x, -6.0, MED["piso_bajo"] + 6.0), 0.25, "Hierro")
        p0 = np.array([x, -6.0, MED["piso_bajo"] + 6.0])
        m.poligono([p0, p0 + (0, 2.2, -2.2), p0 + (0, 2.2 + 0, -6.2), p0 + (0, 0, -4.0)], "Toldo_Azul")
    ed.alto = max(ed.alto, zt + 8)
    return ed


def _xz():
    """Matriz que lleva un prisma construido en XY (extruido en Z) al plano XZ, extruido hacia +Y."""
    m = np.eye(4)
    m[:3, :3] = [[1, 0, 0], [0, 0, 1], [0, 1, 0]]
    # (x, y, z) -> (x, z, y): det = -1 -> la unión invierte el orden de las caras y las normales quedan bien.
    return m
