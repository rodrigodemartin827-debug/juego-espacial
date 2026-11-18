"""
La clínica del pueblo: geometría completa (studs, Z arriba, fachada hacia -Y).

Planta del edificio: 10,4 x 10 studs (paredes exteriores en x = ±5,2 e y = ±5,0), zócalo de 0,4, paredes de 0,5 de
grosor hasta 7,35 (pretil incluido) y techo plano a 6,95. Delante, la rampa de 4,4 studs y su rellano; detrás, el
escalón de la puerta de suministros.

Plano de la fachada (vista desde delante, u = x):
    -4,7 ......... -3,0 [ PUERTA DOBLE 3,6 ] 0,6 ............ 2,7 [VENTANA] 4,5 ... 4,7
     placa, tablón       las hojas se esconden    gel, papelera     cruz luminosa encima
                         dentro de la pared (bolsillos) y cuelgan de un raíl visible tras una tapa transparente
"""

import math

from mathutils import Matrix, Vector

import geo
from geo import V, caja, caja_c, cilindro, prisma, tornillo, tubo

# Medidas principales
X_EXT, Y_EXT = 5.2, 5.0  # cara exterior de las paredes
GROSOR = 0.5
SUELO = 0.4  # altura del suelo interior (zócalo)
TECHO = 6.95  # cara superior del forjado
PRETIL = 7.35  # remate de las paredes
CORTE_INT = 6.6  # techo interior

GRUPOS = [
    "Edificio", "Interior", "Techo_Equipos", "Detalles", "Rampa", "Mobiliario", "Cristales",
    "Puerta_Izq", "Puerta_Der", "Puerta_Izq_Cristal", "Puerta_Der_Cristal", "Puerta_Trasera",
    "Cruz_neon", "Marquesina_neon", "Farola_neon", "Medidor_neon", "Sensor_neon", "Interior_neon", "Antena_neon",
]

# Puertas correderas
PUERTA_U = (-3.0, 0.6)  # hueco
HOJA_D = (-0.32, -0.18)  # plano de las hojas (profundidad desde la cara exterior)
HOJA_IZQ = (-3.05, -1.2)
HOJA_DER = (-1.2, 0.65)
RECORRIDO = 1.8  # lo que se desliza cada hoja al abrir
RECESO_U = (-4.7, 2.55)  # hueco del mecanismo sobre la puerta
RECESO_Z = (5.8, 6.45)
RECESO_D = -0.28

# Puerta trasera
TRASERA_X = (0.6, 3.4)
TRASERA_ALTO = 5.6
BISAGRA = V((3.5, Y_EXT + 0.2, 0.0))


class Pared:
    """Sistema local de una pared: u a lo largo, z arriba, d hacia fuera desde la cara exterior (d < 0: dentro)."""

    def __init__(self, nombre, origen, eje_u, normal, rango_u):
        self.nombre = nombre
        self.o, self.eu, self.n = V(origen), V(eje_u), V(normal)
        self.rango = rango_u

    def p(self, u, z, d=0.0):
        return self.o + self.eu * u + V((0, 0, z)) + self.n * d

    def caja(self, g, u0, u1, z0, z1, d0, d1, mat, **kw):
        a, b = self.p(u0, z0, d0), self.p(u1, z1, d1)
        caja(g, [min(a[i], b[i]) for i in range(3)], [max(a[i], b[i]) for i in range(3)], mat, **kw)


PAREDES = {
    "frente": Pared("frente", (0, -Y_EXT, 0), (1, 0, 0), (0, -1, 0), (-4.7, 4.7)),
    "fondo": Pared("fondo", (0, Y_EXT, 0), (-1, 0, 0), (0, 1, 0), (-4.7, 4.7)),
    "izq": Pared("izq", (-X_EXT, 0, 0), (0, -1, 0), (-1, 0, 0), (-4.5, 4.5)),
    "der": Pared("der", (X_EXT, 0, 0), (0, 1, 0), (1, 0, 0), (-4.5, 4.5)),
}

# Huecos de cada pared (u0, u1, z0, z1)
HUECOS = {
    "frente": [(PUERTA_U[0], PUERTA_U[1], SUELO, RECESO_Z[0]), (RECESO_U[0], RECESO_U[1], RECESO_Z[0], RECESO_Z[1]),
               (2.7, 4.5, 2.0, 4.6)],
    "fondo": [(-TRASERA_X[1], -TRASERA_X[0], SUELO, TRASERA_ALTO)],
    "izq": [(-0.8, 2.2, 1.9, 4.7)],  # ventana de la sala de espera (y de -2,2 a 0,8)
    "der": [(-3.2, -1.8, 3.0, 4.4)],  # ventana de la consulta
}

JUNTAS_V = {"frente": [-4.0, 1.8], "fondo": [-2.6, 1.0, 2.9], "izq": [-3.35, -2.6, 3.4], "der": [-0.4, 1.6, 3.05]}
JUNTA_H = 3.9


def _restar(intervalos, a, b):
    out = []
    for x0, x1 in intervalos:
        if b <= x0 or a >= x1:
            out.append((x0, x1))
            continue
        if a > x0:
            out.append((x0, a))
        if b < x1:
            out.append((b, x1))
    return [(x0, x1) for x0, x1 in out if x1 - x0 > 1e-4]


def construir():
    g = {n: geo.Grupo(n) for n in GRUPOS}
    datos = {}
    estructura(g)
    puertas_correderas(g, datos)
    puerta_trasera(g, datos)
    ventanas(g)
    detalles_fachada(g, datos)
    techo(g, datos)
    entorno(g, datos)
    interior(g, datos)
    return g, datos


# ================================================================================================================
# ESTRUCTURA: zócalo, paredes de paneles, perfiles de esquina, juntas de silicona, forjado, remate
# ================================================================================================================


def estructura(g):
    E = g["Edificio"]

    # Zócalo de hormigón pintado de blanco, con las esquinas redondeadas como las paredes.
    perfil = geo.rect_redondeado(2 * (X_EXT + 0.1), 2 * (Y_EXT + 0.1), 0.6, segs=5)
    prisma(E, perfil, (0, 0, 0), (1, 0, 0), (0, 1, 0), 0.0, SUELO - 0.04, "zocalo")
    # canto superior achaflanado (un escalón de 4 cm un poco más metido)
    perfil2 = geo.rect_redondeado(2 * (X_EXT + 0.06), 2 * (Y_EXT + 0.06), 0.56, segs=5)
    prisma(E, perfil2, (0, 0, 0), (1, 0, 0), (0, 1, 0), SUELO - 0.04, SUELO, "zocalo")

    # Paredes: cajas entre huecos; abajo la cara interior pintada, arriba (pretil) todo panel.
    for nombre, par in PAREDES.items():
        huecos = HUECOS[nombre]
        cortes = sorted({par.rango[0], par.rango[1]} | {h[i] for h in huecos for i in (0, 1)
                                                        if par.rango[0] < h[i] < par.rango[1]})
        for a, b in zip(cortes, cortes[1:]):
            m = (a + b) / 2
            for z0, z1 in ((SUELO, TECHO), (TECHO, PRETIL)):
                tramos = [(z0, z1)]
                for h in huecos:
                    if h[0] < m < h[1]:
                        tramos = _restar(tramos, h[2], h[3])
                for t0, t1 in tramos:
                    interior_ok = t0 < TECHO - 0.01
                    nn = -par.n

                    def mc(c, n, nn=nn, interior_ok=interior_ok):
                        return "interior" if (interior_ok and n.dot(nn) > 0.9) else "panel"

                    par.caja(E, a, b, t0, t1, -GROSOR, 0.0, "panel", mat_cara=mc)

        # Juntas de silicona entre paneles (verticales, una horizontal y la del arranque sobre el zócalo).
        def libre_v(u):
            tr = [(SUELO + 0.05, PRETIL)]
            for h in huecos:
                if h[0] - 0.16 < u < h[1] + 0.16:
                    tr = _restar(tr, h[2] - 0.16, h[3] + 0.16)
            return tr

        def libre_h(z):
            tr = [(par.rango[0] + 0.03, par.rango[1] - 0.03)]
            for h in huecos:
                if h[2] - 0.16 < z < h[3] + 0.16:
                    tr = _restar(tr, h[0] - 0.16, h[1] + 0.16)
            return tr

        for u in JUNTAS_V[nombre]:
            for z0, z1 in libre_v(u):
                par.caja(E, u - 0.025, u + 0.025, z0, z1, -0.01, 0.018, "silicona")
        for u in (par.rango[0] + 0.02, par.rango[1] - 0.02):  # encuentro con el perfil de esquina
            par.caja(E, u - 0.025, u + 0.025, SUELO + 0.05, PRETIL, -0.01, 0.018, "silicona")
        for z, conjunto in ((JUNTA_H, libre_h(JUNTA_H)), (SUELO + 0.03, libre_h(SUELO + 0.03))):
            for u0, u1 in conjunto:
                par.caja(E, u0, u1, z - 0.025, z + 0.025, -0.01, 0.018, "silicona")

    # Perfiles de esquina: cuarto de cilindro de aluminio, un pelo más grueso que la pared, con tornillos.
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (X_EXT - GROSOR), sy * (Y_EXT - GROSOR)
            a0 = {(1, 1): 0, (-1, 1): 90, (-1, -1): 180, (1, -1): 270}[(sx, sy)]
            perfil = geo.sector_anillo(0.0, GROSOR + 0.03, a0 - 3, a0 + 93, 8)
            prisma(E, perfil, (cx, cy, 0), (1, 0, 0), (0, 1, 0), SUELO, PRETIL, "perfil", suave=True)
            nd = V((sx, sy, 0)).normalized()
            for z in (1.4, 4.0, 6.6):
                tornillo(E, V((cx, cy, z)) + nd * (GROSOR + 0.03), nd, r=0.04, alto=0.02)

    # Remate (albardilla) de aluminio sobre el pretil.
    for nombre, par in PAREDES.items():
        par.caja(E, par.rango[0], par.rango[1], PRETIL, PRETIL + 0.07, -GROSOR - 0.05, 0.05, "perfil")
    for sx in (-1, 1):
        for sy in (-1, 1):
            cx, cy = sx * (X_EXT - GROSOR), sy * (Y_EXT - GROSOR)
            a0 = {(1, 1): 0, (-1, 1): 90, (-1, -1): 180, (1, -1): 270}[(sx, sy)]
            prisma(E, geo.sector_anillo(0.0, GROSOR + 0.05, a0, a0 + 90, 6), (cx, cy, 0), (1, 0, 0), (0, 1, 0),
                   PRETIL, PRETIL + 0.07, "perfil")

    # Forjado: arriba la tela asfáltica del techo, abajo el techo interior.
    caja(E, (-X_EXT + GROSOR, -Y_EXT + GROSOR, CORTE_INT), (X_EXT - GROSOR, Y_EXT - GROSOR, TECHO), "membrana",
         mat_cara=lambda c, n: "membrana" if n.z > 0.5 else "techo_int")
    # sumidero del techo
    cilindro(E, (3.9, 3.7, TECHO - 0.01), (3.9, 3.7, TECHO + 0.03), 0.18, 8, "rejilla")


