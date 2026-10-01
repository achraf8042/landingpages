from utils.localization import combo_value, tr
from utils import currency
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                               QTableView, QHeaderView, QDialog, QFormLayout, 
                               QComboBox, QDateEdit, QLineEdit, QTextEdit, QMessageBox, 
                               QAbstractItemView, QStyle, QFileDialog, QLabel, QTableWidget,
                               QTableWidgetItem, QFrame, QTabWidget, QDoubleSpinBox, QScrollArea, QGridLayout,
                               QSizePolicy)
from PySide6.QtCore import Qt, QDate, QRectF, QSize
from PySide6.QtGui import QStandardItemModel, QStandardItem, QPainter, QColor, QFont, QPen, QBrush
from styles.theme import Theme
from data import db_manager
from utils.invoice_pdf_generator import InvoicePDFGenerator
from ui.scrollable_table import ScrollableTableView
from datetime import datetime
import csv

FINANCE_TABLE_STYLESHEET = """
    QTableView, QTableWidget {
        background-color: #FFFFFF;
        color: #0F172A;
        gridline-color: #F1F5F9;
        selection-background-color: #E0E7FF;
        selection-color: #1E3A8A;
        alternate-background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        outline: none;
    }
    QTableView::item, QTableWidget::item {
        color: #0F172A;
        padding: 8px 12px;
        border-bottom: 1px solid #F1F5F9;
    }
    QTableView::item:selected, QTableWidget::item:selected {
        background-color: #E0E7FF;
        color: #1E3A8A;
    }
    QHeaderView::section {
        background-color: #F8FAFC;
        color: #475569;
        font-weight: bold;
        font-size: 12px;
        border: none;
        border-bottom: 2px solid #E2E8F0;
        padding: 10px 12px;
    }
"""

