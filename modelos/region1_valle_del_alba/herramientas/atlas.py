"""
Atlas de texturas del kit: UNA imagen de 1024 × 1024 compartida por todas las piezas (y una máscara de emisión con la
misma distribución, para las ventanas y faroles encendidos en los renders).

Por qué un atlas: el detalle pequeño (tejas, sillares, marcos, contraventanas, tablas) pasa de la geometría a la
textura, y todas las piezas usan la misma imagen: en Roblox se sube una vez y la comparten todas las MeshPart.

Casillas de 128 × 128 píxeles (8 × 8 = 64). Cada casilla se pinta aquí con numpy, en coordenadas (u, v) de 0 a 1 con
la v hacia arriba (como en las UV).

TINTE: las superficies que cambian de color de un edificio a otro (yeso, tejas, contraventanas, puertas, toldos) son
TRANSPARENTES en el atlas (alfa 0) o semitransparentes donde llevan dibujo (juntas de tejas, lamas...). El color de
cada instancia (MeshPart.Color en Roblox, el color del objeto en Blender) se ve a través. Así UNA pieza sirve para
todos los colores. Las casillas opacas (piedra, madera, hierro, cristal...) ignoran el color de la instancia.
"""

import math
import os

import numpy as np
from PIL import Image

TAM = 1024
CASILLA = 128
N = TAM // CASILLA
MARGEN_UV = 2.0 / TAM  # las UV no llegan al borde de la casilla: evita que se mezclen casillas vecinas al filtrar

# Orden de las casillas (de arriba a abajo, de izquierda a derecha). El nombre es el «material» de las caras.
CASILLAS = [
    # fila 0: paredes de yeso (teñibles), 8 × 10 studs por casilla
    "pared_lisa", "pared_lisa_baja", "pared_ventana", "pared_ventana_baja", "pared_puerta", "pared_escaparate",
    "entramado_lisa", "entramado_ventana",
    # fila 1: versiones lejanas (todo pintado: ventana, contraventanas) y hastial
    "pared_ventana_lejos", "pared_ventana_baja_lejos", "pared_puerta_lejos", "pared_escaparate_lejos",
    "entramado_ventana_lejos", "hastial", "sillares", "silueta_fachada",
    # fila 2: tejados (teñibles) y elementos de fachada
    "teja_16", "teja_24", "cumbrera", "teja_lejos", "ventana", "escaparate", "contraventana", "puerta",
    # fila 3: toldo, carteles
    "toldo", "cartel_bolsa", "cartel_espada", "cartel_gema", "cartel_yunque", "cartel_pan", "cartel_pocion",
    "jardinera",
    # fila 4: materiales opacos
    "piedra_clara", "piedra_media", "piedra_oscura", "sillar_muro", "ladrillo", "madera_clara", "madera_media",
    "madera_oscura",
    # fila 5
    "hierro", "oro", "vidrio", "luz", "tablon", "reloj", "agua", "vela",
    # fila 6: vegetación
    "hoja_verde", "hoja_clara", "hoja_oscura", "hoja_pino", "flor_rosa", "corteza", "abedul", "hierba",
    # fila 7
    "flores", "trigo", "col", "tierra_arada", "calabaza", "fruta", "paja", "silueta_teja",
]
assert len(CASILLAS) == N * N, len(CASILLAS)
INDICE = {n: i for i, n in enumerate(CASILLAS)}

# Casillas teñibles (las demás son opacas): sirve para saber qué color poner a cada instancia.
TENIBLES = {"pared_lisa", "pared_lisa_baja", "pared_ventana", "pared_ventana_baja", "pared_puerta",
            "pared_escaparate", "entramado_lisa", "entramado_ventana", "pared_ventana_lejos",
            "pared_ventana_baja_lejos", "pared_puerta_lejos", "pared_escaparate_lejos", "entramado_ventana_lejos",
            "hastial", "sillares", "teja_16", "teja_24", "cumbrera", "teja_lejos", "contraventana", "puerta",
            "toldo"}


def rect_uv(nombre):
    """(u0, v0, u1, v1) de la casilla en el atlas (v = 0 abajo), con un pequeño margen."""
    i = INDICE[nombre]
    col, fila = i % N, i // N
    u0 = col / N
    v1 = 1.0 - fila / N
    return (u0 + MARGEN_UV, v1 - 1.0 / N + MARGEN_UV, u0 + 1.0 / N - MARGEN_UV, v1 - MARGEN_UV)


