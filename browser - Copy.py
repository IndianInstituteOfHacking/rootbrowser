#!/usr/bin/env python3
"""
ROOT BROWSER - Simple Working Version
Sirf PyQt5 + PyQtWebEngine chahiye.
Agar Tor nahi chal raha, USE_TOR = False kar do.
"""
import sys
import os
from urllib.parse import quote

from PyQt5.QtCore import Qt, QUrl, QTimer
from PyQt5.QtGui import QKeySequence, QFont, QColor, QPalette
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout,
    QHBoxLayout, QLineEdit, QPushButton, QToolBar, QStatusBar,
    QLabel, QMessageBox, QProgressBar, QShortcut, QMenu, QComboBox,
    QAction, QTextEdit, QDialog, QDialogButtonBox, QListWidget,
    QListWidgetItem, QFileDialog
)
from PyQt5.QtWebEngineWidgets import (
    QWebEngineView, QWebEngineProfile, QWebEngineSettings, QWebEnginePage
)

# ============================================================
#  SETTINGS
# ============================================================
USE_TOR = False   # True kar do agar Tor chal raha hai (127.0.0.1:9050)

SEARCH_ENGINES = {
    "DuckDuckGo": "https://duckduckgo.com/?q={}",
    "Google": "https://www.google.com/search?q={}",
    "Brave": "https://search.brave.com/search?q={}",
    "Startpage": "https://www.startpage.com/do/dsearch?query={}",
    "Bing": "https://www.bing.com/search?q={}",
}

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")

MAX_TABS = 15


