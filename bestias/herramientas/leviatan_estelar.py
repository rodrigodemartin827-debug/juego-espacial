"""
BESTIA 6 — LEVIATÁN ESTELAR (nave nodriza viviente, 8-12 jinetes).

Una montaña que respira: ballena cósmica entre cachalote y fortaleza, con la cabeza en bloque (melón acústico), la
mandíbula larga y estrecha, el cuerpo hueco con dos aperturas laterales tapadas por placas operculares, aletas
pectorales en ala delta, aleta caudal HORIZONTAL, cuatro tentáculos ventrales con ventosas y un lomo convertido en un
mundo: coral ramificado y coral cerebro, anémonas y nidos. Siglos de historia: arpón oxidado clavado, marcas de
ventosas, quemadura de plasma, percebes, musgo en la placa craneal y las marcas doradas de la simbiosis.
Encima, una civilización: puente de mando con timones y toldo, bridas con cascabeles, red dorsal, pasarelas, puestos
de artillero en las aletas, escaleras de cuerda, estandarte y lámparas de bioluz.

Rig (15 piezas): Cuerpo_Principal (raíz), Cabeza, Mandibula_Inf, Aleta_Pectoral_{Izq,Der}, Aleta_Dorsal,
Cola_Base, Cola_Media, Cola_Punta, Tentaculo_1..4, Placa_Opercular_{Izq,Der}. Soldada a la Cabeza: Ojos_Cornea.
Montaje (8): Puente_Mando, Vigia_Dorsal, Artillero_Izq, Artillero_Der, Timonel_Cola, Acceso_Bodega_Izq,
Acceso_Bodega_Der, Proa_Inferior.

Uso: python bestias/herramientas/leviatan_estelar.py --salida bestias/leviatan_estelar --ronda 1 [--rapido]
"""

import argparse
import math
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import bestia  # noqa: E402
import campos as C  # noqa: E402
import detalles as D  # noqa: E402
import leviatan_forma as F  # noqa: E402
import taller as T  # noqa: E402

NOMBRE = "leviatan_estelar"
PRESUPUESTO = 20000
COL = {"dorso": "#2A3A4A", "vientre": "#E8E0D8", "oro": "#FFD700", "azul": "#00BFFF", "marfil": "#E8DCC8",
       "naranja": "#FF6B35", "rosa": "#FF69B4", "verde": "#90EE90", "purpura": "#9B59B6", "cuero": "#3A2820",
       "madera": "#5A4A3A", "tela": "#8A7560", "rojo": "#8B0000", "musgo": "#4A6A2A", "mucosa": "#C88A8A"}


def lin(h):
    return T.srgb(COL.get(h, h))


def smooth(N, a, b, x):
    m = N.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
    m.inputs["From Min"].default_value = a
    m.inputs["From Max"].default_value = b
    N.enlazar(x, m.inputs["Value"])
    return m.outputs["Result"]


# --------------------------------------------------------------------------------------------------------------
# Materiales
# --------------------------------------------------------------------------------------------------------------


