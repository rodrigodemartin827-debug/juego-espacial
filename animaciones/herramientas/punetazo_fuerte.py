"""
Animación "puñetazo fuerte estilo anime" para el rig R15.

Se describe con claves (fotograma, valor, easing) por canal. Cada canal se muestrea en Python con su
propia curva de easing (nada lineal) y se hornea fotograma a fotograma en el armature de Blender.
El puño y los dos pies se resuelven con cinemática inversa de dos huesos para que los pies no patinen
y el puño llegue exactamente al punto de impacto; el resto va en cinemática directa.

Fases (30 fps):
    0        guardia
    0-10     anticipación: cadera y torso giran hacia atrás, el puño se carga detrás del cuerpo
    10-12    tensión (casi quieto, con un pequeño temblor)
    12-16    golpe: primero cadera (12-14), luego torso (13-15), por último el puño (13-16)
    16-22    impacto exagerado y mantenido ("hit stop")
    22-40    recuperación hasta la guardia
"""

import math

from mathutils import Euler, Quaternion, Vector

import rig_r15 as r15

FPS = 30
ULTIMO_FOTOGRAMA = 40

# ---------------------------------------------------------------------------------------------
# Curvas de easing. Todas llevan t de 0 a 1 y devuelven el avance de 0 a 1 (pueden pasarse de 1).
# ---------------------------------------------------------------------------------------------


def _suave(t):  # entra y sale despacio (smootherstep)
    return t * t * t * (t * (6 * t - 15) + 10)


def _entra(t):  # arranca despacio, termina rápido
    return t**3


def _sale(t):  # arranca rápido, frena suave
    return 1 - (1 - t) ** 3


def _golpe(t):  # explosivo: casi toda la distancia en el primer tramo y frena en seco
    return 1 - (1 - t) ** 5


def _rebote(t):  # se pasa de largo (~12 %) y vuelve: el "latigazo" del golpe
    c1 = 2.6
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


EASING = {"suave": _suave, "entra": _entra, "sale": _sale, "golpe": _golpe, "rebote": _rebote}


def muestrear(claves, fotograma):
    """claves: [(fotograma, valor, easing)]; el easing de cada clave es el del tramo que LLEGA a ella."""
    if fotograma <= claves[0][0]:
        return claves[0][1]
    for (f0, v0, _), (f1, v1, ease) in zip(claves, claves[1:]):
        if f0 <= fotograma <= f1:
            t = (fotograma - f0) / (f1 - f0)
            k = EASING[ease](t)
            return tuple(a + (b - a) * k for a, b in zip(v0, v1))
    return claves[-1][1]


# ---------------------------------------------------------------------------------------------
# Datos de la animación. Ángulos en grados sobre los ejes del mundo (X derecha, Y profundidad, Z arriba).
# En el eje Z, un ángulo positivo adelanta el lado DERECHO del personaje (el que golpea).
# ---------------------------------------------------------------------------------------------

