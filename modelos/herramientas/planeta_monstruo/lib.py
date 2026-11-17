"""
Cadena de producción de los modelos del Planeta Monstruo (Blender sin pantalla, bpy).

Cada modelo se hace en su propia escena limpia y sigue siempre los mismos pasos:

  1. MODELADO. Cada pieza tiene dos tipos de geometría:
       * orgánica: primitivas de volumen (campos de distancia) que se funden entre sí con unión suave, se pueden
         vaciar y restar, y se convierten en una malla alta con «marching cubes». De ahí sale la malla baja
         (decimado) que va al juego. Así la carne, el hueso y la roca se funden como algo que ha crecido.
       * dura: geometría directa de pocos polígonos (espinas, dientes, cristales, membranas con grosor, hilos).
     Todo tiene volumen real: no hay planos sueltos.
  2. MATERIALES procedurales en 3D (sin costuras) sobre la malla alta.
  3. HORNEADO a un atlas 1024 compartido por todas las piezas del modelo: color (con oclusión), normales,
     rugosidad, metal y emisión.
  4. TURNAROUND de 6 vistas con estudio de 3 luces.
  5. FBX (1 unidad = 1 stud, giro de importación de 180° aplicado) y verificación reimportándolo.
  6. JSON con triángulos, tamaño, piezas y, en las bestias, articulaciones y puntos de montura.

Ejes al modelar: X = ancho, Y = fondo (el frente mira a -Y), Z = arriba. Medidas en studs.
"""

import json
import math
import os
import random
import time
import zlib

import bpy  # bpy primero: bmesh y mathutils vienen con él
import bmesh
import numpy as np
from mathutils import Euler, Matrix, Vector
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from skimage import measure

VIOLETA = "#C04DFF"
VERDE = "#39FF14"
ROJO = "#FF2A2A"
AMARILLO = "#FFD21F"
TAM_ATLAS = 1024
GRANDE = 1e3


