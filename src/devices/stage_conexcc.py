"""
Newport Conex-CC Stage
"""

import logging

from PyQt6.QtCore import QTimer, QEvent, pyqtSlot
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QLineEdit, QFormLayout, QHBoxLayout,  QVBoxLayout, QMessageBox

from src.devices.device_main import USBDevice
from src.static_functions.wait import wait_msec


class ConexCCStage(USBDevice):
    
    BAUDRATE = 921600
    TERMINATION_WRITE = '\r\n'
    TERMINATION_READ = 2

    STATUS_CODES = {
        "00": "NOT REFERENCED",
        "0A": "NOT REFERENCED from RESET",
        "0B": "NOT REFERENCED from HOMING",
        "0C": "NOT REFERENCED from CONFIGURATION",
        "0D": "NOT REFERENCED from DISABLE",
        "0E": "NOT REFERENCED from READY",
        "0F": "NOT REFERENCED from MOVING",
        "10": "NOT REFERENCED - NO PARAMETERS IN MEMORY",
        "14": "CONFIGURATION",
        "1E": "HOMING",
        "28": "MOVING",
        "32": "READY from HOMING",
        "33": "READY from MOVING",
        "34": "READY from DISABLE",
        "36": "READY T from READY",
        "37": "READY T from TRACKING",
        "38": "READY T from DISABLE T",
        "3C": "DISABLE from READY",
        "3D": "DISABLE from MOVING",
        "3E": "DISABLE from TRACKING",
        "3F": "DISABLE from READY T",
        "46": "TRACKING from READY T",
        "47": "TRACKING from TRACKING"
    }

    def __init__(self, name, address):
        """
        Connect, then check if stage needs to be homed
        """
        super().__init__(name, address)
        stage_state = self.get_state()
        logging.info(f"{self.name}: In State '{stage_state}'")

        # home if necessary
        if stage_state.startswith("NOT REFERENCED"):
            QMessageBox.warning(
                None, "Warning",
                f"The Stage '{self.name}' with address '{self.address}' needs to be homed to the zero position.\n"
                "Make sure that the travel path is clear before clicking OK.")
            self.home_to_zero()

    def reset(self):
        """
        Exit DISABLE state after error
        """
        state = self.get_state()
        if state.startswith("DISABLE"):
            self.write("1MM1")

    def wait_until_ready(self):
        """
        Block until Status Code is not MOVING or HOMING
        """
        while self.get_state() in ["MOVING", "HOMING"]:
            wait_msec(200)

    def get_position(self):
        """
        Get current Position
        """
        return self.read("1TP")[3:]

    def get_state(self):
        """
        Get current Status Code
        """
        state = self.read("1TS")
        if state == '':
            return ''
        return self.STATUS_CODES[state[-2:]]

    def move_absolute(self, position, blocking=True):
        """
        Move absolute distance
        """
        self.write(f"1PA{position}")
        if blocking:
            self.wait_until_ready()

    def move_relative(self, distance, blocking=True):
        """
        Move relative distance
        """
        self.write(f"1PR{distance}")
        if blocking:
            self.wait_until_ready()

    def home_to_zero(self, blocking=True):
        """
        Home to Zero after Reset
        """
        logging.info(f"{self.name}: Homing to Zero...")
        self.write("1OR")
        if blocking:
            self.wait_until_ready()

        logging.info(f"{self.name}: Homing complete. Current Position: '{self.get_position()}'")

    def gui_open(self):
        self.app = ConexCCStageWindow(self)


class ConexCCStageWindow(QWidget):
    def __init__(self, device: ConexCCStage):
        super().__init__()
        self.device = device

        self.setWindowTitle(f"{self.device.name}")
        self.setGeometry(735, 365, 450, 350)

        self.label_state = QLabel()
        self.label_position = QLabel()
        self.line_edit_position = QLineEdit()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_values)
        self.timer.start(2000)

        self.initialize_widgets()
        self.show()

    def initialize_widgets(self):
        layout_values = QFormLayout()
        widget_values = QWidget()
        layout_values.addRow(QLabel("<b>Values</b>"))
        layout_values.addRow(QLabel("Address"), QLabel(self.device.address))
        layout_values.addRow(QLabel("Status"), QLabel(self.device.status.name))
        layout_values.addRow(QLabel("State"), QLabel(self.device.get_state()))
        layout_values.addRow(QLabel("Position"), QLabel(self.device.get_position()))
        widget_values.setLayout(layout_values)

        widget_line_edit = QWidget()
        layout_line_edit = QFormLayout()
        layout_line_edit.addRow(QLabel("<b>Settings</b>"))
        layout_line_edit.addRow(QLabel("Position"), self.line_edit_position)
        widget_line_edit.setLayout(layout_line_edit)

        widget_buttons = QWidget()
        layout_buttons = QHBoxLayout()
        button_apply = QPushButton("Apply")

        def handle_button_apply():
            self.device.move_absolute(self.line_edit_position.text())

        button_apply.clicked.connect(handle_button_apply)
        layout_buttons.addWidget(button_apply)
        widget_buttons.setLayout(layout_buttons)

        layout = QVBoxLayout()
        layout.addWidget(widget_values)
        layout.addWidget(widget_line_edit)
        layout.addWidget(widget_buttons)
        self.setLayout(layout)

    def refresh_values(self):
        self.label_state.setText(self.device.get_state())
        self.label_position.setText(self.device.get_position())

    @pyqtSlot()
    def closeEvent(self, event: QEvent):
        """
        Close Window Event
        """
        self.timer.stop()
        event.accept()
