"""
Motores. La entrada está delante (y = 0, normal -Y): se acoplan por la cara de delante a CASCO_TRASERO o ALA_MOTOR
(los pequeños con brida UNIVERSAL). El cuerpo se extiende hacia +Y (atrás) y la tobera acaba en el acople
MOTOR_ESCAPE (salida solo visual, sin brida: ahí nacen la estela y la llama).

Parámetros (dict `p`):
  tipo (conector de entrada), acepta, R (radio del cuerpo), largo, perfil [(t, r)] en fracción de largo/R,
  tobera {"garganta", "salida", "largo", "ranura"}, nucleo ("neon" / "neon2"), extras: "aletas", "anillos",
  "anillos_neon", "rejilla", "tuberias", "carenado", "petalos", "llama", "oro"
"""

import math

from .geo import V, Matrix


def _cuerpo(con, p, y0=0.14):
    R, L = p["R"], p["largo"]
    perfil = [(y0 + t * L, r * R) for t, r in p.get("perfil", [(0, 0.8), (0.08, 1.0), (0.75, 1.0), (1.0, 0.82)])]
    perfil = [(perfil[0][0], 0)] + perfil
    caras = con.revolucion((0, 0, 0), (0, 1, 0), perfil, p.get("ranura", "primario"), lados=p.get("lados", 18))
    return y0 + L, perfil[-1][1]


def _tobera(con, y, r_base, t, lados=18, escape="acople_escape", x=0.0, z=0.0, eje=(0, 1, 0)):
    """Tobera en campana hueca desde `y` a lo largo de `eje` (por defecto hacia atrás). Devuelve la salida."""
    e = V(eje)
    g, s, l = t["garganta"], t["salida"], t["largo"]
    perfil = [(0, r_base * 0.95), (l * 0.15, g * 1.05), (l * 0.45, (g + s) / 2 * 0.95), (l, s),
              (l, s - 0.07), (l * 0.45, (g + s) / 2 * 0.95 - 0.07), (l * 0.18, g * 0.92), (l * 0.12, 0)]
    o = V((x, y, z))
    con.revolucion(o, e, perfil, t.get("ranura", "tobera"), lados=lados)
    # núcleo que brilla al fondo de la garganta
    con.revolucion(o + e * l * 0.1, e, [(0, g * 0.85), (0.08, g * 0.85), (0.12, 0)],
                   t.get("nucleo", "neon"), lados=lados, bisel=False)
    if t.get("anillo_salida"):
        con.toro(o + e * (l - 0.02), e, s + 0.02, 0.05, t["anillo_salida"], n1=lados + 6, n2=5)
    con.acople(escape, o + e * l, e, "MOTOR_ESCAPE", "salida", brida=False)
    return o + e * l


