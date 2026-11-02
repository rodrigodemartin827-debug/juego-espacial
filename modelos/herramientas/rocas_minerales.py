"""
Set de rocas y minerales para los planetas: 4 rocas y 3 minerales brillantes.

Cada pieza se genera en dos versiones:
  * ALTA (cientos de miles de triángulos): forma base + ruido de detalle. Solo sirve para hornear.
  * BAJA (la que va al juego, pocos cientos de triángulos): la ALTA simplificada. Lleva UV y dos texturas horneadas
    de la ALTA: color (con oclusión ambiental) y normales, para una SurfaceAppearance.

Los minerales son una base de roca (igual que las rocas) + un grupo de cristales en una malla aparte, con
sombreado plano, para ponerle en Studio el material Neon (el brillo) y una PointLight del mismo color.

Uso:
    python modelos/herramientas/rocas_minerales.py --salida modelos/rocas_minerales [--ronda N] [--rapido]
"""

import argparse
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402  (antes que bmesh)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

import comun as c  # noqa: E402

E = c.ESTUDIO

# --------------------------------------------------------------------------------------------------------------
# Datos de cada pieza (todo lo ajustable está aquí). Medidas en studs.
# --------------------------------------------------------------------------------------------------------------

# Paletas de roca: (color claro, color oscuro, color de las grietas). Neutras para poder teñirlas en Studio.
PALETA_GRIS = ("#9A968F", "#5E5B57", "#2B2927")
PALETA_ARENISCA = ("#B8977A", "#7C6250", "#3A2C24")
PALETA_BASALTO = ("#6A6A70", "#3C3C43", "#1A1A1E")
PALETA_MUSGO = ("#8D9283", "#56594F", "#25261F")

ROCAS = [
    dict(nombre="Roca_Canto", titulo="Canto rodado", tam=(6.0, 5.0, 4.0), cortes=6, redondez=0.85, semilla=11,
         ruido=0.22, estratos=0.0, paleta=PALETA_GRIS, tris=520),
    dict(nombre="Roca_Aguja", titulo="Aguja", tam=(3.2, 3.0, 9.0), cortes=14, redondez=0.15, semilla=27,
         ruido=0.12, estratos=0.0, paleta=PALETA_BASALTO, tris=420, inclinacion=8),
    dict(nombre="Roca_Losa", titulo="Losa en capas", tam=(8.0, 5.5, 2.6), cortes=9, redondez=0.4, semilla=5,
         ruido=0.10, estratos=0.35, paleta=PALETA_ARENISCA, tris=560),
    dict(nombre="Roca_Grupo", titulo="Grupo de piedras", grupo=True, semilla=41, paleta=PALETA_MUSGO, tris=640),
]

MINERALES = [
    dict(nombre="Mineral_Cristal", titulo="Cristal (cian)", color="#4FD8FF", brillo=6.0, semilla=3,
         estilo="prismas", base=(4.2, 3.6, 1.6), paleta=PALETA_BASALTO, n=7, largo=(1.8, 4.2), grosor=(0.35, 0.7)),
    dict(nombre="Mineral_Ambar", titulo="Ambar solar (oro)", color="#FFB23A", brillo=5.0, semilla=8,
         estilo="geoda", base=(4.0, 4.0, 2.2), paleta=PALETA_ARENISCA, n=11, largo=(0.9, 1.9), grosor=(0.35, 0.6)),
    dict(nombre="Mineral_Vacio", titulo="Esquirla del vacio (violeta)", color="#B54DFF", brillo=6.5, semilla=19,
         estilo="esquirlas", base=(4.4, 3.8, 1.4), paleta=PALETA_BASALTO, n=6, largo=(2.6, 5.2), grosor=(0.25, 0.5)),
]

TAM_TEXTURA = 1024


# --------------------------------------------------------------------------------------------------------------
# Formas
# --------------------------------------------------------------------------------------------------------------


def _poliedro(bm, cortes, redondez, rnd):
    """Recorta una esfera con planos al azar: da caras planas de roca rota. `redondez` 1 = casi esfera."""
    bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    for _ in range(cortes):
        n = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))).normalized()
        d = rnd.uniform(0.55, 0.85) + redondez * 0.12
        geo = bm.verts[:] + bm.edges[:] + bm.faces[:]
        res = bmesh.ops.bisect_plane(bm, geom=geo, plane_co=n * d, plane_no=n, clear_outer=True)
        borde = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
        if borde:
            bmesh.ops.holes_fill(bm, edges=borde, sides=0)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])


