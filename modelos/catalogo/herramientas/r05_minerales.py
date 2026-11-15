"""Ronda 5: piedras y minerales (modelos 25-32)."""

import math
import random

from comunes import cristales


def piedra_comun(g):
    # Tres formas en un archivo: canto redondo, losa y aguja.
    g.pieza("a", pivote=(0, 0, 0))
    g.roca("piedra", 1.6, (0, 0, 0.9), esc=(1.2, 1.0, 0.75), semilla=1, sub=2, amp=0.3, plano=-1.15)
    g.pieza("b", pivote=(4.5, 0, 0))
    g.roca("piedra", 1.5, (4.5, 0, 0.5), esc=(1.5, 1.1, 0.45), rot=(0, 0, 30), semilla=7, sub=2, amp=0.35, plano=-1.0)
    g.roca("piedra", 0.8, (5.4, 0.9, 0.9), esc=(1.2, 1.0, 0.5), rot=(8, 5, 70), semilla=8, sub=1, amp=0.3)
    g.pieza("c", pivote=(-4.2, 0, 0))
    g.roca("piedra", 1.3, (-4.2, 0, 1.5), esc=(0.8, 0.75, 1.5), rot=(6, -8, 0), semilla=12, sub=2, amp=0.32, plano=-1.05)
    g.roca("piedra", 0.6, (-3.3, -0.6, 0.35), esc=(1.1, 1, 0.7), semilla=13, sub=1, amp=0.3, plano=-0.5)


def piedra_grande(g):
    g.roca("piedra_musgo", 5.0, (0, 0, 3.2), esc=(1.15, 0.95, 0.85), semilla=3, sub=3, amp=0.3, frec=0.8, plano=-3.75)
    g.roca("piedra_musgo", 2.6, (4.6, -1.6, 1.5), esc=(1.1, 1.0, 0.8), rot=(0, 0, 40), semilla=5, sub=2, amp=0.3, plano=-1.85)
    g.roca("piedra_musgo", 2.0, (-4.4, 2.0, 1.2), esc=(1.0, 1.2, 0.8), semilla=6, sub=2, amp=0.3, plano=-1.5)
    g.roca("piedra", 0.9, (2.6, -4.2, 0.5), esc=(1.2, 1, 0.7), semilla=9, sub=1, amp=0.3, plano=-0.7)
    rnd = random.Random(26)
    # Matas de musgo abultadas y hierbas en las repisas.
    for i, (px, py, pz, r) in enumerate(((-1.0, 0.5, 7.2, 1.5), (2.2, -1.0, 6.2, 1.2), (4.6, -1.4, 3.5, 1.0), (-4.2, 2.2, 2.7, 0.9))):
        g.roca("hoja", r, (px, py, pz), esc=(1.3, 1.2, 0.35), semilla=40 + i, sub=1, amp=0.25)
    for i in range(7):
        a = rnd.uniform(0, 6.28)
        g.cristal("hierba", 0.18, rnd.uniform(0.9, 1.6), (6.2 * math.cos(a), 5.4 * math.sin(a), 0), (rnd.uniform(-18, 18), rnd.uniform(-18, 18), 0),
                  lados=3, punta=0.9, base=1.0)


