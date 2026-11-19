"""
Materiales procedurales (Cycles) que se hornean al atlas. Trabajan en coordenadas del mundo, en studs.

Cada material se describe con un `Mat` (color, rugosidad, metal y capas de historia: suciedad, chorretones,
óxido, arañazos, bordes gastados, franjas de peligro, relieve, calcos pintados, emisión, transparencia).
`construir()` crea el árbol de nodos y deja preparadas cinco salidas para hornear con «EMIT»:
    color, rugosidad, metal, emision, alfa
y la salida «render» (Principled completo), que es la que se usa para hornear las normales (el relieve y el bisel
del sombreador quedan en el mapa de normales).
"""

from dataclasses import dataclass, field

import bpy

REGISTRO = {}  # nombre -> {'mat', 'salidas': {modo: socket}, 'out', 'bsdf', 'emi'}


def srgb(hexa):
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


@dataclass
class Calco:
    """Imagen proyectada en plano. origen = centro; U, V = ejes del plano (unitarios); tam = (ancho, alto) studs."""
    imagen: str
    origen: tuple
    U: tuple
    V: tuple
    tam: tuple
    profundidad: float = 0.3
    modo: str = "pintura"        # pintura | multiplicar | brillo | emision | aranazo
    rugosidad: float = 0.55
    fuerza: float = 1.0          # opacidad (o emisión)
    desgaste: float = 0.0        # 0..1: desconchones extra con ruido


@dataclass
class Mat:
    nombre: str
    color: str
    rug: float = 0.6
    metal: float = 0.0
    ruido: float = 0.08            # variación de color (manchas suaves)
    escala_ruido: float = 1.2
    sucio: float = 0.0             # mugre general + oscurecido cerca del suelo
    z_suelo: float = 0.0           # altura del suelo de referencia para la mugre
    chorretones: float = 0.0       # regueros verticales (agua que cae del tejado)
    oxido: float = 0.0
    color_oxido: str = "#6E3B1F"
    rayas: float = 0.0             # arañazos horizontales (contenedores rozando)
    z_rayas: float = 2.0           # por debajo de esta altura hay arañazos
    color_rayas: str = "#B9BEC2"
    bordes: float = 0.0            # bordes gastados (pintura saltada en las aristas)
    color_bordes: str = "#9DA3A8"
    bisel: float = 0.025           # radio del bisel del sombreador (studs) -> brillo en aristas en el mapa de normales
    relieve: tuple = None          # ('lagrimada', escala_studs, fuerza) | ('ruido', escala, fuerza) | ('poros', ...)
    franjas: tuple = None          # (color_a, color_b, ancho_studs)
    emision: tuple = None          # (color, fuerza)
    alfa: float = 1.0
    malla_alambre: float = 0.0     # paso de la malla del cristal armado (0 = sin malla)
    juntas: float = 0.0            # paso de las juntas de dilatación del hormigón (cortes en X e Y)
    veta: str = ""                 # 'x' | 'y' | 'z': vetas de madera a lo largo de ese eje
    calcos: list = field(default_factory=list)