def _cortar_base(bm, z):
    """Corta la parte de abajo para que la roca se apoye plana en el suelo (y se pueda hundir un poco)."""
    geo = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geo, plane_co=(0, 0, z), plane_no=(0, 0, -1), clear_outer=True)
    borde = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if borde:
        bmesh.ops.holes_fill(bm, edges=borde, sides=0)


def forma_roca(d, rnd):
    """Malla base (baja densidad, en studs) de una roca, con la base en z = 0."""
    bm = bmesh.new()
    _poliedro(bm, d["cortes"], d["redondez"], rnd)
    sx, sy, sz = d["tam"]
    bmesh.ops.scale(bm, vec=(sx / 2, sy / 2, sz / 2), verts=bm.verts)
    if d.get("inclinacion"):
        bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                         matrix=Matrix.Rotation(math.radians(d["inclinacion"]), 3, "X"))
        # La aguja se estrecha hacia arriba.
        for v in bm.verts:
            t = (v.co.z / sz + 0.5)
            f = 1.0 - 0.55 * max(0.0, t) ** 1.4
            v.co.x *= f
            v.co.y *= f
    _cortar_base(bm, -sz * 0.32)
    zmin = min(v.co.z for v in bm.verts)
    for v in bm.verts:
        v.co.z -= zmin
    return bm


def forma_grupo(d, rnd):
    """Varias piedras juntas, la del centro más grande."""
    bm = bmesh.new()
    piezas = [((0, 0), (3.6, 3.0, 3.2), 7), ((2.6, 0.9), (2.2, 2.0, 1.7), 6), ((-2.3, 1.2), (2.4, 1.9, 2.0), 7),
              ((0.9, -2.1), (1.7, 1.5, 1.2), 5), ((-1.5, -1.8), (1.3, 1.2, 0.9), 5), ((3.4, -1.4), (1.0, 0.9, 0.7), 4)]
    for (px, py), (sx, sy, sz), cortes in piezas:
        tmp = bmesh.new()
        _poliedro(tmp, cortes, 0.6, rnd)
        bmesh.ops.scale(tmp, vec=(sx / 2, sy / 2, sz / 2), verts=tmp.verts)
        bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(rnd.uniform(0, 6.28), 3, "Z"))
        _cortar_base(tmp, -sz * 0.3)
        zmin = min(v.co.z for v in tmp.verts)
        bmesh.ops.translate(tmp, vec=(px, py, -zmin), verts=tmp.verts)
        m = bpy.data.meshes.new("tmp")
        tmp.to_mesh(m)
        bm.from_mesh(m)
        bpy.data.meshes.remove(m)
        tmp.free()
    return bm


# --------------------------------------------------------------------------------------------------------------
# Detalle (malla ALTA) y color por vértice
# --------------------------------------------------------------------------------------------------------------


def _remallar(obj, voxel):
    mod = obj.modifiers.new("remallado", "REMESH")
    mod.mode = "VOXEL"
    mod.voxel_size = voxel
    mod.use_smooth_shade = True
    c.aplicar_modificadores(obj)


