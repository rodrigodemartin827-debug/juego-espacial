"""
Imágenes de apoyo (Pillow + numpy) que los materiales proyectan sobre el modelo antes de hornear el atlas:
  * rótulos pintados con plantilla (SECTOR 7-B, números de lote), carteles (OFICINA, horario, ZONA DE CARGA),
    etiquetas de envío (FRÁGIL, SECTOR 7), pantallas de 7 segmentos;
  * marcas del suelo: rodadas de camión, huellas de la transpaleta, arañazos de contenedores, mancha de aceite, charco;
  * relieves repetibles: chapa antideslizante (lagrimada).
Cada función devuelve (ruta_png, ancho/alto). Todo es RGBA: el alfa dice dónde hay pintura.
"""

import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FUENTES = "/usr/share/fonts/truetype"
NEGRITA = f"{FUENTES}/dejavu/DejaVuSans-Bold.ttf"
NORMAL = f"{FUENTES}/dejavu/DejaVuSans.ttf"
MONO = f"{FUENTES}/dejavu/DejaVuSansMono-Bold.ttf"
ESTRECHA = f"{FUENTES}/liberation/LiberationSans-Bold.ttf"

_rng = np.random.default_rng(7)


def _fuente(ruta, tam):
    return ImageFont.truetype(ruta, tam)


def ruido(w, h, escalas=((8, 0.5), (24, 0.3), (80, 0.2)), semilla=0):
    """Ruido suave en [0, 1] (suma de octavas de ruido blanco ampliado)."""
    rng = np.random.default_rng(semilla)
    total = np.zeros((h, w), np.float32)
    for celdas, peso in escalas:
        cw, ch = max(2, int(celdas * w / max(w, h))), max(2, int(celdas * h / max(w, h)))
        a = (rng.random((ch, cw)) * 255).astype(np.uint8)
        im = Image.fromarray(a).resize((w, h), Image.BICUBIC)
        total += np.asarray(im, np.float32) / 255 * peso
    total -= total.min()
    return total / max(1e-6, total.max())


def _guardar(arr_rgba, carpeta, nombre):
    os.makedirs(carpeta, exist_ok=True)
    ruta = os.path.join(carpeta, f"{nombre}.png")
    Image.fromarray(np.clip(arr_rgba, 0, 255).astype(np.uint8), "RGBA").save(ruta)
    return ruta


def _hex(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


# --------------------------------------------------------------------------------------------------------------
# Rótulos
# --------------------------------------------------------------------------------------------------------------

PUENTES = set("OQDB0469APR8&")


def rotulo(carpeta, nombre, texto, color, alto_px=220, fuente=NEGRITA, plantilla=True, desgaste=0.35,
           espaciado=0.06, semilla=1, chorretones=0.0, pulverizado=True):
    """Texto pintado con plantilla sobre transparente: puentes en las letras, bordes pulverizados y desconchones."""
    f = _fuente(fuente, alto_px)
    anchos = [f.getlength(ch) for ch in texto]
    esp = alto_px * espaciado
    w = int(sum(anchos) + esp * (len(texto) - 1) + alto_px * 0.5)
    h = int(alto_px * 1.45)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    x = alto_px * 0.25
    y0 = alto_px * 0.12
    for ch, a in zip(texto, anchos):
        d.text((x, y0), ch, fill=255, font=f)
        if plantilla and ch.upper() in PUENTES:
            # puente vertical de la plantilla (la tira de cartón que sujeta el interior de la letra)
            cx = x + a / 2
            d.rectangle((cx - alto_px * 0.035, 0, cx + alto_px * 0.035, h), fill=0)
        x += a + esp
    alfa = np.asarray(im, np.float32) / 255
    if pulverizado:
        borde = np.asarray(im.filter(ImageFilter.GaussianBlur(alto_px * 0.025)), np.float32) / 255
        motas = _rng.random(alfa.shape) < 0.25 * borde * (1 - alfa)
        alfa = np.maximum(alfa, motas * 0.6)
    if chorretones:
        # gotas que caen de la pintura demasiado cargada
        rng = np.random.default_rng(semilla + 50)
        cols = rng.choice(w, size=int(len(texto) * 2 * chorretones), replace=False)
        for cx in cols:
            filas = np.nonzero(alfa[:, cx] > 0.8)[0]
            if len(filas):
                y_ini = filas.max()
                largo = int(rng.uniform(0.05, 0.35) * alto_px)
                grosor = max(1, int(alto_px * 0.012))
                for yy in range(y_ini, min(h - 1, y_ini + largo)):
                    t = (yy - y_ini) / max(1, largo)
                    alfa[yy, cx - grosor:cx + grosor] = np.maximum(alfa[yy, cx - grosor:cx + grosor], 0.9 * (1 - t))
    n = ruido(w, h, ((6, 0.4), (30, 0.35), (120, 0.25)), semilla)
    alfa *= np.clip((n - desgaste * 0.55) * 3.0, 0, 1)
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., :3] = _hex(color)
    rgba[..., :3] *= (0.9 + 0.1 * n[..., None])
    rgba[..., 3] = alfa * 255
    return _guardar(rgba, carpeta, nombre), w / h


