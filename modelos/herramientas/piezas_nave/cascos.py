"""
Cascos / fuselajes: el centro de la nave. Un loft de secciones a lo largo de Y (morro en -Y) con los acoples de
salida montados en pilones y almohadillas planas, y el detalle propio de cada familia y tier.

Parámetros (dict `p`):
  L, W, H          largo, ancho y alto (studs)
  estaciones       [(t, ancho, alto, z centro, cuadratura[, achate panza])], t de 0 (morro) a 1 (popa),
                   ancho y alto en fracción de W y H, z en fracción de H
  lados, anillos   resolución del loft
  giro             torsión total (radianes) a lo largo del casco (prototipo)
  laterales        [(t, z)] posiciones de los pares de acoples laterales (z en fracción de H)
  traseros         [(x, z)] acoples de motor en la popa (fracción de W/H de la sección de popa)
  superiores       [(t, nombre)] acoples superiores (cabina, torretas, aleta)
  inferiores       [t] acoples inferiores
  frontal          True/False
  extras           lista de detalles: "tomas", "tuberias", "compuertas", "bahia", "blindaje", "neon_lados",
                   "neon_lomo", "aletas", "puente", "cubierta", "costillas", "cristales", "anillos_flotantes",
                   "quilla", "antena", "rejillas", "facetas_oro", "pinchos", "vainas"
"""

import math

from .geo import V, Matrix, seccion

CON_LAT = 1.6


class Superficie:
    """Muestrea el casco en (t, ángulo): sirve para colocar pilones, franjas de neón y detalles encima."""

    def __init__(self, p):
        self.p = p
        self.L, self.W, self.H = p["L"], p["W"], p["H"]
        self.est = p["estaciones"]

    def datos(self, t):
        e = self.est
        t = min(max(t, 0.0), 1.0)
        for i in range(len(e) - 1):
            if e[i][0] <= t <= e[i + 1][0]:
                a, b = e[i], e[i + 1]
                k = (t - a[0]) / max(b[0] - a[0], 1e-6)
                k = k * k * (3 - 2 * k) if self.p.get("suave", True) else k
                vals = [a[j] + (b[j] - a[j]) * k for j in range(1, 5)]
                ach_a = a[5] if len(a) > 5 else 1.0
                ach_b = b[5] if len(b) > 5 else 1.0
                vals.append(ach_a + (ach_b - ach_a) * k)
                return vals
        last = e[-1]
        return [last[1], last[2], last[3], last[4], last[5] if len(last) > 5 else 1.0]

    def y(self, t):
        return -self.L / 2 + t * self.L

    def anillo(self, t, n):
        w, h, zc, cu, ach = self.datos(t)
        giro = self.p.get("giro", 0.0) * t
        return seccion(self.y(t), max(w * self.W, 0.02), max(h * self.H, 0.02), zc * self.H, n, cu, giro=giro,
                       achate_inf=ach)

    def punto(self, t, ang):
        """Punto de la superficie en el ángulo `ang` (0 = izquierda +X, pi/2 = arriba)."""
        w, h, zc, cu, ach = self.datos(t)
        ca, sa = math.cos(ang), math.sin(ang)
        x = math.copysign(abs(ca) ** (2 / cu), ca) * w * self.W / 2
        z = math.copysign(abs(sa) ** (2 / cu), sa) * h * self.H / 2
        if z < 0:
            z *= ach
        return V((x, self.y(t), zc * self.H + z))

    def normal(self, t, ang):
        e = 0.01
        p = self.punto(t, ang)
        du = self.punto(t, ang + e) - self.punto(t, ang - e)
        dv = self.punto(t + e, ang) - self.punto(t - e, ang)
        n = du.cross(dv)
        if n.length < 1e-6:
            return V((math.cos(ang), 0, math.sin(ang)))
        n.normalize()
        rad = V((p.x, 0, p.z - self.datos(t)[2] * self.H))
        if n.dot(rad) < 0:
            n = -n
        return n

    def ancho_en(self, t, z):
        """Semiancho (x) de la sección en t a la altura z (para apoyar pilones en el costado)."""
        w, h, zc, cu, ach = self.datos(t)
        mejor = 0.0
        for k in range(64):
            a = -math.pi / 2 + math.pi * k / 63
            pt = self.punto(t, a)
            if abs(pt.z - z) < h * self.H * 0.08:
                mejor = max(mejor, pt.x)
        return mejor if mejor > 0 else w * self.W / 2

    def arriba_en(self, t, x=0.0):
        w, h, zc, cu, ach = self.datos(t)
        return zc * self.H + h * self.H / 2

    def abajo_en(self, t):
        w, h, zc, cu, ach = self.datos(t)
        return zc * self.H - h * self.H / 2 * ach


