"""
Armas y herramientas de «Humanos vs Monstruos» (catálogo de armas, ver modelos/armas/README.md).

Cada arma es una función que describe sus piezas con armas_kit (medidas en studs, arriba de cada función) y
devuelve un `Arma`. El script construye, hornea los 5 mapas, exporta el FBX (con el Empty "Handle") y su JSON, y
renderiza el turnaround en modelos/armas/rondas/<arma>_ronda_N.png.

Uso:
    python modelos/herramientas/armas.py --salida modelos/armas --ronda 1 [--rapido] [--solo espada_plasma,...]
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image  # noqa: E402

import armas_kit as ak  # noqa: E402
import comun as c  # noqa: E402

CIAN = ak.CIAN
NEON = {"color": CIAN, "rug": 0.4, "met": 0.0, "emision": 5.0}


def neon(color=CIAN, fuerza=5.0):
    return {"color": color, "rug": 0.4, "met": 0.0, "emision": fuerza}


def suave(t, a, b):
    """Rampa suave de 0 (t<=a) a 1 (t>=b)."""
    if t <= a:
        return 0.0
    if t >= b:
        return 1.0
    x = (t - a) / (b - a)
    return x * x * (3 - 2 * x)


def recto(z0, z1):
    return lambda t: (0.0, z0 + (z1 - z0) * t)


def mango(p, mat, z0, z1, r, lados=16, anillos=10, cintura=0.08, estrias=0.0, n_estrias=6):
    """Empuñadura cilíndrica de z0 a z1 con algo de cintura (más estrecha en el centro) y estrías opcionales."""
    import armas_kit  # noqa: F401
    secs = []
    for i in range(anillos + 1):
        t = i / anillos
        rr = r * (1 - cintura * math.sin(math.pi * t))
        if estrias:
            rr *= 1 - estrias * (0.5 + 0.5 * math.cos(t * math.tau * n_estrias))
        secs.append([Vector((math.cos(a) * rr, math.sin(a) * rr, z0 + (z1 - z0) * t))
                     for a in (math.tau * k / lados for k in range(lados))])
    return p.loft(secs, mat)


def spline(puntos):
    """Curva Catmull-Rom por los puntos de control (tuplas 3D): devuelve f(t) con t en 0..1."""
    P = [Vector(p) for p in puntos]
    P = [P[0] * 2 - P[1]] + P + [P[-1] * 2 - P[-2]]
    tramos = len(P) - 3

    def f(t):
        x = min(tramos - 1e-6, max(0.0, t * tramos))
        i = int(x)
        u = x - i
        p0, p1, p2, p3 = P[i:i + 4]
        return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u * u +
                      (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
    return f


def perfil_cara(seccion):
    """Grosor relativo de la cara superior (v >= 0) de una sección de hoja en función de u (interpolación lineal)."""
    pts = sorted({(u, v) for u, v in seccion if v >= 0})

    def f(u):
        for (u0, v0), (u1, v1) in zip(pts, pts[1:]):
            if u0 <= u <= u1:
                return v0 + (v1 - v0) * (u - u0) / max(1e-6, u1 - u0)
        return 0.0
    return f


def sup_hoja(camino, ancho, grueso, desvio=lambda t: 0.0, seccion=None):
    """
    Punto de la superficie de una hoja barrida: f(t, u, lado, elev) con u a lo ancho (-1..1), lado = +1/-1 la cara
    (+Y / -Y) y elev la altura sobre la cara. Sirve para colocar vetas, runas y neón pegados a la hoja.
    """
    cara = perfil_cara(seccion) if seccion else (lambda u: 1.0)

    def f(t, u, lado, elev=0.0):
        x, z = camino(t)
        tg = ak._tangente(camino, t)
        nx, nz = tg.y, -tg.x
        w = desvio(t) + u * ancho(t)
        return Vector((x + nx * w, lado * (grueso(t) * cara(u) + elev), z + nz * w))
    return f


# ==============================================================================================================
# CATEGORÍA 1: ESPADAS (una mano). La hoja apunta a +Z, el plano de la hoja es XZ y el Handle está en el origen.
# ==============================================================================================================


def espada_plasma():
    """#1 Espada de Plasma (Común). Hoja recta de doble filo con canal de energía; guarda en barra; pomo esférico."""
    LARGO_HOJA, ANCHO, GROSOR = 2.2, 0.30, 0.06
    MANGO, R_MANGO = 0.8, 0.085
    GUARDA_ANCHO = 0.6
    paleta = {
        "hoja": {"color": "#BFCBDA", "rug": 0.15, "met": 1.0, "patron": "cepillado", "relieve": 0.25},
        "canal": {"color": "#5D6878", "rug": 0.25, "met": 1.0},
        "guarda": {"color": "#525A66", "rug": 0.28, "met": 1.0, "patron": "cepillado", "relieve": 0.3},
        "sintetico": {"color": "#141619", "rug": 0.7, "met": 0.0, "patron": "diamante", "relieve": 1.0},
        "neon": NEON,
    }
    a = ak.Arma("EspadaPlasma", "espada_plasma.fbx", "Comun", paleta, "Espada de Plasma")
    z_guarda = MANGO / 2
    z_hoja = z_guarda + 0.1

    # Hoja: rombo aplanado con canal profundo en las dos caras (el neón va dentro del canal).
    seccion = [(1, 0), (0.45, 0.8), (0.24, 1), (0.16, 0.15), (-0.16, 0.15), (-0.24, 1), (-0.45, 0.8), (-1, 0),
               (-0.45, -0.8), (-0.24, -1), (-0.16, -0.15), (0.16, -0.15), (0.24, -1), (0.45, -0.8)]
    mats = ["hoja", "hoja", "canal", "canal", "canal", "hoja", "hoja", "hoja", "hoja", "canal", "canal", "canal",
            "hoja", "hoja"]

    def ancho(t):
        return ANCHO / 2 * (1 - 0.12 * t) * (1 - suave(t, 0.84, 1.0) ** 1.4 * 0.97)

    def grueso(t):
        return GROSOR / 2 * (1 - 0.35 * suave(t, 0.6, 1.0))

    h = a.pieza("Hoja")
    h.barrido(recto(z_hoja, z_hoja + LARGO_HOJA), "hoja", n=14, seccion=seccion, ancho=ancho, grueso=grueso,
              mats_seccion=mats)
    # Talón de la hoja (ricasso) que entra en la guarda.
    h.caja((0, 0, z_hoja - 0.02), (ANCHO * 0.78, GROSOR * 1.15, 0.12), "guarda")

    # Guarda: barra que se curva hacia la hoja en las puntas.
    g = a.pieza("Guarda")
    g.barrido(lambda t: (-GUARDA_ANCHO / 2 + GUARDA_ANCHO * t, z_guarda + 0.045 + 0.07 * (2 * t - 1) ** 2),
              "guarda", n=12, seccion=[(1, 0.6), (0.6, 1), (-0.6, 1), (-1, 0.6), (-1, -0.6), (-0.6, -1), (0.6, -1),
                                       (1, -0.6)],
              ancho=lambda t: 0.05 * (1 - 0.35 * abs(2 * t - 1)), grueso=lambda t: 0.065 * (1 - 0.3 * abs(2 * t - 1)),
              punta=False)
    for s in (-1, 1):  # remates de las puntas
        g.esfera((s * GUARDA_ANCHO / 2, 0, z_guarda + 0.115), 0.042, "guarda", seg=8, anillos=6)

    # Empuñadura con grip diamantado (normal map) y anillos en los extremos.
    e = a.pieza("Empunadura", studio={"raiz": True})
    mango(e, "sintetico", -MANGO / 2, MANGO / 2 - 0.02, R_MANGO, lados=16, anillos=10, cintura=0.1)
    e.toro((0, 0, MANGO / 2 - 0.03), R_MANGO * 1.05, 0.022, "guarda", seg=16, lados=6)
    e.toro((0, 0, -MANGO / 2 + 0.02), R_MANGO * 1.05, 0.022, "guarda", seg=16, lados=6)

    # Pomo: esfera pequeña con cuello.
    pm = a.pieza("Pomo")
    pm.cilindro((0, 0, -MANGO / 2 - 0.06), 0.06, 0.07, "guarda", lados=12, radio2=0.075)
    pm.esfera((0, 0, -MANGO / 2 - 0.12), 0.105, "guarda", seg=16, anillos=10)

    # Neón: línea de energía en el fondo del canal, en las dos caras (0,02 de grosor, 0,01 sobre el canal).
    nn = a.pieza("Neon_01", rol="neon", studio={"color": CIAN})
    fondo = GROSOR / 2 * 0.15
    for s in (-1, 1):
        nn.cinta(lambda t, s=s: (0, s * (fondo + 0.01), z_hoja + 0.12 + (LARGO_HOJA * 0.8) * t), 0.045,
                 lambda t, s=s: (0, s, 0), 0.02, "neon", n=1,
                 ancho_fn=lambda t: 0.045 * (1 - 0.55 * t))

    a.agarre("Handle", (0, 0, 0), (0, 0, 1))
    return a


