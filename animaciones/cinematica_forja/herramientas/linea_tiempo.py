"""
Línea de tiempo de la cinemática de la forja: TODOS los datos ajustables (fotogramas, posiciones, poses, colores,
cámaras, partículas). La lógica que los convierte en movimiento está en cinematica.py.

Mundo (Blender, studs): X a la derecha mirando al horno desde la entrada, Y hacia el horno, Z arriba.
El personaje: su sistema local es el de rig_r6 (mira a -Y, su izquierda es +X, los pies en z = 0). «giro» es el giro
del personaje sobre Z en grados: 0 = mira a -Y (hacia la entrada), 180 = mira a +Y (al horno), 90 = mira a +X.

Cada canal es una lista de claves (fotograma, valor, easing); el easing es el del tramo que LLEGA a la clave.
Easings: suave, entra, sale, golpe (explosivo), rebote (se pasa y vuelve), lineal, cte (salto seco).
"""

from mathutils import Vector

FPS = 30
DURACION = 436  # fotogramas 0..435 = 14,5 s

# ---------------------------------------------------------------------------------------------------------------
# Fases (para el documento y la hoja de contactos)
# ---------------------------------------------------------------------------------------------------------------
FASES = [
    (0, 108, "1. El horno"),
    (108, 258, "2. El yunque"),
    (258, 360, "3. El temple"),
    (360, 436, "4. El resultado"),
]

# Impactos del martillo (fotograma exacto del golpe). Cada uno más fuerte que el anterior.
IMPACTOS = [150, 168, 186, 206, 232]
FUERZA_GOLPE = [0.55, 0.65, 0.78, 0.9, 1.0]  # escala la anticipación, las chispas y el temblor
CHISPAS_GOLPE = [70, 100, 140, 190, 320]
TEMBLOR_GOLPE = [0.55, 0.75, 1.0, 1.3, 2.1]  # grados de temblor de cámara al impactar
CONTACTO_AGUA = 295  # la punta de la hoja toca el agua (medido: ver cinematica.contacto_agua)

# Dirección de la hoja al templarla (mundo): 55° hacia abajo, hacia el fondo del barril. La hoja entra en el agua
# empujándola a lo largo de este eje, así no roza el borde del barril.
DIRECCION_TEMPLE = (0.0, -0.57, -0.82)

# Dónde golpea el martillo sobre el yunque (mundo). La cara del yunque está a z = 3.42.
GOLPE = Vector((-2.15, -4.0, 3.42))

# ---------------------------------------------------------------------------------------------------------------
# Raíz del personaje (HumanoidRootPart): (x, y, giro)
# ---------------------------------------------------------------------------------------------------------------
PUESTO_COMPUERTA = (-2.5, -0.62)
PUESTO_HORNO = (-2.75, -0.6)
PUESTO_YUNQUE = (-1.6, -1.3)
PUESTO_BARRIL = (2.55, -0.1)

RAIZ = [
    (0, (-7.9, -2.4, 90), "lineal"),
    (24, (-3.9, -1.8, 125), "lineal"),
    (34, (*PUESTO_COMPUERTA, 180), "sale"),
    (58, (*PUESTO_COMPUERTA, 180), "suave"),
    (68, (*PUESTO_HORNO, 180), "suave"),
    (106, (*PUESTO_HORNO, 180), "suave"),
    (114, (-2.55, -1.2, 176), "sale"),  # da un paso atrás con la pieza fuera del horno
    (119, (-2.0, -1.0, 150), "entra"),  # gira hacia su derecha: la pieza pasa lejos del horno
    (130, (*PUESTO_YUNQUE, -15), "sale"),
    (262, (*PUESTO_YUNQUE, -15), "suave"),
    (272, (0.0, -1.0, 35), "entra"),
    (292, (*PUESTO_BARRIL, 0), "sale"),
    (436, (*PUESTO_BARRIL, 0), "suave"),
]

