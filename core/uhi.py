# -*- coding: utf-8 -*-
"""UHI metrics and statistics."""

import numpy as np
from .constants import UTFVI_CLASSES


def compute_utfvi(lst: np.ndarray) -> np.ndarray:
    vals = lst[np.isfinite(lst)]
    if vals.size == 0:
        return np.full_like(lst, np.nan)
    mean = float(np.nanmean(vals))
    if mean == 0 or not np.isfinite(mean):
        return np.full_like(lst, np.nan)
    with np.errstate(divide='ignore', invalid='ignore'):
        out = (lst - mean) / mean
    out[~np.isfinite(out)] = np.nan
    return out


def compute_uhi_diff(lst: np.ndarray, rural_mask: np.ndarray) -> tuple:
    rural_vals = lst[rural_mask & np.isfinite(lst)]
    if rural_vals.size == 0:
        return np.full_like(lst, np.nan), np.nan
    rural_mean = float(np.nanmean(rural_vals))
    out = lst - rural_mean
    out[~np.isfinite(lst)] = np.nan
    return out, rural_mean


def _pearson_r(a: np.ndarray, b: np.ndarray) -> float:
    mask = np.isfinite(a) & np.isfinite(b)
    if mask.sum() < 2:
        return float('nan')
    aa = a[mask]
    bb = b[mask]
    if np.nanstd(aa) == 0 or np.nanstd(bb) == 0:
        return float('nan')
    return float(np.corrcoef(aa, bb)[0, 1])


def compute_uhi_stats(lst, uhi_diff, utfvi, urban_mask, rural_mask, rural_mean, ndvi=None, ndbi=None):
    def _safe_mean(arr, mask):
        vals = arr[mask & np.isfinite(arr)]
        return float(np.nanmean(vals)) if vals.size > 0 else float('nan')

    lst_urban_mean = _safe_mean(lst, urban_mask)
    out = {
        'lst_scene_mean': float(np.nanmean(lst[np.isfinite(lst)])) if np.any(np.isfinite(lst)) else float('nan'),
        'lst_urban_mean': lst_urban_mean,
        'lst_rural_mean': rural_mean,
        'uhi_intensity': (lst_urban_mean - rural_mean) if np.isfinite(lst_urban_mean) and np.isfinite(rural_mean) else float('nan'),
        'uhi_diff_max': float(np.nanmax(uhi_diff[np.isfinite(uhi_diff)])) if np.any(np.isfinite(uhi_diff)) else float('nan'),
        'urban_px_pct': 100.0 * int(urban_mask.sum()) / urban_mask.size if urban_mask.size else float('nan'),
        'rural_px_pct': 100.0 * int(rural_mask.sum()) / rural_mask.size if rural_mask.size else float('nan'),
    }
    if ndbi is not None:
        out.update({
            'ndbi_scene_mean': float(np.nanmean(ndbi[np.isfinite(ndbi)])) if np.any(np.isfinite(ndbi)) else float('nan'),
            'ndbi_urban_mean': _safe_mean(ndbi, urban_mask),
            'ndbi_rural_mean': _safe_mean(ndbi, rural_mask),
            'ndbi_urban_pct': 100.0 * int(((ndbi > 0) & np.isfinite(ndbi)).sum()) / ndbi.size if ndbi.size else float('nan'),
            'r_lst_ndbi': _pearson_r(lst, ndbi),
        })
    if ndvi is not None:
        out['r_lst_ndvi'] = _pearson_r(lst, ndvi)
    valid_utfvi = utfvi[np.isfinite(utfvi)]
    total = int(valid_utfvi.size) if valid_utfvi.size > 0 else 1
    for lo, hi, label, _ in UTFVI_CLASSES:
        out[f'utfvi_{label}'] = 100.0 * int(((valid_utfvi > lo) & (valid_utfvi <= hi)).sum()) / total
    return out