class _N:
    """Ayudante para crear nodos y enlazarlos con constantes o sockets."""

    def __init__(self, nt):
        self.nt = nt

    def nodo(self, tipo, **props):
        n = self.nt.nodes.new(tipo)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def _in(self, sock, val):
        if isinstance(val, bpy.types.NodeSocket):
            self.nt.links.new(val, sock)
        else:
            if sock.type in ("RGBA",) and len(val) == 3:
                val = (*val, 1.0)
            sock.default_value = val

    def math(self, op, a, b=0.0, clamp=False):
        n = self.nodo("ShaderNodeMath", operation=op, use_clamp=clamp)
        self._in(n.inputs[0], a)
        self._in(n.inputs[1], b)
        return n.outputs[0]

    def vmath(self, op, a, b=(0, 0, 0)):
        n = self.nodo("ShaderNodeVectorMath", operation=op)
        self._in(n.inputs[0], a)
        if op == "SCALE":
            self._in(n.inputs["Scale"], b)
        else:
            self._in(n.inputs[1], b)
        return n.outputs["Value"] if op in ("DOT_PRODUCT", "LENGTH", "DISTANCE") else n.outputs["Vector"]

    def separar(self, v):
        n = self.nodo("ShaderNodeSeparateXYZ")
        self._in(n.inputs[0], v)
        return n.outputs

    def combinar(self, x, y, z=0.0):
        n = self.nodo("ShaderNodeCombineXYZ")
        self._in(n.inputs[0], x)
        self._in(n.inputs[1], y)
        self._in(n.inputs[2], z)
        return n.outputs[0]

    def mapa(self, v, a0, a1, b0, b1, clamp=True):
        n = self.nodo("ShaderNodeMapRange", clamp=clamp)
        self._in(n.inputs["Value"], v)
        n.inputs["From Min"].default_value = a0
        n.inputs["From Max"].default_value = a1
        n.inputs["To Min"].default_value = b0
        n.inputs["To Max"].default_value = b1
        return n.outputs["Result"]

    def ruido(self, vec, escala, detalle=4.0, rugosidad=0.55):
        n = self.nodo("ShaderNodeTexNoise")
        self._in(n.inputs["Vector"], vec)
        n.inputs["Scale"].default_value = escala
        n.inputs["Detail"].default_value = detalle
        n.inputs["Roughness"].default_value = rugosidad
        return n.outputs["Fac"]

    def mezcla(self, fac, a, b, tipo="RGBA", modo="MIX"):
        n = self.nodo("ShaderNodeMix", data_type=tipo, blend_type=modo, clamp_factor=True)
        t = {"RGBA": "RGBA", "FLOAT": "VALUE", "VECTOR": "VECTOR"}[tipo]
        ins = [s for s in n.inputs if s.type == t and s.name in ("A", "B")]
        fac_in = [s for s in n.inputs if s.name == "Factor"][0]
        self._in(fac_in, fac)
        self._in(ins[0], a)
        self._in(ins[1], b)
        out = [s for s in n.outputs if s.type == t][0]
        return out

    def color(self, rgb):
        n = self.nodo("ShaderNodeRGB")
        n.outputs[0].default_value = (*rgb, 1.0)
        return n.outputs[0]

    def valor(self, v):
        n = self.nodo("ShaderNodeValue")
        n.outputs[0].default_value = v
        return n.outputs[0]


