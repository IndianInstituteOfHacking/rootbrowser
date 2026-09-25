#!/usr/bin/env python3
"""
licence.py - Root Browser Legal Disclaimer & License
Right-click menu se access karne ke liye.
"""
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QDialogButtonBox, QTabWidget, QWidget,
    QScrollArea, QCheckBox, QMessageBox
)


DISCLAIMER_TEXT = """
⚠️  WARNING — READ CAREFULLY  ⚠️

Root Browser is a POWERFUL tool. It includes:

    • Tor anonymization
    • Anti-fingerprinting engine
    • Hash cracker
    • SQL injection scanner
    • Request repeater
    • DOM manipulation
    • Dark web search
    • Cookie editor
    • Certificate viewer

These features are DANGEROUS if misused.

❌ DO NOT use this software for:
    • Unauthorized access to systems
    • Hacking accounts / emails / social media
    • Attacking websites without written permission
    • Cracking passwords you don't own
    • Scanning networks you don't own
    • Downloading / distributing illegal content
    • Any activity prohibited by law

✅ YOU MAY use this software for:
    • Testing YOUR OWN websites / servers
    • Learning security concepts (in lab)
    • Bug bounty (with written scope)
    • Penetration testing WITH written permission
    • Security research in isolated environments
    • Personal privacy browsing

THE AUTHOR IS NOT RESPONSIBLE for any damage,
legal trouble, or harm caused by misuse of this
software. YOU are solely responsible.
"""

LEGAL_TEXT = """
═══════════════════════════════════════════════
                LEGAL NOTICE
═══════════════════════════════════════════════

This software is provided for LEGAL, ETHICAL use
only. By using it, you agree to the following:

【 INDIA — Applicable Laws 】
  • Information Technology Act, 2000
    - Section 43  : Unauthorized access / damage
    - Section 66  : Computer-related offences
    - Section 66C : Identity theft
    - Section 66D : Cheating by impersonation
    - Section 67  : Obscene content
  • Indian Penal Code (IPC)
    - Section 379 : Theft
    - Section 420 : Cheating
    - Section 500 : Defamation
  • DPDP Act, 2023 (Data Protection)

【 INTERNATIONAL 】
  • USA  : Computer Fraud & Abuse Act (CFAA)
  • UK   : Computer Misuse Act 1990
  • EU   : GDPR, NIS2, Cybercrime Directive
  • Universal : Budapest Convention on Cybercrime

【 PENALTIES 】
  Unauthorized access can lead to:
  • Imprisonment: 3 years to life (depending on
    country and severity)
  • Fines: ₹5 lakh to ₹1 crore+
  • Permanent criminal record
  • Civil lawsuits

═══════════════════════════════════════════════
  THIS IS NOT A HACKING TOOL. IT IS A SECURITY
  RESEARCH AND PRIVACY TOOL. MISUSE IS YOUR
  RESPONSIBILITY AND YOUR CRIME.
═══════════════════════════════════════════════
"""

TERMS_TEXT = """
═══════════════════════════════════════════════
              TERMS OF USE
═══════════════════════════════════════════════

1. ACCEPTANCE
   By clicking "I Accept", you confirm that you
   have read and understood this entire license.

2. AGE REQUIREMENT
   You must be 18+ years old to use this software.

3. AUTHORIZED USE ONLY
   You will use this software ONLY on systems you
   own or have EXPLICIT WRITTEN permission to test.

4. NO WARRANTY
   This software is provided "AS IS", without
   warranty of any kind. It may contain bugs.

5. NO LIABILITY
   The author(s) shall NOT be held liable for:
   • Any direct or indirect damages
   • Data loss
   • Legal consequences
   • Misuse by third parties

6. NO SUPPORT GUARANTEE
   Support is provided on best-effort basis only.

7. PRIVACY
   This software does NOT phone home. It stores
   data locally only (sessions.db, passwords.enc).

8. MODIFICATION
   You may modify the source for personal use.
   Redistribution must retain this license.

9. TERMINATION
   Violation of these terms = immediate license
   termination. You must stop using and destroy
   all copies.

10. GOVERNING LAW
    These terms are governed by Indian law.
    Disputes shall be settled in Indian courts.

═══════════════════════════════════════════════
  If you do NOT agree, click "I Do NOT Accept"
  and close this software immediately.
═══════════════════════════════════════════════
"""

ABOUT_TEXT = """
═══════════════════════════════════════════════
              ABOUT ROOT BROWSER
═══════════════════════════════════════════════

Version   : 5.0
Type      : Security Research Browser
License   : Custom (see License tab)
Built on  : Python 3 + PyQt5 + QtWebEngine
Network   : Tor (SOCKS5) optional
Storage   : Local only (SQLite + files)

FEATURES
────────
• Tor integration
• Anti-fingerprinting (6 levels)
• Session manager
• Certificate viewer (real)
• Encrypted password manager
• Download manager
• Hash cracker (MD5/SHA/NTLM)
• SQL injection scanner
• HTTP request repeater
• DOM manipulator
• Dark web search
• JS / Python consoles
• Cookie editor
• Geolocation spoof
• User-agent switcher
• Ad blocker

PHILOSOPHY
──────────
Root Browser exists to help security
researchers, students, and privacy advocates
learn and protect themselves. It is NOT meant
to harm anyone.

═══════════════════════════════════════════════
        Made with responsibility.
        Use with responsibility.
═══════════════════════════════════════════════
"""


