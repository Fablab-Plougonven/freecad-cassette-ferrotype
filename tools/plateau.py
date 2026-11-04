"""Print plate: the six printed pieces in one Bambu Studio project (3MF), black PETG.

Each piece is turned so that its visible face, or its largest flat face, is on
the bed (WAY), laid on z = 0 and placed on the X1 Carbon's 256 x 256 plate
(clear of the excluded front-left corner). The 3MF is in Bambu Studio's own
project layout: per-object settings (walls, infill), and the two print pauses
for the embedded magnets (piece 2 and the lid) in
Metadata/custom_gcode_per_layer.xml, at the first layer above the ceiling of
the magnet seats.

The presets (cad/bambu/project_settings.config) are written once by Bambu
Studio's command line (--settings): X1 Carbon 0.4, 0.16mm Optimal, textured PEI,
Bambu PETG Basic black.

Run with FreeCAD's interpreter, after cad/build_cassette.py:
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/plateau.py [--settings] [--slice]
Writes exports/plateau/cassette_ferrotype.3mf and exports/plateau/stl/*.stl;
--slice also slices it with Bambu Studio and prints time, filament and pauses.
(--slice needs Bambu Studio's command line to write its own temporary files: run it
from a normal terminal, not from a sandbox.)
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import uuid
import zipfile
from xml.sax.saxutils import quoteattr

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD as App  # noqa: E402
import MeshPart  # noqa: E402

V = App.Vector
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FCSTD = os.path.join(ROOT, "exports", "cassette_ferrotype.FCStd")
OUT = os.path.join(ROOT, "exports", "plateau")
SETTINGS = os.path.join(ROOT, "cad", "bambu", "project_settings.config")

APP = "/Applications/BambuStudio.app"
PROFILES = os.path.join(APP, "Contents/Resources/profiles/BBL")
MACHINE = "Bambu Lab X1 Carbon 0.4 nozzle"
PROCESS = "0.16mm Optimal @BBL X1C"
FILAMENT = ("Bambu PETG Basic @BBL X1C", "#000000")
BED_TYPE = "Textured PEI Plate"

PLATE = 256.0
EXCLUDED = (0, 0, 18, 28)          # X1 Carbon: front-left corner (bed_exclude_area)
GAP = 6.0                          # between pieces, and to the plate edge

# body, file name, label, way it lies ("tel": as modelled, w = 0 on the bed;
# "retourne": turned over, its highest face on the bed), turned a quarter about z,
# per-object Bambu settings
PIECES = [
    ("Piece1_Interface", "piece1_interface", "Pièce 1 interface", "tel", False,
     [("wall_loops", "4")]),
    ("Piece2_CadreVerre", "piece2_cadre_verre", "Pièce 2 cadre verre", "retourne", False,
     [("wall_loops", "4")]),
    ("Piece3_Couvercle", "piece3_couvercle", "Pièce 3 couvercle", "retourne", False,
     [("wall_loops", "4"), ("sparse_infill_density", "50%")]),
    ("Ressort_Croix", "ressort_croix", "Ressort en croix", "retourne", False,
     [("sparse_infill_density", "100%")]),
    ("Glissiere_Verrou", "glissiere_verrou", "Glissière du verrou", "tel", True, []),
    ("Capot_Verrou", "capot_verrou", "Capot du verrou", "retourne", True, []),
]
# where each piece goes: lower-left corner of its footprint on the plate
SLOTS = {"piece1_interface": (24, 30), "piece3_couvercle": (24 + 91 + GAP + 4, 30),
         "piece2_cadre_verre": (24, 30 + 96 + GAP + 4), "ressort_croix": (125, 140),
         "glissiere_verrou": (125 + 54 + GAP, 140), "capot_verrou": (125 + 54 + GAP + 12 + GAP + 2, 140)}


# --- presets -----------------------------------------------------------------
def flattened(kind, name):
    """A system preset with its `inherits` chain merged in, as the command line needs it."""
    with open(os.path.join(PROFILES, kind, f"{name}.json")) as f:
        data = json.load(f)
    merged = flattened(kind, data["inherits"]) if data.get("inherits") else {}
    merged.update(data)
    merged.pop("inherits", None)
    return merged


def write_settings():
    """Bambu Studio's project settings for the plate, from its command line (a small cube sliced as a project)."""
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "machine.json"), "w") as f:
            json.dump(flattened("machine", MACHINE), f)
        with open(os.path.join(tmp, "process.json"), "w") as f:
            json.dump(flattened("process", PROCESS), f)
        fil = flattened("filament", FILAMENT[0])
        fil["filament_colour"] = [FILAMENT[1]]
        with open(os.path.join(tmp, "filament.json"), "w") as f:
            json.dump(fil, f)
        lines = ["solid cube"]
        v = [(dx, dy, dz) for dx in (0, 5) for dy in (0, 5) for dz in (0, 5)]
        for a, b, c, d in ((0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)):
            for t in ((a, b, c), (a, c, d)):
                lines += ["facet normal 0 0 0", "outer loop", *(f"vertex {v[i][0] + 100} {v[i][1] + 100} {v[i][2]}" for i in t),
                          "endloop", "endfacet"]
        with open(os.path.join(tmp, "cube.stl"), "w") as f:
            f.write("\n".join(lines + ["endsolid cube", ""]))
        cmd = [os.path.join(APP, "Contents/MacOS/BambuStudio"), "--arrange", "0", "--orient", "0",
               "--load-settings", f"{tmp}/machine.json;{tmp}/process.json", "--load-filaments", f"{tmp}/filament.json",
               "--load-filament-ids", "1", "--curr-bed-type", BED_TYPE, "--outputdir", tmp,
               "--export-3mf", "project.3mf", os.path.join(tmp, "cube.stl")]
        subprocess.run(cmd, cwd=tmp, check=True, capture_output=True)
        with zipfile.ZipFile(os.path.join(tmp, "project.3mf")) as z:
            settings = json.loads(z.read("Metadata/project_settings.config"))
    if settings.get("printer_settings_id") != MACHINE or settings.get("filament_colour") != [FILAMENT[1]]:
        raise SystemExit("unexpected presets in Bambu Studio's project")
    os.makedirs(os.path.dirname(SETTINGS), exist_ok=True)
    with open(SETTINGS, "w") as f:
        f.write(json.dumps(settings, indent=4, sort_keys=True) + "\n")
    print(f"{SETTINGS}: Bambu Studio {settings['version']}, {len(settings)} settings")


