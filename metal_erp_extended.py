# ==============================================================================
# 第七部分：扩展业务模块 (Extended Business Modules)
# 包含采购管理、质量管理、BOM 管理、报表分析等高级功能
# ==============================================================================

class PurchaseOrderPage(QWidget):
    """采购订单管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("采购订单管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 统计卡片
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)
        
        self.stat_total = CardWidget("采购总额", "0", "万元")
        self.stat_pending = CardWidget("待入库", "0", "单")
        self.stat_overdue = CardWidget("已逾期", "0", "单")
        self.stat_supplier = CardWidget("合作供应商", "0", "家")
        
        for card in [self.stat_total, self.stat_pending, self.stat_overdue, self.stat_supplier]:
            stats_layout.addWidget(card)
        
        layout.addLayout(stats_layout)
        
        # 工具栏
        toolbar = QHBoxLayout()
        
        self.search_bar = SearchBar("搜索采购单号、供应商...")
        self.search_bar.search_signal.connect(self.filter_data)
        toolbar.addWidget(self.search_bar, stretch=1)
        
        self.supplier_filter = QComboBox()
        self.supplier_filter.addItems(["全部供应商"] + [s.name for s in db.suppliers])
        self.supplier_filter.setStyleSheet("""
            QComboBox {
                padding: 8px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        self.supplier_filter.currentTextChanged.connect(self.filter_data)
        toolbar.addWidget(self.supplier_filter)
        
        new_btn = ActionButton("+ 新建采购单", color="#4CAF50")
        new_btn.clicked.connect(self.create_purchase)
        toolbar.addWidget(new_btn)
        
        layout.addLayout(toolbar)
        
        # 表格
        headers = ["采购单号", "供应商", "下单日期", "期望到货", "总金额", "状态", "创建人", "备注"]
        self.table = DataTable(headers)
        self.table.doubleClicked.connect(self.view_detail)
        layout.addWidget(self.table, stretch=1)
        
        # 底部操作
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        receive_btn = ActionButton("入库验收", color="#2196F3")
        receive_btn.clicked.connect(self.receive_goods)
        btn_layout.addWidget(receive_btn)
        
        layout.addLayout(btn_layout)
    
    def load_data(self):
        self.update_stats()
        self.filter_data("")
    
    def update_stats(self):
        total_amount = sum(po.total_amount for po in db.purchase_orders) / 10000
        pending_count = sum(1 for po in db.purchase_orders if po.status in [OrderStatus.APPROVED, OrderStatus.PRODUCING])
        overdue_count = sum(1 for po in db.purchase_orders if po.expected_date < datetime.date.today() and po.status != OrderStatus.COMPLETED)
        supplier_count = len(set(po.supplier_id for po in db.purchase_orders))
        
        self.stat_total.set_value(f"{total_amount:.1f}", "万元")
        self.stat_pending.set_value(str(pending_count), "单")
        self.stat_overdue.set_value(str(overdue_count), "单")
        self.stat_supplier.set_value(str(supplier_count), "家")
    
    def filter_data(self, keyword: str):
        supplier_text = self.supplier_filter.currentText()
        
        self.table.setRowCount(0)
        
        for po in db.purchase_orders:
            if supplier_text != "全部供应商" and po.supplier_name != supplier_text:
                continue
            
            match = True
            if keyword:
                match = (keyword.lower() in po.order_no.lower() or 
                        keyword.lower() in po.supplier_name.lower())
            
            if match:
                row = [
                    po.order_no,
                    po.supplier_name,
                    po.order_date.strftime("%Y-%m-%d"),
                    po.expected_date.strftime("%Y-%m-%d"),
                    f"{po.total_amount:,.2f}",
                    po.status.value,
                    po.creator_id,
                    po.remark[:20] + "..." if len(po.remark) > 20 else po.remark
                ]
                self.table.add_row(row, po.id)
    
    def create_purchase(self):
        QMessageBox.information(self, "新建采购", "打开采购订单编辑界面")
    
    def view_detail(self, index: QModelIndex):
        row = index.row()
        po_id = self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        if po_id:
            QMessageBox.information(self, "采购详情", f"查看采购单详情：{po_id}")
    
    def receive_goods(self):
        QMessageBox.information(self, "入库验收", "打开入库验收界面")


class QualityManagementPage(QWidget):
    """质量管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("质量管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 质量指标
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        
        self.kpi_pass_rate = CardWidget("合格率", "0%", "")
        self.kpi_total_checks = CardWidget("检验批次", "0", "批")
        self.kpi_defects = CardWidget("不良数", "0", "件")
        self.kpi_customer_complaint = CardWidget("客诉", "0", "起")
        
        for card in [self.kpi_pass_rate, self.kpi_total_checks, self.kpi_defects, self.kpi_customer_complaint]:
            kpi_layout.addWidget(card)
        
        layout.addLayout(kpi_layout)
        
        # 选项卡
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                border-radius: 4px;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 10px 20px;
                border: 1px solid #404040;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
        """)
        
        # 检验记录 tab
        check_tab = QWidget()
        check_layout = QVBoxLayout(check_tab)
        
        check_toolbar = QHBoxLayout()
        self.check_type_filter = QComboBox()
        self.check_type_filter.addItems(["全部类型", "IQC", "IPQC", "OQC"])
        self.check_type_filter.setStyleSheet("""
            QComboBox {
                padding: 6px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        check_toolbar.addWidget(QLabel("检验类型:"))
        check_toolbar.addWidget(self.check_type_filter)
        check_toolbar.addStretch()
        
        new_check_btn = ActionButton("+ 新建检验", color="#2196F3")
        new_check_btn.clicked.connect(self.new_inspection)
        check_toolbar.addWidget(new_check_btn)
        
        check_layout.addLayout(check_toolbar)
        
        check_headers = ["检验单号", "来源", "物料", "检验日期", "样本数", "不良数", "结果", "检验员"]
        self.check_table = DataTable(check_headers)
        check_layout.addWidget(self.check_table)
        
        self.tabs.addTab(check_tab, "检验记录")
        
        # 不合格品处理 tab
        ncr_tab = QWidget()
        ncr_layout = QVBoxLayout(ncr_tab)
        
        ncr_headers = ["NCR 编号", "来源单号", "物料", "不合格数量", "发现日期", "处理方式", "状态", "责任人"]
        self.ncr_table = DataTable(ncr_headers)
        ncr_layout.addWidget(self.ncr_table)
        
        ncr_btn_layout = QHBoxLayout()
        ncr_btn_layout.addStretch()
        
        process_btn = ActionButton("处理不合格品", color="#FF9800")
        process_btn.clicked.connect(self.process_ncr)
        ncr_btn_layout.addWidget(process_btn)
        
        ncr_layout.addLayout(ncr_btn_layout)
        
        self.tabs.addTab(ncr_tab, "不合格品处理")
        
        # 质量趋势 tab
        trend_tab = QWidget()
        trend_layout = QVBoxLayout(trend_tab)
        
        if HAS_PYQTGRAPH:
            self.quality_plot = pg.PlotWidget()
            self.quality_plot.setBackground('#1E1E1E')
            self.quality_plot.getAxis('left').setPen('#B0B0B0')
            self.quality_plot.getAxis('bottom').setPen('#B0B0B0')
            self.quality_plot.showGrid(x=True, y=True, alpha=0.3)
            
            # 模拟合格率趋势
            x_data = list(range(30))
            y_data = [random.uniform(95, 99.5) for _ in range(30)]
            
            self.quality_plot.plot(x_data, y_data, pen='#4CAF50', name='合格率 (%)')
            self.quality_plot.setYRange(90, 100)
            
            trend_layout.addWidget(self.quality_plot)
        else:
            label = QLabel("[质量趋势图区域]")
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setStyleSheet("color: #B0B0B0; padding: 50px;")
            trend_layout.addWidget(label)
        
        self.tabs.addTab(trend_tab, "质量趋势分析")
        
        layout.addWidget(self.tabs, stretch=1)
    
    def load_data(self):
        self.update_kpi()
        self.load_check_records()
        self.load_ncr_records()
    
    def update_kpi(self):
        if db.quality_checks:
            passed = sum(1 for qc in db.quality_checks if qc.result == QualityResult.PASSED)
            pass_rate = passed / len(db.quality_checks) * 100
            total_defects = sum(qc.defect_count for qc in db.quality_checks)
        else:
            pass_rate = 0
            total_defects = 0
        
        self.kpi_pass_rate.set_value(f"{pass_rate:.1f}%", "")
        self.kpi_total_checks.set_value(str(len(db.quality_checks)), "批")
        self.kpi_defects.set_value(str(total_defects), "件")
        self.kpi_customer_complaint.set_value(str(random.randint(0, 5)), "起")
    
    def load_check_records(self):
        self.check_table.setRowCount(0)
        
        for qc in db.quality_checks:
            source = f"{qc.source_type}-{qc.source_id[:8]}"
            mat = db.get_by_id('materials', qc.material_id)
            mat_name = mat.name if mat else "未知物料"
            
            row = [
                qc.check_no,
                source,
                mat_name,
                qc.check_date.strftime("%Y-%m-%d %H:%M"),
                str(qc.sample_size),
                str(qc.defect_count),
                qc.result.value,
                qc.inspector_id
            ]
            self.check_table.add_row(row, qc.id)
    
    def load_ncr_records(self):
        # 模拟 NCR 数据
        ncr_data = [
            ("NCR-20240407-001", "WO-20240407-0012", "板材 - 型号 M0023", "5", "2024-04-07", "返工", "处理中", "张三"),
            ("NCR-20240406-003", "PO-20240406-0008", "标准件 - 型号 M0045", "12", "2024-04-06", "退货", "已完成", "李四"),
        ]
        
        self.ncr_table.setRowCount(0)
        for row in ncr_data:
            self.ncr_table.add_row(row)
    
    def new_inspection(self):
        QMessageBox.information(self, "新建检验", "打开检验单录入界面")
    
    def process_ncr(self):
        QMessageBox.information(self, "不合格品处理", "打开 NCR 处理流程界面")


class BOMManagementPage(QWidget):
    """BOM 管理页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        self.load_data()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("BOM 管理")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # 左侧：产品树
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("产品结构树"))
        
        self.product_tree = QTreeWidget()
        self.product_tree.setHeaderLabels(["物料编码", "物料名称", "用量"])
        self.product_tree.setStyleSheet("""
            QTreeWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QTreeWidget::item {
                padding: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #326CE5;
            }
        """)
        left_layout.addWidget(self.product_tree)
        
        splitter.addWidget(left_widget)
        
        # 右侧：BOM 明细
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_toolbar = QHBoxLayout()
        right_toolbar.addWidget(QLabel("当前产品:"))
        self.current_product_label = QLabel("未选择")
        self.current_product_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        right_toolbar.addWidget(self.current_product_label)
        right_toolbar.addStretch()
        
        edit_btn = ActionButton("编辑 BOM", color="#2196F3")
        edit_btn.clicked.connect(self.edit_bom)
        right_toolbar.addWidget(edit_btn)
        
        right_layout.addLayout(right_toolbar)
        
        bom_headers = ["子件编码", "子件名称", "规格", "单位", "单机用量", "损耗率", "生效日期", "版本"]
        self.bom_table = DataTable(bom_headers)
        right_layout.addWidget(self.bom_table)
        
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter, stretch=1)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        import_btn = ActionButton("导入 BOM", color="#FF9800")
        import_btn.clicked.connect(self.import_bom)
        btn_layout.addWidget(import_btn)
        
        export_btn = ActionButton("导出 BOM", color="#4CAF50")
        export_btn.clicked.connect(self.export_bom)
        btn_layout.addWidget(export_btn)
        
        layout.addLayout(btn_layout)
    
    def load_data(self):
        self.load_product_tree()
    
    def load_product_tree(self):
        self.product_tree.clear()
        
        finished_goods = [m for m in db.materials if m.category == "成品"]
        
        for fg in finished_goods[:10]:
            item = QTreeWidgetItem([fg.code, fg.name, "1"])
            item.setData(0, Qt.ItemDataRole.UserRole, fg.id)
            
            # 加载子件
            children = [b for b in db.bom_items if b.parent_material_id == fg.id]
            for child in children:
                child_mat = db.get_by_id('materials', child.child_material_id)
                if child_mat:
                    child_item = QTreeWidgetItem([
                        child_mat.code,
                        child_mat.name,
                        f"{child.quantity:.2f}"
                    ])
                    item.addChild(child_item)
            
            self.product_tree.addTopLevelItem(item)
        
        self.product_tree.expandAll()
        self.product_tree.itemClicked.connect(self.on_product_selected)
    
    def on_product_selected(self, item: QTreeWidgetItem, column: int):
        product_id = item.data(0, Qt.ItemDataRole.UserRole)
        if product_id:
            product = db.get_by_id('materials', product_id)
            if product:
                self.current_product_label.setText(f"{product.code} - {product.name}")
                self.load_bom_detail(product_id)
    
    def load_bom_detail(self, product_id: str):
        self.bom_table.setRowCount(0)
        
        children = [b for b in db.bom_items if b.parent_material_id == product_id]
        
        for child in sorted(children, key=lambda x: x.sequence):
            child_mat = db.get_by_id('materials', child.child_material_id)
            if child_mat:
                row = [
                    child_mat.code,
                    child_mat.name,
                    child_mat.spec,
                    child_mat.unit,
                    f"{child.quantity:.3f}",
                    f"{child.loss_rate:.2%}",
                    "2024-01-01",
                    "V1.0"
                ]
                self.bom_table.add_row(row, child.id)
    
    def edit_bom(self):
        QMessageBox.information(self, "编辑 BOM", "打开 BOM 编辑器")
    
    def import_bom(self):
        QMessageBox.information(self, "导入 BOM", "从 Excel 导入 BOM 数据")
    
    def export_bom(self):
        QMessageBox.information(self, "导出 BOM", "导出 BOM 到 Excel")


