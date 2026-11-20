"""Vista rápida de la forma (para iterar): genera las piezas de campo de una bestia y renderiza unas vistas en gris.

Uso: python bestias/herramientas/vista_rapida.py manta <carpeta_salida> [pieza1,pieza2]
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import campos as C  # noqa: E402
import taller as T  # noqa: E402


def main():
    bestia, salida = sys.argv[1], sys.argv[2]
    solo = sys.argv[3].split(",") if len(sys.argv) > 3 else None
    T.escena_vacia()
    objs = []
    if bestia == "manta":
        import manta_forma as F
        campo = F.Campo()
        for nombre, (mn, mx, vox) in F.CAJAS.items():
            if solo and nombre not in solo:
                continue
            t = time.time()
            vol, o, p = C.volumen(F.campo_pieza(campo, nombre), mn, mx, vox * 1.6)
            v, c = C.malla_de_volumen(vol, o, p)
            ob = T.malla_numpy(nombre, v, c)
            T.normales_fuera(ob)
            T.suave(ob)
            objs.append(ob)
            print(nombre, len(c), "tris", f"{time.time() - t:.1f}s")
    if bestia in ("dragon", "escarabajo", "leviatan"):
        F = __import__(bestia + "_forma")
        for nombre in F.PIEZAS:
            if solo and nombre not in solo:
                continue
            t = time.time()
            mn, mx = F.caja(nombre)
            vol, o, p = C.volumen(F.campo_pieza(nombre), mn, mx, F.voxel(nombre) * 1.8)
            v, c = C.malla_de_volumen(vol, o, p)
            ob = T.malla_numpy(nombre, v, c)
            T.normales_fuera(ob)
            T.suave(ob)
            objs.append(ob)
            print(nombre, len(c), "tris", f"{time.time() - t:.1f}s", flush=True)
    if bestia == "serpiente":
        import serpiente_forma as F
        for nombre in F.PIEZAS:
            if solo and nombre not in solo:
                continue
            mn, mx = F.caja(nombre)
            vol, o, p = C.volumen(F.campo_pieza(nombre), mn, mx, F.voxel(nombre) * 1.8)
            v, c = C.malla_de_volumen(vol, o, p)
            ob = T.malla_numpy(nombre, v, c)
            T.normales_fuera(ob)
            T.suave(ob)
            objs.append(ob)
            print(nombre, len(c), flush=True)
    mat, _ = T.material_simple("gris", (0.35, 0.37, 0.42), rug=0.55)
    for o in objs:
        T.asignar_material(o, mat)
    T.preparar_estudio(float(os.environ.get("RADIO_EST", "8.0")))
    vistas = [("Arriba", 0, 89.5), ("3/4 Frontal", 40, 25), ("Frente", 0, 4), ("Lateral Izq", 90, 4),
              ("Abajo", 0, -89.5), ("3/4 Trasera", 140, 25)]
    centro = os.environ.get("CENTRO")
    radio = os.environ.get("RADIO")
    if os.environ.get("VISTAS"):
        vistas = [(f"v{i}", float(a), float(e)) for i, (a, e) in
                  enumerate(x.split(":") for x in os.environ["VISTAS"].split(","))]
    rutas = T.renderizar_vistas(objs, salida, vistas, tam=560, muestras=12,
                                centro=[float(x) for x in centro.split(",")] if centro else None,
                                radio=float(radio) if radio else None)
    T.montar_turnaround(rutas, os.path.join(salida, "forma.png"), "forma", columnas=3)


main()
