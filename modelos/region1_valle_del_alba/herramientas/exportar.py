"""
Prepara la región 1 para Roblox (sin subir nada): lee region1_valle_del_alba.blend y escribe en roblox/:

  piezas/<Pieza>.fbx y <Pieza>__lejos.fbx   cada pieza del kit UNA vez (detallada y simple)
  terreno/Terreno_<f>_<c>[__lejos].fbx       los 64 trozos de terreno, detallados y simples
  silueta/Aurora_Silueta.fbx                 Aurora vista de lejos (una malla)
  datos/piezas.json                          tamaño, centro, triángulos y color por defecto de cada pieza
  datos/edificios_<Sitio>.json               cada edificio: su CFrame y la lista de piezas (CFrame relativo, escala, color)
  datos/objetos_<Sitio>.json                 mobiliario, árboles de los pueblos, molinos, torre, fuente...
  datos/terreno.json                         cada trozo: posición, radio, textura
  datos/vegetacion/<f>_<c>.json              árboles, arbustos, rocas y matas, repartidos por trozo de terreno
  datos/lod.json                             las distancias de los niveles de detalle (diseno.LOD)

Coordenadas: las de Roblox (Y arriba, studs). Blender (x, y, z) -> Roblox (x, z, -y), igual que el FBX (que se
exporta con «Apply Transform», delante -Z y arriba Y: la receta oficial de Roblox para Blender).

Un CFrame se guarda como 12 números (x, y, z, R00, R01, R02, R10, R11, R12, R20, R21, R22), el orden del
constructor CFrame.new de Luau. Roblox centra cada malla importada en su caja, por eso cada pieza guarda «centro»
(dónde queda el centro de su caja respecto a su origen): el script de montaje lo compensa.

Uso:
    python modelos/region1_valle_del_alba/herramientas/exportar.py --blend modelos/region1_valle_del_alba/region1_valle_del_alba.blend
        --salida modelos/region1_valle_del_alba/roblox [--sin-fbx]
"""

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix  # noqa: E402

import diseno as D  # noqa: E402

C = np.array([[1.0, 0, 0], [0, 0, 1.0], [0, -1.0, 0]])  # Blender -> Roblox


def a_roblox_m(m):
    """Matriz 4x4 de Blender -> (posición, rotación 3x3, escala por eje local) en Roblox."""
    m = np.asarray(m, float)
    R = m[:3, :3]
    esc = np.linalg.norm(R, axis=0)
    Rn = R / np.where(esc > 1e-9, esc, 1.0)
    Rr = C @ Rn @ C.T
    p = C @ m[:3, 3]
    # escala en ejes locales de Roblox: x -> x, y_b -> -z_r, z_b -> y_r
    er = np.array([esc[0], esc[2], esc[1]])
    return p, Rr, er


def cframe(p, Rr):
    return [round(float(v), 4) for v in (*p, *Rr.ravel())]


def caja_malla(me):
    co = np.zeros(len(me.vertices) * 3)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3)
    if len(co) == 0:
        return np.zeros(3), np.zeros(3)
    lo, hi = co.min(axis=0), co.max(axis=0)
    return (lo + hi) / 2, hi - lo


def triangulos(me):
    return int(sum(len(p.vertices) - 2 for p in me.polygons))


def exportar_fbx(ob, ruta):
    bpy.ops.object.select_all(action="DESELECT")
    ob.hide_set(False)
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH"}, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=True, axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=False, mesh_smooth_type="FACE", use_tspace=False, add_leaf_bones=False, bake_anim=False,
        path_mode="STRIP", embed_textures=False)


