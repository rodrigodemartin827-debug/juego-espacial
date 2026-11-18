"""
Materiales de la taberna. Parte de los de las otras casas y añade los suyos.

La historia que cuentan:
  * madera vieja y cálida, más gris y oscura abajo y en las juntas; más gastada (y sin pintura) junto a la puerta,
  * tablas del porche claras y lisas en el centro (el camino a la puerta) y oscuras en los bordes, con algún nudo,
  * pintura granate de los marcos levantada a trozos,
  * bisagras y herrajes oscurecidos por el uso, el latón de la barra de empuje pulido por las manos,
  * manchas de bebida en el escalón de entrada y musgo en sus esquinas,
  * puerta de atrás con abolladuras abajo (los barriles al entrar),
  * cristal ámbar (la luz de dentro).
"""

import casa_materiales as cm
import comerciante_materiales as com
from casa_materiales import Arbol, pintura_metal


def crear_materiales(P):
    mats = com.crear_materiales(P)

    def nuevo(nombre):
        import bpy

        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        mats[nombre] = m
        return Arbol(m)

    puerta = P["puerta_centro"]

    def madera(t, claro, oscuro, escala_veta=(0.12, 1.0, 1.0), lluvia=True, puerta_gastada=True, grano=5.0):
        x, y, z = t.xyz()
        isla = t.isla()
        tono = t.mezcla(t.rango(isla, 0.0, 1.0), claro, oscuro)
        tono = t.mezcla(t.rango(isla, 0.8, 0.81), tono, "#7C7466")  # alguna tabla cambiada, más gris
        veta = t.ola(grano, t.estirar(escala_veta), direccion="Y", dist=7.0, detalle=3.0)
        veta2 = t.ruido(3.0, t.estirar(tuple(1 / max(v, 0.05) for v in escala_veta)), detalle=5)
        vetas = t.rango(t.suma(t.mul(veta, 0.55), t.mul(veta2, 0.5)), 0.3, 1.0)
        col = t.mezcla(t.mul(vetas, 0.32), tono, "#5A3D26")
        nudo = t.rango(t.voronoi(1.3, salida="Distance"), 0.07, 0.025)
        col = t.mezcla(t.mul(nudo, 0.85), col, "#2F1E12")
        cav = t.cavidad(0.1)
        col = t.mezcla(t.mul(cav, 0.45), col, "#2E2014")
        rug = 0.78
        if lluvia:
            abajo = t.rango(z, 3.6, 2.6)
            col = t.mezcla(t.mul(abajo, 0.45), col, "#5E584E")  # madera lavada abajo
        if puerta_gastada:
            cerca = t.lejos_de(puerta, 0.6, 2.4)
            col = t.mezcla(t.mul(cerca, 0.5), col, "#A07A52")
            rug = t.lerp(cerca, 0.78, 0.6)
        alt = t.suma(t.mul(vetas, 0.005), t.mul(nudo, -0.004))
        return col, rug, alt

    t = nuevo("madera_vieja")
    col, rug, alt = madera(t, "#B07E4E", "#8E633C")
    t.terminar(col, rug, 0.0, alt, bisel=0.012)

    t = nuevo("madera_saloon")
    col, rug, alt = madera(t, "#A06A3C", "#80532E", escala_veta=(0.12, 1.0, 1.0), lluvia=False)
    t.terminar(col, rug, 0.0, alt, bisel=0.012)

    t = nuevo("madera_banco")
    col, rug, alt = madera(t, "#AE8456", "#946B42", lluvia=False, puerta_gastada=False)
    centro = t.lejos_de(P["silla_asiento"], 0.3, 1.9)
    col = t.mezcla(t.mul(centro, 0.45), col, "#B08A60")  # asiento pulido por miles de sentadas
    t.terminar(col, t.lerp(centro, 0.75, 0.45), 0.0, alt, bisel=0.015)

    t = nuevo("madera_porche")
    x, y, z = t.xyz()
    col, rug, alt = madera(t, "#9C7448", "#7E5A36", lluvia=False, puerta_gastada=False)
    # Camino de la puerta: centro del porche claro y liso; bordes oscuros y grises.
    camino = t.mul(t.rango(t.op("ABSOLUTE", t.resta(x, puerta[0])), 4.5, 0.5),
                   t.rango(y, P["porche_y"][1] - 0.2, P["porche_y"][0], 0.6, 1.0))
    col = t.mezcla(t.mul(camino, 0.55), col, "#B39070")
    borde = t.rango(t.op("ABSOLUTE", x), 5.2, 6.3)
    col = t.mezcla(t.mul(borde, 0.5), col, "#4A4038")
    manchas = t.mul(t.rango(t.voronoi(2.5, salida="Distance"), 0.12, 0.04), 0.5)
    col = t.mezcla(manchas, col, "#3A2516")
    t.terminar(col, t.lerp(camino, 0.82, 0.55), 0.0, t.suma(alt, t.mul(camino, -0.002)), bisel=0.012)

    t = nuevo("madera_barril")
    x, y, z = t.xyz()
    veta = t.ruido(4.0, t.estirar((14, 14, 0.6)), detalle=5)
    col = t.mezcla(t.rango(veta, 0.3, 0.8), "#6E6052", "#4C4036")  # roble envejecido, casi gris
    col = t.mezcla(t.mul(t.rango(t.ruido(5.0, detalle=4), 0.55, 0.7), 0.6), col, "#5A4E30")  # verdín
    t.terminar(col, 0.88, 0.0, t.mul(veta, 0.005), bisel=0.01)

    t = nuevo("tronco")
    x, y, z = t.xyz()
    corteza = t.ruido(2.5, t.estirar((8, 8, 0.6)), detalle=6, tipo="RIDGED_MULTIFRACTAL")
    col = t.mezcla(t.rango(corteza, 0.4, 1.0), "#3C2C20", "#6E5A46")
    pelado = t.rango(t.ruido(1.2, detalle=3), 0.55, 0.62)
    col = t.mezcla(pelado, col, "#8D6E4E")  # zonas sin corteza
    altura = t.rango(z, 2.0, 3.0, 1.0, 0.0)
    roce = t.mul(altura, t.rango(t.ruido(3.0), 0.4, 0.7))
    col = t.mezcla(t.mul(roce, 0.4), col, "#9A7A58")  # pulido donde se apoya la gente
    t.terminar(col, 0.9, 0.0, t.mul(t.lerp(pelado, corteza, 0.2), 0.03), bisel=0)

    t = nuevo("cartel_madera")
    x, y, z = t.xyz()
    veta = t.ola(4.0, t.estirar((0.15, 1, 1)), direccion="Z", dist=6.0, detalle=3.0)
    col = t.mezcla(t.rango(veta, 0.2, 1.0), "#7A5232", "#5A3A20")
    col = t.mezcla(t.mul(t.cavidad(0.05), 0.6), col, "#1E120A")
    t.terminar(col, 0.55, 0.0, t.mul(veta, 0.005), bisel=0.02)

    t = nuevo("dorado")  # letras talladas y doradas, con el oro gastado en los cantos
    borde = t.borde(0.01)
    col = t.mezcla(t.mul(borde, 0.6), "#C9A04A", "#8C6A2E")
    col = t.mezcla(t.mul(t.cavidad(0.03), 0.7), col, "#4A3418")
    t.terminar(col, t.lerp(borde, 0.3, 0.5), t.lerp(borde, 0.9, 0.5), bisel=0.006)

    t = nuevo("pintura_granate")
    x, y, z = t.xyz()
    veta = t.ruido(3.0, t.estirar((12, 12, 0.6)), detalle=5)
    madera_d = t.mezcla(t.rango(veta, 0.3, 0.8), "#7D6A58", "#5A4A3C")
    pintura = t.mezcla(t.rango(t.ruido(1.5, detalle=2), 0.3, 0.7), "#6B2620", "#7E2E26")
    borde = t.borde(0.03)
    pelado = t.rango(t.suma(t.ruido(5.0, detalle=5, rug=0.7), t.mul(borde, 0.45)), 0.6, 0.64)
    cerca = t.lejos_de(puerta, 0.4, 1.6)
    pelado = t.maxi(pelado, t.mul(cerca, t.rango(t.ruido(7.0, detalle=4), 0.42, 0.5)))
    col = t.mezcla(pelado, pintura, madera_d)
    col = t.mezcla(t.mul(t.cavidad(0.08), 0.5), col, "#2A1A12")
    t.terminar(col, t.lerp(pelado, 0.5, 0.8), 0.0, t.suma(t.mul(pelado, -0.004), t.mul(veta, t.mul(pelado, 0.004))),
               bisel=0.012)

    t = nuevo("chapa_taberna")  # tejado de chapa pintada de rojo óxido, descolorida y con churretes
    col, rug, met, alt = pintura_metal(t, "#7E4A36", variar_isla=[(0.6, "#8A5640"), (0.85, "#6E4434")],
                                       debajo="#9EA3A6", z_oxido=(5.4, 6.4), desconchon=0.9, suciedad=0.6,
                                       chorretones=0.55, rug_pintura=0.55)
    t.terminar(col, rug, met, alt, bisel=0.015)

    t = nuevo("panel_viejo")  # banda de chapa de abajo: gris verdoso con mucho óxido
    col, rug, met, alt = pintura_metal(t, "#5D6A64", variar_isla=[(0.5, "#66706A"), (0.8, "#555E5A")],
                                       z_oxido=(1.6, 2.7), desconchon=1.0, suciedad=0.6, chorretones=0.5)
    t.terminar(col, rug, met, alt, bisel=0.02)

    t = nuevo("metal_trasera")  # puerta de atrás: abollada abajo por los barriles
    col, rug, met, alt = pintura_metal(t, "#4F5A5E", debajo="#A2A6A8", z_oxido=(1.0, 2.0), desconchon=1.0,
                                       suciedad=0.6, chorretones=0.4)
    x, y, z = t.xyz()
    abajo = t.rango(z, 2.2, 1.3)
    golpes = t.rango(t.voronoi(5.0, salida="Distance"), 0.22, 0.0)
    golpe = t.mul(abajo, golpes)
    rayas = t.mul(abajo, t.rango(t.ruido(3.0, t.estirar((2, 2, 30)), detalle=1), 0.66, 0.7))
    col = t.mezcla(t.mul(t.maxi(golpe, rayas), 0.6), col, "#9EA2A4")
    t.terminar(col, rug, t.lerp(golpe, met, 0.7), t.suma(alt, t.mul(golpe, -0.03)), bisel=0.012)

    t = nuevo("barril_metal")
    col, rug, met, alt = pintura_metal(t, "#2E4A5E", debajo="#A9AEB2", z_oxido=(1.0, 1.6), desconchon=1.0,
                                       suciedad=0.4, chorretones=0.3)
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("hierro_gastado")  # barra del cerrojo: brillante donde roza
    t.terminar("#8D8F90", 0.3, 1.0, t.mul(t.ruido(60.0), 0.002), bisel=0.006)

    t = nuevo("laton_gastado")  # barra de empuje de las puertas: pulida por las manos en el centro
    x, y, z = t.xyz()
    centro = t.lejos_de(puerta, 0.2, 1.0)
    col = t.mezcla(centro, "#8A6A35", "#D8B46A")
    t.terminar(col, t.lerp(centro, 0.5, 0.15), 1.0, bisel=0.006)

    t = nuevo("piedra_oscura")
    t.terminar(t.mezcla(t.rango(t.ruido(4.0, detalle=4), 0.3, 0.7), "#1F1C19", "#2C2723"), 0.95, 0.0, bisel=0)

    t = nuevo("losa_taberna")  # escalones: gastados en el centro, musgo en las esquinas, manchas de bebida
    x, y, z = t.xyz()
    var = t.ruido(3.0, detalle=6, rug=0.6)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#8A8378", "#757066")
    gastado = t.lejos_de(P["escalon_centro"], 0.3, 2.6)
    col = t.mezcla(t.mul(gastado, 0.5), col, "#AAA396")
    musgo = t.mul(t.rango(t.op("ABSOLUTE", x), 4.6, 6.1), t.rango(t.ruido(5.0, detalle=5), 0.35, 0.6))
    col = t.mezcla(t.mul(musgo, 0.85), col, "#4F6230")
    bebida = t.mul(t.lejos_de(P["escalon_centro"], 0.2, 1.6),
                   t.rango(t.voronoi(3.5, salida="Distance"), 0.16, 0.06))
    aros = t.mul(t.lejos_de(P["escalon_centro"], 0.2, 1.6), t.rango(t.voronoi(3.5, salida="Distance"), 0.2, 0.17))
    col = t.mezcla(t.mul(bebida, 0.55), col, "#4A3220")
    col = t.mezcla(t.mul(aros, 0.5), col, "#3A2616")
    col = t.mezcla(t.mul(t.cavidad(0.12), 0.6), col, "#3A352F")
    t.terminar(col, t.lerp(bebida, t.lerp(gastado, 0.88, 0.55), 0.35), 0.0,
               t.mul(var, t.lerp(gastado, 0.012, 0.002)), bisel=0.05)

    # ---- vidrio, bebida, cuerda, corcho... -----------------------------------------------------------------------
    t = nuevo("vidrio_ambar")
    polvo = t.mul(t.rango(t.ruido(6.0, detalle=4), 0.5, 0.75), 0.5)
    t.terminar(t.mezcla(polvo, "#C9852E", "#9A8060"), t.lerp(polvo, 0.05, 0.4), 0.0, bisel=0.004)
    t = nuevo("vidrio_jarra")
    t.terminar("#C7D5CF", 0.08, 0.0, bisel=0.004)
    t = nuevo("cerveza")
    t.terminar("#B8741E", 0.1, 0.0, bisel=0)
    t = nuevo("espuma")
    t.terminar(t.mezcla(t.rango(t.ruido(40.0), 0.3, 0.7), "#F2EAD8", "#E0D2B4"), 0.7, 0.0,
               t.mul(t.ruido(40.0), 0.01), bisel=0)
    t = nuevo("botella")
    t.terminar(t.mezcla(t.rango(t.ruido(3.0), 0.4, 0.6), "#3E5A2E", "#5C3A1C"), 0.12, 0.0, bisel=0.004)
    t = nuevo("neon_calido")
    t.terminar("#FFB45A", 0.3, 0.0, emi="#FFB45A", bisel=0)
    t = nuevo("cuerda")
    trenza = t.ola(60.0, direccion="Z", dist=2.0)
    t.terminar(t.mezcla(t.rango(trenza, 0.3, 0.8), "#8F7550", "#6A5236"), 0.95, 0.0, t.mul(trenza, 0.003), bisel=0)
    t = nuevo("corcho")
    granos = t.voronoi(60.0, salida="Distance")
    col = t.mezcla(t.rango(granos, 0.0, 0.5), "#8E6436", "#B98D58")
    agujeros = t.rango(t.voronoi(9.0, salida="Distance"), 0.04, 0.0)
    col = t.mezcla(t.mul(agujeros, 0.8), col, "#3A2614")  # agujeros de chinchetas antiguas
    t.terminar(col, 0.95, 0.0, t.suma(t.mul(granos, 0.003), t.mul(agujeros, -0.003)), bisel=0.004)
    t = nuevo("ceniza")
    t.terminar(t.mezcla(t.rango(t.ruido(30.0, detalle=4), 0.3, 0.7), "#5A5753", "#9A958C"), 0.95, 0.0,
               t.mul(t.ruido(30.0), 0.004), bisel=0)
    t = nuevo("hollin_rejilla")
    t.terminar("#141210", 0.9, 0.0, bisel=0)

    # ---- speeder bike --------------------------------------------------------------------------------------------
    t = nuevo("pintura_speeder")
    col, rug, met, alt = pintura_metal(t, "#C25A23", debajo="#B8BCBF", z_oxido=(0.0, 0.4), desconchon=0.8,
                                       rug_pintura=0.32, met_pintura=0.35, suciedad=0.3, chorretones=0.15)
    x, y, z = t.xyz()
    franja = t.rango(t.op("ABSOLUTE", t.resta(z, 1.0)), 0.05, 0.03)
    col = t.mezcla(franja, col, "#1E2A33")
    t.terminar(col, rug, met, alt, bisel=0.015)
    t = nuevo("metal_speeder")
    col, rug, met, alt = pintura_metal(t, "#3A4249", debajo="#B8BCBF", z_oxido=(0.0, 0.3), desconchon=0.8,
                                       rug_pintura=0.35, met_pintura=0.6, suciedad=0.4, chorretones=0.1)
    t.terminar(col, rug, met, alt, bisel=0.01)
    return mats
