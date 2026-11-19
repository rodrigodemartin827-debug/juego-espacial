"""
Casa del granjero: el que alimenta al pueblo. Casa de paneles con invernadero hidropónico adosado.

Usa el mismo proceso que las otras casas (casa_minero.generar): piezas separadas con su pivote, atlas PBR de 2048
horneado desde una malla alta, turnaround de 8 vistas, FBX con GIRO_IMPORTACION, reimportación y JSON. Lo nuevo:
  * el cristal del invernadero va en el atlas con alfa (condensación pintada): AlphaMode = Transparency,
  * la lámpara UV es neón morado (#9B59B6); el resto de neones, cian (#3DF2FF).

Uso:
    python modelos/herramientas/casa_granjero.py --salida modelos/pueblo/casa_granjero [--rapido] [--vista]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import casa_minero as proceso  # noqa: E402
import granjero_materiales as mat  # noqa: E402
import granjero_piezas as piezas  # noqa: E402

DETALLES = [
    ("Puerta y delantal", -10, 6, (0.9, -4.3, 2.8), 2.4),
    ("Ventana y macetas", 12, 8, (-2.6, -4.3, 3.0), 1.9),
    ("Cartel y enredadera", 18, 6, (4.1, -4.3, 3.3), 1.7),
    ("Gato y botas", -25, 30, (1.3, -5.1, 0.6), 1.3),
    ("Invernadero", -30, 14, (-9.0, -3.0, 2.6), 4.4),
    ("Dentro del invernadero", -10, 20, (-9.0, -1.0, 2.0), 3.0),
    ("Uniones atornilladas", -15, 10, (-11.5, -4.0, 3.6), 1.0),
    ("Ventilas", -60, 35, (-10.6, 0.0, 4.6), 2.4),
    ("Pasillo", -95, 10, (-5.6, 0.0, 2.2), 2.4),
    ("Mesa de trabajo", -20, 25, (-9.8, -4.9, 1.4), 1.6),
    ("Compostero y sacos", -70, 20, (-12.9, -1.2, 0.6), 2.0),
    ("Carretilla", -110, 25, (-13.3, 2.6, 0.5), 1.3),
    ("Tanque y canalón", 110, 15, (6.0, 2.4, 2.8), 2.9),
    ("Medidores y manguera", 70, 8, (5.2, -2.3, 2.4), 1.7),
    ("Tejado y panel solar", 45, 40, (3.0, -1.0, 6.0), 3.2),
    ("Camino", -15, 40, (1.5, -8.2, 0.0), 2.8),
]

ANIMABLES = {
    "puerta": ("Bisagras (eje vertical, canto izquierdo). Se abre hacia fuera.", "Y", [0, -100]),
    "puerta_lateral": ("Bisagras (eje vertical, canto de delante). Abre hacia el pasillo.", "Y", [0, 100]),
    "puerta_invernadero": ("Bisagras (eje vertical). Abre hacia el pasillo.", "Y", [0, -100]),
    "puerta_invernadero_vidrio": ("Va con puerta_invernadero: mismo pivote (soldarlo a la hoja).", "Y", [0, -100]),
    "ventila_abierta": ("Bisagras arriba, junto a la cumbrera (eje horizontal a lo largo del invernadero). "
                        "Modelada abierta 32°.", "X", [-32, 0]),
    "ventila_abierta_vidrio": ("Va con ventila_abierta: mismo pivote.", "X", [-32, 0]),
    "ventila_cerrada": ("Bisagras arriba (eje horizontal). Modelada cerrada.", "X", [0, 32]),
    "ventila_cerrada_vidrio": ("Va con ventila_cerrada: mismo pivote.", "X", [0, 32]),
    "compostero_tapa": ("Bisagras de atrás (eje horizontal). Modelada medio abierta 38°.", "X", [-38, 0]),
}

EXTRUSION = {"casa_paredes": 0.035, "casa_zocalo": 0.03, "casa_techo": 0.04, "invernadero_plantas": 0.14,
             "invernadero_tomateras": 0.12, "macetas_hierbas": 0.1, "cartel": 0.03, "enredadera": 0.03,
             "camino_piedras": 0.05, "canalon_grande": 0.05, "compostero": 0.06, "semillero": 0.04,
             "invernadero_estanterias": 0.03, "sacos_sustrato": 0.03, "gato": 0.02, "sombrero": 0.03}


def main():
    proceso.generar({
        "nombre": "casa_granjero",
        "titulo": "Casa del granjero",
        "descripcion": "Casa del granjero del pueblo, con invernadero hidropónico adosado por un pasillo cubierto. "
                       "Piezas separadas con un atlas PBR; el cristal del invernadero lleva alfa en el atlas.",
        "presupuesto": 15000,
        "construir": piezas.construir,
        "materiales": mat.crear_materiales,
        "detalles": DETALLES,
        "animables": ANIMABLES,
        "extrusion": EXTRUSION,
        "color_vidrio": "#A6D3CF",
        "neones": {"_neon_morado": ("#9B59B6", 5.0)},
        "translucido": "vidrio",
        # Resplandor morado de la lámpara UV dentro del invernadero y luz de día que entra por el cristal.
        "luces_render": [((-9.0, -2.0, 4.1), 140.0, (0.62, 0.36, 0.72)), ((-9.0, 2.0, 4.1), 140.0, (0.62, 0.36, 0.72)),
                         ((-9.0, 0.0, 3.0), 260.0, (0.92, 1.0, 0.9))],
    })


if __name__ == "__main__":
    main()
