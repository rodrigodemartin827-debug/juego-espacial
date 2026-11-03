"""
Relieve del planeta de prueba: una función continua de la dirección (un vector unitario) a una altura en studs sobre
el nivel del mar. Solo usa numpy, así que se puede probar sin Blender.

Por qué una función y no una malla esculpida: cada vértice de cada trozo pide su altura a esta función, así que dos
trozos vecinos dan EXACTAMENTE la misma altura (y la misma normal) en su borde. No hay costuras, y el relieve no
depende de cómo se parta la esfera.

El relieve se construye con capas, todas suaves (sin escalones ni valores discretos):
  1. Continentes: ruido de muy baja frecuencia, con la dirección deformada para que no salgan manchas redondas.
     Un umbral reparte tierra y mar; la altura base sube suave tierra adentro (tanh) y baja suave mar adentro.
  2. Colinas: ruido de media frecuencia, solo en tierra.
  3. Cordilleras: ruido «de crestas» (1 - |ruido|) elevado al cuadrado, solo en el interior de los continentes y
     donde otro ruido lo permite, para que haya sierras y llanuras y no montañas por todas partes.
  4. Valles: surcos estrechos a lo largo de los cruces por cero de otro ruido; cavan la tierra en meandros.

Las alturas están en studs sobre el nivel del mar (el radio nominal de la esfera).
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Parametros:
    semilla: int = 7
    # Fracción aproximada de la superficie que es tierra.
    fraccion_tierra: float = 0.38
    # Amplitudes en studs.
    playa: float = 6.0  # altura que sube la tierra en la playa (subida corta)
    llanura: float = 52.0  # altura a la que tiende después, muy gradualmente
    plataforma: float = 10.0  # profundidad de la plataforma continental, junto a la costa
    fondo_marino: float = 125.0  # profundidad a la que tiende el fondo, lejos de la costa
    base_activa: bool = True
    colinas: float = 13.0
    montanas: float = 215.0
    valles: float = 15.0
    # Frecuencias (ciclos por radio de planeta).
    f_continentes: float = 1.25
    f_colinas: float = 8.0
    f_cordilleras: float = 2.8
    f_mascara_cordilleras: float = 2.4
    f_valles: float = 3.6


# --------------------------------------------------------------------------------------------------------------
# Ruido de Perlin 3D vectorizado
# --------------------------------------------------------------------------------------------------------------

_GRADIENTES = np.array(
    [(1, 1, 0), (-1, 1, 0), (1, -1, 0), (-1, -1, 0), (1, 0, 1), (-1, 0, 1), (1, 0, -1), (-1, 0, -1),
     (0, 1, 1), (0, -1, 1), (0, 1, -1), (0, -1, -1)],
    dtype=np.float64,
)


class Ruido:
    """Perlin 3D con tabla de permutaciones propia (determinista según la semilla)."""

    def __init__(self, semilla: int):
        rng = np.random.default_rng(semilla)
        p = rng.permutation(256).astype(np.int64)
        self.perm = np.concatenate([p, p])
        # Una rotación aleatoria por octava: evita que las capas se alineen con los ejes de la cuadrícula.
        self.rotaciones = []
        self.desplazamientos = []
        for _ in range(12):
            q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
            self.rotaciones.append(q)
            self.desplazamientos.append(rng.uniform(0, 200, size=3))

    def perlin(self, p: np.ndarray) -> np.ndarray:
        """p: (n, 3). Devuelve (n,) en aproximadamente [-1, 1]."""
        xi = np.floor(p).astype(np.int64)
        f = p - xi
        u = f * f * f * (f * (f * 6 - 15) + 10)  # curva quíntica: continuidad C2
        x0, y0, z0 = xi[:, 0] & 255, xi[:, 1] & 255, xi[:, 2] & 255
        x1, y1, z1 = (x0 + 1) & 255, (y0 + 1) & 255, (z0 + 1) & 255
        perm = self.perm

        def esquina(ix, iy, iz, fx, fy, fz):
            h = perm[perm[perm[ix] + iy] + iz] % 12
            g = _GRADIENTES[h]
            return g[:, 0] * fx + g[:, 1] * fy + g[:, 2] * fz

        fx, fy, fz = f[:, 0], f[:, 1], f[:, 2]
        n000 = esquina(x0, y0, z0, fx, fy, fz)
        n100 = esquina(x1, y0, z0, fx - 1, fy, fz)
        n010 = esquina(x0, y1, z0, fx, fy - 1, fz)
        n110 = esquina(x1, y1, z0, fx - 1, fy - 1, fz)
        n001 = esquina(x0, y0, z1, fx, fy, fz - 1)
        n101 = esquina(x1, y0, z1, fx - 1, fy, fz - 1)
        n011 = esquina(x0, y1, z1, fx, fy - 1, fz - 1)
        n111 = esquina(x1, y1, z1, fx - 1, fy - 1, fz - 1)
        ux, uy, uz = u[:, 0], u[:, 1], u[:, 2]
        nx00 = n000 + ux * (n100 - n000)
        nx10 = n010 + ux * (n110 - n010)
        nx01 = n001 + ux * (n101 - n001)
        nx11 = n011 + ux * (n111 - n011)
        nxy0 = nx00 + uy * (nx10 - nx00)
        nxy1 = nx01 + uy * (nx11 - nx01)
        return (nxy0 + uz * (nxy1 - nxy0)) * 1.15  # el Perlin 3D da ~[-0,87, 0,87]: se normaliza a ~[-1, 1]

    def fbm(self, d: np.ndarray, frecuencia: float, octavas: int, ganancia: float = 0.5, capa: int = 0) -> np.ndarray:
        """Suma de octavas. `capa` elige otra familia de rotaciones y desplazamientos (otro «campo» de ruido)."""
        total = np.zeros(len(d))
        amp, norma = 1.0, 0.0
        for o in range(octavas):
            k = (capa * 3 + o) % len(self.rotaciones)
            p = (d @ self.rotaciones[k].T) * (frecuencia * 2.0 ** o) + self.desplazamientos[k]
            total += amp * self.perlin(p)
            norma += amp
            amp *= ganancia
        return total / norma


def suavizar(x: np.ndarray, a: float, b: float) -> np.ndarray:
    """smoothstep: 0 por debajo de a, 1 por encima de b, con derivada continua entre medias."""
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------------------------------------------
# El relieve
# --------------------------------------------------------------------------------------------------------------


class Relieve:
    def __init__(self, parametros: Parametros = Parametros()):
        self.p = parametros
        self.ruido = Ruido(parametros.semilla)
        self.umbral = 0.0
        self._calibrar_umbral()

    def _continente(self, d: np.ndarray) -> np.ndarray:
        r = self.ruido
        # Deformación de dominio: desplaza la dirección con otro ruido para que las costas sean sinuosas.
        w = np.stack([r.fbm(d, 1.8, 3, capa=1), r.fbm(d, 1.8, 3, capa=2), r.fbm(d, 1.8, 3, capa=3)], axis=1)
        return r.fbm(d + 0.28 * w, self.p.f_continentes, 5, ganancia=0.45, capa=0)

    def _calibrar_umbral(self) -> None:
        """Busca el umbral que deja la fracción de tierra pedida (con una muestra uniforme de la esfera)."""
        rng = np.random.default_rng(self.p.semilla + 1)
        m = rng.normal(size=(40000, 3))
        m /= np.linalg.norm(m, axis=1, keepdims=True)
        self.umbral = float(np.quantile(self._continente(m), 1.0 - self.p.fraccion_tierra))

    def altura(self, d: np.ndarray) -> np.ndarray:
        """d: (n, 3) vectores unitarios. Devuelve la altura en studs sobre el nivel del mar, (n,)."""
        p, r = self.p, self.ruido
        x = self._continente(d) - self.umbral  # > 0 en tierra
        # Altura base, con la misma pendiente a los dos lados de la costa (sin quiebro en la orilla).
        # Cada lado es la suma de una subida corta (playa / plataforma) y otra larga (llanura / fondo). Los anchos
        # están elegidos para que la pendiente en x = 0 sea la misma a los dos lados: sin quiebro en la orilla.
        tierra = p.playa * np.tanh(x / 0.03) + p.llanura * np.tanh(x / 0.35)
        mar = p.plataforma * np.tanh(x / 0.05) + p.fondo_marino * np.tanh(x / 0.855)
        base = np.where(x > 0, tierra, mar) if p.base_activa else np.zeros_like(x)

        interior = suavizar(x, 0.02, 0.22)  # 0 en la costa, 1 tierra adentro
        tierra_firme = suavizar(x, -0.03, 0.07)  # un poco más ancha: las colinas empiezan antes de la costa

        colinas = p.colinas * r.fbm(d, p.f_colinas, 3, ganancia=0.4, capa=4) * (0.25 + 0.75 * tierra_firme)

        # Cordilleras: crestas suaves (raíz de x² + ε² en lugar de |x|, para que la cresta no sea una arista).
        k = r.fbm(d, p.f_cordilleras, 3, ganancia=0.38, capa=5)
        cresta = 1.0 - np.sqrt(k * k + 0.05) / 0.62
        cresta = np.clip(cresta, 0.0, 1.0) ** 1.5
        donde = suavizar(r.fbm(d, p.f_mascara_cordilleras, 3, capa=6), -0.10, 0.30)
        montanas = p.montanas * cresta * donde * interior

        # Valles: surcos a lo largo del cruce por cero de un ruido (curva sinuosa), solo en tierra y atenuados donde
        # hay cordillera para que no se coman las montañas.
        v = r.fbm(d, p.f_valles, 3, capa=7)
        surco = np.exp(-((v / 0.2) ** 2))
        valles = -p.valles * surco * tierra_firme * (1.0 - 0.7 * donde)

        return base + colinas + montanas + valles


def a_unitarios(v: np.ndarray) -> np.ndarray:
    return v / np.linalg.norm(v, axis=-1, keepdims=True)
