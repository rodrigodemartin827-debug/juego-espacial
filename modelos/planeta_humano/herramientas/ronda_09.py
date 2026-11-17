"""Ronda 9 · Naturaleza y terreno (modelos 81-90)."""

import math

from mathutils import Vector, noise

from geometria import arco_pts
from registro import modelo
from ronda_02 import _esparcir_hojas


def _tronco_corteza(m, eje, radios, mat="corteza", nervios=10, seg=10, grosor=0.16):
    """Tronco con corteza modelada: fuste + nervios en relieve que siguen el tronco girando un poco."""
    m.barrido(eje, radios, mat, seg=seg)
    R = m.rng
    for k in range(nervios):
        a = 2 * math.pi * k / nervios + R.uniform(-0.12, 0.12)
        giro = R.uniform(0.1, 0.3)
        pts, rs = [], []
        for i, (x, y, z) in enumerate(eje):
            r = radios[i] * 0.96
            pts.append((x + r * math.cos(a + giro * i), y + r * math.sin(a + giro * i), z + (0.02 if i == 0 else 0)))
            rs.append(radios[i] * grosor * (1.0 if i < len(eje) - 1 else 0.5))
        m.barrido(pts, rs, mat, seg=4)


def _raices(m, n, r0, r1, alto, mat="corteza", fase=0.3):
    for k in range(n):
        a = 2 * math.pi * k / n + fase
        m.barrido([(r0 * 0.6 * math.cos(a), r0 * 0.6 * math.sin(a), alto), (r0 * 1.2 * math.cos(a), r0 * 1.2 * math.sin(a), alto * 0.3),
                   (r1 * math.cos(a + 0.15), r1 * math.sin(a + 0.15), 0.03)], [r0 * 0.38, r0 * 0.27, r0 * 0.08], mat, seg=5)


@modelo(81, "naturaleza", "vegetacion", (6, 6, 14))
def arbol_roble_espacial(m):
    R = m.rng
    eje = [(0, 0, 0), (0.1, 0.05, 1.5), (-0.1, 0.1, 3.0), (0.12, -0.05, 4.6), (0.05, 0.0, 6.0)]
    _tronco_corteza(m, eje, [0.95, 0.78, 0.68, 0.6, 0.5], nervios=11, seg=10)
    _raices(m, 6, 0.9, 2.1, 1.1)
    m.ico((0.62, -0.3, 2.4), 0.26, "corteza", sub=1, esc=(0.8, 1, 1.3), ruido=0.25)           # nudo
    m.torno((0.66, -0.36, 2.4), [(0.12, 0), (0.1, 0.06), (0, 0.02)], "madera_oscura", seg=7, eje="x", rot=(0, 0, -28))
    # Ramas principales y secundarias
    copas = [((2.2, 0.4, 9.0), 2.2), ((-2.0, 1.2, 9.4), 2.1), ((-0.8, -2.1, 9.0), 2.0), ((1.0, 2.0, 10.2), 1.9),
             ((0.1, 0.0, 11.4), 2.4), ((-2.3, -0.9, 10.6), 1.6), ((1.9, -1.6, 10.4), 1.7)]
    copas = [((c[0] * 0.66, c[1] * 0.66, c[2]), r * 0.74) for c, r in copas]
    for i, (c, r) in enumerate(copas):
        mid = (c[0] * 0.4 + 0.05, c[1] * 0.4, 6.0 + (c[2] - 6.0) * 0.5)
        m.barrido([(0.05, 0.0, 5.6), mid, (c[0], c[1], c[2] - r * 0.3)], [0.38 - 0.02 * i, 0.24, 0.1], "corteza", seg=6)
        m.ico(c, r, "hoja", sub=2, esc=(1, 1, 0.82), ruido=0.26, frec=1.4, semilla=i * 2.9)
    def punto(u, v):
        c, r = copas[int(u * len(copas)) % len(copas)]
        a = 2 * math.pi * v
        e = math.radians(R.uniform(-30, 85))
        return (c[0] + r * math.cos(a) * math.cos(e), c[1] + r * math.sin(a) * math.cos(e), c[2] + r * 0.82 * math.sin(e)), a
    _esparcir_hojas(m, 95, punto, 0.7, 0.36, "hoja_clara", subir=22)
    _esparcir_hojas(m, 55, punto, 0.8, 0.4, "hoja2", subir=18)
    _esparcir_hojas(m, 34, punto, 0.75, 0.36, "hoja_cyan", subir=25)
    _esparcir_hojas(m, 22, punto, 0.6, 0.26, "neon", subir=30)                                # bioluminiscentes


