"""
Texturas pintadas a mano (con Pillow) para la casa de la familia.

Son las que cuentan la historia y no se pueden hacer con ruido procedural:
  * la puerta amarilla desconchada con las marcas de altura de los niños,
  * los marcos con la franja azul que pintaron los niños (irregular, con gotas y huecos),
  * el dibujo de la familia pegado en la ventana,
  * la placa del «3» con pegatinas de estrellas,
  * el felpudo de colores,
  * el suelo de hormigón de la entrada con la rayuela de tiza,
  * la loseta de los paneles metálicos de las paredes (juntas, remaches, chorretones),
  * el tablero de células del panel solar.

Cada función devuelve imágenes PIL: color (RGB), rugosidad (L, 0 = brillo) y altura (L, 128 = plano) cuando hace
falta. El script de Blender las guarda en una carpeta temporal y las usa como fuente al hornear el atlas.

Todas las medidas de entrada están en studs y se pintan a una resolución fija por stud (PX), así un trazo de
rotulador mide lo mismo en la puerta que en el marco.
"""

import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

PX = 220  # píxeles por stud en las texturas fuente (el atlas final tiene menos: esto es para que el horneado no pierda)

FUENTES = {
    "mano": "/usr/share/fonts/truetype/freefont/FreeSansBoldOblique.ttf",
    "negrita": "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "normal": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
}


def _fuente(tipo, tam):
    try:
        return ImageFont.truetype(FUENTES[tipo], tam)
    except OSError:
        return ImageFont.load_default(tam)


# ----------------------------------------------------------------------------------------------------------------
# Utilidades: ruido, mezclas y trazos a mano alzada
# ----------------------------------------------------------------------------------------------------------------


def ruido(w, h, celdas, semilla, octavas=4, estirar=(1.0, 1.0)):
    """Ruido de valor (0..1) suave, sumando octavas. `celdas` = tamaño de la rejilla de la octava más grande."""
    rng = np.random.default_rng(semilla)
    total = np.zeros((h, w), np.float32)
    amp, suma = 1.0, 0.0
    for o in range(octavas):
        cx = max(2, int(celdas * (2 ** o) * estirar[0]))
        cy = max(2, int(celdas * (2 ** o) * h / max(w, 1) * estirar[1]))
        base = (rng.random((cy, cx)) * 255).astype(np.uint8)
        capa = np.asarray(Image.fromarray(base).resize((w, h), Image.BICUBIC), np.float32) / 255.0
        total += capa * amp
        suma += amp
        amp *= 0.5
    return np.clip(total / suma, 0, 1)


def a_img(arr, modo="L"):
    if modo == "L":
        return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), "L")
    return Image.fromarray(np.clip(arr * 255, 0, 255).astype(np.uint8), "RGB")


def color_arr(c):
    return np.array(c, np.float32) / 255.0


def mezclar(fondo, color, mascara):
    """fondo (h,w,3) + color (3,) o (h,w,3) con máscara (h,w) 0..1."""
    m = mascara[..., None]
    return fondo * (1 - m) + np.asarray(color, np.float32) * m


def trazo(d, puntos, color, ancho, temblor=0.0, rng=None):
    """Línea a mano alzada: subdivide y mueve un poco cada punto, con extremos redondeados."""
    rng = rng or random.Random(1)
    pts = []
    for (x0, y0), (x1, y1) in zip(puntos[:-1], puntos[1:]):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0) / 6))
        for i in range(n):
            t = i / n
            pts.append((x0 + (x1 - x0) * t + rng.uniform(-temblor, temblor),
                        y0 + (y1 - y0) * t + rng.uniform(-temblor, temblor)))
    pts.append(puntos[-1])
    d.line(pts, fill=color, width=int(ancho), joint="curve")
    r = ancho / 2
    for x, y in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=color)


def estrella(cx, cy, r_ext, r_int=None, puntas=5, giro=0.0):
    r_int = r_int or r_ext * 0.45
    pts = []
    for i in range(puntas * 2):
        a = giro - math.pi / 2 + i * math.pi / puntas
        r = r_ext if i % 2 == 0 else r_int
        pts.append((cx + math.cos(a) * r, cy + math.sin(a) * r))
    return pts


def texto_a_mano(img, xy, texto, color, tam, giro=0.0, tipo="mano"):
    """Texto con un giro leve (rotulador): se pinta en una capa aparte y se pega."""
    f = _fuente(tipo, tam)
    caja = f.getbbox(texto)
    w, h = caja[2] + 8, caja[3] + 8
    capa = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(capa).text((4, 4), texto, font=f, fill=color)
    capa = capa.rotate(giro, expand=True, resample=Image.BICUBIC)
    img.paste(capa, (int(xy[0]), int(xy[1])), capa)


