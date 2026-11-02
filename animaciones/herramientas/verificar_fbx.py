"""
Reimporta un FBX en una escena vacía y comprueba que contiene lo que Roblox espera:
los 7 huesos con nombres R6 y su jerarquía, la animación completa a 30 fps y las mismas posiciones
de articulaciones que la animación original en varios fotogramas.

Uso: python animaciones/herramientas/verificar_fbx.py ruta.fbx
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import punetazo_fuerte as anim  # noqa: E402
import rig_r6 as r6  # noqa: E402


def main(ruta):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y", automatic_bone_orientation=False)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    nombres = {b.name for b in arm.data.bones}
    assert nombres == set(r6.ARTICULACIONES), f"huesos distintos: {nombres ^ set(r6.ARTICULACIONES)}"
    for b in arm.data.bones:
        esperado = r6.PADRE[b.name]
        assert (b.parent.name if b.parent else None) == esperado, f"padre de {b.name}"
    print(f"[ok] {len(nombres)} huesos con nombres y jerarquía R6")

    accion = arm.animation_data.action
    inicio, fin = (int(round(x)) for x in accion.frame_range)
    scn = bpy.context.scene
    assert fin - inicio == anim.ULTIMO_FOTOGRAMA, (inicio, fin)  # Blender empieza a importar en el 1
    assert round(scn.render.fps / scn.render.fps_base) == anim.FPS, scn.render.fps
    print(f"[ok] animación {inicio}-{fin} a {anim.FPS} fps ({(fin - inicio) / anim.FPS:.2f} s)")

    # Escala del FBX: el importador devuelve las unidades de Blender; la comparamos con la original.
    peor = 0.0
    for f in (0, 10, 13, 16, 22, 40):
        scn.frame_set(f + inicio)
        bpy.context.view_layer.update()
        pose = anim.calcular_pose(f)
        for pb in arm.pose.bones:
            real = (arm.matrix_world @ pb.head) / r6.ESTUDIO
            esperado = pose.mundo(pb.name)[0]
            peor = max(peor, (real - esperado).length)
    print(f"[ok] desviación máxima de articulaciones tras reimportar: {peor:.4f} studs")
    assert peor < 0.02, "el FBX no reproduce la animación"


main(sys.argv[-1])
