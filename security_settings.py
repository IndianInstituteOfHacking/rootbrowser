from PyQt5.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QMessageBox, QGroupBox
from PyQt5.QtCore import Qt

class SecuritySettingsDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("Security Settings")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("""
            QDialog { background-color: #0f0f1a; }
            QCheckBox { color: #e2e8f0; spacing: 8px; }
            QCheckBox::indicator { width: 18px; height: 18px; }
            QGroupBox { color: #e2e8f0; border: 1px solid #3f3f5e; margin-top: 10px; padding-top: 10px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QPushButton { background-color: #3a3a5e; color: #e2e8f0; border: 1px solid #4b4b6e; border-radius: 8px; padding: 8px 16px; }
            QPushButton:hover { background-color: #4b4b6e; border-color: #6366f1; }
        """)
        
        layout = QVBoxLayout()
        
        ssl_group = QGroupBox("SSL/TLS Settings")
        ssl_layout = QVBoxLayout()
        self.ssl_verify = QCheckBox("Verify SSL Certificates")
        self.ssl_verify.setChecked(True)
        ssl_layout.addWidget(self.ssl_verify)
        ssl_group.setLayout(ssl_layout)
        layout.addWidget(ssl_group)
        
        js_group = QGroupBox("JavaScript Settings")
        js_layout = QVBoxLayout()
        self.js_enabled = QCheckBox("Enable JavaScript")
        self.js_enabled.setChecked(True)
        js_layout.addWidget(self.js_enabled)
        js_group.setLayout(js_layout)
        layout.addWidget(js_group)
        
        content_group = QGroupBox("Content Settings")
        content_layout = QVBoxLayout()
        self.images_enabled = QCheckBox("Load Images")
        self.images_enabled.setChecked(True)
        content_layout.addWidget(self.images_enabled)
        self.plugins_enabled = QCheckBox("Enable Plugins")
        self.plugins_enabled.setChecked(False)
        content_layout.addWidget(self.plugins_enabled)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self.save_settings)
        layout.addWidget(save_btn)
        
        self.setLayout(layout)
    
    def save_settings(self):
        settings = {
            'ssl_verify': self.ssl_verify.isChecked(),
            'js_enabled': self.js_enabled.isChecked(),
            'images_enabled': self.images_enabled.isChecked(),
            'plugins_enabled': self.plugins_enabled.isChecked()
        }
        # Apply settings
        if hasattr(self.browser, 'apply_settings'):
            self.browser.apply_settings(settings)
        QMessageBox.information(self, "Success", "Settings saved")
        self.accept()