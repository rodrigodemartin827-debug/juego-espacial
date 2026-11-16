"""
Las 100 piezas: nombre, categoría, tier, qué constructor usan y con qué parámetros.

El orden de la lista es el de las rondas (10 piezas por ronda). `escribir_indice` junta todos los JSON en
`catalogo.json` y genera `montar_acoples.luau` (script de Studio que crea los Attachments de cada pieza).
"""

import glob
import json
import math
import os

from . import alas, armas, cascos, datos, motores, otras

PIEZAS = []


def pieza(nombre, titulo, categoria, tier, construir, p, descripcion, **kw):
    d = {"nombre": nombre, "titulo": titulo, "categoria": categoria, "tier": tier, "construir": construir, "p": p,
         "descripcion": descripcion}
    d.update(kw)
    PIEZAS.append(d)
    return d


def _casco(con, p):
    for k, v in p.get("color", {}).items():
        con.colores_extra[k] = v
    if "paleta" in p:
        con.info["paleta"] = p["paleta"]
    if "detalle" in p:
        con.info["detalle"] = p["detalle"]
    if "bisel" in p:
        con.info["bisel"] = p["bisel"]
    con.info["escala_panel"] = p.get("escala_panel", 1.0)
    cascos.construir(con, p)
    plazas = p.get("plazas")
    if plazas:
        con.info["json_plazas"] = plazas


# ==============================================================================================================
# CASCOS (20)
# ==============================================================================================================

EST_EXPLORADOR = [(0, 0.22, 0.3, -0.06, 2.2), (0.07, 0.55, 0.62, -0.02, 2.4), (0.22, 0.88, 0.9, 0.02, 2.7),
                  (0.45, 1, 1, 0.03, 3.0), (0.75, 0.96, 0.95, 0.02, 3.0), (1, 0.8, 0.86, 0.0, 3.0)]
SOCK_EXPLORADOR = dict(laterales=[(0.52, 0.0)], traseros=[(0, 0)], superiores=[(0.28, "acople_cabina"),
                       (0.84, "acople_superior_cola")], inferiores=[0.5], frontal=True, t_frontal=0.16)

pieza("casco_explorador_t1", "Casco explorador (básico)", "casco", 1, _casco,
      dict(L=10, W=3.4, H=3.0, estaciones=EST_EXPLORADOR, lados=16, anillos=12, plazas=1,
           extras=["tuberias", "rejillas", "tomas", "antena"], **SOCK_EXPLORADOR),
      "Fuselaje pequeño de 1 plaza, chapa gris remachada con tuberías por fuera. Industrial y barato.")
pieza("casco_explorador_t2", "Casco explorador (militar)", "casco", 2, _casco,
      dict(L=10.5, W=3.4, H=3.0, estaciones=EST_EXPLORADOR, lados=18, anillos=13, plazas=1,
           extras=["tomas", "aletas", "antena", "rejillas"], **SOCK_EXPLORADOR),
      "Fuselaje pequeño militar, blanco con franjas naranjas y número de escuadrón.")
pieza("casco_explorador_t3", "Casco explorador (avanzado)", "casco", 3, _casco,
      dict(L=11, W=3.3, H=2.9,
           estaciones=[(0, 0.12, 0.2, -0.08, 2.1), (0.1, 0.48, 0.55, -0.03, 2.2), (0.28, 0.86, 0.88, 0.01, 2.4),
                       (0.5, 1, 1, 0.02, 2.6), (0.78, 0.95, 0.95, 0.02, 2.7), (1, 0.8, 0.88, 0.0, 2.7)],
           lados=20, anillos=14, plazas=1, extras=["neon_lados", "neon_lomo", "aletas", "quilla"],
           **SOCK_EXPLORADOR),
      "Fuselaje pequeño avanzado: metal oscuro, líneas aerodinámicas y neón cian.")

EST_CAZA = [(0, 0.06, 0.06, -0.12, 2.0), (0.1, 0.3, 0.32, -0.08, 2.2), (0.28, 0.66, 0.72, -0.02, 2.5),
            (0.5, 1, 1, 0.02, 2.8), (0.8, 0.95, 0.95, 0.02, 3.0), (1, 0.82, 0.95, 0.02, 3.2)]
SOCK_CAZA = dict(laterales=[(0.56, 0.0)], traseros=[(0, 0)], superiores=[(0.34, "acople_cabina"),
                 (0.87, "acople_superior_cola")], inferiores=[0.55], frontal=True, t_frontal=0.2)

pieza("casco_caza_t1", "Casco de caza (básico)", "casco", 1, _casco,
      dict(L=14, W=3.2, H=2.6, estaciones=EST_CAZA, lados=14, anillos=14, plazas=1,
           extras=["tuberias", "tomas", "antena"], **SOCK_CAZA),
      "Fuselaje de caza alargado de 1 plaza, gris con remaches y tuberías.")
pieza("casco_caza_t2", "Casco de caza (militar)", "casco", 2, _casco,
      dict(L=14.5, W=3.2, H=2.6,
           estaciones=[(0, 0.05, 0.05, -0.12, 2.0), (0.12, 0.3, 0.3, -0.08, 2.2), (0.3, 0.68, 0.7, -0.02, 2.4),
                       (0.52, 1, 1, 0.02, 2.6), (0.82, 0.94, 0.95, 0.02, 2.8), (1, 0.82, 0.95, 0.02, 3.0)],
           lados=18, anillos=15, plazas=1, extras=["tomas", "aletas", "antena", "quilla"], **SOCK_CAZA),
      "Fuselaje de caza militar aerodinámico: blanco y naranja con marcas de escuadrón.")
pieza("casco_caza_t3", "Casco de caza (avanzado)", "casco", 3, _casco,
      dict(L=15, W=3.0, H=2.6,
           estaciones=[(0, 0.04, 0.04, -0.1, 1.8), (0.15, 0.32, 0.28, -0.06, 1.9), (0.35, 0.72, 0.68, -0.02, 2.1),
                       (0.55, 1, 1, 0.02, 2.3), (0.84, 0.94, 0.96, 0.02, 2.5), (1, 0.84, 0.96, 0.02, 2.6)],
           lados=16, anillos=16, plazas=1, extras=["neon_lados", "neon2_lados", "aletas", "quilla", "tomas"],
           **SOCK_CAZA),
      "Fuselaje de caza avanzado y agresivo, con aristas marcadas y líneas de neón cian.")
