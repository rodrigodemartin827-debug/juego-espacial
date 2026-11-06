"""
Mapa de alturas de la región 1 para Roblox: la CAPA DE COLISIÓN FIJA del terreno.

Por qué: la colisión de las mallas de terreno en Roblox no es fiable (probado en Studio: con PreciseConvexDecomposition,
51 de los 64 trozos tienen agujeros y el 6_5 no tiene colisión ninguna; son láminas abiertas de 19.200 triángulos y
Roblox las aproxima con pocas envolturas convexas). Por ahí el personaje atravesaba el suelo. Con este mapa el suelo
se calcula a partir de la posición: no depende de la colisión, ni del nivel de detalle, ni de lo que haya llegado al
cliente (StreamingEnabled).

Qué hace: muestrea los trozos de terreno DETALLADOS (los mismos que se ven) con rayos hacia el centro del planeta, en
una cuadrícula regular de las coordenadas de diseño (geo.py: x = R·β, y = R·α' en la cara YP, de -L a L). Escribe
roblox/datos/alturas.luau, un ModuleScript con:
    N            puntos por lado
    L, Radio     el semilado de la cara en coordenadas de diseño y el radio del planeta
    Base, Escala radio = Base + valor · Escala (valor de 16 bits; 0 = sin dato)
    Datos        los N·N valores (uint16, little endian, fila a fila: y de -L a L, x de -L a L) en base64

Uso:
    blender -b --factory-startup --python modelos/region1_valle_del_alba/herramientas/exportar_alturas.py --
        --blend modelos/region1_valle_del_alba/region1_valle_del_alba.blend --salida modelos/region1_valle_del_alba/roblox
        [--n 481]
"""

import argparse
import base64
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402
from mathutils.bvhtree import BVHTree  # noqa: E402

import geo  # noqa: E402

BASE = 2150.0
ESCALA = 0.01  # studs por unidad: de 2150 a ~2805 studs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--n", type=int, default=481)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))

    # Todos los trozos detallados, en coordenadas del mundo (Blender), en un solo árbol de búsqueda.
    verts, caras = [], []
    for ob in bpy.data.objects:
        if ob.get("lod") != "terreno" or ob.get("nivel") != "detalle":
            continue
        me = ob.data
        mw = ob.matrix_world
        base = len(verts)
        verts.extend([tuple(mw @ v.co) for v in me.vertices])
        caras.extend([tuple(base + i for i in p.vertices) for p in me.polygons])
    arbol = BVHTree.FromPolygons(verts, caras)
    print(f"terreno: {len(verts)} vértices, {len(caras)} caras")

    n = a.n
    eje = np.linspace(-geo.L, geo.L, n)
    valores = np.zeros((n, n), dtype=np.uint16)
    sin_dato = 0
    for i, y in enumerate(eje):
        d = geo.direccion(eje, np.full(n, y))
        for j in range(n):
            dj = Vector(d[j])
            hit = arbol.ray_cast(dj * 3300.0, -dj, 2000.0)
            if hit[0] is None:
                sin_dato += 1
                continue
            r = hit[0].length
            valores[i, j] = int(np.clip(round((r - BASE) / ESCALA), 1, 65535))
    print(f"alturas: {n} x {n}, sin dato: {sin_dato}")

    datos = base64.b64encode(valores.astype("<u2").tobytes()).decode("ascii")
    ruta = os.path.join(os.path.abspath(a.salida), "datos", "alturas.luau")
    with open(ruta, "w", encoding="utf-8", newline="\n") as f:
        f.write("--!strict\n")
        f.write("-- GENERADO por herramientas/exportar_alturas.py: mapa de alturas del terreno de la región 1 (no editar).\n")
        f.write("-- Lo lee AlturasRegion. Radio del suelo = Base + valor · Escala (valor uint16; 0 = sin dato).\n")
        f.write("return {\n")
        f.write(f"\tN = {n},\n\tL = {geo.L!r},\n\tRadio = {geo.RADIO!r},\n\tBase = {BASE!r},\n\tEscala = {ESCALA!r},\n")
        f.write(f'\tDatos = "{datos}",\n')
        f.write("}\n")
    print("escrito", ruta, f"({len(datos) / 1e6:.2f} MB)")


main()
