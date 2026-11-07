"""
Hoja de contactos del PORTAL: cada fase (disparo, apertura, abierto, cierre) de la pistola normal (chatarra) y de la VIP,
una fila debajo de la otra, con el tirador (disparo) y un R6 de cajas al lado del portal para ver el tamaño.

Dibuja las mallas de modelos/pistola_portales/vfx (anillo, borde, remolino con su textura, onda, proyectil, fogonazo) con
las curvas de portal_fases.py (que son las que hay que montar en Roblox) y, para las chispas y el destello, rayitas y un
sprite con las texturas de partículas. Lleva el resplandor (bloom) hecho con Pillow.

Uso:  python animaciones/pistola/herramientas/generar_portal.py --salida modelos/pistola_portales/vfx --ronda 5 [--rapido]
"""

import argparse
import math
import os
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
sys.path.insert(1, os.path.join(AQUI, "..", "..", "movimiento", "herramientas"))
sys.path.insert(2, os.path.join(AQUI, "..", "..", "herramientas"))

import bpy  # noqa: E402  (antes que mathutils)
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image  # noqa: E402

import disparo as D  # noqa: E402
import pistola_escena as PE  # noqa: E402
import portal_fases as PF  # noqa: E402
import render_mov  # noqa: E402
import rig_r6 as r6  # noqa: E402

E = r6.ESTUDIO
DISTANCIA = 14.0  # studs desde el tirador hasta donde se abre el portal
CENTRO = Vector((0.0, -DISTANCIA, 3.2))  # centro del portal (studs): el borde de abajo roza el suelo
TEXTURAS = os.path.join(PE.MODELOS, "vfx", "texturas")
NOMBRES = {"chatarra": "Chatarra", "vip": "VIP"}


def _material_remolino(ruta_png, fuerza=2.2):
    """Emisión con la textura del remolino y su alfa como transparencia."""
    m = bpy.data.materials.new("remolino")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    salida = nt.nodes.new("ShaderNodeOutputMaterial")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(ruta_png)
    tex.extension = "CLIP"
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = fuerza
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mezcla = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(tex.outputs["Color"], em.inputs["Color"])
    nt.links.new(tex.outputs["Alpha"], mezcla.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mezcla.inputs[1])
    nt.links.new(em.outputs["Emission"], mezcla.inputs[2])
    nt.links.new(mezcla.outputs["Shader"], salida.inputs["Surface"])
    m["emision"] = em.name
    m["alfa"] = mezcla.name
    return m


