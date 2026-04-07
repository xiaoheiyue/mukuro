#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
金属制品生产全流程协同管理平台 (Metal Products Production Collaborative Management Platform)
================================================================================

版本: 1.0.0
作者: AI Assistant
描述: 
    基于 PyQt6 构建的企业级金属制品生产管理 ERP 系统。
    涵盖销售、计划、采购、库存、生产、质检、设备、财务等全流程业务。
    包含完整的模拟数据引擎、自定义 UI 组件库、业务逻辑层及数据持久化模拟层。

功能模块:
    1. 系统仪表盘 (Dashboard): 实时 KPI 监控，生产趋势图，设备状态概览。
    2. 销售管理 (Sales): 客户档案，销售订单，合同管理，发货追踪。
    3. 计划管理 (Planning): MRP 运算，主生产计划 (MPS)，工单下达。
    4. 采购管理 (Purchase): 供应商管理，采购申请，采购订单，入库检验。
    5. 库存管理 (Inventory): 多仓库管理，物料出入库，盘点，调拨，预警。
    6. 生产管理 (Production): 工单执行，报工，工序流转，在制品跟踪。
    7. 质量管理 (Quality): IQC/IPQC/OQC 检验，不合格品处理，质量追溯。
    8. 设备管理 (Equipment): 设备台账，维护保养，故障报修，OEE 分析。
    9. 基础数据 (Base Data): 物料主数据，BOM 管理，工艺路线，工作中心。
    10. 系统设置 (Settings): 用户权限，角色管理，日志审计，系统配置。

技术栈:
    - Python 3.8+
    - PyQt6 (GUI Framework)
    - PyQtGraph (Data Visualization)
    - Standard Library (json, datetime, random, logging, etc.)

注意:
    本系统为演示用全功能模拟系统，数据存储在内存中，重启后重置。
    代码量设计目标：> 3000 行，包含详尽注释和类型提示。