def a_atlas(nombre, u, v):
    """Lleva (u, v) locales de una casilla (0..1) a coordenadas del atlas."""
    u0, v0, u1, v1 = rect_uv(nombre)
    return u0 + np.clip(u, 0, 1) * (u1 - u0), v0 + np.clip(v, 0, 1) * (v1 - v0)


# ==============================================================================================================
# Pintura
# ==============================================================================================================


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


class Lienzo:
    """Una casilla RGBA en coordenadas (u, v) de 0 a 1 (v hacia arriba) y su máscara de emisión."""

    def __init__(self, semilla=0):
        s = CASILLA
        g = (np.arange(s) + 0.5) / s
        self.U, self.V = np.meshgrid(g, g[::-1])
        self.rgba = np.zeros((s, s, 4), np.float32)
        self.em = np.zeros((s, s), np.float32)
        self.rng = np.random.default_rng(semilla)

    def pintar(self, mascara, color, alfa=1.0):
        m = np.asarray(mascara, np.float32) * alfa
        if m.ndim == 0:
            m = np.full(self.U.shape, float(m), np.float32)
        c = _hex(color) if isinstance(color, str) else np.asarray(color, np.float32)
        # composición «sobre»: el color nuevo encima del que hay
        a0 = self.rgba[..., 3]
        a = m + a0 * (1 - m)
        rgb = (c[None, None, :] * m[..., None] + self.rgba[..., :3] * (a0 * (1 - m))[..., None]) / np.maximum(
            a[..., None], 1e-6)
        self.rgba[..., :3] = rgb
        self.rgba[..., 3] = a

    def caja(self, u0, v0, u1, v1):
        return (self.U >= u0) & (self.U < u1) & (self.V >= v0) & (self.V < v1)

    def grano(self, intensidad=0.06, escala=1.0):
        """Ruido de grano (oscurece y aclara un poco); no cambia el alfa de lo opaco."""
        n = self.rng.normal(0, 1, self.U.shape).astype(np.float32)
        n = (n + np.roll(n, 1, 0) + np.roll(n, 1, 1) + np.roll(n, (1, 1), (0, 1))) / 2
        self.rgba[..., :3] *= (1 + intensidad * n)[..., None]

    def imagen(self):
        return np.clip(self.rgba, 0, 1)


def _opaco(color, grano=0.05, semilla=0, vetas=False):
    l = Lienzo(semilla)
    l.pintar(1.0, color)
    if vetas:  # vetas horizontales de madera
        f = np.sin(l.V * 60 + 3 * np.sin(l.U * 9)) * 0.5 + 0.5
        l.rgba[..., :3] *= (0.93 + 0.1 * f)[..., None]
    l.grano(grano)
    return l


# -------------------------------------------------------------------------------- paredes

# Medidas de los huecos en coordenadas de la casilla (módulo de 8 × 10 studs): las mismas que la geometría (kit.py).
M, H = 8.0, 10.0
VENTANA = (2.5 / M, 3.2 / H, 5.5 / M, 7.4 / H)  # u0, v0, u1, v1
PUERTA = (2.0 / M, 0.0, 6.0 / M, 7.4 / H)
ESCAPARATE = (0.9 / M, 1.3 / H, 7.1 / M, 7.6 / H)
ZOCALO_V = 1.7 / H
PIEDRA = "#CBC1B0"
PIEDRA_JUNTA = "#9C9384"
MADERA_OSC = "#5C4130"
MADERA = "#8A6340"
CRISTAL = "#2F4257"


def _yeso(l):
    """Yeso: transparente (tinte) con un poco de textura (manchas suaves, alfa bajo)."""
    n = l.rng.normal(0, 1, l.U.shape)
    for _ in range(3):
        n = (n + np.roll(n, 2, 0) + np.roll(n, 2, 1)) / 3
    l.pintar(np.clip(n * 0.6, 0, 1), "#000000", 0.08)
    l.pintar(np.clip(-n * 0.6, 0, 1), "#FFFFFF", 0.06)


def _zocalo(l):
    """Banda de sillares en la parte baja (opaca)."""
    z = l.V < ZOCALO_V
    l.pintar(z, "#A2998A")
    filas = 2
    hf = ZOCALO_V / filas
    fila = np.floor(l.V / hf)
    desfase = (fila % 2) * 0.11
    junta_h = (np.abs((l.V % hf) - hf) < 0.006) | ((l.V % hf) < 0.006)
    junta_v = ((l.U + desfase) % 0.22) < 0.008
    l.pintar(z & (junta_h | junta_v), "#7A746B")
    l.pintar((l.V >= ZOCALO_V) & (l.V < ZOCALO_V + 0.012), "#7A746B", 0.6)  # sombra de la repisa


