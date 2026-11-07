"""
Animaciones de la PISTOLA DE PORTALES para el rig R6: APUNTAR (bucle) y DISPARO (una vez), para las dos pistolas:

  * "chatarra" (la normal): más tirón y menos estable. Retroceso grande, el cuerpo se tuerce, la cabeza se echa atrás,
    la pistola tiembla al cargar y todo se bambolea un momento después.
  * "vip": retroceso fuerte pero controlado y limpio. Menos giro, sin temblor, recupera antes y sin bamboleo.

Todo está en torno al «torso» (R6 no tiene codos ni rodillas): el brazo derecho apunta en una dirección (en el sistema
del torso, así que se mezcla bien con reposo, trote y correr), el torso se inclina, gira y retrocede, y el pie trasero da
medio paso atrás usando el mismo modelo de bota (talón, planta, punta) que el reposo y el andar de la #17: pies que no
patinan ni se hunden.

Disparo (60 fps, 0,67 s, sin bucle):
    0 -  9   CARGA (0,15 s): el brazo se tensa y la pistola baja un poco; el torso se inclina hacia delante
    9        SUELTA (marcador «Disparo»): sale el fogonazo y el proyectil
    9 - 12   RETROCESO: el brazo sube de golpe (llega al 87 % en un solo fotograma), el torso se echa atrás y gira, la cabeza
             salta, el pie trasero se levanta
    12 - 14  HITSTOP: se mantiene el máximo (2 fotogramas)
    14 - fin RECUPERACIÓN: vuelve a apuntar, suave pero rápido; el pie trasero planta medio paso atrás y vuelve
    Los últimos fotogramas son idénticos a los del primero: la pose de apuntar.

Apuntar (60 fps, 2 s, bucle perfecto): solo se anima el brazo derecho, con la respiración (la normal además tiembla y se
va un poco de lado). Va con peso 1 solo en el brazo (ver rbxmx_pistola.py): lo demás lo pone la animación de debajo.

Ejes de Blender (los del rig): X = izquierda del personaje, -Y = hacia delante, Z = arriba. Estudios (studs) y grados.
"""

import math

from mathutils import Quaternion, Vector

import ciclo
import rig_r6 as r6
from ciclo import Pose
from punetazo_fuerte import muestrear

FPS = 60
FOTOGRAMA_DISPARO = 9  # 0,15 s de carga
ULTIMO_DISPARO = 40  # 0,67 s
CICLO_APUNTAR = 120  # 2 s

BOTA = ciclo.Bota(0.004)  # planta casi plana, como en el reposo
ANCHO_PIES = 0.20  # los mismos pies que el reposo: la pose de partida encaja con él
INCLINACION_BASE = 2.5  # la misma del reposo

