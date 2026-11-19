"""
Geometría del almacén general del pueblo.

construir() devuelve {pieza: Malla} y la lista de calcos por material. Las piezas son las mallas que se exportan:
  almacen                  cuerpo: estructura, mecanismos, muelle, atrezo e interior (todo lo que no se mueve)
  almacen_porton           persiana del portón principal (se enrolla: pivote arriba, en el eje del tambor)
  almacen_porton_trasero   persiana del portón trasero (igual)
  almacen_puerta           puerta de personal con su ventanilla (pivote en el eje de las bisagras)
  almacen_cristal          cristal armado de las ventanas y policarbonato de los tragaluces
  almacen_neon             lentes de los focos y pantallas (báscula, contador)
"""

import math
import random

from mathutils import Matrix, Vector

import datos as D
from geo import Malla, X, Y, Z, rot, rot_z
from materiales import Calco

rnd = random.Random(1977)

PIEZAS = ["almacen", "almacen_porton", "almacen_porton_trasero", "almacen_puerta", "almacen_cristal", "almacen_neon"]


class Obra:
    """Lo que se va construyendo: mallas, calcos (por material) e imágenes que hacen falta, y anclajes."""

    def __init__(self):
        self.m = {n: Malla(n) for n in PIEZAS}
        self.calcos = {}
        self.anclajes = {}

    @property
    def c(self):
        return self.m["almacen"]

    def calco(self, materiales, cal):
        for mat in materiales:
            self.calcos.setdefault(mat, []).append(cal)


# --------------------------------------------------------------------------------------------------------------
# Piezas pequeñas reutilizables
# --------------------------------------------------------------------------------------------------------------


def remache(m, p, normal, mat="remache", r=0.04):
    """Remache grueso de cabeza abombada (5 lados, dos anillos)."""
    m.cilindro_anillos(p - Vector(normal) * 0.01, normal, [(0.0, r), (0.03, r * 0.55)], mat,
                       lados=5)


def tornillo(m, p, normal, mat="remache", r=0.025):
    m.cilindro(Vector(p) - Vector(normal) * 0.005, r, 0.02, mat, lados=6, eje=normal)


def tubo_codo(puntos, radio_curva=0.12, pasos=3):
    """Polilínea con las esquinas redondeadas (para tubos, barandillas, asas)."""
    P = [Vector(p) for p in puntos]
    out = [P[0]]
    for i in range(1, len(P) - 1):
        a, b, c = P[i - 1], P[i], P[i + 1]
        da, dc = (a - b), (c - b)
        r = min(radio_curva, da.length * 0.45, dc.length * 0.45)
        p0 = b + da.normalized() * r
        p2 = b + dc.normalized() * r
        for k in range(pasos + 1):
            t = k / pasos
            out.append((1 - t) ** 2 * p0 + 2 * (1 - t) * t * b + t * t * p2)
    out.append(P[-1])
    return out


def caja_rot(m, centro, tam, mat, ang_z=0.0, ang_x=0.0, ang_y=0.0, mats=None):
    g = rot(ang_z, "Z") @ rot(ang_y, "Y") @ rot(ang_x, "X")
    return m.caja(centro, tam, mat, giro=g, mats=mats)


def perfil_l(m, origen, U, V, W, a, b, t, mat):
    """Angular en L: alas de a (a lo largo de U) y b (a lo largo de V), espesor t, extruido W."""
    pts = [(0, 0), (a, 0), (a, t), (t, t), (t, b), (0, b)]
    m.extruir(pts, origen, U, V, W, mat)


def perfil_u(m, origen, U, V, W, ancho, fondo, t, mat):
    """Perfil en U abierto hacia +V: base de `ancho` (U), alas de `fondo` (V)."""
    pts = [(0, 0), (ancho, 0), (ancho, fondo), (ancho - t, fondo), (ancho - t, t), (t, t), (t, fondo), (0, fondo)]
    m.extruir(pts, origen, U, V, W, mat)


def eslabon(m, centro, eje, giro, largo, ancho, r, mat):
    """Eslabón de cadena (anillo alargado de 4 tramos y sección triangular)."""
    eje = Vector(eje).normalized()
    lado = (eje.cross(Z) if abs(eje.dot(Z)) < 0.9 else eje.cross(X)).normalized()
    lado = (Matrix.Rotation(giro, 3, eje) @ lado).normalized()
    c = Vector(centro)
    hl, ha = largo / 2 - r, ancho / 2 - r
    pts = [c + eje * hl, c + lado * ha, c - eje * hl, c - lado * ha]
    m.tubo(pts, r, mat, lados=3, cerrado=True)


def cadena(m, puntos, paso, mat, largo=0.27, ancho=0.14, r=0.026):
    """Cadena de eslabones a lo largo de una polilínea; cada eslabón girado 90° respecto al anterior."""
    P = [Vector(p) for p in puntos]
    tramos = [(P[i], P[i + 1]) for i in range(len(P) - 1)]
    total = sum((b - a).length for a, b in tramos)
    n = max(2, int(total / paso))
    for k in range(n):
        d = (k + 0.5) * total / n
        for a, b in tramos:
            L = (b - a).length
            if d <= L:
                p = a + (b - a) * (d / L)
                m_eje = (b - a).normalized()
                break
            d -= L
        eslabon(m, p, m_eje, (math.pi / 2) * (k % 2), largo, ancho, r, mat)


# --------------------------------------------------------------------------------------------------------------
# Estructura
# --------------------------------------------------------------------------------------------------------------

TONOS = ["chapa_gris", "chapa_gris", "chapa_clara", "chapa_gris", "chapa_oscura", "chapa_gris", "chapa_verdosa",
         "chapa_gris", "chapa_gris", "chapa_clara", "chapa_oscura", "chapa_gris"]


def muro(o, cara, huecos, ancho_hoja=1.85, tonos_fijos=None):
    """
    Pared de chapa grecada por hojas. cara = 'frente' | 'trasera' | 'izq' | 'der'.
    huecos: [(u0, u1, z0, z1)] en coordenadas de la pared (u = x en frente/trasera, u = y en laterales).
    Cada hoja es una pieza con su tono (algunas sustituidas con el tiempo) y las hojas alternas sobresalen un pelo
    para que se lea el solape.
    """
    m = o.c
    if cara == "frente":
        org, U, N, ua, ub, zt = Vector((0, D.Y0, 0)), X, -Y, D.X0, D.X1, D.z_arco
    elif cara == "trasera":
        org, U, N, ua, ub, zt = Vector((0, D.Y1, 0)), X, Y, D.X0, D.X1, D.z_arco
    elif cara == "der":
        org, U, N, ua, ub, zt = Vector((D.X1, 0, 0)), Y, X, D.Y0, D.Y1, (lambda u: D.Z_ALERO)
    else:
        org, U, N, ua, ub, zt = Vector((D.X0, 0, 0)), Y, -X, D.Y0, D.Y1, (lambda u: D.Z_ALERO)
    cortes = {ua, ub}
    u = ua
    while u < ub - 0.3:
        cortes.add(round(u, 4))
        u += ancho_hoja
    for h in huecos:
        cortes.add(h[0])
        cortes.add(h[1])
    cortes = sorted(c for c in cortes if ua <= c <= ub)
    hoja = 0
    for a, b in zip(cortes, cortes[1:]):
        if b - a < 0.05:
            continue
        mid = (a + b) / 2
        tramos = [(D.Z_ZOCALO, None)]
        dentro = [h for h in huecos if h[0] <= mid <= h[1]]
        # intervalos en z que quedan fuera de los huecos
        segs = []
        z = D.Z_ZOCALO
        for h in sorted(dentro, key=lambda h: h[2]):
            if h[2] > z + 0.02:
                segs.append((z, h[2]))
            z = h[3]
        segs.append((z, "arriba"))
        idx = hoja
        hoja += 1
        tono = (tonos_fijos or {}).get(idx, TONOS[(idx * 7 + len(cara)) % len(TONOS)])
        sale = 0.012 if idx % 2 else 0.0
        for z0, z1 in segs:
            fz0 = (lambda u, z0=z0: z0)
            fz1 = zt if z1 == "arriba" else (lambda u, z1=z1: z1)
            m.panel_ondulado(org + N * sale, U, N, a, b, fz0, fz1, tono, periodo=D.ONDA["periodo"],
                             fondo=D.ONDA["fondo"], grosor=D.GROSOR_MURO, mat_dentro="chapa_interior")


ZOCALO = (D.X0 - 0.2, D.X1 + 0.2, D.Y0 - 0.05, D.Y1 + 0.2)


def tapado_explanada(x, y):
    """¿Este punto de la explanada queda debajo del zócalo, del muelle o de la repisa trasera?"""
    M, R = D.MUELLE, D.REPISA_TRASERA
    for x0, x1, y0, y1 in ((ZOCALO[0], ZOCALO[1], ZOCALO[2], ZOCALO[3]), (M["x0"], M["x1"], M["y0"], M["y1"]),
                           (R["x0"], R["x1"], D.Y1, R["y1"])):
        if x0 - 1e-3 <= x <= x1 + 1e-3 and y0 - 1e-3 <= y <= y1 + 1e-3:
            return True
    return False


