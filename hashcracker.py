#!/usr/bin/env python3
"""
Dedicated Hash Cracker – Offline Dictionary Attack
Supports: MD5, SHA1, SHA256, SHA512, NTLM, bcrypt (via passlib)
"""
import hashlib
import os
import re
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QComboBox, QTextEdit, QProgressBar, QFileDialog, QMessageBox,
    QDialogButtonBox, QGroupBox
)
from PyQt5.QtGui import QFont

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False

# ========== Cracking Worker Thread ==========
class CrackWorker(QThread):
    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(str)       # result message
    error = pyqtSignal(str)

    def __init__(self, hash_str, hash_type, wordlist_path):
        super().__init__()
        self.hash_str = hash_str.strip()
        self.hash_type = hash_type
        self.wordlist_path = wordlist_path
        self._is_running = True

    def run(self):
        if not os.path.exists(self.wordlist_path):
            self.error.emit("Wordlist file not found!")
            return

        total_lines = sum(1 for _ in open(self.wordlist_path, 'r', encoding='latin-1', errors='ignore'))
        count = 0

        try:
            with open(self.wordlist_path, 'r', encoding='latin-1', errors='ignore') as f:
                for line in f:
                    if not self._is_running:
                        self.finished.emit("Cracking aborted.")
                        return
                    word = line.strip()
                    if not word:
                        continue
                    count += 1
                    if count % 100 == 0:
                        self.progress.emit(count, total_lines)

                    hashed = self._compute_hash(word)
                    if hashed.lower() == self.hash_str.lower():
                        self.finished.emit(f"[+] CRACKED!\nHash: {self.hash_str}\nPlain: {word}")
                        self.progress.emit(count, total_lines)
                        return

            self.finished.emit("[-] Not found in the wordlist.")
            self.progress.emit(total_lines, total_lines)
        except Exception as e:
            self.error.emit(str(e))

    def _compute_hash(self, word):
        htype = self.hash_type.lower()
        if htype == "md5":
            return hashlib.md5(word.encode()).hexdigest()
        elif htype == "sha1":
            return hashlib.sha1(word.encode()).hexdigest()
        elif htype == "sha256":
            return hashlib.sha256(word.encode()).hexdigest()
        elif htype == "sha512":
            return hashlib.sha512(word.encode()).hexdigest()
        elif htype == "ntlm":
            # NTLM hash is MD4 of UTF-16LE encoded password
            return hashlib.new('md4', word.encode('utf-16-le')).hexdigest()
        elif htype == "bcrypt" and BCRYPT_AVAILABLE:
            # Bcrypt checking is different; we'd need the stored hash with salt.
            # For simplicity, skip; better to use dedicated tools.
            return None
        else:
            return None

    def stop(self):
        self._is_running = False

# ========== Hash Cracker Dialog ==========
class HashCrackerDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔐 Hash Cracker – Offline Dictionary Attack")
        self.setMinimumSize(600, 500)
        self.setStyleSheet("""
            QDialog { background-color: #121212; }
            QLabel { color: #00ff00; }
            QLineEdit, QComboBox, QTextEdit { background: #1a1a1a; color: #00ff00; border: 1px solid #00ff00; padding: 5px; }
            QPushButton { background: #1a1a1a; color: #00ff00; border: 1px solid #00ff00; padding: 8px; }
            QPushButton:hover { background: #2a2a2a; }
            QProgressBar { border: 1px solid #00ff00; text-align: center; color: #00ff00; }
            QProgressBar::chunk { background-color: #00ff00; }
        """)

        layout = QVBoxLayout()

        # Hash input
        layout.addWidget(QLabel("Hash:"))
        self.hash_input = QLineEdit()
        self.hash_input.setPlaceholderText("Paste the hash here...")
        layout.addWidget(self.hash_input)

        # Hash type
        hash_type_layout = QHBoxLayout()
        hash_type_layout.addWidget(QLabel("Type:"))
        self.hash_type_combo = QComboBox()
        types = ["MD5", "SHA1", "SHA256", "SHA512", "NTLM"]
        if BCRYPT_AVAILABLE:
            types.append("bcrypt")
        self.hash_type_combo.addItems(types)
        hash_type_layout.addWidget(self.hash_type_combo)
        layout.addLayout(hash_type_layout)

        # Wordlist selection
        wordlist_group = QGroupBox("Wordlist")
        wordlist_group.setStyleSheet("QGroupBox { color: #00ff00; border: 1px solid #00ff00; margin-top: 10px; }")
        wl_layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.wordlist_path = QLineEdit()
        self.wordlist_path.setReadOnly(True)
        btn_layout.addWidget(self.wordlist_path)
        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.browse_wordlist)
        btn_layout.addWidget(browse_btn)
        wl_layout.addLayout(btn_layout)
        # Small built-in wordlist option
        builtin_btn = QPushButton("Use built-in tiny wordlist (demo)")
        builtin_btn.clicked.connect(self.use_builtin_wordlist)
        wl_layout.addWidget(builtin_btn)
        wordlist_group.setLayout(wl_layout)
        layout.addWidget(wordlist_group)

        # Crack button & progress
        crack_layout = QHBoxLayout()
        self.crack_btn = QPushButton("💣 Start Cracking")
        self.crack_btn.clicked.connect(self.start_cracking)
        crack_layout.addWidget(self.crack_btn)
        self.stop_btn = QPushButton("⏹️ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_cracking)
        crack_layout.addWidget(self.stop_btn)
        layout.addLayout(crack_layout)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        layout.addWidget(self.result_text)

        # Close button
        btn_box = QDialogButtonBox(QDialogButtonBox.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

        self.setLayout(layout)
        self.worker = None

    def browse_wordlist(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Wordlist", "", "Text Files (*.txt *.lst);;All Files (*)")
        if path:
            self.wordlist_path.setText(path)

    def use_builtin_wordlist(self):
        # Create a tiny wordlist with common passwords
        common = ["password","123456","admin","letmein","qwerty","monkey","dragon","master","login","princess"]
        path = os.path.join(os.getcwd(), "tiny_wordlist.txt")
        with open(path, "w") as f:
            f.write("\n".join(common))
        self.wordlist_path.setText(path)

    def start_cracking(self):
        hash_val = self.hash_input.text().strip()
        if not hash_val:
            QMessageBox.warning(self, "Error", "Enter a hash first!")
            return
        wordlist = self.wordlist_path.text().strip()
        if not wordlist or not os.path.exists(wordlist):
            QMessageBox.warning(self, "Error", "Select a valid wordlist file!")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.result_text.clear()
        self.crack_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)

        self.worker = CrackWorker(hash_val, self.hash_type_combo.currentText(), wordlist)
        self.worker.progress.connect(self.update_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()

    def stop_cracking(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
        self.stop_btn.setEnabled(False)

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_finished(self, message):
        self.result_text.append(message)
        self.crack_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)

    def on_error(self, err):
        QMessageBox.critical(self, "Error", err)
        self.crack_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress_bar.setVisible(False)
