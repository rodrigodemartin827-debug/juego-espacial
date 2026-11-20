"""
Cuerpo del Dragón Leviatán por campos de distancia: masas + detalle tallado + reparto en piezas del rig.

  * campos_propios(P): el campo de cada pieza sin detalle (masas musculares, cráneo, huesos de las alas).
  * campo_cuerpo(P):   todo el cuerpo fundido (smin) + el detalle (escamas, cicatrices, venas, costillas...).
  * region(P, pieza):  < 0 dentro de la región de esa pieza. Las piezas hijas se cortan en su articulación con
                       un plano que pasa por el pivote; las que salen del torso (patas, alas, cuello, cola) además
                       se limitan a los puntos más cerca de sus masas que de las del torso.
  * campo_pieza(P, pieza): cuerpo ∩ región, encogida 0,01 por cada lado -> 0,02 studs de separación entre piezas.

El color, la rugosidad y la emisión de la piel también se calculan aquí (pintar_piel), por vértice de la malla
de alta resolución, y se hornean después en el atlas.
"""

import math

import numpy as np

import dragon_anatomia as A
import dragon_items as it
import dragon_sdf as s

V = np.array
HUECO = 0.02  # separación entre piezas (studs)

# --------------------------------------------------------------------------------------------------------------
# Huesos de las alas (también por campo de distancia: rótulas como nudos, dedos que se afinan)
# --------------------------------------------------------------------------------------------------------------


def _x(p, k):
    return V([p[0] * k, p[1], p[2]])


def campo_ala(P, lado, tramo):
    k = 1 if lado == "Izq" else -1
    h, c, m = _x(A.ALA_HOMBRO, k), _x(A.ALA_CODO, k), _x(A.ALA_MUNECA, k)
    if tramo == "Hombro":
        d = s.cono_redondeado(P, h, c, 1.15, A.R_HUMERO[1])
        d = s.smin(d, s.elipsoide(P, h * 0.65 + c * 0.35 + V([0, 0.2, 0.1]), (1.1, 1.0, 1.2)), 0.5)  # bíceps alar
        d = s.smin(d, s.esfera(P, c, 0.82), 0.25)  # rótula del codo
        return d
    if tramo == "Antebrazo":
        d = s.cono_redondeado(P, c, m, A.R_RADIO[0], A.R_RADIO[1])
        # radio y cúbito: dos huesos paralelos que se juntan en la muñeca
        u, v, w = s.base_ortonormal(m - c)
        d = s.smin(d, s.cono_redondeado(P, c + v * 0.35, m + v * 0.15, 0.42, 0.3), 0.25)
        d = s.smin(d, s.esfera(P, m, 0.7), 0.2)  # rótula de la muñeca
        return d
    # Mano: carpo + 4 dedos (metacarpo + falange) con nudillos + pulgar libre
    d = s.esfera(P, m, 0.62)
    for punta, nud in A.ALA_DEDOS:
        pu, nu = _x(punta, k), _x(nud, k)
        d = s.smin(d, s.cono_redondeado(P, m, nu, A.R_DEDO[0], A.R_DEDO[0] * 0.78), 0.2)
        d = s.smin(d, s.esfera(P, nu, A.R_DEDO[0] * 0.98), 0.12)
        d = s.smin(d, s.cono_redondeado(P, nu, pu, A.R_DEDO[0] * 0.7, A.R_DEDO[1]), 0.12)
    # pulgar: dedo corto que sale hacia delante desde la muñeca (lleva la garra de combate aéreo)
    pul = m + V([1.0 * k, -1.4, 0.5])
    d = s.smin(d, s.cono_redondeado(P, m, pul, 0.42, 0.3), 0.2)
    return d


def pulgar(lado):
    k = 1 if lado == "Izq" else -1
    m = _x(A.ALA_MUNECA, k)
    return m, m + V([1.0 * k, -1.4, 0.5])


# --------------------------------------------------------------------------------------------------------------
# Cráneo y mandíbula con todo lo tallado (ojos, fosas, oídos, boca, casco óseo)
# --------------------------------------------------------------------------------------------------------------

BOCA_A = V([0.0, -21.4, 8.75])
BOCA_B = V([0.0, -28.3, 8.15])


def cavidad_boca(P):
    """Hueco de la boca (paladar + lengua + garganta). Se resta a cabeza y mandíbula."""
    d = s.capsula_eliptica(P, BOCA_A, BOCA_B, 2.0, 0.95, 1.35, 0.6)
    d = s.smin(d, s.capsula_eliptica(P, BOCA_A + V([0, 1.6, -0.15]), BOCA_A, 1.1, 0.8, 1.6, 0.9), 0.4)  # garganta
    return d


