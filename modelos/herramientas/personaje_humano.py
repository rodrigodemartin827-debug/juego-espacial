"""
Piezas 3D del personaje humano (editor de personaje): peinados, accesorios y los detalles de chaquetas y pantalones.

Uso (desde la raíz del repositorio):
    blender -b --python modelos/herramientas/personaje_humano.py -- --salida modelos/personaje_humano [--rapido]

Qué sale en <salida>:
    roblox/Cabellos.fbx, roblox/Accesorios.fbx, roblox/Chaquetas.fbx, roblox/Pantalones.fbx
        Una malla por objeto. Cada objeto se llama «<Categoria>_<Id>__<Parte>__<Rol>»:
          · Parte: Cabeza, Torso, BrazoI, BrazoD, PiernaI o PiernaD (la parte del R6 a la que va soldada).
          · Rol: de qué color se pinta en el juego (Pelo, Chaqueta, Pantalon, Detalle, Oscuro, Claro, Metal, Neon,
            Cristal). Así un mismo modelo vale para cualquier color que elija el jugador.
    piezas.json      por objeto: parte, centro respecto al centro de su parte (studs, ejes de Roblox) y triángulos.
    hoja_contactos_<ronda>.png   renders de todas las piezas sobre un maniquí R6.

Las medidas son las de un R6 estándar en studs (cabeza 2x1x1 con malla de cabeza a escala 1,25, que se ve como un
cilindro redondeado de ~1,2 de ancho y alto; torso 2x2x1; brazos y piernas 1x2x1). Todo se construye en coordenadas de
Roblox (X derecha del personaje, Y arriba, -Z delante, origen en el centro del torso) y se pasa a Blender al final.
Límite: menos de 1.500 triángulos por peinado y por accesorio.
"""

import argparse
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import comun as c  # noqa: E402

E = c.ESTUDIO

# Centro de cada parte del R6 (coordenadas de Roblox, origen en el centro del torso) y su nombre en Roblox.
PARTES = {
    "Cabeza": ((0.0, 1.5, 0.0), "Head"),
    "Torso": ((0.0, 0.0, 0.0), "Torso"),
    "BrazoI": ((-1.5, 0.0, 0.0), "Left Arm"),
    "BrazoD": ((1.5, 0.0, 0.0), "Right Arm"),
    "PiernaI": ((-0.5, -2.0, 0.0), "Left Leg"),
    "PiernaD": ((0.5, -2.0, 0.0), "Right Leg"),
}

# Colores de muestra de cada rol (solo para los renders; en el juego los pone el jugador o los datos).
MUESTRA = {
    "Pelo": "#4A2F1E",
    "Chaqueta": "#2F6FD6",
    "Pantalon": "#2E3440",
    "Detalle": "#F2F4F7",
    "Oscuro": "#1A1D22",
    "Claro": "#F4F6F8",
    "Metal": "#8C96A6",
    "Neon": "#4DE8FF",
    "Cristal": "#7FD8FF",
    "Piel": "#D9A37A",
}

# Cabeza vista como cilindro redondeado (radio, media altura y redondeo del borde), un poco por fuera de la real.
R_CAB, H_CAB, F_CAB = 0.62, 0.6, 0.28


# ==============================================================================================================
# Malla en coordenadas de Roblox
# ==============================================================================================================