def hoja_cristal():
    """#2 Hoja de Cristal (Poco común). Sable de cristal translúcido con vetas en relieve, guarda en C y gema."""
    LARGO, ANCHO_BASE, ANCHO_PUNTA, GROSOR = 2.4, 0.35, 0.15, 0.05
    CURVA = 0.28  # cuánto se separa la punta del eje (studs)
    MANGO, R_MANGO = 0.8, 0.085
    paleta = {
        "cristal": {"color": "#46F0D2", "rug": 0.05, "met": 0.0, "patron": "cristalino", "relieve": 0.6,
                    "color2": "#1C8FB0", "mezcla": ("grad", "Z", 0.6, 3.0), "alfa": 0.7},
        "veta": {"color": "#F4FFFD", "rug": 0.0, "met": 0.0},
        "patina": {"color": "#46524C", "rug": 0.35, "met": 1.0, "patron": "grabado", "relieve": 0.4,
                   "color2": "#3F7A62", "mezcla": ("manchas", 6.0, 0.62)},
        "cuero": {"color": "#3B2418", "rug": 0.8, "met": 0.0, "patron": "cuero", "relieve": 1.0},
        "gema": {"color": "#2FE0C8", "rug": 0.05, "met": 0.0, "alfa": 0.85},
        "neon": NEON,
    }
    a = ak.Arma("HojaCristal", "hoja_cristal.fbx", "PocoComun", paleta, "Hoja de Cristal")
    z0 = MANGO / 2 + 0.08

    def camino(t):
        return (-CURVA * t * t, z0 + LARGO * t)

    def ancho(t):
        base = ANCHO_BASE + (ANCHO_PUNTA - ANCHO_BASE) * t
        return base / 2 * (1 - suave(t, 0.82, 1.0) ** 1.2 * 0.96)

    def grueso(t):
        return GROSOR / 2 * (1 - 0.4 * t)

    def desvio(t):  # el lomo sigue la curva y la hoja crece hacia el filo (lado convexo, +X)
        return ancho(t) * 0.35

    sec = ak.SECCION_SABLE
    h = a.pieza("Hoja")
    h.barrido(camino, "cristal", n=18, seccion=sec, ancho=ancho, grueso=grueso, desvio=desvio)
    sup = sup_hoja(camino, ancho, grueso, desvio, sec)

    # Vetas: aristas cristalinas levantadas que nacen en la base y se abren en diagonal hacia el filo.
    rnd = random.Random(2)
    v = a.pieza("Vetas")
    nn = a.pieza("Neon_01", rol="neon")
    # (t0, t1, u0, u1): tramos rectos que cambian de dirección como fracturas de cristal.
    vetas = [(0.02, 0.3, -0.7, 0.2), (0.3, 0.55, 0.2, -0.5), (0.55, 0.78, -0.5, 0.15), (0.78, 0.92, 0.15, -0.35),
             (0.12, 0.26, -0.3, 0.55), (0.42, 0.52, -0.05, 0.6), (0.66, 0.74, -0.25, 0.45)]
    for lado in (-1, 1):
        for i, (t0, t1, u0, u1) in enumerate(vetas):
            def cam(s, t0=t0, t1=t1, u0=u0, u1=u1, lado=lado):
                t = t0 + (t1 - t0) * s
                return sup(t, u0 + (u1 - u0) * s, lado, 0.0)
            principal = i < 4
            v.cinta(cam, 0.03, lambda s, lado=lado: (0, lado, 0), 0.02, "veta", n=3,
                    ancho_fn=lambda s, p=principal: (0.034 if p else 0.022) * (1 - 0.4 * s))
            if principal:  # la fractura principal brilla
                nn.cinta(lambda s, cam=cam, lado=lado: cam(s) + Vector((0, lado * 0.03, 0)), 0.012,
                         lambda s, lado=lado: (0, lado, 0), 0.02, "neon", n=3, ancho_fn=lambda s: 0.012)

    # Guarda en C: cruz corta + arco de nudillos que baja por el lado del filo hasta el pomo.
    g = a.pieza("Guarda")
    zg = MANGO / 2 + 0.03
    g.barrido(lambda t: (-0.2 + 0.4 * t, zg + 0.03 * math.sin(t * math.pi)), "patina", n=6,
              seccion=[(1, 0.7), (0.6, 1), (-0.6, 1), (-1, 0.7), (-1, -0.7), (-0.6, -1), (0.6, -1), (1, -0.7)],
              ancho=lambda t: 0.045, grueso=lambda t: 0.075, punta=False)
    g.esfera((-0.21, 0, zg + 0.01), 0.04, "patina", seg=8, anillos=6)
    g.banda(lambda t: (0.2 + 0.16 * math.sin(t * math.pi) - 0.13 * t, 0, zg - (MANGO + 0.1) * t), (0, 1, 0), 0.09,
            0.05, "patina", n=14, ancho_fn=lambda t: 0.1 - 0.035 * math.sin(t * math.pi))
    g.cilindro((0, 0, -MANGO / 2 - 0.08), 0.07, 0.08, "patina", lados=12)  # pomo donde acaba la C

    e = a.pieza("Empunadura", studio={"raiz": True})
    mango(e, "cuero", -MANGO / 2, MANGO / 2, R_MANGO, lados=14, anillos=14, cintura=0.06, estrias=0.07,
          n_estrias=7)
    e.toro((0, 0, -MANGO / 2), R_MANGO * 1.02, 0.02, "patina", seg=14, lados=6)

    # Gema en la unión guarda-hoja (en las dos caras), en un engaste de la guarda.
    gm = a.pieza("Gema")
    n2 = a.pieza("Neon_02", rol="neon")
    for lado in (-1, 1):
        gm.esfera((0, lado * 0.05, zg + 0.04), 0.07, "gema", seg=8, anillos=4, escala=(1, 0.55, 1.2))
        n2.esfera((0, lado * 0.098, zg + 0.04), 0.035, "neon", seg=6, anillos=4, escala=(1, 0.3, 1.2))
    g.toro((0, 0.045, zg + 0.04), 0.074, 0.016, "patina", seg=12, lados=4, eje=(0, 1, 0), escala_r=(1, 1))
    g.toro((0, -0.045, zg + 0.04), 0.074, 0.016, "patina", seg=12, lados=4, eje=(0, 1, 0))

    a.agarre("Handle", (0, 0, 0), (0, 0, 1))
    return a


def sable_gravitacional():
    """#3 Sable Gravitacional (Raro). Cuchilla ancha que se ensancha hacia la punta en diagonal; guarda generador."""
    LARGO, ANCHO, GROSOR = 2.6, 0.4, 0.08
    MANGO, R_MANGO = 1.0, 0.09
    paleta = {
        "gunmetal": {"color": "#2E343D", "rug": 0.2, "met": 1.0, "patron": "fundido", "relieve": 1.8},
        "filo": {"color": "#8C96A3", "rug": 0.12, "met": 1.0},
        "industrial": {"color": "#5C636D", "rug": 0.45, "met": 1.0, "patron": "paneles", "relieve": 0.8},
        "oscuro": {"color": "#2A2E35", "rug": 0.4, "met": 1.0},
        "plata": {"color": "#D5DCE4", "rug": 0.1, "met": 1.0},
        "goma": {"color": "#18191C", "rug": 0.75, "met": 0.0, "patron": "polimero", "relieve": 0.8},
        "neon": NEON,
    }
    a = ak.Arma("SableGravitacional", "sable_gravitacional.fbx", "Raro", paleta, "Sable Gravitacional")
    zg0, zg1 = MANGO / 2, MANGO / 2 + 0.32  # bloque de la guarda
    z0 = zg1 - 0.04
    HW = ANCHO / 2

    def camino(t):
        return (0.0, z0 + LARGO * t)

    def ancho_total(t):  # se ensancha hacia la punta (falchion)
        return HW * (0.7 + 0.5 * t)

    def ancho(t):  # corte diagonal: el lomo cae hacia el filo en el último 18 %
        return ancho_total(t) * (1 - 0.985 * suave(t, 0.8, 1.0) ** 0.9)

    def desvio(t):  # mantiene el filo (u = +1) en su sitio mientras el lomo retrocede
        return ancho_total(t) - ancho(t) - 0.05

    def grueso(t):
        return GROSOR / 2 * (1 - 0.3 * t)

    sec = ak.SECCION_CUCHILLA
    mats = ["filo", "gunmetal", "gunmetal", "gunmetal", "gunmetal", "gunmetal", "filo"]
    h = a.pieza("Hoja")
    h.barrido(camino, "gunmetal", n=16, seccion=sec, ancho=ancho, grueso=grueso, desvio=desvio,
              mats_seccion=mats)
    sup = sup_hoja(camino, ancho, grueso, desvio, sec)

    # Guarda: bloque generador con paneles, conductos y un emisor central.
    g = a.pieza("Guarda", studio={"bisel": 0.015, "angulo_bisel": 60})
    g.caja((0, 0, (zg0 + zg1) / 2), (0.62, 0.26, zg1 - zg0), "industrial")
    g.caja((0, 0, zg1 + 0.01), (0.5, 0.2, 0.05), "oscuro")
    g.caja((0, 0, zg0 - 0.03), (0.3, 0.2, 0.07), "oscuro")
    for lado in (-1, 1):
        for k, zz in enumerate((zg0 + 0.08, zg0 + 0.16, zg0 + 0.24)):  # conductos horizontales
            g.cilindro((-0.33, lado * 0.135, zz), 0.028, 0.66, "oscuro", lados=6, eje="X")
        for xx in (-0.27, 0.27):  # tornillos
            g.cilindro((xx, lado * 0.13, zg1 - 0.03), 0.018, 0.02, "plata", lados=5, eje=(0, lado, 0))
            g.cilindro((xx, lado * 0.13, zg0 + 0.03), 0.018, 0.02, "plata", lados=5, eje=(0, lado, 0))
    for s in (-1, 1):  # tubos laterales que suben a los lados de la hoja
        g.cilindro((s * 0.31, 0, zg0), 0.05, zg1 - zg0 + 0.06, "oscuro", lados=10)
        g.esfera((s * 0.31, 0, zg1 + 0.06), 0.05, "oscuro", seg=10, anillos=6)
    nn = a.pieza("Neon_01", rol="neon")
    for lado in (-1, 1):  # ranura de energía en cada cara del bloque, entre conductos
        for zz in (zg0 + 0.12, zg0 + 0.2):
            nn.caja((0, lado * (0.13 + 0.02), zz), (0.44, 0.02, 0.022), "neon")
        nn.esfera((0, lado * 0.15, zg1 - 0.055), 0.035, "neon", seg=8, anillos=4, escala=(1, 0.5, 1))
    for s in (-1, 1):
        nn.toro((s * 0.31, 0, zg1 - 0.02), 0.06, 0.012, "neon", seg=12, lados=4)

    # Empuñadura larga (dos manos) y pomo de contrapeso.
    e = a.pieza("Empunadura", studio={"raiz": True})
    mango(e, "goma", -MANGO / 2, MANGO / 2 - 0.03, R_MANGO, lados=14, anillos=12, cintura=0.04, estrias=0.08,
          n_estrias=8)
    e.cilindro((0, 0, -MANGO / 2 - 0.12), 0.11, 0.12, "oscuro", lados=8, radio2=0.09)
    e.toro((0, 0, -MANGO / 2 - 0.05), 0.105, 0.02, "plata", seg=12, lados=4)

    # Neón del filo: lámina en cada cara a lo largo del filo exterior.
    n2 = a.pieza("Neon_02", rol="neon")
    for lado in (-1, 1):
        n2.cinta(lambda t, lado=lado: sup(t, 0.62, lado, 0.01), 0.04, lambda t, lado=lado: (0, lado, 0), 0.02,
                 "neon", n=14, t0=0.03, t1=0.97, ancho_fn=lambda t: 0.04 * (1 - 0.5 * suave(t, 0.8, 0.97)))

    # Tres anillos de distorsión que orbitan la hoja, un poco inclinados (piezas sueltas para animarlas).
    n3 = a.pieza("Neon_03", rol="neon", studio={"nota": "Brillo de los 3 anillos: si se animan, soldar cada parte "
                                                           "a su anillo o animar el neón con ellos"})
    for i, (t, inc) in enumerate(((0.18, 0.18), (0.5, -0.22), (0.8, 0.14)), 1):
        zz = z0 + LARGO * t
        R = ancho_total(t) + 0.16
        eje = Vector((math.sin(inc), 0.25 * inc, math.cos(inc))).normalized()
        an = a.pieza(f"Anillo_0{i}")
        an.toro((0.0, 0, zz), R, 0.024, "plata", seg=24, lados=5, eje=eje, escala_r=(0.7, 1.5))
        n3.toro((0.0, 0, zz), R - 0.028, 0.008, "neon", seg=24, lados=3, eje=eje)

    a.agarre("Handle", (0, 0, 0), (0, 0, 1))
    return a


