"""
Piezas «duras» del Dragón Leviatán, como mallas de numpy: dientes, colmillos, garras, cuernos estriados, espinas,
placas tectónicas, percebes, coral, cadenas, fragmentos de naves, arpones, ojos...

Cada generador devuelve una `Malla`: vértices (N,3) en studs, triángulos (M,3) y, por vértice, el material:
  col (N,3)  color base lineal
  rme (N,3)  rugosidad, metal, fuerza de emisión
  emi (N,3)  color de emisión lineal
Con `fino=True` sale la versión de alta resolución (para hornear el relieve y el color); con `fino=False` la de
juego (pocos triángulos).
"""

import math

import numpy as np

import dragon_sdf as s

# --------------------------------------------------------------------------------------------------------------
# Paleta (hex sRGB, como en el encargo) -> lineal
# --------------------------------------------------------------------------------------------------------------


def lin(hexa):
    hexa = hexa.lstrip("#")
    c = np.array([int(hexa[i : i + 2], 16) / 255 for i in (0, 2, 4)])
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


PAL = {
    "piel": lin("#0A0505"),
    "reflejo": lin("#1A0A15"),
    "vientre": lin("#3A3A3A"),
    "placa": lin("#151010"),
    "grieta": lin("#FF2200"),
    "membrana": lin("#6B0000"),
    "cuerno": lin("#2A1A0A"),
    "ojo": lin("#FF4500"),
    "oro": lin("#FFD700"),
    "boca": lin("#FF4500"),
    "garra": lin("#0A0A0A"),
    "marfil": lin("#D4C8A0"),
    "colmillo": lin("#E8DCC8"),
    "sangre": lin("#8B0000"),
    "metal": lin("#6A6A6A"),
    "oxido": lin("#8B4513"),
    "cadena": lin("#1A0A1A"),
    "coral_rojo": lin("#8B0000"),
    "coral_negro": lin("#1A1A1A"),
    "percebe": lin("#C8C8C8"),
    "musgo": lin("#0A0A0A"),
    "casco_nave": lin("#5A6878"),
    "hueso": lin("#B8A888"),
}


def al(rnd, n):
    """n números aleatorios en [0, 1) de un random.Random (para que todo sea reproducible por semilla)."""
    return np.array([rnd.random() for _ in range(n)])


class Malla:
    def __init__(self, v=None, f=None, col=None, rme=None, emi=None, nrm=None):
        self.v = np.zeros((0, 3)) if v is None else np.asarray(v, dtype=np.float64)
        self.f = np.zeros((0, 3), dtype=np.int64) if f is None else np.asarray(f, dtype=np.int64)
        n = len(self.v)
        self.col = np.zeros((n, 3)) if col is None else np.asarray(col, dtype=np.float64)
        self.rme = np.tile([0.6, 0.0, 0.0], (n, 1)) if rme is None else np.asarray(rme, dtype=np.float64)
        self.emi = np.zeros((n, 3)) if emi is None else np.asarray(emi, dtype=np.float64)
        # normal "de membrana" opcional (para desplazar láminas finas); ceros si no se usa
        self.nrm = np.zeros((n, 3)) if nrm is None else np.asarray(nrm, dtype=np.float64)

    def ajustar(self):
        """Rellena los atributos por vértice si algún generador añadió vértices sin ellos."""
        n = len(self.v)
        for nombre, defecto in (("col", (0, 0, 0)), ("rme", (0.6, 0, 0)), ("emi", (0, 0, 0)), ("nrm", (0, 0, 0))):
            a = getattr(self, nombre)
            if len(a) < n:
                a = np.vstack([a, np.tile(defecto, (n - len(a), 1))])
            setattr(self, nombre, a[:n])
        return self

    def __iadd__(self, o):
        self.ajustar()
        o.ajustar()
        base = len(self.v)
        self.v = np.vstack([self.v, o.v])
        self.f = np.vstack([self.f, o.f + base])
        self.col = np.vstack([self.col, o.col])
        self.rme = np.vstack([self.rme, o.rme])
        self.emi = np.vstack([self.emi, o.emi])
        self.nrm = np.vstack([self.nrm, o.nrm])
        return self

    def pintar(self, col=None, rugosidad=None, metal=None, emision=None, color_emision=None):
        n = len(self.v)
        if col is not None:
            self.col = np.broadcast_to(np.asarray(col, dtype=np.float64), (n, 3)).copy()
        if rugosidad is not None:
            self.rme[:, 0] = rugosidad
        if metal is not None:
            self.rme[:, 1] = metal
        if emision is not None:
            self.rme[:, 2] = emision
        if color_emision is not None:
            self.emi = np.broadcast_to(np.asarray(color_emision, dtype=np.float64), (n, 3)).copy()
        return self

    def transformar(self, R=None, t=None):
        if R is not None:
            self.v = self.v @ np.asarray(R).T
        if t is not None:
            self.v = self.v + np.asarray(t)
        return self

    def copia(self):
        return Malla(self.v.copy(), self.f.copy(), self.col.copy(), self.rme.copy(), self.emi.copy(), self.nrm.copy())

    @property
    def tris(self):
        return len(self.f)


def unir(mallas):
    m = Malla()
    for x in mallas:
        m += x
    return m


# --------------------------------------------------------------------------------------------------------------
# Geometría base: tubos curvos con sección variable (todo lo alargado sale de aquí)
# --------------------------------------------------------------------------------------------------------------


def marcos(camino, arriba=(0, 0, 1)):
    """Marcos de transporte paralelo a lo largo de un camino (K,3): devuelve T, U, W (K,3) cada uno."""
    camino = np.asarray(camino, dtype=np.float64)
    K = len(camino)
    T = np.gradient(camino, axis=0)
    nt = np.linalg.norm(T, axis=1, keepdims=True)
    for i in range(K):  # tramos de longitud cero: heredan la tangente vecina
        if nt[i, 0] < 1e-9:
            T[i] = T[i - 1] if i > 0 else np.array([0.0, 0.0, 1.0])
            nt[i, 0] = max(np.linalg.norm(T[i]), 1e-9)
    T = T / nt
    u, _, _ = s.base_ortonormal(T[0], arriba)
    U = np.zeros_like(camino)
    U[0] = u
    for i in range(1, K):
        u = U[i - 1] - T[i] * np.dot(U[i - 1], T[i])
        n = np.linalg.norm(u)
        u = u / n if n > 1e-9 else s.base_ortonormal(T[i], arriba)[0]
        U[i] = u
    W = np.cross(T, U)
    return T, U, W


