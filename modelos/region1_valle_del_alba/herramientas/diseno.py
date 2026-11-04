r"""
Datos de diseño del Valle del Alba: dónde va cada cosa y cuánto mide. Todo lo ajustable está aquí, no en el código.

Coordenadas de DISEÑO (x hacia el este, y hacia el norte, en studs, de -1885 a 1885): ver geo.py.
Las alturas son studs sobre el nivel del mar (radio 2400).

Plano general (norte arriba):

          colinas del norte, bosque, manantial del río
                         |  río
     bosque NO           |                bosque NE
                AURORA   |
              (capital) =puente= cruce --- PRADOVERDE ) COLINA DEL ATARDECER
                         |           \
     bosque O            |            \
                          \        LOS MOLINOS (campos)        bosque SE
                           \
                            río -> al mar del suroeste
"""

# --------------------------------------------------------------------------------------------------------------
# Relieve general
# --------------------------------------------------------------------------------------------------------------

SEMILLA = 11
SUELO_VALLE = 20.0  # altura media del fondo del valle

# Ondulación de las praderas: (amplitud en studs, longitud de onda en studs, octavas)
ONDULACION = [(7.0, 520.0, 4), (2.2, 150.0, 3)]

# Anillo de colinas que cierra el valle: elipse (radio este-oeste, radio norte-sur) en studs.
ANILLO_RADIOS = (1330.0, 1420.0)
ANILLO_ALTURA = 80.0
ANILLO_DESDE, ANILLO_HASTA = 0.66, 0.94  # fracción de la elipse donde empieza a subir y donde está la cresta
COSTA_DESDE, COSTA_HASTA = 1.02, 1.30  # fracción de la elipse donde el valle pasa al relieve del planeta de prueba
COSTA_RUIDO = 0.22
PASO_RIO = 300.0  # ancho (studs) del paso que se abre en la sierra donde sale el río
PASO_CAMINO = 140.0
CAMINOS_A_OTRAS_REGIONES = ("Aurora_Oeste", "Molinos_Sur")

# Franja del borde de la cara donde el valle se funde con el relieve del planeta de prueba (sin costura).
FRANJA_BORDE = 420.0

# Colinas sueltas: (x, y, altura, radio_x, radio_y, giro en grados)
COLINAS = [
    (-950.0, 650.0, 55.0, 300.0, 260.0, 20.0),
    (-250.0, 960.0, 36.0, 260.0, 220.0, -15.0),
    (920.0, 660.0, 62.0, 320.0, 280.0, 35.0),
    (-920.0, -300.0, 44.0, 280.0, 240.0, 0.0),
    (860.0, -760.0, 50.0, 300.0, 260.0, -25.0),
    (-480.0, -760.0, 24.0, 230.0, 200.0, 10.0),
    (560.0, 920.0, 30.0, 200.0, 180.0, 0.0),
    (-720.0, 280.0, 18.0, 180.0, 160.0, 0.0),
]

# La colina del atardecer (sale en la cinemática): cima ancha y casi llana para el mirador.
COLINA_ATARDECER = dict(x=780.0, y=20.0, altura=88.0, radio_x=340.0, radio_y=290.0, giro=12.0, meseta=0.16)
# Mirador: un balcón natural (terraza llana) a media ladera, en la cara oeste. Con un planeta de radio 2400 la
# curvatura es tan fuerte que desde la cima el propio lomo de la colina tapa el valle; desde la ladera se ve la
# bajada hasta Pradoverde, el río y el valle hasta el horizonte, con el sol poniéndose enfrente.
MIRADOR = (650.0, 2.0)
TERRAZA_MIRADOR = dict(radio=17.0, transicion=16.0)
MIRADOR_LIBRE = 45.0  # radio sin rocas ni árboles sueltos alrededor del mirador

# --------------------------------------------------------------------------------------------------------------
# Río
# --------------------------------------------------------------------------------------------------------------

# Puntos del cauce de norte a sur: (x, y, nivel del agua, semiancho). Entre puntos se interpola con una curva suave.
RIO = [
    (230.0, 1270.0, 52.0, 7.0),  # manantial (sale de una charca entre las colinas del norte)
    (190.0, 1100.0, 44.0, 8.0),
    (80.0, 820.0, 26.0, 10.0),
    (130.0, 520.0, 17.5, 12.0),
    (45.0, 280.0, 15.0, 13.0),
    (90.0, 110.0, 13.5, 14.0),  # el puente pasa por aquí
    (70.0, -150.0, 12.0, 15.0),
    (-40.0, -380.0, 10.5, 16.0),
    (-70.0, -640.0, 9.0, 17.0),
    (-200.0, -880.0, 7.5, 18.0),
    (-390.0, -1150.0, 5.0, 19.0),
    (-560.0, -1450.0, 2.0, 21.0),
    (-680.0, -1950.0, -2.0, 24.0),  # sale de la cara y llega al mar
]
RIO_PROFUNDIDAD = 3.6  # bajo el nivel del agua, en el centro del cauce
RIO_TALUD = 0.42  # pendiente de las orillas (subida por stud)
RIO_VEGA = (3.0, 90.0)  # el terreno baja un poco cerca del río: (studs, ancho)
CHARCA_MANANTIAL = (230.0, 1290.0, 34.0)  # (x, y, radio) de la charca donde nace el río

# --------------------------------------------------------------------------------------------------------------
# Sitios. Tamaños en studs; el suelo se aplana a la altura media del terreno dentro de su huella.
# --------------------------------------------------------------------------------------------------------------