# ============================================================
#  MAIN WINDOW
# ============================================================
class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Root Browser")
        self.setGeometry(100, 100, 1400, 900)

        self.current_search_engine = "DuckDuckGo"
        self.history = []

        # Dark palette
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(15, 15, 26))
        palette.setColor(QPalette.WindowText, QColor(226, 232, 240))
        palette.setColor(QPalette.Base, QColor(30, 30, 50))
        palette.setColor(QPalette.Text, QColor(226, 232, 240))
        palette.setColor(QPalette.Button, QColor(45, 45, 75))
        palette.setColor(QPalette.ButtonText, QColor(226, 232, 240))
        palette.setColor(QPalette.Highlight, QColor(99, 102, 241))
        palette.setColor(QPalette.HighlightedText, Qt.white)
        QApplication.setPalette(palette)

        # Stylesheet
        self.setStyleSheet("""
            QMainWindow { background-color: #0f0f1a; }
            QToolBar {
                background-color: #1e1e32;
                border-bottom: 1px solid #3f3f5e;
                spacing: 6px; padding: 6px;
            }
            QStatusBar {
                background-color: #16162a; color: #94a3b8;
                border-top: 1px solid #3f3f5e;
            }
            QLineEdit {
                background-color: #2d2d4a; color: #f1f5f9;
                border: 1px solid #4b4b6e; border-radius: 14px;
                padding: 7px 14px; font: 13px 'Segoe UI';
            }
            QLineEdit:focus { border-color: #6366f1; }
            QPushButton {
                background-color: #3a3a5e; color: #f1f5f9;
                border: 1px solid #4b4b6e; border-radius: 8px;
                padding: 6px 14px; font: 12px 'Segoe UI';
            }
            QPushButton:hover { background-color: #4b4b6e; }
            QPushButton:pressed { background-color: #6366f1; }
            QTabWidget::pane { border: 1px solid #3f3f5e; }
            QTabBar::tab {
                background-color: #1e1e32; color: #94a3b8;
                padding: 7px 18px; margin-right: 2px;
                border-radius: 8px 8px 0 0;
            }
            QTabBar::tab:selected {
                background-color: #0f0f1a; color: white;
                border-bottom: 2px solid #6366f1;
            }
            QComboBox {
                background-color: #2d2d4a; color: #f1f5f9;
                border: 1px solid #4b4b6e; border-radius: 6px;
                padding: 5px 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #2d2d4a; color: #f1f5f9;
                selection-background-color: #6366f1;
            }
            QMenu {
                background-color: #1e1e32; color: #e2e8f0;
                border: 1px solid #4b4b6e; border-radius: 6px;
                padding: 4px;
            }
            QMenu::item { padding: 6px 20px; border-radius: 4px; }
            QMenu::item:selected { background-color: #6366f1; }
            QProgressBar {
                border: none; border-radius: 6px;
                background-color: #2d2d4a; height: 6px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #3b82f6);
                border-radius: 6px;
            }
            QListWidget, QTextEdit {
                background-color: #1e1e32; color: #e2e8f0;
                border: 1px solid #3f3f5e; border-radius: 6px;
            }
            QLabel { color: #e2e8f0; }
        """)

        # Profile + interceptor (Tor proxy agar enabled hai)
        self.profile = QWebEngineProfile(self)
        self.profile.setHttpUserAgent(USER_AGENT)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.tab_context_menu)
        self.tabs.currentChanged.connect(self.on_tab_changed)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        back_btn = QPushButton("◀")
        back_btn.setToolTip("Back")
        back_btn.clicked.connect(self.go_back)
        toolbar.addWidget(back_btn)

        fwd_btn = QPushButton("▶")
        fwd_btn.setToolTip("Forward")
        fwd_btn.clicked.connect(self.go_forward)
        toolbar.addWidget(fwd_btn)

        reload_btn = QPushButton("↻")
        reload_btn.setToolTip("Reload")
        reload_btn.clicked.connect(self.reload_page)
        toolbar.addWidget(reload_btn)

        home_btn = QPushButton("🏠")
        home_btn.setToolTip("Home")
        home_btn.clicked.connect(self.go_home)
        toolbar.addWidget(home_btn)

        new_tab_btn = QPushButton("+")
        new_tab_btn.setToolTip("New Tab (Ctrl+T)")
        new_tab_btn.clicked.connect(lambda: self.new_tab())
        toolbar.addWidget(new_tab_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or type URL...")
        self.url_bar.returnPressed.connect(self.navigate)
        toolbar.addWidget(self.url_bar)

        self.engine_combo = QComboBox()
        self.engine_combo.addItems(SEARCH_ENGINES.keys())
        self.engine_combo.currentTextChanged.connect(self.change_engine)
        toolbar.addWidget(self.engine_combo)

        notes_btn = QPushButton("Notes")
        notes_btn.clicked.connect(self.open_notes)
        toolbar.addWidget(notes_btn)

        panic_btn = QPushButton("PANIC")
        panic_btn.setStyleSheet(
            "background-color:#e11d48; color:white; "
            "font-weight:bold; border-radius:8px; padding:6px 16px;")
        panic_btn.clicked.connect(self.panic)
        toolbar.addWidget(panic_btn)

        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(180)
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        self.status_bar.addPermanentWidget(self.progress_bar)

        # Central widget
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # Shortcuts
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.new_tab())
        QShortcut(QKeySequence("Ctrl+W"), self,
                  lambda: self.close_tab(self.tabs.currentIndex()))
        QShortcut(QKeySequence("Ctrl+L"), self,
                  lambda: self.url_bar.setFocus())
        QShortcut(QKeySequence("Ctrl+R"), self, self.reload_page)
        QShortcut(QKeySequence("F5"), self, self.reload_page)
        QShortcut(QKeySequence("F11"), self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+Shift+Q"), self, self.panic)
        QShortcut(QKeySequence("Ctrl+H"), self, self.show_history)

        # First tab
        self.new_tab()

    # ---------- Tab management ----------
    def new_tab(self, url=None):
        if self.tabs.count() >= MAX_TABS:
            QMessageBox.warning(self, "Limit", f"Max {MAX_TABS} tabs allowed.")
            return

        view = QWebEngineView()
        page = QWebEnginePage(self.profile, view)
        view.setPage(page)

        s = view.settings()
        s.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        s.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        s.setAttribute(QWebEngineSettings.PluginsEnabled, False)
        s.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        s.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)

        view.setContextMenuPolicy(Qt.CustomContextMenu)
        view.customContextMenuRequested.connect(
            lambda pos, v=view: self.page_context_menu(v, pos))
        view.urlChanged.connect(lambda u, v=view: self.on_url_changed(v, u))
        view.titleChanged.connect(
            lambda t, v=view: self.on_title_changed(v, t))
        view.loadProgress.connect(
            lambda p, v=view: self.on_load_progress(v, p))

        idx = self.tabs.addTab(view, "New Tab")
        self.tabs.setCurrentIndex(idx)

        if url:
            view.setUrl(QUrl(url))
        else:
            view.setHtml(self._home_html())
        return view

    def close_tab(self, idx):
        if self.tabs.count() > 1:
            w = self.tabs.widget(idx)
            self.tabs.removeTab(idx)
            if w:
                w.deleteLater()

    def on_tab_changed(self, idx):
        w = self.tabs.widget(idx)
        if isinstance(w, QWebEngineView):
            self.url_bar.setText(w.url().toString())

    def on_title_changed(self, view, title):
        idx = self.tabs.indexOf(view)
        if idx >= 0 and title:
            self.tabs.setTabText(idx, title[:25])

    def on_url_changed(self, view, url):
        if self.tabs.currentWidget() == view:
            self.url_bar.setText(url.toString())
            self.status_bar.showMessage(f"Loaded: {url.toString()}", 3000)
        try:
            if view.title():
                self.history.append({
                    "title": view.title(),
                    "url": url.toString()
                })
        except Exception:
            pass

    def on_load_progress(self, view, progress):
        if view == self.tabs.currentWidget():
            if progress < 100:
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(progress)
            else:
                self.progress_bar.setVisible(False)

    # ---------- Navigation ----------
    def _current(self):
        w = self.tabs.currentWidget()
        return w if isinstance(w, QWebEngineView) else None

    def navigate(self):
        text = self.url_bar.text().strip()
        if not text:
            return
        w = self._current()
        if not w:
            return

        is_url = (' ' not in text) and (
            text.startswith(('http://', 'https://', 'about:', 'file://')) or
            ('.' in text and not text.startswith(('?', '#')))
        )
        if is_url:
            if not text.startswith(('http://', 'https://',
                                    'about:', 'file://')):
                text = 'https://' + text
            w.setUrl(QUrl(text))
        else:
            engine = SEARCH_ENGINES.get(
                self.current_search_engine,
                SEARCH_ENGINES["DuckDuckGo"])
            w.setUrl(QUrl(engine.format(quote(text))))

    def go_back(self):
        w = self._current()
        if w:
            w.back()

    def go_forward(self):
        w = self._current()
        if w:
            w.forward()

    def reload_page(self):
        w = self._current()
        if w:
            w.reload()

    def go_home(self):
        w = self._current()
        if w:
            w.setHtml(self._home_html())

    def change_engine(self, name):
        self.current_search_engine = name
        self.status_bar.showMessage(f"Search Engine: {name}", 3000)

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def panic(self):
        if QMessageBox.question(
                self, "PANIC", "Exit browser?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            QApplication.quit()

    # ---------- Home page HTML ----------
    def _home_html(self):
        engine = SEARCH_ENGINES.get(
            self.current_search_engine,
            SEARCH_ENGINES["DuckDuckGo"])
        return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>New Tab</title>
<style>
* {{ box-sizing: border-box; }}
body {{
  background: linear-gradient(180deg, #0f0f1a, #1a1a2e);
  color: #e2e8f0; font-family: 'Segoe UI', sans-serif;
  display: flex; justify-content: center; align-items: center;
  height: 100vh; margin: 0;
}}
.card {{
  text-align: center; max-width: 600px; width: 100%;
  background-color: #1e1e32; border: 1px solid #3f3f5e;
  border-radius: 16px; padding: 40px;
  box-shadow: 0 12px 24px rgba(0,0,0,0.4);
}}
h2 {{ color: #6366f1; margin-bottom: 20px; }}
p {{ color: #94a3b8; font-size: 14px; }}
.search-box {{ display: flex; gap: 10px; margin-top: 20px; }}
.search-input {{
  flex: 1; padding: 14px 22px; background-color: #2d2d4a;
  border: 1px solid #4b4b6e; border-radius: 30px;
  color: #f1f5f9; font-size: 16px; outline: none;
}}
.search-input:focus {{ border-color: #6366f1; }}
.search-button {{
  padding: 14px 28px;
  background: linear-gradient(90deg, #6366f1, #3b82f6);
  color: white; border: none; border-radius: 30px;
  font-size: 16px; cursor: pointer; font-weight: bold;
}}
.search-button:hover {{ opacity: 0.9; }}
</style></head>
<body>
<div class="card">
  <h2>Root Browser</h2>
  <p>Type a URL or search query below</p>
  <div class="search-box">
    <input id="q" class="search-input"
           placeholder="Search or type URL..." autofocus>
    <button class="search-button" onclick="go()">Search</button>
  </div>
</div>
<script>
const ENGINE = "{engine}";
function go() {{
  var q = document.getElementById('q').value.trim();
  if (!q) return;
  var isUrl = q.indexOf(' ')===-1 && (
      q.startsWith('http') ||
      (q.indexOf('.')!==-1 && !q.startsWith('?') && !q.startsWith('#')));
  if (isUrl) {{
    if (!q.startsWith('http://') && !q.startsWith('https://')) {{
      q = 'https://' + q;
    }}
    window.location.href = q;
  }} else {{
    window.location.href = ENGINE + encodeURIComponent(q);
  }}
}}
document.getElementById('q').addEventListener('keypress', function(e) {{
  if (e.key === 'Enter') go();
}});
</script>
</body></html>"""

    # ---------- Context menu ----------
    def page_context_menu(self, view, pos):
        menu = QMenu(view)
        menu.addAction("Back", view.back)
        menu.addAction("Forward", view.forward)
        menu.addAction("Reload", view.reload)
        menu.addSeparator()
        menu.addAction("Copy", lambda: view.page().triggerAction(
            QWebEnginePage.Copy))
        menu.addAction("Paste", lambda: view.page().triggerAction(
            QWebEnginePage.Paste))
        menu.addAction("Select All", lambda: view.page().triggerAction(
            QWebEnginePage.SelectAll))
        menu.addSeparator()
        menu.addAction("View Source", lambda: self.view_source(view))
        menu.addAction("Save Page As HTML",
                       lambda: self.save_page(view))
        menu.addAction("Take Screenshot",
                       lambda: self.screenshot(view))
        menu.addSeparator()
        menu.addAction("Copy as cURL",
                       lambda: self.copy_curl(view))
        menu.addAction("Extract Links",
                       lambda: self.extract_links(view))
        menu.addAction("Extract Images",
                       lambda: self.extract_images(view))
        menu.addSeparator()
        menu.addAction("Open in System Browser",
                       lambda: self.open_external(view))
        menu.exec_(view.mapToGlobal(pos))

    def tab_context_menu(self, pos):
        menu = QMenu()
        menu.addAction("New Tab", lambda: self.new_tab())
        menu.addAction("Reload", self.reload_page)
        menu.addAction("Close Tab",
                       lambda: self.close_tab(self.tabs.currentIndex()))
        menu.exec_(self.tabs.mapToGlobal(pos))

    # ---------- Tools ----------
    def view_source(self, view):
        view.page().toHtml(lambda html: self._show_text_dialog(
            "View Source", html))

    def save_page(self, view):
        view.page().toHtml(self._save_html)

    def _save_html(self, html):
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Page As", "page.html", "HTML (*.html)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html)
                self.status_bar.showMessage(f"Saved: {path}", 4000)
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def screenshot(self, view):
        pix = view.grab()
        path, _ = QFileDialog.getSaveFileName(
            self, "Save Screenshot", "screenshot.png", "PNG (*.png)")
        if path:
            pix.save(path)
            self.status_bar.showMessage(f"Saved: {path}", 4000)

    def copy_curl(self, view):
        url = view.url().toString()
        ua = USER_AGENT
        if USE_TOR:
            cmd = (f'curl -x socks5h://127.0.0.1:9050 '
                   f'-H "User-Agent: {ua}" "{url}"')
        else:
            cmd = f'curl -H "User-Agent: {ua}" "{url}"'
        QApplication.clipboard().setText(cmd)
        self.status_bar.showMessage("cURL copied to clipboard", 3000)

    def extract_links(self, view):
        js = ("Array.from(document.querySelectorAll('a[href]'))"
              ".map(a => a.href);")
        view.page().runJavaScript(
            js, lambda links: self._show_list_dialog("Links", links))

    def extract_images(self, view):
        js = ("Array.from(document.querySelectorAll('img[src]'))"
              ".map(i => i.src);")
        view.page().runJavaScript(
            js, lambda imgs: self._show_list_dialog("Images", imgs))

    def _show_list_dialog(self, title, items):
        if not items:
            QMessageBox.information(self, title, "Nothing found.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle(f"{title} ({len(items)})")
        dlg.resize(700, 500)
        layout = QVBoxLayout()
        lw = QListWidget()
        for it in items:
            lw.addItem(QListWidgetItem(str(it)))
        lw.itemDoubleClicked.connect(
            lambda item: self.new_tab(item.text()))
        layout.addWidget(lw)
        btn = QDialogButtonBox(QDialogButtonBox.Close)
        btn.rejected.connect(dlg.reject)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec_()

    def _show_text_dialog(self, title, text):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.resize(800, 600)
        layout = QVBoxLayout()
        te = QTextEdit()
        te.setPlainText(text)
        te.setReadOnly(True)
        layout.addWidget(te)
        btn = QDialogButtonBox(QDialogButtonBox.Close)
        btn.rejected.connect(dlg.reject)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec_()

    def open_external(self, view):
        import webbrowser
        webbrowser.open(view.url().toString())

    def open_notes(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Notes")
        dlg.resize(500, 400)
        layout = QVBoxLayout()
        te = QTextEdit()
        layout.addWidget(te)
        btn = QDialogButtonBox(QDialogButtonBox.Close)
        btn.rejected.connect(dlg.reject)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec_()

    def show_history(self):
        dlg = QDialog(self)
        dlg.setWindowTitle(f"History ({len(self.history)})")
        dlg.resize(600, 400)
        layout = QVBoxLayout()
        lw = QListWidget()
        for h in reversed(self.history):
            item = QListWidgetItem(f"{h['title'][:50]} — {h['url']}")
            item.setData(Qt.UserRole, h['url'])
            lw.addItem(item)
        lw.itemDoubleClicked.connect(
            lambda item: self.new_tab(item.data(Qt.UserRole)))
        layout.addWidget(lw)
        btn = QDialogButtonBox(QDialogButtonBox.Close)
        btn.rejected.connect(dlg.reject)
        layout.addWidget(btn)
        dlg.setLayout(layout)
        dlg.exec_()


# ============================================================
#  ENTRY POINT
# ============================================================
def main():
    if USE_TOR:
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = \
            '--proxy-server=socks5://127.0.0.1:9050'
    else:
        os.environ.pop('QTWEBENGINE_CHROMIUM_FLAGS', None)

    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    win = Browser()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()