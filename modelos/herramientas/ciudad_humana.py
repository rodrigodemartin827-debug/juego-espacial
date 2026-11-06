"""
Ciudad humana: tienda con persiana, dos edificios y una farola. Estilo ciencia ficción limpia y luminosa
(hormigón claro, paneles blancos, metal gris azulado, acentos naranja y cian, como la nave humana).

Cada modelo sale en varias mallas:
  <Nombre>          el cuerpo, con una textura horneada (colores + suciedad + oclusión ambiental)
  <Nombre>_Cristal  ventanas y escaparates (en Studio: material Glass)
  <Nombre>_Neon     lo que brilla (en Studio: material Neon)
  Tienda_Persiana   la persiana metálica, aparte para poder subirla y bajarla
  Tienda_Cartel     el letrero, aparte para ponerle un SurfaceGui con el nombre de la tienda

Medidas en studs (un personaje R6 mide 5). La fachada mira a -Y en Blender (a -Z en Roblox).

Uso:
    python modelos/herramientas/ciudad_humana.py --salida modelos/ciudad_humana [--ronda N] [--rapido]
"""

import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bpy  # noqa: E402,F401
from mathutils import Matrix, Vector  # noqa: E402

import comun as c  # noqa: E402
import kit  # noqa: E402

# (color, rugosidad, metal, suciedad[, emisión])
PALETA = {
    "Hormigon": ("#D8D4CC", 0.85, 0.0, 0.55),
    "HormigonOscuro": ("#8C8780", 0.85, 0.0, 0.6),
    "Panel": ("#EEF1F5", 0.45, 0.05, 0.25),
    "PanelGris": ("#B9C0CA", 0.5, 0.1, 0.3),
    "Metal": ("#5D6675", 0.4, 0.7, 0.2),
    "MetalOscuro": ("#2E333D", 0.45, 0.6, 0.2),
    "Acento": ("#FF8A2B", 0.45, 0.1, 0.2),
    "Teal": ("#2BA9A8", 0.45, 0.1, 0.2),
    "Madera": ("#9C6B43", 0.6, 0.0, 0.3),
    "Toldo1": ("#E2553A", 0.8, 0.0, 0.2),
    "Toldo2": ("#F2ECE0", 0.8, 0.0, 0.2),
    "Persiana": ("#C6CDD6", 0.4, 0.6, 0.3),
    "Producto1": ("#3C8DDE", 0.6, 0.0, 0.0),
    "Producto2": ("#F2C230", 0.6, 0.0, 0.0),
    "Producto3": ("#5DBB63", 0.6, 0.0, 0.0),
    "Suelo": ("#C9C2B5", 0.7, 0.0, 0.4),
    "Cristal": ("#1E3A55", 0.05, 0.3, 0.0),
    "Neon": ("#4DF0FF", 0.3, 0.0, 0.0, 3.0),
    "NeonCalido": ("#FFD08A", 0.3, 0.0, 0.0, 3.0),
    "Cartel": ("#1C2430", 0.4, 0.2, 0.0),
}
COLOR_NEON = "#4DF0FF"
COLOR_NEON_CALIDO = "#FFD08A"

# --------------------------------------------------------------------------------------------------------------
# Tienda
# --------------------------------------------------------------------------------------------------------------

TIENDA = dict(ancho=18.0, fondo=12.0, alto=9.0, hueco=(13.0, 6.0), muro=0.6, zocalo=0.5)


