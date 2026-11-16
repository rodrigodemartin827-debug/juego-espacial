"""
Defensas y escudos, cabinas y utilidades.

Entradas:
  blindaje            cara interior (normal -X), CASCO_LATERAL: simétrico delante/detrás, sirve en los dos lados
  generador de escudo abajo (normal -Z), CASCO_SUPERIOR
  contramedidas       abajo, UNIVERSAL
  cabinas             abajo, CASCO_SUPERIOR (en `anclajes_vfx` va el asiento del piloto)
  tren de aterrizaje  arriba (normal +Z), CASCO_INFERIOR
  estabilizadores     abajo, CASCO_SUPERIOR
  tanques             arriba, ALA_PUNTA (cabe también en CASCO_INFERIOR)
  radar               abajo, UNIVERSAL
  bahía de carga      arriba, CASCO_INFERIOR (y una salida CASCO_INFERIOR debajo para el tren)
"""

import math

from .geo import V, Matrix
from .armas import boca


def _color(con, p):
    con.colores_extra.update(p.get("color", {}))
    if "paleta" in p:
        con.info["paleta"] = p["paleta"]


def _ancla(con, nombre, pos, d=(0, -1, 0)):
    boca(con, nombre, pos, d)


# ==============================================================================================================
# Defensas
# ==============================================================================================================

def blindaje(con, p):
    _color(con, p)
    L, H, G = p.get("largo", 3.2), p.get("alto", 2.4), p.get("grosor", 0.45)
    estilo = p.get("estilo", "placa")
    con.acople("acople_montaje", (0, 0, 0), (-1, 0, 0), "CASCO_LATERAL", "entrada",
               acepta=["CASCO_LATERAL", "UNIVERSAL"])
    x0 = 0.14
    # placa con chaflanes (simétrica delante/detrás)
    ch = min(0.5, L * 0.15)
    perfil = [(-L / 2 + ch, -H / 2), (L / 2 - ch, -H / 2), (L / 2, -H / 2 + ch), (L / 2, H / 2 - ch),
              (L / 2 - ch, H / 2), (-L / 2 + ch, H / 2), (-L / 2, H / 2 - ch), (-L / 2, -H / 2 + ch)]
    con.prisma(perfil, (x0, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), G, "primario", centrado=False)
    xs = x0 + G
    if estilo == "placa":
        con.pernos((xs, 0, 0), (1, 0, 0), (0, 1, 0), 1.0, radio=0.1, alto=0.07, ranura="metal")
        con.pernos((xs, 0, 0), (1, 0, 0), (0, 1, 0), 0.55, radio=0.08, alto=0.06, ranura="metal")
        con.caja((xs + 0.03, 0, -H / 2 + 0.35), (0.06, L * 0.8, 0.12), "aviso", bisel=False)
    elif estilo == "gruesa":
        p2 = [(x * 0.82, z * 0.8) for x, z in perfil]
        con.prisma(p2, (xs, 0, 0), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.3, "primario", centrado=False)
        con.caja((xs + 0.32, 0, 0), (0.06, L * 0.7, 0.35), "secundario", bisel=False)
        con.pernos((xs + 0.3, 0, 0), (1, 0, 0), (0, 1, 0), 0.9, radio=0.1, alto=0.07, ranura="metal")
    elif estilo == "reactivo":
        nf, nc = 3, 4
        for i in range(nc):
            for j in range(nf):
                y = (i - (nc - 1) / 2) * (L / nc)
                z = (j - (nf - 1) / 2) * (H / nf)
                con.caja((xs + 0.14, y, z), (0.28, L / nc - 0.1, H / nf - 0.1), "secundario")
                con.caja((xs + 0.29, y + L / nc * 0.3, z + H / nf * 0.3), (0.03, 0.12, 0.12), "neon", bisel=False)
                con.caja((xs + 0.29, y - L / nc * 0.15, z), (0.03, L / nc * 0.4, 0.05), "aviso", bisel=False)
    elif estilo == "energetico":
        for s in (-1, 1):
            con.cilindro((xs, s * (L / 2 - 0.35), 0), (1, 0, 0), 0.22, 0.35, "secundario", lados=10)
            con.esfera((xs + 0.42, s * (L / 2 - 0.35), 0), 0.15, "neon", lados=10, anillos=5)
        con.tira([V((xs + 0.02, -L / 2 + 0.6, 0)), V((xs + 0.02, L / 2 - 0.6, 0))], [V((1, 0, 0))] * 2, 0.08,
                 "neon2", alto=0.03)
        con.tira([V((xs + 0.02, 0, -H / 2 + 0.3)), V((xs + 0.02, 0, H / 2 - 0.3))], [V((1, 0, 0))] * 2, 0.12,
                 "secundario", alto=0.04)
        # campo de fuerza curvado delante de la placa
        filas = []
        for k in range(7):
            u = k / 6 - 0.5
            y = u * L * 1.05
            x = xs + 0.55 - 0.35 * (2 * u) ** 2
            filas.append([V((x, y, -H * 0.55)), V((x, y, H * 0.55)), V((x + 0.02, y, H * 0.55)),
                          V((x + 0.02, y, -H * 0.55))])
        con.loft(filas, "domo")


