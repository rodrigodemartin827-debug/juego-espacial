"""
Datos de la cinemática para recrearla en Roblox:

  * roblox/CinematicaForjaDatos.luau  módulo de datos (claves para TweenService y muestreo a 10 fps)
  * cinematica_forja_keyframes.json   lo mismo en JSON
  * cinematica_forja_r6_solo_huesos.fbx  la animación del cuerpo (7 huesos R6) para el Animation Editor
  * verificación del FBX reimportándolo

    python documento.py

Ejes: Blender (x, y, z) -> Roblox (x, z, -y), con el origen en el centro del suelo de la forja a ras de tierra; es el
mismo sistema que modelos/forja/datos/forja_montaje.json. Así, si la forja se monta con MontarForja.luau, basta con
sumar el CFrame del suelo.
"""

import json
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "..", "herramientas"))

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import cinematica as ci  # noqa: E402
import escena as es  # noqa: E402
import linea_tiempo as lt  # noqa: E402
import rig_r6 as r6  # noqa: E402

SALIDA = os.path.abspath(os.path.join(AQUI, ".."))
PASO_MUESTREO = 3  # fotogramas entre muestras (10 por segundo)

# Mundo: Blender -> Roblox
P = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))
# Ejes locales de una pieza: en Blender delante es -Y y arriba +Z; en Roblox delante es -Z y arriba +Y.
Q = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))
SENSOR_ALTO = 36.0 * 9 / 16  # mm (sensor de 36 mm a 16:9)

EASING_ROBLOX = {  # easing de linea_tiempo -> (EasingStyle, EasingDirection)
    "suave": ["Quad", "InOut"],  # smootherstep: lo más parecido de Roblox
    "entra": ["Cubic", "In"],
    "sale": ["Cubic", "Out"],
    "golpe": ["Quint", "Out"],
    "rebote": ["Back", "Out"],
    "lineal": ["Linear", "InOut"],
    "cte": ["Constant", "In"],  # no es un tween: el valor cambia de golpe al final del tramo
}


def r(v, n=3):
    return round(float(v), n)


def pos_roblox(v):
    v = P @ Vector(v)
    return [r(v.x), r(v.y), r(v.z)]


def cframe(M, ejes_pieza=True):
    """Matriz de Blender (studs) -> 12 componentes de CFrame.new(x, y, z, R00, R01, ..., R22) en Roblox.
    ejes_pieza: la pieza tiene ejes de «personaje» (delante -Y en Blender) y en Roblox delante es -Z."""
    rot = M.to_3x3().normalized()
    rr = P @ rot @ (Q.transposed() if ejes_pieza else P.transposed())
    p = pos_roblox(M.to_translation())
    return p + [r(rr[i][j], 4) for i in range(3) for j in range(3)]


def color3(k, brillo=1.0):
    c = ci.cuerpo_negro_srgb(max(1000.0, k))
    return [r(min(1.0, x * brillo)) for x in c]


def fov(lente):
    return r(math.degrees(2 * math.atan(SENSOR_ALTO / 2 / lente)), 2)


# ---------------------------------------------------------------------------------------------------------------


def claves_raiz():
    res = []
    for f, (x, y, giro), ease in lt.RAIZ:
        M = Matrix.Translation((x, y, es.ALTO_SUELO + 3.0)) @ Matrix.Rotation(math.radians(giro), 4, "Z")
        res.append({"t": r(f / lt.FPS), "cframe": cframe(M), "easing": list(EASING_ROBLOX[ease])})
    return res


def claves_simples(claves, conv=lambda v: r(v)):
    return [{"t": r(f / lt.FPS), "valor": conv(v), "easing": list(EASING_ROBLOX[e])} for f, v, e in claves]


