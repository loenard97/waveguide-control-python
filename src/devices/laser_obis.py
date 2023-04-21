"""
Coherent OBIS Laser with 594nm wavelength and 60mW Power
"""

import logging

from PyQt6.QtCore import QTimer, QEvent, pyqtSlot, QSettings, QSize, QPoint
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QVBoxLayout, QDoubleSpinBox, QPushButton, QHBoxLayout

from src.devices.main_device import USBDevice
from src.static_gui_elements.toggle_button import ToggleButton


class LaserOBIS(USBDevice):

    NAME = "OBIS Laser"
    TERMINATION_WRITE = "\r\n"
    TERMINATION_READ = 2

    def write(self, message: str = "", error_checking: bool = False) -> None:
        """
        Write Message to Device
        :param str message: Message to send
        :param bool error_checking: Check if Error occurred after writing
        :raises ConnectionError: Connection failed or Device Error occurred
        """
        super().write(message, error_checking=error_checking)
        self._ser.readline()

    def read(self, message: str = "", error_checking: bool = False) -> str:
        """
        Read Message from Device
        :param str message: Message to query
        :param bool error_checking: Check if Error occurred after reading
        :return: Received Answer
        :raises ConnectionError: Connection failed or Device Error occurred
        """
        # TODO: check if necessary
        if message:
            super().write(message, error_checking=error_checking)

        data = self._ser.readline().decode()[:-self.TERMINATION_READ]
        self._ser.readline()
        logging.info(f"{self.NAME}: Recv '{data}'")

        return data

    def get_error(self) -> str:
        """
        No Error handling
        """
        # TODO: implement
        # print(self.read("SYST:STAT?", error_checking=False))
        # print(self.read("SYST:FAUL?", error_checking=False))
        return ''

    def get_identification(self):
        """
        Get Identification String
        """
        return self.read("*IDN?")

    def get_output(self) -> bool:
        """
        Get Output
        """
        return "ON" in self.read("SOUR:AM:STAT?")

    def set_output(self, state: bool):
        """
        Set Output
        """
        self.write(f"SOUR:AM:STAT {'ON' if state else 'OFF'}")

    def get_diode_hours(self):
        """
        Get lifetime of diode in hours
        """
        return self.read("SYST:DIOD:HOUR?")

    def get_inf_power(self):
        return self.read("SYST:INF:POW?")

    def get_system_status(self):
        return self.read("SYST:STAT?")

    def get_power_level(self):
        return self.read("SOUR:POW:LEV?")

    def get_power_nominal(self):
        return self.read("SOUR:POW:NOM?")

    def set_power_level(self, power):
        if 0 < float(power) < 0.044:
            self.write(f"SOUR:POW:LEV:IMM:AMPL {power}")
        else:
            logging.error(f"{self.NAME}: Could not set Power Level to '{power}'. Value to high (max = 0.044).")

    def get_power_limit_low(self):
        return float(self.read("SOUR:POW:LIM:LOW?"))

    def get_power_limit_high(self):
        return float(self.read("SOUR:POW:LIM:HIGH?"))

    def get_current_level(self):
        return self.read("SOUR:POW:CURR?")

    def gui_open(self):
        self.app = OBISLaserWindow(self)


class OBISLaserWindow(QWidget):
    def __init__(self, device: LaserOBIS):
        super().__init__()
        # Variables
        self._device = device
        self.setWindowTitle(f"{self._device.NAME}")
        self.resize(QSettings().value(f"{self._device.NAME}_window/size", QSize(1400, 700)))
        self.move(QSettings().value(f"{self._device.NAME}_window/position", QPoint(300, 150)))

        # Layout Settings
        layout_settings = QFormLayout()
        layout_settings.addRow(QLabel("<b>Settings</b>"))
        self._label_current = QLabel()
        layout_settings.addRow(QLabel("Current / A"), self._label_current)
        self._dsb_power = QDoubleSpinBox()
        self._dsb_power.setDecimals(3)
        self._dsb_power.setMinimum(self._device.get_power_limit_low())
        self._dsb_power.setMaximum(self._device.get_power_limit_high())
        layout_settings.addRow(QLabel("Power / W"), self._dsb_power)

        # Layout Button
        layout_buttons = QHBoxLayout()
        self._button_apply = QPushButton("Apply")
        self._button_apply.clicked.connect(self._handle_button_apply)    # NOQA
        layout_buttons.addWidget(self._button_apply)
        self._button_output = ToggleButton(state=self._device.get_output())
        self._button_output.clicked.connect(lambda: self._device.set_output(state=self._button_output.isChecked()))    # NOQA
        layout_buttons.addWidget(self._button_output)

        # Total Layout
        layout = QVBoxLayout()
        layout.addLayout(layout_settings)
        layout.addLayout(layout_buttons)
        self.setLayout(layout)

        # Timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_labels)    # NOQA
        self._timer.start(2000)
        self._refresh_labels()

        self.show()

    def _refresh_labels(self):
        """
        Refresh Labels
        """
        self._label_current.setText(self._device.get_current_level())

    @pyqtSlot()
    def _handle_button_apply(self):
        """
        Write settings to device
        """
        self._device.set_power_level(self._dsb_power.value())

    @pyqtSlot()
    def closeEvent(self, event: QEvent):
        """
        Close Window Event
        """
        self._timer.stop()
        QSettings().setValue(f"{self._device.NAME}_window/size", self.size())
        QSettings().setValue(f"{self._device.NAME}_window/position", self.pos())
        event.accept()