def campo_cabeza_completo(P):
    d = A.campo_cabeza(P)
    # Casco óseo (cresta de gladiador) sobre la bóveda: cáscara de 0,5 que sobresale, borde trasero astillado.
    capa = s.elipsoide(P, (0, -21.6, 11.75), (3.05, 3.2, 2.45))
    casco = np.abs(capa) - 0.25
    casco = np.maximum(casco, -(P[:, 2] - 12.35))  # solo la parte de arriba
    borde = -20.0 + 0.35 * np.sin(P[:, 0] * 4.1) + 0.25 * np.sin(P[:, 0] * 9.7 + 1)  # borde trasero mellado
    casco = np.maximum(casco, P[:, 1] - borde)
    casco = np.maximum(casco, -(P[:, 1] + 25.2))
    d = s.smin(d, casco, 0.08)
    for k in (1, -1):
        o = _x(A.OJO, k)
        # párpados: anillo carnoso alrededor del ojo
        u = s.normalizar(V([k * 0.85, -0.45, 0.1]))
        q = P - o
        a = q @ u
        r = np.linalg.norm(q - np.outer(a, u), axis=1)
        toro = np.sqrt((r - A.R_OJO * 1.0) ** 2 + (a + 0.05) ** 2) - 0.2
        d = s.smin(d, toro, 0.2)
        # cuenca: el globo queda hundido bajo la ceja ósea
        d = s.smax(d, -s.esfera(P, o + u * 0.15, A.R_OJO + 0.04), 0.06)
        # fosas nasales: agujeros grandes (0,5) en la punta del hocico, con reborde
        fn = V([k * 0.85, -29.45, 9.25])
        reborde = s.esfera(P, fn + V([0, 0.05, -0.05]), 0.42)
        d = s.smin(d, reborde, 0.2)
        d = s.smax(d, -s.elipsoide(P, fn + V([0, 0, 0.12]), (0.25, 0.32, 0.4)), 0.05)
        # oídos: hendidura de 0,8 detrás del ojo
        oi = V([k * 3.05, -21.1, 10.9])
        d = s.smax(d, -s.elipsoide(P, oi, (0.35, 0.42, 0.16), A._rot_x(0.5)), 0.05)
        # muescas en el labio superior por donde suben los colmillos inferiores
        d = s.smax(d, -s.cono_redondeado(P, V([k * 1.95, -27.3, 7.3]), V([k * 2.1, -27.15, 9.9]), 0.36, 0.3), 0.12)
    d = s.smax(d, -cavidad_boca(P), 0.1)
    # crestas del paladar y glándulas de aliento
    for i in range(6):
        y = -22.4 - i * 0.95
        cresta = s.capsula_eliptica(P, V([-1.2 + i * 0.07, y, 9.2 - i * 0.07]), V([1.2 - i * 0.07, y, 9.2 - i * 0.07]),
                                    0.12, 0.12, 0.12, 0.12)
        d = s.smin(d, cresta, 0.08)
    for k in (1, -1):
        d = s.smin(d, s.esfera(P, V([k * 0.75, -23.0, 9.35]), 0.3), 0.12)
    return d


def campo_mandibula_completo(P):
    d = A.campo_mandibula(P)
    d = s.smax(d, -cavidad_boca(P), 0.1)
    return d


# --------------------------------------------------------------------------------------------------------------
# Torso: costillas expuestas y detalles grandes
# --------------------------------------------------------------------------------------------------------------

# Las 2 últimas costillas de cada lado sobresalen 0,3 (hueso expuesto, amarillento).
COSTILLAS_EXPUESTAS = []
for _k in (1, -1):
    for _y, _z in ((3.6, 8.6), (5.0, 8.9)):
        COSTILLAS_EXPUESTAS.append((V([_k * 4.75, _y - 0.6, _z + 2.6]), V([_k * 5.05, _y + 0.5, _z - 1.6])))


def campo_torso_completo(P):
    d = A.campo_torso(P)
    for a, b in COSTILLAS_EXPUESTAS:
        d = s.smin(d, s.cono_redondeado(P, a, b, 0.26, 0.2), 0.12)
    return d


# --------------------------------------------------------------------------------------------------------------
# Piezas del rig (las que tienen cuerpo por campo de distancia)
# --------------------------------------------------------------------------------------------------------------


class Def:
    def __init__(self, nombre, padre, pivote, campo, normal=None, modo="plano", voxel=0.06, tris=1500):
        self.nombre = nombre
        self.padre = padre
        self.pivote = np.asarray(pivote, dtype=np.float64)
        self.campo = campo
        self.normal = None if normal is None else s.normalizar(normal)
        self.modo = modo  # "raiz", "plano" (corte por plano), "rama" (plano + cercanía), "boca"
        self.voxel = voxel
        self.tris = tris
        self.esfera = None  # (centro, radio) envolvente, se calcula una vez


