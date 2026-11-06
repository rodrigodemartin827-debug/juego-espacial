"""
Cristal abisal: el recurso exclusivo del planeta de los monstruos. Cristales negros como la obsidiana, con un
corazón morado que brilla por dentro y asoma por las puntas, sobre una roca oscura agrietada, y unas esquirlas que
flotan alrededor.

Mallas:
  Cristal_Abisal_Base       roca con textura (color + normales)
  Cristal_Abisal_Cristales  la obsidiana (en Studio: material Glass, color #2A1838, Transparency 0,35)
  Cristal_Abisal_Brillo     el corazón morado y la grieta de la base (Neon #B54DFF)
  Cristal_Abisal_Esquirlas  esquirlas flotantes (Neon): pieza aparte para hacerlas girar y subir y bajar

Uso:
    python modelos/herramientas/cristal_abisal.py --salida modelos/cristal_abisal [--ronda N] [--rapido]
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402,F401
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun as c  # noqa: E402
import kit  # noqa: E402
import rocas_minerales as rm  # noqa: E402
from ciudad_humana import kit_a_roblox  # noqa: E402
from planeta_monstruos import MORADO, ROCA, baja_horneada, luz_de_pieza  # noqa: E402

PALETA = {
    "Obsidiana": ("#1A1023", 0.08, 0.3, 0.0),
    "Neon": (MORADO, 0.3, 0.0, 0.0, 2.2),
}
# Cristales: (ángulo alrededor, distancia al centro, inclinación en grados, largo, grosor, lados)
CRISTALES = [
    (0.0, 0.0, 4, 6.5, 0.9, 6),
    (0.6, 1.3, 28, 4.4, 0.65, 5),
    (2.0, 1.4, 33, 3.6, 0.55, 6),
    (3.1, 1.2, 25, 4.9, 0.7, 5),
    (4.3, 1.5, 38, 3.0, 0.5, 6),
    (5.3, 1.1, 22, 4.0, 0.6, 5),
    (1.3, 2.1, 55, 2.2, 0.42, 5),
    (3.8, 2.2, 58, 2.0, 0.4, 6),
]


def construir(carpeta, rapido):
    rnd = random.Random(13)
    # Base: roca oscura baja (como las rocas del planeta).
    forma = dict(tam=(7.4, 6.6, 2.3), cortes=8, redondez=0.5, inclinacion=0)
    alta = c.objeto_desde_bmesh("Cristal_Abisal_Base_alta", rm.forma_roca(forma, rnd))
    rm.detallar(alta, dict(forma, ruido=0.12, estratos=0.0, paleta=ROCA), rnd, voxel_studs=0.12 if rapido else 0.06)
    base = baja_horneada(alta, "Cristal_Abisal_Base", 420, carpeta, rapido, angulo=50)

    cr = kit.Pieza("Cristal_Abisal_Cristales", PALETA)
    br = kit.Pieza("Cristal_Abisal_Brillo", PALETA)
    es = kit.Pieza("Cristal_Abisal_Esquirlas", PALETA)
    z0 = 1.3
    puntas = []
    for ang, dist, incl, largo, grosor, lados in CRISTALES:
        pos = Vector((math.cos(ang) * dist, math.sin(ang) * dist * 0.9, z0 - 0.4))
        eje_giro = Vector((-math.sin(ang), math.cos(ang), 0))
        eje = Matrix.Rotation(math.radians(incl), 3, eje_giro) @ Vector((0, 0, 1)) if dist else Vector((0.05, 0, 1))
        giro = rnd.uniform(0, math.tau)
        # Obsidiana: prisma con la punta cortada en bisel (la punta brillante sale de dentro).
        cr.prisma(pos, eje, largo * 0.86, grosor, lados, 0.18, "Obsidiana", rnd=rnd, giro=giro)
        # Corazón: prisma fino que recorre el cristal por dentro y asoma más allá de la punta.
        br.prisma(pos + eje * 0.2, eje, largo, grosor * 0.5, lados, 0.32, "Neon", giro=giro)
        puntas.append(pos + eje * largo)
    # Cristalitos sueltos alrededor de la base, medio enterrados.
    for i in range(6):
        a = i * math.tau / 6 + 0.5
        pos = Vector((math.cos(a) * 3.0, math.sin(a) * 2.7, 0.5))
        eje = Vector((math.cos(a) * 1.2, math.sin(a) * 1.2, 1.0))
        g = rnd.uniform(0, math.tau)
        largo = rnd.uniform(0.8, 1.5)
        cr.prisma(pos, eje, largo * 0.85, 0.22, 5, 0.25, "Obsidiana", rnd=rnd, giro=g)
        br.prisma(pos + eje.normalized() * 0.1, eje, largo, 0.1, 5, 0.4, "Neon", giro=g)
    # Grietas brillantes sobre la roca: líneas que salen del centro y siguen la superficie (rayos hacia abajo).
    E = c.ESTUDIO
    for i in range(6):
        a = i * math.tau / 6 + 0.25
        anterior = None
        for k in range(6):
            r = 1.0 + k * 0.5
            x, y = math.cos(a) * r + math.sin(k * 1.7) * 0.15, math.sin(a) * r * 0.9
            ok, punto, normal, _ = base.ray_cast(Vector((x, y, 20)) * E, Vector((0, 0, -1)))
            if not ok:
                break
            p = punto / E + Vector(normal) * 0.03
            if anterior is not None:
                tramo = p - anterior
                br.caja((p + anterior) / 2, (tramo.length + 0.05, 0.14 * (1 - k / 7), 0.06), "Neon",
                        giro=Vector(tramo).to_track_quat("X", "Z").to_matrix())
            anterior = p
    # Esquirlas flotantes: octaedros pequeños en un anillo inclinado alrededor.
    for i in range(7):
        a = i * math.tau / 7 + rnd.uniform(-0.2, 0.2)
        centro = Vector((math.cos(a) * 3.6, math.sin(a) * 3.3, 3.2 + math.sin(a * 2) * 0.9))
        t = rnd.uniform(0.18, 0.32)
        bm = es.bm
        q = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 1)).normalized().to_track_quat("Z", "Y")
        vs = [bm.verts.new(centro + q @ (v * t)) for v in (Vector((0, 0, 2.2)), Vector((1, 0, 0)),
                                                             Vector((0, 1, 0)), Vector((-1, 0, 0)),
                                                             Vector((0, -1, 0)), Vector((0, 0, -2.2)))]
        for k in range(4):
            j = 1 + (k + 1) % 4
            bm.faces.new((vs[0], vs[1 + k], vs[j]))
            bm.faces.new((vs[5], vs[j], vs[1 + k]))
        for f in bm.faces[-8:]:
            f.material_index = es.m("Neon")

    cristales = kit.terminar(cr, carpeta, rapido, bisel=0, con_textura=False)
    # Obsidiana translúcida: en Studio es Glass con Transparency ~0,35, que deja ver el corazón morado por dentro.
    b = cristales.data.materials[0].node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*c.srgb("#26133A"), 1)
    b.inputs["Transmission Weight"].default_value = 0.55
    b.inputs["Roughness"].default_value = 0.08
    b.inputs["IOR"].default_value = 1.2
    for p in cristales.data.polygons:
        p.use_smooth = False
    brillo = kit.terminar(br, carpeta, rapido, bisel=0, con_textura=False)
    esquirlas = kit.terminar(es, carpeta, rapido, bisel=0, con_textura=False)
    for o in (brillo, esquirlas):
        for p in o.data.polygons:
            p.use_smooth = False
    luz_de_pieza("Cristal_Abisal_luz", (0, 0, 3.0), energia=120)

    def extra(desp):
        return {"nota": "studs, ejes de Roblox, respecto al centro de la base",
                "Luz": kit_a_roblox(Vector((0, 0, 3.0)) + desp),
                "luz_recomendada": f"PointLight {MORADO}, Brightness 1.5, Range 14",
                "CentroEsquirlas": kit_a_roblox(Vector((0, 0, 3.2)) + desp),
                "como_animar_esquirlas": "girar Cristal_Abisal_Esquirlas en Y alrededor de CentroEsquirlas "
                                         "(una vuelta cada ~8 s) y subirla y bajarla 0,3 studs: en el cliente"}
    return [base, cristales, brillo, esquirlas], extra


ITEMS = [dict(archivo="Cristal_Abisal", titulo="Cristal abisal", construir=construir)]

if __name__ == "__main__":
    a = kit.argumentos()
    vistas = [("Frente", 0, 10), ("3/4", -40, 22), ("Lateral", -90, 8), ("3/4 trasera", 140, 25),
              ("Arriba", 15, 70), ("Contrapicado", 25, -8)]
    kit.ejecutar_lote(ITEMS, a.salida, "Cristal abisal (recurso exclusivo de los monstruos)", a.ronda, a.rapido,
                      vistas=vistas, nota="Obsidiana (Glass oscuro) + corazón y esquirlas en Neon morado")
