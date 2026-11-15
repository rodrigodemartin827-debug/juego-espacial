"""
Cinemática de la forja: convierte los datos de linea_tiempo.py en movimiento, fotograma a fotograma.

  * Maniquí R6: cinemática directa propia con los pivotes de rig_r6 (los mismos del Motor6D de Roblox). Brazos y
    piernas son piezas rígidas: los brazos «apuntan» (a una dirección o a que la punta de su herramienta llegue a un
    punto) y las piernas apuntan a sus pies, con la altura del torso calculada para que pisen el suelo.
  * Herramientas: las tenazas van siempre en la mano izquierda con la pieza mordida; el martillo pasa del cinto a la
    mano derecha y vuelve al cinto.
  * Pieza: shape keys de lingote a hoja, temperatura y brillo de cuerpo negro, pulido tras el temple.
  * Cámara: planos con corte seco, profundidad de campo, temblor en cada martillazo y una órbita final.

evaluar(f) devuelve el estado completo del fotograma f (matrices en el mundo de Blender, en studs). Lo usan el
horneado en Blender (hornear) y el documento para Roblox (documento.py).
"""

import math
import os
import sys

from mathutils import Euler, Matrix, Quaternion, Vector

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(0, os.path.join(AQUI, "..", "..", "herramientas"))  # animaciones/herramientas (rig_r6)

import escena as es  # noqa: E402
import linea_tiempo as lt  # noqa: E402
import rig_r6 as r6  # noqa: E402

# ---------------------------------------------------------------------------------------------------------------
# Easing y muestreo
# ---------------------------------------------------------------------------------------------------------------


def _rebote(t):
    c1 = 2.2
    return 1 + (c1 + 1) * (t - 1) ** 3 + c1 * (t - 1) ** 2


EASING = {
    "suave": lambda t: t * t * t * (t * (6 * t - 15) + 10),
    "entra": lambda t: t**3,
    "sale": lambda t: 1 - (1 - t) ** 3,
    "golpe": lambda t: 1 - (1 - t) ** 5,
    "rebote": _rebote,
    "lineal": lambda t: t,
    "cte": lambda t: 1.0 if t >= 1 else 0.0,
}


def _mezclar(a, b, k):
    if isinstance(a, (tuple, list)):
        return tuple(_mezclar(x, y, k) for x, y in zip(a, b))
    return a + (b - a) * k


def tramo(claves, f):
    """(clave anterior, clave siguiente, avance con easing) para el fotograma f."""
    if f <= claves[0][0]:
        return claves[0], claves[0], 0.0
    for c0, c1 in zip(claves, claves[1:]):
        if c0[0] <= f <= c1[0]:
            t = (f - c0[0]) / (c1[0] - c0[0]) if c1[0] > c0[0] else 1.0
            return c0, c1, EASING[c1[2]](t)
    return claves[-1], claves[-1], 0.0


def muestrear(claves, f):
    c0, c1, k = tramo(claves, f)
    return _mezclar(c0[1], c1[1], k)


# ---------------------------------------------------------------------------------------------------------------
# Raíz del personaje y caminata
# ---------------------------------------------------------------------------------------------------------------


def raiz(f):
    x, y, giro = muestrear(lt.RAIZ, f)
    return x, y, giro


def matriz_raiz(f):
    x, y, giro = raiz(f)
    return Matrix.Translation((x, y, es.ALTO_SUELO)) @ Matrix.Rotation(math.radians(giro), 4, "Z")


_RECORRIDO = {}


def recorrido(f):
    """Distancia «andada» acumulada hasta f (traslación + giro), para la fase del paso. Y la velocidad."""
    if not _RECORRIDO:
        total, ant = 0.0, raiz(0)
        for i in range(-60, lt.DURACION + 60):
            r = raiz(i)
            d = math.hypot(r[0] - ant[0], r[1] - ant[1]) + abs(math.radians(r[2] - ant[2])) * 0.55
            total += d
            _RECORRIDO[i] = (total, d)
            ant = r
    fi = max(-60, min(lt.DURACION + 59, int(math.floor(f))))
    return _RECORRIDO[fi]


