#!/usr/bin/env python3
"""
DOM Manipulator – Edit page HTML live and apply changes
"""
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QTextEdit,
    QLabel, QMessageBox, QDialogButtonBox
)
from PyQt5.QtGui import QFont

class DomManipulatorDialog(QDialog):
    def __init__(self, page, parent=None):
        super().__init__(parent)
        self.page = page
        self.setWindowTitle("🧩 DOM Manipulator")
        self.setMinimumSize(900, 650)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; }
            QLabel { color: #e0e0e0; font-family: 'Segoe UI'; }
            QTextEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                font-family: 'Courier New', monospace;
                font-size: 12px;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 6px 16px;
                font-family: 'Segoe UI';
            }
            QPushButton:hover { background-color: #4a4a4a; border-color: #60a5fa; }
        """)

        layout = QVBoxLayout()

        # Info label
        layout.addWidget(QLabel("Edit the HTML below and click 'Apply Changes' to update the page."))

        # Editor
        self.editor = QTextEdit()
        self.editor.setAcceptRichText(False)
        layout.addWidget(self.editor)

        # Buttons
        btn_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.clicked.connect(self.apply_changes)
        btn_layout.addWidget(self.apply_btn)

        self.reload_btn = QPushButton("Reload Original")
        self.reload_btn.clicked.connect(self.load_html)
        btn_layout.addWidget(self.reload_btn)

        btn_layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # Load current HTML
        self.load_html()

    def load_html(self):
        """Fetch the current page's HTML and display it."""
        self.page.toHtml(self.on_html_loaded)

    def on_html_loaded(self, html):
        self.editor.setPlainText(html)

    def apply_changes(self):
        """Inject the edited HTML into the page."""
        new_html = self.editor.toPlainText()
        # Use document.open/write/close to fully replace the page
        js = f"""
        (function() {{
            document.open();
            document.write(`{new_html.replace('`', '\\`')}`);
            document.close();
        }})();
        """
        self.page.runJavaScript(js, self.on_applied)

    def on_applied(self, result):
        QMessageBox.information(self, "Success", "DOM changes applied.")
