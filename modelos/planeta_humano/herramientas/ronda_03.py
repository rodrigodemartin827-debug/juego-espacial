"""Ronda 3 · Fin de la zona residencial (21-25) y primeras tiendas de la zona comercial (26-30)."""

import math

from geometria import arco_pts
from registro import modelo


@modelo(21, "residencial", "prop", (4, 3, 3))
def escalera_publica(m):
    # Seis peldaños macizos entre dos muretes, huellas antideslizantes, luz bajo cada mamperlán y barandillas
    n, huella, contra = 6, 0.5, 0.3
    for i in range(n):
        y0 = -1.5 + huella * i
        m.bloque((-1.7, y0, 0), (1.7, 1.5, contra * (i + 1) - 0.05), "gris")
        m.bloque((-1.7, y0 - 0.04, contra * (i + 1) - 0.05), (1.7, y0 + huella, contra * (i + 1)), "rejilla")
        m.caja((0, y0 - 0.045, contra * (i + 1) - 0.09), (3.2, 0.03, 0.04), "neon")
    for sx in (-1, 1):
        perfil = [(-1.5, 0), (1.5, 0), (1.5, 2.0), (1.1, 2.0), (-1.5, 0.5)]
        m.prisma(perfil, sx * 1.7, sx * 2.0, "blanco", "yz")
        m.prisma([(-1.52, 0.5), (1.1, 2.0), (1.52, 2.0), (1.52, 2.08), (1.08, 2.08), (-1.52, 0.58)], sx * 1.68,
                 sx * 2.02, "gris_liso", "yz")
        x = sx * 1.85
        for y, z in ((-1.35, 0.62), (-0.2, 1.28), (1.0, 1.97), (1.42, 2.08)):
            m.cil((x, y, z + 0.45), 0.05, 0.9, "acero", seg=6)
        m.barrido([(x, -1.35, 1.52), (x, 1.0, 2.87), (x, 1.42, 2.98)], 0.06, "acero", seg=6)
        m.barrido([(x, -1.35, 1.1), (x, 1.0, 2.45), (x, 1.42, 2.56)], 0.035, "acero", seg=5)
        m.esfera((x, -1.35, 1.52), 0.08, "acero", seg=8, anillos=5)
    m.bloque((-1.7, 1.0, 1.75), (1.7, 1.5, 1.8), "rejilla")


@modelo(22, "residencial", "prop", (6, 3, 4))
def marquesina_parada(m):
    # Losa, dos pórticos, cubierta curva con grosor, cristaleras, banco y tótem con pantalla de horarios
    m.caja((0, 0, 0.08), (6, 3, 0.16), "hormigon", bisel=0.03)
    m.bloque((-2.9, -1.45, 0.16), (2.9, -1.2, 0.19), "rayas")
    for x in (-2.6, 2.6):
        m.caja((x, 1.2, 1.9), (0.18, 0.18, 3.5), "blanco_liso", bisel=0.03)
        m.barrido([(x, 1.2, 3.3), (x, 0.4, 3.75), (x, -1.2, 3.62)], 0.07, "blanco_liso", seg=6)
        m.caja((x, 1.2, 0.22), (0.4, 0.4, 0.12), "oscuro")
    techo = [(1.45 - 2.9 * i / 8, 3.62 + 0.3 * math.sin(math.pi * i / 8) - 0.012 * i) for i in range(9)]
    techo_inf = [(y, zz - 0.1) for y, zz in reversed(techo)]
    m.prisma(techo + techo_inf, -2.95, 2.95, "gris", "yz")
    m.caja((0, -1.42, 3.47), (5.6, 0.05, 0.06), "neon")
    # Cristaleras trasera y lateral
    m.bloque((-2.5, 1.17, 0.5), (-0.1, 1.23, 3.1), "cristal")
    m.bloque((0.1, 1.17, 0.5), (2.5, 1.23, 3.1), "cristal")
    m.caja((0, 1.2, 1.8), (0.12, 0.12, 2.9), "blanco_liso")
    for z in (0.45, 3.15):
        m.caja((0, 1.2, z), (5.1, 0.1, 0.1), "blanco_liso")
    m.bloque((2.57, -0.4, 0.5), (2.63, 1.1, 3.1), "cristal")
    m.caja((2.6, -0.45, 1.8), (0.1, 0.1, 2.9), "blanco_liso")
    # Banco de lamas sobre ménsulas
    for x in (-2.1, -0.4):
        m.prisma([(1.15, 0.55), (1.15, 1.0), (0.35, 1.0), (0.35, 0.92)], x - 0.04, x + 0.04, "acero", "yz")
    for y in (0.45, 0.7, 0.95):
        m.caja((-1.25, y, 1.04), (2.5, 0.2, 0.08), "madera_clara", bisel=0.015)
    # Tótem de horarios: carcasa, pantalla y líneas de texto luminosas
    m.caja((1.6, 0.85, 1.3), (0.9, 0.22, 2.3), "oscuro", bisel=0.03)
    m.caja((1.6, 0.73, 1.55), (0.74, 0.03, 1.4), "pantalla")
    m.caja((1.6, 0.715, 2.12), (0.6, 0.02, 0.14), "neon", p="pantalla_neon")
    for k in range(5):
        m.caja((1.52 - 0.04 * (k % 2), 0.715, 1.85 - 0.2 * k), (0.42 - 0.08 * (k % 2), 0.02, 0.06), "neon",
               p="pantalla_neon")
        m.caja((1.86, 0.715, 1.85 - 0.2 * k), (0.1, 0.02, 0.06), "neon_naranja")
    m.cil((1.6, 0.72, 0.55), 0.05, 0.03, "acero", eje="y", seg=8)
    # Poste con el símbolo de parada
    m.cil((-2.6, -1.1, 1.6), 0.05, 2.9, "acero", seg=8)
    m.cil((-2.6, -1.1, 3.25), 0.34, 0.06, "acento", eje="y", seg=14)
    m.tubo((-2.6, -1.1, 3.25), 0.36, 0.08, 0.05, "blanco_liso", eje="y", seg=14)
    m.caja((-2.6, -1.14, 3.25), (0.36, 0.03, 0.1), "neon")


