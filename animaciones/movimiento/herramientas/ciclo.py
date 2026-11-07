"""
Núcleo común de las animaciones de movimiento en bucle (reposo, andar, correr) para el rig R6.

Reutiliza el rig y la cinemática directa del puñetazo (`animaciones/herramientas`): mismos huesos, mismos pivotes y la
misma clase `Pose`. Lo nuevo es lo que necesita un ciclo de locomoción:

  * Curvas CÍCLICAS (spline de Catmull-Rom cerrada): el último fotograma enlaza con el primero con la misma posición
    y la misma velocidad, así que el bucle no tiene saltos ni tirones.
  * Un modelo de la BOTA de R6 para que los pies no patinen ni se hundan. La pierna de R6 es una pieza rígida de
    2 studs sin rodilla ni tobillo, así que el pie no puede doblarse: la suela rueda sobre el suelo como un balancín.
    Se apoya primero en el talón, rueda por la planta y se despega por la punta, sin deslizar en ningún momento.
  * Un resolvedor de la pierna de apoyo: dada la posición de la cadera (que manda el torso) y la huella del pie en el
    suelo, calcula el ángulo de la pierna y la ALTURA del torso que dejan el pie exactamente en su huella. Así el
    cuerpo sube y baja él solo, como un péndulo invertido, que es lo que hace un cuerpo de verdad al andar.

Ejes de Blender (los del rig): X = izquierda del personaje, -Y = hacia delante, Z = arriba. Medidas en studs.
"""

import math

from mathutils import Euler, Quaternion, Vector

import rig_r6 as r6
from punetazo_fuerte import Pose  # noqa: F401  (se reexporta para las animaciones)

ABAJO = Vector((0, 0, -1))
PIERNAS = {"Left Leg": 1, "Right Leg": -1}  # lado: +1 izquierda (+X), -1 derecha
BRAZOS = {"Left Arm": 1, "Right Arm": -1}

# ---------------------------------------------------------------------------------------------
# Curvas
# ---------------------------------------------------------------------------------------------


def _tupla(v):
    return tuple(v) if isinstance(v, (tuple, list)) else (v,)


def ciclica(claves, t, periodo=1.0):
    """Spline de Catmull-Rom CERRADA. claves = [(t, valor)] con t en [0, periodo), en orden.

    Las tangentes son diferencias centradas (también entre el último y el primero), así que la curva tiene la misma
    posición y velocidad al dar la vuelta: bucle perfecto. Devuelve un número o una tupla, según las claves.
    """
    n = len(claves)
    escalar = not isinstance(claves[0][1], (tuple, list))
    ts = [c[0] for c in claves]
    vs = [_tupla(c[1]) for c in claves]
    t = t % periodo

    def punto(i):  # tiempo y valor de la clave i, con vuelta (i puede salirse de 0..n-1)
        vueltas, j = divmod(i, n)
        return ts[j] + vueltas * periodo, vs[j]

    i = n - 1
    for k in range(n):
        if ts[k] > t:
            i = k - 1
            break
    t0, p0 = punto(i)
    t1, p1 = punto(i + 1)
    if t < t0:  # tramo que cruza el final del periodo
        t += periodo
    tm, pm = punto(i - 1)
    t2, p2 = punto(i + 2)
    dt = t1 - t0
    s = (t - t0) / dt
    h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
    out = []
    for a, b, am, bp in zip(p0, p1, pm, p2):
        m0 = (b - am) / (t1 - tm) * dt
        m1 = (bp - a) / (t2 - t0) * dt
        out.append(h00 * a + h10 * m0 + h01 * b + h11 * m1)
    return out[0] if escalar else tuple(out)


def espejo(medio, signo=-1):
    """Claves de medio ciclo [0, 0.5) -> ciclo entero: la segunda mitad repite la primera con `signo`
    (-1 para lo que va de un lado a otro, como el balanceo; +1 para lo que se repite en cada paso, como la inclinación).
    Así el paso izquierdo y el derecho son simétricos por construcción."""
    out = list(medio)
    for t, v in medio:
        out.append((t + 0.5, tuple(signo * x for x in v) if isinstance(v, tuple) else signo * v))
    return out


def hermite(p0, m0, p1, m1, s):
    """Curva de Hermite cúbica entre (p0, pendiente m0) y (p1, pendiente m1), s de 0 a 1 (pendientes por unidad de s)."""
    h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
    return h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1


