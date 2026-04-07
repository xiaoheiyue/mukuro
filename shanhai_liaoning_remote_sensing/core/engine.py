"""
山海辽凝遥感影像快速加工处理平台
核心引擎模块 - 负责影像数据的核心处理逻辑
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import logging
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class DataType(Enum):
    """数据类型枚举"""
    UINT8 = "uint8"
    UINT16 = "uint16"
    INT16 = "int16"
    FLOAT32 = "float32"
    FLOAT64 = "float64"
    COMPLEX64 = "complex64"
    COMPLEX128 = "complex128"


class BandType(Enum):
    """波段类型枚举"""
    RED = "red"
    GREEN = "green"
    BLUE = "blue"
    NIR = "nir"
    SWIR1 = "swir1"
    SWIR2 = "swir2"
    THERMAL = "thermal"
    PANCHROMATIC = "panchromatic"
    COASTAL = "coastal"
    WATER_VAPOR = "water_vapor"
    CIRRUS = "cirrus"
    UNKNOWN = "unknown"


@dataclass
class GeoTransform:
    """地理变换参数"""
    top_left_x: float = 0.0
    pixel_width: float = 1.0
    rotation_x: float = 0.0
    top_left_y: float = 0.0
    rotation_y: float = 0.0
    pixel_height: float = -1.0

    def to_tuple(self) -> Tuple[float, ...]:
        return (self.top_left_x, self.pixel_width, self.rotation_x,
                self.top_left_y, self.rotation_y, self.pixel_height)

    @classmethod
    def from_tuple(cls, values: Tuple[float, ...]) -> 'GeoTransform':
        return cls(
            top_left_x=values[0],
            pixel_width=values[1],
            rotation_x=values[2],
            top_left_y=values[3],
            rotation_y=values[4],
            pixel_height=values[5]
        )


@dataclass
class CoordinateSystem:
    """坐标系统定义"""
    epsg_code: int = 0
    wkt_string: str = ""
    proj4_string: str = ""
    name: str = ""

    def is_valid(self) -> bool:
        return self.epsg_code > 0 or len(self.wkt_string) > 0


@dataclass
class RasterMetadata:
    """栅格元数据"""
    width: int = 0
    height: int = 0
    band_count: int = 0
    data_type: DataType = DataType.UINT8
    geo_transform: GeoTransform = field(default_factory=GeoTransform)
    coordinate_system: CoordinateSystem = field(default_factory=CoordinateSystem)
    no_data_value: Optional[float] = None
    min_value: float = 0.0
    max_value: float = 0.0
    mean_value: float = 0.0
    std_value: float = 0.0
    acquisition_date: Optional[datetime] = None
    sensor_name: str = ""
    platform_name: str = ""
    cloud_cover: float = 0.0
    sun_elevation: float = 0.0
    sun_azimuth: float = 0.0
    processing_level: str = ""
    file_path: str = ""
    file_size: int = 0
    creation_time: datetime = field(default_factory=datetime.now)
    band_types: List[BandType] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    additional_info: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            'width': self.width,
            'height': self.height,
            'band_count': self.band_count,
            'data_type': self.data_type.value,
            'geo_transform': self.geo_transform.to_tuple(),
            'coordinate_system': {
                'epsg_code': self.coordinate_system.epsg_code,
                'wkt_string': self.coordinate_system.wkt_string,
                'name': self.coordinate_system.name
            },
            'no_data_value': self.no_data_value,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'mean_value': self.mean_value,
            'std_value': self.std_value,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'sensor_name': self.sensor_name,
            'platform_name': self.platform_name,
            'cloud_cover': self.cloud_cover,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'creation_time': self.creation_time.isoformat(),
            'band_types': [bt.value for bt in self.band_types],
            'keywords': self.keywords,
            'additional_info': self.additional_info
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RasterMetadata':
        metadata = cls()
        metadata.width = data.get('width', 0)
        metadata.height = data.get('height', 0)
        metadata.band_count = data.get('band_count', 0)
        metadata.data_type = DataType(data.get('data_type', 'uint8'))
        metadata.geo_transform = GeoTransform.from_tuple(tuple(data.get('geo_transform', (0, 1, 0, 0, 0, -1))))
        cs_data = data.get('coordinate_system', {})
        metadata.coordinate_system = CoordinateSystem(
            epsg_code=cs_data.get('epsg_code', 0),
            wkt_string=cs_data.get('wkt_string', ''),
            name=cs_data.get('name', '')
        )
        metadata.no_data_value = data.get('no_data_value')
        metadata.min_value = data.get('min_value', 0.0)
        metadata.max_value = data.get('max_value', 0.0)
        metadata.mean_value = data.get('mean_value', 0.0)
        metadata.std_value = data.get('std_value', 0.0)
        acq_date = data.get('acquisition_date')
        if acq_date:
            metadata.acquisition_date = datetime.fromisoformat(acq_date)
        metadata.sensor_name = data.get('sensor_name', '')
        metadata.platform_name = data.get('platform_name', '')
        metadata.cloud_cover = data.get('cloud_cover', 0.0)
        metadata.file_path = data.get('file_path', '')
        metadata.file_size = data.get('file_size', 0)
        creation_time = data.get('creation_time')
        if creation_time:
            metadata.creation_time = datetime.fromisoformat(creation_time)
        band_types = data.get('band_types', [])
        metadata.band_types = [BandType(bt) for bt in band_types if bt in [e.value for e in BandType]]
        metadata.keywords = data.get('keywords', [])
        metadata.additional_info = data.get('additional_info', {})
        return metadata


class RasterBand:
    """栅格波段类"""

    def __init__(self, data: np.ndarray, band_index: int = 1,
                 band_type: BandType = BandType.UNKNOWN,
                 metadata: Optional[Dict[str, Any]] = None):
        self.data = data
        self.band_index = band_index
        self.band_type = band_type
        self.metadata = metadata or {}
        self._statistics_cached = False
        self._min = None
        self._max = None
        self._mean = None
        self._std = None
        self._histogram = None

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.data.shape

    @property
    def dtype(self) -> np.dtype:
        return self.data.dtype

    @property
    def size(self) -> int:
        return self.data.size

    def calculate_statistics(self, force: bool = False) -> Dict[str, float]:
        """计算波段统计信息"""
        if self._statistics_cached and not force:
            return {
                'min': self._min,
                'max': self._max,
                'mean': self._mean,
                'std': self._std
            }

        valid_data = self.data
        if 'no_data_value' in self.metadata:
            valid_data = self.data[self.data != self.metadata['no_data_value']]

        if valid_data.size == 0:
            logger.warning("No valid data for statistics calculation")
            return {'min': 0.0, 'max': 0.0, 'mean': 0.0, 'std': 0.0}

        self._min = float(np.min(valid_data))
        self._max = float(np.max(valid_data))
        self._mean = float(np.mean(valid_data))
        self._std = float(np.std(valid_data))
        self._statistics_cached = True

        return {
            'min': self._min,
            'max': self._max,
            'mean': self._mean,
            'std': self._std
        }

    def get_histogram(self, bins: int = 256, normalize: bool = False) -> np.ndarray:
        """获取直方图"""
        if self._histogram is not None and self._histogram.shape[0] == bins:
            histogram = self._histogram.copy()
        else:
            valid_data = self.data.flatten()
            if 'no_data_value' in self.metadata:
                valid_data = valid_data[valid_data != self.metadata['no_data_value']]

            if valid_data.size == 0:
                return np.zeros(bins)

            histogram, _ = np.histogram(valid_data, bins=bins, range=(self._min or 0, self._max or 255))
            self._histogram = histogram

        if normalize:
            histogram = histogram.astype(float) / histogram.sum()

        return histogram

    def normalize(self, method: str = 'min_max') -> 'RasterBand':
        """归一化波段数据"""
        if method == 'min_max':
            stats = self.calculate_statistics()
            if stats['max'] - stats['min'] == 0:
                normalized_data = np.zeros_like(self.data, dtype=float)
            else:
                normalized_data = (self.data - stats['min']) / (stats['max'] - stats['min'])
        elif method == 'z_score':
            stats = self.calculate_statistics()
            if stats['std'] == 0:
                normalized_data = np.zeros_like(self.data, dtype=float)
            else:
                normalized_data = (self.data - stats['mean']) / stats['std']
        else:
            raise ValueError(f"Unknown normalization method: {method}")

        return RasterBand(
            data=normalized_data,
            band_index=self.band_index,
            band_type=self.band_type,
            metadata=self.metadata.copy()
        )

    def clip(self, min_value: Optional[float] = None, max_value: Optional[float] = None) -> 'RasterBand':
        """裁剪波段值范围"""
        clipped_data = self.data.copy()
        if min_value is not None:
            clipped_data = np.clip(clipped_data, min_value, None)
        if max_value is not None:
            clipped_data = np.clip(clipped_data, None, max_value)

        return RasterBand(
            data=clipped_data,
            band_index=self.band_index,
            band_type=self.band_type,
            metadata=self.metadata.copy()
        )

    def apply_mask(self, mask: np.ndarray) -> 'RasterBand':
        """应用掩膜"""
        if mask.shape != self.data.shape:
            raise ValueError("Mask shape must match data shape")

        masked_data = np.ma.masked_array(self.data, mask=mask)
        return RasterBand(
            data=masked_data,
            band_index=self.band_index,
            band_type=self.band_type,
            metadata=self.metadata.copy()
        )


class RasterDataset:
    """栅格数据集类"""

    def __init__(self, metadata: RasterMetadata):
        self.metadata = metadata
        self.bands: Dict[int, RasterBand] = {}
        self.pyramids: List[np.ndarray] = []
        self.overviews: Dict[int, RasterDataset] = {}
        self._lock = None  # 用于线程安全

    def add_band(self, band: RasterBand) -> None:
        """添加波段"""
        self.bands[band.band_index] = band

    def get_band(self, band_index: int) -> Optional[RasterBand]:
        """获取指定波段"""
        return self.bands.get(band_index)

    def get_band_by_type(self, band_type: BandType) -> Optional[RasterBand]:
        """根据波段类型获取波段"""
        for band in self.bands.values():
            if band.band_type == band_type:
                return band
        return None

    def get_rgb_composite(self, red_index: int = 1, green_index: int = 2,
                          blue_index: int = 3) -> Optional[np.ndarray]:
        """获取RGB合成图像"""
        red_band = self.get_band(red_index)
        green_band = self.get_band(green_index)
        blue_band = self.get_band(blue_index)

        if not all([red_band, green_band, blue_band]):
            return None

        # 归一化到0-1范围
        red_norm = red_band.normalize().data
        green_norm = green_band.normalize().data
        blue_norm = blue_band.normalize().data

        # 堆叠为RGB图像
        rgb_data = np.stack([red_norm, green_norm, blue_norm], axis=-1)
        return np.clip(rgb_data, 0, 1)

    def get_false_color_composite(self) -> Optional[np.ndarray]:
        """获取假彩色合成图像（标准假彩色：NIR, Red, Green）"""
        nir_band = self.get_band_by_type(BandType.NIR)
        red_band = self.get_band_by_type(BandType.RED)
        green_band = self.get_band_by_type(BandType.GREEN)

        if not all([nir_band, red_band, green_band]):
            # 尝试使用波段索引
            nir_band = self.get_band(4)
            red_band = self.get_band(3)
            green_band = self.get_band(2)

        if not all([nir_band, red_band, green_band]):
            return None

        nir_norm = nir_band.normalize().data
        red_norm = red_band.normalize().data
        green_norm = green_band.normalize().data

        false_color = np.stack([nir_norm, red_norm, green_norm], axis=-1)
        return np.clip(false_color, 0, 1)

    def calculate_overview(self, level: int) -> RasterDataset:
        """计算概览图层"""
        if level <= 0:
            return self

        scale_factor = 2 ** level
        new_width = max(1, self.metadata.width // scale_factor)
        new_height = max(1, self.metadata.height // scale_factor)

        overview_metadata = RasterMetadata(
            width=new_width,
            height=new_height,
            band_count=self.metadata.band_count,
            data_type=self.metadata.data_type,
            geo_transform=GeoTransform(
                top_left_x=self.metadata.geo_transform.top_left_x,
                pixel_width=self.metadata.geo_transform.pixel_width * scale_factor,
                rotation_x=self.metadata.geo_transform.rotation_x,
                top_left_y=self.metadata.geo_transform.top_left_y,
                rotation_y=self.metadata.geo_transform.rotation_y,
                pixel_height=self.metadata.geo_transform.pixel_height * scale_factor
            ),
            coordinate_system=self.metadata.coordinate_system,
            no_data_value=self.metadata.no_data_value
        )

        overview_dataset = RasterDataset(overview_metadata)

        for band_index, band in self.bands.items():
            # 使用平均池化进行降采样
            data = band.data
            if len(data.shape) == 2:
                data = data.reshape(1, data.shape[0], data.shape[1])

            # 简单的降采样实现
            h, w = data.shape[-2:]
            new_h, new_w = min(h, new_height), min(w, new_width)

            step_h = h // new_h
            step_w = w // new_w

            downsampled = np.zeros((data.shape[0], new_h, new_w), dtype=data.dtype)
            for i in range(new_h):
                for j in range(new_w):
                    start_h = i * step_h
                    end_h = min(start_h + step_h, h)
                    start_w = j * step_w
                    end_w = min(start_w + step_w, w)
                    downsampled[:, i, j] = np.mean(data[:, start_h:end_h, start_w:end_w], axis=(1, 2))

            if downsampled.shape[0] == 1:
                downsampled = downsampled[0]

            overview_band = RasterBand(
                data=downsampled,
                band_index=band_index,
                band_type=band.band_type,
                metadata=band.metadata.copy()
            )
            overview_dataset.add_band(overview_band)

        self.overviews[level] = overview_dataset
        return overview_dataset

    def get_pixel_value(self, x: int, y: int, band_indices: Optional[List[int]] = None) -> Dict[int, float]:
        """获取指定位置的像素值"""
        if band_indices is None:
            band_indices = list(self.bands.keys())

        values = {}
        for band_index in band_indices:
            band = self.get_band(band_index)
            if band and 0 <= y < band.data.shape[0] and 0 <= x < band.data.shape[1]:
                values[band_index] = float(band.data[y, x])

        return values

    def get_geographic_coordinates(self, pixel_x: int, pixel_y: int) -> Tuple[float, float]:
        """将像素坐标转换为地理坐标"""
        gt = self.metadata.geo_transform
        geo_x = gt.top_left_x + pixel_x * gt.pixel_width + pixel_y * gt.rotation_x
        geo_y = gt.top_left_y + pixel_x * gt.rotation_y + pixel_y * gt.pixel_height
        return geo_x, geo_y

    def get_pixel_coordinates(self, geo_x: float, geo_y: float) -> Tuple[int, int]:
        """将地理坐标转换为像素坐标"""
        gt = self.metadata.geo_transform
        if abs(gt.rotation_x) < 1e-10 and abs(gt.rotation_y) < 1e-10:
            pixel_x = int((geo_x - gt.top_left_x) / gt.pixel_width)
            pixel_y = int((geo_y - gt.top_left_y) / gt.pixel_height)
        else:
            det = gt.pixel_width * gt.pixel_height - gt.rotation_x * gt.rotation_y
            if abs(det) < 1e-10:
                raise ValueError("Invalid geo transform")
            pixel_x = int((gt.pixel_height * (geo_x - gt.top_left_x) - gt.rotation_x * (geo_y - gt.top_left_y)) / det)
            pixel_y = int((-gt.rotation_y * (geo_x - gt.top_left_x) + gt.pixel_width * (geo_y - gt.top_left_y)) / det)
        return pixel_x, pixel_y

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'metadata': self.metadata.to_dict(),
            'bands': {k: {'index': v.band_index, 'type': v.band_type.value, 'shape': v.shape}
                      for k, v in self.bands.items()}
        }


class ProcessingAlgorithm(ABC):
    """处理算法基类"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.parameters: Dict[str, Any] = {}
        self.progress_callback = None
        self.log_callback = None

    def set_parameter(self, key: str, value: Any) -> None:
        self.parameters[key] = value

    def get_parameter(self, key: str, default: Any = None) -> Any:
        return self.parameters.get(key, default)

    def set_progress_callback(self, callback) -> None:
        self.progress_callback = callback

    def set_log_callback(self, callback) -> None:
        self.log_callback = callback

    def _report_progress(self, progress: float, message: str = "") -> None:
        if self.progress_callback:
            self.progress_callback(progress, message)

    def _log_message(self, level: str, message: str) -> None:
        if self.log_callback:
            self.log_callback(level, message)
        else:
            getattr(logger, level.lower(), logger.info)(f"[{self.name}] {message}")

    @abstractmethod
    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        """执行算法"""
        pass

    @abstractmethod
    def validate_parameters(self) -> Tuple[bool, str]:
        """验证参数"""
        pass