# Cadera (LowerTorso): traslación en studs y rotación.
CADERA_POS = [
    (0, (0.0, 0.0, -0.45), "suave"),
    (10, (0.3, 0.65, -0.9), "suave"),
    (12, (0.3, 0.7, -0.93), "suave"),
    (14, (-0.1, -0.9, -0.7), "golpe"),
    (16, (-0.1, -1.3, -0.78), "sale"),
    (22, (-0.1, -1.45, -0.85), "suave"),
    (32, (0.0, -0.3, -0.52), "suave"),
    (40, (0.0, 0.0, -0.45), "suave"),
]
CADERA_ROT = [
    (0, (0, 0, -12), "suave"),
    (10, (-8, -8, -46), "suave"),
    (12, (-8, -8, -48), "suave"),
    (14, (10, 6, 46), "rebote"),
    (16, (12, 6, 50), "sale"),
    (22, (12, 5, 48), "suave"),
    (32, (3, 1, 10), "suave"),
    (40, (0, 0, -12), "suave"),
]
# El torso llega un fotograma tarde respecto a la cadera.
TORSO_ROT = [
    (0, (2, 0, -6), "suave"),
    (10, (-18, -6, -26), "suave"),
    (12, (-20, -6, -30), "suave"),
    (15, (24, 8, 34), "rebote"),
    (17, (28, 8, 40), "sale"),
    (22, (28, 8, 38), "suave"),
    (33, (6, 2, 4), "suave"),
    (40, (2, 0, -6), "suave"),
]
# La cabeza compensa el giro del cuerpo para seguir mirando al objetivo.
CABEZA_ROT = [
    (0, (0, 0, 14), "suave"),
    (10, (14, 0, 52), "suave"),
    (12, (14, 0, 54), "suave"),
    (15, (-30, 0, -68), "rebote"),
    (22, (-28, 0, -66), "suave"),
    (33, (-4, 0, -10), "suave"),
    (40, (0, 0, 14), "suave"),
]
# Brazo izquierdo (guardia): se estira hacia delante al cargar y se recoge de golpe para dar contrapeso.
BRAZO_I_SUP = [
    (0, (-40, 0, -10), "suave"),
    (10, (-75, 0, -8), "suave"),
    (12, (-75, 0, -8), "suave"),
    (15, (20, 0, -20), "golpe"),
    (22, (28, 0, -24), "suave"),
    (40, (-40, 0, -10), "suave"),
]
BRAZO_I_INF = [
    (0, (-95, 0, 0), "suave"),
    (10, (-35, 0, 0), "suave"),
    (12, (-35, 0, 0), "suave"),
    (15, (-115, 0, 0), "golpe"),
    (22, (-120, 0, 0), "suave"),
    (40, (-95, 0, 0), "suave"),
]
# Puño derecho (posición de la muñeca en el mundo, en studs) y hacia dónde apunta el codo.
PUNO_POS = [
    (0, (-0.9, -0.8, 4.3), "suave"),
    (10, (-1.6, 1.0, 3.9), "suave"),
    (13, (-1.65, 1.1, 3.8), "suave"),
    (16, (-0.5, -4.6, 4.0), "golpe"),
    (22, (-0.5, -4.7, 4.0), "sale"),
    (30, (-1.0, -1.6, 4.2), "suave"),
    (40, (-0.9, -0.8, 4.3), "suave"),
]
PUNO_CODO = [
    (0, (-0.3, 0.4, -1.0), "suave"),
    (10, (-0.2, 1.0, -0.3), "suave"),
    (13, (-0.2, 1.0, -0.3), "suave"),
    (16, (-0.4, 0.1, -1.0), "golpe"),
    (40, (-0.3, 0.4, -1.0), "suave"),
]
# Pies (posición del tobillo en studs, guiñada y cabeceo en grados).
PIE_I = [(0, (0.9, -1.0, 0.35, 12, 0), "suave"), (40, (0.9, -1.0, 0.35, 12, 0), "suave")]
PIE_D = [
    (0, (-0.9, 0.7, 0.35, -35, 0), "suave"),
    (12, (-0.9, 0.7, 0.35, -35, 0), "suave"),
    (13, (-0.85, 0.3, 0.7, -26, 35), "golpe"),
    (14, (-0.85, 0.25, 0.75, -24, 40), "sale"),
    (16, (-0.8, 0.1, 0.85, -20, 50), "sale"),
    (22, (-0.8, 0.1, 0.85, -20, 50), "suave"),
    (31, (-0.9, 0.7, 0.35, -35, 0), "suave"),
    (40, (-0.9, 0.7, 0.35, -35, 0), "suave"),
]

# Fotogramas que se enseñan en la hoja de contactos: (fotograma, nombre).
FOTOGRAMAS_CLAVE = [
    (0, "Guardia"),
    (6, "Anticipación"),
    (10, "Máx. anticipación"),
    (13, "Cadera lidera"),
    (14, "Torso sigue"),
    (16, "IMPACTO"),
    (19, "Impacto mantenido"),
    (24, "Recuperación"),
    (32, "Recuperación"),
    (40, "Guardia"),
]

# ---------------------------------------------------------------------------------------------
# Cinemática directa propia (los huesos tienen rotación en reposo = identidad, así que es muy simple).
# ---------------------------------------------------------------------------------------------


class Pose:
    def __init__(self):
        self.q = {b: Quaternion() for b in r15.ARTICULACIONES}
        self.loc = {b: Vector((0, 0, 0)) for b in r15.ARTICULACIONES}

    def mundo(self, hueso):
        """(posición de la articulación en studs, rotación en el mundo)."""
        padre = r15.PADRE[hueso]
        if padre is None:
            return Vector(r15.ARTICULACIONES[hueso]) + self.loc[hueso], self.q[hueso].copy()
        pp, pr = self.mundo(padre)
        desfase = Vector(r15.ARTICULACIONES[hueso]) - Vector(r15.ARTICULACIONES[padre])
        return pp + pr @ (desfase + self.loc[hueso]), pr @ self.q[hueso]

    def poner_rot_mundo(self, hueso, q_mundo):
        padre = r15.PADRE[hueso]
        q_padre = self.mundo(padre)[1] if padre else Quaternion()
        self.q[hueso] = q_padre.inverted() @ q_mundo


def _euler(grados):
    return Euler([math.radians(g) for g in grados], "XYZ").to_quaternion()


