import sys
sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD, Mesh
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
path, out, axis = sys.argv[1], sys.argv[2], sys.argv[3]   # axis: x|y|z normal
levels = [float(v) for v in sys.argv[4].split(",")]
m = Mesh.Mesh(path)
n = {"x":(1,0,0),"y":(0,1,0),"z":(0,0,1)}[axis]
uv = {"x":(1,2),"y":(0,2),"z":(0,1)}[axis]
b = m.BoundBox
cols = len(levels)
fig, axs = plt.subplots(1, cols, figsize=(7*cols, 7))
if cols == 1: axs=[axs]
for ax, lv in zip(axs, levels):
    o = [0,0,0]; o["xyz".index(axis)] = lv
    secs = m.crossSections([(FreeCAD.Vector(*o), FreeCAD.Vector(*n))], 1e-4)[0]
    for pl in secs:
        a = np.array([[p.x,p.y,p.z] for p in pl])
        ax.plot(a[:,uv[0]], a[:,uv[1]], "k-", lw=0.6)
    ax.set_aspect("equal"); ax.set_title(f"{axis}={lv}"); ax.grid(True, lw=0.3)
    ax.minorticks_on(); ax.grid(True, which="minor", lw=0.1)
    ax.set_xlabel("xyz"[uv[0]]); ax.set_ylabel("xyz"[uv[1]])
plt.tight_layout(); plt.savefig(out, dpi=110)
