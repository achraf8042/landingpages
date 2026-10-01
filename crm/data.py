import sqlite3
import hashlib
import os
import sys
import tempfile
from contextlib import closing
import logging
import secrets
from datetime import datetime, timedelta


class ClosingConnection(sqlite3.Connection):
    """Commit or roll back a context-managed connection, then close it."""

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            return super().__exit__(exc_type, exc_value, traceback)
        finally:
            self.close()


class DatabaseManager:
    def __init__(self):
        self.setup_logging()
        self.db_path = self.get_db_path()
        self.initialize_database()

    def get_app_data_dir(self):
        """Get the application data directory safely"""
        app_name = "DigiSpher EMR"
        if sys.platform == 'win32':
            base_dir = os.environ.get('APPDATA')
            if not base_dir:
                base_dir = os.path.expanduser("~")
            data_dir = os.path.join(base_dir, app_name)
        else:
            base_dir = os.path.expanduser("~")
            data_dir = os.path.join(base_dir, f".{app_name.lower()}")
        
        return data_dir

    def setup_logging(self):
        """Setup logging for database operations"""
        app_dir = self.get_app_data_dir()
        log_dir = os.path.join(app_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "clinic_emr.log")

        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_path, encoding='utf-8'), logging.StreamHandler()],
        )
        self.logger = logging.getLogger(__name__)

    def get_db_path(self):
        """Get database path using user's AppData/Home directory"""
        data_dir = os.path.join(self.get_app_data_dir(), "data")
        os.makedirs(data_dir, exist_ok=True)
        
        db_path = os.path.join(data_dir, "clinic.db")
        self.logger.info(f"Database path: {db_path}")
        return db_path

    def get_db_connection(self):
        """Get database connection with row factory, foreign keys, and WAL journal mode"""
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0, factory=ClosingConnection)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = WAL")
            return conn
        except sqlite3.Error as e:
            self.logger.error(f"Database connection error: {e}")
            return None

    def initialize_database(self):
        """Initialize database tables and migrations for Version 2.0"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()

                # 1. Users
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        salt TEXT NOT NULL,
                        first_name TEXT,
                        last_name TEXT,
                        speciality TEXT,
                        doctor_title TEXT,
                        security_question TEXT,
                        security_answer_hash TEXT,
                        answer_salt TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        last_login TEXT,
                        is_active INTEGER DEFAULT 1,
                        must_change_password INTEGER DEFAULT 0
                    )
                ''')
                self.migrate_users_table(cursor)

                # 2. ClinicInfo
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ClinicInfo (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        clinic_name TEXT NOT NULL,
                        clinic_address TEXT NOT NULL,
                        license_number TEXT NOT NULL,
                        tax_rate REAL DEFAULT 0.0,
                        currency_symbol TEXT DEFAULT '$',
                        currency_code TEXT DEFAULT 'USD',
                        currency_position TEXT DEFAULT 'before',
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.migrate_clinic_info_table(cursor)

                # 3. Patient
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Patient (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        first_name TEXT NOT NULL CHECK(length(first_name) > 0),
                        last_name TEXT NOT NULL CHECK(length(last_name) > 0),
                        date_of_birth TEXT,
                        gender TEXT CHECK(gender IN ('Male', 'Female', 'Other', '')),
                        phone TEXT,
                        email TEXT,
                        address TEXT,
                        medical_history TEXT,
                        emergency_contact TEXT,
                        emergency_phone TEXT,
                        insurance_provider TEXT DEFAULT '',
                        insurance_member_no TEXT DEFAULT '',
                        insurance_coverage_pct REAL DEFAULT 0.0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                self.migrate_patient_table(cursor)

                # 4. Appointment
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Appointment (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        doctor_name TEXT NOT NULL,
                        datetime TEXT NOT NULL,
                        status TEXT DEFAULT 'SCHEDULED'
                            CHECK(status IN ('SCHEDULED', 'CONFIRMED', 'IN_PROGRESS', 'COMPLETED', 'CANCELLED', 'NO_SHOW')),
                        reason TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        reminder_sent_at TEXT,
                        FOREIGN KEY (patient_id) REFERENCES Patient (id) ON DELETE CASCADE
                    )
                ''')

                # 5. ClinicalNote
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS ClinicalNote (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        appointment_id INTEGER,
                        note_date TEXT NOT NULL,
                        subjective TEXT,
                        objective TEXT,
                        assessment TEXT,
                        plan TEXT,
                        status TEXT DEFAULT 'DRAFT' CHECK(status IN ('DRAFT', 'FINALIZED')),
                        finalized_at TEXT,
                        FOREIGN KEY (patient_id) REFERENCES Patient (id) ON DELETE CASCADE,
                        FOREIGN KEY (appointment_id) REFERENCES Appointment (id) ON DELETE SET NULL
                    )
                ''')
                self.migrate_clinical_note_table(cursor)

                # 6. Prescription (Header)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Prescription (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        appointment_id INTEGER,
                        prescription_date TEXT NOT NULL,
                        prescribing_doctor TEXT,
                        instructions TEXT,
                        status TEXT DEFAULT 'ACTIVE'
                            CHECK(status IN ('ACTIVE', 'COMPLETED', 'CANCELLED')),
                        pdf_file_path TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES Patient (id) ON DELETE CASCADE,
                        FOREIGN KEY (appointment_id) REFERENCES Appointment (id) ON DELETE SET NULL
                    )
                ''')

                # 7. PrescriptionItems (Multi-medication support)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS PrescriptionItems (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        prescription_id INTEGER NOT NULL,
                        medication_name TEXT NOT NULL,
                        dosage TEXT,
                        frequency TEXT,
                        duration TEXT,
                        FOREIGN KEY (prescription_id) REFERENCES Prescription (id) ON DELETE CASCADE
                    )
                ''')

                # 8. Allergies
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Allergies (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        allergen TEXT NOT NULL,
                        reaction TEXT,
                        severity TEXT CHECK(severity IN ('Mild', 'Moderate', 'Severe', 'Unknown')),
                        onset_date TEXT,
                        notes TEXT,
                        is_active INTEGER DEFAULT 1,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES Patient (id) ON DELETE CASCADE
                    )
                ''')

                # 9. VitalSigns
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS VitalSigns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        appointment_id INTEGER,
                        measurement_date TEXT NOT NULL,
                        systolic_bp INTEGER,
                        diastolic_bp INTEGER,
                        heart_rate INTEGER,
                        temperature REAL,
                        weight REAL,
                        height REAL,
                        bmi REAL,
                        oxygen_saturation INTEGER,
                        respiratory_rate INTEGER,
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES Patient (id) ON DELETE CASCADE,
                        FOREIGN KEY (appointment_id) REFERENCES Appointment (id) ON DELETE SET NULL
                    )
                ''')

                # 10. Billing (Invoicing & Revenue)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Billing (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        patient_id INTEGER NOT NULL,
                        total_amount REAL NOT NULL,
                        subtotal_amount REAL DEFAULT 0.0,
                        tax_amount REAL DEFAULT 0.0,
                        status TEXT DEFAULT 'UNPAID' CHECK(status IN ('UNPAID', 'PAID', 'PARTIAL', 'CANCELLED')),
                        due_date TEXT,
                        notes TEXT,
                        currency_code TEXT DEFAULT '',
                        insurance_provider TEXT DEFAULT '',
                        insurance_member_no TEXT DEFAULT '',
                        insurance_pct REAL DEFAULT 0.0,
                        insurance_amount REAL DEFAULT 0.0,
                        patient_amount REAL DEFAULT 0.0,
                        insurance_claim_status TEXT DEFAULT 'NOT_SUBMITTED'
                            CHECK(insurance_claim_status IN ('NOT_SUBMITTED', 'SUBMITTED', 'SETTLED', 'DENIED')),
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (patient_id) REFERENCES Patient (id) ON DELETE CASCADE
                    )
                ''')
                self.migrate_billing_table(cursor)

                # 11. BillingItems (Line items per invoice)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS BillingItems (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        bill_id INTEGER NOT NULL,
                        description TEXT NOT NULL,
                        amount REAL NOT NULL,
                        FOREIGN KEY (bill_id) REFERENCES Billing (id) ON DELETE CASCADE
                    )
                ''')

                # 12. Expenses (Clinic operational costs)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS Expenses (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        category TEXT NOT NULL,
                        description TEXT NOT NULL,
                        amount REAL NOT NULL,
                        expense_date TEXT NOT NULL,
                        payment_method TEXT DEFAULT 'Cash',
                        notes TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # 13. NoteTemplates (Clinical SOAP templates)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS NoteTemplates (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        title TEXT NOT NULL,
                        category TEXT,
                        subjective TEXT,
                        objective TEXT,
                        assessment TEXT,
                        plan TEXT,
                        is_default INTEGER DEFAULT 0,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Create Indexes for high performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_patient_name ON Patient(last_name, first_name)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_datetime ON Appointment(datetime)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_allergy_patient ON Allergies(patient_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_vitals_patient ON VitalSigns(patient_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_billing_patient ON Billing(patient_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_billing_date ON Billing(created_at)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_expenses_date ON Expenses(expense_date)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_prescription_patient ON Prescription(patient_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_rx_items ON PrescriptionItems(prescription_id)')

                # Default admin user & note templates
                self.create_default_user(cursor)
                self.seed_default_templates(cursor)

                conn.commit()
            self.logger.info("Database initialized successfully with Version 2.0 schema")
        except Exception as e:
            self.logger.error(f"Error initializing database: {e}")
            raise

    # -------------------------
    # Migrations
    # -------------------------
    def migrate_users_table(self, cursor):
        """Add new columns to Users table if they don't exist"""
        try:
            cursor.execute("PRAGMA table_info(Users)")
            columns = [info[1] for info in cursor.fetchall()]
            
            for col in ['first_name', 'last_name', 'speciality', 'doctor_title']:
                if col not in columns:
                    cursor.execute(f"ALTER TABLE Users ADD COLUMN {col} TEXT")
                    
            if 'security_question' not in columns:
                cursor.execute("ALTER TABLE Users ADD COLUMN security_question TEXT")
            if 'security_answer_hash' not in columns:
                cursor.execute("ALTER TABLE Users ADD COLUMN security_answer_hash TEXT")
            if 'answer_salt' not in columns:
                cursor.execute("ALTER TABLE Users ADD COLUMN answer_salt TEXT")
            
            if 'must_change_password' not in columns:
                cursor.execute("ALTER TABLE Users ADD COLUMN must_change_password INTEGER DEFAULT 0")
            cursor.execute("SELECT password_hash, salt FROM Users WHERE username = 'doctor'")
            user = cursor.fetchone()
            if user and self.verify_password(user['password_hash'], user['salt'], 'doctor123'):
                cursor.execute("UPDATE Users SET must_change_password = 1 WHERE username = 'doctor'")
        except Exception as e:
            self.logger.error(f"Error migrating Users table: {e}")
            raise

    def migrate_clinic_info_table(self, cursor):
        """Add currency and tax rate columns to ClinicInfo if missing"""
        try:
            cursor.execute("PRAGMA table_info(ClinicInfo)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'tax_rate' not in columns:
                cursor.execute("ALTER TABLE ClinicInfo ADD COLUMN tax_rate REAL DEFAULT 0.0")
            if 'currency_symbol' not in columns:
                cursor.execute("ALTER TABLE ClinicInfo ADD COLUMN currency_symbol TEXT DEFAULT '$'")
            if 'currency_code' not in columns:
                cursor.execute("ALTER TABLE ClinicInfo ADD COLUMN currency_code TEXT DEFAULT 'USD'")
            if 'currency_position' not in columns:
                cursor.execute("ALTER TABLE ClinicInfo ADD COLUMN currency_position TEXT DEFAULT 'before'")
            # A clinic-wide default coverage rate was removed: every insurer sets
            # its own rate, so the rate lives only on the patient.
            if 'default_insurance_pct' in columns:
                try:
                    cursor.execute("ALTER TABLE ClinicInfo DROP COLUMN default_insurance_pct")
                    self.logger.info("Removed obsolete ClinicInfo.default_insurance_pct")
                except sqlite3.Error as drop_error:
                    self.logger.warning(
                        f"Could not drop default_insurance_pct (needs SQLite 3.35+): {drop_error}")
        except Exception as e:
            self.logger.error(f"Error migrating ClinicInfo table: {e}")

    def migrate_patient_table(self, cursor):
        """Add optional insurance columns to Patient. Blank means self-pay."""
        try:
            cursor.execute("PRAGMA table_info(Patient)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'insurance_provider' not in columns:
                cursor.execute("ALTER TABLE Patient ADD COLUMN insurance_provider TEXT DEFAULT ''")
            if 'insurance_member_no' not in columns:
                cursor.execute("ALTER TABLE Patient ADD COLUMN insurance_member_no TEXT DEFAULT ''")
            if 'insurance_coverage_pct' not in columns:
                cursor.execute("ALTER TABLE Patient ADD COLUMN insurance_coverage_pct REAL DEFAULT 0.0")
        except Exception as e:
            self.logger.error(f"Error migrating Patient table: {e}")

    def migrate_billing_table(self, cursor):
        """Snapshot invoice currency, insurance details and the coverage split.

        Invoices are financial records, so they must not silently change meaning
        when the clinic later switches currency, or the patient changes insurer
        or coverage rate.
        """
        try:
            cursor.execute("PRAGMA table_info(Billing)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'currency_code' not in columns:
                cursor.execute("ALTER TABLE Billing ADD COLUMN currency_code TEXT DEFAULT ''")
            if 'insurance_provider' not in columns:
                cursor.execute("ALTER TABLE Billing ADD COLUMN insurance_provider TEXT DEFAULT ''")
            if 'insurance_member_no' not in columns:
                cursor.execute("ALTER TABLE Billing ADD COLUMN insurance_member_no TEXT DEFAULT ''")
            if 'insurance_pct' not in columns:
                cursor.execute("ALTER TABLE Billing ADD COLUMN insurance_pct REAL DEFAULT 0.0")
            if 'insurance_amount' not in columns:
                cursor.execute("ALTER TABLE Billing ADD COLUMN insurance_amount REAL DEFAULT 0.0")
            if 'patient_amount' not in columns:
                cursor.execute("ALTER TABLE Billing ADD COLUMN patient_amount REAL DEFAULT 0.0")
            if 'insurance_claim_status' not in columns:
                cursor.execute("ALTER TABLE Billing ADD COLUMN insurance_claim_status TEXT DEFAULT 'NOT_SUBMITTED'")

            # Give pre-existing invoices a concrete currency instead of a blank.
            cursor.execute("""
                UPDATE Billing
                   SET currency_code = COALESCE(
                       (SELECT currency_code FROM ClinicInfo ORDER BY id DESC LIMIT 1), 'USD')
                 WHERE currency_code IS NULL OR currency_code = ''
            """)

            # Historical invoices were entirely self-pay: nothing was split, so
            # the patient owes the whole total.
            cursor.execute("""
                UPDATE Billing
                   SET patient_amount = total_amount
                 WHERE COALESCE(patient_amount, 0) = 0
                   AND COALESCE(insurance_amount, 0) = 0
            """)
        except Exception as e:
            self.logger.error(f"Error migrating Billing table: {e}")

    def migrate_clinical_note_table(self, cursor):
        """Add new columns to ClinicalNote table if they don't exist"""
        try:
            cursor.execute("PRAGMA table_info(ClinicalNote)")
            columns = [info[1] for info in cursor.fetchall()]
            if 'status' not in columns:
                cursor.execute("ALTER TABLE ClinicalNote ADD COLUMN status TEXT DEFAULT 'DRAFT'")
            if 'finalized_at' not in columns:
                cursor.execute("ALTER TABLE ClinicalNote ADD COLUMN finalized_at TEXT")
        except Exception as e:
            self.logger.error(f"Error migrating ClinicalNote table: {e}")

    def create_default_user(self, cursor):
        """Create default admin user"""
        cursor.execute("SELECT id FROM Users WHERE username = ?", ('doctor',))
        if cursor.fetchone() is None:
            salt = secrets.token_hex(16)
            password_hash = self.hash_password("doctor123", salt)
            
            cursor.execute(
                """INSERT INTO Users (username, password_hash, salt, first_name, last_name, speciality, created_at, 
                                    must_change_password) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                ("doctor", password_hash, salt, "John", "Doe", "General Practitioner", datetime.now().isoformat(),
                 1),
            )
            self.logger.info("Default user 'doctor' created")

    def seed_default_templates(self, cursor):
        """Seed pre-built clinical note templates for solo practice"""
        cursor.execute("SELECT COUNT(*) as count FROM NoteTemplates")
        if cursor.fetchone()['count'] == 0:
            templates = [
                (
                    "General Consultation",
                    "General",
                    "Patient presents with chief complaint of [symptoms]. Onset [days/weeks ago]. Severity: [mild/moderate/severe]. Associated symptoms: [fever/cough/fatigue]. No other acute complaints.",
                    "Vitals stable. Alert and oriented x3. HEENT normal. Heart regular rate and rhythm. Lungs clear to auscultation bilaterally. Abdomen soft, non-tender.",
                    "Primary Diagnosis: [Diagnosis/ICD]. Condition is [acute/stable/chronic].",
                    "1. Prescribed [Medication] as directed.\n2. Supportive care and rest.\n3. Return if symptoms worsen or fail to improve in 5 days.",
                    1
                ),
                (
                    "Follow-up / Progress Visit",
                    "Follow-up",
                    "Patient returns for follow-up of [Condition]. Reports symptoms are [improving/unchanged/resolved]. Compliance with prescribed therapy is [good/inconsistent]. No adverse medication side effects reported.",
                    "Physical exam focused on [system]: Findings stable compared to prior visit.",
                    "Status of [Condition]: Well-controlled / Showing expected progress.",
                    "1. Continue current treatment regimen.\n2. Routine labs ordered: [Labs].\n3. Follow up in [1 month / 3 months].",
                    1
                ),
                (
                    "Hypertension / Cardiovascular Review",
                    "Cardiovascular",
                    "Routine follow-up for chronic hypertension. Patient reports no chest pain, shortness of breath, dizziness, or peripheral edema. Takes anti-hypertensives as prescribed.",
                    "BP: [Value] mmHg, HR: [Value] bpm. S1, S2 audible, no murmurs. Peripheral pulses intact. No pedal edema.",
                    "Essential Hypertension (ICD-10 I10) - Currently [Controlled / Uncontrolled].",
                    "1. Maintain antihypertensive regimen.\n2. Low-sodium diet, regular aerobic exercise 30 min/day.\n3. Home BP monitoring log recommended.\n4. Re-evaluate in 3 months with basic metabolic panel.",
                    1
                ),
                (
                    "Pediatric Wellness Exam",
                    "Pediatrics",
                    "Parent brings child for routine wellness check. Appetite good, active and playful. Sleeping well. Normal bowel and bladder habits. No parental concerns.",
                    "Weight: [X] kg ([X] percentile), Height: [X] cm ([X] percentile). Developmentally appropriate milestones met. Clear tympanic membranes. Normal heart sounds. Clear lungs. Abdomen soft.",
                    "Healthy Child Examination. Normal growth and development.",
                    "1. Age-appropriate vaccinations administered / updated.\n2. Guidance on nutrition, safety, and physical activity provided.\n3. Next scheduled checkup in [6 months / 1 year].",
                    1
                ),
                (
                    "Acute Upper Respiratory Infection",
                    "ENT / Respiratory",
                    "Patient complains of sore throat, nasal congestion, runny nose, and dry cough for [X] days. Mild low-grade fever.",
                    "Temp: [X] °C. Pharynx mildly erythematous, no tonsillar exudates. Nasal mucosa congested with clear discharge. Lungs clear bilaterally, no wheezes or rales.",
                    "Acute Upper Respiratory Tract Infection (Likely Viral).",
                    "1. Hydration, warm saline gargles, rest.\n2. Acetaminophen / Ibuprofen for fever or discomfort.\n3. Decongestant / Saline nasal spray as needed.\n4. Re-evaluate if high fever persists >3 days or shortness of breath develops.",
                    1
                ),
            ]
            for title, category, s, o, a, p, is_def in templates:
                cursor.execute("""
                    INSERT INTO NoteTemplates (title, category, subjective, objective, assessment, plan, is_default)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (title, category, s, o, a, p, is_def))
            self.logger.info("Default clinical note templates seeded")

    # -------------------------
    # User Profile & Security
    # -------------------------
    def get_user_details(self, username):
        """Get user details by username"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, username, first_name, last_name, speciality, doctor_title FROM Users WHERE username = ?", (username,))
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Error getting user details: {e}")
            return None

    def update_user_profile(self, current_username, new_data):
        """Update user profile: first_name, last_name, speciality, doctor_title, username, password"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                new_username = new_data.get('username')
                if new_username and new_username != current_username:
                    cursor.execute("SELECT id FROM Users WHERE username = ?", (new_username,))
                    if cursor.fetchone():
                        return False, "Username already exists"

                updates, params = [], []
                for field in ['first_name', 'last_name', 'speciality', 'doctor_title', 'username']:
                    if field in new_data:
                        updates.append(f"{field} = ?")
                        params.append(new_data[field])
                    
                if 'password' in new_data and new_data['password']:
                    if len(new_data['password']) < 8 or new_data['password'] == 'doctor123':
                        return False, "Password must be at least 8 characters and differ from the default"
                    salt = secrets.token_hex(16)
                    password_hash = self.hash_password(new_data['password'], salt)
                    updates.append("password_hash = ?")
                    updates.append("salt = ?")
                    updates.append("must_change_password = 0")
                    params.append(password_hash)
                    params.append(salt)
                
                if not updates:
                    return True, "No changes made"
                    
                params.append(current_username)
                query = f"UPDATE Users SET {', '.join(updates)} WHERE username = ?"
                cursor.execute(query, params)
                conn.commit()
                return True, "Profile updated successfully"
        except Exception as e:
            self.logger.error(f"Error updating user profile: {e}")
            return False, str(e)

    # -------------------------
    # Clinic Information
    # -------------------------
    def has_clinic_info(self):
        """Check if clinic info exists"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM ClinicInfo")
                return cursor.fetchone()['count'] > 0
        except Exception as e:
            self.logger.error(f"Error checking clinic info: {e}")
            return False

    def get_clinic_info(self):
        """Get clinic information"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ClinicInfo ORDER BY id DESC LIMIT 1")
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Error getting clinic info: {e}")
            return None

    def save_clinic_info(self, clinic_name, clinic_address, license_number,
                         tax_rate=None, currency_symbol=None, currency_code=None,
                         currency_position=None):
        """Save or update clinic information.

        Optional arguments default to None, meaning "leave the stored value
        alone". Callers that only know the clinic name must not reset the tax
        rate or the currency.
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM ClinicInfo LIMIT 1")
                existing = cursor.fetchone()

                def keep(value, column, fallback):
                    """Omitted argument -> keep what is already stored."""
                    if value is not None:
                        return value
                    if not existing:
                        return fallback
                    keys = existing.keys()
                    return existing[column] if column in keys else fallback

                if existing:
                    cursor.execute('''
                        UPDATE ClinicInfo
                        SET clinic_name = ?, clinic_address = ?, license_number = ?,
                            tax_rate = ?, currency_symbol = ?, currency_code = ?,
                            currency_position = ?, updated_at = ?
                        WHERE id = ?
                    ''', (clinic_name, clinic_address, license_number,
                          keep(tax_rate, 'tax_rate', 0.0),
                          keep(currency_symbol, 'currency_symbol', '$'),
                          keep(currency_code, 'currency_code', 'USD'),
                          keep(currency_position, 'currency_position', 'before'),
                          datetime.now().isoformat(), existing['id']))
                else:
                    cursor.execute('''
                        INSERT INTO ClinicInfo (clinic_name, clinic_address, license_number,
                                                tax_rate, currency_symbol, currency_code,
                                                currency_position)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (clinic_name, clinic_address, license_number,
                          0.0 if tax_rate is None else tax_rate,
                          '$' if currency_symbol is None else currency_symbol,
                          'USD' if currency_code is None else currency_code,
                          'before' if currency_position is None else currency_position))

                conn.commit()
                return True, "Clinic information saved successfully"
        except Exception as e:
            self.logger.error(f"Error saving clinic info: {e}")
            return False, str(e)

    def get_clinic_currency(self):
        """Return the (code, symbol, position) triple for the clinic."""
        from utils.currency import clinic_currency
        return clinic_currency(self.get_clinic_info())

    # -------------------------
    # Allergies & Vitals
    # -------------------------
    def get_patient_allergies(self, patient_id):
        """Get all allergies for a patient"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM Allergies 
                    WHERE patient_id = ? 
                    ORDER BY severity DESC, created_at DESC
                ''', (patient_id,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error getting allergies: {e}")
            return []

    def add_allergy(self, patient_id, allergen, reaction, severity, onset_date=None, notes=''):
        """Add new allergy for patient"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO Allergies (patient_id, allergen, reaction, severity, onset_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (patient_id, allergen, reaction, severity, onset_date, notes))
                conn.commit()
                return True, "Allergy added successfully"
        except Exception as e:
            self.logger.error(f"Error adding allergy: {e}")
            return False, str(e)

    def update_allergy(self, allergy_id, allergen, reaction, severity, onset_date, notes, is_active):
        """Update existing allergy"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE Allergies 
                    SET allergen = ?, reaction = ?, severity = ?, onset_date = ?, notes = ?, is_active = ?
                    WHERE id = ?
                ''', (allergen, reaction, severity, onset_date, notes, is_active, allergy_id))
                conn.commit()
                return True, "Allergy updated successfully"
        except Exception as e:
            self.logger.error(f"Error updating allergy: {e}")
            return False, str(e)

    def delete_allergy(self, allergy_id):
        """Delete allergy record"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Allergies WHERE id = ?", (allergy_id,))
                conn.commit()
                return True, "Allergy deleted successfully"
        except Exception as e:
            self.logger.error(f"Error deleting allergy: {e}")
            return False, str(e)

    def has_active_allergies(self, patient_id):
        """Check if patient has active allergies"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) as count FROM Allergies WHERE patient_id = ? AND is_active = 1", (patient_id,))
                return cursor.fetchone()['count'] > 0
        except Exception as e:
            self.logger.error(f"Error checking allergies: {e}")
            return False

    def add_vital_signs(self, patient_id, measurement_date, systolic_bp=None, diastolic_bp=None, 
                        heart_rate=None, temperature=None, weight=None, height=None, 
                        oxygen_saturation=None, respiratory_rate=None, notes='', appointment_id=None):
        """Add vital signs record and calculate BMI"""
        try:
            bmi = None
            if weight and height and height > 0:
                height_m = height / 100
                bmi = round(weight / (height_m ** 2), 1)

            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO VitalSigns 
                    (patient_id, appointment_id, measurement_date, systolic_bp, diastolic_bp, 
                     heart_rate, temperature, weight, height, bmi, oxygen_saturation, 
                     respiratory_rate, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (patient_id, appointment_id, measurement_date, systolic_bp, diastolic_bp,
                      heart_rate, temperature, weight, height, bmi, oxygen_saturation,
                      respiratory_rate, notes))
                conn.commit()
                return True, "Vital signs recorded successfully"
        except Exception as e:
            self.logger.error(f"Error adding vital signs: {e}")
            return False, str(e)

    def get_patient_vitals(self, patient_id, limit=20):
        """Get vital signs history for patient"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                if limit:
                    cursor.execute('''
                        SELECT * FROM VitalSigns 
                        WHERE patient_id = ? 
                        ORDER BY measurement_date DESC, created_at DESC
                        LIMIT ?
                    ''', (patient_id, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM VitalSigns 
                        WHERE patient_id = ? 
                        ORDER BY measurement_date DESC, created_at DESC
                    ''', (patient_id,))
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error getting vitals: {e}")
            return []

    def get_latest_vitals(self, patient_id):
        """Get most recent vital signs for patient"""
        vitals = self.get_patient_vitals(patient_id, limit=1)
        return vitals[0] if vitals else None

    def delete_vital_signs(self, vital_id):
        """Delete vital signs record"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM VitalSigns WHERE id = ?", (vital_id,))
                conn.commit()
                return True, "Vital signs deleted successfully"
        except Exception as e:
            self.logger.error(f"Error deleting vital signs: {e}")
            return False, str(e)

    # -------------------------
    # Financials: Billing & Invoicing
    # -------------------------
    def create_bill(self, patient_id, items, total_amount, subtotal_amount=0.0, tax_amount=0.0, status='UNPAID', due_date=None, notes='', currency_code=None, insurance_provider=None, insurance_member_no=None, insurance_pct=None):
        """
        Create a new bill with itemized charges.
        items is a list of dicts: [{'description': 'Consultation', 'amount': 50.0}, ...]

        currency_code, the insurance fields and the coverage split are
        snapshotted onto the invoice. currency_code=None takes the clinic's
        current currency; the insurance fields and insurance_pct default to
        whatever is on the patient's chart, so no caller can accidentally
        produce an invoice that disagrees with the patient record.
        """
        from utils.currency import split_coverage
        try:
            if currency_code is None:
                currency_code = self.get_clinic_currency()[0]
            if insurance_provider is None or insurance_member_no is None or insurance_pct is None:
                on_file = self.get_patient_insurance(patient_id) or {}
                if insurance_provider is None:
                    insurance_provider = on_file.get('provider', '')
                if insurance_member_no is None:
                    insurance_member_no = on_file.get('member_no', '')
                if insurance_pct is None:
                    insurance_pct = on_file.get('coverage_pct', 0.0)

            # No insurer on file means there is nothing to claim against.
            if not (insurance_provider or '').strip() and not (insurance_member_no or '').strip():
                insurance_pct = 0.0

            insurance_amount, patient_amount = split_coverage(total_amount, insurance_pct)

            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO Billing (patient_id, total_amount, subtotal_amount, tax_amount,
                                         status, due_date, notes, currency_code,
                                         insurance_provider, insurance_member_no,
                                         insurance_pct, insurance_amount, patient_amount,
                                         insurance_claim_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'NOT_SUBMITTED')
                ''', (patient_id, total_amount, subtotal_amount, tax_amount, status, due_date,
                      notes, currency_code, insurance_provider or '', insurance_member_no or '',
                      float(insurance_pct or 0.0), insurance_amount, patient_amount))
                bill_id = cursor.lastrowid

                for item in items:
                    cursor.execute('''
                        INSERT INTO BillingItems (bill_id, description, amount)
                        VALUES (?, ?, ?)
                    ''', (bill_id, item.get('description', 'Service'), float(item.get('amount', 0.0))))

                conn.commit()
                return True, bill_id
        except Exception as e:
            self.logger.error(f"Error creating bill: {e}")
            return False, str(e)

    def update_bill_insurance(self, bill_id, insurance_pct, claim_status):
        """Correct an invoice's coverage split or move its claim along.

        Recomputes the insurer/patient amounts from the stored total so the two
        always keep summing back to it.
        """
        from utils.currency import split_coverage
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT total_amount FROM Billing WHERE id = ?", (bill_id,))
                row = cursor.fetchone()
                if not row:
                    return False, "Invoice not found"
                insurance_amount, patient_amount = split_coverage(row['total_amount'], insurance_pct)
                cursor.execute('''
                    UPDATE Billing
                    SET insurance_pct = ?, insurance_amount = ?, patient_amount = ?,
                        insurance_claim_status = ?, updated_at = ?
                    WHERE id = ?
                ''', (float(insurance_pct or 0.0), insurance_amount, patient_amount,
                      claim_status, datetime.now().isoformat(), bill_id))
                conn.commit()
                return True, "Insurance details updated"
        except Exception as e:
            self.logger.error(f"Error updating bill insurance: {e}")
            return False, str(e)

    def update_bill_claim_status(self, bill_id, claim_status):
        """Move an invoice's insurance claim to a new state."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE Billing
                    SET insurance_claim_status = ?, updated_at = ?
                    WHERE id = ?
                ''', (claim_status, datetime.now().isoformat(), bill_id))
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            self.logger.error(f"Error updating claim status: {e}")
            return False

    def get_patient_insurance(self, patient_id):
        """Return the patient's insurance details, or None when self-pay."""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT insurance_provider, insurance_member_no, insurance_coverage_pct
                    FROM Patient WHERE id = ?
                ''', (patient_id,))
                row = cursor.fetchone()
                if not row:
                    return None
                keys = row.keys()
                provider = (row['insurance_provider'] or '').strip()
                member = (row['insurance_member_no'] or '').strip()
                if not provider and not member:
                    return None
                pct = float(row['insurance_coverage_pct'] or 0.0) if 'insurance_coverage_pct' in keys else 0.0
                return {'provider': provider, 'member_no': member, 'coverage_pct': pct}
        except Exception as e:
            self.logger.error(f"Error fetching patient insurance: {e}")
            return None

    def get_bills(self, patient_id=None, status=None, search_text=None):
        """Get all bills with patient details"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT b.*, p.first_name, p.last_name, p.phone, p.email
                    FROM Billing b
                    JOIN Patient p ON b.patient_id = p.id
                    WHERE 1=1
                '''
                params = []
                if patient_id:
                    query += " AND b.patient_id = ?"
                    params.append(patient_id)
                if status and status != 'ALL':
                    query += " AND b.status = ?"
                    params.append(status)
                if search_text:
                    query += " AND (p.first_name LIKE ? OR p.last_name LIKE ? OR b.notes LIKE ?)"
                    wildcard = f"%{search_text}%"
                    params.extend([wildcard, wildcard, wildcard])

                query += " ORDER BY b.created_at DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error fetching bills: {e}")
            return []

    def get_bill_details(self, bill_id):
        """Get full bill details including line items and patient info"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT b.*, p.first_name, p.last_name, p.phone, p.email, p.address
                    FROM Billing b
                    JOIN Patient p ON b.patient_id = p.id
                    WHERE b.id = ?
                ''', (bill_id,))
                bill = cursor.fetchone()
                if not bill:
                    return None

                cursor.execute("SELECT * FROM BillingItems WHERE bill_id = ?", (bill_id,))
                items = cursor.fetchall()
                return {'bill': bill, 'items': items}
        except Exception as e:
            self.logger.error(f"Error fetching bill details: {e}")
            return None

    def update_bill_status(self, bill_id, new_status):
        """Update bill payment status ('PAID', 'UNPAID', 'PARTIAL', 'CANCELLED')"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE Billing 
                    SET status = ?, updated_at = ?
                    WHERE id = ?
                ''', (new_status, datetime.now().isoformat(), bill_id))
                conn.commit()
                return True, "Bill status updated"
        except Exception as e:
            self.logger.error(f"Error updating bill status: {e}")
            return False, str(e)

    def delete_bill(self, bill_id):
        """Delete bill and its line items"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Billing WHERE id = ?", (bill_id,))
                conn.commit()
                return True, "Bill deleted successfully"
        except Exception as e:
            self.logger.error(f"Error deleting bill: {e}")
            return False, str(e)

    # -------------------------
    # Financials: Clinic Expenses
    # -------------------------
    def add_expense(self, category, description, amount, expense_date=None, payment_method='Cash', notes=''):
        """Log a new clinic operating expense"""
        try:
            if not expense_date:
                expense_date = datetime.now().strftime("%Y-%m-%d")
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO Expenses (category, description, amount, expense_date, payment_method, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (category, description, float(amount), expense_date, payment_method, notes))
                conn.commit()
                return True, "Expense recorded successfully"
        except Exception as e:
            self.logger.error(f"Error adding expense: {e}")
            return False, str(e)

    def get_expenses(self, category=None, start_date=None, end_date=None, search_text=None):
        """Get clinic expenses with filtering"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                query = "SELECT * FROM Expenses WHERE 1=1"
                params = []
                if category and category != 'ALL':
                    query += " AND category = ?"
                    params.append(category)
                if start_date:
                    query += " AND expense_date >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND expense_date <= ?"
                    params.append(end_date)
                if search_text:
                    query += " AND (description LIKE ? OR notes LIKE ?)"
                    wildcard = f"%{search_text}%"
                    params.extend([wildcard, wildcard])

                query += " ORDER BY expense_date DESC, id DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error fetching expenses: {e}")
            return []

    def delete_expense(self, expense_id):
        """Delete an expense record"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Expenses WHERE id = ?", (expense_id,))
                conn.commit()
                return True, "Expense deleted successfully"
        except Exception as e:
            self.logger.error(f"Error deleting expense: {e}")
            return False, str(e)

    # -------------------------
    # Financial Analytics & KPIs
    # -------------------------
    def get_financial_kpis(self, currency=None):
        """Get top-level KPI metrics for practice revenue, expenses, and profit.

        Amounts in different currencies are never added together, so when
        `currency` is given only invoices in that currency are counted. It
        defaults to the clinic's current currency, and `foreign_currency_count`
        reports how many invoices were excluded.
        """
        if currency is None:
            currency = self.get_clinic_currency()[0]
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                month_start = datetime.now().strftime("%Y-%m-01")
                same = "IFNULL(currency_code, '') = ?"

                cursor.execute(f"""
                    SELECT COALESCE(SUM(total_amount), 0.0) as total
                    FROM Billing
                    WHERE status = 'PAID' AND {same}
                      AND date(created_at) = date('now', 'localtime')
                """, (currency,))
                today_revenue = cursor.fetchone()['total']

                cursor.execute(f"""
                    SELECT COALESCE(SUM(total_amount), 0.0) as total
                    FROM Billing
                    WHERE status = 'PAID' AND {same} AND date(created_at) >= date(?)
                """, (currency, month_start))
                month_revenue = cursor.fetchone()['total']

                cursor.execute(f"""
                    SELECT COALESCE(SUM(total_amount), 0.0) as total, COUNT(*) as count
                    FROM Billing
                    WHERE status IN ('UNPAID', 'PARTIAL') AND {same}
                """, (currency,))
                pending_row = cursor.fetchone()
                pending_amount = pending_row['total']
                pending_count = pending_row['count']

                # Expenses are clinic operating costs, always in the clinic currency.
                cursor.execute("""
                    SELECT COALESCE(SUM(amount), 0.0) as total
                    FROM Expenses
                    WHERE expense_date >= ?
                """, (month_start,))
                month_expenses = cursor.fetchone()['total']

                # How many invoices sit in some other currency (excluded above).
                cursor.execute("""
                    SELECT COUNT(*) as count FROM Billing
                    WHERE IFNULL(currency_code, '') != ?
                """, (currency,))
                foreign_currency_count = cursor.fetchone()['count']

                # Insurer share not yet settled. Revenue above stays the full
                # invoice total when PAID; this only surfaces what the insurers
                # still owe, so a stalled claim does not hide in the totals.
                cursor.execute(f"""
                    SELECT COALESCE(SUM(insurance_amount), 0.0) as total,
                           COUNT(*) as count
                    FROM Billing
                    WHERE {same}
                      AND IFNULL(insurance_claim_status, 'NOT_SUBMITTED') != 'SETTLED'
                      AND IFNULL(insurance_amount, 0) > 0
                """, (currency,))
                claim_row = cursor.fetchone()

                return {
                    'today_revenue': today_revenue,
                    'month_revenue': month_revenue,
                    'month_expenses': month_expenses,
                    'net_profit': month_revenue - month_expenses,
                    'pending_amount': pending_amount,
                    'pending_count': pending_count,
                    'currency': currency,
                    'foreign_currency_count': foreign_currency_count,
                    'insurance_pending_amount': claim_row['total'],
                    'insurance_pending_count': claim_row['count'],
                }
        except Exception as e:
            self.logger.error(f"Error calculating financial KPIs: {e}")
            return {
                'today_revenue': 0.0,
                'month_revenue': 0.0,
                'month_expenses': 0.0,
                'net_profit': 0.0,
                'pending_amount': 0.0,
                'pending_count': 0,
                'currency': currency,
                'foreign_currency_count': 0,
                'insurance_pending_amount': 0.0,
                'insurance_pending_count': 0,
            }

    def get_daily_financial_stats(self, days=14, currency=None):
        """Get daily revenue and expenses breakdown for charts over the last N days.

        Revenue is restricted to `currency` (default: the clinic currency) so the
        chart never adds unlike currencies together.
        """
        if currency is None:
            currency = self.get_clinic_currency()[0]
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                results = []
                today = datetime.now().date()
                for i in range(days - 1, -1, -1):
                    day_date = today - timedelta(days=i)
                    day_str = day_date.strftime("%Y-%m-%d")

                    cursor.execute("""
                        SELECT COALESCE(SUM(total_amount), 0.0) as total
                        FROM Billing
                        WHERE status = 'PAID' AND IFNULL(currency_code, '') = ?
                          AND date(created_at) = ?
                    """, (currency, day_str))
                    rev = cursor.fetchone()['total']

                    cursor.execute("""
                        SELECT COALESCE(SUM(amount), 0.0) as total
                        FROM Expenses
                        WHERE expense_date = ?
                    """, (day_str,))
                    exp = cursor.fetchone()['total']

                    results.append({
                        'date': day_str,
                        'day_label': day_date.strftime("%b %d"),
                        'revenue': rev,
                        'expenses': exp
                    })
                return results
        except Exception as e:
            self.logger.error(f"Error getting daily financial stats: {e}")
            return []

    # -------------------------
    # Multi-Medication Prescriptions
    # -------------------------
    def create_prescription(self, patient_id, doctor_name, prescription_date, items, instructions='', appointment_id=None, pdf_path=None):
        """
        Create a prescription with multi-medication items.
        items list: [{'medication_name': 'Amoxicillin', 'dosage': '500mg', 'frequency': '3x/day', 'duration': '7 days'}, ...]
        """
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO Prescription (patient_id, appointment_id, prescription_date, prescribing_doctor, instructions, pdf_file_path)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (patient_id, appointment_id, prescription_date, doctor_name, instructions, pdf_path))
                rx_id = cursor.lastrowid

                for item in items:
                    cursor.execute('''
                        INSERT INTO PrescriptionItems (prescription_id, medication_name, dosage, frequency, duration)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (rx_id, item.get('medication_name', ''), item.get('dosage', ''), item.get('frequency', ''), item.get('duration', '')))

                conn.commit()
                return True, rx_id
        except Exception as e:
            self.logger.error(f"Error creating prescription: {e}")
            return False, str(e)

    def get_prescriptions(self, patient_id=None, search_text=None):
        """Get list of prescriptions with patient names and count of medications"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                query = '''
                    SELECT rx.*, p.first_name, p.last_name,
                           (SELECT COUNT(*) FROM PrescriptionItems WHERE prescription_id = rx.id) as med_count,
                           (SELECT GROUP_CONCAT(medication_name, ', ') FROM PrescriptionItems WHERE prescription_id = rx.id) as med_names
                    FROM Prescription rx
                    JOIN Patient p ON rx.patient_id = p.id
                    WHERE 1=1
                '''
                params = []
                if patient_id:
                    query += " AND rx.patient_id = ?"
                    params.append(patient_id)
                if search_text:
                    query += " AND (p.first_name LIKE ? OR p.last_name LIKE ? OR rx.instructions LIKE ?)"
                    wildcard = f"%{search_text}%"
                    params.extend([wildcard, wildcard, wildcard])

                query += " ORDER BY rx.prescription_date DESC, rx.id DESC"
                cursor.execute(query, params)
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error fetching prescriptions: {e}")
            return []

    def get_prescription_details(self, prescription_id):
        """Get complete prescription with all medication line items"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT rx.*, p.first_name, p.last_name, p.date_of_birth, p.gender, p.address
                    FROM Prescription rx
                    JOIN Patient p ON rx.patient_id = p.id
                    WHERE rx.id = ?
                ''', (prescription_id,))
                rx = cursor.fetchone()
                if not rx:
                    return None

                cursor.execute("SELECT * FROM PrescriptionItems WHERE prescription_id = ?", (prescription_id,))
                items = cursor.fetchall()
                return {'prescription': rx, 'items': items}
        except Exception as e:
            self.logger.error(f"Error fetching prescription details: {e}")
            return None

    def update_prescription_status(self, prescription_id, new_status):
        """Update prescription status ('ACTIVE', 'COMPLETED', 'CANCELLED')"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE Prescription SET status = ? WHERE id = ?", (new_status, prescription_id))
                conn.commit()
                return True, "Prescription updated"
        except Exception as e:
            self.logger.error(f"Error updating prescription status: {e}")
            return False, str(e)

    def delete_prescription(self, prescription_id):
        """Delete prescription and medication items"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Prescription WHERE id = ?", (prescription_id,))
                conn.commit()
                return True, "Prescription deleted successfully"
        except Exception as e:
            self.logger.error(f"Error deleting prescription: {e}")
            return False, str(e)

    # -------------------------
    # Note Templates
    # -------------------------
    def get_note_templates(self):
        """Get all clinical note templates"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM NoteTemplates ORDER BY is_default DESC, title ASC")
                return cursor.fetchall()
        except Exception as e:
            self.logger.error(f"Error getting note templates: {e}")
            return []

    def get_note_template(self, template_id):
        """Get a single note template"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM NoteTemplates WHERE id = ?", (template_id,))
                return cursor.fetchone()
        except Exception as e:
            self.logger.error(f"Error getting note template: {e}")
            return None

    def add_note_template(self, title, category, subjective, objective, assessment, plan, is_default=0):
        """Save a new clinical note template"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO NoteTemplates (title, category, subjective, objective, assessment, plan, is_default)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (title, category, subjective, objective, assessment, plan, is_default))
                conn.commit()
                return True, "Template saved successfully"
        except Exception as e:
            self.logger.error(f"Error saving note template: {e}")
            return False, str(e)

    def delete_note_template(self, template_id):
        """Delete a custom note template"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM NoteTemplates WHERE id = ? AND is_default = 0", (template_id,))
                conn.commit()
                return True, "Template deleted"
        except Exception as e:
            self.logger.error(f"Error deleting note template: {e}")
            return False, str(e)

    # -------------------------
    # Patient 360 Full Profile
    # -------------------------
    def get_patient_360(self, patient_id):
        """Aggregate full 360 medical and financial history for a patient"""
        try:
            with self.get_db_connection() as conn:
                cursor = conn.cursor()
                # 1. Patient info
                cursor.execute("SELECT * FROM Patient WHERE id = ?", (patient_id,))
                patient = cursor.fetchone()
                if not patient:
                    return None

                # 2. Allergies
                cursor.execute("SELECT * FROM Allergies WHERE patient_id = ? ORDER BY severity DESC", (patient_id,))
                allergies = cursor.fetchall()

                # 3. Vital signs
                cursor.execute("SELECT * FROM VitalSigns WHERE patient_id = ? ORDER BY measurement_date DESC LIMIT 15", (patient_id,))
                vitals = cursor.fetchall()

                # 4. Clinical Notes
                cursor.execute("SELECT * FROM ClinicalNote WHERE patient_id = ? ORDER BY note_date DESC", (patient_id,))
                notes = cursor.fetchall()

                # 5. Prescriptions with medication items
                cursor.execute('''
                    SELECT rx.*, 
                           (SELECT GROUP_CONCAT(medication_name, ', ') FROM PrescriptionItems WHERE prescription_id = rx.id) as med_names
                    FROM Prescription rx 
                    WHERE rx.patient_id = ? 
                    ORDER BY rx.prescription_date DESC
                ''', (patient_id,))
                prescriptions = cursor.fetchall()

                # 6. Appointments
                cursor.execute("SELECT * FROM Appointment WHERE patient_id = ? ORDER BY datetime DESC", (patient_id,))
                appointments = cursor.fetchall()

                # 7. Billing & Invoices
                cursor.execute("SELECT * FROM Billing WHERE patient_id = ? ORDER BY created_at DESC", (patient_id,))
                bills = cursor.fetchall()

                # Financial totals for this patient
                total_billed = sum(b['total_amount'] for b in bills)
                total_paid = sum(b['total_amount'] for b in bills if b['status'] == 'PAID')
                balance_due = sum(b['total_amount'] for b in bills if b['status'] in ('UNPAID', 'PARTIAL'))

                return {
                    'patient': patient,
                    'allergies': allergies,
                    'vitals': vitals,
                    'notes': notes,
                    'prescriptions': prescriptions,
                    'appointments': appointments,
                    'bills': bills,
                    'total_billed': total_billed,
                    'total_paid': total_paid,
                    'balance_due': balance_due
                }
        except Exception as e:
            self.logger.error(f"Error aggregating Patient 360: {e}")
            return None

    # -------------------------
    # Utilities, Password & Backups
    # -------------------------
    @staticmethod
    def hash_password(password, salt):
        return hashlib.sha256((password + salt).encode("utf-8")).hexdigest()

    def verify_password(self, stored_hash, stored_salt, provided_password):
        return secrets.compare_digest(self.hash_password(provided_password, stored_salt), stored_hash)

    def must_change_password(self, username):
        with self.get_db_connection() as conn:
            row = conn.execute("SELECT must_change_password FROM Users WHERE username = ?", (username,)).fetchone()
            return bool(row and row['must_change_password'])

    def backup_database(self, backup_path=None):
        """Make a consistent SQLite snapshot and atomically install it at the destination."""
        if not backup_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.get_app_data_dir(), "backups", f"clinic_backup_{timestamp}.db")
        temp_path = None
        try:
            backup_path = os.path.abspath(backup_path)
            if os.path.normcase(backup_path) == os.path.normcase(os.path.abspath(self.db_path)):
                raise ValueError("Backup destination cannot be the live database")
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            if not os.path.isfile(self.db_path):
                raise FileNotFoundError(self.db_path)
            fd, temp_path = tempfile.mkstemp(prefix=".clinic_backup_", suffix=".db", dir=os.path.dirname(backup_path))
            os.close(fd)
            with closing(sqlite3.connect(self.db_path, timeout=30.0)) as source:
                with closing(sqlite3.connect(temp_path)) as destination:
                    source.backup(destination)
                    result = destination.execute("PRAGMA quick_check").fetchone()[0]
                    if result != "ok":
                        raise sqlite3.DatabaseError(f"Backup integrity check failed: {result}")
            os.replace(temp_path, backup_path)
            self.logger.info(f"Database backed up to: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except OSError as cleanup_error:
                    self.logger.warning(f"Could not remove temporary backup: {cleanup_error}")

    def perform_auto_backup(self, max_backups=7):
        """Automatically create rotating daily backups in AppData/backups"""
        try:
            app_dir = self.get_app_data_dir()
            backup_dir = os.path.join(app_dir, "backups")
            os.makedirs(backup_dir, exist_ok=True)

            date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
            target_path = os.path.join(backup_dir, f"clinic_autobackup_{date_str}.db")
            if not self.backup_database(target_path):
                return None

            # Cleanup older backups keeping last max_backups
            backups = sorted([os.path.join(backup_dir, f) for f in os.listdir(backup_dir) if f.startswith("clinic_autobackup_") and f.endswith(".db")])
            if len(backups) > max_backups:
                for old in backups[:-max_backups]:
                    try:
                        os.remove(old)
                    except Exception:
                        pass

            self.logger.info(f"Auto-backup complete: {target_path}")
            return target_path
        except Exception as e:
            self.logger.error(f"Auto-backup failed: {e}")
            return None

    # -------------------------
# Global instance
db_manager = DatabaseManager()
