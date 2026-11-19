"""Zona naturaleza (2): palmera alienígena, rocas, río y cascada."""

import math
import random

from ph import NEON, V, Modelo

ZONA = "naturaleza"
AGUA = "#9ADCE8"


def _mechon(c, p, mat, rnd, alto=0.5, hojas=6, ancho=0.05):
    """Mechón de hierba: hojas finas (prismas de 3 lados que acaban en punta) abiertas en abanico."""
    p = V(p)
    for k in range(hojas):
        a = k * math.tau / hojas + rnd.uniform(-0.3, 0.3)
        inc = rnd.uniform(0.15, 0.45)
        h = alto * rnd.uniform(0.7, 1.15)
        tip = p + V((math.cos(a) * h * inc, math.sin(a) * h * inc, h))
        c.cil(p, tip, ancho, mat, n=3, r1=0.0)


def _helecho(c, brillo, p, dirz, mat, rnd, largo=0.9, frondas=5):
    """Helecho alienígena: frondas arqueadas (láminas estrechas con grosor) con la punta luminosa."""
    p = V(p)
    for k in range(frondas):
        a = k * math.tau / frondas + rnd.uniform(-0.4, 0.4)
        d = V((math.cos(a), math.sin(a), 0))
        L = largo * rnd.uniform(0.75, 1.1)

        def f(u, v, d=d, L=L):
            t = u
            ancho = 0.16 * math.sin(math.pi * min(1.0, t * 1.1)) + 0.01
            lado = V((-d.y, d.x, 0))
            q = p + d * (t * L) + V((0, 0, dirz * (math.sin(t * math.pi * 0.8) * L * 0.45 - t * t * L * 0.25)))
            return q + lado * (v - 0.5) * ancho
        c.lamina(f, 6, 1, 0.025, mat)
        tip = p + d * L + V((0, 0, dirz * (math.sin(math.pi * 0.8) * L * 0.45 - L * 0.25)))
        brillo.esfera(tip, 0.04, None, seg=6, anillos=4)


# ==============================================================================================================
def arbol_palmera_alien():
    m = Modelo("arbol_palmera_alien", ZONA, (3, 3, 12), 5000,
               "Palmera alienígena: tronco curvado con anillos de crecimiento modelados como surcos, corona de 7 hojas "
               "en abanico anchas y redondeadas con nervios bioluminiscentes cyan y un racimo de frutos azul oscuro.")
    c = m.parte()
    nervios = m.parte("nervios_neon", tipo="neon", color=NEON, nota="Nervios de las hojas: Neon cyan.")
    rnd = random.Random(31)
    tronco = m.mat("madera", "#7A6048", eje="Z", bump=0.8)
    hoja = m.mat("organico", "#2E7A5A", rug=0.55, bump=0.5)
    hoja2 = m.mat("organico", "#3A8A66", rug=0.55, bump=0.5)
    fruto = m.mat("organico", "#1E2E5A", rug=0.25)
    tierra = m.mat("piedra", "#5A4A36", bump=0.6, escala=1.5)

    m.seccion("tronco con anillos")
    c.cil((0, 0, -0.05), (0, 0, 0.05), 0.9, tierra, n=12, r1=0.7)
    # curva del tronco y puntos cada 0,3: los radios alternan para marcar cada anillo con un surco
    pts, radios = [], []
    n = 34
    for i in range(n + 1):
        t = i / n
        pts.append((0.9 * t * t, 0.15 * math.sin(t * 3.0), 0.0 + t * 10.9))
        r = 0.36 - 0.12 * t
        radios.append(r * (0.86 if i % 2 else 1.0) * (1.25 if i < 2 else 1.0))
    c.tubo(pts, 0.3, tronco, n=10, suave=False, radios=radios)
    copa = V(pts[-1])

    m.seccion("hojas en abanico")
    for k in range(7):
        a = k * math.tau / 7 + rnd.uniform(-0.15, 0.15)
        d = V((math.cos(a), math.sin(a), 0))
        lado = V((-d.y, d.x, 0))
        L = rnd.uniform(2.4, 2.9)
        caida = rnd.uniform(0.9, 1.4)

        def eje_hoja(t, d=d, L=L, caida=caida):
            return copa + d * (t * L) + V((0, 0, 0.55 * math.sin(t * math.pi * 0.7) - caida * t * t))

        def f(u, v, d=d, L=L, lado=lado, eje_hoja=eje_hoja):
            ancho = 1.45 * math.sin(math.pi * min(1.0, u * 0.95)) ** 0.7 + 0.04
            w = (v - 0.5) * ancho
            return eje_hoja(u) + lado * w + V((0, 0, -0.12 * (2 * v - 1) ** 2))  # abanico algo cóncavo
        c.lamina(f, 8, 4, 0.04, hoja if k % 2 else hoja2)
        # nervios luminosos: central y dos laterales, ligeramente por encima de la hoja
        nervios.tubo([eje_hoja(t) + V((0, 0, 0.035)) for t in (0.05, 0.3, 0.55, 0.8, 0.97)], 0.018, None, n=4,
                     suave=False)
        for s in (-1, 1):
            nervios.tubo([eje_hoja(t) + lado * s * 0.42 * math.sin(math.pi * t) + V((0, 0, 0.0)) for t in
                          (0.15, 0.4, 0.65, 0.88)], 0.012, None, n=3, suave=False)
    c.ico(copa + V((0, 0, 0.1)), 0.42, hoja, sub=2, esc=(1, 1, 0.7), suave=(0.12, 1.5), semilla=2)

    m.seccion("racimo de frutos")
    r0 = copa + V((-0.3, 0.1, -0.35))
    c.cil(copa + V((-0.15, 0.05, -0.05)), r0, 0.04, tronco, n=5)
    for k in range(6):
        a = k * math.tau / 5
        q = r0 + (V((math.cos(a) * 0.14, math.sin(a) * 0.14, -0.1)) if k < 5 else V((0, 0, -0.28)))
        c.esfera(q, 0.13, fruto, seg=10, anillos=6)
    m.terminar()


