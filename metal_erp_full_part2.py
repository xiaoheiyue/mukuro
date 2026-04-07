# ==============================================================================
# 第四部分：自定义 UI 组件库 (Custom UI Components)
# 提供统一的视觉风格和交互体验
# ==============================================================================

class StatusLabel(QLabel):
    """状态标签组件，根据状态自动变色"""
    
    STATUS_COLORS = {
        "草稿": "#9E9E9E",
        "待审核": "#FF9800",
        "已审核": "#2196F3",
        "生产中": "#00BCD4",
        "部分发货": "#FFC107",
        "已完成": "#4CAF50",
        "已取消": "#F44336",
        "正常": "#4CAF50",
        "低库存": "#FF9800",
        "缺货": "#F44336",
        "已预留": "#9C27B0",
        "损坏": "#795548",
        "运行中": "#4CAF50",
        "空闲": "#2196F3",
        "维护中": "#FF9800",
        "故障": "#F44336",
        "离线": "#607D8B",
        "合格": "#4CAF50",
        "不合格": "#F44336",
        "让步接收": "#FF9800",
        "返工": "#FFC107",
        "待检": "#9E9E9E",
        "低": "#4CAF50",
        "中": "#2196F3",
        "高": "#FF9800",
        "紧急": "#F44336"
    }

    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                color: white;
                min-width: 60px;
            }
        """)
        self.update_color(text)

    def update_color(self, text: str):
        color = self.STATUS_COLORS.get(text, "#9E9E9E")
        self.setStyleSheet(f"""
            QLabel {{
                padding: 4px 8px;
                border-radius: 4px;
                font-weight: bold;
                color: white;
                background-color: {color};
                min-width: 60px;
            }}
        """)


class CardWidget(QFrame):
    """卡片式容器组件，用于仪表盘和列表项"""
    
    def __init__(self, title: str = "", content: str = "", icon: str = "", parent=None):
        super().__init__(parent)
        self.setObjectName("CardWidget")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame#CardWidget {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #404040;
            }
            QFrame#CardWidget:hover {
                border: 1px solid #2196F3;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        # 标题栏
        header_layout = QHBoxLayout()
        self.title_label = QLabel(title)
        self.title_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        self.title_label.setStyleSheet("color: #FFFFFF;")
        header_layout.addWidget(self.title_label)
        
        if icon:
            icon_label = QLabel(icon)
            icon_label.setStyleSheet("color: #2196F3; font-size: 18px;")
            header_layout.addStretch()
            header_layout.addWidget(icon_label)
        
        layout.addLayout(header_layout)
        
        # 内容
        self.content_label = QLabel(content)
        self.content_label.setFont(QFont("Microsoft YaHei", 10))
        self.content_label.setStyleSheet("color: #B0B0B0;")
        self.content_label.setWordWrap(True)
        layout.addWidget(self.content_label)
        
        layout.addStretch()

    def set_value(self, value: str, unit: str = ""):
        """设置主要数值显示"""
        self.content_label.setText(f"<span style='font-size: 24px; color: #2196F3; font-weight: bold;'>{value}</span> {unit}")
        self.content_label.adjustSize()


class SearchBar(QWidget):
    """通用搜索栏组件"""
    search_signal = pyqtSignal(str)
    
    def __init__(self, placeholder: str = "请输入关键词搜索...", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(placeholder)
        self.search_input.setFont(QFont("Microsoft YaHei", 10))
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #404040;
                border-radius: 4px;
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        self.search_input.textChanged.connect(self.search_signal.emit)
        
        self.clear_btn = QPushButton("✕")
        self.clear_btn.setFixedSize(30, 30)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: #FFFFFF;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #F44336;
            }
        """)
        self.clear_btn.clicked.connect(lambda: self.search_input.setText(""))
        
        layout.addWidget(self.search_input)
        layout.addWidget(self.clear_btn)


class ActionButton(QPushButton):
    """带图标的操作按钮"""
    
    def __init__(self, text: str, icon_char: str = "", color: str = "#2196F3", parent=None):
        super().__init__(text, parent)
        self.setIcon_char = icon_char
        self.base_color = color
        
        self.setStyleSheet(self._get_style())
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        
    def _get_style(self):
        return f"""
            QPushButton {{
                background-color: {self.base_color};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {self._lighten_color(self.base_color)};
            }}
            QPushButton:pressed {{
                background-color: {self._darken_color(self.base_color)};
            }}
        """
    
    def _lighten_color(self, color: str) -> str:
        # 简单变亮逻辑
        return color
    
    def _darken_color(self, color: str) -> str:
        # 简单变暗逻辑
        return color