def estructura(o):
    m = o.c
    # --- explanada de hormigón con el hundido delante del muelle ---
    E = D.EXPLANADA
    xs = sorted(set([E["x0"], E["x1"]] + [] +
                    [D.HUNDIDO["x"] + d for d in (-1.4, 0, 1.4)]))
    ys = sorted(set([E["y0"], E["y1"]] + [] +
                    [D.HUNDIDO["y"] + d for d in (-1.1, 0, 1.0)] + [D.MUELLE["y0"]]))
    M, R = D.MUELLE, D.REPISA_TRASERA
    xs = sorted(set(xs + [ZOCALO[0], ZOCALO[1], M["x0"], M["x1"], R["x0"], R["x1"], D.RAMPA["x0"], D.RAMPA["x1"]]))
    ys = sorted(set(ys + [ZOCALO[2], ZOCALO[3], R["y1"]]))
    xs = [x for x in xs if E["x0"] <= x <= E["x1"]]
    ys = [y for y in ys if E["y0"] <= y <= E["y1"]]

    assert D.HUNDIDO["fondo"] < D.S - 0.01, "el hundido no puede atravesar la losa de la explanada"

    def z_expl(x, y):
        d = math.hypot((x - D.HUNDIDO["x"]) / 1.0, (y - D.HUNDIDO["y"]) / 0.8) / D.HUNDIDO["radio"]
        return D.S - D.HUNDIDO["fondo"] * max(0.0, 1 - d * d) ** 1.5

    bm = m.bm
    top = [[m._v((x, y, z_expl(x, y))) for x in xs] for y in ys]
    bot = [[m._v((x, y, 0.0)) if (i in (0, len(xs) - 1) or j in (0, len(ys) - 1)) else None for i, x in enumerate(xs)]
           for j, y in enumerate(ys)]
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            m._f((top[j][i], top[j][i + 1], top[j + 1][i + 1], top[j + 1][i]), "hormigon_explanada")
    nx, ny = len(xs) - 1, len(ys) - 1
    # costados
    for i in range(nx):
        m._f((top[0][i], bot[0][i], bot[0][i + 1], top[0][i + 1]), "hormigon_explanada")
        m._f((top[ny][i + 1], bot[ny][i + 1], bot[ny][i], top[ny][i]), "hormigon_explanada")
    for j in range(ny):
        m._f((top[j + 1][0], bot[j + 1][0], bot[j][0], top[j][0]), "hormigon_explanada")
        m._f((top[j][nx], bot[j][nx], bot[j + 1][nx], top[j + 1][nx]), "hormigon_explanada")
    borde = [bot[0][i] for i in range(nx + 1)] + [bot[j][nx] for j in range(1, ny + 1)] + \
            [bot[ny][i] for i in range(nx - 1, -1, -1)] + [bot[j][0] for j in range(ny - 1, 0, -1)]
    m._f(borde, "hormigon_explanada")

    # --- zócalo (base de hormigón armado elevada medio stud) y losa interior ---
    # el zócalo es un anillo bajo las paredes; dentro, la losa del suelo (así no se gasta atlas en caras tapadas)
    zx0, zx1, zy0, zy1 = ZOCALO
    m.caja_de((zx0, zy0, 0.0), (D.X0 + 0.05, zy1, D.Z_ZOCALO), "hormigon_zocalo")
    m.caja_de((D.X1 - 0.05, zy0, 0.0), (zx1, zy1, D.Z_ZOCALO), "hormigon_zocalo")
    m.caja_de((D.X0 + 0.05, zy0, 0.0), (D.X1 - 0.05, D.Y0 + 0.02, D.Z_ZOCALO), "hormigon_zocalo")
    m.caja_de((D.X0 + 0.05, D.Y1 - 0.02, 0.0), (D.X1 - 0.05, zy1, D.Z_ZOCALO), "hormigon_zocalo")
    m.caja_de((D.X0 + 0.05, D.Y0 + 0.02, 0.0), (D.X1 - 0.05, D.Y1 - 0.02, D.Z_SUELO), "suelo_interior")

    # --- paredes ---
    P, Pu, V = D.PORTON, D.PUERTA, D.VENTANA_OFICINA
    muro(o, "frente", [(P["x0"], P["x1"], P["z0"], P["z1"]), (Pu["x0"], Pu["x1"], Pu["z0"], Pu["z1"]),
                       (V["x0"], V["x1"], V["z0"], V["z1"])], tonos_fijos={0: "chapa_gris", 3: "chapa_clara"})
    T = D.PORTON_TRASERO
    muro(o, "trasera", [(T["x0"], T["x1"], T["z0"], T["z1"])])
    C = D.CLARISTORIO
    muro(o, "der", [(C["y0"], C["y1"], C["z0"], C["z1"])], tonos_fijos={0: "chapa_gris", 1: "chapa_gris",
                                                                         2: "chapa_clara", 3: "chapa_gris"})
    muro(o, "izq", [])

    # --- remates de esquina (angulares) con remaches ---
    sal = D.ONDA["fondo"] + 0.02
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        x = D.X1 if sx > 0 else D.X0
        y = D.Y1 if sy > 0 else D.Y0
        org = Vector((x + sx * sal, y + sy * sal, D.Z_ZOCALO))
        U = Vector((-sx, 0, 0))
        Vv = Vector((0, -sy, 0))
        top = D.Z_ALERO + 0.02
        perfil_l(m, org, U, Vv, Z * (top - D.Z_ZOCALO), 0.3, 0.3, 0.035, "remate")
        for k in range(3):
            z = D.Z_ZOCALO + 0.6 + k * 1.4
            remache(m, org + U * 0.17 + Z * z + Vector((0, sy * 0.035, 0)) - Z * D.Z_ZOCALO, Vector((0, sy, 0)))
            remache(m, org + Vv * 0.17 + Z * z + Vector((sx * 0.035, 0, 0)) - Z * D.Z_ZOCALO, Vector((sx, 0, 0)))

    # --- vierteaguas del zócalo (remate inferior) ---
    for cara in ("frente", "trasera", "izq", "der"):
        if cara in ("frente", "trasera"):
            y = (D.Y0 - sal) if cara == "frente" else (D.Y1 + sal)
            if cara == "frente":
                continue  # tapado por el muelle
            m.caja_de((D.X0, y - 0.04 if cara == "trasera" else y, D.Z_ZOCALO),
                      (D.X1, y + 0.0 if cara == "trasera" else y + 0.04, D.Z_ZOCALO + 0.12), "remate")
        else:
            x = (D.X0 - sal) if cara == "izq" else (D.X1 + sal)
            m.caja_de((x - 0.0 if cara == "der" else x, D.Y0, D.Z_ZOCALO),
                      (x + 0.04 if cara == "der" else x + 0.04, D.Y1, D.Z_ZOCALO + 0.12), "remate")

    tejado(o)
    canalones(o)


def tejado(o):
    """Tejado en arco tipo hangar con dos tragaluces largos. La onda de la chapa va en el mapa de normales."""
    m = o.c
    R_in, R_out = D.R_ARCO, D.R_ARCO + D.GROSOR_TEJADO
    xe = D.X1 + D.VUELO_LADO
    te = math.asin(xe / R_out)
    # ángulos: reparto uniforme + bordes de los tragaluces
    angs = set(round(-te + 2 * te * i / 22, 6) for i in range(23))
    for xa, xb in D.TRAGALUCES:
        angs.add(round(math.asin(xa / R_out), 6))
        angs.add(round(math.asin(xb / R_out), 6))
    angs = sorted(angs)
    y0, y1 = D.Y0 - D.VUELO_FRENTE, D.Y1 + D.VUELO_FRENTE
    ya, yb = D.TRAGALUZ_Y
    filas = [y0, ya, yb, y1]

    def pt(a, r, y):
        return Vector((r * math.sin(a), y, D.ZC_ARCO + r * math.cos(a)))

    def en_tragaluz(a0, a1):
        xm = R_out * math.sin((a0 + a1) / 2)
        return any(xa < xm < xb for xa, xb in D.TRAGALUCES)

    O = [[m._v(pt(a, R_out, y)) for y in filas] for a in angs]
    I = [[m._v(pt(a, R_in, y)) for y in filas] for a in angs]
    n = len(angs)
    for i in range(n - 1):
        hueco = en_tragaluz(angs[i], angs[i + 1])
        for j in range(3):
            if hueco and j == 1:
                continue
            m._f((O[i][j], O[i + 1][j], O[i + 1][j + 1], O[i][j + 1]), "tejado")
            m._f((I[i][j + 1], I[i + 1][j + 1], I[i + 1][j], I[i][j]), "tejado_interior")
        # testeros
        m._f((O[i][0], I[i][0], I[i + 1][0], O[i + 1][0]), "tejado")
        m._f((O[i + 1][3], I[i + 1][3], I[i][3], O[i][3]), "tejado")
        if hueco:
            m._f((O[i][1], O[i + 1][1], I[i + 1][1], I[i][1]), "tejado")
            m._f((O[i + 1][2], O[i][2], I[i][2], I[i + 1][2]), "tejado")
    # aleros
    for i in (0, n - 1):
        m._f([O[i][0], O[i][1], O[i][2], O[i][3], I[i][3], I[i][2], I[i][1], I[i][0]], "tejado")
    # costados de los huecos (a lo largo de y)
    for i in range(n):
        izq = i > 0 and en_tragaluz(angs[i - 1], angs[i])
        der = i < n - 1 and en_tragaluz(angs[i], angs[i + 1])
        if izq != der:
            m._f((O[i][1], O[i][2], I[i][2], I[i][1]), "tejado")

    # tragaluces: policarbonato ondulado (pieza de cristal) con un marco de remate
    cr = o.m["almacen_cristal"]
    for xa, xb in D.TRAGALUCES:
        aa, ab = math.asin(xa / R_out), math.asin(xb / R_out)
        pasos = 4
        anillos = []
        for k in range(pasos + 1):
            a = aa + (ab - aa) * k / pasos
            anillos.append([pt(a, R_out + 0.02, ya - 0.05), pt(a, R_out + 0.02, yb + 0.05),
                            pt(a, R_in + 0.02, yb + 0.05), pt(a, R_in + 0.02, ya - 0.05)])
        cr.loft(anillos, "policarbonato")
        # marco (costeros a lo largo de y y cabezas en arco)
        for a in (aa, ab):
            d = Vector((math.sin(a), 0, math.cos(a)))
            c = pt(a, R_out + 0.05, (ya + yb) / 2)
            g = Matrix((d.cross(Y), Y, d)).transposed()
            m.caja(c, (0.12, yb - ya + 0.3, 0.1), "remate", giro=g)
        for y in (ya - 0.1, yb + 0.1):
            anillos = []
            for k in range(pasos + 1):
                a = aa + (ab - aa) * k / pasos
                anillos.append([pt(a, R_out + 0.0, y - 0.06), pt(a, R_out + 0.0, y + 0.06),
                                pt(a, R_out + 0.1, y + 0.06), pt(a, R_out + 0.1, y - 0.06)])
            m.loft(anillos, "remate")

    # remates de los testeros (cubren el canto del tejado y el encuentro con la fachada)
    pasos = 10
    for y, s in ((y0, -1), (y1, 1)):
        anillos = []
        for k in range(pasos + 1):
            a = -te + 2 * te * k / pasos
            anillos.append([pt(a, R_in - 0.16, y - s * 0.02), pt(a, R_out + 0.06, y - s * 0.02),
                            pt(a, R_out + 0.06, y + s * 0.05), pt(a, R_in - 0.16, y + s * 0.05)])
        m.loft(anillos, "remate")
    o.anclajes["arco"] = dict(radio=R_out, centro_z=D.ZC_ARCO)


def canalones(o):
    m = o.c
    R_out = D.R_ARCO + D.GROSOR_TEJADO
    xe = D.X1 + D.VUELO_LADO
    ze = D.ZC_ARCO + math.sqrt(R_out ** 2 - xe ** 2)
    y0, y1 = D.Y0 - D.VUELO_FRENTE - 0.05, D.Y1 + D.VUELO_FRENTE + 0.05
    perfil = [(-0.03, 0.02), (-0.03, -0.24), (0.26, -0.24), (0.3, 0.04), (0.27, 0.04), (0.235, -0.205),
              (0.0, -0.205), (0.0, 0.02)]
    bajantes = {1: [D.Y0 + 0.45], -1: [D.Y1 - 0.45]}
    for s in (1, -1):
        U = Vector((s, 0, 0))
        org = Vector((s * (xe - 0.12), y0, ze - 0.02))
        m.extruir(perfil, org, U, Z, Y * (y1 - y0), "canalon")
        for yb in bajantes[s]:
            xb = s * (xe + 0.02)
            xw = s * (D.X1 + D.ONDA["fondo"] + 0.11)
            r = 0.075
            pts = [(xb, yb, ze - 0.2), (xb, yb, ze - 0.42), (xw, yb, ze - 0.82), (xw, yb, 0.42),
                   (xw + s * 0.25, yb, D.S + 0.1)]
            m.tubo(tubo_codo(pts, 0.18, 2), r, "canalon", lados=6)
            # embudo de salida del canalón
            m.cilindro(Vector((xb, yb, ze - 0.25)), r * 1.1, 0.06, "canalon", lados=6, radio2=r * 1.6)
            # abrazaderas
            for z in (1.2, 3.3):
                m.cilindro(Vector((xw, yb, z)), r + 0.018, 0.07, "remate", lados=6)
                m.caja(Vector(((xw + s * D.X1) / 2 + s * 0.04, yb, z + 0.035)), (abs(xw - s * D.X1), 0.06, 0.05),
                       "remate")
            # zapata de hormigón para el agua
            m.caja(Vector((xw + s * 0.42, yb, D.S + 0.025)), (0.5, 0.3, 0.05), "hormigon_zocalo")


# --------------------------------------------------------------------------------------------------------------
# Portones de persiana
# --------------------------------------------------------------------------------------------------------------


def persiana(o, pieza, x0, x1, z0, z1, y_cara, mat, mats_lama=None, abolladura=None, desgaste=0.0):
    """
    Cortina de lamas (pieza móvil) del suelo z0 al eje del tambor z1, en el plano y_cara (cara exterior de la
    cortina, que mira a -Y si la fachada es la principal; para la trasera se gira después).
    Cada lama tiene el perfil abombado con la junta hundida; las lamas de la abolladura van partidas para poder
    hundirlas.
    """
    m = o.m[pieza]
    alto_bajo = 0.12
    nl = max(1, round((z1 - z0 - alto_bajo) / 0.25))
    h = (z1 - z0 - alto_bajo) / nl
    perfil = [(0.025, 0.0), (-0.012, 0.0), (-0.032, 0.5), (-0.012, 1.0), (0.025, 1.0)]
    xa, xb = x0 - 0.07, x1 + 0.07
    for k in range(nl):
        zb = z0 + alto_bajo + k * h
        nombre = (mats_lama or {}).get(k, mat)
        estaciones = [xa, xb]
        if abolladura and abs((zb + h / 2) - abolladura[1]) < abolladura[2] * 0.7 + h / 2:
            ax, az, ar, af = abolladura
            estaciones = sorted(set([xa, xb] + [ax + ar * t for t in (-1.0, -0.45, 0.0, 0.45, 1.0)]))
        anillos = []
        for x in estaciones:
            anillo = []
            for dy, fz in perfil:
                z = zb + fz * h
                dent = 0.0
                if abolladura:
                    ax, az, ar, af = abolladura
                    d = math.hypot((x - ax) / ar, (z - az) / (ar * 0.7))
                    dent = af * max(0.0, 1 - d * d) ** 2
                anillo.append(Vector((x, y_cara + 0.032 + dy + dent, z)))
            anillos.append(anillo)
        m.loft(anillos, nombre)
    # barra inferior con goma, asas y cerradura
    yc = y_cara + 0.032
    m.caja_de((xa, yc - 0.04, z0 + 0.025), (xb, yc + 0.03, z0 + alto_bajo), "guia")
    m.caja_de((xa + 0.02, yc - 0.03, z0), (xb - 0.02, yc + 0.02, z0 + 0.03), "goma")
    for xh in (x0 + 0.9, x1 - 0.9):
        pts = [(xh - 0.13, yc - 0.04, z0 + 0.075), (xh - 0.13, yc - 0.12, z0 + 0.075), (xh + 0.13, yc - 0.12, z0 + 0.075),
               (xh + 0.13, yc - 0.04, z0 + 0.075)]
        m.tubo(pts, 0.018, "metal_desnudo", lados=4)
    xm = (x0 + x1) / 2
    m.caja(Vector((xm, yc - 0.05, z0 + 0.075)), (0.16, 0.03, 0.08), "metal_desnudo")
    m.cilindro(Vector((xm, yc - 0.065, z0 + 0.075)), 0.025, 0.02, "laton", lados=6, eje=-Y)
    return h


