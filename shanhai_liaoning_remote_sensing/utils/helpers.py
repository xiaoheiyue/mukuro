"""
山海辽凝遥感影像快速加工处理平台
工具函数模块
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import numpy as np

logger = logging.getLogger(__name__)


def setup_logging(log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """设置日志系统"""
    logger = logging.getLogger('ShanHaiLiaoNing')
    logger.setLevel(level)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_project_root() -> str:
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_data_directory() -> str:
    """获取数据目录"""
    data_dir = os.path.join(get_project_root(), 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def get_temp_directory() -> str:
    """获取临时目录"""
    temp_dir = os.path.join(get_project_root(), 'temp')
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir


def get_config_directory() -> str:
    """获取配置目录"""
    config_dir = os.path.join(get_project_root(), 'config')
    os.makedirs(config_dir, exist_ok=True)
    return config_dir


def validate_file_path(file_path: str, extensions: Optional[List[str]] = None) -> bool:
    """验证文件路径"""
    if not file_path:
        return False

    if not os.path.exists(file_path):
        return False

    if extensions:
        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext not in [ext.lower() for ext in extensions]:
            return False

    return True


def get_file_size(file_path: str) -> int:
    """获取文件大小（字节）"""
    if os.path.exists(file_path):
        return os.path.getsize(file_path)
    return 0


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} PB"


def calculate_memory_requirement(width: int, height: int, bands: int, dtype: str = 'float64') -> int:
    """计算内存需求（字节）"""
    dtype_sizes = {
        'uint8': 1,
        'uint16': 2,
        'int16': 2,
        'float32': 4,
        'float64': 8,
        'complex64': 8,
        'complex128': 16
    }
    bytes_per_pixel = dtype_sizes.get(dtype, 8)
    return width * height * bands * bytes_per_pixel


def check_memory_availability(required_bytes: int) -> bool:
    """检查内存是否足够"""
    try:
        import psutil
        available_memory = psutil.virtual_memory().available
        return available_memory > required_bytes
    except ImportError:
        logger.warning("psutil not installed, skipping memory check")
        return True


def create_pyramid_levels(width: int, height: int, max_level: int = 10) -> List[Tuple[int, int]]:
    """创建金字塔层级"""
    levels = []
    current_width, current_height = width, height

    for level in range(max_level):
        if current_width < 2 or current_height < 2:
            break
        levels.append((current_width, current_height))
        current_width //= 2
        current_height //= 2

    return levels


def interpolate_no_data(data: np.ndarray, no_data_value: float, method: str = 'nearest') -> np.ndarray:
    """插值填充无效数据"""
    from scipy import interpolate

    mask = data == no_data_value
    if not np.any(mask):
        return data

    x = np.arange(data.shape[1])
    y = np.arange(data.shape[0])
    xx, yy = np.meshgrid(x, y)

    valid_mask = ~mask
    valid_x = xx[valid_mask]
    valid_y = yy[valid_mask]
    valid_values = data[valid_mask]

    if len(valid_values) == 0:
        return data

    if method == 'nearest':
        grid = interpolate.griddata(
            (valid_x, valid_y), valid_values,
            (xx, yy), method='nearest'
        )
    elif method == 'linear':
        grid = interpolate.griddata(
            (valid_x, valid_y), valid_values,
            (xx, yy), method='linear'
        )
    else:
        grid = data

    data[mask] = grid[mask]
    return data


def rescale_data(data: np.ndarray, old_range: Tuple[float, float],
                 new_range: Tuple[float, float]) -> np.ndarray:
    """重缩放数据范围"""
    old_min, old_max = old_range
    new_min, new_max = new_range

    if old_max - old_min == 0:
        return np.full_like(data, new_min)

    scaled = (data - old_min) / (old_max - old_min)
    return scaled * (new_max - new_min) + new_min


def calculate_entropy(data: np.ndarray) -> float:
    """计算图像熵"""
    hist, _ = np.histogram(data.flatten(), bins=256, range=(data.min(), data.max()))
    hist = hist[hist > 0]
    probabilities = hist / hist.sum()
    entropy = -np.sum(probabilities * np.log2(probabilities))
    return entropy


def calculate_contrast(data: np.ndarray) -> float:
    """计算图像对比度"""
    return float(np.std(data))


def calculate_homogeneity(data: np.ndarray) -> float:
    """计算图像均匀性"""
    mean = np.mean(data)
    std = np.std(data)
    if std == 0:
        return 1.0
    return 1.0 / (1.0 + std / mean)


def save_configuration(config: Dict[str, Any], file_path: str) -> bool:
    """保存配置"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False, default=str)
        return True
    except Exception as e:
        logger.error(f"Failed to save configuration: {str(e)}")
        return False


def load_configuration(file_path: str) -> Dict[str, Any]:
    """加载配置"""
    if not os.path.exists(file_path):
        return {}

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load configuration: {str(e)}")
        return {}


def get_timestamp_string(format_str: str = '%Y%m%d_%H%M%S') -> str:
    """获取时间戳字符串"""
    return datetime.now().strftime(format_str)


def parse_coordinate_string(coord_str: str) -> Tuple[float, float]:
    """解析坐标字符串"""
    parts = coord_str.replace(',', ' ').split()
    if len(parts) >= 2:
        return float(parts[0]), float(parts[1])
    raise ValueError(f"Invalid coordinate string: {coord_str}")


def format_coordinate(x: float, y: float, precision: int = 4) -> str:
    """格式化坐标"""
    return f"{x:.{precision}f}, {y:.{precision}f}"


def clamp(value: float, min_value: float, max_value: float) -> float:
    """限制值范围"""
    return max(min_value, min(value, max_value))


