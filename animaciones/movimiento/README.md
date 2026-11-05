# Animaciones de movimiento (R6)

Tres animaciones **en bucle perfecto** para el rig R6: reposo, andar y correr. Están hechas con Blender por código
(`bpy`), reutilizando el rig y el proceso del puñetazo (`animaciones/herramientas/rig_r6.py` y su cinemática). Cada
una se entrega en `.fbx` (para el importador de Studio) y en `.rbxmx` (una `KeyframeSequence` que se mete en Studio sin
importador).

| Animación | Fotogramas (30 fps) | Duración | Pie quieto a | Prioridad | GIF |
| --- | --- | --- | --- | --- | --- |
| Reposo | 0–120 | 4,0 s | — | `Idle` | `reposo.gif` |
| Andar | 0–24 | 0,8 s | 7,5 studs/s | `Movement` | `andar.gif` |
| Correr | 0–18 | 0,6 s | 16 studs/s | `Movement` | `correr.gif` |

El último fotograma es idéntico al primero (en posición y en velocidad, porque todas las curvas son cíclicas), así que
al repetirse no hay salto. El script lo comprueba: la diferencia entre el último y el primero es 0.

## Archivos

Para cada animación (`reposo`, `andar`, `correr`):

| Archivo | Qué es |
| --- | --- |
| `<nombre>.rbxmx` | **La forma más rápida de meterla en Studio**: `KeyframeSequence` con `Loop = true` y su prioridad |
| `<nombre>_solo_huesos.fbx` | Para el importador de FBX del Animation Editor: solo los 7 huesos R6 |
| `<nombre>.fbx` | Rig + cuerpo de cajas + animación, para verla en Blender u otro programa |
| `<nombre>.blend` | Escena de Blender con la animación horneada, para retocarla a mano |
| `<nombre>_hoja_de_contactos.png` | Fotogramas clave desde frente, lateral y 3/4 (versión final) |
| `<nombre>.gif` | El bucle moviéndose, con las tres vistas |
| `rondas/` | Las hojas de contactos de cada ronda de mejora, a media resolución |
| `herramientas/` | Los scripts que lo generan todo |

## Cómo está hecha (y qué hace con las limitaciones de R6)

R6 no tiene codos, rodillas, tobillos ni manos: cada brazo y cada pierna es **un bloque rígido**. Para que no parezca un
muñeco de palo, el movimiento sale del cuerpo entero:

- **Los pies no patinan.** La animación es "en el sitio" (el Humanoid de Roblox mueve al personaje) y el suelo corre
  hacia atrás como una cinta. La bota de R6 se trata como un balancín: apoya el **talón**, rueda por la **planta** y se
  despega por la **punta**, sin deslizar. La pierna de apoyo no se anima a mano: su ángulo se calcula para que la bota
  quede clavada en su huella. En los GIF el suelo corre a la velocidad de la animación, así que se puede comprobar a
  ojo: el pie apoyado no se mueve respecto a las casillas.
- **El cuerpo sube y baja él solo.** Como la pierna es rígida, la altura del torso sale de la geometría (la cadera pasa
  por encima de la pierna como un péndulo invertido). Sube y baja unos 0,21 studs al andar y 0,16 al correr.
- **Peso y cadera.** El torso se balancea hacia la pierna que carga, se ladea para levantar la cadera de la pierna que
  avanza (así la bota no roza el suelo al pasar) y gira con la pierna que va delante. La cabeza compensa parte del giro
  y del ladeo para mirar al frente, con un pequeño retraso.
- **Brazos** al contrario que las piernas, con retraso respecto al torso (van "arrastrados"), separados del cuerpo y
  girando un poco sobre su eje.
- **Correr** lleva el torso más inclinado (~20°), zancada larga, brazos enérgicos y **fase en el aire**: cada pie está
  en el suelo el 17 % del ciclo y el resto vuela, con los dos pies en el aire y las piernas abiertas. El cuerpo sigue
  una parábola entre el despegue (de puntillas, todavía subiendo, sin tirón) y el aterrizaje, que lleva un pequeño
  golpe que se lee como la pisada. Tras despegar, la pierna se queda estirada atrás y después pasa por debajo del
  cuerpo deprisa, cuando está en lo alto.
- **Reposo**: dos respiraciones (el pecho se abre, los hombros suben unas centésimas y la cabeza acompaña) y un cambio
  de peso lento de un pie a otro. Los pies no se mueven: las piernas se ladean sobre la arista de la bota y el torso se
  ladea solo lo justo para que los dos pies sigan apoyados (el "contrapposto").

