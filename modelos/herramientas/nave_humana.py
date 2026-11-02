"""
Nave humana inicial ("Alba"): caza ligero de ciencia ficción limpia, low-poly cuidado (< 5.000 triángulos).

Se construye con secciones (anillos) unidas en loft, así cada pieza tiene justo los polígonos que necesita:
  * Fuselaje con morro afilado, joroba de cabina y cola que se ensancha hacia los motores.
  * Cabina de cristal (malla aparte: en Studio, material Glass).
  * Alas en flecha con un cañón en cada punta.
  * Dos góndolas de motor con toberas acampanadas bien visibles y su núcleo brillante.
  * Dos derivas inclinadas, tomas de aire y patines.
  * Franjas y luces de posición brillantes (malla aparte: en Studio, material Neon).

Salen tres mallas:
  Nave_Casco    el cuerpo, con una textura horneada (colores + oclusión ambiental + bordes biselados en normales)
  Nave_Cristal  la cabina
  Nave_Neon     todo lo que brilla (núcleos de las toberas, franjas, luces)

Medidas en studs. La nave mira a -Y en Blender (a -Z en Roblox). Su derecha es -X en Blender (+X en Roblox).

Uso:
    python modelos/herramientas/nave_humana.py --salida modelos/nave_humana [--ronda N] [--rapido]
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun as c  # noqa: E402

E = c.ESTUDIO

# --------------------------------------------------------------------------------------------------------------
# Datos ajustables
# --------------------------------------------------------------------------------------------------------------

# Colores del bando humano (los mismos tonos que ServicioNaves/Modelo usa para la nave de código).
COLORES = {
    "Casco": ("#E2E9F6", 0.38, 0.15),  # (color, rugosidad, metal)
    "Oscuro": ("#56647F", 0.45, 0.55),
    "Grafito": ("#262A33", 0.55, 0.4),
    "Acento": ("#FF8A2B", 0.4, 0.1),
    "Tobera": ("#3A3E48", 0.35, 0.9),
    "Cristal": ("#16324F", 0.05, 0.0),
    "Neon": ("#4DF0FF", 0.3, 0.0),
}

# Fuselaje: (y, ancho, alto, z del centro, cuadratura). Cuadratura 2 = elipse, más alto = más cuadrado.
FUSELAJE = [
    (-8.9, 0.30, 0.20, -0.10, 2.0),
    (-8.5, 0.70, 0.46, -0.08, 2.2),
    (-7.4, 1.20, 0.80, -0.02, 2.4),
    (-6.9, 1.45, 0.95, 0.0, 2.5),  # banda naranja del morro entre -6,9 y -6,4
    (-6.4, 1.62, 1.04, 0.02, 2.5),
    (-5.6, 1.85, 1.18, 0.05, 2.6),
    (-3.4, 2.35, 1.50, 0.10, 2.8),
    (-1.0, 2.70, 1.70, 0.10, 3.0),
    (1.6, 2.80, 1.70, 0.08, 3.2),
    (3.8, 2.60, 1.55, 0.05, 3.2),
    (5.6, 2.20, 1.30, 0.05, 3.0),
    (6.6, 1.80, 1.05, 0.05, 2.8),
]
LADOS_FUSELAJE = 20

# Cabina: (y, ancho, alto sobre el fuselaje, z de la base)
CABINA = [
    (-5.9, 0.10, 0.02, 0.55),
    (-5.2, 0.95, 0.38, 0.60),
    (-3.8, 1.55, 0.72, 0.72),
    (-2.0, 1.70, 0.80, 0.80),
    (-0.4, 1.45, 0.62, 0.85),
    (0.6, 0.90, 0.25, 0.86),
]

# Góndolas de motor: centro x, z, y desde-hasta, radio.
GONDOLA = dict(x=2.05, z=-0.05, y0=-0.6, y1=6.2, radio=0.78, lados=18)
# Perfil de la tobera (y relativo al final de la góndola, radio): la campana que se ve desde atrás.
TOBERA = [(0.0, 0.70), (0.25, 0.66), (0.55, 0.74), (0.95, 0.92), (1.15, 0.95)]
NUCLEO_Y = 0.35  # dónde está el disco brillante dentro de la tobera

# Ala: (x, y del borde de ataque, y del borde de salida, z, grosor)
ALA = [(1.25, -2.6, 4.8, -0.05, 0.50), (2.9, -0.6, 4.7, -0.12, 0.42), (4.6, 1.0, 4.5, -0.20, 0.32),
       (6.0, 2.0, 4.3, -0.26, 0.26)]
CANON = dict(x=6.2, z=-0.26, y0=0.0, y1=4.5, radio=0.27, lados=8)

DERIVA = dict(y0=2.8, y1=6.0, alto=1.9, inclinacion=22, grosor=0.14, retraso_punta=1.4)

TAM_TEXTURA = 1024


def col(nombre):
    return c.srgb(COLORES[nombre][0])


# --------------------------------------------------------------------------------------------------------------
# Construcción de mallas con anillos
# --------------------------------------------------------------------------------------------------------------


def anillo_superelipse(y, ancho, alto, zc, n, cuadratura, xc=0.0):
    """Puntos de una sección superelíptica en el plano XZ a la altura `y`."""
    pts = []
    for i in range(n):
        a = math.tau * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = math.copysign(abs(ca) ** (2 / cuadratura), ca) * ancho / 2
        z = math.copysign(abs(sa) ** (2 / cuadratura), sa) * alto / 2
        pts.append(Vector((xc + x, y, zc + z)))
    return pts


def loft(bm, anillos, tapar_inicio=True, tapar_fin=True, mat=0):
    """Une anillos consecutivos (todos con el mismo número de puntos) en un tubo. Devuelve los vértices."""
    vs = [[bm.verts.new(p) for p in a] for a in anillos]
    n = len(anillos[0])
    caras = []
    for k in range(len(vs) - 1):
        for i in range(n):
            j = (i + 1) % n
            caras.append(bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i])))
    if tapar_inicio:
        caras.append(bm.faces.new(list(reversed(vs[0]))))
    if tapar_fin:
        caras.append(bm.faces.new(vs[-1]))
    for f in caras:
        f.material_index = mat
    return vs, caras


def caja(bm, centro, tam, mat=0, giro=None):
    r = bmesh.ops.create_cube(bm, size=1.0)
    m = Matrix.Diagonal((*tam, 1.0))
    if giro is not None:
        m = giro.to_4x4() @ m
    bmesh.ops.transform(bm, matrix=Matrix.Translation(centro) @ m, verts=r["verts"])
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat
    return r["verts"]


def espejo_x(bm, verts):
    """Duplica `verts` (y sus caras) reflejados en X."""
    caras = list({f for v in verts for f in v.link_faces if all(w in verts for w in f.verts)})
    res = bmesh.ops.duplicate(bm, geom=caras)
    nuevos = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.scale(bm, vec=(-1, 1, 1), verts=nuevos)
    nuevas_caras = [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]
    bmesh.ops.reverse_faces(bm, faces=nuevas_caras)
    return nuevos


def _en_flap(p):
    """True si el punto del ala está en el último cuarto de la cuerda (el flap)."""
    x = abs(p.x)
    for (x0, a0, s0, _, _), (x1, a1, s1, _, _) in zip(ALA, ALA[1:]):
        if x0 - 1e-4 <= x <= x1 + 1e-4:
            t = (x - x0) / (x1 - x0)
            ya, ys = a0 + (a1 - a0) * t, s0 + (s1 - s0) * t
            return p.y >= ya + (ys - ya) * 0.73
    return False


# Índices de material del casco.
M_CASCO, M_OSCURO, M_GRAFITO, M_ACENTO, M_TOBERA = range(5)


def construir_casco():
    bm = bmesh.new()

    # Fuselaje.
    anillos = [anillo_superelipse(y, w, h, z, LADOS_FUSELAJE, q) for y, w, h, z, q in FUSELAJE]
    vs, caras = loft(bm, anillos, mat=M_CASCO)
    # La panza del fuselaje, más oscura: caras cuyo centro está por debajo del eje.
    for f in caras:
        cen = f.calc_center_median()
        if f.normal.z < -0.55 and abs(cen.x) < 0.75:
            f.material_index = M_OSCURO  # quilla oscura bajo el fuselaje
        elif cen.y < -8.0:
            f.material_index = M_GRAFITO  # punta del morro (radomo)
        elif -6.9 < cen.y < -6.4 and f.normal.z > -0.5:
            f.material_index = M_ACENTO  # banda naranja en el morro
    # La tapa trasera del fuselaje (entre los motores): gris oscuro.
    caras[-1].material_index = M_GRAFITO

    # Góndolas de motor (una y su reflejo).
    g = GONDOLA
    lados = g["lados"]
    perfil = [  # (y, radio)
        (g["y0"] - 0.2, g["radio"] * 0.55),
        (g["y0"] + 0.3, g["radio"] * 0.92),
        (g["y0"] + 1.4, g["radio"]),
        (g["y1"] - 0.9, g["radio"]),
        (g["y1"], g["radio"] * 0.93),
    ]
    anillos_g = [anillo_superelipse(y, r * 2, r * 2, g["z"], lados, 2.0, xc=-g["x"]) for y, r in perfil]
    vg, caras_g = loft(bm, anillos_g, tapar_fin=False, mat=M_CASCO)
    for f in caras_g[-lados:]:
        f.material_index = M_OSCURO  # aro de detrás
    # Tobera acampanada: un loft hacia fuera y su pared interior hacia dentro, para que tenga grosor.
    yb = g["y1"]
    ext = [anillo_superelipse(yb + dy, r * 2, r * 2, g["z"], lados, 2.0, xc=-g["x"]) for dy, r in TOBERA]
    interior = [anillo_superelipse(yb + dy, (r - 0.08) * 2, (r - 0.08) * 2, g["z"], lados, 2.0, xc=-g["x"])
                for dy, r in reversed(TOBERA)]
    vt, caras_t = loft(bm, ext + interior, tapar_inicio=False, tapar_fin=True, mat=M_TOBERA)
    verts_motor = [v for a in vg for v in a] + [v for a in vt for v in a]

    # Pilón que une la góndola al fuselaje.
    pilon = caja(bm, Vector((-(g["x"] + 1.1) / 2, (g["y0"] + g["y1"]) / 2 + 0.6, g["z"] + 0.15)),
                 (g["x"] - 0.9, g["y1"] - g["y0"] - 2.2, 0.55), mat=M_OSCURO)
    verts_motor += pilon

    # Toma de aire delante de la góndola.
    toma = caja(bm, Vector((-g["x"] + 0.05, g["y0"] - 0.05, g["z"] + 0.05)), (0.9, 0.35, 0.7), mat=M_GRAFITO)
    verts_motor += toma

    # Ala: secciones de perfil (rombo achatado) del encastre a la punta.
    anillos_a = []
    for x, ya, ys, z, gr in ALA:
        cuerda = ys - ya
        anillos_a.append([
            Vector((-x, ya, z)),
            Vector((-x, ya + cuerda * 0.3, z + gr / 2)),
            Vector((-x, ya + cuerda * 0.74, z + gr * 0.3)),  # inicio del flap
            Vector((-x, ys, z + gr * 0.1)),
            Vector((-x, ys, z - gr * 0.1)),
            Vector((-x, ya + cuerda * 0.74, z - gr * 0.3)),
            Vector((-x, ya + cuerda * 0.35, z - gr / 2)),
        ])
    va, caras_a = loft(bm, anillos_a, mat=M_CASCO)
    # Franja de acento en el borde de ataque de la última sección del ala.
    for f in caras_a:
        cen = f.calc_center_median()
        ya_f = None
        if abs(cen.x) > 4.0 and f.normal.y < -0.25:
            f.material_index = M_ACENTO  # borde de ataque exterior en naranja
        elif len(f.verts) == 4 and all(_en_flap(v.co) for v in f.verts):
            f.material_index = M_OSCURO  # flaps del borde de salida, en gris
    verts_ala = [v for a in va for v in a]

    # Cañón en la punta del ala: soporte + tubo + boca.
    cn = CANON
    perfil_c = [(cn["y0"] - 0.9, cn["radio"] * 0.55), (cn["y0"] - 0.6, cn["radio"] * 0.7),
                (cn["y0"] + 0.2, cn["radio"] * 0.8), (cn["y0"] + 0.5, cn["radio"] * 1.25),
                (cn["y1"] - 0.5, cn["radio"] * 1.3), (cn["y1"], cn["radio"] * 0.8)]
    anillos_c = [anillo_superelipse(y, r * 2, r * 2, cn["z"], cn["lados"], 2.0, xc=-cn["x"]) for y, r in perfil_c]
    vc, caras_c = loft(bm, anillos_c, mat=M_OSCURO)
    caras_c[-2].material_index = M_GRAFITO  # tapa delantera (la boca)
    verts_ala += [v for a in vc for v in a]

    # Deriva inclinada sobre la góndola.
    d = DERIVA
    base_z = g["z"] + g["radio"] * 0.8
    perfil_d = [
        Vector((0, d["y0"], 0)), Vector((0, d["y1"], 0)),
        Vector((0, d["y1"] + 0.2, d["alto"])), Vector((0, d["y0"] + d["retraso_punta"] + 0.9, d["alto"])),
    ]
    rot = Matrix.Rotation(math.radians(-d["inclinacion"]), 3, "Y")  # se abre hacia fuera (a -X)
    capas = []
    for s in (-1, 1):
        capas.append([rot @ (p + Vector((s * d["grosor"] / 2, 0, 0))) + Vector((-g["x"], 0, base_z))
                      for p in perfil_d])
    vd, caras_d = loft(bm, [capas[0], capas[1]], mat=M_CASCO)
    # Punta de la deriva en naranja: se parte la deriva a 2/3 de su altura.
    caras_f = set(caras_d)
    aristas_f = {e for f in caras_f for e in f.edges}
    verts_f = {v for f in caras_f for v in f.verts}
    corte = bmesh.ops.bisect_plane(bm, geom=list(caras_f) + list(aristas_f) + list(verts_f),
                                   plane_co=Vector((0, 0, base_z + d["alto"] * 0.62)), plane_no=Vector((0, 0, 1)))
    verts_f |= {g for g in corte["geom"] if isinstance(g, bmesh.types.BMVert)}
    for f in {f for v in verts_f for f in v.link_faces}:
        if f.calc_center_median().z > base_z + d["alto"] * 0.62:
            f.material_index = M_ACENTO
    vd = [list(verts_f)]
    verts_motor += [v for a in vd for v in a]

    # Patines de aterrizaje (tres): bajo el morro y bajo cada góndola.
    patines = caja(bm, Vector((-g["x"], 2.6, g["z"] - g["radio"] - 0.18)), (0.18, 1.6, 0.36), mat=M_GRAFITO)
    verts_motor += patines

    # Reflejar el lado derecho (motor, ala, cañón, deriva) al izquierdo.
    espejo_x(bm, verts_motor + verts_ala)

    caja(bm, Vector((0, -5.6, -0.62)), (0.22, 1.2, 0.36), mat=M_GRAFITO)  # patín del morro

    # Tomas de aire laterales junto a la cabina: una caja en cuña con la boca en grafito.
    for sx in (-1, 1):
        anillos_t = []
        for y, w, h, z in [(-3.6, 0.15, 0.55, 0.0), (-3.2, 0.5, 0.75, 0.0), (-0.6, 0.55, 0.8, 0.0),
                           (1.6, 0.25, 0.6, 0.0)]:
            anillos_t.append(anillo_superelipse(y, w, h, z, 8, 3.5, xc=sx * (1.3 + w / 2 - 0.1)))
        vt2, caras_t2 = loft(bm, anillos_t, mat=M_OSCURO)
        caras_t2[-2].material_index = M_GRAFITO  # la boca
        for f in caras_t2:
            if f.normal.y < -0.6:
                f.material_index = M_GRAFITO

    # Antena dorsal y aleta ventral.
    caja(bm, Vector((0, 3.2, 1.55)), (0.06, 0.9, 0.5), mat=M_GRAFITO,
         giro=Matrix.Rotation(math.radians(-25), 3, "X"))
    aleta = [Vector((0, 2.6, -0.7)), Vector((0, 5.8, -0.55)), Vector((0, 6.0, -1.25)), Vector((0, 4.6, -1.3))]
    loft(bm, [[p + Vector((-0.07, 0, 0)) for p in aleta], [p + Vector((0.07, 0, 0)) for p in aleta]], mat=M_OSCURO)

    # Lomo: carenado sobre el fuselaje detrás de la cabina.
    lomo = [anillo_superelipse(y, w, h, z, 8, 2.6) for y, w, h, z in
            [(0.4, 0.3, 0.2, 0.86), (1.0, 1.1, 0.5, 0.9), (4.2, 1.0, 0.45, 0.82), (5.8, 0.4, 0.2, 0.7)]]
    loft(bm, lomo, mat=M_OSCURO)

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mats = [c.material("Casco", col("Casco"), *COLORES["Casco"][1:]),
            c.material("Oscuro", col("Oscuro"), *COLORES["Oscuro"][1:]),
            c.material("Grafito", col("Grafito"), *COLORES["Grafito"][1:]),
            c.material("Acento", col("Acento"), *COLORES["Acento"][1:]),
            c.material("Tobera", col("Tobera"), *COLORES["Tobera"][1:])]
    return c.objeto_desde_bmesh("Nave_Casco", bm, mats)


def construir_cristal():
    bm = bmesh.new()
    anillos = []
    for y, w, h, z in CABINA:
        # Medio óvalo: solo la parte de arriba (la base queda hundida en el fuselaje).
        n = 10
        pts = []
        for i in range(n + 1):
            a = math.pi * i / n
            pts.append(Vector((math.cos(a) * w / 2, y, z + math.sin(a) * h)))
        anillos.append(pts)
    loft(bm, anillos, mat=0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = c.material("Cristal", col("Cristal"), rugosidad=0.04, metal=0.2)
    return c.objeto_desde_bmesh("Nave_Cristal", bm, [m])


def construir_neon():
    bm = bmesh.new()
    g = GONDOLA
    # Núcleo de cada tobera: un disco con un cono hacia dentro (se ve brillante desde detrás y en ángulo).
    for s in (-1, 1):
        yb = g["y1"] + NUCLEO_Y
        aro = anillo_superelipse(yb, 1.2, 1.2, g["z"], 12, 2.0, xc=s * g["x"])
        fondo = anillo_superelipse(yb - 0.25, 0.5, 0.5, g["z"], 12, 2.0, xc=s * g["x"])
        loft(bm, [aro, fondo], tapar_inicio=False)
        # Franja en el lateral de la góndola.
        caja(bm, Vector((s * (g["x"] + g["radio"] - 0.02), 2.6, g["z"] + 0.1)), (0.06, 3.0, 0.12))
        # Luz de posición en la punta del cañón y del ala.
        caja(bm, Vector((s * (CANON["x"] + 0.02), CANON["y1"] - 0.6, CANON["z"] + 0.33)), (0.12, 0.5, 0.06))
        # Línea a lo largo del borde de la deriva.
    # Franjas a los lados del fuselaje, bajo la cabina.
    for s in (-1, 1):
        caja(bm, Vector((s * 1.34, -2.2, 0.2)), (0.05, 3.6, 0.1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = c.material("Neon", col("Neon"), rugosidad=0.3, emision=col("Neon"), fuerza_emision=8.0)
    return c.objeto_desde_bmesh("Nave_Neon", bm, [m])


# Puntos de anclaje (Attachments en Studio), en studs respecto al centro del modelo exportado.
def anclajes():
    g, cn = GONDOLA, CANON
    return {
        "Ejes": (0, 0, 0),
        "Piloto": (0, -2.4, 0.9),
        "CanonDer": (-cn["x"], cn["y0"] - 0.95, cn["z"]),
        "CanonIzq": (cn["x"], cn["y0"] - 0.95, cn["z"]),
        "MotorDer": (-g["x"], g["y1"] + TOBERA[-1][0], g["z"]),
        "MotorIzq": (g["x"], g["y1"] + TOBERA[-1][0], g["z"]),
    }


def a_roblox(p):
    """Blender (x, y, z) en studs -> Roblox (x, y, z): X cambia de signo, Z de Blender es Y, Y de Blender es Z."""
    x, y, z = p
    return (round(-x, 3), round(z, 3), round(y, 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    os.makedirs(os.path.join(salida, "texturas"), exist_ok=True)

    c.escena_vacia()
    casco = construir_casco()
    cristal = construir_cristal()
    neon = construir_neon()
    for o in (casco, cristal, neon):
        c.sombreado_suave(o, angulo=35)

    # Textura del casco: los colores de cada material + oclusión ambiental.
    c.desplegar_uv(casco, margen=0.01)
    c.hornear(casco, None, tam=256 if args.rapido else TAM_TEXTURA,
              ruta_color=os.path.join(salida, "texturas", "Nave_Casco_color.png"), muestras=8 if args.rapido else 64)
    m = casco.data.materials[0].node_tree.nodes["Principled BSDF"]
    m.inputs["Roughness"].default_value = 0.4
    m.inputs["Metallic"].default_value = 0.25

    piezas = [casco, cristal, neon]
    tris = {o.name: c.triangulos(o) for o in piezas}
    total = sum(tris.values())
    mn, mx = c.caja_limite(piezas)
    dim = (mx - mn) / E
    # Centro del modelo en el origen (Ejes).
    c.exportar_fbx(os.path.join(salida, "Nave_Humana.fbx"), piezas)
    with open(os.path.join(salida, "anclajes.json"), "w", encoding="utf-8") as f:
        json.dump({k: a_roblox(v) for k, v in anclajes().items()}, f, indent=2, ensure_ascii=False)

    c.preparar_estudio(z_suelo=mn.z - 0.25 * E)
    vistas = [("Frente", 0, 6), ("3/4 delantera", -38, 20), ("Lateral", -90, 4), ("3/4 trasera", -145, 18),
              ("Detrás (toberas)", 180, 6), ("Arriba", 0, 88), ("Abajo", 30, -40)]
    rutas = c.renderizar_vistas(piezas, os.path.join(salida, "_render_tmp"), vistas, tam=300 if args.rapido else 460,
                                muestras=16 if args.rapido else 64, margen=0.92)
    c.montar_hoja([rutas], os.path.join(salida, f"hoja_contactos_{args.ronda}.png"),
                  f"Nave humana inicial — ronda {args.ronda}",
                  notas=[f"{total} triángulos (casco {tris['Nave_Casco']}, cristal {tris['Nave_Cristal']}, "
                         f"neon {tris['Nave_Neon']})  ·  {dim.x:.1f} × {dim.y:.1f} × {dim.z:.1f} studs (ancho × largo × alto)"])


if __name__ == "__main__":
    main()
