"""Ronda 1: edificios humanos (modelos 1-8). Medidas en studs; el frente mira a -Y."""

import math

from comunes import antena, bandera, barandilla, tira, torreta_deco, ventana


def tienda_humana(g):
    W, D, H = 18.0, 13.0, 9.0
    x, y = W / 2, D / 2
    g.bloque("h_hormigon", (-x - 0.8, -y - 3.2, 0), (x + 0.8, y + 0.6, 0.5), bisel=0.08)
    g.bloque("h_suelo", (-x + 0.6, -y, 0.5), (x - 0.6, y - 0.6, 0.62))
    # Muros con grosor: fondo y laterales; pilares naranjas delante.
    g.bloque("h_blanco", (-x, y - 0.7, 0.5), (x, y, H))
    for s in (-1, 1):
        g.bloque("h_blanco", (s * x, -y + 0.9, 0.5), (s * (x - 0.7), y - 0.7, H))
        g.bloque("h_naranja", (s * x + s * 0.1, -y, 0.5), (s * (x - 1.0), -y + 1.0, H), bisel=0.08)
        ventana(g, s * x, 1.0, 5.0, 3.6, 2.6, "+x" if s > 0 else "-x")
        g.bloque("h_gris", (s * x + s * 0.05, -y + 1.0, 0.5), (s * (x - 0.75), y, 1.3))
    # Dintel, cajón de la persiana y tejado con alero.
    g.bloque("h_blanco", (-x, -y, 7.0), (x, -y + 0.9, H))
    g.bloque("h_gris", (-x + 1.0, -y + 0.1, 6.45), (x - 1.0, -y + 0.85, 7.0))
    g.bloque("h_oscuro", (-x - 0.5, -y - 0.5, H), (x + 0.5, y + 0.4, H + 0.35))
    g.bloque("h_naranja", (-x - 0.6, -y - 0.6, H + 0.35), (x + 0.6, y + 0.5, H + 1.0), bisel=0.1)
    g.bloque("h_hormigon", (-x + 0.2, -y + 0.2, H + 1.0), (x - 0.2, y - 0.3, H + 1.08))
    # Persiana (pieza aparte, enrollada arriba; se baja en Roblox).
    g.pieza("persiana", pivote=(0, -y + 0.45, 6.45))
    for i in range(3):
        g.bloque("h_metal", (-x + 1.05, -y + 0.35, 6.42 - i * 0.3), (x - 1.05, -y + 0.55, 6.18 - i * 0.3))
    g.pieza("cuerpo")
    # Toldo a rayas con faldón y tirantes.
    g.prisma("h_toldo", [(-y - 0.02, 8.9), (-y - 3.2, 7.55), (-y - 3.2, 7.3), (-y - 0.02, 8.65)], W + 1.0, plano="yz")
    g.bloque("h_toldo", (-x - 0.5, -y - 3.28, 6.75), (x + 0.5, -y - 3.1, 7.5))
    for s in (-1, 1):
        g.tubo("h_metal", [(s * (x + 0.3), -y - 0.05, 7.4), (s * (x + 0.3), -y - 3.1, 7.4)], 0.07, lados=5, suave=False)
    # Mostrador con tapa naranja y hueco de paso a la derecha.
    g.bloque("h_blanco_liso", (-x + 1.0, -y + 1.2, 0.62), (4.2, -y + 2.6, 3.4), bisel=0.08)
    g.bloque("h_naranja_liso", (-x + 0.9, -y + 0.9, 3.4), (4.4, -y + 2.8, 3.7), bisel=0.06)
    g.bloque("h_oscuro", (-x + 1.0, -y + 1.15, 0.62), (4.2, -y + 1.25, 1.1))
    tira(g, "h_neon", (-x + 1.2, -y + 1.14, 3.2), (4.0, -y + 1.14, 3.2), 0.14)
    # Caja registradora y productos sobre el mostrador.
    g.caja("h_oscuro", (1.3, 1.0, 0.9), (2.9, -y + 1.9, 4.15), sup=(1, 0.6), bisel=0.05)
    g.caja("h_neon", (0.9, 0.06, 0.45), (2.9, -y + 1.55, 4.3), rot=(-20, 0, 0))
    for i, m in enumerate(("prod_cian", "prod_amarillo", "prod_rojo")):
        g.cil(m, 0.32, 0.8, (-6.5 + i * 0.9, -y + 1.9, 3.7), lados=8)
    # Estantes al fondo con productos.
    g.bloque("h_gris", (-x + 1.2, y - 1.9, 0.62), (x - 1.2, y - 0.7, 1.0))
    colores = ("prod_cian", "prod_rojo", "prod_amarillo", "prod_verde", "h_naranja_liso", "h_blanco_liso")
    for n, z in enumerate((2.6, 4.4, 6.2)):
        g.bloque("h_metal", (-x + 1.2, y - 1.9, z), (x - 1.2, y - 0.7, z + 0.18))
        for i in range(9):
            m = colores[(i * 2 + n * 3) % len(colores)]
            px = -x + 2.2 + i * 1.7
            if (i + n) % 3 == 0:
                g.cil(m, 0.38, 1.0, (px, y - 1.3, z + 0.18), lados=8)
            else:
                g.caja(m, (1.0, 0.8, 0.9 + 0.3 * ((i + n) % 2)), (px, y - 1.3, z + 0.18), base=True, bisel=0.04)
    for px in (-x + 1.3, 0, x - 1.3):
        g.bloque("h_gris", (px - 0.12, y - 1.9, 1.0), (px + 0.12, y - 1.7, 7.4))
    # Cartel (en blanco: el texto se pone en Roblox), luz bajo el dintel y equipos del tejado.
    g.pieza("cartel")
    g.bloque("h_oscuro", (-5.5, -y - 0.75, H + 0.5), (5.5, -y - 0.45, H + 3.0), bisel=0.08)
    g.pieza("cuerpo")
    for px in (-4.5, 4.5):
        g.bloque("h_gris", (px - 0.15, -y - 0.5, H + 0.3), (px + 0.15, -y - 0.2, H + 1.2))
    tira(g, "h_neon", (-5.5, -y - 0.78, H + 0.45), (5.5, -y - 0.78, H + 0.45), 0.14)
    tira(g, "h_neon", (-5.5, -y - 0.78, H + 3.05), (5.5, -y - 0.78, H + 3.05), 0.14)
    tira(g, "h_neon", (-x + 1.2, -y + 0.5, 6.95), (x - 1.2, -y + 0.5, 6.95), 0.12)
    g.caja("h_gris", (3.0, 2.4, 1.3), (4.5, 3.0, H + 1.08), base=True, bisel=0.1)
    g.cil("h_oscuro", 0.9, 0.15, (4.5, 3.0, H + 2.38), lados=10)
    antena(g, (-6.5, 4.0, H + 1.08), 4.0)
    # Cajas apiladas fuera.
    g.caja("tablas", (2.0, 2.0, 2.0), (-x - 0.1 + 1.6, -y - 1.8, 0.5), base=True, bisel=0.06)
    g.caja("tablas", (1.5, 1.5, 1.5), (-x + 1.5, -y - 1.8, 2.5), rot=(0, 0, 20), base=True, bisel=0.06)
    g.ancla("Mostrador", (0, -y + 1.9, 3.7))
    g.ancla("LuzToldo", (0, -y - 1.5, 7.3))
    # Trasera: puerta de servicio, bajante y contador.
    g.bloque("h_gris", (-6.0, y, 0.5), (-3.0, y + 0.15, 6.2))
    g.bloque("h_naranja_liso", (-5.7, y + 0.1, 0.6), (-3.3, y + 0.25, 5.9))
    g.tubo("h_metal", [(6.5, y + 0.3, 0.5), (6.5, y + 0.3, H)], 0.22, lados=6)
    g.caja("h_gris", (1.6, 0.5, 2.2), (3.0, y + 0.25, 4.0), bisel=0.06)
    g.caja("h_neon", (0.6, 0.08, 0.3), (3.0, y + 0.52, 4.5))