ZANCADA = 1.25  # studs por medio ciclo


def pasos(f):
    """Desplazamiento de cada pie por la caminata: ((dy, dz) izq., (dy, dz) der.)."""
    total, vel = recorrido(f)
    # suaviza la velocidad para que el paso entre y salga sin saltos
    vel = sum(recorrido(f + k)[1] for k in range(-3, 4)) / 7
    s = min(1.0, vel / 0.055)  # paso completo ya andando despacio (~1,6 studs/s)
    fase = total / ZANCADA * math.pi
    a = 0.5 * s
    izq = (-a * math.sin(fase), 0.32 * s * max(0.0, math.cos(fase)))
    der = (a * math.sin(fase), 0.32 * s * max(0.0, -math.cos(fase)))
    return izq, der, s, fase


# ---------------------------------------------------------------------------------------------------------------
# Pose R6 (local del personaje, studs)
# ---------------------------------------------------------------------------------------------------------------


class Pose:
    def __init__(self):
        self.q = {b: Quaternion() for b in r6.ARTICULACIONES}
        self.loc = {b: Vector((0, 0, 0)) for b in r6.ARTICULACIONES}

    def mundo(self, hueso):
        """(posición de la articulación, rotación) en el sistema local del personaje."""
        padre = r6.PADRE[hueso]
        if padre is None:
            return Vector(r6.ARTICULACIONES[hueso]) + self.loc[hueso], self.q[hueso].copy()
        pp, pr = self.mundo(padre)
        desfase = Vector(r6.ARTICULACIONES[hueso]) - Vector(r6.ARTICULACIONES[padre])
        return pp + pr @ (desfase + self.loc[hueso]), pr @ self.q[hueso]

    def matriz(self, hueso):
        p, q = self.mundo(hueso)
        return Matrix.Translation(p) @ q.to_matrix().to_4x4()

    def poner_rot(self, hueso, q_local_personaje):
        padre = r6.PADRE[hueso]
        q_padre = self.mundo(padre)[1] if padre else Quaternion()
        self.q[hueso] = q_padre.inverted() @ q_local_personaje


def _euler(g):
    return Euler([math.radians(v) for v in g], "XYZ").to_quaternion()


ABAJO = Vector((0, 0, -1))
EJE_X = Vector((1, 0, 0))

# Herramientas en el sistema del brazo (el brazo cuelga hacia -Z; delante es -Y).
MANO = Vector((0, 0, -1.45))


def agarre(herramienta, angulo=None):
    """Matriz de la herramienta en el sistema del brazo: en la mano, girada `angulo` grados hacia delante."""
    a = lt.AGARRE[herramienta] if angulo is None else angulo
    return Matrix.Translation(MANO) @ Matrix.Rotation(math.radians(-a), 4, "X")


PUNTA_TENAZAS = Matrix.Translation((0, 0, -es.LARGO_TENAZAS))
BOCA_MARTILLO = Vector((0, 0.36, -1.25))  # cara de golpeo, en el sistema del martillo
LIMITES_AGARRE = {"tenazas": (0.0, 125.0), "martillo": (5.0, 125.0)}


def punto_herramienta(herramienta, angulo=None):
    """Punto que tiene que llegar al objetivo, en el sistema del brazo."""
    if herramienta == "mano":
        return MANO.copy()
    if herramienta == "tenazas":
        return (agarre("tenazas", angulo) @ PUNTA_TENAZAS).to_translation()
    return agarre("martillo", angulo) @ BOCA_MARTILLO


