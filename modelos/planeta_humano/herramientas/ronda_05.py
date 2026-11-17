"""Ronda 5 · Fin de la zona comercial (41-45) y comienzo de la industrial (46-50)."""

import math

from geometria import arco_pts
from registro import modelo


@modelo(41, "comercial", "prop", (2, 2, 2))
def caja_envio(m):
    # Caja de transporte espacial: casco biselado, cantoneras, bastidor, correas con hebilla y logotipo en relieve
    m.caja((0, 0, 1.0), (1.84, 1.84, 1.84), "gris", bisel=0.08)
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.caja((sx * 0.92, sy * 0.92, 1.0), (0.16, 0.16, 2.0), "oscuro", bisel=0.03)
            for sz in (0.1, 1.9):
                m.caja((sx * 0.88, sy * 0.88, sz), (0.3, 0.3, 0.2), "acero", bisel=0.04)
    for sz in (0.07, 1.93):
        for s in (-1, 1):
            m.caja((0, s * 0.92, sz), (1.7, 0.14, 0.14), "oscuro")
            m.caja((s * 0.92, 0, sz), (0.14, 1.7, 0.14), "oscuro")
    # Correas naranjas que abrazan la caja, con hebilla
    for x in (-0.45, 0.45):
        m.tubo((x, 0, 1.0), 1.0, 0.2, 0.05, "tela_naranja", eje="x", seg=4, rot=(45, 0, 0)) if False else None
        for s in (-1, 1):
            m.caja((x, s * 0.935, 1.0), (0.2, 0.03, 1.9), "tela_naranja")
        m.caja((x, 0, 1.935), (0.2, 1.9, 0.03), "tela_naranja")
        m.caja((x, -0.96, 1.25), (0.26, 0.05, 0.2), "acero", bisel=0.015)
        m.caja((x, -0.985, 1.25), (0.14, 0.02, 0.08), "oscuro")
    # Logotipo: planeta con órbita y flecha, en relieve, y piloto de estado
    m.cil((0, -0.93, 0.95), 0.2, 0.05, "acento", eje="y", seg=14)
    m.toro((0, -0.94, 0.95), 0.32, 0.025, "blanco_liso", eje="y", seg=18, seg2=5, rot=(0, 25, 0))
    m.prisma([(0.2, 0.2), (0.42, 0.26), (0.34, 0.06)], -0.02, 0.02, "blanco_liso", "xz", c=(0, -0.945, 0.95))
    m.caja((0, -0.935, 0.45), (0.6, 0.03, 0.2), "plastico", bisel=0.01)
    for k in range(3):
        m.caja((-0.12 + 0.02 * k, -0.953, 0.5 - 0.05 * k), (0.3 - 0.06 * k, 0.01, 0.025), "negro")
    m.caja((0.72, -0.93, 1.72), (0.12, 0.03, 0.06), "neon")
    # Asas laterales abatibles
    for s in (-1, 1):
        m.barrido([(s * 0.93, -0.3, 1.2), (s * 1.0, -0.3, 1.1), (s * 1.0, 0.3, 1.1), (s * 0.93, 0.3, 1.2)], 0.03,
                  "acero", seg=5)
        m.caja((s * 0.925, 0, 1.2), (0.03, 0.8, 0.12), "oscuro")


@modelo(42, "comercial", "prop", (1.5, 1.5, 2))
def barril_metal(m):
    # Bidón con nervios, aro de cierre hermético con palanca, tapón roscado y testigo de nivel
    m.torno((0, 0, 0), [(0.64, 0), (0.7, 0.05), (0.7, 0.45), (0.74, 0.5), (0.74, 0.58), (0.7, 0.63), (0.7, 1.2),
                        (0.74, 1.25), (0.74, 1.33), (0.7, 1.38), (0.7, 1.82), (0.66, 1.86), (0, 1.86)], "azul_p", seg=18)
    m.tubo((0, 0, 1.86), 0.75, 0.12, 0.08, "acero", seg=18)
    m.cil((0, 0, 1.88), 0.67, 0.06, "gris_liso", seg=18)
    m.tubo((0, 0, 0.05), 0.72, 0.1, 0.05, "acero", seg=18)
    # Palanca de cierre y pernos
    m.caja((0, -0.78, 1.86), (0.16, 0.1, 0.2), "acero", bisel=0.02)
    m.barrido([(0, -0.8, 1.9), (0.3, -0.76, 1.96), (0.5, -0.62, 1.97)], 0.025, "rojo_p", seg=5)
    for k in range(6):
        a = math.radians(60 * k + 30)
        m.cil((0.55 * math.cos(a), 0.55 * math.sin(a), 1.92), 0.04, 0.03, "acero", seg=6)
    # Tapón y válvula de presión
    m.cil((0.3, 0.2, 1.94), 0.12, 0.08, "acero", seg=8)
    m.cil((0.3, 0.2, 1.99), 0.07, 0.04, "amarillo_p", seg=6)
    m.cil((-0.3, -0.1, 1.95), 0.04, 0.1, "cromo", seg=6)
    m.esfera((-0.3, -0.1, 2.0), 0.05, "rojo_p", seg=6, anillos=4)
    # Banda de aviso, testigo de nivel luminoso y placa
    m.tubo((0, 0, 0.92), 0.715, 0.3, 0.02, "rayas", seg=18)
    m.caja((0, -0.71, 1.55), (0.1, 0.03, 0.36), "pantalla")
    m.caja((0, -0.725, 1.5), (0.06, 0.02, 0.22), "neon")
    m.caja((0.32, -0.63, 0.3), (0.3, 0.03, 0.18), "plastico", rot=(0, 0, 27))


