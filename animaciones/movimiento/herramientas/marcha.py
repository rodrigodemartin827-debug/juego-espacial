"""
Generador de ciclos de marcha (andar y correr) para R6, con los pies clavados en el suelo.

La animación es "en el sitio": el personaje no avanza (de eso se encarga el Humanoid de Roblox) y el suelo corre
hacia atrás a `velocidad` studs/s, como en una cinta. Un pie apoyado se queda quieto respecto a ese suelo: retrocede
exactamente a la velocidad de la cinta, así que en el juego, moviéndose a esa velocidad, no patina.

Cómo se calcula cada fotograma:
  1. El torso (balanceo, inclinación, ladeo, giro de cadera) sale de curvas cíclicas escritas a mano.
  2. La pierna de apoyo se resuelve con `ciclo.apoyo`: su ángulo y la ALTURA del torso salen de la geometría, de modo
     que la bota rueda talón -> planta -> punta sin deslizar ni hundirse. El sube y baja del cuerpo no está dibujado:
     es la consecuencia física de pasar por encima de una pierna rígida.
  3. La pierna en el aire va del despegue al siguiente apoyo con una curva de Hermite que empalma con la velocidad
     del pie al despegar y al aterrizar (sin tirones); el ladeo del torso levanta su cadera para que no roce el suelo.
  4. Si hay fase en el aire (correr), el cuerpo sigue una parábola entre el despegue y el aterrizaje.
  5. Brazos y cabeza encima, con su propio retraso respecto al torso.

La huella de cada pisada se busca para que todo encaje: al andar, que en el cambio de pie las dos piernas pidan al
torso la misma altura (así no hay salto); al correr, que el pie despegue con el ángulo pedido.
"""

import math

from mathutils import Vector

import ciclo
import rig_r6 as r6
from ciclo import Pose, ciclica


