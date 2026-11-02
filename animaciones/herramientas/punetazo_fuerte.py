"""
Animación "puñetazo fuerte estilo anime" para el rig R6.

R6 no tiene codos ni rodillas: brazos y piernas son piezas rígidas. Por eso la expresividad sale de:
  * el TORSO entero (giro, inclinación y desplazamiento), con la cabeza compensando para seguir mirando al blanco;
  * el brazo que golpea, que apunta en una dirección del mundo (así el puño sigue la trayectoria que se quiere);
  * las piernas, que van con cinemática inversa de "apuntar": cada pierna se orienta hacia donde está su pie y la
    altura del torso se calcula en cada fotograma para que los pies lleguen al suelo sin atravesarlo.

Cada canal se describe con claves (fotograma, valor, easing) y se muestrea en Python con su propia curva de
easing (nada lineal); después se hornea fotograma a fotograma en el armature de Blender.

Fases (30 fps):
    0        guardia
    0-10     anticipación: el torso se enrosca hacia atrás, el cuerpo se agacha, el puño se carga detrás
    10-12    tensión (casi quieto)
    12-16    golpe: el torso lidera y el puño llega después, dibujando un arco
    16-22    impacto exagerado y mantenido ("hit stop")
    22-40    recuperación hasta la guardia
"""

import math

from mathutils import Euler, Quaternion, Vector

import rig_r6 as r6

FPS = 30
ULTIMO_FOTOGRAMA = 40
IMPACTO = 16  # fotograma del impacto (0,53 s): coincide con Tiempos.Carga del Remate en Datos/Poderes

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
# Datos de la animación. Mundo de Blender: X = izquierda del personaje, Y = hacia atrás (el personaje y el golpe
# miran a -Y), Z = arriba. Ángulos en grados:
#   TORSO_ROT = (inclinación hacia delante, ladeo hacia su izquierda, giro; giro positivo = a la izquierda).
# ---------------------------------------------------------------------------------------------

# Torso: desplazamiento (x, y) en studs; la altura la calcula el suelo en cada fotograma.
TORSO_POS = [
    (0, (0.0, 0.0), "suave"),
    (10, (-0.2, 0.6), "suave"),
    (12, (-0.2, 0.65), "suave"),
    (14, (0.0, -0.45), "golpe"),
    (16, (0.05, -1.2), "sale"),
    (18, (0.05, -1.3), "suave"),  # rebote: el cuerpo sigue empujando un poco tras el impacto
    (22, (0.05, -1.4), "suave"),
    (32, (0.0, -0.4), "suave"),
    (40, (0.0, 0.0), "suave"),
]
TORSO_ROT = [
    (0, (6, 0, -18), "suave"),
    (10, (10, 5, -90), "suave"),
    (12, (11, 5, -94), "suave"),
    (14, (18, 0, 30), "golpe"),
    (16, (30, -5, 70), "rebote"),
    (18, (27, -4, 64), "suave"),  # se asienta un poco tras pasarse
    (22, (32, -5, 66), "suave"),
    (33, (6, 0, -12), "suave"),
    (40, (6, 0, -18), "suave"),
]
# La cabeza compensa el giro del torso para seguir mirando al blanco.
CABEZA_ROT = [
    (0, (0, 0, 18), "suave"),
    (10, (-4, 0, 72), "suave"),
    (12, (-4, 0, 76), "suave"),
    (15, (-26, 0, -70), "rebote"),
    (22, (-26, 0, -64), "suave"),
    (33, (-2, 0, 10), "suave"),
    (40, (0, 0, 18), "suave"),
]
# Brazo izquierdo (guardia): dirección en el sistema del torso. Se estira al cargar y se recoge de golpe.
BRAZO_I_DIR = [
    (0, (0.30, -0.70, -0.55), "suave"),
    (10, (0.15, -0.95, -0.25), "suave"),
    (12, (0.15, -0.95, -0.25), "suave"),
    (15, (0.80, 0.35, -0.45), "golpe"),
    (22, (0.85, 0.45, -0.35), "suave"),
    (40, (0.30, -0.70, -0.55), "suave"),
]
# Brazo derecho (el que golpea): dirección en el MUNDO. Hacia atrás al cargar y recto hacia delante al golpear.
BRAZO_D_DIR = [
    (0, (-0.20, -0.75, -0.55), "suave"),
    (10, (-0.50, 0.85, -0.25), "suave"),
    (13, (-0.55, 0.75, -0.05), "suave"),
    (16, (-0.04, -1.00, 0.04), "golpe"),
    (22, (-0.04, -1.00, 0.02), "sale"),
    (30, (-0.20, -0.80, -0.40), "suave"),
    (40, (-0.20, -0.75, -0.55), "suave"),
]
# Pies (posición de la punta de la pierna en studs). El izquierdo es el adelantado y no se mueve del suelo: con
# piernas rígidas, un pie que viaja mientras el torso avanza obliga a hundir el cuerpo (se vio en la hoja de la ronda 0).
PIE_I = [(0, (1.0, -1.5, 0.0), "suave"), (40, (1.0, -1.5, 0.0), "suave")]
PIE_D = [
    (0, (-1.2, 0.8, 0.0), "suave"),
    (12, (-1.2, 0.8, 0.0), "suave"),
    (14, (-1.1, 0.4, 0.2), "golpe"),
    (16, (-0.9, -0.3, 0.3), "sale"),  # la pierna trasera se queda estirada hacia atrás, de puntillas
    (22, (-0.9, -0.3, 0.3), "suave"),
    (31, (-1.2, 0.8, 0.0), "suave"),
    (40, (-1.2, 0.8, 0.0), "suave"),
]