@modelo(43, "comercial", "prop", (3, 1, 5))
def estanteria_tienda(m):
    # Cuatro montantes en L, cuatro baldas con borde, cruces de arriostrado, pies y tira de etiquetas luminosa
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 1.42, sy * 0.42
            m.caja((x, y, 2.5), (0.1, 0.03, 5.0), "gris_liso")
            m.caja((x + sx * 0.035, y - sy * 0.035, 2.5), (0.03, 0.1, 5.0), "gris_liso")
            m.caja((x, y, 0.03), (0.2, 0.2, 0.06), "oscuro")
            m.caja((x, y, 4.98), (0.14, 0.14, 0.05), "oscuro")
    for i, z in enumerate((0.5, 1.7, 2.9, 4.1)):
        m.caja((0, 0, z), (2.84, 0.9, 0.07), "blanco_liso")
        m.caja((0, -0.46, z + 0.04), (2.84, 0.04, 0.15), "gris_liso")
        m.caja((0, 0.46, z + 0.1), (2.84, 0.04, 0.26), "gris_liso")
        for sx in (-1, 1):
            m.caja((sx * 1.4, 0, z + 0.04), (0.04, 0.9, 0.15), "gris_liso")
            for sy in (-1, 1):
                m.prisma([(0, 0), (0.22, 0), (0, -0.22)], -0.015, 0.015, "acero", "xz", c=(sx * 1.37 if sx < 0 else 1.15,
                         sy * 0.4, z - 0.035), rot=(0, 0, 0)) if sx < 0 else \
                    m.prisma([(0, 0), (-0.22, 0), (0, -0.22)], -0.015, 0.015, "acero", "xz", c=(1.37, sy * 0.4, z - 0.035))
        m.caja((0, -0.485, z + 0.04), (2.6, 0.015, 0.07), "neon" if i % 2 == 0 else "acento")
    m.barrido([(-1.4, 0.45, 0.6), (1.4, 0.45, 4.0)], 0.02, "acero", seg=4)
    m.barrido([(1.4, 0.45, 0.6), (-1.4, 0.45, 4.0)], 0.02, "acero", seg=4)
    for sx in (-1, 1):
        m.barrido([(sx * 1.44, -0.4, 1.8), (sx * 1.44, 0.4, 2.8)], 0.018, "acero", seg=4)
    m.caja((0, 0, 4.98), (2.9, 0.9, 0.04), "gris_liso")
    m.caja((0, -0.44, 4.86), (1.0, 0.03, 0.2), "oscuro")
    m.caja((0, -0.46, 4.86), (0.8, 0.015, 0.08), "neon")


@modelo(44, "comercial", "prop", (1.5, 1, 5))
def maniqui_expositor(m):
    # Maniquí robótico articulado sobre peana: columna vista, rótulas esféricas y visor luminoso
    m.cil((0, 0, 0.06), 0.5, 0.12, "oscuro", seg=16)
    m.tubo((0, 0, 0.13), 0.42, 0.04, 0.04, "neon", seg=16)
    m.cil((0, 0.18, 1.2), 0.04, 2.3, "cromo", seg=6)
    # Piernas
    for s in (-1, 1):
        x = s * 0.2
        m.caja((x, -0.05, 0.2), (0.22, 0.42, 0.14), "gris_liso", bisel=0.04)                 # pie
        m.esfera((x, 0, 0.32), 0.09, "acero", seg=8, anillos=5)
        m.torno((x, 0, 0.36), [(0.08, 0), (0.12, 0.35), (0.1, 0.85), (0.0, 0.86)], "blanco_liso", seg=8)
        m.esfera((x, 0, 1.28), 0.11, "acero", seg=8, anillos=5)                               # rodilla
        m.torno((x, 0, 1.34), [(0.1, 0), (0.15, 0.4), (0.13, 0.9), (0.0, 0.92)], "blanco_liso", seg=8)
        m.caja((x, -0.13, 1.8), (0.08, 0.03, 0.5), "acento")
        m.esfera((x, 0, 2.32), 0.13, "acero", seg=8, anillos=5)                               # cadera
    # Pelvis, columna segmentada y torso
    m.caja((0, 0, 2.42), (0.62, 0.34, 0.26), "gris_liso", bisel=0.07)
    for k in range(4):
        m.cil((0, 0.02, 2.62 + 0.12 * k), 0.1 - 0.005 * k, 0.09, "acero" if k % 2 else "oscuro", seg=8)
    m.torno((0, 0, 3.05), [(0.2, 0), (0.3, 0.2), (0.4, 0.6), (0.36, 0.85), (0.2, 0.95), (0.0, 0.96)], "blanco_liso",
            seg=10, rot=(0, 0, 0))
    m.caja((0, -0.3, 3.62), (0.34, 0.08, 0.3), "gris_liso", bisel=0.03)
    m.cil((0, -0.345, 3.62), 0.07, 0.03, "neon", eje="y", seg=10)
    m.caja((0, 0.3, 3.55), (0.3, 0.1, 0.5), "oscuro", bisel=0.03)
    # Brazos: hombro, brazo, codo, antebrazo y mano con dedos en pinza
    for s in (-1, 1):
        x = s * 0.5
        m.esfera((x, 0, 3.85), 0.15, "acero", seg=10, anillos=6)
        m.torno((x + s * 0.04, 0, 3.05), [(0.07, 0), (0.1, 0.3), (0.09, 0.72), (0.0, 0.74)], "blanco_liso", seg=8)
        m.esfera((x + s * 0.05, 0, 3.0), 0.09, "acero", seg=8, anillos=5)
        m.torno((x + s * 0.06, -0.02, 2.3), [(0.05, 0), (0.085, 0.3), (0.075, 0.66), (0.0, 0.68)], "blanco_liso", seg=8)
        m.caja((x + s * 0.06, -0.02, 2.2), (0.12, 0.08, 0.16), "gris_liso", bisel=0.02)
        for dy in (-0.04, 0.03):
            m.caja((x + s * 0.06, -0.02 + dy, 2.06), (0.09, 0.025, 0.16), "oscuro")
    # Cuello y cabeza con visor
    m.cil((0, 0, 4.08), 0.07, 0.2, "acero", seg=8)
    m.esfera((0, 0, 4.48), 0.26, "blanco_liso", seg=12, anillos=8, esc=(0.9, 1.0, 1.2))
    m.caja((0, -0.2, 4.52), (0.36, 0.1, 0.1), "pantalla", bisel=0.02)
    m.caja((0, -0.255, 4.52), (0.3, 0.02, 0.05), "neon")
    for s in (-1, 1):
        m.cil((s * 0.24, 0, 4.5), 0.06, 0.05, "acero", eje="x", seg=8)
    m.cil((0.1, 0.05, 4.86), 0.012, 0.22, "acero", seg=4)
    m.esfera((0.1, 0.05, 4.97), 0.025, "neon", seg=6, anillos=4)