def mecanismo(o, x0, x1, y_cara, z_eje, r_tambor, lado_cadena, z_cadena, mat_tambor="tambor", con_cadena=True):
    """
    Tambor (con la persiana enrollada), soportes, eje, rueda de cadena y la cadena de maniobra que cuelga en un lado.
    Todo en la fachada principal (mira a -Y); la trasera se construye igual y se gira.
    """
    m = o.c
    ye = y_cara + 0.032 - r_tambor - 0.012     # el eje: la cortina baja tangente a la cara trasera del rollo
    xa, xb = x0 - 0.12, x1 + 0.12
    # rollo: polígono con caras alternas (se leen las vueltas de lamas)
    lados = 16
    anillos = []
    for x in (xa, xb):
        anillos.append([Vector((x, ye + math.cos(math.tau * i / lados) * r_tambor * (1 if i % 2 else 0.965),
                                z_eje + math.sin(math.tau * i / lados) * r_tambor * (1 if i % 2 else 0.965)))
                        for i in range(lados)])
    m.loft(anillos, mat_tambor)
    # soportes laterales (placas gruesas) atornillados a la pared
    yw = D.Y0 - D.ONDA["fondo"]
    for x, s in ((xa - 0.06, -1), (xb + 0.06, 1)):
        prof = yw - (ye - r_tambor - 0.08)
        m.caja(Vector((x, yw - prof / 2, z_eje + 0.02)), (0.06, prof, r_tambor * 2 + 0.28), "guia")
        m.cilindro(Vector((x - s * 0.03, ye, z_eje)), 0.07, 0.12 if s < 0 else 0.1, "metal_desnudo", lados=8,
                   eje=Vector((s, 0, 0)))
    # rueda de la cadena (fuera del soporte del lado de la cadena)
    xr = (xb + 0.2) if lado_cadena > 0 else (xa - 0.2)
    rr = 0.2
    dientes = 12
    anillos = []
    for x in (xr - 0.03, xr + 0.03):
        anillos.append([Vector((x, ye + math.cos(math.tau * i / dientes) * rr * (1 if i % 2 else 0.88),
                                z_eje + math.sin(math.tau * i / dientes) * rr * (1 if i % 2 else 0.88)))
                        for i in range(dientes)])
    m.loft(anillos, "metal_desnudo")
    m.cilindro(Vector((min(xr, xb) - 0.05, ye, z_eje)), 0.04, abs(xr - xb) + 0.1, "metal_desnudo", lados=6, eje=X)
    # cadena: dos ramales y el bucle de abajo
    ys = (ye - rr, ye + rr)
    zb = z_cadena
    bucle = [Vector((xr, ye + math.cos(math.pi + math.pi * t / 4) * rr, zb + math.sin(math.pi + math.pi * t / 4) * rr))
             for t in range(5)]
    pts = [Vector((xr, ys[0], z_eje))] + bucle + [Vector((xr, ys[1], z_eje))]
    if con_cadena:
        cadena(m, pts, 0.25, "cadena", largo=0.32, ancho=0.16)
    # guías laterales: perfil en U de chapa, abiertas hacia el hueco
    return ye


def guias(o, x0, x1, z0, z_top, y_cara):
    """Guías laterales: perfil en U abierto hacia el hueco; la cortina corre entre sus dos alas."""
    m = o.c
    yw = D.Y0 - D.ONDA["fondo"]
    yf = y_cara - 0.03
    for x, s in ((x0, 1), (x1, -1)):
        pts = [(-0.17, yw), (0.04, yw), (0.04, yw - 0.03), (-0.14, yw - 0.03), (-0.14, yf + 0.03), (0.04, yf + 0.03),
               (0.04, yf), (-0.17, yf)]
        m.extruir([(x + s * u, y) for u, y in pts], Vector((0, 0, z0)), X, Y, Z * (z_top - z0), "guia")
        # tope de goma abajo
        m.caja(Vector((x - s * 0.06, (yw + yf) / 2, z0 + 0.04)), (0.14, yw - yf - 0.04, 0.08), "goma")


def porton_principal(o):
    P = D.PORTON
    yw = D.Y0 - D.ONDA["fondo"]
    y_cara = yw - 0.2          # cara de atrás de la cortina
    r_tambor, z_eje = 0.3, P["z1"] + 0.42
    ye = mecanismo(o, P["x0"], P["x1"], y_cara, z_eje, r_tambor, 1, 2.2)
    guias(o, P["x0"], P["x1"], P["z0"], P["z1"] + 0.15, y_cara)
    persiana(o, "almacen_porton", P["x0"], P["x1"], P["z0"], z_eje, y_cara, "persiana",
             mats_lama={4: "persiana_nueva", 9: "persiana_nueva", 10: "persiana_oscura"},
             abolladura=(P["x0"] + 0.85, P["z0"] + 0.62, 0.38, 0.05))
    m = o.c
    # dintel: chapa de remate sobre el hueco y alféizar de acero en el umbral
    m.caja_de((P["x0"] - 0.25, yw - 0.06, P["z1"]), (P["x1"] + 0.25, yw, P["z1"] + 0.18), "remate")
    m.caja_de((P["x0"], D.Y0 - 0.02, D.Z_SUELO - 0.03), (P["x1"], D.Y0 + 0.25, D.Z_SUELO + 0.012), "metal_desnudo")
    o.anclajes["porton"] = dict(pivote=[(P["x0"] + P["x1"]) / 2, y_cara + 0.032, z_eje], alto=z_eje - P["z0"],
                                ancho=P["x1"] - P["x0"] + 0.14, eje_tambor=[(P["x0"] + P["x1"]) / 2, ye, z_eje],
                                radio_tambor=r_tambor)


def porton_trasero(o):
    """Se construye como si estuviera en la fachada principal y luego se gira 180° alrededor de su centro."""
    T = D.PORTON_TRASERO
    # construir en una obra temporal con la fachada en Y0 y girar a Y1
    tmp = Obra()
    yw = D.Y0 - D.ONDA["fondo"]
    y_cara = yw - 0.2
    r_tambor, z_eje = 0.27, T["z1"] + 0.38
    # x espejada: tras el giro de 180°, x -> -x
    x0, x1 = -T["x1"], -T["x0"]
    ye = mecanismo(tmp, x0, x1, y_cara, z_eje, r_tambor, -1, 2.0, mat_tambor="tambor_viejo", con_cadena=False)
    guias(tmp, x0, x1, T["z0"], T["z1"] + 0.12, y_cara)
    persiana(tmp, "almacen_porton", x0, x1, T["z0"], z_eje, y_cara, "persiana_trasera",
             mats_lama={2: "persiana_oxido", 3: "persiana_oxido", 7: "persiana_trasera_clara"},
             abolladura=(x1 - 0.7, T["z0"] + 0.9, 0.42, 0.06))
    # tirador de correa (cinta de nailon) colgado de la barra de abajo y enganchada en un gancho de la cortina
    pm = tmp.m["almacen_porton"]
    xc = x0 + 0.6
    yc = y_cara + 0.032 - 0.05
    pm.caja(Vector((xc, yc, T["z0"] + 0.33)), (0.05, 0.008, 0.46), "correa")
    pm.caja(Vector((xc, yc - 0.012, T["z0"] + 0.58)), (0.03, 0.03, 0.05), "metal_desnudo")
    tm = tmp.c
    tm.caja_de((x0 - 0.25, yw - 0.06, T["z1"]), (x1 + 0.25, yw, T["z1"] + 0.16), "remate")
    tm.caja_de((x0, D.Y0 - 0.02, D.Z_SUELO - 0.03), (x1, D.Y0 + 0.25, D.Z_SUELO + 0.012), "metal_desnudo")
    giro = Matrix.Translation((0, (D.Y0 + D.Y1) / 2, 0)) @ Matrix.Rotation(math.pi, 4, "Z") @ \
        Matrix.Translation((0, -(D.Y0 + D.Y1) / 2, 0))
    o.c.unir(tm, giro)
    o.m["almacen_porton_trasero"].unir(tmp.m["almacen_porton"], giro)
    piv = giro @ Vector(((x0 + x1) / 2, y_cara + 0.032, z_eje))
    o.anclajes["porton_trasero"] = dict(pivote=list(piv), alto=z_eje - T["z0"], ancho=T["x1"] - T["x0"] + 0.14,
                                        radio_tambor=r_tambor)


# --------------------------------------------------------------------------------------------------------------
# Puerta de personal y ventanas
# --------------------------------------------------------------------------------------------------------------


