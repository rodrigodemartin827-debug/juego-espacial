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

# ---------------------------------------------------------------------------------------------------------------
# Fases (para el documento y la hoja de contactos)
# ---------------------------------------------------------------------------------------------------------------
FASES = None  # se rellena abajo, cuando ya se conocen los golpes

# ---------------------------------------------------------------------------------------------------------------
# Martillazos: 7, lentos y pesados. Cada uno: sube el martillo despacio, pausa arriba, cae acelerando, parada
# (hitstop), rebote y reposo. Entre golpe y golpe mira la pieza; tras el 2.º y el 4.º la levanta y le da la vuelta.
# ---------------------------------------------------------------------------------------------------------------
FUERZA_GOLPE = [0.55, 0.62, 0.7, 0.78, 0.86, 0.93, 1.0]  # escala la anticipación, las chispas y el temblor
CHISPAS_GOLPE = [70, 90, 115, 140, 170, 210, 340]
TEMBLOR_GOLPE = [0.55, 0.7, 0.85, 1.0, 1.2, 1.45, 2.2]  # grados de temblor de cámara al impactar
VUELTA_TRAS = (1, 3)  # índices de los golpes tras los que le da la vuelta a la pieza (2.º y 4.º)
SUBIDA = 20  # fotogramas que tarda en subir el martillo
PAUSA_ARRIBA = 8  # fotogramas quieto arriba (tensión)
CAIDA = 5  # fotogramas de caída (acelera hasta el impacto)
PARADA = 4  # hitstop
REBOTE = 6
REPOSO = 10  # vuelve a la postura de reposo
VUELTA = 40  # fotogramas para levantar la pieza, mirarla, darle la vuelta y volver a apoyarla
ESPERA = 4  # reposo mínimo entre golpes (mira la pieza)


def _impactos(primero):
    res, f = [], primero
    for i in range(len(FUERZA_GOLPE)):
        res.append(f)
        f += PARADA + REBOTE + REPOSO + ESPERA + SUBIDA + PAUSA_ARRIBA + CAIDA
        if i in VUELTA_TRAS:
            f += VUELTA
        if i == len(FUERZA_GOLPE) - 2:
            f += 12  # el último se hace esperar
    return res


IMPACTOS = _impactos(412)  # [400, 445, ...]: el primero a los 13,3 s
FIN_GOLPES = IMPACTOS[-1] + PARADA + REBOTE + REPOSO
B = FIN_GOLPES + 130  # llega al barril (todo el temple y el final cuelgan de aquí)
DURACION = B + 340  # fotogramas en total (unos 44 s)
CONTACTO_AGUA = B + 19  # la punta de la hoja toca el agua (medido con comprobar_choques/cinematica)

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
    (0, (-7.9, -2.4, 90), "lineal"),  # llega andando despacio
    (75, (-3.9, -1.8, 125), "lineal"),
    (100, (*PUESTO_COMPUERTA, 180), "sale"),
    (172, (*PUESTO_COMPUERTA, 180), "suave"),
    (190, (*PUESTO_HORNO, 180), "suave"),
    (306, (*PUESTO_HORNO, 180), "suave"),
    (322, (-2.55, -1.2, 176), "sale"),  # da un paso atrás con la pieza fuera del horno
    (332, (-2.0, -1.0, 150), "entra"),  # gira hacia su derecha: la pieza pasa lejos del horno
    (358, (*PUESTO_YUNQUE, -15), "sale"),
    (FIN_GOLPES + 50, (*PUESTO_YUNQUE, -15), "suave"),
    (FIN_GOLPES + 80, (0.0, -1.0, 35), "entra"),  # camina despacio al barril
    (B, (*PUESTO_BARRIL, 0), "sale"),
    (DURACION, (*PUESTO_BARRIL, 0), "suave"),
]