def lerp(start: float, end: float, t: float) -> float:
    """线性插值"""
    return start + t * (end - start)


def smooth_step(edge0: float, edge1: float, x: float) -> float:
    """平滑步进"""
    t = clamp((x - edge0) / (edge1 - edge0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def gaussian_kernel(size: int, sigma: float = 1.0) -> np.ndarray:
    """生成高斯核"""
    ax = np.linspace(-(size // 2), size // 2, size)
    xx, yy = np.meshgrid(ax, ax)
    kernel = np.exp(-0.5 * (xx**2 + yy**2) / sigma**2)
    return kernel / np.sum(kernel)


def apply_gaussian_blur(data: np.ndarray, kernel_size: int = 3, sigma: float = 1.0) -> np.ndarray:
    """应用高斯模糊"""
    from scipy.ndimage import gaussian_filter
    return gaussian_filter(data, sigma=sigma)


def apply_median_filter(data: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """应用中值滤波"""
    from scipy.ndimage import median_filter
    return median_filter(data, size=kernel_size)


def apply_sobel_edge_detection(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """应用Sobel边缘检测"""
    from scipy.ndimage import sobel
    dx = sobel(data, axis=1)
    dy = sobel(data, axis=0)
    return dx, dy


def calculate_slope_aspect(dem: np.ndarray, cell_size: float = 1.0) -> Tuple[np.ndarray, np.ndarray]:
    """计算坡度和坡向"""
    from scipy.ndimage import gradient

    dz_dy, dz_dx = gradient(dem, cell_size)

    slope = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2)) * 180 / np.pi
    aspect = np.arctan2(-dz_dx, dz_dy) * 180 / np.pi
    aspect = np.where(aspect < 0, aspect + 360, aspect)

    return slope, aspect


def ndvi_calculate(nir: np.ndarray, red: np.ndarray) -> np.ndarray:
    """计算NDVI"""
    denominator = nir + red
    ndvi = np.zeros_like(nir, dtype=float)
    valid_mask = denominator != 0
    ndvi[valid_mask] = (nir[valid_mask] - red[valid_mask]) / denominator[valid_mask]
    return ndvi


def ndwi_calculate(green: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """计算NDWI（归一化水体指数）"""
    denominator = green + nir
    ndwi = np.zeros_like(green, dtype=float)
    valid_mask = denominator != 0
    ndwi[valid_mask] = (green[valid_mask] - nir[valid_mask]) / denominator[valid_mask]
    return ndwi


def savi_calculate(nir: np.ndarray, red: np.ndarray, L: float = 0.5) -> np.ndarray:
    """计算SAVI（土壤调节植被指数）"""
    denominator = nir + red + L
    savi = np.zeros_like(nir, dtype=float)
    valid_mask = denominator != 0
    savi[valid_mask] = ((nir[valid_mask] - red[valid_mask]) / denominator[valid_mask]) * (1 + L)
    return savi


def batch_process_files(file_paths: List[str], processor_func, output_dir: str,
                        progress_callback=None) -> List[str]:
    """批量处理文件"""
    results = []
    total = len(file_paths)

    for idx, file_path in enumerate(file_paths):
        try:
            if progress_callback:
                progress_callback(idx / total, f"Processing {os.path.basename(file_path)}")

            result = processor_func(file_path)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {str(e)}")

    return results


def merge_dicts(*dicts: Dict) -> Dict:
    """合并多个字典"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


def deep_copy_dict(d: Dict) -> Dict:
    """深度复制字典"""
    return json.loads(json.dumps(d, default=str))


def flatten_list(nested_list: List) -> List:
    """展平嵌套列表"""
    result = []
    for item in nested_list:
        if isinstance(item, list):
            result.extend(flatten_list(item))
        else:
            result.append(item)
    return result


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分块"""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def unique_preserve_order(lst: List) -> List:
    """去重并保持顺序"""
    seen = set()
    result = []
    for item in lst:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


def safe_divide(a: float, b: float, default: float = 0.0) -> float:
    """安全除法"""
    if b == 0:
        return default
    return a / b


def normalize_angle(angle: float) -> float:
    """规范化角度到0-360度"""
    angle = angle % 360
    return angle if angle >= 0 else angle + 360


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """计算球面距离（米）"""
    R = 6371000  # 地球半径（米）

    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    delta_lat = np.radians(lat2 - lat1)
    delta_lon = np.radians(lon2 - lon1)

    a = np.sin(delta_lat / 2) ** 2 + \
        np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(delta_lon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

    return R * c


__all__ = [
    'setup_logging',
    'get_project_root',
    'get_data_directory',
    'get_temp_directory',
    'get_config_directory',
    'validate_file_path',
    'get_file_size',
    'format_file_size',
    'calculate_memory_requirement',
    'check_memory_availability',
    'create_pyramid_levels',
    'interpolate_no_data',
    'rescale_data',
    'calculate_entropy',
    'calculate_contrast',
    'calculate_homogeneity',
    'save_configuration',
    'load_configuration',
    'get_timestamp_string',
    'parse_coordinate_string',
    'format_coordinate',
    'clamp',
    'lerp',
    'smooth_step',
    'gaussian_kernel',
    'apply_gaussian_blur',
    'apply_median_filter',
    'apply_sobel_edge_detection',
    'calculate_slope_aspect',
    'ndvi_calculate',
    'ndwi_calculate',
    'savi_calculate',
    'batch_process_files',
    'merge_dicts',
    'deep_copy_dict',
    'flatten_list',
    'chunk_list',
    'unique_preserve_order',
    'safe_divide',
    'normalize_angle',
    'haversine_distance'
]
