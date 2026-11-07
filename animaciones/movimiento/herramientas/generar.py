"""
Genera una animación de movimiento completa: rig R6 -> animación -> comprobaciones -> renders -> FBX y RBXMX.

Uso (desde la raíz del repo, con bpy y pillow instalados):
    python animaciones/movimiento/herramientas/generar.py andar --todo
    python animaciones/movimiento/herramientas/generar.py correr --hoja h.png --gif c.gif

`--todo` escribe en animaciones/movimiento/ los archivos con su nombre de siempre.
"""

import argparse
import importlib
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(AQUI, "..", "..", "herramientas"))  # rig R6 y utilidades del puñetazo

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import marcha  # noqa: E402
import rbxmx  # noqa: E402
import rig_r6 as r6  # noqa: E402

CARPETA = os.path.normpath(os.path.join(AQUI, ".."))
CENTROS = {  # centro de cada pieza en reposo (studs, Blender)
    "HumanoidRootPart": (0, 0, 3),
    "Torso": (0, 0, 3),
    "Head": (0, 0, 4.5),
    "Left Arm": (1.5, 0, 3),
    "Right Arm": (-1.5, 0, 3),
    "Left Leg": (0.5, 0, 1),
    "Right Leg": (-0.5, 0, 1),
}


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0


