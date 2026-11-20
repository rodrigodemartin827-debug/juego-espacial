"""
Coloca todo el detalle «duro» del Dragón Leviatán sobre las piezas del cuerpo, y construye las membranas de las
alas y las dos piezas que no tienen cuerpo propio (Cresta_Dorsal y Cornamenta).

detalles(fino) -> {pieza: Malla}

Reglas:
  * Lo que va dentro de la misma pieza (dientes en la encía, garras en los dedos) se hunde en la carne.
  * Lo que está en una pieza y se apoya en OTRA (cuernos sobre el cráneo, cresta sobre el lomo, membrana junto al
    torso, cadenas que cuelgan delante del pecho) se asienta o se aparta con `asentar` / `despegar` para que no la
    atraviese: queda a 0,02-0,05 studs de su superficie.
"""

import math
import random

import numpy as np

import dragon_anatomia as A
import dragon_cuerpo as C
import dragon_items as it
import dragon_sdf as s

V = np.array
PAL = it.PAL


def _x(p, k):
    return V([p[0] * k, p[1], p[2]])


# --------------------------------------------------------------------------------------------------------------
# Asentar y apartar
# --------------------------------------------------------------------------------------------------------------


def asentar(p, d, campo, hueco=0.03, rango=(-3.0, 3.0), iters=22):
    """
    Mueve cada punto p a lo largo de su dirección d (hacia fuera) hasta que campo = hueco (bisección).
    Vectorizado: p puede ser (3,) o (N, 3) y d (3,) o (N, 3).
    """
    P = np.atleast_2d(np.asarray(p, dtype=np.float64))
    D = np.atleast_2d(np.asarray(d, dtype=np.float64))
    D = D / np.linalg.norm(D, axis=1, keepdims=True)
    D = np.broadcast_to(D, P.shape)
    lo = np.full(len(P), rango[0])
    hi = np.full(len(P), rango[1])
    for _ in range(iters):
        m = (lo + hi) / 2
        v = campo(P + D * m[:, None])
        dentro = v < hueco
        lo = np.where(dentro, m, lo)
        hi = np.where(dentro, hi, m)
    out = P + D * hi[:, None]
    return out[0] if np.asarray(p).ndim == 1 else out


def superficie(p, d, campo):
    """Punto de la superficie (campo = 0) desde p en la dirección d (que apunta hacia fuera)."""
    return asentar(p, d, campo, 0.0, (-6.0, 6.0))


def gradiente(P, campo, h=0.02):
    P = np.atleast_2d(P)
    g = np.zeros_like(P)
    for i in range(3):
        e = np.zeros(3)
        e[i] = h
        g[:, i] = (campo(P + e) - campo(P - e)) / (2 * h)
    n = np.linalg.norm(g, axis=1, keepdims=True)
    return g / np.maximum(n, 1e-9)


def despegar(P, campo, minimo, iters=8):
    """Aparta los puntos que quedan a menos de `minimo` de la superficie del campo (por su gradiente)."""
    P = np.array(P, dtype=np.float64)
    for _ in range(iters):
        d = campo(P)
        malos = d < minimo
        if not malos.any():
            break
        g = gradiente(P[malos], campo)
        P[malos] += g * (minimo - d[malos])[:, None] * 1.05
    return P


# Altura máxima del detalle fino (escamas) sobre la superficie sin detalle: al apoyar algo en OTRA pieza se usa
# como margen para no atravesar las escamas.
MARGEN_DETALLE = 0.09


def campo_de(*piezas, detalle=False, margen=0.0):
    """
    Campo (unión) de una o varias piezas tal como se mallan (con su región y el hueco). Sin el detalle fino por
    velocidad; `margen` lo compensa cuando hace falta (apoyar en otra pieza: margen=MARGEN_DETALLE).
    """

    def f(P):
        P = np.atleast_2d(P)
        d, F = C.campo_cuerpo(P, con_detalle=detalle)
        out = None
        for n in piezas:
            v = np.maximum(d, C.region(P, F, n) + C.HUECO / 2)
            out = v if out is None else np.minimum(out, v)
        return out - margen

    return f


def holgura(m, campo, minimo):
    """Distancia mínima de los vértices de una malla al campo (para comprobar que no atraviesa)."""
    return float(campo(m.v).min())


# --------------------------------------------------------------------------------------------------------------
# Boca: ~40 dientes, lengua bífida, púas de la barbilla, restos entre los dientes
# --------------------------------------------------------------------------------------------------------------


def impacto(P0, d, campo, largo=8.0, pasos=160):
    """
    Trazado de rayo desde fuera: primer punto donde el rayo P0 + d·t entra en el campo (campo < 0), refinado por
    bisección. P0 (N,3) o (3,). Devuelve también si hubo impacto.
    """
    P0 = np.atleast_2d(np.asarray(P0, dtype=np.float64))
    d = s.normalizar(d)
    ts = np.linspace(0, largo, pasos)
    Q = P0[:, None, :] + ts[None, :, None] * d
    v = campo(Q.reshape(-1, 3)).reshape(len(P0), pasos)
    dentro = v < 0
    hay = dentro.any(1)
    k = np.where(hay, dentro.argmax(1), pasos - 1)
    lo = ts[np.maximum(k - 1, 0)]
    hi = ts[k]
    for _ in range(20):
        m = (lo + hi) / 2
        dm = campo(P0 + m[:, None] * d) < 0
        hi = np.where(dm, m, hi)
        lo = np.where(dm, lo, m)
    return P0 + hi[:, None] * d, hay


def linea_labio(y, k, campo_cab, campo_man):
    """Punto exterior de la línea de la boca a la altura y (lado k): donde se tocan cráneo y mandíbula."""
    zs = np.linspace(6.4, 9.8, 69)
    P0 = np.stack([np.full(len(zs), k * 6.0), np.full(len(zs), y), zs], 1)
    Q, hay = impacto(P0, V([-k, 0, 0]), lambda P: np.minimum(campo_cab(P), campo_man(P)), largo=6.0)
    dif = np.abs(campo_cab(Q) - campo_man(Q)) + (~hay) * 99
    return Q[int(np.argmin(dif))]