def puerta(o):
    Pu = D.PUERTA
    m, p = o.c, o.m["almacen_puerta"]
    yw = D.Y0 - D.ONDA["fondo"]
    x0, x1, z0, z1 = Pu["x0"], Pu["x1"], Pu["z0"], Pu["z1"]
    # marco de acero (premarco que abraza el muro)
    fw = 0.09
    for xa, xb in ((x0 - fw, x0), (x1, x1 + fw)):
        m.caja_de((xa, yw - 0.06, z0), (xb, D.Y0 + D.GROSOR_MURO, z1 + fw), "marco_puerta")
    m.caja_de((x0 - fw, yw - 0.06, z1), (x1 + fw, D.Y0 + D.GROSOR_MURO, z1 + fw), "marco_puerta")
    # hoja (pieza móvil): placa con hueco para la ventanilla, refuerzo y chapa de patada
    t = 0.06
    yh = yw - 0.01 - t        # cara exterior de la hoja
    hx0, hx1 = x0 + 0.01, x1 - 0.01
    ancho, alto = hx1 - hx0, z1 - z0 - 0.02
    hueco = (ancho * 0.3, alto * 0.6, ancho * 0.7, alto * 0.88)
    p.placa_hueco(Vector((hx0, yh, z0 + 0.012)), X, Z, Y * t, ancho, alto, hueco, "puerta_azul")
    # junquillo de la ventanilla
    for (a, b, c, d) in ((hueco[0] - 0.03, hueco[1] - 0.03, hueco[2] + 0.03, hueco[1]),
                         (hueco[0] - 0.03, hueco[3], hueco[2] + 0.03, hueco[3] + 0.03),
                         (hueco[0] - 0.03, hueco[1], hueco[0], hueco[3]), (hueco[2], hueco[1], hueco[2] + 0.03, hueco[3])):
        p.caja_de((hx0 + a, yh - 0.015, z0 + 0.012 + b), (hx0 + c, yh + 0.005, z0 + 0.012 + d), "marco_puerta")
    # cristal armado de la ventanilla (en la propia puerta: se mueve con ella)
    p.caja_de((hx0 + hueco[0], yh + t * 0.4, z0 + 0.012 + hueco[1]), (hx0 + hueco[2], yh + t * 0.6, z0 + 0.012 + hueco[3]),
              "cristal")
    # chapa de patada abajo (rayada)
    p.caja_de((hx0 + 0.04, yh - 0.008, z0 + 0.05), (hx1 - 0.04, yh, z0 + 0.32), "chapa_patada")
    # bisagras (lado izquierdo) y su eje
    xb = x0 - 0.005
    for zb in (z0 + 0.35, z1 - 0.35):
        p.cilindro(Vector((xb, yh - 0.02, zb - 0.1)), 0.03, 0.2, "metal_desnudo", lados=6)
        p.caja(Vector((xb + 0.05, yh - 0.004, zb)), (0.09, 0.012, 0.16), "metal_desnudo")
        m.caja(Vector((xb - 0.045, yw - 0.035, zb)), (0.06, 0.03, 0.16), "metal_desnudo")
        pass
    # manilla industrial (roseta + palanca en codo) y cerradura con la llave puesta
    xm, zm = hx1 - 0.11, z0 + 1.0
    p.caja(Vector((xm, yh - 0.012, zm - 0.06)), (0.07, 0.024, 0.3), "metal_desnudo")
    p.cilindro(Vector((xm, yh - 0.024, zm)), 0.022, 0.06, "metal_desnudo", lados=6, eje=-Y)
    p.tubo(tubo_codo([(xm, yh - 0.08, zm), (xm - 0.16, yh - 0.08, zm), (xm - 0.17, yh - 0.06, zm - 0.01)], 0.03, 2),
           0.018, "metal_desnudo", lados=6)
    zl = zm - 0.16
    p.cilindro(Vector((xm, yh - 0.024, zl)), 0.022, 0.025, "laton", lados=6, eje=-Y)
    p.caja(Vector((xm, yh - 0.07, zl)), (0.008, 0.05, 0.022), "laton")                    # paleta de la llave
    p.cilindro(Vector((xm, yh - 0.115, zl - 0.0)), 0.03, 0.006, "laton", lados=6, eje=X)  # cabeza de la llave
    p.tubo([(xm, yh - 0.14, zl + 0.03), (xm, yh - 0.17, zl + 0.0), (xm, yh - 0.14, zl - 0.03),
            (xm, yh - 0.11, zl + 0.0)], 0.005, "laton", lados=3, cerrado=True)                # aro del llavero
    # cierrapuertas arriba (cuerpo en la hoja, brazo al marco)
    p.caja(Vector((hx0 + 0.25, yh - 0.035, z1 - 0.11)), (0.28, 0.06, 0.07), "marco_puerta")
    p.caja(Vector((hx0 + 0.36, yh - 0.075, z1 - 0.1)), (0.2, 0.02, 0.025), "metal_desnudo")
    m.caja(Vector((hx0 + 0.48, yw - 0.07, z1 + 0.04)), (0.08, 0.05, 0.05), "metal_desnudo")
    o.anclajes["puerta"] = dict(pivote=[xb, yh - 0.02, z0], ancho=ancho, alto=alto, abre_hacia="fuera (-Y), bisagras a la izquierda")
    # cartel OFICINA sobre la puerta
    cx = (x0 + x1) / 2
    m.caja(Vector((cx, yw - 0.045, z1 + 0.32)), (0.92, 0.02, 0.24), "cartel_oficina")
    for dx in (-0.4, 0.4):
        m.cilindro(Vector((cx + dx, yw - 0.035, z1 + 0.32)), 0.015, 0.035, "remache", lados=5, eje=-Y)
    o.calco(["cartel_oficina"], Calco("cartel_oficina", (cx, yw - 0.055, z1 + 0.32), (1, 0, 0), (0, 0, 1),
                                      (0.92, 0.24), profundidad=0.02, modo="pintura", rugosidad=0.45))


def ventana(o, x0, x1, z0, z1, cara="frente"):
    """Ventana de acero con cristal armado, vierteaguas inclinado, goterón y junquillos."""
    m, cr = o.c, o.m["almacen_cristal"]
    yw = D.Y0 - D.ONDA["fondo"]
    f = 0.08
    # marco exterior
    m.caja_de((x0 - f, yw - 0.05, z1), (x1 + f, D.Y0 + 0.05, z1 + f), "marco_ventana")
    m.caja_de((x0 - f, yw - 0.05, z0), (x0, D.Y0 + 0.05, z1), "marco_ventana")
    m.caja_de((x1, yw - 0.05, z0), (x1 + f, D.Y0 + 0.05, z1), "marco_ventana")
    # alféizar inclinado (vierteaguas) y goterón superior
    m.extruir([(0, 0), (0.2, -0.06), (0.2, -0.03), (0, 0.025)], Vector((x0 - f - 0.05, yw + 0.02, z0)), -Y, Z,
              X * (x1 - x0 + 2 * f + 0.1), "remate")
    m.caja_de((x0 - f - 0.04, yw - 0.12, z1 + f), (x1 + f + 0.04, yw - 0.02, z1 + f + 0.04), "remate")
    # travesaño y junquillos interiores
    m.caja_de((x0, D.Y0 + 0.07, z0), (x1, D.Y0 + 0.11, z0 + 0.04), "marco_ventana")
    m.caja_de((x0, D.Y0 + 0.07, z1 - 0.04), (x1, D.Y0 + 0.11, z1), "marco_ventana")
    xm = (x0 + x1) / 2
    m.caja_de((xm - 0.025, D.Y0 + 0.07, z0), (xm + 0.025, D.Y0 + 0.11, z1), "marco_ventana")
    cr.caja_de((x0, D.Y0 + 0.08, z0), (x1, D.Y0 + 0.095, z1), "cristal")


def claristorio(o):
    """Ventana alta y estrecha en la pared derecha, solo para luz, con dos montantes."""
    C = D.CLARISTORIO
    m, cr = o.c, o.m["almacen_cristal"]
    xw = D.X1 + D.ONDA["fondo"]
    f = 0.07
    m.caja_de((xw - 0.02, C["y0"] - f, C["z1"]), (xw + 0.05, C["y1"] + f, C["z1"] + f), "marco_ventana")
    m.caja_de((xw - 0.02, C["y0"] - f, C["z0"] - f), (xw + 0.05, C["y1"] + f, C["z0"]), "marco_ventana")
    m.caja_de((xw - 0.02, C["y0"] - f, C["z0"]), (xw + 0.05, C["y0"], C["z1"]), "marco_ventana")
    m.caja_de((xw - 0.02, C["y1"], C["z0"]), (xw + 0.05, C["y1"] + f, C["z1"]), "marco_ventana")
    for k in (1, 2):
        y = C["y0"] + (C["y1"] - C["y0"]) * k / 3
        m.caja_de((xw - 0.02, y - 0.03, C["z0"]), (xw + 0.04, y + 0.03, C["z1"]), "marco_ventana")
    m.extruir([(0, 0), (0.14, -0.04), (0.14, -0.02), (0, 0.02)], Vector((xw - 0.02, C["y0"] - f - 0.04, C["z0"] - f)),
              X, Z, Y * (C["y1"] - C["y0"] + 2 * f + 0.08), "remate")
    cr.caja_de((D.X1 - 0.03, C["y0"], C["z0"]), (D.X1 - 0.015, C["y1"], C["z1"]), "cristal")


# --------------------------------------------------------------------------------------------------------------
# Muelle, rampa, escalones y repisa trasera
# --------------------------------------------------------------------------------------------------------------


def muelle(o):
    m = o.c
    M = D.MUELLE
    m.caja_de((M["x0"], M["y0"], 0.0), (M["x1"], M["y1"] + 0.02, M["z1"]), "hormigon_muelle",
              mats={"-y": "hormigon_zocalo", "-x": "hormigon_zocalo", "+x": "hormigon_zocalo"})
    # angular de protección en el canto delantero y en los costados (franjas de peligro)
    perfil_l(m, Vector((M["x0"] - 0.035, M["y0"] - 0.035, M["z1"] + 0.01)), Y, -Z, X * (M["x1"] - M["x0"] + 0.07),
             0.2, 0.26, 0.035, "angular_franjas")
    for x, s in ((M["x0"], -1), (M["x1"], 1)):
        perfil_l(m, Vector((x + s * 0.035, M["y0"] - 0.035, M["z1"] + 0.01)), Vector((-s, 0, 0)), -Z,
                 Y * (M["y1"] - M["y0"] - 0.02), 0.2, 0.26, 0.035, "angular_franjas")
    # pernos del angular
    x = M["x0"] + 0.3
    while x < M["x1"] - 0.2:
        if not (D.RAMPA["x0"] - 0.1 < x < D.RAMPA["x1"] + 0.1):
            remache(m, Vector((x, M["y0"] - 0.035, M["z1"] - 0.13)), -Y, r=0.03)
        x += 1.6
    # topes de goma para los camiones (a la derecha de la rampa)
    for xt in (3.55, 5.85):
        m.caja(Vector((xt, M["y0"] - 0.06, 0.62)), (0.42, 0.04, 0.5), "metal_desnudo")
        m.caja(Vector((xt, M["y0"] - 0.17, 0.62)), (0.32, 0.2, 0.42), "goma",)
        for dx, dz in ((-0.17, 0.19), (0.17, -0.19)):
            m.cilindro(Vector((xt + dx, M["y0"] - 0.08, 0.62 + dz)), 0.025, 0.04, "remache", lados=5, eje=-Y)
    # canto pintado (franja amarilla) y marcas del suelo del muelle
    W, H = M["x1"] - M["x0"], M["y1"] - M["y0"]
    o.calco(["hormigon_muelle"], Calco("muelle_marcas", ((M["x0"] + M["x1"]) / 2, (M["y0"] + M["y1"]) / 2, M["z1"]),
                                       (1, 0, 0), (0, 1, 0), (W, H), profundidad=0.05, modo="multiplicar", rugosidad=0.8))
    o.calco(["hormigon_muelle"], Calco("muelle_aranazos", ((M["x0"] + M["x1"]) / 2, (M["y0"] + M["y1"]) / 2, M["z1"]),
                                       (1, 0, 0), (0, 1, 0), (W, H), profundidad=0.05, modo="aranazo", rugosidad=0.7))
    o.calco(["hormigon_muelle"], Calco("muelle_manchas", ((M["x0"] + M["x1"]) / 2, (M["y0"] + M["y1"]) / 2, M["z1"]),
                                       (1, 0, 0), (0, 1, 0), (W, H), profundidad=0.05, modo="multiplicar", rugosidad=0.35))
    rampa(o)
    escalones(o)
    repisa_trasera(o)


def rampa(o):
    """Rampa metálica abatible (de chapa lagrimada) del muelle al suelo, con bisagras de nudillos y bordillos."""
    m = o.c
    R, M = D.RAMPA, D.MUELLE
    y_top, z_top = M["y0"], M["z1"] + 0.03
    y_bot, z_bot = R["largo_suelo"], D.S + 0.035
    d = Vector((0, y_bot - y_top, z_bot - z_top))
    L = d.length
    ang = math.atan2(-(z_bot - z_top), -(y_bot - y_top))   # pendiente (hacia abajo al alejarse)
    g = Matrix.Rotation(ang, 3, "X")
    nrm = g @ Z
    t = 0.07
    ancho = R["x1"] - R["x0"]
    centro = Vector(((R["x0"] + R["x1"]) / 2, y_top, z_top)) + d / 2 - nrm * t / 2
    m.caja(centro, (ancho, L, t), "chapa_lagrimada", giro=g)
    # bordillos laterales
    for x in (R["x0"] + 0.04, R["x1"] - 0.04):
        c = Vector((x, y_top, z_top)) + d / 2 + nrm * 0.04
        m.caja(c, (0.08, L - 0.05, 0.1), "angular_franjas", giro=g)
    # largueros por debajo
    for x in (R["x0"] + 0.5, R["x1"] - 0.5):
        c = Vector((x, y_top, z_top)) + d * 0.48 - nrm * (t + 0.06)
        m.caja(c, (0.08, L * 0.9, 0.12), "guia", giro=g)
    # labio biselado en el suelo
    m.extruir([(0, 0), (0.22, 0), (0.0, 0.06)], Vector((R["x0"], y_bot + 0.05, D.S)), -Y, Z, X * ancho, "chapa_lagrimada")
    # bisagra: nudillos alternos (muelle / rampa) y pasador
    n = 5
    for k in range(n):
        xa = R["x0"] + 0.1 + k * (ancho - 0.2) / n
        m.cilindro(Vector((xa + 0.02, y_top - 0.02, z_top + 0.0)), 0.055, (ancho - 0.2) / n - 0.04, "metal_desnudo",
                   lados=6, eje=X)
        if k % 2 == 0:
            m.caja(Vector((xa + (ancho - 0.2) / n / 2, y_top + 0.12, M["z1"] + 0.012)), ((ancho - 0.2) / n - 0.06,
                                                                                          0.22, 0.02), "metal_desnudo")
    m.cilindro(Vector((R["x0"] + 0.06, y_top - 0.02, z_top)), 0.022, ancho - 0.12, "metal_desnudo", lados=6, eje=X)
    o.anclajes["rampa"] = dict(bisagra=[(R["x0"] + R["x1"]) / 2, y_top - 0.02, z_top], angulo_grados=math.degrees(ang))


