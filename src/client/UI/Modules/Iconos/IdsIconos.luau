--!strict
--[[
	IdsIconos: ID de Roblox de cada icono y de cada pieza de arte de la interfaz.

	ESTE ARCHIVO LO REESCRIBE herramientas/iconos_ui/generar.mjs (conserva los IDs que ya tenga). Para añadir
	un icono, dibújalo en herramientas/iconos_ui/iconos.mjs (o arte.mjs) y vuelve a ejecutar el generador.

	Cómo rellenar los IDs (una vez, y cada vez que cambie un icono):
	  1. En Studio: View > Asset Manager > Bulk Import, y elige todos los PNG de
	     src/client/UI/Assets/IconPNGs y src/client/UI/Assets/ArtePNGs (súbelos al GRUPO del juego).
	  2. Clic derecho en cada imagen > Copy ID, y pégalo aquí como "rbxassetid://<número>".

	Mientras un ID esté vacío, IconBuilder dibuja en su lugar un marcador discreto (un rombo con el color del
	icono) y avisa una sola vez por la consola de qué iconos faltan. Nunca se ve un hueco vacío.
	-- TODO: Subir iconos y reemplazar los assetId vacíos.
]]

local IdsIconos = {}

-- Iconos de una sola tinta (blancos; se tiñen con ImageColor3). Origen: Assets/IconPNGs/<nombre>.png
IdsIconos.Iconos = {
	sidebar_personaje = "",
	sidebar_inventario = "",
	sidebar_poderes = "",
	sidebar_clan = "",
	sidebar_ranked = "",
	sidebar_indice = "",
	sidebar_mapa = "",
	sidebar_ajustes = "",
	sidebar_tienda = "",
	slot_casco = "",
	slot_armadura = "",
	slot_espada = "",
	slot_arma = "",
	slot_amuleto = "",
	slot_anillo = "",
	slot_cinturon = "",
	slot_botas = "",
	stat_fuerza = "",
	stat_aguante = "",
	stat_espada = "",
	stat_arma = "",
	stat_habilidad = "",
	ui_cerrar = "",
	ui_check = "",
	ui_candado = "",
	ui_estrella = "",
	ui_estrella_vacia = "",
	ui_moneda = "",
	ui_gema = "",
	ui_logros = "",
	ui_viajar = "",
	ui_posicion = "",
	ui_alerta = "",
	ui_holo_r6 = "",
	ui_interactuar = "",
	aj_graficos = "",
	aj_audio = "",
	aj_controles = "",
	aj_interfaz = "",
	aj_juego = "",
	raza_humano = "",
	raza_monstruo = "",
	hab_rayo = "",
	hab_trueno = "",
	hab_tormenta = "",
	hab_pulso = "",
	hab_aplastar = "",
	hab_singularidad = "",
	hab_combo = "",
	hab_escaner = "",
	hab_propulsor = "",
	hab_sigilo = "",
	hab_salto = "",
	hab_curar = "",
	hab_escudo = "",
	hab_aura = "",
	hab_dron = "",
	rango_bronce = "",
	rango_plata = "",
	rango_oro = "",
	rango_platino = "",
	rango_diamante = "",
	rango_maestro = "",
	rango_granmaestro = "",
	rango_estelar = "",
} :: { [string]: string }

-- Arte a color (objetos, criaturas, planetas, tienda). Origen: Assets/ArtePNGs/<nombre>.png
IdsIconos.Arte = {
	item_hierro = "",
	item_cobre = "",
	item_titanio = "",
	item_cristal = "",
	item_cristal_abisal = "",
	item_lingote_hierro = "",
	item_cable_cobre = "",
	item_lente_cristal = "",
	item_placa_titanio = "",
	item_nucleo_energia = "",
	item_espada_plasma = "",
	item_pistola_foton = "",
	item_casco_nova = "",
	item_peto_reactor = "",
	item_amuleto_vacio = "",
	item_anillo_estelar = "",
	item_cinturon_tactico = "",
	item_botas_gravitatorias = "",
	item_botiquin = "",
	item_celula_energia = "",
	item_chip_estelar = "",
	criatura_medusa_vacio = "",
	criatura_brincador_lanudo = "",
	criatura_acechador_abismo = "",
	criatura_reptador_lunar = "",
	planta_flor_estelar = "",
	planta_hongo_luminoso = "",
	planeta_nueva_tierra = "",
	planeta_umbra = "",
	planeta_verdalia = "",
	planeta_ignea = "",
	planeta_nerea = "",
	planeta_grisalla = "",
	skin_nebula = "",
	estela_aurora = "",
	aura_cosmica = "",
	pack_explorador = "",
	pase_x2 = "",
	pase_almacen = "",
	pase_vip = "",
} :: { [string]: string }

return IdsIconos
