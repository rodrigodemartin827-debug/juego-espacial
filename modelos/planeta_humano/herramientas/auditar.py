"""
Revisa los 105 modelos: que existan todos los archivos, que el JSON esté dentro de presupuesto y que la reimportación
del FBX no haya dado avisos. Escribe ../indice.json (resumen de todos) y devuelve código 1 si algo falla.
Uso: python auditar.py
"""
import json
import os
import sys

from PIL import Image

import generar

RAIZ = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
M = generar.cargar()
problemas, indice = [], []
for n, info in sorted(M.items(), key=lambda x: x[1]["num"]):
    c = os.path.join(RAIZ, n)
    rj = os.path.join(c, f"{n}.json")
    if not os.path.exists(rj):
        problemas.append(f"{n}: falta el JSON")
        continue
    d = json.load(open(rj, encoding="utf-8"))
    necesarios = [f"{n}.fbx", f"{n}_turnaround.png"] + [f"{n}_{k}.png" for k in ("color", "normal", "roughness", "metalness")]
    if any("Neon" == p.get("material_roblox") for p in d["piezas"]):
        necesarios.append(f"{n}_emision.png")
    for f in necesarios:
        r = os.path.join(c, f)
        if not os.path.exists(r):
            problemas.append(f"{n}: falta {f}")
        elif f.endswith(".png"):
            try:
                im = Image.open(r)
                im.load()
                if "turnaround" not in f and im.size != (1024, 1024):
                    problemas.append(f"{n}: {f} mide {im.size}")
            except Exception as e:
                problemas.append(f"{n}: {f} dañado ({e})")
    if not d["dentro_de_presupuesto"]:
        problemas.append(f"{n}: {d['triangulos']} tris > {d['presupuesto_triangulos']}")
    if not d["verificacion_fbx"]["ok"]:
        problemas.append(f"{n}: verificación FBX: {'; '.join(d['verificacion_fbx']['avisos'])}")
    indice.append({"numero": d["numero"], "nombre": n, "zona": d["zona"], "categoria": d["categoria"],
                   "triangulos": d["triangulos"], "presupuesto": d["presupuesto_triangulos"],
                   "tamano_studs": d["tamano_studs"], "piezas": [p["nombre"] for p in d["piezas"]]})
json.dump({"modelos": indice, "total": len(indice)}, open(os.path.join(RAIZ, "indice.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print(f"{len(indice)} modelos con JSON; {len(problemas)} problemas")
for p in problemas:
    print("  -", p)
sys.exit(1 if problemas else 0)