def planos():
    res = []
    for p in lt.PLANOS:
        claves = []
        fs = sorted({p["inicio"], p["fin"] - 1} | {c[0] for c in p.get("claves", [])})
        if "orbita" in p:
            fs = list(range(p["inicio"], p["fin"], 6)) + [p["fin"] - 1]
        for f in fs:
            if not p["inicio"] <= f < p["fin"]:
                continue
            est = ci.evaluar(f)
            pos, mira, lente, fstop, foco, _ = ci.camara(f, est)
            claves.append({"t": r(f / lt.FPS), "posicion": pos_roblox(pos), "mira_a": pos_roblox(mira),
                           "FieldOfView": fov(lente)})
        res.append({"nombre": p["nombre"], "inicio": r(p["inicio"] / lt.FPS), "fin": r(p["fin"] / lt.FPS),
                    "easing": ["Linear", "InOut"] if "orbita" in p else ["Quad", "InOut"],
                    "orbita": "orbita" in p, "claves": claves})
    return res


def temblores():
    res = [{"t": r(f / lt.FPS), "grados": lt.TEMBLOR_GOLPE[i], "caida_s": 0.11, "duracion_s": r(14 / lt.FPS)}
           for i, f in enumerate(lt.IMPACTOS)]
    res.append({"t": r(lt.CONTACTO_AGUA / lt.FPS), "grados": 0.35, "caida_s": 0.1, "duracion_s": 0.33})
    return res


def calor():
    """Color de la pieza (Color3 en Neon) y su PointLight en cada clave de temperatura/brillo."""
    fs = sorted({c[0] for c in lt.TEMPERATURA} | {c[0] for c in lt.BRILLO} | {c[0] for c in lt.PULIDO})
    res = []
    for f in fs:
        k = ci.muestrear(lt.TEMPERATURA, f)
        b = ci.muestrear(lt.BRILLO, f)
        pul = ci.muestrear(lt.PULIDO, f)
        caliente = b > 0.05
        res.append({
            "t": r(f / lt.FPS), "temperatura_k": r(k, 0), "brillo": r(b, 2),
            "Material": "Neon" if caliente else "Metal",
            "Color": color3(k) if caliente else [r(0.11 + 0.5 * pul), r(0.1 + 0.52 * pul), r(0.095 + 0.56 * pul)],
            "Transparency_neon": r(max(0.0, 0.6 - b / 7.2 * 0.6)) if caliente else 0.0,
            "Reflectance": r(0.05 + 0.35 * pul),
            "PointLight": {"Brightness": r(b * 0.9, 2), "Range": r(6 + b * 2.2, 1), "Color": color3(k)},
        })
    return res


def particulas():
    golpes = [{"t": r(f / lt.FPS), "Emit": lt.CHISPAS_GOLPE[i], "Speed": [r(8 + 9 * lt.FUERZA_GOLPE[i], 1),
              r(16 + 14 * lt.FUERZA_GOLPE[i], 1)], "Lifetime": [0.25, r(0.4 + 0.3 * lt.FUERZA_GOLPE[i], 2)],
              "posicion": pos_roblox(ci.punto_golpe(f))} for i, f in enumerate(lt.IMPACTOS)]
    return {
        "chispas_martillo": {
            "nota": "ParticleEmitter en el Attachment «Golpe» del yunque. Rate = 0; en cada impacto :Emit(n). "
                    "SpreadAngle (70, 70), Acceleration (0, -40, 0), Drag 1, LightEmission 1, Size 0.12 -> 0, "
                    "Color de blanco amarillento a naranja oscuro (cuerpo negro de 2600 K a 1100 K), "
                    "Orientation = VelocityParallel y Squash para que salgan alargadas.",
            "eventos": golpes,
            "color_secuencia": [color3(2600), color3(1800), color3(1100)],
        },
        "ascuas_horno": {
            "nota": "ParticleEmitter en «Fuego» del horno, siempre encendido: Rate 36, Lifetime 2-3 s, Speed 1-3, "
                    "Acceleration (0, 2, 0), SpreadAngle (30, 30), Size 0.08, LightEmission 1.",
            "Rate": 36, "color": color3(1900)},
        "estallido_compuerta": {"t": r(lt.ESTALLIDO_COMPUERTA["inicio"] / lt.FPS), "Emit": lt.ESTALLIDO_COMPUERTA["cantidad"],
                                "posicion": pos_roblox((-2.7, 1.3, 2.8)), "Speed": [5, 12]},
        "chispas_al_sacar": {"t": r(lt.CHISPAS_SACAR["inicio"] / lt.FPS), "Emit": lt.CHISPAS_SACAR["cantidad"],
                             "posicion": pos_roblox((-2.65, 1.0, 3.6))},
        "vapor": {"t": r(lt.CONTACTO_AGUA / lt.FPS), "duracion_s": r(lt.VAPOR["duracion"] / lt.FPS),
                  "nota": "Attachment «Vapor» del barril. Al tocar el agua: :Emit(30) y Rate 25 durante 1,2 s. "
                          "Textura de humo suave, Size 1 -> 6, Transparency 0.2 -> 1, Speed 4-7 hacia arriba, "
                          "Lifetime 1.4-2 s, RotSpeed -40..40, Color (220, 216, 210), LightInfluence 0.6.",
                  "posicion": pos_roblox(es.CENTRO_BARRIL)},
        "burbujas": {"t": r(lt.BURBUJAS["inicio"] / lt.FPS), "hasta": r(lt.BURBUJAS["fin"] / lt.FPS),
                     "nota": "ParticleEmitter plano sobre el agua (EmissionDirection Top, Speed 0.3), Rate 60.",
                     "posicion": pos_roblox(es.CENTRO_BARRIL)},
        "salpicadura": {"t": r(lt.CONTACTO_AGUA / lt.FPS), "Emit": 60, "posicion": pos_roblox(es.CENTRO_BARRIL)},
    }


