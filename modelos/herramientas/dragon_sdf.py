"""
Modelado por campos de distancia (SDF) con numpy, para las formas orgánicas del Dragón Leviatán.

Por qué así: el cuerpo de una criatura grande (pecho, cuello, cola, patas, cráneo) es una suma de masas musculares
que se funden entre sí. Con un campo de distancia se escriben esas masas como cápsulas, conos redondeados y
elipsoides, se funden con una unión suave (smin) y se les talla el detalle (escamas, cicatrices, grietas) restando o
sumando al campo. Después «marching cubes» saca la malla de alta resolución.

Todo está en studs (1 unidad = 1 stud). Las funciones reciben P: array (N, 3) de puntos y devuelven (N,) distancias
con signo (negativo = dentro).
"""

import math

import numpy as np

# --------------------------------------------------------------------------------------------------------------
# Operaciones
# --------------------------------------------------------------------------------------------------------------


def smin(a, b, k):
    """Unión suave polinómica: funde dos formas con un filete de tamaño ~k."""
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
    return b * (1 - h) + a * h - k * h * (1 - h)


def smax(a, b, k):
    """Intersección / resta suave (smax(a, -b) resta b de a)."""
    return -smin(-a, -b, k)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def normalizar(v):
    v = np.asarray(v, dtype=np.float64)
    return v / np.linalg.norm(v)


def base_ortonormal(eje, arriba=(0, 0, 1)):
    """Devuelve (u, v, w): w = eje, u = lado, v = 'arriba' del corte transversal."""
    w = normalizar(eje)
    a = np.asarray(arriba, dtype=np.float64)
    if abs(np.dot(a, w)) > 0.97:
        a = np.array([0.0, 1.0, 0.0]) if abs(w[1]) < 0.9 else np.array([1.0, 0.0, 0.0])
    u = normalizar(np.cross(a, w))
    v = np.cross(w, u)
    return u, v, w


# --------------------------------------------------------------------------------------------------------------
# Primitivas
# --------------------------------------------------------------------------------------------------------------


def esfera(P, c, r):
    return np.linalg.norm(P - np.asarray(c), axis=1) - r


