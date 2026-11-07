"""
Texturas del editor de monstruos (Decals): ojos, bocas y marcas luminosas del torso.

Uso (desde la raíz del repositorio, con Pillow):
    python modelos/herramientas/caras_monstruo.py --salida modelos/personaje_monstruo

Sale en <salida>/roblox/texturas:
    Ojos_<Id>.png    en BLANCO con brillo: el juego los tiñe con el color de ojos que elige el jugador (Decal.Color3)
    Boca_<Id>.png    bocas oscuras con dientes
    Marcas_<Id>.png  líneas blancas (se tiñen con el color de detalles) para el pecho
    muestra_monstruo.png   todas las opciones sobre una cara y un torso de muestra
Misma colocación que las caras humanas (ojos a 0,45 de alto, boca a 0,655), para que se vea igual en la misma cabeza.
"""

import argparse
import math
import os

from PIL import Image, ImageDraw, ImageFilter

import caras_humanas as h

TAM = h.TAM
LIENZO = h.LIENZO
BLANCO = (255, 255, 255, 255)
NEGRO = (14, 8, 10, 255)
DIENTE = (232, 226, 206, 255)
ROJO_BOCA = (70, 14, 18, 255)


def nueva():
    img = Image.new("RGBA", (LIENZO, LIENZO), (0, 0, 0, 0))
    return img, ImageDraw.Draw(img)


def brillo(img, radio=14):
    """Halo suave alrededor de lo dibujado (se ve como luz)."""
    halo = img.filter(ImageFilter.GaussianBlur(radio * h.K / 2))
    r, g, b, a = halo.split()
    halo = Image.merge("RGBA", (r, g, b, a.point(lambda v: int(v * 0.8))))
    halo.alpha_composite(img)
    return halo


OJO_X = h.OJO_X
OJO_Y = h.OJO_Y


# ---- Ojos ----

def ojos_dos(d):
    for x in OJO_X:
        h.elipse(d, x, OJO_Y, 0.04, 0.05, BLANCO)


def ojos_tres(d):
    for x in OJO_X:
        h.elipse(d, x, OJO_Y + 0.02, 0.036, 0.045, BLANCO)
    h.elipse(d, 0.5, OJO_Y - 0.12, 0.028, 0.034, BLANCO)


def ojos_uno(d):
    h.elipse(d, 0.5, OJO_Y, 0.1, 0.085, BLANCO)
    h.elipse(d, 0.5, OJO_Y, 0.03, 0.07, NEGRO)


def ojos_cuatro(d):
    for x in OJO_X:
        h.elipse(d, x, OJO_Y - 0.05, 0.03, 0.036, BLANCO)
        h.elipse(d, x, OJO_Y + 0.05, 0.03, 0.036, BLANCO)


def ojos_rendija(d):
    for s, x in ((-1, OJO_X[0]), (1, OJO_X[1])):
        h.poligono(d, [(x - s * 0.06, OJO_Y + 0.025), (x + s * 0.07, OJO_Y - 0.03), (x + s * 0.07, OJO_Y - 0.012),
                       (x - s * 0.06, OJO_Y + 0.045)], BLANCO)


def ojos_cuencas(d):
    for x in OJO_X:
        h.elipse(d, x, OJO_Y, 0.052, 0.06, NEGRO)
        h.elipse(d, x, OJO_Y + 0.006, 0.012, 0.014, BLANCO)


def ojos_grandes(d):
    for x in OJO_X:
        h.elipse(d, x, OJO_Y, 0.06, 0.075, BLANCO)
        h.elipse(d, x, OJO_Y, 0.02, 0.05, NEGRO)


def ojos_multiples(d):
    for k, (dx, dy) in enumerate(((-0.17, -0.02), (-0.08, 0.06), (0.0, -0.06), (0.08, 0.06), (0.17, -0.02), (0.0, 0.07))):
        h.elipse(d, 0.5 + dx, OJO_Y + dy, 0.024, 0.03, BLANCO)


