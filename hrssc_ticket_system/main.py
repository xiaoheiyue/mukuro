#!/usr/bin/env python3
"""
人力资源共享服务中心工单处理系统
主启动入口

六大核心功能：
1. 工单创建与生命周期管理 - TicketService
2. 用户与权限管理 - UserService  
3. 知识库管理 - KnowledgeBaseService
4. 统计分析与报表 - ReportService
5. 消息通知中心 - NotificationService
6. SLA配置与监控 - SLAService
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from views.main_window import main

if __name__ == "__main__":
    print("=" * 60)
    print("人力资源共享服务中心工单处理系统")
    print("=" * 60)
    print("\n六大核心功能模块：")
    print("1. 工单创建与生命周期管理")
    print("2. 用户与权限管理")
    print("3. 知识库管理")
    print("4. 统计分析与报表")
    print("5. 消息通知中心")
    print("6. SLA配置与监控")
    print("\n启动图形界面...")
    print("=" * 60)
    
    main()