# ----------------------------------------------------------------------------------------------------------------
# Puerta amarilla
# ----------------------------------------------------------------------------------------------------------------


def puerta(ancho, alto, marcas, manija, manija_nino, semilla=7):
    """
    Cara exterior de la hoja de la puerta.
      ancho, alto: studs de la hoja.
      marcas: [(altura_studs, texto, (r,g,b))] rayitas de rotulador con nombre y edad.
      manija, manija_nino: (x, z) en studs (desde la esquina inferior izquierda vista desde fuera).
    La bisagra está a la izquierda (x = 0). Devuelve (color, rugosidad, altura).
    """
    w, h = int(ancho * PX), int(alto * PX)
    rng = random.Random(semilla)

    def px(x, z):  # studs -> píxel (y hacia abajo)
        return x * PX, (alto - z) * PX

    # Madera de debajo: tablas verticales con veta.
    veta = ruido(w, h, 3, semilla + 1, 5, estirar=(6.0, 0.25))
    madera = np.stack([0.42 + 0.16 * veta, 0.27 + 0.10 * veta, 0.15 + 0.06 * veta], -1)
    for i in range(1, 4):  # juntas entre tablas
        x = int(w * i / 4)
        madera[:, max(0, x - 2):x + 2] *= 0.55

    # Pintura amarilla con pinceladas verticales y variación (la luz del sol la ha comido arriba).
    pincel = ruido(w, h, 6, semilla + 2, 4, estirar=(4.0, 0.3))
    manchas = ruido(w, h, 3, semilla + 3, 3)
    amarillo = np.stack([0.98 - 0.05 * pincel, 0.77 - 0.07 * pincel + 0.03 * manchas, 0.16 + 0.05 * manchas], -1)
    zz = np.linspace(1, 0, h)[:, None]
    amarillo *= (0.93 + 0.07 * zz[..., None])  # un poco más clara arriba, más sucia abajo

    # Desconchones: más abajo (patadas, la bici), en los cantos y alrededor de las manijas.
    base = ruido(w, h, 9, semilla + 4, 5)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    zst = alto - yy / PX
    xst = xx / PX
    prob = 0.18 * np.exp(-zst / 0.7)  # cerca del suelo
    prob += 0.16 * np.exp(-np.minimum(xst, ancho - xst) / 0.10)  # cantos
    prob += 0.12 * np.exp(-np.minimum(zst, alto - zst) / 0.08)
    for mx, mz in (manija, manija_nino):
        prob += 0.20 * np.exp(-((xst - mx) ** 2 + (zst - mz) ** 2) / 0.05)
    desconchon = (base + prob) > 0.80
    desconchon = np.asarray(
        a_img(desconchon.astype(np.float32)).filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.MinFilter(3)),
        np.float32) / 255
    # Borde de la pintura levantado (más claro) alrededor de cada desconchón.
    borde = np.asarray(a_img(desconchon).filter(ImageFilter.MaxFilter(5)), np.float32) / 255 - desconchon

    col = mezclar(amarillo, madera, desconchon)
    col = mezclar(col, (1.0, 0.90, 0.55), borde * 0.6)

    # Paneles rehundidos (4): la sombra de la ranura va en el color y en la altura.
    altura = np.full((h, w), 0.5, np.float32)
    ranura = np.zeros((h, w), np.float32)
    m = 0.22 * PX
    medio_x = w / 2
    filas = [(0.18, 0.47), (0.53, 0.90)]  # fracción de alto (desde arriba)
    for (fy0, fy1) in filas:
        for (x0, x1) in ((m, medio_x - m * 0.4), (medio_x + m * 0.4, w - m)):
            y0, y1 = fy0 * h, fy1 * h
            d = 0.035 * PX
            ranura[int(y0):int(y1), int(x0):int(x0 + d)] = 1
            ranura[int(y0):int(y1), int(x1 - d):int(x1)] = 1
            ranura[int(y0):int(y0 + d), int(x0):int(x1)] = 1
            ranura[int(y1 - d):int(y1), int(x0):int(x1)] = 1
            altura[int(y0 + d):int(y1 - d), int(x0 + d):int(x1 - d)] = 0.42
    ranura = np.asarray(a_img(ranura).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
    altura -= ranura * 0.25
    altura -= desconchon * 0.12  # la pintura tiene grosor
    col *= (1 - 0.35 * ranura)[..., None]

    # Mancha de manitas sucias junto a la manija baja (de quien vuelve del barro).
    mx, mz = manija_nino
    sucio = np.exp(-(((xst - mx + 0.12) / 0.16) ** 2 + ((zst - mz + 0.05) / 0.22) ** 2))
    sucio *= ruido(w, h, 30, semilla + 9, 2) > 0.45
    col = mezclar(col, (0.36, 0.30, 0.22), sucio * 0.35)
    # Mugre general abajo.
    col *= (1 - 0.18 * np.exp(-zst / 0.35))[..., None]

    img = a_img(col, "RGB")
    d = ImageDraw.Draw(img)

    # Marcas de altura de los niños: rayita de rotulador + nombre y edad, en el lado de las bisagras.
    for z, texto, color in marcas:
        x0, y = px(0.10, z)
        largo = 0.42 * PX
        trazo(d, [(x0, y + rng.uniform(-2, 2)), (x0 + largo, y + rng.uniform(-3, 3))], color, 0.028 * PX, 0.6, rng)
        texto_a_mano(img, (x0 + largo + 0.03 * PX, y - 0.11 * PX), texto, color, int(0.13 * PX), rng.uniform(-6, 4))
    # Una cuarta rayita a lápiz, muy flojita, más alta: «papá» midiéndose en broma.
    x0, y = px(0.10, alto * 0.83)
    trazo(d, [(x0, y), (x0 + 0.30 * PX, y + 2)], (110, 104, 92), 0.012 * PX, 0.4, rng)

    rug = 0.42 + 0.10 * pincel + 0.35 * desconchon + 0.15 * sucio
    alt = np.clip(altura, 0, 1)
    return img, a_img(rug), a_img(alt)


def puerta_interior(ancho, alto, semilla=8):
    """Cara interior y cantos: el mismo amarillo, cuidado (dentro no da el sol ni la bici)."""
    w, h = int(ancho * PX * 0.5), int(alto * PX * 0.5)
    pincel = ruido(w, h, 6, semilla, 4, estirar=(4.0, 0.3))
    col = np.stack([0.97 - 0.04 * pincel, 0.79 - 0.05 * pincel, 0.20 + 0.03 * pincel], -1)
    return a_img(col, "RGB")


# ----------------------------------------------------------------------------------------------------------------
# Marcos con la franja azul de los niños
# ----------------------------------------------------------------------------------------------------------------


def marco_pintado(ancho, alto, grosor_marco, cobertura=1.0, semilla=11):
    """
    Cara frontal de un marco de ventana (anillo) visto de frente, de ancho×alto studs (exterior) y lados de
    `grosor_marco`. Metal gris con una franja azul claro pintada a brocha por niños: irregular, con huecos,
    goterones hacia abajo y algún dedazo. `cobertura` < 1 deja el trabajo a medias (se aburrieron).
    """
    w, h = int(ancho * PX), int(alto * PX)
    rng = random.Random(semilla)
    cepillado = ruido(w, h, 4, semilla, 4, estirar=(5.0, 0.3))
    metal = np.stack([0.60 + 0.06 * cepillado] * 3, -1) * np.array([0.98, 1.0, 1.03])
    col = metal.copy()

    mascara = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(mascara)
    g = grosor_marco * PX
    # Recorrido del anillo por el centro del lado, en sentido horario empezando abajo a la izquierda.
    camino = [(g / 2, h - g / 2), (g / 2, g / 2), (w - g / 2, g / 2), (w - g / 2, h - g / 2), (g / 2, h - g / 2)]
    largo_total = sum(math.dist(a, b) for a, b in zip(camino[:-1], camino[1:]))
    hasta = largo_total * cobertura
    recorrido = 0.0
    for a, b in zip(camino[:-1], camino[1:]):
        seg = math.dist(a, b)
        n = int(seg / (0.05 * PX)) + 1
        for i in range(n):
            if recorrido + seg * i / n > hasta:
                break
            t = i / n
            x = a[0] + (b[0] - a[0]) * t + rng.uniform(-0.03, 0.03) * PX
            y = a[1] + (b[1] - a[1]) * t + rng.uniform(-0.03, 0.03) * PX
            r = g * rng.uniform(0.38, 0.62)
            if rng.random() < 0.06:  # hueco donde no llegó la brocha
                continue
            d.ellipse((x - r, y - r * rng.uniform(0.7, 1.2), x + r, y + r * rng.uniform(0.7, 1.2)),
                      fill=int(255 * rng.uniform(0.85, 1.0)))
        recorrido += seg
    # Goterones: desde el lado de abajo y de los laterales, hacia abajo.
    for _ in range(int(9 * cobertura) + 1):
        x = rng.uniform(g * 0.3, w - g * 0.3) if rng.random() < 0.6 else rng.choice((g * 0.5, w - g * 0.5))
        y = rng.uniform(h - g * 0.8, h - g * 0.3) if rng.random() < 0.6 else rng.uniform(g, h - g)
        l = rng.uniform(0.05, 0.16) * PX
        trazo(d, [(x, y), (x + rng.uniform(-2, 2), y + l)], 255, rng.uniform(0.012, 0.022) * PX)
        d.ellipse((x - 4, y + l - 3, x + 4, y + l + 6), fill=255)
    # Pintura que se pasó del marco hacia el exterior (borde de fuera) en algunos sitios.
    for _ in range(5):
        x, y = rng.uniform(0, w), rng.choice((rng.uniform(0, 6), rng.uniform(h - 6, h)))
        d.ellipse((x - 10, y - 5, x + 12, y + 6), fill=220)
    m = np.asarray(mascara.filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255
    if cobertura < 1:
        # Donde lo dejaron: un brochazo final arrastrado (pintura casi seca).
        pass
    grano = ruido(w, h, 20, semilla + 5, 3)
    azul = np.stack([0.50 + 0.05 * grano, 0.80 + 0.04 * grano, 0.95 + 0.02 * grano], -1)
    # La pintura de niño tiene capas: zonas más finas dejan ver el metal.
    fina = (ruido(w, h, 10, semilla + 6, 3) < 0.35).astype(np.float32) * 0.45
    col = mezclar(col, azul, m * (1 - fina))
    img = a_img(col, "RGB")
    # Huella de un dedito azul en la pared del marco (abajo a la derecha).
    dd = ImageDraw.Draw(img)
    fx, fy = w - g * 0.5 + rng.uniform(-8, 8), h - g * 1.6
    for k in range(3):
        dd.ellipse((fx - 10 + k, fy - 13 + k, fx + 10 - k, fy + 13 - k), outline=(120, 190, 235), width=2)
    rug = 0.38 + 0.10 * cepillado + 0.25 * m
    alt = 0.5 + 0.06 * m - 0.02 * fina
    return img, a_img(rug), a_img(alt)


# ----------------------------------------------------------------------------------------------------------------
# Dibujo infantil pegado en la ventana
# ----------------------------------------------------------------------------------------------------------------


def dibujo_familia(ancho, alto, semilla=21):
    """Garabato con ceras: la casa, papá, mamá y los dos niños de la mano, un sol, estrellas y un corazón."""
    w, h = int(ancho * PX * 1.4), int(alto * PX * 1.4)
    rng = random.Random(semilla)
    papel = ruido(w, h, 8, semilla, 3)
    base = np.stack([0.97 - 0.03 * papel, 0.96 - 0.03 * papel, 0.92 - 0.04 * papel], -1)
    img = a_img(base, "RGB")
    d = ImageDraw.Draw(img)
    s = w / 100.0  # unidades «de dibujo»

    def cera(pts, color, ancho=1.6):
        for k in range(2):  # dos pasadas desplazadas: textura de cera
            trazo(d, [(x * s + rng.uniform(-0.3, 0.3) * s, y * s + rng.uniform(-0.3, 0.3) * s) for x, y in pts],
                  color, ancho * s * (0.8 if k else 1.0), 0.35 * s, rng)

    # Suelo verde.
    cera([(3, 66), (30, 64), (60, 67), (97, 64)], (70, 170, 70), 2.4)
    # Casa (cuadrado y tejado) a la izquierda.
    cera([(8, 64), (8, 40), (30, 40), (30, 64)], (220, 60, 50))
    cera([(5, 41), (19, 28), (33, 41)], (90, 90, 95), 2.0)
    cera([(16, 64), (16, 52), (22, 52), (22, 64)], (240, 190, 30), 1.8)  # puerta amarilla, claro
    # Familia: papá, mamá (con falda), dos niños pequeños.
    def persona(x, alto_p, color, falda=False):
        cab = alto_p * 0.22
        d.ellipse(((x - cab / 2) * s, (64 - alto_p) * s, (x + cab / 2) * s, (64 - alto_p + cab) * s),
                  outline=(60, 40, 30), width=int(1.2 * s))
        cuello = 64 - alto_p + cab
        cadera = 64 - alto_p * 0.38
        if falda:
            cera([(x, cuello), (x - alto_p * 0.16, cadera), (x + alto_p * 0.16, cadera), (x, cuello)], color, 1.6)
        else:
            cera([(x, cuello), (x, cadera)], color, 1.8)
        cera([(x - alto_p * 0.08, 64), (x, cadera), (x + alto_p * 0.08, 64)], (60, 60, 160), 1.4)
        brazo = cuello + alto_p * 0.10
        cera([(x - alto_p * 0.20, brazo + alto_p * 0.08), (x, brazo), (x + alto_p * 0.20, brazo + alto_p * 0.08)],
             color, 1.3)
        # Sonrisa.
        cy = 64 - alto_p + cab * 0.62
        d.arc(((x - cab * 0.25) * s, (cy - cab * 0.18) * s, (x + cab * 0.25) * s, (cy + cab * 0.12) * s), 10, 170,
              fill=(200, 40, 40), width=int(0.8 * s))
    persona(42, 30, (40, 110, 210))
    persona(55, 27, (230, 70, 150), falda=True)
    persona(66, 17, (250, 150, 30))
    persona(75, 14, (120, 200, 60))
    # Sol con rayos en la esquina, estrellas en el cielo (somos del espacio) y un corazón.
    cx, cy, r = 88, 12, 6
    d.ellipse(((cx - r) * s, (cy - r) * s, (cx + r) * s, (cy + r) * s), fill=(255, 205, 40), outline=(245, 160, 20),
              width=int(s))
    for k in range(9):
        a = k * 2 * math.pi / 9
        cera([(cx + math.cos(a) * 8, cy + math.sin(a) * 8), (cx + math.cos(a) * 12, cy + math.sin(a) * 12)],
             (245, 170, 20), 1.0)
    for (x, y, r_, c) in ((45, 10, 3.5, (250, 200, 40)), (60, 18, 2.8, (90, 170, 240)), (70, 7, 2.4, (250, 120, 180)),
                          (37, 22, 2.2, (250, 200, 40)), (8, 12, 3.0, (150, 110, 230))):
        d.polygon([(px_ * s, py_ * s) for px_, py_ in estrella(x, y, r_, giro=rng.uniform(-0.3, 0.3))], fill=c)
    corazon = []
    for k in range(40):
        t = k / 40 * 2 * math.pi
        corazon.append(((49 + 0.22 * 16 * math.sin(t) ** 3) * s,
                        (40 - 0.22 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))) * s))
    d.polygon(corazon, fill=(230, 50, 70))
    # Firma torcida.
    texto_a_mano(img, (6 * s, 68 * s), "MIA y LEO", (60, 60, 200), int(5.2 * s), rng.uniform(-4, 4))
    # Celo en las esquinas (brillante, un poco amarillento).
    capa = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dc = ImageDraw.Draw(capa)
    for (x, y, giro) in ((0, 0, 40), (w, 0, -40), (0, h, -40), (w, h, 40)):
        lw, lh = 14 * s, 4.5 * s
        rect = [(-lw / 2, -lh / 2), (lw / 2, -lh / 2), (lw / 2, lh / 2), (-lw / 2, lh / 2)]
        a = math.radians(giro)
        pts = [(x + px_ * math.cos(a) - py_ * math.sin(a), y + px_ * math.sin(a) + py_ * math.cos(a)) for px_, py_ in rect]
        dc.polygon(pts, fill=(250, 245, 200, 110))
    img.paste(capa, (0, 0), capa)
    # Arrugas suaves del papel.
    pliegue = ruido(w, h, 3, semilla + 3, 2)
    arr = np.asarray(img, np.float32) / 255 * (0.94 + 0.06 * pliegue[..., None])
    return a_img(arr, "RGB")


