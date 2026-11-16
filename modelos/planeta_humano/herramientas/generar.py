"""
Genera modelos del Planeta Humano. Cada modelo se hace en su propio proceso y su propia escena limpia.

  python generar.py casa_pequena_a farola_residencial   # modelos sueltos
  python generar.py --ronda 1 -j 3                      # los modelos 1-10, tres a la vez
  python generar.py --todo -j 3
"""

import argparse
import importlib
import os
import subprocess
import sys
import traceback

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)


def cargar():
    from registro import MODELOS
    for f in sorted(os.listdir(AQUI)):
        if f.startswith("ronda_") and f.endswith(".py"):
            importlib.import_module(f[:-3])
    return MODELOS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("nombres", nargs="*")
    ap.add_argument("--ronda", type=int)
    ap.add_argument("--todo", action="store_true")
    ap.add_argument("-j", type=int, default=1)
    ap.add_argument("--sin-render", action="store_true")
    a = ap.parse_args()
    M = cargar()
    nombres = list(a.nombres)
    if a.ronda:
        nombres += [n for n, i in M.items() if (i["num"] - 1) // 10 + 1 == a.ronda]
    if a.todo:
        nombres = list(M)
    nombres.sort(key=lambda n: M[n]["num"])
    if len(nombres) > 1 or a.j > 1:
        # Un proceso por modelo.
        pend = list(nombres)
        vivos = []
        fallos = []
        while pend or vivos:
            while pend and len(vivos) < a.j:
                n = pend.pop(0)
                cmd = [sys.executable, os.path.abspath(__file__), n] + (["--sin-render"] if a.sin_render else [])
                vivos.append((n, subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)))
            for n, p in list(vivos):
                if p.poll() is not None:
                    out = p.stdout.read()
                    lineas = [l for l in out.splitlines() if l.startswith("[") or "Error" in l or "error" in l]
                    print("\n".join(lineas[-6:]) if lineas else f"[??] {n}: sin salida", flush=True)
                    if p.returncode != 0:
                        fallos.append(n)
                        with open(os.path.join(AQUI, "..", "errores.log"), "a") as f:
                            f.write(f"\n===== {n}\n{out[-4000:]}\n")
                        print(f"[FALLO] {n} (ver errores.log)", flush=True)
                    vivos.remove((n, p))
            import time
            time.sleep(0.5)
        print(f"hechos {len(nombres) - len(fallos)}/{len(nombres)}; fallos: {fallos}")
        return
    for n in nombres:
        from tuberia import construir
        info = M[n]
        try:
            construir(n, {k: v for k, v in info.items() if k != "fn"}, info["fn"], con_render=not a.sin_render)
        except Exception:
            traceback.print_exc()
            sys.exit(1)


if __name__ == "__main__":
    main()
