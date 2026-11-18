"""
Materiales procedurales de la casa del ingeniero. Se hornean al atlas (color, normal, rugosidad, metal, emisión).

Paleta: blancos y grises limpios (es la casa más técnica del pueblo, «sin color»). El color solo aparece donde
tiene una función: avisos amarillos, LEDs, cables codificados, el botón de arranque, el contenedor de RAEE.
La historia: todo está limpio y ordenado, menos la silla de pensar, que está gastadísima.

Todo lo ajustable (colores, periodos de los paneles, rugosidades) está en PALETA y en los argumentos.
"""

import kit_casas as K

PALETA = {
    "panel_casa": "#dfe2e1",       # paneles de la casa: blanco roto muy limpio
    "panel_casa_b": "#d3d7d8",     # variación de un panel a otro
    "panel_lab": "#b9bfc3",        # el lab: gris claro
    "panel_lab_b": "#aeb4b9",
    "remate": "#5b6167",           # zócalos, remates, esquinas
    "metal_oscuro": "#3d4349",     # marcos, bisagras, soportes
    "puerta": "#7d858c",           # puertas metálicas
    "aluminio": "#c4c8cc",
    "galvanizado": "#a9aeb2",
    "hormigon": "#aaa69e",
    "hormigon_limpio": "#b9b5ad",
    "techo": "#8d9195",
    "goma": "#1d1e20",
    "amarillo": "#e8b923",
    "negro_aviso": "#1b1b1c",
    "interior": "#8a847a",
    "interior_suelo": "#55514c",
    "silla_pintura": "#6e7a73",    # verde grisáceo de silla plegable
    "acero_desnudo": "#b4b6b6",
    "generador": "#4f5a54",
    "contenedor": "#3e5f78",
    "celula": "#14234d",
    "celula_b": "#1b2f63",
    "cobre": "#c27a43",
    "pcb": "#1f5c35",
    "cuaderno": "#22314d",
    "papel": "#ece5cf",
    "lapiz": "#e3b02c",
    "madera_lapiz": "#d9b27c",
    "blanco_sensor": "#eceeed",
}

P = PALETA
M = K.Materiales()


# ----------------------------------------------------------------------------------------------------------
# Utilidades de patrones
# ----------------------------------------------------------------------------------------------------------


def coord_pared(g):
    """Coordenada horizontal a lo largo de cualquier pared alineada con los ejes (x en las de ±Y, y en las de ±X)."""
    Pv, N = g.P(), g.N()
    ax = N.x.abs()
    return Pv.x * (1.0 - ax) + Pv.y * ax


def distancia_junta(g, coord, periodo, desfase=0.0):
    """Distancia (en studs) a la junta más cercana de una serie de juntas cada `periodo`."""
    return (((coord - desfase) / periodo + 0.5).fract() - 0.5).abs() * periodo


def brillo_arista(g, col, cantidad=0.25, radio=0.04):
    """Las aristas reciben un poco más de luz (y desgaste en la pintura): no parece plástico."""
    return g.mezcla(col, (1.0, 1.0, 1.0), g.arista(radio) * cantidad)


def piel_pintura(g, escala=60.0):
    """Piel de naranja muy fina de la pintura en polvo (solo relieve)."""
    return g.ruido(g.P(), escala, 2) * 0.0012


# ----------------------------------------------------------------------------------------------------------
# Paneles de las paredes
# ----------------------------------------------------------------------------------------------------------