def espada_estelar():
    """#4 Espada Estelar (Legendario). Hoja dorada de diamante con canal, punta bifurcada, guarda de cuernos."""
    LARGO, ANCHO, GROSOR = 2.8, 0.32, 0.075
    LARGO_PUNTAS = 0.3
    MANGO, R_MANGO = 0.85, 0.085
    paleta = {
        "oro": {"color": "#FFCC55", "rug": 0.08, "met": 1.0, "color2": "#FFA640", "mezcla": ("manchas", 2.5, 0.6)},
        "lava": {"color": "#FF7A1A", "rug": 0.2, "met": 0.0, "color2": "#FFF2C8", "mezcla": ("manchas", 9, 0.55)},
        "oro_viejo": {"color": "#B08A3E", "rug": 0.3, "met": 1.0, "patron": "grabado", "relieve": 0.9},
        "hueso": {"color": "#EEE6D2", "rug": 0.6, "met": 0.0, "patron": "hueso", "relieve": 0.7,
                  "color2": "#C9A24A", "mezcla": ("vetas", 3.5, 0.82)},
        "cristal_oro": {"color": "#FFB800", "rug": 0.05, "met": 0.0, "alfa": 0.88},
        "neon": NEON,
    }
    a = ak.Arma("EspadaEstelar", "espada_estelar.fbx", "Legendario", paleta, "Espada Estelar")
    zg = MANGO / 2
    z0 = zg + 0.1
    T_SPLIT = (LARGO - LARGO_PUNTAS) / LARGO

    def camino(t):  # ligera curva
        return (0.06 * math.sin(t * math.pi * 0.9), z0 + LARGO * t)

    def ancho(t):
        return ANCHO / 2 * (1 - 0.18 * t) * (1 + 0.12 * math.exp(-((t - 0.08) / 0.06) ** 2))

    def grueso(t):
        return GROSOR / 2 * (1 - 0.35 * t)

    sec = ak.SECCION_DIAMANTE
    mats = ["oro", "oro", "lava", "lava", "lava", "lava", "oro", "oro", "oro", "lava", "lava", "lava", "lava", "oro"]
    h = a.pieza("Hoja")
    h.barrido(camino, "oro", n=18, seccion=sec, ancho=ancho, grueso=grueso, punta=False, t1=T_SPLIT,
              mats_seccion=mats)
    # Punta bifurcada: dos puntas separadas 15° que salen del final de la hoja.
    xs, zs = camino(T_SPLIT)
    hw = ancho(T_SPLIT)
    for s in (-1, 1):
        ang = math.radians(7.5) * s
        base_x = xs + s * hw * 0.5

        def cam_p(t, base_x=base_x, ang=ang):
            return (base_x + math.sin(ang) * LARGO_PUNTAS * t, zs - 0.02 + math.cos(ang) * LARGO_PUNTAS * t)
        h.barrido(cam_p, "oro", n=4, seccion=ak.SECCION_ROMBO, ancho=lambda t: hw * 0.5 * (1 - 0.15 * t),
                  grueso=lambda t: grueso(T_SPLIT) * (1 - 0.3 * t))
    sup = sup_hoja(camino, ancho, grueso, seccion=sec)

    # Guarda: dos alas curvadas hacia arriba como cuernos, con un cuerpo central.
    g = a.pieza("Guarda")
    g.esfera((0, 0, zg + 0.04), 0.12, "oro_viejo", seg=12, anillos=8, escala=(1.5, 0.75, 0.8))
    # Emblema de la estrella moribunda en el centro de la guarda (un sol de 8 rayos en cada cara).
    for lado in (-1, 1):
        g.cilindro((0, lado * 0.07, zg + 0.04), 0.075, 0.03, "oro_viejo", lados=16, eje=(0, lado, 0))
        for k in range(8):
            ang = k * math.tau / 8
            largo = 0.2 if k % 2 == 0 else 0.13
            d = Vector((math.cos(ang), 0, math.sin(ang)))
            g.cilindro(Vector((0, lado * 0.075, zg + 0.04)) + d * 0.06, 0.03, largo, "oro_viejo", lados=4,
                       eje=d, radio2=0.002)
    for s in (-1, 1):
        def ala(t, s=s):
            return (s * (0.08 + 0.42 * t - 0.06 * t ** 3), zg + 0.03 + 0.42 * t ** 2.2)
        g.barrido(ala if s > 0 else (lambda t, ala=ala: ala(t)), "oro_viejo", n=12, seccion=ak.SECCION_ROMBO,
                  ancho=lambda t: 0.07 * (1 - 0.85 * t) + 0.004, grueso=lambda t: 0.06 * (1 - 0.6 * t) + 0.004)
    n2 = a.pieza("Neon_02", rol="neon")
    for lado in (-1, 1):  # núcleo del sol
        n2.cilindro((0, lado * 0.1, zg + 0.04), 0.045, 0.02, "neon", lados=12, eje=(0, lado, 0))
    for s in (-1, 1):
        for lado in (-1, 1):
            def borde(t, s=s, lado=lado):
                x = s * (0.08 + 0.42 * t - 0.06 * t ** 3)
                z = zg + 0.03 + 0.42 * t ** 2.2
                return Vector((x, lado * (0.06 * (1 - 0.6 * t) * 0.45 + 0.012), z))
            n2.cinta(borde, 0.02, lambda t, lado=lado: (0, lado, 0), 0.02, "neon", n=10, t0=0.05, t1=0.85,
                     ancho_fn=lambda t: 0.024 * (1 - 0.6 * t))

    # Empuñadura de hueso tallado con runas en relieve.
    e = a.pieza("Empunadura", studio={"raiz": True})
    mango(e, "hueso", -MANGO / 2, MANGO / 2, R_MANGO, lados=14, anillos=12, cintura=0.12, estrias=0.05,
          n_estrias=4)
    n3 = a.pieza("Neon_03", rol="neon")
    glifos = [[(0, -1), (0, 1)], [(-1, 1), (0, 0), (1, 1)], [(-1, -1), (1, 1)], [(-1, 0), (1, 0)]]
    for fila, zz in enumerate((-0.25, 0.0, 0.25)):
        for k in range(4):
            ang = k * math.tau / 4 + fila * 0.4
            rr = R_MANGO * (1 - 0.12 * math.sin(math.pi * (zz / MANGO + 0.5)))
            nrm = Vector((math.cos(ang), math.sin(ang), 0))
            tan = Vector((-math.sin(ang), math.cos(ang), 0))
            gl = glifos[(fila + k) % 4]
            for (u0, v0), (u1, v1) in zip(gl, gl[1:]):
                p0 = nrm * rr + tan * u0 * 0.03 + Vector((0, 0, zz + v0 * 0.045))
                p1 = nrm * rr + tan * u1 * 0.03 + Vector((0, 0, zz + v1 * 0.045))
                m = (p0 + p1) / 2
                d = (p1 - p0)
                eje_z = d.normalized()
                rot = Matrix((tan, eje_z.cross(nrm).cross(eje_z) if False else nrm, eje_z)).transposed()
                # Runa en relieve (parte del hueso) y su brillo encima.
                e.caja(m + nrm * 0.006, (0.018, 0.018, d.length + 0.016), "hueso",
                       giro=Matrix((eje_z.cross(nrm), nrm, eje_z)).transposed())
                n3.caja(m + nrm * 0.026, (0.01, 0.02, d.length + 0.01), "neon",
                        giro=Matrix((eje_z.cross(nrm), nrm, eje_z)).transposed())

    # Pomo: mini planeta con su anillo.
    pm = a.pieza("Pomo")
    pm.cilindro((0, 0, -MANGO / 2 - 0.05), 0.05, 0.06, "oro_viejo", lados=10, radio2=0.065)
    pm.esfera((0, 0, -MANGO / 2 - 0.13), 0.1, "oro_viejo", seg=16, anillos=10)
    pm.toro((0, 0, -MANGO / 2 - 0.13), 0.16, 0.014, "oro_viejo", seg=24, lados=4, eje=(0.35, 0.2, 1),
            escala_r=(1.6, 0.6))
    n5 = a.pieza("Neon_05", rol="neon")
    n5.toro((0, 0, -MANGO / 2 - 0.13), 0.16, 0.007, "neon", seg=24, lados=4, eje=(0.35, 0.2, 1),
            escala_r=(1.0, 1.0))
    # (el neón del anillo va encima del anillo, 0,01 por fuera)
    for v_ in list(n5.bm.verts):
        v_.co += Vector((0.35, 0.2, 1)).normalized() * 0.018

    # Canales de la hoja: núcleo de energía dentro del canal de lava, en las dos caras.
    n1 = a.pieza("Neon_01", rol="neon")
    for lado in (-1, 1):
        n1.cinta(lambda t, lado=lado: sup(t, 0.0, lado, 0.01), 0.035, lambda t, lado=lado: (0, lado, 0), 0.02,
                 "neon", n=14, t0=0.04, t1=T_SPLIT * 0.97, ancho_fn=lambda t: 0.04 * (1 - 0.45 * t))

    # Corona: 6 fragmentos de luz que orbitan la hoja (cristal dorado con núcleo de neón).
    rnd = random.Random(4)
    n4 = a.pieza("Neon_04", rol="neon", studio={"nota": "Núcleos de los 6 fragmentos: animarlos con ellos"})
    for i in range(6):
        ang = i * math.tau / 6 + 0.3
        t = 0.2 + 0.12 * i
        zz = z0 + LARGO * t
        R = 0.42 + 0.06 * math.sin(i * 2.1)
        cen = Vector((math.cos(ang) * R, math.sin(ang) * R * 0.75, zz))
        giro = Matrix.Rotation(rnd.uniform(-0.5, 0.5), 3, "X") @ Matrix.Rotation(ang, 3, "Z")
        fr = a.pieza(f"Fragmento_0{i + 1}")
        fr.fragmento(cen, 0.3, "cristal_oro", giro=giro, rnd=rnd, lados=4)
        n4.fragmento(cen, 0.13, "neon", giro=giro, lados=4)

    a.agarre("Handle", (0, 0, 0), (0, 0, 1))
    return a


