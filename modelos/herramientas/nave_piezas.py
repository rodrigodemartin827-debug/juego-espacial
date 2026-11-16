"""
Genera las piezas modulares de nave: modelo, atlas PBR, turnaround, FBX y JSON con los puntos de acople.

Uso:
    python modelos/herramientas/nave_piezas.py --salida modelos/nave_piezas --ronda 1
    python modelos/herramientas/nave_piezas.py --salida modelos/nave_piezas --solo casco_caza_t1,ala_corta_t1
    python modelos/herramientas/nave_piezas.py --salida modelos/nave_piezas --todas [--rapido]
    python modelos/herramientas/nave_piezas.py --salida modelos/nave_piezas --catalogo   (solo índice y Luau)

Cada ronda son 10 piezas (en el orden de `piezas_nave/catalogo.py`). Por pieza sale nave_piezas/<nombre>/ con:
    <nombre>.fbx, <nombre>.json, <nombre>_turnaround.jpg y texturas/<nombre>_{color,normal,rugosidad,metal,emision}.png
"""

import argparse
import json
import os
import sys
import time
import traceback

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402,F401
from mathutils import Matrix, Vector  # noqa: E402

from piezas_nave import catalogo, datos, final, render  # noqa: E402
from piezas_nave.geo import Constructor  # noqa: E402


def _reflejar_acople(a):
    b = dict(a)
    b["pos"] = Vector((-a["pos"].x, a["pos"].y, a["pos"].z))
    b["normal"] = Vector((-a["normal"].x, a["normal"].y, a["normal"].z))
    b["arriba"] = Vector((-a["arriba"].x, a["arriba"].y, a["arriba"].z))
    return b


def generar(defp, salida, rapido=False):
    t0 = time.time()
    nombre = defp["nombre"]
    carpeta = os.path.join(salida, nombre)
    os.makedirs(os.path.join(carpeta, "texturas"), exist_ok=True)
    final.escena_vacia()
    con = Constructor(nombre, defp["tier"])
    con.info["limite"] = datos.LIMITE_TRIS_CASCO_GRANDE if defp.get("grande") else datos.LIMITE_TRIS
    defp["construir"](con, defp["p"])
    acoples = list(con.acoples)
    vfx = con.info.pop("vfx", [])
    objs, rutas = final.construir_mallas(con, carpeta, rapido)

    if defp.get("lado"):
        # pieza con lado: la que se construye es la izquierda (+X); la derecha es su reflejo
        for o in objs:
            o.name = nombre + "_izq" + o.name[len(nombre):]
            o.data.name = o.name
        der = final.reflejar(objs)
        variantes = [("_izq", objs, acoples), ("_der", der, [_reflejar_acople(a) for a in acoples])]
        todos = objs + der
        acoples_vista = acoples + variantes[1][2]
    else:
        variantes = [("", objs, acoples)]
        todos = objs
        acoples_vista = acoples

    j = final.json_pieza(con, defp, variantes, rutas, carpeta)
    j["descripcion"] = defp["descripcion"]
    if vfx:
        raiz = objs[0]
        mn, mx = final.caja([raiz])
        c = (mn + mx) / 2
        from piezas_nave.geo import a_roblox
        j["anclajes_vfx"] = [{"nombre": v["nombre"], "malla": raiz.name,
                              "posicion": [round(x, 3) + 0.0 for x in a_roblox(Vector(v["pos"]) - c)],
                              "direccion": [round(x, 4) + 0.0 for x in a_roblox(Vector(v["dir"]).normalized())]}
                             for v in vfx]
    limite = j["limite_triangulos"]
    if j["triangulos"] > limite:
        print(f"[AVISO] {nombre}: {j['triangulos']} triángulos > {limite}")

    # turnaround (antes de exportar: la exportación gira la malla y la vuelve a dejar)
    render.preparar_estudio()
    tmp = os.path.join(salida, "_render_tmp")
    vistas = render.renderizar(todos, acoples_vista, tmp, nombre, tam=260 if rapido else 400,
                               muestras=12 if rapido else 40)
    lineas = [(f"{j['titulo']}", "titulo"),
              (f"Categoría: {j['categoria']} · Tier {j['tier']} ({j['estilo']})", ""),
              (f"Triángulos: {j['triangulos']} (límite {limite})", ""),
              (f"Tamaño: {j['tamano'][0]:.1f} × {j['tamano'][1]:.1f} × {j['tamano'][2]:.1f} studs (X×Y×Z)", ""),
              (f"Mallas: {len(j['mallas'])}" + (" · variantes izq/der" if defp.get("lado") else ""), ""),
              ("", ""), ("Puntos de acople", "titulo")]
    for a in j["puntos_acople"]:
        if defp.get("lado") and a.get("variante") == "der":
            continue
        flecha = "→" if a["direccion"] == "salida" else "←"
        p = a["posicion"]
        lineas.append((f"{flecha} {a['nombre']}  {a['tipo']}", "acople"))
        lineas.append((f"    ({p[0]:.2f}, {p[1]:.2f}, {p[2]:.2f})  rot {a['orientacion']}", "acople"))
    ficha = {"titulo_hoja": nombre, "subtitulo": j["descripcion"], "lineas": lineas}
    render.hoja(vistas, os.path.join(carpeta, f"{nombre}_turnaround.jpg"), ficha)

    final.exportar_fbx(os.path.join(carpeta, f"{nombre}.fbx"), todos)
    with open(os.path.join(carpeta, f"{nombre}.json"), "w", encoding="utf-8") as f:
        json.dump(j, f, indent=2, ensure_ascii=False)
    for _, ruta in vistas:
        try:
            os.remove(ruta)
        except OSError:
            pass
    print(f"[ok] {nombre}: {j['triangulos']} tri, {len(j['puntos_acople'])} acoples, {time.time() - t0:.0f} s")
    return j


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", type=int, default=0)
    ap.add_argument("--solo", default="")
    ap.add_argument("--todas", action="store_true")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--catalogo", action="store_true")
    a = ap.parse_args()
    salida = os.path.abspath(a.salida)
    piezas = catalogo.PIEZAS
    if a.solo:
        nombres = set(a.solo.split(","))
        sel = [p for p in piezas if p["nombre"] in nombres]
    elif a.ronda:
        sel = piezas[(a.ronda - 1) * 10: a.ronda * 10]
    elif a.todas:
        sel = piezas
    else:
        sel = []
    fallos = []
    for p in sel:
        try:
            generar(p, salida, a.rapido)
        except Exception:
            traceback.print_exc()
            fallos.append(p["nombre"])
    catalogo.escribir_indice(salida)
    if fallos:
        print("[FALLOS]", ", ".join(fallos))
        sys.exit(1)


if __name__ == "__main__":
    main()
