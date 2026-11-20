"""
BESTIA 4 — MEDUSA NEBULAR (soporte / curación, 1-2 jinetes).

Medusa luna cruzada con aurora boreal, del tamaño de un coche: campana de paraguas translúcida violeta con grosor
real (0,15 en el borde), 8 canales radiales y el órgano rosa en trébol visibles dentro, falda de 12 lóbulos, 4 brazos
orales en cinta con volantes, 8 tentáculos con 3 secciones y nematocistos (el 5 es más corto: se regenera), boca en
cruz y 8 manchas fotosensibles en el borde. Arnés de sanador delicado: red de seda hexagonal, plataforma de hueso con
espirales curativas y musgo, asas, cuerdas de seda con cuentas de cristal e incensario con humo.

Rig (14 piezas): Campana (raíz, pivote arriba en el centro), Falda, Brazo_Oral_1..4, Tentaculo_1..8.
Soldada a la Campana: Humo_Incensario (Transparency en Roblox).
Montaje: Montura_Piloto, Montura_Pasajero, Agarre_Izq, Agarre_Der.

Toda la medusa es geometría paramétrica (superficies de revolución y láminas con grosor), sin campos: así la campana
es una concha fina y limpia, como debe ser.

Uso: python bestias/herramientas/medusa_nebular.py --salida bestias/medusa_nebular --ronda 1 [--rapido]
"""

import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import bestia  # noqa: E402
import detalles as D  # noqa: E402
import taller as T  # noqa: E402

NOMBRE = "medusa_nebular"
PRESUPUESTO = 16000
COL = {"campana": "#5B2C87", "rosa": "#FF69B4", "brazo": "#E8E0F0", "tentaculo": "#D0D8F0", "brillo": "#8E44AD",
       "hueso": "#F0E8D8", "musgo": "#3E6A30", "seda": "#EDE6F5"}

APICE = 10.0           # z de la cima de la campana
BORDE_Z = 7.2          # z del borde de la campana
RADIO = 3.0            # radio de la campana (6 de diámetro)
GROSOR_BORDE = 0.15
GROSOR_CIMA = 0.34
SEG = 40               # divisiones alrededor
TENTACULO_CORTO = 5    # el que se está regenerando


def lin(h):
    return T.srgb(COL.get(h, h))


def smooth(N, a, b, x):
    m = N.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
    m.inputs["From Min"].default_value = a
    m.inputs["From Max"].default_value = b
    N.enlazar(x, m.inputs["Value"])
    return m.outputs["Result"]


# --------------------------------------------------------------------------------------------------------------
# Superficie de la campana
# --------------------------------------------------------------------------------------------------------------


def campana_ext(t, phi):
    """Punto de la superficie exterior: t = 0 en la cima, 1 en el borde. Lóbulos suaves (8) cerca del borde."""
    # Paraguas: cima ancha y algo plana, hombros caídos y borde abierto hacia fuera (no un casco).
    r = RADIO * (math.sin(t * math.pi / 2) ** 0.6) * (0.95 + 0.05 * t ** 3)
    z = BORDE_Z + (APICE - BORDE_Z) * math.cos(t * math.pi / 2) ** 1.6
    r *= 1 + 0.025 * math.cos(8 * phi) * t ** 3 + 0.01 * math.sin(3 * phi + 1.0) * t
    z -= 0.06 * t ** 6  # el borde se curva un poco hacia abajo
    return Vector((r * math.cos(phi), r * math.sin(phi), z))


def normal_ext(t, phi, e=1e-3):
    a = campana_ext(min(t + e, 1), phi) - campana_ext(max(t - e, 0), phi)
    b = campana_ext(t, phi + e) - campana_ext(t, phi - e)
    n = b.cross(a)
    if n.length < 1e-9:
        return Vector((0, 0, 1))
    n.normalize()
    return n if n.z * 0 + (n.dot(campana_ext(t, phi) - Vector((0, 0, BORDE_Z - 1))) > 0) else -n


