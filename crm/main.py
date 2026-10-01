
import sys
import os
import ctypes
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from styles.theme import Theme
from ui.login_window import LoginWindow
from ui.onboarding_window import OnboardingWindow
from ui.standalone_profile import StandaloneProfileWindow
from ui.main_window import MainWindow
from data import db_manager
from utils.localization import install as install_localization

def main():
    # Set Windows AppUserModelID so taskbar displays the app icon properly
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('digispher.emr.app.2.0')
    except Exception:
        pass

    app = QApplication(sys.argv)
    install_localization(app)
    app.setStyle("Fusion") # Good base style for cross-platform consistency
    app.setPalette(Theme.get_palette()) # Prevent OS Dark Mode bleed
    
    # Set Application Window Icon (.ico)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(base_dir, "app_icon.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    elif os.path.exists(os.path.join(base_dir, "dc.ico")):
        app.setWindowIcon(QIcon(os.path.join(base_dir, "dc.ico")))
    
    # Apply Global Theme
    app.setStyleSheet(Theme.STYLESHEET)
    
    # References to windows
    login_window = None
    onboarding_window = None
    profile_window = None
    main_window = None
    current_username = None

    def show_login():
        """Show login window"""
        nonlocal login_window
        login_window = LoginWindow()
        login_window.login_successful.connect(on_login_success)
        login_window.show()

    def on_login_success(username):
        """Handle successful login - check if onboarding is needed"""
        nonlocal current_username
        current_username = username
        
        # Check if clinic info exists
        if not db_manager.has_clinic_info():
            # First time setup - show onboarding
            show_onboarding()
        elif db_manager.must_change_password(username):
            show_profile_setup()
        else:
            # Clinic info exists - go directly to dashboard
            show_main_window()

    def show_onboarding():
        """Show onboarding window for clinic setup"""
        nonlocal onboarding_window
        login_window.close()
        
        onboarding_window = OnboardingWindow()
        onboarding_window.onboarding_complete.connect(show_profile_setup)
        onboarding_window.show()

    def show_profile_setup():
        """Show profile setup window for password change"""
        nonlocal profile_window
        if onboarding_window:
            onboarding_window.close()
        elif login_window:
            login_window.close()
        
        profile_window = StandaloneProfileWindow(current_username)
        profile_window.setup_complete.connect(on_profile_complete)
        profile_window.show()

    def on_profile_complete(username):
        """Handle profile setup completion"""
        nonlocal current_username
        current_username = username
        profile_window.close()
        show_main_window()

    def show_main_window():
        """Show main dashboard window"""
        nonlocal main_window
        if login_window:
            login_window.close()
        
        main_window = MainWindow(current_username)
        main_window.show()

    # Start with login
    show_login()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
