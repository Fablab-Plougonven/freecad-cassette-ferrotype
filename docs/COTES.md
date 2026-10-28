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
| Fenêtre de la plaque Rayfor | 61,5 × 61,5 centrée. Elle laisse entrer la **lèvre intérieure** du boîtier, autour de son ouverture. Dans la cassette (2026-10-28) : ouverture de la peau avant de 55 × 55 (`peau_ouverture`, comme la butée de la pièce 2), et une **deuxième gorge** pour la lèvre intérieure : carré intérieur 59, extérieur 61 (1 de large), 1 de profondeur (`gorge_interieure_cote_interieur`, `gorge_interieure_largeur`, `gorge_interieure_profondeur`). Il reste 2,0 de paroi entre l'ouverture et la gorge, 0,9 de peau entre le fond de la gorge et la fente du volet (contrôlés au build, 0,6 au moins). Avant : ouverture de 61,9 ; un essai à 56 sans gorge, la lèvre intérieure soulevait la pièce 1 |
| 4 trous Ø3,1, entraxe 75 × 75 | Propres à l'Imacon. À réutiliser pour assembler la pièce 1 à la pièce 2 |

Les poches A et B servent de dégagement pour les ergots et l'accouplement du
boîtier. Il faut les garder : sans elles, la cassette ne se plaque pas.

Le boîtier a **deux lèvres** à l'arrière : une intérieure, au bord de
l'ouverture, qui entre dans la deuxième gorge (carré 59 → 61, 1 de profondeur),
et une entre le bord et l'intérieur, qui entre dans la gorge de 1,5 × 0,5
(carré de 70,7). Leurs hauteurs n'ont pas été mesurées : la lèvre intérieure
doit rester sous 1 (fond de sa gorge), sinon la pièce 1 se soulève.

## Plan film et empilement (pièces 1 et 2)

L'émulsion est à **3,55 derrière la face d'appui** (validé). De l'avant vers
l'arrière :