@modelo(82, "naturaleza", "vegetacion", (3, 3, 16))
def arbol_pino_espacial(m):
    R = m.rng
    eje = [(0, 0, 0), (0.03, 0.02, 4.0), (-0.02, 0.0, 9.0), (0.0, 0.0, 15.2)]
    _tronco_corteza(m, eje, [0.42, 0.32, 0.2, 0.03], mat="corteza", nervios=7, seg=8, grosor=0.2)
    _raices(m, 5, 0.42, 0.95, 0.5)
    # Pisos de ramas escalonados: cada rama es un brazo con acículas en abanico y punta luminosa
    pisos = 11
    for i in range(pisos):
        t = i / (pisos - 1)
        z = 3.2 + 11.3 * t
        largo = 1.05 * (1 - t) ** 0.8 + 0.2
        n = 7 if i < 7 else 5
        for k in range(n):
            a = 2 * math.pi * k / n + i * 0.55
            ca, sa = math.cos(a), math.sin(a)
            cae = -0.28 * largo
            m.barrido([(0.1 * ca, 0.1 * sa, z), (largo * 0.55 * ca, largo * 0.55 * sa, z + cae * 0.3),
                       (largo * ca, largo * sa, z + cae)], [0.07, 0.05, 0.02], "corteza", seg=4)
            # Masa de acículas: cuña aplastada con grosor
            for j, f in enumerate((0.45, 0.8)):
                px, py, pz = largo * f * ca, largo * f * sa, z + cae * f * f + 0.02
                m.hoja((px, py, pz), largo * 0.55, largo * 0.6, "hoja2" if (i + k + j) % 3 else "hoja_azul",
                       rot=(0, 14, math.degrees(a)), grosor=0.11)
            if (i + k) % 4 == 0:
                m.esfera((largo * 1.02 * ca, largo * 1.02 * sa, z + cae - 0.02), 0.06, "neon", seg=5, anillos=3)
    m.torno((0, 0, 14.6), [(0.34, 0), (0.2, 0.7), (0.0, 1.45)], "hoja2", seg=7)
    # Piñas colgantes
    for k in range(6):
        a = k * 1.9
        m.torno((0.8 * math.cos(a), 0.8 * math.sin(a), 5.2 + 0.9 * k), [(0.0, 0), (0.09, 0.08), (0.07, 0.24), (0, 0.3)],
                "madera_oscura", seg=6)


@modelo(83, "naturaleza", "vegetacion", (5, 5, 10))
def arbol_sauce_espacial(m):
    R = m.rng
    eje = [(0, 0, 0), (0.15, 0.0, 1.4), (-0.1, 0.12, 2.9), (0.2, -0.05, 4.3), (0.1, 0.0, 5.4)]
    _tronco_corteza(m, eje, [0.75, 0.6, 0.52, 0.46, 0.38], nervios=7, seg=8)
    _raices(m, 6, 0.72, 1.6, 0.8)
    # Brazos que suben y se abren en bóveda
    brazos = 9
    puntas = []
    for k in range(brazos):
        a = 2 * math.pi * k / brazos + 0.2
        ca, sa = math.cos(a), math.sin(a)
        alto = 8.6 + 0.9 * math.sin(k * 2.1)
        pts = [(0.1, 0, 5.2), (0.8 * ca, 0.8 * sa, 7.2), (1.5 * ca, 1.5 * sa, alto), (2.05 * ca, 2.05 * sa, alto - 0.3)]
        m.barrido(pts, [0.24, 0.15, 0.09, 0.05], "corteza", seg=5)
        puntas.append((pts[2], a))
        puntas.append((pts[3], a))
        puntas.append(((1.15 * ca, 1.15 * sa, 8.2), a + 0.3))
    m.ico((0.05, 0, 8.9), 1.9, "hoja2", sub=2, esc=(1, 1, 0.55), ruido=0.22, semilla=4.1)       # bóveda de la copa
    # Cortinas colgantes: tallo fino con hojas alargadas y la punta luminosa
    for i, (p, a) in enumerate(puntas):
        for j in range(2 if i % 5 == 0 else 1):
            ang = a + (j - 0.5) * 0.5 + R.uniform(-0.15, 0.15)
            ex = 0.25 + 0.3 * j
            x0, y0, z0 = p[0] + ex * math.cos(ang) * 0.3, p[1] + ex * math.sin(ang) * 0.3, p[2]
            largo = R.uniform(4.2, 6.6)
            n = 4
            pts = []
            for q in range(n + 1):
                t = q / n
                pts.append((x0 + ex * math.cos(ang) * t + 0.12 * math.sin(t * 3 + i), y0 + ex * math.sin(ang) * t,
                            z0 - largo * t))
            m.barrido(pts, [0.035, 0.03, 0.026, 0.02, 0.012], "hoja2", seg=3)
            for q in range(1, n + 1):
                px, py, pz = pts[q]
                lum = q >= n - 1
                for s in (-1, 1):
                    m.hoja((px, py, pz + 0.2), 0.62, 0.17, "neon" if lum else ("hoja_azul" if (i + q) % 2 else "hoja_clara"),
                           rot=(0, 62, math.degrees(ang) + s * 70))