# ================================================================================================================
# PUERTAS CORREDERAS (hojas separadas, se esconden en la pared) y su mecanismo visible
# ================================================================================================================


def puertas_correderas(g, datos):
    E = g["Edificio"]
    F = PAREDES["frente"]
    d0, d1 = HOJA_D

    for lado, (u0, u1) in (("Izq", HOJA_IZQ), ("Der", HOJA_DER)):
        H = g[f"Puerta_{lado}"]
        C = g[f"Puerta_{lado}_Cristal"]
        z0, z1 = SUELO + 0.02, RECESO_Z[0]
        jamba = u0 if lado == "Izq" else u1  # lado que entra en la pared
        enc = u1 if lado == "Izq" else u0  # lado del encuentro central
        sj = -1 if lado == "Izq" else 1
        # bastidor (perfiles blancos)
        ancho_j, ancho_e = 0.16, 0.12
        uj0, uj1 = sorted((jamba, jamba - sj * ancho_j))
        ue0, ue1 = sorted((enc, enc + sj * ancho_e))
        F.caja(H, uj0, uj1, z0, z1, d0, d1, "puerta")
        F.caja(H, ue0, ue1, z0, z1, d0, d1, "puerta")
        ui0, ui1 = (uj1, ue0) if lado == "Izq" else (ue1, uj0)
        F.caja(H, ui0, ui1, z1 - 0.2, z1, d0, d1, "puerta")
        F.caja(H, ui0, ui1, z0, z0 + 0.56, d0, d1, "puerta")
        # chapas de protección abajo, por fuera y por dentro (marcas de camillas)
        for da, db in ((d1, d1 + 0.012), (d0 - 0.012, d0)):
            F.caja(H, u0 + 0.02, u1 - 0.02, z0 + 0.03, z0 + 0.53, da, db, "zocalo_inox")
        # goma del encuentro central
        ug0, ug1 = sorted((enc, enc - sj * 0.03))
        F.caja(H, ug0, ug1, z0 + 0.02, z1 - 0.02, d0 + 0.03, d1 - 0.03, "caucho")
        # cristal con franja esmerilada (material) y cruz en relieve a los dos lados
        F.caja(C, ui0 - 0.03, ui1 + 0.03, z0 + 0.53, z1 - 0.17, -0.27, -0.23, "cristal_puerta")
        uc = (ui0 + ui1) / 2
        for dd, eu in ((-0.23, (1, 0, 0)), (-0.27, (-1, 0, 0))):
            o = F.p(uc, 4.75, dd)
            prisma(C, geo.perfil_cruz(0.72, 0.24), o, eu, (0, 0, 1), 0.0, 0.014, "esmerilado")
        # junquillos que sujetan el cristal
        for da, db in ((d1, d1 + 0.02), (d0 - 0.02, d0)):
            F.caja(H, ui0, ui1, z1 - 0.23, z1 - 0.2, da, db, "puerta")
            F.caja(H, ui0, ui1, z0 + 0.56, z0 + 0.59, da, db, "puerta")
        # carro: pieza sobre la hoja, placa colgante, ruedas que apoyan en el raíl, pinza a la correa
        uc = (u0 + u1) / 2
        F.caja(H, uc - 0.62, uc + 0.62, z1, z1 + 0.06, d0 + 0.02, -0.10, "oscuro")
        F.caja(H, uc - 0.6, uc + 0.6, z1 + 0.06, 6.3, -0.16, -0.10, "gris")
        for du in (-0.42, 0.42):
            cilindro(H, F.p(uc + du, 6.21, -0.16), F.p(uc + du, 6.21, -0.26), 0.075, 8, "caucho", giro=0.2)
            cilindro(H, F.p(uc + du, 6.21, -0.155), F.p(uc + du, 6.21, -0.27), 0.025, 6, "acero")
            tornillo(H, F.p(uc + du, 6.0, -0.10), F.n, r=0.035, alto=0.015)
        zc = 6.22 if lado == "Izq" else 6.40
        F.caja(H, uc - 0.08, uc + 0.08, zc - 0.035, zc + 0.035, -0.10, -0.055, "oscuro")
        # pivote: centro de la hoja, a ras de suelo, en su plano
        datos[f"Puerta_{lado}"] = {
            "pivote": F.p(uc, SUELO, (d0 + d1) / 2),
            "abrir": F.eu * (sj * RECORRIDO),
        }

    # Umbral de aluminio con la guía del suelo
    F.caja(E, PUERTA_U[0], PUERTA_U[1], SUELO - 0.02, SUELO + 0.025, -0.48, 0.06, "perfil")
    F.caja(E, PUERTA_U[0] - 0.05, PUERTA_U[1] + 0.05, SUELO + 0.025, SUELO + 0.035, -0.27, -0.23, "caucho")
    # Jambas: tapajuntas exteriores y cepillos de las ranuras de los bolsillos
    for u in PUERTA_U:
        s = -1 if u == PUERTA_U[0] else 1
        a, b = sorted((u, u + s * 0.12))
        F.caja(E, a, b, SUELO, RECESO_Z[0], -0.02, 0.035, "marco")
        a, b = sorted((u, u - s * 0.03))
        for da, db in ((HOJA_D[1], HOJA_D[1] + 0.04), (HOJA_D[0] - 0.04, HOJA_D[0])):
            F.caja(E, a, b, SUELO + 0.05, RECESO_Z[0] - 0.02, da, db, "caucho")

    # Receso del mecanismo: fondo (la parte interior de la pared), raíl, poleas, correa, motor, tapa.
    u0, u1 = RECESO_U
    F.caja(E, u0, u1, RECESO_Z[0], RECESO_Z[1], -GROSOR, RECESO_D, "oscuro",
           mat_cara=lambda c, n: "interior" if n.dot(-F.n) > 0.9 else "oscuro")
    F.caja(E, u0 + 0.02, u1 - 0.02, 6.0, 6.14, RECESO_D, -0.18, "perfil")  # raíl
    F.caja(E, u0 + 0.02, u1 - 0.02, 6.07, 6.09, -0.18, -0.175, "acero")  # banda de rodadura
    for u in (u0 + 0.3, -1.2, u1 - 0.3):
        tornillo(E, F.p(u, 6.04, -0.18), F.n, r=0.03, alto=0.015)
    for u in (u0 + 0.2, u1 - 0.2):  # poleas de la correa
        cilindro(E, F.p(u, 6.31, -0.10), F.p(u, 6.31, -0.04), 0.1, 8, "gris")
        cilindro(E, F.p(u, 6.31, -0.11), F.p(u, 6.31, -0.03), 0.03, 6, "acero")
        F.caja(E, u - 0.04, u + 0.04, 6.14, 6.31, -0.12, -0.10, "gris")
    F.caja(E, u0 + 0.2, u1 - 0.2, 6.39, 6.41, -0.085, -0.055, "caucho")  # correa (ramal de arriba)
    F.caja(E, u0 + 0.2, u1 - 0.2, 6.21, 6.23, -0.085, -0.055, "caucho")  # correa (ramal de abajo)
    # motorreductor: caja, motor cilíndrico y bornera
    F.caja(E, -2.25, -1.55, 6.26, 6.44, -0.10, -0.01, "oscuro", bisel=0.015)
    cilindro(E, F.p(-1.55, 6.35, -0.055), F.p(-1.05, 6.35, -0.055), 0.075, 10, "gris")
    cilindro(E, F.p(-1.05, 6.35, -0.055), F.p(-1.0, 6.35, -0.055), 0.06, 10, "oscuro")
    F.caja(E, -2.1, -1.8, 6.44, 6.45, -0.09, -0.03, "gris")
    # tapa transparente del mecanismo, con perfiles arriba y abajo
    F.caja(g["Cristales"], u0 + 0.01, u1 - 0.01, RECESO_Z[0] + 0.03, RECESO_Z[1] - 0.03, 0.0, 0.02, "cristal")
    F.caja(E, u0, u1, RECESO_Z[1] - 0.03, RECESO_Z[1] + 0.07, -0.02, 0.05, "perfil")
    F.caja(E, u0, u1, RECESO_Z[0] - 0.02, RECESO_Z[0] + 0.03, -0.02, 0.05, "perfil")
    for u in (u0 + 0.12, -3.0, -1.2, 0.6, u1 - 0.12):
        tornillo(E, F.p(u, RECESO_Z[1] + 0.02, 0.05), F.n, r=0.03, alto=0.015)

    # Sensor de movimiento sobre la puerta: caja con lente oscura y LED (neón)
    uc = (PUERTA_U[0] + PUERTA_U[1]) / 2
    F.caja(E, uc - 0.26, uc + 0.26, 6.53, 6.73, 0.05, 0.27, "marco", bisel=0.02)
    F.caja(E, uc - 0.18, uc + 0.12, 6.51, 6.53, 0.08, 0.24, "negro_mate")
    cilindro(g["Sensor_neon"], F.p(uc + 0.18, 6.63, 0.265), F.p(uc + 0.18, 6.63, 0.29), 0.028, 8, "neon_rojo")
    datos["Sensor_LED"] = F.p(uc + 0.18, 6.63, 0.29)

    # Marquesina de 1 stud con dos luces empotradas y tirantes
    caja(E, (-3.7, -Y_EXT - 1.0, 6.78), (1.3, -Y_EXT, 6.98), "marco", bisel=0.025)
    caja(E, (-3.72, -Y_EXT - 1.03, 6.75), (1.32, -Y_EXT - 0.97, 7.0), "perfil")  # frente goterón
    for x in (-3.72, 1.27):
        caja(E, (x, -Y_EXT - 1.03, 6.75), (x + 0.05, -Y_EXT, 7.0), "perfil")
    caja(E, (-3.7, -Y_EXT, 6.75), (1.3, -Y_EXT + 0.02, 7.02), "perfil")  # pletina a la pared
    for x in (-3.4, -1.2, 1.0):
        tornillo(E, (x, -Y_EXT - 0.02, 6.98), (0, -1, 0), r=0.03, alto=0.015)
    luces = []
    for x in (-2.45, 0.05):
        cilindro(E, (x, -Y_EXT - 0.55, 6.765), (x, -Y_EXT - 0.55, 6.79), 0.21, 12, "perfil")
        cilindro(g["Marquesina_neon"], (x, -Y_EXT - 0.55, 6.755), (x, -Y_EXT - 0.55, 6.775), 0.15, 12,
                 "neon_calido")
        luces.append(V((x, -Y_EXT - 0.55, 6.75)))
    datos["LucesMarquesina"] = luces
    for x in (-3.45, 1.05):
        cilindro(E, (x, -Y_EXT - 0.92, 6.99), (x, -Y_EXT - 0.02, 7.3), 0.025, 6, "acero")
        caja(E, (x - 0.06, -Y_EXT - 0.92, 6.98), (x + 0.06, -Y_EXT - 0.84, 7.02), "acero")
        caja(E, (x - 0.08, -Y_EXT - 0.03, 7.2), (x + 0.08, -Y_EXT, 7.34), "acero")


