"""Ronda 9: props y decoración (81-90)."""

import math

import numpy as np

from formas import craneo
from lib import VERDE, VIOLETA, curva, modelo


@modelo("props", "prop", (0.5, 0.5, 3), "Antorcha de hueso con llama verde (hace de farola).")
def antorcha_organica(M):
    p = M.pieza("antorcha", tris=1050, res=220, k=0.03, ruido=(0.008, 5.0), suelo=0.0)
    p.tubo([(0, 0, 0), (0.015, 0.01, 1.1), (0, 0, 2.05)], [0.085, 0.06, 0.075], "hueso")
    p.esfera((0, 0, 0), 0.13, "hueso_viejo", esc=(1.2, 1, 0.8))
    p.esfera((0.05, 0, 0.02), 0.09, "hueso_viejo")
    p.torno([(0, 2.0), (0.1, 2.02), (0.2, 2.2), (0.21, 2.36), (0.15, 2.38), (0.12, 2.22), (0, 2.16)], (0, 0, 0), "hueso_viejo", k=0.02)   # cazoleta
    for z in (0.7, 0.78, 1.5):
        p.toro((0.01, 0.005, z), 0.075, 0.022, "cuero", k=0.01)        # empuñadura de tiras de cuero
    d = p.duro
    for j in range(5):   # dedos de garra que sujetan la brasa
        a = math.tau * j / 5
        d.cuerno([(0.17 * math.cos(a), 0.17 * math.sin(a), 2.3), (0.25 * math.cos(a), 0.25 * math.sin(a), 2.5), (0.16 * math.cos(a), 0.16 * math.sin(a), 2.66)], 0.035, "garra", n=4, seg=3)
    d.tubo([(0.07, 0, 1.5), (0.1, 0.02, 1.32)], 0.008, "tendon", n=3)
    d.cono((0.1, 0.02, 1.32), (0.11, 0.02, 1.16), 0.025, "diente", n=4)
    f = M.pieza("llama_neon", tris=520, res=110, k=0.06, ruido=(0.03, 4.0), roblox=dict(material="Neon", color=VERDE, transparencia=0.1))
    f.esfera((0, 0, 2.4), 0.14, "fuego_verde")
    f.tubo([(0, 0, 2.4), (0.04, 0.02, 2.62), (-0.03, 0, 2.84), (0.02, 0, 3.0)], [0.14, 0.13, 0.07, 0.012], "fuego_verde", suave=8)
    f.tubo([(0.06, -0.04, 2.42), (0.12, -0.07, 2.6), (0.09, -0.05, 2.76)], [0.08, 0.06, 0.012], "fuego_verde")
    f.tubo([(-0.06, 0.05, 2.42), (-0.11, 0.08, 2.56), (-0.09, 0.06, 2.68)], [0.07, 0.05, 0.012], "fuego_verde")


@modelo("props", "prop", (2, 2, 2), "Caldero de piedra del chamán, con líquido verde que burbujea.")
def caldero_brujo(M):
    rnd = M.rnd
    p = M.pieza("caldero", tris=1300, res=160, k=0.06, ruido=(0.03, 2.0), suelo=0.0)
    p.torno([(0, 0.3), (0.5, 0.32), (0.86, 0.7), (0.96, 1.15), (0.82, 1.5), (0.88, 1.66), (0.74, 1.66), (0.68, 1.5), (0.8, 1.15), (0.7, 0.75), (0.4, 0.5), (0, 0.48)], (0, 0, 0), "piedra_venas")
    for j in range(3):   # tres patas-garra
        a = math.tau * j / 3 + 0.5
        c, s = math.cos(a), math.sin(a)
        p.tubo([(0.6 * c, 0.6 * s, 0.6), (0.85 * c, 0.85 * s, 0.3), (0.92 * c, 0.92 * s, 0)], [0.16, 0.13, 0.15], "hueso_viejo", k=0.05)
    for j in range(5):   # brasas/piedras debajo
        a = math.tau * j / 5
        p.esfera((0.36 * math.cos(a), 0.36 * math.sin(a), 0.06), 0.15, "piedra")
    d = p.duro
    for s in (-1, 1):   # asas: aros de hueso
        d.toro((s * 0.98, 0, 1.4), 0.17, 0.04, "hueso", eje=(0, 1, 0), n=8, m=4)
    d.tubo([(0.3, -0.2, 1.4), (0.75, -0.5, 1.75), (1.0, -0.66, 1.98)], [0.035, 0.035, 0.045], "hueso", n=5)   # cucharón: un hueso largo
    for j in range(4):   # runas: muescas en relieve alrededor
        a = math.tau * j / 4 + 0.2
        d.cono((0.99 * math.cos(a), 0.99 * math.sin(a), 1.05), (0.99 * math.cos(a + 0.12), 0.99 * math.sin(a + 0.12), 1.32), 0.03, "diente", n=3)
    n = M.pieza("pocion_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    n.duro.torno([(0, 1.2), (0.76, 1.2), (0.72, 1.5), (0.4, 1.54), (0, 1.55)], (0, 0, 0), "acido", n=12)
    for j in range(7):
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.05, 0.55)
        n.duro.esfera((r * math.cos(a), r * math.sin(a), 1.53), rnd.uniform(0.06, 0.15), "acido", sub=1)
    n.duro.tubo([(0.82, 0.3, 1.64), (0.93, 0.34, 1.4), (0.96, 0.36, 1.1)], [0.06, 0.035, 0.05], "acido", n=5)   # chorretón que rebosa


