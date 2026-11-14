"""
Materiales PBR procedurales de la forja (Cycles). Cada material calcula color, rugosidad, metal, relieve y luz
propia con nodos; después se hornean al atlas de cada pieza (ver hornear.py).

Todos leen el atributo `tex` de la malla (ver malla.py) y llevan encima la misma capa de suciedad:
  * mugre en los huecos (oclusión), polvo cerca del suelo,
  * hollín alrededor de los focos de fuego de la pieza (`hollin`: lista de (centro, radios, fuerza)),
  * cantos desgastados (la diferencia entre la normal real y la redondeada del nodo Bevel).
El nodo Bevel también redondea las aristas en el mapa de normales: las cajas no parecen de cartón.

Colores en lineal. `hx("#rrggbb")` convierte desde sRGB.
"""

import bpy

S = bpy.types.NodeSocket


def hx(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# ---- Colores ajustables de la forja --------------------------------------------------------------------------
COLORES = {
    "madera": (hx("#20140c"), hx("#4c3322"), hx("#705138")),        # veta oscura, media y clara (marrón cálido)
    "madera_osc": (hx("#150d07"), hx("#33200f"), hx("#4e3420")),    # madera vieja, ahumada
    "madera_canto": hx("#9c7c56"),                                   # madera pelada en los cantos
    "hierro": (hx("#17181b"), hx("#33353a")),                        # hierro forjado, casi negro
    "hierro_canto": hx("#8d8f96"),                                   # metal vivo en los cantos
    "acero": (hx("#5b5f66"), hx("#9da2ab")),                         # hojas de espada
    "oxido": (hx("#3a180a"), hx("#8a4a1c")),                         # óxido oscuro y naranja
    "piedra": (hx("#26272a"), hx("#4a4b4e")),                        # piedra gris oscuro
    "piedra_canto": hx("#75767a"),
    "mortero": hx("#3b3832"),
    "ladrillo": (hx("#3a1710"), hx("#5e2a1c"), hx("#74402b")),       # ladrillo rojizo
    "cuero": (hx("#2c160a"), hx("#5b3318")),
    "cuero_canto": hx("#8a5a34"),
    "laton": (hx("#3d2c10"), hx("#8a6a2c")),
    "cobre": (hx("#4a2414"), hx("#9a5a36")),
    "hollin": hx("#0d0c0b"),
    "mugre": hx("#15100a"),
    "polvo": hx("#3a332a"),
    "ceniza": hx("#6f6a63"),
    "agua": hx("#0c2226"),
    "pintura_roja": hx("#561510"),
    "pintura_azul": hx("#172c44"),
    "pintura_crema": hx("#7d6f52"),
    "brasa": [(0.0, hx("#060403")), (0.35, hx("#5a0a02")), (0.6, hx("#ff3c05")), (0.85, hx("#ff9a1c")),
              (1.0, hx("#ffe9a0"))],
}

REGISTRO = {}


class G:
    """Atajos para montar nodos: cada función devuelve el enchufe de salida."""

    def __init__(self, nt):
        self.nt = nt
        self._tex = None
        self._pos = None
        self._geo = None

    def nodo(self, tipo, **props):
        n = self.nt.nodes.new(tipo)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def poner(self, enchufe, v):
        if v is None:
            return
        if isinstance(v, S):
            self.nt.links.new(v, enchufe)
            return
        if enchufe.type == "RGBA":
            if isinstance(v, (int, float)):
                v = (v, v, v, 1.0)
            elif len(v) == 3:
                v = (*v, 1.0)
        elif enchufe.type == "VECTOR" and isinstance(v, (int, float)):
            v = (v, v, v)
        enchufe.default_value = v

    # -- coordenadas
    def tex(self):
        if self._tex is None:
            self._tex = self.nodo("ShaderNodeAttribute", attribute_type="GEOMETRY", attribute_name="tex").outputs[
                "Vector"]
        return self._tex

    def pos(self):
        if self._pos is None:
            self._pos = self.nodo("ShaderNodeTexCoord").outputs["Object"]
        return self._pos

    def geo(self, salida):
        if self._geo is None:
            self._geo = self.nodo("ShaderNodeNewGeometry")
        return self._geo.outputs[salida]

    def mapa(self, vec, esc=(1, 1, 1), loc=(0, 0, 0)):
        n = self.nodo("ShaderNodeMapping")
        self.poner(n.inputs["Vector"], vec)
        n.inputs["Scale"].default_value = esc
        n.inputs["Location"].default_value = loc
        return n.outputs[0]

    def xyz(self, vec):
        n = self.nodo("ShaderNodeSeparateXYZ")
        self.poner(n.inputs[0], vec)
        return n.outputs[0], n.outputs[1], n.outputs[2]

    def vec(self, x=0.0, y=0.0, z=0.0):
        n = self.nodo("ShaderNodeCombineXYZ")
        for i, v in enumerate((x, y, z)):
            self.poner(n.inputs[i], v)
        return n.outputs[0]

    def vm(self, op, a, b=None, salida=0):
        n = self.nodo("ShaderNodeVectorMath", operation=op)
        self.poner(n.inputs[0], a)
        if b is not None:
            self.poner(n.inputs[1], b)
        return n.outputs[salida]

    # -- texturas
    def ruido(self, vec, escala, det=4.0, rug=0.55, dist=0.0, color=False):
        n = self.nodo("ShaderNodeTexNoise")
        self.poner(n.inputs["Vector"], vec)
        n.inputs["Scale"].default_value = escala
        n.inputs["Detail"].default_value = det
        n.inputs["Roughness"].default_value = rug
        n.inputs["Distortion"].default_value = dist
        return n.outputs[1 if color else 0]

    def voronoi(self, vec, escala, tipo="F1", salida="Distance", azar=1.0, suave=0.3):
        n = self.nodo("ShaderNodeTexVoronoi", feature=tipo)
        self.poner(n.inputs["Vector"], vec)
        n.inputs["Scale"].default_value = escala
        n.inputs["Randomness"].default_value = azar
        if tipo == "SMOOTH_F1":
            n.inputs["Smoothness"].default_value = suave
        return n.outputs[salida]

    def onda(self, vec, escala, dist=3.0, det=2.0, det_esc=1.0, tipo="RINGS", direccion="X"):
        n = self.nodo("ShaderNodeTexWave", wave_type=tipo)
        if tipo == "RINGS":
            n.rings_direction = direccion
        else:
            n.bands_direction = direccion
        self.poner(n.inputs["Vector"], vec)
        n.inputs["Scale"].default_value = escala
        n.inputs["Distortion"].default_value = dist
        n.inputs["Detail"].default_value = det
        n.inputs["Detail Scale"].default_value = det_esc
        return n.outputs["Fac"] if "Fac" in n.outputs else n.outputs[1]

    def ladrillo(self, vec, escala=1.0, ancho=1.0, alto=0.42, junta=0.03, suave=0.4):
        n = self.nodo("ShaderNodeTexBrick")
        self.poner(n.inputs["Vector"], vec)
        n.inputs["Color1"].default_value = (0, 0, 0, 1)
        n.inputs["Color2"].default_value = (1, 1, 1, 1)
        n.inputs["Mortar"].default_value = (0.5, 0.5, 0.5, 1)
        n.inputs["Scale"].default_value = escala
        n.inputs["Mortar Size"].default_value = junta
        n.inputs["Mortar Smooth"].default_value = suave
        n.inputs["Bias"].default_value = 0.0
        n.inputs["Brick Width"].default_value = ancho
        n.inputs["Row Height"].default_value = alto
        return n.outputs["Color"], n.outputs["Fac"]

    # -- cuentas
    def m(self, op, a, b=None, c=None, tope=False):
        n = self.nodo("ShaderNodeMath", operation=op, use_clamp=tope)
        self.poner(n.inputs[0], a)
        if b is not None:
            self.poner(n.inputs[1], b)
        if c is not None:
            self.poner(n.inputs[2], c)
        return n.outputs[0]

    def rango(self, v, a0, a1, b0=0.0, b1=1.0, suave=False):
        n = self.nodo("ShaderNodeMapRange", clamp=True, interpolation_type="SMOOTHSTEP" if suave else "LINEAR")
        self.poner(n.inputs["Value"], v)
        for k, x in (("From Min", a0), ("From Max", a1), ("To Min", b0), ("To Max", b1)):
            self.poner(n.inputs[k], x)
        return n.outputs[0]

    def rampa(self, fac, paradas, interp="LINEAR"):
        n = self.nodo("ShaderNodeValToRGB")
        r = n.color_ramp
        r.interpolation = interp
        while len(r.elements) < len(paradas):
            r.elements.new(0.5)
        for e, (p, c) in zip(r.elements, paradas):
            e.position = p
            e.color = (*c, 1.0) if len(c) == 3 else c
        self.poner(n.inputs[0], fac)
        return n.outputs[0]

    def mix(self, fac, a, b, modo="MIX"):
        n = self.nodo("ShaderNodeMix", data_type="RGBA", blend_type=modo, clamp_factor=True)
        self.poner(n.inputs[0], fac)
        self.poner(n.inputs[6], a)
        self.poner(n.inputs[7], b)
        return n.outputs[2]

    def mixf(self, fac, a, b):
        n = self.nodo("ShaderNodeMix", data_type="FLOAT", clamp_factor=True)
        self.poner(n.inputs[0], fac)
        self.poner(n.inputs[2], a)
        self.poner(n.inputs[3], b)
        return n.outputs[0]

    # -- máscaras de geometría
    def borde(self, radio=0.06, a0=0.02, a1=0.25):
        """1 en los cantos vivos (aristas convexas y cóncavas), 0 en las caras."""
        b = self.nodo("ShaderNodeBevel", samples=6)
        b.inputs["Radius"].default_value = radio
        d = self.vm("DOT_PRODUCT", b.outputs[0], self.geo("Normal"), salida="Value")
        return self.rango(self.m("SUBTRACT", 1.0, d), a0, a1)

    def hueco(self, dist=0.6, a0=0.25, a1=0.85):
        """1 en los rincones (poca luz ambiente), 0 en lo abierto."""
        n = self.nodo("ShaderNodeAmbientOcclusion", samples=8)
        n.inputs["Distance"].default_value = dist
        return self.rango(n.outputs["AO"], a0, a1, 1.0, 0.0)

    def foco(self, centro, radios):
        """Caída suave (1 en el centro, 0 a partir del radio) alrededor de un punto, en coordenadas del objeto."""
        d = self.vm("SUBTRACT", self.pos(), tuple(centro))
        d = self.vm("DIVIDE", d, tuple(radios))
        return self.rango(self.vm("LENGTH", d, salida="Value"), 0.15, 1.0, 1.0, 0.0, suave=True)


def nuevo(nombre):
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat, G(mat.node_tree)


def terminar(mat, g, color, rug, metal, altura=None, fuerza=0.5, dist=0.05, emision=None, bisel=0.045):
    """Monta el Principled y deja preparados los nodos de horneado (uno de emisión por canal)."""
    nt = mat.node_tree
    p = g.nodo("ShaderNodeBsdfPrincipled")
    p.name = "pbr"
    g.poner(p.inputs["Base Color"], color)
    g.poner(p.inputs["Roughness"], rug)
    g.poner(p.inputs["Metallic"], metal)
    normal = None
    if altura is not None:
        b = g.nodo("ShaderNodeBump")
        b.inputs["Strength"].default_value = fuerza
        b.inputs["Distance"].default_value = dist
        g.poner(b.inputs["Height"], altura)
        normal = b.outputs[0]
    if bisel:
        bv = g.nodo("ShaderNodeBevel", samples=8)
        bv.inputs["Radius"].default_value = bisel
        if normal is not None:
            nt.links.new(normal, bv.inputs["Normal"])
        normal = bv.outputs[0]
    if normal is not None:
        nt.links.new(normal, p.inputs["Normal"])
    if emision is not None:
        g.poner(p.inputs["Emission Color"], emision)
        p.inputs["Emission Strength"].default_value = 1.0
    salida = g.nodo("ShaderNodeOutputMaterial")
    salida.name = "salida"
    nt.links.new(p.outputs[0], salida.inputs[0])
    for canal, v in (("color", color), ("rug", rug), ("metal", metal), ("emision", emision or (0, 0, 0))):
        e = g.nodo("ShaderNodeEmission")
        e.name = "h_" + canal
        g.poner(e.inputs[0], v)
    REGISTRO[mat.name] = mat
    return mat


def modo(mat, canal):
    """Conecta a la salida el Principled ("pbr") o el canal que se va a hornear como emisión."""
    nt = mat.node_tree
    origen = nt.nodes["pbr"] if canal == "pbr" else nt.nodes["h_" + canal]
    nt.links.new(origen.outputs[0], nt.nodes["salida"].inputs[0])


# ---- Capa común de suciedad ----------------------------------------------------------------------------------


def ensuciar(g, color, rug, metal=0.0, hollin=(), suelo=0.9, mugre=0.75, polvo=0.5, hollin_base=0.0):
    """Mugre en los rincones, polvo junto al suelo y hollín junto al fuego. Devuelve (color, rug, metal)."""
    p = g.pos()
    manchas = g.ruido(p, 1.7, det=5, rug=0.65)
    fino = g.ruido(p, 9.0, det=3, rug=0.6)
    # Mugre de rincón
    h = g.m("MULTIPLY", g.hueco(), g.rango(manchas, 0.25, 0.7, 0.45, 1.0))
    h = g.m("MULTIPLY", h, mugre)
    color = g.mix(h, color, COLORES["mugre"])
    rug = g.mixf(h, rug, 0.95)
    metal = g.mixf(h, metal, 0.0) if not isinstance(metal, (int, float)) or metal > 0 else metal
    # Polvo y barro cerca del suelo
    if suelo > 0:
        _, _, z = g.xyz(p)
        zz = g.m("ADD", z, g.m("MULTIPLY", g.m("SUBTRACT", manchas, 0.5), 0.9))
        s = g.m("MULTIPLY", g.rango(zz, 0.0, suelo, 1.0, 0.0, suave=True), polvo)
        color = g.mix(s, color, g.mix(fino, COLORES["mugre"], COLORES["polvo"]))
        rug = g.mixf(s, rug, 0.97)
    # Hollín
    total = None
    for centro, radios, fuerza in hollin:
        f = g.m("MULTIPLY", g.foco(centro, radios), fuerza)
        total = f if total is None else g.m("MAXIMUM", total, f)
    if total is not None or hollin_base > 0:
        base = g.m("MULTIPLY", g.rango(manchas, 0.35, 0.75), hollin_base)
        if total is None:
            total = base
        else:
            total = g.m("ADD", g.m("MULTIPLY", total, g.rango(manchas, 0.2, 0.75, 0.55, 1.25)), base, tope=True)
        color = g.mix(total, color, g.mix(fino, COLORES["hollin"], (0.03, 0.028, 0.026)))
        rug = g.mixf(total, rug, 0.93)
        if not isinstance(metal, (int, float)) or metal > 0:
            metal = g.mixf(total, metal, 0.15)
    return color, rug, metal


# ---- Materiales ----------------------------------------------------------------------------------------------


def madera(nombre, tonos="madera", hollin=(), suelo=0.9, hollin_base=0.0, pintura=None, desgaste=0.75,
           tablas=0.0, diseno=None):
    """Madera con veta a lo largo de tex.x, anillos alrededor de ese eje, grietas y cantos pelados."""
    mat, g = nuevo(nombre)
    v = g.tex()
    osc, med, cla = COLORES[tonos]
    fibras = g.ruido(g.mapa(v, esc=(0.45, 15, 15)), 1.0, det=6, rug=0.62)
    anillos = g.onda(g.mapa(v, esc=(0.35, 1, 1)), 3.4, dist=2.2, det=3, det_esc=0.6)
    tabla = g.ruido(v, 0.3, det=2)
    veta = g.m("ADD", g.m("MULTIPLY", fibras, 0.72), g.m("MULTIPLY", anillos, 0.28))
    color = g.rampa(veta, [(0.22, osc), (0.5, med), (0.78, cla)])
    color = g.mix(g.rango(tabla, 0.3, 0.75, 0.0, 0.55), color, osc)
    # Grietas: ruido muy estirado a lo largo de la veta, con umbral fino
    gr = g.ruido(g.mapa(v, esc=(0.16, 7, 7)), 1.0, det=3, rug=0.55)
    grietas = g.rango(g.m("ABSOLUTE", g.m("SUBTRACT", gr, 0.5)), 0.0, 0.022, 1.0, 0.0, suave=True)
    grietas = g.m("MULTIPLY", grietas, g.rango(g.ruido(v, 1.3, det=2), 0.4, 0.6))
    color = g.mix(g.m("MULTIPLY", grietas, 0.9), color, (0.012, 0.007, 0.004))
    altura = g.m("SUBTRACT", g.m("MULTIPLY", veta, 0.55), g.m("MULTIPLY", grietas, 1.6))
    rug = g.rango(veta, 0.2, 0.8, 0.88, 0.66)
    if tablas:
        # Juntas entre tablas (a lo ancho de tex.y), para escudos y tableros hechos de una sola malla
        _, ty, _ = g.xyz(v)
        fr = g.m("FRACT", g.m("DIVIDE", g.m("ADD", ty, 50.0), tablas))
        jt = g.rango(g.m("ABSOLUTE", g.m("SUBTRACT", fr, 0.5)), 0.44, 0.5)
        color = g.mix(g.m("MULTIPLY", jt, 0.9), color, (0.01, 0.006, 0.004))
        altura = g.m("SUBTRACT", altura, g.m("MULTIPLY", jt, 2.0))
        grietas = g.m("MAXIMUM", grietas, jt)
    if pintura:
        # Pintura vieja: aguanta en las caras, saltada en los cantos y a parches
        salto = g.ruido(g.pos(), 2.3, det=6, rug=0.7)
        capa = g.m("MULTIPLY", g.rango(salto, 0.42, 0.5), g.m("SUBTRACT", 1.0, g.borde(0.1, 0.01, 0.12)))
        _, ny, _ = g.xyz(g.geo("Normal"))
        capa = g.m("MULTIPLY", capa, g.rango(ny, -0.45, -0.25, 1.0, 0.0))   # solo la cara de delante (-Y)
        capa = g.m("MULTIPLY", capa, g.m("SUBTRACT", 1.0, g.m("MULTIPLY", grietas, 0.9)))
        tono = g.mix(g.ruido(g.pos(), 5.0, det=3), COLORES[pintura], tuple(c * 0.55 for c in COLORES[pintura]))
        if diseno:
            tx, ty, _ = g.xyz(v)
            otro = COLORES[diseno[0]]
            if diseno[1] == "cuartos":
                zona = g.rango(g.m("MULTIPLY", tx, ty), -0.004, 0.004)
            elif diseno[1] == "palo":
                zona = g.rango(g.m("ABSOLUTE", ty), diseno[2] - 0.01, diseno[2] + 0.01, 1.0, 0.0)
            else:  # "banda": franja en diagonal
                zona = g.rango(g.m("ABSOLUTE", g.m("ADD", tx, ty)), diseno[2] - 0.01, diseno[2] + 0.01, 1.0, 0.0)
            tono = g.mix(zona, tono, g.mix(g.ruido(g.pos(), 5.0, det=3), otro, tuple(c * 0.6 for c in otro)))
        color = g.mix(capa, color, tono)
        rug = g.mixf(capa, rug, 0.6)
        altura = g.m("ADD", altura, g.m("MULTIPLY", capa, 0.35))
    canto = g.m("MULTIPLY", g.borde(0.07), g.rango(g.ruido(g.pos(), 4.0, det=3), 0.3, 0.65, 0.2, 1.0))
    color = g.mix(g.m("MULTIPLY", canto, desgaste), color, COLORES["madera_canto"])
    color, rug, _ = ensuciar(g, color, rug, 0.0, hollin, suelo, hollin_base=hollin_base)
    return terminar(mat, g, color, rug, 0.0, altura, fuerza=0.55, dist=0.05, bisel=0.05)


def hierro(nombre, tonos="hierro", oxido=0.55, canto=0.8, hollin=(), suelo=0.6, pulido=None, huecos=(),
           rayado=0.0, martillado=1.0, rug_base=(0.42, 0.7), hollin_base=0.0, mugre=0.75):
    """
    Hierro forjado: oscuro, con golpes de martillo, cantos de metal vivo y óxido naranja en rincones y a parches.
    `pulido`: cota z a partir de la cual las caras que miran arriba están pulidas por el uso (la mesa del yunque).
    `huecos`: [(centro, medio_tamaño)] agujeros pintados (el del yunque para las herramientas).
    `rayado`: arañazos a lo largo de tex.x (hojas de espada).
    """
    mat, g = nuevo(nombre)
    p = g.pos()
    a, b = COLORES[tonos]
    grande = g.ruido(p, 1.4, det=5, rug=0.6)
    fino = g.ruido(p, 14.0, det=3, rug=0.6)
    color = g.mix(g.rango(grande, 0.3, 0.7), a, b)
    rug = g.rango(fino, 0.3, 0.7, rug_base[0], rug_base[1])
    metal = 1.0
    golpes = g.voronoi(p, 4.5, tipo="SMOOTH_F1", suave=0.6)
    altura = g.m("ADD", g.m("MULTIPLY", golpes, 0.9 * martillado), g.m("MULTIPLY", fino, 0.25))
    if rayado > 0:
        r = g.ruido(g.mapa(g.tex(), esc=(0.6, 60, 60)), 1.0, det=4, rug=0.7)
        color = g.mix(g.m("MULTIPLY", g.rango(r, 0.35, 0.7), rayado), color, tuple(c * 1.5 for c in b))
        rug = g.m("ADD", rug, g.m("MULTIPLY", g.m("SUBTRACT", r, 0.5), 0.35 * rayado))
        altura = g.m("ADD", altura, g.m("MULTIPLY", r, 0.35 * rayado))
    if pulido is not None:
        _, _, z = g.xyz(p)
        _, _, nz = g.xyz(g.geo("Normal"))
        cara = g.m("MULTIPLY", g.rango(z, pulido - 0.02, pulido), g.rango(nz, 0.8, 0.95))
        cara = g.m("MULTIPLY", cara, g.rango(grande, 0.2, 0.6, 0.55, 1.0))
        ray = g.ruido(g.mapa(p, esc=(1.5, 40, 1)), 1.0, det=4, rug=0.7)
        color = g.mix(cara, color, g.mix(ray, hx("#54575d"), hx("#a9adb5")))
        rug = g.mixf(cara, rug, g.rango(ray, 0.3, 0.7, 0.22, 0.42))
    # Cantos vivos
    c = g.m("MULTIPLY", g.borde(0.05), g.rango(g.ruido(p, 6.0, det=4, rug=0.7), 0.3, 0.6, 0.15, 1.0))
    c = g.m("MULTIPLY", c, canto)
    color = g.mix(c, color, COLORES["hierro_canto"])
    rug = g.mixf(c, rug, 0.3)
    # Óxido: a parches y sobre todo en los rincones
    if oxido > 0:
        par = g.ruido(p, 2.6, det=6, rug=0.72, dist=0.4)
        ox = g.rango(g.m("ADD", par, g.m("MULTIPLY", g.hueco(0.35, 0.3, 0.9), 0.28)), 0.70 - 0.2 * oxido,
                     0.82 - 0.16 * oxido)
        ox = g.m("MULTIPLY", ox, g.m("SUBTRACT", 1.0, g.m("MULTIPLY", c, 0.8)))
        tono = g.mix(g.ruido(p, 11.0, det=4, rug=0.7), *COLORES["oxido"])
        color = g.mix(ox, color, tono)
        rug = g.mixf(ox, rug, 0.92)
        metal = g.mixf(ox, 1.0, 0.1)
        altura = g.m("ADD", altura, g.m("MULTIPLY", ox, g.m("MULTIPLY", fino, 0.5)))
    for centro, medio in huecos:
        d = g.vm("SUBTRACT", p, tuple(centro))
        d = g.vm("ABSOLUTE", g.vm("DIVIDE", d, tuple(medio)))
        x, y, _ = g.xyz(d)
        dentro = g.rango(g.m("MAXIMUM", x, y), 0.85, 1.0, 1.0, 0.0)
        color = g.mix(dentro, color, (0.004, 0.004, 0.004))
        rug = g.mixf(dentro, rug, 1.0)
        metal = g.mixf(dentro, metal, 0.0)
        altura = g.m("SUBTRACT", altura, g.m("MULTIPLY", dentro, 6.0))
    color, rug, metal = ensuciar(g, color, rug, metal, hollin, suelo, mugre=mugre, polvo=0.35,
                                 hollin_base=hollin_base)
    return terminar(mat, g, color, rug, metal, altura, fuerza=0.45, dist=0.03, bisel=0.035)


def sillar(nombre, hollin=(), suelo=1.2, hollin_base=0.0):
    """Piedra gris oscuro de bloques tallados (cada bloque es geometría): veteado, picaduras y cantos rotos."""
    mat, g = nuevo(nombre)
    v = g.tex()
    a, b = COLORES["piedra"]
    grande = g.ruido(v, 0.9, det=6, rug=0.65, dist=0.3)
    fino = g.ruido(v, 7.0, det=5, rug=0.7)
    bloque = g.ruido(g.vm("MULTIPLY", g.voronoi(g.pos(), 0.9, salida="Color"), (20, 20, 20)), 1.0, det=0)
    color = g.mix(g.rango(g.m("ADD", g.m("MULTIPLY", grande, 0.7), g.m("MULTIPLY", fino, 0.3)), 0.3, 0.72), a, b)
    color = g.mix(g.rango(bloque, 0.3, 0.7, 0.0, 0.3), color, hx("#3d3a34"))
    pic = g.voronoi(v, 5.5, tipo="F1")
    picaduras = g.rango(pic, 0.0, 0.16, 1.0, 0.0)
    picaduras = g.m("MULTIPLY", picaduras, g.rango(g.ruido(v, 1.8, det=2), 0.45, 0.6))
    color = g.mix(g.m("MULTIPLY", picaduras, 0.7), color, (0.012, 0.012, 0.012))
    c = g.m("MULTIPLY", g.borde(0.09), g.rango(g.ruido(g.pos(), 5.0, det=4), 0.25, 0.6, 0.1, 1.0))
    color = g.mix(g.m("MULTIPLY", c, 0.55), color, COLORES["piedra_canto"])
    altura = g.m("SUBTRACT", g.m("ADD", g.m("MULTIPLY", grande, 0.8), g.m("MULTIPLY", fino, 0.4)),
                 g.m("MULTIPLY", picaduras, 1.2))
    rug = g.rango(fino, 0.3, 0.7, 0.8, 0.95)
    color, rug, _ = ensuciar(g, color, rug, 0.0, hollin, suelo, hollin_base=hollin_base)
    return terminar(mat, g, color, rug, 0.0, altura, fuerza=0.7, dist=0.06, bisel=0.07)


def ladrillo(nombre, hollin=(), suelo=1.0, hollin_base=0.35, ancho=0.82, alto=0.35, resplandor=None):
    """Ladrillo rojizo a mano: hiladas irregulares, junta hundida de mortero sucio, ladrillos quemados sueltos."""
    mat, g = nuevo(nombre)
    v = g.tex()
    def_ = g.ruido(v, 0.8, det=2, color=True)
    vd = g.vm("ADD", v, g.vm("MULTIPLY", g.vm("SUBTRACT", def_, (0.5, 0.5, 0.5)), (0.09, 0.09, 0.0)))
    tono, junta = g.ladrillo(vd, 1.0, ancho=ancho, alto=alto, junta=0.028, suave=0.5)
    osc, med, cla = COLORES["ladrillo"]
    fino = g.ruido(v, 9.0, det=5, rug=0.7)
    medio = g.ruido(v, 2.2, det=4, rug=0.6)
    color = g.rampa(g.m("ADD", g.m("MULTIPLY", tono, 0.75), g.m("MULTIPLY", medio, 0.25)),
                    [(0.2, osc), (0.5, med), (0.85, cla)])
    # Algunos ladrillos requemados, casi negros
    quem = g.rango(tono, 0.0, 0.12, 1.0, 0.0)
    color = g.mix(g.m("MULTIPLY", quem, 0.8), color, hx("#1c1412"))
    color = g.mix(g.rango(fino, 0.55, 0.8, 0.0, 0.35), color, osc)
    mortero = g.mix(fino, COLORES["mortero"], tuple(c * 0.5 for c in COLORES["mortero"]))
    color = g.mix(junta, color, mortero)
    desconchado = g.rango(g.voronoi(v, 3.3, tipo="F1"), 0.0, 0.2, 1.0, 0.0)
    desconchado = g.m("MULTIPLY", desconchado, g.rango(medio, 0.5, 0.62))
    color = g.mix(g.m("MULTIPLY", desconchado, 0.5), color, osc)
    altura = g.m("ADD", g.m("MULTIPLY", g.m("SUBTRACT", 1.0, junta), 1.0), g.m("MULTIPLY", fino, 0.3))
    altura = g.m("SUBTRACT", altura, g.m("MULTIPLY", desconchado, 0.6))
    altura = g.m("ADD", altura, g.m("MULTIPLY", tono, 0.25))
    rug = g.mixf(junta, g.rango(fino, 0.3, 0.7, 0.78, 0.92), 0.97)
    color, rug, _ = ensuciar(g, color, rug, 0.0, hollin, suelo, hollin_base=hollin_base, mugre=0.6)
    emision = None
    if resplandor:
        # Dentro del horno: el ladrillo de abajo está al rojo. (z0, z1): de dónde a dónde se apaga el resplandor.
        _, _, z = g.xyz(g.pos())
        calor = g.m("MULTIPLY", g.rango(z, resplandor[0], resplandor[1], 1.0, 0.0, suave=True),
                    g.rango(medio, 0.2, 0.8, 0.5, 1.0))
        calor = g.m("MULTIPLY", calor, g.m("SUBTRACT", 1.0, g.m("MULTIPLY", junta, 0.6)))
        color = g.mix(g.m("MULTIPLY", calor, 0.6), color, hx("#7a2408"))
        em = g.rampa(calor, [(0.0, (0, 0, 0)), (0.5, hx("#5a0a02")), (1.0, hx("#ff5a0a"))])
        emision = g.vm("MULTIPLY", em, (0.55, 0.55, 0.55))
    return terminar(mat, g, color, rug, 0.0, altura, fuerza=0.75, dist=0.07, bisel=0.05, emision=emision)


def adoquin(nombre, hollin=(), quemaduras=()):
    """Suelo de adoquín: piedras irregulares (celdas), junta de tierra y ceniza, hollín y marcas de quemado."""
    mat, g = nuevo(nombre)
    v = g.tex()
    def_ = g.ruido(v, 0.55, det=3, color=True)
    vd = g.vm("ADD", v, g.vm("MULTIPLY", g.vm("SUBTRACT", def_, (0.5, 0.5, 0.5)), (0.5, 0.5, 0.0)))
    vd = g.mapa(vd, esc=(1, 1, 0))
    borde = g.voronoi(vd, 0.95, tipo="DISTANCE_TO_EDGE", azar=0.8)
    celda = g.voronoi(vd, 0.95, tipo="F1", salida="Color", azar=0.8)
    cr, cg, _ = g.xyz(celda)
    junta = g.rango(borde, 0.025, 0.06, 1.0, 0.0, suave=True)
    lomo = g.rango(borde, 0.02, 0.22, 0.0, 1.0, suave=True)
    a, b = COLORES["piedra"]
    grande = g.ruido(v, 1.3, det=5, rug=0.65)
    fino = g.ruido(v, 8.0, det=5, rug=0.7)
    color = g.mix(cr, tuple(c * 0.75 for c in a), b)
    color = g.mix(g.rango(cg, 0.6, 1.0, 0.0, 0.5), color, hx("#4a4238"))       # alguna piedra parda
    color = g.mix(g.rango(grande, 0.35, 0.7, 0.0, 0.45), color, a)
    color = g.mix(g.rango(fino, 0.5, 0.8, 0.0, 0.4), color, tuple(c * 0.6 for c in a))
    # Grietas en algunas piedras
    gr = g.voronoi(g.mapa(v, esc=(1, 1, 0)), 1.9, tipo="DISTANCE_TO_EDGE")
    grietas = g.m("MULTIPLY", g.rango(gr, 0.0, 0.018, 1.0, 0.0), g.rango(cr, 0.55, 0.7))
    color = g.mix(g.m("MULTIPLY", grietas, 0.8), color, (0.01, 0.01, 0.01))
    tierra = g.mix(fino, COLORES["mugre"], COLORES["ceniza"])
    tierra = g.mix(0.8, tierra, COLORES["mugre"])
    color = g.mix(junta, color, tierra)
    altura = g.m("ADD", g.m("MULTIPLY", lomo, 1.0), g.m("MULTIPLY", fino, 0.18))
    altura = g.m("ADD", altura, g.m("MULTIPLY", cg, 0.25))
    altura = g.m("SUBTRACT", altura, g.m("MULTIPLY", grietas, 0.5))
    rug = g.mixf(junta, g.rango(fino, 0.3, 0.7, 0.72, 0.9), 0.98)
    # Marcas de quemado: manchas negras de borde irregular con un cerco de ceniza clara
    p = g.pos()
    manchas = g.ruido(p, 0.9, det=6, rug=0.75, dist=0.6)
    total = None
    for centro, radios, fuerza in quemaduras:
        f = g.m("MULTIPLY", g.foco(centro, radios), fuerza)
        total = f if total is None else g.m("MAXIMUM", total, f)
    if total is not None:
        q = g.m("ADD", total, g.m("MULTIPLY", g.m("SUBTRACT", manchas, 0.5), 0.9))
        cerco = g.m("MULTIPLY", g.rango(q, 0.28, 0.42), g.rango(q, 0.42, 0.56, 1.0, 0.0))
        color = g.mix(g.m("MULTIPLY", cerco, 0.45), color, COLORES["ceniza"])
        negro = g.rango(q, 0.4, 0.56)
        color = g.mix(g.m("MULTIPLY", negro, 0.93), color, COLORES["hollin"])
        rug = g.mixf(negro, rug, 0.96)
    color, rug, _ = ensuciar(g, color, rug, 0.0, hollin, suelo=0.0, mugre=0.5, hollin_base=0.45)
    return terminar(mat, g, color, rug, 0.0, altura, fuerza=1.0, dist=0.085, bisel=0.06)


def cuero(nombre, hollin=(), suelo=0.0, hollin_base=0.1):
    mat, g = nuevo(nombre)
    v = g.tex()
    a, b = COLORES["cuero"]
    grande = g.ruido(v, 1.6, det=5, rug=0.65)
    arr = g.voronoi(g.mapa(v, esc=(1.0, 1.0, 1.0)), 9.0, tipo="DISTANCE_TO_EDGE")
    arrugas = g.rango(arr, 0.0, 0.07, 1.0, 0.0)
    color = g.mix(g.rango(grande, 0.3, 0.7), a, b)
    color = g.mix(g.m("MULTIPLY", arrugas, 0.55), color, tuple(c * 0.35 for c in a))
    c = g.m("MULTIPLY", g.borde(0.07, 0.01, 0.2), g.rango(g.ruido(g.pos(), 5.0, det=4), 0.3, 0.6, 0.2, 1.0))
    color = g.mix(g.m("MULTIPLY", c, 0.7), color, COLORES["cuero_canto"])
    altura = g.m("SUBTRACT", g.m("MULTIPLY", grande, 0.5), g.m("MULTIPLY", arrugas, 0.6))
    rug = g.rango(grande, 0.3, 0.7, 0.5, 0.75)
    color, rug, _ = ensuciar(g, color, rug, 0.0, hollin, suelo, hollin_base=hollin_base)
    return terminar(mat, g, color, rug, 0.0, altura, fuerza=0.5, dist=0.04, bisel=0.04)


def brasa(nombre, fuerza=1.0):
    """Carbones encendidos: costra negra con grietas de naranja a amarillo. La luz propia va al mapa de emisión."""
    mat, g = nuevo(nombre)
    p = g.pos()
    borde = g.voronoi(p, 3.2, tipo="DISTANCE_TO_EDGE")
    calor = g.ruido(p, 0.9, det=4, rug=0.6)
    fino = g.ruido(p, 12.0, det=3)
    # Más caliente en las grietas y en las zonas que el ruido marca como vivas
    t = g.m("ADD", g.rango(borde, 0.0, 0.22, 0.75, 0.0), g.m("MULTIPLY", g.m("SUBTRACT", calor, 0.35), 1.1))
    t = g.m("ADD", t, g.m("MULTIPLY", g.m("SUBTRACT", fino, 0.5), 0.2), tope=True)
    em = g.rampa(t, COLORES["brasa"])
    emision = g.vm("MULTIPLY", em, (fuerza, fuerza, fuerza))
    color = g.mix(g.rango(t, 0.3, 0.7), hx("#0b0908"), hx("#6a1c08"))
    altura = g.m("ADD", g.rango(borde, 0.0, 0.25), g.m("MULTIPLY", fino, 0.2))
    return terminar(mat, g, color, 0.9, 0.0, altura, fuerza=0.8, dist=0.06, emision=emision, bisel=0.03)


def carbon(nombre, hollin_base=0.3):
    """Carbón apagado: negro, con caras algo brillantes."""
    mat, g = nuevo(nombre)
    p = g.pos()
    fino = g.ruido(p, 10.0, det=4)
    cel = g.voronoi(p, 4.0, salida="Color")
    r, _, _ = g.xyz(cel)
    color = g.mix(r, hx("#0a0a0b"), hx("#1d1c1d"))
    rug = g.rango(r, 0.2, 0.8, 0.45, 0.9)
    altura = g.m("ADD", g.voronoi(p, 4.0, tipo="DISTANCE_TO_EDGE"), g.m("MULTIPLY", fino, 0.2))
    return terminar(mat, g, color, rug, 0.0, altura, fuerza=0.6, dist=0.05, bisel=0.03)


def agua(nombre):
    """Agua de temple: oscura, sucia, con ceniza flotando y ondas suaves."""
    mat, g = nuevo(nombre)
    p = g.pos()
    ondas = g.onda(g.vm("ADD", p, (0.25, -0.15, 0)), 3.2, dist=1.5, det=2, det_esc=1.2, direccion="Z")
    nata = g.rango(g.ruido(p, 3.0, det=6, rug=0.75, dist=1.2), 0.6, 0.74)
    color = g.mix(g.m("MULTIPLY", nata, 0.55), COLORES["agua"], COLORES["ceniza"])
    color = g.mix(g.rango(g.ruido(p, 1.2, det=3), 0.4, 0.7, 0.0, 0.5), color, hx("#071214"))
    rug = g.mixf(nata, 0.06, 0.6)
    altura = g.m("ADD", g.m("MULTIPLY", ondas, 0.25), g.m("MULTIPLY", nata, 0.3))
    return terminar(mat, g, color, rug, 0.0, altura, fuerza=0.12, dist=0.04, bisel=0.0)


def crear(nombre_pieza, clave, cfg):
    """Crea el material `clave` para una pieza. cfg: {"hollin": [...], "quemaduras": [...], ...}."""
    n = f"{nombre_pieza}__{clave}"
    h = cfg.get("hollin", ())
    hb = cfg.get("hollin_base", 0.0)
    if clave == "madera":
        return madera(n, hollin=h, hollin_base=hb)
    if clave == "madera_osc":
        return madera(n, "madera_osc", hollin=h, hollin_base=hb)
    if clave == "madera_mango":
        return madera(n, hollin=h, suelo=0.0, hollin_base=hb, desgaste=0.4)
    if clave == "escudo_rojo":
        return madera(n, suelo=0.0, pintura="pintura_roja", tablas=0.42, diseno=("pintura_crema", "cuartos"),
                      hollin_base=hb)
    if clave == "escudo_azul":
        return madera(n, suelo=0.0, pintura="pintura_azul", tablas=0.4, diseno=("pintura_crema", "palo", 0.2),
                      hollin_base=hb)
    if clave == "hierro":
        return hierro(n, hollin=h, hollin_base=hb, pulido=cfg.get("pulido"), huecos=cfg.get("huecos", ()))
    if clave == "hierro_herr":   # herramientas: sin polvo del suelo, más canto vivo
        return hierro(n, hollin=h, suelo=0.0, oxido=0.4, canto=1.0)
    if clave == "acero":
        return hierro(n, "acero", oxido=0.22, canto=1.0, suelo=0.0, rayado=1.0, martillado=0.25,
                      rug_base=(0.22, 0.42), mugre=0.45)
    if clave == "laton":
        return hierro(n, "laton", oxido=0.0, canto=0.7, suelo=0.0, martillado=0.4, rug_base=(0.3, 0.5))
    if clave == "cobre":
        return hierro(n, "cobre", oxido=0.0, canto=0.6, suelo=0.0, martillado=0.5, rug_base=(0.3, 0.55),
                      mugre=0.5)
    if clave == "lingote":
        return hierro(n, "acero", oxido=0.3, canto=0.8, suelo=0.0, martillado=0.7, rug_base=(0.35, 0.6),
                      mugre=0.5)
    if clave == "sillar":
        return sillar(n, hollin=h, hollin_base=hb)
    if clave == "ladrillo":
        return ladrillo(n, hollin=h)
    if clave == "ladrillo_dentro":
        return ladrillo(n, hollin=(), hollin_base=0.85, resplandor=cfg.get("resplandor"))
    if clave == "adoquin":
        return adoquin(n, hollin=h, quemaduras=cfg.get("quemaduras", ()))
    if clave == "cuero":
        return cuero(n, hollin=h)
    if clave == "brasa":
        return brasa(n)
    if clave == "carbon":
        return carbon(n)
    if clave == "agua":
        return agua(n)
    raise KeyError(clave)
