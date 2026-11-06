"""
Kit de construcción de piezas low-poly de superficie dura (edificios, hangar, farolas...).

`Pieza` acumula geometría en un bmesh (en studs) con un índice de material por cara, y al final crea el objeto:
  * caja(), cilindro(), loft(), prisma(), perfil_extruido(): formas básicas con su material.
  * Los materiales se piden por nombre a una PALETA {nombre: (color, rugosidad, metal, suciedad)}.
  * "suciedad" > 0 mezcla en el color un ruido y un oscurecimiento cerca del suelo: al hornear queda en la textura
    y los edificios no parecen de plástico.

`terminar()` hace lo de siempre con una pieza de juego: bisel opcional en las aristas, sombreado con corte por
ángulo, UV, horneado de color + oclusión en una textura, y vuelta a un único material con esa textura.
"""

import math
import os

import bpy  # noqa: F401  (antes que bmesh)
import bmesh
from mathutils import Matrix, Vector

import comun as c

E = c.ESTUDIO


def anillo(y, ancho, alto, zc, n, cuadratura=2.0, xc=0.0):
    """Sección superelíptica en el plano XZ a la altura `y` (para lofts a lo largo de Y)."""
    pts = []
    for i in range(n):
        a = math.tau * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = math.copysign(abs(ca) ** (2 / cuadratura), ca) * ancho / 2
        z = math.copysign(abs(sa) ** (2 / cuadratura), sa) * alto / 2
        pts.append(Vector((xc + x, y, zc + z)))
    return pts


def anillo_z(z, rx, ry, n, xc=0.0, yc=0.0, giro=0.0, cuadratura=2.0):
    """Sección horizontal (plano XY) a la altura `z` (para lofts verticales: torres, troncos, farolas)."""
    pts = []
    for i in range(n):
        a = giro + math.tau * i / n
        ca, sa = math.cos(a), math.sin(a)
        x = math.copysign(abs(ca) ** (2 / cuadratura), ca) * rx
        y = math.copysign(abs(sa) ** (2 / cuadratura), sa) * ry
        pts.append(Vector((xc + x, yc + y, z)))
    return pts