@modelo("props", "prop", (1, 0.3, 1), "Amuleto grande colgante: colmillo con cuerda y gemas.", ancla="techo")
def amuleto_colgante(M):
    p = M.pieza("amuleto", tris=0, angulo=35)
    d = p.duro
    # Cordón en V con cuentas, colmillo central y dos colmillos menores.
    izq = curva([(-0.48, 0, 1.0), (-0.36, 0, 0.72), (-0.15, 0, 0.56), (0, 0, 0.52)], 8)
    d.tubo(izq, 0.022, "cuero", n=5, sim=True)
    for i in (2, 4, 6):
        d.torno([(0.02, -0.035), (0.05, 0), (0.02, 0.035)], izq[i], "hueso", n=6, eje=np.array(izq[i + 1]) - np.array(izq[i - 1]), sim=True)
    d.cuerno([(0, 0, 0.56), (0.05, 0.02, 0.3), (0.0, 0, 0.0)], 0.1, "diente", n=7, seg=6, potencia=0.8)
    d.toro((0, 0, 0.5), 0.085, 0.03, "tendon", eje=(0, 0, 1), n=7, m=3)
    d.cuerno([(0.2, 0, 0.6), (0.26, 0.01, 0.46), (0.22, 0, 0.3)], 0.045, "diente", n=5, seg=3, sim=True)
    g = M.pieza("gemas_neon", tris=0, angulo=25, roblox=dict(material="Neon", color=VIOLETA))
    g.duro.prisma((0, -0.07, 0.3), (0, -0.07, 0.46), 0.045, "cristal", n=6, punta=0.5)
    g.duro.prisma((0, -0.07, 0.38), (0, -0.07, 0.24), 0.045, "cristal", n=6, punta=0.6)
    for s in (-1, 1):
        g.duro.esfera((s * 0.36, 0, 0.72), 0.045, "neon_violeta", sub=1)


@modelo("props", "prop", (4, 0.5, 0.5), "Cadena de eslabones de hueso, para atar o decorar.")
def cadena_hueso(M):
    p = M.pieza("cadena", tris=0)
    d = p.duro
    n = 9
    paso = 3.5 / n
    for i in range(n):
        x = -1.75 + paso * (i + 0.5)
        eje = (0, 1, 0) if i % 2 else (0, 0, 1)
        z = 0.25 + 0.04 * math.sin(i * 1.3)
        d.toro((x, 0, z), 0.19, 0.055, "hueso" if i % 3 else "hueso_viejo", eje=eje, n=8, m=5, esc=(1.25, 0.85, 1) if i % 2 == 0 else (1.25, 1, 0.85))
    # Argolla de un extremo y gancho de garra en el otro.
    d.toro((-1.85, 0, 0.25), 0.2, 0.05, "garra", eje=(0, 1, 0), n=9, m=5)
    d.cuerno([(1.72, 0, 0.25), (1.95, 0, 0.42), (2.0, 0, 0.2), (1.85, 0, 0.05)], 0.07, "garra", n=6, seg=6, potencia=0.6)


