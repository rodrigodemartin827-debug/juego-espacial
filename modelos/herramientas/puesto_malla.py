"""
Constructor de mallas de superficie dura del puesto de seguridad.

Es el mismo constructor que usan las casas del pueblo (casa_malla.py en la rama de las casas), copiado aquí para que
el puesto se pueda generar solo, más tres utilidades: `Plano` (cara de un muro), `caja_plano` y `texto` (letras 3D).

Todo se escribe en STUDS: 1 unidad de Blender = 1 stud (la escena usa scale_length = 0,28 para que en metros
también cuadre con Roblox).

`Constructor` acumula geometría en un bmesh:
  * cada cara lleva un material (por nombre), una marca de «suave» (cilindros, tubos, telas) y una marca de
    «oculta» (caras que casi no se ven: debajo, contra la pared...). La marca de oculta sirve para darles menos
    sitio en el atlas de texturas.
  * las cajas pueden omitir caras que nunca se ven (la de atrás de un panel pegado a la pared, la de abajo de una
    losa apoyada en el suelo): así no se gastan triángulos en nada.

`Pieza` junta dos constructores:
  * `baja`: la malla del juego (la que se exporta y cuenta para el presupuesto de triángulos).
  * `alta`: detalles que solo existen para hornear el mapa de normales y el color (remaches, cordones de soldadura,
    letras en relieve...). La malla alta final es baja + alta.
"""

import math

import bpy  # noqa: F401  (antes que bmesh)
import bmesh
from mathutils import Matrix, Vector

# Direcciones de las caras de una caja, para omitirlas por nombre.
_DIRS = {"-x": Vector((-1, 0, 0)), "+x": Vector((1, 0, 0)), "-y": Vector((0, -1, 0)),
         "+y": Vector((0, 1, 0)), "-z": Vector((0, 0, -1)), "+z": Vector((0, 0, 1))}


def rot(eje, grados):
    return Matrix.Rotation(math.radians(grados), 3, eje)


def base_de(normal):
    """Dos ejes perpendiculares a `normal` (u horizontal si se puede, v hacia arriba)."""
    n = Vector(normal).normalized()
    arriba = Vector((0, 0, 1)) if abs(n.z) < 0.95 else Vector((0, 1, 0))
    u = arriba.cross(n).normalized()
    v = n.cross(u).normalized()
    return u, v