def tubo(camino, radios, lados=8, tapa_ini=True, tapa_fin=True, perfil=None, arriba=(0, 0, 1), punta=False,
         giro=0.0):
    """
    Tubo por un camino (K,3) con radio por anillo. `perfil(t, ang) -> (fx, fy)` deforma la sección (fx, fy
    multiplican al radio en los ejes U y W): sirve para hojas aplanadas, filos y estrías.
    Si `punta`, el último anillo se cierra en un vértice (puntas de dientes, cuernos, garras).
    """
    camino = np.asarray(camino, dtype=np.float64)
    K = len(camino)
    T, U, W = marcos(camino, arriba)
    radios = np.broadcast_to(np.asarray(radios, dtype=np.float64), (K,))
    ang = giro + np.linspace(0, math.tau, lados, endpoint=False)
    verts = []
    anillos = K - 1 if punta else K
    for i in range(anillos):
        t = i / max(K - 1, 1)
        if perfil is not None:
            fx, fy = perfil(t, ang)
        else:
            fx = fy = np.ones(lados)
        r = radios[i]
        pts = camino[i] + np.outer(np.cos(ang) * r * fx, U[i]) + np.outer(np.sin(ang) * r * fy, W[i])
        verts.append(pts)
    v = np.vstack(verts)
    caras = []
    for i in range(anillos - 1):
        for j in range(lados):
            a = i * lados + j
            b = i * lados + (j + 1) % lados
            c = (i + 1) * lados + (j + 1) % lados
            d = (i + 1) * lados + j
            caras += [(a, b, c), (a, c, d)]
    extra = []
    if punta:
        ip = len(v)
        extra.append(camino[-1])
        base = (anillos - 1) * lados
        for j in range(lados):
            caras.append((base + j, base + (j + 1) % lados, ip))
    if tapa_ini:
        ic = len(v) + len(extra)
        extra.append(camino[0])
        for j in range(lados):
            caras.append(((j + 1) % lados, j, ic))
    if tapa_fin and not punta:
        ic = len(v) + len(extra)
        extra.append(camino[-1])
        base = (anillos - 1) * lados
        for j in range(lados):
            caras.append((base + j, base + (j + 1) % lados, ic))
    if extra:
        v = np.vstack([v, np.asarray(extra)])
    m = Malla(v, np.asarray(caras))
    return m


def curva(a, direccion, largo, curvatura, hacia, n):
    """Camino curvo: sale de `a` en `direccion` y se dobla hacia `hacia` (`curvatura` en fracción del largo)."""
    a = np.asarray(a, dtype=np.float64)
    d = s.normalizar(direccion)
    h = np.asarray(hacia, dtype=np.float64)
    h = h - d * np.dot(h, d)
    h = h / (np.linalg.norm(h) + 1e-9)
    t = np.linspace(0, 1, n)[:, None]
    return a + d * largo * t + h * curvatura * largo * t**2


def esfera(c, r, seg=10, anillos=6, escala=(1, 1, 1)):
    c = np.asarray(c, dtype=np.float64)
    vs = [c + np.array([0, 0, -r * escala[2]])]
    for i in range(1, anillos):
        th = math.pi * i / anillos
        for j in range(seg):
            ph = math.tau * j / seg
            vs.append(c + np.array([math.sin(th) * math.cos(ph) * r * escala[0],
                                    math.sin(th) * math.sin(ph) * r * escala[1], -math.cos(th) * r * escala[2]]))
    vs.append(c + np.array([0, 0, r * escala[2]]))
    f = []
    for j in range(seg):
        f.append((0, 1 + (j + 1) % seg, 1 + j))
    for i in range(anillos - 2):
        for j in range(seg):
            a = 1 + i * seg + j
            b = 1 + i * seg + (j + 1) % seg
            f += [(a, b, b + seg), (a, b + seg, a + seg)]
    top = len(vs) - 1
    base = 1 + (anillos - 2) * seg
    for j in range(seg):
        f.append((base + j, base + (j + 1) % seg, top))
    return Malla(np.asarray(vs), np.asarray(f))


def orientar(m, origen, eje_z, arriba=(0, 0, 1)):
    """Lleva una malla modelada en local (Z = eje) a `origen` con su Z apuntando a `eje_z`."""
    u, v, w = s.base_ortonormal(eje_z, arriba)
    R = np.stack([u, v, w], axis=1)
    return m.transformar(R, origen)


# --------------------------------------------------------------------------------------------------------------
# Dientes, colmillos, garras, cuernos y espinas
# --------------------------------------------------------------------------------------------------------------


def _ruido_lineal(n, rnd, amp):
    return 1 + amp * (al(rnd, n) - 0.5)


def diente(base, direccion, largo, radio, hacia, rnd, fino, curvatura=0.18, aplanado=0.62, aserrado=False,
           roto=None, estrias=False, tipo="lateral", hundido=0.35):
    """
    Diente/colmillo cónico curvo de sección aplanada (de cuchilla). `roto` = fracción del largo que queda
    (punta partida con corte astillado). `hundido`: parte de la raíz metida en la encía (sin hueco visible).
    """
    n = 14 if fino else 5
    lados = 18 if fino else 6
    a = np.asarray(base, dtype=np.float64) - s.normalizar(direccion) * radio * hundido
    L = largo + radio * hundido
    camino = curva(a, direccion, L, curvatura, hacia, n)
    t = np.linspace(0, 1, n)
    rad = radio * (1 - t) ** 0.85 + 0.02
    if roto is not None:
        k = max(2, int(round(roto * (n - 1))) + 1)
        camino = camino[:k]
        rad = rad[:k]

    def perfil(tt, ang):
        fy = np.full_like(ang, aplanado)
        fx = np.ones_like(ang)
        if aserrado and fino:
            # Filo en sierra en el borde delantero y trasero (dientecillos).
            filo = np.abs(np.cos(ang)) ** 6
            fx = fx + filo * 0.12 * (np.sin(tt * 40) > 0)
        return fx, fy

    m = tubo(camino, rad, lados=lados, tapa_ini=True, tapa_fin=roto is not None, perfil=perfil,
             punta=roto is None, arriba=hacia)
    if roto is not None:
        # Corte astillado en diagonal: el último anillo se inclina y se mella.
        last = len(camino) - 1
        idx = np.arange(last * lados, (last + 1) * lados)
        T, U, W = marcos(camino, hacia)
        inc = (m.v[idx] - camino[last]) @ U[last]
        m.v[idx] += np.outer(inc * 0.55 + al(rnd, lados) * 0.06 * radio, T[last])
    # Color: raíz más oscura (encía, sangre seca), cuerpo de marfil, punta clara; estrías rojas en colmillos.
    eje = s.normalizar(direccion)
    h = np.clip(((m.v - a) @ eje) / L, 0, 1)
    marfil = PAL["colmillo"] if tipo == "colmillo" else PAL["marfil"]
    col = marfil[None, :] * (0.55 + 0.45 * h[:, None]) + PAL["sangre"][None, :] * 0.25 * (1 - h[:, None]) ** 3
    if estrias:
        ang = np.arctan2((m.v - a) @ s.base_ortonormal(eje, hacia)[1], (m.v - a) @ s.base_ortonormal(eje, hacia)[0])
        raya = s.smoothstep(0.75, 0.95, np.sin(ang * 5 + h * 3.0) * 0.5 + 0.5)
        col = col * (1 - 0.65 * raya[:, None]) + PAL["sangre"][None, :] * 0.65 * raya[:, None]
    m.col = col
    m.rme = np.stack([0.35 + 0.25 * (1 - h), np.zeros_like(h), np.zeros_like(h)], axis=1)
    return m