@modelo("props", "prop", (2, 2, 6), "Estatua tosca de un ancestro monstruo, tallada en piedra negra, con ojos que brillan.")
def estatua_ancestro(M):
    p = M.pieza("estatua", tris=1650, res=190, k=0.12, ruido=(0.045, 1.4), suelo=0.0)
    p.caja((0, 0, 0.3), (1.9, 1.7, 0.6), "piedra", red=0.12)                # peana
    p.esfera((0, 0.05, 1.6), 1, "obsidiana", esc=(0.75, 0.6, 1.2))           # piernas en bloque (talla tosca)
    p.caja((0, -0.25, 1.0), (0.12, 0.6, 1.2), None, resta=True, k=0.05)       # la raja entre las piernas
    p.esfera((0, 0.05, 3.2), 1, "obsidiana", esc=(0.9, 0.62, 1.0))           # torso encorvado
    p.esfera((0, -0.2, 4.6), 1, "obsidiana", esc=(0.55, 0.55, 0.78))         # cabeza alargada
    p.tubo([(0.8, 0, 3.6), (1.0, -0.15, 2.5), (0.85, -0.35, 1.45)], [0.3, 0.24, 0.26], "obsidiana", sim=True)   # brazos hasta las rodillas
    p.tubo([(-0.3, -0.62, 4.95), (0, -0.74, 4.85), (0.3, -0.62, 4.95)], [0.1, 0.13, 0.1], "obsidiana")        # ceño
    p.esfera((0.2, -0.68, 4.72), 0.11, "negro", sim=True, resta=True, k=0.02)
    p.caja((0, -0.72, 4.1), (0.12, 0.3, 0.72), "negro", resta=True, k=0.03)                                       # boca vertical
    for i in range(5):   # cresta de vértebras en la espalda
        p.esfera((0, 0.6 - 0.02 * i, 2.5 + i * 0.42), 0.17, "obsidiana", k=0.05)
    d = p.duro
    d.cuerno([(0.3, 0, 5.1), (0.6, 0.1, 5.6), (0.42, -0.1, 6.0)], 0.13, "obsidiana", n=5, seg=4, sim=True)
    for s in (-1, 1):
        for k_ in (-1, 0, 1):   # dedos-garra
            d.cuerno([(s * 0.85 + k_ * 0.1, -0.4, 1.4), (s * 0.85 + k_ * 0.14, -0.5, 1.1), (s * 0.85 + k_ * 0.12, -0.42, 0.75)], 0.06, "obsidiana", n=4, seg=2)
    o = M.pieza("ojos_neon", tris=0, roblox=dict(material="Neon", color=VIOLETA))
    o.duro.esfera((0.2, -0.63, 4.72), 0.085, "neon_violeta", sub=1, sim=True)
    o.duro.esfera((0, -0.62, 4.1), 0.07, "neon_violeta", sub=1, esc=(0.6, 0.6, 3.6))


@modelo("props", "prop", (3, 3, 0.1), "Charco de sangre en el suelo, reflectante (con algo de grosor).")
def charco_sangre(M):
    rnd = M.rnd
    p = M.pieza("charco", tris=1500, res=260, k=0.16, suelo=0.0)
    M.mat("sangre_charco", "sangre", rug=0.2, rug_var=0.1, metal=0.0, relieve=0.05)
    # Mancha irregular: lóbulos fundidos, salpicaduras y un reguero.
    for j in range(13):
        a = math.tau * j / 13 + rnd.uniform(-0.2, 0.2)
        r = rnd.uniform(0.35, 0.95)
        p.esfera((r * math.cos(a), r * math.sin(a), 0), rnd.uniform(0.3, 0.55), "sangre_charco", esc=(1, 1, 0.17))
    p.esfera((0, 0, 0), 1, "sangre_charco", esc=(0.95, 0.85, 0.085))
    p.tubo([(0.8, 0.3, 0), (1.1, 0.7, 0), (1.25, 1.2, 0), (1.42, 1.42, 0)], [0.16, 0.11, 0.08, 0.05], "sangre_charco")
    for j in range(9):
        a = rnd.uniform(0, math.tau)
        r = rnd.uniform(1.15, 1.45)
        p.esfera((r * math.cos(a), r * math.sin(a), 0), rnd.uniform(0.06, 0.13), "sangre_charco", esc=(1, 1, 0.5), k=0.0)