# Desplazamiento del torso (local del personaje, studs): agacharse (z < 0), adelantar el cuerpo (y < 0).
TORSO_POS = [
    (0, (0, 0, 0), "suave"),
    (34, (0, 0, 0), "suave"),
    (40, (0, -0.05, -0.35), "suave"),  # se agacha a coger el asa
    (51, (0, 0.05, 0.1), "sale"),  # estira el cuerpo al subir la compuerta
    (62, (0, 0, 0), "suave"),
    (74, (0, -0.2, -0.1), "suave"),  # se inclina para meter el lingote
    (104, (0, -0.15, -0.1), "suave"),
    (114, (0, 0.05, 0), "suave"),
    (130, (0, 0, -0.1), "suave"),
    (138, (0, 0, -0.18), "suave"),  # saca el martillo del cinto
    *[c for i, f in enumerate([150, 168, 186, 206, 232]) for c in (
        (f - 9 - round(5 * [0.55, 0.65, 0.78, 0.9, 1.0][i]), (0, 0.05, -0.05), "sale"),
        (f, (0, -0.15, -0.3 - 0.04 * i), "golpe"),
        (f + 3, (0, -0.15, -0.3 - 0.04 * i), "cte"),
        (f + 8, (0, 0, -0.18), "suave"))],
    (262, (0, 0, -0.15), "suave"),
    (272, (0, 0, 0), "suave"),
    (298, (0, -0.1, -0.15), "suave"),
    (304, (0, -0.25, -0.3), "golpe"),  # hunde la pieza
    (340, (0, -0.2, -0.25), "suave"),
    (372, (0, 0.08, 0.05), "suave"),  # se yergue con la hoja en alto
    (436, (0, 0.08, 0.05), "suave"),
]
# Rotación del torso: (inclinación hacia delante, ladeo a su izquierda, giro a su izquierda), grados.
TORSO_ROT = [
    (0, (5, 0, 0), "suave"),
    (34, (4, 0, 0), "suave"),
    (40, (9, -4, -8), "suave"),
    (51, (4, -6, -12), "sale"),
    (62, (4, 0, 0), "suave"),
    (74, (18, 2, 4), "suave"),
    (90, (16, 2, 2), "suave"),
    (104, (17, 2, 4), "suave"),
    (114, (2, 0, 10), "suave"),
    (126, (10, 0, 6), "suave"),
    (132, (12, 0, 0), "suave"),
    (138, (10, -6, -14), "suave"),
    *[c for i, f in enumerate([150, 168, 186, 206, 232]) for c in (
        (f - 9 - round(5 * [0.55, 0.65, 0.78, 0.9, 1.0][i]), (0 - 6 * i / 4, -3, -14 - 6 * i / 4), "sale"),  # se arma
        (f, (24 + 6 * i / 4, 3, 8), "golpe"),  # golpe: se vuelca sobre el yunque
        (f + 3, (24 + 6 * i / 4, 3, 8), "cte"),
        (f + 8, (16, 0, -2), "suave"))],
    (262, (10, 0, 0), "suave"),
    (272, (4, 0, 8), "suave"),
    (292, (8, 0, 0), "suave"),
    (304, (24, 0, 2), "golpe"),
    (340, (20, 0, 0), "suave"),
    (372, (-4, 0, 0), "suave"),
    (436, (-5, 0, 0), "suave"),
]
# La cabeza (respecto al torso): (inclinación hacia abajo, ladeo, giro a su izquierda), grados.
CABEZA_ROT = [
    (0, (8, 0, 0), "suave"),
    (24, (6, 0, -25), "suave"),  # mira hacia el horno mientras llega
    (34, (10, 0, 0), "suave"),
    (54, (-12, 0, 6), "sale"),  # sigue la compuerta con la mirada
    (62, (6, 0, 0), "suave"),
    (74, (16, 0, -4), "suave"),
    (104, (14, 0, -2), "suave"),
    (114, (14, 0, -20), "suave"),
    (130, (26, 0, -6), "suave"),
    (262, (26, 0, -6), "suave"),
    (272, (14, 0, 10), "suave"),
    (292, (22, 0, 0), "suave"),
    (306, (30, 0, 0), "suave"),
    (340, (28, 0, 0), "suave"),
    (372, (-24, 0, 0), "suave"),  # mira la hoja en alto
    (436, (-26, 0, 4), "suave"),
]

