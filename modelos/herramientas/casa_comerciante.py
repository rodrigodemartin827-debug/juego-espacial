"""
Casa del comerciante: tienda de suministros en la planta baja y vivienda arriba.

Usa el mismo proceso que la casa del minero (casa_minero.generar): piezas separadas con su pivote, atlas PBR de
2048 horneado desde una malla alta, turnaround de 8 vistas, FBX con GIRO_IMPORTACION, reimportación y JSON.

Uso:
    python modelos/herramientas/casa_comerciante.py --salida modelos/pueblo/casa_comerciante [--rapido] [--vista]
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import casa_minero as proceso  # noqa: E402
import comerciante_materiales as mat  # noqa: E402
import comerciante_piezas as piezas  # noqa: E402

DETALLES = [
    ("Escaparate", -8, 6, (-1.7, -4.4, 3.0), 3.3),
    ("Expositor", 5, 2, (-1.7, -3.4, 2.4), 2.1),
    ("Puerta tienda", -15, 6, (3.2, -4.3, 2.6), 2.2),
    ("Toldo y cartel", -35, 12, (-1.7, -4.8, 4.6), 3.2),
    ("Pizarra", -30, 4, (4.9, -4.2, 2.6), 0.9),
    ("Puerta casa", 70, 6, (6.0, 0.8, 2.6), 2.3),
    ("Cajas y contenedor", 60, 18, (6.6, 3.0, 1.0), 1.5),
    ("Silla y medidor", 65, 10, (6.2, -2.4, 2.4), 1.9),
    ("Persiana", -15, 8, (-1.7, -4.3, 7.5), 1.8),
    ("Cubierta", -35, 40, (-0.5, 1.5, 9.3), 4.0),
    ("Bajante", 160, 10, (-4.8, 4.4, 4.5), 2.4),
    ("Poste y escalón", -40, 15, (-3.5, -5.2, 1.0), 1.6),
]

ANIMABLES = {
    "puerta_tienda": ("Bisagras de vaivén (eje vertical en el canto izquierdo). Abre a los dos lados.", "Y",
                      [-95, 95]),
    "puerta_tienda_cristal": ("Va con la puerta_tienda: mismo pivote (soldarlo a la hoja).", "Y", [-95, 95]),
    "puerta_lateral": ("Bisagras (eje vertical, canto de atrás). Abre hacia fuera.", "Y", [0, -100]),
    "medidor_puerta": ("Bisagras (eje vertical) en el canto delantero.", "Y", [0, 110]),
    "contenedor_tapa": ("Bisagra de atrás del contenedor (eje horizontal).", "Z", [0, 100]),
}

EXTRUSION = {"casa_paredes": 0.035, "casa_zocalo": 0.03, "casa_techo": 0.04, "felpudo_rejilla": 0.03,
             "escaparate_expositor": 0.03, "pizarra": 0.02, "cartel_repartidor": 0.02, "cajas_mercancia": 0.025,
             "silla_plegable": 0.03, "aire_acondicionado": 0.03}


def main():
    proceso.generar({
        "nombre": "casa_comerciante",
        "titulo": "Casa del comerciante",
        "descripcion": "Casa del comerciante del pueblo: tienda de suministros abajo y vivienda arriba. Piezas "
                       "separadas con un atlas PBR.",
        "presupuesto": 14000,
        "construir": piezas.construir,
        "materiales": mat.crear_materiales,
        "detalles": DETALLES,
        "animables": ANIMABLES,
        "extrusion": EXTRUSION,
        "color_vidrio": "#A6D3CF",
        # Luz cálida dentro de la tienda (abierta): ilumina el expositor tras el cristal.
        "luces_render": [((-3.3, -3.4, 4.9), 70.0, (1.0, 0.84, 0.62)), ((-0.2, -3.4, 4.9), 70.0, (1.0, 0.84, 0.62)), ((3.2, -2.0, 4.6), 120.0, (1.0, 0.84, 0.62))],
    })


if __name__ == "__main__":
    main()