class Malla:
    """Un bmesh al que se le añaden piezas en coordenadas de Roblox (studs)."""

    def __init__(self):
        self.bm = bmesh.new()

    def v(self, p):
        return self.bm.verts.new(Vector(p))

    def cara(self, vs):
        try:
            return self.bm.faces.new(vs)
        except ValueError:
            return None

    def caja(self, centro, tam, giro=(0, 0, 0), bisel=0.0, rot=None):
        """Caja (ancho X, alto Y, fondo Z) con bisel opcional de un segmento. `rot` (matriz 4x4) sustituye a `giro`."""
        tmp = bmesh.new()
        bmesh.ops.create_cube(tmp, size=1.0)
        bmesh.ops.scale(tmp, vec=Vector(tam), verts=tmp.verts)
        if bisel > 0:
            bmesh.ops.bevel(tmp, geom=list(tmp.edges), offset=min(bisel, min(tam) * 0.45), segments=1,
                            affect="EDGES", profile=0.5)
        r = rot if rot is not None else (Matrix.Rotation(giro[1], 4, "Y") @ Matrix.Rotation(giro[0], 4, "X")
                                         @ Matrix.Rotation(giro[2], 4, "Z"))
        m = Matrix.Translation(Vector(centro)) @ r
        bmesh.ops.transform(tmp, matrix=m, verts=tmp.verts)
        self._juntar(tmp)

    def cilindro(self, centro, radio, largo, n=12, eje="Y", radio2=None, giro=None, escala=None):
        tmp = bmesh.new()
        bmesh.ops.create_cone(tmp, cap_ends=True, segments=n, radius1=radio,
                              radius2=radio if radio2 is None else radio2, depth=largo)
        if escala is not None:
            bmesh.ops.scale(tmp, vec=Vector(escala), verts=tmp.verts)
        # create_cone crea a lo largo de Z.
        base = {"Z": Matrix.Identity(4), "Y": Matrix.Rotation(-math.pi / 2, 4, "X"),
                "X": Matrix.Rotation(math.pi / 2, 4, "Y")}[eje]
        m = Matrix.Translation(Vector(centro)) @ (giro or Matrix.Identity(4)) @ base
        bmesh.ops.transform(tmp, matrix=m, verts=tmp.verts)
        self._juntar(tmp)

    def esfera(self, centro, radios, u=12, v=8):
        tmp = bmesh.new()
        bmesh.ops.create_uvsphere(tmp, u_segments=u, v_segments=v, radius=1.0)
        bmesh.ops.scale(tmp, vec=Vector(radios), verts=tmp.verts)
        bmesh.ops.translate(tmp, vec=Vector(centro), verts=tmp.verts)
        self._juntar(tmp)

    def tubo(self, puntos, radios, n=8, cerrar=True, aplastar=1.0):
        """Tubo a lo largo de una polilínea, con un radio por punto (coleta, trenzas, diademas)."""
        anillos = []
        for i, p in enumerate(puntos):
            p = Vector(p)
            a = Vector(puntos[max(i - 1, 0)])
            b = Vector(puntos[min(i + 1, len(puntos) - 1)])
            t = (b - a).normalized()
            ref = Vector((1, 0, 0)) if abs(t.x) < 0.9 else Vector((0, 1, 0))
            u = t.cross(ref).normalized()
            w = t.cross(u).normalized()
            anillo = []
            for k in range(n):
                ang = 2 * math.pi * k / n
                anillo.append(self.v(p + (u * math.cos(ang) + w * math.sin(ang) * aplastar) * radios[i]))
            anillos.append(anillo)
        for i in range(len(anillos) - 1):
            for k in range(n):
                k2 = (k + 1) % n
                self.cara([anillos[i][k], anillos[i][k2], anillos[i + 1][k2], anillos[i + 1][k]])
        if cerrar:
            for anillo, rev in ((anillos[0], True), (anillos[-1], False)):
                centro = self.v(sum((x.co for x in anillo), Vector()) / n)
                for k in range(n):
                    a, b = anillo[k], anillo[(k + 1) % n]
                    self.cara([centro, b, a] if rev else [centro, a, b])

    def banda(self, centro, semi, alto, grosor, radio_esq=0.12, n_esq=3, hueco=0.0):
        """
        Banda alrededor de una caja (cuello, puños, cinturón, botas): un rectángulo redondeado de semiejes
        `semi` = (x, z), de `alto` en Y y `grosor` hacia fuera. `hueco` (0-1) deja abierta la parte de delante.
        """
        cx, cy, cz = centro
        sx, sz = semi
        r = min(radio_esq, sx * 0.9, sz * 0.9)
        perfil = []
        esquinas = [(sx - r, -(sz - r), -math.pi / 2), (sx - r, sz - r, 0.0), (-(sx - r), sz - r, math.pi / 2),
                    (-(sx - r), -(sz - r), math.pi)]
        for ex, ez, a0 in esquinas:
            for k in range(n_esq + 1):
                a = a0 + (math.pi / 2) * k / n_esq
                perfil.append((ex + r * math.cos(a), ez + r * math.sin(a), math.cos(a), math.sin(a)))
        # Delante es -Z: la esquina 4 termina en (−x, −z) y la 1 empieza en (x, −z); el hueco corta el frente.
        if hueco > 0:
            ancho = sx * hueco
            perfil = [p for p in perfil if not (p[1] < -sz + r * 0.5 and abs(p[0]) < ancho)]
        n = len(perfil)
        abierto = hueco > 0
        capas = []
        for (px, pz, nx, nz) in perfil:
            ext = (px + nx * grosor, pz + nz * grosor)
            capas.append([
                self.v((cx + px, cy - alto / 2, cz + pz)), self.v((cx + ext[0], cy - alto / 2, cz + ext[1])),
                self.v((cx + ext[0], cy + alto / 2, cz + ext[1])), self.v((cx + px, cy + alto / 2, cz + pz)),
            ])
        tramos = n - 1 if abierto else n
        for i in range(tramos):
            a, b = capas[i], capas[(i + 1) % n]
            for k in range(4):
                k2 = (k + 1) % 4
                self.cara([a[k], b[k], b[k2], a[k2]])
        if abierto:
            self.cara(list(reversed(capas[0])))
            self.cara(capas[-1])

    def _juntar(self, tmp):
        malla = bpy.data.meshes.new("_tmp")
        tmp.to_mesh(malla)
        tmp.free()
        self.bm.from_mesh(malla)
        bpy.data.meshes.remove(malla)


# ==============================================================================================================
# Pelo: casquete que sigue la cabeza
# ==============================================================================================================


def perfil_cabeza(s):
    """Punto del perfil de la cabeza (r, y) y su normal (nr, ny) a una distancia `s` del centro de arriba."""
    la = R_CAB - F_CAB
    lb = math.pi * F_CAB / 2
    if s <= la:
        return (s, H_CAB), (0.0, 1.0)
    if s <= la + lb:
        a = (s - la) / F_CAB
        return (la + F_CAB * math.sin(a), H_CAB - F_CAB + F_CAB * math.cos(a)), (math.sin(a), math.cos(a))
    return (R_CAB, H_CAB - F_CAB - (s - la - lb)), (1.0, 0.0)


def s_de_altura(y):
    """Distancia por el perfil hasta la altura `y` (para poner la línea del pelo por alturas). Vale también en la
    curva de arriba (entre H - F y H)."""
    la = R_CAB - F_CAB
    lb = math.pi * F_CAB / 2
    if y >= H_CAB - F_CAB:
        a = math.acos(max(-1.0, min(1.0, (y - (H_CAB - F_CAB)) / F_CAB)))
        return la + F_CAB * a
    return la + lb + (H_CAB - F_CAB - y)


def angulo_dif(a, b):
    d = (a - b + math.pi) % (2 * math.pi) - math.pi
    return abs(d)


