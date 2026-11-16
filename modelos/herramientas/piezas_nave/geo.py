"""
Constructor de mallas de superficie dura para las piezas de nave (en studs, sistema de Blender).

Ejes de Blender en todo este paquete: la pieza mira a -Y (delante), arriba es +Z y su IZQUIERDA es +X
(la derecha de una nave que mira a -Y queda en -X). Al escribir el JSON se pasa a Roblox con `a_roblox`.

`Constructor` acumula caras en un único bmesh. Cada cara lleva:
  * una ranura de material (primario, secundario, oscuro, ..., neon, cristal, domo, llama), y
  * un grupo: la malla final a la que pertenece ("cuerpo" por defecto; p. ej. "cabeza" de una torreta, que gira).
Las formas devuelven la lista de caras nuevas, para poder moverlas, girarlas o reflejarlas.
"""

import math
from contextlib import contextmanager

import bpy  # noqa: F401  (antes que bmesh)
import bmesh
from mathutils import Matrix, Quaternion, Vector

from . import datos

V = Vector
SIN_ATLAS = ("neon", "neon2", "cristal", "domo", "llama")


def a_roblox(v):
    """Punto o vector de Blender (delante -Y, arriba +Z, izquierda +X) a Roblox (delante -Z, arriba +Y, derecha +X)."""
    return (-v[0], v[2], v[1])


def seccion(y, ancho, alto, zc=0.0, n=16, cuad=2.0, xc=0.0, giro=0.0, achate_inf=1.0):
    """Anillo superelíptico en el plano XZ a la altura `y`. `achate_inf` < 1 aplasta la mitad de abajo (panza)."""
    pts = []
    for i in range(n):
        a = giro + math.tau * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = math.copysign(abs(ca) ** (2 / cuad), ca) * ancho / 2
        z = math.copysign(abs(sa) ** (2 / cuad), sa) * alto / 2
        if z < 0:
            z *= achate_inf
        pts.append(V((xc + x, y, zc + z)))
    return pts


def seccion_poligono(y, puntos_xz):
    return [V((x, y, z)) for x, z in puntos_xz]


def base_ortonormal(eje):
    """Dos vectores perpendiculares a `eje` (y entre sí)."""
    eje = V(eje).normalized()
    ref = V((0, 0, 1)) if abs(eje.z) < 0.9 else V((0, 1, 0))
    u = eje.cross(ref).normalized()
    w = eje.cross(u).normalized()
    return u, w


