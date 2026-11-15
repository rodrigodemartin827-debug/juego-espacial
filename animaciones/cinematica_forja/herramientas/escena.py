"""
Escena de la cinemática de la forja: piezas de la forja, compuerta del horno, utilería (tenazas, martillo, pieza que
se forja), maniquí R6, luces, partículas (chispas, ascuas, vapor, burbujas), mundo y composición.

Unidades: 1 unidad de Blender = 1 stud, como en modelos/forja. Z arriba. El suelo de la forja está a ALTO_SUELO.
La forja se monta con los mismos datos que modelos/forja/herramientas/piezas.py (MONTAJE), así que todo lo que sale
de aquí está en el mismo sistema que modelos/forja/datos/forja_montaje.json.
"""

import math
import os

import bmesh
import bpy
from mathutils import Matrix, Vector

RAIZ_REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
FORJA = os.path.join(RAIZ_REPO, "modelos", "forja")

ALTO_SUELO = 0.62  # cara de arriba del adoquín (piezas.ALTO_SUELO)
MONTAJE = {  # (x, y, giro en grados) - copia de piezas.MONTAJE
    "suelo": (0.0, 0.0, 0.0),
    "horno": (-2.6, 4.2, 0.0),
    "yunque": (-1.9, -4.1, 20.0),
    "barril": (2.6, -3.2, 0.0),
    "mesa": (9.6, -1.6, -90.0),
    "estanteria": (-11.2, -2.2, 90.0),
}

# Boca del horno medida con rayos sobre la malla (studs, mundo)
BOCA = {"x0": -4.2, "x1": -1.2, "z0": 2.0, "z1": 5.3, "y_cara": 1.22}
CENTRO_BRASAS = Vector((-2.6, 3.4, 3.05))  # encima del lecho de brasas
AGUA_Z = 3.30  # superficie del agua del barril
CENTRO_BARRIL = Vector((2.6, -3.2, AGUA_Z))
CARA_YUNQUE_Z = 3.42  # cara de trabajo del yunque

# ---------------------------------------------------------------------------------------------------------------
# Materiales
# ---------------------------------------------------------------------------------------------------------------


def _mat(nombre):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    return m, m.node_tree.nodes, m.node_tree.links


def mat_simple(nombre, color, rug=0.6, metal=0.0, emision=None, fuerza=0.0):
    m, n, _ = _mat(nombre)
    p = n["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Roughness"].default_value = rug
    p.inputs["Metallic"].default_value = metal
    if emision:
        p.inputs["Emission Color"].default_value = (*emision, 1)
        p.inputs["Emission Strength"].default_value = fuerza
    return m