def angulo_para(herramienta, distancia):
    """Ángulo de agarre con el que la punta de la herramienta queda a `distancia` del hombro. La mano abre o cierra
    la herramienta (como al agarrar más arriba o más abajo del mango): así llega exacta sin codo."""
    lo, hi = LIMITES_AGARRE[herramienta]
    if punto_herramienta(herramienta, lo).length <= distancia:
        return lo
    if punto_herramienta(herramienta, hi).length >= distancia:
        return hi
    for _ in range(30):
        m = (lo + hi) / 2
        if punto_herramienta(herramienta, m).length > distancia:
            lo = m
        else:
            hi = m
    return (lo + hi) / 2


def apuntar(punto_local, direccion, lateral):
    """Rotación que lleva `punto_local` (sistema del brazo) a la dirección `direccion`, eligiendo el giro sobre ese
    eje para que el lateral del brazo (X) quede lo más cerca posible de `lateral`."""
    d = direccion.normalized()
    r0 = punto_local.normalized().rotation_difference(d)
    x0 = r0 @ EJE_X
    x0p = (x0 - d * x0.dot(d))
    lp = (lateral - d * lateral.dot(d))
    if x0p.length < 1e-6 or lp.length < 1e-6:
        return r0
    x0p.normalize()
    lp.normalize()
    ang = math.atan2(d.dot(x0p.cross(lp)), x0p.dot(lp))
    return Quaternion(d, ang) @ r0


# ---------------------------------------------------------------------------------------------------------------
# Pieza: forma según la etapa
# ---------------------------------------------------------------------------------------------------------------


def etapa_pieza(f):
    """Dimensiones de la pieza en f (interpoladas entre etapas): (largo, ancho, grueso, filo, punta, espiga)."""
    e = max(0.0, min(5.0, muestrear(lt.ETAPA, f)))
    i = min(4, int(e))
    return _mezclar(es.ETAPAS[i], es.ETAPAS[i + 1], e - i)


def objetivo_yunque(hombro_mundo, f):
    """Punta de las tenazas para que la pieza quede tumbada sobre el yunque con el punto de golpe encima."""
    largo, ancho, grueso, filo, punta, espiga = etapa_pieza(f)
    h = lt.GOLPE - hombro_mundo
    h.z = 0
    h.normalize()
    dist = min(espiga + 0.5 * largo, 1.15)
    return lt.GOLPE - h * dist + Vector((0, 0, grueso / 2))


def punto_golpe(f):
    grueso = etapa_pieza(f)[2]
    return lt.GOLPE + Vector((0, 0, grueso))


# ---------------------------------------------------------------------------------------------------------------
# Evaluación de un fotograma
# ---------------------------------------------------------------------------------------------------------------

PUNTOS_FIJOS = {
    "boca_horno": Vector((-2.75, 1.0, 4.2)),
    "en_brasas": Vector((-2.75, 2.15, 3.22)),
    "en_brasas_2": Vector((-2.55, 2.3, 3.17)),
    "saca_horno": Vector((-2.65, -0.05, 4.15)),
    "alzar": Vector((-1.3, -2.9, 4.7)),
    "sobre_agua": Vector((2.55, -1.15, 6.1)),
    "en_agua": Vector((2.55, -2.06, 4.79)),
    "en_agua_2": Vector((2.62, -1.95, 4.95)),
    "saca_agua": Vector((2.5, -1.1, 6.15)),
    "en_alto": Vector((2.35, -1.5, 5.3)),
    "en_alto_2": Vector((2.3, -1.45, 5.45)),
}
COMPUERTA_BASE = Vector(((es.BOCA["x0"] + es.BOCA["x1"]) / 2, es.BOCA["y_cara"] - 0.12, es.BOCA["z0"] - 0.05))
ASA_LOCAL = Vector((0.55, -0.62, 1.0))  # asa a la derecha de la compuerta (la coge la mano derecha)
# El martillo cuelga a la espalda, a la derecha, con el mango hacia abajo (respecto al centro del torso). Así no
# choca con el horno ni con el brazo. CINTO es donde lo coge la mano.
CINTO = Vector((-0.62, 0.66, -0.62))
MARTILLO_CINTO = Matrix.Translation(CINTO) @ Matrix.Rotation(math.radians(8), 4, "X")
TRANSICION_MARTILLO = 6  # fotogramas en los que el martillo pasa del cinto a la mano (y al revés)


