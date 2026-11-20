"""
Anatomía del Dragón Leviatán: posiciones de las articulaciones (pivotes de los Motor6D) y masas del cuerpo.

Sistema de coordenadas (Blender, en studs): Z arriba, el dragón mira a -Y. Su izquierda es +X y su derecha -X.
El suelo está en Z = 0. Pose de reposo = pose de combate: agazapado, pecho bajo, cabeza baja entre los hombros,
alas abiertas al 70 % hacia arriba y atrás y la cola estirada hacia atrás con el hacha algo levantada.

Todo lo que se ajusta (medidas, posiciones) está aquí arriba, separado del código que construye la malla.
"""

import numpy as np

import dragon_sdf as s

V = np.array

# --------------------------------------------------------------------------------------------------------------
# Articulaciones (pivotes). Lado izquierdo (+X); el derecho es el espejo en X.
# --------------------------------------------------------------------------------------------------------------

TORSO = V([0.0, 0.5, 9.6])  # centro de masa, pieza raíz

# Cuello en S: sube desde el pecho, se arquea y baja hasta dejar la cabeza a la altura de los hombros.
CUELLO = [V([0.0, -8.4, 11.2]), V([0.0, -12.0, 14.6]), V([0.0, -16.5, 14.4]), V([0.0, -19.6, 11.0])]
R_CUELLO = [2.45, 2.2, 1.95, 1.7]

# Cabeza: pivote en el cóndilo occipital (= CUELLO[3]). Mandíbula: bisagra detrás y debajo del ojo.
CABEZA = CUELLO[3]
MANDIBULA = V([0.0, -21.7, 8.75])
PUNTA_HOCICO = V([0.0, -30.3, 7.9])
OJO = V([2.1, -23.6, 10.75])  # centro del globo ocular izquierdo
R_OJO = 0.75  # 1,5 studs de diámetro

# Cola: sale del torso como un puente, baja un poco y la punta (hacha) se levanta.
COLA = [V([0.0, 9.2, 10.6]), V([0.5, 16.2, 8.6]), V([1.9, 23.0, 6.6]), V([3.0, 29.0, 8.3])]
R_COLA = [2.45, 1.9, 1.35, 0.85]
HACHA = V([3.6, 31.6, 9.3])  # centro de la hoja del hacha

# Pata delantera: hombro, codo (atrás y fuera: agazapado), muñeca, y el pie apoyado.
DEL_HOMBRO = V([5.2, -6.2, 8.2])
DEL_CODO = V([7.7, -4.2, 4.5])
DEL_MUNECA = V([8.3, -7.5, 1.95])
DEL_PIE = V([8.5, -8.7, 0.8])

# Pata trasera digitígrada: cadera, rodilla (adelante), tobillo (atrás), bola del pie.
TRAS_CADERA = V([4.9, 7.0, 10.1])
TRAS_RODILLA = V([7.4, 3.6, 6.6])
TRAS_TOBILLO = V([7.8, 9.8, 3.8])
TRAS_PIE = V([8.0, 6.6, 0.9])

# Ala (izquierda): hombro, codo, muñeca y puntas de los 4 dedos. Abierta al 70 %, hacia arriba y atrás.
ALA_HOMBRO = V([4.0, -4.6, 13.4])
ALA_CODO = V([9.8, -1.0, 18.6])
ALA_MUNECA = V([14.6, -1.6, 23.6])
# (punta, nudillo intermedio) de cada dedo; el 1 es el borde de ataque, el 4 el de salida.
ALA_DEDOS = [
    (V([20.0, -1.0, 35.0]), V([17.0, -1.8, 29.2])),
    (V([25.0, 6.5, 28.0]), V([19.6, 2.0, 26.0])),
    (V([24.0, 14.5, 17.5]), V([19.6, 6.4, 20.6])),
    (V([16.5, 18.5, 9.5]), V([15.8, 8.6, 16.8])),
]
ALA_ANCLA_CUERPO = V([5.0, 9.0, 12.4])  # donde la membrana se une al flanco (cerca de la cadera)
R_HUMERO = (0.78, 0.62)
R_RADIO = (0.62, 0.48)
R_DEDO = (0.42, 0.18)


def espejo(p):
    return V([-p[0], p[1], p[2]])


# --------------------------------------------------------------------------------------------------------------
# Campos de cada pieza (masas). Cada función devuelve el campo de distancia de esa pieza sin detalle.
# --------------------------------------------------------------------------------------------------------------