class Constructor:
    def __init__(self, mats):
        self.bm = bmesh.new()
        self.mats = mats  # lista compartida de nombres de material (índice = posición)
        self.c_suave = self.bm.faces.layers.int.new("suave")
        self.c_oculta = self.bm.faces.layers.int.new("oculta")
        self.c_solo_baja = self.bm.faces.layers.int.new("solo_baja")
        self.solo_baja = False  # mientras sea True, lo que se crea no pasa a la malla alta

    # ---- básicos -----------------------------------------------------------------------------------------

    def indice(self, nombre):
        if nombre not in self.mats:
            self.mats.append(nombre)
        return self.mats.index(nombre)

    def cara(self, verts, mat, suave=False, oculta=False):
        f = self.bm.faces.new(verts)
        f.material_index = self.indice(mat)
        f[self.c_suave] = int(suave)
        f[self.c_oculta] = int(oculta)
        f[self.c_solo_baja] = int(self.solo_baja)
        return f

    def v(self, p):
        return self.bm.verts.new(Vector(p))

    # ---- cajas -------------------------------------------------------------------------------------------

    def caja(self, centro, tam, mat, giro=None, sin=(), ocultas=(), mats=None):
        """
        Caja de tamaño `tam` centrada en `centro`, girada con la matriz 3x3 `giro`.
        `sin`: caras que no se crean ('-x', '+z'...). `ocultas`: caras que se crean pero casi no se ven.
        `mats`: material por cara, p. ej. {'+y': 'junta'}.
        """
        c = Vector(centro)
        h = Vector(tam) / 2
        g = giro if giro is not None else Matrix.Identity(3)
        esq = {}
        for sx in (-1, 1):
            for sy in (-1, 1):
                for sz in (-1, 1):
                    esq[(sx, sy, sz)] = self.v(c + g @ Vector((sx * h.x, sy * h.y, sz * h.z)))
        caras = {
            "-x": [(-1, -1, -1), (-1, -1, 1), (-1, 1, 1), (-1, 1, -1)],
            "+x": [(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)],
            "-y": [(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)],
            "+y": [(-1, 1, -1), (-1, 1, 1), (1, 1, 1), (1, 1, -1)],
            "-z": [(-1, -1, -1), (-1, 1, -1), (1, 1, -1), (1, -1, -1)],
            "+z": [(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)],
        }
        hechas = []
        for nombre, idx in caras.items():
            if nombre in sin:
                continue
            m = (mats or {}).get(nombre, mat)
            hechas.append(self.cara([esq[i] for i in idx], m, oculta=nombre in ocultas))
        usados = {v for f in hechas for v in f.verts}
        for vv in esq.values():
            if vv not in usados:
                self.bm.verts.remove(vv)
        return hechas

    def caja_de(self, mn, mx, mat, **kw):
        mn, mx = Vector(mn), Vector(mx)
        return self.caja((mn + mx) / 2, mx - mn, mat, **kw)

    # ---- polígonos extruidos -----------------------------------------------------------------------------

    def placa(self, puntos_uv, origen, u, v, n, grosor, mat, mat_canto=None, atras=False, suave_canto=False,
              oculta_atras=True, mat_frente=None):
        """
        Polígono (en coordenadas u, v del plano) extruido `grosor` en la dirección `n`.
        La cara de delante queda en origen + n*grosor; la de atrás (opcional) en el origen.
        Vale para cóncavos (el «7», el contorno de una hoja): se triangulan al final.
        """
        o, u, v, n = Vector(origen), Vector(u), Vector(v), Vector(n)
        atrasv = [self.v(o + u * a + v * b) for a, b in puntos_uv]
        delante = [self.v(o + u * a + v * b + n * grosor) for a, b in puntos_uv]
        # Orientación: la cara delantera tiene que mirar a +n.
        area = sum(puntos_uv[i][0] * puntos_uv[(i + 1) % len(puntos_uv)][1]
                   - puntos_uv[(i + 1) % len(puntos_uv)][0] * puntos_uv[i][1] for i in range(len(puntos_uv)))
        if u.cross(v).dot(n) < 0:
            area = -area
        if area < 0:
            atrasv.reverse()
            delante.reverse()
        k = len(puntos_uv)
        caras = [self.cara(delante, mat_frente or mat)]
        for i in range(k):
            j = (i + 1) % k
            caras.append(self.cara([atrasv[i], atrasv[j], delante[j], delante[i]], mat_canto or mat,
                                   suave=suave_canto))
        if atras:
            caras.append(self.cara(list(reversed(atrasv)), mat, oculta=oculta_atras))
        return caras

    def anillo_placa(self, exterior_uv, interior_uv, origen, u, v, n, grosor, mat, fondo=None, mat_fondo=None,
                     mat_hueco=None):
        """
        Placa con un agujero: `exterior_uv` e `interior_uv` tienen el mismo número de puntos y se unen con quads.
        Las paredes del agujero bajan hasta `fondo` (profundidad, por defecto todo el grosor) y, si hay fondo,
        se cierra con una cara (el hueco de una cerradura, la ventanilla del medidor).
        """
        o, u, v, n = Vector(origen), Vector(u), Vector(v), Vector(n)
        k = len(exterior_uv)
        ext_d = [self.v(o + u * a + v * b + n * grosor) for a, b in exterior_uv]
        int_d = [self.v(o + u * a + v * b + n * grosor) for a, b in interior_uv]
        ext_a = [self.v(o + u * a + v * b) for a, b in exterior_uv]
        prof = grosor if fondo is None else fondo
        int_f = [self.v(o + u * a + v * b + n * (grosor - prof)) for a, b in interior_uv]
        # Sentido: si el polígono es horario en (u, v) con n = u x v, se invierte el orden de los quads.
        area = sum(exterior_uv[i][0] * exterior_uv[(i + 1) % k][1] - exterior_uv[(i + 1) % k][0] * exterior_uv[i][1]
                   for i in range(k))
        if u.cross(v).dot(n) < 0:
            area = -area
        s = 1 if area > 0 else -1
        for i in range(k):
            j = (i + 1) % k
            a, b = (i, j) if s > 0 else (j, i)
            self.cara([ext_d[a], ext_d[b], int_d[b], int_d[a]], mat)          # frente
            self.cara([ext_a[a], ext_a[b], ext_d[b], ext_d[a]], mat)          # canto exterior
            self.cara([int_d[a], int_d[b], int_f[b], int_f[a]], mat_hueco or mat)  # pared del hueco
        if fondo is not None and fondo < grosor:
            self.cara(int_f if s > 0 else list(reversed(int_f)), mat_fondo or mat)

    # ---- revolución, lofts y tubos -----------------------------------------------------------------------

    def loft(self, anillos, mat, cerrado=True, tapa_ini=True, tapa_fin=True, suave=True, oculta_ini=False,
             oculta_fin=False, mats_tramo=None, mat_ini=None, mat_fin=None):
        """
        Une anillos de puntos (todos con el mismo número). `mats_tramo[k]`: material del tramo k.
        Un anillo de un solo punto es una punta (cono): se une en abanico.
        """
        vs = []
        for a in anillos:
            if len(a) == 1:
                vs.append([self.v(a[0])])
            else:
                vs.append([self.v(p) for p in a])
        n = max(len(a) for a in vs)
        tramos = n if cerrado else n - 1
        caras = []
        for k in range(len(vs) - 1):
            m = mats_tramo[k] if mats_tramo else mat
            A, B = vs[k], vs[k + 1]
            for i in range(tramos):
                j = (i + 1) % n
                if len(A) == 1:
                    caras.append(self.cara((A[0], B[j], B[i]), m, suave=suave))
                elif len(B) == 1:
                    caras.append(self.cara((A[i], A[j], B[0]), m, suave=suave))
                else:
                    caras.append(self.cara((A[i], A[j], B[j], B[i]), m, suave=suave))
        if cerrado and tapa_ini and len(vs[0]) > 2:
            caras.append(self.cara(list(reversed(vs[0])), mat_ini or mat, oculta=oculta_ini))
        if cerrado and tapa_fin and len(vs[-1]) > 2:
            caras.append(self.cara(vs[-1], mat_fin or mat, oculta=oculta_fin))
        self.ultimas = caras
        return vs

    def revolucion(self, perfil_rz, centro, lados, mat, eje=(0, 0, 1), tapa_ini=True, tapa_fin=True, giro=0.0,
                   mats_tramo=None, suave=True, oculta_ini=False, mat_ini=None, mat_fin=None, escala=(1, 1)):
        """
        Sólido de revolución: perfil [(radio, altura)] girado alrededor de `eje` desde `centro`.
        Un radio 0 al principio o al final hace punta. `escala`: (x, y) para secciones elípticas.
        """
        c = Vector(centro)
        q = Vector(eje).normalized().to_track_quat("Z", "Y").to_matrix()
        anillos = []
        for r, z in perfil_rz:
            if r <= 1e-6:
                anillos.append([c + q @ Vector((0, 0, z))])
                continue
            anillo = []
            for i in range(lados):
                a = giro + math.tau * i / lados
                anillo.append(c + q @ Vector((math.cos(a) * r * escala[0], math.sin(a) * r * escala[1], z)))
            anillos.append(anillo)
        return self.loft(anillos, mat, tapa_ini=tapa_ini, tapa_fin=tapa_fin, mats_tramo=mats_tramo, suave=suave,
                         oculta_ini=oculta_ini, mat_ini=mat_ini, mat_fin=mat_fin)

    def cilindro(self, base, eje, radio, largo, mat, lados=8, radio2=None, tapa_ini=True, tapa_fin=True, giro=None,
                 oculta_ini=False):
        r2 = radio if radio2 is None else radio2
        g = (math.pi / lados) if giro is None else giro
        return self.revolucion([(radio, 0), (r2, largo)], base, lados, mat, eje=eje, tapa_ini=tapa_ini,
                               tapa_fin=tapa_fin, giro=g, oculta_ini=oculta_ini)

    def tornillo(self, centro, normal, radio, mat, alto=None, lados=6):
        """Cabeza de tornillo baja (prisma con chaflán arriba). Para la malla alta, mejor `cupula`."""
        alto = radio * 0.45 if alto is None else alto
        return self.revolucion([(radio, 0), (radio, alto * 0.55), (radio * 0.72, alto)], centro, lados, mat,
                               eje=normal, tapa_ini=False, giro=math.pi / lados)

    def cupula(self, centro, normal, radio, mat, alto=None, lados=10):
        """Cabeza redonda (remache, tornillo de carrocería): media esfera aplastada."""
        alto = radio * 0.55 if alto is None else alto
        perfil = [(radio, 0)] + [(radio * math.cos(a), alto * math.sin(a))
                                 for a in (math.radians(35), math.radians(65))] + [(0, alto)]
        return self.revolucion(perfil, centro, lados, mat, eje=normal, tapa_ini=False)

    def tubo(self, camino, radio, mat, lados=8, radio_curva=0.0, pasos_curva=4, tapa_ini=True, tapa_fin=True,
             radios=None, suave=True):
        """
        Tubo a lo largo de una polilínea. Con `radio_curva` las esquinas se redondean (codos de verdad).
        `radios`: radio en cada punto del camino (para tubos que se estrechan); se interpola en las curvas.
        """
        pts = [Vector(p) for p in camino]
        rs = radios or [radio] * len(pts)
        if radio_curva > 0 and len(pts) > 2:
            nuevos, nrs = [pts[0]], [rs[0]]
            for i in range(1, len(pts) - 1):
                a, b, cc = pts[i - 1], pts[i], pts[i + 1]
                d1, d2 = (b - a).normalized(), (cc - b).normalized()
                ang = d1.angle(d2) if d1.dot(d2) < 0.9999 else 0.0
                if ang < 1e-3:
                    nuevos.append(b)
                    nrs.append(rs[i])
                    continue
                t = min(radio_curva * math.tan(ang / 2), (b - a).length * 0.45, (cc - b).length * 0.45)
                p0, p1 = b - d1 * t, b + d2 * t
                for k in range(pasos_curva + 1):
                    f = k / pasos_curva
                    # Bézier cuadrática p0-b-p1: aproxima bien el arco.
                    q = (1 - f) ** 2 * p0 + 2 * (1 - f) * f * b + f * f * p1
                    nuevos.append(q)
                    nrs.append(rs[i])
            nuevos.append(pts[-1])
            nrs.append(rs[-1])
            pts, rs = nuevos, nrs
        # Marcos con transporte paralelo (los anillos no se retuercen).
        tang = []
        for i in range(len(pts)):
            if i == 0:
                t = pts[1] - pts[0]
            elif i == len(pts) - 1:
                t = pts[-1] - pts[-2]
            else:
                t = (pts[i + 1] - pts[i]).normalized() + (pts[i] - pts[i - 1]).normalized()
            tang.append(t.normalized())
        u, _ = base_de(tang[0])
        anillos = []
        for i, p in enumerate(pts):
            if i > 0:
                u = u - tang[i] * u.dot(tang[i])
                u.normalize()
            w = tang[i].cross(u)
            # En los codos el anillo se ensancha para que el tubo mantenga el grosor.
            esc = 1.0
            if 0 < i < len(pts) - 1:
                cosm = max(0.5, (pts[i + 1] - pts[i]).normalized().dot(tang[i]))
                esc = 1 / cosm
            anillo = []
            for k in range(lados):
                a = math.tau * k / lados + math.pi / lados
                anillo.append(p + (u * math.cos(a) + w * math.sin(a)) * rs[i] * esc)
            anillos.append(anillo)
        return self.loft(anillos, mat, tapa_ini=tapa_ini, tapa_fin=tapa_fin, suave=suave)

    # ---- utilidades ----------------------------------------------------------------------------------------

    def poligono(self, puntos, mat, normal, oculta=False):
        """Una cara plana suelta (convexa o no) orientada hacia `normal`."""
        f = self.cara([self.v(p) for p in puntos], mat, oculta=oculta)
        f.normal_update()
        if f.normal.dot(Vector(normal)) < 0:
            f.normal_flip()
        return f

    def recalcular(self, caras):
        """Normales hacia fuera en un trozo cerrado del que no está clara la orientación."""
        bmesh.ops.recalc_face_normals(self.bm, faces=list(caras))

    def cara_con_huecos(self, contorno, huecos, mat, normal, oculta=False):
        """Cara plana con agujeros (muros con ventanas): contorno y huecos son listas de puntos 3D."""
        aristas = []
        for lazo in [contorno] + list(huecos):
            vs = [self.v(p) for p in lazo]
            for i in range(len(vs)):
                aristas.append(self.bm.edges.new((vs[i], vs[(i + 1) % len(vs)])))
        res = bmesh.ops.triangle_fill(self.bm, use_beauty=True, use_dissolve=False, edges=aristas,
                                      normal=Vector(normal))
        caras = [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]
        for f in caras:
            f.normal_update()
            if f.normal.dot(Vector(normal)) < 0:
                f.normal_flip()
            f.material_index = self.indice(mat)
            f[self.c_oculta] = int(oculta)
            f[self.c_solo_baja] = int(self.solo_baja)
        return caras

    def transformar(self, verts, matriz):
        bmesh.ops.transform(self.bm, matrix=matriz, verts=list(verts))

    def verts_de(self, caras):
        return list({v for f in caras for v in f.verts})