@modelo(84, "naturaleza", "vegetacion", (3, 3, 12))
def arbol_palmera_alien(m):
    R = m.rng
    # Tronco curvado con anillos marcados
    eje = []
    for i in range(13):
        t = i / 12
        eje.append((0.5 * math.sin(t * 1.5) - 0.2, 0.15 * math.sin(t * 2.6), 9.9 * t))
    radios = [0.48 - 0.2 * (i / 12) + (0.08 if i == 0 else 0) for i in range(13)]
    m.barrido(eje, radios, "corteza_palma", seg=10)
    for i in range(1, 12):
        x, y, z = eje[i]
        d = (Vector(eje[i + 1]) - Vector(eje[i - 1])).normalized()
        rx = math.degrees(math.atan2(-d.y, d.z))
        ry = math.degrees(math.atan2(d.x, d.z))
        m.tubo((x, y, z), radios[i] + 0.06, 0.2, 0.09, "corteza_palma" if i % 3 else "hoja_azul", seg=10, rot=(rx, ry, 0))
    m.torno((eje[0][0], eje[0][1], 0), [(0.75, 0), (0.6, 0.25), (0.5, 0.6), (0, 0.6)], "corteza_palma", seg=10)
    cx, cy, cz = eje[-1]
    # Corazón luminoso y frutos
    m.esfera((cx, cy, cz + 0.15), 0.42, "hoja_azul", seg=10, anillos=6, esc=(1, 1, 0.9))
    m.esfera((cx, cy, cz + 0.5), 0.2, "neon", seg=8, anillos=5)
    for k in range(5):
        a = k * 1.26
        m.esfera((cx + 0.4 * math.cos(a), cy + 0.4 * math.sin(a), cz - 0.25), 0.17, m.color("#B455E0", 0.35), seg=7, anillos=5)
    # Hojas en abanico: peciolo arqueado y abanico de folíolos con grosor, con los nervios brillantes
    n = 9
    for k in range(n):
        a = 2 * math.pi * k / n + 0.2
        ca, sa = math.cos(a), math.sin(a)
        sube = 1.9 if k % 2 == 0 else 1.1
        alc = 0.85 if k % 2 == 0 else 0.7
        p0 = (cx + 0.2 * ca, cy + 0.2 * sa, cz + 0.2)
        p1 = (cx + alc * 0.55 * ca, cy + alc * 0.55 * sa, cz + sube * 0.75)
        p2 = (cx + alc * ca, cy + alc * sa, cz + sube * 0.72)
        m.barrido([p0, p1, p2], [0.08, 0.06, 0.04], "hoja2", seg=5)
        incl = -18 if k % 2 == 0 else 22
        for j in range(7):
            b = (j - 3) * 0.3
            m.hoja(p2, 0.95 - 0.08 * abs(j - 3), 0.3, "hoja_cyan" if j % 2 == 0 else "hoja_azul",
                   rot=(0, incl + 10 * abs(j - 3), math.degrees(a + b)), grosor=0.07)
        m.hoja(p2, 1.0, 0.1, "neon", rot=(0, incl - 2, math.degrees(a)), grosor=0.06)       # nervio central luminoso
    # Hierba en la base
    for k in range(10):
        a = k * 0.63
        m.hoja((eje[0][0] + 0.7 * math.cos(a), 0.7 * math.sin(a), 0.02), R.uniform(0.6, 1.0), 0.16, "hoja_clara",
               rot=(0, -R.uniform(45, 70), math.degrees(a)))


def _musgo(m, centros, n=18, mat="musgo"):
    R = m.rng
    for i in range(n):
        c, t = centros[i % len(centros)]
        a = R.uniform(0, 6.28)
        e = math.radians(R.uniform(35, 85))
        p = (c[0] + t[0] * 0.46 * math.cos(a) * math.cos(e), c[1] + t[1] * 0.46 * math.sin(a) * math.cos(e),
             c[2] + t[2] * 0.46 * math.sin(e))
        s = R.uniform(0.35, 0.75) * min(t) * 0.5
        m.ico(p, s, mat, sub=1, esc=(1, 1, 0.42), ruido=0.3, semilla=i * 1.7)