def _panel(g, base, base_b, ancho=2.2, alto=2.9, z0=0.85, tornillos=0.72):
    Pv = g.P()
    u = coord_pared(g)
    du = distancia_junta(g, u, ancho)
    dz = distancia_junta(g, Pv.z, alto, z0)
    junta = g.suave(0.045, 0.02, du).max(g.suave(0.045, 0.02, dz))
    # tornillos a los dos lados de cada junta vertical, cada `tornillos` studs
    dzt = distancia_junta(g, Pv.z, tornillos, z0 + tornillos / 2)
    r = g.comb(du - 0.14, dzt, 0.0).largo()
    perno = g.suave(0.04, 0.026, r)
    # tono de cada panel
    idp = g.comb((u / ancho).floor(), ((Pv.z - z0) / alto).floor(), 0.0)
    tono = g.azar(idp)
    nube = g.ruido(Pv, 0.9, 5)
    col = g.mezcla(base, base_b, tono * 0.55 + nube * 0.25)
    col = g.mezcla(col, "#7e8487", junta * 0.85)
    col = g.mezcla(col, "#8d9396", perno * 0.6)
    col = brillo_arista(g, col, 0.22)
    h = -junta * 0.022 + perno * 0.012 + piel_pintura(g)
    rug = g.mezcla(0.42, 0.3, perno) + nube * 0.06
    return {"col": col, "rug": rug, "met": perno * 0.6, "h": h, "fuerza_relieve": 1.0}


@M.definir("panel_casa")
def _(g):
    return _panel(g, P["panel_casa"], P["panel_casa_b"])


@M.definir("panel_lab")
def _(g):
    return _panel(g, P["panel_lab"], P["panel_lab_b"], ancho=1.35, alto=2.2, z0=0.6)


@M.definir("panel_pasillo")
def _(g):
    # nervado horizontal (chapa grecada) para el pasillo
    Pv = g.P()
    onda = ((Pv.z / 0.32).fract() - 0.5).abs() * 2.0
    col = g.mezcla(P["panel_lab"], P["panel_lab_b"], onda * 0.6)
    col = brillo_arista(g, col, 0.2)
    return {"col": col, "rug": 0.45, "met": 0.0, "h": g.suave(0.2, 0.8, onda) * 0.03}


def _pintura(g, color, rug=0.45, met=0.0, arista=0.22, sucio=0.0):
    Pv = g.P()
    n = g.ruido(Pv, 2.5, 5)
    col = g.mezcla(color, K_oscurecer(color, 0.85), n * 0.4)
    if sucio:
        col = g.mezcla(col, K_oscurecer(color, 0.6), g.suave(0.55, 0.8, g.ruido(Pv, 1.2, 6)) * sucio)
    col = brillo_arista(g, col, arista)
    return {"col": col, "rug": rug + n * 0.08, "met": met, "h": piel_pintura(g)}


def K_oscurecer(hexa, k):
    hexa = hexa.lstrip("#")
    c = [min(255, max(0, int(int(hexa[i:i + 2], 16) * k))) for i in (0, 2, 4)]
    return "#%02x%02x%02x" % tuple(c)


@M.definir("remate")
def _(g):
    return _pintura(g, P["remate"], 0.42, 0.0, 0.3)


@M.definir("metal_oscuro")
def _(g):
    d = _pintura(g, P["metal_oscuro"], 0.38, 0.75, 0.35)
    return d


@M.definir("puerta")
def _(g):
    Pv = g.P()
    # chapa con dos pliegues horizontales de refuerzo (en relieve) y piel de pintura
    dz = distancia_junta(g, Pv.z, 1.6, 0.55 + 0.8)
    pliegue = g.suave(0.05, 0.015, dz)
    n = g.ruido(Pv, 3.0, 5)
    col = g.mezcla(P["puerta"], K_oscurecer(P["puerta"], 0.88), n * 0.4)
    col = g.mezcla(col, K_oscurecer(P["puerta"], 0.7), pliegue * 0.5)
    col = brillo_arista(g, col, 0.3)
    return {"col": col, "rug": 0.4 + n * 0.08, "met": 0.15, "h": -pliegue * 0.015 + piel_pintura(g)}


@M.definir("interior", uv=0.18)
def _(g):
    return {"col": g.mezcla(P["interior"], "#6f6a62", g.ruido(g.P(), 0.6, 3) * 0.5), "rug": 0.85}


@M.definir("interior_suelo", uv=0.18)
def _(g):
    return {"col": P["interior_suelo"], "rug": 0.7}


# ----------------------------------------------------------------------------------------------------------
# Metales
# ----------------------------------------------------------------------------------------------------------