class Pieza:
    """Una pieza del modelo: malla baja (juego) + detalles de la malla alta (solo para hornear)."""

    def __init__(self, nombre, pivote=None, peso_uv=1.0, alta_propia=False):
        self.nombre = nombre
        self.mats = []
        self.baja = Constructor(self.mats)
        self.alta = Constructor(self.mats)
        self.pivote = Vector(pivote) if pivote is not None else None  # None: centro de la caja límite
        self.peso_uv = peso_uv  # cuánto sitio del atlas le toca respecto a su superficie
        self.alta_propia = alta_propia  # True: la malla alta NO incluye la baja (p. ej. piedras con relieve)
        self.extra = {}  # datos para el JSON (anclajes...)
        # Cómo se ve en Roblox: "atlas" (SurfaceAppearance con el atlas), "neon" (Material Neon cian) o un cristal
        # ("vidrio" o "vidrio_naranja", Material Glass). Lo que no es atlas no se hornea ni ocupa sitio en el atlas.
        self.tipo = "atlas"



# ======================================================================================================
# Utilidades de muro y texto
# ======================================================================================================


class Plano:
    """Plano de un muro: u horizontal, v = arriba, n hacia fuera; d = distancia hacia fuera desde el plano."""

    def __init__(self, origen, n):
        self.o = Vector(origen)
        self.n = Vector(n).normalized()
        self.u, self.v = base_de(self.n)
        self.giro = Matrix((self.u, -self.n, self.v)).transposed()  # caja local: x=u, y=hacia dentro, z=v

    def p(self, u, v, d=0.0):
        return self.o + self.u * u + self.v * v + self.n * d