def tienda(carpeta, rapido):
    T = TIENDA
    w, d, h, m, z0 = T["ancho"] / 2, T["fondo"] / 2, T["alto"], T["muro"], T["zocalo"]
    hx, hz = T["hueco"][0] / 2, T["hueco"][1]
    p = kit.Pieza("Tienda", PALETA)
    cr = kit.Pieza("Tienda_Cristal", PALETA)
    ne = kit.Pieza("Tienda_Neon", PALETA)

    # Zócalo, suelo y techo.
    p.caja_de((-w - 0.3, -d - 0.3, 0), (w + 0.3, d + 0.3, z0), "HormigonOscuro")
    p.caja_de((-w + m, -d + m, z0), (w - m, d - m, z0 + 0.05), "Suelo")
    p.caja_de((-w - 0.5, -d - 0.5, h), (w + 0.5, d + 0.5, h + 0.6), "Panel")  # losa con vuelo
    p.caja_de((-w - 0.5, -d - 0.5, h + 0.6), (w + 0.5, -d + 0.1, h + 1.6), "Panel")  # pretil delantero
    for sx in (-1, 1):
        p.caja_de((sx * (w + 0.5) - (0.6 if sx > 0 else 0), -d - 0.5, h + 0.6),
                  (sx * (w + 0.5) + (0.6 if sx < 0 else 0), d + 0.5, h + 1.2), "Panel")
    p.caja_de((-w - 0.5, d - 0.1, h + 0.6), (w + 0.5, d + 0.5, h + 1.2), "Panel")
    # Franja de acento en el canto de la losa.
    p.caja_de((-w - 0.55, -d - 0.56, h + 0.15), (w + 0.55, -d - 0.5, h + 0.45), "Acento")

    # Muros: trasero, laterales y la fachada con el hueco del escaparate.
    p.caja_de((-w, d - m, z0), (w, d, h), "Hormigon")
    p.caja_de((-w, -d, z0), (-w + m, d, h), "Hormigon")
    p.caja_de((w - m, -d, z0), (w, d, h), "Hormigon")
    p.caja_de((-w, -d, z0), (-hx, -d + m, h), "Hormigon")
    p.caja_de((hx, -d, z0), (w, -d + m, h), "Hormigon")
    p.caja_de((-hx, -d, z0 + hz + 1.1), (hx, -d + m, h), "Hormigon")
    # Pilastras de panel blanco en las esquinas de la fachada.
    for sx in (-1, 1):
        p.caja_de((sx * w - (0.9 if sx > 0 else -0.0) - (0 if sx > 0 else 0.1), -d - 0.15, z0),
                  (sx * w + (0.1 if sx > 0 else 0.9), -d + 0.4, h), "Panel")
    # Mostrador (lo que se ve cuando la persiana está subida) y estantes con productos al fondo.
    p.caja_de((-hx + 0.4, -d + m, z0), (hx - 0.4, -d + m + 1.2, z0 + 2.6), "Madera")
    p.caja_de((-hx + 0.3, -d + m - 0.1, z0 + 2.6), (hx - 0.3, -d + m + 1.4, z0 + 2.8), "PanelGris")
    rnd = random.Random(4)
    for k, z in enumerate((z0 + 1.5, z0 + 3.4, z0 + 5.3)):
        p.caja_de((-w + m + 0.5, d - m - 1.4, z), (w - m - 0.5, d - m, z + 0.2), "Metal")
        x = -w + m + 0.9
        while x < w - m - 1.4:
            ancho = rnd.uniform(0.6, 1.3)
            alto = rnd.uniform(0.7, 1.5)
            p.caja_de((x, d - m - 1.2, z + 0.2), (x + ancho, d - m - 0.3, z + 0.2 + alto),
                      rnd.choice(["Producto1", "Producto2", "Producto3", "Acento", "Teal"]))
            x += ancho + rnd.uniform(0.15, 0.5)
    # Cajón de la persiana y guías laterales.
    p.caja_de((-hx - 0.4, -d - 0.95, z0 + hz), (hx + 0.4, -d, z0 + hz + 1.1), "Metal")
    for sx in (-1, 1):
        p.caja_de((sx * hx - 0.18 + (0.18 if sx > 0 else 0) - (0.0 if sx > 0 else 0.0) - 0.0, -d - 0.6, z0),
                  (sx * hx + 0.18, -d - 0.15, z0 + hz), "MetalOscuro")

    # Toldo a rayas sobre el escaparate: franjas alternas con caída en el borde.
    n = 9
    for i in range(n):
        x0 = -hx - 0.6 + i * (2 * hx + 1.2) / n
        x1 = x0 + (2 * hx + 1.2) / n
        perfil_y = [(-d - 0.95, h - 0.4), (-d - 4.2, h - 1.7), (-d - 4.2, h - 2.3), (-d - 4.3, h - 2.3),
                    (-d - 4.3, h - 1.65), (-d - 0.95, h - 0.25)]
        vs = p.loft([[Vector((x0, y, z)) for y, z in perfil_y], [Vector((x1, y, z)) for y, z in perfil_y]],
                    "Toldo1" if i % 2 == 0 else "Toldo2")
    for sx in (-1, 1):  # tirantes del toldo
        a = Vector((sx * (hx + 0.4), -d - 0.1, h - 0.3))
        b = Vector((sx * (hx + 0.4), -d - 4.0, h - 1.75))
        p.cilindro(a, 0.08, (b - a).length, "MetalOscuro", lados=6, eje=b - a)

    # Escaparate lateral (ventana en el muro izquierdo) y puerta en el derecho.
    p.caja_de((-w - 0.05, -2.5, z0 + 2.0), (-w + m + 0.05, 2.5, z0 + 2.15), "MetalOscuro")
    cr.caja_de((-w - 0.02, -2.4, z0 + 2.15), (-w + 0.1, 2.4, z0 + 5.5), "Cristal")
    p.caja_de((-w - 0.15, -2.6, z0 + 5.5), (-w, 2.6, z0 + 5.8), "Acento")
    p.caja_de((w - 0.05, 1.5, z0), (w + 0.12, 4.5, z0 + 6.2), "PanelGris")  # puerta
    p.caja_de((w + 0.12, 3.9, z0 + 2.8), (w + 0.3, 4.2, z0 + 3.4), "MetalOscuro")  # tirador
    ne.caja_de((w + 0.12, 1.5, z0 + 6.3), (w + 0.2, 4.5, z0 + 6.45), "Neon")

    # Banda de color en los muros (rompe los paños lisos) y bajante de pluviales.
    for sx in (-1, 1):
        p.caja_de((sx * w - 0.08, -d + 0.4, z0 + 0.9), (sx * w + 0.08, d, z0 + 1.5), "Teal")
    p.caja_de((-w, d - 0.08, z0 + 0.9), (w, d + 0.08, z0 + 1.5), "Teal")
    p.cilindro((w - 0.8, d + 0.25, 0), 0.18, h + 0.6, "MetalOscuro", lados=8)
    # Rótulo de horario junto a la puerta (placa).
    p.caja_de((w, 0.2, z0 + 3.2), (w + 0.1, 1.2, z0 + 4.6), "Acento")

    # Tejado: máquina de aire acondicionado y antena.
    p.caja_de((2.0, 0.5, h + 0.6), (6.0, 4.0, h + 2.4), "PanelGris")
    p.cilindro((4.0, 2.25, h + 2.4), 1.2, 0.2, "MetalOscuro", lados=12)
    p.cilindro((-6.0, 3.0, h + 0.6), 0.1, 4.0, "Metal", lados=6)

    # Neón: tira bajo el toldo y marco del cartel.
    ne.caja_de((-hx - 0.2, -d - 4.25, h - 2.45), (hx + 0.2, -d - 4.05, h - 2.33), "Neon")

    # Cartel (letrero) en el pretil, aparte para el SurfaceGui.
    ca = kit.Pieza("Tienda_Cartel", PALETA)
    ca.caja_de((-5.5, -d - 0.75, h + 0.75), (5.5, -d - 0.55, h + 2.45), "Cartel")
    for z in (h + 0.68, h + 2.45):
        ne.caja_de((-5.6, -d - 0.8, z), (5.6, -d - 0.6, z + 0.08), "Neon")

    persiana = construir_persiana(-d, z0, hx, hz)

    objetos = [kit.terminar(p, carpeta, rapido),
               kit.terminar(cr, carpeta, rapido, bisel=0, con_textura=False),
               kit.terminar(ne, carpeta, rapido, bisel=0, con_textura=False),
               kit.terminar(ca, carpeta, rapido, bisel=0.04, con_textura=False),
               kit.terminar(persiana, carpeta, rapido, bisel=0, tam=512)]

    def extra(desp):
        # Persiana cerrada: su centro y su alto. Para abrirla se encoge hacia arriba dentro del cajón.
        centro = Vector((0, -d - 0.38, z0 + hz / 2)) + desp
        return {
            "nota": "studs, ejes de Roblox, respecto al centro de la base del modelo",
            "Persiana": {
                "CentroCerrada": kit_a_roblox(centro),
                "Alto": hz,
                "AltoAbierta": 0.3,
                "como_abrir": "Size.Y -> AltoAbierta y subir el CFrame (Alto - AltoAbierta) / 2 en Y, a la vez",
            },
            "LuzToldo": kit_a_roblox(Vector((0, -d - 4.1, h - 2.6)) + desp),
        }
    return objetos, extra


