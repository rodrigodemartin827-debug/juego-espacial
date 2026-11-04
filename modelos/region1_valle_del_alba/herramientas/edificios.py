"""
Montaje de edificios con las piezas del kit (kit.py).

Un edificio ya NO es una malla: es una LISTA DE PIEZAS del kit, cada una con su posición (matriz 4x4 respecto al
origen del edificio) y su color de instancia. En Roblox cada pieza será una copia de la MeshPart del kit (la malla se
sube una vez y Roblox la reutiliza); en Blender, una copia enlazada de la malla de la pieza.

Un edificio se pide con pocos datos (módulos de ancho y de fondo, pisos, tipo y una semilla) y sale con su
variedad: color del yeso, de las tejas, de las contraventanas, de la puerta y del toldo; jardineras; chimeneas.

Origen: esquina delantera izquierda de los muros, a la altura del suelo de la planta baja. La fachada principal está
en y = 0 y mira a -Y; el edificio ocupa x ∈ [0, ancho] e y ∈ [0, fondo]. Todos los pisos miden 10 studs.

Tipos: casa (Aurora), rustica (entramado en los pisos altos: Pradoverde, Los Molinos), tienda (escaparates, toldos
y cartel), ayuntamiento (fachada simétrica y portada; ver ayuntamiento()).
"""

import numpy as np

import kit as K
from malla import Rz, T, compone

M = K.M
H = K.H

# Colores (sRGB) entre los que elige cada edificio. Son los de la primera versión (materiales.PALETA).
COLORES = {
    "PARED": ["#EFE2C6", "#F2EFE7", "#EECBA8", "#EFD898", "#E8BFB2", "#CBDDE0"],
    "TEJA": ["#B4452C", "#963A2A", "#C45F38"],
    "PINTURA": ["#4F7F5E", "#4C6F94", "#9B4B3B", "#E9DFC5"],
    "PUERTA": ["#8A6340", "#5C4130", "#4F7F5E", "#4C6F94", "#9B4B3B"],
    "TOLDO": ["#C2413A", "#3F6FA8", "#E8B840", "#4E8C5A"],
}
RUSTICA_PARED = ["#EFE2C6", "#F2EFE7", "#EFD898"]


class Edificio:
    def __init__(self, piezas, ancho, fondo, alto, puerta, nombre=""):
        self.piezas = piezas  # lista de (nombre de pieza, matriz 4x4, color sRGB)
        self.ancho, self.fondo, self.alto = ancho, fondo, alto
        self.puerta = puerta  # (x, y) de la puerta principal, en coordenadas del edificio
        self.nombre = nombre

    @property
    def n_triangulos(self):
        return sum(triangulos_pieza(p) for p, _, _ in self.piezas)


_TRIS = {}


def triangulos_pieza(nombre, lejos=False):
    k = (nombre, lejos)
    if k not in _TRIS:
        m = K.malla(nombre, lejos)
        _TRIS[k] = m.n_triangulos if m is not None else 0
    return _TRIS[k]


def _lados(nx, ny):
    W, D = nx * M, ny * M
    return {
        "frente": (nx, T(0, 0, 0)),
        "derecha": (ny, compone(T(W, 0, 0), Rz(90))),
        "fondo": (nx, compone(T(W, D, 0), Rz(180))),
        "izquierda": (ny, compone(T(0, D, 0), Rz(270))),
    }


def _hex_de(nombre_material):
    import materiales as MAT

    return MAT.PALETA[nombre_material][0] if nombre_material in MAT.PALETA else nombre_material


def elegir_colores(rng, tipo, extra=None):
    c = {k: v[int(rng.integers(len(v)))] for k, v in COLORES.items()}
    if tipo == "rustica":
        c["PARED"] = RUSTICA_PARED[int(rng.integers(len(RUSTICA_PARED)))]
    for k, v in (extra or {}).items():
        if k in c:
            c[k] = _hex_de(v)
    return c


