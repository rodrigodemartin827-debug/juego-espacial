"""
Rig R6 de Roblox para Blender.

Crea un armature con los 7 huesos de R6 con sus nombres exactos (el importador de animaciones de Roblox
empareja por nombre): HumanoidRootPart, Torso, Head, "Right Arm", "Left Arm", "Right Leg" y "Left Leg".
Para poder ver la animación añade un cuerpo de cajas con las medidas de un R6 clásico, pegado al 100 % a
sus huesos.

Decisiones importantes:
  * R6 no tiene codos, rodillas ni manos: cada brazo y cada pierna es UNA pieza rígida. El brazo mide 2 studs
    y gira desde el hombro, que está 0,5 por debajo de su extremo superior; la pierna gira desde su borde
    exterior superior.
  * Los huesos están colocados en el pivote de cada Motor6D de Roblox (cuello, hombros, caderas y RootJoint).
    Roblox solo aplica a cada Motor6D la rotación y el desplazamiento del hueso respecto a su reposo, así que
    el pivote tiene que coincidir con el de Roblox para que el movimiento sea idéntico.
  * Todos los huesos tienen la orientación del mundo (rotación en reposo = identidad). Así una rotación de un
    hueso equivale a la rotación de Motor6D.Transform sobre su pieza.
  * Las medidas se escriben en "studs" y se convierten a metros con ESTUDIO (1 stud = 0,28 m).
  * El personaje mira hacia -Y de Blender (la vista "frontal" de Blender lo ve de cara): su derecha es -X.
"""

import bpy
from mathutils import Vector

ESTUDIO = 0.28  # metros por stud

# Pivote de cada articulación en studs (x, y, z), con Z hacia arriba. La IZQUIERDA del personaje queda en +X.
ARTICULACIONES = {
    "HumanoidRootPart": (0.0, 0.0, 3.0),
    "Torso": (0.0, 0.0, 3.0),  # RootJoint: en el centro del torso
    "Head": (0.0, 0.0, 4.0),  # Neck: arriba del torso
    "Left Arm": (1.0, 0.0, 3.5),  # Left Shoulder: borde del torso, 0,5 por debajo de su cara superior
    "Right Arm": (-1.0, 0.0, 3.5),
    "Left Leg": (1.0, 0.0, 2.0),  # Left Hip: borde inferior del torso (la pierna cuelga hacia dentro)
    "Right Leg": (-1.0, 0.0, 2.0),
}

# Jerarquía de R6 (hueso -> padre). A diferencia de R15, las piernas cuelgan del Torso.
PADRE = {
    "HumanoidRootPart": None,
    "Torso": "HumanoidRootPart",
    "Head": "Torso",
    "Left Arm": "Torso",
    "Right Arm": "Torso",
    "Left Leg": "Torso",
    "Right Leg": "Torso",
}

# Longitudes (studs) desde el pivote hasta la punta de la pieza (el puño, el pie): las usa la animación.
LARGO_BRAZO = 1.5  # el brazo mide 2, pero el hombro está 0,5 por debajo de su extremo superior
LARGO_PIERNA = 2.0

# Cajas del cuerpo: (nombre, hueso, centro en studs, tamaño en studs (x, y, z), color RGB)
PIEL = (0.95, 0.74, 0.55)
NARANJA = (0.95, 0.45, 0.10)
AZUL = (0.12, 0.25, 0.60)
ROJO = (0.80, 0.10, 0.10)
GRIS = (0.18, 0.18, 0.20)
CAJAS = [
    ("Torso", "Torso", (0.0, 0.0, 3.0), (2.0, 1.0, 2.0), NARANJA),
    ("Cinturon", "Torso", (0.0, 0.0, 2.2), (2.04, 1.04, 0.4), AZUL),
    ("Hebilla", "Torso", (0.0, -0.52, 2.2), (0.5, 0.06, 0.3), GRIS),
    ("Head", "Head", (0.0, 0.0, 4.6), (1.2, 1.2, 1.2), PIEL),
    ("Cinta", "Head", (0.0, 0.0, 4.95), (1.26, 1.26, 0.25), ROJO),
    ("Cara", "Head", (0.0, -0.62, 4.55), (0.8, 0.08, 0.25), GRIS),
    ("Left Arm", "Left Arm", (1.5, 0.0, 3.0), (1.0, 1.0, 2.0), NARANJA),
    ("Guante izq", "Left Arm", (1.5, 0.0, 2.2), (1.04, 1.04, 0.7), PIEL),
    ("Right Arm", "Right Arm", (-1.5, 0.0, 3.0), (1.0, 1.0, 2.0), NARANJA),
    ("Guante der", "Right Arm", (-1.5, 0.0, 2.2), (1.04, 1.04, 0.7), ROJO),
    ("Left Leg", "Left Leg", (0.5, 0.0, 1.0), (1.0, 1.0, 2.0), AZUL),
    ("Bota izq", "Left Leg", (0.5, -0.1, 0.25), (1.04, 1.24, 0.5), GRIS),
    ("Right Leg", "Right Leg", (-0.5, 0.0, 1.0), (1.0, 1.0, 2.0), AZUL),
    ("Bota der", "Right Leg", (-0.5, -0.1, 0.25), (1.04, 1.24, 0.5), GRIS),
]

LARGO_HUESO = 0.35 * ESTUDIO  # solo para que el hueso se vea; la orientación importa, no la longitud


def _metros(v):
    return Vector(v) * ESTUDIO


def construir_rig():
    """Crea el armature y el cuerpo de cajas. Devuelve (armature, [mallas])."""
    arm_data = bpy.data.armatures.new("RigR6")
    arm = bpy.data.objects.new("RigR6", arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)

    bpy.ops.object.mode_set(mode="EDIT")
    huesos = {}
    for nombre, pos in ARTICULACIONES.items():
        eb = arm_data.edit_bones.new(nombre)
        cabeza = _metros(pos)
        eb.head = cabeza
        eb.tail = cabeza + Vector((0.0, LARGO_HUESO, 0.0))  # apunta a +Y => orientación del mundo
        eb.roll = 0.0
        huesos[nombre] = eb
    for nombre, padre in PADRE.items():
        if padre:
            huesos[nombre].parent = huesos[padre]
    bpy.ops.object.mode_set(mode="OBJECT")

    # Todos los huesos en modo cuaternión, sin ninguna rotación en reposo.
    for pb in arm.pose.bones:
        pb.rotation_mode = "QUATERNION"

    mallas = []
    for nombre, hueso, centro, tam, color in CAJAS:
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=_metros(centro))
        obj = bpy.context.active_object
        obj.name = nombre
        obj.scale = (tam[0] * ESTUDIO, tam[1] * ESTUDIO, tam[2] * ESTUDIO)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        mat = bpy.data.materials.new(f"mat_{nombre}")
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*color, 1.0)
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
        mat.diffuse_color = (*color, 1.0)
        obj.data.materials.append(mat)
        grupo = obj.vertex_groups.new(name=hueso)
        grupo.add([v.index for v in obj.data.vertices], 1.0, "REPLACE")
        mod = obj.modifiers.new("Armature", "ARMATURE")
        mod.object = arm
        obj.parent = arm
        mallas.append(obj)
    return arm, mallas