# ----------------------------------------------------------------------------------------------------------------
# Placa del número con pegatinas
# ----------------------------------------------------------------------------------------------------------------


def placa_numero(lado, semilla=31):
    w = h = int(lado * PX * 1.6)
    rng = random.Random(semilla)
    grano = ruido(w, h, 6, semilla, 3)
    fondo = np.stack([0.11 + 0.03 * grano, 0.24 + 0.04 * grano, 0.42 + 0.04 * grano], -1)  # esmalte azul marino
    img = a_img(fondo, "RGB")
    d = ImageDraw.Draw(img)
    b = int(w * 0.07)
    d.rounded_rectangle((b, b, w - b, h - b), radius=int(w * 0.08), outline=(230, 232, 236), width=int(w * 0.03))
    f = _fuente("negrita", int(h * 0.62))
    caja = d.textbbox((0, 0), "3", font=f)
    d.text(((w - (caja[2] - caja[0])) / 2 - caja[0], (h - (caja[3] - caja[1])) / 2 - caja[1]), "3", font=f,
           fill=(240, 242, 246))
    # Pegatinas de estrellas alrededor del número, cada una de un color y torcida.
    colores = [(255, 210, 40), (255, 120, 190), (110, 220, 120), (90, 200, 255), (255, 150, 50), (190, 130, 255)]
    sitios = [(0.20, 0.22), (0.80, 0.18), (0.83, 0.55), (0.78, 0.84), (0.22, 0.80), (0.16, 0.50), (0.50, 0.12)]
    alt = Image.new("L", (w, h), 128)
    da = ImageDraw.Draw(alt)
    for i, (sx, sy) in enumerate(sitios):
        r = w * rng.uniform(0.07, 0.10)
        pts = estrella(sx * w, sy * h, r, giro=rng.uniform(-0.5, 0.5))
        d.polygon(pts, fill=colores[i % len(colores)], outline=(255, 255, 255))
        da.polygon(pts, fill=150)
    # Una pegatina medio despegada (esquina levantada, más clara).
    d.polygon(estrella(0.5 * w, 0.88 * h, w * 0.07, giro=0.4), fill=(250, 250, 210))
    rug = Image.new("L", (w, h), 90)
    return img, rug, alt


