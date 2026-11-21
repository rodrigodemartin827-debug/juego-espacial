"""
Nave H2 — Fragata Estelar: nave de combate humana mediana (4-6 tripulantes), dos niveles.

Silueta: buque de guerra compacto con ariete angular en la proa, cuerpo robusto de placas y 3 propulsores
en triángulo en la popa. Cubierta superior abierta (timón elevado, mesa de navegación, 4 cañones) y cubierta
inferior cerrada (sala de motores, almacén con 2 cofres, puesto de reparación), unidas por 2 escaleras.

Ejes: mira a -Y (delante de Roblox). Babor = +X, estribor = -X.
Niveles: suelo inferior en z = 0, techo/cubierta superior en z = 6 (interior de 6 studs), quilla hacia z = -4.

Uso: python modelos/herramientas/nave_fragata.py --salida modelos/nave_fragata [--rapido]
"""

import argparse
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Euler, Vector  # noqa: E402

import comun as c  # noqa: E402
import naves_humanas_comun as h  # noqa: E402

# Límites del casco.
BEAM = 10.5       # medio ancho del costado
Y_PROA = -15.0    # donde empieza a estrecharse la proa
Y_PUNTA = -24.0   # punta del ariete
Y_POPA = 22.0
Z_QUILLA = -4.0
Z_BULW = 6.3      # borde superior del costado (regala)
Z_SUP = 6.0       # cubierta superior
HALF_IN = 9.0     # medio ancho interior


def construir_casco(bm, bmn_hull):
    mc, mo, mp = h.M_CASCO, h.M_OSCURO, h.M_PANEL
    # Fondo / quilla.
    h.caja(bm, (0, (Y_PROA + Y_POPA) / 2, Z_QUILLA + 0.5), (BEAM * 2 - 0.5, Y_POPA - Y_PROA, 1.0), mat=mo)
    h.caja(bm, (0, (Y_PROA + Y_POPA) / 2, Z_QUILLA + 0.2), (2.0, Y_POPA - Y_PROA + 2, 0.5), mat=mo)  # quilla central
    largo = Y_POPA - Y_PROA
    cy = (Y_PROA + Y_POPA) / 2
    zc = (Z_QUILLA + Z_BULW) / 2
    alto = Z_BULW - Z_QUILLA
    for s in (1, -1):
        # Costado con ligero tumblehome (la parte alta hacia dentro).
        h.caja(bm, (s * BEAM, cy, zc), (0.7, largo, alto), mat=mc, giro=Euler((0, math.radians(-s * 5), 0)))
        # Placas de blindaje superpuestas en el costado (relieve real, finas hacia fuera) + línea de energía.
        for yy in range(int(Y_PROA) + 3, int(Y_POPA) - 1, 5):
            h.caja(bm, (s * (BEAM + 0.15), yy, zc), (0.3, 4.4, alto * 0.82), mat=mp)       # placa
            h.caja(bm, (s * (BEAM + 0.28), yy, zc), (0.12, 3.6, alto * 0.7), mat=mc)        # panel central
            for dz in (-alto * 0.3, alto * 0.3):
                h.cilindro(bm, (s * (BEAM + 0.3), yy, zc + dz), 0.08, 0.1, lados=6, eje="X", mat=mo)  # remaches
        h.franja_neon(bmn_hull, (s * (BEAM + 0.3), cy, 4.2), (0.08, largo - 2, 0.16), mat=0)
        h.franja_neon(bmn_hull, (s * (BEAM + 0.3), cy, 0.2), (0.08, largo - 4, 0.12), mat=0)
    # Pared de popa.
    h.caja(bm, (0, Y_POPA, zc), (BEAM * 2, 0.7, alto), mat=mc)
    # Proa: dos planos que convergen de Y_PROA (±BEAM) a la punta (0).
    for s in (1, -1):
        v = [bm.verts.new(p) for p in [
            (s * BEAM, Y_PROA, Z_QUILLA + 0.4), (s * BEAM, Y_PROA, Z_BULW),
            (s * 0.3, Y_PUNTA, Z_BULW - 0.5), (s * 0.3, Y_PUNTA, Z_QUILLA + 1.2)]]
        bm.faces.new(v).material_index = mc
    # Fondo de proa (triángulo).
    v = [bm.verts.new(p) for p in [(BEAM, Y_PROA, Z_QUILLA + 0.4), (-BEAM, Y_PROA, Z_QUILLA + 0.4),
                                   (0, Y_PUNTA, Z_QUILLA + 1.2)]]
    bm.faces.new(v).material_index = mo
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def construir_ariete(bm, bmn_faro):
    # Ariete: espolón blindado que sobresale de la proa (pieza aparte) + nervios + faro potente.
    # Cuerpo piramidal que apunta a -Y, desde una base ancha en Y_PROA hasta una punta roma en Y_PUNTA-0.6.
    base = [(1.8, Y_PROA + 0.5, 0.2), (-1.8, Y_PROA + 0.5, 0.2),
            (-1.8, Y_PROA + 0.5, 3.4), (1.8, Y_PROA + 0.5, 3.4)]
    punta_sup = (0.6, Y_PUNTA - 0.6, 2.4)
    punta_inf = (0.6, Y_PUNTA - 0.6, 1.0)
    vb = [bm.verts.new(p) for p in base]
    pa = bm.verts.new(punta_sup)
    pb = bm.verts.new((-punta_sup[0], punta_sup[1], punta_sup[2]))
    pc = bm.verts.new(punta_inf)
    pd = bm.verts.new((-punta_inf[0], punta_inf[1], punta_inf[2]))
    caras = [(vb[0], vb[3], pa, pc), (vb[2], vb[1], pd, pb), (vb[3], vb[2], pb, pa),
             (vb[1], vb[0], pc, pd), (pa, pb, pd, pc), (vb[0], vb[1], vb[2], vb[3])]
    for cc in caras:
        try:
            bm.faces.new(cc).material_index = h.M_OSCURO
        except ValueError:
            pass
    # Nervios de refuerzo (3 costillas) sobre el espolón.
    for dz in (0.4, 1.7, 3.0):
        h.caja(bm, (0, Y_PROA - 2.0, dz), (3.0, 0.3, 0.3), mat=h.M_PANEL)
    # Placas laterales angulares que lo unen al casco.
    for s in (1, -1):
        v = [bm.verts.new(p) for p in [
            (s * 1.8, Y_PROA + 0.5, 0.4), (s * 0.6, Y_PUNTA - 0.6, 1.0),
            (s * 0.6, Y_PUNTA - 0.6, 2.4), (s * 1.8, Y_PROA + 0.5, 3.4)]]
        try:
            bm.faces.new(v).material_index = h.M_PANEL
        except ValueError:
            pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    h.cilindro(bmn_faro, (0, Y_PUNTA - 0.9, 1.7), 0.35, 0.3, lados=12, eje="Y", mat=0)


