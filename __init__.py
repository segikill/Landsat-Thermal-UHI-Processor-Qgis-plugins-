# -*- coding: utf-8 -*-
"""
Landsat Thermal & UHI Processor — QGIS Plugin
"""

def classFactory(iface):
    from .plugin import LandsatThermalPlugin
    return LandsatThermalPlugin(iface)
