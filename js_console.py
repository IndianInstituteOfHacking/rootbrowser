from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QTextEdit, QLabel
from PyQt5.QtCore import Qt, QEvent

class JavaScriptConsole(QDialog):
    def __init__(self, browser, parent=None):
        super().__init__(parent)
        self.browser = browser
        self.history = []
        self.history_index = 0
        self.setWindowTitle("JavaScript Console")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QDialog { background-color: #0f0f1a; }
            QTextEdit { background-color: #1e1e32; color: #e2e8f0; border: 1px solid #3f3f5e; border-radius: 8px; font-family: 'Courier New'; }
            QLineEdit { background-color: #2d2d4a; color: #f1f5f9; border: 1px solid #4b4b6e; border-radius: 8px; padding: 8px; }
        """)
        
        layout = QVBoxLayout()
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        layout.addWidget(self.output)
        
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("> "))
        self.input = QLineEdit()
        self.input.setPlaceholderText("Enter JavaScript...")
        self.input.returnPressed.connect(self.execute_js)
        input_layout.addWidget(self.input)
        layout.addLayout(input_layout)
        
        self.status = QLabel("Ready")
        self.status.setStyleSheet("color: #94a3b8;")
        layout.addWidget(self.status)
        
        self.setLayout(layout)
        self.output.append("JavaScript Console Ready")
        self.input.installEventFilter(self)
    
    def execute_js(self):
        code = self.input.text().strip()
        if not code:
            return
        self.history.append(code)
        self.history_index = len(self.history)
        self.input.clear()
        self.output.append(f"\n> {code}")
        self.status.setText("Executing...")
        
        current_widget = self.browser.tabs.currentWidget()
        if hasattr(current_widget, 'page'):
            current_widget.page().runJavaScript(code, self.handle_result)
    
    def handle_result(self, result):
        if result is not None:
            self.output.append(f"← {repr(result)}")
        self.status.setText("Ready")
    
    def eventFilter(self, obj, event):
        if obj == self.input and event.type() == event.KeyPress:
            if event.key() == Qt.Key_Up:
                if self.history_index > 0:
                    self.history_index -= 1
                    self.input.setText(self.history[self.history_index])
                return True
            elif event.key() == Qt.Key_Down:
                if self.history_index < len(self.history) - 1:
                    self.history_index += 1
                    self.input.setText(self.history[self.history_index])
                elif self.history_index == len(self.history) - 1:
                    self.history_index = len(self.history)
                    self.input.clear()
                return True
        return super().eventFilter(obj, event)