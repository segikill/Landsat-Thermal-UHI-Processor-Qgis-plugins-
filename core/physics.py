# -*- coding: utf-8 -*-
"""Thermal and spectral calculations."""

import numpy as np
from .constants import BAND10_WAVELENGTH_UM, RHO, NDVI_SOIL, NDVI_VEG, EMIS_SOIL, EMIS_VEG


def compute_bt(b10: np.ndarray, invalid_mask: np.ndarray, c: dict) -> np.ndarray:
    l_rad = c['ML'] * b10 + c['AL']
    with np.errstate(divide='ignore', invalid='ignore'):
        safe = np.where(l_rad > 0, l_rad, np.nan)
        t_k = c['K2'] / np.log(c['K1'] / safe + 1.0)
    t_c = t_k - 273.15
    t_c[invalid_mask] = np.nan
    return t_c


def compute_ndvi(b4: np.ndarray, b5: np.ndarray) -> np.ndarray:
    with np.errstate(divide='ignore', invalid='ignore'):
        denom = b5 + b4
        return np.where(denom != 0, (b5 - b4) / denom, np.nan)


def compute_ndbi(b5: np.ndarray, b6: np.ndarray) -> np.ndarray:
    with np.errstate(divide='ignore', invalid='ignore'):
        denom = b6 + b5
        return np.where(denom != 0, (b6 - b5) / denom, np.nan)


def compute_emissivity(ndvi: np.ndarray) -> np.ndarray:
    pv = np.clip((ndvi - NDVI_SOIL) / (NDVI_VEG - NDVI_SOIL), 0.0, 1.0) ** 2
    emis = EMIS_SOIL + (EMIS_VEG - EMIS_SOIL) * pv
    emis = np.where(ndvi < NDVI_SOIL, EMIS_SOIL, emis)
    emis = np.where(ndvi > NDVI_VEG, EMIS_VEG, emis)
    return np.where(np.isfinite(ndvi), emis, np.nan)


def compute_lst(bt_c: np.ndarray, emis: np.ndarray) -> np.ndarray:
    bt_k = bt_c + 273.15
    with np.errstate(divide='ignore', invalid='ignore'):
        safe_e = np.where(emis > 0, emis, np.nan)
        corr = (BAND10_WAVELENGTH_UM * bt_k / RHO) * np.log(safe_e)
        lst_k = bt_k / (1.0 + corr)
    lst_c = lst_k - 273.15
    lst_c[~np.isfinite(lst_c)] = np.nan
    return lst_c
