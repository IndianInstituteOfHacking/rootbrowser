#!/usr/bin/env python3
"""
🌐 Dark Web Search Aggregator – Multi‑engine .onion search via Tor
Dependencies: pip install requests beautifulsoup4 (already on Kali via apt)
"""
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QGroupBox, QProgressBar
)

# Tor proxy (same as your browser)
TOR_PROXY = {
    'http': 'socks5h://127.0.0.1:9050',
    'https': 'socks5h://127.0.0.1:9050'
}
TIMEOUT = 20

# ========== SEARCH ENGINE DEFINITIONS ==========
SEARCH_ENGINES = {
    "Ahmia (onion)": {
        "url": "http://juhanurmihxlp77nkq76byazcldy2hlmovfu2epvl5ankdibsot4csyd.onion/search/?q={query}",
        "parser": "ahmia"
    },
    "Ahmia (clearnet)": {
        "url": "https://ahmia.fi/search/?q={query}",
        "parser": "ahmia"
    },
    "Torch (onion)": {
        "url": "http://xmh57jrzrnw6insl.onion/search?query={query}",
        "parser": "torch"
    },
    "Not Evil (onion)": {
        "url": "http://hss3uro2hsxfogfq.onion/index.php?q={query}",
        "parser": "not_evil"
    },
    "Haystak (onion)": {
        "url": "http://haystak5njsmn2hqkewecpaxetahtwhsbsa64jom2k22z5afxhnpxfid.onion/?q={query}",
        "parser": "haystak"
    },
    "OnionLand (onion)": {
        "url": "http://3bbad7fauom4d6sg.onion/search?q={query}",
        "parser": "onionland"
    }
}

# ========== HTML PARSERS (each returns list of dicts) ==========
def parse_ahmia(html, query):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for res in soup.select('li.result'):
        title_el = res.select_one('h4 a')
        if not title_el:
            continue
        title = title_el.get_text(strip=True)
        url = title_el.get('href', '')
        snippet_el = res.select_one('p')
        snippet = snippet_el.get_text(strip=True) if snippet_el else ''
        results.append({'title': title, 'url': url, 'snippet': snippet})
    return results

def parse_torch(html, query):
    # Torch returns simple HTML, extract title/url from <a> tags
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.select('a[href]'):
        url = a['href']
        if url.startswith('http') and 'torch' not in url:
            title = a.get_text(strip=True)
            results.append({'title': title, 'url': url, 'snippet': ''})
    return results

def parse_not_evil(html, query):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for row in soup.select('table tr'):
        cols = row.find_all('td')
        if len(cols) >= 2:
            title_el = cols[1].find('a')
            if title_el:
                title = title_el.get_text(strip=True)
                url = title_el.get('href', '')
                results.append({'title': title, 'url': url, 'snippet': ''})
    return results

def parse_haystak(html, query):
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for div in soup.select('.result'):
        a = div.select_one('a.title')
        if a:
            title = a.get_text(strip=True)
            url = a.get('href', '')
            snippet_el = div.select_one('.snippet')
            snippet = snippet_el.get_text(strip=True) if snippet_el else ''
            results.append({'title': title, 'url': url, 'snippet': snippet})
    return results

def parse_onionland(html, query):
    # OnionLand uses simple listing
    results = []
    soup = BeautifulSoup(html, 'html.parser')
    for a in soup.select('a[href]'):
        url = a['href']
        if url.startswith('http') and 'onion' in url:
            title = a.get_text(strip=True)
            results.append({'title': title, 'url': url, 'snippet': ''})
    return results

# ========== WORKER THREAD ==========
class SearchWorker(QThread):
    result_found = pyqtSignal(str, str, str, str)  # engine, title, url, snippet
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, query, engines):
        super().__init__()
        self.query = query
        self.engines = engines  # list of engine names
        self._is_running = True

    def run(self):
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for engine_name in self.engines:
                engine = SEARCH_ENGINES[engine_name]
                url = engine['url'].format(query=urllib.parse.quote(self.query))
                futures[executor.submit(self.fetch_and_parse, engine_name, engine, url)] = engine_name

            for future in as_completed(futures):
                if not self._is_running:
                    break
                try:
                    results = future.result()
                    for r in results:
                        self.result_found.emit(
                            futures[future],
                            r['title'],
                            r['url'],
                            r.get('snippet', '')
                        )
                except Exception as e:
                    self.error.emit(f"{futures[future]}: {str(e)}")
        self.finished.emit()

    def fetch_and_parse(self, engine_name, engine, url):
        try:
            resp = requests.get(url, proxies=TOR_PROXY, timeout=TIMEOUT)
            if resp.status_code != 200:
                return []
            parser_name = engine['parser']
            parser_func = globals().get(f'parse_{parser_name}')
            if parser_func:
                return parser_func(resp.text, self.query)
            return []
        except Exception as e:
            # could log but we'll just return empty
            return []

    def stop(self):
        self._is_running = False