@M.definir("aluminio")
def _(g):
    Pv = g.P()
    cep = g.ruido(g.comb(Pv.x * 2.0, Pv.y * 2.0, Pv.z * 2.0) + g.comb(Pv.x * 90.0, 0.0, 0.0) + g.comb(
        0.0, Pv.y * 90.0, 0.0), 1.0, 3)
    col = g.mezcla(P["aluminio"], "#aeb3b8", cep * 0.6)
    col = brillo_arista(g, col, 0.3, 0.03)
    return {"col": col, "rug": 0.28 + cep * 0.12, "met": 1.0, "h": cep * 0.0015}


@M.definir("galvanizado")
def _(g):
    Pv = g.P()
    v = g.voronoi(Pv, 9.0, "Color")
    tono = g.lum(v)
    col = g.mezcla(P["galvanizado"], "#c2c6c9", tono)
    col = brillo_arista(g, col, 0.25, 0.03)
    return {"col": col, "rug": 0.36 + tono * 0.16, "met": 1.0, "h": tono * 0.001}


@M.definir("acero")
def _(g):
    Pv = g.P()
    n = g.ruido(Pv, 6.0, 4)
    return {"col": brillo_arista(g, g.mezcla("#9a9ea2", "#868a8e", n), 0.3, 0.02), "rug": 0.32 + n * 0.1,
            "met": 1.0}


@M.definir("escape")
def _(g):
    # tubo de escape: acero con el azulado/ocre del calor cerca de la salida
    Pv = g.P()
    n = g.ruido(Pv, 4.0, 5)
    calor = g.suave(1.3, 2.4, Pv.z)
    col = g.mezcla("#5d5a56", "#7a5f42", calor * 0.7 + n * 0.2)
    col = g.mezcla(col, "#3a4256", g.suave(0.55, 0.75, n) * calor * 0.6)
    return {"col": col, "rug": 0.55 + n * 0.2, "met": 0.85}


@M.definir("goma")
def _(g):
    n = g.ruido(g.P(), 8.0, 3)
    return {"col": g.mezcla(P["goma"], "#2a2b2d", n * 0.5), "rug": 0.82, "met": 0.0, "h": n * 0.002}


def _cable(color):
    def f(g):
        n = g.ruido(g.P(), 12.0, 3)
        return {"col": brillo_arista(g, g.mezcla(color, K_oscurecer(color, 0.8), n * 0.4), 0.15, 0.02),
                "rug": 0.45, "met": 0.0}
    return f


for _n, _c in (("cable_negro", "#222326"), ("cable_rojo", "#a3241f"), ("cable_azul", "#1f4f9a"),
               ("cable_amarillo", "#d4a51c"), ("cable_gris", "#6d7276")):
    M.definir(_n)(_cable(_c))


# ----------------------------------------------------------------------------------------------------------
# Hormigón y techo
# ----------------------------------------------------------------------------------------------------------


def _hormigon(g, base, juntas=None):
    Pv = g.P()
    n1 = g.ruido(Pv, 0.7, 6)
    n2 = g.ruido(Pv, 7.0, 4)
    poro = g.suave(0.07, 0.03, g.voronoi(Pv, 16.0))
    col = g.mezcla(base, K_oscurecer(base, 0.86), n1 * 0.8)
    col = g.mezcla(col, K_oscurecer(base, 0.7), poro * 0.5)
    h = n2 * 0.004 - poro * 0.006
    if juntas:
        u, v = Pv.x, Pv.y
        j = g.suave(0.04, 0.015, distancia_junta(g, u, juntas)).max(
            g.suave(0.04, 0.015, distancia_junta(g, v, juntas, 0.3)))
        col = g.mezcla(col, K_oscurecer(base, 0.55), j * 0.8)
        h = h - j * 0.02
    col = brillo_arista(g, col, 0.2, 0.05)
    return {"col": col, "rug": 0.82 + n2 * 0.1, "met": 0.0, "h": h}


@M.definir("hormigon", uv=0.7)
def _(g):
    return _hormigon(g, P["hormigon"])