def garra(base, direccion, largo, radio, hacia, rnd, fino, roto=False, trasera=False):
    """Garra de cuchilla negra, curvada hacia el suelo, con arañazos claros y manchas de lo que ha matado."""
    n = 12 if fino else 5
    lados = 14 if fino else 6
    camino = curva(base, direccion, largo, 0.38, hacia, n)
    t = np.linspace(0, 1, n)
    rad = radio * (1 - t) ** 0.7 + 0.015

    def perfil(tt, ang):
        # Sección de cuchilla: estrecha de lado, alta por el lomo, con filo inferior.
        fx = np.full_like(ang, 0.55)
        fy = 1.0 + 0.25 * (np.sin(ang) > 0)
        return fx, fy

    m = tubo(camino, rad, lados=lados, punta=not roto, tapa_fin=roto, perfil=perfil, arriba=hacia)
    h = np.clip(((m.v - base) @ s.normalizar(direccion)) / largo, 0, 1)
    col = np.tile(PAL["garra"], (len(m.v), 1))
    if fino:
        ruido = s.fbm(m.v * 3, 0.6, 3, semilla=rnd.randint(0, 999))
        aranazo = s.smoothstep(0.55, 0.75, np.abs(np.sin(m.v @ np.array([7.0, 3.0, 11.0]) + ruido * 4)))
        col = col + 0.06 * aranazo[:, None]
        mancha = s.smoothstep(0.1, 0.5, ruido) * (1 - h)
        col = col * (1 - 0.3 * mancha[:, None]) + PAL["sangre"][None, :] * 0.12 * mancha[:, None]
    m.col = col
    m.rme = np.stack([0.22 + 0.2 * (1 - h), np.zeros_like(h), np.zeros_like(h)], axis=1)
    return m


def cuerno(base, direccion, largo, radio, hacia, rnd, fino, curvatura=0.45, roto=None, giro_espiral=0.0,
           desgaste=0.15):
    """Cuerno de hueso oscuro con anillos de crecimiento (estrías) y vetas rojas; punta desgastada."""
    n = 26 if fino else 8
    lados = 20 if fino else 7
    camino = curva(base, direccion, largo, curvatura, hacia, n)
    t = np.linspace(0, 1, n)
    rad = radio * (1 - t * (1 - desgaste * 0.3)) ** 1.15 + 0.03
    if fino:
        # Anillos de crecimiento milenario: el radio ondula a lo largo.
        rad = rad * (1 + 0.07 * np.abs(np.sin(t * 34)) ** 0.5 * (1 - t))
    if roto is not None:
        k = max(2, int(round(roto * (n - 1))) + 1)
        camino, rad = camino[:k], rad[:k]

    def perfil(tt, ang):
        # Surcos longitudinales (estrías) + algo aplanado.
        f = 1 + (0.05 * np.cos(ang * 7 + tt * giro_espiral) if fino else 0)
        return f * 1.0, f * 0.85

    m = tubo(camino, rad, lados=lados, punta=roto is None, tapa_fin=roto is not None, perfil=perfil, arriba=hacia)
    if roto is not None:
        last = len(camino) - 1
        idx = np.arange(last * lados, (last + 1) * lados)
        T, U, W = marcos(camino, hacia)
        inc = (m.v[idx] - camino[last]) @ U[last]
        m.v[idx] += np.outer(inc * 0.7 + al(rnd, lados) * 0.15 * radio, T[last])
    h = np.clip(((m.v - base) @ s.normalizar(direccion)) / largo, 0, 1)
    col = np.tile(PAL["cuerno"], (len(m.v), 1)) * (0.8 + 0.4 * h[:, None])
    if fino:
        veta = s.smoothstep(0.62, 0.9, s.fbm(m.v * np.array([1, 1, 3.0]), 0.5, 3, semilla=rnd.randint(0, 999)) + 0.5)
        col = col * (1 - 0.6 * veta[:, None]) + PAL["sangre"][None, :] * 0.6 * veta[:, None]
        anillo = (np.abs(np.sin(h * 34)) < 0.25).astype(float) * (1 - h)
        col = col * (1 - 0.35 * anillo[:, None])
    m.col = col
    m.rme = np.stack([0.55 - 0.25 * h, np.zeros_like(h), np.zeros_like(h)], axis=1)
    return m


