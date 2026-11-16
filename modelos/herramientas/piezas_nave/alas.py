"""
Alas. Se modela el ala IZQUIERDA (+X); la derecha sale reflejada (variantes _izq y _der en el mismo FBX).

La raíz está en x = 0: una brida CASCO_LATERAL (entrada) con un carenado que pasa del cuadrado de la brida al
perfil del ala. Salidas: ALA_PUNTA bajo la punta y en los hardpoints (normal hacia abajo) y ALA_MOTOR en el borde
de salida (normal hacia atrás, con una góndola corta).

Parámetros (dict `p`):
  envergadura, cuerda_raiz, cuerda_punta, flecha (retraso del borde de ataque en la punta), diedro (z en la punta),
  grosor_raiz, grosor_punta, perfil ("redondo", "rombo", "plano"), secciones (n), curva (z extra ∝ x²),
  quiebros [(fracción, cuerda, flecha)] para alas con quiebro (cranked), hardpoints [fracción], motores [fracción],
  punta (True), extras: "flaps", "neon_borde", "neon_salida", "oro", "winglet", "aleta_punta", "luces"
"""

import math

from .geo import V, Matrix

Y_RAIZ = -0.2  # borde de ataque en la raíz (la brida queda centrada en la cuerda)


def _plano(p):
    """Devuelve una función x -> (y_ba, cuerda, grosor, z) a lo largo de la envergadura."""
    s = p["envergadura"]
    c0, c1 = p["cuerda_raiz"], p["cuerda_punta"]
    quiebros = p.get("quiebros")

    def f(x):
        u = max(0.0, min(1.0, x / s))
        if quiebros:
            pts = [(0.0, c0, 0.0)] + list(quiebros) + [(1.0, c1, p["flecha"])]
            for a, b in zip(pts[:-1], pts[1:]):
                if a[0] <= u <= b[0]:
                    k = (u - a[0]) / max(b[0] - a[0], 1e-6)
                    cuerda = a[1] + (b[1] - a[1]) * k
                    ba = a[2] + (b[2] - a[2]) * k
                    break
        else:
            cuerda = c0 + (c1 - c0) * u
            ba = p["flecha"] * u
        y = -c0 / 2 + ba
        g = p["grosor_raiz"] + (p["grosor_punta"] - p["grosor_raiz"]) * u
        z = p.get("diedro", 0.0) * u + p.get("curva", 0.0) * u * u
        return y, cuerda, g, z

    return f