@modelo(23, "residencial", "prop", (2, 2, 8))
def antena_comunicaciones(m):
    # Zócalo de azotea, mástil de celosía que se estrecha, parabólica, antenas yagi, látigo y baliza
    m.caja((0, 0, 0.1), (1.9, 1.9, 0.2), "hormigon", bisel=0.03)
    def lado(z):
        return 0.6 - 0.42 * z / 5.6
    esquinas = ((1, 1), (-1, 1), (-1, -1), (1, -1))
    for sx, sy in esquinas:
        m.barrido([(sx * lado(0), sy * lado(0), 0.2), (sx * lado(5.6), sy * lado(5.6), 5.8)], 0.05, "acero", seg=5)
        m.caja((sx * lado(0), sy * lado(0), 0.24), (0.24, 0.24, 0.08), "oscuro")
    niveles = [0.0, 1.0, 2.0, 3.0, 4.0, 4.9, 5.6]
    for i in range(len(niveles) - 1):
        z0, z1 = niveles[i] + 0.2, niveles[i + 1] + 0.2
        l0, l1 = lado(niveles[i]), lado(niveles[i + 1])
        for k in range(4):
            (ax, ay), (bx, by) = esquinas[k], esquinas[(k + 1) % 4]
            m.barrido([(ax * l1, ay * l1, z1), (bx * l1, by * l1, z1)], 0.025, "acero", seg=4)
            if i % 2 == k % 2:
                m.barrido([(ax * l0, ay * l0, z0), (bx * l1, by * l1, z1)], 0.022, "acero", seg=4)
            else:
                m.barrido([(bx * l0, by * l0, z0), (ax * l1, ay * l1, z1)], 0.022, "acero", seg=4)
    m.caja((0, 0, 5.86), (0.42, 0.42, 0.12), "gris_liso")
    m.cil((0, 0, 6.6), 0.045, 1.4, "blanco_liso", seg=8)
    m.cil((0, 0, 7.55), 0.018, 0.6, "acero", seg=5)
    m.esfera((0, 0, 7.9), 0.07, "neon_rojo", seg=8, anillos=5)
    # Parabólica orientada al frente con su alimentador
    m.caja((0, -0.3, 4.3), (0.2, 0.5, 0.2), "gris_liso")
    m.cupula((0, -0.5, 4.3), 0.82, "blanco_liso", grosor=0.06, seg=16, anillos=4, altura=0.36, rot=(105, 0, 0))
    for a in (90, 210, 330):
        ra = math.radians(a)
        m.barrido([(0.6 * math.cos(ra), -0.62, 4.3 + 0.6 * math.sin(ra)), (0, -1.02, 4.42)], 0.018, "acero", seg=4)
    m.cil((0, -1.03, 4.42), 0.06, 0.16, "oscuro", eje="y", seg=8)
    # Dos yagis y un panel sectorial
    for z, s in ((3.2, 1), (2.5, -1)):
        m.cil((s * 0.55, 0, z), 0.025, 1.0, "acero", eje="x", seg=5)
        for k in range(5):
            m.cil((s * (0.2 + 0.2 * k), 0, z), 0.014, 0.6 - 0.07 * k, "acero", eje="y", seg=4)
    m.caja((0, 0.34, 5.0), (0.26, 0.1, 0.9), "blanco_liso", bisel=0.02)
    m.caja((0, 0.395, 5.0), (0.06, 0.02, 0.7), "neon")
    # Caja de equipos y cable
    m.caja((0.5, 0.5, 0.55), (0.5, 0.4, 0.7), "gris_claro", bisel=0.03)
    m.caja((0.5, 0.29, 0.7), (0.2, 0.02, 0.1), "neon")
    m.barrido([(0.5, 0.5, 0.9), (0.45, 0.45, 1.3), (0.3, 0.3, 2.6), (0.12, 0.12, 5.7)], 0.03, "goma", seg=5)


@modelo(24, "residencial", "prop", (3, 3, 0.3))
def panel_solar_techo(m):
    # Bastidor, 36 células en relieve con sus colectores, caja de conexiones y carriles de montaje
    for y in (-1.0, 1.0):
        m.caja((0, y, 0.04), (3.0, 0.14, 0.08), "acero")
        for x in (-1.2, 1.2):
            m.caja((x, y, 0.1), (0.22, 0.2, 0.06), "oscuro")
    m.caja((0, 0, 0.14), (2.9, 2.9, 0.06), "gris_liso")
    m.caja((0, 0, 0.19), (2.84, 2.84, 0.04), "negro")
    for sx in (-1, 1):
        m.caja((sx * 1.45, 0, 0.19), (0.1, 3.0, 0.16), "acero", bisel=0.015)
        m.caja((0, sx * 1.45, 0.19), (2.8, 0.1, 0.16), "acero")
    for i in range(6):
        for j in range(6):
            x, y = -1.15 + 0.46 * i, -1.15 + 0.46 * j
            m.caja((x, y, 0.218), (0.42, 0.42, 0.024), "panel_solar", bisel=0.01)
    for i in range(6):
        m.caja((-1.15 + 0.46 * i, 0, 0.233), (0.015, 2.74, 0.008), "cromo")
    m.caja((0, 1.1, 0.07), (0.5, 0.3, 0.1), "plastico_negro", bisel=0.015)
    m.barrido([(0.2, 1.1, 0.06), (0.7, 1.15, 0.05), (1.2, 1.3, 0.04), (1.42, 1.44, 0.04)], 0.022, "goma", seg=5)
    m.caja((-1.3, -1.3, 0.275), (0.12, 0.12, 0.012), "neon")