def _bis(a, b):
    return s.normalizar(s.normalizar(a) + s.normalizar(b))


def definiciones():
    C, T = A.CUELLO, A.COLA
    cabeza_dir = A.PUNTA_HOCICO - C[3]
    D = [
        Def("Torso", None, A.TORSO, campo_torso_completo, modo="raiz", voxel=0.075, tris=4600),
        Def("Cuello_Base", "Torso", C[0], lambda P: A.campo_cuello(P, 0), C[1] - C[0], "rama", 0.06, 1100),
        Def("Cuello_Medio", "Cuello_Base", C[1], lambda P: A.campo_cuello(P, 1), _bis(C[1] - C[0], C[2] - C[1]),
            "plano", 0.06, 1000),
        Def("Cuello_Superior", "Cuello_Medio", C[2], lambda P: A.campo_cuello(P, 2), _bis(C[2] - C[1], C[3] - C[2]),
            "plano", 0.055, 950),
        Def("Cabeza", "Cuello_Superior", C[3], campo_cabeza_completo, _bis(C[3] - C[2], cabeza_dir), "plano", 0.04,
            4200),
        Def("Mandibula", "Cabeza", A.MANDIBULA, campo_mandibula_completo, None, "boca", 0.04, 2000),
        Def("Cola_Base", "Torso", T[0], lambda P: A.campo_cola(P, 0), T[1] - T[0], "rama", 0.065, 1000),
        Def("Cola_Media", "Cola_Base", T[1], lambda P: A.campo_cola(P, 1), _bis(T[1] - T[0], T[2] - T[1]), "plano",
            0.055, 800),
        Def("Cola_Punta", "Cola_Media", T[2], campo_cola_punta, _bis(T[2] - T[1], T[3] - T[2]), "plano", 0.04, 1500),
    ]
    for lado, k in (("Izq", 1), ("Der", -1)):
        h, c, m = _x(A.DEL_HOMBRO, k), _x(A.DEL_CODO, k), _x(A.DEL_MUNECA, k)
        D.append(Def(f"Pata_Del_{lado}_Muslo", "Torso", h, _f(A.campo_pata_del, lado, "Muslo"), c - h, "rama", 0.06,
                     1000))
        D.append(Def(f"Pata_Del_{lado}_Garra", f"Pata_Del_{lado}_Muslo", c, _f(A.campo_pata_del, lado, "Garra"),
                     _bis(c - h, m - c), "plano", 0.045, 1500))
        ca, ro, to = _x(A.TRAS_CADERA, k), _x(A.TRAS_RODILLA, k), _x(A.TRAS_TOBILLO, k)
        D.append(Def(f"Pata_Tras_{lado}_Muslo", "Torso", ca, _f(A.campo_pata_tras, lado, "Muslo"), ro - ca, "rama",
                     0.06, 1100))
        D.append(Def(f"Pata_Tras_{lado}_Tibia", f"Pata_Tras_{lado}_Muslo", ro, _f(A.campo_pata_tras, lado, "Tibia"),
                     _bis(ro - ca, to - ro), "plano", 0.045, 1500))
        wh, wc, wm = _x(A.ALA_HOMBRO, k), _x(A.ALA_CODO, k), _x(A.ALA_MUNECA, k)
        dedos = sum(s.normalizar(_x(p, k) - wm) for p, _ in A.ALA_DEDOS)
        D.append(Def(f"Ala_{lado}_Hombro", "Torso", wh, _f(campo_ala, lado, "Hombro"), wc - wh, "rama", 0.05, 700))
        D.append(Def(f"Ala_{lado}_Antebrazo", f"Ala_{lado}_Hombro", wc, _f(campo_ala, lado, "Antebrazo"),
                     _bis(wc - wh, wm - wc), "plano", 0.045, 600))
        D.append(Def(f"Ala_{lado}_Mano", f"Ala_{lado}_Antebrazo", wm, _f(campo_ala, lado, "Mano"),
                     _bis(wm - wc, dedos), "plano", 0.035, 1000))
    return {d.nombre: d for d in D}


def _f(fn, *args):
    return lambda P: fn(P, *args)


def campo_cola_punta(P):
    """Último tramo de la cola + el HACHA bilateral de hueso (4 × 3 studs, filos de 0,1)."""
    d = A.campo_cola(P, 2)
    eje = s.normalizar(A.HACHA - A.COLA[3])  # a lo largo de la cola
    # La hoja va de lado a lado (bilateral), inclinada 35° para que se vea también de perfil.
    lado0 = s.normalizar(np.cross(eje, V([0, 0, 1])))
    arriba0 = np.cross(lado0, eje)
    g = math.radians(35)
    lado = lado0 * math.cos(g) + arriba0 * math.sin(g)
    grosor_dir = np.cross(eje, lado)
    q = P - A.HACHA
    a = q @ eje
    b = q @ lado
    c = q @ grosor_dir
    ab = np.abs(b)
    # Nudos óseos de refuerzo en el centro
    for t in (-0.7, 0.0, 0.7):
        d = s.smin(d, s.elipsoide(P, A.HACHA + eje * t, (0.4, 0.42, 0.36)), 0.2)
    return d


