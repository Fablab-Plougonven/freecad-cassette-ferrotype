# Dos ferrotype 5 × 5 pour Hasselblad V : cotes

Objectif : une cassette à plaque humide 57 × 57 mm pour boîtier Hasselblad 500
(même principe que la cassette Etsy « cassette à plaques humides 5 × 5 »).

Plan coté : [interface-V-cotes.png](interface-V-cotes.png)

## D'où viennent les cotes

| Source | Ce qu'on en tire | Fiabilité |
|---|---|---|
| Monture V de **Rayfor** pour dos Imacon (`sources/hasselblad-v-mount-for-imacon-digital-back-model_files`, STL) | Toute la géométrie de l'accroche : contour, crochets, verrou, gorge, poches | Bonne : testée sur un vrai boîtier avec un Imacon 132C, et reprise telle quelle par OwlfotO |
| Dos diascope d'**OwlfotO** (`sources/hasselblad-v-system-diascope-back-model_files`, 3MF) | Confirme le contour de Rayfor (plaque 90,7 × 88,85 identique). Fenêtre film 55,0 × 55,0 | Bonne |
| Forums (Pentax Forums, Photrio, Brian Smith) | Tirage mécanique 74,9 mm. Face avant du magasin → plan film **3,55 ± 0,05 mm** (cote de calibrage SAV) | Moyenne : à valider au verre dépoli |
| Photos Etsy (`sources/*.avif`) | Architecture : charnière côté crochets, couvercle avec ressort en croix, aimants aux coins, volet alu inséré **par le côté** | Qualitatif |

Licence : Rayfor et OwlfotO publient en CC BY-NC-SA 4.0. On peut remixer pour
le Fablab en citant les auteurs, mais pas vendre.

## Repère

Vue de l'arrière (côté photographe). **Haut = verrou, bas = crochets.**
Origine = centre de la fenêtre image. u vers la droite, v vers le haut.
La face d'appui est la face qui touche le boîtier.
La droite (u > 0) est le côté de la manivelle, avec le talon et les poches.

Dans le STL de Rayfor : u = 49,0 − x, v = 92,08 − z. La face d'appui est en
y = 16,22 et la face arrière en y = 9,52.

## Interface boîtier (pièce 1)

