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
import random
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

sys.path.append("/Applications/FreeCAD.app/Contents/Resources/Mod/Assembly")
import JointObject  # noqa: E402

V = App.Vector
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "exports")
FCSTD = os.path.join(OUT, "cassette_ferrotype.FCStd")
SHEET = "Parametres"

# --- Parameter table: (name, expression, note) -----------------------------
# Expressions use other names of the table; numbers are mm. Names are French:
# they are what the user reads in the sheet. Frame seen from the rear: x to the
# right (gauche / droite), y up (bas / haut), z = depth from the mating face.
PARAMS = [
    # Body interface (Rayfor V mount)
    ("plaque_demi_largeur", "42.2", "demi-largeur de la plaque"),
    ("plaque_bord_haut", "43.05", "bord haut (cote verrou)"),
    ("plaque_bord_bas", "-43.04", "bord bas (cote crochets)"),
    ("rayon_coins", "3", "rayon des coins"),
    ("languette_demi_largeur", "32", "demi-largeur de la languette haute"),
    ("languette_bord_haut", "45.8", "bord haut de la languette"),
    ("languette_demi_largeur_pied", "34.95", "languette : demi-largeur au pied des pans"),
    ("talon_bord_droit", "48.5", "talon cote manivelle : bord droit"),
    ("talon_demi_hauteur", "37.5", "talon : demi-hauteur"),
    ("piece1_epaisseur", "6.7", "epaisseur de la piece 1"),
    ("gorge_cote_interieur", "70.7", "gorge de la face d'appui (recoit la levre du boitier) : cote interieur du carre"),
    ("gorge_largeur", "1.5", "gorge : largeur"),
    ("gorge_profondeur", "0.5", "gorge : profondeur"),
    ("gorge_interieure_cote_interieur", "59", "deuxieme gorge de la face d'appui (recoit la levre interieure du boitier) : cote interieur du carre"),
    ("gorge_interieure_largeur", "1", "deuxieme gorge : largeur (carre exterieur 61)"),
    ("gorge_interieure_profondeur", "1", "deuxieme gorge : profondeur"),
    ("ergots_profondeur", "5.9", "poches des ergots du boitier"),
    ("ergot1_gauche", "39", ""), ("ergot1_droite", "42", ""),
    ("ergot1_bas", "2.76", ""), ("ergot1_haut", "19.76", ""),
    ("ergot2_gauche", "39.5", ""), ("ergot2_droite", "41.5", ""),
    ("ergot2_bas", "-28.49", ""), ("ergot2_haut", "-23.99", ""),
    ("fenetre_griffe_gauche", "11.75", "fenetres des griffes (symetriques)"),
    ("fenetre_griffe_droite", "18.2", ""),
    ("fenetre_griffe_bas", "39.25", ""), ("fenetre_griffe_haut", "40.86", ""),
    ("verrou_paroi", "0.8", "paroi devant la poche du verrou (1.0 trop epais a l'essai)"),
    ("glissiere_epaisseur", "3", "glissiere : epaisseur"),
    ("verrou_poche_fond", "verrou_paroi + glissiere_epaisseur + 0.2", "fond de la poche du verrou"),
    ("verrou_poche_gauche", "-18.2", "poche de la glissiere Rayfor"), ("verrou_poche_droite", "26.2", ""),
    ("verrou_poche_bas", "37.25", ""), ("verrou_poche_haut", "44.3", ""),
    ("verrou_ilot_droite", "11.75", "ilot de guidage dans la poche (taquet du ressort) : bord droit"),
    ("verrou_ilot_haut", "40.25", ""),
    ("capot_gauche", "-24.2", "poche du capot Rayfor"), ("capot_droite", "32.2", ""),
    ("verrou_jeu", "0.2", "jeu par cote de la glissiere et du capot Rayfor"),
    ("passage_languette_gauche", "-6.2", "passage de la languette de la glissiere"), ("passage_languette_droite", "14.2", ""),
    ("encoche_crochet_gauche", "23.8", "encoches des crochets (symetriques)"), ("encoche_crochet_droite", "30.3", ""),
    ("encoche_crochet_hauteur", "1.55", ""), ("encoche_crochet_levre", "1.1", "levre gardee cote boitier"),
    # Film plane and dark slide stack
    ("plan_film", "3.55", "face d'appui -> emulsion"),
    ("peau_epaisseur", "1.9", "peau avant de la piece 1"),
    ("fente_epaisseur", "0.4", "epaisseur de la fente du volet"),
    ("butee_face_avant", "peau_epaisseur + fente_epaisseur", "face avant de la butee du verre"),
    ("volet_largeur", "65.88", "volet : largeur de la plaque metal mesuree"),
    ("fente_jeu", "0.5", "jeu total du volet en hauteur"),
    ("fente_demi_hauteur", "(volet_largeur + fente_jeu) / 2", "demi-hauteur de la fente"),
    ("fente_fond", "30.9", "butee de fond du volet (u)"),
    ("volet_epaisseur", "0.3", "volet : epaisseur (reference)"),
    ("verre_cote", "57", "verre : cote (57 x 57)"),
    ("verre_epaisseur_min", "1", "verres acceptes : du plus fin..."),
    ("verre_epaisseur_max", "3", "...au plus epais (le logement et le ressort suivent)"),
    ("verre_epaisseur", "verre_epaisseur_min", "verre affiche dans le modele"),
    ("verre_jeu", "0.2", "jeu du verre par cote"),
    ("verre_face_arriere", "plan_film + verre_epaisseur", "dos du verre"),
    ("butee_appui", "1", "appui du verre sur la butee, par cote"),
    ("butee_ouverture", "verre_cote - 2 * butee_appui", "ouverture de la butee = image"),
    ("peau_ouverture", "55", "ouverture de la peau avant, comme la butee de la piece 2 (la levre interieure du boitier entre dans la deuxieme gorge)"),
    # Insert pocket (piece 1) / insert (piece 2)
    ("poche_cadre_droite", "34", "poche de la piece 2 : bord droit"),
    ("poche_cadre_demi_hauteur", "34.8", "poche de la piece 2 : demi-hauteur (reste a l'interieur de la gorge)"),
    ("cadre_jeu", "0.2", "jeu insert / poche"),
    ("aimant_diametre", "6", "aimants : diametre (dans la bande entre le rail du couvercle et le bord)"),
    ("aimant_epaisseur", "2", "aimants : epaisseur (la collerette de la piece 2 suit)"),
    ("aimant_jeu", "0.2", "logements des aimants : jeu au diametre et en profondeur"),
    ("aimant_peau", "0.4", "aimants incrustes : peau entre l'aimant et le joint (pause d'impression pour les poser)"),
    ("aimant_couverture", "0.8", "matiere au-dessus de la cavite de l'aimant dans la piece 2"),
    ("collerette_epaisseur", "aimant_peau + aimant_epaisseur + aimant_jeu + aimant_couverture", "collerette de la piece 2 : epaisseur (porte les aimants incrustes)"),
    ("collerette_face_arriere", "piece1_epaisseur + collerette_epaisseur", "face arriere de la piece 2"),
    ("velours_gauche", "-41.2", "gorges du velours a l'entree de la fente"), ("velours_droite", "-38.2", ""),
    ("velours_profondeur", "0.6", ""),
    # Light traps between piece 1 and piece 2
    ("chicane_axe", "36.1", "chicane collerette : axe (haut, bas, droite)"),
    ("chicane_bout_gauche", "-40.2", "chicane collerette : bout gauche"),
    ("chicane_gorge_largeur", "1", "chicane collerette : largeur de la gorge"), ("chicane_gorge_profondeur", "1", "profondeur de la gorge"),
    ("chicane_nervure_largeur", "0.6", "largeur de la nervure"), ("chicane_nervure_hauteur", "0.8", "hauteur de la nervure"),
    ("chicane_rails_axe", "33.9", "chicane des rails : axe (haut, bas)"),
    ("chicane_rails_axe_droit", "32.35", "chicane des rails : axe du cote droit"),
    ("chicane_rails_gorge_largeur", "0.9", "largeur de la gorge dans le fond de la piece 1"), ("chicane_rails_gorge_profondeur", "0.6", ""),
    ("chicane_rails_nervure_largeur", "0.5", "largeur de la nervure sous les rails"), ("chicane_rails_nervure_hauteur", "0.5", ""),
    ("griffes_degagement", "0.3", "degagement des griffes dans la collerette (par cote)"),
    # Screws M3 x 6 countersunk
    ("vis_bas_x", "38", "vis du bas, dans les coins, paire symetrique : x"), ("vis_bas_y", "-39", "y (0,9 de paroi entre la fraisure et le bord)"),
    ("vis_haut_x", "-28", "vis du haut, a gauche du verrou : x"), ("vis_haut_y", "39", ""),
    ("vis_haut_droite_x", "37", "vis du haut a droite du verrou, hors du capot : x (l'ancienne vis du talon tombait dans le couloir)"),
    ("avant_trou_diametre", "2.5", "avant-trou piece 1 (vis M3 x 8 fraisees)"), ("avant_trou_profondeur", "5.5", ""),
    ("vis_passage_diametre", "3.4", "passage piece 2"), ("vis_fraisure_diametre", "6.2", "fraisure 90 deg"),
    # Lid
    ("couvercle_hauteur", "7.4", "couvercle plein, dans le prolongement de la piece 2 : hauteur (prise ; matiere contre la transparence du PETG)"),
    ("couvercle_face_exterieure", "collerette_face_arriere + couvercle_hauteur", "face exterieure du couvercle"),
    # Sliding lid: dovetail rails in piece 2 (top and bottom), closed on the left and
    # open on the right; the lid sole slides in a channel over the glass
    ("couvercle_jeu", "0.2", "jeu du couvercle coulissant (rails, couloir, butees)"),
    ("couloir_demi_hauteur", "verre_cote / 2 + verre_jeu + couvercle_jeu", "couloir de la piece 2 ou glisse la semelle du couvercle : demi-hauteur"),
    ("couloir_gauche", "-(verre_cote / 2 + verre_jeu + couvercle_jeu)", "couloir : bord gauche (ferme) ; il sort par la droite"),
    ("couloir_fond", "piece1_epaisseur + 0.6", "couloir : fond (0,6 de collerette sur la piece 1)"),
    ("semelle_dessous", "couloir_fond + couvercle_jeu", "dessous de la semelle du couvercle (au-dessus du verre le plus epais)"),
    ("rail_axe", "32.1", "rails du couvercle (haut et bas) : axe ; ils sortent par la face droite du talon"),
    ("levre_gauche_largeur", "1.5", "levre du bord gauche de la piece 2 (chicane), coiffee par une feuillure du couvercle : largeur"),
    ("levre_gauche_hauteur", "1.2", "levre gauche : hauteur au-dessus de la face arriere de la piece 2"),
    ("rail_gauche", "-plaque_demi_largeur + levre_gauche_largeur", "rails : bout gauche, ferme, au pied de la levre gauche"),
    ("rail_gorge_largeur", "1.6", "rails : gorge (chicane de la languette) : largeur"),
    ("rail_gorge_hauteur", "0.8", "rails : gorge : hauteur"),
    ("rail_queue_hauteur", "1.4", "rails : queue d'aronde a 45 deg sous la gorge : hauteur"),
    ("rail_fond", "collerette_face_arriere - rail_gorge_hauteur - rail_queue_hauteur", "fond des rails"),
    ("rail_queue_demi_largeur", "rail_gorge_largeur / 2 + rail_queue_hauteur", "rails : demi-largeur au fond"),
    ("languette_rail_demi_largeur", "rail_gorge_largeur / 2 - couvercle_jeu", "languette continue du couvercle dans la gorge du rail : demi-largeur"),
    ("languette_rail_bas", "collerette_face_arriere - rail_gorge_hauteur - couvercle_jeu", "languette : bas"),
    ("tete_longueur", "12", "queues d'aronde du couvercle, a son bout gauche : longueur"),
    ("tete_bas", "rail_fond + couvercle_jeu", "queue d'aronde : bas"),
    ("tete_jeu", "0.1", "jeu des queues d'aronde sur leurs pans (en horizontal) : le bord gauche du couvercle ne monte que d'autant sous la poussee des lames"),
    ("tete_demi_largeur", "rail_queue_demi_largeur - couvercle_jeu - tete_jeu", "queue d'aronde : demi-largeur en bas"),
    ("tete_epaule", "tete_bas + tete_demi_largeur - languette_rail_demi_largeur", "queue d'aronde : haut du pan a 45 deg"),
    ("couvercle_degagement", "1.5", "couvercle ouvert : son bord gauche depasse le logement du verre de"),
    ("couvercle_course", "plaque_demi_largeur + verre_cote / 2 + verre_jeu + couvercle_degagement", "course du couvercle vers la droite"),
    ("goupille_diametre", "2", "goupilles de butee : bouts de tige"),
    ("goupille_trou_diametre", "goupille_diametre + 0.1", ""),
    ("goupille_x", "rail_gauche + couvercle_jeu + tete_longueur + couvercle_course + couvercle_jeu + goupille_diametre / 2", "goupilles : position (elles arretent les queues d'aronde en fin de course)"),
    ("goupille_enfoncement", "2.5", "goupille : profondeur dans la piece 1"),
    ("goupille_haut", "languette_rail_bas - couvercle_jeu", "haut des goupilles (la languette passe au-dessus)"),
    ("goupille_longueur", "goupille_haut - piece1_epaisseur + goupille_enfoncement", "goupille : longueur"),
    ("fente_couvercle_profondeur", "1.7", "fente dans la paroi gauche du couloir (chicane) : profondeur"),
    ("languette_gauche_longueur", "1.5", "languette du bout de la semelle, dans la fente"),
    ("languette_gauche_epaisseur", "0.8", ""),
    ("languette_gauche_bas", "semelle_dessous + 0.9", ""),
    ("levre_epaisseur", "1.5", "levre du bout droit du couvercle (butee de fermeture, chicane) : epaisseur"),
    ("levre_bas", "5", "levre : bas, devant la face droite du talon de la piece 1"),
    # Magnetic closure
    ("aimant_x", "28", "aimants : x (en haut et en bas, vers le bout droit du couvercle)"),
    ("aimant_y", "(plaque_bord_haut + rail_axe + rail_queue_demi_largeur) / 2", "au milieu de la bande entre le rail et le bord"),
    # Leaf spring (separate printed part glued under the lid sole): presses the glass
    ("lames_epaisseur", "1.2", "ressort a lames : epaisseur"), ("lames_largeur", "8", "lames : largeur"),
    ("lames_axe", "15", "lames : axe (paire symetrique)"),
    ("lames_racine_largeur", "4", "barre de racine (collee dans le couvercle) : largeur"),
    ("lames_racine_droite", "-19", "racine : bord droit, depart des lames"),
    ("lames_longueur", "24", "lames : longueur, de la racine au milieu du patin"),
    ("lames_precharge", "1.5", "ecrasement sur le verre le plus fin (le plus epais ajoute la difference)"),
    ("patin_largeur_bas", "1", "patins : plat d'appui"),
    ("patin_bas", "plan_film + verre_epaisseur_min - lames_precharge", "bas des patins, lames libres"),
    ("patin_hauteur", "semelle_dessous - patin_bas", "patins : hauteur (chanfreins a 45 deg des deux cotes : ils montent les marches)"),
    ("patin_x", "lames_racine_droite + lames_longueur", "milieu des patins"),
    ("chambre_lames_haut", "semelle_dessous + lames_epaisseur + couloir_fond - patin_bas + 0.5", "plafond de la chambre des lames : lames soulevees sur le fond du couloir + 0,5"),
    # Latch slider and cover (Rayfor, remodelled; slider at rest)
    ("glissiere_gauche", "-14.7", "glissiere : bout gauche"), ("glissiere_barre_bas", "41.25", "glissiere : bas de la barre"),
    ("glissiere_dent_droite_bout", "18.25", "dent droite : bout (la dent va jusqu'a verrou_poche_droite)"),
    ("glissiere_dent_gauche_bout", "-11.75", "dent gauche : bout"), ("glissiere_dent_gauche_pied", "-5.25", "dent gauche : pied"),
    ("glissiere_rampe_epaisseur_bout", "0.81", "rampe de verrouillage : epaisseur au bout de la dent"),
    ("glissiere_rampe_longueur", "6.59", "rampe : longueur jusqu'a pleine epaisseur (environ 18 deg)"),
    ("glissiere_guide_bas", "40.46", "guide au-dessus de l'ilot"), ("glissiere_guide_droite", "11.16", ""),
    ("glissiere_languette_gauche", "-2.7", "languette : bords"), ("glissiere_languette_droite", "14.2", ""),
    ("glissiere_languette_haut", "48.3", "languette : bout"),
    ("glissiere_prise_bas", "46.31", "prise : debut (hors de la plaque)"), ("glissiere_prise_surepaisseur", "1.7", "prise : surepaisseur"),
    ("moletage_debut", "-2.7", "moletage : pied de la 1re dent"), ("moletage_pas", "1.92", ""),
    ("moletage_dent_pied", "1.5", "dent trapezoidale : pied"), ("moletage_dent_sommet", "0.75", "dent : sommet"),
    ("moletage_hauteur", "0.66", ""),
    ("glissiere_course", "3.5", "course de la glissiere (vers u negatif)"),
    ("capot_epaisseur", "2.4", "capot : epaisseur (affleure la face arriere de la piece 1)"),
    # Latch spring (compression, bought), in the pocket between the left tooth of
    # the slider and the island: pushes the slider towards locked
    ("ressort_verrou_diametre", "2", "ressort du verrou : diametre exterieur"),
    ("ressort_verrou_longueur_libre", "10", "ressort du verrou : longueur libre"),
    ("ressort_verrou_precharge", "1", "ressort du verrou : ecrasement glissiere verrouillee (il pousse encore)"),
    ("ressort_verrou_longueur_ferme", "ressort_verrou_longueur_libre - ressort_verrou_precharge", "longueur du ressort, glissiere verrouillee"),
    ("ressort_verrou_longueur_ouvert", "ressort_verrou_longueur_ferme - glissiere_course", "longueur du ressort, glissiere poussee a droite (deverrouillee)"),
    ("verrou_ilot_gauche", "glissiere_dent_gauche_pied - glissiere_course + ressort_verrou_longueur_ferme - verrou_jeu", "ilot (taquet du ressort) : bord gauche, a la longueur du ressort verrouille de la dent gauche"),
    ("ressort_verrou_y", "(verrou_poche_bas + glissiere_guide_bas) / 2", "axe du ressort : entre le fond de la poche et le guide de la glissiere"),
    ("ressort_verrou_z", "verrou_paroi + glissiere_epaisseur / 2", "axe du ressort : milieu de la glissiere"),
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


def param_values(rng=None):
    """Pure-Python evaluation of the table (same expressions as the sheet).
    With rng, every literal parameter is scaled at random: a relation that holds
    for both evaluations is structural, not a coincidence of the defaults."""
    vals = {}
    for n, e, _ in PARAMS:      # the sheet separates function arguments with ';'
        vals[n] = eval(e.replace(";", ","), {"__builtins__": {}, "max": max, "min": min}, dict(vals))
        if rng and re.fullmatch(r"-?[\d.]+", e):
            vals[n] *= rng.uniform(0.7, 1.3)
    return vals


def paren(e):
    e = str(e)
    return e if re.fullmatch(r"-?[\w.]+", e) else f"({e})"


# --- Sketch-based builder ---------------------------------------------------
# Sketch planes of a body origin: XY (local u, v; offset = w), YZ (local v, w;
# offset = u), XZ (local u, w; normal -Y, so offset = -v).
PLANES = {"XY": "XY_Plane", "YZ": "YZ_Plane", "XZ": "XZ_Plane"}
DEG = math.pi / 180
WARNINGS = []    # edges horizontal / vertical only by coincidence of the defaults


class PD:
    """Sketches dimensioned like a drawing: horizontal / vertical edges, widths,
    heights, diameters, symmetry about the axes, positions measured from the axes.
    Every dimension is a named constraint driven by the sheet."""

    def __init__(self, doc):
        self.doc = doc
        self.vals = param_values()
        self.alt = param_values(random.Random(7))
        self.labels = {}      # sketch name -> profile labels used
        self.rects = {}       # sketch name -> rectangles drawn, to spot mirrored pairs

    def ev(self, e, vals=None):
        if isinstance(e, (int, float)):
            return float(e)
        return float(eval(e, {"__builtins__": {}}, dict(vals or self.vals)))

    def same(self, a, b):
        return all(abs(self.ev(a, d) - self.ev(b, d)) < 1e-9 for d in (self.vals, self.alt))

    def mirror(self, a, b):
        """a = -b for any parameter values (and not both zero)."""
        return abs(self.ev(a)) > 1e-9 and all(abs(self.ev(a, d) + self.ev(b, d)) < 1e-9
                                              for d in (self.vals, self.alt))

    def diff(self, b, a):
        """Expression of b - a, written as a drawing would read it."""
        if self.mirror(a, b):
            half = re.fullmatch(r"([\w.]+|\(.*\)) / 2", str(b))
            return half.group(1) if half else f"2 * {paren(b)}"
        if self.same(a, 0):
            return str(b)
        m = re.fullmatch(r"-\((.*)\)", str(a))
        return f"{paren(b)} + {paren(m.group(1))}" if m else f"{paren(b)} - {paren(a)}"

    def body(self, label):
        return self.doc.addObject("PartDesign::Body", label)

    def _label(self, sk, label):
        """Prefix of a profile's dimension names, unique in the sketch (none for the first unnamed one)."""
        used = self.labels.setdefault(sk.Name, set())
        name, k = label or "", 1
        while name in used:
            k += 1
            name = f"{label or 'profil'}_{k}"
        used.add(name)
        return name + "_" if name else ""

    def dim(self, sk, cons, e, name):
        c = sk.addConstraint(cons)
        sk.renameConstraint(c, name)
        if not isinstance(e, (int, float)):
            sk.setExpression(f".Constraints.{name}", X(e))

    def con(self, sk, *args):
        sk.addConstraint(Sketcher.Constraint(*args))

    def dist(self, sk, p, q, a, b, name, kind="DistanceX"):
        """Distance along u (DistanceX) or v (DistanceY) between point p at a and point q at b."""
        if self.ev(b) < self.ev(a):
            p, q, a, b = q, p, b, a
        self.dim(sk, Sketcher.Constraint(kind, *p, *q, self.ev(b) - self.ev(a)), self.diff(b, a), name)

    def anchor(self, sk, p, e, axis, name):
        """Place point p at coordinate e along u or v, measured from the axis."""
        if self.same(e, 0):
            self.con(sk, "PointOnObject", *p, -2 if axis == "u" else -1)
        else:
            kind = "DistanceX" if axis == "u" else "DistanceY"
            self.dim(sk, Sketcher.Constraint(kind, -1, 1, *p, self.ev(e)), e, name)

    def _simplest(self, exprs):
        """Index of the coordinate a drawing would dimension: zero, then a bare name, then nearest the axis."""
        return min(range(len(exprs)), key=lambda i: (not self.same(exprs[i], 0), len(str(exprs[i])),
                                                     abs(self.ev(exprs[i]))))

    def poly(self, sk, pts, label=None):
        """Closed polygon: horizontal / vertical edges, one length per edge along u
        and v (the closing one follows from the others), symmetry about an axis when
        an edge is centred on it, otherwise one corner placed from the axes."""
        label = self._label(sk, label)
        p = [V(self.ev(u), self.ev(v), 0) for u, v in pts]
        n, g0 = len(p), sk.GeometryCount
        for i in range(n):
            sk.addGeometry(Part.LineSegment(p[i], p[(i + 1) % n]))
        for i in range(n):
            self.con(sk, "Coincident", g0 + i, 2, g0 + (i + 1) % n, 1)
        ends = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
        flat = [[abs(p[i][k] - p[(i + 1) % n][k]) < 1e-9 for i in range(n)] for k in (0, 1)]  # du = 0, dv = 0
        for k in (0, 1):
            for i in range(n):
                if flat[k][i] and not self.same(ends[i][0][k], ends[i][1][k]):
                    WARNINGS.append(f"{sk.Name}: edge {i + 1} {'vertical' if k == 0 else 'horizontal'} "
                                         "only for the default values")
        # an edge centred on an axis: symmetric about it (replaces H or V + one position)
        sym = [next((i for i in range(n) if flat[1 - k][i] and self.mirror(ends[i][0][k], ends[i][1][k])), None)
               for k in (0, 1)]
        for i in range(n):
            if flat[1][i] and i != sym[0]:
                self.con(sk, "Horizontal", g0 + i)
            if flat[0][i] and i != sym[1]:
                self.con(sk, "Vertical", g0 + i)
        for k, axis in ((0, -2), (1, -1)):
            if sym[k] is not None:
                self.con(sk, "Symmetric", g0 + sym[k], 1, g0 + sym[k], 2, axis)
        for k, (kind, ax) in enumerate((("DistanceX", "u"), ("DistanceY", "v"))):
            edges = [i for i in range(n) if not flat[k][i]]
            skip = max((i for i in edges if i != sym[k]),
                       key=lambda i: (len(str(ends[i][0][k])) + len(str(ends[i][1][k])), i))
            for i in edges:
                if i != skip:
                    self.dist(sk, (g0 + i, 1), (g0 + i, 2), ends[i][0][k], ends[i][1][k],
                              f"{label}{'largeur' if k == 0 else 'hauteur'}_{i + 1}", kind)
            if sym[k] is None:
                i = self._simplest([q[k] for q in pts])
                self.anchor(sk, (g0 + i, 1), pts[i][k], ax, f"{label}position_{'xy'[k]}")

    def rect(self, sk, u0, u1, v0, v1, label=None):
        """Rectangle: width, height, centred on an axis by symmetry or placed from it;
        the mirror of a rectangle already in the sketch is tied to it (equal, symmetric)."""
        label = self._label(sk, label)
        c = [V(self.ev(u), self.ev(v), 0) for u, v in ((u0, v0), (u1, v0), (u1, v1), (u0, v1))]
        g = sk.GeometryCount
        for i in range(4):
            sk.addGeometry(Part.LineSegment(c[i], c[(i + 1) % 4]))
        for i in range(4):
            self.con(sk, "Coincident", g + i, 2, g + (i + 1) % 4, 1)
        bottom, right, top, left = g, g + 1, g + 2, g + 3
        self.con(sk, "Horizontal", top)
        self.con(sk, "Vertical", left)
        twin = next((r for r in self.rects.get(sk.Name, []) if self.mirror(u0, r[1]) and self.mirror(u1, r[0])
                     and self.same(v0, r[2]) and self.same(v1, r[3])), None)
        self.rects.setdefault(sk.Name, []).append((u0, u1, v0, v1, g))
        if twin:
            self.con(sk, "Horizontal", bottom)
            self.con(sk, "Vertical", right)
            self.con(sk, "Equal", twin[4], bottom)
            self.con(sk, "Equal", twin[4] + 1, right)
            self.con(sk, "Symmetric", bottom, 1, twin[4], 2, -2)
            return
        self.dist(sk, (bottom, 1), (bottom, 2), u0, u1, f"{label}largeur")
        self.dist(sk, (right, 1), (right, 2), v0, v1, f"{label}hauteur", "DistanceY")
        if self.mirror(u0, u1):
            self.con(sk, "Symmetric", bottom, 1, bottom, 2, -2)
        else:
            self.con(sk, "Horizontal", bottom)
            i = self._simplest([u0, u1])
            self.anchor(sk, ((bottom, 1), (bottom, 2))[i], (u0, u1)[i], "u", f"{label}position_x")
        if self.mirror(v0, v1):
            self.con(sk, "Symmetric", right, 1, right, 2, -1)
        else:
            self.con(sk, "Vertical", right)
            i = self._simplest([v0, v1])
            self.anchor(sk, ((bottom, 1), (top, 1))[i], (v0, v1)[i], "v", f"{label}position_y")

    def rounded_rect(self, sk, u0, u1, v0, v1, r, label=None):
        """Rectangle with its four corners rounded: width, height, one radius (the
        other arcs equal), placed from the axes."""
        label = self._label(sk, label)
        g = self.outline(sk, [
            ("L", (f"{u0} + {r}", v0), (f"{u1} - {r}", v0)), ("A", (f"{u1} - {r}", f"{v0} + {r}"), r, -90, 0),
            ("L", (u1, f"{v0} + {r}"), (u1, f"{v1} - {r}")), ("A", (f"{u1} - {r}", f"{v1} - {r}"), r, 0, 90),
            ("L", (f"{u1} - {r}", v1), (f"{u0} + {r}", v1)), ("A", (f"{u0} + {r}", f"{v1} - {r}"), r, 90, 180),
            ("L", (u0, f"{v1} - {r}"), (u0, f"{v0} + {r}")), ("A", (f"{u0} + {r}", f"{v0} + {r}"), r, 180, 270)])
        self.con(sk, "Horizontal", g)
        self.con(sk, "Horizontal", g + 4)
        self.con(sk, "Vertical", g + 2)
        self.con(sk, "Vertical", g + 6)
        self.dim(sk, Sketcher.Constraint("Radius", g + 1, self.ev(r)), r, f"{label}rayon")
        for i in (3, 5, 7):
            self.con(sk, "Equal", g + 1, g + i)
        self.dist(sk, (g + 6, 1), (g + 2, 1), u0, u1, f"{label}largeur")
        self.dist(sk, (g, 1), (g + 4, 1), v0, v1, f"{label}hauteur", "DistanceY")
        i = self._simplest([u0, u1])
        self.anchor(sk, ((g + 6, 1), (g + 2, 1))[i], (u0, u1)[i], "u", f"{label}position_x")
        i = self._simplest([v0, v1])
        self.anchor(sk, ((g, 1), (g + 4, 1))[i], (v0, v1)[i], "v", f"{label}position_y")

    def circles(self, sk, pts, d, label=None):
        """Circles of one diameter: the first dimensioned, the others equal to it, and
        symmetric to an earlier one about an axis or the origin when they mirror it."""
        label = self._label(sk, label)
        done = []
        for k, (u, v) in enumerate(pts):
            g = sk.addGeometry(Part.Circle(V(self.ev(u), self.ev(v), 0), V(0, 0, 1), self.ev(d) / 2))
            if done:
                self.con(sk, "Equal", done[0][2], g)
            else:
                self.dim(sk, Sketcher.Constraint("Diameter", g, self.ev(d)), d, f"{label}diametre")
            twin = next(((G, ax) for U, W, G in done for ax, ok in (
                ((-2,), self.mirror(u, U) and self.same(v, W)), ((-1,), self.same(u, U) and self.mirror(v, W)),
                ((-1, 1), self.mirror(u, U) and self.mirror(v, W))) if ok), None)
            if twin:
                self.con(sk, "Symmetric", twin[0], 3, g, 3, *twin[1])
            else:
                s = f"{k + 1}" if len(pts) > 1 else ""
                self.anchor(sk, (g, 3), u, "u", f"{label}position_x{s}")
                self.anchor(sk, (g, 3), v, "v", f"{label}position_y{s}")
            done.append((u, v, g))

    def circle(self, sk, u, v, d, label=None):
        self.circles(sk, [(u, v)], d, label)

    def outline(self, sk, items):
        """Closed outline of lines ("L", a, b) and CCW arcs ("A", centre, r, a0_deg, a1_deg),
        joined in order (tangent next to an arc). Returns the first geometry index;
        the caller adds the dimensions."""
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
        for i in range(len(items)):
            j = (i + 1) % len(items)
            self.con(sk, "Tangent" if "A" in (kinds[i], kinds[j]) else "Coincident", g0 + i, 2, g0 + j, 1)
        return g0

    def slot(self, sk, along, c, w, label=None):
        """Oblong centred on the origin, along u or v: centre distance 2c, width w."""
        label = self._label(sk, label)
        r = f"{w} / 2"
        if along == "u":
            g = self.outline(sk, [("L", (neg(c), neg(r)), (c, neg(r))), ("A", (c, 0), r, -90, 90),
                                  ("L", (c, r), (neg(c), r)), ("A", (neg(c), 0), r, 90, 270)])
            self.con(sk, "Horizontal", g)
        else:
            g = self.outline(sk, [("A", (0, neg(c)), r, 180, 360), ("L", (r, neg(c)), (r, c)),
                                  ("A", (0, c), r, 0, 180), ("L", (neg(r), c), (neg(r), neg(c)))])
            self.con(sk, "Vertical", g + 1)
        a, b = (g + 1, g + 3) if along == "u" else (g, g + 2)
        self.con(sk, "Equal", a, b)
        self.con(sk, "Symmetric", a, 3, b, 3, -1, 1)
        self.dim(sk, Sketcher.Constraint("Diameter", a, self.ev(w)), w, f"{label}largeur")
        ca, cb, kind = (c, neg(c), "DistanceX") if along == "u" else (neg(c), c, "DistanceY")
        self.dist(sk, (a, 3), (b, 3), ca, cb, f"{label}entraxe", kind)

    # PartDesign workflow: named datum planes, sketches on them, pad / pocket /
    # hole by real depths, symmetries and patterns ----------------------------
    def origin(self, body, role):
        return [f for f in body.Origin.OriginFeatures if f.Role == role][0]

    def datum(self, body, label, w):
        """Datum plane parallel to the mating face at depth w."""
        p = body.newObject("PartDesign::Plane", label)
        p.AttachmentSupport = [(self.origin(body, "XY_Plane"), "")]
        p.MapMode = "FlatFace"
        p.AttachmentOffset = App.Placement(V(0, 0, self.ev(w)), App.Rotation())
        p.setExpression(".AttachmentOffset.Base.z", X(w))
        p.Visibility = False
        return p

    def sk(self, body, label, support, draw, off=None):
        """Sketch on an origin plane ("XY", "YZ", "XZ") or a datum plane; off moves
        it along the plane normal (used for XZ, whose normal is -v)."""
        s = body.newObject("Sketcher::SketchObject", "Esq_" + label)
        s.Label = "Esquisse " + label.replace("_", " ")
        s.AttachmentSupport = [(self.origin(body, PLANES[support]) if isinstance(support, str) else support, "")]
        s.MapMode = "FlatFace"
        if off is not None:
            s.AttachmentOffset = App.Placement(V(0, 0, self.ev(off)), App.Rotation())
            s.setExpression(".AttachmentOffset.Base.z", X(off))
        s.Visibility = False
        draw(s)
        return s

    def _feature(self, body, kind, label, s=None):
        f = body.newObject(kind, label)
        f.Label = label.replace("_", " ")
        if s is not None:
            f.Profile = s
        f.Refine = True
        return f

    def pad(self, body, label, s, length, symmetric=False, reverse=False):
        f = self._feature(body, "PartDesign::Pad", label, s)
        f.setExpression("Length", X(length))
        f.SideType = "Symmetric" if symmetric else "One side"
        f.Reversed = reverse
        return f

    def pocket(self, body, label, s, depth=None, symmetric=False, reverse=False):
        """Pocket of a given depth, or through all when depth is None."""
        f = self._feature(body, "PartDesign::Pocket", label, s)
        if depth is None:
            f.Type = "ThroughAll"
        else:
            f.setExpression("Length", X(depth))
        f.SideType = "Symmetric" if symmetric else "One side"
        f.Reversed = reverse
        return f

    def hole(self, body, label, s, d, depth, csk_d=None):
        """Drilled holes at the sketch circles (through all when depth is None), flat
        bottom, optional 90 deg countersink."""
        f = self._feature(body, "PartDesign::Hole", label, s)
        f.Threaded = False
        f.setExpression("Diameter", X(d))
        if depth is None:
            self.doc.recompute()             # ThroughAll checks the base shape when set
            f.DepthType = "ThroughAll"
        else:
            f.DepthType = "Dimension"
            f.setExpression("Depth", X(depth))
        f.DrillPoint = "Flat"
        if csk_d:
            f.HoleCutType = "Countersink"
            f.HoleCutCustomValues = True
            f.setExpression("HoleCutDiameter", X(csk_d))
            f.HoleCutCountersinkAngle = 90
        return f

    def mirrored(self, body, label, feats, plane="YZ_Plane"):
        f = self.doc.addObject("PartDesign::Mirrored", label)
        f.Originals = feats
        f.MirrorPlane = (self.origin(body, plane), [""])
        return self._insert(body, f, label)

    def linear(self, body, label, feats, axis, length, n, reverse=False):
        """n copies spread over length (first to last) along an origin axis."""
        f = self.doc.addObject("PartDesign::LinearPattern", label)
        f.Originals = feats
        f.Direction = (self.origin(body, axis), [""])
        f.Mode = "Extent"
        f.setExpression("Length", X(length))
        f.Occurrences = n
        f.Reversed = reverse
        return self._insert(body, f, label)

    def polar(self, body, label, feats, n, angle=360, axis="Z_Axis"):
        """n copies around an origin axis, spread over angle (360: full turn)."""
        f = self.doc.addObject("PartDesign::PolarPattern", label)
        f.Originals = feats
        f.Axis = (self.origin(body, axis), [""])
        f.Angle = angle
        f.Occurrences = n
        return self._insert(body, f, label)

    def frame(self, body, label, x=0, y=0, z=0, along_u=False):
        """Coordinate system for an assembly joint, placed by expressions on the
        origin: no edge or face reference, so it survives any change of dimension.
        along_u turns its z axis along u (hinge axis, latch travel)."""
        cs = body.newObject("PartDesign::CoordinateSystem", label)
        cs.Label = label.replace("_", " ")
        cs.AttachmentSupport = [(self.origin(body, "XY_Plane"), "")]
        cs.MapMode = "FlatFace"
        rot = App.Rotation(V(0, 1, 0), 90) if along_u else App.Rotation()
        cs.AttachmentOffset = App.Placement(V(self.ev(x), self.ev(y), self.ev(z)), rot)
        for axis, e in (("x", x), ("y", y), ("z", z)):
            if not self.same(e, 0):
                cs.setExpression(f".AttachmentOffset.Base.{axis}", X(e))
        cs.Visibility = False
        return cs

    def _insert(self, body, f, label):
        """Transform features: created outside the body, then added, so that they
        take their place in the chain (body.newObject leaves the tip behind)."""
        f.Label = label.replace("_", " ")
        f.Refine = True
        body.addObject(f)
        return f


# --- Parts -----------------------------------------------------------------
def contour(pd, sk, tab):
    """Outline of the plate and heel (and of the latch tab with its bevelled sides
    for piece 1), corners rounded in the sketch: one radius, the other arcs equal.
    (A Fillet feature loses its edges as soon as a dimension changes, FreeCAD 1.1.)"""
    P, vb, vt, r, H, hv = "plaque_demi_largeur", "plaque_bord_bas", "plaque_bord_haut", "rayon_coins", "talon_bord_droit", "talon_demi_hauteur"
    tc, tu, tv = "languette_demi_largeur_pied", "languette_demi_largeur", "languette_bord_haut"
    if tab:
        top = [("L", (f"{P} - {r}", vt), (tc, vt)), ("L", (tc, vt), (tu, tv)), ("L", (tu, tv), (neg(tu), tv)),
               ("L", (neg(tu), tv), (neg(tc), vt)), ("L", (neg(tc), vt), (f"-{P} + {r}", vt))]
    else:
        top = [("L", (f"{P} - {r}", vt), (f"-{P} + {r}", vt))]
    g0 = pd.outline(sk, [
        ("L", (f"-{P} + {r}", vb), (f"{P} - {r}", vb)),
        ("A", (f"{P} - {r}", f"{vb} + {r}"), r, -90, 0),
        ("L", (P, f"{vb} + {r}"), (P, f"-{hv}")),
        ("L", (P, f"-{hv}"), (f"{H} - {r}", f"-{hv}")),
        ("A", (f"{H} - {r}", f"-{hv} + {r}"), r, -90, 0),
        ("L", (H, f"-{hv} + {r}"), (H, f"{hv} - {r}")),
        ("A", (f"{H} - {r}", f"{hv} - {r}"), r, 0, 90),
        ("L", (f"{H} - {r}", hv), (P, hv)),
        ("L", (P, hv), (P, f"{vt} - {r}")),
        ("A", (f"{P} - {r}", f"{vt} - {r}"), r, 0, 90),
    ] + top + [
        ("A", (f"-{P} + {r}", f"{vt} - {r}"), r, 90, 180),
        ("L", (f"-{P}", f"{vt} - {r}"), (f"-{P}", f"{vb} + {r}")),
        ("A", (f"-{P} + {r}", f"{vb} + {r}"), r, 180, 270),
    ])
    g = lambda i: g0 + i  # noqa: E731
    k = len(top) - 1                                                  # extra lines of the tab
    left, arcs = g(12 + k), (1, 4, 6, 9, 11 + k, 13 + k)
    for i in (3, 7, 10) + ((14,) if tab else ()):
        pd.con(sk, "Horizontal", g(i))
    for i in (g(2), g(5), g(8), left):
        pd.con(sk, "Vertical", i)
    pd.dim(sk, Sketcher.Constraint("Radius", g(1), pd.ev(r)), r, "rayon_coins")
    for i in arcs[1:]:
        pd.con(sk, "Equal", g(1), g(i))
    pd.con(sk, "Symmetric", g(0), 1, g(0), 2, -2)                     # plate centred on the v axis
    pd.dist(sk, (left, 2), (g(2), 1), neg(P), P, "largeur_plaque")
    pd.dist(sk, (g(0), 1), (g(10), 1), vb, vt, "hauteur_plaque", "DistanceY")
    pd.anchor(sk, (g(10), 1), vt, "v", "bord_haut")
    pd.dist(sk, (g(2), 2), (g(5), 1), P, H, "saillie_talon")
    pd.con(sk, "Symmetric", g(3), 1, g(7), 2, -1)                     # heel centred on the u axis
    pd.dist(sk, (g(3), 1), (g(7), 2), f"-{hv}", hv, "hauteur_talon", "DistanceY")
    if tab:
        pd.con(sk, "Symmetric", g(12), 1, g(12), 2, -2)               # tab top centred on the v axis
        pd.con(sk, "Symmetric", g(11), 1, g(13), 2, -2)               # tab foot centred too
        pd.dist(sk, (g(12), 2), (g(12), 1), neg(tu), tu, "largeur_languette")
        pd.dist(sk, (g(11), 1), (g(11), 2), vt, tv, "hauteur_languette", "DistanceY")
        pd.dist(sk, (g(11), 2), (g(11), 1), tu, tc, "pan_languette")


def screw_points():
    """M3 countersunk screws holding piece 2 on piece 1: the corners are left to the magnets."""
    return [("vis_bas_x", "vis_bas_y"), (neg("vis_bas_x"), "vis_bas_y"), ("vis_haut_x", "vis_haut_y"),
            ("vis_haut_droite_x", "vis_haut_y")]


def magnet_points():
    """Two magnets, in the top and bottom bands, towards the right end of the lid."""
    return [("aimant_x", "aimant_y"), ("aimant_x", neg("aimant_y"))]


def pin_points():
    """Stop pins of the lid, at the right end of the two rails."""
    return [("goupille_x", "rail_axe"), ("goupille_x", neg("rail_axe"))]


def rail_profile(pd, s):
    """Dovetail rail of piece 2 seen along u (v, w): a groove for the lid tongue,
    widening at 45 deg below it; drawn above the rear face so that it opens there."""
    a, n, q = "rail_axe", "rail_gorge_largeur / 2", "rail_queue_demi_largeur"
    top, neck = "collerette_face_arriere + 1", "collerette_face_arriere - rail_gorge_hauteur"
    pd.poly(s, [(f"{a} - {n}", top), (f"{a} + {n}", top), (f"{a} + {n}", neck), (f"{a} + {q}", "rail_fond"),
                (f"{a} - {q}", "rail_fond"), (f"{a} - {n}", neck)])


def build_piece1(pd):
    """Interface piece, modelled as by hand: the outline (rounded corners)
    padded; hinge added; then the
    mating face and the rear face machined (pockets, drilled holes), symmetric
    features mirrored and repeated ones patterned."""
    b = pd.body("Piece1_Interface")
    rear = pd.datum(b, "Plan_face_arriere", "piece1_epaisseur")
    floor = pd.datum(b, "Plan_fond_poche_cadre", "peau_epaisseur")
    P, f = "plaque_demi_largeur", "verrou_jeu"
    # the plate
    pd.pad(b, "Plaque", pd.sk(b, "Contour", "XY", lambda s: contour(pd, s, tab=True)), "piece1_epaisseur")
    # mating face (sketches on the XY plane, pockets towards the rear)
    gi, ge = "gorge_cote_interieur / 2", "gorge_cote_interieur / 2 + gorge_largeur"
    pd.pocket(b, "Gorge_levre_boitier", pd.sk(b, "Gorge_levre_boitier", "XY", lambda s: (
        pd.rect(s, neg(ge), ge, neg(ge), ge, "exterieur"), pd.rect(s, neg(gi), gi, neg(gi), gi, "interieur"))),
        "gorge_profondeur", reverse=True)
    gi, ge = "gorge_interieure_cote_interieur / 2", "gorge_interieure_cote_interieur / 2 + gorge_interieure_largeur"
    pd.pocket(b, "Gorge_levre_interieure", pd.sk(b, "Gorge_levre_interieure", "XY", lambda s: (
        pd.rect(s, neg(ge), ge, neg(ge), ge, "exterieur"), pd.rect(s, neg(gi), gi, neg(gi), gi, "interieur"))),
        "gorge_interieure_profondeur", reverse=True)
    pd.pocket(b, "Poches_ergots", pd.sk(b, "Poches_ergots", "XY", lambda s: (
        pd.rect(s, "ergot1_gauche", "ergot1_droite", "ergot1_bas", "ergot1_haut", "ergot_haut"),
        pd.rect(s, "ergot2_gauche", "ergot2_droite", "ergot2_bas", "ergot2_haut", "ergot_bas"))),
        "ergots_profondeur", reverse=True)
    win = pd.pocket(b, "Fenetre_griffe", pd.sk(b, "Fenetre_griffe", "XY", lambda s: pd.rect(
        s, "fenetre_griffe_gauche", "fenetre_griffe_droite", "fenetre_griffe_bas", "fenetre_griffe_haut")), "verrou_paroi", reverse=True)
    pd.mirrored(b, "Fenetres_griffes_symetrie", [win])
    pd.pocket(b, "Ouverture_image", pd.sk(b, "Ouverture_image", "XY", lambda s: pd.rect(
        s, "-peau_ouverture / 2", "peau_ouverture / 2", "-peau_ouverture / 2", "peau_ouverture / 2")), reverse=True)
    # rear face (sketches on the rear plane, pockets towards the mating face)
    pd.pocket(b, "Poche_cadre", pd.sk(b, "Poche_cadre", rear, lambda s: pd.rect(
        s, f"-{P} - 1", "poche_cadre_droite", neg("poche_cadre_demi_hauteur"), "poche_cadre_demi_hauteur")), "piece1_epaisseur - peau_epaisseur")
    pd.pocket(b, "Poche_capot", pd.sk(b, "Poche_capot", rear, lambda s: pd.rect(
        s, f"capot_gauche - {f}", f"capot_droite + {f}", f"verrou_poche_bas - {f}", f"verrou_poche_haut + {f}")), "piece1_epaisseur - verrou_poche_fond")
    pd.pocket(b, "Poche_glissiere", pd.sk(b, "Poche_glissiere", rear, lambda s: pd.poly(s, [
        (f"verrou_poche_gauche - {f}", f"verrou_poche_bas - {f}"), (f"verrou_ilot_gauche + {f}", f"verrou_poche_bas - {f}"),
        (f"verrou_ilot_gauche + {f}", f"verrou_ilot_haut - {f}"), (f"verrou_ilot_droite - {f}", f"verrou_ilot_haut - {f}"),
        (f"verrou_ilot_droite - {f}", f"verrou_poche_bas - {f}"), (f"verrou_poche_droite + {f}", f"verrou_poche_bas - {f}"),
        (f"verrou_poche_droite + {f}", f"verrou_poche_haut + {f}"), (f"verrou_poche_gauche - {f}", f"verrou_poche_haut + {f}")])), "piece1_epaisseur - verrou_paroi")
    pd.pocket(b, "Passage_languette", pd.sk(b, "Passage_languette", rear, lambda s: pd.rect(
        s, f"passage_languette_gauche - {f}", f"passage_languette_droite + {f}", "verrou_poche_haut - 0.3", "languette_bord_haut + 1.2")), "piece1_epaisseur - verrou_paroi")
    hook = pd.pocket(b, "Encoche_crochet", pd.sk(b, "Encoche_crochet", rear, lambda s: pd.rect(
        s, "encoche_crochet_gauche", "encoche_crochet_droite", "plaque_bord_bas - 1", "plaque_bord_bas + encoche_crochet_hauteur")), "piece1_epaisseur - encoche_crochet_levre")
    pd.mirrored(b, "Encoches_crochets_symetrie", [hook])
    tw = ("chicane_axe + chicane_gorge_largeur / 2", "chicane_axe - chicane_gorge_largeur / 2")
    pd.pocket(b, "Gorge_chicane_collerette", pd.sk(b, "Gorge_chicane_collerette", rear, lambda s: pd.poly(s, [
        ("chicane_bout_gauche", tw[0]), (tw[0], tw[0]), (tw[0], neg(tw[0])), ("chicane_bout_gauche", neg(tw[0])),
        ("chicane_bout_gauche", neg(tw[1])), (tw[1], neg(tw[1])), (tw[1], tw[1]), ("chicane_bout_gauche", tw[1])])), "chicane_gorge_profondeur")
    pd.hole(b, "Avant_trous_vis", pd.sk(b, "Avant_trous_vis", rear, lambda s: pd.circles(
        s, screw_points(), "avant_trou_diametre")), "avant_trou_diametre", "avant_trou_profondeur")
    pd.pocket(b, "Trous_goupilles", pd.sk(b, "Trous_goupilles", rear, lambda s: pd.circles(
        s, pin_points(), "goupille_trou_diametre")), "goupille_enfoncement")
    # floor of the frame pocket (dark slide side)
    pd.pocket(b, "Gorge_velours", pd.sk(b, "Gorge_velours", floor, lambda s: pd.rect(
        s, "velours_gauche", "velours_droite", neg("fente_demi_hauteur"), "fente_demi_hauteur")), "velours_profondeur")
    rw = ("chicane_rails_axe + chicane_rails_gorge_largeur / 2", "chicane_rails_axe - chicane_rails_gorge_largeur / 2")
    ru = ("chicane_rails_axe_droit + chicane_rails_gorge_largeur / 2", "chicane_rails_axe_droit - chicane_rails_gorge_largeur / 2")
    pd.pocket(b, "Gorge_chicane_rails", pd.sk(b, "Gorge_chicane_rails", floor, lambda s: pd.poly(s, [
        (f"-{P} - 1", rw[0]), (ru[0], rw[0]), (ru[0], neg(rw[0])), (f"-{P} - 1", neg(rw[0])),
        (f"-{P} - 1", neg(rw[1])), (ru[1], neg(rw[1])), (ru[1], rw[1]), (f"-{P} - 1", rw[1])])), "chicane_rails_gorge_profondeur")
    return b


def build_piece2(pd):
    """Glass frame: the flange (outline) padded on the rear face of piece 1, the
    insert and the dark slide rails padded forwards; then the glass seat, the
    grooves, the clearances and the countersunk screw holes."""
    b = pd.body("Piece2_CadreVerre")
    p1 = pd.datum(b, "Plan_face_arriere_piece1", "piece1_epaisseur")
    skin = pd.datum(b, "Plan_avant_rails", "peau_epaisseur")
    ledge = pd.datum(b, "Plan_avant_insert", "butee_face_avant")
    rear = pd.datum(b, "Plan_face_arriere", "collerette_face_arriere")
    P, ui1, vi, sh = "plaque_demi_largeur", "poche_cadre_droite - cadre_jeu", "poche_cadre_demi_hauteur - cadre_jeu", "fente_demi_hauteur"
    pd.pad(b, "Collerette", pd.sk(b, "Collerette", p1, lambda s: contour(pd, s, tab=False)), "collerette_epaisseur")
    pd.pad(b, "Insert", pd.sk(b, "Insert", p1, lambda s: pd.rect(s, neg(P), ui1, neg(vi), vi)),
           "piece1_epaisseur - butee_face_avant", reverse=True)
    pd.pad(b, "Rails_volet", pd.sk(b, "Rails_volet", skin, lambda s: pd.poly(s, [
        (neg(P), neg(vi)), (ui1, neg(vi)), (ui1, vi), (neg(P), vi), (neg(P), sh),
        ("fente_fond", sh), ("fente_fond", neg(sh)), (neg(P), neg(sh))])), "fente_epaisseur")
    tw = ("chicane_axe + chicane_nervure_largeur / 2", "chicane_axe - chicane_nervure_largeur / 2")
    pd.pad(b, "Nervure_chicane_collerette", pd.sk(b, "Nervure_chicane_collerette", p1, lambda s: pd.poly(s, [
        ("chicane_bout_gauche", tw[0]), (tw[0], tw[0]), (tw[0], neg(tw[0])), ("chicane_bout_gauche", neg(tw[0])),
        ("chicane_bout_gauche", neg(tw[1])), (tw[1], neg(tw[1])), (tw[1], tw[1]), ("chicane_bout_gauche", tw[1])])),
        "chicane_nervure_hauteur", reverse=True)
    rw = ("chicane_rails_axe + chicane_rails_nervure_largeur / 2", "chicane_rails_axe - chicane_rails_nervure_largeur / 2")
    ru = ("chicane_rails_axe_droit + chicane_rails_nervure_largeur / 2", "chicane_rails_axe_droit - chicane_rails_nervure_largeur / 2")
    pd.pad(b, "Nervure_chicane_rails", pd.sk(b, "Nervure_chicane_rails", skin, lambda s: pd.poly(s, [
        (neg(P), rw[0]), (ru[0], rw[0]), (ru[0], neg(rw[0])), (neg(P), neg(rw[0])),
        (neg(P), neg(rw[1])), (ru[1], neg(rw[1])), (ru[1], rw[1]), (neg(P), rw[1])])),
        "chicane_rails_nervure_hauteur", reverse=True)
    g = "verre_cote / 2 + verre_jeu"
    pd.pocket(b, "Ouverture_butee", pd.sk(b, "Ouverture_butee", "XY", lambda s: pd.rect(
        s, "-butee_ouverture / 2", "butee_ouverture / 2", "-butee_ouverture / 2", "butee_ouverture / 2")), reverse=True)
    pd.pocket(b, "Logement_verre", pd.sk(b, "Logement_verre", rear, lambda s: pd.rect(s, neg(g), g, neg(g), g)),
              "collerette_face_arriere - plan_film")
    pd.pocket(b, "Gorge_velours", pd.sk(b, "Gorge_velours", ledge, lambda s: pd.rect(
        s, "velours_gauche", "velours_droite", neg(sh), sh)), "velours_profondeur", reverse=True)
    # sliding lid: the channel of its sole (closed on the left, open on the right), the
    # slot of its left tongue, the two dovetail rails and the holes of the stop pins
    pd.pocket(b, "Couloir_couvercle", pd.sk(b, "Couloir_couvercle", rear, lambda s: pd.rect(
        s, "couloir_gauche", "talon_bord_droit + 1", neg("couloir_demi_hauteur"), "couloir_demi_hauteur")),
        "collerette_face_arriere - couloir_fond")
    t0, t1 = "languette_gauche_bas - couvercle_jeu", "languette_gauche_bas + languette_gauche_epaisseur + couvercle_jeu"
    pd.pocket(b, "Fente_languette", pd.sk(b, "Fente_languette", "YZ", lambda s: pd.rect(
        s, "-couloir_demi_hauteur + 1", "couloir_demi_hauteur - 1", t0, t1), off="couloir_gauche"), "fente_couvercle_profondeur")
    rail = pd.pocket(b, "Rail_haut", pd.sk(b, "Rail_haut", "YZ", lambda s: rail_profile(pd, s), off="talon_bord_droit + 1"),
                     "talon_bord_droit + 1 - rail_gauche")
    pd.mirrored(b, "Rails_symetrie", [rail], "XZ_Plane")
    # light trap of the left edge: a lip from rail to rail (the rails run up to it), capped by a
    # rebate under the left edge of the lid
    pd.pad(b, "Levre_gauche", pd.sk(b, "Levre_gauche", rear, lambda s: pd.rect(
        s, neg(P), f"-{P} + levre_gauche_largeur", "-rail_axe - rail_queue_demi_largeur", "rail_axe + rail_queue_demi_largeur")),
        "levre_gauche_hauteur")
    pins = pd.datum(b, "Plan_fond_rails", "rail_fond")
    pd.pocket(b, "Trous_goupilles", pd.sk(b, "Trous_goupilles", pins, lambda s: pd.circles(
        s, pin_points(), "goupille_trou_diametre")), "rail_fond - piece1_epaisseur")
    # magnets embedded under a skin on the joint side (printed rear face down: pause to drop them in)
    under_skin = pd.datum(b, "Plan_peau_aimants", "collerette_face_arriere - aimant_peau")
    pd.pocket(b, "Logements_aimants", pd.sk(b, "Logements_aimants", under_skin, lambda s: pd.circles(
        s, magnet_points(), "aimant_diametre + aimant_jeu")), "aimant_epaisseur + aimant_jeu")
    cr = "griffes_degagement"
    claw = pd.pocket(b, "Degagement_griffe", pd.sk(b, "Degagement_griffe", rear, lambda s: pd.rect(
        s, f"fenetre_griffe_gauche - {cr}", f"fenetre_griffe_droite + {cr}", f"fenetre_griffe_bas - {cr}",
        f"fenetre_griffe_haut + {cr}")))
    pd.mirrored(b, "Degagements_griffes_symetrie", [claw])
    pd.hole(b, "Trous_vis_fraises", pd.sk(b, "Trous_vis_fraises", rear, lambda s: pd.circles(
        s, screw_points(), "vis_passage_diametre")), "vis_passage_diametre", None, csk_d="vis_fraisure_diametre")
    return b


def build_piece3(pd):
    """Solid lid sliding to the right, in line with the pieces: the outline of
    piece 2 raised from its rear face, as much material as possible against the
    translucency of PETG. Underneath: the sole that slides in the channel of
    piece 2 over the glass, with a tongue at its left end that enters the slot of
    the channel wall; the tongue and the dovetail heads of the two rails; the
    chamber of the leaf spring and the pocket of its root; the magnet seats. At
    the right end, a lip down the face of the heel: closing stop and light trap."""
    b = pd.body("Piece3_Couvercle")
    seat = pd.datum(b, "Plan_appui_piece2", "collerette_face_arriere")
    sole = pd.datum(b, "Plan_dessous_semelle", "semelle_dessous")
    lip = pd.datum(b, "Plan_bas_levre", "levre_bas")
    j = "couvercle_jeu"
    pd.pad(b, "Couvercle", pd.sk(b, "Contour", seat, lambda s: contour(pd, s, tab=False)), "couvercle_hauteur")
    pd.pad(b, "Semelle", pd.sk(b, "Semelle", seat, lambda s: pd.rect(
        s, f"couloir_gauche + {j}", "talon_bord_droit", f"-couloir_demi_hauteur + {j}", f"couloir_demi_hauteur - {j}")),
        "collerette_face_arriere - semelle_dessous", reverse=True)
    pd.pad(b, "Languette_gauche", pd.sk(b, "Languette_gauche", "YZ", lambda s: pd.rect(
        s, f"-couloir_demi_hauteur + 1 + {j}", f"couloir_demi_hauteur - 1 - {j}", "languette_gauche_bas",
        "languette_gauche_bas + languette_gauche_epaisseur"), off=f"couloir_gauche + {j}"),
        "languette_gauche_longueur", reverse=True)
    pd.pad(b, "Levre_droite", pd.sk(b, "Levre_droite", lip, lambda s: pd.rect(
        s, "talon_bord_droit", "talon_bord_droit + levre_epaisseur", "-talon_demi_hauteur + rayon_coins",
        "talon_demi_hauteur - rayon_coins")), "couvercle_face_exterieure - levre_bas")
    pd.pocket(b, "Feuillure_gauche", pd.sk(b, "Feuillure_gauche", seat, lambda s: pd.rect(
        s, "-plaque_demi_largeur - 1", f"-plaque_demi_largeur + levre_gauche_largeur + {j}",
        f"-rail_axe - rail_queue_demi_largeur - {j}", f"rail_axe + rail_queue_demi_largeur + {j}")),
        f"levre_gauche_hauteur + {j}", reverse=True)
    # rails: a tongue all along (light trap in the groove), the dovetail heads at the left end only
    a, lw, tw, top = "rail_axe", "languette_rail_demi_largeur", "tete_demi_largeur", "collerette_face_arriere"
    start = f"rail_gauche + {j}"
    rail = [
        pd.pad(b, "Languette_rail", pd.sk(b, "Languette_rail", "YZ", lambda s: pd.rect(
            s, f"{a} - {lw}", f"{a} + {lw}", "languette_rail_bas", top), off=start), f"talon_bord_droit - ({start})"),
        pd.pad(b, "Queue_aronde", pd.sk(b, "Queue_aronde", "YZ", lambda s: pd.poly(s, [
            (f"{a} - {lw}", top), (f"{a} + {lw}", top), (f"{a} + {lw}", "tete_epaule"), (f"{a} + {tw}", "tete_bas"),
            (f"{a} - {tw}", "tete_bas"), (f"{a} - {lw}", "tete_epaule")]), off=start), "tete_longueur"),
    ]
    pd.mirrored(b, "Rails_symetrie", rail, "XZ_Plane")
    # leaf spring: its root glued in a pocket, the leaves free to lift into a chamber
    w = "lames_axe + lames_largeur / 2"
    pd.pocket(b, "Logement_racine_lames", pd.sk(b, "Logement_racine_lames", sole, lambda s: pd.rect(
        s, "lames_racine_droite - lames_racine_largeur - 0.1", "lames_racine_droite", f"-({w}) - 0.1", f"{w} + 0.1")),
        "lames_epaisseur", reverse=True)
    pd.pocket(b, "Chambre_lames", pd.sk(b, "Chambre_lames", sole, lambda s: pd.rect(
        s, "lames_racine_droite", "patin_x + patin_hauteur + patin_largeur_bas / 2 + 0.5", f"-({w}) - 0.5", f"{w} + 0.5")),
        "chambre_lames_haut - semelle_dessous", reverse=True)
    # closure: magnets embedded towards the right end, facing those of piece 2
    # through two skins (printed outer face down: pause to drop them in)
    above_skin = pd.datum(b, "Plan_peau_aimants", "collerette_face_arriere + aimant_peau")
    pd.pocket(b, "Logements_aimants", pd.sk(b, "Logements_aimants", above_skin, lambda s: pd.circles(
        s, magnet_points(), "aimant_diametre + aimant_jeu")), "aimant_epaisseur + aimant_jeu", reverse=True)
    return b


def build_leaf_spring(pd):
    """Leaf spring, printed flat (pads up), its root bar glued under the lid sole:
    two leaves along u, each ending in a pad chamfered at 45 deg on both sides, so
    that it climbs the steps (edge of the glass seat, entrance of the channel)
    whichever way the lid slides. Drawn free: the pads go into the thinnest glass
    by the preload."""
    b = pd.body("Ressort_Lames")
    sole = pd.datum(b, "Plan_dessous_semelle", "semelle_dessous")
    w, h = "lames_axe + lames_largeur / 2", "patin_hauteur + patin_largeur_bas / 2"
    pd.pad(b, "Racine", pd.sk(b, "Racine", sole, lambda s: pd.rect(
        s, "lames_racine_droite - lames_racine_largeur", "lames_racine_droite", neg(w), w)), "lames_epaisseur")
    leaf = [
        pd.pad(b, "Lame", pd.sk(b, "Lame", sole, lambda s: pd.rect(
            s, "lames_racine_droite", f"patin_x + {h}", "lames_axe - lames_largeur / 2", w)), "lames_epaisseur"),
        pd.pad(b, "Patin", pd.sk(b, "Patin", "XZ", lambda s: pd.poly(s, [
            ("patin_x - patin_largeur_bas / 2", "patin_bas"), ("patin_x + patin_largeur_bas / 2", "patin_bas"),
            (f"patin_x + {h}", "semelle_dessous"), (f"patin_x - ({h})", "semelle_dessous")]), off=neg("lames_axe")),
            "lames_largeur", symmetric=True),
    ]
    pd.mirrored(b, "Lames_symetrie", leaf, "XZ_Plane")
    return b


def build_slider(pd):
    """Rayfor latch slider, remodelled from its STL (rest position)."""
    b = pd.body("Glissiere_Verrou")
    front = pd.datum(b, "Plan_avant_glissiere", "verrou_paroi")
    back = pd.datum(b, "Plan_arriere_glissiere", "verrou_paroi + glissiere_epaisseur")
    pd.pad(b, "Glissiere", pd.sk(b, "Glissiere", front, lambda s: pd.poly(s, [
        ("verrou_poche_droite", "verrou_poche_haut"), ("glissiere_languette_droite", "verrou_poche_haut"),
        ("glissiere_languette_droite", "glissiere_languette_haut"), ("glissiere_languette_gauche", "glissiere_languette_haut"),
        ("glissiere_languette_gauche", "verrou_poche_haut"), ("glissiere_gauche", "verrou_poche_haut"),
        ("glissiere_gauche", "glissiere_barre_bas"), ("glissiere_dent_gauche_pied", "glissiere_barre_bas"),
        ("glissiere_dent_gauche_pied", "glissiere_guide_bas"), ("glissiere_guide_droite", "glissiere_guide_bas"),
        ("glissiere_guide_droite", "glissiere_barre_bas"), ("verrou_poche_droite", "glissiere_barre_bas")])),
        "glissiere_epaisseur")
    # teeth: their back is the locking ramp the body claws ride on (thin at the tip, full at the root)
    s0, slope = "verrou_paroi", "(glissiere_epaisseur - glissiere_rampe_epaisseur_bout) / glissiere_rampe_longueur"
    tooth = "glissiere_barre_bas - verrou_poche_bas"
    pd.pad(b, "Dent_rampe_droite", pd.sk(b, "Dent_rampe_droite", "XZ", lambda s: pd.poly(s, [
        ("glissiere_dent_droite_bout", s0), ("verrou_poche_droite", s0), ("verrou_poche_droite", f"{s0} + glissiere_epaisseur"),
        ("glissiere_dent_droite_bout + glissiere_rampe_longueur", f"{s0} + glissiere_epaisseur"),
        ("glissiere_dent_droite_bout", f"{s0} + glissiere_rampe_epaisseur_bout")]), off=neg("glissiere_barre_bas")), tooth)
    pd.pad(b, "Dent_rampe_gauche", pd.sk(b, "Dent_rampe_gauche", "XZ", lambda s: pd.poly(s, [
        ("glissiere_dent_gauche_bout", s0), ("glissiere_dent_gauche_pied", s0),
        ("glissiere_dent_gauche_pied",
         f"{s0} + glissiere_rampe_epaisseur_bout + (glissiere_dent_gauche_pied - glissiere_dent_gauche_bout) * {slope}"),
        ("glissiere_dent_gauche_bout", f"{s0} + glissiere_rampe_epaisseur_bout")]), off=neg("glissiere_barre_bas")), tooth)
    pd.pad(b, "Prise", pd.sk(b, "Prise", back, lambda s: pd.rect(
        s, "glissiere_languette_gauche", "glissiere_languette_droite", "glissiere_prise_bas", "glissiere_languette_haut")),
        "glissiere_prise_surepaisseur")
    f, top = "(moletage_dent_pied - moletage_dent_sommet) / 2", "glissiere_languette_haut"
    knurl = pd.pad(b, "Dent_moletage", pd.sk(b, "Dent_moletage", front, lambda s: pd.poly(s, [
        ("moletage_debut", top), ("moletage_debut + moletage_dent_pied", top),
        (f"moletage_debut + moletage_dent_pied - {f}", f"{top} + moletage_hauteur"),
        (f"moletage_debut + {f}", f"{top} + moletage_hauteur")])), "glissiere_epaisseur + glissiere_prise_surepaisseur")
    pd.linear(b, "Moletage", [knurl], "X_Axis", "8 * moletage_pas", 9)
    return b


def build_cover(pd):
    """Rayfor latch cover, remodelled; flush with the rear face of piece 1."""
    b = pd.body("Capot_Verrou")
    rear = pd.datum(b, "Plan_face_arriere", "piece1_epaisseur")
    pd.pad(b, "Capot", pd.sk(b, "Capot", rear, lambda s: pd.poly(s, [
        ("capot_gauche", "verrou_poche_bas"), ("capot_droite", "verrou_poche_bas"), ("capot_droite", "verrou_poche_haut"),
        ("passage_languette_droite", "verrou_poche_haut"), ("passage_languette_droite", "languette_bord_haut"),
        ("passage_languette_gauche", "languette_bord_haut"), ("passage_languette_gauche", "verrou_poche_haut"),
        ("capot_gauche", "verrou_poche_haut")])), "capot_epaisseur", reverse=True)
    win = pd.pocket(b, "Fenetre_griffe", pd.sk(b, "Fenetre_griffe", rear, lambda s: pd.rect(
        s, "fenetre_griffe_gauche", "fenetre_griffe_droite", "fenetre_griffe_bas", "fenetre_griffe_haut")))
    pd.mirrored(b, "Fenetres_griffes_symetrie", [win])
    return b


def ref_box(doc, name, u0, u1, v0, v1, w0, w1):
    o = doc.addObject("Part::Box", name)
    o.setExpression("Length", f"({X(u1)}) - ({X(u0)})")
    o.setExpression("Width", f"({X(v1)}) - ({X(v0)})")
    o.setExpression("Height", f"({X(w1)}) - ({X(w0)})")
    for axis, e in (("x", u0), ("y", v0), ("z", w0)):
        o.setExpression(f".Placement.Base.{axis}", X(e))
    return o


def ref_latch_spring(doc):
    """Latch spring as a plain cylinder along u, from the left tooth of the
    slider to the island, latch open (shortest)."""
    o = doc.addObject("Part::Cylinder", "Ressort_verrou")
    o.Label = "Ressort verrou"
    o.Placement = App.Placement(V(), App.Rotation(V(0, 1, 0), 90))
    o.setExpression("Radius", X("ressort_verrou_diametre / 2"))
    o.setExpression("Height", X("ressort_verrou_longueur_ouvert"))
    for axis, e in (("x", "glissiere_dent_gauche_pied"), ("y", "ressort_verrou_y"),
                    ("z", "ressort_verrou_z")):
        o.setExpression(f".Placement.Base.{axis}", X(e))
    return o


def build(doc):
    # same feature names in several bodies (Contour, Trou axe...): keep the labels as written
    App.ParamGet("User parameter:BaseApp/Preferences/Document").SetBool("DuplicateLabels", True)
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
              "piece3_couvercle": build_piece3(pd), "ressort_lames": build_leaf_spring(pd),
              "glissiere_verrou": build_slider(pd), "capot_verrou": build_cover(pd)}
    refs = {
        "Verre_57x57": ref_box(doc, "Verre_57x57", "-verre_cote / 2", "verre_cote / 2", "-verre_cote / 2", "verre_cote / 2",
                               "plan_film", "verre_face_arriere"),
        "Volet": ref_box(doc, "Volet", "-plaque_demi_largeur - 15", "fente_fond - 0.4", "-volet_largeur / 2", "volet_largeur / 2",
                         "peau_epaisseur + (fente_epaisseur - volet_epaisseur) / 2", "peau_epaisseur + (fente_epaisseur + volet_epaisseur) / 2"),
        "Ressort_verrou": ref_latch_spring(doc),
    }
    for (x, y), side in zip(pin_points(), ("haut", "bas")):
        o = doc.addObject("Part::Cylinder", f"Goupille_{side}")
        o.Label = f"Goupille butee {side}"
        o.setExpression("Radius", X("goupille_diametre / 2"))
        o.setExpression("Height", X("goupille_longueur"))
        for axis, e in (("x", x), ("y", y), ("z", "piece1_epaisseur - goupille_enfoncement")):
            o.setExpression(f".Placement.Base.{axis}", X(e))
        refs[o.Name] = o
    doc.recompute()
    asm, magnets = assemble(doc, pd, pieces)
    return pieces, refs, asm, magnets


