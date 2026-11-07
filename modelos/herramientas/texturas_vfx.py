"""
Texturas de los efectos de las pistolas de portales (disparo y portal). Todas son PNG RGBA de 512 como mucho,
generadas con numpy + Pillow (sin Blender), para ParticleEmitter, Beam y mallas.

  * Las de PARTÍCULA y BEAM son BLANCAS (el color lo pone ParticleEmitter.Color / Beam.Color): sirven a las dos pistolas.
  * Los REMOLINOS de las mallas llevan el color de cada portal (verde la chatarra, morado y cian la VIP).
  * Los FLIPBOOKS son una cuadrícula 4x4 de 16 fotogramas de 128 px (ParticleEmitter.FlipbookLayout = Grid4x4) y
    cierran el bucle: el fotograma 17 sería igual al 1.

Uso:  python modelos/herramientas/texturas_vfx.py --salida modelos/pistola_portales/vfx/texturas
"""

import argparse
import math
import os

import numpy as np
from PIL import Image

# --------------------------------------------------------------------------------------------------------------
# Datos ajustables
# --------------------------------------------------------------------------------------------------------------

COLORES = {
    "chatarra": {"claro": "#C8FF8A", "medio": "#7DFF3A", "oscuro": "#1B6B0C", "fondo": "#052A06"},
    "vip": {"claro": "#E8FBFF", "medio": "#3FF0FF", "morado": "#A64BFF", "oscuro": "#2A0C5C", "fondo": "#0B0420"},
}
TAM = 512
CELDA = 128  # fotograma del flipbook