@modelo("props", "prop", (2, 2, 1), "Montón de parásitos retorciéndose: una masa de gusanos y larvas.")
def nido_parasitos(M):
    rnd = M.rnd
    M.mat("larva", "carne_palida", a="#C8B090", b="#8A6A5A", rug=0.3, fibras=dict(esc=14.0, fuerza=0.9))
    M.mat("larva_roja", "carne_viva", a="#8A2A3A", b="#4A1220", rug=0.3)
    p = M.pieza("nido", tris=1900, res=180, k=0.035, ruido=(0.008, 5.0), suelo=0.0)
    M.mat("baba_nido", "mucosa", a="#2E5A1E", b="#16301A", emis=(VERDE, 0.04))
    p.esfera((0, 0, 0), 1, "baba_nido", esc=(0.9, 0.9, 0.2), k=0.1)
    for j in range(26):
        a, r = rnd.uniform(0, math.tau), 0.72 * math.sqrt(rnd.random())
        z0 = 0.12 + 0.62 * (1 - r / 0.75) * rnd.uniform(0.3, 1.0)
        pts = []
        an = rnd.uniform(0, math.tau)
        x, y, z = r * math.cos(a), r * math.sin(a), z0
        for i in range(5):
            pts.append((x, y, max(0.07, z)))
            an += rnd.uniform(-1.1, 1.1)
            x += 0.17 * math.cos(an)
            y += 0.17 * math.sin(an)
            z += rnd.uniform(-0.1, 0.12)
        rr = rnd.uniform(0.05, 0.085)
        p.tubo(pts, [rr * 0.7, rr, rr, rr * 0.9, rr * 0.5], "larva" if j % 4 else "larva_roja", suave=8)
    d = p.duro
    for j in range(6):   # cabecitas con mandíbulas asomando
        a, r = rnd.uniform(0, math.tau), rnd.uniform(0.2, 0.7)
        b = np.array([r * math.cos(a), r * math.sin(a), 0.5 - 0.3 * r])
        d.cono(b + [0.03, 0, 0.1], b + [0.06, 0, 0.22], 0.015, "garra", n=3)
        d.cono(b + [-0.03, 0, 0.1], b + [-0.06, 0, 0.22], 0.015, "garra", n=3)
    M.notas["textura_animada"] = "Para que parezca que se retuercen: desplaza despacio el UV (OffsetStudsU/V) o anima un leve cambio de tamaño."