def boca(fino):
    rnd = random.Random(1)
    cab = campo_de("Cabeza", margen=MARGEN_DETALLE * 0.5)
    man = campo_de("Mandibula", margen=MARGEN_DETALLE * 0.5)
    sup = it.Malla()
    inf = it.Malla()
    for k, lado in ((1, "Izq"), (-1, "Der")):
        # ---- dientes superiores: 7 laterales en sierra por lado (cuelgan por fuera de la mandíbula) ----
        ys = np.linspace(-22.9, -28.9, 9)
        for i, y in enumerate(ys):
            if i == 3:
                continue  # hueco del colmillo-sable superior
            if i == 8:
                continue  # el último lo ocupan los incisivos
            lab = linea_labio(y, k, cab, man)
            raiz = lab + V([-k * 0.22, 0, 0.32])
            largo = 1.15 + 0.4 * math.sin(i / 7 * math.pi)
            roto = 0.45 if (lado == "Der" and i == 5) or (lado == "Izq" and i == 1) else None  # 2 partidos
            dte = it.diente(raiz, V([k * 0.12, 0.08, -1]), largo, 0.26 + 0.03 * largo, V([0, 1, 0]), rnd, fino,
                            curvatura=0.22, aserrado=True, roto=roto)
            dte.v = _apartar_x(dte.v, man, k, 0.04)
            sup += dte
        # ---- colmillo-sable superior (3 studs, curvo hacia atrás, por fuera de la barbilla) ----
        lab = linea_labio(-25.75, k, cab, man)
        raiz = lab + V([-k * 0.3, 0, 0.45])
        sable = it.diente(raiz, V([k * 0.1, 0.12, -1]), 3.0, 0.5, V([0, 1, 0]), rnd, fino, curvatura=0.2,
                          aplanado=0.7, estrias=True, tipo="colmillo", hundido=0.5)
        sable.v = _apartar_x(sable.v, man, k, 0.05)
        sup += sable
        # ---- colmillo inferior (3 studs; el izquierdo roto a 1,5) sube por la muesca del labio superior ----
        base = V([k * 1.98, -27.3, 7.45])
        base = asentar(base, V([0, 0, 1]), man, 0.0, rango=(-1.5, 0.8))  # sobre el borde de la encía
        roto = 0.5 if lado == "Izq" else None
        col_inf = it.diente(base - V([0, 0, 0.35]), V([k * 0.3, -0.12, 1]), 3.0, 0.32, V([k * 0.3, 1, 0]), rnd,
                            fino, curvatura=0.16, aplanado=0.75, estrias=True, tipo="colmillo", roto=roto,
                            hundido=0.4)
        col_inf.v = _apartar_x(col_inf.v, cab, k, 0.04, solo_arriba=8.0)
        inf += col_inf
        # ---- dientes inferiores laterales: 5 por lado, dentro de la boca (se ven al abrirla) ----
        for i, y in enumerate(np.linspace(-22.4, -26.4, 5)):
            t = (y - C.BOCA_A[1]) / (C.BOCA_B[1] - C.BOCA_A[1])
            rx = 2.0 + (1.35 - 2.0) * t
            zc = C.BOCA_A[2] + (C.BOCA_B[2] - C.BOCA_A[2]) * t
            raiz = V([k * (rx * 0.78), y, zc - 0.55])
            raiz = asentar(raiz, V([0, 0, 1]), man, 0.0, rango=(-1.5, 0.5)) - V([0, 0, 0.12])
            dte = it.diente(raiz, V([k * -0.15, -0.05, 1]), 1.0 + 0.1 * (i % 2), 0.2, V([0, -1, 0]), rnd, fino,
                            curvatura=0.15, aserrado=True)
            inf += dte
        # ---- incisivos superiores (3 por lado, 0,5) y barbilla ----
        for j in range(3):
            y = -29.55 - j * 0.22
            x = k * (1.45 - j * 0.5)
            frente, _ = impacto(V([x, -34.0, 8.15]), V([0, 1, 0]), cab, largo=6.0)
            raiz = frente[0] + V([0, 0.3, 0.05])
            sup += it.diente(raiz, V([0, -0.25, -1]), 0.55, 0.12, V([0, 1, 0]), rnd, fino, curvatura=0.1)
        # incisivos inferiores (3 por lado): dentro, en la punta de la mandíbula
        for j in range(3):
            x = k * (0.35 + j * 0.42)
            raiz = V([x, -28.25 + j * 0.25, 7.6])
            raiz = asentar(raiz, V([0, 0, 1]), man, 0.0, rango=(-1.5, 0.6)) - V([0, 0, 0.1])
            inf += it.diente(raiz, V([0, -0.35, 1]), 0.5, 0.11, V([0, -1, 0]), rnd, fino, curvatura=0.1)
        # ---- púas óseas de la barbilla (barba de dragón viejo) ----
        for j, (dx, dy) in enumerate(((0.45, -28.4), (1.15, -27.2))):
            p = superficie(V([k * dx, dy, 7.0]), V([0, -0.2, -1]), man)
            inf += it.espina(p - V([0, 0, -0.1]), V([k * 0.25, 0.75, -0.7]), 0.9 - 0.15 * j, 0.17, V([0, 1, 0]),
                             rnd, fino, curvatura=0.25, color=it.lin("#3A2A1C"))
    # ---- lengua bífida gruesa (3 studs) enrollada en reposo ----
    inf += lengua(fino, man, cab)
    # ---- restos entre los dientes: trozo de metal de nave y hueso de presa (en la mandíbula) ----
    p = linea_labio(-24.0, 1, cab, man)
    trozo = it.casco_nave(p + V([0.1, 0.0, -0.35]), V([1, 0, 0.2]), V([0, 1, 0]), 0.45, 0.32, rnd, fino,
                          grosor=0.05)
    trozo.v = despegar(trozo.v, cab, 0.03)
    inf += trozo
    p = linea_labio(-27.0, -1, cab, man)
    hueso = it.tubo(np.array([p + V([0.25, 0.4, -0.2]), p + V([-0.1, 0.0, -0.15]), p + V([-0.35, -0.5, -0.3])]),
                    [0.1, 0.08, 0.1], lados=8 if fino else 4)
    hueso += it.esfera(p + V([-0.38, -0.55, -0.32]), 0.13, seg=8 if fino else 4, anillos=4 if fino else 3)
    hueso.pintar(col=it.lin("#C8B898"), rugosidad=0.6)
    hueso.v = despegar(hueso.v, cab, 0.03)
    inf += hueso
    return sup, inf


def _apartar_x(v, campo, k, minimo, solo_arriba=None):
    """Empuja hacia fuera (en X) los vértices de un diente que tocan la otra pieza de la boca."""
    v = v.copy()
    for _ in range(12):
        d = campo(v)
        malos = d < minimo
        if solo_arriba is not None:
            malos &= v[:, 2] < 99
        if not malos.any():
            break
        # se mueve el diente entero (no se deforma)
        v[:, 0] += k * (minimo - d[malos].min()) * 0.6 + k * 0.01
    return v


def lengua(fino, man, cab):
    rnd = random.Random(5)
    # camino: de la garganta hacia delante, y la punta enrollada hacia atrás sobre sí misma
    pts = [V([0, -21.9, 8.2]), V([0, -23.2, 8.05]), V([0, -24.6, 8.0]), V([0.05, -25.6, 8.15]),
           V([0.1, -26.1, 8.55]), V([0.05, -25.7, 8.9]), V([-0.05, -25.0, 8.85])]
    cam = []
    for a, b in zip(pts[:-1], pts[1:]):
        for t in np.linspace(0, 1, 5 if fino else 2, endpoint=False):
            cam.append(a + (b - a) * t)
    cam.append(pts[-1])
    cam = np.asarray(cam)
    n = len(cam)
    rad = np.linspace(0.62, 0.3, n)

    def perfil(t, ang):
        return np.ones_like(ang) * 1.0, np.ones_like(ang) * 0.48  # gruesa y aplanada

    m = it.tubo(cam, rad, lados=14 if fino else 6, perfil=perfil, arriba=V([0, 0, 1]), tapa_fin=True)
    # punta bífida: dos puntas que salen del final
    fin = cam[-1]
    d = s.normalizar(cam[-1] - cam[-2])
    for k in (1, -1):
        p = fin + V([k * 0.12, 0, 0])
        m += it.tubo(np.array([p - d * 0.1, p + d * 0.3 + V([k * 0.12, 0, 0]), p + d * 0.55 + V([k * 0.25, 0, 0])]),
                     [0.14, 0.09, 0.02], lados=6 if fino else 4, punta=True)
    m.v = despegar(m.v, cab, 0.04)
    m.col = np.tile(it.lin("#5A3434"), (len(m.v), 1))
    if fino:
        m.col *= (0.8 + 0.4 * (s.fbm(m.v, 0.25, 3, semilla=4) + 0.5))[:, None]
    m.rme = np.tile([0.3, 0, 0.0], (len(m.v), 1))
    return m


# --------------------------------------------------------------------------------------------------------------
# Ojos
# --------------------------------------------------------------------------------------------------------------


