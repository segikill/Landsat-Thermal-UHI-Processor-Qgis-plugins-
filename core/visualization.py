# -*- coding: utf-8 -*-
"""QGIS raster styling helpers."""

from qgis.core import (
    QgsRasterLayer, QgsProject, QgsColorRampShader, QgsRasterShader,
    QgsSingleBandPseudoColorRenderer, QgsRasterBandStats, QgsRasterTransparency,
    QgsContrastEnhancement
)
from qgis.PyQt.QtGui import QColor
from .constants import NODATA_FILL


def _safe_nodata_transparency(layer, nodata_val, renderer):
    try:
        tr_pixel = QgsRasterTransparency.TransparentSingleValuePixel()
        tr_pixel.min = float(nodata_val)
        tr_pixel.max = float(nodata_val)
        tr_pixel.percentTransparent = 100.0
        tr = QgsRasterTransparency()
        tr.setTransparentSingleValuePixelList([tr_pixel])
        renderer.setRasterTransparency(tr)
    except Exception:
        pass
    try:
        ce = QgsContrastEnhancement(layer.dataProvider().dataType(1))
        ce.setContrastEnhancementAlgorithm(QgsContrastEnhancement.NoEnhancement)
        renderer.setContrastEnhancement(ce)
    except Exception:
        pass


def apply_continuous_colormap(layer: QgsRasterLayer, cmap: list, label: str, feedback=None, v_min_data=None, v_max_data=None, sigma=3.0):
    provider = layer.dataProvider()
    if v_min_data is None or v_max_data is None:
        stats = provider.bandStatistics(1, QgsRasterBandStats.Mean | QgsRasterBandStats.StdDev | QgsRasterBandStats.Min | QgsRasterBandStats.Max)
        mean, std = stats.mean, stats.stdDev
        dmin, dmax = stats.minimumValue, stats.maximumValue
        if std < 0.5 or (dmax - dmin) < 2.0:
            v_min, v_max = dmin, dmax
        else:
            v_min = max(dmin, mean - sigma * std)
            v_max = min(dmax, mean + sigma * std)
    else:
        v_min, v_max = float(v_min_data), float(v_max_data)
    cr = QgsColorRampShader()
    cr.setColorRampType(QgsColorRampShader.Interpolated)
    cr.setClip(False)
    span = v_max - v_min if v_max != v_min else 1.0
    items = [QgsColorRampShader.ColorRampItem(v_min + f * span, QColor(c), f'{v_min + f * span:.3f}') for f, c in cmap]
    cr.setColorRampItemList(items)
    shader = QgsRasterShader(); shader.setRasterShaderFunction(cr)
    renderer = QgsSingleBandPseudoColorRenderer(provider, 1, shader)
    renderer.setClassificationMin(v_min); renderer.setClassificationMax(v_max)
    _safe_nodata_transparency(layer, NODATA_FILL, renderer)
    layer.setRenderer(renderer); layer.triggerRepaint()


def apply_utfvi_colormap(layer: QgsRasterLayer, feedback=None):
    provider = layer.dataProvider()
    cr = QgsColorRampShader(); cr.setColorRampType(QgsColorRampShader.Interpolated); cr.setClip(False)
    mids = [
        (-0.025, '#2166ac', 'No UHI / Нет UHI (< 0)'), (0.000, '#74add1', 'No UHI / Нет UHI (= 0)'),
        (0.003, '#ffffbf', 'Weak / Слабый'), (0.008, '#fdae61', 'Moderate / Средний'),
        (0.013, '#f46d43', 'Strong / Сильный'), (0.018, '#d73027', 'Intense / Интенсивный'), (0.030, '#a50026', 'Extreme / Экстремальный'),
    ]
    cr.setColorRampItemList([QgsColorRampShader.ColorRampItem(v, QColor(c), lbl) for v, c, lbl in mids])
    shader = QgsRasterShader(); shader.setRasterShaderFunction(cr)
    renderer = QgsSingleBandPseudoColorRenderer(provider, 1, shader)
    renderer.setClassificationMin(-0.025); renderer.setClassificationMax(0.03)
    _safe_nodata_transparency(layer, NODATA_FILL, renderer)
    layer.setRenderer(renderer); layer.triggerRepaint()


def apply_binary_mask_colormap(layer: QgsRasterLayer, label: str, true_color: QColor, feedback=None, false_transparent: bool = True):
    provider = layer.dataProvider()
    shader = QgsRasterShader()
    ramp = QgsColorRampShader()
    ramp.setColorRampType(QgsColorRampShader.Discrete)
    items = []
    if false_transparent:
        items.append(QgsColorRampShader.ColorRampItem(0, QColor(0, 0, 0, 0), 'No'))
    else:
        items.append(QgsColorRampShader.ColorRampItem(0, QColor(240, 240, 240), 'No'))
    items.append(QgsColorRampShader.ColorRampItem(1, true_color, label))
    ramp.setColorRampItemList(items)
    shader.setRasterShaderFunction(ramp)
    renderer = QgsSingleBandPseudoColorRenderer(provider, 1, shader)
    renderer.setClassificationMin(0.0); renderer.setClassificationMax(1.0)
    layer.setRenderer(renderer)
    layer.triggerRepaint()


def apply_valid_mask_colormap(layer: QgsRasterLayer, feedback=None):
    apply_binary_mask_colormap(layer, 'Valid', QColor(60, 180, 75, 220), feedback=feedback)


def apply_urban_mask_colormap(layer: QgsRasterLayer, feedback=None):
    apply_binary_mask_colormap(layer, 'Urban', QColor(230, 80, 80, 220), feedback=feedback)


def apply_rural_mask_colormap(layer: QgsRasterLayer, feedback=None):
    apply_binary_mask_colormap(layer, 'Rural', QColor(70, 130, 255, 220), feedback=feedback)


def add_layer(path: str, name: str, feedback, style_fn=None, style_args=None):
    layer = QgsRasterLayer(path, name)
    if not layer.isValid():
        feedback.pushWarning(f'Could not load layer / Не удалось загрузить слой: {name}')
        return None
    if style_fn is not None:
        try:
            style_args = style_args or {}
            style_fn(layer, feedback=feedback, **style_args)
        except Exception as exc:
            feedback.pushWarning(f'Style was not applied / Стиль не применен для {name}: {exc}')
    QgsProject.instance().addMapLayer(layer)
    return layer