@modelo("props", "prop", (2, 1.5, 1.5), "Cofre hecho con el caparazón de una bestia: se abre como una concha.")
def cofre_organico(M):
    M.mat("concha", "quitina", a="#2A1838", b="#3E2A1E", rug=0.35, relieve=0.6)
    b = M.pieza("base", tris=900, res=140, k=0.05, ruido=(0.02, 2.2), suelo=0.0)
    b.esfera((0, 0, 0.62), 1, "concha", esc=(1.0, 0.72, 0.62), cascara=0.1)
    b.caja((0, 0, 1.2), (2.4, 1.8, 1.0), None, resta=True)                       # se queda la mitad de abajo
    b.torno([(0, 0), (0.5, 0), (0.56, 0.1), (0, 0.14)], (0, 0, 0), "concha", esc=(1.4, 1, 1), k=0.05)
    for i in range(6):   # costillas radiales de la concha
        a = -1.25 + i * 0.5
        b.tubo([(0, 0.6, 0.2), (0.75 * math.sin(a), 0.1 - 0.5 * math.cos(a) * 0.6, 0.1), (1.0 * math.sin(a), -0.72 * math.cos(a), 0.66)], [0.06, 0.07, 0.05], "concha", k=0.03)
    b.torno([(0, 0.5), (0.8, 0.55), (0.8, 0.66), (0, 0.66)], (0, 0, 0), "carne_viva", esc=(1.15, 0.8, 1), k=0.02)   # forro de carne
    for i in range(7):
        a = -1.2 + i * 0.4
        b.duro.cono((0.95 * math.sin(a), -0.68 * math.cos(a), 0.66), (0.98 * math.sin(a), -0.72 * math.cos(a), 0.88), 0.05, "diente", n=4)
    t = M.pieza("tapa", tris=800, res=140, k=0.05, ruido=(0.02, 2.2))
    with t.en((0, 0.7, 0.7), rot=(-52, 0, 0)):   # abierta, girada sobre la bisagra de atrás
        t.esfera((0, -0.7, 0.0), 1, "concha", esc=(1.02, 0.74, 0.66), cascara=0.1)
        t.caja((0, -0.7, -0.52), (2.4, 1.8, 1.0), None, resta=True)
        for i in range(6):
            a = -1.25 + i * 0.5
            t.tubo([(0, -0.1, 0.5), (0.72 * math.sin(a), -0.7 - 0.5 * math.cos(a) * 0.6, 0.62), (1.0 * math.sin(a), -0.7 - 0.72 * math.cos(a), 0.05)], [0.06, 0.07, 0.05], "concha", k=0.03)
        for i in range(6):
            a = -1.0 + i * 0.4
            t.duro.cono((0.95 * math.sin(a), -0.7 - 0.68 * math.cos(a), 0.02), (0.98 * math.sin(a), -0.7 - 0.72 * math.cos(a), -0.2), 0.05, "diente", n=4)
        t.duro.cuerno([(0, -0.5, 0.64), (0, -0.2, 0.95), (0, 0.2, 0.9)], 0.09, "garra", n=5, seg=3)
    b.tubo([(-0.5, 0.7, 0.68), (0.5, 0.7, 0.68)], 0.07, "tendon", k=0.02)    # bisagra de tendón
    M.articulacion("tapa", "base", (0, 0.7, 0.68))
    g = M.pieza("tesoro_neon", tris=0, angulo=25, roblox=dict(material="Neon", color=VIOLETA))
    for (x, y, L) in ((-0.3, 0.0, 0.42), (0.1, -0.15, 0.56), (0.42, 0.1, 0.36), (-0.05, 0.2, 0.3)):
        g.duro.prisma((x, y, 0.6), (x * 1.2, y * 1.2, 0.6 + L), 0.09, "cristal", n=5, punta=0.4)
    M.notas["animacion"] = "La tapa gira sobre la bisagra trasera (articulación «tapa»); está modelada abierta 52°."


@modelo("props", "prop", (1.5, 1.5, 2), "Contenedor de ácido: una vaina orgánica con el líquido verde dentro.")
def barril_acido(M):
    M.mat("vaina", "piel", a="#2E3A26", b="#1A1622", rug=0.55)
    p = M.pieza("vaina", tris=1350, res=160, k=0.06, ruido=(0.02, 2.2), suelo=0.0)
    perfil = [(0, 0.05), (0.45, 0.1), (0.72, 0.6), (0.74, 1.15), (0.55, 1.62), (0.36, 1.78), (0.3, 1.9), (0.2, 1.9), (0.2, 1.7), (0, 1.6)]
    p.torno(perfil, (0, 0, 0), "vaina")
    p.torno([(0, 0.3), (0.6, 0.62), (0.62, 1.15), (0.42, 1.6), (0, 1.75)], (0, 0, 0), None, resta=True, k=0.03)   # hueca
    for j in range(4):   # ventanas alargadas entre las costillas, por donde se ve el ácido
        a = math.tau * j / 4 + 0.4
        p.esfera((0.72 * math.cos(a), 0.72 * math.sin(a), 0.92), 1, None, esc=(0.25, 0.25, 0.5), rot=(0, 0, math.degrees(a)), resta=True, k=0.04)
        a2 = a + math.tau / 8
        p.tubo([(0.3 * math.cos(a2), 0.3 * math.sin(a2), 0.05), (0.76 * math.cos(a2), 0.76 * math.sin(a2), 0.62), (0.77 * math.cos(a2), 0.77 * math.sin(a2), 1.2), (0.36 * math.cos(a2), 0.36 * math.sin(a2), 1.82)],
               [0.09, 0.1, 0.09, 0.07], "raiz", suave=8, k=0.04)
    p.toro((0, 0, 1.88), 0.26, 0.065, "raiz", k=0.03)
    for j in range(4):
        a = math.tau * j / 4
        p.tubo([(0.4 * math.cos(a), 0.4 * math.sin(a), 0.15), (0.7 * math.cos(a), 0.7 * math.sin(a), 0.0)], [0.1, 0.06], "raiz", k=0.04)
    n = M.pieza("acido_neon", tris=0, roblox=dict(material="Neon", color=VERDE))
    n.duro.torno([(0, 0.34), (0.56, 0.64), (0.6, 1.12), (0.42, 1.52), (0, 1.62)], (0, 0, 0), "acido", n=10)
    n.duro.esfera((0, 0, 1.86), 0.19, "acido", sub=1, esc=(1, 1, 0.5))
    n.duro.tubo([(0.24, 0.05, 1.9), (0.42, 0.1, 1.6), (0.62, 0.14, 1.3)], [0.05, 0.03, 0.045], "acido", n=4)