def construir(con, p):
    s = p["envergadura"]
    f = _plano(p)
    extras = set(p.get("extras", ()))
    n_sec = p.get("secciones", 6)
    x0 = 0.95  # donde empieza el ala de verdad (antes, el carenado)
    perfil = p.get("perfil", "redondo")
    xs = [x0 + (s - x0) * k / n_sec for k in range(n_sec + 1)]
    secs = []
    for x in xs:
        y, c, g, z = f(x)
        secs.append((x, y, c, g, z))
    con.ala(secs, p.get("ranura", "primario"), perfil=perfil, n=p.get("puntos_perfil", 10))

    # carenado de raíz: del cuadrado de la brida (1,6) al perfil
    y0, c0, g0, z0 = f(x0)
    tam = 1.6
    a = [V((0.14, -tam * 0.62, -tam / 2)), V((0.14, tam * 0.62, -tam / 2)), V((0.14, tam * 0.62, tam / 2)),
         V((0.14, -tam * 0.62, tam / 2))]
    b = [V((x0 + 0.05, y0 + c0 * 0.12, z0 - g0 * 0.45)), V((x0 + 0.05, y0 + c0 * 0.8, z0 - g0 * 0.35)),
         V((x0 + 0.05, y0 + c0 * 0.8, z0 + g0 * 0.35)), V((x0 + 0.05, y0 + c0 * 0.12, z0 + g0 * 0.45))]
    con.loft([a, b], "secundario" if con.tier != 5 else "oscuro")
    con.acople("acople_raiz", (0, 0, 0), (-1, 0, 0), "CASCO_LATERAL", "entrada", acepta=["CASCO_LATERAL"])

    # punta
    if p.get("punta", True):
        x = s * 0.93
        y, c, g, z = f(x)
        yc = y + c * 0.45
        caja = con.caja((x, yc, z - g / 2 - 0.12), (0.7, min(1.2, c * 0.8), 0.4), "oscuro")
        con.acople("acople_punta", (x, yc, z - g / 2 - 0.32), (0, 0, -1), "ALA_PUNTA", "salida", en_superficie=True)
    for i, fr in enumerate(p.get("hardpoints", [])):
        x = s * fr
        y, c, g, z = f(x)
        yc = y + c * 0.42
        con.prisma([(-0.5, 0), (0.6, 0), (0.45, -0.38), (-0.35, -0.38)], (x, yc, z - g * 0.3), (0, 1, 0), (0, 0, 1),
                   (1, 0, 0), 0.5, "oscuro")
        con.acople(f"acople_hardpoint_{i + 1}", (x, yc, z - g * 0.3 - 0.38), (0, 0, -1), "ALA_PUNTA",
                   "salida", en_superficie=True)
    for i, fr in enumerate(p.get("motores", [])):
        x = s * fr
        y, c, g, z = f(x)
        y_te = y + c
        r = 0.85
        largo = c * 0.7 + 0.4
        yb = y_te - c * 0.7
        perfil_g = [(0, 0), (0.0, r * 0.5), (0.35, r * 0.95), (largo, r), (largo, 0)]
        con.revolucion((x, yb, z - 0.05), (0, 1, 0), perfil_g, "secundario", lados=14)
        nombre = "acople_motor" if len(p.get("motores", [])) == 1 else f"acople_motor_{i + 1}"
        con.acople(nombre, (x, yb + largo + 0.14, z - 0.05), (0, 1, 0), "ALA_MOTOR", "salida")

    # ---- detalles ---------------------------------------------------------------------------------------------
    if "flaps" in extras:
        for k in range(p.get("n_flaps", 2)):
            u0 = 0.2 + 0.7 * k / p.get("n_flaps", 2)
            u1 = u0 + 0.7 / p.get("n_flaps", 2) - 0.04
            pts = []
            for u in (u0, u1):
                x = x0 + (s - x0) * u
                y, c, g, z = f(x)
                pts.append((x, y + c, z, g, c))
            (xa, ya, za, ga, ca), (xb, yb, zb, gb, cb) = pts
            anillos = []
            for x, y, z, g, c in pts:
                fl = c * 0.22
                anillos.append([V((x, y - fl, z - g * 0.12)), V((x, y + 0.02, z - 0.015)), V((x, y + 0.02, z + 0.015)),
                                V((x, y - fl, z + g * 0.12))])
            con.loft(anillos, "secundario" if con.tier in (1, 3) else "oscuro")
    if "neon_borde" in extras or "oro_borde" in extras:
        pts, nrm = [], []
        for k in range(n_sec * 2 + 1):
            x = x0 + (s - x0) * k / (n_sec * 2)
            y, c, g, z = f(x)
            pts.append(V((x, y - 0.02, z)))
            nrm.append(V((0, -1, 0)))
        con.tira(pts, nrm, p.get("ancho_neon", 0.08), "neon" if "neon_borde" in extras else "secundario",
                 alto=0.06)
    if "neon_salida" in extras:
        pts, nrm = [], []
        for k in range(n_sec + 1):
            x = x0 + (s - x0) * (0.15 + 0.8 * k / n_sec)
            y, c, g, z = f(x)
            pts.append(V((x, y + c * 0.75, z + g * 0.3)))
            nrm.append(V((0, 0, 1)))
        con.tira(pts, nrm, 0.06, p.get("ranura_neon_salida", "neon2"), alto=0.03)
    if "oro" in extras:
        # moldura dorada sobre el extradós, paralela al borde de ataque
        pts, nrm = [], []
        for k in range(n_sec + 1):
            x = x0 + (s - x0) * (0.05 + 0.85 * k / n_sec)
            y, c, g, z = f(x)
            pts.append(V((x, y + c * 0.32, z + g * 0.42)))
            nrm.append(V((0, 0, 1)))
        con.tira(pts, nrm, 0.14, "secundario", alto=0.04)
    if "winglet" in extras or "aleta_punta" in extras:
        y, c, g, z = f(s)
        alto = p.get("alto_winglet", 1.2)
        haciaabajo = "aleta_punta" in extras
        dz = -alto if haciaabajo else alto
        c2 = c * 0.6
        a1 = [V((s, y + c * 0.1, z)), V((s, y + c, z)), V((s + 0.1, y + c, z)), V((s + 0.1, y + c * 0.1, z))]
        a2 = [V((s + alto * 0.25, y + c - c2 * 0.2 + c * 0.1, z + dz)), V((s + alto * 0.25, y + c + c * 0.1, z + dz)),
              V((s + alto * 0.25 + 0.08, y + c + c * 0.1, z + dz)),
              V((s + alto * 0.25 + 0.08, y + c - c2 * 0.2 + c * 0.1, z + dz))]
        con.loft([a1, a2], "secundario")
    if "luces" in extras:
        y, c, g, z = f(s)
        con.esfera((s + 0.02, y + c * 0.25, z), 0.1, "neon2", lados=8, anillos=4)
        con.caja((s * 0.6, f(s * 0.6)[0] + f(s * 0.6)[1] * 0.55, f(s * 0.6)[3] + f(s * 0.6)[2] * 0.42),
                 (0.5, 0.18, 0.04), "neon", bisel=False)


