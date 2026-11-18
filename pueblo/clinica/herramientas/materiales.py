"""
Materiales procedurales de la clínica. Se usan solo para hornear el atlas: cada uno da color, rugosidad, metal,
alfa, emisión y relieve, y el horneado los pasa a las cinco texturas de 2048 (ver pipeline.py).

La historia está en los materiales:
  * Paneles blancos impecables... salvo el polvo que sube del suelo en la parte baja y se acumula en las esquinas
    del edificio (por altura, por cercanía a la esquina y por oclusión).
  * Puertas: marcas de goma negra y abolladuras en la parte baja, de las camillas que entran deprisa.
  * Rampa: bandas antideslizantes, franjas amarillas de aviso y rodadas de camilla.
"""

import bpy

# Esquinas exteriores del edificio (planta), para el polvo acumulado.
ESQ_X, ESQ_Y = 5.2, 5.0


def srgb(hexa):
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


class N:
    """Atajos para construir nodos."""

    def __init__(self, mat):
        self.mat = mat
        self.nt = mat.node_tree
        self.n = self.nt.nodes
        self.l = self.nt.links

    def nodo(self, tipo, **props):
        nd = self.n.new(tipo)
        for k, v in props.items():
            setattr(nd, k, v)
        return nd

    def link(self, a, b):
        self.l.new(a, b)

    def val(self, x):
        nd = self.nodo("ShaderNodeValue")
        nd.outputs[0].default_value = x
        return nd.outputs[0]

    def rgb(self, hexa):
        nd = self.nodo("ShaderNodeRGB")
        nd.outputs[0].default_value = (*srgb(hexa), 1)
        return nd.outputs[0]

    def _in(self, nd, i, x):
        if isinstance(x, (int, float)):
            nd.inputs[i].default_value = x
        elif isinstance(x, tuple):
            nd.inputs[i].default_value = x
        else:
            self.link(x, nd.inputs[i])

    def math(self, op, a, b=0.0, c=None, clamp=False):
        nd = self.nodo("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._in(nd, 0, a)
        self._in(nd, 1, b)
        if c is not None:
            self._in(nd, 2, c)
        return nd.outputs[0]

    def mix(self, fac, a, b):
        """Mezcla de colores (a -> b)."""
        nd = self.nodo("ShaderNodeMix", data_type="RGBA")
        self._in(nd, 0, fac)
        self._in(nd, 6, a if not isinstance(a, str) else (*srgb(a), 1))
        self._in(nd, 7, b if not isinstance(b, str) else (*srgb(b), 1))
        return nd.outputs[2]

    def mixf(self, fac, a, b):
        nd = self.nodo("ShaderNodeMix", data_type="FLOAT")
        self._in(nd, 0, fac)
        self._in(nd, 2, a)
        self._in(nd, 3, b)
        return nd.outputs[0]

    def pos(self):
        if not hasattr(self, "_pos"):
            self._pos = self.nodo("ShaderNodeNewGeometry").outputs["Position"]
        return self._pos

    def xyz(self):
        if not hasattr(self, "_xyz"):
            s = self.nodo("ShaderNodeSeparateXYZ")
            self.link(self.pos(), s.inputs[0])
            self._xyz = s.outputs
        return self._xyz

    def escalar_vec(self, v, esc):
        nd = self.nodo("ShaderNodeVectorMath", operation="MULTIPLY")
        self._in(nd, 0, v)
        nd.inputs[1].default_value = esc
        return nd.outputs[0]

    def ruido(self, escala, detalle=4.0, rug=0.55, vec=None, esc_vec=None, distor=0.0):
        nd = self.nodo("ShaderNodeTexNoise")
        nd.inputs["Scale"].default_value = escala
        nd.inputs["Detail"].default_value = detalle
        nd.inputs["Roughness"].default_value = rug
        nd.inputs["Distortion"].default_value = distor
        v = vec if vec is not None else self.pos()
        if esc_vec is not None:
            v = self.escalar_vec(v, esc_vec)
        self.link(v, nd.inputs["Vector"])
        return nd.outputs["Fac"]

    def voronoi(self, escala, vec=None, salida="Distance", feature="F1"):
        nd = self.nodo("ShaderNodeTexVoronoi", feature=feature)
        nd.inputs["Scale"].default_value = escala
        self.link(vec if vec is not None else self.pos(), nd.inputs["Vector"])
        return nd.outputs[salida]

    def rango(self, x, a, b, c=0.0, d=1.0, suave=True):
        nd = self.nodo("ShaderNodeMapRange", interpolation_type="SMOOTHSTEP" if suave else "LINEAR")
        self._in(nd, 0, x)
        nd.inputs[1].default_value = a
        nd.inputs[2].default_value = b
        nd.inputs[3].default_value = c
        nd.inputs[4].default_value = d
        return nd.outputs[0]

    def ao(self, dist=0.5):
        nd = self.nodo("ShaderNodeAmbientOcclusion", samples=8)
        nd.inputs["Distance"].default_value = dist
        return nd.outputs["AO"]

    def imagen(self, ruta, uv="deco", color=True, ext="EXTEND"):
        img = bpy.data.images.load(ruta, check_existing=True)
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        nd = self.nodo("ShaderNodeTexImage", extension=ext, interpolation="Cubic")
        nd.image = img
        u = self.nodo("ShaderNodeUVMap", uv_map=uv)
        self.link(u.outputs[0], nd.inputs[0])
        return nd

    def uv_deco(self):
        u = self.nodo("ShaderNodeUVMap", uv_map="deco")
        s = self.nodo("ShaderNodeSeparateXYZ")
        self.link(u.outputs[0], s.inputs[0])
        return s.outputs

    def relieve(self, altura, fuerza=0.3, dist=0.02, normal=None):
        nd = self.nodo("ShaderNodeBump")
        nd.inputs["Strength"].default_value = fuerza
        nd.inputs["Distance"].default_value = dist
        self._in(nd, "Height", altura)
        if normal is not None:
            self.link(normal, nd.inputs["Normal"])
        return nd.outputs[0]


# ----------------------------------------------------------------------------------------------------------------
# Piezas comunes de la historia
# ----------------------------------------------------------------------------------------------------------------


def polvo(nb, fuerza=1.0, alto=1.3, base=0.0, esquinas=True):
    """Máscara de polvo: sube del suelo, se acumula en las esquinas del edificio y en los rincones."""
    x, y, z = nb.xyz()[0], nb.xyz()[1], nb.xyz()[2]
    h = nb.math("SUBTRACT", z, base)
    m = nb.rango(h, alto, 0.0)  # 1 abajo, 0 arriba
    m = nb.math("POWER", m, 1.6)
    r = nb.ruido(2.2, 6, 0.6)
    r2 = nb.ruido(14.0, 3, 0.5)
    m = nb.math("MULTIPLY", m, nb.rango(nb.math("ADD", r, nb.math("MULTIPLY", r2, 0.35)), 0.38, 0.85, 0.25, 1.0))
    if esquinas:
        dx = nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("ABSOLUTE", x), ESQ_X))
        dy = nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("ABSOLUTE", y), ESQ_Y))
        d = nb.math("MAXIMUM", dx, dy)
        esq = nb.rango(d, 1.8, 0.0)
        alto_esq = nb.rango(h, alto * 2.2, 0.0)
        m = nb.math("ADD", m, nb.math("MULTIPLY", nb.math("MULTIPLY", esq, alto_esq), 1.2))
    rincon = nb.math("SUBTRACT", 1.0, nb.ao(0.35))
    m = nb.math("ADD", m, nb.math("MULTIPLY", nb.math("MULTIPLY", rincon, nb.rango(h, alto * 1.5, 0.0)), 0.7))
    return nb.math("MULTIPLY", m, fuerza, clamp=True)


