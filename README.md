# 🗺️ Flux Mapper — Plugin QGIS

**Auteur :** KOTIN Ange H.P.  
**Contact :** angekotin@gmail.com  
**Version :** 2.0.0  
**Licence :** GNU GPL v2 or later (GPL-2.0-or-later)  
**Compatibilité QGIS :** 3.28 ou supérieur  

---

## 📌 Description

**Flux Mapper** est un plugin QGIS permettant de générer des **cartes de flux géographiques**
sous forme de **courbes de Bézier** entre des localités.

Il est conçu pour visualiser facilement des relations spatiales telles que :
- Flux de production et d'approvisionnement
- Flux commerciaux et de distribution
- Flux migratoires
- Tout autre réseau Origine–Destination (OD)

### Fonctionnalités principales

- ✅ **Courbes de Bézier** paramétrables entre chaque paire de localités
- ✅ **Flèches automatiques** avec épaisseur proportionnelle au score du flux
- ✅ **Couleur automatique** par type de relation
- ✅ **Flux bidirectionnels** avec décalage automatique des deux flèches
- ✅ **Génération en une seule couche globale** et/ou **une couche par type**
- ✅ **Détection automatique** des champs dans vos tables
- ✅ Fonctionne avec **toute version QGIS 3.x**

---

## 📦 Installation

### Méthode 1 — Via le gestionnaire d'extensions QGIS (recommandée)

1. Dans QGIS : **Extensions → Installer/Gérer les extensions**
2. Cliquez sur **"Installer depuis un ZIP"**
3. Sélectionnez le fichier `flux_mapper.zip`
4. Cliquez **Installer le plugin**
5. Le bouton 🗺️ apparaît dans la barre d'outils

### Méthode 2 — Installation manuelle

1. Décompressez `flux_mapper.zip`
2. Copiez le dossier `flux_mapper` dans le répertoire des plugins QGIS :

| Système | Chemin |
|---------|--------|
| **Windows** | `C:\Users\<VotreNom>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\` |
| **Linux**   | `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/` |
| **macOS**   | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/` |

3. Redémarrez QGIS
4. **Extensions → Gérer les extensions** → activez **Flux Mapper**

---

## 🗂️ Structure du projet

```
flux_mapper/
├── __init__.py            # Point d'entrée du plugin (requis par QGIS)
├── flux_mapper.py         # Classe principale — gestion du menu et du bouton
├── flux_mapper_dialog.py  # Interface graphique et logique de génération
├── metadata.txt           # Métadonnées du plugin (requis par QGIS)
├── LICENSE                # Licence MIT
├── README.md              # Ce fichier
└── icons/
    └── icon.png           # Icône du plugin
```

---

## 🔧 Utilisation

### Étape 1 — Préparer vos données

Vous avez besoin de **deux couches** dans QGIS :

#### Couche de localités (points)

| Propriété | Valeur attendue |
|-----------|----------------|
| Type de géométrie | **Point** |
| Champ obligatoire | Un champ **texte** contenant le **nom de chaque localité** |
| SCR recommandé | WGS84 / EPSG:4326 |

#### Couche de flux (table attributaire)

| Champ | Type | Obligatoire | Description |
|-------|------|-------------|-------------|
| Nom localité départ | Texte | ✅ Oui | Doit correspondre **exactement** au nom dans la couche points |
| Nom localité arrivée | Texte | ✅ Oui | Idem |
| Nom de la relation | Texte | ✅ Oui | Ex : Production, Commerce, Migration… |
| Score du flux | Nombre | ✅ Oui | Intensité du flux — contrôle l'épaisseur de la flèche |
| **Direction** | Texte | ⬜ Optionnel | `unidirectionnel` ou `bidirectionnel` |

> **Important :** Les noms de localités doivent être **identiques** dans les deux couches
> (respect des majuscules, des accents et des espaces).

---

### Étape 2 — Lancer le plugin

Cliquez sur le bouton **🗺️ Flux Mapper** dans la barre d'outils QGIS.

---

### Étape 3 — Configurer les paramètres

La boîte de dialogue comporte 4 onglets :

