"""
Casa de la familia (pueblo): la casa más grande del pueblo, dos plantas, una familia con dos niños (Mia y Leo).

Uso (Blender 4.2 como módulo de Python, sin pantalla):
    python pueblo/herramientas/casa_familia.py            # modelo + atlas + FBX + turnaround + json
    python pueblo/herramientas/casa_familia.py --rapido   # atlas de 1024 y renders pequeños (para probar)

Sale en pueblo/casa_familia/:
    casa_familia.fbx, casa_familia_{color,normal,roughness,metalness,emision}.png (atlas 2048²),
    casa_familia_turnaround.png (8 vistas), casa_familia_detalles.png (primeros planos + malla), casa_familia.json

Medidas en STUDS (1 unidad de Blender = 1 stud). En Blender la fachada mira a -Y y Z es arriba; al exportar se
aplica el giro de importación (180° en el eje vertical).

Lo que cuenta cada detalle está comentado donde se modela.
"""

import json
import math
import os
import random
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import kit_casa as K  # noqa: E402
import pinturas_casa_familia as P  # noqa: E402
from kit_casa import R, S, T, Pieza  # noqa: E402

RAPIDO = "--rapido" in sys.argv
RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "casa_familia"))
NOMBRE = "casa_familia"
TAM_ATLAS = 1024 if RAPIDO else 2048
TMP = tempfile.mkdtemp(prefix="casa_familia_")

# ----------------------------------------------------------------------------------------------------------------
# Medidas (studs). Todo lo ajustable está aquí.
# ----------------------------------------------------------------------------------------------------------------
X0, X1 = -5.0, 5.0  # paredes exteriores
Y0, Y1 = -3.75, 3.75
G = 0.25  # grosor de pared
Z_BASE = 0.5  # zócalo de piedra
Z_MOLD = (3.95, 4.2)  # moldura entre plantas
Z_ALERO = 7.0
SUBIDA = 1.75  # del alero a la cumbrera
TAN = SUBIDA / (Y1)
COS = math.cos(math.atan(TAN))
VUELO, VUELO_LAT = 0.45, 0.35
T_TEJ = 0.12  # grosor de la chapa del tejado
Z_SUELO = 0.12  # losa de la entrada

PUERTA = dict(x=(-2.15, -0.15), z=(Z_BASE, 3.6))
VENT_BAJA = dict(x=(0.9, 4.1), z=(1.35, 3.35))  # frontal grande
VENT_ALTA = dict(x=(-0.9, 1.5), z=(4.75, 6.35))  # dormitorio de los niños
VENT_LAT1 = dict(y=(-1.2, 1.2), z=(1.5, 3.3))  # pared derecha (x+), planta baja
VENT_LAT2 = dict(y=(-0.7, 0.7), z=(4.9, 6.1))  # pared izquierda (x-), planta alta
PIVOTE_PUERTA = Vector((-2.15, -3.80, Z_BASE))

NEON = "#3DF2FF"


def z_tejado_abajo(y):
    """Altura de la cara inferior de la chapa (los dos faldones)."""
    return Z_ALERO + (Y1 - abs(y)) * TAN


def z_tejado_arriba(y):
    return z_tejado_abajo(y) + T_TEJ / COS


# Matriz que lleva un perfil 2D (x, y) al plano (Y, Z) del mundo y la extrusión (z local) a X.
M_YZ = Matrix(((0, 0, 1, 0), (1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 0, 1)))


# ----------------------------------------------------------------------------------------------------------------
# Texturas pintadas a mano
# ----------------------------------------------------------------------------------------------------------------


def imagenes():
    I = {}
    def cargar(pil, nombre, color=True):
        I[nombre] = K.cargar_imagen(pil, nombre, TMP, color)

    pw, ph = PUERTA["x"][1] - PUERTA["x"][0] - 0.04, PUERTA["z"][1] - PUERTA["z"][0] - 0.04
    c, r, a = P.puerta(pw, ph, [(1.28, "Leo 4", (40, 90, 220)), (1.60, "Mia 6", (30, 150, 70)),
                                (1.86, "Leo 7", (215, 40, 40))], (pw - 0.28, 1.53), (pw - 0.28, 0.92))
    cargar(c, "puerta_c"); cargar(r, "puerta_r", False); cargar(a, "puerta_a", False)
    c, r, a = P.marco_pintado(VENT_BAJA["x"][1] - VENT_BAJA["x"][0] + 0.44, VENT_BAJA["z"][1] - VENT_BAJA["z"][0] + 0.44,
                              0.22, 1.0, 11)
    cargar(c, "marco1_c"); cargar(r, "marco1_r", False); cargar(a, "marco1_a", False)
    c, r, a = P.marco_pintado(VENT_LAT1["y"][1] - VENT_LAT1["y"][0] + 0.40, VENT_LAT1["z"][1] - VENT_LAT1["z"][0] + 0.40,
                              0.20, 0.55, 12)
    cargar(c, "marco2_c"); cargar(r, "marco2_r", False); cargar(a, "marco2_a", False)
    cargar(P.dibujo_familia(0.85, 0.64), "dibujo_c")
    c, r, a = P.placa_numero(0.6)
    cargar(c, "placa_c"); cargar(a, "placa_a", False)
    c, r, a = P.felpudo(1.5, 0.48)
    cargar(c, "felpudo_c"); cargar(a, "felpudo_a", False)
    c, r, a = P.suelo_entrada(-6.1, 5.6, -5.8, Y0, (0.3, -5.15, 0.5), [(-5.55, -4.35, 0.55)], [-3.0, 0.4, 3.9])
    cargar(c, "suelo_c"); cargar(r, "suelo_r", False); cargar(a, "suelo_a", False)
    c, a = P.loseta_panel()
    cargar(c, "panel_c"); cargar(a, "panel_a", False)
    cargar(P.celulas_solares(3.2, 2.0, 4, 6), "solar_c")
    return I


# ----------------------------------------------------------------------------------------------------------------
# Materiales (fuente del horneado)
# ----------------------------------------------------------------------------------------------------------------


