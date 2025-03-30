from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QWidget, QListWidget, 
                            QLabel, QPushButton, QHBoxLayout, QCheckBox)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPalette

class MainWindow(QMainWindow):
    alert_received = pyqtSignal(str)  # formatted message
    config_requested = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phishing Annihilator")
        self.setGeometry(100, 100, 800, 600)
        
        # GitHub-inspired dark theme
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(22, 27, 34))
        palette.setColor(QPalette.WindowText, QColor(201, 209, 217))
        palette.setColor(QPalette.Base, QColor(13, 17, 23))
        palette.setColor(QPalette.AlternateBase, QColor(22, 27, 34))
        palette.setColor(QPalette.Button, QColor(33, 38, 45))
        palette.setColor(QPalette.ButtonText, QColor(201, 209, 217))
        palette.setColor(QPalette.Highlight, QColor(88, 166, 255))
        self.setPalette(palette)
        
        # Main layout
        main_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Phishing Annihilator")
        header.setStyleSheet("""
            font-size: 18px; 
            font-weight: bold;
            color: #58a6ff;
            padding-bottom: 10px;
            border-bottom: 1px solid #30363d;
            margin-bottom: 15px;
        """)
        layout.addWidget(header)
        
        # Status bar
        self.status_label = QLabel()
        self.status_label.setStyleSheet("""
            font-size: 14px;
            color: #c9d1d9;
        """)
        self.set_status_active(True)  # Default to active
        layout.addWidget(self.status_label)
        
        # Alert list
        self.alert_list = QListWidget()
        self.alert_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 8px;
                background-color: #0d1117;
                color: #c9d1d9;
            }
            QListWidget::item {
                color: #c9d1d9;
                border-bottom: 1px solid #30363d;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #30363d;
            }
        """)
        layout.addWidget(self.alert_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        auto_start_layout = QHBoxLayout()
        self.auto_start = QCheckBox("Auto Start on Boot")
        self.auto_start.setStyleSheet("color: #c9d1d9;")
        admin_icon = QLabel("🛡️")
        admin_icon.setToolTip("Requires administrator permissions")
        auto_start_layout.addWidget(self.auto_start)
        auto_start_layout.addWidget(admin_icon)
        auto_start_layout.addStretch()
        button_layout.addLayout(auto_start_layout)
        
        self.config_btn = QPushButton("⚙️ Configuration")
        self.config_btn.setStyleSheet("""
            QPushButton {
                background-color: #238636;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #2ea043;
            }
        """)
        self.config_btn.clicked.connect(self.config_requested.emit)
        
        self.hide_btn = QPushButton("↓ Hide to Tray")
        self.hide_console = QPushButton("🖥️ Hide Console")
        self.hide_console.setStyleSheet("""
            QPushButton {
                background-color: #30363d;
                color: #c9d1d9;
                border: 1px solid #8b949e;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3b424b;
            }
        """)
        self.hide_btn.setStyleSheet("""
            QPushButton {
                background-color: #30363d;
                color: #c9d1d9;
                border: 1px solid #8b949e;
                padding: 8px 16px;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #3b424b;
            }
        """)
        
        button_layout.addStretch()
        button_layout.addWidget(self.config_btn)
        button_layout.addWidget(self.hide_btn)
        layout.addLayout(button_layout)
        
        # Connect signals
        self.alert_received.connect(self.add_alert)
        self.hide_btn.clicked.connect(self.hide)
        
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
    
    def set_status_active(self, active):
        """Update status with colored active/inactive text"""
        color = "#3fb950" if active else "#f85149"
        text = "active" if active else "inactive"
        self.status_label.setText(f"Status: Monitoring <span style='color:{color}'>{text}</span>")
        self.status_label.setTextFormat(Qt.RichText)

    def add_alert(self, message):
        """Add new alert to the list with timestamp"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.alert_list.insertItem(0, f"[{timestamp}] {message}")
        self.alert_list.item(0).setForeground(QColor(255, 100, 100))  # Red text
        if self.alert_list.count() > 50:  # Limit to 50 most recent
            self.alert_list.takeItem(50)
        
        # Flash window in taskbar
        self.setWindowState(self.windowState() & ~Qt.WindowMinimized | Qt.WindowActive)
        self.activateWindow()