def espina(base, direccion, largo, radio, hacia, rnd, fino, curvatura=0.25, roto=None, brillo=0.0,
           color=None, aplanado=0.55, corte_limpio=False):
    """Espina ósea de cresta (sección aplanada de lado). `brillo`: emisión en la base (lava por dentro)."""
    n = 10 if fino else 4
    lados = 12 if fino else 5
    camino = curva(base, direccion, largo, curvatura, hacia, n)
    t = np.linspace(0, 1, n)
    rad = radio * (1 - t) ** 0.9 + 0.02
    if roto is not None:
        k = max(2, int(round(roto * (n - 1))) + 1)
        camino, rad = camino[:k], rad[:k]

    def perfil(tt, ang):
        return np.full_like(ang, aplanado), np.ones_like(ang)

    m = tubo(camino, rad, lados=lados, punta=roto is None, tapa_fin=roto is not None, perfil=perfil, arriba=hacia,
             giro=math.pi / 2)
    if roto is not None and not corte_limpio:
        last = len(camino) - 1
        idx = np.arange(last * lados, (last + 1) * lados)
        T, _, _ = marcos(camino, hacia)
        m.v[idx] += np.outer((al(rnd, lados) - 0.3) * 0.25 * radio, T[last])
    h = np.clip(((m.v - base) @ s.normalizar(direccion)) / largo, 0, 1)
    c0 = PAL["placa"] if color is None else color
    col = np.tile(c0, (len(m.v), 1)) * (1.0 + 0.8 * h[:, None])
    m.col = col
    em = brillo * (1 - s.smoothstep(0.0, 0.35, h))
    m.rme = np.stack([0.5 - 0.15 * h, np.zeros_like(h), em], axis=1)
    m.emi = np.tile(PAL["boca"], (len(m.v), 1)) * (em > 0)[:, None]
    if corte_limpio and roto is not None:
        # Corte limpio de arma humana: la cara del corte es hueso claro.
        last_ring = (len(camino) - 1) * lados
        m.col[last_ring:] = PAL["hueso"]
    return m


# --------------------------------------------------------------------------------------------------------------
# Placas tectónicas, percebes, coral, nido
# --------------------------------------------------------------------------------------------------------------


def placa(centro, normal, adelante, largo, ancho, grosor, rnd, fino, grietas=0.6):
    """
    Placa ósea dorsal de piedra volcánica: contorno irregular y astillado, cara superior abombada y agrietada.
    Las grietas brillan rojo (#FF2200) como lava solidificándose.
    """
    angs = 40 if fino else 11
    anillos = 7 if fino else 2
    n = s.normalizar(normal)
    f = s.normalizar(np.asarray(adelante) - n * np.dot(adelante, n))
    l = np.cross(n, f)
    sem = rnd.randint(0, 9999)
    ang = np.linspace(0, math.tau, angs, endpoint=False)
    # Contorno: superelipse con muescas (impactos).
    r_borde = np.ones(angs)
    for _ in range(3):
        a0 = rnd.random() * math.tau
        r_borde -= 0.18 * np.exp(-((np.angle(np.exp(1j * (ang - a0)))) ** 2) / 0.02)
    r_borde *= 1 + 0.08 * np.sin(ang * 3 + rnd.random() * 6) + 0.05 * (np.array([rnd.random() for _ in ang]) - 0.5)
    ca, sa = np.cos(ang), np.sin(ang)
    ex = np.sign(ca) * np.abs(ca) ** 0.75 * largo / 2
    ey = np.sign(sa) * np.abs(sa) ** 0.75 * ancho / 2
    verts = []
    # anillos de la cara superior (de fuera hacia dentro) + centro
    for k in range(anillos + 1):
        q = 1 - k / (anillos + 1)
        x = ex * r_borde * q
        y = ey * r_borde * q
        alt = grosor * (0.55 + 0.45 * (1 - q**2))  # abombada
        pts = centro + np.outer(x, f) + np.outer(y, l) + np.outer(np.full(angs, alt), n)
        verts.append(pts)
    centro_sup = centro + n * grosor * 1.02
    # cara inferior (un anillo algo metido + centro hundido en la carne)
    inf = centro + np.outer(ex * r_borde * 0.92, f) + np.outer(ey * r_borde * 0.92, l) - np.outer(
        np.full(angs, grosor * 0.6), n)
    v = np.vstack(verts + [inf, centro_sup[None, :], (centro - n * grosor)[None, :]])
    ic_sup = len(v) - 2
    ic_inf = len(v) - 1
    fcs = []
    for k in range(anillos):
        for j in range(angs):
            a = k * angs + j
            b = k * angs + (j + 1) % angs
            fcs += [(a, b, b + angs), (a, b + angs, a + angs)]
    last = anillos * angs
    for j in range(angs):
        fcs.append((last + j, last + (j + 1) % angs, ic_sup))
    # pared lateral: anillo 0 (borde superior) -> inferior
    b0 = (anillos + 1) * angs
    for j in range(angs):
        a, b = j, (j + 1) % angs
        fcs += [(b, a, b0 + a), (b, b0 + a, b0 + b)]
        fcs.append((b0 + b, b0 + a, ic_inf))
    m = Malla(v, np.asarray(fcs))
    if fino:
        # Relieve de piedra + grietas: surcos que se hunden y brillan.
        P = m.v
        rel = s.fbm(P, 0.7, 4, semilla=sem)
        m.v = P + np.outer(rel * grosor * 0.18, n)
        f1, f2, _, _ = s.voronoi(P, 0.9, semilla=sem)
        borde = f2 - f1
        grieta = 1 - s.smoothstep(0.0, 0.07, borde)
        arriba = ((P - centro) @ n) > grosor * 0.35
        grieta = grieta * arriba * (s.fbm(P, 1.2, 2, semilla=sem + 5) > -0.25)
        m.v = m.v - np.outer(grieta * grosor * 0.12, n)
        col = np.tile(PAL["placa"], (len(P), 1)) * (0.8 + 0.6 * (rel[:, None] + 0.5))
        borde_astillado = s.smoothstep(0.6, 1.0, np.linalg.norm(
            np.stack([(P - centro) @ f / (largo / 2), (P - centro) @ l / (ancho / 2)], 1), axis=1))
        col = col * (1 + 0.8 * borde_astillado[:, None])  # bordes de impacto más claros (roca viva)
        em = grieta * grietas
        m.col = col * (1 - grieta[:, None]) + PAL["grieta"][None, :] * 0.4 * grieta[:, None]
        m.rme = np.stack([0.8 - 0.3 * grieta, np.zeros(len(P)), em], axis=1)
        m.emi = np.tile(PAL["grieta"], (len(P), 1))
    else:
        m.pintar(col=PAL["placa"], rugosidad=0.8)
    return m