class DataTable(QTableWidget):
    """增强的数据表格组件"""
    
    def __init__(self, headers: List[str], parent=None):
        super().__init__(parent)
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        self.setStyleSheet("""
            QTableWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                gridline-color: #404040;
            }
            QTableWidget::item {
                padding: 8px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #326CE5;
            }
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #FFFFFF;
                padding: 8px;
                border: none;
                border-bottom: 2px solid #404040;
                font-weight: bold;
            }
            QScrollBar:vertical {
                background-color: #1E1E1E;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background-color: #404040;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        # 设置属性
        self.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.doubleClicked.connect(self._on_double_click)
        
    def _on_double_click(self, index: QModelIndex):
        """双击事件，可重写"""
        pass
    
    def add_row(self, data: List[Any], row_id: str = ""):
        """添加一行数据"""
        row_pos = self.rowCount()
        self.insertRow(row_pos)
        for col, value in enumerate(data):
            item = QTableWidgetItem(str(value))
            item.setData(Qt.ItemDataRole.UserRole, row_id)
            self.setItem(row_pos, col, item)
    
    def get_selected_row_data(self) -> Optional[Dict[str, Any]]:
        """获取选中行的数据"""
        selected_rows = self.selectedItems()
        if not selected_rows:
            return None
        
        row = selected_rows[0].row()
        data = {}
        row_id = ""
        for col in range(self.columnCount()):
            item = self.item(row, col)
            if item:
                data[self.horizontalHeaderItem(col).text()] = item.text()
                if col == 0:
                    row_id = item.data(Qt.ItemDataRole.UserRole) or ""
        data['_row_id'] = row_id
        return data


class ModalDialog(QDialog):
    """通用模态对话框"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
        """)
        
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel(title)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #2196F3; padding: 10px;")
        layout.addWidget(title_label)
        
        # 内容区域 (由子类填充)
        self.content_layout = QVBoxLayout()
        layout.addLayout(self.content_layout)
        
        # 按钮区
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #2196F3;
            }
        """)
        layout.addWidget(button_box)


# ==============================================================================
# 第五部分：业务页面模块 (Business Pages)
# 包含各个功能模块的具体实现
# ==============================================================================

