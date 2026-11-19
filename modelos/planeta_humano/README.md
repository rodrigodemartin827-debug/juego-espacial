# Planeta Humano: modelos 3D (todo menos las 10 casas del pueblo)

Edificios y atrezo del planeta de los Humanos: colonia espacial con alma de pueblo (paneles metálicos, madera,
piedra, cosas reparadas). Todo sale de scripts de Blender sin pantalla (`bpy`) en `herramientas/` y se puede
regenerar. Las 10 casas residenciales (casa_minero, taberna, clínica de casa…) se hicieron aparte y **no** están aquí.

- Lista completa con tamaños, triángulos y piezas: **[INDICE.md](INDICE.md)**.
- Todos de un vistazo: `hoja_planeta_humano.png`.
- Cada modelo tiene su `<modelo>_turnaround.png` (Frente, 3/4 Frontal, Lateral Izq, 3/4 Trasera, Trasera,
  Lateral Der, Arriba, Wireframe; estudio de 3 luces).

> **Nada de esto se ha probado todavía en Roblox Studio.** Esta sesión no tiene Studio. Los FBX se han verificado
> reimportándolos en Blender (piezas, triángulos, tamaño, normales). Según CLAUDE.md, el director tiene que
> importarlos en Studio y revisarlos con capturas antes de darlos por buenos.

## Qué hay en cada carpeta

```
<zona>/<modelo>/
  <modelo>.fbx              las mallas (sin texturas incrustadas)
  <modelo>.json             tamaño, triángulos, piezas con su pivote, anclajes, notas y verificación del FBX
  <modelo>_turnaround.png   las 8 vistas
  texturas/<modelo>_color.png, _normal.png, _rugosidad.png, _metal.png   (atlas de 2048 × 2048)
  texturas/<modelo>_color_<variante>.png   solo si el modelo tiene variantes de color (contenedor_basura: azul)
```

## Reglas con las que están hechos

| Regla | Cómo se cumple |
| --- | --- |
| Todo 3D real, con grosor | Cada pieza es un sólido cerrado: frutas esféricas, letras extruidas, tornillos de cabeza hexagonal, cristales con grosor, telas y lonas como láminas con grosor. Lo «pintado» (líneas del suelo, etiquetas, tiza) también tiene unas centésimas de grosor. En el mobiliario urbano 2 (`urbano_b.py`) el texto pintado largo (flechas del poste, horarios, mapa, logos, avisos) va como **calcomanía horneada en el atlas** (`calcos` en `crear_material`): no gasta triángulos y se pela y ensucia con la pintura de debajo. |
| Un modelo = una escena limpia | `Modelo()` llama a `bpy.ops.wm.read_factory_settings()` y lo modela desde cero. No se reutiliza geometría entre modelos. |
| Escala 1 unidad = 1 stud | Se modela en studs y se exporta con **Apply Scalings: FBX All**; la cabecera del FBX dice 0,28 m por unidad (`unidades_fbx.py` corrige los que salieron antes con 1 m). |
| GIRO_IMPORTACION | Antes de exportar se gira 180° sobre el eje vertical (la Y de Roblox). En Studio el frente mira a **-Z**. |
| Atlas de 2048 | Una UV y un atlas por modelo para todas las piezas con textura: color (con desgaste, suciedad, óxido, lluvia y oclusión horneados), normales (relieve procedural), rugosidad y metal. |
| Lo que brilla, aparte | Mallas `*_neon` (Material **Neon**). Cyan humano `#3DF2FF`; la clínica usa blanco `#FFFFFF`; las excepciones (forja naranja `#FF6B35`, cantina ámbar `#FFB347`, llama azul, vapor verde, fluorescentes) van en el JSON. |
| Cristal, aparte | Mallas `*_cristal` (Material **Glass**, color y transparencia en el JSON). |
| Piezas animables, aparte | Puertas, persianas, cajones, grúas, pistones, asas, frenos… cada una con su pivote (en el JSON y como origen de la malla). |
| Presupuesto de triángulos | Se comprueba al generar: si un modelo se pasa, no se exporta. |
| Verificación | Tras exportar se reimporta el FBX en una escena vacía y se comprueban nombres, triángulos, tamaño y normales hacia fuera (volumen con signo positivo). |

## Importar en Studio

1. **Avatar → Import 3D** y elige el `.fbx`.
2. **Unidad:** las coordenadas del FBX están en studs (1 unidad = 1 stud) y el archivo declara que su unidad mide
   0,28 m, lo que mide un stud en Roblox. Así llega con el tamaño del JSON tanto si el importador lee la unidad del
   archivo (*Scale Unit* en automático o *Meter*) como si toma las coordenadas en bruto (*Stud*). Es la misma
   medida física que el resto de modelos del repositorio. Si aun así llega 3,57 veces más grande o más pequeño,
   cambia *File General → Scale Unit* hasta que coincida con el JSON.
3. Comprueba que el frente mira a -Z. Si no, el giro es al revés: gíralo 180° en Y.
4. **Texturas:** sube las cuatro del atlas (Asset Manager → Bulk Import) y en cada MeshPart con textura crea
   una `SurfaceAppearance` con `ColorMap`, `NormalMap`, `RoughnessMap` y `MetalnessMap`. Todas las piezas con
   textura de un modelo comparten las mismas cuatro imágenes.
5. Las mallas `*_neon` → Material Neon y el color del JSON. Las `*_cristal` → Glass con su color y transparencia.
6. Piezas móviles: su `CFrame` de origen es el pivote del JSON (`pivote_studs`, en coordenadas de Roblox
   relativas al centro del suelo del modelo). Las notas de cada pieza dicen cómo se mueve.

## Regenerar

```bash
python -m venv venv && venv/bin/pip install bpy==5.2.3 pillow numpy
cd herramientas
../venv/bin/python generar.py tienda_armas          # uno
../venv/bin/python generar.py zona:industrial       # una zona
PH_DEBUG=1 ../venv/bin/python generar.py forja_principal   # solo cuenta triángulos por sección
python3 indice.py                                   # INDICE.md y hoja_planeta_humano.png
```

Cada modelo tarda unos 3 minutos en una CPU de 4 núcleos (casi todo es el horneado del atlas).

| Archivo | Qué hace |
| --- | --- |
| `ph.py` | El kit: primitivas con grosor (caja con chaflán, cilindro, torno, tubo por curva, lámina con grosor, letras 3D, pernos, remaches), materiales procedurales con desgaste, UV, horneado, turnaround, FBX y verificación. |
| `arq.py` | Piezas paramétricas: muros con huecos, marcos, vigas en H, barandillas, escalones, focos, cámara de seguridad, reja plegable, bajantes, espada, caja de fruta. |
| `comercial*.py`, `industrial*.py`, `hangar.py` | Un modelo por función. |
| `primer_plano.py` | Render de revisión de cerca a partir del FBX ya exportado. |

## Lo que falta o hay que revisar

- El primer encargo llegó cortado en `contenedor_envio_grande`; el segundo completó los modelos #49-85
  (hangar, naturaleza, edificios especiales y mobiliario urbano). Ya están los 85.
- No se ha visto nada en Studio (unidad del importador, giro y SurfaceAppearance sin confirmar).
- Las traseras y laterales de los edificios son más sencillas que las fachadas: están pensadas para ir contra
  otros edificios en el pueblo. Si alguno queda exento, conviene añadirles detalle.
- Las texturas no van incrustadas en el FBX (con 2048 × 4 mapas pesarían el doble en el repositorio).