def materiales(I):
    M = {}
    mat = K.material

    def panel(N):
        v = N.coord(0.5)
        tc = N.imagen(I["panel_c"], v)
        ta = N.imagen(I["panel_a"], v, False)
        br = N.n("ShaderNodeTexBrick", offset=0.0, squash=1.0)
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = 2.0
        br.inputs["Row Height"].default_value = 2.0
        br.inputs["Mortar Size"].default_value = 0.0
        br.inputs["Color1"].default_value = (*K.srgb("#E9ECEE"), 1)
        br.inputs["Color2"].default_value = (*K.srgb("#D9DEE2"), 1)
        br.inputs["Bias"].default_value = 0.0
        N.L(N.uv(), br.inputs["Vector"])
        col = N.mezcla(1.0, tc.outputs["Color"], br.outputs["Color"], "MULTIPLY")
        z = N.separar(N.objeto())[2]
        sucio = N.rango(z, Z_BASE, 1.8, 0.80, 1.0)
        col = N.mezcla(1.0, col, sucio, "MULTIPLY")
        N.set("Base Color", col)
        N.set("Roughness", N.rango(N.ruido(N.uv(), 1.5), 0.3, 0.7, 0.38, 0.6))
        N.bump(ta.outputs["Color"], 0.7, 0.03)
    M["panel"] = mat("pared_paneles", metal=0.25, nodos=panel)

    def interior(N):
        z = N.separar(N.objeto())[2]
        arriba = N.rango(z, 4.15, 4.25)
        col = N.mezcla(arriba, K.srgb("#F3E3C3"), K.srgb("#BFE3F0"))  # abajo crema, arriba azul (niños)
        # Estrellitas en la pared de arriba (papel pintado).
        vor = N.n("ShaderNodeTexVoronoi")
        vor.inputs["Scale"].default_value = 3.0
        N.L(N.objeto(), vor.inputs["Vector"])
        punto = N.mate("LESS_THAN", vor.outputs["Distance"], 0.08)
        col = N.mezcla(N.mate("MULTIPLY", punto, arriba), col, K.srgb("#FFF3A0"))
        N.set("Base Color", col)
    M["interior"] = mat("interior", rug=0.85, nodos=interior)

    def piedra(N):
        br = N.n("ShaderNodeTexBrick", offset=0.5)
        br.inputs["Scale"].default_value = 1.0
        br.inputs["Brick Width"].default_value = 0.75
        br.inputs["Row Height"].default_value = 0.25
        br.inputs["Mortar Size"].default_value = 0.025
        br.inputs["Mortar Smooth"].default_value = 0.3
        br.inputs["Color1"].default_value = (*K.srgb("#8E8A84"), 1)
        br.inputs["Color2"].default_value = (*K.srgb("#A8A39A"), 1)
        br.inputs["Mortar"].default_value = (*K.srgb("#4E4B47"), 1)
        br.inputs["Bias"].default_value = 0.0
        N.L(N.uv(), br.inputs["Vector"])
        r = N.ruido(N.uv(), 9.0, 6)
        col = N.mezcla(0.5, br.outputs["Color"], N.rango(r, 0.3, 0.7, 0.75, 1.1), "MULTIPLY")
        N.set("Base Color", col)
        alt = N.mate("SUBTRACT", N.mate("MULTIPLY", r, 0.4), br.outputs["Fac"])
        N.bump(alt, 0.8, 0.04)
    M["piedra"] = mat("piedra_zocalo", rug=0.9, nodos=piedra)

    def estructura(N):
        r = N.ruido(N.uv(), 6.0, 5)
        N.set("Base Color", N.mezcla(r, K.srgb("#43484F"), K.srgb("#565C64")))
        N.set("Roughness", N.rango(r, 0.3, 0.7, 0.35, 0.6))
        N.bump(N.ruido(N.uv(), 40.0, 3), 0.15, 0.01)
    M["estructura"] = mat("estructura", metal=0.65, nodos=estructura)

    def marco(N):
        r = N.ruido(N.coord((1.0, 6.0, 1.0)), 4.0, 4)
        N.set("Base Color", N.mezcla(r, K.srgb("#8F969E"), K.srgb("#A3A9B0")))
    def moldura(N):
        r = N.ruido(N.uv(), 5.0, 5)
        N.set("Base Color", N.mezcla(r, K.srgb("#23877C"), K.srgb("#2FA597")))
        N.bump(N.ruido(N.uv(), 30.0, 3), 0.2, 0.01)
    M["moldura"] = mat("moldura_pintada", rug=0.45, metal=0.3, nodos=moldura)
    M["marco"] = mat("marco_metal", rug=0.42, metal=0.7, nodos=marco)

    def decal(nombre, c, r=None, a=None, metal=0.0, rug=0.5, fuerza=0.5, dist=0.02):
        def f(N):
            N.set("Base Color", N.imagen(I[c], extension="EXTEND").outputs["Color"])
            if r:
                N.set("Roughness", N.imagen(I[r], color=False, extension="EXTEND").outputs["Color"])
            if a:
                N.bump(N.imagen(I[a], color=False, extension="EXTEND").outputs["Color"], fuerza, dist)
        return mat(nombre, rug=rug, metal=metal, nodos=f)

    M["puerta_frente"] = decal("puerta_frente", "puerta_c", "puerta_r", "puerta_a", fuerza=0.9, dist=0.03)

    def puerta_resto(N):
        r = N.ruido(N.coord((1.0, 6.0, 1.0)), 5.0, 4)
        N.set("Base Color", N.mezcla(r, K.srgb("#F7C531"), K.srgb("#EDB823")))
    M["puerta_resto"] = mat("puerta_resto", rug=0.45, nodos=puerta_resto)
    M["marco_azul1"] = decal("marco_azul_frente", "marco1_c", "marco1_r", "marco1_a", metal=0.4, fuerza=0.5)
    M["marco_azul2"] = decal("marco_azul_lateral", "marco2_c", "marco2_r", "marco2_a", metal=0.4, fuerza=0.5)
    M["dibujo"] = decal("dibujo", "dibujo_c", rug=0.9)
    M["placa"] = decal("placa_numero", "placa_c", None, "placa_a", metal=0.3, rug=0.35, fuerza=0.6)
    M["felpudo"] = decal("felpudo", "felpudo_c", None, "felpudo_a", rug=0.95, fuerza=1.0, dist=0.03)
    M["suelo"] = decal("suelo_entrada", "suelo_c", "suelo_r", "suelo_a", fuerza=0.6, dist=0.03)
    M["solar"] = decal("celulas_solares", "solar_c", rug=0.15, metal=0.2)

    def hormigon(N):
        r = N.ruido(N.uv(), 7.0, 5)
        N.set("Base Color", N.mezcla(r, K.srgb("#8B8984"), K.srgb("#A19F99")))
        N.bump(r, 0.4, 0.02)
    M["hormigon"] = mat("hormigon", rug=0.92, nodos=hormigon)

    def chapa(N):
        x = N.separar(N.uv())[0]
        ondas = N.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="X")
        ondas.inputs["Scale"].default_value = 2 * math.pi / (20 * 0.28)
        N.L(N.uv(), ondas.inputs["Vector"])
        junta = N.mate("LESS_THAN", N.mate("FRACT", N.mate("DIVIDE", x, 3.6)), 0.012)
        r = N.ruido(N.uv(), 2.0, 5)
        oxido = N.rango(N.ruido(N.uv(), 5.0, 6), 0.62, 0.72)
        col = N.mezcla(r, K.srgb("#7D858C"), K.srgb("#98A0A6"))
        col = N.mezcla(oxido, col, K.srgb("#8A5A3C"))
        col = N.mezcla(N.mate("MULTIPLY", junta, 0.6), col, K.srgb("#3A3E42"))
        N.set("Base Color", col)
        N.set("Metallic", N.rango(oxido, 0, 1, 0.75, 0.2))
        N.set("Roughness", N.rango(oxido, 0, 1, 0.42, 0.85))
        alt = N.mate("SUBTRACT", ondas.outputs["Fac"], N.mate("MULTIPLY", junta, 0.4))
        N.bump(alt, 0.9, 0.04)
    M["chapa"] = mat("chapa_tejado", nodos=chapa)

    def madera(N, claro="#9C7650", oscuro="#6B4C31"):
        ondas = N.n("ShaderNodeTexWave", wave_type="BANDS", bands_direction="Y")
        ondas.inputs["Scale"].default_value = 3.0
        ondas.inputs["Distortion"].default_value = 6.0
        ondas.inputs["Detail"].default_value = 3.0
        N.L(N.coord((1.0, 0.15, 1.0)), ondas.inputs["Vector"])
        r = N.ruido(N.uv(), 3.0, 4)
        col = N.mezcla(ondas.outputs["Fac"], K.srgb(claro), K.srgb(oscuro))
        col = N.mezcla(N.mate("MULTIPLY", r, 0.35), col, K.srgb("#8C8C86"))  # gris de intemperie
        N.set("Base Color", col)
        N.bump(ondas.outputs["Fac"], 0.35, 0.015)
    M["madera"] = mat("madera_jardinera", rug=0.85, nodos=madera)
    M["suelo_madera"] = mat("suelo_madera", rug=0.6, nodos=lambda N: madera(N, "#C49A6C", "#A37A50"))

    def tela(N, colores, periodo=0.3, eje=0):
        coord = N.separar(N.uv())[eje]
        rampa = N.n("ShaderNodeValToRGB")
        rampa.color_ramp.interpolation = "CONSTANT"
        els = rampa.color_ramp.elements
        n = len(colores)
        for i, c in enumerate(colores):
            e = els[i] if i < len(els) else els.new(i / n)
            e.position = i / n
            e.color = (*K.srgb(c), 1)
        N.L(N.mate("FRACT", N.mate("DIVIDE", coord, periodo * n)), rampa.inputs["Fac"])
        N.set("Base Color", rampa.outputs["Color"])
        N.bump(N.ruido(N.coord(1.0), 60.0, 2), 0.2, 0.005)
    M["cortina"] = mat("cortina", rug=0.9, nodos=lambda N: tela(N, ["#FF9F1C", "#FFD166", "#06D6A0", "#EF476F"], 0.18))
    M["toalla"] = mat("toalla", rug=0.95, nodos=lambda N: tela(N, ["#FFFFFF", "#2EC4B6", "#FFFFFF", "#FF9F1C"], 0.1, 1))
    M["manta"] = mat("manta", rug=0.95, nodos=lambda N: tela(N, ["#8E7DBE", "#F7B801", "#3A86FF", "#FF006E"], 0.2))

    def buzon(N):
        # Franjas de colores pintadas por los niños: torcidas, con huecos donde se ve el gris.
        y = N.separar(N.objeto())[1]
        z = N.separar(N.objeto())[2]
        r = N.ruido(N.objeto(), 3.0, 3)
        coord = N.mate("ADD", N.mate("MULTIPLY", y, 4.0), N.mate("ADD", N.mate("MULTIPLY", z, 1.2),
                                                                 N.mate("MULTIPLY", r, 1.6)))
        rampa = N.n("ShaderNodeValToRGB")
        rampa.color_ramp.interpolation = "CONSTANT"
        cols = ["#E63946", "#9AA0A6", "#FFB703", "#2A9D8F", "#9AA0A6", "#3A86FF", "#FF70A6", "#9AA0A6"]
        els = rampa.color_ramp.elements
        for i, c in enumerate(cols):
            e = els[i] if i < len(els) else els.new(i / len(cols))
            e.position = i / len(cols)
            e.color = (*K.srgb(c), 1)
        N.L(N.mate("FRACT", N.mate("DIVIDE", coord, 4.0)), rampa.inputs["Fac"])
        N.set("Base Color", rampa.outputs["Color"])
        N.bump(N.ruido(N.objeto(), 25.0, 3), 0.25, 0.01)
    M["buzon"] = mat("buzon_pintado", rug=0.5, metal=0.3, nodos=buzon)

    def balon(N):
        g = N.n("ShaderNodeTexGradient", gradient_type="RADIAL")
        mp = N.n("ShaderNodeMapping")
        mp.inputs["Location"].default_value = (3.2, 4.2, -0.4)  # -centro del balón
        N.L(N.objeto(), mp.inputs["Vector"])
        N.L(mp.outputs["Vector"], g.inputs["Vector"])
        rampa = N.n("ShaderNodeValToRGB")
        rampa.color_ramp.interpolation = "CONSTANT"
        cols = ["#E63946", "#FFFFFF", "#FFB703", "#FFFFFF", "#3A86FF", "#FFFFFF"]
        els = rampa.color_ramp.elements
        for i, c in enumerate(cols):
            e = els[i] if i < len(els) else els.new(i / len(cols))
            e.position = i / len(cols)
            e.color = (*K.srgb(c), 1)
        N.L(g.outputs["Fac"], rampa.inputs["Fac"])
        N.set("Base Color", rampa.outputs["Color"])
    M["balon"] = mat("balon_playa", rug=0.35, nodos=balon)

    def terracota(N):
        r = N.ruido(N.uv(), 12.0, 4)
        N.set("Base Color", N.mezcla(r, K.srgb("#B5603A"), K.srgb("#C9774D")))
        N.bump(r, 0.3, 0.01)
    M["terracota"] = mat("terracota", rug=0.88, nodos=terracota)

    def tierra(N):
        r = N.ruido(N.coord(1.0), 25.0, 6)
        N.set("Base Color", N.mezcla(r, K.srgb("#3B2A1E"), K.srgb("#5A4230")))
        N.bump(r, 0.9, 0.03)
    M["tierra"] = mat("tierra", rug=1.0, nodos=tierra)

    def hoja(N, a="#3E8E41", b="#6BBF59"):
        r = N.ruido(N.objeto(), 6.0, 3)
        N.set("Base Color", N.mezcla(r, K.srgb(a), K.srgb(b)))
    M["hoja"] = mat("hoja", rug=0.55, nodos=hoja)
    M["lechuga"] = mat("lechuga", rug=0.5, nodos=lambda N: hoja(N, "#7CC254", "#B5E07A"))

    sencillos = {
        "metal_brillo": ("#C9CCD0", 0.22, 1.0), "metal_galv": ("#A8AFB5", 0.4, 0.85),
        "cristal": ("#CFE6EE", 0.04, 0.0), "lente": ("#0E1418", 0.08, 0.3),
        "maceta_roja": ("#D64933", 0.45, 0.0), "maceta_verde": ("#43AA8B", 0.45, 0.0),
        "flor_roja": ("#E63946", 0.6, 0.0), "flor_amarilla": ("#FFD166", 0.6, 0.0),
        "tomate": ("#E8361C", 0.3, 0.0), "palo": ("#8B6A45", 0.85, 0.0), "papel": ("#F4F1E8", 0.9, 0.0),
        "estrella_amarilla": ("#FFD23F", 0.35, 0.0), "estrella_rosa": ("#FF70A6", 0.35, 0.0),
        "estrella_cian": ("#5CE1E6", 0.35, 0.0), "estrella_verde": ("#70E000", 0.35, 0.0),
        "lampara": ("#2E3338", 0.4, 0.8), "medidor": ("#B9BDB8", 0.55, 0.1),
        "cable": ("#141414", 0.55, 0.0), "pvc": ("#9EA4A8", 0.5, 0.0), "cinta": ("#8E9296", 0.7, 0.15),
        "camiseta": ("#FF6B35", 0.9, 0.0), "pantalon": ("#3A6EA5", 0.9, 0.0), "calcetin": ("#FFD23F", 0.9, 0.0),
        "pinza_rosa": ("#FF5D8F", 0.35, 0.0), "pinza_verde": ("#38B000", 0.35, 0.0),
        "pinza_azul": ("#4361EE", 0.35, 0.0), "pinza_amarilla": ("#FFC300", 0.35, 0.0),
        "poste": ("#2A9D8F", 0.5, 0.3), "bici": ("#FF4F79", 0.3, 0.2), "bici_blanco": ("#F2F2F2", 0.4, 0.0),
        "goma": ("#1C1C1E", 0.75, 0.0), "sillin": ("#7B2CBF", 0.5, 0.0), "puno": ("#9D4EDD", 0.6, 0.0),
        "caja_juguetes": ("#3A86FF", 0.4, 0.0), "tapa_juguetes": ("#FFBE0B", 0.4, 0.0),
        "espada": ("#9B5DE5", 0.7, 0.0), "guarda": ("#FEE440", 0.5, 0.0), "antena": ("#E9E9E6", 0.45, 0.05),
        "aluminio": ("#B8BEC4", 0.35, 0.9), "mueble": ("#E8DCC8", 0.6, 0.0), "colchon": ("#F4F4F4", 0.9, 0.0),
        "almohada": ("#FFE5EC", 0.9, 0.0), "persiana": ("#7EC8E3", 0.85, 0.0), "techo": ("#F5F3EE", 0.9, 0.0),
    }
    for k, (c, r, m) in sencillos.items():
        M[k] = mat(k, c, r, m)
    M["neon"] = mat("neon", NEON, 0.3, 0.0, NEON, 4.0)
    M["luz_calida"] = mat("luz_calida", "#FFE2B0", 0.4, 0.0, "#FFD9A0", 6.0)
    M["estrella_luz"] = mat("estrella_luz", "#FFE88A", 0.4, 0.0, "#FFE070", 1.5)
    return M


# ----------------------------------------------------------------------------------------------------------------
# Utilidades de modelado
# ----------------------------------------------------------------------------------------------------------------


def caja(p, x, y, z, mat, bisel=0.0, M=None):
    """Caja por rangos (x0,x1), (y0,y1), (z0,z1); M opcional se aplica después (relativa al mundo)."""
    c = ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2)
    tam = (x[1] - x[0], y[1] - y[0], z[1] - z[0])
    geo = K.g_caja_bisel(*tam, bisel) if bisel > 0 else K.g_caja(*tam)
    return p.add(geo, mat, (M or Matrix.Identity(4)) @ T(*c))


def mat_si(p, caras, cond, mat):
    for f in caras:
        f.normal_update()
        if cond(f.calc_center_median(), f):
            f.material_index = p.idx(mat)


# Marcos de las paredes: local (u, prof, v) -> mundo. prof > 0 entra en la pared, < 0 sale.
PAREDES = {
    "frente": T(X0, Y0, 0) @ Matrix.Identity(4),
    "atras": T(X1, Y1, 0) @ R("Z", 180),
    "izq": T(X0, Y1 - G, 0) @ R("Z", -90),
    "der": T(X1, Y0 + G, 0) @ R("Z", 90),
}


def eje_u(pared):
    return tuple(PAREDES[pared].to_3x3() @ Vector((1, 0, 0)))


def ventana(nombre, pared, u0, u1, v0, v1, M, marco_mat=None, densidad_marco=1.0, parteluz=False, alfeizar=False,
            casing=0.22, densidad=1.0):
    """
    Ventana completa en el hueco (u0..u1, v0..v1) de una pared: marco exterior saliente (con la calcomanía azul si
    `marco_mat`), marco interior en el derrame, parteluz opcional, cristal con grosor y alféizar opcional.
    Devuelve la matriz de la pared y la profundidad del cristal.
    """
    W = PAREDES[pared]
    w, h = u1 - u0, v1 - v0
    planos = {}
    if marco_mat is not None:
        o = W @ Vector((u0 - casing, 0, v0 - casing))
        planos[marco_mat.name] = (eje_u(pared), (0, 0, 1), tuple(o), w + 2 * casing, h + 2 * casing)
    pm = Pieza(f"{nombre}_marco", densidad=densidad_marco, planos=planos)
    sale = 0.08
    geo = K.g_pared(w + 2 * casing, h + 2 * casing, sale, [(casing, casing, casing + w, casing + h)])
    exterior = marco_mat or M["marco"]

    def mat_cara(i, tag):
        return exterior if tag == "ext" else M["marco"]
    pm.add(geo, None, W @ T(u0 - casing, -sale, v0 - casing), mat_cara)
    # Marco interior (hoja fija) dentro del derrame.
    s = 0.09
    pm.add(K.g_pared(w, h, 0.10, [(s, s, w - s, h - s)]), M["marco"], W @ T(u0, 0.05, v0))
    if parteluz:
        um = u0 + w / 2
        caja(pm, (um - 0.05, um + 0.05), (0.05, 0.15), (v0 + s, v1 - s), M["marco"], M=W)
    # Cristal(es).
    pc = Pieza(f"{nombre}_cristal", grupo="cristal", densidad=0.15)
    if parteluz:
        um = u0 + w / 2
        tramos = [(u0 + s - 0.01, um - 0.04), (um + 0.04, u1 - s + 0.01)]
    else:
        tramos = [(u0 + s - 0.01, u1 - s + 0.01)]
    for a, b in tramos:
        caja(pc, (a, b), (0.085, 0.125), (v0 + s - 0.01, v1 - s + 0.01), M["cristal"], M=W)
    if alfeizar:
        pa = Pieza(f"{nombre}_alfeizar", densidad=densidad)
        caja(pa, (u0 - casing - 0.08, u1 + casing + 0.08), (-0.42, 0.06), (v0 - casing - 0.07, v0 - casing + 0.02),
             M["marco"], bisel=0.025, M=W)
        # Goterón bajo el alféizar.
        caja(pa, (u0 - casing - 0.08, u1 + casing + 0.08), (-0.42, -0.38), (v0 - casing - 0.12, v0 - casing - 0.07),
             M["marco"], M=W)
    return W