def casquete(m, hasta, grosor, n_t=32, n_s=9, espalda=False, desplazar=None):
    """
    Pelo que cubre la cabeza. Para cada ángulo θ (0 = delante, positivo hacia la derecha del personaje):
      hasta(θ) -> distancia por el perfil hasta donde llega el pelo (s_de_altura ayuda a darla como altura).
      grosor(θ, t) -> grosor del pelo hacia fuera, con t = 0 arriba y 1 en el borde.
    Superficie de fuera + de dentro (metida en la cabeza) + borde: una pieza cerrada.
    `espalda`: lo que baja por debajo de la barbilla se aparta hacia atrás para no atravesar el torso.
    `desplazar(p, θ, t)` -> vector extra (para tupés, flequillos ladeados...).
    """
    cab = Vector(PARTES["Cabeza"][0])

    def punto(theta, s, d):
        (r, y), (nr, ny) = perfil_cabeza(s)
        r2, y2 = r + nr * d, y + ny * d
        p = Vector((r2 * math.sin(theta), y2, -r2 * math.cos(theta)))
        if espalda and y2 < -0.42:
            # Por debajo de la cabeza, el pelo cae por la espalda: por detrás del torso (z > 0,5) y más estrecho.
            k = min(1.0, (-0.42 - y2) / 0.3)
            p.z = max(p.z, 0.56 + d * 0.6) * k + p.z * (1 - k)
            p.x *= 1 - 0.25 * k
        return p

    exterior, interior = [], []
    for i in range(n_t):
        th = 2 * math.pi * i / n_t
        s_max = hasta(th)
        col_e, col_i = [], []
        for j in range(1, n_s + 1):
            t = j / n_s
            s = s_max * t
            p = punto(th, s, grosor(th, t))
            if desplazar:
                p += Vector(desplazar(p, th, t))
            col_e.append(m.v(cab + p))
            col_i.append(m.v(cab + punto(th, s, -0.05)))
        exterior.append(col_e)
        interior.append(col_i)
    # Polos de arriba.
    d0 = sum(grosor(2 * math.pi * i / n_t, 0.0) for i in range(n_t)) / n_t
    p0 = Vector((0, H_CAB + d0, 0))
    if desplazar:
        p0 += Vector(desplazar(p0, 0.0, 0.0))
    polo_e = m.v(cab + p0)
    polo_i = m.v(cab + Vector((0, H_CAB - 0.05, 0)))
    for i in range(n_t):
        i2 = (i + 1) % n_t
        m.cara([polo_e, exterior[i2][0], exterior[i][0]])
        m.cara([polo_i, interior[i][0], interior[i2][0]])
        for j in range(n_s - 1):
            m.cara([exterior[i][j], exterior[i2][j], exterior[i2][j + 1], exterior[i][j + 1]])
            m.cara([interior[i][j], interior[i][j + 1], interior[i2][j + 1], interior[i2][j]])
        # Borde: une la de fuera con la de dentro.
        m.cara([exterior[i][-1], exterior[i2][-1], interior[i2][-1], interior[i][-1]])


def puntas_en_linea(hasta_base, amplitud, periodo=2, n_t=32, desfase=0):
    """Línea del pelo en zigzag (mechones acabados en punta): alterna columnas largas y cortas."""
    def f(th):
        i = round(th / (2 * math.pi) * n_t)
        return hasta_base(th) + (amplitud(th) if (i + desfase) % periodo == 0 else 0.0)
    return f


def mezcla(th, centro, ancho):
    """1 en el ángulo `centro` y 0 a más de `ancho` radianes, con transición suave."""
    d = angulo_dif(th, centro)
    if d >= ancho:
        return 0.0
    return 0.5 + 0.5 * math.cos(math.pi * d / ancho)


def linea_basica(frente=0.34, lado=0.02, nuca=-0.3):
    """Línea del pelo: alta en la frente, a media oreja en los lados y baja en la nuca."""
    def f(th):
        k_frente = mezcla(th, 0.0, 1.3)
        k_nuca = mezcla(th, math.pi, 1.6)
        y = lado + (frente - lado) * k_frente + (nuca - lado) * k_nuca
        return s_de_altura(y)
    return f


def cono(m, base, direccion, largo, radio, n=6):
    d = Vector(direccion).normalized()
    giro = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
    m.cilindro(Vector(base) + d * (largo / 2), radio, largo, n=n, eje="Z", radio2=0.0, giro=giro)


def punto_cabeza(theta, y, d=0.0):
    """Punto de la superficie de la cabeza (más `d` hacia fuera) en coordenadas del personaje."""
    (r, yy), (nr, ny) = perfil_cabeza(s_de_altura(y))
    r2, y2 = r + nr * d, yy + ny * d
    return Vector(PARTES["Cabeza"][0]) + Vector((r2 * math.sin(theta), y2, -r2 * math.cos(theta)))


def normal_cabeza(theta, y):
    _, (nr, ny) = perfil_cabeza(s_de_altura(y))
    return Vector((nr * math.sin(theta), ny, -nr * math.cos(theta)))


# ----- Peinados -----


def cabello_corto(m):
    base = linea_basica(0.36, 0.06, -0.24)
    casquete(m, puntas_en_linea(base, lambda th: 0.07 * mezcla(th, 0, 1.2)),
             lambda th, t: 0.075 + 0.04 * (1 - t) + 0.03 * mezcla(th, 0, 0.8) * (1 - t))


def cabello_rapado(m):
    casquete(m, linea_basica(0.38, 0.12, -0.18), lambda th, t: 0.035, n_t=28, n_s=7)


def cabello_flequillo(m):
    def hasta(th):
        b = linea_basica(0.36, 0.0, -0.32)(th)
        # El flequillo cae por la frente, más largo hacia la izquierda del personaje (θ negativo).
        k = mezcla(th, -0.35, 1.0)
        return b + k * (s_de_altura(0.16) - s_de_altura(0.36))
    casquete(m, puntas_en_linea(hasta, lambda th: 0.08 * mezcla(th, -0.2, 1.4)),
             lambda th, t: 0.09 + 0.05 * (1 - t) + 0.04 * mezcla(th, -0.3, 0.9),
             desplazar=lambda p, th, t: (-0.05 * t * mezcla(th, 0, 1.0), 0, 0))


def cabello_cresta(m):
    casquete(m, linea_basica(0.36, 0.12, -0.2), lambda th, t: 0.035, n_t=28, n_s=7)
    # Cresta: puntas aplanadas (finas de lado a lado) por el centro, de la frente a la nuca, más altas en medio y
    # echadas un poco hacia atrás.
    cab = Vector(PARTES["Cabeza"][0])
    n = 8
    for i in range(n):
        a = -0.9 + 2.1 * i / (n - 1)  # ángulo en el plano medio: negativo hacia la frente, positivo hacia la nuca
        base = cab + Vector((0, 0.66 * math.cos(a) - 0.02, 0.66 * math.sin(a)))
        normal = Vector((0, math.cos(a), math.sin(a)))
        d = (normal + Vector((0, 0.15, 0.55))).normalized()
        largo = 0.36 + 0.24 * math.cos((a - 0.2) * 1.1)
        giro = d.to_track_quat("Z", "Y").to_matrix().to_4x4()
        m.cilindro(base + d * (largo / 2 - 0.06), 0.26, largo, n=6, eje="Z", radio2=0.0, giro=giro,
                   escala=(0.32, 1.0, 1.0))


