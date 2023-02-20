"""
Voltcraft Power Supply PPS11360
"""

import serial

from PyQt6.QtCore import QTimer, pyqtSlot
from PyQt6.QtWidgets import QWidget, QLabel, QDoubleSpinBox, QFormLayout, QHBoxLayout

from src.static_gui_elements.toggle_button import ToggleButton


class PPS11360:

    def __init__(self, name, address, settings):
        self.name = name
        self.address = address
        self.settings = settings
        self.app = None
        self._ser = None
        self.max_voltage, self.max_current = None, None
        try:
            self.connect()
        except RuntimeError:
            raise ConnectionError
        else:
            self.reset()

    def connect(self):
        """
        Connect to Device
        """
        self._ser = serial.Serial(
            port=self.address,
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            xonxoff=False,
            timeout=0.5
        )
        if not self._ser.is_open:
            raise ConnectionError

        self.max_voltage, self.max_current = self.get_max_voltage_and_current()

    def disconnect(self):
        """
        Disconnect from Device
        """
        self._ser.close()

    def reset(self):
        pass

    def _request(self, msg):
        if not isinstance(msg, bytes):
            assert isinstance(msg, str)
            msg = msg.encode("utf-8")

        self._ser.write(msg + b'\r')
        raw = self._ser.read_until(b'OK\r', 128)
        response = raw.strip().split(b'\r')
        if not response[-1] == b'OK':
            raise RuntimeError(f"Invalid response! {msg=} -> {raw=}. Probably the requested value is out of range.")

        return [b.decode('utf-8') for b in response[:-1]]

    @staticmethod
    def _voltage_from_response_string(s):
        if len(s) == 3:
            volt = int(s) / 10
        elif len(s) == 4:
            volt = int(s) / 100
        else:
            raise ValueError(f"Unsupported format of response string: {s}")
        return volt

    @staticmethod
    def _current_from_response_string(s):
        return int(s) / 100

    def _voltage_and_current_from_response_string(self, s):
        return self._voltage_from_response_string(s[:len(s) // 2]), self._current_from_response_string(s[len(s) // 2:])

    def get_max_voltage_and_current(self):
        """
        Get the maximal voltage and current the device is capable of generating
        :return: (voltage, current)
        """
        response = self._request("GMAX")[0]
        return self._voltage_and_current_from_response_string(response)

    def set_output(self, state=True):
        """
        Enable or disable the output
        :param state: True -> On, False -> off
        """
        self._request(f"SOUT{0 if state else 1}")

    def set_voltage(self, voltage):
        """
        Set the output voltage
        :param voltage: Voltage in Volts, Must be > 1 V
        """
        if voltage < 1 or voltage > self.max_voltage:
            raise ValueError(f"Voltage ({voltage} V) out of range! Must be within [1 V, {self.max_voltage} V]")
        self._request(f"VOLT{int(voltage*10):03d}")

    def set_current(self, current):
        """
        Set the output current
        :param current: Current in Ampere
        """
        if current < 0 or current > self.max_current:
            raise ValueError(f"Current ({current} A) out of range! Must be within [0 A, {self.max_current} A]")
        self._request(f"CURR{int(current*100):03d}")

    def get_voltage_and_current(self):
        """
        Get the current settings for voltage and current
        :return: (voltage, current)
        """
        response = self._request("GETS")[0]
        return self._voltage_and_current_from_response_string(response)

    def get_voltage(self):
        """
        Get Voltage in V
        """
        return self.get_voltage_and_current()[0]

    def get_current(self):
        """
        Get Current in A
        """
        return self.get_voltage_and_current()[1]

    def get_display_values(self):
        """
        Get the currently displayed values
        :return: (voltage, current, 'cv'|'cc')
        """
        response = self._request("GETD")[0]
        return *self._voltage_and_current_from_response_string(response[:8]), 'cv' if response[8] == '0' else 'cc'

    def save_voltages_and_currents_to_memory(self, v1, c1, v2, c2, v3, c3):
        """
        Save three pairs of (voltage, current) to the device's memory
        """
        raise NotImplementedError

    def get_voltages_and_currents_from_memory(self):
        """
        Get the saved pairs of (voltage, current) to the device's memory
        :return: [(v, c), (v, c), (v, c)]
        """
        response = self._request("GETM")[0]
        return [self._voltage_and_current_from_response_string(s)
                for s in [response[:6], response[6:12], response[12:]]]

    def apply_setting_from_memory(self, location):
        """
        Apply a previously stored setting
        :param location: Memory location. Must be in [0, 1, 2]
        """
        assert location in [0, 1, 2], f'{location=} out of range! Must be in [0, 1, 2]'
        self._request(f"RUNM{location}")

    def get_max_voltage(self):
        """
        Get preset upper limit of output Voltage
        :return: voltage in Volt
        """
        response = self._request("GOVP")[0]
        return self._voltage_from_response_string(response)

    def set_max_voltage(self, voltage):
        """
        Preset upper limit of output Voltage
        :param voltage: Voltage in Volt
        """
        if voltage < 1 or voltage > self.max_voltage:
            raise ValueError(f"Voltage ({voltage} V) out of range! Must be within [1 V, {self.max_voltage} V]")
        self._request(f"SOVP{int(voltage*10):03d}")

    def get_max_current(self):
        """
        Get preset upper limit of output Current
        :return: current in Ampere
        """
        response = self._request("GOCP")[0]
        return self._current_from_response_string(response)

    def set_max_current(self, current):
        """
        Preset upper limit of output Current
        :param current: Current in Ampere
        """
        if current < 0 or current > self.max_current:
            raise ValueError(f"Current ({current} A) out of range! Must be within [0 A, {self.max_current} A]")
        self._request(f"SOCP{int(current*100):03d}")

    def gui_open(self):
        """
        Open PPS11360 GUI Window
        """
        self.app = PPS11360Window(self)


class PPS11360Window(QWidget):

    def __init__(self, device: PPS11360):
        super().__init__()
        # Variables
        self._device = device

        # Appearance
        self.setWindowTitle(f"{self._device.name}")
        self.setGeometry(900, 500, 0, 0)

        # Current Values
        voltage, current, limiter = self._device.get_display_values()[:3]
        layout_current_values = QFormLayout()
        widget_current_values = QWidget()
        self._label_voltage = QLabel(str(voltage))
        self._label_current = QLabel(str(current))
        self._label_limiter = QLabel(str(limiter.upper()))
        layout_current_values.addRow(QLabel("<b>Current Values</b>"))
        layout_current_values.addRow(QLabel("Voltage / V"), self._label_voltage)
        layout_current_values.addRow(QLabel("Current / A"), self._label_current)
        layout_current_values.addRow(QLabel("Limiter"), self._label_limiter)
        widget_current_values.setLayout(layout_current_values)

        # Set Values
        voltage, current = self._device.get_voltage_and_current()
        layout_set_values = QFormLayout()
        widget_set_values = QWidget()
        layout_set_values.addRow(QLabel("<b>Set Values</b>"))
        self._line_edit_voltage = QDoubleSpinBox()
        self._line_edit_voltage.setRange(1, self._device.max_voltage)
        self._line_edit_voltage.setValue(float(voltage))
        self._line_edit_voltage.valueChanged.connect(self._handle_line_edit_voltage_changed)
        layout_set_values.addRow(QLabel("Voltage / V"), self._line_edit_voltage)
        self._line_edit_current = QDoubleSpinBox()
        self._line_edit_current.setRange(0, self._device.max_current)
        self._line_edit_current.setValue(float(current))
        self._line_edit_current.valueChanged.connect(self._handle_line_edit_current_changed)
        layout_set_values.addRow(QLabel("Current / A"), self._line_edit_current)
        self._button_output = ToggleButton(state=True)
        self._device.set_output(True)
        self._button_output.clicked.connect(self._handle_button_output)
        layout_set_values.addRow(QLabel("Output"), self._button_output)
        widget_set_values.setLayout(layout_set_values)

        # Window Layout
        layout = QHBoxLayout()
        layout.addWidget(widget_current_values)
        layout.addWidget(widget_set_values)
        self.setLayout(layout)

        # Refresh Timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_values)
        self._timer.start(1000)
        self._refresh_values()

        self.show()

    @pyqtSlot()
    def _refresh_values(self):
        """
        Refresh all Labels
        """
        voltage, current, limiter = self._device.get_display_values()[:3]
        self._label_voltage.setText(str(voltage))
        self._label_current.setText(str(current))
        self._label_limiter.setText(limiter.upper())

    @pyqtSlot()
    def _handle_line_edit_voltage_changed(self):
        """
        Set Voltage
        """
        self._device.set_voltage(float(self._line_edit_voltage.value()))

    @pyqtSlot()
    def _handle_line_edit_current_changed(self):
        """
        Set Current
        """
        self._device.set_current(float(self._line_edit_current.value()))

    @pyqtSlot()
    def _handle_button_output(self):
        """
        Set Output
        """
        self._device.set_output(self._button_output.isChecked())

    @pyqtSlot()
    def closeEvent(self, event):
        """
        Stop Timer when Window is closed
        """
        if hasattr(self, "_timer"):
            self._timer.stop()
        event.accept()