| Couche | Profondeur depuis la face d'appui | Épaisseur |
|---|---|---|
| Peau avant de la pièce 1, ouverture 55 × 55, gorge de la lèvre intérieure 59 → 61 sur 1 (il reste 0,9 de peau devant la fente ; à gauche, sous la fente, 0,7 au-dessus de la gorge extérieure) | 0 → 1,9 | 1,9 |
| Fente du volet, entre la peau et les rails de la pièce 2 | 1,9 → 2,3 | 0,4 |
| Butée de la pièce 2, ouverture 55 × 55 (1 d'appui par côté) | 2,3 → 3,55 | 1,25 |
| Plaque 57 × 57, de 1 à 3 d'épaisseur, dans un logement de 57,4 | 3,55 → 4,55 à 6,55 | 1 à 3 |
| Couloir du couvercle (pièce 2) : fond à 7,3 ; semelle du couvercle à 7,5, au-dessus du verre le plus épais (6,55) | 7,3 → 10,1 | — |
| Ressort à lames : lames de 1,2 sous la semelle, patins écrasés de 1,5 (verre de 1) à 3,5 (verre de 3) | 3,05 → 8,7 | — |

## Volet

- Inséré **par la gauche** (u < 0), comme sur le Hasselblad. Par le haut il
  traverserait la poche du verrou, imposée par le boîtier.
- Fente borgne jusqu'à u = +30,9, de 66,38 × 0,4, pour la plaque métal mesurée à
  65,88 de large (0,5 de jeu), épaisse de 0,35 au plus.
- Velours à l'entrée, sur la peau de la pièce 1 et sur la pièce 2.

## Étanchéité entre les pièces

- **Chicane de la collerette** : nervure en U de 0,6 × 0,8 sous la collerette
  de la pièce 2, dans une gorge de 1,0 × 1,0 à l'arrière de la pièce 1, à 36,1
  du centre, en haut, en bas et à droite.
- **Chicane des rails** : nervure de 0,5 × 0,5 sous les rails du volet et sa
  butée de fond, dans une gorge de 0,9 × 0,6 du fond de la poche de la pièce 1.
  Elle coupe le chemin de la lumière qui longerait l'insert depuis le bord
  gauche jusqu'à la fente.
- **Couvercle coulissant** : une languette de 1,2 × 1,0 sur toute la longueur de
  chaque rail, dans la gorge de 1,6 × 0,8 du rail ; à gauche, une languette de
  0,8 × 1,5 au bout de la semelle, dans une fente de 1,2 × 1,7 de la paroi du
  couloir, engagée en fin de course ; au bord gauche, une lèvre de 1,5 × 1,2 de
  la pièce 2, coiffée par une feuillure du couvercle (0,2 de jeu) ; à droite, la lèvre du couvercle descend
  devant la face du talon jusqu'à z 5 (1,7 sous le fond du couloir).
- Les fenêtres des griffes, en haut, sont hors de la zone étanche (au-delà de
  la lèvre du boîtier) ; la collerette de la pièce 2 a un dégagement en face
  d'elles, au cas où les griffes dépassent du capot.

## Couvercle coulissant (2026-10-28)

Remplace le couvercle à charnière : il coulisse vers la droite (vu de l'arrière),
imperdable, et on l'ouvre volet en place.

- **Rails** : deux rails en queue d'aronde dans la collerette de la pièce 2, en
  haut et en bas (axe à ±32,1, `rail_axe`) : une gorge de 1,6 × 0,8 sous la face
  arrière, puis une queue à 45° jusqu'à 4,4 de large au fond (z 7,9). Fermés à
  gauche au pied de la lèvre gauche (à −40,7, 1,5 de paroi), ils sortent par la face droite du talon, dans sa
  partie droite (0,2 avant l'arrondi du coin). Le couvercle porte une languette
  sur toute la longueur (la chicane) et, à son bout gauche, deux queues d'aronde
  de 12 de long (`tete_longueur`), 0,1 de jeu sur les pans (`tete_jeu`,
  2026-10-28 ; 0,3 avant) : elles le tiennent contre la poussée des lames, et le
  bord gauche du couvercle ne monte que de 0,1 (contrôlé au build). Ajustement
  serré : si ça frotte à l'impression, poncer les pans ou passer `tete_jeu` à 0,15.
- **Lèvre gauche** (2026-10-28, demandée pour l'étanchéité) : la pièce 2 porte
  une lèvre de 1,5 de large et 1,2 de haut le long de son bord gauche, d'un rail
  à l'autre : elle s'arrête aux bords extérieurs des rails (±34,3) et les rails
  viennent jusqu'à son pied, si bien que la lèvre et les languettes des rails
  font une chicane continue autour du couloir ; une feuillure sous le bord
  gauche du couvercle la coiffe avec 0,2 de jeu. Le couvercle se ferme vers la
  gauche : la feuillure arrive sur la lèvre en fin de course et la quitte à
  l'ouverture. La lumière qui entre par le bord gauche passe sur la lèvre, la
  descend, puis longe la face jusqu'à la languette du couloir. La pièce 2 repose
  alors sur sa lèvre à l'impression : supports sous le reste de la face arrière,
  pause des aimants à 3,80.
- **Couloir** : la semelle du couvercle (sous sa face, de 7,5 à 10,1) glisse dans
  un couloir de la pièce 2 de 57,8 de haut, fermé à gauche à −28,9 et ouvert à
  droite, au fond à z 7,3 (0,6 de collerette sur la pièce 1). C'est ce qui
  permet des lames : sans couloir, elles devraient plier de plus de 6 mm en
  passant sur la collerette. Il reste 1,0 de paroi entre le couloir et les rails.
- **Course** : 72,4 (`couvercle_course`) ; ouvert, le bord gauche du couvercle
  est 1,5 au-delà du logement du verre (`couvercle_degagement`). Il dépasse alors
  d'environ 72 à droite, tenu par les queues d'aronde.
- **Butée d'ouverture (imperdable)** : deux goupilles Ø2 × 4,7 (bouts de tige) à
  x 45,6, posées par l'avant de la pièce 2 dans un trou Ø2,1 du fond du rail et
  2,5 dans la pièce 1 : la pièce 1 les enferme. Elles dépassent de 1,0 dans la
  queue du rail : les queues d'aronde y butent, la languette passe au-dessus
  (0,2). Il reste 1,85 entre le trou et le bout du rail. Pour sortir le couvercle,
  dévisser la pièce 2.
- **Butée de fermeture** : la lèvre de 1,5 du bout droit du couvercle, devant la
  face droite du talon, de z 5 au dessus. Elle **dépasse de 1,5 à droite du
  talon** (u 48,5 → 50) : à vérifier sur le boîtier.
- **Ressort à lames** (`ressort_lames.stl`, pièce imprimée à part, collée sous
  la semelle par sa barre de racine) : deux lames de 24 × 8 × 1,2 le long de u,
  à v ±15, racine à gauche (elles traînent quand on ferme), un patin au bout,
  plat d'appui de 1 et chanfreins à 45° des deux côtés sur toute sa hauteur
  (4,45). Les patins montent ainsi les marches dans les deux sens : bord du
  logement du verre, et entrée du couloir à droite quand on referme le
  couvercle (4,25 de marche depuis la position libre). Le build suit chaque
  patin sur toute la course, sans verre, avec un verre de 1 et de 3 : levée
  maximale 4,25, sous les chanfreins (4,45) et dans la chambre (4,75).
  Écrasement 1,5 sur un verre de 1, 3,5 sur un verre de 3. Force estimée (PETG,
  E ≈ 2 GPa) : 1,5 N sur un verre de 1, 3,5 N sur un verre de 3, 4,2 N au plus
  haut, déformation 1,3 %. Moins que le ressort en croix (4 à 9 N) : à essayer.
- **Aimants** : deux paires Ø6 × 2 en x 28, y ±38,675, dans les bandes entre les
  rails et les bords (1,28 de paroi vers le rail, 1,27 vers le bord), vers le
  bout droit du couvercle, qui sans eux se soulèverait sous la poussée des lames
  (les queues d'aronde tiennent le bout gauche). Logements fermés Ø6,2 × 2,2
  sous une peau de 0,4, posés pendant une pause d'impression (pièce 2 à 3,80 mm, posée sur sa lèvre gauche ;
  couvercle à 7,00 mm) ; 1,0 entre les aimants couvercle fermé.
- **Vis** : deux dans les coins du bas (x ±38, y −39), une de chaque côté du
  verrou en haut (x −28 et 37, y 39). L'ancienne vis du talon (44, 28) tombait
  dans le couloir.
- **Assemblage FreeCAD** : liaison glissière du couvercle (de 0 à
  `couvercle_course`), ressort à lames fixé au couvercle. Le build vérifie que
  la liaison ne laisse que la translation selon u, fait glisser le couvercle
  millimètre par millimètre, volet en place, sans collision, puis 0,5 au-delà
  (les queues d'aronde touchent les goupilles) et 0,5 avant la fermeture (la
  lèvre touche le talon).
- Supprimés : charnière (nœuds, gousset, axe, bloc sous la pièce 1), ressort
  en croix et son tenon, nervures carrées du couvercle et leurs gorges.
- Impression : le couvercle face extérieure sur le plateau (la lèvre part du
  plateau ; les queues d'aronde à 45° et la languette gauche, 1,5 en
  porte-à-faux, sont en haut). La pièce 2 face arrière vers le plateau, posée
  sur sa lèvre gauche, supports sous le reste de la face : les rails
  s'élargissent à 45° en montant.

## Verrou

- Repris de Rayfor : fenêtres, poche, glissière à rampe, capot. La pièce 1
  laisse 0,2 de jeu par côté (`latch_fit`), la paroi devant la glissière fait
  0,8 (1,0 était trop épais à l'essai).
- Le capot affleure l'arrière de la pièce 1 et c'est la collerette de la pièce 2
  qui le tient : pas de vis.
- Ressort de compression Ø2 × 10 (2026-10-28), dans la poche sous la glissière,
  entre sa dent gauche et l'îlot (le taquet) : il pousse la glissière vers la
  position verrouillée. Avec l'îlot de Rayfor (bord gauche à 2,75), il restait
  11,7 entre la dent et le taquet glissière verrouillée : le ressort flottait
  (essai du 2026-10-28). Le bord gauche de l'îlot est maintenant calculé
  (`verrou_ilot_gauche` = −0,45) pour que le ressort fasse 9 verrouillé
  (écrasé de 1, `ressort_verrou_precharge`) et 5,5 déverrouillé (course 3,5).
  Le build vérifie que le ressort touche la dent et le taquet dans les deux
  positions, sans rien traverser. Le ressort se comprime bien jusqu'à 5,5
  (vérifié sur le ressort le 2026-10-28).
- Derrière la lèvre des crochets, 5,6 de vide sur la largeur des encoches : ni
  charnière ni couvercle à cet endroit.

## Validé

- Plan film à 3,55, plaque de 57 × 57 × 1, volet de 65,88 de large.

## À vérifier sur le boîtier

1. Hauteur et largeur des deux lèvres du boîtier (la lèvre intérieure doit entrer dans 59 → 61 sur 1).
2. Longueur des griffes : dépassent-elles du capot ?
3. Netteté au verre dépoli.
