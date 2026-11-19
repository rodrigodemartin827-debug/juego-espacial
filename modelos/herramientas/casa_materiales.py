"""
Materiales procedurales de la casa del minero (para la malla alta: se hornean al atlas).

Cada material da cinco canales que se hornean por separado:
  color  (base color con todo el desgaste), rug (rugosidad), met (metalicidad), emi (emisión) y la normal
  (relieve con Bump + un Bevel que redondea las aristas: así la malla baja parece biselada sin gastar triángulos).

Los materiales «cuentan la historia» con máscaras en coordenadas del mundo (studs):
  * óxido y suciedad en lo bajo de las paredes, sobre todo en las juntas (oclusión local = cavidad),
  * pintura desconchada en las aristas (diferencia entre la normal biselada y la real),
  * madera más oscura y gris donde le cae la lluvia (abajo) y más clara y lisa donde se agarra la puerta,
  * losa del escalón gastada en el centro, felpudo más sucio donde se pisa...

Los colores y los puntos de la casa que usan las máscaras (manija, escalón...) se pasan en `P` desde la
construcción de las piezas, así las máscaras siguen a la geometría si se mueve algo.
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


def crear_materiales(P):
    """Crea todos los materiales. P: puntos y alturas de la casa (de casa_piezas)."""
    mats = {}

    def nuevo(nombre):
        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        mats[nombre] = m
        return Arbol(m)

    # ---- paredes ------------------------------------------------------------------------------------------
    t = nuevo("pintura_panel")
    col, rug, met, alt = pintura_metal(
        t, "#D9DAD3", variar_isla=[(0.35, "#C9CDCE"), (0.62, "#E2DFD2"), (0.8, "#B9BFC3"), (0.92, "#D7D2BF")], arañazos=(P["manija"], 0.5, 1.6),
        z_oxido=(P["zocalo_z"], P["zocalo_z"] + 1.3), desconchon=0.75)
    t.terminar(col, rug, met, alt, bisel=0.02)

    t = nuevo("junta")
    t.terminar("#2A2C2F", 0.8, 0.3, bisel=0)

    t = nuevo("interior")
    v = t.ruido(1.5, detalle=3)
    t.terminar(t.mezcla(t.rango(v, 0.3, 0.7), "#5B5249", "#6B6156"), 0.9, 0.0, bisel=0)

    t = nuevo("parche")
    x, y, z = t.xyz()
    base = t.mezcla(t.rango(t.ruido(3.0, detalle=4), 0.35, 0.65), "#9A968D", "#7F7B73")
    calor = t.borde(0.07, 0.999, 0.9)
    tinte = t.mezcla(t.ruido(6.0), "#8D6A3C", "#4D5A7A")
    col = t.mezcla(t.mul(calor, 0.7), base, tinte)
    ox = t.rango(t.ruido(7.0, detalle=5), 0.58, 0.72)
    col = t.mezcla(ox, col, "#7A3F1F")
    t.terminar(col, t.lerp(ox, 0.42, 0.85), t.lerp(ox, 0.85, 0.1),
               t.mul(t.ruido(25.0, detalle=4), 0.004), bisel=0.012)

    t = nuevo("parche_minio")  # chapa con imprimación roja de minio (reparación sin pintar)
    col, rug, met, alt = pintura_metal(t, "#8E3B26", debajo="#6E6A63", z_oxido=(1.4, 2.4), desconchon=0.9,
                                       rug_pintura=0.62, met_pintura=0.05, suciedad=0.4)
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("soldadura")
    ondas = t.ola(70.0, tipo="RINGS", dist=4.0, detalle=2.0)
    col = t.mezcla(t.rango(t.ruido(20.0), 0.4, 0.7), "#3E3A35", "#5A4A3A")
    t.terminar(col, 0.6, 0.65, t.mul(t.suma(ondas, t.ruido(40.0)), 0.006), bisel=0.008)

    # ---- metales ------------------------------------------------------------------------------------------
    t = nuevo("metal_oscuro")
    col, rug, met, alt = pintura_metal(t, "#454B53", debajo="#9A9FA4", z_oxido=(0.8, 2.2), desconchon=0.9,
                                       rug_pintura=0.45, met_pintura=0.3, arañazos=(P["manija"], 0.3, 1.2),
                                       suciedad=0.35)
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("metal_hollin")
    col, rug, met, alt = pintura_metal(t, "#3E434A", debajo="#8E9398", z_oxido=(6.0, 6.9), desconchon=0.8,
                                       rug_pintura=0.5, met_pintura=0.3, chorretones=0.6)
    x, y, z = t.xyz()
    hollin = t.mul(t.rango(z, P["chimenea_boca"] - 0.3, P["chimenea_boca"] + 0.05, 0.0, 0.85),
                   t.rango(t.ruido(6.0, t.estirar((1, 1, 0.3)), detalle=3), 0.3, 0.6, 0.6, 1.0))
    col = t.mezcla(hollin, col, "#121110")
    t.terminar(col, t.lerp(hollin, rug, 0.95), t.lerp(hollin, met, 0.0), alt, bisel=0.012)

    t = nuevo("acero")
    var = t.ruido(12.0, detalle=4)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#9DA2A7", "#B3B7BB")
    cav = t.cavidad(0.08)
    col = t.mezcla(t.mul(cav, 0.6), col, "#4A4640")
    t.terminar(col, t.suma(t.rango(var, 0.3, 0.7, 0.25, 0.42), t.mul(cav, 0.3)), 1.0,
               t.mul(t.ruido(80.0, detalle=2), 0.0015), bisel=0.006)

    t = nuevo("acero_pulido")  # la manija: brilla donde se agarra
    var = t.ruido(18.0, detalle=3)
    agarre = t.lejos_de(P["manija_agarre"], 0.05, 0.22)
    col = t.mezcla(agarre, t.mezcla(t.rango(var, 0.3, 0.7), "#8E9296", "#A5A9AD"), "#D2D4D6")
    t.terminar(col, t.lerp(agarre, t.rango(var, 0.3, 0.7, 0.3, 0.45), 0.12), 1.0, bisel=0.008)

    t = nuevo("hierro")
    x, y, z = t.xyz()
    manchas = t.rango(t.ruido(5.0, detalle=5, rug=0.65), 0.5, 0.68)
    cav = t.cavidad(0.1)
    ox = t.op("MINIMUM", t.suma(manchas, t.mul(cav, 0.8)), 1.0)
    col = t.mezcla(t.rango(t.ruido(9.0), 0.3, 0.7), "#4A4744", "#5A5550")
    col = t.mezcla(ox, col, t.mezcla(t.ruido(16.0), "#6E3A1E", "#9A5328"))
    t.terminar(col, t.lerp(ox, 0.55, 0.9), t.lerp(ox, 0.8, 0.1),
               t.mul(t.suma(t.mul(t.ruido(25.0, detalle=5), 0.006), t.mul(ox, 0.004)), 1.0), bisel=0.01)

    t = nuevo("aluminio")
    spots = t.rango(t.ruido(10.0, detalle=4), 0.6, 0.75)
    col = t.mezcla(spots, "#B9BEC2", "#D9DBD8")
    cav = t.cavidad(0.08)
    col = t.mezcla(t.mul(cav, 0.5), col, "#5C5850")
    t.terminar(col, t.lerp(spots, 0.35, 0.7), t.lerp(spots, 1.0, 0.3), bisel=0.008)

    t = nuevo("laton")
    cav = t.cavidad(0.05)
    var = t.ruido(15.0, detalle=4)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#A88440", "#C19A50")
    col = t.mezcla(t.mul(cav, 0.85), col, "#4F6B52")  # pátina verde en los huecos
    t.terminar(col, t.lerp(cav, 0.3, 0.75), t.lerp(cav, 1.0, 0.2), bisel=0.006)

    # ---- techo --------------------------------------------------------------------------------------------
    for nombre, base, galv in (("chapa_techo", "#56636F", False), ("chapa_nueva", "#A5ACB1", True)):
        t = nuevo(nombre)
        x, y, z = t.xyz()
        ax = t.op("ABSOLUTE", x)
        sol = t.mirando_arriba(0.85, 0.99)
        if galv:
            lent = t.voronoi(9.0, salida="Distance")
            col = t.mezcla(t.rango(lent, 0.0, 0.6), "#9AA1A6", "#B6BCC0")
        else:
            col = t.mezcla(t.mul(sol, 0.35), base, "#7A8792")  # descolorido por el sol en las crestas
        cav = t.cavidad(0.12)
        # Óxido en los valles cerca del alero y churretes que bajan por la pendiente (a lo largo de X).
        alero = t.rango(ax, 3.0, 4.9)
        churre = t.rango(t.ruido(1.2, t.estirar((0.35, 9, 9)), detalle=3), 0.55, 0.75)
        ox = t.op("MINIMUM", t.suma(t.mul(t.mul(cav, alero), 1.2), t.mul(churre, 0.45 if not galv else 0.15)),
                  1.0)
        ox = t.mul(ox, t.rango(t.ruido(3.0, detalle=4), 0.3, 0.6, 0.35, 1.0))
        col = t.mezcla(ox, col, t.mezcla(t.ruido(10.0), "#6E3A20", "#9A5A30"))
        # Verdín y tierra en el borde del alero.
        verdin = t.mul(t.rango(ax, 4.55, 5.05), t.rango(t.ruido(8.0, detalle=4), 0.4, 0.65))
        col = t.mezcla(t.mul(verdin, 0.7), col, "#4E5536")
        borde = t.borde(0.03)
        col = t.mezcla(t.mul(borde, 0.6), col, "#A9AFB3")
        rug = t.lerp(ox, 0.38 if galv else 0.5, 0.9)
        met = t.lerp(ox, 0.85 if galv else 0.25, 0.05)
        t.terminar(col, t.lerp(verdin, rug, 0.95), met,
                   t.mul(t.suma(t.mul(ox, t.ruido(30.0, detalle=4)), t.mul(t.ruido(50.0), 0.2)), 0.008),
                   bisel=0.015)

    # ---- madera -------------------------------------------------------------------------------------------
    t = nuevo("madera_puerta")
    x, y, z = t.xyz()
    isla = t.isla()
    tono = t.mezcla(t.rango(isla, 0.0, 1.0), "#7A5232", "#8A6440")
    tono = t.mezcla(t.rango(isla, 0.75, 0.76), tono, "#694529")
    veta = t.ola(5.0, t.estirar((1.0, 1.0, 0.12), desplazar=(0, 0, 0)), direccion="X", dist=6.0, detalle=3.0)
    veta2 = t.ruido(3.0, t.estirar((12, 12, 0.6)), detalle=5)
    vetas = t.rango(t.suma(t.mul(veta, 0.6), t.mul(veta2, 0.5)), 0.3, 1.0)
    col = t.mezcla(t.mul(vetas, 0.55), tono, "#4F3220")
    # Nudos.
    nudo = t.rango(t.voronoi(1.6, t.estirar((1, 1, 0.5)), salida="Distance"), 0.06, 0.02)
    col = t.mezcla(t.mul(nudo, 0.8), col, "#3A2414")
    # Lluvia: abajo más oscura y gris (madera lavada), con salpicaduras.
    lluvia = t.rango(z, P["puerta_z0"] + 1.4, P["puerta_z0"] + 0.1, suave=True)
    col = t.mezcla(t.mul(lluvia, 0.65), col, "#5B544C")
    col = t.mezcla(t.mul(t.mul(lluvia, t.rango(t.ruido(14.0, detalle=4), 0.55, 0.7)), 0.8), col, "#3B3027")
    # Desgaste de manos alrededor de la manija: más clara, lisa y algo grasienta en el centro.
    mano = t.lejos_de(P["manija"], 0.15, 0.75)
    col = t.mezcla(t.mul(mano, 0.55), col, "#A07A50")
    grasa = t.lejos_de(P["manija"], 0.05, 0.3)
    col = t.mezcla(t.mul(grasa, 0.45), col, "#3E2A1C")
    cav = t.cavidad(0.08)
    col = t.mezcla(t.mul(cav, 0.6), col, "#2A1C12")
    rug = t.lerp(mano, t.lerp(lluvia, 0.68, 0.85), 0.42)
    alt = t.suma(t.mul(vetas, 0.004), t.mul(t.ruido(60.0, t.estirar((1, 1, 0.08)), detalle=2), 0.0015))
    t.terminar(col, rug, 0.0, alt, bisel=0.012)

    t = nuevo("madera_oscura")  # trasera de la puerta, travesaños
    veta = t.ruido(3.0, t.estirar((10, 10, 0.5)), detalle=5)
    col = t.mezcla(t.rango(veta, 0.3, 0.8), "#5A3F28", "#3F2A1A")
    t.terminar(col, 0.8, 0.0, t.mul(veta, 0.003), bisel=0.01)

    t = nuevo("madera_pintada")  # contraventanas verdes, con la pintura levantada
    x, y, z = t.xyz()
    veta = t.ruido(3.0, t.estirar((12, 12, 0.55)), detalle=5)
    madera = t.mezcla(t.rango(veta, 0.3, 0.8), "#7D7267", "#5E554C")
    pintura = t.mezcla(t.rango(t.ruido(1.5, detalle=2), 0.3, 0.7), "#557563", "#628571")
    borde = t.borde(0.03)
    pelado = t.rango(t.suma(t.ruido(5.0, detalle=5, rug=0.7), t.mul(borde, 0.4)), 0.62, 0.66)
    abajo = t.rango(z, 2.9, 2.2)
    pelado = t.maxi(pelado, t.mul(abajo, t.rango(t.ruido(9.0, detalle=4), 0.5, 0.56)))
    col = t.mezcla(pelado, pintura, madera)
    cav = t.cavidad(0.08)
    col = t.mezcla(t.mul(cav, 0.55), col, "#2E2A22")
    col = t.mezcla(t.mul(abajo, 0.35), col, "#4A463E")
    t.terminar(col, t.lerp(pelado, 0.55, 0.8), 0.0,
               t.suma(t.mul(pelado, -0.004), t.mul(veta, t.mul(pelado, 0.004))), bisel=0.012)

    t = nuevo("madera_mango")
    x, y, z = t.xyz()
    veta = t.ruido(4.0, t.estirar((14, 14, 0.5)), detalle=5)
    col = t.mezcla(t.rango(veta, 0.3, 0.8), "#8E6B45", "#6A4B2E")
    agarre = t.rango(z, P["pico_agarre"][0], P["pico_agarre"][1])
    col = t.mezcla(t.mul(agarre, 0.75), col, "#4A3220")
    tierra = t.rango(z, 1.1, 0.55)
    col = t.mezcla(t.mul(tierra, 0.7), col, "#5C4A38")
    t.terminar(col, t.lerp(agarre, 0.7, 0.4), 0.0, t.mul(veta, 0.003), bisel=0.01)

    # ---- piedra y hormigón --------------------------------------------------------------------------------
    t = nuevo("piedra")
    x, y, z = t.xyz()
    isla = t.isla()
    tono = t.mezcla(t.rango(isla, 0.0, 0.5), "#8B8478", "#7A746B")
    tono = t.mezcla(t.rango(isla, 0.5, 1.0), tono, "#9C9486")
    tono = t.mezcla(t.rango(isla, 0.85, 0.86), tono, "#857A6C")
    grano = t.ruido(8.0, detalle=8, rug=0.65)
    col = t.brillo(tono, t.rango(grano, 0.3, 0.7, 0.85, 1.12))
    moteado = t.rango(t.voronoi(30.0, salida="Distance"), 0.1, 0.0)
    col = t.mezcla(t.mul(moteado, 0.4), col, "#5F5A53")
    liquen = t.mul(t.rango(t.ruido(4.0, detalle=5), 0.62, 0.7), t.rango(z, 1.3, 0.6))
    col = t.mezcla(t.mul(liquen, 0.85), col, "#7F8450")
    tierra = t.mul(t.rango(z, 1.0, 0.5), t.rango(t.ruido(6.0, detalle=4), 0.25, 0.6))
    col = t.mezcla(tierra, col, "#5A4B3B")
    cav = t.cavidad(0.12)
    col = t.mezcla(t.mul(cav, 0.6), col, "#3A342D")
    borde = t.borde(0.05)
    col = t.mezcla(t.mul(borde, 0.25), col, "#B2AB9E")  # aristas gastadas, más claras
    alt = t.suma(t.mul(grano, 0.02), t.mul(t.ruido(2.5, detalle=3), 0.025))
    alt = t.suma(alt, t.mul(t.rango(t.ruido(12.0, detalle=2, tipo="RIDGED_MULTIFRACTAL"), 0.85, 1.0), -0.01))
    t.terminar(col, t.lerp(liquen, 0.88, 0.95), 0.0, alt, bisel=0.05)

    t = nuevo("mortero")
    x, y, z = t.xyz()
    grit = t.ruido(40.0, detalle=4)
    col = t.mezcla(t.rango(grit, 0.3, 0.7), "#9C9587", "#8A8376")
    col = t.mezcla(t.rango(z, 1.0, 0.5), col, "#6A5D4C")
    t.terminar(col, 0.95, 0.0, t.mul(grit, 0.004), bisel=0)

    t = nuevo("hormigon")
    x, y, z = t.xyz()
    var = t.ruido(1.2, detalle=4)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#9A968E", "#8A857B")
    poros = t.rango(t.voronoi(28.0, salida="Distance"), 0.12, 0.03)
    col = t.mezcla(t.mul(poros, 0.6), col, "#55524C")
    grieta = t.rango(t.ruido(1.6, detalle=6, tipo="RIDGED_MULTIFRACTAL"), 0.88, 0.97)
    col = t.mezcla(grieta, col, "#3F3B35")
    # Manchas de agua donde cae el bajante y tierra en el pie.
    agua = t.lejos_de(P["bajante_pie"], 0.1, 1.1)
    col = t.mezcla(t.mul(agua, 0.6), col, "#5E5A50")
    pie = t.rango(z, 0.25, 0.0)
    col = t.mezcla(t.mul(pie, t.rango(t.ruido(5.0, detalle=4), 0.3, 0.7, 0.4, 0.9)), col, "#5A4A38")
    # Camino gastado hasta la puerta.
    camino = t.lejos_de(P["puerta_suelo"], 0.4, 1.4)
    col = t.mezcla(t.mul(camino, 0.3), col, "#B0AA9E")
    cav = t.cavidad(0.15)
    col = t.mezcla(t.mul(cav, 0.55), col, "#3E3A33")
    borde = t.borde(0.05)
    col = t.mezcla(t.mul(borde, t.rango(t.ruido(12.0), 0.4, 0.6, 0.0, 0.5)), col, "#B5B0A5")
    alt = t.suma(t.mul(t.ruido(10.0, detalle=6), 0.006), t.mul(poros, -0.006))
    alt = t.suma(alt, t.mul(grieta, -0.012))
    t.terminar(col, t.lerp(camino, 0.9, 0.7), 0.0, alt, bisel=0.05)

    t = nuevo("losa")  # escalón y alféizar: piedra gastada en el centro
    x, y, z = t.xyz()
    var = t.ruido(3.0, detalle=6, rug=0.6)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#8E887E", "#7C766C")
    vetas = t.rango(t.ruido(1.2, t.estirar((1, 4, 1)), detalle=4, tipo="RIDGED_MULTIFRACTAL"), 0.8, 0.95)
    col = t.mezcla(t.mul(vetas, 0.4), col, "#A39C90")
    gastado = t.lejos_de(P["escalon_centro"], 0.15, 0.95)
    col = t.mezcla(t.mul(gastado, 0.5), col, "#A8A296")
    cav = t.cavidad(0.12)
    col = t.mezcla(t.mul(cav, 0.6), col, "#3E3933")
    pie = t.rango(z, 0.12, 0.0)
    col = t.mezcla(t.mul(pie, 0.6), col, "#5A4C3B")
    borde = t.borde(0.06)
    alt = t.suma(t.mul(var, t.lerp(gastado, 0.012, 0.002)), t.mul(t.ruido(25.0, detalle=4), 0.003))
    t.terminar(col, t.lerp(gastado, 0.88, 0.55), 0.0, alt, bisel=0.06)

    # ---- macetas y plantas ----------------------------------------------------------------------------------
    t = nuevo("barro")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(4.0, detalle=4), 0.3, 0.7), "#B0613C", "#9C5434")
    sal = t.mul(t.rango(t.ruido(6.0, detalle=5), 0.55, 0.7), t.maxi(t.borde(0.03), t.cavidad(0.06)))
    col = t.mezcla(t.mul(sal, 0.8), col, "#D8CDBB")  # eflorescencias blancas
    col = t.mezcla(t.mul(t.cavidad(0.05), 0.6), col, "#4A2A1A")
    t.terminar(col, 0.85, 0.0, t.mul(t.ruido(30.0, detalle=4), 0.003), bisel=0.01)

    t = nuevo("piedra_maceta")
    x, y, z = t.xyz()
    grano = t.ruido(9.0, detalle=8)
    col = t.mezcla(t.rango(grano, 0.3, 0.7), "#9A9488", "#848074")
    musgo = t.mul(t.rango(t.ruido(5.0, detalle=5), 0.55, 0.7), t.rango(z, 1.1, 0.55))
    col = t.mezcla(musgo, col, "#5E6B3A")
    col = t.mezcla(t.mul(t.cavidad(0.1), 0.6), col, "#3A352E")
    col = t.mezcla(t.mul(t.borde(0.04), 0.3), col, "#B5AFA2")
    t.terminar(col, 0.9, 0.0, t.suma(t.mul(grano, 0.01), t.mul(t.ruido(3.0), 0.01)), bisel=0.04)

    t = nuevo("tierra")
    pied = t.rango(t.voronoi(40.0, salida="Distance"), 0.2, 0.05)
    col = t.mezcla(t.rango(t.ruido(15.0, detalle=5), 0.3, 0.7), "#3A281C", "#4A3424")
    col = t.mezcla(t.mul(pied, 0.6), col, "#7A6C5C")
    t.terminar(col, 0.95, 0.0, t.suma(t.mul(t.ruido(30.0, detalle=6), 0.006), t.mul(pied, 0.004)), bisel=0)

    t = nuevo("hoja")
    isla = t.isla()
    col = t.mezcla(t.rango(isla, 0.0, 1.0), "#3E6A2C", "#6F9A3A")
    col = t.mezcla(t.mul(t.rango(t.ruido(20.0), 0.6, 0.75), 0.5), col, "#8A7A3A")  # puntas secas
    col = t.mezcla(t.mul(t.cavidad(0.08), 0.65), col, "#1C2A12")
    t.terminar(col, 0.55, 0.0, t.mul(t.ruido(60.0), 0.002), bisel=0)

    # ---- tela, goma, cuero, fibra ---------------------------------------------------------------------------
    t = nuevo("goma")
    col = t.mezcla(t.rango(t.ruido(20.0), 0.3, 0.7), "#1C1C1D", "#2A2928")
    t.terminar(col, 0.85, 0.0, t.mul(t.ruido(80.0), 0.0015), bisel=0.008)

    t = nuevo("goma_suela")
    x, y, z = t.xyz()
    barro = t.rango(t.ruido(8.0, detalle=4), 0.35, 0.6)
    col = t.mezcla(barro, "#242322", "#4E3F30")
    t.terminar(col, 0.9, 0.0, t.mul(t.ola(30.0, direccion="X", perfil="SAW"), 0.004), bisel=0.01)

    t = nuevo("cuero")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(3.0, detalle=4), 0.3, 0.7), "#6B4A2F", "#5A3D26")
    roce = t.borde(0.05)
    col = t.mezcla(t.mul(roce, 0.55), col, "#9A7A58")  # punteras y cantos pelados
    barro = t.mul(t.rango(z, 0.85, 0.55), t.rango(t.ruido(7.0, detalle=5), 0.3, 0.6, 0.4, 1.0))
    col = t.mezcla(barro, col, "#5E4E3C")
    pliegue = t.rango(t.ruido(6.0, t.estirar((1, 1, 3)), detalle=3, tipo="RIDGED_MULTIFRACTAL"), 0.7, 0.95)
    col = t.mezcla(t.mul(t.cavidad(0.06), 0.6), col, "#24180F")
    t.terminar(col, t.lerp(barro, 0.6, 0.9), 0.0,
               t.suma(t.mul(pliegue, -0.006), t.mul(t.ruido(50.0, detalle=3), 0.0015)), bisel=0.015)

    t = nuevo("fibra")
    x, y, z = t.xyz()
    tej1 = t.ola(22.0, direccion="X", perfil="SIN")
    tej2 = t.ola(22.0, direccion="Y", perfil="SIN")
    tejido = t.mul(t.suma(tej1, tej2), 0.5)
    pelos = t.ruido(90.0, detalle=2)
    col = t.mezcla(t.rango(t.suma(tejido, t.mul(pelos, 0.5)), 0.3, 1.2), "#7E5A30", "#B08A55")
    pisado = t.lejos_de(P["felpudo_centro"], 0.1, 0.65)
    col = t.mezcla(t.mul(pisado, 0.6), col, "#5A4632")
    t.terminar(col, 0.95, 0.0, t.mul(t.suma(tejido, t.mul(pelos, 0.6)), 0.006), bisel=0.012)

    t = nuevo("tela")
    rayas = t.rango(t.ola(4.0, direccion="Z", perfil="SIN"), 0.85, 0.95)
    trama = t.mul(t.ola(140.0, direccion="X"), 0.5)
    col = t.mezcla(t.mul(rayas, 0.5), "#E4D9C2", "#9DB0C0")
    col = t.mezcla(t.mul(t.cavidad(0.08), 0.5), col, "#8A8070")
    t.terminar(col, 0.9, 0.0, t.mul(trama, 0.0015), bisel=0)

    t = nuevo("papel")
    t.terminar(t.mezcla(t.rango(t.ruido(8.0), 0.4, 0.7), "#EDE6D6", "#D8CDB5"), 0.8, 0.0, bisel=0.004)

    # ---- vidrio, neón y electricidad --------------------------------------------------------------------------
    t = nuevo("vidrio")
    x, y, z = t.xyz()
    polvo = t.mul(t.rango(t.ruido(6.0, detalle=4), 0.45, 0.7), 0.6)
    col = t.mezcla(polvo, "#79B8AE", "#9AA89A")
    t.terminar(col, t.lerp(polvo, 0.05, 0.4), 0.0, bisel=0.004)

    t = nuevo("neon")
    t.terminar("#3DF2FF", 0.3, 0.0, emi="#3DF2FF", bisel=0)

    t = nuevo("celda_solar")
    cristal = t.voronoi(60.0, salida="Color")
    col = t.mezcla(0.15, "#17284A", cristal)
    t.terminar(col, 0.12, 0.3, bisel=0.004)

    # ---- pinturas de color -------------------------------------------------------------------------------------
    t = nuevo("pintura_naranja")
    col, rug, met, alt = pintura_metal(t, "#C9692D", debajo="#8E9398", z_oxido=(2.4, 3.3), desconchon=0.8,
                                       rug_pintura=0.42, chorretones=0.25, suciedad=0.4)
    t.terminar(col, rug, met, alt, bisel=0.01)

    t = nuevo("pintura_roja")
    col, rug, met, alt = pintura_metal(t, "#B3322A", debajo="#8E9398", z_oxido=(2.4, 3.0), desconchon=0.6,
                                       rug_pintura=0.4, chorretones=0.1, suciedad=0.3)
    t.terminar(col, rug, met, alt, bisel=0.006)

    t = nuevo("pintura_gris")
    col, rug, met, alt = pintura_metal(t, "#A3A9AD", debajo="#8E9398", z_oxido=(2.4, 3.0), desconchon=0.7,
                                       rug_pintura=0.5, chorretones=0.3, suciedad=0.4)
    t.terminar(col, rug, met, alt, bisel=0.008)

    t = nuevo("pegatina")
    t.terminar(t.mezcla(t.rango(t.ruido(12.0, detalle=4), 0.55, 0.7), "#E2B321", "#BFA678"), 0.6, 0.0, bisel=0)

    t = nuevo("negro_mate")
    t.terminar("#151617", 0.7, 0.0, bisel=0)

    return mats
