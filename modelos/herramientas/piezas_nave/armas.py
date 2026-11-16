"""
Armas. Apuntan a -Y (delante). Todas (salvo las torretas) llevan un bloque de montaje con tres entradas:
  acople_colgar        encima (normal +Z), ALA_PUNTA: bajo la punta del ala o en un hardpoint
  acople_lateral_izq   en su costado izquierdo (+X), CASCO_LATERAL: se monta en el costado DERECHO del casco
  acople_lateral_der   en su costado derecho (-X), CASCO_LATERAL: se monta en el costado IZQUIERDO del casco
Así el mismo modelo sirve en los dos lados sin reflejarlo y el cañón siempre mira hacia delante.
Las pesadas tienen además acople_trasero (normal +Y, CASCO_FRONTAL) para ir en la proa.
Las torretas se apoyan en acople_base (CASCO_SUPERIOR) y su cabeza es una malla aparte (`_cabeza`) para girarla.
En el JSON, `anclajes_vfx` da las bocas de fuego (posición y dirección) para el fogonazo y el proyectil.
"""

import math

from .geo import V, Matrix


def _color(con, p):
    con.colores_extra.update(p.get("color", {}))
    if "paleta" in p:
        con.info["paleta"] = p["paleta"]


def montaje(con, y, z, largo=1.8, frontal=False, ancho=1.0, alto=1.7):
    """Bloque de montaje con las bridas de entrada (arriba y a los dos lados)."""
    con.caja((0, y, z), (ancho, largo, alto), "oscuro")
    con.caja((0, y, z + alto / 2 + 0.06), (ancho * 0.9, min(largo, 1.0), 0.12), "secundario")
    con.acople("acople_colgar", (0, y, z + alto / 2 + 0.12), (0, 0, 1), "ALA_PUNTA", "entrada",
               acepta=["ALA_PUNTA", "UNIVERSAL"], en_superficie=True)
    con.acople("acople_lateral_izq", (ancho / 2, y, z), (1, 0, 0), "CASCO_LATERAL", "entrada",
               acepta=["CASCO_LATERAL"], en_superficie=True)
    con.acople("acople_lateral_der", (-ancho / 2, y, z), (-1, 0, 0), "CASCO_LATERAL", "entrada",
               acepta=["CASCO_LATERAL"], en_superficie=True)
    if frontal:
        con.acople("acople_trasero", (0, y + largo / 2, z), (0, 1, 0), "CASCO_FRONTAL", "entrada",
                   acepta=["CASCO_FRONTAL"], en_superficie=True)


def boca(con, nombre, pos, d=(0, -1, 0)):
    con.info.setdefault("vfx", []).append({"nombre": nombre, "pos": V(pos), "dir": V(d)})


def canon(con, base, largo, r, ranura="metal", lados=12, freno=True, eje=(0, -1, 0), nombre="boca", anillos=(),
          ranura_anillo="secundario", hueco=True):
    """Cañón a lo largo de `eje` desde `base`, con freno de boca y anillos opcionales."""
    e = V(eje).normalized()
    b = V(base)
    if hueco:
        con.tubo(b, e, r, r * 0.55, largo, ranura, lados=lados)
    else:
        con.cilindro(b, e, r, largo, ranura, lados=lados)
    if freno:
        con.tubo(b + e * (largo - 0.35), e, r * 1.45, r * 0.6, 0.38, "oscuro", lados=lados)
    for t in anillos:
        con.anillo_plano(b + e * largo * t, e, r * 1.5, r * 0.95, 0.14, ranura_anillo, lados=lados)
    boca(con, nombre, b + e * largo, e)


def aletas_radiador(con, y0, y1, z, ancho, n=5, alto=0.25):
    for k in range(n):
        y = y0 + (y1 - y0) * (k + 0.5) / n
        con.caja((0, y, z), (ancho, 0.07, alto), "metal", bisel=False)


# ---- láseres ------------------------------------------------------------------------------------------------