def construir_persiana(y_fachada, z0, hx, hz):
    """Persiana de lamas: cada lama es una cinta con un pliegue, que da la ondulación del metal."""
    pe = kit.Pieza("Tienda_Persiana", PALETA)
    y = y_fachada - 0.38
    paso = 0.4
    n = int(hz / paso)
    for i in range(n):
        za, zb = z0 + i * paso, z0 + (i + 1) * paso
        perfil = [(y + 0.06, za), (y - 0.06, za + paso * 0.5), (y + 0.06, zb), (y + 0.1, zb),
                  (y - 0.02, za + paso * 0.5), (y + 0.1, za)]
        pe.loft([[Vector((-hx + 0.1, yy, zz)) for yy, zz in perfil],
                 [Vector((hx - 0.1, yy, zz)) for yy, zz in perfil]], "Persiana")
    # Barra inferior con el tirador.
    pe.caja_de((-hx + 0.1, y - 0.12, z0), (hx - 0.1, y + 0.14, z0 + 0.3), "MetalOscuro")
    pe.caja_de((-0.6, y - 0.25, z0 + 0.08), (0.6, y - 0.12, z0 + 0.22), "Acento")
    return pe


def kit_a_roblox(v):
    E = c.ESTUDIO
    v = Vector(v)
    return [round(-v.x, 3), round(v.z, 3), round(v.y, 3)]


