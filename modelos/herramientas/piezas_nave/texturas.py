"""
Texturas PBR de las piezas: se hornean en Blender los datos de la superficie y se pinta el atlas con numpy.

1. Con Cycles se hornean en la UV de la pieza: la posición (studs), la normal (espacio del objeto), la ranura de
   material de cada píxel y la oclusión ambiental.
2. Con esos mapas, numpy pinta el atlas como lo haría un artista con máscaras: paneles con juntas, remaches, mugre
   en los huecos, chorretones, arañazos, bordes gastados, marcas de escuadrón, juntas que brillan, escamas...
3. Del mapa de alturas sale el mapa de normales (espacio tangente, convención OpenGL, la que usa Roblox).

Salen: color (sRGB), normal, rugosidad, metal y, si algo brilla, emisión. Todos de 1024 × 1024.
"""

import math
import os

import bpy
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import datos


def lineal(hexa):
    hexa = hexa.lstrip("#")
    c = np.array([int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)], dtype=np.float32)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4).astype(np.float32)


def a_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(c, 1 / 2.4) - 0.055)


# --------------------------------------------------------------------------------------------------------------
# Ruido (numpy)
# --------------------------------------------------------------------------------------------------------------

def _hash(ix, iy, iz, semilla=0):
    h = (ix.astype(np.int64) * 73856093) ^ (iy.astype(np.int64) * 19349663) ^ \
        (iz.astype(np.int64) * 83492791) ^ np.int64(semilla * 2654435761 % (2 ** 31))
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    return ((h & 0xFFFFFF).astype(np.float32)) / np.float32(0x1000000)


def ruido(p, escala, semilla=0):
    """Ruido de valor 3D suave en [0, 1]. `p` (n, 3); `escala` escalar o (3,)."""
    q = p * np.asarray(escala, dtype=np.float32)
    i = np.floor(q)
    f = q - i
    u = f * f * (3 - 2 * f)
    i = i.astype(np.int64)
    res = np.zeros(len(p), dtype=np.float32)
    for dx in (0, 1):
        wx = u[:, 0] if dx else 1 - u[:, 0]
        for dy in (0, 1):
            wy = u[:, 1] if dy else 1 - u[:, 1]
            for dz in (0, 1):
                wz = u[:, 2] if dz else 1 - u[:, 2]
                res += wx * wy * wz * _hash(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, semilla)
    return res


def fbm(p, escala, octavas=4, semilla=0, ganancia=0.5):
    tot = np.zeros(len(p), dtype=np.float32)
    amp, norm = 1.0, 0.0
    esc = np.asarray(escala, dtype=np.float32)
    for k in range(octavas):
        tot += amp * ruido(p, esc * (2.03 ** k), semilla + 17 * k)
        norm += amp
        amp *= ganancia
    return tot / norm


def voronoi(p, escala, semilla=0):
    """F1, F2 (distancias en unidades de celda) y un valor aleatorio por celda."""
    q = p * escala
    i = np.floor(q).astype(np.int64)
    f1 = np.full(len(p), 9.0, dtype=np.float32)
    f2 = np.full(len(p), 9.0, dtype=np.float32)
    idc = np.zeros(len(p), dtype=np.float32)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cx, cy, cz = i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz
                fx = cx + _hash(cx, cy, cz, semilla + 1)
                fy = cy + _hash(cx, cy, cz, semilla + 2)
                fz = cz + _hash(cx, cy, cz, semilla + 3)
                d = np.sqrt((q[:, 0] - fx) ** 2 + (q[:, 1] - fy) ** 2 + (q[:, 2] - fz) ** 2)
                menor = d < f1
                f2 = np.where(menor, f1, np.minimum(f2, d))
                idc = np.where(menor, _hash(cx, cy, cz, semilla + 4), idc)
                f1 = np.where(menor, d, f1)
    return f1, f2, idc