# --------------------------------------------------------------------------------------------------------------
# Datos de cada pistola (aquí se retoca la sensación del disparo)
# --------------------------------------------------------------------------------------------------------------
ESTILOS = {
    "chatarra": dict(
        titulo="Normal (chatarra)",
        # brazo derecho: «adelante» = ángulo desde colgando (90 = horizontal), «fuera» = separarlo del cuerpo (grados)
        brazo_adelante=92.0, brazo_fuera=-2.0,
        carga_baja=13.0,  # cuánto baja la pistola al cargar
        retroceso_sube=30.0,  # cuánto sube de golpe
        retroceso_fuera=11.0,  # se abre hacia fuera
        retroceso_cant=24.0,  # la pistola se ladea (giro del brazo sobre su eje)
        brazo_retrae=0.34,  # el hombro se va hacia atrás (studs)
        carga_retrae=0.12,
        # torso
        carga_inclina=5.0, carga_giro=6.0, carga_atras=-0.12,
        retroceso_inclina=-17.0, retroceso_giro=-28.0, retroceso_atras=0.66, retroceso_lado=0.14,
        # cabeza: compensa el torso (0..1) y, además, salta hacia atrás
        cabeza_comp=0.7, cabeza_salto=-8.0,
        # brazo izquierdo (adelante, fuera) en reposo, al cargar y en el máximo del retroceso
        izq=((18.0, 12.0), (30.0, 8.0), (-42.0, 40.0)),
        # pie trasero: medio paso atrás (studs) y altura a la que levanta el pie
        paso=0.62, paso_alto=0.30,
        # tiempos
        mantener_hasta=14, recuperar_hasta=38, paso_ida=(10, 18), paso_vuelta=(22, 32),
        # bamboleo tras el golpe (amortiguado) y temblor al cargar
        bambolea=dict(brazo=7.0, torso_giro=5.0, torso_incl=2.5, hz=7.0, tau=9.0),
        tiembla=dict(brazo=1.7, lado=1.1, hz=17.0, hz2=11.0),
        # apuntar en bucle: respiración y deriva (grados) con ciclos enteros por bucle
        apuntar=dict(resp=1.3, resp2=0.8, tremor=0.55, deriva=1.6, lado=1.2),
    ),
    "vip": dict(
        titulo="VIP",
        brazo_adelante=92.0, brazo_fuera=-2.0,
        carga_baja=6.0,
        retroceso_sube=20.0, retroceso_fuera=3.0, retroceso_cant=4.0,
        brazo_retrae=0.22, carga_retrae=0.06,
        carga_inclina=3.0, carga_giro=2.0, carga_atras=-0.06,
        retroceso_inclina=-11.0, retroceso_giro=-8.0, retroceso_atras=0.42, retroceso_lado=0.0,
        cabeza_comp=0.85, cabeza_salto=-2.5,
        izq=((18.0, 12.0), (24.0, 10.0), (-8.0, 20.0)),
        paso=0.40, paso_alto=0.22,
        mantener_hasta=13, recuperar_hasta=32, paso_ida=(10, 16), paso_vuelta=(18, 27),
        bambolea=dict(brazo=0.0, torso_giro=0.0, torso_incl=0.0, hz=7.0, tau=9.0),
        tiembla=dict(brazo=0.0, lado=0.0, hz=17.0, hz2=11.0),
        apuntar=dict(resp=0.35, resp2=0.0, tremor=0.0, deriva=0.0, lado=0.0),
    ),
}

# --------------------------------------------------------------------------------------------------------------
# Canales (0..1)
# --------------------------------------------------------------------------------------------------------------


def _curva(claves, f):
    return muestrear(claves, f)[0]


def canal_carga(f):
    """1 al soltar (fotograma 9) y cae a 0 en 2 fotogramas (el retroceso toma el mando)."""
    F = FOTOGRAMA_DISPARO
    return _curva([(0, (0.0,), "suave"), (F, (1.0,), "suave"), (F + 2, (0.0,), "sale")], f)


def canal_retroceso(f, e):
    """0 hasta soltar; casi 1 en el primer fotograma tras soltar («golpe»); se mantiene (hitstop) y recupera suave."""
    F = FOTOGRAMA_DISPARO
    return _curva(
        [(F, (0.0,), "suave"), (F + 3, (1.0,), "golpe"), (e["mantener_hasta"], (1.0,), "suave"),
         (e["recuperar_hasta"], (0.0,), "sale")],  # «sale»: arranca rápido y frena suave
        f,
    )


def _bump(f, a, b):
    """0..1..0 con forma de seno al cuadrado entre los fotogramas a y b."""
    if f <= a or f >= b:
        return 0.0
    return math.sin(math.pi * (f - a) / (b - a)) ** 2


def canal_paso(f, e):
    """Cuánto ha ido hacia atrás el pie trasero (0..1) y cuánto lo levanta (0..1)."""
    a0, a1 = e["paso_ida"]
    b0, b1 = e["paso_vuelta"]
    paso = _curva([(a0, (0.0,), "suave"), (a1, (1.0,), "suave"), (b0, (1.0,), "suave"), (b1, (0.0,), "suave")], f)
    return paso, max(_bump(f, a0 - 1, a1 + 1), _bump(f, b0 - 1, b1 + 1))


