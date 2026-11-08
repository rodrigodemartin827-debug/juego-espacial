"""
Atlas de texturas del kit: UNA imagen de 1024 × 1024 compartida por todas las piezas, una máscara de emisión con la
misma distribución (para las ventanas y faroles encendidos en los renders) y sus mapas PBR.

Por qué un atlas: el detalle pequeño (tejas, sillares, marcos, contraventanas, tablas) pasa de la geometría a la
textura, y todas las piezas usan la misma imagen: en Roblox se sube una vez y la comparten todas las MeshPart.

Casillas de 128 × 128 píxeles (8 × 8 = 64). Cada casilla se pinta aquí con numpy, en coordenadas (u, v) de 0 a 1 con
la v hacia arriba (como en las UV). La distribución (orden de CASILLAS, rect_uv, MARGEN_UV) NO se puede cambiar: las
piezas 3D ya tienen las UV apuntando a esas casillas.

TINTE: las superficies que cambian de color de un edificio a otro (yeso, tejas, contraventanas, puertas, toldos) son
TRANSPARENTES en el atlas (alfa 0) o semitransparentes donde llevan dibujo (juntas de tejas, lamas...). El color de
cada instancia (MeshPart.Color en Roblox, con SurfaceAppearance AlphaMode = Overlay; el color del objeto en Blender) se
ve a través. Así UNA pieza sirve para todos los colores. Las casillas opacas (piedra, madera, hierro, cristal...)
ignoran el color de la instancia. Por eso, en las teñibles el desgaste se pinta SOLO como capas semitransparentes
oscuras o claras (suciedad, humedad, grietas, vetas, descascarillado), que funcionan sobre cualquier color de base.

VERSIÓN «SIN PLÁSTICO» (lo que se añadió):
  * Ruido propio, determinista y PERIÓDICO por casilla (vruido / fbm: ruido de valor con interpolación quíntica y
    varias octavas; la red de valores se repite con el periodo de la casilla). Así las casillas que se repiten en la
    geometría (paredes de 8 studs, tejados, muros) siguen encajando por los bordes y no hay costuras.
  * Aparejos (aparejo()) con juntas irregulares: cada sillar/ladrillo/teja tiene su tono, su desplazamiento y su
    distancia al borde (para biselar y para los golpes en las aristas).
  * Materiales: yeso con manchas, poros, chorretones bajo las ventanas, humedad que sube del zócalo y grietas que
    salen de las esquinas de los huecos; piedra con granos, motas, golpes y musgo en la base; tejas con relieve de
    canal, tonos distintos, alguna rota o desplazada y líquenes; madera con anillos, fibras, nudos y fisuras en la
    dirección de la pieza; hierro con óxido, chorreones y arañazos; oro con pátina; hojas, hierba y cultivos hechos de
    formas (hojas, briznas, espigas) en vez de color plano.
  * Cada casilla lleva, además del color, un campo de ALTURA (alt), RUGOSIDAD (rug) y METALIDAD (met) coherentes con lo
    pintado. De ahí salen los mapas PBR.

MAPAS PBR (misma distribución, 1024 × 1024), que genera generar() junto al atlas:
  * atlas_kit_normal.png: mapa de normales en espacio tangente, convención OpenGL (Y+ = verde hacia arriba en la v),
    que es la que espera SurfaceAppearance.NormalMap. Sale del gradiente del campo de altura (suavizado 3 × 3) por
    la FUERZA de cada casilla.
  * atlas_kit_roughness.png: rugosidad en gris (piedra, yeso y teja altas; madera media; hierro, oro, cristal y agua
    bajas con variación).
  * atlas_kit_metalness.png: metalidad en gris (solo hierro y oro: la casilla de hierro y la de oro, y los herrajes de
    hierro u oro pintados en otras casillas: clavos, pernios, tirador y aro del reloj; el resto 0).

Cómo se regenera todo (desde la carpeta de la región, con un Python que tenga numpy y Pillow; el de Blender sirve
añadiendo Pillow al PYTHONPATH):
    python herramientas/atlas.py texturas
Escribe texturas/atlas_kit.png, atlas_kit_datos.png, atlas_kit_normal.png, atlas_kit_roughness.png y
atlas_kit_metalness.png. Es determinista: mismas semillas, mismo resultado.
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
# Ruido (determinista y periódico)
# ==============================================================================================================


def _hash(ix, iy, s):
    """Número pseudoaleatorio en [0, 1) para cada par de enteros (ix, iy) y semilla s (estable entre ejecuciones)."""
    ix = np.asarray(ix, np.int64)
    iy = np.asarray(iy, np.int64)
    h = (ix * 374761393 + iy * 668265263 + (int(s) % 1000003) * 1442695041) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    h = h ^ (h >> 16)
    return (h & 0xFFFFFF).astype(np.float32) / np.float32(0x1000000)


def vruido(x, y, s, px=0, py=0):
    """Ruido de valor (0..1) con interpolación quíntica. Si px/py > 0, la red se repite con ese periodo (entero)."""
    x = np.asarray(x, np.float64)
    y = np.asarray(y, np.float64)
    xf, yf = np.floor(x), np.floor(y)
    fx, fy = x - xf, y - yf
    xi, yi = xf.astype(np.int64), yf.astype(np.int64)
    px, py = int(round(px)), int(round(py))

    def h(a, b):
        if px:
            a = np.mod(a, px)
        if py:
            b = np.mod(b, py)
        return _hash(a, b, s)

    ux = fx * fx * fx * (fx * (fx * 6 - 15) + 10)
    uy = fy * fy * fy * (fy * (fy * 6 - 15) + 10)
    a, b, c, d = h(xi, yi), h(xi + 1, yi), h(xi, yi + 1), h(xi + 1, yi + 1)
    return (a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy).astype(np.float32)


def fbm(x, y, s, octavas=4, px=0, py=0, gan=0.5):
    """Suma de octavas de vruido, centrada en 0 (aprox. -1..1, la mayoría entre -0,5 y 0,5)."""
    tot = 0.0
    amp = 1.0
    norma = 0.0
    for o in range(octavas):
        f = 2 ** o
        tot = tot + amp * vruido(x * f, y * f, s + o * 7919, px * f, py * f)
        norma += amp
        amp *= gan
    return ((tot / norma) * 2 - 1) * 1.6


def _ss(e0, e1, x):
    """smoothstep."""
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def _hex(h):
    h = h.lstrip("#")
    return np.array([int(h[i: i + 2], 16) for i in (0, 2, 4)], np.float32) / 255.0


def _col(c):
    return _hex(c) if isinstance(c, str) else np.asarray(c, np.float32)


def _segmento(U, V, x0, y0, x1, y1):
    """Distancia de cada punto al segmento (x0, y0)-(x1, y1) y posición t (0..1) a lo largo."""
    dx, dy = x1 - x0, y1 - y0
    t = np.clip(((U - x0) * dx + (V - y0) * dy) / max(dx * dx + dy * dy, 1e-12), 0, 1)
    return np.hypot(U - x0 - t * dx, V - y0 - t * dy), t


# ==============================================================================================================
# Lienzo
# ==============================================================================================================


class Lienzo:
    """Una casilla RGBA en coordenadas (u, v) de 0 a 1 (v hacia arriba), su máscara de emisión y sus canales PBR:
    alt (altura 0..1, para el mapa de normales), rug (rugosidad) y met (metalidad)."""

    def __init__(self, semilla=0, rug=0.85, fuerza=3.0):
        s = CASILLA
        g = (np.arange(s) + 0.5) / s
        self.U, self.V = np.meshgrid(g, g[::-1])
        self.U = self.U.astype(np.float32)
        self.V = self.V.astype(np.float32)
        self.rgba = np.zeros((s, s, 4), np.float32)
        self.em = np.zeros((s, s), np.float32)
        self.alt = np.full((s, s), 0.5, np.float32)
        self.rug = np.full((s, s), rug, np.float32)
        self.met = np.zeros((s, s), np.float32)
        self.fuerza = fuerza
        self.rng = np.random.default_rng(semilla)
        self.s = semilla * 7919 + 13

    def pintar(self, mascara, color, alfa=1.0, rug=None, met=None):
        """Composición «sobre»: el color (hex, RGB o un array (128, 128, 3)) encima de lo que hay, con la cobertura de
        la máscara (bool o 0..1) por alfa. Si se da rug/met, también se mezclan en esa cobertura."""
        m = np.asarray(mascara, np.float32) * alfa
        if m.ndim == 0:
            m = np.full(self.U.shape, float(m), np.float32)
        c = _col(color)
        if c.ndim == 1:
            c = c[None, None, :]
        a0 = self.rgba[..., 3]
        a = m + a0 * (1 - m)
        rgb = (c * m[..., None] + self.rgba[..., :3] * (a0 * (1 - m))[..., None]) / np.maximum(a[..., None], 1e-6)
        self.rgba[..., :3] = rgb
        self.rgba[..., 3] = a
        if rug is not None:
            self.rug += (rug - self.rug) * m
        if met is not None:
            self.met += (met - self.met) * m

    def altura(self, mascara, valor):
        """Mezcla la altura hacia `valor` (escalar o array) con la cobertura de la máscara."""
        m = np.asarray(mascara, np.float32)
        self.alt += (valor - self.alt) * m

    def f(self, cu, cv=None, k=0, oct=4, gan=0.5):
        """fbm periódico en la casilla con cu × cv celdas (enteros) y semilla propia + k."""
        cv = cu if cv is None else cv
        return fbm(self.U * cu, self.V * cv, self.s + k * 131, oct, cu, cv, gan)

    def r(self, cu, cv=None, k=0):
        """Ruido de valor periódico (0..1) de una octava."""
        cv = cu if cv is None else cv
        return vruido(self.U * cu, self.V * cv, self.s + k * 131 + 7, cu, cv)

    def caja(self, u0, v0, u1, v1):
        return (self.U >= u0) & (self.U < u1) & (self.V >= v0) & (self.V < v1)

    def dist_caja(self, u0, v0, u1, v1, su=8.0, sv=10.0):
        """Distancia (en studs) de cada punto al borde de la caja; negativa fuera."""
        return np.minimum(np.minimum(self.U - u0, u1 - self.U) * su, np.minimum(self.V - v0, v1 - self.V) * sv)

    def imagen(self):
        return np.clip(self.rgba, 0, 1)


# ==============================================================================================================
# Pinceles de materiales
# ==============================================================================================================


def aparejo(l, filas, por_fila, k=0, v0=0.0, v1=1.0, desfase=0.5, jit=0.2, alabeo=0.005, su=8.0, sv=10.0):
    """Aparejo de piezas (sillares, ladrillos) en filas, con las juntas verticales desplazadas al azar en cada pieza y
    un leve alabeo de todas las juntas. Periódico en u (y en v si filas es par y v0..v1 = 0..1).
    Devuelve (d, ident, fila, col, fu, fv): d = distancia al borde de la pieza en studs, ident = 0..1 por pieza,
    fu/fv = posición dentro de la pieza (0..1)."""
    U = l.U + l.f(4, k=k + 11, oct=2) * alabeo
    V = l.V + l.f(4, k=k + 12, oct=2) * alabeo
    y = (V - v0) / (v1 - v0) * filas
    r = np.floor(y)
    fy = y - r
    ri = r.astype(np.int64)
    x = U * por_fila - desfase * np.mod(ri, 2)
    c = np.floor(x).astype(np.int64)

    def borde(cc):
        return cc + (_hash(np.mod(ri, filas), np.mod(cc, por_fila), l.s + k + 13) - 0.5) * jit

    c = np.where(x < borde(c), c - 1, c)
    c = np.where(x >= borde(c + 1), c + 1, c)
    izq, der = borde(c), borde(c + 1)
    du = np.minimum(x - izq, der - x) / por_fila * su
    dv = np.minimum(fy, 1 - fy) * (v1 - v0) / filas * sv
    ident = _hash(np.mod(ri, filas), np.mod(c, por_fila), l.s + k + 17)
    return np.minimum(du, dv), ident, ri, c, (x - izq) / (der - izq), fy


def piedra(l, mascara, base, d, ident, k=0, var=0.09, bisel=0.18, golpes=1.0, rug=0.9, relieve=0.4):
    """Piedra opaca dentro de `mascara`: tono por pieza, motas, granos claros y oscuros, arista biselada con golpes.
    d = distancia al borde de la pieza (studs), ident = 0..1 por pieza."""
    m = np.asarray(mascara, np.float32)
    b = _col(base)
    i2 = (ident * 7.31 + 0.27) % 1.0
    tono = 1 + (ident - 0.5) * 2 * var
    calido = (i2 - 0.5) * 0.07
    motas = l.f(5, k=k + 1) * 0.05 + l.f(13, k=k + 2) * 0.04 + l.f(32, k=k + 3, oct=2) * 0.03
    col = b[None, None, :] * (tono * (1 + motas))[..., None]
    col[..., 0] *= 1 + calido
    col[..., 2] *= 1 - calido
    g1, g2 = l.r(64, k=k + 4), l.r(64, k=k + 5)
    col *= (1 - 0.16 * _ss(0.8, 0.93, g1))[..., None]
    col += (1 - col) * (0.12 * _ss(0.82, 0.95, g2))[..., None]
    # golpes: la arista se come hacia dentro donde el ruido es alto
    gr = np.clip(l.f(9, k=k + 6), 0, 1)
    golpe = d < bisel * (0.25 + 1.6 * golpes * gr * gr)
    e = _ss(0.0, bisel, d)
    col *= (0.82 + 0.18 * e)[..., None]
    col *= np.where(golpe, 0.88, 1.0)[..., None]
    l.pintar(m, col, rug=np.clip(rug + motas * 0.6, 0, 1), met=0.0)
    h = 0.3 + relieve * e + motas * 0.8 - golpe * 0.12
    l.altura(m, h)


def mortero(l, mascara, color="#8E877B", k=0, alt=0.15):
    """Junta de mortero: rehundida, arenosa y con tono irregular."""
    m = np.asarray(mascara, np.float32)
    n = l.f(10, k=k + 21) * 0.08 + l.f(40, k=k + 22, oct=2) * 0.06
    col = _col(color)[None, None, :] * (1 + n)[..., None]
    l.pintar(m, col, rug=0.95)
    l.altura(m, alt + n)


def veta(a, b, s, anillos=8, alabeo=0.3, pa=0, pb=0, nudos=()):
    """Madera: devuelve (oscuro, fibras) en 0..1. a = coordenada a lo largo de la fibra, b = de través.
    pa/pb = periodos (enteros) de la casilla en a y b si la madera tiene que repetirse; nudos = [(a, b, radio)].
    El alabeo cambia despacio a lo largo de la fibra (vetas largas y casi rectas, no curvas de nivel)."""
    w = fbm(a * 1, b * 2, s, 3, pa, 2 * pb) * alabeo + fbm(a * 3, b * 6, s + 3, 2, 3 * pa, 6 * pb) * 0.08
    r = b * anillos + w * anillos * 0.25
    for (na, nb, nr) in nudos:
        dn = np.hypot((a - na) / (nr * 2.6), (b - nb) / nr)
        r = r + 1.8 * np.exp(-dn * dn) * np.sign(b - nb + 1e-6)
    anillo = r - np.floor(r)
    oscuro = _ss(0.5, 0.9, anillo) * (1 - _ss(0.9, 1.0, anillo)) * (0.6 + 0.4 * vruido(a * 2, b * anillos, s + 4, 2 * pa, anillos * pb))
    fibras = vruido(a * 4, b * 96, s + 9, 4 * pa, 96 * pb)
    for (na, nb, nr) in nudos:
        dn = np.hypot((a - na) / (nr * 1.2), (b - nb) / (nr * 0.9))
        oscuro = np.maximum(oscuro, _ss(0.6, 0.2, dn))
    return oscuro, fibras


def fisuras(a, b, s, densidad=0.02, pa=0, pb=0):
    """Fisuras finas a lo largo de la fibra (0..1)."""
    f = fbm(a * 2, b * 24, s, 2, 2 * pa, 24 * pb)
    largo = fbm(a * 3, b * 2, s + 5, 2, 3 * pa, 2 * pb)
    return _ss(densidad, 0.0, np.abs(f)) * _ss(0.15, 0.45, largo)


def madera(l, mascara, base, a, b, k=0, anillos=8, contraste=0.28, nudos=(), pa=0, pb=0, grietas=True,
           rug=0.62, relieve=0.18, alt0=0.5):
    """Madera opaca dentro de `mascara`, con la fibra a lo largo de `a`."""
    m = np.asarray(mascara, np.float32)
    os_, fi = veta(a, b, l.s + k, anillos, pa=pa, pb=pb, nudos=nudos)
    tono = 1 - contraste * os_ - 0.12 * (fi - 0.5) + l.f(3, k=k + 31, oct=2) * 0.05
    col = _col(base)[None, None, :] * tono[..., None]
    if grietas:
        g = fisuras(a, b, l.s + k + 50, pa=pa, pb=pb)
        col *= (1 - 0.55 * g)[..., None]
    else:
        g = 0.0
    l.pintar(m, col, rug=np.clip(rug + 0.12 * os_ - 0.05 * fi, 0, 1), met=0.0)
    l.altura(m, alt0 + relieve * (0.5 - os_) * 0.5 + 0.05 * fi - 0.25 * g)


def veladura_madera(l, mascara, a, b, k=0, alfa=0.14, anillos=7, pa=0, pb=0, nudos=()):
    """Vetas de madera SEMITRANSPARENTES (para lo teñible: puerta, contraventana): solo oscurecen."""
    m = np.asarray(mascara, np.float32)
    os_, fi = veta(a, b, l.s + k, anillos, pa=pa, pb=pb, nudos=nudos)
    l.pintar(m * np.clip(os_ * 0.8 + (fi - 0.4) * 0.5, 0, 1), "#1E140C", alfa)
    g = fisuras(a, b, l.s + k + 50, pa=pa, pb=pb)
    l.pintar(m * g, "#140D08", 0.45)
    l.altura(m, l.alt - 0.06 * os_ - 0.2 * g)


# -------------------------------------------------------------------------------- desgaste teñible


def manchas(l, k=0, oscuro=0.13, claro=0.08, escala=3, color_osc="#2B2017"):
    """Variación tonal grande y media (semitransparente): sirve sobre cualquier tinte."""
    t = l.f(escala, k=k + 41) * 0.6 + l.f(escala * 3, k=k + 42) * 0.3 + l.f(escala * 9, k=k + 43, oct=2) * 0.1
    l.pintar(np.clip(t * 1.6, 0, 1), color_osc, oscuro)
    l.pintar(np.clip(-t * 1.6, 0, 1), "#FFFFFF", claro)
    return t


def chorretones(l, mascara, k=0, alfa=0.16, finos=14):
    """Chorretones verticales de agua sucia (más fuertes arriba de la máscara, que ya trae el degradado)."""
    s = l.f(finos, 2, k=k + 51, oct=3)
    m = np.asarray(mascara, np.float32) * np.clip(0.4 + s * 1.2, 0, 1)
    l.pintar(m, "#231A12", alfa)


def grieta(l, x0, y0, angulo, largo, k=0, ancho=0.0035, alfa=0.55, ramas=1, su=1.0):
    """Grieta fina (paseo aleatorio) que empieza en (x0, y0). Oscura, semitransparente y rehundida."""
    rng = np.random.default_rng(l.s + k)
    total = np.zeros(l.U.shape, np.float32)
    trazos = [(x0, y0, angulo, largo, ancho)]
    hechos = 0
    while trazos and hechos < 1 + ramas:
        x, y, ang, lg, w = trazos.pop(0)
        pasos = 9
        for i in range(pasos):
            ang += rng.normal(0, 0.45)
            nx, ny = x + math.cos(ang) * lg / pasos / su, y + math.sin(ang) * lg / pasos
            d, _ = _segmento(l.U, l.V, x, y, nx, ny)
            wi = w * (1 - 0.7 * i / pasos)
            total = np.maximum(total, _ss(wi * 1.6, wi * 0.3, d))
            if i == 4 and hechos < ramas:
                trazos.append((nx, ny, ang + rng.choice([-0.9, 0.9]), lg * 0.45, w * 0.7))
            x, y = nx, ny
        hechos += 1
    l.pintar(total, "#100B07", alfa)
    l.altura(total, l.alt - 0.25)
    return total


# ==============================================================================================================
# Paredes
# ==============================================================================================================

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
VERDE_CONTRA = "#5E8268"


def _yeso(l, k=0, fuerte=1.0):
    """Yeso: transparente (tinte) con desgaste semitransparente: variación tonal, marcas de llana, poros, manchas de
    humedad con cerco y chorretones finos. Todo periódico (las paredes se repiten a lo ancho y a lo alto)."""
    l.rug[:] = 0.9
    t = manchas(l, k, 0.12 * fuerte, 0.08 * fuerte)
    # marcas de llana: trazos anchos y suaves, algo inclinados
    llana = fbm(l.U * 5 + l.V * 2, l.V * 14, l.s + k + 61, 2, 5, 14)
    l.pintar(np.clip(llana - 0.25, 0, 1), "#1F1810", 0.07 * fuerte)
    l.pintar(np.clip(-llana - 0.35, 0, 1), "#FFFFFF", 0.05 * fuerte)
    # poros y picados: puntitos escasos (no ruido de pantalla)
    poro = _ss(0.86, 0.96, l.r(48, k=k + 62))
    l.pintar(poro, "#1A130C", 0.22 * fuerte)
    # manchas de humedad con cerco más oscuro
    hm = l.f(4, k=k + 63)
    cerco = _ss(0.05, 0.0, np.abs(hm - 0.42))
    l.pintar(_ss(0.42, 0.7, hm), "#2A2116", 0.07 * fuerte)
    l.pintar(cerco, "#2A2116", 0.09 * fuerte)
    chorretones(l, np.ones_like(l.U), k + 64, 0.05 * fuerte, finos=16)
    medio = l.f(10, k=k + 65, oct=3)
    l.altura(1.0, 0.5 + 0.06 * medio + 0.03 * t - 0.12 * poro)
    l.rug += 0.04 * medio


def _humedad_baja(l, k=0):
    """Humedad que sube del zócalo: banda oscura de borde irregular con un cerco de salitre."""
    borde = ZOCALO_V + 0.07 + 0.05 * fbm(l.U * 4, 0.0 * l.U, l.s + k + 71, 3, 4, 0)
    dentro = _ss(borde + 0.01, borde - 0.04, l.V) * (l.V > ZOCALO_V)
    l.pintar(dentro, "#22190F", 0.16)
    cerco = _ss(0.012, 0.0, np.abs(l.V - borde)) * (l.V > ZOCALO_V)
    l.pintar(cerco, "#F4F0E6", 0.18)
    l.pintar(_ss(0.006, 0.0, np.abs(l.V - borde - 0.012)), "#22190F", 0.12)
    l.rug += 0.04 * dentro


def _desconchon(l, cx, cy, r, k=0, piedra_debajo="#B3A792"):
    """Desconchón: el yeso se ha caído y se ve la mampostería de debajo (opaca), con el canto del yeso claro y una
    sombra por debajo."""
    d = np.hypot((l.U - cx) * M, (l.V - cy) * H)
    forma = d + 0.35 * fbm(l.U * 12, l.V * 12, l.s + k + 81, 3, 12, 12) * r * 2.5
    hueco = forma < r * 2.5
    canto = (forma >= r * 2.5) & (forma < r * 2.5 + 0.09)
    # mampostería: piedras pequeñas irregulares con mortero
    dd, ident, *_ = aparejo(l, 14, 9, k=k + 82, jit=0.6, alabeo=0.01)
    piedra(l, hueco & (dd > 0.05), piedra_debajo, dd - 0.05, ident, k=k + 83, var=0.15, bisel=0.12, relieve=0.25)
    mortero(l, hueco & (dd <= 0.05), "#9A9180", k=k + 84, alt=0.2)
    l.pintar(hueco, "#000000", 0.18)  # está más hondo: algo más oscuro
    l.altura(hueco, l.alt - 0.25)
    l.pintar(canto, "#FFFFFF", 0.25)
    sombra = (forma < r * 2.5 + 0.18) & ~hueco & (l.V < cy)
    l.pintar(sombra & ~canto, "#000000", 0.1)


def _bloque(l, u0, v0, u1, v1, color=PIEDRA, k=0, bisel=0.16):
    """Una pieza de piedra rectangular (recercados, jambas, dinteles)."""
    d = l.dist_caja(u0, v0, u1, v1)
    piedra(l, d > 0, color, d, _hash(int(u0 * 977), int(v0 * 977), l.s + k) + np.zeros_like(d), k=k, bisel=bisel)
    # sombra que la pieza (que sobresale) arroja abajo y a la derecha sobre el yeso
    sombra = (l.dist_caja(u0 + 0.012, v0 - 0.015, u1 + 0.012, v1 - 0.015) > 0) & (d <= 0)
    l.pintar(sombra, "#000000", 0.22)


def _zocalo(l, k=0):
    """Banda de sillares en la parte baja (opaca), con verdín y salpicaduras de barro en el arranque."""
    z = l.V < ZOCALO_V
    d, ident, *_ = aparejo(l, 2, 5, k=k + 91, v1=ZOCALO_V, jit=0.25)
    junta = 0.06
    piedra(l, z & (d > junta), "#A2998A", d - junta, ident, k=k + 92)
    mortero(l, z & (d <= junta), "#7E786E", k=k + 93)
    verdin = _ss(0.09, 0.0, l.V) * np.clip(0.5 + l.f(6, k=k + 94) * 1.2, 0, 1) * z
    l.pintar(verdin, "#4D6232", 0.5, rug=0.95)
    barro = _ss(0.05, 0.0, l.V) * np.clip(0.3 + l.f(20, k=k + 95, oct=2) * 1.5, 0, 1) * z
    l.pintar(barro, "#3E3022", 0.45)
    # remate del zócalo: canto superior más claro y la sombra que deja sobre el yeso
    l.pintar(z & (l.V > ZOCALO_V - 0.012), "#FFFFFF", 0.12)
    l.pintar((l.V >= ZOCALO_V) & (l.V < ZOCALO_V + 0.02), "#000000", 0.18)


def _recercado(l, u0, v0, u1, v1, ancho=0.055, clave=True, dintel=0.05, k=0):
    """Recercado de piedra alrededor de un hueco: jambas de dos piezas, alféizar, dintel y clave; grietas que salen
    de las esquinas y chorretones bajo el alféizar."""
    # chorretones bajo el alféizar (antes que la piedra)
    bajo = (l.U > u0 - ancho) & (l.U < u1 + ancho) & (l.V < v0 - 0.04)
    caida = _ss(0.0, 0.35, l.V - (v0 - 0.4)) * bajo
    chorretones(l, caida, k + 101, 0.22, finos=24)
    vm = (v0 + v1) / 2
    for (a, b) in ((u0 - ancho, u0), (u1, u1 + ancho)):
        _bloque(l, a, v0, b, vm - 0.003, k=k + 102 + int(a * 50))
        _bloque(l, a, vm + 0.003, b, v1, k=k + 103 + int(a * 50))
    _bloque(l, u0 - ancho - 0.02, v0 - 0.04, u1 + ancho + 0.02, v0, "#BDB3A2", k=k + 104)  # alféizar
    _bloque(l, u0 - ancho, v1, u1 + ancho, v1 + dintel, k=k + 105)  # dintel
    if clave:
        _bloque(l, (u0 + u1) / 2 - 0.035, v1 - 0.01, (u0 + u1) / 2 + 0.035, v1 + dintel + 0.025, "#B8AE9C", k=k + 106)
    # grietas desde las esquinas del dintel y del alféizar
    grieta(l, u1 + ancho, v1 + dintel, 0.9, 0.16, k=k + 107, ramas=1)
    grieta(l, u0 - ancho - 0.02, v0 - 0.04, -2.3, 0.12, k=k + 108, ramas=0)


def _ventana_pintada(l, u0, v0, u1, v1, contraventanas=None, k=0):
    """Ventana completa pintada (para la versión lejana): marco, cristal, cruceta y contraventanas."""
    caja = l.caja(u0, v0, u1, v1)
    madera(l, caja, MADERA_OSC, l.V * 4, l.U * 6, k=k + 111, anillos=4, grietas=False)
    m = 0.02
    vid = l.caja(u0 + m, v0 + m, u1 - m, v1 - m)
    _cristal(l, vid, k + 112, v0 + m, v1 - m)
    l.em = np.maximum(l.em, vid * 0.5)
    um = (u0 + u1) / 2
    vm = v0 + (v1 - v0) * 0.62
    l.pintar(l.caja(um - 0.008, v0, um + 0.008, v1) | l.caja(u0, vm - 0.008, u1, vm + 0.008), MADERA_OSC)
    l.altura(l.caja(um - 0.008, v0, um + 0.008, v1) | l.caja(u0, vm - 0.008, u1, vm + 0.008), 0.55)
    if contraventanas:
        w = (u1 - u0) / 2 + 0.005
        for a, b in ((u0 - 0.065 - w, u0 - 0.065), (u1 + 0.065, u1 + 0.065 + w)):
            c = l.caja(a, v0 + 0.01, b, v1 - 0.01)
            col = _col(contraventanas)[None, None, :] * (1 + 0.06 * l.f(8, k=k + 113))[..., None]
            l.pintar(c, col, rug=0.8)
            l.altura(c, 0.6)
            for j in range(5):
                vv = v0 + 0.04 + j * (v1 - v0 - 0.06) / 5
                l.pintar(l.caja(a + 0.01, vv, b - 0.01, vv + 0.012), "#000000", 0.28)
            l.pintar(c & (l.V < v0 + 0.05), "#2A2016", 0.25)
            l.pintar(l.caja(b, v0, b + 0.01, v1 - 0.02), "#000000", 0.2)


def _cristal(l, mascara, k, v0=0.0, v1=1.0, reflejo=True):
    """Cristal viejo: azul oscuro con degradado de cielo arriba, reflejo, suciedad en las esquinas y leves ondas."""
    m = np.asarray(mascara, np.float32)
    t = np.clip((l.V - v0) / max(v1 - v0, 1e-6), 0, 1)
    base = _hex(CRISTAL)
    cielo = _hex("#4F6A84")
    col = base[None, None, :] * (1 - t[..., None] * 0.6) + cielo[None, None, :] * (t[..., None] * 0.6)
    onda = l.f(6, 18, k=k + 1, oct=2)
    col *= (1 + 0.06 * onda)[..., None]
    l.pintar(m, col, rug=0.08, met=0.0)
    if reflejo:
        r = _ss(0.07, 0.0, np.abs((l.U - l.V * 0.7) - 0.15)) * (0.75 + 0.25 * onda)
        r2 = _ss(0.025, 0.0, np.abs((l.U - l.V * 0.7) - 0.3))
        l.pintar(m * np.clip(r, 0, 1), "#A9BFD4", 0.22)
        l.pintar(m * r2, "#A9BFD4", 0.12)
    sucio = np.clip(l.f(10, k=k + 2) + 0.2 - t * 0.6, 0, 1)
    l.pintar(m * sucio, "#3B3A30", 0.25, rug=0.4)
    l.altura(m, 0.45 + 0.02 * onda)


def pared(nombre):
    l = Lienzo(INDICE[nombre], rug=0.9, fuerza=2.4)
    lejos = "lejos" in nombre
    _yeso(l, 0, 0.8 if lejos else 1.0)
    baja = "baja" in nombre or nombre in ("pared_puerta", "pared_escaparate", "pared_puerta_lejos",
                                          "pared_escaparate_lejos")
    if baja:
        _humedad_baja(l)
        if not lejos and "ventana" in nombre:
            _desconchon(l, 0.86, ZOCALO_V + 0.12, 0.13, k=5)
        _zocalo(l)
    elif "entramado" not in nombre:
        # una grieta fina en el yeso liso (cerca del borde, para que no se note la repetición)
        if nombre == "pared_lisa":
            grieta(l, 0.12, 0.62, -1.2, 0.18, k=9, alfa=0.35, ramas=1)
    if "ventana" in nombre and "entramado" not in nombre:
        _recercado(l, *VENTANA)
        if lejos:
            _ventana_pintada(l, *VENTANA, contraventanas=VERDE_CONTRA)
            _bloque(l, VENTANA[0] - 0.07, VENTANA[1] - 0.04, VENTANA[2] + 0.07, VENTANA[1], k=131)
    if "puerta" in nombre:
        u0, v0, u1, v1 = PUERTA
        # jambas de sillares alternos y dintel con clave
        alto = 1.25 / H
        j = 0
        z = 0.0
        while z < v1 - 0.001:
            w = (0.75 if j % 2 else 1.05) / M
            _bloque(l, u0 - w, z + 0.004, u0, min(z + alto, v1) - 0.004, k=140 + j)
            _bloque(l, u1, z + 0.004, u1 + w, min(z + alto, v1) - 0.004, k=160 + j)
            z += alto
            j += 1
        _bloque(l, u0 - 1.05 / M, v1, u1 + 1.05 / M, v1 + 0.08, k=180)
        _bloque(l, (u0 + u1) / 2 - 0.05, v1 - 0.01, (u0 + u1) / 2 + 0.05, v1 + 0.1, "#B8AE9C", k=181)
        grieta(l, u1 + 1.05 / M, v1 + 0.08, 1.1, 0.14, k=182)
        if lejos:
            c = l.caja(u0, v0, u1, v1)
            madera(l, c, MADERA, l.V * 2, l.U * 5, k=183, anillos=5)
            for j in range(1, 5):
                x = u0 + j * (u1 - u0) / 5
                l.pintar(l.caja(x - 0.003, v0, x + 0.004, v1), "#000000", 0.4)
            l.pintar(c & (l.V < 0.08), "#2A2016", 0.3)
    if "escaparate" in nombre:
        u0, v0, u1, v1 = ESCAPARATE
        friso = l.caja(u0 - 0.06, v1, u1 + 0.06, v1 + 0.13)
        madera(l, friso, MADERA_OSC, l.U * 3, l.V * 6, k=190, anillos=3)  # friso del rótulo
        l.pintar(l.caja(u0 - 0.06, v1 - 0.012, u1 + 0.06, v1), "#000000", 0.25)
        _bloque(l, u0 - 0.04, v0 - 0.03, u1 + 0.04, v0, k=191)  # repisa
        chorretones(l, l.caja(u0 - 0.04, 0, u1 + 0.04, v0 - 0.03), 192, 0.12)
        if lejos:
            c = l.caja(u0, v0, u1, v1)
            madera(l, c, MADERA_OSC, l.V * 2, l.U * 4, k=193, anillos=3)
            vid = l.caja(u0 + 0.02, v0 + 0.02, u1 - 0.02, v1 - 0.17)
            _cristal(l, vid, 194, v0 + 0.02, v1 - 0.17)
            l.em = np.maximum(l.em, vid * 0.5)
            tol = l.caja(u0, v1 - 0.17, u1, v1)
            l.pintar(tol, "#C2413A")  # toldo visto de frente
            l.pintar(tol & (np.floor(l.U * 16) % 2 == 1), "#EDE6D8")
            l.pintar(tol * np.clip(l.f(8, k=195), 0, 1), "#2A1E14", 0.25)
            l.pintar(tol & (l.V < v1 - 0.15), "#000000", 0.3)
    if "entramado" in nombre:
        _entramado(l, nombre)
    return l


def _entramado(l, nombre):
    """Entramado de madera vista (opaco) sobre el yeso: soleras, pies derechos y tornapuntas, cada pieza con la fibra
    en su dirección, aristas gastadas y sombra sobre el yeso."""
    b = 0.055
    piezas = []  # (máscara, a, b) con la fibra a lo largo de a

    def recta(u0, v0, u1, v1, horizontal):
        c = l.caja(u0, v0, u1, v1)
        piezas.append((c, (l.U if horizontal else l.V) * (1.0 if horizontal else 1.25),
                       ((l.V - v0) / max(v1 - v0, 1e-6) if horizontal else (l.U - u0) / max(u1 - u0, 1e-6)) * 0.6,
                       l.dist_caja(u0, v0, u1, v1)))

    def diagonal(x0, y0, x1, y1, w=0.04):
        dx, dy = x1 - x0, y1 - y0
        t = np.clip(((l.U - x0) * dx + (l.V - y0) * dy) / (dx * dx + dy * dy), 0, 1)
        d = np.hypot(l.U - x0 - t * dx, (l.V - y0 - t * dy) * H / M)
        largo = math.hypot(dx, dy)
        piezas.append((d < w, t * largo * 1.25, d / w * 0.3 + 0.37, (w - d) * M))

    recta(0, 0, 1, b, True)
    recta(0, 1 - b, 1, 1, True)
    recta(0, 0, b, 1, False)
    recta(1 - b, 0, 1, 1, False)
    if "ventana" in nombre:
        u0, v0, u1, v1 = VENTANA
        diagonal(0.05, 0.05, u0 - 0.2, v0 - 0.04)
        diagonal(0.95, 0.05, u1 + 0.2, v0 - 0.04)
        recta(u0 - 0.05, v0 - 0.05, u1 + 0.05, v0, True)
        recta(u0 - 0.05, v1, u1 + 0.05, v1 + 0.05, True)
    else:
        diagonal(0.05, 0.05, 0.5, 0.95)
        diagonal(0.95, 0.05, 0.5, 0.95)
        recta(0.5 - b / 2, 0, 0.5 + b / 2, 1, False)
    todo = np.zeros(l.U.shape, bool)
    for c, _, _, _ in piezas:
        todo |= c
    # sombra de las vigas sobre el yeso (abajo a la derecha)
    desplazada = np.roll(np.roll(todo, 2, 0), 2, 1)
    l.pintar(desplazada & ~todo, "#000000", 0.25)
    for i, (c, a, bb, d) in enumerate(piezas):
        madera(l, c, MADERA_OSC, a, bb, k=200 + i * 7, anillos=5, contraste=0.32, alt0=0.62)
        canto = c & (d < 0.07)
        l.pintar(canto, "#000000", 0.18)
        l.altura(canto, l.alt - 0.12)
    if "ventana" in nombre and "lejos" in nombre:
        _ventana_pintada(l, *VENTANA, contraventanas=VERDE_CONTRA, k=230)


def hastial():
    l = Lienzo(5, rug=0.9, fuerza=2.4)
    _yeso(l, 3)
    # óculo de piedra (dovelas) con cristal, en el centro de la parte alta del triángulo
    d = np.hypot((l.U - 0.5) * 1.6, (l.V - 0.42) * 1.0)
    ang = np.arctan2(l.V - 0.42, (l.U - 0.5) * 1.6)
    dovela = np.floor((ang + math.pi) / (2 * math.pi) * 10).astype(np.int64)
    fa = ((ang + math.pi) / (2 * math.pi) * 10) % 1.0
    db = np.minimum(np.minimum(d - 0.09, 0.13 - d) * 8, np.minimum(fa, 1 - fa) * 0.6)
    anillo = (d < 0.13) & (d >= 0.09)
    l.pintar((d < 0.15) & (d >= 0.13) & (l.V < 0.42), "#000000", 0.2)
    piedra(l, anillo & (db > 0.02), PIEDRA, db - 0.02, _hash(dovela, 3, l.s), k=6, bisel=0.06)
    mortero(l, anillo & (db <= 0.02), "#958D80", k=7)
    vid = d < 0.09
    _cristal(l, vid, 8, 0.33, 0.51)
    l.em = np.maximum(l.em, vid * 0.5)
    l.pintar(vid & (np.abs(l.U - 0.5) < 0.006), MADERA_OSC)
    chorretones(l, ((np.abs(l.U - 0.5) < 0.1) & (l.V < 0.33)) * _ss(0.0, 0.3, l.V), 9, 0.15, finos=20)
    # hollín y suciedad bajo el alero (los bordes inclinados del hastial)
    alero = _ss(0.12, 0.0, 1.0 - l.V - np.abs(l.U - 0.5) * 2) * np.clip(0.5 + l.f(8, 3, k=10) * 0.8, 0, 1)
    l.pintar(alero, "#1A140E", 0.22)
    return l


def sillares(lejos=False):
    """Sillares de esquina alternos (opacos) sobre yeso teñible: una cara de la esquina de un piso (1,9 × 10)."""
    l = Lienzo(6, rug=0.9, fuerza=3.0)
    _yeso(l, 4)
    alto = 1.0 / 8
    for j in range(8):
        ancho = 1.0 if j % 2 == 0 else 1.05 / 1.9
        u1 = ancho
        d = l.dist_caja(-1.0, j * alto + 0.006, u1, (j + 1) * alto - 0.006, su=1.9, sv=10.0)
        piedra(l, d > 0, PIEDRA, d, np.full(l.U.shape, _hash(j, 1, l.s)), k=20 + j, bisel=0.14)
        if u1 < 1:  # sombra del sillar corto sobre el yeso
            l.pintar(l.caja(u1, j * alto, u1 + 0.025, (j + 1) * alto - 0.006), "#000000", 0.22)
        mortero(l, l.caja(0, j * alto, ancho, j * alto + 0.006) | l.caja(0, (j + 1) * alto - 0.006, ancho,
                                                                          (j + 1) * alto), "#8E877B", k=40 + j)
    return l


# ==============================================================================================================
# Tejados
# ==============================================================================================================


def teja(hiladas, lejos=False):
    """Tejas teñibles: todo semitransparente (sombras, tonos, líquenes) sobre el color del tejado. Cada teja tiene
    canto redondeado, relieve de canal, su propio tono y alguna está rota o desplazada."""
    l = Lienzo(7 + hiladas + (50 if lejos else 0), rug=0.85, fuerza=4.5 if not lejos else 2.5)
    tejas_fila = 4
    U = l.U + l.f(4, k=1, oct=2) * 0.004
    y = l.V * hiladas
    fila = np.floor(y).astype(np.int64)
    dentro = y - fila
    x = U * tejas_fila + np.mod(fila, 2) * 0.5
    col = np.floor(x).astype(np.int64)
    fx = x - col
    fi, ci = np.mod(fila, hiladas), np.mod(col, tejas_fila)
    ident = _hash(fi, ci, l.s)
    id2 = _hash(fi, ci, l.s + 1)
    # teja desplazada: su canto baja o sube un poco
    desp = np.where(id2 > 0.86, (id2 - 0.86) * 1.2, 0.0)
    canto = 0.04 + 0.26 * (1 - np.sqrt(np.clip(1 - (2 * fx - 1) ** 2, 0, 1))) ** 1.3 - desp
    hueco = dentro < canto  # bajo el canto de esta teja asoma la de abajo (en sombra)
    # tono por teja (oscuras y claras), y variación dentro de la teja
    l.pintar(np.clip((ident - 0.6) * 2.5, 0, 1) * ~hueco, "#FFFFFF", 0.2)
    l.pintar(np.clip((0.45 - ident) * 2.2, 0, 1) * ~hueco, "#1A0F08", 0.26)
    mot = l.f(12, k=2, oct=3)
    l.pintar(np.clip(mot, 0, 1), "#1A0F08", 0.12)
    l.pintar(np.clip(-mot, 0, 1), "#FFFFFF", 0.07)
    # relieve de canal: más luz a la izquierda del lomo, sombra en los bordes
    lomo = np.sin(np.pi * fx)
    l.pintar(_ss(0.35, 0.05, fx) * ~hueco, "#FFFFFF", 0.1)
    l.pintar(_ss(0.65, 1.0, fx) * ~hueco, "#000000", 0.22)
    # sombra del canto de la hilada de encima y del propio canto sobre la de abajo
    l.pintar(_ss(0.7, 1.0, dentro), "#000000", 0.33)
    l.pintar(hueco, "#0E0805", 0.6 if not lejos else 0.4)
    l.pintar(~hueco & (dentro < canto + 0.06), "#FFFFFF", 0.16)
    junta = (fx < 0.035) | (fx > 0.965)
    l.pintar(junta & ~hueco, "#000000", 0.4 if not lejos else 0.25)
    # tejas rotas: les falta una esquina y se ve el hueco
    rota = (ident < 0.07) & (((1 - fx) * 0.8 + dentro * 1.4) < 0.55)
    l.pintar(rota, "#0A0603", 0.7)
    roto_canto = (ident < 0.07) & (np.abs(((1 - fx) * 0.8 + dentro * 1.4) - 0.55) < 0.03)
    l.pintar(roto_canto, "#FFFFFF", 0.2)
    # líquenes (manchas claras amarillentas) y musgo oscuro en las juntas
    liq = _ss(0.45, 0.7, l.f(7, k=3)) * _ss(0.86, 0.95, l.r(56, k=4) + 0.3 * np.clip(l.f(7, k=3), 0, 1))
    l.pintar(liq * ~hueco, "#C9C690", 0.3, rug=0.97)
    musgo = _ss(0.3, 0.6, l.f(5, k=5)) * (hueco | junta)
    l.pintar(musgo, "#3A4626", 0.35, rug=0.97)
    # altura: la teja sube hacia su canto (que monta sobre la de abajo) y tiene lomo
    h = 0.25 + 0.4 * (1 - dentro) + 0.22 * lomo + 0.05 * mot
    h = np.where(hueco, 0.05 + 0.1 * lomo, h)
    h = np.where(rota, 0.0, h)
    l.alt[:] = h
    l.rug[:] = 0.82 + 0.08 * np.clip(mot, -1, 1)
    return l


def cumbrera():
    """Caballete teñible: piezas de lomo redondo solapadas, mortero claro en los bordes."""
    l = Lienzo(9, rug=0.85, fuerza=4.0)
    x = l.U * 5
    seg = np.floor(x).astype(np.int64)
    fs = x - seg
    ident = _hash(np.mod(seg, 5), 0, l.s)
    lomo = np.clip(1 - np.abs(l.V - 0.5) * 2, 0, 1)
    l.pintar(np.clip((ident - 0.55) * 2.5, 0, 1), "#FFFFFF", 0.15)
    l.pintar(np.clip((0.45 - ident) * 2.5, 0, 1), "#1A0F08", 0.2)
    l.pintar(lomo ** 2, "#FFFFFF", 0.18)
    l.pintar(1 - lomo, "#000000", 0.25)
    l.pintar(fs < 0.08, "#000000", 0.45)
    l.pintar((fs >= 0.08) & (fs < 0.13), "#FFFFFF", 0.15)
    mot = l.f(10, 4, k=1)
    l.pintar(np.clip(mot, 0, 1), "#1A0F08", 0.12)
    borde = np.abs(l.V - 0.5) > 0.4 + 0.04 * l.f(16, 2, k=2)
    l.pintar(borde, "#CFC7B6", 0.55, rug=0.95)
    l.pintar(_ss(0.5, 0.75, l.f(6, 2, k=3)), "#C9C690", 0.18)
    l.alt[:] = 0.3 + 0.45 * lomo + 0.2 * fs * (fs > 0.08) + 0.04 * mot
    l.alt[borde] = 0.25
    return l


# ==============================================================================================================
# Piezas de fachada
# ==============================================================================================================


def ventana_casilla():
    """El fondo del hueco de ventana: marco, cristal y cruceta (opaco)."""
    l = Lienzo(10, rug=0.6, fuerza=3.0)
    madera(l, 1.0, MADERA_OSC, l.V * 2, l.U * 3, k=1, anillos=4, contraste=0.3)
    m = 0.08
    vid = l.caja(m, m, 1 - m, 1 - m)
    l.pintar(l.caja(m - 0.02, m - 0.02, 1 - m + 0.02, 1 - m + 0.02) & ~vid, "#000000", 0.3)  # masilla y sombra
    _cristal(l, vid, 2)
    l.em = np.maximum(l.em, vid * 0.5)
    cruz = l.caja(0.47, 0, 0.53, 1) | l.caja(0, 0.6, 1, 0.65)
    madera(l, l.caja(0.47, 0, 0.53, 1), MADERA_OSC, l.V * 2, l.U * 3, k=3, anillos=4)
    madera(l, l.caja(0, 0.6, 1, 0.65), MADERA_OSC, l.U * 2, l.V * 3, k=4, anillos=4)
    l.altura(cruz, 0.7)
    l.pintar(l.caja(0.53, 0.04, 0.55, 0.6) | l.caja(0.04, 0.58, 0.47, 0.6), "#000000", 0.25)
    l.pintar(l.caja(0, 0, 1, 0.025), "#000000", 0.3)
    l.altura(~vid & ~cruz, 0.75)
    return l


def escaparate_casilla():
    l = Lienzo(11, rug=0.6, fuerza=3.0)
    madera(l, 1.0, MADERA_OSC, l.V * 2, l.U * 4, k=1, anillos=4)
    vid = l.caja(0.03, 0.04, 0.97, 0.75)
    _cristal(l, vid, 2, 0.04, 0.75)
    l.em = np.maximum(l.em, vid * 0.5)
    for x in (0.333, 0.666):
        c = l.caja(x - 0.012, 0.04, x + 0.012, 0.97)
        madera(l, c, MADERA_OSC, l.V * 2, l.U * 4, k=int(x * 10), anillos=4)
        l.pintar(l.caja(x + 0.012, 0.04, x + 0.022, 0.75), "#000000", 0.25)
        l.altura(c, 0.75)
    mont = l.caja(0.03, 0.78, 0.97, 0.95)
    l.pintar(mont, "#C9DCE6", 0.5, rug=0.1)
    l.pintar(mont * np.clip(l.f(8, k=5), 0, 1), "#3B3A30", 0.2)
    l.altura(~vid & ~mont, 0.75)
    return l


def contraventana():
    """Contraventana teñible: lamas con relieve (sombras y luces semitransparentes), vetas, pintura saltada en los
    cantos (madera gris a la vista) y marco."""
    l = Lienzo(12, rug=0.78, fuerza=3.5)
    veladura_madera(l, 1.0, l.U * 2, l.V * 3, k=1, alfa=0.12, anillos=6, pa=2, pb=3)
    marco = ~l.caja(0.08, 0.04, 0.92, 0.96)
    l.altura(1.0, 0.5)
    for j in range(9):
        v0 = 0.06 + j * 0.1
        lama = l.caja(0.1, v0, 0.9, v0 + 0.1)
        t = np.clip((l.V - v0) / 0.1, 0, 1)
        l.pintar(lama & (t < 0.35), "#000000", 0.34)
        l.pintar(lama & (t >= 0.35) & (t < 0.5), "#FFFFFF", 0.2)
        l.altura(lama, 0.25 + 0.5 * t)
    l.altura(marco, 0.8)
    l.pintar(marco, "#000000", 0.12)
    l.pintar(l.caja(0.08, 0.04, 0.1, 0.96) | l.caja(0.9, 0.04, 0.92, 0.96), "#000000", 0.3)
    # pintura saltada: se ve la madera gris del fondo (casi opaca), sobre todo en los cantos y abajo
    salto = l.f(10, k=2) + 0.5 * _ss(0.25, 0.0, l.V) + 0.35 * marco
    salt = salto > 0.75
    l.pintar(salt, "#8C7E6B", 0.9, rug=0.9)
    l.pintar(salt * np.clip(l.f(4, 30, k=3) + 0.3, 0, 1), "#4A3E30", 0.5)
    borde_salt = (salto > 0.68) & ~salt
    l.pintar(borde_salt, "#000000", 0.25)
    l.altura(salt, l.alt - 0.08)
    # suciedad abajo y pernios de hierro
    l.pintar(_ss(0.2, 0.0, l.V) * np.clip(0.5 + l.f(8, k=4), 0, 1), "#22180F", 0.3)
    for vv in (0.18, 0.82):
        p = l.caja(0.0, vv - 0.02, 0.32, vv + 0.02)
        _hierro_pieza(l, p, k=int(vv * 100))
        for xx in (0.06, 0.18, 0.28):
            _clavo(l, xx, vv, 0.012)
    return l


def _hierro_pieza(l, mascara, k=0):
    """Herraje de hierro forjado (opaco y metálico) con algo de óxido."""
    m = np.asarray(mascara, np.float32)
    n = l.f(12, k=k + 301)
    col = _hex("#34353A")[None, None, :] * (1 + 0.15 * n)[..., None]
    l.pintar(m, col, rug=0.55, met=1.0)
    ox = _ss(0.2, 0.5, l.f(14, k=k + 302))
    l.pintar(m * ox, "#6E4128", 0.85, rug=0.92, met=0.15)
    l.altura(m, 0.85)
    sombra = np.roll(np.roll(m > 0, 2, 0), 1, 1) & ~(m > 0)
    l.pintar(sombra, "#000000", 0.3)


def _clavo(l, cx, cy, r, color="#2B2A2C", met=1.0):
    d = np.hypot(l.U - cx, l.V - cy)
    l.pintar(d < r, color, rug=0.5, met=met)
    l.pintar((d < r * 0.5) & (l.U < cx) & (l.V > cy), "#FFFFFF", 0.3)
    l.altura(d < r, 0.95 - (d / r) * 0.2)
    l.pintar((d >= r) & (d < r * 1.6) & (l.U > cx) & (l.V < cy), "#000000", 0.3)


def puerta_casilla():
    """Puerta teñible: tablas verticales con vetas semitransparentes y juntas, travesaños en relieve con su sombra,
    pernios de hierro con clavos, tirador dorado y desgaste abajo y alrededor del tirador."""
    l = Lienzo(13, rug=0.75, fuerza=3.5)
    tabla = np.floor(l.U * 5).astype(np.int64)
    ft = l.U * 5 - tabla
    for j in range(5):
        c = tabla == j
        veladura_madera(l, c, l.V * 2 + j * 0.37, ft * 0.7 + j * 0.21, k=10 + j, alfa=0.14, anillos=5,
                        nudos=((0.6 + 0.3 * _hash(j, 1, 3), 0.45 + j * 0.21, 0.04),) if j % 2 else ())
        idt = _hash(j, 0, l.s)
        l.pintar(c, "#000000" if idt < 0.5 else "#FFFFFF", abs(idt - 0.5) * 0.14)
    junta = (ft < 0.03) | (ft > 0.985)
    l.pintar(junta, "#0D0805", 0.5)
    l.altura(junta, 0.2)
    for (v0, v1) in ((0.2, 0.26), (0.72, 0.78)):
        c = l.caja(0, v0, 1, v1)
        veladura_madera(l, c, l.U * 2, (l.V - v0) / 0.06 * 0.6, k=int(v0 * 100), alfa=0.12, anillos=3)
        l.pintar(c & (l.V > v1 - 0.01), "#FFFFFF", 0.18)
        l.pintar(l.caja(0, v0 - 0.02, 1, v0), "#000000", 0.32)
        l.altura(c, 0.8)
        p = l.caja(0.0, v0 + 0.012, 0.42, v1 - 0.012)
        _hierro_pieza(l, p, k=int(v0 * 100))
        for xx in (0.05, 0.16, 0.27, 0.38):
            _clavo(l, xx, (v0 + v1) / 2, 0.011)
        for xx in (0.55, 0.75, 0.93):
            _clavo(l, xx, (v0 + v1) / 2, 0.009)
    # desgaste: patada abajo, mano alrededor del tirador
    l.pintar(_ss(0.16, 0.0, l.V) * np.clip(0.5 + l.f(10, k=20), 0, 1), "#20160D", 0.35)
    mano = np.exp(-(((l.U - 0.8) / 0.12) ** 2 + ((l.V - 0.47) / 0.1) ** 2))
    l.pintar(mano * np.clip(0.6 + l.f(16, k=21), 0, 1), "#20160D", 0.22)
    # tirador dorado (aro con placa)
    pl = l.caja(0.78, 0.43, 0.86, 0.51)
    l.pintar(pl, "#B88E3C", rug=0.35, met=1.0)
    d = np.hypot(l.U - 0.82, (l.V - 0.44) * 1.0)
    aro = (d > 0.03) & (d < 0.042) & (l.V < 0.47)
    l.pintar(aro, "#D2A64A", rug=0.3, met=1.0)
    l.pintar(aro & (l.U < 0.81), "#FFF0C0", 0.35)
    l.pintar((pl | aro) * np.clip(l.f(20, k=22), 0, 1), "#4A3A1A", 0.5)
    l.altura(pl, 0.85)
    l.altura(aro, 0.95)
    return l


def toldo():
    """Toldo teñible: franjas blancas opacas (algo amarillentas y sucias) alternas con franjas del color de la
    instancia; tela con pliegues, manchas de lluvia y festón ondulado abajo."""
    l = Lienzo(14, rug=0.92, fuerza=2.5)
    franja = np.floor(l.U * 8) % 2 == 1
    blanco = _hex("#F0EBE0")[None, None, :] * (1 + 0.04 * l.f(6, k=1))[..., None]
    l.pintar(franja, blanco)
    # pliegues suaves (siguen las franjas, periódicos) y combado entre varillas
    pliegue = np.sin(l.U * 2 * np.pi * 4) * 0.5 + 0.5
    l.pintar(pliegue, "#000000", 0.12)
    l.pintar(1 - pliegue, "#FFFFFF", 0.06)
    # trama de la lona (suave, no de píxel)
    trama = np.sin(l.U * 2 * np.pi * 32) * np.sin(l.V * 2 * np.pi * 32)
    l.pintar(np.clip(trama, 0, 1), "#000000", 0.05)
    # manchas de lluvia y verdín en la parte baja; suciedad en las costuras
    l.pintar(np.clip(l.f(5, k=2) * 1.3, 0, 1), "#2A2015", 0.18)
    chorretones(l, _ss(0.7, 0.1, l.V), 3, 0.18, finos=24)
    costura = np.abs(((l.U * 8 + 0.5) % 1.0) - 0.5) > 0.47
    l.pintar(costura, "#000000", 0.2)
    feston = l.V < 0.05 + 0.025 * np.cos(l.U * 2 * np.pi * 16)
    l.pintar(feston, "#000000", 0.3)
    l.pintar((l.V < 0.09) & ~feston, "#000000", 0.1)
    l.alt[:] = 0.5 + 0.25 * pliegue + 0.02 * trama
    return l


def cartel(emblema):
    """Cartel colgante: marco de madera con la fibra en su dirección e ingletes, tabla pintada envejecida (bordes
    quemados, manchas, pintura cuarteada) y el emblema con contorno y volumen."""
    l = Lienzo(INDICE["cartel_" + emblema], rug=0.7, fuerza=3.0)
    marco_h = (l.V < 0.08) | (l.V > 0.92)
    diag = np.abs(l.U - 0.5) - np.abs(l.V - 0.5) > 0
    vertical = diag & ~(l.caja(0.08, 0.08, 0.92, 0.92))
    horizontal = ~diag & ~(l.caja(0.08, 0.08, 0.92, 0.92))
    madera(l, horizontal, "#8A6340", l.U * 2, l.V * 4, k=1, anillos=4)
    madera(l, vertical, "#83603F", l.V * 2, l.U * 4, k=2, anillos=4)
    l.pintar(_ss(0.006, 0.0, np.abs(np.abs(l.U - 0.5) - np.abs(l.V - 0.5))) * ~l.caja(0.08, 0.08, 0.92, 0.92),
             "#000000", 0.4)
    l.altura(~l.caja(0.08, 0.08, 0.92, 0.92), 0.75)
    for (cx, cy) in ((0.04, 0.04), (0.96, 0.04), (0.04, 0.96), (0.96, 0.96)):
        _clavo(l, cx, cy, 0.016)
    tabla = l.caja(0.08, 0.08, 0.92, 0.92)
    pergamino = _hex("#E9DFC5")[None, None, :] * (1 + 0.05 * l.f(6, k=3) + 0.03 * l.f(24, k=4, oct=2))[..., None]
    l.pintar(tabla, pergamino, rug=0.8)
    borde = np.minimum(np.minimum(l.U - 0.08, 0.92 - l.U), np.minimum(l.V - 0.08, 0.92 - l.V))
    quemado = _ss(0.08, 0.0, borde + 0.02 * l.f(14, k=5)) * tabla
    l.pintar(quemado, "#6B4A28", 0.55)
    l.pintar(tabla * np.clip(l.f(5, k=6) * 1.4, 0, 1), "#7A5A30", 0.2)
    l.pintar(tabla & (borde < 0.012), "#000000", 0.3)
    l.altura(tabla, 0.45)

    emb = np.zeros(l.U.shape, np.float32)

    def figura(mascara, color):
        nonlocal emb
        mk = np.asarray(mascara, bool) & tabla
        c = _col(color)
        # volumen: luz arriba a la izquierda dentro de la figura
        sombra = np.roll(np.roll(mk, -2, 0), -2, 1)
        col = c[None, None, :] * (1 + 0.05 * l.f(10, k=7))[..., None]
        l.pintar(mk, col, rug=0.65)
        l.pintar(mk & ~sombra, "#000000", 0.25)
        l.pintar(mk & ~np.roll(np.roll(mk, 2, 0), 2, 1), "#FFFFFF", 0.25)
        emb = np.maximum(emb, mk)

    if emblema == "bolsa":
        figura(np.hypot(l.U - 0.5, (l.V - 0.42) * 1.1) < 0.24, "#B48858")
        figura(l.caja(0.42, 0.6, 0.58, 0.72), "#B48858")
        figura(l.caja(0.38, 0.6, 0.62, 0.64), "#5C4130")
        figura(np.hypot(l.U - 0.5, l.V - 0.4) < 0.06, "#D2A64A")
    elif emblema == "espada":
        figura(l.caja(0.47, 0.32, 0.53, 0.82) | ((np.abs(l.U - 0.5) < 0.03 * (0.88 - l.V) / 0.06) &
                                                   (l.V >= 0.82) & (l.V < 0.88)), "#C9CDD2")
        figura(l.caja(0.495, 0.36, 0.505, 0.8), "#9AA0A8")
        figura(l.caja(0.36, 0.3, 0.64, 0.35), "#D2A64A")
        figura(l.caja(0.47, 0.18, 0.53, 0.3), "#5C4130")
        figura(np.hypot(l.U - 0.5, l.V - 0.16) < 0.03, "#D2A64A")
    elif emblema == "gema":
        figura(np.abs(l.U - 0.5) * 1.4 + np.abs(l.V - 0.5) < 0.3, "#3F6FA8")
        figura((np.abs(l.U - 0.5) * 1.4 + np.abs(l.V - 0.5) < 0.3) & (l.U > 0.5) & (l.V < 0.5), "#2E5585")
        figura(np.abs(l.U - 0.45) * 1.4 + np.abs(l.V - 0.56) < 0.08, "#9FC3F0")
    elif emblema == "yunque":
        figura(l.caja(0.25, 0.52, 0.75, 0.62) | l.caja(0.42, 0.3, 0.58, 0.52) | l.caja(0.32, 0.24, 0.68, 0.3) |
               ((l.U < 0.25) & (l.U > 0.15) & (l.V > 0.55 + (0.25 - l.U) * 0.4) & (l.V < 0.62)), "#3A3B40")
        figura(l.caja(0.27, 0.6, 0.73, 0.62), "#6A6C72")
    elif emblema == "pan":
        figura(np.hypot((l.U - 0.5) * 0.8, (l.V - 0.5) * 1.6) < 0.22, "#C99A55")
        for x in (0.42, 0.5, 0.58):
            figura((np.abs(l.U - x - (l.V - 0.5) * 0.3) < 0.012) &
                   (np.hypot((l.U - 0.5) * 0.8, (l.V - 0.5) * 1.6) < 0.18), "#8A6340")
    elif emblema == "pocion":
        figura(np.hypot(l.U - 0.5, l.V - 0.42) < 0.2, "#C8352E")
        figura((np.hypot(l.U - 0.5, l.V - 0.42) < 0.2) & (l.V < 0.44 + 0.02 * np.sin(l.U * 40)), "#9E2620")
        figura(l.caja(0.45, 0.58, 0.55, 0.74), "#9FB6CC")
        figura(l.caja(0.44, 0.74, 0.56, 0.79), "#8A6340")
        figura(np.hypot(l.U - 0.44, l.V - 0.5) < 0.035, "#F3B0A8")
    # pintura cuarteada y desgastada encima de todo
    cuarteo = _ss(0.03, 0.0, np.abs(l.f(18, k=8, oct=2)))
    l.pintar(cuarteo * tabla, "#3A2A18", 0.3)
    l.pintar(tabla * _ss(0.55, 0.8, l.f(9, k=9)), "#D8CCAE", 0.5)
    l.altura(emb > 0, 0.5)
    l.altura(cuarteo * tabla, l.alt - 0.1)
    return l


def jardinera():
    """Jardinera: madera abajo (dos tablas con vetas y clavos) y hojas y flores arriba."""
    l = Lienzo(16, rug=0.7, fuerza=3.5)
    caja_m = l.V <= 0.45
    madera(l, caja_m, "#8A6340", l.U * 2, l.V * 4.4, k=1, anillos=4, pa=2)
    for y in (0.15, 0.3):
        l.pintar(np.abs(l.V - y) < 0.008, "#000000", 0.45)
        l.altura(np.abs(l.V - y) < 0.008, 0.2)
    for x in (0.06, 0.94):
        for y in (0.08, 0.23, 0.38):
            _clavo(l, x, y, 0.012)
    l.pintar(caja_m & (l.V > 0.4), "#000000", 0.3)
    l.pintar(caja_m * _ss(0.1, 0.0, l.V), "#2A1E12", 0.3)
    arriba = l.V > 0.45
    l.pintar(arriba, "#2D4F22")
    _hojas_formas(l, arriba, "#4E8A38", 120, 0.035, k=2, v_min=0.43)
    colores = ["#D9443A", "#F2A9C2", "#F2CF45", "#F5F2EA", "#A98BD6"]
    for j in range(22):
        cx, cy = l.rng.uniform(0.05, 0.95), l.rng.uniform(0.52, 0.97)
        _flor(l, cx, cy, l.rng.uniform(0.025, 0.04), colores[j % len(colores)], l.rng.uniform(0, 6))
    return l


# ==============================================================================================================
# Opacos con dibujo
# ==============================================================================================================


def sillar_muro():
    """Muro de sillares (opaco): 4 hiladas de 3 piezas desfasadas, juntas irregulares, golpes, verdín y suciedad en
    la base."""
    l = Lienzo(17, rug=0.9, fuerza=3.5)
    d, ident, *_ = aparejo(l, 4, 3, k=1, jit=0.25, su=8.0, sv=8.0)
    junta = 0.07 + 0.03 * l.f(16, k=2)
    piedra(l, d > junta, "#A2998A", d - junta, ident, k=3, var=0.1, bisel=0.25)
    mortero(l, d <= junta, "#7A746B", k=4)
    musgo = _ss(0.3, 0.0, l.V + 0.1 * l.f(6, k=5)) * np.clip(0.4 + l.f(9, k=6) * 1.3, 0, 1)
    l.pintar(musgo, "#55692F", 0.55, rug=0.97)
    l.pintar(musgo * (d <= junta + 0.04), "#3E5226", 0.6)
    liq = _ss(0.45, 0.65, l.f(8, k=7)) * (d > junta)
    l.pintar(liq, "#C9C49C", 0.35)
    l.pintar(_ss(0.08, 0.0, l.V), "#3A2E22", 0.35)
    return l


def ladrillo():
    """Ladrillo (chimeneas): ladrillos de tonos variados (alguno requemado), juntas de mortero irregulares, cantos
    gastados y hollín arriba."""
    l = Lienzo(18, rug=0.88, fuerza=3.5)
    d, ident, *_ = aparejo(l, 10, 4, k=1, jit=0.12, su=4.0, sv=6.0, alabeo=0.003)
    junta = 0.045 + 0.015 * l.f(20, k=2)
    tonos = ["#A65A3E", "#9A4E36", "#B4673F", "#8E4A34", "#B86F4C", "#6E382A", "#A85F45"]
    idx = np.minimum((ident * len(tonos)).astype(int), len(tonos) - 1)
    pal = np.stack([_hex(t) for t in tonos])[idx]
    lad = d > junta
    piedra(l, lad, "#FFFFFF", d - junta, ident, k=3, var=0.0, bisel=0.06, golpes=1.3, relieve=0.35)
    l.rgba[..., :3] = np.where(lad[..., None], l.rgba[..., :3] * pal, l.rgba[..., :3])
    mortero(l, ~lad, "#C9BCA6", k=4, alt=0.12)
    eflo = _ss(0.4, 0.7, l.f(6, k=5))
    l.pintar(eflo, "#E8E2D4", 0.25)
    hollin = _ss(0.55, 1.0, l.V + 0.15 * l.f(5, k=6)) * np.clip(0.6 + l.f(10, k=7), 0, 1)
    l.pintar(hollin, "#151210", 0.65)
    return l


def tablon():
    """Tablón de misiones: tablas horizontales de madera con vetas y clavos, y papeles clavados (amarillentos, con
    bordes oscuros, sombra y alguna esquina doblada)."""
    l = Lienzo(19, rug=0.65, fuerza=3.0)
    tablas = np.floor(l.V * 5).astype(np.int64)
    fv = l.V * 5 - tablas
    for j in range(5):
        madera(l, tablas == j, "#8A6340" if j % 2 else "#806040", l.U * 2 + j * 0.31, fv * 0.6 + j * 0.27,
               k=j * 5, anillos=4)
    l.pintar((fv < 0.04) | (fv > 0.98), "#0E0905", 0.55)
    l.altura((fv < 0.04) | (fv > 0.98), 0.15)
    for j in range(5):
        for x in (0.04, 0.96):
            _clavo(l, x, (j + 0.5) / 5, 0.012)
    for j in range(9):
        cx, cy = l.rng.uniform(0.15, 0.85), l.rng.uniform(0.2, 0.8)
        w, h = l.rng.uniform(0.09, 0.14), l.rng.uniform(0.11, 0.16)
        giro = l.rng.uniform(-0.12, 0.12)
        du = (l.U - cx) * math.cos(giro) + (l.V - cy) * math.sin(giro)
        dv = -(l.U - cx) * math.sin(giro) + (l.V - cy) * math.cos(giro)
        papel = (np.abs(du) < w / 2) & (np.abs(dv) < h / 2)
        doblez = (du + dv) > (w / 2 + h / 2 - 0.035)
        sombra = (np.abs(du - 0.01) < w / 2) & (np.abs(dv + 0.012) < h / 2) & ~papel
        l.pintar(sombra, "#000000", 0.4)
        col = _hex("#F4EEDC" if j % 3 else "#EFD98A")[None, None, :] * (1 + 0.05 * l.f(8, k=30 + j))[..., None]
        l.pintar(papel & ~doblez, col, rug=0.85)
        l.pintar(papel & ~doblez & (np.minimum(w / 2 - np.abs(du), h / 2 - np.abs(dv)) < 0.012), "#8C6A3A", 0.35)
        l.pintar((papel & ~doblez) * np.clip(l.f(6, k=40 + j), 0, 1), "#9A7A40", 0.3)
        l.pintar(papel & doblez & ((du + dv) < (w / 2 + h / 2 - 0.035) + 0.03), "#D8CCB0")
        l.altura(papel, 0.65)
        for r in range(3):
            linea = (np.abs(dv - (h / 2 - 0.04 - r * 0.03)) < 0.004) & (du > -w / 2 + 0.015) & (du < w / 2 - 0.02)
            l.pintar(linea & papel, "#5A5045", 0.8)
        px_, py_ = cx - (h / 2 - 0.015) * math.sin(giro), cy + (h / 2 - 0.015) * math.cos(giro)
        _clavo(l, px_, py_, 0.012, color="#C8352E", met=0.0)
    return l


def reloj():
    """Esfera de reloj: aro dorado (metal, con pátina), esfera de esmalte envejecida y cuarteada, marcas y agujas de
    hierro."""
    l = Lienzo(20, rug=0.5, fuerza=3.0)
    d = np.hypot(l.U - 0.5, l.V - 0.5)
    l.pintar(1.0, _hex("#E9DFC5")[None, None, :] * (1 + 0.05 * l.f(6, k=1))[..., None], rug=0.85)
    aro = (d < 0.5) & (d >= 0.43)
    col = _hex("#D2A64A")[None, None, :] * (1 + 0.1 * l.f(12, k=2) + 0.12 * (0.5 - (l.V - 0.5)))[..., None]
    l.pintar(aro, col, rug=0.35, met=1.0)
    l.pintar(aro * _ss(0.2, 0.5, l.f(8, k=3)), "#5A4A2A", 0.55, rug=0.6)
    l.altura(aro, 0.6 + 0.3 * np.sin((d - 0.43) / 0.07 * np.pi))
    esf = d < 0.43
    esmalte = _hex("#F4EEDC")[None, None, :] * (1 - 0.1 * np.clip(d / 0.43, 0, 1) ** 2)[..., None]
    l.pintar(esf, esmalte, rug=0.3)
    l.pintar(esf * _ss(0.025, 0.0, np.abs(l.f(10, k=4, oct=2))), "#6A5A40", 0.3)
    l.pintar(esf * np.clip(l.f(4, k=5), 0, 1), "#8A7A50", 0.25)
    a = np.arctan2(l.V - 0.5, l.U - 0.5)
    pos = (a / (2 * math.pi) * 12) % 1.0
    marcas = (np.abs(pos - 0.5) > 0.45) & (d > 0.33) & (d < 0.4)
    grandes = (np.abs(((a / (2 * math.pi) * 4) % 1.0) - 0.5) > 0.47) & (d > 0.3) & (d < 0.4)
    l.pintar(marcas | grandes, "#2E2F33", rug=0.4)
    for j in range(60):
        an = j / 60 * 2 * math.pi
        x0, y0 = 0.5 + 0.395 * math.cos(an), 0.5 + 0.395 * math.sin(an)
        l.pintar(np.hypot(l.U - x0, l.V - y0) < 0.004, "#2E2F33", 0.8)
    l.altura(esf, 0.45)
    ag = ((np.abs(l.U - 0.5) < 0.015) & (l.V > 0.5) & (l.V < 0.75)) | \
         ((np.abs(l.V - 0.5) < 0.012) & (l.U > 0.5) & (l.U < 0.84))
    l.pintar(np.roll(np.roll(ag, 2, 0), 2, 1) & ~ag, "#000000", 0.25)
    l.pintar(ag, "#2E2F33", rug=0.45, met=1.0)
    l.pintar(np.hypot(l.U - 0.5, l.V - 0.5) < 0.03, "#D2A64A", rug=0.3, met=1.0)
    l.altura(ag, 0.75)
    l.pintar(d >= 0.5, _hex("#E9DFC5")[None, None, :] * (1 + 0.06 * l.f(6, k=6))[..., None], rug=0.9, met=0.0)
    l.pintar((d >= 0.5) & (d < 0.52), "#000000", 0.3)
    l.altura(d >= 0.5, 0.4)
    return l


def vela():
    """Aspa de molino: lona con trama, remiendos y manchas, sobre una celosía de madera."""
    l = Lienzo(21, rug=0.9, fuerza=3.0)
    lona = _hex("#EDE3CC")[None, None, :] * (1 + 0.05 * l.f(5, k=1) + 0.03 * l.f(20, k=2, oct=2))[..., None]
    l.pintar(1.0, lona)
    trama = np.sin(l.U * 2 * np.pi * 32) * np.sin(l.V * 2 * np.pi * 32)
    l.pintar(np.clip(trama, 0, 1), "#000000", 0.05)
    l.pintar(np.clip(l.f(4, k=3) * 1.3, 0, 1), "#6A5A3A", 0.2)
    l.alt[:] = 0.4 + 0.03 * trama
    remiendo = l.caja(0.55, 0.3, 0.78, 0.48)
    l.pintar(remiendo, "#DCCFAE")
    l.pintar(remiendo & ~l.caja(0.56, 0.31, 0.77, 0.47), "#5A4A30", 0.5)
    for j in range(10):
        lis = np.abs(l.V - j / 9) < 0.018
        madera(l, lis, "#8A6340", l.U * 2, (l.V - j / 9) * 6 + j * 0.3, k=10 + j, anillos=2, alt0=0.7)
        l.pintar(np.abs(l.V - j / 9 + 0.024) < 0.006, "#000000", 0.3)
    ver = (l.U < 0.06) | (l.U > 0.94)
    madera(l, ver, "#8A6340", l.V * 2, l.U * 3, k=30, anillos=3, alt0=0.75)
    madera(l, l.U < 0.06, "#5C4130", l.V * 2, l.U * 3, k=31, anillos=3, alt0=0.8)
    return l


# ==============================================================================================================
# Vegetación y cultivos
# ==============================================================================================================


def _hojas_formas(l, mascara, color, n, largo, k=0, v_min=0.0, ancho=0.45, base_osc=0.45, var=0.2, giro=None):
    """Capa de hojas (elipses orientadas con nervio y luz), repartidas con envoltura (periódicas). Las de encima,
    más claras y altas."""
    rng = np.random.default_rng(l.s + k)
    c0 = _col(color)
    mk = np.asarray(mascara, np.float32)
    for i in range(n):
        cx, cy = rng.uniform(0, 1), rng.uniform(v_min, 1)
        ang = rng.uniform(0, 2 * np.pi) if giro is None else giro + rng.normal(0, 0.35)
        L = largo * rng.uniform(0.7, 1.3)
        W = L * ancho * rng.uniform(0.8, 1.2)
        dx = (l.U - cx + 0.5) % 1.0 - 0.5
        dy = (l.V - cy + 0.5) % 1.0 - 0.5
        a = dx * math.cos(ang) + dy * math.sin(ang)
        b = -dx * math.sin(ang) + dy * math.cos(ang)
        e = (a / L) ** 2 + (b / W) ** 2
        hoja = e < 1
        if not hoja.any():
            continue
        prof = i / max(n - 1, 1)
        tono = (1 - var + 2 * var * rng.uniform()) * (0.75 + 0.35 * prof)
        luz = np.clip(0.85 + 0.35 * (-b / W) * math.cos(ang - 2.3), 0.6, 1.25)
        col = c0[None, None, :] * (tono * luz * (1 - 0.18 * np.exp(-(b / (W * 0.12)) ** 2)))[..., None]
        borde = _ss(0.7, 1.0, e)
        col *= (1 - 0.25 * borde)[..., None]
        l.pintar(hoja * mk, col, rug=0.65 - 0.15 * prof)
        l.altura(hoja * mk, 0.2 + 0.6 * prof + 0.15 * (1 - e))


def _flor(l, cx, cy, r, color, giro=0.0, petalos=5):
    d = np.hypot(l.U - cx, l.V - cy)
    a = np.arctan2(l.V - cy, l.U - cx) + giro
    forma = r * (0.65 + 0.35 * np.abs(np.cos(a * petalos / 2)))
    pet = d < forma
    c = _col(color)
    col = c[None, None, :] * (0.8 + 0.25 * np.clip(1 - d / r, 0, 1))[..., None]
    l.pintar((d < forma * 1.15) & ~pet & (l.V < cy), "#000000", 0.3)
    l.pintar(pet, col, rug=0.6)
    l.pintar(d < r * 0.28, "#E8B730")
    l.pintar(d < r * 0.14, "#8A5A1A")
    l.altura(pet, 0.85)


def hojas(color, semilla, pino=False, flor=False):
    """Follaje: fondo en sombra y varias capas de hojas (o agujas) periódicas."""
    l = Lienzo(semilla, rug=0.6, fuerza=3.5)
    c = _col(color)
    fondo = (_hex("#2F5226") if flor else c)[None, None, :] * (0.42 + 0.1 * l.f(4, k=1))[..., None]
    l.pintar(1.0, fondo)
    l.alt[:] = 0.1
    if pino:
        for capa in range(4):
            for j in range(34):
                cx, cy = l.rng.uniform(0, 1, 2)
                ramita = l.rng.uniform(-0.4, 0.4) - np.pi / 2
                rng2 = np.random.default_rng(semilla * 100 + capa * 30 + j)
                for t in np.linspace(0.0, 1.0, 7):
                    x = cx + math.cos(ramita) * 0.12 * t
                    y = cy + math.sin(ramita) * 0.12 * t
                    for lado in (-1, 1):
                        ang = ramita + lado * 0.9 + rng2.normal(0, 0.15)
                        dx = (l.U - x + 0.5) % 1.0 - 0.5
                        dy = (l.V - y + 0.5) % 1.0 - 0.5
                        a = dx * math.cos(ang) + dy * math.sin(ang)
                        b = -dx * math.sin(ang) + dy * math.cos(ang)
                        ag = (a > 0) & (a < 0.04) & (np.abs(b) < 0.0065 * (1 - a / 0.05))
                        tono = (0.75 + 0.18 * capa + 0.15 * rng2.uniform()) * (1.15 - 0.3 * t)
                        l.pintar(ag, c * tono, rug=0.6)
                        l.altura(ag, 0.3 + 0.25 * capa)
    elif flor:
        _hojas_formas(l, 1.0, "#4E7A34", 40, 0.06, k=2)
        for j in range(70):
            cx, cy = l.rng.uniform(0, 1, 2)
            r, tono, giro = l.rng.uniform(0.03, 0.05), l.rng.uniform(0.85, 1.12), l.rng.uniform(0, 6)
            # copias desplazadas una casilla para que las flores del borde sigan al otro lado (periódico)
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    if abs(cx + ox - 0.5) < 0.56 and abs(cy + oy - 0.5) < 0.56:
                        _flor(l, cx + ox, cy + oy, r, c * tono, giro)
    else:
        _hojas_formas(l, 1.0, c * 0.85, 70, 0.075, k=2)
        _hojas_formas(l, 1.0, c * 1.0, 70, 0.065, k=3)
        _hojas_formas(l, 1.0, c * 1.15, 45, 0.055, k=4)
    return l


def hierba():
    """Hierba: briznas finas casi verticales de verdes y amarillos sobre un fondo oscuro con tierra a ratos."""
    l = Lienzo(48, rug=0.8, fuerza=2.5)
    base = _hex("#5B8A38")[None, None, :] * (0.7 + 0.12 * l.f(4, k=1))[..., None]
    l.pintar(1.0, base)
    l.pintar(_ss(0.35, 0.6, l.f(5, k=2)), "#6A5638", 0.5)
    _briznas(l, 260, ["#73A845", "#86B846", "#5C9A3B", "#9DB65A", "#B8B866"], 0.07, k=3)
    return l


def _briznas(l, n, colores, largo, k=0, ancho=0.006, vertical=0.35):
    rng = np.random.default_rng(l.s + k)
    for i in range(n):
        cx, cy = rng.uniform(0, 1, 2)
        ang = np.pi / 2 + rng.normal(0, vertical)
        L = largo * rng.uniform(0.6, 1.4)
        x1, y1 = cx + math.cos(ang) * L, cy + math.sin(ang) * L
        dx = (l.U - cx + 0.5) % 1.0 - 0.5 + cx
        dy = (l.V - cy + 0.5) % 1.0 - 0.5 + cy
        d, t = _segmento(dx, dy, cx, cy, x1, y1)
        w = ancho * (1 - 0.8 * t)
        b = d < w
        if not b.any():
            continue
        c = _col(colores[rng.integers(len(colores))]) * rng.uniform(0.8, 1.15)
        col = c[None, None, :] * (0.65 + 0.45 * t)[..., None]
        l.pintar(b, col, rug=0.7)
        l.altura(b, 0.2 + 0.6 * t * (i / n))


def flores():
    l = hierba()
    l.rng = np.random.default_rng(22)
    colores = ["#D9443A", "#F2CF45", "#F5F2EA", "#A98BD6", "#F2A9C2"]
    for j in range(34):
        cx, cy = l.rng.uniform(0.04, 0.96, 2)
        _flor(l, cx, cy, l.rng.uniform(0.03, 0.05), colores[j % 5], l.rng.uniform(0, 6))
    return l


def fruta():
    """Frutal: hojas con manzanas rojas y amarillas con brillo."""
    l = hojas("#4E8A38", 55)
    l.rng = np.random.default_rng(56)
    for j in range(16):
        cx, cy = l.rng.uniform(0.07, 0.93, 2)
        r = l.rng.uniform(0.035, 0.05)
        c = _hex(["#C8352E", "#D9543A", "#E0B040", "#B02A24"][j % 4])
        d = np.hypot(l.U - cx, l.V - cy)
        l.pintar((d < r * 1.2) & (l.V < cy), "#000000", 0.35)
        col = c[None, None, :] * (0.7 + 0.45 * np.clip(1 - np.hypot(l.U - cx + r * 0.35, l.V - cy - r * 0.35) / r,
                                                      0, 1))[..., None]
        l.pintar(d < r, col, rug=0.35)
        l.pintar(np.hypot(l.U - cx + r * 0.35, l.V - cy - r * 0.35) < r * 0.2, "#FFFFFF", 0.5)
        l.pintar(np.hypot(l.U - cx, l.V - cy - r * 0.85) < r * 0.15, "#4A3420")
        l.altura(d < r, 0.9 - (d / r) * 0.3)
    return l


def surcos(base, surco, semilla, tipo):
    """Campos: trigo (espigas), paja (haces de briznas) y tierra arada (caballones con terrones). 6 surcos por
    casilla (periódico)."""
    l = Lienzo(semilla, rug=0.85, fuerza=3.0)
    fu = (l.U * 6 + 0.12 * l.f(2, 3, k=9, oct=3)) % 1.0
    if tipo == "tierra":
        perfil = np.sin(fu * np.pi)
        col = _hex(base)[None, None, :] * (0.7 + 0.35 * perfil + 0.1 * l.f(8, k=1))[..., None]
        l.pintar(1.0, col, rug=0.95)
        terron = _ss(0.25, 0.5, l.f(24, k=2, oct=2))
        l.pintar(terron, "#4A3424", 0.5)
        l.pintar(_ss(0.82, 0.92, l.r(40, k=3)), "#9A8A78", 0.8)  # piedrecitas
        l.pintar(_ss(0.35, 0.0, perfil), _hex(surco) * 0.8, 0.5)
        l.alt[:] = 0.2 + 0.6 * perfil + 0.15 * terron
        hum = _ss(0.3, 0.6, l.f(4, k=4))
        l.pintar(hum * (perfil < 0.4), "#2A1E14", 0.3, rug=0.7)
        return l
    l.pintar(1.0, _hex(surco)[None, None, :] * (0.6 + 0.1 * l.f(6, k=1))[..., None])
    l.alt[:] = 0.15
    rng = np.random.default_rng(semilla)
    n = 360 if tipo == "trigo" else 420
    for i in range(n):
        surco_i = rng.integers(6)
        cx = (surco_i + 0.5 + rng.normal(0, 0.16)) / 6
        cy = rng.uniform(0, 1)
        if tipo == "paja":
            cx = rng.uniform(0, 1)
        ang = np.pi / 2 + rng.normal(0, 0.12 if tipo == "trigo" else 0.25)
        L = rng.uniform(0.08, 0.16)
        x1, y1 = cx + math.cos(ang) * L, cy + math.sin(ang) * L
        dx = (l.U - cx + 0.5) % 1.0 - 0.5 + cx
        dy = (l.V - cy + 0.5) % 1.0 - 0.5 + cy
        d, t = _segmento(dx, dy, cx, cy, x1, y1)
        tallo = d < 0.0045
        c = _hex(base) * rng.uniform(0.8, 1.15)
        col = c[None, None, :] * (0.7 + 0.4 * t)[..., None]
        l.pintar(tallo, col, rug=0.75)
        l.altura(tallo, 0.3 + 0.5 * t)
        if tipo == "trigo" and rng.uniform() < 0.6:
            ex, ey = x1, y1
            de = np.hypot((dx - ex) * 2.6, dy - ey)
            espiga = de < 0.028
            granos = np.sin((dy - ey) * 2 * np.pi * 60) > -0.2
            l.pintar(espiga & granos, c * 1.05, rug=0.7)
            l.pintar(espiga & ~granos, c * 0.6)
            l.altura(espiga, 0.9)
    return l


def corteza(color, semilla, abedul=False):
    """Corteza: grietas verticales profundas con placas y líquenes (o abedul: blanco con lenticelas y ojos negros)."""
    l = Lienzo(semilla, rug=0.92, fuerza=4.0)
    c = _hex(color)
    if abedul:
        col = c[None, None, :] * (0.95 + 0.06 * l.f(4, 8, k=1))[..., None]
        l.pintar(1.0, col)
        l.pintar(_ss(0.3, 0.6, l.f(3, 10, k=2)), "#B8B0A0", 0.5)
        l.alt[:] = 0.5 + 0.05 * l.f(6, 12, k=3)
        for j in range(26):
            cx, cy = l.rng.uniform(0, 1, 2)
            w, h = l.rng.uniform(0.03, 0.12), l.rng.uniform(0.006, 0.014)
            dx = (l.U - cx + 0.5) % 1.0 - 0.5
            dy = (l.V - cy + 0.5) % 1.0 - 0.5
            le = (dx / w) ** 2 + (dy / h) ** 2 < 1
            l.pintar(le, "#2E2A26", 0.9)
            l.altura(le, 0.3)
        for j in range(3):
            cx, cy = l.rng.uniform(0.15, 0.85, 2)
            dx, dy = l.U - cx, l.V - cy
            ojo = (np.abs(dx) * 1.6 + np.maximum(dy, 0) * 4 + np.maximum(-dy, 0) * 1.4 < 0.05)
            l.pintar(ojo, "#1C1A18", 0.95)
            l.altura(ojo, 0.25)
        pelado = _ss(0.4, 0.6, l.f(5, 3, k=4))
        l.pintar(pelado, "#D9B890", 0.25)
        return l
    x = l.U * 7 + l.f(2, 4, k=1, oct=3) * 0.8
    fx = np.abs(((x) % 1.0) - 0.5) * 2
    placa = np.floor(l.V * 5 + l.f(7, 2, k=2) * 0.8)
    idp = _hash(np.floor(x).astype(np.int64), placa.astype(np.int64), l.s)
    grieta_h = np.abs(((l.V * 5 + l.f(7, 2, k=2) * 0.8) % 1.0) - 0.5) > 0.46
    perfil = _ss(0.0, 0.7, 1 - fx)
    col = c[None, None, :] * (0.45 + 0.55 * perfil + 0.12 * (idp - 0.5) + 0.06 * l.f(16, k=3))[..., None]
    l.pintar(1.0, col)
    l.pintar(grieta_h & (perfil > 0.3), "#1A120C", 0.6)
    l.alt[:] = 0.1 + 0.7 * perfil - 0.2 * grieta_h
    liq = _ss(0.4, 0.65, l.f(6, k=4)) * (perfil > 0.4)
    l.pintar(liq, "#8C9A6A", 0.55)
    musgo = _ss(0.25, 0.0, l.V) * np.clip(0.5 + l.f(8, k=5), 0, 1)
    l.pintar(musgo, "#4A6228", 0.5)
    return l


def col_casilla():
    """Coles: hojas grandes azuladas con nervios claros."""
    l = Lienzo(50, rug=0.55, fuerza=3.5)
    l.pintar(1.0, _hex("#3E6A3A") * 0.7)
    rng = np.random.default_rng(50)
    for i in range(40):
        cx, cy = rng.uniform(0, 1, 2)
        r = rng.uniform(0.07, 0.12)
        dx = (l.U - cx + 0.5) % 1.0 - 0.5
        dy = (l.V - cy + 0.5) % 1.0 - 0.5
        d = np.hypot(dx, dy)
        hoja = d < r * (0.9 + 0.1 * np.sin(np.arctan2(dy, dx) * 9))
        a = np.arctan2(dy, dx)
        nervio = np.abs(((a / (2 * np.pi) * 7) % 1.0) - 0.5) > 0.46
        c = _hex("#7DB06A") * rng.uniform(0.8, 1.15)
        col = c[None, None, :] * (0.7 + 0.4 * (1 - d / r) + 0.1 * (i / 40))[..., None]
        l.pintar(hoja, col)
        l.pintar(hoja & nervio & (d < r * 0.9), "#D6E8C0", 0.5)
        l.pintar(hoja & (d > r * 0.8), "#000000", 0.2)
        l.altura(hoja, 0.2 + 0.6 * (i / 40) + 0.2 * (1 - d / r))
    return l


def calabaza():
    """Calabazas: gajos verticales con sombra entre gajos, motas y vetas claras."""
    l = Lienzo(52, rug=0.5, fuerza=3.5)
    fg = (l.U * 6) % 1.0
    lomo = np.sin(fg * np.pi)
    col = _hex("#E08A2E")[None, None, :] * (0.6 + 0.45 * lomo + 0.06 * l.f(6, k=1))[..., None]
    l.pintar(1.0, col)
    vet = _ss(0.02, 0.0, np.abs(l.f(3, 24, k=2, oct=2)))
    l.pintar(vet, "#F6C070", 0.4)
    l.pintar(_ss(0.85, 0.95, l.r(32, k=3)), "#B86A20", 0.6)
    l.pintar(_ss(0.4, 0.7, l.f(5, k=4)), "#6A6A2A", 0.25)
    l.alt[:] = 0.2 + 0.6 * lomo
    return l


def _opaco(color, grano=0.05, semilla=0, rug=0.85):
    """Color opaco con variación multi-octava (sin ruido de píxel)."""
    l = Lienzo(semilla, rug=rug)
    t = l.f(4, k=1) * 0.5 + l.f(12, k=2) * 0.3 + l.f(36, k=3, oct=2) * 0.2
    l.pintar(1.0, _hex(color)[None, None, :] * (1 + grano * 1.5 * t)[..., None])
    l.alt[:] = 0.5 + 0.1 * t
    return l


def piedra_lisa(color, semilla, var=0.1):
    """Piedra de cantería (bloques grandes estirados sobre la cara): motas, granos, vetas, alguna fisura y líquenes."""
    l = Lienzo(semilla, rug=0.9, fuerza=3.0)
    d = np.full(l.U.shape, 10.0, np.float32)
    piedra(l, 1.0, color, d, np.full(l.U.shape, 0.5, np.float32), k=1, var=0.0, bisel=0.1)
    vetas = _ss(0.03, 0.0, np.abs(fbm(l.U * 3 + l.V * 1.5, l.V * 3, l.s + 5, 4, 3, 3) - 0.1))
    l.pintar(vetas, "#FFFFFF", 0.12)
    estrato = l.f(2, 10, k=6, oct=3)
    l.pintar(np.clip(estrato, 0, 1), "#000000", 0.08)
    l.pintar(np.clip(-estrato, 0, 1), "#FFFFFF", 0.06)
    fis = _ss(0.012, 0.0, np.abs(l.f(4, k=7, oct=3))) * _ss(0.2, 0.45, l.f(3, k=8))
    l.pintar(fis, "#1C1813", 0.55)
    l.altura(fis, l.alt - 0.25)
    liq = _ss(0.5, 0.7, l.f(6, k=9)) * _ss(0.7, 0.85, l.r(28, k=10) + 0.3 * np.clip(l.f(6, k=9), 0, 1))
    l.pintar(liq, "#CFCBA0", 0.45, rug=0.97)
    musgo = _ss(0.22, 0.0, l.V + 0.06 * l.f(6, k=11)) * np.clip(0.3 + l.f(10, k=12) * 1.3, 0, 1)
    l.pintar(musgo, "#4F6B30", 0.45, rug=0.97)
    return l


def hierro():
    """Hierro forjado: martillado, arañazos claros, óxido en manchas con chorreones hacia abajo (el óxido no es
    metálico y es rugoso)."""
    l = Lienzo(36, rug=0.5, fuerza=2.0)
    t = l.f(6, k=1) * 0.6 + l.f(18, k=2) * 0.4
    l.pintar(1.0, _hex("#34353A")[None, None, :] * (1 + 0.18 * t)[..., None], rug=0.45, met=1.0)
    l.rug[:] = 0.42 + 0.12 * l.f(8, k=3)
    golpes = l.f(14, k=4, oct=2)
    l.alt[:] = 0.5 + 0.12 * golpes
    rng = np.random.default_rng(36)
    for i in range(34):
        x0, y0 = rng.uniform(0, 1, 2)
        ang = rng.uniform(0, np.pi)
        L = rng.uniform(0.04, 0.18)
        d, _ = _segmento(l.U, l.V, x0, y0, x0 + math.cos(ang) * L, y0 + math.sin(ang) * L)
        ar = _ss(0.003, 0.0, d)
        l.pintar(ar, "#9EA2A8", 0.35, rug=0.3)
    ox = _ss(0.5, 0.75, l.f(5, k=5) + 0.25 * _ss(0.3, 0.0, l.V))
    chorro = _ss(0.35, 0.7, l.f(12, 2, k=6) + ox * 0.5) * _ss(0.2, 0.6, l.f(3, k=7) + 0.3)
    l.pintar(chorro, "#6A3E22", 0.35, rug=0.85, met=0.4)
    oxc = _hex("#7A4A2A")[None, None, :] * (1 + 0.25 * l.f(20, k=8, oct=2))[..., None]
    l.pintar(ox, oxc, 0.95, rug=0.92, met=0.1)
    l.pintar(ox * _ss(0.8, 0.92, l.r(40, k=9)), "#A9632C", 0.8)
    l.altura(ox, l.alt + 0.12 * ox + 0.05 * l.f(24, k=10))
    return l


def oro():
    """Oro: pulido con pátina oscura en las zonas bajas, arañazos finos y brillo variable."""
    l = Lienzo(37, rug=0.3, fuerza=1.6)
    t = l.f(4, k=1) * 0.6 + l.f(14, k=2) * 0.4
    cep = l.f(2, 40, k=3, oct=2)
    l.pintar(1.0, _hex("#D2A64A")[None, None, :] * (1 + 0.12 * t + 0.05 * cep)[..., None], rug=0.28, met=1.0)
    pat = _ss(0.35, 0.75, l.f(6, k=4)) * (0.6 + 0.4 * l.r(24, k=5))
    l.pintar(pat, "#7A6230", 0.4, rug=0.55)
    l.rug[:] = np.clip(0.25 + 0.08 * cep + 0.25 * pat, 0, 1)
    rng = np.random.default_rng(37)
    for i in range(24):
        x0, y0 = rng.uniform(0, 1, 2)
        ang = rng.uniform(0, np.pi)
        L = rng.uniform(0.03, 0.12)
        d, _ = _segmento(l.U, l.V, x0, y0, x0 + math.cos(ang) * L, y0 + math.sin(ang) * L)
        l.pintar(_ss(0.0025, 0.0, d), "#FFF0B8", 0.3)
    l.alt[:] = 0.5 + 0.08 * t
    return l


def vidrio():
    l = Lienzo(38, rug=0.08, fuerza=1.0)
    _cristal(l, 1.0, 1, 0.0, 1.0, reflejo=False)
    l.pintar(_ss(0.3, 0.6, l.f(4, k=3)), "#7A8A9A", 0.12, rug=0.3)
    l.rug[:] = np.clip(0.06 + 0.25 * _ss(0.2, 0.7, l.f(5, k=4)), 0, 1)
    return l


def luz():
    l = Lienzo(39, rug=0.5, fuerza=0.5)
    d = np.hypot(l.U - 0.5, l.V - 0.5)
    col = _hex("#FFC46E")[None, None, :] * (1.08 - 0.25 * d + 0.03 * l.f(6, k=1))[..., None]
    l.pintar(1.0, col)
    return l


def agua():
    """Agua: ondas periódicas en varias direcciones con brillos y profundidad variable (lisa: rugosidad baja)."""
    l = Lienzo(40, rug=0.06, fuerza=1.2)
    o = 0.0
    for (a, b, f) in ((3, 1, 0.0), (-2, 3, 1.3), (1, -4, 2.1), (5, 2, 0.7)):
        o = o + np.sin(2 * np.pi * (a * l.U + b * l.V) + f + 1.5 * l.f(3, k=a + 5, oct=2))
    o = o / 4
    prof = l.f(3, k=1)
    col = _hex("#5B9AA6")[None, None, :] * (0.92 + 0.12 * o + 0.1 * prof)[..., None]
    l.pintar(1.0, col)
    l.pintar(_ss(0.55, 0.85, o), "#E8F4F4", 0.35)
    l.alt[:] = 0.5 + 0.2 * o
    l.rug[:] = 0.05 + 0.05 * np.clip(prof, 0, 1)
    return l


def silueta_fachada():
    """Fachada lejana OPACA (para la silueta de Aurora, que es una sola malla sin color de instancia): yeso crema con
    dos pisos de ventanas."""
    l = Lienzo(60, rug=0.9, fuerza=1.5)
    t = l.f(3, k=1) * 0.6 + l.f(10, k=2) * 0.4
    l.pintar(1.0, _hex("#EADCC0")[None, None, :] * (1 + 0.06 * t)[..., None])
    chorretones(l, np.ones_like(l.U), 3, 0.08)
    for fila in range(2):
        for j in range(4):
            u0 = 0.06 + j * 0.24
            v0 = 0.12 + fila * 0.5
            vid = l.caja(u0, v0, u0 + 0.12, v0 + 0.22)
            _cristal(l, vid, 4 + j + fila * 4, v0, v0 + 0.22, reflejo=False)
            l.pintar(l.caja(u0 + 0.055, v0, u0 + 0.065, v0 + 0.22), "#3A3026")
            l.pintar(l.caja(u0 - 0.03, v0, u0, v0 + 0.22) | l.caja(u0 + 0.12, v0, u0 + 0.15, v0 + 0.22), VERDE_CONTRA)
            l.pintar(l.caja(u0 - 0.02, v0 - 0.025, u0 + 0.14, v0), "#C8BEAC")
            chorretones(l, l.caja(u0, v0 - 0.15, u0 + 0.12, v0 - 0.025), 10 + j, 0.15)
    l.pintar(l.V < 0.06, _hex("#A2998A")[None, None, :] * (1 + 0.08 * t)[..., None])
    l.pintar(l.V < 0.03, "#4D6232", 0.3)
    return l


def silueta_teja():
    """Tejado lejano OPACO: hiladas con tonos de teja variados y algo de liquen."""
    l = Lienzo(61, rug=0.85, fuerza=2.5)
    fila = np.floor(l.V * 8).astype(np.int64)
    x = l.U * 6 + np.mod(fila, 2) * 0.5
    ident = _hash(np.mod(fila, 8), np.mod(np.floor(x).astype(np.int64), 6), l.s)
    col = _hex("#B04A30")[None, None, :] * (0.88 + 0.22 * ident + 0.06 * l.f(8, k=1))[..., None]
    l.pintar(1.0, col)
    dv = (l.V * 8) % 1.0
    l.pintar(dv < 0.12, "#000000", 0.35)
    l.pintar(_ss(0.7, 1.0, dv), "#000000", 0.15)
    l.pintar((x % 1.0) < 0.04, "#000000", 0.2)
    l.pintar(_ss(0.55, 0.8, l.f(5, k=2)) * l.r(32, k=3), "#C9C49C", 0.2)
    l.alt[:] = 0.3 + 0.5 * (1 - dv)
    return l


def casilla(nombre):
    """El lienzo pintado de una casilla."""
    if nombre.startswith(("pared_", "entramado_")):
        return pared(nombre)
    fijos = {
        "piedra_clara": lambda: piedra_lisa("#CBC1B0", 30), "piedra_media": lambda: piedra_lisa("#A2998A", 31),
        "piedra_oscura": lambda: piedra_lisa("#6F6A62", 32),
        "madera_clara": lambda: _madera_casilla("#B48858", 33),
        "madera_media": lambda: _madera_casilla("#8A6340", 34),
        "madera_oscura": lambda: _madera_casilla("#5C4130", 35),
        "hierro": hierro, "oro": oro, "vidrio": vidrio, "luz": luz, "agua": agua,
        "hoja_verde": lambda: hojas("#5C9A3B", 41), "hoja_clara": lambda: hojas("#86B846", 42),
        "hoja_oscura": lambda: hojas("#3E7838", 43), "hoja_pino": lambda: hojas("#3B6A3F", 44, pino=True),
        "flor_rosa": lambda: hojas("#F2A9C2", 45, flor=True), "corteza": lambda: corteza("#6B4E37", 46),
        "abedul": lambda: corteza("#E7E2D6", 47, abedul=True), "hierba": hierba,
        "flores": flores, "trigo": lambda: surcos("#DDB65A", "#8A7035", 49, "trigo"), "col": col_casilla,
        "tierra_arada": lambda: surcos("#7A5A3E", "#5E432D", 51, "tierra"), "calabaza": calabaza,
        "fruta": fruta, "paja": lambda: surcos("#D6B663", "#9A7E3A", 53, "paja"),
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


def _madera_casilla(color, semilla):
    """Madera maciza (vigas, postes, tablas): fibra a lo largo de u, periódica en u y en v, con nudos y fisuras."""
    l = Lienzo(semilla, rug=0.62, fuerza=2.8)
    madera(l, 1.0, color, l.U * 2, l.V * 1, k=1, anillos=9, contraste=0.3, pa=2, pb=1,
           nudos=((0.62, 0.35, 0.03), (1.5, 0.78, 0.022)))
    l.pintar(_ss(0.4, 0.7, l.f(4, k=5)), "#1E140C", 0.12)
    return l


BRILLO = {"vidrio": 1.0, "agua": 1.0, "hierro": 0.5, "oro": 0.7}


def _suavizar(h):
    """Desenfoque binomial 3 × 3 con envoltura (las casillas que se repiten no tienen costura)."""
    h = (np.roll(h, 1, 0) + 2 * h + np.roll(h, -1, 0)) / 4
    return (np.roll(h, 1, 1) + 2 * h + np.roll(h, -1, 1)) / 4


def normal_de_altura(alt, fuerza):
    """Mapa de normales (espacio tangente, OpenGL: +X = +u a la derecha, +Y = +v hacia arriba) desde la altura."""
    h = _suavizar(alt.astype(np.float32))
    dhdu = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) * 0.5
    dhdv = -(np.roll(h, -1, 0) - np.roll(h, 1, 0)) * 0.5  # la fila crece hacia abajo; la v hacia arriba
    n = np.stack([-dhdu * fuerza, -dhdv * fuerza, np.ones_like(h)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    return n * 0.5 + 0.5


def generar(carpeta):
    """Pinta el atlas (RGBA), su mapa de datos (RGB) y los mapas PBR, todos con la misma distribución:
      datos: R = luz propia: 0,5 en los cristales (se encienden al atardecer), 1 en los faroles (siempre algo
             encendidos); G = brillo (1 = liso y reflectante: cristal, agua; 0 = mate). Solo lo usan los renders.
      atlas_kit_normal.png (OpenGL), atlas_kit_roughness.png y atlas_kit_metalness.png (gris de 8 bits): para la
      SurfaceAppearance de Roblox (ColorMap = atlas_kit.png con AlphaMode Overlay).
    Devuelve (ruta_atlas, ruta_datos)."""
    img = np.zeros((TAM, TAM, 4), np.float32)
    datos = np.zeros((TAM, TAM, 3), np.float32)
    nor = np.zeros((TAM, TAM, 3), np.float32)
    rug = np.zeros((TAM, TAM), np.float32)
    met = np.zeros((TAM, TAM), np.float32)
    for i, nombre in enumerate(CASILLAS):
        l = casilla(nombre)
        col, fila = i % N, i // N
        sl = (slice(fila * CASILLA, (fila + 1) * CASILLA), slice(col * CASILLA, (col + 1) * CASILLA))
        img[sl] = l.imagen()
        em = np.full(l.em.shape, 1.0) if nombre == "luz" else l.em
        datos[sl + (0,)] = em
        datos[sl + (1,)] = np.maximum(BRILLO.get(nombre, 0.0), (l.em > 0.25) * 1.0 if nombre != "luz" else 0.0)
        nor[sl] = normal_de_altura(l.alt, l.fuerza)
        rug[sl] = np.clip(l.rug, 0.02, 1)
        met[sl] = np.clip(l.met, 0, 1)
    os.makedirs(carpeta, exist_ok=True)
    ra = os.path.join(carpeta, "atlas_kit.png")
    rd = os.path.join(carpeta, "atlas_kit_datos.png")

    def u8(x):
        return (np.clip(x, 0, 1) * 255 + 0.5).astype(np.uint8)

    Image.fromarray(u8(img), "RGBA").save(ra, optimize=True)
    Image.fromarray(u8(datos), "RGB").save(rd, optimize=True)
    nor_rgba = np.concatenate([u8(nor), np.full((TAM, TAM, 1), 255, np.uint8)], -1)
    Image.fromarray(nor_rgba, "RGBA").save(os.path.join(carpeta, "atlas_kit_normal.png"), optimize=True)
    Image.fromarray(u8(rug), "L").save(os.path.join(carpeta, "atlas_kit_roughness.png"), optimize=True)
    Image.fromarray(u8(met), "L").save(os.path.join(carpeta, "atlas_kit_metalness.png"), optimize=True)
    return ra, rd


if __name__ == "__main__":
    import sys

    print(generar(sys.argv[1] if len(sys.argv) > 1 else "."))