# Pies (local del personaje, x e y en studs; z = 0 es el suelo). La caminata se suma encima en cinematica.py.
PIES = [
    (0, ((0.55, 0.05), (-0.55, -0.05)), "suave"),
    (34, ((0.55, 0.05), (-0.55, -0.05)), "suave"),
    (62, ((0.6, 0.0), (-0.55, 0.0)), "suave"),
    (74, ((0.65, -0.12), (-0.6, 0.5)), "suave"),  # adelanta el pie izquierdo para llegar al fuego
    (104, ((0.65, -0.12), (-0.6, 0.5)), "suave"),
    (114, ((0.55, 0.0), (-0.55, 0.0)), "suave"),
    (132, ((0.75, -0.3), (-0.75, 0.35)), "suave"),  # postura ancha para golpear
    (262, ((0.75, -0.3), (-0.75, 0.35)), "suave"),
    (272, ((0.55, 0.0), (-0.55, 0.0)), "suave"),
    (294, ((0.6, -0.25), (-0.6, 0.35)), "suave"),
    (436, ((0.6, -0.25), (-0.6, 0.35)), "suave"),
]

# ---------------------------------------------------------------------------------------------------------------
# Brazos. Cada clave: (fotograma, objetivo, easing). Objetivos:
#   ("dir", (x, y, z))            el brazo apunta en esa dirección (local del personaje)
#   ("punto", nombre, herramienta) la punta de la herramienta (o la mano) llega al punto con ese nombre
# Los puntos con nombre los calcula cinematica.py (asa de la compuerta, sitio del golpe...).
# ---------------------------------------------------------------------------------------------------------------
BRAZO_IZQ = [  # tenazas con la pieza
    (0, ("dir", (0.2, -0.3, -0.93), 150), "suave"),  # lleva las tenazas en alto, como una antorcha
    (12, ("dir", (0.2, -0.4, -0.9), 150), "suave"),
    (34, ("dir", (0.35, -0.36, -0.86), 155), "suave"),  # tenazas en vertical, a un lado, para abrir
    (56, ("dir", (0.35, -0.36, -0.86), 155), "suave"),
    (65, ("punto", "boca_horno", "tenazas"), "suave"),  # baja el lingote hacia la boca
    (76, ("punto", "en_brasas", "tenazas"), "suave"),  # lo hunde en las brasas
    (90, ("punto", "en_brasas_2", "tenazas"), "suave"),  # la remueve en las brasas
    (104, ("punto", "en_brasas", "tenazas"), "suave"),
    (112, ("punto", "saca_horno", "tenazas"), "sale"),
    (122, ("dir", (0.05, -0.85, -0.3)), "suave"),
    (127, ("punto", "sobre_yunque", "tenazas"), "suave"),  # llega por encima y la baja
    (132, ("punto", "en_yunque", "tenazas"), "suave"),
    (262, ("punto", "en_yunque", "tenazas"), "suave"),
    (270, ("punto", "alzar", "tenazas"), "sale"),  # la levanta del yunque, tumbada
    (284, ("dir", (0.05, -0.8, -0.3), 75), "suave"),  # la lleva delante, por encima del barril
    (294, ("punto", "sobre_agua", "tenazas"), "suave"),  # en alto, inclinada hacia el agua
    (300, ("punto", "en_agua", "tenazas"), "golpe"),  # la hunde de un empujón a lo largo de la hoja
    (314, ("punto", "en_agua_2", "tenazas"), "suave"),  # la agita en el agua
    (326, ("punto", "en_agua", "tenazas"), "suave"),
    (338, ("punto", "en_agua_2", "tenazas"), "suave"),
    (348, ("punto", "en_agua", "tenazas"), "suave"),
    (358, ("punto", "saca_agua", "tenazas"), "sale"),  # la saca por donde entró
    (372, ("punto", "en_alto", "tenazas"), "suave"),  # la levanta en alto
    (436, ("punto", "en_alto_2", "tenazas"), "suave"),
]
# Martillo: anticipación (arriba y atrás), impacto (punto «golpe»), parada y rebote.
_brazo_der = [
    (0, ("dir", (-0.1, 0.25, -0.96)), "suave"),
    (8, ("dir", (-0.1, -0.25, -0.96)), "suave"),  # balanceo al andar
    (16, ("dir", (-0.1, 0.25, -0.96)), "suave"),
    (24, ("dir", (-0.1, -0.2, -0.97)), "suave"),
    (34, ("dir", (-0.1, 0.0, -1.0)), "suave"),
    (40, ("punto", "asa", "mano"), "suave"),
    (51, ("punto", "asa", "mano"), "suave"),  # sube la compuerta y la suelta: sigue subiendo sola
    (56, ("dir", (-0.2, -0.15, 0.97)), "sale"),
    (66, ("dir", (-0.15, 0.05, -0.98)), "suave"),
    (104, ("dir", (-0.15, 0.05, -0.98)), "suave"),
    (116, ("dir", (-0.12, 0.05, -0.99)), "suave"),  # brazo pegado al cuerpo al girar (pasa junto al yunque)
    (130, ("dir", (-0.25, 0.0, -0.97)), "suave"),
    (136, ("punto", "cinto", "mano"), "suave"),  # coge el martillo del cinto
]
for i, f in enumerate(IMPACTOS):
    k = FUERZA_GOLPE[i]
    arriba = 9 + round(5 * k)  # cuánto antes del impacto está arriba del todo
    _brazo_der += [
        (f - arriba, ("dir", (-0.12, 0.25 + 0.35 * k, 0.95)), "suave" if i == 0 else "sale"),  # anticipación
        (f - arriba + 3, ("dir", (-0.12, 0.3 + 0.38 * k, 0.94)), "suave"),  # tensión arriba
        (f, ("punto", "golpe", "martillo"), "golpe"),  # IMPACTO
        (f + 3, ("punto", "golpe", "martillo"), "cte"),  # parada (hitstop)
        (f + 6, ("dir", (-0.1, -0.85, -0.2)), "sale"),  # rebote
    ]