def ojos(fino):
    rnd = random.Random(2)
    m = it.Malla()
    for k in (1, -1):
        mira = V([k * 0.8, -0.55, 0.05])
        c = _x(A.OJO, k) - s.normalizar(mira) * 0.28  # hundido en la cuenca, bajo la ceja ósea
        o = it.ojo(c, mira, A.R_OJO, rnd, fino)
        if k == 1:
            # ojo izquierdo cicatrizado: córnea con un tajo vertical lechoso (ve peor de ese lado)
            P = o.v - c
            u, v, w = s.base_ortonormal(s.normalizar(mira))
            raya = (np.abs(P @ u) < 0.07 * A.R_OJO * 1.6) & ((P @ w) > 0)
            o.col[raya] = it.lin("#6A5A55")
            o.rme[raya, 2] *= 0.15
        m += o
    return m


# --------------------------------------------------------------------------------------------------------------
# Cornamenta (pieza separada) y espinas
# --------------------------------------------------------------------------------------------------------------

CORNAMENTA_PIVOTE = V([0.0, -21.6, 13.6])


def cornamenta(fino):
    rnd = random.Random(3)
    cab = campo_de("Cabeza", margen=MARGEN_DETALLE)
    m = it.Malla()
    defs = []
    for k in (1, -1):
        # 2 principales (4 studs) hacia atrás y arriba
        defs.append((V([k * 1.5, -21.4, 13.2]), V([k * 0.5, 0.55, 0.85]), 4.6, 0.95, V([0, 1, 0.2]), None, 0.5))
        # 4 secundarios (2 studs) en corona
        defs.append((V([k * 2.45, -21.9, 12.7]), V([k * 0.9, 0.5, 0.5]), 2.4, 0.5, V([0, 0.5, 1]),
                     0.4 if k == -1 else None, 0.35))
        defs.append((V([k * 2.75, -20.5, 11.8]), V([k * 0.8, 0.85, 0.1]), 2.2, 0.45, V([0, 0, 1]), None, 0.3))
        # 2 cuernos menores sobre los ojos (cejas blindadas, 1 stud)
        defs.append((V([k * 2.35, -23.9, 12.4]), V([k * 0.5, -0.35, 0.85]), 1.15, 0.3, V([0, 1, 0]), None, 0.3))
    for base, dire, largo, radio, hacia, roto, curv in defs:
        dire = s.normalizar(dire)
        n = gradiente(base[None], cab)[0]
        b = asentar(base - n * 0.5, n, cab, 0.025)
        h = it.cuerno(b, dire, largo, radio, hacia, rnd, fino, curvatura=curv, roto=roto)
        # base ensanchada que se adapta al cráneo: los vértices del primer anillo se asientan sobre él
        lados = 20 if fino else 7
        base_idx = np.arange(lados)
        anillo = h.v[base_idx]
        cen = anillo.mean(0)
        anillo = cen + (anillo - cen) * 1.35
        anillo = asentar(anillo - n * 0.6, n, cab, 0.025)
        h.v[base_idx] = anillo
        # tapa de la base también sobre el cráneo
        h.v[-1] = asentar(cen - n * 0.6, n, cab, 0.03)
        h.v = despegar(h.v, cab, 0.02, iters=4)
        m += h
    return m


def espinas_cuello(fino, nombre):
    """12 espinas a lo largo del cuello (más grandes en la base); varias rotas por las batallas."""
    rnd = random.Random(4)
    C3 = A.CUELLO
    tam = np.linspace(2.0, 0.5, 12)
    tam[1] = 2.0
    tam[2] = 1.9
    rotas = {4: 0.12, 7: 0.15, 9: 0.5}  # 2 con solo la base, 1 a la mitad
    tramo = {"Cuello_Base": 0, "Cuello_Medio": 1, "Cuello_Superior": 2}[nombre]
    m = it.Malla()
    campo = campo_de(nombre)
    for i in range(12):
        t = (i + 0.5) / 12 * 3
        j = min(int(t), 2)
        if j != tramo:
            continue
        f = t - j
        a, b = C3[j], C3[j + 1]
        p = a + (b - a) * f
        eje = s.normalizar(b - a)
        arriba = s.normalizar(np.cross(eje, V([1, 0, 0])) * -1)
        if arriba[2] < 0:
            arriba = -arriba
        base = superficie(p, arriba, campo) - arriba * 0.25
        direc = s.normalizar(arriba * 1.0 + eje * -0.55)  # inclinadas hacia la cola
        m += it.espina(base, direc, tam[i], 0.16 + 0.17 * tam[i] / 2, -eje, rnd, fino, curvatura=0.2,
                       roto=rotas.get(i), color=it.lin("#1E1414"))
    return m


def papada(fino):
    """4 placas semiesféricas de hueso bajo la garganta (protección), en el cuello superior y medio."""
    out = {"Cuello_Medio": it.Malla(), "Cuello_Superior": it.Malla()}
    C3 = A.CUELLO
    for i, (j, f) in enumerate(((1, 0.4), (1, 0.7), (2, 0.3), (2, 0.6))):
        nombre = "Cuello_Medio" if j == 1 else "Cuello_Superior"
        campo = campo_de(nombre)
        a, b = C3[j], C3[j + 1]
        p = a + (b - a) * f
        eje = s.normalizar(b - a)
        abajo = s.normalizar(np.cross(eje, V([1, 0, 0])))
        if abajo[2] > 0:
            abajo = -abajo
        q = superficie(p, abajo, campo)
        r = 0.75 - 0.08 * i
        e = it.esfera((0, 0, 0), r, seg=16 if fino else 7, anillos=8 if fino else 4, escala=(1.0, 1.25, 0.55))
        e = it.orientar(e, q - abajo * 0.12, abajo, arriba=eje)
        e.pintar(col=it.lin("#2A201A"), rugosidad=0.55)
        if fino:
            e.col = e.col * (0.8 + 0.5 * (s.fbm(e.v, 0.3, 3, semilla=i) + 0.5))[:, None]
        out[nombre] += e
    return out


def cresta_dorsal(fino):
    """
    Cresta_Dorsal (pieza neón separada): 20 espinas por la línea del lomo, de la base del cuello al inicio de la
    cola, con membrana de vela entre ellas (rasgada y parcheada) y brillo de lava en las bases. 3 rotas: 2 con la
    base y 1 cortada limpia (arma humana).
    """
    rnd = random.Random(6)
    tor = campo_de("Torso", margen=MARGEN_DETALLE)
    y0, y1 = -6.6, 8.8
    m = it.Malla()
    bases = []
    puntas = []
    rotas = {5: (0.2, False), 12: (0.25, False), 15: (0.45, True)}
    for i in range(20):
        t = i / 19
        y = y0 + (y1 - y0) * t
        alto = 1.0 + 2.0 * math.sin(t * math.pi) ** 1.2  # 1-3 studs, las mayores en el centro
        base = superficie(V([0, y, 9.5]), V([0, 0, 1]), tor) + V([0, 0, 0.03])
        b = asentar(base - V([0, 0, 0.4]), V([0, 0, 1]), tor, 0.03)
        direc = s.normalizar(V([0, 0.45, 1]))
        roto, limpio = rotas.get(i, (None, False))
        e = it.espina(b, direc, alto, 0.2 + 0.08 * alto, V([0, 1, 0]), rnd, fino, curvatura=0.25, roto=roto,
                      brillo=2.2, color=it.lin("#1A0E0C"), corte_limpio=limpio)
        # el primer anillo se asienta sobre el lomo
        lados = 12 if fino else 5
        e.v[:lados] = asentar(e.v[:lados] - V([0, 0, 0.5]), V([0, 0, 1]), tor, 0.025)
        m += e
        bases.append(b)
        h = alto * (roto if roto else 1.0)
        puntas.append(b + direc * h * 0.72)
    m += membrana_cresta(bases, puntas, rotas, fino, tor)
    return m


