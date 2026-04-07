"""
用户管理页面 - User Page
管理系统用户和权限
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QComboBox, QTextEdit, QFormLayout,
    QDialog, QDialogButtonBox, QLineEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

import logging
import hashlib
from typing import Dict

from core.database import DatabaseManager


class UserPage(QWidget):
    """用户管理页面类"""
    
    def __init__(self, db_manager: DatabaseManager, logger: logging.Logger, parent=None):
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.logger = logger
        
        self._init_ui()
        self.refresh_data()
    
    def _init_ui(self):
        """初始化界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(15)
        
        # 标题
        title_label = QLabel("👥 用户管理")
        title_label.setObjectName("pageTitle")
        title_font = QFont("Microsoft YaHei", 18, QFont.Weight.Bold)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)
        
        # 控制栏
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        
        add_btn = QPushButton("➕ 添加用户")
        add_btn.setObjectName("primaryButton")
        add_btn.clicked.connect(self._add_user)
        control_layout.addWidget(add_btn)
        
        control_layout.addStretch()
        
        main_layout.addWidget(control_frame)
        
        # 用户列表
        list_group = QGroupBox("📋 用户列表")
        list_layout = QVBoxLayout(list_group)
        
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(7)
        self.user_table.setHorizontalHeaderLabels([
            "ID", "用户名", "姓名", "角色", "部门", "状态", "操作"
        ])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        list_layout.addWidget(self.user_table)
        
        main_layout.addWidget(list_group)
        
        self._apply_styles()
    
    def _apply_styles(self):
        """应用样式"""
        stylesheet = """
        QLabel#pageTitle {
            color: #1976D2;
            padding: 10px;
            background-color: #E3F2FD;
            border-radius: 5px;
        }
        
        QGroupBox {
            font-weight: bold;
            font-size: 14px;
            border: 1px solid #BDBDBD;
            border-radius: 5px;
            margin-top: 10px;
            padding-top: 10px;
        }
        
        QPushButton#primaryButton {
            background-color: #E91E63;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            font-weight: bold;
        }
        
        QPushButton#editButton {
            background-color: #2196F3;
            color: white;
            border: none;
            padding: 5px 10px;
            border-radius: 3px;
        }
        """
        self.setStyleSheet(stylesheet)
    
    def refresh_data(self):
        """刷新数据"""
        try:
            self._update_user_table()
        except Exception as e:
            self.logger.error(f"刷新用户数据失败：{e}")
    
    def _update_user_table(self):
        """更新用户表格"""
        users = self.db_manager.get_all_users(include_inactive=False)
        
        self.user_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.user_table.setItem(row, 0, QTableWidgetItem(str(user.get('id', ''))))
            self.user_table.setItem(row, 1, QTableWidgetItem(user.get('username', '')))
            self.user_table.setItem(row, 2, QTableWidgetItem(user.get('real_name', '')))
            self.user_table.setItem(row, 3, QTableWidgetItem(user.get('role', '')))
            self.user_table.setItem(row, 4, QTableWidgetItem(user.get('department', '')))
            
            status_item = QTableWidgetItem("✅ 活跃" if user.get('is_active') else "⚫ 禁用")
            self.user_table.setItem(row, 5, status_item)
            
            edit_btn = QPushButton("✏️ 编辑")
            edit_btn.setObjectName("editButton")
            edit_btn.clicked.connect(lambda checked, u=user: self._edit_user(u))
            self.user_table.setCellWidget(row, 6, edit_btn)
    
    def _add_user(self):
        """添加用户"""
        dialog = AddUserDialog(self.db_manager, self)
        if dialog.exec() == 1:
            self.refresh_data()
            QMessageBox.information(self, "成功", "用户已添加！")
    
    def _edit_user(self, user: Dict):
        """编辑用户"""
        dialog = EditUserDialog(user, self.db_manager, self)
        if dialog.exec() == 1:
            self.refresh_data()
            QMessageBox.information(self, "成功", "用户信息已更新！")


class AddUserDialog(QDialog):
    """添加用户对话框"""
    
    def __init__(self, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("添加用户")
        self.setMinimumWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.username_edit = QLineEdit()
        form.addRow("用户名:", self.username_edit)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        form.addRow("密码:", self.password_edit)
        
        self.name_edit = QLineEdit()
        form.addRow("真实姓名:", self.name_edit)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "operator", "viewer", "maintenance"])
        form.addRow("角色:", self.role_combo)
        
        self.dept_edit = QLineEdit()
        form.addRow("部门:", self.dept_edit)
        
        self.phone_edit = QLineEdit()
        form.addRow("电话:", self.phone_edit)
        
        self.email_edit = QLineEdit()
        form.addRow("邮箱:", self.email_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        name = self.name_edit.text().strip()
        role = self.role_combo.currentText()
        dept = self.dept_edit.text().strip()
        phone = self.phone_edit.text().strip()
        email = self.email_edit.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "错误", "用户名和密码不能为空！")
            return
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            self.db_manager.create_user(
                username=username,
                password_hash=password_hash,
                real_name=name,
                role=role,
                department=dept,
                phone=phone,
                email=email
            )
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"添加用户失败：{str(e)}")


class EditUserDialog(QDialog):
    """编辑用户对话框"""
    
    def __init__(self, user: Dict, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.user = user
        self.db_manager = db_manager
        self.setWindowTitle("编辑用户")
        self.setMinimumWidth(400)
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        self.name_edit.setText(self.user.get('real_name', ''))
        form.addRow("真实姓名:", self.name_edit)
        
        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "operator", "viewer", "maintenance"])
        self.role_combo.setCurrentText(self.user.get('role', 'operator'))
        form.addRow("角色:", self.role_combo)
        
        self.dept_edit = QLineEdit()
        self.dept_edit.setText(self.user.get('department', ''))
        form.addRow("部门:", self.dept_edit)
        
        self.phone_edit = QLineEdit()
        self.phone_edit.setText(self.user.get('phone', ''))
        form.addRow("电话:", self.phone_edit)
        
        self.email_edit = QLineEdit()
        self.email_edit.setText(self.user.get('email', ''))
        form.addRow("邮箱:", self.email_edit)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def accept(self):
        user_id = self.user.get('id')
        
        updates = {
            'real_name': self.name_edit.text().strip(),
            'role': self.role_combo.currentText(),
            'department': self.dept_edit.text().strip(),
            'phone': self.phone_edit.text().strip(),
            'email': self.email_edit.text().strip()
        }
        
        try:
            self.db_manager.update_user(user_id, **updates)
            super().accept()
        except Exception as e:
            QMessageBox.critical(self, "错误", f"更新用户失败：{str(e)}")