@modelo(45, "comercial", "vehiculo", (3, 2, 2))
def carro_carga(m):
    # Carro flotante: plataforma, cuatro repulsores (no lleva ruedas), manillar, barandas y carga amarrada
    m.caja((0, 0, 0.52), (2.9, 1.9, 0.24), "blanco_liso", bisel=0.06)
    m.caja((0, 0, 0.655), (2.6, 1.6, 0.03), "rejilla")
    m.caja((0, 0, 0.42), (2.5, 1.5, 0.12), "oscuro", bisel=0.03)
    for s in (-1, 1):
        m.caja((0, s * 0.96, 0.52), (2.2, 0.03, 0.08), "neon")
        m.caja((s * 1.3, 0, 0.36), (0.2, 1.3, 0.1), "acero")
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * 1.05, sy * 0.62
            m.torno((x, y, 0.2), [(0.2, 0.16), (0.3, 0.1), (0.32, 0.0), (0.24, 0.0), (0.2, 0.06), (0, 0.08)], "gris_liso",
                    seg=12, cerrar=False)
            m.cil((x, y, 0.17), 0.22, 0.04, "neon", seg=12, p="repulsores_neon")
            m.tubo((x, y, 0.2), 0.33, 0.05, 0.03, "acero", seg=12)
            m.anclaje(f"repulsor_{'d' if sx > 0 else 'i'}{'f' if sy < 0 else 't'}", (x, y, 0.15))
    # Manillar con panel de control
    for sy in (-1, 1):
        m.barrido([(1.35, sy * 0.7, 0.64), (1.45, sy * 0.7, 1.4), (1.62, sy * 0.7, 1.82)], 0.04, "acero", seg=6)
    m.barrido([(1.62, -0.7, 1.82), (1.62, 0.7, 1.82)], 0.045, "goma", seg=8)
    m.caja((1.52, 0, 1.55), (0.1, 0.6, 0.3), "oscuro", rot=(0, -22, 0), bisel=0.02)
    m.caja((1.57, 0.05, 1.57), (0.02, 0.3, 0.16), "neon", rot=(0, -22, 0), p="pantalla_neon")
    m.cil((1.58, -0.2, 1.55), 0.035, 0.05, "rojo_p", eje="x", seg=8, rot=(0, -22, 0))
    # Barandas bajas y carga: dos cajas y un bidón con cinchas
    for sy in (-1, 1):
        m.barrido([(-1.3, sy * 0.85, 0.64), (-1.3, sy * 0.85, 0.95), (1.2, sy * 0.85, 0.95), (1.2, sy * 0.85, 0.64)], 0.03,
                  "acero", seg=5)
    m.barrido([(-1.3, -0.85, 0.95), (-1.3, 0.85, 0.95)], 0.03, "acero", seg=5)
    m.caja((-0.65, -0.2, 1.07), (1.1, 1.0, 0.8), "gris", bisel=0.04)
    m.caja((-0.65, -0.2, 1.07), (0.16, 1.03, 0.83), "tela_naranja")
    m.caja((-0.6, 0.0, 1.72), (0.8, 0.7, 0.5), "madera_clara", bisel=0.02)
    m.caja((-0.6, 0.0, 1.72), (0.83, 0.1, 0.52), "madera_oscura")
    m.torno((0.55, 0.15, 0.67), [(0.36, 0), (0.4, 0.05), (0.4, 0.95), (0.36, 1.0), (0, 1.0)], "naranja_p", seg=12)
    for z in (0.95, 1.4):
        m.tubo((0.55, 0.15, z), 0.415, 0.06, 0.03, "acero", seg=12)
    m.barrido([(0.1, 0.15, 0.68), (0.1, 0.15, 1.72), (1.0, 0.15, 1.72), (1.0, 0.15, 0.68)], 0.02, "goma", seg=4)


# --------------------------------------------------------------------------------------------------------------
# Zona industrial
# --------------------------------------------------------------------------------------------------------------

def _yunque(m, c, esc=1.0, rot=(0, 0, 0)):
    """Yunque de herrero (el cuerno apunta a +X). `c` = centro de la base."""
    x, y, z = c
    e = esc
    perfil = [(-0.5, 0), (0.5, 0), (0.42, 0.14), (0.22, 0.22), (0.18, 0.5), (0.34, 0.62), (0.62, 0.66), (0.62, 0.86),
              (-0.62, 0.86), (-0.62, 0.72), (-0.34, 0.62), (-0.18, 0.5), (-0.22, 0.22), (-0.42, 0.14)]
    m.prisma([(u * e, v * e) for u, v in perfil], -0.24 * e, 0.24 * e, "hierro", "xz", c=c, rot=rot)
    m.torno((x + 0.62 * e, y, z + 0.76 * e), [(0.1 * e, 0), (0.07 * e, 0.3 * e), (0.0, 0.62 * e)], "hierro", seg=8,
            eje="x", rot=rot) if rot == (0, 0, 0) else None
    m.caja((x, y, z + 0.865 * e), (1.22 * e, 0.5 * e, 0.03 * e), "acero")
    m.caja((x - 0.45 * e, y, z + 0.885 * e), (0.1 * e, 0.1 * e, 0.02 * e), "negro")