def edificio_residencial(g):
    W, D = 20.0, 15.0
    x, y = W / 2, D / 2
    PB, PISO, N = 6.0, 5.0, 4
    H = PB + PISO * N
    g.bloque("h_hormigon", (-x - 1.0, -y - 2.5, 0), (x + 1.0, y + 1.0, 0.5), bisel=0.08)
    # Planta baja (gris) y cuerpo de viviendas (blanco) con esquinas naranjas.
    g.bloque("h_gris", (-x, -y, 0.5), (x, y, PB))
    g.bloque("h_blanco", (-x + 0.3, -y + 0.3, PB), (x - 0.3, y - 0.3, H))
    g.bloque("h_naranja", (-x - 0.1, -y - 0.1, PB - 0.5), (x + 0.1, y + 0.1, PB + 0.1))
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.bloque("h_naranja", (sx * x, sy * y, PB + 0.1), (sx * (x - 1.2), sy * (y - 1.2), H + 0.4), bisel=0.08)
    # Portal: puerta de cristal, marquesina y neón.
    g.bloque("h_oscuro", (-2.6, -y - 0.15, 0.5), (2.6, -y + 0.2, 5.0))
    g.bloque("h_cristal", (-2.2, -y - 0.25, 0.6), (-0.1, -y - 0.1, 4.6))
    g.bloque("h_cristal", (0.1, -y - 0.25, 0.6), (2.2, -y - 0.1, 4.6))
    g.bloque("h_naranja_liso", (-3.4, -y - 2.2, 5.0), (3.4, -y, 5.4), bisel=0.08)
    tira(g, "h_neon", (-3.2, -y - 2.25, 5.0), (3.2, -y - 2.25, 5.0), 0.14)
    for s in (-1, 1):
        ventana(g, s * 6.3, -y, 3.2, 3.6, 2.8)
        g.cil("h_gris", 0.14, 4.5, (s * 3.1, -y - 2.0, 0.5), lados=6)
    # Ventanas y balcones.
    for p in range(N):
        z = PB + PISO * p
        for px in (-6.3, 0.0, 6.3):
            ventana(g, px, -y + 0.3, z + 2.9, 3.0, 2.8)
            ventana(g, px, y - 0.3, z + 2.9, 2.6, 2.4, "+y")
        for s in (-1, 1):
            for py in (-3.4, 3.4):
                ventana(g, s * (x - 0.3), py, z + 2.9, 2.4, 2.4, "+x" if s > 0 else "-x")
        for px in (-6.3, 6.3):
            g.bloque("h_gris", (px - 2.4, -y - 1.6, z + 0.9), (px + 2.4, -y + 0.3, z + 1.2), bisel=0.05)
            barandilla(g, (px - 2.3, -y - 1.5, z + 1.2), (px + 2.3, -y - 1.5, z + 1.2), 1.2, postes=4)
            for s in (-1, 1):
                barandilla(g, (px + s * 2.3, -y - 1.5, z + 1.2), (px + s * 2.3, -y + 0.3, z + 1.2), 1.2, postes=2)
            g.caja("h_naranja_liso", (1.6, 0.5, 0.5), (px - 1.2, -y - 1.15, z + 1.2), base=True)
            g.esfera("hoja_clara", 0.5, (px - 1.2, -y - 1.15, z + 1.9), esc=(1.5, 0.6, 0.8), lados=6, anillos=4)
        tira(g, "h_gris", (-x + 1.2, -y + 0.28, z + 0.3), (x - 1.2, -y + 0.28, z + 0.3), 0.2)
    # Tira vertical de neón en el centro de la fachada y azotea.
    tira(g, "h_neon", (-3.15, -y + 0.25, PB + 0.6), (-3.15, -y + 0.25, H - 0.4), 0.16)
    tira(g, "h_neon", (3.15, -y + 0.25, PB + 0.6), (3.15, -y + 0.25, H - 0.4), 0.16)
    g.bloque("h_oscuro", (-x - 0.2, -y - 0.2, H), (x + 0.2, y + 0.2, H + 0.4))
    for a, b in (((-x, -y, 0), (x, -y + 0.5, 0)), ((-x, y - 0.5, 0), (x, y, 0)),
                 ((-x, -y, 0), (-x + 0.5, y, 0)), ((x - 0.5, -y, 0), (x, y, 0))):
        g.bloque("h_blanco_liso", (a[0], a[1], H + 0.4), (b[0], b[1], H + 1.5))
    g.bloque("h_hormigon", (-x + 0.5, -y + 0.5, H + 0.4), (x - 0.5, y - 0.5, H + 0.5))
    g.caja("h_blanco_liso", (5.0, 4.0, 3.2), (-4.0, 2.0, H + 0.5), base=True, bisel=0.1)
    g.bloque("h_oscuro", (-4.9, -0.1, H + 0.6), (-3.1, 0.05, H + 3.0))
    g.cil("h_metal", 1.6, 2.6, (5.0, 2.5, H + 1.3), lados=12, bisel=0.15)
    for a in range(4):
        g.cil("h_gris", 0.12, 0.8, (5.0 + 1.2 * math.cos(a * 1.57 + 0.8), 2.5 + 1.2 * math.sin(a * 1.57 + 0.8), H + 0.5),
              lados=5)
    for i in range(3):
        g.caja("h_gris", (1.6, 1.4, 1.0), (1.5 + i * 2.2, -3.5, H + 0.5), base=True, bisel=0.08)
        g.cil("h_oscuro", 0.5, 0.1, (1.5 + i * 2.2, -3.5, H + 1.5), lados=8)
    antena(g, (-7.5, -4.5, H + 0.5), 5.0)