def hoja_vacio():
    """#5 Hoja del Vacío (Mítico). Corte de nada con aura, garras de hueso, espinas y un ojo de pomo."""
    LARGO, ANCHO, GROSOR = 3.0, 0.3, 0.03
    MANGO, R_MANGO = 0.85, 0.08
    ROJO, PURPURA_ROJO, ROJO_OSC = "#FF2222", "#E0206A", "#881111"
    paleta = {
        "vacio": {"color": "#000000", "rug": 0.0, "met": 0.0},
        "aura": {"color": "#1A0820", "rug": 0.0, "met": 0.0, "alfa": 0.3},
        "hueso_negro": {"color": "#1C1222", "rug": 0.45, "met": 0.0, "patron": "hueso", "relieve": 1.0,
                        "color2": "#5A0E1C", "mezcla": ("vetas", 4.0, 0.86)},
        "espejo": {"color": "#050507", "rug": 0.0, "met": 1.0},
        "ojo": {"color": "#1A0B10", "rug": 0.25, "met": 0.0, "patron": "hueso", "relieve": 0.4},
        "pupila": {"color": "#000000", "rug": 0.1, "met": 0.0},
        "neon": neon(PURPURA_ROJO, 6), "iris": neon(ROJO, 6), "venas": neon(ROJO_OSC, 4),
    }
    a = ak.Arma("HojaVacio", "hoja_vacio.fbx", "Mitico", paleta, "Hoja del Vacío")
    zg = MANGO / 2 + 0.1
    z0 = zg + 0.05

    def camino(t):
        return (0.0, z0 + LARGO * t)

    def ancho(t):
        return ANCHO / 2 * (1 - 0.1 * t) * (1 - suave(t, 0.86, 1.0) ** 1.3 * 0.97)

    def grueso(t):
        return GROSOR / 2

    sec = [(1, 0), (0.85, 1), (-0.85, 1), (-1, 0), (-0.85, -1), (0.85, -1)]
    h = a.pieza("Hoja")
    h.barrido(camino, "vacio", n=16, seccion=sec, ancho=ancho, grueso=grueso)
    # Aura: una segunda hoja translúcida, más grande, con el borde ondulado como humo congelado.
    au = a.pieza("Aura")
    au.barrido(lambda t: (0.0, z0 - 0.03 + (LARGO + 0.14) * t), "aura", n=24, seccion=ak.SECCION_ROMBO,
               ancho=lambda t: (ancho(min(1, t * 1.0)) + 0.1) * (1 + 0.14 * math.sin(t * 31)) *
               (1 - suave(t, 0.9, 1.0) * 0.9) + 0.005,
               grueso=lambda t: 0.07 * (1 - 0.5 * t))
    # Neón del borde: lámina pegada a cada filo (0,01 por fuera), púrpura-rojo.
    n1 = a.pieza("Neon_01", rol="neon", studio={"color": PURPURA_ROJO})
    for s in (-1, 1):
        n1.banda(lambda t, s=s: (s * (ancho(t) + 0.02), 0, z0 + LARGO * t), (0, 1, 0), 0.026, 0.02, "neon", n=16,
                 t0=0.0, t1=0.985)

    # Guarda: orbe central negro espejo y dos garras de hueso que se abren hacia la hoja.
    ob = a.pieza("Orbe")
    ob.esfera((0, 0, zg - 0.02), 0.14, "espejo", seg=18, anillos=12)
    n3 = a.pieza("Neon_03", rol="neon", studio={"color": ROJO_OSC})
    for s, nombre in ((1, "Garra_Izq"), (-1, "Garra_Der")):
        gr = a.pieza(nombre)
        for k, (dz, dy, largo, ab) in enumerate(((0.0, 0.0, 0.62, 0.0), (-0.05, 0.06, 0.4, -0.35),
                                                  (-0.05, -0.06, 0.4, 0.35))):
            def cam(t, s=s, dz=dz, dy=dy, largo=largo, ab=ab):
                # Sale del orbe hacia fuera y se curva hacia arriba (hacia la hoja) como un dedo con garra.
                x = s * (0.1 + largo * (0.75 * t - 0.15 * t * t))
                z = zg + dz + largo * (0.05 * t + 0.75 * t ** 2.4)
                return (x, dy + ab * 0.12 * t, z)
            gr.tubo_curvo(cam, 0.05, "hueso_negro", n=10, lados=7, punta=True,
                          radio_fn=lambda t, k=k: (0.055 if k == 0 else 0.038) * (1 - 0.8 * t) *
                          (1 + 0.25 * math.exp(-((t - 0.45) / 0.07) ** 2)))
            if k == 0:  # venas rojas encima de la garra principal
                n3.cinta(lambda t, cam=cam: Vector(cam(t)) + Vector((0, -0.05 * (1 - 0.75 * t) - 0.01, 0)), 0.014,
                         lambda t: (0, -1, 0), 0.02, "venas", n=8, t0=0.05, t1=0.8)
                n3.cinta(lambda t, cam=cam: Vector(cam(t)) + Vector((0, 0.05 * (1 - 0.75 * t) + 0.01, 0)), 0.014,
                         lambda t: (0, 1, 0), 0.02, "venas", n=8, t0=0.05, t1=0.8)

    # Empuñadura: espinas negras entrelazadas en hélice alrededor de un alma, con púas.
    e = a.pieza("Empunadura", studio={"raiz": True})
    mango(e, "hueso_negro", -MANGO / 2, MANGO / 2, R_MANGO * 0.7, lados=10, anillos=6, cintura=0.0)
    for k in range(3):
        fase = k * math.tau / 3
        e.tubo_curvo(lambda t, fase=fase: (math.cos(fase + t * math.tau * 1.25) * R_MANGO * 0.78,
                                           math.sin(fase + t * math.tau * 1.25) * R_MANGO * 0.78,
                                           -MANGO / 2 + MANGO * t), 0.036, "hueso_negro", n=22, lados=6)
    rnd = random.Random(5)
    for k in range(9):  # púas cortas
        ang = k * 2.4
        zz = -MANGO / 2 + 0.1 + (MANGO - 0.2) * k / 8
        base = Vector((math.cos(ang) * R_MANGO * 1.05, math.sin(ang) * R_MANGO * 1.05, zz))
        e.cilindro(base, 0.018, 0.07, "hueso_negro", lados=5, eje=(math.cos(ang), math.sin(ang), -0.6),
                   radio2=0.001)

    # Pomo: ojo abierto que mira hacia delante (-Y), con iris rojo y pupila vertical.
    oj = a.pieza("Ojo")
    zc = -MANGO / 2 - 0.15
    oj.esfera((0, 0, zc), 0.14, "ojo", seg=16, anillos=12)
    for s in (-1, 1):  # párpados
        oj.toro((0, -0.02, zc + s * 0.045), 0.12, 0.03, "hueso_negro", seg=16, lados=6, eje=(0, 1, 0),
                arco=(math.radians(20 if s > 0 else 200), math.radians(160 if s > 0 else 340)))
    oj.esfera((0, -0.165, zc), 0.06, "pupila", seg=8, anillos=6, escala=(0.22, 0.2, 1.0))
    n2 = a.pieza("Neon_02", rol="neon", studio={"color": ROJO})
    n2.esfera((0, -0.13, zc), 0.08, "iris", seg=14, anillos=6, escala=(1, 0.3, 1))

    # 8 fragmentos triangulares que flotan alrededor de la hoja.
    for i in range(8):
        ang = rnd.uniform(0, math.tau)
        zz = z0 + LARGO * rnd.uniform(0.1, 0.9)
        R = rnd.uniform(0.3, 0.5)
        fr = a.pieza(f"Fragmento_0{i + 1}")
        fr.fragmento((math.cos(ang) * R, math.sin(ang) * R * 0.6, zz), rnd.uniform(0.13, 0.19), "hueso_negro",
                     giro=Matrix.Rotation(rnd.uniform(0, 3), 3, "X") @ Matrix.Rotation(rnd.uniform(0, 3), 3, "Z"),
                     rnd=rnd, lados=3)

    a.agarre("Handle", (0, 0, 0), (0, 0, 1))
    return a



# ==============================================================================================================
# CATEGORÍA 2: ARMAS PESADAS (dos manos). El mango va a lo largo de Z y la cabeza arriba. "Handle" es la mano de
# abajo (derecha) y "Handle_Frontal" la de arriba (izquierda).
# ==============================================================================================================


def hacha_meteorito():
    """#6 Hacha de Meteorito (Poco común). Cabeza asimétrica de hierro meteorítico con rocas incrustadas."""
    MANGO = 2.0
    ZC = 0.72  # centro de la cabeza
    paleta = {
        "hierro": {"color": "#4A4643", "rug": 0.45, "met": 1.0, "patron": "widman", "relieve": 1.1,
                   "color2": "#6B655E", "mezcla": ("manchas", 3.0, 0.6)},
        "filo": {"color": "#A9A49C", "rug": 0.25, "met": 1.0, "patron": "cepillado", "relieve": 0.4},
        "roca": {"color": "#4A4540", "rug": 0.9, "met": 0.0, "patron": "roca", "relieve": 1.6,
                 "color2": "#E8792A", "mezcla": ("manchas", 6.0, 0.62)},
        "madera": {"color": "#3A2516", "rug": 0.7, "met": 0.0, "patron": "madera", "relieve": 1.0,
                   "color2": "#24160C", "mezcla": ("vetas", 1.4, 0.75)},
        "acero": {"color": "#6E6A64", "rug": 0.35, "met": 1.0, "patron": "cepillado", "relieve": 0.5},
        "neon": NEON,
    }
    a = ak.Arma("HachaMeteorito", "hacha_meteorito.fbx", "PocoComun", paleta, "Hacha de Meteorito")

    # Cabeza: rejilla de secciones desde el ojo (x = 0,1) hasta el filo curvo (x ≈ 0,62).
    cab = a.pieza("Cabeza", studio={"raiz": True})
    bm = cab.bm
    NS, NZ = 9, 9

    def x_filo(z):
        return 0.6 + 0.09 * (1 - ((z - ZC) / 0.5) ** 2)

    anillos = []
    for i in range(NS + 1):
        s_ = i / NS
        e_ = s_ ** 1.5
        zlo = (ZC - 0.2) + ((ZC - 0.5) - (ZC - 0.2)) * e_
        zhi = (ZC + 0.2) + ((ZC + 0.5) - (ZC + 0.2)) * e_
        th = 0.085 + (0.006 - 0.085) * s_ ** 0.75
        frente, atras = [], []
        for j in range(NZ):
            z = zlo + (zhi - zlo) * j / (NZ - 1)
            x = 0.1 + (x_filo(z) - 0.1) * s_
            # El bisel del filo: la cara se estrecha en el último 15 %.
            frente.append(Vector((x, th, z)))
            atras.append(Vector((x, -th, z)))
        anillos.append(frente + list(reversed(atras)))
    vs = [[bm.verts.new(p) for p in an] for an in anillos]
    n = len(anillos[0])
    caras = []
    for A, B in zip(vs, vs[1:]):
        for k in range(n):
            j = (k + 1) % n
            caras.append(bm.faces.new((A[k], A[j], B[j], B[k])))
    caras.append(bm.faces.new(list(reversed(vs[0]))))
    caras.append(bm.faces.new(vs[-1]))
    for f in caras:
        cx = sum(v.co.x for v in f.verts) / len(f.verts)
        f.material_index = cab.m("filo" if cx > 0.5 else "hierro")
    # Ojo (donde entra el mango) y contrapeso cuadrado al otro lado.
    cab.caja((0, 0, ZC), (0.24, 0.2, 0.44), "hierro")
    cab.caja((-0.26, 0, ZC), (0.3, 0.2, 0.3), "hierro")
    cab.caja((-0.42, 0, ZC), (0.06, 0.24, 0.34), "acero")
    for s in (-1, 1):  # remaches
        for zz in (ZC - 0.1, ZC + 0.1):
            cab.cilindro((0.0, s * 0.1, zz), 0.025, 0.02, "acero", lados=6, eje=(0, s, 0))
    # Cuña de fijación que asoma por encima del ojo.
    cab.perfil_x([(-0.07, ZC + 0.22), (0.07, ZC + 0.22), (0.03, ZC + 0.31), (-0.03, ZC + 0.31)], -0.05, 0.05,
                 "acero")

    # Fragmentos de meteorito incrustados en la parte de arriba de la cabeza.
    rnd = random.Random(6)
    r = a.pieza("Roca")
    n1 = a.pieza("Neon_01", rol="neon")
    rocas = ((-0.3, ZC + 0.14, 0.13), (-0.08, ZC + 0.2, 0.12), (0.17, ZC + 0.26, 0.12), (0.36, ZC + 0.36, 0.11),
             (0.52, ZC + 0.45, 0.08), (-0.44, ZC + 0.12, 0.09))
    for k, (x, z, t) in enumerate(rocas):
        r.roca((x, rnd.uniform(-0.02, 0.02), z), t, "roca", rnd, sub=2, aplastar=(1.15, 0.85, 0.75))
    for (x0, z0_, _), (x1, z1, _) in zip(rocas, rocas[1:]):
        # Veta de mineral que brilla en la junta entre dos rocas (y una esquirla que asoma).
        cen = Vector(((x0 + x1) / 2, 0.0, (z0_ + z1) / 2 + 0.02))
        n1.fragmento(cen, 0.12, "neon", giro=Matrix.Rotation(rnd.uniform(-0.5, 0.5), 3, "Y"), rnd=rnd, lados=4)
    for lado in (-1, 1):
        for k in range(3):  # grietas brillantes en zigzag en las caras de la cabeza, bajo las rocas
            x0 = -0.28 + 0.27 * k
            puntos = [(x0, ZC + 0.2), (x0 + 0.05, ZC + 0.14), (x0 + 0.01, ZC + 0.09), (x0 + 0.07, ZC + 0.02)]
            for (xa, za), (xb, zb) in zip(puntos, puntos[1:]):
                n1.cinta(lambda t, xa=xa, za=za, xb=xb, zb=zb, lado=lado:
                         (xa + (xb - xa) * t, lado * (0.1 + 0.01), za + (zb - za) * t),
                         0.016, lambda t, lado=lado: (0, lado, 0), 0.02, "neon", n=1)

    # Mango de madera, un poco ovalado, con anillos de refuerzo.
    m = a.pieza("Mango")
    secs = []
    for i in range(9):
        t = i / 8
        z = -MANGO / 2 + (ZC + 0.24 + MANGO / 2) * t
        k = 1 + 0.12 * math.exp(-((t - 0.05) / 0.06) ** 2)
        secs.append(kitanillo(z, 0.07 * k, 0.058 * k, 12))
    m.loft(secs, "madera")
    an = a.pieza("Anillos")
    for zz in (-0.95, -0.55, 0.05, ZC - 0.32):
        an.cilindro((0, 0, zz - 0.03), 0.082, 0.06, "acero", lados=12)
        an.toro((0, 0, zz), 0.083, 0.012, "acero", seg=12, lados=4)
    an.cilindro((0, 0, -MANGO / 2 - 0.05), 0.085, 0.07, "acero", lados=12, radio2=0.075)

    a.agarre("Handle", (0, 0, -0.75), (0, 0, 1))
    a.agarre("Handle_Frontal", (0, 0, -0.2), (0, 0, 1))
    return a


