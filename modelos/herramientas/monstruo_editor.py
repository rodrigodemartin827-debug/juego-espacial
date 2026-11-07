"""
Piezas 3D del editor de monstruos: cuernos (en la cabeza) y deformaciones (en el cuerpo).

Uso (desde la raíz del repositorio):
    blender -b --python modelos/herramientas/monstruo_editor.py -- --salida modelos/personaje_monstruo [--rapido]

Sale en <salida>:
    roblox/Cuernos.fbx, roblox/Deformaciones.fbx   una malla por objeto, «<Categoria>_<Id>__<Parte>__<Rol>»
    piezas.json                                    parte, centro, tamaño y rol de cada pieza (como el del humano)
    hoja_contactos_<ronda>.png                     renders de todas las piezas sobre un maniquí

Roles (de qué color se pinta cada pieza en el juego): Cuerno (el color de cuernos que elige el jugador), Hueso (el color
de detalles) y Piel (la piel del monstruo, para bultos del propio cuerpo).
Mismas medidas y ejes que el humano (R6 en studs, ejes de Roblox, origen en el centro del torso): se reutilizan las
herramientas de personaje_humano.py. Menos de 1.500 triángulos cada elemento.
"""

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun as c  # noqa: E402
import personaje_humano as ph  # noqa: E402
from personaje_humano import Malla, PARTES, centro_parte, cono  # noqa: E402

E = c.ESTUDIO

MUESTRA = {
    "Cuerno": "#D8D2C2",
    "Hueso": "#C9C3B0",
    "Piel": "#7A8A8F",
    "Oscuro": "#1A1D22",
    "Neon": "#FF3A3A",
}

CAB = Vector(PARTES["Cabeza"][0])


# ==============================================================================================================
# Cuernos (en la cabeza)
# ==============================================================================================================


def cuernos_curvos(mallas):
    m = mallas("Cabeza", "Cuerno")
    for lado in (-1, 1):
        pts = [CAB + Vector(p) for p in ((lado * 0.35, 0.55, -0.05), (lado * 0.55, 0.85, -0.05), (lado * 0.62, 1.2, 0.0),
                                          (lado * 0.5, 1.5, 0.05), (lado * 0.3, 1.72, 0.1))]
        m.tubo(pts, [0.15, 0.13, 0.1, 0.065, 0.015], n=7)


def cuernos_rectos(mallas):
    m = mallas("Cabeza", "Cuerno")
    for lado in (-1, 1):
        cono(m, CAB + Vector((lado * 0.38, 0.56, 0)), Vector((lado * 0.28, 1, -0.05)), 1.15, 0.17, n=7)


def cuernos_carnero(mallas):
    m = mallas("Cabeza", "Cuerno")
    for lado in (-1, 1):
        pts, radios = [], []
        for i in range(17):
            t = i / 16
            a = t * math.pi * 3.4
            r = 0.52 * (1 - t * 0.72)
            pts.append(CAB + Vector((lado * (0.62 + 0.14 * t), 0.38 + r * math.sin(a), 0.05 - r * math.cos(a) + 0.3)))
            radios.append(0.16 * (1 - t) + 0.025)
        m.tubo(pts, radios, n=7)


def cuernos_astas(mallas):
    m = mallas("Cabeza", "Cuerno")
    for lado in (-1, 1):
        tronco = [CAB + Vector(p) for p in ((lado * 0.3, 0.55, 0.1), (lado * 0.45, 0.95, 0.1), (lado * 0.62, 1.35, 0.05),
                                             (lado * 0.6, 1.75, 0.0))]
        m.tubo(tronco, [0.09, 0.08, 0.065, 0.03], n=6)
        for y, dx, dz, largo in ((0.85, 0.5, -0.2, 0.55), (1.2, 0.6, 0.25, 0.6), (1.5, 0.45, -0.25, 0.45)):
            base = CAB + Vector((lado * (0.4 + (y - 0.85) * 0.3), y, 0.1))
            cono(m, base, Vector((lado * dx, 0.7, dz)), largo, 0.06, n=5)


