"""
Constructor de geometría del Planeta Humano.

Todo se hace con sólidos cerrados (cajas, cilindros, tornos, barridos, prismas...): no hay planos sueltos, cada
pieza tiene volumen y grosor. Medidas en studs (1 unidad de Blender = 1 stud). El frente del modelo mira a -Y,
X es el ancho y Z la altura; la base se apoya en z = 0.

Cada primitiva recibe un material de la paleta; el material decide en qué malla cae (base, *_neon, *_cristal...),
salvo que se indique `p="puerta"` para una pieza móvil.
"""

import math
import random

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector, noise

from materiales import spec

EJES = {"z": None, "x": Matrix.Rotation(math.pi / 2, 4, "Y"), "y": Matrix.Rotation(-math.pi / 2, 4, "X")}


def _rot(rot):
    return Euler([math.radians(a) for a in rot], "XYZ").to_matrix().to_4x4()


class Modelo:
    def __init__(self, nombre, info):
        self.nombre = nombre
        self.info = info
        self.partes = {}       # parte -> {"bm": bmesh, "mats": [nombres]}
        self.anclajes = {}     # nombre -> (x, y, z) en coordenadas de Blender
        self.notas = []
        self.rng = random.Random(sum(ord(c) * (i + 1) for i, c in enumerate(nombre)))
        self.esc = min(2.0, max(0.25, max(info["objetivo"]) / 8.0))

    # ------------------------------------------------------------------ interno
    def _dest(self, mat, p):
        sp = spec(mat)
        parte = p or sp.get("parte", "base")
        d = self.partes.setdefault(parte, {"bm": bmesh.new(), "mats": []})
        if mat not in d["mats"]:
            d["mats"].append(mat)
        return d["bm"], d["mats"].index(mat)

    def _fin(self, bm, dst, idx, M=None):
        """Cierra la primitiva (hecha en un bmesh temporal) y la añade a la malla de su parte."""
        if M is not None:
            bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
        for f in bm.faces:
            f.material_index = idx
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new("tmp_prim")
        bm.to_mesh(me)
        bm.free()
        dst.from_mesh(me)
        bpy.data.meshes.remove(me)

    @staticmethod
    def _M(c, rot=None, eje="z", esc=None):
        M = Matrix.Translation(Vector(c))
        if rot:
            M = M @ _rot(rot)
        if EJES.get(eje) is not None:
            M = M @ EJES[eje]
        if esc:
            M = M @ Matrix.Diagonal((*esc, 1.0))
        return M

    def anclaje(self, nombre, pos):
        self.anclajes[nombre] = tuple(pos)

    def nota(self, texto):
        self.notas.append(texto)

    @staticmethod
    def color(hexa, rug=0.5, metal=0.0):
        return f"c:{hexa}:{rug}:{metal}"

    # ------------------------------------------------------------------ primitivas
    def caja(self, c, t, mat, rot=None, bisel=0.0, p=None):
        """Caja centrada en `c` de tamaño `t`."""
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Diagonal((t[0], t[1], t[2], 1.0)))
        if bisel > 0:
            bmesh.ops.bevel(bm, geom=bm.edges[:], offset=bisel, segments=1, affect="EDGES", profile=0.5)
        return self._fin(bm, dst, idx, self._M(c, rot))

    def bloque(self, a, b, mat, **kw):
        """Caja entre dos esquinas."""
        c = [(a[i] + b[i]) / 2 for i in range(3)]
        t = [abs(b[i] - a[i]) for i in range(3)]
        return self.caja(c, t, mat, **kw)

    def cil(self, c, r, h, mat, eje="z", seg=12, r2=None, rot=None, p=None):
        """Cilindro (o cono truncado si se da r2: r abajo, r2 arriba) centrado en `c`."""
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r,
                              radius2=r if r2 is None else r2, depth=h)
        return self._fin(bm, dst, idx, self._M(c, rot, eje))

    def esfera(self, c, r, mat, seg=12, anillos=8, esc=None, rot=None, p=None):
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=anillos, radius=r)
        return self._fin(bm, dst, idx, self._M(c, rot, "z", esc))

    def ico(self, c, r, mat, sub=1, esc=None, rot=None, ruido=0.0, frec=1.0, semilla=0.0, p=None):
        """Icoesfera, opcionalmente deformada con ruido (rocas, copas de árbol)."""
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=sub, radius=r)
        if ruido:
            for v in bm.verts[:]:
                n = noise.noise(v.co * frec / r + Vector((semilla, semilla * 1.7, -semilla)))
                v.co *= 1.0 + ruido * n
        return self._fin(bm, dst, idx, self._M(c, rot, "z", esc))

    def torno(self, c, perfil, mat, seg=16, eje="z", cerrar=False, rot=None, arco=360.0, p=None):
        """
        Sólido de revolución. `perfil` = [(radio, altura), ...] de abajo arriba. Con r = 0 en un extremo se cierra en
        punta; si no, se tapa. Con `cerrar=True` el perfil es un lazo cerrado (cuencos y tubos con grosor).
        """
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        completo = arco >= 359.9
        n = seg if completo else seg + 1
        anillos = []
        for r, z in perfil:
            if r <= 1e-6:
                anillos.append([bm.verts.new((0, 0, z))])
            else:
                anillos.append([bm.verts.new((r * math.cos(math.radians(arco) * i / seg),
                                              r * math.sin(math.radians(arco) * i / seg), z)) for i in range(n)])
        pares = list(zip(anillos[:-1], anillos[1:]))
        if cerrar:
            pares.append((anillos[-1], anillos[0]))
        tramos = seg if completo else seg
        for a, b in pares:
            for i in range(tramos):
                j = (i + 1) % n
                if len(a) == 1 and len(b) == 1:
                    continue
                if len(a) == 1:
                    bm.faces.new((a[0], b[i], b[j]))
                elif len(b) == 1:
                    bm.faces.new((a[i], a[j], b[0]))
                else:
                    bm.faces.new((a[i], a[j], b[j], b[i]))
        if not cerrar:
            for an in (anillos[0], anillos[-1]):
                if len(an) > 2 and completo:
                    bm.faces.new(an)
        if not completo:  # tapas laterales del sector
            for i in (0, n - 1):
                lazo = [an[i] if len(an) > 1 else an[0] for an in anillos]
                lazo = [v for k, v in enumerate(lazo) if k == 0 or v is not lazo[k - 1]]
                if not cerrar:
                    # cierra contra el eje
                    z0, z1 = perfil[0][1], perfil[-1][1]
                    if len(anillos[-1]) > 1:
                        lazo.append(bm.verts.new((0, 0, z1)))
                    if len(anillos[0]) > 1:
                        lazo.append(bm.verts.new((0, 0, z0)))
                if len(lazo) >= 3:
                    bm.faces.new(lazo)
            bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-5)
        return self._fin(bm, dst, idx, self._M(c, rot, eje))

    def tubo(self, c, r, h, grosor, mat, eje="z", seg=16, rot=None, p=None):
        """Anillo o tubo hueco con pared de `grosor` (radio exterior r), centrado en `c`."""
        ri = max(r - grosor, 0.001)
        return self.torno(c, [(ri, -h / 2), (r, -h / 2), (r, h / 2), (ri, h / 2)], mat, seg=seg, eje=eje,
                          cerrar=True, rot=rot, p=p)

    def cupula(self, c, r, mat, grosor=0.15, seg=16, anillos=5, altura=1.0, rot=None, eje="z", p=None):
        """Media esfera hueca con grosor; base en `c`. `altura` aplasta o estira."""
        ext = [(r * math.cos(math.pi / 2 * i / anillos), r * altura * math.sin(math.pi / 2 * i / anillos))
               for i in range(anillos + 1)]
        ri = r - grosor
        inte = [(ri * math.cos(math.pi / 2 * i / anillos), ri * altura * math.sin(math.pi / 2 * i / anillos))
                for i in range(anillos, -1, -1)]
        ext[-1] = (0, ext[-1][1])
        inte[0] = (0, inte[0][1])
        return self.torno(c, ext + inte, mat, seg=seg, cerrar=True, rot=rot, eje=eje, p=p)

    def toro(self, c, R, r, mat, eje="z", seg=20, seg2=8, rot=None, esc=None, p=None):
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        an = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            an.append([bm.verts.new(((R + r * math.cos(2 * math.pi * j / seg2)) * math.cos(a),
                                     (R + r * math.cos(2 * math.pi * j / seg2)) * math.sin(a),
                                     r * math.sin(2 * math.pi * j / seg2))) for j in range(seg2)])
        for i in range(seg):
            a, b = an[i], an[(i + 1) % seg]
            for j in range(seg2):
                k = (j + 1) % seg2
                bm.faces.new((a[j], b[j], b[k], a[k]))
        return self._fin(bm, dst, idx, self._M(c, rot, eje, esc))

    def prisma(self, pts, a, b, mat, plano="xz", c=(0, 0, 0), rot=None, p=None):
        """
        Extruye el polígono 2D `pts` (puede ser cóncavo) entre `a` y `b` en el eje perpendicular al plano:
        'xz' -> a lo largo de Y, 'xy' -> a lo largo de Z, 'yz' -> a lo largo de X.
        """
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()

        def pt(u, v, w):
            return {"xz": (u, w, v), "xy": (u, v, w), "yz": (w, u, v)}[plano]

        va = [bm.verts.new(pt(u, v, a)) for u, v in pts]
        vb = [bm.verts.new(pt(u, v, b)) for u, v in pts]
        n = len(pts)
        fa = bm.faces.new(va)
        fb = bm.faces.new(vb)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((va[i], va[j], vb[j], vb[i]))
        if n > 4:
            fa.normal_update()  # sin normal, la triangulación proyecta mal y deja huecos
            fb.normal_update()
            bmesh.ops.triangulate(bm, faces=[fa, fb], ngon_method="EAR_CLIP")
        return self._fin(bm, dst, idx, self._M(c, rot))

    def barrido(self, pts, r, mat, seg=6, cerrado=False, p=None):
        """Tubo macizo a lo largo de una polilínea 3D. `r` puede ser un número o una lista (un radio por punto)."""
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        P = [Vector(q) for q in pts]
        n = len(P)
        rs = r if isinstance(r, (list, tuple)) else [r] * n
        tans = []
        for i in range(n):
            if cerrado:
                t = P[(i + 1) % n] - P[i - 1]
            else:
                t = P[min(i + 1, n - 1)] - P[max(i - 1, 0)]
            tans.append(t.normalized())
        ref = Vector((0, 0, 1)) if abs(tans[0].z) < 0.9 else Vector((1, 0, 0))
        u = tans[0].cross(ref).normalized()
        an = []
        for i in range(n):
            t = tans[i]
            u = (u - t * u.dot(t))
            u = u.normalized() if u.length > 1e-6 else t.orthogonal().normalized()
            w = t.cross(u)
            an.append([bm.verts.new(P[i] + (u * math.cos(2 * math.pi * k / seg) + w * math.sin(2 * math.pi * k / seg))
                                    * rs[i]) for k in range(seg)])
        tramos = n if cerrado else n - 1
        for i in range(tramos):
            a, b = an[i], an[(i + 1) % n]
            for k in range(seg):
                l = (k + 1) % seg
                bm.faces.new((a[k], a[l], b[l], b[k]))
        if not cerrado:
            bm.faces.new(an[0])
            bm.faces.new(an[-1])
        return self._fin(bm, dst, idx, None)

    def texto(self, txt, c, alto, fondo, mat, rot=None, p=None, espaciado=1.0, res=2):
        """Letras 3D macizas centradas en `c`, de pie y mirando a -Y (o giradas con `rot`)."""
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        cu = bpy.data.curves.new("txt_tmp", "FONT")
        cu.body = txt
        cu.size = alto / 0.72  # altura de las mayúsculas ~0,72 del tamaño de fuente
        cu.extrude = fondo / 2
        cu.resolution_u = res
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.space_character = espaciado
        ob = bpy.data.objects.new("txt_tmp", cu)
        bpy.context.scene.collection.objects.link(ob)
        dep = bpy.context.evaluated_depsgraph_get()
        dep.update()
        me = bpy.data.meshes.new_from_object(ob.evaluated_get(dep))
        bm.from_mesh(me)
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)
        bpy.data.meshes.remove(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-4)
        M = self._M(c, rot) @ Matrix.Rotation(math.pi / 2, 4, "X")
        return self._fin(bm, dst, idx, M)

    # ------------------------------------------------------------------ piezas compuestas pequeñas
    def hoja(self, c, largo, ancho, mat, rot=(0, 0, 0), grosor=None, p=None):
        """Hoja con volumen: rombo aplastado (8 triángulos). Apunta a +X antes de girar."""
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        g = grosor if grosor is not None else ancho * 0.22
        a = bm.verts.new((0, 0, 0))
        b = bm.verts.new((largo, 0, 0))
        l = bm.verts.new((largo * 0.45, ancho / 2, 0))
        r = bm.verts.new((largo * 0.45, -ancho / 2, 0))
        t = bm.verts.new((largo * 0.45, 0, g))
        d = bm.verts.new((largo * 0.45, 0, -g * 0.6))
        for tri in ((a, r, t), (r, b, t), (b, l, t), (l, a, t), (a, d, r), (r, d, b), (b, d, l), (l, d, a)):
            bm.faces.new(tri)
        return self._fin(bm, dst, idx, self._M(c, rot))

    def brizna(self, c, alto, ancho, mat, inclin=(0, 0), giro=0.0, p=None):
        """Brizna de hierba: pirámide triangular cerrada (4 triángulos) con la punta desplazada."""
        dst, idx = self._dest(mat, p)
        bm = bmesh.new()
        base = [bm.verts.new((ancho * math.cos(giro + k * 2.0944), ancho * math.sin(giro + k * 2.0944), 0))
                for k in range(3)]
        punta = bm.verts.new((inclin[0], inclin[1], alto))
        bm.faces.new(base)
        for k in range(3):
            bm.faces.new((base[k], base[(k + 1) % 3], punta))
        return self._fin(bm, dst, idx, Matrix.Translation(Vector(c)))

    def roca(self, c, t, mat, semilla=0.0, sub=2, ruido=0.35, rot=None, p=None):
        """Roca irregular de tamaño aproximado `t` (x, y, z) centrada en `c`."""
        return self.ico(c, 0.5, mat, sub=sub, esc=t, rot=rot, ruido=ruido, frec=1.3, semilla=semilla, p=p)

    def marco(self, c, ancho, alto, grosor, fondo, mat, normal="y", p=None):
        """Marco rectangular (4 listones) en el plano perpendicular a `normal` ('y' o 'x')."""
        x, y, z = c
        g = grosor
        if normal == "y":
            self.caja((x, y, z + alto / 2 - g / 2), (ancho, fondo, g), mat, p=p)
            self.caja((x, y, z - alto / 2 + g / 2), (ancho, fondo, g), mat, p=p)
            self.caja((x - ancho / 2 + g / 2, y, z), (g, fondo, alto - 2 * g), mat, p=p)
            self.caja((x + ancho / 2 - g / 2, y, z), (g, fondo, alto - 2 * g), mat, p=p)
        else:
            self.caja((x, y, z + alto / 2 - g / 2), (fondo, ancho, g), mat, p=p)
            self.caja((x, y, z - alto / 2 + g / 2), (fondo, ancho, g), mat, p=p)
            self.caja((x, y - ancho / 2 + g / 2, z), (fondo, g, alto - 2 * g), mat, p=p)
            self.caja((x, y + ancho / 2 - g / 2, z), (fondo, g, alto - 2 * g), mat, p=p)

    def ventana(self, c, ancho, alto, normal="y", sentido=-1, marco="gris_liso", cristal="cristal", fondo=0.25,
                g=0.15, cruz=False):
        """Ventana: marco saliente + hoja de cristal con grosor. `sentido` = hacia dónde mira (-1 = -eje)."""
        x, y, z = c
        self.marco(c, ancho, alto, g, fondo, marco, normal)
        if normal == "y":
            self.caja((x, y + sentido * 0.02, z), (ancho - 2 * g, 0.08, alto - 2 * g), cristal)
            if cruz:
                self.caja((x, y + sentido * 0.06, z), (g * 0.5, fondo * 0.6, alto - 2 * g), marco)
        else:
            self.caja((x + sentido * 0.02, y, z), (0.08, ancho - 2 * g, alto - 2 * g), cristal)
            if cruz:
                self.caja((x + sentido * 0.06, y, z), (fondo * 0.6, g * 0.5, alto - 2 * g), marco)

    def barandilla(self, a, b, alto, mat="acero", r=0.05, postes=None, travesanos=1, neon=None, seg=6):
        """Barandilla recta entre dos puntos (a ras de suelo): postes, pasamanos y travesaños, todo tubular."""
        A, B = Vector(a), Vector(b)
        L = (B - A).length
        n = postes or max(2, int(round(L / 1.2)) + 1)
        for i in range(n):
            q = A.lerp(B, i / (n - 1))
            self.cil((q.x, q.y, q.z + alto / 2), r, alto, mat, seg=seg)
        up = Vector((0, 0, 1))
        self.barrido([A + up * alto, B + up * alto], r * 1.25, neon or mat, seg=seg)
        for k in range(travesanos):
            h = alto * (k + 1) / (travesanos + 1)
            self.barrido([A + up * h, B + up * h], r * 0.7, mat, seg=seg)

    # ------------------------------------------------------------------ salida
    def objetos(self, angulo_duro=38.0):
        """Convierte las partes en objetos de malla (n-gonos triangulados, aristas duras marcadas)."""
        obs = []
        orden = sorted(self.partes, key=lambda k: (k != "base", k))
        for parte in orden:
            d = self.partes[parte]
            bm = d["bm"]
            if not bm.faces:
                continue
            ng = [f for f in bm.faces if len(f.verts) > 4]
            if ng:
                bmesh.ops.triangulate(bm, faces=ng, ngon_method="BEAUTY")
            lim = math.radians(angulo_duro)
            # El follaje se sombrea más suave que el metal: sus masas son orgánicas, no facetadas.
            organico = {i for i, n in enumerate(d["mats"]) if spec(n)["patron"] == "hojas"}
            lim_org = math.radians(66.0)
            for e in bm.edges:
                if len(e.link_faces) == 2:
                    a, b = e.link_faces
                    l = lim_org if (a.material_index in organico and b.material_index in organico) else lim
                    e.smooth = e.calc_face_angle(0.0) < l
                else:
                    e.smooth = False
            for f in bm.faces:
                f.smooth = True
            nombre = self.nombre if parte == "base" else f"{self.nombre}_{parte}"
            me = bpy.data.meshes.new(nombre)
            bm.to_mesh(me)
            ob = bpy.data.objects.new(nombre, me)
            ob["parte"] = parte
            ob["materiales_origen"] = ",".join(d["mats"])
            bpy.context.scene.collection.objects.link(ob)
            obs.append((ob, d["mats"]))
        return obs


def arco_pts(r_ext, r_int, a0=0.0, a1=180.0, n=10, cx=0.0, cz=0.0, ex=1.0, ez=1.0):
    """Polígono de un arco con grosor (para `prisma`): arco exterior de a0 a a1 y vuelta por el interior."""
    ext = [(cx + ex * r_ext * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
            cz + ez * r_ext * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]
    inte = [(cx + ex * r_int * math.cos(math.radians(a1 - (a1 - a0) * i / n)),
             cz + ez * r_int * math.sin(math.radians(a1 - (a1 - a0) * i / n))) for i in range(n + 1)]
    return ext + inte


def circulo(n, r=1.0, fase=0.0):
    return [(r * math.cos(fase + 2 * math.pi * i / n), r * math.sin(fase + 2 * math.pi * i / n)) for i in range(n)]