def _golpes(reposo, arma, tension, impacto, parada, rebote, vuelta=None):
    """Claves de un canal para los 7 golpes: valor en reposo, al armarse arriba, en tensión, en el impacto, en la
    parada y en el rebote. `vuelta`: valor mientras mira y gira la pieza (o None = reposo)."""
    res = []
    for i, f in enumerate(IMPACTOS):
        k = FUERZA_GOLPE[i]
        arriba = f - CAIDA - PAUSA_ARRIBA
        res += [
            (arriba - SUBIDA, reposo(i, k), "suave"),
            (arriba, arma(i, k), "suave"),
            (f - CAIDA, tension(i, k), "suave"),
            (f, impacto(i, k), "entra"),
            (f + PARADA, parada(i, k), "cte"),
            (f + PARADA + REBOTE, rebote(i, k), "sale"),
            (f + PARADA + REBOTE + REPOSO, reposo(i, k), "suave"),
        ]
        if i in VUELTA_TRAS and vuelta is not None:
            g = f + PARADA + REBOTE + REPOSO
            res += [(g + 10, vuelta(i, k), "suave"), (g + VUELTA - 10, vuelta(i, k), "suave"),
                    (g + VUELTA, reposo(i, k), "suave")]
    return res


# Desplazamiento del torso (local del personaje, studs): agacharse (z < 0), adelantar el cuerpo (y < 0).
TORSO_POS = [
    (0, (0, 0, 0), "suave"),
    (100, (0, 0, 0), "suave"),
    (112, (0, -0.05, -0.35), "suave"),  # se agacha a coger el asa
    (142, (0, 0.05, 0.1), "sale"),  # estira el cuerpo al subir la compuerta
    (165, (0, 0, 0), "suave"),
    (205, (0, -0.2, -0.1), "suave"),  # se inclina para meter el lingote
    (300, (0, -0.15, -0.1), "suave"),
    (322, (0, 0.05, 0), "suave"),
    (364, (0, 0, -0.1), "suave"),
    (374, (0, 0, -0.18), "suave"),  # saca el martillo de la espalda
    *_golpes(lambda i, k: (0, 0, -0.18), lambda i, k: (0, 0.05, -0.02), lambda i, k: (0, 0.06, 0.0),
             lambda i, k: (0, -0.15, -0.3 - 0.03 * i), lambda i, k: (0, -0.15, -0.3 - 0.03 * i),
             lambda i, k: (0, -0.08, -0.22), vuelta=lambda i, k: (0, -0.05, -0.12)),
    (FIN_GOLPES + 50, (0, 0, -0.15), "suave"),
    (FIN_GOLPES + 80, (0, 0, 0), "suave"),
    (B + 15, (0, -0.1, -0.15), "suave"),
    (B + 34, (0, -0.25, -0.3), "golpe"),  # hunde la pieza con decisión
    (B + 130, (0, -0.2, -0.25), "suave"),
    (B + 190, (0, 0.08, 0.05), "suave"),  # se yergue con la hoja en alto
    (DURACION, (0, 0.08, 0.05), "suave"),
]
# Rotación del torso: (inclinación hacia delante, ladeo a su izquierda, giro a su izquierda), grados.
TORSO_ROT = [
    (0, (5, 0, 0), "suave"),
    (100, (4, 0, 0), "suave"),
    (112, (9, -4, -8), "suave"),
    (142, (4, -6, -12), "sale"),
    (165, (4, 0, 0), "suave"),
    (205, (18, 2, 4), "suave"),
    (240, (16, 2, 2), "suave"),
    (300, (17, 2, 4), "suave"),
    (330, (2, 0, 10), "suave"),
    (354, (10, 0, 6), "suave"),
    (364, (12, 0, 0), "suave"),
    (374, (10, -6, -14), "suave"),
    *_golpes(lambda i, k: (14, 0, -2), lambda i, k: (-2 - 5 * k, -3, -16 - 6 * k),
             lambda i, k: (-4 - 6 * k, -3, -18 - 6 * k), lambda i, k: (24 + 7 * k, 3, 8),
             lambda i, k: (24 + 7 * k, 3, 8), lambda i, k: (18, 1, 2), vuelta=lambda i, k: (20, 2, 6)),
    (FIN_GOLPES + 50, (10, 0, 0), "suave"),
    (FIN_GOLPES + 80, (4, 0, 8), "suave"),
    (B, (8, 0, 0), "suave"),
    (B + 34, (24, 0, 2), "golpe"),
    (B + 130, (20, 0, 0), "suave"),
    (B + 190, (-4, 0, 0), "suave"),
    (B + 250, (-5, 0, 6), "suave"),  # se gira un poco para mirar la hoja
    (DURACION, (-5, 0, 2), "suave"),
]
# La cabeza (respecto al torso): (inclinación hacia abajo, ladeo, giro a su izquierda), grados.
CABEZA_ROT = [
    (0, (8, 0, 0), "suave"),
    (75, (6, 0, -25), "suave"),  # mira hacia el horno mientras llega
    (100, (10, 0, 0), "suave"),
    (146, (-12, 0, 6), "sale"),  # sigue la compuerta con la mirada
    (165, (6, 0, 0), "suave"),
    (205, (16, 0, -4), "suave"),
    (300, (14, 0, -2), "suave"),
    (322, (14, 0, -20), "suave"),
    (356, (26, 0, -6), "suave"),
    *_golpes(lambda i, k: (30, 0, -8), lambda i, k: (20, 0, -6), lambda i, k: (22, 0, -6),
             lambda i, k: (30, 0, -4), lambda i, k: (30, 0, -4), lambda i, k: (28, 0, -6),
             vuelta=lambda i, k: (36, 6, -2)),  # mira la pieza de cerca al darle la vuelta
    (FIN_GOLPES + 50, (26, 0, -6), "suave"),
    (FIN_GOLPES + 80, (14, 0, 10), "suave"),
    (B, (22, 0, 0), "suave"),
    (B + 40, (30, 0, 0), "suave"),
    (B + 130, (28, 0, 0), "suave"),
    (B + 190, (-24, 0, 0), "suave"),  # mira la hoja en alto
    (B + 250, (-26, 4, -10), "suave"),  # la inspecciona mientras la gira
    (DURACION, (-26, 0, 6), "suave"),
]