def escudo(con, p):
    _color(con, p)
    R = p.get("radio_domo", 3.0)
    estilo = p.get("estilo", "parcial")
    con.acople("acople_montaje", (0, 0, 0), (0, 0, -1), "CASCO_SUPERIOR", "entrada",
               acepta=["CASCO_SUPERIOR", "UNIVERSAL"])
    if estilo == "alien":
        con.revolucion((0, 0, 0.14), (0, 0, 1), [(0, 0), (0, 1.2), (0.3, 1.0), (0.8, 0.6), (1.0, 0)], "organico",
                       lados=16)
        for k in range(5):
            a = math.tau * k / 5
            d = V((math.cos(a) * 0.45, math.sin(a) * 0.45, 1)).normalized()
            con.cilindro(V((math.cos(a) * 0.4, math.sin(a) * 0.4, 0.6)), d, 0.2, 1.4 + 0.3 * (k % 2), "cristal",
                         lados=6, radio2=0.0)
        con.esfera((0, 0, 1.4), 0.4, "neon", lados=12, anillos=6)
    else:
        con.revolucion((0, 0, 0.14), (0, 0, 1), [(0, 0), (0, 1.0), (0.3, 0.95), (0.4, 0.6), (1.1, 0.45),
                                                 (1.2, 0)], "primario", lados=18)
        con.toro((0, 0, 0.32), (0, 0, 1), 0.98, 0.06, "secundario", n1=20, n2=5)
        for k in range(4):
            a = math.tau * k / 4 + math.pi / 4
            con.caja((math.cos(a) * 0.8, math.sin(a) * 0.8, 0.5), (0.25, 0.25, 0.5), "oscuro",
                     giro=Matrix.Rotation(a, 3, "Z"))
        con.esfera((0, 0, 1.45), 0.35, "neon", lados=12, anillos=6)
        con.toro((0, 0, 1.15), (0, 0, 1), 0.5, 0.05, "neon", n1=16, n2=4)
    if estilo == "parcial":
        # domo parcial: un casquete delante
        filas = []
        for i in range(6):
            el = math.pi / 2 * i / 5
            fila = []
            for j in range(9):
                az = -math.pi * 0.35 + math.pi * 0.7 * j / 8
                fila.append(V((math.sin(az) * math.cos(el) * R, -math.cos(az) * math.cos(el) * R, 0.4 + math.sin(el) * R)))
            filas.append(fila)
        con.loft(filas, "domo", tapa_ini=False, tapa_fin=False, cerrado=False)
    else:
        con.domo((0, 0, 0.3), R, "domo", lados=24, anillos=7)
        if estilo == "doble":
            con.domo((0, 0, 0.3), R * 0.82, "domo", lados=20, anillos=6)
            con.toro((0, 0, 0.32), (0, 0, 1), R, 0.07, "neon", n1=32, n2=4)
            con.toro((0, 0, 0.32), (0, 0, 1), R * 0.82, 0.05, "neon", n1=28, n2=4)
            for k in range(3):
                a = math.tau * k / 3
                con.cilindro((math.cos(a) * 0.9, math.sin(a) * 0.9, 0.3), (0, 0, 1), 0.12, 1.3, "secundario", lados=8)
                con.esfera((math.cos(a) * 0.9, math.sin(a) * 0.9, 1.65), 0.16, "neon", lados=8, anillos=4)
    con.info["json_domo"] = {"radio": R, "material": "ForceField", "nota": "la malla _domo es el escudo encendido"}


def contramedidas(con, p):
    _color(con, p)
    estilo = p.get("estilo", "chaff")
    con.acople("acople_montaje", (0, 0, 0), (0, 0, -1), "UNIVERSAL", "entrada",
               acepta=list(k for k in ("CASCO_SUPERIOR", "CASCO_INFERIOR", "CASCO_LATERAL", "ALA_PUNTA", "UNIVERSAL",
                                       "CASCO_FRONTAL", "CASCO_TRASERO", "ALA_MOTOR")))
    if estilo == "chaff":
        con.caja((0, 0, 0.45), (1.6, 1.4, 0.6), "primario")
        con.caja((0, 0, 0.8), (1.4, 1.2, 0.1), "secundario")
        # tubos inclinados hacia atrás y arriba
        for i in range(3):
            for j in range(2):
                x = (i - 1) * 0.42
                y = (j - 0.5) * 0.45
                d = V((x * 0.6, 0.6, 1)).normalized()
                con.tubo(V((x, y, 0.75)), d, 0.17, 0.12, 0.6, "oscuro", lados=8)
                _ancla(con, f"lanzador_{i * 2 + j + 1}", V((x, y, 0.75)) + d * 0.6, d)
        con.caja((0.82, 0, 0.45), (0.04, 0.9, 0.2), "aviso", bisel=False)
    else:
        con.revolucion((0, 0, 0.14), (0, 0, 1), [(0, 0), (0, 0.7), (0.5, 0.6), (0.6, 0)], "primario", lados=12)
        con.cilindro((0, 0, 0.6), (0, 0, 1), 0.12, 2.6, "secundario", lados=8)
        for k, h in enumerate((1.2, 1.8, 2.4)):
            for s in (-1, 1):
                con.cilindro((0, 0, 0.6 + h), (s, 0, 0.15), 0.04, 0.7 - k * 0.15, "metal", lados=6, bisel=False)
            con.toro((0, 0, 0.6 + h), (0, 0, 1), 0.2, 0.04, "neon", n1=12, n2=4)
        con.esfera((0, 0, 3.3), 0.18, "neon2", lados=10, anillos=5)
        # plato emisor
        con.revolucion((0, -0.2, 1.0), (0, -1, 0.3), [(0, 0.12), (0.25, 0.7), (0.3, 0.72), (0.12, 0.12)], "secundario",
                       lados=16)
        con.cilindro((0, -0.2, 1.0), (0, -1, 0.3), 0.08, 0.55, "neon", lados=8)