def campana_int(t, phi):
    g = GROSOR_CIMA + (GROSOR_BORDE - GROSOR_CIMA) * t ** 0.8
    return campana_ext(t, phi) - normal_ext(max(t, 0.02), phi) * g


def contar(g, etiqueta):
    print(f"   [medusa] {etiqueta}: {sum(len(f.verts) - 2 for f in g.bm.faces)}")


def construir_campana(g, rnd):
    ts = [0.0] + list(np.linspace(0.05, 1.0, 13) ** 1.15)
    phis = [math.tau * k / SEG for k in range(SEG)]
    ext = [[campana_ext(t, p) for p in phis] for t in ts[1:]]
    inn = [[campana_int(t, p) for p in phis] for t in ts[1:]]
    aux_e = [[(t, p / math.tau, 0.0) for p in phis] for t in ts[1:]]
    aux_i = [[(t, p / math.tau, 1.0) for p in phis] for t in ts[1:]]
    ve = g.loft(ext, "campana", tapar_inicio=False, tapar_fin=False, auxs=aux_e,
                punta_inicio=(Vector((0, 0, APICE)), (0, 0, 0)))
    vi = g.loft(inn, "campana", tapar_inicio=False, tapar_fin=False, auxs=aux_i,
                punta_inicio=(Vector((0, 0, APICE - GROSOR_CIMA)), (0, 0, 1.0)))
    for k in range(SEG):  # canto del borde: une la cara exterior con la interior (grosor visible)
        k2 = (k + 1) % SEG
        g.cara((ve[-1][k], vi[-1][k], vi[-1][k2], ve[-1][k2]), "campana")

    # 8 canales radiales en relieve por dentro, que se ramifican cerca del borde.
    for k in range(8):
        phi = math.tau * k / 8 + math.pi / 8
        pts = [campana_int(t, phi) - normal_ext(t, phi) * 0.02 for t in np.linspace(0.08, 0.7, 7)]
        g.tubo(pts, [0.03] * len(pts), "canal", lados=3)
        for s in (-1, 1):
            q = [campana_int(t, phi + s * 0.11 * (t - 0.6) / 0.38) - normal_ext(t, phi) * 0.02
                 for t in np.linspace(0.62, 0.97, 4)]
            g.tubo(q, [0.025, 0.022, 0.02, 0.015], "canal", lados=3)
    # Órgano central: trébol de 4 hojas rosado (gónadas/estómago) bajo la cima.
    zc = APICE - GROSOR_CIMA - 0.16
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        c = Vector((math.cos(a) * 0.42, math.sin(a) * 0.42, zc))
        g.elipsoide(c, (0.42, 0.26, 0.11), "organo", seg=8, anillos=4,
                    rot=D.matriz((Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0)),
                                  Vector((0, 0, 1)))))
    # Manubrio (tallo) y boca en cruz de 4 labios.
    g.tubo([Vector((0, 0, zc - 0.05)), Vector((0, 0, 8.4)), Vector((0, 0, 7.55))], [0.3, 0.24, 0.3], "brazo", lados=10)
    for k in range(4):
        a = math.tau * k / 4
        c = Vector((math.cos(a) * 0.22, math.sin(a) * 0.22, 7.45))
        g.elipsoide(c, (0.24, 0.1, 0.13), "labio", seg=8, anillos=5,
                    rot=D.matriz((Vector((math.cos(a), math.sin(a), 0)), Vector((-math.sin(a), math.cos(a), 0)),
                                  Vector((0, 0, 1)))))
    # Esporas atrapadas en la gelatina y 8 manchas fotosensibles en el borde.
    for (t, p, col) in ((0.35, 0.4, "espora_c"), (0.5, 2.0, "espora_r"), (0.62, 3.3, "espora_d"), (0.28, 4.6, "espora_c"),
                        (0.7, 5.5, "espora_r"), (0.45, 1.2, "espora_d")):
        c = (campana_ext(t, p) + campana_int(t, p)) / 2
        g.elipsoide(c, (0.05, 0.05, 0.05), col, seg=6, anillos=4)
    for k in range(8):
        phi = math.tau * k / 8
        c = campana_ext(0.985, phi) + normal_ext(0.98, phi) * 0.01
        g.elipsoide(c, (0.07, 0.07, 0.05), "ocelo", seg=6, anillos=4)


