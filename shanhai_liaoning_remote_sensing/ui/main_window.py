"""
山海辽凝遥感影像快速加工处理平台
UI模块 - 主窗口和核心界面组件
"""

import sys
import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import logging
import json

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QAction, QToolBar, QStatusBar, QFileDialog,
    QMessageBox, QProgressBar, QLabel, QPushButton, QComboBox,
    QSpinBox, QDoubleSpinBox, QCheckBox, QGroupBox, QScrollArea,
    QTreeWidget, QTreeWidgetItem, QListWidget, QListWidgetItem,
    QTextEdit, QTabWidget, QDialog, QDialogButtonBox, QFormLayout,
    QGridLayout, QFrame, QSlider, QSpacerItem, QSizePolicy,
    QApplication, QSystemTrayIcon, QMenu as QContextMenu
)
from PyQt6.QtCore import (
    Qt, QThread, pyqtSignal, QObject, QSize, QTimer, QUrl,
    QSettings, QMimeData, QPoint, QRect
)
from PyQt6.QtGui import (
    QIcon, QPixmap, QImage, QPainter, QColor, QPen, QBrush,
    QFont, QActionGroup, QKeySequence, QCursor, QPalette
)

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

# 导入核心模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.engine import (
    RasterDataset, RasterBand, RasterMetadata, BandType,
    ProcessingEngine, DataManager, ProcessingAlgorithm,
    GeoTransform, CoordinateSystem, DataType
)
from algorithms.processors import register_algorithms

logger = logging.getLogger(__name__)


class WorkerThread(QThread):
    """工作线程 - 用于后台处理任务"""

    progress_signal = pyqtSignal(float, str)
    log_signal = pyqtSignal(str, str)
    finished_signal = pyqtSignal(object)
    error_signal = pyqtSignal(str)

    def __init__(self, algorithm: ProcessingAlgorithm, dataset: RasterDataset):
        super().__init__()
        self.algorithm = algorithm
        self.dataset = dataset
        self.result = None

    def run(self):
        try:
            def on_progress(progress: float, message: str):
                self.progress_signal.emit(progress, message)

            def on_log(level: str, message: str):
                self.log_signal.emit(level, message)

            self.algorithm.set_progress_callback(on_progress)
            self.algorithm.set_log_callback(on_log)

            valid, error_msg = self.algorithm.validate_parameters()
            if not valid:
                raise ValueError(error_msg)

            self.result = self.algorithm.execute(self.dataset)
            self.finished_signal.emit(self.result)
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            self.error_signal.emit(str(e))


class ImageCanvas(QWidget):
    """图像显示画布"""

    pixel_value_signal = pyqtSignal(int, int, dict)
    coordinate_signal = pyqtSignal(float, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.dataset: Optional[RasterDataset] = None
        self.current_image: Optional[QImage] = None
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.display_bands = [1, 2, 3]  # RGB波段
        self.contrast = 1.0
        self.brightness = 0.0
        self.interpolation = 'bilinear'
        self.mouse_pressed = False
        self.last_mouse_pos = QPoint(0, 0)

        self.setMinimumSize(400, 300)
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(40, 40, 40))
        self.setPalette(palette)

        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

    def set_dataset(self, dataset: RasterDataset):
        self.dataset = dataset
        self.update_display()
        self.update()

    def set_display_bands(self, bands: List[int]):
        self.display_bands = bands
        self.update_display()
        self.update()

    def update_display(self):
        if not self.dataset:
            self.current_image = None
            return

        # 获取RGB合成图像
        if len(self.display_bands) >= 3:
            rgb_data = self.dataset.get_rgb_composite(
                self.display_bands[0],
                self.display_bands[1],
                self.display_bands[2]
            )
        elif len(self.display_bands) == 1:
            band = self.dataset.get_band(self.display_bands[0])
            if band:
                normalized = band.normalize().data
                rgb_data = np.stack([normalized, normalized, normalized], axis=-1)
            else:
                rgb_data = None
        else:
            rgb_data = None

        if rgb_data is None:
            self.current_image = None
            return

        # 应用对比度和亮度调整
        rgb_data = rgb_data * self.contrast + self.brightness
        rgb_data = np.clip(rgb_data, 0, 1)

        # 转换为QImage
        height, width = rgb_data.shape[:2]
        qimage_data = (rgb_data * 255).astype(np.uint8)
        bytes_per_line = 3 * width
        self.current_image = QImage(
            qimage_data.tobytes(),
            width, height, bytes_per_line,
            QImage.Format.Format_RGB888
        )

    def paintEvent(self, event):
        if not self.current_image:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(QPen(QColor(100, 100, 100)))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No Image Loaded")
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform if self.interpolation == 'bilinear'
                              else QPainter.RenderHint.Antialiasing)

        # 计算绘制区域
        img_rect = self.current_image.rect()
        scaled_rect = img_rect.scaled(
            int(img_rect.width() * self.zoom_level),
            int(img_rect.height() * self.zoom_level)
        )

        target_rect = QRect(
            self.pan_offset.x(), self.pan_offset.y(),
            scaled_rect.width(), scaled_rect.height()
        )

        painter.drawImage(target_rect, self.current_image)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.zoom_level *= 1.1
        else:
            self.zoom_level /= 1.1
        self.zoom_level = max(0.1, min(10.0, self.zoom_level))
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed = True
            self.last_mouse_pos = event.position().toPoint()

    def mouseMoveEvent(self, event):
        pos = event.position().toPoint()

        # 发送坐标信号
        if self.dataset:
            # 将屏幕坐标转换为像素坐标
            pixel_x = int((pos.x() - self.pan_offset.x()) / self.zoom_level)
            pixel_y = int((pos.y() - self.pan_offset.y()) / self.zoom_level)

            if 0 <= pixel_x < self.dataset.metadata.width and \
               0 <= pixel_y < self.dataset.metadata.height:
                values = self.dataset.get_pixel_value(pixel_x, pixel_y)
                self.pixel_value_signal.emit(pixel_x, pixel_y, values)

                geo_coords = self.dataset.get_geographic_coordinates(pixel_x, pixel_y)
                self.coordinate_signal.emit(geo_coords[0], geo_coords[1])

        # 平移
        if self.mouse_pressed:
            dx = pos.x() - self.last_mouse_pos.x()
            dy = pos.y() - self.last_mouse_pos.y()
            self.pan_offset += QPoint(dx, dy)
            self.last_mouse_pos = pos
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_pressed = False

    def reset_view(self):
        self.zoom_level = 1.0
        self.pan_offset = QPoint(0, 0)
        self.update()


