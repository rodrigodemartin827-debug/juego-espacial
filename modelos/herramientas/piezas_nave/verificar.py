"""
Comprueba las piezas generadas sin Studio:
  * cada pieza del catálogo tiene su carpeta con FBX, JSON, turnaround y las texturas que nombra el JSON;
  * triángulos por debajo del límite; nombres en snake_case sin ñ ni acentos;
  * cada acople tiene nombre, malla existente, posición, orientación, tipo válido y dirección;
  * la orientación (Euler de Roblox, orden Y-X-Z) reproduce la normal y el "arriba" del JSON;
  * las entradas aceptan su propio tipo y cada salida (menos MOTOR_ESCAPE) tiene alguna pieza que encaja en ella.

Uso: python modelos/herramientas/piezas_nave/verificar.py modelos/nave_piezas
"""

import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from piezas_nave import catalogo, datos  # noqa: E402


def matriz(rx, ry, rz):
    rx, ry, rz = (math.radians(a) for a in (rx, ry, rz))

    def mul(a, b):
        return [[sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)] for i in range(3)]

    Rx = [[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]]
    Ry = [[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]]
    Rz = [[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]]
    return mul(mul(Ry, Rx), Rz)


def main(carpeta):
    errores = []
    entradas, salidas = [], []
    total = 0
    for p in catalogo.PIEZAS:
        n = p["nombre"]
        if not re.fullmatch(r"[a-z0-9_]+", n):
            errores.append(f"{n}: nombre no es snake_case ASCII")
        d = os.path.join(carpeta, n)
        for f in (f"{n}.fbx", f"{n}.json", f"{n}_turnaround.jpg"):
            if not os.path.exists(os.path.join(d, f)):
                errores.append(f"{n}: falta {f}")
        rj = os.path.join(d, f"{n}.json")
        if not os.path.exists(rj):
            continue
        total += 1
        j = json.load(open(rj, encoding="utf-8"))
        if j["triangulos"] > j["limite_triangulos"]:
            errores.append(f"{n}: {j['triangulos']} triángulos > {j['limite_triangulos']}")
        mallas = {m["nombre"] for m in j["mallas"]}
        for m in j["mallas"]:
            for k, ruta in m.get("texturas", {}).items():
                if not os.path.exists(os.path.join(d, ruta)):
                    errores.append(f"{n}: falta la textura {ruta}")
        if not j["puntos_acople"]:
            errores.append(f"{n}: sin puntos de acople")
        if not any(a["direccion"] == "entrada" for a in j["puntos_acople"]) and j["categoria"] != "casco":
            errores.append(f"{n}: sin acople de entrada")
        for a in j["puntos_acople"]:
            ctx = f"{n}.{a['nombre']}"
            for k in ("nombre", "malla", "posicion", "orientacion", "tipo", "direccion"):
                if k not in a:
                    errores.append(f"{ctx}: falta {k}")
            if a["tipo"] not in datos.CONECTORES:
                errores.append(f"{ctx}: tipo desconocido {a['tipo']}")
            if a["direccion"] not in ("entrada", "salida"):
                errores.append(f"{ctx}: dirección {a['direccion']}")
            if a["malla"] not in mallas:
                errores.append(f"{ctx}: la malla {a['malla']} no está en el FBX")
            R = matriz(*a["orientacion"])
            look = [-R[i][2] for i in range(3)]
            up = [R[i][1] for i in range(3)]
            if max(abs(x - y) for x, y in zip(look, a["normal"])) > 2e-3 or \
                    max(abs(x - y) for x, y in zip(up, a["arriba"])) > 2e-3:
                errores.append(f"{ctx}: la orientación no coincide con la normal/arriba")
            if a["direccion"] == "entrada":
                if a["tipo"] not in a.get("acepta", []) and a["tipo"] != "UNIVERSAL":
                    errores.append(f"{ctx}: no acepta su propio tipo")
                entradas.append((n, a))
            else:
                salidas.append((n, a))
    # cada salida tiene al menos una entrada de otra pieza que encaja
    for n, s in salidas:
        if s["tipo"] == "MOTOR_ESCAPE":
            continue
        ok = any(e_n != n and (s["tipo"] in e["acepta"] or "UNIVERSAL" in (s["tipo"], e["tipo"])) and
                 e["brida"] <= s["brida"] + 1e-6 for e_n, e in entradas)
        if not ok:
            errores.append(f"{n}.{s['nombre']}: ninguna pieza encaja en esta salida ({s['tipo']})")
    print(f"{total} piezas, {len(entradas)} entradas, {len(salidas)} salidas")
    for e in errores:
        print("  ERROR", e)
    print("OK" if not errores else f"{len(errores)} errores")
    return 0 if not errores else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