def cartel(carpeta, nombre, lineas, fondo, tinta, ancho_px=1024, alto_px=256, borde=None, desgaste=0.15,
           semilla=3, tornillos=True):
    """
    Placa metálica serigrafiada. lineas = [(texto, alto relativo 0..1, fuente)]. Fondo opaco (la placa entera).
    Lleva un filete, los 4 tornillos pintados encima y suciedad en los bordes.
    """
    im = Image.new("RGBA", (ancho_px, alto_px), _hex(fondo) + (255,))
    d = ImageDraw.Draw(im)
    m = int(alto_px * 0.07)
    if borde:
        d.rounded_rectangle((m, m, ancho_px - m, alto_px - m), radius=m, outline=_hex(borde) + (255,),
                            width=max(2, int(alto_px * 0.025)))
    total = sum(r for _, r, _ in lineas)
    y = alto_px * (0.5 - total * 0.5 * 0.82)
    for texto, rel, fuente in lineas:
        t = int(alto_px * rel * 0.82)
        f = _fuente(fuente, max(8, t))
        tw = f.getlength(texto)
        if tw > ancho_px * 0.86:
            f = _fuente(fuente, max(8, int(t * ancho_px * 0.86 / tw)))
            tw = f.getlength(texto)
        d.text(((ancho_px - tw) / 2, y), texto, fill=_hex(tinta) + (255,), font=f)
        y += t * 1.0
    if tornillos:
        r = alto_px * 0.04
        for cx, cy in ((m * 1.6, m * 1.6), (ancho_px - m * 1.6, m * 1.6), (m * 1.6, alto_px - m * 1.6),
                       (ancho_px - m * 1.6, alto_px - m * 1.6)):
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(150, 152, 150, 255), outline=(60, 60, 60, 255))
            d.line((cx - r * 0.7, cy, cx + r * 0.7, cy), fill=(60, 60, 60, 255), width=max(1, int(r * 0.3)))
    arr = np.asarray(im, np.float32).copy()
    n = ruido(ancho_px, alto_px, ((5, 0.5), (40, 0.5)), semilla)
    yy, xx = np.mgrid[0:alto_px, 0:ancho_px]
    borde_d = np.minimum.reduce([xx, yy, ancho_px - 1 - xx, alto_px - 1 - yy]) / (alto_px * 0.18)
    sucio = np.clip(1 - borde_d, 0, 1) * 0.35 + (n > 1 - desgaste) * 0.25
    arr[..., :3] *= (1 - sucio[..., None])
    return _guardar(arr, carpeta, nombre), ancho_px / alto_px


def flecha_zona_carga(carpeta, nombre="senal_zona_carga"):
    """Señal azul: flecha a la derecha y «ZONA DE CARGA» (el texto de la señal: «→ ZONA DE CARGA»)."""
    w, h = 1024, 384
    im = Image.new("RGBA", (w, h), _hex("#1F4E9C") + (255,))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((14, 14, w - 14, h - 14), radius=28, outline=(245, 245, 245, 255), width=12)
    # flecha
    cy = h * 0.5
    d.polygon([(60, cy - 34), (210, cy - 34), (210, cy - 90), (320, cy), (210, cy + 90), (210, cy + 34),
               (60, cy + 34)], fill=(245, 245, 245, 255))
    f = _fuente(ESTRECHA, 118)
    for i, linea in enumerate(("ZONA DE", "CARGA")):
        d.text((360, 40 + i * 150), linea, fill=(245, 245, 245, 255), font=f)
    arr = np.asarray(im, np.float32).copy()
    n = ruido(w, h, ((4, 0.6), (50, 0.4)), 11)
    arr[..., :3] *= (0.88 + 0.12 * n[..., None])
    return _guardar(arr, carpeta, nombre), w / h