def motor(con, p):
    for k, v in p.get("color", {}).items():
        con.colores_extra[k] = v
    if "paleta" in p:
        con.info["paleta"] = p["paleta"]
    R, L = p["R"], p["largo"]
    extras = set(p.get("extras", ()))
    tipo = p.get("tipo", "CASCO_TRASERO")
    con.acople("acople_montaje", (0, 0, 0), (0, -1, 0), tipo, "entrada", acepta=p.get("acepta", [tipo]))
    # cuello entre la brida y el cuerpo (si la brida es más pequeña que el motor, un cono de adaptación)
    yb, rb = _cuerpo(con, p)
    if "doble" in p:
        # dos toberas a los lados (plasma élite)
        sep = p["doble"]
        for i, sx in enumerate((-sep, sep)):
            con.revolucion((sx, yb - 0.3, 0), (0, 1, 0), [(0, 0), (0, R * 0.55), (0.6, R * 0.6), (0.9, R * 0.5)],
                           "secundario", lados=14)
            _tobera(con, yb + 0.5, R * 0.5, p["tobera"], lados=16, escape=f"acople_escape_{i + 1}", x=sx)
    else:
        _tobera(con, yb - 0.05, rb, p["tobera"], lados=p.get("lados", 18))

    if "aletas" in extras:
        # aletas de radiador
        n = p.get("n_aletas", 6)
        for k in range(n):
            a = math.tau * (k + 0.5) / n
            d = V((math.cos(a), 0, math.sin(a)))
            c = V((0, 0.14 + L * 0.45, 0)) + d * (R + 0.12)
            con.caja(c, (0.08, L * 0.5, 0.3), "oscuro", giro=Matrix.Rotation(-a, 3, "Y"))
    if "anillos" in extras:
        for t in p.get("t_anillos", (0.3, 0.6)):
            con.anillo_plano((0, 0.14 + L * t, 0), (0, 1, 0), R + 0.1, R - 0.05, 0.22, "secundario", lados=20)
    if "anillos_neon" in extras:
        for k, t in enumerate(p.get("t_anillos", (0.3, 0.55, 0.8))):
            y = 0.14 + L * t
            con.anillo_plano((0, y, 0), (0, 1, 0), R + 0.22, R - 0.05, 0.3, "oscuro", lados=22)
            con.toro((0, y, 0), (0, 1, 0), R + 0.24, 0.07, "neon" if k % 2 == 0 else "neon2", n1=26, n2=5)
    if "rejilla" in extras:
        # rejilla iónica en la salida: barras cruzadas
        t = p["tobera"]
        y = yb - 0.05 + t["largo"] * 0.75
        r = (t["garganta"] + t["salida"]) / 2
        for k in range(-2, 3):
            con.caja((k * r * 0.33, y, 0), (0.05, 0.05, r * 1.7), "metal", bisel=False)
            con.caja((0, y, k * r * 0.33), (r * 1.7, 0.05, 0.05), "metal", bisel=False)
    if "tuberias" in extras:
        for s in (-1, 1):
            pts = [V((s * R * 0.7, 0.3, R * 0.75)), V((s * R * 0.75, L * 0.5, R * 0.85)),
                   V((s * R * 0.6, L * 0.9, R * 0.75))]
            for a, b in zip(pts[:-1], pts[1:]):
                con.cilindro(a, b - a, 0.08, (b - a).length, "metal", lados=6, tapas=False, bisel=False)
    if "carenado" in extras:
        # carenado anguloso superior (élite)
        con.cuña([(-R * 0.8, R * 0.6), (R * 0.8, R * 0.6), (R * 0.35, R * 1.25), (-R * 0.35, R * 1.25)],
                 0.3, L * 0.85, "secundario")
    if "oro" in extras:
        for t in (0.15, 0.85):
            con.toro((0, 0.14 + L * t, 0), (0, 1, 0), R * 1.0 + 0.03, 0.06, "secundario", n1=24, n2=5)
    if "petalos" in extras:
        t = p["tobera"]
        y = yb - 0.05 + t["largo"] * 0.4
        n = 12
        for k in range(n):
            a = math.tau * k / n
            d = V((math.cos(a), 0, math.sin(a)))
            c = V((0, y + t["largo"] * 0.35, 0)) + d * (t["salida"] * 0.92 + 0.04)
            caras = con.caja(c, (t["salida"] * 0.42, t["largo"] * 0.7, 0.06), "tobera",
                             giro=Matrix.Rotation(-a + math.pi / 2, 3, "Y"))
    if "llama" in extras:
        t = p["tobera"]
        y = yb - 0.05 + t["largo"]
        s = t["salida"]
        con.revolucion((0, y - 0.1, 0), (0, 1, 0), [(0, s * 0.85), (L * 0.25, s * 0.7), (L * 0.6, s * 0.35),
                                                    (L * 0.95, 0)], "llama", lados=16, bisel=False)
        con.revolucion((0, y - 0.05, 0), (0, 1, 0), [(0, s * 0.5), (L * 0.3, s * 0.32), (L * 0.55, 0)], "neon2",
                       lados=12, bisel=False)
    if "luces" in extras:
        for s in (-1, 1):
            con.caja((s * R * 0.72, 0.14 + L * 0.5, R * 0.72), (0.12, L * 0.35, 0.06), "neon", bisel=False,
                     giro=Matrix.Rotation(s * -math.pi / 4, 3, "Y"))


# --------------------------------------------------------------------------------------------------------------
# Motores especiales
# --------------------------------------------------------------------------------------------------------------