def cuernos_corona(mallas):
    m = mallas("Cabeza", "Cuerno")
    n = 8
    for i in range(n):
        a = 2 * math.pi * i / n
        base = CAB + Vector((0.5 * math.sin(a), 0.6, 0.5 * math.cos(a)))
        alto = 0.7 if i % 2 == 0 else 0.45
        cono(m, base, Vector((0.25 * math.sin(a), 1, 0.25 * math.cos(a))), alto, 0.1, n=6)
    ph.arco_cabeza(m, -math.pi, math.pi, 0.5, 0.66, 0.0, 0.06, n=24)


def cuernos_unicornio(mallas):
    m = mallas("Cabeza", "Cuerno")
    cono(m, CAB + Vector((0, 0.5, -0.45)), Vector((0, 1, -0.55)), 1.35, 0.15, n=8)
    for k in range(5):
        y = 0.7 + 0.2 * k
        m.tubo([CAB + Vector((-0.1 + 0.02 * k, y, -0.5 - 0.18 * (y - 0.5))), CAB + Vector((0.1 - 0.02 * k, y + 0.07,
                                                                                         -0.5 - 0.18 * (y - 0.5)))],
               [0.045, 0.045], n=5)


def cuernos_diablillo(mallas):
    m = mallas("Cabeza", "Cuerno")
    for lado in (-1, 1):
        cono(m, CAB + Vector((lado * 0.4, 0.55, -0.1)), Vector((lado * 0.4, 1, -0.2)), 0.42, 0.13, n=6)


def cuernos_retorcidos(mallas):
    m = mallas("Cabeza", "Cuerno")
    for x, z, alto in ((-0.45, 0.0, 1.2), (0.0, 0.3, 1.5), (0.45, 0.0, 1.2)):
        pts, radios = [], []
        for i in range(11):
            t = i / 10
            pts.append(CAB + Vector((x + 0.12 * math.sin(t * 9), 0.55 + alto * t, z + 0.12 * math.cos(t * 9))))
            radios.append(0.13 * (1 - t) + 0.015)
        m.tubo(pts, radios, n=6)


CUERNOS = [
    ("Curvos", cuernos_curvos), ("Rectos", cuernos_rectos), ("Carnero", cuernos_carnero), ("Astas", cuernos_astas),
    ("Corona", cuernos_corona), ("Unicornio", cuernos_unicornio), ("Diablillo", cuernos_diablillo),
    ("Retorcidos", cuernos_retorcidos),
]


# ==============================================================================================================
# Deformaciones (en el cuerpo)
# ==============================================================================================================


def def_espinas(mallas):
    m = mallas("Torso", "Hueso")
    for i, y in enumerate((0.8, 0.35, -0.1, -0.55, -0.9)):
        largo = 0.7 - 0.07 * i
        cono(m, centro_parte("Torso", (0, y, 0.5)), Vector((0, 0.25, 1)), largo, 0.14, n=6)


def def_vertebras(mallas):
    m = mallas("Torso", "Hueso")
    for i in range(7):
        y = 0.95 - i * 0.3
        m.esfera(centro_parte("Torso", (0, y, 0.56)), (0.17, 0.12, 0.14), u=8, v=5)
    m.esfera(centro_parte("Torso", (0, 1.15, 0.5)), (0.15, 0.12, 0.14), u=8, v=5)


def def_costillas(mallas):
    m = mallas("Torso", "Hueso")
    for i in range(5):
        y = 0.75 - i * 0.38
        for lado in (-1, 1):
            pts = [centro_parte("Torso", p) for p in ((lado * 0.05, y, -0.55), (lado * 0.5, y - 0.02, -0.6),
                                                       (lado * 0.9, y - 0.08, -0.4), (lado * 1.02, y - 0.1, -0.05))]
            m.tubo(pts, [0.05, 0.055, 0.05, 0.04], n=5)
    m.caja(centro_parte("Torso", (0, 0.05, -0.6)), (0.1, 1.9, 0.06), bisel=0.02)


