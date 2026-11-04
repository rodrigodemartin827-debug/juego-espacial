"""
Rehace SOLO algunas piezas del kit en region1_valle_del_alba.blend a partir de kit.py, las vuelve a exportar a FBX y
actualiza su entrada de datos/piezas.json. El resto de piezas, el terreno, los edificios y los demás datos no se tocan.

Sirve para arreglar piezas sueltas sin repetir toda la exportación (y sin tener que volver a importar en Roblox más
que esas piezas). Todas las copias de la pieza en la escena pasan a usar la malla nueva (user_remap).

Uso (Blender; no hace falta PIL ni scipy para paredes y tejados):
    blender -b --factory-startup --python modelos/region1_valle_del_alba/herramientas/rehacer_piezas.py --
        --blend modelos/region1_valle_del_alba/region1_valle_del_alba.blend
        --salida modelos/region1_valle_del_alba/roblox
        --piezas Pared_Lisa,Pared_Lisa__lejos,Puerta
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import sin_dependencias  # noqa: E402, F401
import exportar as EX  # noqa: E402
import kit as K  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--piezas", required=True, help="nombres separados por comas («X__lejos» para la versión simple)")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))
    sal = os.path.abspath(a.salida)
    ruta_json = os.path.join(sal, "datos", "piezas.json")
    with open(ruta_json, encoding="utf-8") as f:
        piezas = json.load(f)

    materiales = {m.name: m for m in bpy.data.materials}
    kit = next((c for c in bpy.data.collections if c.name.startswith("Kit_Piezas")), None)
    for nombre in [n.strip() for n in a.piezas.split(",") if n.strip()]:
        lejos = nombre.endswith("__lejos")
        base = nombre[: -len("__lejos")] if lejos else nombre
        malla = K.malla(base, lejos)
        if malla is None:
            print(f"{nombre}: de lejos no se dibuja, nada que hacer")
            continue
        ob = malla.a_blender("K_tmp_" + nombre, materiales)
        nueva = ob.data
        vieja = bpy.data.meshes.get("K_" + nombre)
        antes = EX.triangulos(vieja) if vieja else None
        if vieja is not None:
            vieja.user_remap(nueva)  # todas las copias de la escena usan ya la malla nueva
            bpy.data.meshes.remove(vieja)
            bpy.data.objects.remove(ob)
        else:
            # Pieza nueva (por ejemplo, una versión de lejos que antes no existía): se guarda en la colección del kit.
            ob.name = "K_" + nombre
            ob["pieza"] = base
            if kit is not None:
                kit.objects.link(ob)
            else:
                nueva.use_fake_user = True
        nueva.name = "K_" + nombre

        # FBX y datos, con las mismas cuentas que exportar.py.
        centro, tam = EX.caja_malla(nueva)
        info = piezas.setdefault(base, {"fbx": None, "fbx_lejos": None, "sin_lejos": False})
        info["lejos" if lejos else "detalle"] = dict(
            centro=[round(float(v), 4) for v in EX.C @ centro],
            tamano=[round(float(v), 4) for v in np.abs(EX.C @ tam)],
            triangulos=EX.triangulos(nueva),
        )
        info["fbx_lejos" if lejos else "fbx"] = f"piezas/{nombre}.fbx"
        info["color"] = K.color_defecto(base)
        if base in K.DOBLE_CARA:
            info["doble_cara"] = True
        tmp = EX.objeto_temporal(nueva, nombre)
        EX.exportar_fbx(tmp, os.path.join(sal, "piezas", nombre + ".fbx"))
        bpy.data.objects.remove(tmp)
        print(f"{nombre}: {antes if antes is not None else 'nueva'} -> {EX.triangulos(nueva)} triángulos, exportada")

    # Las piezas de doble cara (lonas) se marcan aunque no se hayan rehecho.
    for base in K.DOBLE_CARA:
        if base in piezas:
            piezas[base]["doble_cara"] = True
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump(piezas, f, ensure_ascii=False, indent=1)
    bpy.ops.wm.save_mainfile()
    print("guardado", a.blend)


main()
