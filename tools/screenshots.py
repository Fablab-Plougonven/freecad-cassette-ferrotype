"""Screenshots of the cassette, rendered by the FreeCAD GUI.

Run with the GUI binary (a window opens for a few seconds):
  /Applications/FreeCAD.app/Contents/MacOS/FreeCAD tools/screenshots.py
"""
import os

import FreeCAD as App
import FreeCADGui as Gui

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FCSTD = os.path.join(ROOT, "exports", "cassette_ferrotype.FCStd")
DOCS = os.path.join(ROOT, "docs")
V = App.Vector


def look_from(view, to_camera, up=V(0, 1, 0)):
    z = to_camera.normalize()
    x = up.cross(z).normalize()
    y = z.cross(x)
    m = App.Matrix(x.x, y.x, z.x, 0, x.y, y.y, z.y, 0, x.z, y.z, z.z, 0, 0, 0, 0, 1)
    view.setCameraOrientation(App.Rotation(m))
    view.fitAll()


import traceback
try:
    doc = App.openDocument(FCSTD)
    Gui.updateGui()
    view = Gui.activeDocument().activeView()
    view.setCameraType("Perspective")
    for o in doc.Objects:
        if o.Name.startswith("Volet"):
            o.ViewObject.Visibility = False
    # assembled, rear three-quarter (photographer side)
    look_from(view, V(0.9, 0.55, 1.2))
    view.saveImage(os.path.join(DOCS, "vue-assemblee.png"), 1600, 1100, "White")
    # exploded in assembly order, from the body side (w = 0) to the lid; dark slide pulled out to the left
    offsets = {"Piece1_Interface": (0, 0), "Glissiere_Verrou": (0, 12), "Capot_Verrou": (0, 22),
               "Volet": (-60, 30), "Piece2_CadreVerre": (0, 36), "Verre_57x57": (0, 50),
               "Ressort_Croix": (0, 60), "Piece3_Couvercle": (0, 72)}
    for name, (du, dw) in offsets.items():
        o = doc.getObject(name)
        move = App.Placement(V(du, 0, dw), App.Rotation())
        if o.ExpressionEngine:                    # placement driven by the sheet: move a copy
            c = doc.addObject("Part::Feature", name + "_eclate")
            c.Shape = o.Shape.transformGeometry(move.toMatrix())
            c.ViewObject.ShapeAppearance = o.ViewObject.ShapeAppearance
            c.ViewObject.Transparency = o.ViewObject.Transparency
            o.ViewObject.Visibility = False
        else:
            o.ViewObject.Visibility = True
            o.Placement = move.multiply(o.Placement)
    doc.recompute()
    look_from(view, V(1.6, 0.7, 0.8))
    view.saveImage(os.path.join(DOCS, "vue-eclatee.png"), 1600, 1100, "White")
    App.closeDocument(doc.Name)
except Exception:
    open(os.path.join(DOCS, ".screenshots_error"), "w").write(traceback.format_exc())
open(os.path.join(DOCS, ".screenshots_done"), "w").close()
Gui.getMainWindow().close()