def hoja(largo, ancho, grosor=0.018):
    """Hoja (polígono puntiagudo) en XY, a lo largo de +X desde el origen, con grosor."""
    pol = [(0, 0), (largo * 0.4, ancho * 0.5), (largo, 0), (largo * 0.4, -ancho * 0.5)]
    return K.g_prisma(pol, -grosor / 2, grosor / 2)


def maceta(radio_abajo, radio_arriba, alto, grosor=0.025, borde=0.03, lados=12):
    """Maceta con grosor real: pared, borde engrosado y fondo (perfil de revolución cerrado)."""
    rb, ra, h, g = radio_abajo, radio_arriba, alto, grosor
    perfil = [(0, 0), (rb, 0), (ra, h - borde), (ra + 0.02, h - borde), (ra + 0.02, h), (ra - g, h),
              (ra - g, h - borde), (rb - g, g), (0, g)]
    return K.g_torno(perfil, lados)


def esfera(r, lados=10, anillos=6, achatar=1.0):
    perfil = [(0, -r * achatar)]
    for i in range(1, anillos):
        a = -math.pi / 2 + math.pi * i / anillos
        perfil.append((r * math.cos(a), r * math.sin(a) * achatar))
    perfil.append((0, r * achatar))
    return K.g_torno(perfil, lados)


def trozo_maceta(r_ext, grosor, a0, a1, z0, z1, pasos=3, mordida=0.0, rng=None):
    """Trozo de maceta rota: casquete curvo con grosor, bordes irregulares (`mordida`)."""
    rng = rng or random.Random(3)
    v, f = [], []
    for i in range(pasos + 1):
        a = a0 + (a1 - a0) * i / pasos
        zb = z0 + rng.uniform(0, mordida)
        zt = z1 - rng.uniform(0, mordida)
        for (r, z) in ((r_ext, zb), (r_ext, zt), (r_ext - grosor, zt), (r_ext - grosor, zb)):
            v.append((r * math.cos(a), r * math.sin(a), z))
    for i in range(pasos):
        for k in range(4):
            k2 = (k + 1) % 4
            f.append((i * 4 + k, i * 4 + k2, (i + 1) * 4 + k2, (i + 1) * 4 + k))
    f.append((3, 2, 1, 0))
    n = pasos * 4
    f.append((n, n + 1, n + 2, n + 3))
    return v, f


# ----------------------------------------------------------------------------------------------------------------
# Modelo
# ----------------------------------------------------------------------------------------------------------------


def estructura(M):
    # Paredes con huecos. Las caras exteriores son paneles, las interiores pintura de interior, los derrames metal.
    alto = Z_ALERO - Z_BASE
    huecos = {
        "frente": [(PUERTA["x"][0] - X0, 0.0, PUERTA["x"][1] - X0, PUERTA["z"][1] - Z_BASE),
                   (VENT_BAJA["x"][0] - X0, VENT_BAJA["z"][0] - Z_BASE, VENT_BAJA["x"][1] - X0, VENT_BAJA["z"][1] - Z_BASE),
                   (VENT_ALTA["x"][0] - X0, VENT_ALTA["z"][0] - Z_BASE, VENT_ALTA["x"][1] - X0, VENT_ALTA["z"][1] - Z_BASE)],
        "atras": [],
        "izq": [(Y1 - G - VENT_LAT2["y"][1], VENT_LAT2["z"][0] - Z_BASE, Y1 - G - VENT_LAT2["y"][0],
                 VENT_LAT2["z"][1] - Z_BASE)],
        "der": [(VENT_LAT1["y"][0] - (Y0 + G), VENT_LAT1["z"][0] - Z_BASE, VENT_LAT1["y"][1] - (Y0 + G),
                 VENT_LAT1["z"][1] - Z_BASE)],
    }
    largos = {"frente": X1 - X0, "atras": X1 - X0, "izq": (Y1 - Y0) - 2 * G, "der": (Y1 - Y0) - 2 * G}
    p = Pieza("paredes")
    tags = {"ext": M["panel"], "int": M["interior"], "borde": M["panel"], "hueco": M["marco"]}
    for nombre, W in PAREDES.items():
        geo = K.g_pared(largos[nombre], alto, G, huecos[nombre], cortes_v=[Z_MOLD[0] - Z_BASE, Z_MOLD[1] - Z_BASE])
        p.add(geo, None, W @ T(0, 0, Z_BASE), lambda i, t: tags[t])
    # Hastiales (triángulos de los laterales bajo el tejado).
    tri = [(Y0, Z_ALERO), (Y1, Z_ALERO), (0.0, Z_ALERO + SUBIDA)]
    p.add(K.g_prisma(tri, X0, X0 + G), M["panel"], M_YZ)
    p.add(K.g_prisma(tri, X1 - G, X1), M["panel"], M_YZ)

    # Zócalo de piedra (sobresale un poco) y suelos/techos interiores.
    z = Pieza("zocalo")
    caras = caja(z, (X0 - 0.08, X1 + 0.08), (Y0 - 0.08, Y1 + 0.08), (0, Z_BASE), M["piedra"], bisel=0.04)
    z.densidad_caras([f for f in caras if f.calc_center_median().z > Z_BASE - 0.01], 0.02)  # tapada por la casa
    pi = Pieza("interior", densidad=0.2)
    caja(pi, (X0 + G, X1 - G), (Y0 + G, Y1 - G), (Z_BASE, Z_BASE + 0.04), M["suelo_madera"])
    caras = caja(pi, (X0 + G, X1 - G), (Y0 + G, Y1 - G), (Z_MOLD[0], Z_MOLD[1]), M["techo"])
    mat_si(pi, caras, lambda c, f: c.z > Z_MOLD[1] - 0.01, M["suelo_madera"])
    caja(pi, (X0 + G, X1 - G), (Y0 + G, Y1 - G), (Z_ALERO - 0.15, Z_ALERO - 0.02), M["techo"])

    # Esquinas metálicas y moldura entre plantas.
    e = Pieza("esquinas", suave=None)
    for sx in (X0, X1):
        for sy in (Y0, Y1):
            caja(e, (sx - 0.16, sx + 0.16), (sy - 0.16, sy + 0.16), (Z_BASE, Z_ALERO), M["estructura"], bisel=0.03)
    mo = Pieza("moldura")
    d = 0.11
    caja(mo, (X0 - d, X1 + d), (Y0 - d, Y0), Z_MOLD, M["moldura"], bisel=0.025)
    caja(mo, (X0 - d, X1 + d), (Y1, Y1 + d), Z_MOLD, M["moldura"], bisel=0.025)
    caja(mo, (X0 - d, X0), (Y0, Y1), Z_MOLD, M["moldura"], bisel=0.025)
    caja(mo, (X1, X1 + d), (Y0, Y1), Z_MOLD, M["moldura"], bisel=0.025)
    # Remate superior de las paredes (bajo el alero).
    caja(mo, (X0 - 0.06, X1 + 0.06), (Y0 - 0.06, Y0), (Z_ALERO - 0.2, Z_ALERO), M["moldura"])
    caja(mo, (X0 - 0.06, X1 + 0.06), (Y1, Y1 + 0.06), (Z_ALERO - 0.2, Z_ALERO), M["moldura"])

    # Reparación improvisada: chapa galvanizada remachada torcida en la pared delantera (un golpe con la bici).
    rp = Pieza("parche")
    Mp = T(-4.25, Y0 - 0.012, 1.3) @ R("Y", 4)
    caja(rp, (-0.33, 0.33), (-0.012, 0.012), (-0.27, 0.27), M["metal_galv"], M=Mp)
    for (u, v) in ((-0.27, -0.21), (0, -0.22), (0.27, -0.21), (-0.27, 0.21), (0.01, 0.22), (0.27, 0.21)):
        rp.add(K.g_cilindro(0.025, 0.02, 6), M["metal_galv"], Mp @ T(u, -0.012, v) @ R("X", 90))


def tejado(M):
    p = Pieza("tejado", densidad=0.8)
    y_al = Y1 + VUELO
    za, zb = z_tejado_abajo(y_al), z_tejado_arriba(y_al)
    cumbre_b, cumbre_a = Z_ALERO + SUBIDA, Z_ALERO + SUBIDA + T_TEJ / COS
    frente = [(-y_al, za), (0.0, cumbre_b), (0.0, cumbre_a), (-y_al, zb)]
    atras = [(y_al, za), (y_al, zb), (0.0, cumbre_a), (0.0, cumbre_b)]
    for pol in (frente, atras):
        p.add(K.g_prisma(pol, X0 - VUELO_LAT, X1 + VUELO_LAT), M["chapa"], M_YZ)
    # Caballete (cumbrera) con grosor.
    a = 0.34
    cab = [(-a, z_tejado_arriba(-a)), (0.0, cumbre_a + 0.03), (a, z_tejado_arriba(a)), (a, z_tejado_arriba(a) + 0.04),
           (0.0, cumbre_a + 0.075), (-a, z_tejado_arriba(-a) + 0.04)]
    p.add(K.g_prisma(cab, X0 - VUELO_LAT - 0.03, X1 + VUELO_LAT + 0.03), M["metal_galv"], M_YZ)

    # Tablas de remate: en los hastiales siguiendo la pendiente y bajo los aleros.
    f = Pieza("remates", densidad=0.8)
    largo = math.hypot(y_al, za - cumbre_b)
    ang = math.degrees(math.atan(TAN))
    for sx in (X0 - VUELO_LAT - 0.02, X1 + VUELO_LAT + 0.02):
        for lado in (-1, 1):
            Mr = T(sx, lado * y_al / 2, (za + cumbre_b) / 2 - 0.06) @ R("X", -lado * ang)
            caja(f, (-0.04, 0.04), (-largo / 2, largo / 2), (-0.14, 0.12), M["estructura"], bisel=0.015, M=Mr)
    for sy in (-y_al - 0.03, y_al + 0.03):
        caja(f, (X0 - VUELO_LAT, X1 + VUELO_LAT), (sy - 0.03, sy + 0.03), (za - 0.16, za + 0.06), M["estructura"])
    # Canalones (perfil en U con grosor) a lo largo de los aleros.
    u = [(-0.13, 0.0), (-0.11, -0.10), (-0.05, -0.15), (0.05, -0.15), (0.11, -0.10), (0.13, 0.0), (0.105, 0.0),
         (0.087, -0.085), (0.04, -0.125), (-0.04, -0.125), (-0.087, -0.085), (-0.105, 0.0)]
    c = Pieza("canalones", densidad=0.8, suave=50)
    for lado in (-1, 1):
        yc = lado * (y_al + 0.17)
        pol = [(yc + px * lado, za - 0.07 + pz) for px, pz in u]
        c.add(K.g_prisma(pol, X0 - VUELO_LAT + 0.05, X1 + VUELO_LAT - 0.05), M["metal_galv"], M_YZ)
        # Soportes.
        for x in (-4.6, -1.5, 1.5, 4.6):
            caja(c, (x - 0.03, x + 0.03), (min(lado * y_al, yc + lado * 0.14), max(lado * y_al, yc + lado * 0.14)),
                 (za - 0.24, za - 0.20), M["metal_galv"])
    return y_al, za


def marco_tejado(x, s, elev=0.0, lado=-1):
    """Marco local sobre el faldón: x a lo largo del alero, s subiendo por la pendiente desde el alero, n normal."""
    y_al = Y1 + VUELO
    ang = math.atan(TAN)
    d = Vector((0, -lado * math.cos(ang), math.sin(ang)))
    n = Vector((0, lado * math.sin(ang), math.cos(ang)))
    o = Vector((x, lado * y_al, z_tejado_arriba(y_al))) + d * s + n * elev
    m = Matrix((Vector((1, 0, 0)), d, n)).transposed().to_4x4()
    m.translation = o
    return m


