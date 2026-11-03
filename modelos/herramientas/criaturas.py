"""
Dos criaturas pequeñas para escanear:

  Brincador lanudo (planeta humano, pacífica): bola de lana color crema con franjas cian en el lomo, orejas
      largas y caídas, patitas cortas, cola de pompón y ojos grandes. Da ganas de acercarse a escanearla.
  Acechador del abismo (planeta de los monstruos, agresiva): bicho de seis patas de araña, caparazón negro
      violáceo con púas de hueso, mandíbulas en gancho y cuatro ojos morados que brillan.

Cada criatura son varias piezas para poder animarlas con Motor6D (andar, saltar, mover orejas o mandíbulas):
  <Criatura>_Cuerpo      cuerpo y cabeza (la pieza raíz)
  <Criatura>_Pata1..N    patas (pivote donde se unen al cuerpo)
  <Criatura>_OrejaIzq/Der, _Cola, _MandibulaIzq/Der
  <Criatura>_Ojos        ojos (Brincador: SmoothPlastic negro con Reflectance; Acechador: Neon morado)

<Criatura>.json lleva el pivote de cada pieza y su centro, y montar_<criatura>.luau (generado) monta el modelo en
Studio: Motor6D, AnimationController, la etiqueta "Escaneable" y el atributo EspecieId para el escáner.

Uso:
    python modelos/herramientas/criaturas.py --salida modelos/criaturas [--ronda N] [--rapido]
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Vector, noise  # noqa: E402

import comun as c  # noqa: E402
import kit  # noqa: E402
import rocas_minerales as rm  # noqa: E402
from ciudad_humana import kit_a_roblox  # noqa: E402
from monstruo import malla_metabolas  # noqa: E402

E = c.ESTUDIO

# --------------------------------------------------------------------------------------------------------------
# Piezas y pintura
# --------------------------------------------------------------------------------------------------------------


def capsula(a, b, r, rigidez=2.0):
    """Elemento de metabola en cápsula entre dos puntos (formato de monstruo.malla_metabolas)."""
    a, b = Vector(a), Vector(b)
    d = b - a
    # malla_metabolas gira con ángulos de Euler (grados): calculamos los que llevan el eje X a la dirección d.
    q = d.normalized().to_track_quat("X", "Z")
    eul = q.to_euler()
    return ("CAPSULE", tuple((a + b) / 2), (r, d.length / 2), tuple(math.degrees(x) for x in eul), rigidez)


def pieza(nombre, elementos, pintar, rnd, tris, carpeta, rapido, tam_tex=512, relieve=0.03, resolucion=0.03,
          suavizado=0):
    alta = malla_metabolas(f"{nombre}_alta", elementos, resolucion=resolucion if not rapido else resolucion * 1.6)
    if suavizado:  # superficie de peluche: sin los bultos de las metabolas
        mod = alta.modifiers.new("suave", "SMOOTH")
        mod.factor = 0.8
        mod.iterations = suavizado * 3
        c.aplicar_modificadores(alta)
    sem = Vector((rnd.uniform(0, 50), rnd.uniform(0, 50), rnd.uniform(0, 50)))
    bm = bmesh.new()
    bm.from_mesh(alta.data)
    bm.normal_update()
    cols = []
    for v in bm.verts:
        p = v.co / E
        v.co += v.normal * relieve * noise.fractal(p * 4.0 + sem, 0.6, 2.0, 3) * E
        cols.append(pintar(p, v.normal, sem))
    capa = bm.loops.layers.color.new("Col")
    for f in bm.faces:
        for lo in f.loops:
            q = cols[lo.vert.index]
            lo[capa] = (q.x, q.y, q.z, 1.0)
    bm.to_mesh(alta.data)
    bm.free()
    mat = bpy.data.materials.new(f"{nombre}_vc")
    mat.use_nodes = True
    nt = mat.node_tree
    at = nt.nodes.new("ShaderNodeVertexColor")
    at.layer_name = "Col"
    nt.links.new(at.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"])
    nt.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.7
    alta.data.materials.append(mat)
    baja = rm.version_baja(alta, nombre, tris)
    c.sombreado_suave(baja, angulo=70)
    c.desplegar_uv(baja, margen=0.015)
    c.hornear(baja, alta, tam=128 if rapido else tam_tex,
              ruta_color=os.path.join(carpeta, "texturas", f"{nombre}_color.png"),
              ruta_normal=os.path.join(carpeta, "texturas", f"{nombre}_normal.png"),
              extrusion=0.03, muestras=8 if rapido else 24, distancia_oclusion=0.15)
    alta.hide_render = True
    alta.hide_set(True)
    return baja


def esferas(nombre, lista, color, rugosidad=0.1, emision=0.0, metal=0.0):
    bm = bmesh.new()
    for centro, r in lista:
        res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=r)
        bmesh.ops.translate(bm, vec=centro, verts=res["verts"])
    col = c.srgb(color)
    m = c.material(f"{nombre}_mat", col, rugosidad=rugosidad, metal=metal,
                   emision=col if emision else None, fuerza_emision=emision)
    obj = c.objeto_desde_bmesh(nombre, bm, [m])
    for p in obj.data.polygons:
        p.use_smooth = True
    return obj


def V(h):
    return Vector(c.srgb(h))


def suave(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


# --------------------------------------------------------------------------------------------------------------
# Brincador lanudo
# --------------------------------------------------------------------------------------------------------------

BRINCADOR = dict(crema="#F2E4C9", panza="#F7C9A8", franja="#2BA9A8", pata="#8C6E58", oreja_dentro="#F29A9A",
                 ojo="#141018")


def brincador(carpeta, rapido):
    rnd = random.Random(2)
    k = BRINCADOR
    n = "Brincador"

    def pintar_cuerpo(p, nrm, sem):
        lana = 0.5 + 0.5 * noise.noise(p * 14.0 + sem)
        col = V(k["crema"]) * (0.88 + 0.16 * lana)
        # Panza y hocico más rosados.
        col = col.lerp(V(k["panza"]), suave((-nrm.z - 0.1) * 2.0) * 0.8)
        col = col.lerp(V(k["panza"]), suave((-p.y - 1.2) * 4.0) * 0.6)
        # Tres franjas cian en el lomo, de lado a lado.
        if nrm.z > 0.2 and p.y > -0.6:
            banda = math.sin((p.y + 0.15) * 7.5)
            col = col.lerp(V(k["franja"]), suave((banda - 0.5) * 8.0) * suave((nrm.z - 0.25) * 4))
        return col

    def pintar_pata(p, nrm, sem):
        return V(k["crema"]).lerp(V(k["pata"]), suave((0.45 - p.z) * 3.0))

    def pintar_oreja(p, nrm, sem):
        dentro = suave((-nrm.y - 0.5) * 3.0)  # solo la cara que mira hacia delante
        return V(k["crema"]).lerp(V(k["oreja_dentro"]), dentro * 0.85).lerp(V(k["franja"]), suave((1.9 - p.z) * 4))

    cuerpo_el = [
        ("ELLIPSOID", (0, 0.25, 1.25), (0.85, 1.0, 0.78), (0, 0, 0), 2.0),
        ("ELLIPSOID", (0, -0.85, 1.78), (0.76, 0.66, 0.66), (0, 0, 0), 2.0),  # cabeza grande: más tierno
        ("BALL", (0.38, -1.12, 1.55), (0.27,), (0, 0, 0), 2.0),
        ("BALL", (-0.38, -1.12, 1.55), (0.27,), (0, 0, 0), 2.0),
        ("ELLIPSOID", (0, -1.33, 1.58), (0.26, 0.18, 0.18), (0, 0, 0), 2.0),
    ]
    for i in range(9):  # mechones de lana sobre el lomo
        a = i * 2.4
        cuerpo_el.append(("BALL", (math.cos(a) * 0.5, 0.35 + math.sin(a) * 0.6, 1.8 + 0.1 * math.sin(a * 3)),
                          (0.2,), (0, 0, 0), 1.1))
    piezas = [pieza(f"{n}_Cuerpo", cuerpo_el, pintar_cuerpo, rnd, 1100, carpeta, rapido, relieve=0.008,
                    suavizado=3)]
    pivotes = {}
    # Orejas: largas, caídas hacia atrás y hacia fuera.
    for nombre, sx in (("OrejaIzq", 1), ("OrejaDer", -1)):
        # Orejas caídas: suben un poco y se doblan hacia fuera y abajo, como las de un conejo belier.
        base = Vector((sx * 0.38, -0.65, 2.2))
        codo = base + Vector((sx * 0.35, 0.1, 0.35))
        punta = codo + Vector((sx * 0.45, 0.15, -0.75))
        el = [capsula(base, codo, 0.16), capsula(codo, punta, 0.15),
              ("ELLIPSOID", tuple(codo.lerp(punta, 0.5)), (0.26, 0.1, 0.42), (0, sx * -25, 0), 2.0)]
        piezas.append(pieza(f"{n}_{nombre}", el, pintar_oreja, rnd, 260, carpeta, rapido, tam_tex=256, relieve=0.02))
        pivotes[f"{n}_{nombre}"] = base
    # Patas.
    for i, (x, y) in enumerate(((0.5, -0.45), (-0.5, -0.45), (0.5, 0.85), (-0.5, 0.85))):
        top = Vector((x, y, 0.8))
        pie = Vector((x * 1.08, y - 0.08, 0.18))
        el = [capsula(top, pie, 0.27), ("ELLIPSOID", tuple(pie + Vector((0, -0.1, -0.02))), (0.27, 0.34, 0.17),
                                        (0, 0, 0), 2.0)]
        nombre = f"{n}_Pata{i + 1}"
        piezas.append(pieza(nombre, el, pintar_pata, rnd, 220, carpeta, rapido, tam_tex=256, relieve=0.02))
        pivotes[nombre] = top
    # Cola de pompón.
    cola = [("BALL", (0, 1.28, 1.45), (0.36,), (0, 0, 0), 2.0)] + \
        [("BALL", (math.cos(a) * 0.2, 1.4 + math.sin(a) * 0.1, 1.45 + math.sin(a) * 0.2), (0.18,), (0, 0, 0), 1.6)
         for a in (0, 2.1, 4.2)]
    piezas.append(pieza(f"{n}_Cola", cola, lambda p, nr, s: V(k["crema"]) * 1.05, rnd, 200,
                        carpeta, rapido, tam_tex=256, relieve=0.04))
    pivotes[f"{n}_Cola"] = Vector((0, 1.05, 1.45))
    ojos = esferas(f"{n}_Ojos", [((0.36, -1.38, 1.95), 0.21), ((-0.36, -1.38, 1.95), 0.21)], k["ojo"],
                   rugosidad=0.05)
    piezas.append(ojos)
    pivotes[f"{n}_Ojos"] = None  # soldados al cuerpo
    return piezas, datos_criatura(n, "Criatura_BrincadorLanudo", piezas, pivotes, neon=False)


# --------------------------------------------------------------------------------------------------------------
# Acechador del abismo
# --------------------------------------------------------------------------------------------------------------

ACECHADOR = dict(caparazon="#4A3D58", brillo="#9C76BA", vientre="#4E443C", hueso="#BDB29A", punta="#141016",
                 ojos="#B54DFF")


def acechador(carpeta, rapido):
    rnd = random.Random(8)
    k = ACECHADOR
    n = "Acechador"

    def pintar_cuerpo(p, nrm, sem):
        veta = noise.ridged_multi_fractal(p * 2.5 + sem, 1.0, 2.0, 3, 0.0, 2.0)
        col = V(k["caparazon"]).lerp(V(k["brillo"]), suave((veta - 0.6) * 1.5) * suave(nrm.z * 2))
        col = col.lerp(V(k["vientre"]), suave((-nrm.z - 0.2) * 2.5))
        # Segmentos del abdomen: bandas violetas que lo hacen reconocible (y avisan de que es venenoso).
        if p.y > 0.4 and nrm.z > -0.2:
            banda = math.sin((p.y - 0.4) * 7.0)
            col = col.lerp(V(k["brillo"]) * 1.15, suave((banda - 0.3) * 3.0) * 0.75)
        if p.z > 2.0 or (abs(p.x) > 1.05 and p.y > 0.5):  # púas
            col = col.lerp(V(k["hueso"]), suave((p.z - 2.0) * 3) if p.z > 2.0 else 0.7)
        return col

    def pintar_pata(p, nrm, sem):
        col = V(k["caparazon"]).lerp(V(k["brillo"]), suave(nrm.z * 1.5) * 0.5)
        return col.lerp(V(k["punta"]), suave((0.6 - p.z) * 2.0)).lerp(V(k["hueso"]), suave((p.z - 2.15) * 5) * 0.6)

    def pintar_mandibula(p, nrm, sem):
        return V(k["hueso"]).lerp(V(k["punta"]), suave((-p.y - 2.0) * 3.0))

    cuerpo_el = [
        ("ELLIPSOID", (0, 1.35, 1.55), (0.95, 1.25, 0.72), (-12, 0, 0), 2.0),  # abdomen
        ("ELLIPSOID", (0, -0.15, 1.35), (0.78, 0.85, 0.55), (0, 0, 0), 2.0),  # tórax
        ("ELLIPSOID", (0, -1.25, 1.45), (0.58, 0.55, 0.42), (-15, 0, 0), 2.0),  # cabeza, levantada
        ("ELLIPSOID", (0, -0.75, 1.5), (0.5, 0.4, 0.4), (0, 0, 0), 2.0),  # cuello
    ]
    for i in range(6):  # púas del lomo, inclinadas hacia atrás
        y = -0.6 + i * 0.55
        z = 1.85 + 0.25 * math.sin((i + 1) / 7 * math.pi)
        # Púa en dos tramos (gruesa en la base, afilada en la punta): sin esto parecían dedos.
        medio = Vector((0, y + 0.2, z + 0.45 - 0.04 * i))
        cuerpo_el.append(capsula((0, y, z), medio, 0.15, rigidez=2.5))
        cuerpo_el.append(capsula(medio, (0, y + 0.5, z + 1.0 - 0.08 * i), 0.05, rigidez=2.5))
    for sx in (-1, 1):  # púas laterales del abdomen
        for j in range(2):
            y = 1.0 + j * 0.8
            cuerpo_el.append(capsula((sx * 0.85, y, 1.8), (sx * 1.35, y + 0.35, 2.2), 0.08, rigidez=2.5))
    piezas = [pieza(f"{n}_Cuerpo", cuerpo_el, pintar_cuerpo, rnd, 1400, carpeta, rapido, relieve=0.03)]
    pivotes = {}
    # Patas de araña: coxa hacia arriba y fuera, rodilla alta, y la punta clavada en el suelo.
    for i, (y, abre) in enumerate(((-0.6, -0.5), (0.2, 0.0), (1.0, 0.45))):
        for sx in (1, -1):
            base = Vector((sx * 0.62, y, 1.35))
            rodilla = Vector((sx * 1.75, y + abre * 0.6, 2.45))
            tobillo = Vector((sx * 2.55, y + abre * 1.3, 1.0))
            punta = Vector((sx * 2.75, y + abre * 1.5, 0.0))
            el = [capsula(base, rodilla, 0.15), capsula(rodilla, tobillo, 0.1), capsula(tobillo, punta, 0.06),
                  ("BALL", tuple(rodilla), (0.17,), (0, 0, 0), 2.0)]
            nombre = f"{n}_Pata{len(pivotes) + 1}"
            piezas.append(pieza(nombre, el, pintar_pata, rnd, 280, carpeta, rapido, tam_tex=256, relieve=0.015))
            pivotes[nombre] = base
    # Mandíbulas en gancho.
    for nombre, sx in (("MandibulaIzq", 1), ("MandibulaDer", -1)):
        a = Vector((sx * 0.3, -1.65, 1.2))
        b = Vector((sx * 0.6, -2.3, 1.0))
        cc = Vector((sx * 0.12, -2.85, 0.9))
        el = [capsula(a, b, 0.17), capsula(b, cc, 0.1)]
        piezas.append(pieza(f"{n}_{nombre}", el, pintar_mandibula, rnd, 160, carpeta, rapido, tam_tex=256,
                            relieve=0.01))
        pivotes[f"{n}_{nombre}"] = a
    ojos = esferas(f"{n}_Ojos", [((0.2, -1.72, 1.68), 0.11), ((-0.2, -1.72, 1.68), 0.11),
                                 ((0.42, -1.52, 1.8), 0.08), ((-0.42, -1.52, 1.8), 0.08)],
                   k["ojos"], rugosidad=0.3, emision=3.0)
    piezas.append(ojos)
    pivotes[f"{n}_Ojos"] = None
    return piezas, datos_criatura(n, "Criatura_AcechadorAbismo", piezas, pivotes, neon=True)


# --------------------------------------------------------------------------------------------------------------
# Datos para Studio
# --------------------------------------------------------------------------------------------------------------


def datos_criatura(nombre, especie, piezas, pivotes, neon):
    def extra(desp):
        centros = {}
        for o in piezas:
            mn, mx = c.caja_limite([o])
            centros[o.name] = kit_a_roblox((mn + mx) / 2 / E)
        piv = {k: kit_a_roblox(v + desp) for k, v in pivotes.items() if v is not None}
        datos = {"nota": "studs, ejes de Roblox, respecto al centro de la base", "EspecieId": especie,
                 "Raiz": f"{nombre}_Cuerpo", "Pivotes": piv, "Centros": centros,
                 "Soldadas": [k for k, v in pivotes.items() if v is None],
                 "OjosNeon": neon}
        escribir_montar(nombre, datos)
        return datos
    return extra


_CARPETA = {}


def escribir_montar(nombre, datos):
    def v3(p):
        return f"Vector3.new({p[0]}, {p[1]}, {p[2]})"

    plantilla = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "plantilla_montar_criatura.luau"),
                     encoding="utf-8").read()
    texto = (plantilla.replace("--NOMBRE--", nombre)
             .replace("--ESPECIE--", datos["EspecieId"])
             .replace("--RAIZ--", datos["Raiz"])
             .replace("--PIVOTES--", "\n\t".join(f'["{k}"] = {v3(v)},' for k, v in datos["Pivotes"].items()))
             .replace("--CENTROS--", "\n\t".join(f'["{k}"] = {v3(v)},' for k, v in datos["Centros"].items()))
             .replace("--SOLDADAS--", ", ".join(f'"{s}"' for s in datos["Soldadas"]))
             .replace("--OJOS_NEON--", "true" if datos["OjosNeon"] else "false"))
    with open(os.path.join(_CARPETA["salida"], f"montar_{nombre.lower()}.luau"), "w", encoding="utf-8") as f:
        f.write(texto)


ITEMS = [
    dict(archivo="Brincador", titulo="Brincador lanudo\n(pacífico, humanos)", construir=brincador),
    dict(archivo="Acechador", titulo="Acechador del abismo\n(agresivo, monstruos)", construir=acechador),
]

if __name__ == "__main__":
    a = kit.argumentos()
    _CARPETA["salida"] = os.path.abspath(a.salida)
    os.makedirs(_CARPETA["salida"], exist_ok=True)
    vistas = [("Frente", 0, 10), ("3/4", -40, 22), ("Lateral", -90, 6), ("3/4 trasera", 140, 25),
              ("Arriba", 15, 70), ("Cara", -20, 4)]
    kit.ejecutar_lote(ITEMS, a.salida, "Criaturas escaneables", a.ronda, a.rapido, vistas=vistas, solo=a.solo,
                      nota="Piezas separadas para Motor6D · color + normales horneados · ojos aparte",
                      margen=0.95)