def def_hombros(mallas):
    for lado, parte in ((-1, "BrazoI"), (1, "BrazoD")):
        m = mallas(parte, "Hueso")
        cono(m, centro_parte(parte, (lado * 0.35, 0.85, 0)), Vector((lado * 0.5, 1, 0)), 0.75, 0.2, n=7)
        cono(m, centro_parte(parte, (lado * 0.3, 0.7, -0.35)), Vector((lado * 0.4, 0.5, -1)), 0.5, 0.13, n=6)
        cono(m, centro_parte(parte, (lado * 0.3, 0.7, 0.35)), Vector((lado * 0.4, 0.5, 1)), 0.5, 0.13, n=6)


def def_brazo_hinchado(mallas):
    m = mallas("BrazoD", "Piel")
    m.esfera(centro_parte("BrazoD", (0.15, 0.0, 0)), (0.95, 1.25, 0.95), u=14, v=10)
    m.esfera(centro_parte("BrazoD", (0.35, -0.7, -0.2)), (0.5, 0.45, 0.5), u=10, v=7)
    mallas("BrazoD", "Hueso").esfera(centro_parte("BrazoD", (0.5, 0.35, -0.6)), (0.14, 0.14, 0.1), u=8, v=5)


def def_joroba(mallas):
    m = mallas("Torso", "Piel")
    m.esfera(centro_parte("Torso", (0, 0.6, 0.75)), (1.05, 0.85, 0.7), u=14, v=9)
    m.esfera(centro_parte("Torso", (0.35, 0.2, 0.9)), (0.4, 0.4, 0.35), u=8, v=6)


def def_garras(mallas):
    for lado, parte in ((-1, "BrazoI"), (1, "BrazoD")):
        m = mallas(parte, "Hueso")
        for k, dx in enumerate((-0.32, -0.1, 0.12, 0.34)):
            cono(m, centro_parte(parte, (dx, -1.0, -0.15 + 0.1 * (k % 2))), Vector((dx * 0.4, -1, -0.15)), 0.95, 0.07, n=5)


def def_placas(mallas):
    for parte in ("BrazoI", "BrazoD"):
        m = mallas(parte, "Hueso")
        m.caja(centro_parte(parte, (0, -0.35, -0.5)), (0.75, 0.9, 0.12), bisel=0.05)
        m.caja(centro_parte(parte, (0, -0.35, 0.5)), (0.75, 0.9, 0.12), bisel=0.05)
    for parte in ("PiernaI", "PiernaD"):
        m = mallas(parte, "Hueso")
        m.caja(centro_parte(parte, (0, 0.2, -0.54)), (0.8, 1.2, 0.12), bisel=0.06)
        m.caja(centro_parte(parte, (0, -0.75, -0.56)), (0.9, 0.35, 0.16), bisel=0.05)
    mallas("Torso", "Hueso").caja(centro_parte("Torso", (0, 0.3, -0.56)), (1.6, 1.0, 0.14), bisel=0.08)


DEFORMACIONES = [
    ("Espinas", def_espinas), ("Vertebras", def_vertebras), ("Costillas", def_costillas), ("Hombros", def_hombros),
    ("BrazoHinchado", def_brazo_hinchado), ("Joroba", def_joroba), ("Garras", def_garras), ("Placas", def_placas),
]


