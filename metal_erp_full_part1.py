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