class AlgorithmRegistry:
    """算法注册表"""

    _instance = None
    _algorithms: Dict[str, ProcessingAlgorithm] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def register(self, algorithm: ProcessingAlgorithm) -> None:
        self._algorithms[algorithm.name] = algorithm

    def unregister(self, name: str) -> bool:
        if name in self._algorithms:
            del self._algorithms[name]
            return True
        return False

    def get_algorithm(self, name: str) -> Optional[ProcessingAlgorithm]:
        return self._algorithms.get(name)

    def list_algorithms(self) -> List[str]:
        return list(self._algorithms.keys())

    def get_algorithm_info(self, name: str) -> Optional[Dict[str, Any]]:
        algorithm = self._algorithms.get(name)
        if algorithm:
            return {
                'name': algorithm.name,
                'description': algorithm.description,
                'parameters': algorithm.parameters.copy()
            }
        return None


class ProcessingEngine:
    """处理引擎"""

    def __init__(self):
        self.algorithm_registry = AlgorithmRegistry()
        self.processing_queue: List[Tuple[ProcessingAlgorithm, RasterDataset]] = []
        self.results: Dict[str, RasterDataset] = {}
        self.is_processing = False
        self.current_algorithm: Optional[ProcessingAlgorithm] = None
        self._cancel_requested = False

    def add_to_queue(self, algorithm: ProcessingAlgorithm, dataset: RasterDataset) -> None:
        self.processing_queue.append((algorithm, dataset))

    def clear_queue(self) -> None:
        self.processing_queue.clear()

    def cancel_processing(self) -> None:
        self._cancel_requested = True

    def process_queue(self, progress_callback=None, log_callback=None) -> Dict[str, RasterDataset]:
        """处理队列中的所有任务"""
        self.is_processing = True
        self._cancel_requested = False
        total_tasks = len(self.processing_queue)

        for idx, (algorithm, dataset) in enumerate(self.processing_queue):
            if self._cancel_requested:
                self._log_message(log_callback, 'warning', 'Processing cancelled by user')
                break

            self.current_algorithm = algorithm
            algorithm.set_progress_callback(
                lambda p, m, i=idx: self._on_progress(i, total_tasks, p, m, progress_callback)
            )
            algorithm.set_log_callback(
                lambda l, m: self._on_log(l, m, log_callback)
            )

            try:
                result = algorithm.execute(dataset)
                result_key = f"{algorithm.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                self.results[result_key] = result
            except Exception as e:
                self._log_message(log_callback, 'error', f'Error executing {algorithm.name}: {str(e)}')
                continue

        self.is_processing = False
        self.current_algorithm = None
        self.processing_queue.clear()
        return self.results

    def _on_progress(self, task_idx: int, total_tasks: int, progress: float,
                     message: str, callback=None) -> None:
        overall_progress = (task_idx + progress) / total_tasks
        if callback:
            callback(overall_progress, f"Task {task_idx + 1}/{total_tasks}: {message}")

    def _on_log(self, level: str, message: str, callback=None) -> None:
        if callback:
            callback(level, message)
        else:
            getattr(logger, level.lower(), logger.info)(message)

    def _log_message(self, callback, level: str, message: str) -> None:
        if callback:
            callback(level, message)
        else:
            getattr(logger, level.lower(), logger.info)(message)

    def get_result(self, key: str) -> Optional[RasterDataset]:
        return self.results.get(key)

    def clear_results(self) -> None:
        self.results.clear()