def hacha_marco():
    eje = s.normalizar(A.HACHA - A.COLA[3])
    lado0 = s.normalizar(np.cross(eje, V([0, 0, 1])))
    arriba0 = np.cross(lado0, eje)
    g = math.radians(35)
    lado = lado0 * math.cos(g) + arriba0 * math.sin(g)
    return eje, lado, np.cross(eje, lado)


# --------------------------------------------------------------------------------------------------------------
# Evaluación de campos con envolventes (no se evalúa una pieza lejos de ella)
# --------------------------------------------------------------------------------------------------------------

DEFS = definiciones()
HIJOS = {n: [d.nombre for d in DEFS.values() if d.padre == n] for n in DEFS}


def _subarbol(n):
    out = [n]
    for h in HIJOS[n]:
        out += _subarbol(h)
    return out


SUB = {n: _subarbol(n) for n in DEFS}


def calcular_envolventes(voxel=0.5):
    mn, mx = V([-27.0, -33.0, -1.0]), V([27.0, 36.0, 37.0])
    xs = [np.arange(mn[i], mx[i], voxel) for i in range(3)]
    G = np.stack(np.meshgrid(*xs, indexing="ij"), -1).reshape(-1, 3)
    for d in DEFS.values():
        v = d.campo(G)
        dentro = G[v < voxel]
        c = (dentro.min(0) + dentro.max(0)) / 2
        r = float(np.linalg.norm(dentro - c, axis=1).max()) + voxel
        d.esfera = (c, r)


def campo_propio(P, nombre, margen=2.5):
    d = DEFS[nombre]
    c, r = d.esfera
    dist = np.linalg.norm(P - c, axis=1)
    out = dist - r  # cota inferior lejos de la pieza
    cerca = dist < r + margen
    if cerca.any():
        out[cerca] = d.campo(P[cerca])
    return out


def campos_propios(P):
    return {n: campo_propio(P, n) for n in DEFS}


# Fundido entre piezas (filete): menor entre cabeza y mandíbula (la boca se ve como una línea), mayor en el torso.
def _k(a, b):
    par = {a, b}
    if par == {"Cabeza", "Mandibula"}:
        return 0.0
    if any(n.startswith("Ala_") for n in par):
        return 0.45
    if any(n.startswith("Cuello") for n in par) or any(n.startswith("Cola") for n in par):
        return 1.4  # cadenas largas: sin "cuentas" en las uniones
    return 0.75


def cuerpo_macro(F):
    nombres = list(DEFS)
    d = F["Torso"]
    orden = ["Cuello_Base", "Cuello_Medio", "Cuello_Superior", "Cabeza", "Cola_Base", "Cola_Media", "Cola_Punta"]
    orden += [n for n in nombres if n not in orden and n not in ("Torso", "Mandibula")]
    for n in orden:
        d = s.smin(d, F[n], _k(n, DEFS[n].padre))
    d = np.minimum(d, F["Mandibula"])  # unión dura: la boca es la línea de contacto
    return d


# --------------------------------------------------------------------------------------------------------------
# Detalle de la piel (escamas, arrugas, cicatrices). Devuelve el desplazamiento (positivo = relieve hacia fuera).
# --------------------------------------------------------------------------------------------------------------

# Cicatriz en X del pecho (10 studs de punta a punta)
X_CENTRO = V([0.0, -11.2, 8.4])
X_BRAZOS = [(V([-3.6, -10.4, 12.0]), V([3.4, -10.6, 4.6])), (V([3.7, -10.3, 12.1]), V([-3.3, -10.7, 4.8]))]
# Zarpazo triple (cuello, lado izquierdo), quemadura (lado derecho) y surco de cadena (base del cuello)
ZARPAZO = [(V([2.0, -12.4, 16.0]) + V([0, 0.55 * i, -0.15 * i]), V([2.2, -15.4, 12.6]) + V([0, 0.55 * i, -0.15 * i]))
           for i in range(3)]
QUEMADURA = (V([-1.95, -14.6, 14.4]), 0.95)
OJO_CICATRIZ = (V([2.75, -23.45, 12.3]), V([2.95, -23.65, 9.4]))


