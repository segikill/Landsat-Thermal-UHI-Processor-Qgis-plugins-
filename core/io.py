# -*- coding: utf-8 -*-
"""Scene scanning, metadata IO, raster IO and CSV export."""

import csv
import glob
import os
import re

import numpy as np
from osgeo import gdal, gdalconst

from .constants import NODATA_FILL


def find_scene_files(scene_dir: str) -> dict:
    result = {'mtl': None, 'b4': None, 'b5': None, 'b6': None, 'b10': None, 'qa': None, 'scene_id': None}
    if not os.path.isdir(scene_dir):
        return result

    def _find(pattern: str):
        matches = glob.glob(os.path.join(scene_dir, pattern))
        return matches[0] if matches else None

    result['mtl'] = _find('*_MTL.txt')
    result['b4'] = _find('*_B4.TIF')
    result['b5'] = _find('*_B5.TIF')
    result['b6'] = _find('*_B6.TIF')
    result['b10'] = _find('*_B10.TIF')
    result['qa'] = _find('*_QA_PIXEL.TIF')

    if result['mtl']:
        base = re.sub(r'_MTL$', '', os.path.splitext(os.path.basename(result['mtl']))[0])
        parts = base.split('_')
        result['scene_id'] = '_'.join(parts[:4]) if len(parts) >= 4 else base
    return result


def format_file_check(files: dict, mode: str) -> str:
    need = mode in ('LST', 'UHI')
    rows = [
        ('MTL (metadata / метаданные)', files.get('mtl'), True),
        ('Band 10 (thermal / тепловой)', files.get('b10'), True),
        ('Band 4 (red / красный)', files.get('b4'), need),
        ('Band 5 (NIR)', files.get('b5'), need),
        ('Band 6 (SWIR1, for NDBI / для NDBI)', files.get('b6'), need),
        ('QA_PIXEL (clouds / облака)', files.get('qa'), False),
    ]
    lines = ['--- File check / Проверка файлов ---']
    for label, path, required in rows:
        if path and os.path.isfile(path):
            lines.append(f'  OK  {label}: {os.path.basename(path)}')
        else:
            status = 'MISSING' if required else '—'
            lines.append(f'  {status}  {label}')
    if files.get('scene_id'):
        lines.append(f'  Scene ID: {files["scene_id"]}')
    return '\n'.join(lines)


def parse_mtl(mtl_path: str) -> dict:
    needed = {
        'RADIANCE_MULT_BAND_10': None,
        'RADIANCE_ADD_BAND_10': None,
        'K1_CONSTANT_BAND_10': None,
        'K2_CONSTANT_BAND_10': None,
        'DATE_ACQUIRED': None,
        'SCENE_CENTER_TIME': None,
        'SUN_ELEVATION': None,
        'EARTH_SUN_DISTANCE': None,
    }
    with open(mtl_path, 'r', encoding='utf-8', errors='ignore') as handle:
        for raw in handle:
            line = raw.strip()
            if '=' not in line:
                continue
            key, value = [x.strip() for x in line.split('=', 1)]
            if key in needed:
                needed[key] = value.strip('"')

    for key in ('RADIANCE_MULT_BAND_10', 'RADIANCE_ADD_BAND_10', 'K1_CONSTANT_BAND_10', 'K2_CONSTANT_BAND_10'):
        if needed[key] is None:
            raise ValueError(f'MTL: missing {key} / не найден {key}')
        needed[key] = float(needed[key])

    for key in ('SUN_ELEVATION', 'EARTH_SUN_DISTANCE'):
        try:
            needed[key] = float(needed[key]) if needed[key] else None
        except Exception:
            needed[key] = None

    return {
        'ML': needed['RADIANCE_MULT_BAND_10'],
        'AL': needed['RADIANCE_ADD_BAND_10'],
        'K1': needed['K1_CONSTANT_BAND_10'],
        'K2': needed['K2_CONSTANT_BAND_10'],
        'date': needed.get('DATE_ACQUIRED', ''),
        'time': needed.get('SCENE_CENTER_TIME', ''),
        'sun_elev': needed.get('SUN_ELEVATION'),
    }


