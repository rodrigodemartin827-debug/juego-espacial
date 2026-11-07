"""
Reimporta un FBX de movimiento en una escena vacía y comprueba lo que Roblox espera: los 7 huesos R6 con su
jerarquía, la duración del ciclo a 30 fps y las mismas posiciones de articulaciones que la animación original.

Uso: python animaciones/movimiento/herramientas/verificar.py ruta.fbx <reposo|andar|correr>
"""

import importlib
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(AQUI, "..", "..", "herramientas"))

import bpy  # noqa: E402

import rig_r6 as r6  # noqa: E402


def main(ruta, nombre):
    anim = importlib.import_module(nombre)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y", automatic_bone_orientation=False)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    nombres = {b.name for b in arm.data.bones}
    assert nombres == set(r6.ARTICULACIONES), f"huesos distintos: {nombres ^ set(r6.ARTICULACIONES)}"
    for b in arm.data.bones:
        assert (b.parent.name if b.parent else None) == r6.PADRE[b.name], f"padre de {b.name}"
    print(f"[ok] {len(nombres)} huesos con nombres y jerarquía R6")

    accion = arm.animation_data.action
    inicio, fin = (int(round(x)) for x in accion.frame_range)
    scn = bpy.context.scene
    assert fin - inicio == anim.ULTIMO_FOTOGRAMA, (inicio, fin)
    assert round(scn.render.fps / scn.render.fps_base) == anim.FPS, scn.render.fps
    print(f"[ok] animación {inicio}-{fin} a {anim.FPS} fps ({(fin - inicio) / anim.FPS:.2f} s)")

    peor = 0.0
    for f in range(0, anim.ULTIMO_FOTOGRAMA + 1):
        scn.frame_set(f + inicio)
        bpy.context.view_layer.update()
        pose = anim.calcular_pose(f)
        for pb in arm.pose.bones:
            real = (arm.matrix_world @ pb.head) / r6.ESTUDIO
            peor = max(peor, (real - pose.mundo(pb.name)[0]).length)
    print(f"[ok] desviación máxima de articulaciones tras reimportar (todos los fotogramas): {peor:.4f} studs")
    assert peor < 0.02, "el FBX no reproduce la animación"


main(sys.argv[-2], sys.argv[-1])
