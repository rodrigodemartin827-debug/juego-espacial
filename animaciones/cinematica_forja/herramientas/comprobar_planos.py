"""
Comprueba que en cada plano la cámara ve a su sujeto: lanza rayos desde la cámara a los puntos importantes (la pieza,
la cabeza, el punto de golpe...) en varios fotogramas del plano y dice qué objeto se cruza por delante.

    python comprobar_planos.py --blend escena.blend
"""

import argparse
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import cinematica as ci  # noqa: E402
import linea_tiempo as lt  # noqa: E402

# Qué tiene que verse en cada plano (por orden). Puntos con nombre de cinematica.punto_nombrado o «mano_martillo».
SUJETOS = {
    0: ["pecho", "cabeza"],
    1: ["compuerta", "cabeza"],
    2: ["pieza"],
    3: ["cabeza"],
    4: ["pieza", "pecho"],
    5: ["cabeza", "pecho", "golpe"],
    6: ["golpe"],
    7: ["cabeza", "pecho", "golpe"],
    8: ["cabeza", "pecho", "golpe"],
    9: ["pecho", "pieza"],
    10: ["agua"],
    11: ["agua", "cabeza"],
    12: ["hoja", "cabeza"],
}
IGNORAR = ("Vapor", "Llama", "Emisor", "Inst", "Destello", "AguaTemple", "Pieza")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    a = ap.parse_args()
    bpy.ops.wm.open_mainfile(filepath=a.blend)
    scn = bpy.context.scene
    malos = 0
    for i, p in enumerate(lt.PLANOS):
        fs = [p["inicio"] + 1, (p["inicio"] + p["fin"]) // 2, p["fin"] - 2]
        for f in fs:
            scn.frame_set(f)
            dg = bpy.context.evaluated_depsgraph_get()
            cam = scn.camera.matrix_world.translation.copy()
            est = ci.evaluar(f)
            for nombre in SUJETOS[i]:
                obj = ci.punto_nombrado(nombre, f, est)
                d = obj - cam
                origen = cam.copy()
                tapa = None
                for _ in range(8):  # salta los objetos que no tapan (volúmenes, partículas)
                    ok, loc, _n, _i, o, _m = scn.ray_cast(dg, origen, d.normalized(), distance=(obj - origen).length - 0.35)
                    if not ok:
                        break
                    if o.name.startswith(IGNORAR):
                        origen = loc + d.normalized() * 0.01
                        continue
                    if (obj - loc).length < 1.2:  # es la superficie del propio sujeto (el pecho está dentro del torso)
                        break
                    tapa = (o.name, round((loc - cam).length, 2), round(d.length, 2))
                    break
                if tapa:
                    malos += 1
                    print(f"[TAPADO] plano {i} «{p['nombre']}» f{f}: {nombre} tapado por {tapa[0]} a {tapa[1]} de {tapa[2]} studs")
    print(f"[fin] {malos} sujetos tapados")


if __name__ == "__main__":
    main()