def mat_maniqui():
    """Plástico gris del maniquí R6, con algo de brillo para que el fuego lo dibuje."""
    m, n, l = _mat("Maniqui")
    p = n["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.045, 0.045, 0.05, 1)
    p.inputs["Roughness"].default_value = 0.55
    p.inputs["Specular IOR Level"].default_value = 0.55
    return m


def mat_hierro(nombre="Hierro", color=(0.05, 0.048, 0.046), rug=0.48):
    """Hierro forjado oscuro con un ruido de rugosidad para que los brillos no sean de plástico."""
    m, n, l = _mat(nombre)
    p = n["Principled BSDF"]
    p.inputs["Base Color"].default_value = (*color, 1)
    p.inputs["Metallic"].default_value = 0.9
    ruido = n.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 9.0
    rampa = n.new("ShaderNodeMapRange")
    rampa.inputs["To Min"].default_value = rug - 0.15
    rampa.inputs["To Max"].default_value = rug + 0.2
    l.new(ruido.outputs["Fac"], rampa.inputs["Value"])
    l.new(rampa.outputs["Result"], p.inputs["Roughness"])
    return m


def mat_madera(nombre="Mango"):
    m, n, l = _mat(nombre)
    p = n["Principled BSDF"]
    veta = n.new("ShaderNodeTexWave")
    veta.inputs["Scale"].default_value = 6.0
    veta.inputs["Distortion"].default_value = 6.0
    rampa = n.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (0.10, 0.05, 0.025, 1)
    rampa.color_ramp.elements[1].color = (0.24, 0.13, 0.06, 1)
    l.new(veta.outputs["Fac"], rampa.inputs["Fac"])
    l.new(rampa.outputs["Color"], p.inputs["Base Color"])
    p.inputs["Roughness"].default_value = 0.7
    return m


def mat_pieza_caliente():
    """Material de la pieza que se forja. Se animan tres entradas:
    - «Temperatura» (Blackbody, en kelvin) y «Brillo» (fuerza de emisión): rojo vivo -> naranja -> blanco.
    - «Pulido» (0-1): de acero con calamina oscura a acero gris pulido tras el temple.
    Devuelve (material, nodo_blackbody, nodo_principled, nodo_mezcla_pulido)."""
    m, n, l = _mat("PiezaCaliente")
    p = n["Principled BSDF"]
    p.inputs["Metallic"].default_value = 1.0
    # El color de la emisión se anima desde Python (cinematica.cuerpo_negro, con el canal más alto a 1): el nodo
    # Blackbody de Cycles normaliza la luminancia y a ~800 K el rojo sale a más de 4, así que la pieza seguía
    # al rojo vivo con un brillo casi nulo. El nodo se deja solo para guardar la temperatura (la lee el documento).
    cuerpo = n.new("ShaderNodeBlackbody")
    cuerpo.name = "Temperatura"
    cuerpo.inputs["Temperature"].default_value = 1500
    p.inputs["Emission Strength"].default_value = 0.0
    # Calamina (negra y rugosa) frente a acero pulido (gris claro y liso), mezclados por «Pulido»
    ruido = n.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 14.0
    ruido.inputs["Detail"].default_value = 6.0
    calamina = n.new("ShaderNodeValToRGB")
    calamina.color_ramp.elements[0].color = (0.035, 0.03, 0.028, 1)
    calamina.color_ramp.elements[1].color = (0.11, 0.1, 0.095, 1)
    l.new(ruido.outputs["Fac"], calamina.inputs["Fac"])
    mezcla = n.new("ShaderNodeMix")
    mezcla.name = "Pulido"
    mezcla.data_type = "RGBA"
    mezcla.inputs["Factor"].default_value = 0.0
    l.new(calamina.outputs["Color"], mezcla.inputs["A"])
    mezcla.inputs["B"].default_value = (0.62, 0.63, 0.66, 1)
    l.new(mezcla.outputs["Result"], p.inputs["Base Color"])
    rug = n.new("ShaderNodeMix")
    rug.name = "RugPulido"
    rug.data_type = "FLOAT"
    rug.inputs["A"].default_value = 0.62
    rug.inputs["B"].default_value = 0.16
    l.new(rug.outputs["Result"], p.inputs["Roughness"])
    return m, cuerpo, p, mezcla, rug


def mat_chispa():
    """Chispas y ascuas: emisión de cuerpo negro que se enfría con la edad de la partícula."""
    m, n, l = _mat("Chispa")
    salida = n["Material Output"]
    n.remove(n["Principled BSDF"])
    info = n.new("ShaderNodeParticleInfo")
    edad = n.new("ShaderNodeMath")
    edad.operation = "DIVIDE"
    l.new(info.outputs["Age"], edad.inputs[0])
    l.new(info.outputs["Lifetime"], edad.inputs[1])
    temp = n.new("ShaderNodeMapRange")
    temp.inputs["From Min"].default_value = 0.0
    temp.inputs["From Max"].default_value = 1.0
    temp.inputs["To Min"].default_value = 2600.0
    temp.inputs["To Max"].default_value = 1100.0
    l.new(edad.outputs[0], temp.inputs["Value"])
    cuerpo = n.new("ShaderNodeBlackbody")
    l.new(temp.outputs["Result"], cuerpo.inputs["Temperature"])
    fuerza = n.new("ShaderNodeMapRange")
    fuerza.inputs["From Min"].default_value = 0.0
    fuerza.inputs["From Max"].default_value = 1.0
    fuerza.inputs["To Min"].default_value = 30.0
    fuerza.inputs["To Max"].default_value = 4.0
    l.new(edad.outputs[0], fuerza.inputs["Value"])
    em = n.new("ShaderNodeEmission")
    l.new(cuerpo.outputs["Color"], em.inputs["Color"])
    l.new(fuerza.outputs["Result"], em.inputs["Strength"])
    l.new(em.outputs[0], salida.inputs["Surface"])
    return m


def mat_llama():
    """Lengua de fuego: emisión con una máscara de ruido que sube; lo que no es llama, transparente."""
    m, n, l = _mat("Llama")
    salida = n["Material Output"]
    n.remove(n["Principled BSDF"])
    coord = n.new("ShaderNodeTexCoord")
    mapa = n.new("ShaderNodeMapping")
    l.new(coord.outputs["Generated"], mapa.inputs["Vector"])
    ruido = n.new("ShaderNodeTexNoise")
    ruido.name = "RuidoLlama"
    ruido.noise_dimensions = "4D"
    ruido.inputs["Scale"].default_value = 3.2
    ruido.inputs["Detail"].default_value = 4.0
    ruido.inputs["Distortion"].default_value = 1.4
    l.new(mapa.outputs["Vector"], ruido.inputs["Vector"])
    # gradiente vertical: abajo lleno, arriba nada
    sep = n.new("ShaderNodeSeparateXYZ")
    l.new(coord.outputs["Generated"], sep.inputs[0])
    grad = n.new("ShaderNodeMath")
    grad.operation = "SUBTRACT"
    l.new(ruido.outputs["Fac"], grad.inputs[0])
    l.new(sep.outputs["Z"], grad.inputs[1])
    # bordes laterales que se desvanecen (sin esto los planos cruzados se ven como estrellas recortadas)
    borde = n.new("ShaderNodeMath")
    borde.operation = "SUBTRACT"
    borde.inputs[0].default_value = 0.5
    lateral = n.new("ShaderNodeMath")
    lateral.operation = "ABSOLUTE"
    centrado = n.new("ShaderNodeMath")
    centrado.operation = "SUBTRACT"
    centrado.inputs[1].default_value = 0.5
    l.new(sep.outputs["X"], centrado.inputs[0])
    l.new(centrado.outputs[0], lateral.inputs[0])
    l.new(lateral.outputs[0], borde.inputs[1])
    suave_borde = n.new("ShaderNodeMath")
    suave_borde.operation = "MULTIPLY"
    suave_borde.inputs[1].default_value = 2.6
    suave_borde.use_clamp = True
    l.new(borde.outputs[0], suave_borde.inputs[0])
    corte = n.new("ShaderNodeMapRange")
    corte.inputs["From Min"].default_value = -0.05
    corte.inputs["From Max"].default_value = 0.45
    l.new(grad.outputs[0], corte.inputs["Value"])
    mascara0 = n.new("ShaderNodeMath")
    mascara0.operation = "MULTIPLY"
    l.new(corte.outputs["Result"], mascara0.inputs[0])
    l.new(suave_borde.outputs[0], mascara0.inputs[1])
    # el pie de la llama también se desvanece (sin esto se ve una banda recta sobre las brasas)
    pie = n.new("ShaderNodeMapRange")
    pie.inputs["From Min"].default_value = 0.0
    pie.inputs["From Max"].default_value = 0.18
    l.new(sep.outputs["Z"], pie.inputs["Value"])
    mascara = n.new("ShaderNodeMath")
    mascara.operation = "MULTIPLY"
    l.new(mascara0.outputs[0], mascara.inputs[0])
    l.new(pie.outputs["Result"], mascara.inputs[1])
    opacidad = n.new("ShaderNodeMath")
    opacidad.operation = "MULTIPLY"
    opacidad.inputs[1].default_value = 0.5
    l.new(mascara.outputs[0], opacidad.inputs[0])
    # color: rojo oscuro en los bordes, naranja y amarillo en el corazón de la llama
    rampa = n.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].color = (0.55, 0.06, 0.0, 1)
    rampa.color_ramp.elements[1].position = 0.55
    rampa.color_ramp.elements[1].color = (1.0, 0.32, 0.03, 1)
    e = rampa.color_ramp.elements.new(1.0)
    e.color = (1.0, 0.7, 0.25, 1)
    l.new(mascara.outputs[0], rampa.inputs["Fac"])
    em = n.new("ShaderNodeEmission")
    em.inputs["Strength"].default_value = 2.0
    l.new(rampa.outputs["Color"], em.inputs["Color"])
    trans = n.new("ShaderNodeBsdfTransparent")
    mezcla = n.new("ShaderNodeMixShader")
    l.new(opacidad.outputs[0], mezcla.inputs["Fac"])
    l.new(trans.outputs[0], mezcla.inputs[1])
    l.new(em.outputs[0], mezcla.inputs[2])
    l.new(mezcla.outputs[0], salida.inputs["Surface"])
    return m, ruido