pieza("casco_caza_t4", "Casco de caza (élite)", "casco", 4, _casco,
      dict(L=15.5, W=3.3, H=2.6, suave=False,
           estaciones=[(0, 0.04, 0.04, -0.08, 1.3), (0.16, 0.36, 0.3, -0.05, 1.3), (0.36, 0.78, 0.7, -0.02, 1.4),
                       (0.56, 1, 1, 0.02, 1.5), (0.84, 0.96, 0.98, 0.02, 1.6), (1, 0.88, 0.98, 0.02, 1.7)],
           lados=8, anillos=12, plazas=1, extras=["facetas_oro", "pinchos", "neon_lados", "neon2_lados", "quilla"],
           ang_neon=-0.25, **SOCK_CAZA),
      "Fuselaje de caza élite: negro y dorado, facetado y angular, con neón dorado y rojo.")

EST_TRANSPORTE = [(0, 0.55, 0.5, -0.05, 3.5), (0.06, 0.82, 0.78, 0.0, 4.0), (0.18, 1, 1, 0.02, 5.0),
                  (0.85, 1, 1, 0.02, 5.0), (1, 0.86, 0.9, 0.02, 4.5)]
SOCK_TRANSPORTE = dict(laterales=[(0.36, 0.0), (0.68, 0.0)], traseros=[(-0.52, 0), (0.52, 0)],
                       superiores=[(0.16, "acople_cabina"), (0.55, "acople_superior_2"),
                                   (0.9, "acople_superior_cola")],
                       inferiores=[0.25, 0.75], frontal=True, t_frontal=0.1, pilon=0.4)

pieza("casco_transporte_t1", "Casco de transporte (básico)", "casco", 1, _casco,
      dict(L=16, W=6.0, H=4.6, estaciones=EST_TRANSPORTE, lados=16, anillos=10, plazas=3,
           extras=["tuberias", "rejillas", "quilla", "antena"], **SOCK_TRANSPORTE),
      "Fuselaje ancho de carga para 3 plazas. Caja de chapa gris, remaches y tuberías.", grande=True)
pieza("casco_transporte_t2", "Casco de transporte (militar)", "casco", 2, _casco,
      dict(L=16.5, W=6.0, H=4.6, estaciones=EST_TRANSPORTE, lados=18, anillos=10, plazas=3,
           extras=["compuertas", "antena", "rejillas", "quilla"], **SOCK_TRANSPORTE),
      "Fuselaje de transporte militar con compuertas laterales de carga.", grande=True)
pieza("casco_transporte_t3", "Casco de transporte (avanzado)", "casco", 3, _casco,
      dict(L=17, W=6.0, H=4.6,
           estaciones=[(0, 0.4, 0.4, -0.05, 2.8), (0.08, 0.75, 0.75, 0.0, 3.2), (0.22, 1, 1, 0.02, 3.8),
                       (0.85, 1, 1, 0.02, 3.8), (1, 0.86, 0.9, 0.02, 3.5)],
           lados=18, anillos=11, plazas=3, extras=["blindaje", "neon_lados", "vainas", "quilla"],
           **SOCK_TRANSPORTE),
      "Fuselaje de transporte avanzado y blindado, con placas laterales y neón cian.", grande=True)

EST_BOMBARDERO = [(0, 0.2, 0.25, -0.05, 2.4, 1.0), (0.12, 0.55, 0.6, 0.0, 2.8, 0.8), (0.35, 0.95, 1, 0.02, 3.4, 0.7),
                  (0.7, 1, 0.95, 0.02, 3.6, 0.7), (1, 0.8, 0.85, 0.0, 3.4, 0.8)]
SOCK_BOMBARDERO = dict(laterales=[(0.42, 0.0), (0.72, 0.0)], traseros=[(-0.5, 0), (0.5, 0)],
                       superiores=[(0.2, "acople_cabina"), (0.55, "acople_torreta"), (0.9, "acople_superior_cola")],
                       inferiores=[0.2, 0.86], frontal=True, t_frontal=0.14)

pieza("casco_bombardero_t2", "Casco de bombardero (militar)", "casco", 2, _casco,
      dict(L=18, W=7.0, H=4.0, estaciones=EST_BOMBARDERO, lados=18, anillos=12, plazas=2,
           extras=["bahia", "tomas", "aletas", "antena"], t_tomas=0.28, **SOCK_BOMBARDERO),
      "Fuselaje pesado y ancho con bahía de bombas en la panza. Blanco y naranja.", grande=True)
pieza("casco_bombardero_t3", "Casco de bombardero (avanzado)", "casco", 3, _casco,
      dict(L=19, W=7.2, H=4.2, estaciones=EST_BOMBARDERO, lados=18, anillos=12, plazas=2,
           extras=["bahia", "blindaje", "neon_lados", "quilla", "rejillas"], **SOCK_BOMBARDERO),
      "Bombardero avanzado reforzado con placas de blindaje, bahía de bombas y neón cian.", grande=True)

EST_FRAGATA = [(0, 0.3, 0.3, -0.1, 3.0), (0.08, 0.62, 0.6, -0.05, 3.5), (0.2, 0.9, 0.92, 0.0, 4.0),
               (0.8, 1, 1, 0.0, 4.5), (1, 0.9, 0.9, 0.0, 4.0)]
SOCK_FRAGATA = dict(laterales=[(0.3, 0.0), (0.5, 0.0), (0.72, 0.0)], traseros=[(-0.55, 0.25), (0.55, 0.25), (0, -0.45)],
                    superiores=[(0.14, "acople_cabina"), (0.36, "acople_torreta_1"), (0.86, "acople_torreta_2")],
                    inferiores=[0.3, 0.7], frontal=True, t_frontal=0.08, pilon=0.5)

pieza("casco_fragata_t3", "Casco de fragata (avanzado)", "casco", 3, _casco,
      dict(L=28, W=9.0, H=6.0, estaciones=EST_FRAGATA, lados=18, anillos=12, plazas=5,
           extras=["puente", "neon_lados", "rejillas", "quilla", "vainas"], t_puente=0.6, escala_panel=1.4,
           **SOCK_FRAGATA),
      "Fuselaje grande de 5+ plazas con superestructura de mando y muchos conectores.", grande=True)