# --------------------------------------------------------------------------------------------------------------
# Edificio residencial
# --------------------------------------------------------------------------------------------------------------

RESIDENCIAL = dict(ancho=22.0, fondo=18.0, plantas=4, alto_planta=9.0, bajo=10.0)


def residencial(carpeta, rapido):
    R = RESIDENCIAL
    w, d = R["ancho"] / 2, R["fondo"] / 2
    hp, nb = R["alto_planta"], R["plantas"]
    p = kit.Pieza("Edificio_Residencial", PALETA)
    cr = kit.Pieza("Edificio_Residencial_Cristal", PALETA)
    ne = kit.Pieza("Edificio_Residencial_Neon", PALETA)
    rnd = random.Random(12)

    # Planta baja comercial: retranqueada, con escaparates y marquesina.
    hb = R["bajo"]
    p.caja_de((-w, -d + 1.2, 0), (w, d, 0.4), "HormigonOscuro")
    p.caja_de((-w + 0.6, -d + 1.5, 0.4), (w - 0.6, d - 0.6, hb), "PanelGris")
    for x in (-w + 0.6, -w / 3, w / 3, w - 0.6):
        p.caja_de((x - 0.6, -d + 1.0, 0.4), (x + 0.6, -d + 1.8, hb), "Hormigon")
    cr.caja_de((-w + 1.2, -d + 1.45, 1.0), (w - 1.2, -d + 1.55, hb - 1.2), "Cristal")
    p.caja_de((-w - 0.4, -d - 1.5, hb - 0.4), (w + 0.4, -d + 1.8, hb + 0.3), "Panel")  # marquesina
    p.caja_de((-w - 0.45, -d - 1.55, hb - 0.4), (w + 0.45, -d - 1.45, hb + 0.3), "Teal")
    ne.caja_de((-w + 1, -d - 1.3, hb - 0.48), (w - 1, -d - 1.1, hb - 0.4), "NeonCalido")

    # Plantas de viviendas: forjados que sobresalen, paneles, ventanas corridas y balcones alternos.
    for k in range(nb):
        z = hb + k * hp
        p.caja_de((-w - 0.3, -d - 0.3, z), (w + 0.3, d + 0.3, z + 0.7), "Hormigon")  # forjado
        # Cuerpo: muro entre forjados con un hueco de ventana corrida en fachada y en la trasera.
        p.caja_de((-w, -d + 0.4, z + 0.7), (w, d - 0.4, z + 2.2), "Panel")
        p.caja_de((-w, -d + 0.4, z + hp - 1.6), (w, d - 0.4, z + hp), "Panel")
        p.caja_de((-w, -d + 0.4, z + 2.2), (-w + 2.0, d - 0.4, z + hp - 1.6), "Panel")
        p.caja_de((w - 2.0, -d + 0.4, z + 2.2), (w, d - 0.4, z + hp - 1.6), "Panel")
        p.caja_de((-0.7, -d + 0.4, z + 2.2), (0.7, d - 0.4, z + hp - 1.6), "PanelGris")
        p.caja_de((-w + 2.0, -d + 1.2, z + 2.2), (w - 2.0, d - 1.2, z + hp - 1.6), "PanelGris")  # interior
        for sy in (-1, 1):
            yv = sy * (d - 0.45)
            for x0, x1 in ((-w + 2.0, -0.7), (0.7, w - 2.0)):
                cr.caja_de((x0, yv - 0.05, z + 2.2), (x1, yv + 0.05, z + hp - 1.6), "Cristal")
                # Ventanas encendidas al azar (de noche se ven desde lejos).
                if rnd.random() < 0.25:
                    # Media ventana: la otra mitad la tapa una cortina (la textura del interior).
                    ne.caja_de((x0 + 0.3, yv + sy * 0.3, z + 2.4), ((x0 + x1) / 2, yv + sy * 0.35, z + hp - 1.8),
                               "NeonCalido")
                # Parteluces.
                for xm in (x0 + (x1 - x0) / 3, x0 + 2 * (x1 - x0) / 3):
                    p.caja_de((xm - 0.1, yv - 0.12, z + 2.2), (xm + 0.1, yv + 0.12, z + hp - 1.6), "Metal")
        # Ventanas laterales (dos por planta) con alféizar.
        for sx in (-1, 1):
            for yc in (-4.0, 4.0):
                cr.caja_de((sx * w - 0.05, yc - 2.0, z + 2.6), (sx * w + 0.05, yc + 2.0, z + hp - 2.0), "Cristal")
                p.caja_de((sx * w - 0.25, yc - 2.2, z + 2.35), (sx * w + 0.25, yc + 2.2, z + 2.6), "PanelGris")
        # Balcón con barandilla de cristal (en plantas alternas, desplazado).
        bx = -w + 3.0 if k % 2 == 0 else 1.5
        p.caja_de((bx, -d - 3.0, z + 0.3), (bx + 7.5, -d, z + 0.75), "Panel")
        p.caja_de((bx - 0.02, -d - 3.05, z + 0.3), (bx + 7.52, -d - 2.95, z + 0.75), "Teal")
        cr.caja_de((bx + 0.15, -d - 2.95, z + 0.75), (bx + 7.35, -d - 2.85, z + 2.6), "Cristal")
        p.caja_de((bx, -d - 3.05, z + 2.6), (bx + 7.5, -d - 2.75, z + 2.78), "Metal")
        for sx in (bx + 0.12, bx + 7.38):
            p.caja_de((sx - 0.12, -d - 3.0, z + 0.75), (sx + 0.12, -d, z + 2.78), "Metal")
        # Jardinera en el balcón.
        p.caja_de((bx + 0.4, -d - 2.7, z + 0.75), (bx + 2.4, -d - 2.0, z + 1.4), "Madera")
        p.caja_de((bx + 0.5, -d - 2.6, z + 1.4), (bx + 2.3, -d - 2.1, z + 1.7), "Producto3")

    zt = hb + nb * hp
    # Aletas verticales de color en la fachada (de la marquesina a la cubierta): dan ritmo y color.
    for x in (-w + 1.0, w - 1.0):
        p.caja_de((x - 0.25, -d - 0.9, hb + 0.3), (x + 0.25, -d - 0.3, zt + 1.7), "Teal")
    # Cubierta: losa, pretil, depósito de agua, placas solares y franja vertical de acento en la esquina.
    p.caja_de((-w - 0.3, -d - 0.3, zt), (w + 0.3, d + 0.3, zt + 0.7), "Hormigon")
    p.caja_de((-w - 0.3, -d - 0.3, zt + 0.7), (w + 0.3, -d + 0.2, zt + 1.7), "Panel")
    p.caja_de((-w - 0.3, d - 0.2, zt + 0.7), (w + 0.3, d + 0.3, zt + 1.7), "Panel")
    for sx in (-1, 1):
        p.caja_de((sx * w - 0.5 * (1 - sx) - 0.3 * (1 + sx) * 0, -d, zt + 0.7),
                  (sx * w + 0.5 * (1 + sx) * 0.6 - 0.0, d, zt + 1.7), "Panel")
    p.cilindro((-5, 4, zt + 0.7), 2.2, 4.5, "PanelGris", lados=14)
    p.cilindro((-5, 4, zt + 5.2), 2.3, 0.6, "Metal", lados=14, radio2=0.6)
    for i in range(3):
        p.caja((3 + i * 2.6, -1.0, zt + 1.9), (2.3, 4.5, 0.15), "MetalOscuro",
               giro=Matrix.Rotation(math.radians(-25), 3, "X"))
        p.caja((3 + i * 2.6, -0.2, zt + 1.1), (0.15, 0.15, 1.2), "Metal")
    p.caja_de((w + 0.3, -d - 0.31, 0.4), (w + 1.1, -d + 1.2, zt + 1.7), "Teal")  # pilar de esquina
    ne.caja_de((w + 1.1, -d - 0.2, hb), (w + 1.18, -d + 1.0, zt), "Neon")

    objetos = [kit.terminar(p, carpeta, rapido, bisel=0.06),
               kit.terminar(cr, carpeta, rapido, bisel=0, con_textura=False),
               kit.terminar(ne, carpeta, rapido, bisel=0, con_textura=False)]
    return objetos, None