# ==============================================================================================================
# Cabinas
# ==============================================================================================================

def asiento(con, pos, ancho=1.1, ranura="asiento"):
    x, y, z = pos
    con.caja((x, y, z + 0.2), (ancho, 1.0, 0.3), ranura)
    con.caja((x, y + 0.5, z + 0.95), (ancho, 0.25, 1.4), ranura, giro=Matrix.Rotation(-0.2, 3, "X"))
    con.caja((x, y + 0.62, z + 1.75), (ancho * 0.6, 0.25, 0.4), ranura)
    con.caja((x, y, z), (ancho * 0.7, 0.8, 0.2), "oscuro")
    for s in (-1, 1):
        con.caja((x + s * (ancho / 2 + 0.08), y + 0.05, z + 0.5), (0.12, 0.9, 0.12), "oscuro")
    _ancla(con, f"asiento_{len([v for v in con.info.get('vfx', []) if v['nombre'].startswith('asiento')]) + 1}",
           (x, y, z + 0.35), (0, -1, 0))


def consola(con, x, y, z, ancho=1.2, ang=0.6):
    giro = Matrix.Rotation(ang, 3, "X")
    con.caja((x, y, z), (ancho, 0.5, 0.6), "oscuro")
    con.caja((x, y - 0.05, z + 0.38), (ancho * 0.92, 0.5, 0.06), "pantalla", giro=giro)