def kitanillo(z, rx, ry, n):
    return ak.kit.anillo_z(z, rx, ry, n)


def martillo_pulsar():
    """#7 Martillo de Pulsar (Épico). Cabeza tecnológica con núcleo de púlsar a la vista, cara plana y punta."""
    MANGO = 2.2
    HX, HY, HZ = 0.8, 0.5, 0.6
    ZC = MANGO / 2 + HZ / 2 - 0.05
    paleta = {
        "blindaje": {"color": "#737C88", "rug": 0.35, "met": 1.0, "patron": "paneles", "relieve": 0.9},
        "oscuro": {"color": "#22262C", "rug": 0.4, "met": 1.0, "patron": "cepillado", "relieve": 0.5},
        "cara": {"color": "#8D949E", "rug": 0.3, "met": 1.0, "patron": "fundido", "relieve": 0.5},
        "acento": {"color": "#C9CFD6", "rug": 0.15, "met": 1.0},
        "goma": {"color": "#141517", "rug": 0.8, "met": 0.0, "patron": "polimero", "relieve": 1.0},
        "vidrio": {"color": "#BFF6FF", "rug": 0.05, "met": 0.0, "alfa": 0.3},
        "neon": NEON,
    }
    a = ak.Arma("MartilloPulsar", "martillo_pulsar.fbx", "Epico", paleta, "Martillo de Pulsar")
    a.notas.append("Épico: añadir en Studio un ParticleEmitter cian suave alrededor del núcleo (aura)")
    W = 0.17  # semiancho de la ventana del núcleo

    cab = a.pieza("Cabeza", studio={"bisel": 0.025})
    # Dos bloques a los lados de la ventana del núcleo, unidos por arriba y por abajo.
    for s in (-1, 1):
        cab.caja((s * (W + (HX / 2 - W) / 2), 0, ZC), (HX / 2 - W, HY, HZ), "blindaje")
    cab.caja((0, 0, ZC + HZ / 2 - 0.07), (2 * W + 0.02, HY, 0.14), "blindaje")
    cab.caja((0, 0, ZC - HZ / 2 + 0.07), (2 * W + 0.02, HY, 0.14), "blindaje")
    # Placa de la cara plana (+X) con reborde, y collarín de la punta (-X).
    cab.caja((HX / 2 + 0.04, 0, ZC), (0.08, HY + 0.06, HZ + 0.06), "cara")
    cab.caja((-HX / 2 - 0.03, 0, ZC), (0.06, HY - 0.06, HZ - 0.06), "oscuro")
    # Marcos de la ventana del núcleo.
    for lado in (-1, 1):
        cab.toro((0, lado * HY / 2, ZC), W - 0.005, 0.03, "acento", seg=20, lados=4, eje=(0, 1, 0),
                 escala_r=(0.8, 1.2))
    # Abrazadera del mango.
    cab.cilindro((0, 0, ZC - HZ / 2 - 0.16), 0.1, 0.18, "oscuro", lados=8, radio2=0.13)

    p = a.pieza("Punta")
    p.cilindro((-HX / 2 - 0.06, 0, ZC), 0.19, 0.36, "oscuro", lados=8, eje=(-1, 0, 0), radio2=0.012)
    p.cilindro((-HX / 2 - 0.06, 0, ZC), 0.21, 0.05, "acento", lados=8, eje=(-1, 0, 0), radio2=0.19)

    nu = a.pieza("Nucleo", rol="cristal", studio={"color": "#9FEFFF", "transparencia": 0.55})
    nu.cilindro((0, -HY / 2 - 0.01, ZC), W - 0.02, HY + 0.02, "vidrio", lados=20, eje="Y")
    n1 = a.pieza("Neon_01", rol="neon", studio={"nota": "Núcleo: pulsar animando Color/Transparency o un "
                                                        "PointLight cian que sube y baja"})
    n1.esfera((0, 0, ZC), 0.11, "neon", seg=16, anillos=10)
    n1.toro((0, 0, ZC), 0.13, 0.008, "neon", seg=20, lados=3, eje=(1, 0, 0.4))

    # Conductos: 3 por cara de impacto, del núcleo a cada cara (delante, detrás y arriba).
    co = a.pieza("Conductos")
    n2 = a.pieza("Neon_02", rol="neon")
    rutas = [((0, -HY / 2 - 0.035, 0.13), (0, -1, 0)), ((0, HY / 2 + 0.035, 0.13), (0, 1, 0)),
             ((0, 0, HZ / 2 + 0.035), (0, 0, 1))]
    for s in (-1, 1):
        for (_, y, z), nrm in rutas:
            p0 = Vector((s * (W + 0.02), y, ZC + (z if z > 0.2 else -0.16 if s < 0 else 0.16)))
            p1 = Vector((s * (HX / 2 - 0.02), y, p0.z))
            co.cilindro(p0, 0.035, (p1 - p0).length, "oscuro", lados=8, eje=(s, 0, 0))
            for xx in (p0.x + s * 0.02, p1.x - s * 0.03):
                co.cilindro(Vector((xx - s * 0.015, y, p0.z)), 0.045, 0.03, "acento", lados=8, eje=(s, 0, 0))
            n2.caja((p0 + p1) / 2 + Vector(nrm) * 0.045, (abs(p1.x - p0.x) - 0.08, 0.02, 0.02) if nrm[2] == 0
                    else (abs(p1.x - p0.x) - 0.08, 0.02, 0.02), "neon")
    # Neón 3: líneas en las caras de impacto (cruz en la cara plana y anillo en la base de la punta).
    n3 = a.pieza("Neon_03", rol="neon")
    xf = HX / 2 + 0.08 + 0.02
    n3.caja((xf, 0, ZC), (0.02, HY - 0.08, 0.03), "neon")
    n3.caja((xf, 0, ZC), (0.02, 0.03, HZ - 0.08), "neon")
    n3.toro((xf, 0, ZC), 0.14, 0.01, "neon", seg=16, lados=4, eje=(1, 0, 0))
    n3.toro((-HX / 2 - 0.12, 0, ZC), 0.17, 0.01, "neon", seg=8, lados=4, eje=(1, 0, 0))

    # Mango: tubo metálico con grip de goma en el tercio inferior y contrapeso.
    mg = a.pieza("Mango")
    mg.cilindro((0, 0, -MANGO / 2), 0.06, MANGO, "oscuro", lados=12)
    for zz in (0.0, 0.35, 0.7):
        mg.toro((0, 0, zz), 0.064, 0.012, "acento", seg=12, lados=4)
    gr = a.pieza("Grip", studio={"raiz": True})
    mango(gr, "goma", -MANGO / 2 + 0.06, -MANGO / 2 + 0.06 + MANGO / 3, 0.078, lados=14, anillos=12, cintura=0.0,
          estrias=0.1, n_estrias=9)
    cp = a.pieza("Contrapeso", studio={"bisel": 0.015})
    cp.cilindro((0, 0, -MANGO / 2 - 0.1), 0.14, 0.12, "oscuro", lados=16)
    cp.cilindro((0, 0, -MANGO / 2 - 0.13), 0.1, 0.03, "acento", lados=16)

    a.agarre("Handle", (0, 0, -MANGO / 2 + 0.3), (0, 0, 1))
    a.agarre("Handle_Frontal", (0, 0, 0.35), (0, 0, 1))
    return a