def campo_torso(P):
    d = s.capsula_eliptica(P, (0, -5.4, 8.7), (0, 1.0, 9.7), 5.7, 4.9, 5.3, 4.6)  # pecho
    d = s.smin(d, s.capsula_eliptica(P, (0, 1.0, 10.0), (0, 6.4, 10.6), 5.0, 4.1, 4.2, 3.5), 1.2)  # vientre y cadera
    d = s.smin(d, s.elipsoide(P, (0, -6.6, 6.2), (3.2, 3.6, 2.0)), 1.0)  # quilla del esternón (pecho colosal)
    for x in (3.3, -3.3):
        d = s.smin(d, s.elipsoide(P, (x * 0.95, -8.6, 7.9), (2.0, 1.8, 2.7)), 0.6)  # pectorales
        d = s.smin(d, s.elipsoide(P, (x * 1.42, -6.0, 9.2), (1.6, 2.6, 2.8)), 0.6)  # escápula (pata delantera)
        d = s.smin(d, s.elipsoide(P, (x * 1.3, 6.9, 10.4), (2.0, 3.2, 3.0)), 0.7)  # ancas
        # Montañas musculares de las alas: crestas alargadas hacia el húmero, no cúpulas.
        k = 1 if x > 0 else -1
        d = s.smin(d, s.cono_redondeado(P, (k * 1.4, -6.4, 13.2), (k * 4.3, -4.4, 15.3), 1.6, 1.25), 0.6)
        d = s.smin(d, s.cono_redondeado(P, (k * 1.6, -2.0, 13.6), (k * 4.0, -4.2, 14.9), 1.2, 1.1), 0.5)
    d = s.smin(d, s.tubo(P, [V([0, -8.0, 13.0]), V([0, 0.0, 14.1]), V([0, 8.6, 13.9])], [1.3, 1.5, 1.2]), 0.8)
    return d


def campo_cuello(P, i):
    """Tramo i (0 base, 1 medio, 2 superior) del cuello: sección algo más alta que ancha."""
    a, b = CUELLO[i], CUELLO[i + 1]
    ra, rb = R_CUELLO[i], R_CUELLO[i + 1]
    d = s.capsula_eliptica(P, a, b, ra, ra * 1.12, rb, rb * 1.12)
    # Papada blindada bajo la garganta (pliegues).
    if i >= 1:
        m = (a + b) / 2 + V([0, 0, -rb * 0.75])
        d = s.smin(d, s.elipsoide(P, m, (rb * 0.8, 1.9, rb * 0.55)), 0.6)
    return d


def _plano(P, p, n):
    return s.semiespacio(P, p, n)


def campo_cabeza(P):
    """
    Cráneo de depredador: hocico de cuña (techo plano, lados inclinados), ceja ósea que baja hacia el hocico
    (ceño de furia) y pómulo de hueso. Fundidos pequeños para que haya aristas y no parezca un peluche.
    """
    d = s.elipsoide(P, (0, -21.5, 11.2), (2.75, 2.7, 2.15))  # bóveda del cráneo
    hoc = s.capsula_eliptica(P, (0, -22.4, 10.5), (0, -29.9, 8.75), 2.75, 1.9, 1.95, 1.2)
    # cuña: techo plano que baja hacia la punta, flancos inclinados hacia dentro por arriba
    hoc = s.smax(hoc, _plano(P, (0, -26.0, 10.75), (0, 0.17, 1)), 0.3)
    hoc = s.smax(hoc, _plano(P, (0, -31.0, 8.6), (0, -1, 0.45)), 0.35)  # punta en cuña, no en bola
    for k in (1, -1):
        hoc = s.smax(hoc, _plano(P, (k * 2.25, -26.0, 9.6), (k, -0.08, 0.55)), 0.35)
    d = s.smin(d, hoc, 0.6)
    for k in (1, -1):
        # ceja ósea: arista que baja de la sien hacia el hocico, por encima del ojo
        d = s.smin(d, s.cono_redondeado(P, (k * 2.2, -21.2, 12.6), (k * 2.85, -24.8, 11.45), 0.7, 0.5), 0.35)
        # pómulo (arco yugal): barra de hueso bajo el ojo hasta la bisagra de la mandíbula
        d = s.smin(d, s.cono_redondeado(P, (k * 2.8, -20.7, 9.7), (k * 2.4, -25.6, 9.5), 0.6, 0.3), 0.6)
        # crestas nasales
        d = s.smin(d, s.cono_redondeado(P, (k * 1.25, -24.4, 11.2), (k * 0.9, -29.3, 9.85), 0.36, 0.26), 0.2)
        # protuberancia temporal (músculo de la mordida) detrás del ojo
        d = s.smin(d, s.elipsoide(P, (k * 2.5, -20.6, 11.2), (0.9, 1.3, 1.1)), 0.35)
    return d


