# Bestias cósmicas (monturas de los Monstruos)

Modelos generados con Blender sin pantalla (`bpy`) por los scripts de `herramientas/`. Todo se puede regenerar:

```bash
python3 -m venv .venv && .venv/bin/pip install -r modelos/herramientas/requirements.txt scikit-image scipy
# una bestia por script: manta_estelar, dragon_vacio, serpiente_cosmica, medusa_nebular, escarabajo_abisal,
# leviatan_estelar
.venv/bin/python bestias/herramientas/manta_estelar.py --salida bestias/manta_estelar --ronda N
```

| Bestia | Carpeta | Triángulos | Tamaño (studs) | Estado |
| --- | --- | --- | --- | --- |
| Manta Estelar | `manta_estelar/` | 17.930 / 18.000 | 17,99 × 14,25 × 3,93 (sin cola) | Aprobada en la ronda 3 |
| Dragón del Vacío | `dragon_vacio/` | 19.836 / 20.000 | 4,84 × 15,83 × 7,79 (alas plegadas; envergadura abierta 14) | Aprobado en la ronda 3 |
| Serpiente Cósmica | `serpiente_cosmica/` | 19.910 / 20.000 | 6,1 × 29,41 × 4,64 (con el estandarte) | Aprobada en la ronda 2 |
| Medusa Nebular | `medusa_nebular/` | 14.802 / 16.000 | 6,97 × 6,97 × 8,37 | Aprobada en la ronda 2 |
| Escarabajo Abisal | `escarabajo_abisal/` | 19.906 / 20.000 | 9,64 × 18,81 × 7,46 | Aprobado en la ronda 3 |
| Leviatán Estelar | `leviatan_estelar/` | 19.905 / 20.000 | 26,69 × 43,8 × 18,75 (con tentáculos y estandarte) | Aprobado en la ronda 2 |

Cada carpeta lleva el `.fbx`, el atlas de 2048 (`_color`, `_normal`, `_roughness`, `_metalness`, `_emision`), el
`_turnaround.png` de 8 vistas, el `.json` (piezas, pivotes, puntos de montaje) y `verificacion_fbx.txt` (la
reimportación en escena limpia). En `rondas/` están los turnarounds y primeros planos de cada ronda de corrección.

## Cómo están hechas

- **1 unidad de Blender = 1 stud.** La escena usa `scale_length = 0,28`, así el FBX ("Apply Scalings: FBX All") va
  en metros con 1 stud = 0,28 m, la conversión del importador de Roblox (como el resto de `modelos/`).
- **GIRO_IMPORTACION**: 180° en el eje vertical antes de exportar. En Roblox la bestia mira a -Z.
- **Rig de Motor6D, sin huesos.** Cada pieza es una malla rígida con el origen en su articulación y rotación 0,0,0.
  Entre piezas hay 0,02 studs de separación. El JSON da cada pivote en coordenadas de Roblox y el padre de cada pieza.
- **Puntos de montaje**: cubos de 0,3 con nombre. En Roblox: `Transparency = 1`, `CanCollide = false`, y soldados a
  la pieza que indica el JSON.
- **Forma orgánica**: campos de distancia (numpy) → marching cubes → malla alta (para hornear) y malla baja diezmada
  (la que se exporta). El detalle grande (escamas, dientes, arnés, ojos) es geometría real; el fino va en el normal map.
- Los nombres van sin tildes (`Mandibula`, `Tentaculo_Izq`) para que no se estropeen al importar.

## En Studio

1. *Import 3D* del `.fbx` (Scale Unit: Meter). Cada malla llega como `MeshPart` con su nombre.
2. A cada `MeshPart` visible, una `SurfaceAppearance` con `ColorMap`, `NormalMap`, `RoughnessMap` y `MetalnessMap`
   del atlas (todas las piezas comparten las mismas texturas).
3. La emisión: Roblox no tiene mapa de emisión en `SurfaceAppearance`; `_emision.png` sirve de máscara para las
   piezas de neón o un futuro `Emissive`. Las córneas (`Ojos_Cornea`) van con material Glass y algo de transparencia.
4. Motor6D de cada pieza a su padre con `C0`/`C1` en el pivote del JSON. **Falta probarlo en Studio**: estas sesiones
   no tienen Studio, así que el director tiene que verlo funcionar con capturas antes de darlo por bueno.

## Desviaciones de la tabla del encargo (a revisar)

- **Medusa Nebular**: mide ≈ 8,4 de alto, no 10: la anatomía pide campana de 3 y tentáculos de 4.
- **Serpiente Cósmica**: el cuerpo (2 de alto + cresta 0,8) no llega a 5; los 4,6 se alcanzan con el estandarte. La
  cresta dorsal se pliega bajo cada asiento para que los 6 jinetes vayan a horcajadas.
- **Leviatán Estelar**: la caja total (26,7 × 43,8 × 18,8) incluye aletas, tentáculos colgando y estandarte; el cuerpo
  se ajusta a 20 × 40 × 15.
- **Dragón del Vacío**: en reposo las alas van plegadas (4,8 de ancho); abiertas darían los 14 de envergadura.
- **Escarabajo Abisal**: los élitros pivotan en su bisagra delantera (detrás del pronoto), que es donde se abren en
  un escarabajo real.