class FinancialBarChartWidget(QWidget):
    """Custom Qt-native Bar Chart for Everyday Revenue & Expenses (zero heavy dependencies)"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data = [] # List of dicts: {'date': '2026-09-01', 'day_label': 'Sep 01', 'revenue': 120, 'expenses': 40}
        self.symbol = currency.DEFAULT_SYMBOL
        self.position = "before"
        self.setMinimumHeight(240)

    def set_currency(self, symbol, position):
        self.symbol = symbol or currency.DEFAULT_SYMBOL
        self.position = position or "before"
        self.update()

    def set_data(self, data):
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        margin_left = 65
        margin_right = 20
        margin_top = 35
        margin_bottom = 40

        chart_w = w - margin_left - margin_right
        chart_h = h - margin_top - margin_bottom

        # Card container background
        rect = self.rect()
        painter.setPen(QPen(QColor("#E2E8F0"), 1))
        painter.setBrush(QBrush(QColor("#FFFFFF")))
        painter.drawRoundedRect(rect.adjusted(1, 1, -2, -2), 8, 8)

        if not self.data:
            painter.setPen(QColor(Theme.TEXT_SECONDARY))
            painter.setFont(QFont("Segoe UI", 10))
            painter.drawText(rect, Qt.AlignCenter, "No financial transaction data for this period")
            return

        # Find max value for Y-axis
        max_val = 100.0
        for d in self.data:
            max_val = max(max_val, d['revenue'], d['expenses'])
        max_val = max_val * 1.15 # Add 15% headroom

        # Draw grid lines & Y labels
        painter.setPen(QPen(QColor("#F1F5F9"), 1, Qt.DashLine))
        font_small = QFont("Segoe UI", 9)
        painter.setFont(font_small)

        steps = 4
        for i in range(steps + 1):
            val = (max_val / steps) * i
            y = margin_top + chart_h - (i * (chart_h / steps))
            painter.drawLine(margin_left, int(y), margin_left + chart_w, int(y))

            painter.setPen(QColor("#64748B"))
            painter.drawText(QRectF(0, y - 8, margin_left - 8, 16), Qt.AlignRight | Qt.AlignVCenter,
                         currency.format_money(val, self.symbol, self.position, 0))
            painter.setPen(QPen(QColor("#F1F5F9"), 1, Qt.DashLine))

        # Draw Bars
        n_days = len(self.data)
        slot_w = chart_w / max(1, n_days)
        bar_w = max(5.0, (slot_w - 12) / 2)

        rev_color = QColor("#10B981") # Emerald Green
        exp_color = QColor("#F43F5E") # Rose Red

        for i, d in enumerate(self.data):
            slot_x = margin_left + (i * slot_w)
            
            # Revenue bar
            rev_h = (d['revenue'] / max_val) * chart_h
            rev_x = slot_x + 3
            rev_y = margin_top + chart_h - rev_h
            if rev_h > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(rev_color))
                painter.drawRoundedRect(QRectF(rev_x, rev_y, bar_w, rev_h), 2, 2)

            # Expense bar
            exp_h = (d['expenses'] / max_val) * chart_h
            exp_x = rev_x + bar_w + 3
            exp_y = margin_top + chart_h - exp_h
            if exp_h > 0:
                painter.setPen(Qt.NoPen)
                painter.setBrush(QBrush(exp_color))
                painter.drawRoundedRect(QRectF(exp_x, exp_y, bar_w, exp_h), 2, 2)

            # X-axis day label
            painter.setPen(QColor("#475569"))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(QRectF(slot_x - 5, margin_top + chart_h + 8, slot_w + 10, 20), Qt.AlignCenter, d['day_label'])

        # Legend (Top Right)
        legend_x = margin_left + chart_w - 180
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(rev_color))
        painter.drawRoundedRect(QRectF(legend_x, 10, 12, 12), 3, 3)
        painter.setPen(QColor("#1E293B"))
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.drawText(QRectF(legend_x + 16, 8, 65, 16), Qt.AlignLeft | Qt.AlignVCenter, tr("Revenue"))

        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(exp_color))
        painter.drawRoundedRect(QRectF(legend_x + 90, 10, 12, 12), 3, 3)
        painter.setPen(QColor("#1E293B"))
        painter.drawText(QRectF(legend_x + 106, 8, 65, 16), Qt.AlignLeft | Qt.AlignVCenter, tr("Expenses"))


class FinancesView(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.refresh_all()

    def setup_ui(self):
        self.setObjectName("financesView")
        self.setStyleSheet(f"QWidget#financesView {{ background-color: {Theme.BACKGROUND}; }}")

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Scroll Area for responsive fitting on all display resolutions
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: none;
                background-color: {Theme.BACKGROUND};
            }}
            QScrollBar:vertical {{
                border: none;
                background: #F1F5F9;
                width: 8px;
                margin: 0px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: #CBD5E1;
                min-height: 24px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: #94A3B8;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
        """)
        scroll.viewport().setStyleSheet(f"background-color: {Theme.BACKGROUND};")

        content = QWidget()
        content.setStyleSheet(f"background-color: {Theme.BACKGROUND};")
        content.setAutoFillBackground(True)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 10, 0)
        content_layout.setSpacing(16)

        # 1. KPI Top Bar (Grid layout for responsive sizing)
        kpi_layout = QGridLayout()
        kpi_layout.setSpacing(12)

        self.kpi_today_rev = self.create_kpi_card("Today's Revenue", "0.00", "💵", "#059669")
        self.kpi_month_rev = self.create_kpi_card("Month's Revenue", "0.00", "📈", "#2563EB")
        self.kpi_month_exp = self.create_kpi_card("Month's Expenses", "0.00", "🧾", "#E11D48")
        self.kpi_net_profit = self.create_kpi_card("Net Profit (Month)", "0.00", "💰", "#0D9488")
        self.kpi_pending = self.create_kpi_card("Pending Balance", "0.00", "⏳", "#D97706")
        self.kpi_insurance = self.create_kpi_card("Insurance Pending", "0.00", "🛡", "#7C3AED")

        # 3 x 2 grid: six cards in one row would demand ~1700px and stretch the
        # whole view wider than the window.
        kpi_layout.addWidget(self.kpi_today_rev, 0, 0)
        kpi_layout.addWidget(self.kpi_month_rev, 0, 1)
        kpi_layout.addWidget(self.kpi_month_exp, 0, 2)
        kpi_layout.addWidget(self.kpi_net_profit, 1, 0)
        kpi_layout.addWidget(self.kpi_pending, 1, 1)
        kpi_layout.addWidget(self.kpi_insurance, 1, 2)
        content_layout.addLayout(kpi_layout)

        # Shown only when invoices exist in a currency other than the clinic's.
        self.currency_warning = QLabel("")
        self.currency_warning.setWordWrap(True)
        self.currency_warning.setVisible(False)
        self.currency_warning.setStyleSheet(f"""
            QLabel {{
                background-color: #FEF3C7;
                color: #92400E;
                border: 1px solid #FCD34D;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        content_layout.addWidget(self.currency_warning)

        # 2. Main Tabs
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #E2E8F0;
                background-color: #FFFFFF;
                border-radius: 8px;
                top: -1px;
            }}
            QTabBar::tab {{
                background: #F1F5F9;
                color: {Theme.TEXT_SECONDARY};
                padding: 10px 20px;
                font-weight: 600;
                font-size: 13px;
                border: 1px solid #E2E8F0;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin-right: 4px;
            }}
            QTabBar::tab:selected {{
                background: #FFFFFF;
                color: {Theme.PRIMARY};
                border-bottom: 2px solid {Theme.PRIMARY};
                font-weight: bold;
            }}
            QTabBar::tab:hover:!selected {{
                background: #E2E8F0;
                color: {Theme.TEXT_PRIMARY};
            }}
        """)

        # Tab 1: Invoicing & Billing
        self.invoices_tab = QWidget()
        self.invoices_tab.setStyleSheet("background-color: #FFFFFF; border-radius: 8px;")
        self.setup_invoices_tab()
        self.tabs.addTab(self.invoices_tab, "💳 Invoices & Billing")

        # Tab 2: Clinic Expenses
        self.expenses_tab = QWidget()
        self.expenses_tab.setStyleSheet("background-color: #FFFFFF; border-radius: 8px;")
        self.setup_expenses_tab()
        self.tabs.addTab(self.expenses_tab, "📉 Clinic Expenses")

        # Tab 3: Daily Analytics & Charts
        self.analytics_tab = QWidget()
        self.analytics_tab.setStyleSheet("background-color: #FFFFFF; border-radius: 8px;")
        self.setup_analytics_tab()
        self.tabs.addTab(self.analytics_tab, "📊 Revenue & Expense Trends")

        content_layout.addWidget(self.tabs)
        scroll.setWidget(content)
        main_layout.addWidget(scroll)

    def create_kpi_card(self, title, value, icon, color_hex):
        card = QFrame()
        card.setObjectName("kpiCard")
        card.setStyleSheet(f"""
            QFrame#kpiCard {{
                background-color: #FFFFFF;
                border-radius: 8px;
                border: 1px solid #E2E8F0;
                border-top: 4px solid {color_hex};
            }}
        """)
        layout = QHBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(10)

        icon_lbl = QLabel(icon)
        icon_lbl.setStyleSheet(f"""
            font-size: 20px;
            background-color: {color_hex}15;
            border-radius: 6px;
            padding: 4px 6px;
        """)
        layout.addWidget(icon_lbl)

        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        title_lbl = QLabel(title)
        title_lbl.setWordWrap(True)
        title_lbl.setMinimumWidth(0)
        title_lbl.setStyleSheet("font-size: 11px; color: #64748B; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; background: transparent;")
        info_layout.addWidget(title_lbl)

        val_lbl = QLabel(value)
        val_lbl.setObjectName("val")
        val_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {color_hex}; background: transparent;")
        info_layout.addWidget(val_lbl)

        layout.addLayout(info_layout, 1)
        # A small explicit minimum keeps a long amount from stretching the grid;
        # the value elides instead of forcing the window wider.
        card.setMinimumWidth(150)
        return card

    # -------------------------
    # TAB 1: Invoices
    # -------------------------
    def setup_invoices_tab(self):
        layout = QVBoxLayout(self.invoices_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        # Toolbar
        toolbar = QHBoxLayout()
        self.bill_search = QLineEdit()
        self.bill_search.setPlaceholderText("Search invoices by patient or notes...")
        self.bill_search.setMinimumWidth(40)
        self.bill_search.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 10px;")
        self.bill_search.textChanged.connect(self.load_bills)

        self.bill_status_filter = QComboBox()
        self.bill_status_filter.addItems(["ALL", "UNPAID", "PAID", "PARTIAL"])
        self.bill_status_filter.setFixedWidth(86)
        self.bill_status_filter.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px;")
        self.bill_status_filter.currentTextChanged.connect(self.load_bills)

        btn_style = "padding: 6px 10px; font-size: 12px; font-weight: bold; border-radius: 6px;"

        new_bill_btn = QPushButton("+ Invoice")
        new_bill_btn.setStyleSheet(f"background-color: {Theme.PRIMARY}; color: white; {btn_style}")
        new_bill_btn.clicked.connect(self.open_create_invoice_dialog)

        mark_paid_btn = QPushButton("Mark Paid")
        mark_paid_btn.setProperty("class", "secondary")
        mark_paid_btn.setStyleSheet(f"border: 1px solid #CBD5E1; background-color: #FFFFFF; color: #0F172A; {btn_style}")
        mark_paid_btn.clicked.connect(self.mark_selected_paid)

        pdf_btn = QPushButton("Receipt")
        pdf_btn.setProperty("class", "secondary")
        pdf_btn.setStyleSheet(f"border: 1px solid #CBD5E1; background-color: #FFFFFF; color: #0F172A; {btn_style}")
        pdf_btn.clicked.connect(self.export_selected_invoice_pdf)

        claim_btn = QPushButton(tr("Claim"))
        claim_btn.setToolTip(tr("Set the insurer's coverage rate and claim status for this invoice"))
        claim_btn.setProperty("class", "secondary")
        claim_btn.setStyleSheet(
            f"border: 1px solid #BFDBFE; background-color: #EFF6FF; color: #1E3A8A; {btn_style}")
        claim_btn.clicked.connect(self.open_claim_dialog)

        del_btn = QPushButton("Delete")
        del_btn.setProperty("class", "danger")
        del_btn.setStyleSheet(f"background-color: {Theme.ERROR}; color: white; {btn_style}")
        del_btn.clicked.connect(self.delete_selected_bill)

        toolbar.addWidget(self.bill_search)
        toolbar.addWidget(QLabel("Status:"))
        toolbar.addWidget(self.bill_status_filter)
        toolbar.addStretch()
        toolbar.addWidget(pdf_btn)
        toolbar.addWidget(mark_paid_btn)
        toolbar.addWidget(claim_btn)
        toolbar.addWidget(del_btn)
        toolbar.addWidget(new_bill_btn)
        layout.addLayout(toolbar)

        # Invoices Table
        self.bills_table = ScrollableTableView()
        self.bills_table.setStyleSheet(FINANCE_TABLE_STYLESHEET)
        self.bills_table.viewport().setStyleSheet("background-color: #FFFFFF; color: #0F172A;")
        self.bills_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.bills_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.bills_table.verticalHeader().setVisible(False)
        self.bills_table.setAlternatingRowColors(True)
        self.bills_table.setShowGrid(True)

        self.bills_model = QStandardItemModel()
        self.bills_model.setHorizontalHeaderLabels([
            "ID", "Date", "Patient Name", "Total", "Insurance",
            "Insurer Pays", "Claim", "Patient Owes", "Status", "Notes",
        ])
        self.bills_table.setModel(self.bills_model)
        bills_header = self.bills_table.horizontalHeader()
        # Fixed widths rather than Stretch: with this many columns in ~850px,
        # Stretch squeezed names and amounts down to a few characters. Each width
        # includes the 20px horizontal cell padding. The table scrolls sideways
        # (see ScrollableTableView) instead of crushing the content.
        widths = {0: 78,    # ID
                  1: 108,   # Date
                  2: 155,   # Patient Name
                  3: 100,   # Total (carries the currency when it differs)
                  4: 205,   # Insurance
                  5: 105,   # Insurer Pays
                  6: 132,   # Claim
                  7: 110,   # Patient Owes
                  8: 88,    # Status
                  9: 160}   # Notes
        for col, width in widths.items():
            bills_header.setSectionResizeMode(col, QHeaderView.Interactive)
            self.bills_table.setColumnWidth(col, width)
        layout.addWidget(self.bills_table)

    def load_bills(self):
        search_text = self.bill_search.text().strip()
        status = combo_value(self.bill_status_filter)
        bills = db_manager.get_bills(status=status, search_text=search_text)

        self.bills_model.removeRows(0, self.bills_model.rowCount())
        bold_font = QFont("Segoe UI", 9)
        bold_font.setBold(True)

        for b in bills:
            status_str = (b['status'] or 'UNPAID').upper()
            status_item = QStandardItem(f" {tr(status_str)} ")
            status_item.setTextAlignment(Qt.AlignCenter)
            status_item.setFont(bold_font)

            if status_str == 'PAID':
                status_item.setForeground(QColor("#15803D")) # Rich green
                status_item.setBackground(QColor("#DCFCE7")) # Soft green pill
            elif status_str == 'PARTIAL':
                status_item.setForeground(QColor("#B45309")) # Amber
                status_item.setBackground(QColor("#FEF3C7")) # Soft amber pill
            else:
                status_item.setForeground(QColor("#B91C1C")) # Rose red
                status_item.setBackground(QColor("#FEE2E2")) # Soft red pill

            id_item = QStandardItem(f"#{b['id']:04d}")
            id_item.setForeground(QColor("#64748B"))
            id_item.setTextAlignment(Qt.AlignCenter)

            date_item = QStandardItem(b['created_at'][:10] if b['created_at'] else "")
            date_item.setForeground(QColor("#334155"))
            date_item.setTextAlignment(Qt.AlignCenter)

            name_item = QStandardItem(f"{b['first_name']} {b['last_name']}")
            name_item.setForeground(QColor("#0F172A"))
            name_item.setFont(bold_font)

            amt_item = QStandardItem(f"{float(b['total_amount']):.2f}")
            amt_item.setForeground(QColor("#0F172A"))
            amt_item.setFont(bold_font)
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            # Each invoice keeps the currency it was issued in. The code is shown
            # on the amount only when it differs from the clinic's currency,
            # which is exactly the case the reader needs to notice.
            bill_cur = (b['currency_code'] if 'currency_code' in b.keys() else '') or self.currency_code
            if bill_cur != self.currency_code:
                amt_item.setText(f"{float(b['total_amount']):.2f} {bill_cur}")
                amt_item.setForeground(QColor("#B45309"))
                amt_item.setToolTip(
                    f"{tr('This invoice is in')} {bill_cur}, "
                    f"{tr('not the clinic currency')} {self.currency_code}.")

            insurer = (b['insurance_provider'] if 'insurance_provider' in b.keys() else '') or ""
            member = (b['insurance_member_no'] if 'insurance_member_no' in b.keys() else '') or ""
            has_ins = bool(insurer or member)
            ins_text = (f"{insurer} · {member}" if insurer and member
                        else (insurer or member or tr("Self-pay")))
            bkeys = b.keys()
            pct = float(b['insurance_pct'] or 0.0) if 'insurance_pct' in bkeys else 0.0
            if has_ins:
                ins_text = f"{ins_text}  ({pct:g}%)"
            ins_item = QStandardItem(ins_text)
            ins_item.setToolTip(ins_text)
            if not has_ins:
                ins_item.setForeground(QColor("#94A3B8"))
            else:
                ins_item.setForeground(QColor("#1D4ED8"))

            ins_amt = float(b['insurance_amount'] or 0.0) if 'insurance_amount' in bkeys else 0.0
            pat_amt = float(b['patient_amount'] or 0.0) if 'patient_amount' in bkeys else 0.0
            if not pat_amt and not ins_amt:
                pat_amt = float(b['total_amount'])   # legacy row, fully self-pay
            claim = (b['insurance_claim_status'] if 'insurance_claim_status' in bkeys else None) \
                or currency.CLAIM_NOT_SUBMITTED

            ins_pay = QStandardItem(f"{ins_amt:.2f}" if has_ins else "—")
            ins_pay.setFont(bold_font)
            ins_pay.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            ins_pay.setForeground(QColor("#15803D" if ins_amt else "#94A3B8"))

            # No insurer means there is no claim to make.
            claim_text = tr(currency.claim_label(claim)) if has_ins else "—"
            claim_item = QStandardItem(f" {claim_text} ")
            claim_item.setTextAlignment(Qt.AlignCenter)
            claim_item.setFont(bold_font)
            if has_ins:
                claim_item.setForeground(QColor(currency.claim_color(claim)))
                claim_item.setBackground(QColor("#F1F5F9"))
            else:
                claim_item.setForeground(QColor("#CBD5E1"))

            pat_item = QStandardItem(f"{pat_amt:.2f}")
            pat_item.setFont(bold_font)
            pat_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            pat_item.setForeground(QColor("#B45309" if ins_amt else "#0F172A"))

            notes_item = QStandardItem(b['notes'] or "—")
            notes_item.setForeground(QColor("#64748B"))

            row = [id_item, date_item, name_item, amt_item, ins_item,
                   ins_pay, claim_item, pat_item, status_item, notes_item]
            row[0].setData(b['id'], Qt.UserRole)
            for item in row:
                item.setEditable(False)
            self.bills_model.appendRow(row)

    def get_selected_bill_id(self):
        selected = self.bills_table.selectionModel().selectedRows()
        if not selected:
            return None
        return self.bills_model.item(selected[0].row(), 0).data(Qt.UserRole)

    def mark_selected_paid(self):
        bill_id = self.get_selected_bill_id()
        if not bill_id:
            QMessageBox.warning(self, "Select Invoice", "Please select an invoice to mark as paid")
            return
        db_manager.update_bill_status(bill_id, 'PAID')
        self.refresh_all()

    def export_selected_invoice_pdf(self):
        bill_id = self.get_selected_bill_id()
        if not bill_id:
            QMessageBox.warning(self, "Select Invoice", "Please select an invoice to print")
            return
        filename, _ = QFileDialog.getSaveFileName(self, tr("Save Invoice Receipt"), f"Invoice_{bill_id:04d}.pdf", tr("PDF Files (*.pdf)"))
        if filename:
            try:
                InvoicePDFGenerator.generate(filename, bill_id)
                QMessageBox.information(self, "Success", "Invoice PDF saved successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate invoice PDF: {e}")

    def delete_selected_bill(self):
        bill_id = self.get_selected_bill_id()
        if not bill_id:
            QMessageBox.warning(self, "Select Invoice", "Please select an invoice to delete")
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Confirm Delete Invoice")
        box.setText(f"Are you sure you want to delete Invoice #{bill_id}?")
        box.setInformativeText("This will permanently remove the invoice and its line items.")
        yes_btn = box.addButton("Yes, Delete", QMessageBox.YesRole)
        yes_btn.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold; padding: 8px 18px; border-radius: 6px; min-width: 85px;")
        no_btn = box.addButton("Cancel", QMessageBox.NoRole)
        no_btn.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; font-weight: bold; padding: 8px 18px; border-radius: 6px; min-width: 85px;")
        box.setDefaultButton(no_btn)
        box.exec()

        if box.clickedButton() == yes_btn:
            db_manager.delete_bill(bill_id)
            self.refresh_all()

    def open_claim_dialog(self):
        """Edit an invoice's coverage split and move its claim along."""
        bill_id = self.get_selected_bill_id()
        if not bill_id:
            QMessageBox.warning(self, "Select Invoice",
                                tr("Please select an invoice to update its insurance claim"))
            return
        details = db_manager.get_bill_details(bill_id)
        if not details:
            QMessageBox.critical(self, "Error", tr("Could not load this invoice"))
            return
        dialog = InsuranceClaimDialog(self, details['bill'], self.currency_symbol)
        if dialog.exec():
            self.refresh_all()

    def open_create_invoice_dialog(self):
        dialog = CreateInvoiceDialog(self)
        if dialog.exec():
            self.refresh_all()

    # -------------------------
    # TAB 2: Expenses
    # -------------------------
    def setup_expenses_tab(self):
        layout = QVBoxLayout(self.expenses_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        toolbar = QHBoxLayout()
        self.exp_search = QLineEdit()
        self.exp_search.setPlaceholderText("Search expenses by description or notes...")
        self.exp_search.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 6px 10px;")
        self.exp_search.textChanged.connect(self.load_expenses)

        self.exp_cat_filter = QComboBox()
        self.exp_cat_filter.addItems(["ALL", "Rent", "Medical Supplies", "Utilities", "Software", "Equipment", "Salaries", "Other"])
        self.exp_cat_filter.setFixedWidth(140)
        self.exp_cat_filter.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; border-radius: 6px; padding: 5px;")
        self.exp_cat_filter.currentTextChanged.connect(self.load_expenses)

        btn_style = "padding: 6px 14px; font-size: 12px; font-weight: bold; border-radius: 6px;"

        new_exp_btn = QPushButton("+ Expense")
        new_exp_btn.setStyleSheet(f"background-color: {Theme.ERROR}; color: white; {btn_style}")
        new_exp_btn.clicked.connect(self.open_add_expense_dialog)

        del_exp_btn = QPushButton("Delete")
        del_exp_btn.setProperty("class", "secondary")
        del_exp_btn.setStyleSheet(f"border: 1px solid #CBD5E1; background-color: #FFFFFF; color: #0F172A; {btn_style}")
        del_exp_btn.clicked.connect(self.delete_selected_expense)

        toolbar.addWidget(self.exp_search)
        toolbar.addWidget(QLabel("Category:"))
        toolbar.addWidget(self.exp_cat_filter)
        toolbar.addStretch()
        toolbar.addWidget(del_exp_btn)
        toolbar.addWidget(new_exp_btn)
        layout.addLayout(toolbar)

        # Expenses Table
        self.exp_table = ScrollableTableView()
        self.exp_table.setStyleSheet(FINANCE_TABLE_STYLESHEET)
        self.exp_table.viewport().setStyleSheet("background-color: #FFFFFF; color: #0F172A;")
        self.exp_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.exp_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.exp_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.exp_table.verticalHeader().setVisible(False)
        self.exp_table.setAlternatingRowColors(True)
        self.exp_table.setShowGrid(True)

        self.exp_model = QStandardItemModel()
        self.exp_model.setHorizontalHeaderLabels(["ID", "Date", "Category", "Description", "Amount", "Method", "Notes"])
        self.exp_table.setModel(self.exp_model)
        layout.addWidget(self.exp_table)

    def load_expenses(self):
        search_text = self.exp_search.text().strip()
        cat = combo_value(self.exp_cat_filter)
        expenses = db_manager.get_expenses(category=cat, search_text=search_text)

        self.exp_model.removeRows(0, self.exp_model.rowCount())
        bold_font = QFont("Segoe UI", 9)
        bold_font.setBold(True)

        for e in expenses:
            id_item = QStandardItem(f"#{e['id']}")
            id_item.setForeground(QColor("#64748B"))
            id_item.setTextAlignment(Qt.AlignCenter)

            date_item = QStandardItem(e['expense_date'])
            date_item.setForeground(QColor("#334155"))
            date_item.setTextAlignment(Qt.AlignCenter)

            cat_item = QStandardItem(f" {tr(e['category'])} ")
            cat_item.setForeground(QColor("#334155"))
            cat_item.setBackground(QColor("#F1F5F9"))
            cat_item.setTextAlignment(Qt.AlignCenter)
            cat_item.setFont(bold_font)

            desc_item = QStandardItem(e['description'])
            desc_item.setForeground(QColor("#0F172A"))
            desc_item.setFont(bold_font)

            amt_item = QStandardItem(f"-{float(e['amount']):.2f}")
            amt_item.setForeground(QColor("#DC2626")) # Rose red for expense
            amt_item.setFont(bold_font)
            amt_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)

            method_item = QStandardItem(tr(e['payment_method'] or "Cash"))
            method_item.setForeground(QColor("#475569"))
            method_item.setTextAlignment(Qt.AlignCenter)

            notes_item = QStandardItem(e['notes'] or "—")
            notes_item.setForeground(QColor("#64748B"))

            row = [id_item, date_item, cat_item, desc_item, amt_item, method_item, notes_item]
            row[0].setData(e['id'], Qt.UserRole)
            for item in row:
                item.setEditable(False)
            self.exp_model.appendRow(row)

    def get_selected_expense_id(self):
        selected = self.exp_table.selectionModel().selectedRows()
        if not selected:
            return None
        return self.exp_model.item(selected[0].row(), 0).data(Qt.UserRole)

    def delete_selected_expense(self):
        exp_id = self.get_selected_expense_id()
        if not exp_id:
            QMessageBox.warning(self, "Select Expense", "Please select an expense to delete")
            return

        box = QMessageBox(self)
        box.setIcon(QMessageBox.Question)
        box.setWindowTitle("Confirm Delete Expense")
        box.setText(f"Are you sure you want to delete Expense #{exp_id}?")
        box.setInformativeText("This will permanently remove the expense entry from practice records.")
        yes_btn = box.addButton("Yes, Delete", QMessageBox.YesRole)
        yes_btn.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold; padding: 8px 18px; border-radius: 6px; min-width: 85px;")
        no_btn = box.addButton("Cancel", QMessageBox.NoRole)
        no_btn.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; font-weight: bold; padding: 8px 18px; border-radius: 6px; min-width: 85px;")
        box.setDefaultButton(no_btn)
        box.exec()

        if box.clickedButton() == yes_btn:
            db_manager.delete_expense(exp_id)
            self.refresh_all()

    def open_add_expense_dialog(self):
        dialog = AddExpenseDialog(self)
        if dialog.exec():
            self.refresh_all()

    # -------------------------
    # TAB 3: Analytics & Chart
    # -------------------------
    def setup_analytics_tab(self):
        layout = QVBoxLayout(self.analytics_tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        chart_title = QLabel("Daily Practice Cash Flow (Last 14 Days)")
        # Without wrapping this label demands its full 600px+ text width and
        # stretches the whole view past the window.
        chart_title.setWordWrap(True)
        chart_title.setMinimumWidth(0)
        chart_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        chart_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {Theme.PRIMARY};")

        export_csv_btn = QPushButton("Export Accountant CSV")
        export_csv_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.ACCENT};
                color: white;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }}
        """)
        export_csv_btn.clicked.connect(self.export_financial_csv)

        header_layout.addWidget(chart_title)
        header_layout.addStretch()
        header_layout.addWidget(export_csv_btn)
        layout.addLayout(header_layout)

        # Bar Chart Widget
        self.chart_widget = FinancialBarChartWidget()
        layout.addWidget(self.chart_widget)

        # Breakdown Table
        breakdown_title = QLabel("Daily Financial Breakdown:")
        breakdown_title.setStyleSheet("font-weight: bold; font-size: 13px; margin-top: 10px; color: #0F172A;")
        layout.addWidget(breakdown_title)

        self.stats_table = QTableWidget(0, 4)
        self.stats_table.setStyleSheet(FINANCE_TABLE_STYLESHEET)
        self.stats_table.viewport().setStyleSheet("background-color: #FFFFFF; color: #0F172A;")
        self.stats_table.setHorizontalHeaderLabels(["Date", "Collected Revenue", "Clinic Expenses", "Net Daily Profit"])
        self.stats_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.stats_table.verticalHeader().setVisible(False)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setShowGrid(True)
        self.stats_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.stats_table)

    def load_analytics(self):
        stats = db_manager.get_daily_financial_stats(days=14, currency=self.currency_code)
        self.chart_widget.set_currency(self.currency_symbol, self.currency_position)
        self.chart_widget.set_data(stats)
        # Name the currency in the headers so the bare numbers are unambiguous.
        self.stats_table.setHorizontalHeaderLabels([
            tr("Date"),
            f"{tr('Collected Revenue')} ({self.currency_code})",
            f"{tr('Clinic Expenses')} ({self.currency_code})",
            f"{tr('Net Daily Profit')} ({self.currency_code})",
        ])

        bold_font = QFont("Segoe UI", 9)
        bold_font.setBold(True)

        # Populate breakdown table
        self.stats_table.setRowCount(len(stats))
        for r, s in enumerate(reversed(stats)):
            net = s['revenue'] - s['expenses']

            date_item = QTableWidgetItem(s['date'])
            date_item.setForeground(QColor("#334155"))
            date_item.setTextAlignment(Qt.AlignCenter)
            self.stats_table.setItem(r, 0, date_item)

            rev_item = QTableWidgetItem(f"{s['revenue']:.2f}")
            rev_item.setForeground(QColor("#15803D")) # Emerald
            rev_item.setFont(bold_font)
            rev_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.stats_table.setItem(r, 1, rev_item)

            exp_item = QTableWidgetItem(f"{s['expenses']:.2f}")
            exp_item.setForeground(QColor("#DC2626")) # Rose red
            exp_item.setFont(bold_font)
            exp_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.stats_table.setItem(r, 2, exp_item)

            if net >= 0:
                net_item = QTableWidgetItem(f"+{net:.2f}")
                net_item.setForeground(QColor("#15803D"))
                net_item.setBackground(QColor("#DCFCE7"))
            else:
                net_item = QTableWidgetItem(f"-{abs(net):.2f}")
                net_item.setForeground(QColor("#B91C1C"))
                net_item.setBackground(QColor("#FEE2E2"))
            net_item.setFont(bold_font)
            net_item.setTextAlignment(Qt.AlignCenter)
            self.stats_table.setItem(r, 3, net_item)

    def export_financial_csv(self):
        filename, _ = QFileDialog.getSaveFileName(self, tr("Export Financial Report"), f"Financial_Report_{datetime.now().strftime('%Y%m%d')}.csv", tr("CSV Files (*.csv)"))
        if filename:
            try:
                bills = db_manager.get_bills()
                expenses = db_manager.get_expenses()

                with open(filename, mode='w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow([f"=== INVOICES & REVENUE ({self.currency_code}) ==="])
                    writer.writerow(["ID", "Date", "Patient Name", "Total Amount", "Subtotal", "Tax",
                                     "Currency", "Insurance Provider", "Insurance Member No.",
                                     "Status", "Notes"])
                    for b in bills:
                        writer.writerow([
                            b['id'], b['created_at'], f"{b['first_name']} {b['last_name']}",
                            b['total_amount'], b['subtotal_amount'], b['tax_amount'],
                            b['currency_code'] if 'currency_code' in b.keys() else self.currency_code,
                            b['insurance_provider'] if 'insurance_provider' in b.keys() else '',
                            b['insurance_member_no'] if 'insurance_member_no' in b.keys() else '',
                            b['status'], b['notes'],
                        ])

                    writer.writerow([])
                    writer.writerow([f"=== CLINIC EXPENSES ({self.currency_code}) ==="])
                    writer.writerow(["ID", "Date", "Category", "Description", "Amount", "Payment Method", "Notes"])
                    for e in expenses:
                        writer.writerow([e['id'], e['expense_date'], e['category'], e['description'], e['amount'], e['payment_method'], e['notes']])

                QMessageBox.information(self, "Success", "Financial data exported to CSV successfully!")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export CSV: {e}")

    def refresh_all(self):
        # Resolve the clinic currency once; all figures below use it.
        self.currency_code, self.currency_symbol, self.currency_position = db_manager.get_clinic_currency()
        self.money = lambda amount: currency.format_money(
            amount, self.currency_symbol, self.currency_position)
        self.chart_widget.set_currency(self.currency_symbol, self.currency_position)

        kpis = db_manager.get_financial_kpis(self.currency_code)
        self.kpi_today_rev.findChild(QLabel, "val").setText(self.money(kpis['today_revenue']))
        self.kpi_month_rev.findChild(QLabel, "val").setText(self.money(kpis['month_revenue']))
        self.kpi_month_exp.findChild(QLabel, "val").setText(self.money(kpis['month_expenses']))
        
        net_val = kpis['net_profit']
        net_lbl = self.kpi_net_profit.findChild(QLabel, "val")
        net_lbl.setText(self.money(net_val))
        net_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {'#059669' if net_val >= 0 else '#DC2626'};")

        self.kpi_pending.findChild(QLabel, "val").setText(
            f"{self.money(kpis['pending_amount'])} ({kpis['pending_count']})")

        ins_pending = kpis.get('insurance_pending_amount', 0.0)
        ins_count = kpis.get('insurance_pending_count', 0)
        ins_lbl = self.kpi_insurance.findChild(QLabel, "val")
        ins_lbl.setText(f"{self.money(ins_pending)} ({ins_count})")
        ins_lbl.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {'#7C3AED' if ins_pending else '#94A3B8'};")

        # Warn instead of silently mixing currencies in the totals above.
        foreign = kpis.get('foreign_currency_count', 0)
        if hasattr(self, "currency_warning") and foreign:
            self.currency_warning.setText(
                tr("Showing ") + self.currency_code + tr(" only. ")
                + tr("{} invoice(s) are in another currency and are excluded from these totals.").format(foreign))
            self.currency_warning.setVisible(True)
        elif hasattr(self, "currency_warning"):
            self.currency_warning.setVisible(False)

        # Load tabs
        self.load_bills()
        self.load_expenses()
        self.load_analytics()


class InsuranceClaimDialog(QDialog):
    """Correct an invoice's coverage rate and track what the insurer has paid."""

    def __init__(self, parent=None, bill=None, symbol="$"):
        super().__init__(parent)
        self.bill = bill
        self.symbol = symbol or "$"
        self.setWindowTitle(f"{tr('Insurance & Claim')} — #{bill['id']:04d}")
        self.resize(520, 460)
        self.setMinimumWidth(480)
        self.setStyleSheet(Theme.STYLESHEET)
        self.setup_ui()
        self.load_bill()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 22, 22, 22)
        layout.setSpacing(14)

        title = QLabel(tr("Insurance & Claim"))
        title.setStyleSheet(f"font-size: 19px; font-weight: bold; color: {Theme.PRIMARY};")
        layout.addWidget(title)

        self.patient_label = QLabel("")
        self.patient_label.setWordWrap(True)
        self.patient_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.patient_label.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 12px;")
        layout.addWidget(self.patient_label)

        form = QFormLayout()
        form.setSpacing(12)
        input_style = ("background-color: #FFFFFF; color: #0F172A; border: 1.5px solid #CBD5E1;"
                       " border-radius: 6px; padding: 6px 12px; font-size: 13px; min-height: 25px;")

        self.pct_spin = QDoubleSpinBox()
        self.pct_spin.setRange(0.0, 100.0)
        self.pct_spin.setDecimals(0)
        self.pct_spin.setSuffix(" %")
        self.pct_spin.setStyleSheet(input_style)
        self.pct_spin.valueChanged.connect(self._update_preview)
        form.addRow(tr("Insurer covers:"), self.pct_spin)

        self.claim_combo = QComboBox()
        for status in currency.CLAIM_STATUSES:
            self.claim_combo.addItem(tr(currency.claim_label(status)), status)
        self.claim_combo.setStyleSheet(input_style)
        form.addRow(tr("Claim status:"), self.claim_combo)

        layout.addLayout(form)

        # Live split preview. Scoped by object name: a bare stylesheet on a frame
        # also applies to its child labels, boxing each one individually.
        self.split_card = QFrame()
        self.split_card.setObjectName("splitCard")
        self.split_card.setStyleSheet("""
            QFrame#splitCard {
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 8px;
            }
            QFrame#splitCard QLabel {
                background: transparent;
                border: none;
            }
        """)
        split_layout = QVBoxLayout(self.split_card)
        split_layout.setContentsMargins(14, 10, 14, 10)
        split_layout.setSpacing(6)

        self.total_row = QLabel("")
        self.total_row.setStyleSheet("color: #334155; font-size: 13px; font-weight: 600;")
        self.insurer_row = QLabel("")
        self.insurer_row.setStyleSheet("color: #15803D; font-size: 13px; font-weight: 700;")
        self.patient_row = QLabel("")
        self.patient_row.setStyleSheet("color: #B45309; font-size: 13px; font-weight: 700;")
        split_layout.addWidget(self.total_row)
        split_layout.addWidget(self.insurer_row)
        split_layout.addWidget(self.patient_row)
        layout.addWidget(self.split_card)

        note = QLabel(tr("Revenue is counted in full when the invoice is marked paid. This split shows what the patient still owes and what the insurer still owes you."))
        note.setWordWrap(True)
        note.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(note)

        layout.addStretch()

        btn_layout = QHBoxLayout()
        cancel_btn = QPushButton(tr("Cancel"))
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setStyleSheet(
            f"border: 1px solid #CBD5E1; background-color: #FFFFFF; color: #0F172A;"
            f" padding: 9px 20px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        cancel_btn.clicked.connect(self.reject)
        save_btn = QPushButton(tr("Save"))
        save_btn.setStyleSheet(
            f"background-color: {Theme.PRIMARY}; color: white; padding: 9px 22px;"
            f" border-radius: 6px; font-weight: bold; font-size: 13px;")
        save_btn.clicked.connect(self.save)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def _money(self, amount):
        return currency.format_money(amount, self.symbol)

    def load_bill(self):
        b = self.bill
        keys = b.keys()
        self.total_amount = float(b['total_amount'])
        self.patient_label.setText(
            f"<b>{b['first_name']} {b['last_name']}</b><br/>"
            f"{tr('Insurer')}: {(b['insurance_provider'] if 'insurance_provider' in keys else '') or tr('None')}"
            f"   ·   {tr('Member No.')}: "
            f"{(b['insurance_member_no'] if 'insurance_member_no' in keys else '') or '—'}"
        )
        pct = float(b['insurance_pct'] or 0.0) if 'insurance_pct' in keys else 0.0
        self.pct_spin.setValue(pct)
        claim = (b['insurance_claim_status'] if 'insurance_claim_status' in keys else None) \
            or currency.CLAIM_NOT_SUBMITTED
        idx = self.claim_combo.findData(claim)
        if idx >= 0:
            self.claim_combo.setCurrentIndex(idx)
        self._update_preview()

    def _update_preview(self):
        insurer, patient = currency.split_coverage(self.total_amount, self.pct_spin.value())
        self.total_row.setText(f"{tr('Invoice total')}: {self._money(self.total_amount)}")
        self.insurer_row.setText(
            f"{tr('Insurer pays')} ({self.pct_spin.value():g}%): {self._money(insurer)}")
        self.patient_row.setText(f"{tr('Patient pays')}: {self._money(patient)}")

    def save(self):
        success, message = db_manager.update_bill_insurance(
            self.bill['id'],
            self.pct_spin.value(),
            self.claim_combo.currentData() or currency.CLAIM_NOT_SUBMITTED,
        )
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"{tr('Failed to save insurance details')}: {message}")