def tejado_detalles(M):
    # Panel solar sobre patas en el faldón delantero, a la derecha.
    p = Pieza("panel_solar")
    Ms = marco_tejado(2.65, 1.55, 0.14)
    caras = caja(p, (-1.6, 1.6), (-1.0, 1.0), (0, 0.06), M["aluminio"], bisel=0.02, M=Ms)
    o = Ms @ Vector((-1.6, -1.0, 0))
    mat_si(p, caras, lambda c, f: f.normal.dot(Ms.to_3x3() @ Vector((0, 0, 1))) > 0.9 and
           (Ms.inverted() @ c).z > 0.05, M["solar"])
    p.planos[M["solar"].name] = ((1, 0, 0), tuple(Ms.to_3x3() @ Vector((0, 1, 0))), tuple(o), 3.2, 2.0)
    for (u, v) in ((-1.4, -0.8), (1.4, -0.8), (-1.4, 0.8), (1.4, 0.8)):
        caja(p, (u - 0.05, u + 0.05), (v - 0.05, v + 0.05), (-0.15, 0.0), M["aluminio"], M=Ms)
    # Lucernario (luz para la escalera): brocal, marco y cristal inclinado.
    l = Pieza("lucernario")
    Ml = marco_tejado(-2.1, 2.9, 0.0)
    l.add(K.g_pared(1.1, 0.9, 0.18, [(0.1, 0.1, 1.0, 0.8)]), M["estructura"], Ml @ T(-0.55, -0.45, 0.18) @ R("X", 90))
    caja(l, (-0.6, 0.6), (-0.5, 0.5), (0.18, 0.24), M["marco"], M=Ml)
    lc = Pieza("lucernario_cristal", grupo="cristal", densidad=0.15)
    caja(lc, (-0.45, 0.45), (-0.35, 0.35), (0.20, 0.25), M["cristal"], M=Ml)
    # Antena parabólica pequeña (ven las noticias): pie, mástil, plato con grosor, brazo y LNB.
    a = Pieza("antena", suave=40)
    Ma = marco_tejado(-4.15, 3.4, 0.0)
    caja(a, (-0.15, 0.15), (-0.15, 0.15), (0, 0.04), M["metal_galv"], M=Ma)
    base = Ma @ Vector((0, 0, 0.04))
    cima = base + Vector((0, 0, 0.55))
    a.add(K.g_cilindro(0.035, 0.55, 8), M["metal_galv"], T(*base))
    eje = Vector((0.15, -0.7, 0.68)).normalized()
    Mp = K.mirar(cima + eje * 0.05, cima + eje)
    r = 0.36
    perfil = [(0, 0)]
    for i in range(1, 5):
        rr = r * i / 4
        perfil.append((rr, rr * rr * 0.9))
    perfil += [(r - 0.02, r * r * 0.9 + 0.02), (r * 0.5, 0.25 * r * r * 0.9 + 0.02), (0, 0.025)]
    a.add(K.g_torno(perfil, 16), M["antena"], Mp)
    a.add(K.g_tubo([cima, cima + eje * 0.05], 0.05, 8), M["metal_galv"])
    foco = cima + eje * 0.42
    a.add(K.g_tubo([Mp @ Vector((0, -r * 0.9, r * r * 0.9)), foco], 0.015, 5), M["metal_galv"])
    a.add(K.g_cilindro(0.035, 0.12, 8), M["antena"], K.mirar(foco, foco - eje))
    # Chimenea de ventilación en el faldón trasero.
    v = Pieza("ventilacion", suave=40)
    Mv = marco_tejado(3.0, 2.4, 0.0, lado=1)
    o = Mv @ Vector((0, 0, -0.1))
    v.add(K.g_cilindro(0.09, 0.62, 10), M["metal_galv"], T(*o))
    v.add(K.g_cilindro(0.17, 0.05, 10), M["metal_galv"], T(*(o + Vector((0, 0, 0.1)))))
    v.add(K.g_torno([(0, 0), (0.18, 0.0), (0.06, 0.12), (0, 0.12)], 10), M["metal_galv"], T(*(o + Vector((0, 0, 0.68)))))
    for k in range(3):
        aa = 2 * math.pi * k / 3
        p0 = o + Vector((math.cos(aa) * 0.08, math.sin(aa) * 0.08, 0.6))
        v.add(K.g_tubo([p0, p0 + Vector((math.cos(aa) * 0.06, math.sin(aa) * 0.06, 0.1))], 0.012, 4), M["metal_galv"])


def puerta(M):
    """Hoja de la puerta (pieza aparte para animarla, pivote en las bisagras) y lo que va fijo en la pared."""
    x0, x1 = PUERTA["x"][0] + 0.02, PUERTA["x"][1] - 0.02
    z0, z1 = PUERTA["z"][0] + 0.02, PUERTA["z"][1] - 0.02
    y0, y1 = Y0 + 0.02, Y0 + 0.17
    pw, ph = x1 - x0, z1 - z0
    p = Pieza("puerta", grupo="puerta", densidad=4.0, suave=35,
              planos={M["puerta_frente"].name: ((1, 0, 0), (0, 0, 1), (x0, y0, z0), pw, ph)})
    caras = caja(p, (x0, x1), (y0, y1), (z0, z1), M["puerta_resto"], bisel=0.025)
    mat_si(p, caras, lambda c, f: c.y < y0 + 0.001, M["puerta_frente"])

    # Manijas: la normal de los mayores y una más baja para los niños (por fuera y por dentro).
    xm = x0 + pw - 0.28
    for z_m, largo in ((z0 + 1.53, 0.30), (z0 + 0.92, 0.22)):
        for lado, yy in ((-1, y0), (1, y1)):
            esc = T(xm, yy, z_m) @ R("X", lado * 90)
            # Escudo con grosor
            p.add(K.g_cilindro(0.075, 0.025, 12), M["metal_brillo"], esc @ R("X", 180) if lado < 0 else esc)
            base = Vector((xm, yy + lado * 0.025, z_m))
            codo = base + Vector((0, lado * 0.10, 0))
            punta = codo + Vector((-largo, lado * 0.02, -0.02))
            p.add(K.g_tubo([base, codo, codo + Vector((-0.04, lado * 0.01, 0)), punta], 0.024, 8), M["metal_brillo"])
    # Cerradura (bombín) sobre la manija grande, con la ranura de la llave.
    for lado, yy in ((-1, y0), (1, y1)):
        zc = z0 + 1.82
        p.add(K.g_cilindro(0.045, 0.03, 10), M["metal_brillo"], T(xm, yy, zc) @ R("X", lado * 90))
        caja(p, (xm - 0.008, xm + 0.008), (yy + lado * 0.03 - 0.004, yy + lado * 0.03 + 0.004), (zc - 0.025, zc + 0.02),
             M["lente"])
    # Mirilla (ojo de pez): anillo cromado y lente de cristal oscuro abombada.
    zm = z0 + 2.30
    xc = (x0 + x1) / 2
    p.add(K.g_cilindro(0.045, 0.025, 12), M["metal_brillo"], T(xc, y0, zm) @ R("X", 90))
    p.add(K.g_torno([(0, 0), (0.028, 0), (0.022, 0.012), (0, 0.018)], 10), M["lente"], T(xc, y0 - 0.025, zm) @ R("X", 90))
    # Bisagras: pala en la hoja y nudillos (los de arriba y abajo van con la hoja, el del medio con el marco).
    pv = PIVOTE_PUERTA
    fija = Pieza("bisagras_fijas", densidad=1.5, suave=35)
    for zb in (z0 + 0.45, z0 + 2.55):
        caja(p, (x0, x0 + 0.16), (y0 - 0.02, y0), (zb - 0.17, zb + 0.17), M["metal_brillo"], bisel=0.006)
        for (a, b) in ((zb - 0.18, zb - 0.06), (zb + 0.06, zb + 0.18)):
            p.add(K.g_cilindro(0.045, b - a, 8), M["metal_brillo"], T(pv.x, pv.y, a))
        fija.add(K.g_cilindro(0.045, 0.12, 8), M["metal_brillo"], T(pv.x, pv.y, zb - 0.06))
        caja(fija, (pv.x - 0.17, pv.x - 0.03), (Y0 - 0.09, Y0 - 0.07), (zb - 0.06, zb + 0.06), M["metal_brillo"])
        fija.add(K.g_torno([(0, 0), (0.05, 0), (0.035, 0.03), (0, 0.03)], 8), M["metal_brillo"], T(pv.x, pv.y, zb + 0.18))
        fija.add(K.g_torno([(0, 0.0), (0.035, -0.03), (0.05, 0.0), (0, 0.0001)], 8), M["metal_brillo"],
                 T(pv.x, pv.y, zb - 0.18) @ R("X", 180))

    # Fijo en la pared: jambas/dintel salientes, umbral metálico.
    m = Pieza("marco_puerta")
    c = 0.17
    W = PAREDES["frente"]
    u0, u1 = PUERTA["x"][0] - X0, PUERTA["x"][1] - X0
    alto = PUERTA["z"][1] - Z_BASE
    m.add(K.g_pared(u1 - u0 + 2 * c, alto + c, 0.07, [(c, 0, c + u1 - u0, alto)]), M["estructura"],
          W @ T(u0 - c, -0.07, Z_BASE))
    caja(m, PUERTA["x"], (Y0 - 0.04, Y0 + G), (Z_BASE, Z_BASE + 0.025), M["metal_galv"])


