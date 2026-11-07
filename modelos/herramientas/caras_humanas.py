"""
Texturas de la cara del humano (Decals sobre la cara de la cabeza R6) y la rueda de color del editor.

Uso (desde la raíz del repositorio, con Pillow):
    python modelos/herramientas/caras_humanas.py --salida modelos/personaje_humano

Qué sale en <salida>/roblox/texturas (lo que se sube a Roblox con herramientas/subir_modelos --imagenes):
    Ojos_<Id>.png, Cejas_<Id>.png, Nariz_<Id>.png, Boca_<Id>.png   512x512, fondo transparente
    (y en <salida>/roblox/texturas) RuedaColor.png                   rueda de tono (ángulo) y saturación (radio)
    ../../muestra_caras.png                                         todas las opciones sobre una cara de muestra

Cada textura ocupa la cara entera de la cabeza y lleva solo su rasgo en su sitio: el juego pone cuatro Decals en la
cara (ojos, cejas, nariz y boca) y se combinan. Las cejas se dibujan en blanco para teñirlas con el color del pelo
(Decal.Color3); la nariz es una sombra translúcida para que valga con cualquier color de piel.
Se dibuja a 4x y se reduce, para que los bordes salgan suaves.
"""

import argparse
import colorsys
import math
import os

from PIL import Image, ImageDraw

TAM = 512
K = 4  # supermuestreo
LIENZO = TAM * K

# Posiciones (0-1 sobre la textura; 0,0 arriba a la izquierda). La izquierda de la textura es la derecha del personaje.
OJO_X = (0.355, 0.645)
OJO_Y = 0.45
CEJA_Y = 0.335
NARIZ = (0.5, 0.555)
BOCA = (0.5, 0.655)

TINTA = (34, 24, 22, 255)  # casi negro cálido
BLANCO = (255, 255, 255, 255)
ESCLERA = (250, 248, 244, 255)
IRIS = (86, 58, 38, 255)
BOCA_C = (74, 30, 30, 255)
LENGUA = (208, 92, 98, 255)
SOMBRA = (70, 32, 20, 92)


def px(v):
    return v * LIENZO


def elipse(d, cx, cy, rx, ry, color, borde=None, grosor=0.0):
    caja = (px(cx - rx), px(cy - ry), px(cx + rx), px(cy + ry))
    d.ellipse(caja, fill=color, outline=borde, width=int(px(grosor)) if borde else 0)


def arco(d, cx, cy, rx, ry, desde, hasta, color, grosor):
    """Arco con extremos redondeados (ángulos en grados, 0 = derecha, sentido horario como en PIL)."""
    caja = (px(cx - rx), px(cy - ry), px(cx + rx), px(cy + ry))
    g = int(px(grosor))
    d.arc(caja, desde, hasta, fill=color, width=g)
    for a in (desde, hasta):
        ar = math.radians(a)
        # Punto medio del trazo en ese extremo.
        x = cx + (rx - grosor / 2) * math.cos(ar)
        y = cy + (ry - grosor / 2) * math.sin(ar)
        elipse(d, x, y, grosor / 2, grosor / 2, color)


def trazo(d, puntos, color, grosor):
    pts = [(px(x), px(y)) for x, y in puntos]
    d.line(pts, fill=color, width=int(px(grosor)), joint="curve")
    for x, y in puntos:
        elipse(d, x, y, grosor / 2, grosor / 2, color)


def poligono(d, puntos, color):
    d.polygon([(px(x), px(y)) for x, y in puntos], fill=color)


def curva(p0, p1, p2, n=16):
    """Bézier cuadrática."""
    out = []
    for i in range(n + 1):
        t = i / n
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]
        out.append((x, y))
    return out


# ---------------------------------------------------------------------------------------------------------------
# Ojos (se dibuja cada ojo; s = -1 para el de la izquierda de la textura, 1 para el de la derecha)
# ---------------------------------------------------------------------------------------------------------------


def ojos_redondos(d, cx, cy, s):
    elipse(d, cx, cy, 0.034, 0.05, TINTA)
    elipse(d, cx - 0.011, cy - 0.018, 0.011, 0.013, BLANCO)


def ojos_grandes(d, cx, cy, s):
    elipse(d, cx, cy, 0.058, 0.064, ESCLERA, TINTA, 0.009)
    elipse(d, cx + s * -0.004, cy + 0.006, 0.036, 0.042, IRIS)
    elipse(d, cx + s * -0.004, cy + 0.008, 0.02, 0.024, TINTA)
    elipse(d, cx - 0.016, cy - 0.012, 0.011, 0.011, BLANCO)