def cabello_despeinado(m):
    rnd = random.Random(7)
    base = linea_basica(0.34, 0.02, -0.28)
    casquete(m, puntas_en_linea(base, lambda th: 0.09, periodo=3),
             lambda th, t: 0.1 + 0.035 * math.sin(th * 5 + t * 4) + 0.03 * (1 - t))
    for i in range(9):
        th = rnd.uniform(-1.0, 1.0) * math.pi
        y = rnd.uniform(0.35, 0.62)
        p = punto_cabeza(th, y, 0.06)
        n = normal_cabeza(th, y)
        d = (n + Vector((rnd.uniform(-0.5, 0.5), 0.35, 0.3 + rnd.uniform(-0.2, 0.3)))).normalized()
        cono(m, p, d, rnd.uniform(0.22, 0.32), 0.09, n=5)


def cabello_coleta(m):
    casquete(m, linea_basica(0.37, 0.04, -0.2), lambda th, t: 0.075 + 0.025 * (1 - t))
    cab = Vector(PARTES["Cabeza"][0])
    pts = [cab + Vector(p) for p in ((0, 0.42, 0.55), (0, 0.38, 0.78), (0, 0.18, 0.92), (0, -0.15, 0.96),
                                      (0, -0.5, 0.92), (0, -0.85, 0.86), (0, -1.1, 0.84))]
    m.tubo(pts, [0.15, 0.2, 0.2, 0.18, 0.15, 0.1, 0.03], n=10)
    m.tubo([cab + Vector((0, 0.45, 0.6)), cab + Vector((0, 0.39, 0.74))], [0.17, 0.17], n=10)  # goma


def cabello_largo(m):
    def hasta(th):
        lados = s_de_altura(-0.36)
        espalda = s_de_altura(-1.45)
        k = mezcla(th, math.pi, 1.9)
        frente = s_de_altura(0.34)
        kf = mezcla(th, 0.0, 1.1)
        return (lados * (1 - k) + espalda * k) * (1 - kf) + frente * kf
    casquete(m, puntas_en_linea(hasta, lambda th: 0.1), lambda th, t: 0.09 + 0.05 * t * mezcla(th, math.pi, 2.2),
             n_t=30, n_s=11, espalda=True)


def cabello_mono(m):
    casquete(m, linea_basica(0.38, 0.06, -0.18), lambda th, t: 0.07)
    cab = Vector(PARTES["Cabeza"][0])
    m.esfera(cab + Vector((0, 0.72, 0.36)), (0.3, 0.27, 0.3), u=14, v=9)
    m.tubo([cab + Vector((0, 0.6, 0.3)), cab + Vector((0, 0.66, 0.34))], [0.24, 0.24], n=12)


def cabello_rizado(m):
    def grosor(th, t):
        return 0.2 + 0.07 * math.sin(th * 7) * math.sin(t * 9 + 1) + 0.06 * (1 - t)
    casquete(m, linea_basica(0.38, -0.08, -0.32), grosor, n_t=36, n_s=10)


def cabello_tupe(m):
    def grosor(th, t):
        frente = mezcla(th, 0.0, 1.1)
        return 0.07 + 0.05 * (1 - t) + 0.26 * frente * math.exp(-((t - 0.55) / 0.3) ** 2)
    casquete(m, linea_basica(0.38, 0.05, -0.22), grosor,
             desplazar=lambda p, th, t: (0, 0, -0.1 * mezcla(th, 0, 1.0) * math.exp(-((t - 0.6) / 0.3) ** 2)))


def cabello_melena(m):
    def hasta(th):
        frente = s_de_altura(0.3)
        lados = s_de_altura(-0.5)
        kf = mezcla(th, 0.0, 1.05)
        return lados * (1 - kf) + frente * kf
    casquete(m, puntas_en_linea(hasta, lambda th: 0.05 * (1 - mezcla(th, 0, 1.2))),
             lambda th, t: 0.1 + 0.08 * t ** 3 + 0.03 * (1 - t), n_s=11, espalda=True)


def cabello_puntas(m):
    casquete(m, puntas_en_linea(linea_basica(0.34, 0.02, -0.26), lambda th: 0.08),
             lambda th, t: 0.1 + 0.03 * (1 - t))
    for k, (th, y, largo) in enumerate([(0.0, 0.55, 0.42), (0.5, 0.5, 0.4), (-0.5, 0.5, 0.4), (1.2, 0.42, 0.36),
                                         (-1.2, 0.42, 0.36), (2.0, 0.4, 0.38), (-2.0, 0.4, 0.38),
                                         (2.7, 0.35, 0.36), (-2.7, 0.35, 0.36), (math.pi, 0.3, 0.34),
                                         (0.0, 0.62, 0.3)]):
        p = punto_cabeza(th, y, 0.07)
        n = normal_cabeza(th, y)
        d = (n * 0.8 + Vector((0, 0.55, 0.45))).normalized()
        cono(m, p, d, largo, 0.13, n=5)


CABELLOS = [
    ("Corto", cabello_corto), ("Rapado", cabello_rapado), ("Flequillo", cabello_flequillo),
    ("Cresta", cabello_cresta), ("Despeinado", cabello_despeinado), ("Coleta", cabello_coleta),
    ("Largo", cabello_largo), ("Mono", cabello_mono), ("Rizado", cabello_rizado), ("Tupe", cabello_tupe),
    ("Melena", cabello_melena), ("Puntas", cabello_puntas),
]


# ==============================================================================================================
# Accesorios
# ==============================================================================================================


def arco_cabeza(m, desde, hasta_ang, y0, y1, d, grosor, n=16):
    """Tira curva que rodea la cabeza entre dos ángulos (visera, cinta), de y0 a y1 y a `d` por fuera."""
    filas = []
    for i in range(n + 1):
        th = desde + (hasta_ang - desde) * i / n
        fila = []
        for (y, dd) in ((y0, d), (y0, d + grosor), (y1, d + grosor), (y1, d)):
            fila.append(m.v(punto_cabeza(th, y, dd)))
        filas.append(fila)
    for i in range(n):
        a, b = filas[i], filas[i + 1]
        for k in range(4):
            k2 = (k + 1) % 4
            m.cara([a[k], a[k2], b[k2], b[k]])
    m.cara(filas[0])
    m.cara(list(reversed(filas[-1])))


