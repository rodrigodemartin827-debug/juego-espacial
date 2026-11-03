"""
Planeta de prueba: una esfera de radio 2400 studs con relieve suave, partida en MeshParts de Roblox.

Qué hace este script, en orden:
  1. Construye la superficie como una «cubo-esfera»: 6 caras de un cubo, cada una dividida en K×K trozos de N×N
     cuadros, proyectadas sobre la esfera (reparto «de ángulos iguales», que deja los cuadros casi del mismo tamaño
     en todo el planeta, sin los polos pellizcados de una esfera UV).
  2. Pide a terreno.py la altura de cada vértice y su normal EXACTA (derivada del relieve, no de la malla): así el
     sombreado es liso y es idéntico a ambos lados de cada borde entre trozos.
  3. Cada trozo es un SÓLIDO CERRADO: la superficie con relieve, un fondo grueso (esfera de radio R-200, mucho más
     baja que el fondo del mar) y cuatro paredes. La colisión «PreciseConvexDecomposition» de Roblox trabaja con
     volúmenes: una lámina sin grosor se atraviesa más fácil.
  4. Genera una textura de paleta de 2 ejes (altura × pendiente) y da a cada vértice la coordenada UV de su color:
     playa, hierba, roca y nieve salen de la altura, y la roca asoma en las laderas empinadas.
  5. Exporta un FBX por trozo, con el nombre y la posición del trozo, y escribe los datos (JSON) y el script de Luau
     que los coloca en Workspace.

Todas las coordenadas están en el sistema de Roblox (Y arriba) y en studs. El FBX sigue la receta oficial de Roblox
para Blender: unidades de Blender = studs (Unit System: None), «FBX Unit Scale», delante Z y arriba Y.

Límites que respeta (ver README.md para las fuentes):
  - 20.000 triángulos por malla (documentación oficial de Roblox).
  - 2048 studs por eje (límite que cuentan los desarrolladores; no está en la documentación oficial que he podido
    leer, así que se deja margen y se avisa si un trozo pasa de LADO_MAXIMO).

Uso:
    python modelos/planeta_prueba/herramientas/planeta_prueba.py --salida modelos/planeta_prueba
        [--lado 4] [--cuadros 64] [--semilla 7] [--rapido] [--sin-fbx]
"""

import argparse
import json
import math
import os
import sys
import time
from dataclasses import asdict, replace

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import terreno as T  # noqa: E402

# --------------------------------------------------------------------------------------------------------------
# Datos ajustables
# --------------------------------------------------------------------------------------------------------------

RADIO = 2400.0  # radio del nivel del mar, en studs
PROFUNDIDAD_FONDO = 200.0  # el fondo de cada trozo está a RADIO - esto (por debajo del fondo del mar más hondo)

LIMITE_TRIANGULOS = 20000  # por malla: documentación oficial de Roblox
LIMITE_LADO = 2048.0  # por eje: lo que cuentan los desarrolladores (no oficial)
MARGEN_TRIANGULOS = 0.98  # se avisa por encima de este porcentaje del límite
MARGEN_LADO = 0.90

# Paleta (altura × pendiente). Las alturas son studs sobre el nivel del mar; las pendientes, grados.
ALTURA_MIN, ALTURA_MAX = -140.0, 200.0
PENDIENTE_MAX = 60.0
TAM_PALETA = 256