# Fotogramas que se enseñan en la hoja de contactos: (fotograma, nombre).
FOTOGRAMAS_CLAVE = [
    (0, "Guardia"),
    (6, "Anticipación"),
    (10, "Máx. anticipación"),
    (13, "El torso arranca"),
    (14, "El puño sigue"),
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
        self.q = {b: Quaternion() for b in r6.ARTICULACIONES}
        self.loc = {b: Vector((0, 0, 0)) for b in r6.ARTICULACIONES}

    def mundo(self, hueso):
        """(posición de la articulación en studs, rotación en el mundo)."""
        padre = r6.PADRE[hueso]
        if padre is None:
            return Vector(r6.ARTICULACIONES[hueso]) + self.loc[hueso], self.q[hueso].copy()
        pp, pr = self.mundo(padre)
        desfase = Vector(r6.ARTICULACIONES[hueso]) - Vector(r6.ARTICULACIONES[padre])
        return pp + pr @ (desfase + self.loc[hueso]), pr @ self.q[hueso]

    def punta(self, hueso, largo):
        """Posición de la punta de un brazo o una pierna (el puño, el pie)."""
        pos, rot = self.mundo(hueso)
        return pos + rot @ Vector((0, 0, -largo))

    def poner_rot_mundo(self, hueso, q_mundo):
        padre = r6.PADRE[hueso]
        q_padre = self.mundo(padre)[1] if padre else Quaternion()
        self.q[hueso] = q_padre.inverted() @ q_mundo


def _euler(grados):
    return Euler([math.radians(g) for g in grados], "XYZ").to_quaternion()


def _torso_euler(inclinacion, ladeo, giro):
    """Inclinación hacia delante (-Y) = giro positivo alrededor de X; ladeo hacia su izquierda (+X) = giro positivo
    alrededor de Y; giro a la izquierda = giro positivo alrededor de Z. Orden: ladeo, giro, inclinación."""
    return _euler((inclinacion, ladeo, giro))


ABAJO = Vector((0, 0, -1))
ERRORES_PIE = {}  # fotograma -> (error pie izq., error pie der.) en studs, para comprobar que llegan al suelo


def _apuntar(pose, hueso, direccion):
    """Orienta una pieza rígida (que en reposo cuelga hacia abajo) para que apunte hacia `direccion` (en el mundo)."""
    pose.poner_rot_mundo(hueso, ABAJO.rotation_difference(direccion.normalized()))


def _altura_del_torso(pose, objetivo):
    """Busca la altura del torso para que la pierna adelantada (la que apoya todo el rato) llegue exactamente a su
    punto del suelo. La trasera solo apunta hacia el suyo: puede levantarse (de puntillas) sin condicionar la altura."""

    def sobrante(z):
        pose.loc["Torso"].z = z
        cadera = pose.mundo("Left Leg")[0]
        return (objetivo - cadera).length - r6.LARGO_PIERNA

    bajo, alto = -2.5, 1.0  # más alto el torso, más lejos quedan los pies
    for _ in range(40):
        medio = (bajo + alto) / 2
        if sobrante(medio) > 0:
            alto = medio
        else:
            bajo = medio
    pose.loc["Torso"].z = (bajo + alto) / 2


def calcular_pose(fotograma):
    p = Pose()
    x, y = muestrear(TORSO_POS, fotograma)
    p.loc["Torso"] = Vector((x, y, 0))
    p.q["Torso"] = _torso_euler(*muestrear(TORSO_ROT, fotograma))
    p.q["Head"] = _euler(muestrear(CABEZA_ROT, fotograma))

    # Piernas: primero la altura del torso (según la pierna de apoyo), luego cada pierna apunta a su pie.
    objetivos = {
        "Left": Vector(muestrear(PIE_I, fotograma)),
        "Right": Vector(muestrear(PIE_D, fotograma)),
    }
    _altura_del_torso(p, objetivos["Left"])
    errores = []
    for lado, objetivo in objetivos.items():
        cadera = p.mundo(f"{lado} Leg")[0]
        _apuntar(p, f"{lado} Leg", objetivo - cadera)
        errores.append((p.punta(f"{lado} Leg", r6.LARGO_PIERNA) - objetivo).length)
    ERRORES_PIE[fotograma] = (errores[0], errores[1])

    # Brazos: el izquierdo en el sistema del torso, el derecho (que golpea) en el del mundo.
    _, rot_torso = p.mundo("Torso")
    _apuntar(p, "Left Arm", rot_torso @ Vector(muestrear(BRAZO_I_DIR, fotograma)))
    _apuntar(p, "Right Arm", Vector(muestrear(BRAZO_D_DIR, fotograma)))
    return p


def punto_de_impacto():
    """Dónde está el puño en el fotograma del impacto (studs), para colocar el saco del render."""
    pose = calcular_pose(IMPACTO)
    return pose.punta("Right Arm", r6.LARGO_BRAZO), pose.mundo("Right Arm")[1] @ ABAJO * -1


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
            if pb.name == "Torso":
                pb.location = pose.loc[pb.name] * r6.ESTUDIO
                pb.keyframe_insert("location", frame=f)
    return accion
