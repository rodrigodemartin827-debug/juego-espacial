"""Ronda 12: piezas de nave modular II (modelos 71-77): motores, armas, escudo, estabilizador y tren de aterrizaje.
Misma convención que la ronda 11: el origen es el punto de acople; los motores expulsan hacia +Y."""

import math

from comunes import tira
from lib import anillo_y


def _tobera(g, R, y0, largo, lados=12):
    g.rev("n_tobera", [(R * 0.62, y0), (R, y0 + largo), (R * 0.9, y0 + largo), (R * 0.54, y0 + 0.1)], (0, 0, 0), (-90, 0, 0), lados=lados,
          tapas=(False, False))
    g.rev("h_neon", [(0.0, y0 + 0.02), (R * 0.5, y0 + 0.08), (R * 0.76, y0 + largo * 0.72), (0.0, y0 + largo * 0.9)], (0, 0, 0), (-90, 0, 0),
          lados=10)


def motor_avanzado(g):
    # Carcasa ancha con doble tobera y tiras de neón.
    g.caja("h_oscuro", (2.6, 0.35, 1.5), (0, 0.17, 0), bisel=0.08)
    g.loft("n_casco", [anillo_y(0.3 + t * 3.6, 2.3 * kx, 1.25 * kz, 12, pot=3.4) for t, kx, kz in ((0, 0.75, 0.75), (0.2, 1, 1), (0.8, 1, 1), (1, 0.9, 0.88))])
    g.loft("h_naranja_liso", [anillo_y(1.3 + d, 2.34, 1.28, 12, pot=3.4) for d in (0, 0.35)])
    g.caja("h_oscuro", (4.2, 0.3, 2.1), (0, 3.95, 0), bisel=0.06)
    for s in (-1, 1):
        with g.grupo((s * 1.15, 0, 0)):
            _tobera(g, 1.0, 3.9, 1.7)
            g.toro("h_metal", 0.72, 0.1, (0, 4.2, 0), (90, 0, 0), seg=12, lados=4)
        tira(g, "h_neon", (s * 2.32, 0.9, 0.0), (s * 2.32, 3.4, 0.0), 0.12)
        g.caja("h_gris", (0.5, 2.0, 0.9), (s * 2.3, 2.6, 0), sup=(0.5, 0.8), bisel=0.05)
        g.ancla("Escape" + ("Der" if s > 0 else "Izq"), (s * 1.15, 5.6, 0))
    for k in range(4):
        g.caja("h_gris", (1.6, 0.18, 0.12), (0, 1.9 + k * 0.4, 1.27))
    g.caja("h_neon", (1.0, 1.4, 0.06), (0, 2.5, -1.27))
    g.ancla("Acople", (0, 0, 0))


