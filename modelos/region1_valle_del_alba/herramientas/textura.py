"""
Textura de color del terreno de la región (una imagen cuadrada que cubre la cara entera, ~0,9 studs por píxel a
4096 × 4096). Se pinta por capas con numpy, sin Blender:

  1. Pradera: tres verdes mezclados con ruido a varias escalas (manchas de hierba más seca y más fresca), con motas
     de flores.
  2. Suelo de bosque (más oscuro) donde hay bosque; tierra y roca en las laderas empinadas.
  3. Costa: arena en la orilla del mar y fondo marino (se ve a través del agua).
  4. Río: guijarros en la orilla y lecho.
  5. Caminos: tierra batida con bordes más oscuros, roderas y hierba que invade los bordes.
  6. Suelos de los sitios (adoquín, losas, plaza, tierra, césped) según pueblos.py.
  7. Campos de Los Molinos: cada parcela con su cultivo y sus surcos.

Los campos (distancias, coordenadas locales de los sitios, alturas) se calculan a la mitad de resolución y se
interpolan: son funciones suaves, así que los bordes salen nítidos igualmente.
"""

import math

import numpy as np
from scipy.ndimage import zoom

import diseno as D
import geo
import relieve as RV

COLORES = {
    "pradera_a": "#78A744", "pradera_b": "#93B850", "pradera_c": "#5E9440", "bosque": "#4B7836",
    "ladera": "#8C7A58", "roca": "#8A857A", "arena": "#DACB9A", "somero": "#86A196", "hondo": "#3A5F70",
    "guijarro": "#A79E8A", "lecho": "#6E6A55", "camino": "#BFA273", "camino_borde": "#9F8660",
    "adoquin": "#B3A994", "adoquin_junta": "#968C7B", "losas": "#C2B6A0", "plaza": "#CDBFA5",
    "plaza_anillo": "#B8A78C", "tierra": "#B49568", "cesped_ciudad": "#7DAF48", "cesped_pueblo": "#82AE4A",
    "prado": "#8DBC4E", "flor_amarilla": "#E9D259", "flor_blanca": "#F1EFE4", "flor_lila": "#B49ADB",
    "trigo": "#D9B65A", "trigo_surco": "#B89645", "col": "#5F9A48", "col_surco": "#6F5A40", "arado": "#866446",
    "arado_surco": "#6A4D35", "lavanda": "#9178C4", "lavanda_surco": "#5E7B48", "calabaza": "#6F9A42",
    "calabaza_surco": "#7A6040", "barbecho": "#A5B464", "barbecho_surco": "#97A55B",
}


