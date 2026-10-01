from utils.localization import combo_value, tr
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                               QFrame, QGridLayout, QScrollArea, QPushButton, QComboBox, QSizePolicy)
from PySide6.QtCore import Qt, QTimer, Signal
from styles.theme import Theme
from utils import currency
from data import db_manager
from datetime import datetime, date, timedelta

class DashboardView(QWidget):
    # Signals for quick actions and cross-view navigation
    add_patient_requested = Signal()
    new_appointment_requested = Signal()
    new_invoice_requested = Signal()
    new_note_requested = Signal()
    new_prescription_requested = Signal()
    view_notes_requested = Signal()
    view_prescriptions_requested = Signal()
    view_finances_requested = Signal()
    view_patients_requested = Signal()
    view_appointments_requested = Signal()

    def __init__(self):
        super().__init__()
        self.privacy_mode = False
        self.setup_ui()
        self.refresh_data()
        
        # Auto refresh every 30 seconds
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_data)
        self.timer.start(30000)

    def set_privacy_mode(self, enabled):
        self.privacy_mode = enabled
        self.refresh_data()

    def setup_ui(self):
        # Main Layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet(f"""
            QScrollBar:vertical {{
                border: none;
                background: #F1F5F9;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #5B73A7;
                min-height: 24px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #1D4ED8;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
            QScrollBar:horizontal {{
                border: none;
                background: #F1F5F9;
                height: 6px;
                margin: 0px;
                border-radius: 3px;
            }}
            QScrollBar::handle:horizontal {{
                background: #5B73A7;
                min-width: 20px;
                border-radius: 3px;
            }}
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
                width: 0px;
            }}
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
                background: none;
            }}
        """)
        
        # Scroll Content Widget
        scroll_content = QWidget()
        scroll_content.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        
        # Grid Layout
        scroll_layout = QGridLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 20, 24)
        scroll_layout.setSpacing(20)

        # =========================================================================
        # ROW 0: Practice KPI Metrics (5 Responsive Stat Cards)
        # =========================================================================
        self.stats_grid = QGridLayout()
        self.stats_grid.setSpacing(16)
        
        self.total_patients_card = self.create_stat_card("Total Patients", "0", "👥", Theme.PRIMARY)
        self.today_notes_card = self.create_stat_card("Today's Notes", "0", "📝", Theme.SUCCESS)
        self.today_rev_card = self.create_stat_card("Today's Revenue", "0.00", "💵", "#059669")
        self.today_appt_card = self.create_stat_card("Today's Appt", "0", "📅", Theme.WARNING)
        self.week_appt_card = self.create_stat_card("This Week Appt", "0", "🗓️", Theme.PRIMARY_HOVER)
        
        # Row 0: 3 cards
        self.stats_grid.addWidget(self.total_patients_card, 0, 0)
        self.stats_grid.addWidget(self.today_notes_card, 0, 1)
        self.stats_grid.addWidget(self.today_rev_card, 0, 2)
        # Row 1: 2 cards
        self.stats_grid.addWidget(self.today_appt_card, 1, 0)
        self.stats_grid.addWidget(self.week_appt_card, 1, 1, 1, 2)
        
        scroll_layout.addLayout(self.stats_grid, 0, 0, 1, 2)

        # =========================================================================
        # ROW 1: Immediate Operations (Recent Patients & Scheduled Appointments)
        # =========================================================================
        
        # 1. Recent Patients (Column 0)
        activity_frame = QFrame()
        activity_frame.setProperty("class", "card")
        activity_frame.setObjectName("card")
        activity_frame.setMinimumHeight(240)
        activity_frame.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Theme.SURFACE}; 
                border-radius: 16px; 
                border: 1px solid #E2E8F0;
            }}
            QFrame#card QLabel {{
                background: transparent;
            }}
        """)
        activity_layout = QVBoxLayout(activity_frame)
        activity_layout.setContentsMargins(20, 18, 20, 18)
        activity_layout.setSpacing(12)
        
        activity_header = QHBoxLayout()
        activity_title = QLabel("👥 Recent Patients")
        activity_title.setWordWrap(True)
        activity_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        activity_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        view_patients_btn = QPushButton("All Patients →")
        view_patients_btn.setCursor(Qt.PointingHandCursor)
        view_patients_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: none;
                font-weight: 600;
                font-size: 12px;
                padding: 4px 6px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        view_patients_btn.clicked.connect(self.view_patients_requested.emit)
        
        activity_header.addWidget(activity_title)
        activity_header.addStretch()
        activity_header.addWidget(view_patients_btn)
        activity_layout.addLayout(activity_header)
        
        self.activity_list = QVBoxLayout()
        self.activity_list.setAlignment(Qt.AlignTop)
        self.activity_list.setSpacing(8)
        activity_layout.addLayout(self.activity_list)
        activity_layout.addStretch()
        
        scroll_layout.addWidget(activity_frame, 1, 0)

        # 2. Upcoming Appointments (Column 1)
        appt_frame = QFrame()
        appt_frame.setProperty("class", "card")
        appt_frame.setObjectName("card")
        appt_frame.setMinimumHeight(240)
        appt_frame.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Theme.SURFACE}; 
                border-radius: 16px; 
                border: 1px solid #E2E8F0;
            }}
            QFrame#card QLabel {{
                background: transparent;
            }}
        """)
        appt_layout = QVBoxLayout(appt_frame)
        appt_layout.setContentsMargins(20, 18, 20, 18)
        appt_layout.setSpacing(12)
        
        top_header = QHBoxLayout()
        appt_title = QLabel("📅 Scheduled Consultations")
        appt_title.setWordWrap(True)
        appt_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        appt_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")

        self.appt_filter = QComboBox()
        self.appt_filter.addItems(["Today", "This Week", "This Month"])
        self.appt_filter.setFixedWidth(115)
        self.appt_filter.currentIndexChanged.connect(self.refresh_data)

        view_appts_btn = QPushButton("All Appts →")
        view_appts_btn.setCursor(Qt.PointingHandCursor)
        view_appts_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: none;
                font-weight: 600;
                font-size: 12px;
                padding: 4px 6px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        view_appts_btn.clicked.connect(self.view_appointments_requested.emit)

        top_header.addWidget(appt_title)
        top_header.addStretch()
        top_header.addWidget(self.appt_filter)
        top_header.addWidget(view_appts_btn)
        appt_layout.addLayout(top_header)
        
        self.appt_list = QVBoxLayout()
        self.appt_list.setAlignment(Qt.AlignTop)
        self.appt_list.setSpacing(8)
        appt_layout.addLayout(self.appt_list)
        appt_layout.addStretch()

        scroll_layout.addWidget(appt_frame, 1, 1)

        # =========================================================================
        # ROW 2: Deep Practice Workflow (Clinical Activity & Invoices/Cash Flow)
        # =========================================================================
        
        # 3. Clinical Activity & Notes (Column 0)
        clinical_frame = QFrame()
        clinical_frame.setProperty("class", "card")
        clinical_frame.setObjectName("card")
        clinical_frame.setMinimumHeight(240)
        clinical_frame.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Theme.SURFACE}; 
                border-radius: 16px; 
                border: 1px solid #E2E8F0;
            }}
            QFrame#card QLabel {{
                background: transparent;
            }}
        """)
        clinical_layout = QVBoxLayout(clinical_frame)
        clinical_layout.setContentsMargins(20, 18, 20, 18)
        clinical_layout.setSpacing(12)

        clinical_header = QHBoxLayout()
        clinical_title = QLabel("📋 Clinical Activity & Notes")
        clinical_title.setWordWrap(True)
        clinical_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        clinical_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")

        clinical_btn_note = QPushButton("+ Note")
        clinical_btn_note.setCursor(Qt.PointingHandCursor)
        clinical_btn_note.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        clinical_btn_note.clicked.connect(self.new_note_requested.emit)

        clinical_btn_rx = QPushButton("+ Rx")
        clinical_btn_rx.setCursor(Qt.PointingHandCursor)
        clinical_btn_rx.setStyleSheet("""
            QPushButton {
                background-color: #7C3AED;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #6D28D9;
            }
        """)
        clinical_btn_rx.clicked.connect(self.new_prescription_requested.emit)

        view_notes_btn = QPushButton("All Notes →")
        view_notes_btn.setCursor(Qt.PointingHandCursor)
        view_notes_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: none;
                padding: 4px 6px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        view_notes_btn.clicked.connect(self.view_notes_requested.emit)

        clinical_header.addWidget(clinical_title)
        clinical_header.addStretch()
        clinical_header.addWidget(clinical_btn_note)
        clinical_header.addWidget(clinical_btn_rx)
        clinical_header.addWidget(view_notes_btn)
        clinical_layout.addLayout(clinical_header)

        self.clinical_list = QVBoxLayout()
        self.clinical_list.setAlignment(Qt.AlignTop)
        self.clinical_list.setSpacing(8)
        clinical_layout.addLayout(self.clinical_list)
        clinical_layout.addStretch()

        scroll_layout.addWidget(clinical_frame, 2, 0)

        # 4. Recent Invoices & Billing (Column 1)
        billing_frame = QFrame()
        billing_frame.setProperty("class", "card")
        billing_frame.setObjectName("card")
        billing_frame.setMinimumHeight(240)
        billing_frame.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Theme.SURFACE}; 
                border-radius: 16px; 
                border: 1px solid #E2E8F0;
            }}
            QFrame#card QLabel {{
                background: transparent;
            }}
        """)
        billing_layout = QVBoxLayout(billing_frame)
        billing_layout.setContentsMargins(20, 18, 20, 18)
        billing_layout.setSpacing(12)

        billing_header = QHBoxLayout()
        billing_title = QLabel("💳 Recent Invoices & Billing")
        billing_title.setWordWrap(True)
        billing_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        billing_title.setStyleSheet(f"font-size: 17px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")

        add_inv_btn = QPushButton("+ Invoice")
        add_inv_btn.setCursor(Qt.PointingHandCursor)
        add_inv_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #059669;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 4px 10px;
                font-weight: 600;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: #047857;
            }}
        """)
        add_inv_btn.clicked.connect(self.new_invoice_requested.emit)

        view_finances_btn = QPushButton("Finances →")
        view_finances_btn.setCursor(Qt.PointingHandCursor)
        view_finances_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {Theme.PRIMARY};
                border: none;
                padding: 4px 6px;
                font-weight: 600;
                font-size: 12px;
            }}
            QPushButton:hover {{
                text-decoration: underline;
            }}
        """)
        view_finances_btn.clicked.connect(self.view_finances_requested.emit)

        billing_header.addWidget(billing_title)
        billing_header.addStretch()
        billing_header.addWidget(add_inv_btn)
        billing_header.addWidget(view_finances_btn)
        billing_layout.addLayout(billing_header)

        self.billing_list = QVBoxLayout()
        self.billing_list.setAlignment(Qt.AlignTop)
        self.billing_list.setSpacing(8)
        billing_layout.addLayout(self.billing_list)
        billing_layout.addStretch()

        scroll_layout.addWidget(billing_frame, 2, 1)

        # =========================================================================
        # ROW 3: Solopreneur Practice Command Dock (Quick Action Hub)
        # =========================================================================
        dock_frame = QFrame()
        dock_frame.setProperty("class", "card")
        dock_frame.setObjectName("card")
        dock_frame.setStyleSheet(f"""
            QFrame#card {{
                background-color: {Theme.SURFACE}; 
                border-radius: 16px; 
                border: 1px solid #E2E8F0;
            }}
            QFrame#card QLabel {{
                background: transparent;
            }}
        """)
        dock_layout = QVBoxLayout(dock_frame)
        dock_layout.setContentsMargins(22, 18, 22, 20)
        dock_layout.setSpacing(14)

        dock_header = QHBoxLayout()
        dock_title = QLabel("⚡ Practice Quick Actions & Shortcuts")
        dock_title.setWordWrap(True)
        dock_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        dock_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        dock_sub = QLabel("One-click shortcuts to frequent clinical and financial workflows")
        dock_sub.setWordWrap(True)
        dock_sub.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        dock_sub.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY}; margin-left: 8px;")
        
        dock_header.addWidget(dock_title)
        dock_header.addWidget(dock_sub)
        dock_header.addStretch()
        dock_layout.addLayout(dock_header)

        actions_grid = QGridLayout()
        actions_grid.setSpacing(12)

        # 6 Styled Action Cards
        action_defs = [
            ("👤", "+ New Patient", "Register chart & vitals", Theme.PRIMARY, self.add_patient_requested),
            ("📅", "+ Book Visit", "Schedule appointment", "#D97706", self.new_appointment_requested),
            ("📝", "+ Clinical Note", "Document SOAP consult", "#059669", self.new_note_requested),
            ("💊", "+ Prescribe Rx", "Multi-medication Rx", "#7C3AED", self.new_prescription_requested),
            ("💳", "+ Issue Invoice", "Create bill & receipt", "#0D9488", self.new_invoice_requested),
            ("📊", "Practice Finances", "Revenue, P&L & CSV", "#475569", self.view_finances_requested),
        ]

        for i, (icon, title, desc, color, signal) in enumerate(action_defs):
            btn = self.create_dock_action_button(icon, title, desc, color, signal)
            actions_grid.addWidget(btn, i // 3, i % 3)

        dock_layout.addLayout(actions_grid)
        scroll_layout.addWidget(dock_frame, 3, 0, 1, 2)

        self._responsive_grid = scroll_layout
        self._responsive_cards = (activity_frame, appt_frame, clinical_frame, billing_frame, dock_frame)
        self._card_columns = 2

        # Set Scroll Widget
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if not hasattr(self, "_responsive_cards"):
            return
        columns = 1 if self.width() < 850 else 2
        if columns == self._card_columns:
            return
        self._card_columns = columns
        for card in self._responsive_cards:
            self._responsive_grid.removeWidget(card)
        if columns == 1:
            for row, card in enumerate(self._responsive_cards, 1):
                self._responsive_grid.addWidget(card, row, 0, 1, 2)
        else:
            for index, card in enumerate(self._responsive_cards[:-1]):
                self._responsive_grid.addWidget(card, 1 + index // 2, index % 2)
            self._responsive_grid.addWidget(self._responsive_cards[-1], 3, 0, 1, 2)

    def create_stat_card(self, title, value, icon, color):
        card = QFrame()
        card.setObjectName("statCard")
        card.setStyleSheet(f"""
            QFrame#statCard {{
                background-color: {Theme.SURFACE};
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                border-left: 4px solid {color};
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)
        
        header = QHBoxLayout()
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        # Preferred (not Ignored): Ignored discards the size hint and let the
        # sibling stretch collapse the title to zero width, clipping the text.
        title_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # `background: transparent` is required: a stylesheet sets
        # WA_StyledBackground, which makes Qt fill the label with
        # QPalette.Window (#F8FAFC) instead of showing the white card beneath.
        title_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; background: transparent;")
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 22px; background: transparent;")
        
        header.addWidget(title_lbl, 1)
        header.addWidget(icon_lbl)
        
        value_lbl = QLabel(value)
        value_lbl.setObjectName("value")
        value_lbl.setStyleSheet(f"color: {Theme.TEXT_PRIMARY}; font-size: 26px; font-weight: 800; background: transparent;")
        
        layout.addLayout(header)
        layout.addWidget(value_lbl)
        
        return card

    def create_dock_action_button(self, icon, title, desc, accent_color, signal):
        btn = QPushButton()
        btn.setCursor(Qt.PointingHandCursor)
        # Minimum, not fixed: a fixed height clipped the wrapped description.
        btn.setMinimumHeight(72)
        # Tinted fill from the accent so every action reads as a coloured card
        # instead of white, while keeping dark text readable in both languages.
        fill = Theme.tint(accent_color, 0.90)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {fill};
                border: 1px solid {Theme.tint(accent_color, 0.72)};
                border-left: 5px solid {accent_color};
                border-radius: 10px;
                text-align: left;
                padding: 10px 12px;
            }}
            QPushButton:hover {{
                background-color: {Theme.tint(accent_color, 0.80)};
                border-color: {accent_color};
            }}
            QPushButton QLabel {{
                background: transparent;
            }}
        """)
        
        layout = QHBoxLayout(btn)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(10)
        
        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
        icon_lbl.setAlignment(Qt.AlignTop)
        
        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        text_layout.setAlignment(Qt.AlignVCenter)
        
        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {accent_color}; background: transparent;")
        
        desc_lbl = QLabel(desc)
        desc_lbl.setWordWrap(True)
        desc_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        desc_lbl.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY}; background: transparent;")
        
        text_layout.addWidget(title_lbl)
        text_layout.addWidget(desc_lbl)
        
        layout.addWidget(icon_lbl, 0, Qt.AlignTop)
        # Stretch belongs to the text column; a trailing spacer squeezed the
        # wrapped title/description into a narrow, clipped column.
        layout.addLayout(text_layout, 1)
        
        btn.clicked.connect(signal.emit)
        return btn

    def create_clinical_row(self, item):
        row = QFrame()
        row.setCursor(Qt.PointingHandCursor)
        row.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #F1F5F9;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #F1F5F9;
                border-color: #CBD5E1;
            }
        """)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(12)

        # Type badge
        if item['type'] == 'NOTE':
            badge = QLabel("📝 NOTE")
            badge.setStyleSheet("background-color: #EFF6FF; color: #1D4ED8; font-weight: 700; font-size: 11px; padding: 3px 6px; border-radius: 4px;")
        else:
            badge = QLabel("💊 Rx")
            badge.setStyleSheet("background-color: #F5F3FF; color: #6D28D9; font-weight: 700; font-size: 11px; padding: 3px 6px; border-radius: 4px;")
        layout.addWidget(badge)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        p_name = QLabel(item['patient'])
        p_name.setProperty("i18n_skip", True)
        p_name.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {Theme.TEXT_PRIMARY}; background: transparent;")
        
        detail_snippet = item['detail'][:48] + "..." if len(item['detail']) > 48 else item['detail']
        p_detail = QLabel(detail_snippet)
        p_detail.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY}; background: transparent;")
        
        info_layout.addWidget(p_name)
        info_layout.addWidget(p_detail)
        layout.addLayout(info_layout)
        layout.addStretch()

        # Date
        date_lbl = QLabel(str(item['date']))
        date_lbl.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY}; background: transparent;")
        layout.addWidget(date_lbl)

        # Status badge
        status = (item.get('status') or 'ACTIVE').upper()
        if status in ('FINALIZED', 'COMPLETED'):
            s_lbl = QLabel("DONE")
            s_lbl.setStyleSheet("background-color: #DEF7EC; color: #03543F; font-weight: 700; font-size: 10px; padding: 2px 6px; border-radius: 4px;")
        elif status == 'DRAFT':
            s_lbl = QLabel("DRAFT")
            s_lbl.setStyleSheet("background-color: #FEF3C7; color: #92400E; font-weight: 700; font-size: 10px; padding: 2px 6px; border-radius: 4px;")
        else:
            s_lbl = QLabel("ACTIVE")
            s_lbl.setStyleSheet("background-color: #EFF6FF; color: #1D4ED8; font-weight: 700; font-size: 10px; padding: 2px 6px; border-radius: 4px;")
        layout.addWidget(s_lbl)

        if item['type'] == 'NOTE':
            row.mousePressEvent = lambda e: self.view_notes_requested.emit()
        else:
            row.mousePressEvent = lambda e: self.view_prescriptions_requested.emit()

        return row

    def create_billing_row(self, b):
        clinic_code, clinic_symbol, _ = db_manager.get_clinic_currency()
        row = QFrame()
        row.setCursor(Qt.PointingHandCursor)
        row.setStyleSheet("""
            QFrame {
                background-color: #F8FAFC;
                border: 1px solid #F1F5F9;
                border-radius: 8px;
            }
            QFrame:hover {
                background-color: #F1F5F9;
                border-color: #CBD5E1;
            }
        """)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 9, 12, 9)
        layout.setSpacing(12)

        # Invoice ID
        inv_badge = QLabel(f"#{b['id']:04d}")
        inv_badge.setStyleSheet("font-weight: 700; font-size: 11px; color: #475569; background: #E2E8F0; padding: 3px 6px; border-radius: 4px;")
        layout.addWidget(inv_badge)

        # Patient info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        if self.privacy_mode:
            p_name_str = f"{b['first_name'][0]}. {b['last_name'][0]}."
        else:
            p_name_str = f"{b['first_name']} {b['last_name']}"
        p_name = QLabel(p_name_str)
        p_name.setProperty("i18n_skip", True)
        p_name.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {Theme.TEXT_PRIMARY}; background: transparent;")

        date_str = str(b['created_at'])[:10]
        date_lbl = QLabel(f"Date: {date_str}")
        date_lbl.setStyleSheet(f"font-size: 11px; color: {Theme.TEXT_SECONDARY}; background: transparent;")

        info_layout.addWidget(p_name)
        info_layout.addWidget(date_lbl)
        layout.addLayout(info_layout)
        layout.addStretch()

        # Amount
        # Each invoice renders in the currency it was issued in.
        bill_code = (b['currency_code'] if 'currency_code' in b.keys() else '') or clinic_code
        amt_lbl = QLabel(currency.format_money(b['total_amount'], currency.symbol_for(bill_code, clinic_symbol)))
        amt_lbl.setStyleSheet(f"font-weight: 800; font-size: 14px; color: {Theme.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(amt_lbl)

        # Status badge
        status = b['status'].upper() if b['status'] else 'UNPAID'
        if status == 'PAID':
            status_lbl = QLabel("PAID")
            status_lbl.setStyleSheet("background-color: #DCFCE7; color: #166534; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 10px;")
        elif status == 'PARTIAL':
            status_lbl = QLabel("PARTIAL")
            status_lbl.setStyleSheet("background-color: #FEF3C7; color: #92400E; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 10px;")
        else:
            status_lbl = QLabel("UNPAID")
            status_lbl.setStyleSheet("background-color: #FEE2E2; color: #991B1B; font-weight: 700; font-size: 11px; padding: 3px 8px; border-radius: 10px;")
        layout.addWidget(status_lbl)

        row.mousePressEvent = lambda e: self.view_finances_requested.emit()
        return row

    def refresh_data(self):
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()

            # -----------------------------------------------------------------
            # 1. Top KPI Cards
            # -----------------------------------------------------------------
            cursor.execute("SELECT COUNT(*) as count FROM Patient")
            total_patients = cursor.fetchone()['count']
            
            today_str = date.today().strftime('%Y-%m-%d')
            cursor.execute("SELECT COUNT(*) as count FROM ClinicalNote WHERE note_date LIKE ?", (f"{today_str}%",))
            today_notes = cursor.fetchone()['count']
            
            cursor.execute("SELECT COUNT(*) as count FROM Appointment WHERE datetime LIKE ? AND status = 'SCHEDULED'", (f"{today_str}%",))
            today_appts = cursor.fetchone()['count']

            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            cursor.execute("""
                SELECT COUNT(*) as count FROM Appointment 
                WHERE date(datetime) BETWEEN ? AND ? AND status = 'SCHEDULED'
            """, (start_of_week.strftime('%Y-%m-%d'), end_of_week.strftime('%Y-%m-%d')))
            week_appts = cursor.fetchone()['count']

            _, rev_symbol, rev_position = db_manager.get_clinic_currency()
            kpis = db_manager.get_financial_kpis()
            today_rev = kpis.get('today_revenue', 0.0)

            self.update_stat_card(self.total_patients_card, str(total_patients))
            self.update_stat_card(self.today_notes_card, str(today_notes))
            self.update_stat_card(self.today_appt_card, str(today_appts))
            self.update_stat_card(self.week_appt_card, str(week_appts))
            self.update_stat_card(self.today_rev_card, currency.format_money(today_rev, rev_symbol, rev_position, 0))

            # -----------------------------------------------------------------
            # 2. Recent Patients (Row 1, Col 0)
            # -----------------------------------------------------------------
            self.clear_layout(self.activity_list)
            cursor.execute("""
                SELECT id, first_name, last_name, created_at 
                FROM Patient ORDER BY created_at DESC LIMIT 4
            """)
            recent_patients = cursor.fetchall()
            
            if not recent_patients:
                empty_lbl = QLabel("No registered patients yet.")
                empty_lbl.setWordWrap(True)
                empty_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                empty_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 12px; font-size: 13px;")
                self.activity_list.addWidget(empty_lbl)
            else:
                for p in recent_patients:
                    row = QFrame()
                    row.setCursor(Qt.PointingHandCursor)
                    row.setStyleSheet("""
                        QFrame {
                            background-color: #F8FAFC;
                            border: 1px solid #F1F5F9;
                            border-radius: 8px;
                        }
                        QFrame:hover {
                            background-color: #F1F5F9;
                            border-color: #CBD5E1;
                        }
                    """)
                    row_layout = QHBoxLayout(row)
                    row_layout.setContentsMargins(12, 9, 12, 9)
                    row_layout.setSpacing(10)
                    
                    icon_badge = QLabel("👤")
                    icon_badge.setStyleSheet("font-size: 15px; background: transparent;")
                    row_layout.addWidget(icon_badge)

                    name_display = f"{p['first_name'][0]}. {p['last_name'][0]}." if self.privacy_mode else f"{p['first_name']} {p['last_name']}"
                    name_lbl = QLabel(name_display)
                    name_lbl.setProperty("i18n_skip", True)
                    name_lbl.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {Theme.TEXT_PRIMARY}; background: transparent;")
                    row_layout.addWidget(name_lbl)
                    row_layout.addStretch()

                    date_str = str(p['created_at'])[:10] if p['created_at'] else ""
                    date_lbl = QLabel(date_str)
                    date_lbl.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY}; background: transparent;")
                    row_layout.addWidget(date_lbl)

                    tag_lbl = QLabel("Active")
                    tag_lbl.setStyleSheet("background-color: #EFF6FF; color: #1D4ED8; font-weight: 700; font-size: 10px; padding: 2px 6px; border-radius: 4px;")
                    row_layout.addWidget(tag_lbl)

                    row.mousePressEvent = lambda e: self.view_patients_requested.emit()
                    self.activity_list.addWidget(row)

            # -----------------------------------------------------------------
            # 3. Scheduled Appointments (Row 1, Col 1)
            # -----------------------------------------------------------------
            self.clear_layout(self.appt_list)
            try:
                import pandas as pd
                cursor.execute("""
                    SELECT p.first_name, p.last_name, a.datetime 
                    FROM Appointment a 
                    JOIN Patient p ON a.patient_id = p.id
                    WHERE a.status = 'SCHEDULED'
                    ORDER BY a.datetime ASC
                """)
                appointments = cursor.fetchall()
                
                if not appointments:
                    empty_lbl = QLabel("No scheduled consultations.")
                    empty_lbl.setWordWrap(True)
                    empty_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                    empty_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 12px; font-size: 13px;")
                    self.appt_list.addWidget(empty_lbl)
                else:
                    df = pd.DataFrame(appointments, columns=['first_name', 'last_name', 'datetime'])
                    try:
                        df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M')
                    except Exception:
                        df['datetime'] = pd.to_datetime(df['datetime'])
                    
                    now = pd.Timestamp.now()
                    filter_mode = combo_value(self.appt_filter)
                    
                    if filter_mode == "Today":
                        end_of_today = now.replace(hour=23, minute=59, second=59, microsecond=999999)
                        filtered_df = df[(df['datetime'] >= now) & (df['datetime'] <= end_of_today)]
                    elif filter_mode == "This Week":
                        days_until_sunday = 6 - now.weekday()
                        end_of_week = now + pd.Timedelta(days=days_until_sunday)
                        end_of_week = end_of_week.replace(hour=23, minute=59, second=59, microsecond=999999)
                        filtered_df = df[(df['datetime'] >= now) & (df['datetime'] <= end_of_week)]
                    elif filter_mode == "This Month":
                        if now.month == 12:
                            next_month = now.replace(year=now.year + 1, month=1, day=1)
                        else:
                            next_month = now.replace(month=now.month + 1, day=1)
                        end_of_month = next_month - pd.Timedelta(seconds=1)
                        filtered_df = df[(df['datetime'] >= now) & (df['datetime'] <= end_of_month)]
                    else:
                        filtered_df = df[df['datetime'] >= now]
                    
                    filtered_df = filtered_df.sort_values('datetime')
                    
                    if filtered_df.empty:
                        empty_lbl = QLabel(f"{tr('No upcoming appointments for ')}{tr(filter_mode).lower()}.")
                        empty_lbl.setWordWrap(True)
                        empty_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                        empty_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 12px; font-size: 13px;")
                        self.appt_list.addWidget(empty_lbl)
                    else:
                        for idx, row_data in filtered_df.head(4).iterrows():
                            row = QFrame()
                            row.setCursor(Qt.PointingHandCursor)
                            row.setStyleSheet("""
                                QFrame {
                                    background-color: #F8FAFC;
                                    border: 1px solid #F1F5F9;
                                    border-radius: 8px;
                                }
                                QFrame:hover {
                                    background-color: #F1F5F9;
                                    border-color: #CBD5E1;
                                }
                            """)
                            row_layout = QHBoxLayout(row)
                            row_layout.setContentsMargins(12, 9, 12, 9)
                            row_layout.setSpacing(10)

                            icon_badge = QLabel("📅")
                            icon_badge.setStyleSheet("font-size: 14px; background: transparent;")
                            row_layout.addWidget(icon_badge)

                            dt = row_data['datetime']
                            display_time = dt.strftime('%b %d, %I:%M %p')

                            name_display = f"{row_data['first_name'][0]}. {row_data['last_name'][0]}." if self.privacy_mode else f"{row_data['first_name']} {row_data['last_name']}"
                            name_lbl = QLabel(name_display)
                            name_lbl.setProperty("i18n_skip", True)
                            name_lbl.setStyleSheet(f"font-weight: 700; font-size: 13px; color: {Theme.TEXT_PRIMARY}; background: transparent;")
                            row_layout.addWidget(name_lbl)
                            row_layout.addStretch()

                            time_lbl = QLabel(display_time)
                            time_lbl.setStyleSheet(f"font-size: 12px; color: {Theme.TEXT_SECONDARY}; background: transparent;")
                            row_layout.addWidget(time_lbl)

                            row.mousePressEvent = lambda e: self.view_appointments_requested.emit()
                            self.appt_list.addWidget(row)
            except Exception as e:
                self.appt_list.addWidget(QLabel(f"Error loading appointments: {e}"))

            # -----------------------------------------------------------------
            # 4. Clinical Activity & Notes (Row 2, Col 0)
            # -----------------------------------------------------------------
            self.clear_layout(self.clinical_list)
            cursor.execute("""
                SELECT n.id, n.note_date, n.assessment, n.subjective, n.status, p.first_name, p.last_name
                FROM ClinicalNote n
                JOIN Patient p ON n.patient_id = p.id
                ORDER BY n.note_date DESC, n.id DESC
                LIMIT 3
            """)
            recent_notes = cursor.fetchall()

            cursor.execute("""
                SELECT pr.id, pr.prescription_date, pr.status, p.first_name, p.last_name
                FROM Prescription pr
                JOIN Patient p ON pr.patient_id = p.id
                ORDER BY pr.prescription_date DESC, pr.id DESC
                LIMIT 3
            """)
            recent_rx = cursor.fetchall()

            clinical_items = []
            for n in recent_notes:
                p_str = f"{n['first_name'][0]}. {n['last_name'][0]}." if self.privacy_mode else f"{n['first_name']} {n['last_name']}"
                detail_text = n['assessment'] or n['subjective'] or 'Clinical Encounter'
                clinical_items.append({
                    'type': 'NOTE',
                    'id': n['id'],
                    'date': n['note_date'],
                    'patient': p_str,
                    'detail': detail_text,
                    'status': n['status']
                })
            for r in recent_rx:
                p_str = f"{r['first_name'][0]}. {r['last_name'][0]}." if self.privacy_mode else f"{r['first_name']} {r['last_name']}"
                clinical_items.append({
                    'type': 'RX',
                    'id': r['id'],
                    'date': r['prescription_date'],
                    'patient': p_str,
                    'detail': 'Prescription Issued',
                    'status': r['status']
                })
            
            clinical_items.sort(key=lambda x: str(x['date']), reverse=True)
            clinical_items = clinical_items[:4]

            if not clinical_items:
                empty_lbl = QLabel("No clinical notes or prescriptions recorded yet.")
                empty_lbl.setWordWrap(True)
                empty_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                empty_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 12px; font-size: 13px;")
                self.clinical_list.addWidget(empty_lbl)
            else:
                for item in clinical_items:
                    row_widget = self.create_clinical_row(item)
                    self.clinical_list.addWidget(row_widget)

            # -----------------------------------------------------------------
            # 5. Recent Invoices & Billing (Row 2, Col 1)
            # -----------------------------------------------------------------
            self.clear_layout(self.billing_list)
            cursor.execute("""
                SELECT b.id, b.total_amount, b.status, b.created_at, b.currency_code,
                       p.first_name, p.last_name
                FROM Billing b
                JOIN Patient p ON b.patient_id = p.id
                ORDER BY b.created_at DESC, b.id DESC
                LIMIT 4
            """)
            recent_bills = cursor.fetchall()

            if not recent_bills:
                empty_lbl = QLabel("No invoices generated yet.")
                empty_lbl.setWordWrap(True)
                empty_lbl.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
                empty_lbl.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; padding: 12px; font-size: 13px;")
                self.billing_list.addWidget(empty_lbl)
            else:
                for b in recent_bills:
                    row_widget = self.create_billing_row(b)
                    self.billing_list.addWidget(row_widget)

        except Exception as e:
            print(f"Error refreshing dashboard: {e}")
        finally:
            if conn:
                conn.close()

    def update_stat_card(self, card, value):
        value_lbl = card.findChild(QLabel, "value")
        if value_lbl:
            value_lbl.setText(value)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
