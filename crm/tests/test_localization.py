"""Smoke checks for live language switching and stable database codes."""
import os
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QComboBox, QLabel, QLineEdit, QMessageBox, QVBoxLayout, QWidget

from utils.localization import combo_value, find_combo_value, install, tr


class LocalizationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.language = install(cls.app)
        cls.previous = cls.language.locale

    @classmethod
    def tearDownClass(cls):
        cls.language.set_locale(cls.previous)

    def test_switch_updates_existing_and_new_widgets_without_changing_input(self):
        self.language.set_locale("en")
        window = QWidget()
        layout = QVBoxLayout(window)
        label = QLabel("Settings")
        clinical_input = QLineEdit("Patient's original words")
        layout.addWidget(label)
        layout.addWidget(clinical_input)
        window.show()
        self.app.processEvents()

        self.language.set_locale("fr")
        self.app.processEvents()
        self.assertEqual(label.text(), "Paramètres")
        self.assertEqual(clinical_input.text(), "Patient's original words")

        new_label = QLabel("Save Changes", window)
        layout.addWidget(new_label)
        self.app.processEvents()
        self.assertEqual(new_label.text(), "Enregistrer les modifications")

        self.language.set_locale("en")
        self.app.processEvents()
        self.assertEqual(label.text(), "Settings")
        self.assertEqual(new_label.text(), "Save Changes")
        window.close()

    def test_translated_combo_keeps_original_code(self):
        self.language.set_locale("fr")
        combo = QComboBox()
        combo.addItems(["SCHEDULED", "CONFIRMED", "CANCELLED"])
        combo.show()
        self.app.processEvents()

        self.assertEqual(combo.itemText(1), "CONFIRMÉ")
        self.assertEqual(find_combo_value(combo, "CONFIRMED"), 1)
        combo.setCurrentIndex(1)
        self.assertEqual(combo_value(combo), "CONFIRMED")
        self.assertEqual(tr("Failed to save patient: disk full"),
                         "Impossible d'enregistrer le patient : disk full")

        self.language.set_locale("en")
        self.app.processEvents()
        self.assertEqual(combo.itemText(1), "CONFIRMED")
        combo.close()

    def test_message_box_and_standard_buttons_reverse_cleanly(self):
        self.language.set_locale("fr")
        box = QMessageBox(QMessageBox.Question, "Confirm Delete",
                          "Are you sure you want to delete this appointment?",
                          QMessageBox.Yes | QMessageBox.No)
        box.show()
        self.app.processEvents()
        self.assertEqual(box.text(), "Voulez-vous vraiment supprimer ce rendez-vous ?")
        self.assertEqual([button.text() for button in box.buttons()], ["&Oui", "&Non"])

        self.language.set_locale("en")
        self.app.processEvents()
        self.assertEqual(box.text(), "Are you sure you want to delete this appointment?")
        self.assertEqual([button.text() for button in box.buttons()], ["&Yes", "&No"])
        box.close()


if __name__ == "__main__":
    unittest.main()
