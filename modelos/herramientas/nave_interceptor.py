"""
Nave H1 — Interceptor: caza de reconocimiento humano, pequeño (2-3 tripulantes), cubierta abierta tipo lancha.

Silueta: perfil de lancha rápida, proa afilada, popa ancha con 2 motores. Un solo nivel abierto con barandillas,
timón hacia proa, 2 torretas (babor/estribor), ancla lateral a babor, faro de proa. Estética humana + neón cyan.

Piezas (objetos separados en el FBX):
  Interceptor_Casco, _Cubierta, _Proa, _Timon, _Ancla, _Canon_01 (babor), _Canon_02 (estribor),
  _Motor_01, _Motor_02, _Barandilla_Izq, _Barandilla_Der, _Marcas
  Neón: _Neon_01 (líneas del casco + bocas de cañón), _Neon_02 (faro), _Neon_03 (toberas), _Neon_04 (pantalla timón)

Ejes: mira a -Y (delante de Roblox). Babor = +X, estribor = -X. Cubierta transitable en z = 0.

Uso: python modelos/herramientas/nave_interceptor.py --salida modelos/nave_interceptor [--rapido]
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

# Secciones del casco (y, ancho, alto, z_centro, cuadratura). Lancha baja y afilada.
CASCO = [
    (-15.0, 0.6, 1.0, -0.6, 2.6),
    (-12.5, 3.0, 2.2, -0.9, 2.8),
    (-9.0, 6.5, 3.0, -1.2, 3.0),
    (-4.5, 10.5, 3.5, -1.4, 3.2),
    (0.0, 13.2, 3.7, -1.5, 3.4),
    (5.0, 14.0, 3.7, -1.5, 3.4),
    (9.5, 13.6, 3.6, -1.45, 3.3),
    (13.5, 12.0, 3.2, -1.4, 3.2),
]
LADOS = 22
BORDE_CUBIERTA = 0.80  # la cubierta ocupa este fracción del ancho del casco


def contorno_cubierta(y):
    """Ancho de la cubierta a lo largo de y (interpolando el casco)."""
    for (y0, w0, *_), (y1, w1, *_) in zip(CASCO, CASCO[1:]):
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0)
            return (w0 + (w1 - w0) * t) * BORDE_CUBIERTA / 2
    return 0.0


def construir_casco(bm, bmn_hull):
    anillos = [h.superelipse(y, w, ht, z, LADOS, q) for y, w, ht, z, q in CASCO]
    vs, caras = h.loft(bm, anillos, mat=h.M_CASCO)
    # Quilla oscura (panza) y franjas de panel.
    for f in caras:
        cen = f.calc_center_median()
        if f.normal.z < -0.5:
            f.material_index = h.M_OSCURO
        elif abs(f.normal.z) < 0.5 and cen.z > -0.4:
            f.material_index = h.M_PANEL  # banda de costado a la altura de la regala
    # Placas de blindaje sobre el costado (relieve real) y líneas de energía cyan.
    for s in (1, -1):
        for yy in (-6, -1, 4, 9):
            xw = None
            for (y0, w0, *_), (y1, w1, *_) in zip(CASCO, CASCO[1:]):
                if y0 <= yy <= y1:
                    t = (yy - y0) / (y1 - y0)
                    xw = (w0 + (w1 - w0) * t) / 2
            if xw:
                h.franja_neon(bmn_hull, (s * (xw + 0.02), yy, -0.55), (0.06, 3.0, 0.1), mat=0)
    # Peto de popa (tapa trasera) más oscuro.
    caras[-1].material_index = h.M_OSCURO


def construir_cubierta(bm):
    # Losa transitable: loft de un contorno interior en z=0 y z=-0.35.
    ys = [y for y, *_ in CASCO if -9 <= y <= 12.5]
    ys = [-8.5] + [y for y in ys if -8.5 < y < 12] + [12.0]
    arriba, abajo = [], []
    for y in ys:
        r = contorno_cubierta(y)
        arriba.append([bm.verts.new((x, y, 0.0)) for x in (-r, r)])
        abajo.append([bm.verts.new((x, y, -0.35)) for x in (-r, r)])
    # Suelo (cara superior) como tiras entre contornos.
    for k in range(len(ys) - 1):
        a0, a1 = arriba[k], arriba[k + 1]
        bm.faces.new((a0[0], a0[1], a1[1], a1[0])).material_index = h.M_GRIP
        b0, b1 = abajo[k], abajo[k + 1]
        bm.faces.new((b1[0], b1[1], b0[1], b0[0])).material_index = h.M_OSCURO
    # Rejilla antideslizante.
    for yy in range(-8, 12, 1):
        r = contorno_cubierta(yy)
        if r > 0.6:
            h.caja(bm, (0, yy, 0.03), (2 * r - 0.3, 0.07, 0.05), mat=h.M_OSCURO)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--rapido", action="store_true")
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    os.makedirs(salida, exist_ok=True)

    c.escena_vacia()
    mats_metal = h.materiales_metal()

    # Bmeshes por pieza.
    bm_casco = bmesh.new()
    bm_cub = bmesh.new()
    bm_proa = bmesh.new()
    bm_timon = bmesh.new()
    bm_ancla = bmesh.new()
    bm_can = [bmesh.new(), bmesh.new()]
    bm_mot = [bmesh.new(), bmesh.new()]
    bm_bar = [bmesh.new(), bmesh.new()]
    bm_marca = bmesh.new()
    # Neón agrupado.
    n_hull, n_faro, n_tob, n_timon = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()

    construir_casco(bm_casco, n_hull)
    construir_cubierta(bm_cub)

    # Proa: cuchilla afilada + carcasa del faro en la punta.
    h.caja(bm_proa, (0, -13.8, -0.2), (1.2, 2.6, 0.9), mat=h.M_PANEL, giro=Euler((math.radians(-8), 0, 0)))
    h.cilindro(bm_proa, (0, -15.0, -0.3), 0.35, 0.6, lados=10, eje="Y", mat=h.M_OSCURO)
    h.cilindro(n_faro, (0, -15.25, -0.3), 0.22, 0.2, lados=10, eje="Y", mat=0)  # faro

    # Timón hacia proa, piloto mirando -Y.
    h.consola_timon(bm_timon, n_timon, (0, -5.0, 0.0))

    # Cañones babor (+X) y estribor (-X).
    asiento_b = h.canon(bm_can[0], n_hull, (5.2, 1.0, 0.0), longitud=2.4, radio=0.24)
    asiento_e = h.canon(bm_can[1], n_hull, (-5.2, 1.0, 0.0), longitud=2.4, radio=0.24)

    # Motores en la popa (boca a +Y).
    h.tobera(bm_mot[0], n_tob, (4.0, 13.2, -1.0), radio=0.95, largo=2.4)
    h.tobera(bm_mot[1], n_tob, (-4.0, 13.2, -1.0), radio=0.95, largo=2.4)

    # Ancla lateral a babor.
    palanca = h.ancla(bm_ancla, n_hull, (6.2, -1.5, -0.3), lado=1)

    # Barandillas a lo largo del costado (de proa a popa), siguiendo el contorno de la cubierta.
    for idx, s in ((0, 1), (1, -1)):
        pts = []
        for yy in range(-8, 12, 2):
            r = contorno_cubierta(yy)
            if r > 0.6:
                pts.append(Vector((s * (r + 0.1), yy, 0.0)))
        if len(pts) >= 2:
            # Barandilla a la altura de la cintura de un R6 de 5 studs (~2,2 studs; el "0,8" del spec es en metros).
            h.barandilla(bm_bar[idx], pts, alto=2.2, grosor=0.09, paso=3.0)

    # Marcas de interacción.
    for p in [(0, -3.9, 0.0), asiento_b, asiento_e, palanca]:
        h.marca(bm_marca, p)

    # Crear objetos.
    piezas = {}
    piezas["Interceptor_Casco"] = h.objeto("Interceptor_Casco", bm_casco, mats_metal, suavizar=32)
    piezas["Interceptor_Cubierta"] = h.objeto("Interceptor_Cubierta", bm_cub, mats_metal, suavizar=18)
    piezas["Interceptor_Proa"] = h.objeto("Interceptor_Proa", bm_proa, mats_metal, suavizar=30)
    piezas["Interceptor_Timon"] = h.objeto("Interceptor_Timon", bm_timon, mats_metal, suavizar=30)
    piezas["Interceptor_Ancla"] = h.objeto("Interceptor_Ancla", bm_ancla, mats_metal, suavizar=30)
    piezas["Interceptor_Canon_01"] = h.objeto("Interceptor_Canon_01", bm_can[0], mats_metal, suavizar=30)
    piezas["Interceptor_Canon_02"] = h.objeto("Interceptor_Canon_02", bm_can[1], mats_metal, suavizar=30)
    piezas["Interceptor_Motor_01"] = h.objeto("Interceptor_Motor_01", bm_mot[0], mats_metal, suavizar=30)
    piezas["Interceptor_Motor_02"] = h.objeto("Interceptor_Motor_02", bm_mot[1], mats_metal, suavizar=30)
    piezas["Interceptor_Barandilla_Izq"] = h.objeto("Interceptor_Barandilla_Izq", bm_bar[0], mats_metal, suavizar=0)
    piezas["Interceptor_Barandilla_Der"] = h.objeto("Interceptor_Barandilla_Der", bm_bar[1], mats_metal, suavizar=0)
    piezas["Interceptor_Marcas"] = h.objeto("Interceptor_Marcas", bm_marca, [h.material_marca()], suavizar=0)
    # Neón.
    piezas["Interceptor_Neon_01"] = h.objeto("Interceptor_Neon_01", n_hull, h.materiales_neon(), suavizar=0)
    piezas["Interceptor_Neon_02"] = h.objeto("Interceptor_Neon_02", n_faro, h.materiales_neon(), suavizar=0)
    piezas["Interceptor_Neon_03"] = h.objeto("Interceptor_Neon_03", n_tob, h.materiales_neon(), suavizar=0)
    piezas["Interceptor_Neon_04"] = h.objeto("Interceptor_Neon_04", n_timon, h.materiales_neon(), suavizar=0)

    anclajes = {
        "Piloto": (0, -3.9, 1.0), "CanonBabor": asiento_b, "CanonEstribor": asiento_e,
        "Ancla": palanca, "MotorBabor": (4.0, 14.8, -1.0), "MotorEstribor": (-4.0, 14.8, -1.0),
    }
    vistas = [("3/4 proa", -40, 20), ("Lateral", -90, 6), ("3/4 popa", -140, 22),
              ("Proa", 0, 10), ("Popa", 180, 10), ("Cubierta (arriba)", 0, 86)]
    h.finalizar_nave("Interceptor", "nave_interceptor", salida, piezas,
                     piezas["Interceptor_Casco"], anclajes, vistas, rapido=args.rapido,
                     tam_tex=2048, tope_tris=15000, r6_pos=(2.6, -3.0, 0.0))


if __name__ == "__main__":
    main()