class DataManager:
    """数据管理器"""

    def __init__(self):
        self.datasets: Dict[str, RasterDataset] = {}
        self.active_dataset: Optional[RasterDataset] = None
        self.history: List[Dict[str, Any]] = []
        self.max_history_size = 100

    def load_dataset(self, path: str, **kwargs) -> RasterDataset:
        """加载数据集"""
        if path in self.datasets:
            return self.datasets[path]

        # 这里应该调用实际的读取器，暂时创建模拟数据
        metadata = RasterMetadata(
            width=kwargs.get('width', 1000),
            height=kwargs.get('height', 1000),
            band_count=kwargs.get('band_count', 3),
            file_path=path
        )

        dataset = RasterDataset(metadata)

        # 创建模拟波段数据
        for i in range(metadata.band_count):
            band_data = np.random.randint(0, 255, (metadata.height, metadata.width), dtype=np.uint8)
            band = RasterBand(
                data=band_data,
                band_index=i + 1,
                band_type=list(BandType)[i % len(list(BandType))]
            )
            dataset.add_band(band)

        self.datasets[path] = dataset
        self.active_dataset = dataset
        self._add_to_history('load', path)

        return dataset

    def save_dataset(self, dataset: RasterDataset, path: str, format: str = 'GTiff') -> bool:
        """保存数据集"""
        # 实际实现应该调用写入器
        self._add_to_history('save', path)
        return True

    def remove_dataset(self, path: str) -> bool:
        """移除数据集"""
        if path in self.datasets:
            del self.datasets[path]
            if self.active_dataset and self.active_dataset.metadata.file_path == path:
                self.active_dataset = next(iter(self.datasets.values()), None)
            self._add_to_history('remove', path)
            return True
        return False

    def set_active_dataset(self, path: str) -> bool:
        """设置活动数据集"""
        if path in self.datasets:
            self.active_dataset = self.datasets[path]
            return True
        return False

    def get_active_dataset(self) -> Optional[RasterDataset]:
        return self.active_dataset

    def list_datasets(self) -> List[str]:
        return list(self.datasets.keys())

    def _add_to_history(self, action: str, details: str) -> None:
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action': action,
            'details': details
        }
        self.history.append(entry)
        if len(self.history) > self.max_history_size:
            self.history.pop(0)

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        return self.history[-limit:]

    def clear_history(self) -> None:
        self.history.clear()

    def export_metadata(self, path: str) -> bool:
        """导出元数据"""
        if not self.active_dataset:
            return False

        metadata_dict = self.active_dataset.to_dict()
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=2, ensure_ascii=False)

        return True

    def import_metadata(self, path: str) -> Optional[RasterMetadata]:
        """导入元数据"""
        with open(path, 'r', encoding='utf-8') as f:
            metadata_dict = json.load(f)

        return RasterMetadata.from_dict(metadata_dict)


__all__ = [
    'DataType',
    'BandType',
    'GeoTransform',
    'CoordinateSystem',
    'RasterMetadata',
    'RasterBand',
    'RasterDataset',
    'ProcessingAlgorithm',
    'AlgorithmRegistry',
    'ProcessingEngine',
    'DataManager'
]