@M.definir("hormigon_limpio", uv=0.45)
def _(g):
    # la explanada que el ingeniero barre: juntas de dilatación cada 2,5 studs, sin manchas
    return _hormigon(g, P["hormigon_limpio"], juntas=2.5)


@M.definir("techo", uv=0.6)
def _(g):
    Pv = g.P()
    n = g.ruido(Pv, 25.0, 2)
    nube = g.ruido(Pv, 0.8, 4)
    # tiras de lámina soldadas cada 1,8 studs (solape en relieve)
    d = distancia_junta(g, Pv.x, 1.8)
    solape = g.suave(0.06, 0.03, d)
    col = g.mezcla(P["techo"], "#7f8387", nube * 0.6)
    col = g.mezcla(col, "#9a9ea2", solape * 0.5)
    return {"col": col, "rug": 0.78, "met": 0.0, "h": n * 0.003 + solape * 0.01}


# ----------------------------------------------------------------------------------------------------------
# Patrones con el mapa «decal» (0..1 en la cara)
# ----------------------------------------------------------------------------------------------------------


def _celulas(g, nx, ny):
    D = g.D()
    u, v = D.x * nx, D.y * ny
    fu, fv = u.fract(), v.fract()
    hueco = g.suave(0.45, 0.475, (fu - 0.5).abs()).max(g.suave(0.45, 0.475, (fv - 0.5).abs()))
    bus = g.suave(0.012, 0.006, (((fu * 3.0).fract() - 0.5).abs()) / 3.0)
    dedos = g.suave(0.18, 0.06, ((fv * 22.0).fract() - 0.5).abs())
    tono = g.azar(g.comb(u.floor(), v.floor(), 0.0))
    col = g.mezcla(P["celula"], P["celula_b"], tono * 0.7)
    col = g.mezcla(col, "#2a3f78", dedos * 0.35)
    col = g.mezcla(col, "#b9bec4", bus)
    col = g.mezcla(col, "#d9dde1", hueco)
    rug = g.mezcla(0.1, 0.35, hueco)
    return {"col": col, "rug": rug, "met": bus * 0.8, "h": bus * 0.004 - hueco * 0.004}


@M.definir("celulas", uv=1.6)
def _(g):
    return _celulas(g, 6, 10)


@M.definir("celulas_suelo", uv=1.6)
def _(g):
    return _celulas(g, 6, 4)


@M.definir("panel_trasero")
def _(g):
    return {"col": "#e6e7e3", "rug": 0.6}


@M.definir("rejilla", uv=1.4)
def _(g):
    # lamas horizontales de ventilación (en el mapa decal)
    D = g.D()
    f = (D.y * 9.0).fract()
    lama = g.suave(0.15, 0.3, f) * g.suave(0.95, 0.8, f)
    borde = g.suave(0.02, 0.05, D.x).min(g.suave(0.98, 0.95, D.x)).min(g.suave(0.02, 0.05, D.y)).min(
        g.suave(0.98, 0.95, D.y))
    col = g.mezcla("#121315", "#5c6268", lama * borde + (1.0 - borde))
    return {"col": col, "rug": 0.5, "met": 0.5, "h": (f * lama) * borde * 0.03}


@M.definir("rejilla_generador", uv=1.4)
def _(g):
    D = g.D()
    f = (D.y * 7.0).fract()
    lama = g.suave(0.12, 0.3, f) * g.suave(0.95, 0.75, f)
    col = g.mezcla("#151716", P["generador"], lama)
    col = brillo_arista(g, col, 0.15)
    return {"col": col, "rug": 0.5, "met": 0.2, "h": f * lama * 0.03}


@M.definir("rejilla_suelo", uv=1.2)
def _(g):
    # tramex del escalón: rejilla de pletinas con huecos
    Pv = g.P()
    a = ((Pv.x / 0.16).fract() - 0.5).abs()
    b = ((Pv.y / 0.16).fract() - 0.5).abs()
    hueco = g.suave(0.36, 0.3, a) * g.suave(0.36, 0.3, b)
    col = g.mezcla("#8b9095", "#0e0f10", hueco)
    return {"col": col, "rug": 0.5, "met": g.mezcla(0.9, 0.0, hueco), "h": -hueco * 0.04}