def material_piel():
    mat = bpy.data.materials.new("piel")
    N = T.Nodos(mat)
    P = N.pos()
    px_, py_, pz_ = N.sep(P)
    nx_, ny_, nz_ = N.sep(N.normal())
    vientre = N.mate("SUBTRACT", 1.0, smooth(N, -0.45, 0.0, nz_))
    arrugas = N.ruido(N.vmate("MULTIPLY", P, (2.2, 0.25, 2.2)), 1.4, 5.0, 0.6)     # arrugas longitudinales hondas
    poros = N.mate("LESS_THAN", N.voronoi(P, 9.0, rasgo="F1"), 0.1)
    # Placa craneal de marfil con grietas y líquenes.
    q = N.vmate("LENGTH", N.vmate("DIVIDE", N.vmate("SUBTRACT", P, (0, 12.5, F.ZC + 4.3)), (3.0, 3.6, 1.3)))
    placa = N.mate("SUBTRACT", 1.0, smooth(N, 0.85, 1.0, q))
    placa = N.mate("MULTIPLY", placa, smooth(N, 0.45, 0.7, nz_))  # sólo en la cima, no sobre los ojos
    grietas = N.mate("SUBTRACT", 1.0, smooth(N, 0.0, 0.05, N.voronoi(P, 2.2, rasgo="DISTANCE_TO_EDGE")))
    liquen = N.mate("MULTIPLY", smooth(N, 0.55, 0.65, N.ruido(P, 1.6, 3.0)), placa)
    # Melón (frente) más liso.
    melon = smooth(N, 17.2, 18.6, py_)
    # Marcas de simbiosis: dos líneas espirales doradas en cada flanco.
    dy = N.mate("SUBTRACT", py_, 1.5)
    dz = N.mate("SUBTRACT", pz_, F.ZC + 0.5)
    ang = N.mate("ARCTAN2", dz, dy)
    rr = N.vmate("LENGTH", N.combinar(dy, dz, 0.0))
    esp = N.mate("PINGPONG", N.mate("ADD", N.mate("MULTIPLY", ang, 1.0 / math.pi), N.mate("MULTIPLY", rr, 0.42)), 0.5)
    simbiosis = N.mate("MULTIPLY", N.mate("LESS_THAN", esp, 0.025), smooth(N, 0.5, 0.8, N.mate("ABSOLUTE", nx_)))
    simbiosis = N.mate("MULTIPLY", simbiosis, N.mate("MULTIPLY", N.mate("LESS_THAN", rr, 4.4),
                                                     N.mate("GREATER_THAN", rr, 1.2)))
    # Marcas de ventosas (5 círculos en el flanco derecho) y quemadura de plasma cristalina en el lomo.
    ventosas = None
    for (y, z) in ((4.5, 9.3), (3.2, 8.4), (2.0, 9.6), (0.6, 8.6), (-0.6, 9.8)):
        d = N.vmate("LENGTH", N.vmate("SUBTRACT", P, (6.4, y, z)))
        a_ = N.mate("MULTIPLY", N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("SUBTRACT", d, 0.45)), 0.06),
                    N.mate("GREATER_THAN", px_, 4.0))
        ventosas = a_ if ventosas is None else N.mate("MAXIMUM", ventosas, a_)
    q = N.vmate("LENGTH", N.vmate("DIVIDE", N.vmate("SUBTRACT", P, (1.6, -8.4, F.ZC + 4.3)), (1.1, 1.6, 0.8)))
    quema = N.mate("SUBTRACT", 1.0, smooth(N, 0.75, 1.05, q))
    facetas = smooth(N, 0.0, 0.08, N.voronoi(P, 6.0, rasgo="DISTANCE_TO_EDGE"))
    # Boca y cavidad: bioluminiscencia azul.
    qb = N.vmate("LENGTH", N.vmate("DIVIDE", N.vmate("SUBTRACT", P, (0, 14.4, 5.15)), (1.4, 4.8, 0.55)))
    boca = N.mate("SUBTRACT", 1.0, smooth(N, 0.9, 1.05, qb))
    qc = N.vmate("LENGTH", N.vmate("DIVIDE", N.vmate("SUBTRACT", P, (0, -0.5, F.ZC)), (4.75, 7.15, 3.25)))
    cavidad = N.mate("SUBTRACT", 1.0, smooth(N, 0.97, 1.05, qc))
    col = N.mezcla(smooth(N, 0.3, 0.7, arrugas), (0.012, 0.02, 0.03), lin("dorso"))
    col = N.mezcla(N.mate("MULTIPLY", poros, 0.5), col, (0.01, 0.015, 0.02))
    col = N.mezcla(vientre, col, N.mezcla(N.mate("MULTIPLY", smooth(N, 0.4, 0.7, arrugas), 0.3), lin("vientre"),
                                          (0.4, 0.38, 0.36)))
    col = N.mezcla(placa, col, N.mezcla(grietas, lin("marfil"), (0.25, 0.2, 0.15)))
    col = N.mezcla(liquen, col, lin("musgo"))
    col = N.mezcla(ventosas, col, (0.35, 0.4, 0.45))
    col = N.mezcla(quema, col, N.mezcla(facetas, (0.75, 0.85, 0.9), (0.2, 0.25, 0.3)))
    col = N.mezcla(N.mate("MAXIMUM", boca, cavidad), col, lin("mucosa"))
    luz_azul = N.mate("MULTIPLY", N.mate("MAXIMUM", boca, cavidad), 0.8)
    col = N.mezcla(simbiosis, col, lin("oro"))
    N.poner("Base Color", col)
    rug = N.mezcla(vientre, 0.82, 0.55)
    rug = N.mezcla(melon, rug, 0.4)
    rug = N.mezcla(N.mate("MAXIMUM", quema, N.mate("MAXIMUM", boca, cavidad)), rug, 0.15)
    rug = N.mezcla(placa, rug, 0.45)
    N.poner("Roughness", N.sep(rug)[0])
    h = N.mate("ADD", N.mate("MULTIPLY", arrugas, N.mate("SUBTRACT", 1.2, melon)), N.mate("MULTIPLY", poros, -0.3))
    h = N.mate("SUBTRACT", h, N.mate("MULTIPLY", grietas, N.mate("MULTIPLY", placa, 0.9)))
    h = N.mate("ADD", h, N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, facetas), N.mate("MULTIPLY", quema, 0.8)))
    h = N.mate("SUBTRACT", h, N.mate("MULTIPLY", ventosas, 0.8))
    N.poner("Normal", N.relieve(h, fuerza=0.7, distancia=0.08))
    luz = N.mezcla(simbiosis, N.mezcla(luz_azul, (0, 0, 0), lin("azul")), N.mezcla(0.45, (0, 0, 0), lin("oro")))
    N.poner("Emission Color", luz)
    N.poner("Emission Strength", 1.0)
    return mat


