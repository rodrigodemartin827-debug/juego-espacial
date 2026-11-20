"""
BESTIA 1 — MANTA ESTELAR (montura de exploración de los Monstruos).

Una mantarraya gigante adaptada al vacío: piel coriácea azul-violácea, vientre gris perlado, escamas hexagonales en
el lomo, cinco nervaduras por ala, ojos ámbar con pupila de estrella y venas de luz cyan como constelaciones.
Lleva un arnés orgánico (cuero alienígena, hueso tallado, fibra vegetal) y las cicatrices de su vida.

Rig (11 piezas, pivote en cada articulación, rotación 0,0,0):
    Cuerpo_Central (raíz) · Ala_Izquierda_Base · Ala_Izquierda_Punta · Ala_Derecha_Base · Ala_Derecha_Punta
    Cola · Cola_Punta · Cabeza · Mandibula · Tentaculo_Izq · Tentaculo_Der
Más una pieza soldada a la Cabeza: Ojos_Cornea (las córneas, material de cristal en Roblox).
Puntos de montaje (cubos de 0,3, invisibles): Montura_Piloto, Montura_Pasajero, Agarre_Izq, Agarre_Der.

Uso:
    python bestias/herramientas/manta_estelar.py --salida bestias/manta_estelar --ronda 1 [--rapido]
"""

import argparse
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

import campos as C  # noqa: E402
import detalles as D  # noqa: E402
import manta_forma as F  # noqa: E402
import taller as T  # noqa: E402

NOMBRE = "manta_estelar"
PRESUPUESTO = 18000

# --------------------------------------------------------------------------------------------------------------
# Paleta (todo lo ajustable aquí)
# --------------------------------------------------------------------------------------------------------------

COL = {
    "lomo": "#1A1A3E", "lomo2": "#2D1B4E", "vientre": "#C8C8D4", "escama": "#1E3A5F", "neon": "#3DF2FF",
    "ojo": "#FFB347", "aguijon": "#0D0D1A", "cuero": "#4A2820", "costura": "#C4A882", "hueso": "#E8DCC8",
    "cicatriz": "#8E6E96", "regenerada": "#34407A", "quemadura": "#5A2A1E", "boca": "#5A2440",
    "branquia": "#3A1238", "fibra": "#8A7A4A", "fibra2": "#4E4226", "hierro": "#3A3836", "esclera": "#3A2412",
    "membrana": "#9AA0B8", "diente": "#DCCFB4", "espina": "#26304A", "parasito": "#7A6A80",
}

# Arnés y montaje (studs, coordenadas de modelado)
CINCHA_Y = (3.50, 3.86)
SILLA_Y = (-0.50, 3.42)
SILLA_ANCHO = 0.82
ASIENTO_PILOTO_Y = 2.35
ASIENTO_PASAJERO_Y = 0.35
ESTRIBO = (1.55, 1.62)
ALFORJA = (1.36, 0.62)
HEBILLA_X = 0.78
RUNAS_ARRIBA = [(-2.10, 2.92), (2.12, 2.98)]
RUNAS_ABAJO = [(-0.42, 3.05), (0.46, 2.98)]
# Hendiduras branquiales del vientre (5 por lado): y de cada una.
BRANQUIAS_Y = [3.25, 2.95, 2.65, 2.35, 2.05]

# Venas de luz en relieve sobre los flancos del lomo (asimétricas, como constelaciones).
VENAS_LOMO = [
    [(-2.05, 3.05), (-2.38, 2.15), (-2.56, 1.0), (-2.62, -0.4), (-2.48, -1.9), (-2.18, -3.3), (-1.72, -4.5),
     (-1.08, -5.45)],
    [(-2.56, 1.0), (-2.22, 0.45), (-2.12, -0.25)],
    [(2.10, 2.05), (2.48, 1.10), (2.64, -0.20), (2.52, -1.50), (2.24, -2.40)],
    [(2.64, -0.20), (2.26, -0.72)],
    [(2.42, -3.00), (2.02, -4.10), (1.42, -5.25), (0.78, -5.95)],
]
NODOS_VENA = [(-2.38, 2.15), (-2.62, -0.4), (-2.18, -3.3), (-1.08, -5.45), (-2.12, -0.25), (2.48, 1.10),
              (2.52, -1.50), (2.26, -0.72), (2.02, -4.10), (0.78, -5.95)]

# Cicatrices (polilíneas en planta) y parches de escamas regeneradas (centro, radios).
CICATRICES = [
    [(-3.35, 1.85), (-4.30, 0.55), (-5.20, -0.62)],      # zarpazo triple en el ala izquierda
    [(-3.10, 1.55), (-4.05, 0.28), (-4.95, -0.88)],
    [(-2.95, 1.20), (-3.85, 0.02), (-4.70, -1.10)],
    [(0.95, -1.45), (1.55, -2.55), (2.15, -3.55)],        # tajo largo en el lomo
    [(6.35, -0.35), (7.00, -1.15), (7.62, -1.95)],        # roce en la punta derecha
]
REGENERADAS = [((-7.15, -1.35), (0.62, 0.40), 0.4), ((-0.85, -4.55), (0.45, 0.36), -0.3),
               ((4.70, 0.35), (0.38, 0.30), 0.8)]
PARASITOS_VIENTRE = [(0.55, -5.55), (0.82, -5.18), (0.32, -5.92), (0.98, -5.72), (0.66, -5.95)]
PARASITOS_ALA = [(4.25, -2.55), (4.55, -2.85), (4.02, -2.95)]

# Raster de los mapas en planta (para los materiales procedurales de la piel)
DOMINIO = (-9.7, -13.0, 9.7, 7.7)  # x0, y0, x1, y1
PX_STUD = 90


def ruta(*p):
    return os.path.join(*p)


# --------------------------------------------------------------------------------------------------------------
# Mapas en planta (constelaciones, cicatrices, runas...) que lee el material de la piel
# --------------------------------------------------------------------------------------------------------------