# Pies (local del personaje, x e y en studs; z = 0 es el suelo). La caminata se suma encima en cinematica.py.
PIES = [
    (0, ((0.55, 0.05), (-0.55, -0.05)), "suave"),
    (100, ((0.55, 0.05), (-0.55, -0.05)), "suave"),
    (172, ((0.6, 0.0), (-0.55, 0.0)), "suave"),
    (205, ((0.65, -0.12), (-0.6, 0.5)), "suave"),  # adelanta el pie izquierdo para llegar al fuego
    (300, ((0.65, -0.12), (-0.6, 0.5)), "suave"),
    (322, ((0.55, 0.0), (-0.55, 0.0)), "suave"),
    (364, ((0.75, -0.3), (-0.75, 0.35)), "suave"),  # postura ancha para golpear
    (FIN_GOLPES + 50, ((0.75, -0.3), (-0.75, 0.35)), "suave"),
    (FIN_GOLPES + 80, ((0.55, 0.0), (-0.55, 0.0)), "suave"),
    (B + 15, ((0.6, -0.25), (-0.6, 0.35)), "suave"),
    (DURACION, ((0.6, -0.25), (-0.6, 0.35)), "suave"),
]

# ---------------------------------------------------------------------------------------------------------------
# Brazos. Cada clave: (fotograma, objetivo, easing). Objetivos:
#   ("dir", (x, y, z)[, agarre])   el brazo apunta en esa dirección (local del personaje)
#   ("punto", nombre, herramienta) la punta de la herramienta (o la mano) llega al punto con ese nombre
# Los puntos con nombre los calcula cinematica.py (asa de la compuerta, sitio del golpe...).
# ---------------------------------------------------------------------------------------------------------------
_vueltas = []
for _i in VUELTA_TRAS:
    _g = IMPACTOS[_i] + PARADA + REBOTE + REPOSO
    _vueltas += [(_g, ("punto", "en_yunque", "tenazas"), "suave"),
                 (_g + 10, ("punto", "revisar_yunque", "tenazas"), "suave"),  # la levanta para mirarla
                 (_g + VUELTA - 10, ("punto", "revisar_yunque", "tenazas"), "suave"),
                 (_g + VUELTA, ("punto", "en_yunque", "tenazas"), "suave")]  # y la vuelve a apoyar

