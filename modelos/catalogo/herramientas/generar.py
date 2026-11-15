"""
Genera modelos del catálogo.

    python generar.py r01                 # toda la ronda 1
    python generar.py r01 --solo tienda_humana,forja_humana
    python generar.py r01 --rapido        # atlas y renders pequeños, para probar formas

Cada ronda es un módulo rNN_*.py con MODELOS = [(nombre, categoria, limite, funcion), ...].
"""

import argparse
import glob
import importlib
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import lib  # noqa: E402

RAIZ = os.path.dirname(AQUI)


def escribir_montaje(carpeta, info):
    """Rellena plantilla_montar_rig.luau con las piezas, centros, pivotes y padres del modelo."""
    def v3(v):
        return f"Vector3.new({v[0]}, {v[1]}, {v[2]})"

    rig = info["rig"]
    lineas = []
    for nom, d in info["piezas"].items():
        campos = [f"centro = {v3(d['centro'])}"]
        if "pivote" in d:
            campos.append(f"pivote = {v3(d['pivote'])}")
        if "padre" in d:
            campos.append(f'padre = "{d["padre"]}"')
        if nom in rig.get("articulaciones", {}):
            campos.append(f'articulacion = "{rig["articulaciones"][nom]}"')
        lineas.append(f'["{nom}"] = {{ {", ".join(campos)} }},')
    texto = open(os.path.join(AQUI, "plantilla_montar_rig.luau"), encoding="utf-8").read()
    texto = (texto.replace("--NOMBRE--", info["modelo"]).replace("--RAIZ--", rig["raiz"])
             .replace("--ESPECIE--", rig.get("especie", "")).replace("--HUMANOIDE--", "true" if rig.get("humanoide") else "false")
             .replace("--PIEZAS--", "\n\t".join(lineas)))
    with open(os.path.join(carpeta, f"montar_{info['modelo']}.luau"), "w", encoding="utf-8") as f:
        f.write(texto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ronda")
    ap.add_argument("--solo", default="")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--faltan", action="store_true", help="solo los modelos que aún no tienen su .json")
    ap.add_argument("--salida", default=RAIZ)
    a = ap.parse_args()
    arch = glob.glob(os.path.join(AQUI, f"{a.ronda}_*.py"))
    mod = importlib.import_module(os.path.basename(arch[0])[:-3])
    solo = set(filter(None, a.solo.split(",")))
    tmp = os.path.join(a.salida, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    for nombre, categoria, limite, fn in mod.MODELOS:
        if solo and nombre not in solo:
            continue
        if a.faltan and os.path.exists(os.path.join(a.salida, categoria, nombre, f"{nombre}.json")):
            continue
        t0 = time.time()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        g = lib.G(nombre)
        fn(g)
        carpeta = os.path.join(a.salida, categoria, nombre)
        info, tres = lib.procesar(g, carpeta, limite=limite, rapido=a.rapido, tmp=tmp)
        if "rig" in info:
            escribir_montaje(carpeta, info)
        print(f"         {time.time() - t0:.0f} s", flush=True)
    try:
        os.rmdir(tmp)
    except OSError:
        pass


if __name__ == "__main__":
    main()
