"""
TROTAR: trote ligero en bucle para R6, con una fase en el aire corta. Es el ritmo de la W normal (16 studs/s):
andar a esa velocidad sin patinar es imposible con piernas rígidas de 2 studs, pero trotar sí cuadra.

Fase 0 = la pierna izquierda aterriza. Cada pie está en el suelo una fracción `apoyo` del ciclo; el resto del medio
ciclo el cuerpo vuela (los dos pies en el aire) siguiendo una parábola. El pie despega de puntillas con la cadera
todavía subiendo por encima de la punta, así que el vuelo arranca hacia arriba sin tirón; el aterrizaje sí lleva un
pequeño golpe (con piernas rígidas es inevitable), que se lee como la pisada.

Ángulos en grados. Ver andar.py para el significado de cada canal.
"""

from ciclo import espejo
from marcha import Marcha

NOMBRE = "Trotar"
FPS = 30
CICLO = 18  # 0,6 s por ciclo: 200 pasos por minuto (trote ligero)
VELOCIDAD = 16.0  # studs/s: la velocidad normal del juego (PlanetaRedondo.Personaje.Andar)
PRIORIDAD = "Movement"

DATOS = dict(
    fps=FPS,
    ciclo=CICLO,
    velocidad=VELOCIDAD,
    apoyo=0.22,  # más tiempo en el suelo que al correr: vuelo corto y suave
    flecha=0.03,
    ancho_pisada=-0.05,  # al correr el pie cae un poco hacia dentro
    alfa_despegue=-14.0,
    abrir_aire=0.0,  # abrirla hacia fuera baja la arista interior de la bota: mejor recta
    alcance_aire=26,
    inercia=1.0,
    aire_claves=[(0.40, -54.0), (0.68, -2.0), (0.82, 40.0)],
    torso_x=espejo([(0.0, 0.05), (0.12, 0.06), (0.3, 0.02)]),
    torso_y=espejo([(0.0, 0.0), (0.25, 0.0)], +1),
    inclinacion=espejo([(0.0, 9.0), (0.06, 11.5), (0.16, 8.0), (0.3, 10.0)], +1),
    ladeo=espejo([(0.0, 4.0), (0.12, 5.0), (0.3, 2.0)]),
    giro=espejo([(0.0, -9.0), (0.25, 0.0)]),
    brazo=[(0.0, (38.0, 9.0, 12.0)), (0.25, (8.0, 7.0, 0.0)), (0.5, (-32.0, 12.0, -9.0)), (0.75, (8.0, 7.0, 0.0))],
    retraso_brazos=0.05,
    cabeza=[(0.0, (-5.0, 0.0, 5.0)), (0.07, (-8.0, -2.0, 3.0)), (0.25, (-5.0, -1.5, 0.0)), (0.5, (-5.0, 0.0, -5.0)), (0.57, (-8.0, 2.0, -3.0)), (0.75, (-5.0, 1.5, 0.0))],
    retraso_cabeza=0.04,
)

MARCHA = Marcha(DATOS)
calcular_pose = MARCHA.calcular_pose
ULTIMO_FOTOGRAMA = CICLO

FOTOGRAMAS_CLAVE = [
    (0, "Aterriza izq."),
    (2, "Apoyo"),
    (3, "Despega"),
    (6, "En el aire"),
    (9, "Aterriza der."),
    (11, "Apoyo"),
    (12, "Despega"),
    (15, "En el aire"),
]

BUCLE = True
TITULO = "TROTAR  R6  -  18 f (0,6 s)  -  pie quieto a 16 studs/s"
metricas = MARCHA.metricas
LIMITES = dict(hundido=0.02, flota=0.05, patina=0.005, roce=0.03)
