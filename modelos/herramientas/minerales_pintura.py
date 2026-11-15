"""
Relieve y pintura de la malla ALTA de los minerales.

Relieve (dict, amplitudes en fracción del tamaño S del mineral):
  bultos, fino, grano   ruido a tres escalas
  grietas               surcos finos de Voronoi (también dejan "cavidad" para pintar)
  lascas                escalones de roca partida (ruido ridged)
  poros, esc_poros      agujeros redondos (pumita, coral)
  estratos, n_capas     capas horizontales con escalón
  surcos, ancho_surcos  surcos anchos y hondos (por donde se ve un núcleo que brilla)
  olas                  surcos horizontales ondulados (erosión del agua o del viento)
  corte_liso            no tocar las caras que miran al frente (-Y): la cara pulida de un corte

Pintura (dict):
  patron   manchas | liso | moteado | capas | conc | degradado | arcoiris | aurora | espiral | lava | estrellas
  c        lista de colores "#RRGGBB" (sRGB) que usa el patrón
  rug, met rugosidad y metal de base;  emi, ef: color y fuerza (0-1) de la emisión de base
  esc      escala del patrón
  capas    lista de superposiciones {t: tipo, c, rug, met, emi, ef, a (cantidad), esc}
           tipos: vetas, grietas, motas, arriba, abajo, manchas, lado, bandas, puntos
"""

import colorsys
import math

from mathutils import Vector, noise

import comun as c


def col(hexa):
    return Vector(c.srgb(hexa))


def _ss(a, b, x):
    if b == a:
        return 1.0 if x >= b else 0.0
    t = max(0.0, min(1.0, (x - a) / (b - a)))
    return t * t * (3 - 2 * t)


def _hsv(h, s, v):
    r, g, b = colorsys.hsv_to_rgb(h % 1.0, s, v)
    return Vector(c.srgb("#%02X%02X%02X" % (int(r * 255), int(g * 255), int(b * 255))))


# --------------------------------------------------------------------------------------------------------------
# Relieve
# --------------------------------------------------------------------------------------------------------------


def relieve(bm, r, S, semilla, base_plana=False):
    """Desplaza los vértices de `bm` (ALTA) por la normal. Devuelve la cavidad de cada vértice (0-1)."""
    bm.normal_update()
    cav = [0.0] * len(bm.verts)
    if not r:
        return cav
    s = semilla
    zmin = min(v.co.z for v in bm.verts)
    n_capas = r.get("n_capas", 7)
    for i, v in enumerate(bm.verts):
        p = v.co / S
        n = v.normal
        d = 0.0
        if r.get("corte_liso") and n.y < -0.75:
            continue
        if r.get("bultos"):
            d += r["bultos"] * noise.fractal(p * 2.4 + s, 0.6, 2.2, 4, noise_basis="PERLIN_ORIGINAL")
        if r.get("fino"):
            d += r["fino"] * noise.noise(p * 8.0 + s, noise_basis="PERLIN_ORIGINAL")
        if r.get("grano"):
            d += r["grano"] * noise.noise(p * 26.0 + s, noise_basis="PERLIN_ORIGINAL")
        g = 0.0
        if r.get("grietas"):
            pd = p * 2.6 + s + Vector(noise.noise_vector(p * 2.0 + s)) * 0.35
            dist = noise.voronoi(pd, distance_metric="DISTANCE", exponent=2.5)[0]
            g = max(0.0, 0.05 - (dist[1] - dist[0])) / 0.05
            g *= max(0.0, min(1.0, noise.noise(p * 1.6 + s * 3) * 2.5 + 0.35))
            d -= r["grietas"] * g
        if r.get("lascas"):
            lasca = noise.ridged_multi_fractal(p * 3.2 + s * 2, 1.0, 2.0, 3, 0.0, 2.0)
            d += r["lascas"] * (lasca - 0.6)
        if r.get("poros"):
            dist = noise.voronoi(p * r.get("esc_poros", 9.0) + s, distance_metric="DISTANCE")[0]
            poro = _ss(0.32, 0.18, dist[0])
            d -= r["poros"] * poro
            g = max(g, poro)
        if r.get("estratos"):
            capa = (p.z * n_capas + 0.3 * noise.noise(p * 1.5 + s)) % 1.0
            lado = 1.0 - abs(n.z) ** 2
            d += lado * r["estratos"] * (0.4 * capa - 0.6 * (1.0 if capa < 0.13 else 0.0))
            if capa < 0.13:
                g = max(g, 0.5 * lado)
        if r.get("surcos"):
            pd = p * r.get("esc_surcos", 2.2) + s * 1.3 + Vector(noise.noise_vector(p * 1.5 + s)) * 0.3
            dist = noise.voronoi(pd, distance_metric="DISTANCE", exponent=2.5)[0]
            ancho = r.get("ancho_surcos", 0.07)
            sur = _ss(ancho, ancho * 0.35, dist[1] - dist[0])
            d -= r["surcos"] * sur
            g = max(g, sur)
        if r.get("olas"):
            o = math.sin(p.z * 26 + 2.0 * noise.noise(p * 2.0 + s))
            d -= r["olas"] * max(0.0, o) ** 3 * (1 - abs(n.z))
        if base_plana and v.co.z < zmin + 0.03 * S:
            d = min(d, 0.0) * 0.3
        v.co += n * d * S
        cav[i] = g
    return cav