@modelo(25, "residencial", "prop", (2, 2, 2))
def generador_electrico(m):
    # Patín, carcasa biselada, lamas, ventilador con rejilla (pieza aparte), cuadro de mando, escape y cables
    for y in (-0.7, 0.7):
        m.caja((0, y, 0.08), (1.96, 0.2, 0.16), "oscuro", bisel=0.02)
    m.caja((0, 0, 0.92), (1.8, 1.7, 1.5), "blanco_liso", bisel=0.08)
    m.caja((0, 0, 0.3), (1.84, 1.74, 0.3), "rayas")
    m.caja((0, 0, 1.69), (1.6, 1.5, 0.06), "gris_liso", bisel=0.02)
    # Ventilador frontal
    m.tubo((-0.35, -0.86, 1.0), 0.52, 0.1, 0.07, "gris_liso", eje="y", seg=18)
    m.cil((-0.35, -0.84, 1.0), 0.45, 0.04, "negro", eje="y", seg=18)
    m.cil((-0.35, -0.88, 1.0), 0.1, 0.1, "acero", eje="y", seg=10, p="ventilador")
    for k in range(6):
        m.caja((-0.35, -0.875, 1.0), (0.14, 0.02, 0.82), "gris_claro", rot=(0, 30 * k, 0), p="ventilador") if k < 3 else None
    for k in range(3):
        m.tubo((-0.35, -0.905, 1.0), 0.16 + 0.13 * k, 0.02, 0.022, "acero", eje="y", seg=16)
    for a in (0, 45, 90, 135):
        m.caja((-0.35, -0.905, 1.0), (0.96, 0.02, 0.025), "acero", rot=(0, a, 0))
    # Cuadro de mando con indicadores
    m.caja((0.55, -0.87, 1.15), (0.5, 0.06, 0.7), "oscuro", bisel=0.015)
    m.caja((0.55, -0.905, 1.33), (0.36, 0.02, 0.2), "neon", p="pantalla_neon")
    for k, mat in enumerate(("neon_verde", "neon_amarillo", "neon_rojo")):
        m.cil((0.43 + 0.12 * k, -0.905, 1.1), 0.035, 0.03, mat, eje="y", seg=8)
    m.cil((0.55, -0.92, 0.93), 0.07, 0.06, "rojo_p", eje="y", seg=10)
    # Lamas laterales
    for sx in (-1, 1):
        for k in range(6):
            m.caja((sx * 0.91, 0.1, 0.7 + 0.15 * k), (0.05, 1.1, 0.07), "gris_liso", rot=(0, sx * 25, 0))
        m.barrido([(sx * 0.75, -0.5, 1.72), (sx * 0.75, -0.5, 1.85), (sx * 0.75, 0.5, 1.85), (sx * 0.75, 0.5, 1.72)],
                  0.035, "acero", seg=6)
    # Escape y bornes con cables hasta el suelo
    m.barrido([(0.4, 0.4, 1.7), (0.4, 0.4, 1.95), (0.45, 0.55, 2.0)], 0.09, "hierro", seg=8)
    for i, x in enumerate((-0.5, -0.2, 0.1)):
        m.cil((x, 0.87, 1.2), 0.07, 0.08, "cobre", eje="y", seg=8)
        m.barrido([(x, 0.9, 1.2), (x, 1.0, 1.05), (x - 0.05, 0.98, 0.5), (x - 0.1 - 0.1 * i, 0.99, 0.06)], 0.04,
                  "goma" if i != 1 else m.color("#C8352B", 0.7), seg=6)
    m.caja((0.0, 0.855, 1.5), (0.5, 0.02, 0.2), "amarillo_p")


# --------------------------------------------------------------------------------------------------------------
# Tiendas: local con zona delantera de escaparate (nicho real con fondo, suelo y cristal)
# --------------------------------------------------------------------------------------------------------------

def _local(m, W, D, H, vanos, puerta, prof=1.6, hz=4.2, pared="blanco", zocalo="oscuro_paneles", acento="acento",
           puerta_mat="gris_claro"):
    """
    Cuerpo de tienda. `vanos` = [(x0, x1)] escaparates; `puerta` = (centro_x, ancho).
    Devuelve las cotas del nicho: frente (yf), fondo (yb), suelo (zs), dintel (hz) y techo (zt).
    """
    yf, zt = -D / 2 + 0.3, H - 1.5
    yb = yf + prof
    x0, x1 = -W / 2 + 0.3, W / 2 - 0.3
    m.caja((0, 0, 0.2), (W, D, 0.4), "hormigon", bisel=0.06)
    m.bloque((x0, yb, 0.4), (x1, D / 2 - 0.3, zt), pared)
    m.bloque((x0 - 0.05, yb, 0.4), (x1 + 0.05, D / 2 - 0.25, 1.0), zocalo)
    m.bloque((x0, yf, 0.4), (x1, yb, 0.62), "gris_liso")              # suelo de la zona delantera
    m.bloque((x0, yf, hz), (x1, yb, zt), pared)                        # dintel corrido
    m.bloque((x0 - 0.03, yf - 0.03, hz), (x1 + 0.03, yf + 0.2, hz + 0.25), acento)
    m.caja((0, yf - 0.05, hz - 0.06), (W - 1.2, 0.06, 0.07), "neon")
    # Machones entre huecos
    px0, px1 = puerta[0] - puerta[1] / 2, puerta[0] + puerta[1] / 2
    huecos = sorted(list(vanos) + [(px0, px1)])
    x = x0
    for a, b in huecos + [(x1, x1)]:
        if a - x > 0.05:
            m.bloque((x, yf, 0.62), (a, yb, hz), pared)
            m.bloque((x - 0.02, yf - 0.05, 0.4), (a + 0.02, yf + 0.3, 1.0), zocalo)
        x = b
    # Escaparates: antepecho, marco y cristal
    for a, b in vanos:
        m.bloque((a, yf, 0.62), (b, yf + 0.3, 1.05), "gris")
        m.marco(((a + b) / 2, yf + 0.12, (1.05 + hz) / 2), b - a, hz - 1.05, 0.14, 0.26, "gris_liso")
        m.bloque((a + 0.14, yf + 0.09, 1.19), (b - 0.14, yf + 0.15, hz - 0.14), "vidrio")
        m.bloque((a, yf + 0.3, 0.62), (b, yb, 0.9), "gris_claro")       # tarima del escaparate
    # Puerta automática de dos hojas (piezas aparte)
    m.marco((puerta[0], yf + 0.15, (0.62 + hz) / 2), puerta[1], hz - 0.62, 0.18, 0.34, "gris_liso")
    an = (puerta[1] - 0.36) / 2
    for s, nom in ((-1, "puerta_izq"), (1, "puerta_der")):
        cx = puerta[0] + s * an / 2
        m.caja((cx, yf + 0.2, (0.62 + hz) / 2 - 0.09), (an - 0.02, 0.1, hz - 0.62 - 0.2), puerta_mat, p=nom)
        m.caja((cx, yf + 0.14, (0.62 + hz) / 2 + 0.3), (an - 0.4, 0.05, hz - 2.6), "cristal")
    m.caja((puerta[0], yf + 0.12, hz - 0.3), (0.5, 0.06, 0.1), "neon")   # sensor de la puerta
    m.bloque((px0, yf - 0.4, 0.4), (px1, yf, 0.5), "rejilla")
    # Tejado con alero y peto
    m.bloque((x0 - 0.3, yf - 0.3, zt), (x1 + 0.3, D / 2, zt + 0.3), "gris", bisel=0.07)
    for a, b in (((x0 - 0.2, yf - 0.2, zt + 0.3), (x1 + 0.2, yf, zt + 0.55)),
                 ((x0 - 0.2, D / 2 - 0.3, zt + 0.3), (x1 + 0.2, D / 2 - 0.1, zt + 0.55)),
                 ((x0 - 0.2, yf, zt + 0.3), (x0, D / 2 - 0.3, zt + 0.55)),
                 ((x1, yf, zt + 0.3), (x1 + 0.2, D / 2 - 0.3, zt + 0.55))):
        m.bloque(a, b, "blanco_liso")
    return dict(yf=yf, yb=yb, zs=0.9, hz=hz, zt=zt, x0=x0, x1=x1)