# --------------------------------------------------------------------------------------------------------------
# Alas especiales
# --------------------------------------------------------------------------------------------------------------

def ala_variable(con, p):
    """Ala de geometría variable: guante fijo (cuerpo) + panel en dos posiciones (grupos extendida / plegada)."""
    s = p["envergadura"]
    tam = 1.6
    # guante fijo con el pivote
    con.loft([[V((0.14, -1.1, -0.8)), V((0.14, 1.1, -0.8)), V((0.14, 1.1, 0.8)), V((0.14, -1.1, 0.8))],
              [V((2.0, -0.6, -0.22)), V((2.0, 1.4, -0.18)), V((2.0, 1.4, 0.18)), V((2.0, -0.6, 0.22))]],
             "secundario")
    con.cilindro((1.6, 0.4, -0.35), (0, 0, 1), 0.45, 0.7, "metal", lados=12)
    con.acople("acople_raiz", (0, 0, 0), (-1, 0, 0), "CASCO_LATERAL", "entrada", acepta=["CASCO_LATERAL"])
    pivote = V((1.6, 0.4, 0))
    for grupo, ang in (("extendida", 0.0), ("plegada", math.radians(52))):
        with con.grupo(grupo):
            antes = len(con.acoples)
            q = dict(p)
            q["envergadura"] = s
            f = _plano(q)
            xs = [1.7 + (s - 1.7) * k / 6 for k in range(7)]
            secs = [(x,) + tuple(f(x)) for x in xs]
            caras = con.ala([(x, y, c, g, z) for x, y, c, g, z in secs], "primario", perfil="rombo", n=10)
            pts, nrm = [], []
            for x, y, c, g, z in secs:
                pts.append(V((x, y - 0.02, z)))
                nrm.append(V((0, -1, 0)))
            caras += con.tira(pts, nrm, 0.07, "neon", alto=0.05)
            pts = [V((x, y + c * 0.3, z + g * 0.42)) for x, y, c, g, z in secs]
            caras += con.tira(pts, [V((0, 0, 1))] * len(pts), 0.12, "secundario", alto=0.04)
            x = s * 0.92
            y, c, g, z = f(x)
            caras += con.caja((x, y + c * 0.45, z - g / 2 - 0.12), (0.7, min(1.1, c * 0.8), 0.4), "oscuro")
            con.acople("acople_punta", (x, y + c * 0.45, z - g / 2 - 0.32), (0, 0, -1), "ALA_PUNTA", "salida",
                       malla=grupo, en_superficie=True)
            nuevas = con.acoples[antes:]
            # las bridas creadas por acople() también hay que girarlas: se recogen por grupo
            caras_grupo = [fc for fc in con.bm.faces if fc[con.capa_grupo] == con.grupos.index(grupo)]
            if ang:
                giro = Matrix.Translation(pivote) @ Matrix.Rotation(ang, 4, "Z") @ Matrix.Translation(-pivote)
                con.transformar(caras_grupo, giro)
                for a in nuevas:
                    a["pos"] = giro @ a["pos"]
                    a["normal"] = giro.to_3x3() @ a["normal"]
                    a["arriba"] = giro.to_3x3() @ a["arriba"]
    con.info["json_posiciones"] = {"extendida": 0, "plegada": 52,
                                   "nota": "dos mallas del panel: se muestra una u otra (o se interpola el giro "
                                           "alrededor del pivote)"}
    con.info["json_pivote"] = None