def mapas_planta(rnd):
    x0, y0, x1, y1 = DOMINIO
    W = int((x1 - x0) * PX_STUD)
    H = int((y1 - y0) * PX_STUD)

    def px(x, y):
        return ((x - x0) * PX_STUD, (y1 - y) * PX_STUD)  # PIL: y hacia abajo

    def lienzo():
        return Image.new("L", (W, H), 0)

    def linea(d, pts, ancho):
        d.line([px(*p) for p in pts], fill=255, width=max(1, int(ancho * PX_STUD)), joint="curve")

    def punto(d, x, y, r):
        a, b = px(x, y)
        rr = r * PX_STUD
        d.ellipse((a - rr, b - rr, a + rr, b + rr), fill=255)

    # Campos 2D en la rejilla del raster (para el borde de ataque y la distancia al borde).
    # (a un cuarto de resolución: son campos suaves; luego se amplían)
    from scipy.ndimage import zoom

    red = 4
    xs = x0 + (np.arange(W // red) + 0.5) * red / PX_STUD
    ys = y1 - (np.arange(H // red) + 0.5) * red / PX_STUD
    X, Y = np.meshgrid(xs, ys)
    k = F.campos_2d(X, Y)
    dentro = np.clip(-k["d2"], 0, 3) / 3.0
    borde_ataque = (np.clip(1 - k["c"] / 0.16, 0, 1) * C.sstep(2.2, 3.2, np.abs(X)) * (k["d2"] < 0.05))
    dentro = np.clip(zoom(dentro, (H / dentro.shape[0], W / dentro.shape[1]), order=1), 0, 1)[:H, :W]
    borde_ataque = np.clip(zoom(borde_ataque, (H / borde_ataque.shape[0], W / borde_ataque.shape[1]), order=1),
                           0, 1)[:H, :W]

    # Venas de luz en las alas (líneas cortas con estrellas, distintas en cada ala) y la cabeza.
    bio = lienzo()
    d = ImageDraw.Draw(bio)
    ataque = np.array(F.BORDE_ATAQUE)
    for lado, semilla in ((1, 3), (-1, 11)):
        r2 = np.random.default_rng(semilla)
        curva = C.remuestrear(C.catmull_rom(ataque, 10, cerrada=False), 0.05)
        # desplazada hacia dentro 0,32
        tang = np.gradient(curva, axis=0)
        nor = np.stack([tang[:, 1], -tang[:, 0]], 1)
        nor /= np.linalg.norm(nor, axis=1, keepdims=True)
        dentro_c = curva + nor * 0.32 * np.sign(nor[:, 1:2].mean() * -1 + 1e-9)
        i = int(r2.integers(4, 14))
        while i < len(dentro_c) - 10:
            largo = int(r2.integers(14, 34))
            seg = dentro_c[i:i + largo]
            if seg[:, 0].min() > 2.9:
                pts = [(lado * p[0], p[1]) for p in seg]
                linea(d, pts, 0.035)
                punto(d, *pts[0], 0.07)
                punto(d, *pts[-1], 0.055)
            i += largo + int(r2.integers(5, 12))
        # Constelación libre en el ala: 6 estrellas unidas por trazos finos.
        estrellas = []
        while len(estrellas) < 6:
            x = r2.uniform(3.4, 7.6)
            y = r2.uniform(-2.6, 2.0)
            kk = F.campos_2d(np.array([x]), np.array([y]))
            if -kk["d2"][0] > 0.7:
                estrellas.append((x, y))
        estrellas.sort(key=lambda p: p[0] + 0.3 * p[1])
        pts = [(lado * x, y) for x, y in estrellas]
        linea(d, pts, 0.022)
        for (x, y) in pts:
            punto(d, x, y, r2.uniform(0.05, 0.09))
    # Borde de la cabeza.
    cabeza = [(x, y - 0.24) for x, y in [(-1.30, 5.86), (-0.9, 6.05), (-0.4, 6.12), (0.15, 6.12), (0.7, 6.06),
                                         (1.15, 5.92)]]
    linea(d, cabeza, 0.035)
    for p in cabeza[::2]:
        punto(d, *p, 0.05)
    # Puntos a lo largo de la cola.
    for y in np.arange(-7.15, -11.2, -0.55):
        punto(d, 0.0, y + 0.27, 0.035)

    # Puntos luminosos en el borde de fuga (las dos caras del ala).
    puntos_borde = lienzo()
    d = ImageDraw.Draw(puntos_borde)
    fuga = C.remuestrear(np.array(F.BORDE_FUGA), 0.05)
    tang = np.gradient(fuga, axis=0)
    nor = np.stack([-tang[:, 1], tang[:, 0]], 1)
    nor /= np.linalg.norm(nor, axis=1, keepdims=True)
    for lado in (1, -1):
        acum = 0.0
        for i in range(1, len(fuga)):
            acum += np.linalg.norm(fuga[i] - fuga[i - 1])
            if acum >= 0.30:
                acum = 0.0
                p = fuga[i] + nor[i] * 0.17
                if p[0] < 2.6:
                    continue
                if -F.campos_2d(np.array([lado * p[0]]), np.array([p[1]]))["d2"][0] < 0.08:
                    continue
                punto(d, lado * p[0], p[1], 0.045 if i % 3 else 0.065)

    cic = lienzo()
    d = ImageDraw.Draw(cic)
    for pts in CICATRICES:
        lisa = C.remuestrear(C.catmull_rom(pts, 8, cerrada=False), 0.05)
        ruido = np.random.default_rng(len(pts)).normal(0, 0.012, lisa.shape)
        linea(d, [tuple(p) for p in lisa + ruido], 0.095)

    reg = lienzo()
    d = ImageDraw.Draw(reg)
    for (cx, cy), (rx, ry), giro in REGENERADAS:
        pts = []
        for t in np.linspace(0, math.tau, 40, endpoint=False):
            r = 1 + 0.18 * math.sin(3 * t + giro * 5) + 0.1 * math.sin(5 * t)
            x, y = rx * r * math.cos(t), ry * r * math.sin(t)
            pts.append(px(cx + x * math.cos(giro) - y * math.sin(giro), cy + x * math.sin(giro) + y * math.cos(giro)))
        d.polygon(pts, fill=255)

    espir = lienzo()
    d = ImageDraw.Draw(espir)
    for (sx, sy, giro) in F.ESPIRACULOS:
        for lado in (1, -1):
            g = math.radians(giro) * -lado
            pts = []
            for t in np.linspace(0, math.tau, 24, endpoint=False):
                x, y = 0.11 * math.cos(t), 0.27 * math.sin(t)
                pts.append(px(lado * sx + x * math.cos(g) - y * math.sin(g), sy + x * math.sin(g) + y * math.cos(g)))
            d.polygon(pts, fill=255)

    def glifos(lista, semilla):
        img = lienzo()
        dd = ImageDraw.Draw(img)
        r3 = np.random.default_rng(semilla)
        for (cx, cy) in lista:
            a, b = px(cx, cy)
            r = 0.15 * PX_STUD
            dd.ellipse((a - r, b - r, a + r, b + r), outline=255, width=int(0.035 * PX_STUD))
            for _ in range(3):
                t = r3.uniform(0, math.tau)
                u = t + r3.uniform(1.6, 2.8)
                dd.line([px(cx + 0.2 * math.cos(t), cy + 0.2 * math.sin(t)),
                         px(cx + 0.08 * math.cos(u), cy + 0.08 * math.sin(u))], fill=255, width=int(0.03 * PX_STUD))
            punto(dd, cx, cy, 0.035)
        return img

    branq = lienzo()
    d = ImageDraw.Draw(branq)
    for lado in (1, -1):
        for i, y in enumerate(BRANQUIAS_Y):
            largo = 0.62 - 0.05 * i
            pts = [(lado * (1.05 + largo * t), y - 0.12 * math.sin(math.pi * t) - 0.06 * t) for t in np.linspace(0, 1, 12)]
            linea(d, pts, 0.05)

    runas_arriba = glifos(RUNAS_ARRIBA, 5)
    runas_abajo = glifos(RUNAS_ABAJO, 9)

    from scipy.ndimage import gaussian_filter

    def arr(img, sigma=0.9):
        return gaussian_filter(np.asarray(img, dtype=np.float32) / 255.0, sigma)

    img1 = np.stack([dentro, borde_ataque, arr(bio), arr(cic, 1.6)], -1)
    img2 = np.stack([arr(espir, 1.2), arr(runas_arriba), arr(reg, 4.0), arr(puntos_borde)], -1)
    img3 = np.stack([arr(runas_abajo), arr(branq, 1.4), np.zeros_like(dentro), np.ones_like(dentro)], -1)

    def a_blender(nombre, datos):
        im = bpy.data.images.new(nombre, W, H, alpha=True, float_buffer=True)
        im.colorspace_settings.name = "Non-Color"
        im.alpha_mode = "CHANNEL_PACKED"
        im.pixels.foreach_set(np.flipud(datos).astype(np.float32).ravel())  # Blender: fila 0 abajo
        im.pack()
        return im

    return a_blender("mapa_planta_1", img1), a_blender("mapa_planta_2", img2), a_blender("mapa_planta_3", img3)


# --------------------------------------------------------------------------------------------------------------
# Materiales procedurales (se hornean en el atlas)
# --------------------------------------------------------------------------------------------------------------


def smooth(N, a, b, x):
    m = N.n("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP")
    m.inputs["From Min"].default_value = a
    m.inputs["From Max"].default_value = b
    N.enlazar(x, m.inputs["Value"])
    return m.outputs["Result"]


def lin(h):
    return T.srgb(COL[h]) if h in COL else T.srgb(h)


def material_piel(mapas):
    """La piel de la manta: lomo oscuro moteado con escamas (normal map), vientre perlado con pliegues, borde de
    ataque reforzado, cicatrices, parches regenerados, espiráculos, runas quemadas, boca y venas de luz."""
    mat = bpy.data.materials.new("piel")
    N = T.Nodos(mat)
    P = N.pos()
    x0, y0, x1, y1 = DOMINIO
    uv = N.vmate("MULTIPLY", N.vmate("SUBTRACT", P, (x0, y0, 0.0)), (1 / (x1 - x0), 1 / (y1 - y0), 0.0))

    def canales(img):
        t = N.n("ShaderNodeTexImage")
        t.image = img
        t.extension = "EXTEND"
        N.enlazar(uv, t.inputs["Vector"])
        s = N.n("ShaderNodeSeparateColor")
        N.enlazar(t.outputs["Color"], s.inputs["Color"])
        return s.outputs[0], s.outputs[1], s.outputs[2], t.outputs["Alpha"]

    dentro, ataque, bio, cic = canales(mapas[0])
    espir, runa_arr, regen, puntos = canales(mapas[1])
    runa_ab, branq, _, _ = canales(mapas[2])

    px_, py_, pz_ = N.sep(P)
    nx_, ny_, nz_ = N.sep(N.normal())
    arriba = smooth(N, -0.2, 0.35, nz_)
    abajo = N.mate("SUBTRACT", 1.0, arriba)
    ax = N.mate("ABSOLUTE", px_)
    aux = N.atributo("aux")
    auxs = N.sep(aux.outputs["Vector"])
    es_tentaculo = N.mate("COMPARE", auxs[2], 1.0, 0.1)

    # --- Escamas del lomo (normal map): celdas de 0,30 en el centro y 0,17 en las alas ---
    xy = N.combinar(px_, py_, 0.0)
    v1 = N.voronoi(xy, 3.3, rasgo="DISTANCE_TO_EDGE", aleatorio=0.35)
    v2 = N.voronoi(xy, 6.0, rasgo="DISTANCE_TO_EDGE", aleatorio=0.35)
    v3 = N.voronoi(xy, 10.0, rasgo="DISTANCE_TO_EDGE", aleatorio=0.4)  # regeneradas: más pequeñas
    surco1 = smooth(N, 0.0, 0.09, v1)
    surco2 = smooth(N, 0.0, 0.10, v2)
    surco3 = smooth(N, 0.0, 0.12, v3)
    f_alas = smooth(N, 1.6, 4.2, ax)
    surco = N.mezcla(f_alas, surco1, surco2)
    surco = N.mezcla(regen, surco, surco3)
    surco = N.sep(surco)[0]

    # --- Color ---
    mot = N.ruido(P, 0.35, 3.0, 0.5)
    lomo = N.mezcla(smooth(N, 0.35, 0.68, mot), lin("lomo"), lin("lomo2"))
    manchas = N.ruido(P, 2.4, 5.0, 0.6)
    lomo = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.55, 0.75, manchas), 0.45), lomo, (0.012, 0.012, 0.035))
    # Polvo de estrellas: motas pálidas diminutas en el lomo.
    motas = N.voronoi(P, 22.0, rasgo="F1", salida="Distance")
    mota = N.mate("MULTIPLY", N.mate("LESS_THAN", motas, 0.09), smooth(N, 0.62, 0.7, N.ruido(P, 0.9, 2.0)))
    lomo = N.mezcla(N.mate("MULTIPLY", mota, 0.55), lomo, (0.22, 0.2, 0.42))
    lomo = N.mezcla(N.mate("MULTIPLY", ataque, 0.85), lomo, lin("escama"))
    lomo = N.mezcla(N.mate("MULTIPLY", regen, 0.75), lomo, lin("regenerada"))
    lomo = N.mezcla(N.mate("SUBTRACT", 1.0, surco), lomo, (0.006, 0.006, 0.018))
    vientre = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.3, 0.75, N.ruido(P, 0.8, 3.0)), 0.45), lin("vientre"),
                       (0.36, 0.36, 0.46))
    # Manchas oscuras del vientre (cada manta tiene su patrón, como una huella).
    vm = N.voronoi(P, 1.6, rasgo="F1", salida="Distance")
    vc = N.voronoi(P, 1.6, rasgo="F1", salida="Color")
    mancha = N.mate("MULTIPLY", N.mate("LESS_THAN", vm, 0.22), N.mate("GREATER_THAN", N.sep(vc)[0], 0.62))
    mancha = N.mate("MULTIPLY", mancha, N.mate("LESS_THAN", ax, 2.6))
    vientre = N.mezcla(N.mate("MULTIPLY", mancha, 0.8), vientre, (0.13, 0.13, 0.2))
    branquia = N.mate("MULTIPLY", branq, abajo)
    vientre = N.mezcla(branquia, vientre, (0.05, 0.03, 0.08))
    margen = N.mate("SUBTRACT", 1.0, smooth(N, 0.03, 0.2, dentro))
    vientre = N.mezcla(N.mate("MULTIPLY", margen, 0.7), vientre, (0.07, 0.07, 0.13))
    color = N.mezcla(arriba, vientre, lomo)
    # Tentáculos: lomo por fuera, más claros por dentro.
    color = N.mezcla(N.mate("MULTIPLY", es_tentaculo, N.mate("MULTIPLY", abajo, 0.5)), color, lin("lomo2"))
    color = N.mezcla(cic, color, lin("cicatriz"))
    color = N.mezcla(espir, color, lin("branquia"))
    runas = N.mate("MAXIMUM", N.mate("MULTIPLY", runa_arr, arriba), N.mate("MULTIPLY", runa_ab, abajo))
    color = N.mezcla(runas, color, lin("quemadura"))
    # Interior de la boca (dentro del elipsoide de la cavidad).
    cb, rb = F.BOCA_CENTRO, F.BOCA_RADIOS
    q = N.vmate("DIVIDE", N.vmate("SUBTRACT", P, cb), (rb[0] * 1.06, rb[1] * 1.06, rb[2] * 1.5))
    en_boca = N.mate("SUBTRACT", 1.0, smooth(N, 0.92, 1.02, N.vmate("LENGTH", q)))
    color = N.mezcla(en_boca, color, lin("boca"))
    # Venas de luz.
    espiral = N.mate("LESS_THAN", N.mate("FRACT", N.mate("ADD", auxs[1], N.mate("MULTIPLY", auxs[0], 2.6))), 0.09)
    espiral = N.mate("MULTIPLY", espiral, N.mate("MULTIPLY", es_tentaculo, smooth(N, 0.05, 0.15, auxs[0])))
    luz = N.mate("MAXIMUM", N.mate("MULTIPLY", bio, arriba), puntos)
    luz = N.mate("MAXIMUM", luz, espiral)
    luz = N.mate("MULTIPLY", luz, N.mate("SUBTRACT", 1.0, en_boca), clamp=True)
    color = N.mezcla(N.mate("MULTIPLY", luz, 0.85), color, (0.55, 0.95, 1.0))
    N.poner("Base Color", color)

    # --- Rugosidad ---
    rug = N.mate("ADD", N.mate("MULTIPLY", arriba, 0.74), N.mate("MULTIPLY", abajo, 0.42))
    bordes = N.mate("SUBTRACT", 1.0, smooth(N, 0.02, 0.09, dentro))
    rug = N.mezcla(N.mate("MULTIPLY", bordes, 0.85), rug, 0.28)
    rug = N.mezcla(N.mate("MULTIPLY", N.mate("SUBTRACT", 1.0, surco), N.mate("MULTIPLY", arriba, 0.5)), rug, 0.9)
    rug = N.mezcla(cic, rug, 0.55)
    rug = N.mezcla(N.mate("MAXIMUM", en_boca, espir), rug, 0.32)
    rug = N.mezcla(luz, rug, 0.25)
    N.poner("Roughness", N.sep(rug)[0])

    # --- Relieve ---
    poros = N.ruido(P, 28.0, 3.0, 0.5)
    h = N.mate("MULTIPLY", surco, N.mate("MULTIPLY", arriba, 0.55))
    h = N.mate("ADD", h, N.mate("MULTIPLY", poros, 0.12))
    h = N.mate("ADD", h, N.mate("MULTIPLY", cic, 1.1))
    h = N.mate("ADD", h, N.mate("MULTIPLY", bio, N.mate("MULTIPLY", arriba, 0.35)))
    h = N.mate("ADD", h, N.mate("MULTIPLY", puntos, 0.3))
    h = N.mate("ADD", h, N.mate("MULTIPLY", runas, 0.45))
    h = N.mate("SUBTRACT", h, N.mate("MULTIPLY", N.mate("MULTIPLY", branq, abajo), 1.2))
    # Pliegues del vientre (suaves y largos) y arrugas en las articulaciones.
    pliegue = N.mate("SINE", N.mate("ADD", N.mate("MULTIPLY", px_, 7.0), N.mate("MULTIPLY", N.ruido(P, 0.6, 2.0), 6.0)))
    h = N.mate("ADD", h, N.mate("MULTIPLY", pliegue, N.mate("MULTIPLY", abajo, 0.3)))
    for xc in (F.CORTE_ALA, F.CORTE_PUNTA):
        cerca = N.mate("SUBTRACT", 1.0, smooth(N, 0.0, 0.42, N.mate("ABSOLUTE", N.mate("SUBTRACT", ax, xc))))
        arr_ = N.mate("SINE", N.mate("ADD", N.mate("MULTIPLY", ax, 46.0), N.mate("MULTIPLY", py_, 3.0)))
        h = N.mate("ADD", h, N.mate("MULTIPLY", arr_, N.mate("MULTIPLY", cerca, 0.22)))
    cuello = N.mate("SUBTRACT", 1.0, smooth(N, 0.0, 0.35, N.mate("ABSOLUTE", N.mate("SUBTRACT", py_, F.CORTE_CABEZA))))
    arr_ = N.mate("SINE", N.mate("MULTIPLY", py_, 52.0))
    h = N.mate("ADD", h, N.mate("MULTIPLY", arr_, N.mate("MULTIPLY", cuello, 0.18)))
    N.poner("Normal", N.relieve(h, fuerza=0.65, distancia=0.035))

    # --- Emisión ---
    N.poner("Emission Color", N.mezcla(luz, (0, 0, 0), lin("neon")))
    N.poner("Emission Strength", 1.0)
    return mat


