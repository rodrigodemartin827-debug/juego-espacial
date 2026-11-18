"""
Calcos del puesto de seguridad: imágenes que se proyectan sobre la malla alta y acaban horneadas en el atlas.

Se dibujan con Pillow (nada sacado de internet, nada de marcas reales):
  * los tres avisos «SE BUSCA» del tablón (dos criaturas y un contrabandista), el horario de patrulla y un aviso
    de toque de queda,
  * el teclado de la cerradura, la pegatina «SOLO PERSONAL AUTORIZADO» y la etiqueta del extintor,
  * el logo de la colonia (estrella en un círculo) para la bandera,
  * las dos imágenes de las cámaras que salen en los monitores de dentro, la foto familiar del guardia y su
    calendario,
  * la etiqueta del interfono y el dibujo de la taza.

Todas las imágenes son RGBA: lo transparente deja ver el material de debajo.
"""

import math
import os
import random

from PIL import Image, ImageDraw, ImageFilter, ImageFont

DEJAVU = "/usr/share/fonts/truetype/dejavu/"


def _f(nombre, tam):
    ruta = os.path.join(DEJAVU, nombre)
    return ImageFont.truetype(ruta, tam) if os.path.exists(ruta) else ImageFont.load_default()


def sans(tam):
    return _f("DejaVuSans-Bold.ttf", tam)


def sans_fina(tam):
    return _f("DejaVuSans.ttf", tam)


def serif(tam):
    return _f("DejaVuSerif-Bold.ttf", tam)


def mono(tam):
    return _f("DejaVuSansMono-Bold.ttf", tam)


def _centrado(d, y, txt, fuente, ancho, color):
    caja = d.textbbox((0, 0), txt, font=fuente)
    d.text(((ancho - (caja[2] - caja[0])) / 2 - caja[0], y), txt, font=fuente, fill=color)