def assemble(doc, pd, pieces):
    """FreeCAD assembly: piece 1 grounded, piece 2 and the latch cover fixed on it,
    the lid on a slider joint along u (its travel, couvercle_course), the leaf
    spring fixed to the lid, the latch slider on a slider joint (its travel), and
    the magnets fixed in their seats. Joints use coordinate systems placed by
    expressions, never edges or faces, so they survive any change of dimension."""
    asm = doc.addObject("Assembly::AssemblyObject", "Cassette")
    for body in pieces.values():
        asm.addObject(body)
    joints = asm.newObject("Assembly::JointGroup", "Liaisons")
    p1, p2, p3 = pieces["piece1_interface"], pieces["piece2_cadre_verre"], pieces["piece3_couvercle"]
    spring, slider, cover = pieces["ressort_lames"], pieces["glissiere_verrou"], pieces["capot_verrou"]
    origin = {b.Name: pd.frame(b, "Repere_origine") for b in (p1, p2, p3, spring, cover)}
    sliding = [pd.frame(b, "Repere_glissiere_couvercle", along_u=True) for b in (p1, p3)]
    latch = [pd.frame(b, "Repere_verrou", along_u=True) for b in (p1, slider)]
    seats = {}
    for b, z in ((p2, "collerette_face_arriere - aimant_peau - aimant_epaisseur"),
                 (p3, "collerette_face_arriere + aimant_peau + aimant_jeu")):
        for side, (x, y) in zip(("haut", "bas"), magnet_points()):
            seats[(b.Name, side)] = pd.frame(b, f"Repere_aimant_{side}", x, y, z)
    magnets = {}
    for b, where in ((p2, "piece2"), (p3, "couvercle")):
        for side in ("haut", "bas"):
            m = asm.newObject("Part::Cylinder", f"Aimant_{where}_{side}")
            m.Label = f"Aimant {where} {side}"
            m.setExpression("Radius", X("aimant_diametre / 2"))
            m.setExpression("Height", X("aimant_epaisseur"))
            magnets[m.Name] = (m, b, seats[(b.Name, side)])
    doc.recompute()

    def joint(label, kind, a, fa, b, fb):
        j = joints.newObject("App::FeaturePython", label)
        JointObject.Joint(j, JointObject.JointTypes.index(kind))
        j.Label = label.replace("_", " ")
        refb = [b, ["", ""]] if fb is None else [b, [f"{fb.Name}.", f"{fb.Name}."]]
        j.Proxy.setJointConnectors(j, [[a, [f"{fa.Name}.", f"{fa.Name}."]], refb])
        return j

    ground = joints.newObject("App::FeaturePython", "Piece1_fixe")
    JointObject.GroundedJoint(ground, p1)
    ground.Label = "Piece 1 fixe"
    joint("Piece2_vissee", "Fixed", p1, origin[p1.Name], p2, origin[p2.Name])
    joint("Capot_verrou", "Fixed", p1, origin[p1.Name], cover, origin[cover.Name])
    h = joint("Glissiere_couvercle", "Slider", p1, sliding[0], p3, sliding[1])
    h.EnableLengthMin, h.LengthMin, h.EnableLengthMax = True, 0, True
    h.setExpression("LengthMax", X("couvercle_course"))
    joint("Ressort_colle", "Fixed", p3, origin[p3.Name], spring, origin[spring.Name])
    sl = joint("Glissiere_verrou", "Slider", p1, latch[0], slider, latch[1])
    sl.EnableLengthMin, sl.EnableLengthMax, sl.LengthMax = True, True, 0
    sl.setExpression("LengthMin", X("-glissiere_course"))
    for m, b, seat in magnets.values():
        joint(f"{m.Name}_colle", "Fixed", b, seat, m, None)
    doc.recompute()
    asm.solve()
    add_simulations(doc, asm)
    return asm, {k: v[0] for k, v in magnets.items()}