@M.definir("ventilador", uv=1.4)
def _(g):
    # rejilla redonda del extractor: anillos concéntricos y radios
    D = g.D()
    c = g.comb(D.x - 0.5, D.y - 0.5, 0.0)
    r = c.largo()
    anillo = g.suave(0.25, 0.4, ((r * 9.0).fract() - 0.5).abs() * 2.0)
    radio = g.suave(0.06, 0.03, ((c.x * 4.0).abs() - 0.0).min((c.y * 4.0).abs()))
    metal = (1.0 - anillo).max(radio)
    col = g.mezcla("#0d0e0f", "#8a9096", metal)
    return {"col": col, "rug": 0.45, "met": metal * 0.8, "h": metal * 0.02}


@M.definir("aviso", uv=1.2)
def _(g):
    # franjas amarillas y negras en diagonal
    Pv = g.P()
    f = ((Pv.x + Pv.y + Pv.z) / 0.5).fract()
    franja = g.suave(0.48, 0.52, f)
    n = g.ruido(Pv, 5.0, 4)
    col = g.mezcla(P["amarillo"], P["negro_aviso"], franja)
    col = brillo_arista(g, col, 0.2)
    return {"col": col, "rug": 0.5 + n * 0.1, "met": 0.0}


@M.definir("leds_equipo", uv=2.0)
def _(g):
    # frontal de un equipo: filas de LEDs de colores, unos encendidos y otros no
    D = g.D()
    u, v = D.x * 10.0, D.y * 4.0
    c = g.comb(u.fract() - 0.5, v.fract() - 0.5, 0.0)
    punto = g.suave(0.22, 0.14, c.largo())
    al = g.azar(g.comb(u.floor(), v.floor(), 3.0))
    encendido = g.suave(0.35, 0.4, al)
    tono = g.azar(g.comb(u.floor(), v.floor(), 7.0))
    led = g.mezcla(g.mezcla("#38ff7a", "#ffb030", g.suave(0.6, 0.65, tono)), "#ff3b30", g.suave(0.88, 0.9, tono))
    zona = g.suave(0.02, 0.06, D.y).min(g.suave(0.98, 0.94, D.y))
    col = g.mezcla("#1e2023", g.mezcla("#2a2d30", led, encendido), punto * zona)
    emi = led * (punto * encendido * zona * 1.0)
    return {"col": col, "rug": 0.45, "met": 0.1, "emi": emi, "fuerza_emi": 3.0, "h": punto * zona * 0.006}


@M.definir("pcb", uv=1.8)
def _(g):
    D = g.D()
    pista_u = g.suave(0.08, 0.04, ((D.x * 16.0).fract() - 0.5).abs())
    pista_v = g.suave(0.08, 0.04, ((D.y * 11.0).fract() - 0.5).abs())
    mascara = g.suave(0.45, 0.55, g.ruido(g.comb(D.x * 3.0, D.y * 3.0, 0.0), 1.0, 2))
    pistas = pista_u * mascara + pista_v * (1.0 - mascara)
    c = g.comb(((D.x * 8.0).fract() - 0.5), ((D.y * 6.0).fract() - 0.5), 0.0)
    pad = g.suave(0.14, 0.1, c.largo())
    col = g.mezcla(P["pcb"], "#2f8a52", pistas * 0.7)
    col = g.mezcla(col, "#d6b25a", pad)
    return {"col": col, "rug": g.mezcla(0.35, 0.25, pad), "met": pad, "h": pistas * 0.002 + pad * 0.003}


@M.definir("cobre")
def _(g):
    Pv = g.P()
    vuelta = g.suave(0.3, 0.1, (((Pv.x + Pv.y + Pv.z) * 22.0).fract() - 0.5).abs())
    n = g.ruido(Pv, 6.0, 3)
    col = g.mezcla(P["cobre"], "#8e5530", vuelta * 0.5 + n * 0.2)
    return {"col": col, "rug": 0.3 + n * 0.1, "met": 1.0, "h": -vuelta * 0.004}


