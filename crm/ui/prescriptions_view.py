from utils.localization import tr
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                               QTableView, QHeaderView, QDialog, QFormLayout,
                               QComboBox, QDateEdit, QLineEdit, QTextEdit, QMessageBox,
                               QAbstractItemView, QStyle, QFileDialog, QLabel, QTableWidget,
                               QTableWidgetItem, QFrame)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem
from styles.theme import Theme
from data import db_manager
from utils.pdf_generator import PrescriptionPDFGenerator
from datetime import datetime

class PrescriptionsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_prescriptions()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by patient name or instructions...")
        self.search_input.textChanged.connect(self.load_prescriptions)
        
        search_btn = QPushButton("Search")
        search_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        search_btn.setIconSize(QSize(16, 16))
        search_btn.clicked.connect(self.load_prescriptions)
        
        add_btn = QPushButton("+ New Prescription")
        add_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        add_btn.setIconSize(QSize(16, 16))
        add_btn.clicked.connect(self.show_add_dialog)
        
        export_btn = QPushButton("Export PDF")
        export_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        export_btn.setIconSize(QSize(16, 16))
        export_btn.setProperty("class", "secondary")
        export_btn.clicked.connect(self.export_prescription)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setProperty("class", "danger")
        delete_btn.clicked.connect(self.delete_prescription)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(search_btn)
        toolbar.addStretch()
        toolbar.addWidget(export_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(add_btn)
        layout.addLayout(toolbar)

        # Table
        self.table = QTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"alternate-background-color: {Theme.BACKGROUND};")
        
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["ID", "Date", "Patient", "Doctor", "Medications Prescribed", "Status", "Action"])
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True) # Hide ID column
        self.table.doubleClicked.connect(self.view_prescription_details)
        
        layout.addWidget(self.table)

    def load_prescriptions(self):
        search_text = self.search_input.text().strip() if hasattr(self, 'search_input') else ''
        try:
            prescriptions = db_manager.get_prescriptions(search_text=search_text)
            self.model.removeRows(0, self.model.rowCount())
            
            for p in prescriptions:
                med_summary = p['med_names'] or "(No medications listed)"
                row = [
                    QStandardItem(str(p['id'])),
                    QStandardItem(p['prescription_date'] or ""),
                    QStandardItem(f"{p['first_name']} {p['last_name']}"),
                    QStandardItem(p['prescribing_doctor'] or "Doctor"),
                    QStandardItem(med_summary),
                    QStandardItem(p['status']),
                    QStandardItem("📄 PDF")
                ]
                row[0].setData(p['id'], Qt.UserRole)
                for item in row:
                    item.setEditable(False)
                self.model.appendRow(row)
        except Exception as e:
            print(f"Error loading prescriptions: {e}")

    def show_add_dialog(self):
        dialog = PrescriptionDialog(self)
        if dialog.exec():
            self.load_prescriptions()

    def get_selected_prescription_id(self):
        selected_indexes = self.table.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        row = selected_indexes[0].row()
        return self.model.item(row, 0).data(Qt.UserRole)

    def view_prescription_details(self):
        pres_id = self.get_selected_prescription_id()
        if not pres_id:
            return
        dialog = PrescriptionDetailDialog(pres_id, self)
        dialog.exec()

    def delete_prescription(self):
        pres_id = self.get_selected_prescription_id()
        if not pres_id:
            QMessageBox.warning(self, "Warning", "Please select a prescription to delete")
            return
            
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this prescription?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            success, msg = db_manager.delete_prescription(pres_id)
            if success:
                self.load_prescriptions()
            else:
                QMessageBox.critical(self, "Error", f"Failed to delete prescription: {msg}")

    def export_prescription(self):
        pres_id = self.get_selected_prescription_id()
        if not pres_id:
            QMessageBox.warning(self, "Warning", "Please select a prescription to export")
            return
            
        try:
            details = db_manager.get_prescription_details(pres_id)
            if not details:
                QMessageBox.warning(self, "Error", "Prescription not found")
                return
                
            rx = details['prescription']
            items = details['items']

            # Calculate patient age
            age_str = ""
            if rx['date_of_birth']:
                try:
                    dob = QDate.fromString(rx['date_of_birth'], "yyyy-MM-dd")
                    age_str = str(QDate.currentDate().year() - dob.year())
                except Exception:
                    pass

            meds_list = []
            for item in items:
                meds_list.append({
                    'medication_name': item['medication_name'],
                    'dosage': item['dosage'] or '',
                    'frequency': item['frequency'] or '',
                    'duration': item['duration'] or ''
                })

            pdf_data = {
                'patient_name': f"{rx['first_name']} {rx['last_name']}",
                'patient_dob': rx['date_of_birth'] or 'N/A',
                'patient_gender': rx['gender'] or '',
                'patient_age': age_str,
                'visit_date': rx['prescription_date'],
                'doctor_name': rx['prescribing_doctor'] or 'Doctor',
                'medications': meds_list,
                'instructions': rx['instructions'] or ''
            }
            
            filename, _ = QFileDialog.getSaveFileName(
                self, 
                tr("Save Prescription PDF"), 
                f"Prescription_{rx['first_name']}_{rx['last_name']}_{rx['prescription_date']}.pdf", 
                tr("PDF Files (*.pdf)")
            )
            
            if filename:
                PrescriptionPDFGenerator.generate(filename, pdf_data)
                QMessageBox.information(self, "Success", "Prescription PDF exported successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export prescription: {e}")


