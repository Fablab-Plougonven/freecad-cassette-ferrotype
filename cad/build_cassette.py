"""Wet-plate cassette (57 x 57 glass) for Hasselblad V bodies.

Builds a parametric FreeCAD document made of PartDesign bodies: every piece is
a stack of constrained sketches (Pad / Pocket) whose constraints and planes are
driven by the spreadsheet "Parametres", so the FCStd stays editable by hand
without this script. Then exports STL/STEP and runs fit checks. Interface
geometry comes from Rayfor's V mount (see docs/COTES.md).

Frame: u = right seen from the rear (photographer side), v = up (latch side),
w = depth from the body mating face towards the rear. Origin = centre of the
image window. X = u, Y = v, Z = w. Spreadsheet values are plain numbers in mm.

Run with FreeCAD's interpreter:
  /Applications/FreeCAD.app/Contents/Resources/bin/python cad/build_cassette.py
"""
import csv
import math
import os
import re
import struct
import sys
import zipfile

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/lib")
import FreeCAD as App  # noqa: E402
import Mesh  # noqa: E402
import MeshPart  # noqa: E402
import Part  # noqa: E402
import Sketcher  # noqa: E402

V = App.Vector
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "exports")
FCSTD = os.path.join(OUT, "cassette_ferrotype.FCStd")
SHEET = "Parametres"

