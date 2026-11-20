"""
BESTIA 5 — ESCARABAJO ABISAL (tanque pesado, 2-3 jinetes).

Escarabajo rinoceronte cruzado con un acorazado, del tamaño de un autobús: quitina negra verdosa iridiscente con
cráteres de impacto, cristales ámbar crecidos en las grietas (y una geoda en la herida del élitro izquierdo), cuerno con
6 estrías y una muesca rota, mandíbulas en hoz aserradas, 6 patas de 3 segmentos con espinas y garras, ojos
compuestos verdes. Arnés de asedio: silla de respaldo alto, cadenas oxidadas, ariete en V, plataforma del artillero,
3 cinchas remendadas, alforjas con alquitrán y trofeos (bandera desgarrada y dos cascos abollados).

Rig (14 piezas): Torso (raíz), Cabeza, Mandibula_{Izq,Der}, Cuerno_Central, Elitro_{Izq,Der},
Pata_{Del,Med,Tras}_{Izq,Der}, Abdomen.
Montaje: Montura_Piloto, Montura_Artillero, Montura_Lateral_Izq, Montura_Lateral_Der, Punto_Carga.

Uso: python bestias/herramientas/escarabajo_abisal.py --salida bestias/escarabajo_abisal --ronda 1 [--rapido]
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
import escarabajo_forma as F  # noqa: E402
import taller as T  # noqa: E402

NOMBRE = "escarabajo_abisal"
PRESUPUESTO = 20000
COL = {"caparazon": "#1A2F1A", "vientre": "#8A8A7A", "cristal": "#FF8C00", "ojo": "#39FF14", "cuerno": "#2A1A0A",
       "cuero": "#3A2A1A", "hueso": "#D4C8A0", "metal": "#2A2A2A", "alquitran": "#0A0A0A", "madera": "#5A5048",
       "remiendo": "#7A6248", "bandera": "#6A1E1E"}
SURCOS_TORSO = [3.7, 3.1, 2.5, 1.9]          # 5 placas dorsales
ELITRO_Y = (1.42, -6.95)
CINCHAS = [2.2, -0.3, -4.6]


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


def material_quitina(nombre, elitro=False):
    """Quitina negra verdosa iridiscente: placas lisas, juntas rugosas, cráteres con grietas estrelladas, líneas
    verdes entre placas, ojos compuestos facetados, espiráculos con branquias rojas y vientre gris segmentado."""
    mat = bpy.data.materials.new(nombre)
    N = T.Nodos(mat)
    P = N.pos()
    px_, py_, pz_ = N.sep(P)
    nx_, ny_, nz_ = N.sep(N.normal())
    vientre = N.mate("SUBTRACT", 1.0, smooth(N, -0.5, -0.1, nz_))
    irid = N.ruido(P, 0.5, 2.0, 0.5)
    col = N.mezcla(smooth(N, 0.3, 0.5, irid), (0.006, 0.012, 0.02), lin("caparazon"))
    col = N.mezcla(smooth(N, 0.55, 0.72, irid), col, (0.025, 0.012, 0.04))   # reflejo violáceo
    poros = N.mate("LESS_THAN", N.voronoi(P, 30.0 if elitro else 18.0, rasgo="F1"), 0.12)
    # Juntas entre placas (surcos del tórax y segmentos del abdomen): rugosas y con una línea verde tenue.
    junta = None
    for y in SURCOS_TORSO + [-3.9, -5.2, -6.5, -7.6]:
        d = N.mate("ABSOLUTE", N.mate("SUBTRACT", py_, y))
        j = N.mate("SUBTRACT", 1.0, smooth(N, 0.02, 0.09, d))
        junta = j if junta is None else N.mate("MAXIMUM", junta, j)
    if elitro:
        junta = N.mate("MULTIPLY", junta, 0.0)
    escalon = N.mate("PINGPONG", N.mate("MULTIPLY", py_, 1.0), 0.3)  # placas superpuestas (escalón suave)
    crater = None
    for (c, r) in F.CRATERES + ([((-2.2, -2.6, 4.2), 0.5)] if elitro else []):
        d = N.vmate("LENGTH", N.vmate("SUBTRACT", P, c))
        k = N.mate("SUBTRACT", 1.0, smooth(N, r * 0.9, r * 1.6, d))
        crater = k if crater is None else N.mate("MAXIMUM", crater, k)
    grietas = N.mate("SUBTRACT", 1.0, smooth(N, 0.0, 0.05, N.voronoi(P, 7.0, rasgo="DISTANCE_TO_EDGE")))
    grietas = N.mate("MULTIPLY", grietas, crater)
    ojo = None
    for lado in (1, -1):
        q = N.vmate("DIVIDE", N.vmate("SUBTRACT", P, (lado * F.OJO[0], F.OJO[1], F.OJO[2])), (0.5, 0.67, 0.47))
        o = N.mate("SUBTRACT", 1.0, smooth(N, 0.9, 1.0, N.vmate("LENGTH", q)))
        ojo = o if ojo is None else N.mate("MAXIMUM", ojo, o)
    facetas = smooth(N, 0.0, 0.12, N.voronoi(P, 22.0, rasgo="DISTANCE_TO_EDGE", aleatorio=0.05))
    arriba = smooth(N, 0.25, 0.6, nz_)
    fina = None
    for y in SURCOS_TORSO + [-3.9, -5.2, -6.5, -7.6]:
        d = N.mate("ABSOLUTE", N.mate("SUBTRACT", py_, y))
        j = N.mate("SUBTRACT", 1.0, smooth(N, 0.01, 0.035, d))
        fina = j if fina is None else N.mate("MAXIMUM", fina, j)
    luz_lineas = N.mate("MULTIPLY", N.mate("MULTIPLY", fina, arriba), 0.0 if elitro else 1.0)
    col = N.mezcla(vientre, col, N.mezcla(N.mate("MULTIPLY", smooth(N, 0.4, 0.8, N.ruido(P, 3.0)), 0.4),
                                          lin("vientre"), (0.3, 0.3, 0.26)))
    col = N.mezcla(N.mate("MULTIPLY", junta, 0.7), col, (0.02, 0.02, 0.02))
    col = N.mezcla(N.mate("MULTIPLY", crater, 0.6), col, (0.05, 0.05, 0.04))
    col = N.mezcla(grietas, col, (0.12, 0.1, 0.07))
    col = N.mezcla(ojo, col, N.mezcla(facetas, (0.0, 0.02, 0.0), (0.04, 0.35, 0.03)))
    # Espiráculos con branquias rojas y glándula de alquitrán.
    branq = None
    for y in (2.0, 0.3, -3.6, -5.6):
        for lado in (1, -1):
            x = lado * (3.05 if y > -2 else 2.35)
            d = N.vmate("LENGTH", N.vmate("DIVIDE", N.vmate("SUBTRACT", P, (x, y, 2.45)), (0.14, 0.22, 0.1)))
            b = N.mate("SUBTRACT", 1.0, smooth(N, 0.8, 1.0, d))
            branq = b if branq is None else N.mate("MAXIMUM", branq, b)
    col = N.mezcla(branq, col, (0.45, 0.04, 0.03))
    q = N.vmate("LENGTH", N.vmate("DIVIDE", N.vmate("SUBTRACT", P, (0, -7.4, 1.0)), (0.7, 0.9, 0.4)))
    alq = N.mate("SUBTRACT", 1.0, smooth(N, 0.7, 1.1, N.mate("ADD", q, N.mate("MULTIPLY", N.ruido(P, 4.0), 0.4))))
    col = N.mezcla(alq, col, lin("alquitran"))
    # Marca de garra diagonal en la placa frontal de la cabeza.
    garra = N.mate("MULTIPLY", N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("SUBTRACT", N.mate("ADD", px_,
                   N.mate("MULTIPLY", pz_, 1.2)), 4.35)), 0.04),
                   N.mate("MULTIPLY", N.mate("GREATER_THAN", py_, 6.4), N.mate("GREATER_THAN", pz_, 3.0)))
    col = N.mezcla(garra, col, (0.3, 0.3, 0.27))
    N.poner("Base Color", col)
    rug = N.mezcla(N.mate("MAXIMUM", junta, crater), 0.22, 0.75)
    rug = N.mezcla(vientre, rug, 0.6)
    rug = N.mezcla(alq, rug, 0.04)
    N.poner("Roughness", N.sep(rug)[0])
    N.poner("Metallic", N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, N.mate("MAXIMUM", vientre, junta)), 0.2))
    h = N.mate("ADD", N.mate("MULTIPLY", escalon, 0.5), N.mate("MULTIPLY", poros, -0.4))
    h = N.mate("SUBTRACT", h, N.mate("MULTIPLY", grietas, 1.2))
    h = N.mate("ADD", h, N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, facetas), N.mate("MULTIPLY", ojo, -1.0)))
    h = N.mate("ADD", h, N.mate("MULTIPLY", N.ruido(P, 25.0, 4.0), 0.15))
    N.poner("Normal", N.relieve(h, fuerza=0.55, distancia=0.03))
    luz = N.mate("ADD", N.mate("MULTIPLY", luz_lineas, 0.3), N.mate("MULTIPLY", ojo, N.mate("MULTIPLY", facetas, 0.45)))
    N.poner("Emission Color", N.mezcla(N.mate("MINIMUM", luz, 1.0), (0, 0, 0), lin("ojo")))
    N.poner("Emission Strength", 1.0)
    return mat


def materiales():
    m = {"piel": material_quitina("piel"), "elitro": material_quitina("elitro", elitro=True)}
    mat = bpy.data.materials.new("cuerno")
    N = T.Nodos(mat)
    py_ = N.sep(N.pos())[1]
    col = N.mezcla(smooth(N, 0.0, 1.0, N.ruido(N.pos(), 2.0)), (0.008, 0.006, 0.004), lin("cuerno"))
    puntas = smooth(N, 8.6, 9.3, py_)  # puntas de las mandíbulas desgastadas (gris acero)
    col = N.mezcla(puntas, col, (0.25, 0.26, 0.28))
    N.poner("Base Color", col)
    N.poner("Roughness", N.sep(N.mezcla(puntas, 0.3, 0.5))[0])
    N.poner("Normal", N.relieve(N.ruido(N.vmate("MULTIPLY", N.pos(), (1, 4, 1)), 12.0, 4.0), fuerza=0.4,
                                distancia=0.01))
    m["cuerno"] = mat
    for nombre, col, rug, met, emi, f, rel in (
            ("cristal", "cristal", 0.08, 0.0, "cristal", 1.0, None), ("hueso", "hueso", 0.5, 0.0, None, 0, (14.0, 0.35)),
            ("madera", "madera", 0.85, 0.0, None, 0, (30.0, 0.6)), ("alquitran", "alquitran", 0.04, 0.0, None, 0, None),
            ("bandera", "bandera", 0.9, 0.0, None, 0, (40.0, 0.5)), ("garra", "#151210", 0.35, 0.0, None, 0, (40.0, 0.3))):
        mt, _ = T.material_simple(nombre, lin(col), rug=rug, metal=met, emision=lin(emi) if emi else None, fuerza=f,
                                  relieve=rel)
        m[nombre] = mt
    # Metal negro oxidado (cadenas, ariete, cascos).
    mt = bpy.data.materials.new("metal")
    N = T.Nodos(mt)
    oxido = smooth(N, 0.55, 0.7, N.ruido(N.pos(), 5.0, 6.0))
    N.poner("Base Color", N.mezcla(oxido, lin("metal"), (0.25, 0.08, 0.02)))
    N.poner("Metallic", N.sep(N.mezcla(oxido, 0.85, 0.1))[0])
    N.poner("Roughness", N.sep(N.mezcla(oxido, 0.5, 0.9))[0])
    N.poner("Normal", N.relieve(N.mate("ADD", oxido, N.ruido(N.pos(), 40.0, 4.0)), fuerza=0.5, distancia=0.01))
    m["metal"] = mt
    # Cuero viejo con remiendos más claros y costuras.
    mt = bpy.data.materials.new("cuero")
    N = T.Nodos(mt)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    parche = N.mate("MULTIPLY", N.mate("LESS_THAN", N.mate("PINGPONG", a[0], 1.3), 0.22),
                    N.mate("GREATER_THAN", a[2], 0.5))
    col = N.mezcla(smooth(N, 0.4, 0.75, N.ruido(N.pos(), 3.0, 4.0)), lin("cuero"), (0.1, 0.07, 0.04))
    col = N.mezcla(parche, col, lin("remiendo"))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.7)
    N.poner("Normal", N.relieve(N.mate("ADD", N.ruido(N.pos(), 45.0, 4.0), N.mate("MULTIPLY", parche, 0.5)),
                                fuerza=0.5, distancia=0.01))
    m["cuero"] = mt
    return m


# --------------------------------------------------------------------------------------------------------------
# Detalles
# --------------------------------------------------------------------------------------------------------------


def cristal(g, base, eje, largo, radio, rnd):
    """Cristal mineral hexagonal (prisma con punta), ámbar luminoso."""
    eje = Vector(eje).normalized()
    t1, t2, _ = D.marco(eje)
    g0 = rnd.uniform(0, math.pi)
    abajo = [base - eje * 0.08 + (t1 * math.cos(g0 + k * math.pi / 3) + t2 * math.sin(g0 + k * math.pi / 3)) * radio
             for k in range(6)]
    arriba = [base + eje * largo * 0.72 + (t1 * math.cos(g0 + k * math.pi / 3) + t2 * math.sin(g0 + k * math.pi / 3))
              * radio * 0.92 for k in range(6)]
    g.loft([abajo, arriba], "cristal", punta_fin=(base + eje * largo, (0, 0, 0)), tapar_inicio=True)


def racimo(g, p, n, rnd, cuantos, escala=1.0):
    t1, t2, n = D.marco(n)
    for i in range(cuantos):
        a = rnd.uniform(0, math.tau)
        off = (t1 * math.cos(a) + t2 * math.sin(a)) * rnd.uniform(0.0, 0.18) * escala
        eje = (n + (t1 * math.cos(a) + t2 * math.sin(a)) * rnd.uniform(0.15, 0.7)).normalized()
        cristal(g, p + off, eje, rnd.uniform(0.15, 0.32) * escala, rnd.uniform(0.04, 0.08) * escala, rnd)


def elitro(g, bvh, lado, rnd):
    """Élitro: concha de 0,25 que envuelve el lomo (de la línea media al costado), con 3 nervaduras longitudinales y,
    en el izquierdo, el gran cráter de 1 stud con su geoda de cristales. Devuelve el pivote (bisagra)."""
    ys = np.linspace(ELITRO_Y[0], ELITRO_Y[1], 19)
    nth = 14
    rej = []
    crater_c = None
    for i, y in enumerate(ys):
        v = i / (len(ys) - 1)
        th_min = math.radians(16 + 62 * C.sstep(0.82, 1.0, v) + 28 * C.sstep(0.12, 0.0, v))
        fila = []
        for j in range(nth):
            u = j / (nth - 1)
            th = math.radians(88.5) + (th_min - math.radians(88.5)) * u
            d = Vector((lado * math.cos(th), 0, math.sin(th)))
            p = None
            for dy in (0.0, 0.06, -0.06, 0.15, -0.15):  # la junta de 0,02 entre piezas puede dejar pasar el rayo
                p, n = D.proyectar_hacia(bvh, Vector((0, y + dy, 2.35)) + d * 6.0, -d, 8.0)
                if p is not None:
                    p = p - Vector((0, dy, 0))
                    break
            off = 0.115 + 0.125
            for uk in (0.25, 0.5, 0.75):  # nervaduras
                off += 0.1 * math.exp(-((u - uk) / 0.045) ** 2) * (1 - C.sstep(0.85, 1.0, v))
            if lado < 0:  # cráter de impacto (1 stud) en el élitro izquierdo
                dist = math.hypot((u - 0.42) * 3.0, (v - 0.5) * 8.4)
                off += -0.16 * math.exp(-(dist / 0.34) ** 2) + 0.09 * math.exp(-((dist - 0.5) / 0.12) ** 2)
                if crater_c is None and abs(u - 0.42) < 0.04 and abs(v - 0.5) < 0.03:
                    crater_c = (p, n)
            fila.append(p + n * off)
        rej.append(fila)
    # Suavizado de la rejilla (quita las ondas que dejan las proyecciones), sin mover el borde.
    for _ in range(3):
        nueva = [fila[:] for fila in rej]
        for i in range(1, len(rej) - 1):
            for j in range(1, nth - 1):
                nueva[i][j] = (rej[i][j] * 2 + rej[i - 1][j] + rej[i + 1][j] + rej[i][j - 1] + rej[i][j + 1]) / 6
        rej = nueva
    D.lamina(g, rej, 0.25, 0.28, "elitro", Vector((lado, 0, 1)), aux_fn=lambda i, j: (i / 18, j / 13, 0.0))
    if lado < 0:
        if crater_c is None:
            p, n = D.proyectar_hacia(bvh, Vector((0, (ELITRO_Y[0] + ELITRO_Y[1]) / 2, 2.35)) +
                                     Vector((-0.74, 0, 0.67)) * 6.0, Vector((0.74, 0, -0.67)), 8.0)
            crater_c = (p, n)
        p, n = crater_c
        racimo(g, p + n * 0.05, n, rnd, 8, escala=2.3)  # geoda en la herida
    return Vector((lado * 0.05, ELITRO_Y[0], rej[0][0].z - 0.12))


def construir(args):
    T.escena_vacia()
    mats = materiales()
    altas = {}
    for nombre in F.PIEZAS:
        t = time.time()
        mn, mx = F.caja(nombre)
        vol, o, p = C.volumen(F.campo_pieza(nombre), mn, mx, F.voxel(nombre) * (1.7 if args.rapido else 1.0))
        v, c = C.malla_de_volumen(vol, o, p)
        ob = T.malla_numpy(nombre + "_alta", v, c)
        T.normales_fuera(ob)
        T.suave(ob)
        T.asignar_material(ob, mats["cuerno"] if nombre.startswith(("Mandibula", "Cuerno")) else mats["piel"])
        ob["centro_masa"] = list(C.centro_de_masa(vol, o, p))
        altas[nombre] = ob
        print(f"[forma] {nombre}: {len(c)} tri ({time.time() - t:.1f}s)", flush=True)
    bvh = {n: T.bvh_de([o]) for n, o in altas.items()}
    cuerpo = T.bvh_de([altas["Torso"], altas["Abdomen"]])
    rnd = random.Random(55)
    geos = {n: T.Geo(n + "_det") for n in F.PIEZAS}

    # Cristales en las grietas entre placas del tórax y en el dorso del abdomen.
    for (x, y, k) in ((1.45, 3.1, 4), (-0.6, 2.5, 5), (-1.9, 3.7, 3)):
        p, n = D.proyectar(bvh["Torso"], x, y)
        racimo(geos["Torso"], p - n * 0.03, n, rnd, k)
    for (x, y) in ((0.6, -7.5), (-0.9, -8.0)):
        p, n = D.proyectar(bvh["Abdomen"], x, y)
        racimo(geos["Abdomen"], p - n * 0.03, n, rnd, 1, escala=1.4)

    # Cabeza: antenas de 4 segmentos, palpos maxilares.
    g = geos["Cabeza"]
    for lado in (1, -1):
        base = Vector((lado * 0.78, 6.95, 3.35))
        dir_ = Vector((lado * 0.45, 0.75, 0.48)).normalized()
        pts, rad = [], []
        for k in range(9):
            t = k / 8
            pts.append(base + dir_ * t * 1.05 + Vector((lado * 0.1 * t * t, 0, 0)))
            rad.append((0.13 - 0.04 * t) * (1.0 if k % 2 == 0 else 0.78))
        g.tubo(pts, rad, "cuerno", lados=6)
        for (dx, dz) in ((0.32, 0.0), (0.55, 0.15)):
            b = Vector((lado * dx, 7.15, 2.15 + dz))
            g.tubo([b, b + Vector((lado * 0.08, 0.25, -0.25)), b + Vector((lado * 0.12, 0.42, -0.45))],
                   [0.07, 0.055, 0.04], "cuerno", lados=5, punta=True)
    # Ariete frontal en V (hueso y metal) con 3 púas, sobre la placa frontal.
    c = Vector((0, 7.75, 3.0))
    for lado in (1, -1):
        brazo = Vector((lado * 0.95, -0.55, 0.0))
        D.caja(g, c + brazo * 0.5, (brazo.normalized(), Vector((0, 0, 1)).cross(brazo.normalized()) * -lado,
                                    Vector((0, 0, 1))), (1.12, 0.22, 0.42), "hueso")
        D.caja(g, c + brazo * 0.5 + Vector((0, 0.08, 0.0)), (brazo.normalized(),
               Vector((0, 0, 1)).cross(brazo.normalized()) * -lado, Vector((0, 0, 1))), (1.14, 0.08, 0.46), "metal")
    for dx in (-0.5, 0.0, 0.5):
        D.cono(g, c + Vector((dx, 0.1 - abs(dx) * 0.55, 0.0)), Vector((dx * 0.3, 1, 0.05)), 0.42 - abs(dx) * 0.2,
               0.1, "metal", lados=6)
    # Mandíbulas: dientes aserrados en el borde interior (9 por mandíbula).
    for lado, nom in ((1, "Der"), (-1, "Izq")):
        s = (lambda p: p) if lado > 0 else F.esp
        pts = C.remuestrear(C.catmull_rom([s(p) for p in F.MANDIBULA], 8, cerrada=False), 0.1)
        gm = geos[f"Mandibula_{nom}"]
        for k in range(9):
            i = int(3 + k * (len(pts) - 6) / 9)
            p = Vector(pts[i])
            tang = Vector(pts[i + 1]) - Vector(pts[i - 1])
            hacia = Vector((-lado, 0, 0)) - tang.normalized() * tang.normalized().x * -lado
            hacia.z = 0
            r = 0.2 * (1 - k / 11)
            D.cono(gm, p + hacia.normalized() * r * 0.6, hacia, 0.16 - 0.008 * k, 0.05, "cuerno", lados=4)

    # Patas: espinas en la tibia, 2 garras, almohadilla (medias) y espolón (traseras).
    for tipo, pts in F.PATAS.items():
        for lado, nom in ((1, "Der"), (-1, "Izq")):
            s = (lambda p: Vector(p)) if lado > 0 else (lambda p: Vector(F.esp(p)))
            h, k, a, t = (s(p) for p in pts)
            g = geos[f"Pata_{tipo}_{nom}"]
            for f in (0.3, 0.55, 0.8):
                p = k.lerp(a, f)
                d = (Vector((0, -1, 0)) + Vector((lado * 0.4, 0, 0))).normalized()
                D.cono(g, p + d * F.GROSOR_PATA[tipo][1] * 0.6, d + Vector((0, 0, 0.3)), 0.22, 0.05, "garra", lados=4)
            fin = t
            dir_ = (t - a).normalized()
            for sx in (-1, 1):
                D.cono(g, fin, dir_ + Vector((sx * 0.35, 0.2, -0.6)), 0.4 if tipo == "Del" else 0.3, 0.07, "garra",
                       lados=5, curva=Vector((0, 0, -0.06)))
            if tipo == "Med":
                g.elipsoide(fin + Vector((0, 0, -0.05)), (0.14, 0.2, 0.06), "alquitran", seg=8, anillos=4)
            if tipo == "Tras":
                D.cono(g, a, Vector((0, -1, -0.3)), 0.32, 0.07, "garra", lados=5)

    # Arnés: silla de respaldo alto, cadenas, cinchas, plataforma, alforjas y trofeos.
    g = geos["Torso"]
    p, n = D.proyectar(bvh["Torso"], 0.0, 2.75)
    base = p + Vector((0, 0, 0.05))
    g.caja_redonda(base + Vector((0, 0, 0.12)), (1.25, 1.1, 0.26), "hueso", seg=2, redondeo=0.5)
    g.caja_redonda(base + Vector((0, 0.05, 0.32)), (1.0, 0.85, 0.16), "cuero", seg=2, aux=(0.0, 0.5, 0.0),
                   redondeo=0.6)
    for lado in (1, -1):
        g.tubo([base + Vector((lado * 0.45, -0.5, 0.2)), base + Vector((lado * 0.45, -0.62, 1.2))], [0.06, 0.05],
               "hueso", lados=6)
    g.caja_redonda(base + Vector((0, -0.6, 0.78)), (0.92, 0.12, 0.9), "cuero", seg=2, aux=(0.0, 0.5, 0.0),
                   redondeo=0.5)  # respaldo de 1 stud
    for lado in (1, -1):  # estribos
        q, m = D.proyectar_hacia(bvh["Torso"], (lado * 6.0, 2.6, 3.0), (-lado, 0, -0.35), 8.0)
        g.tubo([base + Vector((lado * 0.6, 0, 0.1)), q + m * 0.05], [0.03, 0.03], "cuero", lados=4)
        D.toro(g, q + m * 0.15 + Vector((0, 0, -0.12)), Vector((0, 1, 0)), 0.13, 0.035, "hueso", seg=10, lados=4)
    piloto = base + Vector((0, 0.05, 0.40 + 0.15))
    # Cadenas de metal oxidado hasta las anillas de la placa frontal (van con la cabeza).
    gc = geos["Cabeza"]
    for lado in (1, -1):
        anilla = Vector((lado * 0.48, 6.75, 3.62))
        D.toro(gc, anilla, Vector((1, 0, 0)), 0.1, 0.03, "metal", seg=8, lados=4)
        ini = base + Vector((lado * 0.42, 0.55, 0.3))
        medio = (ini + anilla) / 2 + Vector((lado * 0.15, 0, 0.1))
        curva = C.remuestrear(C.catmull_rom([tuple(ini), tuple(medio), tuple(anilla)], 8, cerrada=False), 0.2)
        for i in range(len(curva) - 1):
            a_, b_ = Vector(curva[i]), Vector(curva[i + 1])
            dd = (b_ - a_).normalized()
            ref = Vector((0, 0, 1)) if i % 2 else dd.cross(Vector((0, 0, 1)))
            D.toro(gc, (a_ + b_) / 2, dd.cross(ref).normalized(), 0.075, 0.022, "metal", seg=6, lados=3)
    # Cinchas de cuero reforzado con placas de hueso, hebillas de calavera y remiendos.
    for y in CINCHAS:
        pieza = "Torso" if y > F.UNION_ABDOMEN[1] else "Abdomen"
        gg = geos[pieza]
        ps, ns = [], []
        for t_ in np.linspace(0, math.tau, 52, endpoint=False):
            d = Vector((math.cos(t_), 0, math.sin(t_)))
            q, m = D.proyectar_hacia(bvh[pieza], Vector((0, y, 2.6)) + d * 6.0, -d, 8.0)
            if q is not None:
                ps.append(q)
                ns.append(m)
        D.cinta(gg, ps, ns, 0.34, 0.07, "cuero", cerrada=True, lateral=[Vector((0, 1, 0))] * len(ps), separacion=0.012,
                aux_flag=1.0)
        for i in range(0, len(ps), 6):
            if ns[i].z < 0.3:  # placas de hueso en la parte visible (costados y vientre)
                D.caja(gg, ps[i] + ns[i] * 0.1, D.marco(ns[i], Vector((0, 1, 0)))[:2] + (ns[i],), (0.26, 0.3, 0.05),
                       "hueso")
        for lado in (1, -1):
            q, m = D.proyectar_hacia(bvh[pieza], (lado * 6.0, y, 2.3), (-lado, 0, 0), 8.0)
            calavera(gg, q + m * 0.17, m, 0.28)
    # Plataforma del artillero sobre el abdomen (elevada 0,5) con barandilla de hueso en 3 lados.
    ga = geos["Abdomen"]
    p, n = D.proyectar(bvh["Abdomen"], 0.0, -7.7)
    suelo = p + Vector((0, 0, 0.5))
    D.caja(ga, suelo, (Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))), (2.0, 1.5, 0.14), "madera")
    for dx in (-0.8, 0.8):
        for dy in (-0.55, 0.55):
            q, m = D.proyectar(bvh["Abdomen"], dx, -7.7 + dy)
            ga.tubo([q - m * 0.04, Vector((suelo.x + dx, suelo.y + dy, suelo.z - 0.05))], [0.06, 0.05], "hueso", lados=5)
    postes = [(-0.95, 0.65), (-0.95, -0.7), (0.95, -0.7), (0.95, 0.65)]
    tops = []
    for (dx, dy) in postes:
        b = suelo + Vector((dx, dy, 0.07))
        ga.tubo([b, b + Vector((0, 0, 0.6))], [0.045, 0.04], "hueso", lados=5)
        tops.append(b + Vector((0, 0, 0.6)))
    ga.tubo(tops, [0.035] * 4, "hueso", lados=5)
    artillero = suelo + Vector((0, 0, 0.07 + 0.15))
    # Bandera enemiga desgarrada en un palo de hueso.
    mastil = suelo + Vector((-0.95, -0.7, 0.07))
    ga.tubo([mastil, mastil + Vector((0, 0, 1.9))], [0.04, 0.03], "hueso", lados=5)
    rej = []
    for i, v in enumerate(np.linspace(0, 1, 5)):
        fila = []
        for j, u in enumerate(np.linspace(0, 1, 7)):
            onda = 0.1 * math.sin(u * 5 + v)
            desgarro = -0.25 * (u > 0.6) * (i % 2) * (u - 0.6)
            fila.append(mastil + Vector((-0.03 + onda, -0.05 - 1.0 * u - desgarro, 1.85 - 0.7 * v)))
        rej.append(fila)
    D.lamina(ga, rej, 0.03, 0.03, "bandera", Vector((1, 0, 0)), aux_fn=lambda i, j: (0, 0, 0))
    # Alforjas bajo los élitros, manchadas de alquitrán.
    for lado in (1, -1):
        q, m = D.proyectar_hacia(cuerpo, (lado * 6.0, -3.1, 1.9), (-lado, 0, 0), 8.0)
        pieza = "Abdomen" if -3.1 < F.UNION_ABDOMEN[1] else "Torso"
        geos[pieza].caja_redonda(q + m * 0.22, (0.4, 0.75, 0.6), "cuero", seg=2, aux=(0.0, 0.5, 1.0), redondeo=0.7)
        geos[pieza].elipsoide(q + m * 0.42 + Vector((0, 0.1, -0.1)), (0.05, 0.25, 0.18), "alquitran", seg=8, anillos=4)
    # Dos cascos abollados colgando de la cincha central.
    for lado in (1, -1):
        q, m = D.proyectar_hacia(bvh["Torso"], (lado * 6.0, -0.3, 1.7), (-lado, 0, 0), 8.0)
        c = q + m * 0.36 + Vector((0, 0, -0.15))
        filas = [[c + Vector((0.3 * math.sin(th) * math.cos(a) * (0.85 if (k + j) % 5 == 0 else 1.0),
                              0.3 * math.sin(th) * math.sin(a), 0.3 * math.cos(th))) for k, a in
                  enumerate(np.linspace(0, math.tau, 10, endpoint=False))] for j, th in enumerate((0.5, 1.0, 1.45))]
        geos["Torso"].loft(filas, "metal", punta_inicio=(c + Vector((0, 0, 0.3)), (0, 0, 0)), tapar_fin=True)
        D.caja(geos["Torso"], c + Vector((0.28 * lado, 0, -0.12)), (Vector((1, 0, 0)), Vector((0, 1, 0)),
                                                                    Vector((0, 0, 1))), (0.05, 0.08, 0.3), "metal")
        geos["Torso"].tubo([q + m * 0.05, c + Vector((0, 0, 0.32))], [0.02, 0.02], "cuero", lados=3)

    # Élitros (piezas de geometría).
    geometricas, piv = {}, {}
    for lado, nom in ((-1, "Izq"), (1, "Der")):
        ge = T.Geo(f"Elitro_{nom}")
        piv[f"Elitro_{nom}"] = elitro(ge, cuerpo, lado, rnd)
        geometricas[f"Elitro_{nom}"] = ge.objeto(mats)

    det = {n: [g.objeto(mats)] for n, g in geos.items() if len(g.bm.faces)}
    p, n = D.proyectar(cuerpo, 0.0, -5.0)
    datos = {"piloto": piloto, "artillero": artillero, "carga": p + Vector((0, 0, 0.115 + 0.25 + 0.2))}
    for lado, nom in ((-1, "Izq"), (1, "Der")):
        q, m = D.proyectar_hacia(bvh["Torso"], (lado * 6.0, 0.4, 2.0), (-lado, 0, 0), 8.0)
        datos[nom] = q + m * 0.4
    return altas, det, geometricas, piv, datos


def calavera(g, c, adelante, s):
    t1, t2, a = D.marco(adelante, Vector((0, 0, 1)))
    g.elipsoide(c, (0.5 * s, 0.5 * s, 0.45 * s), "hueso", seg=8, anillos=5, rot=D.matriz((t1, t2, a)))
    for lado in (1, -1):
        D.disco(g, c + a * 0.38 * s + t1 * 0.2 * s * lado + t2 * 0.08 * s, a, 0.11 * s, "alquitran", seg=6, anillos=1,
                abombado=-0.03 * s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="1")
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    altas, det, geometricas, piv, datos = construir(args)
    pivotes = {n: F.pivote(n) for n in F.PIEZAS}
    pivotes["Torso"] = (0.0,) + tuple(altas["Torso"]["centro_masa"])[1:]
    pivotes.update({k: tuple(v) for k, v in piv.items()})
    padre = {"Torso": None, "Cabeza": "Torso", "Mandibula_Izq": "Cabeza", "Mandibula_Der": "Cabeza",
             "Cuerno_Central": "Cabeza", "Elitro_Izq": "Torso", "Elitro_Der": "Torso", "Abdomen": "Torso"}
    for tipo in ("Del", "Med", "Tras"):
        for l in ("Izq", "Der"):
            padre[f"Pata_{tipo}_{l}"] = "Torso"
    montajes = {"Montura_Piloto": (datos["piloto"], "Torso"), "Montura_Artillero": (datos["artillero"], "Abdomen"),
                "Montura_Lateral_Izq": (datos["Izq"], "Torso"), "Montura_Lateral_Der": (datos["Der"], "Torso"),
                "Punto_Carga": (datos["carga"], "Abdomen")}
    orden = ["Torso", "Cabeza", "Mandibula_Izq", "Mandibula_Der", "Cuerno_Central", "Elitro_Izq", "Elitro_Der"] + \
            [f"Pata_{t}_{l}" for t in ("Del", "Med", "Tras") for l in ("Izq", "Der")] + ["Abdomen"]
    peso = {"Torso": 2.2, "Cabeza": 1.4, "Mandibula_Izq": 0.35, "Mandibula_Der": 0.35, "Cuerno_Central": 0.6,
            "Abdomen": 1.6}
    for t in ("Del", "Med", "Tras"):
        for l in ("Izq", "Der"):
            peso[f"Pata_{t}_{l}"] = 0.55
    cfg = dict(
        nombre=NOMBRE, titulo="ESCARABAJO ABISAL", rol="Tanque pesado / asedio", jinetes="2-3",
        neon=["#FF8C00", "#39FF14"], presupuesto=PRESUPUESTO, salida=args.salida, ronda=args.ronda,
        rapido=args.rapido, altas=altas, detalles=det, geometricas=geometricas, peso_tris=peso, pivotes=pivotes,
        padre=padre, orden=orden, montajes=montajes,
        prioridad_uv={"Cabeza": 1.4, "Cuerno_Central": 1.3, "Elitro_Izq": 1.15, "Elitro_Der": 1.15},
        radio_estudio=10.0, exposicion=1.0, emision_render=3.0,
        cerca=[("Cabeza y cuerno", 40, 15, (0, 7.0, 4.0), 2.6), ("Mandíbulas y ariete", 15, 5, (0, 8.0, 2.6), 1.8),
               ("Élitro izq. (geoda)", 70, 45, (-2.0, -2.6, 4.0), 1.8), ("Silla y cadenas", 25, 40, (0, 3.8, 4.6), 2.2),
               ("Pata trasera", -70, 5, (4.0, -3.4, 1.6), 1.9), ("Artillero y bandera", 150, 25, (0, -7.6, 4.6), 2.2)],
        notas_json=["Los élitros pivotan en su bisagra delantera (detrás del pronoto): se abren hacia arriba y atrás "
                    "para ventilar.",
                    "Metal (cadenas, ariete, cascos) con metalness alto; la quitina lleva un brillo sutil (0,2)."],
    )
    bestia.terminar(cfg)


if __name__ == "__main__":
    main()