OJOS = [("Dos", ojos_dos), ("Tres", ojos_tres), ("Uno", ojos_uno), ("Cuatro", ojos_cuatro), ("Rendija", ojos_rendija),
        ("Cuencas", ojos_cuencas), ("Grandes", ojos_grandes), ("Multiples", ojos_multiples)]


# ---- Bocas ----

def boca_cerrada(d):
    h.trazo(d, [(0.4, 0.66), (0.6, 0.66)], NEGRO, 0.016)


def boca_colmillos(d):
    h.elipse(d, 0.5, 0.665, 0.1, 0.045, ROJO_BOCA)
    for x in (0.43, 0.57):
        h.poligono(d, [(x - 0.016, 0.645), (x + 0.016, 0.645), (x, 0.7)], DIENTE)
        h.poligono(d, [(x - 0.016, 0.69), (x + 0.016, 0.69), (x, 0.64)], DIENTE)


def boca_vertical(d):
    h.elipse(d, 0.5, 0.68, 0.034, 0.13, ROJO_BOCA)
    for i in range(6):
        y = 0.58 + i * 0.04
        h.poligono(d, [(0.466, y), (0.5, y + 0.014), (0.466, y + 0.028)], DIENTE)
        h.poligono(d, [(0.534, y + 0.02), (0.5, y + 0.034), (0.534, y + 0.048)], DIENTE)


def boca_sonrisa_rota(d):
    pts = [(0.3, 0.64), (0.36, 0.69), (0.42, 0.665), (0.5, 0.7), (0.58, 0.665), (0.64, 0.69), (0.7, 0.64)]
    h.trazo(d, pts, NEGRO, 0.016)
    for i in range(1, 6):
        x, y = pts[i]
        h.poligono(d, [(x - 0.012, y - 0.004), (x + 0.012, y - 0.004), (x, y + 0.03)], DIENTE)


def boca_abierta(d):
    h.elipse(d, 0.5, 0.68, 0.085, 0.085, ROJO_BOCA)
    for k in range(10):
        a = 2 * math.pi * k / 10
        x, y = 0.5 + 0.085 * math.cos(a), 0.68 + 0.085 * math.sin(a)
        h.poligono(d, [(x - 0.01, y - 0.01), (x + 0.01, y - 0.01), (0.5 + 0.055 * math.cos(a), 0.68 + 0.055 * math.sin(a))], DIENTE)


def boca_cosida(d):
    h.trazo(d, [(0.34, 0.66), (0.66, 0.66)], NEGRO, 0.014)
    for i in range(7):
        x = 0.36 + i * 0.045
        h.trazo(d, [(x, 0.635), (x + 0.01, 0.685)], (60, 40, 40, 255), 0.01)


BOCAS = [("Cerrada", boca_cerrada), ("Colmillos", boca_colmillos), ("Vertical", boca_vertical),
         ("SonrisaRota", boca_sonrisa_rota), ("Abierta", boca_abierta), ("Cosida", boca_cosida)]


# ---- Marcas del pecho ----

def marcas_venas(d):
    for x0 in (0.2, 0.5, 0.8):
        pts = [(x0 + 0.05 * math.sin(i * 1.3 + x0 * 9), 0.1 + 0.8 * i / 9) for i in range(10)]
        h.trazo(d, pts, BLANCO, 0.018)
        h.trazo(d, [pts[4], (pts[4][0] + 0.12, pts[4][1] + 0.08)], BLANCO, 0.012)


def marcas_runas(d):
    for k in range(3):
        y = 0.22 + k * 0.28
        h.trazo(d, [(0.5, y - 0.1), (0.5, y + 0.1)], BLANCO, 0.022)
        h.trazo(d, [(0.4, y - 0.04), (0.5, y + 0.02), (0.6, y - 0.04)], BLANCO, 0.02)
        h.elipse(d, 0.5, y + 0.13, 0.016, 0.016, BLANCO)


def marcas_grietas(d):
    h.trazo(d, [(0.5, 0.05), (0.44, 0.25), (0.56, 0.4), (0.46, 0.6), (0.54, 0.8), (0.5, 0.95)], BLANCO, 0.022)
    for y, dx in ((0.25, -0.2), (0.4, 0.22), (0.6, -0.18), (0.8, 0.2)):
        h.trazo(d, [(0.5, y), (0.5 + dx, y + 0.06)], BLANCO, 0.014)