def accesorio_visor(mallas):
    arco_cabeza(mallas("Cabeza", "Neon"), -1.25, 1.25, 0.02, 0.24, 0.03, 0.05)
    marco = mallas("Cabeza", "Metal")
    arco_cabeza(marco, -1.35, 1.35, 0.24, 0.29, 0.02, 0.08)
    arco_cabeza(marco, -1.35, 1.35, -0.03, 0.02, 0.02, 0.08)
    cab = Vector(PARTES["Cabeza"][0])
    for lado in (-1, 1):
        marco.cilindro(cab + Vector((lado * 0.68, 0.12, 0.0)), 0.13, 0.08, n=12, eje="X")


def accesorio_gafas(mallas):
    marco = mallas("Cabeza", "Oscuro")
    cristal = mallas("Cabeza", "Cristal")
    cab = Vector(PARTES["Cabeza"][0])
    for lado in (-1, 1):
        centro = cab + Vector((lado * 0.24, 0.1, -0.67))
        marco.tubo([centro + Vector((math.cos(a) * 0.17, math.sin(a) * 0.14, 0)) for a in
                    [2 * math.pi * k / 14 for k in range(15)]], [0.025] * 15, n=5, cerrar=False)
        cristal.cilindro(centro + Vector((0, 0, 0.005)), 0.16, 0.02, n=14, eje="Z", escala=(1.0, 0.85, 1.0))
        # Patilla hasta la oreja.
        marco.tubo([cab + Vector((lado * 0.41, 0.12, -0.66)), cab + Vector((lado * 0.64, 0.13, -0.45)),
                    cab + Vector((lado * 0.66, 0.1, 0.05))], [0.025, 0.025, 0.025], n=5)
    marco.tubo([cab + Vector((-0.08, 0.13, -0.68)), cab + Vector((0, 0.16, -0.7)), cab + Vector((0.08, 0.13, -0.68))],
               [0.022, 0.022, 0.022], n=5)


def accesorio_auriculares(mallas):
    cab = Vector(PARTES["Cabeza"][0])
    oscuro = mallas("Cabeza", "Oscuro")
    neon = mallas("Cabeza", "Neon")
    metal = mallas("Cabeza", "Metal")
    pts = [cab + Vector((0.72 * math.cos(a), 0.05 + 0.75 * math.sin(a), 0.02)) for a in
           [math.radians(x) for x in range(5, 180, 14)]]
    metal.tubo(pts, [0.05] * len(pts), n=6, aplastar=1.6)
    for lado in (-1, 1):
        oscuro.cilindro(cab + Vector((lado * 0.72, 0.02, 0.02)), 0.27, 0.16, n=16, eje="X")
        neon.cilindro(cab + Vector((lado * 0.81, 0.02, 0.02)), 0.17, 0.03, n=16, eje="X")
        oscuro.tubo([cab + Vector((lado * 0.74, -0.12, -0.12)), cab + Vector((lado * 0.6, -0.4, -0.5)),
                     cab + Vector((lado * 0.25, -0.46, -0.66))], [0.03, 0.03, 0.03], n=5) if lado == 1 else None
    neon.esfera(cab + Vector((0.22, -0.46, -0.67)), (0.05, 0.05, 0.05), u=8, v=6)


def accesorio_gorra(mallas):
    cab = Vector(PARTES["Cabeza"][0])
    gorra = mallas("Cabeza", "Detalle")
    casquete(gorra, lambda th: s_de_altura(0.28 + 0.06 * mezcla(th, math.pi, 1.4)), lambda th, t: 0.12 + 0.03 * (1 - t),
             n_t=24, n_s=7)
    # Visera hacia delante, un poco curvada.
    filas = []
    for i in range(9):
        a = -1.0 + 2.0 * i / 8
        x = 0.6 * math.sin(a)
        z0 = -0.7 * math.cos(a)
        fila = [m for m in (Vector((x, 0.28, z0)), Vector((x * 0.95, 0.24 - 0.04 * math.cos(a), z0 - 0.42 * math.cos(a) ** 0.6)))]
        filas.append(fila)
    vs = []
    for f in filas:
        vs.append([gorra.v(cab + f[0]), gorra.v(cab + f[1]), gorra.v(cab + f[1] + Vector((0, 0.035, 0))),
                   gorra.v(cab + f[0] + Vector((0, 0.035, 0)))])
    for i in range(len(vs) - 1):
        for k in range(4):
            k2 = (k + 1) % 4
            gorra.cara([vs[i][k], vs[i][k2], vs[i + 1][k2], vs[i + 1][k]])
    gorra.cara(vs[0])
    gorra.cara(list(reversed(vs[-1])))
    mallas("Cabeza", "Oscuro").esfera(cab + Vector((0, 0.78, 0)), (0.06, 0.04, 0.06), u=8, v=5)


def accesorio_cinta(mallas):
    arco_cabeza(mallas("Cabeza", "Detalle"), -math.pi, math.pi, 0.26, 0.4, 0.06, 0.04, n=28)
    cab = Vector(PARTES["Cabeza"][0])
    nudo = mallas("Cabeza", "Detalle")
    nudo.caja(cab + Vector((0.2, 0.33, 0.74)), (0.12, 0.14, 0.08), bisel=0.03)
    for lado, giro in ((1, -0.5), (-1, 0.4)):
        nudo.caja(cab + Vector((0.2 + lado * 0.1, 0.12, 0.8)), (0.11, 0.4, 0.03), giro=(0.2, 0, giro), bisel=0.01)


def accesorio_comunicador(mallas):
    cab = Vector(PARTES["Cabeza"][0])
    mallas("Cabeza", "Oscuro").cilindro(cab + Vector((-0.68, 0.06, 0.0)), 0.16, 0.1, n=12, eje="X")
    mallas("Cabeza", "Metal").tubo([cab + Vector((-0.72, 0.0, -0.08)), cab + Vector((-0.7, -0.18, -0.4)),
                                    cab + Vector((-0.5, -0.3, -0.62))], [0.025, 0.025, 0.025], n=5)
    neon = mallas("Cabeza", "Neon")
    neon.esfera(cab + Vector((-0.48, -0.3, -0.64)), (0.05, 0.05, 0.05), u=8, v=6)
    neon.cilindro(cab + Vector((-0.74, 0.06, 0.0)), 0.07, 0.02, n=10, eje="X")
    # Antena corta.
    mallas("Cabeza", "Metal").cilindro(cab + Vector((-0.7, 0.4, 0.06)), 0.015, 0.45, n=5, eje="Y")


