import sys
sys.path.insert(0, '.')
from PySide6.QtWidgets import QApplication
from styles.theme import Theme
from ui.notes_view import NoteDialog
from data import db_manager

app = QApplication([])
app.setStyle('Fusion')
app.setPalette(Theme.get_palette())
app.setStyleSheet(Theme.STYLESHEET)

conn = db_manager.get_db_connection()
c = conn.cursor()
c.execute("SELECT id, status FROM ClinicalNote WHERE status = 'FINALIZED' LIMIT 1")
row = c.fetchone()
conn.close()

if row:
    note_id = row['id']
    print(f"Testing with finalized note id: {note_id}")
    dlg = NoteDialog(note_id=note_id)
    print("is_finalized:", dlg.is_finalized)
    print("subjective isReadOnly:", dlg.subjective.isReadOnly())
    print("objective isReadOnly:", dlg.objective.isReadOnly())
    print("assessment isReadOnly:", dlg.assessment.isReadOnly())
    print("plan isReadOnly:", dlg.plan.isReadOnly())
    print("patient_combo isEnabled:", dlg.patient_combo.isEnabled())
    print("date_edit isEnabled:", dlg.date_edit.isEnabled())
    print("template_combo isEnabled:", dlg.template_combo.isEnabled())
    print("save_btn isEnabled:", dlg.save_btn.isEnabled())
    print("locked_banner isVisible:", dlg.locked_banner.isVisible())

    assert dlg.is_finalized == True
    assert dlg.subjective.isReadOnly() == True
    assert dlg.assessment.isReadOnly() == True
    assert dlg.patient_combo.isEnabled() == False
    assert dlg.save_btn.isEnabled() == False
    assert dlg.locked_banner.isVisible() == True
    print("All assertions passed for finalized note!")

# New draft note
dlg_new = NoteDialog()
print("\nTesting new draft note dialog:")
print("is_finalized:", dlg_new.is_finalized)
print("subjective isReadOnly:", dlg_new.subjective.isReadOnly())
print("assessment isReadOnly:", dlg_new.assessment.isReadOnly())
print("patient_combo isEnabled:", dlg_new.patient_combo.isEnabled())
print("save_btn isEnabled:", dlg_new.save_btn.isEnabled())
assert dlg_new.is_finalized == False
assert dlg_new.subjective.isReadOnly() == False
assert dlg_new.save_btn.isEnabled() == True
print("All assertions passed for draft note dialog!")
