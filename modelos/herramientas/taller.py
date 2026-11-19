"""
Taller de reparaciones del pueblo.

Usa el mismo proceso que las casas (casa_minero.generar): piezas separadas con su pivote, atlas PBR de 2048 horneado
desde una malla alta, turnaround de 8 vistas, FBX con GIRO_IMPORTACION (180° en el eje vertical), reimportación y
JSON. Después completa el JSON con lo propio del taller (el portón desliza en vez de girar, anclajes de efectos).

Uso:
    python modelos/herramientas/taller.py --salida modelos/pueblo/taller [--rapido] [--vista] [--detalles]
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import casa_minero as proceso  # noqa: E402
import taller_materiales as mat  # noqa: E402
import taller_piezas as piezas  # noqa: E402

DETALLES = [
    ("Portón y raíl", -15, 8, (-1.6, -4.9, 2.4), 2.9),
    ("Ruedas del raíl", -20, 10, (-2.6, -4.8, 4.45), 0.9),
    ("Quemaduras del portón", -10, 15, (-1.6, -4.9, 0.6), 1.4),
    ("Panel de herramientas", -8, 6, (1.95, -4.7, 2.95), 1.5),
    ("Banco y tornillo", -30, 30, (2.0, -5.1, 1.8), 1.7),
    ("Soldadora", -35, 18, (-4.75, -5.5, 0.6), 1.2),
    ("Cuadro, señal y medidor", -20, 6, (4.7, -4.8, 3.0), 1.5),
    ("Focos, pluma y cadena", -30, 12, (-1.6, -5.5, 4.4), 1.8),
    ("Puerta lateral", 75, 8, (6.2, 0.4, 2.0), 2.1),
    ("Compresor", 60, 18, (6.6, -3.1, 1.1), 1.5),
    ("Bidones", -70, 20, (-7.0, -3.4, 1.0), 1.5),
    ("Ventana lateral", -95, 5, (-6.1, 0.0, 2.75), 1.0),
    ("Piezas apiladas", -115, 20, (-7.0, 3.1, 0.8), 1.8),
    ("Extractor de atrás", 175, 8, (1.85, 4.6, 2.9), 1.1),
    ("Extractor del techo", 150, 30, (2.7, 3.2, 6.6), 1.0),
    ("Rampa y manchas", -10, 45, (-1.6, -5.4, 0.1), 1.9),
]

ANIMABLES = {
    "puerta_lateral": ("Bisagras (eje vertical) en el canto de atrás. Se abre hacia fuera.", "Y", [0, 100]),
    "cuadro_puerta": ("Bisagras (eje vertical) en el canto izquierdo. Modelada abierta 105°.", "Y", [-105, 0]),
    "extractor_aspas": ("Gira sin parar alrededor del eje vertical.", "Y", [0, 360]),
    "ventilador_trasero_aspas": ("Gira sin parar alrededor del eje perpendicular al muro.", "Z", [0, 360]),
}

EXTRUSION = {"losa": 0.03, "zocalo": 0.04, "muros": 0.04, "techo": 0.05, "rampa": 0.03, "panel_herramientas": 0.02,
             "cartel_horario": 0.012, "senal_alto_voltaje": 0.012, "compresor": 0.03, "banco_trabajo": 0.025,
             "soldadora": 0.03, "porton": 0.035, "puerta_lateral": 0.03}


def completar_json(carpeta):
    ruta = os.path.join(carpeta, "taller.json")
    with open(ruta, encoding="utf-8") as f:
        datos = json.load(f)
    d = proceso.a_roblox((-1, 0, 0))
    o = proceso.a_roblox((0, 0, 0))
    eje = [round(d[i] - o[i], 3) for i in range(3)]
    for p in datos["piezas"]:
        if p["nombre"] in ("porton", "porton_cristal"):
            p["animable"] = {
                "descripcion": "Desliza en horizontal a lo largo de la fachada (hacia la izquierda vista desde "
                               "delante) colgado del raíl. Mover el CFrame en la dirección indicada.",
                "direccion_apertura_roblox": eje,
                "recorrido_studs": piezas.CORRIDA,
                "nota": "porton_cristal va soldado (WeldConstraint) a porton y se mueve con él.",
            }
    datos["frente"] = "En Blender la fachada (portón) mira a -Y. Con el giro, en el FBX mira a +Z."
    datos["efectos_sugeridos"] = {
        "chispas_soldadura": "ParticleEmitter en el anclaje 'chispas' de la soldadora (pinza en la rampa), a ráfagas.",
        "chispas_cuadro": "Chispazo ocasional en el anclaje del cuadro eléctrico abierto.",
        "humo_extractor": "Humo gris tenue saliendo de 'extractor_boca' (techo) y de 'boca' del extractor de atrás.",
        "luces": "SpotLight cian #3DF2FF en luz_foco_izq y luz_foco_der apuntando a la explanada; PointLight cálida "
                 "en luz_interior.",
        "sonido": "Martillazos y soldadura en bucle con RollOff desde el centro del portón.",
    }
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)


def main():
    proceso.generar({
        "nombre": "taller",
        "titulo": "Taller de reparaciones",
        "descripcion": "El taller del pueblo: nave de chapa con techo curvo de hangar, portón corredero, banco, "
                       "soldadora, compresor y herramientas con sus siluetas. Piezas separadas con un atlas PBR.",
        "presupuesto": 15000,
        "construir": piezas.construir,
        "materiales": mat.crear_materiales,
        "detalles": DETALLES,
        "animables": ANIMABLES,
        "extrusion": EXTRUSION,
        "color_vidrio": "#8E978C",
        "luces_render": [((-1.6, 0.4, 4.4), 220.0, (1.0, 0.72, 0.45)), ((-1.6, -5.6, 4.6), 90.0, (0.24, 0.95, 1.0)),
                         ((-4.6, -5.9, 0.6), 25.0, (0.6, 0.8, 1.0))],
    })
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    if "--vista" not in args:
        completar_json(os.path.abspath(args[args.index("--salida") + 1]))


if __name__ == "__main__":
    main()
