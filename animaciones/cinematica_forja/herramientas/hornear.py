"""
Monta la escena de la cinemática en Blender y hornea toda la animación (una clave por fotograma).

    python hornear.py [--blend salida.blend]

Lo usan render.py (vídeo y hoja de contactos) y documento.py (datos para Roblox).
"""

import argparse
import math
import os
import random
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

import cinematica as ci  # noqa: E402
import escena as es  # noqa: E402
import linea_tiempo as lt  # noqa: E402


def _clave_matriz(o, M, f, escala=False):
    o.rotation_mode = "QUATERNION"
    loc, rot, esc = M.decompose()
    o.location = loc
    o.rotation_quaternion = rot
    o.keyframe_insert("location", frame=f)
    o.keyframe_insert("rotation_quaternion", frame=f)
    if escala:
        o.scale = esc
        o.keyframe_insert("scale", frame=f)


def _interpolacion(tipo):
    bpy.context.preferences.edit.keyframe_new_interpolation_type = tipo


def montar():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.frame_start = 0
    scn.frame_end = lt.DURACION - 1
    scn.render.fps = lt.FPS
    es.mundo(scn)
    es.importar_forja()
    obs = {}
    obs["compuerta"] = es.compuerta_horno()
    obs["r6"] = es.maniqui()
    obs["tenazas"] = es.tenazas()
    obs["martillo"] = es.martillo()
    obs["pieza"], obs["pz_temp"], obs["pz_princ"], obs["pz_pulido"], obs["pz_rug"] = es.pieza()
    obs["llamas"], obs["llamas_ruido"] = es.llamas()
    obs["agua"], obs["ola"] = es.agua_temple()
    obs["vapor"] = es.bocanadas_vapor(lt.VAPOR["bocanadas"])
    # Destello del filo: una chispa diminuta y muy brillante (el compositor la convierte en estrella)
    obs["destello"] = es.caja_biselada("Destello", (0.03, 0.03, 0.03), es.mat_simple(
        "Destello", (1, 1, 1), emision=(1.0, 0.95, 0.85), fuerza=0.0), 0.01)
    obs["destello"].visible_shadow = False
    # Luces
    obs["luz_horno"] = es.luz("LuzHorno", "POINT", lt.LUZ_HORNO, (-2.6, 3.6, 3.9), (1.0, 0.45, 0.14), 0.9)
    obs["luz_boca"] = es.luz("LuzBoca", "AREA", 0.0, (-2.7, 1.0, 3.6), (1.0, 0.42, 0.12), apuntar=(-2.7, -3.0, 3.6), tam=2.6)
    obs["luz_pieza"] = es.luz("LuzPieza", "POINT", 0.0, (0, 0, 3), (1.0, 0.5, 0.2), 0.25)
    obs["contra"] = es.luz("Contraluz", "AREA", lt.LUZ_CONTRA, (6, -14, 12), (0.55, 0.65, 1.0), apuntar=(-1, 0, 3), tam=6)
    obs["contra2"] = es.luz("Contraluz2", "AREA", lt.LUZ_CONTRA * 0.8, (-12, 4, 10), (0.5, 0.6, 1.0), apuntar=(0, -2, 3),
                            tam=6)
    obs["relleno"] = es.luz("RellenoBarril", "POINT", 260.0, (4.5, -5.5, 6.5), (1.0, 0.7, 0.5), 1.5)
    # Rebote cálido del fuego sobre la zona de trabajo (suave, desde arriba y delante del horno)
    obs["rebote"] = es.luz("ReboteFuego", "AREA", 350.0, (-1.0, -2.5, 11.0), (1.0, 0.55, 0.3), apuntar=(-1.0, -2.0, 0),
                           tam=8)
    cam_d = bpy.data.cameras.new("Camara")
    cam_d.sensor_width = 36
    cam_d.dof.use_dof = True
    cam = bpy.data.objects.new("Camara", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    obs["camara"] = cam
    _particulas(obs)
    return scn, obs


def _particulas(obs):
    chispa, ascua, burbuja = es.particulas_base()
    # Ascuas que salen de la boca del horno y suben (siempre)
    em = es.emisor_disco("EmisorAscuas", (-2.7, 1.9, 4.4), 1.0, normal=(0, -0.6, 1))
    a = lt.ASCUAS_HORNO
    es._sistema_particulas(em, "Ascuas", ascua, cantidad=a["cantidad"], inicio=a["inicio"], fin=a["fin"], vida=a["vida"],
                           normal=0.6, aleatorio=0.5, velocidad=(0, -0.4, 1.2), gravedad=-0.08, browniano=0.9,
                           tam=1.0, tam_aleatorio=0.7, arrastre=0.4, semilla=3)
    # Estallido de chispas al abrir la compuerta
    em = es.emisor_disco("EmisorCompuerta", (-2.7, 1.3, 2.8), 1.1, normal=(0, -1, 0.5))
    a = lt.ESTALLIDO_COMPUERTA
    es._sistema_particulas(em, "EstallidoCompuerta", chispa, cantidad=a["cantidad"], inicio=a["inicio"], fin=a["fin"],
                           vida=a["vida"], normal=5.0, aleatorio=2.5, velocidad=(0, -1.5, 2.0), gravedad=0.6,
                           tam=1.0, tam_aleatorio=0.6, semilla=7)
    # Chispas al sacar la pieza
    em = es.emisor_disco("EmisorSacar", (-2.65, 1.0, 3.6), 0.6, normal=(0, -1, 0.6))
    a = lt.CHISPAS_SACAR
    es._sistema_particulas(em, "ChispasSacar", chispa, cantidad=a["cantidad"], inicio=a["inicio"], fin=a["fin"],
                           vida=a["vida"], normal=4.0, aleatorio=2.5, gravedad=1.0, semilla=11)
    # Martillazos: una ráfaga por golpe, cada una más grande
    for i, f in enumerate(lt.IMPACTOS):
        k = lt.FUERZA_GOLPE[i]
        p = ci.punto_golpe(f)
        em = es.emisor_disco(f"EmisorGolpe{i + 1}", p + Vector((0, 0, 0.02)), 0.12)
        es._sistema_particulas(em, f"Golpe{i + 1}", chispa, cantidad=lt.CHISPAS_GOLPE[i], inicio=f, fin=f + 1,
                               vida=12 + 8 * k, vida_aleatoria=0.6, normal=5.0 + 9.0 * k, aleatorio=7.0 + 8.0 * k,
                               gravedad=1.0, tam=1.0 + 0.4 * k, tam_aleatorio=0.6, semilla=20 + i)
    # Burbujas en el agua durante el temple
    em = es.emisor_disco("EmisorBurbujas", es.CENTRO_BARRIL + Vector((-0.05, 0.3, 0.02)), 0.55)
    a = lt.BURBUJAS
    es._sistema_particulas(em, "Burbujas", burbuja, cantidad=a["cantidad"], inicio=a["inicio"], fin=a["fin"],
                           vida=a["vida"], normal=0.4, aleatorio=0.3, gravedad=0.0, tam=1.0, tam_aleatorio=0.8,
                           semilla=31)
    # Chispas que salen de la pieza al hundirla (antes de apagarse)
    em = es.emisor_disco("EmisorSalpicadura", es.CENTRO_BARRIL + Vector((-0.05, 0.3, 0.05)), 0.25)
    es._sistema_particulas(em, "Salpicadura", chispa, cantidad=60, inicio=lt.CONTACTO_AGUA, fin=lt.CONTACTO_AGUA + 3,
                           vida=10, normal=4.0, aleatorio=3.0, gravedad=1.0, semilla=41)


def _vapor(obs, f):
    """Bocanadas de vapor: nacen en el punto de entrada, crecen, suben y se desvanecen."""
    v = lt.VAPOR
    rnd = random.Random(5)
    base = es.CENTRO_BARRIL + Vector((-0.05, 0.3, 0.0))
    for i, (o, dens) in enumerate(obs["vapor"]):
        ini = v["inicio"] + i * 2.6 + rnd.uniform(0, 1.5)
        vida = v["duracion"] * rnd.uniform(0.7, 1.1)
        deriva = Vector((rnd.uniform(-0.7, 0.7), rnd.uniform(-0.9, 0.3), 0))
        alto = rnd.uniform(4.0, 6.5)
        r0, r1 = rnd.uniform(0.35, 0.5), rnd.uniform(1.4, 2.3)
        t = (f - ini) / vida
        visible = 0.0 <= t <= 1.0 and f < v["fin"]
        if visible:
            sube = 1 - (1 - t) ** 2.2
            o.location = base + deriva * t + Vector((0, 0, 0.3 + alto * sube))
            r = r0 + (r1 - r0) * t**0.6
            o.scale = (r, r, r * 1.15)
            o.rotation_euler = (0, 0, i + t * 0.8)
            d = 1.6 * min(1.0, t / 0.08) * (1 - t) ** 1.6
            d *= max(0.0, min(1.0, (v["fin"] - f) / 12))  # se disipa antes del plano final
        else:
            d = 0.0
        dens.inputs[1].default_value = d
        dens.inputs[1].keyframe_insert("default_value", frame=f)
        o.hide_render = not visible
        o.keyframe_insert("hide_render", frame=f)
        if visible:
            o.keyframe_insert("location", frame=f)
            o.keyframe_insert("scale", frame=f)
            o.keyframe_insert("rotation_euler", frame=f)


def hornear(scn, obs, verbose=True):
    _interpolacion("LINEAR")
    pieza = obs["pieza"]
    claves = pieza.data.shape_keys.key_blocks
    for f in range(lt.DURACION):
        est = ci.evaluar(f)
        for nombre, o in obs["r6"].items():
            _clave_matriz(o, est.M[nombre], f)
        _clave_matriz(obs["tenazas"], est.M_tenazas, f)
        _clave_matriz(obs["martillo"], est.M_martillo, f)
        _clave_matriz(pieza, est.M_pieza, f)
        # Forma: la etapa e mezcla la shape key de la etapa entera de abajo y la de arriba
        e = max(0.0, min(5.0, est.etapa))
        for i in range(1, 6):
            claves[i].value = max(0.0, 1 - abs(e - i))
            if e >= 5 and i == 5:
                claves[i].value = 1.0
            claves[i].keyframe_insert("value", frame=f)
        # Calor
        obs["pz_temp"].inputs["Temperature"].default_value = est.temperatura
        obs["pz_temp"].inputs["Temperature"].keyframe_insert("default_value", frame=f)
        obs["pz_princ"].inputs["Emission Strength"].default_value = est.brillo
        obs["pz_princ"].inputs["Emission Strength"].keyframe_insert("default_value", frame=f)
        obs["pz_princ"].inputs["Emission Color"].default_value = (*ci.color_pieza(est.temperatura), 1)
        obs["pz_princ"].inputs["Emission Color"].keyframe_insert("default_value", frame=f)
        for nodo in (obs["pz_pulido"], obs["pz_rug"]):
            nodo.inputs[0].default_value = est.pulido
            nodo.inputs[0].keyframe_insert("default_value", frame=f)
        lp = obs["luz_pieza"]
        lp.location = est.centro_pieza + Vector((0, 0, 0.25))
        lp.keyframe_insert("location", frame=f)
        destello_golpe = 0.0
        for i, fi in enumerate(lt.IMPACTOS):
            if fi <= f < fi + 6:
                destello_golpe = max(destello_golpe, 2.2 * lt.FUERZA_GOLPE[i] * math.exp(-(f - fi) / 1.6))
        lp.data.energy = est.brillo * lt.LUZ_PIEZA_POR_BRILLO * (1 + destello_golpe)
        lp.data.color = ci.color_pieza(est.temperatura)
        lp.data.keyframe_insert("energy", frame=f)
        lp.data.keyframe_insert("color", frame=f)
        # Destello del filo
        d = obs["destello"]
        if est.destello:
            pos, fuerza = est.destello
            d.location = pos
            d.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 3000 * fuerza
        else:
            d.location = (0, 0, -50)
            d.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.0
        d.keyframe_insert("location", frame=f)
        d.data.materials[0].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].keyframe_insert(
            "default_value", frame=f)
        # Compuerta
        obs["compuerta"].location.z = ci.COMPUERTA_BASE.z + est.compuerta
        obs["compuerta"].keyframe_insert("location", frame=f)
        # Luces del horno: parpadeo de fuego (ruido) y la luz que sale por la boca al abrir
        parpadeo = 1 + 0.18 * noise.noise(Vector((f * 0.11, 0.3, 0.7))) + 0.08 * noise.noise(Vector((f * 0.37, 2.1, 0.2)))
        obs["luz_horno"].data.energy = lt.LUZ_HORNO * parpadeo
        obs["luz_horno"].data.keyframe_insert("energy", frame=f)
        obs["luz_boca"].data.energy = ci.muestrear(lt.LUZ_BOCA, f) * parpadeo
        obs["luz_boca"].data.keyframe_insert("energy", frame=f)
        # Agua y vapor
        obs["ola"].height = ci.muestrear(lt.OLA_AGUA, f)
        obs["ola"].keyframe_insert("height", frame=f)
        _vapor(obs, f)
        # Exposición (fundido de entrada y a negro)
        scn.view_settings.exposure = ci.muestrear(lt.EXPOSICION, f) + ci.plano_en(f).get("exposicion", 0.0)
        scn.view_settings.keyframe_insert("exposure", frame=f)
        if verbose and f % 50 == 0:
            print(f"[horneado] fotograma {f}")
    # Cámara: claves constantes (cortes secos sin estela de desenfoque entre planos)
    _interpolacion("CONSTANT")
    cam = obs["camara"]
    for f in range(lt.DURACION):
        est = ci.evaluar(f)
        M, lente, fstop, foco, _, _ = ci.matriz_camara(f, est)
        _clave_matriz(cam, M, f)
        cam.data.lens = lente
        cam.data.dof.focus_distance = foco
        cam.data.dof.aperture_fstop = fstop
        for prop in ("lens",):
            cam.data.keyframe_insert(prop, frame=f)
        cam.data.dof.keyframe_insert("focus_distance", frame=f)
        cam.data.dof.keyframe_insert("aperture_fstop", frame=f)
    _interpolacion("LINEAR")
    # Llamas: el ruido avanza y sube sin parar
    ruido = obs["llamas_ruido"]
    mapa = ruido.inputs["Vector"].links[0].from_node
    for f, w, z in ((0, 0.0, 0.0), (lt.DURACION, lt.DURACION * 0.05, -lt.DURACION * 0.035)):
        ruido.inputs["W"].default_value = w
        ruido.inputs["W"].keyframe_insert("default_value", frame=f)
        mapa.inputs["Location"].default_value[2] = z
        mapa.inputs["Location"].keyframe_insert("default_value", index=2, frame=f)
    _interpolacion("BEZIER")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", default="")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    scn, obs = montar()
    hornear(scn, obs)
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
        print("[ok]", a.blend)


if __name__ == "__main__":
    main()
