"""
Monstruo base R6 ("El Hueco"): criatura original de estilo creepypasta para el bando de los Monstruos.

Idea del diseño (original, sin copiar personajes conocidos):
  * Cuerpo consumido y encorvado, con las costillas marcadas y una cresta de vértebras que sale de la espalda.
  * Brazos demasiado largos (le llegan a las rodillas), con un codo hinchado y dedos larguísimos con garras.
    Son asimétricos: el derecho es más largo y tiene cuatro dedos; el izquierdo, tres y un bulto deforme.
  * Piernas largas y flacas con la rodilla hacia delante y el tobillo hacia atrás, y pies de dedos largos.
  * Cabeza alargada, sin nariz, partida por una boca VERTICAL llena de dientes, con tres ojos hundidos y
    desiguales que brillan en rojo.
  * Piel cenicienta con moratones, más oscura en manos y pies.

R6: cada pieza es una malla aparte con el nombre exacto de la pieza de Roblox (Head, Torso, "Left Arm",
"Right Arm", "Left Leg", "Right Leg"). Los ojos son otra malla (Ojos) para ponerles material Neon y soldarlos a
Head. Las articulaciones (cuello, hombros, caderas) se guardan en articulaciones.json y el script de Studio
`montar_r6.luau` crea con ellas los Motor6D. También se exporta un FBX con esqueleto R6 (cada malla atada al
100 % a su hueso) para animarlo en Blender.

Cada pieza se modela en ALTA (skin + subdivisión + detalle) y se simplifica a BAJA, con color y normales horneados.

Medidas en studs. Mira a -Y en Blender (a -Z en Roblox). Su izquierda es +X en Blender.

Uso:
    python modelos/herramientas/monstruo.py --salida modelos/monstruo [--ronda N] [--rapido]
"""

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

import comun as c  # noqa: E402

E = c.ESTUDIO

# --------------------------------------------------------------------------------------------------------------
# Datos ajustables
# --------------------------------------------------------------------------------------------------------------

PIEL = {
    "base": "#B9B5AD",  # ceniza
    "palida": "#DDD9CE",  # cara y relieves
    "moraton": "#5E4F5A",
    "extremo": "#2E2629",  # manos y pies
    "garra": "#17120F",
    "boca": "#2A0709",
    "encia": "#6B1A1E",
    "diente": "#D6CBA6",
    "hueso": "#D9D2BE",
}
COLOR_OJOS = "#FF2B2B"

# Articulaciones en studs (Blender: z arriba, la cara mira a -Y, la izquierda del monstruo en +X).
ALTO_CADERA = 2.75  # en un R6 normal es 2: las piernas son más largas
ARTICULACIONES = {
    "RootJoint": (0.0, 0.0, ALTO_CADERA + 1.0),
    "Neck": (0.0, -0.75, ALTO_CADERA + 1.8),  # adelantado: la cabeza cuelga por delante de la joroba
    "Left Shoulder": (1.15, 0.0, ALTO_CADERA + 1.55),
    "Right Shoulder": (-1.15, 0.0, ALTO_CADERA + 1.55),
    "Left Hip": (0.5, 0.0, ALTO_CADERA),
    "Right Hip": (-0.5, 0.0, ALTO_CADERA),
}

# Esqueletos para el modificador Skin: lista de (nombre, posición, radio (x, y)) y aristas por nombre.
# Brazo derecho (el izquierdo se refleja y luego se deforma distinto).
H = ALTO_CADERA

# Presupuesto de triángulos de cada pieza en el juego.
TRIS = {"Head": 1400, "Torso": 1500, "Right Arm": 1100, "Left Arm": 1000, "Right Leg": 800, "Left Leg": 800}
TAM_TEXTURA = 1024
ENGORDE = 1.3  # la subdivisión encoge la malla del Skin; así las medidas de los esqueletos son las reales