ACCESORIOS = [
    ("Visor", accesorio_visor), ("Gafas", accesorio_gafas), ("Auriculares", accesorio_auriculares),
    ("Gorra", accesorio_gorra), ("Cinta", accesorio_cinta), ("Comunicador", accesorio_comunicador),
]


# ==============================================================================================================
# Ropa: detalles 3D sobre el R6 (el cuerpo se pinta con el color de la chaqueta o del pantalón)
# ==============================================================================================================


def centro_parte(parte, local):
    return Vector(PARTES[parte][0]) + Vector(local)


def manga_corta(mallas, rol="Chaqueta"):
    for lado in ("BrazoI", "BrazoD"):
        mallas(lado, rol).caja(centro_parte(lado, (0, 0.62, 0)), (1.1, 0.78, 1.1), bisel=0.08)
        mallas(lado, rol).banda(centro_parte(lado, (0, 0.24, 0)), (0.55, 0.55), 0.1, 0.03, radio_esq=0.1)


def punos(mallas, rol="Detalle", alto=0.22):
    for lado in ("BrazoI", "BrazoD"):
        mallas(lado, rol).banda(centro_parte(lado, (0, -0.86, 0)), (0.5, 0.5), alto, 0.05, radio_esq=0.08)


def chaqueta_exploradora(mallas):
    det = mallas("Torso", "Detalle")
    det.banda(centro_parte("Torso", (0, 1.06, 0)), (0.5, 0.36), 0.18, 0.07, radio_esq=0.14, hueco=0.35)
    for x in (-0.5, 0.5):
        det.caja(centro_parte("Torso", (x, 0.3, -0.53)), (0.52, 0.44, 0.07), bisel=0.04)
        det.caja(centro_parte("Torso", (x, 0.55, -0.565)), (0.58, 0.13, 0.08), bisel=0.03)
    mallas("Torso", "Metal").caja(centro_parte("Torso", (0, -0.05, -0.525)), (0.07, 1.85, 0.05), bisel=0.015)
    mallas("Torso", "Neon").cilindro(centro_parte("Torso", (0.5, 0.78, -0.53)), 0.06, 0.05, n=10, eje="Z")
    # Capucha recogida en la espalda.
    mallas("Torso", "Chaqueta").tubo([centro_parte("Torso", (-0.62, 0.9, 0.42)), centro_parte("Torso", (-0.3, 0.86, 0.62)),
                                      centro_parte("Torso", (0.3, 0.86, 0.62)), centro_parte("Torso", (0.62, 0.9, 0.42))],
                                     [0.12, 0.2, 0.2, 0.12], n=8)
    punos(mallas)
    for lado in ("BrazoI", "BrazoD"):
        mallas(lado, "Detalle").caja(centro_parte(lado, (0, 0.88, 0)), (1.08, 0.2, 1.08), bisel=0.06)


def chaqueta_piloto(mallas):
    det = mallas("Torso", "Detalle")
    det.banda(centro_parte("Torso", (0, 1.12, 0)), (0.46, 0.34), 0.3, 0.06, radio_esq=0.14)
    osc = mallas("Torso", "Oscuro")
    for sentido in (-1, 1):
        osc.caja(centro_parte("Torso", (0, 0.05, -0.53)), (0.16, 2.3, 0.05), giro=(0, 0, sentido * 0.52))
    osc.caja(centro_parte("Torso", (0, 0.05, -0.56)), (0.34, 0.34, 0.06), bisel=0.05)
    mallas("Torso", "Metal").cilindro(centro_parte("Torso", (0, 0.05, -0.6)), 0.1, 0.04, n=12, eje="Z")
    mallas("Torso", "Neon").caja(centro_parte("Torso", (-0.55, 0.62, -0.53)), (0.3, 0.12, 0.04), bisel=0.01)
    for lado in ("BrazoI", "BrazoD"):
        hombro = mallas(lado, "Detalle")
        hombro.caja(centro_parte(lado, (0, 0.82, 0)), (1.16, 0.4, 1.14), bisel=0.12)
        mallas(lado, "Oscuro").banda(centro_parte(lado, (0, -0.15, 0)), (0.5, 0.5), 0.14, 0.04, radio_esq=0.08)
    punos(mallas, "Oscuro", 0.3)


def chaqueta_cazadora(mallas):
    det = mallas("Torso", "Detalle")
    det.banda(centro_parte("Torso", (0, -0.86, 0)), (1.0, 0.5), 0.28, 0.05, radio_esq=0.1)
    det.banda(centro_parte("Torso", (0, 1.05, 0)), (0.48, 0.34), 0.16, 0.06, radio_esq=0.14, hueco=0.3)
    mallas("Torso", "Metal").caja(centro_parte("Torso", (0.12, 0.05, -0.525)), (0.06, 1.7, 0.05), bisel=0.015)
    mallas("Torso", "Metal").caja(centro_parte("Torso", (0.12, 0.62, -0.56)), (0.08, 0.16, 0.04), bisel=0.015)
    punos(mallas, "Detalle", 0.26)
    mallas("BrazoI", "Detalle").caja(centro_parte("BrazoI", (-0.53, 0.45, 0)), (0.07, 0.4, 0.5), bisel=0.03)
    mallas("BrazoI", "Metal").caja(centro_parte("BrazoI", (-0.56, 0.62, 0)), (0.04, 0.05, 0.36))


def chaqueta_mecanico(mallas):
    det = mallas("Torso", "Detalle")
    for x in (-0.45, 0.45):
        det.caja(centro_parte("Torso", (x, 0.25, -0.53)), (0.24, 1.55, 0.05), bisel=0.02)
        det.caja(centro_parte("Torso", (x, 1.02, 0)), (0.24, 0.05, 1.08), bisel=0.02)
        det.caja(centro_parte("Torso", (x, 0.25, 0.53)), (0.24, 1.55, 0.05), bisel=0.02)
        mallas("Torso", "Metal").caja(centro_parte("Torso", (x, 0.45, -0.57)), (0.16, 0.12, 0.04), bisel=0.02)
    det.caja(centro_parte("Torso", (0, -0.55, -0.53)), (1.3, 0.9, 0.05), bisel=0.03)
    det.caja(centro_parte("Torso", (0, -0.45, -0.57)), (0.5, 0.36, 0.05), bisel=0.03)
    mallas("Torso", "Oscuro").caja(centro_parte("Torso", (0.82, -0.75, -0.2)), (0.24, 0.45, 0.5), bisel=0.05)
    manga_corta(mallas)


