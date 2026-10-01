from PySide6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
                               QPushButton, QStackedWidget, QLabel, QFrame, QStyle, QApplication)
from PySide6.QtCore import Qt, QSize, QTimer, QEvent
from PySide6.QtGui import QIcon
from styles.theme import Theme
from data import db_manager
from utils.helpers import resource_path
from utils.localization import manager

from ui.dashboard_view import DashboardView
from ui.patients_view import PatientsView
from ui.appointments_view import AppointmentsView
from ui.notes_view import NotesView
from ui.prescriptions_view import PrescriptionsView
from ui.profile_view import ProfileView
from ui.help_view import HelpView
from ui.settings_view import SettingsView
from ui.finances_view import FinancesView

class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.username = username
        
        # Fetch initial user details
        user = db_manager.get_user_details(self.username)
        self.first_name = user['first_name'] if user and user['first_name'] else ""
        self.last_name = user['last_name'] if user and user['last_name'] else ""
        self.speciality = user['speciality'] if user and user['speciality'] else "General"
        
        self.setWindowTitle("DigiSpher EMR - EMR System")
        self.setMinimumSize(950, 600)
        self.resize(1200, 680)
        
        self.setup_ui()
        manager().changed.connect(self._language_changed)
        self.center_on_screen()

        # Inactivity Timer
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.handle_inactivity_timeout)
        self.inactivity_timer.start(15 * 60 * 1000) # Default 15 mins
        
        # Install event filter to detect activity
        QApplication.instance().installEventFilter(self)

    def center_on_screen(self):
        """Center the window within the primary screen available geometry"""
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            # Ensure window dimensions fit inside screen work area
            target_w = min(1200, geo.width() - 20)
            target_h = min(680, geo.height() - 40)
            self.resize(target_w, target_h)
            x = geo.x() + max(0, (geo.width() - self.width()) // 2)
            y = geo.y() + max(0, (geo.height() - self.height()) // 2)
            self.move(x, y)

    def setup_ui(self):
        # Central Widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        self.setWindowIcon(QIcon(resource_path("app_icon.ico")))

        # Main Layout (Horizontal: Sidebar + Content)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Sidebar (Fixed width)
        sidebar = self.create_sidebar()
        main_layout.addWidget(sidebar)

        # 2. Right Content Area (Vertical: Header + Stack)
        content_area = QWidget()
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(24, 24, 24, 24)
        content_layout.setSpacing(20)

        # Header
        header = self.create_header()
        content_layout.addWidget(header)

        # Stacked Widget for Views
        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        main_layout.addWidget(content_area)

        # Initialize Views
        self.init_views()

    def create_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)

        # App Logo/Title
        title_layout = QHBoxLayout()
        title_layout.setSpacing(10)
        title_layout.setContentsMargins(0, 0, 0, 16)

        import os
        logo_path = resource_path("app_icon.png")
        if os.path.exists(logo_path):
            from PySide6.QtGui import QPixmap
            logo_lbl = QLabel()
            pix = QPixmap(logo_path).scaled(32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
            logo_lbl.setFixedSize(32, 32)
            title_layout.addWidget(logo_lbl)

        title = QLabel("DigiSpher EMR")
        title.setStyleSheet("font-size: 19px; font-weight: 800; color: #FFFFFF;")
        title_layout.addWidget(title)
        title_layout.addStretch()
        layout.addLayout(title_layout)

        # Navigation Buttons
        self.nav_group = []
        
        nav_items = [
            ("Dashboard", 0, QStyle.SP_ComputerIcon),
            ("Patients", 1, QStyle.SP_FileDialogDetailedView),
            ("Appointments", 2, QStyle.SP_FileDialogListView),
            ("Clinical Notes", 3, QStyle.SP_FileDialogContentsView),
            ("Prescriptions", 4, QStyle.SP_FileIcon),
            ("Finances", 5, QStyle.SP_DriveHDIcon)
        ]

        for text, index, icon_type in nav_items:
            btn = QPushButton(text)
            btn.setProperty("class", "nav-btn")
            btn.setObjectName("nav-btn")
            btn.setCheckable(True)
            btn.setAutoExclusive(True)
            btn.setCursor(Qt.PointingHandCursor)
            
            icon = self.style().standardIcon(icon_type)
            btn.setIcon(icon)
            btn.setIconSize(QSize(20, 20))
            
            btn.clicked.connect(lambda checked, idx=index: self.switch_view(idx))
            layout.addWidget(btn)
            self.nav_group.append(btn)

        layout.addStretch()
        
        # Bottom Actions (Settings, Help)
        bottom_items = [
            ("Settings", 7, QStyle.SP_FileDialogDetailedView),
            ("Help", 8, QStyle.SP_MessageBoxInformation)
        ]
        
        for text, index, icon_type in bottom_items:
            btn = QPushButton(text)
            btn.setProperty("class", "nav-btn")
            btn.setObjectName("nav-btn")
            btn.setCursor(Qt.PointingHandCursor)
            btn.setIcon(self.style().standardIcon(icon_type))
            btn.setIconSize(QSize(20, 20))
            btn.clicked.connect(lambda checked, idx=index: self.switch_view(idx))
            layout.addWidget(btn)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        # Lighter separator for dark background
        line.setStyleSheet(f"background-color: #334155; margin: 8px 0;") 
        layout.addWidget(line)

        # User Profile Card
        self.profile_btn = QPushButton()
        self.profile_btn.setCursor(Qt.PointingHandCursor)
        # Updated for dark mode: transparent/darker bg, white text
        self.profile_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(255, 255, 255, 0.05);
                border: 1px solid #334155;
                border-radius: 12px;
                padding: 8px;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
                border-color: {Theme.PRIMARY};
            }}
        """)
        
        profile_layout = QHBoxLayout(self.profile_btn)
        profile_layout.setContentsMargins(8, 8, 8, 8)
        profile_layout.setSpacing(12)
        
        # Avatar
        avatar = QLabel("👨‍⚕️")
        avatar.setStyleSheet("font-size: 24px; background-color: transparent;")
        profile_layout.addWidget(avatar)
        
        # Text Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        self.name_label = QLabel(f"Dr. {self.first_name}")
        self.name_label.setProperty("i18n_skip", True)
        self.name_label.setStyleSheet(f"font-weight: 700; color: #FFFFFF; font-size: 13px; background-color: transparent;")
        
        self.speciality_label = QLabel(f'{self.speciality}')
        self.speciality_label.setProperty("i18n_skip", True)
        self.speciality_label.setStyleSheet(f"color: #94A3B8; font-size: 11px; background-color: transparent;")
        
        info_layout.addWidget(self.name_label)
        info_layout.addWidget(self.speciality_label)
        profile_layout.addLayout(info_layout)
        
        self.profile_btn.clicked.connect(lambda: self.switch_view(6))
        layout.addWidget(self.profile_btn)

        # Logout Button (Red background, White text)
        logout_btn = QPushButton("Sign Out")
        logout_btn.setCursor(Qt.PointingHandCursor)
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ERROR};
                color: #FFFFFF;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-weight: 600;
                font-size: 12px;
                text-align: center;
                margin-top: 8px;
            }}
            QPushButton:hover {{
                background-color: #DC2626; /* Red 600 */
            }}
        """)
        logout_btn.clicked.connect(self.logout)
        layout.addWidget(logout_btn)

        return sidebar

    def create_header(self):
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        self.page_title = QLabel("Dashboard")
        self.page_title.setProperty("class", "title")
        self.page_title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {Theme.TEXT_PRIMARY};")
        
        layout.addWidget(self.page_title)
        layout.addStretch()
        
        return header

    def init_views(self):
        # Create Views
        self.dashboard_view = DashboardView()
        self.dashboard_view.add_patient_requested.connect(self.handle_add_patient)
        self.dashboard_view.new_appointment_requested.connect(self.handle_new_appointment)
        self.dashboard_view.new_invoice_requested.connect(self.handle_new_invoice)
        self.dashboard_view.new_note_requested.connect(self.handle_new_note)
        self.dashboard_view.new_prescription_requested.connect(self.handle_new_prescription)
        self.dashboard_view.view_notes_requested.connect(lambda: self.switch_view(3))
        self.dashboard_view.view_prescriptions_requested.connect(lambda: self.switch_view(4))
        self.dashboard_view.view_finances_requested.connect(lambda: self.switch_view(5))
        self.dashboard_view.view_patients_requested.connect(lambda: self.switch_view(1))
        self.dashboard_view.view_appointments_requested.connect(lambda: self.switch_view(2))
        
        self.patients_view = PatientsView()
        self.appointments_view = AppointmentsView()
        self.notes_view = NotesView()
        self.prescriptions_view = PrescriptionsView()
        self.finances_view = FinancesView()
        self.profile_view = ProfileView(self.username)
        self.profile_view.profile_updated.connect(self.on_profile_updated)
        
        # Settings View
        self.settings_view = SettingsView(self.username)
        self.settings_view.request_profile_view.connect(lambda: self.switch_view(6))
        self.settings_view.inactivity_timeout_changed.connect(self.update_inactivity_timer)
        
        self.help_view = HelpView()
        
        # Add to stack
        self.stack.addWidget(self.dashboard_view)      # 0
        self.stack.addWidget(self.patients_view)       # 1
        self.stack.addWidget(self.appointments_view)   # 2
        self.stack.addWidget(self.notes_view)          # 3
        self.stack.addWidget(self.prescriptions_view)  # 4
        self.stack.addWidget(self.finances_view)       # 5
        self.stack.addWidget(self.profile_view)        # 6
        self.stack.addWidget(self.settings_view)       # 7
        self.stack.addWidget(self.help_view)           # 8
        
        # Select first tab
        if self.nav_group:
            self.nav_group[0].setChecked(True)

    def switch_view(self, index):
        self.stack.setCurrentIndex(index)
        titles = ["Dashboard", "Patients", "Appointments", "Clinical Notes", "Prescriptions", "Practice Finances", "Profile", "Settings", "Help"]
        if 0 <= index < len(titles):
            self.page_title.setText(titles[index])
            
        # Synchronize active sidebar button
        if hasattr(self, 'nav_group') and 0 <= index < len(self.nav_group):
            self.nav_group[index].setChecked(True)
            
        # Refresh data when switching
        if index == 0:
            self.dashboard_view.refresh_data()
        elif index == 1:
            self.patients_view.load_patients()
        elif index == 2:
            self.appointments_view.load_appointments()
        elif index == 3:
            self.notes_view.load_notes()
        elif index == 4:
            self.prescriptions_view.load_prescriptions()
        elif index == 5:
            self.finances_view.refresh_all()
        elif index == 6:
            self.profile_view.load_data()
            self.update_sidebar_profile()

    def _language_changed(self, locale):
        # Data-bearing views refresh their display labels from the original DB codes.
        self.switch_view(self.stack.currentIndex())

    def update_sidebar_profile(self):
        # Update sidebar with latest data from profile view (or DB)
        user = db_manager.get_user_details(self.username)
        if user:
            self.first_name = user['first_name'] if user['first_name'] else ""
            self.last_name = user['last_name'] if user['last_name'] else ""
            self.speciality = user['speciality'] if user['speciality'] else "General"
            
            self.name_label.setText(f"Dr. {self.first_name}")
            self.speciality_label.setText(self.speciality)

    def on_profile_updated(self, new_username):
        self.username = new_username
        self.update_sidebar_profile()

    def handle_add_patient(self):
        self.switch_view(1) # Switch to Patients view
        self.patients_view.show_add_patient_dialog()

    def handle_new_appointment(self):
        self.switch_view(2) # Switch to Appointments view
        self.appointments_view.show_add_dialog()

    def handle_new_note(self):
        self.switch_view(3) # Switch to Clinical Notes view
        self.notes_view.show_add_dialog()

    def handle_new_prescription(self):
        self.switch_view(4) # Switch to Prescriptions view
        self.prescriptions_view.show_add_dialog()

    def handle_new_invoice(self):
        self.switch_view(5) # Switch to Finances view
        self.finances_view.open_create_invoice_dialog()

    def closeEvent(self, event):
        """Auto-backup database on exit to protect solopreneur data"""
        try:
            db_manager.perform_auto_backup()
        except Exception as e:
            print(f"Auto-backup on exit: {e}")
        event.accept()

    # Inactivity and Logout Logic
    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.KeyPress, QEvent.MouseButtonPress):
            self.reset_inactivity_timer()
        return super().eventFilter(obj, event)

    def reset_inactivity_timer(self):
        self.inactivity_timer.start() # Restarts with existing interval

    def handle_inactivity_timeout(self):
        print("Inactivity timeout reached. Logging out.")
        self.logout()

    def update_inactivity_timer(self, minutes):
        self.inactivity_timer.setInterval(minutes * 60 * 1000)
        self.inactivity_timer.start()

    def logout(self):
        from ui.login_window import LoginWindow
        self.login_window = LoginWindow()
        self.login_window.login_successful.connect(self.on_relogin)
        self.login_window.show()
        self.close()

    def on_relogin(self, username):
        self.new_main = MainWindow(username)
        self.new_main.show()
        self.login_window.close()