def _mena(g, roca, pepita, semilla, cristal=None):
    rnd = random.Random(semilla)
    g.roca(roca, 2.3, (0, 0, 1.5), esc=(1.2, 1.0, 0.85), semilla=semilla, sub=3, amp=0.3, plano=-1.75)
    g.roca(roca, 1.3, (2.5, -0.8, 0.8), esc=(1.1, 1.0, 0.8), rot=(0, 0, 50), semilla=semilla + 1, sub=2, amp=0.3, plano=-1.0)
    g.roca(roca, 1.0, (-2.4, 0.9, 0.6), esc=(1.0, 1.2, 0.8), semilla=semilla + 2, sub=2, amp=0.3, plano=-0.75)
    # Pepitas de metal incrustadas en la superficie.
    for i in range(9):
        a = rnd.uniform(0, 6.28)
        el = rnd.uniform(0.1, 1.3)
        px = 2.3 * 1.2 * math.cos(a) * math.cos(el) * 0.93
        py = 2.3 * math.sin(a) * math.cos(el) * 0.93
        pz = 1.5 + 2.3 * 0.85 * math.sin(el) * 0.93
        if cristal:
            g.cristal(cristal, rnd.uniform(0.2, 0.34), rnd.uniform(0.9, 1.7), (px, py, pz - 0.2),
                      (math.degrees(math.pi / 2 - el) * math.sin(a) * 0.8, -math.degrees(math.pi / 2 - el) * math.cos(a) * 0.8, i * 30),
                      lados=5, punta=0.4)
        else:
            g.roca(pepita, rnd.uniform(0.3, 0.5), (px, py, pz), esc=(1, 1, 0.8), rot=(i * 20, i * 35, 0), semilla=semilla + 10 + i, sub=1, amp=0.25)
    for i in range(3):
        a = rnd.uniform(0, 6.28)
        g.roca(pepita, 0.3, (3.4 * math.cos(a), 2.8 * math.sin(a), 0.2), semilla=semilla + 30 + i, sub=1, amp=0.3)


def mineral_hierro(g):
    _mena(g, "roca_hierro", "pepita_hierro", 27)


def mineral_cobre(g):
    _mena(g, "roca_cobre", "pepita_cobre", 28)


def mineral_oro(g):
    _mena(g, "roca_oro", "cris_oro", 29, cristal="cris_oro")
    cristales(g, "cris_oro", (0.2, 0.0, 3.2), n=5, r=0.55, h=2.4, semilla=4, abrir=40)


def _cristal_grande(g, mat, base, semilla, alto=7.0):
    rnd = random.Random(semilla)
    g.roca(base, 2.6, (0, 0, 0.5), esc=(1.2, 1.1, 0.4), semilla=semilla, sub=2, amp=0.3, plano=-1.0)
    g.roca(base, 1.2, (2.6, 1.0, 0.4), esc=(1.1, 1, 0.6), semilla=semilla + 1, sub=1, amp=0.3, plano=-0.6)
    cristales(g, mat, (0, 0, 0.5), n=6, r=1.25, h=alto, semilla=semilla, abrir=30, radio=1.3)
    cristales(g, mat, (2.4, 1.0, 0.7), n=3, r=0.5, h=alto * 0.4, semilla=semilla + 5, abrir=30)
    cristales(g, mat, (-2.3, -0.8, 0.5), n=3, r=0.45, h=alto * 0.35, semilla=semilla + 6, abrir=35)
    for i in range(4):
        a = rnd.uniform(0, 6.28)
        g.cristal(mat, 0.22, 0.9, (3.2 * math.cos(a), 2.8 * math.sin(a), 0.05), (rnd.uniform(-25, 25), rnd.uniform(-25, 25), 0), lados=5)
    g.ancla("Luz", (0, 0, alto * 0.55))


def mineral_cristal_azul(g):
    _cristal_grande(g, "cris_azul", "roca_base", 30)


def mineral_cristal_purpura(g):
    _cristal_grande(g, "cris_purpura", "m_roca_vetas", 31, alto=7.6)


def mineral_cristal_naranja(g):
    _cristal_grande(g, "cris_naranja", "roca_base", 32, alto=6.4)


MODELOS = [
    ("piedra_comun", "minerales", 5000, piedra_comun),
    ("piedra_grande", "minerales", 5000, piedra_grande),
    ("mineral_hierro", "minerales", 5000, mineral_hierro),
    ("mineral_cobre", "minerales", 5000, mineral_cobre),
    ("mineral_oro", "minerales", 5000, mineral_oro),
    ("mineral_cristal_azul", "minerales", 5000, mineral_cristal_azul),
    ("mineral_cristal_purpura", "minerales", 5000, mineral_cristal_purpura),
    ("mineral_cristal_naranja", "minerales", 5000, mineral_cristal_naranja),
]
