"""
Genera la animación completa: rig R15 -> animación -> hoja de contactos -> FBX.

Uso (desde la raíz del repo, con bpy y pillow instalados):
    python animaciones/herramientas/generar.py --hoja ruta/hoja.png [--fbx]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import punetazo_fuerte as anim  # noqa: E402
import rig_r15 as r15  # noqa: E402


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0


def comprobar_contra_blender(armature):
    """Compara mi cinemática directa con la que calcula Blender (debe coincidir al milímetro)."""
    peor = 0.0
    for f in (0, 10, 16, 24):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        pose = anim.calcular_pose(f)
        for pb in armature.pose.bones:
            esperado = pose.mundo(pb.name)[0] * r15.ESTUDIO
            peor = max(peor, (pb.head - esperado).length)
    return peor / r15.ESTUDIO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoja", help="ruta del PNG de la hoja de contactos")
    ap.add_argument("--render-dir", default="/tmp/renders")
    ap.add_argument("--fbx", help="ruta del FBX con rig + malla")
    ap.add_argument("--fbx-huesos", help="ruta del FBX solo con huesos")
    ap.add_argument("--blend", help="ruta del .blend")
    a = ap.parse_args()

    escena_vacia()
    armature, mallas = r15.construir_rig()
    anim.hornear(armature)

    error = comprobar_contra_blender(armature)
    print(f"[ok] FK propia vs Blender: desviación máxima {error:.5f} studs")
    peor = max(max(e) for e in anim.ERRORES_PIE.values())
    print(f"[ok] error máximo de IK en pies: {peor:.4f} studs")
    for f, (i, d) in sorted(anim.ERRORES_PIE.items()):
        if max(i, d) > 0.02:
            print(f"     aviso: f{f} pie izq {i:.3f} der {d:.3f} (objetivo fuera de alcance)")

    if a.hoja:
        import hoja_contactos

        hoja_contactos.renderizar(anim.FOTOGRAMAS_CLAVE, a.render_dir, a.hoja)
        print("[ok] hoja:", a.hoja)
    if a.fbx or a.fbx_huesos:
        import exportar_fbx

        exportar_fbx.exportar(armature, mallas, a.fbx, a.fbx_huesos)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=a.blend)


main()
