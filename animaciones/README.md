# Animaciones de combate

Animaciones para el rig **R15** de Roblox, creadas con Blender en modo sin pantalla (`bpy`) y exportadas a `.fbx`.

| Archivo | Qué es |
| --- | --- |
| `punetazo_fuerte_anime.fbx` | Rig R15 + cuerpo de cajas + animación. Sirve para previsualizar en Blender u otro programa. |
| `punetazo_fuerte_anime_solo_huesos.fbx` | **El que se importa en Studio**: solo los 16 huesos R15 con la animación. |
| `punetazo_fuerte_anime.blend` | Escena de Blender con la animación ya horneada, para retocarla a mano. |
| `punetazo_fuerte_anime_hoja_de_contactos.png` | Fotogramas clave desde frente, lateral y 3/4. |
| `herramientas/` | Los scripts que lo generan todo (ver más abajo). |

## Animación: puñetazo fuerte estilo anime

40 fotogramas a 30 fps (1,33 s). Brazo derecho, sin bucle. Prioridad recomendada: **Action**.

| Fotogramas | Fase |
| --- | --- |
| 0 | Guardia |
| 0–10 | **Anticipación**: cadera y torso giran hacia atrás (unos −75° en total), el cuerpo se agacha, el puño se carga detrás |
| 10–12 | Tensión: casi quieto |
| 12–16 | **Golpe**: primero la cadera (12–14), luego el torso (13–15) y por último el puño (13–16). Son 3 fotogramas (0,1 s) de puño en el aire |
| 16–22 | **Impacto exagerado** y mantenido: lunge profundo, torso inclinado, brazo recto, pie trasero pivotando sobre la punta |
| 22–40 | Recuperación hasta la guardia |

El fotograma del **impacto es el 16** (0,53 s), que es el `Tiempos.Carga` del Remate.

Todas las curvas llevan easing (suave, entrada, salida, "golpe" explosivo y "rebote" con sobrepaso); no hay tramos
lineales. Como Roblox no importa curvas Bézier, el `.fbx` lleva **una clave por fotograma** con el easing ya aplicado.
Los pies no patinan (cinemática inversa de dos huesos; error medido 0,0000 studs) y el puño llega exactamente al punto de impacto.

## Importar en Roblox Studio

1. Abre el lugar y añade un maniquí R15: pestaña **Avatar → Rig Builder → R15 → Block Rig**.
2. Selecciona el rig y abre el **Animation Editor** (pestaña **Avatar → Animation Editor**, o *Plugins*). Pulsa **Create**
   y dale un nombre, p. ej. `PunetazoFuerte`.
3. En el menú **⋮** de la ventana del editor elige **Import → From FBX** (*Import From FBX*) y selecciona
   `punetazo_fuerte_anime_solo_huesos.fbx`. Roblox empareja los huesos con las partes del rig por su nombre
   (`LowerTorso`, `RightUpperArm`...), por eso no hay que cambiar nada.
4. Dale a ▶ para ver el resultado, deja **Looping** desactivado y en **⋮ → Set Animation Priority** elige **Action**.
5. **⋮ → Save** y después **⋮ → Publish to Roblox**. La animación se publica a nombre del mismo creador (tu usuario o
   el grupo) que es dueño del juego: si no, otros jugadores no podrán reproducirla.
6. Al publicar, Studio te da el **ID** (también sale en la ventana *Output*). Solo necesitas el número.

## Poner el ID: es el **Remate** del combo (`Combo4`)

El combate ya tiene su sitio para los IDs: `src/shared/Combate/Datos/Recursos.luau`, tabla `Recursos.Animaciones`
(ver el README principal, sección del combate). El puñetazo fuerte es la animación del cuarto golpe del combo, así que
su ID se pega en `Combo4`:

```lua
Recursos.Animaciones = {
	...
	Combo4 = "rbxassetid://1234567890", -- el ID que te dio Studio, con el prefijo rbxassetid://
}
```