def fusion_legendario(con, p):
    """Núcleo de fusión visible: una estrella atrapada en una jaula de costillas, tras un casco de cristal."""
    con.colores_extra.update(p.get("color", {}))
    R, L = p["R"], p["largo"]
    con.acople("acople_montaje", (0, 0, 0), (0, -1, 0), "CASCO_TRASERO", "entrada", acepta=["CASCO_TRASERO"])
    con.revolucion((0, 0, 0), (0, 1, 0), [(0.14, 0), (0.14, R * 0.9), (0.6, R), (1.1, R * 0.9), (1.1, 0)],
                   "primario", lados=20)
    yc = 1.1 + L * 0.3
    # núcleo + capa de plasma + cristal
    con.esfera((0, yc, 0), R * 0.42, "neon2", lados=16, anillos=8)
    con.esfera((0, yc, 0), R * 0.62, "neon", lados=16, anillos=8, escala=(1, 1.15, 1))
    con.esfera((0, yc, 0), R * 0.86, "cristal", lados=20, anillos=10, escala=(1, 1.3, 1))
    # jaula de costillas curvas
    n = 6
    for k in range(n):
        a = math.tau * k / n
        pts = []
        for i in range(9):
            u = i / 8
            ang = -math.pi / 2 + math.pi * u
            rr = R * 0.98 * math.cos(ang) + 0.05
            pts.append(V((math.cos(a) * rr, yc + math.sin(ang) * R * 1.25, math.sin(a) * rr)))
        for q0, q1 in zip(pts[:-1], pts[1:]):
            con.cilindro(q0, q1 - q0, 0.1, (q1 - q0).length + 0.04, "secundario", lados=6, tapas=False, bisel=False)
    con.toro((0, yc, 0), (0, 1, 0), R * 1.0, 0.1, "secundario", n1=24, n2=6)
    yt = yc + R * 1.1
    con.revolucion((0, yt, 0), (0, 1, 0), [(0, 0), (0, R * 0.7), (0.5, R * 0.85), (1.0, R * 0.75)], "primario",
                   lados=20)
    _tobera(con, yt + 0.95, R * 0.75, {"garganta": R * 0.45, "salida": R * 0.95, "largo": L * 0.35,
                                         "nucleo": "neon2"}, lados=20)


def warp(con, p):
    """Motor de curvatura: cuerpo largo y anillos concéntricos (malla aparte `_anillos`, para hacerlos girar)."""
    con.colores_extra.update(p.get("color", {}))
    R, L = p["R"], p["largo"]
    con.acople("acople_montaje", (0, 0, 0), (0, -1, 0), "CASCO_TRASERO", "entrada", acepta=["CASCO_TRASERO"])
    con.revolucion((0, 0, 0), (0, 1, 0), [(0.14, 0), (0.14, R * 0.85), (0.5, R), (L * 0.55, R * 0.8),
                                          (L * 0.95, R * 0.45), (L, 0)], "primario", lados=20)
    # espina de neón
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        pts = [V((math.cos(a) * R * (1.0 - 0.5 * u * u), 0.5 + (L * 0.9 - 0.5) * u, math.sin(a) * R *
                  (1.0 - 0.5 * u * u))) for u in (i / 6 for i in range(7))]
        nrm = [V((math.cos(a), 0, math.sin(a)))] * 7
        con.tira(pts, nrm, 0.08, "neon", alto=0.04)
    yc = L * 0.62
    with con.grupo("anillos"):
        for k, (rr, inc) in enumerate(((R * 1.35, 0.0), (R * 1.75, 0.25), (R * 2.15, -0.2))):
            eje = V((0, math.cos(inc), math.sin(inc)))
            con.anillo_plano((0, yc, 0), eje, rr + 0.12, rr - 0.12, 0.18, "secundario", lados=32)
            con.toro((0, yc, 0), eje, rr, 0.05, "neon", n1=32, n2=4)
    for a in (0, math.pi * 2 / 3, math.pi * 4 / 3):
        d = V((math.cos(a), 0, math.sin(a)))
        con.cilindro(V((0, yc, 0)) + d * R * 0.7, d, 0.09, R * 0.6, "metal", lados=6)
    con.acople("acople_escape", (0, L, 0), (0, 1, 0), "MOTOR_ESCAPE", "salida", brida=False)
    con.info["json_pivote_anillos"] = "centro de la malla _anillos; giran alrededor del eje Z de Roblox (largo)"


def gravitacional(con, p):
    """Motor alienígena sin tobera: una esfera de gravedad sujeta por garras, con anillos que la orbitan."""
    con.colores_extra.update(p.get("color", {}))
    R = p["R"]
    con.acople("acople_montaje", (0, 0, 0), (0, -1, 0), "CASCO_TRASERO", "entrada", acepta=["CASCO_TRASERO"])
    con.revolucion((0, 0, 0), (0, 1, 0), [(0.14, 0), (0.14, 1.25), (0.7, 1.15), (1.2, 0.7), (1.4, 0)], "organico",
                   lados=20)
    yc = 1.4 + R
    con.esfera((0, yc, 0), R * 0.45, "neon2", lados=16, anillos=8)
    con.esfera((0, yc, 0), R * 0.8, "cristal", lados=20, anillos=10)
    for k in range(4):
        a = math.tau * k / 4 + math.pi / 4
        pts = []
        for i in range(7):
            u = i / 6
            ang = -math.pi * 0.85 + math.pi * 1.2 * u
            pts.append(V((math.cos(a) * (R * 0.95) * math.cos(ang * 0.5 + 0.2), yc + math.sin(ang) * R * 0.95,
                          math.sin(a) * (R * 0.95) * math.cos(ang * 0.5 + 0.2))))
        pts[0] = V((math.cos(a) * 0.8, 1.1, math.sin(a) * 0.8))
        for i, (q0, q1) in enumerate(zip(pts[:-1], pts[1:])):
            r = 0.16 * (1 - i / 7) + 0.04
            con.cilindro(q0, q1 - q0, r, (q1 - q0).length + 0.04, "secundario", lados=7, radio2=r * 0.8,
                         tapas=False, bisel=False)
        con.tira(pts, [V((math.cos(a), 0, math.sin(a)))] * len(pts), 0.05, "neon", alto=0.03)
    with con.grupo("orbita"):
        for inc in (0.5, -0.5):
            eje = V((math.sin(inc), 0.3, math.cos(inc)))
            con.toro((0, yc, 0), eje, R * 1.25, 0.06, "neon", n1=32, n2=5)
    con.acople("acople_escape", (0, yc + R * 0.8, 0), (0, 1, 0), "MOTOR_ESCAPE", "salida", brida=False)