def material_escama():
    """Escamas en relieve: azul medianoche, cada una con su tono; las rotas, más claras y ásperas."""
    mat = bpy.data.materials.new("escama")
    N = T.Nodos(mat)
    aux = N.sep(N.atributo("aux").outputs["Vector"])
    tono = N.mezcla(aux[0], lin("escama"), lin("lomo2"))
    tono = N.mezcla(0.35, tono, lin("lomo"))
    tono = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.4, 0.7, N.ruido(N.pos(), 1.3, 3.0)), 0.5), tono, lin("lomo"))
    tono = N.mezcla(N.mate("MULTIPLY", aux[1], 0.6), tono, lin("cicatriz"))
    N.poner("Base Color", tono)
    N.poner("Roughness", N.sep(N.mezcla(aux[1], 0.6, 0.8))[0])
    anillos = N.mate("SINE", N.mate("MULTIPLY", N.vmate("LENGTH", N.pos()), 140.0))
    h = N.mate("ADD", N.mate("MULTIPLY", N.ruido(N.pos(), 30.0, 4.0), 0.4), N.mate("MULTIPLY", anillos, 0.08))
    N.poner("Normal", N.relieve(h, fuerza=0.5, distancia=0.01))
    return mat


def material_cuero():
    """Cuero alienígena: grano, costuras de tendón a los lados (aux = u a lo largo, v a lo ancho) y desgaste.
    En la silla (aux.z = 2): acolchado, costura del borde y zonas gastadas donde se sientan los jinetes."""
    mat = bpy.data.materials.new("cuero")
    N = T.Nodos(mat)
    P = N.pos()
    a = N.sep(N.atributo("aux").outputs["Vector"])
    es_silla = N.mate("COMPARE", a[2], 2.0, 0.1)
    grano = N.ruido(P, 40.0, 5.0, 0.6)
    arrugas = N.ruido(N.vmate("MULTIPLY", P, (1.0, 6.0, 1.0)), 6.0, 3.0)
    # Correas: costuras en v = 0,15 y 0,85 con puntadas cada 0,07 studs.
    lado = N.mate("MINIMUM", N.mate("ABSOLUTE", N.mate("SUBTRACT", a[1], 0.16)),
                  N.mate("ABSOLUTE", N.mate("SUBTRACT", a[1], 0.84)))
    puntada = N.mate("LESS_THAN", N.mate("FRACT", N.mate("MULTIPLY", a[0], 14.0)), 0.55)
    costura = N.mate("MULTIPLY", N.mate("LESS_THAN", lado, 0.035), puntada)
    # Silla: aux.x en [-1, 1] a lo ancho, P.y a lo largo.
    px_, py_, _ = N.sep(P)
    borde_silla = N.mate("LESS_THAN", N.mate("ABSOLUTE", N.mate("SUBTRACT", N.mate("ABSOLUTE", a[0]), 0.86)), 0.035)
    puntada_s = N.mate("LESS_THAN", N.mate("FRACT", N.mate("MULTIPLY", py_, 14.0)), 0.55)
    costura_s = N.mate("MULTIPLY", borde_silla, puntada_s)
    rombo = N.mate("MINIMUM", N.mate("ABSOLUTE", N.mate("SINE", N.mate("MULTIPLY", N.mate("ADD", px_, py_), 9.0))),
                   N.mate("ABSOLUTE", N.mate("SINE", N.mate("MULTIPLY", N.mate("SUBTRACT", px_, py_), 9.0))))
    acolchado = N.mate("MULTIPLY", N.mate("LESS_THAN", rombo, 0.12), N.mate("LESS_THAN", N.mate("ABSOLUTE", a[0]), 0.8))
    gasto = N.mate("ADD",
                   N.mate("EXPONENT", N.mate("MULTIPLY", N.mate("POWER", N.mate("SUBTRACT", py_, ASIENTO_PILOTO_Y), 2.0),
                                             -5.0)),
                   N.mate("EXPONENT", N.mate("MULTIPLY", N.mate("POWER", N.mate("SUBTRACT", py_, ASIENTO_PASAJERO_Y), 2.0),
                                             -5.0)))
    gasto = N.mate("MULTIPLY", N.mate("MULTIPLY", gasto, es_silla),
                   N.mate("SUBTRACT", 1.0, N.mate("POWER", N.mate("ABSOLUTE", a[0]), 2.0)), clamp=True)
    costura = N.mate("MAXIMUM", N.mate("MULTIPLY", costura, N.mate("SUBTRACT", 1.0, es_silla)), costura_s)
    col = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.3, 0.8, arrugas), 0.4), lin("cuero"), (0.03, 0.012, 0.008))
    col = N.mezcla(N.mate("MULTIPLY", gasto, 0.6), col, (0.2, 0.1, 0.06))
    col = N.mezcla(N.mate("MULTIPLY", acolchado, 0.5), col, (0.02, 0.008, 0.005))
    col = N.mezcla(costura, col, lin("costura"))
    N.poner("Base Color", col)
    N.poner("Roughness", N.sep(N.mezcla(gasto, 0.66, 0.4))[0])
    h = N.mate("ADD", N.mate("MULTIPLY", grano, 0.25), N.mate("MULTIPLY", costura, 0.6))
    h = N.mate("SUBTRACT", h, N.mate("MULTIPLY", acolchado, 0.5))
    h = N.mate("ADD", h, N.mate("MULTIPLY", arrugas, 0.3))
    N.poner("Normal", N.relieve(h, fuerza=0.6, distancia=0.012))
    return mat