# ==============================================================================================================
# Construcción, exportación y hoja de contactos
# ==============================================================================================================


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--sin_render", action="store_true")
    args = ap.parse_args(argv)
    salida = os.path.abspath(args.salida)
    os.makedirs(os.path.join(salida, "roblox"), exist_ok=True)

    c.escena_vacia()
    materiales = {}
    for rol, hexa in MUESTRA.items():
        materiales[rol] = c.material("m_" + rol, c.srgb(hexa), rugosidad=0.5,
                                     emision=c.srgb(hexa) if rol == "Neon" else None,
                                     fuerza_emision=4.0 if rol == "Neon" else 0.0)
    ph_mat = {k: materiales[k] for k in materiales}
    # construir_categoria del humano pide materiales por rol: se le dan los del monstruo.
    grupos = {
        "Cuernos": ph.construir_categoria("Cuerno", CUERNOS, ph_mat),
        "Deformaciones": ph.construir_categoria("Deformacion", DEFORMACIONES, ph_mat),
    }

    piezas, por_elemento = {}, {}
    for archivo, objetos in grupos.items():
        c.exportar_fbx(os.path.join(salida, "roblox", archivo + ".fbx"), list(objetos.values()), incrustar_texturas=False)
        for nombre, o in objetos.items():
            parte = o["parte"]
            centro = Vector(ph.a_roblox(tuple(o.location / E))) - Vector(PARTES[parte][0])
            tam = Vector(ph.a_roblox(tuple(Vector(o.dimensions) / E)))
            tris = c.triangulos(o)
            piezas[nombre] = {
                "Archivo": archivo, "Categoria": o["categoria"], "Id": o["id"], "Parte": PARTES[parte][1],
                "Rol": o["rol"], "Centro": [round(v, 4) for v in centro],
                "Tamano": [round(abs(v), 4) for v in tam], "Triangulos": tris,
            }
            clave = f'{o["categoria"]}_{o["id"]}'
            por_elemento[clave] = por_elemento.get(clave, 0) + tris
    with open(os.path.join(salida, "piezas.json"), "w", encoding="utf-8") as f:
        json.dump({"nota": "studs, ejes de Roblox; Centro = respecto al centro de la parte del R6",
                   "Piezas": piezas, "TriangulosPorElemento": por_elemento}, f, indent=1, ensure_ascii=False)
    print("[ok] triángulos por elemento:")
    for k, v in sorted(por_elemento.items()):
        print(f"   {k}: {v}" + ("  <-- PASA DE 1500" if v >= 1500 else ""))
    if args.sin_render:
        return

    cuerpo = ph.maniqui({"Piel": materiales["Piel"], "Chaqueta": materiales["Piel"], "Pantalon": materiales["Piel"]})
    cabeza = [o for o in cuerpo if o.name == "Maniqui_Cabeza"]
    c.preparar_estudio(z_suelo=-3.0 * E, luz_clave=500)
    tmp = os.path.join(salida, "_render_tmp")
    tam = 260 if args.rapido else 360
    muestras = 12 if args.rapido else 40
    filas = []
    for archivo, vistas, base, margen in (
            ("Cuernos", [("Frente", 0, 6), ("3-4", -40, 12)], cabeza, 0.8),
            ("Deformaciones", [("Frente", 0, 6), ("Detras", 160, 10)], cuerpo, 0.75)):
        objetos = grupos[archivo]
        ids = []
        for o in objetos.values():
            if o["id"] not in ids:
                ids.append(o["id"])
        for id_ in ids:
            propios = [o for o in objetos.values() if o["id"] == id_]
            rutas = c.renderizar_vistas(propios + base, tmp, vistas, tam=tam, muestras=muestras, con_malla=False,
                                        margen=margen, prefijo=f"{archivo}_{id_}_")
            n = por_elemento[f'{propios[0]["categoria"]}_{id_}']
            filas.append([(f"{id_} · {n} tri · {nv}", r) for nv, r in rutas])
    planas = [x for fila in filas for x in fila]
    columnas = 6
    c.montar_hoja([planas[i:i + columnas] for i in range(0, len(planas), columnas)],
                  os.path.join(salida, f"hoja_contactos_{args.ronda}.png"),
                  f"Monstruo — piezas 3D del editor — ronda {args.ronda}",
                  notas=["Colores de muestra: en el juego los elige el jugador (cuernos, detalles)."], columnas=columnas)


if __name__ == "__main__":
    main()