def _papel(w, h, base, semilla, manchas=6):
    """Papel con fibras, manchas de humedad y los bordes algo más oscuros."""
    rnd = random.Random(semilla)
    img = Image.new("RGBA", (w, h), base + (255,))
    d = ImageDraw.Draw(img)
    for _ in range(1400):
        x, y = rnd.randrange(w), rnd.randrange(h)
        k = rnd.randint(-14, 8)
        c = tuple(max(0, min(255, v + k)) for v in base)
        d.point((x, y), fill=c + (255,))
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    for _ in range(manchas):
        r = rnd.randint(w // 14, w // 5)
        x, y = rnd.randrange(w), rnd.randrange(h)
        dc.ellipse((x - r, y - r * 0.8, x + r, y + r * 0.8), outline=(120, 96, 60, 70), width=3,
                   fill=(150, 125, 80, 26))
    capa = capa.filter(ImageFilter.GaussianBlur(3))
    img = Image.alpha_composite(img, capa)
    # Bordes tostados.
    borde = Image.new("L", (w, h), 0)
    db = ImageDraw.Draw(borde)
    for i in range(18):
        db.rectangle((i, i, w - 1 - i, h - 1 - i), outline=int(70 * (1 - i / 18)))
    oscuro = Image.new("RGBA", (w, h), (95, 70, 40, 255))
    img = Image.composite(oscuro, img, borde.filter(ImageFilter.GaussianBlur(4)))
    return img


def se_busca(ruta, semilla, titulo, nombre, lineas, recompensa, dibujo, base=(232, 220, 190)):
    w, h = 600, 860
    img = _papel(w, h, base, semilla)
    d = ImageDraw.Draw(img)
    tinta = (38, 28, 22, 255)
    rojo = (150, 30, 24, 255)
    d.rectangle((26, 26, w - 27, h - 27), outline=tinta, width=5)
    d.rectangle((38, 38, w - 39, h - 39), outline=tinta, width=2)
    _centrado(d, 56, titulo, serif(80), w, tinta)
    _centrado(d, 160, "VIVO O CAPTURADO", serif(34), w, rojo)
    # Retrato con marco.
    d.rectangle((110, 214, w - 110, 520), fill=(214, 200, 166, 255), outline=tinta, width=4)
    dibujo(d, (110, 214, w - 110, 520), tinta)
    _centrado(d, 540, nombre, serif(44), w, tinta)
    y = 600
    for ln in lineas:
        _centrado(d, y, ln, sans_fina(25), w, tinta)
        y += 31
    _centrado(d, h - 150, "RECOMPENSA", serif(44), w, tinta)
    _centrado(d, h - 98, recompensa, serif(52), w, rojo)
    img.save(ruta)


def _criatura_ojos(d, caja, tinta):
    """Silueta de criatura de muchos ojos (la que asusta a los mineros)."""
    x0, y0, x1, y1 = caja
    cx = (x0 + x1) / 2
    d.ellipse((cx - 120, y0 + 60, cx + 120, y1 + 40), fill=(60, 48, 40, 255))
    d.rectangle((x0 + 4, y1 - 4, x1 - 4, y1 + 60), fill=(214, 200, 166, 255))
    for i, (ox, oy, r) in enumerate([(-55, 120, 16), (0, 100, 22), (55, 120, 16), (-30, 160, 10), (30, 160, 10),
                                      (-80, 165, 8), (80, 165, 8)]):
        d.ellipse((cx + ox - r, y0 + oy - r, cx + ox + r, y0 + oy + r), fill=(236, 226, 196, 255))
        d.ellipse((cx + ox - r * 0.35, y0 + oy - r * 0.35, cx + ox + r * 0.35, y0 + oy + r * 0.35),
                  fill=(20, 14, 10, 255))
    for k in range(-3, 4):  # dientes
        x = cx + k * 22
        d.polygon([(x - 9, y0 + 210), (x + 9, y0 + 210), (x, y0 + 245)], fill=(236, 226, 196, 255))
    for k in (-1, 1):  # patas
        d.line([(cx + k * 110, y0 + 200), (cx + k * 160, y0 + 140), (cx + k * 175, y0 + 290)], fill=tinta, width=9)


def _contrabandista(d, caja, tinta):
    """Busto de un contrabandista con gorro, gafas de soldador y cicatriz."""
    x0, y0, x1, y1 = caja
    cx = (x0 + x1) / 2
    piel = (170, 140, 110, 255)
    d.polygon([(cx - 150, y1 - 2), (cx - 120, y1 - 80), (cx + 120, y1 - 80), (cx + 150, y1 - 2)], fill=(70, 62, 55, 255))
    d.ellipse((cx - 72, y0 + 60, cx + 72, y0 + 240), fill=piel, outline=tinta, width=3)
    d.chord((cx - 85, y0 + 30, cx + 85, y0 + 150), 180, 360, fill=(80, 60, 45, 255))
    d.rectangle((cx - 92, y0 + 88, cx + 92, y0 + 100), fill=(80, 60, 45, 255))
    for k in (-1, 1):
        d.ellipse((cx + k * 34 - 24, y0 + 118, cx + k * 34 + 24, y0 + 154), fill=(40, 60, 64, 255), outline=tinta,
                  width=4)
    d.line([(cx - 10, y0 + 136), (cx + 10, y0 + 136)], fill=tinta, width=5)
    d.line([(cx + 30, y0 + 165), (cx + 55, y0 + 215)], fill=(120, 40, 30, 255), width=4)  # cicatriz
    d.arc((cx - 30, y0 + 180, cx + 30, y0 + 215), 20, 160, fill=tinta, width=4)
    d.polygon([(cx - 60, y0 + 200), (cx + 60, y0 + 200), (cx + 40, y0 + 245), (cx - 40, y0 + 245)],
              fill=(90, 70, 50, 255))  # barba


def _babosa(d, caja, tinta):
    """Gusano gigante de las minas, de perfil, con anillos y la boca abierta."""
    x0, y0, x1, y1 = caja
    for i in range(7):
        x = x0 + 46 + i * 36
        y = y1 - 60 - i * 14 - math.sin(i * 1.1) * 18
        r = 46 - i * 2
        d.ellipse((x - r, y - r, x + r, y + r), fill=(84, 74, 58, 255), outline=tinta, width=3)
    hx, hy = x1 - 78, y0 + 120
    d.ellipse((hx - 62, hy - 62, hx + 62, hy + 62), fill=(84, 74, 58, 255), outline=tinta, width=4)
    d.ellipse((hx - 36, hy - 36, hx + 36, hy + 36), fill=(30, 20, 18, 255))
    for k in range(10):
        a = k / 10 * math.tau
        d.polygon([(hx + math.cos(a) * 36, hy + math.sin(a) * 36),
                   (hx + math.cos(a + 0.25) * 36, hy + math.sin(a + 0.25) * 36),
                   (hx + math.cos(a + 0.12) * 16, hy + math.sin(a + 0.12) * 16)], fill=(236, 226, 196, 255))


def horario(ruta):
    w, h = 640, 820
    img = Image.new("RGBA", (w, h), (244, 244, 238, 255))
    d = ImageDraw.Draw(img)
    azul = (24, 52, 96, 255)
    tinta = (30, 30, 34, 255)
    d.rectangle((0, 0, w, 130), fill=azul)
    _centrado(d, 18, "HORARIO DE", sans(44), w, (255, 255, 255, 255))
    _centrado(d, 68, "PATRULLA", sans(48), w, (255, 196, 64, 255))
    filas = [("TURNO", "HORA", "GUARDIA"), ("MAÑANA", "06-14", "B. ORTIZ"), ("TARDE", "14-22", "B. ORTIZ"),
             ("NOCHE", "22-06", "R. VEGA"), ("RONDA", "CADA 2 H", "MINAS"), ("CIERRE", "23:00", "BARRERA")]
    y = 170
    for i, (a, b, c) in enumerate(filas):
        fnt = sans(30) if i == 0 else sans_fina(30)
        if i % 2 == 1:
            d.rectangle((30, y - 8, w - 30, y + 46), fill=(226, 230, 236, 255))
        d.text((44, y), a, font=fnt, fill=tinta)
        d.text((250, y), b, font=fnt, fill=tinta)
        d.text((430, y), c, font=fnt, fill=tinta)
        y += 64
    d.line([(30, 214), (w - 30, 214)], fill=azul, width=3)
    # Anotación a mano (bolígrafo rojo): el guardia hace doble turno.
    rojo = (176, 30, 30, 255)
    d.ellipse((410, 228, 610, 368), outline=rojo, width=4)
    d.text((80, 600), "¡Doble turno toda", font=_f("DejaVuSerif-Italic.ttf", 34) if os.path.exists(
        DEJAVU + "DejaVuSerif-Italic.ttf") else serif(30), fill=rojo)
    d.text((80, 646), "la semana! - B.", font=_f("DejaVuSerif-Italic.ttf", 34) if os.path.exists(
        DEJAVU + "DejaVuSerif-Italic.ttf") else serif(30), fill=rojo)
    d.rectangle((0, h - 70, w, h), fill=azul)
    _centrado(d, h - 58, "SEGURIDAD COLONIAL", sans(32), w, (255, 255, 255, 255))
    img.save(ruta)


def toque_queda(ruta):
    w, h = 560, 400
    img = _papel(w, h, (250, 214, 92), 77, manchas=3)
    d = ImageDraw.Draw(img)
    tinta = (26, 22, 18, 255)
    d.rectangle((16, 16, w - 17, h - 17), outline=tinta, width=6)
    _centrado(d, 40, "AVISO", sans(70), w, tinta)
    _centrado(d, 130, "TOQUE DE QUEDA", sans(46), w, tinta)
    _centrado(d, 196, "22:00 - 06:00", sans(56), w, (150, 26, 20, 255))
    _centrado(d, 280, "Barrera cerrada de noche.", sans_fina(28), w, tinta)
    _centrado(d, 318, "Llamen al interfono.", sans_fina(28), w, tinta)
    img.save(ruta)


def teclado(ruta):
    """Cara del teclado: 4 filas x 3 columnas; las letras se ven en las teclas de la malla alta."""
    w, h = 300, 420
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    teclas = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    for i, t in enumerate(teclas):
        c, f = i % 3, i // 3
        x = 50 + c * 100
        y = 64 + f * 98
        fnt = sans(44)
        caja = d.textbbox((0, 0), t, font=fnt)
        d.text((x - (caja[2] - caja[0]) / 2 - caja[0], y - (caja[3] - caja[1]) / 2 - caja[1]), t, font=fnt,
               fill=(232, 236, 240, 255))
    img.save(ruta)


def pegatina_autorizado(ruta):
    w, h = 640, 260
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=(250, 196, 30, 255))
    for k in range(-4, 40):  # bandas de peligro arriba y abajo
        x = k * 34
        for y0, y1 in ((0, 34), (h - 34, h)):
            d.polygon([(x, y1), (x + 17, y1), (x + 17 + (y1 - y0), y0), (x + (y1 - y0), y0)], fill=(20, 20, 20, 255))
    d.rectangle((0, 34, w, h - 34), fill=(250, 196, 30, 255))
    _centrado(d, 52, "SOLO PERSONAL", sans(66), w, (20, 20, 20, 255))
    _centrado(d, 134, "AUTORIZADO", sans(66), w, (20, 20, 20, 255))
    mascara = Image.new("L", (w, h), 0)
    ImageDraw.Draw(mascara).rounded_rectangle((0, 0, w - 1, h - 1), 22, fill=255)
    img.putalpha(mascara)
    img.save(ruta)


