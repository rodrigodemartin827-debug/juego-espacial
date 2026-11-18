"""
Taberna «La Última Órbita»: el edificio más social del pueblo.

Usa el mismo proceso que las casas (casa_minero.generar): piezas separadas con su pivote, atlas PBR de 2048 horneado
desde una malla alta, turnaround de 8 vistas, FBX con GIRO_IMPORTACION, reimportación y JSON.

Uso:
    python modelos/herramientas/taberna.py --salida modelos/pueblo/taberna [--rapido] [--vista] [--detalles]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import casa_minero as proceso  # noqa: E402
import taberna_materiales as mat  # noqa: E402
import taberna_piezas as piezas  # noqa: E402

DETALLES = [
    ("Porche", -20, 10, (0.0, -4.2, 3.0), 4.2),
    ("Puertas saloon", -8, 5, (1.6, -3.7, 3.2), 1.8),
    ("Ventana y banco", 12, 6, (-3.4, -3.6, 3.3), 2.2),
    ("Cartel", -10, 12, (1.6, -4.3, 6.0), 2.4),
    ("Pizarra y campana", -25, 4, (-0.6, -3.8, 3.2), 1.4),
    ("Tablón y farol", 20, 4, (3.7, -3.6, 3.4), 1.3),
    ("Postes y suelo", -35, 25, (-5.0, -4.6, 1.6), 1.8),
    ("Barril y cenicero", 30, 15, (4.8, -4.4, 1.5), 1.3),
    ("Puerta trasera", 165, 8, (3.5, 4.2, 2.6), 2.4),
    ("Cocina", 80, 8, (6.5, 0.3, 3.4), 2.2),
    ("Tejado", -30, 35, (0.0, 0.5, 8.2), 4.5),
    ("Speeder y farola", -55, 12, (-6.0, -5.2, 1.6), 3.2),
]

ANIMABLES = {
    "puerta_saloon_izq": ("Bisagras de vaivén (eje vertical, canto izquierdo). Abre a los dos lados.", "Y", [-95, 95]),
    "puerta_saloon_der": ("Bisagras de vaivén (eje vertical, canto derecho). Abre a los dos lados.", "Y", [-95, 95]),
    "puerta_trasera": ("Bisagras (eje vertical). Abre hacia fuera.", "Y", [0, 100]),
    "ventana_lateral_contraventana": ("Bisagras (eje vertical). Modelada abierta 65°.", "Y", [-65, 25]),
    "medidor_puerta": ("Bisagras (eje vertical) en el canto delantero.", "Y", [0, 110]),
}

EXTRUSION = {"muros": 0.03, "cimiento": 0.04, "tejado": 0.04, "porche_suelo": 0.025, "porche_postes": 0.035,
             "pizarra_menu": 0.02, "tablon_anuncios": 0.02, "barril_maceta": 0.02, "barriles": 0.025,
             "speeder_bike": 0.03, "aspiradores": 0.03, "cartel": 0.03}


def main():
    proceso.generar({
        "nombre": "taberna",
        "titulo": "Taberna «La Última Órbita»",
        "descripcion": "La taberna del pueblo: una planta de techo alto con porche cubierto, puertas de saloon y "
                       "cartel tallado. Piezas separadas con un atlas PBR.",
        "presupuesto": 16000,
        "construir": piezas.construir,
        "materiales": mat.crear_materiales,
        "detalles": DETALLES,
        "animables": ANIMABLES,
        "extrusion": EXTRUSION,
        "color_vidrio": "#D9A05B",
        # Luz cálida dentro (la taberna está abierta): se ve por las puertas y las ventanas.
        "luces_render": [((-3.0, 0.0, 4.8), 260.0, (1.0, 0.72, 0.42)), ((2.2, 0.5, 4.8), 260.0, (1.0, 0.72, 0.42))],
    })


if __name__ == "__main__":
    main()
