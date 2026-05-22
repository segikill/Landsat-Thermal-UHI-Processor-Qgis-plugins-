# -*- coding: utf-8 -*-
"""Validation helpers for scene inputs, arrays and output paths."""

import os
import numpy as np


def validate_output_dir(out_dir: str) -> str:
    """Ensure output directory exists and is writable. Returns normalized path."""
    if not out_dir:
        raise ValueError('Output folder is not specified. / Папка для сохранения результатов не указана.')
    norm = os.path.abspath(os.path.expanduser(out_dir))
    os.makedirs(norm, exist_ok=True)
    if not os.path.isdir(norm):
        raise ValueError(f'Path is not a folder / Путь не является папкой: {norm}')
    if not os.access(norm, os.W_OK):
        raise ValueError(f'No write permission for folder / Нет прав на запись в папку: {norm}')
    return norm


def validate_scene_files(files: dict) -> None:
    """Validate base scene directory scan result and required core files."""
    if not isinstance(files, dict):
        raise ValueError('Invalid scene file list structure. / Некорректная структура списка файлов сцены.')
    for key in ('mtl', 'b10'):
        path = files.get(key)
        if not path:
            human = 'MTL' if key == 'mtl' else 'Band 10'
            raise ValueError(f'{human} not found / не найден.')
        if not os.path.isfile(path):
            raise ValueError(f'File does not exist / Файл не существует: {path}')


def validate_required_bands_for_mode(files: dict, mode: str) -> None:
    """Validate required bands for selected processing mode."""
    mode = (mode or '').upper()
    required = []
    if mode in ('LST', 'UHI'):
        required.extend([
            ('b4', 'Band 4'),
            ('b5', 'Band 5'),
            ('b6', 'Band 6 (SWIR1, for NDBI / для NDBI)'),
        ])
    missing = []
    for key, label in required:
        path = files.get(key)
        if not path or not os.path.isfile(path):
            missing.append(label)
    if missing:
        raise ValueError('Required files are missing / Отсутствуют обязательные файлы: ' + ', '.join(missing))


def validate_metadata_values(mtl: dict) -> None:
    """Validate parsed MTL values needed for BT/LST calculations."""
    if not isinstance(mtl, dict):
        raise ValueError('MTL was not recognized. / MTL не распознан.')
    required_numeric = ('ML', 'AL', 'K1', 'K2')
    for key in required_numeric:
        value = mtl.get(key)
        if value is None or not np.isfinite(value):
            raise ValueError(f'MTL: missing or invalid parameter {key}. / отсутствует или некорректен параметр {key}.')
    if mtl['ML'] == 0:
        raise ValueError('MTL: RADIANCE_MULT_BAND_10 cannot be 0. / RADIANCE_MULT_BAND_10 не может быть равен 0.')
    if mtl['K1'] <= 0 or mtl['K2'] <= 0:
        raise ValueError('MTL: K1/K2 constants must be positive. / константы K1/K2 должны быть положительными.')


def validate_array_shapes(named_arrays: dict) -> tuple:
    """Ensure all passed arrays have the same 2D shape. Returns that shape."""
    shape = None
    for name, arr in named_arrays.items():
        if arr is None:
            continue
        if not hasattr(arr, 'shape'):
            raise ValueError(f'{name}: object is not an array. / объект не является массивом.')
        if len(arr.shape) != 2:
            raise ValueError(f'{name}: expected a 2D raster. / ожидается двумерный растр.')
        if shape is None:
            shape = tuple(arr.shape)
        elif tuple(arr.shape) != shape:
            raise ValueError(
                f'Raster size mismatch: {name}={tuple(arr.shape)}, expected {shape}. / Несовпадение размеров растров: {name}={tuple(arr.shape)}, ожидается {shape}.'
            )
    if shape is None:
        raise ValueError('No rasters were provided for size validation. / Не передано ни одного растра для проверки размеров.')
    return shape


def validate_mask_shape(mask: np.ndarray, expected_shape: tuple, label: str) -> None:
    if mask is None:
        raise ValueError(f'{label}: mask was not created. / маска не создана.')
    if tuple(mask.shape) != tuple(expected_shape):
        raise ValueError(f'{label}: mask size {tuple(mask.shape)} does not match raster size {tuple(expected_shape)}. / размер {tuple(mask.shape)} не совпадает с размером растра {tuple(expected_shape)}.')


def validate_required_stats(stats: dict, label: str = 'Statistics / Статистика') -> None:
    if not isinstance(stats, dict) or not stats:
        raise ValueError(f'{label}: dictionary is empty or missing. / словарь пуст или отсутствует.')