def caja_plano(c, pl, u0, u1, v0, v1, d0, d1, mat, sin=(), ocultas=(), mats=None):
    """Caja alineada con un muro. Caras: '-y' = la de fuera, '+y' = la de dentro (contra el muro)."""
    centro = pl.p((u0 + u1) / 2, (v0 + v1) / 2, (d0 + d1) / 2)
    return c.caja(centro, (u1 - u0, d1 - d0, v1 - v0), mat, giro=pl.giro, sin=sin, ocultas=ocultas, mats=mats)


def tornillo(p, centro, normal, radio, mat, lados_baja=6, en_baja=True, alto=None):
    """Tornillo: prisma hexagonal en la malla baja (si `en_baja`) y cabeza redonda en la alta."""
    alto = radio * 0.45 if alto is None else alto
    if en_baja:
        p.baja.solo_baja = True
        p.baja.revolucion([(radio, 0), (radio, alto * 0.7), (radio * 0.8, alto)], centro, lados_baja, mat,
                          eje=normal, tapa_ini=False, giro=math.pi / lados_baja, suave=False)
        p.baja.solo_baja = False
    p.alta.cupula(centro, normal, radio, mat, alto=radio * 0.5, lados=12)


def perno_hex(p, centro, normal, radio, mat, alto=None, arandela=False, en_baja=None):
    """
    Perno de anclaje: cabeza hexagonal de verdad (y arandela si se pide). Los pequeños (radio < 0,035) solo van en
    la malla alta: a esa escala se leen en el mapa de normales y no gastan triángulos.
    """
    n = Vector(normal).normalized()
    alto = radio * 0.7 if alto is None else alto
    c = Vector(centro)
    if en_baja is None:
        en_baja = radio >= 0.035
    destino = p.baja if en_baja else p.alta
    if arandela:
        destino.revolucion([(radio * 1.45, 0), (radio * 1.45, radio * 0.18)], c, 8, mat, eje=n, tapa_ini=False,
                           suave=False)
        c = c + n * radio * 0.18
    destino.revolucion([(radio, 0), (radio, alto)], c, 6, mat, eje=n, tapa_ini=False, giro=math.pi / 6, suave=False)
    if not en_baja:
        return
    # Chaflán y punta de la varilla roscada (solo en la alta).
    p.alta.cilindro(c + n * alto, n, radio * 0.45, radio * 0.35, mat, lados=10)


