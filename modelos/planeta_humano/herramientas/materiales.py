"""
Materiales procedurales del Planeta Humano.

Cada material es un Principled BSDF con color, rugosidad, metal, relieve (bump) y, si brilla, emisión. Los patrones
usan coordenadas de objeto (studs), así que el dibujo es continuo entre islas UV: al hornear no quedan costuras.
Luego `horneado.py` los pasa al atlas 1024 (color, normal, rugosidad, metal y emisión).
"""

import bpy

CYAN = "#3DF2FF"  # neón humano


def srgb(hexa):
    """'#RRGGBB' -> color lineal."""
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def _m(color, rug=0.5, metal=0.0, patron="liso", **kw):
    d = dict(color=color, rug=rug, metal=metal, patron=patron)
    d.update(kw)
    return d


def _neon(color, parte):
    return dict(color=color, rug=0.3, metal=0.0, patron="plano", emis=color, parte=parte)


# Paleta. `parte` dice en qué malla va por defecto: las que brillan van a *_neon, el cristal a *_cristal, etc.
PALETA = {
    # Metal pintado y desnudo
    "blanco": _m("#E6EAEE", 0.42, 0.25, "paneles"),
    "blanco_liso": _m("#E6EAEE", 0.42, 0.25),
    "gris": _m("#9AA3AD", 0.45, 0.5, "paneles"),
    "gris_liso": _m("#9AA3AD", 0.45, 0.5),
    "gris_claro": _m("#C3CAD1", 0.42, 0.4),
    "oscuro": _m("#3A4048", 0.5, 0.7, "ruido", tam=2.5, fuerza=0.25, relieve=0.15),
    "oscuro_paneles": _m("#3A4048", 0.5, 0.7, "paneles"),
    "negro": _m("#17191D", 0.6, 0.3),
    "acero": _m("#B8BEC6", 0.3, 1.0, "cepillado"),
    "cromo": _m("#D9DEE3", 0.12, 1.0),
    "hierro": _m("#2B2D31", 0.55, 1.0, "ruido", tam=5, fuerza=0.45, relieve=0.5, color2="#4A3A30"),
    "hierro_viejo": _m("#4A4743", 0.7, 0.9, "ruido", tam=4, fuerza=0.6, relieve=0.6, color2="#6B4630"),
    "cobre": _m("#B87333", 0.35, 1.0, "cepillado"),
    "oro": _m("#D9A441", 0.3, 1.0),
    "bronce": _m("#8C6A3B", 0.4, 1.0, "ruido", tam=3, fuerza=0.35, relieve=0.2, color2="#4F7A66"),
    "acento": _m("#1FB7C9", 0.4, 0.3),
    "naranja_p": _m("#E8762B", 0.45, 0.2),
    "rojo_p": _m("#C8352B", 0.45, 0.2),
    "amarillo_p": _m("#E6B422", 0.45, 0.2),
    "verde_p": _m("#3E9B4F", 0.45, 0.2),
    "azul_p": _m("#2F5FB3", 0.45, 0.2),
    "rayas": _m("#E6B422", 0.5, 0.2, "rayas", color2="#17191D", tam=0.6),
    "rejilla": _m("#7C858F", 0.6, 0.8, "paneles", tam=0.22, ancho=0.3, relieve=0.8),
    "chapa": _m("#AEB6BE", 0.4, 0.9, "ondas", tam=0.5),
    "goma": _m("#1B1B1D", 0.9, 0.0, "ruido", tam=8, fuerza=0.2, relieve=0.3),
    "plastico": _m("#EEF1F3", 0.35, 0.0),
    "plastico_negro": _m("#222428", 0.4, 0.0),
    "panel_solar": _m("#10224A", 0.2, 0.6, "paneles", tam=0.5, ancho=0.12, color2="#AEB9C6", relieve=0.3),
    "pantalla": _m("#0B1418", 0.1, 0.2),
    "hormigon": _m("#A7A9A8", 0.85, 0.0, "ruido", tam=3, fuerza=0.3, relieve=0.35),
    # Cristal y agua
    "cristal": _m("#7FE6F2", 0.08, 0.0, "plano", parte="cristal"),
    "cristal_oscuro": _m("#1C3B4A", 0.08, 0.2, "plano", parte="cristal"),
    "agua": _m("#3FA7C9", 0.06, 0.0, "agua", parte="agua"),
    # Neón
    "neon": _neon(CYAN, "neon"),
    "neon_naranja": _neon("#FF7A1A", "naranja_neon"),
    "neon_verde": _neon("#4DFF7A", "verde_neon"),
    "neon_rojo": _neon("#FF3B3B", "rojo_neon"),
    "neon_azul": _neon("#3D7BFF", "azul_neon"),
    "neon_rosa": _neon("#FF4DD2", "rosa_neon"),
    "neon_amarillo": _neon("#FFD23D", "amarillo_neon"),
    "neon_blanco": _neon("#F4FBFF", "blanco_luz"),
    # Orgánico
    "madera": _m("#8A5A33", 0.7, 0.0, "madera", color2="#5E3B20"),
    "madera_clara": _m("#B98A55", 0.7, 0.0, "madera", color2="#8E6238"),
    "madera_oscura": _m("#4E321E", 0.75, 0.0, "madera", color2="#2E1C10"),
    "corteza": _m("#5B4332", 0.9, 0.0, "corteza", color2="#2F2219"),
    "corteza_gris": _m("#70767C", 0.7, 0.35, "corteza", color2="#3E4A52"),
    "corteza_palma": _m("#7A6A50", 0.85, 0.0, "corteza", color2="#4A3E2C"),
    "hoja": _m("#3F8F45", 0.7, 0.0, "hojas", color2="#27602F"),
    "hoja2": _m("#2E6F3A", 0.7, 0.0, "hojas", color2="#1B4826"),
    "hoja_clara": _m("#6BB84F", 0.7, 0.0, "hojas", color2="#3F8F45"),
    "hoja_cyan": _m("#3FD9C9", 0.55, 0.0, "hojas", color2="#1E9C93"),
    "hoja_azul": _m("#2FA59A", 0.6, 0.0, "hojas", color2="#1B6E78"),
    "cesped": _m("#4FA243", 0.85, 0.0, "hojas", color2="#356F2E"),
    "cesped_alien": _m("#2FB8A0", 0.8, 0.0, "hojas", color2="#1C7A86"),
    "piedra": _m("#8C8F93", 0.9, 0.0, "piedra", color2="#5F6266"),
    "piedra_oscura": _m("#5E6166", 0.9, 0.0, "piedra", color2="#3A3C40"),
    "piedra_clara": _m("#BDBAB2", 0.85, 0.0, "piedra", color2="#8F8C85"),
    "musgo": _m("#5C7F3A", 0.95, 0.0, "ruido", tam=6, fuerza=0.5, relieve=0.6, color2="#35521F"),
    "tierra": _m("#4A3526", 0.95, 0.0, "ruido", tam=7, fuerza=0.5, relieve=0.7, color2="#2B1E15"),
    "carbon": _m("#1A1716", 0.9, 0.0, "piedra", color2="#3A2A22"),
    # Telas
    "tela_roja": _m("#B5332E", 0.9, 0.0, "tejido"),
    "tela_azul": _m("#2D5FA8", 0.9, 0.0, "tejido"),
    "tela_verde": _m("#3F8F55", 0.9, 0.0, "tejido"),
    "tela_amarilla": _m("#E0B43A", 0.9, 0.0, "tejido"),
    "tela_blanca": _m("#E9E6DD", 0.9, 0.0, "tejido"),
    "tela_morada": _m("#7A3FA0", 0.9, 0.0, "tejido"),
    "tela_cyan": _m("#2BB6C4", 0.9, 0.0, "tejido"),
    "tela_naranja": _m("#E07B2E", 0.9, 0.0, "tejido"),
    "tela_rayas": _m("#E9E6DD", 0.9, 0.0, "rayas_rectas", color2="#1FA3B5", tam=0.5),
}


