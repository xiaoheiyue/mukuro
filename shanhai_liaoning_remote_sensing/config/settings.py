"""
山海辽凝遥感影像快速加工处理平台
项目配置文件
"""

# 应用程序信息
APP_NAME = "山海辽凝遥感影像快速加工处理平台"
APP_VERSION = "1.0.0"
APP_AUTHOR = "ShanHaiLiaoNing Team"
APP_ORGANIZATION = "ShanHaiLiaoNing"

# 支持的影像格式
SUPPORTED_FORMATS = {
    'read': [
        '.tif', '.tiff', '.img', '.jp2', '.jpg', '.jpeg',
        '.png', '.bmp', '.hdf', '.nc', '.grd'
    ],
    'write': [
        '.tif', '.tiff', '.img', '.jp2', '.jpg', '.png'
    ]
}

# 默认参数
DEFAULT_PARAMETERS = {
    'ndvi': {
        'nir_band': 4,
        'red_band': 3,
        'scale_factor': 1.0,
        'no_data_value': -9999.0
    },
    'evi': {
        'nir_band': 4,
        'red_band': 3,
        'blue_band': 1,
        'L': 1.0,
        'C1': 6.0,
        'C2': 7.5,
        'G': 2.5
    },
    'classification': {
        'method': 'kmeans',
        'n_classes': 5,
        'max_iterations': 100
    },
    'resampling': {
        'method': 'bilinear',
        'output_resolution': 10.0
    }
}

# UI设置
UI_SETTINGS = {
    'theme': 'dark',
    'language': 'zh_CN',
    'window_width': 1280,
    'window_height': 800,
    'max_recent_files': 5,
    'auto_save_interval': 300
}

# 处理设置
PROCESSING_SETTINGS = {
    'max_threads': 4,
    'chunk_size': 1024,
    'memory_limit_percent': 80,
    'temp_directory': './temp',
    'enable_cache': True
}

# 日志设置
LOGGING_SETTINGS = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'date_format': '%Y-%m-%d %H:%M:%S',
    'log_file': './logs/app.log',
    'max_log_size': 10 * 1024 * 1024,
    'backup_count': 5
}

# 波段组合预设
BAND_COMBINATIONS = {
    'true_color': {'name': '真彩色', 'bands': [3, 2, 1]},
    'false_color': {'name': '标准假彩色', 'bands': [4, 3, 2]},
    'agriculture': {'name': '农业监测', 'bands': [6, 5, 4]},
    'atmospheric': {'name': '大气穿透', 'bands': [7, 6, 4]},
    'natural': {'name': '自然色', 'bands': [5, 4, 3]},
    'color_infrared': {'name': '彩色红外', 'bands': [5, 3, 2]}
}

# 坐标系统预设
COORDINATE_SYSTEMS = {
    'WGS84': {'epsg': 4326, 'name': 'WGS 84', 'type': 'geographic'},
    'WebMercator': {'epsg': 3857, 'name': 'WGS 84 / Pseudo-Mercator', 'type': 'projected'},
    'CGCS2000': {'epsg': 4490, 'name': 'CGCS2000', 'type': 'geographic'},
    'UTM_Zone49N': {'epsg': 32649, 'name': 'WGS 84 / UTM zone 49N', 'type': 'projected'},
    'UTM_Zone50N': {'epsg': 32650, 'name': 'WGS 84 / UTM zone 50N', 'type': 'projected'},
    'UTM_Zone51N': {'epsg': 32651, 'name': 'WGS 84 / UTM zone 51N', 'type': 'projected'},
    'UTM_Zone52N': {'epsg': 32652, 'name': 'WGS 84 / UTM zone 52N', 'type': 'projected'}
}