@modelo(46, "industrial", "edificio_grande", (16, 14, 12))
def forja_principal(m):
    m.caja((0, 0, 0.2), (16, 14, 0.4), "piedra_oscura", bisel=0.06)
    # Muros de piedra abajo y chapa arriba, con el taller abierto al frente (nicho real)
    x0, x1, yf, yn, yb = -7.4, 4.6, -5.6, -1.4, 6.4
    m.bloque((x0, yn, 0.4), (x1, yb, 7.0), "piedra_oscura")
    m.bloque((x0, yf, 0.4), (-4.4, yn, 7.0), "piedra_oscura")
    m.bloque((1.6, yf, 0.4), (x1, yn, 7.0), "piedra_oscura")
    m.bloque((-4.4, yf, 5.4), (1.6, yn, 7.0), "piedra_oscura")
    m.bloque((x0 - 0.05, yf - 0.05, 3.6), (x1 + 0.05, yb + 0.05, 3.9), "hierro")
    m.bloque((x0 - 0.04, yf - 0.04, 6.6), (x1 + 0.04, yb + 0.04, 7.0), "hierro")
    m.bloque((-4.4, yf, 0.4), (1.6, yn, 0.5), "piedra")
    for x in (x0, -4.4, 1.6, x1):
        m.caja((x, yf, 3.7), (0.5, 0.5, 6.6), "hierro", bisel=0.06)
    m.prisma(arco_pts(3.2, 2.8, 0, 180, 10, -1.4, 2.6, 1.0, 1.0), yf - 0.15, yf + 0.3, "hierro", "xz")
    # Cubierta a dos aguas de chapa con lucernario caliente
    m.prisma([(x0 - 0.5, 7.0), (x1 + 0.5, 7.0), (x1 + 0.5, 7.2), (-1.4, 10.0), (x0 - 0.5, 7.2)], yf - 0.4, yb + 0.4,
             "chapa", "xz")
    m.caja((-1.4, 0.4, 10.0), (0.8, 12.6, 0.4), "hierro", bisel=0.05)
    m.caja((-1.4, 0.4, 10.22), (0.4, 11.0, 0.06), "neon_naranja")
    m.prisma([(x0 - 0.3, 7.0), (x1 + 0.3, 7.0), (-1.4, 9.75)], yf - 0.5, yf - 0.38, "piedra_oscura", "xz")
    # Gran chimenea de piedra que se estrecha, con boca incandescente
    m.torno((6.2, 2.5, 0.4), [(2.0, 0), (2.0, 1.2), (1.75, 1.6), (1.4, 7.0), (1.15, 10.6), (1.3, 10.8), (1.3, 11.3),
                              (1.0, 11.3), (1.0, 10.9), (0, 10.9)], "piedra", seg=4, rot=(0, 0, 45))
    for z in (4.0, 7.0, 9.6):
        r = 1.75 - (z - 2.0) * 0.065
        m.torno((6.2, 2.5, z), [(r * 1.0 + 0.06, 0), (r * 1.0 + 0.06, 0.25)], "hierro", seg=4, rot=(0, 0, 45))
    m.caja((6.2, 2.5, 11.42), (1.35, 1.35, 0.06), "neon_naranja")
    m.anclaje("humo_chimenea", (6.2, 2.5, 11.9))
    m.bloque((4.6, 1.2, 0.4), (5.2, 3.8, 5.0), "piedra_oscura")
    # Dentro del taller: horno al fondo con brillo naranja, yunque sobre tocón, pila de temple y carbón
    m.bloque((-3.4, yn - 0.9, 0.5), (0.6, yn, 4.2), "piedra")
    m.prisma(arco_pts(1.25, 1.0, 0, 180, 8, -1.4, 1.7, 1.0, 1.0), yn - 1.05, yn - 0.8, "hierro", "xz")
    m.bloque((-2.4, yn - 0.98, 0.9), (-0.4, yn - 0.86, 1.72), "neon_naranja")
    m.prisma([(-1.0, 1.7)] + [(math.cos(math.radians(a)), 1.7 + math.sin(math.radians(a))) for a in range(15, 180, 15)]
             + [(1.0, 1.7)], yn - 0.98, yn - 0.86, "neon_naranja", "xz", c=(-1.4, 0, 0))
    for k in range(4):
        m.caja((-2.15 + 0.5 * k, yn - 1.02, 1.5), (0.1, 0.08, 1.9), "hierro")
    m.bloque((-2.7, yn - 1.4, 0.5), (-0.1, yn - 0.9, 0.9), "piedra_oscura")
    m.cil((-1.9, -3.8, 0.85), 0.5, 0.7, "madera", seg=12)
    m.tubo((-1.9, -3.8, 1.0), 0.52, 0.1, 0.03, "hierro", seg=12)
    _yunque(m, (-1.9, -3.8, 1.2), 1.0)
    m.cil((-1.75, -3.85, 2.14), 0.03, 0.8, "madera_clara", eje="y", seg=6, rot=(0, 0, 30))     # martillo
    m.caja((-1.55, -4.2, 2.14), (0.34, 0.16, 0.16), "acero", rot=(0, 0, 30))
    m.torno((0.6, -4.4, 0.5), [(0.5, 0), (0.6, 0.5), (0.6, 0.95), (0.52, 0.95), (0.52, 0.5), (0, 0.4)], "madera_oscura",
            seg=12)
    m.cil((0.6, -4.4, 1.3), 0.52, 0.06, "agua", seg=12)
    for z in (0.75, 1.3):
        m.tubo((0.6, -4.4, z), 0.61, 0.08, 0.03, "hierro", seg=12)
    for k in range(9):
        a = k * 2.4
        m.roca((-3.7 + 0.28 * math.cos(a) * (k % 3), -2.3 + 0.3 * math.sin(a) * (k % 3), 0.62 + 0.1 * (k % 3)),
               (0.42, 0.38, 0.3), "carbon", semilla=k, sub=1)
    m.esfera((-3.7, -2.3, 0.7), 0.16, "neon_naranja", seg=6, anillos=4)
    # Canal de metal fundido que cruza el suelo del taller
    m.bloque((-1.6, yn - 2.6, 0.5), (-1.2, yn - 1.4, 0.56), "hierro")
    m.bloque((-1.52, yn - 2.55, 0.53), (-1.28, yn - 1.4, 0.58), "neon_naranja")
    # Portón corredero del taller (pieza aparte), abierto sobre su guía
    m.bloque((-4.6, yf - 0.32, 5.5), (4.4, yf - 0.16, 5.7), "hierro")
    m.bloque((1.7, yf - 0.3, 0.5), (4.4, yf - 0.18, 5.45), "oscuro_paneles", p="porton")
    for z in (1.5, 3.0, 4.5):
        m.caja((3.05, yf - 0.32, z), (2.7, 0.05, 0.14), "hierro", p="porton")
    m.barrido([(1.75, yf - 0.3, 0.6), (4.35, yf - 0.3, 5.3)], 0.05, "hierro", seg=4, p="porton")
    m.caja((2.0, yf - 0.36, 2.6), (0.1, 0.08, 0.6), "acero", p="porton")
    # Rótulo de martillo y yunque, farol, armero exterior y fuelle
    m.caja((-5.9, yf - 0.1, 5.0), (2.2, 0.16, 1.6), "madera_oscura", bisel=0.04)
    _yunque(m, (-5.9, yf - 0.24, 4.45), 0.9, rot=(0, 0, 0.0001))
    m.caja((-5.9, yf - 0.24, 5.45), (0.9, 0.1, 0.1), "acero", rot=(0, 35, 0))
    m.caja((-5.5, yf - 0.24, 5.72), (0.3, 0.2, 0.42), "acero", rot=(0, 35, 0))
    m.barrido([(-4.4, yf - 0.1, 4.6), (-4.4, yf - 0.7, 4.75), (-4.4, yf - 0.7, 4.5)], 0.035, "hierro", seg=5)
    m.torno((-4.4, yf - 0.7, 4.1), [(0.1, 0), (0.18, 0.05), (0.18, 0.34), (0.06, 0.42)], "hierro", seg=8)
    m.cil((-4.4, yf - 0.7, 4.26), 0.12, 0.24, "neon_naranja", seg=8)
    m.bloque((-7.2, yf - 0.5, 0.4), (-5.2, yf - 0.1, 0.6), "madera_oscura")
    m.caja((-6.2, yf - 0.3, 2.6), (2.0, 0.1, 0.12), "madera_oscura")
    for sx in (-7.1, -5.3):
        m.caja((sx, yf - 0.3, 1.5), (0.12, 0.12, 2.3), "madera_oscura")
    for i, x in enumerate((-6.8, -6.4, -6.0, -5.6)):
        hoja = [(-0.07, 0), (0.07, 0), (0.06, 1.3), (0, 1.5), (-0.06, 1.3)]
        m.prisma(hoja, -0.02, 0.02, "acero" if i % 2 else "cromo", "xz", c=(x, yf - 0.36, 0.62), rot=(-6, 0, 0))
        m.caja((x, yf - 0.19, 2.1), (0.34, 0.06, 0.06), "bronce")
        m.cil((x, yf - 0.16, 2.3), 0.035, 0.34, "madera_oscura", seg=5, rot=(-6, 0, 0))
    # Ventanas altas enrejadas y respiraderos
    for y in (0.5, 4.0):
        m.ventana((x0 - 0.02, y, 5.3), 2.0, 1.4, normal="x", sentido=-1, marco="hierro", cristal="cristal_oscuro")
    for x in (-5.0, -1.4, 2.2):
        m.ventana((x, yb + 0.02, 5.3), 2.0, 1.4, sentido=1, marco="hierro", cristal="cristal_oscuro")
    m.barrido([(x1, -3.0, 6.0), (5.4, -3.0, 6.0), (5.4, -3.0, 8.4)], 0.22, "hierro", seg=8)
    m.torno((5.4, -3.0, 8.4), [(0.34, 0), (0.34, 0.06), (0, 0.3)], "hierro", seg=8)