BRAZO_IZQ = [  # tenazas con la pieza
    (0, ("dir", (0.2, -0.3, -0.93), 150), "suave"),  # lleva las tenazas en alto, como una antorcha
    (40, ("dir", (0.2, -0.4, -0.9), 150), "suave"),
    (100, ("dir", (0.35, -0.36, -0.86), 155), "suave"),  # tenazas en vertical, a un lado, para abrir
    (172, ("dir", (0.35, -0.36, -0.86), 155), "suave"),
    (190, ("punto", "boca_horno", "tenazas"), "suave"),  # baja el lingote hacia la boca
    (212, ("punto", "en_brasas", "tenazas"), "suave"),  # lo hunde en las brasas, despacio
    (245, ("punto", "en_brasas_2", "tenazas"), "suave"),  # lo remueve en las brasas
    (275, ("punto", "en_brasas", "tenazas"), "suave"),
    (300, ("punto", "en_brasas", "tenazas"), "suave"),
    (316, ("punto", "saca_horno", "tenazas"), "sale"),
    (326, ("dir", (0.3, -0.3, -0.9), 130), "suave"),  # la recoge en alto, pegada al cuerpo, antes de girar
    (342, ("dir", (0.3, -0.3, -0.9), 130), "suave"),
    (350, ("dir", (0.05, -0.85, -0.3)), "suave"),
    (354, ("punto", "sobre_yunque", "tenazas"), "suave"),  # llega por encima y la baja
    (364, ("punto", "en_yunque", "tenazas"), "suave"),
    *_vueltas,
    (FIN_GOLPES + 50, ("punto", "en_yunque", "tenazas"), "suave"),
    (FIN_GOLPES + 62, ("punto", "alzar", "tenazas"), "sale"),  # la levanta del yunque, tumbada
    (B - 20, ("dir", (0.05, -0.8, -0.3), 75), "suave"),  # la lleva delante, por encima del barril
    (B + 18, ("punto", "sobre_agua", "tenazas"), "suave"),  # en alto, inclinada hacia el agua
    (B + 34, ("punto", "en_agua", "tenazas"), "golpe"),  # la hunde de un empujón a lo largo de la hoja
    (B + 60, ("punto", "en_agua_2", "tenazas"), "suave"),  # la agita en el agua
    (B + 82, ("punto", "en_agua", "tenazas"), "suave"),
    (B + 104, ("punto", "en_agua_2", "tenazas"), "suave"),
    (B + 126, ("punto", "en_agua", "tenazas"), "suave"),
    (B + 148, ("punto", "saca_agua", "tenazas"), "sale"),  # la saca por donde entró
    (B + 190, ("punto", "en_alto", "tenazas"), "suave"),  # la levanta en alto, despacio
    (DURACION, ("punto", "en_alto_2", "tenazas"), "suave"),
]
# Martillo: reposo, subida, pausa arriba, caída (punto «golpe»), parada y rebote.
REPOSO_MARTILLO = (-0.3, -0.45, -0.84)
_brazo_der = [
    (0, ("dir", (-0.1, 0.25, -0.96)), "suave"),
    (20, ("dir", (-0.1, -0.25, -0.96)), "suave"),  # balanceo al andar
    (40, ("dir", (-0.1, 0.25, -0.96)), "suave"),
    (60, ("dir", (-0.1, -0.2, -0.97)), "suave"),
    (80, ("dir", (-0.1, 0.2, -0.97)), "suave"),
    (100, ("dir", (-0.1, 0.0, -1.0)), "suave"),
    (106, ("dir", (-0.1, -0.7, -0.55)), "suave"),  # llega al asa por delante, sin rozar el alféizar
    (112, ("punto", "asa", "mano"), "suave"),
    (138, ("punto", "asa", "mano"), "suave"),  # sube la compuerta con calma y la suelta: sigue subiendo sola
    (148, ("dir", (-0.2, -0.15, 0.97)), "sale"),
    (166, ("dir", (-0.15, 0.05, -0.98)), "suave"),
    (300, ("dir", (-0.15, 0.05, -0.98)), "suave"),
    (322, ("dir", (-0.12, 0.05, -0.99)), "suave"),  # brazo pegado al cuerpo al girar (pasa junto al yunque)
    (360, ("dir", (-0.25, 0.0, -0.97)), "suave"),
    (374, ("punto", "cinto", "mano"), "suave"),  # coge el martillo de la espalda
    *_golpes(lambda i, k: ("dir", REPOSO_MARTILLO),
             lambda i, k: ("dir", (-0.12, 0.25 + 0.35 * k, 0.95)),  # arriba
             lambda i, k: ("dir", (-0.12, 0.32 + 0.4 * k, 0.93)),  # tensión, un poco más atrás
             lambda i, k: ("punto", "golpe", "martillo"),  # IMPACTO
             lambda i, k: ("punto", "golpe", "martillo"),  # parada
             lambda i, k: ("dir", (-0.12, -0.8, 0.25))),  # rebote
    (FIN_GOLPES + 30, ("dir", (-0.4, -0.25, -0.88)), "suave"),
    (FIN_GOLPES + 46, ("punto", "cinto", "mano"), "suave"),  # devuelve el martillo a la espalda
    (FIN_GOLPES + 56, ("dir", (-0.1, 0.0, -1.0)), "suave"),
    (FIN_GOLPES + 76, ("dir", (-0.1, 0.25, -0.96)), "suave"),
    (FIN_GOLPES + 96, ("dir", (-0.1, -0.25, -0.96)), "suave"),
    (B, ("dir", (-0.12, 0.0, -0.99)), "suave"),
    (B + 34, ("dir", (-0.3, -0.3, -0.9)), "suave"),  # equilibrio al hundir la pieza
    (B + 140, ("dir", (-0.3, -0.25, -0.92)), "suave"),
    (B + 190, ("dir", (-0.15, 0.05, -0.98)), "suave"),
    (DURACION, ("dir", (-0.15, 0.05, -0.98)), "suave"),
]
BRAZO_DER = _brazo_der

