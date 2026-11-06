"""
Revisa las caras de cada pieza del kit (detallada y simple): lo que en Roblox se ve como «lámina transparente».

Roblox solo dibuja la cara delantera de cada triángulo (salvo DoubleSided). Una pieza se ve transparente desde algún
lado si es una superficie abierta: tiene ARISTAS ABIERTAS (usadas por una sola cara), o no tiene grosor. Por cada
pieza se cuenta:

  aristas_abiertas  aristas con una sola cara (tras soldar los vértices que coinciden)
  grosor            la menor dimensión de su caja (0 = una lámina)
  volumen           volumen con signo (solo tiene sentido si está cerrada: > 0 = normales hacia fuera)
  invertidas        caras cuya normal apunta hacia el centro de la pieza siendo cerrada (normales al revés)

Uso (con el Python de Blender, que trae numpy):
    blender -b --factory-startup --python modelos/region1_valle_del_alba/herramientas/revisar_caras.py -- [--json salida.json]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import numpy as np  # noqa: E402

import sin_dependencias  # noqa: E402, F401  (PIL y scipy de mentira si faltan: aquí no se pinta ni se hacen copas)
import kit as K  # noqa: E402


def soldar(malla, tol=1e-4):
    """Índices de vértice soldados por posición y lista de caras con esos índices."""
    pts = malla.todos_vertices()
    claves = np.round(pts / tol).astype(np.int64)
    _, inv = np.unique(claves, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    caras = [tuple(int(inv[i]) for i in c) for c in malla.caras]
    return pts, inv, caras


def revisar(malla):
    if malla is None or not malla.v:
        return None
    pts, inv, caras = soldar(malla)
    usos = {}
    for c in caras:
        for k in range(len(c)):
            a, b = c[k], c[(k + 1) % len(c)]
            if a == b:
                continue
            clave = (a, b) if a < b else (b, a)
            usos[clave] = usos.get(clave, 0) + 1
    abiertas = sum(1 for n in usos.values() if n == 1)
    # volumen con signo (abanico desde el origen) con los vértices originales de cada cara
    vol = 0.0
    for c in malla.caras:
        p0 = pts[c[0]]
        for k in range(1, len(c) - 1):
            vol += np.dot(p0, np.cross(pts[c[k]], pts[c[k + 1]])) / 6.0
    lo, hi = malla.limites()
    tam = hi - lo
    return dict(
        triangulos=malla.n_triangulos,
        aristas_abiertas=abiertas,
        grosor=round(float(tam.min()), 3),
        tamano=[round(float(x), 2) for x in tam],
        volumen=round(float(vol), 2),
    )


def main():
    args = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    salida = args[args.index("--json") + 1] if "--json" in args else None
    filas = {}
    for nombre in K.PIEZAS:
        for lejos in (False, True):
            det, sim, _, _ = K.PIEZAS[nombre]
            if lejos and (sim is None or sim is K.SIN_LEJOS):
                continue
            try:
                m = K.malla(nombre, lejos)
            except RuntimeError as e:  # copas de árbol sin scipy: son volúmenes cerrados, no afectan
                print(f"{nombre}: no se puede rehacer aquí ({e})")
                continue
            r = revisar(m)
            if r:
                filas[nombre + ("__lejos" if lejos else "")] = r
    for n, r in sorted(filas.items(), key=lambda kv: -kv[1]["aristas_abiertas"]):
        marca = "ABIERTA" if r["aristas_abiertas"] else "cerrada"
        print(f"{n:28s} {marca:8s} abiertas={r['aristas_abiertas']:4d} grosor={r['grosor']:6.3f} "
              f"tris={r['triangulos']:5d} vol={r['volumen']:9.2f}")
    if salida:
        with open(salida, "w", encoding="utf-8") as f:
            json.dump(filas, f, indent=1, ensure_ascii=False)


main()
