"""
Comprueba el entregable: importa clinica.fbx en una escena vacía, le pone las cinco texturas del atlas y renderiza
los primeros planos (clinica_detalles.png). Si algo falla aquí, fallará también en Studio.

    python pueblo/clinica/herramientas/vista_fbx.py --carpeta pueblo/clinica [--muestras 64]
"""

import argparse
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402

import pipeline as P  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--carpeta", default=os.path.join(AQUI, ".."))
    ap.add_argument("--tmp", default=os.path.join(AQUI, "..", "_tmp"))
    ap.add_argument("--muestras", type=int, default=64)
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    carpeta = os.path.abspath(args.carpeta)

    P.escena_vacia()
    bpy.ops.import_scene.fbx(filepath=os.path.join(carpeta, "clinica.fbx"))
    rutas = {k: os.path.join(carpeta, f"clinica_{k}.png")
             for k in ("color", "normal", "roughness", "metalness", "emision")}
    atlas = P.material_atlas(rutas)
    objs = [o for o in bpy.context.scene.objects if o.type == "MESH"]
    for o in objs:
        o.data.materials.clear()
        o.data.materials.append(atlas)
    print("piezas:", len(objs), "triángulos:", sum(P.triangulos(o) for o in objs))
    P.preparar_luz(bpy.context.scene)
    rd = P.renderizar_detalles(os.path.join(os.path.abspath(args.tmp), "detalles"), girado=True, tam=760,
                               muestras=args.muestras)
    P.hoja_contactos(rd, os.path.join(carpeta, "clinica_detalles.png"),
                     "Clínica Colonial — primeros planos (FBX reimportado + atlas 2048)",
                     ["Renderizado desde clinica.fbx tal como se entrega, con las cinco texturas del atlas"])


if __name__ == "__main__":
    main()