# --------------------------------------------------------------------------------------------------------------
# Torre de oficinas
# --------------------------------------------------------------------------------------------------------------

TORRE = [  # (medio ancho, medio fondo, z0, z1)
    (11.0, 11.0, 0.0, 22.0),
    (8.5, 8.5, 22.0, 46.0),
    (6.0, 6.0, 46.0, 60.0),
]


def torre(carpeta, rapido):
    p = kit.Pieza("Edificio_Torre", PALETA)
    cr = kit.Pieza("Edificio_Torre_Cristal", PALETA)
    ne = kit.Pieza("Edificio_Torre_Neon", PALETA)
    for i, (w, d, z0, z1) in enumerate(TORRE):
        # Núcleo (detrás del cristal) y muro cortina con montantes.
        p.caja_de((-w + 0.6, -d + 0.6, z0), (w - 0.6, d - 0.6, z1), "MetalOscuro")
        for sy in (-1, 1):
            cr.caja_de((-w + 0.4, sy * d - 0.05, z0 + 0.8), (w - 0.4, sy * d + 0.05, z1 - 0.4), "Cristal")
        for sx in (-1, 1):
            cr.caja_de((sx * w - 0.05, -d + 0.4, z0 + 0.8), (sx * w + 0.05, d - 0.4, z1 - 0.4), "Cristal")
        # Montantes verticales cada ~3,6 studs y franjas horizontales cada planta (6 studs).
        n = max(2, round(2 * w / 3.6))
        for k in range(n + 1):
            t = -w + k * 2 * w / n
            for sy in (-1, 1):
                p.caja_de((t - 0.12, sy * d - 0.2, z0), (t + 0.12, sy * d + 0.2, z1), "Panel")
                p.caja_de((sy * d - 0.2, t - 0.12, z0), (sy * d + 0.2, t + 0.12, z1), "Panel")
        z = z0 + 6.0
        while z < z1 - 1.0:
            p.caja_de((-w - 0.15, -d - 0.15, z - 0.25), (w + 0.15, d + 0.15, z + 0.25), "PanelGris")
            z += 6.0
        # Remate de cada cuerpo: cornisa blanca con canto naranja (o cian en el de arriba).
        p.caja_de((-w - 0.5, -d - 0.5, z1 - 0.4), (w + 0.5, d + 0.5, z1 + 0.6), "Panel")
        ne.caja_de((-w - 0.55, -d - 0.56, z1 - 0.1), (w + 0.55, -d - 0.5, z1 + 0.1),
                   "Neon" if i == len(TORRE) - 1 else "NeonCalido")
    # Esquinas del basamento en naranja: el color de la marca humana, visible desde lejos.
    w0, d0 = TORRE[0][0], TORRE[0][1]
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.caja_de((sx * w0 - 0.45, sy * d0 - 0.45, 0), (sx * w0 + 0.45, sy * d0 + 0.45, TORRE[0][3]), "Acento")
    # Entrada: pórtico con marquesina y logo.
    w, d = TORRE[0][0], TORRE[0][1]
    p.caja_de((-5, -d - 4, 0), (5, -d, 0.3), "HormigonOscuro")
    p.caja_de((-5.2, -d - 4.2, 7.0), (5.2, -d, 7.6), "Panel")
    for sx in (-4.6, 4.6):
        p.cilindro((sx, -d - 3.6, 0.3), 0.35, 6.7, "Metal", lados=10)
    p.caja_de((-5.25, -d - 4.25, 7.0), (5.25, -d - 4.15, 7.6), "Acento")
    ne.caja_de((-3, -d - 0.3, 8.2), (3, -d - 0.2, 9.4), "Neon")
    # Cubierta: helipuerto con baliza y antena.
    zt = TORRE[-1][3] + 0.6
    p.cilindro((0, 0, zt), 4.8, 0.4, "PanelGris", lados=16)
    p.caja((0, 0, zt + 0.45), (3.0, 0.5, 0.05), "Acento")
    p.caja((-1.2, 0, zt + 0.45), (0.5, 3.0, 0.05), "Acento")
    p.caja((1.2, 0, zt + 0.45), (0.5, 3.0, 0.05), "Acento")
    p.cilindro((4.2, 4.2, zt - 0.6), 0.25, 9.0, "Metal", lados=6, radio2=0.08)
    ne.cilindro((4.2, 4.2, zt + 8.4), 0.3, 0.6, "Neon", lados=8)
    objetos = [kit.terminar(p, carpeta, rapido, bisel=0.05),
               kit.terminar(cr, carpeta, rapido, bisel=0, con_textura=False),
               kit.terminar(ne, carpeta, rapido, bisel=0, con_textura=False)]
    return objetos, None