def bamboleo(f, e):
    """Oscilación amortiguada tras el máximo (solo la chatarra): 0 antes de soltar."""
    t = f - e["mantener_hasta"]
    if t < 0:
        return 0.0
    b = e["bambolea"]
    fin = max(ULTIMO_DISPARO - e["mantener_hasta"], 1)
    ventana = 1.0 - muestrear([(0, (0.0,), "suave"), (fin, (1.0,), "suave")], t)[0]  # se apaga del todo al final
    return ventana * math.exp(-t / b["tau"]) * math.sin(2 * math.pi * b["hz"] * t / FPS)


def temblor(f, e):
    """(adelante, lado) en grados: la pistola de chatarra tiembla más cuanto más carga; cesa al soltar."""
    t = e["tiembla"]
    c = canal_carga(f) if f <= FOTOGRAMA_DISPARO else 0.0
    k = c * c
    return (
        k * t["brazo"] * math.sin(2 * math.pi * t["hz"] * f / FPS + 0.7),
        k * t["lado"] * math.sin(2 * math.pi * t["hz2"] * f / FPS + 2.1),
    )


# --------------------------------------------------------------------------------------------------------------
# Piezas de la pose
# --------------------------------------------------------------------------------------------------------------


def _huellas(paso):
    """Huella (x, y) del centro de la planta de cada pie. El izquierdo se queda; el derecho da `paso` studs atrás."""
    base = Pose()
    out = {}
    for pierna, lado in ciclo.PIERNAS.items():
        cadera = base.mundo(pierna)[0]
        y = cadera.y + ciclo.CENTRO_BOTA_Y + (paso if lado < 0 else 0.0)
        out[pierna] = (cadera.x - 0.5 * lado + lado * ANCHO_PIES, y)
    return out


def _torso_pose(f, e, ladeo, c, r, escala=1.0, base=INCLINACION_BASE):
    """Pose con el torso colocado (sin altura) en el fotograma f. c = carga, r = retroceso. `escala` reduce lo que se
    inclina y gira el torso (la variante móvil: las piernas van con el torso y no se pueden dejar atrás)."""
    pose = Pose()
    b = e["bambolea"]
    w = bamboleo(f, e)
    inclina = base + escala * (e["carga_inclina"] * c + e["retroceso_inclina"] * r + b["torso_incl"] * w)
    giro = escala * (e["carga_giro"] * c + e["retroceso_giro"] * r + b["torso_giro"] * w)
    pose.loc["Torso"] = Vector((e["retroceso_lado"] * r, e["carga_atras"] * c + e["retroceso_atras"] * r, 0.0))
    pose.q["Torso"] = ciclo.rot_torso(inclina, ladeo, giro)
    return pose


def _dir_brazo_der(adelante, fuera, cant=0.0):
    """Orientación del brazo derecho en el sistema del torso: apunta a (adelante, fuera) con la pistola ladeada `cant`."""
    d = ciclo.dir_brazo(adelante, fuera, -1)
    q = ciclo.ABAJO.rotation_difference(d.normalized())
    return Quaternion(d.normalized(), math.radians(cant)) @ q


def _brazo_derecho(f, e, c, r, w, t):
    """(rotación en el sistema del torso, desplazamiento del hombro) del brazo derecho en el disparo."""
    adelante = (
        e["brazo_adelante"] - e["carga_baja"] * c + e["retroceso_sube"] * r + e["bambolea"]["brazo"] * w + t[0]
    )
    fuera = e["brazo_fuera"] + e["retroceso_fuera"] * r + t[1]
    cant = e["retroceso_cant"] * r
    loc = Vector((0.0, e["carga_retrae"] * c + e["brazo_retrae"] * r, 0.0))
    return _dir_brazo_der(adelante, fuera, cant), loc


