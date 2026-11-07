"""
Escena de Blender para ver el disparo con la pistola en la mano: el R6 animado (rig_r6 + la animación horneada), la
pistola importada de su FBX (con las texturas del atlas) puesta en la mano derecha, y los efectos de ese instante
(fogonazo, proyectil, chispas de la bobina, destello del núcleo) para las hojas de contactos y los GIF.

La pistola NO va unida al rig: en cada fotograma se calcula dónde está la mano con la misma cinemática de la animación
(Pose.mundo) y se coloca la pistola con el Agarre en el extremo del brazo, que es lo que hará Roblox con
`RightGripAttachment` y `Tool.Grip`. Las piezas que se mueven (rueda, depósito, anillos, núcleo) se mueven con las mismas
curvas que van a `datos/piezas_*.json`.

Los renders llevan un resplandor (bloom) hecho con Pillow, que es lo que hace el neón en Roblox con Lighting.Bloom.
"""

import json
import math
import os
import random

import bpy
from mathutils import Matrix, Vector
from PIL import Image, ImageChops, ImageDraw, ImageFilter

import disparo as D
import render_mov
import rig_r6 as r6

E = r6.ESTUDIO
VELOCIDAD_PROYECTIL = 70.0  # studs/s (la misma de portal_fases.py)
AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.normpath(os.path.join(AQUI, "..", "..", ".."))
MODELOS = os.path.join(RAIZ, "modelos", "pistola_portales")
NOMBRES = {"chatarra": "Chatarra", "vip": "VIP"}

# Piezas que se mueven por su cuenta (nombre -> pieza a la que siguen)
SIGUE = {"Chatarra_Deposito": "Chatarra_DepositoMarco", "Chatarra_Combustible": "Chatarra_DepositoMarco",
         "VIP_Anillo1_Luz": "VIP_Anillo1", "VIP_Anillo2_Luz": "VIP_Anillo2", "VIP_Anillo3_Luz": "VIP_Anillo3"}


def srgb(hexa):
    h = hexa.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c)


def de_roblox(v):
    """Posición en el marco del modelo de Roblox (los JSON de las pistolas) -> Blender. Roblox = (-x, z, y) de Blender."""
    return Vector((-v[0], v[2], v[1]))


def _importar_fbx(ruta):
    """Importa un FBX de modelos/ y deja las mallas con su transformación aplicada (marco de Blender: Z arriba, el cañón
    hacia -Y), con la matriz del objeto en la identidad. Los Empty se quedan con su posición en ese marco."""
    antes = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=ruta, axis_forward="-Z", axis_up="Y")
    nuevos = [o for o in bpy.data.objects if o not in antes]
    for o in nuevos:
        mw = o.matrix_world.copy()
        if o.type == "MESH":
            o.data.transform(mw)
            o.parent = None
            o.matrix_world = Matrix.Identity(4)
        else:
            o.parent = None
            o.matrix_world = mw
            o.location = mw.translation
    return nuevos


def _material_neon(nombre, hexa, fuerza=5.0):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    col = srgb(hexa)
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Emission Color"].default_value = (*col, 1)
    b.inputs["Emission Strength"].default_value = fuerza
    return m


def _material_cristal(nombre, hexa):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*srgb(hexa), 1)
    b.inputs["Roughness"].default_value = 0.04
    b.inputs["Transmission Weight"].default_value = 1.0
    b.inputs["IOR"].default_value = 1.2
    return m