def spec(nombre):
    """Especificación del material. Los nombres 'c:#RRGGBB:rug:metal' crean un color liso a medida."""
    if nombre in PALETA:
        return PALETA[nombre]
    if nombre.startswith("c:"):
        p = nombre.split(":")
        return _m(p[1], float(p[2]) if len(p) > 2 else 0.5, float(p[3]) if len(p) > 3 else 0.0)
    raise KeyError(f"material desconocido: {nombre}")


def color_a_medida(hexa, rug=0.5, metal=0.0):
    return f"c:{hexa}:{rug}:{metal}"


# --------------------------------------------------------------------------------------------------------------
# Constructor de nodos
# --------------------------------------------------------------------------------------------------------------


class _G:
    def __init__(self, nt):
        self.nt = nt

    def _pon(self, entrada, v):
        if hasattr(v, "is_output"):
            self.nt.links.new(v, entrada)
        else:
            entrada.default_value = v

    def mat(self, op, a, b=None, c=None):
        n = self.nt.nodes.new("ShaderNodeMath")
        n.operation = op
        self._pon(n.inputs[0], a)
        if b is not None:
            self._pon(n.inputs[1], b)
        if c is not None:
            self._pon(n.inputs[2], c)
        return n.outputs[0]

    def mezcla(self, fac, a, b, modo="MIX"):
        n = self.nt.nodes.new("ShaderNodeMix")
        n.data_type = "RGBA"
        n.blend_type = modo
        n.clamp_factor = True
        ent = {s.identifier: s for s in n.inputs}
        self._pon(ent["Factor_Float"], fac)
        self._pon(ent["A_Color"], a)
        self._pon(ent["B_Color"], b)
        return {s.identifier: s for s in n.outputs}["Result_Color"]

    def rgb(self, c):
        n = self.nt.nodes.new("ShaderNodeRGB")
        n.outputs[0].default_value = (*c, 1.0)
        return n.outputs[0]

    def coord(self):
        return self.nt.nodes.new("ShaderNodeTexCoord").outputs["Object"]

    def mapeo(self, vec, escala=(1, 1, 1), pos=(0, 0, 0)):
        n = self.nt.nodes.new("ShaderNodeMapping")
        n.inputs["Scale"].default_value = escala
        n.inputs["Location"].default_value = pos
        self.nt.links.new(vec, n.inputs["Vector"])
        return n.outputs[0]

    def ruido(self, vec, escala, detalle=3.0, rug=0.55):
        n = self.nt.nodes.new("ShaderNodeTexNoise")
        self.nt.links.new(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = escala
        n.inputs["Detail"].default_value = detalle
        n.inputs["Roughness"].default_value = rug
        return n.outputs[0]

    def voronoi(self, vec, escala):
        n = self.nt.nodes.new("ShaderNodeTexVoronoi")
        n.feature = "F1"
        self.nt.links.new(vec, n.inputs["Vector"])
        n.inputs["Scale"].default_value = escala
        return n.outputs["Distance"]

    def xyz(self, vec):
        n = self.nt.nodes.new("ShaderNodeSeparateXYZ")
        self.nt.links.new(vec, n.inputs[0])
        return n.outputs

    def normal(self):
        return self.nt.nodes.new("ShaderNodeNewGeometry").outputs["Normal"]

    def rango(self, v, a, b):
        """smoothstep(a, b, v)"""
        n = self.nt.nodes.new("ShaderNodeMapRange")
        n.interpolation_type = "SMOOTHSTEP"
        self.nt.links.new(v, n.inputs["Value"])
        n.inputs["From Min"].default_value = a
        n.inputs["From Max"].default_value = b
        return n.outputs[0]


def _oscurecer(c, k):
    return tuple(x * k for x in c)


def crear_material(nombre, esc=1.0):
    """Crea el material `nombre` de la paleta. `esc` ajusta el tamaño de los patrones al tamaño del modelo."""
    if nombre in bpy.data.materials:
        return bpy.data.materials[nombre]
    sp = spec(nombre)
    mat = bpy.data.materials.new(nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    b = nt.nodes["Principled BSDF"]
    g = _G(nt)
    color = srgb(sp["color"])
    color2 = srgb(sp["color2"]) if sp.get("color2") else _oscurecer(color, 0.5)
    rug, metal, patron = sp["rug"], sp["metal"], sp["patron"]
    mat.diffuse_color = (*color, 1.0)
    b.inputs["Metallic"].default_value = metal
    mat["parte"] = sp.get("parte", "base")

    if sp.get("emis"):
        e = srgb(sp["emis"])
        b.inputs["Base Color"].default_value = (*e, 1.0)
        b.inputs["Emission Color"].default_value = (*e, 1.0)
        b.inputs["Emission Strength"].default_value = 4.0
        b.inputs["Roughness"].default_value = rug
        return mat
    if patron == "plano":
        b.inputs["Base Color"].default_value = (*color, 1.0)
        b.inputs["Roughness"].default_value = rug
        return mat

    co = g.coord()
    tam = sp.get("tam")
    fac = None        # máscara del patrón (0..1) que mezcla color -> color2
    alt = None        # altura para el relieve
    drug = 0.0        # cuánto sube la rugosidad donde hay patrón
    fuerza_relieve = sp.get("relieve", 0.15)
    dist_relieve = 0.04 * esc

    if patron == "liso":
        alt = g.ruido(co, 9.0 / esc, 2.0)
        fuerza_relieve = sp.get("relieve", 0.06)
    elif patron == "paneles":
        t = (tam or 2.0) * esc if tam is None else tam * max(esc, 0.6)
        ancho = sp.get("ancho", 0.045 * esc / t if True else 0)  # fracción de la celda
        ancho = max(ancho, 0.012)
        p = g.xyz(g.mapeo(co, (1 / t, 1 / t, 1 / t), (0.137, 0.291, 0.173)))
        nrm = g.xyz(g.normal())
        lineas = None
        for i in range(3):
            d = g.mat("ABSOLUTE", g.mat("SUBTRACT", g.mat("FRACT", p[i]), 0.5))
            lin = g.rango(d, 0.5 - ancho, 0.5 - ancho * 0.35)
            cara = g.mat("LESS_THAN", g.mat("ABSOLUTE", nrm[i]), 0.9)
            lin = g.mat("MULTIPLY", lin, cara)
            lineas = lin if lineas is None else g.mat("MAXIMUM", lineas, lin)
        fac = lineas
        alt = g.mat("SUBTRACT", 1.0, lineas)
        drug = 0.25
        fuerza_relieve = sp.get("relieve", 0.7)
        if not sp.get("color2"):
            color2 = _oscurecer(color, 0.38)
    elif patron == "ruido":
        n = g.ruido(co, (tam or 3.0) / esc, 4.0)
        fac = g.mat("MULTIPLY", g.rango(n, 0.35, 0.7), sp.get("fuerza", 0.4))
        alt = n
        drug = 0.15
    elif patron == "piedra":
        n = g.ruido(co, 1.6 / esc, 6.0, 0.65)
        v = g.voronoi(co, 2.2 / esc)
        fac = g.rango(n, 0.35, 0.72)
        alt = g.mat("ADD", g.mat("MULTIPLY", n, 0.7), g.mat("MULTIPLY", v, 0.5))
        fuerza_relieve = sp.get("relieve", 1.0)
        dist_relieve = 0.12 * esc
        drug = 0.05
    elif patron == "corteza":
        v = g.mapeo(co, (5.0 / esc, 5.0 / esc, 0.6 / esc))
        n = g.ruido(v, 1.0, 5.0, 0.6)
        fac = g.rango(n, 0.3, 0.65)
        alt = n
        fuerza_relieve = sp.get("relieve", 1.0)
        dist_relieve = 0.15 * esc
    elif patron == "madera":
        v = g.mapeo(co, (0.5 / esc, 7.0 / esc, 7.0 / esc))
        n = g.ruido(v, 1.0, 3.0, 0.5)
        fac = g.rango(n, 0.35, 0.7)
        alt = n
        fuerza_relieve = sp.get("relieve", 0.45)
        drug = 0.1
    elif patron == "cepillado":
        v = g.mapeo(co, (0.6 / esc, 40.0 / esc, 40.0 / esc))
        n = g.ruido(v, 1.0, 2.0)
        fac = g.mat("MULTIPLY", g.rango(n, 0.3, 0.7), 0.18)
        alt = n
        fuerza_relieve = 0.08
        drug = 0.25
    elif patron == "ondas":  # chapa ondulada
        t = (tam or 0.5) * esc
        p = g.xyz(g.mapeo(co, (1 / t, 1 / t, 1 / t)))
        s = g.mat("SINE", g.mat("MULTIPLY", p[0], 6.2832))
        alt = g.mat("ADD", g.mat("MULTIPLY", s, 0.5), 0.5)
        fac = g.mat("MULTIPLY", g.mat("SUBTRACT", 1.0, alt), 0.35)
        fuerza_relieve = 1.0
        dist_relieve = 0.08 * esc
    elif patron in ("rayas", "rayas_rectas"):
        t = (tam or 0.6) * max(esc, 0.5)
        p = g.xyz(co)
        s = g.mat("ADD", p[0], p[2]) if patron == "rayas" else p[0]
        if patron == "rayas":
            s = g.mat("ADD", s, p[1])
        f = g.mat("FRACT", g.mat("DIVIDE", s, t))
        fac = g.rango(f, 0.47, 0.53)
        alt = g.ruido(co, 9.0 / esc, 2.0)
        fuerza_relieve = 0.06
    elif patron == "hojas":
        n = g.ruido(co, 3.5 / esc, 3.0)
        fac = g.rango(n, 0.3, 0.7)
        alt = n
        fuerza_relieve = sp.get("relieve", 0.5)
        dist_relieve = 0.06 * esc
    elif patron == "agua":
        n = g.ruido(co, 2.5 / esc, 3.0)
        fac = g.mat("MULTIPLY", g.rango(n, 0.4, 0.8), 0.4)
        color2 = tuple(min(1.0, x * 1.6 + 0.05) for x in color)
        alt = n
        fuerza_relieve = 0.5
        dist_relieve = 0.08 * esc
    elif patron == "tejido":
        v = g.mapeo(co, (30.0 / esc, 30.0 / esc, 30.0 / esc))
        n = g.ruido(v, 1.0, 1.0)
        n2 = g.ruido(co, 1.5 / esc, 2.0)
        fac = g.mat("MULTIPLY", g.rango(n2, 0.3, 0.7), 0.35)
        alt = n
        fuerza_relieve = 0.3
    else:
        raise ValueError(patron)

    # Color: patrón + suciedad suave a gran escala (da vida a las superficies lisas).
    col = g.rgb(color)
    if fac is not None:
        col = g.mezcla(fac, col, g.rgb(color2))
    suciedad = g.rango(g.ruido(co, 0.9 / esc, 4.0, 0.6), 0.42, 0.75)
    col = g.mezcla(g.mat("MULTIPLY", suciedad, 0.22), col, g.rgb((0.35, 0.35, 0.36)), "MULTIPLY")
    nt.links.new(col, b.inputs["Base Color"])

    # Rugosidad
    r = g.mat("ADD", rug, g.mat("MULTIPLY", g.mat("SUBTRACT", suciedad, 0.3), 0.14))
    if fac is not None and drug:
        r = g.mat("ADD", r, g.mat("MULTIPLY", fac, drug))
    r = g.mat("MINIMUM", g.mat("MAXIMUM", r, 0.03), 1.0)
    nt.links.new(r, b.inputs["Roughness"])

    # Relieve
    if alt is not None and fuerza_relieve > 0:
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = min(1.0, fuerza_relieve)
        bump.inputs["Distance"].default_value = dist_relieve
        nt.links.new(alt, bump.inputs["Height"])
        nt.links.new(bump.outputs[0], b.inputs["Normal"])
    return mat
