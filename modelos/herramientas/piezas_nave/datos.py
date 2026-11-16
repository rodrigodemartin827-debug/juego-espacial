"""
Datos ajustables de las piezas modulares de nave: estilos por tier, conectores y la regla de encaje.

Todo lo que se ajusta a ojo (colores, rugosidad, cuánto se ensucia cada tier, tamaño de cada conector) está aquí.
Las medidas van en studs (1 unidad de Blender = 1 stud).
"""

# Giro que se aplica a la malla justo antes de exportar (grados alrededor del eje vertical). Lo pide la importación
# de Roblox: sin él la pieza llega mirando hacia atrás. Los JSON se escriben ya en el sistema de Studio (delante = -Z),
# así que si algún día el importador cambia, basta con tocar este número y volver a generar.
GIRO_IMPORTACION = 180

# --------------------------------------------------------------------------------------------------------------
# Conectores
# --------------------------------------------------------------------------------------------------------------
# forma: "cuadrado" (lado) o "circulo" (diámetro). `tam` en studs. Los conectores de salida (en la pieza que recibe)
# y de entrada (en la pieza que se acopla) del mismo tipo tienen la misma brida, así encajan cara con cara.
CONECTORES = {
    "CASCO_LATERAL": {"forma": "cuadrado", "tam": 1.6, "color": "#FF5A3C",
                      "que": "alas, armas y blindaje en los costados del casco"},
    "CASCO_TRASERO": {"forma": "circulo", "tam": 2.4, "color": "#FFB020", "que": "motor principal en la popa"},
    "CASCO_SUPERIOR": {"forma": "cuadrado", "tam": 2.0, "color": "#3CA0FF",
                       "que": "cabina, torretas, escudos y aletas encima del casco"},
    "CASCO_INFERIOR": {"forma": "cuadrado", "tam": 1.2, "color": "#8CFF3C",
                       "que": "tren de aterrizaje, tanques y bahía de carga debajo"},
    "CASCO_FRONTAL": {"forma": "circulo", "tam": 1.2, "color": "#FF3CC8", "que": "proa: cañones frontales"},
    "ALA_PUNTA": {"forma": "cuadrado", "tam": 0.9, "color": "#3CFFE0",
                  "que": "bajo la punta del ala y en los hardpoints: armas, tanques"},
    "ALA_MOTOR": {"forma": "circulo", "tam": 1.6, "color": "#FF8C3C",
                  "que": "borde de salida del ala: motores pequeños y medianos"},
    "MOTOR_ESCAPE": {"forma": "circulo", "tam": 0.0, "color": "#FFFFFF",
                     "que": "salida de la tobera (solo visual: estelas y llama)"},
    "UNIVERSAL": {"forma": "circulo", "tam": 0.8, "color": "#E0E0E0", "que": "se acopla a cualquier conector"},
}

# Regla de encaje (la misma que aplicará el hangar):
#  * Una entrada encaja en una salida si su tipo está en `compatible_con` de la entrada (o alguno es UNIVERSAL),
#  * y su brida cabe: tam(entrada) <= tam(salida).
#  * Al acoplar, la normal de la entrada queda opuesta a la de la salida y sus vectores "arriba" coinciden.
REGLA_ENCAJE = (
    "entrada.tipo en salida.acepta o UNIVERSAL en ambos lados; brida(entrada) <= brida(salida); "
    "pieza.CFrame = salida.WorldCFrame * CFrame.Angles(0, math.pi, 0) * entrada.CFrame:Inverse()"
)

# --------------------------------------------------------------------------------------------------------------
# Estilos por tier
# --------------------------------------------------------------------------------------------------------------
# Cada ranura de material: (color hex, rugosidad, metal). Las ranuras "neon", "neon2", "cristal", "domo" y "llama" no
# van al atlas: salen como mallas aparte (`_neon`, `_neon2`, `_cristal`, `_domo`, `_llama`) con material de Roblox.
#
# Detalle procedural que se hornea en la textura (0 = nada, 1 = mucho):
#   suciedad   mugre en huecos, chorretones y polvo
#   remaches   filas de remaches junto a las juntas de los paneles
#   rayones    arañazos de metal desnudo y bordes gastados
#   paneles    profundidad de las juntas entre paneles
#   tam_panel  tamaño típico de un panel (studs)
#   lineas     fracción de juntas que se encienden (neón horneado en la emisión)
#   marcas     marcas de escuadrón (franjas, chevrones y número) en los costados
#   alien      escamas, venas y reflejo irisado (tier 5)