# ================================================================================================================
# PUERTA TRASERA (suministros): hoja metálica con bisagras, cerradura de teclado y cartel
# ================================================================================================================


def puerta_trasera(g, datos):
    E = g["Edificio"]
    T = g["Puerta_Trasera"]
    B = PAREDES["fondo"]
    x0, x1 = TRASERA_X
    y = Y_EXT
    # cerco fijo
    for xa, xb in ((x0 - 0.12, x0), (x1, x1 + 0.12)):
        caja(E, (xa, y - 0.02, SUELO), (xb, y + 0.05, TRASERA_ALTO + 0.12), "marco")
    caja(E, (x0 - 0.12, y - 0.02, TRASERA_ALTO), (x1 + 0.12, y + 0.05, TRASERA_ALTO + 0.12), "marco")
    caja(E, (x0, y - 0.48, SUELO - 0.01), (x1, y + 0.02, SUELO + 0.02), "perfil")  # umbral
    # hoja
    hx0, hx1 = x0 - 0.05, x1 + 0.05
    yh0, yh1 = y + 0.05, y + 0.19
    caja(T, (hx0, yh0, SUELO + 0.03), (hx1, yh1, TRASERA_ALTO + 0.05), "puerta", bisel=0.015)
    # nervios de refuerzo marcados en la chapa (dos rectángulos en relieve)
    for z0, z1 in ((1.0, 2.6), (3.2, 5.2)):
        for xa, xb, za, zb in ((hx0 + 0.3, hx1 - 0.3, z0, z0 + 0.05), (hx0 + 0.3, hx1 - 0.3, z1 - 0.05, z1),
                               (hx0 + 0.3, hx0 + 0.35, z0, z1), (hx1 - 0.35, hx1 - 0.3, z0, z1)):
            caja(T, (xa, yh1, za), (xb, yh1 + 0.012, zb), "puerta")
    caja(T, (hx0 + 0.05, yh1, SUELO + 0.06), (hx1 - 0.05, yh1 + 0.012, SUELO + 0.6), "zocalo_inox")
    # bisagras: hoja en la puerta y canuto (el eje de giro), y la contra en el cerco
    for z in (1.2, 3.0, 4.9):
        cilindro(T, (BISAGRA.x, BISAGRA.y, z - 0.2), (BISAGRA.x, BISAGRA.y, z + 0.2), 0.05, 8, "acero")
        cilindro(T, (BISAGRA.x, BISAGRA.y, z + 0.2), (BISAGRA.x, BISAGRA.y, z + 0.23), 0.03, 6, "acero")
        caja(T, (hx1 - 0.3, yh1, z - 0.18), (BISAGRA.x, yh1 + 0.012, z + 0.18), "acero")
        for dz in (-0.1, 0.1):
            tornillo(T, (hx1 - 0.18, yh1 + 0.012, z + dz), (0, 1, 0), r=0.025, alto=0.01)
        caja(E, (x1 + 0.05, y + 0.05, z - 0.18), (BISAGRA.x + 0.08, y + 0.062, z + 0.18), "acero")
    # manilla con roseta
    xm = hx0 + 0.3
    cilindro(T, (xm, yh1, 2.6), (xm, yh1 + 0.04, 2.6), 0.09, 10, "acero")
    cilindro(T, (xm, yh1 + 0.04, 2.6), (xm, yh1 + 0.17, 2.6), 0.035, 8, "acero")
    tubo(T, [V((xm, yh1 + 0.15, 2.6)), V((xm + 0.42, yh1 + 0.15, 2.6)), V((xm + 0.44, yh1 + 0.12, 2.58))], 0.035,
         6, "acero", radio_codo=0.03, pasos_codo=1)
    cilindro(T, (xm, yh1, 2.35), (xm, yh1 + 0.03, 2.35), 0.05, 8, "acero")  # bombín
    # cerradura con teclado numérico: caja, 12 teclas, LED y pantallita
    kx, kz = xm + 0.05, 3.55
    caja(T, (kx - 0.17, yh1, kz - 0.28), (kx + 0.17, yh1 + 0.07, kz + 0.28), "oscuro", bisel=0.015)
    caja(T, (kx - 0.12, yh1 + 0.07, kz + 0.13), (kx + 0.12, yh1 + 0.075, kz + 0.23), "negro_mate")
    cilindro(T, (kx + 0.11, yh1 + 0.07, kz + 0.06), (kx + 0.11, yh1 + 0.085, kz + 0.06), 0.015, 6, "neon_rojo")
    dw, dh = 0.26, 0.36
    zc_tec = kz - 0.1
    deco = (V((kx, yh1 + 0.08, zc_tec)), V((-1, 0, 0)), V((0, 0, 1)), dw, dh)
    teclas = []
    for i in range(12):
        fx, fy = i % 3, i // 3
        # misma rejilla que la imagen del teclado (rotulos.py), con la U invertida porque la cara mira a +Y
        u = (0.5 + (fx - 1) * 0.3 - 0.5) * dw
        v = (0.5 - (0.58 + (fy - 1.5) * 0.19)) * dh
        cx = kx - u
        cz = zc_tec + v
        caja(T, (cx - 0.032, yh1 + 0.07, cz - 0.026), (cx + 0.032, yh1 + 0.095, cz + 0.026), "acero",
             mat_cara=lambda c, n: "teclado" if n.y > 0.9 else "acero", deco=deco)
        teclas.append((cx, cz))
    # cartel SOLO PERSONAL con remaches
    cx, cz = (hx0 + hx1) / 2 + 0.25, 4.45
    geo.placa_con_tornillos(T, (cx, yh1 + 0.012, cz), (-1, 0, 0), (0, 0, 1), 1.4, 0.5, 0.02, "blanco_puro",
                            mat_frente="rot_solo_personal",
                            deco=(V((cx, yh1, cz)), V((-1, 0, 0)), V((0, 0, 1)), 1.4, 0.5), r_torn=0.025,
                            margen=0.06)
    # escalón de hormigón exterior
    caja(g["Rampa"], (x0 - 0.4, y + 0.1, 0.0), (x1 + 0.4, y + 1.4, SUELO), "zocalo", bisel=0.03)
    caja(g["Rampa"], (x0 - 0.3, y + 1.2, SUELO - 0.005), (x1 + 0.3, y + 1.35, SUELO + 0.003), "amarillo")
    datos["Puerta_Trasera"] = {"pivote": V((BISAGRA.x, BISAGRA.y, SUELO)), "angulo_abrir_blender_z": -95.0}