def calcular_pose_disparo(f, estilo, variante="completo"):
    """Pose del disparo en el fotograma f (60 fps). variante: «completo» (con el paso atrás) o «movil» (solo la parte
    de arriba: piernas y desplazamiento quietos, para disparar andando o corriendo)."""
    e = ESTILOS[estilo]
    c, r = canal_carga(f), canal_retroceso(f, e)
    w, t = bamboleo(f, e), temblor(f, e)
    completo = variante == "completo"
    paso, alto = canal_paso(f, e) if completo else (0.0, 0.0)
    huellas = _huellas(paso * e["paso"])

    def torso(ladeo):
        if completo:
            return _torso_pose(f, e, ladeo, c, r)
        # móvil: el torso casi no se mueve (las piernas cuelgan de él y siguen lo que ponga el andar o el correr)
        p = _torso_pose(f, e, ladeo, c, r, escala=0.3, base=0.0)
        p.loc["Torso"] = Vector((0.0, 0.0, 0.0))
        return p

    if completo:
        # Ladeo del torso con el que las dos piernas piden la misma altura (los dos pies en el suelo)
        def diferencia(ladeo):
            z = [ciclo.apoyo(torso(ladeo), p, huellas[p], BOTA)[0] for p in ciclo.PIERNAS]
            return z[0] - z[1]

        bajo, alto_l = -10.0, 10.0
        d_bajo = diferencia(bajo)
        for _ in range(50):
            medio = (bajo + alto_l) / 2
            d = diferencia(medio)
            if (d > 0) == (d_bajo > 0):
                bajo, d_bajo = medio, d
            else:
                alto_l = medio
        ladeo = (bajo + alto_l) / 2
    else:
        ladeo = 0.0

    pose = torso(ladeo)
    if completo:
        sube, q_izq, _ = ciclo.apoyo(pose, "Left Leg", huellas["Left Leg"], BOTA)
        pose.loc["Torso"].z = sube
        pose.poner_rot_mundo("Left Leg", q_izq)
        _, q_der, (_, alfa, gamma) = ciclo.apoyo(pose, "Right Leg", huellas["Right Leg"], BOTA)
        pose.poner_rot_mundo("Right Leg", q_der)
        if alto > 1e-3:  # pie en el aire: gira la pierna hacia atrás lo justo para que la bota quede a `margen`
            margen = e["paso_alto"] * alto

            def libre(delta):
                pose.poner_rot_mundo("Right Leg", ciclo.rot_pierna(alfa - delta, gamma))
                return ciclo.suelo_minimo(pose, "Right Leg")

            lo, hi = 0.0, 1.3
            for _ in range(40):
                mid = (lo + hi) / 2
                if libre(mid) < margen:
                    lo = mid
                else:
                    hi = mid
            libre(hi)
    else:
        pose.q["Left Leg"] = Quaternion()
        pose.q["Right Leg"] = Quaternion()

    # Cabeza: compensa el torso para seguir mirando al frente y salta hacia atrás con el golpe
    rot_t = pose.q["Torso"]
    eul = rot_t.to_euler("XYZ")
    comp = e["cabeza_comp"]
    pose.q["Head"] = ciclo.rot_torso(
        math.degrees(-eul.x) * comp + e["cabeza_salto"] * r, -math.degrees(eul.y) * comp * 0.0,
        -math.degrees(eul.z) * comp,
    )

    # Brazo derecho (el que dispara)
    q_der, loc_der = _brazo_derecho(f, e, c, r, w, t)
    pose.poner_rot_mundo("Right Arm", pose.mundo("Torso")[1] @ q_der)
    pose.loc["Right Arm"] = loc_der

    # Brazo izquierdo: contrapeso. Se estira al cargar y sale despedido hacia atrás y fuera con el golpe
    (a0, f0), (a1, f1), (a2, f2) = e["izq"]
    adel = a0 + (a1 - a0) * c + (a2 - a0) * r
    fu = f0 + (f1 - f0) * c + (f2 - f0) * r
    pose.poner_rot_mundo("Left Arm", pose.mundo("Torso")[1] @ _dir_brazo_izq(adel, fu))
    return pose


