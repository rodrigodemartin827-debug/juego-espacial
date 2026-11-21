"""
Nave H3 — Acorazado Titán: la nave insignia humana, grande (6-10 tripulantes), tres niveles.

Silueta MASIVA: casco de acorazado ancho e intimidante, torre de mando elevada hacia el centro-popa, cañón
frontal grande, y 4 propulsores enormes en cuadrado (2x2) en la popa. No se puede confundir con nada.

Niveles (interiores de 7 studs):
  * Bodega (z 0..7): 4 motores accesibles, 4 cofres, 2 puestos de reparación. Iluminación de emergencia ROJA.
  * Cubierta de artillería (z 7..14): cañón frontal y trasero, mesa de navegación central. Iluminación cyan.
  * Cubierta principal (z 14, abierta): timón en la torre de mando, 4 cañones laterales, barandillas reforzadas.
Conectados por 2 escaleras + 1 rampa. Quilla hacia z = -5, cima de la torre hacia z = 21.

Ejes: mira a -Y. Babor = +X, estribor = -X.
Uso: python modelos/herramientas/nave_acorazado.py --salida modelos/nave_acorazado [--rapido]
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

BEAM = 15.0
HALF_IN = 13.0
Y_PROA = -30.0
Y_PUNTA = -40.0
Y_POPA = 38.0
Z_QUILLA = -5.0
Z_BOD = 0.0      # suelo bodega
Z_ART = 7.0      # suelo artillería
Z_PRIN = 14.0    # cubierta principal
Z_BULW = 14.4
Z_TORRE = 21.0
CY, LARGO = (Y_PROA + Y_POPA) / 2, Y_POPA - Y_PROA


def construir_casco(bm, bmn_hull):
    mc, mo, mp = h.M_CASCO, h.M_OSCURO, h.M_PANEL
    alto = Z_BULW - Z_QUILLA
    zc = (Z_QUILLA + Z_BULW) / 2
    # Fondo / quilla.
    h.caja(bm, (0, CY, Z_QUILLA + 0.6), (BEAM * 2 - 0.5, LARGO, 1.2), mat=mo)
    h.caja(bm, (0, CY, Z_QUILLA + 0.3), (3.0, LARGO + 3, 0.6), mat=mo)
    for s in (1, -1):
        # Costado con tumblehome y blindaje por capas (3 capas de placas escalonadas).
        h.caja(bm, (s * BEAM, CY, zc), (0.9, LARGO, alto), mat=mc, giro=Euler((0, math.radians(-s * 4), 0)))
        for capa, (dz, hh) in enumerate([(-5.0, 7.0), (1.5, 7.0), (7.5, 6.0)]):
            for yy in range(int(Y_PROA) + 4, int(Y_POPA) - 2, 7):
                h.caja(bm, (s * (BEAM + 0.2 + capa * 0.06), yy, zc + dz), (0.3, 6.2, hh), mat=mp)
            h.franja_neon(bmn_hull, (s * (BEAM + 0.45), CY, zc + dz + hh / 2 - 0.3), (0.1, LARGO - 4, 0.18), mat=0)
    # Pared de popa.
    h.caja(bm, (0, Y_POPA, zc), (BEAM * 2, 0.9, alto), mat=mc)
    # Proa: planos convergentes (elevada, con morro romo).
    for s in (1, -1):
        v = [bm.verts.new(p) for p in [
            (s * BEAM, Y_PROA, Z_QUILLA + 0.6), (s * BEAM, Y_PROA, Z_BULW),
            (s * 2.0, Y_PUNTA, Z_BULW - 1.0), (s * 2.0, Y_PUNTA, Z_QUILLA + 2.5)]]
        bm.faces.new(v).material_index = mc
    # Tapa superior de proa y fondo de proa.
    bm.faces.new([bm.verts.new(p) for p in [(2, Y_PUNTA, Z_BULW - 1.0), (-2, Y_PUNTA, Z_BULW - 1.0),
                                            (-BEAM, Y_PROA, Z_BULW), (BEAM, Y_PROA, Z_BULW)]]).material_index = mp
    bm.faces.new([bm.verts.new(p) for p in [(BEAM, Y_PROA, Z_QUILLA + 0.6), (-BEAM, Y_PROA, Z_QUILLA + 0.6),
                                            (-2, Y_PUNTA, Z_QUILLA + 2.5), (2, Y_PUNTA, Z_QUILLA + 2.5)]]).material_index = mo
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)


def suelo(bm, z, mat=h.M_GRIP):
    h.caja(bm, (0, CY, z - 0.25), (HALF_IN * 2, LARGO - 4, 0.5), mat=mat)
    for yy in range(int(Y_PROA) + 4, int(Y_POPA) - 2, 2):
        h.caja(bm, (0, yy, z + 0.03), (HALF_IN * 2 - 1, 0.1, 0.05), mat=h.M_OSCURO)


def paredes_nivel(bm, bmn, z0, z1, mat_neon=0):
    """Paredes perimetrales de un nivel con tira de iluminación (color según mat_neon: 0 cyan, 1 rojo)."""
    mc = h.M_CASCO
    zc = (z0 + z1) / 2
    hh = z1 - z0
    for s in (1, -1):
        h.caja(bm, (s * HALF_IN, CY, zc), (0.5, LARGO - 4, hh), mat=mc)
        h.tuberia(bm, (s * (HALF_IN - 0.5), CY, z0 + 1.3), largo=LARGO - 8, radio=0.2, eje="Y", mat=h.M_OSCURO)
        h.franja_neon(bmn, (s * (HALF_IN - 0.3), CY, z1 - 0.6), (0.06, LARGO - 8, 0.12), mat=mat_neon)
    h.caja(bm, (0, Y_PROA + 2, zc), (HALF_IN * 2, 0.5, hh), mat=mc)
    h.caja(bm, (0, Y_POPA - 2, zc), (HALF_IN * 2, 0.5, hh), mat=mc)


def techo(bm, bmn, z, mat_neon=0):
    for yy in range(int(Y_PROA) + 4, int(Y_POPA) - 2, 5):
        h.caja(bm, (0, yy, z - 0.3), (HALF_IN * 2, 0.6, 0.4), mat=h.M_OSCURO)
    for s in (0, 1, -1):
        h.franja_neon(bmn, (s * 7, CY, z - 0.5), (0.12, LARGO - 8, 0.08), mat=mat_neon)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    os.makedirs(salida, exist_ok=True)

    c.escena_vacia()
    mm = h.materiales_metal()

    piezas = {}
    neon = {k: bmesh.new() for k in ["hull", "tob", "cyan", "rojo", "mesa", "torre", "frontal"]}

    # --- Casco ---
    bm = bmesh.new(); construir_casco(bm, neon["hull"]); piezas["Acorazado_Casco"] = h.objeto("Acorazado_Casco", bm, mm, 22)

    # --- Suelos de cada nivel ---
    bm = bmesh.new(); suelo(bm, Z_BOD); piezas["Acorazado_Bodega_Suelo"] = h.objeto("Acorazado_Bodega_Suelo", bm, mm, 16)
    bm = bmesh.new(); suelo(bm, Z_ART); piezas["Acorazado_Cubierta_Artilleria"] = h.objeto("Acorazado_Cubierta_Artilleria", bm, mm, 16)
    # Cubierta principal con hueco central (escaleras/rampa).
    bm = bmesh.new()
    h.caja(bm, (0, -8, Z_PRIN - 0.25), (HALF_IN * 2, LARGO * 0.55, 0.5), mat=h.M_GRIP)   # mitad de proa
    for s in (1, -1):
        h.caja(bm, (s * 8.5, 22, Z_PRIN - 0.25), (10, 20, 0.5), mat=h.M_GRIP)            # tiras de popa
    for yy in range(int(Y_PROA) + 4, 10, 2):
        h.caja(bm, (0, yy, Z_PRIN + 0.03), (HALF_IN * 2 - 2, 0.1, 0.05), mat=h.M_OSCURO)
    piezas["Acorazado_Cubierta_Principal"] = h.objeto("Acorazado_Cubierta_Principal", bm, mm, 16)

    # --- Paredes interiores (6) ---
    def pared(nombre, z0, z1, mat_neon, lado):
        bm = bmesh.new()
        mc, zc, hh = h.M_CASCO, (z0 + z1) / 2, z1 - z0
        if lado in ("babor", "estribor"):
            s = 1 if lado == "babor" else -1
            h.caja(bm, (s * HALF_IN, CY, zc), (0.5, LARGO - 4, hh), mat=mc)
            h.tuberia(bm, (s * (HALF_IN - 0.5), CY, z0 + 1.3), largo=LARGO - 8, radio=0.2, eje="Y", mat=h.M_OSCURO)
            h.franja_neon(neon["rojo" if mat_neon else "cyan"], (s * (HALF_IN - 0.3), CY, z1 - 0.6),
                          (0.06, LARGO - 8, 0.12), mat=mat_neon)
        else:
            h.caja(bm, (0, Y_PROA + 2, zc), (HALF_IN * 2, 0.5, hh), mat=mc)
            h.caja(bm, (0, Y_POPA - 2, zc), (HALF_IN * 2, 0.5, hh), mat=mc)
        piezas[nombre] = h.objeto(nombre, bm, mm, 16)

    pared("Acorazado_Paredes_Int_01", Z_BOD, Z_ART, 1, "babor")      # bodega (rojo)
    pared("Acorazado_Paredes_Int_02", Z_BOD, Z_ART, 1, "estribor")
    pared("Acorazado_Paredes_Int_03", Z_BOD, Z_ART, 1, "frente")
    pared("Acorazado_Paredes_Int_04", Z_ART, Z_PRIN, 0, "babor")     # artillería (cyan)
    pared("Acorazado_Paredes_Int_05", Z_ART, Z_PRIN, 0, "estribor")
    pared("Acorazado_Paredes_Int_06", Z_ART, Z_PRIN, 0, "frente")

    # --- Techos (3) ---
    bm = bmesh.new(); techo(bm, neon["rojo"], Z_ART, 1); piezas["Acorazado_Techos_01"] = h.objeto("Acorazado_Techos_01", bm, mm, 16)
    bm = bmesh.new(); techo(bm, neon["cyan"], Z_PRIN, 0); piezas["Acorazado_Techos_02"] = h.objeto("Acorazado_Techos_02", bm, mm, 16)
    # Techo de la torre.
    bm = bmesh.new(); h.caja(bm, (0, 16, Z_TORRE, ), (13, 16, 0.6), mat=h.M_PANEL); piezas["Acorazado_Techos_03"] = h.objeto("Acorazado_Techos_03", bm, mm, 16)

    # --- Torre de mando (elevada, con ventanas) ---
    bm = bmesh.new()
    h.caja(bm, (0, 16, (Z_PRIN + Z_TORRE) / 2), (12, 16, Z_TORRE - Z_PRIN), mat=h.M_CASCO)
    for s in (1, -1):  # placas
        h.caja(bm, (s * 6.1, 16, (Z_PRIN + Z_TORRE) / 2), (0.3, 13, Z_TORRE - Z_PRIN - 2), mat=h.M_PANEL)
    # Ventanas de cristal blindado (pieza neón aparte) alrededor de la parte de proa de la torre.
    for s in (1, -1):
        h.franja_neon(neon["torre"], (s * 6.05, 11, Z_PRIN + 3.5), (0.12, 6, 2.0), mat=0)
    h.franja_neon(neon["torre"], (0, 7.9, Z_PRIN + 3.5), (9, 0.12, 2.0), mat=0)
    piezas["Acorazado_Torre_Mando"] = h.objeto("Acorazado_Torre_Mando", bm, mm, 20)
    bm_v = bmesh.new()
    h.caja(bm_v, (0, 7.85, Z_PRIN + 3.5), (9, 0.1, 2.0), mat=h.M_CRISTAL)
    for s in (1, -1):
        h.caja(bm_v, (s * 6.0, 11, Z_PRIN + 3.5), (0.1, 6, 2.0), mat=h.M_CRISTAL)
    piezas["Acorazado_Ventanas_Torre"] = h.objeto("Acorazado_Ventanas_Torre", bm_v, mm, 0)

    # --- Timón en la torre ---
    bm = bmesh.new(); h.consola_timon(bm, neon["cyan"], (0, 13.5, Z_PRIN + 0.5)); piezas["Acorazado_Timon"] = h.objeto("Acorazado_Timon", bm, mm, 28)

    # --- Ancla doble (2 garras, una por lado de la proa) ---
    bm = bmesh.new()
    pal1 = h.ancla(bm, neon["hull"], (6, -24, -1.5), lado=1)
    pal2 = h.ancla(bm, neon["hull"], (-6, -24, -1.5), lado=-1)
    piezas["Acorazado_Ancla"] = h.objeto("Acorazado_Ancla", bm, mm, 26)

    # --- Cañones laterales (4) en la cubierta principal ---
    asientos = []
    for i, (sx, yy) in enumerate([(13, -6), (-13, -6), (13, 8), (-13, 8)]):
        bm = bmesh.new()
        asientos.append(h.canon(bm, neon["hull"], (sx, yy, Z_PRIN), longitud=3.4, dobles=True, radio=0.3))
        piezas[f"Acorazado_Canon_0{i+1}"] = h.objeto(f"Acorazado_Canon_0{i+1}", bm, mm, 28)
    # --- Cañón frontal grande: torreta principal en la proa de la cubierta principal (apunta a -Y) ---
    bm = bmesh.new()
    af = h.canon(bm, neon["frontal"], (0, -21, Z_PRIN), longitud=8.0, dobles=True, radio=0.55, escala=2.4)
    piezas["Acorazado_Canon_Frontal"] = h.objeto("Acorazado_Canon_Frontal", bm, mm, 28)
    # --- Cañón trasero grande: torreta en la popa de la cubierta principal (apunta a +Y) ---
    bm = bmesh.new()
    at = h.canon(bm, neon["hull"], (0, 30, Z_PRIN), longitud=7.0, dobles=True, radio=0.5, escala=2.1, dir_y=1)
    piezas["Acorazado_Canon_Trasero"] = h.objeto("Acorazado_Canon_Trasero", bm, mm, 28)

    # --- 4 motores enormes en cuadrado 2x2 (popa) ---
    for i, (mx, mz) in enumerate([(6, 1.5), (-6, 1.5), (6, 9.0), (-6, 9.0)]):
        bm = bmesh.new()
        h.tobera(bm, neon["tob"], (mx, Y_POPA + 1.0, mz), radio=1.8, largo=4.0)
        piezas[f"Acorazado_Motor_0{i+1}"] = h.objeto(f"Acorazado_Motor_0{i+1}", bm, mm, 28)

    # --- Escaleras (3) + rampa ---
    bm = bmesh.new(); h.escalera(bm, (3, 6, Z_ART), ancho=3.0, subida=7.0, fondo=7.0, pasos=10); piezas["Acorazado_Escalera_01"] = h.objeto("Acorazado_Escalera_01", bm, mm, 0)
    bm = bmesh.new(); h.escalera(bm, (-3, 6, Z_ART), ancho=3.0, subida=7.0, fondo=7.0, pasos=10); piezas["Acorazado_Escalera_02"] = h.objeto("Acorazado_Escalera_02", bm, mm, 0)
    bm = bmesh.new(); h.escalera(bm, (8, 6, Z_BOD), ancho=3.0, subida=7.0, fondo=7.0, pasos=10); piezas["Acorazado_Escalera_03"] = h.objeto("Acorazado_Escalera_03", bm, mm, 0)
    bm = bmesh.new(); h.rampa(bm, (-8, 4, Z_BOD), ancho=4.0, subida=7.0, fondo=9.0); piezas["Acorazado_Rampa"] = h.objeto("Acorazado_Rampa", bm, mm, 0)

    # --- Mesa de navegación (artillería central) ---
    bm = bmesh.new(); h.mesa_nav(bm, neon["mesa"], (0, -4, Z_ART)); piezas["Acorazado_Mesa_Nav"] = h.objeto("Acorazado_Mesa_Nav", bm, mm, 24)

    # --- 4 cofres + 2 reparaciones (bodega) ---
    for i, (cx, cy) in enumerate([(8, -6), (-8, -6), (8, 2), (-8, 2)]):
        bm = bmesh.new(); h.cofre(bm, neon["cyan"], (cx, cy, Z_BOD)); piezas[f"Acorazado_Cofre_0{i+1}"] = h.objeto(f"Acorazado_Cofre_0{i+1}", bm, mm, 20)
    for i, cx in enumerate((11, -11)):
        bm = bmesh.new(); h.reparacion(bm, neon["cyan"], (cx, -12, Z_BOD)); piezas[f"Acorazado_Reparacion_0{i+1}"] = h.objeto(f"Acorazado_Reparacion_0{i+1}", bm, mm, 20)

    # --- Barandillas reforzadas del perímetro principal (6) ---
    def baran(nombre, pts):
        bm = bmesh.new(); h.barandilla(bm, [Vector(p) for p in pts], alto=2.4, grosor=0.12, paso=4.0)
        piezas[nombre] = h.objeto(nombre, bm, mm, 0)
    baran("Acorazado_Barandilla_01", [(13, y, Z_PRIN) for y in (-18, -8, 2)])
    baran("Acorazado_Barandilla_02", [(-13, y, Z_PRIN) for y in (-18, -8, 2)])
    baran("Acorazado_Barandilla_03", [(13, y, Z_PRIN) for y in (10, 20, 30)])
    baran("Acorazado_Barandilla_04", [(-13, y, Z_PRIN) for y in (10, 20, 30)])
    baran("Acorazado_Barandilla_05", [(13, -18, Z_PRIN), (0, -19, Z_PRIN), (-13, -18, Z_PRIN)])  # proa
    baran("Acorazado_Barandilla_06", [(13, 31, Z_PRIN), (-13, 31, Z_PRIN)])  # popa

    # --- Neón (7 piezas) ---
    nombres_neon = [("hull", "01", False), ("tob", "02", False), ("cyan", "03", False), ("rojo", "04", True),
                    ("torre", "05", False), ("mesa", "06", False), ("frontal", "07", False)]
    for k, num, rojo in nombres_neon:
        mats = h.materiales_neon(con_rojo=True) if rojo else h.materiales_neon()
        piezas[f"Acorazado_Neon_{num}"] = h.objeto(f"Acorazado_Neon_{num}", neon[k], mats, suavizar=0)

    # --- Marcas de interacción ---
    bm = bmesh.new()
    for p in [(0, 15, Z_PRIN + 0.5)] + asientos + [af, at, pal1, pal2, (0, -2.5, Z_ART),
              (8, -6, Z_BOD), (-8, -6, Z_BOD), (11, -10, Z_BOD), (-11, -10, Z_BOD)]:
        h.marca(bm, p)
    piezas["Acorazado_Marcas"] = h.objeto("Acorazado_Marcas", bm, [h.material_marca()], suavizar=0)

    anclajes = {"Piloto": (0, 15, Z_PRIN + 0.5), "CanonFrontal": af, "CanonTrasero": at,
                "AnclaBabor": pal1, "AnclaEstribor": pal2, "MesaNav": (0, -2.5, Z_ART)}
    for i, a in enumerate(asientos):
        anclajes[f"Canon0{i+1}"] = a
    for i, (mx, mz) in enumerate([(6, 1.5), (-6, 1.5), (6, 9.0), (-6, 9.0)]):
        anclajes[f"Motor0{i+1}"] = (mx, Y_POPA + 5.0, mz)

    vistas = [("3/4 proa", -42, 18), ("Lateral", -90, 8), ("3/4 popa", -138, 20),
              ("Proa", 0, 10), ("Popa", 180, 12), ("Arriba", 0, 86)]
    seccion = [
        {"label": "Bodega (nivel 3)", "az": -36, "el": 52,
         "ocultar": ["Casco", "Cubierta_Principal", "Cubierta_Artilleria", "Techos_01", "Techos_02", "Paredes_Int_04",
                     "Paredes_Int_05", "Paredes_Int_06", "Torre", "Ventanas", "Barandilla", "Canon", "Timon",
                     "Mesa", "Neon_03", "Neon_05", "Escalera_01", "Escalera_02"],
         "r6": [(8, -6, Z_BOD), (0, -12, Z_BOD)]},
        {"label": "Artillería (nivel 2)", "az": -40, "el": 44,
         "ocultar": ["Casco", "Cubierta_Principal", "Techos_02", "Paredes_Int_04", "Paredes_Int_05", "Paredes_Int_06",
                     "Torre", "Ventanas", "Barandilla", "Canon", "Timon", "Bodega", "Cofre", "Reparacion",
                     "Paredes_Int_01", "Paredes_Int_02", "Paredes_Int_03", "Neon_04", "Escalera_03", "Rampa"],
         "r6": [(0, -2.5, Z_ART), (6, 4, Z_ART)]},
        {"label": "Cubierta principal (nivel 1)", "az": -44, "el": 34,
         "ocultar": ["Casco", "Cubierta_Artilleria", "Bodega", "Paredes_Int", "Techos_01", "Cofre", "Reparacion",
                     "Mesa", "Neon_04", "Escalera", "Rampa"],
         "r6": [(0, 15, Z_PRIN), (13, -6, Z_PRIN)]},
    ]
    h.finalizar_nave("Acorazado Titán", "nave_acorazado", salida, piezas, piezas["Acorazado_Casco"], anclajes, vistas,
                     bake_interior=piezas["Acorazado_Bodega_Suelo"], rapido=args.rapido, tam_tex=2048,
                     tope_tris=40000, r6_pos=(0, 15, Z_PRIN), seccion=seccion)


if __name__ == "__main__":
    main()