@modelo(47, "industrial", "prop", (2, 1, 2))
def yunque_forja(m):
    # Tocón de madera con corteza y zunchos; encima, el yunque pesado con cuerno, agujeros y martillo apoyado
    m.torno((0, 0, 0), [(0.5, 0), (0.48, 0.1), (0.46, 0.9), (0.42, 0.95), (0, 0.95)], "madera", seg=14)
    for k in range(10):
        a = math.radians(36 * k + 5)
        m.barrido([(0.5 * math.cos(a), 0.5 * math.sin(a), 0.02), (0.48 * math.cos(a + 0.08), 0.48 * math.sin(a + 0.08), 0.5),
                   (0.46 * math.cos(a), 0.46 * math.sin(a), 0.88)], [0.06, 0.05, 0.04], "corteza", seg=4)
    for z in (0.25, 0.72):
        m.tubo((0, 0, z), 0.53, 0.09, 0.04, "hierro_viejo", seg=14)
        m.cil((0, -0.53, z), 0.035, 0.04, "acero", eje="y", seg=6)
    perfil = [(-0.55, 0), (0.55, 0), (0.46, 0.16), (0.24, 0.26), (0.2, 0.52), (0.36, 0.66), (0.6, 0.7), (0.6, 0.98),
              (-0.78, 0.98), (-0.78, 0.84), (-0.4, 0.7), (-0.2, 0.52), (-0.24, 0.26), (-0.46, 0.16)]
    m.prisma(perfil, -0.3, 0.3, "hierro", "xz", c=(-0.05, 0, 0.95))
    m.torno((0.55, 0, 1.79), [(0.14, 0), (0.1, 0.25), (0.0, 0.48)], "hierro", seg=8, eje="x")
    m.caja((-0.14, 0, 1.94), (1.34, 0.6, 0.03), "acero")
    m.caja((-0.62, 0.0, 1.955), (0.1, 0.1, 0.02), "negro")
    m.cil((-0.42, 0.14, 1.955), 0.04, 0.02, "negro", seg=8)
    for s in (-1, 1):
        m.caja((s * 0.4 - 0.05, 0, 1.02), (0.2, 0.7, 0.1), "hierro", bisel=0.02)
        for sy in (-1, 1):
            m.cil((s * 0.4 - 0.05, sy * 0.3, 1.09), 0.04, 0.05, "acero", seg=6)
    # Martillo apoyado y tenazas colgadas de una argolla
    m.cil((0.05, -0.05, 2.02), 0.03, 0.85, "madera_clara", eje="x", seg=6, rot=(0, 0, 18))
    m.caja((0.44, 0.08, 2.03), (0.18, 0.4, 0.16), "acero", rot=(0, 0, 18), bisel=0.02)
    m.tubo((0, -0.56, 0.55), 0.08, 0.02, 0.02, "hierro", eje="y", seg=8)
    for s in (-1, 1):
        m.barrido([(s * 0.02, -0.6, 0.6), (s * -0.03, -0.6, 0.35), (s * 0.06, -0.6, 0.12)], 0.018, "hierro", seg=4)


