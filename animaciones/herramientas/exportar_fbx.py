"""
Exporta la animación a FBX con los ajustes que necesita el importador de animaciones de Roblox.

Ajustes que importan:
  * add_leaf_bones=False: sin huesos extra al final de cada cadena (Roblox los tomaría por partes).
  * Eje arriba = Y y delante = Z (el personaje de Blender mira a -Y, así que en el FBX mira a -Z, como en Roblox).
  * Un fotograma clave por fotograma (bake_anim_simplify_factor=0): conserva los easing tal cual, porque Roblox
    no importa curvas Bézier de Blender, solo los valores de cada clave.
  * Solo la acción activa y sin pistas NLA, para que el FBX lleve una única animación.
"""

import bpy


def exportar(armature, mallas, ruta_con_malla=None, ruta_solo_huesos=None):
    comunes = dict(
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        bake_space_transform=False,
        axis_forward="Z",
        axis_up="Y",
        use_armature_deform_only=False,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        armature_nodetype="NULL",
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,
        mesh_smooth_type="FACE",
        use_mesh_modifiers=True,
        embed_textures=False,
        path_mode="AUTO",
    )

    def _exportar(ruta, objetos, tipos):
        bpy.ops.object.select_all(action="DESELECT")
        for o in objetos:
            o.select_set(True)
        bpy.context.view_layer.objects.active = armature
        bpy.ops.export_scene.fbx(filepath=ruta, **{**comunes, "object_types": tipos})
        print("[ok] FBX:", ruta)

    if ruta_con_malla:
        _exportar(ruta_con_malla, [armature, *mallas], {"ARMATURE", "MESH"})
    if ruta_solo_huesos:
        _exportar(ruta_solo_huesos, [armature], {"ARMATURE"})
