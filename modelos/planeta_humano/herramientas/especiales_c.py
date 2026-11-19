"""Edificios especiales (3): monumento a los fundadores y muro perimetral modular."""

import math
import random

import arq
from ph import NEON, V, Modelo

ZONA = "especiales"


def _figura_astronauta(c, mat, base, rnd):
    """Figura humana de pie con traje espacial mirando al cielo: casco en la mano izquierda y bandera en la derecha.
    base = punto entre los pies. Altura ~3,2 (escala heroica)."""
    b = V(base)
    k = 1.0
    # piernas y botas
    for s in (-1, 1):
        cad = b + V((s * 0.2, 0.0, 1.5))
        rod = b + V((s * 0.22, -0.05 + (0.08 if s > 0 else -0.06), 0.8))
        tob = b + V((s * 0.24, 0.0, 0.2))
        c.tubo([cad, rod, tob], 0.17, mat, n=10, suave=False, r_fin=0.13)
        c.esfera(rod, 0.17, mat, seg=10, anillos=6)  # rodillera
        c.caja(tob + V((0, -0.08, -0.08)), (0.3, 0.48, 0.24), mat, 0.07)  # bota
        c.toro(tob + V((0, 0, 0.12)), 0.15, 0.03, mat, n=10, m=3)
    # cadera, torso y mochila de soporte vital
    c.loft([[b + V((math.cos(a) * w, math.sin(a) * d, z)) for a in [i * math.tau / 12 for i in range(12)]]
            for z, w, d in ((1.45, 0.4, 0.24), (1.7, 0.38, 0.23), (2.2, 0.45, 0.27), (2.55, 0.48, 0.28), (2.7, 0.3, 0.2))],
           mat)
    c.caja(b + V((0, 0.33, 2.15)), (0.62, 0.3, 0.8), mat, 0.08)  # mochila
    c.caja(b + V((0, -0.28, 2.2)), (0.32, 0.06, 0.26), mat, 0.03)  # panel del pecho
    for kz in range(3):
        c.cil(b + V((-0.08 + kz * 0.08, -0.31, 2.22)), b + V((-0.08 + kz * 0.08, -0.34, 2.22)), 0.025, mat, n=6)
    c.toro(b + V((0, 0, 2.72)), 0.24, 0.05, mat, n=12, m=4)  # cuello del traje
    # cabeza mirando al cielo (inclinada hacia atrás)
    with c.en(b + V((0, 0.02, 2.95)), (-28, 0, 0)):
        c.esfera((0, 0, 0), 0.2, mat, seg=12, anillos=8, esc=(0.9, 1.0, 1.1))
        c.esfera((0, -0.16, -0.02), 0.05, mat, seg=6, anillos=4)  # nariz
    # brazo derecho alzando la bandera (lado +X del modelo... la derecha de la figura es -X)
    hd = b + V((-0.5, 0.0, 2.55))
    cd = hd + V((-0.22, -0.05, 0.4))
    md = cd + V((0.02, -0.08, 0.45))
    c.tubo([hd, cd, md], 0.12, mat, n=8, suave=False, r_fin=0.1)
    c.esfera(hd, 0.15, mat, seg=10, anillos=6)
    c.esfera(md, 0.11, mat, seg=8, anillos=5)
    asta0 = md + V((0, 0, -1.2))
    asta1 = md + V((0, 0, 1.6))
    c.cil(asta0, asta1, 0.035, mat, n=6)
    c.esfera(asta1, 0.06, mat, seg=6, anillos=4)
    c.lamina(lambda u, v: asta1 + V((-0.05 - u * 1.0, 0.1 * math.sin(u * 5) * u, -0.08 - v * 0.65 - 0.06 * u)), 8, 2, 0.04,
             mat)
    # brazo izquierdo bajado con el casco en la mano
    hi = b + V((0.5, 0.0, 2.55))
    ci = hi + V((0.14, -0.02, -0.5))
    mi = ci + V((0.06, -0.12, -0.42))
    c.tubo([hi, ci, mi], 0.12, mat, n=8, suave=False, r_fin=0.1)
    c.esfera(hi, 0.15, mat, seg=10, anillos=6)
    c.esfera(mi + V((0.18, -0.1, -0.05)), 0.27, mat, seg=12, anillos=8)  # casco
    c.cil(mi + V((0.18, -0.36, -0.05)), mi + V((0.18, -0.3, -0.05)), 0.17, mat, n=12)  # visor
    c.toro(mi + V((0.18, -0.1, -0.3)), 0.2, 0.04, mat, n=12, m=3)


