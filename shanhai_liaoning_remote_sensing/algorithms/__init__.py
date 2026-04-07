"""
山海辽凝遥感影像快速加工处理平台
算法模块包
"""

from .processors import (
    NDVIAlgorithm,
    EVIAlgorithm,
    HistogramEqualizationAlgorithm,
    AtmosphericCorrectionAlgorithm,
    CloudMaskAlgorithm,
    PanSharpeningAlgorithm,
    MosaicAlgorithm,
    ResamplingAlgorithm,
    ClassificationAlgorithm,
    register_algorithms
)

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
