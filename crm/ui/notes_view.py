from utils.localization import tr, manager
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableView, QHeaderView, QDialog, QFormLayout, 
                               QComboBox, QTextEdit, QDateEdit, QMessageBox, 
                               QAbstractItemView, QStyle, QLineEdit, QLabel, QCheckBox, QFileDialog, QFrame)
from PySide6.QtCore import Qt, QDate, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem, QTextDocument
from PySide6.QtPrintSupport import QPrinter
from styles.theme import Theme
from data import db_manager
from datetime import datetime

class NotesView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.load_notes()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        
        # Search functionality
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by patient name...")
        self.search_input.textChanged.connect(self.load_notes)
        
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
        search_btn.clicked.connect(self.load_notes)
        
        add_btn = QPushButton("New Note")
        add_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
        add_btn.setIconSize(QSize(16, 16))
        add_btn.clicked.connect(self.show_add_dialog)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setIcon(self.style().standardIcon(QStyle.SP_FileDialogDetailedView))
        edit_btn.setIconSize(QSize(16, 16))
        edit_btn.setProperty("class", "secondary")
        edit_btn.clicked.connect(self.edit_note)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setIcon(self.style().standardIcon(QStyle.SP_TrashIcon))
        delete_btn.setIconSize(QSize(16, 16))
        delete_btn.setProperty("class", "danger")
        delete_btn.clicked.connect(self.delete_note)
        
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
        self.model.setHorizontalHeaderLabels(["ID", "Date", "Patient", "Assessment", "Status", "Action"])
        self.table.setModel(self.model)
        self.table.setColumnHidden(0, True) # Hide ID column
        
        # Connect click handler for Action column
        self.table.clicked.connect(self.handle_table_click)
        
        layout.addWidget(self.table)

    def load_notes(self):
        search_text = self.search_input.text().strip() if hasattr(self, 'search_input') else ''
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            if search_text:
                cursor.execute("""
                    SELECT n.id, n.note_date, p.first_name, p.last_name, n.assessment, n.status
                    FROM ClinicalNote n
                    JOIN Patient p ON n.patient_id = p.id
                    WHERE p.first_name LIKE ? OR p.last_name LIKE ?
                    ORDER BY n.note_date DESC
                """, (f'%{search_text}%', f'%{search_text}%'))
            else:
                cursor.execute("""
                    SELECT n.id, n.note_date, p.first_name, p.last_name, n.assessment, n.status
                    FROM ClinicalNote n
                    JOIN Patient p ON n.patient_id = p.id
                    ORDER BY n.note_date DESC
                """)
            notes = cursor.fetchall()
            
            self.model.removeRows(0, self.model.rowCount())
            
            for note in notes:
                row = [
                    QStandardItem(str(note['id'])),
                    QStandardItem(note['note_date']),
                    QStandardItem(f"{note['first_name']} {note['last_name']}"),
                    QStandardItem(note['assessment'] or ""),
                    QStandardItem(tr(note['status'] or "DRAFT")),
                    QStandardItem(tr("👁 View Doc"))  # Action button
                ]
                for item in row:
                    item.setEditable(False)
                self.model.appendRow(row)
                
        except Exception as e:
            print(f"Error loading notes: {e}")
        finally:
            if conn:
                conn.close()
    
    def handle_table_click(self, index):
        """Handle clicks on the table, specifically the Action column"""
        if index.column() == 5:  # Action column
            row = index.row()
            note_id = self.model.item(row, 0).text()
            self.view_note(note_id)
    
    def view_note(self, note_id):
        """Open document page for patient's notes"""
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT patient_id FROM ClinicalNote WHERE id = ?", (note_id,))
            result = cursor.fetchone()
            if result:
                patient_id = result['patient_id']
                # Open document view
                doc_view = PatientNotesDocumentView(patient_id)
                doc_view.exec()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open document: {e}")
        finally:
            if conn:
                conn.close()

    def show_add_dialog(self):
        dialog = NoteDialog(self)
        if dialog.exec():
            self.load_notes()

    def edit_note(self):
        selected_indexes = self.table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select a note to edit")
            return
            
        row = selected_indexes[0].row()
        note_id = self.model.item(row, 0).text()
        
        dialog = NoteDialog(self, note_id)
        if dialog.exec():
            self.load_notes()

    def delete_note(self):
        selected_indexes = self.table.selectionModel().selectedRows()
        if not selected_indexes:
            QMessageBox.warning(self, "Warning", "Please select a note to delete")
            return
            
        row = selected_indexes[0].row()
        note_id = self.model.item(row, 0).text()
        
        confirm = QMessageBox.question(
            self, "Confirm Delete", 
            "Are you sure you want to delete this clinical note?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            conn = None
            try:
                conn = db_manager.get_db_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ClinicalNote WHERE id = ?", (note_id,))
                conn.commit()
                self.load_notes()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete note: {e}")
            finally:
                if conn:
                    conn.close()


class PatientNotesDocumentView(QDialog):
    """Document view showing all notes for a specific patient"""
    def __init__(self, patient_id, parent=None):
        super().__init__(parent)
        self.patient_id = patient_id
        manager().changed.connect(lambda locale: self.load_patient_notes())
        self.setWindowTitle("Patient Clinical Notes Document")
        self.resize(1000, 750)
        self.setStyleSheet(Theme.STYLESHEET)
        
        self.setup_ui()
        self.load_patient_notes()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Modern Header Section with gradient background
        header_container = QFrame()
        header_container.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PRIMARY},
                    stop:1 {Theme.PRIMARY_HOVER});
                border-radius: 0px;
                padding: 24px;
            }}
        """)
        header_layout = QVBoxLayout(header_container)
        
        # Title row
        title_row = QHBoxLayout()
        
        # Patient name with icon
        patient_info_container = QHBoxLayout()
        self.patient_name_label = QLabel()
        self.patient_name_label.setProperty("i18n_skip", True)
        self.patient_name_label.setStyleSheet("""
            font-size: 24px;
            font-weight: bold;
            color: white;
        """)
        # patient_info_container.addWidget(QLabel("📋"))
        patient_info_container.addWidget(self.patient_name_label)
        patient_info_container.addStretch()
        
        title_row.addLayout(patient_info_container)
        title_row.addStretch()
        
        # Export and Close buttons with modern styling
        buttons_container = QHBoxLayout()
        
        export_btn = QPushButton("Export to PDF")
        export_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #0F172A;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
                margin-right: 8px;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
            }
            QPushButton:pressed {
                background-color: #E2E8F0;
            }
        """)
        export_btn.clicked.connect(self.export_to_pdf)
        
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.3);
                border-color: white;
            }
            QPushButton:pressed {
                background-color: rgba(255, 255, 255, 0.15);
            }
        """)
        close_btn.clicked.connect(self.accept)
        
        buttons_container.addWidget(export_btn)
        buttons_container.addWidget(close_btn)
        title_row.addLayout(buttons_container)
        
        header_layout.addLayout(title_row)
        
        # Metadata row
        self.metadata_label = QLabel()
        self.metadata_label.setStyleSheet("""
            font-size: 13px;
            color: rgba(255, 255, 255, 0.9);
            margin-top: 8px;
        """)
        header_layout.addWidget(self.metadata_label)
        
        layout.addWidget(header_container)
        
        # Document content area with modern styling
        self.document_text = QTextEdit()
        self.document_text.setReadOnly(True)
        self.document_text.setStyleSheet("""
            QTextEdit {
                background-color: #F9FAFB;
                color: #1F2937;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                font-size: 13px;
                padding: 24px;
                border: none;
            }
        """)
        layout.addWidget(self.document_text)

    def load_patient_notes(self):
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            # Get patient info
            cursor.execute("SELECT first_name, last_name, date_of_birth, gender FROM Patient WHERE id = ?", (self.patient_id,))
            patient = cursor.fetchone()
            
            if not patient:
                return
            
            patient_name = f"{patient['first_name']} {patient['last_name']}"
            self.patient_name_label.setText(f"{patient_name}")
            
            # Get all notes for this patient
            cursor.execute("""
                SELECT id, note_date, subjective, objective, assessment, plan, status, finalized_at
                FROM ClinicalNote
                WHERE patient_id = ?
                ORDER BY note_date DESC
            """, (self.patient_id,))
            notes = cursor.fetchall()
            
            # Get Doctor Info
            cursor.execute("SELECT first_name, last_name, doctor_title, speciality FROM Users LIMIT 1")
            doctor = cursor.fetchone()
            if doctor:
                doc_name = f"Dr. {doctor['first_name']} {doctor['last_name']}"
                doc_title = doctor['doctor_title'] or doctor['speciality'] or "General Practitioner"
            else:
                doc_name = "Dr. Default"
                doc_title = "General Practitioner"
            
            # Get Clinic Info
            cursor.execute("SELECT clinic_name FROM ClinicInfo ORDER BY id DESC LIMIT 1")
            clinic = cursor.fetchone()
            clinic_name = clinic['clinic_name'] if clinic else "N/A"
            
            # Update metadata
            finalized_count = sum(1 for n in notes if n['status'] == 'FINALIZED')
            draft_count = len(notes) - finalized_count
            self.metadata_label.setText(f"Total Notes: {len(notes)} | Finalized: {finalized_count} | Drafts: {draft_count} | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
            
            # Build modern HTML document
            html = f"""
            <html>
            <head>
                <style>
                    @page {{
                        margin: 20mm;
                        size: A4;
                    }}
                    body {{
                        font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
                        margin: 0;
                        padding: 40px;
                        background-color: white;
                        color: #1a1a1a;
                        line-height: 1.5;
                    }}
                    .doc-header {{
                        display: grid;
                        grid-template-columns: 1fr 1fr;
                        gap: 60px;
                        margin-bottom: 40px;
                        padding-bottom: 24px;
                        border-bottom: 3px solid {Theme.PRIMARY};
                    }}
                    .header-section h3 {{
                        color: {Theme.PRIMARY};
                        font-size: 15px;
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        margin: 0 0 16px 0;
                        padding-bottom: 8px;
                        border-bottom: 1px solid #e5e7eb;
                        display: flex;
                        align-items: center;
                        gap: 8px;
                    }}
                    .info-row {{
                        display: flex;
                        align-items: baseline;
                        margin-bottom: 8px;
                        font-size: 14px;
                    }}
                    .info-label {{
                        width: 130px;
                        font-weight: 600;
                        color: #64748b;
                        flex-shrink: 0;
                    }}
                    .info-value {{
                        color: #0f172a;
                        font-weight: 500;
                        flex: 1;
                    }}
                    .note-card {{
                        margin-bottom: 32px;
                        break-inside: avoid;
                        border: 1px solid #e2e8f0;
                        border-radius: 8px;
                        overflow: hidden;
                    }}
                    .note-header {{
                        background: #f8fafc;
                        padding: 16px 24px;
                        border-bottom: 1px solid #e2e8f0;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }}
                    .note-title-group {{
                        display: flex;
                        align-items: center;
                        gap: 12px;
                    }}
                    .note-number {{
                        font-weight: 700;
                        color: #334155;
                        font-size: 15px;
                    }}
                    .status-badge {{
                        padding: 4px 10px;
                        border-radius: 4px;
                        font-size: 11px;
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 0.5px;
                    }}
                    .status-finalized {{
                        background: #dcfce7;
                        color: #166534;
                        border: 1px solid #bbf7d0;
                    }}
                    .status-draft {{
                        background: #fef9c3;
                        color: #854d0e;
                        border: 1px solid #fde047;
                    }}
                    .note-date {{
                        font-family: monospace;
                        color: #64748b;
                        font-size: 13px;
                    }}
                    .note-body {{
                        padding: 24px;
                        background: white;
                    }}
                    .soap-block {{
                        margin-bottom: 20px;
                    }}
                    .soap-block:last-child {{ margin-bottom: 0; }}
                    .soap-label {{
                        color: {Theme.PRIMARY};
                        font-size: 11px;
                        font-weight: 800;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        margin-bottom: 6px;
                        display: block;
                    }}
                    .soap-content {{
                        color: #334155;
                        font-size: 14px;
                        line-height: 1.6;
                        white-space: pre-wrap;
                        background: #f8fafc;
                        padding: 12px;
                        border-radius: 6px;
                        border-left: 3px solid #cbd5e1;
                    }}
                    .footer {{
                        margin-top: 40px;
                        text-align: center;
                        color: #94a3b8;
                        font-size: 11px;
                        border-top: 1px solid #f1f5f9;
                        padding-top: 20px;
                    }}
                </style>
            </head>
            <body>
                <div class="doc-header">
                    <div class="header-section">
                        <h3>{tr('Patient Details')}</h3>
                        <div class="info-row">
                            <span class="info-label">{tr('Patient Name:')}</span>
                            <span class="info-value">{patient_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">{tr('Date of Birth:')}</span>
                            <span class="info-value">{patient['date_of_birth'] or 'N/A'}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">{tr('Gender:')}</span>
                            <span class="info-value">{tr(patient['gender'] or 'N/A')}</span>
                        </div>
                    </div>
                    
                    <div class="header-section">
                        <h3>{tr('Provider Details')}</h3>
                        <div class="info-row">
                            <span class="info-label">{tr('Clinic Name:')}</span>
                            <span class="info-value">{clinic_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">{tr('Physician:')}</span>
                            <span class="info-value">{doc_name}</span>
                        </div>
                        <div class="info-row">
                            <span class="info-label">{tr('Speciality:')}</span>
                            <span class="info-value">{doc_title}</span>
                        </div>
                    </div>
                </div>
            """
            
            if not notes:
                html += f"""
                <div style="text-align: center; padding: 60px; color: #94a3b8;">
                    <!-- <div style="font-size: 48px; margin-bottom: 16px;">📂</div> -->
                    <div style="font-size: 16px;">{tr('No clinical notes found for this patient.')}</div>
                </div>
                """
            else:
                for idx, note in enumerate(notes, 1):
                    status_class = "finalized" if note['status'] == 'FINALIZED' else "draft"
                    status_text = tr("FINALIZED" if note['status'] == 'FINALIZED' else "DRAFT")
                    
                    html += f"""
                    <div class="note-card">
                        <div class="note-header">
                            <div class="note-title-group">
                                <span class="note-number">{tr('Note #')}{idx}</span>
                                <span class="status-badge status-{status_class}">{status_text}</span>
                            </div>
                            <div class="note-date">{note['note_date']}</div>
                        </div>
                        <div class="note-body">
                            <div class="soap-block">
                                <span class="soap-label">{tr('Subjective')}</span>
                                <div class="soap-content">{note['subjective'] or tr('No data')}</div>
                            </div>
                            <div class="soap-block">
                                <span class="soap-label">{tr('Objective')}</span>
                                <div class="soap-content">{note['objective'] or tr('No data')}</div>
                            </div>
                            <div class="soap-block">
                                <span class="soap-label">{tr('Assessment')}</span>
                                <div class="soap-content">{note['assessment'] or tr('No data')}</div>
                            </div>
                            <div class="soap-block">
                                <span class="soap-label">{tr('Plan')}</span>
                                <div class="soap-content">{note['plan'] or tr('No data')}</div>
                            </div>
                        </div>
                    </div>
                    """
            
            generated_at = datetime.now().strftime('%d/%m/%Y %H:%M' if manager().locale == 'fr' else '%B %d, %Y at %H:%M')
            html += f"""
                <div class="footer">
                    {tr('Generated on ')}{generated_at} | {tr('Confidential Medical Record')}
                </div>
            </body>
            </html>
            """
            
            self.document_text.setHtml(html)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load patient notes: {e}")
        finally:
            if conn:
                conn.close()
    
    def export_to_pdf(self):
        """Export document to PDF"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            tr("Export Clinical Notes"),
            f"clinical_notes_patient_{self.patient_id}.pdf",
            tr("PDF Files (*.pdf)")
        )
        
        if filename:
            try:
                printer = QPrinter(QPrinter.HighResolution)
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(filename)
                
                doc = QTextDocument()
                doc.setPlainText(self.document_text.toPlainText())
                doc.print_(printer)
                
                QMessageBox.information(self, "Success", f"Document exported to {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export PDF: {e}")


class NoteDialog(QDialog):
    def __init__(self, parent=None, note_id=None):
        super().__init__(parent)
        self.note_id = note_id
        self.is_finalized = False
        self.setWindowTitle("Edit Clinical Note" if note_id else "New Clinical Note")
        self.resize(700, 750)
        self.setStyleSheet(Theme.STYLESHEET)
        
        self.setup_ui()
        if note_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Header
        self.title_label = QLabel("Clinical Note (SOAP Format)")
        self.title_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.PRIMARY};")
        layout.addWidget(self.title_label)

        # Locked Banner (Visible only when note is FINALIZED)
        self.locked_banner = QFrame()
        self.locked_banner.setStyleSheet("""
            QFrame {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 8px;
                padding: 10px 14px;
            }
        """)
        locked_layout = QHBoxLayout(self.locked_banner)
        locked_layout.setContentsMargins(4, 2, 4, 2)
        locked_icon = QLabel("🔒")
        locked_icon.setStyleSheet("font-size: 18px; background: transparent;")
        self.locked_label = QLabel("This note has been finalized and signed. All fields are locked to read-only.")
        self.locked_label.setStyleSheet("color: #1E40AF; font-weight: 600; font-size: 12px; background: transparent;")
        self.locked_label.setWordWrap(True)
        locked_layout.addWidget(locked_icon)
        locked_layout.addWidget(self.locked_label)
        locked_layout.addStretch()
        self.locked_banner.setVisible(False)
        layout.addWidget(self.locked_banner)
        
        # Patient Info Panel (Allergies & Vitals)
        self.info_frame = QFrame()
        self.info_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SURFACE};
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        info_layout = QVBoxLayout(self.info_frame)
        info_layout.setContentsMargins(0, 0, 0, 0)
        
        self.patient_info_label = QLabel()
        self.patient_info_label.setWordWrap(True)
        self.patient_info_label.setTextFormat(Qt.RichText)
        info_layout.addWidget(self.patient_info_label)
        
        self.info_frame.setVisible(False)  # Hidden initially
        layout.addWidget(self.info_frame)
        
        form_layout = QFormLayout()
        form_layout.setSpacing(12)
        
        # Patient
        self.patient_combo = QComboBox()
        self.patient_combo.currentIndexChanged.connect(self.load_patient_context)
        self.load_patients()
        form_layout.addRow("Patient:", self.patient_combo)
        
        # Clinical Note Templates Dropdown
        template_row = QHBoxLayout()
        self.template_combo = QComboBox()
        self.template_combo.addItem("-- Select Clinical Note Template --", None)
        self.load_templates()
        self.template_combo.currentIndexChanged.connect(self.apply_template)
        template_row.addWidget(self.template_combo)
        
        self.save_tpl_btn = QPushButton("Save as Template")
        self.save_tpl_btn.setProperty("class", "secondary")
        self.save_tpl_btn.setStyleSheet("padding: 4px 10px; font-size: 11px;")
        self.save_tpl_btn.clicked.connect(self.save_as_template)
        template_row.addWidget(self.save_tpl_btn)
        form_layout.addRow("Template:", template_row)
        
        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        
        self.subjective = QTextEdit()
        self.subjective.setPlaceholderText("Subjective (Patient's complaints)")
        self.subjective.setMaximumHeight(100)
        
        self.objective = QTextEdit()
        self.objective.setPlaceholderText("Objective (Physical exam findings)")
        self.objective.setMaximumHeight(100)
        
        self.assessment = QTextEdit()
        self.assessment.setPlaceholderText("Assessment (Diagnosis) - Use specific codes when possible")
        self.assessment.setMaximumHeight(100)
        
        self.plan = QTextEdit()
        self.plan.setPlaceholderText("Plan (Treatment)")
        self.plan.setMaximumHeight(120)
        
        form_layout.addRow("Date:", self.date_edit)
        form_layout.addRow("Subjective:", self.subjective)
        form_layout.addRow("Objective:", self.objective)
        form_layout.addRow("Assessment:", self.assessment)
        form_layout.addRow("Plan:", self.plan)
        
        layout.addLayout(form_layout)
        
        # Finalize checkbox
        finalize_layout = QHBoxLayout()
        self.finalize_checkbox = QCheckBox("Finalize & Sign this note")
        self.finalize_checkbox.setStyleSheet(f"font-weight: bold; color: {Theme.PRIMARY};")
        finalize_layout.addWidget(self.finalize_checkbox)
        finalize_layout.addStretch()
        layout.addLayout(finalize_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Note")
        self.save_btn.clicked.connect(self.save_note)
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "secondary")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
    
    def load_patient_context(self):
        """Load and display patient allergies and latest vitals"""
        patient_id = self.patient_combo.currentData()
        if not patient_id:
            self.info_frame.setVisible(False)
            return
        
        context_html = ""
        
        # Get allergies
        allergies = db_manager.get_patient_allergies(patient_id)
        active_allergies = [a for a in allergies if a['is_active']]
        
        if active_allergies:
            context_html += f"<p style='margin: 0 0 8px 0;'><span style='color: {Theme.ERROR}; font-weight: bold;'>⚠️ ALLERGIES:</span> "
            allergy_list = []
            for a in active_allergies:
                severity_color = Theme.ERROR if a['severity'] == 'Severe' else Theme.WARNING
                allergy_list.append(f"<span style='color: {severity_color};'>{a['allergen']} ({a['severity']})</span>")
            context_html += ", ".join(allergy_list) + "</p>"
        
        # Get latest vitals
        vitals = db_manager.get_latest_vitals(patient_id)
        if vitals:
            context_html += f"<p style='margin: 0;'><span style='color: {Theme.PRIMARY}; font-weight: bold;'>📊 Latest Vitals:</span> "
            vital_parts = []
            
            if vitals['systolic_bp'] and vitals['diastolic_bp']:
                vital_parts.append(f"BP: {vitals['systolic_bp']}/{vitals['diastolic_bp']}")
            if vitals['heart_rate']:
                vital_parts.append(f"HR: {vitals['heart_rate']} BPM")
            if vitals['temperature']:
                vital_parts.append(f"Temp: {vitals['temperature']}°C")
            if vitals['weight']:
                vital_parts.append(f"Wt: {vitals['weight']}kg")
            if vitals['bmi']:
                bmi_color = Theme.SUCCESS if 18.5 <= vitals['bmi'] < 25 else Theme.WARNING
                vital_parts.append(f"<span style='color: {bmi_color};'>BMI: {vitals['bmi']}</span>")
            if vitals['oxygen_saturation']:
                vital_parts.append(f"SpO₂: {vitals['oxygen_saturation']}%")
            
            context_html += " | ".join(vital_parts) + "</p>"
        
        if context_html:
            self.patient_info_label.setText(context_html)
            self.info_frame.setVisible(True)
        else:
            self.info_frame.setVisible(False)

    def load_templates(self):
        """Load note templates into dropdown"""
        try:
            templates = db_manager.get_note_templates()
            for t in templates:
                self.template_combo.addItem(f"📄 {t['title']} ({t['category'] or 'General'})", t['id'])
        except Exception as e:
            print(f"Error loading note templates: {e}")

    def apply_template(self):
        """Apply selected template to SOAP fields"""
        template_id = self.template_combo.currentData()
        if not template_id:
            return
        t = db_manager.get_note_template(template_id)
        if t:
            # If fields have content, warn before overwriting
            if any([self.subjective.toPlainText().strip(), self.objective.toPlainText().strip(), self.assessment.toPlainText().strip(), self.plan.toPlainText().strip()]):
                confirm = QMessageBox.question(self, "Apply Template", "Applying this template will overwrite current SOAP fields. Continue?", QMessageBox.Yes | QMessageBox.No)
                if confirm != QMessageBox.Yes:
                    return
            localize = bool(t['is_default'])
            self.subjective.setPlainText(tr(t['subjective'] or '') if localize else t['subjective'] or '')
            self.objective.setPlainText(tr(t['objective'] or '') if localize else t['objective'] or '')
            self.assessment.setPlainText(tr(t['assessment'] or '') if localize else t['assessment'] or '')
            self.plan.setPlainText(tr(t['plan'] or '') if localize else t['plan'] or '')

    def save_as_template(self):
        """Save current SOAP fields as a new custom template"""
        from PySide6.QtWidgets import QInputDialog
        title, ok = QInputDialog.getText(self, tr("Save Custom Template"), tr("Enter Template Name:"))
        if ok and title.strip():
            db_manager.add_note_template(
                title=title.strip(),
                category="Custom",
                subjective=self.subjective.toPlainText().strip(),
                objective=self.objective.toPlainText().strip(),
                assessment=self.assessment.toPlainText().strip(),
                plan=self.plan.toPlainText().strip(),
                is_default=0
            )
            QMessageBox.information(self, "Success", f"Custom template '{title}' saved!")
            self.template_combo.clear()
            self.template_combo.addItem("-- Select Clinical Note Template --", None)
            self.load_templates()

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
            cursor.execute("SELECT * FROM ClinicalNote WHERE id = ?", (self.note_id,))
            note = cursor.fetchone()
            
            if note:
                note = dict(note)
                # Set patient
                index = self.patient_combo.findData(note['patient_id'])
                if index >= 0:
                    self.patient_combo.setCurrentIndex(index)
                
                # Set date
                dt = QDate.fromString(note['note_date'], "yyyy-MM-dd")
                self.date_edit.setDate(dt)
                
                self.subjective.setText(note['subjective'] or "")
                self.objective.setText(note['objective'] or "")
                self.assessment.setText(note['assessment'] or "")
                self.plan.setText(note['plan'] or "")
                
                # Set finalize checkbox and lock fields if finalized
                if note['status'] == 'FINALIZED':
                    self.is_finalized = True
                    self.finalize_checkbox.setChecked(True)
                    self.finalize_checkbox.setEnabled(False)  # Can't un-finalize

                    self.setWindowTitle(f"View Finalized Clinical Note - #{self.note_id}")
                    self.title_label.setText("Clinical Note (Finalized & Signed)")

                    finalized_date_str = ""
                    if note.get('finalized_at'):
                        try:
                            f_dt = datetime.fromisoformat(note['finalized_at'])
                            finalized_date_str = f" on {f_dt.strftime('%B %d, %Y at %I:%M %p')}"
                        except Exception:
                            finalized_date_str = f" on {note['finalized_at']}"

                    self.locked_label.setText(
                        f"🔒 Finalized & Signed Record{finalized_date_str}\n"
                        "All fields are locked to read-only to preserve clinical documentation integrity."
                    )
                    self.locked_banner.setVisible(True)

                    # Strict Read-Only Lockout
                    self.subjective.setReadOnly(True)
                    self.objective.setReadOnly(True)
                    self.assessment.setReadOnly(True)
                    self.plan.setReadOnly(True)

                    self.patient_combo.setEnabled(False)
                    self.date_edit.setEnabled(False)
                    self.template_combo.setEnabled(False)
                    if hasattr(self, 'save_tpl_btn'):
                        self.save_tpl_btn.setEnabled(False)

                    # Buttons update
                    self.save_btn.setText("🔒 Finalized Record")
                    self.save_btn.setEnabled(False)
                    self.save_btn.setStyleSheet("background-color: #94A3B8; color: #FFFFFF; font-weight: bold; border-radius: 8px; padding: 8px 16px;")
                    self.cancel_btn.setText("Close")
                
                # Load patient context (allergies/vitals)
                self.load_patient_context()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load note data: {e}")
        finally:
            if conn:
                conn.close()

    def save_note(self):
        if self.is_finalized:
            QMessageBox.information(self, "Locked Record", "This clinical note has been finalized and signed. It cannot be modified.")
            return

        patient_id = self.patient_combo.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Error", "Please select a patient")
            return
        
        is_finalizing = self.finalize_checkbox.isChecked()

        if is_finalizing:
            subj = self.subjective.toPlainText().strip()
            obj = self.objective.toPlainText().strip()
            ass = self.assessment.toPlainText().strip()
            pln = self.plan.toPlainText().strip()

            if not (subj or obj or ass or pln):
                QMessageBox.warning(
                    self, "Empty Note", 
                    "Cannot finalize an empty note. Please enter clinical documentation before signing."
                )
                return

            reply = QMessageBox.question(
                self, "Confirm Finalize & Sign",
                "Are you sure you want to finalize and sign this clinical note?\n\n"
                "⚠️ Once finalized, all fields will be permanently locked to READ-ONLY to preserve medical record integrity.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Determine status
        status = "FINALIZED" if is_finalizing else "DRAFT"
        finalized_at = datetime.now().isoformat() if status == "FINALIZED" else None
            
        conn = None
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            
            if self.note_id:
                # Update
                cursor.execute("""
                    UPDATE ClinicalNote 
                    SET patient_id=?, note_date=?, subjective=?, objective=?, assessment=?, plan=?, status=?, finalized_at=?
                    WHERE id=?
                """, (
                    patient_id,
                    self.date_edit.date().toString("yyyy-MM-dd"),
                    self.subjective.toPlainText(),
                    self.objective.toPlainText(),
                    self.assessment.toPlainText(),
                    self.plan.toPlainText(),
                    status,
                    finalized_at,
                    self.note_id
                ))
            else:
                # Insert
                cursor.execute("""
                    INSERT INTO ClinicalNote (patient_id, note_date, subjective, objective, assessment, plan, status, finalized_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    patient_id,
                    self.date_edit.date().toString("yyyy-MM-dd"),
                    self.subjective.toPlainText(),
                    self.objective.toPlainText(),
                    self.assessment.toPlainText(),
                    self.plan.toPlainText(),
                    status,
                    finalized_at
                ))
            
            conn.commit()
            
            if status == "FINALIZED":
                QMessageBox.information(self, "Success", "Note finalized and signed successfully! It is now locked to read-only.")
            
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save note: {e}")
        finally:
            if conn:
                conn.close()