def detallar(obj, d, rnd, voxel_studs=0.07):
    """Remalla denso y desplaza con ruido: grietas, golpes y, si toca, estratos horizontales."""
    _remallar(obj, voxel_studs * E)
    semilla = Vector((rnd.uniform(0, 100), rnd.uniform(0, 100), rnd.uniform(0, 100)))
    fuerza = d.get("ruido", 0.15)
    estratos = d.get("estratos", 0.0)
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.normal_update()
    alt_max = max(v.co.z for v in bm.verts) or 1.0
    cavidades = []
    for v in bm.verts:
        p = v.co / E  # en studs
        q = p * 0.55 + semilla
        # Forma media (bultos), detalle fino y grietas de Voronoi (bordes entre celdas).
        bultos = noise.fractal(q, 0.6, 2.2, 4, noise_basis="PERLIN_ORIGINAL")
        fino = noise.noise(p * 3.1 + semilla, noise_basis="PERLIN_ORIGINAL")
        dist = noise.voronoi(p * 0.9 + semilla, distance_metric="DISTANCE", exponent=2.5)[0]
        grieta = max(0.0, 0.12 - (dist[1] - dist[0])) / 0.12  # 1 en la grieta
        des = fuerza * (0.9 * bultos + 0.25 * fino) - 0.18 * grieta * (0.6 + fuerza * 2)
        if estratos:
            capa = (p.z * 2.6 + 0.4 * noise.noise(p * 0.4 + semilla)) % 1.0
            des -= estratos * 0.28 * (1.0 if capa < 0.18 else 0.0) + estratos * 0.06 * capa
        # La base no se desplaza hacia fuera (para que siga plana).
        if v.co.z < 0.05 * E:
            des = min(des, 0.0) * 0.3
        v.co += v.normal * des * E
        cavidades.append(grieta)
    # Color por vértice: claro arriba y en las aristas, oscuro abajo, casi negro en las grietas.
    claro, oscuro, grieta_c = (Vector(c.srgb(h)) for h in d["paleta"])
    capa_col = bm.loops.layers.color.new("Col")
    colores = {}
    for v, cav in zip(bm.verts, cavidades):
        p = v.co / E
        h = v.co.z / alt_max
        mancha = 0.5 + 0.5 * noise.fractal(p * 0.8 + semilla * 1.7, 0.7, 2.0, 3)
        polvo = max(0.0, v.normal.z) ** 2 * 0.35  # las caras de arriba, más claras (polvo/luz del cielo)
        t = min(1.0, max(0.0, 0.25 + 0.45 * h + 0.35 * mancha + polvo))
        col = oscuro.lerp(claro, t)
        col = col.lerp(grieta_c, min(1.0, cav * 0.9))
        if d.get("estratos"):
            banda = 0.5 + 0.5 * math.sin(p.z * 9.0 + 2 * noise.noise(p * 0.3))
            col = col * (0.85 + 0.25 * banda)
        colores[v.index] = col
    for f in bm.faces:
        for l in f.loops:
            col = colores[l.vert.index]
            l[capa_col] = (col.x, col.y, col.z, 1.0)
    bm.to_mesh(obj.data)
    bm.free()
    mat = bpy.data.materials.new(f"{obj.name}_vc")
    mat.use_nodes = True
    nt = mat.node_tree
    attr = nt.nodes.new("ShaderNodeVertexColor")
    attr.layer_name = "Col"
    nt.links.new(attr.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.88
    obj.data.materials.clear()
    obj.data.materials.append(mat)


def version_baja(alta, nombre, tris):
    baja = alta.copy()
    baja.data = alta.data.copy()
    baja.name = nombre
    baja.data.name = nombre
    bpy.context.scene.collection.objects.link(baja)
    actual = c.triangulos(baja)
    mod = baja.modifiers.new("simplificar", "DECIMATE")
    mod.ratio = min(1.0, tris / max(1, actual))
    mod.use_collapse_triangulate = True
    c.aplicar_modificadores(baja)
    baja.data.materials.clear()
    baja.data.materials.append(c.material(f"{nombre}_tmp", (0.5, 0.5, 0.5), rugosidad=0.88))
    c.sombreado_suave(baja, angulo=55)
    return baja


# --------------------------------------------------------------------------------------------------------------
# Cristales
# --------------------------------------------------------------------------------------------------------------


def _prisma(bm, base, eje, largo, grosor, lados, punta, rnd, torcer=0.0):
    """Un cristal: prisma de `lados` caras con la punta piramidal. Se añade a `bm`."""
    eje = eje.normalized()
    q = eje.to_track_quat("Z", "Y")
    giro = rnd.uniform(0, math.tau)
    anillo_bajo, anillo_alto = [], []
    alto_cuerpo = largo * (1 - punta)
    for i in range(lados):
        a = giro + i * math.tau / lados
        r = grosor * (1 + rnd.uniform(-0.12, 0.12))
        p0 = Vector((math.cos(a) * r, math.sin(a) * r, -0.4 * grosor))
        p1 = Vector((math.cos(a + torcer) * r * 0.92, math.sin(a + torcer) * r * 0.92, alto_cuerpo))
        anillo_bajo.append(bm.verts.new(base + q @ p0))
        anillo_alto.append(bm.verts.new(base + q @ p1))
    # Punta un poco descentrada: los cristales reales no son perfectos.
    desc = Vector((rnd.uniform(-0.2, 0.2) * grosor, rnd.uniform(-0.2, 0.2) * grosor, largo))
    cima = bm.verts.new(base + q @ desc)
    for i in range(lados):
        j = (i + 1) % lados
        bm.faces.new((anillo_bajo[i], anillo_bajo[j], anillo_alto[j], anillo_alto[i]))
        bm.faces.new((anillo_alto[i], anillo_alto[j], cima))
    bm.faces.new(list(reversed(anillo_bajo)))


def cristales(d, rnd, base_obj):
    """Grupo de cristales sobre la base. Devuelve el objeto (en metros), con sombreado plano."""
    bm = bmesh.new()
    sx, sy, sz = d["base"]
    lmin, lmax = d["largo"]
    gmin, gmax = d["grosor"]
    estilo = d["estilo"]
    for i in range(d["n"]):
        t = i / max(1, d["n"] - 1)
        if estilo == "prismas":
            # Abanico: el central grande y recto, los demás más pequeños e inclinados hacia fuera.
            ang = rnd.uniform(0, math.tau)
            r = 0.0 if i == 0 else rnd.uniform(0.35, 1.0) * sx * 0.32
            pos = Vector((math.cos(ang) * r, math.sin(ang) * r * sy / sx, sz * 0.75))
            abre = 0.0 if i == 0 else rnd.uniform(18, 48)
            eje = Matrix.Rotation(math.radians(abre), 3, Vector((-math.sin(ang), math.cos(ang), 0))) @ Vector((0, 0, 1))
            largo = lmax if i == 0 else rnd.uniform(lmin, lmax * 0.8)
            grosor = gmax if i == 0 else rnd.uniform(gmin, gmax * 0.85)
            _prisma(bm, pos, eje, largo, grosor, 6, 0.28, rnd)
        elif estilo == "geoda":
            # Corona de cristales cortos y gruesos que salen de un hueco en la roca, apuntando hacia dentro/arriba.
            ang = t * math.tau * 0.999 + rnd.uniform(-0.2, 0.2)
            r = sx * 0.28 * rnd.uniform(0.6, 1.0)
            pos = Vector((math.cos(ang) * r, math.sin(ang) * r, sz * 0.62))
            hacia = Vector((-math.cos(ang) * 0.5, -math.sin(ang) * 0.5, 1.0))
            if i == d["n"] - 1:
                pos, hacia = Vector((0, 0, sz * 0.4)), Vector((0.1, 0.05, 1))
            _prisma(bm, pos, hacia, rnd.uniform(lmin, lmax), rnd.uniform(gmin, gmax), 6, 0.4, rnd)
        else:  # esquirlas: finas, largas, de 4 caras y torcidas, en direcciones caóticas
            ang = rnd.uniform(0, math.tau)
            r = rnd.uniform(0.0, 1.0) * sx * 0.28
            pos = Vector((math.cos(ang) * r, math.sin(ang) * r, sz * 0.7))
            abre = rnd.uniform(5, 55)
            eje = Matrix.Rotation(math.radians(abre), 3, Vector((-math.sin(ang), math.cos(ang), 0))) @ Vector((0, 0, 1))
            _prisma(bm, pos, eje, rnd.uniform(lmin, lmax), rnd.uniform(gmin, gmax), 4, 0.55, rnd,
                    torcer=rnd.uniform(-0.5, 0.5))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    color = c.srgb(d["color"])
    mat = c.material(f"{d['nombre']}_cristal", color, rugosidad=0.12, emision=color, fuerza_emision=d["brillo"])
    obj = c.objeto_desde_bmesh(f"{d['nombre']}_Cristales", bm, [mat])
    for p in obj.data.polygons:
        p.use_smooth = False
    return obj


def forma_base_mineral(d, rnd):
    """Base de roca baja y ancha, con un hueco arriba en el estilo geoda."""
    dd = dict(tam=d["base"], cortes=8, redondez=0.5, inclinacion=0)
    bm = forma_roca(dd, rnd)
    if d["estilo"] == "geoda":
        # Hundir el centro de arriba: el hueco de la geoda.
        sz = max(v.co.z for v in bm.verts)
        for v in bm.verts:
            r = math.hypot(v.co.x / (d["base"][0] / 2), v.co.y / (d["base"][1] / 2))
            if v.co.z > sz * 0.5 and r < 0.75:
                v.co.z -= (0.75 - r) * sz * 0.9
    return bm


# --------------------------------------------------------------------------------------------------------------
# Construcción, render y exportación
# --------------------------------------------------------------------------------------------------------------


def construir_roca(d, carpeta, rapido):
    rnd = random.Random(d["semilla"])
    bm = forma_grupo(d, rnd) if d.get("grupo") else forma_roca(d, rnd)
    alta = c.objeto_desde_bmesh(f"{d['nombre']}_alta", bm)
    detallar(alta, d, rnd, voxel_studs=0.12 if rapido else 0.06)
    baja = version_baja(alta, d["nombre"], d["tris"])
    c.desplegar_uv(baja)
    tam = 256 if rapido else TAM_TEXTURA
    c.hornear(baja, alta, tam=tam, ruta_color=os.path.join(carpeta, "texturas", f"{d['nombre']}_color.png"),
              ruta_normal=os.path.join(carpeta, "texturas", f"{d['nombre']}_normal.png"), extrusion=0.06,
              muestras=8 if rapido else 32)
    alta.hide_render = True
    alta.hide_set(True)
    return baja, alta


def construir_mineral(d, carpeta, rapido):
    rnd = random.Random(d["semilla"])
    dd = dict(d, ruido=0.14, estratos=0.0)
    alta = c.objeto_desde_bmesh(f"{d['nombre']}_alta", forma_base_mineral(d, rnd))
    detallar(alta, dd, rnd, voxel_studs=0.12 if rapido else 0.06)
    baja = version_baja(alta, f"{d['nombre']}_Base", 360)
    c.desplegar_uv(baja)
    tam = 256 if rapido else TAM_TEXTURA
    c.hornear(baja, alta, tam=tam, ruta_color=os.path.join(carpeta, "texturas", f"{d['nombre']}_Base_color.png"),
              ruta_normal=os.path.join(carpeta, "texturas", f"{d['nombre']}_Base_normal.png"), extrusion=0.06,
              muestras=8 if rapido else 32)
    alta.hide_render = True
    alta.hide_set(True)
    crist = cristales(d, rnd, baja)
    # Luz de la PointLight que se recomienda poner en Studio, para que el render se parezca.
    luz = bpy.data.lights.new(f"{d['nombre']}_luz", "POINT")
    luz.color = c.srgb(d["color"])
    luz.energy = 120
    luz.shadow_soft_size = 0.3
    o = bpy.data.objects.new(f"{d['nombre']}_luz", luz)
    o.location = (0, 0, d["base"][2] * 1.6 * E)
    bpy.context.scene.collection.objects.link(o)
    return baja, crist, o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true", help="texturas y render de baja calidad para probar")
    ap.add_argument("--solo", default="", help="nombres separados por comas")
    args = ap.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else None)
    salida = os.path.abspath(args.salida)
    os.makedirs(os.path.join(salida, "texturas"), exist_ok=True)
    tmp = os.path.join(salida, "_render_tmp")
    solo = set(filter(None, args.solo.split(",")))

    c.escena_vacia()
    c.preparar_estudio()
    filas, etiquetas = [], []
    vistas = [("Frente", 0, 14), ("3/4", -45, 26), ("Lateral", -95, 10), ("Detrás", 170, 18), ("Arriba", 20, 75)]
    muestras = 16 if args.rapido else 64
    tam = 300 if args.rapido else 400

    for d in ROCAS:
        if solo and d["nombre"] not in solo:
            continue
        baja, alta = construir_roca(d, salida, args.rapido)
        tris = c.triangulos(baja)
        mn, mx = c.caja_limite([baja])
        dim = (mx - mn) / E
        c.exportar_fbx(os.path.join(salida, f"{d['nombre']}.fbx"), [baja])
        filas.append(c.renderizar_vistas([baja], tmp, vistas, tam=tam, muestras=muestras, prefijo=d["nombre"]))
        etiquetas.append(f"{d['titulo']}\n{d['nombre']}\n{tris} triángulos\n{dim.x:.1f}×{dim.y:.1f}×{dim.z:.1f} st")
        baja.hide_render = True

    for d in MINERALES:
        if solo and d["nombre"] not in solo:
            continue
        base, crist, luz = construir_mineral(d, salida, args.rapido)
        tris = c.triangulos(base) + c.triangulos(crist)
        mn, mx = c.caja_limite([base, crist])
        dim = (mx - mn) / E
        c.exportar_fbx(os.path.join(salida, f"{d['nombre']}.fbx"), [base, crist])
        filas.append(c.renderizar_vistas([base, crist], tmp, vistas, tam=tam, muestras=muestras,
                                         prefijo=d["nombre"]))
        etiquetas.append(f"{d['titulo']}\n{d['nombre']}\n{tris} triángulos\n{dim.x:.1f}×{dim.y:.1f}×{dim.z:.1f} st")
        base.hide_render = crist.hide_render = True
        luz.hide_render = True

    c.montar_hoja(filas, os.path.join(salida, f"hoja_contactos_{args.ronda}.png"),
                  f"Rocas y minerales — ronda {args.ronda}",
                  notas=["Malla de juego (baja) con color + normales horneados de la malla alta. "
                         "Cristales: malla aparte para material Neon."],
                  etiquetas_fila=etiquetas)


if __name__ == "__main__":
    main()