### Mediciones (las comprueba `generar.py` y falla si se pasan)

| | Reposo | Andar | Correr |
| --- | --- | --- | --- |
| Bota hundida en el suelo (máx.) | 0,000 | 0,000 | 0,000 |
| Bota apoyada que flota (máx.) | 0,004 | 0,033 | 0,021 |
| Pie apoyado que se desplaza (patina) | 0,006 | 0,000 | 0,002 |
| Bota en el aire: lo más cerca que pasa del suelo | — | 0,04 | 0,14 |

En studs. La bota apoyada solo "flota" en el instante en que la planta está plana (la suela se trata como un arco muy
abierto para que el cuerpo no dé un tirón al pasar del talón a la punta); son 1–2 píxeles en los renders.

### Las rondas de mejora

Cada ronda: renderizar la hoja de contactos y el GIF, mirarlos, anotar qué falla y corregirlo en los datos de la
animación (`herramientas/andar.py`, `correr.py`, `reposo.py`). Las hojas están en `rondas/`.

| Ronda | Lo que se vio | Lo que se cambió |
| --- | --- | --- |
| **Andar** 0 (`andar_ronda_0`) | Pies bien clavados (talón → planta → punta), pero el personaje sale pequeño, los brazos casi no se mueven y el torso va tieso | Cámara más cerrada, brazos de +24°/−22° a +32°/−28°, inclinación que sube al impulsarse |
| Andar 1 | Inclinación poco visible y cabeza rígida | Más inclinación (7–9°) y la cabeza cabecea un poco tras cada apoyo |
| Andar 2 | Ritmo demasiado uniforme, sin peso | El cuerpo frena un poco al pasar sobre el pie (±0,04 studs) y el brazo de atrás se separa más |
| Andar 3 | De frente se contonea demasiado (el torso se ladeaba 7° para que la bota no rozara) y la pierna en el aire va abierta | Se vio que abrir la pierna baja la arista interior de la bota: pierna recta y ladeo de 4,5°, que basta. **Final** (`andar_hoja_de_contactos.png`) |
| **Correr** 0 | No se leía como carrera: parecía una marcha levantando las rodillas, con la pierna de atrás recogida y la zancada pasándose de larga (aterrizaba con la pierna a 80°) | Apoyo más corto (17 % del ciclo) para aterrizar a ~30°; la pierna en el aire pasa a una curva con claves |
| Correr 1 | Ya es carrera (vuelo con las piernas abiertas), pero la pierna que vuelve rozaba el suelo al aterrizar la otra y el torso iba casi recto | Tras despegar la pierna se queda estirada atrás (−54°) y pasa por debajo del cuerpo cuando está en lo alto; ladeo durante el apoyo para que la bota no se hunda |
| Correr 2 | Torso aún poco inclinado y brazos flojos | Inclinación 17–22°, brazos +78°/−52° y la cabeza baja un poco al recibir el peso |
| Correr 3 | Brazo delantero casi horizontal, como un puñetazo | Brazos +68°/−58° (más atrás que delante, como un velocista) |
| Correr 4 | Aterrizaje sin peso; piernas algo abiertas de frente | Al aterrizar el torso cae 3,5° hacia delante y la cabeza baja (impacto) y se recupera en el apoyo; pierna en el aire recta y menos ladeo. **Final** |
| **Reposo** 0 | Correcto pero rígido: brazos pegados, postura de soldado, el cambio de peso apenas se nota | Pies más abiertos, brazos separados y girados, más cambio de peso (0,17 studs) y la cabeza acompaña |
| Reposo 1 | Mucho más natural; la respiración casi no se ve y el pecho se echa atrás de más | Hombros suben 0,065 studs al coger aire, menos giro del pecho y torso un pelo adelantado (relajado) |
| Reposo 2 | Los brazos se mueven a la vez que el torso, sin inercia | Los brazos se quedan atrás cuando el torso se desplaza (inercia) |
| Reposo 3 | En la vista lateral el brazo queda adelantado, como si fuera a coger algo | Brazos más caídos y girados hacia dentro. **Final** |

Además de mirar las hojas, el modelo del pie se mejoró dos veces durante las rondas: la huella se centra bajo la cadera
(al principio la pierna se ladeaba 15° y se hundía 0,14 studs) y, al ladearse, la bota pivota sobre su arista lateral
en lugar de sobre su centro (así ya no se hunde nada).

