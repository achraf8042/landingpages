"""
Vital Signs Entry Dialog
Quick entry form for recording patient vital signs
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QTextEdit, QDateEdit, QPushButton, QMessageBox,
                               QHBoxLayout, QLabel, QFrame)
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QDoubleValidator, QIntValidator
from styles.theme import Theme
from data import db_manager

class VitalsDialog(QDialog):
    def __init__(self, patient_id, appointment_id=None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.appointment_id = appointment_id
        self.setWindowTitle("Record Vital Signs")
        self.resize(500, 550)
        self.setStyleSheet(Theme.STYLESHEET)
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header
        header = QLabel("Vital Signs Entry")
        header.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.PRIMARY};")
        layout.addWidget(header)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(10)
        
        # Date
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        self.date_input.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Date:", self.date_input)
        
        # Blood Pressure
        bp_layout = QHBoxLayout()
        self.systolic_input = QLineEdit()
        self.systolic_input.setPlaceholderText("120")
        self.systolic_input.setValidator(QIntValidator(50, 250))
        self.systolic_input.setMaximumWidth(80)
        
        self.diastolic_input = QLineEdit()
        self.diastolic_input.setPlaceholderText("80")
        self.diastolic_input.setValidator(QIntValidator(30, 150))
        self.diastolic_input.setMaximumWidth(80)
        
        bp_layout.addWidget(self.systolic_input)
        bp_layout.addWidget(QLabel("/"))
        bp_layout.addWidget(self.diastolic_input)
        bp_layout.addWidget(QLabel("mmHg"))
        bp_layout.addStretch()
        form_layout.addRow("Blood Pressure:", bp_layout)
        
        # Heart Rate
        self.hr_input = QLineEdit()
        self.hr_input.setPlaceholderText("72")
        self.hr_input.setValidator(QIntValidator(30, 200))
        self.hr_input.setMaximumWidth(100)
        hr_layout = QHBoxLayout()
        hr_layout.addWidget(self.hr_input)
        hr_layout.addWidget(QLabel("BPM"))
        hr_layout.addStretch()
        form_layout.addRow("Heart Rate:", hr_layout)
        
        # Temperature
        self.temp_input = QLineEdit()
        self.temp_input.setPlaceholderText("37.0")
        self.temp_input.setValidator(QDoubleValidator(35.0, 42.0, 1))
        self.temp_input.setMaximumWidth(100)
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(self.temp_input)
        temp_layout.addWidget(QLabel("°C"))
        temp_layout.addStretch()
        form_layout.addRow("Temperature:", temp_layout)
        
        # Weight
        self.weight_input = QLineEdit()
        self.weight_input.setPlaceholderText("70")
        self.weight_input.setValidator(QDoubleValidator(0.0, 500.0, 1))
        self.weight_input.setMaximumWidth(100)
        self.weight_input.textChanged.connect(self.calculate_bmi)
        weight_layout = QHBoxLayout()
        weight_layout.addWidget(self.weight_input)
        weight_layout.addWidget(QLabel("kg"))
        weight_layout.addStretch()
        form_layout.addRow("Weight:", weight_layout)
        
        # Height
        self.height_input = QLineEdit()
        self.height_input.setPlaceholderText("170")
        self.height_input.setValidator(QDoubleValidator(0.0, 300.0, 1))
        self.height_input.setMaximumWidth(100)
        self.height_input.textChanged.connect(self.calculate_bmi)
        height_layout = QHBoxLayout()
        height_layout.addWidget(self.height_input)
        height_layout.addWidget(QLabel("cm"))
        height_layout.addStretch()
        form_layout.addRow("Height:", height_layout)
        
        # BMI (calculated)
        self.bmi_label = QLabel("--")
        self.bmi_label.setStyleSheet(f"font-weight: bold; color: {Theme.PRIMARY};")
        form_layout.addRow("BMI:", self.bmi_label)
        
        # SpO2
        self.spo2_input = QLineEdit()
        self.spo2_input.setPlaceholderText("98")
        self.spo2_input.setValidator(QIntValidator(50, 100))
        self.spo2_input.setMaximumWidth(100)
        spo2_layout = QHBoxLayout()
        spo2_layout.addWidget(self.spo2_input)
        spo2_layout.addWidget(QLabel("%"))
        spo2_layout.addStretch()
        form_layout.addRow("SpO₂:", spo2_layout)
        
        # Respiratory Rate
        self.rr_input = QLineEdit()
        self.rr_input.setPlaceholderText("16")
        self.rr_input.setValidator(QIntValidator(5, 60))
        self.rr_input.setMaximumWidth(100)
        rr_layout = QHBoxLayout()
        rr_layout.addWidget(self.rr_input)
        rr_layout.addWidget(QLabel("breaths/min"))
        rr_layout.addStretch()
        form_layout.addRow("Respiratory Rate:", rr_layout)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional notes...")
        self.notes_input.setMaximumHeight(60)
        form_layout.addRow("Notes:", self.notes_input)
        
        layout.addLayout(form_layout)
        
        # Info label
        info_label = QLabel("At least one vital sign must be entered")
        info_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px; font-style: italic;")
        layout.addWidget(info_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Vital Signs")
        save_btn.clicked.connect(self.save_vitals)
        save_btn.setCursor(Qt.PointingHandCursor)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
    
    def calculate_bmi(self):
        """Auto-calculate BMI when weight/height change"""
        try:
            weight_text = self.weight_input.text().strip()
            height_text = self.height_input.text().strip()
            
            if weight_text and height_text:
                weight = float(weight_text)
                height = float(height_text)
                
                if weight > 0 and height > 0:
                    height_m = height / 100  # Convert cm to m
                    bmi = weight / (height_m ** 2)
                    self.bmi_label.setText(f"{bmi:.1f}")
                    
                    # Color code BMI
                    if bmi < 18.5:
                        self.bmi_label.setStyleSheet(f"font-weight: bold; color: {Theme.WARNING};")
                    elif 18.5 <= bmi < 25:
                        self.bmi_label.setStyleSheet(f"font-weight: bold; color: {Theme.SUCCESS};")
                    elif 25 <= bmi < 30:
                        self.bmi_label.setStyleSheet(f"font-weight: bold; color: {Theme.WARNING};")
                    else:
                        self.bmi_label.setStyleSheet(f"font-weight: bold; color: {Theme.ERROR};")
                    return
            
            self.bmi_label.setText("--")
            self.bmi_label.setStyleSheet(f"font-weight: bold; color: {Theme.PRIMARY};")
        except:
            self.bmi_label.setText("--")
    
    def save_vitals(self):
        # Get values
        measurement_date = self.date_input.date().toString('yyyy-MM-dd')
        
        systolic = int(self.systolic_input.text()) if self.systolic_input.text().strip() else None
        diastolic = int(self.diastolic_input.text()) if self.diastolic_input.text().strip() else None
        hr = int(self.hr_input.text()) if self.hr_input.text().strip() else None
        temp = float(self.temp_input.text()) if self.temp_input.text().strip() else None
        weight = float(self.weight_input.text()) if self.weight_input.text().strip() else None
        height = float(self.height_input.text()) if self.height_input.text().strip() else None
        spo2 = int(self.spo2_input.text()) if self.spo2_input.text().strip() else None
        rr = int(self.rr_input.text()) if self.rr_input.text().strip() else None
        notes = self.notes_input.toPlainText().strip()
        
        # Validate: at least one vital must be entered
        if not any([systolic, diastolic, hr, temp, weight, height, spo2, rr]):
            QMessageBox.warning(self, "Validation Error", "Please enter at least one vital sign.")
            return
        
        # Validate BP: if one is entered, both must be
        if (systolic and not diastolic) or (diastolic and not systolic):
            QMessageBox.warning(self, "Validation Error", 
                              "Both systolic and diastolic blood pressure values are required.")
            return
        
        # Validate BP logic
        if systolic and diastolic and systolic <= diastolic:
            QMessageBox.warning(self, "Validation Error", 
                              "Systolic blood pressure must be greater than diastolic.")
            return
        
        try:
            success, message = db_manager.add_vital_signs(
                self.patient_id,
                measurement_date,
                systolic_bp=systolic,
                diastolic_bp=diastolic,
                heart_rate=hr,
                temperature=temp,
                weight=weight,
                height=height,
                oxygen_saturation=spo2,
                respiratory_rate=rr,
                notes=notes,
                appointment_id=self.appointment_id
            )
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save vital signs: {str(e)}")