def motor_turbo(g):
    # Motor enorme: campana grande con aletas, cuatro impulsores auxiliares y anillos de energía.
    R = 2.2
    g.cil("h_oscuro", R * 0.6, 0.4, (0, 0, 0), (-90, 0, 0), lados=12)
    g.rev("n_casco", [(R * 0.62, 0.35), (R * 0.95, 1.2), (R, 2.2), (R, 4.6), (R * 0.82, 5.4), (R * 0.6, 5.4), (0.0, 5.3)], (0, 0, 0), (-90, 0, 0),
          lados=14)
    for y in (1.8, 4.4):
        g.toro("h_naranja_liso", R * 1.0, 0.14, (0, y, 0), (90, 0, 0), seg=14, lados=4)
    g.toro("h_neon", R * 1.03, 0.09, (0, 3.1, 0), (90, 0, 0), seg=14, lados=4)
    _tobera(g, R * 1.12, 5.3, 3.4, lados=14)
    for y, k in ((6.4, 0.86), (7.6, 1.02)):
        g.toro("h_metal", R * k, 0.12, (0, y, 0), (90, 0, 0), seg=14, lados=4)
    for i in range(8):
        a = math.radians(45 * i)
        ca, sa = math.cos(a), math.sin(a)
        # Aletas de refrigeración alrededor de la campana.
        g.prisma("h_gris", [(5.5, R * 0.75), (8.4, R * 1.2), (8.6, R * 1.5), (6.0, R * 1.25)], 0.14, (0, 0, 0), (0, -math.degrees(a), 0), plano="yz")
        if i % 2 == 1:
            with g.grupo((R * 1.12 * ca, 0, R * 1.12 * sa)):
                g.rev("n_casco", [(0.0, 1.0), (0.5, 1.4), (0.55, 4.2), (0.42, 4.6), (0.0, 4.6)], (0, 0, 0), (-90, 0, 0), lados=8)
                _tobera(g, 0.5, 4.5, 1.2, lados=8)
                g.toro("h_naranja_liso", 0.56, 0.06, (0, 2.2, 0), (90, 0, 0), seg=8, lados=4)
        else:
            g.caja("h_neon", (0.14, 1.8, 0.14), (R * 1.02 * ca, 3.2, R * 1.02 * sa))
            g.caja("h_oscuro", (0.5, 2.4, 0.5), (R * 1.0 * ca, 3.2, R * 1.0 * sa), rot=(0, -math.degrees(a), 0), bisel=0.06)
    # Turbina visible por delante.
    for i in range(6):
        g.caja("h_metal", (R * 0.5, 0.1, 0.28), (0, 0.42, 0), rot=(0, 60 * i, 0)) if False else None
    g.ancla("Acople", (0, 0, 0))
    g.ancla("Escape", (0, 8.7, 0))


def arma_laser_nave(g):
    # Torreta láser: base de acople (origen), cabeza giratoria y dos cañones con bobinas de neón. Dispara hacia -Y.
    g.cil("h_gris", 0.9, 0.3, (0, 0, 0), lados=10, bisel=0.06)
    g.cil("h_oscuro", 0.6, 0.35, (0, 0, 0.3), lados=10)
    g.pieza("cabeza", pivote=(0, 0, 0.65))
    g.caja("n_casco", (1.5, 1.9, 0.9), (0, 0.1, 0.65), base=True, sup=(0.75, 0.8), bisel=0.1)
    g.caja("h_naranja_liso", (1.56, 0.4, 0.4), (0, 0.75, 0.95))
    g.esfera("h_neon", 0.2, (0, -0.2, 1.55), lados=6, anillos=4)
    for s in (-1, 1):
        g.cil("h_gris", 0.3, 0.3, (s * 0.8, 0, 1.05), (0, s * 90, 0), lados=8)
    g.pieza("canones", pivote=(0, -0.3, 1.05), padre="cabeza")
    for s in (-1, 1):
        g.caja("h_gris", (0.5, 1.0, 0.5), (s * 0.42, -1.1, 1.05), bisel=0.06)
        g.cil("h_oscuro", 0.13, 2.6, (s * 0.42, -1.5, 1.05), (90, 0, 0), lados=8)
        for k in range(4):
            g.toro("h_neon", 0.19, 0.045, (s * 0.42, -2.0 - k * 0.42, 1.05), (90, 0, 0), seg=8, lados=4)
        g.cil("h_metal", 0.2, 0.4, (s * 0.42, -3.9, 1.05), (90, 0, 0), lados=8, r2=0.26)
        g.cil("h_neon", 0.14, 0.06, (s * 0.42, -4.3, 1.05), (90, 0, 0), lados=8)
        g.ancla("Boca" + ("Der" if s > 0 else "Izq"), (s * 0.42, -4.4, 1.05))
    g.pieza("cuerpo")
    g.ancla("Acople", (0, 0, 0))


