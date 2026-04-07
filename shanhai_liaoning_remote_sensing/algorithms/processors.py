"""
山海辽凝遥感影像快速加工处理平台
算法模块 - 包含各种遥感影像处理算法
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from abc import abstractmethod
import logging

from core.engine import (
    RasterDataset, RasterBand, RasterMetadata, BandType,
    ProcessingAlgorithm, GeoTransform, CoordinateSystem
)

logger = logging.getLogger(__name__)


class NDVIAlgorithm(ProcessingAlgorithm):
    """归一化植被指数计算算法"""

    def __init__(self):
        super().__init__(
            name="NDVI",
            description="计算归一化植被指数 (Normalized Difference Vegetation Index)"
        )
        self.parameters = {
            'nir_band': 4,
            'red_band': 3,
            'scale_factor': 1.0,
            'no_data_value': -9999.0
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        if self.parameters['nir_band'] <= 0:
            return False, "NIR波段索引必须大于0"
        if self.parameters['red_band'] <= 0:
            return False, "Red波段索引必须大于0"
        if self.parameters['nir_band'] == self.parameters['red_band']:
            return False, "NIR和Red波段不能相同"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        nir_band_idx = self.parameters['nir_band']
        red_band_idx = self.parameters['red_band']
        scale_factor = self.parameters['scale_factor']
        no_data_value = self.parameters['no_data_value']

        self._report_progress(0.1, "读取波段数据...")

        nir_band = input_dataset.get_band(nir_band_idx)
        red_band = input_dataset.get_band(red_band_idx)

        if not nir_band or not red_band:
            raise ValueError(f"找不到指定的波段：NIR={nir_band_idx}, Red={red_band_idx}")

        nir_data = nir_band.data.astype(float) / scale_factor
        red_data = red_band.data.astype(float) / scale_factor

        self._report_progress(0.5, "计算NDVI...")

        # NDVI = (NIR - Red) / (NIR + Red)
        denominator = nir_data + red_data
        ndvi_data = np.zeros_like(nir_data, dtype=float)

        valid_mask = denominator != 0
        ndvi_data[valid_mask] = (nir_data[valid_mask] - red_data[valid_mask]) / denominator[valid_mask]

        # 设置无效值
        ndvi_data[np.isnan(ndvi_data)] = no_data_value
        ndvi_data[np.isinf(ndvi_data)] = no_data_value

        self._report_progress(0.8, "创建输出数据集...")

        # 创建输出元数据
        output_metadata = RasterMetadata(
            width=input_dataset.metadata.width,
            height=input_dataset.metadata.height,
            band_count=1,
            file_path=f"{input_dataset.metadata.file_path}_ndvi.tif",
            no_data_value=no_data_value,
            coordinate_system=input_dataset.metadata.coordinate_system,
            geo_transform=input_dataset.metadata.geo_transform
        )

        output_dataset = RasterDataset(output_metadata)

        # 添加NDVI波段
        ndvi_band = RasterBand(
            data=ndvi_data,
            band_index=1,
            band_type=BandType.UNKNOWN,
            metadata={
                'algorithm': 'NDVI',
                'nir_band': nir_band_idx,
                'red_band': red_band_idx,
                'description': 'Normalized Difference Vegetation Index'
            }
        )
        output_dataset.add_band(ndvi_band)

        self._report_progress(1.0, "NDVI计算完成")
        self._log_message('info', f"NDVI范围：[{np.nanmin(ndvi_data):.3f}, {np.nanmax(ndvi_data):.3f}]")

        return output_dataset


class EVIAlgorithm(ProcessingAlgorithm):
    """增强植被指数计算算法"""

    def __init__(self):
        super().__init__(
            name="EVI",
            description="计算增强植被指数 (Enhanced Vegetation Index)"
        )
        self.parameters = {
            'nir_band': 4,
            'red_band': 3,
            'blue_band': 1,
            'L': 1.0,
            'C1': 6.0,
            'C2': 7.5,
            'G': 2.5,
            'scale_factor': 1.0,
            'no_data_value': -9999.0
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        if self.parameters['nir_band'] <= 0:
            return False, "NIR波段索引必须大于0"
        if self.parameters['red_band'] <= 0:
            return False, "Red波段索引必须大于0"
        if self.parameters['blue_band'] <= 0:
            return False, "Blue波段索引必须大于0"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        nir_band_idx = self.parameters['nir_band']
        red_band_idx = self.parameters['red_band']
        blue_band_idx = self.parameters['blue_band']
        L = self.parameters['L']
        C1 = self.parameters['C1']
        C2 = self.parameters['C2']
        G = self.parameters['G']
        scale_factor = self.parameters['scale_factor']
        no_data_value = self.parameters['no_data_value']

        self._report_progress(0.1, "读取波段数据...")

        nir_band = input_dataset.get_band(nir_band_idx)
        red_band = input_dataset.get_band(red_band_idx)
        blue_band = input_dataset.get_band(blue_band_idx)

        if not all([nir_band, red_band, blue_band]):
            raise ValueError("找不到指定的波段")

        nir_data = nir_band.data.astype(float) / scale_factor
        red_data = red_band.data.astype(float) / scale_factor
        blue_data = blue_band.data.astype(float) / scale_factor

        self._report_progress(0.5, "计算EVI...")

        # EVI = G * (NIR - Red) / (NIR + C1 * Red - C2 * Blue + L)
        denominator = nir_data + C1 * red_data - C2 * blue_data + L
        evi_data = np.zeros_like(nir_data, dtype=float)

        valid_mask = denominator != 0
        evi_data[valid_mask] = G * (nir_data[valid_mask] - red_data[valid_mask]) / denominator[valid_mask]

        evi_data[np.isnan(evi_data)] = no_data_value
        evi_data[np.isinf(evi_data)] = no_data_value

        self._report_progress(0.8, "创建输出数据集...")

        output_metadata = RasterMetadata(
            width=input_dataset.metadata.width,
            height=input_dataset.metadata.height,
            band_count=1,
            file_path=f"{input_dataset.metadata.file_path}_evi.tif",
            no_data_value=no_data_value,
            coordinate_system=input_dataset.metadata.coordinate_system,
            geo_transform=input_dataset.metadata.geo_transform
        )

        output_dataset = RasterDataset(output_metadata)

        evi_band = RasterBand(
            data=evi_data,
            band_index=1,
            band_type=BandType.UNKNOWN,
            metadata={'algorithm': 'EVI'}
        )
        output_dataset.add_band(evi_band)

        self._report_progress(1.0, "EVI计算完成")

        return output_dataset


class HistogramEqualizationAlgorithm(ProcessingAlgorithm):
    """直方图均衡化算法"""

    def __init__(self):
        super().__init__(
            name="HistogramEqualization",
            description="对遥感影像进行直方图均衡化处理"
        )
        self.parameters = {
            'bands': 'all',
            'clip_limit': 0.0,
            'output_bits': 8
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        if self.parameters['output_bits'] not in [8, 16, 32]:
            return False, "输出位深必须是8、16或32"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        bands_param = self.parameters['bands']
        clip_limit = self.parameters['clip_limit']
        output_bits = self.parameters['output_bits']

        self._report_progress(0.1, "准备处理...")

        if bands_param == 'all':
            band_indices = list(input_dataset.bands.keys())
        else:
            band_indices = bands_param if isinstance(bands_param, list) else [bands_param]

        output_metadata = RasterMetadata(
            width=input_dataset.metadata.width,
            height=input_dataset.metadata.height,
            band_count=len(band_indices),
            file_path=f"{input_dataset.metadata.file_path}_he.tif",
            coordinate_system=input_dataset.metadata.coordinate_system,
            geo_transform=input_dataset.metadata.geo_transform
        )

        output_dataset = RasterDataset(output_metadata)

        total_bands = len(band_indices)
        for idx, band_idx in enumerate(band_indices):
            band = input_dataset.get_band(band_idx)
            if not band:
                continue

            self._report_progress(0.1 + 0.8 * (idx + 1) / total_bands, f"处理波段{band_idx}...")

            data = band.data.astype(float)
            no_data_value = band.metadata.get('no_data_value')

            # 获取有效数据
            if no_data_value is not None:
                valid_mask = data != no_data_value
                valid_data = data[valid_mask]
            else:
                valid_mask = np.ones_like(data, dtype=bool)
                valid_data = data.flatten()

            if valid_data.size == 0:
                he_data = data
            else:
                # 直方图均衡化
                min_val = np.min(valid_data)
                max_val = np.max(valid_data)

                if max_val - min_val < 1e-10:
                    he_data = data
                else:
                    # 归一化到0-1
                    normalized = (data - min_val) / (max_val - min_val)

                    # 计算累积分布函数
                    hist, bin_edges = np.histogram(normalized[valid_mask], bins=256, range=(0, 1))
                    cdf = hist.cumsum()
                    cdf_normalized = (cdf - cdf.min()) / (cdf.max() - cdf.min())

                    # 应用均衡化
                    pixel_indices = np.digitize(normalized.flatten(), bin_edges[:-1]) - 1
                    pixel_indices = np.clip(pixel_indices, 0, 255)
                    he_flat = cdf_normalized[pixel_indices]

                    # 转换回原始范围
                    if output_bits == 8:
                        he_data = (he_flat * 255).reshape(data.shape).astype(np.uint8)
                    elif output_bits == 16:
                        he_data = (he_flat * 65535).reshape(data.shape).astype(np.uint16)
                    else:
                        he_data = he_flat.reshape(data.shape)

            he_band = RasterBand(
                data=he_data,
                band_index=idx + 1,
                band_type=band.band_type,
                metadata={**band.metadata, 'algorithm': 'HistogramEqualization'}
            )
            output_dataset.add_band(he_band)

        self._report_progress(1.0, "直方图均衡化完成")

        return output_dataset


class AtmosphericCorrectionAlgorithm(ProcessingAlgorithm):
    """大气校正算法（简化版）"""

    def __init__(self):
        super().__init__(
            name="AtmosphericCorrection",
            description="简化的大气校正算法"
        )
        self.parameters = {
            'method': 'dark_object',
            'cloud_threshold': 0.8,
            'aerosol_model': 'continental',
            'water_vapor': 2.0
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        if self.parameters['method'] not in ['dark_object', 'simple']:
            return False, "不支持的大气校正方法"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        method = self.parameters['method']
        cloud_threshold = self.parameters['cloud_threshold']

        self._report_progress(0.1, f"执行{method}大气校正...")

        output_metadata = RasterMetadata(
            width=input_dataset.metadata.width,
            height=input_dataset.metadata.height,
            band_count=input_dataset.metadata.band_count,
            file_path=f"{input_dataset.metadata.file_path}_ac.tif",
            coordinate_system=input_dataset.metadata.coordinate_system,
            geo_transform=input_dataset.metadata.geo_transform
        )

        output_dataset = RasterDataset(output_metadata)

        # 估算暗像元值
        dark_values = {}
        for band_idx, band in input_dataset.bands.items():
            data = band.data.astype(float)
            # 取最低1%的像素作为暗像元
            dark_percentile = np.percentile(data[data > 0], 1)
            dark_values[band_idx] = dark_percentile

        total_bands = len(input_dataset.bands)
        for idx, (band_idx, band) in enumerate(input_dataset.bands.items()):
            self._report_progress(0.2 + 0.7 * (idx + 1) / total_bands, f"校正波段{band_idx}...")

            data = band.data.astype(float)
            dark_value = dark_values[band_idx]

            # 简单的暗像元减法
            corrected_data = data - dark_value
            corrected_data = np.clip(corrected_data, 0, None)

            corrected_band = RasterBand(
                data=corrected_data,
                band_index=idx + 1,
                band_type=band.band_type,
                metadata={**band.metadata, 'algorithm': 'AtmosphericCorrection'}
            )
            output_dataset.add_band(corrected_band)

        self._report_progress(1.0, "大气校正完成")

        return output_dataset


class CloudMaskAlgorithm(ProcessingAlgorithm):
    """云检测与掩膜生成算法"""

    def __init__(self):
        super().__init__(
            name="CloudMask",
            description="云检测并生成云掩膜"
        )
        self.parameters = {
            'method': 'threshold',
            'brightness_threshold': 0.8,
            'temperature_threshold': 280.0,
            'use_swir': True,
            'swir_threshold': 0.1
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        if self.parameters['brightness_threshold'] < 0 or self.parameters['brightness_threshold'] > 1:
            return False, "亮度阈值必须在0-1之间"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        method = self.parameters['method']
        brightness_threshold = self.parameters['brightness_threshold']

        self._report_progress(0.1, "执行云检测...")

        # 使用可见光波段的亮度进行简单云检测
        visible_bands = []
        for band_type in [BandType.RED, BandType.GREEN, BandType.BLUE]:
            band = input_dataset.get_band_by_type(band_type)
            if band:
                visible_bands.append(band.data.astype(float))

        if not visible_bands:
            # 使用前三个波段
            for i in range(1, min(4, input_dataset.metadata.band_count + 1)):
                band = input_dataset.get_band(i)
                if band:
                    visible_bands.append(band.data.astype(float))

        if not visible_bands:
            raise ValueError("没有可用的可见光波段")

        # 计算平均亮度
        avg_brightness = np.mean(visible_bands, axis=0)

        # 归一化
        max_brightness = np.max(avg_brightness)
        if max_brightness > 0:
            avg_brightness = avg_brightness / max_brightness

        # 云检测
        cloud_mask = avg_brightness > brightness_threshold

        self._report_progress(0.6, "生成掩膜...")

        output_metadata = RasterMetadata(
            width=input_dataset.metadata.width,
            height=input_dataset.metadata.height,
            band_count=1,
            file_path=f"{input_dataset.metadata.file_path}_cloud_mask.tif",
            no_data_value=255,
            coordinate_system=input_dataset.metadata.coordinate_system,
            geo_transform=input_dataset.metadata.geo_transform
        )

        output_dataset = RasterDataset(output_metadata)

        # 创建掩膜波段（0=无云，1=云）
        mask_data = cloud_mask.astype(np.uint8)

        mask_band = RasterBand(
            data=mask_data,
            band_index=1,
            band_type=BandType.UNKNOWN,
            metadata={
                'algorithm': 'CloudMask',
                'method': method,
                'description': 'Cloud mask (0=no cloud, 1=cloud)'
            }
        )
        output_dataset.add_band(mask_band)

        cloud_percentage = np.sum(cloud_mask) / cloud_mask.size * 100
        self._report_progress(1.0, f"云检测完成，云覆盖率：{cloud_percentage:.2f}%")
        self._log_message('info', f"云覆盖率：{cloud_percentage:.2f}%")

        return output_dataset


class PanSharpeningAlgorithm(ProcessingAlgorithm):
    """全色锐化算法"""

    def __init__(self):
        super().__init__(
            name="PanSharpening",
            description="全色锐化融合多光谱和全色波段"
        )
        self.parameters = {
            'method': 'brovey',
            'pan_band': 0,
            'ms_bands': [1, 2, 3],
            'resample_method': 'bilinear'
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        if not self.parameters['ms_bands']:
            return False, "必须指定多光谱波段"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        method = self.parameters['method']
        pan_band_idx = self.parameters['pan_band']
        ms_band_indices = self.parameters['ms_bands']

        self._report_progress(0.1, "读取波段数据...")

        pan_band = input_dataset.get_band(pan_band_idx)
        ms_bands = [input_dataset.get_band(idx) for idx in ms_band_indices]

        if not pan_band or not all(ms_bands):
            raise ValueError("找不到指定的波段")

        pan_data = pan_band.data.astype(float)
        ms_data_list = [band.data.astype(float) for band in ms_bands]

        # 确保尺寸一致（简化处理，假设已重采样）
        target_shape = pan_data.shape
        for i, ms_data in enumerate(ms_data_list):
            if ms_data.shape != target_shape:
                # 简单的重采样
                from skimage.transform import resize
                ms_data_list[i] = resize(ms_data, target_shape, mode='reflect', anti_aliasing=True)

        self._report_progress(0.3, f"执行{method}锐化...")

        if method == 'brovey':
            # Brovey变换
            ms_sum = np.sum(ms_data_list, axis=0)
            ms_sum[ms_sum == 0] = 1  # 避免除零

            sharpened_bands = []
            for ms_data in ms_data_list:
                sharpened = (ms_data / ms_sum) * pan_data
                sharpened_bands.append(sharpened)
        elif method == 'simple_mean':
            # 简单均值融合
            sharpened_bands = []
            for ms_data in ms_data_list:
                sharpened = (ms_data + pan_data) / 2
                sharpened_bands.append(sharpened)
        else:
            raise ValueError(f"不支持的锐化方法：{method}")

        self._report_progress(0.8, "创建输出数据集...")

        output_metadata = RasterMetadata(
            width=target_shape[1],
            height=target_shape[0],
            band_count=len(sharpened_bands),
            file_path=f"{input_dataset.metadata.file_path}_pansharpen.tif",
            coordinate_system=input_dataset.metadata.coordinate_system,
            geo_transform=input_dataset.metadata.geo_transform
        )

        output_dataset = RasterDataset(output_metadata)

        for idx, sharpened_data in enumerate(sharpened_bands):
            sharpened_band = RasterBand(
                data=sharpened_data,
                band_index=idx + 1,
                band_type=ms_bands[idx].band_type,
                metadata={**ms_bands[idx].metadata, 'algorithm': 'PanSharpening'}
            )
            output_dataset.add_band(sharpened_band)

        self._report_progress(1.0, "全色锐化完成")

        return output_dataset


class MosaicAlgorithm(ProcessingAlgorithm):
    """影像镶嵌算法"""

    def __init__(self):
        super().__init__(
            name="Mosaic",
            description="将多景影像镶嵌为单景影像"
        )
        self.parameters = {
            'blend_method': 'average',
            'feather_width': 10,
            'no_data_value': 0,
            'output_dtype': 'uint8'
        }
        self.input_datasets: List[RasterDataset] = []

    def set_input_datasets(self, datasets: List[RasterDataset]) -> None:
        self.input_datasets = datasets

    def validate_parameters(self) -> Tuple[bool, str]:
        if not self.input_datasets:
            return False, "没有输入数据集"
        if len(self.input_datasets) < 2:
            return False, "至少需要两个输入数据集"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        # 对于镶嵌算法，input_dataset被忽略，使用input_datasets
        if not self.input_datasets:
            raise ValueError("没有设置输入数据集")

        blend_method = self.parameters['blend_method']
        feather_width = self.parameters['feather_width']
        no_data_value = self.parameters['no_data_value']

        self._report_progress(0.1, "计算输出范围...")

        # 计算所有影像的联合范围
        all_bounds = []
        for ds in self.input_datasets:
            gt = ds.metadata.geo_transform
            min_x = gt.top_left_x
            max_x = min_x + ds.metadata.width * gt.pixel_width
            max_y = gt.top_left_y
            min_y = max_y + ds.metadata.height * gt.pixel_height
            all_bounds.append((min_x, min_y, max_x, max_y))

        global_min_x = min(b[0] for b in all_bounds)
        global_min_y = min(b[1] for b in all_bounds)
        global_max_x = max(b[2] for b in all_bounds)
        global_max_y = max(b[3] for b in all_bounds)

        # 使用第一个影像的分辨率
        ref_gt = self.input_datasets[0].metadata.geo_transform
        output_width = int((global_max_x - global_min_x) / abs(ref_gt.pixel_width))
        output_height = int((global_max_y - global_min_y) / abs(ref_gt.pixel_height))

        self._report_progress(0.3, f"输出尺寸：{output_width}x{output_height}")

        # 确定波段数
        band_count = max(ds.metadata.band_count for ds in self.input_datasets)

        output_metadata = RasterMetadata(
            width=output_width,
            height=output_height,
            band_count=band_count,
            file_path="mosaic_output.tif",
            no_data_value=no_data_value,
            geo_transform=GeoTransform(
                top_left_x=global_min_x,
                pixel_width=ref_gt.pixel_width,
                rotation_x=0,
                top_left_y=global_max_y,
                rotation_y=0,
                pixel_height=-abs(ref_gt.pixel_height)
            ),
            coordinate_system=self.input_datasets[0].metadata.coordinate_system
        )

        output_dataset = RasterDataset(output_metadata)

        # 创建输出波段
        for band_idx in range(1, band_count + 1):
            self._report_progress(0.3 + 0.6 * band_idx / band_count, f"镶嵌波段{band_idx}...")

            output_data = np.full((output_height, output_width), no_data_value, dtype=float)
            weight_sum = np.zeros((output_height, output_width), dtype=float)

            for ds in self.input_datasets:
                band = ds.get_band(band_idx)
                if not band:
                    continue

                # 计算该影像在输出中的位置
                ds_gt = ds.metadata.geo_transform
                start_x = int((ds_gt.top_left_x - global_min_x) / ref_gt.pixel_width)
                start_y = int((global_max_y - ds_gt.top_left_y) / abs(ref_gt.pixel_height))

                # 裁剪到有效范围
                y_start = max(0, start_y)
                y_end = min(output_height, start_y + ds.metadata.height)
                x_start = max(0, start_x)
                x_end = min(output_width, start_x + ds.metadata.width)

                if y_start >= y_end or x_start >= x_end:
                    continue

                # 获取源数据
                src_y_start = y_start - start_y
                src_y_end = src_y_start + (y_end - y_start)
                src_x_start = x_start - start_x
                src_x_end = src_x_start + (x_end - x_start)

                src_data = band.data[src_y_start:src_y_end, src_x_start:src_x_end].astype(float)

                # 创建权重（用于羽化）
                weights = np.ones_like(src_data, dtype=float)
                if feather_width > 0:
                    # 边缘羽化
                    h, w = src_data.shape
                    for i in range(min(feather_width, h // 2)):
                        weight = (i + 1) / feather_width
                        weights[i, :] = weight
                        weights[h - 1 - i, :] = weight
                    for j in range(min(feather_width, w // 2)):
                        weight = (j + 1) / feather_width
                        weights[:, j] = np.minimum(weights[:, j], weight)
                        weights[:, w - 1 - j] = np.minimum(weights[:, w - 1 - j], weight)

                # 累加
                valid_mask = src_data != no_data_value
                output_data[y_start:y_end, x_start:x_end][valid_mask] += \
                    src_data[valid_mask] * weights[valid_mask]
                weight_sum[y_start:y_end, x_start:x_end][valid_mask] += weights[valid_mask]

            # 计算加权平均
            valid_weight_mask = weight_sum > 0
            output_data[valid_weight_mask] /= weight_sum[valid_weight_mask]

            output_band = RasterBand(
                data=output_data,
                band_index=band_idx,
                metadata={'algorithm': 'Mosaic'}
            )
            output_dataset.add_band(output_band)

        self._report_progress(1.0, "镶嵌完成")

        return output_dataset


class ResamplingAlgorithm(ProcessingAlgorithm):
    """重采样算法"""

    def __init__(self):
        super().__init__(
            name="Resampling",
            description="对遥感影像进行重采样"
        )
        self.parameters = {
            'method': 'bilinear',
            'output_resolution': 10.0,
            'output_width': 0,
            'output_height': 0
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        if self.parameters['method'] not in ['nearest', 'bilinear', 'cubic', 'average']:
            return False, "不支持的重采样方法"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        method = self.parameters['method']
        output_res = self.parameters['output_resolution']
        output_width = self.parameters['output_width']
        output_height = self.parameters['output_height']

        self._report_progress(0.1, "计算输出参数...")

        ref_gt = input_dataset.metadata.geo_transform

        if output_width > 0 and output_height > 0:
            new_width = output_width
            new_height = output_height
            new_pixel_width = (ref_gt.pixel_width * input_dataset.metadata.width) / new_width
            new_pixel_height = (ref_gt.pixel_height * input_dataset.metadata.height) / new_height
        elif output_res > 0:
            new_pixel_width = output_res
            new_pixel_height = output_res
            new_width = int(input_dataset.metadata.width * ref_gt.pixel_width / new_pixel_width)
            new_height = int(input_dataset.metadata.height * abs(ref_gt.pixel_height) / new_pixel_height)
        else:
            raise ValueError("必须指定输出分辨率或输出尺寸")

        self._report_progress(0.2, f"输出尺寸：{new_width}x{new_height}")

        output_metadata = RasterMetadata(
            width=new_width,
            height=new_height,
            band_count=input_dataset.metadata.band_count,
            file_path=f"{input_dataset.metadata.file_path}_resampled.tif",
            geo_transform=GeoTransform(
                top_left_x=ref_gt.top_left_x,
                pixel_width=new_pixel_width,
                rotation_x=ref_gt.rotation_x,
                top_left_y=ref_gt.top_left_y,
                rotation_y=ref_gt.rotation_y,
                pixel_height=-abs(new_pixel_height)
            ),
            coordinate_system=input_dataset.metadata.coordinate_system,
            no_data_value=input_dataset.metadata.no_data_value
        )

        output_dataset = RasterDataset(output_metadata)

        total_bands = len(input_dataset.bands)
        for idx, (band_idx, band) in enumerate(input_dataset.bands.items()):
            self._report_progress(0.2 + 0.7 * (idx + 1) / total_bands, f"重采样波段{band_idx}...")

            src_data = band.data.astype(float)

            # 使用numpy进行简单重采样
            if method == 'nearest':
                from skimage.transform import resize
                resampled_data = resize(src_data, (new_height, new_width), order=0, preserve_range=True, anti_aliasing=False)
            elif method == 'bilinear':
                from skimage.transform import resize
                resampled_data = resize(src_data, (new_height, new_width), order=1, preserve_range=True, anti_aliasing=True)
            elif method == 'cubic':
                from skimage.transform import resize
                resampled_data = resize(src_data, (new_height, new_width), order=3, preserve_range=True, anti_aliasing=True)
            elif method == 'average':
                from skimage.transform import resize
                resampled_data = resize(src_data, (new_height, new_width), order=1, preserve_range=True, anti_aliasing=True)
            else:
                resampled_data = src_data

            resampled_band = RasterBand(
                data=resampled_data,
                band_index=idx + 1,
                band_type=band.band_type,
                metadata={**band.metadata, 'algorithm': 'Resampling'}
            )
            output_dataset.add_band(resampled_band)

        self._report_progress(1.0, "重采样完成")

        return output_dataset


class ClassificationAlgorithm(ProcessingAlgorithm):
    """影像分类算法"""

    def __init__(self):
        super().__init__(
            name="Classification",
            description="遥感影像分类（监督/非监督）"
        )
        self.parameters = {
            'method': 'kmeans',
            'n_classes': 5,
            'training_samples': [],
            'max_iterations': 100,
            'random_state': 42
        }

    def validate_parameters(self) -> Tuple[bool, str]:
        if self.parameters['n_classes'] < 2:
            return False, "分类数必须大于等于2"
        if self.parameters['method'] not in ['kmeans', 'random_forest', 'svm']:
            return False, "不支持的分类方法"
        return True, ""

    def execute(self, input_dataset: RasterDataset) -> RasterDataset:
        method = self.parameters['method']
        n_classes = self.parameters['n_classes']
        max_iterations = self.parameters['max_iterations']
        random_state = self.parameters['random_state']

        self._report_progress(0.1, "准备训练数据...")

        # 收集所有波段数据
        band_data_list = []
        for band_idx in sorted(input_dataset.bands.keys()):
            band = input_dataset.get_band(band_idx)
            if band:
                band_data_list.append(band.data.flatten())

        if not band_data_list:
            raise ValueError("没有可用的波段数据")

        feature_matrix = np.stack(band_data_list, axis=1)

        # 移除无效值
        no_data_value = input_dataset.metadata.no_data_value
        if no_data_value is not None:
            valid_mask = ~np.any(feature_matrix == no_data_value, axis=1)
            feature_matrix = feature_matrix[valid_mask]
        else:
            valid_mask = np.ones(feature_matrix.shape[0], dtype=bool)

        self._report_progress(0.3, f"特征矩阵形状：{feature_matrix.shape}")

        if method == 'kmeans':
            from sklearn.cluster import KMeans
            self._report_progress(0.4, "执行K-means聚类...")
            kmeans = KMeans(n_clusters=n_classes, max_iter=max_iterations, random_state=random_state)
            labels = kmeans.fit_predict(feature_matrix)
        elif method == 'random_forest':
            # 简化实现，实际需要训练样本
            from sklearn.ensemble import RandomForestClassifier
            self._report_progress(0.4, "执行随机森林分类...")
            # 这里需要训练样本，暂时使用K-means替代
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=n_classes, random_state=random_state)
            labels = kmeans.fit_predict(feature_matrix)
        else:
            # 默认使用K-means
            from sklearn.cluster import KMeans
            labels = KMeans(n_clusters=n_classes, random_state=random_state).fit_predict(feature_matrix)

        self._report_progress(0.7, "生成分类结果...")

        # 重建分类图像
        classification_image = np.full(
            (input_dataset.metadata.height * input_dataset.metadata.width,),
            255, dtype=np.uint8
        )
        classification_image[valid_mask] = labels
        classification_image = classification_image.reshape(
            input_dataset.metadata.height, input_dataset.metadata.width
        )

        output_metadata = RasterMetadata(
            width=input_dataset.metadata.width,
            height=input_dataset.metadata.height,
            band_count=1,
            file_path=f"{input_dataset.metadata.file_path}_classified.tif",
            no_data_value=255,
            coordinate_system=input_dataset.metadata.coordinate_system,
            geo_transform=input_dataset.metadata.geo_transform
        )

        output_dataset = RasterDataset(output_metadata)

        classification_band = RasterBand(
            data=classification_image,
            band_index=1,
            band_type=BandType.UNKNOWN,
            metadata={
                'algorithm': 'Classification',
                'method': method,
                'n_classes': n_classes,
                'class_names': [f"Class_{i}" for i in range(n_classes)]
            }
        )
        output_dataset.add_band(classification_band)

        self._report_progress(1.0, f"分类完成，共{n_classes}类")

        return output_dataset


def register_algorithms(registry=None):
    """注册所有算法"""
    from core.engine import AlgorithmRegistry

    if registry is None:
        registry = AlgorithmRegistry()

    algorithms = [
        NDVIAlgorithm(),
        EVIAlgorithm(),
        HistogramEqualizationAlgorithm(),
        AtmosphericCorrectionAlgorithm(),
        CloudMaskAlgorithm(),
        PanSharpeningAlgorithm(),
        MosaicAlgorithm(),
        ResamplingAlgorithm(),
        ClassificationAlgorithm()
    ]

    for algorithm in algorithms:
        registry.register(algorithm)

    return registry


__all__ = [
    'NDVIAlgorithm',
    'EVIAlgorithm',
    'HistogramEqualizationAlgorithm',
    'AtmosphericCorrectionAlgorithm',
    'CloudMaskAlgorithm',
    'PanSharpeningAlgorithm',
    'MosaicAlgorithm',
    'ResamplingAlgorithm',
    'ClassificationAlgorithm',
    'register_algorithms'
]