def _rotulo(m, txt, x, y, z, alto, ancho, mat="neon", fondo="oscuro"):
    """Rótulo luminoso: panel con marco y letras 3D de neón."""
    m.caja((x, y + 0.12, z), (ancho, 0.2, alto + 0.5), fondo, bisel=0.04)
    m.marco((x, y + 0.02, z), ancho + 0.1, alto + 0.6, 0.08, 0.1, "acero")
    m.texto(txt, (x, y - 0.03, z), alto, 0.1, mat)


def _espada(m, c, largo, mat_hoja="cromo", rot=(0, 0, 0), color_empunadura="#3A2A1E"):
    """Espada 3D vertical (punta arriba) centrada en la guarda."""
    x, y, z = c
    hoja = [(-0.07, 0), (0.07, 0), (0.06, largo * 0.85), (0, largo), (-0.06, largo * 0.85)]
    m.prisma(hoja, -0.02, 0.02, mat_hoja, "xz", c=c, rot=rot)
    m.caja(c, (0.36, 0.07, 0.06), "oro", rot=rot)
    m.prisma([(-0.035, -0.3), (0.035, -0.3), (0.035, 0), (-0.035, 0)], -0.03, 0.03, m.color(color_empunadura, 0.8),
             "xz", c=c, rot=rot)
    m.prisma([(-0.06, -0.38), (0.06, -0.38), (0.06, -0.3), (-0.06, -0.3)], -0.04, 0.04, "oro", "xz", c=c, rot=rot)


@modelo(26, "comercial", "edificio_mediano", (12, 10, 8))
def tienda_armas(m):
    L = _local(m, 12, 10, 8, vanos=[(-5.3, -0.9), (3.6, 5.3)], puerta=(1.35, 2.6))
    yf, yb, zs, hz, zt = L["yf"], L["yb"], L["zs"], L["hz"], L["zt"]
    # Fondo del escaparate: panel oscuro con soportes
    m.bloque((-5.2, yb - 0.08, 0.9), (-1.0, yb, hz - 0.1), "oscuro_paneles")
    m.bloque((3.7, yb - 0.08, 0.9), (5.2, yb, hz - 0.1), "oscuro_paneles")
    # Cuatro espadas colgadas, cada una distinta
    for i, (x, largo, mat) in enumerate(((-4.6, 1.5, "cromo"), (-3.9, 1.8, "acero"), (-3.2, 1.3, "cobre"),
                                         (-2.5, 1.6, "cromo"))):
        _espada(m, (x, yb - 0.16, 1.95), largo, mat)
        for dz in (0.25, largo * 0.6):
            m.caja((x, yb - 0.11, 1.95 + dz), (0.22, 0.08, 0.04), "acero")
    # Dos escudos redondos en miniatura sobre peanas y un hacha
    for x, col in ((-1.75, "#B5332E"), (4.5, "#2D5FA8")):
        m.torno((x, yb - 0.2, 2.7), [(0.0, 0.12), (0.2, 0.1), (0.52, 0.02), (0.56, -0.04), (0.5, -0.05), (0.0, -0.02)],
                m.color(col, 0.5, 0.3), seg=14, eje="y", rot=(180, 0, 0))
        m.tubo((x, yb - 0.2, 2.7), 0.57, 0.07, 0.07, "acero", eje="y", seg=14)
        m.esfera((x, yb - 0.3, 2.7), 0.12, "oro", seg=8, anillos=5, esc=(1, 0.6, 1))
    m.cil((4.5, yb - 0.5, 1.5), 0.04, 1.3, "madera_oscura", seg=6, rot=(0, 20, 0))
    m.prisma([(0, -0.25), (0.42, -0.36), (0.5, 0.0), (0.42, 0.36), (0, 0.25)], -0.025, 0.025, "acero", "xz",
             c=(4.72, yb - 0.5, 2.0), rot=(0, 20, 0))
    # Expositor bajo con dagas sobre terciopelo
    m.caja((-3.3, yf + 0.9, 1.05), (3.4, 0.7, 0.3), "tela_roja", bisel=0.04)
    for k in range(4):
        _espada(m, (-4.3 + 0.7 * k, yf + 0.9, 1.23), 0.55, "cromo", rot=(-90, 0, 35 - 20 * k))
    m.caja((4.45, yf + 0.9, 1.1), (1.2, 0.7, 0.4), "madera_oscura", bisel=0.03)
    m.torno((4.45, yf + 0.9, 1.3), [(0.3, 0), (0.34, 0.2), (0.26, 0.5), (0.0, 0.62)], "acero", seg=10)  # yelmo
    m.caja((4.45, yf + 0.61, 1.62), (0.3, 0.06, 0.05), "negro")
    # Rótulo ARMAS y emblema de espadas cruzadas en el tejado
    _rotulo(m, "ARMAS", -2.2, yf - 0.32, hz + 1.25, 0.95, 4.6)
    for s in (-1, 1):
        _espada(m, (1.35, yf - 0.34, zt + 0.9), 1.5, "neon", rot=(0, s * 38, 0))
    m.caja((1.35, yf - 0.24, zt + 1.25), (2.6, 0.16, 2.5), "oscuro", bisel=0.05)
    # Azotea: ventilación y focos
    m.caja((3.2, 2.2, zt + 0.75), (2.0, 1.6, 0.9), "gris_claro", bisel=0.05)
    m.cil((3.2, 2.2, zt + 1.22), 0.55, 0.08, "oscuro", seg=12)
    m.barrido([(-4.0, 2.5, zt + 0.3), (-4.0, 2.5, zt + 0.9), (-3.6, 2.5, zt + 1.0)], 0.12, "acero", seg=8)
    for sx in (-1, 1):
        m.ventana((sx * 5.72, 1.6, 2.8), 2.6, 1.6, normal="x", sentido=sx, cruz=True)
    m.ventana((0, 4.72, 2.8), 3.0, 1.6, sentido=1, cruz=True)