# ================================================================================================================
# VENTANAS
# ================================================================================================================


def _ventana(g, par, u0, u1, z0, z1, mat_cristal, vuelo_alfeizar=0.22, montante=False):
    E = g["Edificio"]
    fw = 0.12
    da, db = -0.32, -0.06
    par.caja(E, u0, u0 + fw, z0, z1, da, db, "marco")
    par.caja(E, u1 - fw, u1, z0, z1, da, db, "marco")
    par.caja(E, u0 + fw, u1 - fw, z1 - fw, z1, da, db, "marco")
    par.caja(E, u0 + fw, u1 - fw, z0, z0 + fw, da, db, "marco")
    if montante:
        um = (u0 + u1) / 2
        par.caja(E, um - 0.05, um + 0.05, z0 + fw, z1 - fw, da, db + 0.01, "marco")
    # cristal en la ranura del marco
    par.caja(g["Cristales"], u0 + fw - 0.03, u1 - fw + 0.03, z0 + fw - 0.03, z1 - fw + 0.03, -0.21, -0.17,
             mat_cristal)
    # junquillos por fuera
    for a, b, c, d in ((u0 + fw, u1 - fw, z0 + fw, z0 + fw + 0.03), (u0 + fw, u1 - fw, z1 - fw - 0.03, z1 - fw),
                       (u0 + fw, u0 + fw + 0.03, z0 + fw, z1 - fw), (u1 - fw - 0.03, u1 - fw, z0 + fw, z1 - fw)):
        par.caja(E, a, b, c, d, -0.17, -0.14, "marco")
    # cordón de silicona entre marco y mocheta
    for a, b, c, d in ((u0, u0 + 0.035, z0, z1), (u1 - 0.035, u1, z0, z1), (u0, u1, z1 - 0.035, z1)):
        par.caja(E, a, b, c, d, -0.06, -0.035, "silicona")
    # alféizar de aluminio con goterón
    par.caja(E, u0 - 0.14, u1 + 0.14, z0 - 0.09, z0, -0.32, vuelo_alfeizar, "perfil", bisel=0.012)
    par.caja(E, u0 - 0.14, u1 + 0.14, z0 - 0.14, z0 - 0.09, vuelo_alfeizar - 0.03, vuelo_alfeizar, "perfil")


def ventanas(g):
    # Frontal (junto a la puerta): esmerilado parcial
    _ventana(g, PAREDES["frente"], 2.7, 4.5, 2.0, 4.6, "cristal_frontal")
    # Lateral 1 (sala de espera): transparente, con montante y alféizar ancho para la planta
    _ventana(g, PAREDES["izq"], -0.8, 2.2, 1.9, 4.7, "cristal", vuelo_alfeizar=0.5, montante=True)
    # Lateral 2 (consulta): esmerilada entera, más pequeña y más alta
    _ventana(g, PAREDES["der"], -3.2, -1.8, 3.0, 4.4, "esmerilado")

    # Planta medicinal (aloe vera) en maceta de cerámica sobre el alféizar de la sala de espera.
    P = PAREDES["izq"]
    E = g["Edificio"]
    base = P.p(1.55, 1.9, 0.26)
    cilindro(E, base, base + V((0, 0, 0.36)), 0.15, 10, "ceramica", r2=0.2)
    cilindro(E, base + V((0, 0, 0.36)), base + V((0, 0, 0.4)), 0.21, 10, "ceramica")  # borde
    cilindro(E, base + V((0, 0, 0.3)), base + V((0, 0, 0.37)), 0.185, 10, "tierra")
    _aloe(E, base + V((0, 0, 0.35)))
    # plato bajo la maceta
    cilindro(E, base - V((0, 0, 0.0)), base + V((0, 0, 0.035)), 0.19, 10, "ceramica")


def _aloe(g, c):
    """Aloe vera: hojas gruesas en roseta, cada una un prisma rómbico que se afila y se curva hacia fuera."""
    import random

    rnd = random.Random(7)
    n = 9
    for i in range(n):
        ang = 2 * math.pi * i / n + rnd.uniform(-0.15, 0.15)
        inclin = math.radians(18 + 32 * (i % 3) / 2 + rnd.uniform(-5, 5))
        largo = 0.55 + rnd.uniform(-0.08, 0.12) - 0.08 * (i % 3)
        anch, grue = 0.085, 0.045
        dir_h = V((math.cos(ang), math.sin(ang), 0))
        lat = V((-math.sin(ang), math.cos(ang), 0))
        bm = geo.bmesh.new()
        anillos = []
        est = 4
        for k in range(est):
            t = k / est
            # la hoja se abre más cuanto más arriba (curva)
            a = inclin + t * t * 0.6
            eje = dir_h * math.sin(a) + V((0, 0, 1)) * math.cos(a)
            p = c + dir_h * 0.03 + _integrar(dir_h, inclin, t, largo)
            w = anch * (1 - 0.75 * t)
            h = grue * (1 - 0.6 * t)
            fuera = eje.cross(lat).normalized()
            pts = [p + lat * w, p + fuera * h, p - lat * w, p - fuera * h * 0.6]
            anillos.append([bm.verts.new(q) for q in pts])
        punta = bm.verts.new(c + dir_h * 0.03 + _integrar(dir_h, inclin, 1.0, largo))
        for k in range(est - 1):
            a1, a2 = anillos[k], anillos[k + 1]
            for j in range(4):
                jj = (j + 1) % 4
                bm.faces.new((a1[j], a1[jj], a2[jj], a2[j]))
        for j in range(4):
            bm.faces.new((anillos[-1][j], anillos[-1][(j + 1) % 4], punta))
        bm.faces.new(list(reversed(anillos[0])))
        g.fusionar(bm, "hoja", suave=True)


def _integrar(dir_h, inclin, t, largo, pasos=8):
    p = V((0, 0, 0))
    for k in range(pasos):
        s = t * (k + 0.5) / pasos
        a = inclin + s * s * 0.6
        p += (dir_h * math.sin(a) + V((0, 0, 1)) * math.cos(a)) * (largo * t / pasos)
    return p


# ================================================================================================================
# DETALLES DE FACHADA
# ================================================================================================================