def _ts(est, anillos):
    """Valores de t para los anillos: las estaciones y repartidos entre medias, más densos en el morro."""
    ts = set(e[0] for e in est)
    for k in range(anillos + 1):
        u = k / anillos
        ts.add(round(u ** 1.35, 4))
    return sorted(ts)


def construir(con, p):
    sup = Superficie(p)
    L, W, H = p["L"], p["W"], p["H"]
    n = p.get("lados", 18)
    tier = con.tier
    extras = set(p.get("extras", ()))
    prim = p.get("ranura_casco", "primario")

    # ---- fuselaje ------------------------------------------------------------------------------------------
    ts = _ts(p["estaciones"], p.get("anillos", 14))
    anillos = [sup.anillo(t, n) for t in ts]
    fus = con.loft(anillos, prim)
    if p.get("organico"):
        amp = p["organico"]

        def onda(v):
            t = (v.y + L / 2) / L
            zc = sup.datos(t)[2] * H
            r = V((v.x, 0, v.z - zc))
            if r.length < 1e-4:
                return v
            k = (math.sin(v.y * 1.7 + v.x * 0.9) * 0.5 + math.sin(v.y * 3.1 - v.z * 2.3) * 0.3 +
                 math.sin(math.atan2(r.z, r.x) * 5 + v.y * 0.6) * 0.4)
            return v + r.normalized() * amp * k * min(1.0, t * 6, (1 - t) * 6)

        con.desplazar(fus, onda)

    y_cola = sup.y(1.0)
    w_c, h_c, zc_c, cu_c, _ = sup.datos(1.0)

    # mamparo de popa (donde van los motores)
    popa = seccion(y_cola + 0.12, w_c * W * 0.9, h_c * H * 0.9, zc_c * H, n, cu_c)
    popa2 = seccion(y_cola, w_c * W * 0.98, h_c * H * 0.98, zc_c * H, n, cu_c)
    con.loft([popa2, popa], "oscuro")

    # ---- acoples laterales (pilones) -------------------------------------------------------------------------
    for i, (t, zf) in enumerate(p.get("laterales", [(0.5, 0.0)])):
        y = sup.y(t)
        z = zf * H
        x_borde = sup.ancho_en(t, z)
        largo_pilon = p.get("pilon", 0.45)
        x_s = x_borde + largo_pilon
        h_pil = CON_LAT * 1.05
        l_pil = CON_LAT * 1.5
        # pilón: cuña que sale del costado y se estrecha
        perfil = [(0, -l_pil / 2), (0, l_pil / 2), (1, l_pil * 0.42), (1, -l_pil * 0.42)]
        a = [V((x_borde - 0.25, y + perfil[0][1], z - h_pil / 2)), V((x_borde - 0.25, y + perfil[1][1], z - h_pil / 2)),
             V((x_s - 0.14, y + perfil[2][1], z - h_pil * 0.42)), V((x_s - 0.14, y + perfil[3][1], z - h_pil * 0.42))]
        b = [q + V((0, 0, h_pil if k < 2 else h_pil * 0.84)) for k, q in enumerate(a)]
        caras = con.loft([a, b], p.get("ranura_pilon", "secundario"))
        sufijo = "" if i == 0 else f"_{i + 1}"
        con.acople(f"acople_lateral_izq{sufijo}", (x_s, y, z), (1, 0, 0), "CASCO_LATERAL", "salida")
        # el derecho: espejo
        con.espejo_x(caras)
        con.acople(f"acople_lateral_der{sufijo}", (-x_s, y, z), (-1, 0, 0), "CASCO_LATERAL", "salida")
        # las bridas del lado derecho las crea acople(); hay que construirlas también: acople ya lo hace.

    # ---- popa: motores -------------------------------------------------------------------------------------------
    traseros = p.get("traseros", [(0.0, 0.0)])
    for i, (xf, zf) in enumerate(traseros):
        x = xf * w_c * W / 2
        z = zc_c * H + zf * h_c * H / 2
        nombre = "acople_motor" if len(traseros) == 1 else f"acople_motor_{i + 1}"
        con.acople(nombre, (x, y_cola + 0.12 + 0.14, z), (0, 1, 0), "CASCO_TRASERO", "salida")

    # ---- superiores ----------------------------------------------------------------------------------------------
    for t, nombre in p.get("superiores", [(0.3, "acople_cabina")]):
        y = sup.y(t)
        z_top = sup.arriba_en(t)
        tam = 2.0
        # almohadilla: base que se hunde en el casco
        con.caja((0, y, z_top - 0.12), (tam * 1.2, tam * 1.25, 0.5), p.get("ranura_pad", "secundario"))
        con.acople(nombre, (0, y, z_top + 0.13 + 0.14), (0, 0, 1), "CASCO_SUPERIOR", "salida")

    # ---- inferiores ----------------------------------------------------------------------------------------------
    for i, t in enumerate(p.get("inferiores", [0.5])):
        y = sup.y(t)
        z_b = sup.abajo_en(t)
        con.caja((0, y, z_b + 0.1), (1.5, 1.5, 0.45), "oscuro")
        nombre = "acople_inferior" if len(p.get("inferiores", [0.5])) == 1 else f"acople_inferior_{i + 1}"
        con.acople(nombre, (0, y, z_b - 0.125 - 0.14), (0, 0, -1), "CASCO_INFERIOR", "salida")

    # ---- frontal (bajo el morro) -----------------------------------------------------------------------------------
    if p.get("frontal", True):
        tf = p.get("t_frontal", 0.14)
        y = sup.y(tf)
        zb = sup.abajo_en(tf)
        zf = zb - 0.55
        # pilón de barbilla: cubre toda la brida (radio 0,6)
        z0, z1 = zf - 0.66, zb + 0.3
        con.caja((0, y + 0.55, (z0 + z1) / 2), (1.3, 1.6, z1 - z0), "oscuro")
        con.acople("acople_frontal", (0, y - 0.25 - 0.14, zf), (0, -1, 0), "CASCO_FRONTAL", "salida")

    # ---- detalles por familia ----------------------------------------------------------------------------------------
    detalles(con, sup, p, extras)
    return sup


