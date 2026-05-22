# -*- coding: utf-8 -*-
"""NoData, QA_PIXEL and zonal masks."""

import numpy as np
from osgeo import gdalconst

from .constants import NDVI_SOIL
from .io import read_band_aligned


def nodata_mask(arr: np.ndarray, nd) -> np.ndarray:
    mask = (arr == 0) | ~np.isfinite(arr)
    if nd is not None and nd == nd:
        mask = mask | (arr == nd)
    return mask


def decode_qa_pixel(qa: np.ndarray) -> np.ndarray:
    qi = np.round(qa).astype(np.uint16)
    cirrus = ((qi >> 2) & 1).astype(bool)
    cloud = ((qi >> 3) & 1).astype(bool)
    shadow = ((qi >> 4) & 1).astype(bool)
    snow = ((qi >> 5) & 1).astype(bool)
    invalid = cirrus | cloud | shadow | snow
    return ~invalid


def build_valid_mask(b10: np.ndarray, nd10, b4: np.ndarray = None, nd4=None, b5: np.ndarray = None, nd5=None, b6: np.ndarray = None, nd6=None, qa_valid: np.ndarray = None) -> np.ndarray:
    valid = ~nodata_mask(b10, nd10)
    if b4 is not None:
        valid &= ~nodata_mask(b4, nd4)
    if b5 is not None:
        valid &= ~nodata_mask(b5, nd5)
    if b6 is not None:
        valid &= ~nodata_mask(b6, nd6)
    if qa_valid is not None:
        valid &= qa_valid
    return valid


def apply_cloud_mask(data: np.ndarray, qa_path: str, ref_path: str) -> tuple:
    try:
        qa, _, _, _, align_info = read_band_aligned(qa_path, ref_path, resample_alg=gdalconst.GRA_NearestNeighbour)
        qa_valid = decode_qa_pixel(qa)
        invalid = ~qa_valid
        pct = 100.0 * invalid.sum() / invalid.size
        return np.where(qa_valid, data, np.nan), {
            'applied': True,
            'cloud_px': int(invalid.sum()),
            'cloud_pct': float(pct),
            'align_info': align_info,
        }
    except Exception as exc:
        return data, {'applied': False, 'error': str(exc)}


def compute_zone_masks(ndvi: np.ndarray, ndvi_rural_threshold: float, ndbi: np.ndarray = None, valid_mask: np.ndarray = None) -> tuple:
    base = np.isfinite(ndvi)
    if valid_mask is not None:
        base &= valid_mask
    rural_mask = (ndvi > ndvi_rural_threshold) & base
    if ndbi is not None:
        urban_mask = (ndbi > 0) & np.isfinite(ndbi) & base
    else:
        urban_mask = (ndvi < NDVI_SOIL) & base
    urban_mask &= ~rural_mask
    rural_mask &= ~urban_mask
    return urban_mask, rural_mask
