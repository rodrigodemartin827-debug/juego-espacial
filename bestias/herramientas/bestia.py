"""
Cierre común de una bestia: presupuesto de triángulos, mallas bajas, pivotes, puntos de montaje, atlas UV, horneado,
render del turnaround (+ primeros planos de revisión), exportación FBX con el giro, reimportación y JSON.

Cada script de bestia construye sus mallas altas (campos), sus detalles y sus materiales y llama a `terminar()`.
"""

import os
import time

import bpy
from mathutils import Vector

import taller as T


def terminar(cfg):
    """
    cfg (dict):
      nombre, titulo, rol, jinetes, color_titulo (rgb 0-255), neon (lista de hex), presupuesto, salida, ronda, rapido,
      altas {pieza: malla alta de campo con su material}, detalles {pieza: [objetos]},
      geometricas {pieza: objeto} (piezas solo de detalle), soldadas {nombre: (objeto, padre)},
      peso_tris {pieza de campo: peso}, pivotes {pieza: (x,y,z)}, padre {pieza: padre}, orden [piezas del rig],
      montajes {nombre: (posición, pieza)}, prioridad_uv {pieza: factor}, planas [piezas con UV cenital],
      cerca [(nombre, az, el, (x, y, z), radio)], render_material {objeto: material solo para el render},
      notas_json [str], tam_nombres (dict nombre_dimension: (eje_x, eje_y, eje_z) para el JSON), radio_estudio
    """
    t0 = time.time()
    salida = os.path.abspath(cfg["salida"])
    os.makedirs(salida, exist_ok=True)
    tmp = os.path.join(salida, "_render_tmp")
    nombre = cfg["nombre"]
    altas = cfg["altas"]
    detalles = cfg.get("detalles", {})
    geometricas = cfg.get("geometricas", {})
    soldadas = cfg.get("soldadas", {})

    # --- Presupuesto ---
    tris_det = sum(T.triangulos(o) for lst in detalles.values() for o in lst)
    tris_det += sum(T.triangulos(o) for o in geometricas.values())
    tris_det += sum(T.triangulos(o) for o, _ in soldadas.values())
    libre = cfg["presupuesto"] - tris_det - 80
    pesos = cfg["peso_tris"]
    suma = sum(pesos.values())
    print(f"[presupuesto] detalles {tris_det} tri; quedan {libre} para las superficies")
    if libre < 1000:
        raise RuntimeError("Los detalles se comen el presupuesto: hay que aligerarlos")

    parejas, piezas = [], {}
    for pieza, alta in altas.items():
        objetivo = max(60, int(libre * pesos[pieza] / suma))
        baja = T.diezmar(alta, objetivo, pieza + "_b")
        T.suave(baja)
        extras_a = [T.copiar(o, o.name + "_a") for o in detalles.get(pieza, [])]
        extras_b = detalles.get(pieza, [])
        for o in extras_a + extras_b:
            T.suave(o, angulo=38)
        a = T.unir([alta] + extras_a, pieza + "_alta")
        b = T.unir([baja] + extras_b, pieza)
        parejas.append((a, b))
        piezas[pieza] = b
    for pieza, o in list(geometricas.items()) + [(n, o) for n, (o, _) in soldadas.items()]:
        T.suave(o, angulo=50)
        o.name = pieza
        parejas.append((T.copiar(o, pieza + "_alta"), o))
        piezas[pieza] = o

    for pieza in cfg.get("planas", []):
        o = piezas[pieza]
        me = o.data
        plano = me.attributes.new("uv_plano", "FLOAT", "FACE")
        prio = me.attributes.new("uv_prioridad", "FLOAT", "FACE")
        for p in me.polygons:
            plano.data[p.index].value = 1.0 if abs(p.normal.z) > 0.5 and p.material_index == 0 else 0.0
            prio.data[p.index].value = 1.2 if p.normal.z > 0.3 else (0.75 if p.normal.z < -0.3 else 1.0)

    # --- Pivotes ---
    for pieza, o in piezas.items():
        T.poner_origen(o, cfg["pivotes"][pieza])
    for a, b in parejas:
        T.poner_origen(a, b.matrix_world.translation)

    # --- Puntos de montaje ---
    mat_m, _ = T.material_simple("punto_montaje", (1.0, 0.1, 0.6), rug=0.5)
    cubos = []
    for nom, (p, padre) in cfg["montajes"].items():
        bpy.ops.mesh.primitive_cube_add(size=0.3, location=Vector(p))
        cu = bpy.context.active_object
        cu.name = nom
        cu.data.name = nom
        T.asignar_material(cu, mat_m)
        cu["padre"] = padre
        cubos.append(cu)

    # --- UV y horneado ---
    orden = cfg["orden"]
    lista = [piezas[n] for n in orden] + [piezas[n] for n in soldadas]
    T.desplegar_piezas(lista, cfg.get("prioridad_uv", {}), margen=0.0035)
    tam = 512 if cfg["rapido"] else T.TAM_ATLAS
    rutas, _ = T.hornear_atlas(parejas, salida, nombre, tam=tam, muestras=4 if cfg["rapido"] else 12,
                               extrusion=0.07, distancia=0.22)
    for a, _ in parejas:
        bpy.data.objects.remove(a)
    tris = {n: T.triangulos(o) for n, o in piezas.items()}
    total = sum(tris.values())
    print(f"[tris] total {total}: {tris}")
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(salida, f"{nombre}.blend"), compress=True)

    # --- Render ---
    if not cfg.get("sin_render"):
        originales = {}
        for o, m in cfg.get("render_material", {}).items():
            originales[o] = o.active_material
            T.asignar_material(o, m)
        for c in cubos:
            c.hide_render = True
        objs = list(piezas.values())
        T.preparar_estudio(cfg.get("radio_estudio", 9.0))
        bpy.context.scene.view_settings.exposure = cfg.get("exposicion", 0.0)
        r = T.renderizar_vistas(objs, tmp, T.VISTAS_TURNAROUND, tam=420 if cfg["rapido"] else 760,
                                muestras=24 if cfg["rapido"] else 96, prefijo="t_", margen=1.02)
        notas = [f"Ronda {cfg['ronda']} · {total} triángulos (presupuesto {cfg['presupuesto']}) · "
                 f"{len(orden)} piezas de rig",
                 f"Atlas 2048 horneado: color, normal, roughness, metalness, emisión ({' + '.join(cfg['neon'])})"]
        T.montar_turnaround(r, os.path.join(salida, f"{nombre}_turnaround.png"), f"{cfg['titulo']} — turnaround",
                            notas)
        r2 = []
        for (nom, az, el, c, rad) in cfg.get("cerca", []):
            r2 += T.renderizar_vistas(objs, tmp, [(nom, az, el)], tam=420 if cfg["rapido"] else 620,
                                      muestras=24 if cfg["rapido"] else 64, prefijo="c_", centro=c, radio=rad,
                                      margen=1.0)
        if r2:
            T.montar_turnaround(r2, os.path.join(tmp, f"primeros_planos_r{cfg['ronda']}.png"),
                                f"{cfg['titulo']} — primeros planos", columnas=3)
        for o, m in originales.items():
            T.asignar_material(o, m)
        for c in cubos:
            c.hide_render = False

    # --- Exportación, JSON y verificación ---
    exportables = lista + cubos
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in lista:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    dim = mx - mn
    ruta_fbx = os.path.join(salida, f"{nombre}.fbx")
    T.exportar_fbx(ruta_fbx, exportables)
    esperado = {o.name: {"pivote": list(o.matrix_world.translation), "tris": T.triangulos(o)} for o in exportables}
    padre = cfg["padre"]
    datos = {
        "nombre": nombre,
        "bestia": cfg["titulo"].title(),
        "rol": cfg["rol"],
        "jinetes": cfg["jinetes"],
        "unidades": "studs (1 unidad de Blender = 1 stud; FBX en metros con 1 stud = 0,28 m)",
        "giro_importacion": "180° en el eje vertical aplicado antes de exportar: la bestia mira a -Z en Roblox",
        "coordenadas": "pivotes en Roblox (X derecha, Y arriba, -Z delante) relativos al origen del modelo; "
                       "'modelado' = coordenadas de Blender antes del giro (X derecha, Y delante, Z arriba)",
        "triangulos": {"total_visibles": total, "presupuesto": cfg["presupuesto"], "por_pieza": tris,
                       "puntos_de_montaje": 12 * len(cubos)},
        "tamano_studs": {"ancho_x_largo_x_alto_en_reposo": [round(dim.x, 2), round(dim.y, 2), round(dim.z, 2)]},
        "color_neon": cfg["neon"],
        "texturas": {k: os.path.basename(v) for k, v in rutas.items()},
        "piezas": [
            {"nombre": n, "padre": padre.get(n), "tipo": "rig (Motor6D)" if n in orden else "soldada (Weld)",
             "pivote_roblox": T.a_roblox(piezas[n].matrix_world.translation),
             "pivote_modelado": [round(c, 4) for c in piezas[n].matrix_world.translation],
             "triangulos": tris[n]}
            for n in list(orden) + list(soldadas)
        ],
        "puntos_montaje": [
            {"nombre": c.name, "pieza": c["padre"], "tamano": 0.3, "orientacion": "hacia delante (-Z en Roblox)",
             "posicion_roblox": T.a_roblox(c.matrix_world.translation),
             "posicion_modelado": [round(v, 4) for v in c.matrix_world.translation],
             "relativo_a_pieza_roblox": T.a_roblox(c.matrix_world.translation -
                                                   piezas[c["padre"]].matrix_world.translation)}
            for c in cubos
        ],
        "notas": cfg.get("notas_json", []) + [
            "Los puntos de montaje son cubos de 0,3: en Roblox, Transparency = 1, CanCollide = false.",
            "El atlas lo comparten todas las piezas (SurfaceAppearance con color, normal, roughness y metal).",
        ],
    }
    datos.update(cfg.get("json_extra", {}))
    T.escribir_json(os.path.join(salida, f"{nombre}.json"), datos)
    ok, informe = T.reimportar_y_verificar(ruta_fbx, esperado)
    with open(os.path.join(salida, "verificacion_fbx.txt"), "w", encoding="utf-8") as f:
        f.write(("OK" if ok else "CON ERRORES") + "\n" + "\n".join(informe) + "\n")
    print("[verificacion]", "OK" if ok else "ERRORES")
    for linea in informe:
        print("   ", linea)
    print(f"[fin] {time.time() - t0:.0f}s")
    return ok