def _recercado(l, u0, v0, u1, v1, ancho=0.055, clave=True, dintel=0.05):
    """Recercado de piedra alrededor de un hueco, con dintel y clave."""
    exterior = l.caja(u0 - ancho, v0 - 0.0, u1 + ancho, v1 + dintel)
    interior = l.caja(u0, v0, u1, v1)
    l.pintar(exterior & ~interior, PIEDRA)
    if clave:
        l.pintar(l.caja((u0 + u1) / 2 - 0.035, v1 - 0.01, (u0 + u1) / 2 + 0.035, v1 + dintel + 0.025), "#B8AE9C")
    # sombra a la derecha y abajo del recercado (luz de arriba a la izquierda)
    l.pintar(l.caja(u1 + ancho, v0, u1 + ancho + 0.012, v1 + dintel), "#000000", 0.18)


def _ventana_pintada(l, u0, v0, u1, v1, contraventanas=None):
    """Ventana completa pintada (para la versión lejana): marco, cristal, cruceta y contraventanas."""
    l.pintar(l.caja(u0, v0, u1, v1), MADERA_OSC)
    m = 0.02
    l.pintar(l.caja(u0 + m, v0 + m, u1 - m, v1 - m), CRISTAL)
    l.em = np.maximum(l.em, l.caja(u0 + m, v0 + m, u1 - m, v1 - m) * 0.5)
    um = (u0 + u1) / 2
    vm = v0 + (v1 - v0) * 0.62
    l.pintar(l.caja(um - 0.008, v0, um + 0.008, v1) | l.caja(u0, vm - 0.008, u1, vm + 0.008), MADERA_OSC)
    if contraventanas:
        w = (u1 - u0) / 2 + 0.005
        for a, b in ((u0 - 0.065 - w, u0 - 0.065), (u1 + 0.065, u1 + 0.065 + w)):
            l.pintar(l.caja(a, v0 + 0.01, b, v1 - 0.01), contraventanas)
            for k in range(5):
                vv = v0 + 0.04 + k * (v1 - v0 - 0.06) / 5
                l.pintar(l.caja(a + 0.01, vv, b - 0.01, vv + 0.012), "#000000", 0.25)