def membrana_cresta(bases, puntas, rotas, fino, tor):
    """Vela entre espinas: grosor 0,1, borde superior festoneado, desgarros y parches."""
    rnd = random.Random(7)
    piezas = []
    for i in range(len(bases) - 1):
        if i in (5, 11, 12):  # desgarrada junto a las espinas rotas
            continue
        nv = 6 if fino else 2
        nu = 6 if fino else 2
        b0, b1 = bases[i], bases[i + 1]
        t0, t1 = puntas[i], puntas[i + 1]
        if i in rotas or i + 1 in rotas:
            # parche bajo (regenerado)
            t0 = b0 + (t0 - b0) * 0.45
            t1 = b1 + (t1 - b1) * 0.45
        grid = []
        for a in range(nu + 1):
            u = a / nu
            fila = []
            for c in range(nv + 1):
                v = c / nv
                abajo = b0 + (b1 - b0) * u
                arriba = t0 + (t1 - t0) * u
                arriba = arriba - V([0, 0, 0.35]) * math.sin(u * math.pi)  # festón
                p = abajo + (arriba - abajo) * v
                fila.append(p)
            grid.append(fila)
        grid = np.asarray(grid)
        # bajo la vela: que no toque el lomo
        g = grid.reshape(-1, 3)
        g = despegar(g, tor, 0.06)
        grid = g.reshape(grid.shape)
        piezas.append(_lamina(grid, 0.1, V([1, 0, 0])))
    m = it.unir(piezas)
    h = m.v[:, 2]
    m.col = np.tile(it.lin("#3A0606"), (len(m.v), 1))
    if fino:
        ven = s.smoothstep(0.6, 0.9, np.abs(np.sin(m.v[:, 1] * 6 + s.fbm(m.v, 0.5, 2, semilla=3) * 3)))
        m.col *= (1 - 0.5 * ven)[:, None]
    m.rme = np.tile([0.5, 0, 0], (len(m.v), 1))
    base_brillo = 1 - s.smoothstep(0.0, 0.6, h - np.interp(m.v[:, 1], [b[1] for b in bases], [b[2] for b in bases]))
    m.rme[:, 2] = base_brillo * 1.2
    m.emi = np.tile(PAL["boca"], (len(m.v), 1))
    return m


def _lamina(grid, grosor, lado):
    """Lámina con grosor a partir de una rejilla (nu+1, nv+1, 3): dos caras + borde."""
    nu1, nv1, _ = grid.shape
    gu = np.gradient(grid, axis=0)
    gv = np.gradient(grid, axis=1)
    n = np.cross(gu, gv)
    n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-9)
    if np.mean(n.reshape(-1, 3) @ lado) < 0:
        n = -n
    a = grid + n * grosor / 2
    b = grid - n * grosor / 2
    V_ = np.vstack([a.reshape(-1, 3), b.reshape(-1, 3)])
    off = nu1 * nv1
    F = []

    def ix(i, j):
        return i * nv1 + j

    for i in range(nu1 - 1):
        for j in range(nv1 - 1):
            p, q, r, t = ix(i, j), ix(i + 1, j), ix(i + 1, j + 1), ix(i, j + 1)
            F += [(p, q, r), (p, r, t), (off + p, off + r, off + q), (off + p, off + t, off + r)]
    borde = [ix(i, 0) for i in range(nu1)] + [ix(nu1 - 1, j) for j in range(1, nv1)] + \
        [ix(i, nv1 - 1) for i in range(nu1 - 2, -1, -1)] + [ix(0, j) for j in range(nv1 - 2, 0, -1)]
    for i in range(len(borde)):
        p, q = borde[i], borde[(i + 1) % len(borde)]
        F += [(q, p, off + p), (q, off + p, off + q)]
    return it.Malla(V_, np.asarray(F))


# --------------------------------------------------------------------------------------------------------------
# Torso: placas tectónicas, ecosistema, fragmentos clavados
# --------------------------------------------------------------------------------------------------------------


def torso(fino):
    rnd = random.Random(8)
    tor = campo_de("Torso")
    m = it.Malla()
    placas = []
    # 8 placas: 4 por lado, escalonadas, inclinadas hacia fuera como tejas de armadura
    for k in (1, -1):
        for j, y in enumerate((-1.2, 1.9, 4.8, 7.4)):
            y2 = y + (0.7 if k == -1 else 0)
            x = k * (2.3 + 0.25 * (j % 2))
            p = superficie(V([x, y2, 10.5]), V([k * 0.45, 0, 1]), tor)
            n = gradiente(p[None], tor)[0]
            largo = 3.0 - 0.25 * j
            ancho = 2.2 - 0.1 * j
            c = p - n * 0.15
            pl = it.placa(c, n, V([0, 1, -0.1]), largo, ancho, 0.5, rnd, fino)
            pl.v = _asentar_base(pl.v, c, n, tor, 0.5)
            m += pl
            placas.append((p, n, largo, ancho))
    # fragmento de casco de nave humana (3×2) encajado entre las 2 primeras placas izquierdas
    p0, n0 = placas[0][0], placas[0][1]
    p1 = placas[1][0]
    c = (p0 + p1) / 2 + V([0.35, 0, 0])
    n = gradiente(c[None], tor)[0]
    q = superficie(c, n, tor)
    nave = it.casco_nave(q + n * 0.3, s.normalizar(n + V([0.6, 0, 0])), V([0, 1, 0.3]), 3.0, 2.0, rnd, fino)
    nave.v = _hundir_borde(nave.v, tor, q, n)
    m += nave
    # lanza rota entre las 2 placas derechas del centro (0,8 visible)
    pa, pb = placas[5][0], placas[6][0]
    c = (pa + pb) / 2
    n = gradiente(c[None], tor)[0]
    q = superficie(c, n, tor)
    m += it.lanza_rota(q, s.normalizar(n + V([0.3, -0.4, 0])), 0.8, rnd, fino)
    # punta de arpón oxidado en el flanco izquierdo (1,5 fuera) con piel cicatrizada (en la textura)
    q = superficie(V([3.0, -0.6, 9.4]), V([1, 0, 0.1]), tor)
    m += it.arpon(q - V([0.15, 0, 0]), V([1, 0.35, 0.25]), 1.5, rnd, fino, cuerda=False, solo_punta=True,
                  sobresale=1.5)
    m += anillo_cicatriz(q, V([1, 0, 0]), 0.55, tor, fino)
    # fragmento de casco en el hombro derecho (2 studs, metal retorcido con musgo)
    q = superficie(V([-4.2, -5.0, 12.0]), V([-1, -0.2, 0.6]), tor)
    n = gradiente(q[None], tor)[0]
    fr = it.casco_nave(q + n * 0.15, s.normalizar(n + V([-0.4, 0.3, 0])), V([0, 1, 0.5]), 2.0, 1.1, rnd, fino,
                       grosor=0.1)
    fr.v = _hundir_borde(fr.v, tor, q, n)
    m += fr
    m += anillo_cicatriz(q, n, 0.9, tor, fino)
    # ecosistema del lomo: 2 corales, 9 percebes, nido
    huecos = [(placas[1][0] + placas[2][0]) / 2, (placas[4][0] + placas[6][0]) / 2 + V([0.4, 0, 0])]
    for i, h in enumerate(huecos):
        n = gradiente(h[None], tor)[0]
        q = superficie(h, n, tor)
        m += it.coral(q, n, 1.3 + 0.2 * i, rnd, fino, PAL["coral_rojo"] if i == 0 else PAL["coral_negro"])
        m += it.coral(q + V([0.35 * (1 if i else -1), 0.4, 0]), n, 0.8, rnd, fino,
                      PAL["coral_negro"] if i == 0 else PAL["coral_rojo"])
    for i in range(9):
        y = -6.0 + i * 1.65 + rnd.random() * 0.5
        x = (1 if i % 2 else -1) * (1.1 + rnd.random() * 2.6)
        q = superficie(V([x, y, 10.0]), V([x * 0.2, 0, 1]), tor)
        n = gradiente(q[None], tor)[0]
        alto = 0.3 + 0.2 * rnd.random()
        m += it.percebe(q - n * 0.05, n, alto, alto * 0.55, rnd, fino, roto=i in (2, 6))
        if i % 3 == 0:  # racimos
            m += it.percebe(q + V([0.3, 0.2, 0]) - n * 0.05, n, alto * 0.7, alto * 0.4, rnd, fino)
    q = superficie(V([-1.4, 3.3, 11.0]), V([0, 0, 1]), tor)
    m += it.nido(q + V([0, 0, 0.25]), V([0, 0, 1]), 0.5, rnd, fino)
    return m


