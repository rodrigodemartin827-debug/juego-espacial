"""
Malla las piezas del cuerpo del Dragón Leviatán (las que salen del campo de distancia) y las guarda en caché:

  <cache>/<Pieza>_alta.npz  vértices, triángulos, normales y pintura por vértice (para hornear el atlas)
  <cache>/<Pieza>_baja.npz  malla sin el detalle fino, a resolución gruesa (se diezma después en Blender)

No necesita Blender. Uso:
    python modelos/herramientas/dragon_mallas.py --cache bestias/dragon_leviatan/_cache [--solo Cabeza,Torso]
        [--rapido] [--procesos 4]
"""

import argparse
import os
import sys
import time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

import dragon_cuerpo as C  # noqa: E402
import dragon_sdf as s  # noqa: E402


def caja_pieza(nombre, voxel=0.2):
    c, r = C.DEFS[nombre].esfera
    voxel = max(voxel, r / 55)
    mn, mx = c - r - 1.5, c + r + 1.5
    xs = [np.arange(mn[i], mx[i], voxel) for i in range(3)]
    G = np.stack(np.meshgrid(*xs, indexing="ij"), -1).reshape(-1, 3)
    d = C.campo_pieza(G, nombre, con_detalle=False)
    dentro = G[d < voxel]
    return dentro.min(0) - 1.0, dentro.max(0) + 1.0


def normales(v, f):
    a, b, c = v[f[:, 0]], v[f[:, 1]], v[f[:, 2]]
    fn = np.cross(b - a, c - a)
    vn = np.zeros_like(v)
    for i in range(3):
        np.add.at(vn, f[:, i], fn)
    return vn / np.maximum(np.linalg.norm(vn, axis=1, keepdims=True), 1e-12)


def mallar_pieza(args):
    nombre, carpeta, rapido = args
    t0 = time.time()
    C.calcular_envolventes()
    d = C.DEFS[nombre]
    mn, mx = caja_pieza(nombre)
    vox = d.voxel * (2.2 if rapido else 1.0)
    guia = lambda P: C.campo_pieza(P, nombre, con_detalle=False)  # noqa: E731
    v, f = s.mallar(lambda P: C.campo_pieza(P, nombre, True), mn, mx, vox, guia=guia)
    n = normales(v, f)
    col, rme, emi = C.pintar_piel(v, n, nombre)
    np.savez_compressed(os.path.join(carpeta, f"{nombre}_alta.npz"), v=v.astype(np.float32), f=f.astype(np.int32),
                        n=n.astype(np.float32), col=col.astype(np.float32), rme=rme.astype(np.float32),
                        emi=emi.astype(np.float32))
    vb, fb = s.mallar(guia, mn, mx, max(0.12, d.voxel * 2.6))
    np.savez_compressed(os.path.join(carpeta, f"{nombre}_baja.npz"), v=vb.astype(np.float32),
                        f=fb.astype(np.int32))
    msg = f"[ok] {nombre}: alta {len(f)} tris, baja {len(fb)} tris, {time.time() - t0:.0f} s"
    print(msg, flush=True)
    return msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--solo", default="")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--procesos", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    nombres = [n for n in C.DEFS if not a.solo or n in a.solo.split(",")]
    # las más caras primero, para repartir mejor
    nombres.sort(key=lambda n: -C.DEFS[n].tris)
    trabajos = [(n, a.cache, a.rapido) for n in nombres]
    if a.procesos <= 1:
        for t in trabajos:
            mallar_pieza(t)
    else:
        with Pool(a.procesos, maxtasksperchild=1) as pool:
            for _ in pool.imap_unordered(mallar_pieza, trabajos):
                pass


if __name__ == "__main__":
    main()
