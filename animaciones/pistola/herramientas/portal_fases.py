"""
El guion del portal en el tiempo: qué hace cada pieza en cada fase. Sin Blender: son las mismas curvas que se describen en
modelos/pistola_portales/vfx_portal.md y las que usa generar_portal.py para dibujar las hojas. Cuando el director monte el
efecto en Roblox, estos números son los de los Tween.

Fases (segundos desde el inicio de cada una):
    DISPARO    0 - (distancia / VELOCIDAD_PROYECTIL)   fogonazo en la «Boca» y proyectil hasta donde se apunta
    APERTURA   0 - 0,45                                 el portal se abre de golpe desde un punto, onda y destello
    ABIERTO    en bucle                                 remolino girando y borde vivo
    CIERRE     0 - 0,40                                 se encoge, gira cada vez más deprisa y desaparece con un destello

Unidades: studs, segundos y grados. Los dos portales (chatarra = inestable; vip = perfecto) comparten la estructura y cambian
los números y el «carácter»: la chatarra parpadea, se bambolea y salta; la VIP es exacta y sin ruido.
"""

import math

VELOCIDAD_PROYECTIL = 70.0  # studs/s
DURACION = {"apertura": 0.45, "cierre": 0.40, "disparo_fogonazo": 0.05}

# Ajustes por portal (aquí se retoca la sensación)
ESTILOS = {
    "chatarra": dict(
        sobrepaso=1.14,  # la apertura se pasa de tamaño (back) y se asienta
        bamboleo=dict(amp=0.06, hz=9.0, decae=6.0),
        giro_abierto=-110.0,  # grados/s del remolino
        giro_temblor=((6.0, 3.1), (4.0, 7.3)),  # (grados, Hz): el giro no es uniforme
        escala_temblor=((0.025, 11.0, 0.0), (0.02, 17.3, 1.0)),  # (amplitud, Hz, fase): el portal «respira» nervioso
        brillo_anillo=(0.75, 0.25, 13.0, 4.7),  # base + amplitud * |sin(a) sin(b)|: parpadeo
        borde_escala=(0.12, 6.0),
        borde_giro=5.0,
        chispas_apertura=26, chispas_cierre=10, chispas_abierto_por_s=7,
        gravedad=18.0, vel_chispa=(8.0, 20.0), vida_chispa=0.5,
        cierre_giro=220.0, cierre_tartamudeo=0.25,
        destello_apertura=7.0, destello_cierre=3.6,
        onda_final=2.25,
    ),
    "vip": dict(
        sobrepaso=1.04,
        bamboleo=dict(amp=0.0, hz=9.0, decae=6.0),
        giro_abierto=-50.0,
        giro_temblor=((0.0, 1.0), (0.0, 1.0)),
        escala_temblor=((0.004, 0.5, 0.0), (0.0, 1.0, 0.0)),
        brillo_anillo=(1.0, 0.0, 1.0, 1.0),
        borde_escala=(0.0, 1.0),
        borde_giro=0.0,
        chispas_apertura=16, chispas_cierre=16, chispas_abierto_por_s=24,
        gravedad=0.0, vel_chispa=(14.0, 14.0), vida_chispa=0.5,
        cierre_giro=360.0, cierre_tartamudeo=0.0,
        destello_apertura=6.0, destello_cierre=3.0,
        onda_final=2.0,
    ),
}


def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def fuera_atras(t, c1=1.70158):
    """Easing «back out»: llega pasándose de largo y vuelve."""
    t = max(0.0, min(1.0, t))
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def dentro_atras(t, c1=1.70158):
    t = max(0.0, min(1.0, t))
    return (c1 + 1) * t**3 - c1 * t**2