## Meterla en Roblox Studio

### Opción A: el `.rbxmx` (sin importador)

1. Arrastra `andar.rbxmx` a la ventana de Studio (o clic derecho en `Workspace` → **Insert from File…**). Aparece una
   `KeyframeSequence` llamada `Andar`.
2. Crea un rig R6 (Avatar → Rig Builder → R6 → Block Rig). Dentro del rig, crea un `Model` llamado `AnimSaves` (si no
   existe) y mete ahí la `KeyframeSequence`.
3. Selecciona el rig, abre el **Animation Editor** y en **⋮ → Load** elige `Andar`. Dale a ▶ para verla.
4. **⋮ → Publish to Roblox** (a nombre del dueño del juego, o no se podrá reproducir). Studio da el ID.

Ya lleva `Loop = true` y la prioridad (`Idle` para el reposo, `Movement` para andar y correr).

### Opción B: el FBX

Como el puñetazo (ver `animaciones/README.md`): rig R6 → Animation Editor → **Create** → **⋮ → Import → From FBX** →
`<nombre>_solo_huesos.fbx`. Después activa **Looping**, pon la prioridad y publica.

### Usarlas en el juego

Las animaciones de andar y correr del personaje las pone el script `Animate` de Roblox. Con los IDs publicados, la
forma más sencilla es cambiar sus `Animation` (`idle`, `walk`, `run`) o el `AnimationId` de un script `Animate` propio.
Para que los pies no patinen, la velocidad de reproducción debe seguir a la del personaje:

```lua
pista:AdjustSpeed(humanoid.WalkSpeed / 7.5)  -- andar (7,5 = velocidad a la que está hecha)
pista:AdjustSpeed(humanoid.WalkSpeed / 16)   -- correr
```

Recomendación: andar por debajo de unos 11 studs/s y correr por encima (con la WalkSpeed por defecto, 16, la carrera
va a su velocidad exacta). En móvil el joystick a medias da velocidades bajas, que es donde entra el andar.

> **No lo he podido probar en Studio** (esta sesión no tiene Studio). He comprobado el `.fbx` volviéndolo a importar en
> Blender y el `.rbxmx` volviéndolo a leer y reproduciendo los Motor6D como lo hace Roblox
> (`Part1 = Part0 * C0 * Transform * C1:Inverse()` con los C0/C1 del R6 estándar): coincide con Blender al
> milímetro. Falta verlo en Studio con capturas antes de darlo por bueno.

Si algo sale raro en Studio:

- **Mira hacia atrás o anda hacia atrás** (FBX): en `animaciones/herramientas/exportar_fbx.py` cambia
  `axis_forward="Z"` por `"-Z"`.
- **Brazos o piernas giran en un sentido raro** (RBXMX): la conversión está en `herramientas/rbxmx.py`
  (`MOTORES` son los C0 del R6 estándar). Si tu rig tiene otros Motor6D, ajusta ahí sus rotaciones.
- **El personaje flota o se hunde un poco**: el torso sube y baja respecto al `HumanoidRootPart` (es el sube y baja del
  paso). Si se quiere menos, baja la inclinación de las piernas acortando el paso (`VELOCIDAD` o `CICLO`).

## Regenerar

Requiere Python 3.13 con `bpy` 5.2 y Pillow (`animaciones/herramientas/requirements.txt`):

```bash
pip install -r animaciones/herramientas/requirements.txt
python animaciones/movimiento/herramientas/generar.py andar --todo     # o reposo / correr
python animaciones/movimiento/herramientas/verificar.py animaciones/movimiento/andar_solo_huesos.fbx andar
```

| Script | Para qué sirve |
| --- | --- |
| `ciclo.py` | Curvas cíclicas, el modelo de la bota (talón → planta → punta) y el resolvedor de la pierna de apoyo |
| `marcha.py` | Generador de andar y correr: huellas, pierna en el aire, fase de vuelo y mediciones |
| `andar.py`, `correr.py`, `reposo.py` | **Los datos de cada animación: aquí se retoca el movimiento** |
| `render_mov.py` | Render con Cycles (CPU) con el suelo en cinta, hoja de contactos y GIF |
| `rbxmx.py` | Escribe y vuelve a leer la `KeyframeSequence` |
| `generar.py` | Lo ejecuta todo y comprueba bucle, pies, cinemática y RBXMX |
| `verificar.py` | Reimporta el FBX y lo compara con la animación |
