
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QMessageBox, QFormLayout,
                               QHBoxLayout)
from PySide6.QtCore import Qt, Signal
import os
from PySide6.QtGui import QIcon, QPixmap
from styles.theme import Theme
from data import db_manager
from utils.helpers import resource_path

class StandaloneProfileWindow(QWidget):
    """Standalone profile window for first-time setup with forced password change"""
    setup_complete = Signal(str)  # Signal to emit username when setup is complete

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setWindowTitle("DigiSpher EMR - Complete Your Profile")
        self.setWindowIcon(QIcon(resource_path("app_icon.ico")))
        self.resize(1000, 700)
        self.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Profile Card
        card = QFrame()
        card.setObjectName("profileCard")
        card.setFixedSize(550, 650)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SURFACE};
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }}
        """)
        # Add shadow effect
        from PySide6.QtWidgets import QGraphicsDropShadowEffect
        from PySide6.QtGui import QColor
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 25))
        card.setGraphicsEffect(shadow)
        
        # Card Layout
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(20)

        # Title
        title = QLabel("Complete Your Profile")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 32px; font-weight: bold; color: {Theme.PRIMARY};")
        
        subtitle = QLabel("Update Your Details and Change Your Password")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(f"font-size: 18px; color: {Theme.TEXT_SECONDARY}; margin-bottom: 10px;")

        warning_label = QLabel("WARNING: You must change your password before continuing")
        warning_label.setWordWrap(True)
        warning_label.setAlignment(Qt.AlignCenter)
        warning_label.setStyleSheet(f"""
            font-size: 13px; 
            color: #F59E0B; 
            background-color: #FEF3C7;
            padding: 12px;
            border-radius: 8px;
            font-weight: bold;
            margin-bottom: 10px;
        """)

        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(18)
        form_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Helper to create field labels
        def create_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-size: 14px; color: {Theme.TEXT_PRIMARY}; font-weight: bold;")
            return lbl

        # Input fields
        self.first_name = QLineEdit()
        self.first_name.setMinimumHeight(40)
        
        self.last_name = QLineEdit()
        self.last_name.setMinimumHeight(40)
        
        self.speciality = QLineEdit()
        self.speciality.setPlaceholderText("e.g. Cardiologist")
        self.speciality.setMinimumHeight(40)
        
        self.doctor_title = QLineEdit()
        self.doctor_title.setPlaceholderText("e.g. MD, DO, MBBS")
        self.doctor_title.setMinimumHeight(40)
        
        self.new_password = QLineEdit()
        self.new_password.setEchoMode(QLineEdit.Password)
        self.new_password.setPlaceholderText("Enter new password *")
        self.new_password.setMinimumHeight(40)
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setPlaceholderText("Confirm new password *")
        self.confirm_password.setMinimumHeight(40)

        form_layout.addRow(create_label("First Name:"), self.first_name)
        form_layout.addRow(create_label("Last Name:"), self.last_name)
        form_layout.addRow(create_label("Speciality:"), self.speciality)
        form_layout.addRow(create_label("Doctor Title:"), self.doctor_title)
        form_layout.addRow(create_label("New Password *:"), self.new_password)
        form_layout.addRow(create_label("Confirm Password *:"), self.confirm_password)

        # Continue Button
        continue_btn = QPushButton("Save & Continue to Dashboard")
        continue_btn.setMinimumHeight(45)
        continue_btn.setCursor(Qt.PointingHandCursor)
        continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: {Theme.TEXT_INVERSE};
                border: none;
                border-radius: 8px;
                font-weight: bold;
                font-size: 16px;
                margin-top: 10px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT};
            }}
        """)
        continue_btn.clicked.connect(self.handle_save)

        # Add widgets to card
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(warning_label)
        card_layout.addLayout(form_layout)
        card_layout.addWidget(continue_btn)
        card_layout.addStretch()

        # Add card to main layout
        main_layout.addWidget(card)

    def load_data(self):
        """Load existing user data"""
        user = db_manager.get_user_details(self.username)
        if user:
            self.first_name.setText(user['first_name'] or "")
            self.last_name.setText(user['last_name'] or "")
            self.speciality.setText(user['speciality'] or "")
            self.doctor_title.setText(user['doctor_title'] or "")

    def handle_save(self):
        # Get values
        first_name = self.first_name.text().strip()
        last_name = self.last_name.text().strip()
        speciality = self.speciality.text().strip()
        doctor_title = self.doctor_title.text().strip()
        password = self.new_password.text()
        confirm = self.confirm_password.text()

        # Validate password (required)
        if not password:
            QMessageBox.warning(self, "Password Required", 
                "You must set a new password before continuing.\n\nPlease enter a new password.")
            self.new_password.setFocus()
            return
        
        if len(password) < 8 or password == 'doctor123':
            QMessageBox.warning(self, "Weak Password", 
                "Password must be at least 8 characters and differ from the default password.")
            self.new_password.setFocus()
            return
        
        if password != confirm:
            QMessageBox.warning(self, "Password Mismatch", 
                "The passwords you entered do not match.\n\nPlease try again.")
            self.confirm_password.clear()
            self.confirm_password.setFocus()
            return

        # Update profile
        data = {
            'first_name': first_name,
            'last_name': last_name,
            'speciality': speciality,
            'doctor_title': doctor_title,
            'password': password
        }

        try:
            success, message = db_manager.update_user_profile(self.username, data)
            
            if success:
                QMessageBox.information(self, "Success", 
                    "Your profile has been updated successfully!")
                self.setup_complete.emit(self.username)
            else:
                QMessageBox.critical(self, "Error", f"Failed to update profile: {message}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