def guadana_nebular():
    """#8 Guadaña Nebular (Legendario). Hoja de nebulosa en arco con jirones, bastón octogonal con runas y gema."""
    LARGO_MANGO = 3.0
    R = 2.0
    Z_TOP = 1.6
    C = Vector((0.0, Z_TOP - R))
    A0, A1 = math.radians(86), math.radians(146)
    paleta = {
        "nebulosa": {"color": "#45E8FF", "rug": 0.0, "met": 0.0, "color2": "#3A0F78",
                     "mezcla": ("grad", "X", -1.9, -0.5), "patron": "cristalino", "relieve": 0.5,
                     "nubes": ("#C24BFF", 3.0, 0.55)},
        "wisp": {"color": "#FFFFFF", "rug": 0.0, "met": 0.0, "alfa": 0.78},
        "madera": {"color": "#141110", "rug": 0.6, "met": 0.0, "patron": "madera", "relieve": 1.0,
                   "color2": "#C9A24A", "mezcla": ("vetas", 1.5, 0.86)},
        "oro": {"color": "#B9933F", "rug": 0.25, "met": 1.0, "patron": "grabado", "relieve": 0.8},
        "plata": {"color": "#AEB6C2", "rug": 0.2, "met": 1.0},
        "gema": {"color": "#1636B8", "rug": 0.05, "met": 0.0, "alfa": 0.75},
        "neon": NEON,
    }
    a = ak.Arma("GuadanaNebular", "guadana_nebular.fbx", "Legendario", paleta, "Guadaña Nebular")
    a.notas.append("Hoja = textura de nebulosa; Neon_01 es el filo que brilla (la hoja entera en Neon taparía la "
                   "textura)")

    def camino(t):
        ang = A0 + (A1 - A0) * t
        return (C.x + R * math.cos(ang), C.y + R * math.sin(ang))

    def ancho(t):
        return (0.3 - 0.25 * t ** 1.3) / 2 * (1 - suave(t, 0.9, 1.0) * 0.9)

    def grueso(t):
        return 0.03 * (1 - 0.6 * t)

    sec = [(-u, v) for u, v in ak.SECCION_SABLE]  # filo en el lado cóncavo (u = -1, hacia el mango)

    def desvio(t):
        return -ancho(t) * 0.2

    h = a.pieza("Hoja")
    h.barrido(camino, "nebulosa", n=22, seccion=sec, ancho=ancho, grueso=grueso, desvio=desvio)
    sup = sup_hoja(camino, ancho, grueso, desvio, sec)

    # Jirones gaseosos que salen del lomo (lado convexo) y se curvan hacia atrás como llamas.
    w = a.pieza("Wisps")
    rnd = random.Random(8)
    for k in range(8):
        t = 0.08 + 0.11 * k
        p0 = sup(t, 0.95, 1, -grueso(t))
        tg = ak._tangente(camino, t)
        nrm = Vector((tg.y, 0, -tg.x))
        tg3 = Vector((tg.x, 0, tg.y))
        L = rnd.uniform(0.22, 0.36) * (1 - 0.45 * t)
        for lado in (-1, 1):  # llama plana en S, una por cara (con volumen: 0,016 de grosor)
            w.cinta(lambda u, p0=p0, nrm=nrm, tg3=tg3, L=L, lado=lado, f=rnd.uniform(0, 3):
                    p0 + Vector((0, lado * 0.004, 0)) + nrm * L * u + tg3 * (0.55 * L * u * u +
                                                                              0.05 * math.sin(f + u * 6)),
                    0.06, lambda u, lado=lado: (0, lado, 0), 0.016, "wisp", n=7,
                    ancho_fn=lambda u: 0.08 * (1 - u) ** 0.9 + 0.006)

    n1 = a.pieza("Neon_01", rol="neon")
    for lado in (-1, 1):
        n1.cinta(lambda t, lado=lado: sup(t, -0.55, lado, 0.01), 0.04, lambda t, lado=lado: (0, lado, 0), 0.02,
                 "neon", n=18, t0=0.04, t1=0.95, ancho_fn=lambda t: 0.04 * (1 - 0.6 * t))

    # Bastón octogonal, un poco curvado.
    def eje_baston(z):
        return 0.05 * math.sin((z + 1.4) / LARGO_MANGO * math.pi)

    m = a.pieza("Mango", studio={"raiz": True, "suavizado": 30})
    z_bajo = Z_TOP - LARGO_MANGO
    secs = []
    for i in range(13):
        z = z_bajo + LARGO_MANGO * i / 12
        rr = 0.068 * (1 + 0.1 * math.exp(-((i - 6) / 2.0) ** 2))
        secs.append(ak.kit.anillo_z(z, rr, rr, 8, xc=eje_baston(z), giro=math.pi / 8))
    m.loft(secs, "madera")
    # Garra metálica en la punta inferior que sujeta la gema.
    zg = z_bajo - 0.16
    for k in range(3):
        ang = k * math.tau / 3
        m.tubo_curvo(lambda t, ang=ang: (math.cos(ang) * (0.06 + 0.06 * math.sin(t * 2.6)) + eje_baston(z_bajo),
                                         math.sin(ang) * (0.06 + 0.06 * math.sin(t * 2.6)), z_bajo + 0.04 - 0.3 * t),
                     0.02, "oro", n=6, lados=5, punta=True, radio_fn=lambda t: 0.022 * (1 - 0.7 * t))
    m.cilindro((eje_baston(z_bajo), 0, z_bajo - 0.04), 0.075, 0.1, "oro", lados=8)

    # Runas en relieve a lo largo del bastón (dos columnas en caras opuestas).
    ru = a.pieza("Runas")
    n2 = a.pieza("Neon_02", rol="neon")
    glifos = [[(0, -1), (0, 1), (0.8, 0.4)], [(-0.8, 1), (0, -1), (0.8, 1)], [(-0.8, -0.6), (0.8, 0.6)],
              [(-0.8, 0), (0.8, 0), (0, 1)], [(0, -1), (0, 1)], [(-0.8, 1), (0.8, -1)]]
    for col, ang in enumerate((0.0, math.pi)):
        nrm = Vector((math.cos(ang), math.sin(ang), 0))
        tan = Vector((-math.sin(ang), math.cos(ang), 0))
        for k in range(6):
            zz = z_bajo + 0.9 + 0.22 * k + col * 0.11
            rr = 0.068 * math.cos(math.pi / 8) + 0.001
            base = Vector((eje_baston(zz), 0, zz)) + nrm * rr
            gl = glifos[(k + col * 3) % len(glifos)]
            for (u0, v0), (u1, v1) in zip(gl, gl[1:]):
                p0 = base + tan * u0 * 0.03 + Vector((0, 0, v0 * 0.05))
                p1 = base + tan * u1 * 0.03 + Vector((0, 0, v1 * 0.05))
                d = p1 - p0
                ez = d.normalized()
                giro = Matrix((ez.cross(nrm), nrm, ez)).transposed()
                ru.caja((p0 + p1) / 2 + nrm * 0.008, (0.016, 0.018, d.length + 0.016), "oro", giro=giro)
                n2.caja((p0 + p1) / 2 + nrm * 0.027, (0.009, 0.02, d.length + 0.008), "neon", giro=giro)

    # Conexión hoja-mango: anillo ornamental con 3 púas.
    an = a.pieza("Anillo")
    an.toro((eje_baston(Z_TOP - 0.1), 0, Z_TOP - 0.1), 0.095, 0.035, "oro", seg=16, lados=6)
    an.toro((eje_baston(Z_TOP - 0.24), 0, Z_TOP - 0.24), 0.085, 0.025, "oro", seg=16, lados=6)
    an.esfera((0, 0, Z_TOP + 0.02), 0.1, "oro", seg=12, anillos=8, escala=(1, 1, 0.9))
    pu = a.pieza("Puas")
    for k, (dx, dz) in enumerate(((0.6, 0.6), (0.9, -0.1), (0.4, -0.85))):
        d = Vector((dx, 0, dz)).normalized()
        pu.cilindro(Vector((0, 0, Z_TOP - 0.05)) + d * 0.08, 0.04, 0.26, "plata", lados=6, eje=d, radio2=0.002)

    gm = a.pieza("Gema")
    gm.esfera((eje_baston(z_bajo), 0, zg), 0.1, "gema", seg=8, anillos=6, escala=(1, 1, 1.35))
    n3 = a.pieza("Neon_03", rol="neon")
    n3.esfera((eje_baston(z_bajo), 0, zg), 0.045, "neon", seg=8, anillos=5, escala=(1, 1, 1.3))

    a.agarre("Handle", (eje_baston(-0.8), 0, -0.8), (0, 0, 1))
    a.agarre("Handle_Frontal", (eje_baston(0.4), 0, 0.4), (0, 0, 1))
    return a



# ==============================================================================================================
# CATEGORÍA 3: PISTOLAS (una mano). El cañón apunta a -Y (delante), arriba es +Z y el ancho va en X.
# El Handle está en el centro del grip con el eje Y hacia la boca del cañón.
# ==============================================================================================================

VIDRIO = {"color": "#BFF6FF", "rug": 0.05, "met": 0.0, "alfa": 0.35}


def gatillo_y_guarda(p, mat, y_frente, y_atras, z_techo, z_fondo, ancho=0.05, grosor=0.03, mat_g=None):
    """Gatillo curvo y guarda en lazo (espacio para el dedo), en el plano YZ."""
    yc = (y_frente + y_atras) / 2
    guarda = spline([(0, y_frente, z_techo + 0.01), (0, y_frente + 0.01, z_fondo + 0.05),
                     (0, yc, z_fondo), (0, y_atras - 0.02, z_fondo + 0.02), (0, y_atras, z_techo - 0.08)])
    p.banda(guarda, (1, 0, 0), ancho, grosor, mat_g or mat, n=14)
    gat = spline([(0, yc + 0.02, z_techo + 0.01), (0, yc - 0.01, z_techo - 0.07), (0, yc + 0.02, z_fondo + 0.07)])
    p.banda(gat, (1, 0, 0), 0.04, 0.022, mat, n=8, grosor_fn=lambda t: 0.03 - 0.012 * t)


def pistola_plasma():
    """#9 Pistola de Plasma (Común). Militar y angular: cañón cuadrado, celda de energía trasera, miras."""
    paleta = {
        "gunmetal": {"color": "#666D77", "rug": 0.3, "met": 1.0, "patron": "cepillado", "relieve": 0.4},
        "oscuro": {"color": "#2E3238", "rug": 0.35, "met": 1.0},
        "polimero": {"color": "#121315", "rug": 0.75, "met": 0.0, "patron": "polimero", "relieve": 1.0},
        "vidrio": VIDRIO,
        "neon": NEON,
    }
    a = ak.Arma("PistolaPlasma", "pistola_plasma.fbx", "Comun", paleta, "Pistola de Plasma")
    ZB = 0.25  # eje del cañón

    cu = a.pieza("Cuerpo", studio={"bisel": 0.012})
    cu.perfil_x_biselado([(-0.42, 0.12), (-0.42, 0.31), (-0.37, 0.37), (0.3, 0.37), (0.42, 0.33), (0.44, 0.2),
                          (0.36, 0.12)], 0.2, 0.035, "gunmetal")
    cu.perfil_x_biselado([(-0.4, 0.05), (-0.4, 0.13), (0.1, 0.13), (0.12, 0.07)], 0.16, 0.025, "oscuro")
    for s in (-1, 1):  # estrías de la corredera
        for k in range(4):
            cu.caja((s * 0.1, 0.12 + k * 0.05, 0.27), (0.012, 0.018, 0.12), "oscuro")
    # Miras: poste delante y ranura en U detrás.
    cu.caja((0, -0.66, ZB + 0.11), (0.03, 0.05, 0.08), "oscuro")
    for s in (-1, 1):
        cu.caja((s * 0.045, 0.36, 0.4), (0.035, 0.05, 0.07), "oscuro")
    cu.caja((0, 0.36, 0.38), (0.13, 0.05, 0.03), "oscuro")
    # Alojamiento de la celda (encima, detrás).
    cu.caja((0, 0.13, 0.4), (0.15, 0.32, 0.06), "oscuro")

    ca = a.pieza("Canon")
    ca.tubo((0, -0.25, ZB), (0, -1, 0), 0.5, 0.075, 0.042, "gunmetal", lados=16, cuad_ext=6.0, mat_int="oscuro")
    ca.tubo((0, -0.7, ZB), (0, -1, 0), 0.05, 0.085, 0.042, "oscuro", lados=16, cuad_ext=6.0)

    gr = a.pieza("Grip", studio={"raiz": True, "bisel": 0.01})
    t15 = math.tan(math.radians(15))
    pts = [(-0.04, 0.12), (0.2, 0.12), (0.2 + 0.5 * t15, -0.38), (0.2 + 0.56 * t15 - 0.04, -0.44),
           (0.0 + 0.56 * t15, -0.44), (-0.04 + 0.5 * t15, -0.38)]
    # Ondulaciones para los dedos en el frente del grip.
    frente = [(-0.04 + t15 * (0.12 - z) + 0.018 * math.sin((0.12 - z) / 0.5 * 3 * math.pi) ** 2, z)
              for z in (0.0, -0.08, -0.16, -0.24, -0.32)]
    gr.perfil_x_biselado(pts[:5] + [pts[5]] + list(reversed(frente)), 0.18, 0.03, "polimero")
    gr.caja((0, 0.2 + 0.56 * t15 - 0.1, -0.455), (0.17, 0.2, 0.04), "oscuro")

    g = a.pieza("Gatillo")
    gatillo_y_guarda(g, "oscuro", -0.22, 0.0, 0.07, -0.08)

    ce = a.pieza("Celda", rol="cristal", studio={"color": "#7FEFFF", "transparencia": 0.45})
    ce.cilindro((0, 0.0, 0.46), 0.05, 0.26, "vidrio", lados=14, eje="Y")
    n2 = a.pieza("Neon_02", rol="neon")
    n2.cilindro((0, 0.02, 0.46), 0.025, 0.22, "neon", lados=10, eje="Y")
    for yy in (0.0, 0.26):  # casquillos de la celda
        cu.cilindro((0, yy - 0.02, 0.46), 0.058, 0.04, "oscuro", lados=14, eje="Y")

    n1 = a.pieza("Neon_01", rol="neon")
    for s in (-1, 1):
        n1.caja((s * (0.1 + 0.02), -0.12, 0.2), (0.02, 0.42, 0.025), "neon")

    a.agarre("Handle", (0, 0.08 + 0.28 * t15, -0.16), (0, -1, 0))
    return a


