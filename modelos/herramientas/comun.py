"""
Utilidades comunes para generar los modelos 3D del juego con Blender sin pantalla (bpy).

Lo comparten todos los modelos:
  * Escena vacía en metros, con la conversión de Roblox: 1 stud = 0,28 m (ESTUDIO). Los modelos se escriben en
    studs y se escalan a metros al crearlos, así llegan a Studio con el tamaño pensado.
  * Materiales Principled sencillos (color, rugosidad, metal, emisión).
  * Horneado de texturas (color con oclusión ambiental y mapa de normales) para usarlas en una SurfaceAppearance.
  * Render con Cycles en CPU desde varios ángulos + vista de malla, y montaje de la hoja de contactos con Pillow.
  * Exportación FBX con los ejes de Roblox: el modelo mira a -Y en Blender y a -Z en el FBX (el "delante" de Roblox).
"""

import math
import os

import bpy  # bpy primero: bmesh y mathutils vienen con él
import bmesh
from mathutils import Matrix, Vector
from PIL import Image, ImageDraw, ImageFont

ESTUDIO = 0.28  # metros por stud

# --------------------------------------------------------------------------------------------------------------
# Escena y utilidades de malla
# --------------------------------------------------------------------------------------------------------------


def escena_vacia():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0
    scn.world = bpy.data.worlds.new("mundo")
    return scn


def objeto_desde_bmesh(nombre, bm, materiales=(), coleccion=None):
    """Crea un objeto de malla a partir de un bmesh (en studs) y lo escala a metros (escala aplicada)."""
    bmesh.ops.scale(bm, vec=Vector((ESTUDIO, ESTUDIO, ESTUDIO)), verts=bm.verts)
    malla = bpy.data.meshes.new(nombre)
    bm.to_mesh(malla)
    bm.free()
    obj = bpy.data.objects.new(nombre, malla)
    (coleccion or bpy.context.scene.collection).objects.link(obj)
    for m in materiales:
        malla.materials.append(m)
    return obj


def triangulos(obj):
    """Triángulos de la malla final (con modificadores)."""
    dep = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dep)
    m = ev.to_mesh()
    n = sum(len(p.vertices) - 2 for p in m.polygons)
    ev.to_mesh_clear()
    return n


def aplicar_modificadores(obj):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


def sombreado_suave(obj, angulo=40):
    """Normales suaves con corte por ángulo: las aristas duras se ven duras y las curvas, lisas."""
    malla = obj.data
    for p in malla.polygons:
        p.use_smooth = True
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(angulo))
    aplicar_modificadores(obj)


def caja_limite(objetos):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objetos:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    return mn, mx


# --------------------------------------------------------------------------------------------------------------
# Materiales
# --------------------------------------------------------------------------------------------------------------


def material(nombre, color, rugosidad=0.5, metal=0.0, emision=None, fuerza_emision=0.0, alfa=1.0, transmision=0.0):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    b = mat.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*color, 1.0)
    b.inputs["Roughness"].default_value = rugosidad
    b.inputs["Metallic"].default_value = metal
    if emision is not None:
        b.inputs["Emission Color"].default_value = (*emision, 1.0)
        b.inputs["Emission Strength"].default_value = fuerza_emision
    if transmision:
        b.inputs["Transmission Weight"].default_value = transmision
    if alfa < 1.0:
        b.inputs["Alpha"].default_value = alfa
    mat.diffuse_color = (*color, 1.0)  # el color que exporta el FBX si no hay textura
    return mat


