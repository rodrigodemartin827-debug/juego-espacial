"""
Genera el almacén del pueblo: geometría, atlas horneado de 2048 (color, normal, rugosidad, metal, emisión),
FBX para Roblox, turnaround de 8 vistas, hoja de detalles y almacen.json.

Uso (desde la raíz del repositorio):
    .venv/bin/python pueblo/almacen/herramientas/generar.py                 # todo, calidad final
    .venv/bin/python pueblo/almacen/herramientas/generar.py --vista-previa  # sin hornear: renders rápidos con los
                                                                            # materiales procedurales (revisar forma)
    .venv/bin/python pueblo/almacen/herramientas/generar.py --rapido        # todo a baja resolución
"""

import argparse
import json
import math
import os
import sys
import time

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)

import bpy  # noqa: E402
import bmesh  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402
from PIL import Image, ImageDraw, ImageFilter, ImageFont  # noqa: E402

import datos as D  # noqa: E402
import imagenes as I  # noqa: E402
import materiales as MT  # noqa: E402
import modelo  # noqa: E402
from geo import triangulos, volumen_firmado  # noqa: E402
from materiales import Mat  # noqa: E402

SALIDA = os.path.abspath(os.path.join(AQUI, ".."))
NOMBRE = "almacen"
PRESUPUESTO = 13000


# --------------------------------------------------------------------------------------------------------------
# Paleta: cada material cuenta su historia (ver materiales.Mat)
# --------------------------------------------------------------------------------------------------------------