# ==============================================================================================================
def roca_grande():
    m = Modelo("roca_grande", ZONA, (4, 3, 3), 3000,
               "Roca grande erosionada: gris con vetas de mineral azulado, musgo arriba, líquenes en la cara norte "
               "(+Z de Roblox) y cristales cyan asomando por las grietas.")
    c = m.parte()
    cristal = m.parte("cristales_neon", tipo="neon", color=NEON, transparencia=0.15)
    rnd = random.Random(41)
    piedra = m.mat("piedra", "#7E7C78", escala=0.9, manchas=[
        (0.0, 0.0, 3.0, 1.6, "#4E6B2A", 0.85),     # musgo en lo alto
        (-0.6, 0.6, 2.6, 0.8, "#5A7A30", 0.7),
        (0.5, 1.3, 1.4, 0.7, "#A8A24A", 0.55),     # líquenes en la cara norte
        (-0.4, 1.3, 1.0, 0.5, "#B4B05A", 0.5),
        (1.2, -0.8, 1.2, 0.5, "#3A5A8A", 0.8),     # vetas azuladas
        (-1.3, -0.5, 1.6, 0.45, "#3A5A8A", 0.7)])
    # masa principal y dos lóbulos erosionados
    c.ico((0, 0, 1.0), 1.6, piedra, sub=4, esc=(1.25, 0.95, 0.85), suave=(0.22, 1.4), semilla=3, base_plana=-0.75)
    c.ico((1.2, 0.3, 0.58), 0.95, piedra, sub=3, esc=(1.0, 0.9, 0.8), suave=(0.25, 1.6), semilla=8, base_plana=-0.8)
    c.ico((-1.25, -0.2, 0.52), 0.8, piedra, sub=3, esc=(1.1, 0.95, 0.85), suave=(0.25, 1.6), semilla=12, base_plana=-0.8)
    # cristales cyan en las grietas: prismas de 6 caras con punta
    for k, (p, d) in enumerate((((0.9, -1.0, 1.3), (0.3, -1, 0.5)), ((-0.6, -1.05, 1.6), (-0.2, -1, 0.6)),
                                ((1.6, -0.4, 1.1), (1, -0.3, 0.4)), ((0.2, -0.4, 2.45), (0.1, -0.2, 1)))):
        p, d = V(p), V(d).normalized()
        for j in range(2):
            dd = (d + V((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), rnd.uniform(0, 0.3)))).normalized()
            L = rnd.uniform(0.25, 0.45)
            cristal.cil(p - dd * 0.15, p + dd * L, 0.06, None, n=6)
            cristal.cil(p + dd * L, p + dd * (L + 0.12), 0.06, None, n=6, r1=0.0)
    m.terminar()