def simulation_module():
    """FreeCAD's simulation module derives a Qt class at import, which fails
    without a GUI: load it with Qt supplied (its Simulation and Motion classes
    keep their module name, so the GUI finds them in the saved file)."""
    if App.GuiUp or "CommandCreateSimulation" in sys.modules:
        import CommandCreateSimulation
        return CommandCreateSimulation
    import types
    from PySide import QtCore, QtGui, QtWidgets
    src = os.path.join(os.path.dirname(JointObject.__file__), "CommandCreateSimulation.py")
    mod = types.ModuleType("CommandCreateSimulation")
    mod.__file__ = src
    mod.__dict__.update(QtCore=QtCore, QtGui=QtGui, QtWidgets=QtWidgets)
    sys.modules["CommandCreateSimulation"] = mod
    exec(compile(open(src).read(), src, "exec"), mod.__dict__)
    return mod


def add_simulations(doc, asm):
    """Two ready-made animations of the assembly (Assembly > Simulation): the lid
    opening to its stop and closing, the latch locking and unlocking. The
    formulas are the solver's own (radians, mm, time in s), set from the table."""
    sim_mod, vals = simulation_module(), param_values()
    group = asm.newObject("Assembly::SimulationGroup", "Simulations")
    joint = {o.Label: o for o in doc.getObject("Liaisons").Group}
    sims = []
    for name, label, kind, jlabel, amplitude in (
            ("Ouverture_couvercle", "Ouvrir et fermer le couvercle", "Linear", "Glissiere couvercle",
             vals["couvercle_course"]),
            ("Verrouillage", "Verrouiller et deverrouiller", "Linear", "Glissiere verrou",
             -vals["glissiere_course"])):
        sim = group.newObject("App::FeaturePython", name)
        sim_mod.Simulation(sim)
        sim.Label, sim.bTimeEnd = label, 4.0
        motion = asm.newObject("App::FeaturePython", "Mouvement_" + name)
        sim_mod.Motion(motion, kind, joint[jlabel], f"{amplitude / 2:.6g}*(1 - cos(pi*time/2))")
        motion.Label = f"{jlabel} : aller-retour en 4 s"
        sim.Group = sim.Group + [motion]
        sims.append(sim)
    doc.recompute()
    return sims