def mat_vapor(nombre):
    """Volumen de vapor: densidad con ruido y caída radial (bordes suaves). «Densidad» se anima por bocanada."""
    m, n, l = _mat(nombre)
    salida = n["Material Output"]
    n.remove(n["Principled BSDF"])
    coord = n.new("ShaderNodeTexCoord")
    ruido = n.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 2.2
    ruido.inputs["Detail"].default_value = 2.0
    l.new(coord.outputs["Object"], ruido.inputs["Vector"])
    dist = n.new("ShaderNodeVectorMath")
    dist.operation = "LENGTH"
    l.new(coord.outputs["Object"], dist.inputs[0])
    caida = n.new("ShaderNodeMapRange")
    caida.inputs["From Min"].default_value = 1.0
    caida.inputs["From Max"].default_value = 0.2
    l.new(dist.outputs["Value"], caida.inputs["Value"])
    mult = n.new("ShaderNodeMath")
    mult.operation = "MULTIPLY"
    l.new(ruido.outputs["Fac"], mult.inputs[0])
    l.new(caida.outputs["Result"], mult.inputs[1])
    forma = n.new("ShaderNodeMapRange")
    forma.inputs["From Min"].default_value = 0.18
    forma.inputs["From Max"].default_value = 0.6
    l.new(mult.outputs[0], forma.inputs["Value"])
    dens = n.new("ShaderNodeMath")
    dens.name = "Densidad"
    dens.operation = "MULTIPLY"
    dens.inputs[1].default_value = 0.0
    l.new(forma.outputs["Result"], dens.inputs[0])
    vol = n.new("ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (0.82, 0.8, 0.78, 1)
    vol.inputs["Anisotropy"].default_value = 0.35
    l.new(dens.outputs[0], vol.inputs["Density"])
    l.new(vol.outputs[0], salida.inputs["Volume"])
    return m, dens


def mat_agua():
    m, n, l = _mat("AguaTemple")
    p = n["Principled BSDF"]
    p.inputs["Base Color"].default_value = (0.02, 0.03, 0.03, 1)
    p.inputs["Roughness"].default_value = 0.06
    p.inputs["Specular IOR Level"].default_value = 0.6
    return m


# ---------------------------------------------------------------------------------------------------------------
# Construcción de mallas
# ---------------------------------------------------------------------------------------------------------------


def _objeto(nombre, bm, mat=None, suave=False):
    me = bpy.data.meshes.new(nombre)
    bm.to_mesh(me)
    bm.free()
    if suave:
        for p in me.polygons:
            p.use_smooth = True
    o = bpy.data.objects.new(nombre, me)
    bpy.context.scene.collection.objects.link(o)
    if mat:
        o.data.materials.append(mat)
    return o


def _caja(bm, centro, tam, mat_idx=0):
    r = bmesh.ops.create_cube(bm, size=1.0)
    for v in r["verts"]:
        v.co = Vector((v.co.x * tam[0], v.co.y * tam[1], v.co.z * tam[2])) + Vector(centro)
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat_idx
    return r["verts"]


def _cilindro(bm, centro, radio, alto, eje="Z", segs=12, mat_idx=0):
    r = bmesh.ops.create_cone(bm, cap_ends=True, segments=segs, radius1=radio, radius2=radio, depth=alto)
    rot = {"Z": Matrix(), "X": Matrix.Rotation(math.pi / 2, 4, "Y"), "Y": Matrix.Rotation(math.pi / 2, 4, "X")}[eje]
    bmesh.ops.transform(bm, matrix=Matrix.Translation(centro) @ rot, verts=r["verts"])
    for f in {f for v in r["verts"] for f in v.link_faces}:
        f.material_index = mat_idx
    return r["verts"]


def caja_biselada(nombre, tam, mat, bisel=0.06):
    bm = bmesh.new()
    _caja(bm, (0, 0, 0), tam)
    bmesh.ops.bevel(bm, geom=list(bm.edges), offset=bisel, segments=2, affect="EDGES", profile=0.5)
    return _objeto(nombre, bm, mat, suave=True)


# ---------------------------------------------------------------------------------------------------------------
# La forja (piezas ya hechas en modelos/forja)
# ---------------------------------------------------------------------------------------------------------------


def islas_martillo_yunque(malla):
    """Índices de vértices del martillo grande que forja_yunque trae apoyado en la cara del yunque (cabeza y mango):
    las islas de la malla que están enteras por encima de la cara de trabajo. En la cinemática el herrero golpea con
    su propio martillo y la pieza tiene que apoyarse en esa cara, así que se quita."""
    bm = bmesh.new()
    bm.from_mesh(malla)
    bm.verts.ensure_lookup_table()
    vistos, quitar = set(), []
    for v in bm.verts:
        if v.index in vistos:
            continue
        pila, isla = [v], []
        vistos.add(v.index)
        while pila:
            x = pila.pop()
            isla.append(x.index)
            for e in x.link_edges:
                w = e.other_vert(x)
                if w.index not in vistos:
                    vistos.add(w.index)
                    pila.append(w)
        # en el sistema del FBX la altura es la Y local (sale de Roblox con Y arriba)
        alturas = [bm.verts[i].co.y for i in isla]
        if min(alturas) > ALTO_MANGO and max(alturas) > ALTO_CABEZA:
            quitar += isla
    bm.free()
    return quitar


# Alturas (sobre la base del yunque, studs) para reconocer el martillo apoyado: todo él está por encima de la cara
ALTO_MANGO = 2.6
ALTO_CABEZA = 2.95


def quitar_vertices(o, indices):
    bm = bmesh.new()
    bm.from_mesh(o.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in indices], context="VERTS")
    bm.to_mesh(o.data)
    bm.free()