# ==============================================================================================================
def roca_formacion():
    m = Modelo("roca_formacion", ZONA, (6, 4, 5), 5000,
               "Formación de tres rocas de distinto tamaño (la principal inclinada), mechones de hierba y una "
               "enredadera creciendo entre ellas y un charco de agua en la base.")
    c = m.parte()
    agua = m.parte("charco_cristal", tipo="cristal", color=AGUA, transparencia=0.45, nota="Agua del charco: Glass.")
    rnd = random.Random(43)
    piedra = m.mat("piedra", "#7A766E", escala=0.9, manchas=[(0.0, 0.0, 4.8, 1.6, "#4E6B2A", 0.75),
                                                           (1.8, 0.4, 2.6, 1.0, "#4E6B2A", 0.6)])
    piedra2 = m.mat("piedra", "#6A665E", escala=0.9, manchas=[(-2.0, 0.2, 2.2, 1.0, "#4E6B2A", 0.6)])
    hierba = [m.mat("organico", "#4E8A3A", rug=0.7), m.mat("organico", "#3E7A44", rug=0.7)]
    hoja = m.mat("organico", "#3A7A34", rug=0.6)
    tallo = m.mat("madera", "#4A5A2A", eje="Z")
    barro = m.mat("piedra", "#4E4236", bump=0.5, escala=2.0)
    # roca principal inclinada
    with c.en((0.2, 0.2, 2.15), (0, 14, 8)):
        c.ico((0, 0, 0), 1.9, piedra, sub=4, esc=(0.9, 0.85, 1.25), suave=(0.2, 1.3), semilla=5, base_plana=-0.95)
    c.ico((2.0, 0.4, 0.88), 1.1, piedra, sub=3, esc=(1.0, 0.9, 0.95), suave=(0.22, 1.5), semilla=9, base_plana=-0.85)
    c.ico((-2.0, 0.0, 0.58), 0.85, piedra2, sub=3, esc=(1.1, 1.0, 0.85), suave=(0.25, 1.6), semilla=14, base_plana=-0.8)
    # charco en la base (orilla de barro y agua con grosor)
    cx, cy = -0.6, -1.5
    c.cil((cx, cy, -0.02), (cx, cy, 0.05), 1.05, barro, n=16, r1=0.95)
    agua.lamina(lambda u, v: (cx + math.cos(u * math.tau) * 0.85 * v, cy + math.sin(u * math.tau) * 0.6 * v,
                              0.07 + 0.006 * math.sin(v * 12)), 16, 2, 0.03, None)
    # mechones de hierba entre las rocas y alrededor del charco
    for (x, y) in ((1.0, -0.8), (-1.1, -0.6), (1.2, 1.2), (-1.4, 1.0), (0.4, -1.6), (-1.7, -1.4), (2.9, -0.3),
                   (-2.9, 0.4), (0.0, -2.2)):
        _mechon(c, (x, y, 0.0), hierba[rnd.randrange(2)], rnd, alto=rnd.uniform(0.35, 0.6))
    # enredadera que trepa por la roca principal con hojitas
    pts = [(-0.9, -0.9, 0.1), (-1.0, -0.8, 1.0), (-0.6, -1.0, 1.9), (-0.2, -1.2, 2.7), (0.3, -1.05, 3.3)]
    c.tubo(pts, 0.03, tallo, n=4, seg=3)
    for k in range(8):
        t = (k + 0.5) / 8
        i = min(int(t * 4), 3)
        p = V(pts[i]).lerp(V(pts[i + 1]), t * 4 - i)
        c.ico(p + V((rnd.uniform(-0.1, 0.1), -0.08, 0)), 0.12, hoja, sub=1, esc=(1, 0.4, 0.8), semilla=k)
    m.terminar()