def detalles_fachada(g, datos):
    D = g["Detalles"]
    F = PAREDES["frente"]

    # --- Cruz médica luminosa (1 x 1) con carcasa metálica y brazo de montaje ------------------------------------
    uc, zc = 3.6, 5.78
    # placa de anclaje a la pared con 4 tornillos
    geo.placa_con_tornillos(D, F.p(uc, zc), F.eu, (0, 0, 1), 0.34, 0.5, 0.03, "perfil", margen=0.07, r_torn=0.03)
    # brazo: tubo cuadrado + cartabón
    F.caja(D, uc - 0.05, uc + 0.05, zc - 0.05, zc + 0.05, 0.03, 0.42, "perfil")
    F.caja(D, uc - 0.012, uc + 0.012, zc - 0.24, zc - 0.05, 0.03, 0.2, "perfil")  # cartabón
    # conducto del cable
    tubo(D, [F.p(uc + 0.12, zc - 0.25, 0.03), F.p(uc + 0.12, zc - 0.05, 0.03), F.p(uc + 0.12, zc - 0.05, 0.35)],
         0.022, 6, "gris", radio_codo=0.05, pasos_codo=2)
    # carcasa de la cruz (metal) y el neón delante, con el borde metálico visible alrededor
    o = F.p(uc, zc)
    prisma(D, geo.perfil_cruz(1.12, 0.44), o, F.eu, (0, 0, 1), 0.42, 0.66, "perfil")
    prisma(g["Cruz_neon"], geo.perfil_cruz(1.0, 0.33), o, F.eu, (0, 0, 1), 0.5, 0.69, "neon_blanco")
    datos["Cruz"] = F.p(uc, zc, 0.69)

    # --- Placa «CLÍNICA COLONIAL — Dra. Voss» grabada --------------------------------------------------------------
    u, z = -3.97, 4.9
    geo.placa_con_tornillos(D, F.p(u, z), F.eu, (0, 0, 1), 1.24, 0.57, 0.05, "perfil", mat_frente="placa",
                            deco=(F.p(u, z), F.eu, V((0, 0, 1)), 1.24, 0.57), margen=0.055, r_torn=0.022,
                            bisel=0.03)

    # --- Tablón informativo con cristal y el papel del HORARIO ---------------------------------------------------
    u, z = -3.97, 2.85
    w, h = 1.2, 1.4
    F.caja(D, u - w / 2, u + w / 2, z - h / 2, z + h / 2, 0.0, 0.03, "blanco_puro")
    for a, b, c, d in ((u - w / 2, u + w / 2, z + h / 2 - 0.07, z + h / 2), (u - w / 2, u + w / 2, z - h / 2,
                                                                          z - h / 2 + 0.07),
                       (u - w / 2, u - w / 2 + 0.07, z - h / 2 + 0.07, z + h / 2 - 0.07),
                       (u + w / 2 - 0.07, u + w / 2, z - h / 2 + 0.07, z + h / 2 - 0.07)):
        F.caja(D, a, b, c, d, 0.03, 0.12, "perfil", bisel=0.01)
    F.caja(D, u - 0.45, u + 0.45, z - 0.54, z + 0.54, 0.03, 0.036, "rot_horario",
           deco=(F.p(u, z), F.eu, V((0, 0, 1)), 0.9, 1.08),
           mat_cara=lambda c, n: "rot_horario" if n.dot(F.n) > 0.9 else "blanco_puro")
    F.caja(g["Cristales"], u - w / 2 + 0.06, u + w / 2 - 0.06, z - h / 2 + 0.06, z + h / 2 - 0.06, 0.085, 0.1,
           "cristal")
    for su in (-1, 1):
        for sz in (-1, 1):
            tornillo(D, F.p(u + su * (w / 2 - 0.035), z + sz * (h / 2 - 0.035), 0.12), F.n, r=0.022, alto=0.012)
    # cerradura del tablón
    cilindro(D, F.p(u + w / 2 - 0.035, z, 0.12), F.p(u + w / 2 - 0.035, z, 0.145), 0.025, 6, "acero")

    # --- Dispensador de gel junto a la puerta ---------------------------------------------------------------------
    u, z = 1.3, 3.45
    F.caja(D, u - 0.14, u + 0.14, z - 0.36, z + 0.32, 0.0, 0.02, "perfil")  # pletina
    for zz in (z - 0.3, z + 0.26):
        tornillo(D, F.p(u, zz, 0.02), F.n, r=0.022, alto=0.012)
    F.caja(D, u - 0.18, u + 0.18, z - 0.2, z + 0.3, 0.02, 0.22, "marco", bisel=0.025)
    F.caja(D, u - 0.14, u + 0.14, z + 0.06, z + 0.22, 0.22, 0.226, "rot_gel",
           deco=(F.p(u, z + 0.14), F.eu, V((0, 0, 1)), 0.28, 0.14),
           mat_cara=lambda c, n: "rot_gel" if n.dot(F.n) > 0.9 else "blanco_puro")
    F.caja(D, u - 0.06, u + 0.06, z - 0.08, z + 0.02, 0.22, 0.225, "cristal")  # ventanita del nivel
    F.caja(D, u - 0.13, u + 0.13, z - 0.2, z - 0.06, 0.2, 0.27, "gris", bisel=0.015)  # pulsador
    cilindro(D, F.p(u, z - 0.2, 0.15), F.p(u, z - 0.25, 0.15), 0.02, 6, "oscuro")  # boquilla
    F.caja(D, u - 0.15, u + 0.15, z - 0.58, z - 0.55, 0.02, 0.22, "gris")  # bandeja antigoteo
    F.caja(D, u - 0.15, u + 0.15, z - 0.55, z - 0.5, 0.19, 0.22, "gris")

    # --- Botiquín rojo de emergencias en la pared lateral izquierda ------------------------------------------------
    L = PAREDES["izq"]
    u, z = 3.45, 3.2  # y = -3,45
    for zz in (z - 0.58, z + 0.52):  # pletinas de anclaje con tornillos
        L.caja(D, u - 0.3, u + 0.3, zz, zz + 0.06, 0.0, 0.025, "rojo")
        for du in (-0.22, 0.22):
            tornillo(D, L.p(u + du, zz + 0.03, 0.025), L.n, r=0.022, alto=0.012)
    L.caja(D, u - 0.45, u + 0.45, z - 0.52, z + 0.52, 0.0, 0.26, "rojo", bisel=0.02)
    L.caja(D, u - 0.42, u + 0.42, z - 0.49, z + 0.49, 0.26, 0.295, "rojo", bisel=0.012)  # puerta
    prisma(D, geo.perfil_cruz(0.44, 0.14), L.p(u, z + 0.1), L.eu, (0, 0, 1), 0.295, 0.315, "blanco_puro")
    L.caja(D, u - 0.34, u + 0.34, z - 0.36, z - 0.22, 0.295, 0.3, "botiquin_texto",
           deco=(L.p(u, z - 0.29), L.eu, V((0, 0, 1)), 0.68, 0.17))
    for zz in (z - 0.3, z + 0.3):  # bisagras
        cilindro(D, L.p(u - 0.45, zz - 0.09, 0.28), L.p(u - 0.45, zz + 0.09, 0.28), 0.025, 6, "acero")
    L.caja(D, u + 0.3, u + 0.36, z - 0.12, z + 0.12, 0.295, 0.33, "gris")  # cierre
    cilindro(D, L.p(u + 0.33, z, 0.33), L.p(u + 0.33, z, 0.36), 0.03, 8, "acero")

    # --- Medidor de energía (pared derecha) -------------------------------------------------------------------------
    R = PAREDES["der"]
    u, z = 2.85, 2.9
    R.caja(D, u - 0.4, u + 0.4, z - 0.5, z + 0.5, 0.0, 0.3, "gris", bisel=0.02)
    R.caja(D, u - 0.32, u + 0.32, z - 0.05, z + 0.32, 0.3, 0.32, "negro_mate")  # marco de la pantalla
    R.caja(g["Medidor_neon"], u - 0.25, u + 0.25, z + 0.03, z + 0.25, 0.31, 0.33, "rot_medidor",
           deco=(R.p(u, z + 0.14), R.eu, V((0, 0, 1)), 0.5, 0.22))
    R.caja(D, u - 0.3, u + 0.3, z - 0.42, z - 0.16, 0.3, 0.31, "blanco_puro")  # etiqueta
    for su in (-1, 1):
        for sz in (-1, 1):
            tornillo(D, R.p(u + su * 0.34, z + sz * 0.44, 0.3), R.n, r=0.022, alto=0.012)
    tubo(D, [R.p(u, z - 0.5, 0.15), R.p(u, 0.6, 0.15), R.p(u, 0.25, 0.32), R.p(u, -0.05, 0.32)], 0.05, 8, "gris",
         radio_codo=0.15, pasos_codo=2)
    R.caja(D, u - 0.08, u + 0.08, 1.4, 1.48, 0.0, 0.22, "gris")  # abrazadera

    # --- Tubo de ventilación con filtro HEPA (pared derecha) -----------------------------------------------------
    u = 0.6
    d = 0.42
    tubo(D, [R.p(u, 2.6, -0.05), R.p(u, 2.6, d), R.p(u, 4.1, d)], 0.14, 10, "acero", radio_codo=0.3, pasos_codo=3)
    R.caja(D, u - 0.22, u + 0.22, 2.38, 2.82, 0.0, 0.03, "perfil")  # tapajuntas del pasamuros
    # filtro HEPA: caja con bridas, tornillos y su etiqueta
    R.caja(D, u - 0.32, u + 0.32, 4.15, 5.05, d - 0.32, d + 0.32, "hvac", bisel=0.02)
    for zz in (4.1, 5.05):
        R.caja(D, u - 0.36, u + 0.36, zz, zz + 0.05, d - 0.36, d + 0.36, "perfil")
    for su in (-1, 1):
        for sz in (4.25, 4.95):
            tornillo(D, R.p(u + su * 0.24, sz, d + 0.32), R.n, r=0.025, alto=0.012)
    R.caja(D, u - 0.2, u + 0.2, 4.45, 4.75, d + 0.32, d + 0.325, "blanco_puro")
    cilindro(D, R.p(u, 4.05, d), R.p(u, 4.15, d), 0.155, 10, "perfil")
    cilindro(D, R.p(u, 5.1, d), R.p(u, 5.2, d), 0.155, 10, "perfil")
    tubo(D, [R.p(u, 5.15, d), R.p(u, 8.0, d)], 0.14, 10, "acero")
    # sombrerete
    cilindro(D, R.p(u, 8.0, d), R.p(u, 8.12, d), 0.16, 10, "acero")
    cilindro(D, R.p(u, 8.12, d), R.p(u, 8.3, d), 0.32, 10, "acero", r2=0.04)
    for k in range(3):
        a = 2 * math.pi * k / 3
        off = R.eu * math.cos(a) * 0.15 + R.n * math.sin(a) * 0.15
        cilindro(D, R.p(u, 7.98, d) + off, R.p(u, 8.17, d) + off * 1.4, 0.012, 4, "acero")
    # abrazaderas a la pared
    for zz in (3.3, 6.0, 7.2):
        cilindro(D, R.p(u, zz - 0.05, d), R.p(u, zz + 0.05, d), 0.155, 10, "gris")
        R.caja(D, u - 0.04, u + 0.04, zz - 0.05, zz + 0.05, 0.0, d - 0.14, "gris")
        R.caja(D, u - 0.12, u + 0.12, zz - 0.09, zz + 0.09, 0.0, 0.02, "gris")
        for du in (-0.08, 0.08):
            tornillo(D, R.p(u + du, zz, 0.02), R.n, r=0.018, alto=0.01)