class Pieza:
    def __init__(self, nombre, paleta):
        self.nombre = nombre
        self.paleta = paleta
        self.bm = bmesh.new()
        self.mats = []  # nombres en orden de índice

    def m(self, nombre):
        if nombre not in self.mats:
            assert nombre in self.paleta, f"material sin definir: {nombre}"
            self.mats.append(nombre)
        return self.mats.index(nombre)

    def _pintar(self, verts, mat):
        i = self.m(mat)
        caras = {f for v in verts for f in v.link_faces if all(w in verts for w in f.verts)}
        for f in caras:
            f.material_index = i
        return verts

    # ---- formas -------------------------------------------------------------------------------------------

    def caja(self, centro, tam, mat, giro=None):
        """Caja de tamaño `tam` (x, y, z) centrada en `centro`. `giro`: Matrix 3x3 opcional."""
        r = bmesh.ops.create_cube(self.bm, size=1.0)
        mtx = Matrix.Diagonal((*tam, 1.0))
        if giro is not None:
            mtx = giro.to_4x4() @ mtx
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(Vector(centro)) @ mtx, verts=r["verts"])
        return self._pintar(set(r["verts"]), mat)

    def caja_de(self, mn, mx, mat):
        """Caja entre dos esquinas."""
        mn, mx = Vector(mn), Vector(mx)
        return self.caja((mn + mx) / 2, mx - mn, mat)

    def cilindro(self, base, radio, alto, mat, lados=12, eje="Z", radio2=None, tapas=True):
        """Cilindro (o cono truncado con `radio2`) desde `base` a lo largo del eje."""
        r2 = radio if radio2 is None else radio2
        ejes = {"Z": Matrix.Identity(3), "X": Matrix.Rotation(math.pi / 2, 3, "Y"),
                "Y": Matrix.Rotation(-math.pi / 2, 3, "X")}
        rot = ejes[eje] if isinstance(eje, str) else Vector(eje).normalized().to_track_quat("Z", "Y").to_matrix()
        base = Vector(base)
        ab = [base + rot @ p for p in anillo_z(0, radio, radio, lados)]
        ar = [base + rot @ p for p in anillo_z(alto, r2, r2, lados)]
        return self.loft([ab, ar], mat, tapar_inicio=tapas, tapar_fin=tapas)

    def loft(self, anillos, mat, tapar_inicio=True, tapar_fin=True, cerrado=True):
        bm = self.bm
        vs = [[bm.verts.new(p) for p in a] for a in anillos]
        n = len(anillos[0])
        tramos = n if cerrado else n - 1
        for k in range(len(vs) - 1):
            for i in range(tramos):
                j = (i + 1) % n
                bm.faces.new((vs[k][i], vs[k][j], vs[k + 1][j], vs[k + 1][i]))
        if tapar_inicio and cerrado:
            bm.faces.new(list(reversed(vs[0])))
        if tapar_fin and cerrado:
            bm.faces.new(vs[-1])
        todos = {v for a in vs for v in a}
        return self._pintar(todos, mat)

    def perfil_extruido(self, puntos_xz, y0, y1, mat):
        """Extruye un polígono del plano XZ entre y0 e y1 (para tejados, toldos, persianas, vigas)."""
        a = [Vector((x, y0, z)) for x, z in puntos_xz]
        b = [Vector((x, y1, z)) for x, z in puntos_xz]
        return self.loft([a, b], mat)

    def prisma(self, base, eje, largo, grosor, lados, punta, mat, rnd=None, giro=0.0):
        """Cristal: prisma con punta piramidal (`punta` = fracción del largo que es pirámide)."""
        bm = self.bm
        eje = Vector(eje).normalized()
        q = eje.to_track_quat("Z", "Y")
        base = Vector(base)
        bajo, alto = [], []
        alto_cuerpo = largo * (1 - punta)
        for i in range(lados):
            a = giro + i * math.tau / lados
            r = grosor * (1 + (rnd.uniform(-0.1, 0.1) if rnd else 0))
            bajo.append(bm.verts.new(base + q @ Vector((math.cos(a) * r, math.sin(a) * r, -0.3 * grosor))))
            alto.append(bm.verts.new(base + q @ Vector((math.cos(a) * r * 0.93, math.sin(a) * r * 0.93,
                                                        alto_cuerpo))))
        cima = bm.verts.new(base + q @ Vector((0, 0, largo)))
        for i in range(lados):
            j = (i + 1) % lados
            bm.faces.new((bajo[i], bajo[j], alto[j], alto[i]))
            bm.faces.new((alto[i], alto[j], cima))
        bm.faces.new(list(reversed(bajo)))
        return self._pintar(set(bajo + alto + [cima]), mat)

    def transformar(self, verts, matriz):
        bmesh.ops.transform(self.bm, matrix=matriz, verts=list(verts))

    def espejo_x(self, verts):
        caras = list({f for v in verts for f in v.link_faces if all(w in verts for w in f.verts)})
        res = bmesh.ops.duplicate(self.bm, geom=caras)
        nuevos = [g for g in res["geom"] if isinstance(g, bmesh.types.BMVert)]
        bmesh.ops.scale(self.bm, vec=(-1, 1, 1), verts=nuevos)
        bmesh.ops.reverse_faces(self.bm, faces=[g for g in res["geom"] if isinstance(g, bmesh.types.BMFace)])
        return set(nuevos)

    def vacia(self):
        return len(self.bm.faces) == 0

    # ---- objeto --------------------------------------------------------------------------------------------

    def objeto(self):
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        # Sin polígonos de más de 4 lados: el FBX no puede calcular tangentes (las necesita el mapa de normales).
        ngons = [f for f in self.bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(self.bm, faces=ngons)
        mats = [material_paleta(n, self.paleta[n]) for n in self.mats]
        return c.objeto_desde_bmesh(self.nombre, self.bm, mats)


def material_paleta(nombre, datos):
    """datos = (color hex, rugosidad, metal, suciedad[, emisión])."""
    color, rug, met = datos[0], datos[1], datos[2]
    sucio = datos[3] if len(datos) > 3 else 0.0
    emision = datos[4] if len(datos) > 4 else 0.0
    lin = c.srgb(color)
    mat = c.material(f"{nombre}", lin, rugosidad=rug, metal=met,
                     emision=lin if emision else None, fuerza_emision=emision)
    if sucio > 0:
        nt = mat.node_tree
        b = nt.nodes["Principled BSDF"]
        coords = nt.nodes.new("ShaderNodeTexCoord")
        ruido = nt.nodes.new("ShaderNodeTexNoise")
        ruido.inputs["Scale"].default_value = 2.2
        ruido.inputs["Detail"].default_value = 6
        nt.links.new(coords.outputs["Object"], ruido.inputs["Vector"])
        rampa = nt.nodes.new("ShaderNodeValToRGB")
        rampa.color_ramp.elements[0].position = 0.35
        rampa.color_ramp.elements[0].color = (1 - sucio * 0.28,) * 3 + (1,)
        rampa.color_ramp.elements[1].position = 0.75
        rampa.color_ramp.elements[1].color = (1, 1, 1, 1)
        nt.links.new(ruido.outputs["Fac"], rampa.inputs["Fac"])
        # Oscurece cerca del suelo (salpicaduras, polvo): z del objeto en metros.
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(coords.outputs["Object"], sep.inputs["Vector"])
        mapa = nt.nodes.new("ShaderNodeMapRange")
        mapa.inputs["From Min"].default_value = 0.0
        mapa.inputs["From Max"].default_value = 1.2 * E
        mapa.inputs["To Min"].default_value = 1 - sucio * 0.6
        mapa.inputs["To Max"].default_value = 1.0
        nt.links.new(sep.outputs["Z"], mapa.inputs["Value"])
        m1 = nt.nodes.new("ShaderNodeMix")
        m1.data_type = "RGBA"
        m1.blend_type = "MULTIPLY"
        m1.inputs["Factor"].default_value = 1.0
        m1.inputs["A"].default_value = (*lin, 1)
        nt.links.new(rampa.outputs["Color"], m1.inputs["B"])
        m2 = nt.nodes.new("ShaderNodeMix")
        m2.data_type = "RGBA"
        m2.blend_type = "MULTIPLY"
        m2.inputs["Factor"].default_value = 1.0
        nt.links.new(m1.outputs["Result"], m2.inputs["A"])
        nt.links.new(mapa.outputs["Result"], m2.inputs["B"])
        nt.links.new(m2.outputs["Result"], b.inputs["Base Color"])
    return mat


def biselar(obj, ancho_studs=0.08, angulo=40):
    """Bisel de un segmento en las aristas vivas: brillos en los bordes, que es lo que hace que no parezca Lego."""
    mod = obj.modifiers.new("bisel", "BEVEL")
    mod.width = ancho_studs * E
    mod.segments = 1
    mod.limit_method = "ANGLE"
    mod.angle_limit = math.radians(angulo)
    mod.harden_normals = False
    c.aplicar_modificadores(obj)


def terminar(pieza, carpeta, rapido, bisel=0.08, tam=1024, uv_margen=0.004, con_textura=True, ao=0.7):
    """Crea el objeto de la pieza, bisela, sombrea y hornea su textura (si `con_textura`). Devuelve el objeto."""
    obj = pieza.objeto()
    if bisel:
        biselar(obj, bisel)
    c.sombreado_suave(obj, angulo=35)
    if con_textura:
        c.desplegar_uv(obj, margen=uv_margen)
        c.hornear(obj, None, tam=256 if rapido else tam,
                  ruta_color=os.path.join(carpeta, "texturas", f"{pieza.nombre}_color.png"),
                  muestras=8 if rapido else 48, distancia_oclusion=ao)
    return obj


def origen_abajo(objetos):
    """Mueve el conjunto para que su base quede en z = 0 y centrado en XY (como se colocan en Studio)."""
    mn, mx = c.caja_limite(objetos)
    d = Vector((-(mn.x + mx.x) / 2, -(mn.y + mx.y) / 2, -mn.z))
    for o in objetos:
        o.data.transform(Matrix.Translation(d))
    return d / E


# --------------------------------------------------------------------------------------------------------------
# Lote: construir varias piezas, exportarlas, renderizarlas y montar una hoja con una fila por pieza
# --------------------------------------------------------------------------------------------------------------

VISTAS_EDIFICIO = [("Frente", 0, 10), ("3/4", -40, 22), ("Lateral", -90, 8), ("3/4 trasera", 140, 25),
                   ("Arriba", 15, 70)]


def ejecutar_lote(items, salida, titulo, ronda, rapido, vistas=None, nota="", solo=(), margen=1.05, tam=400):
    """
    items: lista de dicts {archivo, titulo, construir(carpeta, rapido) -> (objetos, extra)}.
    Cada pieza se centra con la base en z = 0, se exporta a <archivo>.fbx y, si `extra` no es None, a
    <archivo>.json. Devuelve la ruta de la hoja.
    """
    import json

    salida = os.path.abspath(salida)
    os.makedirs(os.path.join(salida, "texturas"), exist_ok=True)
    tmp = os.path.join(salida, "_render_tmp")
    c.escena_vacia()
    c.preparar_estudio(mundo=0.6)
    filas, etiquetas = [], []
    for it in items:
        if solo and it["archivo"] not in solo:
            continue
        objetos, extra = it["construir"](salida, rapido)
        desplazamiento = origen_abajo(objetos)
        tris = sum(c.triangulos(o) for o in objetos)
        mn, mx = c.caja_limite(objetos)
        dim = (mx - mn) / E
        c.exportar_fbx(os.path.join(salida, f"{it['archivo']}.fbx"), objetos)
        if extra is not None:
            if callable(extra):
                extra = extra(desplazamiento)
            with open(os.path.join(salida, f"{it['archivo']}.json"), "w", encoding="utf-8") as f:
                json.dump(extra, f, indent=2, ensure_ascii=False)
        fila = c.renderizar_vistas(objetos, tmp, vistas or VISTAS_EDIFICIO, tam=300 if rapido else tam,
                                   muestras=16 if rapido else 64, prefijo=it["archivo"], margen=margen)
        if it.get("vista_extra"):
            # Una vista más con el modelo cambiado (p. ej. la persiana subida), sustituyendo a la de arriba.
            fila = fila[:4] + it["vista_extra"](objetos, tmp, 300 if rapido else tam, 16 if rapido else 64) + fila[5:]
        filas.append(fila)
        partes = ", ".join(f"{o.name} {c.triangulos(o)}" for o in objetos)
        etiquetas.append(f"{it['titulo']}\n{it['archivo']}\n{tris} triángulos\n"
                         f"{dim.x:.1f}×{dim.y:.1f}×{dim.z:.1f} st")
        print(f"[info] {it['archivo']}: {tris} tri ({partes})")
        for o in objetos:
            o.hide_render = True
            o.hide_set(True)
        for o in bpy.data.objects:
            if o.type == "LIGHT" and o.get("de_pieza"):
                o.hide_render = True
    hoja = os.path.join(salida, f"hoja_contactos_{ronda}.png")
    c.montar_hoja(filas, hoja, f"{titulo} — ronda {ronda}", notas=[nota] if nota else (), etiquetas_fila=etiquetas)
    return hoja


def argumentos():
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", required=True)
    ap.add_argument("--ronda", default="final")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--solo", default="")
    a = ap.parse_args()
    a.solo = tuple(filter(None, a.solo.split(",")))
    return a