pieza("casco_fragata_t4", "Casco de fragata (élite)", "casco", 4, _casco,
      dict(L=29, W=9.0, H=6.0, suave=False,
           estaciones=[(0, 0.25, 0.25, -0.1, 1.5), (0.1, 0.62, 0.55, -0.05, 1.6), (0.24, 0.92, 0.9, 0.0, 1.8),
                       (0.8, 1, 1, 0.0, 1.9), (1, 0.9, 0.9, 0.0, 1.8)],
           lados=10, anillos=10, plazas=5,
           extras=["puente", "facetas_oro", "pinchos", "neon_lados", "neon2_lados", "quilla"], t_puente=0.6,
           escala_panel=1.4, **SOCK_FRAGATA),
      "Fragata élite negra y dorada, facetada, con puente escalonado y neón dorado y rojo.", grande=True)

pieza("casco_crucero_t4", "Casco de crucero (élite)", "casco", 4, _casco,
      dict(L=44, W=12.0, H=8.0, suave=False,
           estaciones=[(0, 0.5, 0.35, -0.1, 1.5), (0.06, 0.78, 0.55, -0.05, 1.6), (0.14, 0.7, 0.72, 0.0, 1.7),
                       (0.3, 0.9, 0.9, 0.0, 1.8), (0.75, 1, 1, 0.0, 1.9), (1, 0.86, 0.86, 0.0, 1.8)],
           lados=10, anillos=12, plazas=8,
           laterales=[(0.2, 0.0), (0.35, 0.0), (0.5, 0.0), (0.65, 0.0), (0.8, 0.0)],
           traseros=[(-0.55, 0.3), (0.55, 0.3), (-0.55, -0.35), (0.55, -0.35), (0, 0)],
           superiores=[(0.12, "acople_cabina"), (0.3, "acople_torreta_1"), (0.45, "acople_torreta_2"),
                       (0.82, "acople_torreta_3")],
           inferiores=[0.25, 0.55, 0.8], frontal=True, t_frontal=0.05, pilon=0.6,
           extras=["puente", "facetas_oro", "pinchos", "neon_lados", "neon2_lados", "quilla", "rejillas"],
           t_puente=0.63, niveles_puente=3, escala_panel=2.0),
      "Fuselaje enorme de crucero con 5 pares de acoples laterales, 5 motores y 3 torretas.", grande=True)

pieza("casco_nave_nodriza_t5", "Casco de nave nodriza (legendario)", "casco", 5, _casco,
      dict(L=60, W=24.0, H=11.0,
           estaciones=[(0, 0.12, 0.15, 0.0, 2.0, 1.0), (0.1, 0.48, 0.45, 0.0, 2.2, 0.8),
                       (0.3, 0.9, 0.85, 0.02, 2.2, 0.7), (0.6, 1, 1, 0.02, 2.2, 0.7), (0.85, 0.85, 0.8, 0.0, 2.2, 0.7),
                       (1, 0.42, 0.5, 0.0, 2.2, 1.0)],
           lados=24, anillos=18, plazas=12, organico=0.35,
           laterales=[(0.3, 0.0), (0.5, 0.0), (0.7, 0.0)], traseros=[(-0.45, 0), (0.45, 0), (0, 0)],
           superiores=[(0.16, "acople_cabina"), (0.5, "acople_torreta_1"), (0.78, "acople_torreta_2")],
           inferiores=[0.3, 0.7], frontal=True, t_frontal=0.06, pilon=0.8,
           extras=["costillas", "cristales", "neon_lomo", "cubierta", "anillos_flotantes"], n_costillas=7,
           t_cristales=(0.3, 0.45, 0.6, 0.75), t_cubierta=(0.22, 0.42), t_anillos=(0.88,), escala_panel=2.5),
      "Fuselaje legendario masivo orgánico-tecnológico: costillas, vainas de cristal y cubierta de hangar.",
      grande=True)

pieza("casco_interceptor_t3", "Casco de interceptor (avanzado)", "casco", 3, _casco,
      dict(L=16, W=2.6, H=2.5,
           estaciones=[(0, 0.03, 0.03, -0.1, 2.0), (0.18, 0.32, 0.3, -0.06, 2.1), (0.4, 0.75, 0.7, -0.02, 2.3),
                       (0.62, 1, 0.95, 0.0, 2.5), (0.86, 1, 1, 0.0, 2.6), (1, 0.96, 1, 0.0, 2.6)],
           lados=16, anillos=16, plazas=1, extras=["neon_lados", "neon_lomo", "aletas", "quilla"],
           laterales=[(0.66, 0.0)], traseros=[(0, 0)], superiores=[(0.42, "acople_cabina"),
                                                                  (0.9, "acople_superior_cola")],
           inferiores=[0.66], frontal=True, t_frontal=0.26, pilon=0.35, ancho_neon=0.08),
      "Fuselaje ultra delgado para velocidad: una aguja de metal oscuro con líneas de neón.")

pieza("casco_stealth_t4", "Casco stealth (élite)", "casco", 4, _casco,
      dict(L=16, W=7.0, H=2.6, suave=False,
           estaciones=[(0, 0.04, 0.1, 0.0, 1.0), (0.3, 0.6, 0.66, 0.0, 1.04), (0.66, 1, 1, 0.0, 1.08),
                       (1, 0.86, 0.96, 0.0, 1.08)],
           lados=12, anillos=8, plazas=1, extras=["neon2_lados", "pinchos"], ang_neon=0.0,
           paleta={"primario": ("#0A0B0D", 0.88, 0.15), "secundario": ("#16171A", 0.8, 0.25)},
           detalle={"lineas": 0.06, "lineas_oro": 0.0, "paneles": 0.5},
           laterales=[(0.62, 0.0)], traseros=[(0, 0)], superiores=[(0.36, "acople_cabina"),
                                                                  (0.86, "acople_superior_cola")],
           inferiores=[0.6], frontal=True, t_frontal=0.3, pilon=0.3),
      "Fuselaje stealth angular de facetas planas, negro mate que absorbe el radar.")

pieza("casco_alien_t5", "Casco alienígena (legendario)", "casco", 5, _casco,
      dict(L=18, W=6.0, H=4.2,
           estaciones=[(0, 0.1, 0.2, 0.1, 2.0, 1.0), (0.15, 0.5, 0.7, 0.12, 2.0, 1.0), (0.35, 1, 1, 0.05, 2.0, 0.6),
                       (0.55, 0.7, 0.8, 0.0, 2.0, 0.8), (0.75, 0.95, 0.72, -0.05, 2.0, 0.8), (1, 0.8, 0.66, 0.0, 2.0, 1.0)],
           lados=22, anillos=20, plazas=1, organico=0.16,
           extras=["costillas", "cristales", "neon_lomo"], n_costillas=5,
           laterales=[(0.4, 0.0)], traseros=[(0, 0)], superiores=[(0.22, "acople_cabina"),
                                                                 (0.86, "acople_superior_cola")],
           inferiores=[0.5], frontal=True, t_frontal=0.14),
      "Fuselaje orgánico alienígena de curvas imposibles, con costillas y vainas de cristal púrpura.")

