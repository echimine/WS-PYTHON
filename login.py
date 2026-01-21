import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QPushButton, QFrame, QGraphicsDropShadowEffect)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont
from Context import Context
from WSClient import WSClient
from app import ChatWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login - Global Chat System")
        self.resize(1200, 800)
        self.initUI()


    def on_click_connect_button(self):
        print(f"Connect button clicked {self.name_input.text()} {self.ip_input.text()} {self.port_input.text()}")
        ctx = Context(self.ip_input.text() or "127.0.0.1", self.port_input.text() or "8080")
        self.client = WSClient(ctx, username=self.name_input.text() or "eliott")
        
        self.chat_window = ChatWindow(self.client)
        self.chat_window.show()

        # Start connection in a separate thread so UI doesn't freeze
        import threading
        self.ws_thread = threading.Thread(target=self.client.connect, daemon=True)
        self.ws_thread.start()
        self.close()

    def initUI(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("background-color: #F2F4F8;")  # Light grey background

        # Card Widget - Wider to fit two columns
        self.card = QFrame()
        self.card.setFixedSize(700, 480) 
        self.card.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 10px;
            }
        """)
        
        # Shadow Effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 20))
        shadow.setOffset(0, 5)
        self.card.setGraphicsEffect(shadow)

        # Card Layout (Horizontal split)
        card_content_layout = QHBoxLayout(self.card)
        card_content_layout.setContentsMargins(0, 0, 0, 0)
        card_content_layout.setSpacing(0)

        # --- LEFT COLUMN: PRESETS ---
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: #F8FAFC; border-top-left-radius: 10px; border-bottom-left-radius: 10px; border-right: 1px solid #E2E8F0;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(30, 40, 30, 40)
        left_layout.setSpacing(15)

        preset_title = QLabel("Presets")
        preset_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #2D3748; margin-bottom: 10px;")
        left_layout.addWidget(preset_title)

        # Preset Buttons (Hardcoded)
        self.add_preset_button(left_layout, "Localhost (Dev)", Context.dev())
        self.add_preset_button(left_layout, "Production", Context.prod())

        left_layout.addStretch()
        card_content_layout.addWidget(left_panel, 40) # 40% width

        # --- RIGHT COLUMN: FORM ---
        right_panel = QWidget()
        right_panel.setStyleSheet("background-color: white; border-top-right-radius: 10px; border-bottom-right-radius: 10px;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(40, 40, 40, 40)
        right_layout.setSpacing(20)

        # Title
        title = QLabel("Custom Connection")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            font-size: 20px; 
            font-weight: bold; 
            color: #1A202C;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            margin-bottom: 10px;
        """)
        right_layout.addWidget(title)
        
        # Name Field
        right_layout.addWidget(self.createLabel("Name"))
        self.name_input = self.createInput("Enter your name")
        right_layout.addWidget(self.name_input)

        # IP Address Field
        right_layout.addWidget(self.createLabel("IP Address"))
        self.ip_input = self.createInput("192.168.1.1")
        right_layout.addWidget(self.ip_input)

        # Port Field
        right_layout.addWidget(self.createLabel("Port"))
        self.port_input = self.createInput("8080")
        right_layout.addWidget(self.port_input)

        # Connect Button
        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setCursor(Qt.PointingHandCursor)
        self.connect_btn.setFixedHeight(45)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #1d4ed8;
                color: white;
                font-weight: 600;
                border-radius: 6px;
                font-size: 14px;
                border: none;
            }
            QPushButton:hover {
                background-color: #1e40af;
            }
            QPushButton:pressed {
                background-color: #172554;
            }
        """)
        self.connect_btn.clicked.connect(self.on_click_connect_button)
        right_layout.addWidget(self.connect_btn)
        
        right_layout.addStretch()
        card_content_layout.addWidget(right_panel, 60) # 60% width

        # Add card to main layout
        main_layout.addWidget(self.card)

    def add_preset_button(self, layout, text, context):
        btn = QPushButton(text)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setFixedHeight(50)
        btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #2D3748;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                font-weight: 600;
                text-align: left;
                padding-left: 20px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                border: 1px solid #CBD5E0;
            }
        """)
        # Calculate values to pass safely
        host_val = context.host
        port_val = str(context.port)
        btn.clicked.connect(lambda: self.load_preset(host_val, port_val))
        layout.addWidget(btn)

    def load_preset(self, host, port):
        self.ip_input.setText(host)
        self.port_input.setText(port)

    def createLabel(self, text):
        label = QLabel(text)
        label.setStyleSheet("""
            font-size: 12px; 
            font-weight: 600; 
            color: #4A5568;
            margin-top: 5px;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        """)
        return label

    def createInput(self, placeholder):
        input_field = QLineEdit()
        input_field.setPlaceholderText(placeholder)
        input_field.setFixedHeight(40)
        input_field.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 0 10px;
                font-size: 14px;
                color: #2D3748;
                background-color: white;
            }
            QLineEdit:focus {
                border: 1px solid #3182CE;
            }
        """)
        return input_field

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