# Herramientas en la mano: ángulo de agarre (grados entre el brazo y la herramienta, hacia delante).
AGARRE = {"tenazas": 30.0, "martillo": 45.0}
MARTILLO_EN_MANO = (374, FIN_GOLPES + 46)  # entre estos fotogramas el martillo va en la mano; fuera, a la espalda

# Orientación de la pieza (ver cinematica.orientacion_pieza). Entre claves gira suavemente.
PIEZA_ORIENTACION = [
    (0, "linea", "suave"),
    (172, "linea", "suave"),
    (196, "tumbada", "suave"),
    (B + 8, "tumbada", "suave"),
    (B + 20, "temple", "suave"),  # sobre el barril la inclina hacia el agua
    (B + 148, "temple", "suave"),
    (B + 190, "arriba", "suave"),  # fuera del agua, la levanta punta arriba, despacio
    (DURACION, "arriba", "suave"),
]
# Giro de la pieza sobre su propio eje (grados): las vueltas en el yunque y la inspección final.
_giro = [(0, 0.0, "suave")]
for _n, _i in enumerate(VUELTA_TRAS):
    _g = IMPACTOS[_i] + PARADA + REBOTE + REPOSO
    _giro += [(_g + 14, 180.0 * _n, "suave"), (_g + VUELTA - 14, 180.0 * (_n + 1), "suave")]
_giro += [(B + 195, 360.0, "suave"), (B + 240, 360.0 + 110.0, "suave"), (B + 280, 360.0 + 170.0, "suave"),
          (DURACION, 360.0 + 180.0, "suave")]
PIEZA_GIRO = _giro

