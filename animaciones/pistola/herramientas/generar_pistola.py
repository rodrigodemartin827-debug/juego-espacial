"""
Genera las animaciones de la pistola de portales: rig R6 -> animación -> comprobaciones -> FBX, RBXMX y .blend -> renders.

Uso (desde la raíz del repo, con bpy y pillow instalados):
    python animaciones/pistola/herramientas/generar_pistola.py --salida animaciones/pistola --ronda 5 --gif
    python animaciones/pistola/herramientas/generar_pistola.py --salida /tmp/prueba --ronda 1 --rapido

Escribe en --salida, para cada pistola (chatarra, vip):
    apuntar_<p>.rbxmx|.fbx|_solo_huesos.fbx|.blend|.gif        bucle de apuntar (solo mueve el brazo derecho)
    disparo_<p>.rbxmx|.fbx|_solo_huesos.fbx|.blend|.gif        el disparo completo (con el paso atrás)
    disparo_<p>_movil.rbxmx|_solo_huesos.fbx                   el mismo disparo solo de cintura para arriba
    datos/piezas_<p>.json                                       curvas de las piezas de la pistola por fotograma
    hoja_disparo_<ronda>.png, hoja_apuntar_<ronda>.png         hojas de contactos (normal y VIP, una fila cada una)
"""

import argparse
import json
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(AQUI, "..", "..", "movimiento", "herramientas"))  # ciclo, rbxmx, marcha, render_mov
sys.path.insert(2, os.path.join(AQUI, "..", "..", "herramientas"))  # rig_r6, exportar_fbx, punetazo_fuerte

import bpy  # noqa: E402  (antes que mathutils)
from mathutils import Vector  # noqa: E402

import ciclo  # noqa: E402
import disparo as D  # noqa: E402
import exportar_fbx  # noqa: E402
import marcha  # noqa: E402
import rbxmx as R  # noqa: E402
import rbxmx_pistola as RP  # noqa: E402
import rig_r6 as r6  # noqa: E402

ESTILOS = ("chatarra", "vip")
CENTROS = {  # centro de cada pieza en reposo (studs, Blender): los de la #17
    "HumanoidRootPart": (0, 0, 3), "Torso": (0, 0, 3), "Head": (0, 0, 4.5), "Left Arm": (1.5, 0, 3),
    "Right Arm": (-1.5, 0, 3), "Left Leg": (0.5, 0, 1), "Right Leg": (-0.5, 0, 1),
}


class Anim:
    """Una animación: nombre de archivo, función de pose, duración, prioridad y pesos."""

    def __init__(self, nombre, estilo, tipo):
        self.NOMBRE = nombre
        self.estilo = estilo
        self.tipo = tipo
        self.FPS = D.FPS
        if tipo == "apuntar":
            self.calcular_pose = lambda f: D.calcular_pose_apuntar(f, estilo)
            self.ULTIMO_FOTOGRAMA, self.PRIORIDAD, self.BUCLE = D.CICLO_APUNTAR, "Action", True
            self.PESOS, self.MARCADORES = D.PESOS["apuntar"], {}
        else:
            variante = "completo" if tipo == "disparo" else "movil"
            self.calcular_pose = lambda f: D.calcular_pose_disparo(f, estilo, variante)
            self.ULTIMO_FOTOGRAMA, self.PRIORIDAD, self.BUCLE = D.ULTIMO_DISPARO, "Action2", False
            self.PESOS, self.MARCADORES = D.PESOS[variante], D.MARCADORES


# --------------------------------------------------------------------------------------------------------------
# Comprobaciones
# --------------------------------------------------------------------------------------------------------------


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0


def comprobar_pies(anim):
    """Pies que no se hunden ni patinan (disparo completo). Devuelve las medidas (studs)."""
    hundido = patina_izq = patina_der = 0.0
    ref = {}
    e = D.ESTILOS[anim.estilo]
    for f in range(anim.ULTIMO_FOTOGRAMA + 1):
        pose = anim.calcular_pose(f)
        paso, alto = D.canal_paso(f, e)
        huellas = D._huellas(paso * e["paso"])
        for pierna, lado in ciclo.PIERNAS.items():
            hundido = max(hundido, -ciclo.suelo_minimo(pose, pierna))
            c = ciclo.punto_mundo(pose, pierna, Vector((-0.5 * lado, ciclo.CENTRO_BOTA_Y, -2)))
            if pierna == "Left Leg":
                ref.setdefault(pierna, c)
                patina_izq = max(patina_izq, (Vector((c.x, c.y, 0)) - Vector((ref[pierna].x, ref[pierna].y, 0))).length)
            elif alto < 1e-3:  # la derecha, cuando está apoyada, debe estar en su huella
                h = huellas[pierna]
                patina_der = max(patina_der, (Vector((c.x, c.y, 0)) - Vector((h[0], h[1], 0))).length)
    return dict(hundido=hundido, patina_izq=patina_izq, patina_der=patina_der)


