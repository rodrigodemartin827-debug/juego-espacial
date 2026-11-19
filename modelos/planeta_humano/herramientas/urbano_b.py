"""Mobiliario urbano (2): poste indicador, puente peatonal, escalera pública, marquesina de parada, contenedor de
basura, antena de comunicaciones y generador eléctrico.

El texto pintado (flechas, horarios, mapa, logos, avisos) va como calcomanía horneada en el atlas (ver «calcos» en
ph.crear_material): así no gasta triángulos y se pela y ensucia con la pintura de debajo."""

import math
import os

from PIL import Image, ImageDraw, ImageFont

from especiales_b import _parabolica
from ph import FUENTES, NEON, V, Modelo

ZONA = "urbano"
DIR_CALCOS = "/tmp/planeta_humano_provisional/_calcos"


# ---- calcomanías -----------------------------------------------------------------------------------------------
def _f(tam, cual="negrita"):
    return ImageFont.truetype(FUENTES[cual], int(tam))


def _png(nombre, w, h, dibujo):
    """Lienzo RGBA transparente de w×h px; dibujo(d, im, w, h) pinta encima. Devuelve la ruta del PNG."""
    os.makedirs(DIR_CALCOS, exist_ok=True)
    im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dibujo(ImageDraw.Draw(im), im, w, h)
    ruta = os.path.join(DIR_CALCOS, nombre + ".png")
    im.save(ruta)
    return ruta


def _calco(img, o, u, v, rug=None):
    """Rectángulo de proyección: o = esquina inferior izquierda vista de frente, u = ancho, v = alto."""
    return dict(img=img, o=tuple(o), u=tuple(u), v=tuple(v), rug=rug)


def _texto_c(d, xy, txt, fuente, color):
    """Texto centrado en xy."""
    caja = d.textbbox((0, 0), txt, font=fuente)
    d.text((xy[0] - (caja[2] - caja[0]) / 2 - caja[0], xy[1] - (caja[3] - caja[1]) / 2 - caja[1]), txt, font=fuente,
           fill=color)


def _flecha_png(nombre, texto, dist, punta_der):
    """Flecha de señal: filete blanco siguiendo el contorno, nombre y distancia en una píldora blanca."""
    W, H = 1024, 320

    def dib(d, im, w, h):
        m, cola = 18, int(w * 0.24)
        if punta_der:
            pol = [(m, m), (w - cola, m), (w - m - 6, h / 2), (w - cola, h - m), (m, h - m)]
        else:
            pol = [(w - m, m), (cola, m), (m + 6, h / 2), (cola, h - m), (w - m, h - m)]
        d.line(pol + [pol[0]], fill=(245, 245, 240, 255), width=10, joint="curve")
        flecha = "→" if punta_der else "←"
        fuente = _f(h * 0.36)
        fd = _f(h * 0.25)
        # nombre con su flecha pintada, centrado en el cuerpo de la señal
        cuerpo0, cuerpo1 = (m + 40, w - cola - 10) if punta_der else (cola + 10, w - m - 40)
        rotulo = f"{texto} {flecha}" if punta_der else f"{flecha} {texto}"
        _texto_c(d, ((cuerpo0 + cuerpo1) / 2, h * 0.42), rotulo, fuente, (248, 248, 244, 255))
        # píldora con la distancia, bajo el nombre
        cx = (cuerpo0 + cuerpo1) / 2
        d.rounded_rectangle((cx - 105, h * 0.62, cx + 105, h * 0.9), radius=26, fill=(245, 245, 240, 255))
        _texto_c(d, (cx, h * 0.75), dist, fd, (30, 32, 36, 255))
    return _png(nombre, W, H, dib)


# ==============================================================================================================
def poste_indicador():
    m = Modelo("poste_indicador", ZONA, (1, 1, 5), 2000,
               "Poste indicador de la colonia: tubo cuadrado sobre dado de hormigón con placa de 4 pernos y cartelas, "
               "4 flechas de chapa con abrazaderas (HANGAR, MERCADO, CENTRO y MINA) con el texto y la distancia "
               "pintados por las dos caras, placa «Usted está aquí» y piloto cyan en la cima.")
    c = m.parte()
    luz = m.parte("piloto_neon", tipo="neon", color=NEON)
    horm = m.mat("hormigon", "#8E8A84", lluvia=0.4)
    acero = m.mat("metal", "#848A91")
    poste = m.mat("pintura", "#39414A", desgaste=0.45, lluvia=0.5)
    m.seccion("base")
    c.caja((0, 0, 0.12), (0.62, 0.62, 0.24), horm, 0.04)
    c.caja((0, 0, 0.255), (0.4, 0.4, 0.03), acero, 0.006)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c.perno((math.cos(a) * 0.235, math.sin(a) * 0.235, 0.27), (0, 0, 1), acero, r=0.028, arandela=True)
    for k in range(4):  # cartelas triangulares de refuerzo
        c.extruir([(0.06, 0.0), (0.18, 0.0), (0.06, 0.16)], 0.014, poste, c=(0, 0, 0.27),
                  rot=(90, 0, k * 90))
    m.seccion("poste")
    c.caja((0, 0, 2.56), (0.12, 0.12, 4.6), poste, 0.012)
    c.cil((0, 0, 4.86), (0, 0, 4.95), 0.095, poste, n=4, r1=0.02, giro=0.5)  # remate en punta
    luz.cil((0, 0, 4.8), (0, 0, 4.86), 0.07, None, n=8)  # piloto cyan bajo el remate
    # placa «usted está aquí» a la altura de los ojos
    placa = _png("poste_aqui", 512, 256, lambda d, im, w, h: (
        d.rounded_rectangle((8, 8, w - 8, h - 8), radius=26, outline=(230, 236, 240, 255), width=8),
        _texto_c(d, (w / 2, h * 0.3), "USTED ESTÁ AQUÍ", _f(h * 0.15), (240, 244, 246, 255)),
        d.ellipse((w / 2 - 22, h * 0.48, w / 2 + 22, h * 0.48 + 44), fill=(61, 242, 255, 255)),
        _texto_c(d, (w / 2, h * 0.82), "PLAZA CENTRAL", _f(h * 0.12), (200, 210, 216, 255))))
    azul_placa = m.mat("pintura", "#1F3550", desgaste=0.3,
                       calcos=[_calco(placa, (-0.17, 0, 1.43), (0.34, 0, 0), (0, 0, 0.17))])
    c.caja((0, -0.07, 1.515), (0.36, 0.02, 0.19), azul_placa, 0.004)
    for x in (-0.15, 0.15):
        c.remache((x, -0.081, 1.515), (0, -1, 0), acero, r=0.012)
    m.seccion("flechas")
    # (nombre, distancia, dirección en grados, color, altura)
    flechas = [("HANGAR", "500 m", 0, "#2F5FA8", 4.35), ("MERCADO", "300 m", 180, "#C98A1E", 3.9),
               ("CENTRO", "200 m", 90, "#2E7D4F", 3.45), ("MINA", "800 m", 270, "#9A3B2A", 3.0)]
    x0, L, h, t = 0.065, 1.02, 0.31, 0.03
    for nombre, dist, ang, color, z in flechas:
        a = math.radians(ang)
        d = V((math.cos(a), math.sin(a), 0))
        s = d.cross(V((0, 0, 1)))
        ancho = L - x0
        ia = _flecha_png(f"flecha_{nombre.lower()}_a", nombre, dist, True)
        ib = _flecha_png(f"flecha_{nombre.lower()}_b", nombre, dist, False)
        abajo = V((0, 0, z - h / 2))
        chapa = m.mat("pintura", color, desgaste=0.5, c_desgaste="#B9BEC4", lluvia=0.5, calcos=[
            _calco(ia, d * x0 + abajo, d * ancho, (0, 0, h)),
            _calco(ib, d * L + abajo, -d * ancho, (0, 0, h))])
        perfil = [(x0, -h / 2), (L - 0.22, -h / 2), (L, 0), (L - 0.22, h / 2), (x0, h / 2)]
        c.extruir(perfil, t, chapa, c=(0, 0, z), rot=(90, 0, ang), b=0.004)
        # dos abrazaderas en U alrededor del poste y sus tornillos sobre la chapa
        for dz in (-0.075, 0.075):
            c.toro((0, 0, z + dz), 0.085, 0.011, acero, n=4, m=3, rot=(0, 0, 45))
            c.perno(d * 0.12 + s * (t / 2) + V((0, 0, z + dz)), s, acero, r=0.016)
    m.terminar()