def importar_forja(quitar_martillo=True):
    """Importa los FBX de modelos/forja y los coloca como en MONTAJE. Los FBX traen ya el giro de importación de
    Roblox (180° sobre el eje vertical): aquí se deshace para que queden igual que en los renders de la forja.
    quitar_martillo: quita el martillo decorativo de la cara del yunque (ver islas_martillo_yunque)."""
    obs = {}
    for clave, (x, y, giro) in MONTAJE.items():
        antes = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=os.path.join(FORJA, f"forja_{clave}.fbx"))
        nuevos = [o for o in bpy.data.objects if o not in antes]
        z = 0.0 if clave == "suelo" else ALTO_SUELO
        m = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(giro), 4, "Z") @ Matrix.Rotation(math.pi, 4, "Z")
        for o in nuevos:
            if quitar_martillo and o.name == "forja_yunque":
                quitar_vertices(o, islas_martillo_yunque(o.data))
            o.matrix_world = m @ o.matrix_world
            obs[o.name] = o
    # Las brasas del horno: emisión fuerte (en el juego van en Neon)
    for mat in bpy.data.materials:
        if mat.name.startswith("forja_horno") and mat.node_tree:
            p = mat.node_tree.nodes.get("Principled BSDF")
            if p and p.inputs["Emission Color"].is_linked:
                p.inputs["Emission Strength"].default_value = 1.6
    return obs