def suelo_inferior(bm):
    h.caja(bm, (0, 3.5, -0.25), (HALF_IN * 2, 32, 0.5), mat=h.M_GRIP)
    for yy in range(-11, 19, 2):
        h.caja(bm, (0, yy, 0.03), (HALF_IN * 2 - 0.6, 0.08, 0.05), mat=h.M_OSCURO)  # rejilla
    # Maquinaria que se ve bajo la rejilla.
    for s in (1, -1):
        h.caja(bm, (s * 5, 15, -0.5), (3, 6, 0.6), mat=h.M_PANEL)


def paredes_inferior(bm, bmn):
    mc = h.M_CASCO
    for s in (1, -1):
        h.caja(bm, (s * HALF_IN, 3.5, 3.0), (0.4, 32, 6), mat=mc)
        h.franja_neon(bmn, (s * (HALF_IN - 0.25), 3.5, 5.5), (0.05, 30, 0.1), mat=0)  # tira de emergencia
        # Tuberías y cables.
        h.tuberia(bm, (s * (HALF_IN - 0.4), 3.5, 1.2), largo=28, radio=0.18, eje="Y", mat=h.M_OSCURO)
    h.caja(bm, (0, -12.5, 3.0), (HALF_IN * 2, 0.4, 6), mat=mc)   # mamparo de proa
    h.caja(bm, (0, 19.5, 3.0), (HALF_IN * 2, 0.4, 6), mat=mc)    # mamparo de popa (sala de motores)


def techo_inferior(bm, bmn):
    # Vigas + luces (debajo de la cubierta superior).
    for yy in range(-10, 19, 4):
        h.caja(bm, (0, yy, 5.4), (HALF_IN * 2, 0.5, 0.4), mat=h.M_OSCURO)
    h.franja_neon(bmn, (0, 3.5, 5.3), (0.14, 30, 0.08), mat=0)
    for s in (1, -1):
        h.franja_neon(bmn, (s * 5, 3.5, 5.3), (0.1, 28, 0.06), mat=0)