def etiqueta_extintor(ruta):
    w, h = 300, 420
    img = Image.new("RGBA", (w, h), (240, 238, 230, 255))
    d = ImageDraw.Draw(img)
    rojo = (190, 30, 26, 255)
    tinta = (24, 24, 24, 255)
    d.rectangle((0, 0, w, 86), fill=rojo)
    _centrado(d, 14, "EXTINTOR", sans(50), w, (255, 255, 255, 255))
    _centrado(d, 100, "POLVO ABC", sans(40), w, tinta)
    _centrado(d, 150, "6 kg", sans(46), w, rojo)
    for i, letra in enumerate("ABC"):
        x = 50 + i * 80
        d.rectangle((x - 30, 220, x + 30, 280), outline=tinta, width=4)
        caja = d.textbbox((0, 0), letra, font=sans(44))
        d.text((x - (caja[2] - caja[0]) / 2 - caja[0], 226), letra, font=sans(44), fill=tinta)
    for i, ln in enumerate(("1. Quitar el seguro", "2. Apuntar a la base", "3. Apretar la palanca")):
        d.text((24, 302 + i * 36), ln, font=sans_fina(24), fill=tinta)
    img.save(ruta)


def senal_extintor(ruta):
    """Señal de evacuación: cuadrado rojo con el pictograma blanco del extintor."""
    w = h = 400
    img = Image.new("RGBA", (w, h), (196, 28, 26, 255))
    d = ImageDraw.Draw(img)
    blanco = (250, 250, 250, 255)
    d.rectangle((10, 10, w - 11, h - 11), outline=blanco, width=8)
    d.rounded_rectangle((150, 130, 230, 340), 30, fill=blanco)          # botella
    d.rectangle((170, 100, 210, 135), fill=blanco)                      # válvula
    d.polygon([(205, 105), (275, 85), (280, 100), (210, 122)], fill=blanco)  # palanca
    d.line([(170, 110), (120, 140), (110, 250)], fill=blanco, width=14)      # manguera
    for k, (x, y) in enumerate(((290, 290), (320, 250), (300, 220))):         # llama
        d.polygon([(x - 26, y + 40), (x, y - 40 + k * 8), (x + 26, y + 40)], fill=blanco)
    return img.save(ruta)