def _asentar_base(v, c, n, campo, grosor):
    """Baja la cara inferior de una placa hasta la carne (sin dejar hueco por debajo)."""
    v = v.copy()
    abajo = ((v - c) @ n) < -grosor * 0.3
    if abajo.any():
        d = campo(v[abajo])
        v[abajo] -= np.outer(np.maximum(d, 0) + 0.12, n)
    return v


def _hundir_borde(v, campo, q, n):
    """Mete en la carne la parte del fragmento que queda por debajo de la superficie (incrustado, no pegado)."""
    v = v.copy()
    d = campo(v)
    cerca = d < 0.25
    v[cerca] -= np.outer(0.25 - d[cerca], n) * 0.8
    return v


def anillo_cicatriz(q, n, r, campo, fino):
    """Reborde de piel cicatrizada alrededor de un fragmento clavado (anillo carnoso algo más claro)."""
    n = s.normalizar(n)
    u, v, _ = s.base_ortonormal(n)
    seg = 24 if fino else 8
    ang = np.linspace(0, math.tau, seg + 1)
    cam = np.array([q + (math.cos(a) * u + math.sin(a) * v) * r * (1 + 0.15 * math.sin(a * 3)) for a in ang])
    cam = asentar(cam - n * 0.4, n, campo, -0.04)
    m = it.tubo(cam, 0.11, lados=6 if fino else 4, tapa_ini=False, tapa_fin=False)
    m.col = np.tile(it.lin("#2E1E1C"), (len(m.v), 1))
    m.rme = np.tile([0.4, 0, 0], (len(m.v), 1))
    return m


# --------------------------------------------------------------------------------------------------------------
# Cadenas rotas (anillo incrustado en la base del cuello izquierdo)
# --------------------------------------------------------------------------------------------------------------


def cadenas(fino):
    rnd = random.Random(9)
    cue = campo_de("Cuello_Base")
    todo = lambda P: C.campo_cuerpo(np.atleast_2d(P), con_detalle=False)[0]  # noqa: E731
    q = superficie(V([1.2, -11.6, 13.4]), V([1, -0.5, 0.1]), cue)
    n = gradiente(q[None], cue)[0]
    m = it.Malla()
    anillo = it.eslabon(q + n * 0.12, s.normalizar(np.cross(n, V([0, 0, 1]))), n, 1.0, 0.2, fino)
    anillo.v = _hundir_borde(anillo.v, cue, q, n)
    m += anillo
    # 2 segmentos colgando (4 studs), por delante del pecho sin tocarlo
    for j, (dx, largo) in enumerate(((0.0, 4.2), (0.25, 2.6))):
        ini = q + n * 0.5 + V([dx, -0.1, -0.35])
        pts = [ini]
        for i in range(1, 12):
            t = i / 11
            pts.append(ini + V([0.25 * t + dx * t, -0.9 * math.sin(t * 2.0) - 0.3 * t, -largo * t]))
        pts = np.asarray(pts)
        pts = despegar(pts, todo, 0.32, iters=12)
        m += it.cadena(pts, 0.5, 0.11, rnd, fino, rotos={len(pts) * 2 - 3} if j == 0 else {3})
    m.v = despegar(m.v, campo_de("Torso", "Pata_Del_Izq_Muslo", margen=MARGEN_DETALLE), 0.03, iters=6)
    return m


# --------------------------------------------------------------------------------------------------------------
# Patas: garras y espolones
# --------------------------------------------------------------------------------------------------------------


def garras_del(lado, fino):
    rnd = random.Random(10 + (lado == "Der"))
    k = 1 if lado == "Izq" else -1
    nombre = f"Pata_Del_{lado}_Garra"
    campo = campo_de(nombre)
    pie = _x(A.DEL_PIE, k)
    m = it.Malla()
    for dx, dy in ((-0.95, -1.55), (-0.3, -1.95), (0.35, -1.9), (0.95, -1.45)):
        punta = pie + V([dx * k, dy, -0.35])
        dire = s.normalizar(V([dx * k * 0.3, -1, 0.15]))
        base = punta - dire * 0.25
        m += it.garra(base, dire, 2.0, 0.3, V([0, 0, -1]), rnd, fino)
    # espolón trasero
    esp = pie + V([0, 1.3, -0.25])
    m += it.garra(esp - V([0, 0.15, 0]), V([0, 1, -0.2]), 1.1, 0.22, V([0, 0, -1]), rnd, fino)
    return m


def garras_tras(lado, fino):
    rnd = random.Random(20 + (lado == "Der"))
    k = 1 if lado == "Izq" else -1
    pie = _x(A.TRAS_PIE, k)
    to = _x(A.TRAS_TOBILLO, k)
    m = it.Malla()
    for dx, dy in ((-0.75, -1.95), (0.0, -2.35), (0.75, -1.9)):
        punta = pie + V([dx * k, dy, -0.45])
        dire = s.normalizar(V([dx * k * 0.25, -1, 0.1]))
        m += it.garra(punta - dire * 0.3, dire, 2.5, 0.38, V([0, 0, -1]), rnd, fino, trasera=True)
    # espolón asesino retráctil (3 studs, en el dedo interior, levantado como un velocirraptor)
    base = pie + V([-0.75 * k, -0.55, 0.55])
    m += it.garra(base, V([-0.25 * k, -0.55, 1.0]), 3.0, 0.42, V([0, -1, 0.2]), rnd, fino)
    return m


# --------------------------------------------------------------------------------------------------------------
# Cola: crestas dorsal (10) y ventral (15), arpón casi entero en la base, metal clavado en el hacha
# --------------------------------------------------------------------------------------------------------------