def laser_precision():
    """#10 Láser de Precisión (Raro). Pistola de tirador: cañón largo con disipador, mira holográfica, trípode."""
    paleta = {
        "blanco": {"color": "#D9DEE4", "rug": 0.25, "met": 0.6, "patron": "paneles", "relieve": 0.35},
        "gunmetal": {"color": "#33373D", "rug": 0.3, "met": 1.0, "patron": "cepillado", "relieve": 0.4},
        "aletas": {"color": "#8A929C", "rug": 0.2, "met": 1.0},
        "polimero": {"color": "#16181B", "rug": 0.7, "met": 0.0, "patron": "polimero", "relieve": 1.0},
        "vidrio": VIDRIO,
        "neon": NEON,
    }
    a = ak.Arma("LaserPrecision", "laser_precision.fbx", "Raro", paleta, "Láser de Precisión")
    ZB = 0.22

    cu = a.pieza("Cuerpo", studio={"bisel": 0.01})
    cu.perfil_x_biselado([(-0.5, 0.1), (-0.5, 0.27), (-0.44, 0.32), (0.4, 0.32), (0.58, 0.26), (0.62, 0.16),
                          (0.5, 0.08), (0.2, 0.08), (0.12, 0.1)], 0.17, 0.035, "blanco")
    cu.perfil_x_biselado([(-0.48, 0.12), (-0.48, 0.2), (0.45, 0.2), (0.45, 0.12)], 0.19, 0.02, "gunmetal")
    # Riel superior para la mira.
    cu.caja((0, -0.05, 0.345), (0.07, 0.6, 0.05), "gunmetal")
    for k in range(7):
        cu.caja((0, -0.3 + k * 0.08, 0.375), (0.09, 0.03, 0.02), "gunmetal")

    ca = a.pieza("Canon")
    ca.tubo((0, -0.42, ZB), (0, -1, 0), 0.8, 0.045, 0.022, "gunmetal", lados=14, mat_int="gunmetal")
    for k in range(7):  # disipador de calor
        ca.cilindro((0, -0.56 - k * 0.05, ZB), 0.075, 0.018, "aletas", lados=14, eje=(0, -1, 0))
    ca.tubo((0, -1.12, ZB), (0, -1, 0), 0.1, 0.06, 0.03, "gunmetal", lados=14)

    mi = a.pieza("Mira", studio={"bisel": 0.006})
    YM, ZM0, ZM1, XM = -0.02, 0.43, 0.63, 0.13
    mi.caja((0, YM + 0.04, 0.39), (0.12, 0.16, 0.04), "gunmetal")  # base sobre el riel
    mi.caja((0, YM, ZM0 - 0.015), (2 * XM + 0.03, 0.04, 0.03), "gunmetal")
    mi.caja((0, YM, ZM1 + 0.015), (2 * XM + 0.03, 0.04, 0.03), "gunmetal")
    for s in (-1, 1):
        mi.caja((s * XM, YM, (ZM0 + ZM1) / 2), (0.03, 0.04, ZM1 - ZM0 + 0.06), "gunmetal")
    cr = a.pieza("Cristal", rol="cristal", studio={"color": "#9FEFFF", "transparencia": 0.6})
    cr.caja((0, YM, (ZM0 + ZM1) / 2), (2 * XM - 0.03, 0.012, ZM1 - ZM0), "vidrio")
    n1 = a.pieza("Neon_01", rol="neon", studio={"nota": "Retícula: Transparency 0,2 para que se vea a través"})
    yr = YM + 0.006 + 0.01 + 0.01  # detrás del cristal, mirando al tirador
    n1.toro((0, yr, (ZM0 + ZM1) / 2), 0.055, 0.006, "neon", seg=20, lados=4, eje=(0, 1, 0))
    n1.caja((0, yr, (ZM0 + ZM1) / 2 + 0.04), (0.008, 0.02, 0.05), "neon")
    n1.caja((0, yr, (ZM0 + ZM1) / 2 - 0.04), (0.008, 0.02, 0.05), "neon")
    n1.caja((0.04, yr, (ZM0 + ZM1) / 2), (0.05, 0.02, 0.008), "neon")
    n1.caja((-0.04, yr, (ZM0 + ZM1) / 2), (0.05, 0.02, 0.008), "neon")
    n1.esfera((0, yr, (ZM0 + ZM1) / 2), 0.01, "neon", seg=6, anillos=4)

    gr = a.pieza("Grip", studio={"raiz": True, "bisel": 0.01})
    t = math.tan(math.radians(18))
    gr.perfil_x_biselado([(0.18, 0.1), (0.42, 0.1), (0.42 + 0.5 * t, -0.36), (0.36 + 0.55 * t, -0.42),
                          (0.18 + 0.55 * t, -0.42), (0.13 + 0.4 * t, -0.3), (0.16 + 0.2 * t, -0.15)], 0.17, 0.035,
                         "polimero")
    gatillo_y_guarda(gr, "gunmetal", -0.04, 0.17, 0.08, -0.1)

    es = a.pieza("Estabilizador")
    es.caja((0, -0.45, ZB - 0.08), (0.1, 0.08, 0.06), "gunmetal")
    for k, dx in enumerate((-0.035, 0.0, 0.035)):
        es.tubo_curvo(lambda u, dx=dx: (dx * (1 + 0.6 * u), -0.47 - 0.45 * u, ZB - 0.1 - 0.012 * abs(dx) * 30 * u),
                      0.012, "aletas", n=2, lados=6)
        es.esfera((dx * 1.6, -0.92, ZB - 0.1 - 0.012 * abs(dx) * 30), 0.018, "polimero", seg=6, anillos=4)

    n2 = a.pieza("Neon_02", rol="neon")
    for s in (-1, 1):
        n2.caja((s * (0.085 + 0.02), -0.05, 0.27), (0.02, 0.75, 0.022), "neon")
    n3 = a.pieza("Neon_03", rol="neon")
    n3.toro((0, -1.225, ZB), 0.045, 0.01, "neon", seg=16, lados=4, eje=(0, 1, 0))

    a.agarre("Handle", (0, 0.3 + 0.15 * t, -0.15), (0, -1, 0))
    return a


def blaster_iones():
    """#11 Blaster de Iones (Poco común). Cuerpo agresivo y ancho, dos cañones hexagonales y rejillas."""
    paleta = {
        "carroceria": {"color": "#4A525E", "rug": 0.28, "met": 1.0, "patron": "cepillado", "relieve": 0.4},
        "acento": {"color": "#8C96A3", "rug": 0.3, "met": 1.0},
        "negro": {"color": "#111215", "rug": 0.6, "met": 0.2},
        "polimero": {"color": "#16171A", "rug": 0.75, "met": 0.0, "patron": "polimero", "relieve": 1.0},
        "neon": NEON,
    }
    a = ak.Arma("BlasterIones", "blaster_iones.fbx", "PocoComun", paleta, "Blaster de Iones")
    ZB = 0.24
    SEP = 0.075  # medio paso entre cañones

    cu = a.pieza("Cuerpo", studio={"bisel": 0.012})
    cu.perfil_x_biselado([(-0.38, 0.1), (-0.38, 0.28), (-0.2, 0.36), (0.2, 0.4), (0.4, 0.38), (0.44, 0.26),
                          (0.38, 0.1)], 0.32, 0.06, "carroceria")
    cu.perfil_x_biselado([(-0.36, 0.06), (-0.36, 0.12), (0.12, 0.12), (0.14, 0.08)], 0.22, 0.03, "acento")
    # Aleta superior y espolones laterales (silueta de coche deportivo).
    cu.perfil_x([(-0.15, 0.37), (0.25, 0.41), (0.35, 0.47), (0.0, 0.39)], -0.02, 0.02, "acento")
    for s in (-1, 1):
        cu.perfil_x([(-0.42, 0.18), (-0.3, 0.3), (0.0, 0.26), (0.1, 0.16)], s * 0.16, s * 0.2, "acento")
    n2 = a.pieza("Neon_02", rol="neon", studio={"nota": "Rejillas: subir el brillo al disparar"})
    for s in (-1, 1):  # rejilla de ventilación: lamas sobre una ranura que brilla
        n2.caja((s * (0.16 + 0.01 + 0.01), 0.18, 0.25), (0.02, 0.3, 0.07), "neon")
        for k in range(6):
            cu.caja((s * (0.16 + 0.035), 0.05 + k * 0.05, 0.25), (0.025, 0.018, 0.09), "negro",
                    giro=Matrix.Rotation(0.4, 3, "X"))

    n1 = a.pieza("Neon_01", rol="neon")
    for s, nombre in ((1, "Canon_Izq"), (-1, "Canon_Der")):
        ca = a.pieza(nombre)
        x = s * SEP
        ca.tubo((x, -0.3, ZB), (0, -1, 0), 0.42, 0.065, 0.04, "carroceria", lados=6, giro=math.pi / 6,
                mat_int="negro")
        ca.tubo((x, -0.66, ZB), (0, -1, 0), 0.06, 0.075, 0.04, "acento", lados=6, giro=math.pi / 6)
        n1.tubo((x, -0.62, ZB), (0, -1, 0), 0.08, 0.038, 0.026, "neon", lados=6, giro=math.pi / 6)

    gr = a.pieza("Grip", studio={"raiz": True, "bisel": 0.01})
    t = math.tan(math.radians(17))
    gr.perfil_x_biselado([(0.04, 0.1), (0.3, 0.1), (0.3 + 0.42 * t, -0.3), (0.06 + 0.42 * t, -0.3),
                          (0.06 + 0.2 * t, -0.1)], 0.2, 0.035, "polimero")
    gatillo_y_guarda(gr, "acento", -0.18, 0.04, 0.07, -0.08)
    # Selector de modo (single/burst) en el lado izquierdo del grip.
    gr.cilindro((0.105, 0.24, 0.02), 0.035, 0.02, "acento", lados=10, eje=(1, 0, 0))
    gr.caja((0.12, 0.27, 0.02), (0.015, 0.07, 0.022), "acento")

    cg = a.pieza("Cargador", studio={"bisel": 0.01})
    cg.perfil_x_biselado([(0.06 + 0.42 * t, -0.28), (0.3 + 0.42 * t, -0.28), (0.3 + 0.55 * t + 0.01, -0.46),
                          (0.05 + 0.55 * t, -0.46)], 0.17, 0.02, "acento")
    cg.caja((0, 0.18 + 0.55 * t, -0.475), (0.19, 0.28, 0.04), "negro")

    a.agarre("Handle", (0, 0.17 + 0.1 * t, -0.1), (0, -1, 0))
    return a