def logo_bandera(ruta, ancho=1000, alto=640):
    """Bandera de la colonia: azul noche, franja naranja en el mástil, círculo blanco y estrella dorada."""
    img = Image.new("RGBA", (ancho, alto), (20, 44, 92, 255))
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 70, alto), fill=(232, 112, 32, 255))
    d.rectangle((70, 0, 86, alto), fill=(240, 240, 236, 255))
    cx, cy, r = ancho * 0.56, alto / 2, alto * 0.34
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=(240, 240, 236, 255), width=int(alto * 0.045))
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = r * 0.8 if k % 2 == 0 else r * 0.33
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=(250, 190, 50, 255))
    img.save(ruta)


def _escena_cctv(d, w, h, que):
    """Dibujo esquemático de lo que ve cada cámara (en tonos verdes de monitor de vigilancia)."""
    fondo = (16, 40, 32, 255)
    claro = (110, 200, 150, 255)
    medio = (52, 110, 84, 255)
    d.rectangle((0, 0, w, h), fill=fondo)
    if que == "barrera":
        d.polygon([(w * 0.1, h), (w * 0.45, h * 0.35), (w * 0.62, h * 0.35), (w * 0.95, h)], fill=(30, 66, 52, 255))
        d.line([(w * 0.28, h * 0.75), (w * 0.78, h * 0.62)], fill=claro, width=10)  # brazo
        for k in range(5):
            x = w * 0.28 + k * w * 0.1
            d.line([(x, h * 0.75 - k * h * 0.026), (x + w * 0.05, h * 0.75 - k * h * 0.026 - h * 0.013)], fill=fondo,
                   width=10)
        d.rectangle((w * 0.24, h * 0.7, w * 0.29, h * 0.95), fill=medio)
        d.polygon([(w * 0.82, h * 0.9), (w * 0.86, h * 0.7), (w * 0.9, h * 0.9)], fill=claro)  # cono
    else:
        d.rectangle((0, h * 0.62, w, h), fill=(30, 66, 52, 255))
        for x0, ww, hh in ((0.05, 0.2, 0.3), (0.3, 0.16, 0.22), (0.55, 0.22, 0.34), (0.82, 0.15, 0.2)):
            d.rectangle((w * x0, h * (0.62 - hh), w * (x0 + ww), h * 0.62), fill=medio)
            d.rectangle((w * (x0 + 0.04), h * (0.62 - hh + 0.06), w * (x0 + 0.08), h * (0.62 - hh + 0.12)),
                        fill=claro)
        d.ellipse((w * 0.42, h * 0.5, w * 0.47, h * 0.58), fill=claro)  # alguien que pasa
        d.rectangle((w * 0.425, h * 0.57, w * 0.465, h * 0.72), fill=claro)
    for y in range(0, h, 4):  # líneas de barrido
        d.line([(0, y), (w, y)], fill=(0, 0, 0, 60))


