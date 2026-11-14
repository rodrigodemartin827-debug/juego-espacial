"""
Comprueba lo que se entrega, volviendo a importar cada FBX en una escena vacía:
  * triángulos por debajo del límite, UV presentes y dentro de 0-1, tamaño en studs igual al de datos/<pieza>.json;
  * texturas de 1024 × 1024;
  * caras del revés: se renderiza la pieza desde 8 puntos con un material que pinta de blanco la cara trasera y se
    cuenta el porcentaje de píxeles blancos (debe ser ~0: todas las normales miran hacia fuera).

    python verificar.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

import proceso as pr  # noqa: E402
from forja import LIMITES  # noqa: E402

SALIDA = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))


def main():
    todo_bien = True
    tmp = os.path.join(SALIDA, "_render_tmp")
    for clave, limite in LIMITES.items():
        nombre = f"forja_{clave}"
        scn = pr.escena_vacia()
        bpy.ops.import_scene.fbx(filepath=os.path.join(SALIDA, nombre + ".fbx"))
        obs = [o for o in scn.objects if o.type == "MESH"]
        for o in obs:   # aplicar la transformación del importador para medir en el espacio del mundo
            o.data.transform(o.matrix_world)
            o.matrix_world.identity()
        tris = sum(pr.triangulos(o) for o in obs)
        mn, mx = pr.caja(obs)
        tam = [round(mx.x - mn.x, 3), round(mx.z - mn.z, 3), round(mx.y - mn.y, 3)]
        with open(os.path.join(SALIDA, "datos", nombre + ".json"), encoding="utf-8") as f:
            d = json.load(f)
        uv_ok = True
        for o in obs:
            if not o.data.uv_layers:
                uv_ok = False
                continue
            uv = np.zeros(len(o.data.loops) * 2, dtype=np.float32)
            o.data.uv_layers[0].data.foreach_get("uv", uv)
            uv_ok = uv_ok and uv.min() >= -1e-4 and uv.max() <= 1 + 1e-4
        tex_ok = all(Image.open(os.path.join(SALIDA, "texturas", t)).size == (1024, 1024)
                     for t in d["texturas"].values())
        # Caras del revés
        scn.world.use_nodes = True
        scn.world.node_tree.nodes["Background"].inputs[1].default_value = 0.0
        scn.view_layers[0].material_override = pr.material_caras_al_reves()
        scn.cycles.use_denoising = False
        scn.view_settings.view_transform = "Standard"
        blancos = total = 0
        for i in range(8):
            pr.encuadrar(scn, obs, i * 45, 25 if i % 2 else 55)
            ruta = pr.render(scn, os.path.join(tmp, "reves.png"), 256, 256, 4)
            im = np.asarray(Image.open(ruta).convert("L"))
            blancos += int((im > 128).sum())
            total += im.size
        pct = 100.0 * blancos / total
        ok = tris <= limite and tris == d["triangulos"] and uv_ok and tex_ok and pct < 0.05 and \
            all(abs(a - b) < 0.01 for a, b in zip(tam, d["tamano_studs"]))
        todo_bien = todo_bien and ok
        print(f"[{'OK' if ok else 'FALLO'}] {nombre}.fbx: {len(obs)} malla(s), {tris} tris (límite {limite}), "
              f"{tam} studs, UV {'bien' if uv_ok else 'MAL'}, texturas 1024 {'bien' if tex_ok else 'MAL'}, "
              f"caras del revés {pct:.3f} %")
    print("TODO BIEN" if todo_bien else "HAY FALLOS")
    return 0 if todo_bien else 1


if __name__ == "__main__":
    sys.exit(main())