def construir_falda(g):
    """12 lóbulos redondeados (borde de tarta), 0,08 de grosor, de violeta a rosa en las puntas."""
    cols = 12 * 8
    rej = []
    for i, u in enumerate((0.0, 0.33, 0.66, 1.0)):
        fila = []
        for j in range(cols + 1):
            phi = math.tau * j / cols
            lob = abs(math.sin(6 * phi)) ** 0.55
            r_ext = RADIO + 0.12 + 0.42 * lob
            r = (RADIO - 0.12) + (r_ext - (RADIO - 0.12)) * u
            z = BORDE_Z - 0.1 - 0.32 * u ** 1.4 - 0.02 * math.sin(6 * phi) * u
            fila.append(Vector((r * math.cos(phi), r * math.sin(phi), z)))
        rej.append(fila)
    D.lamina(g, rej, 0.08, 0.1, "falda", Vector((0, 0, 1)), aux_fn=lambda i, j: (i / 3, j / cols, 0.0))


def tentaculo(nombre, k, rnd):
    """Tentáculo de 4 studs (el 5, 3: roto y regenerándose), 0,15 de diámetro, 3 secciones por estrangulación y
    2-3 nematocistos por sección. aux.x = 0..1 a lo largo (pulso de luz de la base a la punta)."""
    g = T.Geo(nombre)
    phi = math.tau * (k - 1) / 8 + math.pi / 8
    base = Vector(((RADIO + 0.1) * math.cos(phi), (RADIO + 0.1) * math.sin(phi), BORDE_Z - 0.3))
    fuera = Vector((math.cos(phi), math.sin(phi), 0))
    largo = 3.0 if k == TENTACULO_CORTO else 4.0
    fase = rnd.uniform(0, math.tau)
    n = 22
    pts, rad = [], []
    for i in range(n):
        t = i / (n - 1)
        s = (t * 3) % 1.0 if t < 1 else 1.0
        onda = 0.18 * math.sin(t * 5.0 + fase) * t
        p = base + fuera * (0.12 * t + onda) + Vector((0, 0, -largo * t)) + \
            Vector((-math.sin(phi), math.cos(phi), 0)) * 0.1 * math.sin(t * 4 + fase) * t
        r = 0.075 * (1 - 0.6 * t) * (1 - 0.3 * math.exp(-((s - 0.0) / 0.06) ** 2) * (t > 0.05))
        pts.append(p)
        rad.append(r)
    punta_redonda = k == TENTACULO_CORTO
    g.tubo(pts, rad, "tentaculo", lados=6, punta=not punta_redonda,
           aux_fn=lambda t, a: (t, 1.0 if punta_redonda else 0.0, 0.0))
    if punta_redonda:  # muñón redondeado, más claro
        g.elipsoide(pts[-1], (rad[-1] * 1.25, rad[-1] * 1.25, rad[-1] * 1.4), "regenera", seg=8, anillos=5)
    for sec in range(3):  # nematocistos
        for j in range(rnd.choice((2, 3))):
            t = (sec + 0.25 + 0.5 * j / 2) / 3
            i = int(t * (n - 1))
            c = pts[i]
            a = rnd.uniform(0, math.tau)
            d = Vector((math.cos(a), math.sin(a), 0))
            g.elipsoide(c + d * rad[i] * 0.85, (0.04, 0.04, 0.04), "nematocisto", seg=6, anillos=4)
    return g, base