_FUENTES = {}


def fuente(ruta="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    if ruta not in _FUENTES:
        try:
            _FUENTES[ruta] = bpy.data.fonts.load(ruta, check_existing=True)
        except RuntimeError:
            _FUENTES[ruta] = None
    return _FUENTES[ruta]


def texto(c, cadena, origen, u, v, n, alto, grosor, mat, ancho_max=None, resolucion=1, alinear="CENTER",
          ruta_fuente="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
    """
    Letras de verdad: curva de texto de Blender convertida a malla, sin la tapa de atrás (va pegada a algo).
    `alto` es la altura de las mayúsculas en studs; el relieve sale en la dirección `n`.
    """
    cu = bpy.data.curves.new("texto_tmp", "FONT")
    f = fuente(ruta_fuente)
    if f is not None:
        cu.font = f
    cu.body = cadena
    cu.size = 1.0
    cu.align_x = alinear
    cu.align_y = "CENTER"
    cu.resolution_u = resolucion
    cu.extrude = 0.5
    ob = bpy.data.objects.new("texto_tmp", cu)
    bpy.context.scene.collection.objects.link(ob)
    dg = bpy.context.evaluated_depsgraph_get()
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    xs = [vv.co.x for vv in me.vertices]
    ys = [vv.co.y for vv in me.vertices]
    alto_mayus = max(ys) - min(ys) if ys else 1.0
    esc = alto / max(alto_mayus, 1e-6)
    ancho = (max(xs) - min(xs)) * esc
    esc_x = esc * ancho_max / ancho if ancho_max and ancho > ancho_max else esc
    cy = (max(ys) + min(ys)) / 2
    cx = (max(xs) + min(xs)) / 2 if alinear == "CENTER" else 0.0
    o, u, v, n = Vector(origen), Vector(u), Vector(v), Vector(n)
    verts = [c.v(o + u * ((vv.co.x - cx) * esc_x) + v * ((vv.co.y - cy) * esc) + n * ((vv.co.z + 0.5) * grosor))
             for vv in me.vertices]
    caras = []
    for pl in me.polygons:
        if all(me.vertices[i].co.z < -0.49 for i in pl.vertices):
            continue  # la tapa de atrás no se ve
        caras.append(c.cara([verts[i] for i in pl.vertices], mat))
    for vv in verts:
        if not vv.link_faces:
            c.bm.verts.remove(vv)
    ev.to_mesh_clear()
    bpy.data.objects.remove(ob)
    bpy.data.curves.remove(cu)
    return caras