def cabina(con, p):
    _color(con, p)
    estilo = p["estilo"]
    con.acople("acople_montaje", (0, 0, 0), (0, 0, -1), "CASCO_SUPERIOR", "entrada", acepta=["CASCO_SUPERIOR"])
    W, L = p.get("ancho", 2.4), p.get("largo", 4.0)
    z0 = 0.14
    # bañera (base) con faldón
    base_alto = p.get("base", 0.6)
    perfil = [(-W / 2, z0), (W / 2, z0), (W / 2 + 0.1, z0 + base_alto), (-W / 2 - 0.1, z0 + base_alto)]
    if estilo not in ("alien",):
        con.cuña(perfil, -L / 2, L / 2, "primario")
        con.caja((0, 0, z0 + base_alto + 0.02), (W + 0.2, L, 0.06), "secundario")
    zb = z0 + base_alto
    if estilo == "abierta":
        asiento(con, (0, 0.4, zb))
        consola(con, 0, -0.8, zb + 0.3, ancho=1.0)
        con.cilindro((0, -0.3, zb), (0, 0, 1), 0.05, 0.7, "metal", lados=6)
        con.esfera((0, -0.3, zb + 0.72), 0.09, "goma", lados=8, anillos=4)
        # parabrisas simple
        con.prisma([(-0.9, 0), (0.9, 0), (0.7, 0.8), (-0.7, 0.8)], (0, -1.3, zb + 0.6), (1, 0, 0),
                   V((0, -0.35, 1)).normalized(), V((0, 1, 0.35)).normalized(), 0.05, "cristal")
        con.caja((0, -1.3, zb + 0.6), (2.0, 0.12, 0.12), "oscuro")
        # arco antivuelco
        for s in (-1, 1):
            con.cilindro((s * 0.75, 1.2, zb), (0, 0, 1), 0.07, 1.6, "metal", lados=6)
        con.cilindro((-0.75, 1.2, zb + 1.6), (1, 0, 0), 0.07, 1.5, "metal", lados=6)
        con.caja((0, 1.5, zb - 0.1), (0.8, 0.5, 0.4), "secundario")
        return
    if estilo in ("cerrada", "caza", "caza_hud", "caza_elite", "transporte"):
        n_as = 2 if estilo == "transporte" else 1
        for k in range(n_as):
            x = 0 if n_as == 1 else (k - 0.5) * 1.2
            asiento(con, (x, 0.35, zb - 0.3), ancho=1.0)
            consola(con, x, -0.95, zb + 0.15, ancho=1.0)
        alto = p.get("alto", 1.6)
        if estilo == "caza_elite":
            # cúpula facetada de cristal oscuro con marco dorado
            secs = []
            for k, (y, w, h) in enumerate(((-L / 2 - 0.3, 0.2, 0.1), (-L / 2 + 0.6, W * 0.75, alto * 0.7),
                                           (0.2, W * 0.95, alto), (L / 2 - 0.3, W * 0.8, alto * 0.75),
                                           (L / 2, W * 0.6, alto * 0.4))):
                secs.append([V((-w / 2, y, zb)), V((w / 2, y, zb)), V((w * 0.35, y, zb + h)), V((-w * 0.35, y, zb + h))])
            con.loft(secs, "cristal")
            for k in range(1, 4):
                q = secs[k]
                con.tira([q[0] + V((0, 0, 0.0)), q[3], q[2], q[1]], [V((0, -0.2, 1))] * 4, 0.1, "secundario",
                         alto=0.06)
            con.tira([secs[0][3], secs[2][3], secs[4][3]], [V((0, 0, 1))] * 3, 0.08, "secundario", alto=0.05)
            con.tira([secs[0][2], secs[2][2], secs[4][2]], [V((0, 0, 1))] * 3, 0.08, "secundario", alto=0.05)
        elif estilo == "transporte":
            # morro acristalado de varias lunas
            secs = []
            for y, w, h in ((-L / 2, W * 0.9, alto * 0.6), (-L / 2 + 0.9, W, alto), (L / 2, W, alto)):
                secs.append([V((-w / 2, y, zb)), V((w / 2, y, zb)), V((w / 2 * 0.9, y, zb + h)),
                             V((-w / 2 * 0.9, y, zb + h))])
            con.loft(secs[:2], "cristal")
            con.loft(secs[1:], "primario")
            for k in range(-2, 3):
                x = k * W / 5
                con.tira([V((x, -L / 2, zb + 0.02)), V((x * 1.05, -L / 2 + 0.9, zb + alto))], [V((0, -1, 0.4))] * 2,
                         0.08, "secundario", alto=0.05)
            con.caja((0, -L / 2 + 0.45, zb + alto * 0.8 + 0.02), (W, 0.95, 0.1), "secundario")
            con.rejilla((0, L / 4, zb + alto + 0.02), (0, 0, 1), (1, 0, 0), W * 0.5, 0.8, "oscuro", "metal", lamas=4)
        else:
            # burbuja: semielipsoide
            burbuja = con.esfera((0, 0, zb), 1.0, "cristal", lados=20, anillos=10, escala=(W * 0.48, L * 0.5, alto))
            # quitar la mitad de abajo: se aplasta contra la base
            for f in burbuja:
                for v in f.verts:
                    if v.co.z < zb:
                        v.co.z = zb
            marco = "secundario" if estilo != "cerrada" else "oscuro"
            for t in (-0.25, 0.2):
                pts, nrm = [], []
                for k in range(13):
                    a = math.pi * k / 12
                    x = math.cos(a) * W * 0.48
                    z = zb + math.sin(a) * alto * math.sqrt(max(0.0, 1 - (t * 2) ** 2))
                    xx = x * math.sqrt(max(0.0, 1 - (t * 2) ** 2))
                    pts.append(V((xx, t * L, z)))
                    nrm.append(V((xx, 0, z - zb)).normalized() if (xx or z - zb) else V((0, 0, 1)))
                con.tira(pts, nrm, 0.12, marco, alto=0.06)
            pts = [V((0, L * 0.5 * math.cos(a), zb + alto * math.sin(a))) for a in
                   (math.pi * k / 12 for k in range(13))]
            con.tira(pts, [V((0, (q.y) / (L * 0.5), (q.z - zb) / alto)).normalized() for q in pts], 0.1, marco,
                     alto=0.05)
            if estilo == "caza_hud":
                # HUD holográfico flotando delante del piloto
                con.prisma([(-0.45, 0), (0.45, 0), (0.45, 0.4), (-0.45, 0.4)], (0, -0.45, zb + 0.75), (1, 0, 0),
                           V((0, -0.3, 1)).normalized(), V((0, 1, 0.3)).normalized(), 0.02, "neon", bisel=False)
                con.tira([V((-W * 0.46, -L * 0.3, zb + 0.03)), V((-W * 0.3, L * 0.35, zb + 0.03))], [V((0, 0, 1))] * 2,
                         0.06, "neon", alto=0.03)
                con.tira([V((W * 0.46, -L * 0.3, zb + 0.03)), V((W * 0.3, L * 0.35, zb + 0.03))], [V((0, 0, 1))] * 2,
                         0.06, "neon", alto=0.03)
        if estilo == "caza" and con.tier == 2:
            con.caja((0, L / 2 - 0.1, zb + 0.35), (W * 0.6, 0.5, 0.7), "secundario")
        return
    if estilo in ("puente", "puente_elite"):
        alto = p.get("alto", 2.2)
        elite = estilo == "puente_elite"
        # casamata con ventanal corrido
        perfil_b = [(-W / 2, zb), (W / 2, zb), (W / 2 * 0.92, zb + alto * 0.45), (-W / 2 * 0.92, zb + alto * 0.45)]
        con.cuña(perfil_b, -L / 2 + 0.6, L / 2, "primario")
        ventana = [V((-W / 2 * 0.92, -L / 2 + 0.6, zb + alto * 0.45)), V((W / 2 * 0.92, -L / 2 + 0.6, zb + alto * 0.45)),
                   V((W / 2 * 0.8, -L / 2 + 1.1, zb + alto)), V((-W / 2 * 0.8, -L / 2 + 1.1, zb + alto))]
        trasera = [V((q.x, L / 2, q.z)) for q in ventana]
        frente = [V((q.x * 1.0, -L / 2 + 0.3, zb + alto * 0.45)) for q in ventana]
        con.loft([[V((-W / 2 * 0.92, -L / 2 + 0.6, zb + alto * 0.45)), V((W / 2 * 0.92, -L / 2 + 0.6, zb + alto * 0.45)),
                   V((W / 2 * 0.92, L / 2, zb + alto * 0.45)), V((-W / 2 * 0.92, L / 2, zb + alto * 0.45))],
                  [V((-W / 2 * 0.8, -L / 2 + 1.1, zb + alto)), V((W / 2 * 0.8, -L / 2 + 1.1, zb + alto)),
                   V((W / 2 * 0.8, L / 2, zb + alto)), V((-W / 2 * 0.8, L / 2, zb + alto))]], "cristal")
        con.caja((0, 0.25, zb + alto + 0.08), (W * 0.85, L - 1.0, 0.2), "secundario")
        for k in range(-3, 4):
            x = k * W / 7.5
            con.tira([V((x, -L / 2 + 0.6, zb + alto * 0.45)), V((x * 0.87, -L / 2 + 1.1, zb + alto))],
                     [V((0, -1, 0.5))] * 2, 0.1, "secundario" if elite else "oscuro", alto=0.05)
        for k, x in enumerate((-W * 0.3, 0, W * 0.3)):
            asiento(con, (x, 0.3, zb), ancho=0.9)
            consola(con, x, -0.9, zb + 0.45, ancho=0.9)
        con.caja((0, L / 2 - 0.4, zb + 0.9), (W * 0.8, 0.3, 1.2), "pantalla")
        if elite:
            # mesa de hologramas
            con.cilindro((0, 1.0, zb), (0, 0, 1), 0.5, 0.7, "secundario", lados=12)
            con.esfera((0, 1.0, zb + 1.2), 0.4, "neon2", lados=12, anillos=6)
            con.toro((0, 1.0, zb + 1.2), (0, 0, 1), 0.6, 0.03, "neon", n1=16, n2=4)
            con.toro((0, 1.0, zb + 1.2), (1, 0, 0.3), 0.55, 0.03, "neon", n1=16, n2=4)
            con.tira([V((-W / 2, -L / 2 + 0.4, zb + 0.05)), V((W / 2, -L / 2 + 0.4, zb + 0.05))], [V((0, -1, 0))] * 2,
                     0.1, "neon", alto=0.03)
        else:
            con.cilindro((W * 0.3, L / 2 - 0.6, zb + alto + 0.15), (0, 0, 1), 0.05, 1.0, "metal", lados=6)
            con.esfera((W * 0.3, L / 2 - 0.6, zb + alto + 1.15), 0.09, "neon", lados=8, anillos=4)
        return
    if estilo == "alien":
        # vaina orgánica: base carnosa, cúpula de cristal púrpura y un asiento vivo
        con.revolucion((0, 0, z0), (0, 0, 1), [(0, 0), (0, W * 0.55), (0.3, W * 0.6), (0.6, W * 0.52), (0.62, 0)],
                       "organico", lados=20)
        burbuja = con.esfera((0, 0, z0 + 0.55), 1.0, "cristal", lados=20, anillos=10, escala=(W * 0.5, L * 0.5, 1.8))
        for f in burbuja:
            for v in f.verts:
                if v.co.z < z0 + 0.55:
                    v.co.z = z0 + 0.55
        for k in range(6):
            a = math.pi * k / 5
            pts = [V((math.cos(a) * W * 0.5 * math.cos(b), L * 0.5 * math.sin(b) * 0.98, z0 + 0.55 +
                      math.sin(a) * 1.8 * math.cos(b) * 0.0 + 1.8 * math.cos(b) * math.sin(a) * 0.0))
                   for b in (-math.pi / 2 + math.pi * i / 8 for i in range(9))]
        # costillas sobre la cúpula
        for t in (-0.3, 0.0, 0.3):
            pts, nrm = [], []
            for k in range(11):
                a = math.pi * k / 10
                f_ = math.sqrt(max(0.0, 1 - (t * 2) ** 2))
                x = math.cos(a) * W * 0.5 * f_
                z = z0 + 0.55 + math.sin(a) * 1.8 * f_
                pts.append(V((x, t * L, z)))
                nrm.append(V((x, 0, z - z0 - 0.55)).normalized())
            con.tira(pts, nrm, 0.14, "secundario", alto=0.08)
            con.tira([q + n_ * 0.08 for q, n_ in zip(pts, nrm)], nrm, 0.04, "neon", alto=0.02)
        # asiento vivo
        con.esfera((0, 0.4, z0 + 0.85), 0.5, "organico", lados=12, anillos=6, escala=(1.1, 0.9, 0.5))
        con.esfera((0, 0.75, z0 + 1.5), 0.45, "organico", lados=12, anillos=6, escala=(1.0, 0.45, 1.3))
        for k in range(4):
            a = 0.5 + k * 0.7
            con.cilindro((math.cos(a) * 0.5, 0.75, z0 + 1.1 + k * 0.2), (math.cos(a), 0.3, 0.6), 0.06, 0.6, "neon",
                         lados=6, radio2=0.01)
        _ancla(con, "asiento_1", (0, 0.4, z0 + 1.0))
        return
    if estilo == "ia":
        # sin asiento: núcleo de IA (un ojo) rodeado de pantallas
        con.revolucion((0, 0, zb), (0, 0, 1), [(0, 0), (0, 0.9), (0.8, 0.7), (1.0, 0)], "secundario", lados=16)
        con.esfera((0, -0.1, zb + 1.3), 0.55, "oscuro", lados=16, anillos=8)
        con.esfera((0, -0.5, zb + 1.3), 0.25, "neon", lados=12, anillos=6, escala=(1, 0.5, 1))
        con.toro((0, -0.1, zb + 1.3), (0, 1, 0), 0.65, 0.06, "neon2", n1=20, n2=4)
        for k in range(5):
            a = -math.pi * 0.8 + math.pi * 1.6 * k / 4
            d = V((math.sin(a), -math.cos(a), 0))
            c = V((0, -0.1, zb + 1.2)) + d * 1.1
            con.caja_orientada(c, -d, V((0, 0, 1)).cross(-d), (0.8, 1.0, 0.08), "pantalla")
        cup = con.esfera((0, 0, zb), 1.0, "cristal", lados=20, anillos=10, escala=(W * 0.5, L * 0.5, 2.2))
        for f in cup:
            for v in f.verts:
                if v.co.z < zb:
                    v.co.z = zb
        for k in range(8):
            a = math.tau * k / 8
            con.caja((math.cos(a) * W * 0.45, math.sin(a) * L * 0.45, zb + 0.04), (0.3, 0.3, 0.06), "neon",
                     bisel=False)
        con.info["json_plazas"] = 0
        return


