"""
Relieve del Valle del Alba: altura (studs sobre el mar) en cada punto de la cara YP, más los «campos» que necesitan la
textura y la vegetación (distancia al río y a los caminos, dentro de qué sitio cae, densidad de bosque...). Solo numpy
y scipy, así que se puede probar sin Blender.

Igual que en el planeta de prueba, el relieve es una FUNCIÓN y no una malla esculpida: cualquier resolución de malla
(la de los renders o la de los trozos de Roblox) pide la altura a esta función y sale el mismo terreno.

Orden de las capas (cada una trabaja sobre la anterior):
  1. Fondo del valle: suelo + ondulación de praderas + anillo de colinas + colinas sueltas + colina del atardecer.
     La vega del río baja un poco el terreno a su alrededor. En los campos de Los Molinos la ondulación se suaviza.
  2. Sitios: el suelo se aplana a la altura media de su huella (rectángulo de esquinas redondas), con una transición
     suave (smoothstep) alrededor. «Llano» quiere decir a radio constante: sigue la curva del planeta.
  3. Caminos: cada camino tiene un perfil (el terreno suavizado a lo largo del camino) y el terreno se lleva a ese perfil
     en su ancho, con transición suave a los lados. Así no hay cuestas bruscas ni el camino se tuerce de lado.
  4. Río: un cauce de sección parabólica y orillas en talud, unido al terreno con un mínimo suave (sin aristas).
  1b. Exterior: al otro lado de la sierra el terreno pasa poco a poco al relieve del planeta de prueba (con su costa y
     su mar), con una frontera deformada por ruido: la costa no sale recta.
  5. Borde: en los últimos FRANJA_BORDE studs de la cara el valle se funde con el relieve del planeta de prueba, con
     derivada nula en el borde: la región empalma sin costura con las caras vecinas.
"""

import math
import os
import sys

import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import diseno as D  # noqa: E402
import geo  # noqa: E402
import terreno_base as TB  # noqa: E402

suavizar = geo.suavizar


def smin(a, b, k):
    """Mínimo suave (polinómico): igual que min lejos de la unión, redondeado en una franja de ancho k."""
    h = np.clip(k - np.abs(a - b), 0.0, None) / k
    return np.minimum(a, b) - h * h * k * 0.25


def curva_suave(puntos, paso=1.5):
    """Catmull-Rom centrípeta por los puntos (n, k): devuelve muestras (m, k) separadas ~`paso` studs en (x, y).
    Las columnas extra (nivel, ancho...) se interpolan igual que la posición."""
    P = np.asarray(puntos, dtype=np.float64)
    P = np.concatenate([2 * P[:1] - P[1:2], P, 2 * P[-1:] - P[-2:-1]])
    salida = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]

        def t_sig(t, a, b):
            return t + max(np.linalg.norm((b - a)[:2]), 1e-6) ** 0.5

        t0 = 0.0
        t1 = t_sig(t0, p0, p1)
        t2 = t_sig(t1, p1, p2)
        t3 = t_sig(t2, p2, p3)
        n = max(2, int(np.linalg.norm((p2 - p1)[:2]) / paso))
        t = np.linspace(t1, t2, n, endpoint=False)[:, None]
        a1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
        a2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
        a3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        b1 = (t2 - t) / (t2 - t0) * a1 + (t - t0) / (t2 - t0) * a2
        b2 = (t3 - t) / (t3 - t1) * a2 + (t - t1) / (t3 - t1) * a3
        salida.append((t2 - t) / (t2 - t1) * b1 + (t - t1) / (t2 - t1) * b2)
    salida.append(P[-2:-1])
    return np.concatenate(salida)


def sdf_rectangulo(u, v, semiancho, semifondo, esquina):
    """Distancia con signo a un rectángulo de esquinas redondas (negativa dentro)."""
    qx = np.abs(u) - (semiancho - esquina)
    qy = np.abs(v) - (semifondo - esquina)
    fuera = np.hypot(np.clip(qx, 0, None), np.clip(qy, 0, None))
    dentro = np.minimum(np.maximum(qx, qy), 0.0)
    return fuera + dentro - esquina


class Polilinea:
    """Muestras densas de una curva, con un árbol para buscar la muestra más cercana."""

    def __init__(self, muestras):
        self.m = muestras
        self.xy = muestras[:, :2]
        seg = np.linalg.norm(np.diff(self.xy, axis=0), axis=1)
        self.s = np.concatenate([[0.0], np.cumsum(seg)])
        self.arbol = cKDTree(self.xy)

    def cercano(self, x, y):
        d, i = self.arbol.query(np.stack([x.ravel(), y.ravel()], -1), workers=-1)
        return d.reshape(x.shape), i.reshape(x.shape)