def arma_misiles_nave(g):
    # Lanzamisiles: pilón de acople (origen arriba) y contenedor de seis tubos con las ojivas asomando.
    g.caja("h_gris", (0.8, 1.6, 0.5), (0, 0, -0.25), sup=(1.5, 1.2), bisel=0.06)
    g.caja("n_casco", (3.0, 4.2, 2.0), (0, 0, -1.5), bisel=0.14)
    g.caja("h_naranja_liso", (3.06, 0.5, 2.06), (0, 0.9, -1.5))
    g.caja("h_oscuro", (2.7, 0.2, 1.7), (0, -2.1, -1.5))
    n = 0
    for fila in (-1, 1):
        for col in (-1, 0, 1):
            px, pz = col * 0.86, -1.5 + fila * 0.44
            g.cil("h_oscuro", 0.36, 0.3, (px, -2.05, pz), (90, 0, 0), lados=8)
            if n != 4:      # un tubo vacío: ya ha disparado
                g.pieza(f"misil{n + 1}", pivote=(px, -1.9, pz))
                g.rev("h_blanco_liso", [(0.26, 0.0), (0.26, 0.5), (0.0, 1.1)], (px, -1.75, pz), (90, 0, 0), lados=8)
                g.cil("h_luz_roja" if False else "prod_rojo", 0.27, 0.14, (px, -1.95, pz), (90, 0, 0), lados=8)
                g.pieza("cuerpo")
            n += 1
    for s in (-1, 1):
        tira(g, "h_neon", (s * 1.52, -1.4, -1.5), (s * 1.52, 0.4, -1.5), 0.1)
    g.caja("h_oscuro", (2.6, 0.25, 1.6), (0, 2.15, -1.5), bisel=0.05)
    g.ancla("Acople", (0, 0, 0))
    g.ancla("Salida", (0, -2.9, -1.5))


def escudo_nave(g):
    # Generador de escudo: emisor (origen en su base) y domo semitransparente (pieza aparte).
    g.cil("h_gris", 1.5, 0.35, (0, 0, 0), lados=12, bisel=0.08)
    g.cil("n_casco", 1.15, 0.7, (0, 0, 0.35), lados=12, r2=0.85)
    g.toro("h_naranja_liso", 1.2, 0.1, (0, 0, 0.4), seg=12, lados=4)
    g.toro("h_neon", 0.95, 0.07, (0, 0, 1.06), seg=12, lados=4)
    g.cil("h_oscuro", 0.5, 0.5, (0, 0, 1.05), lados=8)
    g.esfera("h_neon", 0.55, (0, 0, 2.0), lados=10, anillos=6)
    for i in range(3):
        a = math.radians(120 * i + 30)
        g.tubo("h_metal", [(1.0 * math.cos(a), 1.0 * math.sin(a), 0.9), (1.25 * math.cos(a), 1.25 * math.sin(a), 1.9),
                           (0.75 * math.cos(a), 0.75 * math.sin(a), 2.7)], [0.14, 0.11, 0.05], lados=5)
    g.pieza("domo", pivote=(0, 0, 0))
    perfil = [(4.0 * math.cos(math.radians(a)), 4.0 * math.sin(math.radians(a))) for a in range(0, 90, 15)] + [(0.0, 4.0)]
    interior = [(3.85 * math.cos(math.radians(a)), 3.85 * math.sin(math.radians(a))) for a in range(75, -1, -15)]
    g.rev("h_cristal", perfil + [(0.0, 3.85)] + interior, (0, 0, 0.05), lados=16, tapas=(False, False))
    g.pieza("cuerpo")
    g.ancla("Acople", (0, 0, 0))
    g.extra["escudo"] = {"radio_domo": 4.0}


