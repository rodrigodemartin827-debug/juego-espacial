"""Mobiliario urbano (1): farola residencial, banco del parque y fuente de la plaza."""

import math
import random

from ph import NEON, V, Modelo

ZONA = "urbano"


# ==============================================================================================================
def farola_residencial():
    m = Modelo("farola_residencial", ZONA, (1, 1, 8), 2000,
               "Farola de calle: poste fino con base ensanchada y 4 pernos, cabeza LED en forma de cobra, luz cyan, "
               "panel solar pequeño bajo la cabeza y número de identificación en la base.")
    c = m.parte()
    luz = m.parte("led_neon", tipo="neon", color=NEON)
    poste = m.mat("pintura", "#3A424C", desgaste=0.45, lluvia=0.5)
    acero = m.mat("metal", "#848A91")
    horm = m.mat("hormigon", "#8E8A84")
    celda = m.mat("metal", "#1E2E5A", rug=0.15)
    blanco = m.mat("pintura", "#E8E6E0", desgaste=0.3)
    c.caja((0, 0, 0.06), (0.9, 0.9, 0.12), horm, 0.03)
    c.cil((0, 0, 0.12), (0, 0, 0.22), 0.36, acero, n=8)  # placa base
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        c.perno((math.cos(a) * 0.28, math.sin(a) * 0.28, 0.22), (0, 0, 1), acero, r=0.035)
    c.cil((0, 0, 0.22), (0, 0, 1.2), 0.2, poste, n=10, r1=0.1)  # base ensanchada
    c.cil((0, 0, 1.2), (0, 0, 6.6), 0.09, poste, n=10, r1=0.07)
    c.toro((0, 0, 1.2), 0.11, 0.025, acero, n=10, m=3)
    # número de identificación en relieve sobre una plaquita
    c.caja((0, -0.17, 0.75), (0.2, 0.02, 0.12), blanco, 0.0, rot=(-8, 0, 0))
    c.texto("F-27", poste, alto=0.07, grosor=0.01, c=(0, -0.185, 0.72), rot=(82, 0, 0), fuente="mono", resol=1)
    # brazo en cuello de cobra y cabeza curvada
    pts = [(0, 0, 6.5), (0.0, -0.05, 7.2), (0.0, -0.35, 7.6), (0.0, -0.75, 7.65)]
    c.tubo(pts, 0.07, poste, n=8, seg=3, r_fin=0.06)
    cab = V((0.0, -0.95, 7.58))
    c.loft([[cab + V((x * w, y, z)) for x, z in ((-1, 0), (1, 0), (0.85, 0.12), (-0.85, 0.12))]
            for y, w in ((0.25, 0.14), (0.0, 0.2), (-0.3, 0.17), (-0.45, 0.08))], poste)
    luz.caja(cab + V((0, -0.05, -0.01)), (0.3, 0.55, 0.02), None)
    # panel solar pequeño bajo la cabeza, en una ménsula del poste
    c.cil((0, 0, 6.0), (0.0, -0.3, 6.15), 0.025, acero, n=5)
    with c.en((0.0, -0.4, 6.18), (25, 0, 0)):
        c.caja((0, 0, 0), (0.45, 0.32, 0.03), acero, 0.005)
        for i in range(3):
            for j in range(2):
                c.caja((-0.14 + i * 0.14, -0.07 + j * 0.14, 0.018), (0.12, 0.12, 0.01), celda, 0.0)
    m.terminar()