pieza("casco_prototipo_t5", "Casco prototipo (legendario)", "casco", 5, _casco,
      dict(L=16, W=5.0, H=4.0, suave=False,
           estaciones=[(0, 0.15, 0.15, 0.0, 1.4), (0.2, 0.7, 0.7, 0.0, 1.5), (0.5, 1, 1, 0.0, 1.5),
                       (0.8, 0.86, 0.86, 0.0, 1.5), (1, 0.78, 0.78, 0.0, 1.5)],
           lados=6, anillos=16, giro=math.pi / 3, plazas=1,
           color={"neon": "#FFFFFF", "neon2": "#C45CFF"},
           paleta={"primario": ("#D8DCE6", 0.18, 0.9), "secundario": ("#1A1426", 0.25, 0.6)},
           detalle={"alien": 0.0, "lineas": 0.25, "paneles": 0.6, "tam_panel": 1.8},
           extras=["anillos_flotantes", "neon_lados", "neon2_lados"], t_anillos=(0.3, 0.62, 0.92),
           laterales=[(0.5, 0.0)], traseros=[(0, 0)], superiores=[(0.26, "acople_cabina"),
                                                                 (0.86, "acople_superior_cola")],
           inferiores=[0.5], frontal=True, t_frontal=0.16),
      "Fuselaje experimental: un prisma retorcido de cromo con anillos de neón blanco que flotan sin tocarlo.")


# ==============================================================================================================
# ALAS (15) — se modela la izquierda; la derecha sale reflejada (lado=True)
# ==============================================================================================================

def _con_estilo(fn):
    def f(con, p):
        con.colores_extra.update(p.get("color", {}))
        if "paleta" in p:
            con.info["paleta"] = p["paleta"]
        # las marcas de escuadrón (número y chevrones) solo van en los cascos
        con.info["detalle"] = dict({"marcas": 0.0}, **p.get("detalle", {}))
        con.info["escala_panel"] = p.get("escala_panel", 0.7)
        fn(con, p)
    return f


_ala = _con_estilo(alas.construir)

pieza("ala_corta_t1", "Ala corta (básica)", "ala", 1, _ala,
      dict(envergadura=4.2, cuerda_raiz=3.0, cuerda_punta=2.1, flecha=0.5, diedro=0.1, grosor_raiz=0.42,
           grosor_punta=0.3, perfil="plano", secciones=4, extras=["flaps", "luces"], n_flaps=1),
      "Ala corta y recta de chapa gris remachada, con un flap. Sencilla y barata.", lado=True)
pieza("ala_corta_t2", "Ala corta (militar)", "ala", 2, _ala,
      dict(envergadura=4.6, cuerda_raiz=3.2, cuerda_punta=1.8, flecha=1.2, diedro=0.15, grosor_raiz=0.4,
           grosor_punta=0.26, perfil="redondo", secciones=5, hardpoints=[0.5], extras=["flaps", "luces"],
           n_flaps=1),
      "Ala corta militar con un hardpoint para armas bajo el ala.", lado=True)
pieza("ala_media_t1", "Ala media (básica)", "ala", 1, _ala,
      dict(envergadura=7.0, cuerda_raiz=3.4, cuerda_punta=2.0, flecha=0.6, diedro=0.2, grosor_raiz=0.45,
           grosor_punta=0.28, perfil="plano", secciones=5, hardpoints=[0.45], extras=["flaps", "luces"]),
      "Ala media recta de chapa gris, con un hardpoint.", lado=True)
pieza("ala_media_t2", "Ala media en flecha (militar)", "ala", 2, _ala,
      dict(envergadura=7.0, cuerda_raiz=3.6, cuerda_punta=1.4, flecha=3.0, diedro=0.25, grosor_raiz=0.42,
           grosor_punta=0.22, perfil="redondo", secciones=6, hardpoints=[0.45], extras=["flaps", "winglet", "luces"],
           alto_winglet=0.9),
      "Ala media en flecha, blanca y naranja, con winglet y un hardpoint.", lado=True)
pieza("ala_media_t3", "Ala media (avanzada)", "ala", 3, _ala,
      dict(envergadura=7.5, cuerda_raiz=3.4, cuerda_punta=1.1, flecha=3.2, diedro=0.3, grosor_raiz=0.3,
           grosor_punta=0.16, perfil="redondo", secciones=7, hardpoints=[0.5],
           extras=["neon_borde", "neon_salida", "flaps"], ranura_neon_salida="neon2"),
      "Ala media avanzada de perfil fino, con el borde de ataque de neón.", lado=True)
pieza("ala_larga_t2", "Ala larga (militar)", "ala", 2, _ala,
      dict(envergadura=11.0, cuerda_raiz=4.0, cuerda_punta=1.6, flecha=2.5, diedro=0.35, grosor_raiz=0.5,
           grosor_punta=0.25, perfil="redondo", secciones=7, motores=[0.32, 0.66], extras=["flaps", "luces"],
           n_flaps=3),
      "Ala larga militar con dos góndolas para motores en el borde de salida.", lado=True)
pieza("ala_larga_t3", "Ala larga curvada (avanzada)", "ala", 3, _ala,
      dict(envergadura=11.5, cuerda_raiz=3.8, cuerda_punta=1.0, flecha=4.0, diedro=-0.2, curva=1.4,
           grosor_raiz=0.36, grosor_punta=0.16, perfil="redondo", secciones=9, motores=[0.38],
           extras=["neon_borde", "neon_salida", "flaps"], n_flaps=2),
      "Ala larga avanzada que se curva hacia arriba, con neón cian en el borde de ataque.", lado=True)