def comprobar_contra_blender(armature, anim):
    """Mi cinemática directa contra la de Blender (deben coincidir)."""
    peor = 0.0
    for f in range(0, anim.ULTIMO_FOTOGRAMA + 1, max(1, anim.ULTIMO_FOTOGRAMA // 6)):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        pose = anim.calcular_pose(f)
        for pb in armature.pose.bones:
            peor = max(peor, (pb.head - pose.mundo(pb.name)[0] * r6.ESTUDIO).length)
    return peor / r6.ESTUDIO


def centros_blender_en_roblox(pose):
    out = {}
    for h, c in CENTROS.items():
        pos, rot = pose.mundo(h)
        centro = pos + rot @ (Vector(c) - Vector(r6.ARTICULACIONES[h]))
        out[h] = rbxmx.B @ centro
    return out


def comprobar_rbxmx(ruta, anim):
    """Lee el .rbxmx, reproduce los Motor6D como Roblox y compara con la animación de Blender."""
    props, claves = rbxmx.leer(ruta)
    assert props["Loop"] == ("true" if anim.BUCLE else "false")
    assert len(claves) == anim.ULTIMO_FOTOGRAMA + 1, len(claves)
    peor = 0.0
    for f, (t, poses) in enumerate(claves):
        assert abs(t - f / anim.FPS) < 1e-4
        assert set(poses) == set(r6.ARTICULACIONES), set(poses) ^ set(r6.ARTICULACIONES)
        reales = rbxmx.centros_roblox(poses)
        esperados = centros_blender_en_roblox(anim.calcular_pose(f))
        peor = max(peor, max((reales[h] - esperados[h]).length for h in reales))
    return peor, claves[-1][0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("animacion", help="reposo | andar | correr")
    ap.add_argument("--todo", action="store_true", help="todos los archivos finales en animaciones/movimiento/")
    ap.add_argument("--hoja")
    ap.add_argument("--gif")
    ap.add_argument("--fbx")
    ap.add_argument("--fbx-huesos")
    ap.add_argument("--rbxmx")
    ap.add_argument("--blend")
    ap.add_argument("--render-dir", default="/tmp/renders_movimiento")
    ap.add_argument("--muestras", type=int, default=16)
    ap.add_argument("--solo-lateral", action="store_true", help="GIF solo con la vista lateral (más rápido)")
    # Con «blender -b --python generar.py -- correr ...» los argumentos propios van detrás de «--».
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None)

    anim = importlib.import_module(a.animacion)
    base = os.path.join(CARPETA, a.animacion)
    if a.todo:
        a.hoja = a.hoja or f"{base}_hoja_de_contactos.png"
        a.gif = a.gif or f"{base}.gif"
        a.fbx = a.fbx or f"{base}.fbx"
        a.fbx_huesos = a.fbx_huesos or f"{base}_solo_huesos.fbx"
        a.rbxmx = a.rbxmx or f"{base}.rbxmx"
        a.blend = a.blend or f"{base}.blend"

    # --- comprobaciones sin Blender
    cierre = marcha.comprobar_bucle(anim.calcular_pose, anim.ULTIMO_FOTOGRAMA)
    print(f"[ok] bucle: diferencia entre el último fotograma y el primero = {cierre:.2e}")
    assert cierre < 1e-6, "el bucle no cierra"
    m = anim.metricas()
    for clave, valor in m.items():
        print(f"     {clave}: {valor:.4f}" if isinstance(valor, float) else f"     {clave}: {valor}")
    for clave, limite in anim.LIMITES.items():
        assert m[clave] <= limite if clave != "roce" else m[clave] >= limite, f"{clave} = {m[clave]:.4f} (límite {limite})"
    print("[ok] pies: dentro de los límites", anim.LIMITES)

    escena_vacia()
    armature, mallas = r6.construir_rig()
    marcha.ciclo.hornear(armature, anim.NOMBRE, anim.calcular_pose, anim.ULTIMO_FOTOGRAMA, anim.FPS)
    error = comprobar_contra_blender(armature, anim)
    print(f"[ok] FK propia vs Blender: desviación máxima {error:.5f} studs")
    assert error < 1e-3

    if a.rbxmx:
        rbxmx.escribir(a.rbxmx, anim.NOMBRE, anim.calcular_pose, anim.ULTIMO_FOTOGRAMA, anim.FPS, anim.PRIORIDAD, anim.BUCLE)
        peor, dur = comprobar_rbxmx(a.rbxmx, anim)
        print(f"[ok] RBXMX: {a.rbxmx} ({dur:.2f} s); reproducido como en Roblox, desviación máxima {peor:.5f} studs")
        assert peor < 1e-3

    if a.fbx or a.fbx_huesos:
        import exportar_fbx

        exportar_fbx.exportar(armature, mallas, a.fbx, a.fbx_huesos)

    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=a.blend)
        print("[ok] blend:", a.blend)

    if a.hoja or a.gif:
        import render_mov

        n = anim.CICLO
        claves = [f for f, _ in anim.FOTOGRAMAS_CLAVE]
        paso = getattr(anim, "PASO_GIF", 1)
        del_gif = list(range(0, n, paso)) if a.gif else []
        vistas_gif = ["Lateral"] if a.solo_lateral else list(render_mov.VISTAS)
        rutas = {}
        if a.hoja:
            rutas.update(
                render_mov.renderizar(claves, a.render_dir, anim.VELOCIDAD, anim.FPS, anim.VELOCIDAD * n / anim.FPS, muestras=a.muestras)
            )
        if a.gif:
            faltan = [f for f in del_gif if not all((v, f) in rutas for v in vistas_gif)]
            bpy.ops.wm.read_factory_settings(use_empty=True)
            armature, _ = r6.construir_rig()
            marcha.ciclo.hornear(armature, anim.NOMBRE, anim.calcular_pose, anim.ULTIMO_FOTOGRAMA, anim.FPS)
            rutas.update(
                render_mov.renderizar(
                    faltan, a.render_dir, anim.VELOCIDAD, anim.FPS, anim.VELOCIDAD * n / anim.FPS, vistas_gif, a.muestras
                )
            )
        if a.hoja:
            render_mov.hoja(rutas, anim.FOTOGRAMAS_CLAVE, a.hoja, anim.TITULO)
            print("[ok] hoja:", a.hoja)
        if a.gif:
            render_mov.gif(rutas, del_gif, a.gif, anim.FPS, vistas_gif, escala=0.75, rotulo=anim.TITULO)
            print("[ok] gif:", a.gif)


main()
