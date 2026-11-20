"""
Campos de distancia con signo (SDF) en numpy y su paso a malla con marching cubes.

Las bestias son orgánicas: en vez de juntar cilindros, cada pieza se describe como un campo f(x, y, z) que es
negativo dentro de la carne y positivo fuera. Así las uniones (cabeza con cuerpo, cola con lomo, crestas sobre
los ojos) salen suaves, y los cortes entre piezas del rig son planos limpios con 0,02 studs de separación.

Todo va en studs (1 unidad de Blender = 1 stud).

Convención de los campos: una función `campo(X, Y, Z)` que recibe arrays numpy (con broadcasting) y devuelve f.
Para los campos que en el fondo son 2D (la planta de la manta, su grosor) hay ayudas que evalúan en la rejilla XY
una sola vez y la reutilizan en todas las rebanadas Z.
"""

import math

import numpy as np

# --------------------------------------------------------------------------------------------------------------
# Operaciones básicas
# --------------------------------------------------------------------------------------------------------------


def smin(a, b, k):
    """Unión suave (mínimo polinómico). k = radio de la transición en studs."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smax(a, b, k):
    """Intersección suave."""
    return -smin(-a, -b, k)


def sstep(a, b, t):
    """Smoothstep de a a b (si a > b, decreciente)."""
    x = np.clip((t - a) / (b - a), 0.0, 1.0)
    return x * x * (3 - 2 * x)


def elipsoide(X, Y, Z, c, r, rot=None):
    """Elipsoide (aproximación de distancia con k0*(k0-1)/k1, buena cerca de la superficie)."""
    px, py, pz = X - c[0], Y - c[1], Z - c[2]
    if rot is not None:  # rot: matriz 3x3 (mundo -> local)
        px, py, pz = (rot[0][0] * px + rot[0][1] * py + rot[0][2] * pz,
                      rot[1][0] * px + rot[1][1] * py + rot[1][2] * pz,
                      rot[2][0] * px + rot[2][1] * py + rot[2][2] * pz)
    k0 = np.sqrt((px / r[0]) ** 2 + (py / r[1]) ** 2 + (pz / r[2]) ** 2)
    k1 = np.sqrt((px / r[0] ** 2) ** 2 + (py / r[1] ** 2) ** 2 + (pz / r[2] ** 2) ** 2)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)


def capsula(X, Y, Z, a, b, ra, rb=None):
    """Cápsula (cono redondeado) de a a b con radios ra -> rb."""
    rb = ra if rb is None else rb
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    ba = b - a
    L2 = float(ba @ ba)
    px, py, pz = X - a[0], Y - a[1], Z - a[2]
    t = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / L2, 0.0, 1.0)
    dx, dy, dz = px - ba[0] * t, py - ba[1] * t, pz - ba[2] * t
    return np.sqrt(dx * dx + dy * dy + dz * dz) - (ra + (rb - ra) * t)


def tubo(X, Y, Z, puntos, radios, escala_z=1.0, k=0.0):
    """Tubo por una polilínea con radio variable (unión de cápsulas). `escala_z` < 1 achata la sección."""
    Zs = Z / escala_z if escala_z != 1.0 else Z
    f = None
    for i in range(len(puntos) - 1):
        a = (puntos[i][0], puntos[i][1], puntos[i][2] / escala_z)
        b = (puntos[i + 1][0], puntos[i + 1][1], puntos[i + 1][2] / escala_z)
        d = capsula(X, Y, Zs, a, b, radios[i], radios[i + 1])
        f = d if f is None else smin(f, d, k)
    return f * min(1.0, escala_z)


def semiespacio(X, Y, Z, punto, normal):
    """Semiespacio: negativo en el lado contrario a `normal` (lo que queda dentro)."""
    n = np.asarray(normal, dtype=np.float64)
    n = n / np.linalg.norm(n)
    return (X - punto[0]) * n[0] + (Y - punto[1]) * n[1] + (Z - punto[2]) * n[2]


def matriz_giro(eje, angulo):
    """Matriz 3x3 de rotación (Rodrigues), como lista de listas."""
    eje = np.asarray(eje, dtype=np.float64)
    eje = eje / np.linalg.norm(eje)
    x, y, z = eje
    c, s = math.cos(angulo), math.sin(angulo)
    C = 1 - c
    return [[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
            [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
            [z * x * C - y * s, z * y * C + x * s, c + z * z * C]]


def transpuesta(m):
    return [[m[j][i] for j in range(3)] for i in range(3)]


# --------------------------------------------------------------------------------------------------------------
# Curvas 2D y distancia a polígonos
# --------------------------------------------------------------------------------------------------------------


def catmull_rom(puntos, por_tramo=12, cerrada=True):
    """Curva suave que pasa por los puntos de control (centrípeta no hace falta aquí: los puntos están repartidos)."""
    P = np.asarray(puntos, dtype=np.float64)
    n = len(P)
    res = []
    tramos = n if cerrada else n - 1
    for i in range(tramos):
        p0 = P[(i - 1) % n] if (cerrada or i > 0) else P[0] * 2 - P[1]
        p1 = P[i % n]
        p2 = P[(i + 1) % n]
        p3 = P[(i + 2) % n] if (cerrada or i + 2 < n) else P[-1] * 2 - P[-2]
        for k in range(por_tramo):
            t = k / por_tramo
            t2, t3 = t * t, t * t * t
            res.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    if not cerrada:
        res.append(P[-1])
    return np.array(res)


def remuestrear(polilinea, paso):
    """Reparte puntos a distancia constante a lo largo de una polilínea abierta."""
    P = np.asarray(polilinea, dtype=np.float64)
    seg = np.linalg.norm(np.diff(P, axis=0), axis=1)
    acum = np.concatenate([[0], np.cumsum(seg)])
    total = acum[-1]
    n = max(2, int(round(total / paso)) + 1)
    ts = np.linspace(0, total, n)
    res = np.empty((n, P.shape[1]))
    for d in range(P.shape[1]):
        res[:, d] = np.interp(ts, acum, P[:, d])
    return res


def distancia_segmentos(px, py, poli, cerrado=True, bloque=40000):
    """Distancia (sin signo) de los puntos (px, py) a una polilínea 2D. px, py: arrays de igual forma."""
    forma = px.shape
    qx = px.ravel()
    qy = py.ravel()
    P = np.asarray(poli, dtype=np.float64)
    A = P if cerrado else P[:-1]
    B = np.roll(P, -1, axis=0) if cerrado else P[1:]
    ax, ay = A[:, 0][None, :], A[:, 1][None, :]
    bx, by = (B[:, 0] - A[:, 0])[None, :], (B[:, 1] - A[:, 1])[None, :]
    L2 = np.maximum(bx * bx + by * by, 1e-12)
    out = np.empty(qx.shape)
    for i in range(0, len(qx), bloque):
        x = qx[i:i + bloque, None]
        y = qy[i:i + bloque, None]
        t = np.clip(((x - ax) * bx + (y - ay) * by) / L2, 0, 1)
        dx = x - ax - bx * t
        dy = y - ay - by * t
        out[i:i + bloque] = np.sqrt((dx * dx + dy * dy).min(axis=1))
    return out.reshape(forma)


def dentro_poligono(px, py, poli, bloque=40000):
    """Prueba par-impar de un polígono cerrado."""
    forma = px.shape
    qx = px.ravel()
    qy = py.ravel()
    P = np.asarray(poli, dtype=np.float64)
    x1, y1 = P[:, 0][None, :], P[:, 1][None, :]
    Q = np.roll(P, -1, axis=0)
    x2, y2 = Q[:, 0][None, :], Q[:, 1][None, :]
    out = np.empty(qx.shape, dtype=bool)
    for i in range(0, len(qx), bloque):
        x = qx[i:i + bloque, None]
        y = qy[i:i + bloque, None]
        cruza = ((y1 > y) != (y2 > y)) & (x < (x2 - x1) * (y - y1) / np.where(y2 - y1 == 0, 1e-12, y2 - y1) + x1)
        out[i:i + bloque] = (cruza.sum(axis=1) % 2) == 1
    return out.reshape(forma)


def sdf_poligono(px, py, poli):
    d = distancia_segmentos(px, py, poli, cerrado=True)
    return np.where(dentro_poligono(px, py, poli), -d, d)


# --------------------------------------------------------------------------------------------------------------
# Malla: marching cubes por bloques
# --------------------------------------------------------------------------------------------------------------


def volumen(campo, mn, mx, voxel, bloque_z=24):
    """
    Evalúa `campo(xs, ys, zs)` (ejes 1D; el campo hace el broadcasting y devuelve (nx, ny, nz)) en la caja
    [mn, mx] con el tamaño de vóxel dado, por rebanadas de Z para no gastar memoria. Devuelve (vol, origen, paso).
    """
    mn = np.asarray(mn, dtype=np.float64)
    mx = np.asarray(mx, dtype=np.float64)
    n = np.ceil((mx - mn) / voxel).astype(int) + 1
    xs = mn[0] + np.arange(n[0]) * voxel
    ys = mn[1] + np.arange(n[1]) * voxel
    zs = mn[2] + np.arange(n[2]) * voxel
    vol = np.empty((n[0], n[1], n[2]), dtype=np.float32)
    for k in range(0, n[2], bloque_z):
        vol[:, :, k:k + bloque_z] = campo(xs, ys, zs[k:k + bloque_z])
    # Borde abierto: fuerza "fuera" en las caras de la caja para que la malla salga cerrada.
    vol[0, :, :] = vol[-1, :, :] = 1.0
    vol[:, 0, :] = vol[:, -1, :] = 1.0
    vol[:, :, 0] = vol[:, :, -1] = 1.0
    return vol, mn, voxel


def malla_de_volumen(vol, origen, paso):
    """Marching cubes -> (vértices Nx3 en studs, caras Mx3) con las normales hacia fuera."""
    from skimage.measure import marching_cubes

    verts, caras, _, _ = marching_cubes(vol, level=0.0, spacing=(paso, paso, paso), allow_degenerate=False)
    verts = verts + origen
    # skimage orienta las caras hacia el lado de valores altos (fuera para nosotros); lo comprobamos igualmente
    # en Blender con recalc_normals, que es más fiable.
    return verts.astype(np.float64), caras.astype(np.int64)


def centro_de_masa(vol, origen, paso):
    idx = np.argwhere(vol < 0)
    if len(idx) == 0:
        return np.zeros(3)
    return origen + idx.mean(axis=0) * paso
