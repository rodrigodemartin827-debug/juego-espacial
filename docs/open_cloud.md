# Subir modelos con Open Cloud (sin importar a mano)

Los `.fbx` de una región se suben a Roblox con la API Open Cloud y después se insertan en Studio por su ID. Así no hay
que pasar cada pieza por el importador 3D.

```
.fbx  ──(herramientas/subir_modelos.luau)──▶  Roblox  ──(ID en datos/ids_modelos.json)──▶  Studio: sustituirDesdeNube
```

- `herramientas/subir_modelos.luau` (Lune) sube los archivos que han cambiado. Lo comprueba por su SHA-256. Apunta
  cada ID en `<región>/roblox/datos/ids_modelos.json`. Si un modelo ya tiene ID, lo **actualiza** y conserva el
  mismo ID.
- `src/shared/Herramientas/ModelosNube.luau` (solo Studio) carga cada ID y pone la MeshPart en lugar de la plantilla
  que tiene el mismo nombre.
- En la región 1, `EjemploArranque.sustituirDesdeNube()` lo junta todo: carga los IDs, sustituye las plantillas en
  Piezas, Terreno y Silueta y las prepara (atlas, colisión precisa, doble cara).

## 1. Crear la clave de API (una vez)

1. Entra en <https://create.roblox.com/dashboard/credentials?activeTab=ApiKeysTab> con tu cuenta.
2. Pulsa **Create API Key**.
3. **Name**: `juego-espacial-subir-modelos`. Si quieres, pon en la descripción: «Sube los .fbx de las regiones».
4. **Access Permissions** → **Select API System** → elige **Assets** → **Add API System**.
5. En **Select Operations** marca solo **Read** y **Write** (`asset:read` y `asset:write`). No añadas ningún otro
   sistema: con esto la clave solo puede subir y leer modelos. No puede tocar tus juegos, tu dinero ni tus datos.
6. **Security**:
   - Si tu conexión tiene IP fija, activa **Restrict IP addresses** y añade tu IP pública.
   - Si tu IP cambia (lo normal en casa), déjalo desactivado.
7. **Expiration**: pon una fecha. Por ejemplo, dentro de 90 días; luego se renueva desde la misma página.
   Además, una clave que no se usa en 60 días caduca sola.
8. Pulsa **Save & Generate key** y luego **Copy Key to Clipboard**.
   **No la pegues en el chat ni en ningún archivo.** Pásala directamente al paso 2.

## 2. Guardarla en una variable de entorno de Windows

Abre una ventana **nueva** de PowerShell: menú Inicio → «PowerShell». No uses el chat de Claude ni el prefijo `!`,
porque lo que escribas ahí queda en la conversación.

```powershell
$clave = Read-Host "Pega la clave de API" -AsSecureString
[Environment]::SetEnvironmentVariable("ROBLOX_API_KEY", [System.Net.NetworkCredential]::new("", $clave).Password, "User")
Remove-Variable clave
```

- `Read-Host -AsSecureString` no enseña lo que pegas (salen asteriscos) y no queda en el historial de PowerShell.
- La variable es de **tu usuario de Windows** (registro, `HKCU\Environment`): no está en el repositorio ni en
  ningún archivo del proyecto.

Después, tu ID de usuario de Roblox: es el número de la dirección de tu perfil (`roblox.com/users/<ID>/profile`).
No es secreto.

```powershell
[Environment]::SetEnvironmentVariable("ROBLOX_CREATOR_ID", "TU_ID_NUMERICO", "User")
```

Para comprobar que la clave está guardada **sin enseñarla**:

```powershell
if ([Environment]::GetEnvironmentVariable("ROBLOX_API_KEY", "User")) { "Clave guardada" } else { "No hay clave" }
```

Para subir a un grupo en vez de a tu cuenta, añade también `ROBLOX_GROUP_ID`. Para eso conviene usar una clave de
una cuenta dedicada del grupo; ver la documentación de Roblox sobre claves de grupo.

### Si la clave se filtra

En la misma página de claves: desactiva **Enable Key** o bórrala, crea una nueva y vuelve a hacer el paso 2. El
script la lee cada vez, así que no hay nada más que cambiar.

## 3. Uso

Desde la raíz del repositorio:

```powershell
# ¿Qué ha cambiado desde la última subida? (no sube nada)
lune run herramientas/subir_modelos modelos/region1_valle_del_alba/roblox

# Simular la subida de unos archivos concretos (no se conecta)
lune run herramientas/subir_modelos modelos/region1_valle_del_alba/roblox piezas/Puente.fbx --prueba

# Subirlos de verdad
lune run herramientas/subir_modelos modelos/region1_valle_del_alba/roblox piezas/Puente.fbx piezas/Puente__lejos.fbx

# Subir todo lo que haya cambiado
lune run herramientas/subir_modelos modelos/region1_valle_del_alba/roblox --todo
```

Luego, en Studio, en modo edición y desde la barra de comandos:

```lua
local EA = require(game.ReplicatedStorage.Region1.EjemploArranque)
EA.sustituirDesdeNube({ "piezas/Puente.fbx", "piezas/Puente__lejos.fbx" })  -- o sin lista: todas
```

y guardar el lugar.

### Cosas a tener en cuenta

- Límite de 20 MB por archivo.
- La API sube los modelos como paquetes; `ModelosNube` quita el enlace de paquete a la plantilla.
- La API de actualizar (PATCH) está en beta y solo admite `.fbx`. Si algún día falla, `--nuevo` crea un recurso
  nuevo con otro ID.
- El script nunca escribe la clave: solo la manda en la cabecera `x-api-key`. Si la variable se creó con la
  terminal ya abierta, la lee directamente de tu usuario de Windows, sin tener que reiniciar nada.