def _pesos_partes(F):
    """Pesos suaves por familia de piezas (para elegir el tamaño de escama)."""
    fam = {
        "torso": ["Torso"],
        "cuello": ["Cuello_Base", "Cuello_Medio", "Cuello_Superior"],
        "cara": ["Cabeza", "Mandibula"],
        "cola": ["Cola_Base", "Cola_Media", "Cola_Punta"],
        "pata": [n for n in DEFS if n.startswith("Pata")],
        "ala": [n for n in DEFS if n.startswith("Ala")],
    }
    m = {f: np.min(np.stack([F[n] for n in ns]), axis=0) for f, ns in fam.items()}
    w = {f: np.exp(-np.maximum(v, 0) * 2.5) for f, v in m.items()}
    tot = sum(w.values()) + 1e-9
    return {f: v / tot for f, v in w.items()}


def _escamas(P, celda, semilla, flujo, amplitud):
    f1, f2, cen, ids = s.voronoi(P, celda, semilla=semilla, jitter=0.9)
    borde = f2 - f1
    meseta = s.smoothstep(0.0, 0.28 * celda, borde)
    lift = np.clip(0.5 + ((P - cen) @ flujo) / celda, 0, 1)
    return amplitud * meseta * (0.45 + 0.55 * lift), borde, ids


def _flujo(P):
    """Dirección en la que 'caen' las escamas (de la cabeza a la cola; en las patas, hacia abajo)."""
    f = np.tile([0.0, 1.0, -0.15], (len(P), 1))
    return s.normalizar(V([0.0, 1.0, -0.2]))


def detalle(P, F, d_macro, devolver_info=False):
    W = _pesos_partes(F)
    n = len(P)
    disp = np.zeros(n)
    banda = np.abs(d_macro) < 0.9
    info = {}
    if banda.any():
        Q = P[banda]
        Wb = {k: v[banda] for k, v in W.items()}
        flujo = _flujo(Q)
        # Tamaños de escama por zona (studs): cara 0,28 (mosaico), patas/alas 0,4, cuello 0,6 (tejas), torso y
        # cola 0,75 (el vientre aún más grandes y blandas).
        capas = [
            (0.3, Wb["cara"], 0.035, 11),
            (0.42, Wb["pata"] + Wb["ala"], 0.05, 23),
            (0.62, Wb["cuello"], 0.07, 37),
            (0.8, Wb["torso"] + Wb["cola"], 0.085, 41),
        ]
        esc = np.zeros(len(Q))
        borde_min = np.full(len(Q), 9.0)
        for celda, w, amp, sem in capas:
            sel = w > 0.02
            if not sel.any():
                continue
            h, borde, _ = _escamas(Q[sel], celda, sem, flujo, amp)
            esc[sel] += h * w[sel]
            borde_min[sel] = np.minimum(borde_min[sel], borde / celda + (1 - w[sel]) * 3)
        # Arrugas y masa muscular (ruido de baja frecuencia)
        arr = s.fbm(Q, 1.6, 3, semilla=5) * 0.07
        # Costillas marcadas bajo la piel de los flancos (relieve para el mapa de normales)
        flanco = s.smoothstep(3.0, 4.6, np.abs(Q[:, 0])) * s.smoothstep(-6.5, -4.5, Q[:, 1]) * (
            1 - s.smoothstep(4.0, 6.5, Q[:, 1])) * s.smoothstep(4.5, 7.5, Q[:, 2]) * (1 - s.smoothstep(11, 13, Q[:, 2]))
        costilla = np.abs(np.sin((Q[:, 1] + 6.5) * math.pi / 1.35)) ** 3 * 0.11 * flanco * Wb["torso"]
        # Cicatriz en X del pecho: piel regenerada lisa (sin escamas) con surco y rebordes.
        dx, _, _ = s.dist_segmentos(Q, [a for a, b in X_BRAZOS], [b for a, b in X_BRAZOS])
        banda_x = 1 - s.smoothstep(0.45, 0.95, dx)
        surco_x = -0.22 * (1 - s.smoothstep(0.0, 0.32, dx)) + 0.1 * np.exp(-((dx - 0.45) ** 2) / 0.02)
        # Zarpazo triple
        dz, tz, _ = s.dist_segmentos(Q, [a for a, b in ZARPAZO], [b for a, b in ZARPAZO])
        prof = np.sin(np.clip(tz, 0, 1) * math.pi) ** 0.6
        surco_z = (-0.16 * (1 - s.smoothstep(0.0, 0.16, dz)) + 0.05 * np.exp(-((dz - 0.2) ** 2) / 0.006)) * prof
        banda_z = (1 - s.smoothstep(0.15, 0.4, dz)) * prof
        # Quemadura circular (piel cristalizada: facetas)
        dq = np.linalg.norm(Q - QUEMADURA[0], axis=1)
        banda_q = 1 - s.smoothstep(QUEMADURA[1] * 0.8, QUEMADURA[1], dq)
        f1, f2, _, _ = s.voronoi(Q, 0.18, semilla=77)
        facetas = (f1 / 0.18) * 0.05 * banda_q
        # Surco de la cadena alrededor de la base del cuello (fue capturado)
        cad_c, cad_n = V([0.0, -10.2, 12.7]), s.normalizar(V([0, -0.75, 0.66]))
        q = Q - cad_c
        ax = q @ cad_n
        surco_c = -0.14 * np.exp(-(ax**2) / 0.025) * (1 + 0.3 * s.fbm(Q, 0.3, 2, semilla=8)) * (
            np.linalg.norm(q - np.outer(ax, cad_n), axis=1) < 3.2)
        # Venas como cables (0,15) sobre las montañas musculares de las alas
        venas = np.zeros(len(Q))
        for k in (1, -1):
            for j in range(4):
                a0 = V([k * (2.2 + j * 0.55), -6.6 + j * 0.9, 13.0 + j * 0.2])
                a1 = V([k * (3.8 + j * 0.3), -3.4 + j * 0.6, 15.4 + j * 0.25])
                a2 = V([k * (4.6 + j * 0.2), -1.4 + j * 0.8, 13.6])
                dv, _, _ = s.dist_segmentos(Q, [a0, a1], [a1, a2])
                venas = np.maximum(venas, 0.15 * np.sqrt(np.clip(1 - (dv / 0.17) ** 2, 0, 1)))
        venas *= Wb["torso"]
        # Cicatriz vertical del ojo izquierdo (cruza el párpado)
        do, to, _ = s.dist_segmentos(Q, [OJO_CICATRIZ[0]], [OJO_CICATRIZ[1]])
        surco_o = -0.08 * (1 - s.smoothstep(0.0, 0.1, do)) + 0.04 * np.exp(-((do - 0.13) ** 2) / 0.002)
        liso = np.clip(banda_x + banda_z + banda_q, 0, 1)
        total = esc * (1 - liso) + arr + costilla + surco_x * banda_x + surco_z + facetas + surco_c + venas + surco_o
        disp[banda] = total
        if devolver_info:
            info = dict(banda=banda, esc=esc, borde=borde_min, banda_x=banda_x, dx=dx, banda_z=banda_z,
                        banda_q=banda_q, surco_c=surco_c, venas=venas, do=do, W=Wb)
    if devolver_info:
        return disp, info
    return disp