# ==============================================================================================================
def rio_segmento():
    m = Modelo("rio_segmento", ZONA, (8, 4, 0.5), 3000,
               "Segmento modular de río de 8 studs: lecho de piedras bajo el agua, superficie de agua ondulada "
               "semitransparente y orillas de tierra y hierba con piedras. Se encadena por los extremos (eje X).")
    c = m.parte()
    agua = m.parte("agua_cristal", tipo="cristal", color=AGUA, transparencia=0.4,
                   nota="Agua: Glass celeste, Transparency 0,4. Las ondas están modeladas en la superficie.")
    rnd = random.Random(47)
    L, W = 8.0, 4.0
    lecho = m.mat("piedra", "#5E5A50", bump=0.7, escala=1.8)
    tierra = m.mat("piedra", "#5A4A36", bump=0.6, escala=1.6)
    hierba = m.mat("organico", "#4E8A3A", rug=0.8, bump=0.6)
    canto = [m.mat("piedra", h, escala=1.2) for h in ("#8A867E", "#6E6A62", "#9A9488")]
    # perfil del cauce: orillas altas a los lados, fondo hundido en el centro (sólido con grosor)
    def fondo(u, v):
        y = -W / 2 + v * W
        t = abs(y) / (W / 2)
        z = 0.05 + 0.3 * max(0.0, (t - 0.55) / 0.45) ** 1.4
        return (-L / 2 + u * L, y, z)
    c.lamina(fondo, 8, 8, 0.1, lecho)
    for s in (-1, 1):  # orillas de tierra con la franja de hierba encima
        c.caja((0, s * (W / 2 - 0.25), 0.25), (L, 0.5, 0.3), tierra, 0.04)
        c.caja((0, s * (W / 2 - 0.2), 0.43), (L, 0.42, 0.06), hierba, 0.02)
    # piedras del lecho (bajo el agua) y de orilla
    for i in range(13):
        x = rnd.uniform(-L / 2 + 0.4, L / 2 - 0.4)
        y = rnd.uniform(-1.0, 1.0)
        c.roca((x, y, 0.08), rnd.uniform(0.15, 0.3), canto[i % 3], semilla=i, esc=(1.2, 1.0, 0.45), ruido=0.0, sub=2,
               suave=(0.25, 1.5))
    for i in range(10):
        s = 1 if i % 2 else -1
        x = rnd.uniform(-L / 2 + 0.3, L / 2 - 0.3)
        c.roca((x, s * rnd.uniform(1.35, 1.6), 0.35), rnd.uniform(0.18, 0.3), canto[i % 3], semilla=40 + i,
               esc=(1.1, 1.0, 0.7), ruido=0.0, sub=2, suave=(0.25, 1.5))
    # agua: lámina con ondas (no plana) que llega de extremo a extremo
    agua.lamina(lambda u, v: (-L / 2 + u * L, -1.45 + v * 2.9,
                              0.32 + 0.025 * math.sin(u * 22 + v * 3) + 0.015 * math.sin(u * 9 - v * 11)), 20, 6, 0.04,
                None)
    m.notas.append("Los extremos están cortados en x = ±4: coloca los segmentos cada 8 studs en el eje X de Roblox.")
    m.terminar()


