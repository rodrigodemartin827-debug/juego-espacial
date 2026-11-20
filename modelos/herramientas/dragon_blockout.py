"""
Blockout del Dragón Leviatán: masas del cuerpo a baja resolución + alas como abanicos planos + cuernos y cola-hacha
como conos. Sirve para la PRUEBA DE SILUETA (negro sobre blanco) antes de modelar el detalle.

Uso: python modelos/herramientas/dragon_blockout.py --salida bestias/dragon_leviatan/proceso/blockout
"""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Vector  # noqa: E402

import dragon_anatomia as A  # noqa: E402
import dragon_sdf as s  # noqa: E402


def campo_cuerpo(P):
    d = A.campo_torso(P)
    for i in range(3):
        d = s.smin(d, A.campo_cuello(P, i), 0.6)
        d = s.smin(d, A.campo_cola(P, i), 0.6)
    d = s.smin(d, A.campo_cabeza(P), 0.6)
    d = s.smin(d, A.campo_mandibula(P), 0.4)
    for lado in ("Izq", "Der"):
        for t in ("Muslo", "Garra"):
            d = s.smin(d, A.campo_pata_del(P, lado, t), 0.6)
        for t in ("Muslo", "Tibia"):
            d = s.smin(d, A.campo_pata_tras(P, lado, t), 0.6)
    return d


def malla_desde(nombre, verts, caras):
    m = bpy.data.meshes.new(nombre)
    m.from_pydata([tuple(v) for v in verts], [], [tuple(int(i) for i in f) for f in caras])
    o = bpy.data.objects.new(nombre, m)
    bpy.context.scene.collection.objects.link(o)
    return o


def ala_plana(k):
    """Abanico de membrana (grosor 0,2) + huesos como cajas finas."""
    bm = bmesh.new()
    x = lambda p: Vector((p[0] * k, p[1], p[2]))  # noqa: E731
    contorno = [A.ALA_HOMBRO, A.ALA_CODO, A.ALA_MUNECA]
    # borde de salida con festones entre puntas
    puntas = [d[0] for d in A.ALA_DEDOS]
    pts = [A.ALA_MUNECA, puntas[0]]
    for i in range(3):
        a, b = puntas[i], puntas[i + 1]
        medio = (a + b) / 2
        hacia = A.ALA_MUNECA - medio
        pts.append(medio + hacia * 0.14)
        pts.append(b)
    medio = (puntas[3] + A.ALA_ANCLA_CUERPO) / 2
    pts.append(medio + (A.ALA_CODO - medio) * 0.25)
    pts.append(A.ALA_ANCLA_CUERPO)
    pts += [A.ALA_HOMBRO, A.ALA_CODO]
    vs = [bm.verts.new(x(p)) for p in pts]
    bm.faces.new(vs)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    m = bpy.data.meshes.new("ala")
    bm.to_mesh(m)
    o = bpy.data.objects.new(f"Ala_{k}", m)
    bpy.context.scene.collection.objects.link(o)
    mod = o.modifiers.new("grosor", "SOLIDIFY")
    mod.thickness = 0.25
    return o


def cono(nombre, a, b, r):
    a, b = Vector(a), Vector(b)
    bpy.ops.mesh.primitive_cone_add(radius1=r, radius2=0.02, depth=(b - a).length, location=(a + b) / 2)
    o = bpy.context.active_object
    o.rotation_euler = (b - a).to_track_quat("Z", "Y").to_euler()
    o.name = nombre
    return o


def renderizar_siluetas(carpeta):
    scn = bpy.context.scene
    # Sin GPU: Cycles con un material negro plano (emisión 0) sobre un mundo blanco.
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = 4
    scn.cycles.use_denoising = False
    if scn.world is None:
        scn.world = bpy.data.worlds.new("mundo")
    scn.world.use_nodes = True
    bg = scn.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (1, 1, 1, 1)
    bg.inputs["Strength"].default_value = 1.0
    negro = bpy.data.materials.new("negro")
    negro.use_nodes = True
    nt = negro.node_tree
    nt.nodes.clear()
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 0.0
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(em.outputs[0], out.inputs["Surface"])
    scn.view_layers[0].material_override = negro
    scn.render.resolution_x = scn.render.resolution_y = 700
    scn.view_settings.view_transform = "Standard"
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = 72
    cam = bpy.data.objects.new("cam", cam_d)
    scn.collection.objects.link(cam)
    scn.camera = cam
    c = Vector((0, 1, 16))
    vistas = [("frente", 0, 4), ("tres_cuartos", -40, 18), ("lateral", -90, 2), ("arriba", 0, 89),
              ("trasera", 180, 8), ("tres_cuartos_tras", -140, 20)]
    rutas = []
    for nombre, az, el in vistas:
        a, e = math.radians(az), math.radians(el)
        d = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
        cam.location = c + d * 120
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
        ruta = os.path.join(carpeta, f"silueta_{nombre}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        rutas.append(ruta)
    return rutas


def main():
    carpeta = sys.argv[sys.argv.index("--salida") + 1]
    os.makedirs(carpeta, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    v, f = s.mallar(campo_cuerpo, (-10, -33, -1), (10, 35, 19), 0.3)
    malla_desde("Cuerpo", v, f)
    for k in (1, -1):
        ala_plana(k)
        for punta, nud in A.ALA_DEDOS:
            pass
    # cuernos principales y hacha
    for k in (1, -1):
        cono("Cuerno", (1.6 * k, -20.9, 13.0), (3.0 * k, -16.8, 15.8), 0.55)
        cono("Colmillo", (1.9 * k, -28.2, 8.4), (2.0 * k, -28.6, 6.0), 0.25)
    # jugador R6 de referencia (5 studs) junto a la pata delantera
    bpy.ops.mesh.primitive_cube_add(location=(14, -12, 2.5))
    bpy.context.active_object.scale = (1, 0.5, 2.5)
    h = A.HACHA
    bpy.ops.mesh.primitive_cube_add(location=tuple(h))
    hb = bpy.context.active_object
    hb.scale = (0.2, 1.5, 2.0)
    for r in renderizar_siluetas(carpeta):
        print("[ok]", r)


if __name__ == "__main__":
    main()
