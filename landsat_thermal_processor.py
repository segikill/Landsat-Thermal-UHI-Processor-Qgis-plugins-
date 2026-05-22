# -*- coding: utf-8 -*-
"""QGIS Processing algorithm for Landsat BT/LST/UHI."""

import os
import numpy as np

from qgis.core import (
    QgsProcessingAlgorithm,
    QgsProcessingParameterFile,
    QgsProcessingParameterFolderDestination,
    QgsProcessingParameterEnum,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterNumber,
    QgsProcessingParameterString,
)
from osgeo import gdalconst

from .core.constants import CMAP_BT, CMAP_LST, CMAP_UHI_DIFF, CMAP_NDVI, CMAP_NDBI
from .core.io import (
    find_scene_files, format_file_check, parse_mtl, read_band, read_band_aligned,
    write_tiff, write_csv_stats, build_path,
)
from .core.masks import decode_qa_pixel, build_valid_mask, compute_zone_masks
from .core.physics import compute_bt, compute_ndvi, compute_ndbi, compute_emissivity, compute_lst
from .core.uhi import compute_utfvi, compute_uhi_diff, compute_uhi_stats
from .core.validation import (
    validate_output_dir, validate_scene_files, validate_required_bands_for_mode,
    validate_metadata_values, validate_array_shapes,
)
from .core.visualization import (
    add_layer, apply_continuous_colormap, apply_utfvi_colormap,
    apply_valid_mask_colormap, apply_urban_mask_colormap, apply_rural_mask_colormap,
)


