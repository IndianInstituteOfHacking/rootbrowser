#!/usr/bin/env python3
"""
Request Repeater – Manual HTTP request tool via Tor SOCKS5
"""
import json
import time
import requests
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QFileDialog, QMessageBox, QCheckBox,
    QSplitter, QListWidget, QListWidgetItem, QTabWidget, QWidget,
    QGroupBox, QGridLayout, QInputDialog, QProgressBar
)
from PyQt5.QtGui import QFont

# Tor proxy
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}

# ========== Worker Thread ==========
class RequestWorker(QThread):
    finished = pyqtSignal(dict)   # result object
    error = pyqtSignal(str)

    def __init__(self, method, url, headers, body, follow_redirects, verify_ssl):
        super().__init__()
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self.follow_redirects = follow_redirects
        self.verify_ssl = verify_ssl

    def run(self):
        try:
            start = time.time()
            resp = requests.request(
                method=self.method,
                url=self.url,
                headers=self.headers,
                data=self.body if self.body else None,
                proxies=TOR_PROXY,
                timeout=30,
                allow_redirects=self.follow_redirects,
                verify=self.verify_ssl
            )
            elapsed = time.time() - start
            result = {
                'status_code': resp.status_code,
                'reason': resp.reason,
                'headers': dict(resp.headers),
                'body': resp.text,
                'time': elapsed,
                'size': len(resp.content)
            }
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))

