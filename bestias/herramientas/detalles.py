"""
Detalles geométricos que se apoyan sobre la piel (escamas, correas, anillos, dientes, espinas...).

Todo se proyecta sobre la malla alta de la pieza con un árbol BVH: así el detalle sigue la curvatura real del cuerpo
y no flota ni se hunde. Las medidas van en studs.
"""

import math

from mathutils import Matrix, Vector


def marco(n, preferido=Vector((1, 0, 0))):
    """Base ortonormal (t1, t2, n) en un punto de normal n."""
    n = Vector(n).normalized()
    t1 = preferido - n * preferido.dot(n)
    if t1.length < 1e-4:
        t1 = Vector((0, 1, 0)) - n * n.y
    t1.normalize()
    t2 = n.cross(t1).normalized()
    return t1, t2, n


def proyectar(bvh, x, y, z_alto=6.0, abajo=False, dist=20.0):
    """Lanza un rayo vertical y devuelve (punto, normal) de la piel, o (None, None)."""
    if abajo:
        o = Vector((x, y, -z_alto))
        d = Vector((0, 0, 1))
    else:
        o = Vector((x, y, z_alto))
        d = Vector((0, 0, -1))
    p, n, _, _ = bvh.ray_cast(o, d, dist)
    if p is None:
        return None, None
    if n.dot(d) > 0:
        n = -n
    return p, n


def proyectar_hacia(bvh, origen, direccion, dist=10.0):
    p, n, _, _ = bvh.ray_cast(Vector(origen), Vector(direccion).normalized(), dist)
    if p is None:
        return None, None
    if n.dot(Vector(direccion)) > 0:
        n = -n
    return p, n


def escama_hex(geo, p, n, tam, alto, mat, giro=0.0, alargada=1.0, rota=False, aux=(0, 0, 0), dir_ref=None,
               hundir=0.05, borde=0.025, rnd=None):
    """Escama hexagonal con relieve real: cara superior en abanico (centro elevado = quilla suave) y faldón que
    se hunde en la piel. 18 triángulos. `rota`: un borde partido (escama dañada)."""
    t1, t2, n = marco(n, dir_ref or Vector((0, 1, 0)))
    centro = geo.v(p + n * alto, aux)
    arriba, abajo = [], []
    for k in range(6):
        a = giro + math.pi / 6 + k * math.pi / 3
        r = tam / 2
        off = t1 * (math.cos(a) * r * alargada) + t2 * (math.sin(a) * r)
        b = borde
        if rota and k in (1, 2):
            b = -0.01
            off = off * 0.72
        if rnd is not None:
            off = off * (1 + rnd.uniform(-0.05, 0.05))
        arriba.append(geo.v(p + off + n * b, aux))
        abajo.append(geo.v(p + off * 1.03 - n * hundir, aux))
    for k in range(6):
        j = (k + 1) % 6
        geo.cara((arriba[k], arriba[j], centro), mat)
        geo.cara((abajo[k], abajo[j], arriba[j], arriba[k]), mat)


def cinta(geo, puntos, normales, ancho, grueso, mat, aux_flag=1.0, separacion=0.006, cerrada=False, achaflan=0.25,
          lateral=None):
    """Correa de sección rectangular (con chaflán) que sigue la piel: `puntos` y `normales` son la línea central
    proyectada. aux = (u en studs a lo largo, v de 0 a 1 a lo ancho, aux_flag)."""
    n = len(puntos)
    anillos, auxs = [], []
    u = 0.0
    for i in range(n):
        p = Vector(puntos[i])
        nn = Vector(normales[i]).normalized()
        if i > 0:
            u += (p - Vector(puntos[i - 1])).length
        if lateral is not None:
            lat = Vector(lateral[i]).normalized()
        else:
            if cerrada:
                t = Vector(puntos[(i + 1) % n]) - Vector(puntos[(i - 1) % n])
            else:
                t = Vector(puntos[min(i + 1, n - 1)]) - Vector(puntos[max(i - 1, 0)])
            lat = t.normalized().cross(nn).normalized()
        h = ancho / 2
        c = achaflan * grueso
        base = p + nn * separacion
        # Sección: abajo-izq, arriba-izq (con chaflán), arriba-der, abajo-der.
        sec = [base - lat * h, base - lat * (h - c) + nn * grueso, base + lat * (h - c) + nn * grueso,
               base + lat * h]
        anillos.append(sec)
        auxs.append([(u, 0.0, aux_flag), (u, 0.08, aux_flag), (u, 0.92, aux_flag), (u, 1.0, aux_flag)])
    vs = []
    for k, a in enumerate(anillos):
        vs.append([geo.v(q, auxs[k][j]) for j, q in enumerate(a)])
    tramos = n if cerrada else n - 1
    for i in range(tramos):
        j = (i + 1) % n
        for s in range(4):
            s2 = (s + 1) % 4
            geo.cara((vs[i][s], vs[j][s], vs[j][s2], vs[i][s2]), mat)
    if not cerrada:
        geo.cara(list(reversed(vs[0])), mat)
        geo.cara(vs[-1], mat)
    return vs