def material_trenza():
    """Riendas trenzadas con fibra vegetal (aux = u en studs a lo largo, ángulo)."""
    mat = bpy.data.materials.new("trenza")
    N = T.Nodos(mat)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    s1 = N.mate("SINE", N.mate("MULTIPLY", N.mate("ADD", N.mate("MULTIPLY", a[1], 3.0), N.mate("MULTIPLY", a[0], 11.0)),
                                 math.tau))
    s2 = N.mate("SINE", N.mate("MULTIPLY", N.mate("SUBTRACT", N.mate("MULTIPLY", a[1], 3.0), N.mate("MULTIPLY", a[0], 11.0)),
                                 math.tau))
    trama = N.mate("MAXIMUM", s1, s2)
    col = N.mezcla(smooth(N, -0.2, 0.8, trama), lin("fibra2"), lin("fibra"))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.8)
    N.poner("Normal", N.relieve(trama, fuerza=0.7, distancia=0.01))
    return mat


def material_hueso():
    mat = bpy.data.materials.new("hueso")
    N = T.Nodos(mat)
    r = N.ruido(N.pos(), 9.0, 5.0, 0.6)
    vetas = N.ruido(N.vmate("MULTIPLY", N.pos(), (1, 1, 7)), 4.0, 3.0)
    col = N.mezcla(smooth(N, 0.45, 0.8, r), lin("hueso"), (0.42, 0.36, 0.26))
    col = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.55, 0.7, vetas), 0.4), col, (0.3, 0.24, 0.16))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.5)
    N.poner("Normal", N.relieve(N.mate("ADD", r, N.mate("MULTIPLY", vetas, 0.5)), fuerza=0.4, distancia=0.01))
    return mat


def materiales(mapas):
    m = {}
    m["piel"] = material_piel(mapas)
    m["escama"] = material_escama()
    m["cuero"] = material_cuero()
    m["trenza"] = material_trenza()
    m["hueso"] = material_hueso()
    m["neon"], N = T.material_simple("neon", (0.6, 0.97, 1.0), rug=0.22, emision=lin("neon"), fuerza=1.0)
    m["hierro"], N = T.material_simple("hierro", lin("hierro"), rug=0.42, metal=0.9, relieve=(60.0, 0.35))
    m["esclera"], N = T.material_simple("esclera", lin("esclera"), rug=0.22, relieve=(18.0, 0.1))
    m["pupila"], N = T.material_simple("pupila", (0.002, 0.001, 0.003), rug=0.08)
    m["membrana"], N = T.material_simple("membrana", lin("membrana"), rug=0.28, relieve=(40.0, 0.15))
    m["cornea"], N = T.material_simple("cornea", T.srgb("#FFD9A0"), rug=0.04)
    m["diente"], N = T.material_simple("diente", lin("diente"), rug=0.38, relieve=(35.0, 0.2))
    m["espina"], N = T.material_simple("espina", lin("espina"), rug=0.34, relieve=(25.0, 0.2))
    m["parasito"], N = T.material_simple("parasito", lin("parasito"), rug=0.88, relieve=(55.0, 0.8))

    # Iris ámbar con fibras radiales (aux = radio 0..1, ángulo) y un brillo suave: el ojo está vivo.
    mat = bpy.data.materials.new("iris")
    N = T.Nodos(mat)
    a = N.sep(N.atributo("aux").outputs["Vector"])
    # Fibras radiales finas (ruido estirado en el ángulo) y anillos: degradado dorado -> ámbar -> borde oscuro.
    fibras = N.ruido(N.combinar(N.mate("MULTIPLY", a[1], 90.0), N.mate("MULTIPLY", a[0], 1.5), 0.0), 2.0, 2.0, 0.4,
                     dim="2D")
    col = N.mezcla(smooth(N, 0.15, 0.75, a[0]), (1.0, 0.72, 0.28), lin("ojo"))
    col = N.mezcla(N.mate("MULTIPLY", smooth(N, 0.45, 0.75, fibras), 0.45), col, (0.55, 0.22, 0.03))
    col = N.mezcla(smooth(N, 0.82, 1.0, a[0]), col, (0.12, 0.04, 0.0))
    N.poner("Base Color", col)
    N.poner("Roughness", 0.3)
    N.poner("Emission Color", N.mezcla(0.75, (0, 0, 0), col))  # brillo suave: el ojo está vivo
    N.poner("Emission Strength", 0.35)
    N.poner("Normal", N.relieve(fibras, fuerza=0.4, distancia=0.004))
    m["iris"] = mat

    # Aguijón: negro violeta, liso y brillante (húmedo).
    mat = bpy.data.materials.new("aguijon")
    N = T.Nodos(mat)
    vetas = N.ruido(N.vmate("MULTIPLY", N.pos(), (2, 2, 8)), 6.0, 3.0)
    N.poner("Base Color", N.mezcla(smooth(N, 0.5, 0.75, vetas), lin("aguijon"), (0.06, 0.02, 0.1)))
    N.poner("Roughness", 0.1)
    m["aguijon"] = mat
    return m


# --------------------------------------------------------------------------------------------------------------
# Construcción
# --------------------------------------------------------------------------------------------------------------

PIEZAS_CAMPO = ["Cuerpo_Central", "Cabeza", "Mandibula", "Ala_Izquierda_Base", "Ala_Izquierda_Punta",
                "Ala_Derecha_Base", "Ala_Derecha_Punta", "Cola", "Cola_Punta"]
PIEZAS_RIG = PIEZAS_CAMPO + ["Tentaculo_Izq", "Tentaculo_Der"]
PADRE = {"Cuerpo_Central": None, "Cabeza": "Cuerpo_Central", "Mandibula": "Cabeza",
         "Ala_Izquierda_Base": "Cuerpo_Central", "Ala_Izquierda_Punta": "Ala_Izquierda_Base",
         "Ala_Derecha_Base": "Cuerpo_Central", "Ala_Derecha_Punta": "Ala_Derecha_Base",
         "Cola": "Cuerpo_Central", "Cola_Punta": "Cola", "Tentaculo_Izq": "Cabeza", "Tentaculo_Der": "Cabeza",
         "Ojos_Cornea": "Cabeza"}
# Peso de cada pieza al repartir el presupuesto que dejan los detalles.
PESO_TRIS = {"Cuerpo_Central": 2.6, "Cabeza": 1.55, "Mandibula": 0.42, "Ala_Izquierda_Base": 1.05,
             "Ala_Derecha_Base": 1.05, "Ala_Izquierda_Punta": 0.7, "Ala_Derecha_Punta": 0.7, "Cola": 0.24,
             "Cola_Punta": 0.15}


def construir_altas(campo, rapido):
    altas = {}
    for nombre in PIEZAS_CAMPO:
        mn, mx, vox = F.CAJAS[nombre]
        t = time.time()
        vol, o, p = C.volumen(F.campo_pieza(campo, nombre), mn, mx, vox * (1.7 if rapido else 1.0))
        v, c = C.malla_de_volumen(vol, o, p)
        ob = T.malla_numpy(nombre + "_alta", v, c)
        T.normales_fuera(ob)
        T.suave(ob)
        ob["centro_masa"] = list(C.centro_de_masa(vol, o, p))
        altas[nombre] = ob
        print(f"[forma] {nombre}: {len(c)} tri ({time.time() - t:.1f}s)")
    return altas


def suelo_y_techo(bvh, x, y):
    p1, n1 = D.proyectar(bvh, x, y)
    p2, n2 = D.proyectar(bvh, x, y, abajo=True)
    return p1, n1, p2, n2


def excluido_escama(x, y):
    ax = abs(x)
    if y > 3.32 or y < -6.2:
        return True
    if ax < SILLA_ANCHO + 0.18 and SILLA_Y[0] - 0.15 < y < SILLA_Y[1] + 0.1:
        return True
    for (sx, sy, _) in F.ESPIRACULOS:
        if math.hypot(ax - sx, y - sy) < 0.52:
            return True
    for (rx, ry) in RUNAS_ARRIBA:
        if math.hypot(x - rx, y - ry) < 0.44:
            return True
    if math.hypot(ax - ALFORJA[0], y - ALFORJA[1]) < 0.62:
        return True
    if math.hypot(ax - ESTRIBO[0], y - ESTRIBO[1]) < 0.36:
        return True
    if ax > 0.8 and abs(y - (ESTRIBO[1] + 0.38)) < 0.22 and ax < ESTRIBO[0] + 0.1:
        return True
    for pts in VENAS_LOMO:
        lis = C.remuestrear(np.array(pts), 0.1)
        if np.min(np.hypot(lis[:, 0] - x, lis[:, 1] - y)) < 0.2:
            return True
    for pts in CICATRICES[3:4]:
        lis = C.remuestrear(np.array(pts), 0.1)
        if np.min(np.hypot(lis[:, 0] - x, lis[:, 1] - y)) < 0.13:
            return True
    (cx, cy), (rx, ry), _ = REGENERADAS[1]
    if ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 < 1.2:
        return True
    return False


def detalles_cuerpo(bvh, rnd, mats_usados):
    """Escamas, cresta, venas, runas, parásitos y todo el arnés del cuerpo."""
    g = T.Geo("Cuerpo_Central_det")
    datos = {}

    # --- Escamas hexagonales con relieve real (lomo central) ---
    paso = 0.41
    n_esc = 0

    def tam_local(ax, y):
        return (1 - 0.30 * C.sstep(0.6, 1.95, ax)) * (1 - 0.22 * C.sstep(-3.6, -6.2, y))

    y = -6.12
    fila = 0
    while y < 3.4:
        # La separación sigue al tamaño: las escamas se hacen pequeñas hacia los bordes sin dejar huecos.
        sy = tam_local(0.0, y)
        for lado in (1, -1):
            x = 0.30 + (paso * sy * 0.5 if fila % 2 else 0.0)
            while x < 1.98:
                t_ = tam_local(x, y)
                xx = lado * x
                if not excluido_escama(xx, y):
                    k = F.campos_2d(np.array([xx]), np.array([y]))
                    if -k["d2"][0] >= 0.4:
                        p, n = D.proyectar(bvh, xx + rnd.uniform(-0.015, 0.015), y + rnd.uniform(-0.015, 0.015))
                        if p is not None:
                            D.escama_hex(g, p, n, 0.42 * t_, 0.04 + 0.022 * (1 - C.sstep(0.5, 1.9, x)), "escama",
                                         giro=rnd.uniform(-0.08, 0.08), rota=rnd.random() < 0.06,
                                         aux=(rnd.random(), 0.0, 2.0), rnd=rnd, borde=0.018)
                            n_esc += 1
                x += paso * t_
        y += paso * 0.866 * sy
        fila += 1
    # --- Cresta dorsal: escamas grandes y elevadas de la cabeza a la cola (detrás de la silla) ---
    for y in np.arange(-6.15, SILLA_Y[0] - 0.25, 0.5):
        p, n = D.proyectar(bvh, 0.0, y)
        if p is None:
            continue
        tam = 0.36 * (1 - 0.3 * C.sstep(-3.5, -6.2, y))
        D.escama_hex(g, p, n, tam, 0.13 * (1 - 0.3 * C.sstep(-3.5, -6.2, y)), "escama", alargada=1.5,
                     aux=(rnd.random() * 0.4, 0.0, 2.0), dir_ref=Vector((0, 1, 0)), hundir=0.06)
        n_esc += 1
    datos["escamas"] = n_esc

    # --- Venas de luz en relieve (0,03) y sus estrellas ---
    for pts in VENAS_LOMO:
        curva = C.remuestrear(C.catmull_rom(pts, 8, cerrada=False), 0.17)
        ps, ns = [], []
        for (x, y) in curva:
            p, n = D.proyectar(bvh, x, y)
            if p is not None:
                ps.append(p)
                ns.append(n)
        D.cinta(g, ps, ns, 0.065, 0.032, "neon", aux_flag=4.0, separacion=-0.008)
    for (x, y) in NODOS_VENA:
        p, n = D.proyectar(bvh, x, y)
        D.disco(g, p - n * 0.01, n, 0.075, "neon", seg=8, anillos=1, abombado=0.055)

    # --- Runas de domesticación: anillos de cicatriz elevados alrededor de la cincha ---
    for (x, y), abajo in [(r, False) for r in RUNAS_ARRIBA] + [(r, True) for r in RUNAS_ABAJO]:
        ps, ns = [], []
        for t in np.linspace(0, math.tau, 14, endpoint=False):
            p, n = D.proyectar(bvh, x + 0.27 * math.cos(t), y + 0.27 * math.sin(t), abajo=abajo)
            ps.append(p)
            ns.append(n)
        D.cinta(g, ps, ns, 0.05, 0.028, "piel", cerrada=True, separacion=-0.006, aux_flag=0.0)

    # --- Parásitos incrustados (como percebes) en el vientre, junto a la cola ---
    for (x, y) in PARASITOS_VIENTRE:
        p, n = D.proyectar(bvh, x, y, abajo=True)
        parasito(g, p, n, rnd)

    arnes_cuerpo(g, bvh, rnd, datos)
    return g, datos