def paleta():
    chapa = dict(rug=0.55, metal=0.15, sucio=0.65, z_suelo=0.5, chorretones=0.55, oxido=0.22, bordes=0.35, ruido=0.07)
    P = [
        Mat("chapa_gris", "#7C848B", **chapa),
        Mat("chapa_clara", "#9AA3A9", **{**chapa, "sucio": 0.35, "chorretones": 0.25, "oxido": 0.04}),
        Mat("chapa_oscura", "#666E74", **{**chapa, "sucio": 0.8, "chorretones": 0.7, "oxido": 0.42}),
        Mat("chapa_verdosa", "#76827A", **{**chapa, "oxido": 0.15}),
        Mat("chapa_interior", "#A9ADAE", rug=0.7, metal=0.2, sucio=0.3, z_suelo=1.0, ruido=0.05),
        Mat("remate", "#3E454B", rug=0.5, metal=0.35, bordes=0.5, oxido=0.18, sucio=0.4, z_suelo=0.5),
        Mat("remache", "#5D646A", rug=0.4, metal=0.7, oxido=0.25, bordes=0.6, bisel=0.012),
        Mat("tejado", "#99A1A6", rug=0.42, metal=0.55, chorretones=0.45, oxido=0.12, sucio=0.2, z_suelo=4.4,
            relieve=("ondas_y", D.ONDA["periodo"], 0.07), ruido=0.06),
        Mat("tejado_interior", "#8E9496", rug=0.7, metal=0.3, ruido=0.05, relieve=("ondas_y", D.ONDA["periodo"], 0.05)),
        Mat("canalon", "#6F777D", rug=0.45, metal=0.6, chorretones=0.3, oxido=0.2, bordes=0.3),
        Mat("hormigon_zocalo", "#9B978E", rug=0.92, sucio=0.6, relieve=("poros", 0.25, 0.012), ruido=0.12,
            bordes=0.4, color_bordes="#B9B4A8"),
        Mat("hormigon_muelle", "#A29E95", rug=0.9, sucio=0.45, z_suelo=1.0, relieve=("poros", 0.25, 0.012),
            ruido=0.1, bordes=0.5, color_bordes="#BDB8AC"),
        Mat("hormigon_explanada", "#8E8A83", rug=0.9, sucio=0.3, relieve=("poros", 0.3, 0.012), ruido=0.14,
            juntas=3.0, escala_ruido=0.6),
        Mat("suelo_interior", "#8D8B86", rug=0.6, ruido=0.1, sucio=0.25, z_suelo=1.0, relieve=("poros", 0.3, 0.006),
            juntas=3.0),
        Mat("angular_franjas", "#1B1B1B", rug=0.55, metal=0.3, franjas=("#E9B10C", "#1A1A1A", 0.16), bordes=0.8,
            color_bordes="#8E9296", rayas=0.6, z_rayas=1.3),
        Mat("chapa_lagrimada", "#8B9297", rug=0.38, metal=0.85, relieve=("lagrimada", 0.5, 0.012), sucio=0.55,
            z_suelo=0.0, rayas=0.4, z_rayas=1.4, oxido=0.08),
        Mat("persiana", "#A7AEB3", rug=0.42, metal=0.55, rayas=0.9, z_rayas=2.6, sucio=0.5, z_suelo=1.0,
            chorretones=0.3, bordes=0.35),
        Mat("persiana_nueva", "#BDC4C8", rug=0.35, metal=0.6, rayas=0.3, z_rayas=2.0, sucio=0.2, z_suelo=1.0),
        Mat("persiana_oscura", "#8F969B", rug=0.48, metal=0.5, rayas=1.0, z_rayas=2.6, sucio=0.6, z_suelo=1.0,
            oxido=0.12),
        Mat("persiana_trasera", "#979EA2", rug=0.52, metal=0.45, rayas=1.0, z_rayas=2.4, sucio=0.8, z_suelo=1.0,
            chorretones=0.6, oxido=0.32, bordes=0.5),
        Mat("persiana_trasera_clara", "#B1B8BC", rug=0.4, metal=0.55, rayas=0.5, sucio=0.4, z_suelo=1.0),
        Mat("persiana_oxido", "#8A8682", rug=0.62, metal=0.35, rayas=0.8, sucio=0.8, z_suelo=1.0, oxido=0.75),
        Mat("guia", "#4A5157", rug=0.5, metal=0.65, bordes=0.55, oxido=0.2, sucio=0.4, z_suelo=1.0),
        Mat("tambor", "#9CA3A8", rug=0.45, metal=0.55, sucio=0.3, chorretones=0.3, ruido=0.08),
        Mat("tambor_viejo", "#8D9397", rug=0.5, metal=0.5, sucio=0.5, oxido=0.35, chorretones=0.5),
        Mat("goma", "#1D1D1F", rug=0.9, ruido=0.08),
        Mat("correa", "#C9A21E", rug=0.7, ruido=0.1, sucio=0.5, z_suelo=1.0),
        Mat("metal_desnudo", "#8C9195", rug=0.35, metal=0.9, oxido=0.12, bisel=0.01),
        Mat("metal_pulido", "#C9CDD0", rug=0.2, metal=1.0, bisel=0.008),
        Mat("laton", "#B69A5A", rug=0.3, metal=1.0, bisel=0.008, sucio=0.2),
        Mat("cadena", "#6E7275", rug=0.4, metal=0.9, oxido=0.35, bisel=0.008),
        Mat("puerta_azul", "#3B5D79", rug=0.48, bordes=0.55, color_bordes="#8A9297", rayas=0.35, z_rayas=1.6,
            sucio=0.45, z_suelo=1.0, ruido=0.06),
        Mat("marco_puerta", "#2D3236", rug=0.5, metal=0.3, bordes=0.6),
        Mat("chapa_patada", "#9DA4A8", rug=0.3, metal=0.9, rayas=1.0, z_rayas=1.4, sucio=0.4, z_suelo=1.0),
        Mat("marco_ventana", "#30363B", rug=0.5, metal=0.3, bordes=0.5, oxido=0.15),
        Mat("cristal", "#A3B5B2", rug=0.08, alfa=0.15, malla_alambre=0.13, sucio=0.5, z_suelo=1.6),
        Mat("cristal_limpio", "#A8BCC0", rug=0.05, alfa=0.25),
        Mat("policarbonato", "#D7E3E6", rug=0.3, alfa=0.55, relieve=("ondas_y", D.ONDA["periodo"], 0.05),
            sucio=0.3, z_suelo=6.0),
        Mat("cartel_oficina", "#1F3F66", rug=0.45),
        Mat("cartel_horario", "#E9E6DC", rug=0.45),
        Mat("cartel_extintor", "#C21E1E", rug=0.45),
        Mat("senal", "#1F4E9C", rug=0.4),
        Mat("poste_galv", "#A6ACB0", rug=0.4, metal=0.85, sucio=0.4, ruido=0.08),
        Mat("extintor_rojo", "#B5181A", rug=0.32, bordes=0.25, color_bordes="#E0E0E0"),
        Mat("extintor_negro", "#1E1F21", rug=0.6),
        Mat("manometro", "#F0EFE8", rug=0.2, emision=("#FFFFFF", 0.0)),
        Mat("visor", "#C9C7BE", rug=0.5, sucio=0.3, z_suelo=1.0),
        Mat("boton", "#2A2C2F", rug=0.5),
        Mat("led_verde", "#30E060", rug=0.3, emision=("#30FF70", 1.0)),
        Mat("led_rojo", "#E02020", rug=0.3, emision=("#FF2020", 1.0)),
        Mat("contador", "#B9BCB8", rug=0.5, sucio=0.35, chorretones=0.4),
        Mat("maneta_roja", "#C0221C", rug=0.4, bordes=0.4),
        Mat("manguera", "#2E7A34", rug=0.55, sucio=0.4),
        Mat("barandilla", "#E2B214", rug=0.45, bordes=0.7, color_bordes="#7E8387", oxido=0.1),
        Mat("contenedor_naranja", "#B65A27", rug=0.55, sucio=0.55, oxido=0.3, bordes=0.6, rayas=0.5, z_rayas=0.9),
        Mat("contenedor_azul", "#2D6685", rug=0.5, sucio=0.45, oxido=0.22, bordes=0.6, rayas=0.4, z_rayas=2.0),
        Mat("contenedor_marco", "#34393D", rug=0.5, metal=0.4, bordes=0.6, oxido=0.3),
        Mat("contenedor_canto", "#4A4F52", rug=0.5, metal=0.6, oxido=0.45, bordes=0.7),
        Mat("contenedor_interior", "#4C5153", rug=0.7, sucio=0.5),
        Mat("paja", "#C4A86A", rug=0.95, relieve=("ruido", 0.03, 0.03), ruido=0.2, escala_ruido=8.0),
        Mat("carton", "#B48B58", rug=0.85, ruido=0.08, sucio=0.15),
        Mat("carton_oscuro", "#9A7448", rug=0.85, ruido=0.08),
        Mat("cinta", "#D2BE8E", rug=0.4),
        Mat("film", "#C7CCCF", rug=0.25, ruido=0.15, escala_ruido=3.0),
        Mat("saco", "#CFC3A3", rug=0.95, relieve=("ruido", 0.05, 0.02), ruido=0.1),
        Mat("caja_madera", "#9C7A50", rug=0.8, veta="x", bordes=0.3, color_bordes="#C9A87A"),
        Mat("madera_palet", "#A88A60", rug=0.85, veta="x", bordes=0.6, color_bordes="#C8AE82", sucio=0.3, z_suelo=1.0),
        Mat("madera_palet_y", "#A28459", rug=0.85, veta="y", bordes=0.6, color_bordes="#C8AE82"),
        Mat("madera_palet_oscura", "#856A48", rug=0.9, veta="z", bordes=0.5, color_bordes="#B2966C"),
        Mat("clavo", "#55595C", rug=0.4, metal=0.9, oxido=0.4),
        Mat("transpaleta", "#C9441B", rug=0.45, bordes=0.75, color_bordes="#7D8185", sucio=0.4, z_suelo=1.0),
        Mat("transpaleta_horquilla", "#C9441B", rug=0.5, bordes=0.9, color_bordes="#8A8E91", rayas=1.0, z_rayas=1.2,
            sucio=0.5, z_suelo=1.0),
        Mat("bidon_azul", "#28479A", rug=0.45, oxido=0.3, bordes=0.55, sucio=0.5, chorretones=0.3),
        Mat("bidon_gris", "#686D70", rug=0.5, metal=0.3, oxido=0.5, bordes=0.5, sucio=0.4),
        Mat("foco_carcasa", "#2F3439", rug=0.45, metal=0.4, bordes=0.4),
        Mat("sensor", "#E4E4DE", rug=0.3),
        Mat("neon_foco", D.NEON, rug=0.2, emision=(D.NEON, 1.0)),
        Mat("pantalla_bascula", "#06100F", rug=0.15),
        Mat("pantalla_contador", "#06100F", rug=0.15),
        # interior
        Mat("pared_oficina", "#CEC8B6", rug=0.8, sucio=0.25, z_suelo=1.0, ruido=0.05),
        Mat("linoleo", "#6F8078", rug=0.5, ruido=0.08, sucio=0.3, z_suelo=1.0),
        Mat("lampara_metal", "#D9D9D2", rug=0.4, metal=0.3),
        Mat("luz_fluorescente", "#FFF4DF", rug=0.2, emision=("#FFF1D6", 3.0)),
        Mat("luz_lampara", D.LUZ_CALIDA, rug=0.2, emision=(D.LUZ_CALIDA, 3.0)),
        Mat("mesa", "#C9BFA9", rug=0.5, ruido=0.05),
        Mat("mesa_metal", "#5B6670", rug=0.45, metal=0.4, bordes=0.4),
        Mat("papel", "#EEEBE2", rug=0.8),
        Mat("papel_escrito", "#E6E2D6", rug=0.8, relieve=("lamas", 0.02, 0.0), ruido=0.15, escala_ruido=40.0),
        Mat("libro_hojas", "#EFEADB", rug=0.8, ruido=0.1, escala_ruido=60.0),
        Mat("libro_tapa", "#6E1F1F", rug=0.6, bordes=0.4),
        Mat("taza", "#E8E4DA", rug=0.25),
        Mat("lampara", "#2E5E4E", rug=0.35, metal=0.3, bordes=0.3),
        Mat("silla", "#2A2F36", rug=0.7),
        Mat("estanteria", "#7E8A91", rug=0.45, metal=0.5, bordes=0.4),
        Mat("archivador_azul", "#2F4F8C", rug=0.5),
        Mat("archivador_rojo", "#9C2A26", rug=0.5),
        Mat("archivador_verde", "#2F6B3D", rug=0.5),
        Mat("corcho", "#A87E52", rug=0.95, relieve=("ruido", 0.02, 0.01), ruido=0.2, escala_ruido=30.0),
        Mat("rack_azul", "#24539A", rug=0.45, bordes=0.4),
        Mat("rack_naranja", "#E0731C", rug=0.45, bordes=0.4),
    ]
    return {m.nombre: m for m in P}


# --------------------------------------------------------------------------------------------------------------
# Imágenes de los calcos
# --------------------------------------------------------------------------------------------------------------