# ========== Main Dialog ==========
class RequestRepeaterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔁 Request Repeater")
        self.setMinimumSize(1000, 700)
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; }
            QLabel { color: #e0e0e0; }
            QLineEdit, QTextEdit, QComboBox, QListWidget {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                padding: 4px;
                font: 12px 'Segoe UI', monospace;
            }
            QPushButton {
                background-color: #3a3a3a;
                color: #e0e0e0;
                border: 1px solid #4a4a4a;
                border-radius: 4px;
                padding: 6px 16px;
            }
            QPushButton:hover { background-color: #4a4a4a; border-color: #60a5fa; }
            QTabWidget::pane { border: 1px solid #4a4a4a; background: #1e1e1e; }
            QTabBar::tab { background: #2d2d2d; color: #a0a0a0; padding: 6px 12px; }
            QTabBar::tab:selected { background: #1e1e1e; color: white; }
            QCheckBox { color: #e0e0e0; }
            QGroupBox { color: #60a5fa; border: 1px solid #4a4a4a; margin-top: 10px; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 5px; }
            QProgressBar { border: 1px solid #4a4a4a; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #60a5fa, stop:1 #3b82f6); }
        """)

        self.history = []          # list of dicts {'method','url','headers','body'}
        self.current_request_data = None

        # Main layout: left history + right request/response
        main_layout = QHBoxLayout()

        # ---- History Panel ----
        history_group = QGroupBox("History")
        history_layout = QVBoxLayout()
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self.load_from_history)
        self.history_list.itemDoubleClicked.connect(self.load_from_history)
        history_layout.addWidget(self.history_list)
        hist_btn_layout = QHBoxLayout()
        clear_hist_btn = QPushButton("Clear")
        clear_hist_btn.clicked.connect(self.clear_history)
        hist_btn_layout.addWidget(clear_hist_btn)
        save_hist_btn = QPushButton("Save")
        save_hist_btn.clicked.connect(self.save_history)
        hist_btn_layout.addWidget(save_hist_btn)
        load_hist_btn = QPushButton("Load")
        load_hist_btn.clicked.connect(self.load_history)
        hist_btn_layout.addWidget(load_hist_btn)
        history_layout.addLayout(hist_btn_layout)
        history_group.setLayout(history_layout)

        # ---- Request/Response Panel ----
        right_panel = QVBoxLayout()

        # Request area
        req_group = QGroupBox("Request")
        req_layout = QVBoxLayout()

        # First line: method, URL, Send
        top_line = QHBoxLayout()
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"])
        top_line.addWidget(QLabel("Method:"))
        top_line.addWidget(self.method_combo)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://example.com/api/...")
        top_line.addWidget(self.url_input)
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_request)
        top_line.addWidget(self.send_btn)
        req_layout.addLayout(top_line)

        # Headers editor
        self.headers_edit = QTextEdit()
        self.headers_edit.setPlaceholderText("Header1: value1\nHeader2: value2")
        self.headers_edit.setMaximumHeight(100)
        req_layout.addWidget(QLabel("Headers (key: value, one per line):"))
        req_layout.addWidget(self.headers_edit)

        # Body editor
        self.body_edit = QTextEdit()
        self.body_edit.setPlaceholderText("Request body (for POST/PUT)...")
        self.body_edit.setMaximumHeight(120)
        req_layout.addWidget(QLabel("Body:"))
        req_layout.addWidget(self.body_edit)

        # Options
        options_layout = QHBoxLayout()
        self.follow_redirects_check = QCheckBox("Follow Redirects")
        self.follow_redirects_check.setChecked(True)
        options_layout.addWidget(self.follow_redirects_check)
        self.verify_ssl_check = QCheckBox("Verify SSL")
        self.verify_ssl_check.setChecked(False)
        options_layout.addWidget(self.verify_ssl_check)
        req_layout.addLayout(options_layout)

        req_group.setLayout(req_layout)

        # Response area
        resp_group = QGroupBox("Response")
        resp_layout = QVBoxLayout()

        # Status bar
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Status: -")
        self.time_label = QLabel("Time: -")
        self.size_label = QLabel("Size: -")
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(self.time_label)
        status_layout.addWidget(self.size_label)
        status_layout.addStretch()
        resp_layout.addLayout(status_layout)

        # Response tabs
        self.resp_tabs = QTabWidget()
        # Headers tab
        self.headers_response_edit = QTextEdit()
        self.headers_response_edit.setReadOnly(True)
        self.resp_tabs.addTab(self.headers_response_edit, "Headers")
        # Body tab
        self.body_response_edit = QTextEdit()
        self.body_response_edit.setReadOnly(True)
        self.resp_tabs.addTab(self.body_response_edit, "Body")
        resp_layout.addWidget(self.resp_tabs)

        resp_group.setLayout(resp_layout)

        right_panel.addWidget(req_group)
        right_panel.addWidget(resp_group)

        # Assemble splitter
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(history_group)
        right_widget = QWidget()
        right_widget.setLayout(right_panel)
        splitter.addWidget(right_widget)
        splitter.setSizes([250, 750])
        main_layout.addWidget(splitter)

        self.setLayout(main_layout)
        self.worker = None

    # ---- History management ----
    def add_to_history(self, method, url, headers, body):
        entry = {
            'method': method,
            'url': url,
            'headers': headers,
            'body': body
        }
        self.history.insert(0, entry)
        item = QListWidgetItem(f"{method} {url[:80]}")
        item.setData(Qt.UserRole, len(self.history)-1)  # store index
        self.history_list.insertItem(0, item)
        if len(self.history) > 50:
            self.history.pop()
            self.history_list.takeItem(50)

    def load_from_history(self, item):
        index = item.data(Qt.UserRole)
        if index is not None and index < len(self.history):
            entry = self.history[index]
            self.method_combo.setCurrentText(entry['method'])
            self.url_input.setText(entry['url'])
            self.headers_edit.setPlainText(entry['headers'])
            self.body_edit.setPlainText(entry['body'])

    def clear_history(self):
        self.history.clear()
        self.history_list.clear()

    def save_history(self):
        path, _ = QFileDialog.getSaveFileName(self, "Save History", "requests.json", "JSON (*.json)")
        if path:
            with open(path, 'w') as f:
                json.dump(self.history, f, indent=2)

    def load_history(self):
        path, _ = QFileDialog.getOpenFileName(self, "Load History", "", "JSON (*.json)")
        if path:
            try:
                with open(path, 'r') as f:
                    self.history = json.load(f)
                self.history_list.clear()
                for i, entry in enumerate(self.history):
                    item = QListWidgetItem(f"{entry['method']} {entry['url'][:80]}")
                    item.setData(Qt.UserRole, i)
                    self.history_list.addItem(item)
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not load history: {e}")

    # ---- Send request ----
    def send_request(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Enter a URL")
            return
        method = self.method_combo.currentText()
        # Parse headers
        headers_text = self.headers_edit.toPlainText().strip()
        headers = {}
        if headers_text:
            for line in headers_text.splitlines():
                if ':' in line:
                    key, val = line.split(':', 1)
                    headers[key.strip()] = val.strip()
        body = self.body_edit.toPlainText()
        follow = self.follow_redirects_check.isChecked()
        verify = self.verify_ssl_check.isChecked()

        # Add to history
        self.add_to_history(method, url, headers_text, body)

        # Disable send button, show progress
        self.send_btn.setEnabled(False)
        self.status_label.setText("Sending...")
        self.time_label.setText("")
        self.size_label.setText("")

        self.worker = RequestWorker(method, url, headers, body, follow, verify)
        self.worker.finished.connect(self.on_response)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def on_response(self, result):
        self.send_btn.setEnabled(True)
        self.status_label.setText(f"Status: {result['status_code']} {result['reason']}")
        self.time_label.setText(f"Time: {result['time']:.2f}s")
        self.size_label.setText(f"Size: {result['size']} bytes")

        # Headers tab
        h = "\n".join([f"{k}: {v}" for k,v in result['headers'].items()])
        self.headers_response_edit.setPlainText(h)

        # Body tab
        self.body_response_edit.setPlainText(result['body'])
        self.resp_tabs.setCurrentIndex(1)  # show body

    def on_error(self, err):
        self.send_btn.setEnabled(True)
        self.status_label.setText("Error")
        self.headers_response_edit.setPlainText(err)
        self.body_response_edit.clear()