# ==============================================================================================================
# Utilidades
# ==============================================================================================================

def tren(con, p):
    _color(con, p)
    estilo = p["estilo"]
    con.acople("acople_montaje", (0, 0, 0), (0, 0, 1), "CASCO_INFERIOR", "entrada", acepta=["CASCO_INFERIOR"])
    z0 = -0.14
    con.caja((0, 0, z0 - 0.25), (1.6, 1.6, 0.5), "secundario")
    if estilo == "hover":
        con.caja((0, 0, z0 - 0.62), (3.6, 0.7, 0.3), "primario")
        con.caja((0, 0, z0 - 0.62), (0.7, 3.2, 0.3), "primario")
        for x, y in ((1.7, 0), (-1.7, 0), (0, 1.5), (0, -1.5)):
            con.revolucion((x, y, z0 - 0.4), (0, 0, -1), [(0, 0), (0, 0.55), (0.3, 0.62), (0.55, 0.5), (0.55, 0)],
                           "oscuro", lados=16)
            con.revolucion((x, y, z0 - 0.97), (0, 0, -1), [(0, 0.42), (0.03, 0.42), (0.05, 0)], "neon", lados=16,
                           bisel=False)
            con.toro((x, y, z0 - 0.92), (0, 0, 1), 0.55, 0.04, "neon2", n1=18, n2=4)
            _ancla(con, f"repulsor_{len(con.info.get('vfx', [])) + 1}", (x, y, z0 - 1.0), (0, 0, -1))
        con.info["json_altura_flotacion"] = 1.6
        return
    largo_pata = p.get("largo_pata", 2.2)
    patas = [(-1.0, 0.4), (1.0, 0.4), (0.0, -0.7)] if estilo == "fijo" else [(-1.0, 0.3), (1.0, 0.3)]
    grupo = "patas" if estilo == "retractil" else "cuerpo"
    with con.grupo(grupo):
        for x, y in patas:
            top = V((x * 0.5, y * 0.5, z0 - 0.4))
            pie = V((x * 1.4, y * 1.4, z0 - largo_pata))
            d = pie - top
            con.cilindro(top, d, 0.14, d.length, "metal" if estilo == "fijo" else "secundario", lados=8)
            if estilo == "retractil":
                # pistón hidráulico
                p0 = V((x * 0.2, y * 0.2 + 0.4, z0 - 0.45))
                p1 = top + d * 0.6
                dd = p1 - p0
                con.cilindro(p0, dd, 0.09, dd.length * 0.6, "oscuro", lados=6)
                con.cilindro(p0 + dd * 0.55, dd, 0.06, dd.length * 0.45, "metal", lados=6)
                con.cilindro(top + d * 0.5 - V((0.15, 0, 0)), (1, 0, 0), 0.18, 0.3, "aviso", lados=8)
                # rueda
                con.cilindro(pie + V((-0.25, 0, 0.25)), (1, 0, 0), 0.4, 0.5, "goma", lados=14)
                con.cilindro(pie + V((-0.27, 0, 0.25)), (1, 0, 0), 0.22, 0.54, "metal", lados=10)
            else:
                # pie plano con muelle
                con.cilindro(pie, (0, 0, 1), 0.45, 0.18, "secundario", lados=10)
                con.cilindro(pie + V((0, 0, -0.05)), (0, 0, 1), 0.5, 0.06, "goma", lados=10)
                con.toro(top + d * 0.4, d, 0.2, 0.04, "metal", n1=10, n2=4)
                con.toro(top + d * 0.5, d, 0.2, 0.04, "metal", n1=10, n2=4)
    if estilo == "retractil":
        con.info["json_posiciones"] = {"desplegado": "malla _patas tal cual",
                                       "recogido": "girar _patas 90° hacia atrás alrededor del eje X en la base"}
    con.info["json_altura_apoyo"] = round(largo_pata + 0.14 + (0.4 if estilo == "retractil" else 0.08), 2)