def brazo_oral(nombre, k):
    """Brazo oral en cinta ondulada (0,5 × 0,1 × 3) con volantes rizados en los bordes."""
    g = T.Geo(nombre)
    a = math.tau * k / 4 + math.pi / 4
    dirx = Vector((math.cos(a), math.sin(a), 0))
    lado = Vector((-math.sin(a), math.cos(a), 0))
    base = Vector((0, 0, 7.42)) + dirx * 0.2
    rej = []
    for i, v in enumerate(np.linspace(-1, 1, 5)):
        fila = []
        for j, t in enumerate(np.linspace(0, 1, 16)):
            ancho = 0.25 * (0.6 + 0.4 * math.sin(math.pi * min(1, t * 1.3))) * (1 - 0.35 * t)
            centro = base + dirx * (0.25 * t + 0.12 * math.sin(t * 6 + k)) + Vector((0, 0, -3.0 * t))
            volante = 0.07 * math.sin(t * 38 + v * 2) * abs(v) ** 2  # rizos en los bordes
            fila.append(centro + lado * ancho * v + dirx * volante + lado * 0.06 * math.sin(t * 9 + k) * (1 - abs(v)))
        rej.append(fila)
    D.lamina(g, rej, 0.1, 0.06, "brazo", dirx, aux_fn=lambda i, j: (j / 15, i / 4, 0.0))
    return g, base