pieza("ala_larga_t4", "Ala larga (élite)", "ala", 4, _ala,
      dict(envergadura=11.0, cuerda_raiz=4.4, cuerda_punta=1.2, flecha=4.6, diedro=0.1, grosor_raiz=0.4,
           grosor_punta=0.18, perfil="rombo", secciones=6, quiebros=[(0.35, 3.0, 1.0), (0.7, 2.2, 3.4)],
           motores=[0.42], hardpoints=[0.72], extras=["neon_borde", "oro", "neon_salida", "aleta_punta"],
           alto_winglet=0.9),
      "Ala larga élite negra y dorada de geometría angular con quiebros.", lado=True)
pieza("ala_delta_t3", "Ala delta (avanzada)", "ala", 3, _ala,
      dict(envergadura=5.6, cuerda_raiz=8.0, cuerda_punta=0.7, flecha=7.0, diedro=0.0, grosor_raiz=0.42,
           grosor_punta=0.12, perfil="rombo", secciones=5, hardpoints=[0.5], extras=["neon_borde", "flaps"],
           n_flaps=1),
      "Ala delta triangular avanzada, fina y con neón en el borde.", lado=True)
pieza("ala_delta_t4", "Ala delta (élite)", "ala", 4, _ala,
      dict(envergadura=7.2, cuerda_raiz=10.0, cuerda_punta=0.8, flecha=9.0, diedro=-0.1, grosor_raiz=0.5,
           grosor_punta=0.14, perfil="rombo", secciones=6, quiebros=[(0.3, 7.2, 2.6)], motores=[0.3],
           hardpoints=[0.62], extras=["neon_borde", "oro", "neon_salida", "winglet"], alto_winglet=1.4),
      "Ala delta élite grande y agresiva, con quiebro, aleta en la punta y neón dorado y rojo.", lado=True)
pieza("ala_variable_t4", "Ala de geometría variable (élite)", "ala", 4, _con_estilo(alas.ala_variable),
      dict(envergadura=9.0, cuerda_raiz=2.6, cuerda_punta=1.1, flecha=1.6, diedro=0.1, grosor_raiz=0.3,
           grosor_punta=0.16),
      "Ala de geometría variable: el panel va en dos mallas, extendido y plegado 52° hacia atrás.", lado=True)
pieza("ala_anular_t3", "Ala anular (avanzada)", "ala", 3, _con_estilo(alas.ala_anular),
      dict(radio=2.1, cuerda=2.6, distancia=3.6),
      "Ala en anillo que rodea un motor: lleva un acople ALA_MOTOR en el centro del anillo.", lado=True)
pieza("ala_canard_t2", "Canard (militar)", "ala", 2, _ala,
      dict(envergadura=2.6, cuerda_raiz=2.0, cuerda_punta=0.9, flecha=1.0, diedro=0.1, grosor_raiz=0.26,
           grosor_punta=0.14, perfil="redondo", secciones=3, punta=False, extras=["luces"]),
      "Aleta delantera pequeña (canard) para ganar maniobrabilidad.", lado=True)
pieza("ala_alien_t5", "Ala alienígena (legendaria)", "ala", 5, _con_estilo(alas.ala_alien),
      dict(envergadura=8.5),
      "Ala orgánica de huesos curvos y membranas púrpura semitransparentes con venas de neón.", lado=True)
pieza("ala_energia_t5", "Ala de energía (legendaria)", "ala", 5, _con_estilo(alas.ala_energia),
      dict(envergadura=7.5, cuerda_raiz=3.4, cuerda_punta=1.4, flecha=3.0,
           color={"neon": "#E6B8FF", "neon2": "#FFFFFF"}),
      "No es un ala física: un marco con emisores y un campo de energía (ForceField) con rejilla de neón.",
      lado=True)

# ==============================================================================================================
# MOTORES (15)
# ==============================================================================================================

_motor = _con_estilo(motores.motor)
PEQ = dict(tipo="ALA_MOTOR", acepta=["ALA_MOTOR", "CASCO_TRASERO"])
GRANDE = dict(tipo="CASCO_TRASERO", acepta=["CASCO_TRASERO"])
UNI = dict(tipo="UNIVERSAL", acepta=["ALA_MOTOR", "CASCO_TRASERO", "UNIVERSAL"])

pieza("motor_quimico_t1", "Motor químico (básico)", "motor", 1, _motor,
      dict(R=1.0, largo=2.6, tobera={"garganta": 0.5, "salida": 0.95, "largo": 1.2}, extras=["aletas", "tuberias"],
           lados=14, **PEQ),
      "Motor químico básico de tobera simple, chapa gris y radiadores.")
pieza("motor_quimico_t2", "Motor químico (militar)", "motor", 2, _motor,
      dict(R=1.1, largo=3.0, tobera={"garganta": 0.55, "salida": 1.05, "largo": 1.3, "ranura": "secundario"},
           extras=["anillos", "rejilla_no"], lados=16,
           perfil=[(0, 0.75), (0.1, 1.0), (0.7, 1.0), (1.0, 0.85)], **PEQ),
      "Motor químico militar con la tobera naranja.")
pieza("motor_ion_t2", "Motor iónico (militar)", "motor", 2, _motor,
      dict(R=1.15, largo=2.8, tobera={"garganta": 0.85, "salida": 1.1, "largo": 0.8, "nucleo": "neon"},
           extras=["rejilla", "anillos"], color={"neon": "#6FB8FF"}, lados=18, **PEQ),
      "Motor iónico azul, eficiente: rejilla de iones con un brillo azul suave.")
pieza("motor_ion_t3", "Motor iónico (avanzado)", "motor", 3, _motor,
      dict(R=1.25, largo=3.6, tobera={"garganta": 0.9, "salida": 1.2, "largo": 0.9, "anillo_salida": "neon"},
           extras=["rejilla", "anillos_neon"], t_anillos=(0.3, 0.7), lados=20, **GRANDE),
      "Motor iónico avanzado con rejilla y anillos de neón cian brillante.")
pieza("motor_plasma_t3", "Motor de plasma (avanzado)", "motor", 3, _motor,
      dict(R=1.4, largo=4.0, tobera={"garganta": 0.7, "salida": 1.6, "largo": 1.6, "anillo_salida": "neon2"},
           extras=["anillos_neon", "luces"], t_anillos=(0.25, 0.55, 0.85),
           color={"neon": "#FF8A3A", "neon2": "#3DA8FF"}, lados=20, **GRANDE),
      "Motor de plasma de tobera ancha, con bobinas de neón naranja y azul.")