@modelo(85, "naturaleza", "vegetacion", (4, 3, 3))
def roca_grande(m):
    # Roca irregular esculpida (ruido a dos escalas), con estratos, lascas al pie y manchas de musgo en relieve
    import bmesh
    dst, idx = m._dest("piedra", None)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    for v in bm.verts:
        p = v.co.copy()
        n1 = noise.noise(p * 1.1 + Vector((3.1, 0.7, 1.9)))
        n2 = noise.noise(p * 3.2 + Vector((7.0, 2.0, 5.0)))
        f = 1.0 + 0.3 * n1 + 0.1 * n2
        v.co = Vector((p.x * 1.95 * f, p.y * 1.45 * f, max(-0.25, p.z * 1.45 * f + 0.2 * n1)))
        v.co.z = v.co.z * (1.05 if v.co.z > 0 else 1.0) + 1.25 if False else v.co.z
    for v in bm.verts:                                                                 # estratos: escalones suaves
        z = v.co.z
        v.co.z = z + 0.06 * math.sin(z * 9.0)
        if v.co.z < -0.2:
            v.co.z = -0.2
    m._fin(bm, dst, idx, m._M((0, 0, 1.28)))
    m.roca((1.5, -0.9, 0.42), (1.3, 1.1, 0.95), "piedra_oscura", semilla=2.2, sub=2, ruido=0.32)
    m.roca((-1.55, 0.7, 0.36), (1.0, 0.9, 0.8), "piedra", semilla=5.1, sub=2, ruido=0.3)
    for i, (x, y, s) in enumerate(((1.0, 1.2, 0.5), (-0.6, -1.25, 0.42), (-1.7, -0.6, 0.36), (0.3, -1.4, 0.3))):
        m.roca((x, y, s * 0.3), (s, s * 0.8, s * 0.6), "piedra_oscura" if i % 2 else "piedra", semilla=i * 3.7, sub=1)
    _musgo(m, [((0, 0, 1.3), (3.6, 2.7, 3.2)), ((-1.55, 0.7, 0.36), (1.0, 0.9, 0.8))], n=20)
    R = m.rng
    for k in range(9):
        a = k * 0.7
        m.hoja((1.9 * math.cos(a), 1.35 * math.sin(a), 0.02), R.uniform(0.4, 0.7), 0.13, "hoja", rot=(0, -R.uniform(50, 75),
               math.degrees(a)))


@modelo(86, "naturaleza", "vegetacion", (6, 4, 5))
def roca_formacion(m):
    # Tres rocas agrupadas: un monolito inclinado, una losa apoyada y un bolo; con lascas, musgo y un cristal
    import bmesh
    def monolito(c, t, semilla, rot, mat):
        dst, idx = m._dest(mat, None)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=3, radius=0.5)
        for v in bm.verts:
            p = v.co.copy()
            n1 = noise.noise(p * 2.4 + Vector((semilla, semilla * 0.3, 1.0)))
            n2 = noise.noise(p * 6.0 + Vector((1.0, semilla, semilla)))
            f = 1.0 + 0.32 * n1 + 0.1 * n2
            # aristas más marcadas: empuja hacia un prisma
            q = Vector((p.x, p.y, p.z)) * f
            q.x = math.copysign(abs(q.x) ** 0.8, q.x) * 0.85
            q.y = math.copysign(abs(q.y) ** 0.8, q.y) * 0.85
            v.co = q
        m._fin(bm, dst, idx, m._M(c, rot, "z", t))
    monolito((-0.9, 0.2, 2.3), (2.6, 2.3, 5.4), 3.3, (6, -9, 20), "piedra")
    monolito((1.4, -0.3, 1.5), (2.4, 2.0, 3.6), 8.1, (-8, 14, -30), "piedra_oscura")
    monolito((0.4, 1.0, 0.9), (2.9, 1.7, 2.0), 12.7, (4, 5, 70), "piedra")
    m.bloque((-1.6, -0.6, 0), (2.0, 1.2, 0.3), "piedra_oscura")
    for i, (x, y, s) in enumerate(((-2.4, -0.9, 0.7), (2.5, 0.8, 0.6), (0.3, -1.6, 0.55), (-1.6, 1.5, 0.45), (2.0, -1.4, 0.4))):
        m.roca((x, y, s * 0.3), (s, s * 0.85, s * 0.6), "piedra" if i % 2 else "piedra_oscura", semilla=i * 2.3, sub=1)
    _musgo(m, [((-0.9, 0.2, 2.5), (2.2, 2.0, 5.0)), ((1.4, -0.3, 1.6), (2.0, 1.7, 3.2)), ((0.4, 1.0, 0.9), (2.6, 1.5, 1.8))],
           n=24)
    for (x, y, h, a) in ((0.1, -1.2, 0.9, 10), (0.4, -1.35, 0.55, -18)):
        m.torno((x, y, 0.05), [(0.1, 0), (0.15, 0.12), (0.1, h * 0.8), (0, h)], "neon", seg=5, rot=(a, a * 0.5, 0))
    R = m.rng
    for k in range(10):
        a = k * 0.63
        m.hoja((2.6 * math.cos(a), 1.7 * math.sin(a), 0.02), R.uniform(0.5, 0.8), 0.14, "hoja", rot=(0, -R.uniform(50, 75),
               math.degrees(a)))


