"""
Biblioteca de formas para los 100 minerales (`minerales.py`). Todo se construye en bmesh y en STUDS
(1 unidad de Blender = 1 stud de Roblox).

Una «pieza» es una malla cerrada con:
  * grupo:   la MeshPart de Roblox a la que va ("" = cuerpo con SurfaceAppearance, "cristal" = Glass,
             "neon" = Neon, "orbita" = trozos que flotan y giran, "interior" = lo que se ve dentro de un cristal).
  * pint:    cómo se pinta (color, rugosidad, metal y emisión por vértice; ver `pintura.py`).
  * relieve: el ruido que se le da a la malla ALTA (golpes, grietas, poros, estratos...) o None.
  * baja:    "limpia" (la malla de juego es la forma original, p. ej. un cristal de caras planas) o "decimar"
             (la malla de juego es la ALTA simplificada, p. ej. una roca).

Las formas genéricas (roca, canto, cristales, geoda...) se configuran desde `minerales_datos.py`; las piezas únicas
(singularidad, semilla cósmica...) tienen su propia función al final del archivo.
"""

import math
import random

import bpy
import bmesh
from mathutils import Matrix, Vector, noise


# --------------------------------------------------------------------------------------------------------------
# Pieza
# --------------------------------------------------------------------------------------------------------------


class Pieza:
    def __init__(self, bm, grupo="", pint=None, relieve=None, baja="limpia", suave=False, voxel=None, tris=None,
                 nombre="pieza", base_plana=False):
        self.bm = bm
        self.grupo = grupo
        self.pint = pint or {}
        self.relieve = relieve
        self.baja = baja
        self.suave = suave
        self.voxel = voxel
        self.tris = tris  # triángulos fijos para "decimar" (si no, reparto del presupuesto)
        self.nombre = nombre
        self.base_plana = base_plana


# --------------------------------------------------------------------------------------------------------------
# Utilidades de bmesh
# --------------------------------------------------------------------------------------------------------------


def unir(dst, src):
    """Copia la geometría de `src` dentro de `dst` (y libera `src`)."""
    m = bpy.data.meshes.new("tmp_union")
    src.to_mesh(m)
    dst.from_mesh(m)
    bpy.data.meshes.remove(m)
    src.free()
    return dst


def transformar(bm, mat):
    bmesh.ops.transform(bm, matrix=mat, verts=bm.verts)
    return bm


def copiar(bm):
    return bm.copy()


def casco(puntos):
    """Envolvente convexa de unos puntos: la forma natural de un cristal o de un trozo de piedra tallado."""
    bm = bmesh.new()
    vs = [bm.verts.new(p) for p in puntos]
    res = bmesh.ops.convex_hull(bm, input=vs)
    sobran = list({v for v in res["geom_interior"] + res["geom_unused"] if isinstance(v, bmesh.types.BMVert)})
    if sobran:
        bmesh.ops.delete(bm, geom=sobran, context="VERTS")
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def girar_a(eje):
    """Matriz 4x4 que lleva +Z a `eje`."""
    return eje.normalized().to_track_quat("Z", "Y").to_matrix().to_4x4()


def cortar(bm, punto, normal):
    """Corta por un plano y quita lo que queda del lado de `normal`; tapa el agujero."""
    geo = bm.verts[:] + bm.edges[:] + bm.faces[:]
    res = bmesh.ops.bisect_plane(bm, geom=geo, plane_co=punto, plane_no=normal, clear_outer=True)
    borde = [e for e in res["geom_cut"] if isinstance(e, bmesh.types.BMEdge)]
    if borde:
        bmesh.ops.holes_fill(bm, edges=borde, sides=0)
    return bm


def bajar_a_cero(bm):
    zmin = min(v.co.z for v in bm.verts)
    bmesh.ops.translate(bm, vec=(0, 0, -zmin), verts=bm.verts)
    bm.normal_update()
    return bm


def caja(bm):
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    return Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))


# --------------------------------------------------------------------------------------------------------------
# Primitivas
# --------------------------------------------------------------------------------------------------------------


def icosfera(r=1.0, sub=3, centro=(0, 0, 0), escala=(1, 1, 1)):
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
    bmesh.ops.scale(bm, vec=escala, verts=bm.verts)
    bmesh.ops.translate(bm, vec=centro, verts=bm.verts)
    return bm


def poliedro(cortes, redondez, rnd, sub=4):
    """Esfera recortada por planos al azar: caras planas de roca rota (redondez 1 = casi esfera)."""
    bm = icosfera(1.0, sub)
    for _ in range(cortes):
        n = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-0.6, 1))).normalized()
        d = rnd.uniform(0.55, 0.85) + redondez * 0.12
        cortar(bm, n * d, n)
    return bm


def roca(tam, cortes=8, redondez=0.5, rnd=None, base=0.3, afinar=0.0, inclinar=0.0):
    """Roca de caras rotas con la base plana en z = 0. `afinar` estrecha la parte de arriba (agujas)."""
    rnd = rnd or random.Random(1)
    bm = poliedro(cortes, redondez, rnd)
    sx, sy, sz = tam
    bmesh.ops.scale(bm, vec=(sx / 2, sy / 2, sz / 2), verts=bm.verts)
    if afinar:
        for v in bm.verts:
            t = v.co.z / sz + 0.5
            f = 1.0 - afinar * max(0.0, t) ** 1.4
            v.co.x *= f
            v.co.y *= f
    if inclinar:
        transformar(bm, Matrix.Rotation(math.radians(inclinar), 4, "X"))
    if base is not None:
        cortar(bm, (0, 0, -sz * base), (0, 0, -1))
    bajar_a_cero(bm)
    bm.normal_update()
    return bm


def canto(tam, rnd, irregular=0.12, base=0.18, sub=3):
    """Canto rodado: elipsoide con bultos suaves de baja frecuencia."""
    bm = icosfera(1.0, sub)
    s = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), rnd.uniform(0, 50)))
    for v in bm.verts:
        v.co *= 1.0 + irregular * noise.noise(v.co * 1.3 + s)
    bmesh.ops.scale(bm, vec=(tam[0] / 2, tam[1] / 2, tam[2] / 2), verts=bm.verts)
    if base:
        cortar(bm, (0, 0, -tam[2] / 2 * (1 - base)), (0, 0, -1))
    return bajar_a_cero(bm)


def gema(base, eje, largo, radio, lados=6, punta=0.3, rnd=None, irregular=0.08, doble=False, aplanar=1.0,
         enterrado=0.4, giro=None, punta_desc=0.15, estrechar=0.92):
    """
    Cristal natural: prisma de `lados` caras con punta piramidal (y otra abajo si `doble`), hecho con la envolvente
    convexa de los puntos, así siempre es cerrado. `aplanar` < 1 lo hace tabular. `enterrado` es lo que se mete
    por debajo de `base` (para que nazca de la roca).
    """
    rnd = rnd or random.Random(1)
    giro = rnd.uniform(0, math.tau) if giro is None else giro
    pts = []
    cuerpo = largo * (1 - punta)
    z0 = -enterrado * radio if not doble else 0.0
    for i in range(lados):
        a = giro + i * math.tau / lados
        r = radio * (1 + rnd.uniform(-irregular, irregular))
        x, y = math.cos(a) * r, math.sin(a) * r * aplanar
        pts.append(Vector((x, y, z0 if not doble else largo * punta)))
        pts.append(Vector((x * estrechar, y * estrechar, cuerpo)))
    pts.append(Vector((rnd.uniform(-punta_desc, punta_desc) * radio, rnd.uniform(-punta_desc, punta_desc) * radio,
                       largo)))
    if doble:
        pts.append(Vector((0, 0, 0)))
    m = Matrix.Translation(base) @ girar_a(eje)
    return casco([m @ p for p in pts])


