"""
Children of QPushButton
"""

from PyQt6.QtWidgets import QPushButton


class ToggleButton(QPushButton):
    """
    QPushButton with boolean state that changes its Label and Color when clicked
    """

    def __init__(self, state=False, labels=None, colors=None):
        super().__init__()

        if labels is None:
            labels = ["ON", "OFF"]
        self.labels = labels
        if colors is None:
            colors = ["green", ""]
        self.colors = colors

        self.setCheckable(True)
        self.setChecked(state)
        self.clicked.connect(self._handle_clicked)
        self._handle_clicked()

    def _handle_clicked(self):
        """
        Change color when clicked
        """
        if self.isChecked():
            self.setText(self.labels[0])
            self.setStyleSheet(f"background-color : {self.colors[0]}")
        else:
            self.setText(self.labels[1])
            self.setStyleSheet(f"background-color : {self.colors[1]}")