# --- layout ------------------------------------------------------------------
def laid(shape, way, quarter):
    s = shape.copy()
    if way == "retourne":
        s.rotate(V(0, 0, 0), V(0, 1, 0), 180)
    if quarter:
        s.rotate(V(0, 0, 0), V(0, 0, 1), 90)
    bb = s.optimalBoundingBox(True, False)
    s.translate(V(-bb.XMin, -bb.YMin, -bb.ZMin))
    return s


def bed_area(shape):
    return sum(f.Area for f in shape.Faces if f.Surface.__class__.__name__ == "Plane"
               and abs(f.BoundBox.ZMin) < 1e-4 and abs(f.BoundBox.ZMax) < 1e-4)


def check_layout(boxes):
    """Every footprint on the plate, GAP from its edges, from the excluded corner and from the others."""
    problems = []
    names = list(boxes)
    for i, n in enumerate(names):
        x0, y0, x1, y1 = boxes[n]
        if x0 < GAP or y0 < GAP or x1 > PLATE - GAP or y1 > PLATE - GAP:
            problems.append(f"{n} off the plate")
        ex0, ey0, ex1, ey1 = EXCLUDED
        if x0 < ex1 + GAP and y0 < ey1 + GAP:
            problems.append(f"{n} too close to the excluded corner")
        for m in names[i + 1:]:
            a0, b0, a1, b1 = boxes[m]
            if x0 < a1 + GAP and a0 < x1 + GAP and y0 < b1 + GAP and b0 < y1 + GAP:
                problems.append(f"{n} and {m} closer than {GAP} mm")
    return problems


# --- 3MF ---------------------------------------------------------------------
def _uuid(name):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"fablab-plougonven/cassette-ferrotype/{name}"))


_HEAD = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
         'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
         'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
         'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n')
_ID = "1 0 0 0 1 0 0 0 1 0 0 0"