def entrada(M):
    """Losa de la entrada (con la rayuela), escalón, felpudo, lámpara, número, buzón, caja de juguetes."""
    # Losa de hormigón con la rayuela de tiza: arriba la calcomanía, los cantos de hormigón.
    s = Pieza("losa", densidad=1.4, planos={M["suelo"].name: ((1, 0, 0), (0, 1, 0), (-6.1, -5.8, 0), 11.7, Y0 + 5.8)})
    caras = caja(s, (-6.1, 5.6), (-5.8, Y0), (0, Z_SUELO), M["hormigon"], bisel=0.03)
    mat_si(s, caras, lambda c, f: f.normal.z > 0.99, M["suelo"])
    # Escalón de entrada.
    e = Pieza("escalon")
    caja(e, (PUERTA["x"][0] - 0.25, PUERTA["x"][1] + 0.25), (-4.45, Y0 - 0.08), (Z_SUELO, 0.32), M["hormigon"], bisel=0.03)
    # Felpudo de colores («HOLA») sobre el escalón.
    f = Pieza("felpudo", densidad=2.5, planos={M["felpudo"].name: ((1, 0, 0), (0, 1, 0), (-1.9, -4.36, 0), 1.5, 0.48)})
    caras = caja(f, (-1.9, -0.4), (-4.36, -3.88), (0.32, 0.36), M["goma"], bisel=0.012)
    mat_si(f, caras, lambda c, fc: fc.normal.z > 0.99, M["felpudo"])

    # Lámpara sobre la puerta: placa, brazo curvo, tulipa con grosor y bombilla de neón cian.
    l = Pieza("lampara", suave=40)
    xl = (PUERTA["x"][0] + PUERTA["x"][1]) / 2
    zl = 3.84
    caja(l, (xl - 0.09, xl + 0.09), (Y0 - 0.03, Y0), (zl - 0.08, zl + 0.08), M["lampara"], bisel=0.01)
    l.add(K.g_tubo([(xl, Y0 - 0.03, zl), (xl, Y0 - 0.22, zl + 0.04), (xl, Y0 - 0.34, zl - 0.02),
                    (xl, Y0 - 0.36, zl - 0.08)], 0.022, 6), M["lampara"])
    tulipa = [(0, 0.10), (0.04, 0.10), (0.16, -0.02), (0.165, -0.04), (0.14, -0.04), (0.035, 0.07), (0, 0.07)]
    l.add(K.g_torno(tulipa, 12), M["lampara"], T(xl, Y0 - 0.36, zl - 0.18))
    n = Pieza("bombilla", grupo="neon", densidad=0.3, suave=60)
    n.add(esfera(0.065, 10, 5), M["neon"], T(xl, Y0 - 0.36, zl - 0.17))

    # Placa del «3» con pegatinas de estrellas, atornillada.
    pl = Pieza("placa", densidad=5.0,
               planos={M["placa"].name: ((1, 0, 0), (0, 0, 1), (-3.27, Y0 - 0.04, 2.57), 0.6, 0.6)})
    caras = caja(pl, (-3.27, -2.67), (Y0 - 0.04, Y0), (2.57, 3.17), M["metal_brillo"], bisel=0.012)
    mat_si(pl, caras, lambda c, fc: c.y < Y0 - 0.039, M["placa"])
    for (x, z) in ((-3.2, 2.64), (-2.74, 2.64), (-3.2, 3.10), (-2.74, 3.10)):
        pl.add(K.g_cilindro(0.018, 0.012, 6), M["metal_brillo"], T(x, Y0 - 0.04, z) @ R("X", 90))

    # Buzón en su poste, pintado a franjas por los niños; banderita roja levantada (hay carta).
    b = Pieza("buzon", densidad=1.6, suave=35)
    bx, by = 4.95, -5.35
    caja(b, (bx - 0.07, bx + 0.07), (by - 0.07, by + 0.07), (Z_SUELO, 1.55), M["poste"], bisel=0.015)
    caja(b, (bx - 0.14, bx + 0.14), (by - 0.14, by + 0.14), (Z_SUELO, Z_SUELO + 0.06), M["poste"], bisel=0.015)
    perfil = [(-0.22, 0.0), (0.22, 0.0), (0.22, 0.20)]
    for k in range(1, 8):
        a = math.pi * k / 8
        perfil.append((0.22 * math.cos(a), 0.20 + 0.22 * math.sin(a)))
    perfil.append((-0.22, 0.20))
    Mb = T(bx, by + 0.42, 1.55) @ R("X", 90)  # perfil de pie, extrusión hacia -Y (hacia la calle)
    b.add(K.g_prisma(perfil, 0.0, 0.85), M["buzon"], Mb)
    # Tapa delantera algo mayor y su tirador.
    b.add(K.g_prisma([(x * 1.06, y * 1.04 - 0.01) for x, y in perfil], 0.85, 0.88), M["buzon"], Mb)
    caja(b, (bx - 0.05, bx + 0.05), (by - 0.47, by - 0.45), (1.80, 1.84), M["metal_brillo"])
    # Banderita.
    caja(b, (bx + 0.235, bx + 0.25), (by - 0.05, by + 0.03), (1.62, 2.05), M["flor_roja"])
    caja(b, (bx + 0.235, bx + 0.25), (by - 0.05, by + 0.15), (1.90, 2.05), M["flor_roja"])
    # Una carta asomando.
    caja(b, (bx - 0.12, bx + 0.10), (by - 0.50, by - 0.44), (1.66, 1.67), M["papel"], M=T(0, 0, 0))

    # Caja de juguetes junto a la puerta, tapa medio abierta; dentro un balón de playa y una espada de goma.
    j = Pieza("caja_juguetes", densidad=1.4, suave=None)
    jx, jy, jz = (-3.95, -2.85), (-4.5, -3.9), (Z_SUELO, 0.62)
    gr = 0.05
    caja(j, jx, jy, (jz[0], jz[0] + gr), M["caja_juguetes"], bisel=0.01)
    caja(j, jx, (jy[0], jy[0] + gr), jz, M["caja_juguetes"], bisel=0.015)
    caja(j, jx, (jy[1] - gr, jy[1]), jz, M["caja_juguetes"], bisel=0.015)
    caja(j, (jx[0], jx[0] + gr), (jy[0] + gr, jy[1] - gr), jz, M["caja_juguetes"], bisel=0.01)
    caja(j, (jx[1] - gr, jx[1]), (jy[0] + gr, jy[1] - gr), jz, M["caja_juguetes"], bisel=0.01)
    # Asas laterales.
    for x in (jx[0] - 0.03, jx[1] + 0.03):
        caja(j, (x - 0.02, x + 0.02), (-4.28, -4.12), (0.46, 0.52), M["tapa_juguetes"], bisel=0.008)
    # Tapa con bisagra en el borde de atrás, abierta 62°.
    Mt = T(0, jy[1], jz[1]) @ R("X", 62)
    caja(j, (jx[0] - 0.02, jx[1] + 0.02), (-0.62, 0.0), (0.0, 0.05), M["tapa_juguetes"], bisel=0.015, M=Mt)
    pb = Pieza("balon", densidad=1.2, suave=60)
    pb.add(esfera(0.21, 12, 8), M["balon"], T(-3.2, -4.2, 0.4))
    es = Pieza("espada", densidad=1.2, suave=35)
    Me = T(-3.62, -4.18, 0.25) @ R("Y", -24) @ R("X", -12)
    hojaesp = [(-0.045, 0.0), (0.045, 0.0), (0.045, 0.62), (0.0, 0.72), (-0.045, 0.62)]
    es.add(K.g_prisma(hojaesp, -0.018, 0.018), M["espada"], Me @ T(0, 0, 0.22) @ R("X", 90))
    caja(es, (-0.15, 0.15), (-0.035, 0.035), (0.18, 0.23), M["guarda"], bisel=0.012, M=Me)
    es.add(K.g_cilindro(0.028, 0.18, 8), M["goma"], Me)
    es.add(esfera(0.04, 8, 4), M["guarda"], Me)

    # Cajón-huerto del padre bajo la ventana: tablas, postes en las esquinas, tierra y verduras.
    h = Pieza("jardinera", densidad=1.2)
    hx, hy, hz = (1.0, 4.0), (-4.55, -3.86), (Z_SUELO, 0.70)
    t = 0.07
    for k in range(2):
        z = (hz[0] + k * 0.29, hz[0] + k * 0.29 + 0.28)
        caja(h, hx, (hy[0], hy[0] + t), z, M["madera"], bisel=0.012)
        caja(h, hx, (hy[1] - t, hy[1]), z, M["madera"], bisel=0.012)
        caja(h, (hx[0], hx[0] + t), (hy[0] + t, hy[1] - t), z, M["madera"], bisel=0.012)
        caja(h, (hx[1] - t, hx[1]), (hy[0] + t, hy[1] - t), z, M["madera"], bisel=0.012)
    for x in (hx[0] - 0.02, hx[1] + 0.02):
        for y in (hy[0] - 0.02, hy[1] + 0.02):
            caja(h, (x - 0.05, x + 0.05), (y - 0.05, y + 0.05), (hz[0], hz[1] + 0.04), M["madera"], bisel=0.012)
    ti = Pieza("tierra_jardinera", densidad=0.8)
    caja(ti, (hx[0] + t, hx[1] - t), (hy[0] + t, hy[1] - t), (hz[0] + 0.05, hz[1] - 0.06), M["tierra"])
    v = Pieza("verduras", densidad=0.9, suave=45)
    rng = random.Random(4)
    zt = hz[1] - 0.06
    for x in (1.45, 2.05, 2.65):  # lechugas: rosetas de hojas levantadas
        for k in range(6):
            a = k * 360 / 6 + rng.uniform(-15, 15)
            v.add(hoja(0.22, 0.17, 0.016), M["lechuga"], T(x, -4.2, zt + 0.02) @ R("Z", a) @ R("Y", -rng.uniform(35, 55)))
        v.add(esfera(0.07, 6, 3, 0.8), M["lechuga"], T(x, -4.2, zt + 0.05))
    # Tomatera con su caña atada y tres tomates.
    tx, ty = 3.6, -4.2
    v.add(K.g_cilindro(0.018, 0.95, 5), M["palo"], T(tx + 0.06, ty, zt - 0.02))
    v.add(K.g_tubo([(tx, ty, zt), (tx + 0.02, ty, zt + 0.35), (tx - 0.02, ty + 0.01, zt + 0.7)], 0.018, 5), M["hoja"])
    for k in range(7):
        z = zt + 0.12 + k * 0.09
        v.add(hoja(0.18, 0.11), M["hoja"], T(tx, ty, z) @ R("Z", k * 137) @ R("Y", -25))
    for (dx, dz) in ((0.09, 0.30), (-0.08, 0.42), (0.05, 0.55)):
        v.add(esfera(0.055, 7, 4), M["tomate"], T(tx + dx, ty - 0.04, zt + dz))
    # Zanahorias: penachos finos.
    for x in (3.0, 3.18):
        for k in range(4):
            v.add(hoja(0.2, 0.05, 0.012), M["hoja"], T(x, -4.1, zt) @ R("Z", k * 90 + 20) @ R("Y", -70))


def ventanas(M):
    # Frontal baja: marco con la franja azul de los niños, parteluz, alféizar con macetas, dibujo, cortinas.
    u0, u1 = VENT_BAJA["x"][0] - X0, VENT_BAJA["x"][1] - X0
    W = ventana("vent_baja", "frente", u0, u1, VENT_BAJA["z"][0], VENT_BAJA["z"][1], M, M["marco_azul1"], 2.0,
                parteluz=True, alfeizar=True)
    zs = VENT_BAJA["z"][0] - 0.22 + 0.02  # encima del alféizar
    mac = Pieza("macetas_alfeizar", densidad=1.3, suave=40)
    mac.add(maceta(0.12, 0.16, 0.27), M["maceta_roja"], T(1.35, Y0 - 0.2, zs))
    mac.add(maceta(0.11, 0.14, 0.24), M["maceta_verde"], T(2.15, Y0 - 0.2, zs))
    mac.add(K.g_cilindro(0.145, 0.03, 12), M["tierra"], T(1.35, Y0 - 0.2, zs + 0.21))
    mac.add(K.g_cilindro(0.125, 0.03, 12), M["tierra"], T(2.15, Y0 - 0.2, zs + 0.19))
    pl = Pieza("plantas_alfeizar", densidad=0.9, suave=45)
    rng = random.Random(9)
    # Geranio rojo en la maceta roja.
    for k in range(8):
        pl.add(hoja(0.16, 0.12), M["hoja"], T(1.35, Y0 - 0.2, zs + 0.24) @ R("Z", k * 45 + rng.uniform(-10, 10))
               @ R("Y", -rng.uniform(15, 40)))
    for (dx, dy, dz) in ((0.0, 0.0, 0.42), (0.08, -0.05, 0.36), (-0.07, 0.03, 0.38)):
        pl.add(K.g_cilindro(0.008, dz - 0.24, 4), M["hoja"], T(1.35 + dx, Y0 - 0.2 + dy, zs + 0.24))
        for k in range(5):
            pl.add(esfera(0.03, 5, 3), M["flor_roja"], T(1.35 + dx + rng.uniform(-0.04, 0.04),
                                                          Y0 - 0.2 + dy + rng.uniform(-0.04, 0.04),
                                                          zs + dz + rng.uniform(-0.01, 0.03)))
    # Planta de hojas largas en la verde, con una flor amarilla.
    for k in range(9):
        pl.add(hoja(0.28, 0.07), M["hoja"], T(2.15, Y0 - 0.2, zs + 0.21) @ R("Z", k * 40) @ R("Y", -rng.uniform(40, 70)))
    pl.add(K.g_cilindro(0.008, 0.25, 4), M["hoja"], T(2.17, Y0 - 0.2, zs + 0.21))
    for k in range(5):
        pl.add(hoja(0.05, 0.035, 0.01), M["flor_amarilla"], T(2.17, Y0 - 0.2, zs + 0.46) @ R("Z", k * 72) @ R("Y", -20))
    # Dibujo de la familia pegado por dentro del cristal (mirando a la calle).
    d = Pieza("dibujo", densidad=7.0, planos={M["dibujo"].name: ((1, 0, 0), (0, 0, 1), (3.0, 0, 1.70), 0.85, 0.64)})
    caras = caja(d, (3.0, 3.85), (Y0 + 0.128, Y0 + 0.136), (1.70, 2.34), M["papel"], M=R("Y", 0))
    mat_si(d, caras, lambda c, f: f.normal.y < -0.9, M["dibujo"])
    # Cortinas de colores recogidas a los lados, con su barra.
    cor = Pieza("cortinas", densidad=0.6, suave=60)
    yb = Y0 + G + 0.12
    cor.add(K.g_cilindro(0.025, 4.0, 8), M["metal_brillo"], T(VENT_BAJA["x"][0] - 0.45, yb, 3.62) @ R("Y", 90))
    for (xa, xb) in ((VENT_BAJA["x"][0] - 0.35, VENT_BAJA["x"][0] + 0.55), (VENT_BAJA["x"][1] - 0.55, VENT_BAJA["x"][1] + 0.35)):
        ancho, alto = xb - xa, 2.45
        cortes = [ancho * k / 10 for k in range(1, 10)]
        cortes_v = [alto * k / 4 for k in range(1, 4)]
        v, f, tg = K.g_pared(ancho, alto, 0.025, [], cortes, cortes_v)
        v = [(x, y + 0.06 * math.sin(x / ancho * 10 * math.pi) * (0.5 + 0.5 * (1 - z / alto)), z) for x, y, z in v]
        cor.add((v, f), M["cortina"], T(xa, yb + 0.06, 3.58 - alto))

    # Frontal alta (dormitorio de los niños): estrellas pegadas en el cristal y persiana medio subida.
    u0, u1 = VENT_ALTA["x"][0] - X0, VENT_ALTA["x"][1] - X0
    ventana("vent_alta", "frente", u0, u1, VENT_ALTA["z"][0], VENT_ALTA["z"][1], M, alfeizar=True)
    est = Pieza("pegatinas_estrellas", densidad=1.5)
    yv = Y0 + 0.085 - 0.006
    colores = ["estrella_amarilla", "estrella_rosa", "estrella_cian", "estrella_verde", "estrella_amarilla",
               "estrella_rosa", "estrella_cian"]
    sitios = [(-0.55, 5.05, 0.13), (-0.2, 5.6, 0.09), (0.25, 5.2, 0.11), (0.7, 5.75, 0.08), (1.1, 5.1, 0.12),
              (1.25, 5.95, 0.07), (-0.6, 5.95, 0.08)]
    for (x, z, r), c in zip(sitios, colores):
        est.add(K.g_estrella(r, r * 0.45, 0.008, 5, rng.uniform(-0.4, 0.4)), M[c], T(x, yv, z) @ R("X", 90))
    pe = Pieza("persiana", densidad=0.6)
    yp = Y0 + G + 0.06
    caja(pe, (VENT_ALTA["x"][0] - 0.15, VENT_ALTA["x"][1] + 0.15), (yp - 0.07, yp + 0.09), (6.38, 6.56), M["persiana"],
         bisel=0.02)
    caja(pe, (VENT_ALTA["x"][0] - 0.05, VENT_ALTA["x"][1] + 0.05), (yp - 0.008, yp + 0.008), (5.55, 6.38), M["persiana"])
    pe.add(K.g_cilindro(0.025, VENT_ALTA["x"][1] - VENT_ALTA["x"][0] + 0.1, 8), M["aluminio"],
           T(VENT_ALTA["x"][0] - 0.05, yp, 5.55) @ R("Y", 90))
    pe.add(K.g_tubo([(1.35, yp - 0.03, 5.55), (1.35, yp - 0.03, 5.15)], 0.006, 4), M["cable"])
    pe.add(K.g_torno([(0, 0), (0.03, 0), (0.03, 0.05), (0, 0.05)], 6), M["persiana"], T(1.35, yp - 0.03, 5.10))

    # Lateral 1 (pared derecha, planta baja): marco a medio pintar de azul y rejilla de ventilación debajo.
    u0, u1 = VENT_LAT1["y"][0] - (Y0 + G), VENT_LAT1["y"][1] - (Y0 + G)
    ventana("vent_lat1", "der", u0, u1, VENT_LAT1["z"][0], VENT_LAT1["z"][1], M, M["marco_azul2"], 1.8, casing=0.20,
            alfeizar=True)
    rj = Pieza("rejilla", densidad=1.2)
    Wd = PAREDES["der"]
    uc = -(Y0 + G)
    rj.add(K.g_pared(1.1, 0.42, 0.05, [(0.06, 0.06, 1.04, 0.36)]), M["marco"], Wd @ T(uc - 0.55, -0.05, 0.72))
    caja(rj, (uc - 0.5, uc + 0.5), (0.0, 0.02), (0.78, 1.08), M["lente"], M=Wd)
    for k in range(4):
        z = 0.82 + k * 0.075
        caja(rj, (uc - 0.49, uc + 0.49), (-0.04, 0.0), (-0.012, 0.012), M["marco"], M=Wd @ T(0, 0, z) @ R("X", 35))

    # Lateral 2 (pared izquierda, planta alta): pequeña.
    u0, u1 = (Y1 - G) - VENT_LAT2["y"][1], (Y1 - G) - VENT_LAT2["y"][0]
    ventana("vent_lat2", "izq", u0, u1, VENT_LAT2["z"][0], VENT_LAT2["z"][1], M, casing=0.16, alfeizar=True)


