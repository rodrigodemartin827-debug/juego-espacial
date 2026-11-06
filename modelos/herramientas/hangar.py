"""
Hangar humano donde se forja la primera nave.

Mismo planteamiento que el hangar que crea el código (src/server/Servicios/Hangar.luau): planta de 46 × 46 studs,
tres muros, el frente abierto y SIN techo (la nave despega hacia arriba), con la plataforma de despegue en el
centro. Lo nuevo es el aspecto: estructura de pilares y celosías, ventanales altos, puente grúa, y al fondo la
FORJA: un gran anillo de fabricación con dos brazos robóticos y la consola, donde el jugador forja su primera nave.

Mallas:
  Hangar          estructura, suelo y maquinaria, con textura horneada
  Hangar_Cristal  ventanales (Glass)
  Hangar_Neon     anillo de la plataforma, interior del anillo de la forja, pantallas y luces (Neon)
  Hangar_Cartel   el letrero de la entrada (para un SurfaceGui)

Hangar.json da los puntos de anclaje: la plataforma, la consola, la forja y las luces.

Uso:
    python modelos/herramientas/hangar.py --salida modelos/hangar [--ronda N] [--rapido]
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
from ciudad_humana import PALETA as PALETA_CIUDAD, kit_a_roblox  # noqa: E402

PALETA = dict(PALETA_CIUDAD)
PALETA.update({
    "Suelo": ("#7D8189", 0.75, 0.1, 0.55),
    "Linea": ("#F2B43A", 0.6, 0.0, 0.4),
    "Estructura": ("#4A5262", 0.45, 0.6, 0.3),
    "Muro": ("#C9CED6", 0.6, 0.15, 0.45),
    "Pantalla": ("#0E1A26", 0.2, 0.2, 0.0),
})

ANCHO = 46.0  # interior, como el hangar de código
ALTO = 22.0
MURO = 1.0


def construir(carpeta, rapido):
    rnd = random.Random(21)
    w = ANCHO / 2
    p = kit.Pieza("Hangar", PALETA)
    cr = kit.Pieza("Hangar_Cristal", PALETA)
    ne = kit.Pieza("Hangar_Neon", PALETA)
    ca = kit.Pieza("Hangar_Cartel", PALETA)

    # ---- Suelo: losa, bordillo y marcas pintadas --------------------------------------------------------
    p.caja_de((-w - 2, -w - 4, 0), (w + 2, w + 2, 0.6), "Suelo")
    p.caja_de((-w - 2.2, -w - 4.2, 0), (w + 2.2, -w - 3.6, 0.65), "HormigonOscuro")
    for sx in (-1, 1):  # franjas de seguridad a los lados del paso de entrada
        for i in range(8):
            y = -w - 3.4 + i * 1.6
            p.caja((sx * (w - 2.5), y, 0.62), (1.6, 0.7, 0.04), "Linea", giro=Matrix.Rotation(0.6 * sx, 3, "Z"))
    # Cuadrado de maniobra alrededor de la plataforma.
    for sx in (-1, 1):
        p.caja_de((sx * 16 - 0.25, -16, 0.6), (sx * 16 + 0.25, 16, 0.64), "Linea")
        p.caja_de((-16, sx * 16 - 0.25, 0.6), (16, sx * 16 + 0.25, 0.64), "Linea")

    # ---- Plataforma de despegue -----------------------------------------------------------------------------
    p.cilindro((0, 0, 0.6), 14.5, 0.35, "MetalOscuro", lados=32)
    p.cilindro((0, 0, 0.95), 13.0, 0.12, "Metal", lados=32)
    # Anillo luminoso: solo la cinta (sin tapas, que llenarían el círculo entero).
    ne.loft([kit.anillo_z(1.0, 13.9, 13.9, 32), kit.anillo_z(1.0, 13.3, 13.3, 32),
             kit.anillo_z(1.08, 13.3, 13.3, 32), kit.anillo_z(1.08, 13.9, 13.9, 32)], "Neon",
            tapar_inicio=False, tapar_fin=False)
    for i in range(8):  # marcas radiales
        a = i * math.tau / 8
        p.caja((math.cos(a) * 10.5, math.sin(a) * 10.5, 1.09), (3.0, 0.45, 0.04), "Linea",
               giro=Matrix.Rotation(a, 3, "Z"))
    # Calzos de la nave.
    for sx in (-1, 1):
        p.caja((sx * 2.0, 0.5, 1.9), (1.0, 9.0, 1.7), "Estructura")

    # ---- Muros: pilares, paneles, zócalo y ventanales altos ---------------------------------------------------
    def muro(eje_x, signo):
        """Muro lateral (eje_x=True: en x = ±w) o trasero (en y = +w)."""
        n = 5
        for i in range(n + 1):
            t = -w + i * ANCHO / n
            pos = Vector((signo * (w + MURO / 2), t, 0)) if eje_x else Vector((t, w + MURO / 2, 0))
            tam = (MURO * 2.2, 1.6, ALTO + 1.5) if eje_x else (1.6, MURO * 2.2, ALTO + 1.5)
            p.caja(pos + Vector((0, 0, (ALTO + 1.5) / 2 + 0.6)), tam, "Estructura")
        for i in range(n):
            t0, t1 = -w + i * ANCHO / n + 0.8, -w + (i + 1) * ANCHO / n - 0.8
            tm = (t0 + t1) / 2
            for z0, z1, mat in ((0.6, 2.4, "HormigonOscuro"), (2.4, 13.5, "Muro"), (17.5, ALTO, "Muro")):
                if eje_x:
                    p.caja_de((signo * w - (MURO if signo < 0 else 0) * 1 + (0 if signo < 0 else 0),
                               t0, z0), (signo * w + (MURO if signo > 0 else 0), t1, z1), mat)
                else:
                    p.caja_de((t0, w, z0), (t1, w + MURO, z1), mat)
            # Nervios horizontales del panel.
            for z in (6.0, 9.8):
                if eje_x:
                    p.caja((signo * (w - 0.1), tm, z), (0.3, t1 - t0, 0.3), "PanelGris")
                else:
                    p.caja((tm, w - 0.1, z), (t1 - t0, 0.3, 0.3), "PanelGris")
            # Ventanal entre 13,5 y 17,5 con parteluz.
            if eje_x:
                cr.caja((signo * (w + MURO / 2), tm, 15.5), (0.15, t1 - t0, 4.0), "Cristal")
                p.caja((signo * (w + MURO / 2), tm, 15.5), (0.4, 0.25, 4.0), "Estructura")
            else:
                cr.caja((tm, w + MURO / 2, 15.5), (t1 - t0, 0.15, 4.0), "Cristal")
                p.caja((tm, w + MURO / 2, 15.5), (0.25, 0.4, 4.0), "Estructura")
            # Lámpara de pared bajo el ventanal.
            if eje_x:
                p.caja((signo * (w - 0.4), tm, 12.6), (0.8, 2.4, 0.5), "MetalOscuro")
                ne.caja((signo * (w - 0.42), tm, 12.32), (0.6, 2.2, 0.08), "NeonCalido")
            else:
                p.caja((tm, w - 0.4, 12.6), (2.4, 0.8, 0.5), "MetalOscuro")
                ne.caja((tm, w - 0.42, 12.32), (2.2, 0.6, 0.08), "NeonCalido")

    muro(True, -1)
    muro(True, 1)
    muro(False, 1)
    # Fuera: franja naranja a media altura y tiras de luz en los pilares (se ve desde lejos que es el hangar).
    for sx in (-1, 1):
        p.caja_de((sx * (w + MURO) - 0.06, -w, 2.4), (sx * (w + MURO) + 0.06, w + MURO, 3.4), "Acento")
        for i in range(6):
            t = -w + i * ANCHO / 5
            ne.caja((sx * (w + MURO * 2.2 / 2 + 0.55), t, 12.0), (0.08, 0.4, 16.0), "Neon")
    p.caja_de((-w - MURO, w + MURO - 0.06, 2.4), (w + MURO, w + MURO + 0.06, 3.4), "Acento")
    # Remate superior: viga perimetral con canto naranja.
    for sx in (-1, 1):
        p.caja_de((sx * w - (1.4 if sx < 0 else -0.0) - (0 if sx < 0 else 0), -w - 1, ALTO),
                  (sx * w + (1.4 if sx > 0 else 0), w + 1.4, ALTO + 1.6), "Panel")
        p.caja_de((sx * (w + 1.4) - 0.06, -w - 1, ALTO + 0.5), (sx * (w + 1.4) + 0.06, w + 1.4, ALTO + 1.0),
                  "Acento")
    p.caja_de((-w - 1.4, w, ALTO), (w + 1.4, w + 1.4, ALTO + 1.6), "Panel")
    # Pórtico de entrada (frente abierto): dintel con el letrero.
    p.caja_de((-w - 1.4, -w - 1.2, ALTO), (w + 1.4, -w + 0.4, ALTO + 2.6), "Panel")
    p.caja_de((-w - 1.45, -w - 1.25, ALTO + 0.9), (w + 1.45, -w - 1.15, ALTO + 1.5), "Acento")
    for sx in (-1, 1):
        p.caja_de((sx * w - 1.2, -w - 1.2, 0.6), (sx * w + 1.2, -w + 0.4, ALTO), "Estructura")
    ca.caja_de((-9, -w - 1.5, ALTO + 0.2), (9, -w - 1.25, ALTO + 2.4), "Cartel")
    ne.caja_de((-9.1, -w - 1.55, ALTO + 0.12), (9.1, -w - 1.3, ALTO + 0.22), "Neon")

    # ---- Puente grúa: dos carriles sobre los muros laterales y una viga que cruza con el carro ----------------
    yc = 9.0
    p.caja_de((-w - 0.2, yc - 0.9, ALTO - 2.6), (w + 0.2, yc + 0.9, ALTO - 1.0), "Acento")
    for sx in (-1, 1):
        p.caja_de((sx * w - 0.8, yc - 1.4, ALTO - 3.2), (sx * w + 0.2 * sx, yc + 1.4, ALTO - 0.6), "MetalOscuro")
    p.caja_de((-4.5, yc - 1.4, ALTO - 3.6), (-1.5, yc + 1.4, ALTO - 2.4), "MetalOscuro")
    p.cilindro((-3.0, yc, ALTO - 3.6), 0.08, 5.0, "MetalOscuro", lados=6, eje=(0, 0, -1))
    p.caja((-3.0, yc, ALTO - 9.0), (1.2, 0.6, 0.8), "Linea")

    # ---- La forja: anillo vertical al fondo, brazos robóticos y consola ---------------------------------------
    yf = w - 6.0
    centro = Vector((0, yf, 10.5))
    rx = 8.0
    n = 28
    perfil = [(rx + 1.6, -0.9), (rx + 1.6, 0.9), (rx, 1.2), (rx, -1.2)]  # (radio, y) sección del aro
    anillos = []
    for i in range(n):
        a = math.tau * i / n
        dirr = Vector((math.cos(a), 0, math.sin(a)))
        anillos.append([centro + dirr * r + Vector((0, yy, 0)) for r, yy in perfil])
    # Loft cerrado alrededor del aro (cada "anillo" del loft es la sección en un ángulo).
    vs = []
    for k in range(n):
        vs.append(anillos[k])
    for k in range(n):
        a0, a1 = anillos[k], anillos[(k + 1) % n]
        p.loft([a0, a1], "Estructura", tapar_inicio=False, tapar_fin=False)
    # Interior brillante del aro (cara interna) y segmentos naranjas.
    for k in range(n):
        a = math.tau * (k + 0.5) / n
        dirr = Vector((math.cos(a), 0, math.sin(a)))
        ne.caja(centro + dirr * (rx - 0.05) + Vector((0, 0, 0)), (1.2, 1.6, 0.1), "Neon",
                giro=Matrix.Rotation(-a + math.pi / 2, 3, "Y"))
        if k % 7 == 0:
            p.caja(centro + dirr * (rx + 1.7), (1.5, 2.2, 0.6), "Acento", giro=Matrix.Rotation(-a + math.pi / 2, 3, "Y"))
    # Núcleo de energía en el centro del anillo: un octaedro alargado que brilla (lo que «forja» la nave).
    nucleo = [Vector((0, 0, 1.6)), Vector((1.0, 0, 0)), Vector((0, 1.0, 0)), Vector((-1.0, 0, 0)),
              Vector((0, -1.0, 0)), Vector((0, 0, -1.6))]
    bm = ne.bm
    vv = [bm.verts.new(centro + q) for q in nucleo]
    for i in range(4):
        j = 1 + (i + 1) % 4
        bm.faces.new((vv[0], vv[1 + i], vv[j]))
        bm.faces.new((vv[5], vv[j], vv[1 + i]))
    for f in bm.faces[-8:]:
        f.material_index = ne.m("Neon")
    # Conductos desde el pedestal hasta el aro.
    for sx in (-1, 1):
        a0 = Vector((sx * 3.5, yf - 1.2, 2.6))
        a1 = centro + Vector((sx * 6.0, -1.2, -5.0))
        p.cilindro(a0, 0.35, (a1 - a0).length, "Teal", lados=8, eje=a1 - a0)
    # Pedestal del anillo.
    p.caja_de((-5, yf - 2.5, 0.6), (5, yf + 2.5, 2.6), "Estructura")
    p.caja_de((-3.0, yf - 1.6, 2.6), (3.0, yf + 1.6, 3.2), "MetalOscuro")

    # Brazos robóticos (dos, simétricos): base giratoria, brazo, antebrazo y cabezal soldador.
    def brazo(sx):
        base = Vector((sx * 9.5, 6.0, 0.6))
        p.cilindro(base, 1.6, 1.0, "MetalOscuro", lados=12)
        p.cilindro(base + Vector((0, 0, 1.0)), 1.2, 1.2, "Acento", lados=12)
        hombro = base + Vector((0, 0, 2.6))
        codo = hombro + Vector((-sx * 2.0, -2.5, 6.5))
        muneca = codo + Vector((-sx * 3.0, -3.5, -2.0))
        for a, b, r, mat in ((hombro, codo, 0.75, "Panel"), (codo, muneca, 0.55, "Panel")):
            p.cilindro(a, r, (b - a).length, mat, lados=8, eje=b - a)
            p.cilindro(a - Vector((0.9, 0, 0)), r + 0.25, 1.8, "MetalOscuro", lados=10, eje="X")
        p.cilindro(codo - Vector((0.8, 0, 0)), 0.75, 1.6, "MetalOscuro", lados=10, eje="X")
        cab = muneca + (muneca - codo).normalized() * 1.2
        p.cilindro(muneca, 0.45, 1.2, "MetalOscuro", lados=8, eje=muneca - codo, radio2=0.25)
        ne.cilindro(cab, 0.18, 0.3, "Neon", lados=6, eje=muneca - codo)
        return cab

    puntas = [brazo(-1), brazo(1)]

    # Consola de la forja (a un lado de la plataforma) con pantalla y teclado.
    cx, cy = 12.0, -6.0
    p.caja_de((cx - 1.6, cy - 1.0, 0.6), (cx + 1.6, cy + 1.0, 3.6), "Panel")
    p.caja((cx, cy - 0.6, 3.9), (3.4, 1.6, 0.4), "MetalOscuro", giro=Matrix.Rotation(math.radians(-25), 3, "X"))
    p.caja((cx, cy + 0.6, 5.6), (3.4, 0.3, 2.4), "MetalOscuro")
    ne.caja((cx, cy + 0.42, 5.6), (3.0, 0.06, 2.0), "Neon")
    ne.caja((cx, cy - 0.85, 4.15), (2.6, 0.9, 0.05), "Neon", giro=Matrix.Rotation(math.radians(-25), 3, "X"))

    # ---- Pasarela en el muro del fondo, con barandilla y escalera ---------------------------------------------
    zp = 8.0
    p.caja_de((-w, w - 3.0, zp - 0.4), (w, w, zp), "Estructura")
    p.caja_de((-w, w - 3.05, zp - 0.15), (w, w - 2.95, zp + 0.05), "Linea")
    for i in range(16):
        x = -w + 1.0 + i * (ANCHO - 2.0) / 15
        p.caja((x, w - 2.9, zp + 1.0), (0.15, 0.15, 2.0), "MetalOscuro")
    p.caja_de((-w, w - 2.98, zp + 1.9), (w, w - 2.82, zp + 2.1), "Acento")
    for i in range(12):  # escalera junto al muro derecho, bajando hacia delante
        z = zp - (i + 1) * zp / 12
        p.caja((w - 1.6, w - 3.6 - i * 0.9, z + 0.2), (2.4, 0.9, 0.3), "Estructura")
    p.caja((w - 0.3, w - 3.6 - 5.0, zp / 2 + 1.0), (0.15, 11.0, 0.15), "Acento",
           giro=Matrix.Rotation(math.atan2(zp, 10.8), 3, "X"))
    for y in (w - 3.2, w - 10.0):  # pilares bajo la pasarela
        pass
    for x in (-w + 6, -w + 18, w - 18, w - 6):
        p.caja((x, w - 2.6, zp / 2), (0.5, 0.5, zp - 0.4), "MetalOscuro")

    # ---- Bolardos en la entrada (pintados a franjas) ---------------------------------------------------------
    for sx in (-1, 1):
        for k in range(2):
            x = sx * (6.0 + k * 3.0)
            p.cilindro((x, -w - 2.4, 0.6), 0.45, 1.6, "Linea", lados=8)
            p.cilindro((x, -w - 2.4, 1.3), 0.47, 0.3, "MetalOscuro", lados=8)
            ne.cilindro((x, -w - 2.4, 2.2), 0.3, 0.1, "Neon", lados=8)

    # ---- Atrezo: cajas, bidones, depósitos, banco de trabajo, estantería -----------------------------------
    for i in range(7):
        x = -w + 2.5 + (i % 3) * 2.3 + rnd.uniform(-0.2, 0.2)
        y = -w + 6 + (i // 3) * 2.3
        z = 0.6 + (2.0 if i == 6 else 0)
        p.caja((x, y, z + 1.0), (2.0, 2.0, 2.0), "Acento" if i % 3 == 0 else "PanelGris",
               giro=Matrix.Rotation(rnd.uniform(-0.15, 0.15), 3, "Z"))
    for i in range(4):
        p.cilindro((w - 2.0 - (i % 2) * 1.6, -w + 3.0 + (i // 2) * 1.6, 0.6), 0.7, 2.2, "Teal", lados=10)
    for i in range(2):  # depósitos de combustible
        p.cilindro((-w + 3.5, w - 4.0 - i * 4.5, 0.6), 1.8, 7.0, "Panel", lados=14)
        p.cilindro((-w + 3.5, w - 4.0 - i * 4.5, 7.6), 1.8, 0.8, "MetalOscuro", lados=14, radio2=0.8)
        p.caja((-w + 3.5, w - 4.0 - i * 4.5, 4.0), (3.7, 0.3, 0.5), "Acento")
    p.caja_de((w - 6.5, w - 3.2, 0.6), (w - 1.5, w - 1.2, 3.2), "Madera")  # banco de trabajo
    p.caja_de((w - 6.6, w - 3.3, 3.2), (w - 1.4, w - 1.1, 3.45), "Metal")
    p.caja_de((w - 6.0, w - 1.2, 3.45), (w - 2.0, w - 0.8, 7.0), "PanelGris")  # tablero de herramientas
    for i in range(5):
        p.caja((w - 5.5 + i * 0.8, w - 1.25, 5.2 + (i % 2) * 0.6), (0.2, 0.15, 1.2), "MetalOscuro")

    objetos = [kit.terminar(p, carpeta, rapido, bisel=0.06, ao=1.4),
               kit.terminar(cr, carpeta, rapido, bisel=0, con_textura=False),
               kit.terminar(ne, carpeta, rapido, bisel=0, con_textura=False),
               kit.terminar(ca, carpeta, rapido, bisel=0.04, con_textura=False)]

    def extra(desp):
        return {
            "nota": "studs, ejes de Roblox, respecto al centro de la base del modelo",
            "Plataforma": kit_a_roblox(Vector((0, 0, 1.1)) + desp),
            "Consola": kit_a_roblox(Vector((cx, cy - 1.2, 3.6)) + desp),
            "Forja": kit_a_roblox(centro + desp),
            "PuntasBrazos": [kit_a_roblox(v + desp) for v in puntas],
            "Gancho": kit_a_roblox(Vector((-3.0, yc, ALTO - 9.4)) + desp),
        }
    return objetos, extra


ITEMS = [dict(archivo="Hangar", titulo="Hangar humano", construir=construir)]

if __name__ == "__main__":
    a = kit.argumentos()
    vistas = [("Frente", 0, 18), ("3/4", -35, 32), ("Lateral", -90, 15), ("3/4 trasera", 145, 35),
              ("Arriba", 0, 80), ("Interior", 10, 8)]
    kit.ejecutar_lote(ITEMS, a.salida, "Hangar humano", a.ronda, a.rapido, vistas=vistas,
                      nota="Hangar · _Cristal: Glass · _Neon: Neon · _Cartel: SurfaceGui", margen=0.95)
