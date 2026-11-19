"""
Materiales de la casa del granjero. Parte de los de la casa del minero (casa_materiales) y añade los suyos.

La historia que cuentan:
  * paneles blancos y grises como los del pueblo, pero con salpicaduras de barro y cercos de cal abajo (se riega
    todo el día) y verdín en el muro que da al invernadero (la humedad sale por el pasillo),
  * la puerta de madera tiene más verdín y la madera más hinchada y oscura abajo que la del minero,
  * el cristal del invernadero es verde muy tenue, con gotas de condensación y vaho en la parte de abajo
    (el alfa va horneado en el PNG de color: SurfaceAppearance con AlphaMode = Transparency),
  * los perfiles de aluminio tienen cal blanca en las uniones y algo de verde en el pie,
  * la mesa de trabajo, la carretilla y las botas están manchadas de tierra; el compost es oscuro y húmedo.

Los puntos que usan las máscaras (manija, grifos, pie del bajante...) vienen en `P` desde granjero_piezas.
"""

import bpy

import casa_materiales as cm
from casa_materiales import Arbol, pintura_metal


def _salpicaduras(t, col, rug, z_suelo, alto=1.0, fuerza=1.0):
    """Barro salpicado desde el suelo y cercos de cal del agua de riego (más densos cuanto más abajo)."""
    x, y, z = t.xyz()
    abajo = t.rango(z, z_suelo + alto, z_suelo, suave=True)
    gotas = t.rango(t.voronoi(14.0, rasgo="F1", salida="Distance", aleatorio=1.0), 0.16, 0.08)
    gotas = t.mul(gotas, t.rango(t.ruido(3.0, detalle=3), 0.35, 0.7))
    manchas = t.rango(t.ruido(7.0, detalle=5, rug=0.65), 0.45, 0.62)
    barro = t.op("MINIMUM", t.mul(abajo, t.maxi(t.mul(manchas, 0.75), gotas)), 1.0)
    col = t.mezcla(t.mul(barro, 0.85 * fuerza), col, "#5C4A35")
    # Cercos de cal: anillos claros donde se secaron las gotas.
    cerco = t.rango(t.voronoi(5.0, rasgo="F1", salida="Distance"), 0.33, 0.36)
    cerco = t.mul(t.mul(cerco, t.rango(z, z_suelo + alto * 1.4, z_suelo + 0.1)), t.rango(t.ruido(2.0), 0.45, 0.7))
    col = t.mezcla(t.mul(cerco, 0.45 * fuerza), col, "#D9D6C8")
    rug = t.lerp(t.mul(barro, fuerza), rug, 0.92)
    return col, rug, barro


def _verdin(t, col, intensidad, escala=4.0):
    """Algas verdes en manchas (humedad)."""
    mancha = t.rango(t.ruido(escala, detalle=5, rug=0.62), 0.47, 0.66)
    tono = t.mezcla(t.ruido(escala * 3.0), "#4F6232", "#6E7F3C")
    return t.mezcla(t.mul(mancha, intensidad), col, tono), mancha