def materiales():
    m = {"piel": material_piel()}
    simples = [
        ("diente", "#D8C890", 0.4, 0, None, 0, (30, 0.3)), ("percebe", "#B8B8B0", 0.85, 0, None, 0, (60, 0.8)),
        ("oxido", "#5A2A12", 0.8, 0.5, None, 0, (50, 0.8)), ("hueso", "marfil", 0.45, 0, None, 0, (14, 0.35)),
        ("cuero", "cuero", 0.7, 0, None, 0, (45, 0.4)), ("cuerda", "#8A7A5A", 0.9, 0, None, 0, (90, 0.6)),
        ("lampara", "azul", 0.1, 0, "azul", 0.8, None), ("mucosa", "mucosa", 0.25, 0, "azul", 0.15, (20, 0.3)),
        ("coral_n", "naranja", 0.6, 0, None, 0, (40, 0.6)), ("coral_r", "rosa", 0.6, 0, None, 0, (40, 0.6)),
        ("punta", "#F4F0E8", 0.5, 0, None, 0, None), ("cerebro", "verde", 0.7, 0, None, 0, None),
        ("anemona", "purpura", 0.35, 0, "purpura", 0.25, None), ("nido", "#7A6A4A", 0.95, 0, None, 0, (70, 0.8)),
        ("esclera", "#1A1410", 0.25, 0, None, 0, None), ("pupila", "#020202", 0.1, 0, None, 0, None),
        ("membrana_ojo", "#4A4038", 0.3, 0, None, 0, None), ("cornea", "#FFF2C0", 0.04, 0, None, 0, None),
        ("ventosa", "#C89A9A", 0.4, 0, None, 0, (30, 0.4)),
    ]
    for nombre, col, rug, met, emi, f, rel in simples:
        mt, _ = T.material_simple(nombre, lin(col), rug=rug, metal=met, emision=lin(emi) if emi else None, fuerza=f,
                                  relieve=rel)
        m[nombre] = mt
    iris = bpy.data.materials.new("iris")
    N = T.Nodos(iris)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    col = N.mezcla(smooth(N, 0.1, 0.95, a[0]), (1.0, 0.85, 0.2), (0.35, 0.18, 0.0))
    N.poner("Base Color", col)
    N.poner("Emission Color", col)
    N.poner("Emission Strength", 0.7)
    m["iris"] = iris
    # Coral cerebro: surcos laberínticos.
    mt = m["cerebro"]
    N = T.Nodos(mt)
    lab = N.mate("PINGPONG", N.ruido(N.pos(), 3.0, 2.0, 0.5), 0.08)
    N.poner("Base Color", N.mezcla(smooth(N, 0.0, 0.08, lab), (0.15, 0.3, 0.12), lin("verde")))
    N.poner("Roughness", 0.7)
    N.poner("Normal", N.relieve(lab, fuerza=0.8, distancia=0.02))
    # Madera petrificada con el mapa estelar tallado (aux = u, v en el suelo del puente).
    mt = bpy.data.materials.new("madera")
    N = T.Nodos(mt)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    vetas = N.ruido(N.vmate("MULTIPLY", N.pos(), (1, 12, 1)), 3.0, 4.0)
    estrellas = N.mate("MULTIPLY", N.mate("LESS_THAN", N.voronoi(N.combinar(a[0], a[1], 0.0), 9.0, rasgo="F1"), 0.06),
                       N.mate("GREATER_THAN", a[2], 0.5))
    orbitas = N.mate("MULTIPLY", N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("PINGPONG", N.vmate("LENGTH",
                     N.combinar(N.mate("SUBTRACT", a[0], 0.5), N.mate("SUBTRACT", a[1], 0.5), 0.0)), 0.12)), 0.006),
                     N.mate("GREATER_THAN", a[2], 0.5))
    tallado = N.mate("MAXIMUM", estrellas, orbitas)
    col = N.mezcla(smooth(N, 0.35, 0.7, vetas), lin("madera"), (0.2, 0.16, 0.12))
    col = N.mezcla(tallado, col, (0.85, 0.75, 0.45))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.8)
    N.poner("Normal", N.relieve(N.mate("SUBTRACT", vetas, tallado), fuerza=0.6, distancia=0.01))
    m["madera"] = mt
    # Estandarte: piel tostada con la bestia de la horda en rojo y negro (aux = u, v de la tela).
    mt = bpy.data.materials.new("tela")
    N = T.Nodos(mt)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    u = N.mate("SUBTRACT", a[1], 0.5)
    v = N.mate("SUBTRACT", a[0], 0.45)
    cuerpo = N.mate("LESS_THAN", N.vmate("LENGTH", N.combinar(N.mate("MULTIPLY", u, 2.2), N.mate("MULTIPLY", v, 1.6),
                                                             0.0)), 0.3)
    cuernos = N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("SUBTRACT", N.mate("ABSOLUTE", u), N.mate("MULTIPLY",
                     N.mate("SUBTRACT", v, -0.35), -0.5))), 0.03)
    cuernos = N.mate("MULTIPLY", cuernos, N.mate("LESS_THAN", v, -0.12))
    ojos = N.mate("LESS_THAN", N.vmate("LENGTH", N.combinar(N.mate("SUBTRACT", N.mate("ABSOLUTE", u), 0.07),
                                                           N.mate("ADD", v, 0.05), 0.0)), 0.035)
    col = N.mezcla(smooth(N, 0.3, 0.75, N.ruido(N.pos(), 5.0, 4.0)), lin("tela"), (0.4, 0.32, 0.24))
    col = N.mezcla(N.mate("MAXIMUM", cuerpo, cuernos), col, lin("rojo"))
    col = N.mezcla(ojos, col, (0.01, 0.01, 0.01))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.85)
    m["tela"] = mt
    # Placa opercular: piel por fuera, mucosa rosada por dentro y fuga de luz azul en el borde sellado.
    mt = bpy.data.materials.new("opercular")
    N = T.Nodos(mt)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    px_ = N.sep(N.pos())[0]
    nx_ = N.sep(N.normal())[0]
    dentro = N.mate("LESS_THAN", N.mate("MULTIPLY", nx_, px_), 0.0)
    borde = smooth(N, 0.93, 1.0, a[0])
    col = N.mezcla(dentro, N.mezcla(smooth(N, 0.3, 0.7, N.ruido(N.pos(), 2.0)), (0.02, 0.03, 0.05), lin("dorso")),
                   lin("mucosa"))
    col = N.mezcla(borde, col, (0.2, 0.18, 0.15))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.6)
    N.poner("Normal", N.relieve(N.ruido(N.vmate("MULTIPLY", N.pos(), (2, 0.3, 2)), 2.0, 4.0), fuerza=0.6,
                                distancia=0.05))
    N.poner("Emission Color", N.mezcla(borde, (0, 0, 0), lin("azul")))
    N.poner("Emission Strength", 0.15)
    m["opercular"] = mt
    return m


# --------------------------------------------------------------------------------------------------------------
# Detalles
# --------------------------------------------------------------------------------------------------------------


def percebe(g, p, n, rnd, s=1.0):
    t1, t2, n = D.marco(n)
    s *= rnd.uniform(0.8, 1.3)
    filas = [[p + (t1 * math.cos(math.tau * k / 6) + t2 * math.sin(math.tau * k / 6)) * r * s + n * h * s
              for k in range(6)] for (r, h) in ((0.11, -0.04), (0.1, 0.02), (0.06, 0.14), (0.035, 0.12))]
    g.loft(filas, "percebe", punta_fin=(p + n * 0.05 * s, (0, 0, 0)))