COLORS = {
    "piece1_interface": (0.15, 0.15, 0.17), "piece2_cadre_verre": (0.35, 0.35, 0.38),
    "piece3_couvercle": (0.22, 0.24, 0.30), "ressort_lames": (0.80, 0.45, 0.10),
    "Goupille_haut": (0.72, 0.72, 0.74), "Goupille_bas": (0.72, 0.72, 0.74),
    "Verre_57x57": (0.60, 0.80, 0.90), "Volet": (0.78, 0.79, 0.80), "Ressort_verrou": (0.72, 0.72, 0.74),
    "glissiere_verrou": (0.75, 0.20, 0.20), "capot_verrou": (0.75, 0.40, 0.40),
    "Rayfor_glissiere": (0.75, 0.20, 0.20), "Rayfor_capot": (0.75, 0.40, 0.40),
    "Aimant": (0.72, 0.72, 0.74),
}


def rayfor_part(name):
    """Rayfor latch parts moved into our frame: u = 49 - x, v = 92.08 - z, w = 16.22 - y."""
    path = os.path.join(ROOT, "sources", "hasselblad-v-mount-for-imacon-digital-back-model_files", name)
    m = Mesh.Mesh(path)
    m.transform(App.Matrix(-1, 0, 0, 49.0, 0, 0, -1, 92.08, 0, -1, 0, 16.22, 0, 0, 0, 1))
    s = Part.Shape()
    s.makeShapeFromMesh(m.Topology, 0.05)
    return Part.Solid(Part.Shell(s.Faces))


