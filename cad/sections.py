"""Section views of the closed cassette (PNG in docs/)."""
import os, sys
sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import FreeCAD as App
import Part
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
import build_cassette as b

V = App.Vector
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
doc, pieces, refs, _ = b.build_document()
shapes = {"Pièce 1 interface": (pieces["piece1_interface"].Shape, "#26262b"),
          "Pièce 2 cadre verre": (pieces["piece2_cadre_verre"].Shape, "#6b6b75"),
          "Pièce 3 couvercle": (pieces["piece3_couvercle"].Shape, "#3a4a6a"),
          "Verre 57×57×1": (refs["Verre_57x57"].Shape, "#5ab4e0"),
          "Volet": (refs["Volet"].Shape, "#b0b4b8"),
          "Glissière": (pieces["glissiere_verrou"].Shape, "#c03030"),
          "Ressort à lames": (pieces["ressort_lames"].Shape, "#d07a1a")}

def section(ax, normal, offset, axes, title, xlim, ylim):
    for label, (s, col) in shapes.items():
        wires = s.slice(normal, offset)
        for w in wires:
            pts = [v.Point for v in w.OrderedVertexes] if not w.isClosed() else w.discretize(Deflection=0.02)
            xy = [(p[axes[0]], p[axes[1]]) for p in pts]
            if len(xy) > 2:
                ax.add_patch(Polygon(xy, closed=True, fc=col, ec="k", lw=0.3, alpha=0.9, label=label))
                label = None
    ax.set_xlim(*xlim); ax.set_ylim(*ylim); ax.set_aspect("equal"); ax.grid(True, lw=0.2)
    ax.set_title(title, fontsize=10)

fig, axs = plt.subplots(3, 1, figsize=(14, 17))
section(axs[0], V(0, 1, 0), 0.0, (0, 2), "Coupe v = 0 (horizontale) : u →, w ↑ (w = 0 : face d'appui côté boîtier)", (-60, 56), (-1, 17))
section(axs[1], V(1, 0, 0), 0.0, (1, 2), "Coupe u = 0 (verticale) : v →, w ↑", (-52, 52), (-1, 17))
section(axs[2], V(1, 0, 0), 15.0, (1, 2), "Coupe u = 15 (fenêtre du verrou)", (-52, 52), (-1, 17))
for ax in axs:
    ax.axhline(3.55, color="#c00", lw=0.6, ls="--"); ax.text(ax.get_xlim()[0] + 1, 3.65, "plan film 3,55", color="#c00", fontsize=8)
h, l = axs[0].get_legend_handles_labels()
fig.legend(h, l, loc="lower center", ncol=7, fontsize=9)
plt.tight_layout(rect=(0, 0.04, 1, 1))
plt.savefig(os.path.join(ROOT, "docs", "coupes-assemblage.png"), dpi=120)
print("ok")