def _ik_dos_huesos(origen, objetivo, largo_a, largo_b, polo):
    """Devuelve las direcciones (hueso superior, hueso inferior); la articulación media se dobla hacia `polo`."""
    d = objetivo - origen
    dist = min(max(d.length, abs(largo_a - largo_b) + 1e-4), largo_a + largo_b - 1e-4)
    dn = d.normalized()
    perp = polo - dn * polo.dot(dn)
    perp = perp.normalized() if perp.length > 1e-6 else Vector((0, -1, 0))
    cos_a = (largo_a * largo_a + dist * dist - largo_b * largo_b) / (2 * largo_a * dist)
    a = math.acos(max(-1.0, min(1.0, cos_a)))
    dir_sup = dn * math.cos(a) + perp * math.sin(a)
    medio = origen + dir_sup * largo_a
    dir_inf = (origen + dn * dist - medio).normalized()
    return dir_sup, dir_inf


ABAJO = Vector((0, 0, -1))
ERRORES_PIE = {}  # fotograma -> (error pie izq., error pie der.) en studs, para comprobar que no patinan


def calcular_pose(fotograma):
    p = Pose()
    p.loc["LowerTorso"] = Vector(muestrear(CADERA_POS, fotograma))
    p.q["LowerTorso"] = _euler(muestrear(CADERA_ROT, fotograma))
    p.q["UpperTorso"] = _euler(muestrear(TORSO_ROT, fotograma))
    p.q["Head"] = _euler(muestrear(CABEZA_ROT, fotograma))
    p.q["LeftUpperArm"] = _euler(muestrear(BRAZO_I_SUP, fotograma))
    p.q["LeftLowerArm"] = _euler(muestrear(BRAZO_I_INF, fotograma))

    # Piernas con IK: los pies se quedan donde dicen las claves, sin patinar.
    errores = []
    for lado, claves in (("Left", PIE_I), ("Right", PIE_D)):
        x, y, z, guinada, cabeceo = muestrear(claves, fotograma)
        objetivo = Vector((x, y, z))
        yaw = math.radians(guinada)
        polo = Vector((math.sin(yaw), -math.cos(yaw), 0.0))
        cadera = p.mundo(f"{lado}UpperLeg")[0]
        dir_sup, dir_inf = _ik_dos_huesos(cadera, objetivo, r15.LARGO_PIERNA_SUP, r15.LARGO_PIERNA_INF, polo)
        p.poner_rot_mundo(f"{lado}UpperLeg", ABAJO.rotation_difference(dir_sup))
        p.poner_rot_mundo(f"{lado}LowerLeg", ABAJO.rotation_difference(dir_inf))
        p.poner_rot_mundo(
            f"{lado}Foot", Quaternion((0, 0, 1), yaw) @ Quaternion((1, 0, 0), math.radians(cabeceo))
        )
        errores.append((p.mundo(f"{lado}Foot")[0] - objetivo).length)
    ERRORES_PIE[fotograma] = tuple(errores)

    # Brazo derecho con IK hacia el puño.
    objetivo = Vector(muestrear(PUNO_POS, fotograma))
    polo = Vector(muestrear(PUNO_CODO, fotograma))
    hombro = p.mundo("RightUpperArm")[0]
    dir_sup, dir_inf = _ik_dos_huesos(hombro, objetivo, r15.LARGO_BRAZO_SUP, r15.LARGO_BRAZO_INF, polo)
    p.poner_rot_mundo("RightUpperArm", ABAJO.rotation_difference(dir_sup))
    q_antebrazo = ABAJO.rotation_difference(dir_inf)
    p.poner_rot_mundo("RightLowerArm", q_antebrazo)
    p.poner_rot_mundo("RightHand", q_antebrazo)  # la mano sigue la línea del antebrazo
    return p


# ---------------------------------------------------------------------------------------------
# Horneado en Blender
# ---------------------------------------------------------------------------------------------


def hornear(armature):
    """Crea la acción con un fotograma clave por cada fotograma, en todos los huesos."""
    import bpy

    scn = bpy.context.scene
    scn.render.fps = FPS
    scn.frame_start = 0
    scn.frame_end = ULTIMO_FOTOGRAMA
    armature.animation_data_create()
    accion = bpy.data.actions.new("PunetazoFuerteAnime")
    armature.animation_data.action = accion

    anterior = {}
    for f in range(ULTIMO_FOTOGRAMA + 1):
        pose = calcular_pose(f)
        for pb in armature.pose.bones:
            q = pose.q[pb.name].copy()
            if pb.name in anterior and anterior[pb.name].dot(q) < 0:
                q.negate()  # evita saltos de signo del cuaternión entre fotogramas
            anterior[pb.name] = q
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if pb.name == "LowerTorso":
                pb.location = pose.loc[pb.name] * r15.ESTUDIO
                pb.keyframe_insert("location", frame=f)
    return accion