def _material_atlas(nombre, carpeta, base):
    m = bpy.data.materials.new(nombre)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]

    def tex(sufijo, color):
        img = bpy.data.images.load(os.path.join(carpeta, "texturas", f"{base}_{sufijo}.png"))
        img.colorspace_settings.name = "sRGB" if color else "Non-Color"
        n = nt.nodes.new("ShaderNodeTexImage")
        n.image = img
        return n

    nt.links.new(tex("color", True).outputs["Color"], b.inputs["Base Color"])
    nt.links.new(tex("metal", False).outputs["Color"], b.inputs["Metallic"])
    nt.links.new(tex("rugosidad", False).outputs["Color"], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tex("normal", False).outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    return m


class Pistola:
    """La pistola importada, con materiales, listas de piezas móviles y sus pivotes."""

    def __init__(self, estilo):
        self.estilo = estilo
        nombre = NOMBRES[estilo]
        carpeta = os.path.join(MODELOS, estilo)
        with open(os.path.join(carpeta, f"Pistola_{nombre}.json"), encoding="utf-8") as f:
            self.datos = json.load(f)
        objs = _importar_fbx(os.path.join(carpeta, f"Pistola_{nombre}.fbx"))
        self.partes = {o.name: o for o in objs if o.type == "MESH"}
        self.vacios = {o.name: o.location.copy() for o in objs if o.type == "EMPTY"}
        for o in objs:
            if o.type == "EMPTY":
                bpy.data.objects.remove(o)
        atlas = _material_atlas(f"atlas_{estilo}", carpeta, nombre)
        self.neon = {}
        for n, o in self.partes.items():
            o.data.materials.clear()
            if n in self.datos["neon"]:
                m = _material_neon(f"neon_{n}", self.datos["neon"][n])
                self.neon[n] = (m, self.datos["neon"][n])
            elif n in self.datos["cristal"]:
                m = _material_cristal(f"cristal_{n}", self.datos["cristal"][n]["color"])
            else:
                m = atlas
            o.data.materials.append(m)
        self.pivotes = {n: de_roblox(v) for n, v in self.datos["pivotes_giro"].items()}
        self.agarre = self.vacios["Agarre"]
        self.boca = self.vacios["Boca"]

    # ------------------------------------------------------------------------------------------ colocación
    def matriz_base(self, pose):
        """Matriz del mundo de la pistola: el Agarre en el extremo del brazo derecho y el cañón hacia delante."""
        pos, rot = pose.mundo("Right Arm")
        return (Matrix.Translation(pos * E) @ rot.to_matrix().to_4x4() @ Matrix.Translation(Vector((-0.5, 0.0, -1.5)) * E)
                @ Matrix.Rotation(math.pi / 2, 4, "X") @ Matrix.Scale(E, 4) @ Matrix.Translation(-self.agarre))

    def _giro(self, nombre, eje, grados):
        p = self.pivotes[nombre]
        return Matrix.Translation(p) @ Matrix.Rotation(math.radians(grados), 4, eje) @ Matrix.Translation(-p)

    def colocar(self, pose, piezas):
        """`piezas` = lo que devuelven disparo.piezas_chatarra / piezas_vip / piezas_apuntar."""
        M = self.matriz_base(pose)
        mov = {n: Matrix.Identity(4) for n in self.partes}
        if self.estilo == "chatarra":
            mov["Chatarra_Rueda"] = self._giro("Chatarra_Rueda", "X", piezas.get("rueda", 0.0))
            salto = Matrix.Translation((0, 0, piezas.get("deposito", 0.0)))
            for n in ("Chatarra_DepositoMarco", "Chatarra_Deposito", "Chatarra_Combustible"):
                mov[n] = salto
        else:
            for i, g in enumerate(piezas.get("anillos", (0, 0, 0)), start=1):
                m = self._giro(f"VIP_Anillo{i}", "Y", g)
                mov[f"VIP_Anillo{i}"] = m
                mov[f"VIP_Anillo{i}_Luz"] = m
            c = self.vacios["Nucleo"]
            esc = piezas.get("nucleo_escala", 1.0)
            mov["VIP_Nucleo"] = Matrix.Translation(c) @ Matrix.Scale(esc, 4) @ Matrix.Translation(-c)
            m, base = self.neon["VIP_Nucleo"]
            blanco = piezas.get("nucleo_blanco", 0.0)
            b = m.node_tree.nodes["Principled BSDF"]
            col = [x + (1 - x) * blanco for x in srgb(base)]
            b.inputs["Emission Color"].default_value = (*col, 1)
            b.inputs["Emission Strength"].default_value = 5.0 + 25.0 * blanco
        for n, o in self.partes.items():
            o.matrix_world = M @ mov[n]
        return M

    def punto_mundo(self, M, nombre):
        return M @ self.vacios[nombre]


class Efectos:
    """Fogonazo y proyectil (mallas de modelos/pistola_portales/vfx) y chispas de la bobina (rayitas, solo para la hoja)."""

    def __init__(self, estilo):
        self.estilo = estilo
        nombre = NOMBRES[estilo]
        objs = _importar_fbx(os.path.join(MODELOS, "vfx", estilo, f"Disparo_{nombre}.fbx"))
        self.mallas = {o.name: o for o in objs if o.type == "MESH"}
        for o in objs:
            if o.type == "EMPTY":
                bpy.data.objects.remove(o)
        colores = {"chatarra": {"Fogonazo_Chatarra": "#C8FF8A", "Proyectil_Chatarra": "#7DFF3A"},
                   "vip": {"Fogonazo_VIP": "#E8FBFF", "Proyectil_VIP_Nucleo": "#C46BFF", "Proyectil_VIP_Aro": "#3FF0FF"}}[estilo]
        for n, o in self.mallas.items():
            o.data.materials.clear()
            o.data.materials.append(_material_neon(f"fx_{n}", colores[n], 9.0))
            o.hide_render = True
        self.temporales = []
        self.mat_chispa = _material_neon("chispa", "#E6FF7A" if estilo == "chatarra" else "#FFFFFF", 14.0)
        self.mat_estela = _material_neon("estela", "#7DFF3A" if estilo == "chatarra" else "#7FFBFF", 6.0)

    def limpiar(self):
        for o in self.temporales:
            bpy.data.objects.remove(o)
        self.temporales = []
        for o in self.mallas.values():
            o.hide_render = True

    def _chispa(self, pos, direccion, largo):
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=pos)
        o = bpy.context.active_object
        o.scale = (0.012 * E * 4, largo * E, 0.012 * E * 4)
        o.rotation_euler = Vector((0, 1, 0)).rotation_difference(direccion).to_euler()
        o.data.materials.append(self.mat_chispa)
        self.temporales.append(o)

    def poner(self, f, pistola, M, M_disparo, pieza):
        """Los efectos del fotograma f. M = matriz de la pistola ahora; M_disparo = la del fotograma de soltar."""
        self.limpiar()
        F = D.FOTOGRAMA_DISPARO
        t = f - F
        boca = pistola.boca
        if 0 <= t <= 2:  # fogonazo pegado a la boca, de más a menos
            n = "Fogonazo_Chatarra" if self.estilo == "chatarra" else "Fogonazo_VIP"
            o = self.mallas[n]
            esc = (1.0, 0.75, 0.4)[t] * (1.0 if self.estilo == "chatarra" else 0.9)
            o.matrix_world = M @ Matrix.Translation(boca) @ Matrix.Scale(esc, 4)
            o.hide_render = False
        if t >= 1:  # proyectil: sale en la dirección en que apuntaba al soltar
            origen = M_disparo @ boca
            direccion = (M_disparo.to_3x3() @ Vector((0, -1, 0))).normalized()
            pos = origen + direccion * (1.3 + VELOCIDAD_PROYECTIL / D.FPS * (t - 1)) * E
            R = M_disparo.to_3x3().normalized().to_4x4()
            for n, o in self.mallas.items():
                if n.startswith("Proyectil"):
                    o.matrix_world = Matrix.Translation(pos) @ R @ Matrix.Scale(E, 4)
                    o.hide_render = False
            # estela (el Beam/Trail del proyectil en Roblox): una raya detrás, hacia la boca, de 3,5 studs como mucho
            largo = min(3.5, 1.3 + VELOCIDAD_PROYECTIL / D.FPS * (t - 1)) * E
            bpy.ops.mesh.primitive_cube_add(size=1.0, location=pos - direccion * largo / 2)
            est = bpy.context.active_object
            est.scale = (0.09 * E, 0.09 * E, largo)
            est.rotation_euler = Vector((0, 0, 1)).rotation_difference(direccion).to_euler()
            est.data.materials.append(self.mat_estela)
            self.temporales.append(est)
        if self.estilo == "chatarra" and pieza.get("chispas", 0.0) > 0:  # chispas de la bobina
            rng = random.Random(100 + f)
            gran = pieza["chispas"] >= 1.0
            puntos = [n for n in pistola.vacios if n.startswith("Chispas_Bobina")]
            for n in puntos:
                p0 = pistola.punto_mundo(M, n)
                for _ in range(8 if gran else 2):
                    d = Vector((rng.uniform(-1, 1), rng.uniform(-0.6, 1), rng.uniform(-0.2, 1.4))).normalized()
                    alcance = rng.uniform(0.2, 0.9) * (1 + 0.5 * max(t, 0))
                    self._chispa(p0 + d * alcance * E, d, rng.uniform(0.12, 0.3))


