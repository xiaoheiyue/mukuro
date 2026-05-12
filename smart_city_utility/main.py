"""
Smart City Utility Platform - Main Entry Point
智慧城市水电平台 - 主程序入口
"""
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from views.main_window import MainWindow


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    
    # Set application info
    app.setApplicationName("智慧城市水电平台")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("Smart City Utilities")
    
    # Set Fusion style for consistent cross-platform look
    app.setStyle("Fusion")
    
    # Set application font
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)
    
    # Set global stylesheet
    app.setStyleSheet("""
        QMainWindow {
            background-color: #ffffff;
        }
        
        QTabWidget::pane {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            background-color: #ffffff;
        }
        
        QTabBar::tab {
            background-color: #f5f5f5;
            border: 1px solid #e0e0e0;
            border-bottom: none;
            border-top-left-radius: 5px;
            border-top-right-radius: 5px;
            padding: 8px 16px;
            margin-right: 2px;
        }
        
        QTabBar::tab:selected {
            background-color: #ffffff;
            border-bottom: 2px solid #3498db;
        }
        
        QTabBar::tab:hover:!selected {
            background-color: #e8e8e8;
        }
        
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 8px 16px;
            font-weight: bold;
        }
        
        QPushButton:hover {
            background-color: #2980b9;
        }
        
        QPushButton:pressed {
            background-color: #21618c;
        }
        
        QPushButton:disabled {
            background-color: #bdc3c7;
        }
        
        QTableWidget {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            gridline-color: #e0e0e0;
            background-color: #ffffff;
        }
        
        QTableWidget::item {
            padding: 8px;
        }
        
        QTableWidget::item:selected {
            background-color: #3498db;
            color: white;
        }
        
        QHeaderView::section {
            background-color: #f5f5f5;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #e0e0e0;
            font-weight: bold;
        }
        
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
            border: 1px solid #e0e0e0;
            border-radius: 5px;
            padding: 6px;
            background-color: #ffffff;
        }
        
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
            border: 2px solid #3498db;
        }
        
        QLabel {
            color: #2c3e50;
        }
        
        QFrame {
            background-color: #f8f9fa;
            border-radius: 10px;
        }
        
        QStatusBar {
            background-color: #f5f5f5;
            border-top: 1px solid #e0e0e0;
        }
        
        QMenuBar {
            background-color: #ffffff;
            border-bottom: 1px solid #e0e0e0;
        }
        
        QMenuBar::item:selected {
            background-color: #f5f5f5;
        }
        
        QMenu {
            background-color: #ffffff;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }
        
        QMenu::item:selected {
            background-color: #3498db;
            color: white;
        }
        
        QMessageBox {
            background-color: #ffffff;
        }
        
        QDialog {
            background-color: #ffffff;
        }
    """)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
