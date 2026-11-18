"""
Hoja de letreros de la casa del ingeniero: todos los textos, pegatinas, teclados y pantallas en UNA imagen
(fuente del horneado, no se exporta). Cada letrero es un rectángulo de la hoja; las caras con letrero llevan el
mapa UV «decal» apuntando a su rectángulo.

Se generan dos imágenes del mismo tamaño:
  * color (RGB): lo que se ve.
  * propiedades (RGBA): R = metal, G = rugosidad, B = relieve (0,5 = plano), A = emisión.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFilter

import kit_casas as K

TAM = 2048

# Rectángulos en píxeles (x0, y0, x1, y1) dentro de la hoja. La proporción es la de la pieza real.
R = {
    "placa_nombre": (20, 20, 760, 220),         # 1,40 × 0,38 studs
    "cartel_lab": (20, 240, 720, 470),          # 1,15 × 0,38
    "pegatina_voltaje": (740, 240, 980, 500),   # 0,40 × 0,44
    "reciclaje": (1000, 240, 1400, 640),        # 0,80 × 0,80
    "zona_vigilada": (1420, 240, 1820, 520),    # 0,70 × 0,50
    "placa_generador": (20, 500, 680, 700),     # 1,00 × 0,30
    "prototipo": (780, 20, 1300, 220),          # 0,62 × 0,24
    "teclado": (1320, 20, 1520, 220 + 80),      # 0,26 × 0,40 (cara del teclado)
    "lector": (1540, 20, 1760, 120),            # 0,26 × 0,12
    "cuadro_general": (20, 720, 700, 880),      # 1,10 × 0,26
    "distribucion": (720, 720, 1240, 880),      # 0,80 × 0,25
    "lcd_generador": (1260, 720, 1560, 880),    # 0,36 × 0,19
    "osciloscopio": (1580, 720, 1980, 1020),    # 0,52 × 0,38
    "monitor": (20, 900, 540, 1220),            # 0,85 × 0,52
    "cuaderno": (560, 900, 780, 1020),          # etiqueta de la tapa 0,30 × 0,16
    "arranque": (800, 900, 1040, 980),
    "parada": (1060, 900, 1300, 980),
    "auto_persiana": (1320, 900, 1520, 980),
    "mantenimiento": (800, 1000, 1240, 1080),   # tira del lab: «Revisado 14/03 · K.»
}
ETIQUETAS = ["FV-1", "FV-2", "FV-3", "ANT-P", "ANT-D", "METEO", "LAB", "CUADRO", "SOLAR-X", "TECHO", "GEN", "CAM"]
for i, t in enumerate(ETIQUETAS):
    x0 = 20 + (i % 6) * 250
    y0 = 1260 + (i // 6) * 110
    R[f"et_{t}"] = (x0, y0, x0 + 230, y0 + 90)


def uv_rect(nombre):
    """Rectángulo UV (u0, v0, u1, v1) del letrero (v hacia arriba, como en Blender)."""
    x0, y0, x1, y1 = R[nombre]
    return (x0 / TAM, 1 - y1 / TAM, x1 / TAM, 1 - y0 / TAM)


def generar(carpeta):
    os.makedirs(carpeta, exist_ok=True)
    col = Image.new("RGB", (TAM, TAM), (128, 128, 128))
    pro = Image.new("RGBA", (TAM, TAM), (0, 140, 128, 0))
    dc = ImageDraw.Draw(col)
    dp = ImageDraw.Draw(pro)
    F = K.fuente

    def props(caja, metal, rug, relieve=128, emision=0):
        dp.rectangle(caja, fill=(int(metal * 255), int(rug * 255), relieve, emision))

    def texto(caja, t, f, c, relieve=None, emision=None):
        # La letra se encoge hasta que cabe en la caja (con un margen).
        x0, y0, x1, y1 = caja
        while f.size > 8:
            bb = dc.textbbox((0, 0), t, font=f)
            if bb[2] - bb[0] <= (x1 - x0) * 0.92 and bb[3] - bb[1] <= (y1 - y0) * 0.9:
                break
            f = f.font_variant(size=f.size - 2)
        K.texto_centrado(dc, caja, t, f, c)
        if relieve is not None or emision is not None:
            # misma posición en la imagen de propiedades
            x0, y0, x1, y1 = caja
            bb = dc.textbbox((0, 0), t, font=f)
            w, h = bb[2] - bb[0], bb[3] - bb[1]
            pos = ((x0 + x1 - w) / 2 - bb[0], (y0 + y1 - h) / 2 - bb[1])
            capa = Image.new("L", (TAM, TAM), 0)
            ImageDraw.Draw(capa).text(pos, t, font=f, fill=255)
            if relieve is not None:
                r, g, b, a = pro.split()
                b = Image.composite(Image.new("L", (TAM, TAM), relieve), b, capa)
                pro.paste(Image.merge("RGBA", (r, g, b, a)))
            if emision is not None:
                r, g, b, a = pro.split()
                a = Image.composite(Image.new("L", (TAM, TAM), emision), a, capa)
                pro.paste(Image.merge("RGBA", (r, g, b, a)))

    def caja_rel(n, fx0, fy0, fx1, fy1):
        x0, y0, x1, y1 = R[n]
        w, h = x1 - x0, y1 - y0
        return (x0 + fx0 * w, y0 + fy0 * h, x0 + fx1 * w, y0 + fy1 * h)

    # 1) Placa del nombre: acero cepillado con letras grabadas en negro y tornillos en las esquinas
    n = "placa_nombre"
    x0, y0, x1, y1 = R[n]
    for y in range(y0, y1):
        t = 168 + int(14 * math.sin(y * 1.7) * math.sin(y * 0.31))
        dc.line((x0, y, x1, y), fill=(t, t + 3, t + 6))
    dc.rectangle(R[n], outline=(90, 94, 98), width=6)
    props(R[n], 1.0, 0.32)
    texto(caja_rel(n, 0.04, 0.08, 0.96, 0.6), "Ing. Kowalski", F(104), (24, 26, 30), relieve=60)
    texto(caja_rel(n, 0.04, 0.6, 0.96, 0.93), "— No tocar nada —", F(54, False), (40, 42, 46), relieve=70)
    dp.rectangle(R[n], outline=(255, 120, 128, 0), width=6)

    # 2) Cartel del laboratorio: esmalte blanco, banda azul técnica arriba, texto oscuro
    n = "cartel_lab"
    dc.rectangle(R[n], fill=(236, 238, 236))
    props(R[n], 0.0, 0.35)
    dc.rectangle(caja_rel(n, 0, 0, 1, 0.16), fill=(36, 70, 118))
    texto(caja_rel(n, 0, 0, 1, 0.16), "ÁREA TÉCNICA · L-01", F(26), (230, 236, 244))
    texto(caja_rel(n, 0.02, 0.18, 0.98, 0.66), "LABORATORIO", F(92), (22, 26, 34), relieve=150)
    texto(caja_rel(n, 0.02, 0.64, 0.98, 0.94), "— Autorizado —", F(52, False), (150, 30, 30), relieve=145)
    dc.rectangle(R[n], outline=(36, 70, 118), width=7)

    # 3) Pegatina de voltaje: triángulo amarillo con rayo
    n = "pegatina_voltaje"
    x0, y0, x1, y1 = R[n]
    dc.rectangle(R[n], fill=(245, 196, 20))
    props(R[n], 0.0, 0.45, 132)
    cx = (x0 + x1) / 2
    tri = [(cx, y0 + 16), (x1 - 16, y0 + 168), (x0 + 16, y0 + 168)]
    dc.polygon(tri, fill=(20, 20, 20))
    tri2 = [(cx, y0 + 40), (x1 - 34, y0 + 156), (x0 + 34, y0 + 156)]
    dc.polygon(tri2, fill=(245, 196, 20))
    rayo = [(cx + 8, y0 + 62), (cx - 22, y0 + 112), (cx - 2, y0 + 112), (cx - 12, y0 + 148), (cx + 22, y0 + 96),
            (cx + 2, y0 + 96)]
    dc.polygon(rayo, fill=(20, 20, 20))
    texto((x0, y0 + 172, x1, y0 + 222), "400 V", F(46), (20, 20, 20))
    texto((x0, y0 + 220, x1, y1 - 4), "PELIGRO", F(30), (20, 20, 20))

    # 4) Reciclaje + rayo (residuos electrónicos)
    n = "reciclaje"
    x0, y0, x1, y1 = R[n]
    dc.rectangle(R[n], fill=(238, 240, 236))
    props(R[n], 0.0, 0.4, 132)
    cx, cy, rr = (x0 + x1) / 2, y0 + 165, 120
    verde = (28, 140, 70)
    for k in range(3):
        a0 = k * 120 + 20
        dc.arc((cx - rr, cy - rr, cx + rr, cy + rr), a0, a0 + 85, fill=verde, width=30)
        a = math.radians(a0 + 85)
        px, py = cx + rr * math.cos(a), cy + rr * math.sin(a)
        ta = a + math.pi / 2
        dc.polygon([(px + 34 * math.cos(ta), py + 34 * math.sin(ta)),
                    (px + 30 * math.cos(a), py + 30 * math.sin(a)),
                    (px - 30 * math.cos(a), py - 30 * math.sin(a))], fill=verde)
    rayo = [(cx + 14, cy - 70), (cx - 36, cy + 10), (cx - 4, cy + 10), (cx - 20, cy + 72), (cx + 38, cy - 12),
            (cx + 6, cy - 12)]
    dc.polygon(rayo, fill=(245, 196, 20), outline=(20, 20, 20))
    texto((x0, y0 + 300, x1, y0 + 350), "RAEE", F(46), (20, 60, 36))
    texto((x0, y0 + 346, x1, y1 - 6), "Residuos electrónicos", F(28, False), (30, 30, 30))
    dc.rectangle(R[n], outline=verde, width=8)

    # 5) Zona vigilada
    n = "zona_vigilada"
    x0, y0, x1, y1 = R[n]
    dc.rectangle(R[n], fill=(28, 74, 140))
    props(R[n], 0.0, 0.38, 132)
    dc.rectangle((x0 + 10, y0 + 10, x1 - 10, y1 - 10), outline=(240, 240, 240), width=5)
    # icono de cámara
    dc.rectangle((x0 + 40, y0 + 52, x0 + 150, y0 + 108), fill=(240, 240, 240))
    dc.polygon([(x0 + 150, y0 + 66), (x0 + 186, y0 + 50), (x0 + 186, y0 + 110), (x0 + 150, y0 + 94)],
               fill=(240, 240, 240))
    dc.rectangle((x0 + 84, y0 + 108, x0 + 100, y0 + 150), fill=(240, 240, 240))
    texto((x0 + 200, y0 + 30, x1 - 20, y0 + 140), "ZONA", F(64), (250, 250, 250))
    texto((x0 + 16, y0 + 150, x1 - 16, y0 + 210), "VIGILADA 24 h", F(46), (250, 250, 250))
    texto((x0 + 16, y0 + 210, x1 - 16, y1 - 18), "Equipo de laboratorio", F(24, False), (210, 222, 240))

    # 6) Placa del generador
    n = "placa_generador"
    dc.rectangle(R[n], fill=(32, 34, 36))
    props(R[n], 0.6, 0.4, 128)
    texto(caja_rel(n, 0.03, 0.06, 0.97, 0.5), "GENERADOR DE EMERGENCIA", F(46), (240, 196, 30), relieve=150)
    texto(caja_rel(n, 0.03, 0.5, 0.97, 0.94), "DIÉSEL · 12 kVA · 400 V · ARRANQUE MANUAL", F(28, False),
          (210, 210, 210), relieve=145)
    dc.rectangle(R[n], outline=(240, 196, 30), width=6)

    # 7) Pegatina del prototipo (panel solar del suelo)
    n = "prototipo"
    dc.rectangle(R[n], fill=(236, 120, 30))
    props(R[n], 0.0, 0.5, 132)
    texto(caja_rel(n, 0.03, 0.04, 0.97, 0.46), "PROTOTIPO FV-7", F(64), (20, 20, 20))
    texto(caja_rel(n, 0.03, 0.48, 0.97, 0.94), "Experimental · medir cada 2 h", F(34, False), (20, 20, 20))

    # 8) Teclado numérico (con pantalla verde arriba)
    n = "teclado"
    x0, y0, x1, y1 = R[n]
    dc.rectangle(R[n], fill=(26, 28, 32))
    props(R[n], 0.2, 0.45, 110)
    pant = caja_rel(n, 0.08, 0.05, 0.7, 0.2)
    dc.rectangle(pant, fill=(10, 40, 24))
    props(pant, 0.0, 0.1, 100, 0)
    texto(pant, "- - - -", F(30, mono=True), (90, 255, 140), emision=255)
    teclas = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]
    for i, t in enumerate(teclas):
        cx0 = x0 + 22 + (i % 3) * 54
        cy0 = y0 + 76 + (i // 3) * 54
        caja = (cx0, cy0, cx0 + 44, cy0 + 44)
        dc.rounded_rectangle(caja, 7, fill=(120, 126, 132))
        dp.rounded_rectangle(caja, 7, fill=(204, 120, 190, 0))
        texto(caja, t, F(28), (20, 22, 24))
    led = caja_rel(n, 0.77, 0.08, 0.9, 0.16)
    dc.ellipse(led, fill=(80, 255, 120))
    dp.ellipse(led, fill=(0, 30, 150, 255))

    # 9) Lector de tarjeta
    n = "lector"
    x0, y0, x1, y1 = R[n]
    dc.rectangle(R[n], fill=(36, 38, 42))
    props(R[n], 0.2, 0.4, 128)
    ranura = (x0 + 20, y0 + 40, x1 - 20, y0 + 58)
    dc.rectangle(ranura, fill=(6, 6, 8))
    dp.rectangle(ranura, fill=(0, 200, 40, 0))
    dc.ellipse((x1 - 40, y0 + 72, x1 - 22, y0 + 90), fill=(255, 70, 50))
    dp.ellipse((x1 - 40, y0 + 72, x1 - 22, y0 + 90), fill=(0, 30, 150, 255))
    texto((x0 + 10, y0 + 66, x1 - 50, y1 - 4), "TARJETA", F(20), (190, 190, 190))

    # 10) Cuadro general
    n = "cuadro_general"
    dc.rectangle(R[n], fill=(238, 238, 232))
    props(R[n], 0.0, 0.4, 132)
    texto(caja_rel(n, 0.03, 0.05, 0.97, 0.55), "CUADRO GENERAL", F(62), (22, 22, 26))
    texto(caja_rel(n, 0.03, 0.55, 0.97, 0.95), "230/400 V · C1 casa · C2 lab · C3 techo · C4 FV", F(26, False),
          (40, 40, 44))
    dc.rectangle(R[n], outline=(22, 22, 26), width=4)

    n = "distribucion"
    dc.rectangle(R[n], fill=(238, 238, 232))
    props(R[n], 0.0, 0.4, 132)
    texto(caja_rel(n, 0.03, 0.05, 0.97, 0.58), "DISTRIBUCIÓN TECHO", F(44), (22, 22, 26))
    texto(caja_rel(n, 0.03, 0.58, 0.97, 0.95), "FV-1·2·3 · ANT-P · ANT-D · METEO", F(24, False), (40, 40, 44))
    dc.rectangle(R[n], outline=(22, 22, 26), width=4)

    # 11) Pantallas (emisión)
    n = "lcd_generador"
    dc.rectangle(R[n], fill=(8, 30, 20))
    props(R[n], 0.0, 0.08, 128, 40)
    texto(caja_rel(n, 0.05, 0.05, 0.95, 0.5), "LISTO", F(52, mono=True), (110, 255, 150), emision=255)
    texto(caja_rel(n, 0.05, 0.5, 0.95, 0.95), "COMB 98%", F(36, mono=True), (110, 255, 150), emision=230)

    n = "osciloscopio"
    x0, y0, x1, y1 = R[n]
    dc.rectangle(R[n], fill=(6, 18, 14))
    props(R[n], 0.0, 0.08, 128, 30)
    for k in range(1, 8):
        xx = x0 + k * (x1 - x0) / 8
        dc.line((xx, y0, xx, y1), fill=(20, 60, 40), width=2)
    for k in range(1, 6):
        yy = y0 + k * (y1 - y0) / 6
        dc.line((x0, yy, x1, yy), fill=(20, 60, 40), width=2)
    pts = [(x0 + i, (y0 + y1) / 2 + 80 * math.sin(i * 0.05) * math.exp(-i * 0.003)) for i in range(0, x1 - x0, 3)]
    dc.line(pts, fill=(120, 255, 160), width=5)
    capa = Image.new("L", (TAM, TAM), 0)
    ImageDraw.Draw(capa).line(pts, fill=255, width=7)
    r, g, b, a = pro.split()
    a = Image.composite(Image.new("L", (TAM, TAM), 255), a, capa)
    pro.paste(Image.merge("RGBA", (r, g, b, a)))

    n = "monitor"
    x0, y0, x1, y1 = R[n]
    dc.rectangle(R[n], fill=(10, 18, 30))
    props(R[n], 0.0, 0.08, 128, 60)
    capa = Image.new("L", (TAM, TAM), 0)
    dcap = ImageDraw.Draw(capa)
    import random
    rnd = random.Random(7)
    y = y0 + 20
    while y < y1 - 30:
        sangria = rnd.choice([0, 0, 30, 60])
        largo = rnd.randint(80, (x1 - x0) - 80 - sangria)
        c = rnd.choice([(120, 200, 255), (160, 240, 180), (230, 230, 240), (255, 200, 120)])
        dc.rectangle((x0 + 24 + sangria, y, x0 + 24 + sangria + largo, y + 10), fill=c)
        dcap.rectangle((x0 + 24 + sangria, y, x0 + 24 + sangria + largo, y + 10), fill=220)
        y += 24
    r, g, b, a = pro.split()
    a = Image.composite(Image.new("L", (TAM, TAM), 230), a, capa)
    pro.paste(Image.merge("RGBA", (r, g, b, a)))

    # 12) Etiqueta del cuaderno (a mano)
    n = "cuaderno"
    dc.rectangle(R[n], fill=(236, 230, 210))
    props(R[n], 0.0, 0.8, 130)
    texto(caja_rel(n, 0.05, 0.05, 0.95, 0.55), "IDEAS", F(54), (30, 40, 90))
    texto(caja_rel(n, 0.05, 0.55, 0.95, 0.95), "vol. 14", F(34, False), (30, 40, 90))

    for n, t, cf, ct in (("arranque", "ARRANQUE", (238, 238, 232), (20, 110, 40)),
                         ("parada", "PARADA", (238, 238, 232), (170, 20, 20)),
                         ("auto_persiana", "AUTO", (40, 42, 46), (200, 210, 220)),
                         ("mantenimiento", "Revisado 14/03 · K.", (238, 238, 232), (30, 30, 34))):
        dc.rectangle(R[n], fill=cf)
        props(R[n], 0.0, 0.45, 132)
        texto(R[n], t, F(40 if n != "mantenimiento" else 36), ct)
        dc.rectangle(R[n], outline=ct, width=4)

    for t in ETIQUETAS:
        n = f"et_{t}"
        dc.rectangle(R[n], fill=(244, 244, 240))
        props(R[n], 0.0, 0.5, 134)
        texto(R[n], t, F(52 if len(t) <= 5 else 42), (16, 16, 18))
        dc.rectangle(R[n], outline=(16, 16, 18), width=4)

    # un poco de suavizado para que el horneado no tenga dientes de sierra
    col = col.filter(ImageFilter.SMOOTH)
    rc = os.path.join(carpeta, "letreros_color.png")
    rp = os.path.join(carpeta, "letreros_props.png")
    col.save(rc)
    pro.save(rp)
    return rc, rp