class Constructor:
    def __init__(self, nombre, tier):
        self.nombre = nombre
        self.tier = tier
        self.estilo = datos.ESTILOS[tier]
        self.bm = bmesh.new()
        self.capa_grupo = self.bm.faces.layers.int.new("grupo")
        self.ranuras = []
        self.grupos = ["cuerpo"]
        self._grupo = 0
        self.acoples = []  # dicts con posición/normal/arriba en Blender
        self.sin_bisel = set()  # caras que no se biselan (tiras finas, neón)
        self.info = {}  # datos extra para el JSON (pivotes, posiciones...)
        self.colores_extra = {}  # ranura -> hex, para cambiar el color de neón de una pieza concreta

    # ---- ranuras y grupos ------------------------------------------------------------------------------------

    def r(self, ranura):
        if ranura not in self.ranuras:
            self.ranuras.append(ranura)
        return self.ranuras.index(ranura)

    @contextmanager
    def grupo(self, nombre):
        if nombre not in self.grupos:
            self.grupos.append(nombre)
        antes = self._grupo
        self._grupo = self.grupos.index(nombre)
        try:
            yield
        finally:
            self._grupo = antes

    def _caras(self, caras, ranura, bisel=True):
        i = self.r(ranura)
        for f in caras:
            f.material_index = i
            f[self.capa_grupo] = self._grupo
            if not bisel or ranura in SIN_ATLAS:
                self.sin_bisel.add(f)
        return list(caras)

    # ---- formas -------------------------------------------------------------------------------------------

    def loft(self, anillos, ranura, tapa_ini=True, tapa_fin=True, cerrado=True, bisel=True):
        bm = self.bm
        vs = [[bm.verts.new(p) for p in a] for a in anillos]
        n = len(anillos[0])
        tramos = n if cerrado else n - 1
        caras = []
        for k in range(len(vs) - 1):
            for i in range(tramos):
                j = (i + 1) % n
                caras.append(bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i])))
        if tapa_ini and cerrado:
            caras.append(bm.faces.new(list(reversed(vs[0]))))
        if tapa_fin and cerrado:
            caras.append(bm.faces.new(vs[-1]))
        return self._caras(caras, ranura, bisel)

    def caja(self, centro, tam, ranura, giro=None, bisel=True):
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        m = Matrix.Diagonal((*tam, 1.0))
        if giro is not None:
            m = giro.to_4x4() @ m
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(V(centro)) @ m, verts=r["verts"])
        caras = list({f for v in r["verts"] for f in v.link_faces})
        return self._caras(caras, ranura, bisel)

    def caja_de(self, mn, mx, ranura, bisel=True):
        mn, mx = V(mn), V(mx)
        return self.caja((mn + mx) / 2, mx - mn, ranura, bisel=bisel)

    def cuña(self, puntos_xz, y0, y1, ranura, bisel=True):
        """Prisma: polígono del plano XZ extruido entre y0 e y1."""
        return self.loft([seccion_poligono(y0, puntos_xz), seccion_poligono(y1, puntos_xz)], ranura, bisel=bisel)

    def prisma(self, puntos_uv, origen, eje_u, eje_v, eje_w, grosor, ranura, bisel=True, centrado=True):
        """Polígono en el plano (u, v) que pasa por `origen`, extruido `grosor` a lo largo de w."""
        o, u, v, w = V(origen), V(eje_u), V(eje_v), V(eje_w)
        d0 = -grosor / 2 if centrado else 0.0
        a = [o + u * p[0] + v * p[1] + w * d0 for p in puntos_uv]
        b = [o + u * p[0] + v * p[1] + w * (d0 + grosor) for p in puntos_uv]
        return self.loft([a, b], ranura, bisel=bisel)

    def revolucion(self, origen, eje, perfil, ranura, lados=16, giro=0.0, bisel=True, escala_u=1.0, u_ref=None):
        """
        Superficie de revolución. `perfil` = [(t, r)]: distancia a lo largo de `eje` y radio. Un radio 0 cierra con
        un vértice (punta). Para algo hueco (toberas) el perfil vuelve hacia dentro por el interior.
        """
        o = V(origen)
        e = V(eje).normalized()
        u, w = base_ortonormal(e)
        if u_ref is not None:
            u = (V(u_ref) - e * V(u_ref).dot(e)).normalized()
            w = e.cross(u)
        bm = self.bm
        filas = []
        for t, rr in perfil:
            if rr <= 1e-5:
                filas.append([bm.verts.new(o + e * t)])
            else:
                fila = []
                for i in range(lados):
                    a = giro + math.tau * i / lados
                    fila.append(bm.verts.new(o + e * t + (u * math.cos(a) * escala_u + w * math.sin(a)) * rr))
                filas.append(fila)
        caras = []
        for k in range(len(filas) - 1):
            A, B = filas[k], filas[k + 1]
            if len(A) == 1 and len(B) == 1:
                continue
            for i in range(lados):
                j = (i + 1) % lados
                if len(A) == 1:
                    caras.append(bm.faces.new((A[0], B[j], B[i])))
                elif len(B) == 1:
                    caras.append(bm.faces.new((A[i], A[j], B[0])))
                else:
                    caras.append(bm.faces.new((A[i], A[j], B[j], B[i])))
        return self._caras(caras, ranura, bisel)

    def cilindro(self, base, eje, radio, largo, ranura, lados=12, radio2=None, tapas=True, bisel=True, giro=0.0):
        r2 = radio if radio2 is None else radio2
        perfil = [(0, radio), (largo, r2)]
        if tapas:
            perfil = [(0, 0)] + perfil + [(largo, 0)]
        return self.revolucion(base, eje, perfil, ranura, lados, giro=giro, bisel=bisel)

    def tubo(self, base, eje, r_ext, r_int, largo, ranura, lados=12, bisel=True):
        """Cilindro hueco (cañones, toberas rectas)."""
        perfil = [(0, r_int), (0, r_ext), (largo, r_ext), (largo, r_int), (0.0001, r_int)]
        return self.revolucion(base, eje, perfil, ranura, lados, bisel=bisel)

    def toro(self, centro, eje, R, r, ranura, n1=24, n2=8, bisel=False, escala=(1, 1)):
        c = V(centro)
        e = V(eje).normalized()
        u, w = base_ortonormal(e)
        bm = self.bm
        filas = []
        for i in range(n1):
            a = math.tau * i / n1
            radial = u * math.cos(a) * escala[0] + w * math.sin(a) * escala[1]
            rd = radial.normalized()
            fila = []
            for j in range(n2):
                b = math.tau * j / n2
                fila.append(bm.verts.new(c + radial * R + (rd * math.cos(b) + e * math.sin(b)) * r))
            filas.append(fila)
        caras = []
        for i in range(n1):
            A, B = filas[i], filas[(i + 1) % n1]
            for j in range(n2):
                k = (j + 1) % n2
                caras.append(bm.faces.new((A[j], A[k], B[k], B[j])))
        return self._caras(caras, ranura, bisel)

    def anillo_plano(self, centro, eje, r_ext, r_int, grosor, ranura, lados=24, bisel=True, giro=0.0, u_ref=None):
        """Arandela gruesa: anillo de sección rectangular (con lados=4 y giro=45°, un marco cuadrado)."""
        e = V(eje).normalized()
        base = V(centro) - e * grosor / 2
        perfil = [(0, r_int), (0, r_ext), (grosor, r_ext), (grosor, r_int), (0.0001, r_int)]
        return self.revolucion(base, e, perfil, ranura, lados, bisel=bisel, giro=giro, u_ref=u_ref)

    def esfera(self, centro, radio, ranura, lados=16, anillos=8, escala=(1, 1, 1), eje=(0, 0, 1), bisel=False):
        perfil = [(-radio, 0)]
        for k in range(1, anillos):
            a = -math.pi / 2 + math.pi * k / anillos
            perfil.append((math.sin(a) * radio, math.cos(a) * radio))
        perfil.append((radio, 0))
        caras = self.revolucion(centro, eje, perfil, ranura, lados, bisel=bisel)
        if escala != (1, 1, 1):
            self.transformar(caras, Matrix.Translation(V(centro)) @ Matrix.Diagonal((*escala, 1)) @
                             Matrix.Translation(-V(centro)))
        return caras

    def domo(self, centro, radio, ranura, lados=20, anillos=6, alto=None, eje=(0, 0, 1), cerrado=False):
        """Media esfera hacia +eje (domo de escudo, burbuja de cabina)."""
        alto = radio if alto is None else alto
        perfil = [] if not cerrado else [(0, 0)]
        for k in range(anillos + 1):
            a = math.pi / 2 * k / anillos
            perfil.append((math.sin(a) * alto, math.cos(a) * radio))
        perfil[-1] = (alto, 0)
        return self.revolucion(centro, eje, perfil, ranura, lados, bisel=False)

    def ala(self, secciones, ranura, perfil="redondo", n=10, tapa_raiz=True, tapa_punta=True, bisel=True):
        """
        Ala a lo largo de X. secciones = [(x, y_borde_ataque, cuerda, grosor, z)]. El perfil se dibuja en el plano YZ
        (y crece hacia atrás). `perfil`: "redondo" (subsónico), "rombo" (anguloso), "plano" (placa biselada).
        """
        anillos = []
        for x, yle, cuerda, grosor, z in secciones:
            pts = []
            for i in range(n):
                t = i / n  # vuelta: borde de ataque -> extradós -> borde de salida -> intradós
                if t <= 0.5:
                    s = t * 2
                    lado = 1
                else:
                    s = (1 - t) * 2
                    lado = -1
                if perfil == "redondo":
                    esp = 0.5 * grosor * (2.97 * math.sqrt(max(s, 0)) - 1.26 * s - 3.52 * s * s + 2.84 * s ** 3
                                          - 1.015 * s ** 4) / 1.0
                    esp = max(esp, 0.004)
                elif perfil == "rombo":
                    esp = 0.5 * grosor * (s / 0.4 if s < 0.4 else (1 - s) / 0.6)
                    esp = max(esp, 0.01)
                else:  # plano
                    esp = 0.5 * grosor * (min(1.0, s / 0.12, (1 - s) / 0.12))
                    esp = max(esp, 0.01)
                pts.append(V((x, yle + s * cuerda, z + lado * esp)))
            anillos.append(pts)
        return self.loft(anillos, ranura, tapa_ini=tapa_raiz, tapa_fin=tapa_punta, bisel=bisel)

    def tira(self, puntos, normales, ancho, ranura, alto=0.04, bisel=False):
        """Cinta con un poco de grosor que sigue `puntos` sobre una superficie (franjas de neón, juntas)."""
        anillos = []
        n = len(puntos)
        for i in range(n):
            p = V(puntos[i])
            nn = V(normales[i]).normalized()
            t = (V(puntos[min(i + 1, n - 1)]) - V(puntos[max(i - 1, 0)])).normalized()
            b = t.cross(nn).normalized()
            anillos.append([p + b * ancho / 2, p + b * ancho / 2 + nn * alto,
                            p - b * ancho / 2 + nn * alto, p - b * ancho / 2])
        return self.loft(anillos, ranura, bisel=bisel)

    # ---- detalles comunes ------------------------------------------------------------------------------------

    def rejilla(self, centro, normal, u, ancho, alto, ranura_marco, ranura_lamas, lamas=5, prof=0.08):
        """Rejilla de ventilación: marco + lamas. `u` = dirección del ancho sobre la superficie."""
        n = V(normal).normalized()
        u = V(u).normalized()
        v = n.cross(u).normalized()
        c = V(centro)
        giro = Matrix((u, v, n)).transposed()
        caras = self.caja(c, (ancho, alto, prof), ranura_marco, giro=giro)
        for k in range(lamas):
            t = (k + 0.5) / lamas - 0.5
            caras += self.caja(c + v * t * alto * 0.86 + n * prof * 0.35, (ancho * 0.88, alto * 0.6 / lamas,
                               prof * 0.6), ranura_lamas, giro=giro)
        return caras

    def caja_orientada(self, centro, normal, u, tam, ranura, bisel=True):
        """Caja con su eje Z a lo largo de `normal` y su X a lo largo de `u`."""
        n = V(normal).normalized()
        u = (V(u) - n * V(u).dot(n)).normalized()
        v = n.cross(u)
        return self.caja(centro, tam, ranura, giro=Matrix((u, v, n)).transposed(), bisel=bisel)

    def pernos(self, centro, normal, u, separacion, radio=0.07, alto=0.06, ranura="metal", n=4, lados=6):
        n_ = V(normal).normalized()
        u = (V(u) - n_ * V(u).dot(n_)).normalized()
        v = n_.cross(u)
        c = V(centro)
        caras = []
        offs = [(1, 1), (-1, 1), (-1, -1), (1, -1)] if n == 4 else \
            [(math.cos(math.tau * k / n), math.sin(math.tau * k / n)) for k in range(n)]
        for a, b in offs:
            p = c + (u * a + v * b) * separacion
            caras += self.cilindro(p, n_, radio, alto, ranura, lados=lados, bisel=False)
        return caras

    # ---- acoples -----------------------------------------------------------------------------------------------

    def acople(self, nombre, pos, normal, tipo, direccion, arriba=None, brida=True, malla="cuerpo", acepta=None,
               brida_tam=None, prof=0.14, en_superficie=False):
        """
        Registra un punto de acople y (si `brida`) modela su brida: una placa del tamaño del conector con pernos,
        cuya cara exterior queda justo en `pos`. `normal` apunta hacia fuera de la pieza.
        `arriba`: vector perpendicular a la normal que fija el giro (por defecto +Z, o -Y si la normal es vertical).
        """
        n = V(normal).normalized()
        if arriba is None:
            arriba = V((0, 0, 1)) if abs(n.z) < 0.9 else V((0, -1, 0))
        arriba = (V(arriba) - n * V(arriba).dot(n)).normalized()
        spec = datos.CONECTORES[tipo]
        tam = spec["tam"] if brida_tam is None else brida_tam
        p = V(pos)
        if en_superficie:
            # `pos` es la superficie donde se apoya la brida: la cara exterior queda `prof` más fuera
            p = p + n * prof
        if brida and tam > 0:
            der = arriba.cross(n)
            ranura = "acople"
            # placa + marco de aviso (franjas en tier 1-2, luz en tier 3+) + pernos
            if spec["forma"] == "cuadrado":
                self.caja_orientada(p - n * prof / 2, n, der, (tam * 0.86, tam * 0.86, prof), ranura)
                r2 = math.sqrt(2) / 2
                self.anillo_plano(p - n * prof * 0.54, n, tam * r2, tam * 0.43 * math.sqrt(2), prof * 0.92,
                                  "aviso", lados=4, giro=math.pi / 4, u_ref=der)
                self.caja_orientada(p - n * (prof + 0.05), n, der, (tam * 0.78, tam * 0.78, 0.1), "oscuro")
                self.pernos(p, n, der, tam * 0.3, radio=min(0.08, tam * 0.06), alto=0.05,
                            ranura="metal", lados=6)
            else:
                self.cilindro(p - n * prof, n, tam * 0.43, prof, ranura, lados=16)
                self.anillo_plano(p - n * prof * 0.54, n, tam / 2, tam * 0.43, prof * 0.92, "aviso", lados=16)
                self.cilindro(p - n * (prof + 0.1), n, tam * 0.4, 0.1, "oscuro", lados=16, tapas=False)
                self.pernos(p, n, der, tam * 0.3, radio=min(0.08, tam * 0.05), alto=0.05, ranura="metal",
                            n=6, lados=6)
        a = {"nombre": nombre, "pos": p.copy(), "normal": n.copy(), "arriba": arriba, "tipo": tipo,
             "direccion": direccion, "malla": malla, "tam": tam}
        if direccion == "entrada":
            a["acepta"] = sorted(set(acepta or [tipo]))
        self.acoples.append(a)
        return a

    # ---- utilidades ------------------------------------------------------------------------------------------

    def transformar(self, caras, matriz):
        verts = list({v for f in caras for v in f.verts})
        bmesh.ops.transform(self.bm, matrix=matriz, verts=verts)

    def mover(self, caras, d):
        self.transformar(caras, Matrix.Translation(V(d)))

    def girar(self, caras, angulo, eje, centro=(0, 0, 0)):
        c = V(centro)
        self.transformar(caras, Matrix.Translation(c) @ Matrix.Rotation(angulo, 4, V(eje)) @ Matrix.Translation(-c))

    def duplicar(self, caras):
        res = bmesh.ops.duplicate(self.bm, geom=list(caras))
        nuevas = [g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)]
        for f in nuevas:
            pass
        orig_bisel = {f for f in caras if f in self.sin_bisel}
        if orig_bisel:
            # las copias heredan si se biselan o no
            mapa = res["face_map"]
            for f in orig_bisel:
                if f in mapa:
                    self.sin_bisel.add(mapa[f])
        return nuevas

    def espejo_x(self, caras, x0=0.0):
        """Copia reflejada en X (respecto al plano x = x0)."""
        nuevas = self.duplicar(caras)
        self.transformar(nuevas, Matrix.Translation((x0, 0, 0)) @ Matrix.Diagonal((-1, 1, 1, 1)) @
                         Matrix.Translation((-x0, 0, 0)))
        bmesh.ops.reverse_faces(self.bm, faces=nuevas)
        return nuevas

    def desplazar(self, caras, funcion):
        """Deforma los vértices de `caras` con funcion(Vector) -> Vector (relieve orgánico)."""
        for v in {v for f in caras for v in f.verts}:
            v.co = funcion(v.co.copy())