def edificio(nx, ny, pisos, semilla, tipo="casa", puerta_en="frente", puerta_i=None, emblema="bolsa",
             chimeneas=None, remap_extra=None):
    rng = np.random.default_rng(semilla)
    W, D = nx * M, ny * M
    ztop = pisos * H
    col = elegir_colores(rng, tipo, remap_extra)
    piezas = []

    def poner(nombre, m, color=None):
        piezas.append((nombre, m, color or K.color_defecto(nombre)))

    poner(K.losa_nombre(nx, ny), np.eye(4))
    lados = _lados(nx, ny)
    if puerta_i is None:
        puerta_i = lados[puerta_en][0] // 2 if tipo != "rustica" else int(rng.integers(lados[puerta_en][0]))
    puerta_xy = None
    jardineras = rng.uniform() < (0.75 if tipo in ("rustica", "casa") else 0.4)
    trasero_de = {"frente": "fondo", "fondo": "frente", "izquierda": "derecha", "derecha": "izquierda"}

    def ventana(mt, baja, entramado):
        nombre = "Entramado_Ventana" if entramado else ("Pared_Ventana_Baja" if baja else "Pared_Ventana")
        poner(nombre, mt, col["PARED"])
        poner("Contraventanas", mt, col["PINTURA"])
        if jardineras and rng.uniform() < 0.5:
            poner("Jardinera", mt)

    def puerta_en_muro(mt):
        poner("Pared_Puerta", mt, col["PARED"])
        poner("Puerta", mt, col["PUERTA"])
        poner("Farolillo", compone(mt, T(7.4, 0, 6.8)))

    for lado, (n, base) in lados.items():
        principal = lado == puerta_en
        trasero = lado == trasero_de[puerta_en]
        for piso in range(pisos):
            z0 = piso * H
            for i in range(n):
                mt = compone(base, T(i * M, 0, z0))
                if piso == 0:
                    if principal and i == puerta_i:
                        puerta_en_muro(mt)
                        puerta_xy = (base @ np.array([i * M + M / 2, -1.5, 0, 1.0]))[:2]
                    elif tipo == "tienda" and principal:
                        poner("Pared_Escaparate", mt, col["PARED"])
                        poner("Toldo", mt, col["TOLDO"])
                    elif trasero and i == n // 2 and tipo != "ayuntamiento" and rng.uniform() < 0.6:
                        puerta_en_muro(mt)
                    elif (not principal) and rng.uniform() < 0.35:
                        poner("Pared_Lisa_Baja", mt, col["PARED"])
                    else:
                        ventana(mt, True, False)
                else:
                    if lado in ("izquierda", "derecha") and rng.uniform() < 0.4:
                        poner("Entramado_Lisa" if tipo == "rustica" else "Pared_Lisa", mt, col["PARED"])
                    else:
                        ventana(mt, False, tipo == "rustica")
            poner("Esquina", compone(base, T(0, 0, z0)), col["PARED"])
        for i in range(n):
            poner("Cornisa", compone(base, T(i * M, 0, ztop - 0.6)))
        poner("Cornisa_Esquina", compone(base, T(0, 0, ztop - 0.6)))
        if tipo == "tienda" and principal:
            poner(f"Cartel_{emblema.capitalize()}", compone(base, T(0.4 if puerta_i else -0.2, 0, H - 2.6)))

    # Tejado a dos aguas por tramos, con remates, hastiales y cumbrera. El lado derecho es el izquierdo girado 180°.
    f = 16 if D <= 16 else 24
    if D not in (16, 24):
        raise ValueError(f"fondo {D} sin piezas de tejado (solo 16 y 24)")
    derecho = compone(T(W, D, ztop), Rz(180))
    for i in range(nx):
        poner(f"Tejado_Tramo_{f}", T(i * M, 0, ztop), col["TEJA"])
        poner(f"Cumbrera_{f}", T(i * M, 0, ztop), col["TEJA"])
    poner(f"Tejado_Remate_{f}", T(0, 0, ztop), col["TEJA"])
    poner(f"Tejado_Remate_{f}", derecho, col["TEJA"])
    poner(f"Hastial_{f}", T(0, 0, ztop), col["PARED"])
    poner(f"Hastial_{f}", derecho, col["PARED"])
    poner(f"Cumbrera_Remate_{f}", T(-K.VUELO, 0, ztop), col["TEJA"])
    poner(f"Cumbrera_Remate_{f}", T(W, 0, ztop), col["TEJA"])
    alto_total = ztop + D / 2 * K.PEND
    nch = chimeneas if chimeneas is not None else int(rng.integers(0, 3))
    for k in range(nch):
        x = float(rng.uniform(2.5, W - 2.5))
        y = D * 0.72
        zr = ztop + (D - y) * K.PEND
        poner("Chimenea", T(x, y, zr - 1.2))
    ed = Edificio(piezas, W, D, alto_total, puerta_xy)
    ed.ztop = ztop
    return ed


def ayuntamiento(semilla=7):
    """Ayuntamiento de Aurora: 7 × 3 módulos, 3 pisos, puerta en el módulo central y la portada (columnas,
    balcón, frontón con reloj y banderas) delante."""
    nx, ny, pisos = 7, 3, 3
    ed = edificio(nx, ny, pisos, semilla, tipo="ayuntamiento", puerta_i=3, chimeneas=0,
                  remap_extra={"PARED": "#F2EFE7", "TEJA": "#B4452C", "PINTURA": "#4C6F94", "PUERTA": "#5C4130"})
    ed.piezas.append(("Portada_Ayuntamiento", np.eye(4), "#3F6FA8"))
    ed.alto = max(ed.alto, pisos * H + 8)
    return ed