def luces():
    return {
        "horno": {"nota": "PointLight dentro del horno (Attachment «Fuego»), parpadeo ±18 % con ruido",
                  "Brightness": 3.0, "Range": 22, "Color": color3(1700)},
        "boca": claves_simples(lt.LUZ_BOCA, lambda v: r(v / 450.0 * 2.0, 2)),
        "fundido_negro": claves_simples(lt.EXPOSICION, lambda v: r(min(0.0, v), 2)),
        "nota_fundido": "Exposición de la cámara: se recrea con un Frame negro a pantalla completa "
                        "(BackgroundTransparency = 1 con exposición 0 y 0 con exposición -9 o menos) o con "
                        "ColorCorrectionEffect.Brightness.",
    }


def muestreo():
    """Cada PASO_MUESTREO fotogramas: CFrame de las 6 piezas del R6, tenazas, martillo, pieza, compuerta y cámara."""
    res = []
    for f in list(range(0, lt.DURACION, PASO_MUESTREO)) + [lt.DURACION - 1]:
        est = ci.evaluar(f)
        Mc, lente, _, _, nombre, _ = ci.matriz_camara(f, est)
        piezas = {}
        for nombre_p, (tam, centro) in es.PIEZAS_R6.items():
            piezas[nombre_p] = cframe(est.M[nombre_p] @ Matrix.Translation(centro))
        raiz = ci.matriz_raiz(f) @ Matrix.Translation((0, 0, 3.0))
        res.append({
            "t": r(f / lt.FPS), "plano": nombre,
            "camara": _camara_cframe(Mc), "FieldOfView": fov(lente),
            "HumanoidRootPart": cframe(raiz), "piezas": piezas,
            "tenazas": cframe(est.M_tenazas), "martillo": cframe(est.M_martillo), "pieza": cframe(est.M_pieza),
            "etapa_pieza": r(est.etapa, 3), "compuerta_subida": r(est.compuerta),
        })
    return res


def _camara_cframe(Mc):
    """La cámara de Blender mira a su -Z local con +Y arriba, igual que la de Roblox: solo cambia el mundo."""
    # columnas en Roblox: X, Y (arriba), Z (detrás) de la cámara
    x, y, z = (P @ Mc.to_3x3().col[i] for i in range(3))
    p = pos_roblox(Mc.to_translation())
    return p + [r(x[0], 4), r(y[0], 4), r(z[0], 4), r(x[1], 4), r(y[1], 4), r(z[1], 4), r(x[2], 4), r(y[2], 4), r(z[2], 4)]