@M.definir("cristal_oscuro")
def _(g):
    # mirillas, lentes y pantallas apagadas: casi negro, muy liso
    n = g.ruido(g.P(), 1.5, 2)
    return {"col": g.mezcla("#0a1418", "#16262c", n), "rug": 0.06, "met": 0.0}


def _led(color, fuerza=4.0):
    def f(g):
        return {"col": color, "rug": 0.2, "met": 0.0, "emi": g._rgb(color), "fuerza_emi": fuerza}
    return f


for _n, _c in (("led_verde", "#3dff7c"), ("led_rojo", "#ff3326"), ("led_ambar", "#ffb02e"),
               ("led_blanco", "#e8f4ff"), ("led_azul", "#3aa8ff")):
    M.definir(_n)(_led(_c))


# ----------------------------------------------------------------------------------------------------------
# Letreros: una sola hoja de imágenes para todos (rutas fijadas desde el script de la casa)
# ----------------------------------------------------------------------------------------------------------

RUTAS_LETREROS = {"color": None, "props": None}


@M.definir("letrero", uv=3.6)
def _(g):
    col, _a = g.imagen(RUTAS_LETREROS["color"])
    props, emi_m = g.imagen(RUTAS_LETREROS["props"], datos=True)
    n = g.n("ShaderNodeSeparateColor")
    g.enlazar(props, n.inputs[0])
    met = K.S(g, n.outputs[0], "f")
    rug = K.S(g, n.outputs[1], "f")
    rel = K.S(g, n.outputs[2], "f")
    # el alfa de la imagen de propiedades es la máscara de emisión
    col = brillo_arista(g, col, 0.15, 0.015)
    return {"col": col, "rug": rug, "met": met, "emi": col * emi_m, "fuerza_emi": 3.0,
            "h": (rel - 0.5) * 0.02}


# ----------------------------------------------------------------------------------------------------------
# Objetos con historia
# ----------------------------------------------------------------------------------------------------------

SILLA = {"centro_asiento": (0.0, 0.0)}  # se fija desde el script (coordenadas del mundo)


@M.definir("silla", uv=1.5)
def _(g):
    """
    Silla plegable de pensar: pintura verde grisácea gastada hasta el acero en las aristas, en el centro del
    asiento y en el respaldo (donde se apoya), con arañazos finos. Es lo único viejo de la casa.
    """
    Pv, N = g.P(), g.N()
    arista = g.arista(0.035)
    n = g.ruido(Pv, 9.0, 6)
    n2 = g.ruido(Pv, 2.2, 4)
    descon = g.suave(0.5, 0.6, arista * 0.95 + n * 0.45)
    cx, cy = SILLA["centro_asiento"]
    arriba = g.suave(0.6, 0.95, N.z)
    d = g.comb((Pv.x - cx) / 0.42, (Pv.y - cy) / 0.38, 0.0).largo()
    roce = arriba * g.suave(1.0, 0.25, d) * (n2 * 0.7 + 0.45)
    arañazo = g.suave(0.62, 0.66, g.ruido(g.comb(Pv.x * 40.0, Pv.y * 3.0, Pv.z * 3.0), 1.0, 2)) * 0.8
    desnudo = descon.max(g.suave(0.35, 0.6, roce)).max(arañazo * g.suave(0.3, 0.7, n2))
    pintura = g.mezcla(P["silla_pintura"], "#5f6a63", n2 * 0.6)
    pintura = g.mezcla(pintura, "#8a948d", g.suave(0.5, 0.9, n) * 0.3)  # pintura descolorida por el sol
    metal = g.mezcla(P["acero_desnudo"], "#8e8a84", n * 0.6)
    col = g.mezcla(pintura, metal, desnudo)
    col = g.mezcla(col, "#6b5a48", g.suave(0.7, 0.85, n2) * desnudo * 0.25)  # algo de óxido donde hay acero
    return {"col": col, "rug": g.mezcla(0.62, 0.3, desnudo), "met": desnudo,
            "h": desnudo * -0.004 + piel_pintura(g)}


