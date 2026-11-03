"""
Renderiza el planeta de prueba A PARTIR DE LOS FBX EXPORTADOS (no de los datos en memoria): reimporta los 96 trozos
en Blender, con su posición guardada en el FBX, y los pinta con la textura de paleta. Así cada imagen comprueba
también que la exportación (nombres, posiciones, normales, UV) sale bien.

Antes de renderizar hace comprobaciones de ida y vuelta e imprime sus resultados:
  - la posición de cada trozo reimportado coincide con la de datos_piezas.json,
  - el tamaño de su caja envolvente coincide,
  - los vértices gemelos de trozos vecinos (los del borde) están en el mismo sitio: no hay grietas,
  - las normales reimportadas son unitarias y, en el mar, apuntan hacia fuera.

Imágenes:
  planeta               el planeta entero desde el espacio (con un mar y una atmósfera de referencia: NO se exportan)
  trozos                el planeta con cada trozo de un color, para ver cómo está partido
  primer_plano          vista cercana de la superficie con un maniquí R6 (5 studs) de escala y montañas al fondo
  primer_plano_malla    la misma vista con las aristas de los triángulos dibujadas

Uso:
    python modelos/planeta_prueba/herramientas/planeta_render.py --salida modelos/planeta_prueba
        [--vista planeta|trozos|primer_plano|todas] [--rapido]
"""

import argparse
import json
import math
import os
import sys
import tempfile
import time
from dataclasses import replace

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import terreno as T  # noqa: E402

RADIO_MAR = 2400.0


def a_blender(v):
    """Roblox (X, Y, Z) -> Blender (-X, Z, Y). Igual que en planeta_prueba.py."""
    v = np.asarray(v, dtype=np.float64)
    return np.stack([-v[..., 0], v[..., 2], v[..., 1]], axis=-1)


# --------------------------------------------------------------------------------------------------------------
# Escena
# --------------------------------------------------------------------------------------------------------------