def compuerta_horno():
    """Compuerta de guillotina de hierro para la boca del horno (el modelo de la forja tiene la boca abierta).
    Sube por dos guías verticales (objeto «GuiasCompuerta») y se abre tirando del asa hacia arriba. Devuelve la compuerta;
    su origen es el centro de su borde de abajo."""
    ancho = BOCA["x1"] - BOCA["x0"] + 0.5
    alto = BOCA["z1"] - BOCA["z0"] + 0.3
    hierro = mat_hierro("CompuertaHierro", (0.045, 0.042, 0.04), 0.55)
    remache = mat_hierro("Remache", (0.08, 0.07, 0.065), 0.35)
    brillo = mat_simple("Mirilla", (0.02, 0.01, 0.0), 0.8, emision=(1.0, 0.38, 0.08), fuerza=14.0)
    bm = bmesh.new()
    _caja(bm, (0, 0, alto / 2), (ancho, 0.16, alto), 0)  # chapa
    for z in (0.35, alto - 0.35):  # pletinas horizontales
        _caja(bm, (0, -0.1, z), (ancho + 0.05, 0.06, 0.28), 0)
    for zx in range(5):  # remaches en las pletinas
        x = -ancho / 2 + 0.3 + zx * (ancho - 0.6) / 4
        for z in (0.35, alto - 0.35):
            _cilindro(bm, Vector((x, -0.15, z)), 0.06, 0.06, "Y", 8, 1)
    # mirilla: ranuras que dejan ver el fuego
    for i in range(4):
        _caja(bm, (-0.45 + i * 0.3, -0.085, alto * 0.62), (0.12, 0.02, 0.62), 2)
    # asa (U de hierro) abajo a la derecha: la coge la mano derecha (cinematica.ASA_LOCAL)
    _caja(bm, (0.55, -0.62, 1.0), (0.8, 0.1, 0.1), 0)
    _caja(bm, (0.2, -0.37, 1.0), (0.1, 0.5, 0.1), 0)
    _caja(bm, (0.9, -0.37, 1.0), (0.1, 0.5, 0.1), 0)
    o = _objeto("Compuerta", bm)
    for m in (hierro, remache, brillo):
        o.data.materials.append(m)
    o.location = ((BOCA["x0"] + BOCA["x1"]) / 2, BOCA["y_cara"] - 0.12, BOCA["z0"] - 0.05)
    # Guías fijas a los lados
    bm = bmesh.new()
    for x in (-ancho / 2 - 0.12, ancho / 2 + 0.12):
        _caja(bm, (x, -0.05, 3.5), (0.16, 0.3, 7.0), 0)
    guias = _objeto("GuiasCompuerta", bm, hierro)
    guias.location = ((BOCA["x0"] + BOCA["x1"]) / 2, BOCA["y_cara"] - 0.12, BOCA["z0"] - 0.05)
    return o


# ---------------------------------------------------------------------------------------------------------------
# Utilería
# ---------------------------------------------------------------------------------------------------------------

LARGO_TENAZAS = 1.7  # studs, de la mano a la punta de las mordazas


def tenazas():
    """Tenazas de herrero. Origen = donde las coge la mano; las mordazas apuntan a -Z local (en la dirección del
    brazo extendido)."""
    hierro = mat_hierro("Tenazas", (0.04, 0.038, 0.036), 0.5)
    bm = bmesh.new()
    L = LARGO_TENAZAS
    for s in (-1, 1):  # dos brazos que se cruzan en el pasador
        _caja(bm, (s * 0.05, 0, -0.55), (0.05, 0.07, 1.1), 0)
        _caja(bm, (s * 0.035, 0, -1.25), (0.05, 0.07, 0.3), 0)
        _caja(bm, (s * 0.07, 0, -1.5), (0.04, 0.12, 0.42), 0)  # mordaza
    _cilindro(bm, Vector((0, 0, -1.1)), 0.06, 0.18, "X", 8, 0)  # pasador
    o = _objeto("Tenazas", bm, hierro)
    o["punta_local"] = (0.0, 0.0, -L)
    return o


def martillo():
    """Martillo de forja. Origen = mano; el mango va a lo largo de -Z local y la boca golpea hacia +Y local."""
    hierro = mat_hierro("CabezaMartillo", (0.06, 0.056, 0.052), 0.38)
    madera = mat_madera()
    bm = bmesh.new()
    _caja(bm, (0, 0, -0.55), (0.12, 0.12, 1.3), 1)  # mango
    _caja(bm, (0, 0, -1.25), (0.26, 0.62, 0.28), 0)  # cabeza
    _caja(bm, (0, 0.33, -1.25), (0.3, 0.06, 0.32), 0)  # boca de golpeo
    _caja(bm, (0, -0.36, -1.25), (0.18, 0.12, 0.16), 0)  # peña
    o = _objeto("Martillo", bm)
    o.data.materials.append(hierro)
    o.data.materials.append(madera)
    return o