class ReportAnalysisPage(QWidget):
    """报表分析页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("报表分析中心")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 报表类型选择
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("报表类型:"))
        
        self.report_type = QComboBox()
        self.report_type.addItems([
            "生产日报", "销售分析", "库存周转分析", "质量月报", 
            "设备 OEE 分析", "成本分析", "交付准时率分析"
        ])
        self.report_type.setStyleSheet("""
            QComboBox {
                padding: 8px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
                min-width: 200px;
            }
        """)
        self.report_type.currentTextChanged.connect(self.generate_report)
        type_layout.addWidget(self.report_type)
        
        type_layout.addWidget(QLabel("日期范围:"))
        
        self.start_date = QDateEdit()
        self.start_date.setDate(QDate.currentDate().addDays(-30))
        self.start_date.setCalendarPopup(True)
        self.start_date.setStyleSheet("""
            QDateEdit {
                padding: 6px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        type_layout.addWidget(self.start_date)
        
        type_layout.addWidget(QLabel("至"))
        
        self.end_date = QDateEdit()
        self.end_date.setDate(QDate.currentDate())
        self.end_date.setCalendarPopup(True)
        self.end_date.setStyleSheet(self.start_date.styleSheet())
        type_layout.addWidget(self.end_date)
        
        generate_btn = ActionButton("生成报表", color="#2196F3")
        generate_btn.clicked.connect(self.generate_report)
        type_layout.addWidget(generate_btn)
        
        type_layout.addStretch()
        layout.addLayout(type_layout)
        
        # 报表内容区
        self.report_content = QTextEdit()
        self.report_content.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 15px;
                font-family: "Microsoft YaHei";
                font-size: 12px;
            }
        """)
        self.report_content.setReadOnly(True)
        layout.addWidget(self.report_content, stretch=1)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        print_btn = ActionButton("打印", color="#FF9800")
        print_btn.clicked.connect(self.print_report)
        btn_layout.addWidget(print_btn)
        
        export_pdf_btn = ActionButton("导出 PDF", color="#F44336")
        export_pdf_btn.clicked.connect(self.export_pdf)
        btn_layout.addWidget(export_pdf_btn)
        
        layout.addLayout(btn_layout)
        
        # 初始生成
        self.generate_report()
    
    def generate_report(self):
        report_type = self.report_type.currentText()
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ color: white; font-family: "Microsoft YaHei"; }}
                h1 {{ color: #2196F3; text-align: center; }}
                h2 {{ color: #4CAF50; border-bottom: 1px solid #404040; padding-bottom: 5px; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #404040; padding: 10px; text-align: left; }}
                th {{ background-color: #2D2D2D; }}
                .kpi {{ display: inline-block; margin: 10px; padding: 20px; background-color: #2D2D2D; 
                       border-radius: 8px; text-align: center; min-width: 150px; }}
                .kpi-value {{ font-size: 28px; color: #2196F3; font-weight: bold; }}
                .kpi-label {{ color: #B0B0B0; margin-top: 5px; }}
            </style>
        </head>
        <body>
            <h1>{report_type}</h1>
            <p style="text-align: center; color: #B0B0B0;">统计期间：{start} 至 {end}</p>
            
            <h2>关键指标</h2>
            <div class="kpi">
                <div class="kpi-value">{random.randint(100, 500)}</div>
                <div class="kpi-label">订单总数</div>
            </div>
            <div class="kpi">
                <div class="kpi-value">{random.uniform(80, 99):.1f}%</div>
                <div class="kpi-label">完成率</div>
            </div>
            <div class="kpi">
                <div class="kpi-value">{random.uniform(95, 99):.2f}%</div>
                <div class="kpi-label">合格率</div>
            </div>
            <div class="kpi">
                <div class="kpi-value">¥{random.randint(50, 200):,}万</div>
                <div class="kpi-label">总产值</div>
            </div>
            
            <h2>详细数据</h2>
            <table>
                <tr>
                    <th>日期</th>
                    <th>计划产量</th>
                    <th>实际产量</th>
                    <th>差异率</th>
                    <th>合格数</th>
                    <th>不良数</th>
                </tr>
        """
        
        # 生成模拟数据行
        for i in range(15):
            date = f"2024-04-{i+1:02d}"
            plan = random.randint(80, 150)
            actual = random.randint(75, 155)
            diff = (actual - plan) / plan * 100 if plan > 0 else 0
            good = int(actual * random.uniform(0.95, 0.99))
            bad = actual - good
            
            html_content += f"""
                <tr>
                    <td>{date}</td>
                    <td>{plan}</td>
                    <td>{actual}</td>
                    <td style="color: {'#4CAF50' if diff >= 0 else '#F44336'}">{diff:+.1f}%</td>
                    <td>{good}</td>
                    <td style="color: #F44336">{bad}</td>
                </tr>
            """
        
        html_content += """
            </table>
            
            <h2>分析总结</h2>
            <p>本期生产整体运行平稳，产能利用率达到较高水平。产品质量稳定，合格率保持在目标值以上。</p>
            <p>建议关注以下事项：</p>
            <ul>
                <li>加强原材料入库检验，减少来料不良</li>
                <li>优化生产排程，提高设备利用率</li>
                <li>关注员工技能培训，提升操作熟练度</li>
            </ul>
            
            <p style="margin-top: 50px; text-align: right; color: #B0B0B0;">
                生成时间：""" + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """
            </p>
        </body>
        </html>
        """
        
        self.report_content.setHtml(html_content)
    
    def print_report(self):
        QMessageBox.information(self, "打印", "发送报表到打印机")
    
    def export_pdf(self):
        QMessageBox.information(self, "导出 PDF", "报表已导出为 PDF 文件")