def finish(doc, pieces, refs, magnets):
    """Containers, visibility (bodies show their tip only), colour map for the GUI file."""
    ref = doc.addObject("App::Part", "References")
    colors = {m.Name: (COLORS["Aimant"], 0) for m in magnets.values()}
    for key, body in pieces.items():
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
    """GuiDocument.xml written without a GUI: visibility, colours, joint view providers.

    FreeCAD hides every object of a file whose GuiDocument.xml lacks
    HasExpansion="1" + <Expand />, and stops reading at a missing <Camera>."""
    cam = ("OrthographicCamera {&#10;  viewportMapping ADJUST_CAMERA&#10;  position 160 -160 140&#10;"
           "  orientation -0.74 -0.31 -0.6 1.15&#10;  nearDistance 1&#10;  farDistance 1000&#10;"
           "  aspectRatio 1&#10;  focalDistance 260&#10;  height 160&#10;&#10;}&#10;")
    vps, files = [], {}
    for o in doc.Objects:
        props = [("Visibility", "App::PropertyBool", f'<Bool value="{"true" if o.Visibility else "false"}"/>')]
        proxy = type(getattr(o, "Proxy", None)).__name__
        module = {"Joint": "JointObject", "GroundedJoint": "JointObject",
                  "Simulation": "CommandCreateSimulation", "Motion": "CommandCreateSimulation"}.get(proxy)
        if module:                                         # joint markers, icons, simulation panel in the GUI
            props.append(("Proxy", "App::PropertyPythonObject",
                          f'<Python value="bnVsbA==" encoded="yes" module="{module}" class="ViewProvider{proxy}"/>'))
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
    """Sketches with remaining degrees of freedom, or redundant / conflicting constraints."""
    out = []
    for o in doc.Objects:
        if o.TypeId == "Sketcher::SketchObject":
            err = o.solve()
            if err or not o.FullyConstrained:
                out.append(f"{o.Name}({err})" if err else o.Name)
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