# Colores de la tierra llana según la altura: (altura, color sRGB). Entre dos puntos se mezcla linealmente.
COLORES_ALTURA = [
    (-140.0, "#26384a"),  # fondo marino hondo
    (-60.0, "#355b6f"),
    (-12.0, "#7e9a94"),  # aguas poco profundas (se ven a través del mar)
    (-1.0, "#bdb48f"),
    (0.0, "#cdbf8c"),  # playa
    (3.0, "#d2c48f"),
    (7.0, "#b3b66f"),  # hierba seca de transición
    (13.0, "#86ab57"),
    (30.0, "#62994a"),  # hierba
    (85.0, "#4f8a3f"),  # pradera frondosa
    (115.0, "#6d8451"),  # monte bajo
    (135.0, "#8b8668"),  # tundra
    (150.0, "#aaa593"),
    (200.0, "#bfbcb0"),
]
COLOR_ROCA_CLARA = "#8a8479"
COLOR_ROCA_OSCURA = "#5d584f"
COLOR_NIEVE = "#f1f4f6"
NIEVE_DESDE, NIEVE_PLENA = 118.0, 142.0  # altura a la que empieza y es completa la nieve
ROCA_DESDE, ROCA_PLENA = 27.0, 45.0  # pendiente (grados) a la que empieza y es completa la roca
NIEVE_ROCA_DESDE, NIEVE_ROCA_PLENA = 38.0, 54.0  # pendiente a la que la nieve se cae y deja ver la roca

# Variación para romper las curvas de nivel perfectas (en studs de altura y grados de pendiente).
RUIDO_ALTURA, RUIDO_PENDIENTE = 3.5, 2.5

CARAS = ("XP", "XN", "YP", "YN", "ZP", "ZN")
# (normal, eje a, eje b) de cada cara, con a × b = normal (orientación exterior).
EJES_CARA = {
    "XP": ((1, 0, 0), (0, 1, 0), (0, 0, 1)),
    "XN": ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "YP": ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    "YN": ((0, -1, 0), (1, 0, 0), (0, 0, 1)),
    "ZP": ((0, 0, 1), (1, 0, 0), (0, 1, 0)),
    "ZN": ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
}


# --------------------------------------------------------------------------------------------------------------
# Paleta
# --------------------------------------------------------------------------------------------------------------