def _material_sprite(ruta_png, color, fuerza=8.0):
    """Sprite de partícula: la textura blanca teñida de `color`, con su alfa."""
    m = _material_remolino(ruta_png, fuerza)
    em = m.node_tree.nodes[m["emision"]]
    tex = [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE"][0]
    mul = m.node_tree.nodes.new("ShaderNodeMix")
    mul.data_type = "RGBA"
    mul.blend_type = "MULTIPLY"
    mul.inputs["Factor"].default_value = 1.0
    mul.inputs["B"].default_value = (*PE.srgb(color), 1)
    m.node_tree.links.new(tex.outputs["Color"], mul.inputs["A"])
    m.node_tree.links.new(mul.outputs["Result"], em.inputs["Color"])
    return m


class Portal:
    """Las mallas del portal de una pistola en su sitio, con sus materiales y su estado."""

    def __init__(self, estilo):
        self.estilo = estilo
        nombre = NOMBRES[estilo]
        carpeta = os.path.join(PE.MODELOS, "vfx", estilo)
        import json

        with open(os.path.join(carpeta, f"Portal_{nombre}.json"), encoding="utf-8") as f:
            datos = json.load(f)
        objs = PE._importar_fbx(os.path.join(carpeta, f"Portal_{nombre}.fbx"))
        self.partes = {o.name: o for o in objs if o.type == "MESH"}
        for o in objs:
            if o.type == "EMPTY":
                bpy.data.objects.remove(o)
        self.neon = {}
        for n, o in self.partes.items():
            o.data.materials.clear()
            uso = datos["piezas"][n]
            if "Remolino" in n or "Fondo" in n:
                o.data.materials.append(_material_remolino(os.path.join(TEXTURAS, uso["textura"]),
                                                           1.0 if "Remolino" in n else 0.9))
            else:
                m = PE._material_neon(f"p_{n}", uso["color"], 5.0)
                self.neon[n] = m
                o.data.materials.append(m)
        self.sprite = {
            "estrella": _material_sprite(os.path.join(TEXTURAS, "particula_estrella.png"),
                                         "#C8FF8A" if estilo == "chatarra" else "#E8FBFF"),
        }
        bpy.ops.mesh.primitive_plane_add(size=1.0)
        self.destello = bpy.context.active_object
        self.destello.data.materials.append(self.sprite["estrella"])
        self.destello.hide_render = True
        self.temporales = []
        self.mat_chispa = PE._material_neon("chispa_p", "#E6FF7A" if estilo == "chatarra" else "#7FFBFF", 14.0)

    def _brillo(self, nombre, k):
        if nombre in self.neon:
            self.neon[nombre].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 5.0 * max(k, 0.0)

    def mostrar(self, si):
        for o in self.partes.values():
            o.hide_render = not si
        self.destello.hide_render = True
        self.limpiar()

    def limpiar(self):
        for o in self.temporales:
            bpy.data.objects.remove(o)
        self.temporales = []

    def poner(self, fase, t, camara, semilla=1):
        """Coloca todo según el estado de portal_fases en el instante t de la fase."""
        self.limpiar()
        st = PF.estado(self.estilo, fase, t)
        esc = st["escala"]
        base = Matrix.Translation(CENTRO * E)
        for n, o in self.partes.items():
            m = base @ Matrix.Scale(E * esc, 4)
            if "Remolino" in n:
                m = base @ Matrix.Rotation(math.radians(st["giro"]), 4, "Y") @ Matrix.Scale(E * esc, 4)
                em = o.data.materials[0].node_tree.nodes[o.data.materials[0]["emision"]]
                em.inputs["Strength"].default_value = 1.0 * st["remolino"]
                o.hide_render = st["remolino"] < 0.02 or esc < 0.01
            elif "Fondo" in n:
                em = o.data.materials[0].node_tree.nodes[o.data.materials[0]["emision"]]
                em.inputs["Strength"].default_value = 0.9 * st["remolino"]
                o.hide_render = st["remolino"] < 0.02 or esc < 0.01
            elif "Borde" in n:
                m = base @ Matrix.Rotation(math.radians(st["borde"][1]), 4, "Y") @ Matrix.Scale(E * esc * st["borde"][0], 4)
                self._brillo(n, st["anillo"])
                o.hide_render = esc < 0.01
            elif "Onda" in n:
                escw, br = st["onda"]
                m = base @ Matrix.Scale(E * escw, 4)
                self._brillo(n, br)
                o.hide_render = br < 0.02
            elif "Marcas" in n:
                self._brillo(n, st["marcas"])
                o.hide_render = esc < 0.01
            else:  # anillo, interior
                self._brillo(n, st["anillo"])
                o.hide_render = esc < 0.01
            o.matrix_world = m
        # destello: sprite que mira a la cámara
        d = self.destello
        d.hide_render = st["destello"] < 0.05
        tam = st["destello"]
        d.matrix_world = Matrix.Translation(CENTRO * E)
        dirc = (camara.location - CENTRO * E).normalized()
        d.rotation_euler = Vector((0, 0, 1)).rotation_difference(dirc).to_euler()
        d.scale = (tam * E, tam * E, 1)
        # chispas
        for (x, z, vx, vz, largo) in PF.chispas(self.estilo, fase, t, semilla):
            if largo < 0.03:
                continue
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=(CENTRO + Vector((x, 0, z))) * E)
            c = bpy.context.active_object
            v = Vector((vx, 0, vz))
            direc = v.normalized() if v.length > 1e-3 else Vector((0, 0, 1))
            c.scale = (0.05 * E, 0.05 * E, max(largo, 0.08) * E)
            c.rotation_euler = Vector((0, 0, 1)).rotation_difference(direc).to_euler()
            c.data.materials.append(self.mat_chispa)
            self.temporales.append(c)


def maniqui(posicion):
    """R6 de cajas en pie (Torso 2x2x1, brazos y piernas 1x2x1, cabeza) como regla de tamaño."""
    m = bpy.data.materials.new("maniqui")
    m.use_nodes = True
    m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.78, 0.8, 0.86, 1)
    m.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Color"].default_value = (0.6, 0.64, 0.72, 1)  # se lee a contraluz
    m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0.35
    out = []
    for centro, tam in (((0, 0, 3), (2, 1, 2)), ((0, 0, 4.6), (1.2, 1.2, 1.2)), ((1.5, 0, 3), (1, 1, 2)),
                        ((-1.5, 0, 3), (1, 1, 2)), ((0.5, 0, 1), (1, 1, 2)), ((-0.5, 0, 1), (1, 1, 2))):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=(Vector(centro) + posicion) * E)
        o = bpy.context.active_object
        o.scale = (tam[0] * E, tam[1] * E, tam[2] * E)
        o.data.materials.append(m)
        out.append(o)
    return out


def preparar_ambiente():
    """Escena más oscura que la de las animaciones: el neón necesita contraste para verse como en un planeta de noche."""
    scn = bpy.context.scene
    fondo = scn.world.node_tree.nodes["Background"]
    fondo.inputs["Color"].default_value = (0.03, 0.04, 0.07, 1)
    fondo.inputs["Strength"].default_value = 0.6
    scn.objects["sol"].data.energy = 1.1
    suelo = bpy.data.materials["suelo"].node_tree.nodes
    suelo["Checker Texture"].inputs["Color1"].default_value = (0.16, 0.17, 0.2, 1)
    suelo["Checker Texture"].inputs["Color2"].default_value = (0.11, 0.12, 0.15, 1)