class CreateInvoiceDialog(QDialog):
    """Dialog for creating itemized patient invoices"""
    def __init__(self, parent=None, patient_id=None):
        super().__init__(parent)
        self.patient_id = patient_id
        self.setWindowTitle("Create New Invoice")
        self.resize(780, 700)
        self.setMinimumWidth(720)
        self.setMinimumHeight(520)
        self.setSizeGripEnabled(True)
        self.setStyleSheet(Theme.STYLESHEET)
        self.currency_code, self.currency_symbol, self.currency_position = db_manager.get_clinic_currency()
        self.setup_ui()

    def setup_ui(self):
        # The form grew past the usable window height once insurance was added,
        # so the body scrolls and the button bar stays pinned and reachable.
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                border: none; background: #F1F5F9; width: 8px;
                margin: 0px; border-radius: 4px;
            }
            QScrollBar::handle:vertical { background: #CBD5E1; min-height: 24px; border-radius: 4px; }
            QScrollBar::handle:vertical:hover { background: #94A3B8; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: none; }
        """)
        outer.addWidget(scroll, 1)

        content = QWidget()
        content.setObjectName("invoiceScrollContent")
        layout = QVBoxLayout(content)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("Patient Invoice & Billing")
        title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {Theme.PRIMARY};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        input_style = "background-color: #FFFFFF; color: #0F172A; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; font-size: 13px; min-height: 25px;"

        self.patient_combo = QComboBox()
        self.patient_combo.setStyleSheet(input_style)
        self.load_patients()
        self.patient_combo.currentIndexChanged.connect(self.update_insurance_preview)
        form.addRow("Patient *:", self.patient_combo)

        self.due_date = QDateEdit(QDate.currentDate())
        self.due_date.setCalendarPopup(True)
        self.due_date.setDisplayFormat("yyyy-MM-dd")
        self.due_date.setStyleSheet(input_style)
        form.addRow("Due Date:", self.due_date)

        self.status_combo = QComboBox()
        self.status_combo.addItems(["UNPAID", "PAID", "PARTIAL"])
        self.status_combo.setStyleSheet(input_style)
        form.addRow("Payment Status *:", self.status_combo)

        cur_row = QHBoxLayout()
        cur_code = QLabel(f"{self.currency_code}  ({self.currency_symbol})")
        cur_code.setStyleSheet(f"font-weight: 600; color: {Theme.TEXT_PRIMARY}; background: transparent;")
        cur_note = QLabel(tr("from Settings > Clinic Information"))
        cur_note.setStyleSheet(f"color: {Theme.TEXT_SECONDARY}; font-size: 11px; background: transparent;")
        cur_row.addWidget(cur_code)
        cur_row.addWidget(cur_note)
        cur_row.addStretch()
        form.addRow(tr("Currency:"), cur_row)
        layout.addLayout(form)

        # --- Insurance: coverage rate + live split (snapshot onto the invoice)
        self._pct_untouched = True
        self.insurance_box = QFrame()
        self.insurance_box.setObjectName("insuranceBox")
        self.insurance_box.setStyleSheet(f"""
            QFrame#insuranceBox {{
                background-color: #EFF6FF;
                border: 1px solid #BFDBFE;
                border-radius: 8px;
            }}
            QFrame#insuranceBox QLabel {{
                background: transparent;
            }}
        """)
        ins_layout = QVBoxLayout(self.insurance_box)
        ins_layout.setContentsMargins(12, 8, 12, 8)
        ins_layout.setSpacing(4)

        self.insurance_label = QLabel("")
        self.insurance_label.setWordWrap(True)
        self.insurance_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.insurance_label.setStyleSheet("color: #1E3A8A; font-size: 12px; font-weight: 600;")
        ins_layout.addWidget(self.insurance_label)

        pct_row = QHBoxLayout()
        pct_row.setSpacing(8)
        pct_caption = QLabel(tr("Insurer covers:"))
        pct_caption.setStyleSheet("color: #1E3A8A; font-size: 12px; font-weight: 600;")
        self.insurance_pct = QDoubleSpinBox()
        self.insurance_pct.setRange(0.0, 100.0)
        self.insurance_pct.setDecimals(0)
        self.insurance_pct.setSuffix(" %")
        self.insurance_pct.setMaximumWidth(100)
        self.insurance_pct.setStyleSheet(
            "background-color: #FFFFFF; color: #1E3A8A; border: 1px solid #BFDBFE;"
            " border-radius: 6px; padding: 4px 8px; font-size: 12px; font-weight: 700;")
        self.insurance_pct.setEnabled(False)
        self.insurance_pct.valueChanged.connect(
            lambda _v: setattr(self, "_pct_untouched", False))
        self.insurance_pct.valueChanged.connect(self.calculate_totals)
        pct_row.addWidget(pct_caption)
        pct_row.addWidget(self.insurance_pct)
        pct_row.addStretch()
        ins_layout.addLayout(pct_row)

        # Live "who pays what" summary.
        self.payer_box = QFrame()
        self.payer_box.setObjectName("payerBox")
        self.payer_box.setStyleSheet("""
            QFrame#payerBox {
                background-color: #FFFFFF;
                border: 1px solid #DBEAFE;
                border-radius: 6px;
            }
            QFrame#payerBox QLabel {
                background: transparent;
                border: none;
            }
        """)
        payer_layout = QHBoxLayout(self.payer_box)
        payer_layout.setContentsMargins(10, 6, 10, 6)
        payer_layout.setSpacing(10)
        ins_caption = QLabel("")
        ins_caption.setStyleSheet("color: #334155; font-size: 12px; font-weight: 700;")
        self.split_caption = ins_caption
        self.insurer_lbl = QLabel("0.00")
        self.insurer_lbl.setStyleSheet("color: #15803D; font-size: 12px; font-weight: 700;")
        self.patient_lbl = QLabel("0.00")
        self.patient_lbl.setStyleSheet("color: #B45309; font-size: 12px; font-weight: 700;")
        payer_layout.addWidget(ins_caption)
        payer_layout.addWidget(QLabel(f"{tr('Insurer pays')}"))
        payer_layout.addWidget(self.insurer_lbl)
        payer_layout.addStretch()
        payer_layout.addWidget(QLabel(f"{tr('Patient pays')}"))
        payer_layout.addWidget(self.patient_lbl)
        ins_layout.addWidget(self.payer_box)
        self.payer_box.setVisible(False)
        layout.addWidget(self.insurance_box)

        # Line Items Header
        items_header = QHBoxLayout()
        items_title = QLabel("Invoice Line Items:")
        items_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #0F172A;")
        add_item_btn = QPushButton("+ Add Line Item")
        add_item_btn.setCursor(Qt.PointingHandCursor)
        add_item_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {Theme.PRIMARY};
                color: white;
                border-radius: 6px;
                padding: 8px 18px;
                font-size: 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {Theme.PRIMARY_HOVER};
            }}
        """)
        add_item_btn.clicked.connect(lambda: self.add_item_row())

        items_header.addWidget(items_title)
        items_header.addStretch()
        items_header.addWidget(add_item_btn)
        layout.addLayout(items_header)

        # Items Table Widget
        self.items_table = QTableWidget(0, 3)
        self.items_table.setObjectName("invoiceItemsTable")
        self.items_table.setStyleSheet("""
            QTableWidget#invoiceItemsTable {
                background-color: #FFFFFF;
                color: #0F172A;
                gridline-color: #F1F5F9;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
            }
            QTableWidget#invoiceItemsTable::item {
                padding: 0px;
                border: none;
                border-bottom: 1px solid #F1F5F9;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #475569;
                font-weight: bold;
                font-size: 12px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                padding: 10px 12px;
            }
        """)
        self.items_table.viewport().setStyleSheet("background-color: #FFFFFF; color: #0F172A;")
        self.items_table.setHorizontalHeaderLabels([
            "Service / Procedure Description *",
            f"Amount ({self.currency_code}) *",
            "Action",
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.items_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Fixed)
        self.items_table.setColumnWidth(1, 170)
        self.items_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        self.items_table.setColumnWidth(2, 95)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.verticalHeader().setDefaultSectionSize(52)
        self.items_table.setShowGrid(True)
        self.items_table.setMinimumHeight(220)
        layout.addWidget(self.items_table)

        # Totals calculation card
        totals_card = QFrame()
        totals_card.setObjectName("totalsCard")
        totals_card.setStyleSheet("""
            QFrame#totalsCard {
                background-color: #F8FAFC;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
            }
            QFrame#totalsCard QLabel {
                background: transparent;
                border: none;
            }
        """)
        totals_layout = QHBoxLayout(totals_card)
        totals_layout.setContentsMargins(14, 8, 14, 8)

        tax_label = QLabel("Tax Rate:")
        tax_label.setStyleSheet("font-weight: 600; color: #475569; font-size: 13px;")
        totals_layout.addWidget(tax_label)

        self.tax_spin = QDoubleSpinBox()
        self.tax_spin.setRange(0, 50)
        self.tax_spin.setSuffix("%")
        # Default to the clinic's configured rate; the doctor can override per invoice.
        clinic = db_manager.get_clinic_info()
        if clinic and clinic['tax_rate'] is not None:
            self.tax_spin.setValue(float(clinic['tax_rate']))
        self.tax_spin.setMinimumHeight(34)
        self.tax_spin.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 4px 8px; font-size: 13px; font-weight: bold;")
        self.tax_spin.valueChanged.connect(self.calculate_totals)
        totals_layout.addWidget(self.tax_spin)

        totals_layout.addStretch()

        self.total_lbl = QLabel("Total: 0.00")
        self.total_lbl.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.PRIMARY};")
        totals_layout.addWidget(self.total_lbl)
        layout.addWidget(totals_card)

        # Pre-seed consultation fee item
        self.add_item_row(tr("Doctor Consultation"), "50.00")

        # Notes
        notes_lbl = QLabel("Notes / Instructions:")
        notes_lbl.setStyleSheet("font-weight: bold; color: #0F172A; font-size: 13px;")
        layout.addWidget(notes_lbl)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Payment terms, insurance notes, or check numbers...")
        self.notes_edit.setStyleSheet("background-color: #FFFFFF; color: #0F172A; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 8px; font-size: 13px;")
        self.notes_edit.setMaximumHeight(65)
        layout.addWidget(self.notes_edit)

        layout.addStretch()
        scroll.setWidget(content)

        # Buttons live outside the scroll area so they are always visible.
        btn_layout = QHBoxLayout()
        btn_layout.setContentsMargins(20, 12, 20, 16)
        save_btn = QPushButton("Save & Issue Invoice")
        save_btn.setStyleSheet(f"background-color: {Theme.PRIMARY}; color: white; font-weight: bold; padding: 10px 22px; border-radius: 6px; font-size: 13px;")
        save_btn.clicked.connect(self.save_invoice)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setStyleSheet("border: 1px solid #CBD5E1; background-color: #FFFFFF; color: #0F172A; padding: 10px 20px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        outer.addLayout(btn_layout)

        self.update_insurance_preview()
        self.calculate_totals()

    def add_item_row(self, desc="", amt="0.00"):
        if not isinstance(desc, str):
            desc = ""
        if isinstance(amt, bool) or not isinstance(amt, (int, float, str)):
            amt = "0.00"

        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        desc_edit = QLineEdit(desc)
        desc_edit.setPlaceholderText("e.g. Doctor Consultation, Blood Work, Ultrasound...")
        desc_edit.setStyleSheet("""
            QLineEdit {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 13px;
                font-weight: 500;
                margin: 3px 6px;
            }
            QLineEdit:focus {
                border: 2px solid #5B73A7;
            }
        """)
        desc_edit.setMinimumHeight(38)
        self.items_table.setCellWidget(row, 0, desc_edit)

        amt_spin = QDoubleSpinBox()
        amt_spin.setRange(0.00, 99999.99)
        amt_spin.setValue(float(amt) if amt else 0.0)
        amt_spin.setPrefix(self.currency_symbol)
        amt_spin.setDecimals(2)
        amt_spin.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        amt_spin.setStyleSheet("""
            QDoubleSpinBox {
                background-color: #FFFFFF;
                color: #0F172A;
                border: 1.5px solid #CBD5E1;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 14px;
                font-weight: bold;
                margin: 3px 6px;
            }
            QDoubleSpinBox:focus {
                border: 2px solid #5B73A7;
            }
        """)
        amt_spin.setMinimumHeight(38)
        amt_spin.valueChanged.connect(self.calculate_totals)
        self.items_table.setCellWidget(row, 1, amt_spin)

        del_btn = QPushButton("✕ Remove")
        del_btn.setToolTip("Remove this line item")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.setStyleSheet("""
            QPushButton {
                background-color: #FEE2E2;
                color: #DC2626;
                border: 1px solid #FCA5A5;
                border-radius: 6px;
                font-weight: bold;
                font-size: 11px;
                padding: 4px;
                margin: 3px 6px;
            }
            QPushButton:hover {
                background-color: #DC2626;
                color: #FFFFFF;
            }
        """)
        del_btn.setMinimumHeight(36)
        del_btn.clicked.connect(lambda _, r=row: self.remove_item_row(r))
        self.items_table.setCellWidget(row, 2, del_btn)

        self.items_table.setRowHeight(row, 52)
        self.calculate_totals()

    def remove_item_row(self, row):
        if self.items_table.rowCount() > 1:
            self.items_table.removeRow(row)
            for r in range(self.items_table.rowCount()):
                btn = self.items_table.cellWidget(r, 2)
                if btn:
                    btn.clicked.disconnect()
                    btn.clicked.connect(lambda _, curr_r=r: self.remove_item_row(curr_r))
            self.calculate_totals()

    def update_insurance_preview(self):
        """Show the selected patient's insurer and pre-fill their coverage rate."""
        patient_id = self.patient_combo.currentData()
        info = db_manager.get_patient_insurance(patient_id) if patient_id else None
        if info:
            if self._pct_untouched:
                self.insurance_pct.setValue(float(info.get('coverage_pct', 0.0)))
            self.insurance_label.setText(
                f"{tr('Insurance')}: {info['provider']}"
                + (f"   ·   {tr('Member No.')}: {info['member_no']}" if info['member_no'] else "")
            )
        else:
            self.insurance_label.setText(tr("Self-pay - this patient has no insurance on file."))
            self.insurance_pct.setValue(0.0)
        self.insurance_pct.setEnabled(bool(info))
        self.insurance_pct.setToolTip(
            tr("Share of this invoice the insurer pays.")
            if info else tr("This patient has no insurer on file, so there is nothing to split."))
        self.insurance_box.setVisible(True)
        self.calculate_totals()

    def _split_now(self):
        """(insurance_amount, patient_amount) for the current line items."""
        subtotal = 0.0
        for r in range(self.items_table.rowCount()):
            amt_widget = self.items_table.cellWidget(r, 1)
            if amt_widget:
                subtotal += amt_widget.value()
        total = subtotal + subtotal * (self.tax_spin.value() / 100.0)
        return currency.split_coverage(total, self.insurance_pct.value())

    def calculate_totals(self):
        if not hasattr(self, 'tax_spin') or not hasattr(self, 'total_lbl'):
            return
        subtotal = 0.0
        for r in range(self.items_table.rowCount()):
            amt_widget = self.items_table.cellWidget(r, 1)
            if amt_widget:
                subtotal += amt_widget.value()

        tax_rate = self.tax_spin.value()
        tax_amount = subtotal * (tax_rate / 100.0)
        total = subtotal + tax_amount
        self.total_lbl.setText(f"{tr('Total')}: {currency.format_money(total, self.currency_symbol, self.currency_position)}")

        if not hasattr(self, "insurer_lbl"):
            return
        insurer, patient = currency.split_coverage(total, self.insurance_pct.value())
        if self.insurance_pct.value() > 0 and insurer > 0:
            self.payer_box.setVisible(True)
            self.split_caption.setText(
                f"{tr('Total')}: {currency.format_money(total, self.currency_symbol, self.currency_position)}")
            self.insurer_lbl.setText(currency.format_money(insurer, self.currency_symbol, self.currency_position))
            self.patient_lbl.setText(currency.format_money(patient, self.currency_symbol, self.currency_position))
        else:
            self.payer_box.setVisible(False)

    def load_patients(self):
        try:
            conn = db_manager.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id, first_name, last_name FROM Patient ORDER BY last_name, first_name")
            patients = cursor.fetchall()
            conn.close()

            selected_idx = 0
            for idx, p in enumerate(patients):
                self.patient_combo.addItem(f"{p['first_name']} {p['last_name']}", p['id'])
                if self.patient_id and p['id'] == self.patient_id:
                    selected_idx = idx

            if self.patient_combo.count() > 0:
                self.patient_combo.setCurrentIndex(selected_idx)
        except Exception as e:
            print(f"Error loading patients: {e}")

    def save_invoice(self):
        patient_id = self.patient_combo.currentData()
        if not patient_id:
            QMessageBox.warning(self, "Error", "Please select a patient")
            return

        items = []
        subtotal = 0.0
        for r in range(self.items_table.rowCount()):
            desc_widget = self.items_table.cellWidget(r, 0)
            amt_widget = self.items_table.cellWidget(r, 1)

            desc = desc_widget.text().strip() if desc_widget else ""
            amt = amt_widget.value() if amt_widget else 0.0
            if desc and amt > 0:
                items.append({'description': desc, 'amount': amt})
                subtotal += amt

        if not items:
            QMessageBox.warning(self, "Error", "Please add at least one line item with an amount")
            return

        tax_rate = self.tax_spin.value()
        tax_amount = subtotal * (tax_rate / 100.0)
        total = subtotal + tax_amount

        due_date_str = self.due_date.date().toString("yyyy-MM-dd")
        status = combo_value(self.status_combo)
        notes = self.notes_edit.toPlainText().strip()

        # The insurer, member number and coverage split are snapshotted from the
        # patient's chart so the printed receipt stays accurate even if the
        # patient later changes insurance. The rate is overridable per invoice.
        success, res = db_manager.create_bill(
            patient_id=patient_id,
            items=items,
            total_amount=total,
            subtotal_amount=subtotal,
            tax_amount=tax_amount,
            status=status,
            due_date=due_date_str,
            notes=notes,
            currency_code=self.currency_code,
            insurance_pct=self.insurance_pct.value() if self.insurance_pct.isEnabled() else 0.0,
        )

        if success:
            QMessageBox.information(self, "Success", f"Invoice #{res} created successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save invoice: {res}")


class AddExpenseDialog(QDialog):
    """Dialog for logging a new clinic expense"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Log Clinic Expense")
        self.resize(480, 420)
        self.setMinimumWidth(440)
        self.setStyleSheet(Theme.STYLESHEET)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        title = QLabel("New Expense Entry")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {Theme.ERROR};")
        layout.addWidget(title)

        form = QFormLayout()
        form.setSpacing(10)
        input_style = "background-color: #FFFFFF; color: #0F172A; border: 1.5px solid #CBD5E1; border-radius: 6px; padding: 6px 12px; font-size: 13px; min-height: 25px;"

        self.cat_combo = QComboBox()
        self.cat_combo.addItems(["Medical Supplies", "Rent", "Utilities", "Software", "Equipment", "Salaries", "Other"])
        self.cat_combo.setStyleSheet(input_style)
        form.addRow("Category *:", self.cat_combo)

        self.desc_edit = QLineEdit()
        self.desc_edit.setPlaceholderText("e.g. Syringes, Gloves, Internet Bill")
        self.desc_edit.setStyleSheet(input_style)
        form.addRow("Description *:", self.desc_edit)

        self.amt_spin = QDoubleSpinBox()
        self.amt_spin.setRange(0.01, 100000.0)
        self.amt_spin.setValue(25.0)
        clinic_symbol = db_manager.get_clinic_currency()[1]
        self.amt_spin.setPrefix(clinic_symbol)
        self.amt_spin.setStyleSheet(input_style)
        form.addRow("Amount *:", self.amt_spin)

        self.date_edit = QDateEdit(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.setStyleSheet(input_style)
        form.addRow("Date *:", self.date_edit)

        self.method_combo = QComboBox()
        self.method_combo.addItems(["Cash", "Credit Card", "Bank Transfer", "Check", "Other"])
        self.method_combo.setStyleSheet(input_style)
        form.addRow("Payment Method:", self.method_combo)

        self.notes_edit = QLineEdit()
        self.notes_edit.setPlaceholderText("Optional receipt/vendor notes...")
        self.notes_edit.setStyleSheet(input_style)
        form.addRow("Notes:", self.notes_edit)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save Expense")
        save_btn.setStyleSheet(f"background-color: {Theme.ERROR}; color: white; font-weight: bold; padding: 10px 22px; border-radius: 6px; font-size: 13px;")
        save_btn.clicked.connect(self.save_expense)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "secondary")
        cancel_btn.setStyleSheet("border: 1px solid #CBD5E1; background-color: #FFFFFF; color: #0F172A; padding: 10px 20px; border-radius: 6px; font-weight: bold; font-size: 13px;")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        layout.addLayout(btn_layout)

    def save_expense(self):
        desc = self.desc_edit.text().strip()
        if not desc:
            QMessageBox.warning(self, "Error", "Please enter a description")
            return

        cat = combo_value(self.cat_combo)
        amt = self.amt_spin.value()
        date_str = self.date_edit.date().toString("yyyy-MM-dd")
        method = combo_value(self.method_combo)
        notes = self.notes_edit.text().strip()

        success, res = db_manager.add_expense(
            category=cat,
            description=desc,
            amount=amt,
            expense_date=date_str,
            payment_method=method,
            notes=notes
        )

        if success:
            QMessageBox.information(self, "Success", "Expense logged successfully!")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Failed to save expense: {res}")