def srgb(hexa):
    """'#RRGGBB' -> color lineal."""
    hexa = hexa.lstrip("#")
    c = [int(hexa[i: i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def log(*a):
    print("[pm]", *a, flush=True)


# ----------------------------------------------------------------------------------------------------------
# Curvas y utilidades geométricas
# ----------------------------------------------------------------------------------------------------------


def curva(pts, n=16):
    """Catmull-Rom por los puntos de control: devuelve n+1 puntos repartidos por la curva."""
    P = [np.asarray(p, float) for p in pts]
    if len(P) < 3:
        return [P[0] + (P[-1] - P[0]) * t for t in np.linspace(0, 1, n + 1)]
    Q = [2 * P[0] - P[1]] + P + [2 * P[-1] - P[-2]]
    tramos = len(P) - 1
    out = []
    for i in range(n + 1):
        u = i / n * tramos
        k = min(int(u), tramos - 1)
        t = u - k
        p0, p1, p2, p3 = Q[k], Q[k + 1], Q[k + 2], Q[k + 3]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return out


def radios_de(radios, n):
    """Radios para n puntos a partir de un número, una lista (se interpola) o una función t->r."""
    if callable(radios):
        return [float(radios(i / (n - 1))) for i in range(n)]
    if isinstance(radios, (int, float)):
        return [float(radios)] * n
    r = list(radios)
    if len(r) == n:
        return [float(x) for x in r]
    xs = np.linspace(0, 1, len(r))
    return [float(np.interp(i / (n - 1), xs, r)) for i in range(n)]


def anillo_pts(c, r, n, z=None, fase=0.0, ry=None):
    """n puntos en círculo horizontal alrededor de c."""
    c = np.asarray(c, float)
    ry = r if ry is None else ry
    return [c + np.array([math.cos(fase + math.tau * i / n) * r, math.sin(fase + math.tau * i / n) * ry, 0.0])
            for i in range(n)]


def _T(pos=(0, 0, 0), rot=None, esc=None, eje=None, espejo=False):
    """Matriz local->mundo. rot = Euler en grados; eje = dirección a la que apunta el Z local."""
    if esc is None:
        esc = (1, 1, 1)
    if isinstance(esc, (int, float)):
        esc = (esc, esc, esc)
    if eje is not None:
        R = Vector(eje).normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()
        if rot is not None:
            R = R @ Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
    elif rot is not None:
        R = Euler([math.radians(a) for a in rot]).to_matrix().to_4x4()
    else:
        R = Matrix.Identity(4)
    M = Matrix.Translation(Vector(pos)) @ R @ Matrix.Diagonal((*esc, 1.0))
    if espejo:
        M = Matrix.Diagonal((-1, 1, 1, 1)) @ M
    return M


def _marcos(P):
    """Marcos de transporte paralelo a lo largo de una polilínea: lista de (tangente, u, v)."""
    P = [np.asarray(p, float) for p in P]
    n = len(P)
    tang = []
    for i in range(n):
        a = P[max(i - 1, 0)]
        b = P[min(i + 1, n - 1)]
        t = b - a
        L = np.linalg.norm(t)
        tang.append(t / L if L > 1e-9 else np.array([0, 0, 1.0]))
    t0 = tang[0]
    ref = np.array([0, 0, 1.0]) if abs(t0[2]) < 0.9 else np.array([1.0, 0, 0])
    u = np.cross(ref, t0)
    u /= np.linalg.norm(u)
    out = []
    for i in range(n):
        t = tang[i]
        u = u - t * np.dot(u, t)
        L = np.linalg.norm(u)
        if L < 1e-6:
            ref = np.array([0, 0, 1.0]) if abs(t[2]) < 0.9 else np.array([1.0, 0, 0])
            u = np.cross(ref, t)
            L = np.linalg.norm(u)
        u = u / L
        v = np.cross(t, u)
        out.append((t, u.copy(), v))
    return out


# ----------------------------------------------------------------------------------------------------------
# Campos de distancia (geometría orgánica)
# ----------------------------------------------------------------------------------------------------------


def _d_conoredondo(P, a, b, r1, r2):
    ba = b - a
    l2 = float(ba @ ba)
    rr = r1 - r2
    if l2 < 1e-10 or l2 - rr * rr <= 1e-10:  # degenerado: esfera
        c, r = (a, r1) if r1 >= r2 else (b, r2)
        return np.linalg.norm(P - c, axis=1) - r
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = P - a
    y = pa @ ba
    z = y - l2
    w = pa * l2 - np.outer(y, ba)
    x2 = np.einsum("ij,ij->i", w, w)
    y2 = y * y * l2
    z2 = z * z * l2
    k = np.sign(rr) * rr * rr * x2
    d = (np.sqrt(x2 * a2 * il2) + y * rr) * il2 - r1
    c1 = np.sign(z) * a2 * z2 > k
    c2 = np.sign(y) * a2 * y2 < k
    d = np.where(c2, np.sqrt(x2 + y2) * il2 - r1, d)
    d = np.where(c1, np.sqrt(x2 + z2) * il2 - r2, d)
    return d


def _d_conotapado(P, a, b, ra, rb):
    ba = b - a
    baba = float(ba @ ba)
    pa = P - a
    papa = np.einsum("ij,ij->i", pa, pa)
    paba = (pa @ ba) / baba
    x = np.sqrt(np.maximum(papa - paba * paba * baba, 0))
    cax = np.maximum(0.0, x - np.where(paba < 0.5, ra, rb))
    cay = np.abs(paba - 0.5) - 0.5
    rba = rb - ra
    k = rba * rba + baba
    f = np.clip((rba * (x - ra) + paba * baba) / k, 0, 1)
    cbx = x - ra - f * rba
    cby = paba - f
    s = np.where((cbx < 0) & (cay < 0), -1.0, 1.0)
    return s * np.sqrt(np.minimum(cax * cax + cay * cay * baba, cbx * cbx + cby * cby * baba))


def _d_poligono(px, py, V):
    V = np.asarray(V, float)
    M = len(V)
    d = (px - V[0, 0]) ** 2 + (py - V[0, 1]) ** 2
    s = np.ones_like(px)
    j = M - 1
    for i in range(M):
        e0, e1 = V[j, 0] - V[i, 0], V[j, 1] - V[i, 1]
        wx, wy = px - V[i, 0], py - V[i, 1]
        ee = e0 * e0 + e1 * e1
        t = np.clip((wx * e0 + wy * e1) / (ee if ee > 1e-12 else 1e-12), 0, 1)
        bx, by = wx - e0 * t, wy - e1 * t
        d = np.minimum(d, bx * bx + by * by)
        c1 = py >= V[i, 1]
        c2 = py < V[j, 1]
        c3 = e0 * wy > e1 * wx
        gira = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(gira, -s, s)
        j = i
    return s * np.sqrt(d)


def _smin(a, b, k):
    if k <= 1e-6:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


class Prim:
    """Una primitiva de volumen: función de distancia local + transformación + cómo se combina."""

    def __init__(self, fn, mn, mx, mat, T=None, k=0.0, resta=False, cascara=None, partes=None, infla=0.0):
        self.infla = infla  # engorda (o adelgaza) la forma esta distancia
        self.fn = fn
        self.mat = mat
        self.k = k
        self.resta = resta
        self.cascara = cascara
        self.partes = partes
        mn = np.asarray(mn, float)
        mx = np.asarray(mx, float)
        if T is not None:
            A = np.array(T)
            inv = np.linalg.inv(A)
            self.R = inv[:3, :3]
            self.t = inv[:3, 3]
            self.sc = float(min(np.linalg.norm(A[:3, i]) for i in range(3)))
            esq = np.array([[x, y, z] for x in (mn[0], mx[0]) for y in (mn[1], mx[1]) for z in (mn[2], mx[2])])
            W = esq @ A[:3, :3].T + A[:3, 3]
            mn, mx = W.min(0), W.max(0)
        else:
            self.R = None
            self.sc = 1.0
        self.mn, self.mx = mn - max(infla, 0.0), mx + max(infla, 0.0)

    def d(self, P):
        if self.R is not None:
            P = P @ self.R.T + self.t
        d = self.fn(P) * self.sc - self.infla
        if self.cascara:
            d = np.abs(d + self.cascara / 2) - self.cascara / 2
        return d

    def d_puntos(self, P, pad):
        """Distancia en puntos sueltos (solo los que caen en la caja; el resto, lejos)."""
        out = np.full(len(P), GRANDE, np.float32)
        lista = self.partes if self.partes is not None else [(self.mn, self.mx, None)]
        for pmn, pmx, fn in lista:
            m = np.all((P >= pmn - pad) & (P <= pmx + pad), axis=1)
            if not m.any():
                continue
            d = self.d(P[m]) if fn is None else fn(P[m]) - self.infla
            out[m] = np.minimum(out[m], d)
        if self.partes is not None and self.cascara:
            out = np.abs(out + self.cascara / 2) - self.cascara / 2
        return out


_RUIDO = np.random.RandomState(7).rand(48, 48, 48).astype(np.float32)


def ruido3(P, freq, octavas=3, semilla=0.0):
    """Ruido de valor fractal en [-1, 1] (aprox.), barato y repetible."""
    out = np.zeros(len(P), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octavas):
        Q = (P * (freq * 2 ** o) + semilla + o * 17.3) % 48
        out += amp * ndimage.map_coordinates(_RUIDO, Q.T, order=1, mode="grid-wrap")
        tot += amp
        amp *= 0.5
    return (out / tot - 0.5) * 2.4


class Organico:
    """Lista ordenada de primitivas que se evalúa en una rejilla y se convierte en malla."""

    def __init__(self):
        self.prims = []
        self.masc = []  # máscara: la pieza solo existe donde también hay máscara (intersección)

    def vacio(self):
        return not self.prims

    def caja(self):
        pos = [p for p in self.prims if not p.resta]
        mn = np.min([p.mn for p in pos], axis=0)
        mx = np.max([p.mx for p in pos], axis=0)
        return mn, mx

    def malla(self, res, ruido=None, suelo=None, techo=None, semilla=0.0, min_isla=40, h_fijo=None, planos=()):
        """Devuelve (verts, caras, mat_por_cara, h)."""
        mn, mx = self.caja()
        amp = ruido[0] if ruido else 0.0
        h = h_fijo or max(float((mx - mn).max()) / res, 0.004)
        mn = mn - (3 * h + amp)
        mx = mx + (3 * h + amp)
        if suelo is not None:
            mn[2] = max(mn[2], suelo - 2 * h)
        if techo is not None:
            mx[2] = min(mx[2], techo + 2 * h)
        ejes = [np.arange(mn[i], mx[i] + h, h, dtype=np.float32) for i in range(3)]
        def rango(a, b):
            sl = []
            for i in range(3):
                i0 = max(int(math.floor((a[i] - mn[i]) / h)), 0)
                i1 = min(int(math.ceil((b[i] - mn[i]) / h)) + 1, len(ejes[i]))
                if i1 <= i0:
                    return None
                sl.append(slice(i0, i1))
            return tuple(sl)

        def puntos(sl):
            X, Y, Z = np.meshgrid(ejes[0][sl[0]], ejes[1][sl[1]], ejes[2][sl[2]], indexing="ij")
            return np.stack([X.ravel(), Y.ravel(), Z.ravel()], axis=1).astype(np.float64), X.shape

        def acumula(prims):
            F = np.full([len(e) for e in ejes], GRANDE, np.float32)
            for pr in prims:
                pad = pr.k + 2 * h
                sl = rango(pr.mn - pad, pr.mx + pad)
                if sl is None:
                    continue
                forma = tuple(s.stop - s.start for s in sl)
                if pr.partes is None:
                    P, _ = puntos(sl)
                    D = pr.d(P).reshape(forma).astype(np.float32)
                else:
                    D = np.full(forma, GRANDE, np.float32)
                    for pmn, pmx, fn in pr.partes:
                        s2 = rango(pmn - pad, pmx + pad)
                        if s2 is None:
                            continue
                        loc = tuple(slice(a.start - b.start, a.stop - b.start) for a, b in zip(s2, sl))
                        P, f2 = puntos(s2)
                        D[loc] = np.minimum(D[loc], fn(P).reshape(f2) - pr.infla)
                    if pr.cascara:
                        D = np.abs(D + pr.cascara / 2) - pr.cascara / 2
                A = F[sl]
                F[sl] = -_smin(-A, D, pr.k) if pr.resta else _smin(A, D, pr.k)
            return F

        F = acumula(self.prims)
        if self.masc:
            F = np.maximum(F, acumula(self.masc))

        if ruido:
            # Ruido solo cerca de la superficie (lo demás no cambia la malla).
            cerca = np.abs(F) < (amp * 1.5 + 2 * h)
            idx = np.argwhere(cerca)
            P = np.stack([ejes[i][idx[:, i]] for i in range(3)], axis=1).astype(np.float64)
            F[cerca] += amp * ruido3(P, ruido[1], ruido[2] if len(ruido) > 2 else 3, semilla)
        if suelo is not None:
            F = np.maximum(F, (suelo - ejes[2])[None, None, :])
        if techo is not None:
            F = np.maximum(F, (ejes[2] - techo)[None, None, :])
        for p0, nrm in planos:  # cortes planos: se queda el lado contrario a la normal
            nrm = np.asarray(nrm, float) / np.linalg.norm(nrm)
            D = ((ejes[0][:, None, None] - p0[0]) * nrm[0] + (ejes[1][None, :, None] - p0[1]) * nrm[1]
                 + (ejes[2][None, None, :] - p0[2]) * nrm[2])
            F = np.maximum(F, D.astype(np.float32))
        # Borde de la rejilla siempre fuera, para que la malla quede cerrada.
        F[0, :, :] = F[-1, :, :] = F[:, 0, :] = F[:, -1, :] = F[:, :, 0] = F[:, :, -1] = GRANDE
        # Fuera las motas sueltas que crea el ruido.
        if min_isla:
            etiq, n = ndimage.label(F < 0)
            if n > 1:
                tam = ndimage.sum_labels(np.ones_like(etiq), etiq, np.arange(1, n + 1))
                for i, t in enumerate(tam):
                    if t < min_isla:
                        F[etiq == i + 1] = GRANDE
        if not (F < 0).any():
            raise RuntimeError("campo vacío: la pieza orgánica no tiene volumen")
        verts, caras, _, _ = measure.marching_cubes(F, 0.0, spacing=(h, h, h))
        verts = verts.astype(np.float64) + mn
        # Normales hacia fuera: volumen con signo positivo.
        a, b, c = verts[caras[:, 0]], verts[caras[:, 1]], verts[caras[:, 2]]
        if np.einsum("ij,ij->i", a, np.cross(b, c)).sum() < 0:
            caras = caras[:, ::-1].copy()
        # Material de cada vértice: la primitiva cuya superficie le queda más cerca.
        mejor = np.full(len(verts), GRANDE, np.float32)
        mat_v = np.zeros(len(verts), np.int32)
        nombres = []
        for pr in self.prims:
            if pr.mat is None:
                continue
            if pr.mat not in nombres:
                nombres.append(pr.mat)
            d = np.abs(pr.d_puntos(verts, pr.k + amp + 2 * h))
            gana = d < mejor - 1e-6
            mejor[gana] = d[gana]
            mat_v[gana] = nombres.index(pr.mat)
        m0, m1, m2 = mat_v[caras[:, 0]], mat_v[caras[:, 1]], mat_v[caras[:, 2]]
        mat_c = np.where(m1 == m2, m1, m0)
        return verts, caras.astype(np.int32), mat_c, nombres, h


# ----------------------------------------------------------------------------------------------------------
# Geometría dura (directa, pocos polígonos, siempre sólidos cerrados)
# ----------------------------------------------------------------------------------------------------------


class Duro:
    def __init__(self):
        self.bm = bmesh.new()
        self.mats = []
        self.marco = None  # matriz local->mundo que se aplica a lo que se crea (la pone Pieza.en)

    def vacio(self):
        return len(self.bm.faces) == 0

    def _fin(self, verts, mat, sim):
        if mat not in self.mats:
            self.mats.append(mat)
        i = self.mats.index(mat)
        vs = set(verts)
        caras = {f for v in vs for f in v.link_faces}
        for f in caras:
            f.material_index = i
        if sim:
            aristas = {e for f in caras for e in f.edges}
            r = bmesh.ops.duplicate(self.bm, geom=list(vs) + list(aristas) + list(caras))
            for e in r["geom"]:
                if isinstance(e, bmesh.types.BMVert):
                    e.co.x = -e.co.x
            bmesh.ops.reverse_faces(self.bm, faces=[e for e in r["geom"] if isinstance(e, bmesh.types.BMFace)])
            verts = list(verts) + [e for e in r["geom"] if isinstance(e, bmesh.types.BMVert)]
        if self.marco is not None:
            bmesh.ops.transform(self.bm, matrix=self.marco, verts=list(verts))
        return verts

    def tubo(self, pts, radios, mat, n=6, sim=False, suave=0, aplastar=1.0):
        """Tubo cerrado a lo largo de una polilínea. Un radio 0 en un extremo lo acaba en punta."""
        if suave:
            pts = curva(pts, suave)
        P = [np.asarray(p, float) for p in pts]
        R = radios_de(radios, len(P))
        bm = self.bm
        marcos = _marcos(P)
        anillos = []
        for p, r, (t, u, v) in zip(P, R, marcos):
            if r <= 1e-5:
                anillos.append([bm.verts.new(p)])
            else:
                anillos.append([bm.verts.new(p + (u * math.cos(math.tau * i / n) + v * math.sin(math.tau * i / n)
                                                  * aplastar) * r) for i in range(n)])
        for a, b in zip(anillos[:-1], anillos[1:]):
            if len(a) == 1 and len(b) == 1:
                continue
            for i in range(n):
                j = (i + 1) % n
                if len(a) == 1:
                    bm.faces.new((a[0], b[j], b[i]))
                elif len(b) == 1:
                    bm.faces.new((a[i], a[j], b[0]))
                else:
                    bm.faces.new((a[i], a[j], b[j], b[i]))
        if len(anillos[0]) > 1:
            bm.faces.new(list(reversed(anillos[0])))
        if len(anillos[-1]) > 1:
            bm.faces.new(anillos[-1])
        return self._fin([v for a in anillos for v in a], mat, sim)

    def cono(self, a, b, r, mat, n=6, sim=False):
        return self.tubo([a, b], [r, 0], mat, n=n, sim=sim)

    def cuerno(self, pts, r, mat, n=6, seg=6, sim=False, aplastar=1.0, potencia=1.0):
        """Cuerno, colmillo o garra: tubo curvo que se afila hasta la punta."""
        P = curva(pts, seg)
        R = [r * (1 - i / seg) ** potencia for i in range(seg + 1)]
        R[-1] = 0
        return self.tubo(P, R, mat, n=n, sim=sim, aplastar=aplastar)

    def prisma(self, a, b, r, mat, n=6, punta=0.25, r2=None, sim=False, giro=0.0):
        """Cristal: prisma con punta."""
        a = np.asarray(a, float)
        b = np.asarray(b, float)
        m = a + (b - a) * (1 - punta)
        bm = self.bm
        (t, u, v) = _marcos([a, b])[0]
        r2 = r if r2 is None else r2

        def anillo(c, rr):
            return [bm.verts.new(c + (u * math.cos(giro + math.tau * i / n) + v * math.sin(giro + math.tau * i / n))
                                 * rr) for i in range(n)]

        A, B = anillo(a, r), anillo(m, r2)
        tip = bm.verts.new(b)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((A[i], A[j], B[j], B[i]))
            bm.faces.new((B[i], B[j], tip))
        bm.faces.new(list(reversed(A)))
        return self._fin(A + B + [tip], mat, sim)

    def esfera(self, c, r, mat, sub=2, esc=None, rot=None, eje=None, sim=False):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=r)
        e = esc if esc is not None else (1, 1, 1)
        bmesh.ops.transform(self.bm, matrix=_T(c, rot, e, eje), verts=res["verts"])
        return self._fin(res["verts"], mat, sim)

    def caja(self, c, tam, mat, rot=None, eje=None, sim=False):
        res = bmesh.ops.create_cube(self.bm, size=1.0)
        bmesh.ops.transform(self.bm, matrix=_T(c, rot, tam, eje), verts=res["verts"])
        return self._fin(res["verts"], mat, sim)

    def toro(self, c, R, r, mat, eje=(0, 0, 1), n=14, m=6, esc=None, sim=False, arco=1.0):
        """Anillo (o arco de anillo, cerrado por los extremos)."""
        bm = self.bm
        T = _T(c, None, esc, eje)
        cerrado = arco >= 0.999
        cuenta = n if cerrado else n + 1
        anillos = []
        for i in range(cuenta):
            a = math.tau * arco * i / n
            ca, sa = math.cos(a), math.sin(a)
            fila = []
            for j in range(m):
                b = math.tau * j / m
                rr = R + r * math.cos(b)
                fila.append(bm.verts.new(T @ Vector((rr * ca, rr * sa, r * math.sin(b)))))
            anillos.append(fila)
        for i in range(n if cerrado else n):
            a, b = anillos[i], anillos[(i + 1) % cuenta]
            for j in range(m):
                k = (j + 1) % m
                bm.faces.new((a[j], b[j], b[k], a[k]))
        if not cerrado:
            bm.faces.new(list(reversed(anillos[0])))
            bm.faces.new(anillos[-1])
        return self._fin([v for a in anillos for v in a], mat, sim)

    def torno(self, perfil, c, mat, n=12, eje=None, esc=None, rot=None, sim=False):
        """Sólido de revolución: perfil [(r, z)...] de abajo arriba; r = 0 en los extremos lo cierra en punta."""
        bm = self.bm
        T = _T(c, rot, esc, eje)
        anillos = []
        for r, z in perfil:
            if r <= 1e-6:
                anillos.append([bm.verts.new(T @ Vector((0, 0, z)))])
            else:
                anillos.append([bm.verts.new(T @ Vector((r * math.cos(math.tau * i / n),
                                                         r * math.sin(math.tau * i / n), z))) for i in range(n)])
        for a, b in zip(anillos[:-1], anillos[1:]):
            if len(a) == 1 and len(b) == 1:
                continue
            for i in range(n):
                j = (i + 1) % n
                if len(a) == 1:
                    bm.faces.new((a[0], b[j], b[i]))
                elif len(b) == 1:
                    bm.faces.new((a[i], a[j], b[0]))
                else:
                    bm.faces.new((a[i], a[j], b[j], b[i]))
        if len(anillos[0]) > 1:
            bm.faces.new(list(reversed(anillos[0])))
        if len(anillos[-1]) > 1:
            bm.faces.new(anillos[-1])
        return self._fin([v for a in anillos for v in a], mat, sim)

    def superficie(self, filas, grosor, mat, sim=False, cerrar_u=False):
        """Membrana con grosor a partir de una rejilla de puntos (filas x columnas): alas, pétalos, banderas."""
        G = np.array(filas, float)
        nr, nc = G.shape[:2]
        du = np.gradient(G, axis=0)
        dv = np.gradient(G, axis=1)
        N = np.cross(du, dv)
        L = np.linalg.norm(N, axis=2, keepdims=True)
        N = N / np.where(L < 1e-9, 1, L)
        gr = np.asarray(grosor, float)
        if gr.ndim == 0:
            gr = np.full((nr, nc), float(gr))
        bm = self.bm
        top = [[bm.verts.new(G[i, j] + N[i, j] * gr[i, j] / 2) for j in range(nc)] for i in range(nr)]
        bot = [[bm.verts.new(G[i, j] - N[i, j] * gr[i, j] / 2) for j in range(nc)] for i in range(nr)]
        ri = nr if cerrar_u else nr - 1
        for i in range(ri):
            i2 = (i + 1) % nr
            for j in range(nc - 1):
                bm.faces.new((top[i][j], top[i2][j], top[i2][j + 1], top[i][j + 1]))
                bm.faces.new((bot[i][j], bot[i][j + 1], bot[i2][j + 1], bot[i2][j]))
        for i in range(ri):
            i2 = (i + 1) % nr
            bm.faces.new((top[i][0], bot[i][0], bot[i2][0], top[i2][0]))
            bm.faces.new((top[i][-1], top[i2][-1], bot[i2][-1], bot[i][-1]))
        if not cerrar_u:
            for j in range(nc - 1):
                bm.faces.new((top[0][j], top[0][j + 1], bot[0][j + 1], bot[0][j]))
                bm.faces.new((top[-1][j], bot[-1][j], bot[-1][j + 1], top[-1][j + 1]))
        return self._fin([v for f in top + bot for v in f], mat, sim)

    def lamina(self, contorno, grosor, mat, sim=False, bombeo=0.0):
        """Placa con grosor a partir de un contorno 3D (abanico desde el centro, con `bombeo` hacia la normal)."""
        C = np.array(contorno, float)
        cen = C.mean(0)
        nrm = np.zeros(3)
        for i in range(len(C)):
            a, b = C[i] - cen, C[(i + 1) % len(C)] - cen
            nrm += np.cross(a, b)
        nrm /= np.linalg.norm(nrm)
        bm = self.bm
        top = [bm.verts.new(p + nrm * grosor / 2) for p in C]
        bot = [bm.verts.new(p - nrm * grosor / 2) for p in C]
        ct = bm.verts.new(cen + nrm * (grosor / 2 + bombeo))
        cb = bm.verts.new(cen - nrm * (grosor / 2 - bombeo * 0.6))
        n = len(C)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((ct, top[i], top[j]))
            bm.faces.new((cb, bot[j], bot[i]))
            bm.faces.new((top[i], bot[i], bot[j], top[j]))
        return self._fin(top + bot + [ct, cb], mat, sim)


# ----------------------------------------------------------------------------------------------------------
# Pieza: orgánico + duro
# ----------------------------------------------------------------------------------------------------------


class Pieza:
    def __init__(self, modelo, nombre, tris, res=150, k=0.0, ruido=None, suelo=None, techo=None, roblox=None,
                 angulo=None, unir=None, planos=()):
        self.planos = planos
        self.unir = unir  # nombre de otra pieza: se modela aparte (con su propia resolución) y acaba en su malla
        self.modelo = modelo
        self.nombre = nombre
        self.tris = tris
        self.res = res
        self.k = k
        self.ruido = ruido
        self.suelo = suelo
        self.techo = techo
        self.roblox = roblox
        self.angulo = angulo
        self.org = Organico()
        self.duro = Duro()
        self.marco = None
        self._masc = False

    def mascara(self):
        """Contexto: lo que se cree dentro es máscara. La pieza queda recortada a donde hay máscara: sirve para
        dibujar manchas y franjas que siguen la superficie de un cuerpo (cuerpo engordado ∩ dibujo)."""
        pieza = self

        class _Ctx:
            def __enter__(self_):
                pieza._masc = True

            def __exit__(self_, *a):
                pieza._masc = False

        return _Ctx()

    def en(self, pos=(0, 0, 0), rot=None, esc=None, eje=None):
        """Contexto: lo que se cree dentro se modela en local y se coloca con esta transformación.
        (Con tubos y cilindros la escala tiene que ser uniforme.)"""
        pieza = self

        class _Ctx:
            def __enter__(self_):
                self_.antes = pieza.marco
                m = _T(pos, rot, esc, eje)
                pieza.marco = m if pieza.marco is None else pieza.marco @ m
                pieza.duro.marco = pieza.marco

            def __exit__(self_, *a):
                pieza.marco = self_.antes
                pieza.duro.marco = self_.antes

        return _Ctx()

    def _pts(self, pts, R=None):
        """Puntos (y radios) locales -> mundo según el marco actual."""
        if self.marco is None:
            return pts, R
        s = self.marco.to_scale()
        k = (abs(s.x) + abs(s.y) + abs(s.z)) / 3
        pts = [np.array(self.marco @ Vector(p)) for p in pts]
        return pts, (None if R is None else [r * k for r in R])

    def _add(self, hacer, sim, kw):
        k = kw.get("k", self.k)
        for espejo in ((False, True) if sim else (False,)):
            fn, mn, mx, T, partes = hacer(espejo)
            if self.marco is not None and partes is None and T is not None:
                T = self.marco @ T
            destino = self.org.masc if self._masc else self.org.prims
            destino.append(Prim(fn, mn, mx, kw["mat"], T, k, kw.get("resta", False), kw.get("cascara"), partes,
                                kw.get("infla", 0.0)))
            continue
            self.org.prims.append(Prim(fn, mn, mx, kw["mat"], T, k, kw.get("resta", False), kw.get("cascara"),
                                       partes))

    def esfera(self, c, r, mat, esc=None, rot=None, eje=None, sim=False, **kw):
        """Esfera o elipsoide (con `esc`)."""
        kw["mat"] = mat

        def hacer(espejo):
            return (lambda P: np.linalg.norm(P, axis=1) - r), (-r,) * 3, (r,) * 3, _T(c, rot, esc, eje, espejo), None

        self._add(hacer, sim, kw)

    def tubo(self, pts, radios, mat, suave=0, sim=False, **kw):
        """Cadena de conos redondeados por una polilínea (tentáculos, ramas, cuerpos, huesos largos)."""
        kw["mat"] = mat
        if suave:
            pts = curva(pts, suave)
        P0 = [np.asarray(p, float) for p in pts]
        R = radios_de(radios, len(P0))

        def hacer(espejo):
            P = [p * np.array([-1, 1, 1]) for p in P0] if espejo else P0
            P, Rm = self._pts(P, R)
            partes = []
            for a, b, r1, r2 in zip(P[:-1], P[1:], Rm[:-1], Rm[1:]):
                rm = max(r1, r2)
                partes.append((np.minimum(a, b) - rm, np.maximum(a, b) + rm,
                               (lambda Q, a=a, b=b, r1=r1, r2=r2: _d_conoredondo(Q, a, b, r1, r2))))
            mn = np.min([p[0] for p in partes], axis=0)
            mx = np.max([p[1] for p in partes], axis=0)
            return None, mn, mx, None, partes

        self._add(hacer, sim, kw)

    def capsula(self, a, b, r1, mat, r2=None, sim=False, **kw):
        self.tubo([a, b], [r1, r1 if r2 is None else r2], mat, sim=sim, **kw)

    def cilindro(self, a, b, r1, mat, r2=None, red=0.0, sim=False, **kw):
        """Cilindro o cono truncado de tapas planas entre dos puntos."""
        kw["mat"] = mat
        a0, b0 = np.asarray(a, float), np.asarray(b, float)
        rb = r1 if r2 is None else r2

        def hacer(espejo):
            a, b = (a0 * [-1, 1, 1], b0 * [-1, 1, 1]) if espejo else (a0, b0)
            (a, b), (q1, q2, qr) = self._pts([a, b], [r1, rb, red])
            rm = max(q1, q2) + qr
            return ((lambda P: _d_conotapado(P, a, b, q1, q2) - qr), np.minimum(a, b) - rm, np.maximum(a, b) + rm,
                    None, [(np.minimum(a, b) - rm, np.maximum(a, b) + rm,
                            (lambda P: _d_conotapado(P, a, b, q1, q2) - qr))])

        self._add(hacer, sim, kw)

    def caja(self, c, tam, mat, red=0.0, rot=None, eje=None, sim=False, **kw):
        kw["mat"] = mat
        b = np.asarray(tam, float) / 2 - red

        def fn(P):
            q = np.abs(P) - b
            return np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(axis=1), 0) - red

        def hacer(espejo):
            return fn, -(b + red), b + red, _T(c, rot, None, eje, espejo), None

        self._add(hacer, sim, kw)

    def toro(self, c, R, r, mat, eje=(0, 0, 1), esc=None, rot=None, sim=False, **kw):
        kw["mat"] = mat

        def fn(P):
            q = np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2) - R
            return np.sqrt(q * q + P[:, 2] ** 2) - r

        def hacer(espejo):
            return fn, (-R - r, -R - r, -r), (R + r, R + r, r), _T(c, rot, esc, eje, espejo), None

        self._add(hacer, sim, kw)

    def torno(self, perfil, c, mat, eje=None, esc=None, rot=None, cerrado=False, sim=False, **kw):
        """Sólido de revolución alrededor del Z local. perfil = [(r, z)...] de abajo arriba (o contorno cerrado)."""
        kw["mat"] = mat
        V = [tuple(p) for p in perfil]
        if not cerrado:
            V = V + [(-r, z) for r, z in reversed(V)]
        V = np.array(V, float)
        rm = float(np.abs(V[:, 0]).max())

        def fn(P):
            return _d_poligono(np.sqrt(P[:, 0] ** 2 + P[:, 1] ** 2), P[:, 2], V)

        def hacer(espejo):
            return fn, (-rm, -rm, V[:, 1].min()), (rm, rm, V[:, 1].max()), _T(c, rot, esc, eje, espejo), None

        self._add(hacer, sim, kw)

    def extrusion(self, poligono, grosor, c, mat, rot=None, eje=None, esc=None, red=0.0, sim=False, **kw):
        """Polígono del plano XY local extruido ±grosor/2 en Z local (losas, hexágonos, placas)."""
        kw["mat"] = mat
        V = np.array(poligono, float)
        g = grosor / 2 - red

        def fn(P):
            d2 = _d_poligono(P[:, 0], P[:, 1], V) + red
            dz = np.abs(P[:, 2]) - g
            return np.minimum(np.maximum(d2, dz), 0) + np.sqrt(np.maximum(d2, 0) ** 2 + np.maximum(dz, 0) ** 2) - red

        def hacer(espejo):
            return (fn, (V[:, 0].min() - red, V[:, 1].min() - red, -grosor / 2),
                    (V[:, 0].max() + red, V[:, 1].max() + red, grosor / 2), _T(c, rot, esc, eje, espejo), None)

        self._add(hacer, sim, kw)


