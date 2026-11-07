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


def nueva():
    img = Image.new("RGBA", (LIENZO, LIENZO), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def guardar(img, ruta):
    img.resize((TAM, TAM), Image.LANCZOS).save(ruta)
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
    columnas = 8
    filas = math.ceil(len(celdas) / columnas)
    hoja = Image.new("RGB", (columnas * 200, filas * 224), (16, 18, 24))
    dh = ImageDraw.Draw(hoja)
    for i, (txt, im) in enumerate(celdas):
        x, y = (i % columnas) * 200, (i // columnas) * 224
        hoja.paste(im, (x, y + 22))
        dh.text((x + 6, y + 4), txt, fill=(230, 235, 245))
    hoja.save(os.path.join(os.path.abspath(args.salida), "muestra_caras.png"))
    print("[ok]", len(hechas), "texturas en", carpeta)


if __name__ == "__main__":
    main()