@modelo("props", "prop", (2, 2, 3), "Campana de resonancia hecha con un cráneo, para dar la alerta.")
def campana_resonancia(M):
    rnd = M.rnd
    p = M.pieza("soporte", tris=800, res=170, k=0.05, ruido=(0.02, 2.2), suelo=0.0)
    for s in (-1, 1):
        p.tubo([(s * 0.9, 0, 0), (s * 0.85, 0.02, 1.6), (s * 0.6, 0, 2.7), (0, 0, 2.95)], [0.14, 0.11, 0.09, 0.09], "hueso_viejo", suave=10)
        p.esfera((s * 0.9, 0, 0), 0.26, "piedra", esc=(1, 1.3, 0.5))
        p.tubo([(s * 0.88, 0.92, 0), (s * 0.86, 0.02, 1.1)], [0.09, 0.07], "hueso_viejo", k=0.03)
        p.tubo([(s * 0.88, -0.92, 0), (s * 0.86, 0.02, 1.1)], [0.09, 0.07], "hueso_viejo", k=0.03)
    p.duro.cuerno([(0, 0, 2.95), (0.1, 0, 3.2), (-0.05, 0, 3.4)], 0.07, "garra", n=5, seg=3)
    p.duro.tubo([(0, 0, 2.9), (0, 0, 2.55)], 0.025, "tendon", n=4)
    c = M.pieza("campana", tris=900, res=150, k=0.06, ruido=(0.015, 2.5))
    # Calota de cráneo boca abajo, hueca, con las cuencas mirando al frente.
    c.esfera((0, 0, 2.0), 1, "hueso", esc=(0.62, 0.7, 0.62), cascara=0.07)
    c.caja((0, 0, 1.25), (1.6, 1.8, 0.85), None, resta=True)
    c.toro((0, 0, 1.66), 0.6, 0.06, "hueso_viejo", esc=(1, 1.12, 1), k=0.03)
    c.esfera((0.22, -0.62, 2.0), 0.15, "negro", sim=True, resta=True, k=0.02)
    c.tubo([(-0.4, -0.5, 2.2), (0, -0.7, 2.14), (0.4, -0.5, 2.2)], [0.06, 0.08, 0.06], "hueso", k=0.03)
    c.esfera((0, 0, 2.6), 0.1, "hueso", k=0.05)
    for i in range(5):
        a = -0.8 + i * 0.4
        c.duro.cono((0.58 * math.sin(a), -0.66 * math.cos(a), 1.66), (0.6 * math.sin(a), -0.68 * math.cos(a), 1.46), 0.045, "diente", n=4)
    M.articulacion("campana", "soporte", (0, 0, 2.6))
    b = M.pieza("badajo", tris=0)
    b.duro.tubo([(0, 0, 2.5), (0, 0, 1.55)], 0.02, "tendon", n=4)
    b.duro.torno([(0, -0.15), (0.1, -0.1), (0.12, 0.02), (0.06, 0.1), (0, 0.12)], (0, 0, 1.45), "hueso_viejo", n=7)
    b.duro.tubo([(0, 0, 1.3), (0, 0, 0.9)], 0.015, "cuero", n=3)      # tirador
    b.duro.cono((0, 0, 0.9), (0, 0, 0.7), 0.04, "diente", n=4)
    M.articulacion("badajo", "campana", (0, 0, 2.5))
    M.notas["animacion"] = "La campana y el badajo se balancean desde arriba (articulaciones «campana» y «badajo»)."
