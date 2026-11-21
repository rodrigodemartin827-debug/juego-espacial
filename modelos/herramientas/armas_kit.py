"""
Kit para modelar las armas y herramientas (ver armas.py).

Se apoya en kit.py (Pieza: cajas, cilindros, lofts) y comun.py (escena, render, FBX) y añade lo propio de las armas:

  * Formas: barrido de hojas por una curva con sección a medida (rombo con canal, sable de un filo...), tubos huecos
    (cañones), esferas, toros, perfiles extruidos de lado (cuerpos de pistola) y láminas de neón que siguen la hoja.
  * Materiales con patrón de relieve (grip diamantado, cuero, madera, hierro meteorítico...) que se hornea en el mapa
    de normales, y variación de color (degradados, manchas, vetas).
  * Horneado en UN atlas por arma para todas las piezas con textura (comparten la misma SurfaceAppearance):
        <Arma>_color.png      albedo con oclusión ambiental (y alfa si alguna pieza es translúcida)
        <Arma>_normal.png     normales en espacio tangente
        <Arma>_roughness.png  rugosidad
        <Arma>_metalness.png  metalicidad
        <Arma>_emision.png    máscara: blanco donde hay una pieza _Neon encima
  * Empty "Handle" (y "Handle_Frontal" en rifles) con el eje Y hacia la hoja o el cañón.
  * Turnaround de 4 vistas (frente, perfil derecho, trasera, perfil izquierdo) en estudio gris de 3 puntos, más
    3/4, comparación con un brazo R6 y malla.

Unidades: todo se escribe en studs (1 unidad del script = 1 stud) y se exporta en metros con 1 stud = 0,28 m, que es
lo que lee el importador de Roblox (ver modelos/README.md). Ejes: las armas cuerpo a cuerpo tienen la hoja hacia +Z y
las de fuego el cañón hacia -Y (el delante); la exportación de comun.py ya convierte los ejes a los de Roblox.
"""

import json
import math
import os

import bpy  # noqa: F401  (antes que bmesh)
import bmesh
import numpy as np
from mathutils import Matrix, Vector

import comun as c
import kit

E = c.ESTUDIO
CIAN = "#3DF2FF"

# Rareza: color del borde, triángulos máximos y tamaño de textura.
RAREZAS = {
    "Comun": {"nombre": "Común", "borde": "#888888", "tris": 2500, "tex": 1024},
    "PocoComun": {"nombre": "Poco común", "borde": "#4AFF8B", "tris": 3000, "tex": 1024},
    "Raro": {"nombre": "Raro", "borde": "#4488FF", "tris": 4000, "tex": 2048},
    "Epico": {"nombre": "Épico", "borde": "#A07AE8", "tris": 5000, "tex": 2048},
    "Legendario": {"nombre": "Legendario", "borde": "#FFB800", "tris": 6500, "tex": 2048},
    "Mitico": {"nombre": "Mítico", "borde": "#FF4444", "tris": 8000, "tex": 2048},
}


# --------------------------------------------------------------------------------------------------------------
# Materiales con patrón
# --------------------------------------------------------------------------------------------------------------
#
# Paleta de un arma: {nombre: dict(color, rug, met, patron=None, relieve=1.0, escala=1.0, color2=None,
#                                  mezcla=None, alfa=1.0, emision=0.0)}
#   patron:  relieve que acaba en el mapa de normales (ver _patron).
#   mezcla:  cómo se reparte color2: ("grad", eje, a, b) degradado en studs a lo largo de un eje,
#            ("manchas", escala, umbral) o ("vetas", escala, umbral).
#   alfa:    < 1 para piezas translúcidas (va al canal alfa del color; en Studio, AlphaMode = Transparency).
#   emision: solo para el render (las piezas _Neon y similares no llevan textura).


def _n(nt, tipo, **props):
    nodo = nt.nodes.new(tipo)
    for k, v in props.items():
        setattr(nodo, k, v)
    return nodo