# --------------------------------------------------------------------------------------------------------------
# Patrones de base
# --------------------------------------------------------------------------------------------------------------


def _patron(P, p, n, s, z01, cols):
    """Devuelve (color, factor de emisión) del patrón de base."""
    tipo = P.get("patron", "manchas")
    esc = P.get("esc", 1.0)
    c0 = cols[0]
    c1 = cols[1] if len(cols) > 1 else cols[0]
    if tipo == "liso":
        t = 0.5 + 0.5 * noise.fractal(p * 2.0 * esc + s, 0.7, 2.0, 3)
        return c0.lerp(c1, t * 0.5), 1.0
    if tipo == "manchas":
        t = 0.5 + 0.5 * noise.fractal(p * 2.6 * esc + s, 0.7, 2.0, 4)
        t = max(0.0, min(1.0, 0.15 + 0.7 * t + 0.25 * (z01 - 0.5)))
        return c1.lerp(c0, t), 1.0
    if tipo == "moteado":
        dist, pts = noise.voronoi(p * 16.0 * esc + s, distance_metric="DISTANCE")
        k = 0.5 + 0.5 * noise.noise(Vector(pts[0]) * 3.1 + s)
        pesos = P.get("pesos", [0.55, 0.3, 0.15])
        acum = 0.0
        elegido = cols[-1]
        for cc, w in zip(cols, pesos):
            acum += w
            if k < acum:
                elegido = cc
                break
        var = 0.85 + 0.3 * (0.5 + 0.5 * noise.noise(p * 40 + s))
        return elegido * var, 1.0
    if tipo == "capas":
        val = p.z * 8.0 * esc + 0.6 * noise.fractal(p * 1.8 + s, 0.6, 2.0, 3)
        i = math.floor(val)
        fr = val - i
        a = cols[i % len(cols)]
        b = cols[(i + 1) % len(cols)]
        mezcla = _ss(0.75, 1.0, fr) * P.get("suavizar_capas", 0.5)
        brillo = 0.88 + 0.24 * (0.5 + 0.5 * math.sin(i * 2.7))
        return a.lerp(b, mezcla) * brillo, 1.0
    if tipo == "conc":
        cen = Vector(P.get("centro", (0, 0, 0.45)))
        q = p - cen
        ex, ey, ez = P.get("ejes", (1.0, 0.3, 1.15))
        dd = Vector((q.x * ex, q.y * ey, q.z * ez)).length + 0.06 * noise.fractal(p * 3.0 + s, 0.6, 2.0, 3)
        val = dd * 22.0 * esc
        i = math.floor(val)
        fr = val - i
        a = cols[i % len(cols)]
        b = cols[(i + 1) % len(cols)]
        return a.lerp(b, _ss(0.6, 1.0, fr)), 1.0
    if tipo == "degradado":
        t = max(0.0, min(1.0, z01 + 0.12 * noise.noise(p * 3.0 + s)))
        if len(cols) > 2:
            seg = t * (len(cols) - 1)
            i = min(len(cols) - 2, int(seg))
            return cols[i].lerp(cols[i + 1], seg - i), 0.4 + 0.6 * t
        return c0.lerp(c1, t), 0.4 + 0.6 * t
    if tipo == "arcoiris":
        h = math.atan2(n.y, n.x) / math.tau + 0.35 * n.z + 0.25 * noise.noise(p * 2.5 * esc + s)
        sat = P.get("sat", 0.75)
        brillo = P.get("brillo", 0.95)
        return _hsv(h, sat, brillo), 1.0
    if tipo == "opalo":
        dist, pts = noise.voronoi(p * 11.0 * esc + s, distance_metric="DISTANCE")
        h = 0.5 + 0.5 * noise.noise(Vector(pts[0]) * 2.3 + s) + 0.3 * n.x
        destello = _ss(0.35, 0.0, dist[0]) * (0.5 + 0.5 * noise.noise(Vector(pts[0]) * 5 + s))
        return c0.lerp(_hsv(h, 0.85, 1.0), destello * P.get("fuerza", 0.8)), destello
    if tipo == "aurora":
        t = max(0.0, min(0.999, z01 + 0.18 * noise.noise(Vector((p.x * 6, p.y * 6, p.z * 0.8)) + s)))
        seg = t * (len(cols) - 1)
        i = int(seg)
        franja = 0.7 + 0.3 * math.sin(p.x * 30 + p.y * 18 + noise.noise(p * 4 + s) * 4)
        return cols[i].lerp(cols[min(i + 1, len(cols) - 1)], seg - i) * franja, franja
    if tipo == "espiral":
        # Galaxia en el plano del disco (local): brazos logarítmicos + núcleo.
        q = p - Vector(P.get("centro", (0, 0, 0.33)))
        w = q.y * 0.375 + q.z * 0.927  # el disco está inclinado 68° sobre X
        r = max(1e-4, math.hypot(q.x, w))
        th = math.atan2(w, q.x)
        brazo = 0.5 + 0.5 * math.cos(2 * (th - 3.2 * math.log(r * 10 + 1e-3)))
        brazo = brazo ** 2.5 * _ss(0.32, 0.05, r)
        nuc = _ss(0.08, 0.0, r)
        polvo = 0.5 + 0.5 * noise.noise(p * 30 + s)
        f = max(nuc, brazo * (0.6 + 0.4 * polvo))
        cc = cols[0].lerp(cols[1], brazo).lerp(cols[2] if len(cols) > 2 else cols[1], nuc)
        return cc, max(0.15, f)
    if tipo == "lava":
        dist = noise.voronoi(p * 5.0 * esc + s, distance_metric="DISTANCE", exponent=2.5)[0]
        caliente = _ss(0.12, 0.0, dist[1] - dist[0])
        t = 0.5 + 0.5 * noise.noise(p * 8 + s)
        return c0.lerp(c1, caliente * (0.6 + 0.4 * t)), caliente
    if tipo == "estrellas":
        dist = noise.voronoi(p * 24.0 * esc + s, distance_metric="DISTANCE")[0]
        est = _ss(0.12, 0.02, dist[0]) * (1.0 if noise.noise(p * 24 * esc + s) > -0.1 else 0.0)
        neb = 0.5 + 0.5 * noise.fractal(p * 3 + s, 0.6, 2.0, 3)
        base = c0.lerp(cols[2] if len(cols) > 2 else c0, neb * 0.6)
        return base.lerp(c1, est), max(est, neb * 0.03)
    raise ValueError(tipo)