class Estado:
    """Todo lo que hace falta para un fotograma (matrices en el mundo)."""


def _resolver_brazo(lado, clave, pose, M_raiz, f, est):
    hueso = f"{lado} Arm"
    hombro, _ = pose.mundo(hueso)
    _, q_torso = pose.mundo("Torso")
    lateral = q_torso @ EJE_X
    tipo, *datos = clave
    if tipo == "dir":  # ("dir", dirección[, ángulo de agarre])
        return apuntar(ABAJO, Vector(datos[0]), lateral), (datos[1] if len(datos) > 1 else None)
    nombre, herramienta = datos
    p_mundo = punto_nombrado(nombre, f, est, pose, M_raiz)
    v = M_raiz.inverted() @ p_mundo - hombro
    ang = angulo_para(herramienta, v.length) if herramienta != "mano" else None
    return apuntar(punto_herramienta(herramienta, ang), v, lateral), ang


def punto_nombrado(nombre, f, est, pose=None, M_raiz=None):
    if nombre in PUNTOS_FIJOS:
        return PUNTOS_FIJOS[nombre].copy()
    if nombre == "asa":
        return COMPUERTA_BASE + ASA_LOCAL + Vector((0, 0, est.compuerta))
    if nombre == "cinto":
        p, q = pose.mundo("Torso")
        return M_raiz @ (p + q @ CINTO)
    if nombre in ("en_yunque", "sobre_yunque", "revisar_yunque"):
        hombro = M_raiz @ pose.mundo("Left Arm")[0]
        alto = {"en_yunque": 0.0, "sobre_yunque": 0.8, "revisar_yunque": 0.55}[nombre]
        return objetivo_yunque(hombro, f) + Vector((0, 0, alto))
    if nombre == "golpe":
        return punto_golpe(f)
    if nombre == "agua":
        return es.CENTRO_BARRIL + Vector((-0.05, 0.25, 0.1))
    if nombre == "compuerta":
        return COMPUERTA_BASE + Vector((0, 0, 1.6 + est.compuerta))
    if nombre == "pecho":
        return est.M["Torso"].to_translation() + Vector((0, 0, 0.4))
    if nombre == "cabeza":
        return est.M["Head"] @ Vector((0, 0, 0.6))
    if nombre in ("pieza", "hoja"):
        return est.centro_pieza.copy()
    raise KeyError(nombre)


def _brazo(lado, claves, herramienta, pose, M_raiz, f, est):
    """Pone la rotación del brazo y devuelve el ángulo de agarre de su herramienta."""
    c0, c1, k = tramo(claves, f)
    q0, a0 = _resolver_brazo(lado, c0[1], pose, M_raiz, f, est)
    a0 = lt.AGARRE[herramienta] if a0 is None else a0
    if k <= 0 or c0 is c1:
        q, a = q0, a0
    else:
        q1, a1 = _resolver_brazo(lado, c1[1], pose, M_raiz, f, est)
        a1 = lt.AGARRE[herramienta] if a1 is None else a1
        if q0.dot(q1) < 0:
            q1.negate()
        q = q0.slerp(q1, k)
        a = a0 + (a1 - a0) * k
    pose.poner_rot(f"{lado} Arm", q)
    return a