================================================================================
"""

import sys
import os
import json
import random
import logging
import datetime
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
from collections import defaultdict
from functools import wraps
import traceback

# 尝试导入 PyQt6 相关模块
try:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
        QGridLayout, QScrollArea, QFrame, QLabel, QPushButton, QLineEdit, 
        QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, 
        QTimeEdit, QDateTimeEdit, QTableWidget, QTableWidgetItem, 
        QHeaderView, QAbstractItemView, QMenu, QAction, QMenuBar, 
        QStatusBar, QToolBar, QDialog, QDialogButtonBox, QMessageBox, 
        QFileDialog, QProgressBar, QStackedWidget, QSplitter, 
        QTreeWidget, QTreeWidgetItem, QTabWidget, QFormLayout, 
        QGroupBox, QRadioButton, QCheckBox, QListWidget, QListWidgetItem,
        QSizePolicy, QSpacerItem, QCompleter, QSystemTrayIcon, QToolTip,
        QStyleFactory, QStyleOptionViewItem, QStyledItemDelegate
    )
    from PyQt6.QtCore import (
        Qt, QThread, pyqtSignal, QObject, QTimer, QDate, QTime, 
        QDateTime, QUrl, QFileInfo, QSize, QPoint, QRect, QModelIndex,
        QSortFilterProxyModel, QAbstractTableModel, QVariant, QRunnable, 
        QThreadPool, QMetaObject, Q_ARG, QPropertyAnimation, QEasingCurve,
        QParallelAnimationGroup, QSequentialAnimationGroup
    )
    from PyQt6.QtGui import (
        QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QFont, 
        QFontMetrics, QPalette, QLinearGradient, QRadialGradient,
        QConicalGradient, QKeySequence, QActionGroup, QCursor, 
        QMovie, QBitmap, QRegion, QValidator, QIntValidator, 
        QDoubleValidator, QRegExpValidator, QTextDocument, QTextCursor,
        QTextFormat, QSyntaxHighlighter, QRegularExpression, 
        QRegularExpressionValidator, QImage, QClipboard
    )
    
    # 尝试导入 pyqtgraph 用于图表，如果不存在则使用 fallback
    try:
        import pyqtgraph as pg
        HAS_PYQTGRAPH = True
    except ImportError:
        HAS_PYQTGRAPH = False
        print("警告: 未检测到 pyqtgraph，图表将使用简化模式显示。请安装: pip install pyqtgraph")

except ImportError as e:
    print(f"严重错误: 无法导入 PyQt6 模块。请确保已安装: pip install PyQt6 pyqtgraph")
    print(f"详细错误: {e}")
    sys.exit(1)

# ==============================================================================
# 第一部分：日志配置与全局常量定义
# ==============================================================================

# 配置日志系统
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MetalERP")

# 全局常量
APP_NAME = "金属制品生产全流程协同管理平台"
APP_VERSION = "1.0.0"
COMPANY_NAME = "未来金属科技有限公司"
DB_VERSION = "1.0"

# 颜色定义 (工业风配色)
COLORS = {
    "primary": "#2196F3",       # 蓝色
    "secondary": "#FF9800",     # 橙色
    "success": "#4CAF50",       # 绿色
    "danger": "#F44336",        # 红色
    "warning": "#FFEB3B",       # 黄色
    "info": "#00BCD4",          # 青色
    "dark_bg": "#1E1E1E",       # 深色背景
    "light_bg": "#F5F5F5",      # 浅色背景
    "panel_bg": "#2D2D2D",      # 面板背景
    "text_main": "#FFFFFF",     # 主文本
    "text_sub": "#B0B0B0",      # 副文本
    "border": "#404040",        # 边框
    "hover": "#3D3D3D",         # 悬停
    "selected": "#326CE5"       # 选中
}

# 状态枚举定义
class OrderStatus(Enum):
    DRAFT = "草稿"
    PENDING = "待审核"
    APPROVED = "已审核"
    PRODUCING = "生产中"
    PARTIAL_SHIPPED = "部分发货"
    COMPLETED = "已完成"
    CANCELLED = "已取消"

class InventoryStatus(Enum):
    NORMAL = "正常"
    LOW_STOCK = "低库存"
    OUT_OF_STOCK = "缺货"
    RESERVED = "已预留"
    DAMAGED = "损坏"

class EquipmentStatus(Enum):
    RUNNING = "运行中"
    IDLE = "空闲"
    MAINTENANCE = "维护中"
    BROKEN = "故障"
    OFFLINE = "离线"

class QualityResult(Enum):
    PENDING = "待检"
    PASSED = "合格"
    REJECTED = "不合格"
    CONDITIONAL_PASS = "让步接收"
    Rework = "返工"

class PriorityLevel(Enum):
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    URGENT = "紧急"

# ==============================================================================
# 第二部分：数据模型层 (Data Models)
# 使用 dataclasses 定义所有业务实体，确保类型安全和结构清晰
# ==============================================================================

@dataclass
class User:
    id: str
    username: str
    password_hash: str
    real_name: str
    email: str
    phone: str
    department: str
    role: str
    is_active: bool
    last_login: Optional[datetime.datetime] = None
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class Customer:
    id: str
    code: str
    name: str
    contact_person: str
    phone: str
    email: str
    address: str
    tax_id: str
    bank_account: str
    credit_limit: float
    status: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class Supplier:
    id: str
    code: str
    name: str
    contact_person: str
    phone: str
    email: str
    address: str
    tax_id: str
    bank_account: str
    rating: int
    status: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class Material:
    id: str
    code: str
    name: str
    spec: str
    unit: str
    category: str
    safety_stock: float
    max_stock: float
    price: float
    supplier_ids: List[str] = field(default_factory=list)
    description: str = ""
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class BOMItem:
    id: str
    parent_material_id: str
    child_material_id: str
    quantity: float
    unit: str
    loss_rate: float
    sequence: int

@dataclass
class WorkCenter:
    id: str
    code: str
    name: str
    type: str
    capacity: float
    efficiency: float
    shift_pattern: str
    cost_per_hour: float

@dataclass
class ProcessRoute:
    id: str
    material_id: str
    version: str
    items: List[Dict[str, Any]] = field(default_factory=list) # {work_center_id, operation_name, std_time}

@dataclass
class SalesOrder:
    id: str
    order_no: str
    customer_id: str
    order_date: datetime.date
    delivery_date: datetime.date
    status: OrderStatus
    priority: PriorityLevel
    items: List[Dict[str, Any]] = field(default_factory=list) # {material_id, quantity, price, amount}
    total_amount: float
    remark: str
    creator_id: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class PurchaseOrder:
    id: str
    order_no: str
    supplier_id: str
    order_date: datetime.date
    expected_date: datetime.date
    status: OrderStatus
    items: List[Dict[str, Any]] = field(default_factory=list)
    total_amount: float
    remark: str
    creator_id: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class InventoryRecord:
    id: str
    material_id: str
    warehouse_id: str
    quantity: float
    locked_quantity: float
    batch_no: str
    production_date: datetime.date
    expiry_date: Optional[datetime.date]
    location: str
    status: InventoryStatus

@dataclass
class Warehouse:
    id: str
    code: str
    name: str
    type: str
    manager: str
    address: str

@dataclass
class WorkOrder:
    id: str
    wo_no: str
    sales_order_id: str
    material_id: str
    plan_qty: float
    completed_qty: float
    scrap_qty: float
    status: str
    priority: PriorityLevel
    start_date: datetime.date
    end_date: datetime.date
    work_center_id: str
    process_route_id: str
    current_process: int
    creator_id: str
    created_at: datetime.datetime = field(default_factory=datetime.datetime.now)

@dataclass
class QualityCheck:
    id: str
    check_no: str
    source_type: str # PO, WO
    source_id: str
    material_id: str
    check_date: datetime.datetime
    inspector_id: str
    sample_size: int
    defect_count: int
    result: QualityResult
    remark: str

@dataclass
class Equipment:
    id: str
    code: str
    name: str
    model: str
    work_center_id: str
    status: EquipmentStatus
    purchase_date: datetime.date
    last_maintenance: datetime.date
    next_maintenance: datetime.date
    oee: float
    running_hours: float

@dataclass
class MaintenanceRecord:
    id: str
    equipment_id: str
    type: str # 预防性，纠正性
    start_time: datetime.datetime
    end_time: Optional[datetime.datetime]
    description: str
    technician_id: str
    cost: float
    status: str

# ==============================================================================
# 第三部分：模拟数据库服务层 (Mock Database Service)
# 生成大量逼真的测试数据，支撑大规模界面展示
# ==============================================================================

class MockDatabase:
    """
    模拟数据库服务类
    负责生成和管理所有业务数据，提供 CRUD 接口模拟
    """
    
    def __init__(self):
        self.users: List[User] = []
        self.customers: List[Customer] = []
        self.suppliers: List[Supplier] = []
        self.materials: List[Material] = []
        self.bom_items: List[BOMItem] = []
        self.work_centers: List[WorkCenter] = []
        self.process_routes: List[ProcessRoute] = []
        self.sales_orders: List[SalesOrder] = []
        self.purchase_orders: List[PurchaseOrder] = []
        self.inventory_records: List[InventoryRecord] = []
        self.warehouses: List[Warehouse] = []
        self.work_orders: List[WorkOrder] = []
        self.quality_checks: List[QualityCheck] = []
        self.equipments: List[Equipment] = []
        self.maintenance_records: List[MaintenanceRecord] = []
        
        self._initialize_data()

    def _generate_id(self, prefix: str) -> str:
        """生成唯一 ID"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        rand_suffix = random.randint(1000, 9999)
        return f"{prefix}{timestamp}{rand_suffix}"

    def _initialize_data(self):
        """初始化所有模拟数据"""
        logger.info("正在初始化模拟数据库...")
        self._init_users()
        self._init_warehouses()
        self._init_work_centers()
        self._init_suppliers()
        self._init_customers()
        self._init_materials()
        self._init_bom()
        self._init_equipment()
        self._init_sales_orders(50)
        self._init_purchase_orders(30)
        self._init_inventory()
        self._init_work_orders(40)
        self._init_quality_checks()
        self._init_maintenance()
        logger.info(f"模拟数据初始化完成。生成订单:{len(self.sales_orders)}, 物料:{len(self.materials)}, 工单:{len(self.work_orders)}")

    def _init_users(self):
        roles = ["admin", "manager", "sales", "planner", "purchaser", "warehouse", "operator", "qc"]
        depts = ["总经办", "销售部", "计划部", "采购部", "仓储部", "生产部", "质检部", "设备部"]
        for i in range(20):
            role = roles[i % len(roles)]
            self.users.append(User(
                id=self._generate_id("USR"),
                username=f"user{i:03d}",
                password_hash="hashed_password",
                real_name=f"员工{i}",
                email=f"user{i}@metalcorp.com",
                phone=f"1380000{i:04d}",
                department=depts[i % len(depts)],
                role=role,
                is_active=True
            ))

    def _init_warehouses(self):
        wh_types = ["原材料仓", "半成品仓", "成品仓", "辅料仓", "废品仓"]
        for i, wtype in enumerate(wh_types):
            self.warehouses.append(Warehouse(
                id=self._generate_id("WH"),
                code=f"WH{i:02d}",
                name=f"{wtype}0{i}",
                type=wtype,
                manager=f"管理员{i}",
                address=f"厂区{chr(65+i)}区"
            ))

    def _init_work_centers(self):
        wc_types = ["切割", "冲压", "焊接", "表面处理", "组装", "包装"]
        for i, wtype in enumerate(wc_types):
            self.work_centers.append(WorkCenter(
                id=self._generate_id("WC"),
                code=f"WC{i:02d}",
                name=f"{wtype}中心",
                type=wtype,
                capacity=100.0 + i * 10,
                efficiency=0.85 + random.random() * 0.1,
                shift_pattern="8h",
                cost_per_hour=50.0 + i * 5
            ))

    def _init_suppliers(self):
        categories = ["钢材供应商", "铝材供应商", "配件供应商", "涂料供应商", "包装材料"]
        for i in range(15):
            cat = categories[i % len(categories)]
            self.suppliers.append(Supplier(
                id=self._generate_id("SUP"),
                code=f"SUP{i:03d}",
                name=f"{cat}{i}号公司",
                contact_person=f"联系人{i}",
                phone=f"021-8888{i:04d}",
                email=f"contact{i}@supplier.com",
                address=f"工业园{i}路{i}号",
                tax_id=f"TAX{i:010d}",
                bank_account=f"ACC{i:015d}",
                rating=random.randint(3, 5),
                status="active"
            ))

    def _init_customers(self):
        industries = ["汽车制造", "航空航天", "建筑工程", "家电制造", "医疗器械"]
        for i in range(20):
            ind = industries[i % len(industries)]
            self.customers.append(Customer(
                id=self._generate_id("CUS"),
                code=f"CUS{i:03d}",
                name=f"{ind}客户{i}有限公司",
                contact_person=f"王经理{i}",
                phone=f"1390000{i:04d}",
                email=f"buyer{i}@customer.com",
                address=f"科技园{i}街{i}号",
                tax_id=f"TAX{i:010d}",
                bank_account=f"ACC{i:015d}",
                credit_limit=100000.0 * (i + 1),
                status="active"
            ))

    def _init_materials(self):
        categories = ["板材", "管材", "型材", "标准件", "半成品", "成品"]
        units = ["kg", "m", "pcs", "set"]
        for i in range(100):
            cat = categories[i % len(categories)]
            unit = units[i % len(units)]
            code = f"M{i:04d}"
            self.materials.append(Material(
                id=self._generate_id("MAT"),
                code=code,
                name=f"{cat}-型号{code}",
                spec=f"规格{i}-{random.randint(10, 100)}mm",
                unit=unit,
                category=cat,
                safety_stock=50.0 + random.random() * 100,
                max_stock=1000.0 + random.random() * 2000,
                price=10.0 + random.random() * 100,
                supplier_ids=[self.suppliers[j].id for j in random.sample(range(len(self.suppliers)), k=min(3, len(self.suppliers)))],
                description=f"这是{cat}的详细描述信息，包含材质、用途等。"
            ))

    def _init_bom(self):
        # 简单模拟：成品由几个半成品和材料组成
        finished_goods = [m for m in self.materials if m.category == "成品"]
        components = [m for m in self.materials if m.category in ["半成品", "标准件"]]
        raw_materials = [m for m in self.materials if m.category in ["板材", "管材", "型材"]]
        
        for fg in finished_goods[:10]:
            parts = random.sample(components + raw_materials, k=min(5, len(components) + len(raw_materials)))
            for seq, part in enumerate(parts):
                self.bom_items.append(BOMItem(
                    id=self._generate_id("BOM"),
                    parent_material_id=fg.id,
                    child_material_id=part.id,
                    quantity=random.uniform(0.5, 5.0),
                    unit=part.unit,
                    loss_rate=random.uniform(0.01, 0.05),
                    sequence=seq
                ))

    def _init_equipment(self):
        for wc in self.work_centers:
            for i in range(3):
                status_list = [EquipmentStatus.RUNNING, EquipmentStatus.IDLE, EquipmentStatus.MAINTENANCE, EquipmentStatus.BROKEN]
                status = random.choice(status_list)
                eq = Equipment(
                    id=self._generate_id("EQP"),
                    code=f"{wc.code}-EQ{i}",
                    name=f"{wc.name}设备-{i}",
                    model=f"MDL-{random.randint(1000, 9999)}",
                    work_center_id=wc.id,
                    status=status,
                    purchase_date=datetime.date.today() - datetime.timedelta(days=random.randint(100, 1000)),
                    last_maintenance=datetime.date.today() - datetime.timedelta(days=random.randint(10, 60)),
                    next_maintenance=datetime.date.today() + datetime.timedelta(days=random.randint(10, 30)),
                    oee=random.uniform(0.6, 0.95),
                    running_hours=random.uniform(100, 5000)
                )
                self.equipments.append(eq)

    def _init_sales_orders(self, count: int):
        for i in range(count):
            cust = random.choice(self.customers)
            mats = random.sample(self.materials, k=min(5, len(self.materials)))
            items = []
            total = 0.0
            for m in mats:
                qty = random.uniform(10, 500)
                amt = qty * m.price
                items.append({
                    "material_id": m.id,
                    "material_code": m.code,
                    "material_name": m.name,
                    "quantity": qty,
                    "price": m.price,
                    "amount": amt
                })
                total += amt
            
            status_list = list(OrderStatus)
            self.sales_orders.append(SalesOrder(
                id=self._generate_id("SO"),
                order_no=f"SO{datetime.date.today().strftime('%Y%m%d')}-{i:04d}",
                customer_id=cust.id,
                customer_name=cust.name,
                order_date=datetime.date.today() - datetime.timedelta(days=random.randint(0, 30)),
                delivery_date=datetime.date.today() + datetime.timedelta(days=random.randint(10, 60)),
                status=random.choice(status_list),
                priority=random.choice(list(PriorityLevel)),
                items=items,
                total_amount=total,
                remark=f"订单备注信息 {i}",
                creator_id=random.choice(self.users).id
            ))

    def _init_purchase_orders(self, count: int):
        for i in range(count):
            sup = random.choice(self.suppliers)
            mats = random.sample(self.materials, k=min(5, len(self.materials)))
            items = []
            total = 0.0
            for m in mats:
                qty = random.uniform(100, 1000)
                amt = qty * m.price * 0.8 # 采购价略低
                items.append({
                    "material_id": m.id,
                    "material_code": m.code,
                    "material_name": m.name,
                    "quantity": qty,
                    "price": m.price * 0.8,
                    "amount": amt
                })
                total += amt
            
            self.purchase_orders.append(PurchaseOrder(
                id=self._generate_id("PO"),
                order_no=f"PO{datetime.date.today().strftime('%Y%m%d')}-{i:04d}",
                supplier_id=sup.id,
                supplier_name=sup.name,
                order_date=datetime.date.today() - datetime.timedelta(days=random.randint(0, 30)),
                expected_date=datetime.date.today() + datetime.timedelta(days=random.randint(10, 45)),
                status=random.choice(list(OrderStatus)),
                items=items,
                total_amount=total,
                remark=f"采购备注 {i}",
                creator_id=random.choice(self.users).id
            ))

    def _init_inventory(self):
        for mat in self.materials:
            for wh in self.warehouses[:3]: # 主要放在前三个仓库
                qty = random.uniform(mat.safety_stock * 0.5, mat.max_stock * 1.2)
                locked = random.uniform(0, qty * 0.2)
                
                if qty < mat.safety_stock:
                    status = InventoryStatus.LOW_STOCK
                elif qty <= 0:
                    status = InventoryStatus.OUT_OF_STOCK
                else:
                    status = InventoryStatus.NORMAL
                
                self.inventory_records.append(InventoryRecord(
                    id=self._generate_id("INV"),
                    material_id=mat.id,
                    material_code=mat.code,
                    material_name=mat.name,
                    warehouse_id=wh.id,
                    warehouse_name=wh.name,
                    quantity=qty,
                    locked_quantity=locked,
                    batch_no=f"BATCH{random.randint(10000, 99999)}",
                    production_date=datetime.date.today() - datetime.timedelta(days=random.randint(0, 100)),
                    expiry_date=None,
                    location=f"{wh.code}-A{random.randint(1,10)}-{random.randint(1,20)}",
                    status=status
                ))

    def _init_work_orders(self, count: int):
        sos = [so for so in self.sales_orders if so.status in [OrderStatus.APPROVED, OrderStatus.PRODUCING]]
        if not sos:
            sos = self.sales_orders[:10]
            
        for i in range(count):
            so = random.choice(sos)
            item = random.choice(so.items)
            mat_id = item['material_id']
            wc = random.choice(self.work_centers)
            
            plan_qty = item['quantity']
            completed = random.uniform(0, plan_qty)
            scrap = random.uniform(0, plan_qty * 0.05)
            
            self.work_orders.append(WorkOrder(
                id=self._generate_id("WO"),
                wo_no=f"WO{datetime.date.today().strftime('%Y%m%d')}-{i:04d}",
                sales_order_id=so.id,
                sales_order_no=so.order_no,
                material_id=mat_id,
                material_name=item['material_name'],
                plan_qty=plan_qty,
                completed_qty=completed,
                scrap_qty=scrap,
                status="PRODUCING" if completed < plan_qty else "COMPLETED",
                priority=so.priority,
                start_date=datetime.date.today() - datetime.timedelta(days=random.randint(0, 10)),
                end_date=datetime.date.today() + datetime.timedelta(days=random.randint(1, 20)),
                work_center_id=wc.id,
                work_center_name=wc.name,
                process_route_id="",
                current_process=random.randint(1, 5),
                creator_id=random.choice(self.users).id
            ))

    def _init_quality_checks(self):
        for wo in self.work_orders[:20]:
            result = random.choice(list(QualityResult))
            sample = int(wo.plan_qty * 0.1)
            defect = int(sample * random.uniform(0, 0.1)) if result != QualityResult.PASSED else 0
            
            self.quality_checks.append(QualityCheck(
                id=self._generate_id("QC"),
                check_no=f"QC{datetime.date.today().strftime('%Y%m%d')}-{len(self.quality_checks):04d}",
                source_type="WO",
                source_id=wo.id,
                material_id=wo.material_id,
                check_date=datetime.datetime.now() - datetime.timedelta(hours=random.randint(1, 100)),
                inspector_id=random.choice(self.users).id,
                sample_size=sample,
                defect_count=defect,
                result=result,
                remark="检验记录备注"
            ))

    def _init_maintenance(self):
        for eq in self.equipments[:10]:
            self.maintenance_records.append(MaintenanceRecord(
                id=self._generate_id("MNT"),
                equipment_id=eq.id,
                type=random.choice(["预防性", "纠正性"]),
                start_time=datetime.datetime.now() - datetime.timedelta(days=random.randint(1, 30)),
                end_time=datetime.datetime.now() - datetime.timedelta(days=random.randint(0, 29)),
                description="定期保养或故障维修记录",
                technician_id=random.choice(self.users).id,
                cost=random.uniform(100, 5000),
                status="COMPLETED"
            ))

    # 通用查询方法
    def get_all(self, entity_type: str) -> List[Any]:
        return getattr(self, entity_type, [])

    def get_by_id(self, entity_type: str, id: str) -> Optional[Any]:
        items = self.get_all(entity_type)
        for item in items:
            if hasattr(item, 'id') and item.id == id:
                return item
        return None

    def add(self, entity_type: str, item: Any):
        getattr(self, entity_type).append(item)
        logger.debug(f"Added {entity_type}: {item.id}")

    def update(self, entity_type: str, id: str, **kwargs):
        item = self.get_by_id(entity_type, id)
        if item:
            for key, value in kwargs.items():
                if hasattr(item, key):
                    setattr(item, key, value)
            logger.debug(f"Updated {entity_type}: {id}")
            return True
        return False

    def delete(self, entity_type: str, id: str):
        items = getattr(self, entity_type)
        original_len = len(items)
        setattr(self, entity_type, [x for x in items if getattr(x, 'id', None) != id])
        if len(getattr(self, entity_type)) < original_len:
            logger.debug(f"Deleted {entity_type}: {id}")
            return True
        return False

# 全局数据库实例
db = MockDatabase()
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