def _coords(nt, escala, rot=(0, 0, 0)):
    """Coordenadas de objeto en studs (el objeto está en metros), escaladas y giradas."""
    tc = _n(nt, "ShaderNodeTexCoord")
    mp = _n(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (escala / E,) * 3
    mp.inputs["Rotation"].default_value = rot
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def _patron(nt, nombre, escala):
    """Devuelve un socket de altura (0..1) con el patrón de relieve pedido."""
    L = nt.links
    if nombre == "diamante":  # moleteado: dos ondas cruzadas en diagonal
        out = []
        for ang in (0.7854, -0.7854):
            w = _n(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", wave_profile="TRI")
            w.inputs["Scale"].default_value = 1.0
            L.new(_coords(nt, 9 * escala, (ang, 0, ang)), w.inputs["Vector"])
            out.append(w.outputs["Fac"])
        m = _n(nt, "ShaderNodeMath", operation="MINIMUM")
        L.new(out[0], m.inputs[0])
        L.new(out[1], m.inputs[1])
        return m.outputs[0]
    if nombre == "cuero":  # tiras enrolladas en espiral con poro fino
        w = _n(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z", wave_profile="SIN")
        w.inputs["Scale"].default_value = 1.0
        w.inputs["Distortion"].default_value = 1.5
        L.new(_coords(nt, 3.2 * escala, (0.35, 0, 0)), w.inputs["Vector"])
        r = _n(nt, "ShaderNodeTexNoise")
        r.inputs["Scale"].default_value = 1.0
        L.new(_coords(nt, 60 * escala), r.inputs["Vector"])
        m = _n(nt, "ShaderNodeMix", data_type="FLOAT", blend_type="MIX")
        m.inputs["Factor"].default_value = 0.2
        L.new(w.outputs["Fac"], m.inputs["A"])
        L.new(r.outputs["Fac"], m.inputs["B"])
        return m.outputs["Result"]
    if nombre == "madera":
        w = _n(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="X", wave_profile="SIN")
        w.inputs["Scale"].default_value = 1.0
        w.inputs["Distortion"].default_value = 6.0
        w.inputs["Detail"].default_value = 4.0
        L.new(_coords(nt, 1.0 * escala) , w.inputs["Vector"])
        mp = w.inputs["Vector"].links[0].from_node
        mp.inputs["Scale"].default_value = (14 * escala / E, 14 * escala / E, 0.8 * escala / E)
        return w.outputs["Fac"]
    if nombre in ("widman", "cristalino"):  # cristales entrecruzados del hierro meteorítico
        v = _n(nt, "ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE")
        v.inputs["Scale"].default_value = 1.0
        L.new(_coords(nt, (5 if nombre == "widman" else 2.5) * escala), v.inputs["Vector"])
        mp = v.inputs["Vector"].links[0].from_node
        mp.inputs["Scale"].default_value = (5 * escala / E, 1.5 * escala / E, 5 * escala / E)
        p = _n(nt, "ShaderNodeMath", operation="POWER")
        L.new(v.outputs["Distance"], p.inputs[0])
        p.inputs[1].default_value = 0.35
        return p.outputs[0]
    if nombre == "fundido":  # ondas de metal que se derrite
        w = _n(nt, "ShaderNodeTexWave", wave_type="RINGS", rings_direction="SPHERICAL", wave_profile="SIN")
        w.inputs["Scale"].default_value = 1.0
        w.inputs["Distortion"].default_value = 9.0
        w.inputs["Detail"].default_value = 3.0
        L.new(_coords(nt, 1.6 * escala), w.inputs["Vector"])
        return w.outputs["Fac"]
    if nombre == "paneles":  # juntas de paneles atornillados
        b = _n(nt, "ShaderNodeTexBrick")
        b.inputs["Scale"].default_value = 1.0
        b.inputs["Mortar Size"].default_value = 0.02
        b.inputs["Color1"].default_value = (1, 1, 1, 1)
        b.inputs["Color2"].default_value = (1, 1, 1, 1)
        b.inputs["Mortar"].default_value = (0, 0, 0, 1)
        L.new(_coords(nt, 3.0 * escala, (1.5708, 0, 0)), b.inputs["Vector"])
        return b.outputs["Fac"]
    if nombre == "polimero":  # punteado antideslizante
        v = _n(nt, "ShaderNodeTexVoronoi", feature="F1")
        v.inputs["Scale"].default_value = 1.0
        L.new(_coords(nt, 40 * escala), v.inputs["Vector"])
        return v.outputs["Distance"]
    if nombre in ("hueso", "roca"):
        r = _n(nt, "ShaderNodeTexNoise")
        r.inputs["Scale"].default_value = 1.0
        r.inputs["Detail"].default_value = 8.0
        r.inputs["Roughness"].default_value = 0.65 if nombre == "roca" else 0.5
        L.new(_coords(nt, (6 if nombre == "roca" else 4) * escala), r.inputs["Vector"])
        return r.outputs["Fac"]
    if nombre == "grabado":  # filigrana: aristas de voronoi muy finas
        v = _n(nt, "ShaderNodeTexVoronoi", feature="DISTANCE_TO_EDGE")
        v.inputs["Scale"].default_value = 1.0
        L.new(_coords(nt, 7 * escala), v.inputs["Vector"])
        s = _n(nt, "ShaderNodeMath", operation="SMOOTH_MAX" if False else "MINIMUM")
        L.new(v.outputs["Distance"], s.inputs[0])
        s.inputs[1].default_value = 0.06
        k = _n(nt, "ShaderNodeMath", operation="MULTIPLY")
        L.new(s.outputs[0], k.inputs[0])
        k.inputs[1].default_value = 16
        return k.outputs[0]
    if nombre == "cepillado":  # metal cepillado a lo largo del eje Z
        r = _n(nt, "ShaderNodeTexNoise")
        r.inputs["Scale"].default_value = 1.0
        L.new(_coords(nt, 1.0 * escala), r.inputs["Vector"])
        mp = r.inputs["Vector"].links[0].from_node
        mp.inputs["Scale"].default_value = (90 * escala / E, 90 * escala / E, 1.5 * escala / E)
        return r.outputs["Fac"]
    raise ValueError(f"patrón desconocido: {nombre}")


def material_arma(nombre, d):
    lin = c.srgb(d["color"])
    emision = d.get("emision", 0.0)
    mat = c.material(nombre, lin, rugosidad=d["rug"], metal=d["met"],
                     emision=lin if emision else None, fuerza_emision=emision)
    mat["metal"] = d["met"]
    mat["alfa"] = d.get("alfa", 1.0)
    nt = mat.node_tree
    L = nt.links
    b = nt.nodes["Principled BSDF"]
    esc = d.get("escala", 1.0)
    # Variación de color.
    mezcla = d.get("mezcla")
    if mezcla and d.get("color2"):
        lin2 = c.srgb(d["color2"])
        if mezcla[0] == "grad":
            _, eje, a, bb = mezcla
            tc = _n(nt, "ShaderNodeTexCoord")
            sep = _n(nt, "ShaderNodeSeparateXYZ")
            L.new(tc.outputs["Object"], sep.inputs["Vector"])
            mr = _n(nt, "ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = a * E
            mr.inputs["From Max"].default_value = bb * E
            L.new(sep.outputs[eje], mr.inputs["Value"])
            fac = mr.outputs["Result"]
        else:
            _, escala_m, umbral = mezcla
            if mezcla[0] == "manchas":
                t = _n(nt, "ShaderNodeTexNoise")
                t.inputs["Detail"].default_value = 6
                t.inputs["Scale"].default_value = 1.0
                L.new(_coords(nt, escala_m), t.inputs["Vector"])
                src = t.outputs["Fac"]
            else:  # vetas
                t = _n(nt, "ShaderNodeTexWave", wave_type="BANDS", bands_direction="Z", wave_profile="SAW")
                t.inputs["Scale"].default_value = 1.0
                t.inputs["Distortion"].default_value = 12
                t.inputs["Detail"].default_value = 5
                L.new(_coords(nt, escala_m), t.inputs["Vector"])
                src = t.outputs["Fac"]
            mr = _n(nt, "ShaderNodeMapRange")
            mr.inputs["From Min"].default_value = umbral
            mr.inputs["From Max"].default_value = umbral + 0.08
            L.new(src, mr.inputs["Value"])
            fac = mr.outputs["Result"]
        mx = _n(nt, "ShaderNodeMix", data_type="RGBA", blend_type="MIX")
        mx.inputs["A"].default_value = (*lin, 1)
        mx.inputs["B"].default_value = (*lin2, 1)
        L.new(fac, mx.inputs["Factor"])
        L.new(mx.outputs["Result"], b.inputs["Base Color"])
    # Nubes: una segunda capa de color con ruido (nebulosas).
    if d.get("nubes"):
        col3, esc_n, fuerza = d["nubes"]
        base = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].is_linked else None
        t = _n(nt, "ShaderNodeTexNoise")
        t.inputs["Scale"].default_value = 1.0
        t.inputs["Detail"].default_value = 8
        L.new(_coords(nt, esc_n), t.inputs["Vector"])
        mr0 = _n(nt, "ShaderNodeMapRange")
        mr0.inputs["From Min"].default_value = 0.45
        mr0.inputs["From Max"].default_value = 0.75
        mr0.inputs["To Max"].default_value = fuerza
        L.new(t.outputs["Fac"], mr0.inputs["Value"])
        mx = _n(nt, "ShaderNodeMix", data_type="RGBA", blend_type="SCREEN")
        if base is not None:
            L.new(base, mx.inputs["A"])
        else:
            mx.inputs["A"].default_value = (*lin, 1)
        mx.inputs["B"].default_value = (*c.srgb(col3), 1)
        L.new(mr0.outputs["Result"], mx.inputs["Factor"])
        L.new(mx.outputs["Result"], b.inputs["Base Color"])
    # Rugosidad con una variación suave (que no parezca plástico uniforme).
    rn = _n(nt, "ShaderNodeTexNoise")
    rn.inputs["Scale"].default_value = 1.0
    L.new(_coords(nt, 3.0), rn.inputs["Vector"])
    mr = _n(nt, "ShaderNodeMapRange")
    var = 0.06 if d["rug"] > 0.1 else 0.02
    mr.inputs["To Min"].default_value = max(0.0, d["rug"] - var)
    mr.inputs["To Max"].default_value = min(1.0, d["rug"] + var)
    L.new(rn.outputs["Fac"], mr.inputs["Value"])
    L.new(mr.outputs["Result"], b.inputs["Roughness"])
    # Relieve.
    if d.get("patron"):
        alt = _patron(nt, d["patron"], esc)
        bump = _n(nt, "ShaderNodeBump")
        bump.inputs["Strength"].default_value = min(1.0, 0.6 * d.get("relieve", 1.0))
        bump.inputs["Distance"].default_value = 0.012 * E * d.get("relieve", 1.0)
        L.new(alt, bump.inputs["Height"])
        L.new(bump.outputs["Normal"], b.inputs["Normal"])
    if d.get("alfa", 1.0) < 1.0:
        b.inputs["Alpha"].default_value = d["alfa"]
        b.inputs["Transmission Weight"].default_value = 0.5
    return mat


# --------------------------------------------------------------------------------------------------------------
# Geometría
# --------------------------------------------------------------------------------------------------------------

# Secciones de hoja (u a lo ancho -1..1, v a lo grueso -1..1), en orden alrededor.
SECCION_ROMBO = [(1, 0), (0.45, 0.8), (0, 1), (-0.45, 0.8), (-1, 0), (-0.45, -0.8), (0, -1), (0.45, -0.8)]
# Rombo aplanado con canal central (fuller) en las dos caras.
SECCION_CANAL = [(1, 0), (0.42, 0.82), (0.16, 1), (0.1, 0.55), (-0.1, 0.55), (-0.16, 1), (-0.42, 0.82), (-1, 0),
                 (-0.42, -0.82), (-0.16, -1), (-0.1, -0.55), (0.1, -0.55), (0.16, -1), (0.42, -0.82)]
# Un solo filo (en u = +1) y lomo plano (u = -1).
SECCION_SABLE = [(1, 0), (0.35, 0.85), (-0.85, 1), (-1, 0.6), (-1, -0.6), (-0.85, -1), (0.35, -0.85)]
# Hoja de cuchilla: lomo grueso, cuerpo plano y bisel al filo.
SECCION_CUCHILLA = [(1, 0), (0.55, 0.75), (-0.8, 1), (-1, 0.7), (-1, -0.7), (-0.8, -1), (0.55, -0.75)]
# Rombo con canal profundo y ancho (espada estelar).
SECCION_DIAMANTE = [(1, 0), (0.5, 0.7), (0.3, 1), (0.16, 0.35), (-0.16, 0.35), (-0.3, 1), (-0.5, 0.7), (-1, 0),
                    (-0.5, -0.7), (-0.3, -1), (-0.16, -0.35), (0.16, -0.35), (0.3, -1), (0.5, -0.7)]


def _tangente(f, t, h=1e-3):
    a = Vector(f(max(0.0, t - h)))
    b = Vector(f(min(1.0, t + h)))
    return (b - a).normalized()


class PiezaArma(kit.Pieza):
    """Pieza de arma: kit.Pieza + formas curvas. Todo en studs."""

    def __init__(self, nombre, paleta):
        super().__init__(nombre, paleta)

    def m(self, nombre):
        if nombre not in self.mats:
            assert nombre in self.paleta, f"material sin definir: {nombre}"
            self.mats.append(nombre)
        return self.mats.index(nombre)

    # ---- hojas ----------------------------------------------------------------------------------------------

    def barrido(self, camino, mat, n=16, seccion=SECCION_ROMBO, ancho=lambda t: 0.15, grueso=lambda t: 0.03,
                desvio=lambda t: 0.0, punta=True, tapar_base=True, y0=0.0, t0=0.0, t1=1.0, giro_v=None,
                mats_seccion=None):
        """
        Barre una sección por una curva del plano XZ. `camino(t)` -> (x, z); la sección se abre a lo ancho en el
        plano XZ (perpendicular a la curva) y a lo grueso en Y. `ancho`/`grueso` son semianchos. `desvio(t)` mueve
        la sección a lo ancho (para hojas de un filo que no van centradas en la curva). Con `punta` el último anillo
        se cierra en un vértice.
        """
        bm = self.bm
        anillos = []
        ts = [t0 + (t1 - t0) * i / n for i in range(n + 1)]
        for k, t in enumerate(ts):
            if punta and k == n:
                break
            x, z = camino(t)
            tx, tz = _tangente(camino, t).x, _tangente(camino, t).y
            nx, nz = tz, -tx  # normal en el plano (a la derecha de la curva)
            hw, ht, dv = ancho(t), grueso(t), desvio(t)
            gv = giro_v(t) if giro_v else 0.0
            anillo = []
            for u, v in seccion:
                w = dv + u * hw
                anillo.append(bm.verts.new((x + nx * w, y0 + v * ht + gv * u, z + nz * w)))
            anillos.append(anillo)
        caras = []
        especiales = []  # (cara, material) de los tramos de la sección con otro material (canal, filo)
        m = len(seccion)
        for a, b in zip(anillos, anillos[1:]):
            for i in range(m):
                j = (i + 1) % m
                f = bm.faces.new((a[i], a[j], b[j], b[i]))
                caras.append(f)
                if mats_seccion and mats_seccion[i] and mats_seccion[i] != mat:
                    especiales.append((f, mats_seccion[i]))
        if punta:
            x, z = camino(ts[-1])
            tx, tz = _tangente(camino, ts[-1]).x, _tangente(camino, ts[-1]).y
            dv = desvio(ts[-1])
            cima = bm.verts.new((x + tz * dv, y0, z - tx * dv))
            u = anillos[-1]
            for i in range(m):
                caras.append(bm.faces.new((u[i], u[(i + 1) % m], cima)))
        else:
            caras.append(bm.faces.new(anillos[-1]))
        if tapar_base:
            caras.append(bm.faces.new(list(reversed(anillos[0]))))
        i = self.m(mat)
        for f in caras:
            f.material_index = i
        for f, mt in especiales:
            f.material_index = self.m(mt)
        return {v for a in anillos for v in a}

    # ---- sólidos ------------------------------------------------------------------------------------------

    def esfera(self, centro, r, mat, seg=12, anillos=8, escala=(1, 1, 1), giro=None):
        res = bmesh.ops.create_uvsphere(self.bm, u_segments=seg, v_segments=anillos, radius=1.0)
        mtx = Matrix.Diagonal((r * escala[0], r * escala[1], r * escala[2], 1.0))
        if giro is not None:
            mtx = giro.to_4x4() @ mtx
        bmesh.ops.transform(self.bm, matrix=Matrix.Translation(Vector(centro)) @ mtx, verts=res["verts"])
        return self._pintar(set(res["verts"]), mat)

    def toro(self, centro, R, r, mat, seg=24, lados=6, eje=(0, 0, 1), escala_r=(1, 1), arco=None):
        """Toro alrededor de `eje`. `escala_r` aplana la sección (radial, axial). `arco`=(a0, a1) para un trozo."""
        bm = self.bm
        rot = Vector(eje).normalized().to_track_quat("Z", "Y").to_matrix()
        cerrado = arco is None
        a0, a1 = arco or (0.0, math.tau)
        npts = seg if cerrado else seg + 1
        anillos = []
        for i in range(npts):
            a = a0 + (a1 - a0) * i / seg
            ca, sa = math.cos(a), math.sin(a)
            anillo = []
            for k in range(lados):
                b = math.tau * k / lados
                rr = R + r * escala_r[0] * math.cos(b)
                p = Vector((ca * rr, sa * rr, r * escala_r[1] * math.sin(b)))
                anillo.append(bm.verts.new(Vector(centro) + rot @ p))
            anillos.append(anillo)
        pares = list(zip(anillos, anillos[1:])) + ([(anillos[-1], anillos[0])] if cerrado else [])
        caras = []
        for a, b in pares:
            for k in range(lados):
                j = (k + 1) % lados
                caras.append(bm.faces.new((a[k], a[j], b[j], b[k])))
        if not cerrado:
            caras.append(bm.faces.new(list(reversed(anillos[0]))))
            caras.append(bm.faces.new(anillos[-1]))
        i = self.m(mat)
        for f in caras:
            f.material_index = i
        return {v for a in anillos for v in a}

    def tubo(self, base, eje, largo, r_ext, r_int, mat, lados=16, cuad_ext=2.0, cuad_int=2.0, giro=0.0,
             r_ext2=None, mat_int=None, fondo=None):
        """
        Tubo hueco (cañón): pared exterior, interior y coronas en los dos extremos. `cuad_*` = 2 círculo, alto =
        cuadrado. `fondo`: profundidad del ánima (si se da, el interior acaba en un fondo cerrado en vez de
        atravesar).
        """
        bm = self.bm
        rot = Vector(eje).normalized().to_track_quat("Z", "Y").to_matrix()
        base = Vector(base)
        r2 = r_ext if r_ext2 is None else r_ext2

        def anillo(z, rx, cu):
            return [bm.verts.new(base + rot @ p) for p in kit.anillo_z(z, rx, rx, lados, giro=giro, cuadratura=cu)]

        e0, e1 = anillo(0, r_ext, cuad_ext), anillo(largo, r2, cuad_ext)
        prof = largo if fondo is None else fondo
        i0, i1 = anillo(largo - prof, r_int, cuad_int), anillo(largo, r_int, cuad_int)
        caras = []
        n = lados
        for k in range(n):
            j = (k + 1) % n
            caras.append(bm.faces.new((e0[k], e0[j], e1[j], e1[k])))   # exterior
            caras.append(bm.faces.new((i0[j], i0[k], i1[k], i1[j])))   # interior (hacia dentro)
            caras.append(bm.faces.new((e1[k], e1[j], i1[j], i1[k])))   # corona de la boca
            if fondo is None:
                caras.append(bm.faces.new((e0[j], e0[k], i0[k], i0[j])))  # corona trasera
        if fondo is not None:
            caras.append(bm.faces.new(list(reversed(e0))))
            caras.append(bm.faces.new(i0))
        im = self.m(mat)
        for f in caras:
            f.material_index = im
        if mat_int:
            ii = self.m(mat_int)
            for f in caras:
                if all(v in i0 or v in i1 for v in f.verts):
                    f.material_index = ii
        return set(e0 + e1 + i0 + i1)

    def perfil_x(self, puntos_yz, x0, x1, mat):
        """Extruye un polígono del plano YZ (vista de perfil) entre x0 y x1: cuerpos de pistola, guardas, gatillos."""
        a = [Vector((x0, y, z)) for y, z in puntos_yz]
        b = [Vector((x1, y, z)) for y, z in puntos_yz]
        return self.loft([a, b], mat)

    def perfil_x_biselado(self, puntos_yz, ancho, chaflan, mat, xc=0.0):
        """Como perfil_x pero con las caras laterales achaflanadas (el contorno encoge `chaflan` en los lados)."""
        c2 = Vector((sum(p[0] for p in puntos_yz) / len(puntos_yz), sum(p[1] for p in puntos_yz) / len(puntos_yz)))

        def encoger(pts, d):
            res = []
            n = len(pts)
            for i in range(n):
                p, a, b = Vector(pts[i]), Vector(pts[i - 1]), Vector(pts[(i + 1) % n])
                n1 = Vector((-(p - a).y, (p - a).x)).normalized()
                n2 = Vector((-(b - p).y, (b - p).x)).normalized()
                nm = (n1 + n2).normalized()
                # Hacia dentro: el lado del centroide.
                if (c2 - p).dot(nm) < 0:
                    nm = -nm
                res.append(p + nm * d / max(0.3, n1.dot(nm) if (c2 - p).dot(n1) > 0 else -n1.dot(nm)))
            return res

        dentro = encoger(puntos_yz, chaflan)
        h = ancho / 2
        capas = [(-h, dentro), (-h + chaflan, puntos_yz), (h - chaflan, puntos_yz), (h, dentro)]
        anillos = [[Vector((xc + x, p[0], p[1])) for p in pts] for x, pts in capas]
        return self.loft(anillos, mat)

    def lamina(self, puntos, normal, grosor, mat):
        """Lámina fina (neón): polígono de `puntos` 3D extruido `grosor` a lo largo de `normal`."""
        nrm = Vector(normal).normalized() * grosor
        a = [Vector(p) for p in puntos]
        b = [p + nrm for p in a]
        return self.loft([a, b], mat)

    def cinta(self, camino, ancho, normal_fn, grosor, mat, n=16, t0=0.0, t1=1.0, ancho_fn=None):
        """
        Cinta de neón que sigue una curva 3D `camino(t)` con su `normal_fn(t)` (hacia fuera de la superficie):
        ancho a los lados, grosor hacia la normal. Caja cerrada fina.
        """
        bm = self.bm
        anillos = []
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            p = Vector(camino(t))
            tg = (Vector(camino(min(t1, t + 1e-3))) - Vector(camino(max(t0, t - 1e-3)))).normalized()
            nm = Vector(normal_fn(t)).normalized()
            lado = tg.cross(nm).normalized()
            w = (ancho_fn(t) if ancho_fn else ancho) / 2
            anillos.append([bm.verts.new(p - lado * w), bm.verts.new(p + lado * w),
                            bm.verts.new(p + lado * w + nm * grosor), bm.verts.new(p - lado * w + nm * grosor)])
        caras = []
        for a, b in zip(anillos, anillos[1:]):
            for k in range(4):
                j = (k + 1) % 4
                caras.append(bm.faces.new((a[k], a[j], b[j], b[k])))
        caras.append(bm.faces.new(list(reversed(anillos[0]))))
        caras.append(bm.faces.new(anillos[-1]))
        im = self.m(mat)
        for f in caras:
            f.material_index = im
        return {v for a in anillos for v in a}

    def banda(self, camino, plano_n, ancho, grosor, mat, n=16, t0=0.0, t1=1.0, ancho_fn=None, grosor_fn=None):
        """
        Banda que sigue una curva 3D con el grosor dentro del plano de la curva y el ancho a lo largo de `plano_n`
        (guardas de gatillo, guardas de nudillos, arcos). Sección rectangular centrada en la curva.
        """
        bm = self.bm
        P = Vector(plano_n).normalized()
        anillos = []
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            p = Vector(camino(t))
            tg = (Vector(camino(min(t1, t + 1e-3))) - Vector(camino(max(t0, t - 1e-3)))).normalized()
            nm = P.cross(tg).normalized()
            w = (ancho_fn(t) if ancho_fn else ancho) / 2
            g = (grosor_fn(t) if grosor_fn else grosor) / 2
            anillos.append([bm.verts.new(p - P * w - nm * g), bm.verts.new(p + P * w - nm * g),
                            bm.verts.new(p + P * w + nm * g), bm.verts.new(p - P * w + nm * g)])
        caras = []
        for a, b in zip(anillos, anillos[1:]):
            for k in range(4):
                j = (k + 1) % 4
                caras.append(bm.faces.new((a[k], a[j], b[j], b[k])))
        caras.append(bm.faces.new(list(reversed(anillos[0]))))
        caras.append(bm.faces.new(anillos[-1]))
        im = self.m(mat)
        for f in caras:
            f.material_index = im
        return {v for a in anillos for v in a}

    def tubo_curvo(self, camino, radio, mat, n=16, lados=8, t0=0.0, t1=1.0, radio_fn=None, punta=False):
        """Tubo macizo que sigue una curva 3D (conductos, espinas, garras). Con `punta` acaba en vértice."""
        bm = self.bm
        anillos = []
        ref = Vector((0.0, 0.0, 1.0))
        for i in range(n + 1):
            t = t0 + (t1 - t0) * i / n
            p = Vector(camino(t))
            tg = (Vector(camino(min(t1, t + 1e-3))) - Vector(camino(max(t0, t - 1e-3)))).normalized()
            if abs(tg.dot(ref)) > 0.95:
                ref = Vector((1.0, 0.0, 0.0))
            a1 = tg.cross(ref).normalized()
            a2 = tg.cross(a1).normalized()
            r = radio_fn(t) if radio_fn else radio
            if punta and i == n:
                anillos.append([bm.verts.new(p)])
                break
            anillos.append([bm.verts.new(p + (a1 * math.cos(k * math.tau / lados) +
                                              a2 * math.sin(k * math.tau / lados)) * r) for k in range(lados)])
        caras = []
        for a, b in zip(anillos, anillos[1:]):
            for k in range(lados):
                j = (k + 1) % lados
                if len(b) == 1:
                    caras.append(bm.faces.new((a[k], a[j], b[0])))
                else:
                    caras.append(bm.faces.new((a[k], a[j], b[j], b[k])))
        caras.append(bm.faces.new(list(reversed(anillos[0]))))
        if not punta:
            caras.append(bm.faces.new(anillos[-1]))
        im = self.m(mat)
        for f in caras:
            f.material_index = im
        return {v for a in anillos for v in a}

    def roca(self, centro, tam, mat, rnd, sub=1, aplastar=(1, 1, 1)):
        """Trozo de roca irregular: icosfera deformada con ruido (aristas vivas)."""
        from mathutils import noise as nz
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=1.0)
        sem = Vector((rnd.uniform(0, 99), rnd.uniform(0, 99), rnd.uniform(0, 99)))
        for v in res["verts"]:
            d = v.co.copy()
            k = 1 + 0.35 * nz.noise(d * 1.7 + sem) + rnd.uniform(-0.08, 0.08)
            v.co = Vector(centro) + Vector((d.x * aplastar[0], d.y * aplastar[1], d.z * aplastar[2])) * tam * k
        return self._pintar(set(res["verts"]), mat)

    def fragmento(self, centro, tam, mat, giro=None, rnd=None, lados=3):
        """Esquirla: bipirámide de `lados` lados (cristal, fragmento orbital, triángulo del vacío)."""
        bm = self.bm
        rot = giro or Matrix.Identity(3)
        c0 = Vector(centro)
        anillo = []
        for i in range(lados):
            a = math.tau * i / lados + (rnd.uniform(-0.3, 0.3) if rnd else 0)
            r = tam * 0.35 * (1 + (rnd.uniform(-0.2, 0.2) if rnd else 0))
            anillo.append(bm.verts.new(c0 + rot @ Vector((math.cos(a) * r, math.sin(a) * r, 0))))
        arriba = bm.verts.new(c0 + rot @ Vector((0, 0, tam * 0.6)))
        abajo = bm.verts.new(c0 + rot @ Vector((0, 0, -tam * 0.4)))
        caras = []
        for i in range(lados):
            j = (i + 1) % lados
            caras.append(bm.faces.new((anillo[i], anillo[j], arriba)))
            caras.append(bm.faces.new((anillo[j], anillo[i], abajo)))
        im = self.m(mat)
        for f in caras:
            f.material_index = im
        return set(anillo + [arriba, abajo])

    def objeto(self):
        # A diferencia de kit.Pieza, los materiales llevan patrón de relieve.
        bmesh.ops.remove_doubles(self.bm, verts=self.bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(self.bm, faces=self.bm.faces)
        ngons = [f for f in self.bm.faces if len(f.verts) > 4]
        if ngons:
            bmesh.ops.triangulate(self.bm, faces=ngons)
        mats = [material_arma(f"{self.nombre}_{n}", self.paleta[n]) for n in self.mats]
        return c.objeto_desde_bmesh(self.nombre, self.bm, mats)


# --------------------------------------------------------------------------------------------------------------
# El arma: piezas, horneado, exportación y render
# --------------------------------------------------------------------------------------------------------------


class Arma:
    """
    Acumula las piezas de un arma. Cada pieza es una PiezaArma con un rol:
      "tex"   pieza con textura (entra en el atlas),
      "neon"  pieza Neon (sin textura, color del neón del arma),
      "cristal" pieza translúcida sin textura (Glass en Studio).
    """

    def __init__(self, nombre, archivo, rareza, paleta, titulo=""):
        self.nombre = nombre
        self.archivo = archivo
        self.rareza = rareza
        self.titulo = titulo or nombre
        self.paleta = paleta
        self.piezas = []  # (PiezaArma, rol, datos_studio)
        self.agarres = {}  # nombre -> (posición studs, dirección del eje Y)
        self.notas = []

    def pieza(self, sufijo, rol="tex", studio=None):
        p = PiezaArma(f"{self.nombre}_{sufijo}", self.paleta)
        self.piezas.append((p, rol, studio or {}))
        return p

    def agarre(self, nombre, pos, eje_y):
        self.agarres[nombre] = (Vector(pos), Vector(eje_y).normalized())


def _ocultar_menos(visibles):
    estado = {}
    for o in bpy.context.scene.objects:
        if o.type == "MESH":
            estado[o] = o.hide_render
            o.hide_render = o not in visibles
    return estado


def _imagen(nombre, tam, color=True, alfa=False):
    img = bpy.data.images.new(nombre, tam, tam, alpha=alfa, float_buffer=False)
    img.colorspace_settings.name = "sRGB" if color else "Non-Color"
    if not color:
        img.generated_color = (0, 0, 0, 1)
    return img


def _destino(obj, img):
    for slot in obj.material_slots:
        nt = slot.material.node_tree
        n = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
        n.name = "destino"
        n.image = img
        nt.nodes.active = n


def _bake(obj, tipo, alta=None, extrusion=0.0, **kw):
    bpy.ops.object.select_all(action="DESELECT")
    if alta:
        alta.select_set(True)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.bake(type=tipo, use_selected_to_active=alta is not None, cage_extrusion=extrusion, margin=6,
                        **kw)


def _emitir_valor(obj, clave):
    """Pone en la emisión de cada material su valor `clave` (metal, alfa) para hornearlo con EMIT."""
    guardado = []
    for slot in obj.material_slots:
        m = slot.material
        b = m.node_tree.nodes["Principled BSDF"]
        ec, es = b.inputs["Emission Color"], b.inputs["Emission Strength"]
        enlaces = [(lk.from_socket, lk.to_socket) for lk in m.node_tree.links if lk.to_socket in (ec, es)]
        for lk in [lk for lk in m.node_tree.links if lk.to_socket in (ec, es)]:
            m.node_tree.links.remove(lk)
        guardado.append((m, tuple(ec.default_value), es.default_value, enlaces))
        es.default_value = 1.0
        if clave == "color":  # el color base tal cual (DIFFUSE da negro en los metales)
            bc = b.inputs["Base Color"]
            if bc.is_linked:
                m.node_tree.links.new(bc.links[0].from_socket, ec)
            else:
                ec.default_value = tuple(bc.default_value)
            continue
        v = m.get(clave, 0.0)
        ec.default_value = (v, v, v, 1)
    return guardado


def _restaurar(guardado):
    for m, col, fuerza, enlaces in guardado:
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Emission Color"].default_value = col
        b.inputs["Emission Strength"].default_value = fuerza
        for lk in [lk for lk in m.node_tree.links if lk.to_socket == b.inputs["Emission Color"]]:
            m.node_tree.links.remove(lk)
        for a, d in enlaces:
            m.node_tree.links.new(a, d)


def _pixeles(img):
    w, h = img.size
    return np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)


def _guardar(img, ruta):
    img.filepath_raw = ruta
    img.file_format = "PNG"
    img.save()


def hornear_atlas(arma, objs_tex, objs_neon, carpeta, tam, rapido):
    """Hornea los 5 mapas del arma en un atlas compartido y deja a cada pieza con el material final."""
    scn = bpy.context.scene
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    tex = os.path.join(carpeta, "texturas")
    os.makedirs(tex, exist_ok=True)
    pre = os.path.join(tex, arma.nombre)

    # 1) UV de todas las piezas con textura en el mismo espacio (edición multiobjeto).
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs_tex:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs_tex[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.006, scale_to_bounds=False)
    bpy.ops.uv.pack_islands(margin=0.006, rotate=True)
    bpy.ops.object.mode_set(mode="OBJECT")

    # 2) Copia unida de las piezas (con sus materiales y UV) sobre la que se hornea todo.
    copias = []
    for o in objs_tex:
        d = o.copy()
        d.data = o.data.copy()
        scn.collection.objects.link(d)
        copias.append(d)
    bpy.ops.object.select_all(action="DESELECT")
    for d in copias:
        d.select_set(True)
    bpy.context.view_layer.objects.active = copias[0]
    bpy.ops.object.join()
    atlas = bpy.context.active_object
    atlas.name = f"{arma.nombre}_atlas"
    for o in objs_tex + objs_neon:
        o.hide_render = True
    estado = _ocultar_menos([atlas])

    # Color (sin luz).
    scn.cycles.samples = 1
    img_c = _imagen(f"{arma.nombre}_color", tam, alfa=True)
    _destino(atlas, img_c)
    g = _emitir_valor(atlas, "color")
    _bake(atlas, "EMIT")
    _restaurar(g)
    # Oclusión ambiental (sombras de la guarda sobre la hoja, huecos de los cañones...).
    scn.cycles.samples = 8 if rapido else 64
    img_ao = _imagen(f"{arma.nombre}_ao", tam, color=False)
    _destino(atlas, img_ao)
    scn.world.light_settings.distance = 0.25 * E
    _bake(atlas, "AO")
    c._multiplicar_ao(img_c, img_ao, fuerza=0.55)
    scn.cycles.samples = 1
    # Alfa (piezas translúcidas).
    if any(m.get("alfa", 1.0) < 1.0 for m in (s.material for s in atlas.material_slots)):
        img_a = _imagen(f"{arma.nombre}_alfa", tam, color=False)
        _destino(atlas, img_a)
        g = _emitir_valor(atlas, "alfa")
        _bake(atlas, "EMIT")
        _restaurar(g)
        px = _pixeles(img_c)
        px[..., 3] = _pixeles(img_a)[..., 0]
        img_c.pixels.foreach_set(px.ravel())
        arma.notas.append("color con alfa: SurfaceAppearance.AlphaMode = Transparency")
    else:
        px = _pixeles(img_c)
        px[..., 3] = 1.0
        img_c.pixels.foreach_set(px.ravel())
    _guardar(img_c, f"{pre}_color.png")

    # Rugosidad.
    img_r = _imagen(f"{arma.nombre}_roughness", tam, color=False)
    _destino(atlas, img_r)
    _bake(atlas, "ROUGHNESS")
    _guardar(img_r, f"{pre}_roughness.png")

    # Metalicidad.
    img_m = _imagen(f"{arma.nombre}_metalness", tam, color=False)
    _destino(atlas, img_m)
    g = _emitir_valor(atlas, "metal")
    _bake(atlas, "EMIT")
    _restaurar(g)
    _guardar(img_m, f"{pre}_metalness.png")

    # Normales (el relieve de los patrones).
    img_n = _imagen(f"{arma.nombre}_normal", tam, color=False)
    _destino(atlas, img_n)
    _bake(atlas, "NORMAL", normal_space="TANGENT")
    _guardar(img_n, f"{pre}_normal.png")

    # Máscara de emisión: rayos desde la superficie hacia las piezas de neón que flotan encima.
    img_e = _imagen(f"{arma.nombre}_emision", tam, color=False)
    if objs_neon:
        alta = atlas.copy()
        alta.data = atlas.data.copy()
        scn.collection.objects.link(alta)
        negro = c.material("mascara_negro", (0, 0, 0), emision=(0, 0, 0), fuerza_emision=1.0)
        blanco = c.material("mascara_blanco", (1, 1, 1), emision=(1, 1, 1), fuerza_emision=1.0)
        alta.data.materials.clear()
        alta.data.materials.append(negro)
        neones = []
        for o in objs_neon:
            d = o.copy()
            d.data = o.data.copy()
            d.data.materials.clear()
            d.data.materials.append(blanco)
            scn.collection.objects.link(d)
            neones.append(d)
        bpy.ops.object.select_all(action="DESELECT")
        for d in [alta] + neones:
            d.select_set(True)
        bpy.context.view_layer.objects.active = alta
        bpy.ops.object.join()
        for p in alta.data.polygons:
            p.material_index = p.material_index  # (los materiales se conservan al unir)
        alta.hide_render = False
        _destino(atlas, img_e)
        _bake(atlas, "EMIT", alta=alta, extrusion=0.06 * E, max_ray_distance=0.12 * E)
        bpy.data.objects.remove(alta)
    _guardar(img_e, f"{pre}_emision.png")

    for o, h in estado.items():
        o.hide_render = h
    bpy.data.objects.remove(atlas)
    for o in objs_tex + objs_neon:
        o.hide_render = False

    # 3) Material final de cada pieza: las 4 texturas (lo que verá Roblox en la SurfaceAppearance).
    translucido = "AlphaMode" in " ".join(arma.notas)
    mat = bpy.data.materials.new(f"{arma.nombre}_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexImage")
    tc.image = img_c
    nt.links.new(tc.outputs["Color"], b.inputs["Base Color"])
    if translucido:
        nt.links.new(tc.outputs["Alpha"], b.inputs["Alpha"])
    for img, entrada in ((img_r, "Roughness"), (img_m, "Metallic")):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = img
        nt.links.new(t.outputs["Color"], b.inputs[entrada])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img_n
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    for o in objs_tex:
        o.data.materials.clear()
        o.data.materials.append(mat)
        for p in o.data.polygons:
            p.material_index = 0
    for img in (img_ao,):
        bpy.data.images.remove(img)
    return mat


def material_plano(nombre, d):
    """Material de una pieza sin textura (neón, cristal): un solo material, el primero de la pieza."""
    return material_arma(nombre, d)


def construir(arma, carpeta, rapido):
    """Crea los objetos, hornea el atlas y añade los Empty de agarre. Devuelve (objetos, empties, info)."""
    objs_tex, objs_neon, todos, info_piezas = [], [], [], []
    for p, rol, studio in arma.piezas:
        if p.vacia():
            continue
        o = p.objeto()
        if rol == "tex" and studio.get("bisel"):
            kit.biselar(o, studio["bisel"], studio.get("angulo_bisel", 40))
        c.sombreado_suave(o, angulo=studio.get("suavizado", 35))
        todos.append(o)
        (objs_tex if rol == "tex" else objs_neon if rol == "neon" else []).append(o)
        info_piezas.append((o, rol, studio))
    tam = 256 if rapido else RAREZAS[arma.rareza]["tex"]
    hornear_atlas(arma, objs_tex, objs_neon, carpeta, tam, rapido)

    empties = []
    for nombre, (pos, eje_y) in arma.agarres.items():
        e = bpy.data.objects.new(nombre, None)
        e.empty_display_type = "ARROWS"
        e.empty_display_size = 0.3 * E
        q = eje_y.to_track_quat("Y", "Z")
        e.matrix_world = Matrix.Translation(pos * E) @ q.to_matrix().to_4x4()
        bpy.context.scene.collection.objects.link(e)
        empties.append(e)
    return todos, empties, info_piezas


def a_roblox(v):
    """Vector de Blender (studs) a ejes de Roblox: la exportación manda (x, y, z) -> (-x, z, y)."""
    return Vector((-v.x, v.z, v.y))


def centro_obj(o):
    mn, mx = c.caja_limite([o])
    return (mn + mx) / 2 / E


def exportar(arma, objetos, empties, info_piezas, carpeta):
    ruta = os.path.join(carpeta, arma.archivo)
    bpy.ops.object.select_all(action="DESELECT")
    for o in objetos + empties:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objetos[0]
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH", "EMPTY"}, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS", bake_space_transform=False, axis_forward="Z", axis_up="Y",
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False, bake_anim=False,
        embed_textures=True, path_mode="COPY")
    # JSON con lo que hace falta en Studio: piezas, materiales y agarres (en ejes de Roblox).
    rz = RAREZAS[arma.rareza]
    principal = next((o for o, rol, s in info_piezas if s.get("raiz")), objetos[0])
    cp = centro_obj(principal)
    datos = {
        "arma": arma.titulo, "archivo": arma.archivo, "rareza": rz["nombre"], "colorBorde": rz["borde"],
        "triangulos": sum(c.triangulos(o) for o in objetos), "trisMax": rz["tris"],
        "texturas": {k: f"texturas/{arma.nombre}_{k}.png" for k in ("color", "normal", "roughness", "metalness",
                                                                    "emision")},
        "piezaRaiz": principal.name,
        "piezas": [],
        "agarres": {},
        "notas": arma.notas,
    }
    for o, rol, s in info_piezas:
        d = {"nombre": o.name, "rol": rol, "triangulos": c.triangulos(o),
             "centro": [round(x, 4) for x in a_roblox(centro_obj(o) - cp)]}
        if rol == "neon":
            d.update({"Material": "Neon", "Color": s.get("color", CIAN)})
        elif rol == "cristal":
            d.update({"Material": "Glass", "Color": s["color"], "Transparency": s.get("transparencia", 0.4)})
        else:
            d["SurfaceAppearance"] = True
        if s.get("nota"):
            d["nota"] = s["nota"]
        datos["piezas"].append(d)
    for nombre, (pos, eje_y) in arma.agarres.items():
        datos["agarres"][nombre] = {"posicion": [round(x, 4) for x in a_roblox(pos - cp)],
                                    "ejeY": [round(x, 4) for x in a_roblox(eje_y)]}
    with open(os.path.splitext(ruta)[0] + ".json", "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    escribir_montaje(arma, datos, carpeta)
    return datos


def a_lua(v, sangria=1):
    """Valor de Python (del JSON) a literal de Luau."""
    tab = "\t" * sangria
    if isinstance(v, dict):
        filas = [f"{tab}{k} = {a_lua(x, sangria + 1)}," if k.isidentifier() else
                 f'{tab}["{k}"] = {a_lua(x, sangria + 1)},' for k, x in v.items()]
        return "{\n" + "\n".join(filas) + "\n" + "\t" * (sangria - 1) + "}"
    if isinstance(v, list):
        if all(isinstance(x, (int, float)) for x in v):
            return "{ " + ", ".join(a_lua(x) for x in v) + " }"
        return "{\n" + "\n".join(f"{tab}{a_lua(x, sangria + 1)}," for x in v) + "\n" + "\t" * (sangria - 1) + "}"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(round(v, 4)) if isinstance(v, float) else str(v)
    return '"' + str(v).replace('"', '\\"') + '"'


def escribir_montaje(arma, datos, carpeta):
    """Script de la barra de comandos que monta el arma como Tool (desde plantilla_montar_arma.luau)."""
    plantilla = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plantilla_montar_arma.luau"),
                     encoding="utf-8").read()
    translucido = any("AlphaMode" in n for n in arma.notas)
    alfa = "sa.AlphaMode = Enum.AlphaMode.Transparency" if translucido else "-- (sin piezas translúcidas)"
    txt = (plantilla.replace("{{ARMA}}", arma.titulo).replace("{{ARCHIVO}}", arma.archivo)
           .replace("{{NOMBRE}}", arma.nombre).replace("{{ALFA}}", alfa).replace("{{DATOS}}", a_lua(datos)))
    os.makedirs(os.path.join(carpeta, "montar"), exist_ok=True)
    with open(os.path.join(carpeta, "montar", arma.archivo[:-4] + ".luau"), "w", encoding="utf-8") as f:
        f.write(txt)


# ---- render ------------------------------------------------------------------------------------------------

VISTAS_TURNAROUND = [("Frente", 0, 4), ("Perfil derecho", 90, 4), ("Trasera", 180, 4), ("Perfil izquierdo", -90, 4)]


def estudio_gris():
    """Estudio de 3 puntos con fondo gris neutro (clave, relleno y contra; el rebote es para las vistas bajas)."""
    c.preparar_estudio(tono_fondo=(0.2, 0.2, 0.205), suelo=False, luz_clave=300, mundo=1.25)


def brazo_r6(arma):
    """
    Brazo R6 de referencia (1 × 2 × 1 studs, color piel) con el extremo de la mano en el Handle y el brazo hacia
    atrás (+Y), como cuando el personaje sostiene el arma: sirve para comprobar las proporciones de un vistazo.
    """
    pos, _ = arma.agarres["Handle"]
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(1, 2, 1), verts=bm.verts)
    bmesh.ops.translate(bm, vec=pos + Vector((0, 0.85, 0)), verts=bm.verts)
    # Translúcido: en Roblox el grip queda dentro del brazo, y así se ve el arma.
    o = c.objeto_desde_bmesh("Brazo_R6_ref", bm, [c.material("brazo_r6", c.srgb("#C9A27E"), rugosidad=0.8,
                                                             alfa=0.45)])
    o.hide_render = True
    return o