def percebe(base, normal, alto, radio, rnd, fino, roto=False):
    """Percebe cósmico: cono truncado con cráter (abertura) arriba y placas a los lados."""
    lados = 12 if fino else 6
    n = s.normalizar(normal)
    camino = np.array([base - n * 0.08, base + n * alto * 0.55, base + n * alto])
    rad = np.array([radio, radio * 0.78, radio * 0.45])
    if roto:
        camino[2] = base + n * alto * 0.6
        rad[2] = radio * 0.7

    def perfil(tt, ang):
        f = 1 + (0.12 * np.cos(ang * 6) if fino else 0)
        return f, f

    m = tubo(camino, rad, lados=lados, tapa_ini=True, tapa_fin=False, perfil=perfil, arriba=(0.3, 0.2, 0.9))
    # cráter: un anillo interior hundido
    T, U, W = marcos(camino, (0.3, 0.2, 0.9))
    ang = np.linspace(0, math.tau, lados, endpoint=False)
    interior = camino[2] - n * alto * 0.35 + np.outer(np.cos(ang) * rad[2] * 0.5, U[2]) + np.outer(
        np.sin(ang) * rad[2] * 0.5, W[2])
    base_idx = len(m.v)
    m.v = np.vstack([m.v, interior, (camino[2] - n * alto * 0.4)[None, :]])
    top = 2 * lados
    fcs = list(m.f)
    for j in range(lados):
        a, b = top + j, top + (j + 1) % lados
        c, d = base_idx + (j + 1) % lados, base_idx + j
        fcs += [(a, b, c), (a, c, d)]
        fcs.append((d, c, base_idx + lados))
    m.f = np.asarray(fcs)
    h = np.clip(((m.v - base) @ n) / alto, 0, 1)
    col = np.tile(PAL["percebe"], (len(m.v), 1)) * (0.55 + 0.45 * h[:, None])
    col[base_idx:] = PAL["percebe"] * 0.15  # dentro oscuro
    m.col = col
    m.rme = np.tile([0.85, 0, 0], (len(m.v), 1))
    m.emi = np.zeros_like(m.v)
    return m


def coral(base, normal, alto, rnd, fino, color):
    """Coral cósmico ramificado (ramas que se bifurcan y engordan en las puntas)."""
    piezas = []
    n = s.normalizar(normal)

    def rama(p, d, largo, r, nivel):
        q = p + d * largo
        cam = np.array([p, p + d * largo * 0.5 + (al(rnd, 3) - 0.5) * largo * 0.15, q])
        piezas.append(tubo(cam, [r, r * 0.85, r * 0.75], lados=8 if fino else 4, tapa_ini=False, tapa_fin=False))
        piezas.append(esfera(q, r * 0.95, seg=8 if fino else 4, anillos=5 if fino else 3))
        if nivel < (3 if fino else 2):
            for _ in range(2):
                nd = s.normalizar(d + (al(rnd, 3) - 0.5) * 1.2 + n * 0.3)
                rama(q, nd, largo * 0.7, r * 0.72, nivel + 1)

    for k in range(3):
        d0 = s.normalizar(n + (al(rnd, 3) - 0.5) * 0.9)
        rama(np.asarray(base) - n * 0.15, d0, alto * 0.45, alto * 0.09, 0)
    m = unir(piezas)
    h = np.clip(((m.v - base) @ n) / alto, 0, 1)
    m.col = np.asarray(color)[None, :] * (0.6 + 0.8 * h[:, None])
    m.rme = np.tile([0.75, 0, 0], (len(m.v), 1))
    if np.allclose(color, PAL["coral_rojo"]):
        # Las puntas del coral rojo brillan un poco (como los líquenes).
        m.rme[:, 2] = 0.6 * s.smoothstep(0.75, 1.0, h)
        m.emi = np.tile(PAL["grieta"], (len(m.v), 1))
    return m


def nido(centro, normal, radio, rnd, fino):
    """Nido vacío de criatura parásita: cuenco de fibras endurecidas."""
    n = s.normalizar(normal)
    u, v, _ = s.base_ortonormal(n)
    piezas = []
    # cuenco: media esfera hueca (dos capas)
    seg = 16 if fino else 8
    for k, rr in enumerate((radio, radio * 0.82)):
        ang = np.linspace(0, math.tau, seg, endpoint=False)
        anillos = []
        for i in range(5):
            th = math.pi / 2 * i / 4
            pts = centro + np.outer(np.cos(ang) * math.sin(th) * rr, u) + np.outer(np.sin(ang) * math.sin(th) * rr, v) \
                - n * (math.cos(th) * rr * 0.6 - rr * 0.35 * k * 0)
            anillos.append(pts)
        V = np.vstack(anillos)
        F = []
        for i in range(4):
            for j in range(seg):
                a = i * seg + j
                b = i * seg + (j + 1) % seg
                F += [(a, b + seg, b), (a, a + seg, b + seg)] if k == 0 else [(a, b, b + seg), (a, b + seg, a + seg)]
        piezas.append(Malla(V, np.asarray(F)))
    # borde que une las dos capas
    ext = piezas[0]
    inte = piezas[1]
    m = unir([ext, inte])
    off = len(ext.v)
    F = list(m.f)
    for j in range(seg):
        a = 4 * seg + j
        b = 4 * seg + (j + 1) % seg
        F += [(a, b, off + b), (a, off + b, off + a)]
    m.f = np.asarray(F)
    # fibras sueltas en el borde
    for _ in range(10 if fino else 4):
        a = rnd.random() * math.tau
        p = centro + (np.cos(a) * u + np.sin(a) * v) * radio
        d = s.normalizar(np.cos(a + 1.3) * u + np.sin(a + 1.3) * v + n * 0.3)
        m += tubo(curva(p, d, radio * 0.9, 0.3, n, 4), [0.05, 0.04, 0.03, 0.01], lados=4, punta=True)
    m.col = np.tile(lin("#2A2018"), (len(m.v), 1))
    m.rme = np.tile([0.9, 0, 0], (len(m.v), 1))
    m.emi = np.zeros_like(m.v)
    return m


# --------------------------------------------------------------------------------------------------------------
# Metal: cadenas, arpones, lanza, casco de nave
# --------------------------------------------------------------------------------------------------------------


