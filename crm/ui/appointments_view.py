
from utils.localization import combo_value, set_combo_value, tr
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableView, QHeaderView, QDialog, QFormLayout, 
                               QComboBox, QDateTimeEdit, QLineEdit, QMessageBox, 
                               QAbstractItemView, QStyle)
from PySide6.QtCore import Qt, QDateTime, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem
from styles.theme import Theme
from data import db_manager

class AppointmentsView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_appointments()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Search functionality
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by patient name...")
        self.search_input.textChanged.connect(self.load_appointments)
        
        search_btn = QPushButton("Search")
        search_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogContentsView))
        search_btn.setIconSize(QSize(16, 16))
        search_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
            QPushButton:pressed {{
                background-color: {Theme.ACCENT};
            }}
        """)
        search_btn.clicked.connect(self.load_appointments)
        
        add_btn = QPushButton("New Appointment")
        add_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        add_btn.setIconSize(QSize(16, 16))
        add_btn.clicked.connect(self.show_add_dialog)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setProperty("class", "secondary")
        edit_btn.clicked.connect(self.edit_appointment)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setProperty("class", "danger")
        delete_btn.clicked.connect(self.delete_appointment)
        
        toolbar.addWidget(self.search_input)
        toolbar.addWidget(search_btn)
        toolbar.addStretch()
        toolbar.addWidget(edit_btn)
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
        self.model.setHorizontalHeaderLabels(["ID", "Date/Time", "Patient", "Doctor", "Status", "Reason"])
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True) # Hide ID column
        
        layout.addWidget(self.table)

    def load_appointments(self):
        search_text = self.search_input.text().strip() if hasattr(self, 'search_input') else ''
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            if search_text:
                cursor.execute("""
                    SELECT a.id, a.datetime, p.first_name, p.last_name, a.doctor_name, a.status, a.reason
                    FROM Appointment a
                    JOIN Patient p ON a.patient_id = p.id
                    WHERE p.first_name LIKE ? OR p.last_name LIKE ?
                    ORDER BY a.datetime DESC
                """, (f'%{search_text}%', f'%{search_text}%'))
            else:
                cursor.execute("""
                    SELECT a.id, a.datetime, p.first_name, p.last_name, a.doctor_name, a.status, a.reason
                    FROM Appointment a
                    JOIN Patient p ON a.patient_id = p.id
                    ORDER BY a.datetime DESC
                """)
            appointments = cursor.fetchall()
            
            self.model.removeRows(0, self.model.rowCount())
            
            for appt in appointments:
                row = [
                    QStandardItem(str(appt['id'])),
                    QStandardItem(appt['datetime']),
                    QStandardItem(f"{appt['first_name']} {appt['last_name']}"),
                    QStandardItem(appt['doctor_name']),
                    QStandardItem(tr(appt['status'])),
                    QStandardItem(appt['reason'] or "")
                ]
                for item in row:
                    item.setEditable(False)
                self.model.appendRow(row)
                
        except Exception as e:
            print(f"Error loading appointments: {e}")
        finally:
            if conn:
                conn.close()

    def show_add_dialog(self):
        dialog = AppointmentDialog(self)
        if dialog.exec():
            self.load_appointments()

    def edit_appointment(self):
        selected_indexes = self.table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select an appointment to edit")
            return
            
        row = selected_indexes[0].row()
        appt_id = self.model.item(row, 0).text()
        
        dialog = AppointmentDialog(self, appt_id)
        if dialog.exec():
            self.load_appointments()

    def delete_appointment(self):
        selected_indexes = self.table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select an appointment to delete")
            return
            
        row = selected_indexes[0].row()
        appt_id = self.model.item(row, 0).text()
        
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this appointment?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            conn = None
            try:
                conn = db_manager.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Appointment WHERE id = ?", (appt_id,))
                conn.commit()
                self.load_appointments()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete appointment: {e}")
            finally:
                if conn:
                    conn.close()

class AppointmentDialog(QDialog):
    def __init__(self, parent=None, appt_id=None):
        super().__init__(parent)
        self.appt_id = appt_id
        self.setWindowTitle("Edit Appointment" if appt_id else "Schedule Appointment")
        self.resize(400, 400)
        self.setStyleSheet(Theme.STYLESHEET)
        
        self.setup_ui()
        if appt_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form_layout = QFormLayout()
        
        # Patient Selection
        self.patient_combo = QComboBox()
        self.load_patients()
        
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("yyyy-MM-dd HH:mm")
        self.datetime_edit.setCalendarPopup(True)
        
        self.doctor_input = QLineEdit()
        self.doctor_input.setPlaceholderText("e.g. Dr. Smith")
        # Fetch current logged-in doctor's name
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT first_name, last_name FROM Users LIMIT 1")
            user = cursor.fetchone()
            if user:
                self.doctor_input.setText(f"Dr. {user['first_name']} {user['last_name']}")
            else:
                self.doctor_input.setText("Dr. Default")
            conn.close()
        except:
            self.doctor_input.setText("Dr. Default")
        
        self.reason_input = QLineEdit()
        self.reason_input.setPlaceholderText("e.g. Annual Checkup")
        
        self.status_combo = QComboBox()
        self.status_combo.addItems(['SCHEDULED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW'])
        
        form_layout.addRow("Patient:", self.patient_combo)
        form_layout.addRow("Date/Time:", self.datetime_edit)
        form_layout.addRow("Doctor:", self.doctor_input)
        form_layout.addRow("Reason:", self.reason_input)
        if self.appt_id:
            form_layout.addRow("Status:", self.status_combo)
        
        layout.addLayout(form_layout)
        
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.save_appointment)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        layout.addLayout(btn_layout)

    def load_patients(self):
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, first_name, last_name FROM Patient")
            patients = cursor.fetchall()
            
            for p in patients:
                self.patient_combo.addItem(f"{p['first_name']} {p['last_name']}", p['id'])
                
        except Exception as e:
            print(f"Error loading patients for combo: {e}")
        finally:
            if conn:
                conn.close()

    def load_data(self):
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM Appointment WHERE id = ?", (self.appt_id,))
            appt = cursor.fetchone()
            
            if appt:
                # Set patient
                index = self.patient_combo.findData(appt['patient_id'])
                if index >= 0:
                    self.patient_combo.setCurrentIndex(index)
                
                # Set datetime
                dt = QDateTime.fromString(appt['datetime'], "yyyy-MM-dd HH:mm")
                self.datetime_edit.setDateTime(dt)
                
                self.doctor_input.setText(appt['doctor_name'])
                self.reason_input.setText(appt['reason'] or "")
                set_combo_value(self.status_combo, appt['status'])
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load appointment data: {e}")
        finally:
            if conn:
                conn.close()

    def save_appointment(self):
        patient_id = self.patient_combo.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Error", "Please select a patient")
            return
            
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            dt_str = self.datetime_edit.dateTime().toString("yyyy-MM-dd HH:mm")
            
            if self.appt_id:
                # Update
                cursor.execute("""
                    UPDATE Appointment 
                    SET patient_id=?, doctor_name=?, datetime=?, status=?, reason=?
                    WHERE id=?
                """, (
                    patient_id,
                    self.doctor_input.text(),
                    dt_str,
                    combo_value(self.status_combo),
                    self.reason_input.text(),
                    self.appt_id
                ))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO Appointment (patient_id, doctor_name, datetime, status, reason)
                    VALUES (?, ?, ?, 'SCHEDULED', ?)
                """, (
                    patient_id,
                    self.doctor_input.text(),
                    dt_str,
                    self.reason_input.text()
                ))
            
            conn.commit()
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save appointment: {e}")
        finally:
            if conn:
                conn.close()
