#!/usr/bin/env python3
"""
updater.py - Root Browser Auto-Updater
Fetches updates from GitHub repo (raw JSON mode).

Repo: https://github.com/indianinstituteofhacking/rootbrowser
"""
import os
import sys
import json
import shutil
import zipfile
import tempfile
from pathlib import Path
from datetime import datetime

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QProgressBar, QMessageBox, QLineEdit, QComboBox,
    QFormLayout
)


# ============================================================
#  ⚙️  CONFIGURATION — Already set for your repo
# ============================================================
GITHUB_USER     = "indianinstituteofhacking"
GITHUB_REPO     = "rootbrowser"
CURRENT_VERSION = "5.0.0"
BRANCH          = "main"           # or "master"
JSON_PATH       = "updater.json"   # file at repo root

CHECK_ON_STARTUP   = True
CHECK_DELAY_SECONDS = 3
# ============================================================


VERSION_FILE = Path(__file__).parent / "version.json"
CONFIG_FILE  = Path(__file__).parent / "updater_config.json"


def load_config():
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def get_current_version():
    if VERSION_FILE.exists():
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("version", CURRENT_VERSION)
        except Exception:
            pass
    return CURRENT_VERSION


def save_version(v):
    try:
        with open(VERSION_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                "version": v,
                "updated": datetime.now().isoformat()
            }, f, indent=2)
    except Exception:
        pass


def parse_version(v):
    try:
        return tuple(int(x) for x in str(v).strip().lstrip("v").split(".")[:3])
    except Exception:
        return (0, 0, 0)


# ============================================================
#  CHECKER THREAD
# ============================================================
class UpdateChecker(QThread):
    update_found = pyqtSignal(dict)
    no_update = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        cfg = load_config()
        self.user = cfg.get("user", GITHUB_USER)
        self.repo = cfg.get("repo", GITHUB_REPO)
        self.branch = cfg.get("branch", BRANCH)
        self.json_path = cfg.get("json_path", JSON_PATH)

    def run(self):
        try:
            import requests
        except ImportError:
            self.error.emit("requests module missing. Run: pip install requests")
            return

        try:
            url = (f"https://raw.githubusercontent.com/"
                   f"{self.user}/{self.repo}/{self.branch}/{self.json_path}")
            r = requests.get(url, timeout=15)

            if r.status_code == 404:
                # try other branch
                other = "master" if self.branch == "main" else "main"
                url2 = (f"https://raw.githubusercontent.com/"
                        f"{self.user}/{self.repo}/{other}/{self.json_path}")
                r = requests.get(url2, timeout=15)
                if r.status_code == 404:
                    self.error.emit(
                        f"updater.json not found in repo.\n"
                        f"URL tried:\n{url}\n{url2}\n\n"
                        f"Make sure 'updater.json' is at repo root and branch is correct.")
                    return

            if r.status_code != 200:
                self.error.emit(f"HTTP {r.status_code} — could not fetch updater.json")
                return

            try:
                data = r.json()
            except Exception:
                self.error.emit("updater.json is not valid JSON")
                return

            remote_version = str(data.get("version", "0.0.0")).strip()
            download_url = data.get("download_url", "")
            notes = data.get("notes", "No notes provided.")
            current = get_current_version()

            if not download_url:
                self.error.emit("updater.json missing 'download_url'")
                return

            if parse_version(remote_version) > parse_version(current):
                self.update_found.emit({
                    "version": remote_version,
                    "url": download_url,
                    "notes": notes,
                    "current": current,
                })
            else:
                self.no_update.emit(current)

        except Exception as e:
            self.error.emit(f"{type(e).__name__}: {e}")


# ============================================================
#  DOWNLOADER THREAD
# ============================================================
class UpdateDownloader(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url):
        super().__init__()
        self.url = url

    def run(self):
        try:
            import requests
        except ImportError:
            self.error.emit("requests module missing")
            return
        try:
            r = requests.get(self.url, timeout=180, stream=True,
                             allow_redirects=True)
            if r.status_code != 200:
                self.error.emit(f"Download failed (HTTP {r.status_code})")
                return

            total = int(r.headers.get('content-length', 0))
            tmp = Path(tempfile.gettempdir()) / "rootbrowser_update.zip"

            done = 0
            with open(tmp, 'wb') as f:
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
                        done += len(chunk)
                        if total:
                            self.progress.emit(int(done * 100 / total))

            extract = Path(tempfile.gettempdir()) / "rootbrowser_update"
            if extract.exists():
                shutil.rmtree(extract, ignore_errors=True)
            extract.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(tmp, 'r') as z:
                z.extractall(extract)

            subs = [p for p in extract.iterdir() if p.is_dir()]
            if len(subs) == 1:
                extract = subs[0]

            self.finished.emit(str(extract))
        except Exception as e:
            self.error.emit(str(e))