def _superficie_agua(m, x0, x1, y0, y1, nx, ny, z, amp, grosor, mat="agua", fase=0.0, p=None, fn=None):
    """Lámina de agua con ondas modeladas en la cara superior y grosor real (sólido cerrado)."""
    import bmesh
    dst, idx = m._dest(mat, p)
    bm = bmesh.new()
    def alt(x, y):
        if fn:
            return fn(x, y)
        return z + amp * (math.sin(x * 2.2 + fase) * math.cos(y * 1.7 + fase * 0.5) * 0.6 + math.sin(x * 4.6 - y * 1.1) * 0.4)
    sup = [[bm.verts.new((x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny,
                          alt(x0 + (x1 - x0) * i / nx, y0 + (y1 - y0) * j / ny))) for j in range(ny + 1)] for i in range(nx + 1)]
    inf = [[bm.verts.new((v.co.x, v.co.y, min(v.co.z, z) - grosor)) for v in fila] for fila in sup]
    for i in range(nx):
        for j in range(ny):
            bm.faces.new((sup[i][j], sup[i + 1][j], sup[i + 1][j + 1], sup[i][j + 1]))
            bm.faces.new((inf[i][j], inf[i][j + 1], inf[i + 1][j + 1], inf[i + 1][j]))
    for i in range(nx):
        bm.faces.new((sup[i][0], inf[i][0], inf[i + 1][0], sup[i + 1][0]))
        bm.faces.new((sup[i][ny], sup[i + 1][ny], inf[i + 1][ny], inf[i][ny]))
    for j in range(ny):
        bm.faces.new((sup[0][j], sup[0][j + 1], inf[0][j + 1], inf[0][j]))
        bm.faces.new((sup[nx][j], inf[nx][j], inf[nx][j + 1], sup[nx][j + 1]))
    m._fin(bm, dst, idx, None)


@modelo(87, "naturaleza", "vegetacion", (8, 4, 0.5))
def rio_segmento(m):
    R = m.rng
    # Lecho de tierra con cauce, agua semitransparente con ondas modeladas y orillas de piedras 3D
    m.caja((0, 0, 0.05), (8.0, 4.0, 0.1), "tierra")
    for s in (-1, 1):
        m.prisma([(s * 2.0, 0.1), (s * 1.25, 0.1), (s * 1.45, 0.3), (s * 2.0, 0.34)], -4.0, 4.0, "tierra", "yz")
        m.prisma([(s * 2.0, 0.34), (s * 1.5, 0.3), (s * 1.62, 0.36), (s * 2.0, 0.4)], -4.0, 4.0, "cesped", "yz")
    _superficie_agua(m, -4.0, 4.0, -1.42, 1.42, 26, 9, 0.27, 0.045, 0.14)
    # Piedras de las dos orillas (redondeadas, de tamaños variados) y algunas dentro del agua
    for s in (-1, 1):
        x = -3.9
        i = 0
        while x < 3.9:
            w = R.uniform(0.35, 0.7)
            m.roca((x + w / 2, s * (1.42 + R.uniform(-0.06, 0.12)), 0.3 + R.uniform(-0.02, 0.05)),
                   (w, R.uniform(0.36, 0.6), R.uniform(0.26, 0.42)), ("piedra", "piedra_clara", "piedra_oscura")[i % 3],
                   semilla=x * 3 + s, sub=1, ruido=0.22, rot=(0, 0, R.uniform(0, 90)))
            x += w * 0.92
            i += 1
    for (x, y, s) in ((-2.2, 0.4, 0.5), (0.8, -0.5, 0.62), (2.9, 0.3, 0.4), (-0.6, 0.7, 0.3)):
        m.roca((x, y, 0.2), (s, s * 0.8, s * 0.6), "piedra_oscura", semilla=x, sub=2, ruido=0.2)
        m.torno((x, y, 0.292), [(s * 0.62, 0), (s * 0.7, 0.008), (s * 0.62, 0.016)], "plastico", seg=10)   # espuma
    # Juncos y hierba en las orillas
    for i in range(16):
        s = 1 if i % 2 else -1
        x = R.uniform(-3.8, 3.8)
        for k in range(3):
            m.brizna((x + 0.08 * k, s * R.uniform(1.6, 1.95), 0.37), R.uniform(0.1, 0.13), 0.035, "hoja",
                     inclin=(R.uniform(-0.04, 0.04), R.uniform(-0.04, 0.04)), giro=k * 1.0)