class PrescriptionDialog(QDialog):
    """Dialog for creating multi-medication prescriptions"""
    def __init__(self, parent=None, patient_id=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle("New Multi-Medication Prescription")
        self.resize(750, 680)
        self.setStyleSheet(Theme.STYLESHEET)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        # Header Title
        title = QLabel("Write Prescription")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.PRIMARY};")
        layout.addWidget(title)
        
        # Form Layout
        form_layout = QFormLayout()
        
        # Patient selector
        self.patient_combo = QComboBox()
        self.patient_combo.currentIndexChanged.connect(self.check_allergies)
        form_layout.addRow("Patient *:", self.patient_combo)
        
        # Allergy Warning Banner
        self.allergy_warning = QLabel()
        self.allergy_warning.setWordWrap(True)
        self.allergy_warning.setVisible(False)
        self.allergy_warning.setStyleSheet(f"""
            QLabel {{
                background-color: #DC2626;
                color: white;
                padding: 10px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 13px;
            }}
        """)
        layout.addWidget(self.allergy_warning)

        # Date & Doctor
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Date *:", self.date_edit)

        self.doctor_input = QLineEdit()
        # Fetch current doctor
        user = db_manager.get_user_details("doctor")
        if user and user['first_name']:
            self.doctor_input.setText(f"Dr. {user['first_name']} {user['last_name']}")
        else:
            self.doctor_input.setText("Dr. Doctor")
        form_layout.addRow("Prescribing Doctor:", self.doctor_input)
        layout.addLayout(form_layout)

        # Medications Header & Table
        meds_header = QHBoxLayout()
        meds_label = QLabel("Prescribed Medications:")
        meds_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY}; font-size: 14px;")
        
        add_med_btn = QPushButton("+ Add Medication")
        add_med_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }}
        """)
        add_med_btn.clicked.connect(lambda: self.add_medication_row())
        meds_header.addWidget(meds_label)
        meds_header.addStretch()
        meds_header.addWidget(add_med_btn)
        layout.addLayout(meds_header)

        # Multi-Medication Table Widget
        self.meds_table = QTableWidget(0, 5)
        self.meds_table.setObjectName("prescMedsTable")
        self.meds_table.setStyleSheet("""
            QTableWidget#prescMedsTable {
                background-color: #FFFFFF;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                gridline-color: #F1F5F9;
            }
            QTableWidget#prescMedsTable::item {
                padding: 0px;
                border: none;
                border-bottom: 1px solid #F1F5F9;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #475569;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                padding: 10px 12px;
            }
        """)
        self.meds_table.viewport().setStyleSheet("background-color: #FFFFFF; color: #0F172A;")
        self.meds_table.setHorizontalHeaderLabels(["Medication Name *", "Dosage", "Frequency", "Duration", "Action"])
        self.meds_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.meds_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.meds_table.setColumnWidth(1, 130)
        self.meds_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.meds_table.setColumnWidth(2, 140)
        self.meds_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Fixed)
        self.meds_table.setColumnWidth(3, 120)
        self.meds_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Fixed)
        self.meds_table.setColumnWidth(4, 90)
        self.meds_table.verticalHeader().setVisible(False)
        self.meds_table.verticalHeader().setDefaultSectionSize(50)
        self.meds_table.setShowGrid(True)
        self.meds_table.setMinimumHeight(200)
        layout.addWidget(self.meds_table)

        # Pre-populate one empty row
        self.add_medication_row()

        # Clinical Instructions
        instr_label = QLabel("Instructions & Advice:")
        instr_label.setStyleSheet(f"font-weight: bold; color: {Theme.TEXT_PRIMARY}; font-size: 13px;")
        layout.addWidget(instr_label)
        
        self.instructions_edit = QTextEdit()
        self.instructions_edit.setPlaceholderText("e.g. Take with food. Drink plenty of water. Return if fever persists...")
        self.instructions_edit.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 8px; font-size: 13px;")
        self.instructions_edit.setMaximumHeight(75)
        layout.addWidget(self.instructions_edit)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Prescription")
        save_btn.setStyleSheet(f"background-color: {Theme.PRIMARY}; color: white; font-weight: bold; padding: 10px 22px; border-radius: 6px; font-size: 13px;")
        save_btn.clicked.connect(self.save_prescription)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setStyleSheet("border: 1px solid #CBD5E1; background-color: #FFFFFF; color: #0F172A; padding: 10px 20px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

        # Load patients into combo
        self.load_patients()

    def add_medication_row(self, name="", dosage="", freq="", dur=""):
        if not isinstance(name, str):
            name = ""
        if not isinstance(dosage, str):
            dosage = ""
        if not isinstance(freq, str):
            freq = ""
        if not isinstance(dur, str):
            dur = ""

        row = self.meds_table.rowCount()
        self.meds_table.insertRow(row)

        cell_input_style = """
            QLineEdit {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
                font-weight: 500;
                margin: 3px 4px;
            }
            QLineEdit:focus {
                border: 2px solid #5B73A7;
            }
        """

        name_edit = QLineEdit(name)
        name_edit.setPlaceholderText("e.g. Amoxicillin")
        name_edit.setStyleSheet(cell_input_style)
        name_edit.setMinimumHeight(36)
        self.meds_table.setCellWidget(row, 0, name_edit)

        dosage_edit = QLineEdit(dosage)
        dosage_edit.setPlaceholderText("e.g. 500mg")
        dosage_edit.setStyleSheet(cell_input_style)
        dosage_edit.setMinimumHeight(36)
        self.meds_table.setCellWidget(row, 1, dosage_edit)

        freq_edit = QLineEdit(freq)
        freq_edit.setPlaceholderText("e.g. 3x/day")
        freq_edit.setStyleSheet(cell_input_style)
        freq_edit.setMinimumHeight(36)
        self.meds_table.setCellWidget(row, 2, freq_edit)

        dur_edit = QLineEdit(dur)
        dur_edit.setPlaceholderText("e.g. 7 days")
        dur_edit.setStyleSheet(cell_input_style)
        dur_edit.setMinimumHeight(36)
        self.meds_table.setCellWidget(row, 3, dur_edit)

        del_btn = QPushButton("✕ Remove")
        del_btn.setToolTip("Remove this medication")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                color: #DC2626;
                border: 1px solid #FCA5A5;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 4px;
                margin: 3px 4px;
            }
            QPushButton:hover {
                background-color: #DC2626;
                color: #FFFFFF;
            }
        """)
        del_btn.setMinimumHeight(34)
        del_btn.clicked.connect(lambda _, r=row: self.remove_medication_row(r))
        self.meds_table.setCellWidget(row, 4, del_btn)

        self.meds_table.setRowHeight(row, 50)

    def remove_medication_row(self, row):
        if self.meds_table.rowCount() > 1:
            self.meds_table.removeRow(row)
            # Re-wire remove buttons with updated indices
            for r in range(self.meds_table.rowCount()):
                btn = self.meds_table.cellWidget(r, 4)
                if btn:
                    btn.clicked.disconnect()
                    btn.clicked.connect(lambda _, curr_r=r: self.remove_medication_row(curr_r))

    def load_patients(self):
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, first_name, last_name FROM Patient ORDER BY last_name, first_name")
            patients = cursor.fetchall()
            conn.close()

            selected_idx = 0
            for idx, p in enumerate(patients):
                self.patient_combo.addItem(f"{p['first_name']} {p['last_name']}", p['id'])
                if self.patient_id and p['id'] == self.patient_id:
                    selected_idx = idx

            if self.patient_combo.count() > 0:
                self.patient_combo.setCurrentIndex(selected_idx)
                self.check_allergies()
        except Exception as e:
            print(f"Error loading patients for combo: {e}")

    def check_allergies(self):
        patient_id = self.patient_combo.currentData()
        if not patient_id:
            self.allergy_warning.setVisible(False)
            return
        
        allergies = db_manager.get_patient_allergies(patient_id)
        active_allergies = [a for a in allergies if a['is_active']]
        
        if active_allergies:
            allergy_text = "⚠️ ALLERGY ALERT — PATIENT HAS KNOWN ALLERGIES:\n"
            for allergy in active_allergies:
                severity = allergy['severity']
                allergen = allergy['allergen']
                reaction = allergy['reaction'] or 'Unknown reaction'
                allergy_text += f"• {allergen} ({severity}) - {reaction}\n"
            
            self.allergy_warning.setText(allergy_text.strip())
            self.allergy_warning.setVisible(True)
        else:
            self.allergy_warning.setVisible(False)

    def save_prescription(self):
        patient_id = self.patient_combo.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Error", "Please select a patient")
            return

        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        doctor_name = self.doctor_input.text().strip() or "Dr. Doctor"
        instructions = self.instructions_edit.toPlainText().strip()

        # Collect medications
        items = []
        for r in range(self.meds_table.rowCount()):
            name_widget = self.meds_table.cellWidget(r, 0)
            dosage_widget = self.meds_table.cellWidget(r, 1)
            freq_widget = self.meds_table.cellWidget(r, 2)
            dur_widget = self.meds_table.cellWidget(r, 3)

            name = name_widget.text().strip() if name_widget else ""
            if name:
                items.append({
                    'medication_name': name,
                    'dosage': dosage_widget.text().strip() if dosage_widget else "",
                    'frequency': freq_widget.text().strip() if freq_widget else "",
                    'duration': dur_widget.text().strip() if dur_widget else ""
                })

        if not items:
            QMessageBox.warning(self, "Error", "Please enter at least one medication")
            return

        success, res = db_manager.create_prescription(
            patient_id=patient_id,
            doctor_name=doctor_name,
            prescription_date=date_str,
            items=items,
            instructions=instructions
        )

        if success:
            QMessageBox.information(self, "Success", "Prescription created successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save prescription: {res}")