def objeto_temporal(me, nombre, centro=None):
    """Objeto suelto en el origen con la malla (o una copia recentrada en `centro`), para exportarlo."""
    if centro is not None:
        me = me.copy()
        me.transform(Matrix.Translation(tuple(-centro)))
    ob = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--sin-fbx", action="store_true")
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    bpy.ops.wm.open_mainfile(filepath=os.path.abspath(a.blend))
    sal = os.path.abspath(a.salida)
    for sub in ("piezas", "terreno", "silueta", "datos", "datos/vegetacion"):
        os.makedirs(os.path.join(sal, sub), exist_ok=True)
    # la colección del kit está excluida de la capa de vista: se vuelve a incluir para poder seleccionar
    for lc in bpy.context.view_layer.layer_collection.children:
        for h in lc.children:
            h.exclude = False
            for hh in h.children:
                hh.exclude = False

    # ---------------------------------------------------------------- piezas
    piezas = {}
    for me in sorted([m for m in bpy.data.meshes if m.name.startswith("K_")], key=lambda m: m.name):
        nombre = me.name[2:]
        lejos = nombre.endswith("__lejos")
        base = nombre[: -len("__lejos")] if lejos else nombre
        centro, tam = caja_malla(me)
        info = piezas.setdefault(base, {"fbx": None, "fbx_lejos": None, "sin_lejos": False})
        clave = "lejos" if lejos else "detalle"
        info[clave] = dict(centro=[round(float(v), 4) for v in C @ centro],
                           tamano=[round(float(v), 4) for v in np.abs(C @ tam)], triangulos=triangulos(me))
        info["fbx_lejos" if lejos else "fbx"] = f"piezas/{me.name[2:]}.fbx"
        if not a.sin_fbx:
            ob = objeto_temporal(me, me.name[2:])
            exportar_fbx(ob, os.path.join(sal, "piezas", me.name[2:] + ".fbx"))
            bpy.data.objects.remove(ob)
    # piezas que de lejos no se dibujan
    for ob in bpy.data.objects:
        if ob.get("sin_lejos") and ob.get("pieza") in piezas:
            piezas[ob["pieza"]]["sin_lejos"] = True
    import kit as K

    for p in piezas:
        if p in K.PIEZAS:
            piezas[p]["color"] = K.color_defecto(p)
    with open(os.path.join(sal, "datos", "piezas.json"), "w") as f:
        json.dump(piezas, f, ensure_ascii=False, indent=1)
    print(f"piezas: {len(piezas)} ({sum(1 for p in piezas.values() if p['fbx_lejos'])} con versión simple)")

    def hex_de(ob):
        return ob.get("color", "#FFFFFF")

    def entrada_pieza(h):
        """Pieza de un grupo: CFrame relativo al grupo (sin escala), escala por eje y color."""
        padre = np.array(h.parent.matrix_world)
        esc_padre = np.linalg.norm(padre[:3, :3], axis=0)
        m = np.diag([*esc_padre, 1.0]) @ np.array(h.matrix_basis)  # el CFrame del grupo no lleva escala
        p, Rr, er = a_roblox_m(m)
        return [h["pieza"], *cframe(p, Rr), *[round(float(v), 4) for v in er], hex_de(h)]

    # ---------------------------------------------------------------- edificios y objetos
    piv = bpy.data.objects.get("Pivote_Planeta")
    sitios = {}
    for ob in bpy.data.objects:
        if "lod" not in ob.keys() or ob["lod"] in ("terreno", "nube", "silueta", "campos"):
            continue
        if ob.parent not in (None, piv):
            continue
        sitio = ob.get("sitio") or "Region"
        tipo = "edificios" if ob.type == "EMPTY" and "ancho" in ob.keys() else "objetos"
        p, Rr, _ = a_roblox_m(np.array(ob.matrix_world))
        e = dict(nombre=ob.name, lod=ob["lod"], cframe=cframe(p, Rr),
                 centro=[round(float(v), 3) for v in C @ np.array(ob["centro"])], radio=round(float(ob["radio"]), 2))
        if ob.type == "EMPTY":
            e["piezas"] = [entrada_pieza(h) for h in ob.children if "pieza" in h]
            if "ancho" in ob.keys():
                e["caja"] = [float(ob["ancho"]), float(ob["fondo"]), float(ob["alto"])]
        else:
            # un objeto de una sola pieza: su CFrame es el de la pieza (la escala va en la pieza)
            e["piezas"] = [[ob["pieza"], *cframe(np.zeros(3), np.eye(3)),
                            *[round(float(v), 4) for v in a_roblox_m(np.array(ob.matrix_world))[2]], hex_de(ob)]]
        sitios.setdefault((sitio, tipo), []).append(e)
    for (sitio, tipo), lista in sitios.items():
        with open(os.path.join(sal, "datos", f"{tipo}_{sitio}.json"), "w") as f:
            json.dump(lista, f, ensure_ascii=False, separators=(",", ":"))
        print(f"{tipo}_{sitio}: {len(lista)} ({sum(len(e['piezas']) for e in lista)} piezas)")

    # ---------------------------------------------------------------- terreno y silueta
    trozos = []
    for ob in sorted([o for o in bpy.data.objects if o.get("lod") == "terreno"], key=lambda o: o.name):
        centro, tam = caja_malla(ob.data)
        mw = np.array(ob.matrix_world)
        c_mundo = mw[:3, :3] @ centro + mw[:3, 3]
        img = ob.data.materials[0].node_tree.nodes["Image Texture"].image
        trozos.append(dict(nombre=ob.name, nivel=ob["nivel"], trozo=ob["trozo"], fbx=f"terreno/{ob.name}.fbx",
                           posicion=[round(float(v), 3) for v in C @ c_mundo],
                           centro_lod=[round(float(v), 3) for v in C @ np.array(ob["centro"])],
                           radio=round(float(ob["radio"]), 2), triangulos=triangulos(ob.data),
                           textura=os.path.basename(img.filepath)))
        if not a.sin_fbx:
            t = objeto_temporal(ob.data, ob.name, centro)
            exportar_fbx(t, os.path.join(sal, "terreno", ob.name + ".fbx"))
            bpy.data.meshes.remove(t.data)
    with open(os.path.join(sal, "datos", "terreno.json"), "w") as f:
        json.dump(trozos, f, ensure_ascii=False, indent=1)
    print(f"terreno: {len(trozos)} trozos")
    sil = bpy.data.objects.get("Aurora_Silueta")
    if sil is not None:
        centro, tam = caja_malla(sil.data)
        p, Rr, _ = a_roblox_m(np.array(sil.matrix_world))
        datos_sil = dict(nombre=sil.name, fbx="silueta/Aurora_Silueta.fbx", cframe=cframe(p, Rr),
                         centro=[round(float(v), 4) for v in C @ centro], tamano=[round(float(v), 4) for v in
                                                                                   np.abs(C @ tam)],
                         triangulos=triangulos(sil.data), centro_lod=[round(float(v), 3) for v in
                                                                      C @ np.array(sil["centro"])])
        with open(os.path.join(sal, "datos", "silueta_Aurora.json"), "w") as f:
            json.dump(datos_sil, f, ensure_ascii=False, indent=1)
        if not a.sin_fbx:
            t = objeto_temporal(sil.data, sil.name)
            exportar_fbx(t, os.path.join(sal, "silueta", "Aurora_Silueta.fbx"))
            bpy.data.objects.remove(t)

    # ---------------------------------------------------------------- vegetación (por trozo de terreno)
    import geo
    from region import FUENTES_VEG

    k = D.TERRENO_TROZOS["trozos"]
    por_trozo = {}
    for nube in [o for o in bpy.data.objects if o.get("lod") == "nube"]:
        me = nube.data
        n = len(me.vertices)
        co = np.zeros(n * 3)
        me.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3)
        tipo = np.zeros(n, np.int32)
        me.attributes["tipo_base"].data.foreach_get("value", tipo)
        q = np.zeros(n * 4)
        me.attributes["rot"].data.foreach_get("value", q)
        q = q.reshape(-1, 4)
        esc = np.zeros(n * 3)
        me.attributes["escala"].data.foreach_get("vector", esc)
        esc = esc.reshape(-1, 3)[:, 0]
        x, y = geo.diseno(co / np.linalg.norm(co, axis=1, keepdims=True))
        fila = np.clip(((geo.L - y) / (2 * geo.L) * k).astype(int), 0, k - 1)
        col = np.clip(((x + geo.L) / (2 * geo.L) * k).astype(int), 0, k - 1)
        cat = nube.get("categoria", "vegetacion")
        for i in range(n):
            # rotación: cuaternión de Blender -> matriz -> Roblox
            w, qx, qy, qz = q[i]
            Rb = np.array([[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * w), 2 * (qx * qz + qy * w)],
                           [2 * (qx * qy + qz * w), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * w)],
                           [2 * (qx * qz - qy * w), 2 * (qy * qz + qx * w), 1 - 2 * (qx * qx + qy * qy)]])
            Rr = C @ Rb @ C.T
            p = C @ co[i]
            por_trozo.setdefault(f"{fila[i]}_{col[i]}", []).append(
                [FUENTES_VEG[tipo[i]], cat, *cframe(p, Rr), round(float(esc[i]), 3)])
    for clave, lista in por_trozo.items():
        with open(os.path.join(sal, "datos", "vegetacion", f"{clave}.json"), "w") as f:
            json.dump(lista, f, separators=(",", ":"))
    print(f"vegetación: {sum(len(v) for v in por_trozo.values())} instancias en {len(por_trozo)} trozos")
    with open(os.path.join(sal, "datos", "lod.json"), "w") as f:
        json.dump(D.LOD, f, indent=1)


if __name__ == "__main__":
    main()
