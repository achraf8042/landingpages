from utils.localization import combo_value, find_combo_value
"""
Allergy Management Dialog
Allows adding/editing patient allergies
"""

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                               QTextEdit, QComboBox, QDateEdit, QCheckBox,
                               QPushButton, QMessageBox, QHBoxLayout, QLabel)
from PySide6.QtCore import Qt, QDate
from styles.theme import Theme
from data import db_manager

class AllergyDialog(QDialog):
    def __init__(self, patient_id, allergy_id=None, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.allergy_id = allergy_id
        self.setWindowTitle("Edit Allergy" if allergy_id else "Add Allergy")
        self.resize(450, 400)
        self.setStyleSheet(Theme.STYLESHEET)
        
        self.setup_ui()
        if allergy_id:
            self.load_data()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Form
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Allergen
        self.allergen_input = QLineEdit()
        self.allergen_input.setPlaceholderText("e.g., Penicillin, Peanuts, Latex")
        form_layout.addRow("Allergen *:", self.allergen_input)
        
        # Reaction
        self.reaction_input = QLineEdit()
        self.reaction_input.setPlaceholderText("e.g., Rash, Hives, Anaphylaxis")
        form_layout.addRow("Reaction:", self.reaction_input)
        
        # Severity
        self.severity_combo = QComboBox()
        self.severity_combo.addItems(['Unknown', 'Mild', 'Moderate', 'Severe'])
        form_layout.addRow("Severity *:", self.severity_combo)
        
        # Onset Date
        self.onset_date = QDateEdit()
        self.onset_date.setCalendarPopup(True)
        self.onset_date.setDate(QDate.currentDate())
        self.onset_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Onset Date:", self.onset_date)
        
        # Notes
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Additional notes...")
        self.notes_input.setMaximumHeight(80)
        form_layout.addRow("Notes:", self.notes_input)
        
        # Active checkbox
        self.active_checkbox = QCheckBox("Active Allergy")
        self.active_checkbox.setChecked(True)
        form_layout.addRow("", self.active_checkbox)
        
        layout.addLayout(form_layout)
        
        # Severity indicator
        severity_label = QLabel("⚠️ Severe allergies will show prominent warnings")
        severity_label.setStyleSheet(f"color: {Theme.WARNING}; font-size: 12px; font-style: italic;")
        layout.addWidget(severity_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.clicked.connect(self.reject)
        
        save_btn = QPushButton("Save Allergy")
        save_btn.clicked.connect(self.save_allergy)
        save_btn.setCursor(Qt.PointingHandCursor)
        
        button_layout.addWidget(cancel_btn)
        button_layout.addWidget(save_btn)
        layout.addLayout(button_layout)
    
    def load_data(self):
        """Load existing allergy data"""
        allergies = db_manager.get_patient_allergies(self.patient_id)
        allergy = next((a for a in allergies if a['id'] == self.allergy_id), None)
        
        if allergy:
            self.allergen_input.setText(allergy['allergen'] or '')
            self.reaction_input.setText(allergy['reaction'] or '')
            
            severity_index = find_combo_value(self.severity_combo, allergy['severity'] or 'Unknown')
            if severity_index >= 0:
                self.severity_combo.setCurrentIndex(severity_index)
            
            if allergy['onset_date']:
                self.onset_date.setDate(QDate.fromString(allergy['onset_date'], 'yyyy-MM-dd'))
            
            self.notes_input.setPlainText(allergy['notes'] or '')
            self.active_checkbox.setChecked(bool(allergy['is_active']))
    
    def save_allergy(self):
        # Validate
        allergen = self.allergen_input.text().strip()
        if not allergen:
            QMessageBox.warning(self, "Validation Error", "Please enter the allergen name.")
            self.allergen_input.setFocus()
            return
        
        reaction = self.reaction_input.text().strip()
        severity = combo_value(self.severity_combo)
        onset_date = self.onset_date.date().toString('yyyy-MM-dd')
        notes = self.notes_input.toPlainText().strip()
        is_active = 1 if self.active_checkbox.isChecked() else 0
        
        try:
            if self.allergy_id:
                # Update
                success, message = db_manager.update_allergy(
                    self.allergy_id, allergen, reaction, severity, onset_date, notes, is_active
                )
            else:
                # Add new
                success, message = db_manager.add_allergy(
                    self.patient_id, allergen, reaction, severity, onset_date, notes
                )
            
            if success:
                QMessageBox.information(self, "Success", message)
                self.accept()
            else:
                QMessageBox.critical(self, "Error", message)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save allergy: {str(e)}")