def pared(nombre):
    l = Lienzo(INDICE[nombre])
    _yeso(l)
    baja = "baja" in nombre or nombre in ("pared_puerta", "pared_escaparate", "pared_puerta_lejos",
                                          "pared_escaparate_lejos")
    if baja:
        _zocalo(l)
    if "ventana" in nombre and "entramado" not in nombre:
        _recercado(l, *VENTANA)
        if "lejos" in nombre:
            _ventana_pintada(l, *VENTANA, contraventanas="#5E8268")
            l.pintar(l.caja(VENTANA[0] - 0.07, VENTANA[1] - 0.04, VENTANA[2] + 0.07, VENTANA[1]), PIEDRA)
    if "puerta" in nombre:
        u0, v0, u1, v1 = PUERTA
        # jambas de sillares alternos y dintel con clave
        alto = 1.25 / H
        k = 0
        z = 0.0
        while z < v1 - 0.001:
            w = (0.75 if k % 2 else 1.05) / M
            l.pintar(l.caja(u0 - w, z + 0.004, u0, min(z + alto, v1) - 0.004), PIEDRA)
            l.pintar(l.caja(u1, z + 0.004, u1 + w, min(z + alto, v1) - 0.004), PIEDRA)
            z += alto
            k += 1
        l.pintar(l.caja(u0 - 1.05 / M, v1, u1 + 1.05 / M, v1 + 0.08), PIEDRA)
        l.pintar(l.caja((u0 + u1) / 2 - 0.05, v1 - 0.01, (u0 + u1) / 2 + 0.05, v1 + 0.1), "#B8AE9C")
        if "lejos" in nombre:
            l.pintar(l.caja(u0, v0, u1, v1), MADERA)
            for k in range(5):
                x = u0 + k * (u1 - u0) / 5
                l.pintar(l.caja(x, v0, x + 0.006, v1), "#000000", 0.3)
    if "escaparate" in nombre:
        u0, v0, u1, v1 = ESCAPARATE
        l.pintar(l.caja(u0 - 0.06, v1, u1 + 0.06, v1 + 0.13), MADERA_OSC)  # friso del rótulo
        l.pintar(l.caja(u0 - 0.04, v0 - 0.03, u1 + 0.04, v0), PIEDRA)  # repisa
        if "lejos" in nombre:
            l.pintar(l.caja(u0, v0, u1, v1), MADERA_OSC)
            l.pintar(l.caja(u0 + 0.02, v0 + 0.02, u1 - 0.02, v1 - 0.17), CRISTAL)
            l.em = np.maximum(l.em, l.caja(u0 + 0.02, v0 + 0.02, u1 - 0.02, v1 - 0.17) * 0.5)
            l.pintar(l.caja(u0, v1 - 0.17, u1, v1), "#C2413A")  # toldo visto de frente
    if "entramado" in nombre:
        b = 0.055
        oscuro = MADERA_OSC
        l.pintar(l.caja(0, 0, 1, b) | l.caja(0, 1 - b, 1, 1) | l.caja(0, 0, b, 1) | l.caja(1 - b, 0, 1, 1), oscuro)

        def diagonal(x0, y0, x1, y1, w=0.04):
            dx, dy = x1 - x0, y1 - y0
            t = np.clip(((l.U - x0) * dx + (l.V - y0) * dy) / (dx * dx + dy * dy), 0, 1)
            d = np.hypot(l.U - x0 - t * dx, (l.V - y0 - t * dy) * H / M)
            return d < w

        if "ventana" in nombre:
            u0, v0, u1, v1 = VENTANA
            l.pintar(diagonal(0.05, 0.05, u0 - 0.2, v0 - 0.04) | diagonal(0.95, 0.05, u1 + 0.2, v0 - 0.04), oscuro)
            l.pintar(l.caja(u0 - 0.05, v0 - 0.05, u1 + 0.05, v0) | l.caja(u0 - 0.05, v1, u1 + 0.05, v1 + 0.05), oscuro)
            if "lejos" in nombre:
                _ventana_pintada(l, *VENTANA, contraventanas="#5E8268")
        else:
            l.pintar(diagonal(0.05, 0.05, 0.5, 0.95) | diagonal(0.95, 0.05, 0.5, 0.95), oscuro)
            l.pintar(l.caja(0.5 - b / 2, 0, 0.5 + b / 2, 1), oscuro)
    return l


def hastial():
    l = Lienzo(5)
    _yeso(l)
    # óculo de piedra con cristal, en el centro de la parte alta del triángulo
    d = np.hypot((l.U - 0.5) * 1.6, (l.V - 0.42) * 1.0)
    l.pintar(d < 0.13, PIEDRA)
    l.pintar(d < 0.09, CRISTAL)
    l.em = np.maximum(l.em, (d < 0.09) * 0.5)
    l.pintar((d < 0.09) & (np.abs(l.U - 0.5) < 0.006), MADERA_OSC)
    return l


def sillares(lejos=False):
    """Sillares de esquina alternos (opacos) sobre yeso teñible: una cara de la esquina de un piso (1,9 × 10)."""
    l = Lienzo(6)
    _yeso(l)
    alto = 1.0 / 8
    for k in range(8):
        ancho = 1.0 if k % 2 == 0 else 1.05 / 1.9
        l.pintar(l.caja(0, k * alto + 0.006, ancho, (k + 1) * alto - 0.006), PIEDRA)
        l.pintar(l.caja(0, k * alto, ancho, k * alto + 0.006), "#000000", 0.25)
        if not lejos:
            l.pintar(l.caja(0, (k + 1) * alto - 0.02, ancho, (k + 1) * alto - 0.006), "#FFFFFF", 0.25)
    return l


# -------------------------------------------------------------------------------- tejados


