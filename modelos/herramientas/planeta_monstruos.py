"""
Elementos del planeta de los monstruos: 3 árboles muertos retorcidos, 2 rocas oscuras con grietas brillantes y una
estructura siniestra (el «Arco de costillas»).

Paleta: negros y grises violáceos, hueso ennegrecido y brillo morado (el color del planeta, cuyo sol es un agujero
negro). Lo orgánico se modela igual que el monstruo: esqueleto + Skin (o metabolas) en ALTA, con ruido y color por
vértice, simplificado a BAJA con color y normales horneados. Lo que brilla va en una malla aparte para Neon.

  Arbol_Retorcido   alto, con el tronco en espiral y ramas como dedos hacia el cielo
  Arbol_Colgante    ancho y encorvado, con las ramas que caen como brazos
  Arbol_Tocon       tronco partido con raíces como garras
  RocaOscura_Partida  peñasco partido en trozos, con un núcleo morado que brilla por las grietas
  RocaOscura_Aguja    aguja partida en vertical, con el mismo núcleo
  Arco_Costillas    costillas gigantes de piedra formando un túnel, columna vertebral y un altar con un ojo

Uso:
    python modelos/herramientas/planeta_monstruos.py --salida modelos/planeta_monstruos [--ronda N] [--rapido]
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

import comun as c  # noqa: E402
import kit  # noqa: E402
import rocas_minerales as rm  # noqa: E402
from ciudad_humana import kit_a_roblox  # noqa: E402

E = c.ESTUDIO

MORADO = "#B54DFF"
CORTEZA = ("#A097AC", "#5A5164", "#1A161D")  # (claro, oscuro, grietas)
HUESO = ("#958B7B", "#575046", "#1A1713")
ROCA = ("#837D8E", "#4A4553", "#121016")

TRIS_ARBOL = 2200

# --------------------------------------------------------------------------------------------------------------
# Utilidades orgánicas
# --------------------------------------------------------------------------------------------------------------


def skin(nombre, nodos, aristas, resolucion=0.12):
    """
    Malla orgánica de un esqueleto de ramas: una metabola en cápsula por cada tramo (de radio el medio de sus dos
    extremos). Se usaba el modificador Skin, pero falla cuando muchas ramas salen del mismo punto (el árbol perdía
    el tronco); las metabolas funden cualquier ramificación sin agujeros.
    nodos: [(pos studs, radio studs)], aristas: [(i, j)].
    """
    from mathutils import Euler  # noqa: F401
    mb = bpy.data.metaballs.new(nombre)
    mb.resolution = resolucion * E
    mb.threshold = 0.6
    k = 1.6  # una metabola sola mide 0,575 veces su radio (ver monstruo.py)
    for i, j in aristas:
        a, ra = Vector(nodos[i][0]), nodos[i][1]
        b, rb = Vector(nodos[j][0]), nodos[j][1]
        # Tramos largos en dos cápsulas, para que el grosor siga la conicidad.
        partes = max(1, int((b - a).length / max(0.4, (ra + rb))))
        for q in range(partes):
            t0, t1 = q / partes, (q + 1) / partes
            p0, p1 = a.lerp(b, t0), a.lerp(b, t1)
            r = ra + (rb - ra) * (t0 + t1) / 2
            e = mb.elements.new(type="CAPSULE")
            e.co = (p0 + p1) / 2 * E
            e.radius = r * E * k
            e.size_x = (p1 - p0).length / 2 * E
            d = (p1 - p0).normalized()
            e.rotation = d.to_track_quat("X", "Z")
    obj_mb = bpy.data.objects.new(nombre + "_mb", mb)
    bpy.context.scene.collection.objects.link(obj_mb)
    dep = bpy.context.evaluated_depsgraph_get()
    malla = bpy.data.meshes.new_from_object(obj_mb.evaluated_get(dep))
    bpy.data.objects.remove(obj_mb)
    obj = bpy.data.objects.new(nombre, malla)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def remallar(obj, voxel):
    mod = obj.modifiers.new("remallado", "REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = voxel * E
    mod.use_smooth_shade = True
    c.aplicar_modificadores(obj)
    mod = obj.modifiers.new("suave", "SMOOTH")
    mod.factor = 0.5
    mod.iterations = 2
    c.aplicar_modificadores(obj)


def corteza(obj, paleta, rnd, fuerza=0.06, vetas=True, brillo_puntas=None):
    """Relieve de corteza (vetas verticales retorcidas) y color por vértice."""
    sem = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), rnd.uniform(0, 50)))
    claro, oscuro, grieta = (Vector(c.srgb(h)) for h in paleta)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    zmax = max(v.co.z for v in bm.verts) / E
    # Primera pasada: el ruido de cada vértice. Se normaliza después por percentiles, porque el rango del ruido
    # ridged depende de la escala y de la semilla (sin normalizar, los árboles salían casi negros).
    crudos = []
    for v in bm.verts:
        p = v.co / E
        if vetas:
            a = p.z * 0.35
            q = Vector((p.x * math.cos(a) - p.y * math.sin(a), p.x * math.sin(a) + p.y * math.cos(a), p.z * 0.12))
            veta = noise.ridged_multi_fractal(q * 3.2 + sem, 1.0, 2.0, 3, 0.0, 2.0)
        else:
            veta = noise.fractal(p * 1.2 + sem, 0.6, 2.0, 4)
        crudos.append((veta, noise.fractal(p * 0.6 + sem, 0.6, 2.0, 3)))
    orden = sorted(x for x, _ in crudos)
    bajo, alto = orden[int(len(orden) * 0.05)], orden[int(len(orden) * 0.95)]
    cols = []
    for v, (veta, bulto) in zip(bm.verts, crudos):
        p = v.co / E
        veta = max(0.0, min(1.0, (veta - bajo) / max(1e-6, alto - bajo)))  # 0..1
        des = fuerza * (veta - 0.5) + fuerza * 0.6 * bulto
        v.co += v.normal * des * E
        t = max(0.0, min(1.0, 0.25 + 0.7 * veta + 0.2 * bulto))
        col = oscuro.lerp(claro, t)
        col = col.lerp(grieta, max(0.0, min(1.0, (0.18 - veta) * 3.0)))
        col *= 0.8 + 0.2 * max(0.0, min(1.0, p.z / max(1.0, zmax * 0.3)))  # más oscuro abajo (humedad)
        if brillo_puntas is not None and p.z > zmax * 0.75:
            col = col.lerp(Vector(c.srgb(brillo_puntas)) * 0.35, (p.z / zmax - 0.75) * 1.2)
        cols.append(col)
    capa = bm.loops.layers.color.new("Col")
    for f in bm.faces:
        for lo in f.loops:
            q = cols[lo.vert.index]
            lo[capa] = (q.x, q.y, q.z, 1.0)
    bm.to_mesh(obj.data)
    bm.free()
    mat = bpy.data.materials.new(f"{obj.name}_vc")
    mat.use_nodes = True
    nt = mat.node_tree
    at = nt.nodes.new("ShaderNodeVertexColor")
    at.layer_name = "Col"
    nt.links.new(at.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def baja_horneada(alta, nombre, tris, carpeta, rapido, extrusion=0.06, angulo=60):
    baja = rm.version_baja(alta, nombre, tris)
    c.sombreado_suave(baja, angulo=angulo)
    c.desplegar_uv(baja, margen=0.01)
    c.hornear(baja, alta, tam=256 if rapido else 1024,
              ruta_color=os.path.join(carpeta, "texturas", f"{nombre}_color.png"),
              ruta_normal=os.path.join(carpeta, "texturas", f"{nombre}_normal.png"),
              extrusion=extrusion, muestras=8 if rapido else 32, distancia_oclusion=0.5)
    alta.hide_render = True
    alta.hide_set(True)
    return baja


def neon(nombre, bm, color=MORADO, fuerza=1.2):
    col = c.srgb(color)
    m = c.material(f"{nombre}_mat", col, rugosidad=0.3, emision=col, fuerza_emision=fuerza)
    obj = c.objeto_desde_bmesh(nombre, bm, [m])
    for p in obj.data.polygons:
        p.use_smooth = False
    return obj


def luz_de_pieza(nombre, pos_studs, color=MORADO, energia=150):
    d = bpy.data.lights.new(nombre, "POINT")
    d.color = c.srgb(color)
    d.energy = energia
    o = bpy.data.objects.new(nombre, d)
    o.location = Vector(pos_studs) * E
    o["de_pieza"] = True
    bpy.context.scene.collection.objects.link(o)
    return o


# --------------------------------------------------------------------------------------------------------------
# Árboles
# --------------------------------------------------------------------------------------------------------------


def rama(nodos, aristas, desde, pos, direccion, largo, radio, segmentos, rnd, giro=0.25, gravedad=0.0,
         hijos=0, nivel=0, puntas=None):
    """Crece una rama desde el nodo `desde` (índice). Añade nodos y aristas. Recursiva."""
    d = Vector(direccion).normalized()
    paso = largo / segmentos
    actual = desde
    p = Vector(pos)
    for k in range(1, segmentos + 1):
        t = k / segmentos
        # Retorcer: girar la dirección alrededor de Z y añadir un poco de ruido; la gravedad la dobla hacia abajo.
        d = Matrix.Rotation(giro * rnd.uniform(0.5, 1.5), 3, "Z") @ d
        d += Vector((rnd.uniform(-0.25, 0.25), rnd.uniform(-0.25, 0.25), rnd.uniform(-0.1, 0.15))) - \
            Vector((0, 0, gravedad * t))
        d.normalize()
        p = p + d * paso
        r = radio * (1 - 0.9 * t) ** 1.2 + 0.03
        nodos.append((tuple(p), r))
        aristas.append((actual, len(nodos) - 1))
        actual = len(nodos) - 1
        # Ramas hijas a media altura.
        if hijos and 0.3 < t < 0.85 and rnd.random() < hijos / segmentos * 1.6:
            lateral = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.2, 0.6))).normalized()
            rama(nodos, aristas, actual, p, (d + lateral * 1.4), largo * (1 - t) * rnd.uniform(0.6, 0.9),
                 r * 0.75, max(3, segmentos - 3), rnd, giro=giro * 1.2, gravedad=gravedad, hijos=hijos - 1,
                 nivel=nivel + 1, puntas=puntas)
    if puntas is not None:
        puntas.append(tuple(p))
    return actual


def arbol(carpeta, rapido, nombre, semilla, tronco_alto, tronco_radio, n_ramas, giro, gravedad, inclinacion,
          raices=5, partido=False, n_astillas=None):
    rnd = random.Random(semilla)
    nodos = [((0, 0, -0.6), tronco_radio * 1.25)]
    aristas = []
    puntas = []
    # Raíces: garras que salen de la base y se hunden.
    for i in range(raices):
        a = i * math.tau / raices + rnd.uniform(-0.3, 0.3)
        d = Vector((math.cos(a), math.sin(a), -0.15))
        rama(nodos, aristas, 0, nodos[0][0], d, tronco_radio * rnd.uniform(3.2, 4.5), tronco_radio * 0.5, 5, rnd,
             giro=0.1, gravedad=0.3)
    # Tronco: sube retorciéndose (y en el tocón, termina partido en dos puntas).
    seg = 7
    p = Vector((0, 0, -0.6))
    actual = 0
    d = Vector((math.sin(inclinacion), 0, 1)).normalized()
    for k in range(1, seg + 1):
        t = k / seg
        d = (Matrix.Rotation(giro, 3, "Z") @ d + Vector((rnd.uniform(-0.15, 0.15), rnd.uniform(-0.15, 0.15), 0)))
        d.normalize()
        p = p + d * tronco_alto / seg
        nodos.append((tuple(p), tronco_radio * (1 - 0.55 * t)))
        aristas.append((actual, len(nodos) - 1))
        actual = len(nodos) - 1
        if not partido and t > 0.45 and rnd.random() < 0.55:
            lateral = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), 0.4)).normalized()
            rama(nodos, aristas, actual, p, lateral, tronco_alto * rnd.uniform(0.4, 0.6),
                 tronco_radio * 0.45, 6, rnd, giro=giro * 1.5, gravedad=gravedad, hijos=1, puntas=puntas)
    # Copa: ramas principales que salen de la cima.
    n_ramas = n_astillas or n_ramas
    for i in range(n_ramas):
        a = i * math.tau / n_ramas + rnd.uniform(-0.4, 0.4)
        # En el tocón, las «ramas» son las astillas del tronco partido: cortas, hacia arriba y en punta.
        sube = 1.3 if partido else rnd.uniform(0.5, 1.4) - gravedad * 0.8
        dd = Vector((math.cos(a), math.sin(a), sube))
        rama(nodos, aristas, actual, p, dd, tronco_alto * (0.6 if partido else rnd.uniform(0.55, 0.8)),
             tronco_radio * (0.5 if partido else 0.42), 7, rnd, giro=giro * 1.3, gravedad=gravedad,
             hijos=0 if partido else 2, puntas=puntas)
    alta = skin(f"{nombre}_alta", nodos, aristas)
    remallar(alta, 0.12 if rapido else 0.06)
    corteza(alta, CORTEZA, rnd, fuerza=0.07, brillo_puntas=None)
    # Corte de la base: lo que queda bajo el suelo no hace falta (más allá de 0,6 studs).
    # Extrusión grande: al simplificar, las ramas finas se separan de la malla alta y el rayo del horneado
    # no las encontraba (salían negras).
    baja = baja_horneada(alta, nombre, TRIS_ARBOL, carpeta, rapido, extrusion=0.2)
    # Hongos brillantes: unas cuantas setas moradas pegadas al tronco (en Neon, de noche guían la vista).
    bm = bmesh.new()
    rnd2 = random.Random(semilla + 1)
    for i in range(5):
        z = rnd2.uniform(0.6, tronco_alto * 0.5)
        a = rnd2.uniform(0, math.tau)
        r = tronco_radio * (1 - 0.55 * z / tronco_alto) * 1.25
        base = Vector((math.cos(a) * r + math.sin(inclinacion) * z, math.sin(a) * r, z))
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.35, radius2=0.05, depth=0.18)
        m = Matrix.Translation(base) @ Vector((math.cos(a), math.sin(a), 0.3)).to_track_quat("Z", "Y").to_matrix().to_4x4()
        bmesh.ops.transform(bm, matrix=m, verts=res["verts"])
    setas = neon(f"{nombre}_Neon", bm, fuerza=1.5)
    return [baja, setas], None


def arbol_retorcido(carpeta, rapido):
    return arbol(carpeta, rapido, "Arbol_Retorcido", 5, 15.0, 1.1, 4, giro=0.35, gravedad=0.0, inclinacion=0.15)


def arbol_colgante(carpeta, rapido):
    return arbol(carpeta, rapido, "Arbol_Colgante", 9, 9.0, 1.4, 6, giro=0.2, gravedad=1.6, inclinacion=0.35)


def arbol_tocon(carpeta, rapido):
    return arbol(carpeta, rapido, "Arbol_Tocon", 14, 5.5, 1.6, 2, giro=0.5, gravedad=0.0, inclinacion=0.05,
                 raices=6, partido=True, n_astillas=3)


# --------------------------------------------------------------------------------------------------------------
# Rocas partidas con núcleo brillante
# --------------------------------------------------------------------------------------------------------------


def roca_partida(carpeta, rapido, nombre, forma, cortes, separacion, semilla, tris):
    rnd = random.Random(semilla)
    base = rm.forma_roca(dict(forma), rnd)
    original = base.copy()  # para el núcleo
    # Trozos: cada corte divide los trozos existentes en dos; luego cada uno se separa de los demás.
    trozos = [base]
    for n, d in cortes:
        n = Vector(n).normalized()
        centro = Vector((0, 0, forma["tam"][2] * 0.45))
        nuevos = []
        for t in trozos:
            for signo in (1, -1):
                copia = t.copy()
                geo = copia.verts[:] + copia.edges[:] + copia.faces[:]
                res = bmesh.ops.bisect_plane(copia, geom=geo, plane_co=centro + n * d, plane_no=n * signo,
                                             clear_outer=True)
                borde = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
                if borde:
                    bmesh.ops.holes_fill(copia, edges=borde, sides=0)
                if len(copia.verts) > 8:
                    nuevos.append(copia)
            t.free()
        trozos = nuevos
    junto = bmesh.new()
    cen_total = Vector((0, 0, forma["tam"][2] * 0.4))
    for t in trozos:
        cen = sum((v.co for v in t.verts), Vector()) / len(t.verts)
        dirr = (cen - cen_total)
        dirr.z *= 0.3
        if dirr.length > 1e-4:
            bmesh.ops.translate(t, vec=dirr.normalized() * separacion, verts=t.verts)
        m = bpy.data.meshes.new("tmp")
        t.to_mesh(m)
        junto.from_mesh(m)
        bpy.data.meshes.remove(m)
        t.free()
    zmin = min(v.co.z for v in junto.verts)
    bmesh.ops.translate(junto, vec=(0, 0, -zmin), verts=junto.verts)
    alta = c.objeto_desde_bmesh(f"{nombre}_alta", junto)
    rm.detallar(alta, dict(forma, ruido=0.12, estratos=0.0, paleta=ROCA), rnd, voxel_studs=0.12 if rapido else 0.06)
    baja = baja_horneada(alta, nombre, tris, carpeta, rapido, angulo=50)
    # Núcleo: la propia roca encogida un 18 %: queda dentro y solo se ve por las grietas entre los trozos.
    bm = original
    cen = sum((v.co for v in bm.verts), Vector()) / len(bm.verts)
    for v in bm.verts:
        v.co = cen + (v.co - cen) * 0.82
    bmesh.ops.translate(bm, vec=(0, 0, -zmin), verts=bm.verts)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(12), verts=bm.verts, edges=bm.edges)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    nucleo = neon(f"{nombre}_Nucleo", bm, fuerza=2.0)
    luz_de_pieza(f"{nombre}_luz", (0, 0, forma["tam"][2] * 0.45), energia=60)
    return [baja, nucleo], None


def roca_partida_1(carpeta, rapido):
    forma = dict(tam=(7.0, 6.0, 5.0), cortes=8, redondez=0.5, inclinacion=0)
    return roca_partida(carpeta, rapido, "RocaOscura_Partida", forma,
                        cortes=[((1, 0.3, 0.2), 0.3), ((0.2, 1, -0.1), -0.4)], separacion=0.35, semilla=31, tris=700)


def roca_partida_2(carpeta, rapido):
    forma = dict(tam=(3.6, 3.2, 10.0), cortes=12, redondez=0.15, inclinacion=6)
    return roca_partida(carpeta, rapido, "RocaOscura_Aguja", forma,
                        cortes=[((1, 0.2, 0.05), 0.1), ((0.2, 1, 0.5), 0.6)], separacion=0.3, semilla=44, tris=600)


# --------------------------------------------------------------------------------------------------------------
# Arco de costillas
# --------------------------------------------------------------------------------------------------------------


def arco_costillas(carpeta, rapido):
    rnd = random.Random(66)
    nodos, aristas = [], []

    def cadena(puntos):
        inicio = len(nodos)
        for i, (p, r) in enumerate(puntos):
            nodos.append((p, r))
            if i:
                aristas.append((inicio + i - 1, inicio + i))
        return inicio

    largo = 18.0
    # Columna vertebral: arco suave a lo largo de Y en lo alto, con vértebras.
    columna = []
    for i in range(13):
        t = i / 12
        y = -largo / 2 + t * largo
        z = 12.5 + 1.5 * math.sin(t * math.pi) - (2.5 if t > 0.92 else 0)
        columna.append(((0, y, z), 0.7 - 0.25 * abs(t - 0.5)))
    i0 = cadena(columna)
    for i in range(13):  # apófisis: pinchos hacia arriba
        p, r = columna[i]
        nodos.append(((p[0], p[1], p[2] + 1.0 + 0.4 * math.sin(i)), 0.08))
        aristas.append((i0 + i, len(nodos) - 1))
    # Costillas: 5 pares que salen de la columna, bajan curvándose hacia fuera y se clavan en el suelo.
    for k in range(5):
        t = (k + 0.5) / 5
        iv = i0 + 1 + round(t * 10)
        py = columna[iv - i0][0][1]
        pz = columna[iv - i0][0][2]
        for sx in (-1, 1):
            pts = []
            for j in range(1, 10):
                u = j / 9
                ang = u * math.pi * 0.62
                x = sx * (7.5 + rnd.uniform(-0.4, 0.4)) * math.sin(ang) * (1.0 + 0.15 * u)
                z = pz - (pz + 0.5) * (1 - math.cos(ang)) / (1 - math.cos(math.pi * 0.62))
                yy = py - 1.0 * u + rnd.uniform(-0.2, 0.2)
                pts.append(((x, yy, z), 0.75 * (1 - 0.55 * u) + 0.1))
            j0 = len(nodos)
            for j, (p, r) in enumerate(pts):
                nodos.append((p, r))
                aristas.append((iv if j == 0 else j0 + j - 1, j0 + j))
    alta = skin("Arco_Costillas_alta", nodos, aristas)
    remallar(alta, 0.12 if rapido else 0.06)
    corteza(alta, HUESO, rnd, fuerza=0.06, vetas=False)

    # Altar al fondo: monolito de piedra (pieza de kit, con su textura) y ojo brillante.
    pal = {"Piedra": ("#2A2730", 0.9, 0.0, 0.6), "PiedraClara": ("#45404D", 0.85, 0.0, 0.5),
           "Neon": (MORADO, 0.3, 0.0, 0.0, 3.0)}
    al = kit.Pieza("Arco_Costillas_Altar", pal)
    ne = kit.Pieza("Arco_Costillas_Neon", pal)
    ya = largo / 2 + 2.0
    al.caja_de((-6.5, -largo / 2 - 3, 0), (6.5, ya + 3.5, 0.6), "Piedra")  # losa del suelo
    al.caja_de((-3.0, ya - 1.5, 0.6), (3.0, ya + 1.5, 1.8), "PiedraClara")  # escalón
    obel = [kit.anillo_z(z, rx, ry, 4, yc=ya, giro=math.pi / 4) for z, rx, ry in
            [(1.8, 1.8, 1.4), (9.0, 1.2, 0.9), (11.0, 0.15, 0.1)]]
    al.loft(obel, "Piedra")
    # Runas: trazos en la cara delantera del monolito.
    for i in range(6):
        z = 3.0 + i * 1.0
        ancho = rnd.uniform(0.3, 0.8)
        ne.caja((rnd.uniform(-0.3, 0.3), ya - 1.25 + 0.05 * i, z), (ancho, 0.08, 0.12), "Neon",
                giro=Matrix.Rotation(rnd.uniform(-0.6, 0.6), 3, "Y"))
    ne.cilindro((0, ya - 1.4, 8.6), 0.55, 0.2, "Neon", lados=10, eje=(0, -1, 0))  # ojo
    # Losas rotas del camino entre las costillas.
    for i in range(6):
        y = -largo / 2 + 1.5 + i * 2.8
        al.caja((rnd.uniform(-0.4, 0.4), y, 0.7), (rnd.uniform(2.5, 3.5), 2.2, 0.3), "PiedraClara",
                giro=Matrix.Rotation(rnd.uniform(-0.2, 0.2), 3, "Z"))
    altar = kit.terminar(al, carpeta, rapido, bisel=0.08)
    neon_obj = kit.terminar(ne, carpeta, rapido, bisel=0, con_textura=False)
    baja = baja_horneada(alta, "Arco_Costillas", 3500, carpeta, rapido, angulo=55)
    luz_de_pieza("Arco_luz", (0, ya - 2.0, 8.6), energia=250)

    def extra(desp):
        return {"nota": "studs, ejes de Roblox, respecto al centro de la base",
                "Ojo": kit_a_roblox(Vector((0, ya - 1.5, 8.6)) + desp),
                "luz_recomendada": f"PointLight {MORADO}, Brightness 2, Range 20"}
    return [baja, altar, neon_obj], extra


ITEMS = [
    dict(archivo="Arbol_Retorcido", titulo="Árbol retorcido", construir=arbol_retorcido),
    dict(archivo="Arbol_Colgante", titulo="Árbol colgante", construir=arbol_colgante),
    dict(archivo="Arbol_Tocon", titulo="Tocón partido", construir=arbol_tocon),
    dict(archivo="RocaOscura_Partida", titulo="Roca partida", construir=roca_partida_1),
    dict(archivo="RocaOscura_Aguja", titulo="Aguja partida", construir=roca_partida_2),
    dict(archivo="Arco_Costillas", titulo="Arco de costillas", construir=arco_costillas),
]

if __name__ == "__main__":
    a = kit.argumentos()
    vistas = [("Frente", 0, 10), ("3/4", -40, 20), ("Lateral", -90, 8), ("3/4 trasera", 140, 22), ("Arriba", 15, 70)]
    kit.ejecutar_lote(ITEMS, a.salida, "Planeta de los monstruos", a.ronda, a.rapido, vistas=vistas, solo=a.solo,
                      nota="Malla con color + normales horneados · _Neon / _Nucleo: material Neon morado")