# Compuerta del horno: cuánto sube (studs). La mano la sube con calma y la suelta; sigue sola hasta arriba.
COMPUERTA = [(0, 0.0, "suave"), (114, 0.0, "suave"), (138, 1.6, "suave"), (152, 3.25, "sale"),
             (DURACION, 3.25, "suave")]

# Forma de la pieza: 0 = lingote ... 5 = hoja terminada. Cada golpe la avanza 5/7 de etapa en 2 fotogramas.
ETAPA = [(0, 0.0, "suave")]
for _i, _f in enumerate(IMPACTOS):
    ETAPA += [(_f - 1, 5.0 * _i / len(IMPACTOS), "cte"), (_f + 1, 5.0 * (_i + 1) / len(IMPACTOS), "golpe")]
ETAPA += [(DURACION, 5.0, "suave")]

# Calor de la pieza: temperatura (K) y fuerza de emisión. Se enfría con cada golpe y se apaga en el agua poco a poco.
TEMPERATURA = [
    (0, 700.0, "suave"),
    (205, 760.0, "suave"),
    (250, 1300.0, "sale"),  # el primer plano: se ve cómo se pone naranja
    (290, 1650.0, "suave"),
    (316, 1900.0, "suave"),  # blanco-naranja al sacarla
    *[(f, 1780.0 - 90.0 * i, "suave") for i, f in enumerate(IMPACTOS)],
    (CONTACTO_AGUA - 2, 1110.0, "suave"),
    (CONTACTO_AGUA + 30, 1000.0, "sale"),
    (CONTACTO_AGUA + 95, 700.0, "suave"),
    (DURACION, 700.0, "suave"),
]
BRILLO = [
    (0, 0.0, "suave"),
    (205, 0.0, "suave"),
    (250, 2.8, "sale"),
    (290, 5.2, "suave"),
    (316, 8.6, "suave"),
    *[(f, 6.8 - 0.75 * i, "suave") for i, f in enumerate(IMPACTOS)],
    (CONTACTO_AGUA - 2, 1.4, "suave"),
    (CONTACTO_AGUA + 25, 0.45, "sale"),
    (CONTACTO_AGUA + 85, 0.0, "suave"),
    (DURACION, 0.0, "suave"),
]
REALCE_COLOR = 500.0  # K que se suman a la temperatura solo para el color (ver cinematica.color_pieza)
# Pulido: 0 = calamina negra, 1 = acero gris pulido.
PULIDO = [(0, 0.0, "suave"), (CONTACTO_AGUA + 5, 0.0, "suave"), (CONTACTO_AGUA + 95, 0.7, "suave"),
          (B + 190, 1.0, "suave"), (DURACION, 1.0, "suave")]

# Destello del filo: recorre el filo de la base a la punta.
DESTELLO = (B + 238, B + 262)

# ---------------------------------------------------------------------------------------------------------------
# Luces
# ---------------------------------------------------------------------------------------------------------------
LUZ_HORNO = 1300.0  # W, dentro de la cámara del horno (la compuerta la tapa hasta que se abre)
LUZ_BOCA = [(0, 0.0, "suave"), (118, 0.0, "suave"), (152, 450.0, "sale"), (DURACION, 450.0, "suave")]
LUZ_PIEZA_POR_BRILLO = 100.0  # W de la luz pegada a la pieza por cada unidad de brillo
LUZ_CONTRA = 900.0  # contraluz azul frío (luna)
EXPOSICION = [(0, -9.0, "suave"), (14, 0.5, "sale"), (DURACION - 54, 0.5, "suave"), (DURACION - 1, -12.0, "entra")]

# ---------------------------------------------------------------------------------------------------------------
# Partículas
# ---------------------------------------------------------------------------------------------------------------
ASCUAS_HORNO = {"inicio": -40, "fin": DURACION, "cantidad": 1400, "vida": 70}
ESTALLIDO_COMPUERTA = {"inicio": 126, "fin": 140, "cantidad": 170, "vida": 28}
CHISPAS_SACAR = {"inicio": 310, "fin": 318, "cantidad": 90, "vida": 20}
# Vapor lento y denso: más bocanadas, más largas y más espesas
VAPOR = {"inicio": CONTACTO_AGUA, "bocanadas": 16, "duracion": 120, "espaciado": 6.0, "densidad": 2.3,
         "fin": B + 162}  # fin: ya no queda vapor