def _dir_brazo_izq(adelante, fuera):
    d = ciclo.dir_brazo(adelante, fuera, 1)
    return ciclo.ABAJO.rotation_difference(d.normalized())


# --------------------------------------------------------------------------------------------------------------
# Apuntar (bucle)
# --------------------------------------------------------------------------------------------------------------


def _apuntar_angulos(f, e):
    """(adelante, fuera) del brazo derecho al apuntar, con la respiración y, en la chatarra, el temblor y la deriva.
    Todo son senos con un número ENTERO de ciclos en el bucle (1, 2, 3, 9...): cierra sin salto, y se resta el valor del
    fotograma 0 para que ahí valga exactamente la base (así empalma con el final del disparo)."""
    a = e["apuntar"]

    def crudo(fr):
        ph = 2 * math.pi * fr / CICLO_APUNTAR
        adel = (a["resp"] * math.sin(ph) + a["resp2"] * math.sin(3 * ph + 1.0) + a["tremor"] * math.sin(9 * ph + 0.4)
                + a["deriva"] * math.sin(2 * ph + 2.0))
        fuera = a["lado"] * math.sin(2 * ph + 0.5) + 0.5 * a["lado"] * math.sin(5 * ph + 1.3)
        return adel, fuera

    adel, fuera = crudo(f)
    adel0, fuera0 = crudo(0)
    return e["brazo_adelante"] + adel - adel0, e["brazo_fuera"] + fuera - fuera0


_CACHE_BASE = {}


def _pose_base(estilo):
    """La pose del fotograma 0 del disparo (pies plantados), calculada una vez; devuelve una copia."""
    if estilo not in _CACHE_BASE:
        _CACHE_BASE[estilo] = calcular_pose_disparo(0, estilo)
    base = _CACHE_BASE[estilo]
    pose = Pose()
    for h in r6.ARTICULACIONES:
        pose.q[h] = base.q[h].copy()
        pose.loc[h] = base.loc[h].copy()
    return pose


def calcular_pose_apuntar(f, estilo):
    """Pose de apuntar: la pose de partida del disparo (pies plantados, torso quieto) y el brazo con su movimiento."""
    e = ESTILOS[estilo]
    pose = _pose_base(estilo)
    adel, fuera = _apuntar_angulos(f % CICLO_APUNTAR, e)
    pose.poner_rot_mundo("Right Arm", pose.mundo("Torso")[1] @ _dir_brazo_der(adel, fuera))
    # respiración: el hombro sube unas centésimas, como en el reposo
    ph = 2 * math.pi * f / CICLO_APUNTAR
    pose.loc["Right Arm"] = Vector((0.0, 0.0, 0.03 * math.sin(ph) ** 2 if e["apuntar"]["resp"] > 0.5 else 0.01))
    return pose


# --------------------------------------------------------------------------------------------------------------
# Metadatos de las animaciones (los usa generar.py)
# --------------------------------------------------------------------------------------------------------------
# peso de cada articulación en el KeyframeSequence (0 = no la toca: se queda lo que pongan las animaciones de debajo)
PESOS = {
    "completo": {"HumanoidRootPart": 0.0, "Torso": 1.0, "Head": 1.0, "Right Arm": 1.0, "Left Arm": 1.0,
                 "Right Leg": 1.0, "Left Leg": 1.0},
    "movil": {"HumanoidRootPart": 0.0, "Torso": 0.6, "Head": 0.8, "Right Arm": 1.0, "Left Arm": 1.0,
              "Right Leg": 0.0, "Left Leg": 0.0},
    "apuntar": {"HumanoidRootPart": 0.0, "Torso": 0.0, "Head": 0.0, "Right Arm": 1.0, "Left Arm": 0.0,
                "Right Leg": 0.0, "Left Leg": 0.0},
}
MARCADORES = {  # fotograma -> [(nombre, valor)] (KeyframeMarker: Animation:GetMarkerReachedSignal)
    0: [("Carga", "")],
    FOTOGRAMA_DISPARO: [("Disparo", "")],
    FOTOGRAMA_DISPARO + 3: [("RetrocesoMax", "")],
}
FOTOGRAMAS_CLAVE = [
    (0, "Apuntar"),
    (5, "Carga"),
    (9, "Suelta"),
    (10, "Retroceso"),
    (12, "Máximo"),
    (19, "Paso atrás"),
    (28, "Vuelve"),
    (40, "Apuntar"),
]