pieza("motor_plasma_t4", "Motor de plasma doble (élite)", "motor", 4, _motor,
      dict(R=1.5, largo=3.6, doble=0.85, tobera={"garganta": 0.38, "salida": 0.75, "largo": 1.3,
                                                  "anillo_salida": "neon"},
           perfil=[(0, 0.8), (0.1, 1.0), (0.8, 1.05), (1.0, 0.95)], escala_u=1.0,
           extras=["oro", "carenado"], color={"neon2": "#3DA8FF"}, lados=12, **GRANDE),
      "Motor de plasma élite con doble tobera, negro y dorado.")
pieza("motor_fusion_t4", "Motor de fusión (élite)", "motor", 4, _motor,
      dict(R=1.6, largo=5.0, tobera={"garganta": 0.9, "salida": 1.5, "largo": 1.6, "anillo_salida": "neon"},
           extras=["anillos_neon", "oro", "carenado"], t_anillos=(0.25, 0.5, 0.75), lados=20, **GRANDE),
      "Motor de fusión grande con anillos de contención de neón dorado y rojo.")
pieza("motor_fusion_t5", "Motor de fusión (legendario)", "motor", 5, _con_estilo(motores.fusion_legendario),
      dict(R=1.5, largo=5.0, color={"neon2": "#FFFFFF"}),
      "Motor de fusión legendario: el núcleo es una estrella visible en una jaula de costillas y cristal.")
pieza("motor_warp_t5", "Motor de curvatura (legendario)", "motor", 5, _con_estilo(motores.warp),
      dict(R=1.3, largo=6.5, color={"neon": "#FFFFFF", "neon2": "#C45CFF"},
           paleta={"primario": ("#D8DCE6", 0.18, 0.9)}, detalle={"alien": 0.0, "lineas": 0.25}),
      "Motor de curvatura con anillos concéntricos de neón blanco (malla aparte para hacerlos girar).")
pieza("motor_gravitacional_t5", "Motor gravitacional (legendario)", "motor", 5, _con_estilo(motores.gravitacional),
      dict(R=1.4, color={"neon2": "#FFFFFF"}),
      "Motor alienígena sin tobera: una esfera de gravedad sujeta por garras, con anillos en órbita.")
pieza("motor_auxiliar_t1", "Motor auxiliar (básico)", "motor", 1, _motor,
      dict(R=0.55, largo=1.4, tobera={"garganta": 0.28, "salida": 0.5, "largo": 0.6}, extras=["aletas"],
           n_aletas=4, lados=12, **UNI),
      "Motor pequeño de maniobra con brida universal.")
pieza("motor_auxiliar_t3", "Motor auxiliar (avanzado)", "motor", 3, _motor,
      dict(R=0.6, largo=1.7, tobera={"garganta": 0.3, "salida": 0.55, "largo": 0.6, "anillo_salida": "neon"},
           extras=["anillos_neon"], t_anillos=(0.5,), lados=14, **UNI),
      "Motor auxiliar avanzado con anillo de neón.")
pieza("motor_retro_t2", "Retrocohete (militar)", "motor", 2, _con_estilo(motores.retro),
      dict(R=0.6, largo=2.2),
      "Retrocohete de frenado: se cuelga por arriba y su tobera mira hacia delante.")
pieza("motor_vtol_t3", "Motor VTOL (avanzado)", "motor", 3, _con_estilo(motores.vtol),
      dict(R=0.8),
      "Motor de despegue vertical: tobera orientable (malla aparte) en una horquilla.")
pieza("motor_turbo_t4", "Postquemador (élite)", "motor", 4, _motor,
      dict(R=1.45, largo=3.8, tobera={"garganta": 0.75, "salida": 1.35, "largo": 1.5, "anillo_salida": "neon2"},
           extras=["petalos", "llama", "oro", "anillos_neon"], t_anillos=(0.3,), color={"neon2": "#3DA8FF"},
           lados=18, **GRANDE),
      "Postquemador élite con tobera de pétalos y la llama naranja y azul visible (malla _llama).")

# ==============================================================================================================
# ARMAS (20)
# ==============================================================================================================

pieza("laser_ligero_t1", "Láser ligero (básico)", "arma", 1, _con_estilo(armas.laser), dict(estilo="basico"),
      "Cañón láser pequeño de un tubo, gris, con radiador y cableado.")
pieza("laser_ligero_t2", "Láser ligero (militar)", "arma", 2, _con_estilo(armas.laser),
      dict(estilo="militar", largo=2.2), "Cañón láser militar con mira, naranja.")
pieza("laser_doble_t2", "Láser doble (militar)", "arma", 2, _con_estilo(armas.laser), dict(estilo="doble"),
      "Cañón láser doble militar.")
pieza("laser_pesado_t3", "Láser pesado (avanzado)", "arma", 3, _con_estilo(armas.laser_pesado), dict(largo=4.2),
      "Cañón láser grande con bobinas de neón cian a lo largo del cañón.")
pieza("laser_pesado_t4", "Láser pesado (élite)", "arma", 4, _con_estilo(armas.laser_pesado), dict(largo=4.0),
      "Cañón láser élite negro y dorado, facetado, con neón dorado y rojo.")
pieza("laser_gatling_t3", "Láser gatling (avanzado)", "arma", 3, _con_estilo(armas.gatling), dict(),
      "Cañón rotativo de 6 tubos (malla _canones aparte, para girarla).")
pieza("misiles_pod_t1", "Lanzamisiles (básico)", "arma", 1, _con_estilo(armas.misiles),
      dict(celdas=(2, 2), largo=2.6, ranura_misil="secundario"), "Lanzamisiles básico de 4 tubos.")
pieza("misiles_pod_t2", "Lanzamisiles (militar)", "arma", 2, _con_estilo(armas.misiles),
      dict(celdas=(4, 2), largo=2.8), "Lanzamisiles militar de 8 tubos.")
pieza("misiles_rack_t3", "Rack de misiles (avanzado)", "arma", 3, _con_estilo(armas.misiles),
      dict(celdas=(4, 3), largo=3.2, paso=0.66), "Rack de misiles grande de 12 celdas con bordes de neón.")
pieza("torpedo_t3", "Lanzatorpedos (avanzado)", "arma", 3, _con_estilo(armas.torpedo), dict(largo=6.0, R=0.75),
      "Lanzatorpedos pesado de tubo grande.")
pieza("torpedo_t4", "Lanzatorpedos (élite)", "arma", 4, _con_estilo(armas.torpedo), dict(largo=6.5, R=0.8),
      "Lanzatorpedos élite con sistema de guía de neón.")