class LandsatThermalProcessor(QgsProcessingAlgorithm):
    SCENE_DIR = 'SCENE_DIR'
    PROC_MODE = 'PROC_MODE'
    APPLY_MASK = 'APPLY_MASK'
    NDVI_RURAL_THR = 'NDVI_RURAL_THR'
    EXPORT_CSV = 'EXPORT_CSV'
    OUT_DIR = 'OUT_DIR'
    CUSTOM_PREFIX = 'CUSTOM_PREFIX'
    EXPORT_DIAGNOSTICS = 'EXPORT_DIAGNOSTICS'

    MODES = [
        'BT — Brightness Temperature / Яркостная температура (Band 10)',
        'LST — Land Surface Temperature / Температура поверхности (Band 4+5+10)',
        'LST + UHI — Urban Heat Island / Тепловой остров (UTFVI + diff + CSV)',
    ]

    def initAlgorithm(self, config=None):
        self.addParameter(QgsProcessingParameterFile(self.SCENE_DIR, 'Landsat scene folder / Папка снимка Landsat', behavior=QgsProcessingParameterFile.Folder))
        self.addParameter(QgsProcessingParameterEnum(self.PROC_MODE, 'Processing mode / Тип обработки', options=self.MODES, defaultValue=2))
        self.addParameter(QgsProcessingParameterBoolean(self.APPLY_MASK, 'QA_PIXEL cloud mask / Облачная маска QA_PIXEL', defaultValue=True, optional=True))
        self.addParameter(QgsProcessingParameterNumber(self.NDVI_RURAL_THR, 'Rural NDVI threshold / NDVI-порог сельской зоны', type=QgsProcessingParameterNumber.Double, defaultValue=0.35, minValue=0.1, maxValue=0.7, optional=True))
        self.addParameter(QgsProcessingParameterBoolean(self.EXPORT_CSV, 'Export statistics to CSV / Экспорт статистики в CSV', defaultValue=True, optional=True))
        self.addParameter(QgsProcessingParameterBoolean(self.EXPORT_DIAGNOSTICS, 'Export diagnostic masks / Экспорт диагностических масок', defaultValue=True, optional=True))
        self.addParameter(QgsProcessingParameterFolderDestination(self.OUT_DIR, 'Output folder / Папка для сохранения результатов'))
        self.addParameter(QgsProcessingParameterString(self.CUSTOM_PREFIX, 'File name prefix / Префикс имён файлов', defaultValue='', optional=True))

    def processAlgorithm(self, parameters, context, feedback):
        scene_dir = self.parameterAsFile(parameters, self.SCENE_DIR, context)
        mode_idx = self.parameterAsEnum(parameters, self.PROC_MODE, context)
        apply_mask = self.parameterAsBool(parameters, self.APPLY_MASK, context)
        ndvi_rural = self.parameterAsDouble(parameters, self.NDVI_RURAL_THR, context)
        export_csv = self.parameterAsBool(parameters, self.EXPORT_CSV, context)
        export_diag = self.parameterAsBool(parameters, self.EXPORT_DIAGNOSTICS, context)
        out_dir = validate_output_dir(self.parameterAsString(parameters, self.OUT_DIR, context))
        custom_prefix = self.parameterAsString(parameters, self.CUSTOM_PREFIX, context).strip()

        mode = {0: 'BT', 1: 'LST', 2: 'UHI'}[mode_idx]
        feedback.pushInfo(f'Mode / Режим: {mode}')

        files = find_scene_files(scene_dir)
        feedback.pushInfo(format_file_check(files, mode))
        validate_scene_files(files)
        validate_required_bands_for_mode(files, mode)

        mtl = parse_mtl(files['mtl'])
        validate_metadata_values(mtl)

        b10, nd10, geo, proj = read_band(files['b10'])
        base_invalid = ~build_valid_mask(b10, nd10)
        bt = compute_bt(b10, base_invalid, mtl)
        bt_stats = self._stats(bt)

        prefix = custom_prefix or files.get('scene_id') or 'landsat'
        results = {}

        bt_path = build_path(prefix, 'BT', out_dir)
        write_tiff(bt_path, bt, geo, proj)
        results['BT'] = bt_path
        add_layer(bt_path, f'{prefix}_BT', feedback, apply_continuous_colormap, {'cmap': CMAP_BT, 'label': 'BT', 'v_min_data': bt_stats.get('min'), 'v_max_data': bt_stats.get('max')})

        if mode == 'BT':
            return results

        b4, nd4, _, _, info4 = read_band_aligned(files['b4'], files['b10'], resample_alg=gdalconst.GRA_Bilinear)
        b5, nd5, _, _, info5 = read_band_aligned(files['b5'], files['b10'], resample_alg=gdalconst.GRA_Bilinear)
        b6, nd6, _, _, info6 = read_band_aligned(files['b6'], files['b10'], resample_alg=gdalconst.GRA_Bilinear)
        validate_array_shapes({'b10': b10, 'b4': b4, 'b5': b5, 'b6': b6})
        if info4: feedback.pushInfo(f'Alignment / Выравнивание B4: {info4}')
        if info5: feedback.pushInfo(f'Alignment / Выравнивание B5: {info5}')
        if info6: feedback.pushInfo(f'Alignment / Выравнивание B6: {info6}')

        qa_valid = None
        qa_invalid_px = 0
        if apply_mask and files.get('qa'):
            qa, _, _, _, infoqa = read_band_aligned(files['qa'], files['b10'], resample_alg=gdalconst.GRA_NearestNeighbour)
            qa_valid = decode_qa_pixel(qa)
            qa_invalid_px = int((~qa_valid).sum())
            if infoqa:
                feedback.pushInfo(f'Alignment / Выравнивание QA: {infoqa}')

        valid = build_valid_mask(b10, nd10, b4, nd4, b5, nd5, b6, nd6, qa_valid)
        invalid = ~valid
        ndvi = np.where(valid, compute_ndvi(b4, b5), np.nan)
        ndbi = np.where(valid, compute_ndbi(b5, b6), np.nan)
        emis = compute_emissivity(ndvi)
        lst = compute_lst(bt, emis)
        lst[invalid] = np.nan
        lst_stats = self._stats(lst)

        lst_path = build_path(prefix, 'LST', out_dir)
        write_tiff(lst_path, lst, geo, proj)
        results['LST'] = lst_path
        add_layer(lst_path, f'{prefix}_LST', feedback, apply_continuous_colormap, {'cmap': CMAP_LST, 'label': 'LST', 'v_min_data': lst_stats.get('min'), 'v_max_data': lst_stats.get('max')})

        diagnostics = self._diagnostics(valid, qa_valid, geo, ndvi_rural)

        if export_diag:
            ndvi_path = build_path(prefix, 'NDVI', out_dir)
            ndbi_path = build_path(prefix, 'NDBI', out_dir)
            write_tiff(ndvi_path, ndvi, geo, proj)
            write_tiff(ndbi_path, ndbi, geo, proj)
            results['NDVI'] = ndvi_path
            results['NDBI'] = ndbi_path
            add_layer(ndvi_path, f'{prefix}_NDVI', feedback, apply_continuous_colormap, {'cmap': CMAP_NDVI, 'label': 'NDVI', 'v_min_data': -1.0, 'v_max_data': 1.0})
            add_layer(ndbi_path, f'{prefix}_NDBI', feedback, apply_continuous_colormap, {'cmap': CMAP_NDBI, 'label': 'NDBI', 'v_min_data': -1.0, 'v_max_data': 1.0})

            valid_path = build_path(prefix, 'VALID_MASK', out_dir)
            urban_tmp = np.zeros_like(valid, dtype=np.float64)
            rural_tmp = np.zeros_like(valid, dtype=np.float64)
            write_tiff(valid_path, valid.astype(np.float64), geo, proj, nodata=0)
            results['VALID_MASK'] = valid_path
            add_layer(valid_path, f'{prefix}_VALID_MASK', feedback, apply_valid_mask_colormap)
        else:
            valid_path = None
            urban_tmp = rural_tmp = None

        if mode == 'LST':
            if export_csv:
                csv_path = os.path.join(out_dir, f'{prefix}_stats.csv')
                write_csv_stats(csv_path, prefix, mode, mtl, lst_stats, diagnostics=diagnostics)
                results['CSV'] = csv_path
            return results

        thresholds = [ndvi_rural, 0.30, 0.25, 0.20]
        used_thr = None
        urban_mask = rural_mask = None
        for thr in thresholds:
            um, rm = compute_zone_masks(ndvi, thr, ndbi=ndbi, valid_mask=valid)
            if int(rm.sum()) > 0 and int(um.sum()) > 0:
                urban_mask, rural_mask, used_thr = um, rm, thr
                break
        if urban_mask is None or rural_mask is None:
            raise ValueError('Could not create non-empty urban and rural zones for UHI. / Не удалось сформировать непустые городскую и сельскую зоны для UHI.')
        diagnostics['rural_ndvi_threshold'] = used_thr
        diagnostics['urban_px'] = int(urban_mask.sum())
        diagnostics['rural_px'] = int(rural_mask.sum())
        diagnostics['urban_area_m2'] = diagnostics['urban_px'] * diagnostics['pixel_area_m2']
        diagnostics['rural_area_m2'] = diagnostics['rural_px'] * diagnostics['pixel_area_m2']
        diagnostics['urban_area_ha'] = diagnostics['urban_area_m2'] / 10000.0
        diagnostics['rural_area_ha'] = diagnostics['rural_area_m2'] / 10000.0

        if export_diag:
            urban_tmp = urban_mask.astype(np.float64)
            rural_tmp = rural_mask.astype(np.float64)
            urban_path = build_path(prefix, 'URBAN_MASK', out_dir)
            rural_path = build_path(prefix, 'RURAL_MASK', out_dir)
            write_tiff(urban_path, urban_tmp, geo, proj, nodata=0)
            write_tiff(rural_path, rural_tmp, geo, proj, nodata=0)
            results['URBAN_MASK'] = urban_path
            results['RURAL_MASK'] = rural_path
            add_layer(urban_path, f'{prefix}_URBAN_MASK', feedback, apply_urban_mask_colormap)
            add_layer(rural_path, f'{prefix}_RURAL_MASK', feedback, apply_rural_mask_colormap)

        utfvi = compute_utfvi(lst)
        uhi_diff, rural_mean = compute_uhi_diff(lst, rural_mask)
        uhi_stats = compute_uhi_stats(lst, uhi_diff, utfvi, urban_mask, rural_mask, rural_mean, ndvi=ndvi, ndbi=ndbi)

        utfvi_path = build_path(prefix, 'UTFVI', out_dir)
        uhi_path = build_path(prefix, 'UHI_DIFF', out_dir)
        write_tiff(utfvi_path, utfvi, geo, proj)
        write_tiff(uhi_path, uhi_diff, geo, proj)
        results['UTFVI'] = utfvi_path
        results['UHI_DIFF'] = uhi_path
        add_layer(utfvi_path, f'{prefix}_UTFVI', feedback, apply_utfvi_colormap)
        add_layer(uhi_path, f'{prefix}_UHI_DIFF', feedback, apply_continuous_colormap, {'cmap': CMAP_UHI_DIFF, 'label': 'UHI diff', 'v_min_data': float(np.nanmin(uhi_diff[np.isfinite(uhi_diff)])) if np.any(np.isfinite(uhi_diff)) else None, 'v_max_data': float(np.nanmax(uhi_diff[np.isfinite(uhi_diff)])) if np.any(np.isfinite(uhi_diff)) else None})

        if export_csv:
            csv_path = os.path.join(out_dir, f'{prefix}_stats.csv')
            write_csv_stats(csv_path, prefix, mode, mtl, lst_stats, uhi_stats=uhi_stats, diagnostics=diagnostics)
            results['CSV'] = csv_path

        return results

    def _stats(self, arr: np.ndarray) -> dict:
        vals = arr[np.isfinite(arr)]
        if vals.size == 0:
            return {'min': float('nan'), 'max': float('nan'), 'mean': float('nan'), 'std': float('nan'), 'valid_pct': 0.0}
        return {
            'min': float(np.nanmin(vals)),
            'max': float(np.nanmax(vals)),
            'mean': float(np.nanmean(vals)),
            'std': float(np.nanstd(vals)),
            'valid_pct': 100.0 * vals.size / arr.size,
        }

    def _diagnostics(self, valid: np.ndarray, qa_valid: np.ndarray, geo, rural_thr: float) -> dict:
        pixel_area_m2 = abs(float(geo[1] * geo[5])) if geo else float('nan')
        valid_px = int(valid.sum())
        invalid_px = int(valid.size - valid_px)
        qa_invalid_px = int((~qa_valid).sum()) if qa_valid is not None else 0
        return {
            'rural_ndvi_threshold': rural_thr,
            'valid_px': valid_px,
            'invalid_px': invalid_px,
            'qa_invalid_px': qa_invalid_px,
            'valid_domain_pct': 100.0 * valid_px / valid.size if valid.size else float('nan'),
            'qa_invalid_pct': 100.0 * qa_invalid_px / valid.size if valid.size else float('nan'),
            'pixel_area_m2': pixel_area_m2,
            'pixel_area_ha': pixel_area_m2 / 10000.0 if np.isfinite(pixel_area_m2) else float('nan'),
        }

    def shortHelpString(self):
        return """
<h2>English</h2>
<p><b>Landsat Thermal &amp; UHI Processor</b> automates the core thermal-processing workflow for Landsat 8/9 Collection 2 Level-1 scenes inside QGIS.</p>

<h3>Processing logic</h3>
<ol>
  <li><b>Scene check.</b> The module searches the selected folder for the MTL metadata file and required bands: B4, B5, B6, B10 and, optionally, QA_PIXEL.</li>
  <li><b>Metadata reading.</b> Radiometric and thermal coefficients are read automatically from the MTL file.</li>
  <li><b>Brightness Temperature.</b> Band 10 is converted to radiance and then to Brightness Temperature.</li>
  <li><b>Surface indices.</b> B4, B5 and B6 are aligned to the thermal band grid; NDVI and NDBI are calculated.</li>
  <li><b>Land Surface Temperature.</b> NDVI is used to estimate emissivity; LST is calculated in degrees Celsius.</li>
  <li><b>Masking.</b> Invalid pixels and, when enabled, QA_PIXEL cloud/shadow pixels are excluded from analysis.</li>
  <li><b>UHI analysis.</b> Rural reference pixels are selected by the NDVI threshold. The module calculates the rural mean LST, UHI difference raster and UTFVI classes.</li>
  <li><b>Export.</b> Results are saved as GeoTIFF layers; CSV statistics and diagnostic masks can be exported additionally.</li>
</ol>

<h3>Processing modes</h3>
<ul>
  <li><b>BT</b> — Brightness Temperature from B10.</li>
  <li><b>LST</b> — Land Surface Temperature using NDVI-based emissivity correction.</li>
  <li><b>LST + UHI</b> — full workflow: LST, UTFVI, UHI difference, NDBI, diagnostic masks and CSV statistics.</li>
</ul>

<h3>Input requirements</h3>
<p>The input folder must contain an unpacked Landsat 8/9 Collection 2 Level-1 scene with original file names. For the full UHI workflow, B4, B5, B6, B10 and MTL are required. QA_PIXEL is used only when cloud masking is enabled.</p>

<h3>Output interpretation</h3>
<p>LST shows surface temperature in °C. UHI difference shows the deviation of each pixel from the rural reference mean. UTFVI provides a classified urban thermal stress layer.</p>

<hr/>

<h2>Русский</h2>
<p><b>Landsat Thermal &amp; UHI Processor</b> автоматизирует базовый процесс тепловой обработки сцен Landsat 8/9 Collection 2 Level-1 внутри QGIS.</p>

<h3>Логика обработки</h3>
<ol>
  <li><b>Проверка сцены.</b> Модуль ищет в выбранной папке файл метаданных MTL и необходимые каналы: B4, B5, B6, B10 и, при наличии, QA_PIXEL.</li>
  <li><b>Чтение метаданных.</b> Радиометрические и тепловые коэффициенты автоматически извлекаются из MTL-файла.</li>
  <li><b>Яркостная температура.</b> Band 10 переводится в радианс, затем рассчитывается Brightness Temperature.</li>
  <li><b>Поверхностные индексы.</b> B4, B5 и B6 выравниваются по сетке теплового канала; рассчитываются NDVI и NDBI.</li>
  <li><b>Температура поверхности.</b> По NDVI оценивается эмиссивность, затем рассчитывается LST в градусах Цельсия.</li>
  <li><b>Маскирование.</b> Невалидные пиксели и, при включении параметра, облака/тени по QA_PIXEL исключаются из анализа.</li>
  <li><b>UHI-анализ.</b> Сельская референсная зона выбирается по NDVI-порогу. Модуль рассчитывает среднюю LST этой зоны, растр UHI difference и классы UTFVI.</li>
  <li><b>Экспорт.</b> Результаты сохраняются как GeoTIFF-слои; дополнительно могут экспортироваться CSV-статистика и диагностические маски.</li>
</ol>

<h3>Режимы обработки</h3>
<ul>
  <li><b>BT</b> — яркостная температура по B10.</li>
  <li><b>LST</b> — температура поверхности с NDVI-коррекцией эмиссивности.</li>
  <li><b>LST + UHI</b> — полный процесс: LST, UTFVI, UHI difference, NDBI, диагностические маски и CSV-статистика.</li>
</ul>

<h3>Требования к входным данным</h3>
<p>Входная папка должна содержать распакованную сцену Landsat 8/9 Collection 2 Level-1 с исходными именами файлов. Для полного UHI-процесса нужны B4, B5, B6, B10 и MTL. QA_PIXEL используется только при включённой облачной маске.</p>

<h3>Интерпретация результатов</h3>
<p>LST показывает температуру поверхности в °C. UHI difference показывает отклонение каждого пикселя от средней температуры сельской референсной зоны. UTFVI даёт классифицированный слой тепловой напряжённости городской среды.</p>
"""

    def name(self):
        return 'landsat_thermal_uhi_processor'

    def displayName(self):
        return 'Landsat Thermal & UHI Processor'

    def group(self):
        return 'Landsat Tools'

    def groupId(self):
        return 'landsat_tools'

    def createInstance(self):
        return LandsatThermalProcessor()
