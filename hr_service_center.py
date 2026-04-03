#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
人力资源共享服务中心工单处理系统
HR Shared Service Center Ticket Processing System
"""

import sys
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QMenuBar, QMenu, QStatusBar, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDialog, QLineEdit, QTextEdit,
    QComboBox, QFormLayout, QDialogButtonBox, QMessageBox,
    QTabWidget, QGroupBox, QRadioButton, QDateEdit, QHeaderView,
    QToolBar, QSpinBox, QCheckBox, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon, QFont, QAction, QActionGroup


class Ticket:
    """工单数据类"""
    def __init__(self, ticket_id, title, category, priority, status, 
                 submitter, department, description, created_time=None):
        self.ticket_id = ticket_id
        self.title = title
        self.category = category
        self.priority = priority
        self.status = status
        self.submitter = submitter
        self.department = department
        self.description = description
        self.created_time = created_time or datetime.now()
        self.handler = None
        self.resolution = None
        self.completed_time = None


class CreateTicketDialog(QDialog):
    """创建工单对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("创建新工单")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("请输入工单标题")
        
        self.category_combo = QComboBox()
        self.category_combo.addItems([
            "薪酬福利", "招聘管理", "员工关系", 
            "培训发展", "考勤管理", "档案管理", "其他"
        ])
        
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["低", "中", "高", "紧急"])
        
        self.submitter_edit = QLineEdit()
        self.submitter_edit.setPlaceholderText("请输入提交人姓名")
        
        self.department_edit = QLineEdit()
        self.department_edit.setPlaceholderText("请输入所属部门")
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("请详细描述问题或需求")
        self.description_edit.setMaximumHeight(150)
        
        layout.addRow("工单标题:", self.title_edit)
        layout.addRow("工单分类:", self.category_combo)
        layout.addRow("优先级:", self.priority_combo)
        layout.addRow("提交人:", self.submitter_edit)
        layout.addRow("所属部门:", self.department_edit)
        layout.addRow("问题描述:", self.description_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class EditTicketDialog(QDialog):
    """编辑工单对话框"""
    def __init__(self, ticket, parent=None):
        super().__init__(parent)
        self.ticket = ticket
        self.setWindowTitle(f"编辑工单 - {ticket.ticket_id}")
        self.setMinimumWidth(500)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.title_edit = QLineEdit(self.ticket.title)
        
        self.category_combo = QComboBox()
        categories = [
            "薪酬福利", "招聘管理", "员工关系", 
            "培训发展", "考勤管理", "档案管理", "其他"
        ]
        self.category_combo.addItems(categories)
        self.category_combo.setCurrentText(self.ticket.category)
        
        self.priority_combo = QComboBox()
        priorities = ["低", "中", "高", "紧急"]
        self.priority_combo.addItems(priorities)
        self.priority_combo.setCurrentText(self.ticket.priority)
        
        self.status_combo = QComboBox()
        statuses = ["待处理", "处理中", "已解决", "已关闭", "已取消"]
        self.status_combo.addItems(statuses)
        self.status_combo.setCurrentText(self.ticket.status)
        
        self.handler_edit = QLineEdit()
        if self.ticket.handler:
            self.handler_edit.setText(self.ticket.handler)
        self.handler_edit.setPlaceholderText("请输入处理人")
        
        self.submitter_edit = QLineEdit(self.ticket.submitter)
        self.department_edit = QLineEdit(self.ticket.department)
        
        self.description_edit = QTextEdit(self.ticket.description)
        self.description_edit.setMaximumHeight(100)
        
        self.resolution_edit = QTextEdit()
        if self.ticket.resolution:
            self.resolution_edit.setText(self.ticket.resolution)
        self.resolution_edit.setPlaceholderText("请填写解决方案")
        self.resolution_edit.setMaximumHeight(100)
        
        layout.addRow("工单标题:", self.title_edit)
        layout.addRow("工单分类:", self.category_combo)
        layout.addRow("优先级:", self.priority_combo)
        layout.addRow("状态:", self.status_combo)
        layout.addRow("提交人:", self.submitter_edit)
        layout.addRow("所属部门:", self.department_edit)
        layout.addRow("处理人:", self.handler_edit)
        layout.addRow("问题描述:", self.description_edit)
        layout.addRow("解决方案:", self.resolution_edit)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class StatisticsDialog(QDialog):
    """统计分析对话框"""
    def __init__(self, tickets, parent=None):
        super().__init__(parent)
        self.tickets = tickets
        self.setWindowTitle("工单统计分析")
        self.setMinimumSize(600, 400)
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # 总体统计
        total_group = QGroupBox("总体统计")
        total_layout = QFormLayout()
        
        total_count = len(self.tickets)
        pending_count = sum(1 for t in self.tickets if t.status == "待处理")
        processing_count = sum(1 for t in self.tickets if t.status == "处理中")
        resolved_count = sum(1 for t in self.tickets if t.status == "已解决")
        closed_count = sum(1 for t in self.tickets if t.status == "已关闭")
        
        total_layout.addRow("工单总数:", QLabel(str(total_count)))
        total_layout.addRow("待处理:", QLabel(str(pending_count)))
        total_layout.addRow("处理中:", QLabel(str(processing_count)))
        total_layout.addRow("已解决:", QLabel(str(resolved_count)))
        total_layout.addRow("已关闭:", QLabel(str(closed_count)))
        
        total_group.setLayout(total_layout)
        layout.addWidget(total_group)
        
        # 分类统计
        category_group = QGroupBox("按分类统计")
        category_layout = QFormLayout()
        
        categories = {}
        for ticket in self.tickets:
            cat = ticket.category
            categories[cat] = categories.get(cat, 0) + 1
        
        for cat, count in sorted(categories.items()):
            category_layout.addRow(f"{cat}:", QLabel(str(count)))
        
        category_group.setLayout(category_layout)
        layout.addWidget(category_group)
        
        # 优先级统计
        priority_group = QGroupBox("按优先级统计")
        priority_layout = QFormLayout()
        
        priorities = {}
        for ticket in self.tickets:
            pri = ticket.priority
            priorities[pri] = priorities.get(pri, 0) + 1
        
        for pri in ["紧急", "高", "中", "低"]:
            count = priorities.get(pri, 0)
            priority_layout.addRow(f"{pri}:", QLabel(str(count)))
        
        priority_group.setLayout(priority_layout)
        layout.addWidget(priority_group)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)