pieza("canon_balistico_t2", "Cañón balístico (militar)", "arma", 2, _con_estilo(armas.balistico),
      dict(largo=6.0, r=0.22), "Cañón de proyectiles cinéticos, largo.")
pieza("canon_balistico_t4", "Cañón balístico (élite)", "arma", 4, _con_estilo(armas.balistico),
      dict(largo=8.5, r=0.32), "Cañón cinético élite masivo; el cañón es una malla aparte para el retroceso.")
pieza("torreta_auto_t3", "Torreta automática (avanzada)", "arma", 3, _con_estilo(armas.torreta), dict(canones=2),
      "Torreta automática giratoria de doble cañón (cabeza aparte para girarla).")
pieza("torreta_auto_t4", "Torreta automática (élite)", "arma", 4, _con_estilo(armas.torreta), dict(canones=4),
      "Torreta élite giratoria de cuatro cañones.")
pieza("railgun_t4", "Railgun (élite)", "arma", 4, _con_estilo(armas.railgun),
      dict(largo=9.0, color={"neon": "#3DA8FF"}), "Cañón electromagnético largo con anillos de neón azul.")
pieza("railgun_t5", "Railgun (legendario)", "arma", 5, _con_estilo(armas.railgun),
      dict(largo=12.0, color={"neon2": "#FFFFFF"}), "Railgun legendario enorme con la carga visible.")
pieza("canon_plasma_t4", "Cañón de plasma (élite)", "arma", 4, _con_estilo(armas.plasma),
      dict(color={"neon": "#FF8A2A"}), "Cañón de plasma con una cámara esférica de neón naranja.")
pieza("arma_alien_t5", "Arma alienígena (legendaria)", "arma", 5, _con_estilo(armas.alien), dict(),
      "Arma orgánica de hueso con un emisor de cristal púrpura.")
pieza("desintegrador_t5", "Desintegrador (legendario)", "arma", 5, _con_estilo(armas.desintegrador),
      dict(color={"neon": "#FFFFFF", "neon2": "#C45CFF"}),
      "Arma legendaria que abre un agujero: un anillo de neón blanco alrededor de una esfera negra.")

# ==============================================================================================================
# DEFENSAS Y ESCUDOS (10)
# ==============================================================================================================

pieza("blindaje_extra_t1", "Blindaje extra (básico)", "defensa", 1, _con_estilo(otras.blindaje),
      dict(estilo="placa"), "Placa de blindaje atornillada, gris. Sirve en los dos costados.")
pieza("blindaje_extra_t2", "Blindaje extra (militar)", "defensa", 2, _con_estilo(otras.blindaje),
      dict(estilo="gruesa", grosor=0.55), "Placa militar más gruesa, en dos capas, naranja.")
pieza("blindaje_reactivo_t3", "Blindaje reactivo (avanzado)", "defensa", 3, _con_estilo(otras.blindaje),
      dict(estilo="reactivo"), "Blindaje reactivo: 12 paneles explosivos con su indicador de neón.")
pieza("blindaje_energetico_t4", "Blindaje energético (élite)", "defensa", 4, _con_estilo(otras.blindaje),
      dict(estilo="energetico"), "Placa élite con emisores y un campo de fuerza curvado delante.")
pieza("generador_escudo_t2", "Generador de escudo (militar)", "defensa", 2, _con_estilo(otras.escudo),
      dict(estilo="parcial", radio_domo=3.2), "Generador de escudo pequeño: domo parcial delante de la nave.")
pieza("generador_escudo_t3", "Generador de escudo (avanzado)", "defensa", 3, _con_estilo(otras.escudo),
      dict(estilo="completo", radio_domo=3.6), "Escudo avanzado de domo completo semitransparente.")
pieza("generador_escudo_t4", "Generador de escudo (élite)", "defensa", 4, _con_estilo(otras.escudo),
      dict(estilo="doble", radio_domo=4.0), "Escudo élite de domo doble con anillos de neón dorado.")
pieza("generador_escudo_t5", "Generador de escudo (legendario)", "defensa", 5, _con_estilo(otras.escudo),
      dict(estilo="alien", radio_domo=4.2), "Escudo legendario alienígena: cristales púrpura y domo de energía.")
pieza("contramedidas_t2", "Contramedidas (militar)", "defensa", 2, _con_estilo(otras.contramedidas),
      dict(estilo="chaff"), "Lanzador de chaff y señuelos de 6 tubos.")
pieza("contramedidas_t4", "Guerra electrónica (élite)", "defensa", 4, _con_estilo(otras.contramedidas),
      dict(estilo="ge"), "Sistema de guerra electrónica: mástil de antenas, emisor y neón.")

# ==============================================================================================================
# CABINAS (10)
# ==============================================================================================================

_cab = _con_estilo(otras.cabina)
pieza("cabina_abierta_t1", "Cabina abierta (básica)", "cabina", 1, _cab, dict(estilo="abierta", ancho=2.2, largo=3.6),
      "Asiento al aire con parabrisas simple y arco antivuelco.")
pieza("cabina_cerrada_t1", "Cabina cerrada (básica)", "cabina", 1, _cab,
      dict(estilo="cerrada", ancho=2.3, largo=3.8, alto=1.7), "Cabina cerrada básica de cristal verdoso.")
pieza("cabina_caza_t2", "Cabina de caza (militar)", "cabina", 2, _cab,
      dict(estilo="caza", ancho=2.3, largo=4.4, alto=1.6), "Cabina de caza de burbuja con cristal amplio.")
pieza("cabina_caza_t3", "Cabina de caza con HUD (avanzada)", "cabina", 3, _cab,
      dict(estilo="caza_hud", ancho=2.3, largo=4.4, alto=1.5),
      "Cabina de caza avanzada con HUD holográfico y consolas de neón visibles.")
pieza("cabina_caza_t4", "Cabina de caza (élite)", "cabina", 4, _cab,
      dict(estilo="caza_elite", ancho=2.4, largo=4.6, alto=1.5), "Cabina élite facetada de cristal oscuro y oro.")
pieza("cabina_transporte_t2", "Cabina de transporte (militar)", "cabina", 2, _cab,
      dict(estilo="transporte", ancho=3.4, largo=4.0, alto=1.8), "Cabina ancha de varias lunas para 2 pilotos.")
