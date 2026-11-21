"""
Kit modular de construcción de naves humanas: 30 piezas, cada una en su propio FBX.

Grid de 2x2x2 studs. Cada pieza lleva:
  * objeto de metal con la estética humana (paneles, remaches, neón aparte),
  * objeto <Pieza>_Neon si tiene energía (Material = Neon en Studio),
  * objeto <Pieza>_Conectores: cilindros de 0,2 studs en las caras que encajan en el grid
    (el director los usa para posicionar los snaps),
  * objeto <Pieza>_Marca para las estaciones interactivas (dónde se pone el ProximityPrompt).

Comparte un atlas PBR tileable (mod_atlas_*.png) para todas las piezas.

Uso:
    python modelos/herramientas/piezas_modulares.py --salida modelos/piezas_modulares [--rapido]
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
import texturas_pbr  # noqa: E402

M = h  # alias corto


# --------------------------------------------------------------------------------------------------------------
# Utilidades de pieza
# --------------------------------------------------------------------------------------------------------------


def nueva():
    return {"metal": bmesh.new(), "neon": bmesh.new(), "con": bmesh.new(), "marca": bmesh.new()}


def conectores(bms, caras):
    """caras: lista de (centro, ) donde encaja el grid. Pone un cilindro de 0,2 studs orientado a esa cara."""
    for p in caras:
        M.conector(bms["con"], p)


def rejilla_suelo(bm, cx, cy, sx, sy, z_top, mat=M.M_GRIP):
    """Dibuja una rejilla antideslizante fina sobre una placa de suelo (listones cruzados)."""
    for i in range(1, int(sx)):
        M.caja(bm, (cx - sx / 2 + i, cy, z_top + 0.02), (0.06, sy * 0.92, 0.05), mat=M.M_OSCURO)
    for j in range(1, int(sy)):
        M.caja(bm, (cx, cy - sy / 2 + j, z_top + 0.02), (sx * 0.92, 0.06, 0.05), mat=M.M_OSCURO)


# --------------------------------------------------------------------------------------------------------------
# CATEGORÍA 1 — Casco / Estructura
# --------------------------------------------------------------------------------------------------------------


def suelo_basico(b, reforzado=False):
    # Losa de 0,5 studs con la cara transitable en z=0 (spans -0.5..0), rejilla antideslizante justo encima.
    M.caja(b["metal"], (0, 0, -0.25), (4, 4, 0.5), mat=M.M_PANEL if reforzado else M.M_CASCO)
    # Juntas en cruz (rehundidas) para marcar 4 cuadrantes.
    M.caja(b["metal"], (0, 0, -0.1), (4, 0.12, 0.12), mat=M.M_OSCURO)
    M.caja(b["metal"], (0, 0, -0.1), (0.12, 4, 0.12), mat=M.M_OSCURO)
    rejilla_suelo(b["metal"], 0, 0, 4, 4, -0.5)
    if reforzado:
        for dx in (-1, 1):
            for dy in (-1, 1):
                M.placa(b["metal"], (dx * 1.0, dy * 1.0, -0.05), (1.5, 1.5, 0.12), mat=M.M_CASCO, borde=0.2,
                        remaches=True)
    conectores(b, [(0, 0, -0.5), (0, 0, 0.05), (-2, 0, -0.25), (2, 0, -0.25), (0, -2, -0.25), (0, 2, -0.25)])


def pared(b, ventana=False):
    # Placa plana (4×4, 0,5 de grueso) puesta en vertical: el relieve mira a -Y.
    M.placa(b["metal"], (0, 0, 2), (4, 4, 0.5), mat=M.M_CASCO, borde=0.4, remaches=not ventana,
            giro=Euler((math.radians(90), 0, 0)))
    if ventana:
        # Hueco con cristal (neón cyan tenue como marco) + cristal real con grosor.
        M.caja(b["metal"], (0, 0, 2.2), (2.4, 0.52, 2.0), mat=M.M_OSCURO)
        M.caja(b["metal"], (0, 0, 2.2), (2.0, 0.2, 1.6), mat=M.M_CRISTAL)
        M.franja_neon(b["neon"], (0, 0.22, 2.2), (2.2, 0.04, 0.08), mat=0)
        M.franja_neon(b["neon"], (0, 0.22, 3.1), (2.2, 0.04, 0.08), mat=0)
    conectores(b, [(-2, 0, 2), (2, 0, 2), (0, 0, 0.1), (0, 0, 3.9)])


def pared_angular(b):
    # Pared vertical (placa plana puesta en pie) y luego girada 45° en planta, para proas aerodinámicas.
    M.placa(b["metal"], (0, 0, 2), (5.6, 4, 0.5), mat=M.M_CASCO, borde=0.4, remaches=True,
            giro=Euler((math.radians(90), math.radians(45), 0)))
    conectores(b, [(-2, -2, 2), (2, 2, 2), (0, 0, 0.1)])


def techo(b):
    # Losa de 0,5 con la cara inferior en z=0 (spans 0..0.5); iluminación interior pegada por debajo.
    M.caja(b["metal"], (0, 0, 0.25), (4, 4, 0.5), mat=M.M_CASCO)
    for dx in (-1, 1):
        for dy in (-1, 1):
            M.placa(b["metal"], (dx, dy, 0.5), (1.5, 1.5, 0.1), mat=M.M_PANEL, borde=0.2, remaches=True)
    M.franja_neon(b["neon"], (0, 0, -0.04), (3.2, 0.1, 0.06), mat=0)
    M.franja_neon(b["neon"], (0, 0, -0.04), (0.1, 3.2, 0.06), mat=0)
    conectores(b, [(0, 0, 0.55), (0, 0, -0.05), (-2, 0, 0.25), (2, 0, 0.25)])


def proa(b):
    # Punta triangular blindada que cierra el frente (apunta a -Y).
    M.cuna(b["metal"], (0, 0, 0), (4, 4, 0.1), mat=M.M_CASCO)  # base
    # Cuerpo: dos planos inclinados que convergen en el morro.
    bm = b["metal"]
    v = [bm.verts.new(p) for p in [(-2, 2, 0), (2, 2, 0), (2, 2, 3.0), (-2, 2, 3.0), (0, -2, 0.4), (0, -2, 1.6)]]
    for cc in [(v[0], v[4], v[5], v[3]), (v[4], v[1], v[2], v[5]), (v[3], v[5], v[2]),
               (v[0], v[1], v[4]), (v[0], v[3], v[2], v[1])]:
        try:
            bm.faces.new(cc)
        except ValueError:
            pass
    M.franja_neon(b["neon"], (0, -1.6, 1.0), (0.1, 1.2, 0.1), mat=0)
    conectores(b, [(0, 2, 1.5), (-2, 0.5, 1.2), (2, 0.5, 1.2), (0, 0, -0.05)])


def popa(b):
    # Bloque trasero con 2 huecos cilíndricos para encajar motores.
    M.placa(b["metal"], (0, -0.5, 1.5), (4, 3, 0.4), mat=M.M_CASCO, borde=0.3,
            giro=Euler((math.radians(90), 0, 0)))  # pared frontal vertical
    M.caja(b["metal"], (0, 1.2, 1.5), (4, 1.6, 3), mat=M.M_CASCO)
    for s in (-1, 1):
        M.cilindro(b["metal"], (s * 1.0, 1.0, 1.5), 0.95, 2.2, lados=16, eje="Y", mat=M.M_OSCURO)
        M.cilindro(b["metal"], (s * 1.0, 0.2, 1.5), 0.95, 0.3, lados=16, eje="Y", mat=M.M_PANEL)
    conectores(b, [(0, 2, 1.5), (-2, 1.2, 1.5), (2, 1.2, 1.5), (0, 0, 0.1)])


def esquina(b):
    # Une 2 paredes a 90°, redondeada por fuera.
    M.cilindro(b["metal"], (0, 0, 2), 1.0, 4, lados=10, mat=M.M_CASCO)
    M.caja(b["metal"], (0.5, -0.5, 2), (1.0, 1.0, 4), mat=M.M_CASCO)  # relleno interior
    conectores(b, [(-1, 0, 2), (0, 1, 2), (0, 0, 0.1), (0, 0, 3.9)])


def escalera_mod(b):
    M.escalera(b["metal"], (0, -2, 0), ancho=3.0, subida=4.0, fondo=4.0, pasos=7)
    conectores(b, [(0, -2, 0), (0, 2, 4), (0, 0, 2)])
    M.marca(b["marca"], (0, -1.6, 0.2))


def rampa_mod(b):
    M.rampa(b["metal"], (0, -2, 0), ancho=4.0, subida=4.0, fondo=5.0)
    conectores(b, [(0, -2, 0), (0, 3, 4)])


def barandilla_mod(b):
    M.barandilla(b["metal"], [Vector((-2, 0, 0)), Vector((2, 0, 0))], alto=1.0, grosor=0.1)
    conectores(b, [(-2, 0, 0), (2, 0, 0)])


# --------------------------------------------------------------------------------------------------------------
# CATEGORÍA 2 — Propulsión
# --------------------------------------------------------------------------------------------------------------


def motor(b, radio, largo, toberas=1):
    sep = radio * 0.55 if toberas > 1 else 0
    for i in range(toberas):
        ox = (i - (toberas - 1) / 2) * sep * 2
        M.tobera(b["metal"], b["neon"], (ox, 0, 0), radio=radio / (1.5 if toberas > 1 else 1), largo=largo)
    # Carcasa de montaje por delante (hacia -Y).
    M.caja(b["metal"], (0, -largo * 0.9, 0), (radio * 2.2, 0.6, radio * 2.0), mat=M.M_CASCO)
    conectores(b, [(0, -largo, 0)])


def propulsor_lateral(b):
    M.cilindro(b["metal"], (0, 0, 0), 0.8, 1.6, lados=14, eje="X", mat=M.M_CASCO)
    M.cilindro(b["neon"], (1.0, 0, 0), 0.5, 0.3, lados=12, eje="X", mat=0, radio2=0.25)
    M.cilindro(b["neon"], (-1.0, 0, 0), 0.5, 0.3, lados=12, eje="X", mat=0, radio2=0.25)
    conectores(b, [(0, 1, 0), (0, -1, 0)])


# --------------------------------------------------------------------------------------------------------------
# CATEGORÍA 3 — Armas
# --------------------------------------------------------------------------------------------------------------


def canon_ligero(b):
    seat = M.canon(b["metal"], b["neon"], (0, 0, 0), longitud=2.4, dobles=False, radio=0.24)
    conectores(b, [(0, 0, -0.05)])
    M.marca(b["marca"], seat)


def canon_pesado(b):
    seat = M.canon(b["metal"], b["neon"], (0, 0, 0), longitud=3.2, dobles=True, radio=0.26)
    conectores(b, [(0, 0, -0.05)])
    M.marca(b["marca"], seat)


def lanzamisiles(b):
    # Rack 2x2 de tubos apuntando a -Y (no gira).
    M.caja(b["metal"], (0, 0.4, 1.2), (2.0, 1.4, 1.6), mat=M.M_CASCO)
    for dx in (-0.55, 0.55):
        for dz in (0.75, 1.65):
            M.cilindro(b["metal"], (dx, -0.4, dz), 0.32, 1.4, lados=12, eje="Y", mat=M.M_OSCURO)
            M.cilindro(b["neon"], (dx, -1.15, dz), 0.2, 0.12, lados=8, eje="Y", mat=0)
    conectores(b, [(0, 0.8, 0.1)])
    M.marca(b["marca"], (0, 1.4, 0.1))


# --------------------------------------------------------------------------------------------------------------
# CATEGORÍA 4 — Estaciones interactivas
# --------------------------------------------------------------------------------------------------------------


def timon_mod(b):
    M.consola_timon(b["metal"], b["neon"], (0, 0.2, 0))
    conectores(b, [(0, 0.2, -0.05)])
    M.marca(b["marca"], (0, 1.0, 0.1))


def ancla_mod(b):
    seat = M.ancla(b["metal"], b["neon"], (0, 0, 0.4), lado=1)
    conectores(b, [(0, 0, 0.0)])
    M.marca(b["marca"], seat)


def mesa_nav_mod(b):
    M.mesa_nav(b["metal"], b["neon"], (0, 0, 0))
    conectores(b, [(0, 0, -0.05)])
    M.marca(b["marca"], (0, -1.6, 0.1))


def reparacion_mod(b):
    M.reparacion(b["metal"], b["neon"], (0, 0.6, 0))
    conectores(b, [(0, 0.9, 0.1)])
    M.marca(b["marca"], (0, -0.6, 0.1))


def cofre_mod(b):
    M.cofre(b["metal"], b["neon"], (0, 0, 0), tam=(2.0, 2.0, 2.0))
    conectores(b, [(0, 0, 0.0)])
    M.marca(b["marca"], (0, -1.4, 0.1))


def cama_mod(b):
    M.cama(b["metal"], b["neon"], (0, 0, 0))
    conectores(b, [(0, 0, 0.0)])
    M.marca(b["marca"], (0, -2.4, 0.1))


# --------------------------------------------------------------------------------------------------------------
# CATEGORÍA 5 — Decoración
# --------------------------------------------------------------------------------------------------------------


def lampara_mod(b):
    M.lampara(b["metal"], b["neon"], (0, 0, 0))
    conectores(b, [(0, 0, 0.12)])


def bandera_mod(b):
    M.bandera(b["metal"], b["neon"], (0, 0, 0))
    conectores(b, [(0, 0, 0.0)])


def panel_deco_mod(b):
    M.panel_deco(b["metal"], b["neon"], (0, 0, 0))
    conectores(b, [(0, 0.2, 0), (0, 0.2, 0)])


def tuberia_mod(b):
    M.tuberia(b["metal"], (0, 0, 0), largo=4.0, radio=0.15, eje="Y")
    conectores(b, [(0, -2, 0), (0, 2, 0)])


def antena_mod(b):
    M.antena(b["metal"], b["neon"], (0, 0, 0))
    conectores(b, [(0, 0, 0.0)])


# --------------------------------------------------------------------------------------------------------------
# Registro de piezas (archivo, función, nombre del objeto, tope de tris)
# --------------------------------------------------------------------------------------------------------------

PIEZAS = [
    # Casco / estructura (<=800)
    ("mod_suelo_basico", lambda b: suelo_basico(b, False), "Suelo_basico", 800),
    ("mod_suelo_reforzado", lambda b: suelo_basico(b, True), "Suelo_reforzado", 800),
    ("mod_pared", lambda b: pared(b, False), "Pared", 800),
    ("mod_pared_ventana", lambda b: pared(b, True), "Pared_ventana", 800),
    ("mod_pared_angular", pared_angular, "Pared_angular", 800),
    ("mod_techo", techo, "Techo", 800),
    ("mod_proa", proa, "Proa", 800),
    ("mod_popa", popa, "Popa", 800),
    ("mod_esquina", esquina, "Esquina", 800),
    ("mod_escalera", escalera_mod, "Escalera", 800),
    ("mod_rampa", rampa_mod, "Rampa", 800),
    ("mod_barandilla", barandilla_mod, "Barandilla", 800),
    # Propulsión (<=1500)
    ("mod_motor_peq", lambda b: motor(b, 0.9, 1.6, 1), "Motor_pequeno", 1500),
    ("mod_motor_med", lambda b: motor(b, 1.3, 2.6, 1), "Motor_mediano", 1500),
    ("mod_motor_grande", lambda b: motor(b, 1.5, 3.6, 2), "Motor_grande", 1500),
    ("mod_propulsor_lat", propulsor_lateral, "Propulsor_lateral", 1500),
    # Armas (<=2000)
    ("mod_canon_ligero", canon_ligero, "Canon_ligero", 2000),
    ("mod_canon_pesado", canon_pesado, "Canon_pesado", 2000),
    ("mod_lanzamisiles", lanzamisiles, "Lanzamisiles", 2000),
    # Estaciones (<=1500)
    ("mod_timon", timon_mod, "Timon", 1500),
    ("mod_ancla", ancla_mod, "Ancla", 1500),
    ("mod_mesa_nav", mesa_nav_mod, "Mesa_navegacion", 1500),
    ("mod_reparacion", reparacion_mod, "Estacion_reparacion", 1500),
    ("mod_cofre", cofre_mod, "Cofre", 1500),
    ("mod_cama", cama_mod, "Cama", 1500),
    # Decoración (<=500)
    ("mod_lampara", lampara_mod, "Lampara", 500),
    ("mod_bandera", bandera_mod, "Bandera", 500),
    ("mod_panel_deco", panel_deco_mod, "Panel_deco", 500),
    ("mod_tuberia", tuberia_mod, "Tuberia", 500),
    ("mod_antena", antena_mod, "Antena", 500),
]


def construir_pieza(archivo, fn, nombre):
    b = nueva()
    fn(b)
    objs = []
    mats_metal = M.materiales_metal()
    metal = M.objeto(nombre, b["metal"], mats_metal, suavizar=35)
    # UV por proyección inteligente: el atlas PBR tileable se puede aplicar en Studio (SurfaceAppearance).
    c.desplegar_uv(metal, margen=0.02)
    objs.append(metal)
    if len(b["neon"].verts) > 0:
        neon = M.objeto(f"{nombre}_Neon", b["neon"], M.materiales_neon(), suavizar=0)
        objs.append(neon)
    else:
        b["neon"].free()
    if len(b["con"].verts) > 0:
        con = M.objeto(f"{nombre}_Conectores", b["con"], [M.material_marca()], suavizar=0)
        objs.append(con)
    else:
        b["con"].free()
    if len(b["marca"].verts) > 0:
        marca = M.objeto(f"{nombre}_Marca", b["marca"], [M.material_marca()], suavizar=0)
        objs.append(marca)
    else:
        b["marca"].free()
    return metal, objs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--solo", default=None, help="construir solo las piezas cuyo archivo contenga este texto")
    args = ap.parse_args()
    salida = os.path.abspath(args.salida)
    os.makedirs(os.path.join(salida, "texturas"), exist_ok=True)
    os.makedirs(os.path.join(salida, "render"), exist_ok=True)

    # Atlas compartido.
    tam_atlas = 512 if args.rapido else 2048
    texturas_pbr.generar(os.path.join(salida, "texturas", "mod_atlas"), tam=tam_atlas, celdas=8)

    piezas = [p for p in PIEZAS if not args.solo or args.solo in p[0]]
    resumen = []
    miniaturas = []
    for archivo, fn, nombre, tope in piezas:
        c.escena_vacia()
        metal, objs = construir_pieza(archivo, fn, nombre)
        tris = M.tris_totales(objs)
        mn, mx = c.caja_limite(objs)
        dim = (mx - mn) / c.ESTUDIO
        estado = "OK" if tris <= tope else f"¡{tris}>{tope}!"
        resumen.append((archivo, nombre, tris, tope, dim, estado))
        c.exportar_fbx(os.path.join(salida, f"{archivo}.fbx"), objs, incrustar_texturas=False)
        # Miniatura 3/4.
        c.preparar_estudio(z_suelo=mn.z - 0.1 * c.ESTUDIO)
        vistas = [("", -38, 22)]
        r = c.renderizar_vistas(objs, os.path.join(salida, "_tmp"), vistas, tam=240 if args.rapido else 360,
                                muestras=12 if args.rapido else 40, con_malla=False, prefijo=archivo + "_")
        miniaturas.append((f"{nombre}\n{tris} tri · {dim.x:.0f}×{dim.y:.0f}×{dim.z:.0f}", r[0][1]))
        c.eliminar_estudio()

    # Guardar .blend con todas las piezas (reconstruidas juntas, separadas en el espacio para inspección).
    # Hoja de contactos por categorías.
    etiquetas = {"Casco/Estructura": miniaturas[0:12], "Propulsión": miniaturas[12:16],
                 "Armas": miniaturas[16:19], "Estaciones": miniaturas[19:25], "Decoración": miniaturas[25:30]}
    filas = []
    etfilas = []
    for cat, items in etiquetas.items():
        if not items:
            continue
        for i in range(0, len(items), 6):
            filas.append(items[i:i + 6])
            etfilas.append(cat if i == 0 else "")
    if not args.solo:
        c.montar_hoja(filas, os.path.join(salida, "render", "piezas_modulares.png"),
                      "Kit modular humano — 30 piezas", columnas=6, etiquetas_fila=etfilas,
                      notas=["Grid 2×2×2 studs · atlas PBR compartido · neón y conectores en objetos aparte"])

    print("\n=== RESUMEN PIEZAS MODULARES ===")
    for archivo, nombre, tris, tope, dim, estado in resumen:
        print(f"  {archivo:22s} {tris:5d}/{tope} tri  {dim.x:4.1f}×{dim.y:4.1f}×{dim.z:4.1f}  {estado}")
    malas = [r for r in resumen if r[5] != "OK"]
    print(f"  {len(resumen)} piezas, {len(malas)} sobre el tope de tris")


if __name__ == "__main__":
    main()