def suave(t):
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------------------------------------
# Rotaciones
# ---------------------------------------------------------------------------------------------


def rot_torso(inclinacion, ladeo, giro):
    """Grados. Inclinación hacia delante (+X), ladeo hacia su izquierda (+Y), giro a su izquierda (+Z).
    Misma convención que el puñetazo."""
    return Euler([math.radians(g) for g in (inclinacion, ladeo, giro)], "XYZ").to_quaternion()


def rot_pierna(alfa, gamma):
    """Rotación de una pieza que cuelga: `alfa` = cuánto adelanta la punta (rad, + hacia delante = -Y),
    `gamma` = ladeo alrededor del eje que mira hacia delante (rad, + lleva la punta hacia -X)."""
    return Quaternion((0, 1, 0), gamma) @ Quaternion((1, 0, 0), -alfa)


def apuntar(pose, hueso, direccion):
    """Orienta una pieza rígida que cuelga para que apunte a `direccion` (mundo), con el giro mínimo."""
    pose.poner_rot_mundo(hueso, ABAJO.rotation_difference(direccion.normalized()))


def dir_brazo(adelante, fuera, lado):
    """Dirección de un brazo en el sistema del torso. `adelante` y `fuera` en grados (fuera = separarlo del cuerpo)."""
    a, b = math.radians(adelante), math.radians(fuera)
    v = Vector((0, -math.sin(a), -math.cos(a)))
    # separar: girar alrededor de Y hacia fuera del cuerpo (+X para el izquierdo, -X para el derecho)
    return Quaternion((0, 1, 0), -lado * b) @ v


# ---------------------------------------------------------------------------------------------
# La bota de R6 como balancín
# ---------------------------------------------------------------------------------------------
# En el sistema del hueso de la pierna (origen en la cadera, pieza colgando): la suela está a z = -2; la bota va de
# y = -0,72 (punta) a y = +0,52 (talón), centrada en y = -0,10; a lo ancho, su centro está 0,5 hacia dentro del pivote.
PUNTA_Y, TALON_Y, SUELA_Z = -0.72, 0.52, -r6.LARGO_PIERNA
SUELA_X = (-0.52, 0.52)  # alrededor del centro de la bota
CENTRO_BOTA_Y = (PUNTA_Y + TALON_Y) / 2
MEDIO_LARGO = (TALON_Y - PUNTA_Y) / 2


class Bota:
    """La suela se modela como un arco que pasa por el talón y la punta y queda `flecha` studs por debajo de la planta
    en el centro. Al rodar sobre ese arco el pie avanza sin patinar; fuera del arco la bota pivota sobre la arista del
    talón (pierna adelantada) o de la punta (pierna atrasada), que se quedan clavadas en el suelo.

    Con flecha pequeña la bota se comporta como una suela plana: casi no flota (como mucho `flecha` studs en el
    centro de la pisada, y solo en ese instante), pero el cuerpo baja un poco al pasar por la planta."""

    def __init__(self, flecha):
        self.f = flecha
        self.rho = (MEDIO_LARGO**2 + flecha**2) / (2 * flecha)
        self.beta = math.asin(MEDIO_LARGO / self.rho)  # ángulo de la pierna en el que el arco llega al talón/punta

    def contacto(self, alfa, lado):
        """(punto de la bota que toca el suelo en el sistema de la pierna, avance de ese punto en el suelo respecto a la
        huella, fase: 'talon' | 'planta' | 'punta')."""
        xc = -0.5 * lado
        if alfa > self.beta:
            return Vector((xc, TALON_Y, SUELA_Z)), self.rho * self.beta, "talon"
        if alfa < -self.beta:
            return Vector((xc, PUNTA_Y, SUELA_Z)), -self.rho * self.beta, "punta"
        centro = Vector((xc, CENTRO_BOTA_Y, SUELA_Z - self.f + self.rho))
        abajo_local = Quaternion((1, 0, 0), alfa) @ ABAJO  # el "abajo" del mundo visto desde la pierna
        return centro + self.rho * abajo_local, self.rho * alfa, "planta"


def esquinas_suela(lado):
    """Las 4 esquinas inferiores de la bota, en el sistema de la pierna."""
    xc = -0.5 * lado
    return [Vector((xc + dx, y, SUELA_Z)) for dx in SUELA_X for y in (PUNTA_Y, TALON_Y)]