def revolver_estelar():
    """
    #12 Revólver Estelar (Épico). Silueta clásica de revólver con materiales del futuro: cañón octogonal pesado,
    tambor de 6 cámaras con núcleos de energía, martillo, grip curvo con incrustación de hueso y grabados.
    (La descripción del catálogo llega cortada en la mira: «post elevado con punto lum[inoso]»; el resto de piezas
    siguen la convención de las demás armas.)
    """
    paleta = {
        "pavonado": {"color": "#2E3A50", "rug": 0.2, "met": 1.0, "patron": "grabado", "relieve": 0.7},
        "oro": {"color": "#C7A34E", "rug": 0.2, "met": 1.0},
        "acero": {"color": "#8F98A4", "rug": 0.18, "met": 1.0, "patron": "cepillado", "relieve": 0.4},
        "madera": {"color": "#2A1A12", "rug": 0.55, "met": 0.0, "patron": "madera", "relieve": 0.8},
        "hueso": {"color": "#EDE4CC", "rug": 0.55, "met": 0.0, "patron": "hueso", "relieve": 0.6,
                  "color2": "#C9A24A", "mezcla": ("vetas", 4.0, 0.86)},
        "neon": NEON,
    }
    a = ak.Arma("RevolverEstelar", "revolver_estelar.fbx", "Epico", paleta, "Revólver Estelar")
    a.notas.append("Épico: añadir en Studio un ParticleEmitter de chispas cian en la boca y en el tambor (aura)")
    ZB = 0.3   # eje del cañón
    ZT = 0.19  # eje del tambor

    cu = a.pieza("Cuerpo", studio={"bisel": 0.01})
    # Armazón: correa superior, ventana del tambor (dos marcos a los lados) y cola.
    cu.perfil_x_biselado([(-0.22, 0.24), (-0.22, 0.37), (0.26, 0.38), (0.34, 0.33), (0.36, 0.2), (0.3, 0.06),
                          (0.16, 0.04), (0.16, 0.3), (-0.2, 0.3), (-0.2, 0.04)], 0.15, 0.025, "pavonado")
    for s in (-1, 1):  # placas laterales del armazón alrededor del tambor
        cu.perfil_x([(-0.22, 0.04), (-0.18, 0.02), (0.18, 0.02), (0.2, 0.06), (-0.2, 0.06)],
                    s * 0.055, s * 0.075, "pavonado")
    # Grabados en relieve: volutas en los costados (además del normal map).
    for s in (-1, 1):
        for k in range(3):
            cu.toro((s * 0.078, 0.24 + k * 0.035, 0.29 - k * 0.04), 0.03 - k * 0.006, 0.004, "oro", seg=10,
                    lados=3, eje=(1, 0, 0), arco=(0.3, 4.8))
    # Varilla extractora bajo el cañón.
    cu.cilindro((0, -0.2, ZB - 0.1), 0.028, 0.5, "acero", lados=8, eje=(0, -1, 0))
    cu.caja((0, -0.62, ZB - 0.06), (0.05, 0.05, 0.07), "pavonado")

    ca = a.pieza("Canon")
    ca.tubo((0, -0.2, ZB), (0, -1, 0), 0.7, 0.085, 0.05, "pavonado", lados=8, giro=math.pi / 8, mat_int="acero")
    ca.tubo((0, -0.84, ZB), (0, -1, 0), 0.06, 0.095, 0.05, "oro", lados=8, giro=math.pi / 8)
    ca.caja((0, -0.52, ZB + 0.08), (0.05, 0.62, 0.04), "pavonado")  # costilla ventilada
    # Mira frontal: poste elevado.
    ca.perfil_x([(-0.86, ZB + 0.1), (-0.78, ZB + 0.1), (-0.8, ZB + 0.2), (-0.84, ZB + 0.2)], -0.012, 0.012,
                "pavonado")
    n2 = a.pieza("Neon_02", rol="neon", studio={"nota": "Punto luminoso de la mira (mira hacia el tirador)"})
    n2.esfera((0, -0.81 + 0.022, ZB + 0.175), 0.014, "neon", seg=8, anillos=4, escala=(1, 0.5, 1))
    n3 = a.pieza("Neon_03", rol="neon")
    for s in (-1, 1):  # líneas en las caras laterales del octógono
        n3.caja((s * (0.085 * math.cos(math.pi / 8) + 0.02), -0.52, ZB), (0.02, 0.5, 0.022), "neon")

    # Tambor de 6 cámaras, estriado, con un núcleo de energía en cada cámara.
    ta = a.pieza("Tambor")
    secs = []
    for i in range(5):
        y = -0.17 + 0.32 * i / 4
        anillo = []
        for k in range(36):
            ang = k * math.tau / 36
            rr = 0.15 * (1 - 0.22 * max(0.0, math.cos(6 * ang)) ** 4 * (1 if 0 < i < 4 else 0.3))
            rr *= 0.94 if i in (0, 4) else 1.0
            anillo.append(Vector((math.cos(ang) * rr, y, ZT + math.sin(ang) * rr)))
        secs.append(anillo)
    ta.loft(secs, "acero")
    n1 = a.pieza("Neon_01", rol="neon", studio={"nota": "Núcleos de las 6 cámaras"})
    for k in range(6):
        ang = k * math.tau / 6 + math.tau / 12
        cx, cz = math.cos(ang) * 0.092, ZT + math.sin(ang) * 0.092
        ta.tubo((cx, -0.18, cz), (0, -1, 0), 0.02, 0.04, 0.03, "oro", lados=10)
        n1.esfera((cx, -0.17, cz), 0.024, "neon", seg=8, anillos=6)
    ta.cilindro((0, -0.19, ZT), 0.03, 0.03, "oro", lados=8, eje=(0, -1, 0))

    ma = a.pieza("Martillo")
    ma.banda(spline([(0, 0.25, 0.3), (0, 0.31, 0.37), (0, 0.36, 0.43), (0, 0.42, 0.45)]), (1, 0, 0), 0.05, 0.05,
             "acero", n=8, grosor_fn=lambda t: 0.07 - 0.03 * t)
    ma.cilindro((-0.035, 0.27, 0.31), 0.035, 0.07, "acero", lados=8, eje=(1, 0, 0))
    for k in range(3):  # estrías de la uña del martillo
        ma.caja((0, 0.4 + 0.012 * k, 0.465 - 0.006 * k), (0.052, 0.006, 0.012), "acero")

    gr = a.pieza("Grip", studio={"raiz": True})
    curva = spline([(0, 0.24, 0.1), (0, 0.3, -0.08), (0, 0.38, -0.24), (0, 0.46, -0.33)])
    frente = spline([(0, 0.12, 0.05), (0, 0.13, -0.1), (0, 0.22, -0.26), (0, 0.32, -0.36)])
    puntos = [(curva(i / 6).y, curva(i / 6).z) for i in range(7)] + \
             [(frente(1 - i / 6).y, frente(1 - i / 6).z) for i in range(7)]
    gr.perfil_x_biselado(puntos, 0.15, 0.03, "madera")
    gr.cilindro((0, 0.38, -0.33), 0.055, 0.17, "oro", lados=10, eje=(1, 0, 0))  # tapa del pomo
    for v_ in list(gr.bm.verts)[-22:]:
        v_.co.x -= 0.085
    de = a.pieza("Detalle_01")  # incrustación de hueso de bestia cósmica en las cachas
    for s in (-1, 1):
        cen = Vector((s * 0.078, 0.27, -0.12))
        placa = de.cilindro(cen - Vector((s * 0.008, 0, 0)), 0.07, 0.016, "hueso", lados=16, eje=(s, 0, 0))
        de.transformar(placa, Matrix.Translation(cen) @ Matrix.Rotation(-0.5, 4, "X") @
                       Matrix.Diagonal((1, 0.6, 1.2, 1)) @ Matrix.Translation(-cen))
        estrella = de.cilindro(cen + Vector((s * 0.006, 0, 0)), 0.03, 0.012, "oro", lados=8, eje=(s, 0, 0))
        de.transformar(estrella, Matrix.Translation(cen) @ Matrix.Rotation(-0.5, 4, "X") @ Matrix.Translation(-cen))
    ga = a.pieza("Gatillo")
    gatillo_y_guarda(ga, "oro", -0.04, 0.17, 0.05, -0.1)

    a.agarre("Handle", (0, 0.26, -0.12), (0, -1, 0))
    return a


# ==============================================================================================================

CATALOGO = [
    ("espada_plasma", espada_plasma),
    ("hoja_cristal", hoja_cristal),
    ("sable_gravitacional", sable_gravitacional),
    ("espada_estelar", espada_estelar),
    ("hoja_vacio", hoja_vacio),
    ("hacha_meteorito", hacha_meteorito),
    ("martillo_pulsar", martillo_pulsar),
    ("guadana_nebular", guadana_nebular),
    ("pistola_plasma", pistola_plasma),
    ("laser_precision", laser_precision),
    ("blaster_iones", blaster_iones),
    ("revolver_estelar", revolver_estelar),
]


def main():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="1")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--solo", default="")
    ap.add_argument("--nota", default="")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    solo = set(filter(None, args.solo.split(",")))
    salida = os.path.abspath(args.salida)
    os.makedirs(salida, exist_ok=True)
    resumen = []
    for clave, fn in CATALOGO:
        if solo and clave not in solo:
            continue
        c.escena_vacia()
        ak.estudio_gris()
        arma = fn()
        objetos, empties, info = ak.construir(arma, salida, args.rapido)
        datos = ak.exportar(arma, objetos, empties, info, salida)
        hoja, tris = ak.render_turnaround(arma, objetos, salida, args.ronda, args.rapido, args.nota)
        jpg = hoja[:-4] + ".jpg"
        Image.open(hoja).convert("RGB").save(jpg, quality=88)
        os.remove(hoja)
        limite = ak.RAREZAS[arma.rareza]["tris"]
        estado = "OK" if tris <= limite else "SUPERA EL LÍMITE"
        resumen.append(f"{arma.archivo}: {tris} tris (máx {limite}) {estado} -> {jpg}")
        print("[info]", resumen[-1], {p["nombre"]: p["triangulos"] for p in datos["piezas"]})
    print("\n".join(resumen))


if __name__ == "__main__":
    main()