def parasito(g, p, n, rnd):
    t1, t2, n = D.marco(n)
    s = rnd.uniform(0.8, 1.25)
    anillos = []
    for (r, h) in ((0.075, -0.03), (0.07, 0.01), (0.042, 0.065), (0.026, 0.055), (0.012, 0.02)):
        fila = []
        for k in range(6):
            a = math.tau * k / 6 + rnd.uniform(-0.15, 0.15)
            fila.append(p + (t1 * math.cos(a) + t2 * math.sin(a)) * r * s + n * h * s)
        anillos.append(fila)
    g.loft(anillos, "parasito", tapar_inicio=True, tapar_fin=True)


def arnes_cuerpo(g, bvh, rnd, datos):
    # --- Cincha: correa ancha alrededor del cuerpo detrás de la cabeza ---
    yc = sum(CINCHA_Y) / 2
    ancho = CINCHA_Y[1] - CINCHA_Y[0]
    centro = Vector((0, yc, 0.05))
    ps, ns = [], []
    for t in np.linspace(0, math.tau, 60, endpoint=False):
        d = Vector((math.cos(t), 0, math.sin(t)))
        p, n = D.proyectar_hacia(bvh, centro + d * 6.0, -d, 12.0)
        if p is None:
            continue
        ps.append(p)
        ns.append(n)
    lateral = [Vector((0, 1, 0))] * len(ps)
    lat = []
    for i in range(len(ps)):
        t = (ps[(i + 1) % len(ps)] - ps[i - 1]).normalized()
        lat.append(t.cross(ns[i]).normalized() * (1 if t.cross(ns[i]).y > 0 else -1))
    D.cinta(g, ps, ns, ancho, 0.07, "cuero", aux_flag=1.0, separacion=0.012, cerrada=True, lateral=lat)
    # Hebillas de hueso tallado sobre la cincha.
    for lado in (1, -1):
        p, n = D.proyectar(bvh, lado * HEBILLA_X, yc)
        ex = Vector((1, 0, 0))
        ex = (ex - n * ex.dot(n)).normalized()
        ey = n.cross(ex).normalized()
        c = p + n * (0.012 + 0.07 + 0.03)
        for dx in (-0.13, 0.13):
            D.caja(g, c + ex * dx, (ex, ey, n), (0.06, 0.46, 0.055), "hueso")
        for dy in (-0.2, 0.2):
            D.caja(g, c + ey * dy, (ex, ey, n), (0.32, 0.06, 0.055), "hueso")
        D.caja(g, c + ex * 0.02 * lado, (ex, ey, n), (0.2, 0.045, 0.04), "hueso")  # púa
        D.cono(g, c + ex * 0.12 * lado + n * 0.02, ex * lado, 0.07, 0.03, "hueso", lados=5)

    # --- Silla de montar (para piloto y pasajero) ---
    nx, ny = 9, 17
    y0, y1 = SILLA_Y
    ym, hy = (y0 + y1) / 2, (y1 - y0) / 2
    arriba, abajo, rim = {}, {}, []
    for j in range(ny):
        v = -1 + 2 * j / (ny - 1)
        for i in range(nx):
            u = -1 + 2 * i / (nx - 1)
            fy = 1 - 0.12 * u ** 8
            fx = 1 - 0.22 * v ** 8
            y = ym + hy * v * fy
            # Cintura entre los dos asientos y punta delantera más estrecha.
            cintura = 1 - 0.24 * math.exp(-((y - 1.45) / 0.35) ** 2) - 0.25 * C.sstep(2.9, 3.42, y)
            x = SILLA_ANCHO * u * fx * cintura
            p, n = D.proyectar(bvh, x, y)
            borde = i in (0, nx - 1) or j in (0, ny - 1)
            plano = 1 - u * u
            esp = 0.10 + 0.05 * plano
            esp -= 0.06 * math.exp(-((y - ASIENTO_PILOTO_Y) / 0.38) ** 2) * plano
            esp -= 0.055 * math.exp(-((y - ASIENTO_PASAJERO_Y) / 0.38) ** 2) * plano
            esp += 0.20 * math.exp(-((y - 1.62) / 0.17) ** 2) * (1 - 0.55 * u * u)   # respaldo del piloto
            esp += 0.16 * math.exp(-((y - (y0 + 0.14)) / 0.17) ** 2) * (1 - 0.5 * u * u)  # respaldo del pasajero
            esp += 0.10 * math.exp(-((y - 1.18) / 0.14) ** 2) * (1 - 0.6 * u * u)   # asidero del pasajero
            esp += 0.13 * math.exp(-((y - (y1 - 0.2)) / 0.2) ** 2) * (1 - 0.5 * u * u)
            if borde:
                esp = 0.04
            aux = (u, (y - y0) / (y1 - y0), 2.0)
            arriba[i, j] = g.v(p + n * (0.01 + esp), aux)
            abajo[i, j] = g.v(p + n * 0.008, aux)
    for j in range(ny - 1):
        for i in range(nx - 1):
            g.cara((arriba[i, j], arriba[i + 1, j], arriba[i + 1, j + 1], arriba[i, j + 1]), "cuero")
            g.cara((abajo[i, j + 1], abajo[i + 1, j + 1], abajo[i + 1, j], abajo[i, j]), "cuero")
    borde_idx = [(i, 0) for i in range(nx)] + [(nx - 1, j) for j in range(1, ny)] + \
                [(i, ny - 1) for i in range(nx - 2, -1, -1)] + [(0, j) for j in range(ny - 2, 0, -1)]
    for k in range(len(borde_idx)):
        a, b = borde_idx[k], borde_idx[(k + 1) % len(borde_idx)]
        g.cara((abajo[a], abajo[b], arriba[b], arriba[a]), "cuero")
    # Perilla de hueso delante (para atar las riendas) y medidas de los asientos.
    p, n = D.proyectar(bvh, 0.0, y1 - 0.2)
    base_perilla = p + n * 0.15
    D.cono(g, base_perilla - n * 0.06, n + Vector((0, 0.35, 0)), 0.30, 0.075, "hueso", lados=7, anillos=2,
           romo=True)
    datos["perilla"] = list(base_perilla + n * 0.2)
    for nombre, ya in (("piloto", ASIENTO_PILOTO_Y), ("pasajero", ASIENTO_PASAJERO_Y)):
        p, n = D.proyectar(bvh, 0.0, ya)
        espesor = 0.17 - 0.055
        datos[nombre] = list(p + n * (0.01 + espesor))

    # --- Estribos de hueso con su correa y anilla de hierro ---
    for lado in (1, -1):
        pts, ns = [], []
        for t in np.linspace(0, 1, 9):
            x = lado * (SILLA_ANCHO - 0.04 + t * (ESTRIBO[0] - SILLA_ANCHO + 0.04))
            y = ESTRIBO[1] + 0.42 * (1 - t) + 0.04
            p, n = D.proyectar(bvh, x, y)
            pts.append(p)
            ns.append(n)
        D.cinta(g, pts, ns, 0.13, 0.035, "cuero", aux_flag=1.0, separacion=0.01)
        p0, n0 = pts[0], ns[0]
        D.toro(g, p0 + n0 * 0.06, Vector((0, 1, 0)), 0.06, 0.016, "hierro", seg=8, lados=4)
        fin, nf = pts[-1], ns[-1]
        dir_ = (pts[-1] - pts[-2]).normalized()
        D.toro(g, fin + nf * 0.17 + dir_ * 0.02, dir_, 0.15, 0.034, "hueso", seg=12, lados=5,
               escala_r=(1.0, 1.15))

    # --- Alforjas de cuero con cierre de hueso ---
    for lado in (1, -1):
        p, n = D.proyectar(bvh, lado * ALFORJA[0], ALFORJA[1])
        ex = Vector((lado, 0, 0))
        ex = (ex - n * ex.dot(n)).normalized()
        ey = n.cross(ex).normalized()
        rot = D.matriz((ex, ey, n))
        tam = (0.62, 0.74, 0.36)
        c = p + n * (tam[2] / 2 - 0.015)
        g.caja_redonda(c, tam, "cuero", rot=rot, seg=3, aux=(0.0, 0.5, 1.0), redondeo=0.75)
        # Solapa blanda que cae sobre el costado exterior y cierre de hueso.
        g.caja_redonda(c + n * 0.15 + ex * 0.1, (0.5, 0.66, 0.08), "cuero", rot=rot, seg=2, aux=(0.0, 0.5, 1.0),
                       redondeo=0.8)
        D.cono(g, c + n * 0.1 + ex * 0.33 - ey * 0.09, ey, 0.18, 0.03, "hueso", lados=6, radio_punta=0.024)
        g.v(c)  # (sin cara: ancla para depurar)
        # Correa a la silla.
        pts, ns = [], []
        for t in np.linspace(0, 1, 5):
            x = lado * (SILLA_ANCHO - 0.05 + t * (ALFORJA[0] - 0.29 - SILLA_ANCHO + 0.05))
            pp, nn = D.proyectar(bvh, x, ALFORJA[1] + 0.02)
            pts.append(pp)
            ns.append(nn)
        D.cinta(g, pts, ns, 0.1, 0.03, "cuero", aux_flag=1.0, separacion=0.012)
        D.toro(g, pts[0] + ns[0] * 0.055, Vector((0, 1, 0)), 0.05, 0.014, "hierro", seg=8, lados=4)


