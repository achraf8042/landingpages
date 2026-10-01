"""Shared table view that never stretches its parent."""
from PySide6.QtCore import QSize
from PySide6.QtWidgets import QTableView


class ScrollableTableView(QTableView):
    """A table that never forces its parent wider than the space it is given.

    QTableView's default minimumSizeHint is the sum of its column widths, so a
    wide table stretches the whole window past its intended size. Returning a
    small horizontal minimum lets the header scroll sideways instead, with every
    column keeping a readable width.
    """

    def minimumSizeHint(self):
        return QSize(140, super().minimumSizeHint().height())