# 传感器参数预设
SENSOR_PARAMETERS = {
    'Landsat8_OLI': {
        'bands': {
            1: {'name': 'Coastal/Aerosol', 'wavelength': '0.43-0.45 μm', 'resolution': 30},
            2: {'name': 'Blue', 'wavelength': '0.45-0.51 μm', 'resolution': 30},
            3: {'name': 'Green', 'wavelength': '0.53-0.59 μm', 'resolution': 30},
            4: {'name': 'Red', 'wavelength': '0.64-0.67 μm', 'resolution': 30},
            5: {'name': 'NIR', 'wavelength': '0.85-0.88 μm', 'resolution': 30},
            6: {'name': 'SWIR1', 'wavelength': '1.57-1.65 μm', 'resolution': 30},
            7: {'name': 'SWIR2', 'wavelength': '2.11-2.29 μm', 'resolution': 30},
            8: {'name': 'Panchromatic', 'wavelength': '0.50-0.68 μm', 'resolution': 15},
            9: {'name': 'Cirrus', 'wavelength': '1.36-1.38 μm', 'resolution': 30},
            10: {'name': 'TIRS1', 'wavelength': '10.60-11.19 μm', 'resolution': 100},
            11: {'name': 'TIRS2', 'wavelength': '11.50-12.51 μm', 'resolution': 100}
        }
    },
    'Sentinel2_MSI': {
        'bands': {
            1: {'name': 'Coastal', 'wavelength': '0.443 μm', 'resolution': 60},
            2: {'name': 'Blue', 'wavelength': '0.490 μm', 'resolution': 10},
            3: {'name': 'Green', 'wavelength': '0.560 μm', 'resolution': 10},
            4: {'name': 'Red', 'wavelength': '0.665 μm', 'resolution': 10},
            5: {'name': 'Red Edge 1', 'wavelength': '0.705 μm', 'resolution': 20},
            6: {'name': 'Red Edge 2', 'wavelength': '0.740 μm', 'resolution': 20},
            7: {'name': 'Red Edge 3', 'wavelength': '0.783 μm', 'resolution': 20},
            8: {'name': 'NIR', 'wavelength': '0.842 μm', 'resolution': 10},
            81: {'name': 'NIR Narrow', 'wavelength': '0.865 μm', 'resolution': 20},
            9: {'name': 'Water Vapor', 'wavelength': '0.945 μm', 'resolution': 60},
            10: {'name': 'Cirrus', 'wavelength': '1.375 μm', 'resolution': 60},
            11: {'name': 'SWIR1', 'wavelength': '1.610 μm', 'resolution': 20},
            12: {'name': 'SWIR2', 'wavelength': '2.190 μm', 'resolution': 20}
        }
    },
    'GF1_PMS': {
        'bands': {
            1: {'name': 'Blue', 'wavelength': '0.45-0.52 μm', 'resolution': 8},
            2: {'name': 'Green', 'wavelength': '0.52-0.59 μm', 'resolution': 8},
            3: {'name': 'Red', 'wavelength': '0.63-0.69 μm', 'resolution': 8},
            4: {'name': 'NIR', 'wavelength': '0.77-0.89 μm', 'resolution': 8}
        }
    },
    'GF2_PMS': {
        'bands': {
            1: {'name': 'Blue', 'wavelength': '0.45-0.52 μm', 'resolution': 4},
            2: {'name': 'Green', 'wavelength': '0.52-0.59 μm', 'resolution': 4},
            3: {'name': 'Red', 'wavelength': '0.63-0.69 μm', 'resolution': 4},
            4: {'name': 'NIR', 'wavelength': '0.77-0.89 μm', 'resolution': 4}
        }
    }
}

# 快捷键定义
SHORTCUTS = {
    'new_project': 'Ctrl+N',
    'open_file': 'Ctrl+O',
    'save_file': 'Ctrl+S',
    'save_as': 'Ctrl+Shift+S',
    'export': 'Ctrl+E',
    'undo': 'Ctrl+Z',
    'redo': 'Ctrl+Y',
    'zoom_in': 'Ctrl++',
    'zoom_out': 'Ctrl+-',
    'fit_to_window': 'Ctrl+0',
    'quit': 'Ctrl+Q',
    'preferences': 'Ctrl+P',
    'help': 'F1'
}

# 颜色映射预设
COLORMAPS = {
    'ndvi': {'name': 'NDVI', 'colors': ['#8B0000', '#FF0000', '#FFFF00', '#00FF00', '#006400'], 'range': [-1, 1]},
    'elevation': {'name': 'Elevation', 'colors': ['#000080', '#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF0000', '#FFFFFF'], 'range': [0, 1]},
    'temperature': {'name': 'Temperature', 'colors': ['#000080', '#0000FF', '#00FFFF', '#00FF00', '#FFFF00', '#FF0000', '#800000'], 'range': [0, 1]},
    'grayscale': {'name': 'Grayscale', 'colors': ['#000000', '#FFFFFF'], 'range': [0, 1]}
}