def agarres():
    """Weld de cada herramienta a su brazo (C0 respecto al centro del brazo de Roblox), con el ángulo de agarre
    por defecto. El ángulo real cambia en cada fotograma (ver muestreo): la mano «abre» o «cierra» la herramienta."""
    res = {}
    for herr, lado in (("tenazas", "Left Arm"), ("martillo", "Right Arm")):
        centro = Vector(es.PIEZAS_R6[lado][1])
        M = Matrix.Translation(-centro) @ ci.agarre(herr)
        rot = Q @ M.to_3x3() @ Q.transposed()
        p = Q @ M.to_translation()
        res[herr] = {"brazo": lado, "C0": [r(p.x), r(p.y), r(p.z)] + [r(rot[i][j], 4) for i in range(3) for j in range(3)],
                     "angulo_por_defecto": lt.AGARRE[herr]}
    return res


def etapas():
    return [{"etapa": i, "largo_hoja": e[0], "ancho": e[1], "grueso": e[2], "filo": e[3], "punta": e[4], "espiga": e[5],
             "t_golpe": r(lt.IMPACTOS[i - 1] / lt.FPS) if i else 0.0} for i, e in enumerate(es.ETAPAS)]


def datos():
    return {
        "nota": "Cinemática de la forja (14,5 s a 30 fps). Coordenadas en studs, ejes de Roblox, origen en el centro "
                "del suelo de la forja a ras de tierra (el mismo de modelos/forja/datos/forja_montaje.json). "
                "CFrame = CFrame.new(table.unpack(c)). easing = {EasingStyle, EasingDirection}; «Constant» significa "
                "que el valor cambia de golpe al final del tramo. Generado por documento.py: no editar a mano.",
        "duracion_s": r(lt.DURACION / lt.FPS),
        "fps": lt.FPS,
        "fases": [{"nombre": n, "inicio": r(a / lt.FPS), "fin": r(b / lt.FPS)} for a, b, n in lt.FASES],
        "impactos_s": [r(f / lt.FPS) for f in lt.IMPACTOS],
        "contacto_agua_s": r(lt.CONTACTO_AGUA / lt.FPS),
        "raiz": claves_raiz(),
        "compuerta": {"nota": "Sube en vertical (eje Y de Roblox) estos studs desde su sitio en la boca del horno.",
                      "posicion_cerrada": pos_roblox(ci.COMPUERTA_BASE), "claves": claves_simples(lt.COMPUERTA)},
        "planos_camara": planos(),
        "temblores_camara": temblores(),
        "pieza_calor": calor(),
        "pieza_etapas": etapas(),
        "pieza_etapa_claves": claves_simples(lt.ETAPA),
        "destello_filo": {"inicio": r(lt.DESTELLO[0] / lt.FPS), "fin": r(lt.DESTELLO[1] / lt.FPS),
                          "nota": "Un punto muy brillante recorre el filo de la base a la punta (ParticleEmitter con "
                                  "una estrella, o un Beam corto) con Size 0 -> 1.5 -> 0."},
        "herramientas": agarres(),
        "martillo_en_mano": [r(lt.MARTILLO_EN_MANO[0] / lt.FPS), r(lt.MARTILLO_EN_MANO[1] / lt.FPS)],
        "particulas": particulas(),
        "luces": luces(),
        "muestreo_10fps": muestreo(),
    }


# ---------------------------------------------------------------------------------------------------------------