class Marcha:
    """`p` es un diccionario con los datos de la animación (ver andar.py y correr.py)."""

    def __init__(self, p):
        self.p = p
        self.fps = p["fps"]
        self.n = p["ciclo"]  # fotogramas del ciclo
        self.T = self.n / self.fps
        self.v = p["velocidad"]
        self.apoyo = p["apoyo"]  # fracción del ciclo que cada pie está en el suelo
        self.bota = ciclo.Bota(p["flecha"])
        # Cada pierna: fase en la que aterriza (la izquierda en 0, la derecha medio ciclo después).
        self.inicio = {"Left Leg": 0.0, "Right Leg": 0.5}
        self.k = 0.0
        self._x_huella = {}
        self._resolver_huella()
        self._preparar_aire()
        self._preparar_vuelo()

    # ------------------------------------------------------------------ torso y huellas
    def _torso(self, fase):
        """Pose con el torso colocado (sin altura) en la fase dada."""
        p = self.p
        pose = Pose()
        x = ciclica(p["torso_x"], fase)
        y = ciclica(p["torso_y"], fase)
        pose.loc["Torso"] = Vector((x, y, 0.0))
        pose.q["Torso"] = ciclo.rot_torso(
            ciclica(p["inclinacion"], fase), ciclica(p["ladeo"], fase), ciclica(p["giro"], fase)
        )
        return pose

    def _en_apoyo(self, pierna, fase):
        """Fracción recorrida del apoyo (0..1) si la pierna está en el suelo, o None."""
        u = (fase - self.inicio[pierna]) % 1.0
        if u <= self.apoyo + 1e-9:
            return u / self.apoyo
        return None

    def _huella(self, pierna, fase):
        """(x, y) de la huella de la pisada en curso, en la cinta: retrocede a la velocidad del suelo."""
        u = (fase - self.inicio[pierna]) % 1.0
        if u > self.apoyo + 1e-9:
            u -= 1.0  # pisada siguiente (para el empalme del aire)
        y = self.k + self.v * u * self.T
        # x: la cadera en promedio durante el apoyo (así la pierna apenas se ladea), más el ancho pedido
        # (negativo = hacia dentro). Se guarda: es igual en todas las pisadas de esa pierna.
        if pierna not in self._x_huella:
            muestras = [self.inicio[pierna] + self.apoyo * i / 8 for i in range(9)]
            self._x_huella[pierna] = sum(self._torso(m % 1.0).mundo(pierna)[0].x for m in muestras) / 9
        cadera_x = self._x_huella[pierna]
        lado = ciclo.PIERNAS[pierna]
        # el centro de la bota está 0,5 hacia dentro del pivote de la cadera
        return cadera_x - 0.5 * lado + lado * self.p["ancho_pisada"], y

    def _resolver_apoyo(self, pierna, fase, pose=None):
        pose = pose or self._torso(fase)
        sube, q, info = ciclo.apoyo(pose, pierna, self._huella(pierna, fase), self.bota)
        return sube, q, info

    def _resolver_huella(self):
        """Busca k (dónde cae la pisada respecto al cuerpo)."""
        if self.p.get("alfa_despegue") is None:
            # Andar: en el cambio de pie (fase = apoyo = 0.5) las dos piernas deben pedir la misma altura.
            fase = 0.5

            def diferencia(k):
                self.k = k
                z_atras = self._resolver_apoyo("Left Leg", fase)[0]
                z_delante = self._resolver_apoyo("Right Leg", fase)[0]
                return z_atras - z_delante

        else:
            # Correr: la pierna despega con el ángulo pedido.
            fase = self.apoyo
            objetivo = math.radians(self.p["alfa_despegue"])

            def diferencia(k):
                self.k = k
                return self._resolver_apoyo("Left Leg", fase)[2][1] - objetivo

        bajo, alto = -4.0, 4.0
        d_bajo = diferencia(bajo)
        for _ in range(60):
            medio = (bajo + alto) / 2
            d = diferencia(medio)
            if (d > 0) == (d_bajo > 0):
                bajo, d_bajo = medio, d
            else:
                alto = medio
        self.k = (bajo + alto) / 2

    # ------------------------------------------------------------------ pierna en el aire
    def _angulos_apoyo(self, pierna, fase):
        info = self._resolver_apoyo(pierna, fase)[2]
        return info[1], info[2]

    def _preparar_aire(self):
        """Ángulos y velocidades de cada pierna al despegar y al aterrizar (para empalmar la curva del aire)."""
        d = 1e-4
        self.aire = {}
        for pierna, ini in self.inicio.items():
            despegue = ini + self.apoyo
            aterriza = ini + 1.0
            a0, g0 = self._angulos_apoyo(pierna, despegue - 1e-7)
            a0m, g0m = self._angulos_apoyo(pierna, despegue - d)
            a1, g1 = self._angulos_apoyo(pierna, aterriza + 1e-7)
            a1p, g1p = self._angulos_apoyo(pierna, aterriza + d)
            self.aire[pierna] = dict(
                inicio=despegue,
                dur=1.0 - self.apoyo,
                a0=a0,
                ma0=(a0 - a0m) / d,
                a1=a1,
                ma1=(a1p - a1) / d,
                g0=g0,
                mg0=(g0 - g0m) / d,
                g1=g1,
                mg1=(g1p - g1) / d,
            )

    def _pierna_aire(self, pierna, fase):
        a = self.aire[pierna]
        s = ((fase - a["inicio"]) % 1.0) / a["dur"]
        dur = a["dur"]
        # `inercia` < 1: la pierna frena antes tras despegar (como si doblara la rodilla) y adelanta antes
        inercia = self.p.get("inercia", 1.0)
        claves = self.p.get("aire_claves")
        if claves:
            # Curva por claves intermedias (s, grados), empalmada con la velocidad del pie al despegar y al aterrizar.
            pts = [(0.0, a["a0"])] + [(sk, math.radians(ak)) for sk, ak in claves] + [(1.0, a["a1"])]
            pend = [a["ma0"] * dur * inercia]
            for i in range(1, len(pts) - 1):
                pend.append((pts[i + 1][1] - pts[i - 1][1]) / (pts[i + 1][0] - pts[i - 1][0]))
            pend.append(a["ma1"] * dur)
            i = max(j for j in range(len(pts) - 1) if pts[j][0] <= s) if s < 1 else len(pts) - 2
            (s0, p0), (s1, p1) = pts[i], pts[i + 1]
            h = s1 - s0
            alfa = ciclo.hermite(p0, pend[i] * h, p1, pend[i + 1] * h, (s - s0) / h)
        else:
            alfa = ciclo.hermite(a["a0"], a["ma0"] * dur * inercia, a["a1"], a["ma1"] * dur, s)
            # `alcance_aire`: empuje extra hacia delante en mitad del vuelo de la pierna (zancada más larga)
            alfa += math.radians(self.p["alcance_aire"]) * math.sin(math.pi * s) ** 2
        gamma = ciclo.hermite(a["g0"], a["mg0"] * dur, a["g1"], a["mg1"] * dur, s)
        # abrir la pierna hacia fuera en mitad del vuelo para que la bota no roce el suelo
        lado = ciclo.PIERNAS[pierna]
        gamma += -lado * math.radians(self.p["abrir_aire"]) * math.sin(math.pi * s) ** 2
        return ciclo.rot_pierna(alfa, gamma)

    # ------------------------------------------------------------------ fase de vuelo (correr)
    def _altura_apoyo(self, fase):
        for pierna in self.inicio:
            if self._en_apoyo(pierna, fase) is not None:
                return self._resolver_apoyo(pierna, fase)[0]
        return None

    def _preparar_vuelo(self):
        self.vuelo = None
        if self.apoyo >= 0.5 - 1e-9:
            return
        d = 1e-4
        f0 = self.apoyo  # despega la izquierda
        f1 = 0.5  # aterriza la derecha
        z0 = self._altura_apoyo(f0 - 1e-7)
        v0 = (z0 - self._altura_apoyo(f0 - d)) / (d * self.T)  # studs/s
        z1 = self._altura_apoyo(f1 + 1e-7)
        t = (f1 - f0) * self.T
        g = 2 * (z0 + v0 * t - z1) / t**2  # gravedad que hace caer justo en el aterrizaje
        self.vuelo = dict(f0=f0, z0=z0, v0=v0, g=g, t=t, v1=v0 - g * t, z1=z1)

    def _altura_vuelo(self, fase):
        v = self.vuelo
        tt = ((fase - v["f0"]) % 0.5) * self.T
        return v["z0"] + v["v0"] * tt - 0.5 * v["g"] * tt * tt

    # ------------------------------------------------------------------ pose completa
    def calcular_pose(self, fotograma):
        fase = (fotograma % self.n) / self.n
        p = self.p
        pose = self._torso(fase)

        apoyadas = [pi for pi in self.inicio if self._en_apoyo(pi, fase) is not None]
        rot_piernas = {}
        if apoyadas:
            principal = apoyadas[0]
            sube, q, _ = self._resolver_apoyo(principal, fase, pose)
            rot_piernas[principal] = q
        else:
            sube = self._altura_vuelo(fase)
        pose.loc["Torso"].z = sube
        for pierna in self.inicio:
            if pierna in apoyadas and pierna not in rot_piernas:
                rot_piernas[pierna] = self._resolver_apoyo(pierna, fase, pose)[1]
            if pierna not in rot_piernas:
                rot_piernas[pierna] = self._pierna_aire(pierna, fase)
            pose.poner_rot_mundo(pierna, rot_piernas[pierna])

        # Brazos: en el sistema del torso, con retraso (los brazos van "arrastrados" por el cuerpo).
        rot_t = pose.mundo("Torso")[1]
        for brazo, lado in ciclo.BRAZOS.items():
            desfase = 0.0 if lado < 0 else 0.5  # el derecho va con la pierna izquierda
            f_b = fase + desfase - p["retraso_brazos"]
            adelante, fuera, giro = ciclica(p["brazo"], f_b)
            d = ciclo.dir_brazo(adelante, fuera, lado)
            ciclo.apuntar(pose, brazo, rot_t @ d)
            # giro del brazo sobre su eje (la palma mira hacia dentro al ir delante)
            q_eje = ciclo.Quaternion(d, math.radians(giro) * -lado)
            pose.poner_rot_mundo(brazo, rot_t @ q_eje @ rot_t.inverted() @ pose.mundo(brazo)[1])

        # Cabeza: compensa parte del giro e inclinación del torso (la mirada se queda al frente).
        cab = ciclica(p["cabeza"], fase - p["retraso_cabeza"])
        pose.q["Head"] = ciclo.rot_torso(*cab)
        return pose

    # ------------------------------------------------------------------ comprobaciones
    def metricas(self):
        """Mide lo que importa: que el pie apoyado no patine ni se hunda y que el del aire no roce el suelo."""
        hundido = 0.0  # lo más que se mete una bota en el suelo (cualquier pierna)
        flota = 0.0  # lo más que flota la bota apoyada
        roce = 9.0  # lo más cerca del suelo que pasa la bota en el aire (lejos del despegue/aterrizaje)
        patina = 0.0  # cuánto se aleja la arista clavada (talón o punta) de donde debe estar en la cinta
        sub = 4  # submuestreo: se mira también entre fotogramas
        anteriores = {}
        alturas = []
        for i in range(self.n * sub):
            f = i / sub
            fase = f / self.n
            pose = self.calcular_pose(f)
            alturas.append(pose.loc["Torso"].z)
            for pierna in self.inicio:
                m = ciclo.suelo_minimo(pose, pierna)
                hundido = max(hundido, -m)
                u = self._en_apoyo(pierna, fase)
                if u is not None:
                    flota = max(flota, m)
                    fase_pie = self._resolver_apoyo(pierna, fase)[2][0]
                    if fase_pie in ("talon", "punta"):
                        lado = ciclo.PIERNAS[pierna]
                        local = Vector((-0.5 * lado, ciclo.TALON_Y if fase_pie == "talon" else ciclo.PUNTA_Y, -2))
                        w = ciclo.punto_mundo(pose, pierna, local)
                        clave = (pierna, fase_pie, round((fase - self.inicio[pierna]) % 1.0 // self.apoyo))
                        if clave in anteriores:
                            f_prev, w_prev = anteriores[clave]
                            esperado = w_prev + Vector((0, self.v * (f - f_prev) / self.fps, 0))
                            patina = max(patina, (Vector((w.x, w.y, w.z)) - esperado).length)
                        anteriores[clave] = (f, w)
                else:
                    a = self.aire[pierna]
                    s = ((fase - a["inicio"]) % 1.0) / a["dur"]
                    if 0.15 < s < 0.85:
                        roce = min(roce, m)
        return dict(
            hundido=hundido,
            flota=flota,
            roce=roce,
            patina=patina,
            sube_baja=max(alturas) - min(alturas),
            k=self.k,
            vuelo=self.vuelo,
        )


def comprobar_bucle(calcular_pose, n):
    """Diferencia entre el fotograma n y el 0 (debe ser 0) y salto máximo entre fotogramas seguidos (studs)."""
    a, b = calcular_pose(0), calcular_pose(n)
    cierre = max((a.mundo(h)[0] - b.mundo(h)[0]).length for h in r6.ARTICULACIONES)
    cierre = max(cierre, max((a.q[h].rotation_difference(b.q[h]).angle) for h in r6.ARTICULACIONES))
    return cierre