def srgb(hexa):
    """'#RRGGBB' -> color lineal (lo que usan los nodos de Blender)."""
    hexa = hexa.lstrip("#")
    c = [int(hexa[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# --------------------------------------------------------------------------------------------------------------
# Horneado de texturas (para SurfaceAppearance en Roblox)
# --------------------------------------------------------------------------------------------------------------


def desplegar_uv(obj, margen=0.02, angulo=66):
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(angulo), island_margin=margen, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")


def _preparar_cycles(muestras=16):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = muestras
    return scn


def hornear(baja, alta=None, tam=1024, ruta_color=None, ruta_normal=None, con_oclusion=True, extrusion=0.04,
            muestras=24, distancia_oclusion=0.7):
    """
    Hornea texturas sobre `baja` (que ya tiene UV y un material único):
      * color: el color base de `alta` (o de la propia `baja`) multiplicado por una oclusión ambiental suave.
      * normal: el relieve de `alta` sobre `baja` (solo si hay `alta`).
    Al terminar, `baja` queda con un material nuevo que usa esas texturas, listo para exportar y renderizar.
    Devuelve el material nuevo.
    """
    scn = _preparar_cycles(muestras)
    fuente = alta or baja

    def imagen(nombre, color=True):
        # 8 bits también para las normales: Roblox no usa más y el PNG pesa la cuarta parte.
        img = bpy.data.images.new(nombre, tam, tam, alpha=False, float_buffer=False)
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return img

    def nodo_destino(img):
        # Blender hornea en el nodo de imagen activo de cada material de `baja`.
        for slot in baja.material_slots:
            nt = slot.material.node_tree
            n = nt.nodes.get("destino_horneado") or nt.nodes.new("ShaderNodeTexImage")
            n.name = "destino_horneado"
            n.image = img
            nt.nodes.active = n

    def ejecutar(tipo, **kw):
        bpy.ops.object.select_all(action="DESELECT")
        if alta:
            alta.select_set(True)
        baja.select_set(True)
        bpy.context.view_layer.objects.active = baja
        bpy.ops.object.bake(type=tipo, use_selected_to_active=alta is not None, cage_extrusion=extrusion,
                            margin=8, **kw)

    def ocultar_otros(lista_visibles):
        estado = {}
        for o in scn.objects:
            estado[o] = o.hide_render
            if o.type == "MESH" and o not in lista_visibles:
                o.hide_render = True
        return estado

    estado = ocultar_otros([baja] + ([alta] if alta else []))
    if alta:
        alta.hide_render = False

    # 1) Color base (sin luz).
    img_color = imagen(f"{baja.name}_color")
    nodo_destino(img_color)
    scn.render.bake.use_pass_direct = False
    scn.render.bake.use_pass_indirect = False
    scn.render.bake.use_pass_color = True
    ejecutar("DIFFUSE", pass_filter={"COLOR"})

    # 2) Oclusión ambiental (de la malla alta, que tiene las grietas).
    if con_oclusion:
        img_ao = imagen(f"{baja.name}_ao", color=False)
        nodo_destino(img_ao)
        scn.world.light_settings.distance = distancia_oclusion
        ejecutar("AO")
        _multiplicar_ao(img_color, img_ao, fuerza=0.75)

    # 3) Normales.
    img_normal = None
    if alta:
        img_normal = imagen(f"{baja.name}_normal", color=False)
        nodo_destino(img_normal)
        ejecutar("NORMAL", normal_space="TANGENT")

    for o, h in estado.items():
        o.hide_render = h

    if ruta_color:
        img_color.filepath_raw = ruta_color
        img_color.file_format = "PNG"
        img_color.save()
    if img_normal is not None and ruta_normal:
        img_normal.filepath_raw = ruta_normal
        img_normal.file_format = "PNG"
        img_normal.save()

    # Material final con las texturas horneadas (lo que verá Roblox).
    rug = 0.8
    met = 0.0
    src = fuente.material_slots[0].material if fuente.material_slots else None
    if src and src.node_tree.nodes.get("Principled BSDF"):
        b = src.node_tree.nodes["Principled BSDF"]
        rug = b.inputs["Roughness"].default_value
        met = b.inputs["Metallic"].default_value
    mat = bpy.data.materials.new(f"{baja.name}_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Roughness"].default_value = rug
    b.inputs["Metallic"].default_value = met
    tc = nt.nodes.new("ShaderNodeTexImage")
    tc.image = img_color
    nt.links.new(tc.outputs["Color"], b.inputs["Base Color"])
    if img_normal is not None:
        tn = nt.nodes.new("ShaderNodeTexImage")
        tn.image = img_normal
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    baja.data.materials.clear()
    baja.data.materials.append(mat)
    for p in baja.data.polygons:
        p.material_index = 0
    return mat


def _multiplicar_ao(img_color, img_ao, fuerza=0.75):
    import numpy as np

    w, h = img_color.size
    c = np.array(img_color.pixels[:], dtype=np.float32).reshape(h, w, 4)
    a = np.array(img_ao.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., :1]
    # AO suave: no oscurece del todo, solo las grietas y los huecos.
    factor = 1.0 - fuerza * (1.0 - np.clip(a, 0, 1)) ** 1.3
    c[..., :3] *= factor
    img_color.pixels.foreach_set(c.ravel())
    img_color.update()


# --------------------------------------------------------------------------------------------------------------
# Render y hoja de contactos
# --------------------------------------------------------------------------------------------------------------

# Vistas (azimut en grados desde el frente, que es -Y; elevación en grados). El frente del modelo mira a la cámara.
VISTAS_ESTANDAR = [
    ("Frente", 0, 8),
    ("3/4 delantera", -40, 22),
    ("Lateral", -90, 6),
    ("3/4 trasera", -140, 24),
    ("Detrás", 180, 10),
    ("Arriba", 0, 88),
    ("Contrapicado", 35, -28),
]


def _fuente(tam, negrita=True):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrita else \
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    if os.path.exists(ruta):
        return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default(tam)


def preparar_estudio(tono_fondo=(0.035, 0.04, 0.055), suelo=True, z_suelo=0.0, luz_clave=900, mundo=0.35):
    """Estudio de fotografía: fondo oscuro degradado, luz clave, de relleno y contraluz, y suelo que recibe sombra."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    if scn.world is None:
        scn.world = bpy.data.worlds.new("mundo")
    scn.world.use_nodes = True
    nt = scn.world.node_tree
    fondo = nt.nodes["Background"]
    fondo.inputs["Color"].default_value = (*tono_fondo, 1)
    fondo.inputs["Strength"].default_value = mundo

    def luz(nombre, tipo, energia, pos, color=(1, 1, 1), tam=3.0):
        d = bpy.data.lights.new(nombre, tipo)
        d.energy = energia
        d.color = color
        if tipo == "AREA":
            d.size = tam
        if tipo == "SPOT":
            # Foco muy abierto y difuso: una luz de área no ilumina detrás de su plano y deja una línea en el suelo.
            d.spot_size = math.radians(150)
            d.spot_blend = 1.0
            d.shadow_soft_size = tam / 2
        o = bpy.data.objects.new(nombre, d)
        o.location = pos
        scn.collection.objects.link(o)
        c = o.constraints.new("TRACK_TO")
        c.target = _mira()
        c.track_axis = "TRACK_NEGATIVE_Z"
        c.up_axis = "UP_Y"
        o["luz_estudio"] = True
        return o

    luz("clave", "SPOT", luz_clave * 2.2, (-4.0, -5.0, 6.0), (1.0, 0.96, 0.9), 4)
    luz("relleno", "SPOT", luz_clave * 0.8, (5.5, -3.5, 2.5), (0.75, 0.85, 1.0), 6)
    luz("contra", "SPOT", luz_clave * 1.8, (2.0, 6.0, 5.0), (0.8, 0.9, 1.0), 3)
    luz("rebote", "AREA", luz_clave * 0.12, (0.0, -1.0, -5.0), (0.85, 0.85, 0.9), 8)  # para las vistas desde abajo

    if suelo:
        bpy.ops.mesh.primitive_plane_add(size=4000, location=(0, 0, z_suelo))
        s = bpy.context.active_object
        s.name = "Suelo_estudio"
        m = material("suelo_estudio", (0.05, 0.055, 0.07), rugosidad=1.0)
        m.node_tree.nodes["Principled BSDF"].inputs["Specular IOR Level"].default_value = 0.0  # sin brillo rasante
        s.data.materials.append(m)
        s["estudio"] = True
    return scn


def _mira():
    o = bpy.data.objects.get("Mira_estudio")
    if o is None:
        o = bpy.data.objects.new("Mira_estudio", None)
        bpy.context.scene.collection.objects.link(o)
    return o


def _material_malla():
    m = bpy.data.materials.get("vista_malla")
    if m:
        return m
    m = bpy.data.materials.new("vista_malla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 1.1
    base = nt.nodes.new("ShaderNodeBsdfDiffuse")
    base.inputs["Color"].default_value = (0.45, 0.47, 0.52, 1)
    linea = nt.nodes.new("ShaderNodeEmission")
    linea.inputs["Color"].default_value = (0.2, 0.85, 1.0, 1)
    linea.inputs["Strength"].default_value = 1.6
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wire.outputs["Fac"], mezcla.inputs["Fac"])
    nt.links.new(base.outputs["BSDF"], mezcla.inputs[1])
    nt.links.new(linea.outputs["Emission"], mezcla.inputs[2])
    nt.links.new(mezcla.outputs["Shader"], salida.inputs["Surface"])
    return m


def renderizar_vistas(objetos, carpeta, vistas=None, tam=460, muestras=48, con_malla=True, margen=1.12, lente=55,
                      centro=None, prefijo=""):
    """Renderiza `objetos` desde cada vista (y una vista de malla). Devuelve [(nombre, ruta_png)]."""
    scn = bpy.context.scene
    scn.cycles.samples = muestras
    scn.render.resolution_x = scn.render.resolution_y = tam
    scn.render.film_transparent = False
    vistas = vistas or VISTAS_ESTANDAR
    os.makedirs(carpeta, exist_ok=True)

    # Solo se ven los objetos pedidos (y el estudio).
    visibles = {}
    for o in scn.objects:
        if o.type == "MESH" and not o.get("estudio"):
            visibles[o] = o.hide_render
            o.hide_render = o not in objetos

    mn, mx = caja_limite(objetos)
    c = centro if centro is not None else (mn + mx) / 2
    radio = (mx - mn).length / 2
    _mira().location = c

    # Las luces del estudio están pensadas para un modelo de ~3 m: con uno más grande se alejan y ganan potencia
    # en proporción, para que un edificio se ilumine igual que una nave.
    k = max(1.0, radio / 1.6)
    for o in scn.objects:
        if o.get("luz_estudio"):
            if "pos_base" not in o:
                o["pos_base"] = list(o.location)
                o["energia_base"] = o.data.energy
            o.location = c + Vector(o["pos_base"]) * k
            o.data.energy = o["energia_base"] * k * k

    cam_d = bpy.data.cameras.new("cam_hoja")
    cam_d.lens = lente
    cam_d.clip_end = 10000
    cam = bpy.data.objects.new("cam_hoja", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    fov = 2 * math.atan(18 / lente)  # sensor de 36 mm
    dist = radio * margen / math.sin(fov / 2)

    rutas = []
    lista = list(vistas) + ([("Malla", -40, 22)] if con_malla else [])
    for nombre, az, el in lista:
        a, e = math.radians(az), math.radians(el)
        direccion = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = c + direccion * dist
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        scn.view_layers[0].material_override = _material_malla() if nombre == "Malla" else None
        suelo = bpy.data.objects.get("Suelo_estudio")
        if suelo:
            suelo.hide_render = el < 0 or nombre == "Malla"
        ruta = os.path.join(carpeta, f"{prefijo}{nombre.replace('/', '-').replace(' ', '_')}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        rutas.append((nombre, ruta))
    scn.view_layers[0].material_override = None
    bpy.data.objects.remove(cam)
    for o, h in visibles.items():
        o.hide_render = h
    return rutas


def montar_hoja(filas, salida, titulo, notas=(), columnas=4, etiquetas_fila=None):
    """
    filas: lista de listas [(nombre, ruta_png)]. Si hay una sola fila larga se reparte en `columnas`.
    etiquetas_fila: texto opcional a la izquierda de cada fila (por ejemplo el nombre de cada roca).
    """
    if len(filas) == 1:
        unica = filas[0]
        filas = [unica[i : i + columnas] for i in range(0, len(unica), columnas)]
        etiquetas_fila = None
    tam = Image.open(filas[0][0][1]).size[0]
    ncol = max(len(f) for f in filas)
    izq = 170 if etiquetas_fila else 0
    cab = 64 + 20 * len(notas)
    hoja = Image.new("RGB", (izq + ncol * tam, cab + len(filas) * tam), (16, 18, 24))
    d = ImageDraw.Draw(hoja)
    d.text((14, 10), titulo, fill=(255, 214, 102), font=_fuente(26))
    for i, n in enumerate(notas):
        d.text((16, 48 + i * 20), n, fill=(210, 214, 224), font=_fuente(15, negrita=False))
    for j, fila in enumerate(filas):
        y = cab + j * tam
        if etiquetas_fila:
            for k, linea in enumerate(etiquetas_fila[j].split("\n")):
                d.text((12, y + tam // 2 - 24 + k * 22), linea, fill=(255, 255, 255) if k == 0 else (180, 186, 200),
                       font=_fuente(17 if k == 0 else 14, negrita=k == 0))
        for i, (nombre, ruta) in enumerate(fila):
            x = izq + i * tam
            hoja.paste(Image.open(ruta).convert("RGB"), (x, y))
            d.rectangle((x, y, x + tam - 1, y + tam - 1), outline=(40, 44, 56))
            d.text((x + 10, y + 8), nombre, fill=(255, 255, 255), font=_fuente(16))
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    hoja.save(salida)
    print("[ok] hoja:", salida)
    return salida


# --------------------------------------------------------------------------------------------------------------
# Exportación FBX para Roblox
# --------------------------------------------------------------------------------------------------------------


def exportar_fbx(ruta, objetos, armature=None, incrustar_texturas=True):
    """
    FBX para el importador 3D de Roblox:
      * Ejes: arriba = Y, delante = Z. El modelo mira a -Y en Blender y queda mirando a -Z, el delante de Roblox.
      * Escala de unidades aplicada (metros): con 1 stud = 0,28 m llega a Studio con el tamaño pensado en studs.
      * Sin huesos hoja extra y con las texturas incrustadas (y copiadas al lado) para que el importador las encuentre.
    """
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos:
        o.select_set(True)
    if armature is not None:
        armature.select_set(True)
    bpy.context.view_layer.objects.active = armature or objetos[0]
    tipos = {"MESH"} | ({"ARMATURE"} if armature is not None else set())
    bpy.ops.export_scene.fbx(
        filepath=ruta,
        use_selection=True,
        object_types=tipos,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        bake_space_transform=False,
        axis_forward="Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        armature_nodetype="NULL",
        use_armature_deform_only=True,
        bake_anim=False,
        embed_textures=incrustar_texturas,
        path_mode="COPY" if incrustar_texturas else "AUTO",
    )
    print("[ok] FBX:", ruta)
    return ruta


def eliminar_estudio():
    for o in list(bpy.data.objects):
        if o.get("estudio") or o.get("luz_estudio") or o.name in ("Mira_estudio",):
            bpy.data.objects.remove(o)