def eslabon(centro, eje_largo, eje_plano, largo, grosor, fino, roto=False, retorcido=0.0):
    """Eslabón (toro alargado). `roto`: abierto (le falta un trozo)."""
    seg = 18 if fino else 8
    lados = 8 if fino else 4
    L = s.normalizar(eje_largo)
    Pn = s.normalizar(eje_plano)
    Pn = s.normalizar(Pn - L * np.dot(Pn, L))
    N = np.cross(L, Pn)
    ang = np.linspace(0, math.tau, seg, endpoint=not roto)
    if roto:
        ang = np.linspace(0.5, math.tau - 0.5, seg)
    a = largo / 2 - grosor / 2
    b = largo * 0.32
    camino = []
    for t in ang:
        x = math.cos(t) * a
        y = math.sin(t) * b
        z = math.sin(t * 2) * retorcido
        camino.append(centro + L * x + Pn * y + N * z)
    camino = np.asarray(camino)
    if not roto:
        camino = np.vstack([camino, camino[:1]])
    m = tubo(camino, grosor / 2, lados=lados, tapa_ini=roto, tapa_fin=roto, arriba=N)
    if not roto:
        # cerrar el anillo: soldamos el último anillo con el primero
        K = len(camino)
        m.v = m.v[: (K - 1) * lados]
        F = []
        for i in range(K - 1):
            for j in range(lados):
                i2 = (i + 1) % (K - 1)
                aa = i * lados + j
                bb = i * lados + (j + 1) % lados
                cc = i2 * lados + (j + 1) % lados
                dd = i2 * lados + j
                F += [(aa, bb, cc), (aa, cc, dd)]
        m = Malla(m.v, np.asarray(F))
    m.col = np.tile(PAL["cadena"], (len(m.v), 1))
    m.rme = np.tile([0.4, 0.85, 0], (len(m.v), 1))
    m.emi = np.zeros_like(m.v)
    return m


def cadena(puntos, eslabon_largo, grosor, rnd, fino, rotos=()):
    """Cadena que sigue una polilínea: eslabones alternados 90°, algunos rotos y retorcidos."""
    puntos = np.asarray(puntos, dtype=np.float64)
    # remuestreo por longitud
    seg = np.linalg.norm(np.diff(puntos, axis=0), axis=1)
    acum = np.concatenate([[0], np.cumsum(seg)])
    paso = eslabon_largo * 0.72
    n = int(acum[-1] / paso)
    m = Malla()
    for i in range(n):
        d = i * paso + paso / 2
        k = np.searchsorted(acum, d) - 1
        k = min(max(k, 0), len(seg) - 1)
        t = (d - acum[k]) / seg[k]
        c = puntos[k] + (puntos[k + 1] - puntos[k]) * t
        eje = puntos[k + 1] - puntos[k]
        plano = np.array([1.0, 0.0, 0.0]) if i % 2 == 0 else np.cross(s.normalizar(eje), [1.0, 0.0, 0.0])
        if np.linalg.norm(plano - s.normalizar(eje) * np.dot(plano, s.normalizar(eje))) < 1e-3:
            plano = np.array([0.0, 1.0, 0.0])
        m += eslabon(c, eje, plano, eslabon_largo, grosor, fino, roto=i in rotos, retorcido=0.06 * rnd.random())
    if fino:
        ox = s.smoothstep(0.2, 0.7, s.fbm(m.v, 0.4, 3, semilla=7) + 0.3)
        m.col = PAL["cadena"][None, :] * (1 - ox[:, None]) + PAL["oxido"][None, :] * 0.35 * ox[:, None]
        m.rme = np.stack([0.35 + 0.5 * ox, 0.85 - 0.5 * ox, np.zeros(len(m.v))], 1)
    return m


def metal_oxidado(m, sem, intensidad=0.6, base=None):
    """Pinta una malla como metal gris oxidado (#6A6A6A + #8B4513)."""
    P = m.v
    ox = s.smoothstep(-0.1, 0.5, s.fbm(P, 0.5, 4, semilla=sem)) * intensidad
    b = PAL["metal"] if base is None else base
    m.col = b[None, :] * (1 - ox[:, None]) + PAL["oxido"][None, :] * ox[:, None]
    m.rme = np.stack([0.35 + 0.55 * ox, 0.9 - 0.6 * ox, np.zeros(len(P))], 1)
    m.emi = np.zeros_like(P)
    return m


def arpon(punta_en_carne, direccion, asta, rnd, fino, cuerda=True, solo_punta=False, sobresale=1.5):
    """
    Arpón: punta con lengüetas clavada en la carne y asta que sobresale. Si `solo_punta`, sale la punta rota con
    un muñón de asta (1,5 studs fuera). Con cuerda podrida colgando.
    """
    d = s.normalizar(direccion)  # hacia fuera de la carne
    u, v, _ = s.base_ortonormal(d)
    piezas = []
    base = np.asarray(punta_en_carne, dtype=np.float64)
    largo_fuera = sobresale if solo_punta else asta
    # asta
    cam = np.array([base - d * 0.6, base + d * largo_fuera * 0.5, base + d * largo_fuera])
    piezas.append(tubo(cam, [0.11, 0.1, 0.09], lados=10 if fino else 5))
    if solo_punta:
        # punta en forma de hoja con lengüetas, medio fuera de la carne
        cab = base + d * 0.15
        hoja = tubo(np.array([cab - d * 0.1, cab + d * 0.25, cab + d * 0.9]), [0.12, 0.32, 0.02],
                    lados=4, punta=False, perfil=lambda t, a: (np.ones_like(a), np.full_like(a, 0.25)))
        hoja.v = 2 * cab - hoja.v  # invertida: la punta hacia dentro, las lengüetas hacia fuera
        piezas.append(hoja)
        for k in (1, -1):
            piezas.append(tubo(np.array([cab + u * 0.1 * k, cab + u * 0.35 * k + d * 0.25]), [0.05, 0.01], lados=4,
                               punta=True))
    else:
        # anillo de amarre y cuerda colgando
        anillo = eslabon(base + d * (asta - 0.15), d, u, 0.36, 0.06, fino)
        piezas.append(anillo)
    m = metal_oxidado(unir(piezas), rnd.randint(0, 999))
    if cuerda:
        p0 = base + d * (largo_fuera * 0.8)
        cam = [p0]
        for i in range(1, 7):
            cam.append(p0 + d * 0.15 * i + np.array([0.05 * math.sin(i), 0.04 * math.cos(i * 1.3), -0.32 * i]))
        cu = tubo(np.asarray(cam), np.linspace(0.06, 0.035, len(cam)), lados=6 if fino else 4, tapa_fin=True)
        cu.col = np.tile(lin("#3A2E1E"), (len(cu.v), 1))
        cu.rme = np.tile([0.95, 0, 0], (len(cu.v), 1))
        if fino:
            podrido = s.smoothstep(0.0, 0.6, s.fbm(cu.v, 0.3, 3, semilla=3))
            cu.col = cu.col * (1 - 0.5 * podrido[:, None]) + lin("#1E2A12")[None, :] * 0.5 * podrido[:, None]
        m += cu
    return m