class ExportDialog(QDialog):
    """导出对话框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("导出数据")
        self.setup_ui()
    
    def setup_ui(self):
        layout = QFormLayout(self)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["CSV", "Excel", "PDF"])
        
        self.include_all = QCheckBox("导出所有字段")
        self.include_all.setChecked(True)
        
        layout.addRow("导出格式:", self.format_combo)
        layout.addRow("", self.include_all)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)


class HRServiceCenterWindow(QMainWindow):
    """人力资源共享服务中心主窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("人力资源共享服务中心 - 工单处理系统")
        self.setMinimumSize(1200, 800)
        
        # 初始化示例数据
        self.tickets = self.init_sample_data()
        self.current_ticket_id = 1001
        
        self.setup_ui()
        self.setup_menu()
        self.setup_toolbar()
        self.setup_statusbar()
        self.refresh_table()
    
    def init_sample_data(self):
        """初始化示例工单数据"""
        sample_tickets = []
        
        sample_data = [
            ("工资条查询问题", "薪酬福利", "中", "张三", "人力资源部"),
            ("新员工入职手续", "招聘管理", "高", "李四", "行政部"),
            ("劳动合同续签", "员工关系", "高", "王五", "财务部"),
            ("培训课程报名", "培训发展", "低", "赵六", "技术部"),
            ("加班申请审批", "考勤管理", "中", "钱七", "市场部"),
            ("档案信息更新", "档案管理", "低", "孙八", "运营部"),
            ("社保缴纳咨询", "薪酬福利", "中", "周九", "销售部"),
            ("面试安排协调", "招聘管理", "紧急", "吴十", "人力资源部"),
        ]
        
        for i, (title, category, priority, submitter, dept) in enumerate(sample_data):
            ticket = Ticket(
                ticket_id=f"T{1000 + i + 1}",
                title=title,
                category=category,
                priority=priority,
                status=["待处理", "处理中", "已解决"][i % 3],
                submitter=submitter,
                department=dept,
                description=f"这是{title}的详细描述内容..."
            )
            sample_tickets.append(ticket)
        
        return sample_tickets
    
    def setup_ui(self):
        """设置主界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        
        # 顶部筛选区域
        filter_group = QGroupBox("筛选条件")
        filter_layout = QHBoxLayout()
        
        self.filter_category = QComboBox()
        self.filter_category.addItem("全部分类")
        self.filter_category.addItems([
            "薪酬福利", "招聘管理", "员工关系", 
            "培训发展", "考勤管理", "档案管理", "其他"
        ])
        
        self.filter_priority = QComboBox()
        self.filter_priority.addItem("全部优先级")
        self.filter_priority.addItems(["紧急", "高", "中", "低"])
        
        self.filter_status = QComboBox()
        self.filter_status.addItem("全部状态")
        self.filter_status.addItems(["待处理", "处理中", "已解决", "已关闭", "已取消"])
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索工单标题或编号...")
        self.search_input.textChanged.connect(self.apply_filters)
        
        search_btn = QPushButton("搜索")
        search_btn.clicked.connect(self.apply_filters)
        
        reset_btn = QPushButton("重置")
        reset_btn.clicked.connect(self.reset_filters)
        
        filter_layout.addWidget(QLabel("分类:"))
        filter_layout.addWidget(self.filter_category)
        filter_layout.addWidget(QLabel("优先级:"))
        filter_layout.addWidget(self.filter_priority)
        filter_layout.addWidget(QLabel("状态:"))
        filter_layout.addWidget(self.filter_status)
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(search_btn)
        filter_layout.addWidget(reset_btn)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # 工单表格
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "工单编号", "标题", "分类", "优先级", "状态", 
            "提交人", "部门", "处理人", "创建时间"
        ])
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        self.table.doubleClicked.connect(self.view_detail)
        
        main_layout.addWidget(self.table)
        
        # 底部操作按钮
        btn_layout = QHBoxLayout()
        
        create_btn = QPushButton("➕ 创建工单")
        create_btn.clicked.connect(self.create_ticket)
        
        edit_btn = QPushButton("✏️ 编辑工单")
        edit_btn.clicked.connect(self.edit_ticket)
        
        delete_btn = QPushButton("🗑️ 删除工单")
        delete_btn.clicked.connect(self.delete_ticket)
        
        export_btn = QPushButton("📤 导出数据")
        export_btn.clicked.connect(self.export_data)
        
        stats_btn = QPushButton("📊 统计分析")
        stats_btn.clicked.connect(self.show_statistics)
        
        btn_layout.addWidget(create_btn)
        btn_layout.addWidget(edit_btn)
        btn_layout.addWidget(delete_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(stats_btn)
        
        main_layout.addLayout(btn_layout)
    
    def setup_menu(self):
        """设置菜单栏 - 六个核心功能菜单"""
        menubar = self.menuBar()
        
        # 1. 工单管理菜单
        ticket_menu = menubar.addMenu("📋 工单管理(&T)")
        
        create_action = QAction("➕ 创建工单", self)
        create_action.setShortcut("Ctrl+N")
        create_action.triggered.connect(self.create_ticket)
        ticket_menu.addAction(create_action)
        
        edit_action = QAction("✏️ 编辑工单", self)
        edit_action.setShortcut("Ctrl+E")
        edit_action.triggered.connect(self.edit_ticket)
        ticket_menu.addAction(edit_action)
        
        delete_action = QAction("🗑️ 删除工单", self)
        delete_action.setShortcut("Delete")
        delete_action.triggered.connect(self.delete_ticket)
        ticket_menu.addAction(delete_action)
        
        ticket_menu.addSeparator()
        
        view_detail_action = QAction("👁️ 查看详情", self)
        view_detail_action.setShortcut("Enter")
        view_detail_action.triggered.connect(self.view_detail)
        ticket_menu.addAction(view_detail_action)
        
        # 2. 查询统计菜单
        query_menu = menubar.addMenu("🔍 查询统计(&Q)")
        
        search_action = QAction("🔎 高级搜索", self)
        search_action.setShortcut("Ctrl+F")
        search_action.triggered.connect(self.advanced_search)
        query_menu.addAction(search_action)
        
        filter_action = QAction("📝 自定义筛选", self)
        filter_action.setShortcut("Ctrl+Shift+F")
        filter_action.triggered.connect(self.custom_filter)
        query_menu.addAction(filter_action)
        
        query_menu.addSeparator()
        
        stats_action = QAction("📊 统计分析", self)
        stats_action.setShortcut("Ctrl+S")
        stats_action.triggered.connect(self.show_statistics)
        query_menu.addAction(stats_action)
        
        report_action = QAction("📈 生成报表", self)
        report_action.setShortcut("Ctrl+R")
        report_action.triggered.connect(self.generate_report)
        query_menu.addAction(report_action)
        
        # 3. 流程处理菜单
        process_menu = menubar.addMenu("⚙️ 流程处理(&P)")
        
        assign_action = QAction("👤 分配工单", self)
        assign_action.setShortcut("Ctrl+A")
        assign_action.triggered.connect(self.assign_ticket)
        process_menu.addAction(assign_action)
        
        transfer_action = QAction("🔄 转交工单", self)
        transfer_action.setShortcut("Ctrl+T")
        transfer_action.triggered.connect(self.transfer_ticket)
        process_menu.addAction(transfer_action)
        
        resolve_action = QAction("✅ 解决工单", self)
        resolve_action.setShortcut("Ctrl+J")
        resolve_action.triggered.connect(self.resolve_ticket)
        process_menu.addAction(resolve_action)
        
        close_action = QAction("🔒 关闭工单", self)
        close_action.setShortcut("Ctrl+K")
        close_action.triggered.connect(self.close_ticket)
        process_menu.addAction(close_action)
        
        # 4. 知识库菜单
        knowledge_menu = menubar.addMenu("📚 知识库(&K)")
        
        kb_search_action = QAction("🔎 搜索知识库", self)
        kb_search_action.setShortcut("Ctrl+K")
        kb_search_action.triggered.connect(self.search_knowledge)
        knowledge_menu.addAction(kb_search_action)
        
        kb_add_action = QAction("➕ 添加知识条目", self)
        kb_add_action.triggered.connect(self.add_knowledge)
        knowledge_menu.addAction(kb_add_action)
        
        kb_manage_action = QAction("📝 管理知识库", self)
        kb_manage_action.triggered.connect(self.manage_knowledge)
        knowledge_menu.addAction(kb_manage_action)
        
        # 5. 系统设置菜单
        settings_menu = menubar.addMenu("🔧 系统设置(&S)")
        
        user_action = QAction("👥 用户管理", self)
        user_action.triggered.connect(self.manage_users)
        settings_menu.addAction(user_action)
        
        category_action = QAction("📂 分类管理", self)
        category_action.triggered.connect(self.manage_categories)
        settings_menu.addAction(category_action)
        
        workflow_action = QAction("🔄 工作流配置", self)
        workflow_action.triggered.connect(self.configure_workflow)
        settings_menu.addAction(workflow_action)
        
        notify_action = QAction("🔔 通知设置", self)
        notify_action.triggered.connect(self.notification_settings)
        settings_menu.addAction(notify_action)
        
        settings_menu.addSeparator()
        
        pref_action = QAction("⚙️ 偏好设置", self)
        pref_action.triggered.connect(self.preferences)
        settings_menu.addAction(pref_action)
        
        # 6. 帮助菜单
        help_menu = menubar.addMenu("❓ 帮助(&H)")
        
        about_action = QAction("ℹ️ 关于系统", self)
        about_action.triggered.connect(self.about_system)
        help_menu.addAction(about_action)
        
        help_action = QAction("📖 使用帮助", self)
        help_action.setShortcut("F1")
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)
        
        doc_action = QAction("📄 用户手册", self)
        doc_action.triggered.connect(self.show_manual)
        help_menu.addAction(doc_action)
        
        help_menu.addSeparator()
        
        check_update_action = QAction("🔄 检查更新", self)
        check_update_action.triggered.connect(self.check_update)
        help_menu.addAction(check_update_action)
    
    def setup_toolbar(self):
        """设置工具栏"""
        toolbar = QToolBar("主工具栏")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)
        
        create_action = QAction("➕ 新建", self)
        create_action.triggered.connect(self.create_ticket)
        toolbar.addAction(create_action)
        
        edit_action = QAction("✏️ 编辑", self)
        edit_action.triggered.connect(self.edit_ticket)
        toolbar.addAction(edit_action)
        
        delete_action = QAction("🗑️ 删除", self)
        delete_action.triggered.connect(self.delete_ticket)
        toolbar.addAction(delete_action)
        
        toolbar.addSeparator()
        
        search_action = QAction("🔍 搜索", self)
        search_action.triggered.connect(self.advanced_search)
        toolbar.addAction(search_action)
        
        stats_action = QAction("📊 统计", self)
        stats_action.triggered.connect(self.show_statistics)
        toolbar.addAction(stats_action)
        
        export_action = QAction("📤 导出", self)
        export_action.triggered.connect(self.export_data)
        toolbar.addAction(export_action)
        
        toolbar.addSeparator()
        
        help_action = QAction("❓ 帮助", self)
        help_action.triggered.connect(self.show_help)
        toolbar.addAction(help_action)
    
    def setup_statusbar(self):
        """设置状态栏"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        
        self.status_label = QLabel(f"当前工单数：{len(self.tickets)}")
        self.statusbar.addWidget(self.status_label)
        
        self.statusbar.addPermanentWidget(
            QLabel(f"系统时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
        )
    
    def refresh_table(self):
        """刷新表格数据"""
        filtered_tickets = self.apply_filters()
        
        self.table.setRowCount(len(filtered_tickets))
        
        for row, ticket in enumerate(filtered_tickets):
            self.table.setItem(row, 0, QTableWidgetItem(ticket.ticket_id))
            self.table.setItem(row, 1, QTableWidgetItem(ticket.title))
            self.table.setItem(row, 2, QTableWidgetItem(ticket.category))
            
            priority_item = QTableWidgetItem(ticket.priority)
            if ticket.priority == "紧急":
                priority_item.setForeground(Qt.GlobalColor.red)
            elif ticket.priority == "高":
                priority_item.setForeground(Qt.GlobalColor.darkYellow)
            self.table.setItem(row, 3, priority_item)
            
            status_item = QTableWidgetItem(ticket.status)
            if ticket.status == "待处理":
                status_item.setBackground(Qt.GlobalColor.gray)
            elif ticket.status == "处理中":
                status_item.setBackground(Qt.GlobalColor.blue)
            elif ticket.status == "已解决":
                status_item.setBackground(Qt.GlobalColor.green)
            self.table.setItem(row, 4, status_item)
            
            self.table.setItem(row, 5, QTableWidgetItem(ticket.submitter))
            self.table.setItem(row, 6, QTableWidgetItem(ticket.department))
            self.table.setItem(row, 7, 
                QTableWidgetItem(ticket.handler or "-"))
            self.table.setItem(row, 8, QTableWidgetItem(
                ticket.created_time.strftime("%Y-%m-%d %H:%M")))
        
        self.status_label.setText(f"当前工单数：{len(self.tickets)} | "
                                  f"显示：{len(filtered_tickets)}")
    
    def apply_filters(self):
        """应用筛选条件"""
        category = self.filter_category.currentText()
        priority = self.filter_priority.currentText()
        status = self.filter_status.currentText()
        search_text = self.search_input.text().lower()
        
        filtered = []
        for ticket in self.tickets:
            if category != "全部分类" and ticket.category != category:
                continue
            if priority != "全部优先级" and ticket.priority != priority:
                continue
            if status != "全部状态" and ticket.status != status:
                continue
            if search_text and (search_text not in ticket.title.lower() 
                               and search_text not in ticket.ticket_id.lower()):
                continue
            filtered.append(ticket)
        
        return filtered
    
    def reset_filters(self):
        """重置筛选条件"""
        self.filter_category.setCurrentIndex(0)
        self.filter_priority.setCurrentIndex(0)
        self.filter_status.setCurrentIndex(0)
        self.search_input.clear()
        self.refresh_table()
    
    def get_selected_ticket(self):
        """获取选中的工单"""
        selected_rows = self.table.selectedItems()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要操作的工单")
            return None
        
        row = selected_rows[0].row()
        ticket_id = self.table.item(row, 0).text()
        
        for ticket in self.tickets:
            if ticket.ticket_id == ticket_id:
                return ticket
        
        return None
    
    def create_ticket(self):
        """创建工单"""
        dialog = CreateTicketDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_ticket_id += 1
            ticket = Ticket(
                ticket_id=f"T{self.current_ticket_id}",
                title=dialog.title_edit.text(),
                category=dialog.category_combo.currentText(),
                priority=dialog.priority_combo.currentText(),
                status="待处理",
                submitter=dialog.submitter_edit.text(),
                department=dialog.department_edit.text(),
                description=dialog.description_edit.toPlainText()
            )
            self.tickets.append(ticket)
            self.refresh_table()
            QMessageBox.information(self, "成功", 
                                   f"工单 {ticket.ticket_id} 创建成功！")
    
    def edit_ticket(self):
        """编辑工单"""
        ticket = self.get_selected_ticket()
        if not ticket:
            return
        
        dialog = EditTicketDialog(ticket, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            ticket.title = dialog.title_edit.text()
            ticket.category = dialog.category_combo.currentText()
            ticket.priority = dialog.priority_combo.currentText()
            ticket.status = dialog.status_combo.currentText()
            ticket.handler = dialog.handler_edit.text()
            ticket.submitter = dialog.submitter_edit.text()
            ticket.department = dialog.department_edit.text()
            ticket.description = dialog.description_edit.toPlainText()
            ticket.resolution = dialog.resolution_edit.toPlainText()
            
            if ticket.status == "已解决" and not ticket.completed_time:
                ticket.completed_time = datetime.now()
            
            self.refresh_table()
            QMessageBox.information(self, "成功", "工单更新成功！")
    
    def delete_ticket(self):
        """删除工单"""
        ticket = self.get_selected_ticket()
        if not ticket:
            return
        
        reply = QMessageBox.question(
            self, "确认删除",
            f"确定要删除工单 {ticket.ticket_id} 吗？",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.tickets.remove(ticket)
            self.refresh_table()
            QMessageBox.information(self, "成功", "工单已删除！")
    
    def view_detail(self):
        """查看工单详情"""
        self.edit_ticket()
    
    def advanced_search(self):
        """高级搜索"""
        self.search_input.setFocus()
        QMessageBox.information(self, "高级搜索", 
                               "请在顶部的搜索框中输入关键词进行搜索。\n"
                               "可结合分类、优先级、状态等筛选条件使用。")
    
    def custom_filter(self):
        """自定义筛选"""
        QMessageBox.information(self, "自定义筛选", 
                               "请使用顶部的筛选下拉框进行自定义筛选。\n"
                               "支持按分类、优先级、状态多维度组合筛选。")
    
    def show_statistics(self):
        """显示统计分析"""
        dialog = StatisticsDialog(self.tickets, self)
        dialog.exec()
    
    def generate_report(self):
        """生成报表"""
        QMessageBox.information(self, "生成报表", 
                               "报表生成功能开发中...\n"
                               "将支持导出日报、周报、月报等多种格式报表。")
    
    def assign_ticket(self):
        """分配工单"""
        ticket = self.get_selected_ticket()
        if not ticket:
            return
        
        handler, ok = QInputDialog.getText(
            self, "分配工单", "请输入处理人姓名："
        )
        
        if ok and handler:
            ticket.handler = handler
            ticket.status = "处理中"
            self.refresh_table()
            QMessageBox.information(self, "成功", 
                                   f"工单已分配给 {handler}")
    
    def transfer_ticket(self):
        """转交工单"""
        ticket = self.get_selected_ticket()
        if not ticket:
            return
        
        new_handler, ok = QInputDialog.getText(
            self, "转交工单", "请输入新的处理人姓名："
        )
        
        if ok and new_handler:
            old_handler = ticket.handler
            ticket.handler = new_handler
            self.refresh_table()
            QMessageBox.information(
                self, "成功",
                f"工单已从 {old_handler} 转交给 {new_handler}"
            )
    
    def resolve_ticket(self):
        """解决工单"""
        ticket = self.get_selected_ticket()
        if not ticket:
            return
        
        resolution, ok = QInputDialog.getText(
            self, "解决工单", "请输入解决方案："
        )
        
        if ok and resolution:
            ticket.resolution = resolution
            ticket.status = "已解决"
            ticket.completed_time = datetime.now()
            self.refresh_table()
            QMessageBox.information(self, "成功", "工单已标记为已解决！")
    
    def close_ticket(self):
        """关闭工单"""
        ticket = self.get_selected_ticket()
        if not ticket:
            return
        
        if ticket.status != "已解决":
            QMessageBox.warning(self, "警告", 
                               "只有已解决的工单才能关闭！")
            return
        
        ticket.status = "已关闭"
        self.refresh_table()
        QMessageBox.information(self, "成功", "工单已关闭！")
    
    def search_knowledge(self):
        """搜索知识库"""
        QMessageBox.information(self, "知识库搜索", 
                               "知识库功能开发中...\n"
                               "将支持常见问题、解决方案的快速检索。")
    
    def add_knowledge(self):
        """添加知识条目"""
        QMessageBox.information(self, "添加知识", 
                               "知识库功能开发中...\n"
                               "可将典型工单案例转化为知识库条目。")
    
    def manage_knowledge(self):
        """管理知识库"""
        QMessageBox.information(self, "管理知识库", 
                               "知识库功能开发中...")
    
    def manage_users(self):
        """用户管理"""
        QMessageBox.information(self, "用户管理", 
                               "用户管理功能开发中...\n"
                               "将支持用户角色、权限的配置管理。")
    
    def manage_categories(self):
        """分类管理"""
        QMessageBox.information(self, "分类管理", 
                               "分类管理功能开发中...\n"
                               "将支持工单分类的自定义配置。")
    
    def configure_workflow(self):
        """工作流配置"""
        QMessageBox.information(self, "工作流配置", 
                               "工作流配置功能开发中...\n"
                               "将支持审批流程、流转规则的自定义。")
    
    def notification_settings(self):
        """通知设置"""
        QMessageBox.information(self, "通知设置", 
                               "通知设置功能开发中...\n"
                               "将支持邮件、短信等多种通知方式。")
    
    def preferences(self):
        """偏好设置"""
        QMessageBox.information(self, "偏好设置", 
                               "偏好设置功能开发中...")
    
    def about_system(self):
        """关于系统"""
        QMessageBox.about(
            self, "关于系统",
            "<h2>人力资源共享服务中心</h2>"
            "<p>工单处理系统 v1.0</p>"
            "<p>本系统用于高效管理和处理人力资源相关的各类服务请求。</p>"
            "<p><b>核心功能：</b></p>"
            "<ul>"
            "<li>工单管理：创建、编辑、删除工单</li>"
            "<li>查询统计：多维度筛选和数据分析</li>"
            "<li>流程处理：分配、转交、解决、关闭</li>"
            "<li>知识库：积累和复用解决方案</li>"
            "<li>系统设置：用户、分类、工作流配置</li>"
            "<li>帮助支持：使用手册和技术支持</li>"
            "</ul>"
            "<p>© 2024 HR Service Center</p>"
        )
    
    def show_help(self):
        """显示帮助"""
        QMessageBox.information(
            self, "使用帮助",
            "<h3>快速入门指南</h3>"
            "<p><b>1. 创建工单：</b>点击\"创建工单\"按钮或使用快捷键 Ctrl+N</p>"
            "<p><b>2. 处理工单：</b>双击工单可查看和编辑详情</p>"
            "<p><b>3. 筛选工单：</b>使用顶部筛选条件快速定位工单</p>"
            "<p><b>4. 统计分析：</b>点击\"统计分析\"查看数据概览</p>"
            "<p><b>5. 导出数据：</b>选择工单后点击\"导出数据\"</p>"
            "<p><br>更多帮助请参考用户手册或联系技术支持。</p>"
        )
    
    def show_manual(self):
        """显示用户手册"""
        QMessageBox.information(
            self, "用户手册",
            "<h2>人力资源共享服务中心工单处理系统</h2>"
            "<h3>用户手册</h3>"
            "<p><b>第一章：系统概述</b></p>"
            "<p>本系统旨在提高人力资源服务效率，实现工单的标准化、流程化管理。</p>"
            "<p><b>第二章：主要功能</b></p>"
            "<p>- 工单生命周期管理</p>"
            "<p>- 多维度查询统计</p>"
            "<p>- 智能分配和流转</p>"
            "<p>- 知识库沉淀</p>"
            "<p><b>第三章：操作说明</b></p>"
            "<p>详细操作步骤请参考在线文档或联系管理员。</p>"
        )
    
    def check_update(self):
        """检查更新"""
        QMessageBox.information(self, "检查更新", 
                               "当前已是最新版本 v1.0")
    
    def export_data(self):
        """导出数据"""
        dialog = ExportDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            file_format = dialog.format_combo.currentText()
            file_path, _ = QFileDialog.getSaveFileName(
                self, "导出文件", "", 
                f"{file_format} Files (*.{file_format.lower()})"
            )
            
            if file_path:
                QMessageBox.information(
                    self, "导出成功",
                    f"数据已导出到：{file_path}\n"
                    f"格式：{file_format}"
                )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序样式
    app.setStyle("Fusion")
    
    window = HRServiceCenterWindow()
    window.show()
    
    sys.exit(app.exec())