SITIOS = {
    "Aurora": dict(x=-390.0, y=210.0, ancho=400.0, fondo=400.0, borde=70.0, esquina=40.0),
    "Pradoverde": dict(x=390.0, y=-10.0, ancho=120.0, fondo=120.0, borde=45.0, esquina=20.0),
    "LosMolinos": dict(x=370.0, y=-590.0, ancho=120.0, fondo=120.0, borde=45.0, esquina=20.0),
}

# Campos de cultivo alrededor de Los Molinos: (x, y, radio_x, radio_y). El relieve se suaviza ahí.
CAMPOS = dict(x=380.0, y=-600.0, radio_x=300.0, radio_y=250.0, suavizado=0.75)

# --------------------------------------------------------------------------------------------------------------
# Caminos: lista de puntos (x, y) en diseño; se suavizan con una curva. Ancho en studs.
# --------------------------------------------------------------------------------------------------------------

# Centro del puente (el camino Aurora - cruce pasa por él). El camino sube en «lomo de asno» al cruzar el río:
# joroba = studs que sube en el centro, ancho_joroba = a qué distancia se nota (gaussiana).
PUENTE = dict(x=88.0, y=118.0, joroba=4.5, ancho_joroba=42.0)
CRUCE = (240.0, 80.0)

CAMINOS = {
    "Aurora_Pradoverde": dict(
        ancho=11.0,
        puntos=[(-190.0, 205.0), (-100.0, 180.0), (-10.0, 140.0), (88.0, 118.0), (170.0, 100.0), CRUCE,
                (300.0, 30.0), (330.0, -8.0)],
    ),
    "Cruce_LosMolinos": dict(
        ancho=10.0,
        puntos=[CRUCE, (255.0, -60.0), (250.0, -220.0), (300.0, -380.0), (360.0, -500.0), (370.0, -530.0)],
    ),
    "Sendero_Mirador": dict(
        ancho=6.0,
        puntos=[(450.0, -5.0), (520.0, 28.0), (585.0, 40.0), (630.0, 24.0), (650.0, 2.0)],
    ),
    "Aurora_Oeste": dict(  # sale hacia la región del oeste, por donde el planeta sigue siendo tierra
        ancho=10.0,
        puntos=[(-592.0, 215.0), (-760.0, 250.0), (-980.0, 360.0), (-1200.0, 440.0), (-1450.0, 500.0)],
    ),
    "Molinos_Sur": dict(
        ancho=8.0,
        puntos=[(370.0, -652.0), (390.0, -800.0), (440.0, -1000.0), (420.0, -1250.0), (360.0, -1500.0)],
    ),
}
CAMINO_SUAVIZADO = 45.0  # studs: el perfil del camino es el terreno suavizado con esta ventana
CAMINO_TRANSICION = 16.0  # studs de transición entre el camino aplanado y el terreno

# --------------------------------------------------------------------------------------------------------------
# Bosques: (x, y, radio, densidad 0-1). La forma exacta la recorta un ruido.
# --------------------------------------------------------------------------------------------------------------

BOSQUES = [
    (-820.0, 760.0, 420.0, 1.0),
    (860.0, 720.0, 360.0, 1.0),
    (-960.0, -260.0, 320.0, 0.9),
    (900.0, -720.0, 340.0, 0.9),
    (-380.0, -1080.0, 330.0, 0.85),
    (-120.0, 1120.0, 300.0, 0.9),
    (720.0, 270.0, 130.0, 0.8),  # bosquete en la ladera norte de la colina del atardecer
    (-60.0, -900.0, 160.0, 0.6),
]
# Bosques sobre la sierra que rodea el valle: dónde (fracción de la elipse) y cuánto.
BOSQUE_SIERRA = dict(desde=0.62, hasta=1.12, densidad=0.85, umbral=0.05)
ROCAS_LADERA = 0.012  # probabilidad de roca en laderas de más de ~20° (por punto de la rejilla)
ARBOLES_SUELTOS = 0.0025  # probabilidad de árbol suelto en pradera (por punto de la rejilla de 8 studs)

# --------------------------------------------------------------------------------------------------------------
# Niveles de detalle (LOD), en studs. Los usan los renders (lod.py) y el script de Roblox (datos exportados).
# Cada cosa se dibuja DETALLADA hasta «detalle», SIMPLE hasta «simple» y no se dibuja más allá. Además, lo que queda
# por debajo del horizonte del planeta (radio 2400: la curva tapa mucho) no se dibuja nunca.
# --------------------------------------------------------------------------------------------------------------
LOD = dict(
    edificios=dict(detalle=220.0, simple=2600.0),
    mobiliario=dict(detalle=140.0, simple=500.0),
    vegetacion=dict(detalle=160.0, simple=1100.0),
    hierba=dict(detalle=110.0, simple=110.0),
    terreno=dict(detalle=650.0, simple=1e9),  # distancia al punto más cercano del trozo
    silueta_aurora=700.0,  # más allá, Aurora entera se cambia por su silueta (una malla)
    horizonte_margen=40.0,  # el horizonte se calcula con el radio del planeta menos esto (por prudencia)
)
TERRENO_TROZOS = dict(trozos=8, cuadros_detalle=96, cuadros_simple=16, faldon=8.0)

DISTANCIAS_LIBRES = dict(sitio=40.0, camino=14.0, rio=20.0)  # sin árboles a menos de esto