def ojos_almendrados(d, cx, cy, s):
    sup = curva((cx - 0.065, cy + 0.006), (cx, cy - 0.06), (cx + 0.065, cy + 0.006))
    inf = curva((cx + 0.065, cy + 0.006), (cx, cy + 0.045), (cx - 0.065, cy + 0.006))
    poligono(d, sup + inf, ESCLERA)
    elipse(d, cx, cy, 0.03, 0.034, IRIS)
    elipse(d, cx, cy + 0.002, 0.016, 0.018, TINTA)
    elipse(d, cx - 0.012, cy - 0.012, 0.008, 0.008, BLANCO)
    trazo(d, sup, TINTA, 0.012)
    # Pestaña hacia fuera.
    ext = cx + s * 0.065
    trazo(d, [(ext, cy + 0.004), (ext + s * 0.018, cy - 0.016)], TINTA, 0.01)


def ojos_serios(d, cx, cy, s):
    # Párpado a media altura: solo se ve la mitad de abajo del ojo.
    capa = Image.new("RGBA", (LIENZO, LIENZO), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    elipse(dc, cx, cy, 0.05, 0.05, ESCLERA)
    elipse(dc, cx, cy + 0.006, 0.03, 0.034, IRIS)
    elipse(dc, cx, cy + 0.008, 0.016, 0.018, TINTA)
    dc.rectangle((0, 0, LIENZO, px(cy - 0.008)), fill=(0, 0, 0, 0))
    d._image.alpha_composite(capa)
    trazo(d, [(cx - 0.06, cy - 0.006 + s * 0.006), (cx + 0.06, cy - 0.006 - s * 0.006)], TINTA, 0.014)


def ojos_alegres(d, cx, cy, s):
    arco(d, cx, cy + 0.02, 0.045, 0.04, 200, 340, TINTA, 0.016)


def ojos_brillantes(d, cx, cy, s):
    elipse(d, cx, cy, 0.04, 0.062, TINTA)
    elipse(d, cx, cy + 0.02, 0.028, 0.03, (70, 120, 190, 255))
    elipse(d, cx - 0.012, cy - 0.022, 0.014, 0.017, BLANCO)
    elipse(d, cx + 0.014, cy + 0.024, 0.007, 0.007, BLANCO)


def ojos_cansados(d, cx, cy, s):
    elipse(d, cx, cy, 0.03, 0.04, TINTA)
    elipse(d, cx - 0.009, cy - 0.013, 0.009, 0.01, BLANCO)
    arco(d, cx, cy + 0.03, 0.04, 0.03, 30, 150, SOMBRA, 0.01)


OJOS = [("Redondos", ojos_redondos), ("Grandes", ojos_grandes), ("Almendrados", ojos_almendrados),
        ("Serios", ojos_serios), ("Alegres", ojos_alegres), ("Brillantes", ojos_brillantes),
        ("Cansados", ojos_cansados)]


# ---------------------------------------------------------------------------------------------------------------
# Cejas (blancas: se tiñen con el color del pelo)
# ---------------------------------------------------------------------------------------------------------------


def cejas_rectas(d, cx, cy, s):
    trazo(d, [(cx - 0.05, cy + 0.004), (cx + 0.05, cy - 0.004 * s * 0)], BLANCO, 0.022)


def cejas_arqueadas(d, cx, cy, s):
    trazo(d, curva((cx - 0.055, cy + 0.012), (cx, cy - 0.03), (cx + 0.055, cy + 0.012)), BLANCO, 0.02)


def cejas_gruesas(d, cx, cy, s):
    interior = cx - s * 0.055
    exterior = cx + s * 0.055
    poligono(d, [(interior, cy - 0.016), (exterior, cy - 0.02), (exterior, cy + 0.008), (interior, cy + 0.018)], BLANCO)
    elipse(d, interior, cy + 0.001, 0.017, 0.017, BLANCO)
    elipse(d, exterior, cy - 0.006, 0.014, 0.014, BLANCO)


def cejas_finas(d, cx, cy, s):
    trazo(d, curva((cx - 0.05, cy + 0.008), (cx, cy - 0.018), (cx + 0.05, cy + 0.008)), BLANCO, 0.01)


def cejas_enfadadas(d, cx, cy, s):
    interior = cx - s * 0.05
    exterior = cx + s * 0.05
    trazo(d, [(exterior, cy - 0.018), (interior, cy + 0.02)], BLANCO, 0.022)


def cejas_preocupadas(d, cx, cy, s):
    interior = cx - s * 0.05
    exterior = cx + s * 0.05
    trazo(d, [(exterior, cy + 0.012), (interior, cy - 0.02)], BLANCO, 0.02)


CEJAS = [("Rectas", cejas_rectas), ("Arqueadas", cejas_arqueadas), ("Gruesas", cejas_gruesas),
         ("Finas", cejas_finas), ("Enfadadas", cejas_enfadadas), ("Preocupadas", cejas_preocupadas)]


# ---------------------------------------------------------------------------------------------------------------
# Nariz (sombra translúcida) y boca
# ---------------------------------------------------------------------------------------------------------------


def nariz_punto(d, cx, cy):
    elipse(d, cx, cy, 0.016, 0.012, SOMBRA)


def nariz_boton(d, cx, cy):
    arco(d, cx, cy - 0.006, 0.026, 0.02, 20, 160, SOMBRA, 0.011)


def nariz_recta(d, cx, cy):
    trazo(d, [(cx + 0.006, cy - 0.06), (cx + 0.016, cy - 0.004), (cx - 0.012, cy + 0.008)], SOMBRA, 0.011)


def nariz_ancha(d, cx, cy):
    arco(d, cx, cy - 0.01, 0.04, 0.026, 15, 165, SOMBRA, 0.01)
    elipse(d, cx - 0.018, cy + 0.006, 0.009, 0.006, SOMBRA)
    elipse(d, cx + 0.018, cy + 0.006, 0.009, 0.006, SOMBRA)


NARICES = [("Punto", nariz_punto), ("Boton", nariz_boton), ("Recta", nariz_recta), ("Ancha", nariz_ancha)]


def boca_sonrisa(d, cx, cy):
    arco(d, cx, cy - 0.03, 0.075, 0.05, 25, 155, BOCA_C, 0.016)


def boca_amplia(d, cx, cy):
    sup = [(cx - 0.085, cy - 0.012), (cx + 0.085, cy - 0.012)]
    inf = curva((cx + 0.085, cy - 0.012), (cx, cy + 0.11), (cx - 0.085, cy - 0.012), n=24)
    poligono(d, sup + inf, BOCA_C)
    # Dientes de arriba y lengua.
    poligono(d, [(cx - 0.07, cy - 0.008), (cx + 0.07, cy - 0.008), (cx + 0.06, cy + 0.012), (cx - 0.06, cy + 0.012)],
             BLANCO)
    elipse(d, cx, cy + 0.04, 0.035, 0.014, LENGUA)


def boca_neutra(d, cx, cy):
    trazo(d, [(cx - 0.04, cy), (cx + 0.04, cy)], BOCA_C, 0.014)


def boca_ladeada(d, cx, cy):
    trazo(d, curva((cx - 0.05, cy + 0.004), (cx + 0.01, cy + 0.02), (cx + 0.06, cy - 0.018)), BOCA_C, 0.015)


def boca_seria(d, cx, cy):
    arco(d, cx, cy + 0.035, 0.055, 0.03, 205, 335, BOCA_C, 0.014)


def boca_sorpresa(d, cx, cy):
    elipse(d, cx, cy + 0.006, 0.026, 0.034, BOCA_C)
    elipse(d, cx, cy + 0.02, 0.015, 0.012, LENGUA)


BOCAS = [("Sonrisa", boca_sonrisa), ("Amplia", boca_amplia), ("Neutra", boca_neutra), ("Ladeada", boca_ladeada),
         ("Seria", boca_seria), ("Sorpresa", boca_sorpresa)]


# ---------------------------------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------------------------------
# Rasgos nuevos
# ---------------------------------------------------------------------------------------------------------------

NEON = (77, 232, 255, 255)
AMARILLO = (232, 200, 60, 255)


def estrella(d, cx, cy, r, color):
    pts = []
    for i in range(10):
        a = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    poligono(d, pts, color)


def ojos_pequenos(d, cx, cy, s):
    elipse(d, cx, cy, 0.017, 0.024, TINTA)


def ojos_rasgados(d, cx, cy, s):
    ex, ix = cx + s * 0.07, cx - s * 0.07
    sup = curva((ix, cy + 0.015), (cx, cy - 0.04), (ex, cy - 0.025))
    inf = curva((ex, cy - 0.025), (cx, cy + 0.03), (ix, cy + 0.015))
    poligono(d, sup + inf, ESCLERA)
    elipse(d, cx, cy - 0.002, 0.022, 0.025, IRIS)
    elipse(d, cx, cy - 0.002, 0.012, 0.015, TINTA)
    trazo(d, sup, TINTA, 0.011)


def ojos_guino(d, cx, cy, s):
    if s < 0:
        arco(d, cx, cy + 0.02, 0.04, 0.035, 200, 340, TINTA, 0.015)
    else:
        ojos_redondos(d, cx, cy, s)


def ojos_estrellas(d, cx, cy, s):
    elipse(d, cx, cy, 0.055, 0.06, (250, 248, 244, 255), TINTA, 0.008)
    estrella(d, cx, cy + 0.003, 0.045, AMARILLO)
    elipse(d, cx - 0.012, cy - 0.012, 0.009, 0.009, BLANCO)


def ojos_gato(d, cx, cy, s):
    elipse(d, cx, cy, 0.046, 0.052, AMARILLO, TINTA, 0.008)
    elipse(d, cx, cy, 0.009, 0.044, TINTA)
    elipse(d, cx - 0.014, cy - 0.016, 0.008, 0.008, BLANCO)


def ojos_ciber(d, cx, cy, s):
    elipse(d, cx, cy, 0.052, 0.052, NEON)
    elipse(d, cx, cy, 0.038, 0.038, (12, 20, 30, 255))
    elipse(d, cx, cy, 0.017, 0.017, NEON)


def ojos_dormidos(d, cx, cy, s):
    arco(d, cx, cy - 0.025, 0.045, 0.035, 20, 160, TINTA, 0.014)
    trazo(d, [(cx + s * 0.05, cy + 0.01), (cx + s * 0.065, cy + 0.025)], TINTA, 0.008)


OJOS += [("Pequenos", ojos_pequenos), ("Rasgados", ojos_rasgados), ("Guino", ojos_guino),
         ("Estrellas", ojos_estrellas), ("Gato", ojos_gato), ("Ciber", ojos_ciber), ("Dormidos", ojos_dormidos)]


def cejas_alzada(d, cx, cy, s):
    if s < 0:
        trazo(d, [(cx - 0.05, cy + 0.004), (cx + 0.05, cy)], BLANCO, 0.022)
    else:
        trazo(d, curva((cx - 0.055, cy - 0.01), (cx, cy - 0.065), (cx + 0.055, cy - 0.035)), BLANCO, 0.022)


def cejas_unidas(d, cx, cy, s):
    interior = cx - s * 0.145
    exterior = cx + s * 0.05
    trazo(d, curva((interior, cy + 0.005), ((interior + exterior) / 2, cy - 0.022), (exterior, cy)), BLANCO, 0.026)


def cejas_cortadas(d, cx, cy, s):
    trazo(d, [(cx - 0.055, cy + 0.006), (cx - 0.012, cy)], BLANCO, 0.022)
    trazo(d, [(cx + 0.012, cy), (cx + 0.055, cy - 0.004)], BLANCO, 0.022)


def cejas_anchas(d, cx, cy, s):
    trazo(d, curva((cx - 0.06, cy + 0.012), (cx, cy - 0.035), (cx + 0.06, cy + 0.012)), BLANCO, 0.034)


def cejas_puntiagudas(d, cx, cy, s):
    trazo(d, [(cx - 0.055, cy + 0.015), (cx - 0.005, cy - 0.03), (cx + 0.055, cy + 0.012)], BLANCO, 0.018)


def cejas_caidas(d, cx, cy, s):
    interior = cx - s * 0.05
    exterior = cx + s * 0.055
    trazo(d, [(interior, cy - 0.014), (exterior, cy + 0.022)], BLANCO, 0.014)


CEJAS += [("Alzada", cejas_alzada), ("Unidas", cejas_unidas), ("Cortadas", cejas_cortadas), ("Anchas", cejas_anchas),
          ("Puntiagudas", cejas_puntiagudas), ("Caidas", cejas_caidas)]


def nariz_aguilena(d, cx, cy):
    trazo(d, [(cx + 0.004, cy - 0.06), (cx + 0.022, cy - 0.01), (cx + 0.006, cy + 0.014), (cx - 0.022, cy + 0.01)], SOMBRA, 0.011)


def nariz_respingona(d, cx, cy):
    arco(d, cx, cy + 0.004, 0.022, 0.015, 200, 340, SOMBRA, 0.01)
    elipse(d, cx - 0.012, cy + 0.012, 0.005, 0.004, SOMBRA)
    elipse(d, cx + 0.012, cy + 0.012, 0.005, 0.004, SOMBRA)


def nariz_chata(d, cx, cy):
    elipse(d, cx - 0.022, cy, 0.012, 0.008, SOMBRA)
    elipse(d, cx + 0.022, cy, 0.012, 0.008, SOMBRA)
    trazo(d, [(cx - 0.04, cy - 0.018), (cx + 0.04, cy - 0.018)], SOMBRA, 0.006)


def nariz_grande(d, cx, cy):
    elipse(d, cx, cy - 0.006, 0.034, 0.03, (70, 32, 20, 40))
    arco(d, cx, cy - 0.008, 0.034, 0.028, 20, 160, SOMBRA, 0.01)
    elipse(d, cx - 0.018, cy + 0.004, 0.008, 0.006, SOMBRA)
    elipse(d, cx + 0.018, cy + 0.004, 0.008, 0.006, SOMBRA)


NARICES += [("Aguilena", nariz_aguilena), ("Respingona", nariz_respingona), ("Chata", nariz_chata),
            ("Grande", nariz_grande)]


def boca_dientes(d, cx, cy):
    cuerpo = [(cx - 0.08, cy - 0.02), (cx + 0.08, cy - 0.02), (cx + 0.07, cy + 0.03), (cx - 0.07, cy + 0.03)]
    poligono(d, cuerpo, BLANCO)
    trazo(d, cuerpo + [cuerpo[0]], BOCA_C, 0.008)
    trazo(d, [(cx - 0.08, cy + 0.005), (cx + 0.08, cy + 0.005)], BOCA_C, 0.006)
    for i in (-0.04, 0.0, 0.04):
        trazo(d, [(cx + i, cy - 0.02), (cx + i, cy + 0.03)], BOCA_C, 0.005)


def boca_gato(d, cx, cy):
    trazo(d, curva((cx - 0.07, cy - 0.01), (cx - 0.035, cy + 0.045), (cx, cy)) +
          curva((cx, cy), (cx + 0.035, cy + 0.045), (cx + 0.07, cy - 0.01)), BOCA_C, 0.012)


def boca_lengua(d, cx, cy):
    elipse(d, cx + 0.012, cy + 0.03, 0.03, 0.045, LENGUA)
    trazo(d, [(cx + 0.012, cy + 0.01), (cx + 0.012, cy + 0.06)], (150, 60, 70, 255), 0.005)
    arco(d, cx, cy - 0.03, 0.075, 0.05, 25, 155, BOCA_C, 0.016)


def boca_mueca(d, cx, cy):
    trazo(d, curva((cx - 0.07, cy), (cx - 0.035, cy + 0.035), (cx, cy)) +
          curva((cx, cy), (cx + 0.035, cy - 0.035), (cx + 0.07, cy)), BOCA_C, 0.013)


def boca_triste(d, cx, cy):
    arco(d, cx, cy + 0.06, 0.085, 0.06, 208, 332, BOCA_C, 0.016)


def boca_labios(d, cx, cy):
    labios = (205, 85, 105, 255)
    poligono(d, curva((cx - 0.07, cy), (cx, cy - 0.05), (cx + 0.07, cy)) + curva((cx + 0.07, cy), (cx, cy + 0.06), (cx - 0.07, cy)), labios)
    trazo(d, [(cx - 0.07, cy), (cx + 0.07, cy)], (120, 40, 60, 255), 0.008)


BOCAS += [("Dientes", boca_dientes), ("Gato", boca_gato), ("Lengua", boca_lengua), ("Mueca", boca_mueca),
          ("Triste", boca_triste), ("Labios", boca_labios)]


# ---------------------------------------------------------------------------------------------------------------
# Cicatrices (en la cara) y tatuajes (en los brazos)
# ---------------------------------------------------------------------------------------------------------------

CICATRIZ = (214, 150, 140, 235)
CICATRIZ_SOMBRA = (120, 60, 56, 170)


def cicatriz_linea(d, pts, grosor=0.012, puntos=0):
    trazo(d, pts, CICATRIZ_SOMBRA, grosor + 0.006)
    trazo(d, pts, CICATRIZ, grosor)
    for i in range(puntos):
        t = (i + 0.5) / puntos
        x = pts[0][0] + (pts[-1][0] - pts[0][0]) * t
        y = pts[0][1] + (pts[-1][1] - pts[0][1]) * t
        dx, dy = pts[-1][1] - pts[0][1], -(pts[-1][0] - pts[0][0])
        n = math.hypot(dx, dy) or 1
        trazo(d, [(x - dx / n * 0.02, y - dy / n * 0.02), (x + dx / n * 0.02, y + dy / n * 0.02)], CICATRIZ_SOMBRA, 0.006)


def cic_ceja(d):
    cicatriz_linea(d, [(0.62, 0.27), (0.68, 0.4)], puntos=3)


def cic_mejilla(d):
    for k in range(3):
        cicatriz_linea(d, [(0.25 + k * 0.03, 0.52 + k * 0.02), (0.33 + k * 0.03, 0.66 + k * 0.02)], 0.01)


def cic_cruz(d):
    cicatriz_linea(d, [(0.66, 0.52), (0.78, 0.66)], puntos=3)
    cicatriz_linea(d, [(0.78, 0.52), (0.66, 0.66)], puntos=3)


def cic_ojo(d):
    for k in range(3):
        cicatriz_linea(d, [(0.27 + k * 0.035, 0.32), (0.33 + k * 0.035, 0.6)], 0.011)


def cic_labio(d):
    cicatriz_linea(d, [(0.585, 0.6), (0.6, 0.72)], puntos=2)


def cic_frente(d):
    cicatriz_linea(d, [(0.3, 0.2), (0.7, 0.22)], puntos=5)


def cic_quemadura(d):
    pts = [(0.66, 0.5), (0.74, 0.47), (0.82, 0.53), (0.8, 0.63), (0.72, 0.68), (0.64, 0.62), (0.62, 0.55)]
    poligono(d, pts, (190, 80, 60, 150))
    poligono(d, [(0.69, 0.53), (0.76, 0.52), (0.77, 0.6), (0.7, 0.62)], (160, 50, 40, 150))


def cic_sutura(d):
    cicatriz_linea(d, [(0.22, 0.56), (0.4, 0.62)], puntos=6)


CICATRICES = [("Ceja", cic_ceja), ("Mejilla", cic_mejilla), ("Cruz", cic_cruz), ("Ojo", cic_ojo), ("Labio", cic_labio),
              ("Frente", cic_frente), ("Quemadura", cic_quemadura), ("Sutura", cic_sutura)]

# Tatuajes: textura de la cara de un brazo (1 de ancho por 2 de alto), de ahí el lienzo de 1:2.
AK = 4
AW, AH = 256 * AK, 512 * AK
TINTA_T = (16, 20, 26, 235)
BLANCO_T = (232, 238, 250, 255)


def nuevo_brazo():
    img = Image.new("RGBA", (AW, AH), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def linea_b(d, pts, color, grosor):
    p = [(x * AW, y * AH) for x, y in pts]
    d.line(p, fill=color, width=int(grosor * AW), joint="curve")
    r = grosor * AW / 2
    for x, y in p:
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def poli_b(d, pts, color):
    d.polygon([(x * AW, y * AH) for x, y in pts], fill=color)


def punto_b(d, x, y, r, color):
    d.ellipse(((x - r) * AW, (y * AH) - r * AW, (x + r) * AW, (y * AH) + r * AW), fill=color)


def tat_tribal(d):
    for y0 in (0.2, 0.44, 0.68):
        pts = [(0.12 + 0.76 * i / 8, y0 + (0.05 if i % 2 else 0)) for i in range(9)]
        linea_b(d, pts, TINTA_T, 0.07)
    linea_b(d, [(0.5, 0.1), (0.5, 0.9)], TINTA_T, 0.05)
    for y in (0.3, 0.55, 0.8):
        poli_b(d, [(0.5, y - 0.04), (0.58, y), (0.5, y + 0.04), (0.42, y)], TINTA_T)


def tat_banda(d):
    for y in (0.3, 0.37, 0.62):
        linea_b(d, [(0.05, y), (0.95, y)], TINTA_T, 0.07 if y == 0.37 else 0.04)
    for i in range(7):
        punto_b(d, 0.12 + i * 0.126, 0.5, 0.035, TINTA_T)


def tat_circuitos(d):
    linea_b(d, [(0.5, 0.08), (0.5, 0.92)], NEON, 0.03)
    for y, x in ((0.2, 0.2), (0.35, 0.8), (0.5, 0.25), (0.66, 0.75), (0.82, 0.3)):
        linea_b(d, [(0.5, y), (x, y), (x, y + 0.06)], NEON, 0.03)
        punto_b(d, x, y + 0.06, 0.04, NEON)
    punto_b(d, 0.5, 0.08, 0.05, NEON)


def tat_constelacion(d):
    estrellas = [(0.25, 0.15), (0.6, 0.25), (0.4, 0.4), (0.78, 0.5), (0.3, 0.62), (0.62, 0.76), (0.45, 0.9)]
    linea_b(d, estrellas, (232, 238, 250, 170), 0.015)
    for x, y in estrellas:
        punto_b(d, x, y, 0.04, BLANCO_T)


def tat_serpiente(d):
    pts = [(0.5 + 0.28 * math.sin(i * 0.9), 0.08 + 0.84 * i / 14) for i in range(15)]
    linea_b(d, pts, TINTA_T, 0.09)
    x, y = pts[-1]
    poli_b(d, [(x - 0.08, y), (x + 0.08, y), (x, y + 0.07)], TINTA_T)
    punto_b(d, 0.5, 0.08, 0.04, TINTA_T)


def tat_espinas(d):
    for i in range(8):
        y = 0.1 + i * 0.1
        poli_b(d, [(0.04, y), (0.4, y + 0.03), (0.04, y + 0.06)], TINTA_T)
        poli_b(d, [(0.96, y + 0.05), (0.6, y + 0.08), (0.96, y + 0.11)], TINTA_T)
    linea_b(d, [(0.5, 0.08), (0.5, 0.95)], TINTA_T, 0.04)


def tat_runas(d):
    for k in range(4):
        y = 0.12 + k * 0.22
        linea_b(d, [(0.5, y), (0.5, y + 0.15)], TINTA_T, 0.045)
        if k % 2 == 0:
            linea_b(d, [(0.3, y + 0.03), (0.5, y + 0.07), (0.7, y + 0.03)], TINTA_T, 0.04)
        else:
            linea_b(d, [(0.3, y + 0.14), (0.5, y + 0.06), (0.7, y + 0.14)], TINTA_T, 0.04)
        punto_b(d, 0.5, y + 0.19 * 0.97, 0.025, TINTA_T)


def tat_rayas(d):
    for i in range(6):
        y = 0.05 + i * 0.16
        linea_b(d, [(0.05, y + 0.2), (0.95, y)], TINTA_T, 0.05)


TATUAJES = [("Tribal", tat_tribal), ("Banda", tat_banda), ("Circuitos", tat_circuitos),
            ("Constelacion", tat_constelacion), ("Serpiente", tat_serpiente), ("Espinas", tat_espinas),
            ("Runas", tat_runas), ("Rayas", tat_rayas)]


def nueva():
    img = Image.new("RGBA", (LIENZO, LIENZO), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def guardar(img, ruta, tam=None):
    img.resize(tam or (TAM, TAM), Image.LANCZOS).save(ruta)
    return ruta


def rueda_color(ruta, tam=512):
    """Tono por ángulo (0 = arriba, sentido horario) y saturación por distancia al centro; brillo al máximo."""
    k = 2
    n = tam * k
    img = Image.new("RGBA", (n, n), (0, 0, 0, 0))
    pix = img.load()
    r = n / 2
    for y in range(n):
        for x in range(n):
            dx, dy = x + 0.5 - r, y + 0.5 - r
            dist = math.hypot(dx, dy) / r
            if dist <= 1.0:
                tono = (math.degrees(math.atan2(dx, -dy)) % 360) / 360
                rr, gg, bb = colorsys.hsv_to_rgb(tono, dist, 1.0)
                pix[x, y] = (int(rr * 255 + 0.5), int(gg * 255 + 0.5), int(bb * 255 + 0.5), 255)
    img.resize((tam, tam), Image.LANCZOS).save(ruta)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()
    carpeta = os.path.join(os.path.abspath(args.salida), "roblox", "texturas")
    os.makedirs(carpeta, exist_ok=True)
    hechas = {}
    for nombre, f in OJOS:
        img, d = nueva()
        for s, x in ((-1, OJO_X[0]), (1, OJO_X[1])):
            f(d, x, OJO_Y, s)
        hechas[("Ojos", nombre)] = guardar(img, os.path.join(carpeta, f"Ojos_{nombre}.png"))
    for nombre, f in CEJAS:
        img, d = nueva()
        for s, x in ((-1, OJO_X[0]), (1, OJO_X[1])):
            f(d, x, CEJA_Y, s)
        hechas[("Cejas", nombre)] = guardar(img, os.path.join(carpeta, f"Cejas_{nombre}.png"))
    for nombre, f in NARICES:
        img, d = nueva()
        f(d, *NARIZ)
        hechas[("Nariz", nombre)] = guardar(img, os.path.join(carpeta, f"Nariz_{nombre}.png"))
    for nombre, f in BOCAS:
        img, d = nueva()
        f(d, *BOCA)
        hechas[("Boca", nombre)] = guardar(img, os.path.join(carpeta, f"Boca_{nombre}.png"))
    rueda_color(os.path.join(carpeta, "RuedaColor.png"))
    cicatrices = {}
    for nombre, f in CICATRICES:
        img, d = nueva()
        f(d)
        cicatrices[nombre] = guardar(img, os.path.join(carpeta, f"Cicatriz_{nombre}.png"))
    tatuajes = {}
    for nombre, f in TATUAJES:
        img, d = nuevo_brazo()
        f(d)
        tatuajes[nombre] = guardar(img, os.path.join(carpeta, f"Tatuaje_{nombre}.png"), (256, 512))

    # Hoja de muestra: cada opción sobre una cara de piel media, con el resto de rasgos por defecto.
    piel = (217, 163, 122, 255)
    pelo = (74, 47, 30, 255)
    defecto = {"Ojos": "Redondos", "Cejas": "Rectas", "Nariz": "Punto", "Boca": "Sonrisa"}
    celdas = []
    for (cat, nombre) in hechas:
        capas = dict(defecto)
        capas[cat] = nombre
        cara = Image.new("RGBA", (TAM, TAM), piel)
        for c2 in ("Cejas", "Ojos", "Nariz", "Boca"):
            t = Image.open(hechas[(c2, capas[c2])])
            if c2 == "Cejas":
                tinte = Image.new("RGBA", t.size, pelo)
                tinte.putalpha(t.getchannel("A"))
                t = tinte
            cara.alpha_composite(t)
        celdas.append((f"{cat} {nombre}", cara.resize((200, 200), Image.LANCZOS)))
    for nombre, ruta in cicatrices.items():
        cara = Image.new("RGBA", (TAM, TAM), piel)
        for c2 in ("Cejas", "Ojos", "Nariz", "Boca"):
            t = Image.open(hechas[(c2, defecto[c2])])
            if c2 == "Cejas":
                tinte = Image.new("RGBA", t.size, pelo)
                tinte.putalpha(t.getchannel("A"))
                t = tinte
            cara.alpha_composite(t)
        cara.alpha_composite(Image.open(ruta))
        celdas.append((f"Cicatriz {nombre}", cara.resize((200, 200), Image.LANCZOS)))
    columnas = 8
    filas = math.ceil(len(celdas) / columnas)
    hoja = Image.new("RGB", (columnas * 200, filas * 224), (16, 18, 24))
    dh = ImageDraw.Draw(hoja)
    for i, (txt, im) in enumerate(celdas):
        x, y = (i % columnas) * 200, (i // columnas) * 224
        hoja.paste(im, (x, y + 22))
        dh.text((x + 6, y + 4), txt, fill=(230, 235, 245))
    hoja.save(os.path.join(os.path.abspath(args.salida), "muestra_caras.png"))
    # Hoja de tatuajes sobre un brazo de piel.
    hoja_t = Image.new("RGB", (len(tatuajes) * 130, 290), (16, 18, 24))
    dt = ImageDraw.Draw(hoja_t)
    for i, (nombre, ruta) in enumerate(tatuajes.items()):
        brazo = Image.new("RGBA", (256, 512), piel)
        brazo.alpha_composite(Image.open(ruta))
        hoja_t.paste(brazo.resize((128, 256), Image.LANCZOS), (i * 130 + 1, 30))
        dt.text((i * 130 + 6, 8), nombre, fill=(230, 235, 245))
    hoja_t.save(os.path.join(os.path.abspath(args.salida), "muestra_tatuajes.png"))
    print("[ok]", len(hechas) + len(cicatrices) + len(tatuajes), "texturas en", carpeta)


if __name__ == "__main__":
    main()
