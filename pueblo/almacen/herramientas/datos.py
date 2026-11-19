"""
Datos ajustables del almacén: medidas (studs) y paleta. Todo lo que se toca a mano está aquí.

Coordenadas de trabajo (Blender, antes del GIRO_IMPORTACION): X = ancho, Y = fondo (la fachada principal mira a
-Y), Z = arriba, z = 0 en la base del modelo. 1 unidad = 1 stud. A esta escala 1 stud ~ 1,1 m: el muelle de 1 stud
es la altura de la caja de un camión y el portón de 4 x 4 deja pasar una carretilla cargada.
"""

import math

# ---- estructura -------------------------------------------------------------------------------------------------
S = 0.06                 # cara de arriba de la explanada de hormigón
X0, X1 = -6.5, 6.5       # paredes laterales (cara exterior, valle de la onda)
Y0, Y1 = -2.5, 5.0       # fachada principal y trasera
Z_ZOCALO = 0.5           # zócalo de hormigón (base elevada medio stud)
Z_SUELO = 1.0            # suelo interior = muelle de carga
Z_ALERO = 4.6            # arranque del arco del tejado
Z_CUMBRE = 7.0           # cumbre del arco
GROSOR_MURO = 0.22
ONDA = dict(periodo=0.85, fondo=0.08)

# arco del tejado (segmento de circunferencia que pasa por los aleros y la cumbre)
_semi, _flecha = X1, Z_CUMBRE - Z_ALERO
R_ARCO = (_semi ** 2 + _flecha ** 2) / (2 * _flecha)
ZC_ARCO = Z_CUMBRE - R_ARCO
VUELO_LADO = 0.3         # el tejado sobresale de las paredes
VUELO_FRENTE = 0.3
GROSOR_TEJADO = 0.1


def z_arco(x, r=None):
    r = R_ARCO if r is None else r
    return ZC_ARCO + math.sqrt(max(0.0, r * r - x * x))


# ---- huecos de la fachada --------------------------------------------------------------------------------------
PORTON = dict(x0=-0.6, x1=3.4, z0=Z_SUELO, z1=Z_SUELO + 4.0)           # 4 x 4
PUERTA = dict(x0=-2.4, x1=-1.5, z0=Z_SUELO, z1=Z_SUELO + 2.0)          # puerta de personal
VENTANA_OFICINA = dict(x0=-5.0, x1=-3.6, z0=1.95, z1=2.95)
PORTON_TRASERO = dict(x0=-3.5, x1=-0.5, z0=Z_SUELO, z1=Z_SUELO + 3.0)  # 3 de ancho
CLARISTORIO = dict(y0=-0.8, y1=3.6, z0=3.8, z1=4.32)                   # pared lateral derecha (+X), arriba
TRAGALUCES = [(-3.6, -2.3), (2.3, 3.6)]                                # bandas en x del tejado
TRAGALUZ_Y = (-1.4, 4.0)

# ---- muelle -------------------------------------------------------------------------------------------------------
MUELLE = dict(x0=-5.8, x1=6.2, y0=-4.5, y1=Y0, z1=Z_SUELO)
RAMPA = dict(x0=0.0, x1=2.8, largo_suelo=-6.7)
ESCALONES = dict(x0=-5.6, x1=-4.6)
REPISA_TRASERA = dict(x0=-3.9, x1=-0.1, y1=Y1 + 1.1)

# ---- explanada ------------------------------------------------------------------------------------------------------
EXPLANADA = dict(x0=-9.4, x1=7.7, y0=-8.9, y1=6.8)
HUNDIDO = dict(x=4.7, y=-5.75, radio=1.9, fondo=0.07)   # donde paran las ruedas traseras de los camiones

# ---- colores neón del pueblo ---------------------------------------------------------------------------------------
NEON = "#3DF2FF"
LUZ_CALIDA = "#FFD49A"