def marcas_espiral(d):
    pts = [(0.5 + (0.04 + 0.37 * i / 60) * math.cos(i * 0.32), 0.5 + (0.04 + 0.37 * i / 60) * math.sin(i * 0.32)) for i in range(60)]
    h.trazo(d, pts, BLANCO, 0.02)


def marcas_ojos(d):
    for cx, cy, r in ((0.3, 0.3, 0.1), (0.7, 0.45, 0.13), (0.38, 0.72, 0.09)):
        h.elipse(d, cx, cy, r, r * 0.65, BLANCO)
        h.elipse(d, cx, cy, r * 0.5, r * 0.55, NEGRO)


def marcas_costuras(d):
    h.trazo(d, [(0.5, 0.05), (0.5, 0.95)], BLANCO, 0.016)
    for i in range(12):
        y = 0.08 + i * 0.075
        h.trazo(d, [(0.44, y), (0.56, y + 0.03)], BLANCO, 0.012)


MARCAS = [("Venas", marcas_venas), ("Runas", marcas_runas), ("Grietas", marcas_grietas), ("Espiral", marcas_espiral),
          ("Ojos", marcas_ojos), ("Costuras", marcas_costuras)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    args = ap.parse_args()
    carpeta = os.path.join(os.path.abspath(args.salida), "roblox", "texturas")
    os.makedirs(carpeta, exist_ok=True)
    rutas = {}
    for prefijo, lista, con_brillo in (("Ojos", OJOS, True), ("Boca", BOCAS, False), ("Marcas", MARCAS, True)):
        for nombre, f in lista:
            img, d = nueva()
            f(d)
            if con_brillo:
                img = brillo(img)
            rutas[(prefijo, nombre)] = h.guardar(img, os.path.join(carpeta, f"{prefijo}_{nombre}.png"))

    # Hoja de muestra: cara gris con los ojos teñidos de rojo y cada boca; torso con cada marca teñida de cian.
    def teñir(ruta, color):
        t = Image.open(ruta)
        tinte = Image.new("RGBA", t.size, color)
        a = t.getchannel("A")
        r, g, b, _ = t.split()
        tinte.putalpha(a)
        # El blanco lleva el color; lo negro de la textura sigue negro.
        base = Image.merge("RGBA", (r.point(lambda v: v * color[0] // 255), g.point(lambda v: v * color[1] // 255),
                                    b.point(lambda v: v * color[2] // 255), a))
        return base

    piel = (112, 126, 132, 255)
    celdas = []
    for (cat, nombre), ruta in rutas.items():
        cara = Image.new("RGBA", (TAM, TAM), piel)
        if cat == "Marcas":
            cara.alpha_composite(teñir(ruta, (77, 232, 255, 255)))
        else:
            ojos = rutas[("Ojos", nombre)] if cat == "Ojos" else rutas[("Ojos", "Dos")]
            boca = rutas[("Boca", nombre)] if cat == "Boca" else rutas[("Boca", "Colmillos")]
            cara.alpha_composite(teñir(ojos, (255, 50, 50, 255)))
            cara.alpha_composite(Image.open(boca))
        celdas.append((f"{cat} {nombre}", cara.resize((200, 200), Image.LANCZOS)))
    columnas = 7
    filas = math.ceil(len(celdas) / columnas)
    hoja = Image.new("RGB", (columnas * 200, filas * 224), (16, 18, 24))
    dh = ImageDraw.Draw(hoja)
    for i, (txt, im) in enumerate(celdas):
        x, y = (i % columnas) * 200, (i // columnas) * 224
        hoja.paste(im, (x, y + 22))
        dh.text((x + 6, y + 4), txt, fill=(230, 235, 245))
    hoja.save(os.path.join(os.path.abspath(args.salida), "muestra_monstruo.png"))
    print("[ok]", len(rutas), "texturas en", carpeta)


if __name__ == "__main__":
    main()
