# Smart City Utility Platform

智慧城市水电平台 - 基于 Python + PyQt6 的桌面应用程序

## 项目概述

本系统是一个公用事业运营管理系统，核心功能包括：
- 供水与供电数据的采集、计量及账单结算
- 智能表具读数自动同步
- 账单自动生成与支付状态追踪
- 异常检测与工单管理

## 技术栈

- **编程语言**: Python 3.12
- **UI 框架**: PyQt6
- **数据库**: MySQL 8
- **ORM**: SQLAlchemy 2.0.25
- **数据验证**: Pydantic 2.5.3+
- **架构模式**: MVVM (Model-View-ViewModel)

## 项目结构

```
smart_city_utility/
├── main.py                 # 主程序入口
├── models/
│   ├── __init__.py         # SQLAlchemy ORM 模型定义
│   └── database.py         # 数据库配置
├── services/
│   ├── __init__.py         # 服务层导出
│   ├── business_services.py # 业务逻辑服务
│   └── schemas.py          # Pydantic 数据模型
├── controllers/
│   ├── __init__.py         # 控制器导出
│   └── viewmodels.py       # MVVM ViewModel 实现
├── views/
│   ├── __init__.py         # 视图导出
│   └── main_window.py      # 主窗口 UI
└── utils/
    └── init_db.py          # 数据库初始化脚本
```

## 安装步骤

### 1. 安装依赖

```bash
pip install pyqt6 sqlalchemy==2.0.25 pydantic pymysql
```

### 2. 配置数据库

编辑 `models/database.py` 文件，修改数据库连接字符串：

```python
DATABASE_URL = "mysql+pymysql://username:password@localhost:3306/smart_city_utility"
```

### 3. 创建数据库并初始化

```bash
# 在 MySQL 中创建数据库
mysql -u root -p -e "CREATE DATABASE smart_city_utility CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 运行初始化脚本
python utils/init_db.py
```

### 4. 运行应用程序

```bash
python main.py
```

## 核心功能

### 1. 仪表盘
- 系统概览统计（用户数、表具数、在线状态等）
- 待缴费账单统计
- 待处理工单统计
- 待收金额汇总

### 2. 表具管理
- 添加/查看智能水表和电表
- 表具状态监控（在线/离线/故障）
- IMEI 唯一标识管理

### 3. 账单管理
- 月度账单自动生成
- 阶梯费率计算（水价/电价）
- 违约金自动计算
- 账单状态追踪（草稿/已发布/已支付）

### 4. 支付管理
- 在线缴费功能
- 支付状态实时更新
- 支付历史记录查询

### 5. 工单管理
- 异常读数自动检测
- 设备故障工单创建
- 巡检任务派发
- 工单状态跟踪

## 数据库表结构

| 表名 | 说明 |
|------|------|
| tbl_user | 用户信息表 |
| tbl_meter | 表具信息表 |
| tbl_meter_reading | 表具读数表 |
| tbl_fee_rule | 费率规则表 |
| tbl_bill | 账单表 |
| tbl_payment | 支付记录表 |
| tbl_work_order | 工单表 |

## 业务特性

### 阶梯费率计算
- 支持多阶梯定价
- 水费/电费分别配置
- 生效日期管理

### 异常检测
- 用量突增检测（超过历史平均 50%）
- 零用量检测
- 表具离线检测

### 容错策略
- 支付超时处理（标记为"处理中"）
- 表具离线估算账单
- 费率快照锁定
- 多渠道通知（短信/APP 站内信）

## 注意事项

1. 本系统为纯桌面直连架构，UI 主线程与 DB 线程严格隔离
2. 采用信号槽机制驱动 MVVM 交互
3. 需要 MySQL 8.0+ 数据库支持
4. 首次运行前必须先执行数据库初始化

## License

MIT License
