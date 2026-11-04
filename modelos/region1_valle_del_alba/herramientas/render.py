"""
Renders de revisión de la región 1. Abre region1_valle_del_alba.blend, coloca la cámara y la luz de cada vista y
renderiza con Cycles. Las vistas están en VISTAS (todo ajustable aquí).

Uso:
    python modelos/region1_valle_del_alba/herramientas/render.py --blend modelos/region1_valle_del_alba/region1_valle_del_alba.blend
        --salida modelos/region1_valle_del_alba/renders [--vistas 01,04] [--ancho 1920] [--muestras 96]
"""

import argparse
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import numpy as np  # noqa: E402

import diseno as D  # noqa: E402
import escena as E  # noqa: E402
import geo  # noqa: E402
import materiales as MAT  # noqa: E402
import relieve as RV  # noqa: E402

R = geo.RADIO
_V = None


def valle():
    global _V
    if _V is None:
        _V = RV.Valle()
    return _V


def altura(x, y):
    return float(valle().altura(np.array([x]), np.array([y]))[0])


def punto_diseno(x, y, sobre=0.0, absoluta=None):
    """Punto del mundo sobre el terreno en (x, y) de diseño: `sobre` studs por encima del suelo (o altura absoluta)."""
    d = geo.direccion(x, y)
    h = altura(x, y) if absoluta is None else absoluta
    return d * (R + h + (sobre if absoluta is None else 0.0))


def punto_sitio(sitio, u, v, sobre=0.0):
    s = valle().sitios[sitio]
    d = s.direccion(np.array(u), np.array(v))
    x, y = geo.diseno(d)
    return punto_diseno(float(x), float(y), sobre)


def mirador(u, v, sobre):
    x, y = D.MIRADOR
    d = geo.direccion(x, y)
    e, n, _ = geo.marco(d)
    p = d * R + u * e + v * n
    p /= np.linalg.norm(p)
    xx, yy = geo.diseno(p)
    return punto_diseno(float(xx), float(yy), sobre)


def puente(u, v, sobre):
    x, y = D.PUENTE["x"], D.PUENTE["y"]
    return punto_diseno(x + u, y + v, sobre)


def hacia(f_cam, rumbo, cabeceo, dist=800.0):
    """Objetivo a `dist` studs de la cámara, en el rumbo (grados desde el norte hacia el este) y el cabeceo dados
    (grados, negativo = hacia abajo), medidos en el marco local de la cámara."""

    def f():
        p = f_cam()
        e, n, u = geo.marco(p / np.linalg.norm(p))
        r, c = math.radians(rumbo), math.radians(cabeceo)
        return p + dist * (math.cos(c) * (math.sin(r) * e + math.cos(r) * n) + math.sin(c) * u)

    f.marco_camara = True
    return f