def escalones(o):
    m = o.c
    E, M = D.ESCALONES, D.MUELLE
    alturas = [0.75, 0.5, 0.25]
    for k, h in enumerate(alturas):
        ya = M["y0"] - 0.3 * (k + 1)
        m.caja_de((E["x0"], ya, 0.0), (E["x1"], M["y0"] + 0.01, h), "hormigon_zocalo",
                  mats={"+z": "hormigon_muelle"})
        # mamperlán de acero con franja
        m.caja_de((E["x0"] + 0.02, ya - 0.025, h - 0.06), (E["x1"] - 0.02, ya + 0.06, h + 0.012), "angular_franjas")
    # barandilla de tubo
    x = E["x0"] + 0.06
    y_ini, y_fin = M["y0"] - 0.9 + 0.12, M["y0"] - 0.05
    pts = [(x, y_ini, 0.25), (x, y_ini, 1.18), (x, y_fin - 0.05, 1.93), (x, y_fin + 0.15, 1.93), (x, y_fin + 0.15, 1.0)]
    m.tubo(tubo_codo(pts, 0.12, 1), 0.035, "barandilla", lados=6)
    m.tubo([(x, (y_ini + y_fin) / 2 - 0.1, 0.62), (x, (y_ini + y_fin) / 2 - 0.1, 1.55)], 0.025, "barandilla", lados=6)
    for p_ in ((x, y_ini, 0.25), (x, y_fin + 0.15, 1.0)):
        m.cilindro(Vector(p_), 0.07, 0.025, "barandilla", lados=6)


def repisa_trasera(o):
    """Repisa de hormigón detrás del portón trasero (descarga de mercancía menor) con su escalera lateral."""
    m = o.c
    R = D.REPISA_TRASERA
    m.caja_de((R["x0"], D.Y1 - 0.02, 0.0), (R["x1"], R["y1"], D.Z_SUELO), "hormigon_muelle",
              mats={"+y": "hormigon_zocalo", "-x": "hormigon_zocalo", "+x": "hormigon_zocalo"})
    perfil_l(m, Vector((R["x0"] - 0.03, R["y1"] + 0.03, D.Z_SUELO + 0.01)), -Y, -Z, X * (R["x1"] - R["x0"] + 0.06),
             0.18, 0.24, 0.03, "angular_franjas")
    for k, h in enumerate((0.67, 0.34)):
        xa = R["x1"] + 0.32 * (k + 1)
        m.caja_de((R["x1"] - 0.01, R["y1"] - 0.9, 0.0), (xa, R["y1"], h), "hormigon_zocalo",
                  mats={"+z": "hormigon_muelle"})
    o.calco(["hormigon_muelle"], Calco("trasera_manchas", ((R["x0"] + R["x1"]) / 2, (D.Y1 + R["y1"]) / 2, D.Z_SUELO),
                                       (1, 0, 0), (0, 1, 0), (R["x1"] - R["x0"], R["y1"] - D.Y1), profundidad=0.05,
                                       modo="multiplicar", rugosidad=0.5))


# --------------------------------------------------------------------------------------------------------------
# Atrezo exterior
# --------------------------------------------------------------------------------------------------------------

YW = D.Y0 - D.ONDA["fondo"]          # cara exterior (crestas) de la fachada principal
SAL = D.ONDA["fondo"]


def bascula(o):
    """Báscula de suelo en el muelle (plataforma de chapa lagrimada) con el visor de pared encima."""
    m, ne = o.c, o.m["almacen_neon"]
    cx, cy, z = -4.3, -3.75, D.Z_SUELO
    a = 1.05
    m.caja(Vector((cx, cy, z + 0.03)), (a, a, 0.06), "chapa_lagrimada")
    for dx, dy, w, d in ((0, -a / 2, a + 0.1, 0.05), (0, a / 2, a + 0.1, 0.05), (-a / 2, 0, 0.05, a), (a / 2, 0, 0.05, a)):
        m.caja(Vector((cx + dx, cy + dy, z + 0.025)), (w, d, 0.05), "angular_franjas")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.caja(Vector((cx + sx * (a / 2 - 0.08), cy + sy * (a / 2 - 0.08), z + 0.065)), (0.1, 0.1, 0.012), "guia")
    # cable de las células de carga al visor
    m.tubo([(cx + 0.3, cy + a / 2, z + 0.02), (cx + 0.3, YW - 0.03, z + 0.02), (cx + 0.3, YW - 0.03, 1.42)],
           0.02, "goma", lados=4)
    # visor (en la pared, bajo la ventana de la oficina)
    zc = 1.55
    m.caja(Vector((cx, YW - 0.07, zc)), (0.4, 0.13, 0.26), "visor")
    m.caja(Vector((cx, YW - 0.015, zc)), (0.3, 0.03, 0.34), "guia")
    ne.caja(Vector((cx - 0.03, YW - 0.137, zc + 0.04)), (0.26, 0.01, 0.085), "pantalla_bascula")
    for k in range(3):
        m.caja(Vector((cx - 0.09 + k * 0.08, YW - 0.14, zc - 0.07)), (0.045, 0.02, 0.03), "boton")
    m.cilindro(Vector((cx + 0.15, YW - 0.135, zc - 0.07)), 0.018, 0.01, "led_verde", lados=6, eje=-Y)
    o.calco(["pantalla_bascula"], Calco("pantalla_bascula", (cx - 0.03, YW - 0.142, zc + 0.04), (1, 0, 0), (0, 0, 1),
                                        (0.26, 0.085), profundidad=0.02, modo="emision", fuerza=1.0))


def extintor(o):
    m = o.c
    cx, base = -2.97, 1.18
    cy = YW - 0.13
    # soporte de pared
    m.caja(Vector((cx, YW - 0.015, base + 0.36)), (0.13, 0.03, 0.42), "guia")
    m.caja(Vector((cx, YW - 0.05, base + 0.52)), (0.05, 0.06, 0.04), "guia")
    perfil = [(0.0, 0.072), (0.025, 0.09), (0.45, 0.09), (0.52, 0.065), (0.56, 0.032)]
    m.cilindro_anillos(Vector((cx, cy, base)), Z, perfil, "extintor_rojo", lados=10)
    m.cilindro(Vector((cx, cy, base + 0.3)), 0.094, 0.035, "guia", lados=10)                 # abrazadera
    # cabeza: válvula, maneta, asa, manómetro, pasador
    m.cilindro(Vector((cx, cy, base + 0.555)), 0.026, 0.06, "laton", lados=6)
    m.caja(Vector((cx, cy, base + 0.635)), (0.08, 0.05, 0.05), "metal_desnudo")
    caja_rot(m, Vector((cx + 0.02, cy, base + 0.68)), (0.16, 0.035, 0.012), "extintor_negro", ang_y=-12)
    caja_rot(m, Vector((cx + 0.01, cy, base + 0.645)), (0.15, 0.035, 0.012), "extintor_negro", ang_y=8)
    m.cilindro(Vector((cx - 0.035, cy - 0.02, base + 0.64)), 0.026, 0.017, "metal_desnudo", lados=6, eje=-Y,
               mat_tapas="manometro")
    # manguera y boquilla sujeta abajo
    pts = [(cx + 0.04, cy, base + 0.62), (cx + 0.1, cy - 0.02, base + 0.6), (cx + 0.11, cy - 0.04, base + 0.4),
           (cx + 0.1, cy - 0.06, base + 0.18), (cx + 0.06, cy - 0.08, base + 0.1)]
    m.tubo(tubo_codo(pts, 0.06, 1), 0.014, "extintor_negro", lados=4)
    m.cilindro(Vector((cx + 0.06, cy - 0.08, base + 0.1)), 0.02, 0.09, "extintor_negro", lados=6,
               eje=Vector((-0.4, -0.3, -1)), radio2=0.012)
    o.calco(["extintor_rojo"], Calco("etiqueta_extintor", (cx, cy - 0.09, base + 0.27), (1, 0, 0), (0, 0, 1),
                                     (0.13, 0.17), profundidad=0.06, modo="pintura", rugosidad=0.5))
    # cartel «EXTINTOR» encima
    m.caja(Vector((cx, YW - 0.012, 2.05)), (0.2, 0.012, 0.2), "cartel_extintor")
    o.calco(["cartel_extintor"], Calco("cartel_extintor", (cx, YW - 0.02, 2.05), (1, 0, 0), (0, 0, 1), (0.2, 0.2),
                                       profundidad=0.02, modo="pintura", rugosidad=0.4))


def cartel_horario(o, aspecto):
    m = o.c
    cx, cz = -1.1, 2.18
    w = 0.46
    h = w / aspecto
    m.caja(Vector((cx, YW - 0.03, cz)), (w, 0.016, h), "cartel_horario")
    for dx in (-w / 2 + 0.035, w / 2 - 0.035):
        for dz in (-h / 2 + 0.035, h / 2 - 0.035):
            m.cilindro(Vector((cx + dx, YW - 0.03, cz + dz)), 0.012, 0.022, "remache", lados=5, eje=-Y)
    m.caja(Vector((cx, YW - 0.012, cz)), (w * 0.7, 0.022, h * 0.6), "guia")   # separadores
    o.calco(["cartel_horario"], Calco("cartel_horario", (cx, YW - 0.04, cz), (1, 0, 0), (0, 0, 1), (w, h),
                                      profundidad=0.02, modo="pintura", rugosidad=0.4))


def foco(o, base, normal_pared, direccion, nombre_ancla, ancho=0.42, alto=0.28):
    """Foco industrial (carcasa con aletas, lente de neón) en un brazo saliendo de la pared."""
    m, ne = o.c, o.m["almacen_neon"]
    base = Vector(base)
    npar = Vector(normal_pared).normalized()
    d = Vector(direccion).normalized()
    # marco: la lente mira a `d`
    up_ref = Z if abs(d.dot(Z)) < 0.95 else Y
    xl = up_ref.cross(d).normalized() * -1
    yl = d.cross(xl).normalized() * -1
    zl = -d
    g = Matrix((xl, yl * -1, zl * -1)).transposed()   # columnas: x local, y local (= d), z local
    g = Matrix((xl, d, xl.cross(d))).transposed()
    m.caja(base + npar * 0.015, (0.16 if abs(npar.x) < 0.5 else 0.03, 0.03 if abs(npar.x) < 0.5 else 0.16, 0.22),
           "foco_carcasa")
    brazo = base + npar * 0.2
    m.tubo([base + npar * 0.02, brazo], 0.03, "foco_carcasa", lados=5)
    c = brazo + npar * 0.06 + d * 0.02
    m.caja(c, (ancho, 0.12, alto), "foco_carcasa", giro=g)
    # aletas de disipación detrás
    for k in range(2):
        dx = (k - 0.5) * ancho / 2.6
        m.caja(c + g @ Vector((dx, -0.09, 0)), (0.018, 0.07, alto * 0.92), "foco_carcasa", giro=g)
    # marco de la lente y lente
    m.caja(c + g @ Vector((0, 0.065, 0)), (ancho * 0.96, 0.012, alto * 0.94), "metal_desnudo", giro=g)
    ne.caja(c + g @ Vector((0, 0.072, 0)), (ancho * 0.84, 0.01, alto * 0.78), "neon_foco", giro=g)
    o.anclajes.setdefault("luces", {})[nombre_ancla] = dict(posicion=list(c + g @ Vector((0, 0.09, 0))),
                                                            direccion=list(d), color=D.NEON)
    return c, g


def focos_muelle(o):
    for x, nombre in ((-0.35, "FocoMuelleIzq"), (3.15, "FocoMuelleDer")):
        foco(o, (x, YW, 5.98), -Y, Vector((0.0, -0.75, -0.66)), nombre)
    # caja de conexiones y tubo entre los dos focos
    m = o.c
    m.caja(Vector((1.4, YW - 0.05, 6.02)), (0.22, 0.1, 0.18), "foco_carcasa")
    m.tubo([(-0.25, YW - 0.04, 6.1), (1.3, YW - 0.04, 6.1)], 0.022, "canalon", lados=6)
    m.tubo([(1.5, YW - 0.04, 6.1), (3.05, YW - 0.04, 6.1)], 0.022, "canalon", lados=6)