def c(nombre):
    h = COLORES[nombre].lstrip("#")
    return np.array([int(h[i : i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


def mezclar(img, color, a):
    a = np.clip(a, 0, 1)[..., None].astype(np.float32)
    if isinstance(color, str):
        color = c(color)
    img *= 1 - a
    img += a * color
    return img


def rejilla(n):
    paso = 2 * geo.L / n
    g = -geo.L + (np.arange(n) + 0.5) * paso
    X, Y = np.meshgrid(g, g[::-1])  # fila 0 = norte (arriba en la imagen)
    return X, Y


def arriba(a, f):
    return zoom(a, f, order=1)


def pintar(valle, trazados, tam=4096, sitio_parcelas=None):
    V = valle
    n2 = tam // 2
    X2, Y2 = rejilla(n2)
    X, Y = rejilla(tam)
    f = tam / n2
    print("  textura: alturas")
    H2 = V.altura(X2, Y2)
    paso2 = 2 * geo.L / n2
    gy, gx = np.gradient(H2, paso2)
    pend2 = np.degrees(np.arctan(np.hypot(gx, gy)))
    H = arriba(H2, f)
    pend = arriba(pend2, f)

    img = np.zeros((tam, tam, 3), np.float32)
    # 1. pradera
    print("  textura: pradera")
    r1 = V.fbm2(X, Y, 260.0, 3, capa=11)
    r2 = V.fbm2(X, Y, 55.0, 3, capa=12)
    r3 = V.fbm2(X, Y, 9.0, 2, capa=13)
    img[:] = c("pradera_a")
    mezclar(img, "pradera_b", geo.suavizar(r1 + 0.35 * r2, 0.05, 0.4))
    mezclar(img, "pradera_c", geo.suavizar(-r1 + 0.3 * r2, 0.15, 0.5) * 0.8)
    img *= (1.0 + 0.06 * r3)[..., None]
    # motas de flores: umbral alto de un ruido fino, en manchas
    manchas = geo.suavizar(V.fbm2(X, Y, 140.0, 2, capa=14), 0.15, 0.4)
    mota = V.fbm2(X, Y, 2.2, 1, capa=15)
    mezclar(img, "flor_amarilla", (mota > 0.55) * manchas * 0.9)
    mota2 = V.fbm2(X, Y, 2.0, 1, capa=16)
    mezclar(img, "flor_blanca", (mota2 > 0.6) * geo.suavizar(V.fbm2(X, Y, 170.0, 2, capa=17), 0.2, 0.45) * 0.8)
    mezclar(img, "flor_lila", (mota > 0.6) * geo.suavizar(-V.fbm2(X, Y, 200.0, 2, capa=18), 0.25, 0.5) * 0.7)

    # 2. bosque y laderas
    print("  textura: bosque y laderas")
    bos = arriba(V.densidad_bosque(X2, Y2), f)
    mezclar(img, "bosque", geo.suavizar(bos, 0.1, 0.6) * 0.85)
    mezclar(img, "ladera", geo.suavizar(pend + 4 * r2, 22.0, 34.0) * 0.8)
    mezclar(img, "roca", geo.suavizar(pend + 4 * r2, 30.0, 42.0))

    # 3. costa
    mezclar(img, "arena", geo.suavizar(H + 0.8 * r2, 3.2, 1.2))
    mezclar(img, "somero", geo.suavizar(H, -0.5, -3.0))
    mezclar(img, "hondo", geo.suavizar(H, -6.0, -45.0))

    # 4. río
    print("  textura: río y caminos")
    d2, i2 = V.rio.cercano(X2, Y2)
    semi2 = V.rio.m[i2, 3]
    dr = arriba(d2 - semi2, f)  # distancia a la orilla (negativa dentro del cauce)
    mezclar(img, "guijarro", geo.suavizar(dr + 1.2 * r3, 4.5, 1.0))
    mezclar(img, "lecho", geo.suavizar(dr, -1.0, -6.0))
    cx, cy, rc = D.CHARCA_MANANTIAL
    dc = np.hypot(X - cx, Y - cy) - rc
    mezclar(img, "guijarro", geo.suavizar(dc + 1.2 * r3, 4.0, 1.0))

    # 5. caminos
    for nombre, cam in D.CAMINOS.items():
        d2, _ = V.caminos[nombre].cercano(X2, Y2)
        d = arriba(d2, f)
        w = cam["ancho"] / 2
        borde = w + 1.5 * r3 + 0.8 * r2
        mezclar(img, "camino_borde", geo.suavizar(d - borde, 1.2, -0.6) * 0.9)
        mezclar(img, "camino", geo.suavizar(d - borde, -0.4, -2.0))
        # roderas: dos franjas algo más oscuras
        if cam["ancho"] >= 8:
            rod = np.exp(-(((d - w * 0.45) / 0.7) ** 2))
            mezclar(img, "camino_borde", rod * 0.35 * (d < w))
        img *= (1.0 + 0.05 * r3 * (d < w))[..., None]

    # 6. sitios
    for nombre, t in trazados.items():
        print(f"  textura: {nombre}")
        s = V.sitios[nombre]
        u2, v2 = s.local(geo.direccion(X2, Y2))
        U, Vv = arriba(u2, f), arriba(v2, f)
        rmax = max(D.SITIOS[nombre]["ancho"], D.SITIOS[nombre]["fondo"]) / 2 + 400
        cerca = (np.abs(U) < rmax) & (np.abs(Vv) < rmax)
        filas = np.where(cerca.any(axis=1))[0]
        cols = np.where(cerca.any(axis=0))[0]
        if not len(filas):
            continue
        sl = (slice(filas[0], filas[-1] + 1), slice(cols[0], cols[-1] + 1))
        u, v = U[sl], Vv[sl]
        sub = img[sl]
        rr = r3[sl]
        for tipo, forma in t.suelos:
            sd = sdf_forma(forma, u, v)
            a = geo.suavizar(sd + 0.5 * rr, 0.6, -0.6)
            mezclar(sub, tipo_color(tipo), a)
            if tipo == "adoquin":
                junta = (np.abs(((u + 0.5 * (np.floor(v / 2.0) % 2)) % 2.0) - 1.0) > 0.85) | (
                    np.abs((v % 2.0) - 1.0) > 0.85)
                mezclar(sub, "adoquin_junta", a * junta * 0.6)
            if tipo in ("plaza", "losas"):
                lado = 4.0 if tipo == "plaza" else 3.0
                junta = (np.abs((u % lado) - lado / 2) > lado / 2 - 0.35) | (np.abs((v % lado) - lado / 2) > lado / 2 - 0.35)
                mezclar(sub, "adoquin", a * junta * 0.55)
        if t.parcelas:
            pintar_parcelas(sub, u, v, t.parcelas, rr)
        img[sl] = sub
    return np.clip(img, 0, 1), H


def tipo_color(tipo):
    return {"cesped_ciudad": "cesped_ciudad", "cesped_pueblo": "cesped_pueblo", "adoquin": "adoquin",
            "losas": "losas", "plaza": "plaza", "plaza_anillo": "plaza_anillo", "tierra": "tierra",
            "prado": "prado"}[tipo]


def sdf_forma(forma, u, v):
    k = forma[0]
    if k == "rect":
        _, u0, v0, u1, v1, esq = forma
        return RV.sdf_rectangulo(u - (u0 + u1) / 2, v - (v0 + v1) / 2, (u1 - u0) / 2, (v1 - v0) / 2,
                                 min(esq, (u1 - u0) / 2, (v1 - v0) / 2))
    if k == "circulo":
        _, cu, cv, r = forma
        return np.hypot(u - cu, v - cv) - r
    if k == "linea":
        _, pts, ancho = forma
        d = np.full(u.shape, 1e9)
        for (a, b) in zip(pts[:-1], pts[1:]):
            a, b = np.asarray(a, float), np.asarray(b, float)
            ab = b - a
            t = np.clip(((u - a[0]) * ab[0] + (v - a[1]) * ab[1]) / (ab @ ab), 0, 1)
            d = np.minimum(d, np.hypot(u - a[0] - t * ab[0], v - a[1] - t * ab[1]))
        return d - ancho / 2
    raise ValueError(k)


def local_parcela(p, u, v):
    g = math.radians(p["giro"])
    cu, cv = p["centro"]
    du, dv = u - cu, v - cv
    a = du * math.cos(g) + dv * math.sin(g)  # a lo ancho
    b = -du * math.sin(g) + dv * math.cos(g)  # a lo largo (los surcos van a lo largo)
    return a, b


def pintar_parcelas(img, u, v, parcelas, ruido):
    for p in parcelas:
        a, b = local_parcela(p, u, v)
        sd = RV.sdf_rectangulo(a, b, p["ancho"] / 2, p["largo"] / 2, 2.0)
        dentro = geo.suavizar(sd + 0.6 * ruido, 0.8, -0.8)
        if not dentro.any():
            continue
        cult = p["cultivo"]
        mezclar(img, cult, dentro)
        surco = 0.5 + 0.5 * np.cos(2 * math.pi * a / 3.2)
        mezclar(img, cult + "_surco", dentro * geo.suavizar(surco, 0.55, 0.9) * 0.8)
        # linde de hierba alrededor
        mezclar(img, "pradera_b", geo.suavizar(np.abs(sd + 1.0), 1.2, 0.2) * 0.7)