def detalles_cabeza(bvh, bvh_cab_cuerpo, rnd, perilla):
    g = T.Geo("Cabeza_det")
    cornea = T.Geo("Ojos_Cornea")
    ox, oy, oz = F.OJO_CENTRO
    for lado in (1, -1):
        c = Vector((lado * ox, oy, oz))
        d = Vector((lado * 1.0, 0.32, 0.24)).normalized()
        ojo(g, cornea, c, d, lado)
    # --- Placas craneales (casco natural) ---
    paso = 0.5
    for j, y in enumerate(np.arange(F.CORTE_CABEZA + 0.2, 5.95, paso * 0.866)):
        off = paso / 2 if j % 2 else 0.0
        for x in np.arange(-1.05 + off, 1.06, paso):
            if abs(x) > 0.9 and y < 5.5:
                continue
            k = F.campos_2d(np.array([x]), np.array([y]))
            if -k["d2"][0] < 0.32:
                continue
            p, n = D.proyectar(bvh, x, y)
            if p is None:
                continue
            tam = 0.5 * (1 - 0.22 * C.sstep(0.4, 1.1, abs(x)) - 0.2 * C.sstep(5.3, 5.95, y))
            D.escama_hex(g, p, n, tam, 0.07, "escama", giro=rnd.uniform(-0.15, 0.15),
                         aux=(0.3 + 0.4 * rnd.random(), 0.0, 2.0), rnd=rnd, rota=rnd.random() < 0.08)
    # --- Dientes romos superiores (cuelgan del paladar) ---
    cx, cy, cz = F.BOCA_CENTRO
    rx, ry, rz = F.BOCA_RADIOS
    for i in range(8):
        a = math.radians(-66 + i * (132 / 7))
        x, y = rx * 0.74 * math.sin(a), cy + ry * 0.74 * math.cos(a)
        p, n = D.proyectar_hacia(bvh, (x, y, cz), (0, 0, 1), 1.0)
        if p is None:
            continue
        D.cono(g, p + Vector((0, 0, 0.02)), Vector((0, 0.15, -1)), 0.095, 0.034, "diente", lados=6, anillos=2,
               romo=True)
    riendas(g, bvh_cab_cuerpo, perilla)
    return g, cornea


def ojo(g, cornea, c, d, lado):
    """Ojo de 1 stud: globo oscuro, iris ámbar abierto al frente, pupila de estrella de 4 puntas, córnea
    abombada (pieza aparte) y membrana nictitante recogida en el lagrimal."""
    R = F.OJO_RADIO
    t1, t2, d = D.marco(d, Vector((0, 0, 1)))  # t1 hacia arriba aproximado
    alfa = 1.0
    anillos = []
    for j in range(0, 7):
        th = math.pi - (math.pi - alfa) * j / 6
        fila = [c + (t1 * math.cos(math.tau * k / 14) + t2 * math.sin(math.tau * k / 14)) * R * math.sin(th)
                + d * R * math.cos(th) for k in range(14)]
        anillos.append(fila)
    anillos[0] = [c - d * R + (p - (c - d * R)) * 0.0001 for p in anillos[0]]
    vs = g.loft(anillos[1:], "esclera", tapar_inicio=False, tapar_fin=False, punta_inicio=(c - d * R, (0, 0, 0)))
    # Iris: disco ligeramente cóncavo que cierra el globo (aux = radio, ángulo).
    rim = vs[-1]
    plano = c + d * R * math.cos(alfa)
    ri = R * math.sin(alfa)
    filas = [rim]
    for j, f in enumerate((0.72, 0.42, 0.18)):
        filas.append([g.v(plano - d * 0.05 * (1 - f) + (t1 * math.cos(math.tau * k / 14) +
                                                        t2 * math.sin(math.tau * k / 14)) * ri * f,
                          (f, k / 14, 5.0)) for k in range(14)])
    # Recolorear el anillo exterior con aux de iris: se duplica para que el iris tenga su propio material.
    filas[0] = [g.v(v.co, (1.0, k / 14, 5.0)) for k, v in enumerate(rim)]
    for j in range(len(filas) - 1):
        for k in range(14):
            k2 = (k + 1) % 14
            g.cara((filas[j][k], filas[j][k2], filas[j + 1][k2], filas[j + 1][k]), "iris")
    centro = g.v(plano - d * 0.05, (0.0, 0.0, 5.0))
    for k in range(14):
        g.cara((filas[-1][k], filas[-1][(k + 1) % 14], centro), "iris")
    # Pupila: estrella de 4 puntas con grosor, sobre el iris.
    base = plano - d * 0.05 + d * 0.006
    estrella = []
    for k in range(8):
        a = math.tau * k / 8  # puntas arriba/abajo/delante/detrás
        r = ri * (0.56 if k % 2 == 0 else 0.22)
        # Sigue la concavidad del iris para no quedar enterrada en él.
        estrella.append(t1 * math.cos(a) * r + t2 * math.sin(a) * r + d * 0.05 * (r / ri))
    arriba_ = [g.v(base + e + d * 0.012) for e in estrella]
    abajo_ = [g.v(base + e * 1.02 - d * 0.004) for e in estrella]
    ca, cb = g.v(base + d * 0.016), g.v(base - d * 0.004)
    for k in range(8):
        k2 = (k + 1) % 8
        g.cara((arriba_[k], arriba_[k2], ca), "pupila")
        g.cara((abajo_[k2], abajo_[k], cb), "pupila")
        g.cara((abajo_[k], abajo_[k2], arriba_[k2], arriba_[k]), "pupila")
    # Córnea: casquete achatado que cubre el iris y apoya en el borde del globo.
    # Esfera de la córnea que pasa por el borde del iris y asoma 0,06 por delante del globo.
    h0 = R * math.cos(alfa)
    A = R + 0.06
    k_ = (A * A - R * R) / (2 * (A - h0))
    rho = A - k_
    alfa_cornea = math.acos(max(-1.0, min(1.0, (h0 - k_) / rho)))
    filas = []
    for j in range(1, 5):
        th = alfa_cornea * j / 4
        filas.append([c + d * (k_ + rho * math.cos(th)) +
                      (t1 * math.cos(math.tau * k / 14) + t2 * math.sin(math.tau * k / 14)) * rho * math.sin(th)
                      for k in range(14)])
    filas.reverse()
    cornea.loft(filas, "cornea", punta_fin=(c + d * (k_ + rho), (0, 0, 0)), tapar_inicio=True)
    del alfa_cornea
    # Membrana nictitante recogida en el ángulo delantero (concha fina de dos capas).
    fil_in, fil_out = [], []
    for j in range(4):
        th = alfa + 0.02 + 0.30 * j / 3
        fi, fo = [], []
        for k in range(9):
            ph = math.radians(-75 + 150 * k / 8)
            dirp = (t1 * math.cos(ph) * 0.0 + t1 * 0) + t2 * 0
            # ángulo phi medido desde la dirección "delante" proyectada
            delante = Vector((0, 1, 0)) - d * d.y
            delante.normalize()
            arr = d.cross(delante).normalized()
            u = delante * math.cos(ph) + arr * math.sin(ph)
            del dirp
            espesor = 0.015 * (1 - (j / 3) ** 2) + 0.004
            radial = d * math.cos(th) + u * math.sin(th)
            fi.append(c + radial * (R + 0.003))
            fo.append(c + radial * (R + 0.003 + espesor))
        fil_in.append(fi)
        fil_out.append(fo)
    vin = [[g.v(p) for p in f] for f in fil_in]
    vout = [[g.v(p) for p in f] for f in fil_out]
    for j in range(3):
        for k in range(8):
            g.cara((vout[j][k], vout[j][k + 1], vout[j + 1][k + 1], vout[j + 1][k]), "membrana")
            g.cara((vin[j + 1][k], vin[j + 1][k + 1], vin[j][k + 1], vin[j][k]), "membrana")
    for k in range(8):
        g.cara((vin[0][k], vin[0][k + 1], vout[0][k + 1], vout[0][k]), "membrana")
        g.cara((vout[3][k], vout[3][k + 1], vin[3][k + 1], vin[3][k]), "membrana")
    for j in range(3):
        g.cara((vin[j][0], vout[j][0], vout[j + 1][0], vin[j + 1][0]), "membrana")
        g.cara((vin[j + 1][8], vout[j + 1][8], vout[j][8], vin[j][8]), "membrana")


def riendas(g, bvh, perilla):
    """Dos riendas trenzadas desde la perilla de la silla hasta la base de los tentáculos sensoriales."""
    perilla = Vector(perilla)
    for lado in (1, -1):
        ctrl = [perilla + Vector((lado * 0.08, -0.02, -0.04))]
        for (x, y, h) in ((0.38, 3.75, 0.2), (0.62, 4.35, 0.055), (0.92, 5.1, 0.05), (1.18, 5.72, 0.05)):
            p, n = D.proyectar(bvh, lado * x, y)
            ctrl.append(p + n * h)
        tx, ty, _ = TENTACULO_BASE
        ctrl.append(Vector((lado * 1.42, 6.07, -0.06)))
        ctrl.append(Vector((lado * (tx + 0.02), ty + 0.32, -0.32)))
        curva = C.remuestrear(C.catmull_rom([tuple(p) for p in ctrl], 10, cerrada=False), 0.13)
        largo = [0.0]
        for i in range(1, len(curva)):
            largo.append(largo[-1] + float(np.linalg.norm(curva[i] - curva[i - 1])))
        g.tubo([Vector(p) for p in curva], [0.036] * len(curva), "trenza", lados=5,
               aux_fn=lambda t, a: (t * largo[-1], a / math.tau, 3.0))


TENTACULO_BASE = (1.38, 5.72, -0.20)