def build_document():
    doc = App.newDocument("cassette")
    pieces, refs, asm, magnets = build(doc)
    colors = finish(doc, pieces, refs, magnets)
    return doc, pieces, refs, colors


def solid_overlap(a, b):
    """Volume of a common to a and b, leaving out slivers (touching faces, < 0.05 mm thick)."""
    if not a.BoundBox.intersect(b.BoundBox):
        return 0.0, None
    c = a.common(b)
    real = [s for s in c.Solids if s.Area > 0 and 2 * s.Volume / s.Area > 0.05]
    return sum(s.Volume for s in real), (Part.makeCompound(real).BoundBox if real else None)


def section_tops(shapes, v, us, zmax):
    """Top of the material below zmax along vertical lines (u, v), from the sections
    of the shapes in the plane v (zmax must be in the open, as under the lid sole)."""
    segs = []
    for sh in shapes:
        for w in sh.slice(V(0, 1, 0), v):
            pts = [(q.x, q.z) for q in w.discretize(Deflection=0.005)]
            segs += list(zip(pts, pts[1:]))
    tops = []
    for u in us:
        best = -math.inf
        for (x0, z0), (x1, z1) in segs:
            if min(x0, x1) <= u <= max(x0, x1) and x0 != x1:
                z = z0 + (z1 - z0) * (u - x0) / (x1 - x0)
                if z < zmax and z > best:
                    best = z
            elif x0 == x1 == u:
                for z in (z0, z1):
                    if z < zmax and z > best:
                        best = z
        tops.append(best)
    return tops