# nombre: (cámara, objetivo, iluminación, lente, niebla opcional (inicio, distancia, máximo))
# Si el objetivo se da con hacia(), el planeta se orienta con la vertical de la cámara; si no, con la del objetivo.
VISTAS = {
    "00_planeta_region": (lambda: punto_diseno(150, -2500, absoluta=2300), lambda: punto_diseno(0, 0, absoluta=0),
                          "dia", 26, (900.0, 9000.0, 0.45)),
    "01_region_aerea": (lambda: punto_diseno(250, -1900, absoluta=950), lambda: punto_diseno(0, 250, absoluta=0),
                        "dia", 24, (700.0, 6000.0, 0.5)),
    "02_region_cenital": (lambda: punto_diseno(0, 0, absoluta=4400), lambda: punto_diseno(0, 1, absoluta=0),
                          "dia", 30, (2000.0, 20000.0, 0.3)),
    "03_aurora_aerea": (lambda: punto_sitio("Aurora", -300, -380, 230), lambda: punto_sitio("Aurora", 0, 10, 0),
                        "dia", 35, (350.0, 4000.0, 0.45)),
    "04_aurora_plaza_suelo": (lambda: punto_sitio("Aurora", 2, -40, 5.5),
                              lambda: punto_sitio("Aurora", -2, 50, 16), "dia", 22, None),
    "05_aurora_calle_mayor": (lambda: punto_sitio("Aurora", 178, -3, 5.5), lambda: punto_sitio("Aurora", 40, 0, 10),
                              "manana", 28, None),
    "06_pradoverde_aerea": (lambda: punto_sitio("Pradoverde", -140, -150, 105),
                            lambda: punto_sitio("Pradoverde", 5, 5, 0), "dia", 35, (250.0, 4000.0, 0.45)),
    "07_pradoverde_suelo": (lambda: punto_sitio("Pradoverde", -58, -10, 5.5),
                            lambda: punto_sitio("Pradoverde", 30, 6, 8), "manana", 24, None),
    "08_molinos_aerea": (lambda: punto_sitio("LosMolinos", -250, -250, 140),
                         lambda: punto_sitio("LosMolinos", 0, 0, 10), "dia", 35, (300.0, 4000.0, 0.45)),
    "09_molinos_suelo": (lambda: punto_sitio("LosMolinos", -70, 4, 5.5),
                         lambda: punto_sitio("LosMolinos", -30, 34, 30), "dia", 26, None),
    "10_colina_atardecer": (lambda: mirador(6, 0, 6.5), hacia(lambda: mirador(6, 0, 6.5), 266.0, -8.0),
                            "atardecer", 24, None),
    "11_colina_desde_el_prado_atardecer": (lambda: punto_diseno(360, -125, 5.5),
                                           hacia(lambda: punto_diseno(360, -125, 5.5), 70.0, 5.0),
                                           "atardecer", 30, None),
    "12_puente_suelo": (lambda: puente(-34, -58, 4.5), lambda: puente(0, 0, 2), "dia", 26, None),
    "13_valle_desde_colina": (lambda: mirador(-12, 0, 7), hacia(lambda: mirador(-12, 0, 7), 280.0, -11.0),
                              "manana", 28, None),
}


def preparar(blend):
    bpy.ops.wm.open_mainfile(filepath=blend)


def renderizar(nombre, salida, ancho, muestras):
    cam_f, obj_f, ilum, lente, niebla = VISTAS[nombre]
    cam = cam_f()
    obj = obj_f()
    # El planeta se gira para que la vertical del punto que se mira sea +Z (el cielo y el sol quedan bien puestos).
    ref = cam if getattr(obj_f, "marco_camara", False) else obj
    e, n, u = geo.marco(ref / np.linalg.norm(ref))
    rot = np.array(E.orientar_planeta(tuple(e), tuple(n), tuple(u)))
    cam, obj = rot @ cam, rot @ obj
    arriba_cam = cam / np.linalg.norm(cam)
    E.configurar_render(ancho, int(ancho * 9 / 16), muestras)
    E.camara(tuple(cam), tuple(obj), tuple(arriba_cam), lente, recorte=(0.3, 30000.0))
    E.iluminar(ilum)
    if niebla:
        ini, dist, mx = niebla
        col = E.ILUMINACIONES[ilum]["niebla"][3]
        MAT.ajustar_niebla(ini, dist, mx, MAT.srgb_a_lineal(col))
    ruta = os.path.abspath(os.path.join(salida, nombre + ".png"))
    t = time.time()
    E.render(ruta)
    print(f"{nombre}: {time.time() - t:.0f} s -> {ruta}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--vistas", default="")
    ap.add_argument("--ancho", type=int, default=1920)
    ap.add_argument("--muestras", type=int, default=96)
    a = ap.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
    os.makedirs(a.salida, exist_ok=True)
    preparar(os.path.abspath(a.blend))
    vistas = [v for v in VISTAS if not a.vistas or any(v.startswith(p) for p in a.vistas.split(","))]
    for v in vistas:
        renderizar(v, a.salida, a.ancho, a.muestras)


if __name__ == "__main__":
    main()