def foco_seguridad(o):
    """Foco con detector de movimiento en la esquina trasera izquierda (vigilancia nocturna)."""
    m = o.c
    base = Vector((D.X0 - SAL, D.Y1 - 0.42, 4.12))
    d = Vector((-0.55, 0.55, -0.62)).normalized()
    c, g = foco(o, base, -X, d, "FocoSeguridad", ancho=0.3, alto=0.2)
    # detector (cúpula) debajo, con su LED rojo
    pir = c + g @ Vector((0, 0.0, -0.17))
    m.caja(pir + Vector((0, 0, 0.04)), (0.08, 0.08, 0.05), "foco_carcasa")
    m.cilindro_anillos(pir, -Z, [(0.0, 0.06), (0.03, 0.058), (0.055, 0.04), (0.07, 0.0)], "sensor", lados=10)
    m.cilindro(pir + d * 0.065 + Vector((0, 0, 0.02)), 0.009, 0.012, "led_rojo", lados=6, eje=d)
    o.anclajes["luces"]["FocoSeguridad"]["sensor"] = list(pir)


def contador(o):
    """Medidor de energía en la pared derecha: caja con mirilla, pantallita de neón y tubo de acometida."""
    m, ne, cr = o.c, o.m["almacen_neon"], o.m["almacen_cristal"]
    x = D.X1 + SAL
    y, z = -1.0, 2.0
    m.caja(Vector((x + 0.07, y, z)), (0.14, 0.42, 0.56), "contador")
    m.caja(Vector((x + 0.145, y, z)), (0.012, 0.38, 0.52), "contador")       # puerta
    m.caja(Vector((x + 0.15, y + 0.15, z - 0.05)), (0.02, 0.025, 0.1), "metal_desnudo")   # cierre
    for dz in (-0.18, 0.18):
        m.caja(Vector((x + 0.148, y - 0.2, z + dz)), (0.02, 0.02, 0.07), "metal_desnudo")  # bisagras
    # mirilla con la pantalla detrás
    m.caja(Vector((x + 0.153, y - 0.02, z + 0.11)), (0.008, 0.24, 0.14), "goma")
    ne.caja(Vector((x + 0.15, y - 0.04, z + 0.11)), (0.006, 0.15, 0.055), "pantalla_contador")
    cr.caja(Vector((x + 0.159, y - 0.02, z + 0.11)), (0.006, 0.2, 0.1), "cristal_limpio")
    m.cilindro(Vector((x + 0.15, y + 0.08, z + 0.11)), 0.01, 0.012, "led_rojo", lados=6, eje=X)
    # precinto y tubo de acometida (sube al alero y baja al zócalo)
    m.tubo([(x + 0.05, y, z + 0.28), (x + 0.05, y, 4.3)], 0.03, "canalon", lados=6)
    m.tubo([(x + 0.05, y + 0.1, z - 0.28), (x + 0.05, y + 0.1, D.Z_ZOCALO)], 0.03, "canalon", lados=6)
    for zz in (2.9, 3.7, 1.2):
        m.caja(Vector((x + 0.03, y + (0.1 if zz < 2 else 0), zz)), (0.06, 0.1, 0.035), "remate")
    o.calco(["pantalla_contador"], Calco("pantalla_contador", (x + 0.154, y - 0.04, z + 0.11), (0, 1, 0), (0, 0, 1),
                                         (0.15, 0.055), profundidad=0.02, modo="emision", fuerza=1.0))
    o.calco(["contador"], Calco("aviso_electrico", (x + 0.152, y - 0.02, z - 0.13), (0, 1, 0), (0, 0, 1),
                                (0.18, 0.16), profundidad=0.02, modo="pintura", rugosidad=0.45))
    o.anclajes["contador"] = [x, y, z]


def grifo(o):
    """Grifo industrial en la pared derecha y la manguera enrollada en su soporte."""
    m = o.c
    x = D.X1 + SAL
    y = 4.15
    # tubería de alimentación (galvanizada) que sale del zócalo
    pts = [(x + 0.06, y, D.Z_ZOCALO), (x + 0.06, y, 1.02), (x + 0.2, y, 1.02)]
    m.tubo(tubo_codo(pts, 0.06, 2), 0.035, "poste_galv", lados=6)
    for zz in (0.62, 0.9):
        m.caja(Vector((x + 0.03, y, zz)), (0.06, 0.1, 0.04), "remate")
    # cuerpo de la válvula, maneta roja de cuarto de vuelta, caño y racor
    m.cilindro(Vector((x + 0.18, y, 0.96)), 0.05, 0.13, "laton", lados=6)
    m.cilindro(Vector((x + 0.18, y, 1.09)), 0.015, 0.03, "laton", lados=6)
    caja_rot(m, Vector((x + 0.24, y + 0.02, 1.12)), (0.17, 0.035, 0.018), "maneta_roja", ang_z=20)
    m.cilindro(Vector((x + 0.25, y, 0.96)), 0.026, 0.11, "laton", lados=6, eje=Vector((0.5, 0, -1)))
    m.cilindro(Vector((x + 0.3, y, 0.86)), 0.035, 0.06, "laton", lados=6, eje=-Z)
    # soporte de la manguera (gancho de pared) y la manguera enrollada
    ys, zs = 3.0, 1.62
    m.caja(Vector((x + 0.015, ys, zs)), (0.03, 0.3, 0.34), "guia")
    for dy in (-0.09, 0.09):
        m.caja(Vector((x + 0.2, ys + dy, zs - 0.02)), (0.36, 0.035, 0.04), "guia")
        m.caja(Vector((x + 0.37, ys + dy, zs + 0.03)), (0.03, 0.035, 0.1), "guia")
    rc, vueltas = 0.21, 2.5
    pts = []
    pasos = int(8 * vueltas)
    for k in range(pasos + 1):
        t = k / pasos
        a = math.tau * vueltas * t
        pts.append(Vector((x + 0.08 + 0.26 * t, ys + math.cos(a) * rc * (1 + 0.04 * math.sin(k)),
                           zs - rc + 0.02 + math.sin(a) * rc)))
    m.tubo(pts, 0.03, "manguera", lados=4, tapas=True)
    # tramo de manguera del caño a la madeja
    cuelga = [(x + 0.3, y, 0.83), (x + 0.32, y - 0.15, 0.6), (x + 0.36, y - 0.6, 0.55), (x + 0.36, 3.45, 0.75),
              pts[-1]]
    m.tubo(tubo_codo(cuelga, 0.2, 2), 0.03, "manguera", lados=4)
    o.anclajes["grifo"] = [x + 0.3, y, 0.86]


def senal(o, aspecto):
    m = o.c
    x, y = -7.75, -6.75
    m.cilindro(Vector((x, y, 0.0)), 0.18, D.S + 0.08, "hormigon_zocalo", lados=10)
    m.cilindro(Vector((x, y, 0.1)), 0.045, 2.5, "poste_galv", lados=8)
    m.cilindro(Vector((x, y, 2.6)), 0.05, 0.03, "poste_galv", lados=8)
    w = 1.12
    h = w / aspecto
    zc = 2.2
    m.caja(Vector((x + 0.25, y - 0.08, zc)), (w, 0.025, h), "poste_galv", mats={"-y": "senal"})
    for dz in (-h / 4, h / 4):
        m.caja(Vector((x, y - 0.04, zc + dz)), (0.14, 0.05, 0.05), "metal_desnudo")
    o.calco(["senal"], Calco("senal_zona_carga", (x + 0.25, y - 0.095, zc), (1, 0, 0), (0, 0, 1), (w, h),
                             profundidad=0.02, modo="pintura", rugosidad=0.35))


def contenedor(o, base, giro_z, abierto, mat, rotulos, tapado=False):
    """
    Contenedor de suministros (1,2 x 1,8 x 1,1): marco de acero con cantoneras, paneles nervados, cáncamos de izado
    en las esquinas de arriba. `abierto`: la tapa abierta (bisagra en el lado de la pared) apoyada hacia atrás.
    """
    t = Malla("tmp")
    W, L, H = 1.2, 1.8, 1.1
    hw, hl = W / 2, L / 2
    mm = "contenedor_marco"
    for sx in (-1, 1):
        for sy in (-1, 1):
            t.caja(Vector((sx * (hw - 0.05), sy * (hl - 0.05), H / 2)), (0.1, 0.1, H), mm)
            for z in ((0.06,) if tapado else (0.06, H - 0.06)):
                t.caja(Vector((sx * (hw - 0.065), sy * (hl - 0.065), z)), (0.14, 0.14, 0.13), "contenedor_canto")
    for z in (0.04, H - 0.04):
        for sx in (-1, 1):
            t.caja(Vector((sx * (hw - 0.04), 0, z)), (0.08, L - 0.2, 0.08), mm)
        for sy in (-1, 1):
            t.caja(Vector((0, sy * (hl - 0.04), z)), (W - 0.2, 0.08, 0.08), mm)
    # paneles nervados
    for sx in (-1, 1):
        t.caja(Vector((sx * (hw - 0.03), 0, H / 2)), (0.025, L - 0.2, H - 0.16), mat)
        for k in range(2):
            y = -hl + 0.6 + k * (L - 1.2)
            t.caja(Vector((sx * (hw - 0.012), y, H / 2)), (0.03, 0.07, H - 0.16), mat)
    for sy in (-1, 1):
        t.caja(Vector((0, sy * (hl - 0.03), H / 2)), (W - 0.2, 0.025, H - 0.16), mat)
        for k in range(1):
            x = 0.0
            t.caja(Vector((x, sy * (hl - 0.012), H / 2)), (0.07, 0.03, H - 0.16), mat)
    t.caja(Vector((0, 0, 0.07)), (W - 0.12, L - 0.12, 0.04), "contenedor_interior")
    # cáncamos de izado (asas en D) en las cuatro esquinas de arriba
    for sx in ((-1, 1) if not tapado else ()):
        for sy in (-1, 1):
            c = Vector((sx * (hw - 0.2), sy * (hl - 0.065), H + 0.005))
            t.caja(c, (0.12, 0.06, 0.02), mm)
            arco = [c + Vector((math.cos(math.pi * k / 3) * 0.05, 0, 0.01 + math.sin(math.pi * k / 3) * 0.06))
                    for k in range(4)]
            t.tubo(arco, 0.013, "metal_desnudo", lados=4)
    if abierto:
        # interior: viruta de embalaje y dos cajas que quedaron
        t.caja(Vector((0, 0.1, 0.2)), (W - 0.2, L - 0.5, 0.2), "paja")
        caja_rot(t, Vector((-0.2, -0.45, 0.42)), (0.4, 0.35, 0.3), "carton", ang_z=12)
        caja_rot(t, Vector((0.22, 0.35, 0.38)), (0.3, 0.3, 0.22), "carton_oscuro", ang_z=-20)
        # tapa abierta 100° (bisagra en +x, arriba)
        tapa = Malla("tapa")
        tapa.caja(Vector((0, 0, 0.03)), (W, L, 0.04), mat, mats={"-z": "contenedor_interior"})
        tapa.caja(Vector((0, 0, -0.01)), (W - 0.04, L - 0.04, 0.04), "contenedor_interior")
        for k in range(2):
            tapa.caja(Vector((0, -hl + 0.5 + k * (L - 1.0), 0.065)), (W - 0.1, 0.06, 0.03), mat)
        mt = Matrix.Translation((hw, 0, H)) @ Matrix.Rotation(math.radians(100), 4, "Y") @ \
            Matrix.Translation((-hw, 0, 0))
        t.unir(tapa, mt)
        for sy in (-1, 1):
            t.cilindro(Vector((hw - 0.02, sy * 0.55, H + 0.02)), 0.025, 0.18, "metal_desnudo", lados=5, eje=Y)
        # cadena de retención de la tapa
        p0 = Vector((hw - 0.06, -hl + 0.12, H - 0.15))
        p1 = mt @ Vector((-hw + 0.25, -hl + 0.12, 0.0))
        t.tubo([p0, (p0 + p1) / 2 + Vector((0.05, 0, -0.1)), p1], 0.012, "correa", lados=3)
    else:
        t.caja(Vector((0, 0, H - 0.02)), (W - 0.1, L - 0.1, 0.04), mat)
        for k in range(2):
            t.caja(Vector((0, -hl + 0.5 + k * (L - 1.0), H + 0.005)), (W - 0.2, 0.06, 0.03), mat)
    mtx = Matrix.Translation(base) @ Matrix.Rotation(math.radians(giro_z), 4, "Z")
    o.c.unir(t, mtx)
    # rótulos (en coordenadas del mundo): (imagen, cara '-x'|'-y', centro_local (u, z), tam, modo)
    for img, cara, (u, zz), tam, modo in rotulos:
        if cara == "-x":
            org = mtx @ Vector((-hw - 0.012, u, zz))
            U = (mtx.to_3x3() @ Vector((0, -1, 0)))
        else:
            org = mtx @ Vector((u, -hl - 0.012, zz))
            U = (mtx.to_3x3() @ Vector((1, 0, 0)))
        o.calco([mat], Calco(img, tuple(org), tuple(U), (0, 0, 1), tam, profundidad=0.06, modo=modo,
                             rugosidad=0.5, desgaste=0.25 if modo == "pintura" else 0.0))