# --- Parameter table: (name, expression, note) -----------------------------
# Expressions use other names of the table; numbers are mm.
PARAMS = [
    # Body interface (Rayfor V mount)
    ("plate_u", "42.2", "demi-largeur de la plaque"),
    ("plate_v_top", "43.05", "bord haut (cote verrou)"),
    ("plate_v_bot", "-43.04", "bord bas (cote crochets)"),
    ("corner_r", "3", "rayon des coins"),
    ("tab_u", "32", "demi-largeur de la languette haute"),
    ("tab_v", "45.8", "bord haut de la languette"),
    ("tab_chamfer_u", "34.95", "pied des chanfreins de la languette"),
    ("tab_v0", "38", "base de la languette (noyee dans la plaque)"),
    ("heel_u", "48.5", "talon cote manivelle : bord exterieur"),
    ("heel_v", "37.5", "talon : demi-hauteur"),
    ("heel_overlap", "3.2", "recouvrement talon / plaque"),
    ("t1", "6.7", "epaisseur de la piece 1"),
    ("seal_out", "37", "gorge anti-lumiere : demi-cote exterieur"),
    ("seal_in", "35", "gorge anti-lumiere : demi-cote interieur"),
    ("seal_depth", "1.2", "gorge qui recoit la levre du boitier : profondeur"),
    ("seal_depth_left", "seal_depth", "profondeur de la gorge a gauche, sous la fente du volet"),
    ("pin_pocket_depth", "5.9", "poches des ergots du boitier"),
    ("pocketA_u0", "39", ""), ("pocketA_u1", "42", ""),
    ("pocketA_v0", "2.76", ""), ("pocketA_v1", "19.76", ""),
    ("pocketB_u0", "39.5", ""), ("pocketB_u1", "41.5", ""),
    ("pocketB_v0", "-28.49", ""), ("pocketB_v1", "-23.99", ""),
    ("latch_win_u0", "11.75", "fenetres des griffes (symetriques)"),
    ("latch_win_u1", "18.2", ""),
    ("latch_win_v0", "39.25", ""), ("latch_win_v1", "40.86", ""),
    ("latch_skin", "0.8", "paroi devant la poche du verrou (1.0 trop epais a l'essai)"),
    ("slider_t", "3", "glissiere : epaisseur"),
    ("latch_depth", "latch_skin + slider_t + 0.2", "fond de la poche du verrou"),
    ("latch_u0", "-18.2", "poche de la glissiere Rayfor"), ("latch_u1", "26.2", ""),
    ("latch_v0", "37.25", ""), ("latch_v1", "44.3", ""),
    ("latch_block_u0", "2.75", "ilot de guidage dans la poche"), ("latch_block_u1", "11.75", ""),
    ("latch_block_v1", "40.25", ""),
    ("cover_u0", "-24.2", "poche du capot Rayfor"), ("cover_u1", "32.2", ""),
    ("latch_fit", "0.2", "jeu par cote de la glissiere et du capot Rayfor"),
    ("tabopen_u0", "-6.2", "passage de la languette de la glissiere"), ("tabopen_u1", "14.2", ""),
    ("hook_u0", "23.8", "encoches des crochets (symetriques)"), ("hook_u1", "30.3", ""),
    ("hook_depth", "1.55", ""), ("hook_lip", "1.1", "levre gardee cote boitier"),
    # Film plane and dark slide stack
    ("film", "3.55", "face d'appui -> emulsion"),
    ("skin", "1.9", "peau avant de la piece 1"),
    ("slot", "0.4", "epaisseur de la fente du volet"),
    ("ledge_w", "skin + slot", "face avant de la butee du verre"),
    ("slide_w", "65.88", "volet : largeur de la plaque metal mesuree"),
    ("slot_play", "0.5", "jeu total du volet en hauteur"),
    ("slot_half", "(slide_w + slot_play) / 2", "demi-hauteur de la fente"),
    ("slot_end", "30.9", "butee de fond du volet (u)"),
    ("slide_t", "0.3", "volet : epaisseur (reference)"),
    ("glass", "57", "verre : cote (57 x 57)"), ("glass_t", "1", "verre : epaisseur"),
    ("glass_gap", "0.2", "jeu du verre par cote"),
    ("glass_back", "film + glass_t", "dos du verre"),
    ("ledge_overlap", "1", "appui du verre sur la butee, par cote"),
    ("aperture", "glass - 2 * ledge_overlap", "ouverture de la butee = image"),
    ("skin_aperture", "61.9", "ouverture de la peau avant : laisse entrer la levre interieure du boitier (fenetre Rayfor 61.5 + jeu)"),
    # Insert pocket (piece 1) / insert (piece 2)
    ("pocket_u_max", "34", "poche de la piece 2 : bord droit"),
    ("pocket_v", "34.8", "poche de la piece 2 : demi-hauteur (reste dans la gorge, seal_in)"),
    ("fit", "0.2", "jeu insert / poche"),
    ("flange_t", "2", "collerette de la piece 2"),
    ("flange_w1", "t1 + flange_t", "face arriere de la piece 2"),
    ("felt_u0", "-41.2", "gorges du velours a l'entree de la fente"), ("felt_u1", "-38.2", ""),
    ("felt_depth", "0.6", ""),
    ("lid_seal_c", "33.5", "gorge du couvercle : axe"), ("lid_seal_w", "1.6", ""),
    ("lid_seal_d", "1", ""),
    ("rib_w", "1", "nervure du couvercle"), ("rib_h", "0.8", ""),
    # Light traps between piece 1 and piece 2
    ("trap_c", "36.1", "chicane collerette : axe (haut, bas, droite)"),
    ("trap_u_left", "-40.2", "chicane collerette : bout gauche"),
    ("trap_w", "1", "chicane collerette : largeur de la gorge"), ("trap_d", "1", "profondeur de la gorge"),
    ("trap_rib", "0.6", "largeur de la nervure"), ("trap_h", "0.8", "hauteur de la nervure"),
    ("rail_trap_c", "33.9", "chicane des rails : axe (haut, bas)"),
    ("rail_trap_u", "32.35", "chicane des rails : axe du cote droit"),
    ("rail_trap_w", "0.9", "largeur de la gorge dans le fond de la piece 1"), ("rail_trap_d", "0.6", ""),
    ("rail_trap_rib", "0.5", "largeur de la nervure sous les rails"), ("rail_trap_h", "0.5", ""),
    ("claw_relief", "0.3", "degagement des griffes dans la collerette (par cote)"),
    # Screws M3 x 6 countersunk
    ("screw_u", "38.5", "vis : |u|"), ("screw_v_top", "39", "vis du haut : v"),
    ("screw_v_bot", "-39.5", "vis du bas : v"),
    ("pilot_d", "2.5", "avant-trou piece 1"), ("pilot_depth", "4.5", ""),
    ("clear_d", "3.4", "passage piece 2"), ("csk_d", "6.2", "fraisure 90 deg"),
    # Lid
    ("lid_t", "2.4", "epaisseur du couvercle"),
    ("lid_w1", "flange_w1 + lid_t", "face exterieure du couvercle"),
    # Hinge (pin 2 mm, along u)
    ("knuckle_r", "2.4", ""), ("pin_d", "2.1", "trou de l'axe (axe 2)"),
    ("hinge_clear", "0.4", "jeu entre noeuds et bord bas"),
    ("hinge_v", "plate_v_bot - knuckle_r - hinge_clear", "axe de la charniere : v"),
    ("hinge_w", "flange_w1", "axe de la charniere : w"),
    ("boss_u", "14", "noeud central (piece 1) : demi-longueur"),
    ("boss_v_top", "-37.5", "haut du bossage de charniere (laisse passer la chicane)"),
    ("boss_lid_gap", "0.8", "jeu couvercle / haut du bossage (ouverture sans frotter)"),
    ("knuckle_gap", "0.4", ""), ("lid_knuckle_u1", "22", "noeuds du couvercle : bout"),
    ("gusset_w0", "1.1", "depart du gousset a 45 deg"),
    ("gusset_drop", "hinge_w - knuckle_r - gusset_w0", ""),
    # Snap clip on the heel (right side)
    ("clipA_v0", "20", "clip du haut"), ("clipA_v1", "33", ""),
    ("clipB_v0", "-7", "clip du milieu"), ("clipB_v1", "6", ""),
    ("bump", "0.6", "saillie de l'arret"), ("bump_w0", "3", ""), ("bump_w1", "4", ""),
    ("ramp_w", "6", "haut de la rampe (pente douce)"),
    ("finger_t", "1.4", "doigt du clip : epaisseur"), ("finger_gap", "0.2", "jeu doigt / arret"), ("lip_w0", "2.3", ""),
    ("finger_u0", "heel_u + bump + finger_gap", ""),
    ("finger_u1", "finger_u0 + finger_t", ""),
    # Cross spring
    ("spring_arm", "24", "bras : longueur depuis le centre"), ("spring_arm_w", "6", ""),
    ("spring_t", "1.6", "bras : epaisseur"), ("spring_hub_d", "14", ""),
    ("spring_foot_d", "5", ""), ("spring_foot_r", "21.5", ""),
    ("preload", "0.8", "ecrasement du ressort"), ("hub_clear", "0.3", "jeu moyeu / verre"),
    ("foot_tip", "glass_back - preload", ""),
    ("arm_front", "glass_back + hub_clear", ""),
    ("post_end", "arm_front + spring_t", ""),
    ("post_d", "8", "tenon du couvercle"), ("pin_post_d", "3", ""), ("pin_post_l", "1", ""),
    ("spring_hole_d", "pin_post_d + 0.5", "trou du ressort (Ø3.2 trop serre a l'essai)"),
    # Latch slider and cover (Rayfor, remodelled; slider at rest)
    ("sl_u0", "-14.7", "glissiere : bout gauche"), ("sl_bar_v0", "41.25", "glissiere : bas de la barre"),
    ("sl_toothA_u0", "18.25", "dent droite : bout (la dent va jusqu'a latch_u1)"),
    ("sl_toothB_u0", "-11.75", "dent gauche : bout"), ("sl_toothB_u1", "-5.25", "dent gauche : pied"),
    ("sl_ramp_t0", "0.81", "rampe de verrouillage : epaisseur au bout de la dent"),
    ("sl_ramp_len", "6.59", "rampe : longueur jusqu'a pleine epaisseur (environ 18 deg)"),
    ("sl_step_v0", "40.46", "guide au-dessus de l'ilot"), ("sl_step_u1", "11.16", ""),
    ("sl_tab_u0", "-2.7", "languette : bords"), ("sl_tab_u1", "14.2", ""),
    ("sl_tab_v1", "48.3", "languette : bout"),
    ("sl_grip_v0", "46.31", "prise : debut (hors de la plaque)"), ("sl_grip_t", "1.7", "prise : surepaisseur"),
    ("knurl_u0", "-2.7", "moletage : pied de la 1re dent"), ("knurl_pitch", "1.92", ""),
    ("knurl_base", "1.5", "dent trapezoidale : pied"), ("knurl_top", "0.75", "dent : sommet"),
    ("knurl_h", "0.66", ""),
    ("sl_travel", "3.5", "course de la glissiere (vers u negatif)"),
    ("cover_t", "2.4", "capot : epaisseur (affleure la face arriere de la piece 1)"),
]
NAMES = {n for n, _, _ in PARAMS}
_TOKEN = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]*\b")


def X(e):
    """Mini-expression -> FreeCAD expression (names -> Parametres.name)."""
    if isinstance(e, (int, float)):
        return repr(float(e))
    return _TOKEN.sub(lambda m: f"{SHEET}.{m.group(0)}" if m.group(0) in NAMES else m.group(0), e)


def neg(e):
    return f"-({e})"


def param_values():
    """Pure-Python evaluation of the table (same expressions as the sheet)."""
    vals = {}
    for n, e, _ in PARAMS:
        vals[n] = eval(e, {"__builtins__": {}}, dict(vals))
    return vals


# --- Sketch-based builder ---------------------------------------------------
# Sketch planes of a body origin: XY (local u, v; offset = w), YZ (local v, w;
# offset = u), XZ (local u, w; normal -Y, so offset = -v).
PLANES = {"XY": "XY_Plane", "YZ": "YZ_Plane", "XZ": "XZ_Plane"}
DEG = math.pi / 180