class DashboardPage(QWidget):
    """系统仪表盘页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.start_timers()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # 顶部标题
        title = QLabel("生产运营驾驶舱")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF; padding: 10px 0;")
        main_layout.addWidget(title)
        
        # KPI 卡片区域
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(15)
        
        self.kpi_cards = {}
        kpi_configs = [
            ("今日订单", "0", "单", "#2196F3"),
            ("本月产值", "0", "万元", "#4CAF50"),
            ("在制工单", "0", "张", "#FF9800"),
            ("设备 OEE", "0", "%", "#00BCD4"),
            ("库存周转", "0", "天", "#9C27B0"),
            ("不良率", "0", "%", "#F44336"),
            ("准时交付", "0", "%", "#FFC107"),
            ("客户满意度", "0", "分", "#E91E63")
        ]
        
        for i, (title, value, unit, color) in enumerate(kpi_configs):
            card = CardWidget(title, "")
            card.set_value(value, unit)
            card.setStyleSheet(f"""
                QFrame#CardWidget {{
                    background-color: #2D2D2D;
                    border-radius: 8px;
                    border-left: 4px solid {color};
                }}
            """)
            self.kpi_cards[title] = card
            kpi_layout.addWidget(card, i // 4, i % 4)
        
        main_layout.addLayout(kpi_layout)
        
        # 中部图表区域
        chart_layout = QHBoxLayout()
        chart_layout.setSpacing(20)
        
        # 左侧：生产趋势图
        trend_group = QGroupBox("近 7 日生产趋势")
        trend_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 8px;
                margin-top: 15px;
                padding-top: 15px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
            }
        """)
        trend_layout = QVBoxLayout(trend_group)
        
        if HAS_PYQTGRAPH:
            self.trend_plot = pg.PlotWidget()
            self.trend_plot.setBackground('#1E1E1E')
            self.trend_plot.getAxis('left').setPen('#B0B0B0')
            self.trend_plot.getAxis('bottom').setPen('#B0B0B0')
            self.trend_plot.showGrid(x=True, y=True, alpha=0.3)
            
            # 模拟数据
            x_data = list(range(7))
            y1_data = [random.randint(50, 150) for _ in range(7)]
            y2_data = [random.randint(40, 140) for _ in range(7)]
            
            line1 = self.trend_plot.plot(x_data, y1_data, pen='#2196F3', name='计划产量')
            line2 = self.trend_plot.plot(x_data, y2_data, pen='#4CAF50', name='实际产量')
            self.trend_plot.addLegend()
            
            trend_layout.addWidget(self.trend_plot)
        else:
            label = QLabel("[图表区域：请安装 pyqtgraph 以显示趋势图]")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #B0B0B0; padding: 50px;")
            trend_layout.addWidget(label)
        
        chart_layout.addWidget(trend_group, stretch=2)
        
        # 右侧：设备状态
        status_group = QGroupBox("设备实时状态")
        status_group.setStyleSheet(trend_group.styleSheet())
        status_layout = QVBoxLayout(status_group)
        
        self.device_scroll = QScrollArea()
        self.device_scroll.setWidgetResizable(True)
        self.device_scroll.setStyleSheet("border: none;")
        
        device_container = QWidget()
        self.device_layout = QVBoxLayout(device_container)
        self.device_layout.setSpacing(10)
        
        # 动态生成设备状态卡片
        self.device_cards = {}
        for eq in db.equipments[:8]:
            card = self.create_device_card(eq)
            self.device_layout.addWidget(card)
        
        self.device_scroll.setWidget(device_container)
        status_layout.addWidget(self.device_scroll)
        
        chart_layout.addWidget(status_group, stretch=1)
        
        main_layout.addLayout(chart_layout, stretch=1)
        
        # 底部：待办事项
        todo_group = QGroupBox("今日待办事项")
        todo_group.setStyleSheet(trend_group.styleSheet())
        todo_layout = QVBoxLayout(todo_group)
        
        self.todo_table = DataTable(["优先级", "类型", "内容", "截止时间", "责任人"])
        self.load_todo_data()
        todo_layout.addWidget(self.todo_table)
        
        main_layout.addWidget(todo_group, stretch=1)
    
    def create_device_card(self, equipment: Equipment) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #1E1E1E;
                border-radius: 4px;
                border: 1px solid #404040;
            }
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(10, 8, 10, 8)
        
        # 状态指示灯
        status_color = {
            EquipmentStatus.RUNNING: "#4CAF50",
            EquipmentStatus.IDLE: "#2196F3",
            EquipmentStatus.MAINTENANCE: "#FF9800",
            EquipmentStatus.BROKEN: "#F44336",
            EquipmentStatus.OFFLINE: "#607D8B"
        }.get(equipment.status, "#9E9E9E")
        
        indicator = QLabel("●")
        indicator.setStyleSheet(f"color: {status_color}; font-size: 20px;")
        layout.addWidget(indicator)
        
        # 信息
        info_layout = QVBoxLayout()
        name_label = QLabel(f"{equipment.name} ({equipment.code})")
        name_label.setStyleSheet("color: #FFFFFF; font-weight: bold;")
        info_layout.addWidget(name_label)
        
        oee_label = QLabel(f"OEE: {equipment.oee:.1%}  运行时长：{equipment.running_hours:.1f}h")
        oee_label.setStyleSheet("color: #B0B0B0; font-size: 12px;")
        info_layout.addWidget(oee_label)
        
        layout.addLayout(info_layout, stretch=1)
        
        # 状态文本
        status_label = StatusLabel(equipment.status.value)
        layout.addWidget(status_label)
        
        return card
    
    def load_todo_data(self):
        todos = [
            ("紧急", "生产", "工单 WO-20240407-0012 物料短缺", "今天 14:00", "张三"),
            ("高", "质检", "批次 B2024040605 复检", "今天 16:00", "李四"),
            ("中", "设备", "冲压机 C-03 定期保养", "明天 09:00", "王五"),
            ("低", "采购", "供应商 S-008 资质审核", "本周五", "赵六"),
        ]
        for t in todos:
            self.todo_table.add_row(t)
    
    def start_timers(self):
        # 定时刷新 KPI
        self.kpi_timer = QTimer()
        self.kpi_timer.timeout.connect(self.update_kpi)
        self.kpi_timer.start(5000)  # 5 秒刷新一次
        
        # 定时刷新设备状态
        self.device_timer = QTimer()
        self.device_timer.timeout.connect(self.update_devices)
        self.device_timer.start(3000)
    
    def update_kpi(self):
        """模拟 KPI 数据更新"""
        updates = {
            "今日订单": (str(random.randint(10, 50)), "单"),
            "本月产值": (str(random.randint(500, 2000)), "万元"),
            "在制工单": (str(random.randint(20, 60)), "张"),
            "设备 OEE": (f"{random.uniform(75, 95):.1f}", "%"),
            "库存周转": (f"{random.uniform(5, 15):.1f}", "天"),
            "不良率": (f"{random.uniform(0.5, 3.0):.2f}", "%"),
            "准时交付": (f"{random.uniform(90, 99):.1f}", "%"),
            "客户满意度": (f"{random.uniform(4.5, 5.0):.1f}", "分")
        }
        
        for title, (value, unit) in updates.items():
            if title in self.kpi_cards:
                self.kpi_cards[title].set_value(value, unit)
    
    def update_devices(self):
        """模拟设备状态更新"""
        # 随机更新 OEE
        for i, eq in enumerate(db.equipments[:8]):
            eq.oee = max(0.6, min(0.98, eq.oee + random.uniform(-0.05, 0.05)))
            eq.running_hours += 0.1
            
        # 重新渲染 (简化处理，实际应只更新变化的部分)
        while self.device_layout.count():
            item = self.device_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        for eq in db.equipments[:8]:
            card = self.create_device_card(eq)
            self.device_layout.addWidget(card)