# --------------------------------------------------------------------------------------------------------------
# Render con resplandor
# --------------------------------------------------------------------------------------------------------------


def resplandor(ruta, fuerza=0.9):
    """Bloom: las zonas muy claras (el neón) se desenfocan y se suman a la imagen."""
    img = Image.open(ruta).convert("RGB")
    brillo = img.point(lambda v: 0 if v < 205 else min(255, int((v - 205) * 5.0)))
    halo = ImageChops.add(brillo.filter(ImageFilter.GaussianBlur(5)), brillo.filter(ImageFilter.GaussianBlur(16)))
    halo = halo.point(lambda v: min(255, int(v * fuerza)))
    ImageChops.screen(img, halo).save(ruta)


class Escena:
    """R6 con la animación horneada + pistola + efectos + cámara. `render(f, vista)` devuelve la ruta del PNG."""

    def __init__(self, estilo, calcular_pose, ultimo, calcular_piezas, directorio, muestras=16, rapido=False,
                 con_efectos=True):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scn = bpy.context.scene
        scn.unit_settings.system = "METRIC"
        scn.unit_settings.scale_length = 1.0
        self.armature, self.mallas = r6.construir_rig()
        import ciclo

        ciclo.hornear(self.armature, "vista", calcular_pose, ultimo, D.FPS)
        self.pistola = Pistola(estilo)
        self.efectos = Efectos(estilo) if con_efectos else None
        render_mov.PUNTO_MIRADO.z = 0.86  # un poco más alto que en el andar: el brazo sube con el retroceso
        for v in render_mov.VISTAS:  # y algo más lejos, para que quepa el brazo levantado (se aplica una sola vez)
            if not getattr(render_mov, "_alejadas", False):
                render_mov.VISTAS[v] = render_mov.VISTAS[v] * 1.13
        render_mov._alejadas = True
        self.cam, self.mapeo = render_mov.preparar_escena(1.0, muestras)
        self.directorio = directorio
        os.makedirs(directorio, exist_ok=True)
        self.calcular_pose = calcular_pose
        self.calcular_piezas = calcular_piezas
        self.rutas = {}
        self.M_disparo = self.pistola.matriz_base(calcular_pose(D.FOTOGRAMA_DISPARO))
        if rapido:
            scn.render.resolution_x, scn.render.resolution_y = int(render_mov.ANCHO * 0.7), int(render_mov.ALTO * 0.7)

    def render(self, f, vista, prefijo=""):
        clave = (prefijo, vista, f)
        if clave in self.rutas:
            return self.rutas[clave]
        scn = bpy.context.scene
        scn.frame_set(f)
        pose = self.calcular_pose(f)
        pieza = self.calcular_piezas(f)
        M = self.pistola.colocar(pose, pieza)
        if self.efectos:
            self.efectos.poner(f, self.pistola, M, self.M_disparo, pieza)
        self.cam.location = render_mov.VISTAS[vista]
        ruta = os.path.join(self.directorio, f"{prefijo}{vista.replace('/', '-')}_{f:03d}.png")
        scn.render.filepath = ruta
        bpy.ops.render.render(write_still=True)
        resplandor(ruta)
        self.rutas[clave] = ruta
        return ruta