def lanza_rota(punto, direccion, visible, rnd, fino):
    """Lanza partida entre dos placas: asta astillada (0,8 studs fuera)."""
    d = s.normalizar(direccion)
    cam = np.array([punto - d * 1.0, punto + d * visible * 0.6, punto + d * visible])
    m = tubo(cam, [0.13, 0.12, 0.11], lados=10 if fino else 5, tapa_fin=True)
    # astillas en el extremo
    last = 2 * (10 if fino else 5)
    lados = 10 if fino else 5
    m.v[last:last + lados] += np.outer(al(rnd, lados) * 0.25, d)
    m = metal_oxidado(m, rnd.randint(0, 99), intensidad=0.75, base=lin("#4A4440"))
    # la punta sigue dentro: no se ve
    return m


def casco_nave(centro, normal, adelante, ancho, alto, rnd, fino, grosor=0.12):
    """
    Fragmento de casco de nave humana (gris azulado) retorcido y con bordes rotos, remaches y una ventana rota.
    Va encajado entre dos placas dorsales, con musgo cósmico creciendo encima.
    """
    n = s.normalizar(normal)
    f = s.normalizar(np.asarray(adelante) - n * np.dot(adelante, n))
    l = np.cross(n, f)
    nu, nv = (24, 16) if fino else (7, 5)
    us = np.linspace(-0.5, 0.5, nu)
    vs = np.linspace(-0.5, 0.5, nv)
    sem = rnd.randint(0, 999)
    U, Vv = np.meshgrid(us, vs, indexing="ij")
    # borde roto: recortamos con un contorno irregular (las celdas fuera se descartan)
    borde = 0.5 - 0.09 * (np.sin(U * 17 + 1) + np.cos(Vv * 13 + 2)) * 0.5 - 0.06 * np.abs(np.sin((U + Vv) * 23))
    dentro = (np.maximum(np.abs(U) * 1.0, np.abs(Vv)) < borde)
    # forma: chapa curvada (fuselaje) y retorcida
    X = U * ancho
    Y = Vv * alto
    Z = -0.25 * (U * 2) ** 2 * ancho * 0.25 + 0.35 * U * Vv * 2 + 0.12 * np.sin(U * 6) * (Vv + 0.5)
    pts = centro + X[..., None] * f + Y[..., None] * l + Z[..., None] * n
    sup = pts.reshape(-1, 3)
    inf = sup - n * grosor
    v = np.vstack([sup, inf])
    off = len(sup)
    F = []

    def idx(i, j):
        return i * nv + j

    celda_ok = np.zeros((nu - 1, nv - 1), dtype=bool)
    for i in range(nu - 1):
        for j in range(nv - 1):
            celda_ok[i, j] = dentro[i, j] and dentro[i + 1, j] and dentro[i, j + 1] and dentro[i + 1, j + 1]
    # ventana rota (agujero) en una zona
    vi, vj = int((nu - 1) * 0.62), int((nv - 1) * 0.45)
    agujero = [(vi, vj)] if not fino else [(vi + a, vj + b) for a in range(3) for b in range(3) if (a, b) != (2, 2)]
    for (i, j) in agujero:
        if 0 <= i < nu - 1 and 0 <= j < nv - 1:
            celda_ok[i, j] = False
    for i in range(nu - 1):
        for j in range(nv - 1):
            if not celda_ok[i, j]:
                continue
            a, b, c, d = idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)
            F += [(a, b, c), (a, c, d), (off + a, off + c, off + b), (off + a, off + d, off + c)]
            # paredes en los bordes de la región
            for (ii, jj, p, q) in ((i, j - 1, a, b), (i + 1, j, b, c), (i, j + 1, c, d), (i - 1, j, d, a)):
                fuera = not (0 <= ii < nu - 1 and 0 <= jj < nv - 1) or not celda_ok[ii, jj]
                if fuera:
                    F += [(q, p, off + p), (q, off + p, off + q)]
    m = Malla(v, np.asarray(F))
    m = metal_oxidado(m, sem, intensidad=0.45, base=PAL["casco_nave"])
    if fino:
        # franjas pintadas (restos de la librea humana) y quemaduras
        franja = (np.abs(((m.v - centro) @ f) / ancho - 0.18) < 0.05).astype(float)
        m.col = m.col * (1 - franja[:, None]) + lin("#C86A1E")[None, :] * 0.6 * franja[:, None]
        musgo = s.smoothstep(0.1, 0.4, s.fbm(m.v, 0.35, 3, semilla=sem + 1)) * (((m.v - centro) @ n) > -0.05)
        m.col = m.col * (1 - musgo[:, None]) + lin("#0E140C")[None, :] * musgo[:, None]
        m.rme[:, 0] = np.maximum(m.rme[:, 0], musgo)
        m.rme[:, 1] *= 1 - musgo
    # remaches
    for i in range(1, nu - 1, 3 if fino else 4):
        for jv in (0.12, 0.88):
            j = int(jv * (nv - 1))
            if dentro[i, j] and (fino or i % 2 == 0):
                c = pts[i, j] + n * 0.02
                r = esfera(c, 0.06, seg=6 if fino else 4, anillos=3, escala=(1, 1, 0.6))
                m += metal_oxidado(r, i, 0.3)
    # marco de la ventana
    cv = (pts[vi, vj] + pts[min(vi + (3 if fino else 1), nu - 1), min(vj + (3 if fino else 1), nv - 1)]) / 2
    mv = eslabon(cv + n * 0.03, f, l, ancho * 0.24, 0.07, fino)
    m += metal_oxidado(mv, 4, 0.5)
    # cristal roto: esquirlas en el marco
    if fino:
        for k in range(5):
            a = k / 5 * math.tau
            p = cv + (math.cos(a) * f * 0.25 + math.sin(a) * l * 0.18)
            es = tubo(np.array([p, p + (cv - p) * 0.5 + n * 0.02]), [0.06, 0.005], lados=3, punta=True)
            es.pintar(col=lin("#2C4058"), rugosidad=0.05, metal=0.0)
            m += es
    return m