def campo_cuerpo(P, F=None, con_detalle=True):
    F = F if F is not None else campos_propios(P)
    d = cuerpo_macro(F)
    if con_detalle:
        d = d - detalle(P, F, d)
    return d, F


# --------------------------------------------------------------------------------------------------------------
# Regiones de las piezas
# --------------------------------------------------------------------------------------------------------------


def _corte(P, F, nombre):
    """< 0 en el lado de la pieza hija `nombre` respecto a su articulación con el padre."""
    d = DEFS[nombre]
    if d.modo == "boca":
        # la mandíbula se queda con lo que está más cerca de su campo que del cráneo
        return np.maximum((F["Mandibula"] - F["Cabeza"]) * 0.5, P[:, 1] - (A.MANDIBULA[1] + 2.6))
    plano = -((P - d.pivote) @ d.normal)
    if d.modo == "plano":
        return plano
    # la rama se queda con lo que está más cerca de sus masas que de CUALQUIER otra (no solo del padre): así la
    # base de la cola no se lleva el tobillo, ni el cuello la punta del ala
    sub = np.min(np.stack([F[n] for n in SUB[nombre]]), axis=0)
    resto = np.min(np.stack([F[n] for n in DEFS if n not in SUB[nombre]]), axis=0)
    return np.maximum(plano, (sub - resto) * 0.5)


def region(P, F, nombre):
    """Campo de la región (negativo dentro) de una pieza: su corte, el de sus antepasados y fuera de sus hijos."""
    partes = []
    n = nombre
    while DEFS[n].padre is not None:
        partes.append(_corte(P, F, n))
        n = DEFS[n].padre
    for h in HIJOS[nombre]:
        partes.append(-_corte(P, F, h))
    if not partes:
        return np.full(len(P), -1e3)
    return np.maximum.reduce(partes)


def campo_pieza(P, nombre, con_detalle=True):
    d, F = campo_cuerpo(P, con_detalle=con_detalle)
    r = region(P, F, nombre)
    return np.maximum(d, r + HUECO / 2)


def campo_cuerpo_simple(P):
    """Para asentar piezas encima (cuernos, cresta): cuerpo sin detalle fino."""
    d, _ = campo_cuerpo(P, con_detalle=False)
    return d


# --------------------------------------------------------------------------------------------------------------
# Pintura de la piel (por vértice de la malla de alta)
# --------------------------------------------------------------------------------------------------------------