def arnes(g, rnd):
    """Red de seda hexagonal, plataforma ovalada de hueso con espirales y musgo, asas, cuerdas con cuentas e
    incensario. Devuelve los puntos de montaje y la geometría del humo."""
    datos = {}
    # Red de seda: celdas hexagonales proyectadas sobre la campana (t < 0.6).
    paso = 0.62
    vistos = set()
    for i in range(-6, 7):
        for j in range(-6, 7):
            cx = paso * (i + 0.5 * (j % 2))
            cy = paso * 0.866 * j
            if math.hypot(cx, cy) > 2.35:
                continue
            esquinas = []
            for k in range(6):
                a = math.pi / 6 + k * math.pi / 3
                esquinas.append((cx + paso / math.sqrt(3) * math.cos(a), cy + paso / math.sqrt(3) * math.sin(a)))
            for k in range(6):
                p1, p2 = esquinas[k], esquinas[(k + 1) % 6]
                clave = tuple(sorted((tuple(round(c, 3) for c in p1), tuple(round(c, 3) for c in p2))))
                if clave in vistos:
                    continue
                vistos.add(clave)
                pts = []
                for s in (0.0, 1.0):
                    x = p1[0] + (p2[0] - p1[0]) * s
                    y = p1[1] + (p2[1] - p1[1]) * s
                    pts.append(sobre_campana(x, y, 0.025))
                if None in pts:
                    continue
                g.tubo(pts, [0.016] * 2, "seda", lados=3)
    # Plataforma ovalada de hueso pulido (3,2 × 2,5) sobre la cima, con almohadilla de musgo.
    cima = Vector((0, 0, APICE + 0.04))
    filas = []
    for z, f in ((0.0, 0.96), (0.1, 1.0), (0.2, 0.98)):
        filas.append([cima + Vector((1.25 * f * math.cos(a), 1.6 * f * math.sin(a), z - 0.18 * (1 - 0) * (
            (math.cos(a) ** 2 * 0.3 + math.sin(a) ** 2 * 0.55)))) for a in np.linspace(0, math.tau, 28,
                                                                                         endpoint=False)])
    g.loft(filas, "hueso_pulido", auxs=[[(1.0, k / 28, 9.0)] * 1 * 0 + [(1.0, k / 28, 9.0) for k in range(28)]
                                         for _ in range(3)],
           punta_inicio=(cima + Vector((0, 0, -0.05)), (0.0, 0.0, 9.0)),
           punta_fin=(cima + Vector((0, 0, 0.22)), (0.0, 0.0, 9.0)))
    for y, nom in ((0.62, "piloto"), (-1.0, "pasajero")):
        c = cima + Vector((0, y, 0.25))
        g.caja_redonda(c, (0.8, 0.75, 0.14), "musgo", seg=2, redondeo=0.7)
        datos[nom] = c + Vector((0, 0, 0.07 + 0.15))
    # Asas de hueso curvado a los lados.
    for lado, nom in ((-1, "Agarre_Izq"), (1, "Agarre_Der")):
        pts = [cima + Vector((lado * 1.18, 0.45, 0.12)), cima + Vector((lado * 1.42, 0.2, 0.45)),
               cima + Vector((lado * 1.45, -0.2, 0.45)), cima + Vector((lado * 1.18, -0.45, 0.12))]
        g.tubo(pts, [0.06, 0.05, 0.05, 0.06], "hueso", lados=6)
        datos[nom] = cima + Vector((lado * 1.44, 0.0, 0.45))
    # Cuerdas de seda desde la plataforma, por encima de la campana y del borde, hasta los brazos orales.
    colores = ["cuenta_c", "cuenta_r", "cuenta_d"]
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        d = Vector((math.cos(a), math.sin(a), 0))
        pts = [cima + Vector((1.15 * math.cos(a), 1.5 * math.sin(a), 0.05))]
        for t in (0.45, 0.65, 0.82, 0.95, 1.0):
            pts.append(campana_ext(t, a) + normal_ext(t, a) * 0.05)
        pts.append(campana_ext(1.0, a) + Vector((0, 0, -0.45)) + d * 0.25)
        pts.append(Vector((0, 0, 7.15)) + d * 0.55)
        pts.append(Vector((0, 0, 7.0)) + d * 0.3)
        from campos import catmull_rom
        curva = catmull_rom([tuple(p) for p in pts], 5, cerrada=False)
        g.tubo([Vector(p) for p in curva], [0.02] * len(curva), "seda", lados=3)
        for b in range(5):  # 5 cuentas de cristal por cuerda
            p = Vector(curva[int(len(curva) * (0.22 + 0.11 * b))])
            g.elipsoide(p, (0.075, 0.075, 0.075), colores[(k + b) % 3], seg=6, anillos=4)
    # Espirales curativas talladas en la plataforma (en el material, aux.z = 9) e incensario colgante.
    brazo = [cima + Vector((0, -1.55, 0.1)), cima + Vector((0, -1.95, 0.25)), cima + Vector((0, -2.2, 0.15))]
    g.tubo(brazo, [0.045, 0.04, 0.035], "hueso", lados=5)
    colgante = brazo[-1] + Vector((0, 0, -0.55))
    for s in (-1, 1):
        g.tubo([brazo[-1], colgante + Vector((s * 0.09, 0, 0.12))], [0.01, 0.01], "seda", lados=3)
    filas = [[colgante + Vector((r * math.cos(a), r * math.sin(a), z)) for a in np.linspace(0, math.tau, 10,
                                                                                            endpoint=False)]
             for r, z in ((0.04, -0.12), (0.12, -0.06), (0.14, 0.06), (0.11, 0.12))]
    g.loft(filas, "hueso", tapar_inicio=True, tapar_fin=True)
    humo = T.Geo("Humo_Incensario")
    filas = []
    for i, z in enumerate(np.linspace(0.14, 1.4, 7)):
        r = 0.05 + 0.13 * (i / 6) ** 1.2
        dx = 0.12 * math.sin(i * 0.9)
        filas.append([colgante + Vector((dx + r * math.cos(a), r * math.sin(a) - 0.08 * i / 6, z))
                      for a in np.linspace(0, math.tau, 8, endpoint=False)])
    humo.loft(filas, "humo", tapar_inicio=True, punta_fin=(colgante + Vector((0.1, -0.12, 1.6)), (0, 0, 0)))
    return datos, humo


_BVH = None


def sobre_campana(x, y, alto):
    """Punto de la superficie exterior de la campana bajo (x, y), elevado `alto`."""
    r = math.hypot(x, y)
    phi = math.atan2(y, x)
    lo, hi = 0.0, 1.0
    for _ in range(30):  # busca t con radio r (el radio crece con t)
        m = (lo + hi) / 2
        if campana_ext(m, phi).xy.length < r:
            lo = m
        else:
            hi = m
    t = (lo + hi) / 2
    if t > 0.97:
        return None
    return campana_ext(t, phi) + normal_ext(max(t, 0.02), phi) * alto