# --------------------------------------------------------------------------------------------------------------
# Farola
# --------------------------------------------------------------------------------------------------------------


def farola(carpeta, rapido):
    p = kit.Pieza("Farola", PALETA)
    ne = kit.Pieza("Farola_Neon", PALETA)
    # Base octogonal y fuste que se estrecha.
    p.cilindro((0, 0, 0), 0.9, 0.5, "HormigonOscuro", lados=8)
    p.cilindro((0, 0, 0.5), 0.6, 1.2, "MetalOscuro", lados=8, radio2=0.42)
    p.cilindro((0, 0, 1.7), 0.34, 9.5, "Panel", lados=10, radio2=0.24)
    p.cilindro((0, 0, 4.5), 0.4, 0.5, "MetalOscuro", lados=10)
    ne.cilindro((0, 0, 4.6), 0.42, 0.3, "Neon", lados=10)
    # Brazo curvo: loft de anillos a lo largo de un arco hacia -Y (hacia la calle).
    anillos = []
    for i in range(9):
        t = i / 8
        a = t * math.pi / 2
        centro = Vector((0, -2.6 * math.sin(a), 11.2 + 2.0 * (1 - math.cos(a)) * 0.6 + t * 0.4))
        tang = Vector((0, -math.cos(a), 0.6 * math.sin(a) + 0.2)).normalized()
        q = tang.to_track_quat("Z", "Y")
        r = 0.24 - 0.06 * t
        anillos.append([centro + q @ v for v in kit.anillo_z(0, r, r, 8)])
    p.loft(anillos, "Panel")
    # Cabeza de la lámpara: cápsula alargada y plana con el difusor brillante debajo.
    cab = [kit.anillo(y, w, hh, 13.0, 10, 2.6) for y, w, hh in
           [(-1.3, 0.5, 0.2), (-1.8, 1.1, 0.42), (-3.4, 1.2, 0.46), (-4.6, 0.9, 0.36), (-5.0, 0.3, 0.12)]]
    p.loft(cab, "Panel")
    p.caja((0, -3.1, 13.27), (0.5, 2.6, 0.06), "Acento")
    ne.caja((0, -3.2, 12.76), (0.8, 2.6, 0.06), "NeonCalido")
    objetos = [kit.terminar(p, carpeta, rapido, bisel=0.03, tam=512),
               kit.terminar(ne, carpeta, rapido, bisel=0, con_textura=False)]

    def extra(desp):
        return {"nota": "studs, ejes de Roblox, respecto al centro de la base",
                "Luz": kit_a_roblox(Vector((0, -3.2, 12.5)) + desp),
                "luz_recomendada": "SpotLight hacia abajo, Brightness 2, Range 24, Angle 110, color #FFD08A"}
    return objetos, extra


