"""English/French UI localization backed by python-i18n.

Only UI chrome is translated. Clinical values and database codes remain in their
original form so changing language cannot change a saved medical record.
"""
import json
import os
import weakref

import i18n
from PySide6.QtCore import QObject, QEvent, QSettings, Signal, Qt, QLocale, QTimer
from PySide6.QtWidgets import (
    QApplication, QAbstractButton, QComboBox, QGroupBox, QLabel, QLineEdit,
    QMessageBox, QPlainTextEdit, QTabWidget, QTableView, QTextEdit, QWidget,
    QAbstractSpinBox,
)


def _catalog_path():
    return os.path.join(os.path.dirname(__file__), "translations", "fr.json")


with open(_catalog_path(), encoding="utf-8") as file:
    FRENCH = json.load(file)

i18n.set("fallback", "en")
for english, french in FRENCH.items():
    i18n.add_translation(english, french, locale="fr")


def tr(source):
    """Translate a known English UI string without changing unknown user data."""
    if not isinstance(source, str) or i18n.get("locale") != "fr":
        return source
    translated = FRENCH.get(source)
    if translated is not None:
        return i18n.t(source)
    # Dynamic messages append a name, number or an exception to a fixed phrase.
    for prefix in _PREFIXES:
        if source.startswith(prefix):
            suffix = source[len(prefix):]
            if prefix in _COMPOSITE_PREFIXES:
                for english, french in _SEGMENTS:
                    suffix = suffix.replace(english, french)
            return i18n.t(prefix) + suffix
    return source


_PREFIXES = sorted(
    (key for key in FRENCH if len(key) >= 6 and key.endswith((" ", "$", "#", "\n"))),
    key=len, reverse=True,
)
_COMPOSITE_PREFIXES = {"Total Notes: ", "DOB: ", "<b>Address:</b> ", "<b>Date:</b> "}
_SEGMENTS = [(key, value) for key, value in FRENCH.items()
             if key.startswith((" | ", "  |  ", " &nbsp;", "<br/>"))]


class LanguageManager(QObject):
    changed = Signal(str)

    def __init__(self, app):
        super().__init__(app)
        self.app = app
        self._busy = False
        self._pending = False
        self._originals = weakref.WeakKeyDictionary()
        locale = QSettings("DigiSpher", "EMR").value("language", "en")
        i18n.set("locale", locale if locale in ("en", "fr") else "en")
        QLocale.setDefault(QLocale(QLocale.French if self.locale == "fr" else QLocale.English))
        app.installEventFilter(self)

    @property
    def locale(self):
        return i18n.get("locale")

    def set_locale(self, locale):
        if locale not in ("en", "fr") or locale == self.locale:
            return
        i18n.set("locale", locale)
        QLocale.setDefault(QLocale(QLocale.French if locale == "fr" else QLocale.English))
        QSettings("DigiSpher", "EMR").setValue("language", locale)
        self.refresh_all()
        self.changed.emit(locale)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Show, QEvent.Paint) and isinstance(obj, QWidget):
            self._translate_widget(obj)
            if event.type() == QEvent.Show:
                if not self._pending:
                    self._pending = True
                    QTimer.singleShot(0, self._scheduled_refresh)
        return False

    def _scheduled_refresh(self):
        self._pending = False
        self.refresh_all()

    def refresh_all(self):
        for window in self.app.topLevelWidgets():
            self._translate_widget(window)
            for child in window.findChildren(QWidget):
                self._translate_widget(child)

    def _set(self, widget, slot, value, setter):
        if not value:
            return
        state = self._originals.setdefault(widget, {})
        original, shown = state.get(slot, (value, None))
        if value != shown:
            original = value
        result = tr(original) if self.locale == "fr" else original
        state[slot] = (original, result)
        if result != value:
            setter(result)

    def _translate_widget(self, widget):
        if self._busy:
            return
        if widget.property("i18n_skip"):
            return
        if isinstance(widget, QLabel) and isinstance(widget.window(), QMessageBox):
            # QMessageBox owns these labels; translate its text properties instead.
            return
        self._busy = True
        try:
            if widget.isWindow():
                self._set(widget, "title", widget.windowTitle(), widget.setWindowTitle)
            if isinstance(widget, QMessageBox):
                self._set(widget, "message", widget.text(), widget.setText)
                self._set(widget, "informative", widget.informativeText(), widget.setInformativeText)
            if isinstance(widget, QAbstractButton) and isinstance(widget.window(), QMessageBox):
                box = widget.window()
                standard = box.standardButton(widget)
                standard_labels = {
                    QMessageBox.Yes: "&Yes", QMessageBox.No: "&No",
                    QMessageBox.Ok: "&OK", QMessageBox.Cancel: "&Cancel",
                }
                if standard in standard_labels:
                    source = standard_labels[standard]
                    desired = tr(source) if self.locale == "fr" else source
                    if widget.text() != desired:
                        widget.setText(desired)
                    return
            if isinstance(widget, (QLabel, QAbstractButton, QGroupBox)):
                self._set(widget, "text", widget.text() if not isinstance(widget, QGroupBox) else widget.title(),
                          widget.setText if not isinstance(widget, QGroupBox) else widget.setTitle)
            if isinstance(widget, (QLineEdit, QTextEdit, QPlainTextEdit)):
                self._set(widget, "placeholder", widget.placeholderText(), widget.setPlaceholderText)
            if isinstance(widget, QAbstractSpinBox):
                widget.setLocale(QLocale(QLocale.French if self.locale == "fr" else QLocale.English))
            if isinstance(widget, QComboBox):
                # Keep the itemData as the stable database value.
                for index in range(widget.count()):
                    if widget.itemData(index, Qt.UserRole + 1) is None:
                        widget.setItemData(index, widget.itemText(index), Qt.UserRole + 1)
                    self._set(widget, ("item", index), widget.itemText(index),
                              lambda text, i=index: widget.setItemText(i, text))
            if isinstance(widget, QTabWidget):
                for index in range(widget.count()):
                    self._set(widget, ("tab", index), widget.tabText(index),
                              lambda text, i=index: widget.setTabText(i, text))
            if isinstance(widget, QTableView) and widget.model():
                model = widget.model()
                for col in range(model.columnCount()):
                    value = model.headerData(col, Qt.Horizontal)
                    if isinstance(value, str):
                        self._set(widget, ("header", col), value,
                                  lambda text, i=col: model.setHeaderData(i, Qt.Horizontal, text))
        finally:
            self._busy = False


_manager = None


def install(app):
    global _manager
    _manager = LanguageManager(app)
    return _manager


def manager():
    return _manager


def combo_value(combo):
    """Get an option's original code while its visible label is localized."""
    return combo.currentData(Qt.UserRole + 1) or combo.currentText()


def find_combo_value(combo, value):
    for index in range(combo.count()):
        if combo.itemData(index, Qt.UserRole + 1) == value:
            return index
    return combo.findText(value)


def set_combo_value(combo, value):
    index = find_combo_value(combo, value)
    if index >= 0:
        combo.setCurrentIndex(index)
