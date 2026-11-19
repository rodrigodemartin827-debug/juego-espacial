"""Zona naturaleza (3): puente de piedra, flores luminosas, hongo, cristal, césped y nenúfar."""

import math
import random

from ph import NEON, V, Modelo, base_eje

ZONA = "naturaleza"
AZUL_FLOR = "#5B9BD5"


# ==============================================================================================================
def puente_rio_piedra():
    m = Modelo("puente_rio_piedra", ZONA, (8, 4, 3), 4000,
               "Puente de piedra de un arco: dovelas individuales con juntas, tímpanos de sillería, calzada de "
               "adoquines 3D, pretiles bajos de piedra, musgo bajo el arco y marcas de humedad en las piedras bajas.")
    c = m.parte()
    rnd = random.Random(61)
    # humedad: manchas oscuras a lo largo de la base de los estribos; musgo en el intradós
    humedad = [(x, y, 0.15, 0.55, "#3A3A34", 0.7) for x in (-3.6, -3.0, -2.5, 2.5, 3.0, 3.6) for y in (-1.6, 1.6)]
    sillar = m.mat("ladrillo", "#8E887C", c2="#5E5A52", tam_ladrillo=(0.9, 0.45), manchas=humedad)
    dovela = m.mat("piedra", "#9A9282", escala=0.8, manchas=[(x, 0.0, z, 0.9, "#4E6B2A", 0.85) for x, z in
                                                            ((-1.8, 0.6), (0.0, 1.2), (1.8, 0.6))])
    adoquin = [m.mat("piedra", h, escala=1.5) for h in ("#7A766E", "#6E6A62", "#86827A")]
    pretil = m.mat("piedra", "#8A8478", escala=0.9)
    W = 3.2  # ancho de la calzada (Y)

    def zd(x):  # rasante de la calzada: lomo de asno
        return 0.6 + 1.4 * (1 - (x / 4.0) ** 2)

    Rc, zc = 2.6, -1.2  # arco rebajado: centro bajo tierra, arranques a ±2,28 en z = 0
    ang0 = math.asin(1.2 / Rc)  # ángulo del arranque sobre la horizontal
    arco = [(math.cos(a) * Rc, zc + math.sin(a) * Rc) for a in
            [ang0 + (math.pi - 2 * ang0) * i / 12 for i in range(13)]]  # de derecha a izquierda

    m.seccion("tímpanos")
    xa = arco[0][0]
    perfil = [(-4.0, 0.0), (-4.0, zd(-4.0))] + [(x, zd(x)) for x in [-4 + 8 * i / 12 for i in range(1, 12)]] + \
             [(4.0, zd(4.0)), (4.0, 0.0), (xa, 0.0)] + arco[1:-1] + [(-xa, 0.0)]
    for s in (-1, 1):
        c.extruir(perfil, 0.4, sillar, c=(0, s * (W / 2 - 0.2), 0), rot=(90, 0, 0))
    m.seccion("dovelas del arco")
    for i in range(12):
        a0 = ang0 + (math.pi - 2 * ang0) * i / 12
        a1 = ang0 + (math.pi - 2 * ang0) * (i + 1) / 12
        am = (a0 + a1) / 2
        r = Rc + 0.25
        cx, cz = math.cos(am) * r, zc + math.sin(am) * r
        largo = Rc * (a1 - a0) - 0.04  # deja la junta
        c.caja((cx, 0, cz), (largo, W + 0.12, 0.5), dovela, 0.04, rot=(0, -(math.degrees(am) - 90), 0))
    m.seccion("calzada de adoquines")
    # relleno bajo la calzada (lámina gruesa que sigue la rasante) y adoquines encima
    c.lamina(lambda u, v: (-4 + u * 8, -W / 2 + 0.4 + v * (W - 0.8), zd(-4 + u * 8) - 0.15), 16, 1, 0.3, sillar)
    nx = 18
    for i in range(nx):
        x = -4 + (i + 0.5) * 8 / nx
        pend = math.degrees(math.atan(-2 * 1.4 * x / 16.0))
        for j in range(6):
            y = -W / 2 + 0.55 + j * (W - 1.1) / 5 + (0.1 if i % 2 else -0.1) * 0.5
            c.caja((x, y, zd(x) + 0.03), (0.38, 0.36, 0.12), adoquin[(i + j) % 3], 0.0, rot=(0, -pend, 0))
    m.seccion("pretiles")
    for s in (-1, 1):
        for i in range(8):
            x0, x1 = -4 + i, -4 + i + 0.97
            xm = (x0 + x1) / 2
            pend = math.degrees(math.atan(-2 * 1.4 * xm / 16.0))
            c.caja((xm, s * (W / 2 - 0.2), zd(xm) + 0.42), (0.96, 0.36, 0.72), pretil, 0.04, rot=(0, -pend, 0))
            c.caja((xm, s * (W / 2 - 0.2), zd(xm) + 0.84), (1.0, 0.44, 0.12), pretil, 0.03, rot=(0, -pend, 0))
    m.terminar()