pieza("cabina_puente_t3", "Puente de mando (avanzado)", "cabina", 3, _cab,
      dict(estilo="puente", ancho=5.0, largo=5.0, alto=2.4, base=0.5),
      "Puente de mando para fragata: ventanal corrido, 3 puestos y consolas.")
pieza("cabina_puente_t4", "Puente de mando (élite)", "cabina", 4, _cab,
      dict(estilo="puente_elite", ancho=6.0, largo=6.0, alto=2.6, base=0.5),
      "Puente élite para crucero con mesa de hologramas.")
pieza("cabina_alien_t5", "Cabina alienígena (legendaria)", "cabina", 5, _cab,
      dict(estilo="alien", ancho=2.6, largo=4.2), "Vaina orgánica de cristal púrpura con un asiento vivo.")
pieza("cabina_ia_t5", "Cabina de IA (legendaria)", "cabina", 5, _cab,
      dict(estilo="ia", ancho=2.6, largo=3.6, color={"neon": "#FFFFFF", "neon2": "#C45CFF"}),
      "Sin asiento: la nave la pilota una IA. Un ojo central rodeado de pantallas.")

# ==============================================================================================================
# UTILIDADES (10)
# ==============================================================================================================

pieza("tren_aterrizaje_fijo_t1", "Tren de aterrizaje fijo (básico)", "utilidad", 1, _con_estilo(otras.tren),
      dict(estilo="fijo", largo_pata=2.0), "Tres patas fijas con muelles y pies planos.")
pieza("tren_aterrizaje_retractil_t2", "Tren retráctil (militar)", "utilidad", 2, _con_estilo(otras.tren),
      dict(estilo="retractil", largo_pata=2.2), "Patas retráctiles con pistones y ruedas (malla _patas aparte).")
pieza("tren_aterrizaje_hover_t3", "Repulsores (avanzado)", "utilidad", 3, _con_estilo(otras.tren),
      dict(estilo="hover"), "Sin patas: cuatro repulsores de neón que hacen flotar la nave.")
pieza("estabilizador_vertical_t1", "Estabilizador vertical (básico)", "utilidad", 1, _con_estilo(otras.estabilizador),
      dict(estilo="basico", alto=2.4, cuerda=2.6, flecha=1.0), "Aleta vertical trasera básica con timón.")
pieza("estabilizador_vertical_t3", "Estabilizador vertical (avanzado)", "utilidad", 3,
      _con_estilo(otras.estabilizador), dict(estilo="avanzado", alto=2.8, cuerda=2.8, flecha=2.0),
      "Aleta vertical avanzada en flecha con neón en el borde.")
pieza("estabilizador_doble_t2", "Estabilizador doble en V (militar)", "utilidad", 2, _con_estilo(otras.estabilizador),
      dict(estilo="doble", alto=2.2, cuerda=2.2, flecha=1.2), "Doble aleta en V militar.")
pieza("tanque_combustible_t1", "Tanque de combustible (básico)", "utilidad", 1, _con_estilo(otras.tanque),
      dict(estilo="cilindro", R=0.75, largo=4.5), "Tanque externo cilíndrico gris con cinchas.")
pieza("tanque_combustible_t3", "Tanque aerodinámico (avanzado)", "utilidad", 3, _con_estilo(otras.tanque),
      dict(estilo="gota", R=0.8, largo=5.0), "Tanque aerodinámico en gota con medidor de neón.")
pieza("radar_t2", "Radar (militar)", "utilidad", 2, _con_estilo(otras.radar), dict(),
      "Antena de radar giratoria (plato aparte para girarlo). Brida universal.")
pieza("bahia_carga_t3", "Bahía de carga (avanzada)", "utilidad", 3, _con_estilo(otras.bahia), dict(),
      "Módulo de carga abierto bajo el casco, con cajas de recursos; debajo admite el tren de aterrizaje.")


# ==============================================================================================================
# Índice, catálogo y script de Studio
# ==============================================================================================================

def escribir_indice(salida):
    entradas = []
    for ruta in sorted(glob.glob(os.path.join(salida, "*", "*.json"))):
        with open(ruta, encoding="utf-8") as f:
            j = json.load(f)
        if "puntos_acople" not in j:
            continue
        entradas.append(j)
    orden = {p["nombre"]: i for i, p in enumerate(PIEZAS)}
    entradas.sort(key=lambda j: orden.get(j["nombre"], 999))
    cat = {
        "version": 1,
        "unidades": "studs",
        "ejes": "Roblox: delante -Z, arriba +Y, derecha +X",
        "giro_importacion": datos.GIRO_IMPORTACION,
        "conectores": datos.CONECTORES,
        "regla_encaje": datos.REGLA_ENCAJE,
        "piezas": [{k: j[k] for k in ("nombre", "titulo", "categoria", "tier", "triangulos", "tamano")}
                   | {"carpeta": j["nombre"]} for j in entradas],
    }
    with open(os.path.join(salida, "catalogo.json"), "w", encoding="utf-8") as f:
        json.dump(cat, f, indent=2, ensure_ascii=False)
    _escribir_luau(salida, entradas)
    print(f"[ok] índice: {len(entradas)} piezas")


def _num(x):
    return ("%.3f" % x).rstrip("0").rstrip(".") if abs(x) > 1e-9 else "0"


def _escribir_luau(salida, entradas):
    lineas = []
    for j in entradas:
        acs = []
        for a in j["puntos_acople"]:
            p, o = a["posicion"], a["orientacion"]
            acepta = ", ".join(f'"{t}"' for t in a.get("acepta", []))
            acs.append(
                f'\t\t{{ malla = "{a["malla"]}", nombre = "{a["nombre"]}", tipo = "{a["tipo"]}", '
                f'direccion = "{a["direccion"]}", brida = {_num(a["brida"])}, '
                f'pos = Vector3.new({_num(p[0])}, {_num(p[1])}, {_num(p[2])}), '
                f'rot = Vector3.new({_num(o[0])}, {_num(o[1])}, {_num(o[2])}), acepta = {{ {acepta} }} }},')
        lineas.append(f'\t["{j["nombre"]}"] = {{\n' + "\n".join(acs) + "\n\t},")
    plantilla = os.path.join(os.path.dirname(__file__), "plantilla_montar_acoples.luau")
    with open(plantilla, encoding="utf-8") as f:
        texto = f.read()
    texto = texto.replace("--[[PIEZAS]]", "\n".join(lineas))
    with open(os.path.join(salida, "montar_acoples.luau"), "w", encoding="utf-8") as f:
        f.write(texto)