def estabilizador(con, p):
    _color(con, p)
    estilo = p["estilo"]
    con.acople("acople_montaje", (0, 0, 0), (0, 0, -1), "CASCO_SUPERIOR", "entrada",
               acepta=["CASCO_SUPERIOR", "UNIVERSAL"])
    z0 = 0.14
    con.caja((0, 0.2, z0 + 0.15), (1.2, 2.6, 0.3), "secundario")
    alto = p.get("alto", 2.6)
    cuerda = p.get("cuerda", 2.6)
    flecha = p.get("flecha", 1.2)

    def aleta(x, inclinacion):
        secs = []
        for k in range(4):
            u = k / 3
            c = cuerda * (1 - 0.55 * u)
            secs.append((0, -cuerda / 2 + flecha * u + 0.2, c, 0.28 * (1 - 0.4 * u), 0))
        # la función ala() construye a lo largo de X: se construye y se gira para ponerla vertical
        caras = con.ala([(z0 + 0.25 + alto * k / 3, y, c, g, 0) for k, (_, y, c, g, _) in enumerate(secs)],
                        "primario", perfil="redondo" if con.tier < 3 else "rombo", n=10)
        con.girar(caras, -math.pi / 2, (0, 1, 0))
        con.girar(caras, inclinacion, (0, 1, 0))
        con.mover(caras, (x, 0, 0))
        return caras

    if estilo == "doble":
        for s in (-1, 1):
            caras = aleta(s * 0.35, s * math.radians(35))
        con.caja((0, 0.2 + cuerda * 0.3, z0 + 0.38), (0.9, 0.5, 0.2), "aviso", bisel=False)
    else:
        aleta(0.0, 0.0)
        # timón
        con.caja((0, -cuerda / 2 + 0.2 + cuerda * 0.92 + flecha * 0.3, z0 + 0.25 + alto * 0.4),
                 (0.16, cuerda * 0.18, alto * 0.6), "secundario" if con.tier == 1 else "oscuro")
        if estilo == "avanzado":
            pts, nrm = [], []
            for k in range(4):
                u = k / 3
                pts.append(V((0, -cuerda / 2 + flecha * u + 0.18, z0 + 0.25 + alto * u)))
                nrm.append(V((0, -1, 0.3)).normalized())
            con.tira(pts, nrm, 0.08, "neon", alto=0.05)
            con.esfera((0, -cuerda / 2 + flecha + 0.5, z0 + 0.3 + alto), 0.1, "neon2", lados=8, anillos=4)
        else:
            con.esfera((0, flecha + 0.2, z0 + 0.3 + alto), 0.09, "neon2", lados=8, anillos=4)


