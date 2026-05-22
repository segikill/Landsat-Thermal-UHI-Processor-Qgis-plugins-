# Landsat Thermal & UHI Processor for QGIS

<p align="center">
  <strong>QGIS Processing plugin for Landsat 8/9 thermal processing, LST mapping and Urban Heat Island analysis.</strong>
</p>

<p align="center">
  <a href="#english">English</a> · <a href="#русский">Русский</a>
</p>

---

# English

## Overview

**Landsat Thermal & UHI Processor** is a QGIS Processing plugin for Landsat 8/9 Collection 2 scenes. It automates the main raster operations required for Brightness Temperature, Land Surface Temperature and Urban Heat Island analysis.

The plugin is intended for urban climate studies, surface temperature mapping, remote sensing education and applied GIS workflows.

## What the plugin does

- Reads Landsat metadata from the `*_MTL.txt` file.
- Calculates Brightness Temperature from Band 10.
- Calculates NDVI and NDVI-based land surface emissivity.
- Calculates Land Surface Temperature in degrees Celsius.
- Performs Urban Heat Island analysis using a rural reference zone.
- Calculates NDBI for built-up area interpretation.
- Classifies UTFVI values into thermal stress classes.
- Supports optional `QA_PIXEL` cloud masking.
- Exports raster outputs and optional CSV statistics.
- Runs directly from the QGIS Processing Toolbox.

## Processing modes

| Mode | Purpose | Required data |
|---|---|---|
| `BT` | Brightness Temperature calculation | B10 + MTL |
| `LST` | Land Surface Temperature with emissivity correction | B4 + B5 + B10 + MTL |
| `LST+UHI` | Full workflow: LST, UTFVI, UHI difference, NDBI and statistics | B4 + B5 + B6 + B10 + MTL |

## Requirements

- QGIS 3.16 or newer.
- Python environment included with QGIS.
- NumPy.
- GDAL.
- Unpacked Landsat 8/9 Collection 2 Level-1 scene.

NumPy and GDAL are usually included in the standard QGIS installation.

## Installation

### Install from ZIP

1. Open QGIS.
2. Go to **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select the plugin ZIP archive.
4. Click **Install Plugin**.
5. Enable the plugin in the plugin manager if it is not enabled automatically.

### Manual installation

Copy the plugin folder to the QGIS profile plugin directory:

```text
Windows: %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
Linux:   ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
macOS:   ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

Restart QGIS and enable the plugin in **Plugins → Manage and Install Plugins**.

## Usage

After installation, open the algorithm from the Processing Toolbox:

```text
Processing Toolbox
└── Landsat Tools
    └── Landsat 8/9 — Thermal & UHI Processor
```

Basic workflow:

1. Download and unpack a Landsat 8/9 Collection 2 Level-1 scene.
2. Open the algorithm in the QGIS Processing Toolbox.
3. Select the scene folder.
4. Choose the processing mode.
5. Set the output folder.
6. Run the algorithm.
7. Review the generated raster layers and CSV statistics.

## Input data

The scene folder must contain the original Landsat files:

| File or band | Purpose |
|---|---|
| `*_MTL.txt` | Scene metadata and calibration coefficients |
| Band 4 | Red band for NDVI |
| Band 5 | Near-infrared band for NDVI |
| Band 6 | Short-wave infrared band for NDBI |
| Band 10 | Thermal infrared band for BT and LST |
| `QA_PIXEL` | Optional cloud mask |

## Parameters

| Parameter | Description |
|---|---|
| `Landsat scene folder` | Folder with unpacked Landsat scene files. |
| `Processing mode` | Select `BT`, `LST` or `LST+UHI`. |
| `QA_PIXEL cloud mask` | Apply cloud masking using the QA_PIXEL layer. |
| `Rural NDVI threshold` | NDVI threshold for rural reference pixels in UHI analysis. |
| `Export statistics to CSV` | Save summary statistics to a CSV file. |
| `Export diagnostic masks` | Save auxiliary masks for quality control. |
| `Output folder` | Folder for generated outputs. |
| `File name prefix` | Optional custom prefix for output files. |

## Output files

Depending on the selected mode, the plugin may generate:

| Output | Description |
|---|---|
| `*_BT.tif` | Brightness Temperature raster. |
| `*_LST.tif` | Land Surface Temperature raster, °C. |
| `*_NDVI.tif` | Normalized Difference Vegetation Index. |
| `*_NDBI.tif` | Normalized Difference Built-up Index. |
| `*_UTFVI.tif` | Urban Thermal Field Variance Index classes. |
| `*_UHI_diff.tif` | Difference between LST and rural mean LST, °C. |
| `*_stats.csv` | Summary scene statistics. |
| diagnostic masks | Auxiliary masks for valid, urban and rural pixels. |

## UTFVI classes

| UTFVI range | Class |
|---|---|
| `< 0` | No UHI |
| `0.000–0.005` | Weak |
| `0.005–0.010` | Moderate |
| `0.010–0.015` | Strong |
| `0.015–0.020` | Intense |
| `> 0.020` | Extreme |

## Project structure

```text
landsat_thermal_uhi/
├── __init__.py                   # QGIS plugin entry point
├── plugin.py                     # Plugin initialization and provider registration
├── provider.py                   # QGIS Processing provider
├── landsat_thermal_processor.py  # Main processing algorithm
├── metadata.txt                  # QGIS plugin metadata
├── README.md                     # Repository documentation
├── LICENSE                       # GPL-2.0 license text
├── icons/
│   └── icon.png                  # Plugin icon
└── core/
    ├── constants.py              # Constants and class names
    ├── io.py                     # File search, raster I/O, CSV export
    ├── masks.py                  # QA/cloud and analysis masks
    ├── physics.py                # Thermal and emissivity calculations
    ├── uhi.py                    # UHI-related calculations
    ├── validation.py             # Input and output validation
    └── visualization.py          # Raster styling and QGIS layer loading