@modelo(88, "naturaleza", "vegetacion", (4, 2, 6))
def cascada_pequena(m):
    R = m.rng
    # Pared de roca escalonada, cortina de agua con grosor que cae en dos saltos, poza con ondas y espuma
    m.bloque((-1.7, 0.1, 0), (1.7, 1.0, 4.9), "piedra_oscura")
    rocas = [((-1.3, 0.35, 1.2), (1.6, 1.3, 2.6)), ((1.3, 0.4, 1.4), (1.6, 1.3, 3.0)), ((-1.2, 0.45, 3.6), (1.7, 1.2, 2.6)),
             ((1.25, 0.5, 4.0), (1.6, 1.1, 2.4)), ((0, 0.75, 5.0), (3.4, 0.9, 1.6)), ((0, 0.6, 2.4), (1.6, 1.0, 1.2)),
             ((-1.5, -0.35, 0.5), (1.0, 1.0, 1.0)), ((1.55, -0.4, 0.45), (0.9, 0.9, 0.9))]
    for i, (c, t) in enumerate(rocas):
        m.roca(c, t, "piedra" if i % 2 else "piedra_oscura", semilla=i * 2.6, sub=2, ruido=0.3)
    # Salto superior, repisa y salto inferior (cortinas curvas con grosor)
    def cortina(x0, x1, pts_yz, mat="agua"):
        n = 6
        for i in range(n):
            xa, xb = x0 + (x1 - x0) * i / n, x0 + (x1 - x0) * (i + 1) / n
            g = 0.1 + 0.04 * math.sin(i * 2.1)
            perfil = [(y - g * 0.5, z) for y, z in pts_yz] + [(y + g * 0.5, z) for y, z in reversed(pts_yz)]
            m.prisma(perfil, xa, xb, mat, "yz", c=(0, 0.03 * math.sin(i * 1.7), 0))
    cortina(-0.55, 0.55, [(0.55, 5.55), (0.3, 5.5), (0.12, 5.2), (0.05, 4.4), (0.0, 3.1)])
    cortina(-0.75, 0.75, [(0.1, 3.0), (-0.12, 2.95), (-0.32, 2.6), (-0.4, 1.6), (-0.44, 0.34)])
    m.caja((0, 0.45, 5.52), (1.3, 0.8, 0.12), "agua")
    m.caja((0, 0.1, 3.0), (1.7, 0.7, 0.12), "agua")
    # Poza: cuenco de piedras y lámina de agua con ondas concéntricas
    def onda(x, y):
        d = math.hypot(x, y + 0.45)
        return 0.3 + 0.05 * math.cos(d * 7.0) * max(0.0, 1 - d / 1.9)
    _superficie_agua(m, -1.7, 1.7, -1.0, 0.25, 12, 6, 0.3, 0, 0.2, fn=onda)
    m.bloque((-1.9, -1.05, 0), (1.9, 0.3, 0.1), "tierra")
    x = -1.9
    i = 0
    while x < 1.9:
        w = R.uniform(0.4, 0.62)
        m.roca((x + w / 2, -1.0 + R.uniform(-0.04, 0.06), 0.24), (w, 0.5, 0.42), ("piedra", "piedra_clara")[i % 2],
               semilla=x * 5, sub=1, ruido=0.22)
        x += w * 0.9
        i += 1
    # Espuma al pie de cada salto y gotas en suspensión
    for (cx, cy, cz, n) in ((0, -0.45, 0.36, 7), (0, 0.02, 3.1, 4)):
        for k in range(n):
            a = k * 2.0
            m.ico((cx + 0.55 * math.cos(a) * (0.4 + 0.1 * (k % 3)), cy + 0.2 * math.sin(a), cz), 0.16 + 0.03 * (k % 3),
                  "plastico", sub=1, esc=(1, 1, 0.6), ruido=0.2, semilla=k, p="espuma")
    m.anclaje("niebla_pie", (0, -0.45, 0.5))
    m.anclaje("caida_arriba", (0, 0.3, 5.5))
    # Musgo, helechos y un cristal luminoso junto a la poza
    _musgo(m, [((-1.2, 0.45, 3.6), (1.7, 1.2, 2.6)), ((1.3, 0.4, 1.4), (1.6, 1.3, 3.0)), ((0, 0.75, 5.0), (3.4, 0.9, 1.6))],
           n=14)
    for (x, y, z) in ((-1.35, -0.2, 1.0), (1.4, -0.25, 0.9), (-1.0, 0.0, 2.6)):
        for k in range(6):
            m.hoja((x, y, z), R.uniform(0.5, 0.75), 0.17, "hoja" if k % 2 else "hoja_clara",
                   rot=(0, -R.uniform(20, 55), -90 + (k - 2.5) * 34))
    m.torno((1.5, -0.75, 0.3), [(0.08, 0), (0.12, 0.1), (0.08, 0.5), (0, 0.62)], "neon", seg=5, rot=(8, -12, 0))