def torre_oficinas(g):
    # Tres cuerpos escalonados de muro cortina (ventanas de neón cian horneadas en el atlas).
    g.bloque("h_hormigon", (-13, -13, 0), (13, 13, 0.6), bisel=0.1)
    g.caja("h_gris", (22, 22, 7.0), (0, 0, 0.6), base=True, bisel=0.2)
    # Vestíbulo de cristal con marquesina.
    g.bloque("h_cristal", (-6, -11.2, 0.8), (6, -11.0, 6.2))
    for px in (-6.2, -2.0, 2.0, 6.2):
        g.bloque("h_metal", (px - 0.15, -11.3, 0.6), (px + 0.15, -10.95, 6.4))
    g.bloque("h_naranja_liso", (-7.5, -14.0, 6.4), (7.5, -11.0, 6.9), bisel=0.1)
    tira(g, "h_neon", (-7.3, -14.05, 6.4), (7.3, -14.05, 6.4), 0.16)
    for s in (-1, 1):
        g.cil("h_metal", 0.2, 5.8, (s * 7.0, -13.5, 0.6), lados=6)
    cuerpos = ((9.6, 7.6, 34.0), (7.8, 41.6, 30.0), (6.0, 71.6, 22.0))
    for r, z0, h in cuerpos:
        g.caja("h_muro_cortina", (r * 2, r * 2, h), (0, 0, z0), base=True)
        # Aletas blancas en las esquinas y cornisa naranja.
        for sx in (-1, 1):
            for sy in (-1, 1):
                g.caja("h_blanco_liso", (1.3, 1.3, h + 1.0), (sx * r, sy * r, z0), base=True, bisel=0.12)
                tira(g, "h_neon", (sx * (r + 0.68), sy * (r + 0.68), z0 + 1.0), (sx * (r + 0.68), sy * (r + 0.68), z0 + h - 1.0),
                     0.2)
        g.caja("h_naranja_liso", (r * 2 + 1.6, r * 2 + 1.6, 0.9), (0, 0, z0 + h), base=True, bisel=0.12)
        g.caja("h_oscuro", (r * 2 + 0.6, r * 2 + 0.6, 0.6), (0, 0, z0 - 0.3), base=True)
    # Franja vertical central blanca con neón en la fachada principal.
    for r, z0, h in cuerpos:
        g.bloque("h_blanco_liso", (-0.9, -r - 0.35, z0), (0.9, -r, z0 + h))
        tira(g, "h_neon", (0, -r - 0.38, z0 + 0.8), (0, -r - 0.38, z0 + h - 0.8), 0.22)
    # Coronación: helipuerto, sala de máquinas y antena.
    zt = 94.5
    g.cil("h_gris", 5.2, 0.6, (0, 0, zt), lados=16, bisel=0.1)
    g.toro("h_neon", 4.4, 0.1, (0, 0, zt + 0.62), seg=16, lados=4)
    g.caja("h_blanco_liso", (3.0, 3.0, 3.0), (0, 0, zt + 0.6), base=True, bisel=0.15)
    g.cil("h_metal", 0.55, 5.0, (0, 0, zt + 3.6), lados=8, r2=0.3)
    g.cil("h_metal", 0.25, 9.0, (0, 0, zt + 8.6), lados=6, r2=0.08)
    for k, w in ((5.5, 2.6), (7.5, 1.8), (10.5, 1.2)):
        g.caja("h_metal", (w, 0.12, 0.12), (0, 0, zt + k))
        g.caja("h_metal", (0.12, w, 0.12), (0, 0, zt + k))
    g.esfera("h_luz_roja", 0.35, (0, 0, zt + 17.8), lados=6, anillos=4)
    g.cil("h_naranja_liso", 1.3, 0.5, (0, 0, zt + 3.6), lados=8)
    # Parabólica.
    g.rev("h_blanco_liso", [(0.0, 0.0), (1.2, 0.35), (1.5, 0.8), (1.4, 0.8), (1.1, 0.45), (0.0, 0.15)],
          (3.6, 2.0, zt + 1.9), (60, 0, 30), lados=10)
    g.cil("h_gris", 0.15, 1.6, (3.6, 2.0, zt + 0.6), lados=5)


