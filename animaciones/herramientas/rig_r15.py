"""
Rig R15 de Roblox para Blender.

Crea un armature con los 15 huesos de R15 con sus nombres exactos (el importador de animaciones de
Roblox empareja por nombre) y, para poder ver la animación, un cuerpo de cajas con el aspecto
de un R15 clásico, cada caja pegada al 100 % a su hueso.

Decisiones importantes:
  * Todos los huesos tienen la orientación del mundo (rotación en reposo = identidad). Así una rotación
    de un hueso equivale a la rotación del Motor6D.Transform de Roblox sobre su pieza, que en el rig por
    defecto también está alineada con los ejes.
  * Las medidas se escriben en "studs" y se convierten a metros con ESTUDIO (1 stud = 0,28 m).
  * El personaje mira hacia -Y de Blender (la vista "frontal" de Blender lo ve de cara).
"""

import bpy
from mathutils import Vector

ESTUDIO = 0.28  # metros por stud

# Posición de cada articulación en studs (x, y, z), con Z hacia arriba.
# "Izquierda" es la izquierda DEL PERSONAJE, que mira a -Y: por eso queda en +X.
ARTICULACIONES = {
    "HumanoidRootPart": (0.0, 0.0, 3.0),
    "LowerTorso": (0.0, 0.0, 2.75),
    "UpperTorso": (0.0, 0.0, 3.15),
    "Head": (0.0, 0.0, 4.75),
    "LeftUpperArm": (1.5, 0.0, 4.45),
    "LeftLowerArm": (1.5, 0.0, 3.25),
    "LeftHand": (1.5, 0.0, 2.15),
    "RightUpperArm": (-1.5, 0.0, 4.45),
    "RightLowerArm": (-1.5, 0.0, 3.25),
    "RightHand": (-1.5, 0.0, 2.15),
    "LeftUpperLeg": (0.5, 0.0, 2.75),
    "LeftLowerLeg": (0.5, 0.0, 1.55),
    "LeftFoot": (0.5, 0.0, 0.35),
    "RightUpperLeg": (-0.5, 0.0, 2.75),
    "RightLowerLeg": (-0.5, 0.0, 1.55),
    "RightFoot": (-0.5, 0.0, 0.35),
}

# Jerarquía de R15 (hueso -> padre). Ojo: las piernas cuelgan de LowerTorso, no de UpperTorso.
PADRE = {
    "HumanoidRootPart": None,
    "LowerTorso": "HumanoidRootPart",
    "UpperTorso": "LowerTorso",
    "Head": "UpperTorso",
    "LeftUpperArm": "UpperTorso",
    "LeftLowerArm": "LeftUpperArm",
    "LeftHand": "LeftLowerArm",
    "RightUpperArm": "UpperTorso",
    "RightLowerArm": "RightUpperArm",
    "RightHand": "RightLowerArm",
    "LeftUpperLeg": "LowerTorso",
    "LeftLowerLeg": "LeftUpperLeg",
    "LeftFoot": "LeftLowerLeg",
    "RightUpperLeg": "LowerTorso",
    "RightLowerLeg": "RightUpperLeg",
    "RightFoot": "RightLowerLeg",
}

# Longitudes de los segmentos (studs), usadas por la cinemática inversa.
LARGO_BRAZO_SUP = 1.2
LARGO_BRAZO_INF = 1.1
LARGO_PIERNA_SUP = 1.2
LARGO_PIERNA_INF = 1.2
ALTURA_TOBILLO = 0.35

# Cajas del cuerpo: (nombre, hueso, centro en studs, tamaño en studs (x, y, z), color RGB)
PIEL = (0.95, 0.74, 0.55)
NARANJA = (0.95, 0.45, 0.10)
AZUL = (0.12, 0.25, 0.60)
ROJO = (0.80, 0.10, 0.10)
GRIS = (0.18, 0.18, 0.20)
CAJAS = [
    ("LowerTorso", "LowerTorso", (0.0, 0.0, 2.95), (2.0, 1.0, 0.4), AZUL),
    ("UpperTorso", "UpperTorso", (0.0, 0.0, 3.95), (2.0, 1.0, 1.6), NARANJA),
    ("Head", "Head", (0.0, 0.0, 5.35), (1.2, 1.2, 1.2), PIEL),
    ("Cinta", "Head", (0.0, -0.02, 5.55), (1.26, 1.26, 0.25), ROJO),
    ("Cara", "Head", (0.0, -0.64, 5.30), (0.8, 0.1, 0.25), GRIS),
    ("LeftUpperArm", "LeftUpperArm", (1.5, 0.0, 3.85), (1.0, 1.0, 1.2), NARANJA),
    ("LeftLowerArm", "LeftLowerArm", (1.5, 0.0, 2.70), (1.0, 1.0, 1.1), PIEL),
    ("LeftHand", "LeftHand", (1.5, 0.0, 1.85), (0.9, 0.9, 0.6), PIEL),
    ("RightUpperArm", "RightUpperArm", (-1.5, 0.0, 3.85), (1.0, 1.0, 1.2), NARANJA),
    ("RightLowerArm", "RightLowerArm", (-1.5, 0.0, 2.70), (1.0, 1.0, 1.1), PIEL),
    ("RightHand", "RightHand", (-1.5, 0.0, 1.85), (0.9, 0.9, 0.6), ROJO),
    ("LeftUpperLeg", "LeftUpperLeg", (0.5, 0.0, 2.15), (1.0, 1.0, 1.2), AZUL),
    ("LeftLowerLeg", "LeftLowerLeg", (0.5, 0.0, 0.95), (1.0, 1.0, 1.2), AZUL),
    ("LeftFoot", "LeftFoot", (0.5, -0.15, 0.175), (1.0, 1.3, 0.35), GRIS),
    ("RightUpperLeg", "RightUpperLeg", (-0.5, 0.0, 2.15), (1.0, 1.0, 1.2), AZUL),
    ("RightLowerLeg", "RightLowerLeg", (-0.5, 0.0, 0.95), (1.0, 1.0, 1.2), AZUL),
    ("RightFoot", "RightFoot", (-0.5, -0.15, 0.175), (1.0, 1.3, 0.35), GRIS),
]

LARGO_HUESO = 0.35 * ESTUDIO  # solo para que el hueso se vea; la orientación importa, no la longitud


def _metros(v):
    return Vector(v) * ESTUDIO


def construir_rig():
    """Crea el armature y el cuerpo de cajas. Devuelve (armature, [mallas])."""
    arm_data = bpy.data.armatures.new("RigR15")
    arm = bpy.data.objects.new("RigR15", arm_data)
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