# ==============================================================================================================
def cascada_pequena():
    m = Modelo("cascada_pequena", ZONA, (4, 2, 6), 5000,
               "Cascada: pared de roca con musgo, cortina de agua ondulada semitransparente, poza con ondas "
               "concéntricas, gotas de salpicadura suspendidas y helechos alienígenas con puntas luminosas en las "
               "grietas.")
    c = m.parte()
    agua = m.parte("agua_cristal", tipo="cristal", color=AGUA, transparencia=0.35)
    brillo = m.parte("helechos_neon", tipo="neon", color=NEON)
    rnd = random.Random(53)
    roca = m.mat("piedra", "#6E6A62", escala=1.0, manchas=[(0.0, 0.0, 6.0, 1.8, "#4E6B2A", 0.8),
                                                         (-1.5, -0.5, 3.0, 0.9, "#4E6B2A", 0.7),
                                                         (1.6, -0.5, 2.0, 0.8, "#4E6B2A", 0.7)])
    oscura = m.mat("piedra", "#4E4A44", escala=1.2)
    espuma = m.mat("tiza", "#EEF6F8")
    helecho = m.mat("organico", "#3E8A5A", rug=0.6)
    # pared de roca: bloques redondeados apilados a ambos lados del canal y detrás de la cortina
    bloques = [(-1.45, 0.3, 1.0, 0.95), (-1.5, 0.35, 2.6, 0.9), (-1.35, 0.3, 4.1, 0.85), (-1.1, 0.35, 5.3, 0.7),
               (1.45, 0.3, 1.0, 0.95), (1.5, 0.35, 2.6, 0.9), (1.35, 0.3, 4.1, 0.85), (1.1, 0.35, 5.3, 0.7),
               (0.0, 0.65, 1.4, 0.95), (0.0, 0.7, 3.2, 0.95), (0.0, 0.65, 4.8, 0.85)]
    for i, (x, y, z, r) in enumerate(bloques):
        c.ico((x, y, z), r, roca if i % 3 else oscura, sub=2, esc=(1.0, 0.75, 1.0), suave=(0.22, 1.5), semilla=i)
    # labio del salto (piedra plana por la que rebosa el agua)
    c.ico((0.0, 0.2, 5.55), 0.75, roca, sub=2, esc=(1.2, 0.9, 0.35), suave=(0.15, 1.5), semilla=30)
    # cortina de agua: lámina ondulada que cae del labio a la poza, más ancha abajo
    agua.lamina(lambda u, v: ((u - 0.5) * (0.9 + 0.35 * v) + 0.04 * math.sin(v * 9 + u * 6),
                              -0.15 - 0.25 * v * v + 0.03 * math.sin(u * 11 + v * 4), 5.55 - v * 5.2), 6, 10, 0.06,
                None)
    # regueros de espuma blanca sobre la cortina (lo que hace que el agua se lea como agua que cae)
    for k in range(4):
        x0 = -0.32 + k * 0.21
        fase = rnd.uniform(0, 3)
        c.lamina(lambda u, v, x0=x0, fase=fase: (x0 * (1 + 0.35 * v) + (u - 0.5) * 0.06 + 0.04 * math.sin(v * 9 + fase),
                                                 -0.2 - 0.25 * v * v + 0.03 * math.sin(v * 4), 5.5 - v * 5.0), 1, 8, 0.02,
                 espuma)
    # poza: borde de piedras y agua con ondas concéntricas
    for k in range(9):
        a = math.pi + k * math.pi / 8
        c.roca((math.cos(a) * 1.6, -0.5 + math.sin(a) * 0.62, 0.18), rnd.uniform(0.25, 0.35), oscura, semilla=50 + k,
               esc=(1.1, 1.0, 0.7), ruido=0.0, sub=2, suave=(0.25, 1.5))
    c.cil((0, -0.55, -0.02), (0, -0.55, 0.06), 1.6, oscura, n=16)  # fondo de la poza
    agua.lamina(lambda u, v: (math.cos(u * math.tau) * 1.45 * v, -0.5 + math.sin(u * math.tau) * 0.55 * v,
                              0.24 + 0.025 * math.cos(v * 18)), 18, 4, 0.04, None)
    # espuma donde cae el agua y gotas suspendidas
    for k in range(3):
        c.ico((rnd.uniform(-0.45, 0.45), -0.45 + rnd.uniform(-0.15, 0.15), 0.32), rnd.uniform(0.12, 0.2), espuma, sub=2,
              esc=(1, 1, 0.6), suave=(0.2, 2.0), semilla=60 + k)
    for k in range(6):
        a = rnd.uniform(0, math.tau)
        agua.esfera((math.cos(a) * rnd.uniform(0.3, 0.8), -0.5 + math.sin(a) * 0.4, rnd.uniform(0.45, 1.1)),
                    rnd.uniform(0.03, 0.05), None, seg=6, anillos=4)
    # helechos en las grietas
    for (p, dz) in (((-1.0, -0.35, 3.4), 1), ((1.0, -0.3, 1.9), 1), ((-0.9, -0.4, 1.0), 1), ((1.1, -0.3, 4.6), 1)):
        _helecho(c, brillo, p, dz, helecho, rnd, largo=0.75)
    m.terminar()


MODELOS = {
    "arbol_palmera_alien": arbol_palmera_alien,
    "roca_grande": roca_grande,
    "roca_formacion": roca_formacion,
    "rio_segmento": rio_segmento,
    "cascada_pequena": cascada_pequena,
}
