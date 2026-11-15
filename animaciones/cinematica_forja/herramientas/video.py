"""
Junta los fotogramas renderizados en el vídeo MP4 (H.264, 1080p, 30 fps) y monta la hoja de contactos.

    python video.py --carpeta ../_fotogramas
"""

import argparse
import os
import subprocess
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402,F401  (linea_tiempo usa mathutils, que viene con bpy)
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import linea_tiempo as lt  # noqa: E402

SALIDA = os.path.abspath(os.path.join(AQUI, ".."))
# Fotogramas de la hoja de contactos: (fotograma, texto)
HOJA = [
    (16, "Llega con el lingote"),
    (50, "Sube la compuerta"),
    (74, "El lingote entra en las brasas"),
    (98, "Espera: el fuego le ilumina"),
    (116, "Saca la pieza al rojo blanco"),
    (150, "1.er martillazo"),
    (168, "2.º: toma forma"),
    (206, "4.º martillazo"),
    (233, "5.º: el más fuerte"),
    (280, "Al barril"),
    (300, "PSSSH: entra en el agua"),
    (330, "El vapor sube, la hoja se apaga"),
    (372, "La levanta"),
    (400, "Destello en el filo"),
    (426, "Fundido a negro"),
]


def fuente(tam, negrita=True):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if negrita else "")
    return ImageFont.truetype(ruta, tam) if os.path.exists(ruta) else ImageFont.load_default(tam)


def video(carpeta, ruta):
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(lt.FPS), "-start_number", "0",
           "-i", os.path.join(carpeta, "f%04d.png"), "-c:v", "libx264", "-preset", "slow", "-crf", "18",
           "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-vf", "scale=1920:1080:flags=lanczos", ruta]
    subprocess.run(cmd, check=True)
    print("[ok]", ruta)


def hoja(carpeta, ruta, cols=5, ancho=576):
    alto = ancho * 9 // 16
    cab = 92
    filas = (len(HOJA) + cols - 1) // cols
    H = Image.new("RGB", (cols * ancho, cab + filas * (alto + 34)), (12, 11, 12))
    d = ImageDraw.Draw(H)
    d.text((18, 14), "Cinemática de la forja · hoja de contactos", fill=(255, 176, 96), font=fuente(32))
    d.text((20, 58), f"{lt.DURACION / lt.FPS:.1f} s a {lt.FPS} fps · maniquí R6 · horno, yunque y barril de modelos/forja",
           fill=(200, 196, 190), font=fuente(17, False))
    for i, (f, texto) in enumerate(HOJA):
        x, y = (i % cols) * ancho, cab + (i // cols) * (alto + 34)
        im = Image.open(os.path.join(carpeta, f"f{f:04d}.png")).convert("RGB").resize((ancho, alto), Image.LANCZOS)
        H.paste(im, (x, y))
        d.text((x + 10, y + alto + 6), f"{f / lt.FPS:5.2f} s  {texto}", fill=(235, 230, 222), font=fuente(16))
    H.save(ruta)
    print("[ok]", ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--carpeta", default=os.path.join(SALIDA, "_fotogramas"))
    ap.add_argument("--video", default=os.path.join(SALIDA, "cinematica_forja_1080p.mp4"))
    ap.add_argument("--hoja", default=os.path.join(SALIDA, "cinematica_forja_hoja_de_contactos.png"))
    a = ap.parse_args()
    video(os.path.abspath(a.carpeta), a.video)
    hoja(os.path.abspath(a.carpeta), a.hoja)


if __name__ == "__main__":
    main()