```

## Limitations

- The plugin expects Landsat Collection 2 Level-1 file naming and metadata structure.
- LST and UHI results depend on atmospheric conditions, scene quality, cloud masking and land cover composition.
- The rural reference zone is selected using an NDVI threshold; this approach may require adjustment for arid, mountainous, coastal or highly fragmented landscapes.
- The tool is intended for GIS analysis and educational workflows. Scientific publication may require additional atmospheric correction, validation and uncertainty assessment.

## License

This plugin is distributed under the GNU General Public License, version 2. See the `LICENSE` file in the plugin package.

## References

- Sobrino, J. A., Jiménez-Muñoz, J. C., & Paolini, L. (2004). Land surface temperature retrieval from Landsat TM 5. *Remote Sensing of Environment*.
- Guha, S., Govil, H., Dey, A., & Gill, N. (2018). Analytical study of land surface temperature with NDVI and NDBI using Landsat 8 OLI and TIRS data. *Journal of Earth System Science*.
- Zha, Y., Gao, J., & Ni, S. (2003). Use of normalized difference built-up index in automatically mapping urban areas from TM imagery. *International Journal of Remote Sensing*.

---

# Русский

## Обзор

**Landsat Thermal & UHI Processor** — это плагин QGIS Processing для сцен Landsat 8/9 Collection 2. Он автоматизирует основные растровые операции для расчёта яркостной температуры, температуры поверхности и анализа городского теплового острова.

Плагин подходит для исследований городского климата, картографирования температуры поверхности, обучения дистанционному зондированию и прикладных ГИС-задач.

## Что делает плагин

- Считывает метаданные Landsat из файла `*_MTL.txt`.
- Рассчитывает яркостную температуру по Band 10.
- Рассчитывает NDVI и эмиссивность поверхности на основе NDVI.
- Рассчитывает температуру поверхности в градусах Цельсия.
- Выполняет анализ городского теплового острова с использованием сельской референсной зоны.
- Рассчитывает NDBI для интерпретации застроенных территорий.
- Классифицирует значения UTFVI по классам тепловой нагрузки.
- Поддерживает опциональную облачную маску `QA_PIXEL`.
- Экспортирует растровые результаты и CSV-статистику.
- Запускается напрямую из панели Processing Toolbox QGIS.

## Режимы обработки

| Режим | Назначение | Необходимые данные |
|---|---|---|
| `BT` | Расчёт яркостной температуры | B10 + MTL |
| `LST` | Расчёт температуры поверхности с коррекцией эмиссивности | B4 + B5 + B10 + MTL |
| `LST+UHI` | Полный цикл: LST, UTFVI, UHI difference, NDBI и статистика | B4 + B5 + B6 + B10 + MTL |

## Требования

- QGIS 3.16 или новее.
- Python-среда, входящая в состав QGIS.
- NumPy.
- GDAL.
- Распакованная сцена Landsat 8/9 Collection 2 Level-1.

NumPy и GDAL обычно входят в стандартную установку QGIS.

## Установка

### Установка из ZIP

1. Откройте QGIS.
2. Перейдите в **Плагины → Управление плагинами → Установить из ZIP**.
3. Выберите ZIP-архив плагина.
4. Нажмите **Установить плагин**.
5. Активируйте плагин в менеджере плагинов, если он не включился автоматически.

### Ручная установка

Скопируйте папку плагина в директорию плагинов профиля QGIS:

```text
Windows: %APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\
Linux:   ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
macOS:   ~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/
```

Перезапустите QGIS и включите плагин через **Плагины → Управление плагинами**.

## Использование

После установки алгоритм доступен в панели Processing Toolbox:

```text
Processing Toolbox
└── Landsat Tools
    └── Landsat 8/9 — Thermal & UHI Processor