BURBUJAS = {"inicio": CONTACTO_AGUA, "fin": CONTACTO_AGUA + 80, "cantidad": 420, "vida": 12}
OLA_AGUA = [(0, 0.0, "suave"), (CONTACTO_AGUA - 1, 0.0, "cte"), (CONTACTO_AGUA + 2, 0.11, "golpe"),
            (CONTACTO_AGUA + 60, 0.04, "suave"), (CONTACTO_AGUA + 110, 0.0, "suave"), (DURACION, 0.0, "suave")]

# ---------------------------------------------------------------------------------------------------------------
# Cámara: planos. Cada plano: inicio, fin, claves [(fotograma, posición, mira_a, lente_mm)], f-stop, foco y los
# sujetos que tienen que verse (los comprueba comprobar_planos.py). mira_a y foco pueden ser un punto o el nombre
# de un punto que se calcula (pieza, cabeza, golpe...). Entre planos hay corte seco.
# ---------------------------------------------------------------------------------------------------------------
PLANOS = [
    {"nombre": "Llegada al horno (plano general, bajo)", "inicio": 0, "fin": 100, "fstop": 4.0, "foco": "cabeza",
     "exposicion": 1.0, "sujetos": ["pecho", "cabeza"],
     "claves": [(0, (-13.5, -13.0, 2.0), (-6.0, -1.2, 5.0), 24), (100, (-10.8, -12.3, 2.3), (-3.0, -0.5, 5.2), 27)]},
    {"nombre": "Abre la compuerta (por encima del hombro)", "inicio": 100, "fin": 172, "fstop": 3.2,
     "foco": "compuerta", "sujetos": ["cabeza"],
     "claves": [(100, (3.4, -6.4, 5.6), (-2.4, 1.0, 3.9), 30), (172, (2.6, -5.4, 5.2), (-2.5, 1.0, 3.7), 34)]},
    {"nombre": "Detalle del fuego: el lingote se hunde en las brasas", "inicio": 172, "fin": 250, "fstop": 2.4,
     "foco": "pieza", "exposicion": -1.4, "sujetos": ["pieza"],
     "claves": [(172, (-0.55, -0.25, 6.0), (-2.7, 2.9, 3.1), 34), (250, (-0.7, 0.05, 5.7), (-2.7, 3.0, 3.1), 42)]},
    {"nombre": "Desde dentro del horno: el herrero espera", "inicio": 250, "fin": 318, "fstop": 3.5, "foco": "cabeza",
     "exposicion": -2.2, "sujetos": ["cabeza"],
     "claves": [(250, (-2.0, 6.0, 3.9), "cabeza", 30), (318, (-2.2, 5.8, 3.75), "cabeza", 37)]},
    {"nombre": "Saca la pieza al rojo y la lleva al yunque", "inicio": 318, "fin": 380, "fstop": 3.2, "foco": "pieza",
     "sujetos": ["pieza"],
     "claves": [(318, (-8.6, -2.6, 6.0), "pieza", 28), (380, (-8.3, -3.4, 5.6), "pieza", 30)]},
    {"nombre": "Golpes 1 y 2 (ángulo bajo, contraluz del horno)", "inicio": 380, "fin": IMPACTOS[1] + 20, "fstop": 3.5,
     "foco": "golpe", "sujetos": ["cabeza", "golpe"],
     "claves": [(380, (-9.0, -8.9, 3.0), (-1.4, -2.4, 4.7), 26), (IMPACTOS[1] + 20, (-8.2, -8.0, 3.0), (-1.4, -2.4, 4.8), 27)]},
    {"nombre": "Detalle: le da la vuelta y 3.er golpe", "inicio": IMPACTOS[1] + 20, "fin": IMPACTOS[2] + 20, "fstop": 2.8, "foco": "golpe",
     "exposicion": -2.6, "sujetos": ["golpe"],
     "claves": [(IMPACTOS[1] + 20, (-3.0, -7.4, 4.1), "golpe", 48), (IMPACTOS[2] + 20, (-2.85, -7.1, 4.0), "golpe", 52)]},
    {"nombre": "Golpes 4 y 5 (frente derecho)", "inicio": IMPACTOS[2] + 20, "fin": IMPACTOS[4] + 20, "fstop": 3.5, "foco": "golpe",
     "exposicion": 0.4, "sujetos": ["cabeza", "golpe"],
     "claves": [(IMPACTOS[2] + 20, (2.1, -9.5, 3.6), (-1.8, -2.4, 4.7), 24), (IMPACTOS[4] + 20, (1.2, -8.0, 3.6), (-1.8, -2.4, 4.8), 25)]},
    {"nombre": "Golpe 6 (frente derecho, cerca)", "inicio": IMPACTOS[4] + 20, "fin": IMPACTOS[5] + 24, "fstop": 3.2, "foco": "golpe",
     "sujetos": ["cabeza", "golpe"],
     "claves": [(IMPACTOS[4] + 20, (2.3, -7.6, 3.6), (-1.8, -2.4, 4.7), 24), (IMPACTOS[5] + 24, (1.9, -7.1, 3.5), (-1.8, -2.4, 4.8), 25)]},
    {"nombre": "Último golpe (contrapicado extremo, lateral)", "inicio": IMPACTOS[5] + 24, "fin": FIN_GOLPES + 50, "fstop": 3.0, "foco": "golpe",
     "sujetos": ["cabeza"],
     "claves": [(IMPACTOS[5] + 24, (-7.9, -4.6, 2.3), (-1.4, -2.6, 5.3), 19), (FIN_GOLPES + 50, (-7.2, -4.9, 2.4), (-1.5, -2.6, 4.9), 21)]},
    {"nombre": "Lleva la pieza al barril", "inicio": FIN_GOLPES + 50, "fin": B + 8, "fstop": 3.5, "foco": "pieza",
     "sujetos": ["pieza"],
     "claves": [(FIN_GOLPES + 50, (6.8, -7.6, 6.6), "pecho", 34), (B + 8, (6.4, -6.8, 6.2), "pieza", 36)]},
    {"nombre": "Detalle: la pieza entra en el agua", "inicio": B + 8, "fin": B + 62, "fstop": 2.8, "foco": "agua",
     "sujetos": ["agua"],
     "claves": [(B + 8, (5.0, -6.4, 5.6), (2.55, -2.9, 3.6), 40), (B + 62, (4.7, -6.0, 5.3), (2.55, -2.9, 3.7), 46)]},
    {"nombre": "El vapor sube lento (plano medio)", "inicio": B + 62, "fin": B + 162, "fstop": 4.0, "foco": "agua",
     "sujetos": ["cabeza"],
     "claves": [(B + 62, (6.9, -9.2, 5.2), (2.4, -2.6, 4.6), 30), (B + 162, (6.5, -8.6, 5.6), (2.4, -2.4, 6.0), 30)]},
    {"nombre": "El resultado: la inspecciona; giro lento alrededor de la hoja", "inicio": B + 162, "fin": DURACION,
     "fstop": 2.8, "foco": "hoja", "exposicion": 0.7, "sujetos": ["hoja"],
     "orbita": {"centro": "hoja", "radio": 7.0, "altura": -2.4, "mira_abajo": 1.1, "angulo": (-170.0, -105.0),
                "lente": 28}},
]
TEMBLOR_MANO = 0.06  # grados de «cámara en mano» siempre presente

FASES = [
    (0, 318, "1. El horno"),
    (318, FIN_GOLPES + 50, "2. El yunque"),
    (FIN_GOLPES + 50, B + 162, "3. El temple"),
    (B + 162, DURACION, "4. El resultado"),
]
assert DESTELLO[1] < DURACION - 54, "el final no cabe: alarga DURACION"