No hay que tocar nada más: mientras `Combo4` valga `""` se usa la animación provisional hecha por código, y con un ID
el cliente (`VFX/Animador`) carga esa en su lugar, igual que con el resto de animaciones.

**Sincronización con el golpe.** El impacto de este puñetazo cae en el fotograma 16 (0,53 s), así que el Remate
(`Combo4` en `Datos/Poderes`) tiene `Tiempos.Carga = 0.53`: el servidor aplica el daño y el cliente lanza el efecto de
impacto justo cuando el puño llega. La animación provisional del Remate se retrasó igual (impacto en T = 0.53) para que
también cuadre mientras no haya ID. Si cambias el ritmo de la animación, cambia `Carga` a la vez. El Remate queda así más
pesado que los otros tres golpes del combo (que siguen siendo rápidos): es el golpe fuerte del final.

## Si algo sale mal en Studio

No he podido probar la importación en Studio desde este entorno (sin Studio), sino que he comprobado el `.fbx` volviéndolo
a importar en Blender (`herramientas/verificar_fbx.py`). Si al probarlo ves algo raro:

- **El personaje sale mirando hacia atrás o el golpe va en sentido contrario**: en `herramientas/exportar_fbx.py` cambia
  `axis_forward="Z"` por `"-Z"` y vuelve a generar.
- **La cadera se desplaza demasiado o muy poco**: el avance del cuerpo se anima en la traslación de `LowerTorso`
  (en studs de Blender: 1 stud = 0,28 m). Se puede suavizar en `CADERA_POS` de `herramientas/punetazo_fuerte.py`.
- **Sale un hueso de más o una pieza suelta**: importa el `solo_huesos`, que no lleva mallas, y no el de rig + cuerpo.

## Regenerar las animaciones

Requiere Python 3.13 (el de `bpy` 5.2) y las bibliotecas de `herramientas/requirements.txt`:

```bash
python3 -m venv .venv && .venv/bin/pip install -r animaciones/herramientas/requirements.txt
```

```bash
.venv/bin/python animaciones/herramientas/generar.py \
  --hoja animaciones/punetazo_fuerte_anime_hoja_de_contactos.png \
  --fbx animaciones/punetazo_fuerte_anime.fbx \
  --fbx-huesos animaciones/punetazo_fuerte_anime_solo_huesos.fbx \
  --blend animaciones/punetazo_fuerte_anime.blend
```

```bash
.venv/bin/python animaciones/herramientas/verificar_fbx.py animaciones/punetazo_fuerte_anime_solo_huesos.fbx
```

| Script | Para qué sirve |
| --- | --- |
| `rig_r15.py` | Crea los 16 huesos R15 (orientados con los ejes del mundo, como los Motor6D) y el cuerpo de cajas |
| `punetazo_fuerte.py` | Las claves y curvas de la animación, la cinemática inversa y el horneado. **Aquí se retoca el movimiento** |
| `hoja_contactos.py` | Render con Cycles (CPU) y montaje de la hoja de contactos |
| `exportar_fbx.py` | Exportación FBX con los ajustes para Roblox |
| `verificar_fbx.py` | Reimporta el FBX y comprueba huesos, jerarquía, duración y posiciones |
| `generar.py` | Lo ejecuta todo |

## Por qué no se usó un modelo de IA

Se intentó generar la base con un modelo de texto a movimiento y no fue posible en este entorno:

- **HY-Motion 1.0** (Tencent): los pesos están en Hugging Face, pero piden **24–26 GB de VRAM** (no hay GPU), el código
  de inferencia está en GitHub (bloqueado en el entorno) y además necesita Qwen3 y modelos corporales SMPL. Su licencia
  tampoco cubre la UE, el Reino Unido ni Corea del Sur.
- **MoMask** y **MDM**: repositorios en GitHub bloqueados y pesos en Hugging Face con acceso denegado.

Por eso el movimiento está escrito a mano en código (poses clave con easing e IK), no generado por IA.