# ================================================================================================================
# TECHO: climatizador con ventilador, panel solar, antena de emergencias
# ================================================================================================================


def techo(g, datos):
    T = g["Techo_Equipos"]
    zt = TECHO

    # --- Climatizador / filtración ----------------------------------------------------------------------------
    x0, x1, y0, y1 = -3.7, -1.1, 0.5, 3.5
    for y in (y0 + 0.4, y1 - 0.4):  # bancadas
        caja(T, (x0 - 0.2, y - 0.08, zt), (x1 + 0.2, y + 0.08, zt + 0.15), "oscuro")
        for x in (x0 - 0.1, x1 + 0.1):
            tornillo(T, (x, y, zt + 0.15), (0, 0, 1), r=0.03, alto=0.015)
    zb, za = zt + 0.15, zt + 1.05
    caja(T, (x0, y0, zb), (x1, y1, za), "hvac", bisel=0.035)
    # rejillas de lamas en las dos caras largas (-X y +X)
    for sx, xx in ((-1, x0), (1, x1)):
        caja(T, (xx - 0.01 if sx > 0 else xx - 0.04, y0 + 0.3, zb + 0.15),
             (xx + 0.04 if sx > 0 else xx + 0.01, y1 - 0.3, za - 0.2), "rejilla")
        for k in range(6):
            z = zb + 0.24 + k * 0.105
            rot = Matrix.Rotation(math.radians(35 * sx), 3, "Y")
            caja(T, (xx - 0.03, y0 + 0.32, z - 0.012), (xx + 0.03, y1 - 0.32, z + 0.012), "hvac", rot=rot,
                 pivote=(xx + sx * 0.04, (y0 + y1) / 2, z))
    # ventilador de arriba: hueco oscuro, aro, rejilla, aspas y buje
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2 + 0.15
    cilindro(T, (cx, cy, za - 0.01), (cx, cy, za + 0.005), 0.7, 16, "negro_mate")
    prisma(T, geo.sector_anillo(0.66, 0.78, 0, 359.9, 16), (cx, cy, 0), (1, 0, 0), (0, 1, 0), za, za + 0.1, "hvac")
    for k in range(3):
        a = math.radians(30 + 120 * k)
        rot = Matrix.Rotation(a, 3, "Z") @ Matrix.Rotation(math.radians(22), 3, "X")
        caja(T, (cx + 0.08, cy - 0.11, za - 0.05), (cx + 0.62, cy + 0.11, za - 0.03), "gris", rot=rot,
             pivote=(cx, cy, za - 0.04))
    cilindro(T, (cx, cy, za - 0.08), (cx, cy, za + 0.02), 0.12, 8, "oscuro")
    for k in range(4):  # rejilla de protección: 4 radios y un aro intermedio
        a = math.radians(45 + 90 * k)
        cilindro(T, (cx, cy, za + 0.09), (cx + 0.7 * math.cos(a), cy + 0.7 * math.sin(a), za + 0.09), 0.015, 4,
                 "rejilla", suave=False)
    prisma(T, geo.sector_anillo(0.36, 0.39, 0, 359.9, 12), (cx, cy, 0), (1, 0, 0), (0, 1, 0), za + 0.075, za + 0.105,
           "rejilla")
    # panel de acceso al filtro en la cara -Y con tornillos y asa
    caja(T, (x0 + 0.4, y0 - 0.02, zb + 0.15), (x1 - 0.4, y0 + 0.01, za - 0.15), "hvac")
    for x in (x0 + 0.5, x1 - 0.5):
        for z in (zb + 0.25, za - 0.25):
            tornillo(T, (x, y0 - 0.02, z), (0, -1, 0), r=0.025, alto=0.012)
    tubo(T, [V(((x0 + x1) / 2 - 0.3, y0 - 0.02, za - 0.45)), V(((x0 + x1) / 2 - 0.3, y0 - 0.12, za - 0.45)),
             V(((x0 + x1) / 2 + 0.3, y0 - 0.12, za - 0.45)), V(((x0 + x1) / 2 + 0.3, y0 - 0.02, za - 0.45))], 0.02, 6,
         "acero", radio_codo=0.04, pasos_codo=1)
    # placa de características
    caja(T, (x1 - 0.65, y0 - 0.015, zb + 0.2), (x1 - 0.45, y0, zb + 0.32), "blanco_puro")
    # conductos frigoríficos que bajan al techo
    for k, x in enumerate((x1 - 0.5, x1 - 0.32)):
        tubo(T, [V((x, y1, zb + 0.35 - k * 0.1)), V((x, y1 + 0.35, zb + 0.35 - k * 0.1)), V((x, y1 + 0.35, zt))],
             0.04, 6, "acero" if k else "negro_mate", radio_codo=0.15, pasos_codo=2)
    caja(T, (x1 - 0.65, y1 + 0.2, zt), (x1 - 0.15, y1 + 0.5, zt + 0.12), "hvac")  # pasamuros

    # --- Panel solar grande --------------------------------------------------------------------------------------
    cx, cy = 2.35, -2.05
    w, h, inc = 3.6, 2.4, math.radians(22)
    zfr = zt + 0.45
    rot = Matrix.Rotation(inc, 3, "X")
    centro = V((cx, cy, zfr + h / 2 * math.sin(inc)))
    eu, ev, en = V((1, 0, 0)), rot @ V((0, 1, 0)), rot @ V((0, 0, 1))
    caja(T, centro - V((w / 2, h / 2, 0.045)), centro + V((w / 2, h / 2, 0.045)), "perfil", rot=rot, pivote=centro,
         mat_cara=lambda c, n: "solar" if n.dot(en) > 0.9 else "perfil",
         deco=(centro, eu, ev, w - 0.1, h - 0.1))
    # marco perimetral sobresaliente
    for a0, a1 in (((-w / 2, -h / 2), (w / 2, -h / 2 + 0.06)), ((-w / 2, h / 2 - 0.06), (w / 2, h / 2)),
                   ((-w / 2, -h / 2), (-w / 2 + 0.06, h / 2)), ((w / 2 - 0.06, -h / 2), (w / 2, h / 2))):
        caja(T, centro + V((a0[0], a0[1], 0.04)), centro + V((a1[0], a1[1], 0.065)), "perfil", rot=rot, pivote=centro)
    # patas: delanteras cortas, traseras largas, riostras y pies atornillados
    for x in (cx - 1.4, cx + 1.4):
        pf = centro + rot @ V((x - cx, -h / 2 + 0.25, -0.045))
        pt = centro + rot @ V((x - cx, h / 2 - 0.25, -0.045))
        cilindro(T, (pf.x, pf.y, zt + 0.02), pf, 0.04, 6, "perfil")
        cilindro(T, (pt.x, pt.y, zt + 0.02), pt, 0.04, 6, "perfil")
        cilindro(T, (pf.x, pf.y, zt + 0.08), (pt.x, pt.y, pt.z - 0.15), 0.025, 6, "perfil")
        for p in (pf, pt):
            caja(T, (p.x - 0.12, p.y - 0.12, zt), (p.x + 0.12, p.y + 0.12, zt + 0.03), "gris")
            tornillo(T, (p.x + 0.07, p.y, zt + 0.03), (0, 0, 1), r=0.025, alto=0.012)
            tornillo(T, (p.x - 0.07, p.y, zt + 0.03), (0, 0, 1), r=0.025, alto=0.012)
    # caja de conexiones y cable al techo
    cb = centro + rot @ V((0.6, 0.4, -0.045))
    caja(T, cb - V((0.15, 0.1, 0.1)), cb + V((0.15, 0.1, 0.0)), "oscuro")
    tubo(T, [cb - V((0, 0, 0.1)), V((cb.x, cb.y, zt + 0.3)), V((cb.x + 0.6, cb.y + 0.4, zt + 0.05)),
             V((cb.x + 0.9, cb.y + 0.4, zt + 0.05))], 0.025, 6, "negro_mate", radio_codo=0.2, pasos_codo=2)

    # --- Antena de comunicaciones de emergencia --------------------------------------------------------------
    ax, ay = 3.7, 2.9
    caja(T, (ax - 0.25, ay - 0.25, zt), (ax + 0.25, ay + 0.25, zt + 0.04), "gris")
    for sx in (-1, 1):
        for sy in (-1, 1):
            tornillo(T, (ax + sx * 0.18, ay + sy * 0.18, zt + 0.04), (0, 0, 1), r=0.028, alto=0.015)
    cilindro(T, (ax, ay, zt + 0.04), (ax, ay, 9.7), 0.065, 8, "acero")
    cilindro(T, (ax, ay, zt + 0.04), (ax, ay, zt + 0.25), 0.1, 8, "gris")
    for z in (8.4, 9.3):
        cilindro(T, (ax, ay, z - 0.06), (ax, ay, z + 0.06), 0.085, 8, "gris")
    # brazo con dos dipolos
    cilindro(T, (ax, ay, 9.3), (ax - 0.75, ay, 9.3), 0.03, 6, "acero")
    for x in (ax - 0.4, ax - 0.7):
        cilindro(T, (x, ay, 9.0), (x, ay, 9.65), 0.022, 6, "poste")
    # radomo de fibra (látigo) y baliza roja arriba
    cilindro(T, (ax, ay, 9.7), (ax, ay, 10.9), 0.05, 8, "poste", r2=0.035)
    cilindro(g["Antena_neon"], (ax, ay, 10.9), (ax, ay, 11.02), 0.06, 8, "neon_rojo")
    datos["Baliza"] = V((ax, ay, 10.96))
    # vientos
    for k in range(3):
        a = math.radians(200 + 120 * k)
        pa = V((ax + 1.15 * math.cos(a), ay + 1.15 * math.sin(a), zt))
        pa.x = max(min(pa.x, 4.55), -4.55)
        pa.y = max(min(pa.y, 4.35), -4.35)
        cilindro(T, (ax, ay, 8.6), pa + V((0, 0, 0.06)), 0.012, 4, "acero", suave=False)
        caja(T, pa - V((0.07, 0.07, 0)), pa + V((0.07, 0.07, 0.06)), "gris")
    # cable de la antena a la caja
    tubo(T, [V((ax + 0.07, ay, 7.6)), V((ax + 0.07, ay, zt + 0.2)), V((ax + 0.5, ay, zt + 0.05)),
             V((ax + 0.75, ay, zt + 0.05))], 0.022, 6, "negro_mate", radio_codo=0.15, pasos_codo=2)