def apoyo(pose, pierna, huella, bota):
    """Pierna de apoyo: `huella` = (x, y) en el suelo del punto de referencia de la pisada (centro de la planta).

    Con el torso ya colocado (sin su altura definitiva), calcula el ángulo de la pierna que deja la cadera encima de
    la bota rodando y cuánto hay que subir o bajar el torso para que la bota toque el suelo sin hundirse.
    Devuelve (subida del torso, rotación de la pierna en el mundo, fase del pie)."""
    lado = PIERNAS[pierna]
    cadera = pose.mundo(pierna)[0]
    hx, hy = huella

    def cadera_y(alfa):
        p, avance, _ = bota.contacto(alfa, lado)
        return hy + avance - (Quaternion((1, 0, 0), -alfa) @ p).y

    bajo, alto = -1.4, 1.4  # cadera_y crece con alfa
    for _ in range(60):
        medio = (bajo + alto) / 2
        if cadera_y(medio) < cadera.y:
            bajo = medio
        else:
            alto = medio
    alfa = (bajo + alto) / 2
    p, _, fase = bota.contacto(alfa, lado)

    # Ladeo: que la cadera quede en su x (la pisada no está justo debajo si el torso se balancea). Una bota que se
    # ladea pivota sobre la arista lateral que baja (como un ladrillo), no sobre su centro: así no se hunde. Se prueba
    # con la arista de cada lado y se queda la que es coherente con el sentido del ladeo.
    def resolver_ladeo(dx):
        pp = Quaternion((1, 0, 0), -alfa) @ (p + Vector((dx, 0, 0)))
        objetivo_x = cadera.x - (hx + dx)  # cadera respecto a la arista de apoyo

        def cadera_x(g):
            return -(Quaternion((0, 1, 0), g) @ pp).x

        bajo, alto = -0.6, 0.6  # cadera_x crece con g (pp.z ~ -2)
        for _ in range(60):
            medio = (bajo + alto) / 2
            if cadera_x(medio) < objetivo_x:
                bajo = medio
            else:
                alto = medio
        return (bajo + alto) / 2, pp

    medio_ancho = SUELA_X[1]
    gamma, pp = resolver_ladeo(medio_ancho)
    if gamma < 0:
        gamma, pp = resolver_ladeo(-medio_ancho)
        gamma = min(gamma, 0.0)
    z_cadera = -(Quaternion((0, 1, 0), gamma) @ pp).z
    return z_cadera - cadera.z, rot_pierna(alfa, gamma), (fase, alfa, gamma)


def suelo_minimo(pose, pierna):
    """Altura de la esquina más baja de la bota (negativo = hundida en el suelo)."""
    pos, rot = pose.mundo(pierna)
    return min((pos + rot @ e).z for e in esquinas_suela(PIERNAS[pierna]))


def punto_mundo(pose, hueso, local):
    pos, rot = pose.mundo(hueso)
    return pos + rot @ local


# ---------------------------------------------------------------------------------------------
# Horneado en Blender
# ---------------------------------------------------------------------------------------------

HUESOS_CON_POSICION = ("Torso", "Head", "Left Arm", "Right Arm")


def hornear(armature, nombre, calcular_pose, ultimo, fps):
    """Una clave por fotograma en todos los huesos, de 0 a `ultimo` (que es igual que el 0: bucle cerrado)."""
    import bpy

    scn = bpy.context.scene
    scn.render.fps = fps
    scn.frame_start = 0
    scn.frame_end = ultimo
    armature.animation_data_create()
    accion = bpy.data.actions.new(nombre)
    armature.animation_data.action = accion
    anterior = {}
    for f in range(ultimo + 1):
        pose = calcular_pose(f)
        for pb in armature.pose.bones:
            q = pose.q[pb.name].copy()
            if pb.name in anterior and anterior[pb.name].dot(q) < 0:
                q.negate()  # evita saltos de signo del cuaternión entre fotogramas
            anterior[pb.name] = q
            pb.rotation_quaternion = q
            pb.keyframe_insert("rotation_quaternion", frame=f)
            if pb.name in HUESOS_CON_POSICION:
                pb.location = pose.loc[pb.name] * r6.ESTUDIO
                pb.keyframe_insert("location", frame=f)
    return accion