def retro(con, p):
    """Retrocohete de frenado: se cuelga por arriba y su tobera mira hacia delante."""
    con.colores_extra.update(p.get("color", {}))
    R, L = p["R"], p["largo"]
    con.acople("acople_montaje", (0, 0, R + 0.25), (0, 0, 1), "ALA_PUNTA", "entrada",
               acepta=["ALA_PUNTA", "CASCO_INFERIOR", "UNIVERSAL"], en_superficie=True)
    con.caja((0, 0, R + 0.1), (0.8, 1.4, 0.35), "secundario")
    con.revolucion((0, L / 2, 0), (0, -1, 0), [(0, 0), (0, R * 0.8), (0.2, R), (L * 0.75, R), (L, R * 0.8)],
                   "primario", lados=16)
    _tobera(con, -L / 2 + 0.05, R * 0.8, {"garganta": R * 0.45, "salida": R * 0.85, "largo": 0.9,
                                          "ranura": "secundario"}, lados=16, eje=(0, -1, 0))
    for k in range(3):
        con.caja((0, -L / 2 + 0.4 + k * 0.5, -R - 0.02), (0.5, 0.12, 0.12), "aviso", bisel=False)


def vtol(con, p):
    """Motor de despegue vertical: soporte fijo y una tobera orientable (malla aparte `_tobera`)."""
    con.colores_extra.update(p.get("color", {}))
    R = p["R"]
    con.acople("acople_montaje", (0, 0, 0.6), (0, 0, 1), "ALA_PUNTA", "entrada",
               acepta=["ALA_PUNTA", "CASCO_INFERIOR", "UNIVERSAL"], en_superficie=True)
    # horquilla
    con.caja((0, 0, 0.35), (2 * R + 0.9, 1.2, 0.5), "secundario")
    for s in (-1, 1):
        con.caja((s * (R + 0.3), 0, -0.35), (0.3, 1.0, 1.3), "secundario")
        con.cilindro((s * (R + 0.45), 0, -0.6), (s, 0, 0), 0.3, 0.2, "metal", lados=12)
    with con.grupo("tobera"):
        con.cilindro((-(R + 0.15), 0, -0.6), (1, 0, 0), 0.22, 2 * R + 0.3, "metal", lados=10)
        con.revolucion((0, 0, -0.6 + R * 0.6), (0, 0, -1), [(0, 0), (0, R * 0.7), (0.25, R), (R * 1.2, R),
                                                             (R * 1.4, R * 0.85)], "primario", lados=18)
        perfil = [(0, R * 0.85), (0.15, R * 0.55), (0.6, R * 0.95), (0.6, R * 0.88), (0.18, R * 0.5), (0.12, 0)]
        y0 = -0.6 - R * 0.8
        con.revolucion((0, 0, y0), (0, 0, -1), perfil, "tobera", lados=18)
        con.revolucion((0, 0, y0 - 0.1), (0, 0, -1), [(0, R * 0.45), (0.04, R * 0.45), (0.06, 0)], "neon", lados=18,
                       bisel=False)
        con.toro((0, 0, y0 - 0.58), (0, 0, 1), R * 0.92, 0.05, "neon", n1=24, n2=4)
    con.acople("acople_escape", (0, 0, y0 - 0.6), (0, 0, -1), "MOTOR_ESCAPE", "salida", brida=False, malla="tobera")
    con.info["json_pivote_tobera"] = {"eje": "X de Roblox", "nota": "la malla _tobera gira alrededor de su eje "
                                      "transversal (el del soporte); de -30° a +90° para pasar de vertical a empuje"}