# --------------------------------------------------------------------------------------------------------------
# Máscaras de las capas
# --------------------------------------------------------------------------------------------------------------


def _mascara(ov, p, n, s, z01, cav):
    t = ov["t"]
    a = ov.get("a", 0.5)
    esc = ov.get("esc", 1.0)
    if t == "vetas":
        q = p * 2.2 * esc + s * 1.7 + Vector(noise.noise_vector(p * 1.4 * esc + s)) * 0.5
        w = 1.0 - abs(noise.noise(q, noise_basis="PERLIN_ORIGINAL"))
        return _ss(1.0 - a * 0.12, 1.0 - a * 0.04, w)
    if t == "grietas":
        return min(1.0, cav * a * 2.0)
    if t == "motas":
        dist, pts = noise.voronoi(p * 14.0 * esc + s * 0.7, distance_metric="DISTANCE")
        sel = 1.0 if noise.noise(Vector(pts[0]) * 7.7 + s) > (0.5 - a) else 0.0
        return _ss(0.3, 0.12, dist[0]) * sel
    if t == "puntos":
        dist, pts = noise.voronoi(p * 30.0 * esc + s * 0.3, distance_metric="DISTANCE")
        sel = 1.0 if noise.noise(Vector(pts[0]) * 9.1 + s) > (0.6 - a) else 0.0
        return _ss(0.14, 0.04, dist[0]) * sel
    if t == "arriba":
        v = n.z + 0.35 * noise.fractal(p * 3.0 * esc + s, 0.6, 2.0, 3)
        return _ss(1.0 - a, 1.0 - a + 0.25, v)
    if t == "abajo":
        return _ss(a, 0.0, z01 + 0.05 * noise.noise(p * 5 + s))
    if t == "manchas":
        v = noise.fractal(p * 2.5 * esc + s * 2.3, 0.6, 2.0, 4)
        return _ss(0.35 - a * 0.6, 0.5 - a * 0.6, v)
    if t == "lado":
        return _ss(0.55, 0.8, -n.y)
    if t == "nolado":
        return 1.0 - _ss(0.55, 0.8, -n.y)
    if t == "bandas":
        v = math.sin(p.z * 40 * esc + 3 * noise.noise(p * 2 + s))
        return _ss(1 - a, 1.0, v)
    raise ValueError(t)