def esqueleto_torso():
    n = [
        ("pelvis", (0, 0.0, H - 0.05), (0.62, 0.40)),
        ("vientre", (0, 0.06, H + 0.3), (0.52, 0.34)),
        ("cintura", (0, 0.12, H + 0.65), (0.46, 0.31)),
        ("pecho", (0, 0.02, H + 1.15), (0.74, 0.48)),
        ("joroba", (0, 0.22, H + 1.65), (0.82, 0.56)),
        ("cuello", (0, -0.7, H + 1.85), (0.22, 0.2)),
        ("hombro_i", (1.08, 0.1, H + 1.62), (0.32, 0.32)),
        ("hombro_d", (-1.08, 0.1, H + 1.62), (0.32, 0.32)),
        # Huesos que asoman por encima de los hombros (omóplatos y clavículas marcados).
        ("omo_i", (0.8, 0.45, H + 2.0), (0.06, 0.06)),
        ("omo_d", (-0.8, 0.45, H + 2.0), (0.06, 0.06)),
    ]
    a = [("hombro_i", "omo_i"), ("hombro_d", "omo_d"), ("pelvis", "vientre"), ("vientre", "cintura"), ("cintura", "pecho"), ("pecho", "joroba"), ("joroba", "cuello"),
         ("joroba", "hombro_i"), ("joroba", "hombro_d")]
    # Vértebras: pinchos que salen de la espalda (+Y) a lo largo de la columna.
    for i in range(6):
        t = i / 5
        z = H + 0.45 + t * 1.45
        y = 0.3 + 0.35 * math.sin(t * math.pi * 0.9) + 0.12
        n.append((f"vb{i}", (0, y, z), (0.10, 0.10)))
        n.append((f"vp{i}", (0, y + 0.22 + 0.06 * math.sin(t * 3), z + 0.08), (0.03, 0.03)))
        a.append((f"vb{i}", f"vp{i}"))
        a.append((f"vb{i}", "cintura" if t < 0.4 else "pecho" if t < 0.8 else "joroba"))
    return n, a


# Torso y cabeza con METABOLAS: elipsoides y cápsulas que se funden entre sí. El Skin da secciones cuadradas y
# pliegues en las ramas; las metabolas dan volúmenes orgánicos (costillar, vientre hundido, joroba, cráneo).
# Cada elemento: (tipo, centro, semiejes (x, y, z) o (radio, semilargo), giro en grados (x, y, z), rigidez).


def metabolas_torso():
    el = [
        ("ELLIPSOID", (0, 0.05, H + 1.2), (0.82, 0.52, 0.62), (0, 0, 0), 2.0),  # costillar
        ("ELLIPSOID", (0, 0.0, H + 0.08), (0.6, 0.38, 0.32), (0, 0, 0), 2.0),  # pelvis
        ("ELLIPSOID", (0, 0.12, H + 0.55), (0.4, 0.27, 0.42), (0, 0, 0), 1.6),  # vientre chupado
        ("ELLIPSOID", (0, 0.32, H + 1.62), (0.7, 0.42, 0.42), (-25, 0, 0), 2.0),  # joroba
        ("BALL", (1.06, 0.12, H + 1.62), (0.3,), (0, 0, 0), 2.0),  # hombros
        ("BALL", (-1.06, 0.12, H + 1.62), (0.3,), (0, 0, 0), 2.0),
        ("CAPSULE", (0.55, -0.25, H + 1.82), (0.09, 0.45), (0, -14, 18), 2.0),  # clavículas
        ("CAPSULE", (-0.55, -0.25, H + 1.82), (0.09, 0.45), (0, 14, -18), 2.0),
        ("CAPSULE", (0, -0.45, H + 1.82), (0.2, 0.3), (0, 90, 60), 2.0),  # cuello hacia delante
        ("ELLIPSOID", (0.5, 0.5, H + 1.55), (0.3, 0.1, 0.36), (0, 0, -20), 2.0),  # omóplatos
        ("ELLIPSOID", (-0.5, 0.5, H + 1.55), (0.3, 0.1, 0.36), (0, 0, 20), 2.0),
    ]
    for i in range(8):  # vértebras: bultos a lo largo de la columna, que sigue la joroba
        t = i / 7
        z = H + 0.35 + t * 1.5
        y = 0.38 + 0.42 * math.sin(t * math.pi * 0.85)
        el.append(("BALL", (0, y, z), (0.1 - 0.02 * abs(t - 0.6),), (0, 0, 0), 2.5))
    return el


def metabolas_cabeza():
    nz = ARTICULACIONES["Neck"][2]
    return [
        ("CAPSULE", (0, -0.66, nz + 0.12), (0.15, 0.16), (0, 90, 60), 2.0),  # cuello (corto: sigue en el torso)
        ("ELLIPSOID", (0, -0.62, nz + 1.35), (0.36, 0.4, 0.62), (-12, 0, 0), 2.0),  # cráneo alargado
        ("ELLIPSOID", (0, -0.8, nz + 0.75), (0.3, 0.27, 0.48), (8, 0, 0), 2.0),  # cara
        ("ELLIPSOID", (0, -0.86, nz + 0.28), (0.18, 0.2, 0.2), (0, 0, 0), 2.0),  # barbilla
        ("BALL", (0.27, -0.9, nz + 0.78), (0.11,), (0, 0, 0), 2.0),  # pómulos
        ("BALL", (-0.27, -0.9, nz + 0.74), (0.11,), (0, 0, 0), 2.0),
        ("CAPSULE", (0, -0.95, nz + 1.18), (0.07, 0.24), (0, 0, 0), 2.0),  # arco de las cejas
    ]