def teja(hiladas, lejos=False):
    """Tejas teñibles: juntas y sombras semitransparentes sobre el color del tejado."""
    l = Lienzo(7 + hiladas)
    tejas_fila = 4
    fila = np.floor(l.V * hiladas)
    dentro_v = (l.V * hiladas) % 1.0
    desfase = (fila % 2) * 0.5
    col = np.floor(l.U * tejas_fila + desfase)
    # tono por teja (aleatorio, estable)
    tono = np.sin(fila * 12.9898 + col * 78.233) * 43758.5453
    tono = tono - np.floor(tono)
    l.pintar(np.clip((tono - 0.6) * 2.5, 0, 1), "#FFFFFF", 0.16)
    l.pintar(np.clip((0.4 - tono) * 2.5, 0, 1), "#000000", 0.18)
    # sombra en lo alto de cada hilada (bajo la teja de encima) y borde inferior marcado (goterón)
    l.pintar(np.clip((dentro_v - 0.65) / 0.35, 0, 1), "#000000", 0.35)
    l.pintar(dentro_v < 0.08, "#000000", 0.55 if not lejos else 0.35)
    l.pintar((dentro_v >= 0.08) & (dentro_v < 0.16), "#FFFFFF", 0.18)
    junta = ((l.U * tejas_fila + desfase) % 1.0) < 0.05
    l.pintar(junta, "#000000", 0.35 if not lejos else 0.2)
    return l


def cumbrera():
    l = Lienzo(9)
    seg = (l.U * 5) % 1.0
    l.pintar(seg < 0.08, "#000000", 0.45)
    l.pintar(np.clip(1 - np.abs(l.V - 0.5) * 2, 0, 1) ** 2, "#FFFFFF", 0.2)
    return l


# -------------------------------------------------------------------------------- piezas de fachada


def ventana_casilla():
    """El fondo del hueco de ventana: marco, cristal y cruceta (opaco)."""
    l = Lienzo(10)
    l.pintar(1.0, MADERA_OSC)
    m = 0.08
    l.pintar(l.caja(m, m, 1 - m, 1 - m), CRISTAL)
    l.em = np.maximum(l.em, l.caja(m, m, 1 - m, 1 - m) * 0.5)
    # reflejo diagonal en el cristal
    l.pintar(l.caja(m, m, 1 - m, 1 - m) & (np.abs((l.U - l.V * 0.7) - 0.15) < 0.06), "#9FB6CC", 0.35)
    l.pintar(l.caja(0.47, 0, 0.53, 1) | l.caja(0, 0.6, 1, 0.65), MADERA_OSC)
    l.pintar(l.caja(0, 0, 1, 0.025), "#000000", 0.3)
    return l


def escaparate_casilla():
    l = Lienzo(11)
    l.pintar(1.0, MADERA_OSC)
    l.pintar(l.caja(0.03, 0.04, 0.97, 0.75), CRISTAL)
    l.em = np.maximum(l.em, l.caja(0.03, 0.04, 0.97, 0.75) * 0.5)
    for x in (0.333, 0.666):
        l.pintar(l.caja(x - 0.012, 0.04, x + 0.012, 0.97), MADERA_OSC)
    l.pintar(l.caja(0.03, 0.78, 0.97, 0.95), "#C9DCE6", 0.5)  # montante
    l.pintar(l.caja(0.03, 0.04, 0.97, 0.75) & (np.abs((l.U - l.V * 0.5) - 0.3) < 0.05), "#9FB6CC", 0.3)
    return l


def contraventana():
    """Contraventana teñible: lamas (sombras) sobre el color de la instancia; marco claro."""
    l = Lienzo(12)
    for k in range(9):
        v0 = 0.06 + k * 0.1
        l.pintar(l.caja(0.1, v0, 0.9, v0 + 0.035), "#000000", 0.32)
        l.pintar(l.caja(0.1, v0 + 0.035, 0.9, v0 + 0.05), "#FFFFFF", 0.18)
    l.pintar(~l.caja(0.08, 0.04, 0.92, 0.96), "#000000", 0.2)
    return l


def puerta_casilla():
    """Puerta teñible: tablas, travesaños y tirador dorado."""
    l = Lienzo(13)
    for k in range(1, 5):
        l.pintar(np.abs(l.U - k / 5) < 0.008, "#000000", 0.35)
    l.pintar(l.caja(0, 0.2, 1, 0.26) | l.caja(0, 0.72, 1, 0.78), "#000000", 0.22)
    l.pintar(l.caja(0.78, 0.44, 0.86, 0.5), "#D2A64A")
    for k in range(5):  # vetas
        l.pintar(np.abs(((l.U * 5) % 1.0) - 0.3 - 0.05 * np.sin(l.V * 30 + k)) < 0.01, "#000000", 0.08)
    return l