# --------------------------------------------------------------------------------------------------------------
# Piezas de la pistola (para animarlas en Roblox y para las hojas): rueda, depósito, anillos, núcleo
# --------------------------------------------------------------------------------------------------------------

def _rebote(t, amp, tau, largo):
    """Salto con rebotes que se amortiguan: 0 en t=0, sube, cae y vuelve a subir menos."""
    if t <= 0:
        return 0.0
    return amp * math.exp(-t / tau) * abs(math.sin(math.pi * t / largo))


def piezas_chatarra(f):
    """Rueda (grados acumulados sobre su eje), salto del depósito (studs) y chispas de la bobina, en el disparo."""
    F = FOTOGRAMA_DISPARO
    c = canal_carga(f)
    # la rueda: va cogiendo velocidad al cargar (hasta 140°) y al soltar da media vuelta y pico, frenando
    if f <= F:
        giro = 140.0 * c * c
    else:
        giro = 140.0 + 560.0 * muestrear([(F, (0.0,), "sale"), (F + 26, (1.0,), "sale")], f)[0]
    t = f - F
    vibra = 0.008 * c * math.sin(2 * math.pi * 22 * f / FPS) if f <= F else 0.0  # el depósito vibra al cargar
    salto = _rebote(t - 0.5, 0.075, 8.0, 10.0) + vibra
    chispas = 1.0 if F <= f <= F + 2 else (0.35 if f in (3, 6, 8) else 0.0)  # 1 = ráfaga grande, 0,35 = chisporroteo
    return dict(rueda=giro, deposito=salto, chispas=chispas)


def piezas_vip(f):
    """Anillos (grados acumulados de cada uno), escala y blancura del núcleo, en el disparo."""
    F = FOTOGRAMA_DISPARO
    base = (60.0, -90.0, 120.0)  # grados por segundo en reposo; el del medio al revés

    def velocidad(frame):  # multiplicador de la velocidad: sube al cargar (x3) y estalla al soltar (x15) y se calma
        if frame < F:
            return 1.0 + 2.0 * canal_carga(frame)
        return 1.0 + 14.0 * math.exp(-(frame - F) / 14.0)

    angulos = [0.0, 0.0, 0.0]
    for i in range(int(f)):
        for j in range(3):
            angulos[j] += base[j] / FPS * velocidad(i)
    c = canal_carga(f) if f <= F else 0.0
    flash = math.exp(-(f - F) / 5.0) if f >= F else 0.0
    return dict(anillos=angulos, nucleo_escala=1.0 + 0.35 * c + 1.1 * flash, nucleo_blanco=min(1.0, 0.25 * c + flash))


def piezas_apuntar(f, estilo):
    """Lo que se mueve de la pistola al apuntar: los anillos giran despacio; la chatarra tiembla un pelín."""
    ph = f / CICLO_APUNTAR
    if estilo == "vip":
        base = (60.0, -90.0, 120.0)
        return dict(anillos=[b * ph * CICLO_APUNTAR / FPS for b in base], nucleo_escala=1.0 + 0.03 * math.sin(2 * math.pi * ph),
                    nucleo_blanco=0.0)
    return dict(rueda=0.0, deposito=0.006 * math.sin(2 * math.pi * 3 * ph), chispas=0.0)