# ----------------------------------------------------------------------------------------------------------
# Materiales procedurales
# ----------------------------------------------------------------------------------------------------------

# a, b: colores que mezcla el ruido. esc: tamaño del ruido. rug: rugosidad. relieve: fuerza del relieve.
# venas / manchas / fibras / escamas: capas opcionales. emis: (color, fuerza) emisión uniforme.
PALETA = {
    "carne": dict(a="#7A1E2E", b="#3A0F24", esc=1.6, rug=0.42, relieve=0.5,
                  venas=dict(color="#2A0A1E", esc=1.3, ancho=0.07, hondo=-0.5)),
    "carne_viva": dict(a="#A62B36", b="#5E1428", esc=2.0, rug=0.33, relieve=0.5,
                       venas=dict(color="#3D0B2A", esc=1.6, ancho=0.06, hondo=0.5)),
    "carne_palida": dict(a="#B98A8C", b="#7A4A5E", esc=1.8, rug=0.45, relieve=0.4,
                         venas=dict(color="#5A1E4A", esc=1.5, ancho=0.05, hondo=0.4)),
    "musculo": dict(a="#8B2B36", b="#4A1226", esc=1.5, rug=0.4, relieve=0.7, fibras=dict(esc=3.0, fuerza=0.9)),
    "tendon": dict(a="#C9B49A", b="#8E6A62", esc=2.0, rug=0.45, relieve=0.6, fibras=dict(esc=4.0, fuerza=0.8)),
    "membrana": dict(a="#5B2A5E", b="#2E1238", esc=1.4, rug=0.4, relieve=0.3,
                     venas=dict(color="#9A2F52", esc=2.2, ancho=0.05, hondo=0.6)),
    "piel": dict(a="#3A2338", b="#1E1224", esc=1.2, rug=0.72, relieve=0.6, escamas=dict(esc=5.0, fuerza=0.35)),
    "piel_purpura": dict(a="#4A2468", b="#22102E", esc=1.0, rug=0.55, relieve=0.5,
                         escamas=dict(esc=6.0, fuerza=0.25)),
    "piel_gris": dict(a="#4E4658", b="#2C2438", esc=0.8, rug=0.6, relieve=0.5, escamas=dict(esc=4.0, fuerza=0.3)),
    "quitina": dict(a="#1A1022", b="#34194A", esc=0.9, rug=0.26, metal=0.2, relieve=0.35,
                    escamas=dict(esc=1.6, fuerza=0.25)),
    "quitina_negra": dict(a="#0C0A10", b="#1C1426", esc=0.9, rug=0.2, metal=0.3, relieve=0.3,
                          escamas=dict(esc=1.4, fuerza=0.2)),
    "escamas": dict(a="#4B1F7A", b="#1B5A40", esc=0.7, rug=0.3, metal=0.35, relieve=0.5,
                    escamas=dict(esc=4.5, fuerza=0.8)),
    "hueso": dict(a="#D8CDB0", b="#A89878", esc=1.8, rug=0.62, relieve=0.35,
                  venas=dict(color="#4A3F30", esc=1.4, ancho=0.025, hondo=-0.8)),
    "hueso_viejo": dict(a="#9C8F78", b="#62574A", esc=1.8, rug=0.75, relieve=0.5,
                        venas=dict(color="#2E261E", esc=1.6, ancho=0.03, hondo=-0.8)),
    "diente": dict(a="#E8E0C8", b="#C4B288", esc=2.5, rug=0.3, relieve=0.15),
    "garra": dict(a="#1A141C", b="#3A2E36", esc=2.5, rug=0.25, relieve=0.15, fibras=dict(esc=5.0, fuerza=0.4)),
    "piedra": dict(a="#1E1A26", b="#322A3C", esc=1.1, rug=0.88, relieve=0.9,
                   venas=dict(color="#0C0A10", esc=0.9, ancho=0.03, hondo=-1.0)),
    "piedra_venas": dict(a="#1A1622", b="#2C2436", esc=1.1, rug=0.85, relieve=0.8,
                         venas=dict(color=VIOLETA, esc=0.7, ancho=0.035, hondo=-0.6, emis=1.0)),
    "obsidiana": dict(a="#0B0910", b="#22163A", esc=0.8, rug=0.16, metal=0.1, relieve=0.25),
    "cristal": dict(a="#3A1466", b="#8A3AD0", esc=1.5, rug=0.12, relieve=0.1, emis=(VIOLETA, 0.55)),
    "cristal_oscuro": dict(a="#150A24", b="#3A1466", esc=1.5, rug=0.1, metal=0.1, relieve=0.15,
                           venas=dict(color=VIOLETA, esc=1.2, ancho=0.04, hondo=0.0, emis=1.0)),
    "neon_violeta": dict(a="#7A2AB0", b="#C04DFF", esc=3.0, rug=0.3, relieve=0.0, emis=(VIOLETA, 1.0)),
    "neon_verde": dict(a="#1E9A0A", b="#39FF14", esc=3.0, rug=0.3, relieve=0.0, emis=(VERDE, 1.0)),
    "neon_rojo": dict(a="#A01010", b="#FF2A2A", esc=3.0, rug=0.3, relieve=0.0, emis=(ROJO, 1.0)),
    "neon_amarillo": dict(a="#B08A00", b="#FFD21F", esc=3.0, rug=0.3, relieve=0.0, emis=(AMARILLO, 1.0)),
    "acido": dict(a="#39FF14", b="#128A10", esc=1.6, rug=0.1, relieve=0.25, emis=(VERDE, 0.8),
                  manchas=dict(color="#D8FFB0", esc=2.5, radio=0.22)),
    "lava_purpura": dict(a="#C04DFF", b="#5A148A", esc=1.4, rug=0.2, relieve=0.4, emis=(VIOLETA, 0.9),
                         venas=dict(color="#1A0A24", esc=1.2, ancho=0.08, hondo=0.6)),
    "sangre": dict(a="#6A0A14", b="#2A0408", esc=1.2, rug=0.07, relieve=0.12),
    "sangre_neon": dict(a="#B01A3A", b="#5A0A2A", esc=1.4, rug=0.1, relieve=0.15, emis=("#FF2A4A", 0.6)),
    "liquido_violeta": dict(a="#C04DFF", b="#6A1EB0", esc=1.5, rug=0.08, relieve=0.2, emis=(VIOLETA, 0.85)),
    "hongo_tallo": dict(a="#CFC3B8", b="#8E7A8A", esc=2.0, rug=0.6, relieve=0.5, fibras=dict(esc=4.0, fuerza=0.6)),
    "hongo_sombrero": dict(a="#6A2590", b="#2E0F45", esc=1.2, rug=0.4, relieve=0.3,
                           manchas=dict(color=VERDE, esc=2.4, radio=0.2, emis=1.0)),
    "hongo_laminas": dict(a="#B49AC0", b="#5A3A6A", esc=2.0, rug=0.6, relieve=0.8, fibras=dict(esc=7.0, fuerza=1.0)),
    "hongo_verde": dict(a="#4FA81E", b="#1E4A12", esc=1.6, rug=0.45, relieve=0.4,
                        manchas=dict(color="#C8FF6A", esc=3.0, radio=0.18, emis=0.6)),
    "seda": dict(a="#D2CBDA", b="#8C849E", esc=2.0, rug=0.5, relieve=0.8, fibras=dict(esc=6.0, fuerza=1.0)),
    "resina": dict(a="#8A35C8", b="#3A1260", esc=1.5, rug=0.12, relieve=0.2, emis=(VIOLETA, 0.35)),
    "mucosa": dict(a="#5FB81E", b="#1E5A12", esc=1.6, rug=0.1, relieve=0.3, emis=(VERDE, 0.25)),
    "corteza": dict(a="#17111C", b="#2E1C36", esc=1.4, rug=0.85, relieve=1.0, fibras=dict(esc=3.0, fuerza=1.0)),
    "raiz": dict(a="#3A1830", b="#1C0E1E", esc=1.4, rug=0.7, relieve=0.8, fibras=dict(esc=3.5, fuerza=0.8),
                 venas=dict(color="#7A1E3A", esc=1.4, ancho=0.04, hondo=0.4)),
    "musgo": dict(a="#1E5A1A", b="#0C2A12", esc=3.0, rug=0.9, relieve=1.0,
                  manchas=dict(color=VERDE, esc=4.0, radio=0.25, emis=0.7)),
    "tierra": dict(a="#1C141A", b="#2C1E26", esc=1.5, rug=0.92, relieve=0.8),
    "paja": dict(a="#6A5A3A", b="#3A2E22", esc=2.5, rug=0.85, relieve=1.0, fibras=dict(esc=6.0, fuerza=1.0)),
    "ojo": dict(a="#D8CFC0", b="#B89A98", esc=2.0, rug=0.15, relieve=0.1,
                venas=dict(color="#8A1A22", esc=2.5, ancho=0.03, hondo=0.0)),
    "pupila": dict(a="#050308", b="#0C0812", esc=2.0, rug=0.08, relieve=0.0),
    "negro": dict(a="#07060A", b="#120E18", esc=2.0, rug=0.6, relieve=0.2),
    "cuero": dict(a="#4A2E2A", b="#2A1A1C", esc=1.6, rug=0.7, relieve=0.6,
                  venas=dict(color="#1A1012", esc=2.0, ancho=0.03, hondo=-0.6)),
    "pintura_sangre": dict(a="#8A0F18", b="#4A060C", esc=2.5, rug=0.5, relieve=0.2),
    "fuego_verde": dict(a="#39FF14", b="#D8FF8A", esc=2.0, rug=0.4, relieve=0.0, emis=(VERDE, 1.0)),
    "fuego_violeta": dict(a="#C04DFF", b="#F0C0FF", esc=2.0, rug=0.4, relieve=0.0, emis=(VIOLETA, 1.0)),
}