# ----------------------------------------------------------------------------------------------------------------
# Felpudo
# ----------------------------------------------------------------------------------------------------------------


def felpudo(ancho, alto, semilla=41):
    w, h = int(ancho * PX), int(alto * PX)
    rng = random.Random(semilla)
    img = Image.new("RGB", (w, h), (60, 45, 40))
    d = ImageDraw.Draw(img)
    colores = [(235, 70, 60), (250, 160, 40), (250, 215, 60), (90, 190, 90), (60, 150, 230), (160, 90, 210)]
    n = len(colores)
    m = int(0.05 * PX)
    for i, c in enumerate(colores):  # franjas diagonales tipo arcoíris
        x0 = m + (w - 2 * m) * i / n
        x1 = m + (w - 2 * m) * (i + 1) / n
        d.polygon([(x0 + 10, m), (x1 + 10, m), (x1 - 10, h - m), (x0 - 10, h - m)], fill=c)
    f = _fuente("negrita", int(h * 0.42))
    caja = d.textbbox((0, 0), "HOLA", font=f)
    d.text(((w - caja[2]) / 2, (h - caja[3]) / 2 - caja[1] / 2), "HOLA", font=f, fill=(250, 248, 240))
    # Fibras: ruido fino oscuro + desgaste en el centro (donde se pisa).
    fibra = ruido(w, h, 60, semilla, 2)
    yy, xx = np.mgrid[0:h, 0:w]
    pisado = np.exp(-(((xx - w / 2) / (w * 0.3)) ** 2 + ((yy - h / 2) / (h * 0.35)) ** 2))
    arr = np.asarray(img, np.float32) / 255
    arr *= (0.78 + 0.22 * fibra)[..., None]
    arr = mezclar(arr, (0.42, 0.36, 0.30), pisado * 0.28)
    alt = 0.5 + 0.25 * (fibra - 0.5)
    alt[:m, :] = alt[-m:, :] = 0.62  # ribete
    alt[:, :m] = alt[:, -m:] = 0.62
    return a_img(arr, "RGB"), a_img(np.full((h, w), 0.95)), a_img(alt)