def _piernas(pose, f):
    """Altura del torso y orientación de las piernas para que los pies pisen sus puntos."""
    (pi, pd) = muestrear(lt.PIES, f)
    (dyi, dzi), (dyd, dzd), _, _ = pasos(f)
    objetivos = {"Left": Vector((pi[0], pi[1] + dyi, dzi)), "Right": Vector((pd[0], pd[1] + dyd, dzd))}
    pose.loc["Torso"].z = 0.0
    necesario = []
    for lado, obj in objetivos.items():
        cadera = pose.mundo(f"{lado} Leg")[0]
        dh = math.hypot(obj.x - cadera.x, obj.y - cadera.y)
        h = obj.z + math.sqrt(max(0.0, r6.LARGO_PIERNA**2 - dh * dh))
        necesario.append(h - cadera.z)
    agachado = min(0.0, muestrear(lt.TORSO_POS, f)[2])
    pose.loc["Torso"].z = min(necesario) + agachado
    for lado, obj in objetivos.items():
        cadera = pose.mundo(f"{lado} Leg")[0]
        v = obj - cadera
        if v.length < r6.LARGO_PIERNA:  # el pie no llega a estirar la pierna: se abre en horizontal
            dz = obj.z - cadera.z
            horiz = Vector((v.x, v.y, 0))
            r = math.sqrt(max(0.0, r6.LARGO_PIERNA**2 - dz * dz))
            horiz = horiz.normalized() * r if horiz.length > 1e-4 else Vector((0, 0, 0))
            v = Vector((horiz.x, horiz.y, dz))
        pose.poner_rot(f"{lado} Leg", ABAJO.rotation_difference(v.normalized()))


def evaluar(f):
    est = Estado()
    est.f = f
    est.compuerta = muestrear(lt.COMPUERTA, f)
    M_raiz = matriz_raiz(f)
    est.M_raiz = M_raiz
    pose = Pose()
    tx, ty, tz = muestrear(lt.TORSO_POS, f)
    pose.loc["Torso"] = Vector((tx, ty, 0))
    pose.q["Torso"] = _euler(muestrear(lt.TORSO_ROT, f))
    _, _, s_paso, fase = pasos(f)
    pose.q["Torso"] = pose.q["Torso"] @ _euler((0, 0, -6 * s_paso * math.sin(fase)))  # contragiro al andar
    pose.q["Head"] = _euler(muestrear(lt.CABEZA_ROT, f))
    _piernas(pose, f)
    est.M = {}
    est.agarre = {"tenazas": _brazo("Left", lt.BRAZO_IZQ, "tenazas", pose, M_raiz, f, est),
                  "martillo": _brazo("Right", lt.BRAZO_DER, "martillo", pose, M_raiz, f, est)}
    est.pose = pose
    est.M = {b: M_raiz @ pose.matriz(b) for b in es.PIEZAS_R6}

    # Tenazas y pieza
    est.M_tenazas = est.M["Left Arm"] @ agarre("tenazas", est.agarre["tenazas"])
    M_punta = est.M_tenazas @ PUNTA_TENAZAS
    c0, c1, k = tramo(lt.PIEZA_ORIENTACION, f)
    q0 = orientacion_pieza(c0[1], M_punta)
    q1 = orientacion_pieza(c1[1], M_punta)
    if q0.dot(q1) < 0:
        q1.negate()
    giro = Quaternion((0, 0, 1), math.radians(muestrear(lt.PIEZA_GIRO, f)))  # sobre su propio eje
    est.M_pieza = Matrix.Translation(M_punta.to_translation()) @ (q0.slerp(q1, k) @ giro).to_matrix().to_4x4()
    largo, ancho, grueso, filo, punta, espiga = etapa_pieza(f)
    est.etapa = muestrear(lt.ETAPA, f)
    est.dim_pieza = (largo, ancho, grueso, filo, punta, espiga)
    est.centro_pieza = est.M_pieza @ Vector((0, 0, -(espiga + largo / 2)))

    # Martillo: en la mano entre MARTILLO_EN_MANO; fuera, en el cinto (pegado al torso)
    est.M_martillo = martillo_mundo(f, est)

    # Calor y material
    est.temperatura = muestrear(lt.TEMPERATURA, f)
    est.brillo = muestrear(lt.BRILLO, f)
    est.pulido = muestrear(lt.PULIDO, f)
    est.destello = None
    d0, d1 = lt.DESTELLO
    if d0 <= f <= d1:
        u = EASING["suave"]((f - d0) / (d1 - d0))
        z = -(espiga + 0.12 + u * (largo - 0.35))
        est.destello = (est.M_pieza @ Vector((ancho / 2 * (1 - 0.6 * max(0, u - 0.7) / 0.3), 0, z)),
                        math.sin(math.pi * (f - d0) / (d1 - d0)))
    return est


