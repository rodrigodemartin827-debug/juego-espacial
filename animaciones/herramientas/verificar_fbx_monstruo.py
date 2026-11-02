"""
Reimporta los FBX del andar de monstruo y comprueba que reproducen la animación: los 7 huesos R6 con su jerarquía,
el número de fotogramas y las posiciones de las articulaciones en varios fotogramas (contra el rig horneado
directamente desde el JSON de exportar_monstruo.luau).

Uso: python animaciones/herramientas/verificar_fbx_monstruo.py --json /tmp/monstruo.json --fbx-dir animaciones/andar_monstruo
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv, _args = sys.argv[:1], sys.argv[1:]  # andar_monstruo.py lee sus propios argumentos al importarse

import bpy  # noqa: E402

import rig_r6 as r6  # noqa: E402


def posiciones(arm, fotogramas, inicio=0):
    scn = bpy.context.scene
    resultado = {}
    for f in fotogramas:
        scn.frame_set(f + inicio)
        bpy.context.view_layer.update()
        resultado[f] = {pb.name: (arm.matrix_world @ pb.head) / r6.ESTUDIO for pb in arm.pose.bones}
    return resultado


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True)
    ap.add_argument("--fbx-dir", required=True)
    a = ap.parse_args(_args)
    import importlib.util

    sys.argv = ["andar_monstruo.py", "--json", a.json, "--solo", "-"]
    spec = importlib.util.spec_from_file_location(
        "andar_monstruo", os.path.join(os.path.dirname(os.path.abspath(__file__)), "andar_monstruo.py")
    )
    am = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(am)

    with open(a.json, encoding="utf-8") as archivo:
        animaciones = json.load(archivo)
    for anim in animaciones:
        ultimo = len(anim["Cuadros"]) - 1
        muestras = sorted({0, ultimo // 3, ultimo // 2, (2 * ultimo) // 3, ultimo})
        am.escena_vacia()
        arm, _ = am.construir_rig()
        am.hornear(arm, anim)
        esperado = posiciones(arm, muestras)

        bpy.ops.wm.read_factory_settings(use_empty=True)
        ruta = os.path.join(a.fbx_dir, f"{anim['Nombre'].lower()}_solo_huesos.fbx")
        bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y", automatic_bone_orientation=False)
        importado = next(o for o in bpy.data.objects if o.type == "ARMATURE")
        nombres = {b.name for b in importado.data.bones}
        assert nombres == set(r6.ARTICULACIONES), f"{ruta}: huesos {nombres}"
        for b in importado.data.bones:
            assert (b.parent.name if b.parent else None) == r6.PADRE[b.name], f"{ruta}: padre de {b.name}"
        inicio, fin = (int(round(x)) for x in importado.animation_data.action.frame_range)
        assert fin - inicio == ultimo, f"{ruta}: {fin - inicio} fotogramas en vez de {ultimo}"
        real = posiciones(importado, muestras, inicio)
        peor = max((real[f][n] - esperado[f][n]).length for f in muestras for n in esperado[f])
        assert peor < 0.02, f"{ruta}: las articulaciones se desvían {peor:.3f} studs"
        print(f"[ok] {os.path.basename(ruta)}: 7 huesos R6, {ultimo + 1} fotogramas, desviación {peor:.4f} studs")


main()