def con_polvo(nb, color, rug, fuerza=1.0, alto=1.3, tono="#9C8B72", esquinas=True):
    m = polvo(nb, fuerza, alto, esquinas=esquinas)
    c = nb.mix(nb.math("MULTIPLY", m, 0.85), color, tono)
    r = nb.mixf(m, rug, 0.92)
    return c, r, m


# ----------------------------------------------------------------------------------------------------------------
# Biblioteca
# ----------------------------------------------------------------------------------------------------------------


def _nuevo(nombre):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    m.node_tree.nodes.clear()
    return m


def _cerrar(mat, nb, color, rug, metal=0.0, alfa=1.0, emis=None, normal=None, emis_fuerza=6.0):
    """Conecta las salidas a un Principled y guarda los sockets para hornear."""
    b = nb.nodo("ShaderNodeBsdfPrincipled")
    out = nb.nodo("ShaderNodeOutputMaterial")
    for nombre, x in (("Base Color", color), ("Roughness", rug), ("Metallic", metal), ("Alpha", alfa)):
        if isinstance(x, str):
            x = (*srgb(x), 1)
        nb._in(b, nombre, x)
    if emis is not None:
        if isinstance(emis, str):
            emis = (*srgb(emis), 1)
        nb._in(b, "Emission Color", emis)
        b.inputs["Emission Strength"].default_value = emis_fuerza
    if normal is not None:
        nb.link(normal, b.inputs["Normal"])
    nb.link(b.outputs[0], out.inputs[0])

    # Sockets de horneado: un nodo "Value"/"RGB" o el socket que ya alimenta al Principled.
    def fuente(nombre, defecto):
        ent = b.inputs[nombre]
        if ent.is_linked:
            return ent.links[0].from_socket
        v = ent.default_value
        if hasattr(v, "__len__"):
            nd = nb.nodo("ShaderNodeRGB")
            nd.outputs[0].default_value = tuple(v)
            return nd.outputs[0]
        return nb.val(v if v is not None else defecto)

    mat["_hornear"] = True
    if not isinstance(alfa, (int, float)) or alfa < 1:
        try:
            mat.surface_render_method = "BLENDED"
        except AttributeError:
            pass
    mat.diffuse_color = (*srgb("#EEEEEE"), 1)
    sockets = {
        "color": fuente("Base Color", 0.8),
        "rug": fuente("Roughness", 0.5),
        "metal": fuente("Metallic", 0.0),
        "alfa": fuente("Alpha", 1.0),
        "emis": fuente("Emission Color", 0.0) if emis is not None else nb.rgb("#000000"),
        "bsdf": b.outputs[0],
        "salida": out,
    }
    return sockets


