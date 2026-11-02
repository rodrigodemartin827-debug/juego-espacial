"""
Andar de los monstruos en Blender: hojas de contactos y FBX a partir de los datos del JUEGO.

La fuente de verdad son los datos de Luau (src/shared/Personajes/Datos/AnimacionesMonstruo.luau). Este script no
inventa nada: lee el JSON que saca exportar_monstruo.luau (las poses horneadas tal cual las reproduce el cliente) y
las pone en el rig R6 de rig_r6.py. Así la hoja de contactos enseña lo que se verá en Roblox, y el FBX sirve para
subir la animación como asset si se quiere (ver animaciones/README.md).

Uso (desde la raíz del repo, con bpy y pillow instalados):
    lune run animaciones/herramientas/exportar_monstruo.luau /tmp/monstruo.json
    python animaciones/herramientas/andar_monstruo.py --json /tmp/monstruo.json \
        --hojas animaciones/andar_monstruo/hoja --gifs animaciones/andar_monstruo/bucle \
        --fbx-dir animaciones/andar_monstruo

Conversión de ejes. Roblox (personaje): X derecha, Y arriba, Z atrás. Blender (rig_r6): el personaje mira a -Y y su
derecha es -X, Z arriba. Así que un vector de Roblox (x, y, z) es (-x, z, y) en Blender, y una rotación R pasa a
S·R·Sᵀ con S esa misma matriz. Como los huesos de rig_r6 están en el pivote de cada Motor6D y orientados con el
mundo, la rotación de cada pieza respecto a su padre ES la rotación del hueso.
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import rig_r6 as r6  # noqa: E402
from hoja_contactos import _fuente  # noqa: E402

E = r6.ESTUDIO
S = Matrix(((-1, 0, 0), (0, 0, 1), (0, 1, 0)))

# Aspecto del monstruo para las hojas (solo visual: en el juego es el avatar del jugador).
PIEL = (0.62, 0.66, 0.56)
OSCURO = (0.07, 0.07, 0.09)
TORSO = (0.16, 0.17, 0.2)
GARRA = (0.1, 0.1, 0.1)
OJO = (0.9, 0.05, 0.05)
CAJAS_MONSTRUO = [
    ("Torso", "Torso", (0.0, 0.0, 3.0), (2.0, 1.0, 2.0), TORSO),
    ("Costilla1", "Torso", (0.0, -0.52, 3.45), (1.3, 0.06, 0.12), PIEL),
    ("Costilla2", "Torso", (0.0, -0.52, 3.1), (1.4, 0.06, 0.12), PIEL),
    ("Costilla3", "Torso", (0.0, -0.52, 2.75), (1.2, 0.06, 0.12), PIEL),
    ("Head", "Head", (0.0, 0.0, 4.6), (1.2, 1.2, 1.2), PIEL),
    ("Ojo izq", "Head", (0.27, -0.61, 4.72), (0.22, 0.06, 0.14), OSCURO),
    ("Ojo der", "Head", (-0.27, -0.61, 4.72), (0.22, 0.06, 0.14), OSCURO),
    ("Pupila izq", "Head", (0.27, -0.645, 4.72), (0.07, 0.03, 0.07), OJO),
    ("Pupila der", "Head", (-0.27, -0.645, 4.72), (0.07, 0.03, 0.07), OJO),
    ("Boca", "Head", (0.0, -0.61, 4.32), (0.8, 0.06, 0.08), OSCURO),
    ("Left Arm", "Left Arm", (1.5, 0.0, 3.0), (1.0, 1.0, 2.0), PIEL),
    ("Garra izq", "Left Arm", (1.5, 0.0, 2.15), (1.04, 1.04, 0.32), GARRA),
    ("Right Arm", "Right Arm", (-1.5, 0.0, 3.0), (1.0, 1.0, 2.0), PIEL),
    ("Garra der", "Right Arm", (-1.5, 0.0, 2.15), (1.04, 1.04, 0.32), GARRA),
    ("Left Leg", "Left Leg", (0.5, 0.0, 1.0), (1.0, 1.0, 2.0), OSCURO),
    ("Right Leg", "Right Leg", (-0.5, 0.0, 1.0), (1.0, 1.0, 2.0), OSCURO),
]

# Fotogramas (en segundos) que salen en cada hoja, con su rótulo.
MOMENTOS = {
    "Reposo": [
        (0.0, "inicio"),
        (1.15, "se hunde"),
        (1.55, "tensión"),
        (1.6, "latigazo"),
        (1.9, "mantiene"),
        (2.07, "vuelve"),
        (3.63, "tic"),
        (3.7, "tic + brazo"),
    ],
    "Andar": [(i * 0.1, t) for i, t in enumerate(
        ["pisa der.", "apoyo der.", "medio", "arrastra izq.", "pisa izq.", "desplome", "tirón cabeza", "apoyo izq.", "llega der."]
    )],
    "Correr": [(round(i * 0.0667, 3), t) for i, t in enumerate(
        ["pisa der.", "aplasta", "apoyo der.", "despega", "aire", "pisa izq.", "espasmo", "despega", "aire"]
    )],
    "Saltar": [(0.0, "inicio"), (0.07, "se encoge"), (0.13, "impulso"), (0.2, "estira"), (0.3, "brazos atrás"), (0.45, "final")],
    "Caer": [(0.0, "inicio"), (0.2, ""), (0.5, "cabeza"), (0.57, "tirón"), (0.8, ""), (1.0, "")],
}

ANCHO, ALTO = 300, 380


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0


def construir_rig():
    r6.CAJAS[:] = CAJAS_MONSTRUO
    return r6.construir_rig()


def hornear(armature, anim):
    """Un fotograma clave por cuadro, en todos los huesos. Devuelve el último fotograma."""
    scn = bpy.context.scene
    fps = anim["Fps"]
    scn.render.fps = fps
    scn.frame_start = 0
    scn.frame_end = len(anim["Cuadros"]) - 1
    armature.animation_data_create()
    accion = bpy.data.actions.new(anim["Nombre"])
    armature.animation_data.action = accion

    anterior = {}
    for f, cuadro in enumerate(anim["Cuadros"]):
        for nombre, pieza in cuadro["Piezas"].items():
            r = pieza["R"]
            rot = Matrix(((r[0], r[1], r[2]), (r[3], r[4], r[5]), (r[6], r[7], r[8])))
            q = (S @ rot @ S.transposed()).to_quaternion()
            if nombre in anterior and anterior[nombre].dot(q) < 0:
                q.negate()  # sin saltos de signo entre fotogramas
            anterior[nombre] = q
            pb = armature.pose.bones[nombre]
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if nombre == "Torso":
                pb.location = (S @ Vector(pieza["T"])) * E
                pb.keyframe_insert("location", frame=f)
        hrp = armature.pose.bones["HumanoidRootPart"]
        hrp.keyframe_insert("rotation_quaternion", frame=f)
        hrp.keyframe_insert("location", frame=f)
    return len(anim["Cuadros"]) - 1


def mover_raiz(armature, anim, ultimo):
    """Para la hoja: el personaje avanza a VelocidadReferencia (así se ve si los pies patinan sobre el suelo).
    Los saltos se ven en el aire. Devuelve el punto medio del recorrido (para centrar las cámaras)."""
    v = anim.get("VelocidadReferencia") or 0
    altura = 1.6 if anim["Estado"] in ("Saltar", "Caer") else 0.0
    for f in range(ultimo + 1):
        t = f / anim["Fps"]
        armature.location = (0.0, -v * t * E, altura * E)
        armature.keyframe_insert("location", frame=f)
    return Vector((0.0, -v * anim["Duracion"] * E / 2, (altura + 2.4) * E))


def material(nombre, color, rugosidad=0.7):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = rugosidad
    return mat


def preparar_escena(centro):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 16
    scn.cycles.use_denoising = True
    scn.render.resolution_x, scn.render.resolution_y = ANCHO, ALTO

    # Suelo de cuadros de 1 stud: un pie que no patina se queda sobre la misma casilla.
    bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, 0))
    suelo = bpy.context.active_object
    mat = bpy.data.materials.new("suelo")
    mat.use_nodes = True
    nt = mat.node_tree
    chk = nt.nodes.new("ShaderNodeTexChecker")
    chk.inputs["Color1"].default_value = (0.42, 0.44, 0.5, 1)
    chk.inputs["Color2"].default_value = (0.3, 0.32, 0.37, 1)
    chk.inputs["Scale"].default_value = 40 / E / 2  # casillas de 1 stud
    nt.links.new(chk.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    suelo.data.materials.append(mat)

    scn.world = bpy.data.worlds.new("mundo")
    scn.world.use_nodes = True
    fondo = scn.world.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.32, 0.3, 0.38, 1)  # crepúsculo del planeta de los monstruos
    fondo.inputs["Strength"].default_value = 0.8
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy = 3.2
    sol.angle = math.radians(10)
    objsol = bpy.data.objects.new("sol", sol)
    objsol.rotation_euler = (math.radians(48), 0, math.radians(-38))
    scn.collection.objects.link(objsol)

    cam = bpy.data.cameras.new("cam")
    cam.lens = 50
    objcam = bpy.data.objects.new("cam", cam)
    scn.collection.objects.link(objcam)
    scn.camera = objcam
    mira = bpy.data.objects.new("mira", None)
    scn.collection.objects.link(mira)
    mira.location = centro
    c = objcam.constraints.new("TRACK_TO")
    c.target = mira
    c.track_axis = "TRACK_NEGATIVE_Z"
    c.up_axis = "UP_Y"
    return objcam


def vistas(centro, recorrido=0.0):
    d = 4.6 + 0.8 * recorrido  # se aleja si el personaje recorre mucho en un ciclo, para que no se salga
    return {
        "Frente": centro + Vector((0.0, -d, 0.15)),
        "Lateral": centro + Vector((-d, 0.0, 0.15)),  # desde el lado derecho del personaje
        "3/4": centro + Vector((-d * 0.72, -d * 0.72, 0.6)),
    }


def renderizar_hoja(anim, directorio, salida):
    escena_vacia()
    armature, _ = construir_rig()
    ultimo = hornear(armature, anim)
    centro = mover_raiz(armature, anim, ultimo)
    cam = preparar_escena(centro)
    scn = bpy.context.scene
    momentos = MOMENTOS[anim["Estado"]]
    os.makedirs(directorio, exist_ok=True)

    rutas = {}
    for nombre_vista, pos in vistas(centro, recorrido(anim)).items():
        cam.location = pos
        for t, _ in momentos:
            f = min(ultimo, round(t * anim["Fps"]))
            scn.frame_set(f)
            ruta = os.path.join(directorio, f"{anim['Estado']}_{nombre_vista.replace('/', '-')}_{f:03d}.png")
            scn.render.filepath = ruta
            bpy.ops.render.render(write_still=True)
            rutas[(nombre_vista, f)] = ruta

    cab_izq, cab_arriba, pie = 90, 54, 30
    hoja = Image.new(
        "RGB", (cab_izq + ANCHO * len(momentos), cab_arriba + ALTO * 3 + pie), (20, 20, 26)
    )
    d = ImageDraw.Draw(hoja)
    f_tit, f_peq = _fuente(17), _fuente(13)
    for i, (t, rotulo) in enumerate(momentos):
        f = min(ultimo, round(t * anim["Fps"]))
        x = cab_izq + i * ANCHO
        d.text((x + 8, 6), f"{f / anim['Fps']:.2f} s", fill=(255, 210, 90), font=f_tit)
        d.text((x + 8, 30), rotulo, fill=(220, 220, 230), font=f_peq)
        for j, nombre_vista in enumerate(("Frente", "Lateral", "3/4")):
            hoja.paste(Image.open(rutas[(nombre_vista, f)]).convert("RGB"), (x, cab_arriba + j * ALTO))
    for j, nombre_vista in enumerate(("Frente", "Lateral", "3/4")):
        d.text((10, cab_arriba + j * ALTO + ALTO // 2 - 10), nombre_vista, fill=(255, 255, 255), font=f_tit)
    texto = f"{anim['Nombre']}  ·  {anim['Duracion']:.2f} s  ·  {'bucle' if anim['Bucle'] else 'una vez'}"
    medidas = anim.get("Medidas")
    if medidas:
        texto += (
            f"  ·  avanza a {anim['VelocidadReferencia']} studs/s (pies: {medidas['VelocidadNatural']:.1f})"
            f"  ·  patinaje medio {medidas['Patinaje'] * 100:.0f} %  ·  en el aire {medidas['Aire'] * 100:.0f} %"
        )
    d.text((10, cab_arriba + ALTO * 3 + 6), texto, fill=(200, 200, 210), font=f_peq)
    hoja.save(salida)
    print("[ok] hoja:", salida)


def recorrido(anim):
    """Metros que avanza el personaje en un ciclo."""
    return (anim.get("VelocidadReferencia") or 0) * anim["Duracion"] * E


def renderizar_gif(anim, directorio, salida, fps_gif=15):
    """Animación en bucle desde la vista 3/4 (dos ciclos), para ver el ritmo y los tirones sin Studio."""
    escena_vacia()
    armature, _ = construir_rig()
    ultimo = hornear(armature, anim)
    centro = mover_raiz(armature, anim, ultimo)
    cam = preparar_escena(centro)
    scn = bpy.context.scene
    scn.render.resolution_x, scn.render.resolution_y = 260, 320
    cam.location = vistas(centro, recorrido(anim))["3/4"]
    os.makedirs(directorio, exist_ok=True)
    paso = max(1, round(anim["Fps"] / fps_gif))
    imagenes = []
    for f in range(0, ultimo, paso):
        scn.frame_set(f)
        ruta = os.path.join(directorio, f"gif_{anim['Estado']}_{f:03d}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        imagenes.append(Image.open(ruta).convert("RGB"))
    vueltas = 1 if anim["Duracion"] > 2 else 2
    secuencia = imagenes * vueltas
    secuencia[0].save(
        salida, save_all=True, append_images=secuencia[1:], duration=round(1000 * paso / anim["Fps"]), loop=0
    )
    print("[ok] gif:", salida)


def exportar_fbx(anim, ruta):
    """FBX solo con huesos y la animación en el sitio (sin avanzar), para importar en el Animation Editor."""
    import exportar_fbx

    escena_vacia()
    armature, mallas = construir_rig()
    hornear(armature, anim)
    exportar_fbx.exportar(armature, mallas, None, ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", required=True, help="salida de exportar_monstruo.luau")
    ap.add_argument("--hojas", help="prefijo de las hojas de contactos (se añade _<estado>.png)")
    ap.add_argument("--fbx-dir", help="carpeta para los FBX (uno por animación)")
    ap.add_argument("--gifs", help="prefijo de los GIF en bucle (se añade _<estado>.gif)")
    ap.add_argument("--solo", help="solo esta animación (Reposo, Andar, Correr, Saltar o Caer)")
    ap.add_argument("--render-dir", default="/tmp/renders_monstruo")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None)

    with open(a.json, encoding="utf-8") as archivo:
        animaciones = json.load(archivo)
    for anim in animaciones:
        if a.solo and anim["Estado"] != a.solo:
            continue
        if a.hojas:
            renderizar_hoja(anim, a.render_dir, f"{a.hojas}_{anim['Estado'].lower()}.png")
        if a.gifs:
            renderizar_gif(anim, a.render_dir, f"{a.gifs}_{anim['Estado'].lower()}.gif")
        if a.fbx_dir:
            os.makedirs(a.fbx_dir, exist_ok=True)
            exportar_fbx(anim, os.path.join(a.fbx_dir, f"{anim['Nombre'].lower()}_solo_huesos.fbx"))


main()