# Etapas de la pieza: de lingote a hoja. Cada una: largo de la hoja, ancho, grueso, filo (0 = canto recto,
# 1 = filo vivo), punta (0 = recta, 1 = punta completa), largo de la espiga.
ETAPAS = [
    (1.00, 0.42, 0.26, 0.00, 0.00, 0.00),  # lingote
    (1.35, 0.40, 0.21, 0.15, 0.10, 0.10),
    (1.75, 0.38, 0.16, 0.35, 0.30, 0.25),
    (2.10, 0.36, 0.12, 0.55, 0.55, 0.40),
    (2.45, 0.34, 0.09, 0.78, 0.80, 0.52),
    (2.70, 0.33, 0.07, 0.95, 1.00, 0.62),  # hoja terminada
]
N_LARGO = 28


def _seccion(w, g, e):
    """Sección de 8 puntos (x, y): ancho w, grueso g, canto e (1 = canto recto, 0 = filo vivo)."""
    return [(-w / 2, g / 2 * e), (-w / 4, g / 2), (w / 4, g / 2), (w / 2, g / 2 * e),
            (w / 2, -g / 2 * e), (w / 4, -g / 2), (-w / 4, -g / 2), (-w / 2, -g / 2 * e)]


MORDIDA = 0.15  # cuánto entra la pieza entre las mordazas de las tenazas


def _vertices_pieza(etapa):
    """Vértices de la pieza en una etapa (mismo orden en todas, para las shape keys). El origen es la punta de las
    tenazas; la pieza empieza MORDIDA por detrás y se extiende hacia -Z local: espiga y después la hoja."""
    largo, ancho, grueso, filo, punta, espiga = etapa
    secciones = []
    w_espiga = ancho * (1 - 0.62 * espiga / 0.62)
    for i in range(4):  # espiga (en el lingote, el primer trozo del propio lingote)
        z = MORDIDA - (MORDIDA + espiga) * i / 3
        secciones.append((_seccion(w_espiga, grueso * (1 + 0.4 * espiga), 1.0), z))
    for i in range(N_LARGO + 1):  # hoja
        u = i / N_LARGO
        w = ancho
        if u > 0.7:
            t = (u - 0.7) / 0.3
            w = ancho * (1 - punta * 0.93 * t**1.25)
        g = grueso * (1 - 0.4 * punta * max(0.0, u - 0.55))
        secciones.append((_seccion(w, g, 1 - filo), -espiga - u * largo))
    return [Vector((x, y, z)) for sec, z in secciones for x, y in sec]


def pieza():
    """Malla de la pieza con una shape key por etapa (Etapa1..Etapa5). La base es el lingote."""
    base = _vertices_pieza(ETAPAS[0])
    n_sec = len(base) // 8
    bm = bmesh.new()
    vs = [bm.verts.new(v) for v in base]
    for s in range(n_sec - 1):
        for k in range(8):
            a, b = s * 8 + k, s * 8 + (k + 1) % 8
            c, d = (s + 1) * 8 + (k + 1) % 8, (s + 1) * 8 + k
            bm.faces.new((vs[a], vs[b], vs[c], vs[d]))
    bm.faces.new([vs[k] for k in range(8)])
    bm.faces.new([vs[(n_sec - 1) * 8 + k] for k in reversed(range(8))])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mat, cuerpo, princ, pulido, rug = mat_pieza_caliente()
    o = _objeto("Pieza", bm, mat, suave=True)
    o.shape_key_add(name="Lingote")
    for i, etapa in enumerate(ETAPAS[1:], 1):
        k = o.shape_key_add(name=f"Etapa{i}", from_mix=False)
        for j, v in enumerate(_vertices_pieza(etapa)):
            k.data[j].co = v
    mod = o.modifiers.new("Bisel", "BEVEL")
    mod.width = 0.012
    mod.segments = 1
    mod.limit_method = "ANGLE"
    return o, cuerpo, princ, pulido, rug


# ---------------------------------------------------------------------------------------------------------------
# Maniquí R6 (6 piezas)
# ---------------------------------------------------------------------------------------------------------------

PIEZAS_R6 = {  # pieza: (tamaño en studs, centro de la pieza respecto a su articulación)
    "Torso": ((2.0, 1.0, 2.0), (0, 0, 0)),
    "Head": ((1.2, 1.2, 1.2), (0, 0, 0.6)),
    "Left Arm": ((1.0, 1.0, 2.0), (0.5, 0, -0.5)),
    "Right Arm": ((1.0, 1.0, 2.0), (-0.5, 0, -0.5)),
    "Left Leg": ((1.0, 1.0, 2.0), (-0.5, 0, -1.0)),
    "Right Leg": ((1.0, 1.0, 2.0), (0.5, 0, -1.0)),
}


def maniqui():
    """Las 6 piezas del R6, con el origen de cada una en su articulación (pivote del Motor6D)."""
    mat = mat_maniqui()
    obs = {}
    for nombre, (tam, centro) in PIEZAS_R6.items():
        o = caja_biselada("R6_" + nombre, (tam[0] - 0.02, tam[1] - 0.02, tam[2] - 0.02), mat, 0.07)
        o.data.transform(Matrix.Translation(centro))
        obs[nombre] = o
    return obs