def comprobar_contra_blender(armature, anim):
    peor = 0.0
    paso = max(1, anim.ULTIMO_FOTOGRAMA // 8)
    for f in list(range(0, anim.ULTIMO_FOTOGRAMA + 1, paso)) + [anim.ULTIMO_FOTOGRAMA]:
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        pose = anim.calcular_pose(f)
        for pb in armature.pose.bones:
            peor = max(peor, (pb.head - pose.mundo(pb.name)[0] * r6.ESTUDIO).length)
    return peor / r6.ESTUDIO


def centros_roblox_de_pose(pose):
    out = {}
    for h, c in CENTROS.items():
        pos, rot = pose.mundo(h)
        out[h] = R.B @ (pos + rot @ (Vector(c) - Vector(r6.ARTICULACIONES[h])))
    return out


def comprobar_rbxmx(ruta, anim):
    """Lee el .rbxmx, comprueba pesos, marcadores, prioridad y bucle, y reproduce los Motor6D como Roblox."""
    props, claves = RP.leer(ruta)
    assert props["Loop"] == ("true" if anim.BUCLE else "false")
    assert props["Priority"] == str(R.PRIORIDADES[anim.PRIORIDAD]), props["Priority"]
    assert len(claves) == anim.ULTIMO_FOTOGRAMA + 1, len(claves)
    peor = 0.0
    vistos = {}
    for f, (t, nombre, marcas, poses, pesos) in enumerate(claves):
        assert abs(t - f / anim.FPS) < 1e-4
        assert pesos == {h: float(anim.PESOS[h]) for h in anim.PESOS}, pesos
        for m in marcas:
            vistos.setdefault(m, f)
        reales = R.centros_roblox(poses)
        esperados = centros_roblox_de_pose(RP.enmascarar(anim.calcular_pose(f), anim.PESOS))
        peor = max(peor, max((reales[h] - esperados[h]).length for h in reales))
    esperadas = {n: f for f, lista in anim.MARCADORES.items() for n, _ in lista}
    assert vistos == esperadas, (vistos, esperadas)
    return peor, claves[-1][0], vistos


def verificar_fbx(ruta, anim):
    """Reimporta el FBX (solo huesos) y compara las articulaciones con la animación en todos los fotogramas."""
    escena_vacia()
    bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y", automatic_bone_orientation=False)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    assert {b.name for b in arm.data.bones} == set(r6.ARTICULACIONES)
    for b in arm.data.bones:
        assert (b.parent.name if b.parent else None) == r6.PADRE[b.name], b.name
    inicio, fin = (int(round(x)) for x in arm.animation_data.action.frame_range)
    assert fin - inicio == anim.ULTIMO_FOTOGRAMA, (inicio, fin)
    assert round(bpy.context.scene.render.fps / bpy.context.scene.render.fps_base) == anim.FPS
    peor = 0.0
    for f in range(anim.ULTIMO_FOTOGRAMA + 1):
        bpy.context.scene.frame_set(f + inicio)
        bpy.context.view_layer.update()
        pose = anim.calcular_pose(f)
        for pb in arm.pose.bones:
            peor = max(peor, ((arm.matrix_world @ pb.head) / r6.ESTUDIO - pose.mundo(pb.name)[0]).length)
    return peor


# --------------------------------------------------------------------------------------------------------------
# Datos de las piezas de la pistola (para animarlas en Roblox)
# --------------------------------------------------------------------------------------------------------------


def datos_piezas(estilo):
    """Curvas por fotograma de lo que se mueve en la pistola, en el disparo y al apuntar (60 fps)."""
    out = {"fps": D.FPS, "fotograma_disparo": D.FOTOGRAMA_DISPARO, "disparo": [], "apuntar": []}
    if estilo == "chatarra":
        out["unidades"] = {"rueda": "grados sobre su eje (X)", "deposito": "studs hacia arriba (Y de Roblox)",
                           "chispas": "0 nada, 0,35 chisporroteo, 1 ráfaga"}
        for f in range(D.ULTIMO_DISPARO + 1):
            p = D.piezas_chatarra(f)
            out["disparo"].append({"f": f, **{k: round(v, 4) for k, v in p.items()}})
        for f in range(0, D.CICLO_APUNTAR + 1, 2):
            p = D.piezas_apuntar(f, estilo)
            out["apuntar"].append({"f": f, **{k: round(v, 4) for k, v in p.items()}})
    else:
        out["unidades"] = {"anillos": "grados acumulados [anillo1, anillo2, anillo3] sobre el eje del cañón (Z de Roblox)",
                           "nucleo_escala": "factor sobre el tamaño del núcleo",
                           "nucleo_blanco": "0 = su color, 1 = blanco (mezcla del Color3)"}
        for f in range(D.ULTIMO_DISPARO + 1):
            p = D.piezas_vip(f)
            out["disparo"].append({"f": f, "anillos": [round(a, 2) for a in p["anillos"]],
                                   "nucleo_escala": round(p["nucleo_escala"], 4), "nucleo_blanco": round(p["nucleo_blanco"], 4)})
        for f in range(0, D.CICLO_APUNTAR + 1, 2):
            p = D.piezas_apuntar(f, estilo)
            out["apuntar"].append({"f": f, "anillos": [round(a, 2) for a in p["anillos"]],
                                   "nucleo_escala": round(p["nucleo_escala"], 4), "nucleo_blanco": 0.0})
    return out


# --------------------------------------------------------------------------------------------------------------
# Exportación de una animación
# --------------------------------------------------------------------------------------------------------------


def exportar(anim, salida, con_malla=True, con_blend=True):
    base = os.path.join(salida, anim.NOMBRE)
    print(f"\n=== {anim.NOMBRE} ({anim.ULTIMO_FOTOGRAMA} fotogramas a {anim.FPS} fps)")
    if anim.tipo == "apuntar":
        cierre = marcha.comprobar_bucle(anim.calcular_pose, anim.ULTIMO_FOTOGRAMA)
        print(f"[ok] bucle: diferencia entre el último fotograma y el primero = {cierre:.2e}")
        assert cierre < 1e-6, "el bucle no cierra"
    elif anim.tipo == "disparo":
        m = comprobar_pies(anim)
        print("     pies:", {k: round(v, 4) for k, v in m.items()})
        assert m["hundido"] <= 0.01 and m["patina_izq"] <= 0.03 and m["patina_der"] <= 0.04, m
        p0, p1 = anim.calcular_pose(0), anim.calcular_pose(anim.ULTIMO_FOTOGRAMA)
        vuelta = max((p0.mundo(h)[0] - p1.mundo(h)[0]).length for h in r6.ARTICULACIONES)
        print(f"[ok] el último fotograma vuelve a la pose de partida (diferencia {vuelta:.2e} studs)")
        assert vuelta < 1e-3
    escena_vacia()
    armature, mallas = r6.construir_rig()
    ciclo.hornear(armature, anim.NOMBRE, anim.calcular_pose, anim.ULTIMO_FOTOGRAMA, anim.FPS)
    error = comprobar_contra_blender(armature, anim)
    print(f"[ok] FK propia vs Blender: desviación máxima {error:.5f} studs")
    assert error < 1e-3
    ruta_rbx = f"{base}.rbxmx"
    RP.escribir(ruta_rbx, anim.NOMBRE, anim.calcular_pose, anim.ULTIMO_FOTOGRAMA, anim.FPS, anim.PRIORIDAD, anim.BUCLE,
                anim.PESOS, anim.MARCADORES)
    peor, dur, marcas = comprobar_rbxmx(ruta_rbx, anim)
    print(f"[ok] RBXMX: {dur:.3f} s, prioridad {anim.PRIORIDAD}, marcadores {marcas}; reproducido como en Roblox, "
          f"desviación máxima {peor:.5f} studs")
    assert peor < 1e-3
    exportar_fbx.exportar(armature, mallas, f"{base}.fbx" if con_malla else None, f"{base}_solo_huesos.fbx")
    if con_blend:
        bpy.ops.wm.save_as_mainfile(filepath=f"{base}.blend")


# --------------------------------------------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true", help="renders pequeños y con pocas muestras")
    ap.add_argument("--gif", action="store_true", help="también los GIF (tardan)")
    ap.add_argument("--sin-render", action="store_true", help="solo exportar y comprobar")
    ap.add_argument("--solo-render", action="store_true", help="solo los renders (sin volver a escribir los archivos de animación)")
    a = ap.parse_args()
    sal = os.path.abspath(a.salida)
    os.makedirs(os.path.join(sal, "datos"), exist_ok=True)
    tmp = os.path.join(sal, "_render_tmp")

    if not a.solo_render:
        for estilo in ESTILOS:
            for tipo in ("apuntar", "disparo", "disparo_movil"):
                nombre = f"{tipo}_{estilo}" if tipo != "disparo_movil" else f"disparo_{estilo}_movil"
                anim = Anim(nombre, estilo, tipo)
                exportar(anim, sal, con_malla=tipo != "disparo_movil", con_blend=tipo != "disparo_movil")
            with open(os.path.join(sal, "datos", f"piezas_{estilo}.json"), "w", encoding="utf-8") as f:
                json.dump(datos_piezas(estilo), f, indent=1, ensure_ascii=False)
        # FBX reimportados: un solo huesos de cada tipo
        for estilo in ESTILOS:
            for tipo in ("apuntar", "disparo"):
                anim = Anim(f"{tipo}_{estilo}", estilo, tipo)
                peor = verificar_fbx(os.path.join(sal, f"{anim.NOMBRE}_solo_huesos.fbx"), anim)
                print(f"[ok] {anim.NOMBRE}_solo_huesos.fbx reimportado: desviación máxima {peor:.4f} studs")
                assert peor < 0.02

    if a.sin_render:
        return
    import pistola_escena as PE

    rutas_disp, rutas_apu, gifs = {}, {}, {}
    gif_disp = list(range(0, D.ULTIMO_DISPARO + 1, 2))
    gif_apu = list(range(0, D.CICLO_APUNTAR, 4))
    cols_disp = D.FOTOGRAMAS_CLAVE
    cols_apu = [(f, "") for f in range(0, D.CICLO_APUNTAR, 20)]
    vistas = ("Lateral", "3/4")
    muestras = 8 if a.rapido else 16
    for estilo in ESTILOS:
        piezas_d = D.piezas_chatarra if estilo == "chatarra" else D.piezas_vip
        sc = PE.Escena(estilo, lambda f, e=estilo: D.calcular_pose_disparo(f, e), D.ULTIMO_DISPARO, piezas_d,
                       os.path.join(tmp, estilo, "disparo"), muestras, a.rapido)
        frames = sorted({f for f, _ in cols_disp} | (set(gif_disp) if a.gif else set()))
        for v in vistas:
            for f in frames:
                rutas_disp[(estilo, v, f)] = sc.render(f, v)
        if a.gif:
            gifs[f"disparo_{estilo}"] = PE.gif([[rutas_disp[(estilo, v, f)] for f in gif_disp] for v in vistas], gif_disp,
                                               os.path.join(sal, f"disparo_{estilo}.gif"), D.FPS,
                                               f"{D.ESTILOS[estilo]['titulo']}  -  disparo  -  60 fps")
        sc = PE.Escena(estilo, lambda f, e=estilo: D.calcular_pose_apuntar(f, e), D.CICLO_APUNTAR,
                       lambda f, e=estilo: D.piezas_apuntar(f, e), os.path.join(tmp, estilo, "apuntar"), muestras,
                       a.rapido, con_efectos=False)
        frames = sorted({f for f, _ in cols_apu} | (set(gif_apu) if a.gif else set()))
        for v in vistas:
            for f in frames:
                rutas_apu[(estilo, v, f)] = sc.render(f, v)
        if a.gif:
            gifs[f"apuntar_{estilo}"] = PE.gif([[rutas_apu[(estilo, v, f)] for f in gif_apu] for v in vistas], gif_apu,
                                               os.path.join(sal, f"apuntar_{estilo}.gif"), D.FPS,
                                               f"{D.ESTILOS[estilo]['titulo']}  -  apuntar (bucle de 2 s)")
    filas, etiquetas = [], []
    for v in vistas:
        for estilo in ESTILOS:
            filas.append([rutas_disp[(estilo, v, f)] for f, _ in cols_disp])
            etiquetas.append(f"{D.ESTILOS[estilo]['titulo']}\n{v}")
    PE.hoja(filas, cols_disp, os.path.join(sal, f"hoja_disparo_{a.ronda}.png"),
            "Disparo de la pistola de portales (60 fps): carga 0,15 s, retroceso, hitstop y vuelta. Normal frente a VIP", etiquetas)
    filas = []
    for v in vistas:
        for estilo in ESTILOS:
            filas.append([rutas_apu[(estilo, v, f)] for f, _ in cols_apu])
    PE.hoja(filas, cols_apu, os.path.join(sal, f"hoja_apuntar_{a.ronda}.png"),
            "Apuntar (bucle de 2 s): la normal tiembla y se va de lado; la VIP está firme", etiquetas)
    print("[ok] hojas y GIF:", list(gifs))


main()