# Una metabola sola, con umbral 0,6 y rigidez 2, mide 0,575 veces su radio: se compensa para que los tamaños
# escritos arriba sean los reales (un poco menos, porque al fundirse las piezas ganan volumen).
K_METABOLA = 1.6


def malla_metabolas(nombre, elementos, resolucion=0.035):
    mb = bpy.data.metaballs.new(nombre)
    mb.resolution = resolucion * E
    mb.threshold = 0.6
    from mathutils import Euler
    for tipo, co, tam, giro, rigidez in elementos:
        e = mb.elements.new(type=tipo)
        e.co = Vector(co) * E
        e.stiffness = rigidez
        e.rotation = Euler([math.radians(g) for g in giro]).to_quaternion()
        if tipo == "BALL":
            e.radius = tam[0] * E * K_METABOLA
        elif tipo == "CAPSULE":
            e.radius = tam[0] * E * K_METABOLA
            e.size_x = tam[1] * E
        else:
            e.radius = E * K_METABOLA
            e.size_x, e.size_y, e.size_z = tam
    obj_mb = bpy.data.objects.new(nombre + "_mb", mb)
    bpy.context.scene.collection.objects.link(obj_mb)
    dep = bpy.context.evaluated_depsgraph_get()
    malla = bpy.data.meshes.new_from_object(obj_mb.evaluated_get(dep))
    bpy.data.objects.remove(obj_mb)
    obj = bpy.data.objects.new(nombre, malla)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def esqueleto_brazo(derecho=True):
    s = -1 if derecho else 1
    largo = 1.0 if derecho else 0.9  # el derecho es más largo
    hz = H + 1.55
    def p(x, y, z):
        # Cuanto más abajo, más adelantado: los brazos cuelgan hacia delante, como si fuera a agarrar algo.
        caida = (hz - z) * largo
        return (s * x, y - 0.22 * caida / 3.3, hz - caida)
    n = [
        ("hombro", p(1.2, 0.05, hz + 0.08), (0.30, 0.30)),
        ("biceps", p(1.3, 0.04, hz - 0.45), (0.15, 0.15)),
        ("brazo", p(1.36, 0.08, hz - 1.05), (0.10, 0.10)),
        ("codo", p(1.42, 0.24, hz - 1.6), (0.24, 0.22)),
        ("punta_codo", p(1.44, 0.42, hz - 1.62), (0.07, 0.07)),
        ("antebrazo", p(1.47, 0.02, hz - 2.15), (0.12, 0.11)),
        ("antebrazo2", p(1.5, -0.06, hz - 2.7), (0.075, 0.075)),
        ("muneca", p(1.52, -0.1, hz - 2.98), (0.11, 0.10)),
        ("palma", p(1.55, -0.16, hz - 3.25), (0.18, 0.10)),
    ]
    a = [("hombro", "biceps"), ("biceps", "brazo"), ("brazo", "codo"), ("codo", "punta_codo"),
         ("codo", "antebrazo"), ("antebrazo", "antebrazo2"), ("antebrazo2", "muneca"), ("muneca", "palma")]
    dedos = 4 if derecho else 3
    for d in range(dedos):
        t = (d / (dedos - 1)) - 0.5  # -0.5 .. 0.5 (de delante a atrás)
        base = Vector(p(1.55, -0.14, hz - 3.32)) + Vector((s * 0.05 * (1 - abs(t) * 2), t * 0.32, 0))
        largo_dedo = 1.05 - abs(t) * 0.35
        prev = "palma"
        for k in range(1, 4):
            f = k / 3
            # Los dedos bajan y se curvan hacia delante (hacia -Y) al final, como garras.
            pos = base + Vector((s * 0.06 * f, t * 0.18 * f - 0.28 * f ** 2.2, -largo_dedo * f))
            r = (0.075 if k > 1 else 0.085) * (1 - 0.4 * f)  # nudillos gruesos
            nombre = f"d{d}_{k}"
            n.append((nombre, tuple(pos), (r, r)))
            a.append((prev, nombre))
            prev = nombre
        punta = base + Vector((s * 0.07, t * 0.18 - 0.42, -largo_dedo - 0.18))
        n.append((f"g{d}", tuple(punta), (0.012, 0.012)))
        a.append((prev, f"g{d}"))
    if not derecho:
        # Bulto deforme en el antebrazo izquierdo.
        n.append(("bulto", p(1.62, 0.25, hz - 2.0), (0.2, 0.2)))
        a.append(("antebrazo", "bulto"))
    return n, a