def read_band(path: str):
    ds = gdal.Open(path, gdal.GA_ReadOnly)
    if ds is None:
        raise IOError(f'Could not open / Не удалось открыть: {path}')
    band = ds.GetRasterBand(1)
    arr = band.ReadAsArray().astype(np.float64)
    nd, geo, prj = band.GetNoDataValue(), ds.GetGeoTransform(), ds.GetProjection()
    ds = None
    return arr, nd, geo, prj


def read_band_aligned(src_path: str, ref_path: str, resample_alg=None) -> tuple:
    ref_ds = gdal.Open(ref_path, gdal.GA_ReadOnly)
    src_ds = gdal.Open(src_path, gdal.GA_ReadOnly)
    if ref_ds is None:
        raise IOError(f'Could not open reference raster / Не удалось открыть эталонный растр: {ref_path}')
    if src_ds is None:
        raise IOError(f'Could not open source raster / Не удалось открыть исходный растр: {src_path}')

    rg, rp = ref_ds.GetGeoTransform(), ref_ds.GetProjection()
    rc, rr = ref_ds.RasterXSize, ref_ds.RasterYSize
    sg = src_ds.GetGeoTransform()
    sc, sr = src_ds.RasterXSize, src_ds.RasterYSize
    match = rc == sc and rr == sr and abs(rg[0] - sg[0]) < 1e-9 and abs(rg[3] - sg[3]) < 1e-9 and abs(rg[1] - sg[1]) < 1e-9 and abs(rg[5] - sg[5]) < 1e-9
    if match:
        src_ds = None
        ref_ds = None
        arr, nd, geo, prj = read_band(src_path)
        return arr, nd, geo, prj, None

    info = {
        'src_name': os.path.basename(src_path),
        'src_shape': (sr, sc),
        'ref_shape': (rr, rc),
    }
    mem = gdal.GetDriverByName('MEM').Create('', rc, rr, 1, gdal.GDT_Float64)
    mem.SetGeoTransform(rg)
    mem.SetProjection(rp)
    band = mem.GetRasterBand(1)
    band.Fill(np.nan)
    band.SetNoDataValue(np.nan)
    if resample_alg is None:
        resample_alg = gdalconst.GRA_Bilinear
    gdal.ReprojectImage(src_ds, mem, src_ds.GetProjection(), rp, resample_alg)
    arr = band.ReadAsArray().astype(np.float64)
    nd = band.GetNoDataValue()
    src_ds = None
    ref_ds = None
    mem = None
    return arr, nd, rg, rp, info


def write_tiff(path: str, arr: np.ndarray, geo, prj, nodata: float = NODATA_FILL) -> None:
    drv = gdal.GetDriverByName('GTiff')
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    rows, cols = arr.shape
    ds = drv.Create(path, cols, rows, 1, gdal.GDT_Float32, options=['TILED=YES', 'COMPRESS=DEFLATE', 'PREDICTOR=2', 'BIGTIFF=IF_SAFER'])
    ds.SetGeoTransform(geo)
    if prj:
        ds.SetProjection(prj)
    band = ds.GetRasterBand(1)
    band.SetNoDataValue(float(nodata))
    out = arr.astype(np.float32)
    out[~np.isfinite(out)] = np.float32(nodata)
    band.WriteArray(out)
    band.FlushCache()
    ds = None


