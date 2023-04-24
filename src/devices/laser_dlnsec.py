from PyQt6.QtWidgets import QVBoxLayout, QLabel, QFormLayout, QWidget, QComboBox

from src.devices.main_device import USBDevice
from src.static_gui_elements.toggle_button import ToggleButton
from src.static_gui_elements.delayed_spin_box import DelayedDoubleSpinBox


class LaserDLNSEC(USBDevice):
    NAME = "DLNSEC Laser"
    ICON = "laser"
    TERMINATION_WRITE = '\r'
    TERMINATION_READ = 1

    def __repr__(self):
        """
        Get current status
        """
        return f"{self.NAME} at {self.address}\n" \
               f"Power: {self.get_power()}"

    def get_identification(self):
        """
        Get Identification String
        """
        return self.read("*IDN")

    def reboot(self):
        """
        Reboot with Default Settings
        """
        self.write("*RBT")

    def reset(self):
        """
        Reset to Default Settings
        """
        self.write("*RST")

    def set_output(self, state=False):
        """
        Turn Output ON | OFF
        """
        if state:
            self.write("*ON")
        else:
            self.write("*OFF")

    def set_power(self, power):
        """
        Set Power in %
        """
        self.write(f"PWR {int(power)}")

    def get_power(self):
        """
        Get Power in %
        """
        return int(self.read("PWR?"))

    def set_mode(self, mode):
        """
        Set Mode LAS | EXT | INT
        """
        self.write(f"{mode}")

    def set_continuous_power(self, power, state):
        """
        Set Continuous Power
        """
        self.write("LAS")
        self.set_power(power)
        self.set_output(state)

    def set_external_power(self, power):
        """
        Set External Power
        """
        self.write("EXT")
        self.set_power(power)

    def set_internal_power(self, power, prescaler, width):
        """
        Set Internal Power
        """
        self.write("INT")
        self.set_power(power)
        self.write(f"PRE {prescaler}")
        self.write(f"WID {width}")

    def gui_open(self):
        self.app = DLNSECLaserWindow(self)


class DLNSECLaserWindow(QWidget):
    def __init__(self, device: LaserDLNSEC):
        super().__init__()
        # Variables
        self._device = device
        self.setWindowTitle(f"{self._device.NAME}")
        self.setGeometry(900, 500, 0, 0)

        # Layout Settings
        layout_settings = QFormLayout()
        layout_settings.addRow(QLabel("<b>Settings</b>"))
        combo_box_mode = QComboBox()
        combo_box_mode.addItems(["LAS", "EXT", "INT"])
        combo_box_mode.currentTextChanged.connect(
            lambda: self._device.set_mode(combo_box_mode.currentText())
        )
        layout_settings.addRow(QLabel("Mode"), combo_box_mode)
        line_edit_power = DelayedDoubleSpinBox()
        line_edit_power.setDecimals(0)
        line_edit_power.setRange(0, 100)
        line_edit_power.textChanged.connect(
            lambda: self._device.set_power(line_edit_power.text())
        )
        layout_settings.addRow(QLabel("Power / %"), line_edit_power)

        # Layout Button
        self._button_output = ToggleButton(state=False)
        self._button_output.clicked.connect(
            lambda: self._device.set_output(state=self._button_output.isChecked())
        )

        # Total Layout
        layout = QVBoxLayout()
        layout.addLayout(layout_settings)
        layout.addWidget(self._button_output)
        self.setLayout(layout)

        self.show()
