"""
Materiales procedurales del puesto de seguridad (para la malla alta: se hornean al atlas).

El «Arbol» de nodos, `poner_canal` y la receta `pintura_metal` son los mismos que usan las casas del pueblo
(casa_materiales.py en la rama de las casas), copiados para que el puesto se genere solo. Añade `calco`: una imagen
(generada con Pillow en puesto_calcos.py) proyectada en un plano del mundo, para los carteles, los avisos «SE BUSCA»,
el teclado, las pantallas y el logo de la bandera.

Cada material da cinco canales que se hornean por separado: color, rug (rugosidad), met (metalicidad), emi (emisión)
y la normal (Bump + Bevel, que redondea las aristas).
"""

import bpy
from mathutils import Vector


def lin(hexa):
    """'#RRGGBB' -> RGB lineal."""
    hexa = hexa.lstrip("#")
    c = [int(hexa[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


# Canales de cada material: {nombre_material: {"color": socket|valor, "rug": ..., "met": ..., "emi": ...}}
CANALES = {}


class Arbol:
    """Pequeño lenguaje para escribir árboles de nodos sin perderse en enlaces."""

    def __init__(self, mat):
        self.mat = mat
        self.nt = mat.node_tree
        self.nt.nodes.clear()
        self._geo = None

    # ---- básicos -----------------------------------------------------------------------------------------

    def nodo(self, tipo, **props):
        n = self.nt.nodes.new(tipo)
        for k, v in props.items():
            setattr(n, k, v)
        return n

    def _salida(self, nodo, ident):
        for s in nodo.outputs:
            if s.identifier == ident:
                return s
        return nodo.outputs[ident]

    def _socket(self, nodo, ident):
        for s in nodo.inputs:
            if s.identifier == ident:
                return s
        return nodo.inputs[ident]

    def poner(self, socket, valor):
        if isinstance(valor, bpy.types.NodeSocket):
            self.nt.links.new(valor, socket)
        elif isinstance(valor, str):
            col = lin(valor)
            socket.default_value = (*col, 1.0) if len(socket.default_value) == 4 else col
        elif isinstance(valor, (tuple, list, Vector)):
            v = tuple(valor)
            n = len(socket.default_value)
            socket.default_value = v + (1.0,) * (n - len(v)) if len(v) < n else v[:n]
        else:
            socket.default_value = valor

    def geo(self):
        if self._geo is None:
            self._geo = self.nodo("ShaderNodeNewGeometry")
        return self._geo

    def pos(self):
        return self.geo().outputs["Position"]

    def normal(self):
        return self.geo().outputs["Normal"]

    def isla(self):
        """Aleatorio por isla de malla: cada tabla, piedra o panel de la malla alta tiene su propio valor."""
        return self.geo().outputs["Random Per Island"]

    def xyz(self, vec=None):
        s = self.nodo("ShaderNodeSeparateXYZ")
        self.poner(s.inputs[0], vec if vec is not None else self.pos())
        return s.outputs["X"], s.outputs["Y"], s.outputs["Z"]

    def op(self, operacion, a, b=None, c=None, clamp=False):
        n = self.nodo("ShaderNodeMath", operation=operacion, use_clamp=clamp)
        self.poner(n.inputs[0], a)
        if b is not None:
            self.poner(n.inputs[1], b)
        if c is not None:
            self.poner(n.inputs[2], c)
        return n.outputs[0]

    def mul(self, a, b, clamp=False):
        return self.op("MULTIPLY", a, b, clamp=clamp)

    def suma(self, a, b, clamp=False):
        return self.op("ADD", a, b, clamp=clamp)

    def resta(self, a, b, clamp=False):
        return self.op("SUBTRACT", a, b, clamp=clamp)

    def maxi(self, a, b):
        return self.op("MAXIMUM", a, b)

    def mini(self, a, b):
        return self.op("MINIMUM", a, b)

    def inv(self, a):
        return self.op("SUBTRACT", 1.0, a, clamp=True)

    def vop(self, operacion, a, b=None):
        n = self.nodo("ShaderNodeVectorMath", operation=operacion)
        self.poner(n.inputs[0], a)
        if b is not None:
            self.poner(n.inputs[1], b)
        return n.outputs["Value"] if operacion in ("DOT_PRODUCT", "DISTANCE", "LENGTH") else n.outputs["Vector"]

    def estirar(self, escala, vec=None, desplazar=(0, 0, 0)):
        """Coordenadas del mundo escaladas por eje (para ruidos alargados: vetas, churretes)."""
        v = self.vop("MULTIPLY", vec if vec is not None else self.pos(), Vector(escala))
        if any(desplazar):
            v = self.vop("ADD", v, Vector(desplazar))
        return v

    def rango(self, x, a, b, c=0.0, d=1.0, suave=False):
        n = self.nodo("ShaderNodeMapRange", clamp=True, interpolation_type="SMOOTHSTEP" if suave else "LINEAR")
        self.poner(n.inputs["Value"], x)
        self.poner(n.inputs["From Min"], a)
        self.poner(n.inputs["From Max"], b)
        self.poner(n.inputs["To Min"], c)
        self.poner(n.inputs["To Max"], d)
        return n.outputs["Result"]

    def mezcla(self, fac, a, b, modo="MIX"):
        n = self.nodo("ShaderNodeMix", data_type="RGBA", blend_type=modo, clamp_result=True)
        self.poner(self._socket(n, "Factor_Float"), fac)
        self.poner(self._socket(n, "A_Color"), a)
        self.poner(self._socket(n, "B_Color"), b)
        return self._salida(n, "Result_Color")

    def lerp(self, fac, a, b):
        n = self.nodo("ShaderNodeMix", data_type="FLOAT", clamp_factor=True)
        self.poner(self._socket(n, "Factor_Float"), fac)
        self.poner(self._socket(n, "A_Float"), a)
        self.poner(self._socket(n, "B_Float"), b)
        return self._salida(n, "Result_Float")

    def brillo(self, col, factor):
        """Color multiplicado por un factor (socket o número)."""
        n = self.nodo("ShaderNodeMix", data_type="RGBA", blend_type="MULTIPLY", clamp_result=False)
        self.poner(self._socket(n, "Factor_Float"), 1.0)
        self.poner(self._socket(n, "A_Color"), col)
        if isinstance(factor, bpy.types.NodeSocket):
            self.poner(self._socket(n, "B_Color"), factor)
        else:
            self._socket(n, "B_Color").default_value = (factor, factor, factor, 1.0)
        return self._salida(n, "Result_Color")

    # ---- texturas ----------------------------------------------------------------------------------------

    def ruido(self, escala, vec=None, detalle=3.0, rug=0.55, dist=0.0, tipo="FBM", salida="Fac"):
        n = self.nodo("ShaderNodeTexNoise", noise_dimensions="3D", noise_type=tipo, normalize=True)
        if vec is not None:
            self.poner(n.inputs["Vector"], vec)
        else:
            self.poner(n.inputs["Vector"], self.pos())
        n.inputs["Scale"].default_value = escala
        n.inputs["Detail"].default_value = detalle
        n.inputs["Roughness"].default_value = rug
        n.inputs["Distortion"].default_value = dist
        return n.outputs[salida]

    def voronoi(self, escala, vec=None, rasgo="F1", salida="Distance", aleatorio=1.0):
        n = self.nodo("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature=rasgo)
        self.poner(n.inputs["Vector"], vec if vec is not None else self.pos())
        n.inputs["Scale"].default_value = escala
        n.inputs["Randomness"].default_value = aleatorio
        return n.outputs[salida]

    def ola(self, escala, vec=None, direccion="Z", dist=0.0, detalle=0.0, tipo="BANDS", perfil="SIN",
            fase=0.0):
        n = self.nodo("ShaderNodeTexWave", wave_type=tipo, bands_direction=direccion, rings_direction="Z",
                      wave_profile=perfil)
        self.poner(n.inputs["Vector"], vec if vec is not None else self.pos())
        n.inputs["Scale"].default_value = escala
        n.inputs["Distortion"].default_value = dist
        n.inputs["Detail"].default_value = detalle
        n.inputs["Phase Offset"].default_value = fase
        return n.outputs["Fac"]

    def borde(self, radio=0.03, a=0.995, b=0.86):
        """Máscara de aristas: 1 en los cantos (donde la normal biselada se separa de la real)."""
        bev = self.nodo("ShaderNodeBevel", samples=8)
        bev.inputs["Radius"].default_value = radio
        d = self.vop("DOT_PRODUCT", bev.outputs["Normal"], self.normal())
        return self.rango(d, a, b, 0.0, 1.0)

    def cavidad(self, distancia=0.2, a=0.55, b=1.0):
        """Máscara de huecos y juntas (1 dentro de los rincones), con oclusión local."""
        ao = self.nodo("ShaderNodeAmbientOcclusion", only_local=True, samples=12)
        ao.inputs["Distance"].default_value = distancia
        return self.rango(ao.outputs["AO"], b, a, 0.0, 1.0)

    def lejos_de(self, punto, r0, r1, vec=None):
        """1 cerca del punto (dentro de r0) y 0 a partir de r1 (en studs)."""
        d = self.vop("DISTANCE", vec if vec is not None else self.pos(), Vector(punto))
        return self.rango(d, r0, r1, 1.0, 0.0, suave=True)

    def mirando_arriba(self, a=0.3, b=0.9):
        _, _, nz = self.xyz(self.normal())
        return self.rango(nz, a, b)

    # ---- calcos (imágenes proyectadas) ------------------------------------------------------------------

    def calco(self, ruta, origen, u, v, ancho, alto, color_srgb=True):
        """
        Imagen PNG proyectada en el plano (origen, u, v) del mundo, `ancho` x `alto` studs (origen = esquina de
        abajo a la izquierda). Devuelve (color, alfa); fuera del rectángulo el alfa es 0.
        """
        o, u, v = Vector(origen), Vector(u).normalized(), Vector(v).normalized()
        rel = self.vop("SUBTRACT", self.pos(), o)
        s = self.op("DIVIDE", self.vop("DOT_PRODUCT", rel, u), ancho)
        t = self.op("DIVIDE", self.vop("DOT_PRODUCT", rel, v), alto)
        comb = self.nodo("ShaderNodeCombineXYZ")
        self.poner(comb.inputs[0], s)
        self.poner(comb.inputs[1], t)
        tex = self.nodo("ShaderNodeTexImage", extension="CLIP", interpolation="Cubic")
        img = bpy.data.images.load(ruta, check_existing=True)
        img.colorspace_settings.name = "sRGB" if color_srgb else "Non-Color"
        tex.image = img
        self.nt.links.new(comb.outputs[0], tex.inputs["Vector"])
        return tex.outputs["Color"], tex.outputs["Alpha"]

    def de_cara(self, direccion, a=0.5, b=0.8):
        """1 en las caras que miran hacia `direccion` (para que un calco no atraviese a la cara de atrás)."""
        d = self.vop("DOT_PRODUCT", self.normal(), Vector(direccion).normalized())
        return self.rango(d, a, b)

    # ---- salida ------------------------------------------------------------------------------------------

    def terminar(self, color, rug, met, alt=None, emi=None, bisel=0.025, bump=1.0, alfa_vidrio=False):
        nt = self.nt
        out = self.nodo("ShaderNodeOutputMaterial")
        out.name = "salida"
        b = self.nodo("ShaderNodeBsdfPrincipled")
        b.name = "bsdf"
        self.poner(b.inputs["Base Color"], color)
        self.poner(b.inputs["Roughness"], rug)
        self.poner(b.inputs["Metallic"], met)
        if emi is not None:
            self.poner(b.inputs["Emission Color"], emi)
            b.inputs["Emission Strength"].default_value = 1.0
        if alfa_vidrio:
            b.inputs["Transmission Weight"].default_value = 0.85
        normal = None
        if alt is not None:
            bp = self.nodo("ShaderNodeBump")
            bp.inputs["Strength"].default_value = bump
            bp.inputs["Distance"].default_value = 1.0
            self.poner(bp.inputs["Height"], alt)
            normal = bp.outputs["Normal"]
        if bisel:
            bv = self.nodo("ShaderNodeBevel", samples=8)
            bv.inputs["Radius"].default_value = bisel
            if normal is not None:
                nt.links.new(normal, bv.inputs["Normal"])
            normal = bv.outputs["Normal"]
        if normal is not None:
            nt.links.new(normal, b.inputs["Normal"])
        nt.links.new(b.outputs[0], out.inputs["Surface"])
        CANALES[self.mat.name] = {"color": color, "rug": rug, "met": met, "emi": emi if emi is not None else "#000000"}
        self.mat.diffuse_color = (*lin(color), 1.0) if isinstance(color, str) else (0.6, 0.6, 0.6, 1.0)
        return b


def poner_canal(mat, canal):
    """Conecta la salida del material al canal pedido (para hornear con EMIT) o al BSDF (para la normal)."""
    nt = mat.node_tree
    out = nt.nodes["salida"]
    if canal == "normal":
        nt.links.new(nt.nodes["bsdf"].outputs[0], out.inputs["Surface"])
        return
    em = nt.nodes.get("canal_emision")
    if em is None:
        em = nt.nodes.new("ShaderNodeEmission")
        em.name = "canal_emision"
    em.inputs["Strength"].default_value = 1.0
    for l in list(em.inputs["Color"].links):
        nt.links.remove(l)
    valor = CANALES[mat.name][canal]
    if isinstance(valor, bpy.types.NodeSocket):
        nt.links.new(valor, em.inputs["Color"])
    elif isinstance(valor, str):
        em.inputs["Color"].default_value = (*lin(valor), 1.0)
    else:
        em.inputs["Color"].default_value = (valor, valor, valor, 1.0)
    nt.links.new(em.outputs[0], out.inputs["Surface"])


# ======================================================================================================
# Recetas
# ======================================================================================================


def pintura_metal(t, base, debajo="#8E9398", oxido="#7A3F1F", z_oxido=(1.4, 2.6), desconchon=0.6,
                  rug_pintura=0.5, met_pintura=0.15, variar_isla=None, arañazos=None, suciedad=0.5,
                  chorretones=0.35):
    """Metal pintado y viejo: base -> suciedad en juntas -> churretes -> desconchones -> óxido abajo."""
    x, y, z = t.xyz()
    col = base
    if variar_isla:
        # Paneles cambiados en distintos años: cada uno con su tono.
        isla = t.isla()
        for umbral, otro in variar_isla:
            col = t.mezcla(t.rango(isla, umbral, umbral + 0.001), col, otro)
    # Variación grande y suave (la pintura no es plana).
    var = t.ruido(0.6, detalle=2)
    col = t.brillo(col, t.rango(var, 0.3, 0.7, 0.92, 1.05))
    # Suciedad en juntas y rincones.
    cav = t.cavidad(0.22)
    col = t.mezcla(t.mul(cav, suciedad), col, "#4E463C")
    # Churretes verticales (lluvia), más fuertes abajo.
    chorro = t.rango(t.ruido(1.0, t.estirar((7, 7, 0.45)), detalle=3), 0.52, 0.72)
    abajo = t.rango(z, z_oxido[1] + 1.5, z_oxido[0], 0.25, 1.0)
    col = t.mezcla(t.mul(t.mul(chorro, abajo), chorretones), col, "#6B5D4C")
    # Polvo de tierra salpicado desde el suelo.
    polvo = t.mul(t.rango(z, z_oxido[0] + 0.9, z_oxido[0]), t.rango(t.ruido(5.0, detalle=4), 0.35, 0.75))
    col = t.mezcla(t.mul(polvo, 0.55), col, "#7A6A55")
    # Desconchones en las aristas: se ve el metal (o la imprimación).
    borde = t.borde(0.035)
    rotura = t.rango(t.ruido(9.0, detalle=4, rug=0.7), 0.42, 0.62)
    chip = t.rango(t.mul(borde, t.suma(rotura, 0.25)), 0.35, 0.6)
    chip = t.mul(chip, desconchon)
    # Arañazos finos (donde roza la gente o las herramientas).
    rasp = None
    if arañazos is not None:
        punto, r0, r1 = arañazos
        cerca = t.lejos_de(punto, r0, r1)
        lineas = t.rango(t.ruido(2.0, t.estirar((1.5, 1.5, 38)), detalle=1), 0.66, 0.70)
        rasp = t.mul(cerca, lineas)
        chip = t.maxi(chip, t.mul(rasp, 0.8))
    col = t.mezcla(chip, col, debajo)
    # Óxido: en lo bajo, sobre todo en juntas y desconchones.
    bajo = t.rango(z, z_oxido[1], z_oxido[0], suave=True)
    manchas = t.rango(t.ruido(4.0, detalle=5, rug=0.65), 0.45, 0.7)
    ox = t.mul(bajo, t.maxi(t.mul(cav, 1.3), t.mul(manchas, 0.55)))
    ox = t.maxi(ox, t.mul(chip, t.mul(bajo, 0.9)))
    ox = t.op("MINIMUM", ox, 1.0)
    tono_ox = t.mezcla(t.ruido(14.0, detalle=2), oxido, "#A0582A")
    col = t.mezcla(ox, col, tono_ox)
    rug = t.lerp(chip, rug_pintura, 0.32)
    rug = t.lerp(ox, rug, 0.88)
    rug = t.suma(rug, t.mul(t.mul(cav, suciedad), 0.15))
    met = t.lerp(chip, met_pintura, 0.85)
    met = t.lerp(ox, met, 0.05)
    piel = t.mul(t.ruido(40.0, detalle=2), 0.0025)  # piel de naranja de la pintura
    alt = t.suma(piel, t.mul(chip, -0.008))
    alt = t.suma(alt, t.mul(ox, t.mul(t.ruido(30.0, detalle=4), 0.01)))
    return col, rug, met, alt