class Valle:
    def __init__(self):
        self.base = TB.Relieve()  # el planeta de prueba, tal cual
        self.ruido = TB.Ruido(D.SEMILLA)
        self.rio = Polilinea(curva_suave(D.RIO))
        self.sitios = {n: geo.Sitio(s["x"], s["y"]) for n, s in D.SITIOS.items()}
        self.alturas_sitio = {}
        self.caminos = {n: Polilinea(curva_suave(c["puntos"])) for n, c in D.CAMINOS.items()}
        self.perfiles = {}
        self.altura_terraza = None
        self.altura_terraza = float(self.capa_fondo(np.array([D.MIRADOR[0]]), np.array([D.MIRADOR[1]]))[0])
        self._preparar()

    # ----------------------------------------------------------------------------------------------------------
    # Ruido 2D (sobre el plano de diseño)
    # ----------------------------------------------------------------------------------------------------------

    def fbm2(self, x, y, longitud, octavas, capa, ganancia=0.5, trozo=2_000_000):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        xr, yr = x.ravel(), y.ravel()
        r = self.ruido
        salida = np.empty(x.size)
        for a in range(0, x.size, trozo):
            p = np.stack([xr[a : a + trozo], yr[a : a + trozo], np.zeros(min(trozo, x.size - a))], -1) / longitud
            total = np.zeros(len(p))
            amp, norma = 1.0, 0.0
            for o in range(octavas):
                k = (capa * 3 + o) % len(r.rotaciones)
                q = (p @ r.rotaciones[k].T) * (2.0**o) + r.desplazamientos[k]
                total += amp * r.perlin(q)
                norma += amp
                amp *= ganancia
            salida[a : a + trozo] = total / norma
        return salida.reshape(x.shape)

    # ----------------------------------------------------------------------------------------------------------
    # Capas
    # ----------------------------------------------------------------------------------------------------------

    def mascara_campos(self, x, y):
        c = D.CAMPOS
        q = np.hypot((x - c["x"]) / c["radio_x"], (y - c["y"]) / c["radio_y"])
        q = q + 0.12 * self.fbm2(x, y, 180.0, 2, capa=9)
        return suavizar(q, 1.0, 0.75)

    def capa_fondo(self, x, y):
        campos = self.mascara_campos(x, y)
        h = np.full(x.shape, D.SUELO_VALLE)
        for i, (amp, lon, octv) in enumerate(D.ONDULACION):
            suave = 1.0 - D.CAMPOS["suavizado"] * campos if i > 0 else 1.0 - 0.5 * D.CAMPOS["suavizado"] * campos
            h = h + amp * self.fbm2(x, y, lon, octv, capa=i + 1) * suave

        # Anillo de colinas: una sierra (sube y vuelve a bajar hacia la costa) con la elipse deformada por ruido y la
        # altura muy variable, para que sean colinas sueltas y no una muralla. Se abre un paso donde sale el río y
        # donde salen los caminos hacia otras regiones.
        rx, ry = D.ANILLO_RADIOS
        q = np.hypot(x / rx, y / ry) + 0.09 * self.fbm2(x, y, 650.0, 3, capa=4)
        cresta = np.clip(0.8 + 0.9 * self.fbm2(x, y, 380.0, 3, capa=5), 0.15, 1.5)
        sierra = suavizar(q, D.ANILLO_DESDE, D.ANILLO_HASTA) * suavizar(q, D.ANILLO_HASTA + 0.40, D.ANILLO_HASTA)
        d_rio, _ = self.rio.cercano(x, y)
        paso = 1.0 - np.exp(-((d_rio / D.PASO_RIO) ** 2))
        for nombre in D.CAMINOS_A_OTRAS_REGIONES:
            dc, _ = self.caminos[nombre].cercano(x, y)
            paso = paso * (1.0 - 0.75 * np.exp(-((dc / D.PASO_CAMINO) ** 2)))
        h = h + D.ANILLO_ALTURA * cresta * sierra * paso

        for (cx, cy, alt, rx, ry, giro) in D.COLINAS:
            t = self._dist_elipse(x, y, cx, cy, rx, ry, giro) + 0.10 * self.fbm2(x, y, 260.0, 2, capa=6)
            h = h + alt * suavizar(t, 1.0, 0.0) * paso

        c = D.COLINA_ATARDECER
        t = self._dist_elipse(x, y, c["x"], c["y"], c["radio_x"], c["radio_y"], c["giro"])
        t = t + 0.05 * self.fbm2(x, y, 200.0, 2, capa=7) * suavizar(t, 0.2, 0.5)
        h = h + c["altura"] * suavizar(t, 1.0, c["meseta"])

        # Terraza del mirador: un rellano llano a media ladera (a la altura que tenía el terreno en su centro).
        if self.altura_terraza is not None:
            t = D.TERRAZA_MIRADOR
            dm = np.hypot(x - D.MIRADOR[0], y - D.MIRADOR[1])
            f = suavizar(dm, t["radio"] + t["transicion"], t["radio"])
            h = h + f * (self.altura_terraza - h)

        # Vega: el terreno baja un poco alrededor del río.
        d, _ = self.rio.cercano(x, y)
        h = h - D.RIO_VEGA[0] * np.exp(-((d / D.RIO_VEGA[1]) ** 2))
        return h

    @staticmethod
    def _dist_elipse(x, y, cx, cy, rx, ry, giro):
        g = math.radians(giro)
        dx, dy = x - cx, y - cy
        u = dx * math.cos(g) + dy * math.sin(g)
        v = -dx * math.sin(g) + dy * math.cos(g)
        return np.hypot(u / rx, v / ry)

    def peso_sitio(self, nombre, x, y):
        s = D.SITIOS[nombre]
        u, v = self.sitios[nombre].local(geo.direccion(x, y))
        sd = sdf_rectangulo(u, v, s["ancho"] / 2, s["fondo"] / 2, s["esquina"])
        return suavizar(sd, s["borde"], 0.0), u, v, sd

    def capa_sitios(self, x, y, h):
        for nombre in D.SITIOS:
            f, _, _, _ = self.peso_sitio(nombre, x, y)
            h = h + f * (self.alturas_sitio[nombre] - h)
        return h

    def capa_caminos(self, x, y, h, hasta=None):
        for nombre, c in D.CAMINOS.items():
            if nombre == hasta:
                break
            pl = self.caminos[nombre]
            d, i = pl.cercano(x, y)
            f = suavizar(d, c["ancho"] / 2 + D.CAMINO_TRANSICION, c["ancho"] / 2 + 1.0)
            h = h + f * (self.perfiles[nombre][i] - h)
        return h

    def capa_rio(self, x, y, h):
        d, i = self.rio.cercano(x, y)
        nivel = self.rio.m[i, 2]
        semi = self.rio.m[i, 3]
        prof = D.RIO_PROFUNDIDAD
        # Cauce parabólico hasta la orilla y talud recto después, con la misma pendiente en la unión.
        pend_orilla = 2 * prof / semi
        talud = np.minimum(pend_orilla, D.RIO_TALUD)
        cauce = np.where(d < semi, nivel - prof + prof * (d / semi) ** 2, nivel + (d - semi) * talud)
        h = smin(h, cauce, 4.0)
        cx, cy, r = D.CHARCA_MANANTIAL
        dc = np.hypot(x - cx, y - cy)
        nivel_c = D.RIO[0][2]
        charca = np.where(dc < r, nivel_c - 3.0 + 3.0 * (dc / r) ** 2, nivel_c + (dc - r) * 0.35)
        return smin(h, charca, 4.0)

    def mascara_exterior(self, x, y):
        """0 dentro del valle, 1 al otro lado de la sierra: ahí manda el relieve del planeta de prueba, con su costa."""
        rx, ry = D.ANILLO_RADIOS
        q = np.hypot(x / rx, y / ry) + D.COSTA_RUIDO * self.fbm2(x, y, 600.0, 4, capa=8, ganancia=0.55)
        return suavizar(q, D.COSTA_DESDE, D.COSTA_HASTA)

    def capa_borde(self, x, y, h, base):
        # Producto de dos smoothstep (uno por eje): suave también en las diagonales (con max() saldría una arista).
        w = suavizar(geo.L - np.abs(x), 0.0, D.FRANJA_BORDE) * suavizar(geo.L - np.abs(y), 0.0, D.FRANJA_BORDE)
        return base + w * (h - base)

    def altura_base(self, x, y):
        d = geo.blender_a_roblox(geo.direccion(x, y))
        return self.base.altura(d.reshape(-1, 3)).reshape(x.shape)

    # ----------------------------------------------------------------------------------------------------------
    # Preparación: alturas de los sitios y perfiles de los caminos
    # ----------------------------------------------------------------------------------------------------------

    def _preparar(self):
        for nombre, s in D.SITIOS.items():
            g = np.linspace(-0.5, 0.5, 25)
            U, V = np.meshgrid(g * s["ancho"], g * s["fondo"])
            x, y = self.sitios[nombre].diseno(U, V)
            self.alturas_sitio[nombre] = float(np.mean(self.capa_fondo(x, y)))
        for nombre in D.CAMINOS:
            pl = self.caminos[nombre]
            x, y = pl.xy[:, 0].copy(), pl.xy[:, 1].copy()
            h = self.capa_sitios(x, y, self.capa_fondo(x, y))
            h = self.capa_caminos(x, y, h, hasta=nombre)
            # Suavizado gaussiano a lo largo del camino (por distancia recorrida, no por índice).
            paso = np.median(np.diff(pl.s))
            sig = D.CAMINO_SUAVIZADO / paso
            k = np.arange(-int(3 * sig), int(3 * sig) + 1)
            w = np.exp(-0.5 * (k / sig) ** 2)
            w /= w.sum()
            hp = np.pad(h, len(k) // 2, mode="edge")
            perfil = np.convolve(hp, w, mode="valid")
            # «lomo de asno» del camino que cruza el puente
            dp = np.hypot(pl.xy[:, 0] - D.PUENTE["x"], pl.xy[:, 1] - D.PUENTE["y"])
            if dp.min() < 10:
                i0 = int(np.argmin(dp))
                ds = pl.s - pl.s[i0]
                perfil = perfil + D.PUENTE["joroba"] * np.exp(-((ds / D.PUENTE["ancho_joroba"]) ** 2))
            self.perfiles[nombre] = perfil

    # ----------------------------------------------------------------------------------------------------------
    # API
    # ----------------------------------------------------------------------------------------------------------

    def altura(self, x, y, trozo=400_000):
        x = np.asarray(x, dtype=np.float64)
        y = np.asarray(y, dtype=np.float64)
        forma = x.shape
        x, y = x.ravel(), y.ravel()
        h = np.empty(x.size)
        for a in range(0, x.size, trozo):
            xs, ys = x[a : a + trozo], y[a : a + trozo]
            base = self.altura_base(xs, ys)
            hh = self.capa_fondo(xs, ys)
            m = self.mascara_exterior(xs, ys)
            hh = hh + m * (base - hh)
            hh = self.capa_sitios(xs, ys, hh)
            hh = self.capa_caminos(xs, ys, hh)
            hh = self.capa_rio(xs, ys, hh)
            hh = self.capa_borde(xs, ys, hh, base)
            h[a : a + trozo] = hh
        return h.reshape(forma)

    def densidad_bosque(self, x, y):
        """0 = pradera, 1 = bosque cerrado. Respeta las distancias libres a sitios, caminos y río."""
        dens = np.zeros(x.shape)
        # forma orgánica: la distancia al centro se deforma con dos ruidos (lóbulos grandes y bordes rotos)
        deform = 0.55 * self.fbm2(x, y, 260.0, 3, capa=10) + 0.22 * self.fbm2(x, y, 70.0, 2, capa=24)
        for (cx, cy, r, k) in D.BOSQUES:
            q = np.hypot(x - cx, y - cy) / r + deform
            dens = np.maximum(dens, k * suavizar(q, 1.0, 0.5))
        # bosques a manchas sobre la sierra del valle
        b = D.BOSQUE_SIERRA
        rx, ry = D.ANILLO_RADIOS
        qa = np.hypot(x / rx, y / ry)
        banda = suavizar(qa, b["desde"], b["desde"] + 0.12) * suavizar(qa, b["hasta"], b["hasta"] - 0.12)
        manchas = suavizar(self.fbm2(x, y, 330.0, 3, capa=25) + 0.3 * self.fbm2(x, y, 90.0, 2, capa=26),
                           b["umbral"], b["umbral"] + 0.2)
        dens = np.maximum(dens, b["densidad"] * banda * manchas)
        # claros dentro de los bosques
        dens *= 1.0 - 0.8 * suavizar(self.fbm2(x, y, 60.0, 2, capa=27), 0.35, 0.5)
        return dens * self.libre(x, y)

    def libre(self, x, y):
        """1 donde se puede poner vegetación grande; 0 en sitios, caminos y cauce (con transición)."""
        lib = np.ones(x.shape)
        for nombre in D.SITIOS:
            _, _, _, sd = self.peso_sitio(nombre, x, y)
            lib *= suavizar(sd, D.DISTANCIAS_LIBRES["sitio"] * 0.5, D.DISTANCIAS_LIBRES["sitio"])
        for nombre, c in D.CAMINOS.items():
            d, _ = self.caminos[nombre].cercano(x, y)
            lib *= suavizar(d, c["ancho"] / 2 + 2, c["ancho"] / 2 + D.DISTANCIAS_LIBRES["camino"])
        d, i = self.rio.cercano(x, y)
        lib *= suavizar(d, self.rio.m[i, 3] + 4, self.rio.m[i, 3] + D.DISTANCIAS_LIBRES["rio"])
        return lib