def tanque(con, p):
    _color(con, p)
    estilo = p["estilo"]
    con.acople("acople_montaje", (0, 0, 0), (0, 0, 1), "ALA_PUNTA", "entrada",
               acepta=["ALA_PUNTA", "CASCO_INFERIOR", "UNIVERSAL"])
    z0 = -0.14
    con.prisma([(-0.7, 0), (0.7, 0), (0.45, -0.45), (-0.45, -0.45)], (0, 0, z0), (0, 1, 0), (0, 0, 1), (1, 0, 0), 0.5,
               "oscuro")
    R = p.get("R", 0.75)
    L = p.get("largo", 4.5)
    zc = z0 - 0.45 - R + 0.1
    if estilo == "cilindro":
        con.revolucion((0, -L / 2, zc), (0, 1, 0), [(0, 0), (0.15, R * 0.6), (0.5, R), (L - 0.5, R), (L - 0.15, R * 0.6),
                                                    (L, 0)], "primario", lados=16)
        for t in (0.25, 0.75):
            con.toro((0, -L / 2 + L * t, zc), (0, 1, 0), R + 0.02, 0.06, "secundario", n1=16, n2=4)
        con.caja((0, 0, zc - R - 0.02), (0.08, L * 0.5, 0.08), "aviso", bisel=False)
        con.cilindro((R * 0.7, L * 0.3, zc + R * 0.7), (1, 0, 1), 0.1, 0.18, "metal", lados=6)
        for s in (-1, 1):
            con.caja((s * 0.35, s * 0.6, z0 - 0.5), (0.12, 0.25, 0.3), "metal", bisel=False)
    else:
        # gota aerodinámica integrada, con aleta y medidor de neón
        perf = [(0, 0), (0.2, R * 0.55), (0.8, R * 0.95), (L * 0.5, R * 1.05), (L * 0.85, R * 0.7), (L, 0.06), (L, 0)]
        con.revolucion((0, -L * 0.45, zc), (0, 1, 0), perf, "primario", lados=18, escala_u=1.25)
        con.prisma([(0, 0), (0.9, 0), (1.1, -0.55), (0.6, -0.55)], (0, L * 0.25, zc - R * 0.9), (0, 1, 0), (0, 0, 1),
                   (1, 0, 0), 0.08, "secundario")
        con.tira([V((R * 1.2, -L * 0.25, zc)), V((R * 1.2, L * 0.2, zc))], [V((1, 0, 0))] * 2, 0.1, "neon", alto=0.03)
        con.tira([V((-R * 1.2, -L * 0.25, zc)), V((-R * 1.2, L * 0.2, zc))], [V((-1, 0, 0))] * 2, 0.1, "neon", alto=0.03)