_brazo_der += [
    (246, ("dir", (-0.4, -0.25, -0.88)), "suave"),
    (262, ("punto", "cinto", "mano"), "suave"),  # devuelve el martillo al cinto
    (270, ("dir", (-0.1, 0.0, -1.0)), "suave"),
    (276, ("dir", (-0.1, 0.25, -0.96)), "suave"),
    (284, ("dir", (-0.1, -0.25, -0.96)), "suave"),
    (294, ("dir", (-0.12, 0.0, -0.99)), "suave"),
    (304, ("dir", (-0.3, -0.3, -0.9)), "suave"),  # equilibrio al hundir la pieza
    (350, ("dir", (-0.3, -0.25, -0.92)), "suave"),
    (372, ("dir", (-0.15, 0.05, -0.98)), "suave"),
    (436, ("dir", (-0.15, 0.05, -0.98)), "suave"),
]
BRAZO_DER = _brazo_der

# Herramientas en la mano: ángulo de agarre (grados entre el brazo y la herramienta, hacia delante).
AGARRE = {"tenazas": 30.0, "martillo": 45.0}
MARTILLO_EN_MANO = (136, 262)  # entre estos fotogramas el martillo va en la mano; fuera, en el cinto

# Orientación de la pieza (ver cinematica.orientacion_pieza): tumbada, abajo (colgando para el temple), arriba
# (en alto para enseñarla) o linea (sigue a las tenazas). Entre claves gira suavemente.
PIEZA_ORIENTACION = [
    (0, "linea", "suave"),
    (58, "linea", "suave"),
    (70, "tumbada", "suave"),
    (284, "tumbada", "suave"),
    (294, "temple", "suave"),  # sobre el barril la inclina hacia el agua
    (358, "temple", "suave"),
    (370, "arriba", "suave"),  # fuera del agua, la levanta punta arriba
    (436, "arriba", "suave"),
]

# Compuerta del horno: cuánto sube (studs). El asa sigue a la mano entre 40 y 55.
COMPUERTA = [(0, 0.0, "suave"), (42, 0.0, "suave"), (51, 1.6, "entra"), (56, 3.25, "sale"), (436, 3.25, "suave")]

# Forma de la pieza: 0 = lingote ... 5 = hoja terminada. Cada golpe sube una etapa en 2 fotogramas.
ETAPA = [(0, 0.0, "suave")]
for i, f in enumerate(IMPACTOS):
    ETAPA += [(f - 1, float(i), "cte"), (f + 1, float(i + 1), "golpe")]
ETAPA += [(436, 5.0, "suave")]