def coral_ramificado(g, p, dir_, largo, radio, mat, profundidad, rnd):
    """Acropora: ramas que se bifurcan; las puntas, blancas (crecimiento)."""
    fin = p + dir_ * largo
    ultimo = profundidad == 0
    g.tubo([p, (p + fin) / 2, fin], [radio, radio * 0.9, radio * 0.75], "punta" if ultimo else mat, lados=4,
           punta=ultimo)
    if ultimo:
        return
    t1, t2, _ = D.marco(dir_)
    for s in (-1, 1):
        a = rnd.uniform(0, math.tau)
        lado = t1 * math.cos(a) + t2 * math.sin(a)
        nd = (dir_ + lado * s * rnd.uniform(0.45, 0.8)).normalized()
        nd.z = abs(nd.z) * 0.6 + 0.4 * nd.z
        coral_ramificado(g, fin, nd.normalized(), largo * rnd.uniform(0.65, 0.8), radio * 0.72, mat, profundidad - 1,
                         rnd)


def anemona(g, p, n, rnd):
    t1, t2, n = D.marco(n)
    D.disco(g, p + n * 0.02, n, 0.38, "anemona", seg=9, anillos=1, abombado=0.1)
    for k in range(9):
        a = math.tau * k / 9
        b = p + (t1 * math.cos(a) + t2 * math.sin(a)) * 0.24 + n * 0.06
        d = (n + (t1 * math.cos(a) + t2 * math.sin(a)) * 0.7).normalized()
        g.tubo([b, b + d * 0.3, b + d * 0.48 + n * 0.12], [0.06, 0.045, 0.02], "anemona" if k % 3 else "coral_r",
               lados=3, punta=True)


def nido(g, p, n):
    D.toro(g, p + n * 0.12, n, 0.42, 0.11, "nido", seg=12, lados=4)
    D.disco(g, p + n * 0.03, n, 0.42, "nido", seg=10, anillos=1, abombado=-0.05)


def tentaculo(nombre, base, lado, rnd):
    """Tentáculo ventral de 10 studs (0,5 → 0,15), anillado, con dos filas de 9 ventosas en la cara interior."""
    g = T.Geo(nombre)
    fase = rnd.uniform(0, math.tau)
    ctrl = [base, base + Vector((lado * 0.4, -1.0, -1.9)), base + Vector((lado * 0.8, -3.0, -3.3)),
            base + Vector((lado * 0.5, -5.5, -4.0)), base + Vector((lado * 0.1, -8.0, -4.1)),
            base + Vector((lado * 0.5, -9.7, -3.6))]
    curva = C.remuestrear(C.catmull_rom([tuple(p) for p in ctrl], 8, cerrada=False), 0.6)
    n = len(curva)
    pts = [Vector(p) + Vector((lado * 0.15 * math.sin(i * 0.5 + fase), 0, 0)) for i, p in enumerate(curva)]
    rad = [0.5 * (1 - i / (n - 1)) + 0.15 * i / (n - 1) for i in range(n)]
    rad = [r * (1 - 0.06 * (i % 2)) for i, r in enumerate(rad)]  # anillado transversal
    g.tubo(pts, rad, "piel", lados=7, punta=True)
    for fila in (-1, 1):
        for k in range(8):
            i = int(2 + k * (n - 5) / 8)
            p = pts[i]
            t = (pts[i + 1] - pts[i - 1]).normalized()
            abajo = Vector((0, 0, -1)) - t * t.z * -1
            abajo = (abajo - t * abajo.dot(t)).normalized()
            lat = t.cross(abajo).normalized()
            c = p + abajo * rad[i] * 0.9 + lat * fila * rad[i] * 0.42
            r = 0.1 * (1 - 0.4 * k / 9)
            D.toro(g, c, abajo, r * 1.2, r * 0.45, "ventosa", seg=6, lados=3)  # anillo con el centro cóncavo
    return g


