# Pueblo: casas

Modelos de las casas del pueblo, generados con scripts de Python en Blender sin pantalla (`bpy` 4.2). No hay nada
hecho a mano: todo sale de `herramientas/` y se puede regenerar.

| Carpeta | Qué es | Triángulos |
| --- | --- | --- |
| `casa_familia/` | La casa de la familia: la más grande del pueblo, dos plantas, con niños | 13.886 (límite: 14.000) |

## Convenciones (distintas de `modelos/`)

- **1 unidad de Blender = 1 stud.** El FBX se exporta con *Apply Scalings = FBX All*. En Studio se importa con
  **Scale Unit = Stud**.
- **Giro de importación:** antes de exportar, el modelo se gira 180° sobre el eje vertical, porque el importador de
  Roblox mete las mallas giradas (lo mismo que `MontarRegion.GIRO_IMPORTACION` en el valle del Alba).
- **Un atlas de 2048²** por casa con Base Color, Normal, Roughness, Metalness y Emisión horneados. Todas las mallas
  de la casa lo comparten.
- Todas las piezas son mallas cerradas con grosor real y normales hacia fuera.

## Regenerar

```bash
pip install bpy==4.2.0 pillow numpy   # Python 3.11
python pueblo/herramientas/casa_familia.py            # unos 20 minutos en CPU
python pueblo/herramientas/casa_familia.py --rapido   # atlas de 1024 y renders pequeños, para probar
python pueblo/herramientas/verificar_casa.py          # reimporta el FBX y comprueba tris, UV, tamaño y pivote
```

| Archivo | Para qué |
| --- | --- |
| `herramientas/kit_casa.py` | Primitivas con grosor (paredes con huecos, revoluciones, tubos, prismas), atlas, horneado, exportación |
| `herramientas/pinturas_casa_familia.py` | Texturas pintadas a mano con Pillow (puerta, marcos azules, dibujo, placa, felpudo, rayuela...) |
| `herramientas/casa_familia.py` | El modelo: medidas, materiales y cada pieza |
| `herramientas/verificar_casa.py` | Comprobación del FBX |

## casa_familia en Studio

1. *Import 3D* → `casa_familia/casa_familia.fbx`, **Scale Unit = Stud**, Anchored activado.
2. Salen 4 `MeshPart`:
   - `casa_familia`: la casa y su entorno. `SurfaceAppearance` con `ColorMap`, `NormalMap`, `RoughnessMap` y
     `MetalnessMap` del atlas.
   - `casa_familia_Puerta`: la hoja de la puerta, con el origen en el eje de las bisagras para animarla (girando en
     Y). Lleva el mismo `SurfaceAppearance`. Abre hacia fuera.
   - `casa_familia_Cristal`: **Material Glass**, Transparency 0,4, color `#CFE6EE`.
   - `casa_familia_Neon`: **Material Neon**, color `#3DF2FF` (la bombilla de la puerta y la pantallita del medidor).
3. Luces recomendadas y sus posiciones en `casa_familia/casa_familia.json` (`luces_recomendadas`).

**Sin probar en Studio todavía.** Hay que comprobarlo con capturas: que la fachada (la puerta amarilla) quede
mirando hacia delante, el tamaño (12,6 × 10,4 × 9,4 studs con el entorno) y que la puerta gire sobre sus bisagras.

**Ojo con la escala:** con 9 studs de alto y dos plantas, la puerta mide 3,1 studs y un R6 mide 5. Es la medida que se
pidió para el pueblo. Si los jugadores tienen que entrar, hay que escalar el modelo entero (×1,6 más o menos).