def ala_anular(con, p):
    """Ala en anillo alrededor de un motor: puntal desde la raíz y un anillo de perfil alar con su acople."""
    R = p.get("radio", 2.1)
    cuerda = p.get("cuerda", 2.6)
    cx = p.get("distancia", 3.4)
    centro = V((cx, -0.4, 0))
    # anillo: revolución de un perfil alar (cerrado) alrededor de Y
    perfil = []
    n = 10
    g = 0.32
    for i in range(n):
        t = i / n
        sgn = 1 if t <= 0.5 else -1
        s_ = t * 2 if t <= 0.5 else (1 - t) * 2
        esp = 0.5 * g * (2.97 * math.sqrt(max(s_, 0)) - 1.26 * s_ - 3.52 * s_ * s_ + 2.84 * s_ ** 3 - 1.015 * s_ ** 4)
        perfil.append((s_ * cuerda, R + sgn * max(esp, 0.004)))
    perfil.append(perfil[0])
    con.revolucion(centro - V((0, cuerda / 2, 0)), (0, 1, 0), perfil, "primario", lados=28, bisel=False)
    con.toro(centro - V((0, cuerda / 2 - 0.15, 0)), (0, 1, 0), R + 0.02, 0.05, "neon", n1=28, n2=5)
    # puntales
    for dz, ang in ((0.0, 0.0),):
        pass
    a = [V((0.14, -0.9, -0.8)), V((0.14, 0.9, -0.8)), V((0.14, 0.9, 0.8)), V((0.14, -0.9, 0.8))]
    b = [V((cx - R + 0.1, -1.0, -0.14)), V((cx - R + 0.1, 0.5, -0.14)), V((cx - R + 0.1, 0.5, 0.14)),
         V((cx - R + 0.1, -1.0, 0.14))]
    con.loft([a, b], "secundario")
    for ang in (math.radians(120), math.radians(240)):
        d = V((math.cos(ang), 0, math.sin(ang)))
        p0 = centro + d * 0.75
        p1 = centro + d * (R - 0.08)
        caras = con.caja((p0 + p1) / 2, ((p1 - p0).length, 0.9, 0.12), "secundario",
                         giro=Matrix.Rotation(-ang, 3, "Y"))
    # cubo central con la brida de motor mirando atrás
    con.revolucion(centro + V((0, -0.6, 0)), (0, 1, 0), [(0, 0), (0.0, 0.45), (0.5, 0.82), (1.2, 0.82), (1.2, 0)],
                   "oscuro", lados=16)
    caras_puntal = con.caja((centro.x - (R + 0.75) / 2, centro.y, 0), (R - 0.75, 0.9, 0.12), "secundario")
    con.acople("acople_raiz", (0, 0, 0), (-1, 0, 0), "CASCO_LATERAL", "entrada", acepta=["CASCO_LATERAL"])
    con.acople("acople_motor", (centro.x, centro.y + 0.6 + 0.14, 0), (0, 1, 0), "ALA_MOTOR", "salida")
    # punta: bajo el anillo
    con.caja((cx, centro.y, -R - 0.25), (0.6, 1.0, 0.4), "oscuro")
    con.acople("acople_punta", (cx, centro.y, -R - 0.45), (0, 0, -1), "ALA_PUNTA", "salida", en_superficie=True)


