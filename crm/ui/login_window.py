
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit,
                               QPushButton, QFrame, QMessageBox,
                               QApplication)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from styles.theme import Theme
from data import db_manager
from utils.helpers import resource_path

class LoginWindow(QWidget):
    login_successful = Signal(str)  # Signal to emit username on success

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DigiSpher EMR - Login")
        from utils.helpers import resource_path
        from PySide6.QtGui import QIcon
        self.setWindowIcon(QIcon(resource_path("app_icon.ico")))
        self.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        self.setup_ui()
        self._fit_to_screen()

    def _fit_to_screen(self, margin=40):
        """Grow to a pleasant size but never past what the screen allows.

        The login card is 420x550 inside a centred layout, so the window only
        needs to be as large as the card plus a little breathing room. Asking
        for a fixed 1000x700 made the window overflow smaller screens.
        """
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(1000, 700)
            return
        geo = screen.availableGeometry()
        want_w = min(1000, geo.width() - margin)
        want_h = min(700, geo.height() - margin)
        min_w = self.minimumSizeHint().width()
        min_h = self.minimumSizeHint().height()
        width = max(want_w, min(min_w, geo.width() - 20))
        height = max(want_h, min(min_h, geo.height() - 20))
        self.resize(width, height)
        self.move(geo.x() + max(0, (geo.width() - self.width()) // 2),
                  geo.y() + max(0, (geo.height() - self.height()) // 2))

    def setup_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Login Card
        card = QFrame()
        card.setObjectName("loginCard")
        card.setProperty("class", "card") # For styling if needed, though QFrame.card is in theme
        card.setFixedSize(420, 550)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SURFACE};
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }}
        """)
        # Add shadow effect
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor, QPixmap
        import os
        from utils.helpers import resource_path

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))  # 10% opacity black
        card.setGraphicsEffect(shadow)
        
        # Card Layout
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 32, 40, 36)
        card_layout.setSpacing(16)

        # Logo
        logo_path = resource_path("app_icon.png")
        if os.path.exists(logo_path):
            logo_lbl = QLabel()
            pix = QPixmap(logo_path).scaled(72, 72, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(logo_lbl)

        # Title
        title = QLabel("DigiSpher EMR")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {Theme.PRIMARY};")
        
        subtitle = QLabel("Doctor Login")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 15px; color: {Theme.TEXT_SECONDARY}; margin-bottom: 10px;")

        # Inputs
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setMinimumHeight(45)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setMinimumHeight(45)
        self.password_input.returnPressed.connect(self.handle_login)

        # Login Button
        login_btn = QPushButton("Login")
        login_btn.setMinimumHeight(45)
        login_btn.setCursor(Qt.PointingHandCursor)
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_INVERSE};
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT};
            }}
        """)
        login_btn.clicked.connect(self.handle_login)

        # Add widgets to card
        card_layout.addStretch()
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(self.username_input)
        card_layout.addWidget(self.password_input)
        card_layout.addWidget(login_btn)
        
        # Forgot Password Link
        forgot_btn = QPushButton("Forgot Password?")
        forgot_btn.setCursor(Qt.PointingHandCursor)
        forgot_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.TEXT_SECONDARY};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {Theme.PRIMARY};
                text-decoration: underline;
            }}
        """)
        forgot_btn.clicked.connect(self.show_forgot_password)
        card_layout.addWidget(forgot_btn)
        
        card_layout.addStretch()

        # Add card to main layout
        main_layout.addWidget(card)

    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Error", "Please enter both username and password")
            return

        try:
            conn = db_manager.get_db_connection()
            if not conn:
                QMessageBox.critical(self, "Error", "Database connection failed")
                return
                
            cursor = conn.cursor()
            
            # Get user by username
            cursor.execute("SELECT password_hash, salt FROM Users WHERE username = ?", (username,))
            user = cursor.fetchone()
            conn.close()

            if user:
                stored_hash = user['password_hash']
                salt = user['salt']
                
                if db_manager.verify_password(stored_hash, salt, password):
                    self.login_successful.emit(username)
                else:
                    self.show_error("Invalid username or password")
            else:
                self.show_error("Invalid username or password")

        except Exception as e:
            self.show_error(f"Login error: {str(e)}")

    def show_error(self, message):
        QMessageBox.warning(self, "Login Failed", message)
        self.password_input.clear()

    def show_forgot_password(self):
        QMessageBox.information(
            self, "Password Recovery",
            "For your patients' privacy, passwords cannot be reset using the clinic name. "
            "Contact your clinic administrator for access to an authorized recovery process."
        )