def render_turnaround(arma, objetos, carpeta, ronda, rapido, notas_ronda=""):
    tmp = os.path.join(carpeta, "_render_tmp")
    tam = 300 if rapido else 420
    muestras = 12 if rapido else 40
    vistas = VISTAS_TURNAROUND + [("3/4", -35, 22)]
    fila = c.renderizar_vistas(objetos, tmp, vistas, tam=tam, muestras=muestras, margen=1.02, lente=70,
                               prefijo=arma.nombre + "_")
    # Comparación de escala con un brazo R6.
    brazo = brazo_r6(arma)
    brazo.hide_render = False
    fila += [(n.replace("3/4", "Escala R6 (brazo 1×2×1)"), r) for n, r in
             c.renderizar_vistas(objetos + [brazo], tmp, [("3/4", -60, 15)], tam=tam, muestras=muestras,
                                 con_malla=False, margen=1.0, lente=70, prefijo=arma.nombre + "_r6_")]
    bpy.data.objects.remove(brazo)
    rz = RAREZAS[arma.rareza]
    tris = sum(c.triangulos(o) for o in objetos)
    mn, mx = c.caja_limite(objetos)
    dim = (mx - mn) / E
    titulo = f"{arma.titulo} ({rz['nombre']}) — ronda {ronda}"
    notas = [f"{arma.archivo} · {tris} triángulos (máx. {rz['tris']}) · {dim.x:.2f} × {dim.y:.2f} × {dim.z:.2f} studs"
             f" · {len(objetos)} piezas"]
    if notas_ronda:
        notas.append(notas_ronda)
    hoja = os.path.join(carpeta, "rondas", f"{arma.archivo[:-4]}_ronda_{ronda}.png")
    os.makedirs(os.path.dirname(hoja), exist_ok=True)
    c.montar_hoja([fila], hoja, titulo, notas=notas, columnas=4)
    return hoja, tris
