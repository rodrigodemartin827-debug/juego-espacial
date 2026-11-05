"""
REPOSO (idle): bucle de 4 s para R6.

Qué se mueve:
  * Respiración (2 por ciclo, 2 s cada una): el pecho se abre (el torso se echa un poco atrás), los hombros suben
    (los brazos se desplazan hacia arriba unas centésimas, como al coger aire) y la cabeza acompaña.
  * Cambio de peso lento (1 por ciclo): el torso se desplaza de un pie a otro. Los pies NO se mueven: las piernas, que
    son rígidas, se ladean sobre la arista de la bota, y para que los dos pies sigan tocando el suelo el torso se
    ladea solo (sale de resolver las dos piernas a la vez, ver `_pose`), que es justo el "contrapposto" de quien carga
    el peso en una pierna.
  * La mirada se da una vuelta suave, y los brazos se balancean un poco por inercia, con retraso respecto al torso.

Todo son curvas cíclicas (ver ciclo.ciclica), así que el fotograma 120 es idéntico al 0 en posición y velocidad.
"""

import math

from mathutils import Vector

import ciclo
from ciclo import Pose, ciclica

NOMBRE = "Reposo"
FPS = 30
CICLO = 120  # 4 s
ULTIMO_FOTOGRAMA = CICLO
VELOCIDAD = 0.0
PRIORIDAD = "Idle"
BUCLE = True
PASO_GIF = 2  # el GIF a 15 fps basta para un movimiento tan lento (y pesa la mitad)
TITULO = "REPOSO  R6  -  120 f (4 s)  -  2 respiraciones y un cambio de peso"

BOTA = ciclo.Bota(0.004)  # planta casi plana: en reposo el pie está apoyado entero
ANCHO_PIES = 0.20  # cada pie, hacia fuera de su cadera (studs)

# Fase 0..1 del ciclo. Respiración: 0 = fin de soltar el aire; coge aire hasta 0.22 y lo suelta hasta 0.5 (y repite).
RESPIRA = [(0.0, 0.0), (0.22, 1.0), (0.5, 0.0), (0.72, 1.0)]
# Cambio de peso: torso hacia su izquierda (+X) y luego hacia la derecha, en studs, con algo de pausa en cada lado.
PESO_X = [(0.0, 0.0), (0.16, 0.15), (0.32, 0.17), (0.5, 0.0), (0.66, -0.15), (0.82, -0.17)]
TORSO_Y = [(0.0, 0.0), (0.25, -0.015), (0.5, 0.0), (0.75, 0.015)]
GIRO = [(0.0, 0.0), (0.25, 4.0), (0.5, 0.0), (0.75, -4.0)]  # la cadera gira un poco hacia el pie que carga
INCLINACION_BASE = 2.5
# Cabeza (inclinación, ladeo, giro) relativa al torso: compensa el ladeo y mira un poco a los lados.
CABEZA = [
    (0.0, (0.0, 0.0, 0.0)),
    (0.2, (-2.0, -4.0, 9.0)),
    (0.38, (1.0, -5.0, 12.0)),
    (0.55, (1.5, 0.0, -1.0)),
    (0.75, (-1.5, 4.0, -8.0)),
    (0.9, (0.5, 2.0, -4.0)),
]
# Brazos (adelante, separado, giro sobre su eje) para el DERECHO; el izquierdo, espejo con su propio retraso.
BRAZO = [(0.0, (5.0, 7.0, 12.0)), (0.25, (7.0, 9.0, 15.0)), (0.5, (4.0, 7.5, 12.0)), (0.75, (6.0, 6.0, 9.0))]


def _torso(fase, ladeo):
    pose = Pose()
    r = ciclica(RESPIRA, fase)
    pose.loc["Torso"] = Vector((ciclica(PESO_X, fase), ciclica(TORSO_Y, fase), 0.0))
    pose.q["Torso"] = ciclo.rot_torso(INCLINACION_BASE - 1.4 * r, ladeo, ciclica(GIRO, fase))
    return pose


def _huellas():
    pose = Pose()
    out = {}
    for pierna, lado in ciclo.PIERNAS.items():
        cadera = pose.mundo(pierna)[0]
        out[pierna] = (cadera.x - 0.5 * lado + lado * ANCHO_PIES, cadera.y + ciclo.CENTRO_BOTA_Y)
    return out