def construir(rot):
    """rot: {nombre: ruta_png} de rotulos.generar. Devuelve ({nombre: material}, {nombre: sockets})."""
    mats, socks = {}, {}

    def reg(nombre, fn):
        m = _nuevo(nombre)
        nb = N(m)
        socks[nombre] = fn(nb)
        mats[nombre] = m

    # --- Paneles blancos de fachada: los más limpios del pueblo -------------------------------------------------
    def panel(nb):
        base = nb.mix(nb.math("MULTIPLY", nb.ruido(0.6, 2, 0.5), 0.12), "#F1F3F2", "#E2E6E5")
        c, r, m = con_polvo(nb, base, 0.3, 1.6, 1.45)
        # salpicaduras de lluvia contra el zócalo, finas
        gotas = nb.rango(nb.ruido(38.0, 2, 0.5), 0.66, 0.75)
        gotas = nb.math("MULTIPLY", gotas, nb.rango(nb.xyz()[2], 1.1, 0.45))
        c = nb.mix(nb.math("MULTIPLY", gotas, 0.5), c, "#8D7E68")
        piel = nb.math("MULTIPLY", nb.ruido(90.0, 2, 0.4), 0.15)  # piel de naranja de la pintura en polvo
        n = nb.relieve(nb.math("ADD", piel, nb.math("MULTIPLY", m, 0.3)), 0.05, 0.01)
        return _cerrar(nb.mat, nb, c, r, 0.0, normal=n)

    reg("panel", panel)

    def interior(nb):
        return _cerrar(nb.mat, nb, nb.mix(nb.math("MULTIPLY", nb.ruido(1.0), 0.1), "#DCEBE6", "#CFE0DA"),
                       0.6)

    reg("interior", interior)

    def techo_int(nb):
        return _cerrar(nb.mat, nb, "#F4F4F0", 0.7)

    reg("techo_int", techo_int)

    # --- Metales ------------------------------------------------------------------------------------------------
    def perfil_alu(nb):
        cep = nb.ruido(3.0, 8, 0.7, esc_vec=(60.0, 60.0, 0.6))  # cepillado vertical
        base = nb.mix(nb.math("MULTIPLY", cep, 0.4), "#CDD2D7", "#B6BCC2")
        c, r, m = con_polvo(nb, base, nb.mixf(cep, 0.24, 0.36), 0.9, 1.2)
        n = nb.relieve(cep, 0.08, 0.005)
        met = nb.mixf(m, 1.0, 0.2)
        return _cerrar(nb.mat, nb, c, r, met, normal=n)

    reg("perfil", perfil_alu)

    def acero(nb):
        cep = nb.ruido(4.0, 8, 0.7, esc_vec=(80.0, 2.0, 80.0))
        mancha = nb.rango(nb.ruido(3.0, 3), 0.45, 0.7)  # huellas y pulido de manos
        c = nb.mix(nb.math("MULTIPLY", cep, 0.35), "#C9CDD1", "#A9AEB4")
        r = nb.mixf(mancha, 0.18, 0.32)
        c2, r2, m = con_polvo(nb, c, r, 0.6, 0.7, esquinas=False)
        return _cerrar(nb.mat, nb, c2, r2, nb.mixf(m, 1.0, 0.3), normal=nb.relieve(cep, 0.05, 0.004))

    reg("acero", acero)

    def silicona(nb):
        c, r, _ = con_polvo(nb, "#D6D9D7", 0.55, 1.1, 1.3)
        return _cerrar(nb.mat, nb, c, r, 0.0)

    reg("silicona", silicona)

    def marco(nb):
        c, r, m = con_polvo(nb, "#F3F4F3", 0.36, 0.9, 1.1)
        return _cerrar(nb.mat, nb, c, r, 0.0, normal=nb.relieve(nb.ruido(80.0, 2), 0.03, 0.01))

    reg("marco", marco)

    def puerta(nb):
        """Marco de las puertas correderas: marcas de goma y roces en la parte baja (camillas de urgencia)."""
        x, y, z = nb.xyz()
        bajo = nb.rango(z, 1.85, 0.7)
        # rayas horizontales largas: ruido estirado en X
        rayas = nb.ruido(5.0, 6, 0.6, esc_vec=(0.25, 1.0, 9.0))
        rayas = nb.rango(rayas, 0.55, 0.68)
        golpes = nb.rango(nb.ruido(7.0, 4, 0.6), 0.6, 0.72)
        marca = nb.math("MULTIPLY", nb.math("MAXIMUM", rayas, nb.math("MULTIPLY", golpes, 0.7)), bajo)
        c, r, m = con_polvo(nb, "#F3F4F3", 0.36, 0.7, 0.9, esquinas=False)
        c = nb.mix(nb.math("MULTIPLY", marca, 0.85), c, "#2E2F31")
        # pintura saltada que deja ver el metal
        saltado = nb.math("MULTIPLY", nb.rango(nb.ruido(22.0, 3), 0.7, 0.74), bajo)
        c = nb.mix(saltado, c, "#9EA4AA")
        met = nb.mixf(saltado, 0.0, 1.0)
        r = nb.mixf(marca, r, 0.7)
        n = nb.relieve(nb.math("ADD", nb.math("MULTIPLY", marca, 0.4), nb.math("MULTIPLY", saltado, -0.6)), 0.25,
                       0.01)
        return _cerrar(nb.mat, nb, c, r, met, normal=n)

    reg("puerta", puerta)

    def zocalo_inox(nb):
        """Chapa de protección inferior de las puertas: abollada y rayada por las camillas."""
        cep = nb.ruido(4.0, 8, 0.7, esc_vec=(90.0, 2.0, 2.0))
        abol = nb.voronoi(9.0)
        abol = nb.math("MULTIPLY", nb.rango(abol, 0.0, 0.35, 1.0, 0.0), nb.rango(nb.ruido(3.0), 0.45, 0.6))
        rayas = nb.rango(nb.ruido(8.0, 6, 0.6, esc_vec=(0.2, 1.0, 14.0)), 0.6, 0.66)
        goma = nb.rango(nb.ruido(6.0, 5, 0.6, esc_vec=(0.3, 1.0, 6.0)), 0.6, 0.7)
        c = nb.mix(nb.math("MULTIPLY", cep, 0.3), "#C3C8CD", "#9EA4AA")
        c = nb.mix(nb.math("MULTIPLY", goma, 0.8), c, "#2A2B2D")
        c = nb.mix(rayas, c, "#E2E6EA")
        r = nb.mixf(goma, nb.mixf(rayas, 0.25, 0.12), 0.75)
        met = nb.mixf(goma, 1.0, 0.0)
        n = nb.relieve(nb.math("ADD", nb.math("MULTIPLY", abol, -1.0), nb.math("MULTIPLY", rayas, -0.2)), 0.5, 0.02)
        return _cerrar(nb.mat, nb, c, r, met, normal=n)

    reg("zocalo_inox", zocalo_inox)

    def caucho(nb):
        return _cerrar(nb.mat, nb, nb.mix(nb.ruido(20.0), "#1D1E20", "#2A2B2E"), 0.85, 0.0)

    reg("caucho", caucho)

    def oscuro(nb):
        return _cerrar(nb.mat, nb, "#3A3F45", 0.45, 0.6, normal=nb.relieve(nb.ruido(60.0), 0.04, 0.01))

    reg("oscuro", oscuro)

    def gris(nb):
        c, r, _ = con_polvo(nb, "#A4AAAF", 0.45, 0.7, 1.0)
        return _cerrar(nb.mat, nb, c, r, 0.3)

    reg("gris", gris)

    def poste(nb):
        c, r, m = con_polvo(nb, "#ECEEED", 0.4, 1.2, 1.4, esquinas=False)
        return _cerrar(nb.mat, nb, c, r, 0.0)

    reg("poste", poste)

    # --- Hormigón -------------------------------------------------------------------------------------------------
    def zocalo(nb):
        poros = nb.math("SUBTRACT", 1.0, nb.rango(nb.voronoi(40.0), 0.0, 0.08))
        base = nb.mix(nb.math("MULTIPLY", nb.ruido(1.5, 4), 0.25), "#E6E4DE", "#D4D1C8")
        c, r, m = con_polvo(nb, base, 0.78, 1.35, 0.55, "#8F7F67")
        c = nb.mix(nb.math("MULTIPLY", poros, 0.25), c, "#B5B1A6")
        n = nb.relieve(nb.math("ADD", nb.math("MULTIPLY", poros, -0.5), nb.ruido(25.0, 4)), 0.2, 0.01)
        return _cerrar(nb.mat, nb, c, r, 0.0, normal=n)

    reg("zocalo", zocalo)

    def rampa(nb):
        x, y, z = nb.xyz()
        # bandas antideslizantes transversales (cada 0,25 studs)
        banda = nb.math("SINE", nb.math("MULTIPLY", y, 25.13))
        banda = nb.rango(banda, 0.3, 0.6)
        arido = nb.ruido(55.0, 4, 0.7)
        base = nb.mix(nb.math("MULTIPLY", nb.ruido(1.2, 4), 0.3), "#ABA8A1", "#96938B")
        base = nb.mix(nb.math("MULTIPLY", banda, 0.25), base, "#85827B")
        # franjas amarillas de aviso al principio y al final de la rampa
        fr = nb.math("MAXIMUM", nb.rango(nb.math("ABSOLUTE", nb.math("SUBTRACT", y, -6.65)), 0.18, 0.12),
                     nb.rango(nb.math("ABSOLUTE", nb.math("SUBTRACT", y, -11.0)), 0.18, 0.12))
        gasta = nb.rango(nb.ruido(9.0, 4), 0.35, 0.65)
        base = nb.mix(nb.math("MULTIPLY", fr, gasta), base, "#E4B321")
        # rodadas de camilla: dos pares de líneas a lo largo de la rampa
        rod = nb.math("ABSOLUTE", nb.math("SINE", nb.math("MULTIPLY", nb.math("ADD", x, 1.2), 3.6)))
        rod = nb.math("MULTIPLY", nb.rango(rod, 0.97, 1.0), nb.rango(nb.ruido(4.0, 3, 0.5, esc_vec=(1, 0.15, 1)),
                                                                     0.45, 0.65))
        rod = nb.math("MULTIPLY", rod, nb.rango(nb.math("ABSOLUTE", nb.math("ADD", x, 1.2)), 1.6, 1.2))
        base = nb.mix(nb.math("MULTIPLY", rod, 0.55), base, "#3A3936")
        c, r, m = con_polvo(nb, base, nb.mixf(banda, 0.82, 0.95), 0.6, 0.5, esquinas=False)
        n = nb.relieve(nb.math("ADD", nb.math("MULTIPLY", banda, 0.6), nb.math("MULTIPLY", arido, 0.5)), 0.35, 0.02)
        return _cerrar(nb.mat, nb, c, r, 0.0, normal=n)

    reg("rampa", rampa)

    def membrana(nb):
        parches = nb.rango(nb.ruido(0.8, 4), 0.45, 0.6)
        c = nb.mix(nb.math("MULTIPLY", parches, 0.35), "#BFC2C2", "#A5A8A6")
        charco = nb.rango(nb.ruido(0.5, 2), 0.62, 0.66)
        c = nb.mix(nb.math("MULTIPLY", charco, 0.3), c, "#8E8A80")
        n = nb.relieve(nb.ruido(30.0, 5, 0.6), 0.15, 0.01)
        return _cerrar(nb.mat, nb, c, nb.mixf(charco, 0.9, 0.55), 0.0, normal=n)

    reg("membrana", membrana)

    def vinilo(nb):
        motas = nb.rango(nb.ruido(70.0, 2), 0.62, 0.7)
        c = nb.mix(motas, "#C9D2CE", "#9FAAA6")
        return _cerrar(nb.mat, nb, c, 0.35, 0.0)

    reg("vinilo", vinilo)

    # --- Cristales (alfa en el atlas) -------------------------------------------------------------------------------
    def cristal(nb):
        return _cerrar(nb.mat, nb, "#CFE4E8", 0.05, 0.0, alfa=0.25)

    reg("cristal", cristal)

    def esmerilado(nb):
        return _cerrar(nb.mat, nb, nb.mix(nb.ruido(40.0), "#EEF3F4", "#E3EAEC"), 0.6, 0.0, alfa=0.86)

    reg("esmerilado", esmerilado)

    def cristal_puerta(nb):
        """Cristal de las puertas: franja esmerilada horizontal a la altura de los ojos."""
        z = nb.xyz()[2]
        franja = nb.math("MULTIPLY", nb.rango(z, 2.75, 2.8, 0, 1, False), nb.rango(z, 4.05, 4.0, 0, 1, False))
        # rayitas finas en el borde de la franja (decorativas, más claras)
        lineas = nb.math("MULTIPLY", nb.rango(nb.math("SINE", nb.math("MULTIPLY", z, 120.0)), 0.9, 1.0),
                         nb.math("SUBTRACT", 1.0, franja))
        lineas = nb.math("MULTIPLY", lineas, nb.math("ADD", nb.rango(z, 2.55, 2.75, 0, 1, False),
                                                     0.0))
        lineas = nb.math("MULTIPLY", lineas, nb.rango(z, 2.75, 2.7))
        f = nb.math("MAXIMUM", franja, lineas)
        c = nb.mix(f, "#CFE4E8", "#F1F5F6")
        return _cerrar(nb.mat, nb, c, nb.mixf(f, 0.05, 0.6), 0.0, alfa=nb.mixf(f, 0.22, 0.88))

    reg("cristal_puerta", cristal_puerta)

    def cristal_frontal(nb):
        """Ventana frontal: esmerilada de abajo hasta 2/3 (se ve la luz, no el interior) con degradado de puntos."""
        z = nb.xyz()[2]
        x = nb.xyz()[0]
        corte = 3.95
        pts = nb.voronoi(30.0, salida="Distance")
        grad = nb.rango(z, corte + 0.35, corte - 0.05, 0, 1, False)
        f = nb.math("GREATER_THAN", grad, nb.math("MULTIPLY", pts, 1.8))
        f = nb.math("MAXIMUM", f, nb.rango(z, corte, corte - 0.01, 0, 1, False))
        c = nb.mix(f, "#CFE4E8", "#F1F5F6")
        return _cerrar(nb.mat, nb, c, nb.mixf(f, 0.05, 0.6), 0.0, alfa=nb.mixf(f, 0.22, 0.88))

    reg("cristal_frontal", cristal_frontal)

    # --- Colores sueltos --------------------------------------------------------------------------------------------
    def plano(nombre, hexa, rug, metal=0.0, pol=0.0):
        def f(nb):
            if pol:
                c, r, _ = con_polvo(nb, hexa, rug, pol, 1.0, esquinas=False)
                return _cerrar(nb.mat, nb, c, r, metal)
            return _cerrar(nb.mat, nb, hexa, rug, metal)
        reg(nombre, f)

    plano("rojo", "#C0252B", 0.38, 0.0, 0.4)
    plano("blanco_puro", "#F6F6F4", 0.4)
    plano("negro_mate", "#232528", 0.7)
    plano("tierra", "#3B2B1F", 0.95)
    plano("ceramica", "#EEEBE5", 0.25)
    plano("amarillo", "#E7B526", 0.5)
    plano("mostrador", "#7FB7AE", 0.45)
    plano("asiento", "#3E8C83", 0.5)

    def hoja(nb):
        v = nb.ruido(6.0, 3)
        c = nb.mix(v, "#4D7E36", "#6E9A45")
        venas = nb.rango(nb.ruido(30.0, 2, 0.4, esc_vec=(1, 1, 8)), 0.6, 0.7)
        c = nb.mix(nb.math("MULTIPLY", venas, 0.3), c, "#A7C77C")
        return _cerrar(nb.mat, nb, c, 0.55, 0.0, normal=nb.relieve(venas, 0.1, 0.01))

    reg("hoja", hoja)

    def solar(nb):
        """Celdas del panel solar: rejilla de células con buses plateados (por UV deco)."""
        u, v = nb.uv_deco()[0], nb.uv_deco()[1]
        fu = nb.math("FRACT", nb.math("MULTIPLY", u, 10.0))
        fv = nb.math("FRACT", nb.math("MULTIPLY", v, 6.0))
        borde = nb.math("MAXIMUM", nb.rango(nb.math("ABSOLUTE", nb.math("SUBTRACT", fu, 0.5)), 0.46, 0.48),
                        nb.rango(nb.math("ABSOLUTE", nb.math("SUBTRACT", fv, 0.5)), 0.46, 0.48))
        bus = nb.rango(nb.math("ABSOLUTE", nb.math("SUBTRACT", nb.math("FRACT", nb.math("MULTIPLY", u, 30.0)),
                                                   0.5)), 0.47, 0.49)
        c = nb.mix(nb.math("MULTIPLY", nb.ruido(3.0), 0.3), "#16264A", "#22355F")
        c = nb.mix(nb.math("MULTIPLY", bus, 0.6), c, "#8A93A3")
        c = nb.mix(borde, c, "#D9DEE5")
        pol = nb.math("MULTIPLY", nb.rango(nb.ruido(1.2, 4), 0.5, 0.8), 0.5)
        c = nb.mix(pol, c, "#8F8678")
        return _cerrar(nb.mat, nb, c, nb.mixf(pol, 0.08, 0.7), nb.mixf(borde, 0.1, 0.9),
                       normal=nb.relieve(borde, 0.2, 0.01))

    reg("solar", solar)

    def rejilla(nb):
        return _cerrar(nb.mat, nb, "#2C2F33", 0.55, 0.5)

    reg("rejilla", rejilla)

    def hvac(nb):
        c, r, m = con_polvo(nb, "#E8EBEA", 0.42, 0.8, 7.6, esquinas=False)
        # suciedad que escurre de las rejillas
        z = nb.xyz()[2]
        esc = nb.math("MULTIPLY", nb.rango(nb.ruido(4.0, 4, 0.6, esc_vec=(6, 6, 0.4)), 0.55, 0.7), 0.35)
        c = nb.mix(esc, c, "#9A9283")
        return _cerrar(nb.mat, nb, c, r, 0.0)

    reg("hvac", hvac)

    def banco_asiento(nb):
        """Chapa perforada del banco (agujeros por relieve y color)."""
        x, y, z = nb.xyz()
        vec = nb.nodo("ShaderNodeCombineXYZ")
        nb.link(x, vec.inputs[0])
        nb.link(nb.math("ADD", y, z), vec.inputs[1])
        g = nb.nodo("ShaderNodeVectorMath", operation="FRACTION")
        nb.link(nb.escalar_vec(vec.outputs[0], (9.0, 9.0, 0.0)), g.inputs[0])
        d = nb.nodo("ShaderNodeVectorMath", operation="DISTANCE")
        nb.link(g.outputs[0], d.inputs[0])
        d.inputs[1].default_value = (0.5, 0.5, 0.0)
        agujero = nb.rango(d.outputs["Value"], 0.26, 0.22)
        c, r, _ = con_polvo(nb, "#F2F3F2", 0.38, 0.5, 1.6, esquinas=False)
        c = nb.mix(agujero, c, "#4A4C4F")
        return _cerrar(nb.mat, nb, c, r, 0.0, normal=nb.relieve(nb.math("MULTIPLY", agujero, -1.0), 0.6,
                                                                         0.02))

    reg("banco_asiento", banco_asiento)

    # --- Rótulos ----------------------------------------------------------------------------------------------------
    def placa(nb):
        """Placa de latón cepillado con el texto grabado (surco oscuro + relieve)."""
        img = nb.imagen(rot["placa_grabado"], color=False)
        g = img.outputs["Color"]
        g = nb.rango(g, 0.08, 0.45, 0.0, 1.0, False)  # surco nítido
        cep = nb.ruido(4.0, 8, 0.7, esc_vec=(1.0, 80.0, 80.0))
        base = nb.mix(nb.math("MULTIPLY", cep, 0.35), "#C9CED3", "#AEB4BA")
        c = nb.mix(g, base, "#2B2E33")
        return _cerrar(nb.mat, nb, c, nb.mixf(g, 0.25, 0.6), nb.mixf(g, 1.0, 0.3),
                       normal=nb.relieve(nb.math("MULTIPLY", g, -1.0), 0.9, 0.01))

    reg("placa", placa)

    def imagen_mat(nombre, clave, rug=0.4, metal=0.0, emis=False, pol=0.0):
        def f(nb):
            img = nb.imagen(rot[clave])
            c = img.outputs["Color"]
            if pol:
                c2, r, _ = con_polvo(nb, c, rug, pol, 1.6, esquinas=False)
                c = c2
            return _cerrar(nb.mat, nb, c, rug, metal, emis=c if emis else None, emis_fuerza=3.0)
        reg(nombre, f)

    imagen_mat("rot_solo_personal", "solo_personal", 0.35)
    imagen_mat("rot_parking_p", "parking_p", 0.3, pol=0.3)
    imagen_mat("rot_parking_sub", "parking_sub", 0.3, pol=0.3)
    imagen_mat("rot_horario", "horario", 0.8)
    imagen_mat("rot_medidor", "medidor", 0.2, emis=True)
    imagen_mat("rot_gel", "gel", 0.4)
    imagen_mat("rot_residuos", "residuos", 0.45)
    imagen_mat("rot_cartel", "cartel_interior", 0.6)

    def teclado(nb):
        img = nb.imagen(rot["teclado"], color=False)
        g = img.outputs["Color"]
        c = nb.mix(g, "#B9BEC3", "#1E2024")
        return _cerrar(nb.mat, nb, c, 0.35, nb.mixf(g, 0.9, 0.0),
                       normal=nb.relieve(nb.math("MULTIPLY", g, -1.0), 0.4, 0.005))

    reg("teclado", teclado)

    def botiquin_texto(nb):
        img = nb.imagen(rot["botiquin_texto"], color=False)
        g = img.outputs["Color"]
        c, r, _ = con_polvo(nb, "#C0252B", 0.38, 0.4, 1.0, esquinas=False)
        return _cerrar(nb.mat, nb, nb.mix(g, c, "#F6F6F4"), r, 0.0)

    reg("botiquin_texto", botiquin_texto)

    # --- Neón (en Roblox: Material Neon; aquí emisión) --------------------------------------------------------------
    def neon(nombre, hexa, fuerza=8.0):
        def f(nb):
            return _cerrar(nb.mat, nb, hexa, 0.3, 0.0, emis=hexa, emis_fuerza=fuerza)
        reg(nombre, f)

    neon("neon_blanco", "#FFFFFF", 10.0)
    neon("neon_calido", "#FFE1B5", 8.0)
    neon("neon_verde", "#5CFF9A", 6.0)
    neon("neon_rojo", "#FF2E2E", 8.0)
    return mats, socks