class HistogramWidget(FigureCanvas):
    """直方图显示组件"""

    def __init__(self, parent=None):
        self.fig = Figure(figsize=(4, 3), facecolor='#2b2b2b')
        super().__init__(self.fig)
        self.setParent(parent)
        self.axes = self.fig.add_subplot(111)
        self.axes.set_facecolor('#2b2b2b')
        self.axes.tick_params(colors='white')
        for spine in self.axes.spines.values():
            spine.set_color('white')
        self.datasets = {}
        self.update_plot()

    def update_plot(self, dataset: Optional[RasterDataset] = None, bands: Optional[List[int]] = None):
        self.axes.clear()
        self.axes.set_facecolor('#2b2b2b')
        self.axes.tick_params(colors='white')
        for spine in self.axes.spines.values():
            spine.set_color('white')

        if dataset and bands:
            colors = ['red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
            for idx, band_idx in enumerate(bands):
                band = dataset.get_band(band_idx)
                if band:
                    hist = band.get_histogram(bins=256, normalize=True)
                    x = np.linspace(0, 255, 256)
                    color = colors[idx % len(colors)]
                    self.axes.fill_between(x, hist, alpha=0.3, color=color, label=f'Band {band_idx}')
                    self.axes.plot(x, hist, color=color, linewidth=1)

            self.axes.set_xlabel('DN Value', color='white')
            self.axes.set_ylabel('Frequency', color='white')
            self.axes.legend(facecolor='#2b2b2b', edgecolor='white', labelcolor='white')
            self.axes.set_title('Histogram', color='white')

        self.fig.tight_layout()
        self.draw()


class LayerTreeWidget(QTreeWidget):
    """图层树控件"""

    layer_visibility_changed = pyqtSignal(str, bool)
    layer_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setHeaderLabels(['Layer', 'Type'])
        self.setColumnCount(2)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTreeWidget {
                background-color: #323232;
                color: white;
                border: 1px solid #505050;
            }
            QTreeWidget::item:selected {
                background-color: #505050;
            }
            QTreeWidget::item:hover {
                background-color: #404040;
            }
        """)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def add_layer(self, name: str, layer_type: str = 'Raster', visible: bool = True):
        item = QTreeWidgetItem([name, layer_type])
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(0, Qt.CheckState.Checked if visible else Qt.CheckState.Unchecked)
        item.setData(0, Qt.ItemDataRole.UserRole, name)
        self.addTopLevelItem(item)
        item.toggled.connect(lambda checked: self.layer_visibility_changed.emit(name, checked))

    def remove_layer(self, name: str):
        for i in range(self.topLevelItemCount()):
            item = self.topLevelItem(i)
            if item.data(0, Qt.ItemDataRole.UserRole) == name:
                self.takeTopLevelItem(i)
                break

    def clear_layers(self):
        self.clear()

    def show_context_menu(self, position: QPoint):
        item = self.itemAt(position)
        if not item:
            return

        menu = QContextMenu(self)
        zoom_action = menu.addAction("Zoom to Layer")
        properties_action = menu.addAction("Properties")
        remove_action = menu.addAction("Remove")

        action = menu.exec_(self.viewport().mapToGlobal(position))
        if action == zoom_action:
            pass  # TODO: 实现缩放至图层
        elif action == properties_action:
            pass  # TODO: 显示属性
        elif action == remove_action:
            name = item.data(0, Qt.ItemDataRole.UserRole)
            self.remove_layer(name)


class LogWidget(QTextEdit):
    """日志显示控件"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                border: 1px solid #505050;
            }
        """)
        self.max_lines = 1000

    def append_log(self, level: str, message: str):
        timestamp = datetime.now().strftime('%H:%M:%S')
        color_map = {
            'info': '#4ec9b0',
            'warning': '#dcdcaa',
            'error': '#f44747',
            'debug': '#808080'
        }
        color = color_map.get(level.lower(), '#d4d4d4')
        html = f'<span style="color: #808080;">[{timestamp}]</span> ' \
               f'<span style="color: {color};">[{level.upper()}]</span> {message}'
        self.append(html)

        # 限制行数
        if self.document().blockCount() > self.max_lines:
            cursor = self.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.select(cursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()
            cursor.deleteChar()  # 删除换行符

    def clear_log(self):
        self.clear()


class ProcessingDialog(QDialog):
    """处理进度对话框"""

    cancel_requested = pyqtSignal()

    def __init__(self, algorithm_name: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Processing: {algorithm_name}")
        self.setModal(True)
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # 算法名称
        name_label = QLabel(f"<h3>{algorithm_name}</h3>")
        layout.addWidget(name_label)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # 状态标签
        self.status_label = QLabel("Initializing...")
        layout.addWidget(self.status_label)

        # 取消按钮
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.on_cancel)
        layout.addWidget(self.cancel_button)

    def update_progress(self, value: float, message: str):
        self.progress_bar.setValue(int(value * 100))
        self.status_label.setText(message)

    def on_cancel(self):
        self.cancel_requested.emit()
        self.close()


class AttributePanel(QScrollArea):
    """属性面板"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet("""
            QScrollArea {
                background-color: #323232;
                border: 1px solid #505050;
            }
            QLabel {
                color: white;
                padding: 2px;
            }
        """)

        container = QWidget()
        self.setWidget(container)
        self.layout = QVBoxLayout(container)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop)

    def set_dataset(self, dataset: Optional[RasterDataset]):
        # 清除现有内容
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not dataset:
            info_label = QLabel("No dataset selected")
            info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout.addWidget(info_label)
            return

        metadata = dataset.metadata

        # 基本信息组
        basic_group = QGroupBox("Basic Information")
        basic_layout = QFormLayout()
        basic_layout.addRow("File Path:", QLabel(metadata.file_path or "N/A"))
        basic_layout.addRow("Dimensions:", QLabel(f"{metadata.width} x {metadata.height}"))
        basic_layout.addRow("Bands:", QLabel(str(metadata.band_count)))
        basic_layout.addRow("Data Type:", QLabel(metadata.data_type.value))
        basic_group.setLayout(basic_layout)
        self.layout.addWidget(basic_group)

        # 地理信息组
        geo_group = QGroupBox("Geographic Information")
        geo_layout = QFormLayout()
        gt = metadata.geo_transform
        geo_layout.addRow("Top Left X:", QLabel(f"{gt.top_left_x:.4f}"))
        geo_layout.addRow("Top Left Y:", QLabel(f"{gt.top_left_y:.4f}"))
        geo_layout.addRow("Pixel Width:", QLabel(f"{gt.pixel_width:.6f}"))
        geo_layout.addRow("Pixel Height:", QLabel(f"{gt.pixel_height:.6f}"))
        cs = metadata.coordinate_system
        geo_layout.addRow("EPSG Code:", QLabel(str(cs.epsg_code) if cs.epsg_code else "N/A"))
        geo_group.setLayout(geo_layout)
        self.layout.addWidget(geo_group)

        # 统计信息组
        stats_group = QGroupBox("Statistics")
        stats_layout = QFormLayout()
        stats_layout.addRow("Min:", QLabel(f"{metadata.min_value:.2f}"))
        stats_layout.addRow("Max:", QLabel(f"{metadata.max_value:.2f}"))
        stats_layout.addRow("Mean:", QLabel(f"{metadata.mean_value:.2f}"))
        stats_layout.addRow("Std Dev:", QLabel(f"{metadata.std_value:.2f}"))
        stats_group.setLayout(stats_layout)
        self.layout.addWidget(stats_group)

        # 元数据组
        meta_group = QGroupBox("Metadata")
        meta_layout = QFormLayout()
        if metadata.acquisition_date:
            meta_layout.addRow("Acquisition Date:",
                               QLabel(metadata.acquisition_date.strftime('%Y-%m-%d')))
        if metadata.sensor_name:
            meta_layout.addRow("Sensor:", QLabel(metadata.sensor_name))
        if metadata.platform_name:
            meta_layout.addRow("Platform:", QLabel(metadata.platform_name))
        meta_layout.addRow("Cloud Cover:", QLabel(f"{metadata.cloud_cover:.1f}%"))
        meta_group.setLayout(meta_layout)
        self.layout.addWidget(meta_group)

        # 波段信息
        bands_group = QGroupBox("Bands")
        bands_layout = QVBoxLayout()
        for band_idx, band in dataset.bands.items():
            band_info = f"Band {band_idx}: {band.band_type.value} - Shape: {band.shape}"
            band_label = QLabel(band_info)
            bands_layout.addWidget(band_label)
        bands_group.setLayout(bands_layout)
        self.layout.addWidget(bands_group)

        self.layout.addStretch()


class ToolBarManager:
    """工具栏管理器"""

    def __init__(self, main_window):
        self.main_window = main_window
        self.toolbars: Dict[str, QToolBar] = {}

    def create_standard_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Standard")
        toolbar.setObjectName("StandardToolBar")
        toolbar.setMovable(False)

        # 添加文件操作按钮
        new_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.DocumentNew), "New", self.main_window)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.main_window.new_project)
        toolbar.addAction(new_action)

        open_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.DocumentOpen), "Open", self.main_window)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.main_window.open_file)
        toolbar.addAction(open_action)

        save_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.DocumentSave), "Save", self.main_window)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.main_window.save_file)
        toolbar.addAction(save_action)

        toolbar.addSeparator()

        # 添加撤销重做按钮
        undo_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.EditUndo), "Undo", self.main_window)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.main_window.undo)
        toolbar.addAction(undo_action)

        redo_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.EditRedo), "Redo", self.main_window)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.main_window.redo)
        toolbar.addAction(redo_action)

        self.toolbars['standard'] = toolbar
        return toolbar

    def create_navigation_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Navigation")
        toolbar.setObjectName("NavigationToolBar")
        toolbar.setMovable(False)

        zoom_in_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.ZoomIn), "Zoom In", self.main_window)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(lambda: self.main_window.adjust_zoom(1.2))
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.ZoomOut), "Zoom Out", self.main_window)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(lambda: self.main_window.adjust_zoom(0.8))
        toolbar.addAction(zoom_out_action)

        fit_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.ZoomFitBest), "Fit to Window", self.main_window)
        fit_action.setShortcut("Ctrl+0")
        fit_action.triggered.connect(self.main_window.fit_to_window)
        toolbar.addAction(fit_action)

        pan_action = QAction(QIcon.fromTheme(QIcon.ThemeIcon.EditMove), "Pan", self.main_window)
        pan_action.setCheckable(True)
        toolbar.addAction(pan_action)

        self.toolbars['navigation'] = toolbar
        return toolbar

    def create_processing_toolbar(self) -> QToolBar:
        toolbar = QToolBar("Processing")
        toolbar.setObjectName("ProcessingToolBar")
        toolbar.setMovable(False)

        ndvi_action = QAction("NDVI", self.main_window)
        ndvi_action.triggered.connect(lambda: self.main_window.run_algorithm("NDVI"))
        toolbar.addAction(ndvi_action)

        evi_action = QAction("EVI", self.main_window)
        evi_action.triggered.connect(lambda: self.main_window.run_algorithm("EVI"))
        toolbar.addAction(evi_action)

        he_action = QAction("Histogram Eq.", self.main_window)
        he_action.triggered.connect(lambda: self.main_window.run_algorithm("HistogramEqualization"))
        toolbar.addAction(he_action)

        cloud_action = QAction("Cloud Mask", self.main_window)
        cloud_action.triggered.connect(lambda: self.main_window.run_algorithm("CloudMask"))
        toolbar.addAction(cloud_action)

        classify_action = QAction("Classification", self.main_window)
        classify_action.triggered.connect(lambda: self.main_window.run_algorithm("Classification"))
        toolbar.addAction(classify_action)

        self.toolbars['processing'] = toolbar
        return toolbar


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("山海辽凝遥感影像快速加工处理平台")
        self.setMinimumSize(1280, 800)

        # 初始化数据管理器
        self.data_manager = DataManager()
        self.processing_engine = ProcessingEngine()
        register_algorithms(self.processing_engine.algorithm_registry)

        # 当前工作线程
        self.worker_thread: Optional[WorkerThread] = None

        # 初始化UI
        self.init_ui()
        self.init_menu()
        self.init_toolbars()
        self.init_statusbar()
        self.apply_dark_theme()

        # 加载设置
        self.load_settings()

    def init_ui(self):
        """初始化用户界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 创建主分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板（图层和属性）
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(2, 2, 2, 2)

        # 图层树
        left_layout.addWidget(QLabel("<b>Layers</b>"))
        self.layer_tree = LayerTreeWidget()
        self.layer_tree.layer_visibility_changed.connect(self.on_layer_visibility_changed)
        self.layer_tree.layer_selected.connect(self.on_layer_selected)
        left_layout.addWidget(self.layer_tree, stretch=1)

        # 属性面板
        left_layout.addWidget(QLabel("<b>Properties</b>"))
        self.attribute_panel = AttributePanel()
        left_layout.addWidget(self.attribute_panel, stretch=1)

        main_splitter.addWidget(left_panel)

        # 中间面板（图像显示）
        center_panel = QWidget()
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(2, 2, 2, 2)

        # 图像画布
        self.image_canvas = ImageCanvas()
        self.image_canvas.pixel_value_signal.connect(self.on_pixel_value_changed)
        self.image_canvas.coordinate_signal.connect(self.on_coordinate_changed)
        center_layout.addWidget(self.image_canvas, stretch=1)

        # 直方图
        self.histogram_widget = HistogramWidget()
        center_layout.addWidget(self.histogram_widget, stretch=0)

        main_splitter.addWidget(center_panel)

        # 右侧面板（工具和日志）
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(2, 2, 2, 2)

        # 波段组合选择
        band_group = QGroupBox("Band Combination")
        band_layout = QFormLayout(band_group)

        self.red_combo = QComboBox()
        self.green_combo = QComboBox()
        self.blue_combo = QComboBox()
        for i in range(1, 13):
            self.red_combo.addItem(f"Band {i}", i)
            self.green_combo.addItem(f"Band {i}", i)
            self.blue_combo.addItem(f"Band {i}", i)

        self.red_combo.setCurrentIndex(2)  # Band 3
        self.green_combo.setCurrentIndex(1)  # Band 2
        self.blue_combo.setCurrentIndex(0)  # Band 1

        self.red_combo.currentIndexChanged.connect(self.update_band_combination)
        self.green_combo.currentIndexChanged.connect(self.update_band_combination)
        self.blue_combo.currentIndexChanged.connect(self.update_band_combination)

        band_layout.addRow("Red:", self.red_combo)
        band_layout.addRow("Green:", self.green_combo)
        band_layout.addRow("Blue:", self.blue_combo)

        right_layout.addWidget(band_group)

        # 对比度/亮度调整
        adjust_group = QGroupBox("Adjustments")
        adjust_layout = QFormLayout(adjust_group)

        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(50, 200)
        self.contrast_slider.setValue(100)
        self.contrast_slider.valueChanged.connect(self.update_contrast_brightness)
        adjust_layout.addRow("Contrast:", self.contrast_slider)

        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-50, 50)
        self.brightness_slider.setValue(0)
        self.brightness_slider.valueChanged.connect(self.update_contrast_brightness)
        adjust_layout.addRow("Brightness:", self.brightness_slider)

        reset_btn = QPushButton("Reset")
        reset_btn.clicked.connect(self.reset_adjustments)
        adjust_layout.addRow(reset_btn)

        right_layout.addWidget(adjust_group)

        # 日志窗口
        right_layout.addWidget(QLabel("<b>Log</b>"))
        self.log_widget = LogWidget()
        right_layout.addWidget(self.log_widget, stretch=1)

        # 清空日志按钮
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.clicked.connect(self.log_widget.clear_log)
        right_layout.addWidget(clear_log_btn)

        main_splitter.addWidget(right_panel)

        # 设置分割器初始比例
        main_splitter.setSizes([250, 800, 300])

        main_layout.addWidget(main_splitter)

    def init_menu(self):
        """初始化菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("&File")

        new_project_action = QAction("&New Project", self)
        new_project_action.setShortcut(QKeySequence.StandardKey.New)
        new_project_action.triggered.connect(self.new_project)
        file_menu.addAction(new_project_action)

        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        open_recent_menu = file_menu.addMenu("Open Recent")
        self.recent_files_actions = []
        for i in range(5):
            action = QAction("", self)
            action.setVisible(False)
            action.triggered.connect(lambda checked, idx=i: self.open_recent_file(idx))
            self.recent_files_actions.append(action)
            open_recent_menu.addAction(action)

        file_menu.addSeparator()

        save_action = QAction("&Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_file)
        file_menu.addAction(save_action)

        save_as_action = QAction("Save &As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_file_as)
        file_menu.addAction(save_as_action)

        file_menu.addSeparator()

        export_action = QAction("&Export...", self)
        export_action.triggered.connect(self.export_data)
        file_menu.addAction(export_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu("&Edit")

        undo_action = QAction("&Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction("&Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)

        edit_menu.addSeparator()

        preferences_action = QAction("&Preferences...", self)
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)

        # 处理菜单
        process_menu = menubar.addMenu("&Processing")

        algorithms = self.processing_engine.algorithm_registry.list_algorithms()
        for algo_name in algorithms:
            action = QAction(algo_name, self)
            action.triggered.connect(lambda checked, name=algo_name: self.run_algorithm(name))
            process_menu.addAction(action)

        process_menu.addSeparator()

        batch_action = QAction("&Batch Processing...", self)
        batch_action.triggered.connect(self.batch_processing)
        process_menu.addAction(batch_action)

        # 视图菜单
        view_menu = menubar.addMenu("&View")

        zoom_in_action = QAction("Zoom &In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(lambda: self.adjust_zoom(1.2))
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom &Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(lambda: self.adjust_zoom(0.8))
        view_menu.addAction(zoom_out_action)

        fit_action = QAction("&Fit to Window", self)
        fit_action.setShortcut("Ctrl+0")
        fit_action.triggered.connect(self.fit_to_window)
        view_menu.addAction(fit_action)

        view_menu.addSeparator()

        layers_action = QAction("&Layers Panel", self)
        layers_action.setCheckable(True)
        layers_action.setChecked(True)
        view_menu.addAction(layers_action)

        properties_action = QAction("&Properties Panel", self)
        properties_action.setCheckable(True)
        properties_action.setChecked(True)
        view_menu.addAction(properties_action)

        # 帮助菜单
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        documentation_action = QAction("&Documentation", self)
        documentation_action.triggered.connect(self.show_documentation)
        help_menu.addAction(documentation_action)

    def init_toolbars(self):
        """初始化工具栏"""
        self.toolbar_manager = ToolBarManager(self)

        self.addToolBar(self.toolbar_manager.create_standard_toolbar())
        self.addToolBar(self.toolbar_manager.create_navigation_toolbar())
        self.addToolBar(self.toolbar_manager.create_processing_toolbar())

    def init_statusbar(self):
        """初始化状态栏"""
        statusbar = self.statusBar()

        # 坐标显示
        self.coordinate_label = QLabel("X: 0, Y: 0")
        statusbar.addPermanentWidget(self.coordinate_label)

        # 像素值显示
        self.pixel_value_label = QLabel("Value: -")
        statusbar.addPermanentWidget(self.pixel_value_label)

        # 进度条
        self.status_progress = QProgressBar()
        self.status_progress.setRange(0, 100)
        self.status_progress.setVisible(False)
        statusbar.addPermanentWidget(self.status_progress, stretch=1)

        # 消息标签
        self.message_label = QLabel("Ready")
        statusbar.addWidget(self.message_label)

    def apply_dark_theme(self):
        """应用暗色主题"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
            }
            QMenuBar {
                background-color: #323232;
                color: white;
                padding: 2px;
            }
            QMenuBar::item:selected {
                background-color: #505050;
            }
            QMenu {
                background-color: #323232;
                color: white;
                border: 1px solid #505050;
            }
            QMenu::item:selected {
                background-color: #505050;
            }
            QToolBar {
                background-color: #323232;
                border: none;
                padding: 2px;
                spacing: 3px;
            }
            QToolButton {
                background-color: transparent;
                border: 1px solid transparent;
                border-radius: 3px;
                padding: 3px;
                color: white;
            }
            QToolButton:hover {
                background-color: #505050;
                border: 1px solid #707070;
            }
            QToolButton:pressed {
                background-color: #404040;
            }
            QStatusBar {
                background-color: #323232;
                color: white;
            }
            QProgressBar {
                border: 1px solid #505050;
                border-radius: 3px;
                text-align: center;
                background-color: #2b2b2b;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
            }
            QComboBox {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #505050;
                border-radius: 3px;
                padding: 3px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #3c3c3c;
                color: white;
                border: 1px solid #505050;
                selection-background-color: #505050;
            }
            QSlider::groove:horizontal {
                border: 1px solid #505050;
                height: 4px;
                background: #2b2b2b;
                margin: 2px 0;
            }
            QSlider::handle:horizontal {
                background: #0078d4;
                border: 1px solid #505050;
                width: 10px;
                margin: -4px 0;
                border-radius: 3px;
            }
            QGroupBox {
                font-weight: bold;
                color: white;
                border: 1px solid #505050;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #1084d8;
            }
            QPushButton:pressed {
                background-color: #006cbd;
            }
        """)

    # 槽函数
    def new_project(self):
        """新建项目"""
        reply = QMessageBox.question(
            self, 'New Project',
            'Create a new project? Current unsaved changes will be lost.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.data_manager = DataManager()
            self.layer_tree.clear_layers()
            self.attribute_panel.set_dataset(None)
            self.image_canvas.set_dataset(None)
            self.histogram_widget.update_plot()
            self.message_label.setText("New project created")

    def open_file(self):
        """打开文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Remote Sensing Image",
            "",
            "GeoTIFF (*.tif *.tiff);;All Files (*)"
        )

        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        """加载文件"""
        try:
            self.message_label.setText(f"Loading: {file_path}")
            QApplication.processEvents()

            # 模拟加载数据集
            dataset = self.data_manager.load_dataset(
                file_path,
                width=2000,
                height=2000,
                band_count=6
            )

            # 更新UI
            file_name = os.path.basename(file_path)
            self.layer_tree.add_layer(file_name, 'Raster')
            self.attribute_panel.set_dataset(dataset)
            self.image_canvas.set_dataset(dataset)

            # 更新波段组合下拉框
            band_count = dataset.metadata.band_count
            for combo in [self.red_combo, self.green_combo, self.blue_combo]:
                combo.clear()
                for i in range(1, band_count + 1):
                    combo.addItem(f"Band {i}", i)

            # 更新直方图
            self.histogram_widget.update_plot(dataset, [1, 2, 3])

            # 添加到最近文件
            self.add_to_recent_files(file_path)

            self.message_label.setText(f"Loaded: {file_name}")
            self.log_widget.append_log('info', f"Loaded file: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load file:\n{str(e)}")
            self.log_widget.append_log('error', f"Failed to load file: {str(e)}")

    def save_file(self):
        """保存文件"""
        dataset = self.data_manager.get_active_dataset()
        if not dataset:
            QMessageBox.warning(self, "Warning", "No active dataset to save")
            return

        file_path = dataset.metadata.file_path
        if not file_path:
            self.save_file_as()
            return

        self.data_manager.save_dataset(dataset, file_path)
        self.message_label.setText(f"Saved: {os.path.basename(file_path)}")
        self.log_widget.append_log('info', f"Saved file: {file_path}")

    def save_file_as(self):
        """另存为"""
        dataset = self.data_manager.get_active_dataset()
        if not dataset:
            QMessageBox.warning(self, "Warning", "No active dataset to save")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Remote Sensing Image",
            "",
            "GeoTIFF (*.tif *.tiff)"
        )

        if file_path:
            self.data_manager.save_dataset(dataset, file_path)
            self.message_label.setText(f"Saved: {os.path.basename(file_path)}")
            self.log_widget.append_log('info', f"Saved file as: {file_path}")

    def export_data(self):
        """导出数据"""
        dataset = self.data_manager.get_active_dataset()
        if not dataset:
            QMessageBox.warning(self, "Warning", "No active dataset to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Data",
            "",
            "JSON (*.json);;GeoTIFF (*.tif);;PNG (*.png)"
        )

        if file_path:
            if file_path.endswith('.json'):
                self.data_manager.export_metadata(file_path)
                self.log_widget.append_log('info', f"Exported metadata to: {file_path}")
            else:
                self.data_manager.save_dataset(dataset, file_path)
                self.log_widget.append_log('info', f"Exported data to: {file_path}")

    def run_algorithm(self, algorithm_name: str):
        """运行算法"""
        dataset = self.data_manager.get_active_dataset()
        if not dataset:
            QMessageBox.warning(self, "Warning", "No active dataset for processing")
            return

        algorithm = self.processing_engine.algorithm_registry.get_algorithm(algorithm_name)
        if not algorithm:
            QMessageBox.critical(self, "Error", f"Algorithm not found: {algorithm_name}")
            return

        # 显示进度对话框
        self.processing_dialog = ProcessingDialog(algorithm_name)
        self.processing_dialog.cancel_requested.connect(self.cancel_processing)
        self.processing_dialog.show()

        # 创建工作线程
        self.worker_thread = WorkerThread(algorithm, dataset)
        self.worker_thread.progress_signal.connect(self.on_processing_progress)
        self.worker_thread.log_signal.connect(self.on_processing_log)
        self.worker_thread.finished_signal.connect(self.on_processing_finished)
        self.worker_thread.error_signal.connect(self.on_processing_error)
        self.worker_thread.start()

    def cancel_processing(self):
        """取消处理"""
        if self.worker_thread and self.worker_thread.isRunning():
            self.processing_engine.cancel_processing()
            self.message_label.setText("Processing cancelled")

    def on_processing_progress(self, progress: float, message: str):
        """处理进度更新"""
        self.processing_dialog.update_progress(progress, message)
        self.status_progress.setValue(int(progress * 100))
        self.status_progress.setVisible(True)

    def on_processing_log(self, level: str, message: str):
        """处理日志输出"""
        self.log_widget.append_log(level, message)

    def on_processing_finished(self, result):
        """处理完成"""
        self.processing_dialog.close()
        self.status_progress.setVisible(False)
        self.status_progress.setValue(0)

        if result:
            # 添加结果到数据管理器
            output_path = result.metadata.file_path
            self.data_manager.datasets[output_path] = result
            self.layer_tree.add_layer(os.path.basename(output_path), 'Result')

            self.message_label.setText("Processing completed successfully")
            self.log_widget.append_log('info', f"Processing completed: {result.metadata.file_path}")

            # 询问是否显示结果
            reply = QMessageBox.question(
                self, 'Processing Complete',
                'Display the result?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.data_manager.set_active_dataset(output_path)
                self.attribute_panel.set_dataset(result)
                self.image_canvas.set_dataset(result)

    def on_processing_error(self, error_message: str):
        """处理错误"""
        self.processing_dialog.close()
        self.status_progress.setVisible(False)
        QMessageBox.critical(self, "Processing Error", error_message)
        self.log_widget.append_log('error', f"Processing error: {error_message}")

    def update_band_combination(self):
        """更新波段组合"""
        red = self.red_combo.currentData()
        green = self.green_combo.currentData()
        blue = self.blue_combo.currentData()

        self.image_canvas.set_display_bands([red, green, blue])
        self.image_canvas.update()

        # 更新直方图
        dataset = self.data_manager.get_active_dataset()
        if dataset:
            self.histogram_widget.update_plot(dataset, [red, green, blue])

    def update_contrast_brightness(self):
        """更新对比度和亮度"""
        contrast = self.contrast_slider.value() / 100.0
        brightness = self.brightness_slider.value() / 100.0

        self.image_canvas.contrast = contrast
        self.image_canvas.brightness = brightness
        self.image_canvas.update()

    def reset_adjustments(self):
        """重置调整"""
        self.contrast_slider.setValue(100)
        self.brightness_slider.setValue(0)

    def adjust_zoom(self, factor: float):
        """调整缩放"""
        self.image_canvas.zoom_level *= factor
        self.image_canvas.zoom_level = max(0.1, min(10.0, self.image_canvas.zoom_level))
        self.image_canvas.update()

    def fit_to_window(self):
        """适应窗口"""
        self.image_canvas.reset_view()

    def on_pixel_value_changed(self, x: int, y: int, values: Dict[int, float]):
        """像素值变化"""
        value_str = ", ".join([f"B{k}: {v:.1f}" for k, v in sorted(values.items())])
        self.pixel_value_label.setText(f"Value: {value_str}")

    def on_coordinate_changed(self, x: float, y: float):
        """坐标变化"""
        self.coordinate_label.setText(f"X: {x:.2f}, Y: {y:.2f}")

    def on_layer_visibility_changed(self, layer_name: str, visible: bool):
        """图层可见性变化"""
        self.log_widget.append_log('info', f"Layer '{layer_name}' visibility: {visible}")

    def on_layer_selected(self, layer_name: str):
        """图层选中"""
        # 查找并激活对应的数据集
        for path, dataset in self.data_manager.datasets.items():
            if os.path.basename(path) == layer_name:
                self.data_manager.set_active_dataset(path)
                self.attribute_panel.set_dataset(dataset)
                break

    def undo(self):
        """撤销"""
        self.message_label.setText("Undo not implemented yet")

    def redo(self):
        """重做"""
        self.message_label.setText("Redo not implemented yet")

    def show_preferences(self):
        """显示偏好设置"""
        QMessageBox.information(self, "Preferences", "Preferences dialog not implemented yet")

    def show_about(self):
        """显示关于"""
        QMessageBox.about(
            self,
            "About 山海辽凝遥感影像快速加工处理平台",
            "<h2>山海辽凝遥感影像快速加工处理平台</h2>"
            "<p>Version 1.0.0</p>"
            "<p>A professional remote sensing image processing platform.</p>"
            "<p>Built with PyQt6 and Python.</p>"
            "<p>&copy; 2024 All Rights Reserved.</p>"
        )

    def show_documentation(self):
        """显示文档"""
        QMessageBox.information(
            self,
            "Documentation",
            "Documentation viewer not implemented yet."
        )

    def batch_processing(self):
        """批量处理"""
        QMessageBox.information(
            self,
            "Batch Processing",
            "Batch processing dialog not implemented yet."
        )

    def add_to_recent_files(self, file_path: str):
        """添加到最近文件列表"""
        settings = QSettings("ShanHaiLiaoNing", "RemoteSensingPlatform")
        recent_files = settings.value("recentFiles", [])

        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        recent_files = recent_files[:5]  # 保留最多5个

        settings.setValue("recentFiles", recent_files)
        self.update_recent_files_menu(recent_files)

    def update_recent_files_menu(self, recent_files: List[str]):
        """更新最近文件菜单"""
        for i, file_path in enumerate(recent_files):
            if i < len(self.recent_files_actions):
                display_name = os.path.basename(file_path)
                self.recent_files_actions[i].setText(f"&{i + 1} {display_name}")
                self.recent_files_actions[i].setData(file_path)
                self.recent_files_actions[i].setVisible(True)

        for i in range(len(recent_files), len(self.recent_files_actions)):
            self.recent_files_actions[i].setVisible(False)

    def open_recent_file(self, index: int):
        """打开最近文件"""
        if index < len(self.recent_files_actions):
            file_path = self.recent_files_actions[index].data()
            if file_path and os.path.exists(file_path):
                self.load_file(file_path)
            else:
                QMessageBox.warning(self, "Warning", f"File not found: {file_path}")

    def load_settings(self):
        """加载设置"""
        settings = QSettings("ShanHaiLiaoNing", "RemoteSensingPlatform")
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)

        window_state = settings.value("windowState")
        if window_state:
            self.restoreState(window_state)

        # 加载最近文件
        recent_files = settings.value("recentFiles", [])
        self.update_recent_files_menu(recent_files)

    def closeEvent(self, event):
        """关闭事件"""
        settings = QSettings("ShanHaiLiaoNing", "RemoteSensingPlatform")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

        # 检查工作线程
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, 'Processing Running',
                'A processing task is still running. Quit anyway?',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return

        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("山海辽凝遥感影像快速加工处理平台")
    app.setOrganizationName("ShanHaiLiaoNing")

    # 设置应用程序样式
    app.setStyle("Fusion")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
