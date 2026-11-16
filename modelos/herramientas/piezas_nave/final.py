"""
De un `Constructor` a la pieza terminada: bisel, sombreado, mallas separadas, UV, atlas PBR, render, FBX y JSON.

Mallas que salen de cada pieza (todas con el nombre de la pieza delante):
  <pieza>                 el cuerpo con el atlas (SurfaceAppearance)
  <pieza>_<grupo>         partes con atlas que se mueven aparte (cabeza de torreta, plato de radar...)
  <pieza>[_grupo]_neon    lo que brilla (Material Neon), _neon2 para el segundo color
  <pieza>[_grupo]_cristal cristal (Material Glass)
  <pieza>[_grupo]_domo    campo de fuerza (Material ForceField)
  <pieza>[_grupo]_llama   llama del postquemador (Neon semitransparente)
Las piezas con lado (alas) salen dos veces: <pieza>_izq... y <pieza>_der..., la derecha reflejada.
"""

import json
import math
import os

import bpy
import bmesh
from mathutils import Matrix, Vector

from . import datos, texturas
from .geo import SIN_ATLAS, a_roblox, rot_euler_roblox

V = Vector


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0
    scn.world = bpy.data.worlds.new("mundo")
    return scn


def _biselar_y_sombrear(con, ancho, angulo_bisel=33, angulo_duro=32):
    bm = con.bm
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    capa_orig = bm.faces.layers.int.new("orig")
    for f in bm.faces:
        f[capa_orig] = 1
    if ancho > 0:
        aristas = []
        for e in bm.edges:
            if len(e.link_faces) != 2:
                continue
            f1, f2 = e.link_faces
            if f1 in con.sin_bisel or f2 in con.sin_bisel:
                continue
            if f1.normal.angle(f2.normal, 0) > math.radians(angulo_bisel) and e.calc_length() > ancho * 3:
                aristas.append(e)
        if aristas:
            bmesh.ops.bevel(bm, geom=aristas, offset=ancho, offset_type="OFFSET", segments=1, profile=0.5,
                            affect="EDGES", clamp_overlap=True)
    # las caras nuevas del bisel heredan grupo y material de sus vecinas originales
    capa_g = con.capa_grupo
    for f in bm.faces:
        if f[capa_orig] == 1:
            continue
        vecinas = [g for e in f.edges for g in e.link_faces if g is not f and g[capa_orig] == 1]
        if vecinas:
            f[capa_g] = vecinas[0][capa_g]
            f.material_index = vecinas[0].material_index
    ngons = [f for f in bm.faces if len(f.verts) > 4]
    if ngons:
        bmesh.ops.triangulate(bm, faces=ngons)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:
        if len(e.link_faces) != 2:
            e.smooth = False
            continue
        f1, f2 = e.link_faces
        e.smooth = f1.normal.angle(f2.normal, 0) < math.radians(angulo_duro) and \
            f1.material_index == f2.material_index
    bm.faces.layers.int.remove(capa_orig)


def _objeto_de_caras(con, nombre, caras_sel, materiales):
    """Copia las caras elegidas a un objeto nuevo (con sus materiales)."""
    bm = con.bm
    nuevo = bmesh.new()
    capa = nuevo.faces.layers.int.new("grupo")
    mapa = {}
    for f in caras_sel:
        vs = []
        for v in f.verts:
            if v not in mapa:
                mapa[v] = nuevo.verts.new(v.co)
            vs.append(mapa[v])
        try:
            g = nuevo.faces.new(vs)
        except ValueError:
            continue
        g.material_index = f.material_index
        g.smooth = f.smooth
        g[capa] = f[con.capa_grupo]
    nuevo.verts.index_update()
    # bordes duros: copiar el suavizado de las aristas originales
    nuevo.edges.ensure_lookup_table()
    inv = {mapa[v]: v for v in mapa}
    for e in nuevo.edges:
        a, b = inv[e.verts[0]], inv[e.verts[1]]
        eo = bm.edges.get((a, b))
        if eo is not None:
            e.smooth = eo.smooth
    malla = bpy.data.meshes.new(nombre)
    nuevo.to_mesh(malla)
    nuevo.free()
    obj = bpy.data.objects.new(nombre, malla)
    bpy.context.scene.collection.objects.link(obj)
    for m in materiales:
        malla.materials.append(m)
    return obj


def _uv(obj, margen=0.006):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=margen, scale_to_bounds=False)
    try:
        bpy.ops.uv.pack_islands(margin=margen, rotate=True)
    except Exception:
        pass
    bpy.ops.object.mode_set(mode="OBJECT")