def vista_persiana_abierta(objetos, tmp, tam, muestras):
    """Render de la tienda con la persiana subida (escalada en Z hacia su borde de arriba, como en Studio)."""
    per = next(o for o in objetos if o.name == "Tienda_Persiana")
    mn, mx = c.caja_limite([per])
    arriba = mx.z
    datos = per.data.copy()
    factor = 0.3 / TIENDA["hueco"][1]
    for v in per.data.vertices:
        v.co.z = arriba + (v.co.z - arriba) * factor
    r = c.renderizar_vistas(objetos, tmp, [("Persiana abierta", -25, 12)], tam=tam, muestras=muestras,
                            con_malla=False, prefijo="Tienda_abierta", margen=0.9)
    per.data = datos
    return r


ITEMS = [
    dict(archivo="Tienda", titulo="Tienda humana", construir=tienda, vista_extra=vista_persiana_abierta),
    dict(archivo="Edificio_Residencial", titulo="Edificio residencial", construir=residencial),
    dict(archivo="Edificio_Torre", titulo="Torre de oficinas", construir=torre),
    dict(archivo="Farola", titulo="Farola", construir=farola),
]

if __name__ == "__main__":
    a = kit.argumentos()
    kit.ejecutar_lote(ITEMS, a.salida, "Ciudad humana", a.ronda, a.rapido, solo=a.solo,
                      nota="Cuerpo con textura horneada · _Cristal: Glass · _Neon: Neon · Persiana y Cartel aparte")