def contenedores(o, aspecto_sector7, aspecto_id):
    x = D.X0 - 1.32
    hs = 0.5
    contenedor(o, Vector((x, 0.55, D.S)), 0.0, False, "contenedor_naranja",
               [("rotulo_sector7", "-x", (0.0, 0.62), (1.3, 1.3 / aspecto_sector7), "pintura"),
                ("etiqueta_envio", "-y", (0.28, 0.6), (0.24, 0.3), "pintura"),
                ("rotulo_id_inf", "-y", (-0.15, 0.85), (0.5, 0.5 / aspecto_id), "pintura")], tapado=True)
    contenedor(o, Vector((x + 0.04, 0.5, D.S + 1.1 + 0.005)), 4.0, True, "contenedor_azul",
               [("etiqueta_fragil", "-x", (-0.35, 0.55), (0.6, 0.4), "pintura"),
                ("rotulo_sector7", "-x", (0.45, 0.62), (0.75, 0.75 / aspecto_sector7), "pintura"),
                ("etiqueta_envio", "-y", (-0.25, 0.6), (0.24, 0.3), "pintura"),
                ("rotulo_id_sup", "-y", (0.2, 0.85), (0.5, 0.5 / aspecto_id), "pintura")])


def bidon(m, base, mat, inclinacion=0.0, giro=0.0):
    perfil = [(0.0, 0.265), (0.025, 0.288), (0.275, 0.288), (0.285, 0.299), (0.565, 0.299), (0.575, 0.288),
              (0.83, 0.288), (0.85, 0.272), (0.84, 0.25)]
    t = Malla("b")
    t.cilindro_anillos(Vector((0, 0, 0)), Z, perfil, mat, lados=10)
    t.cilindro(Vector((0.12, 0.05, 0.83)), 0.035, 0.03, "metal_desnudo", lados=6)
    mtx = Matrix.Translation(base) @ Matrix.Rotation(math.radians(giro), 4, "Z") @ \
        Matrix.Rotation(math.radians(inclinacion), 4, "X")
    m.unir(t, mtx)
    return mtx


def bidones(o):
    m = o.c
    x, y = D.X0 - 0.75, 3.5
    bidon(m, Vector((x, y, D.S)), "bidon_azul", giro=10)
    bidon(m, Vector((x + 0.03, y - 0.02, D.S + 0.85)), "bidon_gris", inclinacion=2.0, giro=-25)
    o.calco(["bidon_azul"], Calco("tiza_vacio", (x - 0.29, y, D.S + 0.42), (0, -1, 0), (0, 0, 1), (0.42, 0.17),
                                  profundidad=0.3, modo="pintura", rugosidad=0.9))
    o.calco(["bidon_gris"], Calco("tiza_vacio", (x - 0.26, y - 0.02, D.S + 1.3), (0, -1, 0), (0, 0, 1), (0.36, 0.15),
                                  profundidad=0.3, modo="pintura", rugosidad=0.9, fuerza=0.8))


def palet(o):
    """Palé de madera vacío, gastado, con una tabla rota y clavos a la vista."""
    t = Malla("p")
    L, W = 1.1, 0.75
    for k, y in enumerate((-0.31, -0.155, 0.0, 0.155, 0.31)):
        largo = L if k != 3 else L * 0.7
        xc = 0 if k != 3 else -L * 0.15
        t.caja(Vector((xc, y, 0.12)), (largo, 0.12 if k in (0, 2, 4) else 0.09, 0.022), "madera_palet")
        if k == 3:   # el trozo partido, suelto y torcido
            caja_rot(t, Vector((L * 0.42, y + 0.02, 0.118)), (0.2, 0.085, 0.02), "madera_palet_oscura", ang_z=9,
                     ang_y=4)
        for xb in (-L / 2 + 0.07, 0.0, L / 2 - 0.07):
            if k == 3 and xb > L * 0.1:
                continue
            if k in (0, 2, 4) and xb != 0.0 or (k == 1 and xb == 0.0):
                t.cilindro(Vector((xb + 0.02, y, 0.127)), 0.012, 0.008, "clavo", lados=4)
    for x in (-L / 2 + 0.07, 0.0, L / 2 - 0.07):
        t.caja(Vector((x, 0, 0.098)), (0.1, W, 0.022), "madera_palet_y")
        for y in (-W / 2 + 0.06, 0.0, W / 2 - 0.06):
            t.caja(Vector((x, y, 0.053)), (0.12, 0.1 if y else 0.14, 0.068), "madera_palet_oscura")
    for y in (-W / 2 + 0.06, 0.0, W / 2 - 0.06):
        t.caja(Vector((0, y, 0.0095)), (L, 0.1, 0.019), "madera_palet")
    mtx = Matrix.Translation((5.15, -3.55, D.Z_SUELO)) @ Matrix.Rotation(math.radians(7), 4, "Z")
    o.c.unir(t, mtx)


def transpaleta(o):
    """Transpaleta manual aparcada en el muelle con las horquillas bajadas hacia la pared."""
    t = Malla("t")
    for sx in (-1, 1):
        x = sx * 0.2
        t.caja(Vector((x, 0.42, 0.045)), (0.16, 1.0, 0.07), "transpaleta_horquilla", mats={"+z": "transpaleta_horquilla"})
        t.extruir([(0, 0), (0.16, 0), (0.0, 0.07)], Vector((x - 0.08, 0.92, 0.01)), Y, Z, X * 0.16,
                  "transpaleta_horquilla")
    t.caja(Vector((0, -0.18, 0.12)), (0.56, 0.24, 0.17), "transpaleta")
    t.caja(Vector((0, -0.05, 0.08)), (0.56, 0.06, 0.1), "transpaleta")
    t.cilindro(Vector((0, -0.25, 0.2)), 0.07, 0.25, "transpaleta", lados=8)
    t.cilindro(Vector((0, -0.25, 0.45)), 0.035, 0.08, "metal_pulido", lados=6)
    t.caja(Vector((0, -0.25, 0.53)), (0.16, 0.1, 0.06), "transpaleta")
    for sx in (-1, 1):
        t.cilindro(Vector((sx * 0.13 - 0.03, -0.3, 0.09)), 0.09, 0.06, "goma", lados=8, eje=X)
        t.cilindro(Vector((sx * 0.13 - 0.01, -0.3, 0.09)), 0.04, 0.02, "metal_desnudo", lados=6, eje=X)
    t.caja(Vector((0, -0.3, 0.17)), (0.2, 0.1, 0.06), "transpaleta")
    # timón con el lazo de agarre y la palanca de mando
    pts = [(0, -0.26, 0.53), (0, -0.5, 1.1), (-0.13, -0.55, 1.18), (-0.13, -0.6, 1.36), (0.13, -0.6, 1.36),
           (0.13, -0.55, 1.18), (0.01, -0.5, 1.11)]
    t.tubo(tubo_codo(pts, 0.05, 1), 0.025, "transpaleta", lados=5)
    t.caja(Vector((0.0, -0.585, 1.33)), (0.08, 0.03, 0.03), "goma")
    caja_rot(t, Vector((0.07, -0.57, 1.27)), (0.012, 0.012, 0.09), "metal_desnudo", ang_x=-25)
    mtx = Matrix.Translation((3.95, -3.45, D.Z_SUELO)) @ Matrix.Rotation(math.radians(-8), 4, "Z")
    o.c.unir(t, mtx)
    o.anclajes["transpaleta"] = list(mtx.translation)


# --------------------------------------------------------------------------------------------------------------
# Interior: oficina (se ve por la ventana) y nave (por los portones y los tragaluces)
# --------------------------------------------------------------------------------------------------------------


