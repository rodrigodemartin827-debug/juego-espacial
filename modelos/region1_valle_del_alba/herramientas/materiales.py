"""
Paleta y materiales del Valle del Alba (Blender, Cycles).

Estilo: colores limpios y cálidos, sin texturas (salvo el terreno), pensados para traducirse a Roblox como Color +
Material. Cada material multiplica su color por el atributo de cara «Tinte» de la malla (variación de teja en teja,
de piedra en piedra) y por un poco de azar por objeto.

Dos grupos de nodos compartidos se ajustan por render, sin tocar los materiales:
  * «Niebla»: perspectiva aérea. Mezcla cada superficie con el color del horizonte según la distancia a la cámara.
  * «Luces»: intensidad de las ventanas y farolas encendidas (0 de día, más al atardecer).

Las «ranuras» (nombres en MAYÚSCULAS que usan las piezas del kit) se sustituyen por un material concreto al montar
cada edificio: ver RANURAS.
"""

import bpy

# nombre: (color sRGB, rugosidad, extra)
PALETA = {
    # Paredes de yeso
    "Yeso_Crema": ("#EFE2C6", 0.85, {}),
    "Yeso_Blanco": ("#F2EFE7", 0.85, {}),
    "Yeso_Melocoton": ("#EECBA8", 0.85, {}),
    "Yeso_Amarillo": ("#EFD898", 0.85, {}),
    "Yeso_Rosa": ("#E8BFB2", 0.85, {}),
    "Yeso_Celeste": ("#CBDDE0", 0.85, {}),
    # Piedra
    "Piedra_Clara": ("#CBC1B0", 0.9, {}),
    "Piedra_Media": ("#A2998A", 0.9, {}),
    "Piedra_Oscura": ("#7A746B", 0.9, {}),
    "Ladrillo": ("#A65A3E", 0.9, {}),
    # Tejados
    "Teja_Roja": ("#B4452C", 0.7, {}),
    "Teja_Roja_Oscura": ("#963A2A", 0.7, {}),
    "Teja_Naranja": ("#C45F38", 0.7, {}),
    # Madera
    "Madera_Clara": ("#B48858", 0.75, {}),
    "Madera_Media": ("#8A6340", 0.75, {}),
    "Madera_Oscura": ("#5C4130", 0.75, {}),
    # Contraventanas y puertas pintadas
    "Pintura_Verde": ("#4F7F5E", 0.6, {}),
    "Pintura_Azul": ("#4C6F94", 0.6, {}),
    "Pintura_Roja": ("#9B4B3B", 0.6, {}),
    "Pintura_Crema": ("#E9DFC5", 0.6, {}),
    # Metal y vidrio
    "Hierro": ("#2E2F33", 0.45, {"metal": 0.6}),
    "Oro": ("#D2A64A", 0.3, {"metal": 1.0}),
    "Vidrio": ("#2F4257", 0.06, {"ventana": True}),
    "Luz_Calida": ("#FFC46E", 0.4, {"emision": 3.0}),
    # Telas
    "Toldo_Rojo": ("#C2413A", 0.8, {}),
    "Toldo_Blanco": ("#F2EEE6", 0.8, {}),
    "Toldo_Azul": ("#3F6FA8", 0.8, {}),
    "Toldo_Amarillo": ("#E8B840", 0.8, {}),
    "Toldo_Verde": ("#4E8C5A", 0.8, {}),
    "Tela_Vela": ("#EDE3CC", 0.85, {}),
    "Papel": ("#F4EEDC", 0.9, {}),
    "Papel_Amarillo": ("#EFD98A", 0.9, {}),
    # Vegetación
    "Hoja_Verde": ("#5C9A3B", 0.8, {"hoja": True}),
    "Hoja_Clara": ("#86B846", 0.8, {"hoja": True}),
    "Hoja_Oscura": ("#3E7838", 0.8, {"hoja": True}),
    "Hoja_Pino": ("#3B6A3F", 0.8, {"hoja": True}),
    "Hoja_Otono": ("#D9973A", 0.8, {"hoja": True}),
    "Flor_Rosa": ("#F2A9C2", 0.8, {"hoja": True}),
    "Corteza": ("#6B4E37", 0.9, {}),
    "Corteza_Abedul": ("#E7E2D6", 0.9, {}),
    "Hierba": ("#73A845", 0.85, {"hoja": True}),
    "Flor_Roja": ("#D9443A", 0.8, {}),
    "Flor_Amarilla": ("#F2CF45", 0.8, {}),
    "Flor_Blanca": ("#F5F2EA", 0.8, {}),
    "Flor_Lila": ("#A98BD6", 0.8, {}),
    # Campo
    "Trigo": ("#DDB65A", 0.85, {"hoja": True}),
    "Paja": ("#D6B663", 0.9, {}),
    "Col": ("#7DB06A", 0.8, {"hoja": True}),
    "Tierra_Arada": ("#7A5A3E", 0.95, {}),
    "Calabaza": ("#E08A2E", 0.7, {}),
    "Fruta_Roja": ("#C8352E", 0.5, {}),
    "Fruta_Naranja": ("#E8902C", 0.5, {}),
    # Agua
    "Agua": ("#2B5A64", 0.035, {"agua": True}),
    "Agua_Fuente": ("#4E8E99", 0.03, {"agua": True}),
    "Agua_Chorro": ("#DDF2F4", 0.05, {"agua": True, "alfa": 0.5}),
}