def write_3mf(path, objects, pauses):
    """objects: [(file name, label, mesh, settings)], vertices in plate coordinates; pauses: [top_z]."""
    with open(SETTINGS) as f:
        project = json.load(f)
    files, resources, items, cfg, rels = {}, [], [], [], []
    for k, (name, label, mesh, settings) in enumerate(objects, 1):
        sub = f"3D/Objects/object_{k}.model"
        pid, own = 2 * k - 1, 2 * k
        pts, tris = mesh.Topology
        body = [f' <object id="{pid}" p:UUID="{_uuid(name)}" type="model">', "  <mesh>", "   <vertices>"]
        body += [f'    <vertex x="{p.x:.4f}" y="{p.y:.4f}" z="{p.z:.4f}"/>' for p in pts]
        body += ["   </vertices>", "   <triangles>"]
        body += [f'    <triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in tris]
        body += ["   </triangles>", "  </mesh>", " </object>"]
        files[sub] = (_HEAD + ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n <resources>\n'
                      + "\n".join(body) + "\n </resources>\n <build/>\n</model>\n")
        rels.append(f' <Relationship Target="/{sub}" Id="rel-{k}" '
                    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
        resources.append(f'  <object id="{own}" p:UUID="{_uuid(name + "/o")}" type="model">\n   <components>\n'
                         f'    <component p:path="/{sub}" objectid="{pid}" p:UUID="{_uuid(name + "/c")}" transform="{_ID}"/>\n'
                         "   </components>\n  </object>")
        items.append(f'  <item objectid="{own}" p:UUID="{_uuid(name + "/i")}" transform="{_ID}" printable="1"/>')
        cfg += [f'  <object id="{own}">', f'    <metadata key="name" value={quoteattr(label)}/>',
                '    <metadata key="extruder" value="1"/>']
        cfg += [f'    <metadata key="{key}" value={quoteattr(val)}/>' for key, val in settings]
        cfg += [f'    <part id="{pid}" subtype="normal_part">', f'      <metadata key="name" value={quoteattr(name)}/>',
                '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>',
                '      <metadata key="extruder" value="1"/>', "    </part>", "  </object>"]
    files["3D/3dmodel.model"] = (
        _HEAD + f' <metadata name="Application">BambuStudio-{project["version"]}</metadata>\n'
        ' <metadata name="BambuStudio:3mfVersion">1</metadata>\n'
        ' <metadata name="Title">Cassette ferrotype</metadata>\n'
        " <resources>\n" + "\n".join(resources) + "\n </resources>\n"
        f' <build p:UUID="{_uuid("build")}">\n' + "\n".join(items) + "\n </build>\n</model>\n")
    files["3D/_rels/3dmodel.model.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        + "\n".join(rels) + "\n</Relationships>\n")
    files["Metadata/model_settings.config"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "\n".join(cfg) + "\n"
        '  <plate>\n    <metadata key="plater_id" value="1"/>\n'
        '    <metadata key="plater_name" value="Cassette ferrotype"/>\n    <metadata key="locked" value="false"/>\n'
        "  </plate>\n</config>\n")
    layers = "\n".join(f'<layer top_z="{z:.2f}" type="1" extruder="1" color="" extra="" gcode="M400 U1"/>'
                       for z in pauses)
    files["Metadata/custom_gcode_per_layer.xml"] = (
        '<?xml version="1.0" encoding="utf-8"?>\n<custom_gcodes_per_layer>\n<plate>\n<plate_info id="1"/>\n'
        f'{layers}\n<mode value="SingleExtruder"/>\n</plate>\n</custom_gcodes_per_layer>\n')
    files["Metadata/project_settings.config"] = json.dumps(project, indent=4, sort_keys=True) + "\n"
    files["[Content_Types].xml"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">\n'
        ' <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>\n'
        ' <Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>\n'
        "</Types>\n")
    files["_rels/.rels"] = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">\n'
        ' <Relationship Target="/3D/3dmodel.model" Id="rel-1" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>\n</Relationships>\n')
    order = ["[Content_Types].xml", "_rels/.rels", "3D/3dmodel.model", "3D/_rels/3dmodel.model.rels",
             *sorted(n for n in files if n.startswith("3D/Objects/")), "Metadata/model_settings.config",
             "Metadata/project_settings.config", "Metadata/custom_gcode_per_layer.xml"]
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for n in order:
            z.writestr(n, files[n])


def pause_layers(project, ceilings):
    """First layer whose top is above each magnet-seat ceiling (the seat is still open below it)."""
    h0, h = float(project["initial_layer_print_height"]), float(project["layer_height"])
    out = []
    for c in ceilings:
        k = math.floor((c - h0) / h + 1e-6) + 1
        out.append(round(h0 + k * h, 4))
    return out


def slice_plate(path):
    """Slice with Bambu Studio's command line; print time, filament and the pauses found in the G-code."""
    folder = os.path.dirname(path)
    cmd = [os.path.join(APP, "Contents/MacOS/BambuStudio"), "--slice", "1", "--outputdir", folder,
           "--export-3mf", "sliced.3mf", path]
    r = subprocess.run(cmd, cwd=folder, capture_output=True, text=True)
    sliced = os.path.join(folder, "sliced.3mf")
    if r.returncode != 0 or not os.path.exists(sliced):
        print("slicing failed:", r.returncode, (r.stdout + r.stderr)[-1500:])
        return False
    with zipfile.ZipFile(sliced) as z:
        gcode = z.read("Metadata/plate_1.gcode").decode()
    os.remove(sliced)
    info = [ln for ln in gcode.splitlines() if ln.startswith(("; model printing time", "; total filament weight",
                                                                "; total estimated time"))]
    z_now, pauses = 0.0, []
    for ln in gcode.splitlines():
        if ln.startswith("; Z_HEIGHT:"):
            z_now = float(ln.split(":")[1])
        elif ln.startswith("M400 U1"):
            pauses.append(z_now)
    print("\n".join(info))
    print("pauses (M400 U1) after the layer at z:", pauses)
    return pauses


def main(argv):
    if "--settings" in argv or not os.path.exists(SETTINGS):
        write_settings()
    with open(SETTINGS) as f:
        project = json.load(f)
    doc = App.openDocument(FCSTD)
    sheet = doc.getObject("Parametres")
    get = lambda n: float(sheet.get(n))  # noqa: E731
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "stl"))
    objects, boxes, ok = [], {}, True
    print(f"{'piece':20s} {'lies':9s} {'footprint (mm)':>16s} {'height':>7s} {'on the bed':>11s}")
    for body, name, label, way, quarter, settings in PIECES:
        s = laid(doc.getObject(body).Shape, way, quarter)
        bb = s.optimalBoundingBox(True, False)
        x, y = SLOTS[name]
        s.translate(V(x, y, 0))
        boxes[name] = (x, y, x + bb.XLength, y + bb.YLength)
        area = bed_area(s)
        ok &= area > 0
        print(f"{name:20s} {way:9s} {bb.XLength:7.1f} x {bb.YLength:6.1f} {bb.ZLength:7.2f} {area:8.0f} mm2")
        mesh = MeshPart.meshFromShape(Shape=s, LinearDeflection=0.02, AngularDeflection=0.15, Relative=False)
        zmin = min(p.z for p in mesh.Topology[0])
        if abs(zmin) > 1e-3:
            ok = False
            print(f"  {name}: lowest point at z {zmin:.3f}  <-- !")
        if mesh.hasNonManifolds():
            ok = False
            print(f"  {name}: non-manifold mesh  <-- !")
        mesh.write(os.path.join(OUT, "stl", f"{name}.stl"))
        objects.append((name, label, mesh, settings))
    problems = check_layout(boxes)
    for p in problems:
        print("layout:", p, " <-- !")
    ok &= not problems
    # magnet seats: ceilings measured from the bed (piece 2 and the lid lie on their faces at the magnet skins)
    ceilings = {"piece2_cadre_verre": get("aimant_peau") + get("aimant_epaisseur") + get("aimant_jeu"),
                "piece3_couvercle": get("couvercle_hauteur") - get("aimant_peau")}
    pauses = pause_layers(project, sorted(ceilings.values()))
    for (n, c), z in zip(sorted(ceilings.items(), key=lambda kv: kv[1]), pauses):
        top = c - get("aimant_jeu")
        print(f"pause for the magnets of {n}: seat closed at {c:.2f}, magnet top at {top:.2f}, "
              f"pause before the layer ending at {z:.2f} (nozzle at {z - float(project['layer_height']):.2f})")
    path = os.path.join(OUT, "cassette_ferrotype.3mf")
    write_3mf(path, objects, pauses)
    App.closeDocument(doc.Name)
    print("written", os.path.relpath(path, ROOT))
    if "--slice" in argv:
        found = slice_plate(path)
        ok &= bool(found) and len(found) == len(pauses)
    print("PLATE OK" if ok else "PLATE PROBLEMS", flush=True)
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1:]) else 1)