def elipsoide(P, c, radios, rot=None):
    """Elipsoide (aproximación de Íñigo Quílez). rot: matriz 3x3 local->mundo."""
    q = P - np.asarray(c)
    if rot is not None:
        q = q @ np.asarray(rot)  # mundo -> local (rot ortonormal: inversa = traspuesta)
    r = np.asarray(radios, dtype=np.float64)
    k0 = np.linalg.norm(q / r, axis=1)
    k1 = np.linalg.norm(q / (r * r), axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def cono_redondeado(P, a, b, ra, rb):
    """Cápsula de radio variable entre a (radio ra) y b (radio rb). Exacta (Quílez)."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    ba = b - a
    l2 = float(ba @ ba)
    rr = ra - rb
    a2 = l2 - rr * rr
    il2 = 1.0 / l2
    pa = P - a
    y = pa @ ba
    z = y - l2
    t = pa * l2 - np.outer(y, ba)
    x2 = np.einsum("ij,ij->i", t, t)
    y2 = y * y * l2
    z2 = z * z * l2
    k = math.copysign(1.0, rr) * rr * rr * x2
    d1 = np.sqrt(x2 + z2) * il2 - rb
    d2 = np.sqrt(x2 + y2) * il2 - ra
    d3 = (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - ra
    out = np.where(np.sign(z) * a2 * z2 > k, d1, np.where(np.sign(y) * a2 * y2 < k, d2, d3))
    return out


def capsula_eliptica(P, a, b, rxa, rza, rxb, rzb, arriba=(0, 0, 1)):
    """
    Tramo de sección elíptica (ancho rx, alto rz) entre a y b, con los radios interpolados y extremos redondeados.
    Sirve para el pecho (más ancho que alto), la cola (más alta que ancha) o el hocico.
    """
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    u, v, w = base_ortonormal(b - a, arriba)
    L = float(np.linalg.norm(b - a))
    q = P - a
    s = q @ w
    t = np.clip(s / L, 0.0, 1.0)
    rx = rxa + (rxb - rxa) * t
    rz = rza + (rzb - rza) * t
    dw = s - t * L
    du = q @ u
    dv = q @ v
    rw = np.minimum(rx, rz)
    lq = np.stack([du / rx, dv / rz, dw / rw], axis=1)
    k0 = np.linalg.norm(lq, axis=1)
    lq2 = np.stack([du / rx**2, dv / rz**2, dw / rw**2], axis=1)
    k1 = np.linalg.norm(lq2, axis=1)
    return k0 * (k0 - 1.0) / np.maximum(k1, 1e-9)


def caja_redondeada(P, c, medio, r=0.0, rot=None):
    q = P - np.asarray(c)
    if rot is not None:
        q = q @ np.asarray(rot)
    d = np.abs(q) - (np.asarray(medio) - r)
    fuera = np.linalg.norm(np.maximum(d, 0), axis=1)
    dentro = np.minimum(np.max(d, axis=1), 0)
    return fuera + dentro - r


def semiespacio(P, p, n):
    """Distancia con signo a un plano: negativo detrás del plano (en sentido contrario a n)."""
    return (P - np.asarray(p)) @ normalizar(n)


def tubo(P, puntos, radios, k=0.3, eliptico=None, arriba=(0, 0, 1)):
    """Cadena de conos redondeados por una polilínea (cuello, cola, dedos). eliptico: lista de (rx, rz) por punto."""
    d = None
    for i in range(len(puntos) - 1):
        if eliptico is None:
            di = cono_redondeado(P, puntos[i], puntos[i + 1], radios[i], radios[i + 1])
        else:
            (rxa, rza), (rxb, rzb) = eliptico[i], eliptico[i + 1]
            di = capsula_eliptica(P, puntos[i], puntos[i + 1], rxa, rza, rxb, rzb, arriba)
        d = di if d is None else smin(d, di, k)
    return d


def bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = (np.asarray(p, dtype=np.float64) for p in (p0, p1, p2, p3))
    return (1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t**2 * p2 + t**3 * p3


# --------------------------------------------------------------------------------------------------------------
# Ruido y patrones (para escamas, piel y grietas)
# --------------------------------------------------------------------------------------------------------------


def _hash3(ix, iy, iz, semilla):
    """Hash entero -> 3 floats en [0,1) por celda (vectorizado)."""
    h = (ix.astype(np.int64) * 73856093) ^ (iy.astype(np.int64) * 19349663) ^ (iz.astype(np.int64) * 83492791)
    h = h ^ (semilla * 2654435761)
    h = (h ^ (h >> 13)) * 1274126177
    h = h ^ (h >> 16)
    a = (h & 0x3FF) / 1024.0
    b = ((h >> 10) & 0x3FF) / 1024.0
    c = ((h >> 20) & 0x3FF) / 1024.0
    return a, b, c


def voronoi(P, celda, semilla=0, jitter=0.85):
    """
    Ruido celular 3D. Devuelve (f1, f2, centro_mas_cercano (N,3), id_celda (N,)).
    f2 - f1 es la distancia al borde de la celda: con eso se tallan escamas y placas.
    """
    q = P / celda
    base = np.floor(q).astype(np.int64)
    f1 = np.full(len(P), 1e9)
    f2 = np.full(len(P), 1e9)
    cen = np.zeros_like(P)
    ids = np.zeros(len(P), dtype=np.int64)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                cx, cy, cz = base[:, 0] + dx, base[:, 1] + dy, base[:, 2] + dz
                ha, hb, hc = _hash3(cx, cy, cz, semilla)
                px = cx + 0.5 + (ha - 0.5) * jitter
                py = cy + 0.5 + (hb - 0.5) * jitter
                pz = cz + 0.5 + (hc - 0.5) * jitter
                d = np.sqrt((q[:, 0] - px) ** 2 + (q[:, 1] - py) ** 2 + (q[:, 2] - pz) ** 2)
                menor = d < f1
                f2 = np.where(menor, f1, np.minimum(f2, d))
                f1 = np.where(menor, d, f1)
                cen[menor] = np.stack([px[menor], py[menor], pz[menor]], axis=1)
                ids[menor] = (cx[menor] * 7919 + cy[menor] * 104729 + cz[menor] * 1299709)
    return f1 * celda, f2 * celda, cen * celda, ids


def ruido_valor(P, escala, semilla=0):
    """Ruido de valor 3D suave en [-1, 1] (interpolación trilineal con suavizado)."""
    q = P / escala
    i = np.floor(q).astype(np.int64)
    f = q - i
    f = f * f * (3 - 2 * f)
    out = np.zeros(len(P))
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                a, _, _ = _hash3(i[:, 0] + dx, i[:, 1] + dy, i[:, 2] + dz, semilla)
                wx = f[:, 0] if dx else 1 - f[:, 0]
                wy = f[:, 1] if dy else 1 - f[:, 1]
                wz = f[:, 2] if dz else 1 - f[:, 2]
                out += (a * 2 - 1) * wx * wy * wz
    return out


def fbm(P, escala, octavas=4, semilla=0, ganancia=0.5):
    total = np.zeros(len(P))
    amp = 1.0
    norma = 0.0
    for o in range(octavas):
        total += amp * ruido_valor(P, escala / (2**o), semilla + o * 31)
        norma += amp
        amp *= ganancia
    return total / norma


def dist_segmentos(P, A, B):
    """Distancia mínima de cada punto a un conjunto de segmentos A[i]-B[i]. Devuelve (dist, t, índice)."""
    A = np.asarray(A, dtype=np.float64)
    B = np.asarray(B, dtype=np.float64)
    mejor = np.full(len(P), 1e9)
    mejor_t = np.zeros(len(P))
    mejor_i = np.zeros(len(P), dtype=np.int64)
    for i in range(len(A)):
        ab = B[i] - A[i]
        l2 = max(float(ab @ ab), 1e-12)
        t = np.clip((P - A[i]) @ ab / l2, 0, 1)
        d = np.linalg.norm(P - (A[i] + t[:, None] * ab), axis=1)
        m = d < mejor
        mejor = np.where(m, d, mejor)
        mejor_t = np.where(m, t, mejor_t)
        mejor_i = np.where(m, i, mejor_i)
    return mejor, mejor_t, mejor_i


# --------------------------------------------------------------------------------------------------------------
# Mallado: marching cubes por bloques (solo se evalúa cerca de la superficie)
# --------------------------------------------------------------------------------------------------------------


def mallar(campo, mn, mx, voxel, bloque=40, guia=None, guia_voxel=None):
    """
    Evalúa `campo(P)` en una rejilla entre mn y mx con paso `voxel` y saca la isosuperficie 0.
    Para no evaluar millones de puntos lejos de la superficie se usa un campo guía grueso: los bloques cuyo centro
    está más lejos de la superficie que su radio se rellenan con el signo sin evaluar.
    Devuelve (verts (V,3), caras (F,3)).
    """
    from skimage import measure

    mn = np.asarray(mn, dtype=np.float64)
    mx = np.asarray(mx, dtype=np.float64)
    n = np.ceil((mx - mn) / voxel).astype(int) + 1
    vol = np.empty(tuple(n), dtype=np.float32)
    radio_bloque = math.sqrt(3) * bloque * voxel / 2
    guia = guia or campo
    for i0 in range(0, n[0], bloque):
        for j0 in range(0, n[1], bloque):
            for k0 in range(0, n[2], bloque):
                i1, j1, k1 = min(i0 + bloque + 1, n[0]), min(j0 + bloque + 1, n[1]), min(k0 + bloque + 1, n[2])
                c = mn + voxel * np.array([(i0 + i1 - 1) / 2, (j0 + j1 - 1) / 2, (k0 + k1 - 1) / 2])
                dc = float(guia(c[None, :])[0])
                if abs(dc) > radio_bloque * 1.05 + 0.6:
                    vol[i0:i1, j0:j1, k0:k1] = math.copysign(1.0, dc)
                    continue
                xs = mn[0] + voxel * np.arange(i0, i1)
                ys = mn[1] + voxel * np.arange(j0, j1)
                zs = mn[2] + voxel * np.arange(k0, k1)
                G = np.stack(np.meshgrid(xs, ys, zs, indexing="ij"), axis=-1).reshape(-1, 3)
                vol[i0:i1, j0:j1, k0:k1] = campo(G).reshape(i1 - i0, j1 - j0, k1 - k0)
    # Borde de la rejilla fuera del objeto, para cerrar la malla.
    vol[0, :, :] = vol[-1, :, :] = 1
    vol[:, 0, :] = vol[:, -1, :] = 1
    vol[:, :, 0] = vol[:, :, -1] = 1
    if vol.min() >= 0:
        return np.zeros((0, 3)), np.zeros((0, 3), dtype=np.int64)
    verts, caras, _, _ = measure.marching_cubes(vol, level=0.0, spacing=(voxel, voxel, voxel))
    verts += mn
    # Con gradient_direction="descent" (por defecto) skimage ya deja las normales hacia fuera (campo creciente).
    return verts, caras
