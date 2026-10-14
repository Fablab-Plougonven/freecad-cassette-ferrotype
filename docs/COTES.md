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
| Gorge anti-lumière (face d'appui) | 2 de large × 1,2 de profondeur. Axe sur un carré de 72 × 72 centré, contournée autour des 4 trous. Elle **reçoit une lèvre du boîtier** : sans gorge sur le côté gauche, la pièce 1 se soulevait (essai du 2026-10-14). Remise sur les 4 côtés ; profondeur du côté gauche réglable (`seal_depth_left`), car sous la fente il ne reste que 0,7 de peau |
| Fenêtre de la plaque Rayfor | 61,5 × 61,5 centrée. Elle laisse entrer la **lèvre intérieure** du boîtier, autour de son ouverture. Dans la cassette : ouverture de la peau avant de 61,9 (`skin_aperture`) ; avec 56, la lèvre intérieure soulevait la pièce 1 |
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
| Plaque 57 × 57 × 1 dans un logement de 57,4 | 3,55 → 4,55 | 1,0 |
| Ressort en croix (pieds écrasés de 0,8) | à partir de 4,55 | — |

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
- **Couvercle** : nervure de 1,0 × 0,8 dans une gorge de 1,6 × 1,0 de la pièce 2.
- Les fenêtres des griffes, en haut, sont hors de la zone étanche (au-delà de
  la lèvre du boîtier) ; la collerette de la pièce 2 a un dégagement en face
  d'elles, au cas où les griffes dépassent du capot.

## Fermeture du couvercle

- Charnière côté crochets, axe Ø2 ; deux clips côté manivelle (v 20 → 33 et
  −7 → 6), doigts de 1,4, arrêt de 0,6 sur une rampe de 2 de haut, bec biseauté.
  Un seul clip de 1,2 paraissait fragile à l'essai.

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
