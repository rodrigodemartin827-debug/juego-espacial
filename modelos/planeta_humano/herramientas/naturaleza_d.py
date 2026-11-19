"""Zona naturaleza (4): placa de césped alienígena y nenúfar espacial."""

import math
import random

from ph import NEON, V, Modelo

ZONA = "naturaleza"


# ==============================================================================================================
def cesped_alien():
    m = Modelo("cesped_alien", ZONA, (8, 8, 0.3), 3000,
               "Placa modular de césped alienígena (8 x 8): tierra con mechones de hierba volumétrica verde azulada, "
               "algunos con puntas luminosas cyan, y flores diminutas intercaladas. Encaja sin costuras con sus "
               "vecinas.")
    c = m.parte()
    puntas = m.parte("puntas_neon", tipo="neon", color=NEON, transparencia=0.2)
    rnd = random.Random(83)
    tierra = m.mat("piedra", "#3E5A3A", bump=0.5, escala=2.0, suciedad=0.2)
    hierba = [m.mat("organico", h, rug=0.75) for h in ("#3E8A6A", "#4E9A6E", "#2E7A62")]
    flores = [m.mat("organico", h, rug=0.4) for h in ("#E8D24A", "#E86A9A", "#F0F0F0", "#9A7AE8")]
    S = 8.0
    # placa de tierra: los bordes son rectos y a la misma altura para que las placas casen
    c.caja((0, 0, 0.04), (S, S, 0.08), tierra, 0.0)
    # mechones repartidos en rejilla con azar (dejando 0,15 de margen para no pisar la placa vecina)
    n = 8
    k = 0
    for i in range(n):
        for j in range(n):
            x = -S / 2 + (i + 0.5) * S / n + rnd.uniform(-0.3, 0.3)
            y = -S / 2 + (j + 0.5) * S / n + rnd.uniform(-0.3, 0.3)
            x = max(-S / 2 + 0.2, min(S / 2 - 0.2, x))
            y = max(-S / 2 + 0.2, min(S / 2 - 0.2, y))
            p = V((x, y, 0.08))
            hojas = 4
            mat = hierba[(i + j) % 3]
            luminoso = rnd.random() < 0.14
            for h in range(hojas):
                a = h * math.tau / hojas + rnd.uniform(-0.4, 0.4)
                alto = rnd.uniform(0.14, 0.22)
                inc = rnd.uniform(0.25, 0.6)
                tip = p + V((math.cos(a) * alto * inc, math.sin(a) * alto * inc, alto))
                c.cil(p, tip, 0.025, mat, n=3, r1=0.0, giro=a)
                if luminoso and h % 2 == 0:
                    puntas.cil(tip - (tip - p) * 0.25, tip + (tip - p).normalized() * 0.02, 0.012, None, n=3, r1=0.0)
            k += 1
    # flores diminutas entre la hierba
    for f in range(16):
        x = rnd.uniform(-S / 2 + 0.25, S / 2 - 0.25)
        y = rnd.uniform(-S / 2 + 0.25, S / 2 - 0.25)
        c.cil((x, y, 0.08), (x, y, 0.2), 0.008, hierba[0], n=3)
        c.ico((x, y, 0.21), 0.025, flores[f % 4], sub=1, esc=(1, 1, 0.6))
    m.notas.append("Placa de 8 x 8 studs exactos, la tierra a ras en los cuatro bordes: se coloca en rejilla de 8.")
    m.terminar()


# ==============================================================================================================
def nenufar_espacial():
    m = Modelo("nenufar_espacial", ZONA, (2, 2, 0.3), 1000,
               "Nenúfar flotante: hoja circular con el borde ondulado y la ranura típica, flor central de 3 pétalos "
               "con brillo cyan suave, raíz colgando bajo la hoja y tres gotas de agua sobre ella.")
    c = m.parte()
    flor = m.parte("flor_neon", tipo="neon", color=NEON, transparencia=0.35, nota="Pétalos: Neon cyan suave.")
    gotas = m.parte("gotas_cristal", tipo="cristal", color="#DDF6FA", transparencia=0.5)
    hoja = m.mat("organico", "#3E7A44", rug=0.35, bump=0.4)
    raiz = m.mat("organico", "#8A9A6A", rug=0.7)
    centro = m.mat("organico", "#E8D86A", rug=0.5)
    R = 0.95
    ranura = 0.22  # ancho angular de la ranura (radianes)
    # hoja: corona circular abierta en la ranura, borde ondulado y algo levantado
    c.lamina(lambda u, v: (math.cos(ranura / 2 + u * (math.tau - ranura)) * (0.05 + v * R),
                           math.sin(ranura / 2 + u * (math.tau - ranura)) * (0.05 + v * R),
                           0.06 + 0.035 * v ** 3 * math.sin(u * math.tau * 7) + 0.03 * v ** 4), 20, 3, 0.025, hoja)
    # nervios en relieve
    for k in range(7):
        a = ranura / 2 + (k + 0.5) * (math.tau - ranura) / 7
        c.cil((math.cos(a) * 0.08, math.sin(a) * 0.08, 0.08), (math.cos(a) * 0.8, math.sin(a) * 0.8, 0.085), 0.012, hoja,
              n=3)
    # flor: base, 3 pétalos abiertos luminosos y el centro
    c.cil((0, 0, 0.06), (0, 0, 0.14), 0.07, hoja, n=8, r1=0.05)
    for k in range(3):
        a = k * math.tau / 3 + 0.3
        d = V((math.cos(a), math.sin(a), 0))
        lado = V((-d.y, d.x, 0))
        flor.lamina(lambda u, v, d=d, lado=lado: V((0, 0, 0.14)) + d * (0.02 + u * 0.24) +
                    lado * (v - 0.5) * 0.16 * math.sin(math.pi * u) + V((0, 0, 0.12 * u - 0.05 * u * u)), 3, 2, 0.015,
                    None)
    c.ico((0, 0, 0.17), 0.045, centro, sub=2, esc=(1, 1, 0.7))
    # raíz: hilo que cuelga bajo la hoja (va bajo el agua)
    c.tubo([(0, 0, 0.04), (0.03, 0.02, -0.25), (-0.02, 0.05, -0.55), (0.04, 0.0, -0.85)], 0.015, raiz, n=4, seg=2,
           r_fin=0.006)
    # gotas de agua aplanadas sobre la hoja
    for (x, y, r) in ((0.45, 0.2, 0.06), (-0.35, 0.4, 0.045), (0.1, -0.55, 0.05)):
        gotas.esfera((x, y, 0.1), r, None, seg=8, anillos=5, esc=(1, 1, 0.5))
    m.notas.append("El origen está a nivel del agua: la hoja flota y la raíz cuelga 0,85 studs bajo la superficie.")
    m.terminar()


MODELOS = {
    "cesped_alien": cesped_alien,
    "nenufar_espacial": nenufar_espacial,
}
