from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, 
                            QPushButton, QFormLayout, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor

class ConfigWindow(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration")
        self.setFixedSize(500, 400)
        
        # Apply GitHub dark theme
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(22, 27, 34))
        palette.setColor(QPalette.WindowText, QColor(201, 209, 217))
        self.setPalette(palette)
        
        layout = QVBoxLayout()
        form = QFormLayout()
        
        # API Settings
        form.addRow(QLabel("<b>API Settings</b>"))
        self.phishtank_key = QLineEdit(config.get('phishtank_api_key', ''))
        form.addRow("PhishTank API Key:", self.phishtank_key)
        
        self.virustotal_key = QLineEdit(config.get('virustotal_api_key', ''))
        form.addRow("VirusTotal API Key:", self.virustotal_key)
        
        # Network Settings
        form.addRow(QLabel("<b>Network Settings</b>"))
        self.network_monitoring = QCheckBox()
        self.network_monitoring.setChecked(config.get('network', {}).get('enable_network_monitoring', False))
        form.addRow("Enable Network Monitoring:", self.network_monitoring)
        
        # Detection Settings
        form.addRow(QLabel("<b>Detection Settings</b>"))
        self.homoglyph_threshold = QLineEdit(str(config.get('thresholds', {}).get('homoglyph', 0.3)))
        form.addRow("Homoglyph Threshold:", self.homoglyph_threshold)
        
        # Save button
        save_btn = QPushButton("Save Configuration")
        save_btn.setStyleSheet("""
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
        
        layout.addLayout(form)
        layout.addWidget(save_btn)
        self.setLayout(layout)
        
        save_btn.clicked.connect(self.accept)