@modelo(48, "industrial", "prop", (3, 3, 4))
def horno_forja(m):
    # Horno de fundición: cuerpo de piedra abombado con zunchos, puerta de hierro (aparte) con mirilla, chimenea
    m.torno((0, 0, 0), [(1.45, 0), (1.45, 0.3), (1.3, 0.4), (1.42, 1.2), (1.3, 2.0), (0.95, 2.5), (0.6, 2.7), (0, 2.7)],
            "piedra", seg=10)
    for z, r in ((0.5, 1.34), (1.25, 1.44), (2.0, 1.33)):
        m.tubo((0, 0, z), r, 0.12, 0.05, "hierro", seg=10)
    # Boca del horno con brillo interior
    m.caja((0, -1.25, 1.1), (1.3, 0.5, 1.5), "hierro", bisel=0.05)
    m.caja((0, -1.42, 1.1), (1.0, 0.2, 1.2), "neon_naranja")
    m.prisma(arco_pts(0.62, 0.5, 0, 180, 6, 0, 1.3, 1.0, 1.0), -1.56, -1.46, "hierro", "xz")
    # Puerta entreabierta con bisagras, mirilla enrejada y tirador
    P = "puerta"
    m.caja((-0.78, -1.82, 1.1), (0.08, 0.9, 1.2), "hierro_viejo", rot=(0, 0, -20), bisel=0.02, p=P)
    m.caja((-0.86, -1.86, 1.3), (0.03, 0.4, 0.3), "neon_naranja", rot=(0, 0, -20))
    for k in range(3):
        m.caja((-0.84 - 0.03, -1.99 + 0.13 * k, 1.3), (0.05, 0.03, 0.32), "hierro", rot=(0, 0, -20), p=P)
    for z in (0.75, 1.45):
        m.cil((-0.62, -1.46, z), 0.05, 0.2, "acero", seg=6)
    m.barrido([(-0.98, -2.1, 0.95), (-1.08, -2.14, 1.0), (-1.08, -2.14, 1.2), (-0.98, -2.1, 1.25)], 0.025, "acero", seg=5,
              p=P)
    # Rejilla de cenizas, tobera con tubo de aire y fuelle
    m.caja((0, -1.4, 0.32), (1.1, 0.4, 0.2), "hierro", bisel=0.02)
    for k in range(5):
        m.caja((-0.4 + 0.2 * k, -1.61, 0.32), (0.06, 0.03, 0.16), "neon_naranja")
    m.barrido([(1.3, 0.2, 0.8), (1.7, 0.2, 0.8), (1.75, 0.2, 0.5), (1.75, -0.4, 0.4)], 0.1, "cobre", seg=8)
    m.cil((1.33, 0.2, 0.8), 0.16, 0.1, "hierro", eje="x", seg=8)
    # Chimenea con sombrerete
    m.torno((0, 0.1, 2.6), [(0.5, 0), (0.42, 0.3), (0.38, 1.0), (0.44, 1.05), (0.44, 1.15), (0.3, 1.15), (0.3, 1.0),
                            (0, 1.0)], "hierro_viejo", seg=10)
    for a in (0, 120, 240):
        m.cil((0.36 * math.cos(math.radians(a)), 0.1 + 0.36 * math.sin(math.radians(a)), 3.83), 0.025, 0.2, "hierro", seg=4)
    m.torno((0, 0.1, 3.9), [(0.55, 0), (0.0, 0.14)], "hierro", seg=10)
    m.cil((0, 0.1, 3.72), 0.3, 0.04, "neon_naranja", seg=10)
    m.anclaje("humo", (0, 0.1, 4.1))
    # Carbón y lingotes junto al horno
    for k in range(7):
        m.roca((-1.5 + 0.2 * (k % 3), -1.0 - 0.25 * (k // 3) + 0.1 * (k % 2), 0.14 + 0.12 * (k % 2)), (0.34, 0.3, 0.24),
               "carbon", semilla=k * 1.3, sub=1)
    for k in range(3):
        m.prisma([(-0.2, 0), (0.2, 0), (0.15, 0.12), (-0.15, 0.12)], -0.08, 0.08, "cobre" if k < 2 else "acero", "xz",
                 c=(1.2, -1.5 + 0.2 * (k % 2), 0.0 + 0.12 * (k // 2)), rot=(0, 0, 80 + 10 * k))


@modelo(49, "industrial", "prop", (3, 2, 2.5))
def mesa_crafting(m):
    # Banco de trabajo: sobre grueso, bastidor, cajonera, panel de herramientas colgadas y tornillo de banco
    for i in range(3):
        m.caja((0, -0.52 + 0.52 * i, 1.24), (3.0, 0.5, 0.14), "madera" if i % 2 == 0 else "madera_clara", bisel=0.02)
    m.caja((0, -0.78, 1.2), (3.0, 0.05, 0.2), "hierro")
    for sx in (-1, 1):
        for sy in (-1, 1):
            m.caja((sx * 1.36, sy * 0.66, 0.58), (0.14, 0.14, 1.16), "oscuro", bisel=0.02)
        m.caja((sx * 1.36, 0, 0.3), (0.1, 1.2, 0.1), "oscuro")
    m.caja((0, 0.66, 0.3), (2.6, 0.1, 0.1), "oscuro")
    m.caja((-0.3, 0, 0.33), (1.9, 1.2, 0.06), "madera_oscura")
    # Cajonera con tres cajones y tiradores
    m.caja((0.85, -0.05, 0.75), (0.8, 1.3, 0.8), "gris", bisel=0.03)
    for k in range(3):
        m.caja((0.85, -0.71, 0.5 + 0.25 * k), (0.7, 0.04, 0.21), "gris_claro", bisel=0.01, p=f"cajon_{k + 1}")
        m.caja((0.85, -0.75, 0.5 + 0.25 * k), (0.3, 0.04, 0.04), "acero", p=f"cajon_{k + 1}")
    # Panel trasero con herramientas colgadas de sus ganchos
    m.caja((0, 0.72, 1.9), (3.0, 0.08, 1.2), "madera_clara", bisel=0.02)
    for sx in (-1, 1):
        m.caja((sx * 1.4, 0.74, 1.3), (0.1, 0.1, 2.4), "oscuro")
    y = 0.66
    m.cil((-1.1, y, 1.85), 0.03, 0.7, "madera", seg=6)                                   # martillo
    m.caja((-1.1, y, 2.24), (0.36, 0.12, 0.14), "acero", bisel=0.02)
    m.caja((-0.55, y, 1.85), (0.07, 0.03, 0.75), "cromo")                                 # llave inglesa
    m.tubo((-0.55, y, 2.27), 0.1, 0.03, 0.045, "cromo", eje="y", seg=8)
    m.prisma([(-0.4, 0), (0.4, 0.04), (0.4, 0.2), (-0.4, 0.12)], -0.012, 0.012, "acero", "xz", c=(0.15, y, 2.05))    # serrucho
    m.prisma([(-0.62, -0.02), (-0.4, -0.02), (-0.4, 0.16), (-0.62, 0.2)], -0.03, 0.03, "madera_oscura", "xz",
             c=(0.15, y, 2.05))
    for s in (-1, 1):                                                                     # alicates
        m.barrido([(0.85 + s * 0.02, y, 2.3), (0.85 - s * 0.03, y, 2.0), (0.85 + s * 0.08, y, 1.7)], 0.022,
                  "rojo_p" if s < 0 else "rojo_p", seg=4)
    m.cil((1.2, y, 1.95), 0.022, 0.5, "cromo", seg=5)                                     # destornillador
    m.cil((1.2, y, 2.3), 0.045, 0.24, "amarillo_p", seg=6)
    for x, z in ((-1.1, 2.12), (-0.55, 2.38), (0.15, 2.3), (0.85, 2.38), (1.2, 2.14)):
        m.cil((x, 0.67, z), 0.02, 0.08, "acero", eje="y", seg=5)
    # Tornillo de banco 3D en la esquina
    m.caja((-1.05, -0.5, 1.36), (0.44, 0.5, 0.1), "hierro", bisel=0.02)
    m.caja((-1.05, -0.36, 1.56), (0.36, 0.14, 0.34), "azul_p", bisel=0.02)
    m.caja((-1.05, -0.66, 1.56), (0.36, 0.12, 0.34), "azul_p", bisel=0.02, p="mordaza")
    for yy in (-0.435, -0.595):
        m.caja((-1.05, yy, 1.69), (0.38, 0.03, 0.1), "acero")
    m.cil((-1.05, -0.62, 1.46), 0.035, 0.6, "acero", eje="y", seg=6)
    m.cil((-1.05, -0.92, 1.46), 0.02, 0.4, "cromo", eje="x", seg=5, p="mordaza")
    for s in (-1, 1):
        m.esfera((-1.05 + s * 0.2, -0.92, 1.46), 0.035, "cromo", seg=6, anillos=4, p="mordaza")
    # Pieza en curso, plano holográfico y flexo
    m.caja((0.0, -0.2, 1.335), (0.7, 0.14, 0.05), "acero", rot=(0, 0, 15))
    m.cil((-0.4, 0.2, 1.33), 0.14, 0.04, "oscuro", seg=10)
    m.cil((-0.4, 0.2, 1.36), 0.09, 0.02, "neon", seg=10)
    m.caja((-0.4, 0.2, 1.72), (0.5, 0.02, 0.4), "neon", rot=(0, 0, 20), p="plano_neon")
    m.barrido([(1.3, 0.5, 1.31), (1.3, 0.45, 1.8), (1.05, 0.2, 2.05)], 0.025, "acero", seg=5)
    m.torno((1.05, 0.2, 1.93), [(0.14, 0), (0.06, 0.12), (0.0, 0.14)], "oscuro", seg=8)
    m.cil((1.05, 0.2, 1.925), 0.1, 0.03, "neon_amarillo", seg=8)


@modelo(50, "industrial", "edificio_mediano", (6, 6, 5))
def entrada_mina(m):
    R = m.rng
    # Ladera de roca: masas irregulares a los lados y encima del túnel
    m.bloque((-3.0, -0.6, 0), (-1.5, 3.0, 3.8), "piedra_oscura")
    m.bloque((1.5, -0.6, 0), (3.0, 3.0, 3.8), "piedra_oscura")
    m.bloque((-3.0, -0.6, 3.3), (3.0, 3.0, 4.4), "piedra_oscura")
    m.bloque((-1.5, 2.6, 0), (1.5, 3.0, 3.3), "negro")
    m.bloque((-1.5, -0.6, 0), (1.5, 2.6, 0.06), "tierra")
    rocas = [((-2.4, -0.6, 1.0), (1.9, 1.6, 2.4)), ((-2.5, 1.2, 1.6), (1.6, 3.0, 3.4)), ((2.4, -0.5, 1.2), (1.8, 1.7, 2.8)),
             ((2.5, 1.3, 1.5), (1.6, 3.0, 3.2)), ((-1.6, 0.3, 4.0), (2.8, 2.6, 1.9)), ((1.5, 0.5, 4.1), (2.9, 2.8, 1.7)),
             ((0, 1.6, 4.3), (3.4, 2.8, 1.4)), ((-2.6, -1.4, 0.45), (1.1, 1.0, 0.9)), ((2.5, -1.7, 0.35), (0.9, 1.1, 0.7))]
    for i, (c, t) in enumerate(rocas):
        m.roca(c, t, "piedra" if i % 3 else "piedra_oscura", semilla=i * 2.1, sub=2, ruido=0.3)
    m.roca((-2.2, 0.2, 3.3), (1.2, 1.4, 0.4), "musgo", semilla=7, sub=1)
    m.roca((1.9, -0.2, 3.2), (1.0, 1.2, 0.35), "musgo", semilla=9, sub=1)
    # Portal reforzado: pies derechos, dintel, jabalcones y cartelas con pernos; tres cuadros más hacia dentro
    for i, y in enumerate((-0.75, 0.4, 1.4, 2.3)):
        g = 0.3 if i == 0 else 0.2
        mat = "hierro" if i == 0 else "madera_oscura"
        for s in (-1, 1):
            m.caja((s * 1.4, y, 1.6), (g, g, 3.2), mat, bisel=0.03 if i == 0 else 0)
        m.caja((0, y, 3.2 + g / 2 - 0.02), (3.3 if i == 0 else 3.0, g, g), mat, bisel=0.03 if i == 0 else 0)
        if i:
            m.cil((0, y, 2.98), 0.1, 0.14, "oscuro", seg=8)
            m.cil((0, y, 2.9), 0.07, 0.05, "neon_amarillo", seg=8)                       # luces interiores
    m.barrido([(0, -0.75, 3.12), (0, 0.4, 3.08), (0, 1.4, 3.08), (0, 2.3, 3.08)], 0.02, "goma", seg=4)
    for s in (-1, 1):
        m.barrido([(s * 1.38, -0.75, 2.35), (s * 0.6, -0.75, 3.18)], 0.09, "hierro", seg=4)
        m.caja((s * 1.4, -0.92, 3.05), (0.5, 0.05, 0.5), "acero", bisel=0.02)
        m.caja((s * 1.4, -0.92, 0.3), (0.5, 0.05, 0.6), "acero", bisel=0.02)
        for dz in (2.9, 3.2, 0.15, 0.45):
            m.cil((s * 1.4, -0.96, dz), 0.045, 0.04, "hierro", eje="y", seg=6)
        m.caja((s * 1.42, -0.93, 1.6), (0.1, 0.03, 1.8), "rayas")
    # Cartel MINA colgado de cadenas y farol
    m.caja((0, -0.98, 3.95), (2.2, 0.12, 0.8), "madera_oscura", bisel=0.03)
    m.texto("MINA", (0, -1.06, 3.95), 0.48, 0.06, "amarillo_p")
    for s in (-1, 1):
        m.barrido([(s * 0.9, -0.95, 3.5), (s * 0.9, -0.98, 3.6)], 0.025, "hierro", seg=4)
        m.caja((s * 0.9, -1.05, 4.2), (0.1, 0.04, 0.1), "hierro")
    m.barrido([(1.4, -0.9, 2.4), (1.4, -1.35, 2.5), (1.4, -1.35, 2.3)], 0.03, "hierro", seg=5)
    m.torno((1.4, -1.35, 1.95), [(0.08, 0), (0.15, 0.04), (0.15, 0.3), (0.05, 0.36)], "hierro", seg=8)
    m.cil((1.4, -1.35, 2.11), 0.1, 0.2, "neon_amarillo", seg=8)
    # Raíles de vagoneta con traviesas que salen del túnel, tope y minerales sueltos
    for k in range(8):
        m.caja((0, -2.7 + 0.72 * k, 0.1), (1.7, 0.24, 0.1), "madera_oscura")
    for s in (-1, 1):
        m.prisma([(-0.07, 0), (0.07, 0), (0.07, 0.03), (0.02, 0.05), (0.02, 0.12), (0.05, 0.14), (0.05, 0.18), (-0.05, 0.18),
                  (-0.05, 0.14), (-0.02, 0.12), (-0.02, 0.05), (-0.07, 0.03)], -3.0, 2.6, "hierro_viejo", "xz",
                 c=(s * 0.6, 0, 0.14))
    for i in range(6):
        m.roca((R.uniform(-2.4, -1.2), R.uniform(-2.8, -1.6), 0.15), (0.4, 0.35, 0.3),
               ("piedra", "cobre", "piedra_oscura")[i % 3], semilla=i * 3.3, sub=1)
    m.ico((-1.7, -2.1, 0.32), 0.14, "neon", sub=1, esc=(0.7, 0.7, 1.6), ruido=0.2, p="mineral_neon")
