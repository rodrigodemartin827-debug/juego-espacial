"""Genera modelos del Planeta Humano.

    python generar.py <modelo> [<modelo> ...]     # uno o varios
    python generar.py zona:comercial               # todos los de una zona
    python generar.py todos
    PH_DEBUG=1 python generar.py <modelo>          # solo cuenta triángulos por sección, sin hornear
"""
import importlib
import sys

MODULOS = ["comercial", "comercial_b", "comercial_c", "comercial_d", "industrial", "industrial_b", "hangar", "hangar_b", "naturaleza", "naturaleza_b", "especiales", "especiales_b", "urbano"]
MODELOS = {}
for nombre in MODULOS:
    try:
        mod = importlib.import_module(nombre)
    except ModuleNotFoundError as e:
        if e.name == nombre:
            continue
        raise
    MODELOS.update(mod.MODELOS)

if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["todos"]:
        args = list(MODELOS)
    elif len(args) == 1 and args[0].startswith("zona:"):
        args = [k for k, f in MODELOS.items() if f.__module__.startswith(args[0][5:])]
    for a in args:
        MODELOS[a]()
