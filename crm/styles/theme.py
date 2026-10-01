
class Theme:
    # Colors
    PRIMARY = "#5B73A7"      # Blue 600
    PRIMARY_HOVER = "#1D4ED8" # Blue 700
    SECONDARY = "#64748B"    # Slate 500
    ACCENT = "#0F172A"       # Slate 900
    
    BACKGROUND = "#F8FAFC"   # Slate 50
    SURFACE = "#FFFFFF"      # White
    
    TEXT_PRIMARY = "#0F172A" # Slate 900
    TEXT_SECONDARY = "#64748B" # Slate 500
    TEXT_INVERSE = "#FFFFFF" # White
    
    ERROR = "#EF4444"        # Red 500
    SUCCESS = "#22C55E"      # Green 500
    WARNING = "#F59E0B"      # Amber 500
    BORDER = "#E2E8F0"       # Slate 200 (used for borders across app)

    # Fonts
    FONT_FAMILY = "Segoe UI" # Standard Windows font, clean and modern
    FONT_SIZE_SMALL = "12px"
    FONT_SIZE_NORMAL = "14px"
    FONT_SIZE_LARGE = "16px"
    FONT_SIZE_TITLE = "24px"

    # Styles
    STYLESHEET = f"""
        QMainWindow, QDialog {{
            background-color: {BACKGROUND};
        }}
        
        QWidget {{
            font-family: "{FONT_FAMILY}";
            font-size: {FONT_SIZE_NORMAL};
            color: {TEXT_PRIMARY};
        }}
        
        /* Specific label styling to ensure visibility */
        QLabel {{
            color: {TEXT_PRIMARY};
        }}

        /* Cards / Containers */
        QFrame.card {{
            background-color: {SURFACE};
            border-radius: 12px;
            border: 1px solid #E2E8F0; /* Slate 200 */
        }}

        /* Buttons */
        QPushButton {{
            background-color: {PRIMARY};
            color: {TEXT_INVERSE};
            border: none;
            border-radius: 8px;
            padding: 10px 20px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {PRIMARY_HOVER};
        }}
        QPushButton:pressed {{
            background-color: {ACCENT};
        }}
        QPushButton.secondary {{
            background-color: transparent;
            color: {TEXT_SECONDARY};
            border: 1px solid {SECONDARY};
        }}
        QPushButton.secondary:hover {{
            background-color: #F1F5F9; /* Slate 100 */
            color: {TEXT_PRIMARY};
        }}
        QPushButton.danger {{
            background-color: {ERROR};
        }}
        QPushButton.danger:hover {{
            background-color: #DC2626; /* Red 600 */
        }}

        /* Inputs */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid #CBD5E1; /* Slate 300 */
            border-radius: 8px;
            padding: 8px;
            selection-background-color: {PRIMARY};
        }}
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
            border: 2px solid {PRIMARY};
        }}
        
        /* ComboBox (Dropdown) */
        QComboBox {{
            background-color: {SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 8px;
            min-height: 25px;
        }}
        QComboBox:hover {{
            background-color: #F1F5F9;
            color: {TEXT_PRIMARY};
            border: 1px solid {PRIMARY};
        }}
        QComboBox:focus {{
            border: 2px solid {PRIMARY};
        }}
        QComboBox::drop-down {{
            border: none;
            width: 30px;
        }}
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {TEXT_SECONDARY};
            width: 0;
            height: 0;
            margin-right: 10px;
        }}
        QComboBox QAbstractItemView {{
            background-color: {SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid #CBD5E1;
            selection-background-color: {PRIMARY};
            selection-color: {TEXT_INVERSE};
            outline: none;
        }}
        
        /* Date/Time Inputs */
        QDateEdit, QDateTimeEdit, QTimeEdit {{
            background-color: {SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            padding: 8px;
            min-height: 25px;
        }}
        QDateEdit:hover, QDateTimeEdit:hover, QTimeEdit:hover {{
            border: 1px solid {PRIMARY};
        }}
        QDateEdit:focus, QDateTimeEdit:focus, QTimeEdit:focus {{
            border: 2px solid {PRIMARY};
        }}
        QDateEdit::drop-down, QDateTimeEdit::drop-down, QTimeEdit::drop-down {{
            border: none;
            width: 30px;
        }}
        QDateEdit::down-arrow, QDateTimeEdit::down-arrow, QTimeEdit::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {TEXT_SECONDARY};
            width: 0;
            height: 0;
            margin-right: 10px;
        }}
        
        /* Calendar Popup Enhanced */
        QCalendarWidget {{
            background-color: {SURFACE};
            border: 1px solid #CBD5E1;
            border-radius: 8px;
            min-width: 280px;
            min-height: 220px;
        }}
        QCalendarWidget QWidget#qt_calendar_navigationbar {{
            background-color: #F8FAFC;
            border-bottom: 1px solid #E2E8F0;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            min-height: 36px;
        }}
        QCalendarWidget QToolButton {{
            background-color: transparent;
            color: {TEXT_PRIMARY};
            font-weight: 700;
            font-size: 13px;
            border: none;
            border-radius: 6px;
            padding: 4px 8px;
        }}
        QCalendarWidget QToolButton:hover {{
            background-color: #E2E8F0;
            color: #1E3A8A;
        }}
        QCalendarWidget QMenu {{
            background-color: {SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid #CBD5E1;
            border-radius: 6px;
            padding: 4px;
        }}
        QCalendarWidget QSpinBox {{
            background-color: {SURFACE};
            color: {TEXT_PRIMARY};
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            padding: 2px;
            font-weight: 600;
        }}
        QCalendarWidget QTableView {{
            background-color: {SURFACE};
            color: {TEXT_PRIMARY};
            border: none;
            selection-background-color: #E0E7FF;
            selection-color: #1E3A8A;
            alternate-background-color: {SURFACE};
            gridline-color: transparent;
            outline: none;
        }}
        QCalendarWidget QTableView::item {{
            color: {TEXT_PRIMARY};
            padding: 0px;
            margin: 0px;
            border-radius: 6px;
        }}
        QCalendarWidget QTableView::item:hover {{
            background-color: #F1F5F9;
            color: {TEXT_PRIMARY};
        }}
        QCalendarWidget QTableView::item:selected {{
            background-color: #E0E7FF;
            color: #1E3A8A;
            font-weight: bold;
        }}
        QCalendarWidget QTableView::item:disabled {{
            color: #94A3B8;
        }}
        QCalendarWidget QHeaderView::section {{
            background-color: #F8FAFC;
            color: #64748B;
            font-weight: 600;
            font-size: 11px;
            border: none;
            padding: 2px 0px;
        }}

        /* Labels */
        QLabel.title {{
            font-size: {FONT_SIZE_TITLE};
            font-weight: bold;
            color: {TEXT_PRIMARY};
        }}
        QLabel.subtitle {{
            font-size: {FONT_SIZE_LARGE};
            font-weight: 600;
            color: {TEXT_SECONDARY};
        }}
        
        /* Sidebar */
        QWidget#sidebar {{
            background-color: #0F172A; /* Slate 900 - Dark background */
            border-right: 1px solid #1E293B; /* Slate 800 */
            color: #F8FAFC; /* Slate 50 - White text */
        }}
        
        /* Navigation Buttons */
        QPushButton.nav-btn {{
            text-align: left;
            padding: 12px 16px;
            background-color: transparent;
            color: #94A3B8; /* Slate 400 */
            border-radius: 8px;
            margin: 4px 8px;
            font-weight: 600;
            font-size: 14px;
            border: none;
            qproperty-iconSize: 20px 20px;
        }}
        
        QPushButton.nav-btn:hover {{
            background-color: rgba(255, 255, 255, 0.1);
            color: #F8FAFC; /* White */
        }}
        
        QPushButton.nav-btn:checked {{
            background-color: {PRIMARY}; /* Blue 600 */
            color: #FFFFFF;
        }}
        
        /* Tables */
        QHeaderView::section {{
            background-color: #F8FAFC;
            padding: 8px 12px;
            border: none;
            border-bottom: 2px solid #E2E8F0;
            font-weight: bold;
            font-size: 12px;
            color: #475569;
        }}
        QTableView, QTableWidget {{
            background-color: #FFFFFF;
            color: #0F172A;
            border: 1px solid #E2E8F0;
            border-radius: 8px;
            selection-background-color: #E0E7FF; /* Indigo 100 - soft modern highlight */
            selection-color: #1E3A8A; /* Deep indigo text */
            gridline-color: #F1F5F9;
            alternate-background-color: #F8FAFC;
        }}
        QTableView::item, QTableWidget::item {{
            padding: 6px 10px;
            color: #0F172A;
        }}
        QTableView::item:selected, QTableWidget::item:selected {{
            background-color: #E0E7FF;
            color: #1E3A8A;
        }}
        
        /* Scrollbars (global) */
        QScrollBar:vertical, QScrollBar:horizontal {{
            background: {BACKGROUND};
            border-radius: 6px;
            width: 10px;
            height: 10px;
        }}
        QScrollBar::handle:vertical, QScrollBar::handle:horizontal {{
            background: {PRIMARY};
            min-width: 20px;
            min-height: 20px;
            border-radius: 6px;
        }}
        QScrollBar::handle:vertical:hover, QScrollBar::handle:horizontal:hover {{
            background: {PRIMARY_HOVER};
        }}
        QScrollBar::add-line, QScrollBar::sub-line {{
            background: none;
            height: 0;
            width: 0;
        }}
        QScrollBar::add-page, QScrollBar::sub-page {{
            background: none;
        }}

        /* Scroll Area Base */
        QScrollArea {{
            background-color: {BACKGROUND};
            border: none;
        }}

        /* Checkboxes */
        QCheckBox::indicator {{
            width: 16px;
            height: 16px;
            border: 1px solid #CBD5E1;
            border-radius: 4px;
            background: {SURFACE};
        }}
        QCheckBox::indicator:checked {{
            background-color: {PRIMARY};
            border: 1px solid {PRIMARY};
        }}
        QCheckBox::indicator:checked:hover {{
            background-color: {PRIMARY_HOVER};
        }}
        QCheckBox {{
            spacing: 6px;
        }}
        
        /* Message Boxes & Confirmation Dialogs */
        QMessageBox {{
            background-color: {SURFACE};
        }}
        QMessageBox QLabel {{
            color: {TEXT_PRIMARY};
            font-size: 13px;
            background-color: transparent;
            min-height: 36px;
        }}
        QMessageBox QPushButton {{
            background-color: {PRIMARY};
            color: #FFFFFF;
            border: 1px solid #475569;
            border-radius: 6px;
            padding: 8px 22px;
            min-width: 80px;
            min-height: 22px;
            font-weight: bold;
            font-size: 13px;
        }}
        QMessageBox QPushButton:hover {{
            background-color: {PRIMARY_HOVER};
        }}
        QMessageBox QPushButton:pressed {{
            background-color: {ACCENT};
        }}
        QDialogButtonBox QPushButton {{
            min-width: 80px;
            min-height: 22px;
            padding: 8px 20px;
            font-weight: bold;
            font-size: 13px;
            border-radius: 6px;
        }}
    """

    @staticmethod
    def tint(hex_color, amount=0.90):
        """Blend a hex colour toward white. amount=0 returns the colour as-is,
        amount=1 returns pure white. Used to derive soft card fills from accents."""
        hex_color = hex_color.lstrip("#")
        r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
        mix = lambda c: int(round(c + (255 - c) * amount))
        return f"#{mix(r):02X}{mix(g):02X}{mix(b):02X}"

    @staticmethod
    def get_palette():
        """Returns a high-contrast, clean light palette preventing OS Dark Mode bleed"""
        from PySide6.QtGui import QPalette, QColor
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(Theme.BACKGROUND))
        palette.setColor(QPalette.WindowText, QColor(Theme.TEXT_PRIMARY))
        palette.setColor(QPalette.Base, QColor(Theme.SURFACE))
        palette.setColor(QPalette.AlternateBase, QColor(Theme.BACKGROUND))
        palette.setColor(QPalette.Text, QColor(Theme.TEXT_PRIMARY))
        palette.setColor(QPalette.Button, QColor(Theme.SURFACE))
        palette.setColor(QPalette.ButtonText, QColor(Theme.TEXT_PRIMARY))
        palette.setColor(QPalette.Highlight, QColor("#E0E7FF"))
        palette.setColor(QPalette.HighlightedText, QColor("#1E3A8A"))
        palette.setColor(QPalette.PlaceholderText, QColor(Theme.TEXT_SECONDARY))
        return palette