def interior(o):
    m = o.c
    xi0 = D.X0 + D.GROSOR_MURO
    yi0 = D.Y0 + D.GROSOR_MURO
    xo1, yo1 = -1.1, 0.45
    zt = 3.5
    # tabiques de la oficina (con un hueco de paso a la nave)
    m.caja_de((xi0, yo1 - 0.1, D.Z_SUELO), (-2.3, yo1, zt), "pared_oficina")
    m.caja_de((-1.4, yo1 - 0.1, D.Z_SUELO), (xo1, yo1, zt), "pared_oficina")
    m.caja_de((-2.3, yo1 - 0.1, 3.0), (-1.4, yo1, zt), "pared_oficina")
    m.caja_de((xo1 - 0.1, yi0, D.Z_SUELO), (xo1, yo1, zt), "pared_oficina")
    m.caja_de((xi0, yi0, zt), (xo1, yo1, zt + 0.08), "pared_oficina")
    m.caja_de((xi0, yi0, D.Z_SUELO), (xo1 - 0.1, yo1 - 0.1, D.Z_SUELO + 0.012), "linoleo")
    # pantalla fluorescente
    m.caja(Vector((-4.3, -1.0, zt - 0.04)), (0.95, 0.24, 0.06), "lampara_metal", mats={"-z": "luz_fluorescente"})
    o.anclajes["LuzOficina"] = [-4.3, -1.0, zt - 0.1]
    # mesa bajo la ventana
    zm = D.Z_SUELO + 0.72
    m.caja_de((-5.15, yi0 + 0.02, zm), (-3.45, yi0 + 0.68, zm + 0.045), "mesa")
    m.caja_de((-5.12, yi0 + 0.05, D.Z_SUELO), (-5.08, yi0 + 0.65, zm), "mesa_metal")
    m.caja_de((-3.9, yi0 + 0.05, D.Z_SUELO), (-3.48, yi0 + 0.65, zm), "mesa_metal")
    for k in range(3):
        z = D.Z_SUELO + 0.1 + k * 0.21
        m.caja_de((-3.87, yi0 + 0.65, z), (-3.51, yi0 + 0.67, z + 0.19), "mesa_metal")
        m.caja(Vector((-3.69, yi0 + 0.685, z + 0.15)), (0.12, 0.015, 0.02), "metal_desnudo")
    # papeles, libro de registro abierto, carpeta con pinza, taza, bolígrafo
    for (x, y, a, h) in ((-4.85, yi0 + 0.3, 8, 0.035), (-4.55, yi0 + 0.42, -14, 0.012), (-3.75, yi0 + 0.25, 25, 0.02)):
        caja_rot(m, Vector((x, y, zm + 0.045 + h / 2)), (0.21, 0.3, h), "papel", ang_z=a)
    caja_rot(m, Vector((-4.55, yi0 + 0.42, zm + 0.058)), (0.21, 0.3, 0.002), "papel_escrito", ang_z=-14)
    for s in (-1, 1):
        caja_rot(m, Vector((-4.2 + s * 0.105, yi0 + 0.3, zm + 0.056 + 0.006)), (0.2, 0.28, 0.014),
                 "libro_hojas", ang_y=-s * 4)
    m.caja(Vector((-4.2, yi0 + 0.3, zm + 0.05)), (0.43, 0.3, 0.008), "libro_tapa")
    m.cilindro(Vector((-3.72, yi0 + 0.55, zm + 0.045)), 0.042, 0.1, "taza", lados=8)
    m.tubo([(-3.68, yi0 + 0.55, zm + 0.12), (-3.64, yi0 + 0.55, zm + 0.11), (-3.64, yi0 + 0.55, zm + 0.07),
            (-3.68, yi0 + 0.55, zm + 0.06)], 0.008, "taza", lados=4)
    # lámpara de escritorio articulada, encendida
    xb, yb = -5.0, yi0 + 0.18
    m.cilindro(Vector((xb, yb, zm + 0.045)), 0.08, 0.025, "lampara", lados=8)
    codo = Vector((xb + 0.06, yb + 0.12, zm + 0.36))
    cab = Vector((xb + 0.27, yb + 0.18, zm + 0.42))
    m.tubo([(xb, yb, zm + 0.07), codo], 0.012, "lampara", lados=5)
    m.tubo([codo, cab], 0.012, "lampara", lados=5)
    m.cilindro(codo - Vector((0.025, 0, 0)), 0.022, 0.05, "lampara", lados=6, eje=X)
    dlam = Vector((0.35, 0.05, -1)).normalized()
    m.cilindro(cab, 0.03, 0.13, "lampara", lados=8, eje=dlam, radio2=0.085)
    m.cilindro(cab + dlam * 0.125, 0.075, 0.004, "luz_lampara", lados=8, eje=dlam)
    o.anclajes["LuzLampara"] = list(cab + dlam * 0.15)
    # silla
    sx, sy = -4.4, yi0 + 1.05
    m.caja(Vector((sx, sy, D.Z_SUELO + 0.47)), (0.42, 0.42, 0.07), "silla")
    caja_rot(m, Vector((sx, sy + 0.24, D.Z_SUELO + 0.78)), (0.4, 0.05, 0.42), "silla", ang_x=-8)
    m.cilindro(Vector((sx, sy, D.Z_SUELO + 0.08)), 0.025, 0.36, "metal_pulido", lados=6)
    for k in range(5):
        caja_rot(m, Vector((sx + 0.15 * math.cos(k * 1.2566), sy + 0.15 * math.sin(k * 1.2566), D.Z_SUELO + 0.07)),
                 (0.3, 0.04, 0.03), "extintor_negro", ang_z=math.degrees(k * 1.2566))
    # estantería metálica de 3 niveles con cajas (contra el tabique del fondo: se ve por la ventana)
    ex0, ex1, ey0, ey1 = -5.8, -4.3, yo1 - 0.48, yo1 - 0.1
    for x in (ex0, ex1 - 0.04):
        for y in (ey0, ey1 - 0.04):
            perfil_l(m, Vector((x, y, D.Z_SUELO)), X, Y, Z * 1.85, 0.04, 0.04, 0.008, "estanteria")
    niveles = (D.Z_SUELO + 0.15, D.Z_SUELO + 0.8, D.Z_SUELO + 1.45)
    for z in niveles:
        m.caja_de((ex0, ey0, z), (ex1, ey1, z + 0.03), "estanteria")
    cajas = [
        [(-5.5, 0.48, 0.34, 0.34, "carton", 3), (-4.9, 0.36, 0.3, 0.26, "carton_oscuro", -6), (-4.5, 0.25, 0.3, 0.2, "carton", 10)],
        [(-5.45, 0.55, 0.33, 0.3, "carton_oscuro", -3), (-4.75, 0.6, 0.3, 0.36, "carton", 4)],
        [(-5.55, 0.36, 0.3, 0.24, "carton", 8), (-5.05, 0.45, 0.32, 0.3, "carton", -4), (-4.55, 0.3, 0.28, 0.18, "carton_oscuro", 0)],
    ]
    for z, fila in zip(niveles, cajas):
        for x, w, d, h, mt, a in fila:
            caja_rot(m, Vector((x, (ey0 + ey1) / 2, z + 0.03 + h / 2)), (w, d, h), mt, ang_z=a)
    # archivadores en el nivel del medio
    for k in range(4):
        m.caja(Vector((-5.2 + k * 0.065 + 0.6, ey0 + 0.17, niveles[1] + 0.18)), (0.055, 0.28, 0.3),
               ["archivador_azul", "archivador_rojo", "archivador_azul", "archivador_verde", "archivador_azul"][k])
    # tablón de corcho con papeles en el tabique
    m.caja(Vector((xo1 - 0.115, -0.9, 2.25)), (0.02, 0.7, 0.5), "corcho")
    for k, (dy, dz, a) in enumerate(((-0.15, 0.06, 4), (0.15, -0.04, -6))):
        caja_rot(m, Vector((xo1 - 0.128, -0.9 + dy, 2.25 + dz)), (0.004, 0.15, 0.2), "papel_escrito", ang_x=a)

    # nave: estanterías de palés contra la pared del fondo, con mercancía
    yr0, yr1 = 3.75, D.Y1 - D.GROSOR_MURO - 0.08
    xs = (0.2, 3.0, 5.8)
    for x in xs:
        for y in (yr0, yr1 - 0.08):
            m.caja_de((x, y, D.Z_SUELO), (x + 0.08, y + 0.08, D.Z_SUELO + 3.1), "rack_azul")
        caja_rot(m, Vector((x + 0.04, (yr0 + yr1) / 2, D.Z_SUELO + 1.3)), (0.03, yr1 - yr0 - 0.1, 0.03), "rack_azul",
                 ang_x=55)
    for xa, xb in zip(xs, xs[1:]):
        for z in (D.Z_SUELO + 1.2, D.Z_SUELO + 2.3):
            for y in (yr0, yr1 - 0.06):
                m.caja_de((xa + 0.08, y, z - 0.12), (xb, y + 0.06, z), "rack_naranja")
    cargas = [(1.6, D.Z_SUELO, 0.62, "carton"), (4.4, D.Z_SUELO, 0.5, "saco"), (1.6, D.Z_SUELO + 1.2, 0.7, "carton_oscuro"),
              (4.4, D.Z_SUELO + 1.2, 0.55, "carton"), (4.4, D.Z_SUELO + 2.3, 0.6, "film")]
    for x, z, h, mt in cargas:
        m.caja(Vector((x, (yr0 + yr1) / 2, z + 0.065)), (1.1, 0.8, 0.13), "madera_palet_oscura")
        caja_rot(m, Vector((x, (yr0 + yr1) / 2, z + 0.13 + h / 2)), (1.0, 0.72, h), mt, ang_z=rnd.uniform(-3, 3))
    # carga suelta en el suelo de la nave
    m.caja(Vector((1.9, 1.3, D.Z_SUELO + 0.065)), (1.1, 0.8, 0.13), "madera_palet_oscura")
    caja_rot(m, Vector((1.9, 1.3, D.Z_SUELO + 0.43)), (0.95, 0.7, 0.6), "film", ang_z=4)
    caja_rot(m, Vector((-0.2, 2.6, D.Z_SUELO + 0.3)), (0.7, 0.6, 0.6), "caja_madera", ang_z=-12)
    caja_rot(m, Vector((4.6, 0.6, D.Z_SUELO + 0.2)), (0.5, 0.4, 0.4), "carton", ang_z=20)
    # lámparas colgantes de la nave
    for x, y in ((0.8, 1.6), (4.0, 1.6)):
        ztop = D.z_arco(x)
        m.cilindro(Vector((x, y, 4.6)), 0.01, ztop - 4.6, "metal_desnudo", lados=4)
        m.cilindro(Vector((x, y, 4.35)), 0.3, 0.25, "lampara_metal", lados=8, radio2=0.06,
                   mat_tapas="luz_fluorescente")
    o.calco(["suelo_interior"], Calco("suelo_marcas", (2.6, 1.25, D.Z_SUELO), (1, 0, 0), (0, 1, 0), (7.4, 7.06),
                                      profundidad=0.05, modo="pintura", rugosidad=0.5))


# --------------------------------------------------------------------------------------------------------------
# Rótulos de las paredes, del suelo y de las persianas
# --------------------------------------------------------------------------------------------------------------

CHAPAS = ["chapa_gris", "chapa_clara", "chapa_oscura", "chapa_verdosa"]


def rotulos(o, asp):
    # SECTOR 7-B grande en la pared derecha (amarillo industrial)
    w = 4.6
    o.calco(CHAPAS, Calco("rotulo_sector7b", (D.X1, 2.0, 2.78), (0, 1, 0), (0, 0, 1), (w, w / asp["rotulo_sector7b"]),
                          profundidad=0.14, modo="pintura", rugosidad=0.5))
    # números de lote (blanco, plantilla)
    o.calco(CHAPAS, Calco("rotulo_7b", (5.0, D.Y0, 3.25), (1, 0, 0), (0, 0, 1), (1.6, 1.6 / asp["rotulo_7b"]),
                          profundidad=0.14, modo="pintura", rugosidad=0.5))
    o.calco(CHAPAS, Calco("rotulo_lote114", (5.0, D.Y0, 2.4), (1, 0, 0), (0, 0, 1), (1.7, 1.7 / asp["rotulo_lote114"]),
                          profundidad=0.14, modo="pintura", rugosidad=0.5))
    o.calco(CHAPAS, Calco("rotulo_lote209", (-4.6, D.Y1, 2.9), (-1, 0, 0), (0, 0, 1), (2.2, 2.2 / asp["rotulo_lote209"]),
                          profundidad=0.14, modo="pintura", rugosidad=0.5))
    o.calco(CHAPAS, Calco("rotulo_lote031", (D.X0, 1.9, 3.4), (0, -1, 0), (0, 0, 1), (2.4, 2.4 / asp["rotulo_lote031"]),
                          profundidad=0.14, modo="pintura", rugosidad=0.5))
    # persianas: número de muelle
    P = D.PORTON
    yc = o.anclajes["porton"]["pivote"][1] - 0.06
    o.calco(["persiana", "persiana_nueva", "persiana_oscura"],
            Calco("rotulo_muelle1", ((P["x0"] + P["x1"]) / 2, yc, 3.45), (1, 0, 0), (0, 0, 1),
                  (2.4, 2.4 / asp["rotulo_muelle1"]), profundidad=0.12, modo="pintura", rugosidad=0.5))
    T = D.PORTON_TRASERO
    yt = o.anclajes["porton_trasero"]["pivote"][1] + 0.06
    o.calco(["persiana_trasera", "persiana_oxido", "persiana_trasera_clara"],
            Calco("rotulo_muelle2", ((T["x0"] + T["x1"]) / 2, yt, 3.0), (-1, 0, 0), (0, 0, 1),
                  (1.8, 1.8 / asp["rotulo_muelle2"]), profundidad=0.12, modo="pintura", rugosidad=0.5, desgaste=0.45))
    # explanada: rodadas, charco del hundido, manchas
    E = D.EXPLANADA
    cx, cy, w, h = (E["x0"] + E["x1"]) / 2, (E["y0"] + D.MUELLE["y0"]) / 2, E["x1"] - E["x0"], D.MUELLE["y0"] - E["y0"]
    for img, modo, r in (("explanada_rodadas", "multiplicar", 0.85), ("explanada_charco", "brillo", 0.55),
                         ("explanada_manchas", "multiplicar", 0.4)):
        o.calco(["hormigon_explanada"], Calco(img, (cx, cy, D.S), (1, 0, 0), (0, 1, 0), (w, h), profundidad=0.2,
                                              modo=modo, rugosidad=r))
    o.calco(["hormigon_explanada"], Calco("explanada_aranazos", (cx, cy, D.S), (1, 0, 0), (0, 1, 0), (w, h),
                                          profundidad=0.2, modo="aranazo", rugosidad=0.8, fuerza=0.35))
    o.calco(["chapa_lagrimada"], Calco("rampa_rodadas", ((D.RAMPA["x0"] + D.RAMPA["x1"]) / 2, -5.6, 0.5), (1, 0, 0),
                                       (0, 1, 0), (D.RAMPA["x1"] - D.RAMPA["x0"], 2.4), profundidad=1.0,
                                       modo="multiplicar", rugosidad=0.7))


def construir(asp):
    """asp: {imagen: ancho/alto} de las imágenes de los rótulos (ya generadas)."""
    o = Obra()
    estructura(o)
    porton_principal(o)
    porton_trasero(o)
    puerta(o)
    V = D.VENTANA_OFICINA
    ventana(o, V["x0"], V["x1"], V["z0"], V["z1"])
    claristorio(o)
    muelle(o)
    bascula(o)
    extintor(o)
    cartel_horario(o, asp["cartel_horario"])
    focos_muelle(o)
    foco_seguridad(o)
    contador(o)
    grifo(o)
    senal(o, asp["senal_zona_carga"])
    contenedores(o, asp["rotulo_sector7"], asp["rotulo_id_inf"])
    bidones(o)
    palet(o)
    transpaleta(o)
    interior(o)
    rotulos(o, asp)
    return o