def toldo():
    """Toldo teñible: franjas blancas opacas alternas con franjas del color de la instancia; festón oscurecido."""
    l = Lienzo(14)
    franja = np.floor(l.U * 8) % 2 == 1
    l.pintar(franja, "#F2EEE6")
    l.pintar(l.V < 0.05, "#000000", 0.25)
    return l


def cartel(emblema):
    l = Lienzo(INDICE["cartel_" + emblema])
    l.pintar(1.0, "#8A6340")
    l.pintar(l.caja(0.08, 0.08, 0.92, 0.92), "#E9DFC5")
    d = np.hypot(l.U - 0.5, l.V - 0.5)
    if emblema == "bolsa":
        l.pintar(np.hypot(l.U - 0.5, (l.V - 0.42) * 1.1) < 0.24, "#B48858")
        l.pintar(l.caja(0.42, 0.6, 0.58, 0.72), "#B48858")
        l.pintar(l.caja(0.38, 0.6, 0.62, 0.64), "#5C4130")
    elif emblema == "espada":
        l.pintar(l.caja(0.47, 0.32, 0.53, 0.82), "#C9CDD2")
        l.pintar(l.caja(0.36, 0.3, 0.64, 0.35), "#D2A64A")
        l.pintar(l.caja(0.47, 0.18, 0.53, 0.3), "#5C4130")
    elif emblema == "gema":
        l.pintar(np.abs(l.U - 0.5) * 1.4 + np.abs(l.V - 0.5) < 0.3, "#3F6FA8")
        l.pintar(np.abs(l.U - 0.45) * 1.4 + np.abs(l.V - 0.56) < 0.08, "#9FC3F0")
    elif emblema == "yunque":
        l.pintar(l.caja(0.25, 0.52, 0.75, 0.62) | l.caja(0.42, 0.3, 0.58, 0.52) | l.caja(0.32, 0.24, 0.68, 0.3),
                 "#3A3B40")
    elif emblema == "pan":
        l.pintar(np.hypot((l.U - 0.5) * 0.8, (l.V - 0.5) * 1.6) < 0.22, "#C99A55")
        for x in (0.42, 0.5, 0.58):
            l.pintar(np.abs(l.U - x - (l.V - 0.5) * 0.3) < 0.012, "#8A6340")
    elif emblema == "pocion":
        l.pintar(np.hypot(l.U - 0.5, l.V - 0.42) < 0.2, "#C8352E")
        l.pintar(l.caja(0.45, 0.58, 0.55, 0.74), "#9FB6CC")
    return l


def jardinera():
    """Jardinera: madera abajo y flores arriba (la cara de arriba y el frente usan la misma casilla)."""
    l = Lienzo(16)
    l.pintar(1.0, "#8A6340")
    l.pintar(l.V > 0.45, "#4E8A38")
    colores = ["#D9443A", "#F2A9C2", "#F2CF45", "#F5F2EA", "#A98BD6"]
    for k in range(26):
        cx, cy = l.rng.uniform(0.05, 0.95), l.rng.uniform(0.5, 0.97)
        l.pintar(np.hypot(l.U - cx, l.V - cy) < 0.045, colores[k % len(colores)])
    for y in (0.15, 0.3):
        l.pintar(np.abs(l.V - y) < 0.01, "#000000", 0.25)
    return l


# -------------------------------------------------------------------------------- opacos con dibujo


def sillar_muro():
    l = _opaco("#A2998A", 0.04, 17)
    hf = 1 / 4
    fila = np.floor(l.V / hf)
    desfase = (fila % 2) * 0.17
    l.pintar(((l.V % hf) < 0.02) | (((l.U + desfase) % 0.34) < 0.02), "#7A746B")
    return l


def ladrillo():
    l = _opaco("#A65A3E", 0.06, 18)
    hf = 1 / 10
    fila = np.floor(l.V / hf)
    desfase = (fila % 2) * 0.12
    l.pintar(((l.V % hf) < 0.015) | (((l.U + desfase) % 0.24) < 0.015), "#D8CBB8")
    return l


def tablon():
    """Tablón de misiones: tablero de madera con papeles clavados."""
    l = _opaco("#8A6340", 0.05, 19, vetas=True)
    for k in range(9):
        cx, cy = l.rng.uniform(0.15, 0.85), l.rng.uniform(0.2, 0.8)
        w, h = l.rng.uniform(0.09, 0.14), l.rng.uniform(0.11, 0.16)
        col = "#F4EEDC" if k % 3 else "#EFD98A"
        l.pintar(l.caja(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2), col)
        for j in range(3):
            l.pintar(l.caja(cx - w / 2 + 0.015, cy + h / 2 - 0.04 - j * 0.03, cx + w / 2 - 0.02,
                            cy + h / 2 - 0.035 - j * 0.03), "#8A7F70")
        l.pintar(np.hypot(l.U - cx, l.V - cy - h / 2 + 0.015) < 0.012, "#C8352E")
    return l