def esqueleto_pierna(derecha=True):
    s = -1 if derecha else 1
    n = [
        ("cadera", (s * 0.5, 0.0, H + 0.15), (0.36, 0.36)),
        ("muslo", (s * 0.5, -0.08, H - 0.6), (0.17, 0.17)),
        ("rodilla", (s * 0.52, -0.3, H - 1.2), (0.2, 0.19)),
        ("espinilla", (s * 0.52, -0.05, H - 1.85), (0.10, 0.10)),
        ("tobillo", (s * 0.52, 0.22, H - 2.45), (0.11, 0.11)),
        ("talon", (s * 0.52, 0.24, 0.12), (0.12, 0.10)),
        ("planta", (s * 0.52, -0.15, 0.12), (0.17, 0.09)),
    ]
    a = [("cadera", "muslo"), ("muslo", "rodilla"), ("rodilla", "espinilla"), ("espinilla", "tobillo"),
         ("tobillo", "talon"), ("talon", "planta")]
    for d, dx in enumerate((-0.14, 0.0, 0.14)):
        largo = 0.65 if d == 1 else 0.5
        prev = "planta"
        for k in range(1, 3):
            f = k / 2
            pos = (s * (0.52 + dx * (1 + 0.6 * f)), -0.15 - largo * f, 0.1 - 0.02 * f)
            nombre = f"t{d}_{k}"
            n.append((nombre, pos, (0.055 * (1 - 0.3 * f),) * 2))
            a.append((prev, nombre))
            prev = nombre
        n.append((f"u{d}", (s * (0.52 + dx * 1.7), -0.15 - largo - 0.17, 0.03), (0.01, 0.01)))
        a.append((prev, f"u{d}"))
    return n, a


def esqueleto_cabeza():
    nz = ARTICULACIONES["Neck"][2]
    n = [
        ("nuca", (0, -0.45, nz - 0.2), (0.24, 0.22)),
        ("menton", (0, -0.78, nz + 0.3), (0.30, 0.28)),
        ("pomulo_i", (0.3, -0.85, nz + 0.75), (0.1, 0.1)),
        ("pomulo_d", (-0.3, -0.85, nz + 0.72), (0.1, 0.1)),
        ("cara", (0, -0.72, nz + 0.8), (0.36, 0.34)),
        ("craneo", (0, -0.52, nz + 1.3), (0.40, 0.40)),
        ("cima", (0, -0.2, nz + 1.95), (0.22, 0.22)),
    ]
    a = [("nuca", "menton"), ("menton", "cara"), ("cara", "craneo"), ("craneo", "cima"), ("cara", "pomulo_i"),
         ("cara", "pomulo_d")]
    return n, a


# --------------------------------------------------------------------------------------------------------------
# Malla con Skin
# --------------------------------------------------------------------------------------------------------------


def malla_skin(nombre, esqueleto, subdiv=2, engorde=None):
    nodos, aristas = esqueleto
    idx = {nm: i for i, (nm, _, _) in enumerate(nodos)}
    malla = bpy.data.meshes.new(nombre)
    malla.from_pydata([Vector(p) * E for _, p, _ in nodos], [(idx[x], idx[y]) for x, y in aristas], [])
    obj = bpy.data.objects.new(nombre, malla)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("skin", "SKIN")
    mod.use_smooth_shade = True
    mod.branch_smoothing = 0.6
    for i, (_, _, r) in enumerate(nodos):
        sv = malla.skin_vertices[0].data[i]
        k = engorde or ENGORDE
        sv.radius = (r[0] * E * k, r[1] * E * k)
        sv.use_root = i == 0
    sub = obj.modifiers.new("sub", "SUBSURF")
    sub.levels = sub.render_levels = subdiv
    c.aplicar_modificadores(obj)
    return obj