def _crear_material(nombre, sp, kt):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes, nt.links
    salida = N.new("ShaderNodeOutputMaterial")
    bsdf = N.new("ShaderNodeBsdfPrincipled")
    L.new(bsdf.outputs[0], salida.inputs["Surface"])
    geo = N.new("ShaderNodeNewGeometry")
    pos = geo.outputs["Position"]

    def valor(x):
        n = N.new("ShaderNodeValue")
        n.outputs[0].default_value = x
        return n.outputs[0]

    def mate(op, a, b=None, c=None, clamp=False):
        n = N.new("ShaderNodeMath")
        n.operation = op
        n.use_clamp = clamp
        for i, x in enumerate((a, b, c)):
            if x is None:
                continue
            if isinstance(x, (int, float)):
                n.inputs[i].default_value = x
            else:
                L.new(x, n.inputs[i])
        return n.outputs[0]

    def suave(x, a, b, sal0=0.0, sal1=1.0):
        n = N.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        L.new(x, n.inputs[0])
        n.inputs[1].default_value, n.inputs[2].default_value = a, b
        n.inputs[3].default_value, n.inputs[4].default_value = sal0, sal1
        return n.outputs[0]

    def mezcla(fac, c1, c2):
        n = N.new("ShaderNodeMix")
        n.data_type = "RGBA"
        if isinstance(fac, (int, float)):
            n.inputs[0].default_value = fac
        else:
            L.new(fac, n.inputs[0])
        for i, c in ((6, c1), (7, c2)):
            if isinstance(c, tuple):
                n.inputs[i].default_value = (*c, 1.0)
            else:
                L.new(c, n.inputs[i])
        return n.outputs[2]

    def ruido(esc, detalle=4.0, vec=None, salida_color=False):
        n = N.new("ShaderNodeTexNoise")
        L.new(vec or pos, n.inputs["Vector"])
        n.inputs["Scale"].default_value = esc * kt
        n.inputs["Detail"].default_value = detalle
        return n.outputs[1] if salida_color else n.outputs[0]

    def voronoi(esc, rasgo, vec=None):
        n = N.new("ShaderNodeTexVoronoi")
        n.feature = rasgo
        L.new(vec or pos, n.inputs["Vector"])
        n.inputs["Scale"].default_value = esc * kt
        return n.outputs["Distance"]

    def vec_mate(op, a, b=None, escala=None):
        n = N.new("ShaderNodeVectorMath")
        n.operation = op
        L.new(a, n.inputs[0])
        if b is not None:
            if isinstance(b, tuple):
                n.inputs[1].default_value = b
            else:
                L.new(b, n.inputs[1])
        if escala is not None:
            n.inputs["Scale"].default_value = escala
        return n.outputs[0]

    n1 = ruido(sp.get("esc", 1.5))
    n2 = ruido(sp.get("esc", 1.5) * 0.35, 2.0)
    fac = suave(n1, 0.3, 0.7)
    color = mezcla(fac, srgb(sp["a"]), srgb(sp["b"]))
    color = mezcla(suave(n2, 0.35, 0.75, 0.0, 0.35), color, tuple(x * 0.35 for x in srgb(sp["b"])))
    altura = mate("MULTIPLY", n1, 0.6)
    fino = ruido(sp.get("esc", 1.5) * 6.0, 3.0)
    altura = mate("ADD", altura, mate("MULTIPLY", fino, 0.25))
    emis_color = None
    emis_fac = None

    if "fibras" in sp:
        f = sp["fibras"]
        estirado = vec_mate("MULTIPLY", pos, (1.0, 1.0, 0.08))
        nf = ruido(f["esc"], 3.0, vec=estirado)
        altura = mate("ADD", altura, mate("MULTIPLY", nf, f["fuerza"]))
        color = mezcla(suave(nf, 0.35, 0.65, 0.45, 0.0), color, tuple(x * 0.3 for x in srgb(sp["b"])))

    if "escamas" in sp:
        e = sp["escamas"]
        d = voronoi(e["esc"], "F1")
        altura = mate("ADD", altura, mate("MULTIPLY", mate("SUBTRACT", 0.7, d), e["fuerza"] * 1.6))
        color = mezcla(suave(d, 0.3, 0.6, 0.0, 0.55), color, tuple(x * 0.4 for x in srgb(sp["b"])))

    if "venas" in sp:
        v = sp["venas"]
        deform = vec_mate("ADD", pos, vec_mate("SCALE", ruido(v["esc"] * 1.3, 2.0, salida_color=True),
                                               escala=0.45 / (v["esc"] * kt)))
        d = voronoi(v["esc"], "DISTANCE_TO_EDGE", vec=deform)
        masc = suave(d, 0.0, v["ancho"], 1.0, 0.0)
        color = mezcla(masc, color, srgb(v["color"]))
        if v.get("hondo"):
            altura = mate("ADD", altura, mate("MULTIPLY", masc, v["hondo"]))
        if v.get("emis"):
            emis_color = mezcla(masc, (0, 0, 0), tuple(x * v["emis"] for x in srgb(v["color"])))

    if "manchas" in sp:
        m = sp["manchas"]
        d = voronoi(m["esc"], "F1")
        masc = suave(d, m["radio"] * 0.6, m["radio"], 1.0, 0.0)
        color = mezcla(masc, color, srgb(m["color"]))
        altura = mate("ADD", altura, mate("MULTIPLY", masc, 0.5))
        if m.get("emis"):
            e2 = mezcla(masc, (0, 0, 0), tuple(x * m["emis"] for x in srgb(m["color"])))
            emis_color = e2 if emis_color is None else mezcla(masc, emis_color, e2)

    L.new(color, bsdf.inputs["Base Color"])
    rug = mate("ADD", sp.get("rug", 0.6), mate("MULTIPLY", mate("SUBTRACT", n1, 0.5), sp.get("rug_var", 0.25)),
               clamp=True)
    L.new(rug, bsdf.inputs["Roughness"])
    bsdf.inputs["Metallic"].default_value = 0.0  # el metal se hornea aparte (si no, el color difuso sale negro)
    if sp.get("relieve", 0) > 0:
        bump = N.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = min(1.0, sp["relieve"])
        bump.inputs["Distance"].default_value = 0.05 / kt * max(1.0, sp["relieve"])
        L.new(altura, bump.inputs["Height"])
        L.new(bump.outputs[0], bsdf.inputs["Normal"])
    if "emis" in sp:
        ec, ef = sp["emis"]
        base = tuple(x * ef for x in srgb(ec))
        # La emisión uniforme sigue un poco el dibujo del color, para que no sea una mancha plana.
        e3 = mezcla(suave(n1, 0.2, 0.8, 0.0, 0.45), base, tuple(x * 0.45 for x in base))
        emis_color = e3 if emis_color is None else mezcla(0.5, emis_color, e3)
    if emis_color is not None:
        L.new(emis_color, bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = 1.0
    mat["metal"] = float(sp.get("metal", 0.0))
    mat["brilla"] = emis_color is not None
    return mat


def _material_plano(nombre, v):
    """Material que emite un gris constante (para hornear el metal)."""
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    o = nt.nodes.new("ShaderNodeOutputMaterial")
    e = nt.nodes.new("ShaderNodeEmission")
    e.inputs["Color"].default_value = (v, v, v, 1)
    nt.links.new(e.outputs[0], o.inputs["Surface"])
    return m


# ----------------------------------------------------------------------------------------------------------
# Utilidades de Blender
# ----------------------------------------------------------------------------------------------------------


def _malla_np(nombre, verts, caras, mat_c=None):
    me = bpy.data.meshes.new(nombre)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    me.loops.add(len(caras) * 3)
    me.loops.foreach_set("vertex_index", caras.ravel())
    me.polygons.add(len(caras))
    me.polygons.foreach_set("loop_start", np.arange(0, len(caras) * 3, 3, dtype=np.int32))
    me.polygons.foreach_set("loop_total", np.full(len(caras), 3, dtype=np.int32))
    if mat_c is not None:
        me.polygons.foreach_set("material_index", mat_c.astype(np.int32))
    me.polygons.foreach_set("use_smooth", np.ones(len(caras), bool))
    me.update(calc_edges=True)
    me.validate()
    obj = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _limpiar(obj):
    """Quita triángulos degenerados y vértices sueltos (el importador de FBX los descarta y descuadra la cuenta)."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
    sueltos = [v for v in bm.verts if not v.link_faces]
    if sueltos:
        bmesh.ops.delete(bm, geom=sueltos, context="VERTS")
    bm.to_mesh(obj.data)
    bm.free()


def _activar(obj, otros=()):
    bpy.ops.object.select_all(action="DESELECT")
    for o in otros:
        o.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _tris(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def _attr_pieza(obj, i):
    a = obj.data.attributes.get("pieza") or obj.data.attributes.new("pieza", "INT", "FACE")
    a.data.foreach_set("value", np.full(len(obj.data.polygons), i, np.int32))


def _unir(objs, nombre):
    _activar(objs[0], objs[1:])
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    o.name = nombre
    return o


def _copia_filtrada(obj, nombre, attr, valor):
    """Copia de `obj` solo con las caras cuyo atributo entero `attr` vale `valor`."""
    nuevo = obj.copy()
    nuevo.data = obj.data.copy()
    nuevo.name = nuevo.data.name = nombre
    bpy.context.scene.collection.objects.link(nuevo)
    bm = bmesh.new()
    bm.from_mesh(nuevo.data)
    capa = bm.faces.layers.int.get(attr)
    fuera = [f for f in bm.faces if f[capa] != valor]
    bmesh.ops.delete(bm, geom=fuera, context="FACES")
    bm.to_mesh(nuevo.data)
    bm.free()
    return nuevo


def _volumen(me):
    n = len(me.vertices)
    co = np.empty(n * 3, np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(-1, 3).astype(np.float64)
    me.calc_loop_triangles()
    t = np.empty(len(me.loop_triangles) * 3, np.int32)
    me.loop_triangles.foreach_get("vertices", t)
    t = t.reshape(-1, 3)
    cen = co.mean(0)
    a, b, c = co[t[:, 0]] - cen, co[t[:, 1]] - cen, co[t[:, 2]] - cen
    return float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6)


def _fuente(tam, negrita=True):
    ruta = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if negrita else \
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    return ImageFont.truetype(ruta, tam) if os.path.exists(ruta) else ImageFont.load_default(tam)


# ----------------------------------------------------------------------------------------------------------
# Modelo
# ----------------------------------------------------------------------------------------------------------

PRESUPUESTOS = dict(grande=15000, mediana=8000, prop=2000, vegetacion=4000, bestia=20000, bestia_menor=8000)


class Modelo:
    def __init__(self, nombre, zona, clase, tam, descripcion="", tex=None, ancla="suelo", ajustar=True):
        self.nombre = nombre
        self.zona = zona
        self.clase = clase
        self.presupuesto = PRESUPUESTOS[clase]
        self.tam = tam
        self.descripcion = descripcion
        self.tex = tex  # multiplicador de la escala de las texturas procedurales
        self.ancla = ancla
        self.ajustar = ajustar
        self.piezas = []
        self.paleta = {}
        self.rnd = random.Random(zlib.crc32(nombre.encode()))
        self.articulaciones = []
        self.monturas = []
        self.carga = None
        self.raiz = None
        self.avisos = []
        self.notas = {}

    # ---- declaración ----------------------------------------------------------------------------------

    def pieza(self, nombre, tris=1500, **kw):
        p = Pieza(self, nombre, tris, **kw)
        self.piezas.append(p)
        return p

    def mat(self, nombre, base, **cambios):
        """Variante de un material de la paleta solo para este modelo."""
        sp = dict(PALETA[base])
        sp.update(cambios)
        self.paleta[nombre] = sp
        return nombre

    def articulacion(self, pieza, padre, pivote):
        self.articulaciones.append((pieza, padre, tuple(pivote)))

    def montura(self, pos, nombre=None, mirando=(0, -1, 0)):
        self.monturas.append(dict(nombre=nombre or f"asiento_{len(self.monturas) + 1}", pos=tuple(pos),
                                  mirando=tuple(mirando)))

    def bahia(self, pos, tam, nota=""):
        self.carga = dict(pos=tuple(pos), tam=tuple(tam), nota=nota)

    def aviso(self, txt):
        log("AVISO:", txt)
        self.avisos.append(txt)

    # ---- construcción ---------------------------------------------------------------------------------

    def construir(self, carpeta, rapido=False):
        t0 = time.time()
        os.makedirs(carpeta, exist_ok=True)
        scn = bpy.context.scene
        scn.unit_settings.system = "NONE"
        scn.world = bpy.data.worlds.new("mundo")
        scn.render.engine = "CYCLES"
        scn.cycles.device = "CPU"
        scn.render.threads_mode = "FIXED"
        scn.render.threads = int(os.environ.get("PM_HILOS", "2"))
        nombre = self.nombre

        # 1) Mallas altas (orgánico) y bmesh duro de cada pieza.
        altas = []
        for i, p in enumerate(self.piezas):
            if p.org.vacio():
                altas.append(None)
                continue
            res = p.res * (0.6 if rapido else 1.0)
            try:
                altas.append(p.org.malla(res, p.ruido, p.suelo, p.techo, semilla=self.rnd.uniform(0, 40),
                                         planos=p.planos))
            except RuntimeError as e:
                self.aviso(f"{p.nombre}: {e}")
                altas.append(None)
        log(f"campos listos {time.time() - t0:.1f}s")

        # 2) Ajuste al tamaño pedido (escala por eje) y anclaje al origen.
        todos = [a[0] for a in altas if a is not None]
        for p in self.piezas:
            if not p.duro.vacio():
                todos.append(np.array([v.co[:] for v in p.duro.bm.verts]))
        P = np.concatenate(todos)
        mn, mx = P.min(0), P.max(0)
        tam = mx - mn
        if self.ajustar:
            S = np.array(self.tam, float) / tam
            if S.min() < 0.7 or S.max() > 1.45:
                self.aviso(f"ajuste de escala grande {np.round(S, 2).tolist()} (modelado {np.round(tam, 2).tolist()})")
        else:
            S = np.ones(3)
        cen = (mn + mx) / 2
        if self.ancla == "suelo":
            ori = np.array([cen[0], cen[1], mn[2]])
        elif self.ancla == "techo":  # cosas que cuelgan: el origen arriba
            ori = np.array([cen[0], cen[1], mx[2]])
        else:
            ori = cen

        def fijar(q):
            return (np.asarray(q, float) - ori) * S

        self._fijar = fijar
        dims = tam * S
        self.dims = dims
        diag = float(np.linalg.norm(dims))
        kt = self.tex or float(np.clip((9.0 / dims.max()) ** 0.75, 0.3, 14.0))

        # 3) Materiales.
        mats, planos = {}, {}

        def material(n):
            if n not in mats:
                sp = self.paleta.get(n) or PALETA[n]
                mats[n] = _crear_material(n, sp, kt)
                planos[n] = _material_plano(n + "_metal", sp.get("metal", 0.0))
            return mats[n]

        destino = bpy.data.materials.new("destino")
        destino.use_nodes = True
        nodo_img = destino.node_tree.nodes.new("ShaderNodeTexImage")
        destino.node_tree.nodes.active = nodo_img

        # 4) Objetos: alta y baja orgánicas por pieza, y duro por pieza.
        objs_alta, objs_baja, objs_duro = [], [], []
        tris_duro = 0
        info_piezas = []
        for i, p in enumerate(self.piezas):
            if not p.duro.vacio():
                bm = p.duro.bm
                for v in bm.verts:
                    v.co = Vector(fijar(v.co))
                bmesh.ops.triangulate(bm, faces=bm.faces[:])
                bmesh.ops.dissolve_degenerate(bm, dist=1e-5, edges=bm.edges[:])
                bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
                log(f"  {p.nombre}: duro {len(bm.faces)}")
                tris_duro += len(bm.faces)
        tris_org = sum(p.tris for p, a in zip(self.piezas, altas) if a is not None)
        libre = self.presupuesto * 0.985 - tris_duro
        factor = min(1.0, libre / tris_org) if tris_org else 1.0
        if tris_duro > self.presupuesto:
            self.aviso(f"la geometría dura sola ya pasa del presupuesto: {tris_duro}")
        h_max = 0.0
        nombres_p = [p.nombre for p in self.piezas]
        indice = [nombres_p.index(p.unir) if p.unir else i for i, p in enumerate(self.piezas)]
        for i, p in enumerate(self.piezas):
            if altas[i] is not None:
                verts, caras, mat_c, nombres, h = altas[i]
                h_max = max(h_max, h * float(S.max()))
                alta = _malla_np(f"alta_{p.nombre}", fijar(verts), caras, mat_c)
                bm_ = bmesh.new()  # suelda los vértices casi coincidentes que deja el marching cubes
                bm_.from_mesh(alta.data)
                bmesh.ops.remove_doubles(bm_, verts=bm_.verts[:], dist=h * 0.08)
                bm_.to_mesh(alta.data)
                bm_.free()
                caras = np.zeros((len(alta.data.polygons), 3))
                for n in nombres:
                    alta.data.materials.append(material(n))
                objs_alta.append(alta)
                baja = alta.copy()
                baja.data = alta.data.copy()
                bpy.context.scene.collection.objects.link(baja)
                objetivo = max(40, int(p.tris * factor))
                actual = len(caras)
                if actual > objetivo:
                    mod = baja.modifiers.new("dec", "DECIMATE")
                    mod.ratio = objetivo / actual
                    _activar(baja)
                    bpy.ops.object.modifier_apply(modifier=mod.name)
                baja.data.materials.clear()
                _limpiar(baja)
                log(f"  {p.nombre}: alta {actual} -> baja {_tris(baja)} (objetivo {objetivo})")
                _attr_pieza(baja, indice[i])
                objs_baja.append(baja)
            if not p.duro.vacio():
                me = bpy.data.meshes.new(f"duro_{p.nombre}")
                p.duro.bm.to_mesh(me)
                p.duro.bm.free()
                d = bpy.data.objects.new(f"duro_{p.nombre}", me)
                bpy.context.scene.collection.objects.link(d)
                for n in p.duro.mats:
                    me.materials.append(material(n))
                _attr_pieza(d, indice[i])
                _activar(d)
                bpy.ops.object.shade_smooth_by_angle(angle=math.radians(p.angulo or 42))
                objs_duro.append(d)
        log(f"mallas listas {time.time() - t0:.1f}s  (duro {tris_duro} tris)")

        baja = _unir(objs_baja, "baja_org") if objs_baja else None
        duro = _unir(objs_duro, "duro") if objs_duro else None
        if baja:
            baja.data.materials.clear()
            baja.data.materials.append(destino)
            for pol in baja.data.polygons:
                pol.material_index = 0

        # 5) UV conjunto: todas las piezas comparten atlas.
        if duro:
            # Copia del duro que hace de «alta» (con sus materiales procedurales); el duro final recibe el atlas.
            duro_alta = duro.copy()
            duro_alta.data = duro.data.copy()
            duro_alta.name = "duro_alta"
            bpy.context.scene.collection.objects.link(duro_alta)
            objs_alta.append(duro_alta)
        a_uv = [o for o in (baja, duro) if o]
        _activar(a_uv[0], a_uv[1:])
        bpy.ops.object.mode_set(mode="EDIT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=math.radians(70), island_margin=0.0035, area_weight=0.0,
                                 scale_to_bounds=False)
        bpy.ops.uv.pack_islands(margin=0.0035, rotate=True)
        bpy.ops.object.mode_set(mode="OBJECT")
        log(f"UV listo {time.time() - t0:.1f}s")

        # 6) Horneado.
        tam_img = 256 if rapido else TAM_ATLAS
        ext = max(2.2 * h_max, 0.006 * diag)
        capas = {}

        def hornear(tipo, clave, color, muestras=1, **kw):
            img = bpy.data.images.new(f"h_{clave}", tam_img, tam_img, alpha=True, float_buffer=True)
            img.generated_color = (0, 0, 0, 0)
            # Siempre lineal: el horneado escribe en el espacio de la imagen y la conversión a sRGB se hace una sola
            # vez, al guardar (si no, el color y la emisión salen con la gamma aplicada dos veces, lavados).
            img.colorspace_settings.name = "Non-Color"
            scn.cycles.samples = muestras
            scn.render.bake.margin = 0
            if baja:
                nodo_img.image = img
                for o in bpy.data.objects:
                    o.hide_render = o.type == "MESH" and o not in objs_alta
                baja.hide_render = False
                _activar(baja, [o for o in objs_alta if o.name.startswith("alta_")])
                bpy.ops.object.bake(type=tipo, use_selected_to_active=True, cage_extrusion=ext,
                                    max_ray_distance=ext * 2.5, use_clear=False, margin=0, **kw)
            if duro:
                # El duro se hornea sobre sí mismo (sin rayos: no hay artefactos) con los materiales de su copia.
                for o in bpy.data.objects:
                    o.hide_render = o.type == "MESH" and o not in objs_alta and o is not duro
                duro_alta.hide_render = True
                duro.hide_render = False
                for sl in duro.material_slots:
                    nt = sl.material.node_tree
                    n = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
                    n.name = "destino"
                    n.image = img
                    nt.nodes.active = n
                _activar(duro)
                bpy.ops.object.bake(type=tipo, use_selected_to_active=False, use_clear=False, margin=0, **kw)
            px = np.array(img.pixels[:], dtype=np.float32).reshape(tam_img, tam_img, 4)
            capas[clave] = px
            bpy.data.images.remove(img)

        scn.render.bake.use_pass_direct = False
        scn.render.bake.use_pass_indirect = False
        scn.render.bake.use_pass_color = True
        hornear("DIFFUSE", "color", True, pass_filter={"COLOR"})
        hornear("ROUGHNESS", "rug", False)
        hornear("EMIT", "emis", True)
        hornear("NORMAL", "normal", False, normal_space="TANGENT")
        scn.world.light_settings.distance = max(0.08 * diag, 0.05)
        hornear("AO", "ao", False, muestras=6 if rapido else 20)
        # Metal: se cambian los materiales por grises planos y se hornea como emisión.
        for o in objs_alta + ([duro] if duro else []):
            for sl in o.material_slots:
                sl.material = planos[sl.material.name]
        hornear("EMIT", "metal", False)
        for o in objs_alta + ([duro] if duro else []):
            for sl in o.material_slots:
                sl.material = mats[sl.material.name[:-6]]
        log(f"horneado listo {time.time() - t0:.1f}s")

        # 7) Texturas finales: rellenar huecos (cada texel vacío copia el válido más cercano) y guardar.
        valido = capas["normal"][..., 3] > 0.5
        cobertura = float(valido.mean())
        _, (iy, ix) = ndimage.distance_transform_edt(~valido, return_indices=True)

        def rellena(a):
            return a[iy, ix]

        def a_srgb(x):
            x = np.clip(x, 0, 1)
            return np.where(x <= 0.0031308, x * 12.92, 1.055 * np.power(x, 1 / 2.4) - 0.055)

        ao = rellena(capas["ao"][..., 0])
        ao = ndimage.gaussian_filter(ao, 1.2)
        sombra = 1.0 - 0.8 * (1.0 - np.clip(ao, 0, 1)) ** 1.2
        color = rellena(capas["color"][..., :3]) * sombra[..., None]
        emis = rellena(capas["emis"][..., :3])
        normal = rellena(capas["normal"][..., :3])
        rug = rellena(capas["rug"][..., 0])
        metal = rellena(capas["metal"][..., 0])
        brilla = bool(emis.max() > 0.02)

        def guardar(arr, sufijo, modo):
            ruta = os.path.join(carpeta, f"{nombre}_{sufijo}.png")
            a8 = (np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8)[::-1]
            Image.fromarray(a8, modo).save(ruta, optimize=True)
            return ruta

        rutas = dict(color=guardar(a_srgb(color), "color", "RGB"), normal=guardar(normal, "normal", "RGB"),
                     roughness=guardar(rug, "roughness", "L"), metalness=guardar(metal, "metalness", "L"))
        if brilla:
            rutas["emision"] = guardar(a_srgb(emis), "emision", "RGB")

        # 8) Material final con el atlas y piezas definitivas.
        final = bpy.data.materials.new(f"{nombre}_mat")
        final.use_nodes = True
        nt = final.node_tree
        nt.nodes.clear()
        sal = nt.nodes.new("ShaderNodeOutputMaterial")
        b = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(b.outputs[0], sal.inputs["Surface"])

        def tex(clave, color_):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = bpy.data.images.load(rutas[clave])
            n.image.colorspace_settings.name = "sRGB" if color_ else "Non-Color"
            return n

        nt.links.new(tex("color", True).outputs[0], b.inputs["Base Color"])
        nt.links.new(tex("roughness", False).outputs[0], b.inputs["Roughness"])
        nt.links.new(tex("metalness", False).outputs[0], b.inputs["Metallic"])
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tex("normal", False).outputs[0], nm.inputs["Color"])
        nt.links.new(nm.outputs[0], b.inputs["Normal"])
        if brilla:
            nt.links.new(tex("emision", True).outputs[0], b.inputs["Emission Color"])
            b.inputs["Emission Strength"].default_value = 1.3

        for o in objs_alta:
            bpy.data.objects.remove(o)
        for o in a_uv:
            o.data.materials.clear()
            o.data.materials.append(final)
            for pol in o.data.polygons:
                pol.material_index = 0
        todo = _unir(a_uv, "todo")
        finales = []
        for i, p in enumerate(self.piezas):
            if p.unir:
                continue
            o = _copia_filtrada(todo, p.nombre, "pieza", i)
            if len(o.data.polygons) == 0:
                bpy.data.objects.remove(o)
                self.aviso(f"pieza vacía: {p.nombre}")
                continue
            o.data.attributes.remove(o.data.attributes["pieza"])
            o.hide_render = False
            finales.append((p, o))
        bpy.data.objects.remove(todo)
        total = sum(_tris(o) for _, o in finales)
        if total > self.presupuesto:
            self.aviso(f"triángulos {total} > presupuesto {self.presupuesto}")
        log(f"piezas finales: {total} tris, cobertura atlas {cobertura:.2f}  {time.time() - t0:.1f}s")

        # 9) Turnaround.
        objs = [o for _, o in finales]
        self._turnaround(objs, os.path.join(carpeta, f"{nombre}_turnaround.png"), total, dims, rapido)
        log(f"turnaround listo {time.time() - t0:.1f}s")

        # 10) FBX con el giro de importación (180° sobre la vertical) aplicado.
        for o in list(bpy.data.objects):
            if o.type != "MESH" or o not in objs:
                bpy.data.objects.remove(o)
        giro = Matrix.Rotation(math.pi, 4, "Z")
        for o in objs:
            o.data.transform(giro)
            o.data.update()
        ruta_fbx = os.path.join(carpeta, f"{nombre}.fbx")
        _activar(objs[0], objs[1:])
        bpy.ops.export_scene.fbx(filepath=ruta_fbx, use_selection=True, object_types={"MESH"},
                                 apply_unit_scale=True, apply_scale_options="FBX_SCALE_ALL",
                                 bake_space_transform=False, axis_forward="Z", axis_up="Y",
                                 use_mesh_modifiers=True, mesh_smooth_type="OFF", use_tspace=False,
                                 bake_anim=False, embed_textures=False, path_mode="STRIP")

        # Coordenadas de Roblox del archivo exportado: (x, y, z)_roblox = (x, z, -y) del modelado.
        def rbx(q):
            q = fijar(q)
            return [round(float(q[0]), 3), round(float(q[2]), 3), round(float(-q[1]), 3)]

        def rbx_dir(d):
            d = np.asarray(d, float)
            d = d / np.linalg.norm(d)
            return [round(float(d[0]), 3), round(float(d[2]), 3), round(float(-d[1]), 3)]

        piezas_json = []
        centros = {}
        for p, o in finales:
            co = np.array([v.co[:] for v in o.data.vertices])
            mn_, mx_ = co.min(0), co.max(0)
            c_ = (mn_ + mx_) / 2
            t_ = mx_ - mn_
            # tras el giro: blender (x, y, z) -> roblox (-x, z, y)
            centros[p.nombre] = [round(float(-c_[0]), 3), round(float(c_[2]), 3), round(float(c_[1]), 3)]
            d = dict(nombre=p.nombre, triangulos=_tris(o),
                     tamano_studs=[round(float(t_[0]), 2), round(float(t_[2]), 2), round(float(t_[1]), 2)],
                     centro=centros[p.nombre])
            rb = p.roblox
            if rb is None:
                if p.nombre.endswith(("_neon", "_biolum")):
                    rb = dict(material="Neon")
                elif p.nombre.endswith("_cristal"):
                    rb = dict(material="Glass", transparencia=0.35)
            if rb:
                d["roblox"] = rb
            piezas_json.append(d)

        # 11) Verificación: reimportar el FBX en una escena vacía.
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=ruta_fbx)
        ver = dict(piezas=0, triangulos=0, normales_hacia_fuera=True, uv=True, escala_ok=True, nombres_ok=True)
        mn_i, mx_i = np.full(3, 1e9), np.full(3, -1e9)
        esperados = {p.nombre for p, _ in finales}
        vistos = set()
        for o in bpy.context.scene.objects:
            if o.type != "MESH":
                continue
            vistos.add(o.name)
            ver["piezas"] += 1
            ver["triangulos"] += _tris(o)
            if _volumen(o.data) <= 0:
                ver["normales_hacia_fuera"] = False
            if not o.data.uv_layers:
                ver["uv"] = False
            for c in o.bound_box:
                w = np.array(o.matrix_world @ Vector(c))
                mn_i, mx_i = np.minimum(mn_i, w), np.maximum(mx_i, w)
        t_i = mx_i - mn_i
        ver["tamano_reimportado"] = [round(float(x), 2) for x in t_i]
        # Sirve para pillar errores de unidades (3,57 veces más grande, ejes cambiados): se admite lo poco que
        # pierde el decimado en las puntas.
        ver["escala_ok"] = bool(np.all(np.abs(t_i - dims) <= 0.03 * dims.max() + 0.02))
        ver["nombres_ok"] = vistos == esperados
        ver["triangulos_ok"] = abs(ver["triangulos"] - total) <= max(2, total // 1000)
        total = ver["triangulos"]  # lo que de verdad lleva el archivo
        ver["correcto"] = all(ver[k] for k in ("normales_hacia_fuera", "uv", "escala_ok", "nombres_ok",
                                               "triangulos_ok"))
        if not ver["correcto"]:
            self.aviso(f"verificación del FBX con fallos: {ver}")

        # 12) JSON (+ script de montaje en las bestias).
        datos = dict(
            nombre=nombre, zona=self.zona, clase=self.clase, descripcion=self.descripcion,
            triangulos=total, presupuesto_triangulos=self.presupuesto,
            tamano_studs=dict(x=round(float(dims[0]), 2), y=round(float(dims[2]), 2), z=round(float(dims[1]), 2)),
            tamano_pedido=dict(ancho=self.tam[0], fondo=self.tam[1], alto=self.tam[2]),
            origen={"suelo": "centro de la base", "techo": "centro de la parte de arriba (cuelga)",
                    "centro": "centro del modelo"}[self.ancla],
            piezas=piezas_json,
            texturas={k: os.path.basename(v) for k, v in rutas.items()},
            atlas=TAM_ATLAS, escala="1 unidad = 1 stud", giro_importacion="180 grados en Y aplicado",
            ejes="studs, ejes del archivo FBX (Y arriba, el frente mira a +Z: tras el giro de importación de Studio queda mirando a -Z)",
            verificacion_fbx=ver,
        )
        datos.update(self.notas)
        if self.monturas or self.articulaciones:  # bestias y cosas con bisagra
            datos["raiz"] = self.raiz or self.piezas[0].nombre
            datos["articulaciones"] = [dict(pieza=a, padre=b, pivote=rbx(c)) for a, b, c in self.articulaciones]
            datos["puntos_montura"] = [dict(nombre=m["nombre"], posicion=rbx(m["pos"]),
                                            orientacion=rbx_dir(m["mirando"])) for m in self.monturas]
            if self.carga:
                datos["bahia_carga"] = dict(posicion=rbx(self.carga["pos"]),
                                            tamano=[round(abs(float(x)), 2) for x in
                                                    (np.array(self.carga["tam"]) * S)[[0, 2, 1]]],
                                            nota=self.carga["nota"])
            if self.clase.startswith("bestia"):
                _escribir_montar(os.path.join(carpeta, f"montar_{nombre}.luau"), datos, centros)
        if self.avisos:
            datos["avisos"] = self.avisos
        with open(os.path.join(carpeta, f"{nombre}.json"), "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2)
        log(f"== {nombre}: {total} tris, {np.round(dims, 2).tolist()} studs, FBX "
            f"{'OK' if ver['correcto'] else 'CON FALLOS'}, {time.time() - t0:.0f}s")
        return datos

    # ---- turnaround -----------------------------------------------------------------------------------

    def _turnaround(self, objs, ruta, total, dims, rapido):
        scn = bpy.context.scene
        scn.render.engine = "CYCLES"
        scn.cycles.samples = 12 if rapido else 40
        scn.cycles.use_denoising = True
        try:
            scn.view_settings.view_transform = "AgX"
            scn.view_settings.look = "AgX - Medium High Contrast"
        except Exception:
            pass
        lado = 256 if rapido else 512
        scn.render.resolution_x = scn.render.resolution_y = lado
        scn.render.resolution_percentage = 100
        scn.render.image_settings.file_format = "PNG"
        scn.world.use_nodes = True
        fondo = scn.world.node_tree.nodes["Background"]
        fondo.inputs["Color"].default_value = (0.09, 0.09, 0.12, 1)
        fondo.inputs["Strength"].default_value = 0.4

        co = np.concatenate([np.array([v.co[:] for v in o.data.vertices]) for o in objs])
        mn, mx = co.min(0), co.max(0)
        c = Vector((mn + mx) / 2)
        radio = float(np.linalg.norm(mx - mn)) / 2
        mira = bpy.data.objects.new("mira", None)
        scn.collection.objects.link(mira)
        mira.location = c

        def luz(nombre_, energia, pos, color, tam):
            d = bpy.data.lights.new(nombre_, "AREA")
            d.energy = energia * radio * radio
            d.color = color
            d.size = tam * radio
            o = bpy.data.objects.new(nombre_, d)
            o.location = c + Vector(pos) * radio
            scn.collection.objects.link(o)
            k = o.constraints.new("TRACK_TO")
            k.target = mira
            k.track_axis = "TRACK_NEGATIVE_Z"
            k.up_axis = "UP_Y"

        # Estudio de 3 luces: clave cálida, relleno frío y contraluz.
        luz("clave", 170, (-2.2, -2.6, 2.6), (1.0, 0.95, 0.88), 1.6)
        luz("relleno", 50, (2.8, -1.8, 0.9), (0.72, 0.82, 1.0), 2.4)
        luz("contra", 190, (1.2, 3.0, 2.4), (0.85, 0.8, 1.0), 1.4)

        bpy.ops.mesh.primitive_plane_add(size=radio * 60, location=(c.x, c.y, mn[2] - 0.002 * radio))
        suelo = bpy.context.active_object
        ms = bpy.data.materials.new("suelo")
        ms.use_nodes = True
        bs = ms.node_tree.nodes["Principled BSDF"]
        bs.inputs["Base Color"].default_value = (0.07, 0.07, 0.09, 1)
        bs.inputs["Roughness"].default_value = 1.0
        suelo.data.materials.append(ms)

        malla = bpy.data.materials.new("vista_malla")
        malla.use_nodes = True
        nt = malla.node_tree
        nt.nodes.clear()
        sal = nt.nodes.new("ShaderNodeOutputMaterial")
        wire = nt.nodes.new("ShaderNodeWireframe")
        wire.use_pixel_size = True
        wire.inputs["Size"].default_value = 0.9
        base = nt.nodes.new("ShaderNodeBsdfDiffuse")
        base.inputs["Color"].default_value = (0.42, 0.4, 0.5, 1)
        linea = nt.nodes.new("ShaderNodeEmission")
        linea.inputs["Color"].default_value = (0.75, 0.3, 1.0, 1)
        linea.inputs["Strength"].default_value = 1.5
        mez = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(wire.outputs[0], mez.inputs[0])
        nt.links.new(base.outputs[0], mez.inputs[1])
        nt.links.new(linea.outputs[0], mez.inputs[2])
        nt.links.new(mez.outputs[0], sal.inputs["Surface"])

        cam_d = bpy.data.cameras.new("cam")
        cam_d.lens = 60
        cam_d.clip_end = 100000
        cam = bpy.data.objects.new("cam", cam_d)
        scn.collection.objects.link(cam)
        scn.camera = cam
        dist = radio * 1.08 / math.sin(math.atan(18 / 60))
        vistas = [("Frente", 0, 10), ("3/4", -40, 22), ("Lateral", -90, 8), ("3/4 trasera", -140, 22),
                  ("Arriba", 0, 86), ("Wireframe", -40, 22)]
        tmp = os.path.join(os.path.dirname(ruta), "_tmp_vista.png")
        tiles = []
        for nombre_, az, el in vistas:
            a, e = math.radians(az), math.radians(el)
            direc = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
            cam.location = c + direc * dist
            cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
            scn.view_layers[0].material_override = malla if nombre_ == "Wireframe" else None
            suelo.hide_render = nombre_ == "Wireframe"
            scn.render.filepath = tmp
            bpy.ops.render.render(write_still=True)
            tiles.append((nombre_, Image.open(tmp).convert("RGB").copy()))
        scn.view_layers[0].material_override = None
        os.remove(tmp)
        cab = 54
        hoja = Image.new("RGB", (lado * 3, cab + lado * 2), (14, 12, 20))
        d = ImageDraw.Draw(hoja)
        d.text((14, 8), self.nombre, fill=(200, 110, 255), font=_fuente(26 if not rapido else 14))
        d.text((lado * 3 - 14, 16), f"{total} tris  ·  {dims[0]:.1f} × {dims[1]:.1f} × {dims[2]:.1f} studs  ·  "
               f"{self.zona}", fill=(205, 205, 220), font=_fuente(17 if not rapido else 9, False), anchor="ra")
        for i, (nombre_, im) in enumerate(tiles):
            x, y = (i % 3) * lado, cab + (i // 3) * lado
            hoja.paste(im, (x, y))
            d.rectangle((x, y, x + lado - 1, y + lado - 1), outline=(44, 38, 60))
            d.text((x + 10, y + 8), nombre_, fill=(255, 255, 255), font=_fuente(16 if not rapido else 9))
        hoja.save(ruta, optimize=True)


# ----------------------------------------------------------------------------------------------------------
# Script de montaje de las bestias (Motor6D + asientos)
# ----------------------------------------------------------------------------------------------------------

_PLANTILLA = '''--!strict
--[[
	Monta la bestia cósmica «--NOMBRE--» importada en Studio.
	Pégalo en la barra de comandos (View → Command Bar) con el modelo importado SELECCIONADO y pulsa Enter.

	Lo genera modelos/herramientas/planeta_monstruo/lib.py: no lo edites a mano (los números salen de Blender).

	Qué hace:
	  1. Junta las piezas rígidas en un Model con «--RAIZ--» como PrimaryPart.
	  2. Une cada pieza móvil a su padre con un Motor6D cuyo pivote es la articulación (para animarla).
	  3. Suelda las piezas que no se mueven (las que brillan pasan a material Neon).
	  4. Crea los asientos (Seat) de los puntos de montura, soldados a la raíz.
	  5. Añade AnimationController + Animator (las bestias no son Humanoid) y deja atributos para el juego.

	Las posiciones están en studs, relativas al origen del modelo, en los ejes del archivo FBX. Si Studio gira el
	modelo al importarlo (o lo giras tú), el script lo detecta solo.
]]

local RAIZ = "--RAIZ--"

-- Centro de cada pieza (así se sabe dónde ha quedado el origen del modelo al importarlo).
local CENTROS: { [string]: Vector3 } = {
--CENTROS--
}

-- pieza = { padre, pivote }
local ARTICULACIONES: { [string]: { padre: string, pivote: Vector3 } } = {
--ARTICULACIONES--
}

-- Piezas que brillan: material y color.
local NEON: { [string]: Color3 } = {
--NEON--
}

local CRISTAL: { [string]: number } = {
--CRISTAL--
}

local MONTURAS: { { nombre: string, posicion: Vector3, mirando: Vector3 } } = {
--MONTURAS--
}

local BAHIA_CARGA: { posicion: Vector3, tamano: Vector3 }? = --BAHIA--

local seleccion = game:GetService("Selection"):Get()[1]
assert(seleccion, "Selecciona el modelo importado antes de ejecutar el script")

local piezas: { [string]: BasePart } = {}
for _, d in seleccion:GetDescendants() do
	if d:IsA("BasePart") and CENTROS[d.Name] then
		piezas[d.Name] = d
	end
end
for nombre in CENTROS do
	assert(piezas[nombre], `Falta la pieza {nombre} en el modelo importado`)
end

local raiz = piezas[RAIZ]

-- Marco del origen del modelo. El importador puede girar el modelo entero sobre la vertical (en este proyecto las
-- mallas entran giradas 180°, ver MontarRegion.GIRO_IMPORTACION) y tú puedes haberlo girado después: el giro se
-- averigua comparando dónde ha quedado la pieza más alejada de la raíz con dónde estaba en Blender.
local function marcoOrigen(): CFrame
	local cRaiz = CENTROS[RAIZ]
	local lejos: string? = nil
	local distancia = 0
	for nombre, c in CENTROS do
		local d = Vector3.new(c.X - cRaiz.X, 0, c.Z - cRaiz.Z).Magnitude
		if nombre ~= RAIZ and d > distancia then
			lejos, distancia = nombre, d
		end
	end
	local giro = 0
	if lejos and distancia > 0.5 then
		local esperado = CENTROS[lejos] - cRaiz
		local real = piezas[lejos].Position - raiz.Position
		giro = math.atan2(real.X, real.Z) - math.atan2(esperado.X, esperado.Z)
	end
	return CFrame.new(raiz.Position) * CFrame.Angles(0, giro, 0) * CFrame.new(-cRaiz)
end
local origen = marcoOrigen()

local modelo = Instance.new("Model")
modelo.Name = "--NOMBRE--"
modelo.Parent = seleccion.Parent

for nombre, parte in piezas do
	parte.Anchored = nombre == RAIZ
	parte.CanCollide = nombre == RAIZ
	parte.Massless = nombre ~= RAIZ
	parte.Parent = modelo
	if NEON[nombre] then
		parte.Material = Enum.Material.Neon
		parte.Color = NEON[nombre]
	end
	if CRISTAL[nombre] then
		parte.Material = Enum.Material.Glass
		parte.Transparency = CRISTAL[nombre]
	end
end
modelo.PrimaryPart = raiz

for nombre, parte in piezas do
	if nombre == RAIZ then
		continue
	end
	local art = ARTICULACIONES[nombre]
	if art then
		local padre = piezas[art.padre]
		local marco = origen * CFrame.new(art.pivote)
		local motor = Instance.new("Motor6D")
		motor.Name = nombre
		motor.Part0 = padre
		motor.Part1 = parte
		motor.C0 = padre.CFrame:Inverse() * marco
		motor.C1 = parte.CFrame:Inverse() * marco
		motor.Parent = padre
	else
		local soldadura = Instance.new("WeldConstraint")
		soldadura.Part0 = raiz
		soldadura.Part1 = parte
		soldadura.Parent = parte
	end
end

local asientos = Instance.new("Folder")
asientos.Name = "Monturas"
asientos.Parent = modelo
for i, m in MONTURAS do
	local asiento = Instance.new("Seat")
	asiento.Name = m.nombre
	asiento.Size = Vector3.new(2, 0.4, 2)
	asiento.Transparency = 1
	asiento.CanCollide = false
	asiento.Massless = true
	local pos = origen * m.posicion
	asiento.CFrame = CFrame.lookAt(pos, pos + origen:VectorToWorldSpace(m.mirando))
	asiento:SetAttribute("Orden", i)
	asiento.Parent = asientos
	local soldadura = Instance.new("WeldConstraint")
	soldadura.Part0 = raiz
	soldadura.Part1 = asiento
	soldadura.Parent = asiento
end

if BAHIA_CARGA then
	local bahia = Instance.new("Part")
	bahia.Name = "BahiaCarga"
	bahia.Size = BAHIA_CARGA.tamano
	bahia.CFrame = origen * CFrame.new(BAHIA_CARGA.posicion)
	bahia.Transparency = 1
	bahia.CanCollide = false
	bahia.Massless = true
	bahia.Parent = modelo
	local soldadura = Instance.new("WeldConstraint")
	soldadura.Part0 = raiz
	soldadura.Part1 = bahia
	soldadura.Parent = bahia
end

local controlador = Instance.new("AnimationController")
controlador.Parent = modelo
Instance.new("Animator").Parent = controlador

modelo:SetAttribute("Bestia", "--NOMBRE--")
modelo:SetAttribute("Asientos", #MONTURAS)
if seleccion ~= modelo and #seleccion:GetDescendants() == 0 then
	seleccion:Destroy()
end
game:GetService("Selection"):Set({ modelo })
print(`Bestia --NOMBRE-- montada: {#MONTURAS} asientos`)
'''


def _escribir_montar(ruta, datos, centros):
    def v3(p):
        return f"Vector3.new({p[0]}, {p[1]}, {p[2]})"

    def color(hexa):
        h = hexa.lstrip("#")
        return f"Color3.fromRGB({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)})"

    cen = "\n".join(f'\t["{n}"] = {v3(c)},' for n, c in centros.items())
    art = "\n".join(f'\t["{a["pieza"]}"] = {{ padre = "{a["padre"]}", pivote = {v3(a["pivote"])} }},'
                    for a in datos["articulaciones"])
    neon, cristal = [], []
    for p in datos["piezas"]:
        rb = p.get("roblox") or {}
        if rb.get("material") == "Neon":
            neon.append(f'\t["{p["nombre"]}"] = {color(rb.get("color", VIOLETA))},')
        if rb.get("material") == "Glass":
            cristal.append(f'\t["{p["nombre"]}"] = {rb.get("transparencia", 0.35)},')
    mon = "\n".join(f'\t{{ nombre = "{m["nombre"]}", posicion = {v3(m["posicion"])}, '
                    f'mirando = {v3(m["orientacion"])} }},' for m in datos["puntos_montura"])
    b = datos.get("bahia_carga")
    bahia = f'{{ posicion = {v3(b["posicion"])}, tamano = {v3(b["tamano"])} }}' if b else "nil"
    txt = (_PLANTILLA.replace("--NOMBRE--", datos["nombre"]).replace("--RAIZ--", datos["raiz"])
           .replace("--CENTROS--", cen).replace("--ARTICULACIONES--", art).replace("--NEON--", "\n".join(neon))
           .replace("--CRISTAL--", "\n".join(cristal)).replace("--MONTURAS--", mon).replace("--BAHIA--", bahia))
    with open(ruta, "w", encoding="utf-8") as f:
        f.write(txt)


# ----------------------------------------------------------------------------------------------------------
# Registro de modelos
# ----------------------------------------------------------------------------------------------------------

REGISTRO = {}


def modelo(zona, clase, tam, descripcion="", **kw):
    """Decorador: registra la función que modela `nombre` (el nombre de la función)."""

    def deco(fn):
        REGISTRO[fn.__name__] = dict(fn=fn, zona=zona, clase=clase, tam=tam, descripcion=descripcion, kw=kw)
        return fn

    return deco