def hangar_humano(g):
    W, L, R = 52.0, 64.0, 26.0          # ancho, fondo y radio de la bóveda
    x, y = W / 2, L / 2
    PARED = 9.0                          # altura del muro recto antes de la bóveda
    g.bloque("h_hormigon", (-x - 3, -y - 10, 0), (x + 3, y + 2, 0.5), bisel=0.1)
    g.bloque("h_suelo", (-x + 1, -y, 0.5), (x - 1, y - 1, 0.6))
    # Marcas del suelo: círculo de aterrizaje y carril central.
    g.toro("h_neon", 9.0, 0.12, (0, 2, 0.62), seg=24, lados=4)
    g.toro("h_naranja_liso", 11.0, 0.3, (0, 2, 0.6), seg=24, lados=4, pot=4)
    g.bloque("h_naranja_liso", (-0.4, -y - 9, 0.5), (0.4, -11, 0.63))
    for s in (-1, 1):
        g.bloque("h_naranja_liso", (s * 14 - 0.3, -y - 9, 0.5), (s * 14 + 0.3, -y + 6, 0.63))

    def arco(yy, r_ext, r_int, mat, ancho, n=14, a0=0.0, a1=math.pi):
        """Costilla de la bóveda: arco con grosor entre dos radios."""
        ext, inte = [], []
        for i in range(n + 1):
            a = a0 + (a1 - a0) * i / n
            ext.append((r_ext * math.cos(a), PARED + r_ext * 0.62 * math.sin(a)))
            inte.append((r_int * math.cos(a), PARED + r_int * 0.62 * math.sin(a)))
        g.prisma(mat, ext + inte[::-1], ancho, (0, yy, 0), plano="xz")

    # Muros laterales con zócalo naranja y ventanales.
    for s in (-1, 1):
        g.bloque("h_blanco", (s * x, -y, 0.5), (s * (x - 1.0), y, PARED))
        g.bloque("h_naranja", (s * x + s * 0.15, -y, 0.5), (s * (x - 1.1), y, 2.6))
        for i in range(5):
            py = -y + 8.5 + i * 11.8
            ventana(g, s * x, py, 6.0, 7.0, 3.0, "+x" if s > 0 else "-x")
            g.bloque("h_gris", (s * x + s * 0.5, py - 6.4, 0.5), (s * (x - 1.2), py - 5.4, PARED + 0.4), bisel=0.1)
    # Costillas metálicas y paños alternos de chapa y cristal.
    ys = [-y + 0.8 + i * (L - 1.6) / 8 for i in range(9)]
    for yy in ys:
        arco(yy, R + 0.9, R - 0.9, "h_gris", 1.3)
    for i in range(8):
        ym = (ys[i] + ys[i + 1]) / 2
        largo = ys[i + 1] - ys[i] - 1.2
        # Tres tramos por vano: chapa a los lados y lucernario de cristal en la clave.
        arco(ym, R + 0.3, R - 0.15, "h_blanco", largo, n=5, a0=0.0, a1=math.radians(62))
        arco(ym, R + 0.3, R - 0.15, "h_blanco", largo, n=5, a0=math.radians(118), a1=math.pi)
        arco(ym, R + 0.2, R - 0.05, "h_cristal", largo, n=5, a0=math.radians(62), a1=math.radians(118))
    # Largueros a lo largo de la bóveda y luces de neón interiores.
    for a in (62, 118, 30, 150):
        ar = math.radians(a)
        px, pz = (R - 0.9) * math.cos(ar), PARED + (R - 0.9) * 0.62 * math.sin(ar)
        g.bloque("h_gris", (px - 0.35, -y + 0.8, pz - 0.35), (px + 0.35, y - 0.8, pz + 0.35))
        tira(g, "h_neon", (px * 0.985, -y + 2, pz - 0.5), (px * 0.985, y - 2, pz - 0.5), 0.25)
    # Muro del fondo (testero) con ventanal alto.
    fondo = [(R + 0.3) * math.cos(math.pi * i / 14) for i in range(15)]
    g.prisma("h_blanco", [(-x, 0.5), (x, 0.5)] + [((R + 0.3) * math.cos(math.pi * i / 14),
             PARED + (R + 0.3) * 0.62 * math.sin(math.pi * i / 14)) for i in range(15)], 1.0, (0, y - 0.5, 0), plano="xz")
    g.bloque("h_cristal", (-10, y - 1.15, 12), (10, y - 1.0, 19))
    g.bloque("h_cristal", (-10, y + 0.0, 12), (10, y + 0.12, 19))
    for px in (-10, -5, 0, 5, 10):
        g.bloque("h_gris", (px - 0.2, y - 1.25, 11.6), (px + 0.2, y + 0.2, 19.4))
    for pz in (11.6, 19.2):
        g.bloque("h_gris", (-10.2, y - 1.25, pz), (10.2, y + 0.2, pz + 0.4))
    # Frente: tímpano sobre el portón, carril y dos hojas correderas naranjas entreabiertas.
    ALTO = 17.0
    RA = R + 0.3

    def z_arco(px):
        return PARED + 0.62 * math.sqrt(max(RA * RA - px * px, 0.0))

    xs = [-19.0 + 38.0 * i / 10 for i in range(11)]
    g.prisma("h_blanco", [(-19.0, ALTO), (19.0, ALTO)] + [(px, z_arco(px)) for px in reversed(xs)], 1.0, (0, -y + 0.5, 0),
             plano="xz")
    for s in (-1, 1):
        g.bloque("h_blanco", (s * x, -y, 0.5), (s * 19.0, -y + 1.0, PARED))
        g.bloque("h_naranja", (s * x + s * 0.15, -y - 0.15, 0.5), (s * 19.0, -y + 1.0, 2.6))
        lado = [19.0 + (RA - 19.0) * i / 5 for i in range(6)]
        g.prisma("h_blanco", [(s * 19.0, PARED), (s * RA, PARED)] + [(s * px, z_arco(px)) for px in reversed(lado[:-1])], 1.0,
                 (0, -y + 0.5, 0), plano="xz")
    g.bloque("h_gris", (-x, -y - 0.9, ALTO), (x, -y + 1.0, ALTO + 1.2), bisel=0.12)
    tira(g, "h_neon", (-19, -y - 0.95, ALTO + 0.15), (19, -y - 0.95, ALTO + 0.15), 0.2)
    g.pieza("cartel")
    g.bloque("h_oscuro", (-7, -y - 0.3, ALTO + 2.0), (7, -y + 0.5, ALTO + 5.0), bisel=0.1)
    g.pieza("cuerpo")
    for s, nom in ((-1, "puerta_izq"), (1, "puerta_der")):
        g.pieza(nom, pivote=(s * 14.0, -y - 0.45, 0.5))
        x0, x1 = s * 9.0, s * 19.0
        g.bloque("h_naranja", (x0, -y - 0.75, 0.6), (x1, -y - 0.15, ALTO))
        g.bloque("h_oscuro", (x0, -y - 0.82, 0.6), (x1, -y - 0.1, 1.4))
        for k in (0.33, 0.66):
            g.bloque("h_gris", (x0, -y - 0.85, ALTO * k), (x1, -y - 0.1, ALTO * k + 0.5))
        g.bloque("h_cristal", (x0 + s * 2.0, -y - 0.82, 8.0), (x1 - s * 2.0, -y - 0.08, 10.6))
        g.bloque("h_blanco_liso", (x0, -y - 0.84, 0.6), (x0 + s * 0.6, -y - 0.08, ALTO))
        g.pieza("cuerpo")
    g.bloque("h_gris", (-x, -y - 0.9, 0.5), (x, -y, 0.7))
    # Interior: sala de control elevada, pasarela, depósitos, cajas y luces.
    g.bloque("h_gris", (-x + 1, y - 13, 7.0), (-x + 13, y - 1, 7.5), bisel=0.08)
    g.bloque("h_blanco_liso", (-x + 1, y - 13, 7.5), (-x + 13, y - 1, 12.0), bisel=0.12)
    g.bloque("h_cristal", (-x + 2, y - 13.15, 8.6), (-x + 12, y - 13.0, 11.0))
    g.bloque("h_cristal", (-x + 13.0, y - 12, 8.6), (-x + 13.15, y - 2, 11.0))
    tira(g, "h_neon", (-x + 1.5, y - 13.1, 11.6), (-x + 12.8, y - 13.1, 11.6), 0.18)
    for px, py in ((-x + 2, y - 12), (-x + 12, y - 12), (-x + 12, y - 2)):
        g.cil("h_gris", 0.35, 6.5, (px, py, 0.5), lados=8)
    # Escalera a la sala.
    for i in range(10):
        g.bloque("h_gris", (-x + 13 + i * 0.9, y - 5, 6.9 - i * 0.65), (-x + 14 + i * 0.9, y - 2, 7.2 - i * 0.65))
    barandilla(g, (-x + 13, y - 5, 7.5), (-x + 22, y - 5, 1.0), 1.2, postes=4)
    # Depósitos de combustible.
    for i in range(3):
        g.cil("h_naranja_liso", 2.2, 7.0, (x - 5, y - 6 - i * 6, 0.6), lados=12, bisel=0.3)
        g.cil("h_metal", 2.3, 0.5, (x - 5, y - 6 - i * 6, 3.5), lados=12)
        g.tubo("h_metal", [(x - 5, y - 6 - i * 6, 7.6), (x - 5, y - 6 - i * 6, 9.5), (x - 1.6, y - 6 - i * 6, 9.5)], 0.25,
               lados=6)
    # Banco de herramientas y cajas.
    g.bloque("h_gris", (x - 9, -y + 6, 0.6), (x - 2, -y + 9, 3.4), bisel=0.08)
    g.bloque("h_naranja_liso", (x - 9.2, -y + 5.8, 3.4), (x - 1.8, -y + 9.2, 3.7))
    g.bloque("h_oscuro", (x - 2.4, -y + 6, 3.7), (x - 2.0, -y + 9, 7.0))
    tira(g, "h_neon", (x - 2.45, -y + 6.4, 6.6), (x - 2.45, -y + 8.6, 6.6), 0.15)
    for i, (px, py, t) in enumerate(((-x + 5, -y + 8, 3.0), (-x + 8.5, -y + 7, 2.4), (-x + 5.5, -y + 12, 2.4),
                                    (-x + 5.2, -y + 8.2, 2.0))):
        g.caja("h_naranja_liso" if i % 2 else "h_blanco_liso", (t, t, t), (px, py, 0.6 if i < 3 else 3.6), base=True,
               rot=(0, 0, i * 17), bisel=0.1)
    # Puente grúa.
    for s in (-1, 1):
        g.bloque("h_gris", (s * (x - 1.2), -y + 2, PARED - 1.2), (s * (x - 2.2), y - 14, PARED - 0.4))
    g.bloque("h_naranja_liso", (-x + 1.2, -6, PARED - 0.4), (x - 1.2, -4, PARED + 1.0), bisel=0.12)
    g.caja("h_oscuro", (3.0, 2.6, 1.6), (6, -5, PARED - 1.8), bisel=0.1)
    g.cil("h_metal", 0.1, 4.0, (6, -5, PARED - 6.6), lados=5)
    g.toro("h_metal", 0.45, 0.14, (6, -5, PARED - 7.0), (90, 0, 0), seg=8, lados=5, arco=250)
    # Exterior: focos sobre el portón, bolardos y antena.
    for s in (-1, 1):
        g.caja("h_oscuro", (1.6, 1.0, 0.8), (s * 12, -y - 1.2, ALTO + 1.6), bisel=0.08)
        g.caja("h_neon", (1.3, 0.1, 0.5), (s * 12, -y - 1.75, ALTO + 1.55))
        for k in range(3):
            g.cil("h_naranja_liso", 0.45, 2.4, (s * 21.5, -y - 3 - k * 3, 0.5), lados=8, bisel=0.1)
            g.cil("h_neon", 0.47, 0.25, (s * 21.5, -y - 3 - k * 3, 2.4), lados=8)
    antena(g, (x - 6, y - 8, PARED + R * 0.62 * 0.42), 9.0, r=0.2)
    g.ancla("Plataforma", (0, 2, 0.6))
    g.ancla("Gancho", (6, -5, PARED - 7.4))