# Ranura -> material por defecto (los edificios eligen variantes).
RANURAS = {
    "PARED": "Yeso_Crema",
    "TEJA": "Teja_Roja",
    "TEJA_B": "Teja_Roja_Oscura",
    "PINTURA": "Pintura_Verde",
    "PUERTA": "Madera_Media",
    "TOLDO_A": "Toldo_Rojo",
    "TOLDO_B": "Toldo_Blanco",
    "PIEDRA": "Piedra_Clara",
    "MARCO": "Madera_Oscura",
}

VARIANTES = {
    "PARED": ["Yeso_Crema", "Yeso_Blanco", "Yeso_Melocoton", "Yeso_Amarillo", "Yeso_Rosa", "Yeso_Celeste"],
    "TEJA": ["Teja_Roja", "Teja_Roja_Oscura", "Teja_Naranja"],
    "PINTURA": ["Pintura_Verde", "Pintura_Azul", "Pintura_Roja", "Pintura_Crema"],
    "PUERTA": ["Madera_Media", "Madera_Oscura", "Pintura_Verde", "Pintura_Azul", "Pintura_Roja"],
    "TOLDO_A": ["Toldo_Rojo", "Toldo_Azul", "Toldo_Amarillo", "Toldo_Verde"],
    "PIEDRA": ["Piedra_Clara", "Piedra_Media"],
    "MARCO": ["Madera_Oscura", "Madera_Media", "Yeso_Blanco"],
}