# ============================================================
#  UPDATE DIALOG
# ============================================================
class UpdateDialog(QDialog):
    def __init__(self, info, parent=None):
        super().__init__(parent)
        self.info = info
        self.new_dir = None
        self.setWindowTitle("🚀  Update Available — Root Browser")
        self.setMinimumSize(660, 520)
        self.setStyleSheet("""
            QDialog { background-color: #0f0f1a; }
            QLabel { color: #e2e8f0; }
            QTextEdit {
                background-color: #1e1e32; color: #e2e8f0;
                border: 1px solid #3f3f5e; border-radius: 8px;
                font-family: 'Consolas', monospace;
                font-size: 12px; padding: 10px;
            }
            QPushButton {
                background-color: #3a3a5e; color: #e2e8f0;
                border: 1px solid #4b4b6e; border-radius: 8px;
                padding: 8px 20px; font: 12px 'Segoe UI';
            }
            QPushButton:hover { background-color: #4b4b6e; }
            QProgressBar {
                border: none; border-radius: 6px; text-align: center;
                background-color: #2d2d4a; height: 22px; color: #e2e8f0;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #6366f1, stop:1 #3b82f6);
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout()

        banner = QLabel(f"🚀  Version {info['version']} is available!")
        banner.setAlignment(Qt.AlignCenter)
        banner.setStyleSheet("""
            background-color: #1e3a8a; color: #bfdbfe;
            font: bold 16px 'Segoe UI'; padding: 14px;
            border-radius: 8px; border: 2px solid #3b82f6;
        """)
        layout.addWidget(banner)

        cur = info.get("current", "unknown")
        head = QLabel(
            f"<b>Current:</b> {cur} &nbsp;→&nbsp; <b>New:</b> {info['version']}"
        )
        head.setAlignment(Qt.AlignCenter)
        layout.addWidget(head)

        layout.addWidget(QLabel("📋 Release Notes:"))
        notes = QTextEdit()
        notes.setPlainText(info.get("notes", "No notes."))
        notes.setReadOnly(True)
        notes.setMaximumHeight(220)
        layout.addWidget(notes)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        self.progress.setRange(0, 100)
        layout.addWidget(self.progress)

        self.status = QLabel("Click 'Update Now' to begin.")
        self.status.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        btns = QHBoxLayout()
        btns.addStretch()

        self.later_btn = QPushButton("⏰ Later")
        self.later_btn.clicked.connect(self.reject)
        btns.addWidget(self.later_btn)

        self.update_btn = QPushButton("⬇️  Update Now")
        self.update_btn.setStyleSheet("""
            QPushButton {
                background-color: #065f46; color: #d1fae5;
                border: 1px solid #10b981; border-radius: 8px;
                padding: 8px 24px; font-weight: bold;
            }
            QPushButton:hover { background-color: #047857; }
        """)
        self.update_btn.clicked.connect(self.start_download)
        btns.addWidget(self.update_btn)

        layout.addLayout(btns)
        self.setLayout(layout)

    def start_download(self):
        self.update_btn.setEnabled(False)
        self.later_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setValue(0)
        self.status.setText("Downloading update...")

        self.dl = UpdateDownloader(self.info["url"])
        self.dl.progress.connect(self.progress.setValue)
        self.dl.finished.connect(self.on_extracted)
        self.dl.error.connect(self.on_error)
        self.dl.start()

    def on_extracted(self, extract_dir):
        self.new_dir = extract_dir
        self.progress.setValue(100)
        self.status.setText(f"✅ Downloaded to: {extract_dir}")

        reply = QMessageBox.question(
            self, "Install Update",
            f"Download complete!\n\n"
            f"Apply the update now?\n"
            f"(A backup of the current files will be created.)",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.apply_update()
        else:
            self.later_btn.setEnabled(True)
            self.status.setText(
                f"⚠️ Not applied. Files kept at:\n{extract_dir}")

    def apply_update(self):
        try:
            current_dir = Path(__file__).parent.resolve()
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup = current_dir.parent / f"rootbrowser_backup_{ts}"

            self.status.setText("Backing up current files...")
            shutil.copytree(current_dir, backup, dirs_exist_ok=True)

            self.status.setText("Copying new files...")
            new_dir = Path(self.new_dir)
            protected = {"sessions.db", "passwords.enc", ".pm_key",
                         "version.json", "updater_config.json"}
            copied = 0
            for item in new_dir.iterdir():
                if item.name in protected:
                    continue
                dest = current_dir / item.name
                if item.is_file():
                    shutil.copy2(item, dest)
                    copied += 1
                elif item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                    copied += 1

            save_version(self.info["version"])

            self.status.setText(f"✅ Applied {copied} items. Backup: {backup}")

            QMessageBox.information(
                self, "Update Complete",
                f"Update applied successfully!\n\n"
                f"Backup: {backup}\n\n"
                f"Please RESTART the browser.")
            self.accept()

        except Exception as e:
            QMessageBox.critical(
                self, "Update Failed",
                f"Could not apply update:\n{e}\n\n"
                f"Manual copy from:\n{self.new_dir}")
            self.later_btn.setEnabled(True)
            self.update_btn.setEnabled(True)

    def on_error(self, err):
        self.status.setText(f"❌ Error: {err}")
        self.update_btn.setEnabled(True)
        self.later_btn.setEnabled(True)
        QMessageBox.critical(self, "Update Error", err)


# ============================================================
#  CONFIG DIALOG
# ============================================================
class UpdateConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("⚙️  Updater Configuration")
        self.setMinimumSize(520, 380)
        self.setStyleSheet("""
            QDialog { background-color: #0f0f1a; }
            QLabel { color: #e2e8f0; }
            QLineEdit, QComboBox {
                background-color: #2d2d4a; color: #f1f5f9;
                border: 1px solid #4b4b6e; border-radius: 6px;
                padding: 6px 10px;
            }
            QPushButton {
                background-color: #3a3a5e; color: #e2e8f0;
                border: 1px solid #4b4b6e; border-radius: 8px;
                padding: 8px 18px;
            }
            QPushButton:hover { background-color: #4b4b6e; }
        """)
        layout = QVBoxLayout()
        form = QFormLayout()

        cfg = load_config()
        self.user_edit = QLineEdit(cfg.get("user", GITHUB_USER))
        self.repo_edit = QLineEdit(cfg.get("repo", GITHUB_REPO))
        self.branch_edit = QLineEdit(cfg.get("branch", BRANCH))
        self.json_edit = QLineEdit(cfg.get("json_path", JSON_PATH))

        form.addRow("GitHub Username:", self.user_edit)
        form.addRow("GitHub Repo:", self.repo_edit)
        form.addRow("Branch:", self.branch_edit)
        form.addRow("JSON file path:", self.json_edit)
        layout.addLayout(form)

        info = QLabel(
            "• updater.json should be at repo root\n"
            "• Default branch: main\n"
            "• Restart browser after changing these"
        )
        info.setStyleSheet("color:#94a3b8; font-size:11px;")
        layout.addWidget(info)

        btns = QHBoxLayout()
        btns.addStretch()

        reset_btn = QPushButton("🔄 Reset to Default")
        reset_btn.clicked.connect(self.reset_default)
        btns.addWidget(reset_btn)

        save_btn = QPushButton("💾 Save")
        save_btn.clicked.connect(self.save)
        btns.addWidget(save_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.reject)
        btns.addWidget(close_btn)

        layout.addLayout(btns)
        self.setLayout(layout)

    def reset_default(self):
        self.user_edit.setText(GITHUB_USER)
        self.repo_edit.setText(GITHUB_REPO)
        self.branch_edit.setText(BRANCH)
        self.json_edit.setText(JSON_PATH)

    def save(self):
        cfg = {
            "user": self.user_edit.text().strip(),
            "repo": self.repo_edit.text().strip(),
            "branch": self.branch_edit.text().strip() or "main",
            "json_path": self.json_edit.text().strip() or "updater.json",
        }
        save_config(cfg)
        QMessageBox.information(self, "Saved",
                                "Configuration saved.\nRestart to apply.")
        self.accept()


# ============================================================
#  PUBLIC API
# ============================================================
_keep_alive = []


def check_for_updates(parent=None, silent=True):
    """Check GitHub for updates in background."""
    checker = UpdateChecker()
    _keep_alive.append(checker)

    def on_found(info):
        if hasattr(parent, 'status_bar'):
            try:
                parent.status_bar.showMessage(
                    f"🚀 Update available: {info['version']}", 10000)
            except Exception:
                pass
        dlg = UpdateDialog(info, parent)
        dlg.exec_()

    def on_no_update(cur):
        if not silent:
            QMessageBox.information(
                parent, "No Update",
                f"You are running the latest version ({cur}).")

    def on_error(err):
        if not silent:
            QMessageBox.warning(
                parent, "Update Check Failed",
                f"{err}\n\n"
                f"Check: Help → Updater Config")

    checker.update_found.connect(on_found)
    checker.no_update.connect(on_no_update)
    checker.error.connect(on_error)
    checker.start()
    return checker


def check_for_updates_manual(parent=None):
    return check_for_updates(parent, silent=False)


def open_updater_config(parent=None):
    dlg = UpdateConfigDialog(parent)
    dlg.exec_()


# ============================================================
#  Test standalone
# ============================================================
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)

    # Live test — actually checks your GitHub repo
    print(f"Checking https://github.com/{GITHUB_USER}/{GITHUB_REPO}...")
    print(f"Current version: {get_current_version()}")
    check_for_updates_manual(None)
    sys.exit(app.exec_())