def chaqueta_camiseta(mallas):
    mallas("Torso", "Detalle").banda(centro_parte("Torso", (0, 0.97, -0.02)), (0.42, 0.3), 0.07, 0.04, radio_esq=0.14)
    mallas("Torso", "Detalle").caja(centro_parte("Torso", (0, 0.25, -0.52)), (0.8, 0.5, 0.03), bisel=0.01)
    manga_corta(mallas)


# Ropa: (id, función, color de cada parte del cuerpo). Lo segundo lo usan los datos del juego (DatosHumanos).
CHAQUETAS = [
    ("Exploradora", chaqueta_exploradora), ("Piloto", chaqueta_piloto), ("Cazadora", chaqueta_cazadora),
    ("Mecanico", chaqueta_mecanico), ("Camiseta", chaqueta_camiseta),
]


def cinturon(mallas):
    mallas("Torso", "Oscuro").banda(centro_parte("Torso", (0, -0.9, 0)), (1.0, 0.5), 0.2, 0.05, radio_esq=0.08)
    mallas("Torso", "Metal").caja(centro_parte("Torso", (0, -0.9, -0.57)), (0.26, 0.2, 0.05), bisel=0.03)


def botas(mallas, rol="Oscuro", suela="Oscuro", alto=0.62):
    for lado in ("PiernaI", "PiernaD"):
        b = mallas(lado, rol)
        b.caja(centro_parte(lado, (0, -1 + alto / 2, 0.0)), (1.1, alto, 1.1), bisel=0.08)
        b.caja(centro_parte(lado, (0, -0.86, -0.56)), (1.06, 0.28, 0.24), bisel=0.08)
        mallas(lado, suela).caja(centro_parte(lado, (0, -0.97, -0.06)), (1.14, 0.08, 1.3), bisel=0.03)


def pantalon_cargo(mallas):
    cinturon(mallas)
    botas(mallas)
    for lado, s in (("PiernaI", -1), ("PiernaD", 1)):
        mallas(lado, "Pantalon").caja(centro_parte(lado, (s * 0.53, 0.2, 0)), (0.1, 0.5, 0.6), bisel=0.03)
        mallas(lado, "Pantalon").caja(centro_parte(lado, (s * 0.565, 0.43, 0)), (0.06, 0.12, 0.64), bisel=0.02)
        mallas(lado, "Oscuro").caja(centro_parte(lado, (0, -0.15, -0.54)), (0.68, 0.42, 0.1), bisel=0.05)


def pantalon_piloto(mallas):
    cinturon(mallas)
    botas(mallas, alto=0.9)
    for lado, s in (("PiernaI", -1), ("PiernaD", 1)):
        mallas(lado, "Detalle").caja(centro_parte(lado, (s * 0.51, 0.35, 0)), (0.04, 1.3, 0.16))
        mallas(lado, "Detalle").caja(centro_parte(lado, (0, 0.0, -0.55)), (0.7, 0.46, 0.12), bisel=0.06)


def pantalon_vaquero(mallas):
    cinturon(mallas)
    botas(mallas, rol="Claro", suela="Oscuro", alto=0.34)
    for lado in ("PiernaI", "PiernaD"):
        mallas(lado, "Pantalon").banda(centro_parte(lado, (0, -0.56, 0)), (0.5, 0.5), 0.14, 0.045, radio_esq=0.08)
        mallas(lado, "Pantalon").caja(centro_parte(lado, (0, 0.65, 0.53)), (0.5, 0.42, 0.05), bisel=0.03)


def pantalon_tactico(mallas):
    cinturon(mallas)
    botas(mallas, alto=0.7)
    for lado, s in (("PiernaI", -1), ("PiernaD", 1)):
        mallas(lado, "Oscuro").banda(centro_parte(lado, (0, 0.52, 0)), (0.5, 0.5), 0.12, 0.04, radio_esq=0.08)
        mallas(lado, "Oscuro").banda(centro_parte(lado, (0, 0.12, 0)), (0.5, 0.5), 0.1, 0.04, radio_esq=0.08)
        mallas(lado, "Oscuro").caja(centro_parte(lado, (0, -0.16, -0.55)), (0.74, 0.45, 0.12), bisel=0.06)
    mallas("PiernaD", "Detalle").caja(centro_parte("PiernaD", (0.58, 0.32, 0)), (0.18, 0.5, 0.56), bisel=0.05)
    mallas("PiernaD", "Metal").caja(centro_parte("PiernaD", (0.68, 0.45, 0)), (0.04, 0.1, 0.3))


PANTALONES = [
    ("Cargo", pantalon_cargo), ("Piloto", pantalon_piloto), ("Vaquero", pantalon_vaquero),
    ("Tactico", pantalon_tactico),
]


# ==============================================================================================================
# Construcción, exportación y hoja de contactos
# ==============================================================================================================


def a_blender(bm):
    """Coordenadas de Roblox -> Blender (lo contrario de a_roblox): (x, y, z) -> (-x, z, y)."""
    m = Matrix(((-1, 0, 0, 0), (0, 0, 1, 0), (0, 1, 0, 0), (0, 0, 0, 1)))
    bmesh.ops.transform(bm, matrix=m, verts=bm.verts)


def a_roblox(p):
    x, y, z = p
    return [round(-x, 4), round(z, 4), round(y, 4)]


def construir_categoria(categoria, lista, materiales):
    """Construye cada elemento de la lista; devuelve {nombre: objeto}."""
    objetos = {}
    for id_, funcion in lista:
        mallas = {}

        def pedir(parte, rol, mallas=mallas):
            if (parte, rol) not in mallas:
                mallas[(parte, rol)] = Malla()
            return mallas[(parte, rol)]

        if categoria == "Cabello":
            funcion(pedir("Cabeza", "Pelo"))
        else:
            funcion(pedir)
        for (parte, rol), malla in mallas.items():
            bm = malla.bm
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0005)
            bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
            a_blender(bm)
            nombre = f"{categoria}_{id_}__{parte}__{rol}"
            obj = c.objeto_desde_bmesh(nombre, bm, [materiales[rol]])
            c.sombreado_suave(obj, 50)
            mn, mx = c.caja_limite([obj])
            centro = (mn + mx) / 2
            obj.data.transform(Matrix.Translation(-centro))
            obj.location = centro
            obj["categoria"] = categoria
            obj["id"] = id_
            obj["parte"] = parte
            obj["rol"] = rol
            objetos[nombre] = obj
    return objetos