class PD:
    def __init__(self, doc):
        self.doc = doc
        self.vals = param_values()
        self.n = 0
        self.k = {}

    def ev(self, e):
        if isinstance(e, (int, float)):
            return float(e)
        return float(eval(e, {"__builtins__": {}}, dict(self.vals)))

    def _name(self, label):
        self.n += 1
        return f"{label}_{self.n:03d}"

    def body(self, label):
        return self.doc.addObject("PartDesign::Body", label)

    # sketches ---------------------------------------------------------------
    def sketch(self, body, label, plane, off):
        sk = body.newObject("Sketcher::SketchObject", self._name("Esq_" + label))
        support = [f for f in body.Origin.OriginFeatures if f.Role == PLANES[plane]][0]
        sk.AttachmentSupport = [(support, "")]
        sk.MapMode = "FlatFace"
        o = f"-({off})" if plane == "XZ" else off
        sk.AttachmentOffset = App.Placement(V(0, 0, self.ev(o)), App.Rotation())
        if not (isinstance(off, (int, float)) and off == 0):
            sk.setExpression(".AttachmentOffset.Base.z", X(o))
        sk.Visibility = False
        return sk

    def _datum(self, sk, cons, e):
        self.k[sk.Name] = self.k.get(sk.Name, 0) + 1
        c = sk.addConstraint(cons)
        name = f"c{self.k[sk.Name]}"
        sk.renameConstraint(c, name)
        if not isinstance(e, (int, float)):
            sk.setExpression(f".Constraints.{name}", X(e))

    def _fix(self, sk, geo, pos, x, y):
        """Pin a sketch point to (x, y) expressions, measured from the origin."""
        for kind, e, axis in (("DistanceX", x, -2), ("DistanceY", y, -1)):
            if isinstance(e, (int, float)) and e == 0:
                sk.addConstraint(Sketcher.Constraint("PointOnObject", geo, pos, axis))
            else:
                self._datum(sk, Sketcher.Constraint(kind, -1, 1, geo, pos, self.ev(e)), e)

    def poly(self, sk, pts):
        """Closed polygon, every vertex driven by its coordinates."""
        p = [V(self.ev(u), self.ev(v), 0) for u, v in pts]
        n, g0 = len(p), sk.GeometryCount
        for i in range(n):
            sk.addGeometry(Part.LineSegment(p[i], p[(i + 1) % n]))
        for i in range(n):
            sk.addConstraint(Sketcher.Constraint("Coincident", g0 + i, 2, g0 + (i + 1) % n, 1))
        for i, (u, v) in enumerate(pts):
            self._fix(sk, g0 + i, 1, u, v)

    def rect(self, sk, u0, u1, v0, v1):
        self.poly(sk, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def circle(self, sk, u, v, r):
        g = sk.addGeometry(Part.Circle(V(self.ev(u), self.ev(v), 0), V(0, 0, 1), self.ev(r)))
        self._fix(sk, g, 3, u, v)
        self._datum(sk, Sketcher.Constraint("Radius", g, self.ev(r)), r)

    def profile(self, sk, items):
        """Closed outline of lines and CCW arcs, joined in order.
        ("L", (u0, v0), (u1, v1), "H" | "V" | None) ; ("A", (cu, cv), r, a0_deg, a1_deg).
        Arcs: centre and radius driven; joins next to an arc are tangent."""
        g0, kinds = sk.GeometryCount, []
        for it in items:
            if it[0] == "L":
                a, b = (V(self.ev(x), self.ev(y), 0) for x, y in it[1:3])
                sk.addGeometry(Part.LineSegment(a, b))
            else:
                c = V(self.ev(it[1][0]), self.ev(it[1][1]), 0)
                circ = Part.Circle(c, V(0, 0, 1), self.ev(it[2]))
                sk.addGeometry(Part.ArcOfCircle(circ, it[3] * DEG, it[4] * DEG))
            kinds.append(it[0])
        n = len(items)
        for i in range(n):
            j = (i + 1) % n
            kind = "Tangent" if "A" in (kinds[i], kinds[j]) else "Coincident"
            sk.addConstraint(Sketcher.Constraint(kind, g0 + i, 2, g0 + j, 1))
        for i, it in enumerate(items):
            if it[0] == "L" and it[3]:
                sk.addConstraint(Sketcher.Constraint("Horizontal" if it[3] == "H" else "Vertical", g0 + i))
            elif it[0] == "A":
                self._fix(sk, g0 + i, 3, *it[1])
                self._datum(sk, Sketcher.Constraint("Radius", g0 + i, self.ev(it[2])), it[2])

    # features ---------------------------------------------------------------
    def add(self, body, label, plane, a0, a1, draw, reverse_xz=False):
        """Pad from a0 to a1 along the plane axis (w, u, or v for XZ)."""
        if plane == "XZ":
            sk = self.sketch(body, label, plane, a1)       # normal -v: pad from v=a1 down to a0
        else:
            sk = self.sketch(body, label, plane, a0)
        draw(sk)
        f = body.newObject("PartDesign::Pad", self._name(label))
        f.Profile = sk
        f.setExpression("Length", X(f"({a1}) - ({a0})"))
        f.Refine = True
        return f

    def cut(self, body, label, plane, a0, a1, draw, taper=None):
        """Pocket from a1 back to a0 (from a0 up to a1 for XZ)."""
        sk = self.sketch(body, label, plane, a0 if plane == "XZ" else a1)
        draw(sk)
        f = body.newObject("PartDesign::Pocket", self._name(label))
        f.Profile = sk
        f.setExpression("Length", X(f"({a1}) - ({a0})"))
        if taper is not None:
            f.TaperAngle = taper
        f.Refine = True
        return f


# --- Parts -----------------------------------------------------------------
def footprint(pd, sk):
    """Main plate + heel, rounded corners (rear view, CCW)."""
    P, vb, vt, r, H, hv = "plate_u", "plate_v_bot", "plate_v_top", "corner_r", "heel_u", "heel_v"
    pd.profile(sk, [
        ("L", (f"-{P} + {r}", vb), (f"{P} - {r}", vb), None),
        ("A", (f"{P} - {r}", f"{vb} + {r}"), r, -90, 0),
        ("L", (P, f"{vb} + {r}"), (P, f"-{hv}"), "V"),
        ("L", (P, f"-{hv}"), (f"{H} - {r}", f"-{hv}"), "H"),
        ("A", (f"{H} - {r}", f"-{hv} + {r}"), r, -90, 0),
        ("L", (H, f"-{hv} + {r}"), (H, f"{hv} - {r}"), None),
        ("A", (f"{H} - {r}", f"{hv} - {r}"), r, 0, 90),
        ("L", (f"{H} - {r}", hv), (P, hv), "H"),
        ("L", (P, hv), (P, f"{vt} - {r}"), "V"),
        ("A", (f"{P} - {r}", f"{vt} - {r}"), r, 0, 90),
        ("L", (f"{P} - {r}", vt), (f"-{P} + {r}", vt), None),
        ("A", (f"-{P} + {r}", f"{vt} - {r}"), r, 90, 180),
        ("L", (f"-{P}", f"{vt} - {r}"), (f"-{P}", f"{vb} + {r}"), None),
        ("A", (f"-{P} + {r}", f"{vb} + {r}"), r, 180, 270),
    ])


def screw_points():
    return [(su, sv) for su in ("screw_u", neg("screw_u")) for sv in ("screw_v_top", "screw_v_bot")]


def build_piece1(pd):
    b = pd.body("Piece1_Interface")
    pd.add(b, "Plaque", "XY", 0, "t1", lambda s: footprint(pd, s))
    pd.add(b, "Languette", "XY", 0, "t1", lambda s: pd.poly(s, [
        (neg("tab_chamfer_u"), "tab_v0"), ("tab_chamfer_u", "tab_v0"), ("tab_chamfer_u", "plate_v_top"),
        ("tab_u", "tab_v"), (neg("tab_u"), "tab_v"), (neg("tab_chamfer_u"), "plate_v_top")]))
    pd.add(b, "Bossage_charniere", "XY", "hinge_w - knuckle_r", "lid_w1",
           lambda s: pd.rect(s, neg("boss_u"), "boss_u", "hinge_v", "boss_v_top"))
    pd.add(b, "Noeud_charniere", "YZ", neg("boss_u"), "boss_u",
           lambda s: pd.circle(s, "hinge_v", "hinge_w", "knuckle_r"))
    pd.add(b, "Gousset_45", "YZ", neg("boss_u"), "boss_u", lambda s: pd.poly(s, [
        ("plate_v_bot + 0.01", "gusset_w0"), ("plate_v_bot + 0.01", "hinge_w - knuckle_r"),
        ("plate_v_bot - gusset_drop", "hinge_w - knuckle_r")]))
    for c in ("clipA", "clipB"):
        pd.add(b, f"Arret_{c}", "XZ", f"{c}_v0", f"{c}_v1", lambda s: pd.poly(s, [
            ("heel_u - 0.01", "bump_w0"), ("heel_u + bump", "bump_w0"), ("heel_u + bump", "bump_w1"),
            ("heel_u - 0.01", "ramp_w")]))
    # mating face
    pd.cut(b, "Gorge_levre_boitier", "XY", -1, "seal_depth", lambda s: pd.poly(s, [
        (neg("seal_in"), neg("seal_out")), ("seal_out", neg("seal_out")), ("seal_out", "seal_out"),
        (neg("seal_in"), "seal_out"), (neg("seal_in"), "seal_in"), ("seal_in", "seal_in"),
        ("seal_in", neg("seal_in")), (neg("seal_in"), neg("seal_in"))]))
    pd.cut(b, "Gorge_levre_gauche", "XY", -1, "seal_depth_left",
           lambda s: pd.rect(s, neg("seal_out"), neg("seal_in"), neg("seal_out"), "seal_out"))
    pd.cut(b, "Poches_ergots", "XY", -1, "pin_pocket_depth", lambda s: (
        pd.rect(s, "pocketA_u0", "pocketA_u1", "pocketA_v0", "pocketA_v1"),
        pd.rect(s, "pocketB_u0", "pocketB_u1", "pocketB_v0", "pocketB_v1")))
    pd.cut(b, "Fenetres_griffes", "XY", -1, "latch_skin", lambda s: (
        pd.rect(s, neg("latch_win_u1"), neg("latch_win_u0"), "latch_win_v0", "latch_win_v1"),
        pd.rect(s, "latch_win_u0", "latch_win_u1", "latch_win_v0", "latch_win_v1")))
    f = "latch_fit"
    pd.cut(b, "Poche_glissiere", "XY", "latch_skin", "latch_depth", lambda s: pd.poly(s, [
        (f"latch_u0 - {f}", f"latch_v0 - {f}"), (f"latch_block_u0 + {f}", f"latch_v0 - {f}"),
        (f"latch_block_u0 + {f}", f"latch_block_v1 - {f}"), (f"latch_block_u1 - {f}", f"latch_block_v1 - {f}"),
        (f"latch_block_u1 - {f}", f"latch_v0 - {f}"), (f"latch_u1 + {f}", f"latch_v0 - {f}"),
        (f"latch_u1 + {f}", f"latch_v1 + {f}"), (f"latch_u0 - {f}", f"latch_v1 + {f}")]))
    pd.cut(b, "Poche_capot", "XY", "latch_depth", "t1 + 1", lambda s: pd.rect(
        s, f"cover_u0 - {f}", f"cover_u1 + {f}", f"latch_v0 - {f}", f"latch_v1 + {f}"))
    pd.cut(b, "Passage_languette", "XY", "latch_skin", "t1 + 1", lambda s: pd.rect(
        s, f"tabopen_u0 - {f}", f"tabopen_u1 + {f}", "latch_v1 - 0.3", "tab_v + 1.2"))
    pd.cut(b, "Encoches_crochets", "XY", "hook_lip", "t1 + 1", lambda s: (
        pd.rect(s, neg("hook_u1"), neg("hook_u0"), "plate_v_bot - 1", "plate_v_bot + hook_depth"),
        pd.rect(s, "hook_u0", "hook_u1", "plate_v_bot - 1", "plate_v_bot + hook_depth")))
    pd.cut(b, "Ouverture_image", "XY", -1, "skin + 0.01", lambda s: pd.rect(
        s, "-skin_aperture / 2", "skin_aperture / 2", "-skin_aperture / 2", "skin_aperture / 2"))
    pd.cut(b, "Poche_cadre", "XY", "skin", "t1 + 5", lambda s: pd.rect(
        s, "-plate_u - 1", "pocket_u_max", neg("pocket_v"), "pocket_v"))
    pd.cut(b, "Gorge_velours", "XY", "skin - felt_depth", "skin + 0.01",
           lambda s: pd.rect(s, "felt_u0", "felt_u1", neg("slot_half"), "slot_half"))
    pd.cut(b, "Gorge_chicane_collerette", "XY", "t1 - trap_d", "t1 + 1", lambda s: pd.poly(s, [("trap_u_left", "trap_c + trap_w / 2"), ("trap_c + trap_w / 2", "trap_c + trap_w / 2"), ("trap_c + trap_w / 2", "-(trap_c + trap_w / 2)"), ("trap_u_left", "-(trap_c + trap_w / 2)"), ("trap_u_left", "-(trap_c - trap_w / 2)"), ("trap_c - trap_w / 2", "-(trap_c - trap_w / 2)"), ("trap_c - trap_w / 2", "trap_c - trap_w / 2"), ("trap_u_left", "trap_c - trap_w / 2")]))
    pd.cut(b, "Gorge_chicane_rails", "XY", "skin - rail_trap_d", "skin + 0.01", lambda s: pd.poly(s, [("-plate_u - 1", "rail_trap_c + rail_trap_w / 2"), ("rail_trap_u + rail_trap_w / 2", "rail_trap_c + rail_trap_w / 2"), ("rail_trap_u + rail_trap_w / 2", "-(rail_trap_c + rail_trap_w / 2)"), ("-plate_u - 1", "-(rail_trap_c + rail_trap_w / 2)"), ("-plate_u - 1", "-(rail_trap_c - rail_trap_w / 2)"), ("rail_trap_u - rail_trap_w / 2", "-(rail_trap_c - rail_trap_w / 2)"), ("rail_trap_u - rail_trap_w / 2", "rail_trap_c - rail_trap_w / 2"), ("-plate_u - 1", "rail_trap_c - rail_trap_w / 2")]))
    pd.cut(b, "Trou_axe", "YZ", "-boss_u - 1", "boss_u + 1", lambda s: pd.circle(s, "hinge_v", "hinge_w", "pin_d / 2"))
    pd.cut(b, "Avant_trous_vis", "XY", "t1 - pilot_depth", "t1 + 1",
           lambda s: [pd.circle(s, u, v, "pilot_d / 2") for u, v in screw_points()])
    return b


def build_piece2(pd):
    b = pd.body("Piece2_CadreVerre")
    ui1, vi, sh = "pocket_u_max - fit", "pocket_v - fit", "slot_half"
    pd.add(b, "Insert", "XY", "ledge_w", "t1 + 0.01", lambda s: pd.rect(s, neg("plate_u"), ui1, neg(vi), vi))
    pd.add(b, "Collerette", "XY", "t1", "flange_w1", lambda s: footprint(pd, s))
    pd.add(b, "Rails_volet", "XY", "skin", "ledge_w + 0.01", lambda s: pd.poly(s, [
        (neg("plate_u"), neg(vi)), (ui1, neg(vi)), (ui1, vi), (neg("plate_u"), vi), (neg("plate_u"), sh),
        ("slot_end", sh), ("slot_end", neg(sh)), (neg("plate_u"), neg(sh))]))
    pd.add(b, "Nervure_chicane_collerette", "XY", "t1 - trap_h", "t1 + 0.01", lambda s: pd.poly(s, [("trap_u_left", "trap_c + trap_rib / 2"), ("trap_c + trap_rib / 2", "trap_c + trap_rib / 2"), ("trap_c + trap_rib / 2", "-(trap_c + trap_rib / 2)"), ("trap_u_left", "-(trap_c + trap_rib / 2)"), ("trap_u_left", "-(trap_c - trap_rib / 2)"), ("trap_c - trap_rib / 2", "-(trap_c - trap_rib / 2)"), ("trap_c - trap_rib / 2", "trap_c - trap_rib / 2"), ("trap_u_left", "trap_c - trap_rib / 2")]))
    pd.add(b, "Nervure_chicane_rails", "XY", "skin - rail_trap_h", "skin + 0.01", lambda s: pd.poly(s, [(neg("plate_u"), "rail_trap_c + rail_trap_rib / 2"), ("rail_trap_u + rail_trap_rib / 2", "rail_trap_c + rail_trap_rib / 2"), ("rail_trap_u + rail_trap_rib / 2", "-(rail_trap_c + rail_trap_rib / 2)"), (neg("plate_u"), "-(rail_trap_c + rail_trap_rib / 2)"), (neg("plate_u"), "-(rail_trap_c - rail_trap_rib / 2)"), ("rail_trap_u - rail_trap_rib / 2", "-(rail_trap_c - rail_trap_rib / 2)"), ("rail_trap_u - rail_trap_rib / 2", "rail_trap_c - rail_trap_rib / 2"), (neg("plate_u"), "rail_trap_c - rail_trap_rib / 2")]))
    g = "glass / 2 + glass_gap"
    pd.cut(b, "Ouverture_butee", "XY", 0, "film + 0.01",
           lambda s: pd.rect(s, "-aperture / 2", "aperture / 2", "-aperture / 2", "aperture / 2"))
    pd.cut(b, "Logement_verre", "XY", "film", "flange_w1 + 1", lambda s: pd.rect(s, neg(g), g, neg(g), g))
    pd.cut(b, "Gorge_velours", "XY", "ledge_w - 0.01", "ledge_w + felt_depth",
           lambda s: pd.rect(s, "felt_u0", "felt_u1", neg(sh), sh))
    co, ci = "lid_seal_c + lid_seal_w / 2", "lid_seal_c - lid_seal_w / 2"
    pd.cut(b, "Gorge_couvercle", "XY", "flange_w1 - lid_seal_d", "flange_w1 + 1", lambda s: (
        pd.rect(s, neg(co), co, neg(co), co), pd.rect(s, neg(ci), ci, neg(ci), ci)))
    pd.cut(b, "Degagement_charniere", "XY", "t1 - 0.01", "flange_w1 + 1", lambda s: pd.rect(
        s, "-boss_u - 0.3", "boss_u + 0.3", "plate_v_bot - 1", "boss_v_top + 0.3"))
    cr = "claw_relief"
    pd.cut(b, "Degagement_griffes", "XY", "t1 - 0.01", "flange_w1 + 1", lambda s: (
        pd.rect(s, f"-latch_win_u1 - {cr}", f"-latch_win_u0 + {cr}", f"latch_win_v0 - {cr}", f"latch_win_v1 + {cr}"),
        pd.rect(s, f"latch_win_u0 - {cr}", f"latch_win_u1 + {cr}", f"latch_win_v0 - {cr}", f"latch_win_v1 + {cr}")))
    pd.cut(b, "Passages_vis", "XY", "t1 - 1", "flange_w1 + 1",
           lambda s: [pd.circle(s, u, v, "clear_d / 2") for u, v in screw_points()])
    pd.cut(b, "Fraisures", "XY", "flange_w1 - (csk_d - clear_d) / 2", "flange_w1",
           lambda s: [pd.circle(s, u, v, "csk_d / 2") for u, v in screw_points()], taper=-45)
    return b


def build_piece3(pd):
    b = pd.body("Piece3_Couvercle")
    k0, k1 = "boss_u + knuckle_gap", "lid_knuckle_u1"
    pd.add(b, "Couvercle", "XY", "flange_w1", "lid_w1", lambda s: footprint(pd, s))
    co, ci = "lid_seal_c + rib_w / 2", "lid_seal_c - rib_w / 2"
    pd.add(b, "Nervure", "XY", "flange_w1 - rib_h", "flange_w1 + 0.01", lambda s: (
        pd.rect(s, neg(co), co, neg(co), co), pd.rect(s, neg(ci), ci, neg(ci), ci)))
    pd.add(b, "Tenon", "XY", "post_end", "flange_w1 + 0.01", lambda s: pd.circle(s, 0, 0, "post_d / 2"))
    pd.add(b, "Pion", "XY", "post_end - pin_post_l", "post_end + 0.01", lambda s: pd.circle(s, 0, 0, "pin_post_d / 2"))
    for c in ("clipA", "clipB"):
        v0, v1 = f"{c}_v0", f"{c}_v1"
        pd.add(b, f"Racine_{c}", "XY", "flange_w1", "lid_w1",
               lambda s: pd.rect(s, "heel_u - 1", "finger_u1", v0, v1))
        pd.add(b, f"Doigt_{c}", "XY", "lip_w0", "lid_w1 - 0.01",
               lambda s: pd.rect(s, "finger_u0", "finger_u1", v0, v1))
        pd.add(b, f"Bec_{c}", "XZ", v0, v1, lambda s: pd.poly(s, [
            ("finger_u0 + 0.01", "lip_w0"), ("finger_u0 + 0.01", "bump_w0 - 0.1"), ("heel_u + 0.2", "bump_w0 - 0.1")]))
        pd.add(b, f"Tirette_{c}", "XY", "lid_w1 - 1.5", "lid_w1",
               lambda s: pd.rect(s, "finger_u1 - 0.01", "finger_u1 + 2", f"{v0} + 3", f"{v1} - 3"))
    for side, (a, c) in (("gauche", (neg(k1), neg(k0))), ("droit", (k0, k1))):
        pd.add(b, f"Patte_noeud_{side}", "YZ", a, c,
               lambda s: pd.rect(s, "hinge_v", "plate_v_bot + 0.5", "hinge_w", "lid_w1"))
        pd.add(b, f"Noeud_{side}", "YZ", a, c, lambda s: pd.circle(s, "hinge_v", "hinge_w", "knuckle_r"))
    pd.cut(b, "Degagement_bossage", "XY", "hinge_w - knuckle_r - 1", "lid_w1 + 1", lambda s: pd.rect(
        s, "-boss_u - 0.3", "boss_u + 0.3", "hinge_v - knuckle_r - 2", "boss_v_top + boss_lid_gap"))
    pd.cut(b, "Trou_axe", "YZ", f"-({k1}) - 1", f"({k1}) + 1", lambda s: pd.circle(s, "hinge_v", "hinge_w", "pin_d / 2"))
    return b


def build_spring(pd):
    b = pd.body("Ressort_Croix")
    a, aw, r = "spring_arm", "spring_arm_w / 2", "spring_foot_r"
    c = f"{a} - {aw}"
    pd.add(b, "Moyeu", "XY", "arm_front", "post_end", lambda s: pd.circle(s, 0, 0, "spring_hub_d / 2"))
    pd.add(b, "Bras_u", "XY", "arm_front", "post_end", lambda s: pd.profile(s, [
        ("L", (neg(c), neg(aw)), (c, neg(aw)), None), ("A", (c, 0), aw, -90, 90),
        ("L", (c, aw), (neg(c), aw), None), ("A", (neg(c), 0), aw, 90, 270)]))
    pd.add(b, "Bras_v", "XY", "arm_front", "post_end", lambda s: pd.profile(s, [
        ("A", (0, neg(c)), aw, 180, 360), ("L", (aw, neg(c)), (aw, c), None),
        ("A", (0, c), aw, 0, 180), ("L", (neg(aw), c), (neg(aw), neg(c)), None)]))
    pd.add(b, "Pieds", "XY", "foot_tip", "arm_front + 0.01", lambda s: [
        pd.circle(s, u, v, "spring_foot_d / 2") for u, v in ((r, 0), (neg(r), 0), (0, r), (0, neg(r)))])
    pd.cut(b, "Trou_pion", "XY", "arm_front - 1", "post_end + 1", lambda s: pd.circle(s, 0, 0, "spring_hole_d / 2"))
    return b


def build_slider(pd):
    """Rayfor latch slider, remodelled from its STL (rest position)."""
    b = pd.body("Glissiere_Verrou")
    pd.add(b, "Glissiere", "XY", "latch_skin", "latch_skin + slider_t", lambda s: pd.poly(s, [
        ("latch_u1", "latch_v1"), ("sl_tab_u1", "latch_v1"), ("sl_tab_u1", "sl_tab_v1"), ("sl_tab_u0", "sl_tab_v1"),
        ("sl_tab_u0", "latch_v1"), ("sl_u0", "latch_v1"), ("sl_u0", "sl_bar_v0"), ("sl_toothB_u1", "sl_bar_v0"),
        ("sl_toothB_u1", "sl_step_v0"), ("sl_step_u1", "sl_step_v0"), ("sl_step_u1", "sl_bar_v0"),
        ("latch_u1", "sl_bar_v0")]))
    # teeth: their back is the locking ramp the body claws ride on (thin at the tip, full at the root)
    s0, slope = "latch_skin", "(slider_t - sl_ramp_t0) / sl_ramp_len"
    pd.add(b, "Dent_rampe_droite", "XZ", "latch_v0", "sl_bar_v0 + 0.01", lambda s: pd.poly(s, [
        ("sl_toothA_u0", s0), ("latch_u1", s0), ("latch_u1", f"{s0} + slider_t"),
        ("sl_toothA_u0 + sl_ramp_len", f"{s0} + slider_t"), ("sl_toothA_u0", f"{s0} + sl_ramp_t0")]))
    pd.add(b, "Dent_rampe_gauche", "XZ", "latch_v0", "sl_bar_v0 + 0.01", lambda s: pd.poly(s, [
        ("sl_toothB_u0", s0), ("sl_toothB_u1", s0),
        ("sl_toothB_u1", f"{s0} + sl_ramp_t0 + (sl_toothB_u1 - sl_toothB_u0) * {slope}"),
        ("sl_toothB_u0", f"{s0} + sl_ramp_t0")]))
    pd.add(b, "Prise", "XY", "latch_skin + slider_t - 0.01", "latch_skin + slider_t + sl_grip_t",
           lambda s: pd.rect(s, "sl_tab_u0", "sl_tab_u1", "sl_grip_v0", "sl_tab_v1"))
    def knurl(s):
        for k in range(9):
            x0, f = f"knurl_u0 + {k} * knurl_pitch", "(knurl_base - knurl_top) / 2"
            pd.poly(s, [(x0, "sl_tab_v1 - 0.01"), (f"{x0} + knurl_base", "sl_tab_v1 - 0.01"),
                        (f"{x0} + knurl_base - {f}", "sl_tab_v1 + knurl_h"), (f"{x0} + {f}", "sl_tab_v1 + knurl_h")])
    pd.add(b, "Moletage", "XY", "latch_skin", "latch_skin + slider_t + sl_grip_t", knurl)
    return b


def build_cover(pd):
    """Rayfor latch cover, remodelled; flush with the rear face of piece 1."""
    b = pd.body("Capot_Verrou")
    pd.add(b, "Capot", "XY", "t1 - cover_t", "t1", lambda s: pd.poly(s, [
        ("cover_u0", "latch_v0"), ("cover_u1", "latch_v0"), ("cover_u1", "latch_v1"), ("tabopen_u1", "latch_v1"),
        ("tabopen_u1", "tab_v"), ("tabopen_u0", "tab_v"), ("tabopen_u0", "latch_v1"), ("cover_u0", "latch_v1")]))
    pd.cut(b, "Fenetres_griffes", "XY", "t1 - cover_t - 1", "t1 + 1", lambda s: (
        pd.rect(s, neg("latch_win_u1"), neg("latch_win_u0"), "latch_win_v0", "latch_win_v1"),
        pd.rect(s, "latch_win_u0", "latch_win_u1", "latch_win_v0", "latch_win_v1")))
    return b


def ref_box(doc, name, u0, u1, v0, v1, w0, w1):
    o = doc.addObject("Part::Box", name)
    o.setExpression("Length", f"({X(u1)}) - ({X(u0)})")
    o.setExpression("Width", f"({X(v1)}) - ({X(v0)})")
    o.setExpression("Height", f"({X(w1)}) - ({X(w0)})")
    for axis, e in (("x", u0), ("y", v0), ("z", w0)):
        o.setExpression(f".Placement.Base.{axis}", X(e))
    return o


def build(doc):
    sheet = doc.addObject("Spreadsheet::Sheet", SHEET)
    sheet.set("A1", "parametre"); sheet.set("B1", "valeur (mm)"); sheet.set("C1", "note")
    for i, (n, _, note) in enumerate(PARAMS, start=2):     # aliases first
        sheet.set(f"A{i}", n)
        sheet.set(f"B{i}", "0")
        sheet.setAlias(f"B{i}", n)
        if note:
            sheet.set(f"C{i}", "'" + note)
    for i, (n, e, _) in enumerate(PARAMS, start=2):        # then expressions
        sheet.set(f"B{i}", e if re.fullmatch(r"-?[\d.]+", e) else "=" + e)
    doc.recompute()
    pd = PD(doc)
    pieces = {"piece1_interface": build_piece1(pd), "piece2_cadre_verre": build_piece2(pd),
              "piece3_couvercle": build_piece3(pd), "ressort_croix": build_spring(pd),
              "glissiere_verrou": build_slider(pd), "capot_verrou": build_cover(pd)}
    refs = {
        "Verre_57x57": ref_box(doc, "Verre_57x57", "-glass / 2", "glass / 2", "-glass / 2", "glass / 2",
                               "film", "glass_back"),
        "Volet": ref_box(doc, "Volet", "-plate_u - 15", "slot_end - 0.4", "-slide_w / 2", "slide_w / 2",
                         "skin + (slot - slide_t) / 2", "skin + (slot + slide_t) / 2"),
    }
    doc.recompute()
    return pieces, refs


COLORS = {
    "piece1_interface": (0.15, 0.15, 0.17), "piece2_cadre_verre": (0.35, 0.35, 0.38),
    "piece3_couvercle": (0.22, 0.24, 0.30), "ressort_croix": (0.80, 0.45, 0.10),
    "Verre_57x57": (0.60, 0.80, 0.90), "Volet": (0.78, 0.79, 0.80),
    "glissiere_verrou": (0.75, 0.20, 0.20), "capot_verrou": (0.75, 0.40, 0.40),
    "Rayfor_glissiere": (0.75, 0.20, 0.20), "Rayfor_capot": (0.75, 0.40, 0.40),
}


def rayfor_part(name):
    """Rayfor latch parts moved into our frame: u = 49 - x, v = 92.08 - z, w = 16.22 - y."""
    path = os.path.join(ROOT, "sources", "hasselblad-v-mount-for-imacon-digital-back-model_files", name)
    m = Mesh.Mesh(path)
    m.transform(App.Matrix(-1, 0, 0, 49.0, 0, 0, -1, 92.08, 0, -1, 0, 16.22, 0, 0, 0, 1))
    s = Part.Shape()
    s.makeShapeFromMesh(m.Topology, 0.05)
    return Part.Solid(Part.Shell(s.Faces))


def finish(doc, pieces, refs):
    """Containers, visibility (bodies show their tip only), colour map for the GUI file."""
    asm = doc.addObject("App::Part", "Cassette")
    ref = doc.addObject("App::Part", "References")
    colors = {}
    for key, body in pieces.items():
        asm.addObject(body)
        for f in body.Group:
            f.Visibility = f is body.Tip
            if f.isDerivedFrom("PartDesign::Feature"):
                colors[f.Name] = (COLORS[key], 0)
        body.Visibility = True
        colors[body.Name] = (COLORS[key], 0)
    for key, o in refs.items():
        ref.addObject(o)
        colors[o.Name] = (COLORS[key], 60 if key.startswith("Verre") else 0)
    for key, fname in (("Rayfor_glissiere", "imacon_V_-_Latch-1.STL"),
                       ("Rayfor_capot", "imacon_V_-_LatchCover-1.STL")):
        o = doc.addObject("Part::Feature", key)
        o.Shape = rayfor_part(fname)
        o.Visibility = False                  # original STL, kept for comparison
        ref.addObject(o)
        colors[o.Name] = (COLORS[key], 0)
    for o in doc.Objects:                     # origin axes and planes
        if o.TypeId in ("App::Origin", "App::Line", "App::Plane", "App::Point"):
            o.Visibility = False
    doc.recompute()
    return colors


def _appearance(rgb, transparency):
    """ShapeAppearance file (PropertyMaterialList v3, one material)."""
    r, g, b = (int(round(c * 255)) for c in rgb)
    pack = lambda r, g, b: (r << 24) | (g << 16) | (b << 8) | 0xFF  # noqa: E731
    return struct.pack("<IIIIIffIII", 1, pack(0x55, 0x55, 0x55), pack(r, g, b), pack(0x88, 0x88, 0x88),
                       pack(0, 0, 0), 0.9, transparency / 100.0, 0, 0, 0)


def write_gui_document(path, doc, colors):
    """GuiDocument.xml written without a GUI: visibility and colours.

    FreeCAD hides every object of a file whose GuiDocument.xml lacks
    HasExpansion="1" + <Expand />, and stops reading at a missing <Camera>."""
    cam = ("OrthographicCamera {&#10;  viewportMapping ADJUST_CAMERA&#10;  position 160 -160 140&#10;"
           "  orientation -0.74 -0.31 -0.6 1.15&#10;  nearDistance 1&#10;  farDistance 1000&#10;"
           "  aspectRatio 1&#10;  focalDistance 260&#10;  height 160&#10;&#10;}&#10;")
    vps, files = [], {}
    for o in doc.Objects:
        props = [("Visibility", "App::PropertyBool", f'<Bool value="{"true" if o.Visibility else "false"}"/>')]
        if o.Name in colors:
            rgb, tr = colors[o.Name]
            fname = f"ShapeAppearance_{o.Name}"
            files[fname] = _appearance(rgb, tr)
            props += [("ShapeAppearance", "App::PropertyMaterialList", f'<MaterialList file="{fname}" version="3"/>'),
                      ("Transparency", "App::PropertyPercent", f'<Integer value="{tr}"/>')]
        body = "\n".join(f'                <Property name="{n}" type="{ty}" status="1">\n'
                         f'                    {v}\n                </Property>' for n, ty, v in props)
        vps.append(f'        <ViewProvider name="{o.Name}" expanded="0" treeRank="-1">\n'
                   f'            <Properties Count="{len(props)}" TransientCount="0">\n{body}\n'
                   f'            </Properties>\n        </ViewProvider>')
    xml = ("<?xml version='1.0' encoding='utf-8'?>\n<Document SchemaVersion=\"1\" HasExpansion=\"1\">\n"
           "    <Expand />\n"
           f'    <ViewProviderData Count="{len(vps)}">\n' + "\n".join(vps) + "\n    </ViewProviderData>\n"
           f'    <Camera settings="{cam}"/>\n</Document>\n')
    with zipfile.ZipFile(path) as z:
        if "GuiDocument.xml" in z.namelist():
            return
    with zipfile.ZipFile(path, "a") as z:
        z.writestr("GuiDocument.xml", xml)
        for fname, data in files.items():
            z.writestr(fname, data)


def write_csv():
    with open(os.path.join(ROOT, "cad", "parameters.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["name", "expression", "unit", "note"])
        for n, e, note in PARAMS:
            w.writerow([n, e, "mm", note])


def invalid_objects(doc):
    return [o.Name for o in doc.Objects if "Invalid" in o.State or "Error" in o.State]


def underconstrained(doc):
    """Sketches with remaining degrees of freedom."""
    out = []
    for o in doc.Objects:
        if o.TypeId == "Sketcher::SketchObject":
            o.solve()
            if not o.FullyConstrained:
                out.append(o.Name)
    return out


def check_sheet(doc):
    """The sheet and the Python evaluator must agree, parameter by parameter."""
    sheet, vals = doc.getObject(SHEET), param_values()
    return [n for n in vals if abs(float(sheet.get(n)) - vals[n]) > 1e-9]


# --- Build, export, check --------------------------------------------------
def export(shape, name):
    mesh = MeshPart.meshFromShape(Shape=shape, LinearDeflection=0.02, AngularDeflection=0.2)
    mesh.write(os.path.join(OUT, name + ".stl"))
    shape.exportStep(os.path.join(OUT, name + ".step"))


def lid_rotated(shape, deg, hv, hw):
    pl = App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), deg), V(0, hv, hw))
    return shape.transformGeometry(pl.toMatrix())


