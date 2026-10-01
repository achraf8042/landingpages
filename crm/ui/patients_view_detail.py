from utils.localization import tr
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                               QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
                               QHeaderView, QFrame, QMessageBox, QTextEdit, QAbstractItemView,
                               QScrollArea, QWidget, QFileDialog, QSizePolicy, QApplication)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QColor, QFont
from styles.theme import Theme
from data import db_manager
from ui.allergy_dialog import AllergyDialog
from ui.vitals_dialog import VitalsDialog
from ui.prescriptions_view import PrescriptionDialog
from ui.finances_view import CreateInvoiceDialog
from utils.pdf_generator import PrescriptionPDFGenerator
from utils.invoice_pdf_generator import InvoicePDFGenerator

# Compact style for the per-tab action buttons. The global 10px/20px padding
# made these wide enough to push the dialog's minimum past the screen width.
_TAB_BTN_STYLE = ("padding: 6px 12px; font-size: 12px; font-weight: 600;"
                  " border-radius: 6px; white-space: nowrap;")

class PatientDetailDialog(QDialog):
    """
    Patient 360 Comprehensive Clinical & Financial Detail Hub
    """
    def __init__(self, patient_id=None, parent=None, **kwargs):
        from PySide6.QtWidgets import QWidget
        # Handle if parent was passed first as positional argument
        if isinstance(patient_id, QWidget):
            actual_parent = patient_id
            actual_pid = parent if parent is not None else kwargs.get('patient_id')
            parent = actual_parent
            patient_id = actual_pid
        elif 'patient_id' in kwargs and patient_id is None:
            patient_id = kwargs.get('patient_id')

        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle("Patient 360° Comprehensive Record")
        self.setStyleSheet(Theme.STYLESHEET)
        # Guarantee a small minimum: without one, a long unwrapped label can
        # push the dialog's implicit minimum past the screen width.
        self.setMinimumSize(560, 480)
        
        self.setup_ui()
        self.load_patient_data()
        # Sized last, once every child exists, so the minimum is the real one.
        self._size_to_screen()

    def _size_to_screen(self, preferred_w=1000, preferred_h=750):
        """Request a comfortable size, but never larger than the screen.

        Called after setup_ui so the layout's real minimum is known; if the
        content still wants more than fits, the window is capped and the body
        scrolls instead of overflowing off-screen.
        """
        screen = QApplication.primaryScreen()
        if screen is None:
            self.resize(preferred_w, preferred_h)
            return
        geo = screen.availableGeometry()
        width = min(preferred_w, geo.width() - 40)
        height = min(preferred_h, geo.height() - 40)
        # Never ask for less than the minimum; clamp that too, or Qt logs
        # "Unable to set geometry" and the dialog ends up unusable.
        min_w = self.minimumSizeHint().width()
        min_h = self.minimumSizeHint().height()
        width = max(width, min(min_w, geo.width() - 20))
        height = max(height, min(min_h, geo.height() - 20))
        self.resize(width, height)
        self.move(geo.x() + max(0, (geo.width() - self.width()) // 2),
                  geo.y() + max(0, (geo.height() - self.height()) // 3))

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(16)

        # 1. Header Card (Patient Demographics + Allergy Alert)
        self.header_frame = QFrame()
        self.header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SURFACE};
                border-radius: 12px;
                border: 1px solid #E2E8F0;
                padding: 14px;
            }}
        """)
        header_vbox = QVBoxLayout(self.header_frame)
        header_vbox.setSpacing(10)

        # Top row: Avatar, Info, Actions
        top_row = QHBoxLayout()
        avatar = QLabel("👤")
        avatar.setStyleSheet("font-size: 40px; background: transparent;")
        top_row.addWidget(avatar)

        self.info_layout = QVBoxLayout()
        self.name_label = QLabel(tr("Loading Patient..."))
        self.name_label.setProperty("i18n_skip", True)
        self.name_label.setStyleSheet(f"font-size: 22px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        self.sub_info_label = QLabel("DOB: -- | Phone: -- | Email: --")
        # Must wrap: as a single unwrapped line this label's minimum width was
        # over 1100px, which dragged the whole dialog past the screen width.
        self.sub_info_label.setWordWrap(True)
        self.sub_info_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.sub_info_label.setStyleSheet(f"font-size: 13px; color: {Theme.TEXT_SECONDARY};")

        self.name_label.setWordWrap(True)
        self.name_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.info_layout.addWidget(self.name_label)
        self.info_layout.addWidget(self.sub_info_label)

        self.insurance_label = QLabel("")
        self.insurance_label.setWordWrap(True)
        self.insurance_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.insurance_label.setStyleSheet(
            f"font-size: 12px; font-weight: 600; color: #1D4ED8;"
            f" background: {Theme.tint('#1D4ED8', 0.90)};"
            f" border: 1px solid {Theme.tint('#1D4ED8', 0.72)};"
            " border-radius: 6px; padding: 4px 8px;")
        self.insurance_label.setVisible(False)
        self.info_layout.addWidget(self.insurance_label)
        top_row.addLayout(self.info_layout, 1)
        top_row.addStretch()

        # Quick action buttons in header
        quick_actions = QHBoxLayout()
        quick_actions.setSpacing(8)

        # Compact padding: the four default-padded buttons needed ~790px, which
        # plus the info column overran narrower screens.
        quick_style = ("padding: 6px 12px; font-size: 12px; font-weight: 600;"
                       " border-radius: 6px; white-space: nowrap;")

        vitals_btn = QPushButton("+ Vitals")
        vitals_btn.setStyleSheet(quick_style)
        vitals_btn.clicked.connect(self.record_vitals)
        
        allergy_btn = QPushButton("+ Allergy")
        allergy_btn.setStyleSheet(quick_style)
        allergy_btn.clicked.connect(self.add_allergy)

        rx_btn = QPushButton("+ Rx")
        rx_btn.setStyleSheet(quick_style)
        rx_btn.clicked.connect(self.new_prescription)

        bill_btn = QPushButton("+ Invoice")
        bill_btn.setStyleSheet(quick_style)
        bill_btn.clicked.connect(self.new_invoice)

        quick_actions.addWidget(vitals_btn)
        quick_actions.addWidget(allergy_btn)
        quick_actions.addWidget(rx_btn)
        quick_actions.addWidget(bill_btn)
        # Their own row: side by side with the info column, the four buttons plus
        # the details forced a ~980px header minimum. Stacked, the header only
        # needs as wide as the widest of the two.
        quick_actions.addStretch()
        header_vbox.addLayout(top_row)
        header_vbox.addLayout(quick_actions)

        # Allergy Alert Warning Banner
        self.allergy_banner = QLabel()
        self.allergy_banner.setWordWrap(True)
        self.allergy_banner.setVisible(False)
        header_vbox.addWidget(self.allergy_banner)

        main_layout.addWidget(self.header_frame)

        # 2. Tabbed Section
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #E2E8F0;
                background-color: {Theme.SURFACE};
                border-radius: 8px;
            }}
            QTabBar::tab {{
                background: #F1F5F9;
                color: {Theme.TEXT_SECONDARY};
                padding: 8px 16px;
                font-weight: bold;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: {Theme.SURFACE};
                color: {Theme.PRIMARY};
                border-bottom: 2px solid {Theme.PRIMARY};
            }}
        """)

        # Tab 1: Overview & Medical History
        self.tab_overview = QWidget()
        self.setup_tab_overview()
        self.tabs.addTab(self.tab_overview, "📋 Medical History")

        # Tab 2: Vitals & BMI
        self.tab_vitals = QWidget()
        self.setup_tab_vitals()
        self.tabs.addTab(self.tab_vitals, "❤️ Vitals & BMI")

        # Tab 3: Clinical Notes
        self.tab_notes = QWidget()
        self.setup_tab_notes()
        self.tabs.addTab(self.tab_notes, "📝 SOAP Notes")

        # Tab 4: Prescriptions
        self.tab_rx = QWidget()
        self.setup_tab_rx()
        self.tabs.addTab(self.tab_rx, "💊 Prescriptions")

        # Tab 5: Invoices & Financial Ledger
        self.tab_billing = QWidget()
        self.setup_tab_billing()
        self.tabs.addTab(self.tab_billing, "💳 Invoices & Balance")

        main_layout.addWidget(self.tabs)

        # Close Button
        bottom_bar = QHBoxLayout()
        bottom_bar.addStretch()
        close_btn = QPushButton("Close")
        close_btn.setProperty("class", "secondary")
        close_btn.clicked.connect(self.accept)
        bottom_bar.addWidget(close_btn)
        main_layout.addLayout(bottom_bar)

    # -------------------------
    # TAB 1: Overview
    # -------------------------
    def setup_tab_overview(self):
        layout = QVBoxLayout(self.tab_overview)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Contact & Emergency Card
        info_frame = QFrame()
        info_frame.setStyleSheet(f"background-color: {Theme.BACKGROUND}; border-radius: 8px; padding: 12px;")
        info_layout = QVBoxLayout(info_frame)
        self.full_contact_label = QLabel("Loading contact info...")
        self.full_contact_label.setWordWrap(True)
        info_layout.addWidget(self.full_contact_label)
        layout.addWidget(info_frame)

        # Medical History Section
        med_hist_title = QLabel("Past Medical History & Chronic Conditions:")
        med_hist_title.setWordWrap(True)
        med_hist_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        med_hist_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(med_hist_title)

        self.med_history_text = QTextEdit()
        self.med_history_text.setPlaceholderText("Record major medical conditions, surgeries, family history...")
        layout.addWidget(self.med_history_text)

        save_history_btn = QPushButton("Save Medical History")
        save_history_btn.setStyleSheet(_TAB_BTN_STYLE)
        save_history_btn.clicked.connect(self.save_medical_history)
        
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        btn_box.addWidget(save_history_btn)
        layout.addLayout(btn_box)

    # -------------------------
    # TAB 2: Vitals
    # -------------------------
    def setup_tab_vitals(self):
        layout = QVBoxLayout(self.tab_vitals)
        layout.setContentsMargins(16, 16, 16, 16)

        tb = QHBoxLayout()
        vitals_title = QLabel("<b>Vital Signs Progression & BMI History</b>")
        vitals_title.setWordWrap(True)
        vitals_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(vitals_title, 1)
        add_vitals_btn = QPushButton("+ Record New Vitals")
        add_vitals_btn.setStyleSheet(_TAB_BTN_STYLE)
        add_vitals_btn.clicked.connect(self.record_vitals)
        tb.addWidget(add_vitals_btn, 0, Qt.AlignTop)
        layout.addLayout(tb)

        self.vitals_table = QTableWidget(0, 8)
        self.vitals_table.setHorizontalHeaderLabels(["Date", "BP (mmHg)", "Pulse (bpm)", "Temp (°C)", "Weight (kg)", "Height (cm)", "BMI", "SpO2 (%)"])
        self.vitals_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vitals_table.verticalHeader().setVisible(False)
        self.vitals_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.vitals_table)

    # -------------------------
    # TAB 3: SOAP Notes
    # -------------------------
    def setup_tab_notes(self):
        layout = QVBoxLayout(self.tab_notes)
        layout.setContentsMargins(16, 16, 16, 16)

        self.notes_table = QTableWidget(0, 4)
        self.notes_table.setHorizontalHeaderLabels(["Date", "Assessment / Diagnosis", "Status", "Action"])
        self.notes_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.notes_table.verticalHeader().setVisible(False)
        self.notes_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.notes_table)

        # Selected Note SOAP preview
        preview_title = QLabel("SOAP Note Content:")
        preview_title.setWordWrap(True)
        preview_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        preview_title.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(preview_title)

        self.note_preview = QTextEdit()
        self.note_preview.setReadOnly(True)
        self.note_preview.setMaximumHeight(150)
        self.note_preview.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        layout.addWidget(self.note_preview)

        self.notes_table.itemSelectionChanged.connect(self.display_selected_note)

    # -------------------------
    # TAB 4: Prescriptions
    # -------------------------
    def setup_tab_rx(self):
        layout = QVBoxLayout(self.tab_rx)
        layout.setContentsMargins(16, 16, 16, 16)

        tb = QHBoxLayout()
        rx_title = QLabel("<b>Prescription History & Active Medications</b>")
        rx_title.setWordWrap(True)
        rx_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        tb.addWidget(rx_title, 1)
        new_rx_btn = QPushButton("+ New Prescription")
        new_rx_btn.setStyleSheet(_TAB_BTN_STYLE)
        new_rx_btn.clicked.connect(self.new_prescription)
        tb.addWidget(new_rx_btn, 0, Qt.AlignTop)
        layout.addLayout(tb)

        self.rx_table = QTableWidget(0, 5)
        self.rx_table.setHorizontalHeaderLabels(["Date", "Prescribed Medications", "Doctor", "Status", "Export PDF"])
        self.rx_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.rx_table.verticalHeader().setVisible(False)
        self.rx_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.rx_table)

    # -------------------------
    # TAB 5: Billing
    # -------------------------
    def setup_tab_billing(self):
        layout = QVBoxLayout(self.tab_billing)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Financial Summary Card
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"background-color: {Theme.BACKGROUND}; border-radius: 8px; padding: 10px;")
        summary_layout = QHBoxLayout(summary_frame)

        self.lbl_total_billed = QLabel("Total Billed: $0.00")
        self.lbl_total_billed.setWordWrap(True)
        self.lbl_total_billed.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.lbl_total_billed.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.lbl_total_paid = QLabel("Total Paid: $0.00")
        self.lbl_total_paid.setWordWrap(True)
        self.lbl_total_paid.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.lbl_total_paid.setStyleSheet("font-size: 14px; font-weight: bold; color: #16A34A;")
        self.lbl_balance_due = QLabel("Balance Due: $0.00")
        self.lbl_balance_due.setWordWrap(True)
        self.lbl_balance_due.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.lbl_balance_due.setStyleSheet("font-size: 14px; font-weight: bold; color: #DC2626;")

        summary_layout.addWidget(self.lbl_total_billed)
        summary_layout.addStretch()
        summary_layout.addWidget(self.lbl_total_paid)
        summary_layout.addStretch()
        summary_layout.addWidget(self.lbl_balance_due)
        layout.addWidget(summary_frame)

        # Invoices Table
        self.bills_table = QTableWidget(0, 5)
        self.bills_table.setHorizontalHeaderLabels(["Invoice #", "Date", "Amount", "Status", "Notes"])
        self.bills_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.bills_table.verticalHeader().setVisible(False)
        self.bills_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.bills_table)

        btn_row = QHBoxLayout()
        new_inv_btn = QPushButton("+ Create Invoice")
        new_inv_btn.setStyleSheet(_TAB_BTN_STYLE)
        new_inv_btn.clicked.connect(self.new_invoice)
        btn_row.addStretch()
        btn_row.addWidget(new_inv_btn)
        layout.addLayout(btn_row)

    # -------------------------
    # Data Loading & Populating
    # -------------------------
    def load_patient_data(self):
        data = db_manager.get_patient_360(self.patient_id)
        if not data:
            return

        p = data['patient']
        self.patient_record = p
        self.name_label.setText(f"{p['first_name']} {p['last_name']}")
        
        # Calculate age
        age = "N/A"
        if p['date_of_birth']:
            try:
                dob = QDate.fromString(p['date_of_birth'], "yyyy-MM-dd")
                age = f"{QDate.currentDate().year() - dob.year()} {tr('years old')}"
            except Exception:
                pass

        self.sub_info_label.setText(
            f"DOB: {p['date_of_birth'] or 'N/A'} ({age})  |  Gender: {tr(p['gender'] or 'N/A')}  |  Phone: {p['phone'] or 'N/A'}  |  Email: {p['email'] or 'N/A'}"
        )

        # Full contact overview
        self.full_contact_label.setText(
            f"<b>Address:</b> {p['address'] or 'None recorded'}<br/>"
            f"<b>Emergency Contact:</b> {p['emergency_contact'] or 'None'} &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"<b>Emergency Phone:</b> {p['emergency_phone'] or 'None'}"
        )

        # Insurance badge - hidden entirely for self-pay patients.
        provider = (p['insurance_provider'] or "").strip() if 'insurance_provider' in p.keys() else ""
        member = (p['insurance_member_no'] or "").strip() if 'insurance_member_no' in p.keys() else ""
        if provider or member:
            text = f"🛡  {tr('Insurance')}: {provider or '—'}"
            if member:
                text += f"   ·   {tr('Member No.')}: {member}"
            self.insurance_label.setText(text)
            self.insurance_label.setVisible(True)
        else:
            self.insurance_label.setVisible(False)

        self.med_history_text.setText(p['medical_history'] or "")

        # Allergies Banner
        allergies = data['allergies']
        active_allergies = [a for a in allergies if a['is_active']]
        if active_allergies:
            allergy_msg = "⚠️ <b>KNOWN ALLERGIES:</b> " + ", ".join(
                [f"<b>{a['allergen']}</b> ({tr(a['severity'])}{': ' + a['reaction'] if a['reaction'] else ''})" for a in active_allergies]
            )
            has_severe = any(a['severity'] == 'Severe' for a in active_allergies)
            bg_color = "#DC2626" if has_severe else "#D97706"
            self.allergy_banner.setText(allergy_msg)
            self.allergy_banner.setStyleSheet(f"background-color: {bg_color}; color: white; padding: 10px; border-radius: 6px; font-size: 13px;")
            self.allergy_banner.setVisible(True)
        else:
            self.allergy_banner.setVisible(False)

        # Populate Vitals
        vitals = data['vitals']
        self.vitals_table.setRowCount(len(vitals))
        for r, v in enumerate(vitals):
            bp_str = f"{v['systolic_bp']}/{v['diastolic_bp']}" if v['systolic_bp'] else "--"
            self.vitals_table.setItem(r, 0, QTableWidgetItem(v['measurement_date'] or ""))
            self.vitals_table.setItem(r, 1, QTableWidgetItem(bp_str))
            self.vitals_table.setItem(r, 2, QTableWidgetItem(str(v['heart_rate'] or "--")))
            self.vitals_table.setItem(r, 3, QTableWidgetItem(str(v['temperature'] or "--")))
            self.vitals_table.setItem(r, 4, QTableWidgetItem(str(v['weight'] or "--")))
            self.vitals_table.setItem(r, 5, QTableWidgetItem(str(v['height'] or "--")))

            bmi_val = v['bmi']
            bmi_item = QTableWidgetItem(str(bmi_val) if bmi_val else "--")
            if bmi_val:
                if bmi_val > 25.0:
                    bmi_item.setForeground(QColor("#D97706"))
                elif bmi_val > 30.0:
                    bmi_item.setForeground(QColor("#DC2626"))
                else:
                    bmi_item.setForeground(QColor("#16A34A"))
            self.vitals_table.setItem(r, 6, bmi_item)
            self.vitals_table.setItem(r, 7, QTableWidgetItem(str(v['oxygen_saturation'] or "--")))

        # Populate Notes
        self.clinical_notes_data = data['notes']
        self.notes_table.setRowCount(len(self.clinical_notes_data))
        for r, n in enumerate(self.clinical_notes_data):
            self.notes_table.setItem(r, 0, QTableWidgetItem(n['note_date']))
            self.notes_table.setItem(r, 1, QTableWidgetItem(n['assessment'] or "(No assessment recorded)"))
            status_item = QTableWidgetItem(n['status'])
            if n['status'] == 'FINALIZED':
                status_item.setForeground(QColor("#16A34A"))
            self.notes_table.setItem(r, 2, status_item)
            self.notes_table.setItem(r, 3, QTableWidgetItem(tr("👁 View Note")))

        # Populate Prescriptions
        rx_list = data['prescriptions']
        self.rx_table.setRowCount(len(rx_list))
        for r, rx in enumerate(rx_list):
            self.rx_table.setItem(r, 0, QTableWidgetItem(rx['prescription_date']))
            self.rx_table.setItem(r, 1, QTableWidgetItem(rx['med_names'] or rx['instructions'] or "(Medications)"))
            self.rx_table.setItem(r, 2, QTableWidgetItem(rx['prescribing_doctor'] or "Doctor"))
            self.rx_table.setItem(r, 3, QTableWidgetItem(rx['status']))
            self.rx_table.setItem(r, 4, QTableWidgetItem("📄 PDF"))

        # Populate Billing
        bills = data['bills']
        self.bills_table.setRowCount(len(bills))
        for r, b in enumerate(bills):
            self.bills_table.setItem(r, 0, QTableWidgetItem(f"#{b['id']:04d}"))
            self.bills_table.setItem(r, 1, QTableWidgetItem(b['created_at'][:10] if b['created_at'] else ""))
            self.bills_table.setItem(r, 2, QTableWidgetItem(f"${float(b['total_amount']):.2f}"))
            
            st_item = QTableWidgetItem(b['status'])
            st_item.setForeground(QColor("#16A34A" if b['status'] == 'PAID' else "#DC2626"))
            self.bills_table.setItem(r, 3, st_item)
            self.bills_table.setItem(r, 4, QTableWidgetItem(b['notes'] or ""))

        self.lbl_total_billed.setText(f"Total Billed: ${data['total_billed']:.2f}")
        self.lbl_total_paid.setText(f"Total Paid: ${data['total_paid']:.2f}")
        self.lbl_balance_due.setText(f"Balance Due: ${data['balance_due']:.2f}")

    def display_selected_note(self):
        selected = self.notes_table.selectedIndexes()
        if not selected or not hasattr(self, 'clinical_notes_data'):
            return
        row = selected[0].row()
        if row < len(self.clinical_notes_data):
            n = self.clinical_notes_data[row]
            soap_text = (
                f"=== SOAP CLINICAL NOTE ({n['note_date']}) - Status: {n['status']} ===\n\n"
                f"SUBJECTIVE:\n{n['subjective'] or 'N/A'}\n\n"
                f"OBJECTIVE:\n{n['objective'] or 'N/A'}\n\n"
                f"ASSESSMENT:\n{n['assessment'] or 'N/A'}\n\n"
                f"PLAN:\n{n['plan'] or 'N/A'}"
            )
            self.note_preview.setText(soap_text)

    def save_medical_history(self):
        new_history = self.med_history_text.toPlainText().strip()
        try:
            with db_manager.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE Patient SET medical_history = ? WHERE id = ?", (new_history, self.patient_id))
                conn.commit()
            QMessageBox.information(self, "Success", "Medical history updated successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save medical history: {e}")

    def record_vitals(self):
        dialog = VitalsDialog(self.patient_id, parent=self)
        if dialog.exec():
            self.load_patient_data()

    def add_allergy(self):
        dialog = AllergyDialog(self.patient_id, parent=self)
        if dialog.exec():
            self.load_patient_data()

    def new_prescription(self):
        dialog = PrescriptionDialog(parent=self, patient_id=self.patient_id)
        if dialog.exec():
            self.load_patient_data()

    def new_invoice(self):
        dialog = CreateInvoiceDialog(parent=self, patient_id=self.patient_id)
        if dialog.exec():
            self.load_patient_data()