| Élément | Cote (mm) |
|---|---|
| Plaque principale | 84,4 (u ±42,2) × 86,1 (v −43,04 → +43,05), coins r ≈ 3 |
| Languette haute (côté verrou) | 64 de large (u ±32), dépasse de 2,75 (jusqu'à v +45,8), chanfreins 2,9 × 2,75 |
| Talon côté manivelle | u +42,2 → +48,5 (6,3) × 75 de haut (v ±37,5), coins r ≈ 3 |
| Encombrement total | 90,7 × 88,85 |
| Épaisseur de la plaque Rayfor | 6,7 |
| **Encoches des crochets** (bord bas) | 2 encoches de 6,5 de large, centrées à u = ±27,05 (entraxe 54,1), profondes de 1,55. Évidées sur les 5,6 arrière ; il reste une **lèvre de 1,1 côté boîtier**, que les crochets viennent prendre |
| **Fenêtres du verrou** (haut, face d'appui) | 2 fenêtres de 6,45 × 1,61, u = ±11,75 → ±18,2 (entraxe ≈ 30), v = +39,25 → +40,86 |
| Poche du verrou | u −18,2 → +26,2, v +37,25 → +44,3, de 1,0 à 4,0 de profondeur sous la face d'appui (une paroi de 1,0 reste côté boîtier). Dans la cassette : paroi ramenée à 0,8 et 0,2 de jeu par côté pour la glissière et le capot (impression d'essai du 2026-10-14) |
| Verrou coulissant (pièce `Latch`) | 40,9 × 4,7 × 11,7. Course ≈ 3,5 selon u. Languette moletée de 16,9 qui sort de ≈ 3 au-dessus du bord haut. Le dos des deux dents est une **rampe** : 0,81 d'épaisseur au bout, pleine épaisseur 6,59 plus loin (≈ 18°) ; la griffe monte dessus et plaque la cassette. Capot `LatchCover` de 56,4 × 2,4, fixé par 2 trous Ø1,8, avec deux fenêtres en face de celles des griffes. Remodélisés en esquisses (`glissiere_verrou`, `capot_verrou`), écart de volume 2 % avec les STL |
| Poche A (côté manivelle) | 3 × 17 : u +39 → +42, v +2,76 → +19,76, profonde de 5,9 depuis la face d'appui |
| Poche B (côté manivelle) | 2 × 4,5 : u +39,5 → +41,5, v −24,0 → −28,5, profonde de 5,9 |
| Gorge anti-lumière (face d'appui) | Carré intérieur 70,7 × 70,7 centré, 1,5 de large × 0,5 de profondeur, sur les 4 côtés, une seule esquisse (`gorge_cote_interieur`, `gorge_largeur`, `gorge_profondeur`). Elle **reçoit une lèvre du boîtier** : sans gorge sur le côté gauche, la pièce 1 se soulevait (essai du 2026-10-14). Avant le 2026-10-21 : 2 × 1,2, axe sur un carré de 72, profondeur du côté gauche réglable à part |
| Fenêtre de la plaque Rayfor | 61,5 × 61,5 centrée. Elle laisse entrer la **lèvre intérieure** du boîtier, autour de son ouverture. Dans la cassette : ouverture de la peau avant de 61,9 (`peau_ouverture`) ; avec 56, la lèvre intérieure soulevait la pièce 1 |
| 4 trous Ø3,1, entraxe 75 × 75 | Propres à l'Imacon. À réutiliser pour assembler la pièce 1 à la pièce 2 |

Les poches A et B servent de dégagement pour les ergots et l'accouplement du
boîtier. Il faut les garder : sans elles, la cassette ne se plaque pas.

Le boîtier a **deux lèvres** à l'arrière : une intérieure, au bord de
l'ouverture, qui entre dans l'ouverture de 61,9, et une entre le bord et
l'intérieur, qui entre dans la gorge de 2 × 1,2 (carré de 72). Leurs hauteurs
n'ont pas été mesurées : la lèvre intérieure doit rester sous 1,9 (elle arrive
devant le volet).

## Plan film et empilement (pièces 1 et 2)

L'émulsion est à **3,55 derrière la face d'appui** (validé). De l'avant vers
l'arrière :

| Couche | Profondeur depuis la face d'appui | Épaisseur |
|---|---|---|
| Peau avant de la pièce 1, ouverture 61,9 (à gauche, sous la fente, il reste 0,7 au-dessus de la gorge) | 0 → 1,9 | 1,9 |
| Fente du volet, entre la peau et les rails de la pièce 2 | 1,9 → 2,3 | 0,4 |
| Butée de la pièce 2, ouverture 55 × 55 (1 d'appui par côté) | 2,3 → 3,55 | 1,25 |
| Plaque 57 × 57, de 1 à 3 d'épaisseur, dans un logement de 57,4 | 3,55 → 4,55 à 6,55 | 1 à 3 |
| Ressort en croix : moyeu et bras à 0,3 au-dessus du verre le plus épais, pieds écrasés de 1,5 (verre de 1) à 3,5 (verre de 3) | 6,85 → 7,85 | 1,0 |

## Volet

- Inséré **par la gauche** (u < 0), comme sur le Hasselblad. Par le haut il
  traverserait la poche du verrou, imposée par le boîtier.
- Fente borgne jusqu'à u = +30,9, de 66,38 × 0,4, pour la plaque métal mesurée à
  65,88 de large (0,5 de jeu), épaisse de 0,35 au plus.
- Velours à l'entrée, sur la peau de la pièce 1 et sur la pièce 2.

## Étanchéité entre les pièces

- **Chicane de la collerette** : nervure en U de 0,6 × 0,8 sous la collerette
  de la pièce 2, dans une gorge de 1,0 × 1,0 à l'arrière de la pièce 1, à 36,1
  du centre, en haut, en bas et à droite. Le bossage de la charnière descend à
  −37,5 pour la laisser passer.
- **Chicane des rails** : nervure de 0,5 × 0,5 sous les rails du volet et sa
  butée de fond, dans une gorge de 0,9 × 0,6 du fond de la poche de la pièce 1.
  Elle coupe le chemin de la lumière qui longerait l'insert depuis le bord
  gauche jusqu'à la fente.
- **Couvercle** : deux nervures de 1,0 × 0,8 dans deux gorges de 1,6 × 1,0 de la pièce 2, et une paroi qui ferme la face de la charnière.
- Les fenêtres des griffes, en haut, sont hors de la zone étanche (au-delà de
  la lèvre du boîtier) ; la collerette de la pièce 2 a un dégagement en face
  d'elles, au cas où les griffes dépassent du capot.

## Fermeture du couvercle

- Couvercle plein dans le prolongement des pièces (2026-10-21) : contour de la
  pièce 2 (plaque et talon), 7,4 de haut au-dessus d'elle (`couvercle_hauteur`),
  posé à plat sur toute sa face arrière, sans rien qui descende sur les côtés :
  on ouvre volet en place. Plein pour la matière contre la transparence du
  PETG : il n'est creusé que d'une chambre ronde pour le ressort (rayon 27,5,
  jusqu'à z 11,85 : bras soulevés de 3,5 + 0,5), des nervures, des logements
  d'aimants et d'un dégagement de 2,5 × 2,8 au-dessus du nœud central de la
  charnière. 5,65 de matière au-dessus de la chambre. Cassette de 17,5
  d'épaisseur (pièce 2 à 3,4 pour les aimants incrustés).
- Deux nervures de 1,0 × 0,8 dans deux gorges de 1,6 × 1,0 de la pièce 2
  (axes 33,5 et 30,7), autour de la chambre du ressort.
- Charnière côté crochets, axe Ø2. Le bloc du nœud central de la pièce 1 est
  hors de la cassette, sous la pièce 2 (jeu 0,4), tenu par le gousset à 45° :
  il laisse tourner le couvercle. La pièce 2 n'a plus de dégagement.
- Fermeture par aimants incrustés : deux paires Ø6 × 2 dans les coins opposés à
  la charnière, x ±35,2, y 38,675. En y, au milieu de la bande entre la gorge
  extérieure (34,3) et le bord haut (43,05) : 1,28 de paroi de chaque côté, le
  maximum. En x, au plus loin du bord latéral (3,9) que permet la fraisure de la
  vis du haut (1 de paroi). Logements fermés Ø6,2 × 2,2 (jeu 0,2) sous une peau
  de 0,4 côté joint, posés pendant une pause d'impression (pièce 2 à 2,60 mm,
  couvercle à 7,00 mm) ; 1,0 entre les aimants couvercle fermé. Collerette de
  la pièce 2 passée à 3,4 (0,8 au-dessus de la cavité). Vis : deux en bas
  (x ±20), une en haut à gauche du verrou (x −28), une sur le talon droit
  (44, 28), M3 × 8.
- Assemblage FreeCAD : liaison pivot de la charnière, butée à 160° (le couvercle
  plein touche le gousset de la pièce 1 vers 168°). Le build vérifie que la liaison est
  bien la charnière modélisée, puis ouvre le couvercle degré par degré de 0 à
  30°, de 2 en 2 au-delà, volet en place : aucune collision.
- Clips abandonnés (2026-10-21) : plus d'ergots sur le talon de la pièce 1. Le couvercle de test
  pour les pièces de la v0.1 (`tools/lid_for_v0_1.py`) garde les clips.
- Ressort pour des verres de 1 à 3 mm (`verre_epaisseur_min`, `verre_epaisseur_max`) :
  bras de 27 × 6 × 1, pieds Ø5 au bout. Écrasement 1,5 sur le verre le plus fin,
  3,5 sur le plus épais ; le bout des bras monte alors jusqu'à z 11,4, dans le
  logement du verre, sans toucher la pièce 2 ni le couvercle (vérifié au build).
  Force estimée (PETG, E ≈ 2 GPa) : environ 4 N sur un verre de 1, 8 à 9 N sur
  un verre de 3, que les deux paires d'aimants doivent retenir : à vérifier à
  l'essai. Déformation maximale des bras environ 1,8 %.

## Verrou

- Repris de Rayfor : fenêtres, poche, glissière à rampe, capot. La pièce 1
  laisse 0,2 de jeu par côté (`latch_fit`), la paroi devant la glissière fait
  0,8 (1,0 était trop épais à l'essai).
- Le capot affleure l'arrière de la pièce 1 et c'est la collerette de la pièce 2
  qui le tient : pas de vis.
- Derrière la lèvre des crochets, 5,6 de vide sur la largeur des encoches : ni
  charnière ni couvercle à cet endroit.

## Validé

- Plan film à 3,55, plaque de 57 × 57 × 1, volet de 65,88 de large.

## À vérifier sur le boîtier

1. Hauteur et largeur des deux lèvres du boîtier.
2. Longueur des griffes : dépassent-elles du capot ?
3. Netteté au verre dépoli.
