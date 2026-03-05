"""
Flux Mapper - Boîte de dialogue principale
Version 2.0 - Flèches automatiques + gestion bidirectionnelle
"""

from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QComboBox, QPushButton, QGroupBox,
    QCheckBox, QDoubleSpinBox, QSpinBox, QMessageBox,
    QProgressBar, QTabWidget, QWidget, QFrame, QTextEdit
)
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.PyQt.QtGui import QColor, QFont

from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry,
    QgsPointXY, QgsField, QgsFields,
    QgsRendererCategory, QgsCategorizedSymbolRenderer,
    QgsSingleSymbolRenderer, QgsArrowSymbolLayer,
    QgsLineSymbol, QgsProperty, QgsSymbolLayer,
)

PALETTE = [
    "#2ca02c", "#ff7f0e", "#d62728", "#1f77b4",
    "#9467bd", "#8c564b", "#e377c2", "#17becf",
    "#bcbd22", "#7f7f7f",
]


class FluxMapperDialog(QDialog):

    def __init__(self, iface, parent=None):
        super().__init__(parent or iface.mainWindow())
        self.iface = iface
        self.setWindowTitle("Flux Mapper v2.0 — Carte de flux géographiques")
        self.setMinimumWidth(620)
        self.setMinimumHeight(730)
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        self.setLayout(main_layout)

        title = QLabel("🗺️  Flux Mapper")
        f = QFont(); f.setPointSize(14); f.setBold(True)
        title.setFont(f); title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)

        sub = QLabel("Génération de cartes de flux courbes — flèches automatiques & bidirectionnelles")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet("color:#555;margin-bottom:5px;")
        main_layout.addWidget(sub)

        sep = QFrame(); sep.setFrameShape(QFrame.HLine); sep.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(sep)

        tabs = QTabWidget()
        tabs.addTab(self._tab_donnees(), "📂  Données")
        tabs.addTab(self._tab_champs(),  "🔤  Champs")
        tabs.addTab(self._tab_style(),   "🎨  Style")
        tabs.addTab(self._tab_aide(),    "❓  Aide")
        main_layout.addWidget(tabs)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        btn_go = QPushButton("▶  Générer les flux")
        btn_go.setStyleSheet(
            "QPushButton{background:#2ca02c;color:white;font-weight:bold;"
            "padding:8px 20px;border-radius:4px;}"
            "QPushButton:hover{background:#1e7a1e;}")
        btn_go.clicked.connect(self.generer_flux)

        btn_close = QPushButton("✖  Fermer")
        btn_close.setStyleSheet(
            "QPushButton{background:#d62728;color:white;padding:8px 20px;border-radius:4px;}"
            "QPushButton:hover{background:#a01010;}")
        btn_close.clicked.connect(self.reject)

        btn_row.addWidget(btn_go); btn_row.addWidget(btn_close)
        main_layout.addLayout(btn_row)

        self.lbl_statut = QLabel("")
        self.lbl_statut.setAlignment(Qt.AlignCenter)
        self.lbl_statut.setStyleSheet("color:#2ca02c;font-style:italic;")
        main_layout.addWidget(self.lbl_statut)

    # ---- Onglet Données ----

    def _tab_donnees(self):
        w = QWidget(); lay = QVBoxLayout(); w.setLayout(lay)

        g1 = QGroupBox("📍  Couche de localités (points)")
        g1.setStyleSheet("QGroupBox{font-weight:bold;}")
        v1 = QVBoxLayout(); g1.setLayout(v1)
        info1 = QTextEdit(); info1.setReadOnly(True); info1.setMaximumHeight(60)
        info1.setStyleSheet("background:#f0f8ff;border:1px solid #aac;border-radius:3px;")
        info1.setHtml(
            "<b>Format :</b> Couche <b>Point</b> | "
            "<b>Champ obligatoire :</b> nom de chaque localité (texte) | "
            "<b>SCR :</b> WGS84 / EPSG:4326 recommandé")
        v1.addWidget(info1)
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Couche :"))
        self.combo_points = QComboBox(); row1.addWidget(self.combo_points)
        btn_r = QPushButton("🔄"); btn_r.setMaximumWidth(35)
        btn_r.clicked.connect(self._refresh_layers); row1.addWidget(btn_r)
        v1.addLayout(row1); lay.addWidget(g1)

        g2 = QGroupBox("📊  Couche de flux (table attributaire)")
        g2.setStyleSheet("QGroupBox{font-weight:bold;}")
        v2 = QVBoxLayout(); g2.setLayout(v2)
        info2 = QTextEdit(); info2.setReadOnly(True); info2.setMaximumHeight(115)
        info2.setStyleSheet("background:#fff8f0;border:1px solid #ca8;border-radius:3px;")
        info2.setHtml(
            "<b>Format :</b> Couche vecteur ou table | <b>SCR :</b> Non requis<br>"
            "<b>Champs obligatoires :</b> Nom départ · Nom arrivée · Nom relation · Score (nombre)<br>"
            "<b>Champ optionnel :</b> <b>Direction</b> → valeurs acceptées :<br>"
            "&nbsp;&nbsp;• <b><i>unidirectionnel</i></b> — une flèche A → B<br>"
            "&nbsp;&nbsp;• <b><i>bidirectionnel</i></b> — deux flèches A ⇄ B (décalées automatiquement)<br>"
            "<i>Si absent ou vide : unidirectionnel par défaut</i>")
        v2.addWidget(info2)
        row2 = QHBoxLayout(); row2.addWidget(QLabel("Couche :"))
        self.combo_flux = QComboBox(); row2.addWidget(self.combo_flux)
        v2.addLayout(row2); lay.addWidget(g2)

        g3 = QGroupBox("📤  Options de sortie")
        g3.setStyleSheet("QGroupBox{font-weight:bold;}")
        v3 = QVBoxLayout(); g3.setLayout(v3)
        self.chk_globale = QCheckBox("Créer une couche globale (tous les flux)")
        self.chk_globale.setChecked(True); v3.addWidget(self.chk_globale)
        self.chk_par_type = QCheckBox("Créer une couche par type de relation")
        self.chk_par_type.setChecked(True); v3.addWidget(self.chk_par_type)
        lay.addWidget(g3); lay.addStretch()

        self._refresh_layers()
        return w

    # ---- Onglet Champs ----

    def _tab_champs(self):
        w = QWidget(); lay = QVBoxLayout(); w.setLayout(lay)

        info = QLabel(
            "Associez chaque rôle au champ correspondant.\n"
            "Cliquez sur 🔄 après avoir sélectionné chaque couche dans l'onglet Données.")
        info.setWordWrap(True)
        info.setStyleSheet("background:#fffde7;padding:8px;border-radius:4px;")
        lay.addWidget(info)

        # Couche points
        gp = QGroupBox("📍 Couche de localités")
        gp.setStyleSheet("QGroupBox{font-weight:bold;}")
        gp_lay = QGridLayout(); gp.setLayout(gp_lay)
        gp_lay.addWidget(QLabel("Champ nom de la localité :"), 0, 0)
        self.combo_nom_pt = QComboBox(); gp_lay.addWidget(self.combo_nom_pt, 0, 1)
        btn_pt = QPushButton("🔄  Charger les champs")
        btn_pt.clicked.connect(self._refresh_point_fields)
        gp_lay.addWidget(btn_pt, 1, 0, 1, 2)
        lay.addWidget(gp)

        # Couche flux
        gf = QGroupBox("📊 Couche de flux")
        gf.setStyleSheet("QGroupBox{font-weight:bold;}")
        gf_lay = QGridLayout(); gf.setLayout(gf_lay)

        labels = [
            ("🏠  Nom localité départ :",   "combo_origine"),
            ("🏁  Nom localité arrivée :",  "combo_dest"),
            ("🔗  Nom de la relation :",    "combo_type"),
            ("📈  Score du flux :",         "combo_score"),
        ]
        for row, (lbl, attr) in enumerate(labels):
            gf_lay.addWidget(QLabel(lbl), row, 0)
            combo = QComboBox(); setattr(self, attr, combo)
            gf_lay.addWidget(combo, row, 1)

        # Direction optionnelle
        gf_lay.addWidget(QLabel("↔️  Direction (optionnel) :"), 4, 0)
        self.combo_direction = QComboBox()
        self.combo_direction.setToolTip(
            "Champ optionnel.\n"
            "Valeurs attendues dans la table :\n"
            "  • 'unidirectionnel'  → flèche simple A → B\n"
            "  • 'bidirectionnel'   → deux flèches A ⇄ B\n"
            "Si absent ou vide : unidirectionnel par défaut.")
        gf_lay.addWidget(self.combo_direction, 4, 1)

        self.chk_no_dir = QCheckBox("Pas de champ direction (tous unidirectionnels par défaut)")
        self.chk_no_dir.setChecked(True)
        self.chk_no_dir.stateChanged.connect(
            lambda s: self.combo_direction.setEnabled(not bool(s)))
        self.combo_direction.setEnabled(False)
        gf_lay.addWidget(self.chk_no_dir, 5, 0, 1, 2)

        btn_fl = QPushButton("🔄  Charger les champs")
        btn_fl.clicked.connect(self._refresh_fields)
        gf_lay.addWidget(btn_fl, 6, 0, 1, 2)
        lay.addWidget(gf); lay.addStretch()
        return w

    # ---- Onglet Style ----

    def _tab_style(self):
        w = QWidget(); lay = QVBoxLayout(); w.setLayout(lay)

        # Courbure
        gc = QGroupBox("〜  Courbure des flèches")
        gc.setStyleSheet("QGroupBox{font-weight:bold;}")
        gc_lay = QGridLayout(); gc.setLayout(gc_lay)

        gc_lay.addWidget(QLabel("Intensité de courbure :"), 0, 0)
        self.spin_courb = QDoubleSpinBox()
        self.spin_courb.setRange(-1.0, 1.0); self.spin_courb.setSingleStep(0.05)
        self.spin_courb.setValue(0.2)
        self.spin_courb.setToolTip("0=droit | 0.2=léger | 0.5=fort | négatif=autre côté")
        gc_lay.addWidget(self.spin_courb, 0, 1)

        gc_lay.addWidget(QLabel("Nombre de points :"), 1, 0)
        self.spin_npts = QSpinBox()
        self.spin_npts.setRange(10, 200); self.spin_npts.setValue(50)
        gc_lay.addWidget(self.spin_npts, 1, 1)

        gc_lay.addWidget(QLabel("Décalage bidirectionnel :"), 2, 0)
        self.spin_bi = QDoubleSpinBox()
        self.spin_bi.setRange(0.0, 1.0); self.spin_bi.setSingleStep(0.01)
        self.spin_bi.setValue(0.08)
        self.spin_bi.setToolTip(
            "Les deux flèches d'un flux bidirectionnel sont décalées\n"
            "de chaque côté de la ligne pour ne pas se superposer.\n"
            "0.08 = décalage modéré (recommandé)")
        gc_lay.addWidget(self.spin_bi, 2, 1)
        lay.addWidget(gc)

        # Épaisseur
        ge = QGroupBox("↔️  Épaisseur automatique (pilotée par Score)")
        ge.setStyleSheet("QGroupBox{font-weight:bold;}")
        ge_lay = QGridLayout(); ge.setLayout(ge_lay)

        note = QLabel("✅ Appliquée automatiquement — Score × multiplicateur")
        note.setStyleSheet("color:#2ca02c;font-style:italic;")
        ge_lay.addWidget(note, 0, 0, 1, 2)

        ge_lay.addWidget(QLabel("Multiplicateur :"), 1, 0)
        self.spin_mult = QDoubleSpinBox()
        self.spin_mult.setRange(0.1, 10.0); self.spin_mult.setSingleStep(0.1)
        self.spin_mult.setValue(0.8)
        ge_lay.addWidget(self.spin_mult, 1, 1)

        self.lbl_apercu = QLabel()
        self.lbl_apercu.setStyleSheet("color:#555;font-style:italic;padding-left:10px;")
        ge_lay.addWidget(self.lbl_apercu, 2, 0, 1, 2)
        self.spin_mult.valueChanged.connect(self._update_apercu)
        self._update_apercu()
        lay.addWidget(ge)

        # Tête de flèche
        gt = QGroupBox("➤  Tête de flèche")
        gt.setStyleSheet("QGroupBox{font-weight:bold;}")
        gt_lay = QGridLayout(); gt.setLayout(gt_lay)

        gt_lay.addWidget(QLabel("Longueur de la tête (mm) :"), 0, 0)
        self.spin_tete_l = QDoubleSpinBox()
        self.spin_tete_l.setRange(0.5, 20.0); self.spin_tete_l.setValue(3.0)
        gt_lay.addWidget(self.spin_tete_l, 0, 1)

        gt_lay.addWidget(QLabel("Largeur de la tête (mm) :"), 1, 0)
        self.spin_tete_w = QDoubleSpinBox()
        self.spin_tete_w.setRange(0.5, 20.0); self.spin_tete_w.setValue(2.0)
        gt_lay.addWidget(self.spin_tete_w, 1, 1)

        lay.addWidget(gt); lay.addStretch()
        return w

    # ---- Onglet Aide ----

    def _tab_aide(self):
        w = QWidget(); lay = QVBoxLayout(); w.setLayout(lay)
        aide = QTextEdit(); aide.setReadOnly(True)
        aide.setHtml("""
        <h2>📖 Guide — Flux Mapper v2.0</h2>
        <h3>🔧 Deux couches nécessaires</h3>
        <p><b>1. Couche de localités</b> : points avec un champ <b>nom</b></p>
        <p><b>2. Couche de flux</b> : table avec ces champs :</p>
        <table border="1" cellpadding="4">
          <tr style="background:#eee">
            <th>Champ</th><th>Type</th><th>Requis</th><th>Description</th>
          </tr>
          <tr><td>Nom départ</td><td>Texte</td><td>✅</td>
              <td>Nom exact de la localité de départ</td></tr>
          <tr><td>Nom arrivée</td><td>Texte</td><td>✅</td>
              <td>Nom exact de la localité d'arrivée</td></tr>
          <tr><td>Nom relation</td><td>Texte</td><td>✅</td>
              <td>Ex : Production, Commerce, Migration</td></tr>
          <tr><td>Score</td><td>Nombre</td><td>✅</td>
              <td>Intensité — contrôle l'épaisseur de la flèche</td></tr>
          <tr><td><b>Direction</b></td><td>Texte</td><td>⬜ Optionnel</td>
              <td><b>unidirectionnel</b> ou <b>bidirectionnel</b></td></tr>
        </table>

        <h3>↔️ Flux bidirectionnels</h3>
        <ul>
          <li>Mettez <b>bidirectionnel</b> dans le champ Direction</li>
          <li>Le plugin crée automatiquement <b>deux flèches décalées</b> (aller + retour)</li>
          <li>Ajustez le <b>décalage bidirectionnel</b> dans l'onglet Style si les flèches se chevauchent</li>
        </ul>

        <h3>🎨 Flèches 100% automatiques</h3>
        <ul>
          <li><b>Épaisseur</b> : proportionnelle au Score (Score × multiplicateur)</li>
          <li><b>Couleur</b> : une couleur par type de relation, appliquée automatiquement</li>
          <li><b>Courbure</b> : paramétrable dans l'onglet Style</li>
        </ul>

        <h3>📋 Étapes rapides</h3>
        <ol>
          <li><b>Données</b> : sélectionner les 2 couches</li>
          <li><b>Champs</b> : cliquer 🔄 et associer les champs</li>
          <li><b>Style</b> : ajuster si besoin</li>
          <li>Cliquer <b>▶ Générer</b></li>
        </ol>

        <h3>⚠️ Important</h3>
        <p>Les noms de localités doivent être <b>identiques</b> dans les deux couches
        (majuscules, accents, espaces).</p>
        """)
        lay.addWidget(aide)
        return w

    # ------------------------------------------------------------------
    # UTILITAIRES
    # ------------------------------------------------------------------

    def _update_apercu(self):
        m = self.spin_mult.value()
        self.lbl_apercu.setText(
            "  |  ".join(f"Score {s} → {s*m:.1f} mm" for s in [1, 2, 3, 4, 5]))

    def _refresh_layers(self):
        self.combo_points.clear(); self.combo_flux.clear()
        for layer in QgsProject.instance().mapLayers().values():
            self.combo_points.addItem(layer.name(), layer.id())
            self.combo_flux.addItem(layer.name(), layer.id())

    def _get_layer(self, combo):
        lid = combo.currentData()
        return QgsProject.instance().mapLayer(lid) if lid else None

    def _refresh_point_fields(self):
        layer = self._get_layer(self.combo_points)
        if not layer:
            QMessageBox.warning(self, "Attention", "Sélectionnez d'abord la couche de points."); return
        fields = [f.name() for f in layer.fields()]
        self.combo_nom_pt.clear(); self.combo_nom_pt.addItems(fields)
        lf = [f.lower() for f in fields]
        for kw in ["name", "nom", "localite", "ville", "label"]:
            for i, f in enumerate(lf):
                if kw in f: self.combo_nom_pt.setCurrentIndex(i); break
        self.lbl_statut.setText(f"✅ Champs points chargés")

    def _refresh_fields(self):
        layer = self._get_layer(self.combo_flux)
        if not layer:
            QMessageBox.warning(self, "Attention", "Sélectionnez d'abord la couche de flux."); return
        fields = [f.name() for f in layer.fields()]
        self.combo_direction.clear()
        self.combo_direction.addItem("— aucun —", None)
        for combo in [self.combo_origine, self.combo_dest, self.combo_type,
                      self.combo_score, self.combo_direction]:
            # Garder l'option "aucun" pour direction et rajouter les champs
            if combo != self.combo_direction:
                combo.clear()
            combo.addItems(fields)
        lf = [f.lower() for f in fields]
        hints = {
            self.combo_origine:    ["origine", "depart", "from", "source"],
            self.combo_dest:       ["destination", "arrivee", "to", "dest"],
            self.combo_type:       ["type", "relation", "categorie"],
            self.combo_score:      ["score", "intensite", "poids", "weight"],
            self.combo_direction:  ["direction", "sens", "bidir"],
        }
        for combo, kws in hints.items():
            for kw in kws:
                for i, f in enumerate(lf):
                    if kw in f:
                        offset = 1 if combo == self.combo_direction else 0
                        combo.setCurrentIndex(i + offset); break
        self.lbl_statut.setText(f"✅ {len(fields)} champs chargés")

    # ------------------------------------------------------------------
    # COURBE DE BÉZIER
    # ------------------------------------------------------------------

    def bezier(self, x1, y1, x2, y2, courbure):
        nb  = self.spin_npts.value()
        mx  = (x1+x2)/2; my = (y1+y2)/2
        dx  = x2-x1;     dy = y2-y1
        cx  = mx - courbure*dy
        cy  = my + courbure*dx
        pts = []
        for i in range(nb+1):
            t  = i/nb
            bx = (1-t)**2*x1 + 2*(1-t)*t*cx + t**2*x2
            by = (1-t)**2*y1 + 2*(1-t)*t*cy + t**2*y2
            pts.append(QgsPointXY(bx, by))
        return pts

    # ------------------------------------------------------------------
    # GÉNÉRATION
    # ------------------------------------------------------------------

    def generer_flux(self):
        layer_pts  = self._get_layer(self.combo_points)
        layer_flux = self._get_layer(self.combo_flux)
        if not layer_pts or not layer_flux:
            QMessageBox.critical(self, "Erreur", "Veuillez sélectionner les deux couches."); return

        ch_nom   = self.combo_nom_pt.currentText()
        ch_ori   = self.combo_origine.currentText()
        ch_dest  = self.combo_dest.currentText()
        ch_type  = self.combo_type.currentText()
        ch_score = self.combo_score.currentText()
        use_dir  = not self.chk_no_dir.isChecked()
        ch_dir   = self.combo_direction.currentText() if use_dir else None

        if not all([ch_nom, ch_ori, ch_dest, ch_type, ch_score]):
            QMessageBox.critical(self, "Erreur", "Définissez tous les champs obligatoires."); return

        # Dictionnaire des coordonnées
        coords = {}
        for feat in layer_pts.getFeatures():
            nom  = str(feat[ch_nom]).strip()
            geom = feat.geometry()
            if geom and not geom.isNull():
                pt = geom.asPoint()
                coords[nom] = (pt.x(), pt.y())

        if not coords:
            QMessageBox.critical(self, "Erreur", "Aucune coordonnée trouvée dans la couche points."); return

        # Lecture des flux
        raw_flux = []
        for feat in layer_flux.getFeatures():
            ori   = str(feat[ch_ori]).strip()
            dest  = str(feat[ch_dest]).strip()
            typ   = str(feat[ch_type]).strip()
            try:   score = float(feat[ch_score])
            except: score = 1.0
            direc = "unidirectionnel"
            if use_dir and ch_dir and ch_dir != "— aucun —":
                try:
                    v = str(feat[ch_dir]).strip().lower()
                    if "bi" in v: direc = "bidirectionnel"
                except: pass
            raw_flux.append((ori, dest, typ, score, direc))

        if not raw_flux:
            QMessageBox.critical(self, "Erreur", "Aucun flux trouvé."); return

        self.progress_bar.setVisible(True)
        self.progress_bar.setMaximum(len(raw_flux))

        mult      = self.spin_mult.value()
        c_base    = self.spin_courb.value()
        c_bi      = self.spin_bi.value()
        feats_all = []
        feats_typ = {}
        manquants = []
        fid       = 0

        def make_feat(ori, dest, typ, score, direc, courbure):
            nonlocal fid
            if ori not in coords:
                manquants.append(f"Origine inconnue : '{ori}'"); return
            if dest not in coords:
                manquants.append(f"Destination inconnue : '{dest}'"); return
            x1,y1 = coords[ori]; x2,y2 = coords[dest]
            pts = self.bezier(x1, y1, x2, y2, courbure)
            feat = QgsFeature(); fid += 1
            feat.setGeometry(QgsGeometry.fromPolylineXY(pts))
            feat.setAttributes([fid, ori, dest, typ, score, round(score*mult,2), direc])
            feats_all.append(feat)
            feats_typ.setdefault(typ, []).append(feat)

        for i, (ori, dest, typ, score, direc) in enumerate(raw_flux):
            self.progress_bar.setValue(i+1)
            if direc == "bidirectionnel":
                # Aller : décalé vers la droite
                make_feat(ori, dest, typ, score, "bidirectionnel_aller",  c_base + c_bi)
                # Retour : décalé vers la gauche (même côté donc même courbure,
                # mais départ/arrivée inversés → la courbe part de l'autre côté)
                make_feat(dest, ori, typ, score, "bidirectionnel_retour", c_base + c_bi)
            else:
                make_feat(ori, dest, typ, score, "unidirectionnel", c_base)

        # Supprimer anciennes couches
        noms = ["Flux_Global"] + [f"Flux_{t.replace(' ','_')}" for t in feats_typ]
        for lyr in list(QgsProject.instance().mapLayers().values()):
            if lyr.name() in noms:
                QgsProject.instance().removeMapLayer(lyr)

        def fields_def():
            flds = QgsFields()
            for nm, tp in [("id_flux", QVariant.Int), ("Origine", QVariant.String),
                           ("Destination", QVariant.String), ("Type_flux", QVariant.String),
                           ("Score_flux", QVariant.Double), ("Epaisseur_mm", QVariant.Double),
                           ("Direction", QVariant.String)]:
                flds.append(QgsField(nm, tp))
            return flds

        def new_layer(nom, feats, couleur=None):
            vl = QgsVectorLayer("LineString?crs=EPSG:4326", nom, "memory")
            pr = vl.dataProvider()
            pr.addAttributes(fields_def()); vl.updateFields()
            pr.addFeatures(feats); vl.updateExtents()
            self._style(vl, couleur=couleur, categorise=(couleur is None))
            return vl

        created = []
        if self.chk_globale.isChecked() and feats_all:
            vl = new_layer("Flux_Global", feats_all)
            QgsProject.instance().addMapLayer(vl)
            created.append(f"Flux_Global ({len(feats_all)} entités)")

        if self.chk_par_type.isChecked():
            for idx, (typ, feats) in enumerate(feats_typ.items()):
                nom = f"Flux_{typ.replace(' ','_')}"
                vl  = new_layer(nom, feats, couleur=PALETTE[idx % len(PALETTE)])
                QgsProject.instance().addMapLayer(vl)
                created.append(f"{nom} ({len(feats)} entités)")

        self.progress_bar.setVisible(False)
        msg = f"✅ {len(created)} couche(s) créée(s) :\n" + "\n".join(f"  • {c}" for c in created)
        if manquants:
            u = list(set(manquants))[:10]
            msg += "\n\n⚠️ Localités non trouvées :\n" + "\n".join(f"  • {m}" for m in u)
        QMessageBox.information(self, "Terminé", msg)
        self.lbl_statut.setText(f"✅ Terminé — {len(feats_all)} flux générés")

    # ------------------------------------------------------------------
    # STYLE FLÈCHES AUTOMATIQUE
    # ------------------------------------------------------------------

    def _style(self, layer, couleur=None, categorise=False):
        mult = self.spin_mult.value()
        tl   = self.spin_tete_l.value()
        tw   = self.spin_tete_w.value()

        expr = (
            f'CASE '
            f'WHEN "Score_flux"<=1 THEN {1*mult:.2f} '
            f'WHEN "Score_flux"<=2 THEN {2*mult:.2f} '
            f'WHEN "Score_flux"<=3 THEN {3*mult:.2f} '
            f'WHEN "Score_flux"<=4 THEN {4*mult:.2f} '
            f'ELSE {5*mult:.2f} END'
        )

        def make_symbol(hex_col):
            sym = QgsLineSymbol()
            sym.deleteSymbolLayer(0)
            arrow = QgsArrowSymbolLayer()
            arrow.setArrowWidth(1.0)
            arrow.setArrowStartWidth(0.3)
            arrow.setHeadLength(tl)
            arrow.setHeadThickness(tw)
            arrow.setIsCurved(True)
            arrow.setIsRepeated(False)
            sub = arrow.subSymbol()
            if sub and hex_col:
                sub.setColor(QColor(hex_col))
            arrow.setDataDefinedProperty(
                QgsSymbolLayer.PropertyArrowWidth,
                QgsProperty.fromExpression(expr))
            sym.appendSymbolLayer(arrow)
            return sym

        if categorise:
            types = sorted(set(str(f["Type_flux"]) for f in layer.getFeatures()))
            cats  = [QgsRendererCategory(t, make_symbol(PALETTE[i % len(PALETTE)]), t)
                     for i, t in enumerate(types)]
            layer.setRenderer(QgsCategorizedSymbolRenderer("Type_flux", cats))
        else:
            layer.setRenderer(QgsSingleSymbolRenderer(make_symbol(couleur)))

        layer.triggerRepaint()