```

Базовый порядок работы:

1. Скачайте и распакуйте сцену Landsat 8/9 Collection 2 Level-1.
2. Откройте алгоритм в панели Processing Toolbox QGIS.
3. Укажите папку сцены.
4. Выберите режим обработки.
5. Укажите выходную папку.
6. Запустите алгоритм.
7. Проверьте созданные растровые слои и CSV-статистику.

## Исходные данные

Папка сцены должна содержать исходные файлы Landsat:

| Файл или канал | Назначение |
|---|---|
| `*_MTL.txt` | Метаданные сцены и калибровочные коэффициенты |
| Band 4 | Красный канал для NDVI |
| Band 5 | Ближний инфракрасный канал для NDVI |
| Band 6 | Коротковолновый инфракрасный канал для NDBI |
| Band 10 | Тепловой инфракрасный канал для BT и LST |
| `QA_PIXEL` | Опциональная облачная маска |

## Параметры

| Параметр | Описание |
|---|---|
| `Landsat scene folder` | Папка с распакованными файлами сцены Landsat. |
| `Processing mode` | Выбор режима `BT`, `LST` или `LST+UHI`. |
| `QA_PIXEL cloud mask` | Применение облачной маски на основе QA_PIXEL. |
| `Rural NDVI threshold` | NDVI-порог для выбора сельских референсных пикселей. |
| `Export statistics to CSV` | Сохранение сводной статистики в CSV. |
| `Export diagnostic masks` | Сохранение вспомогательных масок для проверки. |
| `Output folder` | Папка для сохранения результатов. |
| `File name prefix` | Дополнительный префикс имён выходных файлов. |

## Выходные файлы

В зависимости от выбранного режима плагин может формировать:

| Результат | Описание |
|---|---|
| `*_BT.tif` | Растр яркостной температуры. |
| `*_LST.tif` | Растр температуры поверхности, °C. |
| `*_NDVI.tif` | Нормализованный разностный вегетационный индекс. |
| `*_NDBI.tif` | Нормализованный разностный индекс застройки. |
| `*_UTFVI.tif` | Классы Urban Thermal Field Variance Index. |
| `*_UHI_diff.tif` | Разница между LST и средней LST сельской зоны, °C. |
| `*_stats.csv` | Сводная статистика сцены. |
| diagnostic masks | Вспомогательные маски валидных, городских и сельских пикселей. |

## Классы UTFVI

| Диапазон UTFVI | Класс |
|---|---|
| `< 0` | Нет UHI |
| `0.000–0.005` | Слабый |
| `0.005–0.010` | Средний |
| `0.010–0.015` | Сильный |
| `0.015–0.020` | Интенсивный |
| `> 0.020` | Экстремальный |

## Структура проекта

```text
landsat_thermal_uhi/
├── __init__.py                   # точка входа QGIS-плагина
├── plugin.py                     # инициализация плагина и регистрация провайдера
├── provider.py                   # провайдер QGIS Processing
├── landsat_thermal_processor.py  # основной алгоритм обработки
├── metadata.txt                  # метаданные QGIS-плагина
├── README.md                     # документация репозитория
├── LICENSE                       # текст лицензии GPL-2.0
├── icons/
│   └── icon.png                  # иконка плагина
└── core/
    ├── constants.py              # константы и названия классов
    ├── io.py                     # поиск файлов, ввод/вывод растров, экспорт CSV
    ├── masks.py                  # QA/cloud-маски и аналитические маски
    ├── physics.py                # тепловые расчёты и эмиссивность
    ├── uhi.py                    # расчёты, связанные с UHI
    ├── validation.py             # проверка входных и выходных данных
    └── visualization.py          # стилизация растров и загрузка слоёв в QGIS
```

## Ограничения

- Плагин рассчитан на структуру файлов и метаданных Landsat Collection 2 Level-1.
- Результаты LST и UHI зависят от атмосферных условий, качества сцены, облачной маски и структуры земного покрова.
- Сельская референсная зона выбирается по NDVI-порогу; для засушливых, горных, прибрежных или сильно фрагментированных территорий порог может требовать настройки.
- Инструмент предназначен для ГИС-анализа и учебно-прикладных задач. Для научной публикации могут потребоваться дополнительная атмосферная коррекция, валидация и оценка неопределённости.

## Лицензия

Плагин распространяется на условиях GNU General Public License, version 2. Текст лицензии находится в файле `LICENSE` внутри пакета плагина.

## Источники

- Sobrino, J. A., Jiménez-Muñoz, J. C., & Paolini, L. (2004). Методика расчёта температуры поверхности по данным Landsat TM 5.
- Guha, S., Govil, H., Dey, A., & Gill, N. (2018). Исследование температуры поверхности, NDVI и NDBI по данным Landsat 8 OLI/TIRS.
- Zha, Y., Gao, J., & Ni, S. (2003). Использование NDBI для автоматического картографирования городских территорий по снимкам TM.