def etiqueta_fragil(carpeta, nombre="etiqueta_fragil"):
    """Pegatina roja de FRÁGIL con la copa rota y «ESTE LADO ARRIBA»."""
    w, h = 768, 512
    im = Image.new("RGBA", (w, h), (238, 232, 216, 255))
    d = ImageDraw.Draw(im)
    rojo = _hex("#C3261E") + (255,)
    d.rectangle((10, 10, w - 10, h - 10), outline=rojo, width=14)
    # copa rota
    cx, cy = 150, 250
    d.polygon([(cx - 70, cy - 150), (cx + 70, cy - 150), (cx + 40, cy - 30), (cx - 40, cy - 30)], fill=rojo)
    d.rectangle((cx - 9, cy - 30, cx + 9, cy + 80), fill=rojo)
    d.rectangle((cx - 60, cy + 80, cx + 60, cy + 100), fill=rojo)
    d.line([(cx - 20, cy - 150), (cx + 5, cy - 110), (cx - 10, cy - 80), (cx + 15, cy - 40)], fill=(238, 232, 216, 255),
           width=8)
    f = _fuente(NEGRITA, 150)
    d.text((265, 70), "FRÁGIL", fill=rojo, font=_fuente(NEGRITA, 120))
    f = _fuente(NEGRITA, 46)
    d.text((270, 250), "ESTE LADO ARRIBA", fill=rojo, font=f)
    for i in range(2):
        x = 330 + i * 160
        d.polygon([(x, 330), (x + 50, 390), (x + 20, 390), (x + 20, 460), (x - 20, 460), (x - 20, 390), (x - 50, 390)],
                  fill=rojo)
    arr = np.asarray(im, np.float32).copy()
    n = ruido(w, h, ((5, 0.5), (60, 0.5)), 21)
    arr[..., :3] *= (0.85 + 0.15 * n[..., None])
    # esquina despegada y arrugas: alfa recortado en una esquina
    yy, xx = np.mgrid[0:h, 0:w]
    arr[..., 3] = np.where((xx + (h - yy)) < 70, 0, 255)
    return _guardar(arr, carpeta, nombre), w / h


def etiqueta_envio(carpeta, nombre="etiqueta_envio", destino="PUEBLO / SECTOR 7-B", ref="SUM-07B-0219"):
    """Albarán de envío: código de barras, destino y referencia."""
    w, h = 640, 800
    im = Image.new("RGBA", (w, h), (244, 241, 230, 255))
    d = ImageDraw.Draw(im)
    tinta = (25, 25, 28, 255)
    d.rectangle((0, 0, w - 1, 120), fill=tinta)
    d.text((24, 22), "SUMINISTROS", fill=(244, 241, 230, 255), font=_fuente(NEGRITA, 64))
    d.text((24, 150), "DESTINO", fill=tinta, font=_fuente(NORMAL, 34))
    d.text((24, 195), destino, fill=tinta, font=_fuente(NEGRITA, 46))
    d.text((24, 270), "REF " + ref, fill=tinta, font=_fuente(MONO, 44))
    d.text((24, 330), "PESO 412 kg   BULTOS 1/1", fill=tinta, font=_fuente(NORMAL, 34))
    rng = np.random.default_rng(5)
    x = 30
    while x < w - 40:
        bw = int(rng.integers(3, 12))
        if rng.random() < 0.6:
            d.rectangle((x, 420, x + bw, 700), fill=tinta)
        x += bw + int(rng.integers(3, 9))
    d.text((150, 715), "7 41250 02197 3", fill=tinta, font=_fuente(MONO, 40))
    arr = np.asarray(im, np.float32).copy()
    n = ruido(w, h, ((4, 0.5), (40, 0.5)), 31)
    arr[..., :3] *= (0.86 + 0.14 * n[..., None])
    return _guardar(arr, carpeta, nombre), w / h