def toro(geo, c, eje, R, r, mat, seg=12, lados=6, aux=(0, 0, 0), arco=math.tau, escala_r=(1, 1)):
    """Toro (o arco de toro) de radio mayor R y menor r alrededor de `eje` por el centro c."""
    c = Vector(c)
    t1, t2, n = marco(eje)
    cerrado = abs(arco - math.tau) < 1e-6
    nseg = seg if cerrado else seg + 1
    anillos = []
    for i in range(nseg):
        a = arco * i / seg
        d = t1 * math.cos(a) * R * escala_r[0] + t2 * math.sin(a) * R * escala_r[1]
        rad = d.normalized()
        anillo = []
        for k in range(lados):
            b = math.tau * k / lados
            anillo.append(c + d + rad * math.cos(b) * r + n * math.sin(b) * r)
        anillos.append(anillo)
    vs = [[geo.v(p, aux) for p in a] for a in anillos]
    tramos = nseg if cerrado else nseg - 1
    for i in range(tramos):
        j = (i + 1) % nseg
        for k in range(lados):
            k2 = (k + 1) % lados
            geo.cara((vs[i][k], vs[j][k], vs[j][k2], vs[i][k2]), mat)
    if not cerrado:
        geo.cara(list(reversed(vs[0])), mat)
        geo.cara(vs[-1], mat)


def cono(geo, base, direccion, largo, radio, mat, lados=6, curva=None, aux=(0, 0, 0), radio_punta=0.0, anillos=1,
         romo=False):
    """Cono (espina, diente, garra). `curva`: vector que dobla la punta (desplazamiento final). `romo`: punta
    redondeada (dientes de filtrador)."""
    base = Vector(base)
    d = Vector(direccion).normalized()
    t1, t2, _ = marco(d)
    filas = []
    for j in range(anillos + 1):
        s = j / (anillos + 1)
        centro = base + d * largo * s + (Vector(curva) * (s * s) if curva else Vector())
        rr = radio * (1 - s) + radio_punta * s
        if romo:
            rr = radio * math.sqrt(max(0.0, 1 - s ** 2.2)) * 0.9 + radio * 0.1 * (1 - s)
        filas.append([centro + (t1 * math.cos(math.tau * k / lados) + t2 * math.sin(math.tau * k / lados)) * rr
                      for k in range(lados)])
    punta = base + d * largo + (Vector(curva) if curva else Vector())
    geo.loft(filas, mat, auxs=[[aux] * lados for _ in filas], punta_fin=(punta, aux), tapar_inicio=True)


def caja(geo, c, ejes, tam, mat, aux=(0, 0, 0)):
    """Caja orientada: `ejes` = (ex, ey, ez) vectores unitarios; `tam` = medidas completas."""
    c = Vector(c)
    ex, ey, ez = (Vector(e) for e in ejes)
    hx, hy, hz = (t / 2 for t in tam)
    pts = []
    for sz in (-1, 1):
        for sy in (-1, 1):
            for sx in (-1, 1):
                pts.append(geo.v(c + ex * hx * sx + ey * hy * sy + ez * hz * sz, aux))
    caras = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    for f in caras:
        geo.cara([pts[i] for i in f], mat)


def disco(geo, c, normal, radio, mat, seg=16, anillos=2, abombado=0.0, aux_fn=None, preferido=Vector((0, 0, 1))):
    """Disco (con abombado opcional) orientado según `normal`, cara visible hacia la normal."""
    c = Vector(c)
    t1, t2, n = marco(normal, preferido)
    centro = geo.v(c + n * abombado, aux_fn(0, 0) if aux_fn else (0, 0, 0))
    filas = []
    for j in range(1, anillos + 1):
        rr = radio * j / anillos
        h = abombado * (1 - (j / anillos) ** 2)
        fila = []
        for k in range(seg):
            a = math.tau * k / seg
            p = c + (t1 * math.cos(a) + t2 * math.sin(a)) * rr + n * h
            fila.append(geo.v(p, aux_fn(j / anillos, k / seg) if aux_fn else (0, 0, 0)))
        filas.append(fila)
    for k in range(seg):
        k2 = (k + 1) % seg
        geo.cara((filas[0][k], filas[0][k2], centro), mat)
    for j in range(len(filas) - 1):
        for k in range(seg):
            k2 = (k + 1) % seg
            geo.cara((filas[j][k], filas[j][k2], filas[j + 1][k2], filas[j + 1][k]), mat)
    return filas


def rotar_a(v_desde, v_hacia):
    return Vector(v_desde).rotation_difference(Vector(v_hacia)).to_matrix()


def matriz(ejes):
    return Matrix([list(e) for e in ejes]).transposed()