def pintar_piel(P, N, nombre):
    """Color, rugosidad/metal/emisión y color de emisión de la piel en los puntos P con normales N."""
    F = campos_propios(P)
    d_macro = cuerpo_macro(F)
    _, info = detalle(P, F, d_macro, devolver_info=True)
    n = len(P)
    W = _pesos_partes(F)
    piel = it.PAL["piel"]
    refl = it.PAL["reflejo"]
    sem = 3
    var = s.fbm(P, 2.2, 3, semilla=sem)
    col = piel[None, :] * (1.0 + 0.6 * var[:, None]) + refl[None, :] * s.smoothstep(0.0, 0.6, var)[:, None] * 0.9
    rug = np.full(n, 0.58)
    em = np.zeros(n)
    emc = np.tile(it.PAL["grieta"], (n, 1))
    # escamas: la cima algo más clara (gastada), las juntas oscuras
    b = np.full(n, 9.0)
    b[info["banda"]] = info["borde"]
    junta = 1 - s.smoothstep(0.0, 0.18, b)
    col *= (1 - 0.6 * junta)[:, None]
    _, _, _, ids = s.voronoi(P, 0.8, semilla=41)
    alea = ((ids * 2654435761) % 1000) / 1000.0
    col *= (0.75 + 0.55 * alea)[:, None]
    rug += 0.18 * junta
    # Vientre gris ceniza: parte baja del torso, cuello y cola (y cara interior de las patas, más suave).
    abajo = s.smoothstep(-0.15, -0.6, N[:, 2])
    zona_vientre = (W["torso"] + W["cuello"] + W["cola"]) * abajo
    zona_vientre *= 1 - s.smoothstep(0.55, 0.9, np.abs(P[:, 0]) / 5.5)
    vien = it.PAL["vientre"] * (0.85 + 0.3 * alea[:, None])
    col = col * (1 - zona_vientre[:, None]) + vien * zona_vientre[:, None] * (1 - 0.5 * junta)[:, None]
    rug = rug * (1 - zona_vientre) + 0.78 * zona_vientre
    # Placas de garganta y papada algo más claras
    # Hollín en la cara (alrededor de las fosas y la boca: de su propio aliento)
    hollin = np.exp(-np.sum(((P - V([0, -29.2, 8.8])) / V([2.6, 1.6, 1.5])) ** 2, 1))
    col *= (1 - 0.85 * hollin)[:, None]
    rug = rug + 0.3 * hollin
    # Interior de la boca: paladar y lengua gris rojizo, garganta que brilla como un horno (#FF4500)
    cav = cavidad_boca(P)
    dentro = s.smoothstep(0.25, -0.05, cav) * (W["cara"] > 0.3)
    gar = s.smoothstep(-25.2, -21.8, P[:, 1])  # hacia la garganta
    boca_col = it.lin("#4A2622") * (1 - gar[:, None]) + it.PAL["boca"] * 0.5 * gar[:, None]
    col = col * (1 - dentro[:, None]) + boca_col * dentro[:, None]
    rug = rug * (1 - dentro) + 0.3 * dentro
    em = np.maximum(em, dentro * (0.4 + 3.6 * gar ** 1.5))
    emc = np.where((dentro > 0.05)[:, None], it.PAL["boca"][None, :], emc)
    # Glándulas del paladar: poros negros
    for k in (1, -1):
        g = np.linalg.norm(P - V([k * 0.75, -23.0, 9.35]), axis=1)
        poro = (g < 0.32) * (np.sin(P[:, 0] * 40) * np.sin(P[:, 1] * 40) > 0.6)
        col[poro] = 0.0
    # Bordes ennegrecidos de las fosas nasales
    for k in (1, -1):
        g = np.linalg.norm(P - V([k * 0.85, -29.45, 9.3]), axis=1)
        col *= (1 - 0.9 * (g < 0.6))[:, None]
    # Cicatriz en X: piel regenerada más oscura y lisa + marcas volcánicas que brillan como magma alrededor
    bx = np.zeros(n)
    bx[info["banda"]] = info["banda_x"]
    dxx = np.full(n, 9.0)
    dxx[info["banda"]] = info["dx"]
    col = col * (1 - 0.7 * bx[:, None]) + it.lin("#030202")[None, :] * 0.7 * bx[:, None]
    rug = rug * (1 - bx) + 0.32 * bx
    f1, f2, _, _ = s.voronoi(P, 0.55, semilla=13)
    venas_magma = (1 - s.smoothstep(0.0, 0.06, f2 - f1)) * s.smoothstep(2.4, 0.5, dxx) * (dxx > 0.35)
    venas_magma *= s.fbm(P, 0.8, 2, semilla=21) > -0.2
    nucleo = (1 - s.smoothstep(0.0, 0.14, dxx))  # el fondo del surco también arde
    lava = np.clip(venas_magma + nucleo * 0.8, 0, 1)
    col = col * (1 - lava[:, None]) + it.PAL["grieta"][None, :] * 0.45 * lava[:, None]
    em = np.maximum(em, lava * 2.2)
    # Zarpazo: piel más clara
    bz = np.zeros(n)
    bz[info["banda"]] = info["banda_z"]
    col = col * (1 - bz[:, None]) + it.lin("#3A2C2C")[None, :] * bz[:, None]
    rug = rug * (1 - bz) + 0.45 * bz
    # Quemadura cristalizada: brillante, violácea
    bq = np.zeros(n)
    bq[info["banda"]] = info["banda_q"]
    col = col * (1 - bq[:, None]) + it.lin("#20102A")[None, :] * bq[:, None]
    rug = rug * (1 - bq) + 0.1 * bq
    borde_q = np.exp(-((np.linalg.norm(P - QUEMADURA[0], axis=1) - QUEMADURA[1] * 0.9) ** 2) / 0.01)
    col = col * (1 - 0.6 * borde_q[:, None]) + it.lin("#4A1A10")[None, :] * 0.6 * borde_q[:, None]
    # Surco de la cadena: piel rugosa y algo más clara
    sc = np.zeros(n)
    sc[info["banda"]] = np.clip(-info["surco_c"] / 0.14, 0, 1)
    col = col * (1 - 0.5 * sc[:, None]) + it.lin("#2A1E1A")[None, :] * 0.5 * sc[:, None]
    rug = np.maximum(rug, 0.9 * sc)
    # Cicatriz del ojo izquierdo: línea clara
    do = np.full(n, 9.0)
    do[info["banda"]] = info["do"]
    co = 1 - s.smoothstep(0.05, 0.16, do)
    col = col * (1 - co[:, None]) + it.lin("#4A3A38")[None, :] * co[:, None]
    # Costillas expuestas: hueso amarillento
    for a, b2 in COSTILLAS_EXPUESTAS:
        dd = s.cono_redondeado(P, a, b2, 0.26, 0.2)
        h = s.smoothstep(0.1, -0.02, dd) * (F["Torso"] > -0.05)
        col = col * (1 - h[:, None]) + it.PAL["hueso"][None, :] * 0.8 * h[:, None]
        rug = rug * (1 - h) + 0.5 * h
    # Lomo: musgo negro y líquenes rojos tenues en las grietas entre placas
    lomo = s.smoothstep(12.4, 13.6, P[:, 2]) * W["torso"] * s.smoothstep(-8.5, -6.5, P[:, 1]) * (
        1 - s.smoothstep(8.0, 9.5, P[:, 1]))
    musgo = lomo * s.smoothstep(-0.1, 0.4, s.fbm(P, 0.6, 3, semilla=31))
    col = col * (1 - musgo[:, None]) + it.PAL["musgo"][None, :] * musgo[:, None]
    rug = np.maximum(rug, 0.95 * musgo)
    liquen = lomo * (1 - s.smoothstep(0.0, 0.05, f2 - f1)) * (s.fbm(P, 0.9, 2, semilla=55) > 0.1)
    col = col * (1 - liquen[:, None]) + it.PAL["grieta"][None, :] * 0.3 * liquen[:, None]
    em = np.maximum(em, liquen * 0.8)
    # Huesos de las alas: hueso oscuro, rótulas gastadas
    ala = W["ala"]
    col = col * (1 - 0.5 * ala[:, None]) + it.lin("#1C1210")[None, :] * 0.5 * ala[:, None]
    # Hacha de la cola: hueso oscuro con filos claros, rayas y abolladuras
    if nombre == "Cola_Punta":
        eje, lado, gro = hacha_marco()
        q = P - A.HACHA
        ab = np.abs(q @ lado)
        hueso = s.smoothstep(0.9, 1.3, ab)
        filo = s.smoothstep(1.6, 1.95, ab)
        col = col * (1 - hueso[:, None]) + it.lin("#2A2018")[None, :] * hueso[:, None]
        col = col * (1 - filo[:, None]) + it.PAL["marfil"][None, :] * 0.55 * filo[:, None]
        raya = s.smoothstep(0.75, 0.95, np.abs(np.sin(P @ V([9.0, 4.0, 13.0]) + 3 * s.fbm(P, 0.4, 2, semilla=2))))
        col = col * (1 + 0.8 * raya[:, None] * hueso[:, None])
        rug = rug * (1 - hueso) + (0.45 - 0.2 * filo) * hueso
    rme = np.stack([np.clip(rug, 0.05, 1), np.zeros(n), em], 1)
    return np.clip(col, 0, 1), rme, emc