def _maniqui(m, c, armadura, detalle="oro"):
    """Maniquí de escaparate con armadura puesta (peto, hombreras, yelmo, faldar)."""
    x, y, z = c
    m.cil((x, y, z + 0.04), 0.34, 0.08, "oscuro", seg=12)
    m.cil((x, y, z + 0.6), 0.04, 1.1, "acero", seg=6)
    for s in (-1, 1):                                     # piernas con grebas
        m.torno((x + s * 0.16, y, z + 0.1), [(0.1, 0), (0.12, 0.5), (0.14, 0.62), (0.13, 1.1), (0.0, 1.12)],
                armadura, seg=8)
        m.esfera((x + s * 0.16, y - 0.04, z + 0.68), 0.13, detalle, seg=8, anillos=5, esc=(1, 0.8, 1))
    m.torno((x, y, z + 1.12), [(0.3, 0), (0.36, 0.1), (0.3, 0.42), (0.0, 0.44)], armadura, seg=10)   # faldar
    m.torno((x, y, z + 1.5), [(0.26, 0), (0.3, 0.25), (0.4, 0.62), (0.34, 0.85), (0.14, 0.95), (0.0, 0.96)], armadura,
            seg=10, rot=(0, 0, 0))
    m.caja((x, y - 0.3, z + 2.0), (0.3, 0.1, 0.4), detalle, bisel=0.03)
    for s in (-1, 1):
        m.esfera((x + s * 0.46, y, z + 2.32), 0.2, armadura, seg=10, anillos=6, esc=(1, 1, 0.8))
        m.tubo((x + s * 0.46, y, z + 2.22), 0.21, 0.05, 0.03, detalle, seg=10)
        m.torno((x + s * 0.5, y, z + 1.45), [(0.07, 0), (0.1, 0.3), (0.09, 0.75), (0.0, 0.76)], armadura, seg=8)
    m.cil((x, y, z + 2.52), 0.08, 0.14, "gris_claro", seg=8)
    m.torno((x, y, z + 2.58), [(0.17, 0), (0.22, 0.15), (0.2, 0.36), (0.1, 0.46), (0.0, 0.48)], armadura, seg=10)
    m.caja((x, y - 0.2, z + 2.8), (0.26, 0.05, 0.05), "negro")
    m.prisma([(-0.03, 0), (0.03, 0), (0.03, 0.3), (-0.03, 0.22)], -0.14, 0.2, detalle, "xz", c=(x, y, z + 3.0))


@modelo(27, "comercial", "edificio_mediano", (12, 10, 8))
def tienda_armaduras(m):
    L = _local(m, 12, 10, 8, vanos=[(-5.3, -2.3), (2.3, 5.3)], puerta=(0, 2.8), acento="oro", zocalo="oscuro")
    yf, yb, zs, hz, zt = L["yf"], L["yb"], L["zs"], L["hz"], L["zt"]
    for a, b in ((-5.2, -2.4), (2.4, 5.2)):
        m.bloque((a, yb - 0.08, 0.9), (b, yb, hz - 0.1), "tela_azul")
    # Tres maniquíes con armaduras distintas
    _maniqui(m, (-4.4, yf + 0.9, 0.9), "acero", "oro")
    _maniqui(m, (-3.2, yf + 0.95, 0.9), m.color("#27303B", 0.4, 0.9), "acento")
    _maniqui(m, (3.2, yf + 0.9, 0.9), "bronce", "cromo")
    # Soporte con cascos y escudo de lágrima
    m.caja((4.5, yf + 1.0, 1.4), (1.0, 0.6, 1.0), "madera_oscura", bisel=0.03)
    for k, mat in enumerate(("acero", "oro")):
        m.torno((4.25 + 0.5 * k, yf + 0.95, 1.9), [(0.17, 0), (0.22, 0.15), (0.2, 0.34), (0.0, 0.46)], mat, seg=10)
    m.prisma([(-0.4, 0.5), (0.4, 0.5), (0.4, 0.0), (0.0, -0.6), (-0.4, 0.0)], -0.04, 0.04, m.color("#B5332E", 0.5, 0.3),
             "xz", c=(4.5, yb - 0.14, 3.2))
    m.prisma([(-0.05, 0.5), (0.05, 0.5), (0.05, -0.5), (-0.05, -0.5)], -0.06, 0.06, "oro", "xz", c=(4.5, yb - 0.16, 3.2))
    # Frontón escalonado con rótulo ARMADURAS y emblema de escudo
    m.bloque((-4.6, yf - 0.1, zt + 0.3), (4.6, yf + 0.5, zt + 1.3), "blanco")
    m.bloque((-2.6, yf - 0.12, zt + 1.3), (2.6, yf + 0.5, zt + 1.9), "blanco")
    m.bloque((-4.7, yf - 0.16, zt + 1.3), (-2.6, yf + 0.56, zt + 1.42), "oro")
    m.bloque((2.6, yf - 0.16, zt + 1.3), (4.7, yf + 0.56, zt + 1.42), "oro")
    m.bloque((-2.7, yf - 0.18, zt + 1.9), (2.7, yf + 0.56, zt + 2.0), "oro")
    m.caja((0, yf - 0.08, hz + 1.2), (7.6, 0.14, 1.2), "oscuro", bisel=0.04)
    m.texto("ARMADURAS", (0, yf - 0.2, hz + 1.2), 0.7, 0.1, "neon")
    m.prisma([(-0.45, 0.4), (0.45, 0.4), (0.45, -0.05), (0.0, -0.55), (-0.45, -0.05)], -0.05, 0.05, "neon", "xz",
             c=(0, yf - 0.2, zt + 1.15))
    for sx in (-1, 1):
        m.ventana((sx * 5.72, 1.6, 2.8), 2.2, 1.8, normal="x", sentido=sx)
        m.torno((sx * 4.9, yf + 0.2, zt + 1.3), [(0.3, 0), (0.2, 0.1), (0.24, 0.5), (0.0, 0.9)], "oro", seg=8)
    m.ventana((0, 4.72, 2.8), 3.4, 1.6, sentido=1, cruz=True)
    m.caja((2.8, 2.4, zt + 0.7), (1.8, 1.4, 0.8), "gris_claro", bisel=0.05)