def cola(fino):
    rnd = random.Random(11)
    out = {n: it.Malla() for n in ("Cola_Base", "Cola_Media", "Cola_Punta")}
    T = A.COLA
    nombres = ["Cola_Base", "Cola_Media", "Cola_Punta"]
    campos = {n: campo_de(n) for n in nombres}

    def punto(t):
        j = min(int(t), 2)
        f = t - j
        return j, T[j] + (T[j + 1] - T[j]) * f, s.normalizar(T[j + 1] - T[j])

    for i in range(10):  # dorsal
        t = 0.15 + i / 10 * 2.6
        j, p, eje = punto(t)
        campo = campos[nombres[j]]
        q = superficie(p, V([0, 0, 1]), campo) - V([0, 0, 0.2])
        tam = 1.4 - 0.08 * i
        out[nombres[j]] += it.espina(q, s.normalizar(V([0, 0.6, 1])), tam, 0.15 + 0.08 * tam, V([0, 1, 0]), rnd,
                                     fino, color=it.lin("#1E1414"))
    for i in range(15):  # ventral, alternando tamaños
        t = 0.2 + i / 15 * 2.6
        j, p, eje = punto(t)
        campo = campos[nombres[j]]
        q = superficie(p, V([0, 0, -1]), campo) + V([0, 0, 0.18])
        tam = (0.9 if i % 2 == 0 else 0.5) * (1 - i / 30)
        out[nombres[j]] += it.espina(q, s.normalizar(V([0, 0.8, -1])), tam, 0.11 + 0.06 * tam, V([0, 1, 0]), rnd,
                                     fino, color=it.lin("#2A1E1A"))
    # escamas largas y puntiagudas en los lados de la cola: hileras de púas pequeñas
    for i in range(12):
        t = 0.3 + i / 12 * 2.5
        j, p, eje = punto(t)
        for k in (1, -1):
            campo = campos[nombres[j]]
            q = superficie(p, V([k, 0, 0.35]), campo) - V([k * 0.12, 0, 0])
            tam = 0.35 + 0.25 * t / 3
            out[nombres[j]] += it.espina(q, s.normalizar(V([k * 0.8, 1.0, 0.25])), tam, 0.1 + 0.05 * tam,
                                         V([0, 1, 0]), rnd, fino, color=it.lin("#160E0E"), aplanado=0.4)
    # arpón casi completo en la base de la cola (asta de 2 studs, cuerda podrida)
    q = superficie(V([1.0, 12.0, 10.5]), V([1, 0.2, 0.7]), campos["Cola_Base"])
    n = gradiente(q[None], campos["Cola_Base"])[0]
    out["Cola_Base"] += it.arpon(q - n * 0.1, s.normalizar(n + V([0.2, -0.5, 0.3])), 2.0, rnd, fino)
    out["Cola_Base"] += anillo_cicatriz(q, n, 0.4, campos["Cola_Base"], fino)
    # la hoja del hacha (pieza dura de filo real) y un fragmento de metal clavado en ella
    hoja, sup_hoja = hacha(fino, rnd)
    out["Cola_Punta"] += hoja
    eje, lado, gro = C.hacha_marco()
    q = sup_hoja(1.15, 0.35)
    fr = it.casco_nave(q - gro * 0.05, s.normalizar(gro + lado * 0.4), eje, 0.75, 0.5, rnd, fino, grosor=0.06)
    out["Cola_Punta"] += fr
    return out


def lamina_g(mid, n, gro):
    """Lámina de grosor variable: rejilla media (nu, nv, 3), normales (nu, nv, 3) y grosor (nu, nv)."""
    nu1, nv1, _ = mid.shape
    a = mid + n * gro[..., None] / 2
    b = mid - n * gro[..., None] / 2
    Vt = np.vstack([a.reshape(-1, 3), b.reshape(-1, 3)])
    off = nu1 * nv1
    F = []

    def ix(i, j):
        return i * nv1 + j

    for i in range(nu1 - 1):
        for j in range(nv1 - 1):
            p, q, r, t = ix(i, j), ix(i + 1, j), ix(i + 1, j + 1), ix(i, j + 1)
            F += [(p, q, r), (p, r, t), (off + p, off + r, off + q), (off + p, off + t, off + r)]
    borde = [ix(i, 0) for i in range(nu1)] + [ix(nu1 - 1, j) for j in range(1, nv1)] + \
        [ix(i, nv1 - 1) for i in range(nu1 - 2, -1, -1)] + [ix(0, j) for j in range(nv1 - 2, 0, -1)]
    for i in range(len(borde)):
        p, q = borde[i], borde[(i + 1) % len(borde)]
        F += [(q, p, off + p), (q, off + p, off + q)]
    return it.Malla(Vt, np.asarray(F), nrm=np.vstack([n.reshape(-1, 3), -n.reshape(-1, 3)]))


def hacha(fino, rnd):
    """
    Hoja del hacha de la cola: doble filo (bilateral) de hueso, 4 × 3 studs, que se ensancha en media luna hacia
    cada filo y se afila hasta 0,1. Muescas de impacto, rayas y abolladuras: esta cola ha destruido naves.
    """
    eje, lado, gro = C.hacha_marco()
    nb, na = (60, 26) if fino else (16, 7)
    B = np.linspace(-1, 1, nb)
    Aa = np.linspace(-1, 1, na)
    BB, AA = np.meshgrid(B, Aa, indexing="ij")
    muescas = np.zeros_like(BB)
    for (a0, lado_b, prof) in ((0.45, 1, 0.22), (-0.55, -1, 0.3), (0.05, -1, 0.15), (-0.2, 1, 0.12)):
        muescas += prof * np.exp(-((AA - a0) ** 2) / 0.012) * (np.sign(BB) == lado_b) * (np.abs(BB) > 0.6)
    b = BB * 2.0 * (1 - 0.14 * AA**2) - np.sign(BB) * muescas
    a_half = 0.42 + 1.08 * np.clip(np.abs(b) / 2.0, 0, 1) ** 1.6
    a = AA * a_half
    t = 0.5 * (1 - np.clip(np.abs(b) / 2.0, 0, 1)) ** 1.1 + 0.05  # grosor: 0,55 en el centro, 0,05+ en el filo
    t = t * (1 - 0.6 * np.abs(AA) ** 4) + 0.04
    mid = A.HACHA + b[..., None] * lado + a[..., None] * eje
    n = np.broadcast_to(gro, mid.shape).copy()
    if fino:
        # abolladuras y rayas en las caras
        ab = s.fbm(mid.reshape(-1, 3), 0.5, 3, semilla=12).reshape(b.shape)
        t = t * (1 + 0.15 * ab)
    m = lamina_g(mid, n, t)
    P = m.v
    q = P - A.HACHA
    ab_ = np.abs(q @ lado)
    filo = s.smoothstep(1.55, 1.95, ab_)
    col = np.tile(it.lin("#2A2018"), (len(P), 1)) * 0.8
    col = col * (1 - filo[:, None]) + PAL["marfil"][None, :] * 0.6 * filo[:, None]
    rug = 0.5 - 0.25 * filo
    if fino:
        raya = s.smoothstep(0.82, 0.97, np.abs(np.sin(P @ V([9.0, 4.0, 13.0]) + 3 * s.fbm(P, 0.4, 2, semilla=2))))
        col = col * (1 + 1.5 * raya[:, None])
        mancha = s.smoothstep(0.2, 0.6, s.fbm(P, 0.6, 3, semilla=19))
        col = col * (1 - 0.5 * mancha[:, None])
        col = col + PAL["sangre"][None, :] * 0.08 * mancha[:, None]
    m.col = np.clip(col, 0, 1)
    m.rme = np.stack([rug, np.zeros(len(P)), np.zeros(len(P))], 1)

    def sup_hoja(bv, av):
        tt = 0.5 * (1 - min(abs(bv) / 2.0, 1)) ** 1.1 + 0.09
        return A.HACHA + lado * bv + eje * av + gro * tt / 2

    return m, sup_hoja


# --------------------------------------------------------------------------------------------------------------
# Alas: membranas (grosor 0,2 en bordes), venas, desgarros reparados, agujero, percebes, cangrejo fósil, pulgar
# --------------------------------------------------------------------------------------------------------------