def laser(con, p):
    _color(con, p)
    L = p.get("largo", 2.4)
    estilo = p.get("estilo", "basico")
    montaje(con, 0.5, 0.0, largo=1.6)
    zc = 0.0
    if estilo == "basico":
        con.caja((0, -0.2, zc), (0.8, L, 0.8), "primario")
        aletas_radiador(con, -0.6, 0.6, zc + 0.48, 0.7)
        canon(con, (0, -0.2 - L / 2, zc), 2.0, 0.17, anillos=(0.3,))
        con.cilindro((0.3, 0.6, zc - 0.4), (0, -1, 0), 0.06, 1.6, "goma", lados=6, bisel=False)
        con.caja((0, -0.2 - L / 2 + 0.05, zc), (0.5, 0.1, 0.5), "neon", bisel=False)
    elif estilo == "militar":
        a = [V((-0.42, -L / 2 - 0.4, zc - 0.32)), V((0.42, -L / 2 - 0.4, zc - 0.32)), V((0.42, -L / 2 - 0.4, zc + 0.3)),
             V((-0.42, -L / 2 - 0.4, zc + 0.3))]
        b = [q + V((0, L, 0)) for q in a]
        b = [V((q.x * 1.15, q.y, q.z * 1.2)) for q in b]
        con.loft([a, b], "primario")
        con.caja((0, 0.2, zc - 0.36), (0.7, 1.0, 0.12), "secundario")
        canon(con, (0, -L / 2 - 0.4, zc), 2.2, 0.16, anillos=(0.25, 0.5))
        # mira
        con.cilindro((0, -L / 2 + 0.3, zc + 0.55), (0, -1, 0), 0.14, 0.9, "oscuro", lados=10)
        con.cilindro((0, -L / 2 - 0.62, zc + 0.55), (0, -1, 0), 0.1, 0.03, "neon2", lados=10, bisel=False)
        for s in (-0.25, 0.25):
            con.caja((0, -L / 2 + 0.3 + s, zc + 0.42), (0.1, 0.1, 0.25), "oscuro", bisel=False)
    elif estilo == "doble":
        con.caja((0, -0.1, zc), (1.5, L, 0.85), "primario")
        con.caja((0, -0.1, zc + 0.47), (1.2, L * 0.7, 0.12), "secundario")
        for i, sx in enumerate((-0.45, 0.45)):
            canon(con, (sx, -0.1 - L / 2, zc), 2.3, 0.15, anillos=(0.3,), nombre=f"boca_{i + 1}")
            con.caja((sx, -0.1 - L / 2 + 0.05, zc), (0.42, 0.1, 0.42), "neon", bisel=False)
        aletas_radiador(con, 0.2, 1.0, zc + 0.48, 1.2, n=4)
        con.cilindro((0, -0.3, zc + 0.6), (0, -1, 0), 0.12, 0.8, "oscuro", lados=8)


def laser_pesado(con, p):
    _color(con, p)
    L = p.get("largo", 4.2)
    t4 = con.tier >= 4
    montaje(con, 0.6, 0.0, largo=2.0, frontal=True, ancho=1.3, alto=1.8)
    if t4:
        perf = [(-0.8, -0.5), (0.8, -0.5), (0.95, 0.15), (0.4, 0.75), (-0.4, 0.75), (-0.95, 0.15)]
        a = [V((x, -L / 2, z)) for x, z in perf]
        b = [V((x * 1.1, L / 2, z * 1.1)) for x, z in perf]
        f = [V((x * 0.6, -L / 2 - 0.8, z * 0.6)) for x, z in perf]
        con.loft([f, a, b], "primario")
        con.tira([V((0.62, -L / 2 - 0.5, 0.42)), V((0.75, L / 2, 0.55))], [V((0.6, 0, 0.8))] * 2, 0.12,
                 "secundario", alto=0.05)
        con.tira([V((-0.62, -L / 2 - 0.5, 0.42)), V((-0.75, L / 2, 0.55))], [V((-0.6, 0, 0.8))] * 2, 0.12,
                 "secundario", alto=0.05)
        y_c = -L / 2 - 0.8
        canon(con, (0, y_c, 0.1), 3.0, 0.3, anillos=(0.2, 0.45, 0.7), ranura_anillo="secundario")
        for k, t in enumerate((0.2, 0.45, 0.7)):
            con.toro((0, y_c - 3.0 * t, 0.1), (0, 1, 0), 0.46, 0.05, "neon" if k % 2 == 0 else "neon2", n1=16, n2=4)
        for s in (-1, 1):
            con.prisma([(0, 0), (1.2, 0), (0.9, 0.45)], (s * 0.5, -L / 2 + 0.3, 0.7), (0, 1, 0), (0, 0, 1), (1, 0, 0),
                       0.08, "secundario")
    else:
        con.revolucion((0, -L / 2, 0.1), (0, 1, 0), [(0, 0), (0, 0.45), (0.3, 0.7), (L * 0.8, 0.75), (L, 0.6),
                                                     (L, 0)], "primario", lados=16)
        con.caja((0, 0.4, 0.1 - 0.62), (0.9, L * 0.6, 0.3), "secundario")
        y_c = -L / 2
        canon(con, (0, y_c, 0.1), 2.8, 0.3, anillos=(0.15, 0.35, 0.55, 0.75))
        for t in (0.15, 0.35, 0.55, 0.75):
            con.toro((0, y_c - 2.8 * t, 0.1), (0, 1, 0), 0.46, 0.05, "neon", n1=16, n2=4)
        con.tira([V((0, -L / 2 + 0.3, 0.86)), V((0, L / 2 - 0.3, 0.86))], [V((0, 0, 1))] * 2, 0.1, "neon", alto=0.04)
        aletas_radiador(con, 0.2, L / 2 - 0.2, 0.86, 0.8, n=4, alto=0.18)
    con.cilindro((0, y_c - 0.05, 0.1), (0, -1, 0), 0.18, 0.08, "neon2", lados=12, bisel=False)