def pad_path(doc, pieces, refs, vals, say):
    """The pads of the leaf spring along their path, for no glass and for the
    thinnest and thickest glass: every step they meet (edge of the glass seat,
    entrance of the channel) stays under the height of their 45 deg chamfers, and
    the lift stays in the chamber of the lid. Returns (ok, max lift)."""
    pb, wb, h = vals["patin_bas"], vals["patin_largeur_bas"], vals["patin_hauteur"]
    room = vals["chambre_lames_haut"] - vals["semelle_dessous"] - vals["lames_epaisseur"]
    half = wb / 2 + h
    step = 0.25
    us = [vals["patin_x"] - half + i * step for i in range(int((vals["couvercle_course"] + 2 * half) / step) + 1)]
    base = [pieces["piece1_interface"].Shape, pieces["piece2_cadre_verre"].Shape, refs["Volet"].Shape]
    ok, worst = True, 0.0
    for label, t in (("no glass", None), ("glass min", vals["verre_epaisseur_min"]), ("glass max", vals["verre_epaisseur_max"])):
        shapes = list(base)
        if t is not None:
            c = vals["verre_cote"]
            shapes.append(Part.makeBox(c, c, t, V(-c / 2, -c / 2, vals["plan_film"])))
        lifts = []
        for v in (vals["lames_axe"] - vals["lames_largeur"] / 2 + 0.3, vals["lames_axe"],
                  vals["lames_axe"] + vals["lames_largeur"] / 2 - 0.3):
            for sv in (1, -1):
                tops = section_tops(shapes, sv * v, us, vals["semelle_dessous"] - 0.01)
                for k in range(int(vals["couvercle_course"] / 0.5) + 1):
                    pc = vals["patin_x"] + k * 0.5
                    lift = 0.0
                    for u, z in zip(us, tops):
                        if abs(u - pc) <= half and z > -math.inf:
                            lift = max(lift, z - (pb + max(0.0, abs(u - pc) - wb / 2)))
                    lifts.append(lift)
        top = max(lifts)
        worst = max(worst, top)
        good = top <= h - 0.15 and top <= room - 0.2
        ok &= good
        say(f"  leaf pads along the travel, {label}: lifted up to {top:.2f} mm "
            f"(chamfers {h:.2f}, chamber {room:.2f})" + ("" if good else "  <-- !"))
    return ok, worst


