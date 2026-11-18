"""
Imágenes de los rótulos de la clínica (Pillow). Se proyectan con la UV «deco» y se hornean en el atlas: el texto
grabado de la placa (máscara para el relieve), los carteles, el horario, la pantalla del medidor y el teclado.
Devuelve {nombre: ruta_png}.
"""

import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FUENTES = "/usr/share/fonts/truetype/dejavu/"


def _f(tam, estilo="Bold"):
    nombre = {"Bold": "DejaVuSans-Bold.ttf", "Book": "DejaVuSans.ttf", "Cond": "../liberation/LiberationSans-Bold.ttf",
              "Mono": "DejaVuSansMono-Bold.ttf", "Serif": "DejaVuSerif-Bold.ttf"}[estilo]
    return ImageFont.truetype(os.path.join(FUENTES, nombre), tam)


def _centrado(d, txt, cx, cy, fuente, color, espacio=0):
    if espacio:
        anchos = [d.textlength(ch, font=fuente) + espacio for ch in txt]
        x = cx - (sum(anchos) - espacio) / 2
        for ch, w in zip(txt, anchos):
            d.text((x, cy), ch, font=fuente, fill=color, anchor="lm")
            x += w
    else:
        d.text((cx, cy), txt, font=fuente, fill=color, anchor="mm")