def reloj():
    l = Lienzo(20)
    d = np.hypot(l.U - 0.5, l.V - 0.5)
    l.pintar(d < 0.5, "#D2A64A")
    l.pintar(d < 0.43, "#F4EEDC")
    a = np.arctan2(l.V - 0.5, l.U - 0.5)
    marcas = (np.abs(((a / (2 * math.pi) * 12) % 1.0) - 0.5) > 0.45) & (d > 0.33) & (d < 0.4)
    l.pintar(marcas, "#2E2F33")
    l.pintar((np.abs(l.U - 0.5) < 0.015) & (l.V > 0.5) & (l.V < 0.75), "#2E2F33")
    l.pintar((np.abs(l.V - 0.5) < 0.012) & (l.U > 0.5) & (l.U < 0.84), "#2E2F33")
    l.pintar(d >= 0.5, "#E9DFC5")
    return l  # (reloj)


def vela():
    """Aspa de molino: celosía de madera y lona."""
    l = _opaco("#EDE3CC", 0.05, 21)
    for k in range(10):
        l.pintar(np.abs(l.V - k / 9) < 0.018, "#8A6340")
    l.pintar((l.U < 0.06) | (l.U > 0.94), "#8A6340")
    l.pintar((l.U < 0.06), "#5C4130")
    return l


def hojas(color, semilla):
    l = _opaco(color, 0.0, semilla)
    for k in range(60):
        cx, cy = l.rng.uniform(0, 1, 2)
        r = l.rng.uniform(0.04, 0.09)
        claro = l.rng.uniform() > 0.5
        l.pintar(np.hypot(l.U - cx, l.V - cy) < r, "#FFFFFF" if claro else "#000000", 0.12)
    return l


def flores():
    l = _opaco("#5C9A3B", 0.04, 22)
    colores = ["#D9443A", "#F2CF45", "#F5F2EA", "#A98BD6", "#F2A9C2"]
    for k in range(40):
        cx, cy = l.rng.uniform(0, 1, 2)
        l.pintar(np.hypot(l.U - cx, l.V - cy) < 0.05, colores[k % 5])
    return l


def surcos(base, surco, semilla):
    l = _opaco(base, 0.06, semilla)
    l.pintar(((l.U * 6) % 1.0) < 0.3, surco, 0.7)
    return l


def corteza(color, semilla, abedul=False):
    l = _opaco(color, 0.08, semilla)
    if abedul:
        for k in range(10):
            cx, cy = l.rng.uniform(0, 1, 2)
            l.pintar(l.caja(cx - 0.06, cy - 0.015, cx + 0.06, cy + 0.015), "#3A3530")
    else:
        l.pintar(((l.U * 7 + 0.3 * np.sin(l.V * 20)) % 1.0) < 0.2, "#000000", 0.25)
    return l


def silueta_fachada():
    """Fachada lejana OPACA (para la silueta de Aurora, que es una sola malla sin color de instancia): yeso crema con
    dos pisos de ventanas."""
    l = _opaco("#EADCC0", 0.05, 60)
    for fila in range(2):
        for k in range(4):
            u0 = 0.06 + k * 0.24
            v0 = 0.12 + fila * 0.5
            l.pintar(l.caja(u0, v0, u0 + 0.12, v0 + 0.22), "#3A4A5C")
            l.pintar(l.caja(u0 - 0.03, v0, u0, v0 + 0.22) | l.caja(u0 + 0.12, v0, u0 + 0.15, v0 + 0.22), "#5E8268")
    l.pintar(l.V < 0.06, "#A2998A")
    return l


def silueta_teja():
    l = _opaco("#B04A30", 0.06, 61)
    l.pintar(((l.V * 8) % 1.0) < 0.12, "#000000", 0.3)
    return l


