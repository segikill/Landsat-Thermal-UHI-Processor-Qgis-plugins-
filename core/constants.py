# -*- coding: utf-8 -*-
"""Shared constants for Landsat thermal processing."""

BAND10_WAVELENGTH_UM = 10.895
RHO = 14387.77

NDVI_SOIL = 0.2
NDVI_VEG = 0.5
EMIS_SOIL = 0.979
EMIS_VEG = 0.986

NODATA_FILL = -9999.0

UTFVI_CLASSES = [
    (float('-inf'), 0.000, 'No UHI / Нет UHI', '#2166ac'),
    (0.000, 0.005, 'Weak / Слабый', '#74add1'),
    (0.005, 0.010, 'Moderate / Средний', '#ffffbf'),
    (0.010, 0.015, 'Strong / Сильный', '#fdae61'),
    (0.015, 0.020, 'Intense / Интенсивный', '#f46d43'),
    (0.020, float('inf'), 'Extreme / Экстремальный', '#a50026'),
]

CMAP_LST = [
    (0.00, '#0d0887'), (0.15, '#5302a3'), (0.30, '#8b0aa5'),
    (0.45, '#b83289'), (0.60, '#db5c68'), (0.75, '#f48849'),
    (0.88, '#febc2a'), (1.00, '#f0f921'),
]
CMAP_BT = [
    (0.00, '#000000'), (0.33, '#ff0000'), (0.66, '#ffff00'), (1.00, '#ffffff'),
]
CMAP_UHI_DIFF = [
    (0.00, '#2166ac'), (0.25, '#92c5de'), (0.50, '#f7f7f7'),
    (0.75, '#f4a582'), (1.00, '#b2182b'),
]

CMAP_NDVI = [
    (0.00, "#8c510a"), (0.20, "#d8b365"), (0.40, "#f6e8c3"),
    (0.60, "#c7eae5"), (0.80, "#5ab4ac"), (1.00, "#01665e"),
]
CMAP_NDBI = [
    (0.00, "#2166ac"), (0.25, "#67a9cf"), (0.50, "#f7f7f7"),
    (0.75, "#ef8a62"), (1.00, "#b2182b"),
]