def gatling(con, p):
    _color(con, p)
    montaje(con, 1.1, 0.0, largo=1.8, ancho=1.2, alto=1.8)
    con.revolucion((0, 0.4, 0.1), (0, -1, 0), [(0, 0), (0, 0.75), (0.2, 0.85), (1.6, 0.85), (1.8, 0.65), (1.8, 0)],
                   "primario", lados=16)
    con.toro((0, -0.3, 0.1), (0, 1, 0), 0.86, 0.06, "neon", n1=20, n2=4)
    con.caja((0.95, -0.2, 0.1), (0.5, 1.2, 0.9), "secundario")  # tambor de munición
    con.cilindro((0.95, -0.2, 0.1), (1, 0, 0), 0.32, 0.3, "oscuro", lados=10)
    with con.grupo("canones"):
        y0 = -1.4
        for k in range(6):
            a = math.tau * k / 6
            x, z = math.cos(a) * 0.38, 0.1 + math.sin(a) * 0.38
            canon(con, (x, y0, z), 2.6, 0.12, lados=8, freno=False, nombre=f"boca_{k + 1}")
        for t in (0.15, 0.75):
            con.anillo_plano((0, y0 - 2.6 * t, 0.1), (0, 1, 0), 0.62, 0.15, 0.16, "secundario", lados=16)
        con.cilindro((0, y0 + 0.1, 0.1), (0, -1, 0), 0.2, 2.6, "oscuro", lados=8)
    con.info["json_pivote_canones"] = "los cañones (malla _canones) giran alrededor del eje Z de Roblox"


# ---- misiles y torpedos -----------------------------------------------------------------------------------------

