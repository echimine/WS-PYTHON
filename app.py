import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QListWidget, QListWidgetItem, QLineEdit, 
                             QComboBox, QFrame, QScrollArea, QSizePolicy, QFileDialog, QStackedWidget)
from PyQt5.QtCore import Qt, QSize, QUrl
from PyQt5.QtGui import QIcon, QFont, QColor
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from Message import Message
import datetime
from Message import MessageType
import base64
import tempfile
import os
from PyQt5.QtGui import QPixmap

class ChatWindow(QMainWindow):
    def __init__(self, client):
        super().__init__()
        self.setWindowTitle("Global Chat System")
        self.resize(1200, 800)
        self.client = client
        self.client.message_received.connect(self.on_new_message)
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.initUI()

    def on_click_disconnect_button(self):
        from login import LoginWindow
        self.client.ws.close()
        self.login_window = LoginWindow()
        self.login_window.show()
        self.close()

    def on_new_message(self, message:Message):
        message_type = message.message_type
        receiver = message.receiver
        content = message.value
        emitter = message.emitter
        time_str = datetime.datetime.now().strftime("%I:%M %p")
        if message_type == MessageType.SYS_MESSAGE:
            if content == "VU":
                self.add_mock_message(emitter, receiver, time_str, "Le message à bien été reçu")
        if message_type == MessageType.RECEPTION.IMAGE:
            # decode image + add in ui
            content = content.split(":")[1]
            content = base64.b64decode(content)
            self.update_media_panel(content)

        elif message_type == MessageType.RECEPTION.AUDIO:
            # split header if present (e.g. AUDIO:base64...)
            if ":" in content:
                content = content.split(":")[1]
            
            self.play_media(content, is_video=False)
        
        elif message_type == MessageType.RECEPTION.VIDEO:
            print("Video received client")
            content = content.split(":")[1]
            self.play_media(content, is_video=True)

        elif message_type == MessageType.RECEPTION.TEXT:
            if receiver == "ALL" and emitter != self.client.username:
                self.add_mock_message(emitter, receiver, time_str, content)
            elif emitter != self.client.username:
                self.add_mock_message(emitter, receiver, time_str, content)

        elif message_type == MessageType.RECEPTION.CLIENT_LIST:
            self.update_client_list(content)

    def update_client_list(self, content):
        self.send_to_box.clear()
        self.send_to_box.addItem("ALL")
        for client_name in content:
            if client_name != "ALL" and not client_name.startswith(("ADMIN", "ADMIN_")):
                self.send_to_box.addItem(client_name)

    def send_message(self):
        message = self.msg_input.text()
        if message:
            self.client.send(message, self.send_to_box.currentText())
            self.msg_input.clear()
            self.add_mock_message(self.client.username, self.send_to_box.currentText(), datetime.datetime.now().strftime("%I:%M %p"), message)

    def on_click_attach(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getOpenFileName(self, "Select File", "", "ALL Files (*);;Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp);;Audio (*.mp3 *.wav *.aac *.flac);;Video (*.mp4 *.mov *.avi *.mkv)", options=options)
        if fileName:
            dest = self.send_to_box.currentText()
            # Determine type based on extension
            lower_name = fileName.lower()
            if lower_name.endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif')):
                self.client.send_image(fileName, dest)
                self.add_mock_message(self.client.username, dest, datetime.datetime.now().strftime("%I:%M %p"), f"Image sent: {fileName.split('/')[-1]}")
            elif lower_name.endswith(('.mp3', '.wav', '.aac', '.flac')):
                self.client.send_audio(fileName, dest)
                self.add_mock_message(self.client.username, dest, datetime.datetime.now().strftime("%I:%M %p"), f"Audio sent: {fileName.split('/')[-1]}")
            elif lower_name.endswith(('.mp4', '.mov', '.avi', '.mkv')):
                self.client.send_video(fileName, dest)
                self.add_mock_message(self.client.username, dest, datetime.datetime.now().strftime("%I:%M %p"), f"Video sent: {fileName.split('/')[-1]}")
            else:
                print("Unsupported file format")

    def initUI(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Header
        header = QFrame()
        header.setFixedHeight(80)
        header.setStyleSheet("background-color: white; border-bottom: 1px solid #E2E8F0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(30, 0, 30, 0)

        # Title and Subtitle area
        title_area = QVBoxLayout()
        title_area.setSpacing(2)
        
        app_title = QLabel("Global Chat System")
        app_title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1A202C;")
        
        status_label = QLabel(f"Connected as {self.client.username}")
        status_label.setStyleSheet("font-size: 13px; color: #718096;")
        
        title_area.addWidget(app_title)
        title_area.addWidget(status_label)
        
        header_layout.addLayout(title_area)
        header_layout.addStretch()

        # Disconnect Button
        disconnect_btn = QPushButton("Disconnect")
        disconnect_btn.setIcon(QIcon.fromTheme("application-exit")) # Placeholder icon
        disconnect_btn.setFixedHeight(38)
        disconnect_btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; 
                color: white; 
                border-radius: 6px; 
                padding: 0 15px;
                font-weight: 600;
                font-size: 13px;
                border: none;
            }
            QPushButton:hover { background-color: #DC2626; }
        """)
        disconnect_btn.clicked.connect(self.on_click_disconnect_button)
        header_layout.addWidget(disconnect_btn)

        main_layout.addWidget(header)

        # 2. Main Content Area (Split Left/Right)
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # --- Left Panel: Chat ---
        left_panel = QWidget()
        left_panel.setStyleSheet("background-color: white;")
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(30, 30, 30, 30)
        
        # Message Area (For now using QListWidget to hold items)
        self.message_list = QListWidget()
        self.message_list.setFrameShape(QFrame.NoFrame)
        self.message_list.setStyleSheet("""
            QListWidget {
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #F7FAFC;
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #CBD5E0;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #A0AEC0;
            }
            QScrollBar::add-line:vertical {
                height: 0px;
                subcontrol-position: bottom;
                subcontrol-origin: margin;
            }
            QScrollBar::sub-line:vertical {
                height: 0px;
                subcontrol-position: top;
                subcontrol-origin: margin;
            }
        """)
        # Add some mock messages
        #self.add_mock_message("Bob", "ALL", "08:38 AM", "Hello everyone!")
        
        left_layout.addWidget(self.message_list)
        
        # Input Area
        input_container = QFrame()
        input_container.setStyleSheet("border-top: 1px solid #E2E8F0; background-color: white;")
        input_layout = QHBoxLayout(input_container)
        input_layout.setContentsMargins(0, 20, 0, 0)
        
        # "Send to" dropdown
        send_to_layout = QVBoxLayout()
        send_to_label = QLabel("Send to:")
        send_to_label.setStyleSheet("font-size: 12px; color: #718096; font-weight: 600;")
        self.send_to_box = QComboBox()
        self.send_to_box.setFixedSize(120, 40)
        self.send_to_box.setStyleSheet("""
            QComboBox {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding-left: 10px;
                background-color: white;
                color: #2D3748;
            }
            QComboBox:hover {
                border: 1px solid #CBD5E0;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background-color: white;
                border: 1px solid #E2E8F0;
                selection-background-color: #E2E8F0;
                selection-color: #2D3748;
                outline: none;
            }
        """)
        send_to_layout.addWidget(send_to_label)
        send_to_layout.addWidget(self.send_to_box)
        
        # Message Input
        msg_layout = QVBoxLayout()
        msg_label = QLabel("Message:")
        msg_label.setStyleSheet("font-size: 12px; color: #718096; font-weight: 600;")
        self.msg_input = QLineEdit()
        self.msg_input.setPlaceholderText("Type your message...")
        self.msg_input.setFixedHeight(40)
        self.msg_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #E2E8F0;
                border-radius: 6px;
                padding: 0 10px;
                background-color: white;
            }
        """)
        msg_layout.addWidget(msg_label)
        msg_layout.addWidget(self.msg_input)
        
        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setAlignment(Qt.AlignBottom)
        
        attach_btn = QPushButton("+")
        attach_btn.setFixedSize(50, 40)
        attach_btn.setStyleSheet("""
            QPushButton {
                background-color: #F1F5F9;
                color: #475569;
                border-radius: 6px;
                font-weight: bold;
                font-size: 20px;
                border: 1px solid #E2E8F0;
            }
            QPushButton:hover { 
                background-color: #E2E8F0;
                color: #1E293B;
            }
        """)
        attach_btn.clicked.connect(self.on_click_attach)
        
        send_btn = QPushButton("Send")
        send_btn.setIcon(QIcon.fromTheme("document-send"))
        send_btn.setFixedSize(90, 40)
        send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3B82F6; 
                color: white;
                border-radius: 6px; 
                font-weight: 600;
                border: none;
            }
            QPushButton:hover { background-color: #2563EB; }
        """)
        send_btn.clicked.connect(self.send_message)
        # If active: background-color: #3B82F6 (Blue)
        
        btn_layout.addWidget(attach_btn)
        btn_layout.addWidget(send_btn)
        
        input_layout.addLayout(send_to_layout)
        input_layout.addSpacing(10)
        input_layout.addLayout(msg_layout)
        input_layout.addSpacing(10)
        input_layout.addLayout(btn_layout)
        
        left_layout.addWidget(input_container)
        
        # --- Right Panel: Media ---
        right_panel = QFrame()
        right_panel.setFixedWidth(350)
        right_panel.setStyleSheet("background-color: white; border-left: 1px solid #E2E8F0;")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(20, 20, 20, 20)
        
        media_title = QLabel("Media Panel")
        media_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #2D3748;")
        media_subtitle = QLabel("Latest shared media")
        media_subtitle.setStyleSheet("font-size: 12px; color: #718096; margin-bottom: 20px;")
        
        right_layout.addWidget(media_title)
        right_layout.addWidget(media_subtitle)
        
        # Placeholder Content
        placeholder_widget = QWidget()
        ph_layout = QVBoxLayout(placeholder_widget)
        ph_layout.setAlignment(Qt.AlignCenter)
        
        # In a real app, use an icon image. Here, just a Label with unicode or text

        # Stacked Widget to switch between Image and Video
        self.media_stack = QStackedWidget()
        
        # 1. Image Page
        self.image_label = QLabel("📷")
        self.image_label.setStyleSheet("font-size: 40px; color: #CBD5E0; background-color: #F7FAFC; padding: 20px; border-radius: 40px;")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.media_stack.addWidget(self.image_label)
        
        # 2. Video/Audio Page
        self.video_container = QWidget()
        self.video_layout = QVBoxLayout(self.video_container)
        self.video_layout.setContentsMargins(0,0,0,0)
        
        self.video_widget = QVideoWidget()
        self.video_widget.setStyleSheet("background-color: black;")
        self.video_layout.addWidget(self.video_widget)
        
        # Media Controls
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 10, 0, 0)
        
        play_btn = QPushButton("▶ Play")
        play_btn.setFixedSize(80, 30)
        play_btn.clicked.connect(self.media_player.play)
        
        pause_btn = QPushButton("⏸ Pause")
        pause_btn.setFixedSize(80, 30)
        pause_btn.clicked.connect(self.media_player.pause)
        
        controls_layout.addStretch()
        controls_layout.addWidget(play_btn)
        controls_layout.addWidget(pause_btn)
        controls_layout.addStretch()
        
        self.video_layout.addLayout(controls_layout)
        
        self.media_player.setVideoOutput(self.video_widget)
        self.media_player.error.connect(self.handle_media_error)

        self.media_stack.addWidget(self.video_container)
        
        ph_layout.addWidget(self.media_stack)
        
        right_layout.addWidget(placeholder_widget)
        right_layout.addStretch()

        # Add panels to split layout
        content_layout.addWidget(left_panel, 70)
        content_layout.addWidget(right_panel, 30)

        main_layout.addWidget(content_area)

    def handle_media_error(self):
        print(f"Media Error: {self.media_player.errorString()}")

    def update_media_panel(self, image_bytes):
        pixmap = QPixmap()
        pixmap.loadFromData(image_bytes)
        
        if not pixmap.isNull():
            # Scale to fit
            scaled_pixmap = pixmap.scaled(300, 300, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setText("") 
            self.image_label.setStyleSheet("background-color: transparent;")
            self.media_stack.setCurrentWidget(self.image_label)

    def play_media(self, base64_content, is_video=True):
        # Decode and save to temp file
        try:
            data = base64.b64decode(base64_content)
            # Create a temp file with appropriate extension
            suffix = ".mp4" if is_video else ".mp3"
            
            # Note: In a real app we might want to manage these files better (clean up)
            # For now, we create a temp file that persists at least until played
            fd, path = tempfile.mkstemp(suffix=suffix)
            with os.fdopen(fd, 'wb') as tmp:
                tmp.write(data)
            
            url = QUrl.fromLocalFile(path)
            content = QMediaContent(url)
            self.media_player.setMedia(content)
            
            self.media_stack.setCurrentWidget(self.video_container)
            self.media_player.play()
            print(f"Playing media from: {path}")
            
        except Exception as e:
            print(f"Error playing media: {e}")

    def add_mock_message(self, sender, target, time, message):
        item_widget = QWidget()
        item_layout = QVBoxLayout(item_widget)
        item_layout.setContentsMargins(0, 0, 0, 15)
        
        # Header: Name -> Target Time
        header_text = QLabel(f"<b>{sender}</b> <span style='color:#718096;'>&rarr; {target} {time}</span>")
        header_text.setStyleSheet("font-size: 12px; color: #2D3748; margin-bottom: 5px;")
        header_text.setTextFormat(Qt.RichText)
        
        # Body
        msg_box = QLabel(message)
        msg_box.setWordWrap(True)
        msg_box.setStyleSheet("""
            background-color: white; 
            border: 1px solid #E2E8F0; 
            border-radius: 8px; 
            padding: 12px; 
            font-size: 14px; 
            color: #2D3748;
        """)
        
        item_layout.addWidget(header_text)
        item_layout.addWidget(msg_box)
        
        item = QListWidgetItem(self.message_list)
        item.setSizeHint(item_widget.sizeHint())
        self.message_list.setItemWidget(item, item_widget)
        self.message_list.scrollToBottom()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    chat_win = ChatWindow()
    chat_win.show()
    sys.exit(app.exec_())