def poner_camara(cam, pos, objetivo, lente):
    cam.location = Vector(pos) * E
    cam.data.lens = lente
    bpy.data.objects["mira"].location = Vector(objetivo) * E


VISTAS_CERCA = {
    "3/4": ((-12.0, -DISTANCIA - 12.0, 5.0), (-0.8, -DISTANCIA, 3.0), 50),
    "Eje": ((-4.0, 8.0, 4.5), (-0.8, -DISTANCIA, 3.0), 40),
}
# Planos del disparo: «cerca» del tirador (el fogonazo) y «medio» (el proyectil rumbo al portal)
VISTAS_DISPARO = {
    ("3/4", "fogonazo"): ((-9.0, -8.0, 5.2), (-1.5, -2.0, 3.8), 50),
    ("Eje", "fogonazo"): ((2.0, -10.0, 5.2), (-1.0, -2.0, 3.8), 50),
    ("3/4", "vuelo"): ((-16.0, -6.5, 5.5), (0.0, -6.5, 3.4), 26),
    ("Eje", "vuelo"): ((-3.0, 9.0, 5.5), (0.0, -8.0, 3.2), 40),
}
COLUMNAS = [
    ("Disparo", "fogonazo", ("disparo", 10)),
    ("Proyectil en vuelo", "vuelo", ("disparo", 18)),
    ("Apertura 0,05 s", "cerca", ("apertura", 0.05)),
    ("Apertura 0,15 s", "cerca", ("apertura", 0.15)),
    ("Apertura 0,30 s", "cerca", ("apertura", 0.30)),
    ("Abierto", "cerca", ("abierto", 1.00)),
    ("Abierto (0,45 s después)", "cerca", ("abierto", 1.45)),
    ("Cierre 0,15 s", "cerca", ("cierre", 0.15)),
    ("Cierre 0,34 s", "cerca", ("cierre", 0.34)),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    sal = os.path.abspath(a.salida)
    tmp = os.path.join(sal, "_render_tmp")
    muestras = 8 if a.rapido else 24
    rutas = {}
    for estilo in ("chatarra", "vip"):
        piezas = D.piezas_chatarra if estilo == "chatarra" else D.piezas_vip
        sc = PE.Escena(estilo, lambda f, e=estilo: D.calcular_pose_disparo(f, e), D.ULTIMO_DISPARO, piezas,
                       os.path.join(tmp, estilo), muestras, a.rapido)
        preparar_ambiente()
        portal = Portal(estilo)
        reg = maniqui(Vector((3.9, -DISTANCIA + 1.0, 0)))
        for nombre, plano, (fase, t) in COLUMNAS:
            for vista in ("3/4", "Eje"):
                lejos = plano != "cerca"
                cfg = VISTAS_DISPARO[(vista, plano)] if lejos else VISTAS_CERCA[vista]
                poner_camara(sc.cam, *cfg)
                for o in sc.mallas + list(sc.pistola.partes.values()):
                    o.hide_render = not lejos
                for o in reg:
                    o.hide_render = lejos
                sc.efectos.limpiar()
                if lejos:
                    portal.mostrar(False)
                    scn = bpy.context.scene
                    scn.frame_set(t)
                    pose = sc.calcular_pose(t)
                    pieza = sc.calcular_piezas(t)
                    M = sc.pistola.colocar(pose, pieza)
                    sc.efectos.poner(t, sc.pistola, M, sc.M_disparo, pieza)
                else:
                    portal.mostrar(True)
                    portal.poner(fase, t, sc.cam)
                ruta = os.path.join(tmp, estilo, f"{vista.replace('/', '-')}_{nombre.replace(' ', '_')}_{t}.png")
                bpy.context.scene.render.filepath = ruta
                bpy.ops.render.render(write_still=True)
                PE.resplandor(ruta)
                rutas[(estilo, vista, nombre)] = ruta
    filas, etiquetas = [], []
    for vista in ("3/4", "Eje"):
        for estilo in ("chatarra", "vip"):
            filas.append([rutas[(estilo, vista, n)] for n, _, _ in COLUMNAS])
            etiquetas.append(f"{D.ESTILOS[estilo]['titulo']}\n{vista}")
    columnas = [(0, n) for n, _, _ in COLUMNAS]
    PE.hoja_libre(filas, [n for n, _, _ in COLUMNAS], os.path.join(sal, f"hoja_portal_{a.ronda}.png"),
                  "Portal de la pistola: disparo, apertura, abierto y cierre. Normal (verde, inestable) frente a VIP (morado y cian, perfecto)",
                  etiquetas)
    print("[ok] hoja del portal")


main()