def pantalla_7seg(carpeta, nombre, texto, color="#3DF2FF", ancho_px=512, alto_px=192, sufijo=""):
    """Dígitos de 7 segmentos encendidos (blanco = luz) sobre fondo casi negro, con los segmentos apagados tenues."""
    segs = {"0": "abcdef", "1": "bc", "2": "abged", "3": "abgcd", "4": "fgbc", "5": "afgcd", "6": "afgedc",
            "7": "abc", "8": "abcdefg", "9": "abcdfg", "-": "g", " ": ""}
    im = Image.new("RGBA", (ancho_px, alto_px), (8, 14, 16, 255))
    d = ImageDraw.Draw(im)
    col = _hex(color)
    apagado = tuple(int(c * 0.12 + 10) for c in col)
    digitos = [ch for ch in texto if ch != "."]
    puntos = [i for i, ch in enumerate(texto.replace(".", "|.")) if ch == "."]
    nd = len(digitos)
    margen = alto_px * 0.16
    zona = ancho_px * (0.78 if sufijo else 0.92)
    dw = zona / nd
    sh, sw = alto_px - 2 * margen, dw * 0.62
    t = max(3, int(sh * 0.11))
    for i, ch in enumerate(digitos):
        x0 = margen * 0.6 + i * dw + dw * 0.08
        y0 = margen
        geo = {"a": (x0 + t, y0, x0 + sw - t, y0 + t), "g": (x0 + t, y0 + sh / 2 - t / 2, x0 + sw - t, y0 + sh / 2 + t / 2),
               "d": (x0 + t, y0 + sh - t, x0 + sw - t, y0 + sh), "f": (x0, y0 + t, x0 + t, y0 + sh / 2 - t / 2),
               "b": (x0 + sw - t, y0 + t, x0 + sw, y0 + sh / 2 - t / 2),
               "e": (x0, y0 + sh / 2 + t / 2, x0 + t, y0 + sh - t), "c": (x0 + sw - t, y0 + sh / 2 + t / 2, x0 + sw,
                                                                         y0 + sh - t)}
        for s, r in geo.items():
            d.rectangle(r, fill=(col if s in segs.get(ch, "") else apagado) + (255,))
    for p in puntos:
        k = p - puntos.index(p) - 1  # dígito anterior al punto
        x = margen * 0.6 + (k + 1) * dw - dw * 0.12
        d.rectangle((x, margen + sh - t, x + t, margen + sh), fill=col + (255,))
    if sufijo:
        d.text((ancho_px * 0.8, alto_px * 0.42), sufijo, fill=col + (255,), font=_fuente(NEGRITA, int(alto_px * 0.3)))
    arr = np.asarray(im.filter(ImageFilter.GaussianBlur(1.2)), np.float32).copy()
    return _guardar(arr, carpeta, nombre), ancho_px / alto_px


# --------------------------------------------------------------------------------------------------------------
# Suelo
# --------------------------------------------------------------------------------------------------------------


def _trazo(alfa, pts, ancho, valor, escala_px):
    im = Image.fromarray((alfa * 255).astype(np.uint8))
    d = ImageDraw.Draw(im)
    d.line([(x * escala_px, y * escala_px) for x, y in pts], fill=int(valor * 255), width=max(1, int(ancho * escala_px)),
           joint="curve")
    return np.asarray(im, np.float32) / 255


def _bezier(p0, p1, p2, p3, n=40):
    out = []
    for i in range(n + 1):
        t = i / n
        a = (1 - t) ** 3
        b = 3 * (1 - t) ** 2 * t
        c = 3 * (1 - t) * t ** 2
        d = t ** 3
        out.append((a * p0[0] + b * p1[0] + c * p2[0] + d * p3[0], a * p0[1] + b * p1[1] + c * p2[1] + d * p3[1]))
    return out


def rodadas(carpeta, nombre, ancho_st, alto_st, trazas, px_por_stud=128, semilla=41, extra=None):
    """
    Marcas oscuras de neumáticos vistas desde arriba (imagen = rectángulo de ancho_st x alto_st studs, la fila 0 es
    el borde +Y del rectángulo). trazas = [(puntos_en_studs, ancho_banda, intensidad, dibujo)].
    `dibujo` > 0 añade el dibujo de la banda de rodadura (tacos).
    """
    w, h = int(ancho_st * px_por_stud), int(alto_st * px_por_stud)
    alfa = np.zeros((h, w), np.float32)
    for pts, ancho, inten, dibujo in trazas:
        capa = _trazo(np.zeros((h, w), np.float32), pts, ancho, 1.0, px_por_stud)
        if dibujo:
            # tacos: bandas perpendiculares a la marcha, muestreadas con una onda sobre la longitud del trazo
            n = ruido(w, h, ((40, 1.0),), semilla)
            yy, xx = np.mgrid[0:h, 0:w]
            onda = 0.5 + 0.5 * np.sin((yy + xx * 0.15) / (px_por_stud * 0.06))
            capa *= 0.55 + 0.45 * onda * (0.6 + 0.4 * n)
        alfa = np.maximum(alfa, capa * inten)
    if extra:
        alfa = extra(alfa, px_por_stud)
    alfa = np.asarray(Image.fromarray((alfa * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2.0)),
                      np.float32) / 255
    n = ruido(w, h, ((10, 0.4), (60, 0.6)), semilla + 1)
    alfa *= 0.55 + 0.45 * n
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., :3] = (22, 20, 19)
    rgba[..., 3] = np.clip(alfa, 0, 1) * 255
    return _guardar(rgba, carpeta, nombre), w / h


