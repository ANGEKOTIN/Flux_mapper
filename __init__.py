# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Flux Mapper
 ----------
 Plugin QGIS pour la création de cartes de flux géographiques courbes.

 Auteur  : KOTIN Ange H.P.
 Contact : angekotin@gmail.com
 Version : 2.0.0
 Licence : GPL v2
***************************************************************************/
"""


def classFactory(iface):
    """
    Point d'entrée obligatoire appelé par QGIS au chargement du plugin.

    :param iface: QgisInterface — interface principale de QGIS,
                  donne accès à la carte, aux menus, aux barres d'outils.
    """
    from .flux_mapper import FluxMapper
    return FluxMapper(iface)
