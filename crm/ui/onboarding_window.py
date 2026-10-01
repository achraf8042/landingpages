
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QLineEdit, 
                               QPushButton, QFrame, QMessageBox, QTextEdit, QComboBox, QHBoxLayout,
                               QScrollArea, QDoubleSpinBox)
from PySide6.QtCore import Qt, Signal
import os
from PySide6.QtGui import QFont, QIcon, QPixmap
from styles.theme import Theme
from data import db_manager
from utils.helpers import resource_path
from utils import currency
from utils.localization import manager, tr

class OnboardingWindow(QWidget):
    onboarding_complete = Signal()  # Signal to emit when onboarding is successful

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DigiSpher EMR - Clinic Setup")
        self.setWindowIcon(QIcon(resource_path("app_icon.ico")))
        # Sized to fit a 1366x768 laptop without the title bar clipping.
        self.resize(560, 740)
        self.setMinimumSize(540, 600)
        self.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        
        self.setup_ui()

    def setup_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignCenter)

        # Onboarding Card
        card = QFrame()
        card.setObjectName("onboardingCard")
        # Fixed width, flexible height: the fields scroll, so the card can grow
        # with the content instead of clipping the Save button.
        card.setFixedWidth(496)
        card.setMinimumHeight(560)
        card.setMaximumHeight(900)
        card.setStyleSheet(f"""
            QFrame#onboardingCard {{
                background-color: {Theme.SURFACE};
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }}
            QFrame#onboardingCard QLabel {{
                background: transparent;
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
        card_layout.setContentsMargins(32, 26, 32, 26)
        card_layout.setSpacing(10)

        # Title
        title = QLabel("Welcome to DigiSpher EMR")
        title.setAlignment(Qt.AlignCenter)
        title.setWordWrap(True)
        title.setStyleSheet(f"font-size: 26px; font-weight: bold; color: {Theme.PRIMARY};")
        
        subtitle = QLabel("Clinic Information Setup")
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet(f"font-size: 15px; color: {Theme.TEXT_SECONDARY};")

        info_label = QLabel("Please complete the required compliance information before accessing the system.")
        info_label.setWordWrap(True)
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY};")
        language_row = QHBoxLayout()
        language_label = QLabel("Language")
        language_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        self.language_combo = QComboBox()
        self.language_combo.addItem("English", "en")
        self.language_combo.addItem("Français", "fr")
        self.language_combo.setCurrentIndex(0 if manager().locale == "en" else 1)
        self.language_combo.setMinimumHeight(36)
        self.language_combo.currentIndexChanged.connect(
            lambda index: manager().set_locale(self.language_combo.itemData(index))
        )
        language_row.addWidget(language_label)
        language_row.addWidget(self.language_combo)

        # Input Fields
        # Clinic Name
        clinic_name_label = QLabel("Clinic Name *")
        clinic_name_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        self.clinic_name_input = QLineEdit()
        self.clinic_name_input.setPlaceholderText("Enter clinic name")
        self.clinic_name_input.setMinimumHeight(38)
        
        # Clinic Address
        clinic_address_label = QLabel("Clinic Address *")
        clinic_address_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        self.clinic_address_input = QTextEdit()
        self.clinic_address_input.setPlaceholderText("Enter complete clinic address")
        self.clinic_address_input.setMinimumHeight(70)
        self.clinic_address_input.setMaximumHeight(70)
        
        # License Number
        license_label = QLabel("License Number *")
        license_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        self.license_input = QLineEdit()
        self.license_input.setPlaceholderText("Enter license number")
        self.license_input.setMinimumHeight(38)

        # --- Currency & tax -------------------------------------------------
        # Without this, a fresh install silently starts on USD / $ / 0% tax and
        # the doctor has to hunt through Settings to correct their money.
        self.currency_combo = QComboBox()
        self.currency_combo.setEditable(True)          # allow a custom ISO code
        self.currency_combo.setInsertPolicy(QComboBox.NoInsert)
        for code in currency.sorted_codes():
            self.currency_combo.addItem(currency.label_for(code), code)
        # Sensible starting guess from the chosen UI language; still one click to change.
        self.currency_combo.setCurrentIndex(
            self.currency_combo.findData("EUR" if manager().locale == "fr" else "USD"))
        self.currency_combo.currentIndexChanged.connect(self._sync_currency_fields)
        self.currency_combo.setMinimumHeight(36)

        self.currency_symbol = QLineEdit()
        self.currency_symbol.setMaximumWidth(90)
        self.currency_symbol.setMinimumHeight(36)
        self._sync_currency_fields()

        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0.0, 100.0)
        self.tax_rate.setDecimals(2)
        self.tax_rate.setSuffix(" %")
        self.tax_rate.setMinimumHeight(36)
        self.tax_rate.setMaximumWidth(110)

        # Save Button
        save_btn = QPushButton("Save & Continue")
        save_btn.setMinimumHeight(38)
        save_btn.setCursor(Qt.PointingHandCursor)
        save_btn.setStyleSheet(f"""
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
        save_btn.clicked.connect(self.handle_save)

        # Add widgets to card. The fields live in a scroll area so the currency
        # and tax inputs do not push the Save button off a short screen; the
        # title and the button itself stay pinned.
        card_layout.addWidget(title)
        card_layout.addWidget(subtitle)
        card_layout.addWidget(info_label)

        fields = QWidget()
        fields_layout = QVBoxLayout(fields)
        fields_layout.setContentsMargins(0, 0, 0, 0)
        fields_layout.setSpacing(7)

        fields_layout.addLayout(language_row)
        fields_layout.addWidget(clinic_name_label)
        fields_layout.addWidget(self.clinic_name_input)
        fields_layout.addWidget(clinic_address_label)
        fields_layout.addWidget(self.clinic_address_input)
        fields_layout.addWidget(license_label)
        fields_layout.addWidget(self.license_input)

        money_sep = QFrame()
        money_sep.setFixedHeight(1)
        money_sep.setStyleSheet("background-color: #E2E8F0; border: none;")
        fields_layout.addSpacing(4)
        fields_layout.addWidget(money_sep)
        fields_layout.addSpacing(2)

        money_label = QLabel(tr("Currency & Tax"))
        money_label.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        fields_layout.addWidget(money_label)

        currency_row = QHBoxLayout()
        currency_row.setSpacing(10)
        currency_row.addWidget(self.currency_combo, 1)
        currency_row.addWidget(QLabel(tr("Symbol")))
        currency_row.addWidget(self.currency_symbol)
        fields_layout.addLayout(currency_row)

        tax_row = QHBoxLayout()
        tax_row.setSpacing(10)
        tax_row.addWidget(QLabel(tr("Default Tax Rate")))
        tax_row.addWidget(self.tax_rate)
        tax_row.addStretch()
        fields_layout.addLayout(tax_row)

        money_note = QLabel(tr("Invoices keep the currency they were issued in."))
        money_note.setWordWrap(True)
        money_note.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY};")
        fields_layout.addWidget(money_note)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none; background: #F1F5F9; width: 8px;
                margin: 0px; border-radius: 4px;
            }
            QScrollBar::handle:vertical { background: #CBD5E1; min-height: 24px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        scroll.setWidget(fields)
        card_layout.addWidget(scroll, 1)

        card_layout.addWidget(save_btn)

        # Add card to main layout
        main_layout.addWidget(card)

    def _sync_currency_fields(self):
        """Auto-fill the symbol when a known currency code is selected.

        A hand-typed custom code keeps whatever symbol the doctor entered.
        """
        code = (self.currency_combo.currentData() or "").upper()
        if not currency.is_known(code):
            typed = self.currency_combo.currentText().strip().upper()
            if currency.is_known(typed):
                code = typed
        if currency.is_known(code):
            self.currency_symbol.setText(currency.symbol_for(code))

    def handle_save(self):
        clinic_name = self.clinic_name_input.text().strip()
        clinic_address = self.clinic_address_input.toPlainText().strip()
        license_number = self.license_input.text().strip()

        # Validate inputs
        if not clinic_name:
            QMessageBox.warning(self, "Validation Error", "Please enter the clinic name.")
            self.clinic_name_input.setFocus()
            return
        
        if not clinic_address:
            QMessageBox.warning(self, "Validation Error", "Please enter the clinic address.")
            self.clinic_address_input.setFocus()
            return
        
        if not license_number:
            QMessageBox.warning(self, "Validation Error", "Please enter the license number.")
            self.license_input.setFocus()
            return

        code = (self.currency_combo.currentData() or self.currency_combo.currentText()).strip().upper()
        if not code:
            QMessageBox.warning(self, "Validation Error", "Please choose a currency.")
            self.currency_combo.setFocus()
            return
        if len(code) != 3 or not code.isalpha():
            QMessageBox.warning(self, "Validation Error",
                                "Currency code must be 3 letters, e.g. USD, EUR, MAD")
            self.currency_combo.setFocus()
            return

        symbol = self.currency_symbol.text().strip() or currency.symbol_for(code)

        # Save to database
        try:
            success, message = db_manager.save_clinic_info(
                clinic_name, clinic_address, license_number,
                tax_rate=self.tax_rate.value(),
                currency_symbol=symbol,
                currency_code=code,
            )
            
            if success:
                QMessageBox.information(self, "Success", "Clinic information saved successfully!")
                self.onboarding_complete.emit()
            else:
                QMessageBox.critical(self, "Error", f"Failed to save clinic information: {message}")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