# --------------------------------------------------------------------------------------------------------------
# Materiales
# --------------------------------------------------------------------------------------------------------------


def materiales():
    m = {}
    mat = bpy.data.materials.new("campana")
    N = T.Nodos(mat)
    P = N.pos()
    a = N.sep(N.atributo("aux").outputs["Vector"])
    px_, py_, pz_ = N.sep(P)
    gel = N.ruido(P, 9.0, 4.0, 0.6)
    venas = smooth(N, 0.0, 0.04, N.voronoi(P, 3.0, rasgo="DISTANCE_TO_EDGE"))
    # 3 manchas más opacas (quemaduras solares).
    q = N.ruido(N.vmate("ADD", P, (13.0, 4.0, 0.0)), 0.9, 1.0, 0.5)
    quema = N.mate("MULTIPLY", smooth(N, 0.68, 0.74, q), N.mate("LESS_THAN", a[2], 0.5))
    quema = N.mate("MULTIPLY", quema, 0.35)
    # Dos espirales luminosas en la cima (marcas de domesticación inducidas).
    ang = N.mate("ARCTAN2", py_, px_)
    rr = N.vmate("LENGTH", N.combinar(px_, py_, 0.0))
    esp = N.mate("PINGPONG", N.mate("ADD", N.mate("MULTIPLY", ang, 1.0 / math.pi), N.mate("MULTIPLY", rr, 1.6)), 0.5)
    espiral = N.mate("MULTIPLY", N.mate("LESS_THAN", esp, 0.06),
                     N.mate("MULTIPLY", N.mate("LESS_THAN", rr, 1.6), N.mate("GREATER_THAN", rr, 0.3)))
    espiral = N.mate("MULTIPLY", espiral, N.mate("LESS_THAN", a[2], 0.5))
    borde = smooth(N, 0.8, 1.0, a[0])
    col = N.mezcla(smooth(N, 0.3, 0.7, gel), lin("campana"), (0.42, 0.22, 0.6))
    col = N.mezcla(N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, venas), 0.35), col, (0.55, 0.35, 0.75))
    col = N.mezcla(quema, col, (0.62, 0.5, 0.66))
    col = N.mezcla(espiral, col, (0.85, 0.65, 1.0))
    N.poner("Base Color", col)
    N.poner("Roughness", N.sep(N.mezcla(quema, 0.12, 0.55))[0])
    N.poner("Normal", N.relieve(N.mate("ADD", N.mate("MULTIPLY", gel, 0.5), N.mate("MULTIPLY", quema, 0.6)),
                                fuerza=0.35, distancia=0.02))
    luz = N.mate("ADD", N.mate("ADD", 0.18, N.mate("MULTIPLY", borde, 0.6)), espiral)
    N.poner("Emission Color", N.mezcla(N.mate("MULTIPLY", luz, 0.8), (0, 0, 0), lin("brillo")))
    N.poner("Emission Strength", 1.0)
    m["campana"] = mat

    def gradiente(nombre, c0, c1, emi, k_emi=1.0, eje=0, pulso=False):
        mt = bpy.data.materials.new(nombre)
        N = T.Nodos(mt)
        a = N.sep(N.atributo("aux").outputs["Vector"])
        t = a[eje]
        col = N.mezcla(smooth(N, 0.2, 1.0, t), lin(c0), lin(c1))
        venas = smooth(N, 0.0, 0.05, N.voronoi(N.pos(), 5.0, rasgo="DISTANCE_TO_EDGE"))
        col = N.mezcla(N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, venas), 0.4), col, lin("campana"))
        luz = smooth(N, 0.5, 1.0, t)
        if pulso:  # pulsos de luz de la base a la punta
            luz = N.mate("ADD", N.mate("MULTIPLY", luz, 0.6),
                         N.mate("MULTIPLY", N.mate("LESS_THAN", N.mate("PINGPONG", N.mate("MULTIPLY", t, 4.0), 0.5),
                                                   0.12), 0.7))
        N.poner("Base Color", col)
        N.poner("Roughness", 0.25)
        burbujas = N.voronoi(N.pos(), 25.0, rasgo="F1")
        N.poner("Normal", N.relieve(N.mate("ADD", N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, venas), 0.4),
                                           smooth(N, 0.0, 0.3, burbujas)), fuerza=0.35, distancia=0.01))
        N.poner("Emission Color", N.mezcla(N.mate("MULTIPLY", luz, k_emi), (0, 0, 0), lin(emi)))
        N.poner("Emission Strength", 1.0)
        return mt

    m["falda"] = gradiente("falda", "campana", "rosa", "brillo", 1.0, eje=0)
    m["brazo"] = gradiente("brazo", "brazo", "brazo", "brillo", 1.0, eje=0)
    m["tentaculo"] = gradiente("tentaculo", "tentaculo", "tentaculo", "brillo", 0.9, eje=0, pulso=True)
    for nombre, col, rug, emi, f in (("canal", "#B488D8", 0.2, "brillo", 0.5), ("organo", "rosa", 0.3, "rosa", 0.55),
                                     ("labio", "#C8A8D8", 0.35, None, 0), ("espora_c", "#80FFFF", 0.2, "#80FFFF", 1.0),
                                     ("espora_r", "rosa", 0.2, "rosa", 1.0), ("espora_d", "#FFD27A", 0.2, "#FFD27A", 1.0),
                                     ("ocelo", "#3A0A28", 0.15, "rosa", 0.25), ("nematocisto", "#F0D8FF", 0.2, "brillo", 1.0),
                                     ("regenera", "#F4F0FA", 0.3, "brillo", 0.3), ("hueso", "hueso", 0.35, None, 0),
                                     ("musgo", "musgo", 0.95, None, 0), ("seda", "seda", 0.5, None, 0),
                                     ("cuenta_c", "#7FF6FF", 0.05, "#7FF6FF", 0.35), ("cuenta_r", "#FF9AD0", 0.05, "#FF9AD0", 0.35),
                                     ("cuenta_d", "#FFD98A", 0.05, "#FFD98A", 0.35), ("humo", "#D8D0E0", 0.9, None, 0)):
        mt, N = T.material_simple(nombre, lin(col), rug=rug, emision=lin(emi) if emi else None, fuerza=f,
                                  relieve=(60.0, 0.6) if nombre == "musgo" else None)
        m[nombre] = mt
    # Hueso pulido de la plataforma con espirales curativas talladas que brillan suavemente.
    mt = bpy.data.materials.new("hueso_pulido")
    N = T.Nodos(mt)
    px_, py_, pz_ = N.sep(N.pos())
    ang = N.mate("ARCTAN2", py_, px_)
    rr = N.vmate("LENGTH", N.combinar(px_, N.mate("MULTIPLY", py_, 0.78), 0.0))
    esp = N.mate("PINGPONG", N.mate("ADD", N.mate("MULTIPLY", ang, 0.5 / math.pi), N.mate("MULTIPLY", rr, 3.0)), 0.5)
    tallado = N.mate("MULTIPLY", N.mate("LESS_THAN", esp, 0.07), N.mate("LESS_THAN", rr, 1.15))
    N.poner("Base Color", N.mezcla(tallado, lin("hueso"), (0.75, 0.5, 0.95)))
    N.poner("Roughness", 0.18)
    N.poner("Normal", N.relieve(N.mate("MULTIPLY", tallado, -1.0), fuerza=0.6, distancia=0.01))
    N.poner("Emission Color", N.mezcla(tallado, (0, 0, 0), lin("brillo")))
    N.poner("Emission Strength", 0.6)
    m["hueso_pulido"] = mt
    return m


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="1")
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    T.escena_vacia()
    mats = materiales()
    rnd = random.Random(8)
    g = T.Geo("Campana")
    construir_campana(g, rnd)
    contar(g, "campana")
    datos, humo = arnes(g, rnd)
    contar(g, "campana + arnés")
    geometricas = {"Campana": g.objeto(mats)}
    g = T.Geo("Falda")
    construir_falda(g)
    geometricas["Falda"] = g.objeto(mats)
    pivotes = {"Campana": (0.0, 0.0, APICE), "Falda": (0.0, 0.0, BORDE_Z - 0.1)}
    padre = {"Campana": None, "Falda": "Campana", "Humo_Incensario": "Campana"}
    for k in range(1, 5):
        gb, base = brazo_oral(f"Brazo_Oral_{k}", k)
        geometricas[f"Brazo_Oral_{k}"] = gb.objeto(mats)
        pivotes[f"Brazo_Oral_{k}"] = tuple(base)
        padre[f"Brazo_Oral_{k}"] = "Campana"
    for k in range(1, 9):
        gt, base = tentaculo(f"Tentaculo_{k}", k, rnd)
        geometricas[f"Tentaculo_{k}"] = gt.objeto(mats)
        pivotes[f"Tentaculo_{k}"] = tuple(base)
        padre[f"Tentaculo_{k}"] = "Falda"
    humo_obj = humo.objeto(mats)
    pivotes["Humo_Incensario"] = pivotes["Campana"]
    montajes = {"Montura_Piloto": (datos["piloto"], "Campana"), "Montura_Pasajero": (datos["pasajero"], "Campana"),
                "Agarre_Izq": (datos["Agarre_Izq"], "Campana"), "Agarre_Der": (datos["Agarre_Der"], "Campana")}
    orden = ["Campana", "Falda"] + [f"Brazo_Oral_{k}" for k in range(1, 5)] + [f"Tentaculo_{k}" for k in range(1, 9)]
    cfg = dict(
        nombre=NOMBRE, titulo="MEDUSA NEBULAR", rol="Soporte / curación", jinetes="1-2",
        neon=["#8E44AD", "#FF69B4"], presupuesto=PRESUPUESTO, salida=args.salida, ronda=args.ronda,
        rapido=args.rapido, altas={}, peso_tris={}, geometricas=geometricas,
        soldadas={"Humo_Incensario": (humo_obj, "Campana")}, pivotes=pivotes, padre=padre, orden=orden,
        montajes=montajes, prioridad_uv={"Campana": 1.3, "Falda": 1.0, "Humo_Incensario": 0.4},
        translucidas={"Campana": 0.62, "Falda": 0.7, "Humo_Incensario": 0.3,
                      **{f"Brazo_Oral_{k}": 0.72 for k in range(1, 5)},
                      **{f"Tentaculo_{k}": 0.75 for k in range(1, 9)}},
        radio_estudio=6.5, exposicion=0.6, emision_render=2.5,
        cerca=[("Campana 3/4", 35, 25, (0, 0, 8.6), 3.4), ("Plataforma y red", 20, 55, (0, 0, 9.9), 2.0),
               ("Desde abajo", 30, -55, (0, 0, 7.2), 3.0), ("Falda y ocelos", -62, 12, (2.7, -1.45, 7.0), 1.2),
               ("Tentáculos (el 5 corto)", 120, 5, (0, 0, 5.0), 4.0), ("Incensario y cuentas", 160, 20, (0, -2.4, 9.4), 1.4)],
        notas_json=[
            "Translúcida: en Roblox, Transparency ≈ 0,4 en Campana, 0,3 en Falda, 0,3 en brazos y 0,25 en "
            "tentáculos (por eso los canales y el órgano rosa interior se ven a través de la campana).",
            "Humo_Incensario va soldado a la Campana con Transparency 0,7.",
            "Alto real ≈ 7,6 studs: la campana mide 3 y los tentáculos 4, como pide la anatomía; los 10 de la tabla "
            "no cuadran con esas medidas.",
            "Tentaculo_5 mide 3 studs (roto, regenerándose) y tiene la punta redondeada y más clara.",
        ],
    )
    bestia.terminar(cfg)


if __name__ == "__main__":
    main()