def instalaciones(M):
    """Bajantes con abrazaderas (una con cinta americana), medidor de energía con pantallita de neón y cableado."""
    y_al = Y1 + VUELO
    za = z_tejado_abajo(y_al)
    b = Pieza("bajantes", densidad=0.9, suave=50)
    for (x, lado) in ((4.62, -1), (-4.62, 1)):
        yc = lado * (y_al + 0.17)
        yw = lado * (Y1 + 0.12)
        pts = [(x, yc, za - 0.2), (x, yc, za - 0.45), (x, yw, za - 0.85), (x, yw, 0.45), (x, yw + lado * 0.05, 0.28),
               (x, yw + lado * 0.32, Z_SUELO + 0.1)]
        b.add(K.g_tubo(pts, 0.075, 8), M["pvc"])
        for z in (1.4, 3.6, 5.8):
            b.add(K.g_toro([(0.085, -0.03), (0.105, -0.03), (0.105, 0.03), (0.085, 0.03)], 8), M["metal_galv"],
                  T(x, yw, z))
            caja(b, (x - 0.025, x + 0.025), sorted((yw - lado * 0.10, lado * Y1)), (z - 0.03, z + 0.03), M["metal_galv"])
    # Cinta americana en la bajante delantera (una grieta arreglada a lo rápido), torcida.
    b.add(K.g_cilindro(0.083, 0.16, 8), M["cinta"], T(4.62, -(Y1 + 0.12), 2.1) @ R("X", 6))
    b.add(K.g_cilindro(0.082, 0.07, 8), M["cinta"], T(4.62, -(Y1 + 0.12), 2.22) @ R("X", -9))

    # Medidor de energía en la pared izquierda.
    m = Pieza("medidor", densidad=1.6, suave=None)
    xm = X0
    ym, zm = 1.5, 2.0
    caja(m, (xm - 0.15, xm), (ym - 0.26, ym + 0.26), (zm, zm + 0.7), M["medidor"], bisel=0.02)
    caja(m, (xm - 0.17, xm - 0.14), (ym - 0.2, ym + 0.2), (zm + 0.36, zm + 0.62), M["lampara"], bisel=0.008)
    for k, yy in enumerate((ym - 0.12, ym + 0.0, ym + 0.12)):
        m.add(K.g_cilindro(0.025, 0.03, 8), M["lente"] if k else M["flor_roja"], T(xm - 0.15, yy, zm + 0.18) @ R("Y", -90))
    n = Pieza("pantalla_medidor", grupo="neon", densidad=0.5)
    caja(n, (xm - 0.18, xm - 0.165), (ym - 0.15, ym + 0.15), (zm + 0.44, zm + 0.56), M["neon"])
    # Tubo (conduit) hacia arriba hasta el alero y cable hacia el suelo.
    m.add(K.g_tubo([(xm - 0.07, ym, zm + 0.7), (xm - 0.07, ym, Z_ALERO - 0.25), (xm + 0.05, ym, Z_ALERO - 0.12)],
                   0.035, 6), M["metal_galv"])
    for z in (3.3, 5.0, 6.3):
        caja(m, (xm - 0.12, xm), (ym - 0.06, ym + 0.06), (z - 0.025, z + 0.025), M["metal_galv"])
    cab = Pieza("cables", densidad=0.6, suave=50)
    cab.add(K.g_tubo([(xm - 0.07, ym + 0.15, zm), (xm - 0.08, ym + 0.18, 0.7), (xm - 0.12, ym + 0.2, 0.25),
                      (xm - 0.3, ym + 0.2, 0.02), (xm - 0.3, ym + 0.2, -0.05)], 0.02, 5), M["cable"])
    # Cable de la lámpara: sale del medidor, sube bajo la moldura, dobla la esquina y llega a la puerta.
    xl = (PUERTA["x"][0] + PUERTA["x"][1]) / 2
    zc = 3.86
    cab.add(K.g_tubo([(xm - 0.07, ym - 0.2, zm + 0.66), (xm - 0.05, ym - 0.4, zc), (X0 - 0.2, Y0 + 0.1, zc),
                      (X0 - 0.22, Y0 - 0.2, zc), (X0 + 0.2, Y0 - 0.21, zc), (xl - 0.12, Y0 - 0.03, zc)], 0.017, 5),
            M["cable"])
    for x in (-4.3, -3.4, -2.5):
        caja(cab, (x - 0.025, x + 0.025), (Y0 - 0.05, Y0), (zc - 0.03, zc + 0.03), M["lampara"])
    for y in (0.4, -1.0, -2.4):
        caja(cab, (X0 - 0.05, X0), (y - 0.025, y + 0.025), (zc - 0.03, zc + 0.03), M["lampara"])


def tendedero(M):
    """Dos postes en T en el lateral derecho, dos cables tensos y la ropa con pinzas de colores."""
    p = Pieza("tendedero", densidad=0.9, suave=None)
    xp = 6.1
    ys = (-2.9, 2.9)
    zl = 4.05
    for y in ys:
        caja(p, (xp - 0.18, xp + 0.18), (y - 0.18, y + 0.18), (0, 0.14), M["hormigon"], bisel=0.02)
        caja(p, (xp - 0.06, xp + 0.06), (y - 0.06, y + 0.06), (0.14, 4.25), M["poste"], bisel=0.015)
        caja(p, (xp - 0.42, xp + 0.42), (y - 0.05, y + 0.05), (4.1, 4.2), M["poste"], bisel=0.015)
        for s in (-1, 1):
            p.add(K.g_tubo([(xp + s * 0.04, y, 3.75), (xp + s * 0.32, y, 4.1)], 0.025, 4), M["poste"])
    lineas = (xp - 0.33, xp + 0.33)
    c = Pieza("cuerdas", densidad=0.3, suave=60)

    def z_linea(y):
        t = (y - ys[0]) / (ys[1] - ys[0])
        return zl - 0.10 * 4 * t * (1 - t)  # cable tenso: comba pequeña
    for x in lineas:
        pts = [(x, ys[0] + (ys[1] - ys[0]) * k / 10, z_linea(ys[0] + (ys[1] - ys[0]) * k / 10)) for k in range(11)]
        c.add(K.g_tubo(pts, 0.018, 4), M["cable"])

    ropa = Pieza("ropa", densidad=1.0, suave=50)
    pinzas = Pieza("pinzas", densidad=0.6)
    colores_pinza = ["pinza_rosa", "pinza_verde", "pinza_azul", "pinza_amarilla"]
    rng = random.Random(17)
    contador = [0]

    def colgar(nombre, x, y, ancho, alto, huecos, mat, ondas=0.05, fase=0.0):
        cu = [ancho * k / 6 for k in range(1, 6)]
        cv = [alto * k / 3 for k in range(1, 3)]
        v, f, tg = K.g_pared(ancho, alto, 0.035, huecos, cu, cv)
        v = [(u, yy + ondas * math.sin(u / ancho * 2 * math.pi * 1.5 + fase) * (1 - zz / alto) + 0.03 * math.sin(zz * 4),
              zz) for u, yy, zz in v]
        zt = z_linea(y)
        Mr = T(x + 0.0175, y - ancho / 2, zt - 0.02 - alto) @ R("Z", 90)
        ropa.add((v, f), mat, Mr)
        for yy in (y - ancho / 2 + 0.06, y + ancho / 2 - 0.06):  # dos pinzas en las esquinas de arriba
            cp = M[colores_pinza[contador[0] % 4]]
            contador[0] += 1
            Mp = T(x, yy, z_linea(yy)) @ R("Y", rng.uniform(-8, 8))
            for s in (-1, 1):
                caja(pinzas, (s * 0.022 - 0.012, s * 0.022 + 0.012), (-0.022, 0.022), (-0.15, 0.04), cp,
                     M=Mp @ R("Y", s * 6))
            pinzas.add(K.g_cilindro(0.014, 0.05, 6), M["metal_brillo"], Mp @ T(0, -0.025, -0.04) @ R("X", -90))

    # Camiseta naranja de niño, pantalón vaquero, toalla de rayas y un par de calcetines amarillos.
    colgar("camiseta", lineas[1], -1.75, 0.95, 0.85,
           [(0, 0, 0.2, 0.60), (0.75, 0, 0.95, 0.60), (0.37, 0.80, 0.58, 0.85)], M["camiseta"], 0.05, 0.3)
    colgar("pantalon", lineas[1], -0.3, 0.62, 1.0, [(0.28, 0, 0.34, 0.55)], M["pantalon"], 0.04, 1.4)
    colgar("toalla", lineas[0], 0.9, 0.85, 1.15, [], M["toalla"], 0.06, 2.1)
    colgar("calcetin1", lineas[0], 2.05, 0.26, 0.36, [(0.12, 0.12, 0.26, 0.36)], M["calcetin"], 0.0)
    colgar("calcetin2", lineas[0], 2.4, 0.26, 0.36, [(0.12, 0.12, 0.26, 0.36)], M["estrella_rosa"], 0.0)


