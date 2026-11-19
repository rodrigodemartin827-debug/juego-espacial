"""
Materiales del taller. Parte de los de las casas (casa_materiales) y añade los suyos.

La historia que cuentan:
  * chapa gris oscuro de los muros, cada paño de un tono (se han ido cambiando), con óxido abajo y churretes;
    HOLLÍN encima del extractor de atrás (sube en penacho) y bajo el extractor del techo; GRASA alrededor del banco,
    de la jamba del portón (manos) y de la manija de la puerta lateral,
  * portón azul acero con el borde de abajo QUEMADO por la soldadura (tintes de calor, hollín y gotas de metal
    pegadas), la pintura pelada en los cantos y rozada alrededor del tirador,
  * losa de hormigón con MANCHAS DE ACEITE permanentes delante del portón y por dentro, las rodadas que entran,
    el charco del grifo de purga del compresor y el goteo de la soldadora,
  * zócalo de hormigón con las juntas del encofrado, los agujeros de los latiguillos, churretes de óxido bajo las
    pletinas y salpicaduras de barro,
  * tablero del banco lleno de rayas, golpes de martillo y quemaduras; panel perforado con las siluetas pintadas,
  * bidones con chorretones de lo que guardan bajo la boca, etiquetas y abolladuras.
"""

import bpy

import casa_materiales as cm
from casa_materiales import Arbol, pintura_metal


