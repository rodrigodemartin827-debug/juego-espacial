"""
Genera la animación completa: rig R6 -> animación -> hoja de contactos -> FBX.

Uso (desde la raíz del repo, con bpy y pillow instalados):
    python animaciones/herramientas/generar.py --hoja ruta/hoja.png [--fbx]
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402

import punetazo_fuerte as anim  # noqa: E402
import rig_r6 as r6  # noqa: E402


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
            esperado = pose.mundo(pb.name)[0] * r6.ESTUDIO
            peor = max(peor, (pb.head - esperado).length)
    return peor / r6.ESTUDIO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hoja", help="ruta del PNG de la hoja de contactos")
    ap.add_argument("--render-dir", default="/tmp/renders")
    ap.add_argument("--fbx", help="ruta del FBX con rig + malla")
    ap.add_argument("--fbx-huesos", help="ruta del FBX solo con huesos")
    ap.add_argument("--blend", help="ruta del .blend")
    a = ap.parse_args()

    escena_vacia()
    armature, mallas = r6.construir_rig()
    anim.hornear(armature)

    error = comprobar_contra_blender(armature)
    print(f"[ok] FK propia vs Blender: desviación máxima {error:.5f} studs")
    # La pierna adelantada (izquierda) apoya todo el movimiento: debe llegar al suelo sin patinar. La trasera
    # solo apunta hacia su pie (R6 no tiene rodillas, así que no siempre llega) y puede quedar estirada.
    peor_apoyo = max(i for i, _ in anim.ERRORES_PIE.values())
    peor_trasera = max(d for _, d in anim.ERRORES_PIE.values())
    print(f"[ok] error máximo de la pierna de apoyo respecto al suelo: {peor_apoyo:.4f} studs")
    print(f"[ok] la pierna trasera (libre, de puntillas) queda como mucho a {peor_trasera:.2f} studs de su objetivo")
    assert peor_apoyo < 0.05, "el pie de apoyo patina o se hunde"

    if a.hoja:
        import hoja_contactos

        hoja_contactos.renderizar(anim.FOTOGRAMAS_CLAVE, a.render_dir, a.hoja, anim.punto_de_impacto())
        print("[ok] hoja:", a.hoja)
    if a.fbx or a.fbx_huesos:
        import exportar_fbx

        exportar_fbx.exportar(armature, mallas, a.fbx, a.fbx_huesos)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=a.blend)


main()