def rot_euler_roblox(look, up):
    """
    Orientación (grados) de un Attachment de Roblox cuyo LookVector (-Z) es `look` y su UpVector (+Y) es `up`,
    con el orden de Roblox (Orientation: Y, luego X, luego Z).
    """
    look = V(look).normalized()
    up = (V(up) - look * V(up).dot(look)).normalized()
    back = -look
    right = up.cross(back)
    # Columnas de la matriz: right (X), up (Y), back (Z).
    m = [[right[0], up[0], back[0]], [right[1], up[1], back[1]], [right[2], up[2], back[2]]]
    rx = math.asin(max(-1.0, min(1.0, -m[1][2])))
    if abs(m[1][2]) < 0.99999:
        ry = math.atan2(m[0][2], m[2][2])
        rz = math.atan2(m[1][0], m[1][1])
    else:
        ry = math.atan2(-m[2][0], m[0][0])
        rz = 0.0
    return [round(math.degrees(a), 3) + 0.0 for a in (rx, ry, rz)]


def matriz_roblox(rx, ry, rz):
    """La inversa de rot_euler_roblox, para comprobarla: R = Ry * Rx * Rz."""
    rx, ry, rz = (math.radians(a) for a in (rx, ry, rz))
    Rx = Matrix.Rotation(rx, 3, "X")
    Ry = Matrix.Rotation(ry, 3, "Y")
    Rz = Matrix.Rotation(rz, 3, "Z")
    return Ry @ Rx @ Rz


__all__ = ["Constructor", "seccion", "seccion_poligono", "a_roblox", "rot_euler_roblox", "matriz_roblox", "V",
           "Matrix", "Quaternion", "base_ortonormal", "SIN_ATLAS"]