def _bez(a, b, c, t):
    return (1 - t) ** 2 * a + 2 * (1 - t) * t * b + t**2 * c


def _dedo(k, i, t):
    """Punto a lo largo del dedo i (0 muñeca, 1 punta) pasando por el nudillo."""
    m = _x(A.ALA_MUNECA, k)
    punta, nud = _x(A.ALA_DEDOS[i][0], k), _x(A.ALA_DEDOS[i][1], k)
    L1 = np.linalg.norm(nud - m)
    L2 = np.linalg.norm(punta - nud)
    f = L1 / (L1 + L2)
    if t <= f:
        return m + (nud - m) * (t / f)
    return nud + (punta - nud) * ((t - f) / (1 - f))


def membranas_ala(lado, fino):
    """Devuelve {pieza: Malla} con la membrana de la mano (entre dedos) y la del antebrazo (dedo 4 -> cuerpo)."""
    k = 1 if lado == "Izq" else -1
    rnd = random.Random(30 + (k < 0))
    nu, nv = (34, 20) if fino else (11, 6)
    otros = campo_de("Torso", f"Ala_{lado}_Hombro", margen=MARGEN_DETALLE)
    mano_c = campo_de(f"Ala_{lado}_Mano", margen=MARGEN_DETALLE)
    ante_c = campo_de(f"Ala_{lado}_Antebrazo", margen=MARGEN_DETALLE)
    # Lado hacia el que se combada la membrana (hacia atrás y algo hacia dentro: el viento la empuja)
    comba = s.normalizar(V([-0.25 * k, 0.9, -0.2]))
    sectores = {}
    # ---- sectores de la mano: entre dedo i e i+1 ----
    for i in range(3):
        grid = np.zeros((nu + 1, nv + 1, 3))
        for a in range(nu + 1):
            u = a / nu
            for c in range(nv + 1):
                v = c / nv
                p0 = _dedo(k, i, u)
                p1 = _dedo(k, i + 1, u)
                p = p0 + (p1 - p0) * v
                # festón del borde de salida (curva hacia la muñeca) y comba
                medio = (_dedo(k, i, 1.0) + _dedo(k, i + 1, 1.0)) / 2
                fest = 0.16 * 4 * v * (1 - v) * u**3
                p = p + (_x(A.ALA_MUNECA, k) - medio) * fest
                p = p + comba * 0.9 * math.sin(math.pi * v) * math.sin(math.pi * u * 0.9) * 0.9
                grid[a, c] = p
        sectores[f"mano{i}"] = grid
    # ---- membrana del antebrazo (plagiopatagio): dedo 4 -> flanco, y borde de ataque por húmero y antebrazo ----
    nb = nu
    grid = np.zeros((nb + 1, nv + 1, 3))
    wh, wc, wm = _x(A.ALA_HOMBRO, k), _x(A.ALA_CODO, k), _x(A.ALA_MUNECA, k)
    ancla = _x(A.ALA_ANCLA_CUERPO, k)
    p4 = _x(A.ALA_DEDOS[3][0], k)
    for a in range(nb + 1):
        u = a / nb  # 0: cuerpo, 1: dedo 4
        # borde de ataque: hombro -> codo -> muñeca (por detrás de los huesos)
        if u < 0.5:
            ataque = wh + (wc - wh) * (u / 0.5)
        else:
            ataque = wc + (wm - wc) * ((u - 0.5) / 0.5)
        # borde de salida: ancla -> punta del dedo 4 (festoneado)
        salida = ancla + (p4 - ancla) * u
        medio = (ancla + p4) / 2
        salida = salida + (wc - medio) * 0.22 * 4 * u * (1 - u)
        if u > 0.999:
            salida = p4
        for c in range(nv + 1):
            v = c / nv
            if u > 0.999:
                p = _dedo(k, 3, v)
            else:
                # en u=1 la membrana coincide con el dedo 4; mezcla hacia él
                dedo = _dedo(k, 3, v)
                lin_ = ataque + (salida - ataque) * v
                w = s.smoothstep(0.75, 1.0, u)
                p = lin_ * (1 - w) + dedo * w
            p = p + comba * 1.2 * math.sin(math.pi * v) * math.sin(math.pi * u)
            grid[a, c] = p
    sectores["antebrazo"] = grid
    # ---- construir láminas con grosor (0,12 en el centro, 0,2 en los bordes libres) ----
    resultado = {f"Ala_{lado}_Mano": it.Malla(), f"Ala_{lado}_Antebrazo": it.Malla()}
    for nombre, grid in sectores.items():
        pieza = f"Ala_{lado}_Mano" if nombre.startswith("mano") else f"Ala_{lado}_Antebrazo"
        g = grid.reshape(-1, 3)
        if nombre == "antebrazo":
            # apartar del torso y del húmero (otras piezas) y del dedo 4 (pieza Mano)
            g = despegar(g, otros, 0.09, iters=10)
            g = despegar(g, mano_c, 0.09, iters=10)
        else:
            g = despegar(g, ante_c, 0.09, iters=10)
        grid = g.reshape(grid.shape)
        lam = _lamina_variable(grid, fino, borde_libre=(nombre == "antebrazo"))
        resultado[pieza] += lam
    _pintar_membrana(resultado, lado, k, fino, rnd)
    # ---- percebes y cangrejo fósil en la cara interior (la que mira hacia delante) ----
    mano = resultado[f"Ala_{lado}_Mano"]
    puntos = [(1, 0.35, 0.4), (1, 0.55, 0.6), (0, 0.45, 0.5), (2, 0.3, 0.5), (2, 0.5, 0.3)]
    for j, (sec, u, v) in enumerate(puntos[: (5 if k == 1 else 4)]):
        g = sectores[f"mano{sec}"]
        a, c = int(u * nu), int(v * nv)
        p = g[a, c]
        nrm = np.cross(g[a + 1, c] - g[a, c], g[a, c + 1] - g[a, c])
        nrm = s.normalizar(nrm)
        if nrm[1] > 0:  # cara interior = la que mira a -Y (delante)
            nrm = -nrm
        alto = 0.3 + 0.15 * (j % 3)
        mano += it.percebe(p + nrm * 0.03, nrm, alto, alto * 0.6, rnd, fino, roto=j == 3)
    if k == 1:
        g = sectores["mano1"]
        a, c = int(0.42 * nu), int(0.25 * nv)
        p = g[a, c]
        nrm = s.normalizar(np.cross(g[a + 1, c] - g[a, c], g[a, c + 1] - g[a, c]))
        if nrm[1] > 0:
            nrm = -nrm
        mano += it.cangrejo_fosil(p + nrm * 0.06, nrm, g[a + 1, c] - g[a, c], rnd, fino)
    # garra del pulgar (1,5) y garritas en los nudillos
    m0, m1 = C.pulgar(lado)
    mano += it.garra(m1 - s.normalizar(m1 - m0) * 0.15, s.normalizar(m1 - m0 + V([0, -0.3, 0.3])), 1.5, 0.3,
                     V([0, 0, -1]), rnd, fino)
    return resultado, sectores