def _frasco(m, c, r, liquido, tipo=0):
    """Frasco de cristal con líquido dentro: 0 = redondo, 1 = cilíndrico, 2 = cónico."""
    x, y, z = c
    col = m.color(liquido, 0.25)
    if tipo == 0:
        m.esfera((x, y, z + r), r * 0.86, col, seg=8, anillos=6, esc=(1, 1, 0.8))
        m.esfera((x, y, z + r), r, "cristal", seg=10, anillos=6)
        cuello = z + r * 1.9
    elif tipo == 1:
        m.cil((x, y, z + r * 0.75), r * 0.72, r * 1.2, col, seg=8)
        m.cil((x, y, z + r), r * 0.82, r * 2.0, "cristal", seg=10)
        cuello = z + r * 2.0
    else:
        m.torno((x, y, z + 0.02), [(r * 0.85, 0), (r * 0.5, r * 0.9), (0, r * 0.9)], col, seg=8)
        m.torno((x, y, z), [(r, 0), (r * 0.3, r * 1.9), (0, r * 1.9)], "cristal", seg=10)
        cuello = z + r * 1.8
    m.cil((x, y, cuello + r * 0.2), r * 0.3, r * 0.5, "cristal", seg=8)
    m.cil((x, y, cuello + r * 0.52), r * 0.33, r * 0.22, "madera_clara", seg=6)


@modelo(28, "comercial", "edificio_mediano", (10, 8, 7))
def tienda_pociones(m):
    L = _local(m, 10, 8, 7, vanos=[(-4.3, 0.4)], puerta=(2.6, 2.4), hz=3.9, acento="verde_p", prof=1.4)
    yf, yb, zs, hz, zt = L["yf"], L["yb"], L["zs"], L["hz"], L["zt"]
    m.bloque((-4.2, yb - 0.08, 0.9), (0.3, yb, hz - 0.1), "madera_oscura")
    # Estantes con frascos de colores
    colores = ["#E0403A", "#3DB8F2", "#57D95B", "#B455E0", "#F2C230", "#FF7A1A", "#2FE0C0"]
    k = 0
    for z in (1.75, 2.6, 3.3):
        m.caja((-1.95, yb - 0.38, z), (4.3, 0.6, 0.07), "madera", bisel=0.015)
        for sx in (-4.0, 0.1):
            m.prisma([(0, 0), (0.5, 0), (0, -0.3)], -0.03, 0.03, "hierro", "yz", c=(sx, yb - 0.62, z - 0.03))
        n = 6 if z < 3 else 5
        for i in range(n):
            x = -3.75 + (3.6 / (n - 1)) * i
            _frasco(m, (x, yb - 0.4, z + 0.035), 0.2 if z < 3 else 0.16, colores[k % 7], tipo=k % 3)
            k += 1
    # Tarima: caldero, caja de suministros y dos garrafas grandes
    m.torno((-3.2, yf + 0.8, 0.9), [(0.3, 0), (0.48, 0.2), (0.5, 0.5), (0.42, 0.62), (0.34, 0.62), (0.4, 0.5),
                                    (0.38, 0.22), (0, 0.12)], "hierro", seg=12)
    m.cil((-3.2, yf + 0.8, 1.42), 0.38, 0.06, "neon_verde", seg=12)
    m.caja((-1.9, yf + 0.8, 1.15), (0.9, 0.7, 0.5), "madera_clara", bisel=0.02)
    for i in range(3):
        _frasco(m, (-2.15 + 0.25 * i, yf + 0.75, 1.4), 0.11, colores[i + 2], tipo=1)
    _frasco(m, (-0.6, yf + 0.8, 0.9), 0.34, "#3DB8F2", tipo=0)
    _frasco(m, (-0.05, yf + 0.95, 0.9), 0.26, "#E0403A", tipo=2)
    # Rótulo SUMINISTROS y gran frasco luminoso en la azotea
    m.caja((-0.8, yf - 0.1, hz + 1.0), (7.4, 0.16, 1.0), "oscuro", bisel=0.04)
    m.texto("SUMINISTROS", (-0.8, yf - 0.22, hz + 1.0), 0.56, 0.1, "neon")
    m.cil((3.2, -1.5, zt + 0.5), 0.5, 0.4, "gris_liso", seg=12)
    m.esfera((3.2, -1.5, zt + 1.35), 0.6, "neon_verde", seg=12, anillos=8, esc=(1, 1, 0.75))
    m.esfera((3.2, -1.5, zt + 1.45), 0.75, "cristal", seg=14, anillos=8)
    m.cil((3.2, -1.5, zt + 2.3), 0.22, 0.5, "cristal", seg=10)
    m.cil((3.2, -1.5, zt + 2.62), 0.26, 0.16, "madera_clara", seg=8)
    # Toldo de lona sobre el escaparate
    m.prisma([(yf - 1.1, hz - 0.5), (yf, hz - 0.05), (yf, hz + 0.05), (yf - 1.1, hz - 0.4)], -4.4, 0.5, "tela_verde",
             "yz")
    for x in (-4.35, 0.45):
        m.barrido([(x, yf, hz - 0.5), (x, yf - 1.08, hz - 0.47)], 0.03, "acero", seg=5)
    for sx in (-1, 1):
        m.ventana((sx * 4.72, 1.4, 2.6), 2.0, 1.6, normal="x", sentido=sx, cruz=True)
    m.ventana((0, 3.72, 2.6), 2.6, 1.5, sentido=1)
    m.barrido([(-3.0, 2.0, zt + 0.3), (-3.0, 2.0, zt + 1.3)], 0.2, "acero", seg=10)
    m.torno((-3.0, 2.0, zt + 1.3), [(0.34, 0), (0.34, 0.06), (0, 0.3)], "hierro", seg=10)


