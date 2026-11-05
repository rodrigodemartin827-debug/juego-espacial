"""
ANDAR: ciclo de marcha en bucle para R6.

Fase 0 = la pierna izquierda apoya el talón delante. La izquierda está en el suelo de 0 a 0,5 y la derecha de 0,5 a 1
(el cambio de pie es instantáneo: con piernas rígidas, el doble apoyo largo de una persona obligaría a patinar).

Todos los ángulos en grados. Las curvas son cíclicas (ver ciclo.ciclica); `espejo` copia el paso izquierdo en el
derecho, con el signo cambiado en lo que va de un lado a otro.
"""

from ciclo import espejo
from marcha import Marcha

NOMBRE = "Andar"
FPS = 30
CICLO = 24  # fotogramas: 0,8 s por ciclo (2 pasos), 150 pasos por minuto
VELOCIDAD = 7.5  # studs/s a los que el pie no patina (velocidad de reproducción = WalkSpeed / VELOCIDAD)
PRIORIDAD = "Movement"

DATOS = dict(
    fps=FPS,
    ciclo=CICLO,
    velocidad=VELOCIDAD,
    apoyo=0.5,
    flecha=0.04,  # la suela "redondeada" queda como mucho 0,04 studs por encima del suelo en mitad de la pisada
    ancho_pisada=0.0,
    alfa_despegue=None,
    abrir_aire=6.0,
    alcance_aire=0.0,
    # Torso: el peso va sobre la pierna de apoyo (balanceo lateral y ladeo) y la cadera gira con la pierna que avanza.
    torso_x=espejo([(0.0, 0.0), (0.25, 0.12)]),
    torso_y=espejo([(0.0, -0.04), (0.25, 0.04)], +1),  # el cuerpo frena un poco al pasar sobre el pie
    inclinacion=espejo([(0.0, 7.0), (0.15, 5.0), (0.4, 9.0)], +1),
    ladeo=espejo([(0.0, 0.0), (0.22, 7.0)]),
    giro=espejo([(0.0, -7.0), (0.25, 0.0)]),
    # Brazo DERECHO (el izquierdo es el mismo medio ciclo después): (adelante, separado, giro sobre su eje).
    brazo=[(0.0, (32.0, 5.0, 10.0)), (0.25, (3.0, 4.0, 0.0)), (0.5, (-30.0, 11.0, -8.0)), (0.75, (3.0, 4.0, 0.0))],
    retraso_brazos=0.05,
    # Cabeza (inclinación, ladeo, giro) relativa al torso: compensa el giro y el ladeo para mirar al frente.
    cabeza=[(0.0, (-4.0, 0.0, 5.5)), (0.1, (-1.5, -2.0, 3.0)), (0.25, (-3.5, -4.0, 0.0)), (0.5, (-4.0, 0.0, -5.5)), (0.6, (-1.5, 2.0, -3.0)), (0.75, (-3.5, 4.0, 0.0))],
    retraso_cabeza=0.03,
)

MARCHA = Marcha(DATOS)
calcular_pose = MARCHA.calcular_pose
ULTIMO_FOTOGRAMA = CICLO

FOTOGRAMAS_CLAVE = [
    (0, "Contacto izq."),
    (3, "Recibe el peso"),
    (6, "Paso medio"),
    (9, "Impulso"),
    (12, "Contacto der."),
    (15, "Recibe el peso"),
    (18, "Paso medio"),
    (21, "Impulso"),
]

BUCLE = True
TITULO = "ANDAR  R6  -  24 f (0,8 s)  -  pie quieto a 7,5 studs/s"
metricas = MARCHA.metricas
# Lo que se admite (studs): bota hundida, bota apoyada flotando, arista clavada que se mueve y bota en el aire que
# pasa a menos de `roce` del suelo.
LIMITES = dict(hundido=0.02, flota=0.05, patina=0.005, roce=0.03)