def tentaculo(nombre, lado, bvh_cabeza):
    """Tentáculo sensorial (aleta cefálica): cono achatado de 4 secciones articuladas, con 5 filamentos en la
    punta. El primer anillo se ajusta a la piel de la cabeza dejando 0,02 de separación."""
    g = T.Geo(nombre)
    bx, by, bz = TENTACULO_BASE
    # Cuelga hacia delante y abajo y la punta se enrosca hacia atrás y hacia dentro (como un helecho joven).
    ctrl = [(lado * bx, by, bz), (lado * 1.44, 6.22, -0.56), (lado * 1.42, 6.78, -1.08), (lado * 1.28, 7.06, -1.66),
            (lado * 1.10, 6.92, -2.10), (lado * 0.98, 6.62, -2.16), (lado * 0.96, 6.46, -1.96)]
    curva = C.catmull_rom(ctrl, 30, cerrada=False)
    acum = np.concatenate([[0], np.cumsum(np.linalg.norm(np.diff(curva, axis=0), axis=1))])
    total = acum[-1]
    ts = []
    for s in range(4):
        for f in (0.0, 0.1, 0.35, 0.65, 0.9):
            ts.append((s + f) / 4)
    ts.append(1.0)
    pts, rad = [], []
    for t in ts:
        d = t * total
        p = np.array([np.interp(d, acum, curva[:, i]) for i in range(3)])
        s = (t * 4) % 1.0 if t < 1 else 1.0
        base = 0.29 * (1 - t) + 0.075 * t
        bulto = 1 + 0.07 * math.sin(math.pi * s) - 0.13 * math.exp(-(s / 0.06) ** 2) * (t > 0.01)
        pts.append(Vector(p))
        rad.append(base * bulto)
    vs = g.tubo(pts, rad, "piel", lados=8, achatado=0.58, arriba=(1, 0, 0), tapas=True,
                aux_fn=lambda t, a: (t, a / math.tau, 1.0))
    # Ajuste del primer anillo a la piel de la cabeza (0,02 por debajo).
    for v in vs[0]:
        p, n, _, _ = bvh_cabeza.ray_cast(v.co + Vector((0, 0, -0.4)), Vector((0, 0, 1)), 1.5)
        if p is not None:
            v.co = p - Vector((0, 0, 0.02))
    # Filamentos sensoriales.
    fin = pts[-1]
    eje = (pts[-1] - pts[-2]).normalized()
    t1, t2, _ = D.marco(eje)
    for k in range(5):
        a = math.tau * k / 5 + 0.3
        dirf = (eje + (t1 * math.cos(a) + t2 * math.sin(a)) * 0.6).normalized()
        q = [fin + (t1 * math.cos(a) + t2 * math.sin(a)) * 0.035]
        for j in range(1, 4):
            q.append(q[-1] + dirf * 0.11 + (t1 * math.cos(a + 1) + t2 * math.sin(a + 1)) * 0.02 * j)
        g.tubo(q, [0.024, 0.018, 0.012, 0.006], "piel", lados=4, punta=True,
               aux_fn=lambda t, a_: (1.0, 0.0, 1.0))
    return g


def detalles_cola(bvh, nombre, ys, rnd):
    g = T.Geo(nombre + "_det")
    for y in ys:
        p, n = D.proyectar(bvh, 0.0, y)
        if p is None:
            continue
        esc = C.sstep(-6.9, -11.4, y)
        D.cono(g, p - n * 0.03, n + Vector((0, -0.55, 0)), 0.30 - 0.12 * esc, 0.068 - 0.026 * esc, "espina", lados=5,
               anillos=1, curva=Vector((0, -0.03, 0)))
    if nombre == "Cola_Punta":
        # Aguijón venenoso curvado como el de un escorpión.
        pts = [(0, -11.50, 0.04), (0, -11.72, 0.05), (0, -11.94, 0.09), (0, -12.16, 0.17), (0, -12.34, 0.29),
               (0, -12.46, 0.43), (0, -12.50, 0.56), (0, -12.44, 0.67)]
        rad = [0.088, 0.105, 0.11, 0.092, 0.07, 0.048, 0.03, 0.014]
        g.tubo([Vector(p) for p in pts], rad, "aguijon", lados=8, punta=True, tapas=True)
    return g