# ----------------------------------------------------------------------------------------------------------------
# Suelo de la entrada con la rayuela
# ----------------------------------------------------------------------------------------------------------------


def suelo_entrada(x0, x1, y0, y1, rayuela, tierra, juntas_x, semilla=51):
    """
    Losa de hormigón vista desde arriba. Coordenadas en studs del mundo (x a la derecha, y hacia la casa).
      rayuela: (x_inicio, y_centro, lado_casilla) la rayuela se dibuja a lo largo de +x.
      tierra: [(x, y, radio)] manchas de tierra derramada (la maceta rota).
      juntas_x: posiciones x de las juntas de dilatación.
    """
    ancho, fondo = x1 - x0, y1 - y0
    w, h = int(ancho * PX * 0.7), int(fondo * PX * 0.7)
    k = w / ancho
    rng = random.Random(semilla)

    def px(x, y):
        return (x - x0) * k, (y1 - y) * k  # y del mundo hacia arriba en la imagen = hacia la casa

    grano = ruido(w, h, 60, semilla, 3)
    manchas = ruido(w, h, 4, semilla + 1, 4)
    hormigon = np.stack([0.58 + 0.05 * grano - 0.05 * manchas] * 3, -1) * np.array([1.0, 0.99, 0.96])
    # Árido: puntitos.
    puntos = (ruido(w, h, 120, semilla + 2, 1) > 0.78).astype(np.float32)
    hormigon *= (1 - 0.12 * puntos)[..., None]
    img = a_img(hormigon, "RGB")
    alt = np.full((h, w), 0.5, np.float32) + 0.04 * (grano - 0.5)
    d = ImageDraw.Draw(img)
    for jx in juntas_x:
        x, _ = px(jx, 0)
        d.line([(x, 0), (x, h)], fill=(70, 70, 68), width=max(2, int(0.03 * k)))
        alt[:, max(0, int(x) - 2):int(x) + 2] = 0.38
    # Borde de la losa (arista gastada).
    d.rectangle((0, 0, w - 1, h - 1), outline=(120, 118, 112), width=3)

    # Rayuela de tiza: 1, 2, 3, 4-5, 6, 7-8 y «CIELO». Líneas temblorosas, con el relleno rosa en el 1.
    rx, ry, c = rayuela
    tiza = Image.new("L", (w, h), 0)
    dt = ImageDraw.Draw(tiza)
    filas = [[1], [2], [3], [4, 5], [6], [7, 8]]
    x = rx
    numeros = []
    for fila in filas:
        if len(fila) == 1:
            cajas = [(x, ry - c / 2, x + c, ry + c / 2)]
        else:
            cajas = [(x, ry - c, x + c, ry), (x, ry, x + c, ry + c)]
        for (a0, b0, a1, b1), n in zip(cajas, fila):
            p = [px(a0, b0), px(a1, b0), px(a1, b1), px(a0, b1), px(a0, b0)]
            trazo(dt, p, 255, 0.035 * k, 1.2, rng)
            numeros.append((n, px((a0 + a1) / 2, (b0 + b1) / 2)))
        x += c
    # Semicírculo final (cielo).
    cx_, cy_ = px(x, ry)
    r = c * k
    dt.arc((cx_ - r, cy_ - r, cx_ + r, cy_ + r), -90, 90, fill=255, width=int(0.035 * k))
    capa_tiza = a_img(np.asarray(tiza, np.float32) / 255 * (0.55 + 0.45 * ruido(w, h, 40, 9, 2)))
    img.paste((246, 244, 238), (0, 0), capa_tiza)
    # Números de colores.
    colores = [(255, 140, 190), (250, 230, 120), (150, 210, 255), (255, 255, 255), (190, 240, 160), (255, 190, 120),
               (255, 140, 190), (250, 230, 120)]
    for n, (x_, y_) in numeros:
        texto_a_mano(img, (x_ - 0.12 * k, y_ - 0.16 * k), str(n), colores[n - 1], int(0.26 * k),
                     rng.uniform(-10, 10) + 90, "negrita")
    texto_a_mano(img, (cx_ + 0.10 * k, cy_ - 0.30 * k), "CIELO", (150, 210, 255), int(0.16 * k), 90, "mano")
    # La piedra de jugar (pintada: la piedra de verdad ya se la llevó alguien) y un cohete de tiza al lado.
    d = ImageDraw.Draw(img)
    pcx, pcy = px(rx + c * 2.5, ry + c * 0.9)
    cohete = [(0, -0.30), (0.09, -0.12), (0.09, 0.16), (0.16, 0.26), (-0.16, 0.26), (-0.09, 0.16), (-0.09, -0.12)]
    for i in range(len(cohete)):
        a, b = cohete[i], cohete[(i + 1) % len(cohete)]
        trazo(d, [(pcx + a[1] * k, pcy - a[0] * k), (pcx + b[1] * k, pcy - b[0] * k)], (250, 200, 120), 0.025 * k, 0.8, rng)
    d.ellipse((pcx - 0.04 * k, pcy - 0.04 * k, pcx + 0.04 * k, pcy + 0.04 * k), outline=(150, 210, 255),
              width=int(0.02 * k))
    for i in range(3):  # llamitas
        trazo(d, [(pcx + 0.27 * k, pcy + (i - 1) * 0.06 * k), (pcx + 0.40 * k, pcy + (i - 1) * 0.09 * k)],
              (255, 140, 60), 0.02 * k, 1.0, rng)
    # Tierra derramada de la maceta rota.
    arr = np.asarray(img, np.float32) / 255
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    rough = 0.88 + 0.06 * grano
    for (tx, ty, tr) in tierra:
        cx_, cy_ = px(tx, ty)
        dist = np.sqrt((xx - cx_) ** 2 + (yy - cy_) ** 2) / (tr * k)
        m = np.clip(1.3 - dist - 0.6 * ruido(w, h, 25, int(tx * 100) % 97, 3), 0, 1)
        m = np.clip(m * 2.2, 0, 1)
        arr = mezclar(arr, (0.26, 0.18, 0.12), m)
        alt += m * 0.10
        rough = rough * (1 - m) + 0.97 * m
    # Mugre junto a la pared (donde no se barre).
    junto = np.exp(-(yy / (0.25 * k)))
    arr *= (1 - 0.18 * junto)[..., None]
    tz = np.asarray(tiza, np.float32) / 255
    rough = rough * (1 - tz) + 0.98 * tz
    return a_img(arr, "RGB"), a_img(rough), a_img(np.clip(alt, 0, 1))