def ala_alien(con, p):
    """Ala orgánica: huesos curvos y membranas semitransparentes con venas de neón."""
    s = p["envergadura"]
    # raíz carnosa
    con.loft([[V((0.14, -0.9, -0.8)), V((0.14, 0.9, -0.8)), V((0.14, 0.9, 0.8)), V((0.14, -0.9, 0.8))],
              [V((1.2, -0.5, -0.3)), V((1.2, 0.8, -0.3)), V((1.2, 0.8, 0.3)), V((1.2, -0.5, 0.3))]], "organico")
    con.acople("acople_raiz", (0, 0, 0), (-1, 0, 0), "CASCO_LATERAL", "entrada", acepta=["CASCO_LATERAL"])
    huesos = []
    for k, (ang, largo) in enumerate(((-0.25, 1.0), (0.1, 0.92), (0.45, 0.78), (0.8, 0.6))):
        pts = []
        for i in range(8):
            u = i / 7
            x = 1.0 + (s - 1.0) * largo * u
            y = 0.2 + math.sin(ang) * s * largo * u * 0.9 + 0.5 * math.sin(u * math.pi) * (k - 1.5) * 0.3
            z = 0.25 * math.sin(u * math.pi) + 0.6 * u * u
            pts.append(V((x, y, z)))
        huesos.append(pts)
        for i in range(7):
            a, b = pts[i], pts[i + 1]
            r = 0.2 * (1 - i / 8) + 0.04
            con.cilindro(a, b - a, r, (b - a).length + 0.05, "secundario", lados=8, radio2=r * 0.85, tapas=i in (0, 6),
                         bisel=False)
        con.esfera(pts[-1], 0.12, "secundario", lados=8, anillos=4, escala=(1, 1, 1))
        # vena de neón sobre el hueso
        con.tira([q + V((0, 0, 0.17 * (1 - i / 9))) for i, q in enumerate(pts)], [V((0, 0, 1))] * 8, 0.05, "neon",
                 alto=0.03)
    # membranas entre huesos (cristal semitransparente)
    for h1, h2 in zip(huesos[:-1], huesos[1:]):
        filas = []
        for i in range(8):
            a, b = h1[i], h2[i]
            m = (a + b) / 2 + V((0, 0, -0.18))
            filas.append([a + V((0, 0, 0.02)), m, b + V((0, 0, 0.02)), b - V((0, 0, 0.02)), m - V((0, 0, 0.04)),
                          a - V((0, 0, 0.02))])
        con.loft(filas, "cristal", tapa_ini=False, tapa_fin=False)
    # punta: garra bajo el primer hueso
    q = huesos[1][6]
    con.caja((q.x, q.y, q.z - 0.3), (0.6, 0.8, 0.4), "organico")
    con.acople("acople_punta", (q.x, q.y, q.z - 0.5), (0, 0, -1), "ALA_PUNTA", "salida", en_superficie=True)


def ala_energia(con, p):
    """Marco de ala con emisores: el campo de energía es una lámina (ForceField) con una rejilla de neón."""
    s = p["envergadura"]
    c0, c1, fl = p["cuerda_raiz"], p["cuerda_punta"], p["flecha"]
    esquinas = [V((0.9, -c0 / 2, 0)), V((s, -c0 / 2 + fl, 0.5)), V((s, -c0 / 2 + fl + c1, 0.5)),
                V((0.9, c0 / 2, 0))]
    con.loft([[V((0.14, -1.0, -0.8)), V((0.14, 1.0, -0.8)), V((0.14, 1.0, 0.8)), V((0.14, -1.0, 0.8))],
              [V((1.1, -c0 / 2, -0.25)), V((1.1, c0 / 2, -0.25)), V((1.1, c0 / 2, 0.25)), V((1.1, -c0 / 2, 0.25))]],
             "secundario")
    con.acople("acople_raiz", (0, 0, 0), (-1, 0, 0), "CASCO_LATERAL", "entrada", acepta=["CASCO_LATERAL"])
    # marco: borde de ataque y de salida + punta, tubos
    for a, b in ((esquinas[0], esquinas[1]), (esquinas[1], esquinas[2]), (esquinas[3], esquinas[2])):
        con.cilindro(a, b - a, 0.16, (b - a).length, "primario", lados=8)
        n = 4
        for k in range(1, n):
            q = a + (b - a) * k / n
            con.toro(q, b - a, 0.2, 0.05, "neon", n1=10, n2=4)
    for q in esquinas[1:3]:
        con.esfera(q, 0.26, "metal", lados=10, anillos=6)
        con.esfera(q, 0.14, "neon", lados=8, anillos=4, escala=(1.9, 1.9, 1.9))
    # lámina del campo y rejilla
    a, b, c_, d = esquinas
    filas = []
    for k in range(5):
        u = k / 4
        p0 = a + (b - a) * u
        p1 = d + (c_ - d) * u
        filas.append([p0, p1])
    sup = [[f[0] + V((0, 0, 0.02)), f[1] + V((0, 0, 0.02))] for f in filas]
    inf = [[f[1] - V((0, 0, 0.02)), f[0] - V((0, 0, 0.02))] for f in filas]
    con.loft([s_ + i_ for s_, i_ in zip(sup, inf)], "domo", tapa_ini=False, tapa_fin=False)
    for k in range(1, 4):
        u = k / 4
        p0 = a + (b - a) * u
        p1 = d + (c_ - d) * u
        con.tira([p0, p1], [V((0, 0, 1))] * 2, 0.03, "neon2", alto=0.02)
    q = (b + c_) / 2
    con.caja((q.x - 0.3, q.y, q.z - 0.35), (0.6, 0.9, 0.4), "oscuro")
    con.acople("acople_punta", (q.x - 0.3, q.y, q.z - 0.55), (0, 0, -1), "ALA_PUNTA", "salida", en_superficie=True)