def misiles(con, p):
    _color(con, p)
    cols, filas = p["celdas"]
    paso = p.get("paso", 0.62)
    W = cols * paso + 0.3
    H = filas * paso + 0.3
    L = p.get("largo", 2.6)
    zc = 0.0
    montaje(con, 0.0, zc + H / 2 + 0.9 - 0.06, largo=1.6, ancho=1.0, alto=1.7) if p.get("montaje_arriba") else \
        montaje(con, L / 2 - 0.9, 0.0, largo=1.6, ancho=W + 0.04, alto=max(1.7, H * 0.8))
    if con.tier >= 3:
        perfil = [(-W / 2, -H / 2), (W / 2, -H / 2), (W / 2 + 0.1, H / 2 - 0.2), (W / 2 - 0.2, H / 2 + 0.1),
                  (-W / 2 + 0.2, H / 2 + 0.1), (-W / 2 - 0.1, H / 2 - 0.2)]
        con.cuña(perfil, -L / 2, L / 2 - 1.0, "primario")
    else:
        con.caja((0, -0.5, zc), (W, L - 1.0, H), "primario")
    yf = -L / 2 - 0.02
    for i in range(cols):
        for j in range(filas):
            x = (i - (cols - 1) / 2) * paso
            z = zc + (j - (filas - 1) / 2) * paso
            con.tubo((x, yf + 0.1, z), (0, -1, 0), paso * 0.42, paso * 0.32, 0.18, "oscuro", lados=10)
            # punta del misil asomando
            con.revolucion((x, yf + 0.5, z), (0, -1, 0), [(0, paso * 0.3), (0.25, paso * 0.3), (0.5, paso * 0.12),
                                                         (0.58, 0)], p.get("ranura_misil", "aviso"), lados=8,
                           bisel=False)
            boca(con, f"tubo_{i * filas + j + 1}", (x, yf, z))
            if con.tier >= 3:
                con.toro((x, yf - 0.06, z), (0, 1, 0), paso * 0.43, 0.025, "neon", n1=12, n2=3)
    if con.tier == 1:
        for s in (-1, 1):
            con.caja((s * (W / 2 + 0.03), -0.5, zc), (0.06, L - 1.2, H * 0.6), "secundario")
    elif con.tier == 2:
        con.caja((0, -0.5, zc + H / 2 + 0.03), (W * 0.9, L - 1.3, 0.06), "secundario")
        con.caja((0, -L / 2 + 0.05, zc - H / 2 - 0.05), (W, 0.25, 0.1), "aviso", bisel=False)


def torpedo(con, p):
    _color(con, p)
    L = p.get("largo", 6.0)
    R = p.get("R", 0.75)
    montaje(con, 0.8, 0.0, largo=2.2, frontal=True, ancho=1.2, alto=2.0)
    con.revolucion((0, L / 2, 0), (0, -1, 0), [(0, 0), (0, R * 0.8), (0.3, R * 1.05), (L * 0.9, R * 1.05),
                                               (L, R * 1.12)], "primario", lados=18)
    con.tubo((0, -L / 2 + 0.02, 0), (0, -1, 0), R * 1.2, R * 0.82, 0.35, "secundario", lados=18)
    # torpedo asomando
    con.revolucion((0, -L / 2 + 0.6, 0), (0, -1, 0), [(0, R * 0.7), (0.4, R * 0.7), (0.9, R * 0.45), (1.1, 0)],
                   "aviso", lados=14, bisel=False)
    boca(con, "boca", (0, -L / 2 - 0.35, 0))
    for t in (0.3, 0.6):
        con.anillo_plano((0, -L / 2 + L * t, 0), (0, 1, 0), R * 1.2, R * 1.0, 0.2, "secundario", lados=18)
    # aletas traseras
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        d = V((math.cos(a), 0, math.sin(a)))
        con.prisma([(0, 0), (1.2, 0), (1.2, 0.5), (0.5, 0.5)], V((0, L / 2 - 1.3, 0)) + d * R, (0, 1, 0), d,
                   d.cross(V((0, 1, 0))), 0.08, "secundario")
    if con.tier >= 4:
        # sistema de guía: lente + anillos de neón
        con.cilindro((0, -L / 2 + 1.2, R * 1.05), (0, 0, 1), 0.4, 0.3, "oscuro", lados=12)
        con.esfera((0, -L / 2 + 1.2, R * 1.4), 0.3, "neon2", lados=12, anillos=6)
        for t in (0.15, 0.45, 0.75):
            con.toro((0, -L / 2 + L * t, 0), (0, 1, 0), R * 1.08, 0.05, "neon", n1=24, n2=4)
        con.tira([V((0, -L / 2 + 0.4, R * 1.06)), V((0, L / 2 - 0.4, R * 1.06))], [V((0, 0, 1))] * 2, 0.16,
                 "secundario", alto=0.04)
    else:
        con.toro((0, -L / 2 + L * 0.15, 0), (0, 1, 0), R * 1.08, 0.05, "neon", n1=24, n2=4)
        con.rejilla((0, L / 2 - 1.8, R * 1.0), (0, 0, 1), (0, 1, 0), 1.2, 0.6, "oscuro", "metal", lamas=4)


