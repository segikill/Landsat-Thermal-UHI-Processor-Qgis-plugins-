# Landsat Thermal & UHI Processor — QGIS Plugin

## English

**Version:** 2.2.0  
**Compatibility:** QGIS 3.16+  
**Dependencies:** numpy, GDAL (included in a standard QGIS installation)

---

## Installation

### Method 1 — Plugin Manager (ZIP)

1. In QGIS, open **Plugins → Manage and Install Plugins → Install from ZIP**.
2. Select `landsat_thermal_uhi.zip`.
3. Click **Install Plugin**.

### Method 2 — Manual installation

1. Copy the `landsat_thermal_uhi` folder to the QGIS plugins directory:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
2. Restart QGIS.
3. Enable the plugin: **Plugins → Manage and Install Plugins** → find `Landsat Thermal & UHI Processor`.

---

## Usage

The algorithm appears in the **Processing Toolbox** under the **Landsat Tools** group.

```
Processing Toolbox
└── Landsat Tools
    └── Landsat 8/9 — Thermal & UHI Processor
```

### Input parameters

| Parameter | Description |
|---|---|
| **Scene folder** | Path to the folder with unpacked Landsat files (`*.TIF`, `*_MTL.txt`) |
| **Processing mode** | BT / LST / LST+UHI |
| **Output folder** | Folder where the output TIFF files are saved |
| **Rural NDVI threshold** | UHI reference threshold for the “green” rural zone, usually 0.30–0.40 |
| **Export CSV** | Save scene statistics to CSV; new rows are appended on each run |
| **Export diagnostic masks** | Save auxiliary masks for valid pixels, urban zones and rural zones |
| **File prefix** | Optional custom prefix for output file names |

### Processing modes

| Mode | Description | Required files |
|---|---|---|
| **BT** | Brightness Temperature | B10 + MTL |
| **LST** | Land Surface Temperature with NDVI-based emissivity correction | B4 + B5 + B10 + MTL |
| **LST+UHI** | Full UHI workflow: LST + UTFVI + UHI difference + NDBI + CSV statistics | B4 + B5 + B6 + B10 + MTL |

### Output files in UHI mode

| File | Description |
|---|---|
| `*_LST.tif` | Land Surface Temperature, °C |
| `*_UTFVI.tif` | Urban Thermal Field Variance Index, 6 classes |
| `*_UHI_diff.tif` | LST minus rural-zone mean LST, °C |
| `*_NDVI.tif` | Normalized Difference Vegetation Index |
| `*_NDBI.tif` | Normalized Difference Built-up Index |
| `*_stats.csv` | Scene summary statistics |

### UTFVI classification (Guha et al., 2018)

| Range | Class |
|---|---|
| < 0 | No UHI |
| 0.000–0.005 | Weak |
| 0.005–0.010 | Moderate |
| 0.010–0.015 | Strong |
| 0.015–0.020 | Intense |
| > 0.020 | Extreme |

---

## Plugin structure

```
landsat_thermal_uhi/
├── __init__.py                   # QGIS entry point
├── plugin.py                     # Provider registration and toolbar/menu action
├── provider.py                   # QgsProcessingProvider
├── landsat_thermal_processor.py  # Main QgsProcessingAlgorithm
├── metadata.txt                  # Plugin Manager metadata
├── icons/
│   └── icon.png
└── README.md
```

---

## Supported satellites

- **Landsat 8** (LC08), Collection 2, Level-1
- **Landsat 9** (LC09), Collection 2, Level-1

---

## References

- Sobrino et al. (2004) — NDVI-based emissivity
- Guha et al. (2018) — UTFVI classification
- Zha et al. (2003) — NDBI (Normalized Difference Built-up Index)

---

## Русский

**Версия:** 2.2.0  
**Совместимость:** QGIS 3.16+  
**Зависимости:** numpy, GDAL (входят в стандартную установку QGIS)

---

## Установка

### Способ 1 — через менеджер плагинов (ZIP)

1. В QGIS откройте **Плагины → Управление плагинами → Установить из ZIP**.
2. Укажите файл `landsat_thermal_uhi.zip`.
3. Нажмите **Установить плагин**.

### Способ 2 — вручную

1. Скопируйте папку `landsat_thermal_uhi` в директорию плагинов QGIS:
   - **Windows:** `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - **Linux:** `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - **macOS:** `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`
2. Перезапустите QGIS.
3. Активируйте плагин: **Плагины → Управление плагинами** → найдите `Landsat Thermal & UHI Processor`.

---

## Использование

Алгоритм появится в **Панели инструментов обработки** в группе **Landsat Tools**.

```
Processing Toolbox
└── Landsat Tools
    └── Landsat 8/9 — Thermal & UHI Processor
```

### Входные параметры

| Параметр | Описание |
|---|---|
| **Папка сцены** | Путь к папке с распакованными файлами Landsat (`*.TIF`, `*_MTL.txt`) |
| **Режим обработки** | BT / LST / LST+UHI |
| **Выходная папка** | Папка, куда сохраняются результирующие TIFF |
| **NDVI-порог сельской зоны** | Эталонный порог для “зелёной” сельской зоны в UHI-анализе, обычно 0.30–0.40 |
| **Экспорт CSV** | Сохранение статистики сцены в CSV; новые строки добавляются при каждом запуске |
| **Экспорт диагностических масок** | Сохранение вспомогательных масок валидных пикселей, городской и сельской зон |
| **Префикс файлов** | Опциональный пользовательский префикс для имён выходных файлов |

### Режимы

| Режим | Описание | Нужные файлы |
|---|---|---|
| **BT** | Яркостная температура | B10 + MTL |
| **LST** | Температура поверхности с учётом NDVI-эмиссивности | B4 + B5 + B10 + MTL |
| **LST+UHI** | Полный UHI-анализ: LST + UTFVI + UHI diff + NDBI + CSV-статистика | B4 + B5 + B6 + B10 + MTL |

### Выходные файлы в режиме UHI

| Файл | Описание |
|---|---|
| `*_LST.tif` | Температура поверхности, °C |
| `*_UTFVI.tif` | Urban Thermal Field Variance Index, 6 классов |
| `*_UHI_diff.tif` | LST минус средняя LST сельской зоны, °C |
| `*_NDVI.tif` | Нормализованный разностный вегетационный индекс |
| `*_NDBI.tif` | Нормализованный разностный индекс застройки |
| `*_stats.csv` | Сводная статистика сцены |

### Классификация UTFVI (Guha et al., 2018)

| Диапазон | Класс |
|---|---|
| < 0 | Нет UHI |
| 0.000–0.005 | Слабый |
| 0.005–0.010 | Средний |
| 0.010–0.015 | Сильный |
| 0.015–0.020 | Интенсивный |
| > 0.020 | Экстремальный |

---

## Структура плагина

```
landsat_thermal_uhi/
├── __init__.py                   # Точка входа QGIS
├── plugin.py                     # Регистрация провайдера, кнопки и пункта меню
├── provider.py                   # QgsProcessingProvider
├── landsat_thermal_processor.py  # Основной алгоритм QgsProcessingAlgorithm
├── metadata.txt                  # Метаданные для менеджера плагинов
├── icons/
│   └── icon.png
└── README.md
```

---

## Поддерживаемые спутники

- **Landsat 8** (LC08), Collection 2, Level-1
- **Landsat 9** (LC09), Collection 2, Level-1

---

## Литература

- Sobrino et al. (2004) — NDVI-based emissivity
- Guha et al. (2018) — UTFVI classification
- Zha et al. (2003) — NDBI (Normalized Difference Built-up Index)
