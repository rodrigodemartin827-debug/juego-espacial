"""
KeyframeSequence (.rbxmx) de las animaciones de la pistola, con lo que no tiene la de la #17 (`movimiento/rbxmx.py`):

  * PESOS por articulación (Pose.Weight). Un peso 0 significa «esta articulación no es de esta animación»: Roblox deja lo
    que pongan las animaciones de debajo (reposo, andar, correr). Así «apuntar» solo mueve el brazo derecho y se mezcla con
    cualquier movimiento, y la variante «móvil» del disparo no toca las piernas.
  * MARCADORES (KeyframeMarker): «Carga», «Disparo» (el momento de soltar) y «RetrocesoMax». En Roblox:
        pista:GetMarkerReachedSignal("Disparo"):Connect(...)
    para sacar el fogonazo, el proyectil y el temblor de cámara justo en ese fotograma.

La conversión de Blender a Roblox es la misma (reutiliza `rbxmx.transform`). Las articulaciones de peso 0 se escriben con
la pose neutra: así la secuencia, abierta en el Animation Editor, solo enseña lo que mueve.
"""

import xml.etree.ElementTree as ET

from mathutils import Matrix, Vector

import rbxmx as R
import rig_r6 as r6

NEUTRA = (Matrix.Identity(3), Vector((0.0, 0.0, 0.0)))


def _pose(padre, ref, nombre, rot, pos, peso):
    item = ET.SubElement(padre, "Item", {"class": "Pose", "referent": ref()})
    props = ET.SubElement(item, "Properties")
    cf = ET.SubElement(props, "CoordinateFrame", name="CFrame")
    for eje, v in zip("XYZ", pos):
        ET.SubElement(cf, eje).text = R._num(v)
    for i in range(3):
        for j in range(3):
            ET.SubElement(cf, f"R{i}{j}").text = R._num(rot[i][j])
    R._prop(props, "token", "EasingDirection", "0")
    R._prop(props, "token", "EasingStyle", "0")  # Linear: una clave por fotograma, con el easing ya aplicado
    R._prop(props, "string", "Name", nombre)
    R._prop(props, "float", "Weight", R._num(peso))
    return item


def escribir(ruta, nombre, calcular_pose, ultimo, fps, prioridad, bucle, pesos, marcadores=None):
    marcadores = marcadores or {}
    ref = R._Ref()
    raiz = ET.Element(
        "roblox",
        {
            "xmlns:xmime": "http://www.w3.org/2005/05/xmlmime",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "xsi:noNamespaceSchemaLocation": "http://www.roblox.com/roblox.xsd",
            "version": "4",
        },
    )
    seq = ET.SubElement(raiz, "Item", {"class": "KeyframeSequence", "referent": ref()})
    props = ET.SubElement(seq, "Properties")
    R._prop(props, "bool", "Loop", "true" if bucle else "false")
    R._prop(props, "string", "Name", nombre)
    R._prop(props, "token", "Priority", str(R.PRIORIDADES[prioridad]))
    for f in range(ultimo + 1):
        pose = calcular_pose(f)
        kf = ET.SubElement(seq, "Item", {"class": "Keyframe", "referent": ref()})
        kp = ET.SubElement(kf, "Properties")
        R._prop(kp, "string", "Name", marcadores[f][0][0] if f in marcadores else "Keyframe")
        R._prop(kp, "float", "Time", R._num(f / fps))
        for n, v in marcadores.get(f, []):
            mk = ET.SubElement(kf, "Item", {"class": "KeyframeMarker", "referent": ref()})
            mp = ET.SubElement(mk, "Properties")
            R._prop(mp, "string", "Name", n)
            R._prop(mp, "string", "Value", v)

        def datos(h):
            if pesos[h] == 0:
                return NEUTRA
            return R.transform(h, pose.q[h], pose.loc[h])

        raiz_pose = _pose(kf, ref, "HumanoidRootPart", *NEUTRA, pesos["HumanoidRootPart"])
        torso = _pose(raiz_pose, ref, "Torso", *datos("Torso"), pesos["Torso"])
        for h in R.HIJOS_DEL_TORSO:
            _pose(torso, ref, h, *datos(h), pesos[h])
    ET.indent(raiz, space="\t")
    ET.ElementTree(raiz).write(ruta, encoding="utf-8", xml_declaration=False)
    return ruta


def leer(ruta):
    """(propiedades, [(tiempo, nombre del fotograma, [marcadores], {pieza: ((rot, pos), padre)}, {pieza: peso})])."""
    arbol = ET.parse(ruta).getroot()
    seq = arbol.find("Item[@class='KeyframeSequence']")
    props = {e.get("name"): e.text for e in seq.find("Properties")}
    claves = []
    for kf in seq.findall("Item[@class='Keyframe']"):
        t = float(kf.find("Properties/float[@name='Time']").text)
        nombre = kf.find("Properties/string[@name='Name']").text
        marcas = [m.find("Properties/string[@name='Name']").text for m in kf.findall("Item[@class='KeyframeMarker']")]
        poses, pesos = {}, {}

        def recorrer(item, padre):
            n = R._nombre(item)
            poses[n] = (R._cframe(item), padre)
            pesos[n] = float(item.find("Properties/float[@name='Weight']").text)
            for hijo in item.findall("Item[@class='Pose']"):
                recorrer(hijo, n)

        for p in kf.findall("Item[@class='Pose']"):
            recorrer(p, None)
        claves.append((t, nombre, marcas, poses, pesos))
    return props, claves


def enmascarar(pose, pesos):
    """Copia de la pose con las articulaciones de peso 0 en neutro (lo que de verdad lleva el archivo)."""
    from ciclo import Pose

    out = Pose()
    for h in r6.ARTICULACIONES:
        if pesos[h] > 0:
            out.q[h] = pose.q[h].copy()
            out.loc[h] = pose.loc[h].copy()
    return out