def cubierta_superior(bm):
    # Cubierta principal (transitable) con hueco de popa para las escaleras.
    h.caja(bm, (0, 1.0, Z_SUP - 0.25), (HALF_IN * 2, 29, 0.5), mat=h.M_GRIP)  # y -13.5..15.5
    for s in (1, -1):
        h.caja(bm, (s * 6.5, 18.5, Z_SUP - 0.25), (6, 6, 0.5), mat=h.M_GRIP)  # tiras de popa (dejan hueco central)
    for yy in range(-12, 15, 2):
        h.caja(bm, (0, yy, Z_SUP + 0.03), (HALF_IN * 2 - 1, 0.08, 0.05), mat=h.M_OSCURO)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    os.makedirs(salida, exist_ok=True)

    c.escena_vacia()
    mm = h.materiales_metal()

    bms = {k: bmesh.new() for k in [
        "casco", "ariete", "sup", "inf_suelo", "inf_par", "inf_techo", "timon", "ancla", "mesa", "rep"]}
    bm_can = [bmesh.new() for _ in range(4)]
    bm_mot = [bmesh.new() for _ in range(3)]
    bm_esc = [bmesh.new() for _ in range(2)]
    bm_cof = [bmesh.new() for _ in range(2)]
    bm_bar = [bmesh.new() for _ in range(4)]
    bm_marca = bmesh.new()
    neon = {k: bmesh.new() for k in ["hull", "tob", "int", "mesa", "faro", "timon"]}

    construir_casco(bms["casco"], neon["hull"])
    construir_ariete(bms["ariete"], neon["faro"])
    suelo_inferior(bms["inf_suelo"])
    paredes_inferior(bms["inf_par"], neon["int"])
    techo_inferior(bms["inf_techo"], neon["int"])
    cubierta_superior(bms["sup"])

    # Timón en plataforma elevada (popa de la cubierta superior).
    h.caja(bms["timon"], (0, 15.5, Z_SUP + 0.5), (6, 4, 1.0), mat=h.M_PANEL)  # plataforma
    h.consola_timon(bms["timon"], neon["timon"], (0, 15.0, Z_SUP + 1.0))
    # Mesa de navegación cerca del timón.
    h.mesa_nav(bms["mesa"], neon["mesa"], (0, 11.0, Z_SUP))
    # 4 cañones (2 por lado).
    asientos = []
    for i, (sx, yy) in enumerate([(9, -4), (-9, -4), (9, 8), (-9, 8)]):
        asientos.append(h.canon(bm_can[i], neon["hull"], (sx, yy, Z_SUP), longitud=3.0, dobles=(i < 2), radio=0.26))
    # 3 motores en triángulo (2 abajo, 1 arriba).
    for i, (mx, mz) in enumerate([(4.5, -1.0), (-4.5, -1.0), (0.0, 3.5)]):
        h.tobera(bm_mot[i], neon["tob"], (mx, Y_POPA + 0.5, mz), radio=1.2, largo=3.0)
    # 2 escaleras laterales (bajan de la cubierta superior a la inferior en el hueco de popa).
    for i, sx in enumerate((2.6, -2.6)):
        h.escalera(bm_esc[i], (sx, 15.0, 0.0), ancho=2.6, subida=6.0, fondo=6.0, pasos=9)
    # Almacén: 2 cofres en la cubierta inferior.
    h.cofre(bm_cof[0], neon["int"], (5.5, 2.0, 0.0))
    h.cofre(bm_cof[1], neon["int"], (-5.5, 2.0, 0.0))
    # Puesto de reparación (mamparo de proa, mirando a +Y).
    h.reparacion(bms["rep"], neon["int"], (0, -11.6, 0.0))
    # Ancla central bajo la proa.
    palanca = h.ancla(bms["ancla"], neon["hull"], (2.0, -12.0, -1.0), lado=1)
    # Barandillas del perímetro de la cubierta superior.
    h.barandilla(bm_bar[0], [Vector((9, y, Z_SUP)) for y in (-13, -6, 2, 10, 15)], alto=2.2, grosor=0.09, paso=3.5)
    h.barandilla(bm_bar[1], [Vector((-9, y, Z_SUP)) for y in (-13, -6, 2, 10, 15)], alto=2.2, grosor=0.09, paso=3.5)
    h.barandilla(bm_bar[2], [Vector(x) for x in [(9, -13, Z_SUP), (0, -13.5, Z_SUP), (-9, -13, Z_SUP)]],
                 alto=2.2, grosor=0.09, paso=3.5)
    h.barandilla(bm_bar[3], [Vector((9.5, 21, Z_SUP)), Vector((-9.5, 21, Z_SUP))], alto=2.2, grosor=0.09, paso=3.5)

    # Marcas de interacción.
    for p in [(0, 16.5, Z_SUP + 1.0)] + asientos + [palanca, (5.5, 0.3, 0.0), (-5.5, 0.3, 0.0),
                                                    (0, -9.8, 0.0), (0, 9.0, Z_SUP)]:
        h.marca(bm_marca, p)

    # Crear objetos.
    piezas = {}
    def add(nombre, bm, mats=mm, suav=30):
        piezas[nombre] = h.objeto(nombre, bm, mats, suavizar=suav)

    add("Fragata_Casco", bms["casco"], suav=25)
    add("Fragata_Ariete", bms["ariete"], suav=20)
    add("Fragata_Cubierta_Sup", bms["sup"], suav=16)
    add("Fragata_Cubierta_Inf_Suelo", bms["inf_suelo"], suav=16)
    add("Fragata_Cubierta_Inf_Paredes", bms["inf_par"], suav=16)
    add("Fragata_Cubierta_Inf_Techo", bms["inf_techo"], suav=16)
    add("Fragata_Timon", bms["timon"])
    add("Fragata_Ancla", bms["ancla"])
    add("Fragata_Mesa_Nav", bms["mesa"])
    add("Fragata_Reparacion", bms["rep"])
    for i in range(4):
        add(f"Fragata_Canon_0{i+1}", bm_can[i])
    for i in range(3):
        add(f"Fragata_Motor_0{i+1}", bm_mot[i])
    for i in range(2):
        add(f"Fragata_Escalera_0{i+1}", bm_esc[i], mats=mm, suav=0)
    for i in range(2):
        add(f"Fragata_Cofre_0{i+1}", bm_cof[i])
    for i in range(4):
        add(f"Fragata_Barandilla_0{i+1}", bm_bar[i], suav=0)
    piezas["Fragata_Marcas"] = h.objeto("Fragata_Marcas", bm_marca, [h.material_marca()], suavizar=0)
    nombres_neon = {"hull": "01", "tob": "02", "int": "03", "mesa": "04", "faro": "05", "timon": "06"}
    for k, num in nombres_neon.items():
        piezas[f"Fragata_Neon_{num}"] = h.objeto(f"Fragata_Neon_{num}", neon[k], h.materiales_neon(), suavizar=0)

    anclajes = {"Piloto": (0, 16.5, Z_SUP + 1.0), "MesaNav": (0, 9.0, Z_SUP), "Ancla": palanca,
                "Reparacion": (0, -9.8, 0.0)}
    for i, a in enumerate(asientos):
        anclajes[f"Canon0{i+1}"] = a
    for i, (mx, mz) in enumerate([(4.5, -1.0), (-4.5, -1.0), (0.0, 3.5)]):
        anclajes[f"Motor0{i+1}"] = (mx, Y_POPA + 3.8, mz)

    vistas = [("3/4 proa", -42, 20), ("Lateral", -90, 7), ("3/4 popa", -138, 22),
              ("Proa", 0, 10), ("Popa", 180, 12), ("Arriba", 0, 86)]
    seccion = [
        {"label": "Cubierta inferior", "az": -36, "el": 55,
         "ocultar": ["Casco", "Cubierta_Sup", "Cubierta_Inf_Techo", "Barandilla", "Canon", "Timon", "Mesa", "Neon_06"],
         "r6": [(5.0, 2.0, 0.0), (0, -9.5, 0.0)]},
        {"label": "Cubierta superior", "az": -40, "el": 40,
         "ocultar": ["Casco", "Cubierta_Inf_Suelo", "Cubierta_Inf_Paredes", "Cofre", "Reparacion", "Neon_03"],
         "r6": [(0, 14.5, Z_SUP), (6, 8, Z_SUP)]},
    ]
    h.finalizar_nave("Fragata Estelar", "nave_fragata", salida, piezas, piezas["Fragata_Casco"], anclajes, vistas,
                     bake_interior=piezas["Fragata_Cubierta_Inf_Suelo"], rapido=args.rapido, tam_tex=2048,
                     tope_tris=25000, r6_pos=(5.0, 2.0, Z_SUP), seccion=seccion)


if __name__ == "__main__":
    main()