#### 📂 Onglet Données
- Sélectionnez la **couche de localités** (points)
- Sélectionnez la **couche de flux** (table)
- Choisissez le type de sortie : couche globale et/ou couches par type

#### 🔤 Onglet Champs
- Cliquez sur **🔄 Charger les champs** pour chaque couche
- Associez chaque rôle au bon champ de votre table
- Activez le champ **Direction** si votre table en contient un

#### 🎨 Onglet Style
- **Courbure** : intensité de la courbe de Bézier (0 = droit, 0.2 = recommandé)
- **Décalage bidirectionnel** : espacement entre les deux flèches d'un flux aller-retour
- **Multiplicateur d'épaisseur** : Score × multiplicateur = épaisseur en mm
- **Tête de flèche** : longueur et largeur de la pointe

#### ❓ Onglet Aide
Résumé rapide de l'utilisation directement dans le plugin.

---

### Étape 4 — Générer

Cliquez sur **▶ Générer les flux**.

Les couches générées apparaissent dans le panneau des couches QGIS avec :
- Flèches directionnelles automatiques
- Épaisseur proportionnelle au score
- Couleur différente par type de relation

---

## ↔️ Flux bidirectionnels

Pour représenter un flux aller-retour entre deux localités :

1. Dans votre table, renseignez `bidirectionnel` dans le champ Direction
2. Le plugin génère automatiquement **deux flèches décalées** :
   - une flèche A → B
   - une flèche B → A
3. Le décalage évite que les deux flèches se superposent (réglable dans Style)

---

## 🎨 Style des couches générées

Après génération, vous pouvez affiner le style dans **Propriétés → Symbologie** :

Pour une épaisseur encore plus contrastée, utilisez cette expression QGIS dans
la largeur de la flèche :

```
CASE
  WHEN "Score_flux" = 1 THEN 0.3
  WHEN "Score_flux" = 2 THEN 0.8
  WHEN "Score_flux" = 3 THEN 1.5
  WHEN "Score_flux" = 4 THEN 2.5
  WHEN "Score_flux" = 5 THEN 4.0
  ELSE 0.5
END
```

---

## 📋 Champs des couches générées

Chaque couche de flux produite contient les champs suivants :

| Champ | Type | Description |
|-------|------|-------------|
| `id_flux` | Entier | Identifiant unique de chaque entité |
| `Origine` | Texte | Nom de la localité de départ |
| `Destination` | Texte | Nom de la localité d'arrivée |
| `Type_flux` | Texte | Type / nom de la relation |
| `Score_flux` | Décimal | Score d'intensité du flux |
| `Epaisseur_mm` | Décimal | Épaisseur calculée en mm (Score × multiplicateur) |
| `Direction` | Texte | `unidirectionnel`, `bidirectionnel_aller` ou `bidirectionnel_retour` |

---

## ❓ Dépannage

| Problème | Cause probable | Solution |
|----------|---------------|----------|
| Flux manquants dans le résultat | Noms de localités différents entre les deux couches | Vérifiez la casse, les accents et les espaces |
| Aucune couche créée | Champs mal associés | Rechargez les champs dans l'onglet Champs |
| Flèches non visibles | Épaisseur trop faible | Augmentez le multiplicateur dans Style |
| Flèches bidirectionnelles superposées | Décalage trop faible | Augmentez le décalage bidirectionnel dans Style |
| Plugin non visible après installation | Plugin pas activé | Extensions → Gérer → cochez Flux Mapper |

---

## 📜 Licence

Ce projet est distribué sous licence **GNU General Public License v2 or later (GPL-2.0-or-later)** —
la licence officielle de QGIS et de ses plugins.

Voir le fichier [LICENSE](LICENSE) pour les détails complets.

```
Copyright (C) 2025 KOTIN Ange H.P. <angekotin@gmail.com>
Ce programme est un logiciel libre, redistribuable et/ou modifiable
selon les termes de la GNU GPL v2 publiée par la Free Software Foundation.
```

---

## 📧 Contact

**KOTIN Ange H.P.**  
✉️ angekotin@gmail.com

---

*Flux Mapper — Visualisez vos réseaux géographiques avec QGIS.*