# ================================================================================================================
# ENTORNO: rampa con barandillas, banco, papelera, parking, farola
# ================================================================================================================

RAMPA_X = (-3.4, 1.0)
RELLANO = (-3.8, 1.6, -6.8)  # x0, x1, y del borde delantero
RAMPA_Y = (-11.2, -6.8)


def entorno(g, datos):
    R = g["Rampa"]
    M = g["Mobiliario"]
    rx0, rx1 = RAMPA_X
    lx0, lx1, ly = RELLANO
    # rellano
    caja(R, (lx0, ly, 0.0), (lx1, -Y_EXT - 0.1, SUELO), "rampa", bisel=0.02)
    # rampa (cuña)
    perfil = [(RAMPA_Y[0], 0.0), (RAMPA_Y[1], 0.0), (RAMPA_Y[1], SUELO)]
    prisma(R, perfil, (rx0, 0, 0), (0, 1, 0), (0, 0, 1), 0.0, -(rx1 - rx0), "rampa")
    # bordillos laterales de la rampa
    for xa, xb in ((rx0, rx0 + 0.15), (rx1 - 0.15, rx1)):
        perfil = [(RAMPA_Y[0], 0.0), (RAMPA_Y[1], SUELO), (RAMPA_Y[1], SUELO + 0.12), (RAMPA_Y[0], 0.12)]
        prisma(R, perfil, (xa, 0, 0), (0, 1, 0), (0, 0, 1), 0.0, -(xb - xa), "zocalo")

    def suelo_en(y):
        if y >= RAMPA_Y[1]:
            return SUELO
        return SUELO * (y - RAMPA_Y[0]) / (RAMPA_Y[1] - RAMPA_Y[0])

    # Barandillas: postes, pasamanos arriba (con remate curvo) y barra intermedia.
    for lado in (-1, 1):
        xr = rx0 + 0.075 if lado < 0 else rx1 - 0.075
        xl = lx0 + 0.08 if lado < 0 else lx1 - 0.08
        y_pared = -Y_EXT - 0.12
        ruta = [(xl, y_pared), (xl, ly + 0.08), (xr, ly + 0.08), (xr, RAMPA_Y[0] + 0.2)]
        postes = [(xl, -Y_EXT - 0.6), (xl, ly + 0.08), (xr, ly - 0.25), (xr, -8.4), (xr, -9.8),
                  (xr, RAMPA_Y[0] + 0.2)]
        for alto, r, segs in ((2.6, 0.06, 8), (1.35, 0.045, 6)):
            pts = []
            for x, y in ruta:
                base = suelo_en(y) + (0.12 if (x == xr and y < RAMPA_Y[1]) else 0.0)
                if x == xr and abs(y - (ly + 0.08)) < 1e-6:
                    base = SUELO
                pts.append(V((x, y, base + alto)))
            if alto > 2:
                # remate: se alarga 0,3 y baja hacia el suelo (como piden las normas de accesibilidad)
                fin = pts[-1]
                pts += [fin + V((0, -0.3, -0.02)), fin + V((0, -0.32, -0.55))]
                tubo(R, pts, r, segs, "acero", radio_codo=0.18, pasos_codo=3)
                # roseta en la pared
                cilindro(R, (xl, -Y_EXT, SUELO + alto), (xl, -Y_EXT - 0.04, SUELO + alto), 0.11, 8, "acero")
            else:
                pts[0] = pts[0] + V((0, -0.5, 0))
                tubo(R, pts, r, segs, "acero", radio_codo=0.12, pasos_codo=2)
        for x, y in postes:
            base = suelo_en(y) + (0.12 if (x == xr and y < RAMPA_Y[1]) else 0.0)
            altura_post = 2.6 - 0.03
            cilindro(R, (x, y, base), (x, y, base + altura_post), 0.05, 6, "acero")
            caja(R, (x - 0.1, y - 0.1, base), (x + 0.1, y + 0.1, base + 0.025), "acero")
            tornillo(R, (x + 0.065, y + 0.065, base + 0.025), (0, 0, 1), r=0.02, alto=0.01)
            tornillo(R, (x - 0.065, y - 0.065, base + 0.025), (0, 0, 1), r=0.02, alto=0.01)

    # --- Banco de espera: tres asientos separados por reposabrazos, patas atornilladas -----------------------------
    bx0, by_atras = 2.45, -Y_EXT - 1.05
    seat_w, arm_w = 0.8, 0.075
    xs = [bx0]
    for i in range(3):
        xs.append(xs[-1] + arm_w + seat_w)
    largo = xs[-1] + arm_w - bx0
    zs = 1.22
    fondo = 0.72

    def yb(f):  # f: distancia desde atrás hacia delante
        return by_atras - f

    for x in xs:  # bastidores (reposabrazos + patas)
        xa, xb = x, x + arm_w
        for f0, f1 in ((0.04, 0.12), (fondo - 0.1, fondo - 0.02)):  # patas
            caja(M, (xa, yb(f1), 0.03), (xb, yb(f0), zs), "poste")
            caja(M, (xa - 0.05, yb(f1) - 0.06, 0.0), (xb + 0.05, yb(f0) + 0.06, 0.03), "gris")
            tornillo(M, ((xa + xb) / 2, yb(f1) - 0.03, 0.03), (0, 0, 1), r=0.022, alto=0.012)
            tornillo(M, ((xa + xb) / 2, yb(f0) + 0.03, 0.03), (0, 0, 1), r=0.022, alto=0.012)
        caja(M, (xa, yb(fondo - 0.02), zs - 0.1), (xb, yb(0.04), zs), "poste")  # travesaño
        caja(M, (xa, yb(fondo - 0.02), zs), (xb, yb(fondo - 0.1), 1.78), "poste")  # pilar del reposabrazos
        caja(M, (xa - 0.01, yb(fondo + 0.02), 1.78), (xb + 0.01, yb(0.14), 1.86), "poste", bisel=0.02)
        caja(M, (xa, yb(0.12), zs), (xb, yb(0.04), 2.35), "poste")  # montante del respaldo
    caja(M, (bx0, yb(0.5), zs - 0.16), (bx0 + largo, yb(0.42), zs - 0.08), "gris")  # larguero
    for i in range(3):
        xa = xs[i] + arm_w + 0.02
        xb = xs[i + 1] - 0.02
        caja(M, (xa, yb(fondo - 0.03), zs), (xb, yb(0.13), zs + 0.05), "banco_asiento", bisel=0.015)
        rot = Matrix.Rotation(math.radians(-10), 3, "X")
        caja(M, (xa, yb(0.14), zs + 0.2), (xb, yb(0.09), 2.3), "banco_asiento", rot=rot,
             pivote=((xa + xb) / 2, yb(0.12), zs + 0.2))
    datos["Banco"] = V((bx0 + largo / 2, yb(fondo / 2), zs + 0.05))

    # --- Papelera médica con pedal, en el rellano junto a la puerta ---------------------------------------------
    px, py = 1.25, -Y_EXT - 0.48
    cilindro(M, (px, py, SUELO), (px, py, SUELO + 0.05), 0.27, 12, "oscuro")
    cilindro(M, (px, py, SUELO + 0.05), (px, py, SUELO + 0.8), 0.25, 12, "marco", r2=0.26)
    cilindro(M, (px, py, SUELO + 0.8), (px, py, SUELO + 0.86), 0.275, 12, "amarillo",
             mat_cara=lambda c, n: "rot_residuos" if n.z > 0.9 else "amarillo")
    # pegatina en la tapa: la UV deco solo cuenta en la cara de arriba
    _uv_tapa(M, (px, py), 0.5)
    caja(M, (px - 0.1, py + 0.24, SUELO + 0.78), (px + 0.1, py + 0.31, SUELO + 0.84), "gris")  # bisagra
    caja(M, (px - 0.12, py - 0.4, SUELO + 0.02), (px + 0.12, py - 0.2, SUELO + 0.07), "gris", bisel=0.01)  # pedal
    caja(M, (px - 0.04, py - 0.26, SUELO + 0.04), (px + 0.04, py - 0.2, SUELO + 0.25), "gris")
    datos["Papelera"] = V((px, py, SUELO))

    # --- Señal de parking ------------------------------------------------------------------------------------------
    sx, sy = -4.9, -10.4
    caja(M, (sx - 0.2, sy - 0.2, 0.0), (sx + 0.2, sy + 0.2, 0.03), "gris")
    for a in (1, -1):
        for b in (1, -1):
            tornillo(M, (sx + a * 0.14, sy + b * 0.14, 0.03), (0, 0, 1), r=0.025, alto=0.015)
    cilindro(M, (sx, sy, 0.03), (sx, sy, 6.0), 0.07, 8, "gris")
    cilindro(M, (sx, sy, 6.0), (sx, sy, 6.05), 0.08, 8, "oscuro")
    for zc, alto, mat in ((5.15, 1.2, "rot_parking_p"), (4.1, 0.5, "rot_parking_sub")):
        caja(M, (sx - 0.6, sy - 0.12, zc - alto / 2), (sx + 0.6, sy - 0.09, zc + alto / 2), "gris",
             mat_cara=lambda c, n, mat=mat: mat if n.y < -0.9 else "gris",
             deco=(V((sx, sy - 0.12, zc)), V((1, 0, 0)), V((0, 0, 1)), 1.2, alto))
        for dz in ((-alto / 2 + 0.15), (alto / 2 - 0.15)):
            caja(M, (sx - 0.1, sy - 0.09, zc + dz - 0.04), (sx + 0.1, sy + 0.09, zc + dz + 0.04), "acero")

    # --- Farola (luz blanca, no cian) ------------------------------------------------------------------------------
    fx, fy = 6.6, -9.3
    cilindro(M, (fx, fy, 0.0), (fx, fy, 0.55), 0.32, 8, "gris", giro=math.pi / 8)
    cilindro(M, (fx, fy, 0.55), (fx, fy, 0.65), 0.24, 8, "gris", r2=0.15, giro=math.pi / 8)
    caja(M, (fx - 0.1, fy - 0.31, 0.15), (fx + 0.1, fy - 0.295, 0.42), "oscuro")  # registro
    tornillo(M, (fx, fy - 0.31, 0.38), (0, -1, 0), r=0.015, alto=0.008)
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        tornillo(M, (fx + 0.22 * math.cos(a), fy + 0.22 * math.sin(a), 0.55), (0, 0, 1), r=0.035, alto=0.03)
    cilindro(M, (fx, fy, 0.6), (fx, fy, 8.0), 0.12, 10, "poste", r2=0.075)
    brazo = [V((fx, fy, 7.9)), V((fx, fy, 8.35)), V((fx - 1.6, fy, 8.35))]
    tubo(M, brazo, 0.065, 8, "poste", radio_codo=0.35, pasos_codo=4)
    hx = fx - 1.75
    caja(M, (hx - 0.55, fy - 0.24, 8.18), (hx + 0.45, fy + 0.24, 8.42), "poste", bisel=0.05)
    caja(g["Farola_neon"], (hx - 0.45, fy - 0.17, 8.14), (hx + 0.38, fy + 0.17, 8.18), "neon_blanco")
    caja(M, (hx - 0.5, fy - 0.2, 8.15), (hx + 0.42, fy + 0.2, 8.19), "oscuro",
         mat_cara=lambda c, n: "oscuro")  # marco del difusor (deja ver el neón por debajo)
    datos["Farola"] = V((hx, fy, 8.1))