def pantalla(ruta, que, texto):
    w, h = 640, 400
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(img, "RGBA")
    _escena_cctv(d, w, h, que)
    d.text((16, 12), texto, font=mono(30), fill=(200, 255, 220, 255))
    d.text((16, h - 46), "03:47:12", font=mono(30), fill=(200, 255, 220, 255))
    d.ellipse((w - 52, 16, w - 24, 44), fill=(255, 60, 50, 255))
    d.text((w - 128, 12), "REC", font=mono(30), fill=(255, 90, 80, 255))
    img.save(ruta)


def foto_familia(ruta):
    """La foto del guardia: atardecer en el planeta, con su pareja y su perro."""
    w, h = 400, 300
    img = Image.new("RGBA", (w, h), (0, 0, 0, 255))
    d = ImageDraw.Draw(img)
    for y in range(h):
        f = y / h
        d.line([(0, y), (w, y)], fill=(int(250 - 90 * f), int(170 - 90 * f), int(90 + 40 * f), 255))
    d.ellipse((w * 0.6, h * 0.25, w * 0.85, h * 0.58), fill=(255, 226, 150, 255))
    d.rectangle((0, h * 0.68, w, h), fill=(60, 48, 60, 255))
    for x, alto in ((0.32, 0.5), (0.48, 0.44)):
        d.ellipse((w * x - 18, h * (0.68 - alto), w * x + 18, h * (0.68 - alto) + 36), fill=(40, 30, 40, 255))
        d.rectangle((w * x - 22, h * (0.68 - alto) + 32, w * x + 22, h * 0.9), fill=(40, 30, 40, 255))
    d.ellipse((w * 0.6, h * 0.74, w * 0.7, h * 0.84), fill=(40, 30, 40, 255))
    d.ellipse((w * 0.68, h * 0.7, w * 0.74, h * 0.78), fill=(40, 30, 40, 255))
    img.save(ruta)