class PrescriptionDetailDialog(QDialog):
    """View details of a prescription with medication list"""
    def __init__(self, prescription_id, parent=None):
        super().__init__(parent)
        self.prescription_id = prescription_id
        self.setWindowTitle("Prescription Details")
        self.resize(550, 500)
        self.setStyleSheet(Theme.STYLESHEET)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        details = db_manager.get_prescription_details(self.prescription_id)
        if not details:
            layout.addWidget(QLabel("Prescription details not found."))
            return

        rx = details['prescription']
        items = details['items']

        # Header card
        header = QLabel(f"Prescription #{rx['id']} — {rx['first_name']} {rx['last_name']}")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.PRIMARY};")
        layout.addWidget(header)

        info_box = QLabel(f"<b>Date:</b> {rx['prescription_date']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Doctor:</b> {rx['prescribing_doctor']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Status:</b> {tr(rx['status'])}")
        info_box.setStyleSheet(f"background-color: {Theme.BACKGROUND}; padding: 8px; border-radius: 6px;")
        layout.addWidget(info_box)

        # Medications List
        meds_title = QLabel("Prescribed Medications:")
        meds_title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(meds_title)

        meds_table = QTableWidget(len(items), 4)
        meds_table.setHorizontalHeaderLabels(["Medication", "Dosage", "Frequency", "Duration"])
        meds_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        meds_table.verticalHeader().setVisible(False)
        meds_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        for r, itm in enumerate(items):
            meds_table.setItem(r, 0, QTableWidgetItem(itm['medication_name']))
            meds_table.setItem(r, 1, QTableWidgetItem(itm['dosage'] or ''))
            meds_table.setItem(r, 2, QTableWidgetItem(itm['frequency'] or ''))
            meds_table.setItem(r, 3, QTableWidgetItem(itm['duration'] or ''))

        layout.addWidget(meds_table)

        if rx['instructions']:
            instr_title = QLabel("Instructions:")
            instr_title.setStyleSheet("font-weight: bold;")
            layout.addWidget(instr_title)
            instr_text = QLabel(rx['instructions'])
            instr_text.setStyleSheet(f"background-color: #FFFBEB; padding: 10px; border-radius: 6px; border: 1px solid #FDE68A;")
            instr_text.setWordWrap(True)
            layout.addWidget(instr_text)

        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)
