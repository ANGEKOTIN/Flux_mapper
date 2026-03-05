# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Flux Mapper — Classe principale
 --------------------------------
 Gère le cycle de vie du plugin dans QGIS :
 initialisation, ajout du bouton/menu, ouverture de la boîte de dialogue.

 Auteur  : KOTIN Ange H.P.
 Contact : angekotin@gmail.com
 Version : 2.0.0
 Licence : GPL v2
***************************************************************************/
"""

import os
from qgis.PyQt.QtWidgets import QAction, QMessageBox
from qgis.PyQt.QtGui import QIcon

from .flux_mapper_dialog import FluxMapperDialog


class FluxMapper:
    """Classe principale du plugin Flux Mapper."""

    def __init__(self, iface):
        """
        Constructeur.

        :param iface: QgisInterface fourni par QGIS au démarrage du plugin.
        """
        self.iface      = iface
        self.plugin_dir = os.path.dirname(__file__)
        self.actions    = []
        self.menu       = "Flux Mapper"
        self.dlg        = None

    # ------------------------------------------------------------------

    def initGui(self):
        """
        Appelé par QGIS quand le plugin est activé.
        Ajoute le bouton dans la barre d'outils et dans le menu Extensions.
        """
        icon_path = os.path.join(self.plugin_dir, "icons", "icon.png")
        action = QAction(QIcon(icon_path), "Flux Mapper — Carte de flux", self.iface.mainWindow())
        action.setToolTip(
            "Flux Mapper\n"
            "Générer des cartes de flux courbes entre localités.\n"
            "Auteur : KOTIN Ange H.P. — angekotin@gmail.com"
        )
        action.triggered.connect(self.run)

        self.iface.addToolBarIcon(action)
        self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)

    # ------------------------------------------------------------------

    def unload(self):
        """
        Appelé par QGIS quand le plugin est désactivé ou désinstallé.
        Retire le bouton de la barre d'outils et du menu.
        """
        for action in self.actions:
            self.iface.removePluginMenu(self.menu, action)
            self.iface.removeToolBarIcon(action)
        self.actions.clear()

    # ------------------------------------------------------------------

    def run(self):
        """Ouvre la boîte de dialogue principale du plugin."""
        self.dlg = FluxMapperDialog(self.iface)
        self.dlg.show()
        self.dlg.exec_()