def _lamina_variable(grid, fino, borde_libre):
    """Lámina con grosor que crece hacia los bordes (0,12 -> 0,2)."""
    nu1, nv1, _ = grid.shape
    U, Vv = np.meshgrid(np.linspace(0, 1, nu1), np.linspace(0, 1, nv1), indexing="ij")
    borde = np.minimum.reduce([U, 1 - U, Vv, 1 - Vv])
    gro = 0.12 + 0.08 * (1 - s.smoothstep(0.0, 0.12, borde))
    gu = np.gradient(grid, axis=0)
    gv = np.gradient(grid, axis=1)
    n = np.cross(gu, gv)
    n /= np.maximum(np.linalg.norm(n, axis=2, keepdims=True), 1e-9)
    if np.mean(n[..., 1]) > 0:
        n = -n  # la cara A mira hacia delante (-Y)
    a = grid + n * gro[..., None] / 2
    b = grid - n * gro[..., None] / 2
    Vt = np.vstack([a.reshape(-1, 3), b.reshape(-1, 3)])
    off = nu1 * nv1
    F = []

    def ix(i, j):
        return i * nv1 + j

    for i in range(nu1 - 1):
        for j in range(nv1 - 1):
            p, q, r, t = ix(i, j), ix(i + 1, j), ix(i + 1, j + 1), ix(i, j + 1)
            F += [(p, q, r), (p, r, t), (off + p, off + r, off + q), (off + p, off + t, off + r)]
    borde_ix = [ix(i, 0) for i in range(nu1)] + [ix(nu1 - 1, j) for j in range(1, nv1)] + \
        [ix(i, nv1 - 1) for i in range(nu1 - 2, -1, -1)] + [ix(0, j) for j in range(nv1 - 2, 0, -1)]
    for i in range(len(borde_ix)):
        p, q = borde_ix[i], borde_ix[(i + 1) % len(borde_ix)]
        F += [(q, p, off + p), (q, off + p, off + q)]
    m = it.Malla(Vt, np.asarray(F), nrm=np.vstack([n.reshape(-1, 3), -n.reshape(-1, 3)]))
    return m


# Desgarros reparados (3 por ala) y agujero reciente (ala derecha, cerca de la punta)
PARCHES = {
    "Izq": [("mano0", 0.55, 0.5, 0.9), ("mano2", 0.7, 0.4, 1.1), ("antebrazo", 0.6, 0.55, 1.3)],
    "Der": [("mano1", 0.45, 0.55, 1.0), ("mano2", 0.35, 0.6, 0.8), ("antebrazo", 0.4, 0.65, 1.2)],
}
AGUJERO = ("Der", "mano0", 0.83, 0.55, 0.25)


def _pintar_membrana(resultado, lado, k, fino, rnd):
    """Color rojo sangre muy oscuro (#6B0000), venas ramificadas en relieve, parches más claros y gruesos."""
    for pieza, m in resultado.items():
        m.ajustar()
        n = len(m.v)
        if n == 0:
            continue
        base = PAL["membrana"]
        col = np.tile(base, (n, 1)) * 0.42
        rug = np.full(n, 0.55)
        if fino:
            # venas: ríos ramificados (ruido celular de bordes) + relieve 0,1 en la cara interior
            f1, f2, _, _ = s.voronoi(m.v * V([1, 1, 1]), 1.6, semilla=31 + k)
            g1, g2, _, _ = s.voronoi(m.v, 0.6, semilla=37 + k)
            vena = np.maximum(1 - s.smoothstep(0.0, 0.11, f2 - f1), 0.6 * (1 - s.smoothstep(0.0, 0.05, g2 - g1)))
            vena *= s.fbm(m.v, 1.2, 2, semilla=3) > -0.35
            nm = m.nrm
            m.v = m.v + nm * (vena * 0.1)[:, None]
            col = col * (1 - 0.55 * vena[:, None]) + it.lin("#2A0000")[None, :] * 0.55 * vena[:, None]
            # translucidez fingida: el centro de cada panel algo más claro
            col *= (0.85 + 0.35 * (s.fbm(m.v, 3.0, 3, semilla=9) + 0.5))[:, None]
            rug -= 0.15 * vena
        m.col = col
        m.rme = np.stack([rug, np.zeros(n), np.zeros(n)], 1)
        m.emi = np.zeros((n, 3))


def aplicar_parches(resultado, sectores, lado, fino):
    """Los parches (desgarros reparados): membrana más clara y gruesa con borde cicatrizado."""
    k = 1 if lado == "Izq" else -1
    for sec, u, v, r in PARCHES[lado]:
        pieza = f"Ala_{lado}_Mano" if sec.startswith("mano") else f"Ala_{lado}_Antebrazo"
        g = sectores[sec]
        nu, nv = g.shape[0] - 1, g.shape[1] - 1
        c = g[int(u * nu), int(v * nv)]
        m = resultado[pieza].ajustar()
        d = np.linalg.norm(m.v - c, axis=1)
        forma = r * (1 + 0.25 * np.sin(np.arctan2(m.v[:, 2] - c[2], m.v[:, 1] - c[1]) * 5))
        dentro = s.smoothstep(forma, forma * 0.8, d)
        borde = np.exp(-((d - forma * 0.9) ** 2) / (0.004 + 0.01 * fino))
        m.v = m.v + m.nrm * ((dentro * 0.04 + borde * 0.05) if fino else dentro * 0.03)[:, None]
        m.col = m.col * (1 - dentro[:, None]) + it.lin("#8A2A22")[None, :] * dentro[:, None] * 0.75
        m.col = m.col * (1 - 0.6 * borde[:, None])
        m.rme[:, 0] = m.rme[:, 0] * (1 - dentro) + 0.75 * dentro


def borde_ataque(lado, fino):
    """Escamas reforzadas del borde de ataque (dedo 1): placas pequeñas solapadas, desgastadas."""
    rnd = random.Random(40 + (lado == "Der"))
    k = 1 if lado == "Izq" else -1
    campo = campo_de(f"Ala_{lado}_Mano")
    m = it.Malla()
    for i in range(10):
        t = 0.08 + i * 0.085
        p = _dedo(k, 0, t)
        p2 = _dedo(k, 0, t + 0.02)
        eje = s.normalizar(p2 - p)
        fuera = s.normalizar(np.cross(eje, V([0, 1, 0])) * k)
        if fuera[1] > 0:
            fuera = -fuera
        q = superficie(p, s.normalizar(fuera + V([0, -0.6, 0])), campo)
        sc = it.esfera((0, 0, 0), 0.3 * (1 - t * 0.5), seg=10 if fino else 5, anillos=5 if fino else 3,
                       escala=(1.0, 1.6, 0.45))
        sc = it.orientar(sc, q - fuera * 0.05, s.normalizar(fuera + V([0, -0.6, 0])), arriba=eje)
        sc.pintar(col=it.lin("#1A1010") * (1.2 + 0.5 * rnd.random()), rugosidad=0.4)
        m += sc
    return m


def detalles(fino):
    """{pieza: Malla} con todo el detalle duro y las membranas."""
    out = {}

    def add(p, m):
        if p not in out:
            out[p] = it.Malla()
        out[p] += m

    sup, inf = boca(fino)
    add("Cabeza", sup)
    add("Cabeza", ojos(fino))
    add("Mandibula", inf)
    add("Cornamenta", cornamenta(fino))
    for n in ("Cuello_Base", "Cuello_Medio", "Cuello_Superior"):
        add(n, espinas_cuello(fino, n))
    for n, m in papada(fino).items():
        add(n, m)
    add("Cresta_Dorsal", cresta_dorsal(fino))
    add("Torso", torso(fino))
    add("Cuello_Base", cadenas(fino))
    for lado in ("Izq", "Der"):
        add(f"Pata_Del_{lado}_Garra", garras_del(lado, fino))
        add(f"Pata_Tras_{lado}_Tibia", garras_tras(lado, fino))
        mem, sect = membranas_ala(lado, fino)
        aplicar_parches(mem, sect, lado, fino)
        for n, m in mem.items():
            add(n, m)
        add(f"Ala_{lado}_Mano", borde_ataque(lado, fino))
    for n, m in cola(fino).items():
        add(n, m)
    return out