@modelo(89, "naturaleza", "edificio_mediano", (8, 4, 3))
def puente_rio_piedra(m):
    R = m.rng
    # Arco de dovelas, tímpanos de mampostería con sillares en relieve, calzada empedrada y pretil bajo
    def zs(x):
        return 1.55 + 0.55 * (1 - (x / 4.0) ** 2)                                   # rasante de la calzada
    xs = [-4 + 0.8 * i for i in range(11)]
    intr = [(2.3 * math.cos(math.radians(a)), 1.5 * math.sin(math.radians(a))) for a in range(0, 181, 15)]
    for sy in (-1, 1):
        cara = [(4.0, 0), (4.0, zs(4.0))] + [(x, zs(x)) for x in reversed(xs[1:-1])] + [(-4.0, zs(-4.0)), (-4.0, 0), (-2.3, 0)] \
               + list(reversed(intr[1:-1])) + [(2.3, 0)]
        m.prisma(cara, sy * 1.55, sy * 2.0, "piedra", "xz")
        # dovelas del arco, una a una
        for k in range(12):
            a0, a1 = math.radians(15 * k + 1), math.radians(15 * (k + 1) - 1)
            d = [(2.3 * math.cos(a0), 1.5 * math.sin(a0)), (2.3 * math.cos(a1), 1.5 * math.sin(a1)),
                 (2.75 * math.cos(a1), 1.85 * math.sin(a1)), (2.75 * math.cos(a0), 1.85 * math.sin(a0))]
            m.prisma(d, sy * 2.0 - 0.02, sy * 2.0 + 0.06, "piedra_clara" if k % 2 else "piedra", "xz") if sy > 0 else \
                m.prisma(d, sy * 2.0 - 0.06, sy * 2.0 + 0.02, "piedra_clara" if k % 2 else "piedra", "xz")
        # sillares sueltos en relieve en los tímpanos
        for i in range(12):
            x = R.uniform(2.6, 3.7) * (1 if i % 2 else -1)
            z = R.uniform(0.2, 1.3)
            m.caja((x, sy * 2.03, z), (R.uniform(0.4, 0.7), 0.08, R.uniform(0.22, 0.34)),
                   ("piedra_oscura", "piedra_clara", "piedra")[i % 3], bisel=0.03)
    # Bóveda (intradós) y relleno bajo la calzada
    boveda = intr + [(2.5 * math.cos(math.radians(a)), 1.68 * math.sin(math.radians(a))) for a in range(180, -1, -15)]
    m.prisma(boveda, -1.55, 1.55, "piedra_oscura", "xz")
    for sx in (-1, 1):
        m.prisma([(sx * 4.0, 0), (sx * 2.35, 0), (sx * 2.35, 1.0), (sx * 1.4, 1.6), (sx * 1.4, zs(1.4) - 0.1),
                  (sx * 4.0, zs(4.0) - 0.1)], -1.55, 1.55, "piedra_oscura", "xz")
    m.prisma([(-1.45, 1.55), (1.45, 1.55), (1.45, zs(1.4) - 0.1), (-1.45, zs(1.4) - 0.1)], -1.55, 1.55, "piedra_oscura", "xz")
    # Calzada: losas individuales siguiendo la rasante
    for i in range(10):
        x0, x1 = xs[i], xs[i + 1]
        xm = (x0 + x1) / 2
        ang = -math.degrees(math.atan2(zs(x1) - zs(x0), 0.8))
        for j in range(3):
            y = -1.0 + 1.0 * j
            m.caja((xm, y + (0.12 if i % 2 else -0.12) * 0, (zs(x0) + zs(x1)) / 2 - 0.03), (0.76, 0.96, 0.14),
                   ("piedra_clara", "piedra", "piedra_clara")[(i + j) % 3], rot=(0, ang, 0), bisel=0.03)
    # Pretil bajo con albardilla y pilastras en los extremos
    for sy in (-1, 1):
        for i in range(10):
            x0, x1 = xs[i], xs[i + 1]
            ang = -math.degrees(math.atan2(zs(x1) - zs(x0), 0.8))
            m.caja(((x0 + x1) / 2, sy * 1.78, (zs(x0) + zs(x1)) / 2 + 0.28), (0.82, 0.4, 0.56), "piedra", rot=(0, ang, 0))
            m.caja(((x0 + x1) / 2, sy * 1.78, (zs(x0) + zs(x1)) / 2 + 0.6), (0.84, 0.5, 0.1), "piedra_clara", rot=(0, ang, 0),
                   bisel=0.02)
        for sx in (-1, 1):
            m.caja((sx * 3.85, sy * 1.78, zs(4) + 0.4), (0.5, 0.56, 1.0), "piedra_clara", bisel=0.04)
            m.torno((sx * 3.85, sy * 1.78, zs(4) + 0.9), [(0.3, 0), (0.2, 0.1), (0.14, 0.16)], "piedra", seg=4, rot=(0, 0, 45))
            m.esfera((sx * 3.85, sy * 1.78, zs(4) + 1.18), 0.13, "neon", seg=8, anillos=5)
    _musgo(m, [((-3.2, 2.0, 0.5), (1.6, 0.3, 1.2)), ((3.2, -2.0, 0.5), (1.6, 0.3, 1.2)), ((0, 2.0, 1.7), (2.0, 0.3, 0.5))], n=12)