def importar_trozos(bpy, carpeta: str, datos: dict):
    """Importa los FBX con los mismos ejes con los que se exportaron. Devuelve {nombre: objeto}."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "NONE"
    objetos = {}
    for p in datos["piezas"]:
        ruta = os.path.join(carpeta, "piezas", p["nombre"] + ".fbx")
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="Z", axis_up="Y")
        nuevos = [o for o in bpy.data.objects if o not in antes and o.type == "MESH"]
        assert len(nuevos) == 1, f"{p['nombre']}: el FBX debería traer exactamente una malla y trae {len(nuevos)}"
        objetos[p["nombre"]] = nuevos[0]
        assert nuevos[0].name == p["nombre"], f"el objeto se llama {nuevos[0].name}, no {p['nombre']}"
    return objetos


def comprobar_ida_y_vuelta(bpy, objetos: dict, datos: dict) -> None:
    from mathutils.kdtree import KDTree

    peor_pos = peor_tam = 0.0
    puntos = []
    dueno = []
    for k, p in enumerate(datos["piezas"]):
        o = objetos[p["nombre"]]
        esperado = a_blender(p["centro"])
        peor_pos = max(peor_pos, float(np.linalg.norm(np.array(o.location) - esperado)))
        co = np.empty(len(o.data.vertices) * 3, dtype=np.float32)
        o.data.vertices.foreach_get("co", co)
        co = co.reshape(-1, 3).astype(np.float64)
        mundo = co + np.array(o.location)
        # Tamaño en ejes de Roblox: (x, y, z)_Roblox = (-x, z, y)_Blender.
        ext = mundo.max(axis=0) - mundo.min(axis=0)
        peor_tam = max(peor_tam, float(np.abs(np.array([ext[0], ext[2], ext[1]]) - np.array(p["tamano"])).max()))
        puntos.append(mundo)
        dueno.append(np.full(len(mundo), k))
    print(f"[ok] ida y vuelta: error de posición {peor_pos:.4f} studs, error de tamaño {peor_tam:.4f} studs")

    # Vértices gemelos: los de trozos distintos que están a menos de 0,5 studs deben ser el mismo punto.
    todos = np.concatenate(puntos)
    due = np.concatenate(dueno)
    kd = KDTree(len(todos))
    for i, v in enumerate(todos):
        kd.insert(v, i)
    kd.balance()
    peor_gap, pares = 0.0, 0
    paso = max(1, len(todos) // 60000)  # una muestra basta: miles de vértices de borde
    for i in range(0, len(todos), paso):
        for _, j, dist in kd.find_range(todos[i], 0.5):
            if due[j] != due[i]:
                pares += 1
                peor_gap = max(peor_gap, dist)
    print(f"[ok] costuras: {pares} pares de vértices gemelos entre trozos, separación máxima {peor_gap:.5f} studs")

    # Normales reimportadas.
    o = objetos[datos["piezas"][0]["nombre"]]
    o.data.calc_loop_triangles()
    nrm = np.empty(len(o.data.corner_normals) * 3, dtype=np.float32)
    o.data.corner_normals.foreach_get("vector", nrm)
    nrm = nrm.reshape(-1, 3)
    print(f"[ok] normales: {len(nrm)} por esquina, longitud {np.linalg.norm(nrm, axis=1).min():.4f}..{np.linalg.norm(nrm, axis=1).max():.4f}")


def material_paleta(bpy, ruta_paleta: str):
    mat = bpy.data.materials.new("Planeta_paleta")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    img = bpy.data.images.load(ruta_paleta)
    img.colorspace_settings.name = "sRGB"
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tex.interpolation = "Linear"
    tex.extension = "EXTEND"  # en los bordes de la paleta no se repite: se estira
    uv = nt.nodes.new("ShaderNodeUVMap")
    uv.uv_map = "UVMap"
    nt.links.new(uv.outputs["UV"], tex.inputs["Vector"])
    nt.links.new(tex.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.93
    b.inputs["Specular IOR Level"].default_value = 0.15
    return mat


def pintar_trozos(bpy, objetos: dict, mat) -> None:
    viejos = set()
    for o in objetos.values():
        for m in o.data.materials:
            viejos.add(m)
        o.data.materials.clear()
        o.data.materials.append(mat)
    for m in viejos:
        if m and m.users == 0:
            bpy.data.materials.remove(m)


def oceano(bpy, padre):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=RADIO_MAR, segments=384, ring_count=192)
    o = bpy.context.active_object
    o.name = "Mar_referencia"
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new("Mar")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    pr = nt.nodes.new("ShaderNodeBsdfPrincipled")
    pr.inputs["Base Color"].default_value = (0.02, 0.19, 0.42, 1)
    pr.inputs["Roughness"].default_value = 0.06
    pr.inputs["Specular IOR Level"].default_value = 0.6
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    mezcla.inputs["Fac"].default_value = 0.62  # el fondo marino se ve a través: claro junto a la costa, oscuro lejos
    nt.links.new(tr.outputs["BSDF"], mezcla.inputs[1])
    nt.links.new(pr.outputs["BSDF"], mezcla.inputs[2])
    nt.links.new(mezcla.outputs["Shader"], salida.inputs["Surface"])
    o.data.materials.append(mat)
    o.parent = padre
    return o


def atmosfera(bpy, padre, grosor: float = 95.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=RADIO_MAR + grosor, segments=192, ring_count=96)
    o = bpy.context.active_object
    o.name = "Atmosfera_referencia"
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new("Atmosfera")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    brillo = nt.nodes.new("ShaderNodeMath")  # el resplandor crece hacia el borde (ángulo rasante): fresnel^p
    brillo.operation = "POWER"
    brillo.inputs[1].default_value = 1.6
    nt.links.new(lw.outputs["Fresnel"], brillo.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.30, 0.56, 1.0, 1)
    em.inputs["Strength"].default_value = 1.4
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(brillo.outputs["Value"], mezcla.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mezcla.inputs[1])
    nt.links.new(em.outputs["Emission"], mezcla.inputs[2])
    nt.links.new(mezcla.outputs["Shader"], salida.inputs["Surface"])
    o.data.materials.append(mat)
    # Solo se ve: no proyecta sombras ni ilumina (si no, rellenaría de luz el lado nocturno del planeta).
    for propiedad in ("visible_shadow", "visible_diffuse", "visible_glossy", "visible_transmission",
                      "visible_volume_scatter"):
        setattr(o, propiedad, False)
    o.parent = padre
    return o


def estrellas(ruta: str, n: int = 5200, semilla: int = 4) -> None:
    rng = np.random.default_rng(semilla)
    w, h = 4096, 2048
    img = np.zeros((h, w), dtype=np.float32)
    ys = rng.integers(0, h, n)
    xs = rng.integers(0, w, n)
    brillo = rng.pareto(2.2, n) * 0.25 + 0.12
    img[ys, xs] = np.minimum(brillo, 6.0)
    pil = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.9))
    rgb = np.array(pil, dtype=np.float32)[..., None] / 255.0 * 5.0
    tinte = rng.uniform(0.85, 1.0, (h, w, 3)).astype(np.float32) * np.array([0.9, 0.95, 1.0], dtype=np.float32)
    Image.fromarray((np.clip(rgb * tinte, 0, 1) * 255).astype(np.uint8)).save(ruta)


def mundo_espacio(bpy, ruta_estrellas: str) -> None:
    scn = bpy.context.scene
    scn.world = bpy.data.worlds.new("espacio")
    scn.world.use_nodes = True
    nt = scn.world.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputWorld")
    fondo = nt.nodes.new("ShaderNodeBackground")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(ruta_estrellas)
    fondo.inputs["Strength"].default_value = 1.0
    # Luz de relleno: en la realidad la atmósfera dispersa la luz hacia las sombras; aquí un azul muy tenue.
    suma = nt.nodes.new("ShaderNodeMix")
    suma.data_type = "RGBA"
    suma.blend_type = "ADD"
    suma.inputs["Factor"].default_value = 1.0
    suma.inputs["B"].default_value = (0.012, 0.018, 0.034, 1.0)
    nt.links.new(env.outputs["Color"], suma.inputs["A"])
    nt.links.new(suma.outputs["Result"], fondo.inputs["Color"])
    nt.links.new(fondo.outputs["Background"], salida.inputs["Surface"])


def mundo_cielo(bpy, direccion_sol) -> None:
    """Cielo de día. El disco solar se apaga: la luz directa la da la luz solar de la escena, con su dirección."""
    scn = bpy.context.scene
    scn.world = bpy.data.worlds.new("cielo")
    scn.world.use_nodes = True
    nt = scn.world.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputWorld")
    fondo = nt.nodes.new("ShaderNodeBackground")
    cielo = nt.nodes.new("ShaderNodeTexSky")
    cielo.sky_type = "HOSEK_WILKIE"
    cielo.sun_direction = tuple(direccion_sol)
    cielo.sun_disc = False
    cielo.turbidity = 2.2
    cielo.ground_albedo = 0.3
    fondo.inputs["Strength"].default_value = 2.4
    nt.links.new(cielo.outputs["Color"], fondo.inputs["Color"])
    nt.links.new(fondo.outputs["Background"], salida.inputs["Surface"])


def sol(bpy, desde, energia: float = 4.5):
    from mathutils import Vector

    luz = bpy.data.lights.new("sol", "SUN")
    luz.energy = energia
    luz.angle = math.radians(0.6)
    o = bpy.data.objects.new("sol", luz)
    bpy.context.scene.collection.objects.link(o)
    o.rotation_euler = (-Vector(desde)).normalized().to_track_quat("-Z", "Y").to_euler()
    return o


def camara(bpy, pos, mira_a, lente: float = 50.0):
    from mathutils import Vector

    d = bpy.data.cameras.new("cam")
    d.lens = lente
    d.clip_start, d.clip_end = 0.3, 100000.0
    o = bpy.data.objects.new("cam", d)
    bpy.context.scene.collection.objects.link(o)
    o.location = Vector(pos)
    o.rotation_euler = (Vector(mira_a) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = o
    return o


def ajustes_render(bpy, ancho: int, alto: int, muestras: int) -> None:
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = muestras
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = "OPENIMAGEDENOISE"
    scn.cycles.max_bounces = 4
    scn.render.resolution_x, scn.render.resolution_y = ancho, alto
    scn.render.resolution_percentage = 100
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.render.image_settings.file_format = "PNG"


# --------------------------------------------------------------------------------------------------------------
# Elegir un sitio bonito para el primer plano
# --------------------------------------------------------------------------------------------------------------


def buscar_vista(rel: T.Relieve, semilla: int = 3) -> dict:
    """
    Busca un sitio para el primer plano: un prado llano (el maniquí se ve y el suelo es transitable en 250 studs a la
    redonda) con una sierra VISIBLE delante. Con un radio de 2400 la superficie se curva rápido: lo que está a una
    distancia d queda d²/(2R) por debajo del plano del observador (a 600 studs, 75; a 900, 169). Por eso la altura de
    las montañas se compara descontando esa caída.
    """
    rng = np.random.default_rng(semilla)
    d = rng.normal(size=(40000, 3))
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    h = rel.altura(d)
    cand = np.where((h > 14.0) & (h < 45.0))[0]
    cand = rng.choice(cand, size=min(len(cand), 5000), replace=False)
    mejor, mejor_puntos = None, -1e9
    azimuts = np.linspace(0, 2 * np.pi, 24, endpoint=False)
    distancias = (60.0, 150.0, 250.0, 380.0, 500.0, 650.0, 800.0)
    for c in cand:
        dc = d[c]
        ref = np.array([1.0, 0, 0]) if abs(dc[1]) > 0.9 else np.array([0.0, 1, 0])
        t1 = np.cross(dc, ref)
        t1 /= np.linalg.norm(t1)
        t2 = np.cross(dc, t1)
        pts, info = [], []
        for dist in distancias:
            th = dist / RADIO_MAR
            for az in azimuts:
                pts.append(math.cos(th) * dc + math.sin(th) * (math.cos(az) * t1 + math.sin(az) * t2))
                info.append((dist, az))
        alt = rel.altura(np.array(pts))
        dist_ = np.array([i[0] for i in info])
        az_ = np.array([i[1] for i in info])
        cerca = np.abs(alt[dist_ <= 150.0] - h[c]).max()
        if cerca > 14.0:  # el suelo junto al maniquí tiene que ser llano
            continue
        visible = alt - dist_ ** 2 / (2 * RADIO_MAR) - (h[c] + 7.0)  # altura sobre el plano de los ojos, con curvatura
        for fase in range(len(azimuts)):
            az0 = azimuts[fase]
            delante = (np.abs(np.angle(np.exp(1j * (az_ - az0)))) < 0.5) & (dist_ >= 250)
            if not delante.any():
                continue
            v = visible[delante]
            # Se premia que haya cumbre visible alta, y que el encuadre también incluya laderas de otros colores.
            puntos = v.max() + 0.6 * np.degrees(np.arctan2(v.max(), dist_[delante][int(np.argmax(v))])) \
                + 25 * (alt[delante] > 110).mean() * 10 - 3 * cerca
            if puntos > mejor_puntos:
                mejor_puntos = puntos
                mejor = dict(direccion=dc.copy(), azimut=float(az0), t1=t1.copy(), t2=t2.copy(), puntos=float(puntos),
                             altura=float(h[c]), maxima=float(alt[delante].max()), visible=float(v.max()))
    return mejor


# --------------------------------------------------------------------------------------------------------------
# Muñeco de escala y materiales de apoyo
# --------------------------------------------------------------------------------------------------------------


def muneco_r6(bpy, base, hacia, padre=None):
    """Un maniquí R6 hecho de cajas, de 5 studs de alto (1 unidad de Blender = 1 stud), mirando hacia `hacia`."""
    from mathutils import Matrix, Vector

    colores = {"torso": (0.85, 0.38, 0.08), "piernas": (0.10, 0.22, 0.55), "piel": (0.95, 0.74, 0.55)}
    cajas = [  # (nombre, centro relativo (x, y, z), tamaño, color); z desde los pies; y mira hacia delante
        ("piernas", (0, 0, 1.0), (2, 1, 2), "piernas"),
        ("torso", (0, 0, 3.0), (2, 1, 2), "torso"),
        ("brazo_i", (-1.5, 0, 3.0), (1, 1, 2), "torso"),
        ("brazo_d", (1.5, 0, 3.0), (1, 1, 2), "torso"),
        ("cabeza", (0, 0, 4.5), (1.2, 1.2, 1.0), "piel"),
    ]
    angulo = math.atan2(hacia.y, hacia.x) - math.pi / 2  # el frente del muñeco es +Y local
    rot = Matrix.Rotation(angulo, 4, "Z")
    objetos = []
    for nombre, centro, tam, col in cajas:
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        o = bpy.context.active_object
        o.name = f"muneco_{nombre}"
        o.scale = tam
        o.matrix_world = Matrix.Translation(base) @ rot @ Matrix.Translation(Vector(centro)) @ Matrix.Diagonal((*tam, 1.0))
        mat = bpy.data.materials.new(f"muneco_{nombre}")
        mat.use_nodes = True
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (*colores[col], 1)
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.6
        o.data.materials.append(mat)
        objetos.append(o)
    return objetos


def material_con_malla(bpy, mat):
    """Copia del material de la paleta con las aristas de los triángulos dibujadas encima."""
    m = mat.copy()
    m.name = mat.name + "_malla"
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    origen = b.inputs["Base Color"].links[0].from_socket
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 1.3
    mezcla = nt.nodes.new("ShaderNodeMix")
    mezcla.data_type = "RGBA"
    mezcla.inputs["B"].default_value = (0.02, 0.02, 0.03, 1)
    nt.links.new(wire.outputs["Fac"], mezcla.inputs["Factor"])
    nt.links.new(origen, mezcla.inputs["A"])
    nt.links.new(mezcla.outputs["Result"], b.inputs["Base Color"])
    return m


def colores_por_trozo(bpy, objetos: dict) -> None:
    """Un color distinto por trozo (para ver el troceado)."""
    rng = np.random.default_rng(5)
    for o in objetos.values():
        mat = bpy.data.materials.new("trozo_" + o.name)
        mat.use_nodes = True
        h = rng.uniform(0, 1)
        r, g, b = (float(x) for x in __import__("colorsys").hsv_to_rgb(h, rng.uniform(0.45, 0.8), rng.uniform(0.65, 0.95)))
        mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (r, g, b, 1)
        mat.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
        o.data.materials.clear()
        o.data.materials.append(mat)


# --------------------------------------------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True, help="carpeta del planeta (con piezas/ y paleta_color.png)")
    ap.add_argument("--imagenes", default=None, help="dónde guardar los PNG (por defecto, la misma carpeta)")
    ap.add_argument("--vista", default="todas", choices=["planeta", "trozos", "primer_plano", "todas"])
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--muestras", type=int, default=0)
    ap.add_argument("--sin-comprobar", action="store_true")
    a = ap.parse_args()
    carpeta = os.path.abspath(a.salida)
    destino = os.path.abspath(a.imagenes or carpeta)
    os.makedirs(destino, exist_ok=True)
    with open(os.path.join(carpeta, "datos_piezas.json"), encoding="utf-8") as f:
        datos = json.load(f)

    import bpy
    from mathutils import Vector

    t0 = time.time()
    objetos = importar_trozos(bpy, carpeta, datos)
    print(f"[ok] importados {len(objetos)} FBX en {time.time() - t0:.0f} s")
    if not a.sin_comprobar:
        comprobar_ida_y_vuelta(bpy, objetos, datos)
    mat = material_paleta(bpy, os.path.join(carpeta, "paleta_color.png"))
    pintar_trozos(bpy, objetos, mat)

    rel = T.Relieve(replace(T.Parametros(), **{k: v for k, v in datos["parametros_relieve"].items()}))
    assert abs(rel.umbral - datos["umbral_continental"]) < 1e-9, "el relieve no coincide con el de los datos"

    padre = bpy.data.objects.new("Planeta", None)
    bpy.context.scene.collection.objects.link(padre)
    for o in objetos.values():
        o.parent = padre
    mar = oceano(bpy, padre)
    muestras = a.muestras or (24 if a.rapido else 128)
    res = (700, 700) if a.rapido else (1600, 1600)
    quiere = lambda *nombres: a.vista in nombres or a.vista == "todas"  # noqa: E731

    with tempfile.TemporaryDirectory() as tmp:
        if quiere("planeta", "trozos"):
            ruta_est = os.path.join(tmp, "estrellas.png")
            estrellas(ruta_est)
            mundo_espacio(bpy, ruta_est)
            direccion = Vector(a_blender(np.array([0.60, 0.337, -0.72])))
            direccion.normalize()
            cam = camara(bpy, direccion * 8300.0, (0, 0, 0), lente=50)
            # El Sol a ~55° de la cámara, a un lado y algo arriba: se ve el día, el terminador y la noche.
            lado = Vector((0, 0, 1)).cross(direccion).normalized()
            desde_sol = (direccion * 0.57 + lado * 0.80 + Vector((0, 0, 0.22))).normalized() * 20000
            s = sol(bpy, desde_sol, energia=4.2)
            ajustes_render(bpy, res[0], res[1], muestras)
            if quiere("planeta"):
                atm = atmosfera(bpy, padre)
                bpy.context.scene.render.filepath = os.path.join(destino, "render_planeta.png")
                bpy.ops.render.render(write_still=True)
                print("[ok] render_planeta.png")
                bpy.data.objects.remove(atm)
            if quiere("trozos"):
                # Despiece: cada trozo se aparta del centro 150 studs, para verlos uno a uno (y su grosor).
                mar.hide_render = True
                colores_por_trozo(bpy, objetos)
                originales = {}
                for p in datos["piezas"]:
                    o = objetos[p["nombre"]]
                    originales[o.name] = o.location.copy()
                    u = Vector(a_blender(np.array(p["centro"]))).normalized()
                    o.location = o.location + u * 150.0
                bpy.context.scene.render.filepath = os.path.join(destino, "render_trozos.png")
                bpy.ops.render.render(write_still=True)
                print("[ok] render_trozos.png")
                for nombre, loc in originales.items():
                    objetos[nombre].location = loc
                pintar_trozos(bpy, objetos, mat)
                mar.hide_render = False
            bpy.data.objects.remove(cam)
            bpy.data.objects.remove(s)

        if quiere("primer_plano"):
            vista = buscar_vista(rel)
            print(f"[info] vista elegida: altura {vista['altura']:.1f} studs, cumbre {vista['maxima']:.0f} studs ({vista['visible']:.0f} sobre los ojos), "
                  f"azimut {math.degrees(vista['azimut']):.0f}°")
            # Se gira el planeta para que el punto de vista quede en el polo norte: el cielo y la gravedad coinciden.
            d_blender = Vector(a_blender(vista["direccion"]))
            padre.rotation_mode = "QUATERNION"
            padre.rotation_quaternion = d_blender.rotation_difference(Vector((0, 0, 1)))
            bpy.context.view_layer.update()
            q = padre.rotation_quaternion
            t1, t2 = q @ Vector(a_blender(vista["t1"])), q @ Vector(a_blender(vista["t2"]))
            az = vista["azimut"]
            hacia = math.cos(az) * t1 + math.sin(az) * t2
            hacia.z = 0
            hacia.normalize()
            # Sol a ~55° a la derecha de la dirección de la vista y 32° sobre el horizonte: deja ver el relieve.
            az_sol = math.atan2(hacia.y, hacia.x) - math.radians(55)
            el_sol = math.radians(32)
            dir_sol = Vector((math.cos(el_sol) * math.cos(az_sol), math.cos(el_sol) * math.sin(az_sol), math.sin(el_sol)))
            sol(bpy, dir_sol * 20000, energia=3.4)
            mundo_cielo(bpy, dir_sol)
            mar.hide_render = False

            def altura_en(x: float, y: float) -> float:
                """Altura de la superficie bajo (x, y) del mundo ya girado, lanzando un rayo contra los trozos."""
                dg = bpy.context.evaluated_depsgraph_get()
                ok, loc, *_ = bpy.context.scene.ray_cast(dg, Vector((x, y, 4000.0)), Vector((0, 0, -1)))
                return loc.z if ok else RADIO_MAR

            def encuadre(cam_atras, cam_alto, delante_muneco, destino_adelante, destino_alto, fov, ancho, alto, con_muneco):
                """Coloca la cámara; si hay muñeco, la sube hasta que un rayo le llegue a la cabeza sin chocar."""
                base_muneco = Vector((0, 0, 0)) + hacia * delante_muneco
                base_muneco.z = altura_en(base_muneco.x, base_muneco.y)
                objs = muneco_r6(bpy, base_muneco, hacia) if con_muneco else []
                pos = -hacia * cam_atras
                pos.z = altura_en(pos.x, pos.y) + cam_alto
                if con_muneco:
                    cabeza = base_muneco + Vector((0, 0, 4.5))
                    for _ in range(14):
                        dg = bpy.context.evaluated_depsgraph_get()
                        v = cabeza - pos
                        ok, _loc, _nrm, _idx, tocado, _mtx = bpy.context.scene.ray_cast(
                            dg, pos, v.normalized(), distance=v.length - 0.5)
                        if not ok or "muneco" in tocado.name:
                            break
                        pos.z += 4.0
                mira = hacia * destino_adelante
                mira.z = altura_en(mira.x, mira.y) + destino_alto
                cam = camara(bpy, pos, mira, lente=18.0 / math.tan(math.radians(fov / 2)))
                ajustes_render(bpy, ancho, alto, muestras)
                return cam, objs

            ancho = 900 if a.rapido else 1600
            if quiere("primer_plano"):
                cam, objs = encuadre(14.0, 7.0, 12.0, 90.0, 12.0, 64.0, ancho, int(ancho * 0.62), True)
                bpy.context.scene.render.filepath = os.path.join(destino, "render_primer_plano.png")
                bpy.ops.render.render(write_still=True)
                print("[ok] render_primer_plano.png")
                malla = material_con_malla(bpy, mat)
                for o in objetos.values():
                    o.data.materials.clear()
                    o.data.materials.append(malla)
                bpy.context.scene.render.filepath = os.path.join(destino, "render_primer_plano_malla.png")
                bpy.ops.render.render(write_still=True)
                print("[ok] render_primer_plano_malla.png")
                pintar_trozos(bpy, objetos, mat)
                bpy.data.objects.remove(cam)
                for o in objs:
                    bpy.data.objects.remove(o)
    print(f"[ok] listo en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
