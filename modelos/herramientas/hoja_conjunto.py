"""
Hoja de contactos con TODOS los modelos juntos: recorta la vista 3/4 de la hoja final de cada uno y las monta en
una cuadrícula con su nombre, sus triángulos y la carpeta.

Las hojas finales salen de los otros scripts (con el mismo estudio y la misma luz), así que todas las miniaturas
son coherentes. No renderiza nada: si cambias un modelo, regenera su hoja y vuelve a ejecutar esto.

Uso:
    python modelos/herramientas/hoja_conjunto.py modelos/hoja_contactos_todo.png
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

RAIZ = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

# Disposición de cada hoja (ver comun.montar_hoja): tamaño de la miniatura, margen izquierdo de las etiquetas,
# alto de la cabecera y columnas. Las hojas «de una fila» se repartieron en 4 columnas.
LOTE = dict(tam=400, izq=170, cab=84)
NAVE = dict(tam=460, izq=0, cab=84)
UNO = dict(tam=400, izq=0, cab=84)  # hojas de un solo modelo con 400 px: 4 columnas sin etiquetas

# (hoja, fila, columna, disposición, nombre, carpeta, triángulos)
MODELOS = [
    ("nave_humana/hoja_contactos_5.png", 0, 1, NAVE, "Nave humana «Alba»", "nave_humana", 2360),
    ("monstruo/hoja_contactos_5.png", 0, 1, NAVE, "Monstruo R6 «El Hueco»", "monstruo", 6912),
    ("ciudad_humana/hoja_contactos_5.png", 0, 1, LOTE, "Tienda (persiana aparte)", "ciudad_humana", None),
    ("ciudad_humana/hoja_contactos_5.png", 0, 4, LOTE, "Tienda: persiana subida", "ciudad_humana", None),
    ("ciudad_humana/hoja_contactos_5.png", 1, 1, LOTE, "Edificio residencial", "ciudad_humana", None),
    ("ciudad_humana/hoja_contactos_5.png", 2, 1, LOTE, "Torre de oficinas", "ciudad_humana", None),
    ("ciudad_humana/hoja_contactos_5.png", 3, 1, LOTE, "Farola", "ciudad_humana", None),
    ("hangar/hoja_contactos_5.png", 0, 1, UNO, "Hangar con la forja", "hangar", None),
    ("hangar/hoja_contactos_5.png", 1, 1, UNO, "Hangar: interior", "hangar", None),
    ("planeta_monstruos/hoja_contactos_5.png", 0, 1, LOTE, "Árbol retorcido", "planeta_monstruos", None),
    ("planeta_monstruos/hoja_contactos_5.png", 1, 1, LOTE, "Árbol colgante", "planeta_monstruos", None),
    ("planeta_monstruos/hoja_contactos_5.png", 2, 1, LOTE, "Tocón partido", "planeta_monstruos", None),
    ("planeta_monstruos/hoja_contactos_5.png", 3, 1, LOTE, "Roca oscura partida", "planeta_monstruos", None),
    ("planeta_monstruos/hoja_contactos_5.png", 4, 1, LOTE, "Aguja oscura partida", "planeta_monstruos", None),
    ("planeta_monstruos/hoja_contactos_5.png", 5, 1, LOTE, "Arco de costillas", "planeta_monstruos", None),
    ("cristal_abisal/hoja_contactos_5.png", 0, 1, UNO, "Cristal abisal (recurso)", "cristal_abisal", None),
    ("criaturas/hoja_contactos_5.png", 0, 1, LOTE, "Brincador lanudo", "criaturas", None),
    ("criaturas/hoja_contactos_5.png", 1, 1, LOTE, "Acechador del abismo", "criaturas", None),
]
for i, (nombre, archivo) in enumerate([("Canto rodado", "Roca_Canto"), ("Aguja", "Roca_Aguja"),
                                        ("Losa en capas", "Roca_Losa"), ("Grupo de piedras", "Roca_Grupo"),
                                        ("Cristal cian", "Mineral_Cristal"), ("Ámbar solar", "Mineral_Ambar"),
                                        ("Esquirla del vacío", "Mineral_Vacio")]):
    MODELOS.append(("rocas_minerales/hoja_contactos_5.png", i, 1, LOTE, nombre, "rocas_minerales", None))

LADO = 360
COLUMNAS = 6


def fuente(tam, negrita=True):
    ruta = f"/usr/share/fonts/truetype/dejavu/DejaVuSans{'-Bold' if negrita else ''}.ttf"
    return ImageFont.truetype(ruta, tam) if os.path.exists(ruta) else ImageFont.load_default(tam)


def recorte(hoja, fila, col, disp):
    t = disp["tam"]
    x = disp["izq"] + col * t
    y = disp["cab"] + fila * t
    return hoja.crop((x + 2, y + 30, x + t - 2, y + t - 2)).resize((LADO, LADO - 28 * LADO // t), Image.LANCZOS)


def main(salida):
    cache = {}
    filas = (len(MODELOS) + COLUMNAS - 1) // COLUMNAS
    alto_celda = LADO + 46
    cab = 90
    img = Image.new("RGB", (COLUMNAS * LADO, cab + filas * alto_celda), (16, 18, 24))
    d = ImageDraw.Draw(img)
    d.text((16, 14), "Todos los modelos — hojas finales", fill=(255, 214, 102), font=fuente(30))
    d.text((18, 56), f"{len(MODELOS)} vistas de {len({m[5] for m in MODELOS})} carpetas · vista 3/4 de cada hoja "
                     "final (mismo estudio y luz) · detalles y medidas en la hoja de cada carpeta",
           fill=(200, 205, 215), font=fuente(16, False))
    for i, (hoja, fila, col, disp, nombre, carpeta, _) in enumerate(MODELOS):
        ruta = os.path.join(RAIZ, hoja)
        if ruta not in cache:
            cache[ruta] = Image.open(ruta).convert("RGB")
        mini = recorte(cache[ruta], fila, col, disp)
        x = (i % COLUMNAS) * LADO
        y = cab + (i // COLUMNAS) * alto_celda
        img.paste(mini, (x, y))
        d.rectangle((x, y, x + LADO - 1, y + alto_celda - 1), outline=(40, 44, 56))
        d.text((x + 10, y + mini.height + 4), nombre, fill=(255, 255, 255), font=fuente(17))
        d.text((x + 10, y + mini.height + 26), f"modelos/{carpeta}", fill=(150, 160, 178), font=fuente(13, False))
    img.save(salida)
    print("[ok]", salida)


if __name__ == "__main__":
    main(sys.argv[1])