ESTILOS = {
    1: {
        "nombre": "Básico",
        "ranuras": {
            "primario": ("#7E848B", 0.62, 0.55),
            "secundario": ("#5C6168", 0.66, 0.5),
            "oscuro": ("#2F3237", 0.7, 0.4),
            "metal": ("#A3A8AE", 0.42, 0.95),
            "tobera": ("#4C4843", 0.5, 0.9),
            "acople": ("#8C9097", 0.55, 0.7),
            "aviso": ("#E8B41E", 0.6, 0.1),
            "goma": ("#1B1C1E", 0.9, 0.0),
            "pantalla": ("#1E2A22", 0.3, 0.0),
            "asiento": ("#4A3C30", 0.85, 0.0),
            "organico": ("#5A5048", 0.7, 0.0),
        },
        "neon": "#FFB347", "neon2": "#FF5A3A", "cristal": "#5E8A6E", "domo": "#9FD8FF", "llama": "#FF9A3A",
        "detalle": {"suciedad": 1.0, "remaches": 1.0, "rayones": 0.9, "paneles": 1.0, "tam_panel": 1.6,
                    "lineas": 0.0, "marcas": 0.0, "alien": 0.0},
        "bisel": 0.06,
    },
    2: {
        "nombre": "Militar",
        "ranuras": {
            "primario": ("#E6E8EC", 0.36, 0.25),
            "secundario": ("#FF7A1A", 0.4, 0.15),
            "oscuro": ("#3A4048", 0.5, 0.5),
            "metal": ("#B9BFC7", 0.3, 1.0),
            "tobera": ("#55585E", 0.38, 0.95),
            "acople": ("#4A5058", 0.45, 0.7),
            "aviso": ("#FF7A1A", 0.45, 0.1),
            "goma": ("#1A1B1D", 0.88, 0.0),
            "pantalla": ("#12202C", 0.25, 0.0),
            "asiento": ("#2E3238", 0.75, 0.0),
            "organico": ("#6A6055", 0.6, 0.0),
        },
        "neon": "#FF9A3A", "neon2": "#7FD4FF", "cristal": "#1D3B5A", "domo": "#FFB060", "llama": "#FF8A2A",
        "detalle": {"suciedad": 0.35, "remaches": 0.45, "rayones": 0.35, "paneles": 0.8, "tam_panel": 2.0,
                    "lineas": 0.0, "marcas": 1.0, "alien": 0.0},
        "bisel": 0.06,
    },
    3: {
        "nombre": "Avanzado",
        "ranuras": {
            "primario": ("#46505C", 0.32, 0.8),
            "secundario": ("#6A7684", 0.28, 0.85),
            "oscuro": ("#14181D", 0.4, 0.6),
            "metal": ("#8C96A4", 0.22, 1.0),
            "tobera": ("#3A4250", 0.3, 0.95),
            "acople": ("#1C2128", 0.35, 0.8),
            "aviso": ("#3DF2FF", 0.3, 0.2),
            "goma": ("#16181B", 0.8, 0.0),
            "pantalla": ("#061820", 0.2, 0.0),
            "asiento": ("#1E242C", 0.6, 0.1),
            "organico": ("#2C323A", 0.4, 0.5),
        },
        "neon": "#3DF2FF", "neon2": "#2A8CFF", "cristal": "#123848", "domo": "#3DF2FF", "llama": "#5AD8FF",
        "detalle": {"suciedad": 0.08, "remaches": 0.0, "rayones": 0.06, "paneles": 0.7, "tam_panel": 2.6,
                    "lineas": 0.22, "marcas": 0.0, "alien": 0.0},
        "bisel": 0.05,
    },
    4: {
        "nombre": "Élite",
        "ranuras": {
            "primario": ("#1C1D22", 0.34, 0.65),
            "secundario": ("#D4A63A", 0.22, 1.0),
            "oscuro": ("#07070A", 0.45, 0.5),
            "metal": ("#2C2C33", 0.25, 1.0),
            "tobera": ("#3A3430", 0.3, 1.0),
            "acople": ("#1A1A20", 0.3, 0.9),
            "aviso": ("#D4A63A", 0.22, 1.0),
            "goma": ("#121214", 0.8, 0.0),
            "pantalla": ("#120806", 0.2, 0.0),
            "asiento": ("#1A1416", 0.55, 0.1),
            "organico": ("#111216", 0.3, 0.7),
        },
        "neon": "#FFB020", "neon2": "#FF2A4A", "cristal": "#1A1408", "domo": "#FFC040", "llama": "#FF7A2A",
        "detalle": {"suciedad": 0.0, "remaches": 0.0, "rayones": 0.0, "paneles": 0.75, "tam_panel": 2.2,
                    "lineas": 0.18, "marcas": 0.0, "alien": 0.0, "lineas_oro": 0.5},
        "bisel": 0.05,
    },
    5: {
        "nombre": "Legendario",
        "ranuras": {
            "primario": ("#21122E", 0.25, 0.45),
            "secundario": ("#E6DCF2", 0.3, 0.15),
            "oscuro": ("#0B0712", 0.4, 0.3),
            "metal": ("#6E5A86", 0.22, 0.9),
            "tobera": ("#2A1A3A", 0.3, 0.8),
            "acople": ("#2A1A3A", 0.3, 0.6),
            "aviso": ("#C45CFF", 0.3, 0.2),
            "goma": ("#120A18", 0.7, 0.0),
            "pantalla": ("#0E0618", 0.2, 0.0),
            "asiento": ("#3A1650", 0.5, 0.0),
            "organico": ("#3A1650", 0.42, 0.1),
        },
        "neon": "#C45CFF", "neon2": "#FFFFFF", "cristal": "#8A3DFF", "domo": "#C45CFF", "llama": "#E0A0FF",
        "detalle": {"suciedad": 0.0, "remaches": 0.0, "rayones": 0.0, "paneles": 0.35, "tam_panel": 2.4,
                    "lineas": 0.0, "marcas": 0.0, "alien": 1.0},
        "bisel": 0.05,
    },
}

# Material de Roblox para las mallas sin textura.
MATERIAL_ROBLOX = {
    "neon": "Neon", "neon2": "Neon", "llama": "Neon",
    "cristal": "Glass", "domo": "ForceField",
}
TRANSPARENCIA_ROBLOX = {"cristal": 0.35, "domo": 0.0, "llama": 0.25}

# Límite de triángulos por pieza (por variante, si la pieza tiene izquierda y derecha).
LIMITE_TRIS = 5000
LIMITE_TRIS_CASCO_GRANDE = 8000