def crear_materiales(P):
    mats = cm.crear_materiales(P)

    def nuevo(nombre):
        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        mats[nombre] = m
        return Arbol(m)

    def mezclar(t, col, rug, mascara, color, rug_valor, fuerza=1.0):
        f = t.mul(mascara, fuerza) if fuerza != 1.0 else mascara
        return t.mezcla(f, col, color), t.lerp(f, rug, rug_valor)

    def hollin_extractor(t):
        """Hollín bajo el extractor del techo (en el techo y el muro de atrás) y en penacho sobre el de atrás."""
        x, y, z = t.xyz()
        ex, ey, ez = P["extractor"]
        cerca = t.lejos_de((ex, ey, ez - 0.4), 0.5, 2.4)
        # Churretes que bajan por la bóveda hacia el alero (a lo largo de x) y por el muro de atrás.
        churre = t.rango(t.ruido(1.6, t.estirar((0.25, 5.0, 2.0)), detalle=4), 0.42, 0.7)
        franja = t.rango(t.op("ABSOLUTE", t.resta(y, ey)), 1.3, 0.5)
        abajo_x = t.mul(t.rango(x, ex - 0.6, ex + 0.2), t.rango(x, ex + 4.5, ex + 1.0))
        hollin = t.maxi(cerca, t.mul(t.mul(churre, franja), abajo_x))
        fx, fy, fz = P["ventilador"]
        dx = t.op("ABSOLUTE", t.resta(x, fx))
        ancho = t.suma(0.55, t.mul(t.maxi(t.resta(z, fz), 0.0), 0.32))
        cono = t.rango(t.op("DIVIDE", dx, ancho), 1.0, 0.35)
        vert = t.mul(t.rango(z, fz - 0.65, fz - 0.15), t.rango(z, fz + 2.9, fz + 0.6))
        detras = t.rango(y, P["ventilador"][1] - 0.6, P["ventilador"][1] - 0.3)
        penacho = t.mul(t.mul(cono, vert), detras)
        penacho = t.mul(penacho, t.rango(t.ruido(2.5, t.estirar((3.0, 3.0, 0.7)), detalle=4), 0.25, 0.65, 0.45, 1.0))
        return t.op("MINIMUM", t.maxi(hollin, penacho), 1.0)

    def grasa_manos(t):
        """Grasa negra donde se apoyan las manos: junto al banco, la jamba del portón y la puerta lateral."""
        x, y, z = t.xyz()
        banco = t.mul(t.lejos_de(P["banco"], 0.6, 2.0), t.rango(z, P["banco"][2] + 1.3, P["banco"][2] + 0.2))
        jamba = t.lejos_de((P["porton_borde_x"] + 0.3, -4.6, 1.9), 0.1, 0.8)
        puerta = t.lejos_de(P["puerta_lateral_manija"], 0.15, 0.9)
        m = t.maxi(t.maxi(banco, jamba), puerta)
        manchas = t.rango(t.ruido(7.0, detalle=5, rug=0.7), 0.42, 0.62)
        return t.mul(m, manchas)

    # ---- muros y techo ---------------------------------------------------------------------------------------
    t = nuevo("chapa_muro")
    col, rug, met, alt = pintura_metal(
        t, "#4C5258", variar_isla=[(0.3, "#454B52"), (0.55, "#535A5F"), (0.78, "#4A4E50"), (0.92, "#3F4650")],
        debajo="#8E9398", z_oxido=(P["zocalo_z"], P["zocalo_z"] + 1.0), desconchon=0.55, suciedad=0.55,
        chorretones=0.5, rug_pintura=0.55, met_pintura=0.25, arañazos=(P["banco"], 0.5, 2.2))
    col, rug = mezclar(t, col, rug, hollin_extractor(t), "#141312", 0.95, 0.92)
    col, rug = mezclar(t, col, rug, grasa_manos(t), "#1A1714", 0.35, 0.85)
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("chapa_remate")
    col, rug, met, alt = pintura_metal(t, "#2E3236", debajo="#9A9FA4", z_oxido=(P["zocalo_z"], P["zocalo_z"] + 0.6),
                                       desconchon=0.8, suciedad=0.45, chorretones=0.3, met_pintura=0.3)
    col, rug = mezclar(t, col, rug, hollin_extractor(t), "#121110", 0.95, 0.8)
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("chapa_techo_taller")
    col, rug, met, alt = pintura_metal(
        t, "#6E767C", variar_isla=[(0.4, "#687076"), (0.7, "#757C80"), (0.9, "#5F676D")], debajo="#A3A9AD",
        z_oxido=(4.0, 4.9), desconchon=0.5, suciedad=0.4, chorretones=0.0, rug_pintura=0.5, met_pintura=0.35)
    x, y, z = t.xyz()
    sol = t.mirando_arriba(0.85, 0.99)
    col = t.mezcla(t.mul(sol, 0.25), col, "#8E959A")  # descolorido por el sol en la cumbrera
    col, rug = mezclar(t, col, rug, hollin_extractor(t), "#151413", 0.92, 0.95)
    # Hojas y polvo acumulados contra los nervios (lado de arriba).
    polvo = t.mul(t.cavidad(0.18), t.rango(t.ruido(3.0, detalle=4), 0.35, 0.7))
    col = t.mezcla(t.mul(polvo, 0.55), col, "#6A5A45")
    t.terminar(col, rug, met, alt, bisel=0.015)

    t = nuevo("interior_techo")
    t.terminar(t.mezcla(t.rango(t.ruido(2.0, detalle=3), 0.3, 0.7), "#4E5254", "#5C6062"), 0.7, 0.4, bisel=0)

    t = nuevo("metal_marco")
    col, rug, met, alt = pintura_metal(t, "#2C2F33", debajo="#A2A6A9", z_oxido=(0.0, 0.9), desconchon=1.0,
                                       suciedad=0.5, chorretones=0.25, met_pintura=0.35, rug_pintura=0.45)
    col, rug = mezclar(t, col, rug, grasa_manos(t), "#161412", 0.3, 0.9)
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("metal_hollin_taller")
    col, rug, met, alt = pintura_metal(t, "#3B4045", debajo="#8E9398", z_oxido=(0.0, 0.5), desconchon=0.7,
                                       suciedad=0.6, chorretones=0.4, met_pintura=0.35)
    col, rug = mezclar(t, col, rug, hollin_extractor(t), "#121110", 0.95, 1.0)
    x, y, z = t.xyz()
    boca = t.lejos_de(P["ventilador"], 0.2, 0.75)
    col, rug = mezclar(t, col, rug, boca, "#100F0E", 0.95, 0.9)
    t.terminar(col, rug, met, alt, bisel=0.012)

    # ---- hormigón ------------------------------------------------------------------------------------------
    t = nuevo("hormigon_zocalo")
    x, y, z = t.xyz()
    var = t.ruido(1.3, detalle=4)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#8F8B83", "#7E7A72")
    # Tablas del encofrado: bandas horizontales con su junta.
    tabla = t.ola(1.0 / 0.32 / 1.0, t.estirar((0.0, 0.0, 1.0)), direccion="Z", perfil="SAW")
    junta_enc = t.rango(tabla, 0.95, 0.99)
    col = t.mezcla(t.mul(junta_enc, 0.5), col, "#5E5A52")
    veta_enc = t.ruido(2.0, t.estirar((0.6, 0.6, 9.0)), detalle=4)
    col = t.brillo(col, t.rango(veta_enc, 0.3, 0.7, 0.92, 1.06))
    # Agujeros de los latiguillos: rejilla regular a lo largo del muro (x + y) y en dos alturas.
    uu = t.suma(x, y)
    fu = t.op("ABSOLUTE", t.resta(t.op("FRACT", t.op("DIVIDE", uu, 1.15)), 0.5))
    fz = t.op("ABSOLUTE", t.resta(t.op("FRACT", t.op("DIVIDE", t.resta(z, 0.12), 0.62)), 0.5))
    d_ag = t.op("SQRT", t.suma(t.mul(t.mul(fu, 1.15), t.mul(fu, 1.15)), t.mul(t.mul(fz, 0.62), t.mul(fz, 0.62))))
    agujero = t.rango(d_ag, 0.045, 0.03)
    col = t.mezcla(agujero, col, "#2E2B27")
    # Poros, grietas, óxido bajo las pletinas, barro salpicado y oscuro de humedad abajo.
    poros = t.rango(t.voronoi(30.0, salida="Distance"), 0.1, 0.02)
    col = t.mezcla(t.mul(poros, 0.6), col, "#4F4B45")
    grieta = t.rango(t.ruido(1.4, detalle=6, tipo="RIDGED_MULTIFRACTAL"), 0.9, 0.97)
    col = t.mezcla(grieta, col, "#3A3631")
    oxido = t.mul(t.rango(t.ruido(1.2, t.estirar((5.0, 5.0, 0.35)), detalle=3), 0.55, 0.75), t.rango(z, 0.4, 1.4))
    col = t.mezcla(t.mul(oxido, 0.5), col, "#7A4A2C")
    humedad = t.mul(t.rango(z, 0.55, 0.1), t.rango(t.ruido(2.5, detalle=4), 0.3, 0.7, 0.5, 1.0))
    col = t.mezcla(t.mul(humedad, 0.6), col, "#55504A")
    barro = t.mul(t.rango(z, 0.6, 0.15), t.rango(t.ruido(9.0, detalle=5), 0.5, 0.65))
    col = t.mezcla(barro, col, "#5A4A38")
    aceite = t.mul(t.rango(z, 0.7, 0.1), t.lejos_de(P["porton_centro"], 1.5, 3.5))
    col = t.mezcla(t.mul(aceite, t.rango(t.ruido(5.0, detalle=4), 0.45, 0.7)), col, "#2B2620")
    cav = t.cavidad(0.12)
    col = t.mezcla(t.mul(cav, 0.55), col, "#3E3A33")
    borde = t.borde(0.06)
    rotura = t.rango(t.ruido(10.0, detalle=4), 0.45, 0.6)
    col = t.mezcla(t.mul(borde, t.mul(rotura, 0.6)), col, "#B4AFA4")
    alt = t.suma(t.mul(t.ruido(12.0, detalle=6), 0.006), t.mul(poros, -0.008))
    alt = t.suma(alt, t.suma(t.mul(grieta, -0.012), t.mul(agujero, -0.02)))
    alt = t.suma(alt, t.mul(junta_enc, -0.006))
    t.terminar(col, t.lerp(aceite, 0.9, 0.55), 0.0, alt, bisel=0.05)

    t = nuevo("losa_taller")
    x, y, z = t.xyz()
    var = t.ruido(0.8, detalle=4)
    col = t.mezcla(t.rango(var, 0.3, 0.7), "#8C877E", "#7A756C")
    col = t.brillo(col, t.rango(t.ruido(6.0, detalle=6), 0.3, 0.7, 0.93, 1.05))
    # Rodadas que entran por el portón.
    pc = P["porton_centro"]
    rueda = t.maxi(t.rango(t.op("ABSOLUTE", t.resta(x, pc[0] - 0.85)), 0.32, 0.08),
                   t.rango(t.op("ABSOLUTE", t.resta(x, pc[0] + 0.85)), 0.32, 0.08))
    rueda = t.mul(rueda, t.rango(y, pc[1] - 3.5, pc[1] - 0.4, 0.35, 1.0))
    rueda = t.mul(rueda, t.rango(y, pc[1] + 4.5, pc[1] + 1.0))
    col = t.mezcla(t.mul(rueda, t.rango(t.ruido(4.0, t.estirar((3, 0.3, 1)), detalle=4), 0.3, 0.7, 0.25, 0.6)), col,
                   "#3E3A34")
    # Manchas de aceite: manchones de bordes irregulares con el cerco más oscuro, sobre todo delante del portón.
    def manchas_aceite(escala, umbral, desplazar=(0, 0, 0)):
        deform = t.vop("ADD", t.estirar((1, 1, 1), desplazar=desplazar), t.vop("MULTIPLY", t.vop(
            "SUBTRACT", _ruido_color(t, 1.2), (0.5, 0.5, 0.5)), (0.8, 0.8, 0.0)))
        d = t.voronoi(escala, deform, salida="Distance")
        return t.rango(d, umbral, umbral * 0.55), t.rango(d, umbral, umbral * 0.85)

    zona = t.maxi(t.lejos_de(P["porton_suelo"], 0.6, 2.6), t.lejos_de((pc[0], pc[1] + 2.4, 0.08), 0.8, 3.0))
    zona = t.maxi(zona, t.mul(t.lejos_de(P["compresor_purga"], 0.1, 0.9), 1.0))
    grande, cerco = manchas_aceite(0.9, 0.34)
    peq, cerco_p = manchas_aceite(3.2, 0.2, desplazar=(3.1, 1.7, 0))
    aceite = t.maxi(t.mul(grande, zona), t.mul(peq, t.mul(t.suma(zona, 0.25), 0.9)))
    aceite = t.op("MINIMUM", aceite, 1.0)
    col = t.mezcla(t.mul(aceite, 0.85), col, "#2A241D")
    col = t.mezcla(t.mul(t.mul(t.resta(cerco, grande, clamp=True), zona), 0.6), col, "#1C1915")
    # Goteos de la soldadora y charco del grifo de purga del compresor.
    goteo = t.mul(t.lejos_de(P["soldadora"], 0.1, 1.2), t.rango(t.voronoi(9.0, salida="Distance"), 0.14, 0.06))
    col = t.mezcla(goteo, col, "#2E2822")
    purga = t.lejos_de(P["compresor_purga"], 0.15, 0.55)
    col = t.mezcla(t.mul(purga, 0.8), col, "#3A3128")
    # Juntas, grietas, polvo y salpicaduras de pintura.
    grieta = t.rango(t.ruido(0.9, detalle=7, tipo="RIDGED_MULTIFRACTAL"), 0.9, 0.97)
    col = t.mezcla(grieta, col, "#3A3630")
    pintura = t.mul(t.rango(t.voronoi(5.0, salida="Distance"), 0.035, 0.015), t.lejos_de(P["banco"], 0.5, 2.0))
    col = t.mezcla(pintura, col, "#C9692D")
    cav = t.cavidad(0.15)
    col = t.mezcla(t.mul(cav, 0.55), col, "#3B372F")
    rug = t.lerp(aceite, 0.92, 0.22)
    rug = t.lerp(purga, rug, 0.3)
    alt = t.suma(t.mul(t.ruido(10.0, detalle=6), 0.006), t.mul(grieta, -0.012))
    t.terminar(col, rug, 0.0, alt, bisel=0.04)

    # ---- portón y puertas --------------------------------------------------------------------------------------
    t = nuevo("metal_porton")
    col, rug, met, alt = pintura_metal(
        t, "#3C5A6B", variar_isla=[(0.6, "#41606F"), (0.85, "#375463")], debajo="#A4A8AB", z_oxido=(0.2, 1.3),
        desconchon=0.9, suciedad=0.5, chorretones=0.35, rug_pintura=0.5, met_pintura=0.3,
        arañazos=(P["porton_centro"][:2] + (2.38,), 0.4, 1.3))
    x, y, z = t.xyz()
    # Quemaduras de soldadura en el borde de abajo: tintes de calor, hollín y gotas de metal pegadas.
    zq = P["porton_quemaduras_z"]
    bajo = t.rango(z, zq + 0.25, 0.25, suave=True)
    manchon = t.rango(t.ruido(1.8, detalle=5, rug=0.65), 0.38, 0.62)
    quema = t.mul(bajo, manchon)
    tinte = t.ruido(5.0, detalle=3)
    color_calor = t.mezcla(t.rango(tinte, 0.3, 0.5), "#6F4E2A", "#4A3355")
    color_calor = t.mezcla(t.rango(tinte, 0.5, 0.72), color_calor, "#2B3C5E")
    col = t.mezcla(t.mul(quema, 0.9), col, color_calor)
    centro_q = t.rango(t.ruido(1.8, detalle=5, rug=0.65), 0.52, 0.7)
    col = t.mezcla(t.mul(t.mul(bajo, centro_q), 0.95), col, "#151311")
    gotas = t.mul(bajo, t.rango(t.voronoi(55.0, salida="Distance"), 0.09, 0.03))
    gotas = t.mul(gotas, t.rango(t.ruido(3.0), 0.4, 0.6))
    col = t.mezcla(gotas, col, "#8A8D90")
    rug = t.lerp(quema, rug, 0.75)
    rug = t.lerp(gotas, rug, 0.35)
    met = t.lerp(quema, met, 0.55)
    met = t.lerp(gotas, met, 1.0)
    alt = t.suma(alt, t.mul(gotas, 0.012))
    # Grasa de manos alrededor del tirador.
    manos = t.mul(t.lejos_de((P["porton_borde_x"] - 0.6, -4.95, 2.38), 0.1, 0.65),
                  t.rango(t.ruido(8.0, detalle=4), 0.4, 0.6))
    col, rug = mezclar(t, col, rug, manos, "#1F1C19", 0.4, 0.8)
    t.terminar(col, rug, met, alt, bisel=0.012)

    t = nuevo("metal_porton_dentro")
    col, rug, met, alt = pintura_metal(t, "#6C706E", debajo="#9EA3A6", z_oxido=(0.2, 1.0), desconchon=0.5,
                                       suciedad=0.6, chorretones=0.2)
    t.terminar(col, rug, met, alt, bisel=0.01)

    t = nuevo("metal_puerta")
    col, rug, met, alt = pintura_metal(
        t, "#56664E", variar_isla=None, debajo="#A2A6A9", z_oxido=(0.0, 1.0), desconchon=1.0, suciedad=0.65,
        chorretones=0.35, rug_pintura=0.55, arañazos=(P["puerta_lateral_manija"], 0.25, 0.95))
    col, rug = mezclar(t, col, rug, grasa_manos(t), "#1A1714", 0.35, 0.95)
    x, y, z = t.xyz()
    patadas = t.mul(t.rango(z, 1.0, 0.3), t.rango(t.voronoi(4.0, salida="Distance"), 0.2, 0.05))
    col = t.mezcla(t.mul(patadas, 0.7), col, "#3A3630")
    t.terminar(col, rug, met, t.suma(alt, t.mul(patadas, -0.01)), bisel=0.012)

    t = nuevo("chapa_patada")
    x, y, z = t.xyz()
    rayas = t.rango(t.ruido(2.0, t.estirar((1.0, 30.0, 1.0)), detalle=2), 0.55, 0.7)
    abolladura = t.rango(t.voronoi(3.0, salida="Distance"), 0.3, 0.05)
    col = t.mezcla(t.rango(t.ruido(6.0), 0.3, 0.7), "#8A8E91", "#9EA2A5")
    col = t.mezcla(t.mul(rayas, 0.6), col, "#C3C6C8")
    col = t.mezcla(t.mul(t.cavidad(0.06), 0.6), col, "#3A3632")
    col = t.mezcla(t.mul(t.rango(z, 0.6, 0.15), 0.5), col, "#5A4C3E")
    t.terminar(col, t.lerp(rayas, 0.45, 0.3), 0.9, t.suma(t.mul(abolladura, -0.025), t.mul(rayas, 0.002)),
               bisel=0.006)

    t = nuevo("hierro_bisagra")
    x, y, z = t.xyz()
    grasa = t.rango(t.ruido(6.0, detalle=4), 0.45, 0.65)
    col = t.mezcla(t.rango(t.ruido(10.0), 0.3, 0.7), "#2C2B2A", "#3A3836")
    col = t.mezcla(t.mul(t.borde(0.02), 0.6), col, "#7E8184")
    col = t.mezcla(t.mul(grasa, 0.6), col, "#1A1714")
    t.terminar(col, t.lerp(grasa, 0.55, 0.25), 0.85, t.mul(t.ruido(30.0, detalle=4), 0.004), bisel=0.01)

    # ---- aceros varios -------------------------------------------------------------------------------------------
    for nombre, base, rug0, borde_col in (("acero_galv", "#A3A9AD", 0.42, "#C4C8CB"), ("acero_gastado", "#7D8185", 0.4,
                                                                                        "#C2C5C8"),
                                          ("acero_rueda", "#4E5256", 0.35, "#A9ADB0"), ("acero_mordaza", "#55595D", 0.45,
                                                                                         "#9DA1A4"),
                                          ("acero_herramienta", "#4A4D51", 0.4, "#B0B4B8")):
        t = nuevo(nombre)
        var = t.ruido(9.0, detalle=4)
        col = t.mezcla(t.rango(var, 0.3, 0.7), base, borde_col)
        if nombre == "acero_galv":
            col = t.mezcla(t.rango(t.voronoi(10.0, salida="Distance"), 0.0, 0.5), col, "#8E9498")
        col = t.mezcla(t.mul(t.borde(0.02), 0.6), col, borde_col)
        col = t.mezcla(t.mul(t.cavidad(0.08), 0.65), col, "#2E2A26")
        ox = t.mul(t.rango(t.ruido(5.0, detalle=5), 0.6, 0.75), 0.7)
        col = t.mezcla(ox, col, "#7A3F1F")
        t.terminar(col, t.lerp(ox, rug0, 0.85), t.lerp(ox, 1.0, 0.1), t.mul(t.ruido(40.0, detalle=3), 0.003),
                   bisel=0.008)

    t = nuevo("acero_zocalo")
    col, rug, met, alt = pintura_metal(t, "#34393E", debajo="#9EA3A6", z_oxido=(0.1, 1.2), desconchon=1.0,
                                       suciedad=0.6, chorretones=0.5, met_pintura=0.35)
    t.terminar(col, rug, met, alt, bisel=0.008)

    t = nuevo("acero_hollin")
    col = t.mezcla(t.rango(t.ruido(6.0, detalle=4), 0.3, 0.7), "#2A2826", "#3C3A37")
    col = t.mezcla(t.mul(t.borde(0.02), 0.5), col, "#6E7174")
    t.terminar(col, 0.75, 0.6, t.mul(t.ruido(25.0, detalle=3), 0.004), bisel=0.006)

    t = nuevo("cromo")
    col = t.mezcla(t.rango(t.ruido(12.0), 0.3, 0.7), "#BFC4C8", "#D5D9DC")
    sucio = t.mul(t.cavidad(0.05), 0.75)
    col = t.mezcla(sucio, col, "#3C3833")
    grasa = t.mul(t.rango(t.ruido(5.0, detalle=4), 0.55, 0.7), 0.6)
    col = t.mezcla(grasa, col, "#4A443C")
    t.terminar(col, t.lerp(t.maxi(sucio, grasa), 0.16, 0.6), t.lerp(grasa, 1.0, 0.4), bisel=0.006)

    t = nuevo("cadena")
    ox = t.rango(t.ruido(8.0, detalle=5), 0.55, 0.72)
    col = t.mezcla(t.rango(t.ruido(15.0), 0.3, 0.7), "#2F2E2C", "#45423F")
    col = t.mezcla(t.mul(t.borde(0.015), 0.7), col, "#8C8E90")  # roce de eslabón contra eslabón: brilla
    col = t.mezcla(t.mul(ox, 0.7), col, "#6E3A1E")
    t.terminar(col, t.lerp(ox, 0.35, 0.85), t.lerp(ox, 0.9, 0.2), t.mul(t.ruido(30.0, detalle=4), 0.004), bisel=0.008)

    t = nuevo("alambre")
    t.terminar("#55585B", 0.5, 0.9, bisel=0)
    t = nuevo("rejilla")
    t.terminar(t.mezcla(t.rango(t.ruido(6.0), 0.3, 0.7), "#1E1D1C", "#33312F"), 0.8, 0.5, bisel=0)

    # ---- pinturas de colores -------------------------------------------------------------------------------------
    def pintura(nombre, base, z_ox=(0.1, 0.9), desconchon=0.8, suciedad=0.45, chorretones=0.2, rug_p=0.45,
                arañazos=None, extra=None):
        t = nuevo(nombre)
        col, rug, met, alt = pintura_metal(t, base, debajo="#A2A6A9", z_oxido=z_ox, desconchon=desconchon,
                                           suciedad=suciedad, chorretones=chorretones, rug_pintura=rug_p,
                                           arañazos=arañazos)
        if extra:
            col, rug, met, alt = extra(t, col, rug, met, alt)
        t.terminar(col, rug, met, alt, bisel=0.01)

    pintura("pintura_roja_gastada", "#9E2B22", desconchon=1.0)
    pintura("pintura_azul_tornillo", "#2D4D78", desconchon=1.0, suciedad=0.6)
    pintura("metal_banco", "#3E4A45", z_ox=(0.1, 0.8), desconchon=0.9, suciedad=0.55)
    pintura("pintura_gris_cuadro", "#B9BCB6", z_ox=(1.9, 2.1), desconchon=0.35, suciedad=0.35, chorretones=0.3)
    pintura("placa_montaje", "#D7822F", z_ox=(1.9, 2.0), desconchon=0.1, suciedad=0.3, chorretones=0.0)
    pintura("pintura_amarilla_pluma", "#C9A227", z_ox=(4.6, 5.3), desconchon=1.0, suciedad=0.5, chorretones=0.45)
    pintura("pintura_soldadora", "#D99A22", z_ox=(0.0, 0.4), desconchon=0.8, suciedad=0.55, chorretones=0.2,
            rug_p=0.4)
    pintura("pintura_compresor", "#B03A22", z_ox=(0.0, 0.7), desconchon=0.8, suciedad=0.55, chorretones=0.3,
            rug_p=0.38)
    pintura("pintura_motor", "#2F3A34", z_ox=(0.0, 0.5), desconchon=0.6, suciedad=0.5)
    pintura("pintura_carretilla", "#A3291E", z_ox=(0.0, 0.8), desconchon=1.0, suciedad=0.6, rug_p=0.5)
    pintura("cartel_fondo", "#22303A", z_ox=(4.6, 4.9), desconchon=0.6, suciedad=0.4, chorretones=0.6)
    pintura("letras_taller", "#E27A28", z_ox=(4.7, 4.9), desconchon=0.7, suciedad=0.3, chorretones=0.3, rug_p=0.4)
    pintura("carcasa_foco", "#3A3E43", z_ox=(4.7, 5.0), desconchon=0.5, suciedad=0.5, chorretones=0.2)
    pintura("tubo_pintado", "#3E6B49", z_ox=(0.0, 1.2), desconchon=1.0, suciedad=0.6, chorretones=0.4)
    pintura("chapa_curva", "#8A3A26", z_ox=(0.0, 1.4), desconchon=1.0, suciedad=0.6, chorretones=0.5, rug_p=0.62)
    pintura("aceitera", "#8C2A1E", z_ox=(1.7, 1.8), desconchon=0.7, suciedad=0.6)

    def gancho_extra(t, col, rug, met, alt):
        x, y, z = t.xyz()
        roce = t.mul(t.mirando_arriba(0.2, 0.8), t.rango(t.ruido(6.0), 0.3, 0.6))
        return t.mezcla(roce, col, "#8D9093"), t.lerp(roce, rug, 0.3), t.lerp(roce, met, 0.95), alt
    pintura("gancho_amarillo", "#E0A71E", z_ox=(1.8, 2.4), desconchon=1.0, suciedad=0.4, extra=gancho_extra)

    def bidon(nombre, base, liquido):
        def extra(t, col, rug, met, alt):
            x, y, z = t.xyz()
            # Etiqueta pintada en una banda y chorretones de lo que guarda bajo la boca.
            # Etiqueta: banda estrecha entre los dos aros, solo en un lado del bidón (ruido grande).
            banda = t.mul(t.mul(t.rango(z, 0.82, 0.85), t.rango(z, 1.0, 0.97)),
                          t.rango(t.ruido(0.7, detalle=1), 0.45, 0.55))
            col = t.mezcla(t.mul(banda, 0.8), col, "#CFC8B4")
            chorro = t.mul(t.rango(z, 1.55, 0.6), t.rango(t.ruido(2.0, t.estirar((6.0, 6.0, 0.35)), detalle=3), 0.6, 0.72))
            col = t.mezcla(t.mul(chorro, 0.85), col, liquido)
            rug = t.lerp(chorro, rug, 0.18)
            golpe = t.rango(t.voronoi(3.0, salida="Distance"), 0.25, 0.05)
            return col, rug, met, t.suma(alt, t.mul(golpe, -0.02))
        pintura(nombre, base, z_ox=(0.0, 0.5), desconchon=0.9, suciedad=0.5, chorretones=0.3, rug_p=0.42, extra=extra)

    bidon("bidon_azul", "#24508E", "#1E1A12")
    bidon("bidon_rojo", "#A6261D", "#4A3A1A")
    bidon("bidon_verde", "#2E7A3B", "#5FC0A0")

    def seguridad_extra(t, col, rug, met, alt):
        x, y, z = t.xyz()
        rayas = t.ola(2.6, t.vop("ADD", t.pos(), (0, 0, 0)), direccion="DIAGONAL", perfil="SAW")
        negro = t.rango(rayas, 0.49, 0.51)
        return t.mezcla(t.mul(negro, 0.92), col, "#171717"), rug, met, alt
    pintura("seguridad", "#E5B522", z_ox=(0.0, 0.5), desconchon=1.0, suciedad=0.6, extra=seguridad_extra)

    # ---- banco, panel y herramientas -------------------------------------------------------------------------------
    t = nuevo("banco_tapa")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(3.0, detalle=4), 0.3, 0.7), "#5E6266", "#6E7276")
    rayas = t.op("MAXIMUM", t.rango(t.ruido(3.0, t.estirar((40.0, 2.0, 1.0)), detalle=1), 0.66, 0.7),
                 t.rango(t.ruido(3.0, t.estirar((2.0, 35.0, 1.0)), detalle=1), 0.68, 0.71))
    col = t.mezcla(t.mul(rayas, 0.7), col, "#B8BCBF")
    golpes = t.rango(t.voronoi(14.0, salida="Distance"), 0.08, 0.02)
    col = t.mezcla(t.mul(golpes, 0.5), col, "#3E4144")
    quemado = t.mul(t.rango(t.voronoi(1.5, salida="Distance"), 0.22, 0.08), t.rango(t.ruido(4.0), 0.4, 0.6))
    col = t.mezcla(quemado, col, t.mezcla(t.ruido(9.0), "#2A2522", "#4A3A5A"))
    cercos = t.rango(t.op("ABSOLUTE", t.resta(t.voronoi(2.2, salida="Distance"), 0.12)), 0.012, 0.0)
    col = t.mezcla(t.mul(cercos, 0.7), col, "#2A241E")
    tiza = t.mul(t.rango(t.ruido(1.0, t.estirar((1.0, 8.0, 1.0)), detalle=1), 0.69, 0.7), 0.7)
    col = t.mezcla(tiza, col, "#D8D4C8")
    col = t.mezcla(t.mul(t.borde(0.02), 0.6), col, "#A9ADB0")
    t.terminar(col, t.lerp(rayas, t.lerp(quemado, 0.5, 0.7), 0.3), t.lerp(quemado, 0.75, 0.3),
               t.suma(t.mul(golpes, -0.01), t.mul(rayas, -0.002)), bisel=0.01)

    t = nuevo("pegboard")
    x, y, z = t.xyz()
    paso = 0.1
    fx = t.op("ABSOLUTE", t.resta(t.op("FRACT", t.op("DIVIDE", x, paso)), 0.5))
    fz = t.op("ABSOLUTE", t.resta(t.op("FRACT", t.op("DIVIDE", z, paso)), 0.5))
    dist = t.op("SQRT", t.suma(t.mul(fx, fx), t.mul(fz, fz)))
    agujero = t.rango(dist, 0.2, 0.15)
    col = t.mezcla(t.rango(t.ruido(2.0, detalle=3), 0.3, 0.7), "#A4AA9F", "#959B90")
    col = t.mezcla(t.mul(t.lejos_de((sum(P["panel_x"]) / 2, -4.7, 2.95), 0.4, 1.8), 0.25), col, "#6E6E60")
    col = t.mezcla(agujero, col, "#121212")
    col = t.mezcla(t.mul(t.borde(0.02), 0.5), col, "#C9CCC5")
    col = t.mezcla(t.mul(t.rango(t.ruido(5.0, detalle=4), 0.55, 0.7), 0.6), col, "#3A3630")  # dedos grasientos
    t.terminar(col, t.lerp(agujero, 0.55, 0.95), t.lerp(agujero, 0.3, 0.0), t.mul(agujero, -0.02), bisel=0.008)

    t = nuevo("silueta")
    col = t.mezcla(t.rango(t.ruido(10.0, detalle=4), 0.6, 0.72), "#E9E4D2", "#B9B4A2")
    t.terminar(col, 0.6, 0.0, bisel=0)

    for nombre, base in (("mango_amarillo", "#E0B021"), ("mango_rojo", "#B12A22")):
        t = nuevo(nombre)
        col = t.mezcla(t.mul(t.cavidad(0.04), 0.7), base, "#2A2420")
        col = t.mezcla(t.mul(t.rango(t.ruido(6.0, detalle=4), 0.5, 0.7), 0.5), col, "#3A322A")
        t.terminar(col, 0.45, 0.0, t.mul(t.ruido(50.0), 0.002), bisel=0.008)

    # ---- electricidad, señales y rótulos ------------------------------------------------------------------------------
    for nombre, base, rug0 in (("plastico_blanco", "#E5E3DA", 0.45), ("plastico_negro", "#1D1E20", 0.5),
                               ("plastico_rojo", "#B5261E", 0.4), ("cable_rojo", "#A3221A", 0.5),
                               ("cable_azul", "#1F4F9A", 0.5), ("cable_negro", "#1A1A1A", 0.5),
                               ("cable_amarillo", "#C9B21E", 0.5), ("cable_rojo_soldadura", "#8A1F18", 0.6),
                               ("pintura_negra", "#131313", 0.6), ("grabado", "#1B1B1B", 0.7),
                               ("vidrio_oscuro", "#0C1A12", 0.08), ("goma_rueda", "#1B1B1C", 0.85),
                               ("ceramica", "#6B3A22", 0.15), ("plomo", "#7A7D80", 0.5),
                               ("esfera_manometro", "#ECE9DF", 0.3)):
        t = nuevo(nombre)
        col = t.mezcla(t.mul(t.cavidad(0.05), 0.5), base, "#2A2622")
        t.terminar(col, rug0, 0.0, bisel=0.004)

    t = nuevo("senal_amarilla")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(3.0, detalle=3), 0.3, 0.7), "#EDBE1C", "#D9AC18")
    col = t.mezcla(t.mul(t.rango(t.ruido(1.5, t.estirar((5, 5, 0.4)), detalle=3), 0.55, 0.75), 0.5), col, "#8A7A4A")
    t.terminar(col, 0.45, 0.1, bisel=0.004)

    t = nuevo("placa_horario")
    x, y, z = t.xyz()
    cepillado = t.ruido(2.0, t.estirar((1.0, 40.0, 1.0)), detalle=2)
    col = t.mezcla(t.rango(cepillado, 0.3, 0.7), "#A2A6A9", "#BABEC1")
    col = t.mezcla(t.mul(t.cavidad(0.03), 0.6), col, "#3A3632")
    col = t.mezcla(t.mul(t.rango(t.ruido(4.0, detalle=4), 0.55, 0.7), 0.5), col, "#6E5A40")
    t.terminar(col, t.rango(cepillado, 0.3, 0.7, 0.28, 0.4), 1.0, t.mul(cepillado, 0.002), bisel=0.006)

    t = nuevo("conducto")
    t.terminar(t.mezcla(t.mul(t.rango(t.ruido(4.0, detalle=4), 0.45, 0.7), 0.6), "#8E908D", "#5A5A52"), 0.6, 0.0,
               bisel=0.004)

    # ---- soldadora, compresor ---------------------------------------------------------------------------------------
    t = nuevo("cobre")
    t.terminar(t.mezcla(t.mul(t.cavidad(0.04), 0.8), "#B87333", "#3E5A40"), 0.35, 1.0, bisel=0.004)
    t = nuevo("mascara")
    col = t.mezcla(t.rango(t.ruido(5.0, detalle=3), 0.3, 0.7), "#2C3230", "#363C38")
    col = t.mezcla(t.mul(t.rango(t.voronoi(30.0, salida="Distance"), 0.06, 0.02), 0.6), col, "#8A8D90")  # chispas
    t.terminar(col, 0.55, 0.0, bisel=0.006)
    t = nuevo("aluminio_fundido")
    col = t.mezcla(t.rango(t.ruido(14.0, detalle=5), 0.3, 0.7), "#8E918E", "#A4A7A3")
    col = t.mezcla(t.mul(t.cavidad(0.06), 0.7), col, "#2E2A26")
    t.terminar(col, 0.62, 0.9, t.mul(t.ruido(40.0, detalle=4), 0.004), bisel=0.008)
    t = nuevo("manguera")
    col = t.mezcla(t.rango(t.ruido(4.0, detalle=3), 0.3, 0.7), "#2F6EB2", "#295E99")
    col = t.mezcla(t.mul(t.rango(t.ruido(5.0, detalle=4), 0.5, 0.7), 0.6), col, "#2B2A28")
    t.terminar(col, 0.5, 0.0, bisel=0)
    t = nuevo("embudo")
    col = t.mezcla(t.rango(t.voronoi(8.0, salida="Distance"), 0.0, 0.5), "#8E9498", "#A9AFB3")
    col = t.mezcla(t.mul(t.cavidad(0.05), 0.7), col, "#2A2420")
    t.terminar(col, 0.4, 0.9, t.mul(t.rango(t.voronoi(4.0, salida="Distance"), 0.3, 0.05), -0.01), bisel=0.004)
    t = nuevo("trapo")
    col = t.mezcla(t.rango(t.ruido(6.0, detalle=4), 0.3, 0.7), "#8E7E66", "#6E604C")
    col = t.mezcla(t.mul(t.rango(t.ruido(3.0, detalle=4), 0.5, 0.65), 0.8), col, "#2A241C")
    t.terminar(col, 0.9, 0.0, t.mul(t.ruido(30.0, detalle=4), 0.006), bisel=0)

    # ---- piezas viejas -------------------------------------------------------------------------------------------------
    t = nuevo("tubo_oxidado")
    ox = t.ruido(4.0, detalle=6, rug=0.65)
    col = t.mezcla(t.rango(ox, 0.3, 0.7), "#5E3A24", "#8E5530")
    col = t.mezcla(t.mul(t.rango(t.ruido(9.0, detalle=4), 0.55, 0.7), 0.6), col, "#3E2A1C")
    col = t.mezcla(t.mul(t.cavidad(0.08), 0.6), col, "#24180F")
    t.terminar(col, 0.88, 0.2, t.mul(ox, 0.012), bisel=0.008)
    t = nuevo("turbina")
    x, y, z = t.xyz()
    tinte = t.ruido(3.0, detalle=3)
    col = t.mezcla(t.rango(tinte, 0.3, 0.55), "#7E8184", "#6E5A3E")
    col = t.mezcla(t.rango(tinte, 0.55, 0.75), col, "#3E3A5A")
    col = t.mezcla(t.mul(t.rango(t.ruido(5.0, detalle=5), 0.45, 0.7), 0.85), col, "#141210")  # quemado
    col = t.mezcla(t.mul(t.borde(0.02), 0.5), col, "#B5B8BB")
    t.terminar(col, 0.55, 0.85, t.mul(t.ruido(30.0, detalle=4), 0.005), bisel=0.006)
    t = nuevo("turbina_cubo")
    t.terminar(t.mezcla(t.rango(t.ruido(6.0), 0.3, 0.7), "#2E2C2A", "#4A4642"), 0.6, 0.8, bisel=0.006)
    t = nuevo("madera_traviesa")
    veta = t.ruido(3.0, t.estirar((14.0, 0.5, 14.0)), detalle=5)
    col = t.mezcla(t.rango(veta, 0.3, 0.8), "#3E2E20", "#5A4532")
    col = t.mezcla(t.mul(t.rango(t.ruido(4.0, detalle=4), 0.55, 0.7), 0.6), col, "#1E1610")  # creosota
    t.terminar(col, 0.85, 0.0, t.mul(veta, 0.008), bisel=0.01)
    t = nuevo("carton")
    col = t.mezcla(t.rango(t.ruido(3.0, detalle=3), 0.3, 0.7), "#A88456", "#8E6E46")
    t.terminar(t.mezcla(t.mul(t.cavidad(0.05), 0.6), col, "#3A2A1A"), 0.9, 0.0, bisel=0.004)

    # ---- rampa de chapa estriada -------------------------------------------------------------------------------------
    t = nuevo("rampa_diamante")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(3.0, detalle=4), 0.3, 0.7), "#6C7074", "#7E8286")
    cav = t.cavidad(0.03, 0.75, 1.0)
    col = t.mezcla(t.mul(cav, 0.8), col, "#2E2A25")  # tierra entre los diamantes
    gastado = t.mul(t.mirando_arriba(0.9, 0.99), t.lejos_de(P["porton_suelo"], 0.4, 2.2))
    alto = t.rango(z, 0.09, 0.16)
    col = t.mezcla(t.mul(t.mul(alto, gastado), 0.7), col, "#B5B9BC")  # crestas pulidas por las ruedas
    ox = t.mul(t.rango(t.ruido(4.0, detalle=5), 0.6, 0.75), 0.75)
    col = t.mezcla(ox, col, "#7A4022")
    aceite = t.mul(t.rango(t.voronoi(2.0, salida="Distance"), 0.25, 0.1), 0.7)
    col = t.mezcla(aceite, col, "#2A241D")
    t.terminar(col, t.lerp(aceite, t.lerp(ox, 0.42, 0.85), 0.25), t.lerp(ox, 0.9, 0.1),
               t.mul(t.ruido(40.0, detalle=3), 0.002), bisel=0.006)

    t = nuevo("neon_calido")
    t.terminar("#FFB45A", 0.3, 0.0, emi="#FFB45A", bisel=0)
    return mats


def _ruido_color(t, escala):
    n = t.nodo("ShaderNodeTexNoise", noise_dimensions="3D", noise_type="FBM", normalize=True)
    t.poner(n.inputs["Vector"], t.pos())
    n.inputs["Scale"].default_value = escala
    n.inputs["Detail"].default_value = 2.0
    return n.outputs["Color"]