def write_csv_stats(csv_path: str, scene_id: str, mode: str, mtl_meta: dict, lst_stats: dict, uhi_stats: dict = None, diagnostics: dict = None) -> None:
    row = {
        'scene_id': scene_id or '',
        'date': mtl_meta.get('date', ''),
        'time_utc': mtl_meta.get('time', ''),
        'mode': mode,
        'sun_elevation': mtl_meta.get('sun_elev', ''),
        'lst_min': f'{lst_stats.get("min", float("nan")):.3f}',
        'lst_max': f'{lst_stats.get("max", float("nan")):.3f}',
        'lst_mean': f'{lst_stats.get("mean", float("nan")):.3f}',
        'lst_std': f'{lst_stats.get("std", float("nan")):.3f}',
        'valid_pct': f'{lst_stats.get("valid_pct", float("nan")):.1f}',
    }
    if uhi_stats:
        row.update({
            'lst_urban_mean': f'{uhi_stats.get("lst_urban_mean", float("nan")):.3f}',
            'lst_rural_mean': f'{uhi_stats.get("lst_rural_mean", float("nan")):.3f}',
            'uhi_intensity': f'{uhi_stats.get("uhi_intensity", float("nan")):.3f}',
            'uhi_diff_max': f'{uhi_stats.get("uhi_diff_max", float("nan")):.3f}',
            'urban_px_pct': f'{uhi_stats.get("urban_px_pct", float("nan")):.1f}',
            'rural_px_pct': f'{uhi_stats.get("rural_px_pct", float("nan")):.1f}',
            'utfvi_none_pct': f'{uhi_stats.get("utfvi_No UHI / Нет UHI", float("nan")):.1f}',
            'utfvi_weak_pct': f'{uhi_stats.get("utfvi_Weak / Слабый", float("nan")):.1f}',
            'utfvi_moderate_pct': f'{uhi_stats.get("utfvi_Moderate / Средний", float("nan")):.1f}',
            'utfvi_strong_pct': f'{uhi_stats.get("utfvi_Strong / Сильный", float("nan")):.1f}',
            'utfvi_intense_pct': f'{uhi_stats.get("utfvi_Intense / Интенсивный", float("nan")):.1f}',
            'utfvi_extreme_pct': f'{uhi_stats.get("utfvi_Extreme / Экстремальный", float("nan")):.1f}',
            'ndbi_scene_mean': f'{uhi_stats.get("ndbi_scene_mean", float("nan")):.4f}',
            'ndbi_urban_mean': f'{uhi_stats.get("ndbi_urban_mean", float("nan")):.4f}',
            'ndbi_rural_mean': f'{uhi_stats.get("ndbi_rural_mean", float("nan")):.4f}',
            'ndbi_urban_pct': f'{uhi_stats.get("ndbi_urban_pct", float("nan")):.1f}',
            'r_lst_ndbi': f'{uhi_stats.get("r_lst_ndbi", float("nan")):.4f}',
            'r_lst_ndvi': f'{uhi_stats.get("r_lst_ndvi", float("nan")):.4f}',
        })
    diagnostics = diagnostics or {}
    row.update({
        'rural_ndvi_threshold': diagnostics.get('rural_ndvi_threshold', ''),
        'valid_px': diagnostics.get('valid_px', ''),
        'invalid_px': diagnostics.get('invalid_px', ''),
        'qa_invalid_px': diagnostics.get('qa_invalid_px', ''),
        'valid_domain_pct': f'{diagnostics.get("valid_domain_pct", float("nan")):.1f}' if diagnostics.get('valid_domain_pct') is not None else '',
        'qa_invalid_pct': f'{diagnostics.get("qa_invalid_pct", float("nan")):.1f}' if diagnostics.get('qa_invalid_pct') is not None else '',
        'pixel_area_m2': f'{diagnostics.get("pixel_area_m2", float("nan")):.3f}' if diagnostics.get('pixel_area_m2') is not None else '',
        'pixel_area_ha': f'{diagnostics.get("pixel_area_ha", float("nan")):.6f}' if diagnostics.get('pixel_area_ha') is not None else '',
        'urban_px': diagnostics.get('urban_px', ''),
        'rural_px': diagnostics.get('rural_px', ''),
        'urban_area_m2': f'{diagnostics.get("urban_area_m2", float("nan")):.3f}' if diagnostics.get('urban_area_m2') is not None else '',
        'rural_area_m2': f'{diagnostics.get("rural_area_m2", float("nan")):.3f}' if diagnostics.get('rural_area_m2') is not None else '',
        'urban_area_ha': f'{diagnostics.get("urban_area_ha", float("nan")):.6f}' if diagnostics.get('urban_area_ha') is not None else '',
        'rural_area_ha': f'{diagnostics.get("rural_area_ha", float("nan")):.6f}' if diagnostics.get('rural_area_ha') is not None else '',
    })
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, 'a', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row.keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def build_path(scene_id, suffix: str, out_dir: str) -> str:
    if scene_id:
        parts = scene_id.split('_')
        stem = f'{parts[0] if len(parts) > 0 else "LC"}_{parts[2] if len(parts) > 2 else "UNK"}_{parts[3] if len(parts) > 3 else "UNK"}_{suffix}'
    else:
        stem = f'landsat_{suffix}'
    return os.path.join(out_dir, f'{stem}.tif')