# Calor de la pieza: temperatura (K) y fuerza de emisión. Se enfría con cada golpe y se apaga en el agua.
TEMPERATURA = [
    (0, 700.0, "suave"),
    (68, 760.0, "suave"),
    (82, 1150.0, "sale"),  # en el primer plano ya brilla naranja
    (100, 1450.0, "suave"),
    (112, 1750.0, "suave"),  # blanco-naranja al sacarla
    (150, 1580.0, "suave"),
    (168, 1450.0, "suave"),
    (186, 1320.0, "suave"),
    (206, 1180.0, "suave"),
    (232, 1050.0, "suave"),
    (298, 960.0, "suave"),
    (CONTACTO_AGUA + 14, 820.0, "sale"),
    (CONTACTO_AGUA + 30, 700.0, "suave"),
    (436, 700.0, "suave"),
]
BRILLO = [
    (0, 0.0, "suave"),
    (68, 0.0, "suave"),
    (82, 2.2, "sale"),
    (100, 4.05, "suave"),
    (112, 7.2, "suave"),
    (150, 5.4, "suave"),
    (186, 3.6, "suave"),
    (232, 2.02, "suave"),
    (298, 1.17, "suave"),
    (CONTACTO_AGUA + 12, 0.11, "sale"),
    (CONTACTO_AGUA + 26, 0.0, "suave"),
    (436, 0.0, "suave"),
]
# Pulido: 0 = calamina negra, 1 = acero gris pulido.
PULIDO = [(0, 0.0, "suave"), (CONTACTO_AGUA + 2, 0.0, "suave"), (CONTACTO_AGUA + 26, 0.7, "sale"),
          (372, 1.0, "suave"), (436, 1.0, "suave")]

# Destello del filo: recorre el filo de la base a la punta.
DESTELLO = (392, 408)

# ---------------------------------------------------------------------------------------------------------------
# Luces
# ---------------------------------------------------------------------------------------------------------------
LUZ_HORNO = 1300.0  # W, dentro de la cámara del horno (la compuerta la tapa hasta que se abre)
LUZ_BOCA = [(0, 0.0, "suave"), (44, 0.0, "suave"), (56, 450.0, "sale"), (436, 450.0, "suave")]
LUZ_PIEZA_POR_BRILLO = 60.0  # W de la luz pegada a la pieza por cada unidad de brillo
LUZ_CONTRA = 900.0  # contraluz azul frío (luna)
EXPOSICION = [(0, -9.0, "suave"), (8, 0.5, "sale"), (418, 0.5, "suave"), (435, -12.0, "entra")]

# ---------------------------------------------------------------------------------------------------------------
# Partículas: (nombre, emisor, fotograma inicio, fin, cantidad, parámetros)
# ---------------------------------------------------------------------------------------------------------------
ASCUAS_HORNO = {"inicio": -40, "fin": 436, "cantidad": 520, "vida": 70}
ESTALLIDO_COMPUERTA = {"inicio": 46, "fin": 54, "cantidad": 160, "vida": 26}
CHISPAS_SACAR = {"inicio": 108, "fin": 114, "cantidad": 90, "vida": 20}
VAPOR = {"inicio": CONTACTO_AGUA, "bocanadas": 14, "duracion": 54}
BURBUJAS = {"inicio": CONTACTO_AGUA, "fin": CONTACTO_AGUA + 44, "cantidad": 240, "vida": 10}
OLA_AGUA = [(0, 0.0, "suave"), (CONTACTO_AGUA - 1, 0.0, "cte"), (CONTACTO_AGUA + 2, 0.11, "golpe"),
            (CONTACTO_AGUA + 40, 0.03, "suave"), (CONTACTO_AGUA + 60, 0.0, "suave"), (436, 0.0, "suave")]