def motion_check(doc, pieces, refs, say):
    """Slide the lid open and closed, dark slide in place.
    1. The joints are the mechanism: thrown anywhere and solved, the lid must end
       up moved along u only (the slider joint is the rails), its spring and
       magnets with it, and the latch slider along u only. (The solver leaves a
       free joint where it likes and applies the limits only when dragging.)
    2. Millimetre by millimetre over the travel, the lid and its magnets must not
       enter what stays; past the end the stop pins hold it (captive), and below
       0 the lip stops it.
    3. The pads of the leaf spring climb every step on their way (pad_path)."""
    sheet, asm = doc.getObject(SHEET), doc.getObject("Cassette")
    get = lambda n: float(sheet.get(n))  # noqa: E731
    vals = param_values()
    lid, spring = pieces["piece3_couvercle"], pieces["ressort_lames"]
    mags = [o for o in asm.Group if o.TypeId == "Part::Cylinder"]
    moving = {"couvercle": lid, "ressort": spring}
    moving.update({m.Label: m for m in mags if "couvercle" in m.Name})
    pins = {o.Label: o for k, o in refs.items() if k.startswith("Goupille")}
    fixed = {"piece 1": pieces["piece1_interface"], "piece 2": pieces["piece2_cadre_verre"],
             "glissiere": pieces["glissiere_verrou"], "capot": pieces["capot_verrou"], "volet": refs["Volet"],
             "verre": refs["Verre_57x57"]}
    fixed.update({m.Label: m for m in mags if "piece2" in m.Name})
    fixed.update(pins)
    rest = {k: o.Placement for k, o in moving.items()}
    ok, problems = True, []
    for x in (10, 40, 70):
        lid.Placement = App.Placement(V(x, 3, -2), App.Rotation(V(0, 0, 1), 7) * App.Rotation(V(1, 0, 0), 20))
        asm.solve()
        pl = lid.Placement
        slide_ok = pl.Rotation.Angle < 1e-6 and abs(pl.Base.y) < 1e-4 and abs(pl.Base.z) < 1e-4
        follow_ok = all(o.Placement.isSame(pl.multiply(rest[k]), 1e-6) for k, o in moving.items())
        if not (slide_ok and follow_ok):
            ok = False
            problems.append(f"lid thrown {x} mm away and solved: "
                            + ("not moved along u only" if not slide_ok else "spring or magnets left behind"))
    for k, o in moving.items():
        o.Placement = rest[k]
    slider = pieces["glissiere_verrou"]
    slider.Placement = App.Placement(V(-2, 1, 1), App.Rotation(V(0, 0, 1), 3))
    asm.solve()
    pl = slider.Placement
    if abs(pl.Base.y) > 1e-6 or abs(pl.Base.z) > 1e-6 or pl.Rotation.Angle > 1e-9:
        ok = False
        problems.append("latch slider not kept on its travel along u")
    slider.Placement = App.Placement()
    for k, o in moving.items():
        o.Placement = rest[k]
    # sweep: the lid and its magnets (the spring is elastic: its pads are checked on their path)
    course = get("couvercle_course")
    steps = [float(i) for i in range(int(course) + 1)] + [course]
    rigid = {k: o.Shape for k, o in moving.items() if k != "ressort"}
    fixed_shapes = {k: o.Shape for k, o in fixed.items()}

    def entering(dx):
        out = []
        move = App.Placement(V(dx, 0, 0), App.Rotation()).toMatrix()
        for k, sh in rigid.items():
            moved = sh.transformGeometry(move)
            for f, fs in fixed_shapes.items():
                v, _ = solid_overlap(moved, fs)
                if v >= 0.01:
                    out.append((k, f, v))
        return out
    for dx in steps:
        for k, f, v in entering(dx):
            ok = False
            problems.append(f"{dx:g} mm: {k} enters {f} ({v:.2f} mm3)")
    beyond = entering(course + 0.5)
    captive = beyond and all(f in pins for _, f, _ in beyond)
    closed = [f for _, f, _ in entering(-0.5)]
    stop = closed and all(f.startswith("piece") for f in closed)
    ok &= bool(captive) and bool(stop)
    say(f"  stops: 0.5 mm past the travel the dovetails hit the pins: {'yes' if captive else 'NO  <-- !'}; "
        f"0.5 mm before closed the lip hits the heel: {'yes' if stop else 'NO  <-- !'}")
    # the ready-made animations play: half way, the lid at the end of its travel and the latch locked
    parts = {o.Name: o.Placement for o in asm.Group if hasattr(o, "Placement")}
    for sim in [o for g in asm.Group if g.TypeId == "Assembly::SimulationGroup" for o in g.Group]:
        asm.generateSimulation(sim)
        asm.updateForFrame(asm.numberOfFrames() // 2)
        if sim.Name == "Ouverture_couvercle":
            pl = lid.Placement
            got, want = pl.Base.x, course
            good = abs(got - want) < 0.01 and abs(pl.Base.y) < 1e-4 and abs(pl.Base.z) < 1e-4
        else:
            got, want = pieces["glissiere_verrou"].Placement.Base.x, -get("glissiere_course")
            good = abs(got - want) < 0.01
        ok &= good
        say(f"  animation '{sim.Label}': half way {got:.2f} (expected {want:.2f})" + ("" if good else "  <-- !"))
    for o in asm.Group:
        if o.Name in parts:
            o.Placement = parts[o.Name]
    say(f"  joints: lid along u, spring and magnets following, latch on its travel: "
        f"{'yes' if not any('solved' in p or 'slider' in p for p in problems) else 'NO'}")
    say(f"  {len(steps)} positions from 0 to {course:g} mm: "
        f"{'no collision' if not problems else str(len(problems)) + ' problems'}")
    for p in problems[:12]:
        say(f"    {p}  <-- !")
    good, lift = pad_path(doc, pieces, refs, vals, say)
    return ok and good, lift


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
                                          "piece3_couvercle", "ressort_lames"))
    gl, ds = refs["Verre_57x57"].Shape, refs["Volet"].Shape
    latch, cover = shapes["glissiere_verrou"], shapes["capot_verrou"]
    travel = App.Placement(V(-param_values()["glissiere_course"], 0, 0), App.Rotation())
    latch_on = latch.transformGeometry(travel.toMatrix())
    pairs = [("p1-p2", p1, p2), ("p1-p3", p1, p3), ("p2-p3", p2, p3),
             ("glass-p1", gl, p1), ("glass-p2", gl, p2), ("glass-p3", gl, p3),
             ("slide-p1", ds, p1), ("slide-p2", ds, p2), ("slide-p3", ds, p3),
             ("latch-p3", latch, p3), ("cover-p3", cover, p3),
             ("leaves-p1", sp, p1), ("leaves-p2", sp, p2), ("leaves-p3", sp, p3), ("leaves-slide", sp, ds),
             ("latch-p1", latch, p1), ("cover-p1", cover, p1), ("cover-p2", cover, p2),
             ("latch-p2", latch, p2), ("latch-cover", latch, cover),
             ("latch_locked-p1", latch_on, p1), ("latch_locked-cover", latch_on, cover),
             ("latch_locked-p3", latch_on, p3)]
    vals = param_values()
    gc = vals["verre_cote"]
    gl_max = Part.makeBox(gc, gc, vals["verre_epaisseur_max"], V(-gc / 2, -gc / 2, vals["plan_film"]))
    pairs += [("glass_max-p2", gl_max, p2), ("glass_max-p3", gl_max, p3)]
    for k, o in refs.items():
        if k.startswith("Goupille"):
            pairs += [(f"{k}-p1", o.Shape, p1), (f"{k}-p2", o.Shape, p2), (f"{k}-p3", o.Shape, p3)]
    ls = refs["Ressort_verrou"].Shape
    ls_on = Part.makeCylinder(vals["ressort_verrou_diametre"] / 2, vals["ressort_verrou_longueur_ferme"],
                              V(vals["glissiere_dent_gauche_pied"] - vals["glissiere_course"], vals["ressort_verrou_y"],
                                vals["ressort_verrou_z"]), V(1, 0, 0))
    pairs += [("latch_spring-p1", ls, p1), ("latch_spring-p2", ls, p2), ("latch_spring-latch", ls, latch),
              ("latch_spring-cover", ls, cover), ("latch_spring_locked-p1", ls_on, p1),
              ("latch_spring_locked-latch", ls_on, latch_on), ("latch_spring_locked-cover", ls_on, cover)]
    say("\nInterferences (mm3, expected 0):")
    for name, a, b in pairs:
        c = a.common(b)
        # Rayfor meshes share faces with our pockets: slivers thinner than 0.05 mm are contacts
        real = [s for s in c.Solids if s.Area > 0 and 2 * s.Volume / s.Area > 0.05]
        v = sum(s.Volume for s in real)
        ok &= v < 0.01
        note = "  (contact)" if c.Volume > 0.01 and v < 0.01 else ""
        say(f"  {name:12s} {v:8.3f}{'' if v < 0.01 else '  <-- !'}{note}")
    # leaf spring: only the pads touch the glass, squeezed by the preload (thinnest) or more
    for t in ("verre_epaisseur_min", "verre_epaisseur_max"):
        g = Part.makeBox(gc, gc, vals[t], V(-gc / 2, -gc / 2, vals["plan_film"]))
        d = vals["plan_film"] + vals[t] - vals["patin_bas"]
        d0 = max(0.0, vals["plan_film"] - vals["patin_bas"])     # a free pad may go through a thin glass
        want = 2 * vals["lames_largeur"] * (vals["patin_largeur_bas"] * (d - d0) + d * d - d0 * d0)   # two pads, 45 deg sides
        got = sp.common(g).Volume
        good = abs(got - want) < 0.01 * want and vals["plan_film"] + vals[t] < vals["semelle_dessous"] - 0.5
        ok &= good
        say(f"  leaf pads on a {vals[t]:g} mm glass: squeezed {d:.2f} mm, only the pads touch it"
            + ("" if good else f"  <-- ! ({got:.1f} vs {want:.1f} mm3)"))
    # embedded magnets: inside their cavities, enough cover, and where to pause the prints
    for m in [o for o in doc.Objects if o.TypeId == "Part::Cylinder" and o.Name.startswith("Aimant_")]:
        piece = p2 if "piece2" in m.Name else p3
        v = m.Shape.common(piece).Volume
        ok &= v < 0.01
        if v >= 0.01:
            say(f"  {m.Label} enters its piece ({v:.2f} mm3)  <-- !")
    cover = vals["collerette_epaisseur"] - vals["aimant_peau"] - vals["aimant_epaisseur"] - vals["aimant_jeu"]
    ok &= cover >= 0.6
    seat_r = (vals["aimant_diametre"] + vals["aimant_jeu"]) / 2
    csk = vals["vis_fraisure_diametre"] / 2
    walls = {"rail": vals["aimant_y"] - seat_r - vals["rail_axe"] - vals["rail_queue_demi_largeur"],
             "edge": vals["plaque_bord_haut"] - vals["aimant_y"] - seat_r,
             "screws": min(math.hypot(vals["aimant_x"] - x, vals["aimant_y"] - abs(y)) - seat_r - csk
                           for x, y in ((vals["vis_bas_x"], vals["vis_bas_y"]), (vals["vis_haut_droite_x"], vals["vis_haut_y"]))),
             "claw clearance": vals["aimant_x"] - seat_r - vals["fenetre_griffe_droite"] - vals["griffes_degagement"]}
    thin = {k: w for k, w in walls.items() if w < 0.6}
    ok &= not thin
    say("  walls around the magnet seats: " + ", ".join(f"{k} {w:.2f}" for k, w in walls.items())
        + (f"  <-- ! under 0.6 mm" if thin else ""))
    # latch spring: always compressed, both ends bearing (left tooth of the slider, island of piece 1)
    sl, so = latch.distToShape(ls)[0], p1.distToShape(ls)[0]
    sl_on, so_on = latch_on.distToShape(ls_on)[0], p1.distToShape(ls_on)[0]
    pre = vals["ressort_verrou_precharge"]
    good = pre > 0 and max(sl, so, sl_on, so_on) < 1e-6
    ok &= good
    say(f"  latch spring {vals['ressort_verrou_diametre']:g} x {vals['ressort_verrou_longueur_libre']:g}: "
        f"{vals['ressort_verrou_longueur_ouvert']:g} mm open, {vals['ressort_verrou_longueur_ferme']:g} mm locked "
        f"(preload {pre:.1f} mm), bearing on the slider and piece 1" + ("" if good else
        f"  <-- ! (gaps {sl:.2f} {so:.2f} / {sl_on:.2f} {so_on:.2f})"))
    # inner groove of the mating face: walls to the opening and to the dark slide slot
    lip = {"to the opening": (vals["gorge_interieure_cote_interieur"] - vals["peau_ouverture"]) / 2,
           "to the dark slide": vals["peau_epaisseur"] - vals["gorge_interieure_profondeur"]}
    thin = {k: w for k, w in lip.items() if w < 0.6}
    ok &= not thin
    say("  walls around the inner lip groove: " + ", ".join(f"{k} {w:.2f}" for k, w in lip.items())
        + (f"  <-- ! under 0.6 mm" if thin else ""))
    say(f"  magnets: {2 * vals['aimant_peau'] + vals['aimant_jeu']:.1f} mm apart through two skins, "
        f"{cover:.1f} mm over the cavity of piece 2" + ("" if cover >= 0.6 else "  <-- !"))
    say(f"  print pause to drop the magnets in: piece 2 (rear face down, on its left lip) at "
        f"{vals['levre_gauche_hauteur'] + vals['aimant_peau'] + vals['aimant_epaisseur'] + vals['aimant_jeu']:.2f} mm, lid (outer face down) at "
        f"{vals['couvercle_hauteur'] - vals['aimant_peau']:.2f} mm")
    # sliding lid: rails out through the straight face of the heel, walls, the lid clears the glass
    q = vals["rail_axe"] + vals["rail_queue_demi_largeur"]
    geo = {"channel to rail": vals["rail_axe"] - vals["rail_queue_demi_largeur"] - vals["couloir_demi_hauteur"],
           "rail to the rounded heel corner": vals["talon_demi_hauteur"] - vals["rayon_coins"] - q,
           "pin hole to the end of the rail": vals["talon_bord_droit"] - vals["goupille_x"] - vals["goupille_trou_diametre"] / 2,
           "lid open past the glass seat": -vals["plaque_demi_largeur"] + vals["couvercle_course"]
           - vals["verre_cote"] / 2 - vals["verre_jeu"]}
    mins = {"channel to rail": 0.8, "rail to the rounded heel corner": 0.0, "pin hole to the end of the rail": 0.8,
            "lid open past the glass seat": 0.5}
    bad = [k for k, w in geo.items() if w < mins[k] - 1e-9]
    ok &= not bad
    say("  sliding lid: " + ", ".join(f"{k} {w:.2f}" for k, w in geo.items()) + ("  <-- ! " + ", ".join(bad) if bad else ""))
    # pushed up by the leaves, the lid is held by the dovetails: free up to tete_jeu, caught just above
    def lifted(dz):
        return p3.transformGeometry(App.Placement(V(0, 0, dz), App.Rotation()).toMatrix()).common(p2).Volume
    tj = vals["tete_jeu"]
    free, caught = lifted(tj - 0.02), lifted(tj + 0.05)
    good = free < 0.01 and caught >= 0.01
    ok &= good
    say(f"  lid pushed up by the leaves: free up to {tj:.2f} mm, the dovetails catch it above"
        + ("" if good else f"  <-- ! ({free:.3f} / {caught:.3f} mm3)"))
    shift = {"glissiere_verrou": param_values()["verrou_paroi"] - 1.0, "capot_verrou": 0.0}
    for key, ref in (("glissiere_verrou", "Rayfor_glissiere"), ("capot_verrou", "Rayfor_capot")):
        r = doc.getObject(ref).Shape.transformGeometry(
            App.Placement(V(0, 0, shift[key]), App.Rotation()).toMatrix())
        say(f"  {key}: volume {shapes[key].Volume:.1f} vs Rayfor STL {r.Volume:.1f} mm3, "
            f"difference {shapes[key].cut(r).Volume + r.cut(shapes[key]).Volume:.1f} mm3")
    say("\nSliding the lid open and closed, dark slide in:")
    good, lift = motion_check(doc, pieces, refs, say)
    ok &= good
    # leaf spring, PETG (E about 2 GPa): force on the glass, strain at the highest lift
    E, t, b, L = 2000.0, vals["lames_epaisseur"], vals["lames_largeur"], vals["lames_longueur"]
    k = 3 * E * (b * t ** 3 / 12) / L ** 3
    d0 = vals["lames_precharge"]
    d1 = d0 + vals["verre_epaisseur_max"] - vals["verre_epaisseur_min"]
    strain = 3 * t * lift / (2 * L ** 2)
    say(f"  leaf spring: {2 * k * d0:.1f} N on the thinnest glass, {2 * k * d1:.1f} N on the thickest, "
        f"{2 * k * lift:.1f} N at the highest lift ({lift:.2f} mm, strain {100 * strain:.1f} %)"
        + ("" if strain < 0.02 else "  <-- ! over 2 %"))
    ok &= strain < 0.02
    return ok, shapes


def main():
    os.makedirs(OUT, exist_ok=True)
    doc, pieces, refs, colors = build_document()
    for w in WARNINGS:
        print("warning:", w, flush=True)
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
    print(f"\nEmulsion plane at w = {vals['plan_film']} ; dark slide gap w {vals['peau_epaisseur']}..{vals['butee_face_avant']:.2f}")
    print("ALL CHECKS OK" if ok else "CHECKS FAILED", flush=True)
    return ok


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