class SalesOrderPage(QWidget):
    """销售订单管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("销售订单管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.search_bar = SearchBar("搜索订单号、客户名称...")
        self.search_bar.search_signal.connect(self.filter_data)
        toolbar.addWidget(self.search_bar, stretch=1)
        
        # 筛选下拉框
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部状态"] + [s.value for s in OrderStatus])
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        self.status_filter.currentTextChanged.connect(self.filter_data)
        toolbar.addWidget(self.status_filter)
        
        # 新建按钮
        new_btn = ActionButton("+ 新建订单", color="#4CAF50")
        new_btn.clicked.connect(self.create_order)
        toolbar.addWidget(new_btn)
        
        # 导出按钮
        export_btn = ActionButton("导出 Excel", color="#FF9800")
        toolbar.addWidget(export_btn)
        
        layout.addLayout(toolbar)
        
        # 数据表格
        headers = ["订单号", "客户名称", "订单日期", "交货日期", "金额 (元)", "状态", "优先级", "创建人"]
        self.table = DataTable(headers)
        self.table.doubleClicked.connect(self.view_order_detail)
        layout.addWidget(self.table, stretch=1)
        
        # 状态栏
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #B0B0B0;")
        layout.addWidget(self.status_label)
    
    def load_data(self):
        self.table.setRowCount(0)
        for order in db.sales_orders:
            row = [
                order.order_no,
                order.customer_name,
                order.order_date.strftime("%Y-%m-%d"),
                order.delivery_date.strftime("%Y-%m-%d"),
                f"{order.total_amount:,.2f}",
                order.status.value,
                order.priority.value,
                order.creator_id
            ]
            self.table.add_row(row, order.id)
        
        self.status_label.setText(f"共 {len(db.sales_orders)} 条记录")
    
    def filter_data(self, keyword: str):
        status_text = self.status_filter.currentText()
        count = 0
        self.table.setRowCount(0)
        
        for order in db.sales_orders:
            # 状态筛选
            if status_text != "全部状态" and order.status.value != status_text:
                continue
            
            # 关键词筛选
            match = True
            if keyword:
                match = (keyword.lower() in order.order_no.lower() or 
                        keyword.lower() in order.customer_name.lower())
            
            if match:
                row = [
                    order.order_no,
                    order.customer_name,
                    order.order_date.strftime("%Y-%m-%d"),
                    order.delivery_date.strftime("%Y-%m-%d"),
                    f"{order.total_amount:,.2f}",
                    order.status.value,
                    order.priority.value,
                    order.creator_id
                ]
                self.table.add_row(row, order.id)
                count += 1
        
        self.status_label.setText(f"筛选结果：{count} 条记录")
    
    def create_order(self):
        QMessageBox.information(self, "提示", "新建订单功能演示\n此处应弹出订单编辑表单")
    
    def view_order_detail(self, index: QModelIndex):
        row = index.row()
        order_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if order_id:
            QMessageBox.information(self, "订单详情", f"查看订单详情：{order_id}\n此处应显示详细信息表单")


class InventoryPage(QWidget):
    """库存管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("库存管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.search_bar = SearchBar("搜索物料编码、名称...")
        self.search_bar.search_signal.connect(self.filter_data)
        toolbar.addWidget(self.search_bar, stretch=1)
        
        self.warehouse_filter = QComboBox()
        self.warehouse_filter.addItems(["全部仓库"] + [wh.name for wh in db.warehouses])
        self.warehouse_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        self.warehouse_filter.currentTextChanged.connect(self.filter_data)
        toolbar.addWidget(self.warehouse_filter)
        
        # 预警开关
        self.warning_only = QCheckBox("仅显示预警")
        self.warning_only.setStyleSheet("color: #FFFFFF;")
        self.warning_only.stateChanged.connect(self.filter_data)
        toolbar.addWidget(self.warning_only)
        
        layout.addLayout(toolbar)
        
        # 统计卡片
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.stat_normal = CardWidget("正常物料", "0", "种")
        self.stat_low = CardWidget("低库存", "0", "种")
        self.stat_out = CardWidget("缺货", "0", "种")
        
        for card in [self.stat_normal, self.stat_low, self.stat_out]:
            stats_layout.addWidget(card)
        
        layout.addLayout(stats_layout)
        
        # 表格
        headers = ["物料编码", "物料名称", "规格", "仓库", "当前库存", "锁定库存", "可用库存", "安全库存", "状态", "库位"]
        self.table = DataTable(headers)
        layout.addWidget(self.table, stretch=1)
        
        # 底部信息
        self.info_label = QLabel("")
        self.info_label.setStyleSheet("color: #B0B0B0;")
        layout.addWidget(self.info_label)
    
    def load_data(self):
        self.update_stats()
        self.filter_data("")
    
    def update_stats(self):
        normal_count = sum(1 for inv in db.inventory_records if inv.status == InventoryStatus.NORMAL)
        low_count = sum(1 for inv in db.inventory_records if inv.status == InventoryStatus.LOW_STOCK)
        out_count = sum(1 for inv in db.inventory_records if inv.status == InventoryStatus.OUT_OF_STOCK)
        
        self.stat_normal.set_value(str(normal_count), "种")
        self.stat_low.set_value(str(low_count), "种")
        self.stat_low.setStyleSheet("""
            QFrame#CardWidget {
                background-color: #2D2D2D;
                border-radius: 8px;
                border-left: 4px solid #FF9800;
            }
        """)
        self.stat_out.set_value(str(out_count), "种")
        self.stat_out.setStyleSheet("""
            QFrame#CardWidget {
                background-color: #2D2D2D;
                border-radius: 8px;
                border-left: 4px solid #F44336;
            }
        """)
    
    def filter_data(self, keyword: str):
        warehouse_text = self.warehouse_filter.currentText()
        show_warning = self.warning_only.isChecked()
        
        self.table.setRowCount(0)
        count = 0
        
        for inv in db.inventory_records:
            # 仓库筛选
            if warehouse_text != "全部仓库" and inv.warehouse_name != warehouse_text:
                continue
            
            # 预警筛选
            if show_warning and inv.status == InventoryStatus.NORMAL:
                continue
            
            # 关键词筛选
            match = True
            if keyword:
                match = (keyword.lower() in inv.material_code.lower() or 
                        keyword.lower() in inv.material_name.lower())
            
            if match:
                available = inv.quantity - inv.locked_quantity
                row = [
                    inv.material_code,
                    inv.material_name,
                    inv.batch_no,  # Using batch_no as spec placeholder
                    inv.warehouse_name,
                    f"{inv.quantity:.2f}",
                    f"{inv.locked_quantity:.2f}",
                    f"{available:.2f}",
                    f"{db.get_by_id('materials', inv.material_id).safety_stock if db.get_by_id('materials', inv.material_id) else 0:.2f}",
                    inv.status.value,
                    inv.location
                ]
                self.table.add_row(row, inv.id)
                count += 1
        
        self.info_label.setText(f"共 {count} 条库存记录")
    
    def create_order(self):
        QMessageBox.information(self, "提示", "库存操作功能演示")


class WorkOrderPage(QWidget):
    """生产工单管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("生产工单管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 进度概览
        progress_layout = QHBoxLayout()
        progress_layout.setSpacing(15)
        
        self.progress_total = CardWidget("总计划量", "0")
        self.progress_completed = CardWidget("已完成", "0")
        self.progress_scrap = CardWidget("报废量", "0")
        self.progress_rate = CardWidget("完成率", "0%")
        
        for card in [self.progress_total, self.progress_completed, self.progress_scrap, self.progress_rate]:
            progress_layout.addWidget(card)
        
        layout.addLayout(progress_layout)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.search_bar = SearchBar("搜索工单号、物料...")
        self.search_bar.search_signal.connect(self.filter_data)
        toolbar.addWidget(self.search_bar, stretch=1)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部状态", "PRODUCING", "COMPLETED", "PENDING"])
        self.status_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        self.status_filter.currentTextChanged.connect(self.filter_data)
        toolbar.addWidget(self.status_filter)
        
        layout.addLayout(toolbar)
        
        # 表格
        headers = ["工单号", "关联订单", "物料名称", "计划数量", "完成数量", "报废数量", "工作中心", "状态", "优先级", "开始日期", "结束日期"]
        self.table = DataTable(headers)
        layout.addWidget(self.table, stretch=1)
        
        # 操作按钮区
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        report_btn = ActionButton("报工", color="#2196F3")
        report_btn.clicked.connect(self.report_work)
        btn_layout.addWidget(report_btn)
        
        scrap_btn = ActionButton("报废登记", color="#F44336")
        btn_layout.addWidget(scrap_btn)
        
        finish_btn = ActionButton("完工入库", color="#4CAF50")
        btn_layout.addWidget(finish_btn)
        
        layout.addLayout(btn_layout)
    
    def load_data(self):
        self.update_progress()
        self.filter_data("")
    
    def update_progress(self):
        total = sum(wo.plan_qty for wo in db.work_orders)
        completed = sum(wo.completed_qty for wo in db.work_orders)
        scrap = sum(wo.scrap_qty for wo in db.work_orders)
        rate = (completed / total * 100) if total > 0 else 0
        
        self.progress_total.set_value(f"{total:,.0f}")
        self.progress_completed.set_value(f"{completed:,.0f}")
        self.progress_scrap.set_value(f"{scrap:,.0f}")
        self.progress_rate.set_value(f"{rate:.1f}%")
    
    def filter_data(self, keyword: str):
        status_text = self.status_filter.currentText()
        
        self.table.setRowCount(0)
        
        for wo in db.work_orders:
            if status_text != "全部状态" and wo.status != status_text:
                continue
            
            match = True
            if keyword:
                match = (keyword.lower() in wo.wo_no.lower() or 
                        keyword.lower() in wo.material_name.lower())
            
            if match:
                row = [
                    wo.wo_no,
                    wo.sales_order_no,
                    wo.material_name,
                    f"{wo.plan_qty:.2f}",
                    f"{wo.completed_qty:.2f}",
                    f"{wo.scrap_qty:.2f}",
                    wo.work_center_name,
                    wo.status,
                    wo.priority.value,
                    wo.start_date.strftime("%Y-%m-%d"),
                    wo.end_date.strftime("%Y-%m-%d")
                ]
                self.table.add_row(row, wo.id)
    
    def report_work(self):
        QMessageBox.information(self, "报工", "报工功能演示\n此处应弹出报工表单")


class EquipmentPage(QWidget):
    """设备管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
        self.start_timer()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("设备监控与管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 统计
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.stat_running = CardWidget("运行中", "0", "台")
        self.stat_idle = CardWidget("空闲", "0", "台")
        self.stat_maint = CardWidget("维护中", "0", "台")
        self.stat_broken = CardWidget("故障", "0", "台")
        
        for card in [self.stat_running, self.stat_idle, self.stat_maint, self.stat_broken]:
            stats_layout.addWidget(card)
        
        layout.addLayout(stats_layout)
        
        # 设备网格
        self.device_scroll = QScrollArea()
        self.device_scroll.setWidgetResizable(True)
        self.device_scroll.setStyleSheet("border: 1px solid #404040; border-radius: 8px;")
        
        self.device_container = QWidget()
        self.device_grid = QGridLayout(self.device_container)
        self.device_grid.setSpacing(15)
        self.device_grid.setContentsMargins(15, 15, 15, 15)
        
        self.device_scroll.setWidget(self.device_container)
        layout.addWidget(self.device_scroll, stretch=1)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        maintain_btn = ActionButton("维护保养", color="#FF9800")
        maintain_btn.clicked.connect(self.open_maintenance)
        btn_layout.addWidget(maintain_btn)
        
        repair_btn = ActionButton("故障报修", color="#F44336")
        btn_layout.addWidget(repair_btn)
        
        layout.addLayout(btn_layout)
    
    def load_data(self):
        self.update_stats()
        self.render_devices()
    
    def update_stats(self):
        counts = defaultdict(int)
        for eq in db.equipments:
            counts[eq.status.value] += 1
        
        self.stat_running.set_value(str(counts.get("运行中", 0)), "台")
        self.stat_idle.set_value(str(counts.get("空闲", 0)), "台")
        self.stat_maint.set_value(str(counts.get("维护中", 0)), "台")
        self.stat_broken.set_value(str(counts.get("故障", 0)), "台")
    
    def render_devices(self):
        # 清空现有
        while self.device_grid.count():
            item = self.device_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 重新添加
        for i, eq in enumerate(db.equipments):
            card = self.create_device_card(eq)
            row = i // 3
            col = i % 3
            self.device_grid.addWidget(card, row, col)
    
    def create_device_card(self, equipment: Equipment) -> QFrame:
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-radius: 8px;
                border: 1px solid #404040;
            }
            QFrame:hover {
                border: 1px solid #2196F3;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # 头部
        header = QHBoxLayout()
        name_label = QLabel(f"{equipment.name}")
        name_label.setFont(QFont("Microsoft YaHei", 12, QFont.Weight.Bold))
        name_label.setStyleSheet("color: #FFFFFF;")
        header.addWidget(name_label)
        
        status_label = StatusLabel(equipment.status.value)
        header.addWidget(status_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # 信息
        info_layout = QFormLayout()
        info_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        info_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        style = "color: #B0B0B0;"
        
        info_layout.addRow("设备编码:", QLabel(f"<span style='{style}'>{equipment.code}</span>"))
        info_layout.addRow("型号:", QLabel(f"<span style='{style}'>{equipment.model}</span>"))
        
        # OEE 进度条
        oee_progress = QProgressBar()
        oee_progress.setValue(int(equipment.oee * 100))
        oee_progress.setFormat("%.1f%%" % (equipment.oee * 100))
        oee_progress.setStyleSheet("""
            QProgressBar {
                background-color: #1E1E1E;
                border-radius: 4px;
                text-align: center;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #2196F3;
                border-radius: 4px;
            }
        """)
        info_layout.addRow("OEE:", oee_progress)
        
        info_layout.addRow("运行时长:", QLabel(f"<span style='{style}'>{equipment.running_hours:.1f} h</span>"))
        info_layout.addRow("下次保养:", QLabel(f"<span style='{style}'>{equipment.next_maintenance.strftime('%Y-%m-%d')}</span>"))
        
        layout.addLayout(info_layout)
        
        # 操作按钮
        btn_layout = QHBoxLayout()
        
        detail_btn = QPushButton("详情")
        detail_btn.setStyleSheet("""
            QPushButton {
                background-color: #404040;
                color: white;
                border: none;
                padding: 6px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #2196F3;
            }
        """)
        btn_layout.addWidget(detail_btn)
        
        layout.addLayout(btn_layout)
        
        return card
    
    def start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(5000)
    
    def refresh_data(self):
        # 模拟数据变化
        for eq in db.equipments:
            if eq.status == EquipmentStatus.RUNNING:
                eq.oee = max(0.6, min(0.98, eq.oee + random.uniform(-0.02, 0.02)))
                eq.running_hours += 0.1
        
        self.update_stats()
        self.render_devices()
    
    def open_maintenance(self):
        QMessageBox.information(self, "维护保养", "打开维护保养工单界面")


# ==============================================================================
# 第六部分：主窗口与应用程序入口 (Main Window & Entry Point)
# ==============================================================================

class MainWindow(QMainWindow):
    """主应用程序窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(1400, 900)
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1E1E1E;
            }
        """)
        
        self.init_ui()
        logger.info("主窗口初始化完成")
    
    def init_ui(self):
        # 中央控件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 左侧导航栏
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # 右侧内容区
        content_area = QVBoxLayout()
        content_area.setContentsMargins(0, 0, 0, 0)
        content_area.setSpacing(0)
        
        # 顶部栏
        top_bar = self.create_top_bar()
        content_area.addWidget(top_bar)
        
        # 页面堆栈
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("background-color: #1E1E1E;")
        
        # 添加页面
        self.pages = {
            "dashboard": DashboardPage(),
            "sales": SalesOrderPage(),
            "inventory": InventoryPage(),
            "production": WorkOrderPage(),
            "equipment": EquipmentPage()
        }
        
        for page in self.pages.values():
            self.stack.addWidget(page)
        
        content_area.addWidget(self.stack, stretch=1)
        main_layout.addLayout(content_area, stretch=1)
        
        # 状态栏
        self.statusBar().showMessage(f"欢迎使用 {APP_NAME} v{APP_VERSION}")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 5px;
            }
        """)
    
    def create_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setFixedWidth(220)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-right: 1px solid #404040;
            }
        """)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 20, 0, 0)
        layout.setSpacing(5)
        
        # Logo 区域
        logo_label = QLabel("金属 ERP 平台")
        logo_label.setFont(QFont("Microsoft YaHei", 16, QFont.Weight.Bold))
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("color: #2196F3; padding: 20px 0;")
        layout.addWidget(logo_label)
        
        # 导航菜单
        menu_items = [
            ("dashboard", "📊 仪表盘"),
            ("sales", "📝 销售管理"),
            ("planning", "📅 计划管理"),
            ("purchase", "🛒 采购管理"),
            ("inventory", "📦 库存管理"),
            ("production", "🏭 生产管理"),
            ("quality", "✅ 质量管理"),
            ("equipment", "🔧 设备管理"),
            ("settings", "⚙️ 系统设置")
        ]
        
        self.nav_buttons = {}
        for key, text in menu_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setStyleSheet(self.get_nav_button_style())
            btn.clicked.connect(lambda checked, k=key: self.navigate_to(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn
        
        # 默认选中第一个
        self.nav_buttons["dashboard"].setChecked(True)
        
        layout.addStretch()
        
        # 用户信息
        user_info = QLabel("当前用户：管理员")
        user_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        user_info.setStyleSheet("color: #B0B0B0; padding: 15px;")
        layout.addWidget(user_info)
        
        return sidebar
    
    def get_nav_button_style(self) -> str:
        return """
            QPushButton {
                background-color: transparent;
                color: #B0B0B0;
                text-align: left;
                padding: 12px 20px;
                border: none;
                border-left: 3px solid transparent;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #3D3D3D;
                color: #FFFFFF;
            }
            QPushButton:checked {
                background-color: #326CE5;
                color: #FFFFFF;
                border-left: 3px solid #FFFFFF;
            }
        """
    
    def create_top_bar(self) -> QWidget:
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet("""
            QFrame {
                background-color: #2D2D2D;
                border-bottom: 1px solid #404040;
            }
        """)
        
        layout = QHBoxLayout(top_bar)
        layout.setContentsMargins(20, 0, 20, 0)
        
        # 面包屑
        self.breadcrumb = QLabel("首页 / 仪表盘")
        self.breadcrumb.setStyleSheet("color: #B0B0B0; font-size: 14px;")
        layout.addWidget(self.breadcrumb)
        
        layout.addStretch()
        
        # 通知图标
        notify_btn = QPushButton("🔔")
        notify_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #FFFFFF;
                border: none;
                font-size: 18px;
                padding: 5px;
            }
        """)
        layout.addWidget(notify_btn)
        
        # 时间显示
        self.time_label = QLabel("")
        self.time_label.setStyleSheet("color: #FFFFFF; font-size: 14px;")
        layout.addWidget(self.time_label)
        
        # 更新时间
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self.update_time)
        self.time_timer.start(1000)
        self.update_time()
        
        return top_bar
    
    def update_time(self):
        now = datetime.datetime.now()
        self.time_label.setText(now.strftime("%Y-%m-%d %H:%M:%S"))
    
    def navigate_to(self, page_key: str):
        if page_key in self.pages:
            self.stack.setCurrentWidget(self.pages[page_key])
            self.breadcrumb.setText(f"首页 / {page_key}")
            
            # 更新按钮状态
            for key, btn in self.nav_buttons.items():
                btn.setChecked(key == page_key)
            
            logger.info(f"导航至页面：{page_key}")
        elif page_key in ["planning", "purchase", "quality", "settings"]:
            QMessageBox.information(self, "功能开发中", f"{page_key} 模块正在开发中...\n当前演示版本包含：仪表盘、销售、库存、生产、设备管理。")
            # 返回到上一个有效页面
            self.nav_buttons["dashboard"].setChecked(True)
            self.stack.setCurrentIndex(0)


def main():
    """应用程序入口"""
    logger.info(f"启动 {APP_NAME} v{APP_VERSION}")
    
    # 创建应用
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # 设置全局字体
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # 设置调色板
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(COLORS["dark_bg"]))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(COLORS["text_main"]))
    palette.setColor(QPalette.ColorRole.Base, QColor(COLORS["panel_bg"]))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(COLORS["dark_bg"]))
    palette.setColor(QPalette.ColorRole.Text, QColor(COLORS["text_main"]))
    palette.setColor(QPalette.ColorRole.Button, QColor(COLORS["panel_bg"]))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(COLORS["text_main"]))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(COLORS["selected"]))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(COLORS["text_main"]))
    app.setPalette(palette)
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    # 进入事件循环
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