# ==============================================================================================================
def _rejilla_png():
    """Agujeros de rombo de la chapa perforada del tablero (oscuros sobre transparente)."""
    def dib(d, im, w, h):
        paso = 22
        for j in range(-1, h // paso + 2):
            for i in range(-1, w // paso + 2):
                cx = i * paso + (paso / 2 if j % 2 else 0)
                cy = j * paso * 0.62
                r = paso * 0.36
                d.polygon([(cx - r, cy), (cx, cy - r * 0.62), (cx + r, cy), (cx, cy + r * 0.62)],
                          fill=(10, 12, 14, 255))
    return _png("rejilla_rombos", 2048, 732, dib)


def puente_peatonal():
    m = Modelo("puente_peatonal", ZONA, (10, 4, 3), 5000,
               "Puente peatonal: dos arcos de tubo de acero con péndolas, vigas cajón laterales, tablero de chapa "
               "perforada en rombos, barandillas de tubo con cables por los dos lados, 6 luces cyan en el pasamanos "
               "bajo, mini rampas de chapa estriada y estribos de hormigón en los extremos.")
    c = m.parte()
    luz = m.parte("luces_neon", tipo="neon", color=NEON)
    acero = m.mat("pintura", "#D9DCDF", desgaste=0.35, c_desgaste="#8A9097", lluvia=0.5)
    gris = m.mat("metal", "#6E757C")
    horm = m.mat("hormigon", "#8E8A84", lluvia=0.5)
    estriada = m.mat("grip", "#7C8389")
    cable = m.mat("metal", "#A9B0B6", rug=0.3)
    perforada = m.mat("metal", "#8A9198", calcos=[_calco(_rejilla_png(), (-4.2, -1.5, 0), (8.4, 0, 0), (0, 3.0, 0))])
    X, Y = 4.2, 1.5

    def zt(x):  # cota de la cara superior del tablero
        return 0.42 + 0.62 * (1 - (x / X) ** 2)

    m.seccion("tablero y vigas")
    c.lamina(lambda u, v: (-X + 2 * X * u, -Y + 2 * Y * v, zt(-X + 2 * X * u) - 0.04), 12, 1, 0.08, perforada)
    for s in (-1, 1):  # vigas cajón laterales
        c.lamina(lambda u, v, s=s: (-X + 2 * X * u, s * (Y + 0.04), zt(-X + 2 * X * u) - 0.3 + 0.38 * v), 12, 1,
                 0.08, acero)
    for k in range(5):  # traviesas bajo el tablero
        x = -X + 0.3 + k * (2 * X - 0.6) / 4
        c.caja((x, 0, zt(x) - 0.17), (0.12, 2 * Y, 0.12), gris, 0.01)
    m.seccion("arcos y péndolas")
    for s in (-1, 1):
        yA = s * (Y + 0.2)
        pts = [(x, yA, 0.32 + 2.55 * (1 - (x / 4.5) ** 2)) for x in (-4.5, -3.4, -2.0, 0.0, 2.0, 3.4, 4.5)]
        c.tubo(pts, 0.085, acero, n=7, seg=2)
        for x in (-3.0, -1.5, 0.0, 1.5, 3.0):  # péndolas del arco a la viga
            za = 0.32 + 2.55 * (1 - (x / 4.5) ** 2)
            c.cil((x, yA, za), (x, s * (Y + 0.08), zt(x) + 0.05), 0.022, cable, n=4)
            c.caja((x, s * (Y + 0.1), zt(x) + 0.04), (0.08, 0.1, 0.06), gris)  # orejeta de anclaje
        for x in (-4.5, 4.5):  # zapata del arco
            c.caja((x, yA, 0.24), (0.32, 0.32, 0.18), gris, 0.02)
    m.seccion("barandillas")
    xs = [-X + 0.15 + i * (2 * X - 0.3) / 8 for i in range(9)]
    for s in (-1, 1):
        yb = s * (Y - 0.05)
        for x in xs:
            c.cil((x, yb, zt(x)), (x, yb, zt(x) + 0.95), 0.03, acero, n=6)
            c.caja((x, yb, zt(x) + 0.01), (0.1, 0.1, 0.02), gris)
        c.tubo([(x, yb, zt(x) + 0.98) for x in xs[::2]], 0.04, acero, n=6, seg=2)  # pasamanos
        c.tubo([(x, yb, zt(x) + 0.22) for x in xs[::2]], 0.035, acero, n=6, seg=2)  # pasamanos bajo
        for dz in (0.47, 0.72):  # cables tensados
            c.tubo([(x, yb, zt(x) + dz) for x in xs[::2]], 0.01, cable, n=4, seg=2)
        for x in (-2.6, 0.0, 2.6):  # 3 luces por lado en el pasamanos bajo, mirando al tablero
            z = zt(x) + 0.22
            c.caja((x, yb - s * 0.035, z), (0.3, 0.03, 0.08), gris, 0.005)
            luz.caja((x, yb - s * 0.052, z), (0.24, 0.01, 0.045), None)
    m.seccion("rampas y estribos")
    for s in (-1, 1):
        perfil = [(X - 0.02, zt(X)), (X + 0.8, 0.03), (X + 0.8, 0.0), (X - 0.02, 0.0)]
        c.extruir([(s * x, z) for x, z in (perfil if s > 0 else perfil[::-1])], 2 * Y, estriada, rot=(90, 0, 0))
        c.caja((s * (X + 0.05), 0, 0.12), (0.7, 2 * Y + 0.9, 0.24), horm, 0.03)
        for y in (-Y + 0.3, Y - 0.3):  # bolardos de la rampa
            c.cil((s * (X + 0.75), y * 1.12, 0.24), (s * (X + 0.75), y * 1.12, 0.62), 0.07, acero, n=8)
            luz.cil((s * (X + 0.75), y * 1.12, 0.62), (s * (X + 0.75), y * 1.12, 0.65), 0.05, None, n=8)
    m.terminar()


# ==============================================================================================================
def escalera_publica():
    m = Modelo("escalera_publica", ZONA, (4, 3, 3), 2000,
               "Escalera pública de 6 peldaños de chapa: zancas laterales dentadas, tabicas, bandas antideslizantes "
               "y canto amarillo en cada huella, pasamanos de tubo en un lado con un apoyo cada 2 peldaños y anclajes "
               "atornillados abajo y arriba.")
    c = m.parte()
    zanca = m.mat("pintura", "#3E4A56", desgaste=0.5, lluvia=0.5)
    chapa = m.mat("grip", "#868D93")
    goma = m.mat("goma", "#1C1E20")
    amarillo = m.mat("pintura", "#E0B12A", desgaste=0.7, c_desgaste="#868D93")
    acero = m.mat("metal", "#8A9097")
    tubo = m.mat("pintura", "#E0B12A", desgaste=0.45, c_desgaste="#8A9097")
    N, sube, huella, ancho = 6, 0.5, 0.5, 3.6
    y0 = -1.5
    m.seccion("zancas")
    dientes = [(y0, 0.0)]
    for i in range(N):
        dientes += [(y0 + i * huella, (i + 1) * sube), (y0 + (i + 1) * huella, (i + 1) * sube)]
    perfil = dientes + [(y0 + N * huella, N * sube - 0.55), (y0 + 0.55, 0.0)]
    for x in (-1.86, 1.86):
        c.extruir([(y, z) for y, z in perfil], 0.1, zanca, c=(x, 0, 0), rot=(90, 0, 90), b=0.01)
    m.seccion("peldaños")
    for i in range(N):
        yf = y0 + i * huella
        zt = (i + 1) * sube
        c.caja((0, yf + huella / 2, zt - 0.03), (ancho, huella, 0.06), chapa, 0.008)
        c.caja((0, yf + 0.015, zt - 0.27), (ancho, 0.03, 0.42), zanca, 0.004)  # tabica
        c.caja((0, yf + 0.04, zt + 0.002), (ancho - 0.04, 0.08, 0.012), amarillo)  # canto de seguridad
        for k in range(2):  # bandas antideslizantes
            c.caja((0, yf + 0.16 + k * 0.12, zt + 0.004), (ancho - 0.3, 0.06, 0.012), goma)
    m.seccion("pasamanos")
    xr = 1.98
    apoyos = [1, 3, 5]
    pts_p = []
    for i in apoyos:
        yp = y0 + i * huella + huella / 2
        zp = (i + 1) * sube
        c.caja((xr - 0.02, yp, zp - 0.12), (0.03, 0.14, 0.2), acero, 0.005)  # placa a la zanca
        c.perno((xr, yp, zp - 0.07), (1, 0, 0), acero, r=0.022)
        c.perno((xr, yp, zp - 0.17), (1, 0, 0), acero, r=0.022)
        c.cil((xr + 0.02, yp, zp - 0.05), (xr + 0.02, yp, zp + 0.95), 0.03, tubo, n=6)
        pts_p.append((xr + 0.02, yp, zp + 1.0))
    a, b = V(pts_p[0]), V(pts_p[-1])
    dirp = (b - a).normalized()
    ini = a - dirp * 0.35
    fin = b + dirp * 0.35
    c.tubo([ini + V((0, 0, -0.25)), ini, a, b, fin, fin + V((0, 0.08, -0.22))], 0.04, tubo, n=6, seg=2)
    m.seccion("anclajes")
    for x in (-1.86, 1.86):
        c.caja((x, y0 + 0.28, 0.015), (0.3, 0.5, 0.03), acero, 0.005)  # placa de pie
        for y in (y0 + 0.12, y0 + 0.44):
            for dx in (-0.09, 0.09):
                c.perno((x + dx, y, 0.03), (0, 0, 1), acero, r=0.026)
        # escuadra superior atornillada al rellano
        c.caja((x, y0 + N * huella + 0.015, N * sube - 0.25), (0.26, 0.03, 0.4), acero, 0.005)
        for z in (N * sube - 0.12, N * sube - 0.38):
            c.perno((x, y0 + N * huella + 0.03, z), (0, 1, 0), acero, r=0.022)
    m.terminar()


# ==============================================================================================================
def _mapa_png():
    def dib(d, im, w, h):
        d.rectangle((0, 0, w, h), fill=(232, 236, 238, 255))
        d.rectangle((0, 0, w, 90), fill=(31, 53, 80, 255))
        _texto_c(d, (w / 2, 45), "RED DE LÍNEAS", _f(52), (245, 248, 250, 255))
        cols = [(46, 125, 79), (47, 95, 168), (201, 138, 30), (154, 59, 42)]
        rutas = [[(80, 300), (260, 300), (380, 420), (620, 420), (760, 560)],
                 [(120, 760), (300, 600), (300, 420), (520, 240), (690, 240)],
                 [(60, 520), (380, 520), (520, 680), (720, 680)],
                 [(420, 160), (420, 900), (650, 1050)]]
        for col, ruta in zip(cols, rutas):
            d.line(ruta, fill=(*col, 255), width=22, joint="curve")
            for p in ruta:
                d.ellipse((p[0] - 17, p[1] - 17, p[0] + 17, p[1] + 17), fill=(255, 255, 255, 255),
                          outline=(30, 30, 30, 255), width=5)
        d.ellipse((380 - 30, 520 - 30, 380 + 30, 520 + 30), fill=(61, 242, 255, 255), outline=(20, 30, 40, 255),
                  width=6)
        _texto_c(d, (380, 580), "ESTÁ AQUÍ", _f(30), (20, 30, 40, 255))
        for i, (col, nom) in enumerate(zip(cols, ("L1 CENTRO", "L2 HANGAR", "L3 MERCADO", "L4 MINA"))):
            y = 1120 + i * 58
            d.rectangle((60, y, 110, y + 36), fill=(*col, 255))
            d.text((130, y - 4), nom, font=_f(36), fill=(30, 32, 36, 255))
    return _png("mapa_lineas", 820, 1360, dib)


def _parada_png():
    def dib(d, im, w, h):
        d.ellipse((6, 6, w - 6, h - 6), outline=(31, 53, 80, 255), width=40)
        # autobús esquemático
        d.rounded_rectangle((w * 0.27, h * 0.22, w * 0.73, h * 0.52), radius=26, fill=(31, 53, 80, 255))
        d.rectangle((w * 0.31, h * 0.26, w * 0.69, h * 0.38), fill=(230, 236, 240, 255))
        for x in (0.35, 0.65):
            d.ellipse((w * x - 22, h * 0.5, w * x + 22, h * 0.5 + 44), fill=(31, 53, 80, 255))
        _texto_c(d, (w / 2, h * 0.7), "PARADA", _f(h * 0.13), (31, 53, 80, 255))
    return _png("disco_parada", 512, 512, dib)


def marquesina_parada():
    m = Modelo("marquesina_parada", ZONA, (6, 3, 4), 4000,
               "Marquesina de parada: pórticos de acero con viga curva en voladizo, cubierta curva de cristal, luz "
               "cyan bajo el alero, cristal trasero con banda de aviso, banco con 2 asientos moldeados, pantalla de "
               "horarios cyan con líneas de texto, panel lateral con el mapa de líneas, papelera al lado y poste con "
               "el disco «PARADA».")
    c = m.parte()
    cr = m.parte("cristal", tipo="cristal", color="#A8D4E2", transparencia=0.55)
    luz = m.parte("luces_neon", tipo="neon", color=NEON)
    pantalla = m.parte("pantalla_neon", tipo="neon", color=NEON, nota="Pantalla de horarios.")
    acero = m.mat("pintura", "#2E3A46", desgaste=0.4, lluvia=0.5)
    gris = m.mat("metal", "#8A9097")
    horm = m.mat("hormigon", "#9A968E", lluvia=0.3)
    amarillo = m.mat("goma", "#D8B030")
    asiento = m.mat("plastico", "#E06A2A")
    osc = m.mat("metal", "#1A1D21", rug=0.35)
    mapa = _mapa_png()
    anuncio = _png("anuncio_marquesina", 820, 1360, lambda d, im, w, h: (
        d.rectangle((0, 0, w, h), fill=(16, 28, 44, 255)),
        d.ellipse((w * 0.15, h * 0.18, w * 0.85, h * 0.18 + w * 0.7), fill=(46, 125, 160, 255)),
        d.ellipse((w * 0.62, h * 0.12, w * 0.76, h * 0.12 + w * 0.14), fill=(200, 210, 220, 255)),
        _texto_c(d, (w / 2, h * 0.74), "NUEVA", _f(110), (240, 244, 246, 255)),
        _texto_c(d, (w / 2, h * 0.83), "ESPERANZA", _f(110), (61, 242, 255, 255)),
        _texto_c(d, (w / 2, h * 0.93), "TU HOGAR ENTRE LAS ESTRELLAS", _f(36), (200, 210, 216, 255))))
    panel = m.mat("pintura", "#E8ECEE", desgaste=0.2, calcos=[
        _calco(mapa, (2.7, 1.12, 0.62), (0, -1.24, 0), (0, 0, 2.06)),
        _calco(anuncio, (2.7, -0.12, 0.62), (0, 1.24, 0), (0, 0, 2.06))])
    rotulo = _png("rotulo_alero", 2048, 128, lambda d, im, w, h: (
        _texto_c(d, (w / 2, h / 2), "LÍNEA 3  ·  CENTRO  —  MERCADO  —  HANGAR", _f(h * 0.6), (240, 244, 246, 255))))
    m.seccion("andén")
    c.caja((0, 0, 0.075), (6.4, 3.2, 0.15), horm, 0.03)
    c.caja((0, -1.42, 0.155), (6.2, 0.22, 0.012), amarillo)  # banda táctil del borde
    m.seccion("pórticos y cubierta")

    def curva(v):  # sección de la cubierta, de atrás (v=0) a delante (v=1)
        return 1.32 - 2.8 * v, 3.45 + 0.32 * math.sin(math.pi * v) - 0.12 * v

    for x in (-2.6, 2.6):
        c.caja((x, 1.25, 1.8), (0.14, 0.2, 3.3), acero, 0.02)
        c.caja((x, 1.25, 0.17), (0.34, 0.34, 0.04), gris, 0.005)
        for dx in (-0.11, 0.11):
            c.perno((x + dx, 1.25 + 0.11, 0.19), (0, 0, 1), gris, r=0.02)
        c.tubo([(x, *(lambda y, z: (y, z - 0.08))(*curva(v))) for v in (0.0, 0.33, 0.66, 1.0)], 0.07, acero, n=6,
               seg=3)
    cr.lamina(lambda u, v: (-3.0 + 6.0 * u, *curva(v)), 6, 6, 0.04, None)
    for v in (0.0, 1.0):  # perfiles de borde de la cubierta
        y, z = curva(v)
        c.cil((-3.02, y, z), (3.02, y, z), 0.045, acero, n=6)
    y1, z1 = curva(1.0)
    fascia = m.mat("pintura", "#2E3A46", desgaste=0.4,
                   calcos=[_calco(rotulo, (-2.9, y1, z1 - 0.21), (5.8, 0, 0), (0, 0, 0.18))])
    c.caja((0, y1 - 0.01, z1 - 0.12), (6.0, 0.05, 0.2), fascia, 0.008)
    luz.caja((0, y1 + 0.06, z1 - 0.21), (5.7, 0.05, 0.025), None)  # tira LED bajo el alero
    y0_, z0_ = curva(0.0)
    c.caja((0, y0_ + 0.06, z0_ - 0.04), (6.0, 0.12, 0.08), gris, 0.01)  # canalón trasero
    m.seccion("cerramiento trasero")
    cr.caja((0, 1.25, 1.36), (5.06, 0.03, 2.0), None)
    for z in (0.33, 2.39):
        c.caja((0, 1.25, z), (5.08, 0.08, 0.08), acero, 0.01)
    c.caja((0, 1.23, 1.55), (5.04, 0.008, 0.06), osc)  # banda de aviso sobre el cristal
    m.seccion("panel lateral")
    # marco de acero y, sobresaliendo 1,5 cm por cada cara, el panel con el mapa (dentro) y el anuncio (fuera)
    c.caja((2.7, 0.5, 1.65), (0.05, 1.38, 2.2), acero, 0.008)
    c.caja((2.7, 0.5, 1.65), (0.08, 1.26, 2.08), panel, 0.0)
    m.seccion("banco")
    for x in (-1.25, 1.0):
        c.extruir([(1.21, 0.36), (1.21, 0.58), (0.75, 0.46), (0.75, 0.4)], 0.06, acero, c=(x, 0, 0),
                  rot=(90, 0, 90))
    c.caja((-0.12, 0.92, 0.43), (2.9, 0.08, 0.07), gris, 0.01)
    perfil = [(0.62, 0.44), (0.66, 0.5), (0.86, 0.49), (1.0, 0.48), (1.08, 0.6), (1.12, 0.98)]
    for x0 in (-0.85, 0.45):
        def asiento_f(u, v, x0=x0):
            i = min(len(perfil) - 2, int(v * (len(perfil) - 1)))
            t = v * (len(perfil) - 1) - i
            y = perfil[i][0] + (perfil[i + 1][0] - perfil[i][0]) * t
            z = perfil[i][1] + (perfil[i + 1][1] - perfil[i][1]) * t
            return (x0 - 0.28 + 0.56 * u, y, z - 0.025 * math.sin(math.pi * u))
        c.lamina(asiento_f, 3, 5, 0.04, asiento)
    m.seccion("pantalla de horarios")
    c.caja((-1.95, 1.19, 1.95), (1.0, 0.08, 0.7), osc, 0.015)
    pantalla.caja((-1.95, 1.145, 1.97), (0.86, 0.012, 0.52), None)
    lineas = [(0.35, 0.18, 0.1), (0.22, 0.3, 0.1), (0.28, 0.2, 0.1), (0.16, 0.34, 0.1), (0.3, 0.24, 0.1)]
    for i, (a, b, cc) in enumerate(lineas):  # líneas de texto: destino, hora y andén
        z = 2.17 - i * 0.095
        x = -2.33
        for w in (a, b, cc):
            c.caja((x + w / 2, 1.137, z), (w, 0.006, 0.04), osc)
            x += w + 0.05
    for x in (-2.3, -1.6):  # soportes al larguero alto
        c.caja((x, 1.21, 2.34), (0.05, 0.05, 0.1), gris)
    m.seccion("papelera y poste")
    xp, yp = -3.35, 0.7
    c.cil((xp, yp, 0.0), (xp, yp, 0.3), 0.045, gris, n=6)
    c.cil((xp, yp, 0.3), (xp, yp, 1.05), 0.24, acero, n=12)
    c.cil((xp, yp, 1.05), (xp, yp, 1.12), 0.26, gris, n=12)
    c.caja((xp, yp - 0.2, 0.95), (0.22, 0.1, 0.12), osc, 0.01)  # boca
    xs_, ys_ = 3.4, -1.35
    c.cil((xs_, ys_, 0.0), (xs_, ys_, 3.0), 0.045, gris, n=8)
    disco = m.mat("pintura", "#F2F4F5", desgaste=0.25, calcos=[
        _calco(_parada_png(), (xs_ - 0.38, ys_, 2.32), (0.76, 0, 0), (0, 0, 0.76)),
        _calco(_parada_png(), (xs_ + 0.38, ys_, 2.32), (-0.76, 0, 0), (0, 0, 0.76))])
    c.cil((xs_, ys_ - 0.018, 2.7), (xs_, ys_ + 0.018, 2.7), 0.38, disco, n=16)
    for z in (2.4, 3.0):
        c.caja((xs_, ys_, z), (0.12, 0.05, 0.05), gris)
    m.terminar()


# ==============================================================================================================
def _logo_png(nombre, rotulo, organico):
    def dib(d, im, w, h):
        col = (245, 248, 244, 255)
        cx, cy, r = w / 2, h * 0.36, w * 0.28
        if organico:  # hoja con su nervio
            d.ellipse((cx - r * 0.55, cy - r, cx + r * 0.55, cy + r), fill=col)
            d.line([(cx, cy + r * 1.1), (cx, cy - r * 0.8)], fill=(0, 0, 0, 0), width=14)
            for k in range(3):
                yy = cy - r * 0.4 + k * r * 0.4
                d.line([(cx, yy + r * 0.25), (cx - r * 0.38, yy - r * 0.05)], fill=(0, 0, 0, 0), width=9)
                d.line([(cx, yy + r * 0.25), (cx + r * 0.38, yy - r * 0.05)], fill=(0, 0, 0, 0), width=9)
        else:  # tres flechas en triángulo (símbolo de reciclaje)
            for k in range(3):
                a0 = math.radians(90 + k * 120)
                a1 = math.radians(90 + k * 120 + 95)
                p0 = (cx + math.cos(a0) * r, cy - math.sin(a0) * r)
                p1 = (cx + math.cos(a1) * r, cy - math.sin(a1) * r)
                d.line([p0, p1], fill=col, width=34)
                ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
                pu = (p1[0] + math.cos(ang) * 40, p1[1] + math.sin(ang) * 40)
                pa = (p1[0] + math.cos(ang + 2.2) * 46, p1[1] + math.sin(ang + 2.2) * 46)
                pb = (p1[0] + math.cos(ang - 2.2) * 46, p1[1] + math.sin(ang - 2.2) * 46)
                d.polygon([pu, pa, pb], fill=col)
        _texto_c(d, (cx, h * 0.83), rotulo, _f(h * 0.11), col)
    return _png(nombre, 512, 640, dib)


def contenedor_basura():
    m = Modelo("contenedor_basura", ZONA, (2, 1.5, 2.5), 2000,
               "Contenedor de basura: cuerpo cilíndrico ovalado con nervios, pedal delantero con varilla hasta la "
               "tapa, tapa abombada con bisagra y muelle a la vista, 2 ruedas traseras, sensor de llenado con "
               "pantallita de barra y logo pintado. Dos variantes en la textura: verde (orgánico, la del atlas) y azul "
               "(reciclable, en contenedor_basura_color_azul.png).")
    c = m.parte()
    barra = m.parte("sensor_neon", tipo="neon", color=NEON, nota="Barra de llenado del sensor.")
    logo_o = _logo_png("logo_organico", "ORGÁNICO", True)
    logo_r = _logo_png("logo_reciclable", "RECICLABLE", False)
    rx, ry = 0.86, 0.6
    cal = dict(o=(-0.42, -ry, 0.75), u=(0.84, 0, 0), v=(0, 0, 1.05))
    verde = m.mat("plastico", "#2E7D3A", calcos=[_calco(logo_o, **cal)], suciedad=0.5, lluvia=0.4, desgaste=0.0)
    azul = m.mat("plastico", "#2459A8", calcos=[_calco(logo_r, **cal)], suciedad=0.5, lluvia=0.4, desgaste=0.0)
    tapa_v = m.mat("plastico", "#22602C", suciedad=0.4)
    tapa_a = m.mat("plastico", "#1B447F", suciedad=0.4)
    m.variantes["azul"] = {verde: azul, tapa_v: tapa_a}
    m.notas.append("Variante azul (reciclable): usar texturas/contenedor_basura_color_azul.png como ColorMap.")
    acero = m.mat("metal", "#8A9097")
    goma = m.mat("goma", "#1A1B1D")
    osc = m.mat("metal", "#1A1D21", rug=0.35)
    gal = m.mat("metal", "#B5BBC0", rug=0.3)
    m.seccion("cuerpo")

    def anillo(z, k):
        return [V((math.cos(a) * rx * k, math.sin(a) * ry * k, z)) for a in
                (i * math.tau / 20 for i in range(20))]
    c.loft([anillo(0.22, 0.94), anillo(0.3, 0.97), anillo(1.95, 1.0), anillo(2.0, 1.04), anillo(2.05, 1.04)], verde)
    for z in (0.62, 1.55):  # nervios de refuerzo
        c.loft([anillo(z - 0.03, 1.0), anillo(z - 0.01, 1.025), anillo(z + 0.01, 1.025), anillo(z + 0.03, 1.0)], verde)
    m.seccion("tapa")
    c.loft([anillo(2.06, 1.07), anillo(2.12, 1.07), anillo(2.2, 1.0), anillo(2.32, 0.8), anillo(2.39, 0.45),
            anillo(2.41, 0.1)], tapa_v)
    c.caja((0, -ry * 1.05, 2.1), (0.3, 0.08, 0.06), tapa_v, 0.01)  # asidero delantero
    # bisagra trasera con su muelle helicoidal a la vista
    yb, zb = ry * 1.07 + 0.03, 2.08
    c.cil((-0.45, yb, zb), (0.45, yb, zb), 0.03, acero, n=6)
    for x in (-0.4, 0.4):
        c.caja((x, yb - 0.04, zb - 0.06), (0.1, 0.08, 0.16), osc, 0.01)
    espiras = [V((-0.3 + 0.6 * t / 48, yb + math.cos(t * 0.8) * 0.055, zb + math.sin(t * 0.8) * 0.055))
               for t in range(49)]
    c.tubo(espiras, 0.011, gal, n=4, suave=False)
    m.seccion("pedal y ruedas")
    c.caja((0, -ry - 0.17, 0.12), (0.46, 0.22, 0.04), acero, 0.01)  # pedal
    c.caja((0, -ry - 0.17, 0.142), (0.42, 0.18, 0.006), m.mat("grip", "#6A7076"))
    c.cil((-0.24, -ry - 0.04, 0.12), (0.24, -ry - 0.04, 0.12), 0.025, acero, n=6)
    c.tubo([(0.35, -ry - 0.02, 0.14), (0.62, -0.47, 0.6), (0.82, -0.3, 1.7), (0.84, -0.3, 2.12)], 0.014, gal, n=4,
           seg=2)  # varilla del pedal a la tapa
    for x in (-0.6, 0.6):
        c.cil((x - 0.05 * (1 if x > 0 else -1), ry * 0.7, 0.2), (x + 0.07 * (1 if x > 0 else -1), ry * 0.7, 0.2),
              0.2, goma, n=12)
        c.cil((x + 0.08 * (1 if x > 0 else -1), ry * 0.7, 0.2), (x + 0.1 * (1 if x > 0 else -1), ry * 0.7, 0.2),
              0.08, acero, n=8)
    c.cil((-0.72, ry * 0.7, 0.2), (0.72, ry * 0.7, 0.2), 0.03, acero, n=6)  # eje
    c.caja((0, ry * 0.72, 0.3), (1.0, 0.12, 0.14), osc, 0.015)  # soporte del eje
    for x in (-0.5, 0.5):  # tacos de apoyo delanteros
        c.caja((x, -ry * 0.75, 0.11), (0.16, 0.16, 0.22), goma, 0.02)
    m.seccion("sensor de llenado")
    c.caja((0, -0.25, 2.37), (0.3, 0.16, 0.08), osc, 0.015, rot=(-14, 0, 0))
    c.caja((0, -0.33, 2.38), (0.22, 0.012, 0.05), m.mat("metal", "#0C1014", rug=0.2), rot=(-14, 0, 0))
    barra.caja((-0.035, -0.338, 2.378), (0.13, 0.006, 0.026), None, rot=(-14, 0, 0))
    m.terminar()


# ==============================================================================================================
def antena_comunicaciones():
    m = Modelo("antena_comunicaciones", ZONA, (2, 2, 8), 3000,
               "Antena de comunicaciones: mástil de tubo en tramos con bridas atornilladas, 3 vientos de cable a "
               "120° con tensores y anclajes, parábola pequeña con su brazo y LNB, látigo y baliza roja en la cima, "
               "cable coaxial bajando por el mástil con abrazaderas, peldaños y placa base con 4 pernos.")
    c = m.parte()
    baliza = m.parte("baliza_neon", tipo="neon", color="#FF2A2A", nota="Baliza de obstáculo: parpadeo lento.")
    horm = m.mat("hormigon", "#8E8A84", lluvia=0.4)
    galv = m.mat("metal", "#A6ADB3", rug=0.35)
    pint = m.mat("pintura", "#E8E6E0", desgaste=0.4, lluvia=0.5)
    rojo = m.mat("pintura", "#B8322A", desgaste=0.4)
    osc = m.mat("metal", "#1E2124", rug=0.5)
    cable = m.mat("goma", "#141516")
    blanco = m.mat("plastico", "#ECEDEE")
    m.seccion("base")
    c.caja((0, 0, 0.1), (1.0, 1.0, 0.2), horm, 0.03)
    c.caja((0, 0, 0.22), (0.56, 0.56, 0.04), galv, 0.006)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c.perno((math.cos(a) * 0.33, math.sin(a) * 0.33, 0.24), (0, 0, 1), galv, r=0.03, arandela=True)
    c.caja((0.0, -0.13, 0.6), (0.24, 0.12, 0.3), osc, 0.015)  # caja de conexiones
    c.cil((0.0, -0.13, 0.45), (0.0, -0.13, 0.24), 0.025, osc, n=6)
    m.seccion("mástil")
    tramos = [(0.24, 2.6, pint), (2.6, 5.0, rojo), (5.0, 7.3, pint)]  # franjas de balizamiento
    for z0, z1, mt in tramos:
        c.cil((0, 0, z0), (0, 0, z1), 0.065 if z0 < 5 else 0.055, mt, n=8)
    for z in (2.6, 5.0):  # bridas atornilladas
        c.cil((0, 0, z - 0.03), (0, 0, z + 0.03), 0.11, galv, n=8)
        for k in range(4):
            a = k * math.pi / 2
            c.perno((math.cos(a) * 0.09, math.sin(a) * 0.09, z + 0.03), (0, 0, 1), galv, r=0.014)
    for i in range(13):  # peldaños alternos
        z = 0.9 + i * 0.45
        s = 1 if i % 2 else -1
        c.cil((s * 0.05, 0.03, z), (s * 0.2, 0.03, z), 0.014, galv, n=4)
    m.seccion("vientos")
    zc = 5.85
    c.cil((0, 0, zc - 0.05), (0, 0, zc + 0.05), 0.085, galv, n=8)
    for k in range(3):
        a = math.radians(90 + k * 120)
        d = V((math.cos(a), math.sin(a), 0))
        arriba = d * 0.08 + V((0, 0, zc))
        abajo = d * 0.95 + V((0, 0, 0.1))
        tens = abajo.lerp(arriba, 0.12)
        c.cil(arriba, tens, 0.008, galv, n=4)
        c.cil(tens, tens.lerp(abajo, 0.45), 0.025, galv, n=6)  # tensor
        c.cil(tens.lerp(abajo, 0.45), abajo, 0.008, galv, n=4)
        c.caja(d * 0.95 + V((0, 0, 0.03)), (0.16, 0.16, 0.06), horm, 0.01)  # muerto de anclaje
        c.toro(abajo, 0.03, 0.008, galv, n=6, m=3, rot=(90, 0, math.degrees(a)))
    m.seccion("parábola y cima")
    c.caja((0, -0.12, 6.75), (0.08, 0.18, 0.08), galv, 0.01)
    _parabolica(c, blanco, galv, (0, -0.2, 6.75), (90, 0, 0), 0.32, profundo=0.12)
    c.cil((0, 0, 7.3), (0, 0, 7.95), 0.012, galv, n=4)  # látigo
    c.cil((0, 0, 7.3), (0, 0, 7.36), 0.06, osc, n=8)
    baliza.cil((0, 0, 7.36), (0, 0, 7.46), 0.045, None, n=8, r1=0.03)
    m.seccion("coaxial")
    xc = 0.085
    c.tubo([(xc, -0.03, 0.62), (xc, 0.0, 0.9), (xc, 0.0, 6.4), (0.05, -0.12, 6.7), (0.0, -0.33, 6.85)], 0.014, cable,
           n=4, seg=2)
    for i in range(7):  # abrazaderas
        c.caja((0.07, 0.0, 1.2 + i * 0.85), (0.06, 0.05, 0.03), galv)
    m.terminar()


# ==============================================================================================================
def _aviso_png():
    def dib(d, im, w, h):
        tri = [(w / 2, 20), (w - 20, h * 0.62), (20, h * 0.62)]
        d.polygon(tri, fill=(240, 196, 40, 255), outline=(20, 20, 20, 255), width=14)
        d.polygon([(w * 0.53, h * 0.18), (w * 0.4, h * 0.42), (w * 0.5, h * 0.42), (w * 0.45, h * 0.58),
                   (w * 0.62, h * 0.33), (w * 0.52, h * 0.33)], fill=(20, 20, 20, 255))
        d.rectangle((10, h * 0.68, w - 10, h - 10), fill=(240, 196, 40, 255))
        _texto_c(d, (w / 2, h * 0.76), "PELIGRO", _f(h * 0.1), (20, 20, 20, 255))
        _texto_c(d, (w / 2, h * 0.89), "ALTA TENSIÓN", _f(h * 0.08), (20, 20, 20, 255))
    return _png("aviso_tension", 512, 640, dib)


def generador_electrico():
    m = Modelo("generador_electrico", ZONA, (2, 2, 2), 3000,
               "Generador eléctrico: caja metálica sobre patín con orejetas de izado, rejillas de lamas inclinadas, "
               "escape lateral con silenciador y tapa basculante, puerta de acceso con bisagras y cerradura, display "
               "de voltaje verde, interruptor de palanca, 2 cables gruesos de salida con prensaestopas y toma de "
               "tierra.")
    c = m.parte()
    verde = m.parte("display_neon", tipo="neon", color="#39FF14", nota="Dígitos del display de voltaje.")
    rotulo = _png("rotulo_generador", 1024, 256, lambda d, im, w, h: (
        _texto_c(d, (w / 2, h * 0.35), "NE-GEN 40 kW", _f(h * 0.34), (236, 238, 232, 255)),
        _texto_c(d, (w / 2, h * 0.78), "COLONIA NUEVA ESPERANZA", _f(h * 0.15), (236, 238, 232, 255))))
    on_off = _png("on_off", 256, 256, lambda d, im, w, h: (
        _texto_c(d, (w / 2, h * 0.12), "ON", _f(56), (240, 240, 236, 255)),
        _texto_c(d, (w / 2, h * 0.88), "OFF", _f(56), (240, 240, 236, 255))))
    Wx, Wy, Hz, z0 = 1.7, 1.3, 1.25, 0.3
    yf = -Wy / 2
    cuerpo = m.mat("pintura", "#C9A227", desgaste=0.55, lluvia=0.5, hollin=None, calcos=[
        _calco(rotulo, (-0.62, yf, 1.42), (0.8, 0, 0), (0, 0, 0.2))])
    puerta_m = m.mat("pintura", "#C9A227", desgaste=0.55, lluvia=0.5, calcos=[
        _calco(_aviso_png(), (-0.36, yf - 0.03, 0.55), (0.22, 0, 0), (0, 0, 0.275))])
    panel = m.mat("pintura", "#2E3238", desgaste=0.4, calcos=[_calco(on_off, (0.27, yf - 0.03, 0.77),
                                                                     (0.18, 0, 0), (0, 0, 0.18))])
    patin = m.mat("pintura", "#2A2D31", desgaste=0.6, lluvia=0.5)
    acero = m.mat("metal", "#8A9097")
    osc = m.mat("metal", "#16181B", rug=0.4)
    escape = m.mat("oxido", "#6A4A36", hollin=(1.5, 1.95))
    negro = m.mat("goma", "#151617")
    rojo = m.mat("goma", "#7A1612")
    tierra = m.mat("goma", "#3C8A3A")
    m.seccion("patín y cuerpo")
    for y in (-0.48, 0.48):
        c.caja((0, y, 0.1), (1.9, 0.16, 0.2), patin, 0.015)
        for x in (-0.95, 0.95):  # orejetas de izado
            c.toro((x * 0.98, y, 0.22), 0.06, 0.016, acero, n=6, m=3, rot=(90, 0, 0))
    c.caja((0, 0, z0 + Hz / 2), (Wx, Wy, Hz), cuerpo, 0.03)
    c.caja((0, 0, z0 + Hz + 0.03), (Wx + 0.06, Wy + 0.06, 0.06), cuerpo, 0.015)  # tejadillo
    c.cil((0.5, 0.25, z0 + Hz + 0.06), (0.5, 0.25, z0 + Hz + 0.12), 0.07, osc, n=8)  # tapón de combustible
    c.toro((0, 0, z0 + Hz + 0.12), 0.07, 0.018, acero, n=6, m=3, rot=(90, 0, 0))  # cáncamo central
    m.seccion("rejillas")
    xl = -Wx / 2
    c.caja((xl - 0.005, 0, 0.95), (0.02, 0.96, 0.8), osc)
    for i in range(7):
        c.caja((xl - 0.03, 0, 0.64 + i * 0.105), (0.05, 0.9, 0.075), cuerpo, 0.004, rot=(0, 38, 0))
    c.caja((0, Wy / 2 + 0.005, 0.95), (1.2, 0.02, 0.7), osc)
    for i in range(6):
        c.caja((0, Wy / 2 + 0.03, 0.68 + i * 0.105), (1.14, 0.05, 0.075), cuerpo, 0.004, rot=(-38, 0, 0))
    m.seccion("escape")
    xe = Wx / 2
    c.cil((xe, 0.25, 1.1), (xe + 0.04, 0.25, 1.1), 0.11, acero, n=8)  # brida
    c.tubo([(xe, 0.25, 1.1), (xe + 0.17, 0.25, 1.12), (xe + 0.2, 0.25, 1.3)], 0.06, escape, n=8, seg=2)
    c.cil((xe + 0.2, 0.25, 1.28), (xe + 0.2, 0.25, 1.62), 0.12, escape, n=10)  # silenciador
    c.cil((xe + 0.2, 0.25, 1.62), (xe + 0.2, 0.25, 1.95), 0.05, escape, n=8)
    c.cil((xe + 0.2, 0.25, 1.96), (xe + 0.24, 0.25, 2.0), 0.06, acero, n=8)  # tapa basculante abierta
    c.cil((xe + 0.13, 0.25, 1.945), (xe + 0.13, 0.25, 1.955), 0.015, acero, n=4)
    for z in (1.36, 1.54):
        c.toro((xe + 0.2, 0.25, z), 0.125, 0.012, acero, n=10, m=3)
    m.seccion("puerta")
    c.caja((-0.25, yf - 0.006, 0.95), (0.9, 0.012, 1.0), osc)  # junta perimetral
    c.caja((-0.25, yf - 0.02, 0.95), (0.86, 0.03, 0.96), puerta_m, 0.01)
    for z in (0.62, 1.28):
        c.cil((-0.69, yf - 0.03, z - 0.07), (-0.69, yf - 0.03, z + 0.07), 0.022, acero, n=6)
    c.cil((0.12, yf - 0.035, 0.95), (0.12, yf - 0.07, 0.95), 0.035, acero, n=8)  # cerradura
    c.caja((0.12, yf - 0.075, 0.95), (0.03, 0.012, 0.15), acero, 0.004)  # maneta en T
    c.cil((0.12, yf - 0.071, 1.03), (0.12, yf - 0.075, 1.03), 0.008, osc, n=4)  # bombín
    m.seccion("panel de mando")
    c.caja((0.48, yf - 0.02, 1.02), (0.48, 0.04, 0.62), panel, 0.01)
    c.caja((0.48, yf - 0.045, 1.2), (0.38, 0.012, 0.16), m.mat("metal", "#06120A", rug=0.2), 0.004)
    verde.texto("400V", None, alto=0.09, grosor=0.006, c=(0.48, yf - 0.054, 1.158), fuente="mono", resol=1)
    c.caja((0.36, yf - 0.06, 0.86), (0.09, 0.04, 0.14), osc, 0.01)  # caja de la palanca
    c.cil((0.36, yf - 0.08, 0.86), (0.36, yf - 0.2, 0.95), 0.012, acero, n=5)  # palanca en ON
    c.esfera((0.36, yf - 0.205, 0.955), 0.025, rojo, seg=6, anillos=4)
    for x in (0.55, 0.64):  # pilotos
        c.cil((x, yf - 0.04, 0.88), (x, yf - 0.05, 0.88), 0.02, m.mat("plastico", "#2A7A2A"), n=6)
    m.seccion("cables y tierra")
    for x, mt in ((0.5, negro), (0.28, rojo)):
        c.cil((x, Wy / 2, 0.5), (x, Wy / 2 + 0.07, 0.5), 0.07, osc, n=8)  # prensaestopas
        c.tubo([(x, Wy / 2 + 0.05, 0.5), (x, Wy / 2 + 0.2, 0.46), (x + 0.1, Wy / 2 + 0.32, 0.12),
                (x + 0.35, Wy / 2 + 0.38, 0.05), (x + 0.6, Wy / 2 + 0.4, 0.05)], 0.045, mt, n=6, seg=2)
    c.tubo([(xl, -0.45, 0.4), (xl - 0.06, -0.5, 0.25), (xl - 0.08, -0.62, 0.06)], 0.012, tierra, n=4, seg=2)
    c.cil((xl - 0.08, -0.62, -0.02), (xl - 0.08, -0.62, 0.1), 0.018, m.mat("metal", "#B5703A"), n=5)
    m.terminar()


MODELOS = {
    "poste_indicador": poste_indicador,
    "puente_peatonal": puente_peatonal,
    "escalera_publica": escalera_publica,
    "marquesina_parada": marquesina_parada,
    "contenedor_basura": contenedor_basura,
    "antena_comunicaciones": antena_comunicaciones,
    "generador_electrico": generador_electrico,
}