def a_luau(v, sangria=0):
    pad = "\t" * sangria
    if isinstance(v, dict):
        if not v:
            return "{}"
        partes = []
        for k, x in v.items():
            clave = k if k.isidentifier() else f'["{k}"]'
            partes.append(f"{pad}\t{clave} = {a_luau(x, sangria + 1)},")
        return "{\n" + "\n".join(partes) + f"\n{pad}}}"
    if isinstance(v, list):
        if all(isinstance(x, (int, float)) for x in v):
            return "{ " + ", ".join(a_luau(x) for x in v) + " }"
        return "{\n" + "\n".join(f"{pad}\t{a_luau(x, sangria + 1)}," for x in v) + f"\n{pad}}}"
    if isinstance(v, bool):
        return "true" if v else "false"
    if v is None:
        return "nil"
    if isinstance(v, (int, float)):
        return repr(v)
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def escribir_datos(pivotes=None):
    d = datos()
    if pivotes:
        d["utileria_pivotes"] = pivotes
    with open(os.path.join(SALIDA, "cinematica_forja_keyframes.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(SALIDA, "roblox"), exist_ok=True)
    with open(os.path.join(SALIDA, "roblox", "CinematicaForjaDatos.luau"), "w", encoding="utf-8") as f:
        f.write("--!strict\n-- Datos de la cinemática de la forja (generado por animaciones/cinematica_forja/herramientas/"
                "documento.py: no editar a mano).\n-- Ver animaciones/cinematica_forja/README.md para cómo usarlos.\n\n")
        f.write("local Datos = " + a_luau(d) + "\n\nreturn Datos\n")
    print("[ok] datos:", len(d["muestreo_10fps"]), "muestras")
    return d


def exportar_fbx():
    """Animación del cuerpo (huesos R6) con el rig de animaciones/herramientas/rig_r6.py (en metros)."""
    import exportar_fbx as ex

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.render.fps = lt.FPS
    scn.frame_start, scn.frame_end = 0, lt.DURACION - 1
    arm, mallas = r6.construir_rig()
    bpy.context.preferences.edit.keyframe_new_interpolation_type = "LINEAR"
    for f in range(lt.DURACION):
        est = ci.evaluar(f)
        for pb in arm.pose.bones:
            pb.rotation_quaternion = est.pose.q[pb.name]
            pb.location = est.pose.loc[pb.name] * r6.ESTUDIO
            pb.keyframe_insert("rotation_quaternion", frame=f)
            pb.keyframe_insert("location", frame=f)
    ruta = os.path.join(SALIDA, "cinematica_forja_r6_solo_huesos.fbx")
    ex.exportar(arm, mallas, None, ruta)
    return ruta


def verificar_fbx(ruta):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y", automatic_bone_orientation=False)
    arm = next(o for o in bpy.data.objects if o.type == "ARMATURE")
    assert {b.name for b in arm.data.bones} == set(r6.ARTICULACIONES)
    for b in arm.data.bones:
        assert (b.parent.name if b.parent else None) == r6.PADRE[b.name], b.name
    ini, fin = (int(round(x)) for x in arm.animation_data.action.frame_range)
    assert fin - ini == lt.DURACION - 1, (ini, fin)
    scn = bpy.context.scene
    peor = 0.0
    for f in (0, 40, 51, 76, 150, 232, 306, 380, 435):
        scn.frame_set(f + ini)
        bpy.context.view_layer.update()
        est = ci.evaluar(f)
        for pb in arm.pose.bones:
            real = (arm.matrix_world @ pb.head) / r6.ESTUDIO
            peor = max(peor, (real - est.pose.mundo(pb.name)[0]).length)
    print(f"[ok] FBX: 7 huesos R6, {fin - ini + 1} fotogramas, desviación máxima {peor:.4f} studs")
    assert peor < 0.02


def exportar_utileria():
    """Mallas nuevas de la cinemática para importar en Studio: compuerta del horno, tenazas, martillo y la pieza en sus
    6 etapas (de lingote a hoja). Cada malla conserva su origen de Blender (agarre, punta de las tenazas...), que es
    el punto al que se refieren los CFrame del muestreo; en Studio hay que poner ese punto como pivote (PivotOffset)
    con los valores de «pivote» de la tabla que devuelve esta función.
    Se exportan SIN el giro de importación de modelos/forja: así los ejes locales quedan como los de una pieza de
    personaje en Roblox (delante -Z, arriba +Y), que es como se escriben los CFrame de estas mallas."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obs = {"Compuerta": es.compuerta_horno(), "Tenazas": es.tenazas(), "Martillo": es.martillo()}
    obs["Compuerta"].location = (0, 0, 0)
    obs["GuiasCompuerta"] = bpy.data.objects["GuiasCompuerta"]
    obs["GuiasCompuerta"].location = (0, 0, 0)
    pieza, *_ = es.pieza()
    claves = pieza.data.shape_keys.key_blocks
    for i in range(len(es.ETAPAS)):
        me = bpy.data.meshes.new(f"Pieza_Etapa{i}")
        co = [v.co.copy() for v in (claves[i].data if i else claves[0].data)]
        me.from_pydata(co, [], [list(p.vertices) for p in pieza.data.polygons])
        for p in me.polygons:
            p.use_smooth = True
        o = bpy.data.objects.new(f"Pieza_Etapa{i}", me)
        bpy.context.scene.collection.objects.link(o)
        o.data.materials.append(pieza.data.materials[0])
        obs[o.name] = o
    bpy.data.objects.remove(pieza)
    pivotes = {}
    for nombre, o in obs.items():
        vs = [Vector(v.co) for v in o.data.vertices]
        mn = Vector([min(v[i] for v in vs) for i in range(3)])
        mx = Vector([max(v[i] for v in vs) for i in range(3)])
        c = (mn + mx) / 2
        # PivotOffset en Roblox = origen de Blender respecto al centro de la caja, en ejes locales de Roblox
        p = Q @ (-c)
        pivotes[nombre] = {"PivotOffset": [r(p.x), r(p.y), r(p.z)], "tamano": [r(x) for x in (Q @ (mx - mn))]}
        pivotes[nombre]["tamano"] = [abs(x) for x in pivotes[nombre]["tamano"]]
    bpy.ops.object.select_all(action="DESELECT")
    for o in obs.values():
        o.select_set(True)
    ruta = os.path.join(SALIDA, "cinematica_forja_utileria.fbx")
    bpy.ops.export_scene.fbx(filepath=ruta, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=True, axis_forward="-Z",
                             axis_up="Y", mesh_smooth_type="FACE", bake_anim=False)
    print("[ok] utilería:", ruta)
    return pivotes


def exportar_yunque_sin_martillo():
    """forja_yunque.fbx sin el martillo grande apoyado en su cara (ver escena.islas_martillo_yunque): para la estación
    de forja, donde la pieza se apoya en esa cara y el jugador usa su propio martillo. Mismo sistema, escala, UV y
    texturas que el original de modelos/forja (se reexporta con los mismos ajustes de ejes)."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    original = os.path.join(es.FORJA, "forja_yunque.fbx")
    bpy.ops.import_scene.fbx(filepath=original)
    o = bpy.data.objects["forja_yunque"]
    quitar = es.islas_martillo_yunque(o.data)
    antes = len(o.data.vertices)
    es.quitar_vertices(o, quitar)
    o.name = o.data.name = "forja_yunque_sin_martillo"
    bpy.ops.object.select_all(action="DESELECT")
    o.select_set(True)
    ruta = os.path.join(SALIDA, "forja_yunque_sin_martillo.fbx")
    bpy.ops.export_scene.fbx(filepath=ruta, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
                             apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=True, axis_forward="-Z",
                             axis_up="Y", mesh_smooth_type="FACE", path_mode="COPY", embed_textures=True,
                             bake_anim=False)
    # Comprobación: reimportado, lo que queda está donde estaba en el original
    quedan = sorted((round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3)) for v in o.data.vertices)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta)
    n = next(x for x in bpy.data.objects if x.type == "MESH")
    nuevos = sorted((round(v.co.x, 3), round(v.co.y, 3), round(v.co.z, 3)) for v in n.data.vertices)
    assert len(nuevos) == len(quedan) and max(abs(a - b) for p, q in zip(nuevos, quedan) for a, b in zip(p, q)) < 0.002
    print(f"[ok] {ruta}: {antes} -> {len(nuevos)} vértices (sin el martillo), {len(n.data.polygons)} caras, "
          f"tamaño {tuple(round(x, 3) for x in n.dimensions)}")


def main():
    exportar_yunque_sin_martillo()
    pivotes = exportar_utileria()
    d = escribir_datos(pivotes)
    ruta = exportar_fbx()
    verificar_fbx(ruta)


if __name__ == "__main__":
    main()