def campo_mandibula(P):
    d = s.capsula_eliptica(P, (0, -21.0, 8.1), (0, -29.4, 7.35), 2.45, 1.6, 1.7, 0.95)
    d = s.smax(d, _plano(P, (0, -25, 6.55), (0, -0.09, -1)), 0.3)  # panza plana de la mandíbula
    d = s.smax(d, _plano(P, (0, -30.3, 7.4), (0, -1, -0.35)), 0.3)  # barbilla angulosa
    d = s.smin(d, s.elipsoide(P, (0, -22.6, 7.4), (1.9, 2.4, 1.15)), 0.6)  # garganta
    for x in (1, -1):
        d = s.smin(d, s.elipsoide(P, (x * 2.2, -21.3, 8.35), (0.85, 1.5, 1.15)), 0.35)  # masetero
        # arista ósea a lo largo de la mandíbula
        d = s.smin(d, s.cono_redondeado(P, (x * 2.25, -21.8, 7.6), (x * 1.6, -28.6, 7.2), 0.32, 0.22), 0.2)
    return d


def campo_pata_del(P, lado, tramo):
    k = 1 if lado == "Izq" else -1
    h, c, m, pie = (_x(DEL_HOMBRO, k), _x(DEL_CODO, k), _x(DEL_MUNECA, k), _x(DEL_PIE, k))
    if tramo == "Muslo":
        d = s.cono_redondeado(P, h, c, 2.35, 1.55)
        d = s.smin(d, s.elipsoide(P, h * 0.55 + c * 0.45 + V([0, 0.5, 0]), (2.0, 2.1, 2.6)), 0.9)  # bíceps
        return d
    d = s.cono_redondeado(P, c, m, 1.55, 1.05)
    d = s.smin(d, s.elipsoide(P, c * 0.6 + m * 0.4, (1.5, 1.6, 2.0)), 0.7)  # antebrazo
    d = s.smin(d, s.elipsoide(P, pie, (1.25, 1.35, 0.75)), 0.6)  # palma
    for dx, dy in ((-0.95, -1.55), (-0.3, -1.95), (0.35, -1.9), (0.95, -1.45)):  # 4 dedos hacia delante
        punta = pie + V([dx * k, dy, -0.35])
        d = s.smin(d, s.cono_redondeado(P, pie + V([dx * k * 0.5, -0.4, 0.05]), punta, 0.42, 0.3), 0.3)
    d = s.smin(d, s.cono_redondeado(P, m + V([0, 0.4, -0.6]), pie + V([0, 1.3, -0.25]), 0.35, 0.25), 0.3)  # espolón
    return d


def campo_pata_tras(P, lado, tramo):
    k = 1 if lado == "Izq" else -1
    ca, ro, to, pie = (_x(TRAS_CADERA, k), _x(TRAS_RODILLA, k), _x(TRAS_TOBILLO, k), _x(TRAS_PIE, k))
    if tramo == "Muslo":
        d = s.cono_redondeado(P, ca, ro, 2.7, 1.75)
        d = s.smin(d, s.elipsoide(P, ca * 0.5 + ro * 0.5 + V([0.25 * k, -0.6, 0.3]), (2.3, 2.7, 3.2),
                                  _rot_x(0.75)), 1.1)  # cuádriceps
        d = s.smin(d, s.elipsoide(P, ca * 0.6 + ro * 0.4 + V([0, 1.2, -0.2]), (1.5, 1.6, 2.2)), 0.9)  # isquios
        return d
    d = s.cono_redondeado(P, ro, to, 1.65, 1.0)
    d = s.smin(d, s.elipsoide(P, ro * 0.62 + to * 0.38 + V([0, 0.45, 0.25]), (1.3, 1.65, 1.8), _rot_x(-0.6)),
               0.7)  # gemelo
    d = s.smin(d, s.cono_redondeado(P, to, pie, 1.0, 0.85), 0.5)  # metatarso
    d = s.smin(d, s.elipsoide(P, pie + V([0, -0.3, -0.15]), (1.0, 1.25, 0.65)), 0.5)
    for dx, dy in ((-0.75, -1.95), (0.0, -2.35), (0.75, -1.9)):  # 3 dedos
        punta = pie + V([dx * k, dy, -0.45])
        d = s.smin(d, s.cono_redondeado(P, pie + V([dx * k * 0.4, -0.5, 0.0]), punta, 0.48, 0.34), 0.3)
    return d


def campo_cola(P, i):
    a, b = COLA[i], COLA[i + 1]
    ra, rb = R_COLA[i], R_COLA[i + 1]
    d = s.capsula_eliptica(P, a, b, ra * 0.92, ra * 1.08, rb * 0.9, rb * 1.1)
    if i == 2:
        # Raíz del hacha: el hueso se ensancha antes de la hoja.
        d = s.smin(d, s.elipsoide(P, HACHA + V([-0.15, -1.2, -0.25]), (0.75, 1.6, 0.95)), 0.5)
    return d


# --------------------------------------------------------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------------------------------------------------------


def _x(p, k):
    return V([p[0] * k, p[1], p[2]])


def _rot_x(a):
    c, si = np.cos(a), np.sin(a)
    return V([[1, 0, 0], [0, c, -si], [0, si, c]])


def _rot_z(a):
    c, si = np.cos(a), np.sin(a)
    return V([[c, -si, 0], [si, c, 0], [0, 0, 1]])