# ----------------------------------------------------------------------------------------------------------------
# Loseta de los paneles metálicos de las paredes
# ----------------------------------------------------------------------------------------------------------------


def loseta_panel(ancho=2.0, alto=2.0, semilla=61):
    """
    Loseta repetible (ancho×alto studs) de los paneles: junta en x=0 e y=0, remaches a lo largo de las juntas,
    abolladuras suaves y chorretones verticales. Color en gris claro (se tiñe en el shader). Devuelve (color, alt).
    """
    w, h = int(ancho * 256), int(alto * 256)
    k = w / ancho
    rng = random.Random(semilla)

    def rep(arr):  # hace repetible sumando la copia desplazada
        return 0.5 * (arr + np.roll(np.roll(arr, w // 2, 1), h // 2, 0))

    abol = rep(ruido(w, h, 3, semilla, 3))
    chorro = rep(ruido(w, h, 2, semilla + 1, 4, estirar=(8.0, 0.15)))
    fino = rep(ruido(w, h, 40, semilla + 2, 2))
    col = np.full((h, w), 0.86, np.float32) - 0.10 * (chorro - 0.5) - 0.03 * (fino - 0.5)
    alt = 0.5 + 0.06 * (abol - 0.5)
    # Juntas (rehundidas) en los bordes de la loseta.
    jw = int(0.04 * k)
    for arr_, v in ((alt, 0.18), (col, 0.45)):
        arr_[:jw // 2, :] = v
        arr_[-jw // 2:, :] = v
        arr_[:, :jw // 2] = v
        arr_[:, -jw // 2:] = v
    # Remaches.
    paso = 0.25 * k
    r = 0.028 * k
    img_alt = a_img(alt)
    img_col = a_img(col)
    da = ImageDraw.Draw(img_alt)
    dc = ImageDraw.Draw(img_col)
    for i in range(int(w / paso)):
        for (x, y) in ((i * paso + paso / 2, jw * 1.6), (i * paso + paso / 2, h - jw * 1.6)):
            da.ellipse((x - r, y - r, x + r, y + r), fill=210)
            dc.ellipse((x - r, y - r, x + r, y + r), fill=200)
    for i in range(int(h / paso)):
        for (x, y) in ((jw * 1.6, i * paso + paso / 2), (w - jw * 1.6, i * paso + paso / 2)):
            da.ellipse((x - r, y - r, x + r, y + r), fill=210)
            dc.ellipse((x - r, y - r, x + r, y + r), fill=200)
    # Chorretón de óxido bajo algunos remaches (poco: la casa está cuidada).
    arr_c = np.asarray(img_col, np.float32) / 255
    rgb = np.stack([arr_c, arr_c, arr_c * 1.02], -1)
    for _ in range(3):
        x = int(rng.choice([jw * 1.6, w - jw * 1.6]))
        y = int(rng.uniform(0.2, 0.8) * h)
        largo = int(rng.uniform(0.15, 0.4) * k)
        for yy in range(y, min(h, y + largo)):
            a = 0.25 * (1 - (yy - y) / largo)
            x0, x1 = max(0, x - 3), min(w, x + 4)
            rgb[yy, x0:x1] = rgb[yy, x0:x1] * (1 - a) + np.array([0.55, 0.38, 0.25]) * a
    alt_f = img_alt.filter(ImageFilter.GaussianBlur(1.5))
    return a_img(np.clip(rgb, 0, 1), "RGB"), alt_f


def celulas_solares(ancho, alto, filas, columnas, semilla=71):
    w, h = int(ancho * 200), int(alto * 200)
    img = Image.new("RGB", (w, h), (200, 205, 215))
    d = ImageDraw.Draw(img)
    g = ruido(w, h, 8, semilla, 3)
    m = int(0.03 * 200)
    cw = (w - 2 * m) / columnas
    ch = (h - 2 * m) / filas
    for i in range(columnas):
        for j in range(filas):
            x0, y0 = m + i * cw + 2, m + j * ch + 2
            x1, y1 = x0 + cw - 4, y0 + ch - 4
            d.rectangle((x0, y0, x1, y1), fill=(22, 38, 82))
            for k in range(1, 4):  # barras colectoras plateadas
                xx = x0 + (x1 - x0) * k / 4
                d.line([(xx, y0), (xx, y1)], fill=(120, 130, 150), width=1)
            # Esquinas recortadas de las células.
            for (cx, cy) in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
                d.ellipse((cx - 5, cy - 5, cx + 5, cy + 5), fill=(200, 205, 215))
    arr = np.asarray(img, np.float32) / 255 * (0.92 + 0.08 * g[..., None])
    # Polvo y una hoja seca encima.
    polvo = ruido(w, h, 4, semilla + 1, 3)
    arr = mezclar(arr, (0.55, 0.52, 0.45), np.clip(polvo - 0.6, 0, 1) * 0.6)
    return a_img(arr, "RGB")
