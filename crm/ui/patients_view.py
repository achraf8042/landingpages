

from utils.localization import combo_value, set_combo_value, tr
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableView, QHeaderView, QLineEdit, QDialog, 
                               QFormLayout, QMessageBox, QAbstractItemView, QDateEdit, QStyle, QComboBox,
                               QLabel, QFrame, QSizePolicy, QDoubleSpinBox)
from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QDate, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor
from styles.theme import Theme
from data import db_manager
from ui.patients_view_detail import PatientDetailDialog
from ui.scrollable_table import ScrollableTableView

class PatientsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_patients()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Compact toolbar buttons: the default 20px horizontal padding plus a
        # 16px icon made this row demand ~1300px in French, clipping the view.
        compact = "padding: 7px 12px; font-size: 12px; font-weight: 600; border-radius: 6px;"
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(tr("Search by name, insurer or member number..."))
        self.search_input.setMinimumWidth(60)
        self.search_input.textChanged.connect(self.load_patients)
        
        # Search button
        search_btn = QPushButton("Search")
        search_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        search_btn.setIconSize(QSize(16, 16))
        search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                {compact}
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT};
            }}
        """)
        search_btn.clicked.connect(self.load_patients)
        
        add_btn = QPushButton("Add Patient")
        add_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        add_btn.setIconSize(QSize(16, 16))
        add_btn.setStyleSheet(f"{compact} border: none; background-color: {Theme.PRIMARY}; color: white;")
        add_btn.clicked.connect(self.show_add_patient_dialog)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setProperty("class", "secondary")
        edit_btn.setStyleSheet(
            f"border: 1px solid #CBD5E1; background-color: #FFFFFF; color: {Theme.TEXT_PRIMARY}; {compact}")
        edit_btn.clicked.connect(self.edit_patient)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setProperty("class", "danger")
        delete_btn.setStyleSheet(f"background-color: {Theme.ERROR}; color: white; border: none; {compact}")
        delete_btn.clicked.connect(self.delete_patient)
        
        # Clinical buttons
        allergies_btn = QPushButton("Allergies")
        allergies_btn.setStyleSheet(
            f"border: 1px solid #CBD5E1; background-color: #FFFFFF; color: {Theme.TEXT_PRIMARY}; {compact}")
        allergies_btn.clicked.connect(self.manage_allergies)
        
        vitals_btn = QPushButton("Vitals")
        vitals_btn.setStyleSheet(
            f"border: 1px solid #CBD5E1; background-color: #FFFFFF; color: {Theme.TEXT_PRIMARY}; {compact}")
        vitals_btn.clicked.connect(self.record_vitals)
        
        toolbar.addWidget(self.search_input, 1)
        toolbar.addWidget(search_btn)
        toolbar.addStretch()
        toolbar.addWidget(allergies_btn)
        toolbar.addWidget(vitals_btn)
        toolbar.addWidget(edit_btn)
        toolbar.addWidget(delete_btn)
        toolbar.addWidget(add_btn)
        
        layout.addLayout(toolbar)

        # Table
        self.table = ScrollableTableView()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(f"alternate-background-color: {Theme.BACKGROUND};")
        
        
        self.model = QStandardItemModel()
        self.model.setHorizontalHeaderLabels(["First Name", "Last Name", "DOB", "Phone", "Email", "Insurance", "Action"])
        self.table.setModel(self.model)
        patients_header = self.table.horizontalHeader()
        # Fixed widths (including the 20px cell padding) so the table scrolls
        # sideways rather than squeezing names and insurers to a few characters.
        for col, width in {0: 130, 1: 140, 2: 118, 3: 125, 4: 190, 5: 210, 6: 80}.items():
            patients_header.setSectionResizeMode(col, QHeaderView.Interactive)
            self.table.setColumnWidth(col, width)
        
        # Connect click handler for Action column and double click for entire row
        self.table.clicked.connect(self.handle_table_click)
        self.table.doubleClicked.connect(lambda idx: self.show_patient_detail(self.model.item(idx.row(), 0).data(Qt.UserRole)))
        
        layout.addWidget(self.table)

    def load_patients(self):
        search_text = self.search_input.text().strip()
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            query = ("SELECT id, first_name, last_name, date_of_birth, phone, email, "
                     "insurance_provider, insurance_member_no FROM Patient")
            params = []
            
            if search_text:
                query += (" WHERE first_name LIKE ? OR last_name LIKE ?"
                          " OR IFNULL(insurance_provider, '') LIKE ?"
                          " OR IFNULL(insurance_member_no, '') LIKE ?")
                wildcard = f"%{search_text}%"
                params = [wildcard, wildcard, wildcard, wildcard]
                
            query += " ORDER BY last_name, first_name"
            cursor.execute(query, params)
            patients = cursor.fetchall()
            
            self.model.removeRows(0, self.model.rowCount())
            
            for p in patients:
                provider = (p['insurance_provider'] or "").strip()
                member = (p['insurance_member_no'] or "").strip()
                if provider and member:
                    insurance_text = f"{provider} · {member}"
                else:
                    insurance_text = provider or member or tr("Self-pay")

                insurance_item = QStandardItem(insurance_text)
                insurance_item.setToolTip(insurance_text)
                if insurance_text == tr("Self-pay"):
                    insurance_item.setForeground(QColor("#94A3B8"))
                else:
                    insurance_item.setForeground(QColor("#1D4ED8"))

                row = [
                    QStandardItem(p['first_name']),
                    QStandardItem(p['last_name']),
                    QStandardItem(p['date_of_birth'] or ""),
                    QStandardItem(p['phone'] or ""),
                    QStandardItem(p['email'] or ""),
                    insurance_item,
                    QStandardItem(tr("👁 View"))
                ]
                # Store patient ID in the first item's data
                row[0].setData(p['id'], Qt.UserRole)
                for item in row:
                    item.setEditable(False)
                self.model.appendRow(row)
                
        except Exception as e:
            print(f"Error loading patients: {e}")
        finally:
            if conn:
                conn.close()

    def show_add_patient_dialog(self):
        dialog = PatientDialog(self)
        if dialog.exec():
            self.load_patients()

    def get_selected_patient_id(self):
        """Helper to get the ID of the selected patient"""
        selected_indexes = self.table.selectionModel().selectedRows()
        if not selected_indexes:
            return None
        
        row = selected_indexes[0].row()
        # Retrieve ID from UserRole data of the first column (where we stored it)
        patient_id = self.model.item(row, 0).data(Qt.UserRole)
        return patient_id

    def edit_patient(self):
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            QMessageBox.warning(self, "Warning", "Please select a patient to edit")
            return
            
        dialog = PatientDialog(self, patient_id)
        if dialog.exec():
            self.load_patients()

    def delete_patient(self):
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            QMessageBox.warning(self, "Warning", "Please select a patient to delete")
            return
            
        # Get name for confirmation message (row must be valid if we got an ID)
        selected_indexes = self.table.selectionModel().selectedRows()
        row = selected_indexes[0].row()
        name = f"{self.model.item(row, 0).text()} {self.model.item(row, 1).text()}"  # First Name + Last Name
        
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            f"Are you sure you want to delete patient {name}?\nThis will also delete all their appointments and notes.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            conn = None
            try:
                conn = db_manager.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Patient WHERE id = ?", (patient_id,))
                conn.commit()
                self.load_patients()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete patient: {e}")
            finally:
                if conn:
                    conn.close()
    
    def handle_table_click(self, index):
        """Handle clicks on the table, specifically the Action column"""
        if index.column() == self.model.columnCount() - 1:  # Action column
            row = index.row()
            # Get patient ID from first item's UserRole data
            patient_id = self.model.item(row, 0).data(Qt.UserRole)
            self.show_patient_detail(patient_id)
    
    def show_patient_detail(self, patient_id):
        """Show detailed patient information dialog"""
        if not patient_id:
            return
        dialog = PatientDetailDialog(patient_id, parent=self)
        dialog.exec()
        self.load_patients()

    def manage_allergies(self):
        """Manage allergies for selected patient"""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            QMessageBox.warning(self, "Warning", "Please select a patient first")
            return
        
        # Get name for window title
        selected_indexes = self.table.selectionModel().selectedRows()
        row = selected_indexes[0].row()
        patient_name = f"{self.model.item(row, 0).text()} {self.model.item(row, 1).text()}"
        
        from ui.allergy_dialog import AllergyDialog
        dialog = AllergyDialog(patient_id)
        dialog.setWindowTitle(f"Manage Allergies - {patient_name}")
        dialog.exec()
    
    def record_vitals(self):
        """Record vital signs for selected patient"""
        patient_id = self.get_selected_patient_id()
        if not patient_id:
            QMessageBox.warning(self, "Warning", "Please select a patient first")
            return
        
        # Get name for window title
        selected_indexes = self.table.selectionModel().selectedRows()
        row = selected_indexes[0].row()
        patient_name = f"{self.model.item(row, 0).text()} {self.model.item(row, 1).text()}"
        
        from ui.vitals_dialog import VitalsDialog
        dialog = VitalsDialog(patient_id)
        dialog.setWindowTitle(f"Record Vital Signs - {patient_name}")
        if dialog.exec():
            QMessageBox.information(self, "Success", "Vital signs recorded successfully!")

class PatientDialog(QDialog):
    def __init__(self, parent=None, patient_id=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle("Edit Patient" if patient_id else "Add New Patient")
        self.resize(440, 720)
        self.setStyleSheet(Theme.STYLESHEET)
        
        self.setup_ui()
        if patient_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        self.first_name = QLineEdit()
        self.first_name.setPlaceholderText("e.g. John")
        self.last_name = QLineEdit()
        self.last_name.setPlaceholderText("e.g. Doe")
        self.dob = QDateEdit(QDate.currentDate())
        self.dob.setCalendarPopup(True)
        self.dob.setDisplayFormat("yyyy-MM-dd")
        self.gender = QComboBox()
        self.gender.addItems(["", "Male", "Female", "Other"])
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("e.g. 555-0123")
        self.email = QLineEdit()
        self.email.setPlaceholderText("e.g. john.doe@example.com")
        self.address = QLineEdit()
        self.address.setPlaceholderText("e.g. 123 Main St")
        self.medical_history = QLineEdit()
        self.medical_history.setPlaceholderText("e.g. Diabetes, Hypertension")
        self.emergency_contact = QLineEdit()
        self.emergency_contact.setPlaceholderText("e.g. Jane Doe")
        self.emergency_phone = QLineEdit()
        self.emergency_phone.setPlaceholderText("e.g. 555-0124")
        self.insurance_provider = QLineEdit()
        self.insurance_provider.setPlaceholderText(tr("e.g. Allianz, CNAM, AXA - leave blank if none"))
        self.insurance_member_no = QLineEdit()
        self.insurance_member_no.setPlaceholderText(tr("e.g. 123-456-789 - leave blank if none"))
        self.insurance_coverage = QDoubleSpinBox()
        self.insurance_coverage.setRange(0.0, 100.0)
        self.insurance_coverage.setDecimals(0)
        self.insurance_coverage.setSuffix(" %")
        self.insurance_coverage.setMaximumWidth(110)
        # Always editable: every insurer sets its own rate, so there is no clinic
        # default to fall back on.
        self.insurance_coverage.setToolTip(
            tr("Share of each invoice this insurer pays. 0% means the patient pays everything."))
        
        form_layout.addRow("First Name:", self.first_name)
        form_layout.addRow("Last Name:", self.last_name)
        form_layout.addRow("Date of Birth:", self.dob)
        form_layout.addRow("Gender:", self.gender)
        form_layout.addRow("Phone:", self.phone)
        form_layout.addRow("Email:", self.email)
        form_layout.addRow("Address:", self.address)
        form_layout.addRow("Medical History:", self.medical_history)
        form_layout.addRow("Emergency Contact:", self.emergency_contact)
        form_layout.addRow("Emergency Phone:", self.emergency_phone)
        layout.addLayout(form_layout)

        # --- Insurance (optional) -------------------------------------------
        # A separate form layout so the note can sit between the two groups.
        insurance_sep = QFrame()
        insurance_sep.setFixedHeight(1)
        insurance_sep.setStyleSheet("background-color: #E2E8F0; border: none;")
        layout.addSpacing(10)
        layout.addWidget(insurance_sep)
        layout.addSpacing(4)

        insurance_note = QLabel(tr("Optional. Leave both fields blank if the patient has no insurance."))
        insurance_note.setWordWrap(True)
        insurance_note.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        insurance_note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        layout.addWidget(insurance_note)

        insurance_form = QFormLayout()
        insurance_form.addRow("Insurance Provider:", self.insurance_provider)
        insurance_form.addRow("Insurance Member No.:", self.insurance_member_no)
        insurance_form.addRow("Coverage:", self.insurance_coverage)
        layout.addLayout(insurance_form)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_patient)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def load_data(self):
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Patient WHERE id = ?", (self.patient_id,))
            patient = cursor.fetchone()
            
            if patient:
                self.first_name.setText(patient['first_name'])
                self.last_name.setText(patient['last_name'])
                if patient['date_of_birth']:
                    self.dob.setDate(QDate.fromString(patient['date_of_birth'], "yyyy-MM-dd"))
                set_combo_value(self.gender, patient['gender'] or "")
                self.phone.setText(patient['phone'] or "")
                self.email.setText(patient['email'] or "")
                self.address.setText(patient['address'] or "")
                self.medical_history.setText(patient['medical_history'] or "")
                self.emergency_contact.setText(patient['emergency_contact'] or "")
                self.emergency_phone.setText(patient['emergency_phone'] or "")
                self.insurance_provider.setText(patient['insurance_provider'] or "")
                self.insurance_member_no.setText(patient['insurance_member_no'] or "")
                if patient['insurance_coverage_pct'] is not None:
                    self.insurance_coverage.setValue(float(patient['insurance_coverage_pct']))
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load patient data: {e}")
        finally:
            if conn:
                conn.close()

    def save_patient(self):
        if not self.first_name.text() or not self.last_name.text():
            QMessageBox.warning(self, "Error", "First and Last Name are required")
            return
            
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            if self.patient_id:
                # Update
                cursor.execute("""
                    UPDATE Patient 
                    SET first_name=?, last_name=?, date_of_birth=?, gender=?, 
                        phone=?, email=?, address=?, medical_history=?, 
                        emergency_contact=?, emergency_phone=?,
                        insurance_provider=?, insurance_member_no=?, insurance_coverage_pct=?
                    WHERE id=?
                """, (
                    self.first_name.text(),
                    self.last_name.text(),
                    self.dob.date().toString("yyyy-MM-dd"),
                    combo_value(self.gender),
                    self.phone.text(),
                    self.email.text(),
                    self.address.text(),
                    self.medical_history.text(),
                    self.emergency_contact.text(),
                    self.emergency_phone.text(),
                    self.insurance_provider.text().strip(),
                    self.insurance_member_no.text().strip(),
                    self.insurance_coverage.value(),
                    self.patient_id
                ))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO Patient (first_name, last_name, date_of_birth, gender, phone, email, address, medical_history, emergency_contact, emergency_phone, insurance_provider, insurance_member_no, insurance_coverage_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    self.first_name.text(),
                    self.last_name.text(),
                    self.dob.date().toString("yyyy-MM-dd"),
                    combo_value(self.gender),
                    self.phone.text(),
                    self.email.text(),
                    self.address.text(),
                    self.medical_history.text(),
                    self.emergency_contact.text(),
                    self.emergency_phone.text(),
                    self.insurance_provider.text().strip(),
                    self.insurance_member_no.text().strip(),
                    self.insurance_coverage.value()
                ))
            
            conn.commit()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save patient: {e}")
        finally:
            if conn:
                conn.close()