# ==============================================================================
# 第八部分：系统设置模块 (System Settings Module)
# 用户管理、权限配置、系统日志等功能
# ==============================================================================

class SystemSettingsPage(QWidget):
    """系统设置页面"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        title = QLabel("系统设置")
        title.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title)
        
        # 设置选项卡
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #404040;
                border-radius: 4px;
                background-color: #1E1E1E;
            }
            QTabBar::tab {
                background-color: #2D2D2D;
                color: #B0B0B0;
                padding: 10px 20px;
                border: 1px solid #404040;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #1E1E1E;
                color: #FFFFFF;
            }
        """)
        
        # 用户管理 tab
        user_tab = self.create_user_management_tab()
        self.tabs.addTab(user_tab, "用户管理")
        
        # 权限配置 tab
        role_tab = self.create_role_management_tab()
        self.tabs.addTab(role_tab, "角色权限")
        
        # 系统日志 tab
        log_tab = self.create_system_log_tab()
        self.tabs.addTab(log_tab, "系统日志")
        
        # 参数配置 tab
        config_tab = self.create_config_tab()
        self.tabs.addTab(config_tab, "系统参数")
        
        layout.addWidget(self.tabs, stretch=1)
    
    def create_user_management_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("搜索用户:"))
        
        search_input = QLineEdit()
        search_input.setPlaceholderText("输入用户名或姓名...")
        search_input.setStyleSheet("""
            QLineEdit {
                padding: 6px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        toolbar.addWidget(search_input)
        
        add_user_btn = ActionButton("+ 添加用户", color="#4CAF50")
        add_user_btn.clicked.connect(lambda: QMessageBox.information(self, "添加用户", "打开用户编辑对话框"))
        toolbar.addWidget(add_user_btn)
        
        layout.addLayout(toolbar)
        
        user_headers = ["用户名", "姓名", "部门", "角色", "邮箱", "手机", "状态", "最后登录"]
        user_table = DataTable(user_headers)
        
        for user in db.users:
            row = [
                user.username,
                user.real_name,
                user.department,
                user.role,
                user.email,
                user.phone,
                "正常" if user.is_active else "禁用",
                user.last_login.strftime("%Y-%m-%d %H:%M") if user.last_login else "从未"
            ]
            user_table.add_row(row, user.id)
        
        layout.addWidget(user_table)
        
        return tab
    
    def create_role_management_tab(self) -> QWidget:
        tab = QWidget()
        layout = QHBoxLayout(tab)
        
        # 左侧角色列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        left_layout.addWidget(QLabel("角色列表"))
        self.role_list = QListWidget()
        self.role_list.addItems(["系统管理员", "部门经理", "销售经理", "计划员", "采购员", "仓管员", "操作员", "质检员"])
        self.role_list.setStyleSheet("""
            QListWidget {
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #326CE5;
            }
        """)
        left_layout.addWidget(self.role_list)
        
        layout.addWidget(left_widget, stretch=1)
        
        # 右侧权限配置
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        right_layout.addWidget(QLabel("权限配置"))
        
        perm_group = QGroupBox("功能权限")
        perm_layout = QVBoxLayout(perm_group)
        
        permissions = [
            "销售管理 - 查看", "销售管理 - 新增", "销售管理 - 修改", "销售管理 - 删除",
            "生产管理 - 查看", "生产管理 - 派工", "生产管理 - 报工",
            "库存管理 - 查看", "库存管理 - 入库", "库存管理 - 出库",
            "采购管理 - 查看", "采购管理 - 下单",
            "质量管理 - 查看", "质量管理 - 检验",
            "系统设置 - 查看", "系统设置 - 修改"
        ]
        
        for perm in permissions:
            cb = QCheckBox(perm)
            cb.setStyleSheet("color: #FFFFFF; padding: 3px;")
            perm_layout.addWidget(cb)
        
        right_layout.addWidget(perm_group)
        
        save_btn = ActionButton("保存权限", color="#2196F3")
        save_btn.clicked.connect(lambda: QMessageBox.information(self, "保存", "权限配置已保存"))
        right_layout.addWidget(save_btn)
        
        layout.addWidget(right_widget, stretch=2)
        
        return tab
    
    def create_system_log_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("日志级别:"))
        
        level_filter = QComboBox()
        level_filter.addItems(["全部", "INFO", "WARNING", "ERROR"])
        level_filter.setStyleSheet("""
            QComboBox {
                padding: 6px;
                background-color: #1E1E1E;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 4px;
            }
        """)
        filter_layout.addWidget(level_filter)
        
        clear_btn = ActionButton("清空日志", color="#F44336")
        clear_btn.clicked.connect(lambda: QMessageBox.information(self, "清空", "日志已清空"))
        filter_layout.addWidget(clear_btn)
        
        filter_layout.addStretch()
        layout.addLayout(filter_layout)
        
        log_text = QTextEdit()
        log_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #B0B0B0;
                border: 1px solid #404040;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        log_text.setReadOnly(True)
        
        # 生成模拟日志
        logs = []
        for i in range(50):
            timestamp = datetime.datetime.now() - datetime.timedelta(minutes=i*10)
            level = random.choice(["INFO", "INFO", "INFO", "WARNING", "ERROR"])
            module = random.choice(["Sales", "Production", "Inventory", "Equipment", "User"])
            message = f"操作日志：{module} 模块执行了某项操作，ID={random.randint(1000, 9999)}"
            
            color = "#4CAF50" if level == "INFO" else "#FF9800" if level == "WARNING" else "#F44336"
            logs.append(f'<span style="color: {color}">[{timestamp.strftime("%Y-%m-%d %H:%M:%S")}] [{level}] [{module}] {message}</span>')
        
        log_text.setHtml("<br>".join(logs))
        layout.addWidget(log_text)
        
        return tab
    
    def create_config_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        configs = [
            ("公司名称", COMPANY_NAME),
            ("系统标题", APP_NAME),
            ("默认仓库", "原材料仓 00"),
            ("安全库存预警天数", "7"),
            ("订单自动审核金额上限", "100000"),
            ("会话超时时间 (分钟)", "30"),
            ("最大上传文件大小 (MB)", "50"),
            ("数据备份周期 (天)", "7")
        ]
        
        for label, value in configs:
            input_widget = QLineEdit(value)
            input_widget.setStyleSheet("""
                QLineEdit {
                    padding: 8px;
                    background-color: #1E1E1E;
                    color: #FFFFFF;
                    border: 1px solid #404040;
                    border-radius: 4px;
                }
            """)
            form_layout.addRow(label, input_widget)
        
        layout.addLayout(form_layout)
        layout.addStretch()
        
        save_btn = ActionButton("保存配置", color="#4CAF50")
        save_btn.clicked.connect(lambda: QMessageBox.information(self, "保存", "系统配置已保存"))
        layout.addWidget(save_btn)
        
        return tab


# ==============================================================================
# 第九部分：登录窗口 (Login Window)
# 用户认证入口
# ==============================================================================

class LoginWindow(QDialog):
    """登录窗口"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("用户登录")
        self.setFixedSize(450, 550)
        self.setStyleSheet("""
            QDialog {
                background-color: #1E1E1E;
            }
        """)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 40, 50, 40)
        layout.setSpacing(20)
        
        # Logo 和标题
        logo_label = QLabel("🏭")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet("font-size: 64px;")
        layout.addWidget(logo_label)
        
        title_label = QLabel("金属制品生产全流程协同管理平台")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setFont(QFont("Microsoft YaHei", 14, QFont.Weight.Bold))
        title_label.setStyleSheet("color: #FFFFFF;")
        layout.addWidget(title_label)
        
        subtitle_label = QLabel("Metal Products Production Collaborative Management Platform")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet("color: #B0B0B0; font-size: 11px;")
        layout.addWidget(subtitle_label)
        
        layout.addSpacing(20)
        
        # 表单
        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        
        # 用户名
        username_input = QLineEdit()
        username_input.setPlaceholderText("请输入用户名")
        username_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow("用户名:", username_input)
        
        # 密码
        password_input = QLineEdit()
        password_input.setPlaceholderText("请输入密码")
        password_input.setEchoMode(QLineEdit.EchoMode.Password)
        password_input.setStyleSheet("""
            QLineEdit {
                padding: 12px;
                background-color: #2D2D2D;
                color: #FFFFFF;
                border: 1px solid #404040;
                border-radius: 6px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border: 1px solid #2196F3;
            }
        """)
        form_layout.addRow("密码:", password_input)
        
        layout.addLayout(form_layout)
        
        # 记住我 & 忘记密码
        options_layout = QHBoxLayout()
        
        remember_cb = QCheckBox("记住我")
        remember_cb.setStyleSheet("color: #B0B0B0;")
        options_layout.addWidget(remember_cb)
        
        forgot_link = QPushButton("忘记密码？")
        forgot_link.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #2196F3;
                border: none;
                text-decoration: underline;
            }
        """)
        forgot_link.clicked.connect(lambda: QMessageBox.information(self, "忘记密码", "请联系系统管理员重置密码"))
        options_layout.addWidget(forgot_link)
        
        layout.addLayout(options_layout)
        
        # 登录按钮
        login_btn = QPushButton("登 录")
        login_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                padding: 14px;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        login_btn.clicked.connect(self.do_login)
        layout.addWidget(login_btn)
        
        # 版本信息
        version_label = QLabel(f"Version {APP_VERSION} © {COMPANY_NAME}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version_label.setStyleSheet("color: #606060; font-size: 10px; margin-top: 20px;")
        layout.addWidget(version_label)
    
    def do_login(self):
        # 简化登录逻辑，实际应验证数据库
        QMessageBox.information(self, "登录成功", "欢迎使用金属 ERP 平台！")
        self.accept()


# ==============================================================================
# 第十部分：更新的主函数 (Updated Main Function)
# ==============================================================================

def main_extended():
    """扩展版应用程序入口，包含登录流程"""
    logger.info(f"启动 {APP_NAME} v{APP_VERSION}")
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
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
    
    # 显示登录窗口
    login_window = LoginWindow()
    if login_window.exec() == QDialog.DialogCode.Accepted:
        # 登录成功后显示主窗口
        window = MainWindow()
        
        # 将新页面添加到主窗口
        extended_pages = {
            "purchase": PurchaseOrderPage(),
            "quality": QualityManagementPage(),
            "bom": BOMManagementPage(),
            "reports": ReportAnalysisPage(),
            "settings": SystemSettingsPage()
        }
        
        # 需要重新初始化主窗口的 pages
        for key, page in extended_pages.items():
            window.pages[key] = page
            window.stack.addWidget(page)
        
        window.show()
        sys.exit(app.exec())
    else:
        sys.exit(0)


if __name__ == "__main__":
    main_extended()