# --------------------------------------------------------------------------------------------------------------
# Hojas y GIF
# --------------------------------------------------------------------------------------------------------------


def _fuente(tam):
    return render_mov._fuente(tam)


def hoja(filas, columnas, salida, titulo, etiquetas_filas):
    """filas: lista de listas de rutas (una fila por (estilo, vista)); columnas: [(fotograma, nombre)]."""
    primera = Image.open(filas[0][0])
    an, al = primera.size
    izq, arriba = 190, 84
    img = Image.new("RGB", (izq + an * len(columnas), arriba + al * len(filas)), (24, 26, 32))
    d = ImageDraw.Draw(img)
    d.text((10, 8), titulo, fill=(255, 255, 255), font=_fuente(22))
    for i, (f, nombre) in enumerate(columnas):
        x = izq + i * an
        d.text((x + 8, arriba - 50), f"f{f}  ({f / D.FPS:.2f} s)", fill=(255, 210, 90), font=_fuente(17))
        if nombre:
            d.text((x + 8, arriba - 26), nombre, fill=(220, 220, 230), font=_fuente(14))
    for j, fila in enumerate(filas):
        y = arriba + j * al
        for k, linea in enumerate(etiquetas_filas[j].split("\n")):
            d.text((8, y + al // 2 - 22 + k * 20), linea, fill=(255, 255, 255) if k == 0 else (190, 196, 210),
                   font=_fuente(16 if k == 0 else 13))
        for i, ruta in enumerate(fila):
            img.paste(Image.open(ruta).convert("RGB"), (izq + i * an, y))
    img.save(salida)
    return salida


def hoja_libre(filas, nombres, salida, titulo, etiquetas_filas):
    """Como `hoja`, pero las columnas solo llevan un nombre (las fases del portal)."""
    primera = Image.open(filas[0][0])
    an, al = primera.size
    izq, arriba = 150, 70
    img = Image.new("RGB", (izq + an * len(nombres), arriba + al * len(filas)), (24, 26, 32))
    d = ImageDraw.Draw(img)
    d.text((10, 8), titulo, fill=(255, 255, 255), font=_fuente(20))
    for i, nombre in enumerate(nombres):
        d.text((izq + i * an + 8, arriba - 26), nombre, fill=(255, 210, 90), font=_fuente(16))
    for j, fila in enumerate(filas):
        y = arriba + j * al
        for k, linea in enumerate(etiquetas_filas[j].split("\n")):
            d.text((8, y + al // 2 - 22 + k * 20), linea, fill=(255, 255, 255) if k == 0 else (190, 196, 210),
                   font=_fuente(15 if k == 0 else 13))
        for i, ruta in enumerate(fila):
            img.paste(Image.open(ruta).convert("RGB"), (izq + i * an, y))
    img.save(salida)
    return salida


def gif(rutas_por_vista, fotogramas, salida, fps, rotulo="", escala=0.7):
    """GIF en bucle; `rutas_por_vista` = [[ruta por fotograma] por vista], las vistas una al lado de otra."""
    fuente = _fuente(14)
    cuadros = []
    for i in range(len(fotogramas)):
        imgs = [Image.open(v[i]).convert("RGB") for v in rutas_por_vista]
        lienzo = Image.new("RGB", (sum(x.width for x in imgs), imgs[0].height))
        x = 0
        for im in imgs:
            lienzo.paste(im, (x, 0))
            x += im.width
        if rotulo:
            ImageDraw.Draw(lienzo).text((8, 6), rotulo, fill=(20, 22, 30), font=fuente)
        lienzo = lienzo.resize((int(lienzo.width * escala), int(lienzo.height * escala)), Image.LANCZOS)
        cuadros.append(lienzo.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE))
    paso = fotogramas[1] - fotogramas[0]
    cuadros[0].save(salida, save_all=True, append_images=cuadros[1:], duration=max(10, round(1000 * paso / fps / 10) * 10),
                    loop=0, optimize=True)
    return salida