def bici(M):
    """
    Bici de niño apoyada en la pared izquierda, torcida y con el manillar girado: la dejaron a toda prisa.
    Local: X hacia delante, Y lateral (hacia la pared), Z arriba.
    """
    p = Pieza("bici", densidad=1.1, suave=40)
    Mb = T(-5.66, -2.55, 0) @ R("Z", -90 - 7) @ R("X", -13)
    rd = 0.38  # radio de la rueda (al centro del neumático)
    rt = 0.055
    ruedas = {"tras": Vector((-0.62, 0, rd + rt)), "del": Vector((0.62, 0, rd + rt))}
    giro_dir = 24  # grados que está girado el manillar
    eje_dir_a = Vector((0.40, 0, 1.02))
    eje_dir_b = Vector((0.50, 0, 0.74))
    Mdir = Matrix.Translation(eje_dir_b) @ Matrix.Rotation(math.radians(giro_dir), 4, (eje_dir_a - eje_dir_b).normalized()) \
        @ Matrix.Translation(-eje_dir_b)

    def rueda(c, Mx):
        Mr = Mb @ Mx @ T(*c) @ R("X", 90)
        perfil = [(rd + rt * math.cos(a), rt * math.sin(a)) for a in [2 * math.pi * k / 5 for k in range(5)]]
        p.add(K.g_toro(perfil, 14), M["goma"], Mr)
        p.add(K.g_toro([(0.28, -0.022), (0.335, -0.022), (0.335, 0.022), (0.28, 0.022)], 14), M["bici_blanco"], Mr)
        p.add(K.g_cilindro(0.045, 0.14, 8), M["metal_brillo"], Mr @ T(0, 0, -0.07))
        for k in range(5):  # radios de plástico (rueda de niño)
            p.add(K.g_caja(0.26, 0.04, 0.025), M["bici_blanco"], Mr @ R("Z", k * 72 + 10) @ T(0.165, 0, 0))
    rueda(ruedas["tras"], Matrix.Identity(4))
    rueda(ruedas["del"], Mdir)

    bb = Vector((-0.10, 0, 0.36))
    st = Vector((-0.30, 0, 0.92))
    cuadro = M["bici"]
    W = lambda v: Mb @ Vector(v)  # noqa: E731
    p.add(K.g_tubo([W(eje_dir_b + Vector((-0.02, 0, 0.04))), W((0.15, 0, 0.45)), W(bb)], 0.042, 6), cuadro)  # bajo
    p.add(K.g_tubo([W(bb), W(st)], 0.04, 6), cuadro)  # sillín
    p.add(K.g_tubo([W(eje_dir_a + Vector((-0.02, 0, -0.08))), W((-0.27, 0, 0.84))], 0.033, 6), cuadro)  # superior
    for s in (-1, 1):
        r = ruedas["tras"] + Vector((0, s * 0.07, 0))
        p.add(K.g_tubo([W(bb + Vector((0, s * 0.04, 0))), W(r)], 0.022, 6), cuadro)
        p.add(K.g_tubo([W(st + Vector((0, s * 0.03, -0.04))), W(r)], 0.02, 6), cuadro)
    p.add(K.g_tubo([W(eje_dir_b), W(eje_dir_a)], 0.05, 8), cuadro)  # tubo de dirección
    # Horquilla, potencia y manillar (todo girado con la dirección).
    Wd = lambda v: Mb @ Mdir @ Vector(v)  # noqa: E731
    for s in (-1, 1):
        p.add(K.g_tubo([Wd(eje_dir_b + Vector((0, s * 0.05, 0))), Wd((0.57, s * 0.07, 0.6)),
                        Wd(ruedas["del"] + Vector((0, s * 0.07, 0)))], 0.022, 6), cuadro)
    pot = eje_dir_a + Vector((-0.04, 0, 0.16))
    p.add(K.g_tubo([Wd(eje_dir_a), Wd(pot)], 0.028, 6), M["metal_brillo"])
    manillar = [Wd(pot + Vector((-0.10, -0.33, 0.04))), Wd(pot + Vector((0.0, -0.20, 0.0))),
                Wd(pot + Vector((0.0, 0.20, 0.0))), Wd(pot + Vector((-0.10, 0.33, 0.04)))]
    p.add(K.g_tubo(manillar, 0.022, 6), M["metal_brillo"])
    for s in (-1, 1):
        a = pot + Vector((-0.10, s * 0.33, 0.04))
        b = pot + Vector((-0.12, s * 0.45, 0.06))
        p.add(K.g_tubo([Wd(a), Wd(b)], 0.032, 6), M["puno"])
        # Flecos de colores en los puños.
        for k, col in enumerate(("estrella_rosa", "estrella_amarilla", "estrella_cian")):
            ext = b + Vector((-0.01, s * 0.01, 0))
            p.add(K.g_tubo([Wd(ext), Wd(ext + Vector((-0.04 - 0.02 * k, s * (0.05 + 0.02 * k), -0.16 + 0.02 * k)))],
                           0.008, 3), M[col])
    # Timbre.
    p.add(K.g_cilindro(0.04, 0.03, 10), M["metal_brillo"], Mb @ Mdir @ T(*(pot + Vector((-0.02, 0.12, 0.03)))))
    # Sillín y tija.
    sp = st + Vector((-0.03, 0, 0.14))
    p.add(K.g_tubo([W(st), W(sp)], 0.025, 6), M["metal_brillo"])
    sillin = [(-0.16, -0.05), (0.04, -0.11), (0.20, -0.04), (0.20, 0.04), (0.04, 0.11), (-0.16, 0.05)]
    p.add(K.g_prisma(sillin, 0.0, 0.065), M["sillin"], Mb @ T(*sp))
    # Bielas, plato con guardacadenas y pedales.
    p.add(K.g_cilindro(0.12, 0.02, 14), M["metal_galv"], Mb @ T(*bb) @ T(0, 0.07, 0) @ R("X", 90))
    guarda = [(-0.15, -0.09), (0.55, -0.05), (0.62, 0.0), (0.55, 0.06), (-0.15, 0.12)]
    p.add(K.g_prisma(guarda, 0.0, 0.015), M["bici_blanco"], Mb @ T(*bb) @ T(0, 0.10, 0) @ R("X", 90) @ R("Z", 180 + 7))
    for s, ang in ((1, 40), (-1, 220)):
        Mc = Mb @ T(*bb) @ T(0, s * 0.11, 0) @ R("Y", ang)
        caja(p, (-0.02, 0.02), (-0.012, 0.012), (0, 0.17), M["metal_brillo"], M=Mc)
        caja(p, (-0.07, 0.07), (s * 0.02, s * 0.12) if s > 0 else (s * 0.12, s * 0.02), (0.15, 0.19), M["goma"],
             M=Mc)
    # Guardabarros traseros (de colores, un poco abollado).
    arco = [ruedas["tras"] + Vector((math.cos(a) * 0.46, 0, math.sin(a) * 0.46)) for a in
            [math.radians(x) for x in (100, 125, 150, 175, 200)]]
    p.add(K.g_tubo([W(x) for x in arco], 0.03, 6), M["bici_blanco"])

    # La maceta de barro que tiró: base volcada, trozos, tierra derramada y la planta en el suelo.
    rota = Pieza("maceta_rota", densidad=1.2, suave=35)
    cx, cy = -5.55, -4.35
    rota.add(maceta(0.13, 0.15, 0.12, 0.022, 0.0, 10), M["terracota"],
             T(cx + 0.12, cy + 0.05, Z_SUELO + 0.14) @ R("Y", 95) @ R("Z", 20))
    rng = random.Random(23)
    for k in range(7):
        a0 = rng.uniform(0, 6.28)
        Mt = T(cx + rng.uniform(-0.45, 0.45), cy + rng.uniform(-0.45, 0.35), Z_SUELO + 0.01) @ R("Z", rng.uniform(0, 360))
        rota.add(trozo_maceta(0.16, 0.022, a0, a0 + rng.uniform(0.5, 1.0), 0.0, rng.uniform(0.06, 0.11), 3, 0.02, rng),
                 M["terracota"], Mt @ R("X", 90 + rng.uniform(-20, 20)) @ T(-0.16, 0, 0))
    tm = Pieza("tierra_derramada", densidad=0.8, suave=50)
    perfil = [(0, Z_SUELO - 0.01), (0.32, Z_SUELO - 0.01), (0.26, Z_SUELO + 0.04), (0.14, Z_SUELO + 0.08), (0, Z_SUELO + 0.09)]
    v, f = K.g_torno(perfil, 10)
    v = [(x * (1 + 0.25 * math.sin(math.atan2(y, x) * 3)), y * 0.8, z) for x, y, z in v]
    tm.add((v, f), M["tierra"], T(cx - 0.05, cy, 0))
    for k in range(5):
        tm.add(esfera(0.04, 6, 3, 0.6), M["tierra"], T(cx + rng.uniform(-0.5, 0.4), cy + rng.uniform(-0.45, 0.4),
                                                       Z_SUELO + 0.01))
    pl = Pieza("planta_caida", densidad=0.9, suave=45)
    pl.add(K.g_tubo([(cx, cy, Z_SUELO + 0.06), (cx + 0.15, cy - 0.12, Z_SUELO + 0.05), (cx + 0.3, cy - 0.15, Z_SUELO + 0.04)],
                    0.012, 4), M["hoja"])
    for k in range(6):
        pl.add(hoja(0.15, 0.1), M["hoja"], T(cx + 0.05 * k, cy - 0.025 * k, Z_SUELO + 0.05) @ R("Z", k * 70) @ R("Y", -10))
    for k in range(4):
        pl.add(esfera(0.03, 5, 3), M["flor_roja"], T(cx + 0.28 + rng.uniform(-0.04, 0.04), cy - 0.15 + rng.uniform(-0.05, 0.05),
                                                     Z_SUELO + 0.05))


def interior(M):
    """Lo que se ve por las ventanas: lámparas encendidas, cocina y mesa abajo, litera de los niños arriba."""
    p = Pieza("muebles", densidad=0.35)
    # Abajo: encimera y armario alto en la pared del fondo, mesa con dos sillas, lámpara.
    caja(p, (0.4, 4.6), (Y1 - G - 0.6, Y1 - G), (Z_BASE, 1.9), M["mueble"])
    caja(p, (0.35, 4.65), (Y1 - G - 0.65, Y1 - G), (1.9, 1.98), M["madera"])
    caja(p, (0.4, 4.6), (Y1 - G - 0.4, Y1 - G), (2.8, 3.6), M["mueble"])
    caja(p, (1.7, 3.3), (-0.3, 0.7), (1.62, 1.7), M["madera"])
    for x in (1.8, 3.2):
        for y in (-0.2, 0.6):
            caja(p, (x - 0.04, x + 0.04), (y - 0.04, y + 0.04), (Z_BASE, 1.62), M["madera"])
    for x, y in ((2.1, -0.75), (2.9, 1.15)):
        caja(p, (x - 0.25, x + 0.25), (y - 0.25, y + 0.25), (1.05, 1.12), M["caja_juguetes"])
        caja(p, (x - 0.22, x + 0.22), (y - 0.22, y + 0.22), (Z_BASE, 1.05), M["caja_juguetes"])
    luces = Pieza("luces_interiores", densidad=0.3, suave=60)
    for (x, y, z) in ((2.5, 0.2, Z_MOLD[0]), (0.3, 0.6, Z_ALERO - 0.15)):
        luces.add(K.g_cilindro(0.008, 0.25, 4), M["cable"], T(x, y, z - 0.25))
        luces.add(K.g_torno([(0, 0), (0.22, 0.0), (0.24, 0.05), (0.05, 0.12), (0, 0.12)], 12), M["luz_calida"],
                  T(x, y, z - 0.37))
    # Arriba: litera (dos niños) con mantas de colores, y una lamparita de estrella.
    bx = (-1.6, 1.9)
    by = (Y1 - G - 1.25, Y1 - G - 0.05)
    for zb in (Z_MOLD[1], 5.5):
        caja(p, bx, by, (zb + 0.25, zb + 0.4), M["madera"])
        caja(p, (bx[0] + 0.05, bx[1] - 0.05), (by[0] + 0.05, by[1] - 0.05), (zb + 0.4, zb + 0.6), M["colchon"])
        caja(p, (bx[0] + 0.6, bx[1] - 0.03), (by[0] + 0.02, by[1] - 0.02), (zb + 0.58, zb + 0.66), M["manta"])
        caja(p, (bx[0] + 0.1, bx[0] + 0.55), (by[0] + 0.25, by[1] - 0.25), (zb + 0.6, zb + 0.75), M["almohada"])
    for x in bx:
        for y in by:
            caja(p, (x - 0.06, x + 0.06), (y - 0.06, y + 0.06), (Z_MOLD[1], 6.45), M["madera"])
    luces.add(K.g_estrella(0.18, 0.08, 0.04), M["estrella_luz"], T(2.6, Y1 - G - 0.01, 5.4) @ R("X", 90))


# ----------------------------------------------------------------------------------------------------------------
# Ensamblado, atlas, render, exportación
# ----------------------------------------------------------------------------------------------------------------


def construir():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "METRIC"
    scn.unit_settings.scale_length = 1.0
    scn.world = bpy.data.worlds.new("mundo")
    I = imagenes()
    M = materiales(I)
    estructura(M)
    tejado(M)
    tejado_detalles(M)
    puerta(M)
    entrada(M)
    ventanas(M)
    instalaciones(M)
    tendedero(M)
    bici(M)
    interior(M)
    objs = K.cerrar_todas()
    malos = {o.name: K.comprobar_cerradas(o) for o in objs}
    abiertas = {k: v for k, v in malos.items() if v}
    print("[comprobación] piezas con aristas abiertas:", abiertas or "ninguna")
    grupos = {}
    for o in objs:
        grupos.setdefault(o["grupo"], []).append(o)
    final = {
        "casa": K.unir(grupos["casa"], NOMBRE),
        "puerta": K.unir(grupos["puerta"], f"{NOMBRE}_Puerta"),
        "cristal": K.unir(grupos["cristal"], f"{NOMBRE}_Cristal"),
        "neon": K.unir(grupos["neon"], f"{NOMBRE}_Neon"),
    }
    # Pivote de la puerta en el eje de las bisagras.
    pu = final["puerta"]
    pu.data.transform(Matrix.Translation(-PIVOTE_PUERTA))
    pu.location = PIVOTE_PUERTA
    return final, M, abiertas