def _img_muelle(carpeta):
    """Suelo del muelle: franja amarilla en el canto, huellas de la transpaleta hacia el portón."""
    M = D.MUELLE
    ppx = 160
    w, h = int((M["x1"] - M["x0"]) * ppx), int((M["y1"] - M["y0"]) * ppx)
    rgba = np.zeros((h, w, 4), np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    ys = (h - 1 - yy) / ppx                                       # distancia al canto delantero (studs)
    xs = xx / ppx + M["x0"]
    n = I.ruido(w, h, ((10, 0.4), (60, 0.6)), 81)
    banda = (ys > 0.04) & (ys < 0.2)
    banda &= ~((xs > D.RAMPA["x0"] - 0.05) & (xs < D.RAMPA["x1"] + 0.05))
    a = banda * np.clip((n - 0.22) * 3, 0, 1) * 0.95
    rgba[..., :3] = np.where(banda[..., None], np.array(I._hex("#E2AE14")), 0)
    rgba[..., 3] = a
    # huellas de rodillos de la transpaleta (pares de líneas oscuras de la rampa al portón)
    alfa = np.zeros((h, w), np.float32)
    trazas = []
    for x0 in (0.7, 1.5, 2.3):
        for dx in (-0.2, 0.2):
            trazas.append(([(x0 + dx - M["x0"], h / ppx), (x0 + dx * 1.05 - M["x0"] + 0.1, 0.0)], 0.05, 0.35, 0))
    trazas.append(([(3.6 - M["x0"], 0.3), (3.9 - M["x0"], 1.0), (4.3 - M["x0"], 2.0)], 0.06, 0.25, 0))
    for pts, anc, inten, _ in trazas:
        capa = I._trazo(np.zeros((h, w), np.float32), pts, anc, 1.0, ppx)
        alfa = np.maximum(alfa, capa * inten)
    alfa = np.asarray(Image.fromarray((alfa * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(2)), np.float32) / 255
    alfa *= 0.5 + 0.5 * n
    oscuro = alfa > rgba[..., 3]
    rgba[..., :3] = np.where(oscuro[..., None], np.array((25, 23, 22)), rgba[..., :3])
    rgba[..., 3] = np.maximum(rgba[..., 3], alfa)
    rgba[..., 3] *= 255
    return I._guardar(rgba, carpeta, "muelle_marcas")


def generar_imagenes(carpeta):
    """Crea todas las imágenes. Devuelve {nombre: ruta} y {nombre: aspecto}."""
    rutas, asp = {}, {}

    def r(nombre, resultado):
        rutas[nombre], asp[nombre] = resultado

    amarillo, blanco, negro = "#F0C22E", "#E9E8E1", "#1E1E1E"
    r("rotulo_sector7b", I.rotulo(carpeta, "rotulo_sector7b", "SECTOR 7-B", amarillo, 240, desgaste=0.32,
                                  chorretones=0.7, semilla=2))
    r("rotulo_7b", I.rotulo(carpeta, "rotulo_7b", "7-B", blanco, 240, desgaste=0.3, semilla=3, chorretones=0.4))
    r("rotulo_lote114", I.rotulo(carpeta, "rotulo_lote114", "LOTE 7B-114", blanco, 160, fuente=I.MONO, desgaste=0.35,
                                 semilla=4))
    r("rotulo_lote209", I.rotulo(carpeta, "rotulo_lote209", "LOTE 7B-209", blanco, 160, fuente=I.MONO, desgaste=0.5,
                                 semilla=5))
    r("rotulo_lote031", I.rotulo(carpeta, "rotulo_lote031", "LOTE 7B-031", amarillo, 160, fuente=I.MONO,
                                 desgaste=0.4, semilla=6, chorretones=0.3))
    r("rotulo_muelle1", I.rotulo(carpeta, "rotulo_muelle1", "MUELLE 1", negro, 200, desgaste=0.35, semilla=7))
    r("rotulo_muelle2", I.rotulo(carpeta, "rotulo_muelle2", "MUELLE 2", negro, 200, desgaste=0.5, semilla=8))
    r("rotulo_sector7", I.rotulo(carpeta, "rotulo_sector7", "SECTOR 7", blanco, 180, desgaste=0.3, semilla=9))
    r("rotulo_id_inf", I.rotulo(carpeta, "rotulo_id_inf", "C7-0219", blanco, 140, fuente=I.MONO, desgaste=0.3,
                                semilla=10, plantilla=False))
    r("rotulo_id_sup", I.rotulo(carpeta, "rotulo_id_sup", "C7-0388", blanco, 140, fuente=I.MONO, desgaste=0.3,
                                semilla=11, plantilla=False))
    r("tiza_vacio", I.rotulo(carpeta, "tiza_vacio", "VACÍO", "#EDEDE8", 160, fuente=I.NORMAL, plantilla=False,
                             desgaste=0.55, semilla=12, pulverizado=False))
    r("cartel_oficina", I.cartel(carpeta, "cartel_oficina", [("OFICINA", 0.7, I.NEGRITA)], "#1F3F66", "#F2F2EC",
                                 1024, 267, borde="#F2F2EC"))
    r("cartel_horario", I.cartel(carpeta, "cartel_horario", [("HORARIO DE RECEPCIÓN", 0.2, I.NEGRITA),
                                                             ("06:00 - 20:00", 0.36, I.MONO),
                                                             ("ALMACÉN GENERAL · SECTOR 7-B", 0.12, I.NORMAL)],
                                 "#E9E6DC", "#1B2B3A", 1024, 730, borde="#1B2B3A"))
    r("cartel_extintor", I.cartel(carpeta, "cartel_extintor", [("EXTINTOR", 0.22, I.NEGRITA), ("▼", 0.45, I.NEGRITA)],
                                  "#C21E1E", "#F4F4F0", 512, 512, borde="#F4F4F0", tornillos=False))
    r("etiqueta_extintor", I.cartel(carpeta, "etiqueta_extintor", [("EXTINTOR", 0.17, I.NEGRITA),
                                                                   ("POLVO ABC", 0.15, I.NEGRITA), ("6 kg", 0.2, I.NEGRITA),
                                                                   ("REVISADO 03/2186", 0.09, I.NORMAL)],
                                    "#EDEDE6", "#222222", 512, 670, tornillos=False))
    r("pantalla_bascula", I.pantalla_7seg(carpeta, "pantalla_bascula", "0000.0", D.NEON, 512, 168, sufijo="kg"))
    r("pantalla_contador", I.pantalla_7seg(carpeta, "pantalla_contador", "04217", D.NEON, 512, 188, sufijo="kWh"))
    r("senal_zona_carga", I.flecha_zona_carga(carpeta))
    r("etiqueta_fragil", I.etiqueta_fragil(carpeta))
    r("etiqueta_envio", I.etiqueta_envio(carpeta))
    # aviso eléctrico: triángulo amarillo con el rayo
    w = 512
    im = Image.new("RGBA", (w, int(w * 0.9)), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.polygon([(w / 2, 10), (w - 10, w * 0.9 - 10), (10, w * 0.9 - 10)], fill=(20, 20, 20, 255))
    d.polygon([(w / 2, 50), (w - 50, w * 0.9 - 32), (50, w * 0.9 - 32)], fill=(242, 190, 20, 255))
    d.polygon([(w * 0.55, 150), (w * 0.38, 310), (w * 0.5, 310), (w * 0.42, 420), (w * 0.64, 250), (w * 0.52, 250),
               (w * 0.6, 150)], fill=(20, 20, 20, 255))
    p = os.path.join(carpeta, "aviso_electrico.png")
    im.save(p)
    rutas["aviso_electrico"], asp["aviso_electrico"] = p, 1 / 0.9
    r("relieve_lagrimada", I.chapa_lagrimada(carpeta))

    # suelo exterior (explanada): rodadas de camión que llegan a la zona de los topes y huellas de la rampa
    E, M = D.EXPLANADA, D.MUELLE
    W, H = E["x1"] - E["x0"], M["y0"] - E["y0"]

    def im_xy(x, y):  # mundo -> studs de la imagen (fila 0 = borde del muelle)
        return (x - E["x0"], M["y0"] - y)

    trazas = []
    for xc in (3.85, 5.55):           # ruedas traseras de un camión que entra marcha atrás
        for dx in (-0.14, 0.14):      # rueda gemela
            p0, p3 = im_xy(xc + dx - 4.6, -8.95), im_xy(xc + dx, -4.6)
            p1, p2 = im_xy(xc + dx - 4.0, -6.8), im_xy(xc + dx, -6.2)
            trazas.append((I._bezier(p0, p1, p2, p3), 0.2, 0.55, 1))
    for xc in (3.4, 6.0):             # marcas viejas, más claras
        p0, p3 = im_xy(xc + 2.0, -8.95), im_xy(xc, -4.8)
        trazas.append((I._bezier(p0, im_xy(xc + 1.5, -6.5), im_xy(xc, -6.3), p3), 0.22, 0.25, 1))
    for xc in (0.8, 2.0):             # transpaleta bajando por la rampa
        for dx in (-0.2, 0.2):
            p0 = im_xy(xc + dx, -6.75)
            trazas.append((I._bezier(p0, im_xy(xc + dx, -7.3), im_xy(xc + dx - 1.0, -7.9), im_xy(xc + dx - 2.6, -8.3)),
                           0.05, 0.4, 0))
    r("explanada_rodadas", I.rodadas(carpeta, "explanada_rodadas", W, H, trazas, px_por_stud=110))
    hx, hy = im_xy(D.HUNDIDO["x"], D.HUNDIDO["y"])
    r("explanada_charco", I.manchas(carpeta, "explanada_charco", W, H,
                                    [(hx, hy, 0.75, 0.85, (0, 0, 0)), (hx + 0.7, hy - 0.25, 0.35, 0.7, (0, 0, 0))]))
    r("explanada_manchas", I.manchas(carpeta, "explanada_manchas", W, H,
                                     [(hx - 0.2, hy - 0.6, 0.5, 0.7, (18, 16, 14)), (hx + 0.6, hy + 0.5, 0.3, 0.6, (20, 18, 15)),
                                      (im_xy(-3.0, -6.0)[0], im_xy(-3.0, -6.0)[1], 0.7, 0.25, (70, 60, 50)),
                                      (im_xy(6.9, -4.7)[0], im_xy(6.9, -4.7)[1], 0.5, 0.45, (95, 60, 35))]))
    r("explanada_aranazos", I.aranazos(carpeta, "explanada_aranazos", W, H,
                                       [(im_xy(4.2, -4.7) + im_xy(4.8, -7.5) + (14, 0.25)),
                                        (im_xy(1.0, -6.9) + im_xy(-1.0, -8.6) + (8, 0.3))], px_por_stud=110))
    # rampa (de arriba): huellas que bajan
    trazas = [([(x + dx, 0.0), (x + dx * 1.1, 2.4)], 0.05, 0.45, 0) for x in (0.8, 2.0) for dx in (-0.2, 0.2)]
    trazas.append(([(1.4, 0.0), (1.45, 2.4)], 0.5, 0.18, 0))
    r("rampa_rodadas", I.rodadas(carpeta, "rampa_rodadas", D.RAMPA["x1"] - D.RAMPA["x0"], 2.4, trazas, px_por_stud=120))
    # muelle
    rutas["muelle_marcas"] = _img_muelle(carpeta)
    asp["muelle_marcas"] = (M["x1"] - M["x0"]) / (M["y1"] - M["y0"])
    WM, HM = M["x1"] - M["x0"], M["y1"] - M["y0"]
    r("muelle_aranazos", I.aranazos(carpeta, "muelle_aranazos", WM, HM,
                                    [(0.0 - M["x0"], 0.05, 0.2 - M["x0"], 1.95, 18, 0.5),
                                     (2.7 - M["x0"], 0.05, 2.9 - M["x0"], 1.95, 12, 0.35),
                                     (4.0 - M["x0"], 0.3, 5.8 - M["x0"], 1.6, 6, 0.2)], px_por_stud=150))
    r("muelle_manchas", I.manchas(carpeta, "muelle_manchas", WM, HM,
                                  [(4.6 - M["x0"], 1.0, 0.35, 0.55, (25, 22, 20)), (1.1 - M["x0"], 0.6, 0.25, 0.4, (30, 26, 22)),
                                   (-1.95 - M["x0"], 0.3, 0.4, 0.3, (60, 52, 44))]))
    R = D.REPISA_TRASERA
    r("trasera_manchas", I.manchas(carpeta, "trasera_manchas", R["x1"] - R["x0"], R["y1"] - D.Y1,
                                   [(1.5, 0.5, 0.5, 0.5, (40, 34, 28)), (2.9, 0.8, 0.3, 0.6, (90, 55, 30))]))
    # suelo interior: líneas de pasillo
    x0i, y1i = -1.1, D.Y1 - D.GROSOR_MURO
    rects = [(3.6 - x0i * 0 - x0i - 3.6 + 0.2, y1i - 4.7, 7.2, y1i - 3.65, 0.08),       # frente de las estanterías
             (0.35, y1i - 3.4, 3.7, y1i + 2.2 - 0.05, 0.06),                           # pasillo del portón
             (4.2, y1i - 3.3, 7.1, y1i - 0.6 - 1.2, 0.06)]
    rects = [(0.25, 0.15, 7.15, 1.05, 0.08), (0.3, 1.6, 4.6, 6.9, 0.07), (5.0, 2.4, 7.1, 4.4, 0.06)]
    r("suelo_marcas", I.marcas_suelo_interior(carpeta, "suelo_marcas", 7.4, 7.06, rects))
    return rutas, asp


# --------------------------------------------------------------------------------------------------------------
# Escena, objetos, sombreado
# --------------------------------------------------------------------------------------------------------------


def escena():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scn = bpy.context.scene
    scn.unit_settings.system = "NONE"     # 1 unidad = 1 stud
    scn.unit_settings.scale_length = 1.0
    scn.world = bpy.data.worlds.new("mundo")
    scn.render.engine = "CYCLES"
    scn.cycles.device = "CPU"
    return scn


APOYOS = (0.0, D.S, D.Z_SUELO, D.Z_SUELO + 0.012, D.Z_SUELO + 0.01)


def crear_objetos(obra, mats_blender):
    objs = {}
    for nombre in modelo.PIEZAS:
        malla = obra.m[nombre]
        origen = None
        if nombre == "almacen_porton":
            origen = obra.anclajes["porton"]["pivote"]
        elif nombre == "almacen_porton_trasero":
            origen = obra.anclajes["porton_trasero"]["pivote"]
        elif nombre == "almacen_puerta":
            origen = obra.anclajes["puerta"]["pivote"]
        objs[nombre] = malla.objeto(mats_blender, origen=origen, quitar_apoyos=APOYOS)
    for o in objs.values():
        sombreado(o)
    return objs


def sombreado(obj, angulo=35):
    for p in obj.data.polygons:
        p.use_smooth = True
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_auto_smooth(angle=math.radians(angulo))
    for mod in list(obj.modifiers):
        bpy.ops.object.modifier_apply(modifier=mod.name)


# --------------------------------------------------------------------------------------------------------------
# UV del atlas
# --------------------------------------------------------------------------------------------------------------

AMPLIAR = {"cartel_oficina", "cartel_horario", "cartel_extintor", "senal", "pantalla_bascula", "pantalla_contador",
           "visor", "contador", "extintor_rojo"}
MATS_INTERIOR = {"chapa_interior", "tejado_interior", "pared_oficina", "contenedor_interior", "rack_azul",
                 "rack_naranja", "film", "saco", "suelo_interior"}


def desplegar_atlas(objs):
    lista = list(objs.values())
    bpy.ops.object.select_all(action="DESELECT")
    for o in lista:
        o.select_set(True)
    bpy.context.view_layer.objects.active = lista[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, area_weight=0.0, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    # caras que no se ven (apoyadas en el suelo) o de interior: menos resolución
    for o in lista:
        me = o.data
        uv = me.uv_layers.active.data
        mw = o.matrix_world
        for p in me.polygons:
            c = mw @ p.center
            n = (mw.to_3x3() @ p.normal).normalized()
            mat = me.materials[p.material_index].name if me.materials else ""
            esc = 1.0
            if o.name == "almacen_neon" or mat in AMPLIAR:
                esc = 3.0
            elif n.z < -0.9 and c.z < 1.12:
                esc = 0.12
            elif mat == "hormigon_explanada" and n.z > 0.5 and modelo.tapado_explanada(c.x, c.y):
                esc = 0.03
            elif mat == "suelo_interior" and abs(n.z) < 0.5:
                esc = 0.05
            elif mat in MATS_INTERIOR:
                esc = 0.4
            elif mat == "hormigon_explanada":
                esc = 0.6
            elif mat == "tejado":
                esc = 0.8
            if esc != 1.0:
                idx = list(p.loop_indices)
                cu = sum((uv[i].uv for i in idx), Vector((0, 0))) / len(idx)
                for i in idx:
                    uv[i].uv = cu + (uv[i].uv - cu) * esc
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.context.scene.tool_settings.use_uv_select_sync = True
    r = bpy.ops.uv.pack_islands(rotate=True, margin=0.0015, margin_method="FRACTION", shape_method="CONCAVE",
                                scale=True)
    print("[uv] empaquetado:", r)
    bpy.ops.object.mode_set(mode="OBJECT")
    # densidad de texels (de las caras a resolución completa: paredes, atrezo)
    area3, areauv = 0.0, 0.0
    completas = MATS_INTERIOR | {"hormigon_explanada", "tejado"}
    for o in lista:
        me = o.data
        uv = me.uv_layers.active.data
        for p in me.polygons:
            if (me.materials[p.material_index].name in completas) or (p.normal.z < -0.9):
                continue
            area3 += p.area
            pts = [uv[i].uv for i in p.loop_indices]
            a = 0.0
            for k in range(1, len(pts) - 1):
                a += abs((pts[k] - pts[0]).cross(pts[k + 1] - pts[0])) / 2
            areauv += a
    return areauv, area3


# --------------------------------------------------------------------------------------------------------------
# Horneado
# --------------------------------------------------------------------------------------------------------------


def hornear(objs, tam, muestras_ao, rapido):
    scn = bpy.context.scene
    lista = list(objs.values())
    imgs = {}
    for nombre, color in (("color", True), ("rugosidad", False), ("metal", False), ("emision", True),
                          ("alfa", False), ("normal", False), ("ao", False)):
        img = bpy.data.images.new(f"atlas_{nombre}", tam, tam, alpha=False, float_buffer=False)
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        imgs[nombre] = img

    def destino(img):
        for r in MT.REGISTRO.values():
            nt = r["mat"].node_tree
            n = nt.nodes.get("destino") or nt.nodes.new("ShaderNodeTexImage")
            n.name = "destino"
            n.image = img
            nt.nodes.active = n

    def ejecutar(tipo, **kw):
        bpy.ops.object.select_all(action="DESELECT")
        for o in lista:
            o.select_set(True)
        bpy.context.view_layer.objects.active = lista[0]
        bpy.ops.object.bake(type=tipo, margin=3, margin_type="EXTEND", use_clear=True, **kw)

    for modo in ("color", "rugosidad", "metal", "emision", "alfa"):
        t = time.time()
        MT.modo_salida(modo)
        scn.cycles.samples = 1 if rapido else 6
        destino(imgs[modo])
        ejecutar("EMIT")
        print(f"[horneado] {modo}: {time.time() - t:.0f} s", flush=True)
    MT.modo_salida("render")
    t = time.time()
    scn.cycles.samples = 1 if rapido else 8
    destino(imgs["normal"])
    ejecutar("NORMAL", normal_space="TANGENT")
    print(f"[horneado] normal: {time.time() - t:.0f} s", flush=True)
    t = time.time()
    scn.cycles.samples = muestras_ao
    scn.world.light_settings.distance = 0.9
    destino(imgs["ao"])
    ejecutar("AO")
    print(f"[horneado] ao: {time.time() - t:.0f} s", flush=True)
    return imgs


def _px(img):
    w, h = img.size
    a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
    return a[::-1]  # fila 0 arriba (como el PNG)


def guardar_texturas(imgs, carpeta):
    col = _px(imgs["color"])[..., :3]
    ao = _px(imgs["ao"])[..., 0:1]
    alfa = _px(imgs["alfa"])[..., 0]
    factor = 1.0 - 0.7 * (1.0 - np.clip(ao, 0, 1)) ** 1.4
    # la oclusión no oscurece lo que emite luz
    emi = _px(imgs["emision"])[..., :3]
    emite = np.clip(emi.max(axis=2, keepdims=True) * 3, 0, 1)
    col = col * (factor * (1 - emite) + emite)
    rgba = np.concatenate([col, alfa[..., None]], axis=2)
    rutas = {}

    def guardar(nombre, arr, modo):
        ruta = os.path.join(carpeta, f"{NOMBRE}_{nombre}.png")
        Image.fromarray((np.clip(arr, 0, 1) * 255 + 0.5).astype(np.uint8), modo).save(ruta, optimize=True)
        rutas[nombre] = ruta

    guardar("color", rgba, "RGBA")
    guardar("normal", _px(imgs["normal"])[..., :3], "RGB")
    guardar("roughness", _px(imgs["rugosidad"])[..., 0], "L")
    guardar("metalness", _px(imgs["metal"])[..., 0], "L")
    guardar("emision", emi, "RGB")
    return rutas


def materiales_finales(objs, rutas):
    """Un material por pieza con el atlas (lo que se exporta y lo que se ve en los renders)."""
    cargadas = {}
    for k, ruta in rutas.items():
        img = bpy.data.images.load(ruta, check_existing=True)
        img.colorspace_settings.name = "sRGB" if k in ("color", "emision") else "Non-Color"
        cargadas[k] = img
    for nombre, obj in objs.items():
        mat = bpy.data.materials.new(f"{nombre}_atlas")
        mat.use_nodes = True
        nt = mat.node_tree
        b = nt.nodes["Principled BSDF"]

        def tex(k):
            n = nt.nodes.new("ShaderNodeTexImage")
            n.image = cargadas[k]
            return n

        tc = tex("color")
        nt.links.new(tc.outputs["Color"], b.inputs["Base Color"])
        if nombre in ("almacen_cristal", "almacen_puerta"):
            nt.links.new(tc.outputs["Alpha"], b.inputs["Alpha"])
        nt.links.new(tex("roughness").outputs["Color"], b.inputs["Roughness"])
        nt.links.new(tex("metalness").outputs["Color"], b.inputs["Metallic"])
        nt.links.new(tex("emision").outputs["Color"], b.inputs["Emission Color"])
        b.inputs["Emission Strength"].default_value = 6.0 if nombre == "almacen_neon" else 3.0
        tn = tex("normal")
        nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
        nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
        obj.data.materials.clear()
        obj.data.materials.append(mat)
        for p in obj.data.polygons:
            p.material_index = 0


# --------------------------------------------------------------------------------------------------------------
# Render: estudio de exterior (sol + cielo) y hojas
# --------------------------------------------------------------------------------------------------------------


def estudio(noche=False):
    scn = bpy.context.scene
    scn.view_settings.view_transform = "AgX"
    scn.view_settings.look = "AgX - Medium High Contrast"
    scn.world.use_nodes = True
    nt = scn.world.node_tree
    fondo = nt.nodes["Background"]
    # cielo: degradado por la altura de la dirección de la vista
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    rampa.color_ramp.elements[0].position = 0.45
    rampa.color_ramp.elements[0].color = (0.42, 0.45, 0.48, 1)
    rampa.color_ramp.elements[1].position = 1.0
    rampa.color_ramp.elements[1].color = (0.26, 0.42, 0.72, 1)
    nt.links.new(sep.outputs["Z"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], fondo.inputs["Color"])
    fondo.inputs["Strength"].default_value = 0.9
    sol = bpy.data.lights.new("sol", "SUN")
    sol.energy = 4.2
    sol.angle = math.radians(2.5)
    sol.color = (1.0, 0.96, 0.9)
    o = bpy.data.objects.new("sol", sol)
    o.rotation_euler = (math.radians(48), 0, math.radians(-38))
    scn.collection.objects.link(o)
    # suelo de alrededor (tierra compactada)
    bpy.ops.mesh.primitive_plane_add(size=400, location=(0, 0, 0.001))
    s = bpy.context.active_object
    s.name = "suelo_estudio"
    m = bpy.data.materials.new("suelo_estudio")
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.16, 0.15, 0.12, 1)
    b.inputs["Roughness"].default_value = 1.0
    s.data.materials.append(m)
    s["estudio"] = True
    return scn


def luces_render(obra):
    """Las PointLight que el json propone para Studio (oficina y lámpara), para que el render se vea como en el juego."""
    an = obra.anclajes
    for nombre, pos, energia, color in (("LuzOficina", an["LuzOficina"], 25, (1.0, 0.93, 0.82)),
                                        ("LuzLampara", an["LuzLampara"], 6, (1.0, 0.82, 0.6))):
        d = bpy.data.lights.new(nombre, "POINT")
        d.energy = energia
        d.color = color
        d.shadow_soft_size = 0.1
        o = bpy.data.objects.new(nombre, d)
        o.location = pos
        bpy.context.scene.collection.objects.link(o)


def camara(nombre="cam", lente=40):
    d = bpy.data.cameras.new(nombre)
    d.lens = lente
    d.clip_start = 0.05
    d.clip_end = 1000
    o = bpy.data.objects.new(nombre, d)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.scene.camera = o
    return o


def render(cam, pos, mira, ruta, tam, muestras, lente=40, ancho=None):
    scn = bpy.context.scene
    scn.render.resolution_x = ancho or tam
    scn.render.resolution_y = tam
    scn.cycles.samples = muestras
    scn.cycles.use_denoising = True
    cam.data.lens = lente
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(mira) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()
    scn.render.filepath = ruta
    bpy.ops.render.render(write_still=True)
    return ruta


def orbita(az, el, dist, centro):
    a, e = math.radians(az), math.radians(el)
    c = Vector(centro)
    return c + Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e))) * dist