def radar(con, p):
    _color(con, p)
    con.acople("acople_montaje", (0, 0, 0), (0, 0, -1), "UNIVERSAL", "entrada",
               acepta=["CASCO_SUPERIOR", "CASCO_INFERIOR", "CASCO_LATERAL", "ALA_PUNTA", "UNIVERSAL", "CASCO_FRONTAL"])
    con.revolucion((0, 0, 0.14), (0, 0, 1), [(0, 0), (0, 0.8), (0.3, 0.7), (0.45, 0.35), (1.3, 0.25), (1.4, 0)],
                   "primario", lados=14)
    con.rejilla((0, 0.62, 0.45), (0, 1, 0), (1, 0, 0), 0.8, 0.3, "oscuro", "metal", lamas=3)
    with con.grupo("plato"):
        zc = 1.9
        con.cilindro((0, 0, 1.4), (0, 0, 1), 0.2, 0.5, "secundario", lados=10)
        eje = V((0, -1, 0.35)).normalized()
        c = V((0, 0.35, zc))
        con.revolucion(c, eje, [(0, 0.2), (0.3, 0.9), (0.5, 1.35), (0.56, 1.4), (0.5, 1.33), (0.28, 0.85),
                                (0.04, 0.15)], "secundario", lados=20)
        con.cilindro(c + eje * 0.1, eje, 0.06, 1.0, "metal", lados=6)
        con.esfera(c + eje * 1.1, 0.12, "neon", lados=8, anillos=4)
        for s in (-1, 1):
            con.cilindro(c + eje * 0.45 + V((s * 1.2, 0, 0)), -eje + V((-s * 1.0, 0, 0)), 0.03, 1.4, "metal", lados=4,
                         bisel=False)
    con.info["json_pivote_plato"] = "la malla _plato gira alrededor del eje Y de Roblox (vertical)"


def bahia(con, p):
    _color(con, p)
    con.acople("acople_montaje", (0, 0, 0), (0, 0, 1), "CASCO_INFERIOR", "entrada", acepta=["CASCO_INFERIOR"])
    W, L, H = p.get("ancho", 4.0), p.get("largo", 6.0), p.get("alto", 2.6)
    z0 = -0.14
    # techo, suelo y vigas (abierto por los lados y por detrás)
    con.caja((0, 0, z0 - 0.15), (W, L, 0.3), "primario")
    con.caja((0, 0, z0 - H), (W, L, 0.3), "primario")
    for x in (-W / 2 + 0.15, W / 2 - 0.15):
        for y in (-L / 2 + 0.15, 0, L / 2 - 0.15):
            con.caja((x, y, z0 - H / 2), (0.3, 0.3, H - 0.3), "secundario")
        con.caja((x, 0, z0 - 0.45), (0.2, L, 0.25), "oscuro")
    con.caja((0, -L / 2 + 0.1, z0 - H / 2), (W, 0.2, H - 0.3), "secundario")  # mamparo delantero
    # carriles de neón en el suelo
    for x in (-W * 0.3, W * 0.3):
        con.caja((x, 0, z0 - H + 0.17), (0.08, L * 0.9, 0.04), "neon", bisel=False)
    # cajas de recursos
    for (x, y, s) in ((-0.9, -1.6, 1.1), (0.8, -1.4, 0.9), (-0.8, 0.4, 0.95), (0.9, 0.7, 1.15), (0.0, 2.0, 1.0)):
        con.caja((x, y, z0 - H + 0.15 + s / 2), (s, s, s), "aviso" if (x > 0) else "oscuro")
        con.caja((x, y - s / 2 - 0.01, z0 - H + 0.15 + s / 2), (s * 0.6, 0.04, s * 0.15), "neon2", bisel=False)
    # foco
    con.cilindro((0, 0, z0 - 0.3), (0, 0, -1), 0.3, 0.1, "neon", lados=12, bisel=False)
    con.acople("acople_inferior", (0, 0, z0 - H - 0.15), (0, 0, -1), "CASCO_INFERIOR", "salida", en_superficie=True)
    con.info["json_capacidad"] = "caja interior de %.1f × %.1f × %.1f studs" % (W - 0.6, L - 0.4, H - 0.6)