# ==============================================================================================================
def flor_luminosa_a():
    m = Modelo("flor_luminosa_a", ZONA, (0.5, 0.5, 1), 500,
               "Flor bioluminiscente abierta: tallo fino, 5 pétalos 3D en estrella, centro brillante con estambres "
               "cyan y una hoja.")
    c = m.parte()
    luz = m.parte("centro_neon", tipo="neon", color=NEON)
    tallo = m.mat("organico", "#3E7A34", rug=0.6)
    petalo = m.mat("organico", "#D8E8F0", rug=0.45, ruido=0.08)
    hoja = m.mat("organico", "#4E8A3A", rug=0.6)
    top = V((0.02, 0.0, 0.78))
    c.tubo([(0, 0, 0), (0.03, 0.0, 0.3), (0.0, 0.02, 0.55), top], 0.018, tallo, n=4, seg=2, r_fin=0.012)
    c.lamina(lambda u, v: (0.02 + u * 0.18, (v - 0.5) * 0.08 * math.sin(math.pi * u), 0.3 + 0.12 * u - 0.1 * u * u), 3, 1,
             0.012, hoja)
    for k in range(5):
        a = k * math.tau / 5
        d = V((math.cos(a), math.sin(a), 0))
        lado = V((-d.y, d.x, 0))
        c.lamina(lambda u, v, d=d, lado=lado: top + d * (0.03 + u * 0.2) + lado * (v - 0.5) * 0.12 * math.sin(math.pi * u)
                 + V((0, 0, 0.06 * u - 0.1 * u * u + 0.02 * (2 * v - 1) ** 2)), 2, 1, 0.015, petalo)
    luz.ico(top + V((0, 0, 0.02)), 0.035, None, sub=2)
    for k in range(5):
        a = k * math.tau / 5 + 0.6
        tip = top + V((math.cos(a) * 0.05, math.sin(a) * 0.05, 0.09))
        luz.cil(top + V((0, 0, 0.02)), tip, 0.006, None, n=3)
        luz.ico(tip, 0.012, None, sub=1)
    m.terminar()


# ==============================================================================================================
def flor_luminosa_b():
    m = Modelo("flor_luminosa_b", ZONA, (0.5, 0.5, 1.2), 500,
               "Flor campana: tallo curvado, flor colgante en forma de campana con el borde ondulado, brillo azul "
               "interno y dos hojas.")
    c = m.parte()
    luz = m.parte("brillo_neon", tipo="neon", color=AZUL_FLOR, nota="Brillo interno: Neon azul #5B9BD5.")
    tallo = m.mat("organico", "#3E7A34", rug=0.6)
    campana = m.mat("organico", "#6A8AC8", rug=0.4, ruido=0.08)
    hoja = m.mat("organico", "#4E8A3A", rug=0.6)
    pts = [(0, 0, 0), (0.0, 0.0, 0.5), (0.04, 0.0, 0.95), (0.16, 0.0, 1.12), (0.24, 0.0, 1.06)]
    c.tubo(pts, 0.016, tallo, n=4, seg=2, r_fin=0.01)
    boca = V((0.25, 0.0, 0.78))
    # campana: superficie de revolución con el borde ondulado (lámina con grosor)
    c.lamina(lambda u, v: boca + V((math.cos(u * math.tau) * (0.025 + 0.085 * v ** 0.8 + 0.012 * math.sin(u * math.tau * 6)
                                                               * v ** 4),
                                    math.sin(u * math.tau) * (0.025 + 0.085 * v ** 0.8 + 0.012 * math.sin(u * math.tau * 6)
                                                              * v ** 4),
                                    0.27 - v * 0.24)), 10, 4, 0.012, campana)
    c.cil(boca + V((0, 0, 0.27)), V(pts[-1]), 0.012, tallo, n=4)
    luz.ico(boca + V((0, 0, 0.09)), 0.05, None, sub=2)
    for k, (z, s) in enumerate(((0.35, 1), (0.58, -1))):
        c.lamina(lambda u, v, z=z, s=s: (s * (0.01 + u * 0.2), (v - 0.5) * 0.09 * math.sin(math.pi * u),
                                         z + 0.1 * u - 0.09 * u * u), 3, 1, 0.012, hoja)
    m.terminar()