# --------------------------------------------------------------------------------------------------------------
# Ojo: globo con iris de brasa, pupila de rendija, córnea convexa agrietada y membrana nictitante
# --------------------------------------------------------------------------------------------------------------


def ojo(centro, mira, radio, rnd, fino, cicatriz=False):
    mira = s.normalizar(mira)
    seg = 28 if fino else 12
    an = 16 if fino else 7
    g = esfera((0, 0, 0), radio, seg=seg, anillos=an)
    # Z local = hacia donde mira
    g = orientar(g, centro, mira)
    P = g.v - centro
    u, v, w = s.base_ortonormal(mira)
    z = P @ w / radio
    x = P @ u / radio
    y = P @ v / radio
    # córnea abombada: la parte delantera sobresale (convexa)
    bulto = s.smoothstep(0.55, 1.0, z) * 0.18 * radio
    g.v = g.v + np.outer(bulto, w)
    # pupila vertical (rendija) e iris con vetas doradas
    r_iris = np.sqrt(x**2 + y**2)
    rendija = (np.abs(x) < 0.09 * (1 - np.abs(y) * 0.6)) & (z > 0.5)
    iris = z > 0.25
    vetas = s.smoothstep(0.5, 0.9, np.sin(np.arctan2(y, x) * 9 + r_iris * 14) * 0.5 + 0.5)
    col = np.tile(PAL["ojo"], (len(P), 1))
    col = col * (1 - 0.6 * vetas[:, None]) + PAL["oro"][None, :] * 0.6 * vetas[:, None]
    col[~iris] = lin("#200400")
    col[rendija] = 0.0
    em = np.where(iris, 3.0 + 2.0 * vetas, 0.3)
    em[rendija] = 0.0
    emi = col.copy()
    if fino:
        # córnea agrietada (cristal volcánico): líneas finas más oscuras
        f1, f2, _, _ = s.voronoi(P * 1.0, radio * 0.45, semilla=rnd.randint(0, 99))
        grieta = 1 - s.smoothstep(0.0, radio * 0.03, f2 - f1)
        grieta *= z > 0.3
        col = col * (1 - 0.7 * grieta[:, None])
        em = em * (1 - 0.6 * grieta)
    g.col = col
    g.rme = np.stack([np.full(len(P), 0.05), np.zeros(len(P)), em], 1)
    g.emi = emi
    piezas = [g]
    # membrana nictitante: casquete fino en el lagrimal (delante y algo abajo), semitransparente en el juego
    cas = esfera((0, 0, 0), radio * 1.06, seg=seg, anillos=an)
    cas = orientar(cas, centro, mira)
    Pc = cas.v - centro
    zc = Pc @ w
    lado = Pc @ u
    sel = (zc > radio * 0.15) & (lado < -radio * 0.25 * np.sign(centro[0]) * -1)
    # nos quedamos con las caras del lagrimal
    keep = sel[cas.f].all(axis=1)
    if keep.sum() > 0:
        cas.f = cas.f[keep]
        cas.col = np.tile(lin("#5A2A20"), (len(cas.v), 1))
        cas.rme = np.tile([0.15, 0, 0.4], (len(cas.v), 1))
        cas.emi = np.tile(PAL["ojo"] * 0.4, (len(cas.v), 1))
        piezas.append(_cerrar_casquete(cas, centro, radio * 0.02))
    return unir(piezas)


def _cerrar_casquete(m, centro, grosor):
    """Da grosor a una malla abierta (casquete): copia desplazada hacia el centro + caras invertidas."""
    usados = np.unique(m.f)
    mapa = -np.ones(len(m.v), dtype=np.int64)
    mapa[usados] = np.arange(len(usados))
    v = m.v[usados]
    f = mapa[m.f]
    dentro = v - (v - centro) / np.linalg.norm(v - centro, axis=1, keepdims=True) * grosor
    V = np.vstack([v, dentro])
    F = np.vstack([f, f[:, ::-1] + len(v)])
    # paredes del borde
    aristas = {}
    for tri in f:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            k = (min(a, b), max(a, b))
            aristas[k] = aristas.get(k, 0) + 1
    paredes = []
    for tri in f:
        for a, b in ((tri[0], tri[1]), (tri[1], tri[2]), (tri[2], tri[0])):
            if aristas[(min(a, b), max(a, b))] == 1:
                paredes += [(b, a, a + len(v)), (b, a + len(v), b + len(v))]
    if paredes:
        F = np.vstack([F, np.asarray(paredes)])
    out = Malla(V, F)
    out.col = np.vstack([m.col[usados]] * 2)
    out.rme = np.vstack([m.rme[usados]] * 2)
    out.emi = np.vstack([m.emi[usados]] * 2)
    return out


def cangrejo_fosil(centro, normal, adelante, rnd, fino):
    """Criatura parásita fosilizada (cangrejo chato de 0,5 studs con 6 patas) pegada a la membrana."""
    n = s.normalizar(normal)
    f = s.normalizar(np.asarray(adelante) - n * np.dot(adelante, n))
    l = np.cross(n, f)
    cuerpo = esfera((0, 0, 0), 0.25, seg=12 if fino else 6, anillos=6 if fino else 3, escala=(1.0, 0.8, 0.3))
    R = np.stack([f, l, n], axis=1)
    cuerpo.transformar(R, np.asarray(centro) + n * 0.03)
    piezas = [cuerpo]
    for k in range(6):
        lado = 1 if k < 3 else -1
        a = (k % 3 - 1) * 0.6
        p0 = np.asarray(centro) + l * 0.18 * lado + f * a * 0.2 + n * 0.04
        p1 = p0 + l * 0.2 * lado + f * a * 0.25 + n * 0.08
        p2 = p1 + l * 0.15 * lado + f * a * 0.2 - n * 0.1
        piezas.append(tubo(np.array([p0, p1, p2]), [0.035, 0.03, 0.01], lados=4, punta=True))
    m = unir(piezas)
    m.col = np.tile(lin("#4A4238"), (len(m.v), 1))
    if fino:
        m.col = m.col * (0.7 + 0.6 * (s.fbm(m.v, 0.1, 2, semilla=9)[:, None] + 0.5))
    m.rme = np.tile([0.9, 0, 0], (len(m.v), 1))
    return m
