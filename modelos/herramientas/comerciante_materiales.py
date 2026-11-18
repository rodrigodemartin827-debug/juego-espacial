"""
Materiales de la casa del comerciante. Parte de los de la casa del minero (casa_materiales) y añade los suyos.

La historia que cuentan:
  * paneles más limpios que los del minero, y los de la fachada aún más nuevos (es la cara del negocio),
  * azul oscuro de la tienda desconchado solo en las esquinas y los cantos,
  * cristal del escaparate sin polvo (lo limpia cada día),
  * puerta de casa mucho más gastada que la de la tienda (entra y sale por ahí todo el día),
  * toldo descolorido por el sol en lo que mira arriba y en el borde de delante,
  * lona de la silla pelada en el centro del asiento.
"""

import casa_materiales as cm
from casa_materiales import Arbol, pintura_metal


def crear_materiales(P):
    mats = cm.crear_materiales(P)

    def nuevo(nombre):
        import bpy

        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        mats[nombre] = m
        return Arbol(m)

    # ---- paredes ----------------------------------------------------------------------------------------------
    t = nuevo("panel_limpio")
    col, rug, met, alt = pintura_metal(t, "#D8DBD8", variar_isla=[(0.5, "#CFD3D3"), (0.85, "#DEDDD3")],
                                       z_oxido=(P["zocalo_z"], P["zocalo_z"] + 0.7), desconchon=0.3,
                                       suciedad=0.25, chorretones=0.15)
    t.terminar(col, rug, met, alt, bisel=0.02)

    t = nuevo("panel_fachada")  # paneles más nuevos de la fachada de la tienda
    col, rug, met, alt = pintura_metal(t, "#E6E7E2", variar_isla=[(0.6, "#E1E4E4")],
                                       z_oxido=(P["zocalo_z"], P["zocalo_z"] + 0.45), desconchon=0.12,
                                       suciedad=0.15, chorretones=0.07, rug_pintura=0.42)
    t.terminar(col, rug, met, alt, bisel=0.02)

    t = nuevo("azul_tienda")  # marcos de la tienda: azul oscuro, desconchado en esquinas y cantos
    col, rug, met, alt = pintura_metal(t, "#1F3550", debajo="#A5ABB0", z_oxido=(0.6, 1.4), desconchon=1.0,
                                       rug_pintura=0.38, met_pintura=0.25, suciedad=0.25, chorretones=0.1,
                                       arañazos=(P["manija"], 0.1, 0.55))
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("metal_lateral")  # puerta de casa: gris verdoso, muy usada
    col, rug, met, alt = pintura_metal(t, "#55635D", debajo="#9EA3A6", z_oxido=(0.6, 1.8), desconchon=1.0,
                                       rug_pintura=0.5, met_pintura=0.2, suciedad=0.6, chorretones=0.45,
                                       arañazos=(P["manija_lateral"], 0.15, 0.85))
    x, y, z = t.xyz()
    mano = t.lejos_de(P["manija_lateral"], 0.05, 0.45)
    col = t.mezcla(t.mul(mano, 0.5), col, "#3B3A36")  # grasa de las manos alrededor de la manija
    pie = t.mul(t.rango(z, 1.1, 0.6), t.rango(t.ruido(9.0, detalle=4), 0.4, 0.7))
    col = t.mezcla(t.mul(pie, 0.6), col, "#5E5040")  # patadas de bota abajo
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("pintura_verde_silla")
    col, rug, met, alt = pintura_metal(t, "#2F5444", debajo="#9EA3A6", z_oxido=(0.5, 1.2), desconchon=0.9,
                                       rug_pintura=0.45, chorretones=0.1, suciedad=0.3)
    t.terminar(col, rug, met, alt, bisel=0.006)

    # ---- cubierta -----------------------------------------------------------------------------------------------
    t = nuevo("tela_asfaltica")
    x, y, z = t.xyz()
    grano = t.ruido(60.0, detalle=3)
    col = t.mezcla(t.rango(grano, 0.3, 0.7), "#3A3C3F", "#4A4B4C")
    charco = t.mul(t.rango(y, 2.0, 4.1), t.rango(t.ruido(1.2, detalle=3), 0.45, 0.6))
    col = t.mezcla(t.mul(charco, 0.6), col, "#56544C")  # cercos secos de charcos (abajo de la pendiente)
    col = t.mezcla(t.mul(t.rango(t.ruido(5.0, detalle=4), 0.6, 0.7), 0.4), col, "#2A2B2C")
    t.terminar(col, t.lerp(charco, 0.92, 0.75), 0.0, t.mul(grano, 0.004), bisel=0.01)

    # ---- vidrio, letreros, papel ----------------------------------------------------------------------------------
    t = nuevo("vidrio_limpio")
    t.terminar("#A6D3CF", 0.03, 0.0, bisel=0.003)

    t = nuevo("rotulo")
    t.terminar(t.mezcla(t.rango(t.ruido(30.0), 0.5, 0.7), "#F2EEDF", "#DCD6C3"), 0.35, 0.0, bisel=0.002)

    t = nuevo("tinta")
    t.terminar("#23262F", 0.6, 0.0, bisel=0)
    t = nuevo("tinta_roja")
    t.terminar("#9E2A22", 0.6, 0.0, bisel=0)

    t = nuevo("carton")
    x, y, z = t.xyz()
    fibras = t.ruido(25.0, detalle=5)
    col = t.mezcla(t.rango(fibras, 0.3, 0.7), "#A7804F", "#B88F5C")
    col = t.mezcla(t.mul(t.borde(0.03), 0.4), col, "#7A5A36")
    t.terminar(col, 0.9, 0.0, t.mul(fibras, 0.002), bisel=0.01)

    # ---- pizarra y tiza -------------------------------------------------------------------------------------------
    t = nuevo("pizarra")
    borrones = t.rango(t.ruido(3.0, t.estirar((1, 1, 0.5)), detalle=4), 0.45, 0.8)
    col = t.mezcla(t.mul(borrones, 0.35), "#1D211F", "#4B4F4B")  # restos de tiza borrada
    t.terminar(col, t.lerp(borrones, 0.85, 0.95), 0.0, t.mul(t.ruido(80.0), 0.0008), bisel=0)

    t = nuevo("tiza")
    roto = t.rango(t.ruido(120.0, detalle=2), 0.35, 0.6)  # el trazo de tiza no es continuo
    t.terminar(t.mezcla(roto, "#6B6E69", "#E9E7DE"), 0.95, 0.0, bisel=0)

    # ---- toldo: rayas blancas y azules, descolorido por el sol ----------------------------------------------------
    t = nuevo("toldo")
    x, y, z = t.xyz()
    rayas = t.rango(t.ola(0.5236, direccion="X", perfil="SIN"), 0.47, 0.53)
    blanco = t.mezcla(t.rango(t.ruido(2.0), 0.3, 0.7), "#ECE7DA", "#E2DCCB")
    azul = t.mezcla(t.rango(t.ruido(2.0), 0.3, 0.7), "#1E3A5E", "#24426A")
    col = t.mezcla(rayas, blanco, azul)
    sol = t.mirando_arriba(0.2, 0.7)
    frente = t.rango(y, P["toldo_frente_y"] + 0.55, P["toldo_frente_y"] - 0.05)
    quemado = t.op("MINIMUM", t.suma(t.mul(sol, 0.55), t.mul(frente, 0.5)), 1.0)
    quemado = t.mul(quemado, t.rango(t.ruido(1.5, detalle=3), 0.2, 0.8, 0.7, 1.0))
    palido = t.mezcla(rayas, "#F4EFE1", "#6C84A0")
    col = t.mezcla(quemado, col, palido)
    lluvia = t.mul(t.rango(t.ruido(3.0, t.estirar((0.6, 4, 4)), detalle=3), 0.6, 0.72), 0.35)
    col = t.mezcla(lluvia, col, "#8C8676")
    trama = t.mul(t.suma(t.ola(70.0, direccion="X"), t.ola(70.0, direccion="Y")), 0.5)
    t.terminar(col, 0.9, 0.0, t.mul(trama, 0.0012), bisel=0.004)

    t = nuevo("lona_silla")
    x, y, z = t.xyz()
    centro = t.lejos_de(P.get("silla_asiento", (6.0, -1.85, 2.05)), 0.05, 0.45)
    col = t.mezcla(t.rango(t.ruido(6.0, detalle=4), 0.3, 0.7), "#7B5E3C", "#6C5233")
    col = t.mezcla(t.mul(centro, 0.6), col, "#B49A74")  # gastada donde se sienta
    col = t.mezcla(t.mul(t.cavidad(0.05), 0.5), col, "#3A2B1C")
    trama = t.mul(t.suma(t.ola(90.0, direccion="X"), t.ola(90.0, direccion="Z")), 0.5)
    t.terminar(col, 0.92, 0.0, t.mul(trama, 0.0015), bisel=0.004)

    # ---- plásticos -------------------------------------------------------------------------------------------------
    for nombre, base, claro in (("plastico_naranja", "#D9832B", "#E9A65C"), ("plastico_gris", "#6F777D", "#9AA1A6"),
                                ("reciclaje", "#2F6E45", "#5D9A70")):
        t = nuevo(nombre)
        x, y, z = t.xyz()
        col = t.mezcla(t.rango(t.ruido(3.0, detalle=3), 0.3, 0.7), base, claro if nombre == "reciclaje" else base)
        roce = t.borde(0.03)
        col = t.mezcla(t.mul(roce, 0.5), col, claro)  # plástico blanqueado en los cantos
        sucio = t.mul(t.rango(z, 0.9, 0.0), t.rango(t.ruido(6.0, detalle=4), 0.3, 0.6))
        col = t.mezcla(t.mul(sucio, 0.5), col, "#4E4434")
        col = t.mezcla(t.mul(t.cavidad(0.06), 0.5), col, "#2B2620")
        rayas = t.rango(t.ruido(3.0, t.estirar((30, 30, 1.5)), detalle=1), 0.68, 0.72)
        t.terminar(col, t.lerp(rayas, 0.5, 0.75), 0.0, t.mul(rayas, -0.002), bisel=0.012)
    return mats
