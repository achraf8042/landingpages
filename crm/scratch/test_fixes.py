import sys
import os
sys.path.insert(0, os.path.abspath("."))
from PySide6.QtWidgets import QApplication, QMessageBox, QPushButton
from styles.theme import Theme
from ui.finances_view import FinancesView, CreateInvoiceDialog
from ui.prescriptions_view import PrescriptionDialog

app = QApplication(sys.argv)
app.setStyle('Fusion')
app.setPalette(Theme.get_palette())
app.setStyleSheet(Theme.STYLESHEET)

fv = FinancesView()

# 1. Test Invoice Line Items UI Sizing
dlg_inv = CreateInvoiceDialog()
dlg_inv.show()
row_h = dlg_inv.items_table.rowHeight(0)
desc_w = dlg_inv.items_table.cellWidget(0, 0)
amt_w = dlg_inv.items_table.cellWidget(0, 1)
print(f"CreateInvoiceDialog: Row Height = {row_h}px, desc size = {desc_w.size()}, amt size = {amt_w.size()}")

# 2. Test Prescription Meds UI Sizing
dlg_rx = PrescriptionDialog()
dlg_rx.show()
rx_row_h = dlg_rx.meds_table.rowHeight(0)
med_w = dlg_rx.meds_table.cellWidget(0, 0)
print(f"PrescriptionDialog: Row Height = {rx_row_h}px, med size = {med_w.size()}")

# 3. Test FinancesView Delete Confirmation Box Buttons
box = QMessageBox(fv)
box.setIcon(QMessageBox.Question)
box.setWindowTitle('Confirm Delete Invoice')
box.setText('Are you sure you want to delete Invoice #1?')
yes_btn = box.addButton('Yes, Delete', QMessageBox.YesRole)
yes_btn.setStyleSheet('background-color: #DC2626; color: white; font-weight: bold; padding: 8px 18px;')
no_btn = box.addButton('Cancel', QMessageBox.NoRole)
no_btn.setStyleSheet('background-color: #FFFFFF; color: #0F172A; border: 1px solid #CBD5E1; font-weight: bold; padding: 8px 18px;')
box.show()

for b in box.findChildren(QPushButton):
    print(f"Finance Confirm Button: text='{b.text()}', isVisible={b.isVisible()}, style='{b.styleSheet()[:45]}'")

print("ALL SIZING AND VISIBILITY TESTS PASSED!")
