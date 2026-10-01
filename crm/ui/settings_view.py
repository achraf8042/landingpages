from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QPushButton, QFrame, QFileDialog, QMessageBox, 
                               QSpinBox, QScrollArea, QLineEdit, QDialog, QFormLayout, QTextEdit, QComboBox, QSizePolicy,
                               QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
from styles.theme import Theme
from data import db_manager
from utils import currency
from utils.localization import manager, tr
from utils.french_documents import privacy_html, LICENSE
import os
from datetime import datetime

class SettingsView(QWidget):
    request_profile_view = Signal() # Signal to switch to profile view
    inactivity_timeout_changed = Signal(int) # Signal when timeout changes (minutes)
    
    def __init__(self, username):
        super().__init__()
        self.username = username
        self.setup_ui()

    def setup_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background-color: transparent;
            }
            QScrollBar:vertical {
                border: none;
                background: #F1F5F9;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #06b6d4;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
                width: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
        """)

        # Scroll Content
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(25)

        # Title
        title = QLabel("Settings")
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {Theme.TEXT_PRIMARY}; margin-bottom: 10px;")
        content_layout.addWidget(title)

        # 1. Profile Card
        profile_card = self.create_card()
        profile_layout = QHBoxLayout(profile_card)
        profile_layout.setContentsMargins(30, 30, 30, 30)
        profile_layout.setSpacing(20)

        # Avatar
        avatar_label = QLabel("👨‍⚕️")
        avatar_label.setStyleSheet("font-size: 64px;")
        profile_layout.addWidget(avatar_label)

        # User Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(5)
        
        name_label = QLabel("User Profile")
        name_label.setWordWrap(True)
        name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        name_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        desc_label = QLabel("Manage your personal information and account settings")
        desc_label.setWordWrap(True)
        desc_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        desc_label.setStyleSheet(f"font-size: 14px; color: {Theme.TEXT_SECONDARY};")
        
        info_layout.addWidget(name_label)
        info_layout.addWidget(desc_label)
        info_layout.addStretch()
        
        # Stretch is given to the text column, not to a trailing spacer, otherwise
        # the spacer (stretch factor 1) wins and the wrapped text is squeezed.
        profile_layout.addLayout(info_layout, 1)

        # Edit Profile Button
        edit_profile_btn = QPushButton("Edit Profile")
        edit_profile_btn.setCursor(Qt.PointingHandCursor)
        edit_profile_btn.setMinimumWidth(140)
        edit_profile_btn.setFixedHeight(40)
        edit_profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        edit_profile_btn.clicked.connect(self.request_profile_view.emit)
        profile_layout.addWidget(edit_profile_btn, alignment=Qt.AlignVCenter)

        content_layout.addWidget(profile_card)

        language_card = self.create_card()
        language_layout = QHBoxLayout(language_card)
        language_layout.setContentsMargins(30, 22, 30, 22)
        language_info = QVBoxLayout()
        language_title = QLabel("Language")
        language_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        language_desc = QLabel("Choose the language used throughout DigiSpher EMR")
        language_desc.setWordWrap(True)
        language_desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        language_desc.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        language_info.addWidget(language_title)
        language_info.addWidget(language_desc)
        language_layout.addLayout(language_info, 1)
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Français", "fr")
        self.language_combo.setCurrentIndex(0 if manager().locale == "en" else 1)
        self.language_combo.setMinimumSize(120, 36)
        self.language_combo.currentIndexChanged.connect(
            lambda index: manager().set_locale(self.language_combo.itemData(index))
        )
        language_layout.addWidget(self.language_combo, alignment=Qt.AlignVCenter)
        content_layout.addWidget(language_card)

        # 2. Clinic Information Card
        clinic_card = self.create_card()
        clinic_layout = QHBoxLayout(clinic_card)
        clinic_layout.setContentsMargins(30, 30, 30, 30)
        clinic_layout.setSpacing(20)

        # Clinic Icon
        clinic_icon = QLabel("🏥")
        clinic_icon.setStyleSheet("font-size: 64px;")
        clinic_layout.addWidget(clinic_icon)

        # Clinic Info
        clinic_info_layout = QVBoxLayout()
        clinic_info_layout.setSpacing(5)
        
        clinic_name_label = QLabel("Clinic Information")
        clinic_name_label.setWordWrap(True)
        clinic_name_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        clinic_name_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        self.clinic_name_label = clinic_name_label
        
        clinic_desc_label = QLabel("Manage your clinic details and license information")
        clinic_desc_label.setWordWrap(True)
        clinic_desc_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        clinic_desc_label.setStyleSheet(f"font-size: 14px; color: {Theme.TEXT_SECONDARY};")
        self.clinic_desc_label = clinic_desc_label
        
        clinic_info_layout.addWidget(clinic_name_label)
        clinic_info_layout.addWidget(clinic_desc_label)
        clinic_info_layout.addStretch()
        
        clinic_layout.addLayout(clinic_info_layout, 1)

        # Edit Clinic Button
        edit_clinic_btn = QPushButton("Edit Clinic Info")
        edit_clinic_btn.setCursor(Qt.PointingHandCursor)
        edit_clinic_btn.setMinimumWidth(140)
        edit_clinic_btn.setFixedHeight(40)
        edit_clinic_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        edit_clinic_btn.clicked.connect(self.open_clinic_edit_dialog)
        clinic_layout.addWidget(edit_clinic_btn, alignment=Qt.AlignVCenter)

        content_layout.addWidget(clinic_card)

        # 3. Security & Data Card
        security_card = self.create_card()
        security_layout = QVBoxLayout(security_card)
        security_layout.setContentsMargins(30, 30, 30, 30)
        security_layout.setSpacing(20)

        security_title = QLabel("Security & Data")
        security_title.setWordWrap(True)
        security_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.TEXT_PRIMARY}; margin-bottom: 10px;")
        security_layout.addWidget(security_title)

        # Database Backup Row
        backup_row = QHBoxLayout()
        backup_row.setSpacing(15)
        
        backup_icon = QLabel("💾")
        backup_icon.setStyleSheet("font-size: 32px;")
        backup_row.addWidget(backup_icon)
        
        backup_info = QVBoxLayout()
        backup_info.setSpacing(5)
        
        backup_label = QLabel("Database Backup")
        backup_label.setWordWrap(True)
        backup_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        backup_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {Theme.TEXT_PRIMARY};")
        
        backup_desc = QLabel("Create a backup copy of your clinic database")
        backup_desc.setWordWrap(True)
        backup_desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        backup_desc.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        
        backup_info.addWidget(backup_label)
        backup_info.addWidget(backup_desc)
        
        backup_row.addLayout(backup_info, 1)
        
        backup_btn = QPushButton("Backup Now")
        backup_btn.setCursor(Qt.PointingHandCursor)
        backup_btn.setMinimumWidth(120)
        backup_btn.setFixedHeight(36)
        backup_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SUCCESS};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #16a34a;
            }}
        """)
        backup_btn.clicked.connect(self.backup_database)
        backup_row.addWidget(backup_btn, alignment=Qt.AlignVCenter)
        
        security_layout.addLayout(backup_row)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        security_layout.addWidget(divider)

        # Auto-Logout Row
        logout_row = QHBoxLayout()
        logout_row.setSpacing(15)
        
        logout_icon = QLabel("⏱️")
        logout_icon.setStyleSheet("font-size: 32px;")
        logout_row.addWidget(logout_icon)
        
        logout_info = QVBoxLayout()
        logout_info.setSpacing(5)
        
        logout_label = QLabel("Auto-Logout Timer")
        logout_label.setWordWrap(True)
        logout_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        logout_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {Theme.TEXT_PRIMARY};")
        
        logout_desc = QLabel("Automatically logout after period of inactivity")
        logout_desc.setWordWrap(True)
        logout_desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        logout_desc.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        
        logout_info.addWidget(logout_label)
        logout_info.addWidget(logout_desc)
        
        logout_row.addLayout(logout_info, 1)
        
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 120)
        self.timeout_spin.setValue(15)
        self.timeout_spin.setFixedSize(100, 36)
        self.timeout_spin.setSuffix(" min")
        self.timeout_spin.setStyleSheet(f"""
            QSpinBox {{
                background-color: {Theme.SURFACE};
                color: {Theme.TEXT_PRIMARY};
                border: 1px solid #CBD5E1;
                border-radius: 6px;
                padding: 8px;
                font-size: 13px;
            }}
            QSpinBox:hover {{
                border: 1px solid {Theme.PRIMARY};
            }}
            QSpinBox:focus {{
                border: 2px solid {Theme.PRIMARY};
            }}
        """)
        self.timeout_spin.valueChanged.connect(self.inactivity_timeout_changed.emit)
        logout_row.addWidget(self.timeout_spin, alignment=Qt.AlignVCenter)
        
        security_layout.addLayout(logout_row)

        content_layout.addWidget(security_card)

        # 4. Legal & Privacy Card (Replaced the old Preferences card)
        legal_card = self.create_card()
        legal_layout = QVBoxLayout(legal_card)
        legal_layout.setContentsMargins(30, 30, 30, 30)
        legal_layout.setSpacing(20)

        legal_title = QLabel("Legal & Privacy")
        legal_title.setWordWrap(True)
        legal_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.TEXT_PRIMARY}; margin-bottom: 10px;")
        legal_layout.addWidget(legal_title)

        # License Information Row
        license_row = QHBoxLayout()
        license_row.setSpacing(15)
        
        license_icon = QLabel("📜")
        license_icon.setStyleSheet("font-size: 32px;")
        license_row.addWidget(license_icon)
        
        license_info = QVBoxLayout()
        license_info.setSpacing(5)
        
        license_label = QLabel("License Information")
        license_label.setWordWrap(True)
        license_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        license_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {Theme.TEXT_PRIMARY};")
        
        license_desc = QLabel("Commercial License: Solo Practice Edition")
        license_desc.setWordWrap(True)
        license_desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        license_desc.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        
        license_info.addWidget(license_label)
        license_info.addWidget(license_desc)
        
        license_row.addLayout(license_info, 1)
        
        view_license_btn = QPushButton("View License")
        view_license_btn.setCursor(Qt.PointingHandCursor)
        view_license_btn.setMinimumWidth(120)
        view_license_btn.setFixedHeight(36)
        view_license_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SURFACE};
                color: {Theme.PRIMARY};
                border: 1px solid {Theme.PRIMARY};
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #F8FAFC;
            }}
        """)
        view_license_btn.clicked.connect(self.view_license)
        license_row.addWidget(view_license_btn, alignment=Qt.AlignVCenter)
        
        legal_layout.addLayout(license_row)
        
        # Divider
        divider_legal = QFrame()
        divider_legal.setFrameShape(QFrame.HLine)
        divider_legal.setStyleSheet("background-color: #E2E8F0; max-height: 1px;")
        legal_layout.addWidget(divider_legal)

        # Privacy Policy Row
        privacy_row = QHBoxLayout()
        privacy_row.setSpacing(15)
        
        privacy_icon = QLabel("🔒")
        privacy_icon.setStyleSheet("font-size: 32px;")
        privacy_row.addWidget(privacy_icon)
        
        privacy_info = QVBoxLayout()
        privacy_info.setSpacing(5)
        
        privacy_label = QLabel("Privacy Policy")
        privacy_label.setWordWrap(True)
        privacy_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        privacy_label.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {Theme.TEXT_PRIMARY};")
        
        privacy_desc = QLabel("Review data ownership and on-premise storage policies")
        privacy_desc.setWordWrap(True)
        privacy_desc.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        privacy_desc.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")
        
        privacy_info.addWidget(privacy_label)
        privacy_info.addWidget(privacy_desc)
        
        privacy_row.addLayout(privacy_info, 1)
        
        view_policy_btn = QPushButton("View Policy")
        view_policy_btn.setCursor(Qt.PointingHandCursor)
        view_policy_btn.setMinimumWidth(120)
        view_policy_btn.setFixedHeight(36)
        view_policy_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.SURFACE};
                color: {Theme.PRIMARY};
                border: 1px solid {Theme.PRIMARY};
                border-radius: 6px;
                font-weight: 600;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: #F8FAFC;
            }}
        """)
        view_policy_btn.clicked.connect(self.view_privacy_policy)
        privacy_row.addWidget(view_policy_btn, alignment=Qt.AlignVCenter)
        
        legal_layout.addLayout(privacy_row)

        content_layout.addWidget(legal_card)

        # 5. About Section
        about_card = self.create_card()
        about_layout = QVBoxLayout(about_card)
        about_layout.setContentsMargins(30, 25, 30, 25)
        about_layout.setSpacing(10)
        # No layout-level AlignCenter: it sizes every item to one narrow width,
        # which wrapped these labels and clipped them. Each label centres its
        # own text instead.

        from utils.helpers import resource_path
        from PySide6.QtGui import QPixmap
        logo_path = resource_path("app_icon.png")
        if os.path.exists(logo_path):
            about_logo = QLabel()
            pix = QPixmap(logo_path).scaled(56, 56, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            about_logo.setPixmap(pix)
            about_logo.setAlignment(Qt.AlignCenter)
            about_layout.addWidget(about_logo)

        version_label = QLabel("DigiSpher EMR System")
        version_label.setWordWrap(True)
        version_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {Theme.TEXT_PRIMARY};")
        about_layout.addWidget(version_label)
        
        version_num = QLabel("Version 2.0.0 (Solopreneur Edition)")
        version_num.setWordWrap(True)
        version_num.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        version_num.setAlignment(Qt.AlignCenter)
        version_num.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {Theme.PRIMARY};")
        about_layout.addWidget(version_num)
        
        copyright_label = QLabel("© 2026 DigiSpher EMR Systems • All Rights Reserved")
        copyright_label.setWordWrap(True)
        copyright_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        copyright_label.setAlignment(Qt.AlignCenter)
        copyright_label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY};")
        about_layout.addWidget(copyright_label)

        content_layout.addWidget(about_card)

        content_layout.addStretch()

        self.refresh_clinic_card()

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def create_card(self):
        card = QFrame()
        card.setObjectName("card")
        # Scoped to #card on purpose: a bare `QFrame` selector also matches every
        # child QLabel (QLabel derives from QFrame), which drew a bordered box
        # around each label and hid the card surface.
        card.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Theme.SURFACE};
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }}
            QFrame#card QLabel {{
                background: transparent;
            }}
        """)
        return card

    def backup_database(self):
        # Generate default filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"clinic_backup_{timestamp}.db"

        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            tr("Save Database Backup"), 
            default_name, 
            tr("SQLite Database (*.db)")
        )

        if file_path:
            try:
                if db_manager.backup_database(file_path):
                    QMessageBox.information(self, "Success", f"Database backup created successfully at:\n{file_path}")
                else:
                    QMessageBox.critical(self, "Error", "Database backup failed. Check the application log for details.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create backup: {str(e)}")

    def open_clinic_edit_dialog(self):
        dialog = ClinicInfoEditDialog(self)
        if dialog.exec():
            self.refresh_clinic_card()
            QMessageBox.information(self, "Success", "Clinic information updated successfully!")

    def refresh_clinic_card(self):
        """Show the live clinic name plus its currency and tax rate."""
        clinic = db_manager.get_clinic_info()
        if not clinic:
            return
        code, symbol, _ = currency.clinic_currency(clinic)
        tax = float(clinic['tax_rate'] or 0.0)
        self.clinic_name_label.setText(clinic['clinic_name'] or tr("Clinic Information"))
        self.clinic_desc_label.setText(
            tr("License") + f": {clinic['license_number'] or '—'}"
            f"   ·   {tr('Currency')}: {code} ({symbol})"
            f"   ·   {tr('Tax Rate')}: {tax:g}%"
        )

    def view_privacy_policy(self):
        dialog = PrivacyPolicyDialog(self)
        dialog.exec()

    def view_license(self):
        dialog = LicenseDialog(self)
        dialog.exec()


class ClinicInfoEditDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Clinic Information")
        self.resize(500, 640)
        self.setMinimumSize(420, 480)
        self.setStyleSheet(Theme.STYLESHEET)
        
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)

        title = QLabel("Edit Clinic Details")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.PRIMARY}; margin-bottom: 10px;")
        layout.addWidget(title)

        form_layout = QFormLayout()
        form_layout.setSpacing(15)
        
        self.clinic_name = QLineEdit()
        self.clinic_name.setPlaceholderText("e.g. City Medical Center")
        
        self.clinic_address = QLineEdit()
        self.clinic_address.setPlaceholderText("e.g. 123 Main Street, City, State")
        
        self.license_number = QLineEdit()
        self.license_number.setPlaceholderText("e.g. MED-12345")

        form_layout.addRow("Clinic Name:", self.clinic_name)
        form_layout.addRow("Clinic Address:", self.clinic_address)
        form_layout.addRow("License Number:", self.license_number)

        # --- Currency & tax -------------------------------------------------
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #E2E8F0; border: none;")
        layout.addSpacing(6)
        layout.addWidget(sep)
        layout.addSpacing(6)

        self.currency_combo = QComboBox()
        self.currency_combo.setEditable(True)   # allow a custom ISO code
        self.currency_combo.setInsertPolicy(QComboBox.NoInsert)
        # No fixed width: the long "XXX - Currency Name (SYM)" labels would
        # otherwise set a dialog minimum wider than a small screen. The combo
        # elides its text and the chosen code is shown in Settings.
        self.currency_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.currency_combo.setMinimumWidth(160)
        for code in currency.sorted_codes():
            self.currency_combo.addItem(currency.label_for(code), code)
        self.currency_combo.currentIndexChanged.connect(self._sync_currency_fields)

        self.currency_symbol = QLineEdit()
        self.currency_symbol.setMaximumWidth(90)
        self.currency_symbol.setPlaceholderText("$")

        position_row = QHBoxLayout()
        self.position_combo = QComboBox()
        self.position_combo.addItem(tr("Before"), "before")
        self.position_combo.addItem(tr("After"), "after")
        # Short labels: the long examples set a minimum width that pushed this
        # dialog past narrow screens. The examples live in the tooltips.
        self.position_combo.setToolTip(
            tr("Before amount: $1,234.56    After amount: 1,234.56 $"))
        self.position_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        self.position_combo.setMinimumWidth(110)
        position_row.addWidget(self.position_combo)
        position_row.addStretch()

        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0.0, 100.0)
        self.tax_rate.setDecimals(2)
        self.tax_rate.setSuffix(" %")
        self.tax_rate.setMaximumWidth(110)

        form_layout.addRow(tr("Currency:"), self.currency_combo)
        form_layout.addRow(tr("Symbol:"), self.currency_symbol)
        form_layout.addRow(tr("Symbol Position:"), position_row)
        form_layout.addRow(tr("Default Tax Rate:"), self.tax_rate)

        currency_note = QLabel(tr("Invoices keep the currency they were issued in, so changing this later does not rewrite past invoices."))
        currency_note.setWordWrap(True)
        currency_note.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        currency_note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; background: transparent;")

        layout.addLayout(form_layout)
        layout.addSpacing(6)
        layout.addWidget(currency_note)
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

    def _sync_currency_fields(self):
        """Auto-fill symbol/position when a known currency code is selected.

        A hand-typed custom code is left alone so it keeps its own symbol.
        """
        code = (self.currency_combo.currentData() or "").upper()
        if not currency.is_known(code):
            typed = self.currency_combo.currentText().strip().upper()
            if currency.is_known(typed):
                code = typed
        if currency.is_known(code):
            self.currency_symbol.setText(currency.symbol_for(code))
            idx = self.position_combo.findData(currency.position_for(code))
            if idx >= 0:
                self.position_combo.setCurrentIndex(idx)

    def load_data(self):
        clinic = db_manager.get_clinic_info()
        if clinic:
            self.clinic_name.setText(clinic['clinic_name'] or "")
            self.clinic_address.setText(clinic['clinic_address'] or "")
            self.license_number.setText(clinic['license_number'] or "")

        code, symbol, position = currency.clinic_currency(clinic)
        idx = self.currency_combo.findData(code)
        if idx >= 0:
            self.currency_combo.setCurrentIndex(idx)
        else:
            self.currency_combo.setCurrentText(code)
        self.currency_symbol.setText(symbol)
        pos_idx = self.position_combo.findData(position)
        if pos_idx >= 0:
            self.position_combo.setCurrentIndex(pos_idx)
        if clinic and clinic['tax_rate'] is not None:
            self.tax_rate.setValue(float(clinic['tax_rate']))

    def save_changes(self):
        clinic_name = self.clinic_name.text().strip()
        clinic_address = self.clinic_address.text().strip()
        license_number = self.license_number.text().strip()

        if not clinic_name:
            QMessageBox.warning(self, "Error", "Clinic name cannot be empty")
            return

        if not clinic_address:
            QMessageBox.warning(self, "Error", "Clinic address cannot be empty")
            return

        if not license_number:
            QMessageBox.warning(self, "Error", "License number cannot be empty")
            return

        code = (self.currency_combo.currentData() or self.currency_combo.currentText()).strip().upper()
        if not code:
            QMessageBox.warning(self, "Error", "Please choose a currency")
            return
        if len(code) != 3 or not code.isalpha():
            QMessageBox.warning(self, "Error", "Currency code must be 3 letters, e.g. USD, EUR, MAD")
            return

        symbol = self.currency_symbol.text().strip()
        if not symbol:
            symbol = currency.symbol_for(code)

        success, message = db_manager.save_clinic_info(
            clinic_name,
            clinic_address,
            license_number,
            tax_rate=self.tax_rate.value(),
            currency_symbol=symbol,
            currency_code=code,
            currency_position=self.position_combo.currentData() or "before",
        )
        
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to update clinic info: {message}")


class PrivacyPolicyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Privacy Policy & Data Responsibility")
        self.resize(800, 600)
        self.setStyleSheet(Theme.STYLESHEET)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header with professional look (text only, similar to doc note)
        header_container = QFrame()
        header_container.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 2px solid {Theme.PRIMARY};
                padding: 24px;
            }}
        """)
        header_layout = QVBoxLayout(header_container)
        
        title_label = QLabel("Privacy Policy and Terms")
        title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {Theme.PRIMARY};")
        
        subtitle_label = QLabel("Data Responsibility Agreement")
        subtitle_label.setStyleSheet("font-size: 14px; color: #64748B; margin-top: 4px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_container)

        # Content Area
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: #F8FAFC;
                padding: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #334155;
            }
        """)
        
        # HTML Content
        html_content = f"""
        <html>
        <head>
            <style>
                h2 {{ color: {Theme.TEXT_PRIMARY}; font-size: 18px; margin-top: 20px; margin-bottom: 10px; }}
                p {{ margin-bottom: 15px; }}
                .highlight {{ background-color: #FEF3C7; padding: 2px 5px; border-radius: 4px; color: #92400E; font-weight: bold; }}
                ul {{ margin-bottom: 15px; }}
                li {{ margin-bottom: 5px; }}
                .footer {{ margin-top: 40px; font-size: 12px; color: #94A3B8; border-top: 1px solid #E2E8F0; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <h2>1. On-Premise Software Declaration</h2>
            <p>DigiSpher EMR is strictly an <span class="highlight">On-Premise Software Solution</span>. This means that the software and all associated data are installed, stored, and processed locally on your own hardware infrastructure.</p>
            
            <h2>2. Data Ownership and Storage</h2>
            <p>Unlike cloud-based solutions, DigiSpher EMR does NOT store, transmit, or back up your data to any external cloud servers. All patient records, clinical notes, and medical history are stored in a local SQLite database file located on this machine.</p>
            
            <h2>3. User Responsibility</h2>
            <p>As the user and administrator of this software installation, you acknowledge and agree that:</p>
            <ul>
                <li><strong>Data Security:</strong> You are solely responsible for securing physical and digital access to the computer running this software.</li>
                <li><strong>Backups:</strong> You are responsible for creating regular backups of your database. A backup tool is provided in the Settings menu, but you must initiate it.</li>
                <li><strong>Loss Prevention:</strong> DigiSpher EMR Systems cannot recover lost data due to hardware failure, theft, or accidental deletion, as we do not have a copy of your data.</li>
            </ul>

            <h2>4. Compliance</h2>
            <p>You are responsible for ensuring that your use of this software and storage of patient data complies with all applicable local, state, and federal privacy regulations (e.g., HIPAA, GDPR). This includes ensuring that the device hosting this data is encrypted and password-protected.</p>

            <div class="footer">
                Last Updated: {datetime.now().strftime('%B %d, %Y')} | DigiSpher EMR Systems
            </div>
        </body>
        </html>
        """
        self.text_view.setHtml(privacy_html() if manager().locale == "fr" else html_content)
        manager().changed.connect(
            lambda locale: self.text_view.setHtml(privacy_html() if locale == "fr" else html_content)
        )
        layout.addWidget(self.text_view)

        # Footer Button
        footer = QFrame()
        footer.setStyleSheet("background: white; border-top: 1px solid #E2E8F0; padding: 16px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.addStretch()
        
        close_btn = QPushButton("I Understand")
        close_btn.setFixedSize(140, 40)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addWidget(footer)


class LicenseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Commercial License Agreement")
        self.resize(800, 600)
        self.setStyleSheet(Theme.STYLESHEET)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header_container = QFrame()
        header_container.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 2px solid {Theme.PRIMARY};
                padding: 24px;
            }}
        """)
        header_layout = QVBoxLayout(header_container)
        
        title_label = QLabel("Commercial License")
        title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {Theme.PRIMARY};")
        
        subtitle_label = QLabel("Solo Practice Edition - Terms of Use")
        subtitle_label.setStyleSheet("font-size: 14px; color: #64748B; margin-top: 4px;")
        
        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        layout.addWidget(header_container)

        # Content Area
        self.text_view = QTextEdit()
        self.text_view.setReadOnly(True)
        self.text_view.setStyleSheet("""
            QTextEdit {
                border: none;
                background-color: #F8FAFC;
                padding: 30px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                color: #334155;
            }
        """)
        
        # HTML Content
        html_content = f"""
        <html>
        <head>
            <style>
                h2 {{ color: {Theme.TEXT_PRIMARY}; font-size: 18px; margin-top: 20px; margin-bottom: 10px; }}
                p {{ margin-bottom: 15px; }}
                .highlight {{ background-color: #FEE2E2; padding: 2px 5px; border-radius: 4px; color: #991B1B; font-weight: bold; }}
                ul {{ margin-bottom: 15px; }}
                li {{ margin-bottom: 8px; }}
                .warning-box {{ background-color: #FEF2F2; border-left: 4px solid #EF4444; padding: 15px; margin: 20px 0; color: #7F1D1D; }}
                .footer {{ margin-top: 40px; font-size: 12px; color: #94A3B8; border-top: 1px solid #E2E8F0; padding-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="warning-box">
                <strong>IMPORTANT LEGAL NOTICE:</strong> This software is licensed, not sold. By using this software, you agree to the terms below.
            </div>

            <h2>1. Grant of License</h2>
            <p>DigiSpher EMR Systems grants you a revocable, non-exclusive, non-transferable, limited license to use the DigiSpher EMR software strictly in accordance with the terms of this agreement.</p>
            
            <h2>2. License Type: Commercial Solo Practice</h2>
            <p>This license is expressly designated as a <span class="highlight">Solo Practice Commercial License</span>. It is authorized for use by a single (1) medical practitioner or provider only.</p>
            
            <h2>3. Installation and Usage Restrictions</h2>
            <ul>
                <li><strong>Single Machine:</strong> This license permits installation and operation on exactly <span class="highlight">ONE (1) physical machine</span> or workstation.</li>
                <li><strong>No Network Sharing:</strong> You may not install this software on a server for access by multiple workstations or users.</li>
                <li><strong>Non-Transferable:</strong> You may not rent, lease, lend, sell, redistribute, or sublicense this software.</li>
            </ul>

            <h2>4. Unauthorized Sharing and Legal Consequences</h2>
            <p>Any distribution, copying, or sharing of this software to other practitioners, clinics, or third parties is a direct violation of this agreement and international copyright laws.</p>
            <p><strong>Warning:</strong> Unauthorized use or distribution will result in immediate termination of this license and may subject you to <span class="highlight">civil and criminal penalties</span>, including monetary damages for copyright infringement.</p>

            <h2>5. Limit of Liability</h2>
            <p>DigiSpher EMR Systems shall not be liable for any damages (including, without limitation, lost profits, business interruption, or lost information) rising out of 'Authorized Users' use of or inability to use this product.</p>

            <div class="footer">
                License ID: SPEC-2024-SOLO-001 | © 2024 DigiSpher EMR Systems
            </div>
        </body>
        </html>
        """
        self.text_view.setHtml(LICENSE if manager().locale == "fr" else html_content)
        manager().changed.connect(
            lambda locale: self.text_view.setHtml(LICENSE if locale == "fr" else html_content)
        )
        layout.addWidget(self.text_view)

        # Footer Button
        footer = QFrame()
        footer.setStyleSheet("background: white; border-top: 1px solid #E2E8F0; padding: 16px;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.addStretch()
        
        close_btn = QPushButton("I Agree")
        close_btn.setFixedSize(140, 40)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                font-weight: bold;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        close_btn.clicked.connect(self.accept)
        footer_layout.addWidget(close_btn)
        
        layout.addWidget(footer)
