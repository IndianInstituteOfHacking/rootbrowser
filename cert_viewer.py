from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem, QMessageBox
from PyQt5.QtCore import Qt

class CertificateViewer(QDialog):
    def __init__(self, cert_manager, hostname=None, parent=None):
        super().__init__(parent)
        self.cert_manager = cert_manager
        self.setWindowTitle("Certificate Viewer")
        self.setMinimumSize(700, 500)
        self.setStyleSheet("""
            QDialog { background-color: #0f0f1a; }
            QLabel { color: #e2e8f0; }
            QLineEdit { background-color: #2d2d4a; color: #f1f5f9; border: 1px solid #4b4b6e; border-radius: 8px; padding: 8px; }
            QPushButton { background-color: #3a3a5e; color: #e2e8f0; border: 1px solid #4b4b6e; border-radius: 8px; padding: 8px 16px; }
            QPushButton:hover { background-color: #4b4b6e; border-color: #6366f1; }
            QTreeWidget { background-color: #1e1e32; color: #e2e8f0; border: 1px solid #3f3f5e; border-radius: 8px; }
            QTreeWidget::item:selected { background-color: #6366f1; }
        """)
        
        layout = QVBoxLayout()
        
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Hostname:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("example.com")
        if hostname:
            self.search_input.setText(hostname)
        self.search_input.returnPressed.connect(self.search_cert)
        search_layout.addWidget(self.search_input)
        search_btn = QPushButton("Search")
        search_btn.clicked.connect(self.search_cert)
        search_layout.addWidget(search_btn)
        layout.addLayout(search_layout)
        
        self.cert_tree = QTreeWidget()
        self.cert_tree.setHeaderLabel("Certificate Information")
        layout.addWidget(self.cert_tree)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)
        
        self.setLayout(layout)
        if hostname:
            self.search_cert()
    
    def search_cert(self):
        hostname = self.search_input.text().strip()
        if not hostname:
            QMessageBox.warning(self, "Error", "Enter a hostname")
            return
        
        self.cert_tree.clear()
        cert_info = self.cert_manager.show_certificate_info(hostname)
        if not cert_info:
            cert_info = {
                'subject': f"CN={hostname}",
                'issuer': "Unknown Issuer",
                'valid_from': "Unknown",
                'valid_to': "Unknown",
                'serial': "Unknown",
                'status': "Not validated (use browser to visit site first)"
            }
        
        for key, value in cert_info.items():
            item = QTreeWidgetItem(self.cert_tree)
            item.setText(0, f"{key}: {value}")
            self.cert_tree.addTopLevelItem(item)