def construir(args):
    T.escena_vacia()
    mats = materiales()
    altas = {}
    for nombre in F.PIEZAS:
        t = time.time()
        mn, mx = F.caja(nombre)
        vol, o, p = C.volumen(F.campo_pieza(nombre), mn, mx, F.voxel(nombre) * (1.6 if args.rapido else 1.0))
        v, c = C.malla_de_volumen(vol, o, p)
        ob = T.malla_numpy(nombre + "_alta", v, c)
        T.normales_fuera(ob)
        T.suave(ob)
        T.asignar_material(ob, mats["piel"])
        ob["centro_masa"] = list(C.centro_de_masa(vol, o, p))
        altas[nombre] = ob
        print(f"[forma] {nombre}: {len(c)} tri ({time.time() - t:.1f}s)", flush=True)
    bvh = {n: T.bvh_de([o]) for n, o in altas.items()}
    rnd = random.Random(99)
    geos = {n: T.Geo(n + "_det") for n in F.PIEZAS}
    datos = {}

    # --- Cabeza: ojos, puente de mando, bridas con cascabeles ---
    gc = geos["Cabeza"]
    cor = T.Geo("Ojos_Cornea")
    for lado in (1, -1):
        D.ojo_completo(gc, cor, (lado * F.OJO[0], F.OJO[1], F.OJO[2]), Vector((lado, 0.15, 0.1)), 0.5, alfa=0.85,
                       pupila="horizontal", nictitante=False)
    # Puente de mando (4 × 3) sobre la cabeza, detrás de los ojos.
    p, n = D.proyectar(bvh["Cabeza"], 0.0, 12.0)
    suelo = Vector((0, 12.0, p.z + 0.55))
    filas = [[suelo + Vector((x, y, 0.0)) for x in np.linspace(-2, 2, 5)] for y in np.linspace(-1.5, 1.5, 4)]
    D.lamina(gc, filas, 0.18, 0.18, "madera", Vector((0, 0, 1)), aux_fn=lambda i, j: (j / 4, i / 3, 1.0))
    for (x, y) in ((-1.8, -1.3), (1.8, -1.3), (-1.8, 1.3), (1.8, 1.3), (0, 0)):
        q, m = D.proyectar(bvh["Cabeza"], x, 12.0 + y)
        gc.tubo([q - m * 0.05, suelo + Vector((x, y, -0.09))], [0.09, 0.08], "hueso", lados=5)
    esquinas = [(-2.0, 1.5), (-2.0, -1.5), (2.0, -1.5), (2.0, 1.5)]
    tops = []
    for (x, y) in esquinas + [(-2.0, 0.0), (2.0, 0.0), (0.0, -1.5)]:
        b = suelo + Vector((x, y, 0.09))
        gc.tubo([b, b + Vector((0, 0, 1.0))], [0.05, 0.045], "hueso", lados=5)
    for tramo in ([(-2.0, 1.5), (-2.0, 0.0), (-2.0, -1.5), (0.0, -1.5), (2.0, -1.5), (2.0, 0.0), (2.0, 1.5)],):
        gc.tubo([suelo + Vector((x, y, 1.09)) for x, y in tramo], [0.04] * len(tramo), "hueso", lados=5)
    # Dos timones de hueso (1,5) con cuerdas hacia las bridas.
    for lado in (1, -1):
        c = suelo + Vector((lado * 1.05, 1.15, 0.85))
        gc.tubo([suelo + Vector((lado * 1.05, 1.15, 0.09)), c], [0.06, 0.05], "hueso", lados=5)
        D.toro(gc, c + Vector((0, 0.08, 0)), Vector((0, 1, 0)), 0.7, 0.045, "hueso", seg=14, lados=4)
        for k in range(6):
            a = math.tau * k / 6
            gc.tubo([c + Vector((0, 0.08, 0)), c + Vector((math.cos(a) * 0.72, 0.08, math.sin(a) * 0.72))],
                    [0.025, 0.025], "hueso", lados=3)
        q, m = D.proyectar_hacia(bvh["Cabeza"], (lado * 6.0, 16.5, F.ZC + 1.5), (-lado, 0, 0), 9.0)
        gc.tubo([c + Vector((lado * 0.2, 0.1, -0.3)), (c + q) / 2 + Vector((0, 0, -0.3)), q + m * 0.12],
                [0.025] * 3, "cuerda", lados=3)
    # Toldo de piel curtida (2 × 2) sobre 4 postes.
    for (x, y) in ((-1.0, -0.2), (1.0, -0.2), (-1.0, -1.4), (1.0, -1.4)):
        b = suelo + Vector((x, y, 0.09))
        gc.tubo([b, b + Vector((0, 0, 2.2))], [0.045, 0.04], "hueso", lados=5)
    rej = [[suelo + Vector((x, y, 2.25 - 0.18 * (1 - (2 * u - 1) ** 2))) for u, x in
            zip(np.linspace(0, 1, 5), np.linspace(-1.15, 1.15, 5))] for y in np.linspace(-1.5, -0.1, 4)]
    D.lamina(gc, rej, 0.04, 0.05, "cuero", Vector((0, 0, 1)), aux_fn=lambda i, j: (0, 0, 0))
    datos["Puente_Mando"] = (suelo + Vector((0, 0.3, 0.09 + 0.15)), "Cabeza")
    # Bridas: correa alrededor de la cabeza (sobre el melón y por debajo) con 5 cascabeles de hueso.
    ps, ns = [], []
    for t in np.linspace(0, math.tau, 48, endpoint=False):
        d = Vector((math.cos(t), 0, math.sin(t)))
        q, m = D.proyectar_hacia(bvh["Cabeza"], Vector((0, 16.6, F.ZC + 1.2)) + d * 9.0, -d, 12.0)
        if q is not None:
            ps.append(q)
            ns.append(m)
    D.cinta(gc, ps, ns, 0.5, 0.12, "cuero", cerrada=True, lateral=[Vector((0, 1, 0))] * len(ps), separacion=0.02)
    bajos = sorted(range(len(ps)), key=lambda i: ps[i].z)[:12]
    for k, i in enumerate(sorted(bajos, key=lambda i: ps[i].x)[1::2][:5]):
        c = ps[i] + ns[i] * 0.15 + Vector((0, 0, -0.4))
        gc.tubo([ps[i] + ns[i] * 0.12, c + Vector((0, 0, 0.18))], [0.02, 0.02], "cuerda", lados=3)
        D.cono(gc, c + Vector((0, 0, 0.18)), Vector((0, 0, -1)), 0.32, 0.17, "hueso", lados=7, radio_punta=0.2)
    # --- Mandíbula: 11 dientes cónicos amarillentos (algunos rotos) ---
    gm = geos["Mandibula_Inf"]
    for k in range(11):
        y = 11.0 + k * 0.7
        x = 0.55 * (1 if k % 2 else -1)
        q, m = D.proyectar_hacia(bvh["Mandibula_Inf"], (x, y, 6.5), (0, 0, -1), 4.0)
        if q is None:
            continue
        roto = k in (3, 8)
        D.cono(gm, q - m * 0.05, Vector((0, 0.15, 1)), 0.18 if roto else 0.32, 0.12, "diente", lados=6,
               radio_punta=0.07 if roto else 0.0)
    q, m = D.proyectar(bvh["Mandibula_Inf"], 0.0, 15.5, abajo=True)
    datos["Proa_Inferior"] = (q - Vector((0, 0, 0.35)), "Mandibula_Inf")

    # --- Cuerpo: percebes, arpón oxidado, red dorsal, pasarelas, escaleras, lámparas ---
    g = geos["Cuerpo_Principal"]
    for (cx, cy, abajo) in ((4.8, 6.5, False), (-5.2, -4.5, False), (3.0, -7.5, False), (-2.5, 4.0, True)):
        for _ in range(6):
            x, y = cx + rnd.uniform(-0.7, 0.7), cy + rnd.uniform(-0.8, 0.8)
            q, m = D.proyectar(bvh["Cuerpo_Principal"], x, y, abajo=abajo, z_alto=20)
            if q is not None:
                percebe(g, q - m * 0.03, m, rnd)
    q, m = D.proyectar_hacia(bvh["Cuerpo_Principal"], (-12.0, 2.6, 8.6), (1, 0, -0.1), 14.0)
    if q is not None:
        d = (m + Vector((0, 0.4, 0.3))).normalized()
        g.tubo([q - d * 0.2, q + d * 0.35], [0.07, 0.06], "oxido", lados=6)
        D.cono(g, q + d * 0.3, d, 0.12, 0.13, "oxido", lados=4, radio_punta=0.02)
    # Red dorsal (10 × 6, cuadrícula de 1) delante de la aleta dorsal, con 8 clavos de hueso.
    for x in np.arange(-3.0, 3.01, 1.0):
        pts = []
        for y in np.linspace(8.0, -0.5, 9):
            q, m = D.proyectar(bvh["Cuerpo_Principal"], x, y, z_alto=20)
            if q is not None:
                pts.append(q + m * 0.06)
        if len(pts) > 1:
            g.tubo(pts, [0.035] * len(pts), "cuerda", lados=3)
    for y in np.arange(8.0, -0.6, -1.0):
        pts = []
        for x in np.linspace(-3.0, 3.0, 7):
            q, m = D.proyectar(bvh["Cuerpo_Principal"], x, y, z_alto=20)
            if q is not None:
                pts.append(q + m * 0.06)
        if len(pts) > 1:
            g.tubo(pts, [0.035] * len(pts), "cuerda", lados=3)
    for (x, y) in ((-3, 8), (0, 8), (3, 8), (-3, 3.5), (3, 3.5), (-3, -0.5), (0, -0.5), (3, -0.5)):
        q, m = D.proyectar(bvh["Cuerpo_Principal"], x, y, z_alto=20)
        D.cono(g, q - m * 0.1, m, 0.35, 0.08, "hueso", lados=5)
    # Pasarelas laterales de madera petrificada (0,5 × 8) con ganchos de hueso y barandilla de cuerda.
    for lado in (1, -1):
        tablas = []
        for y in np.linspace(6.0, -2.0, 5):
            q, m = D.proyectar_hacia(bvh["Cuerpo_Principal"], (lado * 12.0, y, F.ZC + 3.4), (-lado, 0, -0.35), 14.0)
            tablas.append((q, m))
        filas = []
        for (q, m) in tablas:
            fuera = Vector((lado, 0, 0))
            base = q + m * 0.25
            filas.append([base - fuera * 0.25, base + fuera * 0.25])
        rej = [[filas[i][j] for i in range(len(filas))] for j in range(2)]
        D.lamina(g, rej, 0.12, 0.12, "madera", Vector((0, 0, 1)), aux_fn=lambda i, j: (i, j / 4, 0.0))
        for (q, m) in tablas:
            D.cono(g, q + m * 0.22 + Vector((lado * 0.3, 0, 0)), -m, 0.5, 0.05, "hueso", lados=4)  # ganchos
        postes = [(q + m * 0.25 + Vector((lado * 0.25, 0, 0)), m) for q, m in tablas]
        for b, _ in postes:
            g.tubo([b, b + Vector((0, 0, 0.9))], [0.04, 0.035], "hueso", lados=4)
        g.tubo([b + Vector((0, 0, 0.85)) for b, _ in postes], [0.025] * len(postes), "cuerda", lados=3)
        # Lámpara de bioluz colgando de la barandilla.
        c = postes[1][0] + Vector((lado * 0.15, 0, 0.55))
        g.tubo([postes[1][0] + Vector((0, 0, 0.85)), c + Vector((0, 0, 0.15))], [0.015, 0.015], "cuerda", lados=3)
        g.elipsoide(c, (0.15, 0.15, 0.15), "lampara", seg=8, anillos=5)
        # Escalera de cuerda (3) desde la red hasta el borde de la apertura.
        top, _ = D.proyectar(bvh["Cuerpo_Principal"], lado * 3.2, -1.0, z_alto=20)
        bajo = Vector((lado * (F.APERTURA[0] + 0.5), F.APERTURA[1], F.APERTURA[2] + 1.9))
        for dy in (-0.25, 0.25):
            g.tubo([top + Vector((0, dy, 0.05)), (top + bajo) / 2 + Vector((lado * 0.6, dy, 0.2)),
                    bajo + Vector((0, dy, 0))], [0.025] * 3, "cuerda", lados=3)
        for k in range(1, 6):
            t = k / 6
            pa = top.lerp(bajo, t) + Vector((lado * 0.6 * math.sin(math.pi * t), 0, 0.2 * math.sin(math.pi * t)))
            g.tubo([pa + Vector((0, -0.25, 0)), pa + Vector((0, 0.25, 0))], [0.03, 0.03], "madera", lados=3)
        datos[f"Acceso_Bodega_{'Der' if lado > 0 else 'Izq'}"] = (bajo + Vector((lado * 0.3, 1.0, 0.0)),
                                                                   "Cuerpo_Principal")

    # --- Aleta dorsal: coral ramificado, coral cerebro, anémonas, nidos y estandarte ---
    gd = geos["Aleta_Dorsal"]
    for (y, mat, s) in ((-1.4, "coral_n", 1.0), (-6.0, "coral_r", 0.9)):
        q, m = D.proyectar(bvh["Aleta_Dorsal"], 0.0, y, z_alto=25)
        for k in range(3):
            d = (Vector((rnd.uniform(-0.5, 0.5), rnd.uniform(-0.5, 0.5), 1))).normalized()
            coral_ramificado(gd, q - m * 0.05, d, 1.25 * s, 0.2 * s, mat, 3, rnd)
    q, m = D.proyectar_hacia(bvh["Aleta_Dorsal"], (4.0, -4.6, 12.6), (-1, 0, -0.2), 8.0)
    gd.elipsoide(q + m * 0.45, (0.8, 0.8, 0.6), "cerebro", seg=12, anillos=7)
    for (x, y) in ((0.4, -2.6), (-0.5, -3.1), (0.3, -5.2), (-0.6, -6.9)):
        q, m = D.proyectar(bvh["Aleta_Dorsal"], x, y, z_alto=25)
        if q is not None:
            anemona(gd, q - m * 0.03, m, rnd)
    for (x, y) in ((1.6, -8.8), (-1.8, -7.8)):
        q, m = D.proyectar(bvh["Cuerpo_Principal"], x, y, z_alto=25)
        nido(geos["Cuerpo_Principal"], q, m)
    cima, m = D.proyectar(bvh["Aleta_Dorsal"], 0.0, -3.6, z_alto=25)
    gd.tubo([cima - m * 0.1, cima + Vector((0, 0, 3.0))], [0.09, 0.07], "hueso", lados=6)
    D.cono(gd, cima + Vector((0, 0, 3.0)), Vector((0, 0, 1)), 0.35, 0.1, "hueso", lados=5)
    rej = [[cima + Vector((0.05 + 0.15 * math.sin(u * 4 + v), -0.1 - 2.0 * u, 2.9 - 1.0 * v)) for u in
            np.linspace(0, 1, 8)] for v in np.linspace(0, 1, 5)]
    D.lamina(gd, rej, 0.04, 0.05, "tela", Vector((1, 0, 0)), aux_fn=lambda i, j: (i / 4, j / 7, 0.0))
    datos["Vigia_Dorsal"] = (cima + Vector((0, 0.6, 0.35)), "Aleta_Dorsal")

    # --- Aletas pectorales: percebes en el borde y puesto de artillero (2 × 2) ---
    for lado, nom in ((1, "Der"), (-1, "Izq")):
        ga = geos[f"Aleta_Pectoral_{nom}"]
        for k in range(5):
            x = lado * (8.0 + k * 0.9)
            q, m = D.proyectar(bvh[f"Aleta_Pectoral_{nom}"], x, 2.6 - k * 0.55 + 1.3, z_alto=20)
            if q is not None:
                percebe(ga, q - m * 0.02, m, rnd, 0.9)
        c = Vector((lado * 7.6, 2.8, 0))
        q, m = D.proyectar(bvh[f"Aleta_Pectoral_{nom}"], c.x, c.y, z_alto=20)
        base = q + Vector((0, 0, 0.35))
        D.caja(ga, base, (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))), (2.0, 2.0, 0.15), "madera")
        tops = []
        for (dx, dy) in ((-0.95, 0.95), (0.95, 0.95), (0.95, -0.95), (-0.95, -0.95)):
            qq, mm = D.proyectar(bvh[f"Aleta_Pectoral_{nom}"], c.x + dx, c.y + dy, z_alto=20)
            if qq is not None:
                D.cono(ga, qq - mm * 0.12, Vector((0, 0, 1)), base.z - qq.z + 0.2, 0.07, "hueso", lados=5)
            b = base + Vector((dx, dy, 0.08))
            ga.tubo([b, b + Vector((0, 0, 0.8))], [0.04, 0.035], "hueso", lados=4)
            tops.append(b + Vector((0, 0, 0.8)))
        barandilla = tops[:3]  # tres lados (el cuarto queda abierto hacia el cuerpo)
        ga.tubo(barandilla, [0.03] * len(barandilla), "hueso", lados=4)
        lamp = tops[0] + Vector((0, 0, -0.35))
        ga.elipsoide(lamp, (0.15, 0.15, 0.15), "lampara", seg=8, anillos=5)
        ga.tubo([tops[0], lamp + Vector((0, 0, 0.15))], [0.015, 0.015], "cuerda", lados=3)
        datos[f"Artillero_{nom}"] = (base + Vector((0, 0, 0.08 + 0.15)), f"Aleta_Pectoral_{nom}")
    # Lámparas del puente (4).
    for (x, y) in ((-2.0, 1.5), (2.0, 1.5)):
        b = suelo + Vector((x, y, 1.09))
        c = b + Vector((0, 0.15, -0.45))
        gc.tubo([b, c + Vector((0, 0, 0.15))], [0.015, 0.015], "cuerda", lados=3)
        gc.elipsoide(c, (0.15, 0.15, 0.15), "lampara", seg=8, anillos=5)
    # Timonel en la base de la cola.
    q, m = D.proyectar(bvh["Cola_Base"], 0.0, -13.6, z_alto=25)
    datos["Timonel_Cola"] = (q + m * 0.3, "Cola_Base")

    # --- Placas operculares (geometría) y tentáculos ---
    geometricas, piv = {}, {}
    for lado, nom in ((1, "Der"), (-1, "Izq")):
        go = T.Geo(f"Placa_Opercular_{nom}")
        ax, ay, az = F.APERTURA
        rej = []
        for i, w in enumerate(np.linspace(-1, 1, 7)):
            fila = []
            for j, v in enumerate(np.linspace(-1, 1, 9)):
                r = max(abs(w), abs(v))
                e = math.sqrt(max(0.0, 1 - min(1.0, (w * w + v * v) ** 0.5) ** 2))
                y = ay + v * 2.7 * math.sqrt(max(0.0, 1 - (w * 0.75) ** 2))
                z = az + w * 1.75
                x = lado * (ax + 0.95 + 0.38 * e - 0.12 * (v * v))
                fila.append(Vector((x, y, z)))
            rej.append(fila)
        D.lamina(go, rej, 0.3, 0.34, "opercular", Vector((lado, 0, 0)),
                 aux_fn=lambda i, j: (max(abs(i / 3 - 1), abs(j / 4 - 1)), 0, 0))
        for k in range(4):
            c = Vector((lado * (ax + 1.35), ay + rnd.uniform(-1.6, 1.6), az + rnd.uniform(-0.9, 0.9)))
            percebe(go, c, Vector((lado, 0, 0)), rnd, 0.8)
        geometricas[f"Placa_Opercular_{nom}"] = go.objeto(mats)
        piv[f"Placa_Opercular_{nom}"] = (lado * (ax + 0.95), ay, az + 1.8)
    for k, (x, y, lado) in enumerate(((-2.4, 7.6, -1), (2.4, 7.6, 1), (-3.0, 1.0, -1), (3.0, 1.0, 1)), start=1):
        q, m = D.proyectar(bvh["Cuerpo_Principal"], x, y, abajo=True, z_alto=20)
        base = q + Vector((0, 0, 0.25))
        gt = tentaculo(f"Tentaculo_{k}", base, lado, rnd)
        geometricas[f"Tentaculo_{k}"] = gt.objeto(mats)
        piv[f"Tentaculo_{k}"] = tuple(base)

    det = {n: [gg.objeto(mats)] for n, gg in geos.items() if len(gg.bm.faces)}
    return altas, det, geometricas, piv, cor.objeto(mats), datos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="1")
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    altas, det, geometricas, piv, cornea, datos = construir(args)
    pivotes = {n: F.pivote(n) for n in F.PIEZAS}
    pivotes["Cuerpo_Principal"] = (0.0,) + tuple(altas["Cuerpo_Principal"]["centro_masa"])[1:]
    pivotes.update(piv)
    pivotes["Ojos_Cornea"] = F.CUELLO
    padre = {"Cuerpo_Principal": None, "Cabeza": "Cuerpo_Principal", "Mandibula_Inf": "Cabeza",
             "Aleta_Pectoral_Izq": "Cuerpo_Principal", "Aleta_Pectoral_Der": "Cuerpo_Principal",
             "Aleta_Dorsal": "Cuerpo_Principal", "Cola_Base": "Cuerpo_Principal", "Cola_Media": "Cola_Base",
             "Cola_Punta": "Cola_Media", "Placa_Opercular_Izq": "Cuerpo_Principal",
             "Placa_Opercular_Der": "Cuerpo_Principal", "Ojos_Cornea": "Cabeza"}
    for k in range(1, 5):
        padre[f"Tentaculo_{k}"] = "Cuerpo_Principal"
    orden = ["Cuerpo_Principal", "Cabeza", "Mandibula_Inf", "Aleta_Pectoral_Izq", "Aleta_Pectoral_Der", "Aleta_Dorsal",
             "Cola_Base", "Cola_Media", "Cola_Punta"] + [f"Tentaculo_{k}" for k in range(1, 5)] + \
            ["Placa_Opercular_Izq", "Placa_Opercular_Der"]
    peso = {"Cuerpo_Principal": 3.2, "Cabeza": 2.4, "Mandibula_Inf": 0.6, "Aleta_Pectoral_Izq": 0.7,
            "Aleta_Pectoral_Der": 0.7, "Aleta_Dorsal": 0.6, "Cola_Base": 0.7, "Cola_Media": 0.5, "Cola_Punta": 1.0}
    vidrio = bpy.data.materials.new("cornea_render")
    N = T.Nodos(vidrio)
    N.poner("Base Color", T.srgb("#FFF2C0"))
    N.poner("Roughness", 0.02)
    N.poner("Transmission Weight", 1.0)
    cfg = dict(
        nombre=NOMBRE, titulo="LEVIATÁN ESTELAR", rol="Nave nodriza viviente", jinetes="8-12",
        neon=["#FFD700", "#00BFFF"], presupuesto=PRESUPUESTO, salida=args.salida, ronda=args.ronda,
        rapido=args.rapido, altas=altas, detalles=det, geometricas=geometricas,
        soldadas={"Ojos_Cornea": (cornea, "Cabeza")}, peso_tris=peso, pivotes=pivotes, padre=padre, orden=orden,
        montajes=datos, prioridad_uv={"Cabeza": 1.3, "Aleta_Dorsal": 1.4, "Ojos_Cornea": 1.5, "Cuerpo_Principal": 1.0,
                                      "Tentaculo_1": 0.8, "Tentaculo_2": 0.8, "Tentaculo_3": 0.8, "Tentaculo_4": 0.8},
        render_material={cornea: vidrio}, radio_estudio=22.0, exposicion=0.9, emision_render=3.0,
        cerca=[("Cabeza y puente", 35, 25, (0, 14.0, 10.5), 5.5), ("Lomo con coral", 60, 35, (0, -3.8, 13.5), 3.4),
               ("Ojo y bridas", -75, 10, (3.9, 14.5, 8.0), 2.4), ("Opercular y escalera", -80, 15, (6.3, -1.0, 8.0), 3.8),
               ("Tentáculos", 40, -30, (0, 2.0, 1.0), 6.5), ("Aleta caudal HORIZONTAL", 150, 30, (0, -19.5, 8.6), 5.5)],
        notas_json=["La aleta caudal es HORIZONTAL (como una ballena).",
                    "Ojos_Cornea va soldada a la Cabeza: en Roblox, material Glass o Transparency 0,35.",
                    "Las placas operculares pivotan en su bisagra superior (se abren como puertas de garaje)."],
    )
    bestia.terminar(cfg)


if __name__ == "__main__":
    main()