# ========== DIALOG ==========
class DarkSearchDialog(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.setWindowTitle("🌐 Dark Web Search Aggregator")
        self.setMinimumSize(900, 650)
        self.setStyleSheet("""
            QDialog { background: #0f0f1a; }
            QLabel { color: #e2e8f0; }
            QLineEdit { background: #2d2d4a; color: #f1f5f9; border: 1px solid #4b4b6e; border-radius: 8px; padding: 6px; }
            QPushButton { background: #3a3a5e; color: #f1f5f9; border: 1px solid #4b4b6e; border-radius: 8px; padding: 8px 16px; }
            QPushButton:hover { background: #4b4b6e; }
            QCheckBox { color: #e2e8f0; }
            QTableWidget { background: #1e1e32; color: #e2e8f0; gridline-color: #3f3f5e; }
            QTableWidget::item { color: #e2e8f0; }
            QHeaderView::section { background: #2d2d4a; color: #e2e8f0; border: 1px solid #3f3f5e; padding: 4px; }
            QProgressBar { border: 1px solid #4b4b6e; border-radius: 4px; text-align: center; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6366f1, stop:1 #3b82f6); }
        """)

        layout = QVBoxLayout()

        # Search row
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Query:"))
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Search dark web...")
        self.query_input.returnPressed.connect(self.start_search)
        search_layout.addWidget(self.query_input)
        layout.addLayout(search_layout)

        # Engines group
        engines_group = QGroupBox("Search Engines (select at least one)")
        engines_group.setStyleSheet("QGroupBox { color: #6366f1; border: 1px solid #3f3f5e; margin-top: 10px; padding-top: 15px; }")
        engines_layout = QHBoxLayout()
        self.engine_checks = {}
        for name in SEARCH_ENGINES:
            cb = QCheckBox(name)
            cb.setChecked(True)  # default all
            engines_layout.addWidget(cb)
            self.engine_checks[name] = cb
        engines_group.setLayout(engines_layout)
        layout.addWidget(engines_group)

        # Buttons
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("🔍 Start Search")
        self.start_btn.clicked.connect(self.start_search)
        btn_layout.addWidget(self.start_btn)
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_search)
        btn_layout.addWidget(self.stop_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Progress bar
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Results table
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Title", "URL", "Engine"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.doubleClicked.connect(self.open_link)
        layout.addWidget(self.table)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        layout.addWidget(close_btn, alignment=Qt.AlignRight)

        self.setLayout(layout)
        self.worker = None
        self.seen_urls = set()

    def start_search(self):
        query = self.query_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Error", "Enter a search query.")
            return
        selected = [name for name, cb in self.engine_checks.items() if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Error", "Select at least one search engine.")
            return

        self.table.setRowCount(0)
        self.seen_urls.clear()
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.worker = SearchWorker(query, selected)
        self.worker.result_found.connect(self.add_result)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def add_result(self, engine, title, url, snippet):
        if url in self.seen_urls:
            return
        self.seen_urls.add(url)
        row = self.table.rowCount()
        self.table.insertRow(row)
        title_item = QTableWidgetItem(title)
        url_item = QTableWidgetItem(url)
        engine_item = QTableWidgetItem(engine)
        self.table.setItem(row, 0, title_item)
        self.table.setItem(row, 1, url_item)
        self.table.setItem(row, 2, engine_item)

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)

    def on_error(self, err):
        # we could log, but ignore single errors
        pass

    def stop_search(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)

    def open_link(self, index):
        url = self.table.item(index.row(), 1).text()
        if url:
            self.browser.new_tab(url)