# ==============================================================================================================
def banco_parque():
    m = Modelo("banco_parque", ZONA, (4, 2, 2), 2500,
               "Banco de parque: patas de fundición con curvas y motivo de estrella, asiento de 5 tablones y respaldo de "
               "3 con su separación, 8 tornillos a la vista, reposabrazos metálicos y placa de dedicatoria.")
    c = m.parte()
    fundicion = m.mat("pintura", "#24302A", desgaste=0.5, c_desgaste="#6A706C", lluvia=0.4)
    tabla = m.mat("madera", "#A2703E", eje="X", desgaste=0.4, c_desgaste="#C9A57A", lluvia=0.5)
    acero = m.mat("metal", "#8A9097")
    laton = m.mat("metal", "#C9A040", rug=0.25)
    tinta = m.mat("metal", "#4A3A1A", rug=0.4)
    L = 3.8
    m.seccion("patas de fundición")
    for x in (-1.55, 1.55):
        # perfil lateral de la pata: pie delantero curvo, pie trasero, apoyo del asiento y del respaldo
        perfil = [(-0.75, 0.0), (-0.55, 0.0), (-0.42, 0.45), (0.35, 0.45), (0.55, 0.0), (0.75, 0.0), (0.6, 0.55),
                  (0.62, 0.9), (0.78, 1.75), (0.66, 1.78), (0.5, 0.95), (0.45, 0.62), (-0.55, 0.62), (-0.62, 0.5)]
        c.extruir([(y, z) for y, z in perfil], 0.1, fundicion, c=(x, 0, 0), rot=(90, 0, 90), b=0.02)
        # motivo de estrella calado en relieve en la pata
        estrella = [(math.cos(math.pi / 2 + k * math.pi / 5) * (0.12 if k % 2 == 0 else 0.05),
                     math.sin(math.pi / 2 + k * math.pi / 5) * (0.12 if k % 2 == 0 else 0.05)) for k in range(10)]
        c.extruir(estrella, 0.14, laton, c=(x, 0.0, 0.53), rot=(90, 0, 90))
        # reposabrazos metálico curvo
        c.tubo([(x, 0.55, 0.62), (x, 0.1, 0.95), (x, -0.45, 0.95), (x, -0.6, 0.8)], 0.04, fundicion, n=6, seg=3)
    m.seccion("asiento y respaldo")
    for k in range(5):
        y = -0.5 + k * 0.24
        c.caja((0, y, 0.67), (L, 0.2, 0.08), tabla, 0.015)
    for k in range(3):
        z = 1.0 + k * 0.26
        y = 0.6 + (z - 0.95) * 0.19
        c.caja((0, y, z), (L, 0.07, 0.2), tabla, 0.015, rot=(-11, 0, 0))
    # 8 tornillos de fijación (cabezas sobre los tablones extremos)
    for x in (-1.55, 1.55):
        for y in (-0.5, -0.02, 0.46):
            if y == -0.02:
                continue
            c.perno((x, y, 0.71), (0, 0, 1), acero, r=0.025, arandela=False)
        for z in (1.0, 1.52):
            y = 0.6 + (z - 0.95) * 0.19
            c.perno((x, y - 0.04, z), (0, -1, 0.2), acero, r=0.025, arandela=False)
    # placa de dedicatoria en el respaldo central
    zp = 1.26
    yp = 0.6 + (zp - 0.95) * 0.19 - 0.04
    with c.en((0, yp, zp), (-11, 0, 0)):
        c.caja((0, 0, 0), (0.5, 0.02, 0.12), laton, 0.005)
        c.texto("PARA ELENA", tinta, alto=0.05, grosor=0.008, c=(0, -0.012, -0.025), rot=(90, 0, 0), fuente="mono", resol=1)
    m.terminar()


