"""
Genera modelos del Planeta Monstruo. Cada modelo se hace en un proceso y una escena limpia propios.

  python ejecutar.py <nombre> [--rapido]          un modelo, en este proceso
  python ejecutar.py --lote n1 n2 ... [-j 3]      varios, cada uno en su proceso (registros en --logs)
  python ejecutar.py --ronda 1 [-j 3]             los de ronda_01.py
  python ejecutar.py --lista                      lista de modelos registrados
"""

import argparse
import glob
import importlib
import os
import subprocess
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
SALIDA = os.path.normpath(os.path.join(AQUI, "..", "..", "planeta_monstruo"))


def cargar():
    import lib

    por_ronda = {}
    for ruta in sorted(glob.glob(os.path.join(AQUI, "ronda_*.py"))):
        antes = set(lib.REGISTRO)
        importlib.import_module(os.path.basename(ruta)[:-3])
        por_ronda[int(os.path.basename(ruta)[6:8])] = [n for n in lib.REGISTRO if n not in antes]
    return lib, por_ronda


def uno(nombre, rapido, salida):
    import bpy

    lib, _ = cargar()
    r = lib.REGISTRO[nombre]
    bpy.ops.wm.read_factory_settings(use_empty=True)  # un modelo = una escena limpia
    M = lib.Modelo(nombre, r["zona"], r["clase"], r["tam"], r["descripcion"], **r["kw"])
    r["fn"](M)
    M.construir(os.path.join(salida, nombre), rapido=rapido)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nombres", nargs="*")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--lote", action="store_true")
    ap.add_argument("--ronda", type=int)
    ap.add_argument("--lista", action="store_true")
    ap.add_argument("-j", type=int, default=3)
    ap.add_argument("--salida", default=SALIDA)
    ap.add_argument("--logs", default=os.path.join(AQUI, "_logs"))
    a = ap.parse_args()
    if a.lista:
        _, por_ronda = cargar()
        for k, v in por_ronda.items():
            print(k, " ".join(v))
        return
    if a.ronda is not None:
        _, por_ronda = cargar()
        a.nombres, a.lote = por_ronda[a.ronda], True
    if not a.lote:
        for n in a.nombres:
            uno(n, a.rapido, a.salida)
        return
    os.makedirs(a.logs, exist_ok=True)
    cola, vivos, fallos = list(a.nombres), [], []
    while cola or vivos:
        while cola and len(vivos) < a.j:
            n = cola.pop(0)
            f = open(os.path.join(a.logs, n + ".log"), "w")
            cmd = [sys.executable, os.path.abspath(__file__), n, "--salida", a.salida] + (["--rapido"] if a.rapido else [])
            vivos.append((n, subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT), f, time.time()))
        time.sleep(1)
        for v in list(vivos):
            n, p, f, t = v
            if p.poll() is not None:
                f.close()
                vivos.remove(v)
                ok = p.returncode == 0
                if not ok:
                    fallos.append(n)
                print(f"{'OK   ' if ok else 'FALLO'} {n} ({time.time() - t:.0f}s)", flush=True)
    print("FALLOS:", fallos or "ninguno")


if __name__ == "__main__":
    main()
