"""
Comprueba que la pieza y las herramientas no atraviesan la forja (horno, yunque, barril, suelo).

Para cada fotograma lanza rayos a lo largo de la pieza (del talón a la punta) y de las tenazas y el martillo contra
las mallas reales de modelos/forja (BVH). La superficie del agua del barril no cuenta: la pieza tiene que entrar ahí.

    python comprobar_choques.py [--desde 0 --hasta 435]
"""

import argparse
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import cinematica as ci  # noqa: E402
import escena as es  # noqa: E402
import linea_tiempo as lt  # noqa: E402


def arboles():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    es.importar_forja()
    dg = bpy.context.evaluated_depsgraph_get()
    res = {}
    for o in bpy.data.objects:
        if o.type == "MESH" and o.name in ("forja_horno", "forja_yunque", "forja_barril", "forja_suelo"):
            res[o.name] = BVHTree.FromObject(o, dg, deform=False)
            res[o.name + "_M"] = o.matrix_world.copy()
    return res


def es_agua(p):
    return abs(p.z - es.AGUA_Z) < 0.08 and math.hypot(p.x - es.CENTRO_BARRIL.x, p.y - es.CENTRO_BARRIL.y) < 1.3


def segmento(arb, a, b):
    """Primer choque del segmento a-b con la forja (nombre, punto) o None."""
    d = b - a
    if d.length < 1e-4:
        return None
    for nombre in ("forja_horno", "forja_yunque", "forja_barril", "forja_suelo"):
        M = arb[nombre + "_M"]
        Mi = M.inverted()
        al, bl = Mi @ a, Mi @ b
        dl = bl - al
        origen = al.copy()
        restante = dl.length
        for _ in range(4):
            loc, _n, _i, dist = arb[nombre].ray_cast(origen, dl.normalized(), restante)
            if loc is None:
                break
            pm = M @ loc
            if nombre == "forja_barril" and es_agua(pm):
                origen = loc + dl.normalized() * 0.02
                restante -= dist + 0.02
                continue
            return nombre, pm
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", type=int, default=0)
    ap.add_argument("--hasta", type=int, default=lt.DURACION - 1)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    arb = arboles()
    choques = 0
    for f in range(a.desde, a.hasta + 1):
        est = ci.evaluar(f)
        L = est.dim_pieza
        talon = est.M_pieza @ Vector((0, 0, 0.15))
        punta = est.M_pieza @ Vector((0, 0, -(L[5] + L[0])))
        mano_t = est.M_tenazas.to_translation()
        punta_t = est.M_tenazas @ Vector((0, 0, -es.LARGO_TENAZAS))
        cabeza_m = est.M_martillo @ Vector((0, 0, -1.25))
        mano_m = est.M_martillo.to_translation()
        for que, (p0, p1) in (("pieza", (talon, punta)), ("tenazas", (mano_t, punta_t)),
                              ("martillo", (mano_m, cabeza_m))):
            # la pieza descansa SOBRE el yunque: se mira medio grueso por encima de su eje
            if que == "pieza":
                arriba = Vector((0, 0, L[2] / 2 + 0.02))
                p0, p1 = p0 + arriba, p1 + arriba
            c = segmento(arb, p0, p1)
            if c:
                choques += 1
                print(f"[CHOQUE] f{f} {que} con {c[0]} en {tuple(round(x, 2) for x in c[1])}")
        # El cuerpo: las 12 aristas de cada pieza del R6 (encogidas un 5 %: las piernas tocan el suelo)
        for parte, (tam, centro) in es.PIEZAS_R6.items():
            M = est.M[parte] @ Matrix.Translation(centro)
            h = [t * 0.475 for t in tam]
            esquinas = [M @ Vector((sx * h[0], sy * h[1], sz * h[2])) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
            for i in range(8):
                for j in range(i + 1, 8):
                    if bin(i ^ j).count("1") == 1:
                        c = segmento(arb, esquinas[i], esquinas[j])
                        if c and not (c[0] == "forja_suelo" and parte.endswith("Leg")):
                            choques += 1
                            print(f"[CHOQUE] f{f} {parte} con {c[0]} en {tuple(round(x, 2) for x in c[1])}")
                            break
    print(f"[fin] {choques} choques")


if __name__ == "__main__":
    main()