def sale_quinta(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 5


def estado(estilo, fase, t):
    """
    Estado de cada pieza del portal. Devuelve un diccionario:
        escala     tamaño del conjunto (1 = 4,4 x 6,2 studs)
        giro       grados acumulados del remolino
        remolino   opacidad del remolino (0..1)
        anillo     brillo del anillo (0..1)
        borde      (escala, giro) del borde de llamas
        onda       (escala, brillo) de la onda expansiva (0 = invisible)
        destello   tamaño en studs del destello de estrella (0 = ninguno)
        marcas     brillo de las marcas de orden (solo VIP; en la chatarra no existen): late a 0,83 Hz
    """
    e = ESTILOS[estilo]
    base_giro = e["giro_abierto"]
    jit = sum(a * math.sin(2 * math.pi * hz * t) for a, hz in e["giro_temblor"])
    out = dict(escala=1.0, giro=base_giro * t + jit, remolino=1.0, anillo=1.0, borde=(1.0, 0.0), onda=(1.0, 0.0),
               destello=0.0, marcas=1.0)
    b0, a0, f1, f2 = e["brillo_anillo"]
    out["anillo"] = b0 + a0 * abs(math.sin(2 * math.pi * f1 * t) * math.sin(2 * math.pi * f2 * t))
    amp_b, hz_b = e["borde_escala"]
    out["borde"] = (1.0 + amp_b * math.sin(2 * math.pi * hz_b * t), e["borde_giro"] * math.sin(2 * math.pi * 2.3 * t))
    esc = 1.0
    for a, hz, ph in e["escala_temblor"]:
        esc += a * math.sin(2 * math.pi * hz * t + ph)
    out["escala"] = esc
    out["marcas"] = 0.4 + 0.6 * (0.5 + 0.5 * math.cos(2 * math.pi * t / 1.2)) ** 2
    if fase == "abierto":
        return out

    if fase == "apertura":
        d = DURACION["apertura"]
        u = t / d
        grande = e["sobrepaso"] - 1.0
        c1 = 1.70158 * (grande / 0.1) if grande > 0 else 0.0
        esc_ap = fuera_atras(min(1.0, t / 0.30), c1=max(c1, 0.0001)) if t < 0.30 else 1.0
        bam = e["bamboleo"]
        esc_ap += bam["amp"] * math.sin(2 * math.pi * bam["hz"] * t) * math.exp(-bam["decae"] * t) if t >= 0.3 else 0.0
        out["escala"] = max(0.0, esc_ap)
        out["remolino"] = suave((t - 0.04) / 0.22)
        out["anillo"] = min(1.0, 0.4 + 2.0 * t) * (out["anillo"] if e["brillo_anillo"][1] else 1.0)
        out["onda"] = (0.15 + (e["onda_final"] - 0.15) * sale_quinta(t / 0.40), max(0.0, 1 - t / 0.40) ** 1.5)
        s = e["destello_apertura"]
        out["destello"] = s * (t / 0.06 if t < 0.06 else math.exp(-(t - 0.06) / 0.07)) if t < 0.30 else 0.0
        out["giro"] = base_giro * t * 2.5 + jit
        return out

    if fase == "cierre":
        d = DURACION["cierre"]
        u = max(0.0, min(1.0, t / d))
        esc = 1.0 - dentro_atras(u)
        if e["cierre_tartamudeo"] and abs(math.sin(2 * math.pi * 14 * t)) > 0.7:
            esc *= 1.0 - e["cierre_tartamudeo"] * u
        out["escala"] = max(0.0, esc)
        out["giro"] = base_giro * t + e["cierre_giro"] * u * u
        out["remolino"] = 1.0 - suave(u * u)
        out["anillo"] = out["anillo"] * (1.0 - 0.6 * u)
        out["onda"] = (1.0 + 0.5 * u, 0.0)
        tf = t - 0.85 * d
        out["destello"] = e["destello_cierre"] * (tf / 0.04 if 0 <= tf < 0.04 else math.exp(-(tf - 0.04) / 0.06)) if tf >= 0 else 0.0
        return out
    raise ValueError(fase)


def chispas(estilo, fase, t, semilla=1):
    """
    Chispas sueltas en el plano del portal (studs, desde el centro, x hacia la derecha y z hacia arriba) en el instante t:
    [(x, z, vx, vz, largo)]. En la apertura y el cierre salen en ráfaga; abierto: las de la chatarra saltan del borde y las de
    la VIP giran ordenadas hacia dentro.
    """
    import random

    e = ESTILOS[estilo]
    rng = random.Random(semilla)
    out = []
    ax, az = 2.2, 3.1

    def borde(th, k=1.0):
        return ax * math.cos(th) * k, az * math.sin(th) * k

    if fase in ("apertura", "cierre"):
        n = e["chispas_apertura"] if fase == "apertura" else e["chispas_cierre"]
        t0 = 0.0 if fase == "apertura" else DURACION["cierre"] * 0.85
        tt = t - t0
        if tt < 0:
            return out
        for i in range(n):
            th = (math.tau * i / n) + (rng.uniform(-0.12, 0.12) if estilo == "chatarra" else 0.0)
            v = rng.uniform(*e["vel_chispa"])
            vx, vz = math.cos(th) * v, math.sin(th) * v
            if tt > e["vida_chispa"]:
                continue
            x0, z0 = (borde(th, 0.4) if fase == "apertura" else borde(th, 0.9))
            out.append((x0 + vx * tt, z0 + vz * tt - 0.5 * e["gravedad"] * tt * tt, vx, vz - e["gravedad"] * tt,
                        0.22 * (1 - tt / e["vida_chispa"]) + 0.06))
        return out
    # abierto
    n = e["chispas_abierto_por_s"]
    if estilo == "vip":
        for i in range(n):
            ciclo = (t * 0.7 + i / n) % 1.0
            th = math.tau * i / n + 3.0 * ciclo + t * 0.9
            k = 1.0 - 0.9 * ciclo
            x, z = borde(th, k * 0.97)
            out.append((x, z, 0.0, 0.0, 0.10))
    else:
        for i in range(n * 2):
            fase_i = (t * 1.0 + rng.random()) % 1.0
            th = rng.uniform(0, math.tau)
            v = rng.uniform(4.0, 11.0)
            tt = fase_i * 0.5
            x0, z0 = borde(th, 1.0)
            vx, vz = math.cos(th) * v, math.sin(th) * v
            out.append((x0 + vx * tt, z0 + vz * tt - 0.5 * e["gravedad"] * tt * tt, vx, vz - e["gravedad"] * tt,
                        0.2 * (1 - fase_i)))
    return out