def calendario(ruta):
    w, h = 400, 560
    img = Image.new("RGBA", (w, h), (246, 244, 236, 255))
    d = ImageDraw.Draw(img)
    for y in range(240):  # foto del mes: el planeta humano visto desde la órbita
        d.line([(0, y), (w, y)], fill=(10, 14 + y // 12, 40 + y // 5, 255))
    d.ellipse((90, 60, 310, 280), fill=(60, 130, 200, 255))
    d.chord((90, 60, 310, 280), 200, 340, fill=(90, 160, 90, 255))
    d.rectangle((0, 240, w, 300), fill=(200, 60, 40, 255))
    _centrado(d, 248, "CICLO 7", sans(40), w, (255, 255, 255, 255))
    rojo = (190, 30, 30, 255)
    for i in range(30):
        c, f = i % 7, i // 7
        x, y = 22 + c * 52, 318 + f * 46
        d.text((x, y), str(i + 1), font=sans_fina(24), fill=(40, 40, 40, 255))
        if i < 17:  # días tachados
            d.line([(x - 4, y + 2), (x + 30, y + 30)], fill=rojo, width=3)
            d.line([(x + 30, y + 2), (x - 4, y + 30)], fill=rojo, width=3)
    d.ellipse((22 + 3 * 52 - 10, 318 + 3 * 46 - 8, 22 + 3 * 52 + 40, 318 + 3 * 46 + 38), outline=rojo, width=3)
    img.save(ruta)


def etiqueta_interfono(ruta):
    w, h = 300, 120
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    _centrado(d, 14, "PULSE PARA", sans(36), w, (236, 236, 236, 255))
    _centrado(d, 62, "LLAMAR", sans(40), w, (255, 200, 60, 255))
    img.save(ruta)


def taza(ruta):
    w, h = 400, 300
    img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    azul = (24, 52, 110, 255)
    cx, cy = w / 2, 92
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5
        rr = 64 if k % 2 == 0 else 26
        pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
    d.polygon(pts, fill=(240, 170, 40, 255))
    _centrado(d, 168, "EL MEJOR", sans(46), w, azul)
    _centrado(d, 222, "GUARDIA", sans(52), w, azul)
    img.save(ruta)


def generar(carpeta):
    os.makedirs(carpeta, exist_ok=True)
    r = {}

    def ruta(n):
        r[n] = os.path.join(carpeta, n + ".png")
        return r[n]

    se_busca(ruta("se_busca_1"), 11, "SE BUSCA", "EL DE LOS OJOS",
             ["Criatura nocturna de las minas.", "Visto en el túnel 4.", "NO ACERCARSE."], "800 CRÉDITOS",
             _criatura_ojos)
    se_busca(ruta("se_busca_2"), 23, "SE BUSCA", "TUERTO MARLOW",
             ["Contrabandista de cristal abisal.", "Peligroso. Va armado.", "Avise al guardia."], "1.500 CRÉDITOS",
             _contrabandista, base=(226, 214, 180))
    se_busca(ruta("se_busca_3"), 37, "SE BUSCA", "GUSANO DE ROCA",
             ["Se come los cables de la mina.", "Mide más de 3 metros.", "Recompensa por la cabeza."],
             "500 CRÉDITOS", _babosa, base=(236, 226, 200))
    horario(ruta("horario"))
    toque_queda(ruta("toque_queda"))
    teclado(ruta("teclado"))
    pegatina_autorizado(ruta("autorizado"))
    etiqueta_extintor(ruta("extintor"))
    senal_extintor(ruta("senal_extintor"))
    logo_bandera(ruta("bandera"))
    pantalla(ruta("pantalla_1"), "barrera", "CAM 01 BARRERA")
    pantalla(ruta("pantalla_2"), "calle", "CAM 02 CALLE")
    foto_familia(ruta("foto"))
    calendario(ruta("calendario"))
    etiqueta_interfono(ruta("interfono"))
    taza(ruta("taza"))
    return r


if __name__ == "__main__":
    import sys

    salida = generar(sys.argv[1] if len(sys.argv) > 1 else "/tmp/calcos")
    print("\n".join(salida.values()))