def suave(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------------------------------------------
# Horneado de los datos de la superficie
# --------------------------------------------------------------------------------------------------------------

def _imagen(nombre, tam, flotante):
    img = bpy.data.images.new(nombre, tam, tam, alpha=True, float_buffer=flotante)
    img.colorspace_settings.name = "Non-Color"
    img.generated_color = (0, 0, 0, 0)
    return img


def _pixeles(img):
    w, h = img.size
    a = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(a)
    return a.reshape(h, w, 4)


def hornear_datos(obj, tam, muestras_ao=24, distancia_ao=1.2):
    """Hornea posición, normal, ranura y oclusión. Devuelve dict de arrays (h, w, ...) y la caja del objeto."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.render.bake.margin = 6
    scn.render.bake.margin_type = "EXTEND"

    mn = np.array([min(v.co[k] for v in obj.data.vertices) for k in range(3)], dtype=np.float32) - 0.01
    mx = np.array([max(v.co[k] for v in obj.data.vertices) for k in range(3)], dtype=np.float32) + 0.01
    ext = mx - mn

    imgs = {k: _imagen(f"{obj.name}_{k}", tam, True) for k in ("pos", "nrm", "id")}
    imgs["ao"] = _imagen(f"{obj.name}_ao", tam, False)

    mats = [s.material for s in obj.material_slots]

    def preparar(paso):
        for idx, m in enumerate(mats):
            nt = m.node_tree
            nt.nodes.clear()
            out = nt.nodes.new("ShaderNodeOutputMaterial")
            img = nt.nodes.new("ShaderNodeTexImage")
            img.image = imgs[paso]
            nt.nodes.active = img
            if paso == "ao":
                b = nt.nodes.new("ShaderNodeBsdfDiffuse")
                nt.links.new(b.outputs[0], out.inputs["Surface"])
                continue
            em = nt.nodes.new("ShaderNodeEmission")
            nt.links.new(em.outputs[0], out.inputs["Surface"])
            if paso == "id":
                em.inputs["Color"].default_value = ((idx + 0.5) / 64.0, 0, 0, 1)
                continue
            tc = nt.nodes.new("ShaderNodeTexCoord")
            if paso == "pos":
                sub = nt.nodes.new("ShaderNodeVectorMath")
                sub.operation = "SUBTRACT"
                sub.inputs[1].default_value = tuple(mn)
                div = nt.nodes.new("ShaderNodeVectorMath")
                div.operation = "DIVIDE"
                div.inputs[1].default_value = tuple(ext)
                nt.links.new(tc.outputs["Object"], sub.inputs[0])
                nt.links.new(sub.outputs[0], div.inputs[0])
                nt.links.new(div.outputs[0], em.inputs["Color"])
            else:
                mul = nt.nodes.new("ShaderNodeVectorMath")
                mul.operation = "MULTIPLY_ADD"
                mul.inputs[1].default_value = (0.5, 0.5, 0.5)
                mul.inputs[2].default_value = (0.5, 0.5, 0.5)
                nt.links.new(tc.outputs["Normal"], mul.inputs[0])
                nt.links.new(mul.outputs[0], em.inputs["Color"])

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    for paso in ("pos", "nrm", "id"):
        preparar(paso)
        scn.cycles.samples = 1
        bpy.ops.object.bake(type="EMIT", margin=6)
    preparar("ao")
    scn.cycles.samples = muestras_ao
    scn.world.light_settings.distance = distancia_ao
    bpy.ops.object.bake(type="AO", margin=6)

    pos = _pixeles(imgs["pos"])
    nrm = _pixeles(imgs["nrm"])
    ids = _pixeles(imgs["id"])
    ao = _pixeles(imgs["ao"])
    mascara = pos[..., 3] > 0.5
    res = {
        "pos": pos[..., :3] * ext + mn,
        "nrm": nrm[..., :3] * 2 - 1,
        "id": np.clip(np.floor(ids[..., 0] * 64.0), 0, 63).astype(np.int32),
        "ao": ao[..., 0],
        "mascara": mascara,
        "caja": (mn, mx),
    }
    for img in imgs.values():
        bpy.data.images.remove(img)
    return res


# --------------------------------------------------------------------------------------------------------------
# Pintado del atlas
# --------------------------------------------------------------------------------------------------------------

def _fuente(tam):
    for ruta in ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",):
        if os.path.exists(ruta):
            return ImageFont.truetype(ruta, tam)
    return ImageFont.load_default()


def _mascara_texto(texto, alto_px=128):
    f = _fuente(alto_px)
    caja = f.getbbox(texto)
    w, h = caja[2] - caja[0] + 8, caja[3] - caja[1] + 8
    img = Image.new("L", (w, h), 0)
    ImageDraw.Draw(img).text((4 - caja[0], 4 - caja[1]), texto, fill=255, font=f)
    return np.asarray(img, dtype=np.float32) / 255.0


def _muestrear(mascara, u, v):
    """Muestrea una máscara 2D con u, v en [0, 1] (fuera = 0). v = 0 abajo."""
    h, w = mascara.shape
    dentro = (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    x = np.clip((u * (w - 1)).astype(np.int32), 0, w - 1)
    y = np.clip(((1 - v) * (h - 1)).astype(np.int32), 0, h - 1)
    return np.where(dentro, mascara[y, x], 0.0)


def _juntas(P, N, tam, semilla):
    """
    Juntas de paneles: planos perpendiculares a cada eje cortan la superficie en líneas, como las chapas de un casco.
    Las de cada eje se ven solo donde la superficie no es paralela a ese plano. Las líneas de X y Z se escalonan
    entre bandas de Y, como un aparejo de ladrillo. Devuelve la distancia a la junta más cercana (studs), el eje de
    esa junta y un número aleatorio por panel.
    """
    sy, sx, sz = tam * 1.25, tam * 0.85, tam * 0.7
    banda = np.floor(P[:, 1] / sy)
    alea_b = _hash(banda.astype(np.int64), np.zeros_like(banda, dtype=np.int64), np.zeros_like(banda, dtype=np.int64),
                   semilla)
    fy = P[:, 1] / sy
    dy = np.abs(fy - np.round(fy)) * sy
    fx = P[:, 0] / sx + alea_b * 0.9
    dx = np.abs(fx - np.round(fx)) * sx
    fz = P[:, 2] / sz + alea_b * 0.7 + 0.31
    dz = np.abs(fz - np.round(fz)) * sz
    # peso: la junta de un eje solo se dibuja donde la normal no apunta a lo largo de ese eje
    big = 9.0
    dy = np.where(np.abs(N[:, 1]) < 0.7, dy, big)
    dx = np.where(np.abs(N[:, 0]) < 0.7, dx, big)
    dz = np.where(np.abs(N[:, 2]) < 0.7, dz, big)
    pila = np.stack([dy, dx, dz], axis=1)
    eje = np.argmin(pila, axis=1)
    d = np.min(pila, axis=1)
    celda = _hash(np.floor(fx).astype(np.int64), banda.astype(np.int64), np.floor(fz).astype(np.int64), semilla + 9)
    return d, eje, celda, (dy, dx, dz)


def pintar(datos_sup, constructor, tam_px):
    """Pinta color, rugosidad, metal, emisión y altura. Devuelve dict de imágenes (h, w, c) en lineal."""
    estilo = constructor.estilo
    det = dict(estilo["detalle"])
    det.update(constructor.info.get("detalle", {}))
    ranuras = constructor.ranuras
    M = datos_sup["mascara"]
    h, w = M.shape
    sel = np.ones((h, w), dtype=bool)  # se pintan también los márgenes (vienen extendidos)
    P = datos_sup["pos"][sel].astype(np.float32)
    N = datos_sup["nrm"][sel].astype(np.float32)
    N /= np.maximum(np.linalg.norm(N, axis=1, keepdims=True), 1e-6)
    S = datos_sup["id"][sel]
    AO = np.clip(datos_sup["ao"][sel], 0, 1)
    n = len(P)
    semilla = abs(hash(constructor.nombre)) % 9973
    mn, mx = datos_sup["caja"]
    ext = mx - mn
    tier = constructor.tier

    col = np.zeros((n, 3), dtype=np.float32)
    rug = np.zeros(n, dtype=np.float32)
    met = np.zeros(n, dtype=np.float32)
    emi = np.zeros((n, 3), dtype=np.float32)
    alt = np.zeros(n, dtype=np.float32)

    paleta = dict(estilo["ranuras"])
    paleta.update(constructor.info.get("paleta", {}))
    for k, v in constructor.colores_extra.items():
        if k in paleta:
            paleta[k] = (v, paleta[k][1], paleta[k][2])
    neon = lineal(constructor.colores_extra.get("neon", estilo["neon"]))
    neon2 = lineal(constructor.colores_extra.get("neon2", estilo["neon2"]))

    for i, nombre in enumerate(ranuras):
        m = S == i
        if nombre in paleta:
            hexa, r0, m0 = paleta[nombre]
        else:
            hexa, r0, m0 = paleta["primario"]
        col[m] = lineal(hexa)
        rug[m] = r0
        met[m] = m0

    es = {nombre: (S == i) for i, nombre in enumerate(ranuras)}
    vacio = np.zeros(n, dtype=bool)

    def ranura(*nombres):
        r = vacio.copy()
        for x in nombres:
            if x in es:
                r |= es[x]
        return r

    chapa = ranura("primario", "secundario", "oscuro", "acople")

    # ---- paneles y juntas --------------------------------------------------------------------------------------
    tam_panel = det["tam_panel"] * constructor.info.get("escala_panel", 1.0)
    d, eje, celda, (dy, dx, dz) = _juntas(P, N, tam_panel, semilla)
    ancho_junta = 0.035 if tier < 5 else 0.05
    junta = (1 - suave(ancho_junta * 0.4, ancho_junta, d)) * chapa
    alt -= junta * 0.03 * det["paneles"]
    col *= (1 - 0.55 * junta * det["paneles"])[:, None]
    rug += junta * 0.15
    # cada panel un tono un poco distinto (más en los tiers sucios)
    var = (celda - 0.5) * (0.10 * det["suciedad"] + 0.035)
    col *= (1 + var * chapa)[:, None]
    alt += (celda - 0.5) * 0.006 * chapa

    # ---- remaches ------------------------------------------------------------------------------------------
    if det["remaches"] > 0:
        paso = 0.24
        off = 0.11
        rr = 0.035
        rem = np.zeros(n, dtype=np.float32)
        for dist_eje, u in ((dy, P[:, 0] + P[:, 2]), (dx, P[:, 1] + P[:, 2]), (dz, P[:, 0] + P[:, 1])):
            du = (u / paso - np.round(u / paso)) * paso
            r = np.sqrt((dist_eje - off) ** 2 + du ** 2)
            rem = np.maximum(rem, 1 - suave(rr * 0.5, rr, r))
        rem *= chapa * det["remaches"]
        alt += rem * 0.018
        col *= (1 + 0.12 * rem)[:, None]
        rug -= rem * 0.1

    # ---- detalle por tier ----------------------------------------------------------------------------------------
    sucio = det["suciedad"]
    if sucio > 0:
        cav = 1 - AO
        manchas = fbm(P, 0.9, 4, semilla + 3)
        chorro = fbm(P * np.array([1, 1, 0.12], dtype=np.float32), 2.4, 3, semilla + 5)
        polvo = suave(0.45, 0.85, manchas) * 0.35 + suave(0.55, 0.9, chorro) * 0.4 + suave(0.15, 0.6, cav) * 0.7
        polvo = np.clip(polvo * sucio, 0, 1) * (1 - ranura("goma"))
        mugre = np.array([0.08, 0.07, 0.055], dtype=np.float32)
        col = col * (1 - polvo[:, None] * 0.6) + mugre * polvo[:, None] * 0.6
        rug += polvo * 0.25
        met -= polvo * 0.35
        # óxido en los huecos (solo tier 1)
        if tier == 1:
            oxido = suave(0.62, 0.8, fbm(P, 1.7, 4, semilla + 11)) * suave(0.2, 0.55, cav) * chapa
            col = col * (1 - oxido[:, None] * 0.7) + np.array([0.18, 0.07, 0.03], dtype=np.float32) * \
                oxido[:, None] * 0.7
            rug += oxido * 0.3
            met -= oxido * 0.5

    if det["rayones"] > 0:
        # arañazos: ruido muy estirado en dos direcciones
        r1 = ruido(P @ np.array([[0.8, 0.6, 0], [-0.6, 0.8, 0], [0, 0, 1]], dtype=np.float32).T,
                   np.array([28, 1.5, 1.5]), semilla + 21)
        r2 = ruido(P @ np.array([[1, 0, 0], [0, 0.7, 0.7], [0, -0.7, 0.7]], dtype=np.float32).T,
                   np.array([1.5, 26, 1.5]), semilla + 23)
        zona = suave(0.55, 0.75, fbm(P, 0.7, 2, semilla + 25))
        ray = (suave(0.86, 0.9, r1) + suave(0.87, 0.91, r2)) * zona * det["rayones"] * chapa
        ray = np.clip(ray, 0, 1)
        desnudo = lineal("#B8BCC2")
        col = col * (1 - ray[:, None] * 0.8) + desnudo * ray[:, None] * 0.8
        met = met * (1 - ray) + ray
        rug = rug * (1 - ray) + 0.3 * ray
        alt -= ray * 0.004

    # bordes gastados: donde la normal cambia rápido en el atlas y no es un hueco (se calcula fuera, ver abajo)
    bordes = constructor.info.get("_bordes")
    if bordes is not None:
        b = bordes[sel] * (AO > 0.6) * chapa
        b = np.clip(b * 1.4, 0, 1)
        if tier <= 2:
            desg = b * (0.7 if tier == 1 else 0.4)
            col = col * (1 - desg[:, None]) + lineal("#C6CACF") * desg[:, None]
            met = met * (1 - desg) + desg
            rug = rug * (1 - desg) + 0.35 * desg
        elif tier in (3, 4):
            # brillo fino en las aristas del metal pulido
            col *= (1 + 0.25 * b)[:, None]
            rug -= 0.12 * b

    # ---- marcas de escuadrón (tier 2) ------------------------------------------------------------------------------
    if det.get("marcas", 0) > 0:
        prim = ranura("primario")
        naranja = lineal(paleta["secundario"][0])
        yr = (P[:, 1] - mn[1]) / max(ext[1], 1e-3)  # 0 delante, 1 detrás
        # franja doble transversal
        f1 = (np.abs(yr - 0.22) < 0.025) | (np.abs(yr - 0.275) < 0.01)
        # chevrón en el lomo apuntando hacia delante
        xr = np.abs(P[:, 0]) / max(ext[0] * 0.5, 1e-3)
        chev = ((yr - 0.55 - xr * 0.18) % 0.09 < 0.035) & (yr > 0.5) & (yr < 0.75) & (N[:, 2] > 0.55)
        # número del escuadrón en los costados
        numero = constructor.info.get("numero", "%02d" % (semilla % 90 + 10))
        mtx = _mascara_texto(numero)
        alto_num = min(ext[2] * 0.45, 1.6)
        ancho_num = alto_num * mtx.shape[1] / mtx.shape[0]
        y0 = mn[1] + ext[1] * 0.36
        zc = (mn[2] + mx[2]) / 2
        lado = np.abs(N[:, 0]) > 0.55
        uu = np.where(N[:, 0] > 0, (y0 + ancho_num - P[:, 1]) / ancho_num, (P[:, 1] - y0) / ancho_num)
        vv = (P[:, 2] - (zc - alto_num / 2)) / alto_num
        num = _muestrear(mtx, uu, vv) * lado
        marca = (f1 | chev).astype(np.float32) * prim
        col = col * (1 - marca[:, None]) + naranja * marca[:, None]
        oscuro = lineal("#2A2E34")
        num = num * prim
        col = col * (1 - num[:, None]) + oscuro * num[:, None]
        rug += num * 0.05

    # ---- juntas que brillan (tier 3 y 4) y oro (tier 4) ---------------------------------------------------------------
    if det.get("lineas", 0) > 0:
        # solo juntas longitudinales (las de X y Z, que corren a lo largo de la nave): líneas aerodinámicas
        largo = (eje != 0)
        sel_l = celda < det["lineas"]
        lin = (1 - suave(0.006, 0.018, d)) * largo * sel_l * chapa
        color_l = np.where((celda < det["lineas"] * 0.5)[:, None] | (tier == 3), neon, neon2) if tier == 4 else neon
        emi += color_l * lin[:, None] * 2.2
        col = col * (1 - lin[:, None]) + color_l * lin[:, None] * 0.6
    if det.get("lineas_oro", 0) > 0:
        oro = lineal(paleta["secundario"][0])
        lo = (1 - suave(0.012, 0.03, d)) * (celda > 1 - det["lineas_oro"]) * ranura("primario")
        col = col * (1 - lo[:, None]) + oro * lo[:, None]
        met = met * (1 - lo) + lo
        rug = rug * (1 - lo) + 0.22 * lo
        alt += lo * 0.035  # el oro queda en relieve (molduras)

    # ---- alienígena (tier 5) -----------------------------------------------------------------------------------------
    if det.get("alien", 0) > 0:
        org = ranura("primario", "organico", "oscuro", "acople")
        f1, f2, idc = voronoi(P, 1.6, semilla + 31)
        borde = f2 - f1
        escama = 1 - suave(0.0, 0.16, borde)
        alt += (suave(0.0, 0.5, borde) * 0.03 - escama * 0.02) * org
        escala_v = 1.3 / max(1.0, float(np.max(ext)) / 12.0) ** 0.5
        vena = 1 - np.abs(fbm(P, escala_v, 4, semilla + 33) * 2 - 1)
        vena = suave(0.93, 0.985, vena) * org
        # irisado: el tono cambia con la orientación de la superficie
        fase = (N @ np.array([0.35, -0.55, 0.76], dtype=np.float32)) * 0.5 + 0.5
        fase = fase * 0.7 + fbm(P, 0.4, 2, semilla + 35) * 0.3
        c1 = lineal("#2A0F3E")
        c2 = lineal("#0F2A3E")
        c3 = lineal("#4A1A5A")
        iris = np.where((fase < 0.5)[:, None], c1 + (c2 - c1) * (fase[:, None] * 2),
                        c2 + (c3 - c2) * ((fase[:, None] - 0.5) * 2))
        base = np.where(es.get("organico", vacio)[:, None], col, iris)
        col = np.where(org[:, None], base * (0.8 + 0.4 * idc[:, None]), col)
        col *= (1 - 0.5 * escama * org)[:, None]
        c_vena = lineal(estilo["neon"])  # las venas siempre del púrpura del tier, aunque la pieza cambie su neón
        emi += c_vena * (vena * 1.8)[:, None]
        col = col * (1 - vena[:, None] * 0.5) + c_vena * vena[:, None] * 0.5
        rug = np.where(org, 0.22 + 0.2 * escama, rug)
        # nácar en la ranura secundaria
        sec = ranura("secundario")
        nac = fbm(P, 2.0, 3, semilla + 37)
        col = np.where(sec[:, None], col * (0.9 + 0.2 * nac[:, None]) +
                       lineal("#B0E8FF") * (0.08 * fase[:, None]), col)

    # ---- ranuras especiales -----------------------------------------------------------------------------------------
    if "aviso" in es:
        a = es["aviso"]
        raya = ((P[:, 0] + P[:, 1] + P[:, 2]) / 0.32) % 1.0 < 0.5
        if tier <= 2:
            col = np.where((a & raya)[:, None], lineal("#1A1A1C"), col)
        else:
            emi += neon * (a * 1.6)[:, None]
    if "tobera" in es:
        t = es["tobera"]
        calor = fbm(P, 1.4, 3, semilla + 41)
        tinte = np.where((calor < 0.5)[:, None], lineal("#4A3A6A"), lineal("#8A6A3A"))
        col = np.where(t[:, None], col * 0.7 + tinte * 0.3 * (0.6 + calor[:, None]), col)
        hollin = suave(0.3, 0.8, 1 - AO) * t
        col *= (1 - hollin * 0.7)[:, None]
        rug += hollin * 0.3
    if "metal" in es:
        mt = es["metal"]
        cep = ruido(P, np.array([40, 1.2, 40]), semilla + 43)
        rug = np.where(mt, rug + (cep - 0.5) * 0.12, rug)
    if "goma" in es:
        g = es["goma"]
        rug = np.where(g, 0.85 + (fbm(P, 6, 2, semilla) - 0.5) * 0.1, rug)
    if "pantalla" in es:
        p_ = es["pantalla"]
        # pantallas: rejilla de datos, barras y un borde brillante
        u = P[:, 0] + P[:, 1] * 0.5
        v = P[:, 2]
        filas = ((v / 0.09) % 1.0 < 0.35) & (ruido(np.stack([np.floor(u / 0.05), np.floor(v / 0.09),
                                                              np.zeros(n)], 1).astype(np.float32), 1.0, 7) > 0.45)
        rejilla = ((u / 0.25) % 1.0 < 0.06) | ((v / 0.25) % 1.0 < 0.06)
        brillo = (filas * 0.9 + rejilla * 0.5) * p_
        color_p = neon if tier >= 2 else lineal("#7DFF9A")
        emi += color_p * brillo[:, None] * 1.5
        col = col * (1 - brillo[:, None] * 0.5) + color_p * brillo[:, None] * 0.4
        rug = np.where(p_, 0.15, rug)
    if "asiento" in es:
        s = es["asiento"]
        acolch = suave(0.3, 0.5, np.abs(((P[:, 2] + P[:, 0]) / 0.3) % 1.0 - 0.5))
        alt += acolch * 0.01 * s
        col *= (1 - 0.15 * (1 - acolch) * s)[:, None]

    # oclusión horneada en el color (suave: Roblox ya hace la suya)
    col *= (0.55 + 0.45 * AO ** 0.8)[:, None]

    def lleno(arr, c):
        out = np.zeros((h, w, c), dtype=np.float32) if c > 1 else np.zeros((h, w), dtype=np.float32)
        out[sel] = arr
        return out

    return {
        "color": lleno(np.clip(col, 0, 1), 3),
        "rugosidad": lleno(np.clip(rug, 0.04, 1), 1),
        "metal": lleno(np.clip(met, 0, 1), 1),
        "emision": lleno(np.clip(emi, 0, 8), 3),
        "altura": lleno(alt, 1),
    }


def bordes_desde_normales(datos_sup):
    """Mapa de 'aristas': cuánto cambia la normal de un píxel a otro (en las aristas biseladas cambia mucho)."""
    N = datos_sup["nrm"]
    g = np.zeros(N.shape[:2], dtype=np.float32)
    for k in range(3):
        gy, gx = np.gradient(N[..., k])
        g += gx * gx + gy * gy
    g = np.sqrt(g)
    P = datos_sup["pos"]
    # quita los saltos entre islas (la posición también salta ahí)
    salto = np.zeros_like(g)
    for k in range(3):
        gy, gx = np.gradient(P[..., k])
        salto += gx * gx + gy * gy
    salto = np.sqrt(salto)
    paso = np.median(salto[datos_sup["mascara"]]) if datos_sup["mascara"].any() else 1.0
    g = np.where(salto > paso * 6, 0, g)
    return np.clip(g / 0.25, 0, 1), paso


def normales_desde_altura(altura, paso_studs, fuerza=1.0):
    """Mapa de normales en espacio tangente (OpenGL, verde hacia arriba) a partir de la altura en studs."""
    gy, gx = np.gradient(altura)
    gx = np.clip(gx / max(paso_studs, 1e-5), -3, 3) * fuerza
    gy = np.clip(gy / max(paso_studs, 1e-5), -3, 3) * fuerza
    nrm = np.stack([-gx, -gy, np.ones_like(gx)], axis=-1)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    return nrm * 0.5 + 0.5


def guardar(arr, ruta, modo):
    """Guarda un array de Blender (fila 0 abajo) como PNG (fila 0 arriba)."""
    a = np.flipud(arr)
    if modo == "RGB_SRGB":
        img = Image.fromarray((a_srgb(a) * 255 + 0.5).astype(np.uint8), "RGB")
    elif modo == "RGB":
        img = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "RGB")
    else:
        img = Image.fromarray((np.clip(a, 0, 1) * 255 + 0.5).astype(np.uint8), "L")
    img.save(ruta, optimize=True)
    return ruta


def texturizar(obj, constructor, carpeta_tex, tam=1024, muestras_ao=24):
    """Hornea, pinta y guarda el atlas de `obj`. Devuelve dict ranura_mapa -> ruta y si tiene emisión."""
    os.makedirs(carpeta_tex, exist_ok=True)
    escala = max(obj.dimensions)
    ds = hornear_datos(obj, tam, muestras_ao=muestras_ao, distancia_ao=min(2.5, max(0.6, escala * 0.08)))
    bordes, paso = bordes_desde_normales(ds)
    constructor.info["_bordes"] = bordes
    capas = pintar(ds, constructor, tam)
    constructor.info.pop("_bordes", None)
    nombre = constructor.nombre
    rutas = {}
    rutas["color"] = guardar(capas["color"], os.path.join(carpeta_tex, f"{nombre}_color.png"), "RGB_SRGB")
    nrm = normales_desde_altura(capas["altura"], paso, fuerza=1.0)
    rutas["normal"] = guardar(nrm, os.path.join(carpeta_tex, f"{nombre}_normal.png"), "RGB")
    rutas["rugosidad"] = guardar(capas["rugosidad"], os.path.join(carpeta_tex, f"{nombre}_rugosidad.png"), "L")
    rutas["metal"] = guardar(capas["metal"], os.path.join(carpeta_tex, f"{nombre}_metal.png"), "L")
    if capas["emision"].max() > 0.01:
        e = capas["emision"]
        rutas["emision"] = guardar(np.clip(e / 2.2, 0, 1), os.path.join(carpeta_tex, f"{nombre}_emision.png"),
                                   "RGB_SRGB")
    return rutas


def material_final(nombre, rutas, fuerza_emision=6.0):
    """Material de Blender con el atlas (para el render y para el FBX)."""
    mat = bpy.data.materials.new(f"{nombre}_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]

    def tex(ruta, color):
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = bpy.data.images.load(ruta, check_existing=True)
        n.image.colorspace_settings.name = "sRGB" if color else "Non-Color"
        return n

    nt.links.new(tex(rutas["color"], True).outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex(rutas["rugosidad"], False).outputs["Color"], b.inputs["Roughness"])
    nt.links.new(tex(rutas["metal"], False).outputs["Color"], b.inputs["Metallic"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex(rutas["normal"], False).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    if "emision" in rutas:
        nt.links.new(tex(rutas["emision"], True).outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = fuerza_emision
    return mat


def material_plano(nombre, tipo, hexa):
    """Material de las mallas sin atlas: neón, cristal, domo de escudo, llama."""
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    c = tuple(lineal(hexa)) + (1.0,)
    b.inputs["Base Color"].default_value = c
    mat.diffuse_color = c
    if tipo in ("neon", "neon2", "llama"):
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = 9.0 if tipo != "llama" else 7.0
        b.inputs["Roughness"].default_value = 0.4
    elif tipo == "cristal":
        b.inputs["Roughness"].default_value = 0.04
        b.inputs["Transmission Weight"].default_value = 0.85
        b.inputs["IOR"].default_value = 1.45
        b.inputs["Coat Weight"].default_value = 0.5
    elif tipo == "domo":
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = 1.2
        b.inputs["Alpha"].default_value = 0.18
        b.inputs["Roughness"].default_value = 0.1
        try:
            mat.surface_render_method = "BLENDED"
        except Exception:
            pass
    return mat