def construir(m: Mat, imagenes: dict):
    """Crea el material de Blender a partir de la descripción. `imagenes`: {nombre: bpy.types.Image}."""
    mat = bpy.data.materials.new(m.nombre)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    n = _N(nt)
    geo = n.nodo("ShaderNodeNewGeometry")
    P, Nn = geo.outputs["Position"], geo.outputs["Normal"]
    Px, Py, Pz = n.separar(P)[0:3]

    col = n.color(srgb(m.color))
    rug = n.valor(m.rug)
    met = n.valor(m.metal)
    alto = n.valor(0.0)  # relieve acumulado (studs)
    emi = n.color((0, 0, 0))

    # 1) variación suave de color
    if m.ruido:
        f = n.ruido(P, m.escala_ruido, 3.0)
        k = n.mapa(f, 0.3, 0.7, 1 - m.ruido, 1 + m.ruido)
        col = n.mezcla(1.0, col, n.combinar(k, k, k), modo="MULTIPLY")
        rug = n.math("ADD", rug, n.mapa(n.ruido(P, m.escala_ruido * 2.3, 2.0), 0.3, 0.7, -0.06, 0.06))

    # 2) mugre y polvo en la parte baja
    if m.sucio:
        f = n.ruido(P, 2.4, 6.0, 0.6)
        k1 = n.mapa(f, 0.42, 0.78, 1 - m.sucio * 0.4, 1.0)
        k2 = n.mapa(Pz, m.z_suelo, m.z_suelo + 1.3, 1 - m.sucio * 0.45, 1.0)
        k = n.math("MULTIPLY", k1, k2)
        tono = n.mezcla(n.math("SUBTRACT", 1.0, k), (1, 1, 1), srgb("#C9B79C"))  # mugre tirando a tierra
        col = n.mezcla(1.0, col, n.vmath("SCALE", tono, k), modo="MULTIPLY")
        rug = n.math("ADD", rug, n.math("MULTIPLY", n.math("SUBTRACT", 1.0, k), 0.25))

    # 3) chorretones verticales
    if m.chorretones:
        v = n.vmath("MULTIPLY", P, (7.0, 7.0, 0.35))
        f = n.ruido(v, 1.0, 5.0, 0.5)
        k = n.mapa(f, 0.5, 0.78, 1.0, 1 - m.chorretones * 0.45)
        col = n.mezcla(1.0, col, n.combinar(k, k, k), modo="MULTIPLY")

    # 4) óxido (más abajo, donde salpica el agua)
    if m.oxido:
        f = n.ruido(P, 3.2, 8.0, 0.65)
        sesgo = n.mapa(Pz, m.z_suelo, m.z_suelo + 1.6, 0.16, 0.0)
        f = n.math("ADD", f, sesgo)
        umbral = 1.0 - m.oxido * 0.42
        mk = n.mapa(f, umbral, umbral + 0.06, 0.0, 1.0)
        vari = n.mapa(n.ruido(P, 9.0, 4.0), 0.3, 0.7, 0.7, 1.25)
        c_ox = n.vmath("SCALE", n.color(srgb(m.color_oxido)), vari)
        col = n.mezcla(mk, col, c_ox)
        rug = n.mezcla(mk, rug, 0.88, tipo="FLOAT")
        met = n.mezcla(mk, met, 0.0, tipo="FLOAT")
        alto = n.math("ADD", alto, n.math("MULTIPLY", mk, 0.004))

    # 4b) vetas de madera
    if m.veta:
        esc = {"x": (0.6, 9.0, 9.0), "y": (9.0, 0.6, 9.0), "z": (9.0, 9.0, 0.6)}[m.veta]
        f = n.ruido(n.vmath("MULTIPLY", P, esc), 1.0, 6.0, 0.6)
        k = n.mapa(f, 0.3, 0.75, 0.72, 1.12)
        col = n.mezcla(1.0, col, n.combinar(k, k, k), modo="MULTIPLY")
        alto = n.math("ADD", alto, n.math("MULTIPLY", f, 0.01))

    # 4c) juntas de dilatación del hormigón
    if m.juntas:
        lin = []
        for comp in (Px, Py):
            fr = n.math("FRACT", n.math("DIVIDE", comp, m.juntas))
            lin.append(n.math("LESS_THAN", n.math("ABSOLUTE", n.math("SUBTRACT", fr, 0.5)), 0.006 / m.juntas * 3))
        mk = n.math("MAXIMUM", lin[0], lin[1])
        col = n.mezcla(n.math("MULTIPLY", mk, 0.6), col, (0.02, 0.02, 0.02))
        alto = n.math("SUBTRACT", alto, n.math("MULTIPLY", mk, 0.01))

    # 5) franjas de peligro (amarillo y negro en diagonal)
    if m.franjas:
        ca, cb, ancho = m.franjas
        s = n.math("ADD", n.math("ADD", Px, Py), Pz)
        fr = n.math("FRACT", n.math("DIVIDE", s, ancho * 2))
        mk = n.math("GREATER_THAN", fr, 0.5)
        col = n.mezcla(mk, n.color(srgb(ca)), n.color(srgb(cb)))

    # 6) arañazos horizontales de contenedores
    if m.rayas:
        v = n.combinar(n.math("MULTIPLY", Px, 1.4), n.math("MULTIPLY", Py, 1.4), n.math("MULTIPLY", Pz, 75.0))
        f = n.ruido(v, 1.0, 2.0, 0.5)
        f2 = n.ruido(P, 1.6, 2.0)
        alto_mk = n.mapa(Pz, m.z_rayas, m.z_rayas - 0.5, 0.0, 1.0)
        mk = n.math("MULTIPLY", n.mapa(f, 0.7 - m.rayas * 0.08, 0.74 - m.rayas * 0.08, 0.0, 1.0),
                    n.math("MULTIPLY", alto_mk, n.mapa(f2, 0.35, 0.55, 0.0, 1.0)))
        col = n.mezcla(mk, col, n.color(srgb(m.color_rayas)))
        rug = n.mezcla(mk, rug, 0.32, tipo="FLOAT")
        met = n.mezcla(mk, met, 1.0, tipo="FLOAT")
        alto = n.math("SUBTRACT", alto, n.math("MULTIPLY", mk, 0.004))

    # 7) bordes gastados (con el bisel del sombreador: donde la normal biselada se aparta de la real hay arista)
    bev = n.nodo("ShaderNodeBevel", samples=8)
    bev.inputs["Radius"].default_value = max(0.005, m.bisel)
    if m.bordes:
        d = n.vmath("DOT_PRODUCT", bev.outputs["Normal"], Nn)
        arista = n.mapa(d, 0.985, 0.9, 0.0, 1.0)
        f = n.ruido(P, 6.0, 6.0, 0.7)
        mk = n.math("MULTIPLY", arista, n.mapa(f, 0.55 - m.bordes * 0.25, 0.62 - m.bordes * 0.25, 0.0, 1.0))
        col = n.mezcla(mk, col, n.color(srgb(m.color_bordes)))
        rug = n.mezcla(mk, rug, 0.4, tipo="FLOAT")
        if m.metal < 0.5:
            met = n.mezcla(mk, met, 0.8, tipo="FLOAT")

    # 8) relieve
    if m.relieve:
        tipo, escala, fuerza = m.relieve
        if tipo == "lagrimada":
            img = n.nodo("ShaderNodeTexImage", image=imagenes["relieve_lagrimada"], projection="BOX",
                         projection_blend=0.25, interpolation="Linear", extension="REPEAT")
            n._in(img.inputs["Vector"], n.vmath("SCALE", P, 1.0 / escala))
            alto = n.math("ADD", alto, n.math("MULTIPLY", img.outputs["Color"], fuerza))
        elif tipo == "ruido":
            alto = n.math("ADD", alto, n.math("MULTIPLY", n.ruido(P, 1.0 / escala, 8.0, 0.6), fuerza))
        elif tipo == "poros":
            f = n.ruido(P, 1.0 / escala, 10.0, 0.75)
            poros = n.mapa(n.ruido(P, 5.0 / escala, 2.0), 0.72, 0.8, 0.0, -1.0)
            alto = n.math("ADD", alto, n.math("MULTIPLY", n.math("ADD", f, poros), fuerza))
        elif tipo == "ondas_y":  # chapa grecada del tejado: perfil trapezoidal a lo largo de Y
            fr = n.math("FRACT", n.math("DIVIDE", Py, escala))
            tri = n.math("ABSOLUTE", n.math("SUBTRACT", n.math("MULTIPLY", fr, 2.0), 1.0))
            tra = n.mapa(tri, 0.25, 0.6, 0.0, 1.0)
            alto = n.math("ADD", alto, n.math("MULTIPLY", tra, fuerza))
        elif tipo == "lamas":  # acanalado fino (madera, goma)
            onda = n.math("SINE", n.math("MULTIPLY", Pz, 6.2832 / escala))
            alto = n.math("ADD", alto, n.math("MULTIPLY", onda, fuerza))

    # 9) calcos (rótulos, marcas del suelo, pantallas)
    for cal in m.calcos:
        d = n.vmath("SUBTRACT", P, cal.origen)
        u = n.math("ADD", n.math("DIVIDE", n.vmath("DOT_PRODUCT", d, cal.U), cal.tam[0]), 0.5)
        v = n.math("ADD", n.math("DIVIDE", n.vmath("DOT_PRODUCT", d, cal.V), cal.tam[1]), 0.5)
        nrm = _cruz(cal.U, cal.V)
        prof = n.math("ABSOLUTE", n.vmath("DOT_PRODUCT", d, nrm))
        dentro = n.math("LESS_THAN", prof, cal.profundidad)
        img = n.nodo("ShaderNodeTexImage", image=imagenes[cal.imagen], extension="CLIP", interpolation="Linear")
        n._in(img.inputs["Vector"], n.combinar(u, v, 0.0))
        a = n.math("MULTIPLY", n.math("MULTIPLY", img.outputs["Alpha"], dentro), cal.fuerza)
        if cal.desgaste:
            f = n.ruido(P, 7.0, 6.0, 0.7)
            a = n.math("MULTIPLY", a, n.mapa(f, cal.desgaste * 0.6, cal.desgaste * 0.6 + 0.1, 0.0, 1.0))
        if cal.modo == "pintura":
            col = n.mezcla(a, col, img.outputs["Color"])
            rug = n.mezcla(a, rug, cal.rugosidad, tipo="FLOAT")
            met = n.mezcla(a, met, 0.0, tipo="FLOAT")
            alto = n.math("ADD", alto, n.math("MULTIPLY", a, 0.002))
        elif cal.modo == "multiplicar":
            col = n.mezcla(a, col, n.mezcla(1.0, col, img.outputs["Color"], modo="MULTIPLY"))
            col = n.mezcla(n.math("MULTIPLY", a, 0.6), col, img.outputs["Color"])
            rug = n.mezcla(a, rug, cal.rugosidad, tipo="FLOAT")
        elif cal.modo == "brillo":   # charco: oscurece y deja la superficie lisa y mojada
            col = n.mezcla(n.math("MULTIPLY", a, 0.55), col, (0, 0, 0))
            rug = n.mezcla(a, rug, cal.rugosidad, tipo="FLOAT")
        elif cal.modo == "aranazo":
            col = n.mezcla(a, col, img.outputs["Color"])
            rug = n.mezcla(a, rug, cal.rugosidad, tipo="FLOAT")
            alto = n.math("SUBTRACT", alto, n.math("MULTIPLY", a, 0.003))
        elif cal.modo == "emision":
            emi = n.mezcla(1.0, emi, n.vmath("SCALE", img.outputs["Color"], n.math("MULTIPLY", a, cal.fuerza)),
                           modo="ADD")
            col = n.mezcla(a, col, n.vmath("SCALE", img.outputs["Color"], 0.35))
            rug = n.mezcla(a, rug, 0.15, tipo="FLOAT")

    # 10) emisión propia
    if m.emision:
        ce, fe = m.emision
        emi = n.mezcla(1.0, emi, n.vmath("SCALE", n.color(srgb(ce)), fe), modo="ADD")

    # 11) transparencia (cristal armado: la malla de alambre es opaca)
    alfa = n.valor(m.alfa)
    if m.malla_alambre:
        paso = m.malla_alambre
        absN = n.vmath("ABSOLUTE", Nn)
        Nx, Ny, Nz = n.separar(absN)[0:3]
        lineas = []
        for comp, nc in ((Px, Nx), (Py, Ny), (Pz, Nz)):
            fr = n.math("FRACT", n.math("DIVIDE", comp, paso))
            ln = n.math("LESS_THAN", n.math("ABSOLUTE", n.math("SUBTRACT", fr, 0.5)), 0.05)
            lineas.append(n.math("MULTIPLY", ln, n.math("LESS_THAN", nc, 0.5)))
        hilo = n.math("MAXIMUM", n.math("MAXIMUM", lineas[0], lineas[1]), lineas[2])
        alfa = n.mezcla(hilo, alfa, 1.0, tipo="FLOAT")
        col = n.mezcla(hilo, col, n.color(srgb("#8A8F92")))
        met = n.mezcla(hilo, met, 0.9, tipo="FLOAT")
        rug = n.mezcla(hilo, rug, 0.45, tipo="FLOAT")

    # normal: bisel + relieve
    bump = n.nodo("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 1.0
    bump.inputs["Distance"].default_value = 1.0
    n._in(bump.inputs["Height"], alto)
    n._in(bump.inputs["Normal"], bev.outputs["Normal"])

    rug = n.math("ADD", rug, 0.0, clamp=True)
    met = n.math("ADD", met, 0.0, clamp=True)

    bsdf = n.nodo("ShaderNodeBsdfPrincipled")
    n._in(bsdf.inputs["Base Color"], col)
    n._in(bsdf.inputs["Roughness"], rug)
    n._in(bsdf.inputs["Metallic"], met)
    n._in(bsdf.inputs["Emission Color"], emi)
    bsdf.inputs["Emission Strength"].default_value = 1.0
    n._in(bsdf.inputs["Alpha"], alfa)
    n._in(bsdf.inputs["Normal"], bump.outputs["Normal"])
    e = n.nodo("ShaderNodeEmission")
    e.inputs["Strength"].default_value = 1.0
    out = n.nodo("ShaderNodeOutputMaterial")
    nt.links.new(bsdf.outputs[0], out.inputs["Surface"])
    mat.diffuse_color = (*srgb(m.color), 1.0)
    REGISTRO[m.nombre] = {"mat": mat, "out": out, "bsdf": bsdf, "emi": e,
                          "salidas": {"color": col, "rugosidad": rug, "metal": met, "emision": emi, "alfa": alfa}}
    return mat


def _cruz(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def modo_salida(modo):
    """Cambia TODOS los materiales a una salida: 'render' o una de las cinco de horneado (por EMIT)."""
    for r in REGISTRO.values():
        nt = r["mat"].node_tree
        for l in list(r["out"].inputs["Surface"].links):
            nt.links.remove(l)
        for l in list(r["emi"].inputs["Color"].links):
            nt.links.remove(l)
        if modo == "render":
            nt.links.new(r["bsdf"].outputs[0], r["out"].inputs["Surface"])
        else:
            s = r["salidas"][modo]
            nt.links.new(s, r["emi"].inputs["Color"])
            nt.links.new(r["emi"].outputs[0], r["out"].inputs["Surface"])