def _hex(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def color_paleta(altura: np.ndarray, pendiente: np.ndarray) -> np.ndarray:
    """Color sRGB (n, 3) en [0, 1] de un punto de altura `altura` (studs) y pendiente `pendiente` (grados)."""
    xs = np.array([a for a, _ in COLORES_ALTURA])
    cs = np.stack([_hex(c) for _, c in COLORES_ALTURA])
    base = np.stack([np.interp(altura, xs, cs[:, k]) for k in range(3)], axis=-1)
    roca = _hex(COLOR_ROCA_CLARA)[None] * (1 - 0.35 * T.suavizar(pendiente, 38, 60)[..., None]) + \
        _hex(COLOR_ROCA_OSCURA)[None] * (0.35 * T.suavizar(pendiente, 38, 60)[..., None])
    en_roca = T.suavizar(pendiente, ROCA_DESDE, ROCA_PLENA)[..., None]
    # Bajo el agua no hay acantilados: se mantiene el color del fondo.
    en_roca = en_roca * T.suavizar(altura, -6.0, 2.0)[..., None]
    color = base * (1 - en_roca) + roca * en_roca
    nieve = (T.suavizar(altura, NIEVE_DESDE, NIEVE_PLENA) *
             (1 - T.suavizar(pendiente, NIEVE_ROCA_DESDE, NIEVE_ROCA_PLENA)))[..., None]
    return color * (1 - nieve) + _hex(COLOR_NIEVE)[None] * nieve


def escribir_paletas(carpeta: str) -> None:
    """Escribe la paleta (v = 0 abajo: llano) y una copia invertida en vertical por si Studio invierte la V."""
    s = TAM_PALETA
    alt = ALTURA_MIN + (np.arange(s) + 0.5) / s * (ALTURA_MAX - ALTURA_MIN)
    pen = (np.arange(s) + 0.5) / s * PENDIENTE_MAX
    A, P = np.meshgrid(alt, pen)  # filas = pendiente
    rgb = color_paleta(A.reshape(-1), P.reshape(-1)).reshape(s, s, 3)
    img = (np.clip(rgb, 0, 1) * 255 + 0.5).astype(np.uint8)
    # Imagen: la fila 0 es la de ARRIBA; la pendiente 0 (llano) va ABAJO (v = 0), como en Blender y en el FBX.
    Image.fromarray(img[::-1]).save(os.path.join(carpeta, "paleta_color.png"), optimize=True)
    Image.fromarray(img).save(os.path.join(carpeta, "paleta_color_v_invertida.png"), optimize=True)


def uv_paleta(altura: np.ndarray, pendiente: np.ndarray) -> np.ndarray:
    """Coordenadas UV (n, 2) del centro del texel de la paleta que corresponde a (altura, pendiente)."""
    s = TAM_PALETA
    u = np.clip((altura - ALTURA_MIN) / (ALTURA_MAX - ALTURA_MIN), 0.0, 1.0)
    v = np.clip(pendiente / PENDIENTE_MAX, 0.0, 1.0)
    return np.stack([(0.5 + u * (s - 1)) / s, (0.5 + v * (s - 1)) / s], axis=-1)


# --------------------------------------------------------------------------------------------------------------
# Cubo-esfera
# --------------------------------------------------------------------------------------------------------------


class Superficie:
    """Los vértices de las 6 caras (K·N + 1 por lado), con altura, normal exacta y UV."""

    def __init__(self, relieve: T.Relieve, lado: int, cuadros: int):
        self.relieve, self.K, self.N = relieve, lado, cuadros
        self.m = lado * cuadros + 1
        self.dir, self.pos, self.normal, self.altura, self.pendiente, self.uv = {}, {}, {}, {}, {}, {}
        for cara in CARAS:
            self._cara(cara)

    def _direcciones(self, cara: str) -> np.ndarray:
        n, a, b = (np.array(v, dtype=np.float64) for v in EJES_CARA[cara])
        alfa = -math.pi / 4 + (math.pi / 2) * np.arange(self.m) / (self.m - 1)
        s = np.tan(alfa)
        s[0], s[-1] = -1.0, 1.0  # los bordes, exactos: así dos caras vecinas calculan el mismo punto bit a bit
        p = n[None, None, :] + s[:, None, None] * a[None, None, :] + s[None, :, None] * b[None, None, :]
        return p / np.linalg.norm(p, axis=-1, keepdims=True)  # [i (eje a), j (eje b), 3]

    def _cara(self, cara: str) -> None:
        d = self._direcciones(cara).reshape(-1, 3)
        r = self.relieve
        h = r.altura(d)
        # Normal exacta: se derivan dos tangentes del PROPIO relieve con una diferencia centrada de 1 stud.
        ref = np.where(np.abs(d[:, 1:2]) > 0.9, np.array([[1.0, 0.0, 0.0]]), np.array([[0.0, 1.0, 0.0]]))
        t1 = np.cross(d, ref)
        t1 /= np.linalg.norm(t1, axis=1, keepdims=True)
        t2 = np.cross(d, t1)
        e = 1.0 / RADIO

        def punto(dd):
            dd = dd / np.linalg.norm(dd, axis=1, keepdims=True)
            return dd * (RADIO + r.altura(dd))[:, None]

        v1 = punto(d + e * t1) - punto(d - e * t1)
        v2 = punto(d + e * t2) - punto(d - e * t2)
        nrm = np.cross(v1, v2)
        nrm /= np.linalg.norm(nrm, axis=1, keepdims=True)
        nrm *= np.sign(np.sum(nrm * d, axis=1))[:, None]  # hacia fuera
        pendiente = np.degrees(np.arccos(np.clip(np.sum(nrm * d, axis=1), -1.0, 1.0)))

        # Variación de las curvas de nivel: ruido de ~40 studs en la coordenada de la paleta.
        pos = d * (RADIO + h)[:, None]
        q = pos / 40.0
        ru = r.ruido
        alt_uv = h + RUIDO_ALTURA * ru.perlin(q)
        pen_uv = pendiente + RUIDO_PENDIENTE * ru.perlin(q + 31.7)

        m = self.m
        self.dir[cara] = d.reshape(m, m, 3)
        self.pos[cara] = pos.reshape(m, m, 3)
        self.normal[cara] = nrm.reshape(m, m, 3)
        self.altura[cara] = h.reshape(m, m)
        self.pendiente[cara] = pendiente.reshape(m, m)
        self.uv[cara] = uv_paleta(alt_uv, pen_uv).reshape(m, m, 2)



# --------------------------------------------------------------------------------------------------------------
# Un trozo = un sólido cerrado
# --------------------------------------------------------------------------------------------------------------


def construir_trozo(sup: Superficie, cara: str, ti: int, tj: int, fondo_cuadros: int) -> dict:
    N, M = sup.N, fondo_cuadros
    r = N // M
    i0, j0 = ti * N, tj * N
    sl = (slice(i0, i0 + N + 1), slice(j0, j0 + N + 1))
    P_top = sup.pos[cara][sl].reshape(-1, 3)
    N_top = sup.normal[cara][sl].reshape(-1, 3)
    UV_top = sup.uv[cara][sl].reshape(-1, 2)
    D = sup.dir[cara][sl]
    idx = np.arange((N + 1) ** 2).reshape(N + 1, N + 1)

    # Fondo grueso: la rejilla gruesa (M+1)², con las mismas direcciones que cada r-ésimo vértice de arriba.
    Db = D[::r, ::r].reshape(-1, 3)
    P_bot = Db * (RADIO - PROFUNDIDAD_FONDO)
    idxb = (N + 1) ** 2 + np.arange((M + 1) ** 2).reshape(M + 1, M + 1)
    uv_roca = uv_paleta(np.array([ALTURA_MAX]), np.array([PENDIENTE_MAX]))[0]
    UV_bot = np.tile(uv_roca, (len(P_bot), 1))

    verts = np.concatenate([P_top, P_bot])
    uv = np.concatenate([UV_top, UV_bot])

    # Superficie: dos triángulos por cuadro, con la diagonal alternada (sin sesgo en una dirección).
    v00, v10, v01, v11 = idx[:-1, :-1], idx[1:, :-1], idx[:-1, 1:], idx[1:, 1:]
    par = ((np.add.outer(np.arange(N), np.arange(N))) % 2 == 0)
    t_a = np.where(par[..., None], np.stack([v00, v10, v11], -1), np.stack([v00, v10, v01], -1))
    t_b = np.where(par[..., None], np.stack([v00, v11, v01], -1), np.stack([v10, v11, v01], -1))
    tris_top = np.concatenate([t_a.reshape(-1, 3), t_b.reshape(-1, 3)])

    # Fondo (visto desde dentro: el orden de los vértices va al revés).
    b00, b10, b01, b11 = idxb[:-1, :-1], idxb[1:, :-1], idxb[:-1, 1:], idxb[1:, 1:]
    tris_bot = np.concatenate([np.stack([b00, b11, b10], -1).reshape(-1, 3),
                               np.stack([b00, b01, b11], -1).reshape(-1, 3)])

    # Paredes: por cada tramo del fondo, un abanico hacia los r+1 vértices de arriba y un triángulo de cierre.
    paredes = []
    lados = [(idx[:, 0], idxb[:, 0]), (idx[:, N], idxb[:, M]), (idx[0, :], idxb[0, :]), (idx[N, :], idxb[M, :])]
    for arriba, abajo in lados:
        for q in range(M):
            for k in range(q * r, (q + 1) * r):
                paredes.append((abajo[q], arriba[k], arriba[k + 1]))
            paredes.append((abajo[q], arriba[(q + 1) * r], abajo[q + 1]))
    tris_pared = np.array(paredes, dtype=np.int64)

    # Orientación de las paredes: hacia fuera del eje del trozo. Se corrige con un producto escalar.
    eje = D[N // 2, N // 2]
    a_, b_, c_ = verts[tris_pared[:, 0]], verts[tris_pared[:, 1]], verts[tris_pared[:, 2]]
    ng = np.cross(b_ - a_, c_ - a_)
    cen = (a_ + b_ + c_) / 3.0
    hacia_fuera = cen - (cen @ eje)[:, None] * eje[None, :]
    flip = np.sum(ng * hacia_fuera, axis=1) < 0
    tris_pared[flip] = tris_pared[flip][:, [0, 2, 1]]

    tris = np.concatenate([tris_top, tris_bot, tris_pared]).astype(np.int64)

    # Normales por esquina de triángulo: las de la superficie, las exactas (lisas); las del resto, planas.
    a_, b_, c_ = verts[tris[:, 0]], verts[tris[:, 1]], verts[tris[:, 2]]
    ng = np.cross(b_ - a_, c_ - a_)
    ng /= np.maximum(np.linalg.norm(ng, axis=1, keepdims=True), 1e-12)
    normales = np.repeat(ng[:, None, :], 3, axis=1)
    n_top = len(tris_top)
    normales[:n_top] = N_top[tris_top]  # (n_top, 3, 3)

    # Posición del trozo: el centro de su caja envolvente, redondeado al milímetro (el FBX guarda lo local).
    mn, mx = verts.min(axis=0), verts.max(axis=0)
    centro = np.round((mn + mx) / 2.0, 3)
    local = verts - centro[None, :]
    return dict(
        nombre=f"Planeta_{cara}_{ti}_{tj}", cara=cara, i=ti, j=tj, centro=centro, tamano=mx - mn,
        verts=local, uv=uv, tris=tris, normales=normales.reshape(-1, 3),
        alt_min=float(sup.altura[cara][sl].min()), alt_max=float(sup.altura[cara][sl].max()),
    )


# --------------------------------------------------------------------------------------------------------------
# Muestras para comprobar en Studio: dónde está la superficie en direcciones dadas
# --------------------------------------------------------------------------------------------------------------


def paridad_cuadro(sup: Superficie, gi: int, gj: int) -> bool:
    """True si el cuadro (gi, gj) de la cara usa la diagonal v00-v11 (la misma regla que construir_trozo)."""
    return ((gi % sup.N) + (gj % sup.N)) % 2 == 0


def radio_malla(sup: Superficie, d: np.ndarray) -> float:
    """Distancia al centro de la superficie TRIANGULADA (no la del relieve exacto) en la dirección d: se cruza el
    rayo con los dos triángulos que de verdad hay en ese cuadro."""
    eje = int(np.argmax(np.abs(d)))
    cara = ("X", "Y", "Z")[eje] + ("P" if d[eje] > 0 else "N")
    n, a, b = (np.array(v, dtype=np.float64) for v in EJES_CARA[cara])
    s, t = (d @ a) / (d @ n), (d @ b) / (d @ n)
    total = sup.m - 1
    gi = int(np.clip((math.atan(s) + math.pi / 4) / (math.pi / 2) * total, 0, total - 1e-9))
    gj = int(np.clip((math.atan(t) + math.pi / 4) / (math.pi / 2) * total, 0, total - 1e-9))
    P = sup.pos[cara]
    p00, p10, p01, p11 = P[gi, gj], P[gi + 1, gj], P[gi, gj + 1], P[gi + 1, gj + 1]
    if paridad_cuadro(sup, gi, gj):
        triangulos = ((p00, p10, p11), (p00, p11, p01))
    else:
        triangulos = ((p00, p10, p01), (p10, p11, p01))
    for v0, v1, v2 in triangulos:
        nrm = np.cross(v1 - v0, v2 - v0)
        lam = float(v0 @ nrm) / float(d @ nrm)
        e0, e1, e2 = v1 - v0, v2 - v0, d * lam - v0
        d00, d01, d11, d20, d21 = e0 @ e0, e0 @ e1, e1 @ e1, e2 @ e0, e2 @ e1
        den = d00 * d11 - d01 * d01
        w1, w2 = (d11 * d20 - d01 * d21) / den, (d00 * d21 - d01 * d20) / den
        if w1 >= -1e-7 and w2 >= -1e-7 and w1 + w2 <= 1 + 1e-7:
            return lam
    return float(np.linalg.norm(P[gi, gj]))


def muestras(sup: Superficie, cantidad: int = 240, semilla: int = 11) -> list:
    """Direcciones donde el script de Luau lanza rayos: unas al azar y otras sobre los bordes entre trozos."""
    rng = np.random.default_rng(semilla)
    dirs = rng.normal(size=(cantidad, 3))
    dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    lista = [d for d in dirs]
    N, K = sup.N, sup.K
    for cara in CARAS:  # esquinas y mitades de borde entre trozos: justo donde estaría una grieta
        for a in range(0, K * N + 1, N):
            for b in range(N // 2, K * N, N):
                lista.append(sup.dir[cara][a, b])
                lista.append(sup.dir[cara][b, a])
    salida = []
    for d in lista:
        d = np.asarray(d, dtype=np.float64)
        salida.append([float(x) for x in np.round(d, 9)] + [round(radio_malla(sup, d), 4)])
    return salida


# --------------------------------------------------------------------------------------------------------------
# Script de Luau
# --------------------------------------------------------------------------------------------------------------


def _num(x: float, decimales: int = 3) -> str:
    t = f"{x:.{decimales}f}".rstrip("0").rstrip(".")
    return "0" if t in ("", "-0") else t


def escribir_luau(datos: dict, ruta: str) -> None:
    """Rellena plantilla_colocar_planeta.luau con los números de los trozos y las muestras de colisión."""
    aqui = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(aqui, "plantilla_colocar_planeta.luau"), encoding="utf-8") as f:
        plantilla = f.read()
    piezas = "\n".join(
        f'\t{{ Nombre = "{p["nombre"]}", Centro = Vector3.new({", ".join(_num(x) for x in p["centro"])}), '
        f'Tamano = Vector3.new({", ".join(_num(x) for x in p["tamano"])}), Triangulos = {p["triangulos"]} }},'
        for p in datos["piezas"])
    muestras = "\n".join(
        f'\t{{ {", ".join(_num(x, 9) for x in m[:3])}, {_num(m[3], 4)} }},' for m in datos["muestras"])
    texto = (plantilla.replace("--RADIO--", _num(datos["radio"])).replace("--PIEZAS--", piezas)
             .replace("--MUESTRAS--", muestras))
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(texto)


# --------------------------------------------------------------------------------------------------------------
# Blender: crear los objetos y exportar
# --------------------------------------------------------------------------------------------------------------


def a_blender(v: np.ndarray) -> np.ndarray:
    """Roblox/FBX (X, Y, Z) -> Blender (x, y, z). Es la inversa de lo que hace el exportador con Z delante, Y arriba:
    el FBX recibe (-x, z, y), así que Blender necesita (x, y, z) = (-X, Z, Y). Es una rotación (determinante +1):
    no cambia el sentido de los triángulos."""
    v = np.asarray(v)
    return np.stack([-v[..., 0], v[..., 2], v[..., 1]], axis=-1)


def crear_objeto(bpy, trozo: dict, material):
    verts = a_blender(trozo["verts"]).astype(np.float32)
    tris = trozo["tris"].astype(np.int32)
    mesh = bpy.data.meshes.new(trozo["nombre"])
    mesh.vertices.add(len(verts))
    mesh.vertices.foreach_set("co", verts.ravel())
    mesh.loops.add(len(tris) * 3)
    mesh.loops.foreach_set("vertex_index", tris.ravel())
    mesh.polygons.add(len(tris))
    mesh.polygons.foreach_set("loop_start", np.arange(0, len(tris) * 3, 3, dtype=np.int32))
    mesh.polygons.foreach_set("loop_total", np.full(len(tris), 3, dtype=np.int32))
    mesh.polygons.foreach_set("use_smooth", np.ones(len(tris), dtype=bool))
    mesh.update(calc_edges=True)
    capa = mesh.uv_layers.new(name="UVMap")
    capa.data.foreach_set("uv", trozo["uv"][tris.ravel()].astype(np.float32).ravel())
    mesh.normals_split_custom_set(a_blender(trozo["normales"]).astype(np.float32))
    mesh.materials.append(material)
    obj = bpy.data.objects.new(trozo["nombre"], mesh)
    obj.location = tuple(float(x) for x in a_blender(trozo["centro"]))
    bpy.context.scene.collection.objects.link(obj)
    return obj


def exportar_fbx(bpy, obj, ruta: str) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH"},
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",  # receta oficial de Roblox
        bake_space_transform=False, axis_forward="Z", axis_up="Y",
        use_mesh_modifiers=False, mesh_smooth_type="OFF",  # «solo normales»: se exportan las normales exactas
        use_tspace=False, add_leaf_bones=False, bake_anim=False,
        path_mode="STRIP", embed_textures=False,  # la textura se pone desde el script (un solo archivo para 96 trozos)
    )


# --------------------------------------------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------------------------------------------


def estadisticas(sup: Superficie) -> dict:
    alt = np.concatenate([sup.altura[c].ravel() for c in CARAS])
    pen = np.concatenate([sup.pendiente[c].ravel() for c in CARAS])
    tierra = alt > 0
    return dict(
        altura_min=float(alt.min()), altura_max=float(alt.max()),
        fraccion_tierra=float(tierra.mean()),
        pendiente_tierra_p50=float(np.percentile(pen[tierra], 50)),
        pendiente_tierra_p90=float(np.percentile(pen[tierra], 90)),
        pendiente_tierra_p99=float(np.percentile(pen[tierra], 99)),
        pendiente_tierra_max=float(pen[tierra].max()),
    )


def hueco_de_costuras(sup: Superficie) -> float:
    """Mayor distancia entre los dos cálculos de un mismo vértice del borde entre caras del cubo (debe ser ~0)."""
    puntos = {}
    m = sup.m
    for cara in CARAS:
        P = sup.pos[cara]
        for borde in (P[0, :], P[m - 1, :], P[:, 0], P[:, m - 1]):
            for p in borde:
                puntos.setdefault(tuple(np.round(p, 2)), []).append(p)
    peor = 0.0
    for lista in puntos.values():
        if len(lista) > 1:
            a = np.array(lista)
            peor = max(peor, float(np.linalg.norm(a - a[0], axis=1).max()))
    return peor


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--lado", type=int, default=4, help="trozos por lado de cada cara (6·K² trozos en total)")
    ap.add_argument("--cuadros", type=int, default=64, help="cuadros por lado de cada trozo (múltiplo de 8)")
    ap.add_argument("--semilla", type=int, default=7)
    ap.add_argument("--rapido", action="store_true", help="resolución mínima para probar (cuadros = 16)")
    ap.add_argument("--sin-fbx", action="store_true", help="no exporta FBX: solo datos, paleta y comprobaciones")
    a = ap.parse_args()
    if a.rapido:
        a.cuadros = 16
    assert a.cuadros % 8 == 0, "--cuadros tiene que ser múltiplo de 8 (el fondo usa 1/8 de los cuadros)"
    salida = os.path.abspath(a.salida)
    os.makedirs(os.path.join(salida, "piezas"), exist_ok=True)

    t0 = time.time()
    relieve = T.Relieve(replace(T.Parametros(), semilla=a.semilla))
    sup = Superficie(relieve, a.lado, a.cuadros)
    print(f"[ok] relieve calculado: {6 * sup.m ** 2} vértices en {time.time() - t0:.1f} s")
    est = estadisticas(sup)
    costura = hueco_de_costuras(sup)
    print(f"[info] alturas {est['altura_min']:.0f}..{est['altura_max']:.0f} studs · tierra {est['fraccion_tierra']:.0%} · "
          f"pendiente en tierra p50/p90/p99 = {est['pendiente_tierra_p50']:.1f}/{est['pendiente_tierra_p90']:.1f}/"
          f"{est['pendiente_tierra_p99']:.1f}° · hueco máximo entre caras {costura:.2e} studs")

    escribir_paletas(salida)

    fondo = a.cuadros // 8
    trozos = []
    for cara in CARAS:
        for ti in range(a.lado):
            for tj in range(a.lado):
                trozos.append(construir_trozo(sup, cara, ti, tj, fondo))
    max_tris = max(len(t["tris"]) for t in trozos)
    max_lado = max(float(t["tamano"].max()) for t in trozos)
    print(f"[info] {len(trozos)} trozos · máx {max_tris} triángulos (límite {LIMITE_TRIANGULOS}) · "
          f"mayor lado {max_lado:.0f} studs (límite {LIMITE_LADO:.0f})")
    if max_tris > LIMITE_TRIANGULOS:
        sys.exit(f"ERROR: un trozo tiene {max_tris} triángulos (> {LIMITE_TRIANGULOS}). Baja --cuadros.")
    if max_lado > LIMITE_LADO:
        sys.exit(f"ERROR: un trozo mide {max_lado:.0f} studs (> {LIMITE_LADO:.0f}). Sube --lado.")
    if max_tris > LIMITE_TRIANGULOS * MARGEN_TRIANGULOS or max_lado > LIMITE_LADO * MARGEN_LADO:
        print("[aviso] un trozo está muy cerca de un límite")

    datos = dict(
        nota="studs, ejes de Roblox (Y arriba). El centro es el de la caja envolvente de cada trozo.",
        radio=RADIO, profundidad_fondo=PROFUNDIDAD_FONDO, lado=a.lado, cuadros=a.cuadros, semilla=a.semilla,
        parametros_relieve=asdict(relieve.p), umbral_continental=relieve.umbral,
        paleta=dict(altura_min=ALTURA_MIN, altura_max=ALTURA_MAX, pendiente_max=PENDIENTE_MAX, tamano=TAM_PALETA),
        limites=dict(triangulos=LIMITE_TRIANGULOS, lado=LIMITE_LADO),
        estadisticas=est, hueco_costuras=costura,
        total_triangulos=int(sum(len(t["tris"]) for t in trozos)),
        piezas=[dict(nombre=t["nombre"], cara=t["cara"], i=t["i"], j=t["j"],
                     centro=[float(x) for x in t["centro"]], tamano=[round(float(x), 3) for x in t["tamano"]],
                     triangulos=int(len(t["tris"])), vertices=int(len(t["verts"]))) for t in trozos],
        muestras=muestras(sup),
    )
    with open(os.path.join(salida, "datos_piezas.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=1, ensure_ascii=False)
    print(f"[ok] datos_piezas.json: {len(datos['piezas'])} piezas, {len(datos['muestras'])} muestras de colisión")
    escribir_luau(datos, os.path.join(salida, "colocar_planeta.luau"))
    print("[ok] colocar_planeta.luau")

    if a.sin_fbx:
        return
    import bpy  # se importa aquí: así lo demás se puede probar sin Blender

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "NONE"  # 1 unidad de Blender = 1 stud (guía oficial de Roblox)
    material = bpy.data.materials.new("Planeta")
    material.diffuse_color = (0.5, 0.5, 0.5, 1.0)
    for k, trozo in enumerate(trozos):
        obj = crear_objeto(bpy, trozo, material)
        exportar_fbx(bpy, obj, os.path.join(salida, "piezas", trozo["nombre"] + ".fbx"))
        bpy.data.objects.remove(obj)
        if k % 16 == 0:
            print(f"  exportados {k + 1}/{len(trozos)}")
    peso = sum(os.path.getsize(os.path.join(salida, "piezas", f)) for f in os.listdir(os.path.join(salida, "piezas")))
    print(f"[ok] {len(trozos)} FBX en {salida}/piezas ({peso / 1e6:.1f} MB) · {time.time() - t0:.0f} s en total")


if __name__ == "__main__":
    main()