def _tira_superficie(con, sup, ang, t0, t1, ancho, ranura, pasos=14, alto=0.05, espejo=True, sobre=0.015):
    pts, nrm = [], []
    for k in range(pasos + 1):
        t = t0 + (t1 - t0) * k / pasos
        nn = sup.normal(t, ang)
        pts.append(sup.punto(t, ang) + nn * sobre)
        nrm.append(nn)
    caras = con.tira(pts, nrm, ancho, ranura, alto=alto)
    if espejo:
        con.espejo_x(caras)
    return caras


def detalles(con, sup, p, extras):
    L, W, H = p["L"], p["W"], p["H"]
    tier = con.tier

    if "tomas" in extras:
        # tomas de aire a los lados, por detrás de la cabina
        t = p.get("t_tomas", 0.32)
        y = sup.y(t)
        z = sup.datos(t)[2] * H - H * 0.05
        x = sup.ancho_en(t, z)
        lt = L * 0.22
        perfil_ext = [V((x - 0.2, y, z - H * 0.16)), V((x + 0.35, y, z - H * 0.16)), V((x + 0.35, y, z + H * 0.16)),
                      V((x - 0.2, y, z + H * 0.16))]
        perfil_fin = [q + V((-(0.3 if k in (1, 2) else 0), lt, 0)) for k, q in enumerate(perfil_ext)]
        c1 = con.loft([perfil_ext, perfil_fin], "secundario" if tier != 1 else "oscuro")
        boca = con.caja((x + 0.08, y - 0.02, z), (0.42, 0.08, H * 0.26), "oscuro", bisel=False)
        con.espejo_x(c1 + boca)

    if "tuberias" in extras:
        # tuberías externas a lo largo de los costados (tier 1: industrial)
        for zf, r in ((0.12, 0.09), (-0.18, 0.07)):
            pts = []
            for k in range(9):
                t = 0.25 + 0.62 * k / 8
                z = zf * H + sup.datos(t)[2] * H
                pts.append((sup.ancho_en(t, z) + r * 0.6, sup.y(t), z))
            for a, b in zip(pts[:-1], pts[1:]):
                d = V(b) - V(a)
                c1 = con.cilindro(a, d, r, d.length, "metal", lados=6, tapas=False, bisel=False)
                con.espejo_x(c1)
            for q in pts[::3]:
                c2 = con.caja(q, (r * 3, 0.12, r * 3), "oscuro", bisel=False)
                con.espejo_x(c2)

    if "rejillas" in extras:
        for t in (0.62, 0.74):
            y = sup.y(t)
            z = sup.arriba_en(t)
            con.rejilla((W * 0.18, y, z - 0.02), (0, 0, 1), (0, 1, 0), L * 0.08, W * 0.16, "oscuro", "metal",
                        lamas=4)
            con.rejilla((-W * 0.18, y, z - 0.02), (0, 0, 1), (0, 1, 0), L * 0.08, W * 0.16, "oscuro", "metal",
                        lamas=4)

    if "compuertas" in extras:
        # compuertas laterales de carga (marco en relieve + bisagras)
        for t in (0.42, 0.62):
            y = sup.y(t)
            z = sup.datos(t)[2] * H
            x = sup.ancho_en(t, z)
            c1 = con.caja((x + 0.02, y, z), (0.12, L * 0.14, H * 0.55), "oscuro")
            c2 = con.caja((x + 0.06, y, z), (0.08, L * 0.12, H * 0.48), "secundario")
            c3 = con.caja((x + 0.1, y - L * 0.055, z + H * 0.18), (0.08, 0.3, 0.2), "aviso", bisel=False)
            con.espejo_x(c1 + c2 + c3)

    if "bahia" in extras:
        # bahía de bombas en la panza: dos puertas con bisagras y raíles
        t0, t1 = 0.35, 0.68
        y0, y1 = sup.y(t0), sup.y(t1)
        zb = min(sup.abajo_en(t0), sup.abajo_en(t1))
        ancho = W * 0.42
        con.caja(((0), (y0 + y1) / 2, zb + 0.05), (ancho + 0.3, y1 - y0 + 0.3, 0.3), "oscuro")
        for s in (-1, 1):
            con.caja((s * ancho / 4, (y0 + y1) / 2, zb - 0.08), (ancho / 2 - 0.08, y1 - y0, 0.12), "secundario")
            for k in range(4):
                yy = y0 + (y1 - y0) * (k + 0.5) / 4
                con.caja((s * (ancho / 2 + 0.05), yy, zb - 0.05), (0.12, 0.3, 0.2), "metal", bisel=False)

    if "blindaje" in extras:
        # placas de blindaje superpuestas en los costados
        for k in range(4):
            t = 0.3 + k * 0.14
            y = sup.y(t)
            z = sup.datos(t)[2] * H + H * 0.18
            x = sup.ancho_en(t, z)
            c1 = con.caja_orientada((x + 0.06, y, z), (1, 0, 0.25), (0, 1, 0), (L * 0.13, H * 0.4, 0.16),
                                    "secundario")
            con.espejo_x(c1)

    if "neon_lados" in extras:
        ang = p.get("ang_neon", 0.12)
        _tira_superficie(con, sup, ang, p.get("t_neon", (0.12, 0.92))[0], p.get("t_neon", (0.12, 0.92))[1],
                         p.get("ancho_neon", 0.12), "neon")
    if "neon_lomo" in extras:
        _tira_superficie(con, sup, math.pi / 2, 0.42, 0.95, 0.1, "neon", espejo=False)
    if "neon2_lados" in extras:
        _tira_superficie(con, sup, -0.35, 0.2, 0.85, 0.08, "neon2")

    if "aletas" in extras:
        # aletas ventrales en la popa
        y = sup.y(0.88)
        zb = sup.abajo_en(0.88)
        for s in (-1, 1):
            con.prisma([(0, 0), (L * 0.14, 0), (L * 0.18, -H * 0.4), (L * 0.1, -H * 0.42)],
                       (s * W * 0.22, y - L * 0.08, zb + 0.12), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.12, "secundario")

    if "quilla" in extras:
        y0, y1 = sup.y(0.2), sup.y(0.9)
        zb = min(sup.abajo_en(t) for t in (0.2, 0.5, 0.9))
        con.cuña([(-0.25, zb + 0.3), (0.25, zb + 0.3), (0.12, zb - H * 0.12), (-0.12, zb - H * 0.12)], y0, y1,
                 "oscuro")

    if "antena" in extras:
        t = 0.72
        y = sup.y(t)
        z = sup.arriba_en(t)
        con.cilindro((W * 0.15, y, z - 0.1), (0.15, 0.3, 1), 0.05, H * 0.6, "metal", lados=6, bisel=False)
        con.esfera((W * 0.15 + 0.09, y + 0.18, z - 0.1 + H * 0.57), 0.08, "neon2", lados=8, anillos=4)

    if "puente" in extras:
        # superestructura escalonada (fragatas, cruceros)
        niveles = p.get("niveles_puente", 2)
        t = p.get("t_puente", 0.62)
        y = sup.y(t)
        z = sup.arriba_en(t)
        for k in range(niveles):
            w = W * (0.55 - k * 0.14)
            l = L * (0.22 - k * 0.05)
            hh = H * 0.16
            con.cuña([(-w / 2, z + k * hh - 0.1), (w / 2, z + k * hh - 0.1), (w / 2 * 0.86, z + (k + 1) * hh),
                      (-w / 2 * 0.86, z + (k + 1) * hh)], y - l / 2, y + l / 2, "secundario" if k % 2 else "primario")
            # ventanales
            con.caja((0, y - l / 2 - 0.02, z + k * hh + hh * 0.55), (w * 0.7, 0.06, hh * 0.3), "neon",
                     bisel=False)

    if "cubierta" in extras:
        # cubierta plana con líneas de pista (portanaves)
        t0, t1 = p.get("t_cubierta", (0.12, 0.5))
        y0, y1 = sup.y(t0), sup.y(t1)
        z = max(sup.arriba_en(t0), sup.arriba_en(t1))
        con.caja((0, (y0 + y1) / 2, z + 0.1), (W * 0.62, y1 - y0, 0.3), "oscuro")
        for k in range(6):
            yy = y0 + (y1 - y0) * (k + 0.5) / 6
            con.caja((0, yy, z + 0.27), (W * 0.04, (y1 - y0) / 14, 0.04), "neon", bisel=False)

    if "costillas" in extras:
        # costillas orgánicas (tier 5): anillos aplastados a lo largo del casco
        for k in range(p.get("n_costillas", 6)):
            t = 0.2 + 0.65 * k / max(p.get("n_costillas", 6) - 1, 1)
            w, h, zc, cu, ach = sup.datos(t)
            c = con.toro((0, sup.y(t), zc * H), (0, 1, 0), 1.0, 0.09, "secundario", n1=20, n2=5,
                         escala=(w * W / 2 + 0.02, h * H / 2 + 0.02))

    if "cristales" in extras:
        # vainas de cristal a los lados (tier 5)
        for k, t in enumerate(p.get("t_cristales", (0.35, 0.55, 0.75))):
            y = sup.y(t)
            z = sup.datos(t)[2] * H + H * 0.1
            x = sup.ancho_en(t, z)
            c1 = con.esfera((x - 0.05, y, z), 0.45 + 0.1 * (k % 2), "cristal", lados=10, anillos=6,
                            escala=(0.7, 1.6, 0.8))
            c2 = con.esfera((x - 0.08, y, z), 0.22, "neon", lados=8, anillos=4, escala=(0.6, 1.4, 0.7))
            con.espejo_x(c1 + c2)

    if "anillos_flotantes" in extras:
        for k, t in enumerate(p.get("t_anillos", (0.45, 0.75))):
            w, h, zc, cu, ach = sup.datos(t)
            r = max(w * W, h * H) * 0.62 + 0.3
            c = con.toro((0, sup.y(t), zc * H), (0, 1, 0.15 * (-1) ** k), r, 0.07, "neon", n1=28, n2=6)

    if "facetas_oro" in extras:
        # molduras doradas en las aristas del casco élite
        for ang in (0.0, math.pi * 0.5):
            _tira_superficie(con, sup, ang, 0.06, 0.97, 0.1, "secundario", alto=0.07, espejo=ang == 0.0,
                             sobre=0.0)

    if "pinchos" in extras:
        # aletas-cuchilla agresivas en la popa (tier 4)
        for s in (-1, 1):
            y = sup.y(0.86)
            z = sup.arriba_en(0.86)
            c = con.prisma([(0, 0), (L * 0.16, 0), (L * 0.24, H * 0.55), (L * 0.2, H * 0.58)],
                           (s * W * 0.26, y - L * 0.1, z - 0.15), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.1, "secundario")
            con.girar(c, s * -0.35, (0, 1, 0), (s * W * 0.26, y, z))

    if "vainas" in extras:
        # vainas de sensores/carga a los lados de la popa
        for s in (-1, 1):
            t = 0.7
            z = sup.datos(t)[2] * H - H * 0.15
            x = sup.ancho_en(0.7, z) + 0.2
            y = sup.y(t)
            perfil = [(0, 0), (0.25, 0.35), (1.2, 0.45), (L * 0.2, 0.45), (L * 0.22, 0.3), (L * 0.22, 0)]
            con.revolucion((s * x, y - L * 0.11, z), (0, 1, 0), perfil, "secundario", lados=10)
