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
    "09_molinos_suelo": (lambda: punto_sitio("LosMolinos", -125, -30, 5.5),
                         lambda: punto_sitio("LosMolinos", -20, 30, 24), "dia", 26, None),
    "10_colina_atardecer": (lambda: mirador(-15, -1, 6.5), hacia(lambda: mirador(-15, -1, 6.5), 266.0, -11.0),
                            "atardecer", 24, None),
    "11_colina_desde_el_prado_atardecer": (lambda: punto_diseno(360, -125, 5.5),
                                           hacia(lambda: punto_diseno(360, -125, 5.5), 70.0, 5.0),
                                           "atardecer", 30, None),
    "12_puente_suelo": (lambda: puente(-20, -62, 4.5), lambda: puente(0, 0, 2), "dia", 28, None),
    "13_valle_desde_colina": (lambda: mirador(-15, 4, 6), hacia(lambda: mirador(-15, 4, 6), 296.0, -15.0),
                              "manana", 28, None),
}


# El planeta de los monstruos, visto en el cielo (CLAUDE.md: «desde tu planeta se ve el otro mundo a lo lejos»).
# Solo de referencia para los renders: (rumbo, elevación) en grados en el marco del sitio, tamaño aparente en grados.
OTRO_MUNDO = dict(rumbo=250.0, elevacion=5.0, tamano=5.5, distancia=45000.0, color="#2A1838", halo="#9B5CFF")


def otro_mundo(visible):
    ob = bpy.data.objects.get("Planeta_Monstruos_referencia")
    if ob is None:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=48, radius=1.0)
        ob = bpy.context.active_object
        ob.name = "Planeta_Monstruos_referencia"
        for p in ob.data.polygons:
            p.use_smooth = True
        mat = bpy.data.materials.new("Planeta_Monstruos")
        nt = mat.node_tree
        nt.nodes.clear()
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (*MAT.srgb_a_lineal(OTRO_MUNDO["color"]), 1)
        bsdf.inputs["Roughness"].default_value = 0.8
        # halo violeta en el borde (atmósfera)
        lw = nt.nodes.new("ShaderNodeLayerWeight")
        lw.inputs["Blend"].default_value = 0.35
        em = nt.nodes.new("ShaderNodeEmission")
        em.inputs["Color"].default_value = (*MAT.srgb_a_lineal(OTRO_MUNDO["halo"]), 1)
        pw = nt.nodes.new("ShaderNodeMath")
        pw.operation = "POWER"
        pw.inputs[1].default_value = 2.5
        nt.links.new(lw.outputs["Facing"], pw.inputs[0])
        mul = nt.nodes.new("ShaderNodeMath")
        mul.operation = "MULTIPLY"
        mul.inputs[1].default_value = 3.0
        nt.links.new(pw.outputs[0], mul.inputs[0])
        nt.links.new(mul.outputs[0], em.inputs["Strength"])
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(bsdf.outputs[0], add.inputs[0])
        nt.links.new(em.outputs[0], add.inputs[1])
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(add.outputs[0], out.inputs["Surface"])
        ob.data.materials.append(mat)
    ob.hide_render = not visible
    return ob


def colocar_otro_mundo(cam):
    o = OTRO_MUNDO
    r, e = math.radians(o["rumbo"]), math.radians(o["elevacion"])
    d = np.array([math.cos(e) * math.sin(r), math.cos(e) * math.cos(r), math.sin(e)])  # marco del mundo = sitio
    ob = otro_mundo(True)
    ob.location = tuple(cam + d * o["distancia"])
    radio = o["distancia"] * math.tan(math.radians(o["tamano"] / 2))
    ob.scale = (radio, radio, radio)


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
    E.camara(tuple(cam), tuple(obj), tuple(arriba_cam), lente, recorte=(0.3, 60000.0))
    E.iluminar(ilum)
    if ilum == "atardecer":
        colocar_otro_mundo(cam)
    else:
        otro_mundo(False)
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