# --------------------------------------------------------------------------------------------------------------
# Principal
# --------------------------------------------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="1")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--sin_render", action="store_true")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    salida = os.path.abspath(args.salida)
    os.makedirs(salida, exist_ok=True)
    tmp = ruta(salida, "_render_tmp")
    t0 = time.time()
    rnd = __import__("random").Random(1234)

    T.escena_vacia()
    campo = F.Campo()
    altas = construir_altas(campo, args.rapido)
    bvh = {n: T.bvh_de([o]) for n, o in altas.items()}
    mapas = mapas_planta(rnd)
    mats = materiales(mapas)

    # --- Detalles por pieza ---
    det = {}
    g, datos = detalles_cuerpo(bvh["Cuerpo_Central"], rnd, mats)
    det["Cuerpo_Central"] = [g.objeto(mats)]
    gc, gcor = detalles_cabeza(bvh["Cabeza"], T.bvh_de([altas["Cabeza"], altas["Cuerpo_Central"]]), rnd,
                               datos["perilla"])
    det["Cabeza"] = [gc.objeto(mats)]
    cornea_obj = gcor.objeto(mats)
    gm = T.Geo("Mandibula_det")
    cx, cy, cz = F.BOCA_CENTRO
    rx, ry, rz = F.BOCA_RADIOS
    for i in range(7):
        a = math.radians(-57 + i * (114 / 6))
        x, y = rx * 0.66 * math.sin(a), cy + ry * 0.66 * math.cos(a)
        p, n = D.proyectar_hacia(bvh["Mandibula"], (x, y, cz), (0, 0, -1), 1.0)
        if p is not None:
            D.cono(gm, p - Vector((0, 0, 0.02)), Vector((0, 0.2, 1)), 0.085, 0.03, "diente", lados=6, anillos=2,
                   romo=True)
    det["Mandibula"] = [gm.objeto(mats)]
    det["Cola"] = [detalles_cola(bvh["Cola"], "Cola", [-7.25, -7.8, -8.35, -8.9, -9.45], rnd).objeto(mats)]
    det["Cola_Punta"] = [detalles_cola(bvh["Cola_Punta"], "Cola_Punta", [-10.2, -10.65, -11.05], rnd).objeto(mats)]
    ga = T.Geo("Ala_Derecha_Base_det")
    for (x, y) in PARASITOS_ALA:
        p, n = D.proyectar(bvh["Ala_Derecha_Base"], x, y, abajo=True)
        parasito(ga, p, n, rnd)
    det["Ala_Derecha_Base"] = [ga.objeto(mats)]
    tent = {"Tentaculo_Izq": tentaculo("Tentaculo_Izq", -1, bvh["Cabeza"]).objeto(mats),
            "Tentaculo_Der": tentaculo("Tentaculo_Der", 1, bvh["Cabeza"]).objeto(mats)}

    for o in altas.values():
        T.asignar_material(o, mats["piel"])

    # --- Presupuesto: lo que dejan los detalles se reparte entre las superficies de campo ---
    tris_det = sum(T.triangulos(o) for lst in det.values() for o in lst)
    tris_det += sum(T.triangulos(o) for o in tent.values()) + T.triangulos(cornea_obj)
    libre = PRESUPUESTO - tris_det - 60
    suma = sum(PESO_TRIS.values())
    print(f"[presupuesto] detalles {tris_det} tri; quedan {libre} para las superficies")

    # --- Altas (para hornear) y bajas (lo que se exporta) ---
    parejas = []
    piezas = {}
    for nombre in PIEZAS_CAMPO:
        alta = altas[nombre]
        objetivo = int(libre * PESO_TRIS[nombre] / suma)
        baja = T.diezmar(alta, objetivo, nombre + "_b")
        T.suave(baja)
        extras_a = [T.copiar(o, o.name + "_a") for o in det.get(nombre, [])]
        extras_b = det.get(nombre, [])
        for o in extras_a + extras_b:
            T.suave(o, angulo=38)
        alta = T.unir([alta] + extras_a, nombre + "_alta")
        baja = T.unir([baja] + extras_b, nombre)
        parejas.append((alta, baja))
        piezas[nombre] = baja
    for nombre, o in tent.items():
        T.suave(o)
        alta = T.copiar(o, nombre + "_alta")
        parejas.append((alta, o))
        piezas[nombre] = o
    T.suave(cornea_obj)
    parejas.append((T.copiar(cornea_obj, "Ojos_Cornea_alta"), cornea_obj))
    piezas["Ojos_Cornea"] = cornea_obj

    # Atributos para el UV: proyección cenital en las superficies grandes y prioridad del lomo.
    for nombre in ("Cuerpo_Central", "Cabeza", "Ala_Izquierda_Base", "Ala_Izquierda_Punta", "Ala_Derecha_Base",
                   "Ala_Derecha_Punta"):
        o = piezas[nombre]
        me = o.data
        plano = me.attributes.new("uv_plano", "FLOAT", "FACE")
        prio = me.attributes.new("uv_prioridad", "FLOAT", "FACE")
        piel = [i for i, s in enumerate(o.material_slots) if s.material and s.material.name.startswith("piel")]
        for p in me.polygons:
            es_piel = p.material_index in piel
            plano.data[p.index].value = 1.0 if (es_piel and abs(p.normal.z) > 0.5) else 0.0
            prio.data[p.index].value = 1.25 if p.normal.z > 0.3 else (0.72 if p.normal.z < -0.3 else 1.0)

    # --- Pivotes (articulaciones) ---
    def medio(x, y):
        k = F.campos_2d(np.array([x]), np.array([y]))
        arriba = k["m"][0] + k["arriba"][0] + k["radio"][0]
        abajo = k["m"][0] - k["abajo"][0] - k["radio"][0]
        return (arriba + abajo) / 2

    def y_medio(ax):
        return (np.interp(ax, *zip(*F.BORDE_ATAQUE)) + np.interp(ax, *zip(*sorted(F.BORDE_FUGA)))) / 2

    pivotes = {
        "Cuerpo_Central": (0.0,) + tuple(altas["Cuerpo_Central"]["centro_masa"])[1:],
        "Cabeza": (0.0, F.CORTE_CABEZA, medio(0.0, F.CORTE_CABEZA)),
        "Mandibula": (0.0, F.BOCA_BISAGRA[0] + 0.03, F.BOCA_BISAGRA[1] - 0.06),
        "Cola": (0.0, F.CORTE_COLA, medio(0.0, F.CORTE_COLA)),
        "Cola_Punta": (0.0, F.CORTE_COLA_PUNTA, -0.05),
        "Tentaculo_Izq": (-TENTACULO_BASE[0], TENTACULO_BASE[1], TENTACULO_BASE[2] - 0.04),
        "Tentaculo_Der": (TENTACULO_BASE[0], TENTACULO_BASE[1], TENTACULO_BASE[2] - 0.04),
    }
    for lado, nom in ((1, "Derecha"), (-1, "Izquierda")):
        ym = float(y_medio(F.CORTE_ALA))
        pivotes[f"Ala_{nom}_Base"] = (lado * F.CORTE_ALA, ym, medio(lado * F.CORTE_ALA, ym))
        ym = float(y_medio(F.CORTE_PUNTA))
        pivotes[f"Ala_{nom}_Punta"] = (lado * F.CORTE_PUNTA, ym, medio(lado * F.CORTE_PUNTA, ym))
    pivotes["Ojos_Cornea"] = pivotes["Cabeza"]
    cm = altas["Cuerpo_Central"].get("centro_masa")
    for nombre, o in piezas.items():
        T.poner_origen(o, pivotes[nombre])
    for a, b in parejas:
        T.poner_origen(a, b.matrix_world.translation)

    # --- Puntos de montaje ---
    montajes = {}
    bvh_ala = {1: bvh["Ala_Derecha_Base"], -1: bvh["Ala_Izquierda_Base"]}
    montajes["Montura_Piloto"] = (Vector(datos["piloto"]) + Vector((0, 0, 0.15)), "Cuerpo_Central")
    montajes["Montura_Pasajero"] = (Vector(datos["pasajero"]) + Vector((0, 0, 0.15)), "Cuerpo_Central")
    for lado, nom in ((-1, "Agarre_Izq"), (1, "Agarre_Der")):
        x = lado * 3.25
        y = float(np.interp(3.25, *zip(*F.BORDE_ATAQUE))) - 0.28
        p, n = D.proyectar(bvh_ala[lado], x, y)
        montajes[nom] = (p + n * 0.15, "Ala_Derecha_Base" if lado > 0 else "Ala_Izquierda_Base")
    mat_montaje, _ = T.material_simple("punto_montaje", (1.0, 0.1, 0.6), rug=0.5)
    cubos = []
    for nom, (p, padre) in montajes.items():
        bpy.ops.mesh.primitive_cube_add(size=0.3, location=p)
        cu = bpy.context.active_object
        cu.name = nom
        cu.data.name = nom
        T.asignar_material(cu, mat_montaje)
        cu["padre"] = padre
        cubos.append(cu)

    # --- UV del atlas y horneado ---
    lista = [piezas[n] for n in PIEZAS_RIG] + [cornea_obj]
    prioridad = {"Cuerpo_Central": 1.15, "Cabeza": 1.35, "Mandibula": 1.0, "Tentaculo_Izq": 1.1,
                 "Tentaculo_Der": 1.1, "Ojos_Cornea": 1.6, "Cola": 0.9, "Cola_Punta": 1.0}
    T.desplegar_piezas(lista, prioridad, margen=0.0035)
    tam = 512 if args.rapido else T.TAM_ATLAS
    rutas, mat_final = T.hornear_atlas(parejas, salida, NOMBRE, tam=tam, muestras=4 if args.rapido else 12,
                                       extrusion=0.07, distancia=0.22)
    for a, _ in parejas:
        bpy.data.objects.remove(a)
    print(f"[ok] horneado ({time.time() - t0:.0f}s)")

    tris = {n: T.triangulos(o) for n, o in piezas.items()}
    total = sum(tris.values())
    print(f"[tris] total {total}: {tris}")

    # Guardado del .blend (para revisar o retocar).
    bpy.ops.wm.save_as_mainfile(filepath=ruta(salida, f"{NOMBRE}.blend"), compress=True)

    # --- Render ---
    if not args.sin_render:
        render(piezas, cubos, salida, tmp, args, total)

    # --- Exportación, verificación y JSON ---
    exportables = [piezas[n] for n in PIEZAS_RIG] + [cornea_obj] + cubos
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in [piezas[n] for n in PIEZAS_RIG if not n.startswith("Cola")]:
        for c_ in o.bound_box:
            w = o.matrix_world @ Vector(c_)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    tam_sin_cola = mx - mn
    for o in [piezas[n] for n in PIEZAS_RIG]:
        for c_ in o.bound_box:
            w = o.matrix_world @ Vector(c_)
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    tam_total = mx - mn
    ruta_fbx = ruta(salida, f"{NOMBRE}.fbx")
    T.exportar_fbx(ruta_fbx, exportables)
    esperado = {o.name: {"pivote": list(o.matrix_world.translation), "tris": T.triangulos(o)} for o in exportables}

    datos_json = {
        "nombre": NOMBRE,
        "bestia": "Manta Estelar",
        "rol": "Exploración / velocidad",
        "jinetes": "1-2",
        "unidades": "studs (1 unidad de Blender = 1 stud; FBX en metros con 1 stud = 0,28 m)",
        "giro_importacion": "180° en el eje vertical aplicado antes de exportar: la bestia mira a -Z en Roblox",
        "coordenadas": "pivotes en Roblox (X derecha, Y arriba, -Z delante) relativos al origen del modelo; "
                       "'modelado' = coordenadas de Blender antes del giro (X derecha, Y delante, Z arriba)",
        "triangulos": {"total_visibles": total, "presupuesto": PRESUPUESTO, "por_pieza": tris,
                       "puntos_de_montaje": 12 * len(cubos)},
        "tamano_studs": {
            "envergadura_largo_alto_sin_cola": [round(tam_sin_cola.x, 2), round(tam_sin_cola.y, 2),
                                                round(tam_sin_cola.z, 2)],
            "con_cola": [round(tam_total.x, 2), round(tam_total.y, 2), round(tam_total.z, 2)],
        },
        "color_neon": "#3DF2FF",
        "texturas": {k: os.path.basename(v) for k, v in rutas.items()},
        "piezas": [
            {"nombre": n, "padre": PADRE[n], "tipo": "rig (Motor6D)" if n in PIEZAS_RIG else "soldada (Weld)",
             "pivote_roblox": T.a_roblox(piezas[n].matrix_world.translation),
             "pivote_modelado": [round(c_, 4) for c_ in piezas[n].matrix_world.translation],
             "triangulos": tris[n]}
            for n in PIEZAS_RIG + ["Ojos_Cornea"]
        ],
        "puntos_montaje": [
            {"nombre": c_.name, "pieza": c_["padre"], "tamano": 0.3, "orientacion": "hacia delante (-Z en Roblox)",
             "posicion_roblox": T.a_roblox(c_.matrix_world.translation),
             "posicion_modelado": [round(v, 4) for v in c_.matrix_world.translation],
             "relativo_a_pieza_roblox": T.a_roblox(c_.matrix_world.translation -
                                                   piezas[c_["padre"]].matrix_world.translation)}
            for c_ in cubos
        ],
        "notas": [
            "Los nombres van sin tilde (Mandibula, Tentaculo_Izq/Der) para que no se estropeen al importar.",
            "Ojos_Cornea va soldada a la Cabeza: en Roblox, material Glass o Transparency 0,35 con su color ámbar.",
            "Los puntos de montaje son cubos de 0,3: en Roblox, Transparency = 1, CanCollide = false.",
            "El atlas es compartido por todas las piezas (SurfaceAppearance con color, normal, roughness y metal).",
        ],
    }
    T.escribir_json(ruta(salida, f"{NOMBRE}.json"), datos_json)
    # Reimportación en escena limpia.
    ok, informe = T.reimportar_y_verificar(ruta_fbx, esperado)
    with open(ruta(salida, "verificacion_fbx.txt"), "w", encoding="utf-8") as f:
        f.write(("OK" if ok else "CON ERRORES") + "\n" + "\n".join(informe) + "\n")
    print("[verificacion]", "OK" if ok else "ERRORES")
    for linea in informe:
        print("   ", linea)
    print(f"[fin] {time.time() - t0:.0f}s")


def render(piezas, cubos, salida, tmp, args, total):
    # Córneas de cristal en el render (en el atlas llevan su color para Roblox).
    vidrio = bpy.data.materials.new("cornea_render")
    N = T.Nodos(vidrio)
    N.poner("Base Color", T.srgb("#FFE3B0"))
    N.poner("Roughness", 0.02)
    N.poner("Transmission Weight", 1.0)
    N.poner("IOR", 1.38)
    atlas = piezas["Ojos_Cornea"].active_material
    T.asignar_material(piezas["Ojos_Cornea"], vidrio)
    for c_ in cubos:
        c_.hide_render = True
    objs = [o for o in piezas.values()]
    T.preparar_estudio(9.0)
    rutas = T.renderizar_vistas(objs, tmp, T.VISTAS_TURNAROUND, tam=420 if args.rapido else 760,
                                muestras=24 if args.rapido else 96, prefijo="t_", margen=1.02)
    notas = [f"Ronda {args.ronda} · {total} triángulos (presupuesto {PRESUPUESTO}) · 11 piezas de rig + córneas",
             "Atlas 2048 horneado: color, normal, roughness, metalness, emisión (#3DF2FF)"]
    T.montar_turnaround(rutas, ruta(salida, f"{NOMBRE}_turnaround.png"), "MANTA ESTELAR — turnaround", notas)
    # Primeros planos para la revisión (no forman parte de la entrega).
    cerca = [("Cabeza 3/4", 35, 22), ("Ojo", 80, 8), ("Lomo y silla", 20, 50), ("Boca abajo", 10, -35),
             ("Cola y aguijón", 150, 20), ("Ala izq. (cicatrices)", 60, 70)]
    centros = [(0, 4.9, 0.0, 2.6), (-1.9, 4.95, 0.1, 0.9), (0, 1.7, 0.4, 2.9), (0, 5.6, -0.6, 1.6),
               (0, -10.6, 0.1, 2.1), (-4.8, 0.2, 0.2, 3.0)]
    rutas2 = []
    for (nom, az, el), (x, y, z, r) in zip(cerca, centros):
        rutas2 += T.renderizar_vistas(objs, tmp, [(nom, az, el)], tam=420 if args.rapido else 620,
                                      muestras=24 if args.rapido else 64, prefijo="c_", centro=(x, y, z), radio=r,
                                      margen=1.0)
    T.montar_turnaround(rutas2, ruta(salida, "_render_tmp", f"primeros_planos_r{args.ronda}.png"),
                        "MANTA ESTELAR — primeros planos", columnas=3)
    T.asignar_material(piezas["Ojos_Cornea"], atlas)
    for c_ in cubos:
        c_.hide_render = False


if __name__ == "__main__":
    main()