def pintar(bm, P, S, semilla, centro, zmin, zmax, cav):
    """Calcula color, rugosidad, metal y emisión de cada vértice y los guarda como atributos de punto."""
    capa_col = bm.verts.layers.float_color.get("col") or bm.verts.layers.float_color.new("col")
    capa_emi = bm.verts.layers.float_color.get("emi") or bm.verts.layers.float_color.new("emi")
    capa_rug = bm.verts.layers.float.get("rug") or bm.verts.layers.float.new("rug")
    capa_met = bm.verts.layers.float.get("met") or bm.verts.layers.float.new("met")
    cols = [col(h) for h in P.get("c", ["#808080"])]
    rug0 = P.get("rug", 0.85)
    met0 = P.get("met", 0.0)
    emi0 = col(P["emi"]) * P.get("ef", 1.0) if P.get("emi") else None
    capas = []
    for ov in P.get("capas", ()):
        capas.append((ov, col(ov["c"]) if "c" in ov else None,
                      col(ov["emi"]) * ov.get("ef", 1.0) if ov.get("emi") else None))
    alto = max(1e-4, zmax - zmin)
    s = semilla
    oscurecer_base = P.get("oscurecer_base", 0.25)
    bm.normal_update()
    for i, v in enumerate(bm.verts):
        p = (v.co - centro) / S
        n = v.normal
        z01 = (v.co.z - zmin) / alto
        cc, f = _patron(P, p, n, s, z01, cols)
        # Algo más oscuro abajo (polvo, sombra de contacto) para que el mineral "pese".
        cc = cc * (1.0 - oscurecer_base * (1.0 - min(1.0, z01 * 2.5)))
        rug, met = rug0, met0
        emi = emi0 * f if emi0 is not None else Vector((0, 0, 0))
        for ov, oc, oe in capas:
            m = _mascara(ov, p, n, s, z01, cav[i])
            if m <= 0.0:
                continue
            m *= ov.get("fuerza", 1.0)
            if oc is not None:
                cc = cc.lerp(oc, m)
            if "rug" in ov:
                rug += (ov["rug"] - rug) * m
            if "met" in ov:
                met += (ov["met"] - met) * m
            if oe is not None:
                emi = emi.lerp(oe, m)
        v[capa_col] = (cc.x, cc.y, cc.z, 1.0)
        v[capa_emi] = (emi.x, emi.y, emi.z, 1.0)
        v[capa_rug] = max(0.02, min(1.0, rug))
        v[capa_met] = max(0.0, min(1.0, met))