def srgb_a_lineal(h):
    h = h.lstrip("#")
    c = [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# --------------------------------------------------------------------------------------------------------------
# Grupos compartidos
# --------------------------------------------------------------------------------------------------------------


def grupo_niebla():
    """Entrada: Shader. Salida: Shader mezclado con el color de la niebla según la distancia a la cámara."""
    if "Niebla" in bpy.data.node_groups:
        return bpy.data.node_groups["Niebla"]
    g = bpy.data.node_groups.new("Niebla", "ShaderNodeTree")
    g.interface.new_socket("Shader", in_out="INPUT", socket_type="NodeSocketShader")
    g.interface.new_socket("Shader", in_out="OUTPUT", socket_type="NodeSocketShader")
    n, l = g.nodes, g.links
    ent, sal = n.new("NodeGroupInput"), n.new("NodeGroupOutput")
    cam = n.new("ShaderNodeCameraData")
    inicio = n.new("ShaderNodeValue")
    inicio.name = inicio.label = "inicio"
    inicio.outputs[0].default_value = 300.0
    dist = n.new("ShaderNodeValue")
    dist.name = dist.label = "distancia"
    dist.outputs[0].default_value = 2500.0
    maximo = n.new("ShaderNodeValue")
    maximo.name = maximo.label = "maximo"
    maximo.outputs[0].default_value = 0.85
    color = n.new("ShaderNodeRGB")
    color.name = color.label = "color"
    color.outputs[0].default_value = (0.62, 0.72, 0.85, 1)
    # f = maximo * (1 - exp(-max(d - inicio, 0) / distancia))
    resta = n.new("ShaderNodeMath")
    resta.operation = "SUBTRACT"
    l.new(cam.outputs["View Distance"], resta.inputs[0])
    l.new(inicio.outputs[0], resta.inputs[1])
    mx = n.new("ShaderNodeMath")
    mx.operation = "MAXIMUM"
    mx.inputs[1].default_value = 0.0
    l.new(resta.outputs[0], mx.inputs[0])
    div = n.new("ShaderNodeMath")
    div.operation = "DIVIDE"
    l.new(mx.outputs[0], div.inputs[0])
    l.new(dist.outputs[0], div.inputs[1])
    neg = n.new("ShaderNodeMath")
    neg.operation = "MULTIPLY"
    neg.inputs[1].default_value = -1.0
    l.new(div.outputs[0], neg.inputs[0])
    ex = n.new("ShaderNodeMath")
    ex.operation = "EXPONENT"
    l.new(neg.outputs[0], ex.inputs[0])
    uno = n.new("ShaderNodeMath")
    uno.operation = "SUBTRACT"
    uno.inputs[0].default_value = 1.0
    l.new(ex.outputs[0], uno.inputs[1])
    fac = n.new("ShaderNodeMath")
    fac.operation = "MULTIPLY"
    l.new(uno.outputs[0], fac.inputs[0])
    l.new(maximo.outputs[0], fac.inputs[1])
    brillo = n.new("ShaderNodeValue")
    brillo.name = brillo.label = "brillo"
    brillo.outputs[0].default_value = 3.0
    em = n.new("ShaderNodeEmission")
    l.new(color.outputs[0], em.inputs["Color"])
    l.new(brillo.outputs[0], em.inputs["Strength"])
    mix = n.new("ShaderNodeMixShader")
    l.new(fac.outputs[0], mix.inputs[0])
    l.new(ent.outputs[0], mix.inputs[1])
    l.new(em.outputs[0], mix.inputs[2])
    l.new(mix.outputs[0], sal.inputs[0])
    return g


def grupo_luces():
    if "Luces" in bpy.data.node_groups:
        return bpy.data.node_groups["Luces"]
    g = bpy.data.node_groups.new("Luces", "ShaderNodeTree")
    g.interface.new_socket("Valor", in_out="OUTPUT", socket_type="NodeSocketFloat")
    v = g.nodes.new("ShaderNodeValue")
    v.name = v.label = "intensidad"
    v.outputs[0].default_value = 0.0
    sal = g.nodes.new("NodeGroupOutput")
    g.links.new(v.outputs[0], sal.inputs[0])
    return g


def ajustar_niebla(inicio, distancia, maximo, color_lineal, brillo=None):
    g = grupo_niebla()
    if brillo is not None and "brillo" in g.nodes:
        g.nodes["brillo"].outputs[0].default_value = brillo
    g.nodes["inicio"].outputs[0].default_value = inicio
    g.nodes["distancia"].outputs[0].default_value = distancia
    g.nodes["maximo"].outputs[0].default_value = maximo
    g.nodes["color"].outputs[0].default_value = (*color_lineal, 1.0)


def ajustar_luces(intensidad):
    grupo_luces().nodes["intensidad"].outputs[0].default_value = intensidad


# --------------------------------------------------------------------------------------------------------------
# Materiales
# --------------------------------------------------------------------------------------------------------------


def salida_con_niebla(mat, shader_socket):
    nt = mat.node_tree
    gn = nt.nodes.new("ShaderNodeGroup")
    gn.node_tree = grupo_niebla()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    nt.links.new(shader_socket, gn.inputs[0])
    nt.links.new(gn.outputs[0], out.inputs["Surface"])
    return out


def color_con_tinte(nt, color_lineal, variacion_objeto=0.06):
    """Devuelve un socket de color = color base × Tinte × (1 ± variación por objeto)."""
    n, l = nt.nodes, nt.links
    rgb = n.new("ShaderNodeRGB")
    rgb.outputs[0].default_value = (*color_lineal, 1)
    at = n.new("ShaderNodeAttribute")
    at.attribute_type = "GEOMETRY"
    at.attribute_name = "Tinte"
    # Si la malla no tiene Tinte, el atributo vale 0: se usa max(tinte, ...) con «Fac» = 1 por defecto mediante
    # una mezcla: tinte_efectivo = tinte si existe. Todas las mallas del proyecto lo tienen; el terreno no usa esto.
    obj = n.new("ShaderNodeObjectInfo")
    var = n.new("ShaderNodeMapRange")
    var.inputs["To Min"].default_value = 1.0 - variacion_objeto
    var.inputs["To Max"].default_value = 1.0 + variacion_objeto
    l.new(obj.outputs["Random"], var.inputs["Value"])
    m1 = n.new("ShaderNodeVectorMath")
    m1.operation = "SCALE"
    l.new(rgb.outputs[0], m1.inputs[0])
    l.new(at.outputs["Fac"], m1.inputs["Scale"])
    m2 = n.new("ShaderNodeVectorMath")
    m2.operation = "SCALE"
    l.new(m1.outputs[0], m2.inputs[0])
    l.new(var.outputs[0], m2.inputs["Scale"])
    return m2.outputs[0]


def crear_material(nombre):
    if nombre in bpy.data.materials:
        return bpy.data.materials[nombre]
    hexa, rug, extra = PALETA[nombre]
    col = srgb_a_lineal(hexa)
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = rug
    mat.diffuse_color = (*col, 1)
    if extra.get("agua"):
        bsdf.inputs["Base Color"].default_value = (*col, 1)
        bsdf.inputs["IOR"].default_value = 1.33
        bsdf.inputs["Specular IOR Level"].default_value = 0.6
        bsdf.inputs["Alpha"].default_value = extra.get("alfa", 0.82)  # deja ver un poco el fondo
        # Ondas: bump con ruido estirado.
        tc = nt.nodes.new("ShaderNodeTexCoord")
        mp = nt.nodes.new("ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (0.08, 0.2, 0.08)
        nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
        ruido = nt.nodes.new("ShaderNodeTexNoise")
        ruido.inputs["Scale"].default_value = 3.0
        ruido.inputs["Detail"].default_value = 4.0
        nt.links.new(mp.outputs[0], ruido.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.12
        nt.links.new(ruido.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    else:
        nt.links.new(color_con_tinte(nt, col), bsdf.inputs["Base Color"])
    if "metal" in extra:
        bsdf.inputs["Metallic"].default_value = extra["metal"]
    if extra.get("hoja"):
        # Un poco de luz que atraviesa las hojas: más vivo a contraluz (atardecer).
        bsdf.inputs["Subsurface Weight"].default_value = 0.0
        bsdf.inputs["Sheen Weight"].default_value = 0.15
    if extra.get("ventana") or "emision" in extra:
        luces = nt.nodes.new("ShaderNodeGroup")
        luces.node_tree = grupo_luces()
        fuerza = nt.nodes.new("ShaderNodeMath")
        fuerza.operation = "MULTIPLY_ADD"
        # ventanas: 0 de día; farolas: un mínimo de día (cristal cálido) y mucho más de noche
        base = 0.0 if extra.get("ventana") else 0.3
        k = 1.0 if extra.get("ventana") else extra["emision"]
        nt.links.new(luces.outputs[0], fuerza.inputs[0])
        fuerza.inputs[1].default_value = k
        fuerza.inputs[2].default_value = base
        nt.links.new(fuerza.outputs[0], bsdf.inputs["Emission Strength"])
        bsdf.inputs["Emission Color"].default_value = (*srgb_a_lineal("#FFB65C"), 1)
        if extra.get("ventana"):
            # Solo algunas ventanas se encienden: por azar de objeto y del tinte de la cara.
            pass
    salida_con_niebla(mat, bsdf.outputs[0])
    return mat


def todos():
    """Crea (si no existen) todos los materiales de la paleta y devuelve {nombre: material}, con las ranuras."""
    mats = {n: crear_material(n) for n in PALETA}
    for ranura, defecto in RANURAS.items():
        mats[ranura] = mats[defecto]
    return mats