# ==============================================================================================================
def hongo_luminoso():
    m = Modelo("hongo_luminoso", ZONA, (1, 1, 2), 1500,
               "Seta grande bioluminiscente: pie grueso poroso con anillo, sombrero convexo con laminillas radiales "
               "debajo, puntos luminosos cyan y esporas flotando alrededor.")
    c = m.parte()
    luz = m.parte("puntos_neon", tipo="neon", color=NEON)
    esporas = m.parte("esporas_neon", tipo="neon", color="#9AF6FF", transparencia=0.3,
                      nota="Esporas flotantes: Neon cyan claro; se pueden mover despacio en el cliente.")
    rnd = random.Random(71)
    pie = m.mat("organico", "#E6DCC6", rug=0.8, bump=1.0, patron="poros", escala=1.5)
    sombrero = m.mat("organico", "#5A3A7A", rug=0.45, bump=0.4)
    lamina_m = m.mat("organico", "#C8B8D8", rug=0.7)
    tierra = m.mat("piedra", "#4E3E2E", bump=0.6, escala=1.6)
    c.cil((0, 0, -0.03), (0, 0, 0.03), 0.45, tierra, n=10, r1=0.38)
    c.torno([(0.0, 0.0), (0.24, 0.0), (0.2, 0.15), (0.16, 0.6), (0.15, 1.15), (0.13, 1.35), (0.0, 1.35)], pie, n=12)
    c.toro((0, 0, 1.0), 0.17, 0.03, pie, n=12, m=4)  # anillo
    # sombrero convexo con borde y su cara inferior
    c.torno([(0.0, 1.2), (0.3, 1.25), (0.45, 1.28), (0.5, 1.33), (0.46, 1.5), (0.33, 1.68), (0.15, 1.78), (0.0, 1.8)],
            sombrero, n=16)
    # laminillas: pliegues radiales bajo el sombrero
    for k in range(16):
        a = k * math.tau / 16
        c.caja((math.cos(a) * 0.31, math.sin(a) * 0.31, 1.24), (0.3, 0.012, 0.06), lamina_m, 0.0,
               rot=(0, 0, math.degrees(a)))
    # puntos luminosos sobre el sombrero
    for k in range(11):
        a = rnd.uniform(0, math.tau)
        t = rnd.uniform(0.15, 0.85)
        r = 0.48 * math.sin(t * math.pi / 2 + 0.25)
        z = 1.33 + 0.45 * math.cos(t * math.pi / 2) * 0.95
        luz.ico((math.cos(a) * r * 0.95, math.sin(a) * r * 0.95, z + 0.02), rnd.uniform(0.025, 0.045), None, sub=1,
                esc=(1, 1, 0.5))
    for k in range(12):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(0.35, 0.55)
        esporas.ico((math.cos(a) * r, math.sin(a) * r, rnd.uniform(0.4, 1.9)), rnd.uniform(0.012, 0.022), None, sub=1)
    m.terminar()


# ==============================================================================================================
def cristal_decorativo():
    m = Modelo("cristal_decorativo", ZONA, (1, 1, 3), 1500,
               "Racimo de 4 cristales cyan (prismas hexagonales con punta) que salen en ángulo de una base de roca, "
               "con cristal semitransparente, núcleo luminoso y polvo de cristal en la base.")
    c = m.parte()
    vidrio = m.parte("cristal", tipo="cristal", color="#7FE8F2", transparencia=0.45,
                     nota="Cuerpo de los cristales: Glass cyan, Transparency 0,45; deja ver el núcleo.")
    nucleo = m.parte("nucleo_neon", tipo="neon", color=NEON, nota="Núcleo luminoso: Neon cyan.")
    roca = m.mat("piedra", "#5E5A54", escala=1.2)
    c.ico((0, 0, 0.18), 0.48, roca, sub=2, esc=(1.0, 0.95, 0.55), suave=(0.25, 1.6), semilla=4, base_plana=-0.6)
    for k, (x, y) in enumerate(((0.38, 0.2), (-0.35, 0.28), (0.1, -0.42))):
        c.ico((x, y, 0.06), 0.13, roca, sub=1, esc=(1.2, 1, 0.6), ruido=0.2, semilla=k)
    datos = [((0.0, 0.0, 0.3), (0.05, 0.02, 1.0), 2.6, 0.17), ((0.12, 0.1, 0.25), (0.45, 0.25, 0.85), 1.6, 0.12),
             ((-0.1, 0.05, 0.25), (-0.4, 0.2, 0.9), 1.3, 0.11), ((0.02, -0.12, 0.22), (0.1, -0.5, 0.85), 1.0, 0.09)]
    for k, (p, d, L, r) in enumerate(datos):
        p, d = V(p), V(d).normalized()
        punta = p + d * L
        vidrio.cil(p, punta - d * r * 1.6, r, None, n=6, giro=k * 0.4)
        vidrio.cil(punta - d * r * 1.6, punta, r, None, n=6, r1=0.0, giro=k * 0.4)
        nucleo.cil(p + d * 0.1, punta - d * r * 2.2, r * 0.42, None, n=6, giro=k * 0.4)
        nucleo.cil(punta - d * r * 2.2, punta - d * r * 0.7, r * 0.42, None, n=6, r1=0.0, giro=k * 0.4)
    rnd = random.Random(77)
    for k in range(16):
        a = rnd.uniform(0, math.tau)
        rr = rnd.uniform(0.3, 0.5)
        nucleo.caja((math.cos(a) * rr, math.sin(a) * rr, rnd.uniform(0.05, 0.3)), (0.025, 0.025, 0.025), None, 0.0,
                    rot=(rnd.uniform(0, 90), rnd.uniform(0, 90), 0))
    m.terminar()


MODELOS = {
    "puente_rio_piedra": puente_rio_piedra,
    "flor_luminosa_a": flor_luminosa_a,
    "flor_luminosa_b": flor_luminosa_b,
    "hongo_luminoso": hongo_luminoso,
    "cristal_decorativo": cristal_decorativo,
}