# ---------------------------------------------------------------------------------------------------------------
# Fuego, partículas y vapor
# ---------------------------------------------------------------------------------------------------------------


def llamas(n=9):
    """Lenguas de fuego sobre las brasas (planos cruzados con el material de llama)."""
    mat, ruido = mat_llama()
    obs = []
    import random
    rnd = random.Random(4)
    for i in range(n):
        bm = bmesh.new()
        for ang in (0, 60, 120):
            r = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
            bmesh.ops.transform(bm, matrix=Matrix.Rotation(math.radians(ang), 4, "Z") @ Matrix.Rotation(math.pi / 2, 4, "X")
                                @ Matrix.Diagonal((1.0, 1.0, 1.0, 1.0)), verts=r["verts"])
        o = _objeto(f"Llama{i}", bm, mat)
        alto = rnd.uniform(1.0, 1.7)
        o.scale = (rnd.uniform(0.6, 1.0), rnd.uniform(0.6, 1.0), alto)
        o.location = (rnd.uniform(-3.9, -1.5), rnd.uniform(2.3, 5.5), 2.95 + alto * 0.5)
        o.visible_shadow = False
        obs.append(o)
    return obs, ruido


def _sistema_particulas(emisor, nombre, instancia, **kw):
    mod = emisor.modifiers.new(nombre, "PARTICLE_SYSTEM")
    ps = mod.particle_system
    s = ps.settings
    s.name = nombre
    s.render_type = "OBJECT"
    s.instance_object = instancia
    s.use_rotation_instance = False
    s.emit_from = "FACE"
    s.use_emit_random = True
    s.physics_type = "NEWTON"
    s.normal_factor = kw.get("normal", 1.0)
    s.factor_random = kw.get("aleatorio", 0.5)
    s.object_align_factor = kw.get("velocidad", (0, 0, 0))
    s.count = kw["cantidad"]
    s.frame_start = kw["inicio"]
    s.frame_end = kw["fin"]
    s.lifetime = kw.get("vida", 20)
    s.lifetime_random = kw.get("vida_aleatoria", 0.5)
    s.particle_size = kw.get("tam", 1.0)
    s.size_random = kw.get("tam_aleatorio", 0.5)
    s.brownian_factor = kw.get("browniano", 0.0)
    s.drag_factor = kw.get("arrastre", 0.0)
    s.effector_weights.gravity = kw.get("gravedad", 1.0)
    s.use_die_on_collision = False
    s.display_method = "DOT"
    ps.seed = kw.get("semilla", 1)
    emisor.show_instancer_for_render = False
    return ps


def particulas_base():
    """Instancias de las partículas (fuera de cámara): chispa alargada, ascua y burbuja."""
    chispa = mat_chispa()
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.025)
    inst_chispa = _objeto("InstChispa", bm, chispa)
    inst_chispa.location = (0, 0, -50)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=0.03)
    inst_ascua = _objeto("InstAscua", bm, chispa)
    inst_ascua.location = (0, 0, -50)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.035)
    inst_burbuja = _objeto("InstBurbuja", bm, mat_simple("Burbuja", (0.06, 0.07, 0.07), 0.08), suave=True)
    inst_burbuja.location = (0, 0, -50)
    return inst_chispa, inst_ascua, inst_burbuja


def emisor_disco(nombre, centro, radio, normal=(0, 0, 1)):
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, radius=radio, segments=12)
    o = _objeto(nombre, bm)
    o.location = centro
    o.rotation_euler = Vector((0, 0, 1)).rotation_difference(Vector(normal)).to_euler()
    o.hide_render = False
    return o


def agua_temple():
    """Superficie de agua del barril que se agita durante el temple (Wave animado)."""
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, radius=1.18, segments=40)
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=4, use_grid_fill=True)
    o = _objeto("AguaTemple", bm, mat_agua(), suave=True)
    o.location = (CENTRO_BARRIL.x, CENTRO_BARRIL.y, AGUA_Z + 0.03)
    sub = o.modifiers.new("Sub", "SUBSURF")
    sub.levels = sub.render_levels = 2
    ola = o.modifiers.new("Ola", "WAVE")
    ola.height = 0.0
    ola.width = 0.25
    ola.speed = 0.06
    ola.narrowness = 1.2
    ola.start_position_object = None
    return o, ola


def bocanadas_vapor(n=14):
    """Bocanadas de vapor (volúmenes) que suben del barril. Devuelve [(objeto, nodo_densidad)]."""
    res = []
    for i in range(n):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
        m, dens = mat_vapor(f"Vapor{i}")
        o = _objeto(f"Vapor{i}", bm, m)
        o.visible_shadow = False
        res.append((o, dens))
    return res


# ---------------------------------------------------------------------------------------------------------------
# Luz, mundo, cámara y render
# ---------------------------------------------------------------------------------------------------------------


