"""Box lid with clips (no magnets) for pieces 1 and 2 printed from release v0.1.

In v0.1 the flange of piece 2 is 2 mm thick, piece 2 has one groove for the lid
rib, and the hinge block of piece 1 reaches into the cassette up to the old lid
face. The current lid is built with those dimensions, with one rib, and with a
notch in its hinge-side wall over the old hinge block. It is then checked
against the v0.1 pieces (closed, and opening from 0 to 180 deg with the dark
slide in) and exported to exports/piece3_couvercle_pour_v0.1.stl / .step.

Run with FreeCAD's interpreter, with the STEP files of the v0.1 release
(gh release download v0.1 -p "*.step" -D <dir>):
  /Applications/FreeCAD.app/Contents/Resources/bin/python tools/lid_for_v0_1.py <dir>
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "cad"))
import build_cassette as bc  # noqa: E402

App, V, Part = bc.App, bc.V, bc.Part
V01 = {"collerette_epaisseur": "2", "fermeture_aimants": "0"}


def read_step(path):
    s = Part.Shape()
    s.read(path)
    return s


def main(v01_dir):
    bc.PARAMS[:] = [(n, V01.get(n, e), note) for n, e, note in bc.PARAMS]
    doc, pieces, refs, _ = bc.build_document()
    pd, lid = bc.PD(doc), pieces["piece3_couvercle"]
    feature = {f.Label: f for f in lid.Group}
    seat = next(f for f in lid.Group if f.Label.startswith("Plan_appui_piece2"))
    # one rib, for the single groove of the v0.1 piece 2
    feature["Nervures"].Suppressed = True
    pd.pad(lid, "Nervure_v0_1", pd.sk(lid, "Nervure_v0_1", seat, lambda s: bc.square_rings(
        pd, s, ("couvercle_gorge_axe",), "couvercle_nervure_largeur")), "couvercle_nervure_hauteur", reverse=True)
    # the v0.1 hinge block rises to the top of the knuckle inside the cassette: notch the wall over it
    wall_top = "plaque_bord_bas + paroi_charniere_retrait + jupe_epaisseur + 0.5"
    pd.pocket(lid, "Encoche_bloc_charniere_v0_1", pd.sk(lid, "Encoche_bloc_charniere_v0_1", seat, lambda s: pd.rect(
        s, "-bossage_demi_longueur - 0.3", "bossage_demi_longueur + 0.3", "plaque_bord_bas - 1", wall_top)),
        "noeud_rayon + 0.4", reverse=True)
    doc.recompute()
    bad = bc.invalid_objects(doc)
    shape = lid.Shape
    ok = not bad and shape.isValid() and len(shape.Solids) == 1
    print(f"lid: valid={ok} vol={shape.Volume:.0f} mm3 {'' if not bad else bad}", flush=True)

    old = {n: read_step(os.path.join(v01_dir, n + ".step")) for n in (
        "piece1_interface", "piece2_cadre_verre", "glissiere_verrou", "capot_verrou", "ressort_croix")}
    fixed = {k: v for k, v in old.items() if k != "ressort_croix"}
    fixed["volet"] = refs["Volet"].Shape
    print("closed, against the v0.1 pieces (mm3, expected 0):")
    for k, s in fixed.items():
        v, _ = bc.solid_overlap(shape, s)
        ok &= v < 0.01
        print(f"  {k:20s} {v:8.3f}{'' if v < 0.01 else '  <-- !'}")
    gap = shape.distToShape(old["piece2_cadre_verre"])[0]
    print(f"  lid to piece 2: {gap:.3f} mm (expected 0: the frame bears on it)")
    ok &= gap < 1e-3

    vals = bc.param_values()
    center = V(0, vals["charniere_axe_y"], vals["charniere_axe_z"])
    top = vals["couvercle_ouverture_max"]
    angles = list(range(0, 31)) + list(range(32, int(top), 2)) + [top]
    moving = {"couvercle": shape, "ressort": old["ressort_croix"]}
    problems, snaps = [], []
    for a in angles:
        m = App.Placement(V(), App.Rotation(V(1, 0, 0), a), center).toMatrix()
        for k, s in moving.items():
            turned = s.transformGeometry(m)
            for f, fs in fixed.items():
                v, bb = bc.solid_overlap(turned, fs)
                if v < 0.01:
                    continue
                if k == "couvercle" and f == "piece1_interface" and a <= 5 and bb.XMin >= vals["talon_bord_droit"] - 0.5:
                    snaps.append(a)
                else:
                    problems.append(f"{a} deg: {k} enters {f} ({v:.2f} mm3)")
    ok &= not problems
    print(f"opening, {len(angles)} positions from 0 to {top:g} deg, dark slide in: "
          f"{'no collision' if not problems else str(len(problems)) + ' problems'}"
          + (f"; clip hooks over their stops up to {max(snaps)} deg (expected)" if snaps else ""))
    for p in problems[:12]:
        print(f"    {p}  <-- !")

    bc.export(shape, "piece3_couvercle_pour_v0.1")
    print("exported exports/piece3_couvercle_pour_v0.1.stl and .step")
    print("ALL CHECKS OK" if ok else "CHECKS FAILED", flush=True)
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(sys.argv[1]) else 1)