def casilla(nombre):
    """El lienzo pintado de una casilla."""
    if nombre.startswith(("pared_", "entramado_")):
        return pared(nombre)
    fijos = {
        "piedra_clara": lambda: _opaco("#CBC1B0", 0.05, 30), "piedra_media": lambda: _opaco("#A2998A", 0.06, 31),
        "piedra_oscura": lambda: _opaco("#6F6A62", 0.06, 32),
        "madera_clara": lambda: _opaco("#B48858", 0.04, 33, vetas=True),
        "madera_media": lambda: _opaco("#8A6340", 0.04, 34, vetas=True),
        "madera_oscura": lambda: _opaco("#5C4130", 0.04, 35, vetas=True),
        "hierro": lambda: _opaco("#2E2F33", 0.03, 36), "oro": lambda: _opaco("#D2A64A", 0.04, 37),
        "vidrio": lambda: _opaco(CRISTAL, 0.02, 38), "luz": lambda: _opaco("#FFC46E", 0.0, 39),
        "agua": lambda: _opaco("#5B9AA6", 0.03, 40),
        "hoja_verde": lambda: hojas("#5C9A3B", 41), "hoja_clara": lambda: hojas("#86B846", 42),
        "hoja_oscura": lambda: hojas("#3E7838", 43), "hoja_pino": lambda: hojas("#3B6A3F", 44),
        "flor_rosa": lambda: hojas("#F2A9C2", 45), "corteza": lambda: corteza("#6B4E37", 46),
        "abedul": lambda: corteza("#E7E2D6", 47, abedul=True), "hierba": lambda: _opaco("#73A845", 0.05, 48),
        "flores": flores, "trigo": lambda: surcos("#DDB65A", "#B89645", 49), "col": lambda: hojas("#7DB06A", 50),
        "tierra_arada": lambda: surcos("#7A5A3E", "#5E432D", 51), "calabaza": lambda: _opaco("#E08A2E", 0.05, 52),
        "fruta": flores, "paja": lambda: surcos("#D6B663", "#B89645", 53),
        "silueta_fachada": silueta_fachada, "silueta_teja": silueta_teja,
        "sillar_muro": sillar_muro, "ladrillo": ladrillo, "tablon": tablon, "reloj": reloj, "vela": vela,
        "hastial": hastial, "sillares": sillares,
        "teja_16": lambda: teja(8), "teja_24": lambda: teja(11), "teja_lejos": lambda: teja(8, lejos=True),
        "cumbrera": cumbrera, "ventana": ventana_casilla, "escaparate": escaparate_casilla,
        "contraventana": contraventana, "puerta": puerta_casilla, "toldo": toldo, "jardinera": jardinera,
    }
    if nombre.startswith("cartel_"):
        return cartel(nombre.split("_", 1)[1])
    return fijos[nombre]()


BRILLO = {"vidrio": 1.0, "agua": 1.0, "hierro": 0.5, "oro": 0.7}


def generar(carpeta):
    """Pinta el atlas (RGBA) y su mapa de datos (RGB) con la misma distribución:
      R = luz propia: 0,5 en los cristales (se encienden al atardecer), 1 en los faroles (siempre algo encendidos);
      G = brillo (1 = liso y reflectante: cristal, agua; 0 = mate).
    El mapa de datos solo lo usan los renders de Blender; en Roblox bastaría el atlas (o una SurfaceAppearance con
    RoughnessMap si se quiere el brillo). Devuelve (ruta_atlas, ruta_datos)."""
    img = np.zeros((TAM, TAM, 4), np.float32)
    datos = np.zeros((TAM, TAM, 3), np.float32)
    for i, nombre in enumerate(CASILLAS):
        l = casilla(nombre)
        col, fila = i % N, i // N
        sl = (slice(fila * CASILLA, (fila + 1) * CASILLA), slice(col * CASILLA, (col + 1) * CASILLA))
        img[sl] = l.imagen()
        em = np.full(l.em.shape, 1.0) if nombre == "luz" else l.em
        datos[sl + (0,)] = em
        datos[sl + (1,)] = np.maximum(BRILLO.get(nombre, 0.0), (l.em > 0.25) * 1.0 if nombre != "luz" else 0.0)
    os.makedirs(carpeta, exist_ok=True)
    ra = os.path.join(carpeta, "atlas_kit.png")
    rd = os.path.join(carpeta, "atlas_kit_datos.png")
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(ra, optimize=True)
    Image.fromarray((datos * 255 + 0.5).astype(np.uint8), "RGB").save(rd, optimize=True)
    return ra, rd


if __name__ == "__main__":
    import sys

    print(generar(sys.argv[1] if len(sys.argv) > 1 else "."))