def balistico(con, p):
    _color(con, p)
    L = p.get("largo", 6.0)
    r = p.get("r", 0.24)
    t4 = con.tier >= 4
    montaje(con, 1.2, 0.0, largo=2.2, frontal=True, ancho=1.4 if t4 else 1.1, alto=2.0 if t4 else 1.7)
    # recámara
    if t4:
        con.cuña([(-0.9, -0.7), (0.9, -0.7), (1.05, 0.3), (0.55, 0.9), (-0.55, 0.9), (-1.05, 0.3)], -0.8, 2.2,
                 "primario")
        con.tira([V((0.9, -0.8, 0.45)), V((0.9, 2.2, 0.45))], [V((1, 0, 0.3))] * 2, 0.14, "secundario", alto=0.05)
        con.tira([V((-0.9, -0.8, 0.45)), V((-0.9, 2.2, 0.45))], [V((-1, 0, 0.3))] * 2, 0.14, "secundario", alto=0.05)
    else:
        con.caja((0, 0.6, 0), (1.2, 2.8, 1.2), "primario")
        con.caja((0, 0.6, 0.66), (0.9, 2.0, 0.14), "secundario")
    # cañón (malla aparte en el élite: retrocede)
    grupo = "canon" if t4 else "cuerpo"
    with con.grupo(grupo):
        canon(con, (0, -0.8, 0.1), L, r, lados=14, anillos=(0.05, 0.4) if not t4 else (0.05, 0.3, 0.55),
              ranura_anillo="secundario")
        con.revolucion((0, -0.8, 0.1), (0, -1, 0), [(0, r * 2.4), (0.6, r * 2.2), (1.2, r * 1.4)], "oscuro", lados=14)
    # cilindros de retroceso
    for s in (-1, 1):
        con.cilindro((s * 0.42, -0.6, -0.32), (0, -1, 0), 0.13, 1.8, "metal", lados=8)
        con.cilindro((s * 0.42, -2.3, -0.32), (0, -1, 0), 0.09, 0.6, "oscuro", lados=8)
    if t4:
        con.toro((0, -0.8 - L * 0.98, 0.1), (0, 1, 0), r * 1.6, 0.05, "neon", n1=16, n2=4)
        con.caja((0, 1.0, -0.75), (0.6, 1.2, 0.1), "neon2", bisel=False)
        con.info["json_retroceso"] = {"malla": "_canon", "distancia": 0.8, "eje": "+Z de Roblox (hacia atrás)"}
    else:
        con.caja((0.62, 0.9, 0), (0.06, 1.2, 0.5), "aviso", bisel=False)


def torreta(con, p):
    _color(con, p)
    n = p.get("canones", 2)
    t4 = con.tier >= 4
    # base fija con la brida abajo
    con.acople("acople_base", (0, 0, 0), (0, 0, -1), "CASCO_SUPERIOR", "entrada", acepta=["CASCO_SUPERIOR"])
    con.revolucion((0, 0, 0.14), (0, 0, 1), [(0, 0), (0, 1.35), (0.35, 1.25), (0.5, 1.0), (0.5, 0)], "secundario",
                   lados=20)
    con.toro((0, 0, 0.56), (0, 0, 1), 1.0, 0.05, "neon", n1=24, n2=4)
    with con.grupo("cabeza"):
        zc = 1.25
        if t4:
            perf = [(-1.1, -0.55), (1.1, -0.55), (1.2, 0.15), (0.7, 0.6), (-0.7, 0.6), (-1.2, 0.15)]
            con.cuña([(x, zc + z) for x, z in perf], -1.0, 1.3, "primario")
            for s in (-1, 1):
                con.tira([V((s * 1.15, -0.95, zc + 0.15)), V((s * 1.15, 1.25, zc + 0.15))], [V((s, 0, 0))] * 2, 0.1,
                         "secundario", alto=0.05)
        else:
            con.revolucion((0, 0, 0.6), (0, 0, 1), [(0, 0), (0, 1.1), (0.75, 1.05), (1.1, 0.7), (1.2, 0)],
                           "primario", lados=18)
        con.cilindro((0, 0, zc), (0, 0, 1), 0.12, 0.6, "oscuro", lados=6)
        # sensor
        con.caja((0, 0.4, zc + 0.75), (0.5, 0.5, 0.3), "oscuro")
        con.cilindro((0, 0.14, zc + 0.75), (0, -1, 0), 0.12, 0.05, "neon2", lados=10, bisel=False)
        sep = 0.36
        xs = [(-0.5 * sep * (n - 1) + k * sep) for k in range(n)] if n <= 2 else \
            [(-0.55, -0.12), (-0.55, 0.22), (0.55, -0.12), (0.55, 0.22)]
        for k, x in enumerate(xs):
            if isinstance(x, tuple):
                bx, bz = x
            else:
                bx, bz = x * 2.2, 0.0
            canon(con, (bx, -0.9, zc + bz), 2.6 if n <= 2 else 2.2, 0.13, lados=10, nombre=f"boca_{k + 1}",
                  anillos=(0.4,), ranura_anillo="secundario" if t4 else "oscuro")
        if t4:
            con.caja((0, -0.95, zc), (1.6, 0.12, 0.8), "secundario")
    con.info["json_pivote_cabeza"] = "la malla _cabeza gira alrededor del eje Y de Roblox (vertical)"