def maniqui(materiales):
    """R6 de muestra para los renders (no se exporta)."""
    objs = []
    for parte, (centro, _) in PARTES.items():
        m = Malla()
        if parte == "Cabeza":
            # Cilindro redondeado como la malla de cabeza de Roblox.
            m.cilindro(Vector(centro), 0.6, 1.2 - 0.3, n=24, eje="Y")
            for s in (1, -1):
                m.esfera(Vector(centro) + Vector((0, s * 0.45, 0)), (0.6, 0.16, 0.6), u=24, v=8)
        else:
            tam = (2, 2, 1) if parte == "Torso" else (1, 2, 1)
            m.caja(Vector(centro), tam, bisel=0.02)
        a_blender(m.bm)
        rol = "Piel" if parte == "Cabeza" else ("Chaqueta" if parte in ("Torso", "BrazoI", "BrazoD") else "Pantalon")
        o = c.objeto_desde_bmesh("Maniqui_" + parte, m.bm, [materiales[rol]])
        c.sombreado_suave(o, 50)
        o["maniqui"] = True
        objs.append(o)
    return objs


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--sin_render", action="store_true")
    args = ap.parse_args(argv)
    salida = os.path.abspath(args.salida)
    os.makedirs(os.path.join(salida, "roblox"), exist_ok=True)

    c.escena_vacia()
    materiales = {}
    for rol, hexa in MUESTRA.items():
        materiales[rol] = c.material(
            "m_" + rol, c.srgb(hexa), rugosidad=0.25 if rol in ("Metal", "Cristal") else 0.6,
            metal=0.8 if rol == "Metal" else 0.0,
            emision=c.srgb(hexa) if rol == "Neon" else None, fuerza_emision=4.0 if rol == "Neon" else 0.0)

    grupos = {
        "Cabellos": construir_categoria("Cabello", CABELLOS, materiales),
        "Accesorios": construir_categoria("Accesorio", ACCESORIOS, materiales),
        "Chaquetas": construir_categoria("Chaqueta", CHAQUETAS, materiales),
        "Pantalones": construir_categoria("Pantalon", PANTALONES, materiales),
    }

    piezas = {}
    por_elemento = {}
    for archivo, objetos in grupos.items():
        c.exportar_fbx(os.path.join(salida, "roblox", archivo + ".fbx"), list(objetos.values()), incrustar_texturas=False)
        for nombre, o in objetos.items():
            parte = o["parte"]
            centro_parte_r = Vector(PARTES[parte][0])
            centro = Vector(a_roblox(tuple(o.location / E))) - centro_parte_r
            tam = Vector(a_roblox(tuple(Vector(o.dimensions) / E)))
            tris = c.triangulos(o)
            piezas[nombre] = {
                "Archivo": archivo, "Categoria": o["categoria"], "Id": o["id"], "Parte": PARTES[parte][1],
                "Rol": o["rol"], "Centro": [round(v, 4) for v in centro],
                "Tamano": [round(abs(v), 4) for v in tam], "Triangulos": tris,
            }
            clave = f'{o["categoria"]}_{o["id"]}'
            por_elemento[clave] = por_elemento.get(clave, 0) + tris
    with open(os.path.join(salida, "piezas.json"), "w", encoding="utf-8") as f:
        json.dump({"nota": "studs, ejes de Roblox; Centro = respecto al centro de la parte del R6",
                   "Piezas": piezas, "TriangulosPorElemento": por_elemento}, f, indent=1, ensure_ascii=False)
    print("[ok] triángulos por elemento:")
    for k, v in sorted(por_elemento.items()):
        aviso = "  <-- PASA DE 1500" if v >= 1500 and (k.startswith("Cabello") or k.startswith("Accesorio")) else ""
        print(f"   {k}: {v}{aviso}")

    if args.sin_render:
        return

    # Hoja de contactos: cada peinado y accesorio sobre la cabeza; cada chaqueta y pantalón sobre el maniquí.
    cuerpo = maniqui(materiales)
    cabeza = [o for o in cuerpo if o.name == "Maniqui_Cabeza"]
    c.preparar_estudio(z_suelo=-3.0 * E, luz_clave=500)
    tmp = os.path.join(salida, "_render_tmp")
    tam = 260 if args.rapido else 360
    muestras = 12 if args.rapido else 40
    filas = []
    for archivo, vistas in (("Cabellos", [("Frente", 0, 6), ("3-4", -40, 12), ("Detras", 160, 10)]),
                            ("Accesorios", [("Frente", 0, 6), ("3-4", -40, 12)]),
                            ("Chaquetas", [("Frente", 0, 6), ("Detras", 160, 10)]),
                            ("Pantalones", [("Frente", 0, 6), ("3-4", -40, 4)])):
        objetos = grupos[archivo]
        ids = []
        for o in objetos.values():
            if o["id"] not in ids:
                ids.append(o["id"])
        for id_ in ids:
            propios = [o for o in objetos.values() if o["id"] == id_]
            base = cabeza if archivo in ("Cabellos", "Accesorios") else cuerpo
            rutas = c.renderizar_vistas(propios + base, tmp, vistas, tam=tam, muestras=muestras, con_malla=False,
                                        margen=0.85 if archivo in ("Cabellos", "Accesorios") else 0.7,
                                        prefijo=f"{archivo}_{id_}_")
            n = por_elemento[f'{propios[0]["categoria"]}_{id_}']
            filas.append([(f"{id_} · {n} tri · {nv}", r) for nv, r in rutas])
    columnas = 6
    planas = [x for fila in filas for x in fila]
    filas_hoja = [planas[i:i + columnas] for i in range(0, len(planas), columnas)]
    c.montar_hoja(filas_hoja, os.path.join(salida, f"hoja_contactos_{args.ronda}.png"),
                  f"Personaje humano — piezas 3D — ronda {args.ronda}",
                  notas=["Colores de muestra: en el juego los elige el jugador (pelo, chaqueta, pantalón, detalles)."],
                  columnas=columnas)


if __name__ == "__main__":
    main()