# ---------------------------------------------------------------------------------------------------------------
# Cámara: planos. Cada plano: inicio, fin, claves [(fotograma, posición, mira_a, lente_mm)], f-stop, foco.
# mira_a y foco pueden ser un punto o el nombre de un punto que se calcula (pieza, cabeza, golpe...).
# Entre planos hay corte seco.
# ---------------------------------------------------------------------------------------------------------------
PLANOS = [
    {"nombre": "Llegada al horno (plano general, bajo)", "inicio": 0, "fin": 34, "fstop": 4.0, "foco": "cabeza",
     "exposicion": 1.0,
     "claves": [(0, (-13.5, -13.0, 2.0), (-5.0, -1.0, 5.0), 24), (34, (-10.5, -12.2, 2.3), (-3.0, -0.5, 5.2), 26)]},
    {"nombre": "Abre la compuerta (por encima del hombro)", "inicio": 34, "fin": 58, "fstop": 3.2, "foco": "compuerta",
     "claves": [(34, (3.4, -6.4, 5.6), (-2.4, 1.0, 3.9), 30), (58, (2.8, -5.6, 5.3), (-2.5, 1.0, 3.7), 33)]},
    {"nombre": "Detalle del fuego: el lingote entra en las brasas", "inicio": 58, "fin": 82, "fstop": 2.4,
     "foco": "pieza",
     "exposicion": -0.7,
     "claves": [(58, (-0.55, -0.25, 6.0), (-2.7, 2.9, 3.1), 34), (82, (-0.65, -0.05, 5.8), (-2.7, 3.0, 3.1), 38)]},
    {"nombre": "Desde dentro del horno: el herrero espera", "inicio": 82, "fin": 108, "fstop": 3.5, "foco": "cabeza",
     "exposicion": -1.5,
     "claves": [(82, (-2.0, 6.0, 3.9), "cabeza", 30), (108, (-2.15, 5.85, 3.8), "cabeza", 34)]},
    {"nombre": "Saca la pieza al rojo y la lleva al yunque", "inicio": 108, "fin": 138, "fstop": 3.2, "foco": "pieza",
     "claves": [(108, (-8.6, -2.6, 6.0), "pieza", 28), (138, (-8.3, -3.4, 5.6), "pieza", 30)]},
    {"nombre": "Primer martillazo (ángulo bajo, contraluz del horno)", "inicio": 138, "fin": 163, "fstop": 3.5,
     "foco": "golpe",
     "claves": [(138, (-9.0, -8.9, 3.0), (-1.4, -2.4, 4.7), 26), (163, (-8.5, -8.3, 3.0), (-1.4, -2.4, 4.8), 26)]},
    {"nombre": "Detalle del yunque: la pieza toma forma", "inicio": 163, "fin": 180, "fstop": 2.8, "foco": "golpe",
     "exposicion": -1.0,
     "claves": [(163, (-3.0, -7.4, 4.1), "golpe", 50), (180, (-2.9, -7.2, 4.05), "golpe", 52)]},
    {"nombre": "Golpes 3 y 4 (frente derecho)", "inicio": 180, "fin": 214, "fstop": 3.5, "foco": "golpe",
     "exposicion": 0.4,
     "claves": [(180, (2.1, -9.5, 3.6), (-1.8, -2.4, 4.7), 24), (214, (1.4, -8.2, 3.6), (-1.8, -2.4, 4.8), 24)]},
    {"nombre": "Último golpe (contrapicado extremo, lateral)", "inicio": 214, "fin": 258, "fstop": 3.0, "foco": "golpe",
     "claves": [(214, (-7.9, -4.6, 2.3), (-1.4, -2.6, 5.3), 19), (258, (-7.2, -4.9, 2.4), (-1.5, -2.6, 4.9), 21)]},
    {"nombre": "Lleva la pieza al barril", "inicio": 258, "fin": 290, "fstop": 3.5, "foco": "pieza",
     "claves": [(258, (6.8, -7.6, 6.6), "pecho", 34), (290, (6.4, -6.8, 6.2), "pieza", 36)]},
    {"nombre": "Detalle: la pieza entra en el agua", "inicio": 290, "fin": 314, "fstop": 2.8, "foco": "agua",
     "claves": [(290, (5.0, -6.4, 5.6), (2.55, -2.9, 3.6), 40), (314, (4.8, -6.1, 5.4), (2.55, -2.9, 3.7), 44)]},
    {"nombre": "El vapor sube (plano medio)", "inicio": 314, "fin": 362, "fstop": 4.0, "foco": "agua",
     "claves": [(314, (6.9, -9.2, 5.2), (2.4, -2.6, 4.6), 30), (362, (6.6, -8.8, 5.4), (2.4, -2.4, 5.6), 30)]},
    {"nombre": "El resultado: giro alrededor de la hoja", "inicio": 362, "fin": 436, "fstop": 2.8, "foco": "hoja",
     "orbita": {"centro": "hoja", "radio": 7.0, "altura": -2.4, "mira_abajo": 1.1, "angulo": (-168.0, -98.0),
                "lente": 28}},
]
TEMBLOR_MANO = 0.06  # grados de «cámara en mano» siempre presente
