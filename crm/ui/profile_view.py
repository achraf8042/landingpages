from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QFrame, QMessageBox, QFormLayout, QDialog)
from PySide6.QtCore import Qt, Signal
from styles.theme import Theme
from data import db_manager

class ProfileView(QWidget):
    profile_updated = Signal(str) # Emits new username

    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Title
        title = QLabel("Profile Settings")
        title.setProperty("class", "title")
        title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        layout.addWidget(title)

        # Main Card
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SURFACE};
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }}
        """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(40, 40, 40, 40)
        card_layout.setSpacing(25)

        # Header with Edit Button
        header_layout = QHBoxLayout()
        
        info_title = QLabel("My Profile")
        info_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.PRIMARY};")
        
        edit_btn = QPushButton("Edit Profile")
        edit_btn.setCursor(Qt.PointingHandCursor)
        edit_btn.clicked.connect(self.open_edit_dialog)
        
        header_layout.addWidget(info_title)
        header_layout.addStretch()
        header_layout.addWidget(edit_btn)
        
        card_layout.addLayout(header_layout)
        
        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #E2E8F0;")
        card_layout.addWidget(line)

        # Details Grid
        details_layout = QFormLayout()
        details_layout.setSpacing(20)
        details_layout.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        # Labels for displaying data
        self.lbl_name = QLabel()
        self.lbl_name.setProperty("i18n_skip", True)
        self.lbl_name.setStyleSheet(f"font-size: 16px; color: {Theme.TEXT_PRIMARY}; font-weight: 500;")
        
        self.lbl_speciality = QLabel()
        self.lbl_speciality.setProperty("i18n_skip", True)
        self.lbl_speciality.setStyleSheet(f"font-size: 16px; color: {Theme.TEXT_PRIMARY}; font-weight: 500;")
        
        self.lbl_doctor_title = QLabel()
        self.lbl_doctor_title.setProperty("i18n_skip", True)
        self.lbl_doctor_title.setStyleSheet(f"font-size: 16px; color: {Theme.TEXT_PRIMARY}; font-weight: 500;")
        
        self.lbl_username = QLabel()
        self.lbl_username.setProperty("i18n_skip", True)
        self.lbl_username.setStyleSheet(f"font-size: 16px; color: {Theme.TEXT_PRIMARY}; font-weight: 500;")

        # Helper to style labels
        def create_label(text):
            lbl = QLabel(text)
            lbl.setStyleSheet(f"font-size: 14px; color: {Theme.TEXT_SECONDARY}; font-weight: bold;")
            return lbl

        details_layout.addRow(create_label("Full Name:"), self.lbl_name)
        details_layout.addRow(create_label("Speciality:"), self.lbl_speciality)
        details_layout.addRow(create_label("Doctor Title:"), self.lbl_doctor_title)
        details_layout.addRow(create_label("Username:"), self.lbl_username)

        card_layout.addLayout(details_layout)
        card_layout.addStretch()

        layout.addWidget(card)
        layout.addStretch()

    def load_data(self):
        user = db_manager.get_user_details(self.username)
        if user:
            full_name = f"{user['first_name']} {user['last_name']}" if user['first_name'] and user['last_name'] else "Not set"
            self.lbl_name.setText(full_name)
            self.lbl_speciality.setText(user['speciality'] or "Not set")
            self.lbl_doctor_title.setText(user['doctor_title'] or "Not set")
            self.lbl_username.setText(user['username'])

    def open_edit_dialog(self):
        dialog = ProfileEditDialog(self.username, self)
        if dialog.exec():
            # Refresh data
            self.load_data()
            
            # Check if username changed
            new_username = dialog.new_username_if_changed
            if new_username:
                self.username = new_username
            
            # Always emit signal to update sidebar
            self.profile_updated.emit(self.username)


class ProfileEditDialog(QDialog):
    def __init__(self, username, parent=None):
        super().__init__(parent)
        self.username = username
        self.new_username_if_changed = None
        self.setWindowTitle("Edit Profile")
        self.resize(450, 550)
        self.setStyleSheet(Theme.STYLESHEET)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Edit Your Details")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.PRIMARY}; margin-bottom: 10px;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.first_name = QLineEdit()
        self.last_name = QLineEdit()
        self.speciality = QLineEdit()
        self.speciality.setPlaceholderText("e.g. Cardiologist")
        
        self.doctor_title = QLineEdit()
        self.doctor_title.setPlaceholderText("e.g. MD, DO, MBBS")
        
        self.username_input = QLineEdit()
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Leave blank to keep current")
        
        self.confirm_password = QLineEdit()
        self.confirm_password.setEchoMode(QLineEdit.Password)
        self.confirm_password.setPlaceholderText("Confirm new password")

        form_layout.addRow("First Name:", self.first_name)
        form_layout.addRow("Last Name:", self.last_name)
        form_layout.addRow("Speciality:", self.speciality)
        form_layout.addRow("Doctor Title:", self.doctor_title)
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("New Password:", self.password_input)
        form_layout.addRow("Confirm Password:", self.confirm_password)

        layout.addLayout(form_layout)
        layout.addStretch()

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def load_data(self):
        user = db_manager.get_user_details(self.username)
        if user:
            self.first_name.setText(user['first_name'] or "")
            self.last_name.setText(user['last_name'] or "")
            self.speciality.setText(user['speciality'] or "")
            self.doctor_title.setText(user['doctor_title'] or "")
            self.username_input.setText(user['username'])

    def save_changes(self):
        first_name = self.first_name.text().strip()
        last_name = self.last_name.text().strip()
        speciality = self.speciality.text().strip()
        new_username = self.username_input.text().strip()
        password = self.password_input.text()
        confirm = self.confirm_password.text()

        if not new_username:
            QMessageBox.warning(self, "Error", "Username cannot be empty")
            return

        if password and password != confirm:
            QMessageBox.warning(self, "Error", "Passwords do not match")
            return

        data = {
            'first_name': first_name,
            'last_name': last_name,
            'speciality': speciality,
            'doctor_title': self.doctor_title.text().strip(),
            'username': new_username,
            'password': password if password else None
        }

        success, message = db_manager.update_user_profile(self.username, data)
        
        if success:
            if new_username != self.username:
                self.new_username_if_changed = new_username
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to update profile: {message}")