def railgun(con, p):
    _color(con, p)
    L = p.get("largo", 9.0)
    t5 = con.tier >= 5
    montaje(con, 1.6, 0.0, largo=2.4, frontal=True, ancho=1.5, alto=2.0)
    con.cuña([(-0.8, -0.6), (0.8, -0.6), (0.9, 0.5), (0.5, 0.85), (-0.5, 0.85), (-0.9, 0.5)], 0.0, 3.0, "primario")
    y0 = 0.0
    sep = 0.42 if not t5 else 0.55
    for s in (-1, 1):
        con.caja((s * sep, y0 - L / 2, 0.1), (0.22, L, 0.75 if not t5 else 0.95), "secundario" if not t5 else "metal")
        con.caja((s * (sep - 0.13), y0 - L / 2, 0.1), (0.05, L * 0.96, 0.4), "metal", bisel=False)
    n = 7 if not t5 else 9
    for k in range(n):
        y = y0 - L * (k + 0.5) / n
        r = 0.85 if not t5 else 1.05
        con.anillo_plano((0, y, 0.1), (0, 1, 0), r, r - 0.14, 0.18, "oscuro", lados=6 if not t5 else 8, giro=math.pi / 6)
        con.toro((0, y, 0.1), (0, 1, 0), r - 0.07, 0.045, "neon", n1=18, n2=4)
    boca(con, "boca", (0, y0 - L, 0.1))
    if t5:
        # carga visible: núcleo de cristal y bobinas
        con.esfera((0, 1.4, 1.2), 0.75, "cristal", lados=14, anillos=8, escala=(1, 1.6, 1))
        con.esfera((0, 1.4, 1.2), 0.42, "neon2", lados=12, anillos=6, escala=(1, 1.6, 1))
        for k in range(3):
            con.toro((0, 0.6 + k * 0.8, 1.2), (0, 1, 0), 0.8, 0.07, "secundario", n1=18, n2=5)
        pts = [V((0, y0 - L * u, 0.1)) for u in (0.0, 0.3, 0.6, 0.95)]
        con.tira(pts, [V((0, 0, 1))] * 4, 0.12, "neon2", alto=0.03)
    con.info["json_carga"] = "acople visual: el brillo de los anillos (neón) sube mientras carga"


def plasma(con, p):
    _color(con, p)
    montaje(con, 1.2, 0.0, largo=2.0, frontal=True, ancho=1.4, alto=2.0)
    yc = -0.6
    con.esfera((0, yc, 0.2), 1.05, "neon", lados=18, anillos=10)
    # jaula
    for k in range(6):
        a = math.tau * k / 6
        pts = []
        for i in range(7):
            ang = -math.pi / 2 + math.pi * i / 6
            rr = 1.25 * math.cos(ang) + 0.04
            pts.append(V((math.cos(a) * rr, yc + math.sin(ang) * 1.25, 0.2 + math.sin(a) * rr)))
        for q0, q1 in zip(pts[:-1], pts[1:]):
            con.cilindro(q0, q1 - q0, 0.09, (q1 - q0).length + 0.03, "secundario", lados=6, tapas=False, bisel=False)
    con.toro((0, yc, 0.2), (0, 1, 0), 1.28, 0.1, "primario", n1=24, n2=6)
    con.revolucion((0, 0.5, 0.2), (0, 1, 0), [(0, 0), (0, 0.9), (1.5, 0.8), (1.5, 0)], "primario", lados=16)
    con.revolucion((0, yc - 1.1, 0.2), (0, -1, 0), [(0, 0.5), (0.4, 0.7), (1.1, 0.95), (1.1, 0.82), (0.45, 0.55),
                                                    (0.4, 0)], "primario", lados=16)
    con.toro((0, yc - 2.15, 0.2), (0, 1, 0), 0.9, 0.06, "secundario", n1=20, n2=5)
    boca(con, "boca", (0, yc - 2.2, 0.2))