def aranazos(carpeta, nombre, ancho_st, alto_st, lineas, color=(196, 194, 188), px_por_stud=128, semilla=51):
    """Arañazos claros (cantos de contenedores arrastrados): líneas finas casi paralelas con temblor."""
    w, h = int(ancho_st * px_por_stud), int(alto_st * px_por_stud)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    rng = np.random.default_rng(semilla)
    for (x0, y0, x1, y1, n, separacion) in lineas:
        for k in range(n):
            dx = rng.normal(0, separacion)
            pts = []
            for t in np.linspace(0, 1, 12):
                x = x0 + (x1 - x0) * t + dx + rng.normal(0, 0.01)
                y = y0 + (y1 - y0) * t
                pts.append((x * px_por_stud, y * px_por_stud))
            ini = int(rng.integers(0, 4))
            fin = int(rng.integers(8, 13))
            d.line(pts[ini:fin], fill=int(rng.uniform(120, 255)), width=int(rng.integers(1, 3)))
    alfa = np.asarray(im, np.float32) / 255
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., :3] = color
    rgba[..., 3] = alfa * 255
    return _guardar(rgba, carpeta, nombre), w / h


def manchas(carpeta, nombre, ancho_st, alto_st, lista, px_por_stud=96, semilla=61):
    """Manchas (aceite, óxido, humedad): lista = [(x, y, radio, intensidad, (r,g,b))] en studs; borde irregular."""
    w, h = int(ancho_st * px_por_stud), int(alto_st * px_por_stud)
    yy, xx = np.mgrid[0:h, 0:w] / px_por_stud
    rgba = np.zeros((h, w, 4), np.float32)
    n = ruido(w, h, ((8, 0.5), (30, 0.5)), semilla)
    for (x, y, r, inten, col) in lista:
        dist = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r + (n - 0.5) * 0.6
        a = np.clip(1.0 - dist, 0, 1) ** 0.6 * inten
        rgba[..., :3] = rgba[..., :3] * (1 - a[..., None]) + np.array(col) * a[..., None]
        rgba[..., 3] = np.maximum(rgba[..., 3], a * 255)
    return _guardar(rgba, carpeta, nombre), w / h


def marcas_suelo_interior(carpeta, nombre, ancho_st, alto_st, rect_pasillos, px_por_stud=64):
    """Líneas amarillas de los pasillos del almacén y huecos de palé, desgastadas por el paso."""
    w, h = int(ancho_st * px_por_stud), int(alto_st * px_por_stud)
    im = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(im)
    for (x0, y0, x1, y1, grosor) in rect_pasillos:
        d.rectangle((x0 * px_por_stud, y0 * px_por_stud, x1 * px_por_stud, y1 * px_por_stud), outline=255,
                    width=max(2, int(grosor * px_por_stud)))
    alfa = np.asarray(im, np.float32) / 255
    n = ruido(w, h, ((8, 0.4), (50, 0.6)), 71)
    alfa *= np.clip((n - 0.18) * 2.2, 0, 1)
    rgba = np.zeros((h, w, 4), np.float32)
    rgba[..., :3] = _hex("#E8B414")
    rgba[..., 3] = alfa * 255
    return _guardar(rgba, carpeta, nombre), w / h


# --------------------------------------------------------------------------------------------------------------
# Relieves repetibles (alto en escala de grises)
# --------------------------------------------------------------------------------------------------------------


def chapa_lagrimada(carpeta, nombre="relieve_lagrimada", tam=512, celdas=4):
    """Chapa antideslizante: lágrimas alargadas a ±45° alternadas en damero. Repetible."""
    im = Image.new("L", (tam, tam), 0)
    d = ImageDraw.Draw(im)
    c = tam / celdas
    largo, ancho = c * 0.62, c * 0.16
    for i in range(-1, celdas + 1):
        for j in range(-1, celdas + 1):
            cx, cy = (i + 0.5) * c, (j + 0.5) * c
            a = math.radians(45 if (i + j) % 2 == 0 else -45)
            dx, dy = math.cos(a) * largo / 2, math.sin(a) * largo / 2
            for k in range(14):
                t = k / 13
                r = ancho / 2 * (0.6 + 0.4 * math.sin(math.pi * t))
                x, y = cx - dx + 2 * dx * t, cy - dy + 2 * dy * t
                d.ellipse((x - r, y - r, x + r, y + r), fill=255)
    im = im.filter(ImageFilter.GaussianBlur(c * 0.04))
    arr = np.asarray(im, np.float32)
    rgba = np.zeros((tam, tam, 4), np.float32)
    rgba[..., :3] = arr[..., None]
    rgba[..., 3] = 255
    return _guardar(rgba, carpeta, nombre), 1.0