def forja_humana(g):
    W, D = 17.0, 14.0
    x, y = W / 2, D / 2
    g.bloque("piedra_clara", (-x - 0.5, -y - 0.5, 0), (x + 0.5, y + 0.5, 0.5), bisel=0.1)
    # Cubierta metálica naranja a un agua sobre cuatro postes; muro trasero de ladrillo.
    for sx in (-1, 1):
        for sy in (-1, 1):
            g.caja("h_gris", (0.7, 0.7, 9.6 if sy > 0 else 8.6), (sx * (x - 0.6), (y - 0.6) if sy > 0 else -0.6, 0.5), base=True, bisel=0.08)
    g.bloque("h_ladrillo", (-x + 1.0, y - 0.9, 0.5), (x - 1.0, y - 0.2, 9.0))
    g.prisma("h_naranja", [(-1.8, 8.9), (y + 0.8, 10.3), (y + 0.8, 10.7), (-1.8, 9.3)], W + 1.6, plano="yz")
    for k in (-0.6, 0.0, 0.6):
        g.prisma("h_gris", [(-1.6, 8.65), (y + 0.6, 10.0), (y + 0.6, 10.3), (-1.6, 8.95)], 0.4, (k * x, 0, 0),
                 plano="yz")
    tira(g, "h_neon", (-x + 0.6, -1.85, 8.95), (x - 0.6, -1.85, 8.95), 0.16)
    # Horno: cuerpo de ladrillo con boca en arco, fuego y chimenea que atraviesa el tejado.
    hx, hy = -4.2, y - 3.4
    g.caja("h_ladrillo", (6.0, 5.0, 5.2), (hx, hy, 0.5), base=True, bisel=0.12)
    g.caja("h_ladrillo", (4.6, 3.8, 2.4), (hx, hy, 5.7), base=True, sup=(0.45, 0.5))
    g.cil("h_oscuro", 0.95, 5.5, (hx, hy, 8.1), lados=8, r2=0.8)
    g.cil("h_gris", 1.15, 0.5, (hx, hy, 13.2), lados=8)
    boca = [(-1.5, 1.2), (1.5, 1.2)] + [(1.5 * math.cos(math.pi * i / 6), 2.6 + 1.3 * math.sin(math.pi * i / 6))
                                        for i in range(7)]
    g.prisma("h_oscuro", boca, 0.5, (hx, hy - 2.45, 0.5), plano="xz")
    g.prisma("h_lava", [(a * 0.82, 1.35 + (b - 1.2) * 0.85) for a, b in boca], 0.3, (hx, hy - 2.62, 0.5), plano="xz")
    g.bloque("h_gris", (hx - 2.2, hy - 3.2, 1.3), (hx + 2.2, hy - 2.4, 1.7), bisel=0.06)
    # Fuelle y tubos.
    g.tubo("cobre", [(hx + 3.0, hy, 2.0), (hx + 4.2, hy, 2.0), (hx + 4.2, hy, 6.5), (hx + 2.0, hy, 6.5)], 0.3, lados=6)
    # Yunque sobre tocón.
    ax, ay = 1.5, -4.0
    g.cil("corteza", 1.3, 1.8, (ax, ay, 0.5), lados=10, r2=1.15, suave=False)
    g.cil("madera", 1.15, 0.05, (ax, ay, 2.3), lados=10)
    g.caja("hierro_osc", (1.6, 1.1, 0.4), (ax, ay, 2.35), base=True, bisel=0.05)
    g.caja("hierro_osc", (1.0, 0.7, 0.7), (ax, ay, 2.75), base=True, sup=(1.2, 1.0))
    g.caja("hierro", (2.6, 1.2, 0.6), (ax, ay, 3.45), base=True, bisel=0.08)
    g.cil("hierro", 0.42, 1.4, (ax + 1.3, ay, 3.78), (0, 90, 0), lados=8, r2=0.05)
    # Lingote al rojo y martillo.
    g.caja("h_neon_naranja", (1.1, 0.35, 0.22), (ax - 0.2, ay, 4.16))
    g.tubo("madera_h", [(ax - 1.0, ay - 1.0, 4.15), (ax + 0.6, ay - 0.45, 4.15)], 0.09, lados=5, suave=False)
    g.caja("hierro_osc", (0.45, 0.9, 0.45), (ax + 0.6, ay - 0.45, 4.2), rot=(0, 0, 20))
    # Barril de temple con agua y aros.
    bx, by = 5.8, -4.6
    perfil = [(0.0, 0.0), (1.15, 0.0), (1.4, 1.2), (1.4, 1.9), (1.2, 3.0), (1.05, 3.0), (1.05, 2.6), (0.0, 2.6)]
    g.rev("tablas", perfil, (bx, by, 0.5), lados=12, suave=False)
    g.cil("h_agua", 1.04, 0.1, (bx, by, 3.2), lados=12)
    for z in (1.0, 2.5):
        g.toro("hierro_osc", 1.36 if z < 2 else 1.3, 0.09, (bx, by, 0.5 + z), seg=12, lados=4)
    # Estantería de armas: espadas, hacha y escudo.
    rx = 5.0
    g.bloque("madera_osc", (rx - 2.6, y - 1.3, 0.5), (rx - 2.3, y - 0.9, 7.0))
    g.bloque("madera_osc", (rx + 2.3, y - 1.3, 0.5), (rx + 2.6, y - 0.9, 7.0))
    for z in (2.0, 5.6):
        g.bloque("madera_osc_h", (rx - 2.8, y - 1.5, z), (rx + 2.8, y - 0.9, z + 0.35))
    for i in range(4):
        px = rx - 1.8 + i * 1.2
        g.prisma("acero", [(-0.16, 0), (0.16, 0), (0.16, 3.2), (0, 3.7), (-0.16, 3.2)], 0.07, (px, y - 1.65, 2.4), plano="xz")
        g.caja("oro" if i % 2 else "hierro", (0.8, 0.18, 0.16), (px, y - 1.65, 2.35))
        g.cil("cuero", 0.09, 0.8, (px, y - 1.65, 1.5), lados=6)
    g.cil("hierro", 1.1, 0.16, (rx, y - 1.1, 7.6), (90, 0, 0), lados=12)
    g.cil("h_naranja_liso", 0.4, 0.2, (rx, y - 1.28, 7.6), (90, 0, 0), lados=8)
    # Mesa de trabajo con tenazas y lingotes.
    g.bloque("tablas_h", (-x + 1.2, -y + 1.2, 3.0), (-x + 5.8, -y + 3.6, 3.35))
    for px in (-x + 1.5, -x + 5.5):
        for py in (-y + 1.5, -y + 3.3):
            g.caja("madera_osc", (0.35, 0.35, 2.5), (px, py, 0.5), base=True)
    for i in range(3):
        g.caja("hierro" if i else "cobre", (1.0, 0.45, 0.3), (-x + 2.2 + i * 0.5, -y + 2.2 + i * 0.3, 3.35 + 0.0), base=True,
               rot=(0, 0, i * 25), sup=(0.8, 0.7))
    g.caja("h_oscuro", (0.9, 0.7, 1.6), (-x + 4.9, -y + 2.5, 3.35), base=True, bisel=0.06)
    g.caja("h_neon", (0.6, 0.06, 0.8), (-x + 4.9, -y + 2.12, 4.3))
    # Carbón junto al horno.
    for i in range(6):
        g.roca("h_oscuro", 0.45, (hx + 3.6 + (i % 3) * 0.6, hy - 2.6 - (i // 3) * 0.6, 0.75 + (i // 4) * 0.3), semilla=i, sub=1)
    g.ancla("Yunque", (ax, ay, 4.1))
    g.ancla("Fuego", (hx, hy - 2.6, 2.2))


def cuartel_humano(g):
    W, D, H = 30.0, 20.0, 11.0
    x, y = W / 2, D / 2
    g.bloque("h_hormigon", (-x - 2.5, -y - 4.5, 0), (x + 2.5, y + 2.5, 0.5), bisel=0.1)
    # Búnker de muros inclinados, zócalo y cornisa.
    g.caja("h_gris", (W + 1.6, D + 1.6, 2.2), (0, 0, 0.5), base=True, sup=(0.97, 0.96))
    g.caja("h_blanco", (W, D, H - 2.2), (0, 0, 2.7), base=True, sup=(0.9, 0.86))
    tx, ty = x * 0.9, y * 0.86
    g.caja("h_naranja", (tx * 2 + 0.8, ty * 2 + 0.8, 0.9), (0, 0, H + 0.5), base=True, bisel=0.12)
    g.caja("h_oscuro", (tx * 2 - 0.6, ty * 2 - 0.6, 0.5), (0, 0, H + 1.4), base=True)
    # Almenas / parapeto de la azotea.
    for i in range(7):
        px = -tx + 1.5 + i * (tx * 2 - 3.0) / 6
        for s in (-1, 1):
            g.caja("h_blanco_liso", (2.2, 0.8, 1.3), (px, s * (ty - 0.4), H + 1.4), base=True, bisel=0.08)
    for i in range(4):
        py = -ty + 2.6 + i * (ty * 2 - 5.2) / 3
        for s in (-1, 1):
            g.caja("h_blanco_liso", (0.8, 2.2, 1.3), (s * (tx - 0.4), py, H + 1.4), base=True, bisel=0.08)
    # Entrada blindada con rampa y contrafuertes.
    g.caja("h_gris", (9.0, 3.0, 8.0), (0, -y - 0.2, 0.5), base=True, sup=(0.85, 0.8), desv=(0, 0.3), bisel=0.12)
    g.bloque("h_oscuro", (-2.6, -y - 1.85, 0.5), (2.6, -y - 1.4, 6.2))
    g.bloque("h_naranja_liso", (-2.2, -y - 1.95, 0.6), (-0.08, -y - 1.75, 5.8))
    g.bloque("h_naranja_liso", (0.08, -y - 1.95, 0.6), (2.2, -y - 1.75, 5.8))
    tira(g, "h_neon", (-2.6, -y - 1.9, 6.45), (2.6, -y - 1.9, 6.45), 0.2)
    g.caja("h_hormigon", (7.0, 3.0, 0.5), (0, -y - 3.0, 0.5), base=True, sup=(1, 0.2), desv=(0, 1.2))
    # Emblema (escudo) sobre la puerta.
    g.cil("h_blanco_liso", 1.1, 0.25, (0, -y - 1.25, 7.6), (78, 0, 0), lados=6)
    g.cil("h_naranja_liso", 0.7, 0.3, (0, -y - 1.3, 7.6), (78, 0, 0), lados=6)
    # Ventanas estrechas (troneras) con neón.
    for s in (-1, 1):
        for px in (7.0, 11.0):
            g.caja("h_oscuro", (1.6, 0.6, 3.4), (s * px, -y + 0.75, 6.0), rot=(-8, 0, 0))
            g.caja("h_cristal", (1.0, 0.6, 2.6), (s * px, -y + 0.6, 6.0), rot=(-8, 0, 0))
        for py in (-4.0, 4.0):
            g.caja("h_oscuro", (0.6, 1.6, 3.4), (s * (x - 0.55), py, 6.0), rot=(0, -s * 6, 0))
            g.caja("h_cristal", (0.6, 1.0, 2.6), (s * (x - 0.42), py, 6.0), rot=(0, -s * 6, 0))
        tira(g, "h_neon", (s * 5.4, -y + 0.25, 3.2), (s * 13.6, -y + 0.25, 3.2), 0.18)
    # Torres de esquina con torretas decorativas.
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = sx * (x + 0.4), sy * (y + 0.4)
            g.cil("h_gris", 3.0, 13.0, (px, py, 0.5), lados=8, r2=2.6, suave=False)
            g.cil("h_naranja_liso", 3.1, 0.7, (px, py, 13.5), lados=8, suave=False)
            g.cil("h_oscuro", 2.7, 0.3, (px, py, 14.2), lados=8, suave=False)
            g.cil("h_neon", 2.66, 0.25, (px, py, 9.0), lados=8, suave=False)
            torreta_deco(g, (px, py, 14.5), 1.0, giro=(0 if sy < 0 else 180) + sx * (35 if sy < 0 else -35))
    # Azotea: puesto de mando, radar y bandera.
    g.caja("h_blanco_liso", (8.0, 6.0, 3.6), (-4.0, 1.0, H + 1.9), base=True, sup=(0.85, 0.8), bisel=0.12)
    g.caja("h_cristal", (6.0, 0.2, 1.4), (-4.0, -1.75, H + 3.9), rot=(-10, 0, 0))
    g.caja("h_naranja_liso", (7.0, 5.0, 0.4), (-4.0, 1.0, H + 5.5), base=True)
    g.cil("h_gris", 0.35, 3.0, (-6.0, 2.0, H + 5.9), lados=6)
    g.rev("h_blanco_liso", [(0.0, 0.0), (1.6, 0.4), (2.1, 1.0), (1.95, 1.0), (1.5, 0.55), (0.0, 0.2)],
          (-6.0, 2.0, H + 9.2), (55, 0, -30), lados=10)
    bandera(g, (6.5, 1.0, H + 1.9), alto=13.0, ancho=6.0, caida=3.6)
    g.caja("h_gris", (2.4, 2.4, 0.8), (6.5, 1.0, H + 1.9), base=True, bisel=0.1)
    # Barreras antitanque y focos.
    for s in (-1, 1):
        g.caja("h_hormigon", (4.0, 1.4, 2.0), (s * 9.0, -y - 3.0, 0.5), base=True, sup=(0.9, 0.35), bisel=0.08)
        g.caja("h_naranja_liso", (4.02, 0.5, 0.4), (s * 9.0, -y - 3.0, 1.2))
    g.ancla("Puerta", (0, -y - 2.0, 0.5))


def hospital_humano(g):
    W, D = 26.0, 18.0
    x, y = W / 2, D / 2
    PISO, N = 6.0, 3
    H = 0.5 + PISO * N
    g.bloque("h_hormigon", (-x - 2, -y - 5, 0), (x + 2, y + 1.5, 0.5), bisel=0.1)
    g.bloque("h_blanco", (-x, -y, 0.5), (x, y, H))
    # Fachada: gran paño de cristal central y franjas azul cian por planta.
    g.bloque("h_cristal", (-5.0, -y - 0.3, 0.7), (5.0, -y - 0.12, H - 0.8))
    for px in (-5.2, -1.7, 1.7, 5.2):
        g.bloque("h_metal", (px - 0.15, -y - 0.4, 0.5), (px + 0.15, -y + 0.1, H - 0.5))
    for p in range(N + 1):
        z = 0.5 + PISO * p
        g.bloque("h_metal", (-5.2, -y - 0.4, max(z - 0.2, 0.5)), (5.2, -y + 0.1, z + 0.2 if p < N else z - 0.5))
    for p in range(N):
        z = 0.5 + PISO * p
        for s in (-1, 1):
            for px in (7.4, 10.7):
                ventana(g, s * px, -y, z + 3.3, 2.2, 2.8)
            for py in (-5.0, 0.0, 5.0):
                ventana(g, s * x, py, z + 3.3, 3.0, 2.8, "+x" if s > 0 else "-x")
        for px in (-9.0, -3.0, 3.0, 9.0):
            ventana(g, px, y, z + 3.3, 3.4, 2.8, "+y")
        if p:
            g.bloque("h_cristal" if False else "h_gris", (-x - 0.15, -y - 0.15, z - 0.25), (x + 0.15, y + 0.15, z + 0.25))
    tira(g, "h_neon_azul", (-x - 0.2, -y - 0.2, H - 0.9), (-5.6, -y - 0.2, H - 0.9), 0.3)
    tira(g, "h_neon_azul", (5.6, -y - 0.2, H - 0.9), (x + 0.2, -y - 0.2, H - 0.9), 0.3)
    # Entrada de urgencias: marquesina, puertas y rampa.
    g.bloque("h_blanco_liso", (-7.0, -y - 4.5, 5.6), (7.0, -y, 6.3), bisel=0.12)
    tira(g, "h_neon_azul", (-6.8, -y - 4.56, 5.75), (6.8, -y - 4.56, 5.75), 0.2)
    for s in (-1, 1):
        g.cil("h_metal", 0.3, 5.1, (s * 6.2, -y - 3.8, 0.5), lados=8)
    g.bloque("h_oscuro", (-2.6, -y - 0.5, 0.5), (2.6, -y - 0.2, 5.2))
    g.bloque("h_blanco_liso", (-2.3, -y - 0.62, 0.6), (-0.06, -y - 0.42, 4.9))
    g.bloque("h_blanco_liso", (0.06, -y - 0.62, 0.6), (2.3, -y - 0.42, 4.9))

    def cruz(mat, c, t, fondo, eje="y"):
        cx, cy, cz = c
        if eje == "y":
            g.caja(mat, (t * 3, fondo, t), (cx, cy, cz))
            g.caja(mat, (t, fondo, t * 3), (cx, cy, cz))
        else:
            g.caja(mat, (t * 3, t, fondo), (cx, cy, cz))
            g.caja(mat, (t, t * 3, fondo), (cx, cy, cz))

    # Cruz azul de neón: sobre la marquesina, en un tótem de la azotea y en el helipuerto.
    cruz("h_blanco_liso", (0, -y - 4.3, 8.3), 1.25, 0.35)
    cruz("h_neon_azul", (0, -y - 4.52, 8.3), 0.95, 0.2)
    g.bloque("h_gris", (-0.3, -y - 4.3, 6.3), (0.3, -y - 4.0, 6.6))
    # Azotea: peto, tótem con cruz, helipuerto y máquinas.
    g.bloque("h_gris", (-x - 0.3, -y - 0.3, H), (x + 0.3, y + 0.3, H + 0.5))
    for a, b in (((-x, -y), (x, -y + 0.5)), ((-x, y - 0.5), (x, y)), ((-x, -y), (-x + 0.5, y)), ((x - 0.5, -y), (x, y))):
        g.bloque("h_blanco_liso", (a[0], a[1], H + 0.5), (b[0], b[1], H + 1.6))
    g.bloque("h_hormigon", (-x + 0.5, -y + 0.5, H + 0.5), (x - 0.5, y - 0.5, H + 0.6))
    g.caja("h_blanco_liso", (6.0, 1.2, 7.0), (-7.0, -y + 1.6, H + 0.6), base=True, bisel=0.15)
    cruz("h_neon_azul", (-7.0, -y + 0.92, H + 4.2), 1.3, 0.2)
    cruz("h_neon_azul", (-7.0, -y + 2.28, H + 4.2), 1.3, 0.2)
    g.cil("h_gris", 5.5, 0.5, (6.0, 1.0, H + 0.6), lados=16, bisel=0.1)
    g.toro("h_neon_azul", 4.8, 0.12, (6.0, 1.0, H + 1.12), seg=16, lados=4)
    cruz("h_blanco_liso", (6.0, 1.0, H + 1.13), 1.4, 0.08, eje="z")
    for i in range(2):
        g.caja("h_gris", (2.6, 2.2, 1.6), (-9.0 + i * 3.4, 5.0, H + 0.6), base=True, bisel=0.1)
        g.cil("h_oscuro", 0.8, 0.12, (-9.0 + i * 3.4, 5.0, H + 2.2), lados=8)
    antena(g, (-2.0, 6.0, H + 0.6), 5.0)
    # Bancos y jardineras en la acera.
    for s in (-1, 1):
        g.caja("h_blanco_liso", (4.0, 1.6, 1.2), (s * 10.0, -y - 2.6, 0.5), base=True, bisel=0.1)
        g.esfera("hoja", 1.0, (s * 10.0, -y - 2.6, 2.0), esc=(1.8, 0.7, 0.8), lados=8, anillos=4)
    g.ancla("Entrada", (0, -y - 1.0, 0.5))


def centro_mando(g):
    R = 14.0
    N = 16
    g.cil("h_hormigon", R + 3.0, 0.5, (0, 0, 0), lados=N, bisel=0.1, suave=False)
    # Anillo exterior: zócalo, muro con banda de cristal y cornisa naranja.
    g.cil("h_gris", R + 0.4, 2.4, (0, 0, 0.5), lados=N, r2=R, suave=False)
    g.cil("h_blanco", R, 3.0, (0, 0, 2.9), lados=N, suave=False)
    g.cil("h_cristal", R + 0.08, 2.6, (0, 0, 5.9), lados=N, suave=False)
    g.cil("h_blanco", R, 1.6, (0, 0, 8.5), lados=N, suave=False)
    g.cil("h_naranja", R + 0.7, 0.9, (0, 0, 10.1), lados=N, bisel=0.15, suave=False)
    g.toro("h_neon", R + 0.15, 0.14, (0, 0, 8.6), seg=N, lados=4)
    for i in range(N):
        a = 2 * math.pi * (i + 0.5) / N
        if abs(math.sin(a) + 1) < 0.2:
            continue
        with g.grupo((0, 0, 0), (0, 0, math.degrees(a))):
            g.caja("h_gris", (1.4, 1.2, 10.6), (R * 0.985 + 0.3, 0, 0.5), base=True, sup=(0.6, 0.8), desv=(-0.3, 0), bisel=0.08)
            g.caja("h_neon", (0.12, 0.3, 3.0), (R * 0.985 + 0.95, 0, 3.6))
    # Entrada: pórtico que sobresale, puerta y escalones.
    g.caja("h_gris", (8.0, 4.0, 8.0), (0, -R - 0.6, 0.5), base=True, sup=(0.85, 0.9), bisel=0.15)
    g.bloque("h_oscuro", (-2.4, -R - 2.75, 0.5), (2.4, -R - 2.4, 6.0))
    g.bloque("h_cristal", (-2.1, -R - 2.85, 0.6), (-0.06, -R - 2.65, 5.7))
    g.bloque("h_cristal", (0.06, -R - 2.85, 0.6), (2.1, -R - 2.65, 5.7))
    g.bloque("h_naranja_liso", (-4.4, -R - 3.3, 6.4), (4.4, -R - 2.2, 7.2), bisel=0.1)
    tira(g, "h_neon", (-4.2, -R - 3.35, 6.3), (4.2, -R - 3.35, 6.3), 0.16)
    g.pieza("cartel")
    g.bloque("h_oscuro", (-3.0, -R - 2.9, 7.5), (3.0, -R - 2.6, 9.1), bisel=0.08)
    g.pieza("cuerpo")
    # Cubierta: terraza anular, tambor y cúpula de cristal con nervios.
    g.cil("h_oscuro", R - 0.4, 0.4, (0, 0, 11.0), lados=N, suave=False)
    for i in range(N):
        a0 = 2 * math.pi * i / N
        a1 = 2 * math.pi * (i + 1) / N
        barandilla(g, ((R - 0.8) * math.cos(a0), (R - 0.8) * math.sin(a0), 11.4),
                   ((R - 0.8) * math.cos(a1), (R - 0.8) * math.sin(a1), 11.4), 1.2, postes=2, r=0.06)
    RD = 9.0
    g.cil("h_blanco_liso", RD + 0.8, 1.6, (0, 0, 11.4), lados=N, r2=RD + 0.3, suave=False)
    g.toro("h_neon", RD + 0.62, 0.12, (0, 0, 12.4), seg=N, lados=4)
    g.cil("h_suelo", RD - 0.2, 0.3, (0, 0, 12.8), lados=N)
    # Consolas interiores en corro, mesa holográfica central y sillas.
    for i in range(8):
        a = 2 * math.pi * i / 8 + 0.39
        with g.grupo((0, 0, 13.1), (0, 0, math.degrees(a) - 90)):
            g.caja("h_gris", (2.6, 1.3, 1.4), (0, 6.6, 0), base=True, sup=(1, 0.6), desv=(0, 0.2), bisel=0.06)
            g.caja("h_oscuro", (2.3, 0.2, 1.3), (0, 7.05, 2.05), rot=(-15, 0, 0))
            g.caja("h_neon" if i % 3 else "h_neon_naranja", (2.0, 0.06, 1.0), (0, 6.92, 2.05), rot=(-15, 0, 0))
            g.caja("h_neon", (2.0, 0.5, 0.05), (0, 6.3, 1.43), rot=(-12, 0, 0))
            g.cil("h_oscuro", 0.45, 0.9, (0, 4.9, 0), lados=6)
            g.caja("h_naranja_liso", (0.9, 0.25, 1.0), (0, 4.5, 0.9), base=True)
    g.cil("h_gris", 2.2, 1.3, (0, 0, 13.1), lados=12, r2=2.5, bisel=0.08)
    g.cil("h_neon", 2.1, 0.08, (0, 0, 14.42), lados=12)
    g.rev("h_neon", [(0.0, 0.0), (0.9, 0.8), (1.1, 1.6), (0.7, 2.4), (0.0, 2.9)], (0, 0, 15.0), lados=8, suave=False)
    # Cúpula (cristal con grosor) y nervios metálicos.
    perf_ext = [(RD * math.cos(math.radians(a)), RD * 0.8 * math.sin(math.radians(a))) for a in range(0, 90, 15)] + [(0.0, RD * 0.8)]
    perf_int = [((RD - 0.25) * math.cos(math.radians(a)), (RD - 0.25) * 0.8 * math.sin(math.radians(a)))
                for a in range(75, -1, -15)]
    g.rev("h_cristal", [(RD - 0.25, 0.0)] + perf_ext[0:1] + perf_ext[1:] + [(0.0, (RD - 0.25) * 0.8)] + perf_int[0:0],
          (0, 0, 13.0), lados=N, tapas=(False, False))
    for i in range(8):
        a = 2 * math.pi * i / 8
        pts = [((RD + 0.1) * math.cos(math.radians(b)) * math.cos(a), (RD + 0.1) * math.cos(math.radians(b)) * math.sin(a),
                13.0 + (RD + 0.1) * 0.8 * math.sin(math.radians(b))) for b in range(0, 91, 15)]
        g.tubo("h_metal", pts, 0.2, lados=4, suave=False)
    g.toro("h_metal", RD * math.cos(math.radians(45)) + 0.1, 0.16, (0, 0, 13.0 + RD * 0.8 * math.sin(math.radians(45))), seg=N,
           lados=4)
    g.cil("h_naranja_liso", 1.4, 0.7, (0, 0, 13.0 + RD * 0.8 - 0.1), lados=8, bisel=0.1)
    antena(g, (0, 0, 13.5 + RD * 0.8), 6.0, r=0.2)
    # Parabólicas en la terraza.
    for a in (0.6, 2.6):
        px, py = (R - 3.0) * math.cos(a), (R - 3.0) * math.sin(a)
        g.cil("h_gris", 0.25, 2.0, (px, py, 11.4), lados=6)
        g.rev("h_blanco_liso", [(0.0, 0.0), (1.3, 0.35), (1.7, 0.9), (1.55, 0.9), (1.2, 0.5), (0.0, 0.18)],
              (px, py, 13.6), (50, 0, math.degrees(a) - 90), lados=10)
    g.ancla("Puerta", (0, -R - 3.0, 0.5))
    g.ancla("Holograma", (0, 0, 16.5))


MODELOS = [
    ("tienda_humana", "edificios_humanos", 5000, tienda_humana),
    ("edificio_residencial", "edificios_humanos", 10000, edificio_residencial),
    ("torre_oficinas", "edificios_humanos", 10000, torre_oficinas),
    ("hangar_humano", "edificios_humanos", 15000, hangar_humano),
    ("forja_humana", "edificios_humanos", 5000, forja_humana),
    ("cuartel_humano", "edificios_humanos", 10000, cuartel_humano),
    ("hospital_humano", "edificios_humanos", 10000, hospital_humano),
    ("centro_mando", "edificios_humanos", 10000, centro_mando),
]