def cubo(centro, lado, rot=(0, 0, 0), estirar=(1, 1, 1)):
    pts = [Vector((x * estirar[0], y * estirar[1], z * estirar[2])) * lado / 2
           for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    m = Matrix.Translation(centro) @ Matrix.LocRotScale(None, _euler(rot), None)
    return casco([m @ p for p in pts])


def _euler(rot):
    from mathutils import Euler
    return Euler([math.radians(a) for a in rot]).to_quaternion()


PHI = (1 + 5 ** 0.5) / 2


def platonico(tipo, centro=(0, 0, 0), r=1.0, rot=(0, 0, 0)):
    """Los cinco sólidos platónicos (inscritos en una esfera de radio r)."""
    if tipo == "tetra":
        pts = [(1, 1, 1), (1, -1, -1), (-1, 1, -1), (-1, -1, 1)]
    elif tipo == "cubo":
        pts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
    elif tipo == "octa":
        pts = [(1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
    elif tipo == "dodeca":
        pts = [(x, y, z) for x in (-1, 1) for y in (-1, 1) for z in (-1, 1)]
        for a in (-1, 1):
            for b in (-1, 1):
                pts += [(0, a / PHI, b * PHI), (a / PHI, b * PHI, 0), (a * PHI, 0, b / PHI)]
    else:  # icosa
        pts = []
        for a in (-1, 1):
            for b in (-1, 1):
                pts += [(0, a, b * PHI), (a, b * PHI, 0), (a * PHI, 0, b)]
    vs = [Vector(p).normalized() * r for p in pts]
    m = Matrix.Translation(centro) @ Matrix.LocRotScale(None, _euler(rot), None)
    return casco([m @ v for v in vs])


def tubo(puntos, radios, lados=6, punta=True):
    """Tubo cerrado a lo largo de una polilínea (raíces, rayos, ramas de coral). Si `punta`, acaba en un vértice."""
    bm = bmesh.new()
    puntos = [Vector(p) for p in puntos]
    anillos = []
    ref = Vector((0, 0, 1))
    n = len(puntos)
    for i, p in enumerate(puntos):
        t = (puntos[min(i + 1, n - 1)] - puntos[max(i - 1, 0)]).normalized()
        if abs(t.dot(ref)) > 0.9:
            ref = Vector((1, 0, 0))
        u = t.cross(ref).normalized()
        w = t.cross(u).normalized()
        ref = w
        if punta and i == n - 1:
            anillos.append([bm.verts.new(p)])
            continue
        r = radios[i]
        anillos.append([bm.verts.new(p + (u * math.cos(a) + w * math.sin(a)) * r)
                        for a in (k * math.tau / lados for k in range(lados))])
    for i in range(n - 1):
        a, b = anillos[i], anillos[i + 1]
        for k in range(lados):
            k2 = (k + 1) % lados
            if len(b) == 1:
                bm.faces.new((a[k], a[k2], b[0]))
            else:
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
    bm.faces.new(list(reversed(anillos[0])))
    if len(anillos[-1]) > 1:
        bm.faces.new(anillos[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def toro(R, r, seg=32, lados=8, centro=(0, 0, 0), rot=(0, 0, 0), escala_z=1.0):
    bm = bmesh.new()
    anillos = []
    for i in range(seg):
        a = i * math.tau / seg
        cen = Vector((math.cos(a) * R, math.sin(a) * R, 0))
        rad = Vector((math.cos(a), math.sin(a), 0))
        anillos.append([bm.verts.new(cen + rad * math.cos(b) * r + Vector((0, 0, math.sin(b) * r * escala_z)))
                        for b in (k * math.tau / lados for k in range(lados))])
    for i in range(seg):
        a, b = anillos[i], anillos[(i + 1) % seg]
        for k in range(lados):
            k2 = (k + 1) % lados
            bm.faces.new((a[k], b[k], b[k2], a[k2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = Matrix.Translation(centro) @ Matrix.LocRotScale(None, _euler(rot), None)
    return transformar(bm, m)


def disco(r_in, r_out, alto, seg=40, centro=(0, 0, 0), rot=(0, 0, 0), alabeo=0.0, rnd=None):
    """Anillo plano con grosor (disco de acreción, anillo de energía). `alabeo` lo ondula."""
    bm = bmesh.new()
    rnd = rnd or random.Random(2)
    fase = rnd.uniform(0, 6)
    filas = []
    for i in range(seg):
        a = i * math.tau / seg
        dz = alabeo * math.sin(a * 2 + fase)
        ca, sa = math.cos(a), math.sin(a)
        filas.append([bm.verts.new((ca * r_in, sa * r_in, -alto / 2 + dz * 0.6)),
                      bm.verts.new((ca * r_out, sa * r_out, -alto / 4 + dz)),
                      bm.verts.new((ca * r_out, sa * r_out, alto / 4 + dz)),
                      bm.verts.new((ca * r_in, sa * r_in, alto / 2 + dz * 0.6))])
    for i in range(seg):
        a, b = filas[i], filas[(i + 1) % seg]
        for k in range(4):
            k2 = (k + 1) % 4
            bm.faces.new((a[k], b[k], b[k2], a[k2]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = Matrix.Translation(centro) @ Matrix.LocRotScale(None, _euler(rot), None)
    return transformar(bm, m)


def loft(perfil, n=16, lados=12, z0=0.0, z1=1.0, cerrar_abajo=True, cerrar_arriba=True):
    """
    Superficie de revolución deformable: `perfil(t)` -> (rx, ry, cx, cy, giro) para t de 0 a 1 entre z0 y z1.
    Los extremos se cierran con un vértice (punta) si el radio es ~0, o con una tapa.
    """
    bm = bmesh.new()
    anillos = []
    for i in range(n + 1):
        t = i / n
        rx, ry, cx, cy, g = perfil(t)
        z = z0 + (z1 - z0) * t
        if rx < 1e-4 and ry < 1e-4:
            anillos.append([bm.verts.new((cx, cy, z))])
            continue
        anillos.append([bm.verts.new((cx + math.cos(a + g) * rx, cy + math.sin(a + g) * ry, z))
                        for a in (k * math.tau / lados for k in range(lados))])
    for i in range(n):
        a, b = anillos[i], anillos[i + 1]
        if len(a) == 1 and len(b) == 1:
            continue
        for k in range(lados):
            k2 = (k + 1) % lados
            if len(a) == 1:
                bm.faces.new((a[0], b[k2], b[k]))
            elif len(b) == 1:
                bm.faces.new((a[k], a[k2], b[0]))
            else:
                bm.faces.new((a[k], a[k2], b[k2], b[k]))
    if len(anillos[0]) > 1:
        bm.faces.new(list(reversed(anillos[0])))
    if len(anillos[-1]) > 1:
        bm.faces.new(anillos[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def estrella(puntas=5, R=1.0, r=0.42, grosor=0.45, centro=(0, 0, 0), rot=(0, 0, 0)):
    """Estrella tallada: anillo de puntas en el plano XZ con un vértice delante y otro detrás (caras de gema)."""
    bm = bmesh.new()
    anillo = []
    for i in range(puntas * 2):
        a = math.pi / 2 + i * math.pi / puntas
        rr = R if i % 2 == 0 else r
        anillo.append(bm.verts.new((math.cos(a) * rr, 0, math.sin(a) * rr)))
    delante = bm.verts.new((0, -grosor, 0))
    detras = bm.verts.new((0, grosor, 0))
    for i in range(len(anillo)):
        a, b = anillo[i], anillo[(i + 1) % len(anillo)]
        bm.faces.new((a, b, delante))
        bm.faces.new((b, a, detras))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    m = Matrix.Translation(centro) @ Matrix.LocRotScale(None, _euler(rot), None)
    return transformar(bm, m)


def metabolas(bolas, resolucion=0.08, umbral=0.6, capsulas=()):
    """Forma orgánica con metabolas. bolas: [(pos, radio)] (radio aproximado de la esfera que sale)."""
    mb = bpy.data.metaballs.new("mb_tmp")
    mb.resolution = resolucion
    mb.render_resolution = resolucion
    mb.threshold = umbral
    k = 1.0 / 0.575  # una metabola sola mide 0,575 veces su radio con umbral 0,6
    for p, r in bolas:
        e = mb.elements.new()
        e.co = p
        e.radius = r * k
    for a, b, r in capsulas:
        a, b = Vector(a), Vector(b)
        e = mb.elements.new(type="CAPSULE")
        e.co = (a + b) / 2
        e.radius = r * k
        e.size_x = (b - a).length / 2
        e.rotation = (b - a).normalized().to_track_quat("X", "Z")
    obj = bpy.data.objects.new("mb_tmp", mb)
    bpy.context.scene.collection.objects.link(obj)
    dep = bpy.context.evaluated_depsgraph_get()
    malla = bpy.data.meshes.new_from_object(obj.evaluated_get(dep))
    bpy.data.objects.remove(obj)
    bpy.data.metaballs.remove(mb)
    bm = bmesh.new()
    bm.from_mesh(malla)
    bpy.data.meshes.remove(malla)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def esquirla(centro, tam, rnd, alargar=1.6):
    """Trozo pequeño de piedra o cristal (8-10 puntos al azar)."""
    pts = []
    for _ in range(9):
        v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1) * alargar)).normalized()
        pts.append(v * tam * rnd.uniform(0.6, 1.0))
    m = Matrix.Translation(centro) @ Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ \
        Matrix.Rotation(rnd.uniform(-1, 1), 4, "X")
    return casco([m @ p for p in pts])


def rayo(a, b, rnd, quiebros=6, desvio=0.25, radio=0.05):
    """Rayo en zigzag de `a` a `b` (tubo fino acabado en punta)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    perp1 = d.orthogonal().normalized()
    perp2 = d.cross(perp1).normalized()
    pts = [a]
    for i in range(1, quiebros):
        t = i / quiebros
        off = (perp1 * rnd.uniform(-1, 1) + perp2 * rnd.uniform(-1, 1)) * desvio * d.length / quiebros * 2
        pts.append(a + d * t + off)
    pts.append(b)
    radios = [radio * (1 - 0.6 * i / len(pts)) for i in range(len(pts))]
    return tubo(pts, radios, lados=4, punta=True)


# --------------------------------------------------------------------------------------------------------------
# Relieves y pinturas predefinidos (se pueden sobrescribir desde los datos)
# --------------------------------------------------------------------------------------------------------------

RELIEVE_ROCA = dict(bultos=0.05, fino=0.018, grano=0.006, grietas=0.03, lascas=0.012)
RELIEVE_LISO = dict(bultos=0.025, fino=0.006, grano=0.002)
RELIEVE_CRISTAL = None  # los cristales no llevan ruido: la ALTA solo redondea un poco las aristas


def R(base=None, **kw):
    d = dict(RELIEVE_ROCA if base is None else base)
    d.update(kw)
    return d


# --------------------------------------------------------------------------------------------------------------
# Formas genéricas (se eligen con forma="..." en los datos)
# --------------------------------------------------------------------------------------------------------------


def _base_roca(d, rnd, tam=None, pint_key="roca"):
    """La roca de base de un mineral (o la roca entera)."""
    tam = tam or d["tam"]
    bm = roca(tam, d.get("cortes", 8), d.get("redondez", 0.5), rnd, base=d.get("base", 0.3),
              afinar=d.get("afinar", 0.0), inclinar=d.get("inclinar", 0.0))
    return Pieza(bm, "", d["pint"][pint_key], d.get("relieve", RELIEVE_ROCA), "decimar", nombre="roca",
                 base_plana=True)


def f_roca(d, rnd):
    return [_base_roca(d, rnd, d.get("tam_roca"))]


def f_canto(d, rnd):
    bm = canto(d["tam"], rnd, d.get("irregular", 0.12), d.get("base", 0.18))
    return [Pieza(bm, "", d["pint"]["roca"], d.get("relieve", RELIEVE_LISO), "decimar", nombre="canto",
                  base_plana=True)]


def f_blob(d, rnd):
    """Masa orgánica de metabolas (arcilla, escoria, hematita botrioidal...)."""
    sx, sy, sz = d["tam"]
    bolas = []
    n = d.get("bolas", 9)
    for i in range(n):
        r = rnd.uniform(*d.get("radios", (0.25, 0.42))) * min(sx, sy)
        p = Vector((rnd.uniform(-0.5, 0.5) * (sx - r), rnd.uniform(-0.5, 0.5) * (sy - r), r * 0.6 +
                    rnd.uniform(0, 1) * max(0.0, sz - 2 * r)))
        bolas.append((p, r))
    bm = metabolas(bolas, resolucion=min(sx, sy) / 26)
    bm = cortar(bm, (0, 0, min(v.co.z for v in bm.verts) + sz * 0.06), (0, 0, -1))
    bajar_a_cero(bm)
    return [Pieza(bm, "", d["pint"]["roca"], d.get("relieve", RELIEVE_LISO), "decimar", nombre="blob",
                  base_plana=True)]


def f_laminas(d, rnd):
    """Pila de láminas planas (pizarra, mica, yeso), cada una algo girada y desplazada."""
    sx, sy, sz = d["tam"]
    n = d.get("n", 6)
    piezas = []
    bm_total = bmesh.new()
    z = 0.0
    grosor = sz / n
    for i in range(n):
        f = 1.0 - 0.35 * (i / n) * rnd.uniform(0.6, 1.2)
        lam = roca((sx * f, sy * f * rnd.uniform(0.85, 1.05), grosor * rnd.uniform(1.0, 1.6)), 7, 0.1, rnd,
                   base=0.0)
        # Aplastar la parte de arriba también: lámina con dos caras planas.
        lam = cortar(lam, (0, 0, grosor * rnd.uniform(0.85, 1.05)), (0, 0, 1))
        transformar(lam, Matrix.Translation((rnd.uniform(-0.12, 0.12) * sx, rnd.uniform(-0.1, 0.1) * sy, z)) @
                    Matrix.Rotation(rnd.uniform(-0.25, 0.25), 4, "Z") @ Matrix.Rotation(rnd.uniform(-0.04, 0.04), 4,
                                                                                         "X"))
        z += grosor * rnd.uniform(0.78, 0.92)
        unir(bm_total, lam)
    grupo = d.get("grupo_laminas", "")
    if grupo == "cristal":
        piezas.append(Pieza(bm_total, "cristal", d["pint"]["roca"], None, "decimar", tris=d.get("tris_laminas", 1400),
                            nombre="laminas", voxel=grosor / 6))
    else:
        piezas.append(Pieza(bm_total, "", d["pint"]["roca"], d.get("relieve", R(estratos=0.0, bultos=0.02)),
                            "decimar", nombre="laminas", base_plana=True, voxel=grosor / 5))
    return piezas


def f_columnas(d, rnd):
    """Columnas hexagonales de basalto, de distintas alturas y con la cara de arriba algo inclinada."""
    sx, sy, sz = d["tam"]
    r = d.get("radio_col", sx / 6.5)
    bm_total = bmesh.new()
    celdas = []
    for q in range(-3, 4):
        for s in range(-3, 4):
            x = r * 1.73 * (q + s / 2)
            y = r * 1.5 * s
            if (x / (sx / 2)) ** 2 + (y / (sy / 2)) ** 2 <= 1.0:
                celdas.append((x, y))
    for x, y in celdas:
        dist = math.hypot(x / sx, y / sy) * 2
        h = sz * (1.0 - 0.55 * dist) * rnd.uniform(0.7, 1.05)
        pts = []
        for i in range(6):
            a = math.pi / 6 + i * math.tau / 6
            rr = r * 0.94
            pts.append(Vector((x + math.cos(a) * rr, y + math.sin(a) * rr, 0)))
        inc = Vector((rnd.uniform(-0.18, 0.18), rnd.uniform(-0.18, 0.18)))
        arriba = [Vector((p.x, p.y, h + (p.x - x) * inc.x + (p.y - y) * inc.y)) for p in pts]
        unir(bm_total, casco(pts + arriba))
    return [Pieza(bm_total, "", d["pint"]["roca"], d.get("relieve", R(bultos=0.012, fino=0.006, grietas=0.015,
                                                                     lascas=0.006)),
                  "decimar", nombre="columnas", base_plana=True, voxel=r / 7)]


def f_grupo(d, rnd):
    """Montón de piedras pequeñas apelmazadas (grava, pepitas)."""
    sx, sy, sz = d["tam"]
    bm_total = bmesh.new()
    n = d.get("n", 12)
    for i in range(n):
        t = i / n
        tam = rnd.uniform(0.28, 0.5) * min(sx, sy) * (1.25 if i == 0 else 1.0)
        ang = rnd.uniform(0, math.tau)
        rad = (0 if i == 0 else rnd.uniform(0.2, 1.0)) * 0.5
        p = Vector((math.cos(ang) * rad * (sx - tam), math.sin(ang) * rad * (sy - tam), 0))
        z = tam * 0.3 + (sz - tam) * (1 - rad * 1.6) * rnd.uniform(0.2, 0.8) if sz > tam else tam * 0.3
        piedra = canto((tam, tam * rnd.uniform(0.7, 1.0), tam * rnd.uniform(0.55, 0.8)), rnd, 0.15, 0.0, sub=2)
        transformar(piedra, Matrix.Translation((p.x, p.y, max(0.0, z - tam * 0.4))) @
                    Matrix.Rotation(rnd.uniform(0, 6.28), 4, "Z") @ Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, "X"))
        unir(bm_total, piedra)
    bm_total = cortar(bm_total, (0, 0, 0.02 * sz), (0, 0, -1))
    bajar_a_cero(bm_total)
    return [Pieza(bm_total, "", d["pint"]["roca"], d.get("relieve", R(RELIEVE_LISO, grietas=0.01)), "decimar",
                  nombre="grupo", base_plana=True)]


def _cristales_sobre(d, rnd, cuerpo, cfg):
    """
    Grupo de cristales sobre una base (o sueltos si no hay base).
    cfg: estilo (hex|cubo|octa|bipiramide|esquirla|tabla|prisma4), n, largo (min,max), grosor (min,max),
         abrir (grados máx.), radio (reparto en XY, fracción del tamaño), z (altura de nacimiento), grupo, pint.
    """
    sx, sy, sz = d["tam"]
    piezas = []
    bm_total = bmesh.new()
    n = cfg.get("n", 7)
    lmin, lmax = cfg.get("largo", (0.4, 0.8))
    gmin, gmax = cfg.get("grosor", (0.1, 0.2))
    estilo = cfg.get("estilo", "hex")
    z_base = cfg.get("z", sz * 0.55)
    reparto = cfg.get("radio", 0.3)
    abrir = cfg.get("abrir", 40)
    S = max(sx, sy, sz)
    for i in range(n):
        ang = rnd.uniform(0, math.tau)
        rr = 0.0 if i == 0 else rnd.uniform(0.3, 1.0) * reparto
        pos = Vector((math.cos(ang) * rr * sx, math.sin(ang) * rr * sy, z_base * (1 - 0.35 * rr / max(reparto, 1e-3))))
        if cfg.get("pos"):
            pos = Vector(cfg["pos"][i % len(cfg["pos"])])
        inc = 0.0 if i == 0 else rnd.uniform(abrir * 0.35, abrir)
        eje = Matrix.Rotation(math.radians(inc), 3, Vector((-math.sin(ang), math.cos(ang), 0))) @ Vector((0, 0, 1))
        if cfg.get("eje"):
            eje = Vector(cfg["eje"]).normalized()
        k = 1.0 if i == 0 else rnd.uniform(0.55, 0.9)
        largo = (lmax if i == 0 else rnd.uniform(lmin, lmax)) * S * (1 if i == 0 else k)
        grosor = (gmax if i == 0 else rnd.uniform(gmin, gmax)) * S
        if estilo == "hex":
            g = gema(pos, eje, largo, grosor, 6, cfg.get("punta", 0.28), rnd, doble=cfg.get("doble", False),
                     aplanar=cfg.get("aplanar", 1.0))
        elif estilo == "prisma4":
            g = gema(pos, eje, largo, grosor, 4, cfg.get("punta", 0.45), rnd, irregular=0.12)
        elif estilo == "bipiramide":
            g = gema(pos - eje * largo * 0.2, eje, largo, grosor, 6, 0.42, rnd, doble=True, estrechar=0.96)
        elif estilo == "barril":
            g = gema(pos, eje, largo, grosor, 6, 0.08, rnd, estrechar=0.85, punta_desc=0.05)
        elif estilo == "tabla":
            g = gema(pos, eje, largo, grosor, 6, 0.18, rnd, aplanar=0.35, estrechar=0.97)
        elif estilo == "cubo":
            lado = grosor * 2
            g = cubo(pos + Vector((0, 0, lado * 0.25)), lado,
                     (rnd.uniform(-30, 30), rnd.uniform(-30, 30), rnd.uniform(0, 90)))
        elif estilo == "octa":
            g = platonico("octa", pos + Vector((0, 0, grosor * 0.5)), grosor * 1.4,
                          (rnd.uniform(-25, 25), rnd.uniform(-25, 25), rnd.uniform(0, 90)))
        elif estilo == "esquirla":
            g = gema(pos, eje, largo, grosor, 4, 0.6, rnd, irregular=0.25, punta_desc=0.3)
        else:
            raise ValueError(estilo)
        unir(bm_total, g)
    grupo = cfg.get("grupo", "cristal")
    piezas.append(Pieza(bm_total, grupo, d["pint"][cfg.get("pint", "cristal")], None, "limpia",
                        nombre="cristales", voxel=gmin * S / 3))
    return piezas


def f_cristales(d, rnd):
    """Base de roca (opcional) + grupo de cristales."""
    piezas = []
    cfg = d["cristales"]
    if d.get("con_base", True):
        tam_base = d.get("tam_base", (d["tam"][0], d["tam"][1], d["tam"][2] * 0.35))
        piezas.append(_base_roca(d, rnd, tam_base))
        cfg = dict(cfg)
        cfg.setdefault("z", tam_base[2] * 0.75)
    else:
        cfg = dict(cfg)
        cfg.setdefault("z", 0.0)
    piezas += _cristales_sobre(d, rnd, None, cfg)
    for extra in d.get("mas_cristales", ()):
        piezas += _cristales_sobre(d, rnd, None, extra)
    return piezas


def f_geoda(d, rnd):
    """
    Geoda abierta: media cáscara de roca (hueca) con cristales que apuntan hacia el centro, vista de frente (-Y).
    """
    sx, sy, sz = d["tam"]
    R0 = max(sx, sz) / 2
    exterior = canto((sx, sy * 2, sz), rnd, 0.05, 0.0, sub=3)
    bmesh.ops.translate(exterior, vec=(0, 0, -sz / 2), verts=exterior.verts)
    cortar(exterior, (0, -sy * 0.0, 0), (0, -1, 0))  # quitar la mitad delantera
    # Hueco: quitar una esfera de dentro con un booleano por voxel (se hace en la ALTA con "hueco").
    hueco = d.get("hueco", 0.75)
    bajar_a_cero(exterior)
    bm_c = bmesh.new()
    cfg = d["cristales"]
    n = cfg.get("n", 22)
    centro = Vector((0, sy * 0.0, sz / 2))
    S = max(sx, sy, sz)
    lmin, lmax = cfg.get("largo", (0.12, 0.22))
    gmin, gmax = cfg.get("grosor", (0.04, 0.07))
    for i in range(n):
        # Puntos repartidos por la pared interior (semiesfera trasera, y >= 0).
        u = rnd.uniform(-1, 1)
        th = rnd.uniform(0, math.tau)
        dirv = Vector((math.sqrt(1 - u * u) * math.cos(th), abs(math.sqrt(1 - u * u) * math.sin(th)) + 0.15, u))
        dirv.normalize()
        pared = centro + Vector((dirv.x * sx / 2, dirv.y * sy, dirv.z * sz / 2)) * hueco
        eje = (centro - pared).normalized().lerp(Vector((0, -1, 0.3)), 0.2)
        g = gema(pared, eje, rnd.uniform(lmin, lmax) * S, rnd.uniform(gmin, gmax) * S, 6, 0.4, rnd, enterrado=0.7)
        unir(bm_c, g)
    # Relieve suave: uno fuerte tapa los cristales con bultos de roca dentro del hueco.
    rel = d.get("relieve", dict(bultos=0.022, fino=0.008, grano=0.003, grietas=0.012))
    p_roca = Pieza(exterior, "", d["pint"]["roca"], dict(rel, hueco=hueco, hueco_c=tuple(centro),
                                                         hueco_r=(sx / 2, sy, sz / 2)),
                   "limpia", nombre="cascara", base_plana=True, suave=True)
    return [p_roca, Pieza(bm_c, d.get("grupo_cristal", "cristal"), d["pint"]["cristal"], None, "limpia",
                          nombre="cristales", voxel=gmin * S / 3)]


def f_pepitas(d, rnd):
    """Roca con nódulos o pepitas medio enterradas (oro, estaño...)."""
    piezas = [_base_roca(d, rnd)]
    sx, sy, sz = d["tam"]
    cfg = d["pepitas"]
    bm_p = bmesh.new()
    base_tmp = roca(d["tam"], d.get("cortes", 8), d.get("redondez", 0.5), random.Random(d["semilla"]),
                    base=d.get("base", 0.3))
    # Puntos de la superficie de la roca (sus vértices) donde asoman las pepitas.
    vs = [v for v in base_tmp.verts if v.co.z > sz * 0.15]
    S = max(sx, sy, sz)
    for i in range(cfg.get("n", 6)):
        v = rnd.choice(vs)
        r = rnd.uniform(*cfg.get("radio", (0.06, 0.12))) * S
        centro = v.co - v.normal * r * 0.3 if v.normal.length > 0 else v.co
        if cfg.get("forma", "pepita") == "esfera":
            bmp = icosfera(r, 2, centro)
        else:
            bmp = esquirla(centro, r, rnd, 0.8)
        unir(bm_p, bmp)
    base_tmp.free()
    piezas.append(Pieza(bm_p, cfg.get("grupo", ""), d["pint"][cfg.get("pint", "pepita")],
                        cfg.get("relieve", dict(bultos=0.012, fino=0.004)), "decimar",
                        tris=cfg.get("tris", 500), nombre="pepitas", voxel=cfg.get("radio", (0.06, 0.1))[0] * S / 4))
    return piezas


# --------------------------------------------------------------------------------------------------------------
# Extras que se añaden a cualquier forma (d["extras"])
# --------------------------------------------------------------------------------------------------------------


def x_nucleo(d, rnd, piezas, cfg):
    """
    Núcleo que brilla por las grietas: la roca se vuelve a hacer más pequeña (desplazada hacia dentro) y va en el
    grupo Neon. La roca lleva surcos profundos (relieve "surcos") para que se vea a través.
    """
    roca_p = piezas[0]
    nucleo = copiar(roca_p.bm)
    bmesh.ops.remove_doubles(nucleo, verts=nucleo.verts, dist=1e-4)
    cmin, cmax = caja(nucleo)
    cen = (cmin + cmax) / 2
    S = max(cmax - cmin)
    k = cfg.get("escala", 0.86)
    for v in nucleo.verts:
        v.co = cen + (v.co - cen) * k
    return [Pieza(nucleo, cfg.get("grupo", "neon"), d["pint"][cfg.get("pint", "nucleo")],
                  dict(bultos=0.02), "decimar", tris=cfg.get("tris", 220), nombre="nucleo", suave=True,
                  voxel=S / 50)]


def x_orbitas(d, rnd, piezas, cfg):
    """Trozos que flotan en anillos alrededor (grupo orbita, para hacerlos girar en el cliente)."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    bm_o = bmesh.new()
    cen = Vector(cfg.get("centro", (0, 0, sz * 0.5)))
    for anillo in cfg.get("anillos", [dict(n=7, radio=0.75, alto=0.0, incl=12, tam=(0.05, 0.09))]):
        n = anillo["n"]
        R0 = anillo["radio"] * S
        inc = math.radians(anillo.get("incl", 0))
        for i in range(n):
            a = i * math.tau / n + rnd.uniform(-0.25, 0.25)
            p = Vector((math.cos(a) * R0, math.sin(a) * R0, rnd.uniform(-0.05, 0.05) * S))
            p = Matrix.Rotation(inc, 3, "X") @ p
            p += cen + Vector((0, 0, anillo.get("alto", 0) * S))
            t = rnd.uniform(*anillo.get("tam", (0.05, 0.09))) * S
            if anillo.get("forma") == "octa":
                g = platonico("octa", p, t, (rnd.uniform(0, 90), rnd.uniform(0, 90), 0))
            elif anillo.get("forma") == "cubo":
                g = cubo(p, t * 1.3, (rnd.uniform(0, 90), rnd.uniform(0, 90), 0))
            else:
                g = esquirla(p, t, rnd)
            unir(bm_o, g)
    return [Pieza(bm_o, cfg.get("grupo", "orbita"), d["pint"][cfg.get("pint", "orbita")], None, "limpia",
                  nombre="orbitas", voxel=S / 90)]


def x_motas_neon(d, rnd, piezas, cfg):
    """Puntos de luz incrustados en la superficie de la roca (estrellas, chispas): octaedros pequeños en Neon."""
    roca_p = piezas[0]
    vs = [v for v in roca_p.bm.verts if v.co.z > 0.05]
    cmin, cmax = caja(roca_p.bm)
    S = max(cmax - cmin)
    bm_m = bmesh.new()
    for i in range(cfg.get("n", 20)):
        v = rnd.choice(vs)
        t = rnd.uniform(*cfg.get("tam", (0.015, 0.035))) * S
        nrm = v.normal if v.normal.length > 0 else Vector((0, 0, 1))
        unir(bm_m, platonico("octa", v.co + nrm * t * 0.1, t, (rnd.uniform(0, 90), rnd.uniform(0, 90), 0)))
    return [Pieza(bm_m, "neon", d["pint"][cfg.get("pint", "motas")], None, "limpia", nombre="motas", voxel=S / 120)]


def x_interior(d, rnd, piezas, cfg):
    """Algo dentro de un cristal: núcleo encogido del propio cristal (energía interna)."""
    origen = [p for p in piezas if p.grupo == cfg.get("de", "cristal")][0]
    bm = copiar(origen.bm)
    # Encoger cada cristal hacia su propio eje: se aproxima encogiendo hacia el centro de cada isla.
    islas = _islas(bm)
    k = cfg.get("escala", 0.55)
    for isla in islas:
        cen = sum((v.co for v in isla), Vector()) / len(isla)
        for v in isla:
            v.co = cen + (v.co - cen) * k
    return [Pieza(bm, cfg.get("grupo", "neon"), d["pint"][cfg.get("pint", "nucleo")], None, "limpia",
                  nombre="interior", voxel=cfg.get("voxel"))]


def _islas(bm):
    bm.verts.ensure_lookup_table()
    visto = set()
    islas = []
    for v in bm.verts:
        if v.index in visto:
            continue
        pila, isla = [v], []
        visto.add(v.index)
        while pila:
            a = pila.pop()
            isla.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in visto:
                    visto.add(b.index)
                    pila.append(b)
        islas.append(isla)
    return islas


def x_escarcha(d, rnd, piezas, cfg):
    """Corona de púas de hielo en el suelo alrededor (congelación visible)."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    bm = bmesh.new()
    n = cfg.get("n", 16)
    for i in range(n):
        a = i * math.tau / n + rnd.uniform(-0.15, 0.15)
        r = cfg.get("radio", 0.55) * S * rnd.uniform(0.85, 1.15)
        p = Vector((math.cos(a) * r, math.sin(a) * r, 0))
        eje = Vector((math.cos(a) * 0.6, math.sin(a) * 0.6, 1))
        unir(bm, gema(p, eje, rnd.uniform(0.12, 0.26) * S, rnd.uniform(0.025, 0.05) * S, 5, 0.5, rnd,
                      irregular=0.2, enterrado=0.8))
    return [Pieza(bm, cfg.get("grupo", "cristal"), d["pint"][cfg.get("pint", "escarcha")], None, "limpia",
                  nombre="escarcha", voxel=S / 150)]


def x_estrellas(d, rnd, piezas, cfg):
    """Estrellas dentro de los cristales: octaedros diminutos en Neon repartidos por el interior de cada uno."""
    origen = [p for p in piezas if p.grupo == "cristal"][0]
    cmin, cmax = caja(origen.bm)
    S = max(cmax - cmin)
    bm = bmesh.new()
    islas = _islas(origen.bm)
    for i in range(cfg.get("n", 30)):
        isla = rnd.choice(islas)
        cen = sum((v.co for v in isla), Vector()) / len(isla)
        p = cen.lerp(rnd.choice(isla).co, rnd.uniform(0.0, 0.7))
        t = rnd.uniform(*cfg.get("tam", (0.008, 0.016))) * S
        unir(bm, platonico("octa", p, t, (rnd.uniform(0, 90), rnd.uniform(0, 90), 0)))
    return [Pieza(bm, "neon", d["pint"][cfg.get("pint", "motas")], None, "limpia", nombre="estrellas",
                  voxel=S / 300)]


EXTRAS = dict(estrellas=x_estrellas, nucleo=x_nucleo, orbitas=x_orbitas, motas_neon=x_motas_neon, interior=x_interior,
              escarcha=x_escarcha)


# --------------------------------------------------------------------------------------------------------------
# Formas únicas
# --------------------------------------------------------------------------------------------------------------


def f_agata(d, rnd):
    """Nódulo de ágata partido: se ve la cara cortada (de frente) con las bandas, y la corteza rugosa detrás."""
    sx, sy, sz = d["tam"]
    bm = canto((sx, sy * 2, sz), rnd, 0.08, 0.0, sub=4)
    cortar(bm, (0, 0, 0), (0, -1, 0))
    transformar(bm, Matrix.Rotation(math.radians(-12), 4, "X"))
    bajar_a_cero(bm)
    return [Pieza(bm, "", d["pint"]["roca"], dict(bultos=0.02, fino=0.008, grano=0.003, corte_liso=True),
                  "decimar", nombre="agata", base_plana=True)]


def f_coral(d, rnd):
    """Coral ramificado sobre una piedra (ramas como tubos que se dividen)."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    piezas = [_base_roca(d, rnd, (sx * 0.75, sy * 0.75, sz * 0.25))]
    bm = bmesh.new()

    def rama(p, dirv, largo, r, nivel):
        pts, rad = [p], [r]
        q = Vector(p)
        dd = Vector(dirv)
        pasos = 5
        for i in range(pasos):
            dd = (dd + Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0.15))).normalized()
            q = q + dd * largo / pasos
            pts.append(Vector(q))
            rad.append(r * (1 - 0.5 * (i + 1) / pasos))
        unir(bm, tubo(pts, rad, 6, punta=False))
        unir(bm, icosfera(rad[-1] * 1.25, 1, q))
        if nivel > 0:
            for k in range(2):
                nd = (dd + Vector((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), 0.3))).normalized()
                rama(pts[3], nd, largo * 0.65, rad[3] * 0.8, nivel - 1)

    for k in range(d.get("ramas", 4)):
        a = k * math.tau / d.get("ramas", 4) + rnd.uniform(-0.3, 0.3)
        p = Vector((math.cos(a) * sx * 0.12, math.sin(a) * sy * 0.12, sz * 0.15))
        rama(p, Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, 1)), sz * 0.55, S * 0.045, 1)
    piezas.append(Pieza(bm, d.get("grupo_coral", "neon"), d["pint"]["coral"], dict(bultos=0.008, poros=0.006,
                                                                                    esc_poros=30),
                        "decimar", tris=d.get("tris_coral", 1500), nombre="coral", voxel=S * 0.008, suave=True))
    return piezas


def f_alambres(d, rnd):
    """Plata nativa: roca con hilos de plata retorcidos que salen de ella (dendritas)."""
    piezas = [_base_roca(d, rnd)]
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    bm = bmesh.new()
    base_tmp = roca(d["tam"], d.get("cortes", 8), d.get("redondez", 0.5), random.Random(d["semilla"]), base=0.3)
    vs = [v for v in base_tmp.verts if v.co.z > sz * 0.35 and v.normal.z > 0.1]
    for i in range(d.get("hilos", 7)):
        v = rnd.choice(vs)
        p = Vector(v.co) - v.normal * 0.05 * S
        dd = (v.normal + Vector((0, 0, 0.6))).normalized()
        pts = [p]
        for k in range(7):
            dd = (dd + Vector((rnd.uniform(-0.7, 0.7), rnd.uniform(-0.7, 0.7), rnd.uniform(-0.2, 0.5)))).normalized()
            p = p + dd * S * rnd.uniform(0.05, 0.08)
            pts.append(p)
        r = S * rnd.uniform(0.018, 0.03)
        unir(bm, tubo(pts, [r * (1 - 0.6 * k / 8) for k in range(8)], 5, punta=True))
    base_tmp.free()
    piezas.append(Pieza(bm, "", d["pint"]["pepita"], dict(bultos=0.004), "decimar", tris=700, nombre="hilos",
                        voxel=S * 0.006, suave=True))
    return piezas


def f_ambar_fosil(d, rnd):
    """Gota de ámbar (cristal) con una amonites en espiral dentro (interior)."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    bolas = [((0, 0, sz * 0.42), sz * 0.42), ((sx * 0.18, 0, sz * 0.35), sz * 0.36), ((-sx * 0.2, sy * 0.05, sz * 0.3),
                                                                                   sz * 0.32)]
    amb = metabolas(bolas, resolucion=S / 22)
    cortar(amb, (0, 0, min(v.co.z for v in amb.verts) + sz * 0.08), (0, 0, -1))
    bajar_a_cero(amb)
    # Amonites: tubo en espiral logarítmica que engorda, en un plano casi vertical mirando al frente.
    pts, rad = [], []
    vueltas = 2.6
    for i in range(46):
        t = i / 45
        a = t * vueltas * math.tau
        rr = S * 0.02 * math.exp(0.9 * t * vueltas)
        pts.append(Vector((math.cos(a) * rr, 0.0, math.sin(a) * rr)))
        rad.append(rr * 0.38)
    esp = tubo(pts, rad, 6, punta=False)
    cmin, cmax = caja(amb)
    transformar(esp, Matrix.Translation(((cmin.x + cmax.x) / 2, (cmin.y + cmax.y) / 2, (cmin.z + cmax.z) / 2)) @
                Matrix.Rotation(math.radians(18), 4, "Z"))
    return [Pieza(amb, "cristal", d["pint"]["cristal"], None, "decimar", tris=900, nombre="ambar", suave=True,
                  voxel=S / 80),
            Pieza(esp, "interior", d["pint"]["fosil"], dict(bultos=0.004, surcos_esp=1), "decimar", tris=900,
                  nombre="amonites", voxel=S / 120, suave=True)]


def f_tormenta(d, rnd):
    """Cristal gris translúcido con rayos azules dentro."""
    piezas = f_cristales(d, rnd)
    crist = [p for p in piezas if p.grupo == "cristal"][0]
    islas = _islas(crist.bm)
    bm = bmesh.new()
    for isla in islas:
        cen = sum((v.co for v in isla), Vector()) / len(isla)
        zs = sorted(isla, key=lambda v: v.co.z)
        bajo, alto = zs[0].co, zs[-1].co
        a = cen.lerp(bajo, 0.55)
        b = cen.lerp(alto, 0.75)
        ancho = max((v.co - cen).length for v in isla)
        for k in range(d.get("rayos_por", 2)):
            unir(bm, rayo(a, b, rnd, 7, 0.22, radio=ancho * 0.07))
    piezas.append(Pieza(bm, "neon", d["pint"]["nucleo"], None, "limpia", nombre="rayos"))
    return piezas


def f_rayos_fuera(d, rnd):
    """Supernova congelada: roca con rayos de luz que estallan desde el centro y la atraviesan."""
    piezas = [_base_roca(d, rnd)]
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    bm = bmesh.new()
    cen = Vector((0, 0, sz * 0.5))
    for i in range(d.get("rayos", 16)):
        u = rnd.uniform(-0.2, 1.0)
        th = rnd.uniform(0, math.tau)
        dirv = Vector((math.sqrt(1 - u * u) * math.cos(th), math.sqrt(1 - u * u) * math.sin(th), u))
        largo = rnd.uniform(0.38, 0.6) * S
        unir(bm, gema(cen, dirv, largo, S * rnd.uniform(0.02, 0.04), 4, 0.7, rnd, irregular=0.1, enterrado=0))
    unir(bm, icosfera(S * 0.2, 2, cen))
    piezas.append(Pieza(bm, "neon", d["pint"]["nucleo"], None, "limpia", nombre="rayos", voxel=S / 150))
    return piezas


def f_estrella(d, rnd):
    """Diamante en forma de estrella de cinco puntas, de pie sobre una peana de roca."""
    sx, sy, sz = d["tam"]
    piezas = [_base_roca(d, rnd, (sx * 0.65, sy * 0.9, sz * 0.18))]
    R0 = (sz * 0.82) / 2
    est = estrella(5, R0, R0 * 0.47, R0 * 0.55, (0, 0, sz * 0.16 + R0 * 0.95), (0, 0, rnd.uniform(-8, 8)))
    piezas.append(Pieza(est, "cristal", d["pint"]["cristal"], None, "limpia", nombre="estrella", voxel=R0 / 40))
    for extra in d.get("extras_internos", ()):
        pass
    return piezas


def f_gota(d, rnd):
    """Lágrima del universo: gota de cristal con una galaxia espiral (disco Neon) dentro."""
    sx, sy, sz = d["tam"]

    def perfil(t):
        # De la base redonda a la punta afilada arriba.
        r = math.sin(math.pi * min(1.0, t * 1.0) ** 0.75) * (1 - t) ** 0.35
        return (sx / 2 * r * 1.05, sy / 2 * r * 1.05, 0, 0, 0)

    gota = loft(perfil, 18, 16, 0.0, sz)
    galaxia = disco(sx * 0.03, sx * 0.3, sx * 0.05, 32, (0, 0, sz * 0.33), (68, 0, 25), alabeo=sx * 0.02, rnd=rnd)
    nucleo = icosfera(sx * 0.07, 2, (0, 0, sz * 0.33), (1, 1, 0.6))
    unir(galaxia, nucleo)
    return [Pieza(gota, "cristal", d["pint"]["cristal"], None, "limpia", suave=True, nombre="gota", voxel=sx / 60),
            Pieza(galaxia, "neon", d["pint"]["nucleo"], None, "limpia", nombre="galaxia", voxel=sx / 200)]


def f_llama(d, rnd):
    """Gema fénix: cristal tallado en forma de llama que se retuerce, con lenguas de fuego, sobre una peana."""
    sx, sy, sz = d["tam"]
    piezas = [_base_roca(d, rnd, (sx * 0.8, sy * 0.8, sz * 0.14))]
    fase = rnd.uniform(0, 6)

    def perfil_k(escala, desfase, alto):
        def p(t):
            r = (math.sin(math.pi * min(1, t * 1.6)) ** 0.6 if t < 0.3 else (1 - t) ** 0.9 * 1.15) * escala
            cx = math.sin(t * 5 + fase + desfase) * sx * 0.08 * t
            return (sx / 2 * r, sy / 2 * r * 0.75, cx, 0, t * 2.4 + desfase)
        return p

    bm = loft(perfil_k(1.0, 0, 1), 16, 8, sz * 0.1, sz)
    for k, (dx, h, esc) in enumerate([(-0.25, 0.7, 0.45), (0.27, 0.62, 0.4), (0.05, 0.5, 0.35)]):
        lengua = loft(perfil_k(esc, k * 1.7, h), 10, 6, 0, sz * h)
        transformar(lengua, Matrix.Translation((dx * sx, rnd.uniform(-0.05, 0.05) * sy, sz * 0.1)) @
                    Matrix.Rotation(dx * 0.9, 4, "Y"))
        unir(bm, lengua)
    piezas.append(Pieza(bm, "cristal", d["pint"]["cristal"], None, "limpia", nombre="llama", voxel=sx / 70))
    nucleo = loft(perfil_k(0.45, 0.3, 1), 12, 6, sz * 0.14, sz * 0.8)
    piezas.append(Pieza(nucleo, "neon", d["pint"]["nucleo"], None, "limpia", nombre="nucleo", voxel=sx / 90))
    return piezas


def f_corazon(d, rnd):
    """Corazón cristalizado: corazón de metabolas translúcido con un corazón de luz dentro y arterias."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)

    def bolas(k):
        return [((-sx * 0.2 * k, 0, sz * 0.62 * k + sz * (1 - k) * 0.5), sx * 0.29 * k),
                ((sx * 0.2 * k, 0, sz * 0.6 * k + sz * (1 - k) * 0.5), sx * 0.3 * k),
                ((0, 0, sz * 0.42 * k + sz * (1 - k) * 0.5), sx * 0.3 * k),
                ((0, 0, sz * 0.2 * k + sz * (1 - k) * 0.5), sx * 0.17 * k),
                ((0, 0, sz * 0.06 * k + sz * (1 - k) * 0.5), sx * 0.06 * k)]

    cor = metabolas(bolas(1.0), resolucion=S / 30)
    transformar(cor, Matrix.Rotation(math.radians(-14), 4, "Y"))
    bajar_a_cero(cor)
    dentro = metabolas(bolas(0.72), resolucion=S / 30)
    transformar(dentro, Matrix.Rotation(math.radians(-14), 4, "Y"))
    zc = (caja(cor)[0].z + caja(cor)[1].z) / 2
    zd = (caja(dentro)[0].z + caja(dentro)[1].z) / 2
    bmesh.ops.translate(dentro, vec=(0, 0, zc - zd), verts=dentro.verts)
    art = bmesh.new()
    top = caja(cor)[1].z
    for k, (x, ang) in enumerate([(-0.12, -0.5), (0.05, 0.1), (0.2, 0.6)]):
        p0 = Vector((x * sx, 0, top - sz * 0.15))
        dd = Vector((math.sin(ang), 0.1 * k, math.cos(ang)))
        pts = [p0 + dd * sz * 0.12 * i + Vector((0, 0, -0.02 * i * i * sz)) for i in range(5)]
        unir(art, tubo(pts, [S * 0.06 * (1 - 0.15 * i) for i in range(5)], 8, punta=False))
    return [Pieza(cor, "cristal", d["pint"]["cristal"], None, "decimar", tris=1200, nombre="corazon", suave=True,
                  voxel=S / 90),
            Pieza(dentro, "neon", d["pint"]["nucleo"], None, "decimar", tris=500, nombre="latido", suave=True,
                  voxel=S / 60),
            Pieza(art, "", d["pint"]["roca"], dict(bultos=0.01, fino=0.004), "decimar", tris=500, nombre="arterias",
                  voxel=S / 110, suave=True)]


def f_singularidad(d, rnd):
    """Esfera negra perfecta, anillo de energía blanca (disco) y un anillo de fotones inclinado."""
    sx, sy, sz = d["tam"]
    r = sz * 0.3
    cen = (0, 0, sz * 0.5)
    esfera = icosfera(r, 3, cen)
    anillo = disco(r * 1.35, r * 2.6, r * 0.05, 64, cen, (8, 0, 0), alabeo=r * 0.03, rnd=rnd)
    fotones = toro(r * 1.12, r * 0.035, 48, 6, cen, (82, 0, 0))
    return [Pieza(esfera, "", d["pint"]["roca"], None, "limpia", suave=True, nombre="esfera", voxel=r / 40),
            Pieza(anillo, "neon", d["pint"]["nucleo"], None, "limpia", nombre="anillo", voxel=r / 60),
            Pieza(fotones, "neon", d["pint"]["nucleo"], None, "limpia", nombre="fotones", suave=True, voxel=r / 80)]


def f_agujero(d, rnd):
    """Fragmento de agujero negro: esquirla oscura con un disco de acreción naranja girando alrededor."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    cen = Vector((0, 0, sz * 0.5))
    frag = bmesh.new()
    unir(frag, gema(cen - Vector((0, 0, sz * 0.32)), Vector((0.1, 0, 1)), sz * 0.64, S * 0.13, 5, 0.4, rnd,
                    doble=True, irregular=0.25))
    for k in range(3):
        unir(frag, esquirla(cen + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * S * 0.08,
                            S * 0.09, rnd))
    disco_a = disco(S * 0.2, S * 0.48, S * 0.03, 64, cen, (14, 4, 0), alabeo=S * 0.015, rnd=rnd)
    halo = toro(S * 0.17, S * 0.018, 40, 6, cen, (80, 0, 10))
    unir(disco_a, halo)
    return [Pieza(frag, "", d["pint"]["roca"], None, "limpia", nombre="fragmento", voxel=S / 120),
            Pieza(disco_a, "neon", d["pint"]["nucleo"], None, "limpia", nombre="disco", voxel=S / 220)]


def f_nucleo_estelar(d, rnd):
    """Esfera perfecta de energía blanca con partículas en tres órbitas."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    r = sz * 0.26
    cen = (0, 0, sz * 0.5)
    esfera = icosfera(r, 3, cen)
    capa = icosfera(r * 1.18, 3, cen)
    piezas = [Pieza(esfera, "neon", d["pint"]["nucleo"], None, "limpia", suave=True, nombre="nucleo", voxel=r / 40),
              Pieza(capa, "cristal", d["pint"]["cristal"], None, "limpia", suave=True, nombre="halo", voxel=r / 40)]
    piezas += x_orbitas(d, rnd, piezas, dict(centro=cen, anillos=[
        dict(n=10, radio=0.4, incl=20, tam=(0.02, 0.035), forma="octa"),
        dict(n=12, radio=0.46, incl=-35, tam=(0.018, 0.03), forma="octa"),
        dict(n=8, radio=0.36, incl=75, tam=(0.02, 0.03), forma="octa")], pint="orbita", grupo="orbita"))
    return piezas


def f_semilla(d, rnd):
    """Semilla cristalina dorada (tallada) sobre una piedra, con raíces de luz que crecen desde ella."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    piezas = [_base_roca(d, rnd, (sx * 0.85, sy * 0.85, sz * 0.2))]
    pts = []
    for i in range(9):
        t = i / 8
        z = sz * (0.16 + 0.8 * t)
        r = math.sin(math.pi * t) ** 0.8 * sx * 0.22
        for k in range(8):
            a = k * math.tau / 8 + i * 0.4
            pts.append(Vector((math.cos(a) * r, math.sin(a) * r, z)))
    semilla = casco(pts)
    transformar(semilla, Matrix.Translation((0, 0, sz * 0.5)) @ Matrix.Rotation(0.18, 4, "Y") @
                Matrix.Translation((0, 0, -sz * 0.5)))
    raices = bmesh.new()
    for k in range(d.get("raices", 9)):
        a = k * math.tau / d.get("raices", 9) + rnd.uniform(-0.2, 0.2)
        p = Vector((0, 0, sz * 0.24))
        pts = [p]
        dd = Vector((math.cos(a), math.sin(a), -0.25)).normalized()
        for i in range(8):
            dd = (dd + Vector((rnd.uniform(-0.4, 0.4), rnd.uniform(-0.4, 0.4), -0.15))).normalized()
            p = p + dd * S * 0.07
            p.z = max(p.z, sz * 0.02)
            pts.append(Vector(p))
        unir(raices, tubo(pts, [S * 0.025 * (1 - i / 9) for i in range(9)], 5, punta=True))
    piezas.append(Pieza(semilla, "", d["pint"]["cristal"], None, "limpia", nombre="semilla", voxel=S / 120))
    piezas.append(Pieza(raices, "neon", d["pint"]["nucleo"], None, "decimar", tris=900, nombre="raices",
                        voxel=S / 220, suave=True))
    return piezas


def f_genesis(d, rnd):
    """Cristal blanco perfecto (bipirámide) con los cinco sólidos platónicos dentro, uno sobre otro."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    peana = _base_roca(d, rnd, (sx * 1.1, sy * 1.1, sz * 0.12))
    z0 = sz * 0.08
    alto = sz * 0.9
    crist = gema(Vector((0, 0, z0)), Vector((0, 0, 1)), alto, sx * 0.3, 6, 0.3, rnd, doble=True, irregular=0.0,
                 estrechar=1.0, punta_desc=0.0)
    dentro = bmesh.new()
    for i, tipo in enumerate(("tetra", "cubo", "octa", "dodeca", "icosa")):
        z = z0 + alto * (0.22 + 0.14 * i)
        r = sx * (0.1 if i in (0, 4) else 0.12)
        unir(dentro, platonico(tipo, (0, 0, z), r, (rnd.uniform(0, 60), rnd.uniform(0, 60), rnd.uniform(0, 60))))
    corona = bmesh.new()
    for k in range(7):
        a = k * math.tau / 7 + rnd.uniform(-0.2, 0.2)
        p = Vector((math.cos(a) * sx * 0.3, math.sin(a) * sy * 0.3, sz * 0.08))
        eje = Vector((math.cos(a) * 0.6, math.sin(a) * 0.6, 1))
        unir(corona, gema(p, eje, sz * rnd.uniform(0.14, 0.24), sx * 0.06, 6, 0.35, rnd, enterrado=0.6))
    return [peana,
            Pieza(crist, "cristal", d["pint"]["cristal"], None, "limpia", nombre="cristal", voxel=S / 100),
            Pieza(corona, "cristal", d["pint"]["cristal"], None, "limpia", nombre="corona", voxel=S / 160),
            Pieza(dentro, "neon", d["pint"]["nucleo"], None, "limpia", nombre="solidos", voxel=S / 200)]


def f_dios(d, rnd):
    """Fragmento de dios: todos los sólidos a la vez, girados y encajados unos en otros, con esquirlas en órbita."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    cen = (0, 0, sz * 0.5)
    nucleo = bmesh.new()
    for tipo, r, rot in (("icosa", 0.26, (0, 0, 0)), ("dodeca", 0.25, (31, 17, 0)), ("octa", 0.36, (0, 45, 20)),
                         ("tetra", 0.42, (10, 0, 35)), ("tetra", 0.42, (190, 0, 35)), ("cubo", 0.3, (45, 35, 0))):
        unir(nucleo, platonico(tipo, cen, sz * r, rot))
    cascara = platonico("icosa", cen, sz * 0.4, (13, 7, 0))
    # Tres anillos cruzados como un giroscopio (cada uno con su giro en el cliente).
    for rot, R0 in (((90, 0, 0), 0.47), ((90, 0, 60), 0.43), ((90, 0, 120), 0.39), ((0, 0, 0), 0.5)):
        unir(nucleo, toro(sz * R0, sz * 0.012, 40, 4, cen, rot))
    piezas = [Pieza(nucleo, "neon", d["pint"]["nucleo"], None, "limpia", nombre="nucleo", voxel=S / 300),
              Pieza(cascara, "cristal", d["pint"]["cristal"], None, "limpia", nombre="cascara", voxel=S / 100)]
    piezas += x_orbitas(d, rnd, piezas, dict(centro=cen, anillos=[
        dict(n=8, radio=0.62, incl=25, tam=(0.03, 0.05), forma="octa"),
        dict(n=8, radio=0.66, incl=-40, tam=(0.03, 0.05), forma="cubo"),
        dict(n=6, radio=0.58, incl=85, tam=(0.03, 0.05))], pint="orbita"))
    return piezas


def f_big_bang(d, rnd):
    """Cristal translúcido con una explosión de luz dentro (bola de púas multicolor)."""
    piezas = f_cristales(d, rnd)
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    crist = [p for p in piezas if p.grupo == "cristal"][0]
    cmin, cmax = caja(crist.bm)
    cen = Vector((0, 0, cmin.z + (cmax.z - cmin.z) * 0.42))
    bm = icosfera(S * 0.09, 1, cen)
    for i in range(22):
        u = rnd.uniform(-1, 1)
        th = rnd.uniform(0, math.tau)
        dirv = Vector((math.sqrt(1 - u * u) * math.cos(th), math.sqrt(1 - u * u) * math.sin(th), u))
        unir(bm, gema(cen, dirv, S * rnd.uniform(0.12, 0.22), S * 0.015, 3, 0.8, rnd, enterrado=0))
    piezas.append(Pieza(bm, "neon", d["pint"]["nucleo"], None, "limpia", nombre="explosion", voxel=S / 220))
    return piezas


def f_sol_negro(d, rnd):
    """Cristal oscuro (bipirámide) con una corona de púas de energía dorada flotando a su alrededor."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    piezas = [_base_roca(d, rnd, (sx * 0.6, sy * 0.6, sz * 0.16))]
    cen = Vector((0, 0, sz * 0.56))
    crist = gema(Vector((0, 0, sz * 0.1)), Vector((0, 0, 1)), sz * 0.9, sx * 0.17, 6, 0.33, rnd, doble=True,
                 irregular=0.05)
    corona = bmesh.new()
    n = 14
    for i in range(n):
        a = i * math.tau / n
        dirv = Vector((math.cos(a), 0, math.sin(a)))
        base = cen + dirv * S * 0.25
        largo = S * (0.17 if i % 2 == 0 else 0.11)
        unir(corona, gema(base, dirv, largo, S * 0.022, 4, 0.75, rnd, irregular=0.05, enterrado=0))
    unir(corona, toro(S * 0.25, S * 0.013, 48, 6, cen, (90, 0, 0)))
    piezas += [Pieza(crist, "cristal", d["pint"]["cristal"], None, "limpia", nombre="cristal", voxel=S / 110),
               Pieza(corona, "neon", d["pint"]["nucleo"], None, "limpia", nombre="corona", voxel=S / 220)]
    return piezas


def f_dimensional(d, rnd):
    """Cristal transparente con otro paisaje dentro: montañas, un lago y una luna pequeña."""
    piezas = f_cristales(d, rnd)
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    crist = [p for p in piezas if p.grupo == "cristal"][0]
    isla = max(_islas(crist.bm), key=len)
    cen = sum((v.co for v in isla), Vector()) / len(isla)
    ancho = min((v.co - cen).length for v in isla) * 0.6
    paisaje = bmesh.new()
    # Suelo: disco fino con montañas (conos).
    suelo = loft(lambda t: (ancho * (1 - t * 0.02), ancho * (1 - t * 0.02), 0, 0, 0), 1, 16, 0, ancho * 0.08)
    bmesh.ops.translate(suelo, vec=cen - Vector((0, 0, ancho * 0.6)), verts=suelo.verts)
    unir(paisaje, suelo)
    for k in range(5):
        a = rnd.uniform(0, math.tau)
        rr = rnd.uniform(0.1, 0.6) * ancho
        h = rnd.uniform(0.35, 0.8) * ancho
        m = gema(cen + Vector((math.cos(a) * rr, math.sin(a) * rr, -ancho * 0.55)), Vector((0, 0, 1)), h,
                 ancho * 0.28, 6, 0.85, rnd, irregular=0.3, enterrado=0)
        unir(paisaje, m)
    luna = icosfera(ancho * 0.12, 1, cen + Vector((ancho * 0.35, 0, ancho * 0.55)))
    return piezas + [Pieza(paisaje, "interior", d["pint"]["paisaje"], dict(bultos=0.01), "decimar", tris=500,
                           nombre="paisaje", voxel=S / 160),
                     Pieza(luna, "neon", d["pint"]["nucleo"], None, "limpia", nombre="luna", suave=True)]


def f_filosofal(d, rnd):
    """Piedra filosofal: gema roja perfecta tallada (dodecaedro alargado) con un halo dorado y chispas."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    piezas = [_base_roca(d, rnd, (sx * 0.55, sy * 0.55, sz * 0.12))]
    cen = Vector((0, 0, sz * 0.5))
    gem = platonico("dodeca", (0, 0, 0), sz * 0.27, (20, 0, 0))
    transformar(gem, Matrix.Translation(cen) @ Matrix.Diagonal((0.9, 0.9, 1.25, 1)))
    halo = toro(S * 0.36, S * 0.016, 56, 6, cen, (72, 0, 18))
    unir(halo, toro(S * 0.4, S * 0.01, 56, 6, cen, (100, 0, -24)))
    piezas += [Pieza(gem, "cristal", d["pint"]["cristal"], None, "limpia", nombre="gema", voxel=S / 110),
               Pieza(halo, "neon", d["pint"]["nucleo"], None, "limpia", nombre="halo", voxel=S / 300)]
    piezas += x_orbitas(d, rnd, piezas, dict(centro=tuple(cen), anillos=[
        dict(n=9, radio=0.33, incl=60, tam=(0.015, 0.025), forma="octa")], pint="orbita", grupo="orbita"))
    return piezas


def f_materia_oscura(d, rnd):
    """Roca negra con grietas violeta y una envoltura de cristal que deforma lo que hay detrás."""
    piezas = [_base_roca(d, rnd)]
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    piezas += x_nucleo(d, rnd, piezas, dict(escala=0.88))
    env = canto((sx * 1.25, sy * 1.25, sz * 1.25), rnd, 0.15, 0.0, sub=3)
    bmesh.ops.translate(env, vec=(0, 0, -sz * 0.12), verts=env.verts)
    piezas.append(Pieza(env, "cristal", d["pint"]["cristal"], None, "limpia", suave=True, nombre="distorsion",
                        voxel=S / 60))
    return piezas


def f_cero(d, rnd):
    """Cristal de hielo perfecto (hexagonal, doble punta) que flota sobre una corona de escarcha."""
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    piezas = [_base_roca(d, rnd, (sx * 0.7, sy * 0.7, sz * 0.12))]
    piezas.append(Pieza(gema(Vector((0, 0, sz * 0.12)), Vector((0, 0, 1)), sz * 0.86, sx * 0.2, 6, 0.28, rnd,
                             doble=True, irregular=0.0, estrechar=1.0, punta_desc=0.0),
                        "cristal", d["pint"]["cristal"], None, "limpia", nombre="hielo", voxel=S / 110))
    piezas += x_escarcha(d, rnd, piezas, dict(n=18, radio=0.3, pint="escarcha", grupo=""))
    piezas[-1].grupo = ""
    return piezas


def f_cabujon(d, rnd):
    """Ópalo / piedra pulida grande con forma de huevo, apoyada en una roca de matriz."""
    sx, sy, sz = d["tam"]
    piezas = [_base_roca(d, rnd, (sx, sy, sz * 0.3))]
    op = icosfera(1.0, 3)
    bmesh.ops.scale(op, vec=(sx * 0.36, sy * 0.3, sz * 0.42), verts=op.verts)
    transformar(op, Matrix.Translation((0, 0, sz * 0.55)) @ Matrix.Rotation(0.25, 4, "Y"))
    # Malla limpia y suave (una esfera simplificada se ve facetada con un material tan brillante).
    piezas.append(Pieza(op, d.get("grupo_cabujon", ""), d["pint"]["cristal"], None, "limpia", nombre="opalo",
                        suave=True))
    return piezas


def f_antimateria(d, rnd):
    """Cristales que parecen un negativo, rodeados de esquirlas Neon inestables (como si se deshicieran)."""
    piezas = f_cristales(d, rnd)
    sx, sy, sz = d["tam"]
    S = max(sx, sy, sz)
    crist = [p for p in piezas if p.grupo == "cristal"][0]
    bm = bmesh.new()
    for isla in _islas(crist.bm):
        top = max(isla, key=lambda v: v.co.z).co
        cen = sum((v.co for v in isla), Vector()) / len(isla)
        for k in range(4):
            p = cen.lerp(top, rnd.uniform(0.3, 1.1)) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1),
                                                                rnd.uniform(-0.3, 0.6))) * S * 0.07
            unir(bm, esquirla(p, S * rnd.uniform(0.018, 0.035), rnd, 2.2))
    piezas.append(Pieza(bm, "neon", d["pint"]["nucleo"], None, "limpia", nombre="inestable"))
    return piezas


FORMAS = dict(roca=f_roca, canto=f_canto, blob=f_blob, laminas=f_laminas, columnas=f_columnas, grupo=f_grupo,
              cristales=f_cristales, geoda=f_geoda, pepitas=f_pepitas, agata=f_agata, coral=f_coral,
              alambres=f_alambres, ambar_fosil=f_ambar_fosil, tormenta=f_tormenta, rayos_fuera=f_rayos_fuera,
              estrella=f_estrella, gota=f_gota, llama=f_llama, corazon=f_corazon, singularidad=f_singularidad,
              agujero=f_agujero, nucleo_estelar=f_nucleo_estelar, semilla=f_semilla, genesis=f_genesis,
              dios=f_dios, big_bang=f_big_bang, sol_negro=f_sol_negro, dimensional=f_dimensional,
              filosofal=f_filosofal, materia_oscura=f_materia_oscura, cero=f_cero, cabujon=f_cabujon,
              antimateria=f_antimateria)


def construir_piezas(d, rnd):
    piezas = FORMAS[d["forma"]](d, rnd)
    for nombre, cfg in d.get("extras", {}).items():
        clave = nombre.split("#")[0]
        piezas += EXTRAS[clave](d, rnd, piezas, cfg)
    return piezas