def _uv_tapa(g, c, tam):
    """Ajusta la UV deco de las caras de arriba de la última tapa (pegatina de residuos)."""
    import bmesh  # noqa: F401

    idx = g.indice("rot_residuos")
    for f in g.bm.faces:
        if f.material_index == idx:
            for lp in f.loops:
                p = lp.vert.co
                lp[g.deco].uv = ((p.x - c[0]) / tam + 0.5, (p.y - c[1]) / tam + 0.5)


# ================================================================================================================
# INTERIOR (lo que se ve por la puerta y por la ventana de la sala de espera)
# ================================================================================================================


def interior(g, datos):
    I = g["Interior"]
    xi, yi = X_EXT - GROSOR, Y_EXT - GROSOR
    caja(I, (-xi, -yi, SUELO), (xi, yi, SUELO + 0.02), "vinilo")
    zs = SUELO + 0.02
    # rodapié
    for (a, b) in (((-xi, -yi), (xi, -yi + 0.04)), ((-xi, yi - 0.04), (xi, yi)), ((-xi, -yi), (-xi + 0.04, yi)),
                   ((xi - 0.04, -yi), (xi, yi))):
        caja(I, (a[0], a[1], zs), (b[0], b[1], zs + 0.25), "asiento")
    # tabiques de la consulta (esquina delantera derecha): x = 1,1 y y = -1,0, con puerta
    for y0, y1, z0, z1 in ((-yi, -2.9, zs, CORTE_INT), (-2.9, -1.6, 5.4, CORTE_INT), (-1.6, -0.93, zs, CORTE_INT)):
        caja(I, (1.05, y0, z0), (1.2, y1, z1), "interior")
    caja(I, (1.05, -1.08, zs), (xi, -0.93, CORTE_INT), "interior")
    caja(I, (1.0, -2.95, zs), (1.25, -2.9, 5.45), "marco")
    caja(I, (1.0, -1.6, zs), (1.25, -1.55, 5.45), "marco")
    caja(I, (1.0, -2.95, 5.4), (1.25, -1.55, 5.45), "marco")
    # cartel en el tabique, mirando a la sala de espera
    caja(I, (1.035, -4.2, 3.0), (1.05, -3.45, 4.0), "rot_cartel",
         deco=(V((1.035, -3.825, 3.5)), V((0, -1, 0)), V((0, 0, 1)), 0.75, 1.0),
         mat_cara=lambda c, n: "rot_cartel" if n.x < -0.9 else "blanco_puro")
    # mostrador de recepción frente a la puerta
    caja(I, (-3.4, 1.5, zs), (-0.4, 2.2, 2.85), "mostrador")
    caja(I, (-3.5, 1.38, 2.85), (-0.3, 2.25, 2.95), "blanco_puro", bisel=0.02)
    caja(I, (-3.4, 1.47, 0.5), (-0.4, 1.5, 0.75), "acero")  # zócalo de acero
    caja(I, (-2.2, 1.9, 2.95), (-1.4, 2.0, 3.55), "negro_mate")  # pantalla del ordenador
    caja(I, (-1.85, 1.95, 2.95), (-1.75, 2.05, 3.0), "gris")
    # bancada de espera bajo la ventana lateral (3 asientos)
    caja(I, (-xi + 0.25, -2.3, 0.95), (-xi + 0.35, 1.0, 1.05), "gris")
    for y in (-2.1, 0.8):
        caja(I, (-xi + 0.2, y - 0.05, zs), (-xi + 0.45, y + 0.05, 1.05), "gris")
    for k in range(3):
        y0 = -2.25 + k * 1.08
        caja(I, (-xi + 0.05, y0, 1.05), (-xi + 0.8, y0 + 1.0, 1.15), "asiento", bisel=0.02)
        caja(I, (-xi + 0.02, y0, 1.3), (-xi + 0.1, y0 + 1.0, 2.3), "asiento", bisel=0.02)
    # luces del techo (neón)
    N = g["Interior_neon"]
    for (x, y) in ((-2.0, -2.3), (-2.0, 1.6), (3.0, -2.8), (3.0, 2.2)):
        caja(I, (x - 0.85, y - 0.35, CORTE_INT - 0.05), (x + 0.85, y + 0.35, CORTE_INT), "perfil")
        caja(N, (x - 0.78, y - 0.28, CORTE_INT - 0.07), (x + 0.78, y + 0.28, CORTE_INT - 0.04), "neon_blanco")
    datos["LucesInterior"] = [V((-2.0, -2.3, 6.4)), V((-2.0, 1.6, 6.4)), V((3.0, -2.8, 6.4)), V((3.0, 2.2, 6.4))]