def generar(carpeta):
    os.makedirs(carpeta, exist_ok=True)
    rutas = {}

    def guardar(nombre, img):
        r = os.path.join(carpeta, nombre + ".png")
        img.save(r)
        rutas[nombre] = r

    # Placa grabada «CLÍNICA COLONIAL — Dra. Voss» (1,3 x 0,6 studs). Blanco = surco grabado.
    w, h = 1300, 600
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    _centrado(d, "CLÍNICA COLONIAL", w / 2, 215, _f(118, "Cond"), 255, espacio=6)
    d.line((150, 318, w - 150, 318), fill=255, width=7)
    _centrado(d, "— Dra. Voss —", w / 2, 418, _f(96, "Serif"), 255)
    # cruz pequeña en las esquinas superiores
    for cx in (70, w - 70):
        d.rectangle((cx - 12, 60, cx + 12, 120), fill=255)
        d.rectangle((cx - 30, 78, cx + 30, 102), fill=255)
    guardar("placa_grabado", im.filter(ImageFilter.GaussianBlur(1.2)))

    # Cartel de la puerta trasera «SOLO PERSONAL» (1,4 x 0,5).
    w, h = 1400, 500
    im = Image.new("RGB", (w, h), (246, 246, 242))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 120), fill=(196, 34, 40))
    _centrado(d, "ACCESO RESTRINGIDO", w / 2, 62, _f(74, "Cond"), (255, 255, 255), espacio=4)
    _centrado(d, "SOLO PERSONAL", w / 2, 285, _f(150, "Cond"), (30, 30, 34))
    _centrado(d, "Clínica Colonial · Suministros", w / 2, 430, _f(54, "Book"), (90, 92, 98))
    d.rectangle((14, 14, w - 14, h - 14), outline=(196, 34, 40), width=10)
    guardar("solo_personal", im)

    # Señal de parking: «P» (1,2 x 1,2) y placa «Solo emergencias» (1,2 x 0,5).
    w = 1024
    im = Image.new("RGB", (w, w), (18, 86, 168))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((34, 34, w - 34, w - 34), radius=70, outline=(255, 255, 255), width=26)
    _centrado(d, "P", w / 2, w / 2 + 20, _f(760), (255, 255, 255))
    guardar("parking_p", im)
    w, h = 1200, 500
    im = Image.new("RGB", (w, h), (250, 250, 248))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((18, 18, w - 18, h - 18), radius=40, outline=(200, 30, 36), width=18)
    _centrado(d, "Solo", w / 2 + 130, 150, _f(120, "Cond"), (200, 30, 36))
    _centrado(d, "emergencias", w / 2 + 130, 330, _f(128, "Cond"), (200, 30, 36))
    cx, cy = 165, 250  # cruz médica a la izquierda
    d.rectangle((cx - 32, cy - 100, cx + 32, cy + 100), fill=(200, 30, 36))
    d.rectangle((cx - 100, cy - 32, cx + 100, cy + 32), fill=(200, 30, 36))
    guardar("parking_sub", im)

    # Papel del tablón: «HORARIO» (1,0 x 1,2), con la esquina un poco amarillenta.
    w, h = 1000, 1200
    im = Image.new("RGB", (w, h), (247, 246, 240))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 170), fill=(40, 130, 120))
    _centrado(d, "HORARIO", w / 2, 92, _f(110, "Cond"), (255, 255, 255), espacio=8)
    filas = [("Lun – Vie", "08:00 – 20:00"), ("Sábado", "09:00 – 14:00"), ("Domingo", "Cerrado")]
    y = 260
    for a, b in filas:
        d.text((60, y), a, font=_f(48, "Book"), fill=(40, 40, 46))
        d.text((w - 60, y), b, font=_f(48), fill=(40, 40, 46), anchor="ra")
        y += 110
        d.line((70, y - 22, w - 70, y - 22), fill=(200, 200, 196), width=3)
    d.rectangle((60, 640, w - 60, 820), fill=(200, 34, 40))
    _centrado(d, "URGENCIAS 24 h", w / 2, 700, _f(78, "Cond"), (255, 255, 255))
    _centrado(d, "Llame al timbre o al canal 9", w / 2, 775, _f(40, "Book"), (255, 230, 230))
    for i, t in enumerate(["Curas · Vacunas · Revisiones de minería", "Dra. Voss — Médica de la colonia"]):
        _centrado(d, t, w / 2, 900 + i * 70, _f(40, "Book"), (70, 72, 80))
    for cx, cy in ((120, 1080), (w - 120, 1080)):
        d.rectangle((cx - 14, cy - 44, cx + 14, cy + 44), fill=(40, 130, 120))
        d.rectangle((cx - 44, cy - 14, cx + 44, cy + 14), fill=(40, 130, 120))
    # chincheta y sombra de la esquina
    for cx, cy in ((80, 220), (w - 80, 220)):
        d.ellipse((cx - 18, cy - 18, cx + 18, cy + 18), fill=(190, 40, 40))
    guardar("horario", im)

    # Pantalla del medidor de energía (0,5 x 0,22): fondo negro, dígitos verdes. Es también la emisión.
    w, h = 1000, 440
    im = Image.new("RGB", (w, h), (6, 14, 10))
    d = ImageDraw.Draw(im)
    _centrado(d, "0427.8", w / 2 - 60, h / 2 + 10, _f(230, "Mono"), (120, 255, 170))
    d.text((w - 40, h - 50), "kWh", font=_f(70, "Mono"), fill=(90, 210, 140), anchor="rs")
    d.text((40, 40), "▲ 2.4 kW", font=_f(50, "Mono"), fill=(90, 210, 140))
    guardar("medidor", im)

    # Etiquetas del teclado numérico (0,26 x 0,36): rejilla 3 x 4 de cifras sobre fondo transparente (negro).
    w, h = 520, 720
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    teclas = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    for i, t in enumerate(teclas):
        fx, fy = i % 3, i // 3
        cx = w * (0.5 + (fx - 1) * 0.3)
        cy = h * (0.58 + (fy - 1.5) * 0.19)
        _centrado(d, t, cx, cy, _f(70), 255)
    guardar("teclado", im)

    # Etiqueta del dispensador de gel y del botiquín.
    w, h = 600, 300
    im = Image.new("RGB", (w, h), (240, 244, 246))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 90), fill=(30, 120, 190))
    _centrado(d, "GEL", w / 2, 47, _f(70), (255, 255, 255), espacio=6)
    _centrado(d, "hidroalcohólico", w / 2, 160, _f(56, "Book"), (30, 60, 90))
    _centrado(d, "Pulse y frote 20 s", w / 2, 240, _f(44, "Book"), (80, 90, 100))
    guardar("gel", im)

    w, h = 800, 200
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    _centrado(d, "PRIMEROS AUXILIOS", w / 2, h / 2, _f(76, "Cond"), 255)
    guardar("botiquin_texto", im)

    # Símbolo de residuos biológicos para la tapa de la papelera (pegatina amarilla).
    w = 600
    im = Image.new("RGB", (w, w), (240, 196, 30))
    d = ImageDraw.Draw(im)
    d.ellipse((10, 10, w - 10, w - 10), outline=(20, 20, 20), width=14)
    _centrado(d, "☣", w / 2, w / 2 - 30, _f(330, "Book"), (20, 20, 20))
    _centrado(d, "RESIDUOS", w / 2, w - 120, _f(56, "Cond"), (20, 20, 20), espacio=3)
    guardar("residuos", im)

    # Cartel interior (visible por la ventana de la sala de espera).
    w, h = 600, 800
    im = Image.new("RGB", (w, h), (236, 246, 244))
    d = ImageDraw.Draw(im)
    d.rectangle((0, 0, w, 220), fill=(40, 130, 120))
    _centrado(d, "+", w / 2, 110, _f(200), (255, 255, 255))
    _centrado(d, "Lávese", w / 2, 330, _f(80, "Cond"), (40, 60, 70))
    _centrado(d, "las manos", w / 2, 430, _f(80, "Cond"), (40, 60, 70))
    for i in range(4):
        d.ellipse((90 + i * 115, 560, 170 + i * 115, 640), fill=(120, 200, 190))
    guardar("cartel_interior", im)
    return rutas


if __name__ == "__main__":
    import sys

    print(generar(sys.argv[1] if len(sys.argv) > 1 else "rotulos"))