@M.definir("cuaderno_tapa", uv=1.8)
def _(g):
    Pv = g.P()
    arista = g.arista(0.02)
    n = g.ruido(Pv, 14.0, 4)
    col = g.mezcla(P["cuaderno"], "#3a4a68", arista * 0.8 + n * 0.15)  # esquinas gastadas
    return {"col": col, "rug": 0.75, "met": 0.0, "h": n * 0.002}


@M.definir("cuaderno_hojas", uv=1.8)
def _(g):
    Pv = g.P()
    hoja = g.suave(0.3, 0.1, ((Pv.z / 0.007).fract() - 0.5).abs())
    col = g.mezcla(P["papel"], "#cfc7ad", hoja * 0.6)
    return {"col": col, "rug": 0.85, "met": 0.0, "h": -hoja * 0.002}


@M.definir("lapiz", uv=2.0)
def _(g):
    return {"col": brillo_arista(g, P["lapiz"], 0.2, 0.01), "rug": 0.4, "met": 0.0}


@M.definir("madera_lapiz", uv=2.0)
def _(g):
    return {"col": P["madera_lapiz"], "rug": 0.7, "met": 0.0}


@M.definir("grafito", uv=2.0)
def _(g):
    return {"col": "#2b2b2d", "rug": 0.35, "met": 0.5}


@M.definir("goma_borrar", uv=2.0)
def _(g):
    return {"col": "#d47f7d", "rug": 0.8, "met": 0.0}


@M.definir("generador")
def _(g):
    return _pintura(g, P["generador"], 0.48, 0.0, 0.3)


@M.definir("contenedor")
def _(g):
    Pv = g.P()
    d = _pintura(g, P["contenedor"], 0.55, 0.0, 0.25)
    # costillas verticales del contenedor de plástico rígido
    costilla = g.suave(0.05, 0.02, distancia_junta(g, coord_pared(g), 0.35))
    d["col"] = g.mezcla(d["col"], K_oscurecer(P["contenedor"], 0.8), costilla * 0.5)
    d["h"] = costilla * 0.012
    return d


@M.definir("blanco_sensor")
def _(g):
    return _pintura(g, P["blanco_sensor"], 0.4, 0.0, 0.15)


@M.definir("rojo_boton")
def _(g):
    return _pintura(g, "#c3261f", 0.3, 0.0, 0.3)


@M.definir("verde_boton")
def _(g):
    return _pintura(g, "#2e9a48", 0.3, 0.0, 0.3)


@M.definir("amarillo_pintura")
def _(g):
    return _pintura(g, P["amarillo"], 0.45, 0.0, 0.25)


@M.definir("escoba_cerdas", uv=1.0)
def _(g):
    Pv = g.P()
    f = g.ruido(g.comb(Pv.x * 60.0, Pv.y * 60.0, Pv.z * 2.0), 1.0, 2)
    return {"col": g.mezcla("#3b3b3d", "#56575a", f), "rug": 0.8, "met": 0.0, "h": f * 0.006}


@M.definir("madera_mango", uv=1.0)
def _(g):
    Pv = g.P()
    veta = g.ruido(g.comb(Pv.x * 30.0, Pv.y * 30.0, Pv.z * 1.5), 1.0, 3)
    return {"col": g.mezcla("#a8794a", "#8a5f37", veta), "rug": 0.55, "met": 0.0}


# ----------------------------------------------------------------------------------------------------------
# Piezas que en Roblox van con material propio (no usan el atlas)
# ----------------------------------------------------------------------------------------------------------


@M.definir("cristal", especial="cristal")
def _(g):
    return {"col": (0.86, 0.93, 0.96), "rug": 0.02}


@M.definir("neon_blanco", especial="neon")
def _(g):
    return {"col": "#dff1ff", "rug": 0.2, "met": 0.0, "emi": g._rgb("#dff1ff"), "fuerza_emi": 12.0}
