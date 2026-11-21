"""
Generador de atlas PBR tileable para la estética humana: metal blindado con paneles, juntas y remaches.

Produce los 5 mapas que pide la especificación, listos para una SurfaceAppearance en Roblox:
  *_color.png      albedo (gris-azulado con paneles, rayado de cepillado y oclusión en las juntas)
  *_normal.png     relieve de juntas, remaches y rayado (tangent space, Y+)
  *_roughness.png  rugosidad (juntas más rugosas, placas más pulidas)
  *_metalness.png  metalicidad (casi todo metal; juntas un poco menos)
  *_emision.png    máscara de emisión (negra: el neón va en piezas aparte)

Es un patrón TILEABLE pensado para repetirse sobre las piezas: el director pone StudsPerTile en la
SurfaceAppearance. No sustituye al horneado por nave (color+AO+normal ajustado a la malla), que se hace aparte.
"""

import numpy as np
from PIL import Image

# Paleta base (sRGB 0-255) del casco humano.
BASE = (90, 107, 134)       # gris-azulado
JUNTA = (34, 40, 52)        # grafito de las juntas
REMACHE = (150, 165, 190)   # brillo del remache


def _ruido(tam, escala, semilla):
    """Ruido suave (valor) por interpolación de una rejilla aleatoria pequeña."""
    rng = np.random.default_rng(semilla)
    g = rng.random((escala + 1, escala + 1)).astype(np.float32)
    g[-1, :] = g[0, :]  # tileable
    g[:, -1] = g[:, 0]
    ys = np.linspace(0, escala, tam, endpoint=False)
    xs = np.linspace(0, escala, tam, endpoint=False)
    y0 = np.floor(ys).astype(int); x0 = np.floor(xs).astype(int)
    fy = (ys - y0)[:, None]; fx = (xs - x0)[None, :]
    def s(t):
        return t * t * (3 - 2 * t)
    fy, fx = s(fy), s(fx)
    a = g[y0][:, x0]; b = g[y0][:, x0 + 1]; cc = g[y0 + 1][:, x0]; d = g[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (cc * (1 - fx) + d * fx) * fy


def _mascaras(tam, celdas):
    """Devuelve (junta, remache, altura) tileables: junta=líneas de rejilla, remache=puntos, altura para normales."""
    paso = tam // celdas
    xx, yy = np.meshgrid(np.arange(tam), np.arange(tam))
    dx = np.minimum(xx % paso, paso - (xx % paso))
    dy = np.minimum(yy % paso, paso - (yy % paso))
    junta = (np.minimum(dx, dy) < max(2, paso // 28)).astype(np.float32)
    # Remaches: cerca de las esquinas de cada celda.
    cx = (xx % paso); cy = (yy % paso)
    borde = paso // 8
    r = paso // 22 + 1
    cerca = (((np.minimum(cx, paso - cx) - borde) ** 2 + (np.minimum(cy, paso - cy) - borde) ** 2) < r * r)
    remache = cerca.astype(np.float32)
    # Altura: placa alta, junta hundida, remache sobresale, + rayado fino + ruido de superficie.
    raya = 0.5 + 0.5 * np.sin(yy / 2.0 + _ruido(tam, 48, 7) * 6)
    altura = 0.7 + 0.1 * _ruido(tam, 24, 3) + 0.04 * raya
    altura = altura * (1 - 0.85 * junta) + 0.18 * remache
    return junta, remache, altura, raya


def _normal_desde_altura(altura, fuerza=2.2):
    gy, gx = np.gradient(altura.astype(np.float32))
    nx = -gx * fuerza; ny = -gy * fuerza; nz = np.ones_like(altura)
    ln = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([nx / ln, ny / ln, nz / ln], axis=-1)
    return ((n * 0.5 + 0.5) * 255).astype(np.uint8)


def generar(ruta_base, tam=2048, celdas=8):
    """Escribe los 5 PNG en <ruta_base>_{color,normal,roughness,metalness,emision}.png."""
    junta, remache, altura, raya = _mascaras(tam, celdas)
    sombra = 0.6 + 0.4 * _ruido(tam, 20, 11)  # variación de tono entre placas

    base = np.array(BASE, np.float32)[None, None, :]
    jcol = np.array(JUNTA, np.float32)[None, None, :]
    rcol = np.array(REMACHE, np.float32)[None, None, :]
    col = base * (0.82 + 0.25 * sombra[..., None])
    col = col * (0.9 + 0.12 * raya[..., None])          # rayado de cepillado
    col = col * (1 - junta[..., None]) + jcol * junta[..., None]
    col = col * (1 - remache[..., None]) + rcol * remache[..., None]
    col = np.clip(col, 0, 255).astype(np.uint8)
    Image.fromarray(col, "RGB").save(f"{ruta_base}_color.png")

    Image.fromarray(_normal_desde_altura(altura), "RGB").save(f"{ruta_base}_normal.png")

    rug = 0.42 + 0.10 * raya + 0.35 * junta + 0.08 * (1 - sombra)
    rug = np.clip(rug, 0, 1)
    Image.fromarray((rug * 255).astype(np.uint8), "L").save(f"{ruta_base}_roughness.png")

    met = np.clip(0.9 - 0.5 * junta, 0, 1)
    Image.fromarray((met * 255).astype(np.uint8), "L").save(f"{ruta_base}_metalness.png")

    Image.fromarray(np.zeros((tam, tam), np.uint8), "L").save(f"{ruta_base}_emision.png")
    print(f"[ok] atlas PBR: {ruta_base}_*.png ({tam}px)")


if __name__ == "__main__":
    import sys
    generar(sys.argv[1] if len(sys.argv) > 1 else "atlas", int(sys.argv[2]) if len(sys.argv) > 2 else 2048)
