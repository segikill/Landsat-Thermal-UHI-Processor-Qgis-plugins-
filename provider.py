# -*- coding: utf-8 -*-
"""
Processing Provider — registers LandsatThermalProcessor
in the “Landsat Tools” group of the Processing Toolbox.

Processing Provider — регистрирует LandsatThermalProcessor
в группе «Landsat Tools» панели Processing.
"""

import os
from qgis.core import QgsProcessingProvider
from qgis.PyQt.QtGui import QIcon

from .landsat_thermal_processor import LandsatThermalProcessor


class LandsatThermalProvider(QgsProcessingProvider):

    def loadAlgorithms(self):
        self.addAlgorithm(LandsatThermalProcessor())

    def id(self):
        return 'landsat_tools'

    def name(self):
        return 'Landsat Tools'

    def longName(self):
        return 'Landsat Thermal & UHI Tools'

    def icon(self):
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
        if os.path.isfile(icon_path):
            return QIcon(icon_path)
        return super().icon()
