"""
登录对话框模块
Login Dialog Module
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QCheckBox, QWidget
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont


class LoginDialog(QDialog):
    """登录对话框"""
    
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.user_data = None
        
        self._init_ui()
    
    def _init_ui(self):
        """初始化 UI"""
        self.setWindowTitle("用户登录 - 工业锅炉除污处理系统")
        self.setFixedSize(400, 300)
        self.setModal(True)
        
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(40, 40, 40, 40)
        self.setLayout(layout)
        
        # 标题
        title_label = QLabel("🔐 用户登录")
        title_label.setFont(QFont("Microsoft YaHei", 18, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # 用户名
        username_label = QLabel("用户名:")
        layout.addWidget(username_label)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setStyleSheet("padding: 8px;")
        layout.addWidget(self.username_input)
        
        # 密码
        password_label = QLabel("密码:")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setStyleSheet("padding: 8px;")
        self.password_input.returnPressed.connect(self.on_login)
        layout.addWidget(self.password_input)
        
        # 记住我
        self.remember_checkbox = QCheckBox("记住用户名")
        layout.addWidget(self.remember_checkbox)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.login_button = QPushButton("登录")
        self.login_button.setObjectName("infoButton")
        self.login_button.clicked.connect(self.on_login)
        button_layout.addWidget(self.login_button)
        
        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # 提示信息
        hint_label = QLabel("默认账户：admin / admin123")
        hint_label.setStyleSheet("color: #666666; font-size: 12px;")
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hint_label)
    
    def on_login(self):
        """处理登录"""
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(self, "警告", "请输入用户名和密码！")
            return
        
        # 验证用户
        import hashlib
        password_hash = hashlib.md5(password.encode()).hexdigest()
        
        user = self.db_manager.get_user_by_username(username)
        
        if user is None:
            QMessageBox.critical(self, "错误", "用户名不存在！")
            return
        
        if user['password_hash'] != password_hash:
            # 记录失败登录
            self.db_manager.record_login(user['id'], False)
            QMessageBox.critical(self, "错误", "密码错误！")
            return
        
        if not user['is_active']:
            QMessageBox.critical(self, "错误", "账户已被禁用！")
            return
        
        # 登录成功
        self.user_data = user
        self.accept()
    
    def get_user(self):
        """获取登录用户数据"""
        return self.user_data
