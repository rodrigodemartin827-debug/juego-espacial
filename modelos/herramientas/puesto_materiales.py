"""
Materiales del puesto de seguridad (procedurales, para hornear al atlas).

La historia que cuentan:
  * Es el edificio más nuevo y mejor mantenido del pueblo: la pintura gris oscuro está entera, sin óxido; solo
    hay polvo al pie de los muros, un poco de suciedad en las juntas y los cantos algo más claros de limpiarlos.
  * Lo que más se toca sí está gastado: la manilla y el teclado de la puerta, la chapa de patada (botas), el
    bombín, el botón del interfono.
  * La silla del guardia está hundida y brillante en el centro del asiento, con la tela más clara y un parche de
    cinta americana. La encimera tiene marcas de tazas.
  * Fuera: el hormigón de la isla tiene manchas de aceite donde paran los coches y la punta pintada a franjas.

Cada función recibe `t` (Arbol) y termina con t.terminar(color, rugosidad, metal, altura, emisión).
"""

import bpy
from mathutils import Vector

from puesto_materiales_base import Arbol, lin, pintura_metal  # noqa: F401

# Materiales con emisión en el atlas (se hornea su canal «emi»).
EMISIVOS = set()


def crear_materiales(P, calcos):
    """P: puntos del modelo (de puesto_piezas); calcos: {nombre: ruta png} (de puesto_calcos)."""
    mats = {}

    def nuevo(nombre):
        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        mats[nombre] = m
        return Arbol(m)

    def simple(nombre, color, rug, met=0.0, bisel=0.01, ruido=0.0):
        t = nuevo(nombre)
        if ruido:
            v = t.ruido(6.0, detalle=4)
            col = t.brillo(color, t.rango(v, 0.3, 0.7, 1 - ruido, 1 + ruido))
            t.terminar(col, rug, met, t.mul(v, 0.002), bisel=bisel)
        else:
            t.terminar(color, rug, met, bisel=bisel)
        return t

    def calco_sobre(t, col, nombre, d, cara=None, rug=None):
        """Mezcla un calco (P[...]) sobre `col`. `cara`: solo en las caras que miran hacia esa dirección."""
        c, a = t.calco(calcos[nombre], d["origen"], d.get("u", (1, 0, 0)), d.get("v", (0, 0, 1)), d["ancho"],
                       d["alto"])
        if cara is not None:
            a = t.mul(a, t.de_cara(cara, 0.35, 0.7))
        return t.mezcla(a, col, c), a

    # ---- hormigón de la losa ------------------------------------------------------------------------------
    t = nuevo("hormigon")
    x, y, z = t.xyz()
    var = t.ruido(1.1, detalle=4)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#A7A39B", "#958F86")
    poros = t.rango(t.voronoi(30.0, salida="Distance"), 0.12, 0.03)
    col = t.mezcla(t.mul(poros, 0.5), col, "#5F5B55")
    # Manchas de aceite donde paran los coches (junto al interfono y la barrera).
    aceite = t.mul(t.lejos_de(P["isla_punta"] + Vector((0.4, 1.0, 0)), 0.2, 1.1),
                   t.rango(t.ruido(3.0, detalle=5), 0.45, 0.7))
    col = t.mezcla(t.mul(aceite, 0.5), col, "#3B3732")
    # Polvo al pie de la caseta y cantos más claros.
    borde = t.borde(0.05)
    col = t.mezcla(t.mul(borde, 0.35), col, "#C4C0B6")
    cav = t.cavidad(0.15)
    col = t.mezcla(t.mul(cav, 0.5), col, "#4A463F")
    # Punta de la isla: bordillo pintado a franjas amarillas y negras (caras verticales y canto).
    isla = t.mul(t.rango(y, -3.45, -3.7), t.rango(x, 2.82, 2.95))
    vertical = t.inv(t.mirando_arriba(0.5, 0.9))
    franja = t.op("LESS_THAN", t.op("FRACT", t.mul(t.suma(t.resta(x, y), t.mul(z, 0.0)), 1.6)), 0.5)
    pinta = t.mezcla(franja, "#E2B21C", "#1C1C1C")
    gasto = t.rango(t.ruido(9.0, detalle=4), 0.6, 0.72)
    pinta = t.mezcla(t.mul(gasto, 0.7), pinta, "#9A958B")
    fac_pinta = t.mul(isla, vertical)
    col = t.mezcla(fac_pinta, col, pinta)
    alt = t.suma(t.mul(t.ruido(12.0, detalle=6), 0.006), t.mul(poros, -0.005))
    t.terminar(col, t.lerp(fac_pinta, t.lerp(aceite, 0.88, 0.5), 0.55), 0.0, alt, bisel=0.04)

    simple("junta", "#2E2F30", 0.85, bisel=0)

    # ---- paredes: chapa de acero pintada gris oscuro, nueva -------------------------------------------------
    for nombre, base in (("pared", "#3D434A"), ("pared_canto", "#3A4047")):
        t = nuevo(nombre)
        col, rug, met, alt = pintura_metal(
            t, base, debajo="#7E858C", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1), desconchon=0.12, rug_pintura=0.42,
            met_pintura=0.35, variar_isla=None, suciedad=0.25, chorretones=0.08)
        x, y, z = t.xyz()
        # Polvo de la calle subiendo desde el pie (es lo único sucio).
        polvo = t.mul(t.rango(z, 1.1, 0.3), t.rango(t.ruido(4.0, detalle=4), 0.3, 0.7, 0.5, 1.0))
        col = t.mezcla(t.mul(polvo, 0.45), col, "#77705F")
        borde = t.borde(0.03)
        col = t.mezcla(t.mul(borde, 0.25), col, "#6A737C")  # cantos limpiados, más claros
        t.terminar(col, rug, met, alt, bisel=0.02)

    t = nuevo("interior_pared")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(2.0, detalle=3), 0.3, 0.7), "#C9C6BC", "#BDB9AE")
    # Marca de la silla contra la pared y roces a la altura del respaldo.
    roce = t.mul(t.rango(z, 1.5, 1.9), t.rango(t.ruido(5.0, detalle=4), 0.6, 0.75))
    col = t.mezcla(t.mul(roce, 0.4), col, "#8A857A")
    t.terminar(col, 0.8, 0.0, t.mul(t.ruido(30.0, detalle=3), 0.002), bisel=0.01)

    t = nuevo("alfeizar_int")
    col = t.mezcla(t.rango(t.ruido(3.0, detalle=3), 0.3, 0.7), "#3A3F45", "#2F3439")
    t.terminar(col, 0.5, 0.4, bisel=0.01)

    t = nuevo("techo_int")
    t.terminar(t.mezcla(t.rango(t.ruido(1.5), 0.3, 0.7), "#D8D5CB", "#CFCBC0"), 0.85, 0.0, bisel=0)

    # ---- cinta reflectante: diagonales naranjas y amarillas, con microprismas ---------------------------------
    t = nuevo("cinta")
    x, y, z = t.xyz()
    diag = t.op("FRACT", t.mul(t.suma(t.suma(x, y), z), 2.6))
    franja = t.op("LESS_THAN", diag, 0.5)
    col = t.mezcla(franja, "#F4B41A", "#EE5A12")
    prisma = t.ola(220.0, direccion="X", perfil="TRI")
    col = t.brillo(col, t.rango(t.ruido(30.0), 0.3, 0.7, 0.92, 1.06))
    t.terminar(col, 0.32, 0.0, t.mul(prisma, 0.0008), bisel=0.002)

    # ---- metales -----------------------------------------------------------------------------------------
    t = nuevo("tornilleria")
    var = t.ruido(25.0, detalle=3)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#8E959B", "#A9AFB4")
    t.terminar(col, t.rango(var, 0.3, 0.7, 0.3, 0.45), 1.0, bisel=0.004)

    t = nuevo("galvanizado")
    lent = t.voronoi(7.0, salida="Distance")
    col = t.mezcla(t.rango(lent, 0.0, 0.6), "#9DA4A9", "#B7BDC1")
    cav = t.cavidad(0.08)
    col = t.mezcla(t.mul(cav, 0.5), col, "#565A5C")
    t.terminar(col, t.lerp(t.rango(lent, 0, 0.6), 0.32, 0.48), 0.9, t.mul(t.ruido(60.0), 0.001), bisel=0.008)

    for nombre, base, met in (("acero_angular", "#2B3036", 0.6), ("marco", "#2A2F35", 0.55),
                              ("albardilla", "#4A5159", 0.6), ("acero_oscuro", "#2C3035", 0.6),
                              ("barrera_gris", "#5E666E", 0.5), ("foco_carcasa", "#30353B", 0.55),
                              ("radio_caja", "#3C4A3E", 0.4), ("interfono_caja", "#33393F", 0.5),
                              ("puerta_int", "#5A6068", 0.45)):
        t = nuevo(nombre)
        col, rug, met_, alt = pintura_metal(t, base, debajo="#9AA1A7", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1),
                                            desconchon=0.2, rug_pintura=0.4, met_pintura=met, suciedad=0.3,
                                            chorretones=0.05)
        borde = t.borde(0.025)
        col = t.mezcla(t.mul(borde, 0.3), col, "#8C949B")
        t.terminar(col, rug, met_, alt, bisel=0.012)

    t = nuevo("soldadura")
    ondas = t.ola(80.0, tipo="RINGS", dist=4.0, detalle=2.0)
    t.terminar(t.mezcla(t.rango(t.ruido(20.0), 0.4, 0.7), "#2E3135", "#45403A"), 0.55, 0.6,
               t.mul(t.suma(ondas, t.ruido(40.0)), 0.005), bisel=0.006)

    t = nuevo("acero_pulido")
    var = t.ruido(18.0, detalle=3)
    agarre = t.lejos_de(P["manija"], 0.05, 0.25)
    col = t.mezcla(agarre, t.mezcla(t.rango(var, 0.3, 0.7), "#9EA3A8", "#B4B8BC"), "#DADCDE")
    t.terminar(col, t.lerp(agarre, t.rango(var, 0.3, 0.7, 0.2, 0.32), 0.1), 1.0, bisel=0.006)

    t = nuevo("inox")
    x, y, z = t.xyz()
    cepillado = t.ruido(3.0, t.estirar((1, 80, 1)), detalle=2)
    botas = t.mul(t.lejos_de(P["puerta_patada"], 0.1, 0.6), t.rango(t.ruido(2.0, t.estirar((1, 4, 40)), detalle=2),
                                                                     0.6, 0.66))
    col = t.mezcla(t.rango(cepillado, 0.3, 0.7), "#A9AEB2", "#BFC3C6")
    col = t.mezcla(t.mul(botas, 0.8), col, "#5D5852")
    t.terminar(col, t.lerp(botas, t.rango(cepillado, 0.3, 0.7, 0.22, 0.32), 0.6), 1.0,
               t.mul(botas, -0.002), bisel=0.004)

    t = nuevo("aluminio")
    col = t.mezcla(t.rango(t.ruido(10.0, detalle=4), 0.6, 0.75), "#B9BEC2", "#CDD0D0")
    col = t.mezcla(t.mul(t.cavidad(0.06), 0.5), col, "#5C5850")
    t.terminar(col, 0.35, 0.95, bisel=0.006)

    t = nuevo("laton")
    cav = t.cavidad(0.05)
    var = t.ruido(15.0, detalle=4)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#B08A45", "#C9A257")
    col = t.mezcla(t.mul(cav, 0.6), col, "#5E5236")
    t.terminar(col, t.lerp(cav, 0.28, 0.6), 1.0, bisel=0.005)

    t = nuevo("cobre")
    t.terminar(t.mezcla(t.rango(t.ruido(20.0), 0.3, 0.7), "#B86A3C", "#D08250"), 0.3, 1.0, bisel=0.003)

    t = nuevo("antena")
    t.terminar(t.mezcla(t.rango(t.ruido(30.0), 0.3, 0.7), "#C8CCCF", "#AEB3B7"), 0.3, 1.0, bisel=0.003)

    t = nuevo("bisagra")
    var = t.ruido(14.0, detalle=4)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#3A3F44", "#4A5056")
    grasa = t.mul(t.cavidad(0.05), 0.8)
    col = t.mezcla(grasa, col, "#1B1A18")
    borde = t.borde(0.02)
    col = t.mezcla(t.mul(borde, 0.5), col, "#9AA0A6")  # el roce del nudo deja el acero a la vista
    t.terminar(col, t.lerp(grasa, 0.45, 0.25), t.lerp(borde, 0.65, 1.0), bisel=0.008)

    t = nuevo("contrapeso")
    col, rug, met, alt = pintura_metal(t, "#2A2C2E", debajo="#8E9398", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1),
                                       desconchon=0.5, rug_pintura=0.5, met_pintura=0.4, suciedad=0.4)
    t.terminar(col, rug, met, alt, bisel=0.015)

    # ---- franjas: brazo de la barrera, poste de apoyo y banda reductora --------------------------------------
    t = nuevo("brazo_franjas")
    x, y, z = t.xyz()
    franja = t.op("LESS_THAN", t.op("FRACT", t.op("DIVIDE", t.resta(x, P["brazo_x0"] + 0.05), 0.5)), 0.5)
    col = t.mezcla(franja, "#F2F0EA", "#C8211B")
    corto = t.op("LESS_THAN", x, P["brazo_x0"] + 0.2)
    col = t.mezcla(corto, col, "#5E666E")
    col = t.mezcla(t.mul(t.borde(0.02), 0.2), col, "#FFFFFF")
    sucio = t.mul(t.rango(z, P.get("brazo_z", 2.95) - 0.02, P.get("brazo_z", 2.95) - 0.09),
                  t.rango(t.ruido(6.0, detalle=4), 0.4, 0.7))
    col = t.mezcla(t.mul(sucio, 0.35), col, "#6E665A")
    t.terminar(col, t.lerp(corto, 0.3, 0.45), t.lerp(corto, 0.05, 0.4), t.mul(t.ruido(40.0), 0.001), bisel=0.006)

    t = nuevo("apoyo_franjas")
    x, y, z = t.xyz()
    franja = t.op("LESS_THAN", t.op("FRACT", t.op("DIVIDE", z, 0.3)), 0.5)
    t.terminar(t.mezcla(franja, "#F2F0EA", "#C8211B"), 0.35, 0.05, bisel=0.006)

    t = nuevo("banda")
    x, y, z = t.xyz()
    modulo = t.op("LESS_THAN", t.op("FRACT", t.op("DIVIDE", x, 0.5)), 0.5)
    col = t.mezcla(modulo, "#1E1E1F", "#E6B21E")
    desgaste = t.mul(t.rango(z, 0.1, 0.155), t.rango(t.ruido(10.0, detalle=4), 0.4, 0.65))
    col = t.mezcla(t.mul(desgaste, 0.55), col, "#545250")  # las ruedas gastan la parte de arriba
    rayas = t.ola(25.0, direccion="Y", perfil="SIN")
    t.terminar(col, 0.85, 0.0, t.mul(rayas, 0.004), bisel=0.01)

    # ---- goma, cables, plásticos -------------------------------------------------------------------------------
    simple("goma", "#1D1D1E", 0.85, ruido=0.08, bisel=0.006)
    simple("cable", "#141516", 0.55, ruido=0.05, bisel=0.002)
    simple("negro_mate", "#121314", 0.75, bisel=0.002)
    simple("plastico_negro", "#1F2124", 0.5, ruido=0.04, bisel=0.006)
    simple("cuerda", "#D8D2C0", 0.9, ruido=0.1, bisel=0)

    t = nuevo("plastico_blanco")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(4.0, detalle=3), 0.3, 0.7), "#E4E6E6", "#D6D9DA")
    arriba = t.mirando_arriba(0.5, 0.9)
    col = t.mezcla(t.mul(arriba, t.rango(t.ruido(8.0, detalle=4), 0.3, 0.6, 0.15, 0.4)), col, "#8D877A")
    t.terminar(col, 0.42, 0.0, bisel=0.008)

    simple("lente", "#06080A", 0.04, 0.0, bisel=0.002)
    simple("rejilla", "#16181A", 0.6, 0.4, bisel=0.002)
    simple("reflector", "#D9DDE0", 0.08, 1.0, bisel=0.002)
    simple("espejo", "#E2E4E6", 0.05, 1.0, bisel=0)

    t = nuevo("bombilla")
    EMISIVOS.add("bombilla")
    t.terminar("#FFB25A", 0.2, 0.0, emi="#FF8A1E", bisel=0)

    t = nuevo("led")
    EMISIVOS.add("led")
    t.terminar("#3CFF7A", 0.2, 0.0, emi="#2BFF6A", bisel=0)

    t = nuevo("led_ir")
    t.terminar("#3A0E10", 0.25, 0.0, bisel=0)

    # ---- pinturas de color ---------------------------------------------------------------------------------
    t = nuevo("pintura_roja")
    col, rug, met, alt = pintura_metal(t, "#B5221C", debajo="#9AA1A7", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1),
                                       desconchon=0.15, rug_pintura=0.35, met_pintura=0.15, suciedad=0.25,
                                       chorretones=0.05)
    t.terminar(col, rug, met, alt, bisel=0.008)

    t = nuevo("barra_roja")
    t.terminar(t.mezcla(t.lejos_de(Vector((X1_INT - 0.25, 1.55, 2.6)), 0.1, 0.4), "#B5221C", "#D9443A"), 0.35, 0.2,
               bisel=0.006)

    simple("amarillo", "#E8B41C", 0.4, bisel=0.004)
    simple("chincheta", "#C9302C", 0.3, bisel=0.002)

    # ---- puerta ---------------------------------------------------------------------------------------------
    t = nuevo("puerta_acero")
    col, rug, met, alt = pintura_metal(t, "#2F4258", debajo="#8E979F", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1),
                                       desconchon=0.15, rug_pintura=0.38, met_pintura=0.45,
                                       arañazos=(P["manija"], 0.25, 0.9), suciedad=0.3, chorretones=0.05)
    mano = t.lejos_de(P["manija"], 0.15, 0.6)
    col = t.mezcla(t.mul(mano, 0.35), col, "#4E6176")
    col, a = calco_sobre(t, col, "autorizado", P["pegatina"], cara=(1, 0, 0))
    t.terminar(col, t.lerp(a, t.lerp(mano, rug, 0.25), 0.4), t.lerp(a, met, 0.0), alt, bisel=0.015)

    t = nuevo("teclado_caja")
    col = t.mezcla(t.rango(t.ruido(12.0), 0.3, 0.7), "#2A2D31", "#33373B")
    t.terminar(col, 0.35, 0.6, bisel=0.008)

    t = nuevo("tecla")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(30.0), 0.3, 0.7), "#3A3E43", "#44494E")
    if "teclado" in P:
        col, _ = calco_sobre(t, col, "teclado", P["teclado"], cara=(1, 0, 0))
    # El código se marca siempre igual: el 1, el 7 y el 0 están más gastados (brillan).
    gast = t.maxi(t.lejos_de(P["teclado"]["origen"] + Vector((0, 0.045, 0.27)), 0.0, 0.04),
                  t.lejos_de(P["teclado"]["origen"] + Vector((0, 0.045, 0.04)), 0.0, 0.04)) if "teclado" in P else 0.0
    t.terminar(col, t.lerp(gast, 0.55, 0.2), t.lerp(gast, 0.0, 0.3), bisel=0.006)

    t = nuevo("placa_azul")
    col = t.mezcla(t.rango(t.ruido(5.0, detalle=3), 0.3, 0.7), "#1B3768", "#21407A")
    t.terminar(col, 0.35, 0.3, bisel=0.008)
    simple("letras", "#F4F4F0", 0.3, 0.1, bisel=0.003)
    t = nuevo("letras_oro")
    t.terminar(t.mezcla(t.rango(t.ruido(18.0), 0.3, 0.7), "#D8A93E", "#E9C062"), 0.25, 1.0, bisel=0.003)

    # ---- ventanas -------------------------------------------------------------------------------------------
    t = nuevo("alfeizar")
    col, rug, met, alt = pintura_metal(t, "#4A5159", debajo="#9AA1A7", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1),
                                       desconchon=0.2, rug_pintura=0.4, met_pintura=0.55, suciedad=0.3,
                                       chorretones=0.05)
    # Cercos de taza (el café de todos los días) en la repisa de la fachada.
    x, y, z = t.xyz()
    tc = P["taza"]
    aros = t.rango(t.op("ABSOLUTE", t.resta(t.vop("DISTANCE", t.pos(), tc + Vector((-0.35, 0.05, 0))), 0.1)), 0.012,
                   0.0)
    aros2 = t.rango(t.op("ABSOLUTE", t.resta(t.vop("DISTANCE", t.pos(), tc + Vector((0.25, -0.08, 0))), 0.1)), 0.01,
                    0.0)
    arriba = t.mirando_arriba(0.8, 0.95)
    col = t.mezcla(t.mul(t.mul(t.maxi(aros, aros2), arriba), 0.6), col, "#3A2A1C")
    t.terminar(col, rug, met, alt, bisel=0.01)

    simple("alambre", "#3C4146", 0.45, 0.8, bisel=0)
    simple("vidrio", "#9FC4CF", 0.05, bisel=0)
    simple("vidrio_naranja", "#FF8A1E", 0.05, bisel=0)
    simple("neon", "#3DF2FF", 0.3, bisel=0)

    # ---- techo -----------------------------------------------------------------------------------------------
    t = nuevo("membrana")
    x, y, z = t.xyz()
    grava = t.voronoi(40.0, salida="Distance")
    col = t.mezcla(t.rango(t.ruido(2.0, detalle=4), 0.3, 0.7), "#4A4C4E", "#57595A")
    col = t.mezcla(t.mul(t.rango(grava, 0.25, 0.05), 0.4), col, "#77787A")
    charco = t.mul(t.lejos_de(P["gargola"] + Vector((0, -0.4, 0)), 0.2, 1.2), t.rango(t.ruido(3.0), 0.4, 0.6))
    col = t.mezcla(t.mul(charco, 0.5), col, "#2F3132")
    t.terminar(col, t.lerp(charco, 0.85, 0.35), 0.0, t.mul(t.rango(grava, 0.3, 0.0), 0.006), bisel=0.01)

    t = nuevo("celda_solar")
    cristal = t.voronoi(80.0, salida="Color")
    col = t.mezcla(0.12, "#13254A", cristal)
    x, y, z = t.xyz()
    pistas = t.op("LESS_THAN", t.op("FRACT", t.mul(x, 14.0)), 0.06)
    col = t.mezcla(t.mul(pistas, 0.6), col, "#B8BEC4")
    t.terminar(col, 0.1, 0.3, bisel=0.003)

    simple("etiqueta_radio", "#E8E2CF", 0.6, bisel=0)
    t = nuevo("radio_display")
    EMISIVOS.add("radio_display")
    t.terminar("#2A6E3C", 0.2, 0.0, emi="#58FF8C", bisel=0)

    t = nuevo("tela_bandera")
    x, y, z = t.xyz()
    trama = t.mul(t.suma(t.ola(160.0, direccion="X"), t.ola(160.0, direccion="Z")), 0.5)
    col = "#14305C"
    if "bandera" in P:
        col, _ = calco_sobre(t, col, "bandera", P["bandera"])
    col = t.brillo(col, t.rango(trama, 0.0, 1.0, 0.94, 1.04))
    # Un poco descolorida por el sol en la punta.
    punta = t.rango(x, -1.2, -0.6)
    col = t.mezcla(t.mul(punta, 0.15), col, "#C7C3B8")
    t.terminar(col, 0.85, 0.0, t.mul(trama, 0.002), bisel=0)

    # ---- cámaras, tablón, extintor, papelera, taza -------------------------------------------------------------
    t = nuevo("corcho")
    granos = t.voronoi(90.0, salida="Distance")
    col = t.mezcla(t.rango(t.ruido(25.0, detalle=5), 0.3, 0.7), "#A57A4E", "#8C643E")
    col = t.mezcla(t.mul(t.rango(granos, 0.2, 0.0), 0.6), col, "#5A3E25")
    # Marcas de chinchetas viejas.
    marcas = t.rango(t.voronoi(9.0, salida="Distance", aleatorio=1.0), 0.015, 0.0)
    col = t.mezcla(t.mul(marcas, 0.8), col, "#3A2A1A")
    t.terminar(col, 0.92, 0.0, t.suma(t.mul(t.ruido(60.0, detalle=4), 0.004), t.mul(marcas, -0.004)), bisel=0.004)

    for d in P.get("papeles", []):
        t = nuevo("papel_" + d["calco"])
        col, a = calco_sobre(t, "#E2D7BC", d["calco"], d)
        cav = t.cavidad(0.04)
        col = t.mezcla(t.mul(cav, 0.4), col, "#6B5A40")
        arrugas = t.ruido(8.0, detalle=5, tipo="RIDGED_MULTIFRACTAL")
        t.terminar(col, 0.85, 0.0, t.mul(arrugas, 0.002), bisel=0.002)

    t = nuevo("extintor")
    col, rug, met, alt = pintura_metal(t, "#C1201A", debajo="#9AA1A7", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1),
                                       desconchon=0.1, rug_pintura=0.28, met_pintura=0.2, suciedad=0.2,
                                       chorretones=0.0)
    col, a = calco_sobre(t, col, "extintor", P["extintor"], cara=P["extintor"]["normal"])
    t.terminar(col, t.lerp(a, rug, 0.6), t.lerp(a, met, 0.0), alt, bisel=0.008)

    t = nuevo("senal_extintor")
    col, _ = calco_sobre(t, "#C41C1A", "senal_extintor", P["senal_extintor"], cara=(1, 0, 0))
    t.terminar(col, 0.45, 0.0, bisel=0.003)

    simple("manometro", "#F0F0E8", 0.2, bisel=0)

    t = nuevo("papelera")
    col, rug, met, alt = pintura_metal(t, "#2D4A3A", debajo="#9AA1A7", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1),
                                       desconchon=0.3, rug_pintura=0.45, met_pintura=0.35, suciedad=0.5,
                                       chorretones=0.2)
    t.terminar(col, rug, met, alt, bisel=0.01)
    t = nuevo("papelera_tapa")
    col, rug, met, alt = pintura_metal(t, "#2D4A3A", debajo="#9AA1A7", z_oxido=(SUELO_BAJO, SUELO_BAJO + 0.1),
                                       desconchon=0.45, rug_pintura=0.45, met_pintura=0.35, suciedad=0.4,
                                       chorretones=0.1)
    t.terminar(col, rug, met, alt, bisel=0.01)
    simple("bolsa", "#1B1C1E", 0.35, ruido=0.1, bisel=0)

    t = nuevo("ceramica")
    col = "#F2F0EA"
    tc = P.get("taza_c", P["taza"])
    impresion = dict(origen=tc + Vector((-0.1, -0.12, 0.05)), u=Vector((1, 0, 0)), v=Vector((0, 0, 1)), ancho=0.2,
                     alto=0.15)
    col, _ = calco_sobre(t, col, "taza", impresion, cara=(0, -1, 0))
    goteo = t.mul(t.lejos_de(tc + Vector((0.0, -0.11, 0.24)), 0.0, 0.1), t.rango(t.ruido(30.0), 0.5, 0.6))
    col = t.mezcla(t.mul(goteo, 0.7), col, "#5A3A22")
    t.terminar(col, 0.12, 0.0, bisel=0.004)

    simple("cafe", "#2A170C", 0.08, bisel=0)
    simple("cafe_mancha", "#4A2E1A", 0.3, bisel=0)

    # ---- barrera, interfono, cono, STOP --------------------------------------------------------------------------
    simple("catadioptrico", "#D11B14", 0.15, bisel=0)
    t = nuevo("boton")
    EMISIVOS.add("boton")
    t.terminar("#2F7FD1", 0.25, 0.0, emi="#2B7CFF", bisel=0.004)

    t = nuevo("cono")
    x, y, z = t.xyz()
    banda = t.maxi(t.mul(t.rango(z, 0.55, 0.56), t.rango(z, 0.78, 0.77)),
                   t.mul(t.rango(z, 0.95, 0.96), t.rango(z, 1.12, 1.11)))
    col = t.mezcla(banda, "#F06418", "#ECEDEA")
    sucio = t.mul(t.rango(z, 0.5, 0.05), t.rango(t.ruido(6.0, detalle=4), 0.3, 0.7))
    col = t.mezcla(t.mul(sucio, 0.5), col, "#5E5245")
    t.terminar(col, t.lerp(banda, 0.45, 0.25), 0.0, bisel=0.01)
    simple("cono_base", "#1D1D1E", 0.8, ruido=0.08, bisel=0.01)

    t = nuevo("senal_stop")
    col = t.mezcla(t.rango(t.ruido(6.0, detalle=3), 0.3, 0.7), "#C5161D", "#D21E22")
    atras = t.de_cara((0, 1, 0), 0.4, 0.7)
    col = t.mezcla(atras, col, "#A7ADB1")
    t.terminar(col, t.lerp(atras, 0.32, 0.45), t.lerp(atras, 0.0, 0.85), bisel=0.004)
    simple("reflectante_blanco", "#F2F2EE", 0.3, bisel=0.002)

    # ---- interior -------------------------------------------------------------------------------------------------
    t = nuevo("suelo_goma")
    x, y, z = t.xyz()
    botones = t.rango(t.voronoi(9.0, salida="Distance", aleatorio=0.0), 0.12, 0.08)
    col = t.mezcla(t.rango(t.ruido(2.0, detalle=3), 0.3, 0.7), "#2D3033", "#25282A")
    pisado = t.lejos_de(Vector((SILLA_X, -0.95, 0.3)), 0.2, 1.2)
    col = t.mezcla(t.mul(pisado, 0.3), col, "#45484A")
    t.terminar(col, t.lerp(pisado, 0.8, 0.6), 0.0, t.mul(botones, 0.006), bisel=0)

    simple("rodapie", "#2B2E31", 0.7, bisel=0.003)
    t = nuevo("encimera")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(1.2, detalle=3), 0.3, 0.7), "#8E8A80", "#9A958A")
    aros = t.rango(t.op("ABSOLUTE", t.resta(t.vop("DISTANCE", t.pos(), Vector((0.75, -2.15, 1.95))), 0.1)), 0.012,
                   0.0)
    col = t.mezcla(t.mul(t.mul(aros, t.mirando_arriba(0.8, 0.95)), 0.6), col, "#4A3524")
    codos = t.lejos_de(Vector((0.35, -1.85, 1.95)), 0.1, 0.7)
    col = t.mezcla(t.mul(codos, 0.25), col, "#B4AFA2")  # gastado donde apoya los brazos
    t.terminar(col, t.lerp(codos, 0.45, 0.25), 0.0, bisel=0.008)
    simple("mueble", "#4C535A", 0.55, 0.2, ruido=0.05)

    for nombre in ("pantalla_1", "pantalla_2"):
        t = nuevo(nombre)
        EMISIVOS.add(nombre)
        d = next(q for q in P["pantallas"] if q["calco"] == nombre)
        col, _ = calco_sobre(t, "#050806", nombre, d)
        t.terminar(col, 0.08, 0.0, emi=col, bisel=0)

    simple("walkie", "#24272A", 0.5, ruido=0.05)

    t = nuevo("tela_silla")
    x, y, z = t.xyz()
    trama = t.mul(t.suma(t.ola(90.0, direccion="X"), t.ola(90.0, direccion="Y")), 0.5)
    hueco = t.lejos_de(P["silla_hueco"], 0.05, 0.42)
    col = t.mezcla(t.rango(t.ruido(3.0, detalle=4), 0.3, 0.7), "#22385A", "#2A4268")
    col = t.mezcla(t.mul(hueco, 0.55), col, "#3E5778")       # tela clareada de tanto sentarse
    col = t.mezcla(t.mul(t.mul(hueco, t.rango(t.ruido(12.0, detalle=5), 0.45, 0.7)), 0.5), col, "#1A2232")  # brillo
    bolitas = t.mul(t.rango(t.voronoi(60.0, salida="Distance"), 0.15, 0.0), hueco)
    col = t.mezcla(t.mul(bolitas, 0.6), col, "#56708F")
    t.terminar(col, t.lerp(hueco, 0.9, 0.55), 0.0, t.suma(t.mul(trama, 0.0025), t.mul(bolitas, 0.002)), bisel=0.01)
    simple("cinta_americana", "#9CA0A3", 0.45, 0.4, bisel=0)

    simple("marco_foto", "#5B3B24", 0.5, ruido=0.08)
    t = nuevo("foto")
    col, _ = calco_sobre(t, "#808080", "foto", P["foto"])
    t.terminar(col, 0.15, 0.0, bisel=0)
    simple("termo", "#2D5A8C", 0.3, 0.6, ruido=0.04)
    simple("maceta", "#B0603A", 0.85, ruido=0.08)
    t = nuevo("cactus")
    costillas = t.ola(40.0, tipo="RINGS", dist=0.0)
    col = t.mezcla(t.rango(t.ruido(10.0), 0.3, 0.7), "#3F7A3A", "#4E8E45")
    t.terminar(col, 0.6, 0.0, t.mul(costillas, 0.004), bisel=0.01)
    simple("flor", "#E7508A", 0.5, bisel=0)
    simple("espina", "#EDE6CF", 0.6, bisel=0)
    simple("carton", "#8E6A44", 0.8, ruido=0.08)
    simple("papel_hoja", "#F1EEE4", 0.8, ruido=0.03)
    simple("boli", "#1F4FB0", 0.3, bisel=0.002)
    t = nuevo("gorra")
    col = t.mezcla(t.rango(t.ruido(5.0, detalle=4), 0.3, 0.7), "#1B2A44", "#22355A")
    col = t.mezcla(t.mul(t.borde(0.03), 0.4), col, "#41567A")
    t.terminar(col, 0.85, 0.0, t.mul(t.ola(120.0, direccion="Z"), 0.0015), bisel=0.008)

    t = nuevo("calendario")
    col, _ = calco_sobre(t, "#F2F0E8", "calendario", P["calendario"], cara=(0, -1, 0))
    t.terminar(col, 0.7, 0.0, bisel=0)
    simple("caja_llaves", "#7D1F1A", 0.5, 0.3, ruido=0.05)
    t = nuevo("reloj")
    x, y, z = t.xyz()
    t.terminar("#E9E7DF", 0.4, 0.0, bisel=0.006)

    t = nuevo("luz_techo")
    EMISIVOS.add("luz_techo")
    t.terminar("#FFF4DC", 0.3, 0.0, emi="#FFE7B8", bisel=0)

    # Cristales transparentes y neón brillante también en las vistas de modelado (malla alta).
    for nombre, alfa in (("vidrio", 0.16), ("vidrio_naranja", 0.55)):
        mats[nombre].node_tree.nodes["bsdf"].inputs["Alpha"].default_value = alfa
    bn = mats["neon"].node_tree.nodes["bsdf"]
    bn.inputs["Emission Color"].default_value = (*lin("#3DF2FF"), 1)
    bn.inputs["Emission Strength"].default_value = 6.0
    return mats


# Alturas de referencia (las rellena puesto_piezas al importarse).
SUELO_BAJO = -2.0      # z_oxido por debajo del suelo: sin óxido (el edificio es nuevo)
X1_INT = 2.45
SILLA_X = 0.35