def alien(con, p):
    _color(con, p)
    montaje(con, 1.4, 0.0, largo=2.0, ancho=1.2, alto=1.8)
    # cuerpo de hueso (loft curvo)
    anillos = []
    for k in range(9):
        u = k / 8
        y = 2.2 - 5.0 * u
        r = 0.55 + 0.35 * math.sin(u * math.pi) - 0.2 * u
        anillos.append([V((math.cos(a) * r * 1.1, y, 0.2 + math.sin(a) * r + 0.25 * math.sin(u * 3))) for a in
                        (math.tau * i / 12 for i in range(12))])
    caras = con.loft(anillos, "organico")
    con.desplazar(caras, lambda v: v + V((0.06 * math.sin(v.y * 4), 0, 0.05 * math.sin(v.y * 3 + v.x * 5))))
    # púas de hueso y cristal
    for k in range(5):
        y = 1.6 - k * 0.9
        a = 0.6 if k % 2 else -0.6
        d = V((math.sin(a), 0.2, math.cos(a)))
        con.cilindro((0, y, 0.6), d, 0.14, 0.9, "secundario", lados=6, radio2=0.0)
    # emisor de cristal
    for k in range(5):
        a = math.tau * k / 5
        d = V((math.cos(a) * 0.5, -1, math.sin(a) * 0.5)).normalized()
        con.cilindro(V((0, -2.6, 0.2 + 0.2)) + V((math.cos(a), 0, math.sin(a))) * 0.35, d, 0.16, 1.3, "cristal",
                     lados=6, radio2=0.0)
    con.esfera((0, -2.7, 0.4), 0.36, "neon", lados=10, anillos=6)
    con.tira([V((0, 2.0, 0.95)), V((0, 0.0, 1.05)), V((0, -2.3, 0.75))], [V((0, 0, 1))] * 3, 0.07, "neon", alto=0.03)
    boca(con, "boca", (0, -3.3, 0.4))


def desintegrador(con, p):
    _color(con, p)
    montaje(con, 1.6, 0.0, largo=2.2, frontal=True, ancho=1.4, alto=2.0)
    con.revolucion((0, 2.4, 0.2), (0, -1, 0), [(0, 0), (0, 0.8), (0.5, 1.0), (2.6, 0.95), (3.2, 0.6), (3.2, 0)],
                   "primario", lados=16)
    for k in range(3):
        con.toro((0, 1.6 - k * 0.7, 0.2), (0, 1, 0), 1.0, 0.06, "neon", n1=20, n2=4)
    # tres púas que sujetan el anillo
    yc = -2.2
    for k in range(3):
        a = math.tau * k / 3 + math.pi / 2
        d = V((math.cos(a), 0, math.sin(a)))
        p0 = V((0, -0.6, 0.2)) + d * 0.7
        p1 = V((0, yc, 0.2)) + d * 1.5
        con.cilindro(p0, p1 - p0, 0.16, (p1 - p0).length, "secundario", lados=6, radio2=0.08)
    con.anillo_plano((0, yc, 0.2), (0, 1, 0), 1.7, 1.35, 0.3, "secundario", lados=28)
    con.toro((0, yc, 0.2), (0, 1, 0), 1.33, 0.07, "neon", n1=28, n2=5)
    # el "agujero": esfera negra con borde blanco
    con.esfera((0, yc, 0.2), 0.62, "oscuro", lados=16, anillos=8)
    con.toro((0, yc, 0.2), (0, 1, 0.3), 0.75, 0.05, "neon2", n1=24, n2=4)
    boca(con, "boca", (0, yc - 0.3, 0.2))