def hexa(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


# --------------------------------------------------------------------------------------------------------------
# Ruido y utilidades
# --------------------------------------------------------------------------------------------------------------


def _suave(t):
    return t * t * (3 - 2 * t)


def ruido(ancho, alto, celdas_x, celdas_y, semilla, periodico_x=False, desp=(0.0, 0.0)):
    """Ruido de valor 0..1 de `celdas` celdas; `desp` desplaza el muestreo (en celdas). periodico_x: cierra en horizontal."""
    rng = np.random.default_rng(semilla)
    nx = celdas_x + 2 + int(abs(desp[0])) + 1
    ny = celdas_y + 2 + int(abs(desp[1])) + 1
    malla = rng.random((ny, nx), dtype=np.float32)
    if periodico_x:
        malla[:, celdas_x] = malla[:, 0]
        malla[:, celdas_x + 1] = malla[:, 1]
    xs = np.linspace(0, celdas_x, ancho, endpoint=False, dtype=np.float32) + desp[0]
    ys = np.linspace(0, celdas_y, alto, endpoint=False, dtype=np.float32) + desp[1]
    if periodico_x:
        xs = np.mod(xs, celdas_x)
    xi, yi = np.floor(xs).astype(int), np.floor(ys).astype(int)
    fx, fy = _suave(xs - xi)[None, :], _suave(ys - yi)[:, None]
    a = malla[yi[:, None], xi[None, :]]
    b = malla[yi[:, None], xi[None, :] + 1]
    c = malla[yi[:, None] + 1, xi[None, :]]
    d = malla[yi[:, None] + 1, xi[None, :] + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(ancho, alto, base, octavas, semilla, periodico_x=False, desp=(0.0, 0.0)):
    total, amp, norma = np.zeros((alto, ancho), dtype=np.float32), 1.0, 0.0
    for o in range(octavas):
        f = base * 2 ** o
        total += amp * ruido(ancho, alto, f, f if not periodico_x else max(1, f // 4), semilla + 17 * o,
                             periodico_x, (desp[0] * 2 ** o, desp[1] * 2 ** o))
        norma += amp
        amp *= 0.5
    return total / norma


def _guardar(rgb, alfa, ruta):
    """rgb (H,W,3) 0..1 y alfa (H,W) 0..1 -> PNG RGBA de 8 bits. El color se conserva donde alfa = 0 (sin halos oscuros)."""
    img = np.dstack([np.clip(rgb, 0, 1), np.clip(alfa, 0, 1)])
    Image.fromarray((img * 255 + 0.5).astype(np.uint8), "RGBA").save(ruta, optimize=True)
    print("[ok]", ruta)


def blanco(alfa, ruta):
    _guardar(np.ones(alfa.shape + (3,), dtype=np.float32), alfa, ruta)


def rejilla(n):
    y, x = np.mgrid[0:n, 0:n].astype(np.float32)
    return (x + 0.5) / n * 2 - 1, (y + 0.5) / n * 2 - 1


# --------------------------------------------------------------------------------------------------------------
# Partículas (blancas)
# --------------------------------------------------------------------------------------------------------------


def brillo(n=128):
    x, y = rejilla(n)
    r = np.sqrt(x * x + y * y)
    return np.clip(1 - r, 0, 1) ** 2.2 * 1.0 + np.exp(-r * r * 40) * 0.6


def chispa(n=128):
    """Trazo horizontal con el centro caliente y las puntas afiladas: con orientación «Velocity» se estira solo."""
    x, y = rejilla(n)
    largo = np.clip(1 - np.abs(x), 0, 1) ** 1.3
    grosor = 0.07 + 0.05 * (1 - np.abs(x))
    a = np.exp(-(y / grosor) ** 2) * largo
    return np.clip(a + np.exp(-(x * x * 30 + y * y * 400)) * 0.8, 0, 1)


def estrella(n=256):
    """Estrella de 4 puntas con 4 más pequeñas en diagonal: el destello del fogonazo."""
    x, y = rejilla(n)
    r = np.sqrt(x * x + y * y) + 1e-6
    a = np.exp(-(np.abs(x) * np.abs(y)) * 90) * np.clip(1 - r, 0, 1) ** 1.2
    d = np.exp(-(np.abs(x - y) * np.abs(x + y)) * 160) * np.clip(1 - r * 1.5, 0, 1) ** 1.5 * 0.7
    return np.clip(a + d + np.exp(-r * r * 60), 0, 1)


def onda(n=256):
    """Anillo fino con el borde exterior más brillante: la onda expansiva (se agranda y se desvanece)."""
    x, y = rejilla(n)
    r = np.sqrt(x * x + y * y)
    anillo = np.exp(-((r - 0.82) / 0.07) ** 2)
    interior = np.clip(1 - np.abs(r - 0.7) / 0.2, 0, 1) ** 2 * 0.25
    return np.clip(anillo + interior, 0, 1) * np.clip((1 - r) * 8, 0, 1)


def humo(n=128, semilla=3):
    x, y = rejilla(n)
    r = np.sqrt(x * x + y * y)
    return np.clip(fbm(n, n, 3, 4, semilla) * 1.6 - 0.35, 0, 1) * np.clip((1 - r) * 3, 0, 1)


# --------------------------------------------------------------------------------------------------------------
# Beams (blancos, 512 x 64, se repiten a lo largo del beam: cierran en horizontal)
# --------------------------------------------------------------------------------------------------------------


def beam_energia(ancho=512, alto=64):
    """Estela con pulsos: banda central caliente y bordes suaves; los pulsos se mueven al animar la textura."""
    y = (np.arange(alto, dtype=np.float32) + 0.5) / alto * 2 - 1
    x = np.arange(ancho, dtype=np.float32) / ancho
    nucleo = np.exp(-(y / 0.22) ** 2)[:, None]
    halo = np.exp(-(y / 0.62) ** 2)[:, None] * 0.35
    pulso = 0.62 + 0.38 * np.cos(2 * math.pi * x * 4)[None, :]
    chispas = (fbm(ancho, alto, 8, 2, 9, periodico_x=True) > 0.62) * 0.35
    return np.clip((nucleo + halo) * pulso + chispas * nucleo, 0, 1)


def beam_rayo(ancho=512, alto=64, semilla=21):
    """Rayo irregular: un hilo brillante que serpentea, con ramas pequeñas. Cierra en horizontal."""
    rng = np.random.default_rng(semilla)
    puntos = 16
    ys = 0.5 + np.cumsum(rng.normal(0, 0.09, puntos))
    ys -= np.linspace(ys[0], ys[0], puntos)
    ys += np.linspace(0, -(ys[-1] - ys[0]), puntos)  # que el último punto = el primero (cierra el bucle)
    ys = 0.5 + (ys - ys.mean()) * 1.2
    xs = np.linspace(0, ancho, puntos, endpoint=False)
    x = np.arange(ancho)
    centro = np.interp(x, np.append(xs, ancho), np.append(ys, ys[0])) * alto
    yy = np.arange(alto, dtype=np.float32)[:, None]
    d = np.abs(yy - centro[None, :])
    hilo = np.exp(-(d / 3.2) ** 2) + 0.4 * np.exp(-(d / 9.0) ** 2)
    rama = np.zeros_like(hilo)
    for k in range(5):
        x0 = rng.integers(0, ancho)
        dirc = rng.choice([-1, 1])
        for t in range(26):
            px, py = (x0 + t * 3) % ancho, int(centro[(x0 + t * 3) % ancho] + dirc * t * 0.5 + rng.normal(0, 0.6))
            if 0 <= py < alto:
                rama[max(py - 1, 0):py + 2, px] = np.maximum(rama[max(py - 1, 0):py + 2, px], 0.8 * (1 - t / 26))
    return np.clip(hilo + rama, 0, 1)


# --------------------------------------------------------------------------------------------------------------
# Remolinos con color (mallas y flipbooks)
# --------------------------------------------------------------------------------------------------------------


def _espiral(x, y, brazos, apretado, giro):
    """Fase de una espiral logarítmica: 0..1 repetido, `giro` en radianes."""
    r = np.sqrt(x * x + y * y) + 1e-6
    th = np.arctan2(y, x)
    return (th + giro) * brazos / (2 * math.pi) + apretado * np.log(r + 0.04), r


def remolino_vip(n, giro=0.0):
    """Espiral limpia y perfecta: 3 brazos cian con filo blanco sobre un fondo morado profundo, centro oscuro."""
    c = COLORES["vip"]
    x, y = rejilla(n)
    fase, r = _espiral(x, y, 3, -1.15, giro)
    brazo = np.cos(fase * 2 * math.pi) * 0.5 + 0.5
    cuerpo = _suave(np.clip((brazo - 0.35) / 0.5, 0, 1))
    filo = np.exp(-((brazo - 0.97) / 0.045) ** 2) + np.exp(-((brazo - 0.03) / 0.03) ** 2) * 0.0
    fino = (np.cos(fase * 2 * math.pi * 3) * 0.5 + 0.5) ** 12 * 0.5  # hilos finos entre brazos
    centro = np.clip((r - 0.06) / 0.5, 0, 1)
    fondo = hexa(c["fondo"]) * (1 - 0.5 * r[..., None]) + hexa(c["oscuro"]) * (0.3 + 0.7 * r[..., None]) * 0.6
    valle = hexa(c["morado"]) * ((1 - cuerpo) * 0.75 * np.clip(r * 1.6, 0, 1))[..., None]  # entre brazos: morado
    brazos = hexa(c["medio"]) * (cuerpo * 0.95)[..., None]  # los brazos: cian
    rgb = fondo + valle + brazos * (0.35 + 0.65 * centro[..., None])
    rgb = rgb + hexa(c["claro"]) * (filo[..., None] * 0.6 + fino[..., None] * 0.25) * centro[..., None]
    pozo = np.exp(-(r / 0.09) ** 2)[..., None]  # el centro se hunde en negro-violeta
    rgb = rgb * (1 - 0.8 * pozo) + hexa(c["fondo"]) * 0.8 * pozo
    alfa = np.clip((1.0 - r) / 0.16, 0, 1) * 0.97
    return rgb, alfa


def remolino_chatarra(n, fase_ruido=0.0, semilla=5):
    """Remolino inestable: 4 brazos irregulares (la espiral se deforma con ruido), manchas, chispazos verdes."""
    c = COLORES["chatarra"]
    x, y = rejilla(n)
    R = 1.6  # el desplazamiento del ruido recorre un círculo: el bucle cierra
    dx, dy = R * math.cos(fase_ruido), R * math.sin(fase_ruido)
    ru1 = fbm(n, n, 3, 4, semilla, desp=(dx, dy))
    ru2 = fbm(n, n, 7, 3, semilla + 40, desp=(dy, -dx))
    fase, r = _espiral(x + (ru1 - 0.5) * 0.22, y + (ru2 - 0.5) * 0.22, 4, -0.9, fase_ruido * 0 + 0.0)
    brazo = np.cos(fase * 2 * math.pi) * 0.5 + 0.5
    brazo = np.clip(brazo + (ru2 - 0.5) * 0.7, 0, 1)
    cuerpo = _suave(np.clip((brazo - 0.35) / 0.45, 0, 1))
    chispazo = (ru1 > 0.66) * ((ru2 - 0.4) * 2).clip(0, 1) * np.clip(r * 2, 0, 1)
    centro = np.clip((r - 0.05) / 0.4, 0, 1)
    fondo = hexa(c["fondo"]) * (1 - 0.3 * r[..., None]) + hexa(c["oscuro"]) * (0.25 + 0.5 * ru1[..., None])
    rgb = fondo + hexa(c["medio"]) * (cuerpo[..., None] * 0.7 * centro[..., None])
    rgb = rgb + hexa(c["claro"]) * (chispazo[..., None] * 0.8 + (cuerpo ** 4)[..., None] * 0.25)
    mancha = (ru2 > 0.7) * 0.5  # restos oscuros, como hollín de la chatarra
    rgb = rgb * (1 - mancha[..., None] * 0.6)
    pozo = np.exp(-(r / 0.1) ** 2)[..., None]
    rgb = rgb * (1 - 0.8 * pozo) + hexa(c["fondo"]) * 0.8 * pozo
    # borde roto: el alfa se come a mordiscos
    borde = 1.0 - 0.14 - (ru1 - 0.5) * 0.2
    alfa = np.clip((borde - r) / 0.12, 0, 1) * 0.95
    return rgb, alfa


def fondo_portal(tipo, n=TAM):
    """Fondo fijo del hueco elíptico (detrás del remolino, que es un círculo que gira): oscuro en el centro, con textura."""
    x, y = rejilla(n)
    r = np.sqrt(x * x + y * y)
    if tipo == "vip":
        c = COLORES["vip"]
        anillos = np.exp(-((r % 0.27 - 0.13) / 0.012) ** 2) * 0.35 * np.clip(r * 2, 0, 1)
        rgb = hexa(c["fondo"]) * (1 - r[..., None]) + hexa(c["oscuro"]) * (r ** 1.4)[..., None] * 0.9
        rgb = rgb + hexa(c["medio"]) * anillos[..., None] * 0.6 + hexa(c["morado"]) * (r ** 3 * 0.25)[..., None]
    else:
        c = COLORES["chatarra"]
        ru = fbm(n, n, 4, 5, 77)
        rgb = hexa(c["fondo"]) * (1 - 0.5 * r[..., None]) + hexa(c["oscuro"]) * ((r ** 1.5) * (0.4 + 0.9 * ru))[..., None]
        rgb = rgb + hexa(c["medio"]) * ((ru > 0.7) * 0.25 * r)[..., None]
    alfa = np.clip((1.0 - r) / 0.05, 0, 1) * 0.95
    return rgb, alfa


def flipbook(funcion, ruta, **kw):
    """Cuadrícula 4x4 de 16 fotogramas de CELDA x CELDA. `funcion(i, n)` -> (rgb, alfa)."""
    hoja_rgb = np.zeros((TAM, TAM, 3), dtype=np.float32)
    hoja_a = np.zeros((TAM, TAM), dtype=np.float32)
    for i in range(16):
        rgb, a = funcion(i, CELDA)
        f, c = divmod(i, 4)
        hoja_rgb[f * CELDA:(f + 1) * CELDA, c * CELDA:(c + 1) * CELDA] = rgb
        hoja_a[f * CELDA:(f + 1) * CELDA, c * CELDA:(c + 1) * CELDA] = a
    _guardar(hoja_rgb, hoja_a, ruta)


# --------------------------------------------------------------------------------------------------------------
# Bandas de los anillos (512 x 64, se repiten alrededor del aro)
# --------------------------------------------------------------------------------------------------------------


def banda_anillo(tipo):
    ancho, alto = 512, 64
    y = (np.arange(alto, dtype=np.float32) + 0.5) / alto * 2 - 1
    x = np.arange(ancho, dtype=np.float32) / ancho
    if tipo == "vip":
        c = COLORES["vip"]
        linea = np.exp(-(y / 0.18) ** 2)[:, None] * np.ones((1, ancho), dtype=np.float32)
        marcas = (np.cos(2 * math.pi * x * 24) * 0.5 + 0.5)[None, :] ** 8 * np.exp(-(y / 0.8) ** 2)[:, None] * 0.6
        rgb = hexa(c["morado"]) * (0.55 + 0.3 * np.exp(-(y / 0.8) ** 2))[:, None, None] * np.ones((1, ancho, 1))
        rgb = rgb + hexa(c["claro"]) * (linea + marcas)[..., None]
        a = np.clip(0.55 + linea * 0.45 + marcas, 0, 1)
        return rgb, a
    c = COLORES["chatarra"]
    ru = fbm(ancho, alto, 6, 4, 33, periodico_x=True)
    ru2 = fbm(ancho, alto, 14, 2, 71, periodico_x=True)
    nucleo = np.exp(-((y / 0.35) ** 2))[:, None] * (0.55 + 0.6 * ru)
    rgb = hexa(c["oscuro"]) * (0.7 + 0.5 * ru2)[..., None] + hexa(c["medio"]) * nucleo[..., None]
    rgb = rgb + hexa(c["claro"]) * ((ru > 0.72) * nucleo)[..., None] * 0.9
    a = np.clip(0.7 + nucleo * 0.3 - (ru2 > 0.8) * 0.4, 0, 1)
    return rgb, a


# --------------------------------------------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    s = a.salida
    os.makedirs(s, exist_ok=True)
    p = lambda n: os.path.join(s, n)  # noqa: E731

    # Partículas (blancas: el color va en ParticleEmitter.Color)
    blanco(brillo(), p("particula_brillo.png"))
    blanco(chispa(), p("particula_chispa.png"))
    blanco(estrella(), p("particula_estrella.png"))
    blanco(onda(), p("particula_onda.png"))
    blanco(humo(), p("particula_humo.png"))
    # Beams (blancos)
    blanco(beam_energia(), p("beam_energia.png"))
    blanco(beam_rayo(), p("beam_rayo.png"))
    # Remolinos de las mallas (con color)
    for nombre, f in (("chatarra", remolino_chatarra), ("vip", remolino_vip)):
        rgb, alfa = f(TAM)
        _guardar(rgb, alfa, p(f"portal_remolino_{nombre}.png"))
        rgb, alfa = fondo_portal(nombre)
        _guardar(rgb, alfa, p(f"portal_fondo_{nombre}.png"))
        rgb, alfa = banda_anillo(nombre)
        _guardar(rgb, alfa, p(f"anillo_banda_{nombre}.png"))
    # Flipbooks (4x4 de 128 px, blancos con la forma: en Roblox se tiñen igual que el resto de partículas)
    brazos_vip = 3

    def fotograma_vip(i, n):
        rgb, alfa = remolino_vip(n, giro=-i / 16 * 2 * math.pi / brazos_vip)
        lum = np.clip(rgb.mean(axis=2) * 1.4, 0, 1)
        return np.ones_like(rgb), alfa * lum

    def fotograma_chatarra(i, n):
        rgb, alfa = remolino_chatarra(n, fase_ruido=i / 16 * 2 * math.pi)
        lum = np.clip(rgb.mean(axis=2) * 1.6, 0, 1)
        return np.ones_like(rgb), alfa * lum

    flipbook(fotograma_vip, p("flipbook_remolino_vip.png"))
    flipbook(fotograma_chatarra, p("flipbook_remolino_chatarra.png"))


if __name__ == "__main__":
    main()
