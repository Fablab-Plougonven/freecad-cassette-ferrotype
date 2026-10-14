import sys
sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD, Mesh
import numpy as np, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
m = Mesh.Mesh(sys.argv[1]); out = sys.argv[2]
X0, Z0 = 49.0, 92.08            # window centre
def uv(a): return np.c_[X0 - a[:,0], Z0 - a[:,2]]   # rear view, latch up
def loops(y):
    s = m.crossSections([(FreeCAD.Vector(0,y,0), FreeCAD.Vector(0,1,0))], 1e-4)[0]
    return [uv(np.array([[p.x,p.y,p.z] for p in pl])) for pl in s]
fig, ax = plt.subplots(figsize=(13, 12))
for a in loops(12.5):
    ax.plot(a[:,0], a[:,1], color="#222", lw=1.1)
for a in loops(15.6):
    if len(a) > 100 or (abs(a[:,0]).max() > 33 and abs(a[:,0]).max() < 36.5):
        ax.plot(a[:,0], a[:,1], color="#1f6fd1", lw=0.8, ls="--")
for a in loops(16.1):
    if 6.0 < np.ptp(a[:,0]) < 7 and np.ptp(a[:,1]) < 2:
        ax.fill(a[:,0], a[:,1], color="#d1361f", alpha=0.8)
ax.set_aspect("equal"); ax.grid(True, lw=0.25, alpha=0.6)
ax.set_xticks(range(-50, 55, 10)); ax.set_yticks(range(-50, 55, 10))
def dim(p1, p2, txt, off=(0,0), c="#b0004c"):
    ax.annotate("", p1, p2, arrowprops=dict(arrowstyle="<->", color=c, lw=0.9))
    mx, my = (p1[0]+p2[0])/2 + off[0], (p1[1]+p2[1])/2 + off[1]
    ax.text(mx, my, txt, color=c, fontsize=9, ha="center", va="center",
            bbox=dict(fc="white", ec="none", alpha=0.85, pad=1))
def note(xy, txt, xyt, c="#333"):
    ax.annotate(txt, xy, xyt, fontsize=8.5, color=c, arrowprops=dict(arrowstyle="-", color=c, lw=0.6),
                bbox=dict(fc="#fffbe6", ec="#999", lw=0.5, pad=2))
dim((-42.2,-52), (42.2,-52), "84,4")
dim((-42.2,-57), (48.5,-57), "90,7 (avec talon)")
dim((-52,-43.04), (-52,43.05), "86,1", off=(0,-10))
dim((-60,-43.04), (-60,45.8), "88,85\n(avec\nlanguette)", off=(0,10))
dim((-30.75,-30.75), (30.75,-30.75), "fenêtre 61,5 × 61,5")
dim((-27.05,-47.5), (27.05,-47.5), "entraxe crochets 54,1")
dim((-14.98,50.5), (14.98,50.5), "entraxe fenêtres verrou ≈ 30,0")
note((-27.05,-42.3), "encoche crochet 6,5 × 1,55\n(arrière évidé sur 5,6 ; lèvre 1,1 côté boîtier)", (-40,-68))
note((27.05,-42.3), "idem, centrée à ±27,05", (18,-66))
note((15,40.05), "2 fenêtres 6,45 × 1,61 côté boîtier\n→ poche du verrou (paroi 1,0)", (2,62))
note((6,47.3), "languette du verrou coulissant\n(course ≈ 3,5)", (-48,60))
note((40.5,11.3), "poche 3 × 17,\nprof. 5,9 côté boîtier", (52,22))
note((40.5,-26.2), "poche 2 × 4,5,\nprof. 5,9", (52,-30))
note((45.3,0), "talon 6,3 × 75\n(côté manivelle)", (52,2))
note((0,36), "gorge lumière 2 × 1,2\naxe = carré 72 × 72 (pointillés)", (-22,22), c="#1f6fd1")
note((37.5,-37.5), "4 trous Ø3,1 entraxe 75 × 75\n(propres à l'Imacon)", (44,-48))
note((-21.2,40.8), "2 trous Ø1,8 (capot du verrou)", (-60,52))
ax.text(0, 0, "plan film à 3,55 ± 0,05\nderrière la face d'appui\népaisseur plaque Rayfor 6,7", ha="center", va="center", fontsize=10, color="#555")
ax.set_title("Interface magasin Hasselblad V : relevé sur la monture de Rayfor (Imacon), en mm\n"
             "Vue arrière (côté photographe), haut = verrou, bas = crochets. Origine = centre de la fenêtre", fontsize=11)
ax.set_xlim(-72, 75); ax.set_ylim(-75, 70)
plt.tight_layout(); plt.savefig(out, dpi=130)
