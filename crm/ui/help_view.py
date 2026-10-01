from PySide6.QtWidgets import (QWidget, QVBoxLayout, QTextBrowser, QFrame, QLabel, QHBoxLayout)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from styles.theme import Theme
from utils.localization import manager
from utils.french_documents import HELP

class HelpView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Main Container
        container = QFrame()
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {Theme.SURFACE};
                border-radius: 12px;
                border: 1px solid #E2E8F0;
            }}
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)

        # Header Section
        header_frame = QFrame()
        header_frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {Theme.PRIMARY}, stop:1 {Theme.ACCENT});
                border-radius: 8px;
                padding: 16px;
            }}
        """)
        header_layout = QVBoxLayout(header_frame)
        
        title = QLabel("DigiSpher EMR 2.0 - Professional User Guide")
        title.setWordWrap(True)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white; margin: 0;")
        subtitle = QLabel("Version 2.0.0 (Solopreneur Edition) • Complete Documentation & Reference Manual")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("font-size: 14px; color: white; opacity: 0.9; margin-top: 4px;")
        
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        container_layout.addWidget(header_frame)

        # Help Content
        self.help_browser = QTextBrowser()
        self.help_browser.setOpenExternalLinks(True)
        self.help_browser.setStyleSheet(f"""
            QTextBrowser {{
                background-color: transparent;
                border: none;
                color: {Theme.TEXT_PRIMARY};
                font-size: 15px;
                line-height: 1.8;
            }}
        """)
        
        # Comprehensive HTML Content
        html_content = self.get_help_content()
        self.help_browser.setHtml(html_content)
        manager().changed.connect(self._language_changed)
        container_layout.addWidget(self.help_browser)

        layout.addWidget(container)

    def _language_changed(self, locale):
        self.help_browser.setHtml(HELP if locale == "fr" else self.get_help_content())

    def get_help_content(self):
        if manager().locale == "fr":
            return HELP
        return f"""
        <style>
            body {{ margin: 20px 0; }}
            h1 {{ 
                color: {Theme.PRIMARY}; 
                font-size: 28px; 
                margin-top: 40px; 
                margin-bottom: 15px;
                border-bottom: 3px solid {Theme.ACCENT};
                padding-bottom: 10px;
            }}
            h2 {{ 
                color: {Theme.SECONDARY}; 
                font-size: 22px; 
                margin-top: 30px; 
                margin-bottom: 12px;
                font-weight: 600;
            }}
            h3 {{ 
                color: {Theme.TEXT_PRIMARY}; 
                font-size: 18px; 
                font-weight: bold; 
                margin-top: 20px;
                margin-bottom: 8px;
            }}
            p {{ margin-bottom: 12px; line-height: 1.8; }}
            ul, ol {{ margin-bottom: 18px; margin-left: 25px; line-height: 1.8; }}
            li {{ margin-bottom: 8px; }}
            .highlight {{ color: {Theme.ACCENT}; font-weight: bold; }}
            .badge {{ 
                background-color: {Theme.PRIMARY}; 
                color: white; 
                padding: 3px 10px; 
                border-radius: 12px;
                font-size: 12px;
                font-weight: bold;
            }}
            .section-card {{
                background-color: #F8FAFC;
                border-left: 4px solid {Theme.PRIMARY};
                padding: 15px;
                margin: 15px 0;
                border-radius: 4px;
            }}
            .section-card a {{
                color: {Theme.PRIMARY};
                text-decoration: none;
                font-weight: 500;
                transition: all 0.2s;
            }}
            .section-card a:hover {{
                color: {Theme.ACCENT};
                text-decoration: underline;
            }}
            .section-card li {{
                margin-bottom: 10px;
                font-size: 16px;
            }}
            .warning {{
                background-color: #FFF3CD;
                border-left: 4px solid #FFC107;
                padding: 12px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            .info {{
                background-color: #E7F3FF;
                border-left: 4px solid {Theme.PRIMARY};
                padding: 12px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            code {{
                background-color: #F1F5F9;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: monospace;
                color: {Theme.SECONDARY};
            }}
        </style>

        <h1>📖 Table of Contents</h1>
        <div class="section-card">
            <ol>
                <li><a href="#intro">Introduction & Getting Started</a></li>
                <li><a href="#login">Login & Password Recovery</a></li>
                <li><a href="#patients">Patient Management</a></li>
                <li><a href="#appointments">Appointment Scheduling</a></li>
                <li><a href="#notes">Clinical Notes (SOAP)</a></li>
                <li><a href="#allergies">Allergy Management</a></li>
                <li><a href="#vitals">Vital Signs Tracking</a></li>
                <li><a href="#prescriptions">Prescription Management</a></li>
                <li><a href="#settings">Settings & Configuration</a></li>
                <li><a href="#security">Security & Profile Management</a></li>
                <li><a href="#backup">Database Backup & Restore</a></li>
                <li><a href="#tips">Tips & Best Practices</a></li>
            </ol>
        </div>

        <h1 id="intro">🏥 Introduction & Getting Started</h1>
        <p><strong>DigiSpher EMR</strong> is a comprehensive Electronic Medical Record system designed for solo practitioners and small clinics. This desktop application provides a complete suite of tools to manage patient records, appointments, clinical notes, prescriptions, and more.</p>

        <h1 id="login">🔐 Login & Password Recovery</h1>

        <h2>First Time Login</h2>
        <div class="info">
            <strong>Default Credentials:</strong><br>
            Username: <code>doctor</code><br>
            Password: <code>doctor123</code>
        </div>
        <p><strong>⚠️ Important:</strong> Change your password immediately after first login for security.</p>

        <h2>Forgot Password? (Secure Recovery)</h2>
        <div class="info">
            <strong>🔒 Enhanced Security:</strong> Password recovery now requires secondary authentication to protect your account.
        </div>
        <p>If you forget your password, follow this secure 3-step recovery process:</p>
        <ol>
            <li>On the login screen, click <span class="highlight">Forgot Password?</span></li>
            <li><strong>Step 1:</strong> Enter your username</li>
            <li><strong>Step 2:</strong> Enter your clinic name for verification (secondary authentication)
                <ul>
                    <li>This ensures only authorized users can reset passwords</li>
                    <li>The clinic name must match what's stored in the system</li>
                    <li>Case-insensitive matching</li>
                </ul>
            </li>
            <li><strong>Step 3:</strong> Enter your new password twice to confirm</li>
            <li>Click <span class="highlight">Reset Password</span></li>
            <li>You can now login with your new password</li>
        </ol>
        <div class="warning">
            <strong>⚠️ Important:</strong> If you don't know your clinic name, you'll need to contact your system administrator to recover your account.
        </div>

        <h1 id="patients">👥 Patient Management</h1>

        <h2>Adding a New Patient</h2>
        <ol>
            <li>Navigate to <span class="highlight">Patients</span> from the sidebar</li>
            <li>Click <span class="highlight">+ Add Patient</span> (top right)</li>
            <li>Fill in the patient information:
                <ul>
                    <li><strong>Required:</strong> First Name, Last Name</li>
                    <li><strong>Recommended:</strong> Date of Birth, Gender, Phone, Email</li>
                    <li><strong>Optional:</strong> Address, Medical History, Emergency Contact</li>
                </ul>
            </li>
            <li>Click <span class="highlight">Save</span> to create the patient record</li>
        </ol>

        <h2>Editing Patient Information</h2>
        <ol>
            <li>Select the patient row from the table</li>
            <li>Click the <span class="highlight">Edit</span> button in the toolbar</li>
            <li>Update any information as needed</li>
            <li>Click <span class="highlight">Save</span> to apply changes</li>
        </ol>

        <h2>Deleting Patients</h2>
        <div class="warning">
            <strong>⚠️ Warning:</strong> Deleting a patient will also delete all associated appointments, notes, and prescriptions. This action cannot be undone!
        </div>

        <h1 id="appointments">📅 Appointment Scheduling</h1>

        <h2>Creating a New Appointment</h2>
        <ol>
            <li>Go to <span class="highlight">Appointments</span> tab</li>
            <li>Click <span class="highlight">New Appointment</span></li>
            <li>Select the patient from the dropdown</li>
            <li>Choose date and time</li>
            <li>Enter the reason for visit (e.g., "Annual Checkup")</li>
            <li>Set the status (default: SCHEDULED)</li>
            <li>Click <span class="highlight">Schedule</span></li>
        </ol>

        <h2>Appointment Statuses</h2>
        <ul>
            <li><span class="badge">SCHEDULED</span> - Appointment booked</li>
            <li><span class="badge">CONFIRMED</span> - Patient confirmed attendance</li>
            <li><span class="badge">IN_PROGRESS</span> - Patient currently being seen</li>
            <li><span class="badge">COMPLETED</span> - Appointment finished</li>
            <li><span class="badge">CANCELLED</span> - Appointment cancelled</li>
            <li><span class="badge">NO_SHOW</span> - Patient did not attend</li>
        </ul>

        <h2>Editing or Rescheduling</h2>
        <ol>
            <li>Select the appointment from the list</li>
            <li>Click <span class="highlight">Edit</span></li>
            <li>Modify date, time, status, or other details</li>
            <li>Click <span class="highlight">Save</span></li>
        </ol>

        <h1 id="notes">📝 Clinical Notes (SOAP Format)</h1>

        <h2>Creating a New Clinical Note</h2>
        <ol>
            <li>Navigate to <span class="highlight">Clinical Notes</span></li>
            <li>Click <span class="highlight">New Note</span></li>
            <li>Select the patient</li>
            <li>Enter the note date</li>
            <li>Complete the SOAP format:
                <ul>
                    <li><strong>S</strong>ubjective: Patient's chief complaints and symptoms</li>
                    <li><strong>O</strong>bjective: Physical exam findings and vital signs</li>
                    <li><strong>A</strong>ssessment: Diagnosis and clinical impression</li>
                    <li><strong>P</strong>lan: Treatment plan and follow-up</li>
                </ul>
            </li>
            <li><em>Optional:</em> Check <span class="highlight">Finalize & Sign</span> if note is complete</li>
            <li>Click <span class="highlight">Save Note</span></li>
        </ol>

        <h2>Patient Context Panel</h2>
        <p>When creating or editing notes, the system automatically displays:</p>
        <ul>
            <li><strong>⚠️ Active Allergies:</strong> Shows all active allergies with severity</li>
            <li><strong>📊 Latest Vitals:</strong> Displays most recent vital signs (BP, HR, Temp, etc.)</li>
        </ul>

        <h2>Viewing Clinical Notes Document</h2>
        <ol>
            <li>In the Clinical Notes table, click <span class="highlight">👁 View Doc</span></li>
            <li>A document view opens showing all notes for that patient</li>
            <li>The header displays patient details and doctor information</li>
            <li>All notes are shown in chronological order with status markers</li>
        </ol>

        <h2>Exporting Notes to PDF</h2>
        <ol>
            <li>Open the document view for a patient (click <span class="highlight">👁 View Doc</span>)</li>
            <li>Click <span class="highlight">📄 Export to PDF</span> button</li>
            <li>Choose save location and filename</li>
            <li>The PDF will include all clinical notes with professional formatting</li>
        </ol>

        <h1 id="allergies">⚠️ Allergy Management</h1>

        <h2>Adding Patient Allergies</h2>
        <ol>
            <li>Go to <span class="highlight">Patients</span> tab</li>
            <li>Select a patient</li>
            <li>Look for the <span class="highlight">Allergies</span> section in the patient details panel</li>
            <li>Click <span class="highlight">+ Add Allergy</span></li>
            <li>Enter allergy details:
                <ul>
                    <li><strong>Allergen:</strong> Name of the substance (e.g., "Penicillin")</li>
                    <li><strong>Reaction:</strong> Description of reaction (e.g., "Rash, itching")</li>
                    <li><strong>Severity:</strong> Mild, Moderate, or Severe</li>
                    <li><strong>Onset Date:</strong> When allergy was first identified</li>
                    <li><strong>Notes:</strong> Additional information</li>
                </ul>
            </li>
            <li>Click <span class="highlight">Save</span></li>
        </ol>

        <h2>Clinical Safety Features</h2>
        <div class="warning">
            <strong>⚠️ Safety Alert:</strong> Active allergies automatically appear when creating clinical notes or prescriptions to prevent adverse reactions!
        </div>

        <h1 id="vitals">📊 Vital Signs Tracking</h1>

        <h2>Recording Vital Signs</h2>
        <ol>
            <li>Navigate to the patient view</li>
            <li>Find the <span class="highlight">Vital Signs</span> section</li>
            <li>Click <span class="highlight">+ Add Vitals</span></li>
            <li>Enter measurements:
                <ul>
                    <li>Blood Pressure (Systolic/Diastolic)</li>
                    <li>Heart Rate (BPM)</li>
                    <li>Temperature (°C)</li>
                    <li>Weight (kg) & Height (cm) - BMI auto-calculated</li>
                    <li>Oxygen Saturation (SpO₂ %)</li>
                    <li>Respiratory Rate</li>
                    <li>Notes</li>
                </ul>
            </li>
            <li>Click <span class="highlight">Save</span></li>
        </ol>

        <h2>BMI Auto-Calculation</h2>
        <p>The system automatically calculates BMI when both weight and height are entered, and color-codes the result:</p>
        <ul>
            <li><strong>Green:</strong> Normal range (18.5 - 24.9)</li>
            <li><strong>Yellow:</strong> Outside normal range</li>
        </ul>

        <h1 id="prescriptions">💊 Prescription Management</h1>

        <h2>Creating a Prescription</h2>
        <ol>
            <li>Go to <span class="highlight">Prescriptions</span> tab</li>
            <li>Click <span class="highlight">New Prescription</span></li>
            <li>Select the patient</li>
            <li>Enter medication details:
                <ul>
                    <li><strong>Medication:</strong> Drug name (e.g., "Amoxicillin")</li>
                    <li><strong>Dosage:</strong> Strength (e.g., "500mg")</li>
                    <li><strong>Frequency:</strong> How often (e.g., "Twice daily")</li>
                    <li><strong>Duration:</strong> Treatment length (e.g., "7 days")</li>
                    <li><strong>Instructions:</strong> Additional patient instructions</li>
                    <li><strong>Doctor:</strong> Prescribing physician name</li>
                </ul>
            </li>
            <li>Click <span class="highlight">Save Prescription</span></li>
        </ol>

        <h2>Exporting Prescription to PDF</h2>
        <ol>
            <li>Select a prescription from the list</li>
            <li>Click <span class="highlight">Export PDF</span></li>
            <li>A professional prescription document will be generated with:
                <ul>
                    <li>Patient information</li>
                    <li>Doctor details and clinic information</li>
                    <li>Medication details and instructions</li>
                    <li>Prescription date and ID</li>
                </ul>
            </li>
        </ol>

        <h1 id="settings">⚙️ Settings & Configuration</h1>

        <h2>Clinic Information Management</h2>
        <div class="info">
            <strong>ℹ️ Important:</strong> Clinic information is used throughout the system for prescriptions, documents, and password recovery.
        </div>
        
        <h3>Setting Up Clinic Information</h3>
        <ol>
            <li>Navigate to <span class="highlight">Settings</span></li>
            <li>Find the <span class="highlight">Clinic Information</span> card (below User Profile)</li>
            <li>Click <span class="highlight">Edit Clinic Info</span></li>
            <li>Enter your clinic details:
                <ul>
                    <li><strong>Clinic Name:</strong> Official name of your practice</li>
                    <li><strong>Clinic Address:</strong> Full address including city/state</li>
                    <li><strong>License Number:</strong> Medical practice license number</li>
                </ul>
            </li>
            <li>Click <span class="highlight">Save Changes</span></li>
        </ol>
        
        <h3>Where Clinic Information is Used</h3>
        <ul>
            <li><strong>📄 Prescription PDFs:</strong> Appears as header with clinic details</li>
            <li><strong>🔒 Password Recovery:</strong> Clinic name is required as secondary authentication</li>
            <li><strong>📋 Clinical Documents:</strong> Included in all exported documents</li>
            <li><strong>⚙️ System Identification:</strong> Identifies your practice throughout the app</li>
        </ul>
        
        <h3>Editing Clinic Information</h3>
        <p>You can update clinic information anytime from Settings:</p>
        <ol>
            <li>Go to <span class="highlight">Settings</span></li>
            <li>In the Clinic Information card, click <span class="highlight">Edit Clinic Info</span></li>
            <li>Update any fields as needed</li>
            <li>Click <span class="highlight">Save Changes</span></li>
        </ol>
        <div class="warning">
            <strong>⚠️ Note:</strong> Changing the clinic name will affect password recovery. Make sure to remember the new clinic name!
        </div>

        <h1 id="security">🔒 Security & Profile Management</h1>

        <h2>Editing Your Profile</h2>
        <ol>
            <li>Go to <span class="highlight">Settings</span> or click your profile card in the sidebar</li>
            <li>Click <span class="highlight">Edit Profile</span></li>
            <li>Update your information:
                <ul>
                    <li>First Name & Last Name</li>
                    <li>Professional Speciality</li>
                    <li>Doctor Title (e.g., "MD", "MBBS")</li>
                    <li>Username (login ID)</li>
                </ul>
            </li>
            <li>Click <span class="highlight">Save Changes</span></li>
        </ol>

        <h2>Changing Your Password</h2>
        <ol>
            <li>In the Edit Profile dialog, enter:
                <ul>
                    <li><strong>New Password:</strong> Your desired password</li>
                    <li><strong>Confirm Password:</strong> Repeat the new password</li>
                </ul>
            </li>
            <li>Leave blank if you don't want to change password</li>
            <li>Click <span class="highlight">Save Changes</span></li>
        </ol>

        <h2>Session Timeout</h2>
        <p>For security, the system automatically logs you out after 30 minutes of inactivity. Any unsaved work will be lost, so save your work regularly.</p>

        <h1 id="backup">💾 Database Backup & Restore</h1>

        <h2>Creating a Backup</h2>
        <div class="info">
            <strong>ℹ️ Best Practice:</strong> Create regular backups to prevent data loss!
        </div>
        <ol>
            <li>Go to <span class="highlight">Settings</span></li>
            <li>Click <span class="highlight">Backup Database</span></li>
            <li>Choose a save location (recommended: external drive or cloud storage)</li>
            <li>A timestamped backup file will be created (e.g., <code>clinic_backup_20241204_183000.db</code>)</li>
        </ol>

        <h2>Backup Schedule Recommendations</h2>
        <ul>
            <li><strong>Daily:</strong> For active practices with many patients</li>
            <li><strong>Weekly:</strong> For smaller practices</li>
            <li><strong>Before Major Updates:</strong> Always backup before software updates</li>
        </ul>

        <h1 id="tips">💡 Tips & Best Practices</h1>

        <h2>Data Entry Best Practices</h2>
        <ul>
            <li><strong>Consistency:</strong> Use standardized abbreviations and formats</li>
            <li><strong>Completeness:</strong> Fill in all relevant fields for better record-keeping</li>
            <li><strong>Accuracy:</strong> Double-check patient information, especially allergies</li>
            <li><strong>Timeliness:</strong> Enter clinical notes immediately after patient visits</li>
        </ul>

        <h2>Security Best Practices</h2>
        <ul>
            <li>Change default password immediately</li>
            <li>Use strong passwords (8+ characters, mix of letters, numbers, symbols)</li>
            <li>Never share your login credentials</li>
            <li>Log out when leaving your workstation</li>
            <li>Keep backup copies securely stored</li>
        </ul>

        <h2>Keyboard Shortcuts</h2>
        <div class="section-card">
            <ul>
                <li><code>Ctrl+N</code> - New record (in current view)</li>
                <li><code>Ctrl+E</code> - Edit selected record</li>
                <li><code>Ctrl+S</code> - Save current form</li>
                <li><code>Esc</code> - Close dialog without saving</li>
                <li><code>Enter</code> - Submit login/password forms</li>
            </ul>
        </div>

        <h2>Troubleshooting Common Issues</h2>
        <h3>Cannot login / Forgot password</h3>
        <p>Use the <span class="highlight">Forgot Password?</span> link on the login screen to reset.</p>

        <h3>Database locked error</h3>
        <p>Ensure only one instance of the application is running. Restart if necessary.</p>

        <h3>Missing data or records</h3>
        <p>Check if you're viewing the correct date range or filter settings. Restore from backup if data is truly missing.</p>

        <hr>
        <div class="info">
            <p><strong>📧 Support & Feedback</strong></p>
            <p>For technical support, feature requests, or bug reports, please contact your IT administrator or the DigiSpher development team.</p>
            <p><em>Version 2.0.0 (Solopreneur Edition) | Release: 2.0.0 • Updated: September 2026</em></p>
        </div>
        """