def _pico(m, c, rot, largo=1.3):
    m.cil(c, 0.04, largo, "madera", seg=6, rot=rot)
    pts = []
    for i in range(7):
        t = -1 + 2 * i / 6
        pts.append((0.55 * t, largo / 2 - 0.05 - 0.2 * t * t))
    m.prisma(pts + [(x, zz - 0.09 * (1 - abs(x) / 0.55) - 0.01) for x, zz in reversed(pts)], -0.04, 0.04, "acero", "xz",
             c=c, rot=rot)


def _hacha(m, c, rot, largo=1.2):
    m.cil(c, 0.04, largo, "madera_oscura", seg=6, rot=rot)
    m.prisma([(0.0, 0.2), (0.34, 0.3), (0.42, 0.05), (0.34, -0.2), (0.0, -0.08)], -0.03, 0.03, "acero", "xz",
             c=(c[0], c[1], c[2]), rot=(rot[0], rot[1], rot[2])) if False else None
    m.prisma([(0.0, largo / 2 - 0.05), (0.34, largo / 2 + 0.06), (0.42, largo / 2 - 0.2), (0.34, largo / 2 - 0.44),
              (0.0, largo / 2 - 0.32)], -0.03, 0.03, "acero", "xz", c=c, rot=rot)


@modelo(29, "comercial", "edificio_mediano", (10, 8, 7))
def tienda_herramientas(m):
    L = _local(m, 10, 8, 7, vanos=[(0.2, 4.3)], puerta=(-2.2, 2.4), hz=3.9, acento="naranja_p", prof=1.4,
               pared="gris", puerta_mat="oscuro_paneles")
    yf, yb, zs, hz, zt = L["yf"], L["yb"], L["zs"], L["hz"], L["zt"]
    # Panel perforado dentro del escaparate con picos y hachas en miniatura
    m.bloque((0.3, yb - 0.08, 0.9), (4.2, yb, hz - 0.1), "madera_clara")
    _pico(m, (1.0, yb - 0.16, 2.5), (0, 0, 0))
    _pico(m, (2.0, yb - 0.16, 2.4), (0, 180, 0), 1.1)
    _hacha(m, (2.9, yb - 0.16, 2.5), (0, 0, 0))
    _hacha(m, (3.7, yb - 0.16, 2.35), (0, 0, 0), 1.0)
    for x in (1.0, 2.0, 2.9, 3.7):
        m.caja((x, yb - 0.12, 2.3), (0.2, 0.1, 0.04), "hierro")
    # Cajas de herramientas apiladas, una abierta con llaves
    m.caja((1.2, yf + 0.85, 1.12), (1.1, 0.6, 0.44), "rojo_p", bisel=0.03)
    m.caja((1.2, yf + 0.85, 1.36), (1.14, 0.64, 0.06), "oscuro")
    m.barrido([(0.9, yf + 0.85, 1.4), (0.9, yf + 0.85, 1.52), (1.5, yf + 0.85, 1.52), (1.5, yf + 0.85, 1.4)], 0.03,
              "acero", seg=5)
    m.caja((2.9, yf + 0.9, 1.05), (1.3, 0.7, 0.3), "azul_p", bisel=0.03)
    m.caja((2.9, yf + 0.9, 1.4), (1.1, 0.6, 0.36), "amarillo_p", bisel=0.03)
    for i in range(3):
        m.caja((2.6 + 0.3 * i, yf + 0.6, 1.4), (0.2, 0.02, 0.08), "acero")
    for i, ang in enumerate((15, -10, 30)):                      # llaves fijas sobre la tarima
        c = (3.6 + 0.0 * i, yf + 0.55 + 0.0 * i, 0.93)
        m.caja((1.9 + 0.25 * i, yf + 0.55, 0.92), (0.07, 0.6, 0.03), "cromo", rot=(0, 0, ang))
        m.tubo((1.9 + 0.25 * i - 0.3 * math.sin(math.radians(ang)), yf + 0.55 + 0.3 * math.cos(math.radians(ang)), 0.92),
               0.08, 0.03, 0.035, "cromo", seg=8)
    # Fuera: rollo de cable, bidón y tablero de ofertas
    m.tubo((-4.3, yf - 0.5, 0.75), 0.36, 0.5, 0.2, "goma", eje="x", seg=14)
    for sx in (-0.28, 0.28):
        m.cil((-4.3 + sx, yf - 0.5, 0.75), 0.46, 0.05, "madera_clara", eje="x", seg=14)
    m.cil((-4.3, yf - 0.5, 0.75), 0.08, 0.7, "acero", eje="x", seg=8)
    # Rótulo con engranaje luminoso y letras
    m.caja((0, yf - 0.1, hz + 1.0), (8.6, 0.16, 1.0), "oscuro", bisel=0.04)
    m.texto("HERRAMIENTAS", (0.6, yf - 0.22, hz + 1.0), 0.5, 0.1, "neon_naranja")
    m.tubo((-3.6, yf - 0.24, hz + 1.0), 0.3, 0.1, 0.12, "neon_naranja", eje="y", seg=12)
    for k in range(8):
        a = math.radians(45 * k)
        m.caja((-3.6 + 0.36 * math.cos(a), yf - 0.24, hz + 1.0 + 0.36 * math.sin(a)), (0.14, 0.1, 0.12), "neon_naranja",
               rot=(0, -45 * k, 0))
    # Persiana lateral de almacén y azotea con depósito
    m.marco((4.72, 1.2, 2.2), 3.0, 3.4, 0.2, 0.26, "hierro", "x")
    for k in range(9):
        m.caja((4.7, 1.2, 0.75 + 0.34 * k), (0.1, 2.6, 0.3), "chapa", rot=(0, 8, 0), p="persiana")
    m.ventana((-4.72, 1.4, 2.6), 2.0, 1.6, normal="x", sentido=-1, marco="hierro")
    m.ventana((0, 3.72, 2.6), 2.6, 1.5, sentido=1, marco="hierro")
    m.cil((2.6, 1.6, zt + 0.95), 0.7, 1.3, "naranja_p", eje="x", seg=12)
    for sx in (-0.4, 0.4):
        m.caja((2.6 + sx, 1.6, zt + 0.45), (0.12, 1.0, 0.3), "hierro")
    m.barrido([(-2.5, 1.5, zt + 0.3), (-2.5, 1.5, zt + 1.4)], 0.18, "acero", seg=10)
    m.torno((-2.5, 1.5, zt + 1.4), [(0.3, 0), (0.3, 0.06), (0, 0.26)], "hierro", seg=10)