class LicenseDialog(QDialog):
    """Full legal disclaimer dialog with tabs."""

    def __init__(self, parent=None, show_accept=False):
        super().__init__(parent)
        self.setWindowTitle("⚖️  Root Browser — License & Legal Disclaimer")
        self.setMinimumSize(820, 640)
        self.setStyleSheet("""
            QDialog { background-color: #0f0f1a; }
            QLabel { color: #e2e8f0; }
            QTextEdit {
                background-color: #1e1e32;
                color: #e2e8f0;
                border: 1px solid #3f3f5e;
                border-radius: 8px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
            }
            QPushButton {
                background-color: #3a3a5e;
                color: #e2e8f0;
                border: 1px solid #4b4b6e;
                border-radius: 8px;
                padding: 8px 20px;
                font: 12px 'Segoe UI';
            }
            QPushButton:hover {
                background-color: #4b4b6e;
                border-color: #6366f1;
            }
            QTabWidget::pane {
                border: 1px solid #3f3f5e;
                background-color: #0f0f1a;
                border-radius: 8px;
            }
            QTabBar::tab {
                background-color: #1e1e32;
                color: #94a3b8;
                border: 1px solid #3f3f5e;
                padding: 8px 18px;
                margin-right: 2px;
                border-radius: 8px 8px 0 0;
                font: 12px 'Segoe UI';
            }
            QTabBar::tab:selected {
                background-color: #0f0f1a;
                color: #ffffff;
                border-bottom: 2px solid #e11d48;
            }
            QCheckBox { color: #e2e8f0; spacing: 8px; }
        """)

        layout = QVBoxLayout()

        # ---- Danger banner ----
        banner = QLabel("⚠️  DANGEROUS TOOL — READ BEFORE USE  ⚠️")
        banner.setAlignment(Qt.AlignCenter)
        banner.setStyleSheet("""
            background-color: #7f1d1d;
            color: #fecaca;
            font: bold 15px 'Segoe UI';
            padding: 14px;
            border-radius: 8px;
            border: 2px solid #e11d48;
        """)
        layout.addWidget(banner)

        # ---- Tabs ----
        tabs = QTabWidget()
        tabs.addTab(self._make_tab(DISCLAIMER_TEXT), "⚠️ Disclaimer")
        tabs.addTab(self._make_tab(LEGAL_TEXT),      "⚖️ Legal Notice")
        tabs.addTab(self._make_tab(TERMS_TEXT),      "📜 Terms of Use")
        tabs.addTab(self._make_tab(ABOUT_TEXT),      "ℹ️ About")
        layout.addWidget(tabs)

        # ---- Accept checkbox (only on first run) ----
        self.accept_check = None
        if show_accept:
            self.accept_check = QCheckBox(
                "I have read and understood the above. "
                "I will use this software legally and ethically only."
            )
            layout.addWidget(self.accept_check)

        # ---- Buttons ----
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        copy_btn = QPushButton("📋 Copy to Clipboard")
        copy_btn.clicked.connect(self.copy_all)
        btn_layout.addWidget(copy_btn)

        if show_accept:
            decline = QPushButton("❌ I Do NOT Accept")
            decline.setStyleSheet("""
                QPushButton {
                    background-color: #7f1d1d;
                    color: #fecaca;
                    border: 1px solid #e11d48;
                    border-radius: 8px;
                    padding: 8px 20px;
                }
                QPushButton:hover { background-color: #991b1b; }
            """)
            decline.clicked.connect(self.reject_license)
            btn_layout.addWidget(decline)

            accept = QPushButton("✅ I Accept")
            accept.setStyleSheet("""
                QPushButton {
                    background-color: #065f46;
                    color: #d1fae5;
                    border: 1px solid #10b981;
                    border-radius: 8px;
                    padding: 8px 24px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #047857; }
            """)
            accept.clicked.connect(self.accept_license)
            btn_layout.addWidget(accept)
        else:
            close = QPushButton("Close")
            close.clicked.connect(self.accept)
            btn_layout.addWidget(close)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def _make_tab(self, text):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(8, 8, 8, 8)
        te = QTextEdit()
        te.setPlainText(text)
        te.setReadOnly(True)
        l.addWidget(te)
        return w

    def copy_all(self):
        from PyQt5.QtWidgets import QApplication
        all_text = (
            DISCLAIMER_TEXT + "\n\n" +
            LEGAL_TEXT + "\n\n" +
            TERMS_TEXT + "\n\n" +
            ABOUT_TEXT
        )
        QApplication.clipboard().setText(all_text)
        QMessageBox.information(self, "Copied",
                                "Full license copied to clipboard.")

    def accept_license(self):
        if self.accept_check and not self.accept_check.isChecked():
            QMessageBox.warning(
                self, "Not Accepted",
                "Please tick the checkbox to confirm you agree.")
            return
        self.accept()

    def reject_license(self):
        QMessageBox.warning(
            self, "License Declined",
            "You have not accepted the license.\n"
            "The software will now close.")
        self.reject()


# ============================================================
#  Quick shortcut functions
# ============================================================
def show_license(parent=None):
    """Show license dialog (read-only, no accept needed)."""
    dlg = LicenseDialog(parent, show_accept=False)
    dlg.exec_()


def request_acceptance(parent=None) -> bool:
    """
    Show license on first run. Returns True if accepted, False otherwise.
    """
    dlg = LicenseDialog(parent, show_accept=True)
    result = dlg.exec_()
    return result == QDialog.Accepted


# ============================================================
#  Test standalone
# ============================================================
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    dlg = LicenseDialog(show_accept=False)
    dlg.exec_()