def orientacion_pieza(modo, M_punta):
    """Orientación de la pieza en el mundo. La pieza se extiende hacia su -Z local desde la punta de las tenazas;
    su cara plana es el plano XZ local (el grueso va en Y).
      linea:   sigue a las tenazas
      tumbada: horizontal, en la dirección de las tenazas, con la cara plana hacia arriba
      temple:  inclinada hacia el barril (lt.DIRECCION_TEMPLE), de canto
      abajo:   colgando en vertical, punta abajo
      arriba:  en vertical, punta arriba (para enseñarla)"""
    q_linea = M_punta.to_quaternion()
    if modo == "linea":
        return q_linea
    h = q_linea @ Vector((0, 0, -1))
    h.z = 0
    h = h.normalized() if h.length > 1e-4 else Vector((0, -1, 0))
    arriba = Vector((0, 0, 1))
    if modo == "tumbada":
        z, y = -h, arriba
    elif modo == "temple":  # inclinada 55° hacia el barril, de canto: entra en el agua empujándola por su eje
        z, y = -Vector(lt.DIRECCION_TEMPLE).normalized(), Vector((1, 0, 0))
    elif modo == "abajo":
        z, y = arriba, h
    else:  # arriba: de canto hacia los lados (como en el temple), así el giro desde el agua es en su plano
        z, y = -arriba, Vector((1, 0, 0))
    x = y.cross(z)
    return Matrix((x, y, z)).transposed().to_quaternion()


def martillo_mundo(f, est):
    """En la mano entre MARTILLO_EN_MANO y colgado a la espalda fuera; al cogerlo y al dejarlo pasa de uno a otro en
    TRANSICION_MARTILLO fotogramas (mientras la mano está en el cinto), sin saltos."""
    a, b = lt.MARTILLO_EN_MANO
    en_mano = est.M["Right Arm"] @ agarre("martillo", est.agarre["martillo"])
    cinto = est.M["Torso"] @ MARTILLO_CINTO
    t = TRANSICION_MARTILLO
    if a <= f <= b:
        k = 1.0
    elif a - t < f < a:
        k = EASING["suave"]((f - (a - t)) / t)
    elif b < f < b + t:
        k = 1 - EASING["suave"]((f - b) / t)
    else:
        k = 0.0
    if k <= 0:
        return cinto
    if k >= 1:
        return en_mano
    q0, q1 = cinto.to_quaternion(), en_mano.to_quaternion()
    if q0.dot(q1) < 0:
        q1.negate()
    p = cinto.to_translation().lerp(en_mano.to_translation(), k)
    return Matrix.Translation(p) @ q0.slerp(q1, k).to_matrix().to_4x4()


# ---------------------------------------------------------------------------------------------------------------
# Cámara
# ---------------------------------------------------------------------------------------------------------------


def plano_en(f):
    for p in lt.PLANOS:
        if p["inicio"] <= f < p["fin"]:
            return p
    return lt.PLANOS[-1]


def _resolver(v, f, est):
    return punto_nombrado(v, f, est) if isinstance(v, str) else Vector(v)


_CENTRO_ORBITA = {}