def crear_materiales(P):
    mats = cm.crear_materiales(P)

    def nuevo(nombre):
        m = bpy.data.materials.new(nombre)
        m.use_nodes = True
        mats[nombre] = m
        return Arbol(m)

    zz = P["zocalo_z"]

    # ---- paredes ----------------------------------------------------------------------------------------------
    t = nuevo("panel_granjero")
    col, rug, met, alt = pintura_metal(
        t, "#D9DCD5", variar_isla=[(0.4, "#CBD0CF"), (0.7, "#E0DFD3"), (0.9, "#C3C9C6")],
        z_oxido=(zz, zz + 0.9), desconchon=0.45, suciedad=0.35, chorretones=0.3)
    col, rug, barro = _salpicaduras(t, col, rug, zz - 0.05, alto=1.1)
    x, y, z = t.xyz()
    # Verdín: el muro que da al invernadero (x negativo) y lo bajo de todos.
    humedo = t.maxi(t.mul(t.rango(x, -3.0, -5.2), t.rango(z, 4.2, zz)), t.mul(t.rango(z, zz + 0.9, zz), 0.55))
    musgo = t.mul(t.rango(t.ruido(4.0, detalle=5, rug=0.62), 0.48, 0.66), humedo)
    col = t.mezcla(t.mul(musgo, 0.75), col, "#5E7038")
    # Churretes de cal bajo el grifo y el medidor de agua.
    for punto in (P["grifo_pared"], P["medidor_agua"]):
        px, py, pz = punto
        cerca = t.lejos_de((px, py, pz - 0.6), 0.1, 0.75)
        rayas = t.rango(t.ruido(2.0, t.estirar((14, 14, 0.6)), detalle=2), 0.5, 0.65)
        col = t.mezcla(t.mul(t.mul(cerca, rayas), t.rango(z, pz + 0.1, pz - 0.2)), col, "#C9C7B8")
    t.terminar(col, t.lerp(musgo, rug, 0.85), met, alt, bisel=0.02)

    # ---- madera de la puerta: como la del minero, con más humedad y verdín ----------------------------------
    t = nuevo("madera_humeda")
    x, y, z = t.xyz()
    isla = t.isla()
    tono = t.mezcla(t.rango(isla, 0.0, 1.0), "#6E4A2E", "#80603F")
    veta = t.ola(5.0, t.estirar((1.0, 1.0, 0.12)), direccion="X", dist=6.0, detalle=3.0)
    veta2 = t.ruido(3.0, t.estirar((12, 12, 0.6)), detalle=5)
    vetas = t.rango(t.suma(t.mul(veta, 0.6), t.mul(veta2, 0.5)), 0.3, 1.0)
    col = t.mezcla(t.mul(vetas, 0.55), tono, "#45301F")
    nudo = t.rango(t.voronoi(1.6, t.estirar((1, 1, 0.5)), salida="Distance"), 0.06, 0.02)
    col = t.mezcla(t.mul(nudo, 0.8), col, "#33200F")
    # Madera empapada abajo: oscura, gris, con verdín que sube por las vetas.
    humeda = t.rango(z, P["puerta_z0"] + 1.9, P["puerta_z0"] + 0.05, suave=True)
    col = t.mezcla(t.mul(humeda, 0.6), col, "#4A4236")
    verde = t.mul(humeda, t.rango(t.suma(t.ruido(5.0, detalle=5), t.mul(vetas, 0.35)), 0.5, 0.75))
    col = t.mezcla(t.mul(verde, 0.85), col, "#566B33")
    # Canto de las bisagras (el lado del invernadero) más verde: le llega el vaho.
    lado = t.mul(t.lejos_de(P["bisagras_puerta"], 0.2, 1.4), t.rango(t.ruido(6.0, detalle=4), 0.45, 0.7))
    col = t.mezcla(t.mul(lado, 0.6), col, "#5F7438")
    mano = t.lejos_de(P["manija"], 0.15, 0.75)
    col = t.mezcla(t.mul(mano, 0.5), col, "#9A7650")
    grasa = t.lejos_de(P["manija"], 0.05, 0.3)
    col = t.mezcla(t.mul(grasa, 0.45), col, "#3A281A")
    cav = t.cavidad(0.08)
    col = t.mezcla(t.mul(cav, 0.65), col, "#1F1A10")
    rug = t.lerp(mano, t.lerp(humeda, 0.7, 0.88), 0.45)
    alt = t.suma(t.mul(vetas, 0.005), t.mul(t.ruido(60.0, t.estirar((1, 1, 0.08)), detalle=2), 0.002))
    alt = t.suma(alt, t.mul(verde, 0.003))
    t.terminar(col, rug, 0.0, alt, bisel=0.012)

    # ---- invernadero ------------------------------------------------------------------------------------------
    t = nuevo("aluminio_perfil")
    x, y, z = t.xyz()
    spots = t.rango(t.ruido(10.0, detalle=4), 0.55, 0.75)
    col = t.mezcla(spots, "#B7BDC0", "#CDD1D0")
    cav = t.cavidad(0.07)
    cal = t.mul(cav, t.rango(t.ruido(12.0, detalle=4), 0.35, 0.6))
    col = t.mezcla(t.mul(cal, 0.8), col, "#E4E2D8")   # cal blanca en las uniones
    col = t.mezcla(t.mul(cav, 0.35), col, "#56544C")
    pie = t.mul(t.rango(z, 1.2, 0.5), t.rango(t.ruido(6.0, detalle=4), 0.4, 0.7))
    col = t.mezcla(t.mul(pie, 0.7), col, "#64703F")    # verde en el pie
    t.terminar(col, t.lerp(spots, 0.32, 0.55), t.lerp(pie, t.lerp(spots, 0.95, 0.6), 0.2),
               t.mul(t.ruido(70.0, detalle=2), 0.0015), bisel=0.008)

    t = nuevo("vidrio_invernadero")
    x, y, z = t.xyz()
    # Gotas: celdas de Voronoi; la gota es el centro de la celda, de tamaño variable.
    vor = t.nodo("ShaderNodeTexVoronoi", voronoi_dimensions="3D", feature="F1")
    t.poner(vor.inputs["Vector"], t.estirar((1, 1, 0.8)))
    vor.inputs["Scale"].default_value = 9.0
    tam_gota = t.rango(t.ruido(1.5, detalle=2), 0.3, 0.7, 0.02, 0.06)
    # Borde suave (no un corte duro): al hornear no salen gotas cuadradas.
    gota = t.rango(t.resta(vor.outputs["Distance"], tam_gota), 0.03, -0.02, suave=True)
    finas = t.rango(t.voronoi(22.0, salida="Distance"), 0.11, 0.05)
    # Regueros: gotas que han resbalado (rayas verticales).
    reguero = t.mul(t.rango(t.ruido(1.0, t.estirar((26, 26, 0.7)), detalle=1), 0.68, 0.74),
                    t.rango(t.ruido(1.3, detalle=2), 0.5, 0.65))
    # Vaho: más en la parte baja de cada paño y en manchas.
    vaho = t.mul(t.rango(z, 2.6, 0.6, 0.25, 1.0), t.rango(t.ruido(1.2, detalle=3), 0.3, 0.75, 0.3, 1.0))
    vaho = t.op("MINIMUM", t.suma(vaho, t.mul(finas, 0.6)), 1.0)
    agua = t.op("MINIMUM", t.suma(gota, t.mul(reguero, 0.8)), 1.0)
    col = t.mezcla(t.mul(vaho, 0.55), "#86D49A", "#D8EEDC")
    col = t.mezcla(t.mul(agua, 0.7), col, "#EAF6EE")
    # Polvo y verdín en el borde de abajo, por fuera.
    pie = t.mul(t.rango(z, 0.95, 0.55), t.rango(t.ruido(8.0, detalle=4), 0.35, 0.65))
    col = t.mezcla(t.mul(pie, 0.7), col, "#7A7F55")
    # Opacidad: base del 30 % (se lee el verde del cristal aunque dentro esté en sombra) + vaho y gotas.
    alfa = t.suma(0.3, t.suma(t.mul(vaho, 0.28), t.suma(t.mul(agua, 0.25), t.mul(pie, 0.45))))
    alfa = t.op("MINIMUM", alfa, 0.92)
    alt = t.suma(t.mul(gota, 0.004), t.mul(reguero, 0.0015))
    t.terminar(col, t.lerp(agua, t.lerp(vaho, 0.06, 0.3), 0.02), 0.0, alt, bisel=0, alfa=alfa)

    t = nuevo("grava")
    piedras = t.voronoi(30.0, salida="Distance")
    col = t.mezcla(t.rango(t.voronoi(30.0, salida="Color"), 0.3, 0.7), "#8C8478", "#A8A194")
    col = t.mezcla(t.rango(piedras, 0.25, 0.05), "#4A4238", col)
    col = t.mezcla(t.mul(t.rango(t.ruido(3.0), 0.5, 0.7), 0.6), col, "#5C5240")  # mojada
    t.terminar(col, 0.85, 0.0, t.mul(t.rango(piedras, 0.3, 0.0), 0.012), bisel=0)

    t = nuevo("sustrato")
    grumos = t.voronoi(55.0, salida="Distance")
    col = t.mezcla(t.rango(t.ruido(12.0, detalle=5), 0.3, 0.7), "#2E2017", "#3D2B1D")
    perlita = t.rango(t.voronoi(40.0, salida="Distance", aleatorio=1.0), 0.06, 0.03)
    col = t.mezcla(t.mul(perlita, 0.85), col, "#D8D4C6")   # bolitas de perlita
    t.terminar(col, t.lerp(perlita, 0.7, 0.9), 0.0, t.mul(t.rango(grumos, 0.3, 0.0), 0.006), bisel=0)

    def hoja(nombre, claro, oscuro, venas="#C9E39A", brillo=0.45, seco=0.0):
        t = nuevo(nombre)
        isla = t.isla()
        col = t.mezcla(t.rango(isla, 0.0, 1.0), oscuro, claro)
        nervios = t.rango(t.ruido(6.0, t.estirar((1, 1, 1)), detalle=1, tipo="RIDGED_MULTIFRACTAL"), 0.88, 0.97)
        col = t.mezcla(t.mul(nervios, 0.35), col, venas)
        if seco:
            col = t.mezcla(t.mul(t.rango(t.ruido(18.0), 0.62, 0.72), seco), col, "#9A8A44")
        col = t.mezcla(t.mul(t.cavidad(0.06), 0.7), col, "#16240F")
        t.terminar(col, brillo, 0.0, t.suma(t.mul(nervios, 0.0025), t.mul(t.ruido(50.0), 0.0015)), bisel=0)

    hoja("hoja_lechuga", "#9CCB5A", "#5E9A35", venas="#E2F2B5", brillo=0.5)
    hoja("hoja_albahaca", "#4F8F35", "#2F6A24", venas="#86B866", brillo=0.35)
    hoja("hoja_tomate", "#5D8E3A", "#3B6828", venas="#9BC07A", brillo=0.6, seco=0.3)
    hoja("hoja_enredadera", "#5C8C34", "#2F5A22", venas="#A7C77A", brillo=0.42, seco=0.25)
    hoja("hoja_romero", "#6F8A5A", "#4E6B44", venas="#9DB28A", brillo=0.7)

    t = nuevo("tomate")
    isla = t.isla()
    col = t.mezcla(t.rango(isla, 0.0, 1.0), "#B8261C", "#E0452A")
    col = t.mezcla(t.rango(isla, 0.82, 0.85), col, "#E89A2E")   # alguno aún verdea
    col = t.mezcla(t.rango(isla, 0.93, 0.95), col, "#7BA33A")
    col = t.mezcla(t.mul(t.mirando_arriba(0.6, 0.95), 0.25), col, "#F07A55")
    t.terminar(col, 0.22, 0.0, t.mul(t.ruido(40.0), 0.0015), bisel=0)

    t = nuevo("flor")
    isla = t.isla()
    col = t.mezcla(t.rango(isla, 0.0, 1.0), "#8E5BC8", "#B98AE0")   # lavanda
    t.terminar(col, 0.6, 0.0, bisel=0)

    t = nuevo("tallo")
    veta = t.ruido(4.0, t.estirar((10, 10, 0.6)), detalle=4)
    col = t.mezcla(t.rango(veta, 0.3, 0.8), "#5D4A2C", "#6F7A3A")
    t.terminar(col, 0.75, 0.0, t.mul(veta, 0.002), bisel=0)

    t = nuevo("cuerda")
    hilos = t.ola(60.0, t.estirar((1, 1, 1)), direccion="Z", dist=2.0)
    t.terminar(t.mezcla(t.mul(hilos, 0.4), "#B9A47A", "#8C7A55"), 0.9, 0.0, t.mul(hilos, 0.002), bisel=0)

    # ---- plásticos y goma ----------------------------------------------------------------------------------------
    t = nuevo("plastico_tanque")
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(2.0, detalle=3), 0.3, 0.7), "#7E8A8C", "#8D989A")
    # Línea de agua por dentro (se transparenta el nivel) y verdín que sube desde el pie.
    nivel = t.rango(z, P["tanque_nivel"] + 0.04, P["tanque_nivel"] - 0.06)
    col = t.mezcla(t.mul(nivel, 0.18), col, "#3E4E4C")
    col, rug, _ = _salpicaduras(t, col, 0.55, P["tanque_pie"], alto=0.6, fuerza=0.8)
    col, mus = _verdin(t, col, 0.55)
    col = t.mezcla(t.mul(t.rango(z, P["tanque_pie"] + 0.5, P["tanque_pie"]), t.mul(mus, 0.7)), col, "#4D5E30")
    col = t.mezcla(t.mul(t.cavidad(0.08), 0.55), col, "#2F3333")
    sol = t.mirando_arriba(0.7, 0.95)
    col = t.mezcla(t.mul(sol, 0.3), col, "#B3BCBC")   # tapa descolorida por el sol
    t.terminar(col, rug, 0.0, t.mul(t.ruido(30.0, detalle=3), 0.002), bisel=0.02)

    t = nuevo("plastico_negro")   # bandejas de cultivo, macetas de vivero
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(6.0), 0.3, 0.7), "#1E2120", "#2A2D2B")
    tierra = t.mul(t.cavidad(0.1), t.rango(t.ruido(9.0, detalle=4), 0.3, 0.6))
    col = t.mezcla(t.mul(tierra, 0.8), col, "#4A3A2A")
    cal = t.mul(t.borde(0.02), t.rango(t.ruido(14.0, detalle=3), 0.5, 0.7))
    col = t.mezcla(t.mul(cal, 0.6), col, "#9A9A90")   # cal en los cantos
    t.terminar(col, 0.55, 0.0, bisel=0.01)

    t = nuevo("manguera")
    x, y, z = t.xyz()
    franja = t.rango(t.ola(9.0, direccion="Z", perfil="SIN"), 0.92, 0.97)
    col = t.mezcla(t.rango(t.ruido(5.0), 0.3, 0.7), "#2E8A3A", "#36A043")
    col = t.mezcla(t.mul(franja, 0.6), col, "#E0C33A")   # franja amarilla de la manguera
    col = t.mezcla(t.mul(t.cavidad(0.05), 0.6), col, "#173F1D")
    barro = t.mul(t.rango(z, 0.6, 0.2), t.rango(t.ruido(8.0, detalle=4), 0.35, 0.65))
    col = t.mezcla(barro, col, "#5A4A35")
    t.terminar(col, 0.38, 0.0, bisel=0.004)

    t = nuevo("goma_verde")   # botas de agua: verde oscuro, barro hasta media caña
    x, y, z = t.xyz()
    col = t.mezcla(t.rango(t.ruido(4.0), 0.3, 0.7), "#2C4A2A", "#355932")
    barro = t.mul(t.rango(z, P["botas_barro"], 0.5), t.rango(t.ruido(6.0, detalle=5, rug=0.65), 0.3, 0.6, 0.45, 1.0))
    salpic = t.mul(t.rango(t.voronoi(18.0, salida="Distance"), 0.14, 0.07), t.rango(z, 1.0, 0.5))
    barro = t.op("MINIMUM", t.suma(barro, salpic), 1.0)
    tono = t.mezcla(t.ruido(10.0), "#4E3C28", "#6A553A")
    col = t.mezcla(barro, col, tono)
    seco = t.mul(barro, t.rango(t.ruido(12.0, detalle=3), 0.5, 0.7))
    col = t.mezcla(t.mul(seco, 0.6), col, "#8E7A5C")   # barro seco, más claro y polvoriento
    col = t.mezcla(t.mul(t.cavidad(0.05), 0.6), col, "#121A10")
    t.terminar(col, t.lerp(barro, 0.3, 0.92), 0.0, t.mul(t.mul(barro, t.ruido(30.0, detalle=4)), 0.006),
               bisel=0.01)

    t = nuevo("saco")
    x, y, z = t.xyz()
    tej1 = t.ola(45.0, direccion="X", perfil="SIN")
    tej2 = t.ola(45.0, direccion="Z", perfil="SIN")
    tejido = t.mul(t.suma(tej1, tej2), 0.5)
    col = t.mezcla(t.rango(tejido, 0.2, 1.0), "#B9AE8C", "#D4C9A6")
    franja = t.rango(t.op("ABSOLUTE", t.resta(t.op("FRACT", t.mul(z, 1.6)), 0.5)), 0.06, 0.04)
    col = t.mezcla(t.mul(franja, 0.7), col, "#3E7A3A")   # franja verde impresa
    col = t.mezcla(t.mul(t.cavidad(0.08), 0.65), col, "#4A3E2A")
    tierra = t.mul(t.rango(z, 0.9, 0.5), t.rango(t.ruido(6.0, detalle=4), 0.35, 0.65))
    col = t.mezcla(t.mul(tierra, 0.8), col, "#5A4632")
    t.terminar(col, 0.92, 0.0, t.mul(tejido, 0.0025), bisel=0)

    # ---- madera de exterior -----------------------------------------------------------------------------------
    def madera_vieja(nombre, claro, oscuro, tierra_z, manchas=0.6, verdin=0.0, bisel=0.012):
        t = nuevo(nombre)
        x, y, z = t.xyz()
        isla = t.isla()
        tono = t.mezcla(t.rango(isla, 0.0, 1.0), oscuro, claro)
        veta = t.ruido(3.0, t.estirar((12, 12, 0.6)), detalle=5)
        veta_b = t.ruido(3.0, t.estirar((0.6, 12, 12)), detalle=5)
        vetas = t.rango(t.mezcla(t.rango(isla, 0.45, 0.55), veta, veta_b), 0.3, 0.85)
        col = t.mezcla(t.mul(vetas, 0.5), tono, "#4A3A2A")
        gris = t.rango(t.ruido(1.5, detalle=3), 0.4, 0.7)
        col = t.mezcla(t.mul(gris, 0.4), col, "#8C877C")   # madera agrisada por el sol
        sucio = t.mul(t.rango(t.ruido(5.0, detalle=5, rug=0.65), 0.45, 0.65), manchas)
        col = t.mezcla(sucio, col, "#4C3B2A")              # manchas de tierra
        col = t.mezcla(t.mul(t.rango(z, tierra_z + 0.5, tierra_z), 0.6), col, "#5A4A38")
        if verdin:
            col, _ = _verdin(t, col, verdin)
        col = t.mezcla(t.mul(t.cavidad(0.07), 0.6), col, "#241A10")
        col = t.mezcla(t.mul(t.borde(0.03), 0.3), col, "#B4A68C")
        t.terminar(col, t.lerp(sucio, 0.82, 0.92), 0.0, t.suma(t.mul(vetas, 0.004), t.mul(sucio, 0.002)),
                   bisel=bisel)

    madera_vieja("madera_rustica", "#9A7A55", "#7A5A3A", 0.0, manchas=0.75)
    madera_vieja("madera_compost", "#8A7458", "#6A5640", 0.0, manchas=0.5, verdin=0.6)
    madera_vieja("madera_bancal", "#8E6E4A", "#6E5034", 0.5, manchas=0.6, verdin=0.3)

    t = nuevo("compost")
    x, y, z = t.xyz()
    trozos = t.voronoi(18.0, salida="Color")
    col = t.mezcla(t.rango(t.ruido(10.0, detalle=5), 0.3, 0.7), "#1E160E", "#33261A")
    restos = t.rango(t.voronoi(12.0, salida="Distance"), 0.08, 0.02)
    col = t.mezcla(t.mul(restos, 0.8), col, t.mezcla(trozos, "#6B5A2E", "#7C8A3A"))  # pieles y hojas
    col = t.mezcla(t.mul(t.rango(t.voronoi(25.0, salida="Distance"), 0.05, 0.02), 0.7), col, "#C7A15A")  # paja
    t.terminar(col, 0.75, 0.0, t.suma(t.mul(t.ruido(14.0, detalle=6), 0.012), t.mul(restos, 0.006)), bisel=0)

    t = nuevo("tierra_suelta")   # la de la carretilla y el saco abierto: más clara y seca que el sustrato
    col = t.mezcla(t.rango(t.ruido(10.0, detalle=5), 0.3, 0.7), "#4A3626", "#5E4632")
    terrones = t.voronoi(20.0, salida="Distance")
    col = t.mezcla(t.mul(t.rango(terrones, 0.3, 0.05), 0.35), col, "#7A644A")
    t.terminar(col, 0.95, 0.0, t.suma(t.mul(t.rango(terrones, 0.0, 0.4), 0.014), t.mul(t.ruido(30.0), 0.004)),
               bisel=0)

    t = nuevo("galvanizado")   # regadera y balde de la carretilla
    x, y, z = t.xyz()
    lent = t.voronoi(9.0, salida="Distance")
    col = t.mezcla(t.rango(lent, 0.0, 0.6), "#8E979C", "#B0B7BA")
    cav = t.cavidad(0.08)
    col = t.mezcla(t.mul(cav, 0.6), col, "#4A4A42")
    golpe = t.rango(t.ruido(3.0, detalle=2), 0.62, 0.7)
    tierra = t.mul(t.rango(z, P["galv_tierra"], P["galv_tierra"] - 0.5), t.rango(t.ruido(7.0, detalle=4), 0.35, 0.6))
    col = t.mezcla(t.mul(tierra, 0.75), col, "#5C4A36")
    ox = t.mul(cav, t.rango(t.ruido(9.0, detalle=4), 0.5, 0.7))
    col = t.mezcla(ox, col, "#8A5530")
    t.terminar(col, t.lerp(tierra, t.lerp(golpe, 0.35, 0.5), 0.9), t.lerp(t.maxi(tierra, ox), 0.85, 0.1),
               t.suma(t.mul(golpe, -0.006), t.mul(t.ruido(40.0), 0.0015)), bisel=0.008)

    t = nuevo("pintura_carretilla")
    col, rug, met, alt = pintura_metal(t, "#2F6B45", debajo="#9EA3A6", z_oxido=(0.0, 0.7), desconchon=1.0,
                                       rug_pintura=0.45, chorretones=0.1, suciedad=0.5)
    col, rug, _ = _salpicaduras(t, col, rug, 0.0, alto=0.7)
    t.terminar(col, rug, met, alt, bisel=0.01)

    t = nuevo("pintura_verde")   # soporte de la manguera
    col, rug, met, alt = pintura_metal(t, "#2F5444", debajo="#9EA3A6", z_oxido=(1.5, 2.6), desconchon=0.9,
                                       rug_pintura=0.45, chorretones=0.15, suciedad=0.35)
    t.terminar(col, rug, met, alt, bisel=0.008)

    t = nuevo("delantal")   # lona verde con bolsillo, manchada de tierra donde se limpia las manos
    x, y, z = t.xyz()
    trama = t.mul(t.suma(t.ola(70.0, direccion="X"), t.ola(70.0, direccion="Z")), 0.5)
    col = t.mezcla(t.rango(t.ruido(3.0, detalle=3), 0.3, 0.7), "#3F5E3C", "#4C6E46")
    manos = t.mul(t.rango(z, P["delantal_manos"] + 0.35, P["delantal_manos"] - 0.1),
                  t.rango(t.ruido(5.0, detalle=5), 0.35, 0.6))
    col = t.mezcla(t.mul(manos, 0.85), col, "#5A4632")
    col = t.mezcla(t.mul(t.cavidad(0.06), 0.6), col, "#1E2A1A")
    t.terminar(col, 0.92, 0.0, t.mul(trama, 0.0015), bisel=0)

    t = nuevo("pelaje")   # gato atigrado naranja
    x, y, z = t.xyz()
    ox, oy, oz = P["gato"]
    rayas = t.rango(t.ola(9.0, t.estirar((1, 1, 1), desplazar=(-ox, -oy, -oz)), direccion="X", dist=3.0,
                          detalle=2.0), 0.55, 0.8)
    col = t.mezcla(t.mul(rayas, 0.65), "#D58A3E", "#8A4E22")
    blanco = t.rango(z, oz + 0.07, oz + 0.02)      # panza y patas blancas (por abajo)
    col = t.mezcla(t.mul(blanco, 0.85), col, "#EDE3D2")
    pelo = t.ruido(120.0, t.estirar((1, 1, 1)), detalle=2)
    col = t.brillo(col, t.rango(pelo, 0.3, 0.7, 0.88, 1.08))
    col = t.mezcla(t.mul(t.cavidad(0.03), 0.6), col, "#3A2210")
    t.terminar(col, 0.85, 0.0, t.mul(pelo, 0.003), bisel=0)

    t = nuevo("nariz_gato")
    t.terminar("#C9727A", 0.45, 0.0, bisel=0)

    t = nuevo("madera_cartel")   # tablón tallado: barnizado, más claro donde lo frota la lluvia
    x, y, z = t.xyz()
    veta = t.ola(4.0, t.estirar((0.12, 1.0, 1.0)), direccion="Z", dist=5.0, detalle=3.0)
    col = t.mezcla(t.rango(veta, 0.3, 0.9), "#9A6B3E", "#6E4527")
    col = t.mezcla(t.mul(t.cavidad(0.05), 0.85), col, "#2A180C")   # el fondo de las letras talladas
    col = t.mezcla(t.mul(t.borde(0.02), 0.3), col, "#C49A68")
    col, _ = _verdin(t, col, 0.25, escala=6.0)
    t.terminar(col, 0.55, 0.0, t.mul(veta, 0.003), bisel=0.01)

    t = nuevo("letras_cartel")
    t.terminar(t.mezcla(t.rango(t.ruido(20.0, detalle=3), 0.5, 0.7), "#EFE3BF", "#C9BC98"), 0.6, 0.0, bisel=0.004)

    t = nuevo("neon_morado")
    t.terminar("#9B59B6", 0.3, 0.0, emi="#9B59B6", bisel=0)

    t = nuevo("lampara_uv_carcasa")
    t.terminar(t.mezcla(t.mul(t.cavidad(0.05), 0.6), "#E6E8E6", "#7A7E80"), 0.35, 0.2, bisel=0.008)

    return mats