def _a_bmesh(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    return bm


def _remallar(obj, voxel):
    mod = obj.modifiers.new("remallado", "REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = voxel * E
    mod.use_smooth_shade = True
    c.aplicar_modificadores(obj)


def suavizar(obj, factor=0.5, repes=4):
    mod = obj.modifiers.new("suave", "SMOOTH")
    mod.factor = factor
    mod.iterations = repes
    c.aplicar_modificadores(obj)


# --------------------------------------------------------------------------------------------------------------
# Detalle, color y cara
# --------------------------------------------------------------------------------------------------------------


def detalle_piel(obj, rnd, fuerza=0.025, costillas=False, extremos=None):
    """Arrugas, venas y (en el torso) costillas. Guarda en `obj` un color por vértice."""
    sem = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), rnd.uniform(0, 50)))
    bm = _a_bmesh(obj)
    for v in bm.verts:
        p = v.co / E
        arruga = noise.ridged_multi_fractal(p * 2.2 + sem, 0.9, 2.1, 3, 0.0, 2.0) * 0.5
        vena = noise.voronoi(p * 1.6 + sem, distance_metric="DISTANCE")[0]
        vena = max(0.0, 0.06 - (vena[1] - vena[0])) / 0.06
        des = fuerza * (arruga - 0.4) + 0.018 * vena
        if costillas:
            # Costillas: bandas horizontales en el pecho y los costados (no en la espalda).
            # Bajan en diagonal desde la espalda hacia el esternón y se cortan antes del centro del pecho.
            zr = p.z - (H + 0.65) - 0.3 * max(0.0, 0.6 - p.y)
            lateral = max(0.0, min(1.0, (abs(p.x) - 0.3) / 0.25))  # solo en los costados, no en el pecho
            if 0 < zr < 1.0 and v.normal.y < 0.5:
                banda = max(0.0, math.sin(zr * math.pi * 5.0)) ** 4
                des += 0.035 * banda * lateral
                des -= 0.02 * (1 - banda) * lateral
            # Esternón hundido y vientre chupado.
            if v.normal.y < -0.5 and H + 0.35 < p.z < H + 0.85:
                des -= 0.06
        v.co += v.normal * des * E
    bm.to_mesh(obj.data)
    bm.free()


def tallar_cara(obj):
    """Boca vertical (surco profundo) y tres cuencas de ojos en la cabeza ALTA."""
    nz = ARTICULACIONES["Neck"][2]
    bm = _a_bmesh(obj)
    ojos = posiciones_ojos()
    for v in bm.verts:
        p = v.co / E
        if v.normal.y < -0.1:
            # Surco de la boca: estrecho en X, desde la barbilla hasta la frente; más ancho en el centro.
            t = (p.z - (nz + 0.18)) / 1.15
            if 0 < t < 1:
                ancho = ancho_boca(t)
                dx = abs(p.x) / ancho
                if dx < 1.6:
                    prof = (1 - min(1, dx) ** 2) * (0.30 * math.sin(t * math.pi) ** 0.5)
                    labio = 0.05 * math.exp(-((dx - 1.15) ** 2) / 0.05)
                    v.co += v.normal * (-prof + labio) * E
            for (ox, oy, oz), r in ojos:
                d = math.hypot(p.x - ox, p.z - oz) / (r * 1.6)
                if d < 1:
                    v.co += v.normal * (-(1 - d * d) * r * 1.1) * E
    bm.to_mesh(obj.data)
    bm.free()


# Copia de la cabeza ALTA antes de tallarla: sirve para saber dónde está la superficie de la cara.
_REFERENCIA = {}


def superficie_y(x, z):
    """Y (studs) de la superficie de la cara en (x, z), lanzando un rayo desde delante hacia +Y."""
    ref = _REFERENCIA.get("cabeza")
    if ref is None:
        return -0.9
    ok, punto, _, _ = ref.ray_cast(Vector((x, -6.0, z)) * E, Vector((0, 1, 0)))
    return punto.y / E if ok else -0.9


def ancho_boca(t):
    """Medio ancho (studs) de la boca vertical a la altura relativa t (0 = barbilla, 1 = frente)."""
    return 0.035 + 0.085 * math.sin(t * math.pi) ** 0.8


def posiciones_ojos():
    """(centro en la superficie, radio) de los tres ojos, en studs: dos a los lados de la boca, desiguales, y uno
    en la frente."""
    nz = ARTICULACIONES["Neck"][2]
    ojos = [
        ((0.2, nz + 1.02), 0.075),  # izquierdo del monstruo, más alto
        ((-0.19, nz + 0.84), 0.095),  # derecho, más bajo y más grande
        ((0.1, nz + 1.42), 0.045),  # tercer ojo, pequeño y torcido
    ]
    return [((x, superficie_y(x, z), z), r) for (x, z), r in ojos]