def camara(f, est):
    """(posición, punto al que mira, lente mm, f-stop, distancia de foco, nombre del plano)."""
    p = plano_en(f)
    if "orbita" in p:
        o = p["orbita"]
        if p["nombre"] not in _CENTRO_ORBITA:
            cs = [evaluar(i).centro_pieza for i in range(p["inicio"], p["fin"], 4)]
            _CENTRO_ORBITA[p["nombre"]] = sum(cs, Vector()) / len(cs)
        c = _CENTRO_ORBITA[p["nombre"]]
        t = EASING["suave"]((f - p["inicio"]) / (p["fin"] - 1 - p["inicio"]))
        a = math.radians(o["angulo"][0] + (o["angulo"][1] - o["angulo"][0]) * t)
        pos = c + Vector((o["radio"] * math.cos(a), o["radio"] * math.sin(a), o["altura"] + 0.4 * t))
        mira, lente = c - Vector((0, 0, o.get("mira_abajo", 0.0))), o["lente"]
    else:
        claves = p["claves"]
        if len(claves) == 1 or f <= claves[0][0]:
            c0 = c1 = claves[0]
            k = 0.0
        else:
            c0, c1 = claves[0], claves[-1]
            for x, y in zip(claves, claves[1:]):
                if x[0] <= f <= y[0]:
                    c0, c1 = x, y
            k = EASING["suave"](min(1.0, (f - c0[0]) / max(1, c1[0] - c0[0])))
        pos = Vector(c0[1]).lerp(Vector(c1[1]), k)
        mira = _resolver(c0[2], f, est).lerp(_resolver(c1[2], f, est), k)
        lente = c0[3] + (c1[3] - c0[3]) * k
    foco = _resolver(p["foco"], f, est)
    return pos, mira, lente, p["fstop"], (foco - pos).length, p["nombre"]


def temblor(f):
    """Giro extra de la cámara (grados de cabeceo y guiñada) por los martillazos y la cámara en mano."""
    cab = lt.TEMBLOR_MANO * (math.sin(f * 0.21) + 0.6 * math.sin(f * 0.53 + 1.3))
    gui = lt.TEMBLOR_MANO * (math.sin(f * 0.17 + 2.1) + 0.6 * math.sin(f * 0.47))
    for i, fi in enumerate(lt.IMPACTOS):
        if fi <= f < fi + 14:
            t = f - fi
            a = lt.TEMBLOR_GOLPE[i] * math.exp(-t / 3.2)
            cab += a * math.sin(t * 2.6 + i)
            gui += a * 0.7 * math.sin(t * 3.3 + 2 * i)
    if lt.CONTACTO_AGUA <= f < lt.CONTACTO_AGUA + 10:
        t = f - lt.CONTACTO_AGUA
        a = 0.35 * math.exp(-t / 3)
        cab += a * math.sin(t * 2.9)
    return cab, gui


def matriz_camara(f, est):
    pos, mira, lente, fstop, foco, nombre = camara(f, est)
    q = (mira - pos).to_track_quat("-Z", "Y")
    cab, gui = temblor(f)
    q = q @ Euler((math.radians(cab), math.radians(gui), 0), "XYZ").to_quaternion()
    return Matrix.Translation(pos) @ q.to_matrix().to_4x4(), lente, fstop, foco, nombre, mira


# ---------------------------------------------------------------------------------------------------------------
# Utilidades de color
# ---------------------------------------------------------------------------------------------------------------


def cuerpo_negro(k):
    """Color RGB (0-1, lineal aproximado) de un cuerpo negro a k kelvin (aproximación de Tanner Helland)."""
    t = k / 100.0
    r = 255.0 if t <= 66 else 329.698727446 * (t - 60) ** -0.1332047592
    g = (99.4708025861 * math.log(t) - 161.1195681661) if t <= 66 else 288.1221695283 * (t - 60) ** -0.0755148492
    b = 255.0 if t >= 66 else (0.0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307)
    srgb = [max(0.0, min(255.0, c)) / 255.0 for c in (r, g, b)]
    return tuple(c**2.2 for c in srgb)


def color_pieza(k):
    """Color de la pieza a k kelvin: cuerpo negro desplazado lt.REALCE_COLOR kelvin hacia el amarillo (el ojo se
    adapta a la luz de la forja y el metal caliente se ve más claro que el cuerpo negro de su temperatura)."""
    return cuerpo_negro(max(1000.0, k) + lt.REALCE_COLOR)


def cuerpo_negro_srgb(k):
    return tuple(c ** (1 / 2.2) for c in cuerpo_negro(k))