def preparar_render(final, tam=900):
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.use_denoising = True
    scn.cycles.samples = 24 if RAPIDO else 96
    scn.render.resolution_x = scn.render.resolution_y = tam
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    w = scn.world
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    cielo = w.node_tree.nodes.new("ShaderNodeTexSky")
    cielo.sky_type = "HOSEK_WILKIE"
    cielo.sun_direction = Vector((-0.55, -0.75, 0.6)).normalized()
    cielo.turbidity = 3.0
    w.node_tree.links.new(cielo.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.75
    sol_d = bpy.data.lights.new("sol", "SUN")
    sol_d.energy = 4.2
    sol_d.angle = math.radians(2.5)
    sol_d.color = (1.0, 0.95, 0.88)
    sol = bpy.data.objects.new("sol", sol_d)
    sol.rotation_euler = Vector((-0.55, -0.75, 0.6)).to_track_quat("Z", "Y").to_euler()
    scn.collection.objects.link(sol)
    # Suelo de tierra/césped corto alrededor.
    bpy.ops.mesh.primitive_plane_add(size=80, location=(0, 0, -0.002))
    s = bpy.context.active_object
    s.name = "suelo_render"
    m = K.material("suelo_render", "#6E7B4E", 0.95, nodos=lambda N: N.set(
        "Base Color", N.mezcla(N.ruido(N.objeto(), 0.6, 4), K.srgb("#5F6E42"), K.srgb("#7D7A58"))))
    s.data.materials.append(m)
    # Cristal para el render (en Roblox: material Glass).
    vid = K.material("cristal_render", "#DCEFF5", 0.03)
    vid.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
    vid.node_tree.nodes["Principled BSDF"].inputs["IOR"].default_value = 1.05
    K.poner_material(final["cristal"], vid)


def camara(objetivo, az, el, dist, lente=50):
    scn = bpy.context.scene
    cam = scn.camera
    if cam is None:
        cd = bpy.data.cameras.new("cam")
        cam = bpy.data.objects.new("cam", cd)
        scn.collection.objects.link(cam)
        scn.camera = cam
    cam.data.lens = lente
    a, e = math.radians(az), math.radians(el)
    d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    cam.location = Vector(objetivo) + d * dist
    cam.rotation_euler = (Vector(objetivo) - cam.location).to_track_quat("-Z", "Y").to_euler()


def render(ruta):
    bpy.context.scene.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
    return ruta


def hoja_contactos(rutas, salida, titulo, notas, columnas=4):
    from PIL import Image, ImageDraw, ImageFont
    ims = [(n, Image.open(r).convert("RGB")) for n, r in rutas]
    t = ims[0][1].size[0]
    filas = (len(ims) + columnas - 1) // columnas
    cab = 70 + 22 * len(notas)
    hoja = Image.new("RGB", (columnas * t, cab + filas * t), (16, 18, 24))
    d = ImageDraw.Draw(hoja)
    f1 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 30)
    f2 = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 17)
    d.text((16, 12), titulo, fill=(255, 214, 102), font=f1)
    for i, n in enumerate(notas):
        d.text((18, 56 + i * 22), n, fill=(210, 214, 224), font=f2)
    for i, (n, im) in enumerate(ims):
        x, y = (i % columnas) * t, cab + (i // columnas) * t
        hoja.paste(im, (x, y))
        d.rectangle((x, y, x + t - 1, y + t - 1), outline=(40, 44, 56))
        d.text((x + 12, y + 10), n, fill=(255, 255, 255), font=f2)
    hoja.save(salida)
    print("[ok] hoja:", salida)


def main():
    os.makedirs(RAIZ, exist_ok=True)
    final, M, abiertas = construir()
    objs = list(final.values())
    for o in objs:
        K.triangular(o)
    tris = {o.name: K.triangulos(o) for o in objs}
    print("[triángulos]", tris, "total", sum(tris.values()))

    # Atlas compartido.
    factores = {"interior": 0.25, "techo": 0.2, "suelo_madera": 0.3}
    K.desplegar_atlas(objs, factores, margen=0.0018 if not RAPIDO else 0.0035)
    texel = K.densidad_texel([final["casa"]], TAM_ATLAS)
    texel_puerta = K.densidad_texel([final["puerta"]], TAM_ATLAS)
    print(f"[atlas] {texel:.0f} px/stud (casa), {texel_puerta:.0f} px/stud (puerta)")
    K.hornear_atlas(objs, TAM_ATLAS, RAIZ, NOMBRE)
    mat_final = K.material_final(f"{NOMBRE}_atlas", RAIZ, NOMBRE)
    for o in objs:
        K.poner_material(o, mat_final)
        o.data.uv_layers.remove(o.data.uv_layers["fuente"])

    # FBX (con el giro de importación) .
    K.exportar_fbx(os.path.join(RAIZ, f"{NOMBRE}.fbx"), objs)

    # Turnaround: 8 vistas alrededor.
    preparar_render(final, 640 if RAPIDO else 900)
    centro = Vector((0.0, -0.6, 3.6))
    vistas = []
    carpeta = os.path.join(TMP, "vistas")
    os.makedirs(carpeta, exist_ok=True)
    for i, (nombre, az, el) in enumerate((("Frente", 0, 12), ("3/4 frente-der", 45, 16), ("Derecha", 90, 10),
                                         ("3/4 atrás-der", 135, 18), ("Atrás", 180, 12), ("3/4 atrás-izq", 225, 18),
                                         ("Izquierda", 270, 10), ("3/4 frente-izq", 315, 16))):
        camara(centro, az, el, 24.0, 50)
        vistas.append((nombre, render(os.path.join(carpeta, f"v{i}.png"))))
    total = sum(tris.values())
    notas = [f"Casa de la familia · {total:,} triángulos (límite 14.000) · atlas {TAM_ATLAS}² · {texel:.0f} px/stud".replace(",", "."),
             "Render con los mapas horneados del atlas (lo que verá Roblox). Cristal: material Glass en Studio."]
    hoja_contactos(vistas, os.path.join(RAIZ, f"{NOMBRE}_turnaround.png"), "casa_familia — turnaround", notas)

    # Primeros planos de los detalles que cuentan la historia.
    det = []
    planos = [("Puerta: marcas de altura", (-1.15, -3.8, 2.1), 0, 4, 5.2, 50),
              ("Ventana: dibujo y macetas", (2.5, -3.8, 2.2), 8, 6, 6.5, 50),
              ("Bici y maceta rota", (-5.3, -3.4, 0.7), -60, 18, 5.0, 45),
              ("Caja de juguetes y número", (-3.3, -4.0, 1.6), -18, 18, 4.6, 45),
              ("Tendedero", (6.1, 0.0, 3.2), 110, 12, 9.0, 45),
              ("Buzón y rayuela", (3.4, -5.0, 0.9), 20, 40, 6.0, 45),
              ("Tejado: antena, solar, lucernario", (0.0, -2.0, 7.8), -10, 35, 11.0, 45)]
    for i, (n, c, az, el, d_, lente) in enumerate(planos):
        camara(c, az, el, d_, lente)
        det.append((n, render(os.path.join(carpeta, f"d{i}.png"))))
    # Vista de malla.
    malla = bpy.data.materials.new("vista_malla")
    malla.use_nodes = True
    nt = malla.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    wf = nt.nodes.new("ShaderNodeWireframe")
    wf.use_pixel_size = True
    wf.inputs["Size"].default_value = 0.8
    df = nt.nodes.new("ShaderNodeBsdfDiffuse")
    df.inputs["Color"].default_value = (0.45, 0.47, 0.52, 1)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (0.2, 0.85, 1.0, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wf.outputs["Fac"], mx.inputs["Fac"])
    nt.links.new(df.outputs["BSDF"], mx.inputs[1])
    nt.links.new(em.outputs["Emission"], mx.inputs[2])
    nt.links.new(mx.outputs["Shader"], out.inputs["Surface"])
    bpy.context.scene.view_layers[0].material_override = malla
    camara(centro, 315, 16, 24.0, 50)
    det.append(("Malla", render(os.path.join(carpeta, "malla.png"))))
    bpy.context.scene.view_layers[0].material_override = None
    hoja_contactos(det, os.path.join(RAIZ, f"{NOMBRE}_detalles.png"), "casa_familia — detalles",
                   ["Primeros planos de los detalles de la historia y la malla."])

    datos_json(final, tris, texel, texel_puerta, abiertas)


def datos_json(final, tris, texel, texel_puerta, abiertas):
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    for o in final.values():
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
    tam = mx - mn

    def roblox(v):
        """Posición en Blender (fachada a -Y) -> coordenadas del FBX tras el giro: (X, Y, Z) = (-x, z, y)."""
        return [round(-v[0], 3), round(v[2], 3), round(v[1], 3)]

    xl = (PUERTA["x"][0] + PUERTA["x"][1]) / 2
    datos = {
        "nombre": NOMBRE,
        "descripcion": "Casa de la familia del pueblo: dos plantas, la más grande. Puerta amarilla desconchada con "
                       "marcas de altura, franja azul pintada por los niños, dibujo en la ventana, bici tirada, maceta "
                       "rota, tendedero, caja de juguetes, huerto del padre, rayuela de tiza.",
        "unidades": "studs (1 unidad de Blender = 1 stud)",
        "tamano_studs": {"ancho_x": round(tam.x, 2), "fondo": round(tam.y, 2), "alto": round(tam.z, 2)},
        "tamano_casa_sin_entorno": {"ancho": 10.0, "fondo": 7.5, "alto_cumbrera": round(Z_ALERO + SUBIDA + T_TEJ / COS + 0.075, 2)},
        "triangulos": {**tris, "total": sum(tris.values()), "limite": 14000},
        "mallas": {
            NOMBRE: "Casa y entorno (todo lo fijo). SurfaceAppearance con el atlas.",
            f"{NOMBRE}_Puerta": "Hoja de la puerta, pieza aparte para animar. Pivote en el eje de las bisagras.",
            f"{NOMBRE}_Cristal": "Cristales con grosor. En Studio: Material Glass, Transparency 0.4, color #CFE6EE.",
            f"{NOMBRE}_Neon": f"Bombilla de la lámpara y pantallita del medidor. En Studio: Material Neon, color {NEON}.",
        },
        "texturas": {k: f"{NOMBRE}_{k}.png" for k in ("color", "normal", "roughness", "metalness", "emision")},
        "atlas": {"tamano": TAM_ATLAS, "px_por_stud_casa": round(texel), "px_por_stud_puerta": round(texel_puerta)},
        "surface_appearance": {"ColorMap": f"{NOMBRE}_color.png", "NormalMap": f"{NOMBRE}_normal.png",
                               "RoughnessMap": f"{NOMBRE}_roughness.png", "MetalnessMap": f"{NOMBRE}_metalness.png",
                               "nota_emision": "SurfaceAppearance no usa mapa de emisión: el brillo de las lámparas "
                                               "interiores va pintado en el color; las piezas de neón van en "
                                               f"{NOMBRE}_Neon. emision.png queda para otros motores o para el futuro."},
        "exportacion": {
            "giro_importacion": "Rotado 180° sobre el eje vertical antes de exportar (como MontarRegion.GIRO_IMPORTACION).",
            "ejes_fbx": "Y arriba, -Z delante; Apply Scalings = FBX All; importar con Scale Unit = Stud.",
            "fachada_en_blender": "-Y",
            "coordenadas": "Las posiciones *_fbx son las del archivo: (X, Y, Z) = (-x, z, y) de Blender. "
                           "Sin probar en Studio: si la casa entra mirando al revés, girarla 180° en Y.",
        },
        "puerta": {
            "pivote_blender": [round(c, 3) for c in PIVOTE_PUERTA],
            "pivote_fbx": roblox(PIVOTE_PUERTA),
            "eje_giro": "vertical",
            "abre_hacia": "fuera (bisagras vistas por fuera); ángulo de apertura recomendado 100°",
            "hoja_studs": [round(PUERTA["x"][1] - PUERTA["x"][0] - 0.04, 2), 0.15,
                           round(PUERTA["z"][1] - PUERTA["z"][0] - 0.04, 2)],
            "manijas": "normal a 1,53 studs del suelo de la hoja y la de los niños a 0,92",
        },
        "luces_recomendadas": [
            {"nombre": "LuzPuerta", "tipo": "PointLight", "blender": [xl, Y0 - 0.36, 3.67],
             "fbx": roblox((xl, Y0 - 0.36, 3.67)), "color": NEON, "brightness": 1.5, "range": 12},
            {"nombre": "LuzSalon", "tipo": "PointLight", "blender": [2.5, 0.2, 3.5], "fbx": roblox((2.5, 0.2, 3.5)),
             "color": "#FFD9A0", "brightness": 1, "range": 10, "nota": "dentro, se ve por la ventana grande"},
            {"nombre": "LuzNinos", "tipo": "PointLight", "blender": [0.3, 0.6, 6.4], "fbx": roblox((0.3, 0.6, 6.4)),
             "color": "#FFD9A0", "brightness": 0.8, "range": 8},
        ],
        "escala": "Ojo: con 9 studs de alto y 2 plantas, la puerta mide 3,1 studs (un R6 mide 5). Es la escala pedida "
                  "para el pueblo; si los jugadores tienen que entrar, escalar el modelo entero (×1,6 aprox.).",
        "comprobaciones": {"piezas_con_aristas_abiertas": abiertas or "ninguna (todas las piezas son cerradas)",
                           "normales": "recalculadas hacia fuera en cada pieza"},
        "historia": {
            "puerta": "amarilla, desconchada abajo (patadas, la bici) y junto a las manijas; marcas de altura: "
                      "Leo 4, Mia 6, Leo 7, y una rayita de lápiz muy arriba (papá, en broma); manchita de manos",
            "ventana_baja": "marco con franja azul de niño (irregular, gotas, dedazo), dibujo de la familia con estrellas "
                            "firmado «MIA y LEO», geranio rojo y planta con flor amarilla, cortinas de colores",
            "ventana_alta": "pegatinas de estrellas en el cristal (3D), persiana medio subida, litera detrás",
            "ventana_lateral_1": "marco azul a medio pintar (se aburrieron), rejilla de ventilación debajo",
            "entorno": "bici rosa con flecos tirada contra la pared y manillar girado; maceta de barro rota con la "
                       "tierra derramada; rayuela de tiza con un cohete; felpudo «HOLA»; buzón a franjas con la "
                       "banderita levantada y una carta; huerto del padre (lechugas, tomatera, zanahorias); tendedero "
                       "con camiseta, pantalón, toalla y calcetines; chapa remachada torcida (reparación); cinta "
                       "americana en la bajante",
        },
    }
    with open(os.path.join(RAIZ, f"{NOMBRE}.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
    print("[ok] json")


if __name__ == "__main__":
    main()