def build_document():
    doc = App.newDocument("cassette")
    pieces, refs = build(doc)
    colors = finish(doc, pieces, refs)
    return doc, pieces, refs, colors


def run_checks(doc, pieces, refs, verbose=True):
    say = print if verbose else (lambda *a, **k: None)
    ok = True
    shapes = {k: o.Shape for k, o in pieces.items()}
    for name, s in shapes.items():
        bb = s.BoundBox
        valid = s.isValid() and len(s.Solids) == 1
        ok &= valid
        say(f"{name:20s} valid={valid} solids={len(s.Solids)} vol={s.Volume:9.0f} mm3  "
            f"u[{bb.XMin:.2f},{bb.XMax:.2f}] v[{bb.YMin:.2f},{bb.YMax:.2f}] w[{bb.ZMin:.2f},{bb.ZMax:.2f}]",
            flush=True)
    p1, p2, p3, sp = (shapes[k] for k in ("piece1_interface", "piece2_cadre_verre",
                                          "piece3_couvercle", "ressort_croix"))
    gl, ds = refs["Verre_57x57"].Shape, refs["Volet"].Shape
    latch, cover = shapes["glissiere_verrou"], shapes["capot_verrou"]
    travel = App.Placement(V(-param_values()["sl_travel"], 0, 0), App.Rotation())
    latch_on = latch.transformGeometry(travel.toMatrix())
    pairs = [("p1-p2", p1, p2), ("p1-p3", p1, p3), ("p2-p3", p2, p3),
             ("glass-p1", gl, p1), ("glass-p2", gl, p2), ("glass-p3", gl, p3),
             ("slide-p1", ds, p1), ("slide-p2", ds, p2),
             ("spring-p1", sp, p1), ("spring-p2", sp, p2),
             ("latch-p1", latch, p1), ("cover-p1", cover, p1), ("cover-p2", cover, p2),
             ("latch-p2", latch, p2), ("latch-cover", latch, cover),
             ("latch_locked-p1", latch_on, p1), ("latch_locked-cover", latch_on, cover)]
    say("\nInterferences (mm3, expected 0):")
    for name, a, b in pairs:
        c = a.common(b)
        # Rayfor meshes share faces with our pockets: slivers thinner than 0.05 mm are contacts
        real = [s for s in c.Solids if s.Area > 0 and 2 * s.Volume / s.Area > 0.05]
        v = sum(s.Volume for s in real)
        ok &= v < 0.01
        note = "  (contact)" if c.Volume > 0.01 and v < 0.01 else ""
        say(f"  {name:12s} {v:8.3f}{'' if v < 0.01 else '  <-- !'}{note}")
    say(f"  spring-glass {sp.common(gl).Volume:8.3f}  (preload: expected > 0, feet only)")
    shift = {"glissiere_verrou": param_values()["latch_skin"] - 1.0, "capot_verrou": 0.0}
    for key, ref in (("glissiere_verrou", "Rayfor_glissiere"), ("capot_verrou", "Rayfor_capot")):
        r = doc.getObject(ref).Shape.transformGeometry(
            App.Placement(V(0, 0, shift[key]), App.Rotation()).toMatrix())
        say(f"  {key}: volume {shapes[key].Volume:.1f} vs Rayfor STL {r.Volume:.1f} mm3, "
            f"difference {shapes[key].cut(r).Volume + r.cut(shapes[key]).Volume:.1f} mm3")
    vals = param_values()
    say("\nLid opening sweep (common volume with pieces 1+2):")
    p12 = p1.fuse(p2)
    for deg in (5, 15, 30, 60, 90, 120):
        v = lid_rotated(p3, deg, vals["hinge_v"], vals["hinge_w"]).common(p12).Volume
        ok &= v < 0.01
        say(f"  {deg:4d} deg  {v:8.3f}")
    return ok, shapes


def main():
    os.makedirs(OUT, exist_ok=True)
    doc, pieces, refs, colors = build_document()
    bad = invalid_objects(doc) + check_sheet(doc)
    if bad:
        print("INVALID or sheet mismatch:", bad, flush=True)
        return False
    loose = underconstrained(doc)
    print(f"sketches: {sum(o.TypeId == 'Sketcher::SketchObject' for o in doc.Objects)}, "
          f"not fully constrained: {loose or 'none'}", flush=True)
    ok, shapes = run_checks(doc, pieces, refs)
    ok &= not loose
    for name, s in shapes.items():
        export(s, name)
    doc.saveAs(FCSTD)
    write_gui_document(FCSTD, doc, colors)
    App.closeDocument(doc.Name)
    for f in os.listdir(OUT):
        if f.endswith(".FCBak"):
            os.remove(os.path.join(OUT, f))
    write_csv()
    vals = param_values()
    print(f"\nEmulsion plane at w = {vals['film']} ; dark slide gap w {vals['skin']}..{vals['ledge_w']:.2f}")
    print("ALL CHECKS OK" if ok else "CHECKS FAILED", flush=True)
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