HUELLAS = _huellas()


def _pose(fase):
    """Busca el ladeo del torso con el que las dos piernas piden la misma altura (los dos pies en el suelo)."""

    def diferencia(ladeo):
        pose = _torso(fase, ladeo)
        z = [ciclo.apoyo(pose, p, HUELLAS[p], BOTA)[0] for p in ciclo.PIERNAS]
        return z[0] - z[1]

    bajo, alto = -10.0, 10.0
    d_bajo = diferencia(bajo)
    for _ in range(50):
        medio = (bajo + alto) / 2
        d = diferencia(medio)
        if (d > 0) == (d_bajo > 0):
            bajo, d_bajo = medio, d
        else:
            alto = medio
    ladeo = (bajo + alto) / 2
    pose = _torso(fase, ladeo)
    sube, q_izq, _ = ciclo.apoyo(pose, "Left Leg", HUELLAS["Left Leg"], BOTA)
    pose.loc["Torso"].z = sube
    pose.poner_rot_mundo("Left Leg", q_izq)
    pose.poner_rot_mundo("Right Leg", ciclo.apoyo(pose, "Right Leg", HUELLAS["Right Leg"], BOTA)[1])
    return pose, ladeo


def calcular_pose(fotograma):
    fase = (fotograma % CICLO) / CICLO
    pose, _ = _pose(fase)
    r = ciclica(RESPIRA, fase)
    rot_t = pose.mundo("Torso")[1]
    for brazo, lado in ciclo.BRAZOS.items():
        retraso = 0.04 if lado < 0 else 0.06
        adelante, fuera, giro = ciclica(BRAZO, fase - retraso + (0.5 if lado > 0 else 0.0))
        # al coger aire los brazos se separan un pelo y los hombros suben
        # inercia: cuando el torso se desplaza a un lado, los brazos se quedan un poco atrás
        inercia = -lado * 3.0 * ciclica(PESO_X, fase - 0.08) / 0.17
        d = ciclo.dir_brazo(adelante, fuera + 1.5 * r + inercia, lado)
        ciclo.apuntar(pose, brazo, rot_t @ d)
        q_eje = ciclo.Quaternion(d, math.radians(giro) * -lado)
        pose.poner_rot_mundo(brazo, rot_t @ q_eje @ rot_t.inverted() @ pose.mundo(brazo)[1])
        pose.loc[brazo] = Vector((0.0, 0.0, 0.065 * ciclica(RESPIRA, fase - 0.02)))
    cab = ciclica(CABEZA, fase - 0.03)
    pose.q["Head"] = ciclo.rot_torso(cab[0] + 1.6 * r, cab[1], cab[2])
    return pose


def metricas():
    hundido = flota = patina = 0.0
    ladeos = []
    ref = {}
    for i in range(CICLO * 2):
        f = i / 2
        pose = calcular_pose(f)
        ladeos.append(_pose(f / CICLO)[1])
        for pierna, lado in ciclo.PIERNAS.items():
            m = ciclo.suelo_minimo(pose, pierna)
            hundido = max(hundido, -m)
            flota = max(flota, m)
            # el centro de la planta no debe moverse (los pies están quietos)
            c = ciclo.punto_mundo(pose, pierna, Vector((-0.5 * lado, ciclo.CENTRO_BOTA_Y, -2)))
            ref.setdefault(pierna, c)
            patina = max(patina, (Vector((c.x, c.y, 0)) - Vector((ref[pierna].x, ref[pierna].y, 0))).length)
    return dict(hundido=hundido, flota=flota, patina=patina, ladeo_max=max(abs(x) for x in ladeos))


# Ladeado, la bota apoya en una arista y la otra se levanta un poco: se admite hasta 0,03 studs. El centro de la planta
# puede moverse un pelo al rodar de una arista a otra (0,03).
LIMITES = dict(hundido=0.01, flota=0.03, patina=0.03)

FOTOGRAMAS_CLAVE = [
    (0, "Suelta el aire"),
    (14, "Coge aire"),
    (26, "Lleno"),
    (38, "Peso a la izq."),
    (60, "Suelta / centro"),
    (86, "Coge aire"),
    (98, "Peso a la der."),
    (112, "Vuelve"),
]