def _separar_por_grupo(obj, con, nombre_base, mat):
    """Divide el objeto con atlas en un objeto por grupo. Devuelve {grupo: objeto}."""
    capa = obj.data.attributes.get("grupo")
    grupos = sorted({v.value for v in capa.data}) if capa is not None else [0]
    if len(grupos) <= 1:
        obj.name = nombre_base if con.grupos[grupos[0]] == "cuerpo" else f"{nombre_base}_{con.grupos[grupos[0]]}"
        obj.data.name = obj.name
        return {con.grupos[grupos[0]]: obj}
    res = {}
    for g in grupos:
        copia = obj.copy()
        copia.data = obj.data.copy()
        bpy.context.scene.collection.objects.link(copia)
        bm = bmesh.new()
        bm.from_mesh(copia.data)
        lay = bm.faces.layers.int.get("grupo")
        borrar = [f for f in bm.faces if f[lay] != g]
        bmesh.ops.delete(bm, geom=borrar, context="FACES")
        bm.to_mesh(copia.data)
        bm.free()
        nombre = nombre_base if con.grupos[g] == "cuerpo" else f"{nombre_base}_{con.grupos[g]}"
        copia.name = nombre
        copia.data.name = nombre
        res[con.grupos[g]] = copia
    bpy.data.objects.remove(obj)
    return res


def tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def caja(objs):
    mn = V((1e9, 1e9, 1e9))
    mx = V((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = V(map(min, mn, w))
            mx = V(map(max, mx, w))
    return mn, mx


def construir_mallas(con, carpeta, rapido=False):
    """Bisela, separa y texturiza. Devuelve (objetos, rutas_texturas)."""
    ancho = con.info.get("bisel", con.estilo["bisel"])
    _biselar_y_sombrear(con, ancho)
    estilo = con.estilo
    mats_base = []
    for r in con.ranuras:
        m = bpy.data.materials.new(f"{con.nombre}_{r}")
        m.use_nodes = True
        mats_base.append(m)

    bm = con.bm
    con_atlas = [f for f in bm.faces if con.ranuras[f.material_index] not in SIN_ATLAS]
    objetos = []
    rutas = {}
    if con_atlas:
        obj = _objeto_de_caras(con, con.nombre, con_atlas, mats_base)
        # límite de triángulos: si se pasa, se simplifica un poco el cuerpo (colapso de aristas)
        limite = con.info.get("limite")
        if limite:
            otros = sum(len(f.verts) - 2 for f in bm.faces if con.ranuras[f.material_index] in SIN_ATLAS)
            propio = tris(obj)
            if propio + otros > limite:
                ratio = max(0.5, (limite * 0.985 - otros) / propio)
                mod = obj.modifiers.new("simplificar", "DECIMATE")
                mod.decimate_type = "COLLAPSE"
                mod.ratio = ratio
                mod.use_collapse_triangulate = True
                bpy.ops.object.select_all(action="DESELECT")
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                bpy.ops.object.modifier_apply(modifier=mod.name)
                print(f"[info] {con.nombre}: {propio + otros} -> {tris(obj) + otros} triángulos (simplificado)")
        _uv(obj)
        tam = 256 if rapido else 1024
        rutas = texturas.texturizar(obj, con, os.path.join(carpeta, "texturas"), tam=tam,
                                    muestras_ao=6 if rapido else 24)
        mat = texturas.material_final(con.nombre, rutas)
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        for p in obj.data.polygons:
            p.material_index = 0
        partes = _separar_por_grupo(obj, con, con.nombre, mat)
        # el cuerpo primero
        objetos += [partes[g] for g in con.grupos if g in partes]

    for r in SIN_ATLAS:
        if r not in con.ranuras:
            continue
        idx = con.ranuras.index(r)
        for gi, g in enumerate(con.grupos):
            caras = [f for f in bm.faces if f.material_index == idx and f[con.capa_grupo] == gi]
            if not caras:
                continue
            hexa = con.colores_extra.get(r, estilo.get(r, "#FFFFFF"))
            mat = texturas.material_plano(f"{con.nombre}_{g}_{r}", r, hexa)
            nombre = con.nombre + ("" if g == "cuerpo" else f"_{g}") + f"_{r}"
            o = _objeto_de_caras(con, nombre, caras, [mat])
            for p in o.data.polygons:
                p.material_index = 0
            o["ranura"] = r
            o["color"] = hexa
            objetos.append(o)
    con.bm.free()
    return objetos, rutas


def reflejar(objetos, sufijo_de="_izq", sufijo_a="_der"):
    """Copia reflejada en X de cada objeto (variante derecha de una pieza con lado)."""
    nuevos = []
    for o in objetos:
        c = o.copy()
        c.data = o.data.copy()
        c.data.transform(Matrix.Diagonal((-1, 1, 1, 1)))
        c.data.flip_normals()
        c.name = o.name.replace(sufijo_de, sufijo_a)
        c.data.name = c.name
        for k in o.keys():
            c[k] = o[k]
        bpy.context.scene.collection.objects.link(c)
        nuevos.append(c)
    return nuevos


def _acople_json(a, centro_malla, nombre_malla):
    p = a["pos"] - centro_malla
    look = a_roblox(a["normal"])
    up = a_roblox(a["arriba"])
    d = {
        "nombre": a["nombre"],
        "malla": nombre_malla,
        "posicion": [round(x, 3) + 0.0 for x in a_roblox(p)],
        "orientacion": rot_euler_roblox(look, up),
        "normal": [round(x, 4) + 0.0 for x in look],
        "arriba": [round(x, 4) + 0.0 for x in up],
        "tipo": a["tipo"],
        "direccion": a["direccion"],
        "brida": a["tam"],
    }
    if a["direccion"] == "entrada":
        d["acepta"] = a["acepta"]
    return d


def json_pieza(con, def_pieza, variantes, rutas, carpeta):
    """
    variantes: lista de (sufijo, objetos, acoples). Las posiciones de cada acople son relativas al centro de la caja
    de su malla (en Roblox, la Position de la MeshPart), en studs y con los ejes de Studio.
    """
    mallas = []
    acoples = []
    tri_var = []
    tam_total = None
    for sufijo, objs, acs in variantes:
        mn, mx = caja(objs)
        if tam_total is None:
            tam_total = mx - mn
        tri_var.append(sum(tris(o) for o in objs))
        centros = {}
        for o in objs:
            omn, omx = caja([o])
            centros[o.name] = (omn + omx) / 2
        raiz = objs[0]
        for o in objs:
            r = o.get("ranura")
            info = {
                "nombre": o.name,
                "triangulos": tris(o),
                "tamano": [round(abs(x), 3) for x in a_roblox(caja([o])[1] - caja([o])[0])],
                "centro": [round(x, 3) + 0.0 for x in a_roblox(centros[o.name] - centros[raiz.name])],
            }
            if r:
                info["material_roblox"] = datos.MATERIAL_ROBLOX[r]
                info["color"] = o.get("color")
                if r in datos.TRANSPARENCIA_ROBLOX:
                    info["transparencia"] = datos.TRANSPARENCIA_ROBLOX[r]
            else:
                info["material_roblox"] = "SurfaceAppearance"
                info["texturas"] = {k: os.path.relpath(v, carpeta) for k, v in rutas.items()}
            if sufijo:
                info["variante"] = sufijo.strip("_")
            mallas.append(info)
        for a in acs:
            nombre_malla = con.nombre + sufijo + ("" if a["malla"] == "cuerpo" else f"_{a['malla']}")
            if nombre_malla not in centros:
                nombre_malla = raiz.name
            d = _acople_json(a, centros[nombre_malla], nombre_malla)
            if sufijo:
                d["variante"] = sufijo.strip("_")
            acoples.append(d)
    limite = datos.LIMITE_TRIS_CASCO_GRANDE if def_pieza.get("grande") else datos.LIMITE_TRIS
    j = {
        "nombre": con.nombre,
        "titulo": def_pieza["titulo"],
        "categoria": def_pieza["categoria"],
        "tier": con.tier,
        "estilo": con.estilo["nombre"],
        "triangulos": max(tri_var),
        "limite_triangulos": limite,
        "tamano": [round(abs(x), 3) for x in a_roblox(tam_total)],
        "unidades": "studs (1 unidad de Blender = 1 stud)",
        "ejes": "Roblox: delante -Z, arriba +Y, derecha +X. Posiciones relativas al centro de la malla del acople",
        "giro_importacion": datos.GIRO_IMPORTACION,
        "variantes": [v[0].strip("_") for v in variantes if v[0]] or None,
        "mallas": mallas,
        "puntos_acople": acoples,
    }
    for k, v in con.info.items():
        if k.startswith("json_"):
            j[k[5:]] = v
    if j["variantes"] is None:
        del j["variantes"]
    return j


def exportar_fbx(ruta, objetos):
    """
    FBX para el importador de Roblox. 1 unidad = 1 stud (en Studio: Scale Unit = Stud), escalas aplicadas
    (FBX All) y la malla girada GIRO_IMPORTACION grados alrededor del eje vertical justo antes de exportar.
    """
    giro = Matrix.Rotation(math.radians(datos.GIRO_IMPORTACION), 4, "Z")
    for o in objetos:
        o.data.transform(giro)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta,
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=False,
        apply_scale_options="FBX_SCALE_ALL",
        bake_space_transform=False,
        axis_forward="Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        add_leaf_bones=False,
        bake_anim=False,
        embed_textures=False,
        path_mode="STRIP",
    )
    inv = giro.inverted()
    for o in objetos:
        o.data.transform(inv)
    return ruta