# ==============================================================================================================
def monumento_fundadores():
    m = Modelo("monumento_fundadores", ZONA, (3, 3, 8), 8000,
               "Monumento a los fundadores: pedestal de piedra de 3 escalones con placa de bronce A LOS QUE LLEGARON "
               "PRIMERO, estatua de un astronauta mirando al cielo con el casco en una mano y la bandera en la otra, "
               "corona de flores metálica, dos focos que la iluminan desde abajo y dos bancos de piedra a los lados.")
    c = m.parte()
    luces = m.parte("focos_neon", tipo="neon", color=NEON)
    rnd = random.Random(111)
    piedra = m.mat("piedra", "#B8B0A0", escala=0.7, rug=0.6)
    piedra2 = m.mat("piedra", "#9E968A", escala=0.7)
    bronce = m.mat("metal", "#7A5E34", rug=0.38, aranazos=0.2,
                   manchas=[(0.0, -0.3, 4.2, 0.6, "#3E7A64", 0.55), (0.3, 0.3, 5.6, 0.5, "#3E7A64", 0.5),
                            (-0.6, 0.0, 6.2, 0.4, "#3E7A64", 0.45)])  # pátina verde
    laton = m.mat("metal", "#C9A040", rug=0.25)
    tinta = m.mat("metal", "#4A3A1A", rug=0.4)
    esmalte = [m.mat("pintura", h, desgaste=0.3, c_desgaste="#C9A040") for h in ("#B83A3A", "#E8D24A", "#F0F0F0")]
    osc = m.mat("metal", "#24282C", rug=0.45)
    m.seccion("pedestal")
    for k, (lado, alto) in enumerate(((3.0, 0.2), (2.6, 0.2), (2.2, 0.2))):
        c.caja((0, 0, 0.1 + k * 0.2), (lado, lado, alto), piedra2 if k % 2 else piedra, 0.03)
    c.caja((0, 0, 0.6 + 1.0), (1.6, 1.6, 2.0), piedra, 0.05)
    c.caja((0, 0, 0.7), (1.75, 1.75, 0.2), piedra2, 0.04)  # basa
    c.caja((0, 0, 2.7), (1.85, 1.85, 0.2), piedra2, 0.05)  # cornisa
    c.caja((0, 0, 2.85), (1.5, 1.5, 0.1), piedra, 0.03)
    # placa de bronce con el texto en relieve
    c.caja((0, -0.82, 1.65), (1.3, 0.05, 0.75), laton, 0.02)
    c.texto("A LOS QUE", tinta, alto=0.14, grosor=0.02, c=(0, -0.85, 1.83), fuente="mono", resol=1)
    c.texto("LLEGARON PRIMERO", tinta, alto=0.12, grosor=0.02, c=(0, -0.85, 1.55), fuente="mono", resol=1)
    c.caja((0, -0.85, 1.45), (1.0, 0.012, 0.02), tinta, 0.0)
    for dx in (-0.58, 0.58):
        for dz in (-0.3, 0.3):
            c.perno((dx, -0.85, 1.65 + dz), (0, -1, 0), laton, r=0.025, arandela=False)
    m.seccion("estatua")
    _figura_astronauta(c, bronce, (0, 0.05, 2.9), rnd)
    m.seccion("corona de flores")
    cw = V((0, -1.25, 0.75))
    with c.en(cw, (78, 0, 0)):
        c.toro((0, 0, 0), 0.32, 0.05, laton, n=16, m=4)
        for k in range(14):
            a = k * math.tau / 14
            p = V((math.cos(a) * 0.32, math.sin(a) * 0.32, 0.03))
            if k % 2:
                c.ico(p, 0.07, esmalte[k % 3], sub=1, esc=(1, 1, 0.6))
            else:
                c.ico(p, 0.06, laton, sub=1, esc=(1.6, 0.7, 0.4), semilla=k)
    c.caja((0, -1.22, 0.55), (0.06, 0.06, 0.4), laton, 0.01)
    m.seccion("focos y bancos")
    for s in (-1, 1):
        p = V((s * 1.05, -1.05, 0.62))
        c.caja(p, (0.3, 0.25, 0.12), osc, 0.02)
        with c.en(p + V((0, 0, 0.18)), (-70, 0, s * 25)):
            c.cil((0, 0, -0.1), (0, 0, 0.12), 0.11, osc, n=10)
            luces.cil((0, 0, 0.12), (0, 0, 0.135), 0.085, None, n=10)
    for s in (-1, 1):
        x = s * 2.35
        for y in (-0.6, 0.6):
            c.caja((x, y, 0.22), (0.5, 0.3, 0.44), piedra2, 0.04)
        c.caja((x, 0, 0.5), (0.65, 1.8, 0.14), piedra, 0.04)
    m.terminar()


