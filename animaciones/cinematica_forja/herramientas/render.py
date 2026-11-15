"""
Render de la cinemática con Cycles (CPU).

    python render.py --previo 0,50,150 [--ancho 640 --alto 360 --muestras 16]   fotogramas sueltos para revisar
    python render.py --completo [--desde 0 --hasta 435]                         todos los fotogramas a 1920x1080

Los fotogramas salen como PNG en --carpeta; video.py los junta en el MP4.
Las partículas se simulan avanzando fotograma a fotograma desde el 0 (su caché se llena por el camino), así que un
fotograma suelto sale igual que en el render completo.
"""

import argparse
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402

import escena as es  # noqa: E402
import hornear  # noqa: E402
import linea_tiempo as lt  # noqa: E402


def preparar(ancho, alto, muestras, blend=None):
    if blend and os.path.exists(blend):
        bpy.ops.wm.open_mainfile(filepath=blend)
        scn = bpy.context.scene
    else:
        scn, obs = hornear.montar()
        hornear.hornear(scn, obs)
        if blend:
            bpy.ops.wm.save_as_mainfile(filepath=blend)
    es.ajustes_render(scn, ancho, alto, muestras)
    es.composicion(scn)
    return scn


def renderizar(scn, fotogramas, carpeta, prefijo="f"):
    os.makedirs(carpeta, exist_ok=True)
    fotogramas = sorted(fotogramas)
    hecho = -1
    for f in fotogramas:
        for g in range(hecho + 1, f):  # avanza la simulación de partículas
            scn.frame_set(g)
        scn.frame_set(f)
        hecho = f
        ruta = os.path.join(carpeta, f"{prefijo}{f:04d}.png")
        if os.path.exists(ruta) and os.path.getsize(ruta) > 0:
            continue
        t = time.time()
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        print(f"[render] {ruta} {time.time() - t:.1f} s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--previo", default="")
    ap.add_argument("--completo", action="store_true")
    ap.add_argument("--desde", type=int, default=0)
    ap.add_argument("--hasta", type=int, default=lt.DURACION - 1)
    ap.add_argument("--ancho", type=int, default=1920)
    ap.add_argument("--alto", type=int, default=1080)
    ap.add_argument("--muestras", type=int, default=48)
    ap.add_argument("--carpeta", default=os.path.join(AQUI, "..", "_fotogramas"))
    ap.add_argument("--blend", default="")
    a = ap.parse_args()
    scn = preparar(a.ancho, a.alto, a.muestras, a.blend or None)
    if a.previo:
        fotogramas = [int(x) for x in a.previo.split(",")]
    else:
        fotogramas = list(range(a.desde, a.hasta + 1))
    renderizar(scn, fotogramas, os.path.abspath(a.carpeta))


if __name__ == "__main__":
    main()