@modelo(90, "naturaleza", "vegetacion", (0.5, 0.5, 1))
def flor_luminosa_a(m):
    # Flor bioluminiscente abierta: tallo curvo, dos hojas, cáliz, ocho pétalos 3D en dos coronas y centro brillante
    m.barrido([(0, 0, 0), (0.03, 0.0, 0.3), (-0.02, 0.01, 0.6), (0, 0, 0.82)], [0.03, 0.025, 0.022, 0.02], "hoja2", seg=6)
    m.hoja((0.02, 0, 0.22), 0.28, 0.12, "hoja", rot=(0, -40, 30))
    m.hoja((0.0, 0.0, 0.4), 0.24, 0.1, "hoja_clara", rot=(0, -35, 200))
    m.torno((0, 0, 0.8), [(0.02, 0), (0.06, 0.03), (0.05, 0.06), (0, 0.05)], "hoja2", seg=8)
    for k in range(5):
        m.hoja((0, 0, 0.82), 0.1, 0.05, "hoja", rot=(0, 25, 72 * k))
    petalo = "hoja_cyan"
    for k in range(8):
        m.hoja((0, 0, 0.86), 0.24, 0.12, petalo, rot=(0, -22, 45 * k), grosor=0.02)
    for k in range(6):
        m.hoja((0, 0, 0.88), 0.16, 0.085, "neon", rot=(0, -50, 60 * k + 30), grosor=0.018, p="petalos_neon")
    m.esfera((0, 0, 0.9), 0.05, "neon", seg=8, anillos=5, esc=(1, 1, 0.8), p="centro_neon")
    for k in range(5):
        a = math.radians(72 * k)
        m.barrido([(0.02 * math.cos(a), 0.02 * math.sin(a), 0.92), (0.06 * math.cos(a), 0.06 * math.sin(a), 0.99)], 0.006,
                  "hoja_clara", seg=3)
        m.esfera((0.06 * math.cos(a), 0.06 * math.sin(a), 0.992), 0.014, "neon_blanco", seg=5, anillos=3)
    for k in range(5):
        a = k * 1.3
        m.brizna((0.08 * math.cos(a), 0.08 * math.sin(a), 0), 0.14, 0.02, "hoja", inclin=(0.05 * math.cos(a), 0.05 * math.sin(a)),
                 giro=a)