@modelo(30, "comercial", "edificio_mediano", (14, 12, 8))
def tienda_naves(m):
    L = _local(m, 14, 12, 8, vanos=[(-6.3, 2.2)], puerta=(4.3, 3.0), hz=4.4, prof=2.6)
    yf, yb, zs, hz, zt = L["yf"], L["yb"], L["zs"], L["hz"], L["zt"]
    m.bloque((-6.2, yb - 0.08, 0.9), (2.1, yb, hz - 0.1), "oscuro_paneles")
    yc = yf + 1.4
    # Maqueta de nave sobre peana giratoria (pieza aparte)
    m.cil((-3.6, yc, 1.0), 1.3, 0.2, "oscuro", seg=18)
    m.tubo((-3.6, yc, 1.1), 1.32, 0.05, 0.05, "neon", seg=18)
    m.cil((-3.6, yc, 1.5), 0.08, 0.9, "cromo", seg=8)
    P = "maqueta_nave"
    cz = 2.2
    m.torno((-3.6, yc, cz), [(0.0, -1.3), (0.16, -1.05), (0.3, -0.5), (0.34, 0.2), (0.28, 0.9), (0.2, 1.1), (0.0, 1.1)],
            "blanco_liso", seg=10, eje="x", rot=(0, 0, 0), p=P)
    for s in (-1, 1):
        m.prisma([(0.5, 0.0), (0.0, 0.0), (-0.6, s * 1.2), (-0.3, s * 1.25)], -0.05, 0.05, "gris_liso", "xy",
                 c=(-3.6, yc, cz - 0.05), p=P)
        m.cil((-4.35, yc + s * 0.42, cz), 0.14, 0.7, "oscuro", eje="x", seg=8, p=P)
        m.cil((-4.72, yc + s * 0.42, cz), 0.1, 0.06, "neon", eje="x", seg=8)
        m.prisma([(-0.5, 0.0), (-1.0, 0.0), (-1.15, 0.5), (-0.95, 0.5)], -0.03, 0.03, "acento", "xz",
                 c=(-3.6, yc + s * 0.2, cz + 0.2), p=P)
    m.esfera((-3.1, yc, cz + 0.2), 0.26, "cristal_oscuro", seg=10, anillos=6, esc=(1.7, 0.8, 0.7))
    m.prisma([(1.25, -0.03), (1.25, 0.03), (0.2, 0.36), (0.2, -0.36)], -0.03, 0.03, "naranja_p", "xy",
             c=(-3.6, yc, cz + 0.02), p=P) if False else None
    # Piezas sueltas expuestas: tobera, ala, tren de aterrizaje y núcleo de energía
    m.torno((-0.6, yc + 0.2, 0.9), [(0.5, 0), (0.56, 0.1), (0.36, 0.7), (0.4, 0.95), (0.3, 0.95), (0.26, 0.7),
                                    (0.44, 0.12), (0, 0.1)], "hierro", seg=14)
    m.cil((-0.6, yc + 0.2, 1.06), 0.3, 0.06, "neon", seg=12)
    m.prisma([(0, 0), (1.6, 0), (1.2, 1.9), (0.7, 1.9)], -0.06, 0.06, "blanco_liso", "xz", c=(0.3, yb - 0.25, 1.2),
             rot=(-8, 0, 0))
    m.prisma([(0.1, 0.1), (0.5, 0.1), (0.85, 1.8), (0.75, 1.8)], -0.075, 0.075, "acento", "xz", c=(0.3, yb - 0.25, 1.2),
             rot=(-8, 0, 0))
    m.cil((1.4, yc - 0.5, 1.5), 0.07, 1.2, "cromo", seg=8, rot=(0, 12, 0))
    m.cil((1.52, yc - 0.5, 1.1), 0.11, 0.5, "acero", seg=8, rot=(0, 12, 0))
    m.cil((1.28, yc - 0.5, 1.05), 0.24, 0.16, "goma", eje="y", seg=12)
    m.cil((-5.6, yc + 0.3, 1.35), 0.36, 0.9, "cristal", seg=12)
    m.cil((-5.6, yc + 0.3, 1.35), 0.14, 0.8, "neon", seg=8)
    for z in (0.95, 1.85):
        m.cil((-5.6, yc + 0.3, z), 0.4, 0.14, "acero", seg=12)
    # Marquesina curva de chapa sobre el frente y rótulo NAVES con silueta
    m.prisma(arco_pts(1.5, 1.38, 180, 270, 6, yf, hz + 1.3, 1.0, 0.75), -6.7, 6.7, "chapa", "yz")
    for x in (-6.5, 0, 6.5):
        m.prisma(arco_pts(1.4, 1.25, 180, 270, 6, yf, hz + 1.3, 1.0, 0.75), x - 0.06, x + 0.06, "acero", "yz")
    m.caja((-1.0, yf + 0.25, zt + 1.3), (7.0, 0.3, 1.9), "oscuro", bisel=0.05)
    m.texto("NAVES", (-0.2, yf + 0.06, zt + 1.3), 1.0, 0.12, "neon")
    m.prisma([(-0.7, -0.25), (0.7, 0.0), (-0.7, 0.25), (-0.45, 0.0)], -0.05, 0.05, "neon_naranja", "xz",
             c=(-3.6, yf + 0.06, zt + 1.3))
    for x in (-4.3, 2.3):
        m.caja((x, yf + 0.4, zt + 0.5), (0.2, 0.2, 0.5), "acero")
    for sx in (-1, 1):
        m.ventana((sx * 6.72, 2.0, 2.9), 3.4, 1.8, normal="x", sentido=sx, cruz=True)
    m.ventana((0, 5.72, 2.9), 4.0, 1.6, sentido=1, cruz=True)
    m.caja((4.0, 3.0, zt + 0.75), (2.4, 1.8, 0.9), "gris_claro", bisel=0.05)
    for x in (3.4, 4.6):
        m.cil((x, 3.0, zt + 1.22), 0.45, 0.08, "oscuro", seg=10)