# ==============================================================================================================
def fuente_plaza():
    m = Modelo("fuente_plaza", ZONA, (6, 6, 3), 6000,
               "Fuente circular de plaza: base octogonal de piedra con molduras, pileta con agua, columna central con 3 "
               "platos de borde geométrico, chorros de cristal, monedas de los deseos en el fondo e iluminación "
               "subacuática cyan.")
    c = m.parte()
    agua = m.parte("agua_cristal", tipo="cristal", color="#9ADCE8", transparencia=0.4, nota="Agua y chorros: Glass.")
    luz = m.parte("luz_neon", tipo="neon", color=NEON, transparencia=0.25)
    rnd = random.Random(131)
    piedra = m.mat("piedra", "#C8C0B0", escala=0.7, rug=0.55)
    piedra2 = m.mat("piedra", "#A8A090", escala=0.7)
    fondo = m.mat("ceramica", "#2E6A7A")
    moneda = [m.mat("metal", "#C9A040", rug=0.25), m.mat("metal", "#B8BCC0", rug=0.25), m.mat("metal", "#B5703A", rug=0.3)]
    m.seccion("pileta octogonal")
    R = 2.95
    # brocal octogonal (torno de 8 lados) con moldura y borde de asiento
    c.torno([(R - 0.55, 0.0), (R, 0.0), (R, 0.12), (R - 0.06, 0.18), (R - 0.06, 0.62), (R + 0.04, 0.7), (R + 0.04, 0.82),
             (R - 0.5, 0.82), (R - 0.5, 0.2)], piedra, n=8)
    c.cil((0, 0, 0.0), (0, 0, 0.2), R - 0.5, fondo, n=8)  # fondo de la pileta
    agua.lamina(lambda u, v: (math.cos(u * math.tau) * (R - 0.52) * v, math.sin(u * math.tau) * (R - 0.52) * v,
                              0.62 + 0.012 * math.sin(v * 22)), 16, 4, 0.04, None)
    for k in range(8):  # luces subacuáticas
        a = k * math.tau / 8 + math.pi / 8
        luz.cil((math.cos(a) * (R - 0.75), math.sin(a) * (R - 0.75), 0.2), (math.cos(a) * (R - 0.75),
                                                                           math.sin(a) * (R - 0.75), 0.24), 0.1, None, n=8)
    for k in range(22):  # monedas de los deseos
        a = rnd.uniform(0, math.tau)
        rr = rnd.uniform(0.8, R - 0.8)
        c.cil((math.cos(a) * rr, math.sin(a) * rr, 0.2), (math.cos(a) * rr, math.sin(a) * rr, 0.215), 0.045,
              moneda[k % 3], n=7)
    m.seccion("columna y platos")
    c.cil((0, 0, 0.2), (0, 0, 0.5), 0.55, piedra2, n=8)
    c.cil((0, 0, 0.5), (0, 0, 2.6), 0.2, piedra, n=8, r1=0.14)
    for k, (z, r) in enumerate(((1.05, 1.3), (1.75, 0.9), (2.4, 0.55))):
        # plato con el borde de dientes geométricos
        c.torno([(0.0, z - 0.25), (r * 0.35, z - 0.2), (r, z - 0.02), (r, z + 0.06), (r * 0.9, z + 0.06),
                 (r * 0.3, z - 0.08), (0.0, z - 0.08)], piedra, n=12)
        for j in range(12):
            a = j * math.tau / 12
            c.caja((math.cos(a) * r, math.sin(a) * r, z + 0.1), (0.14, 0.1, 0.1), piedra2, 0.01,
                   rot=(0, 0, math.degrees(a)))
        agua.cil((0, 0, z - 0.04), (0, 0, z + 0.03), r * 0.88, None, n=12)
        # chorros: cilindros finos de cristal que caen del borde
        for j in range(6):
            a = j * math.tau / 6 + k * 0.5
            p0 = V((math.cos(a) * r, math.sin(a) * r, z))
            zf = (1.05, 1.75)[k - 1] if k > 0 else 0.62
            p1 = V((math.cos(a) * (r + 0.25), math.sin(a) * (r + 0.25), zf + 0.02))
            agua.tubo([p0, p0.lerp(p1, 0.4) + V((math.cos(a) * 0.12, math.sin(a) * 0.12, 0.05)), p1], 0.03, None, n=5,
                      seg=2)
    agua.tubo([(0, 0, 2.6), (0, 0, 2.95), (0.05, 0, 3.0)], 0.05, None, n=6, seg=2)  # surtidor de la cima
    m.terminar()


MODELOS = {
    "farola_residencial": farola_residencial,
    "banco_parque": banco_parque,
    "fuente_plaza": fuente_plaza,
}
