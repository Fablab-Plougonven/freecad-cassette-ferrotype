import sys
sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD, Mesh
import numpy as np
path, axis = sys.argv[1], sys.argv[2]
levels = [float(v) for v in sys.argv[3].split(",")]
m = Mesh.Mesh(path)
n = {"x":(1,0,0),"y":(0,1,0),"z":(0,0,1)}[axis]
uv = {"x":(1,2),"y":(0,2),"z":(0,1)}[axis]
for lv in levels:
    o = [0,0,0]; o["xyz".index(axis)] = lv
    secs = m.crossSections([(FreeCAD.Vector(*o), FreeCAD.Vector(*n))], 1e-4)[0]
    print(f"== {axis}={lv}: {len(secs)} loops")
    for pl in secs:
        a = np.array([[p.x,p.y,p.z] for p in pl])[:, list(uv)]
        # simplify: drop collinear points
        keep=[a[0]]
        for i in range(1,len(a)-1):
            d1=a[i]-keep[-1]; d2=a[i+1]-a[i]
            if abs(d1[0]*d2[1]-d1[1]*d2[0])>1e-3: keep.append(a[i])
        keep.append(a[-1])
        k=np.array(keep)
        print(f"  loop {len(k)} pts  {'xyz'[uv[0]]}[{k[:,0].min():.2f},{k[:,0].max():.2f}] {'xyz'[uv[1]]}[{k[:,1].min():.2f},{k[:,1].max():.2f}]")
        if len(k) <= 40:
            print("    " + " ".join(f"({p[0]:.2f},{p[1]:.2f})" for p in k))