def estado_abierto(objs, abierto):
    """Persianas enrolladas (encogidas hacia su eje, como se hará en Roblox) y puerta abierta 80°."""
    for n in ("almacen_porton", "almacen_porton_trasero"):
        objs[n].scale = (1, 1, 0.07 if abierto else 1)
    objs["almacen_puerta"].rotation_euler = (0, 0, math.radians(80) if abierto else 0)


def hoja(rutas, salida, titulo, notas, columnas=4):
    tam = Image.open(rutas[0][1]).size
    filas = math.ceil(len(rutas) / columnas)
    cab = 70 + 22 * len(notas)
    W, H = columnas * tam[0], cab + filas * tam[1]
    h = Image.new("RGB", (W, H), (16, 18, 24))
    d = ImageDraw.Draw(h)
    d.text((16, 12), titulo, fill=(255, 214, 102), font=ImageFont.truetype(I.NEGRITA, 30))
    for k, n in enumerate(notas):
        d.text((18, 54 + k * 22), n, fill=(210, 214, 224), font=ImageFont.truetype(I.NORMAL, 17))
    for k, (nombre, ruta) in enumerate(rutas):
        x, y = (k % columnas) * tam[0], cab + (k // columnas) * tam[1]
        h.paste(Image.open(ruta).convert("RGB"), (x, y))
        d.rectangle((x, y, x + tam[0] - 1, y + tam[1] - 1), outline=(40, 44, 56))
        d.text((x + 12, y + 10), nombre, fill=(255, 255, 255), font=ImageFont.truetype(I.NEGRITA, 20))
    h.save(salida)
    print("[ok] hoja:", salida)


VISTAS = [  # nombre, azimut (0 = de frente), elevación, distancia, centro, lente, ¿abierto?
    ("Frente", 0, 8, 30, (0, -1.5, 3.0), 40, False),
    ("3/4 delantera derecha", 38, 20, 30, (0, -1.0, 2.8), 40, False),
    ("Lateral derecho", 90, 8, 28, (0, 0.5, 3.0), 40, False),
    ("3/4 trasera derecha", 140, 22, 30, (0, 1.0, 2.8), 40, False),
    ("Detrás", 180, 8, 30, (0, 1.5, 3.0), 40, False),
    ("3/4 trasera izquierda", -138, 20, 30, (-1, 1.0, 2.8), 40, False),
    ("Lateral izquierdo", -90, 8, 28, (-1.0, 0.0, 3.0), 40, False),
    ("3/4 delantera izquierda, abierto", -35, 24, 30, (-0.5, -1.0, 2.6), 40, True),
]

DETALLES = [  # nombre, posición cámara, mira, lente, abierto
    ("Muelle: báscula, extintor, puerta, horario", (-3.0, -9.0, 2.9), (-2.8, -3.0, 2.0), 40, False),
    ("Ventana de oficina (mesa, lámpara, estantería)", (-4.3, -4.7, 2.85), (-4.3, -0.6, 1.75), 42, False),
    ("Portón: tambor, cadena, guías, lamas", (4.8, -7.4, 4.6), (1.4, -2.7, 4.0), 32, False),
    ("Rampa, topes, transpaleta y palé", (7.6, -8.2, 2.6), (3.2, -3.8, 0.8), 36, False),
    ("Contenedores y bidones", (-11.5, -3.4, 2.6), (-7.6, 1.4, 1.2), 34, False),
    ("Pared derecha: contador, grifo, manguera", (11.5, -3.2, 2.2), (6.6, 1.4, 1.8), 34, False),
    ("Abierto: interior por el portón", (1.4, -9.5, 2.0), (1.4, 2.0, 2.0), 36, True),
    ("Arriba: tejado y tragaluces", (6.0, -14.0, 22.0), (0, 0.8, 3.0), 36, False),
]


def renderizar(objs, carpeta_tmp, tam, muestras, sufijo, malla=True):
    cam = camara()
    os.makedirs(carpeta_tmp, exist_ok=True)
    vistas, detalles = [], []
    for k, (nombre, az, el, dist, centro, lente, abierto) in enumerate(VISTAS):
        estado_abierto(objs, abierto)
        ruta = os.path.join(carpeta_tmp, f"v{k}{sufijo}.png")
        render(cam, orbita(az, el, dist, centro), centro, ruta, tam, muestras, lente)
        vistas.append((nombre, ruta))
    for k, (nombre, pos, mira, lente, abierto) in enumerate(DETALLES):
        estado_abierto(objs, abierto)
        ruta = os.path.join(carpeta_tmp, f"d{k}{sufijo}.png")
        render(cam, pos, mira, ruta, tam, muestras, lente)
        detalles.append((nombre, ruta))
    estado_abierto(objs, False)
    return vistas, detalles


def vista_malla(objs, carpeta_tmp, tam, sufijo):
    """Vista de alambre para revisar la topología."""
    scn = bpy.context.scene
    m = bpy.data.materials.new("vista_malla")
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    wire = nt.nodes.new("ShaderNodeWireframe")
    wire.use_pixel_size = True
    wire.inputs["Size"].default_value = 0.8
    base = nt.nodes.new("ShaderNodeBsdfDiffuse")
    base.inputs["Color"].default_value = (0.45, 0.47, 0.52, 1)
    lin = nt.nodes.new("ShaderNodeEmission")
    lin.inputs["Color"].default_value = (0.2, 0.85, 1.0, 1)
    lin.inputs["Strength"].default_value = 1.5
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(wire.outputs["Fac"], mix.inputs["Fac"])
    nt.links.new(base.outputs["BSDF"], mix.inputs[1])
    nt.links.new(lin.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    scn.view_layers[0].material_override = m
    suelo = bpy.data.objects.get("suelo_estudio")
    suelo.hide_render = True
    cam = scn.camera
    ruta = os.path.join(carpeta_tmp, f"malla{sufijo}.png")
    render(cam, orbita(38, 22, 30, (0, -1, 2.8)), (0, -1, 2.8), ruta, tam, 8, 40)
    scn.view_layers[0].material_override = None
    suelo.hide_render = False
    return ruta


# --------------------------------------------------------------------------------------------------------------
# Exportación
# --------------------------------------------------------------------------------------------------------------

C_ROBLOX = Matrix(((1, 0, 0), (0, 0, 1), (0, -1, 0)))   # Blender (tras el giro) -> Roblox (x, z, -y)
GIRO = Matrix.Rotation(math.pi, 4, "Z")                 # GIRO_IMPORTACION: 180° sobre el eje vertical


def a_roblox(p):
    """
    Punto de trabajo (Blender, antes del giro) -> dónde queda en Studio. El FBX lleva el GIRO (180°) y el importador
    de Roblox gira otros 180° (comprobado con la región 1): se anulan, y en Studio queda (x, z, -y) del punto de trabajo.
    """
    return [round(v, 3) for v in (C_ROBLOX @ Vector(p))]


def exportar(objs, ruta):
    lista = list(objs.values())
    for o in lista:
        o.scale = (1, 1, 1)
        o.rotation_euler = (0, 0, 0)
        o.matrix_world = GIRO @ o.matrix_world
    bpy.ops.object.select_all(action="DESELECT")
    for o in lista:
        o.select_set(True)
    bpy.context.view_layer.objects.active = lista[0]
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.ops.export_scene.fbx(
        filepath=ruta, use_selection=True, object_types={"MESH"}, global_scale=1.0, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL", bake_space_transform=True, axis_forward="-Z", axis_up="Y",
        use_mesh_modifiers=True, mesh_smooth_type="FACE", use_tspace=True, add_leaf_bones=False, bake_anim=False,
        embed_textures=True, path_mode="COPY")
    print("[ok] FBX:", ruta)


def verificar_fbx(ruta):
    """Reimporta el FBX en una escena vacía y devuelve {malla: (triángulos, tamaño, centro)}."""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=ruta)
    res = {}
    for o in bpy.data.objects:
        if o.type != "MESH":
            continue
        dep = bpy.context.evaluated_depsgraph_get()
        mn = Vector((1e9,) * 3)
        mx = Vector((-1e9,) * 3)
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            mn = Vector(map(min, mn, w))
            mx = Vector(map(max, mx, w))
        res[o.name] = dict(triangulos=sum(len(p.vertices) - 2 for p in o.data.polygons),
                           tam=[round(v, 3) for v in (mx - mn)], uv=len(o.data.uv_layers),
                           escala_objeto=[round(v, 4) for v in o.scale])
    return res


# --------------------------------------------------------------------------------------------------------------


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vista-previa", action="store_true")
    ap.add_argument("--rapido", action="store_true")
    ap.add_argument("--contar", action="store_true", help="solo construir y contar triángulos")
    ap.add_argument("--solo-json", action="store_true", help="solo reescribir almacen.json")
    a = ap.parse_args()
    t0 = time.time()
    tmp = os.path.join(SALIDA, "_tmp")
    os.makedirs(tmp, exist_ok=True)
    rutas_img, asp = generar_imagenes(os.path.join(tmp, "calcos"))
    scn = escena()
    imgs_blender = {}
    for n, ruta in rutas_img.items():
        img = bpy.data.images.load(ruta)
        if n.startswith("relieve"):
            img.colorspace_settings.name = "Non-Color"
        imgs_blender[n] = img
    obra = modelo.construir(asp)
    pal = paleta()
    usados = set()
    for m in obra.m.values():
        usados |= set(m.mats)
    faltan = usados - set(pal)
    assert not faltan, f"materiales sin definir: {faltan}"
    for nombre, cals in obra.calcos.items():
        pal[nombre].calcos = cals
    mats_blender = {n: MT.construir(pal[n], imgs_blender) for n in usados}
    objs = crear_objetos(obra, mats_blender)
    total = 0
    resumen = {}
    for n, o in objs.items():
        tr = triangulos(o)
        comp, malas = volumen_firmado(o)
        total += tr
        resumen[n] = tr
        print(f"[malla] {n}: {tr} triángulos, {comp} piezas, {malas} con normales hacia dentro")
    print(f"[malla] TOTAL {total} triángulos (presupuesto {PRESUPUESTO})")
    if a.contar:
        import collections
        pm = collections.Counter()
        for o in objs.values():
            for p in o.data.polygons:
                pm[o.data.materials[p.material_index].name] += len(p.vertices) - 2
        print(pm.most_common(40))
        return
    if a.solo_json:
        mn, mx, cajas = medir(objs)
        dens = json.load(open(os.path.join(SALIDA, f"{NOMBRE}.json")))["texturas"]["densidad_px_stud"]
        escribir_json(obra, resumen, total, mn, mx, cajas, dens, 2048)
        return
    estudio()
    if a.vista_previa:
        sufijo = "_previa"
        vistas, detalles = renderizar(objs, os.path.join(tmp, "render"), 520, 24, sufijo)
        hoja(vistas, os.path.join(tmp, "previa_vistas.png"), f"Almacén — vista previa ({total} tri)", [])
        hoja(detalles, os.path.join(tmp, "previa_detalles.png"), "Almacén — detalles (vista previa)", [])
        print(f"[ok] vista previa en {time.time() - t0:.0f} s")
        return

    luces_render(obra)
    tam = 512 if a.rapido else 2048
    areauv, area3 = desplegar_atlas(objs)
    densidad = tam * math.sqrt(areauv / area3)
    print(f"[uv] ocupación {areauv * 100:.1f} %, {densidad:.0f} px/stud de media")
    imgs = hornear(objs, tam, 8 if a.rapido else 48, a.rapido)
    rutas_tex = guardar_texturas(imgs, SALIDA)
    materiales_finales(objs, rutas_tex)

    tam_r, mu = (360, 16) if a.rapido else (900, 96)
    vistas, detalles = renderizar(objs, os.path.join(tmp, "render"), tam_r, mu, "")
    ruta_malla = vista_malla(objs, os.path.join(tmp, "render"), tam_r, "")
    notas = [f"{total} triángulos (presupuesto {PRESUPUESTO}) · atlas {tam}×{tam}: color, normal, rugosidad, metal, emisión"
             f" · 1 stud = 1 unidad · {densidad:.0f} px/stud",
             "Piezas: almacen, almacen_porton, almacen_porton_trasero, almacen_puerta, almacen_cristal, almacen_neon"
             " · la última vista: persianas enrolladas y puerta abierta"]
    hoja(vistas, os.path.join(SALIDA, f"{NOMBRE}_turnaround.png"), "Almacén general del pueblo — turnaround", notas)
    hoja(detalles + [("Malla", ruta_malla)], os.path.join(SALIDA, f"{NOMBRE}_detalles.png"),
         "Almacén general del pueblo — detalles", notas[:1], columnas=3)

    mn, mx, cajas = medir(objs)
    ruta_fbx = os.path.join(SALIDA, f"{NOMBRE}.fbx")
    exportar(objs, ruta_fbx)
    escribir_json(obra, resumen, total, mn, mx, cajas, densidad, tam)
    comprobacion = verificar_fbx(ruta_fbx)
    print("[verificación FBX]", json.dumps(comprobacion, indent=1))
    with open(os.path.join(tmp, "verificacion_fbx.json"), "w") as f:
        json.dump(comprobacion, f, indent=1)
    print(f"[ok] todo en {time.time() - t0:.0f} s")


def medir(objs):
    """Caja de todo y de cada pieza (coordenadas de trabajo, antes del giro)."""
    mn = Vector((1e9,) * 3)
    mx = Vector((-1e9,) * 3)
    cajas = {}
    for n, o in objs.items():
        omn = Vector((1e9,) * 3)
        omx = Vector((-1e9,) * 3)
        for v in o.data.vertices:
            w = o.matrix_world @ v.co
            omn = Vector(map(min, omn, w))
            omx = Vector(map(max, omx, w))
        cajas[n] = (omn, omx)
        mn = Vector(map(min, mn, omn))
        mx = Vector(map(max, mx, omx))
    return mn, mx, cajas


def escribir_json(obra, resumen, total, mn, mx, cajas, densidad, tam):
    an = obra.anclajes

    def piv(p):
        return dict(blender=[round(v, 3) for v in p], roblox=a_roblox(p))

    datos = {
        "nombre": NOMBRE,
        "descripcion": "Almacén general del pueblo: nave de chapa grecada con tejado en arco, muelle de carga con "
                       "rampa abatible, portón enrollable principal y trasero, puerta de personal y oficina.",
        "unidades": "studs (1 unidad de Blender = 1 stud). A esta escala 1 stud ~ 1,1 m.",
        "ejes": {
            "trabajo": "Blender antes del giro: X ancho, Y fondo, Z arriba; la fachada (portón) mira a -Y; z = 0 en la base.",
            "giro_importacion": "Antes de exportar se gira 180° sobre el eje vertical (GIRO_IMPORTACION), para compensar el "
                                "giro de 180° que mete el importador 3D de Roblox (probado con la región 1).",
            "roblox": "Las coordenadas 'roblox' son dónde queda cada punto en Studio (contando el GIRO del FBX y el giro "
                      "del importador, que se anulan): (x, z, -y) de las coordenadas de trabajo, en studs, respecto al "
                      "centro de la base del almacén. La fachada del portón queda hacia +Z del modelo. Si en Studio sale "
                      "al revés, el importador no ha girado: girar el modelo 180° en Y.",
            "fbx": "FBX con 'Apply Scalings: FBX All', delante -Z, arriba Y, 'Apply Transform'. Importar con Scale Unit = Stud.",
        },
        "tamano_studs": {"ancho_x": round(mx.x - mn.x, 2), "fondo": round(mx.y - mn.y, 2), "alto": round(mx.z - mn.z, 2)},
        "edificio_studs": {"ancho": D.X1 - D.X0, "fondo": D.Y1 - D.Y0, "alero": D.Z_ALERO, "cumbre": D.Z_CUMBRE,
                           "suelo_interior_y_muelle": D.Z_SUELO, "zocalo": D.Z_ZOCALO},
        "triangulos": {"total": total, "presupuesto": PRESUPUESTO, **resumen},
        "texturas": {
            "tam": [tam, tam], "densidad_px_stud": round(densidad),
            "color": f"{NOMBRE}_color.png (RGBA: el alfa es la transparencia del cristal armado y del policarbonato)",
            "normal": f"{NOMBRE}_normal.png (espacio tangente, convención OpenGL +Y)",
            "roughness": f"{NOMBRE}_roughness.png", "metalness": f"{NOMBRE}_metalness.png",
            "emision": f"{NOMBRE}_emision.png",
            "nota": "Un solo atlas para las 6 mallas: todas usan las mismas texturas (una subida).",
        },
        "piezas": {},
        "animacion": {
            "porton": {"pivote": piv(an["porton"]["pivote"]), "alto": round(an["porton"]["alto"], 3),
                       "ancho": round(an["porton"]["ancho"], 3),
                       "como_abrir": "Enrollar = encoger Size.Y hasta ~0,07 del alto dejando fijo el borde de arriba "
                                     "(el pivote, a la altura del eje del tambor): CFrame sube (alto - alto_abierto)/2.",
                       "alto_abierto": 0.3},
            "porton_trasero": {"pivote": piv(an["porton_trasero"]["pivote"]), "alto": round(an["porton_trasero"]["alto"], 3),
                               "ancho": round(an["porton_trasero"]["ancho"], 3), "alto_abierto": 0.27},
            "puerta": {"pivote_bisagras": piv(an["puerta"]["pivote"]), "eje": "vertical (Y de Roblox)",
                       "abre": "hacia fuera, girando sobre las bisagras de su lado izquierdo (visto desde fuera); "
                               "abierta = 80-90°", "ancho": round(an["puerta"]["ancho"], 3)},
        },
        "luces": {k: {"posicion": piv(v["posicion"]), "direccion_roblox": a_roblox(Vector(v["direccion"]) +
                                                                                     Vector((0, 0, 0))) if False else
                      [round(c, 3) for c in (C_ROBLOX @ Vector(v["direccion"]))],
                      "color": v["color"], "tipo": "SpotLight", "sugerido": {"Brightness": 2, "Range": 18, "Angle": 70}}
                  for k, v in an["luces"].items()},
        "luces_calidas": {"LuzOficina": piv(an["LuzOficina"]), "LuzLampara": piv(an["LuzLampara"]),
                          "color": D.LUZ_CALIDA, "tipo": "PointLight (Brightness 0,8, Range 6)"},
        "otros_anclajes": {"contador": piv(an["contador"]), "grifo": piv(an["grifo"]),
                           "transpaleta": piv(an["transpaleta"]), "rampa_bisagra": piv(an["rampa"]["bisagra"]),
                           "sensor_movimiento": piv(an["luces"]["FocoSeguridad"]["sensor"])},
        "studio": {
            "almacen": "SurfaceAppearance con las 4 texturas (Color, Normal, Roughness, Metalness). Anchored. "
                       "Colisión: Box o Hull; para entrar por los portones, CollisionFidelity = PreciseConvexDecomposition.",
            "almacen_porton / almacen_porton_trasero": "Igual que el cuerpo; Anchored; tween de Size/CFrame (ver animacion).",
            "almacen_puerta": "SurfaceAppearance con AlphaMode = Transparency (la ventanilla es cristal armado). "
                              "Pivot en las bisagras (pivote_bisagras).",
            "almacen_cristal": "SurfaceAppearance con AlphaMode = Transparency, CastShadow desactivado, CanCollide no.",
            "almacen_neon": f"Material Neon, color {D.NEON} (lentes y pantallas). Si se quiere ver los dígitos de "
                            f"las pantallas, SurfaceAppearance con {NOMBRE}_emision.png como máscara de emisión.",
        },
    }
    for n, (a, b) in cajas.items():
        datos["piezas"][n] = {"triangulos": resumen[n], "centro_caja": piv((a + b) / 2),
                              "tam_caja_roblox": [round(abs(v), 3) for v in C_ROBLOX @ (b - a)]}
    with open(os.path.join(SALIDA, f"{NOMBRE}.json"), "w", encoding="utf-8") as f:
        json.dump(datos, f, indent=2, ensure_ascii=False)
    print("[ok] json")


if __name__ == "__main__":
    main()
