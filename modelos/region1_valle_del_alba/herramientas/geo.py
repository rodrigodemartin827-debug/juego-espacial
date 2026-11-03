"""
Geometría de la región: la cara del cubo-esfera, las coordenadas de diseño y los marcos locales. Solo numpy.

El planeta es el de modelos/planeta_prueba: radio 2400 studs, cubo-esfera con reparto «de ángulos iguales». La región 1
(Valle del Alba) ocupa la cara YP (la normal +Y de Roblox, el «polo de arriba»).

Tres sistemas de coordenadas:

  * Roblox: Y arriba, en studs. Es el del planeta de prueba y el de la exportación futura.
  * Blender: Z arriba. Roblox (x, y, z) -> Blender (x, -z, y). Así la cara YP queda arriba, centrada en (0, 0, R).
  * Diseño (x, y): plano de la cara, en studs. x = R·β (hacia el «este», +X de Blender) e y = R·α' (hacia el
    «norte», +Y de Blender), donde β y α' son los ángulos del reparto de ángulos iguales. Van de -L a L con
    L = R·π/4 ≈ 1885 studs. Sobre los ejes de la cara la distancia es exacta; cerca de las esquinas se estira un poco
    (no importa: los pueblos están en el centro y se colocan con marcos locales exactos, ver abajo).

Los pueblos se diseñan en coordenadas LOCALES (u, v) de su plano tangente (proyección gnomónica desde su centro):
un edificio a (u, v) = (30, 0) está a 30 studs reales al este del centro del pueblo, sin deformación.
"""

import math

import numpy as np

RADIO = 2400.0
L = RADIO * math.pi / 4.0  # semilado de la cara en coordenadas de diseño


def direccion(x, y):
    """Coordenadas de diseño -> dirección unitaria en Blender. Acepta escalares o arrays; devuelve (..., 3)."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    p = np.stack([np.tan(x / RADIO), np.tan(y / RADIO), np.ones_like(x)], axis=-1)
    return p / np.linalg.norm(p, axis=-1, keepdims=True)


def diseno(d):
    """Dirección (Blender, con z > 0) -> coordenadas de diseño (x, y)."""
    d = np.asarray(d, dtype=np.float64)
    return RADIO * np.arctan2(d[..., 0], d[..., 2]), RADIO * np.arctan2(d[..., 1], d[..., 2])


def blender_a_roblox(v):
    v = np.asarray(v, dtype=np.float64)
    return np.stack([v[..., 0], v[..., 2], -v[..., 1]], axis=-1)


def marco(d):
    """Marco local (este, norte, arriba) en una dirección d (Blender). El este sigue el eje +X de diseño."""
    d = np.asarray(d, dtype=np.float64)
    arriba = d / np.linalg.norm(d)
    # El este es la derivada de la posición respecto a x, ortogonalizada.
    x, y = diseno(arriba)
    e = direccion(x + 1.0, y) - direccion(x - 1.0, y)
    e = e - np.dot(e, arriba) * arriba
    e /= np.linalg.norm(e)
    n = np.cross(arriba, e)
    return e, n, arriba


class Sitio:
    """Plano tangente de un sitio (pueblo, ciudad): pasa de (u, v) locales a direcciones y al revés."""

    def __init__(self, x: float, y: float):
        self.x, self.y = x, y
        self.centro = direccion(x, y)
        self.este, self.norte, self.arriba = marco(self.centro)

    def direccion(self, u, v):
        u = np.asarray(u, dtype=np.float64)
        v = np.asarray(v, dtype=np.float64)
        p = self.arriba * RADIO + u[..., None] * self.este + v[..., None] * self.norte
        return p / np.linalg.norm(p, axis=-1, keepdims=True)

    def local(self, d):
        """Dirección(es) -> (u, v) en studs (proyección gnomónica sobre el plano tangente a radio R)."""
        d = np.asarray(d, dtype=np.float64)
        k = RADIO / np.clip(d @ self.arriba, 1e-6, None)
        return (d @ self.este) * k, (d @ self.norte) * k

    def diseno(self, u, v):
        return diseno(self.direccion(u, v))


def suavizar(x, a, b):
    """smoothstep: 0 por debajo de a, 1 por encima de b (vale también con a > b, al revés)."""
    t = np.clip((np.asarray(x, dtype=np.float64) - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)