def pintar(obj, region, rnd):
    """Color por vértice de la malla ALTA según la zona. `region`: head, torso, arm, leg."""
    sem = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), rnd.uniform(0, 50)))
    col = {k: Vector(c.srgb(v)) for k, v in PIEL.items()}
    nz = ARTICULACIONES["Neck"][2]
    bm = _a_bmesh(obj)
    capa = bm.loops.layers.color.new("Col")
    colores = []
    for v in bm.verts:
        p = v.co / E
        mancha = 0.5 + 0.5 * noise.fractal(p * 1.3 + sem, 0.8, 2.0, 4)
        k = col["base"].lerp(col["palida"], max(0.0, min(1.0, 0.5 + v.normal.z * 0.3 + (mancha - 0.5))))
        moraton = max(0.0, noise.noise(p * 0.9 + sem * 2) - 0.15) * 1.6
        k = k.lerp(col["moraton"], min(0.7, moraton))
        if region in ("arm", "leg"):
            # Más oscuro hacia las manos y los pies; las garras, negras.
            altura = p.z / (H + 1.5) if region == "arm" else p.z / H
            oscuro = max(0.0, min(1.0, (0.42 - altura) / 0.3)) if region == "arm" else \
                max(0.0, min(1.0, (0.25 - altura) / 0.2))
            k = k.lerp(col["extremo"], oscuro * 0.85)
        if region == "torso":
            # Costillas y vértebras más pálidas (hueso bajo la piel).
            if p.y > 0.35:
                k = k.lerp(col["hueso"], min(1.0, (p.y - 0.35) / 0.25))
        if region == "head":
            t = (p.z - (nz + 0.18)) / 1.15
            if v.normal.y < 0 and 0 < t < 1:
                ancho = ancho_boca(t)
                dx = abs(p.x) / ancho
                if dx < 1.0:
                    k = col["boca"]
                elif dx < 1.9:
                    k = k.lerp(col["encia"], (1.9 - dx) / 0.9 * 0.9)
            for (ox, oy, oz), r in posiciones_ojos():
                d = math.hypot(p.x - ox, p.z - oz) / (r * 2.6)
                if d < 1 and v.normal.y < 0:
                    k = k.lerp(col["boca"], (1 - d) ** 1.5)
        colores.append(k)
    for f in bm.faces:
        for l in f.loops:
            q = colores[l.vert.index]
            l[capa] = (q.x, q.y, q.z, 1.0)
    bm.to_mesh(obj.data)
    bm.free()
    mat = bpy.data.materials.new(f"{obj.name}_vc")
    mat.use_nodes = True
    nt = mat.node_tree
    at = nt.nodes.new("ShaderNodeVertexColor")
    at.layer_name = "Col"
    nt.links.new(at.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.62
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def dientes(rnd):
    """Dientes finos a los dos lados de la boca vertical (bmesh en studs)."""
    nz = ARTICULACIONES["Neck"][2]
    bm = bmesh.new()
    n = 9
    for lado in (-1, 1):
        for i in range(n):
            t = 0.12 + 0.76 * i / (n - 1)
            z = nz + 0.18 + t * 1.15
            ancho = ancho_boca(t)
            ys = superficie_y(lado * ancho * 1.05, z)
            raiz = Vector((lado * ancho * 0.95, ys + 0.07, z))
            punta = Vector((-lado * ancho * 0.55, ys + 0.02, z + rnd.uniform(-0.04, 0.04)))
            largo = (punta - raiz).length * rnd.uniform(0.7, 0.95)
            eje = (punta - raiz).normalized()
            q = eje.to_track_quat("Z", "Y")
            r = 0.028 + 0.012 * math.sin(t * math.pi)
            vs = [bm.verts.new(raiz + q @ Vector((math.cos(a) * r, math.sin(a) * r, 0)))
                  for a in (0, 2.1, 4.2)]
            cima = bm.verts.new(raiz + eje * largo)
            for j in range(3):
                bm.faces.new((vs[j], vs[(j + 1) % 3], cima))
            bm.faces.new(list(reversed(vs)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def ojos():
    bm = bmesh.new()
    for (x, y, z), r in posiciones_ojos():
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r * 0.75)
        bmesh.ops.translate(bm, vec=(x, y + r * 0.9, z), verts=res["verts"])  # dentro de la cuenca
    col = c.srgb(COLOR_OJOS)
    m = c.material("Ojos", col, rugosidad=0.2, emision=col, fuerza_emision=6)
    return c.objeto_desde_bmesh("Ojos", bm, [m])


# --------------------------------------------------------------------------------------------------------------
# Construcción
# --------------------------------------------------------------------------------------------------------------


def baja_de(alta, nombre, tris):
    baja = alta.copy()
    baja.data = alta.data.copy()
    baja.name = nombre
    baja.data.name = nombre
    bpy.context.scene.collection.objects.link(baja)
    mod = baja.modifiers.new("simplificar", "DECIMATE")
    mod.ratio = min(1.0, tris / max(1, c.triangulos(baja)))
    mod.use_collapse_triangulate = True
    c.aplicar_modificadores(baja)
    baja.data.materials.clear()
    baja.data.materials.append(c.material(f"{nombre}_tmp", (0.5, 0.5, 0.5)))
    c.sombreado_suave(baja, angulo=70)
    return baja


def construir(rapido, carpeta):
    rnd = random.Random(7)
    piezas = {}
    altas = {}
    voxel = 0.05 if rapido else 0.028
    definicion = {
        "Torso": (metabolas_torso(), "torso"),
        "Head": (metabolas_cabeza(), "head"),
        "Right Arm": (esqueleto_brazo(True), "arm"),
        "Left Arm": (esqueleto_brazo(False), "arm"),
        "Right Leg": (esqueleto_pierna(True), "leg"),
        "Left Leg": (esqueleto_pierna(False), "leg"),
    }
    for nombre, (esq, region) in definicion.items():
        # Las extremidades, más consumidas que el tronco.
        if region in ("torso", "head"):
            alta = malla_metabolas(f"{nombre}_alta", esq)
        else:
            alta = malla_skin(f"{nombre}_alta", esq, engorde=1.08)
        _remallar(alta, voxel)
        suavizar(alta, 0.4, 2)
        if region == "head":
            ref = alta.copy()
            ref.data = alta.data.copy()
            bpy.context.scene.collection.objects.link(ref)
            ref.hide_render = True
            _REFERENCIA["cabeza"] = ref
            tallar_cara(alta)
            suavizar(alta, 0.35, 2)
        detalle_piel(alta, rnd, fuerza=0.02 if region == "head" else 0.03, costillas=region == "torso")
        pintar(alta, region, rnd)
        baja = baja_de(alta, nombre, TRIS[nombre])
        if region == "head":
            # Los dientes van igual en las dos versiones, para que el horneado los pinte bien.
            for o in (alta, baja):
                bm = bmesh.new()
                bm.from_mesh(o.data)
                tmp = c.objeto_desde_bmesh("tmp_dientes", dientes(random.Random(3)))
                bm.from_mesh(tmp.data)
                bpy.data.objects.remove(tmp)
                bm.to_mesh(o.data)
                bm.free()
            # Color de los dientes en la ALTA.
            capa = alta.data.color_attributes.get("Col")
            dc = c.srgb(PIEL["diente"])
            n0 = len(alta.data.vertices) - 18 * 4
            if capa is not None:
                for poly in alta.data.polygons:
                    if poly.vertices[0] >= n0:
                        for li in poly.loop_indices:
                            capa.data[li].color = (*dc, 1.0)
        c.desplegar_uv(baja, margen=0.012)
        c.hornear(baja, alta, tam=256 if rapido else TAM_TEXTURA,
                  ruta_color=os.path.join(carpeta, "texturas", f"{nombre.replace(' ', '')}_color.png"),
                  ruta_normal=os.path.join(carpeta, "texturas", f"{nombre.replace(' ', '')}_normal.png"),
                  extrusion=0.03, muestras=8 if rapido else 32, distancia_oclusion=0.25)
        alta.hide_render = True
        alta.hide_set(True)
        piezas[nombre] = baja
        altas[nombre] = alta
    piezas["Ojos"] = ojos()
    return piezas


def centrar_origen(obj):
    """Pone el origen de cada pieza en el centro de su caja (así lo hace también Roblox con las MeshPart)."""
    mn, mx = c.caja_limite([obj])
    centro = (mn + mx) / 2
    obj.data.transform(__import__("mathutils").Matrix.Translation(-centro))
    obj.location = centro


def esqueleto_r6(piezas):
    """Armature con los 7 huesos R6 en las articulaciones de este monstruo, y cada pieza atada a su hueso."""
    arm_d = bpy.data.armatures.new("R6")
    arm = bpy.data.objects.new("Monstruo_R6", arm_d)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    j = ARTICULACIONES
    huesos = {
        "HumanoidRootPart": (j["RootJoint"], None),
        "Torso": (j["RootJoint"], "HumanoidRootPart"),
        "Head": (j["Neck"], "Torso"),
        "Left Arm": (j["Left Shoulder"], "Torso"),
        "Right Arm": (j["Right Shoulder"], "Torso"),
        "Left Leg": (j["Left Hip"], "Torso"),
        "Right Leg": (j["Right Hip"], "Torso"),
    }
    for nombre, (pos, padre) in huesos.items():
        b = arm_d.edit_bones.new(nombre)
        b.head = Vector(pos) * E
        b.tail = b.head + Vector((0, 0, 0.35 * E))
        if padre:
            b.parent = arm_d.edit_bones[padre]
    bpy.ops.object.mode_set(mode="OBJECT")
    for nombre, obj in piezas.items():
        hueso = "Head" if nombre == "Ojos" else nombre
        obj.parent = arm
        vg = obj.vertex_groups.new(name=hueso)
        vg.add(list(range(len(obj.data.vertices))), 1.0, "REPLACE")
        mod = obj.modifiers.new("arm", "ARMATURE")
        mod.object = arm
    return arm


def a_roblox(p):
    x, y, z = p
    return [round(-x, 4), round(z, 4), round(y, 4)]


def escribir_montar_r6(ruta, centros):
    """Rellena la plantilla del script de Studio con las articulaciones y los centros de este modelo."""
    def v3(p):
        return f"Vector3.new({p[0]}, {p[1]}, {p[2]})"

    def tabla(d):
        return "\n\t".join(f'["{k}"] = {v3(v)},' for k, v in d.items())

    plantilla = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plantilla_montar_r6.luau"),
                     encoding="utf-8").read()
    texto = (plantilla.replace("--ARTICULACIONES--", tabla({k: a_roblox(v) for k, v in ARTICULACIONES.items()}))
             .replace("--CENTROS--", tabla(centros))
             .replace("--ALTURA--", str(ALTO_CADERA))
             .replace("--COLOR_OJOS--", COLOR_OJOS))
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    os.makedirs(os.path.join(salida, "texturas"), exist_ok=True)

    c.escena_vacia()
    piezas = construir(args.rapido, salida)
    for o in piezas.values():
        centrar_origen(o)
    lista = list(piezas.values())
    tris = {k: c.triangulos(o) for k, o in piezas.items()}
    total = sum(tris.values())
    mn, mx = c.caja_limite(lista)
    alto = (mx.z - mn.z) / E

    # Exportación: piezas sueltas (para montar el R6 en Studio) y versión con esqueleto (para animar en Blender).
    c.exportar_fbx(os.path.join(salida, "Monstruo_R6.fbx"), lista)
    centros = {k: a_roblox(tuple(o.location / E)) for k, o in piezas.items()}
    with open(os.path.join(salida, "articulaciones.json"), "w", encoding="utf-8") as f:
        json.dump({
            "nota": "studs, ejes de Roblox (X derecha del monstruo, Y arriba, -Z delante), origen en el suelo",
            "Articulaciones": {k: a_roblox(v) for k, v in ARTICULACIONES.items()},
            "CentrosPiezas": centros,
            "AlturaCadera": ALTO_CADERA,
        }, f, indent=2, ensure_ascii=False)

    escribir_montar_r6(os.path.join(salida, "montar_r6.luau"), centros)

    c.preparar_estudio(z_suelo=0.0, luz_clave=700)
    vistas = [("Frente", 0, 4), ("3/4", -35, 10), ("Lateral", -90, 2), ("Detrás", 180, 8),
              ("Cara", 0, 6), ("Contrapicado", -25, -14), ("3/4 trasera", 140, 18)]
    tmp = os.path.join(salida, "_render_tmp")
    rutas = c.renderizar_vistas(lista, tmp, [v for v in vistas if v[0] != "Cara"], tam=300 if args.rapido else 460,
                                muestras=16 if args.rapido else 64, margen=0.95, con_malla=True)
    cabeza = c.renderizar_vistas([piezas["Head"], piezas["Ojos"]], tmp, [("Cara", -12, 4)],
                                 tam=300 if args.rapido else 460, muestras=16 if args.rapido else 64, margen=0.9,
                                 con_malla=False, prefijo="cab_")
    rutas = rutas[:4] + cabeza + rutas[4:]
    c.montar_hoja([rutas], os.path.join(salida, f"hoja_contactos_{args.ronda}.png"),
                  f"Monstruo base R6 «El Hueco» — ronda {args.ronda}",
                  notas=[f"{total} triángulos · {alto:.1f} studs de alto · " +
                         ", ".join(f"{k} {v}" for k, v in tris.items())])

    arm = esqueleto_r6(piezas)
    c.exportar_fbx(os.path.join(salida, "Monstruo_R6_esqueleto.fbx"), lista, armature=arm)


if __name__ == "__main__":
    main()