# ==============================================================================================================
def muro_perimetral():
    m = Modelo("muro_perimetral", ZONA, (6, 1, 5), 4000,
               "Segmento modular de muro defensivo de 6 studs: paneles de acero con costillas, pasarela superior con "
               "barandilla, torreta automática giratoria (pieza aparte), luces de seguridad cyan, puerta peatonal "
               "(pieza aparte, con su tapa para los tramos sin puerta) y escalera (pieza aparte, para 1 de cada 4).")
    c = m.parte()
    torreta = m.parte("torreta", pivote=(1.6, 0.0, 5.0), nota="Torreta: gira sobre el eje vertical del pivote.")
    puerta = m.parte("puerta", pivote=(-1.95, -0.32, 0.25), nota="Puerta peatonal: gira sobre su bisagra.")
    tapa = m.parte("tapa_sin_puerta", nota="Para los tramos SIN puerta: deja esta pieza y borra la puerta. En los tramos "
                                           "con puerta, borra esta tapa.")
    escalera = m.parte("escalera", nota="Escalera de acceso a la pasarela: déjala en uno de cada 4 tramos.")
    luces = m.parte("luces_neon", tipo="neon", color=NEON)
    acero = m.mat("paneles", "#5A626C", tam_panel=(1.5, 1.4), desgaste=0.45, lluvia=0.5)
    costilla = m.mat("pintura", "#3A424C", desgaste=0.5)
    horm = m.mat("hormigon", "#8E8A84")
    metal = m.mat("metal", "#848A91")
    osc = m.mat("metal", "#24282C", rug=0.45)
    amar = m.mat("pintura", "#E3B22A", desgaste=0.6)
    grip = m.mat("grip", "#6E747A")
    L, G, H = 6.0, 0.6, 4.2
    m.seccion("muro")
    c.caja((0, 0, 0.12), (L, 1.0, 0.25), horm, 0.03)  # zapata
    PUE = (-1.95, -0.95, 0.25, 2.55)
    arq.muro_huecos(c, -L / 2, L / 2, 0.25, H, -G / 2, G / 2, [PUE], acero, b=0.0)
    for s in (-1, 1):  # costillas verticales en las dos caras
        for k in range(6):
            x = -L / 2 + 0.5 + k * (L - 1.0) / 5
            if PUE[0] - 0.1 < x < PUE[1] + 0.1:
                continue
            c.caja((x, s * (G / 2 + 0.06), (0.25 + H) / 2), (0.14, 0.12, H - 0.25), costilla, 0.02)
        c.caja((0, s * (G / 2 + 0.04), H - 0.3), (L, 0.08, 0.14), costilla, 0.01)
        c.caja((0, s * (G / 2 + 0.04), 0.55), (L, 0.08, 0.14), costilla, 0.01)
    arq.marco(c, PUE[0], PUE[1], PUE[2], PUE[3], -G / 2, 0.1, 0.08, osc, abajo=False)
    puerta.caja_de((PUE[0] + 0.02, -G / 2 - 0.02, PUE[2]), (PUE[1] - 0.02, -G / 2 + 0.08, PUE[3] - 0.02), osc, 0.02)
    puerta.cil((PUE[1] - 0.2, -G / 2 - 0.03, 1.4), (PUE[1] - 0.2, -G / 2 - 0.12, 1.4), 0.025, metal, n=6)
    puerta.caja(((PUE[0] + PUE[1]) / 2, -G / 2 - 0.03, 2.1), (0.4, 0.02, 0.15), amar, 0.0)
    tapa.caja_de((PUE[0], -G / 2 + 0.01, PUE[2]), (PUE[1], G / 2 - 0.01, PUE[3]), acero)
    m.seccion("pasarela y barandilla")
    c.caja((0, 0.1, H + 0.06), (L, 1.0, 0.12), grip, 0.02)
    for k in range(4):
        c.extruir([(0, 0), (0.45, 0), (0, -0.45)], 0.08, costilla, c=(-L / 2 + 0.8 + k * 1.45, G / 2, H), rot=(90, 0, 90))
    # parapeto exterior (cara -Y) y barandilla interior
    c.caja((0, -0.42, H + 0.5), (L, 0.16, 0.9), acero, 0.03)
    for k in range(4):  # almenas
        c.caja((-L / 2 + 0.75 + k * 1.5, -0.42, H + 1.05), (0.7, 0.18, 0.2), acero, 0.02)
    for x in (-L / 2 + 0.1, 0.0, L / 2 - 0.1):
        c.cil((x, 0.55, H + 0.12), (x, 0.55, H + 1.0), 0.035, amar, n=6)
    c.cil((-L / 2, 0.55, H + 1.0), (L / 2, 0.55, H + 1.0), 0.035, amar, n=6)
    c.cil((-L / 2, 0.55, H + 0.55), (L / 2, 0.55, H + 0.55), 0.025, amar, n=5)
    for x in (-2.0, 0.0, 2.0):  # luces de seguridad en el parapeto
        c.caja((x, -0.53, H + 0.7), (0.3, 0.08, 0.14), osc, 0.02)
        luces.caja((x, -0.575, H + 0.7), (0.24, 0.01, 0.08), None)
    m.seccion("torreta")
    tx = 1.6
    c.cil((tx, 0.05, H + 0.12), (tx, 0.05, H + 0.4), 0.38, osc, n=12)
    torreta.pivote = V((tx, 0.05, H + 0.4))
    torreta.cil((tx, 0.05, H + 0.4), (tx, 0.05, H + 0.55), 0.34, metal, n=12)
    torreta.caja((tx, 0.05, H + 0.78), (0.5, 0.55, 0.38), osc, 0.06)
    for s in (-1, 1):
        torreta.cil((tx + s * 0.1, -0.2, H + 0.78), (tx + s * 0.1, -1.0, H + 0.78), 0.045, metal, n=8)
        torreta.cil((tx + s * 0.1, -1.0, H + 0.78), (tx + s * 0.1, -1.08, H + 0.78), 0.06, osc, n=8)
    torreta.caja((tx + 0.3, 0.1, H + 0.85), (0.1, 0.2, 0.15), metal, 0.01)  # sensor
    luces.cil((tx + 0.36, 0.0, H + 0.88), (tx + 0.38, 0.0, H + 0.88), 0.04, None, n=8)
    m.seccion("escalera")
    ex = -2.6
    for s in (-1, 1):
        escalera.cil((ex + s * 0.25, G / 2 + 0.35, 0.25), (ex + s * 0.25, G / 2 + 0.35, H + 1.0), 0.035, amar, n=5)
    for k in range(13):
        z = 0.55 + k * 0.32
        escalera.cil((ex - 0.25, G / 2 + 0.35, z), (ex + 0.25, G / 2 + 0.35, z), 0.02, amar, n=4)
    for z in (1.0, 2.5, 3.8):
        for s in (-1, 1):
            escalera.cil((ex + s * 0.25, G / 2 + 0.35, z), (ex + s * 0.25, G / 2 + 0.02, z), 0.02, amar, n=4)
    m.notas.append("Los extremos están en x = ±3: coloca los tramos cada 6 studs en el eje X de Roblox.")
    m.terminar()


MODELOS = {
    "monumento_fundadores": monumento_fundadores,
    "muro_perimetral": muro_perimetral,
}