def luz(nombre, tipo, energia, pos, color, radio=0.3, apuntar=None, tam=1.0):
    d = bpy.data.lights.new(nombre, tipo)
    d.energy = energia
    d.color = color
    if tipo in ("POINT", "SPOT"):
        d.shadow_soft_size = radio
    if tipo == "AREA":
        d.size = tam
    o = bpy.data.objects.new(nombre, d)
    bpy.context.scene.collection.objects.link(o)
    o.location = pos
    if apuntar is not None:
        o.rotation_euler = (Vector(apuntar) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    return o


def mundo(scn):
    w = bpy.data.worlds.new("Noche")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.004, 0.005, 0.009, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 1.0
    scn.world = w


def ajustes_render(scn, ancho, alto, muestras, desenfoque=True):
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    scn.cycles.samples = muestras
    scn.cycles.use_adaptive_sampling = True
    scn.cycles.adaptive_threshold = 0.05
    scn.cycles.use_denoising = True
    scn.cycles.denoiser = "OPENIMAGEDENOISE"
    scn.cycles.max_bounces = 4
    scn.cycles.diffuse_bounces = 1
    scn.cycles.glossy_bounces = 1
    scn.cycles.transmission_bounces = 2
    scn.cycles.volume_bounces = 0
    scn.cycles.transparent_max_bounces = 8
    scn.cycles.caustics_reflective = False
    scn.cycles.caustics_refractive = False
    scn.cycles.blur_glossy = 1.0
    scn.cycles.volume_step_rate = 10.0
    scn.cycles.volume_max_steps = 96
    scn.cycles.use_light_tree = False  # con estas luces es un 25 % más rápido y no se nota
    # Lo que brilla pero no tiene que iluminar como luz (de eso se encargan las luces de punto): chispas, llamas,
    # brasas, mirilla y destello. Así no se convierten en miles de luces diminutas.
    for m in bpy.data.materials:
        if m.name in ("Chispa", "Llama", "Mirilla", "Destello") or m.name.startswith("forja_horno"):
            m.cycles.emission_sampling = "NONE"
    scn.cycles.sample_clamp_indirect = 6.0
    scn.render.use_persistent_data = True  # no reconstruye la escena en cada fotograma
    scn.cycles.denoising_prefilter = "FAST"
    scn.cycles.denoising_quality = "BALANCED"
    scn.render.resolution_x = ancho
    scn.render.resolution_y = alto
    scn.render.resolution_percentage = 100
    scn.render.fps = 30
    scn.render.use_motion_blur = desenfoque
    scn.render.motion_blur_shutter = 0.6
    scn.render.image_settings.file_format = "PNG"
    scn.render.image_settings.color_mode = "RGB"
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Punchy"
    scn.view_settings.exposure = 0.0
    scn.render.film_transparent = False


def composicion(scn):
    """Resplandor (bloom) sobre lo que brilla, estrellas sobre lo que brilla muchísimo (el destello del filo) y una
    viñeta suave que oscurece las esquinas."""
    arbol = bpy.data.node_groups.new("Composicion", "CompositorNodeTree")
    scn.compositing_node_group = arbol
    arbol.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
    n, l = arbol.nodes, arbol.links
    entrada = n.new("CompositorNodeRLayers")
    salida = n.new("NodeGroupOutput")
    halo = n.new("CompositorNodeGlare")
    _glare(halo, "Bloom", umbral=1.2, tam=0.65, fuerza=0.6)
    estrella = n.new("CompositorNodeGlare")
    _glare(estrella, "Streaks", umbral=60.0, tam=0.5, fuerza=0.8)
    l.new(entrada.outputs["Image"], halo.inputs["Image"])
    l.new(halo.outputs["Image"], estrella.inputs["Image"])
    elipse = n.new("CompositorNodeEllipseMask")
    elipse.inputs["Size"].default_value = (0.95, 0.85)
    elipse.inputs["Value"].default_value = 1.0
    blur = n.new("CompositorNodeBlur")
    blur.inputs["Size"].default_value = (260, 260)
    rango = n.new("ShaderNodeMapRange")
    rango.inputs["To Min"].default_value = 0.5
    rango.inputs["To Max"].default_value = 1.0
    mult = n.new("ShaderNodeMix")
    mult.data_type = "RGBA"
    mult.blend_type = "MULTIPLY"
    mult.inputs[0].default_value = 1.0
    l.new(elipse.outputs["Mask"], blur.inputs["Image"])
    l.new(blur.outputs["Image"], rango.inputs["Value"])
    l.new(estrella.outputs["Image"], mult.inputs[6])
    l.new(rango.outputs["Result"], mult.inputs[7])
    l.new(mult.outputs[2], salida.inputs[0])


def _glare(nodo, tipo, umbral, tam, fuerza):
    e = nodo.inputs
    e["Type"].default_value = tipo
    e["Quality"].default_value = "Medium"
    e["Threshold"].default_value = umbral
    e["Size"].default_value = tam
    e["Strength"].default_value = fuerza
    if tipo == "Streaks":
        e["Streaks"].default_value = 4
        e["Streaks Angle"].default_value = math.radians(45)
        e["Fade"].default_value = 0.9
