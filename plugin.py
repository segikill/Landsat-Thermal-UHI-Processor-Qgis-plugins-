# -*- coding: utf-8 -*-
"""
Landsat Thermal & UHI Processor — QGIS Plugin.
Registers the Processing algorithm, adds a toolbar button,
and adds an item to the Raster menu.

Landsat Thermal & UHI Processor — плагин QGIS.
Регистрирует алгоритм в панели Processing, добавляет кнопку
на панель инструментов и пункт меню Растр.
"""

import os
from qgis.core import QgsApplication
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.PyQt.QtGui import QIcon
import processing

from .provider import LandsatThermalProvider

ALGO_ID = 'landsat_tools:landsat_thermal_uhi_processor'


class LandsatThermalPlugin:
    def __init__(self, iface):
        self.iface    = iface
        self.provider = None
        self.action   = None
        self.toolbar  = None

    # ----------------------------------------------------------------
    def initGui(self):
        # 1. Register the Processing provider / Регистрируем провайдер Processing
        self.provider = LandsatThermalProvider()
        QgsApplication.processingRegistry().addProvider(self.provider)

        # 2. Icon / Иконка
        icon_path = os.path.join(os.path.dirname(__file__), 'icons', 'icon.png')
        icon = QIcon(icon_path) if os.path.isfile(icon_path) else QIcon()

        # 3. Shared QAction for the toolbar button and menu item / Общий QAction для кнопки и меню
        self.action = QAction(icon, 'Landsat Thermal && UHI…', self.iface.mainWindow())
        self.action.setToolTip(
            'Landsat 8/9 — Brightness Temperature / LST / Urban Heat Island'
        )
        self.action.triggered.connect(self._run)

        # 4. Dedicated plugin toolbar / Отдельная панель инструментов плагина
        #    Appears in View → Toolbars → Landsat Tools / Появится в View → Toolbars → Landsat Tools
        self.toolbar = QToolBar('Landsat Tools', self.iface.mainWindow())
        self.toolbar.setObjectName('LandsatToolsToolbar')
        self.iface.mainWindow().addToolBar(self.toolbar)
        self.toolbar.addAction(self.action)

        # 5. Raster menu item / Пункт в меню Растр
        self.iface.addPluginToRasterMenu('Landsat Tools', self.action)

    # ----------------------------------------------------------------
    def unload(self):
        # Remove menu item / Убираем пункт меню
        self.iface.removePluginRasterMenu('Landsat Tools', self.action)

        # Remove toolbar / Убираем панель инструментов
        if self.toolbar is not None:
            self.iface.mainWindow().removeToolBar(self.toolbar)
            self.toolbar.deleteLater()
            self.toolbar = None

        # Remove Processing provider / Убираем провайдер Processing
        if self.provider:
            QgsApplication.processingRegistry().removeProvider(self.provider)
            self.provider = None

    # ----------------------------------------------------------------
    def _run(self):
        """Open the standard Processing dialog for the algorithm. / Открывает стандартный диалог Processing для алгоритма."""
        processing.execAlgorithmDialog(ALGO_ID)