def estabilizador(g):
    # Aleta trasera en flecha: origen en la base, crece hacia +Z y hacia la cola (+Y).
    g.caja("h_gris", (0.7, 3.4, 0.4), (0, 0.6, 0.2), sup=(0.7, 0.9), bisel=0.06)
    secs = []
    for t, cuerda, grosor in ((0.0, 3.2, 0.42), (0.5, 2.4, 0.3), (0.9, 1.5, 0.2), (1.0, 1.0, 0.12)):
        y = 0.5 + t * 2.2
        z = 0.3 + t * 4.2
        secs.append([(grosor / 2 * math.sin(a) * (1 if math.cos(a) > 0 else 1 - 0.75 * -math.cos(a)), y - cuerda / 2 * math.cos(a), z)
                     for a in [2 * math.pi * i / 10 for i in range(10)]])
    g.loft("n_casco", secs)
    g.loft("h_naranja_liso", [[(p[0] * 1.15, p[1] + (p[1] - (0.5 + t * 2.2)) * 0.03, p[2]) for p in s] for t, s in ((0.9, secs[2]),)] +
           [[(p[0] * 1.2, p[1], p[2] + 0.06) for p in secs[3]]])
    for s in (-1, 1):
        g.caja("h_neon", (0.06, 0.12, 2.6), (s * 0.17, 0.75, 1.9), rot=(-27.5, 0, 0))
    g.caja("n_panza", (0.2, 0.9, 2.8), (0, 2.55, 2.1), rot=(-27.5, 0, 0))
    g.esfera("h_luz_roja", 0.13, (0, 2.75, 4.62), lados=6, anillos=4)
    g.ancla("Acople", (0, 0, 0))


def tren_aterrizaje(g):
    # Pata retráctil: soporte fijo (origen arriba, acoplado a la panza), y pata articulada que gira hacia atrás.
    g.caja("h_gris", (1.3, 2.0, 0.4), (0, 0, -0.2), bisel=0.06)
    for s in (-1, 1):
        g.caja("h_oscuro", (0.2, 1.0, 0.7), (s * 0.45, 0, -0.7), sup=(1, 0.6))
    g.cil("h_metal", 0.16, 1.2, (-0.6, 0, -0.75), (0, 90, 0), lados=8)
    g.pieza("pata", pivote=(0, 0, -0.75))
    g.tubo("h_naranja_liso", [(0, 0, -0.75), (0, -0.25, -2.0)], 0.27, lados=8)
    g.tubo("h_metal", [(0, -0.25, -2.0), (0, -0.45, -3.2)], 0.17, lados=8)
    g.toro("h_oscuro", 0.28, 0.07, (0, -0.25, -2.0), (10, 0, 0), seg=8, lados=4)
    # Amortiguador diagonal y zapata con almohadilla.
    g.tubo("h_gris", [(0, 0.75, -0.9), (0, -0.2, -2.3)], 0.1, lados=6)
    g.pieza("zapata", pivote=(0, -0.45, -3.2), padre="pata")
    g.esfera("h_gris", 0.26, (0, -0.45, -3.2), lados=8, anillos=4)
    g.caja("h_gris", (1.5, 2.1, 0.28), (0, -0.55, -3.5), sup=(0.75, 0.8), bisel=0.06)
    g.caja("h_oscuro", (1.6, 2.2, 0.16), (0, -0.55, -3.7))
    g.caja("h_neon", (0.5, 0.08, 0.1), (0, -1.62, -3.5))
    g.pieza("cuerpo")
    g.ancla("Acople", (0, 0, 0))
    g.ancla("Suelo", (0, -0.55, -3.78))
    g.extra["tren"] = {"giro_plegado_grados": 95, "eje": "X de Roblox, en el pivote de «pata»"}


MODELOS = [
    ("motor_avanzado", "nave", 5000, motor_avanzado),
    ("motor_turbo", "nave", 5000, motor_turbo),
    ("arma_laser_nave", "nave", 5000, arma_laser_nave),
    ("arma_misiles_nave", "nave", 5000, arma_misiles_nave),
    ("escudo_nave", "nave", 5000, escudo_nave),
    ("estabilizador", "nave", 5000, estabilizador),
    ("tren_aterrizaje", "nave", 5000, tren_aterrizaje),
]
