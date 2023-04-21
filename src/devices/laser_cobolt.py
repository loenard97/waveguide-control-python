"""
Cobolt Laser Series 06-01
"""

from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QComboBox, QDoubleSpinBox, QVBoxLayout, QMainWindow

from src.devices.main_device import USBDevice
from src.measurement.units import mA, mW
from src.static_gui_elements.toggle_button import ToggleButton


class LaserCobolt(USBDevice):

    # Laser always returns 'OK', 'Syntax error: illegal command' or a value.
    # That means you should always use self._LAST_ERROR = self.read("<command>") instead of self.write("<command>")
    # when sending commands.

    TERMINATION_WRITE = '\r'
    BAUDRATE = 112500
    _LAST_ERROR = ""

    OPERATING_MODE_CODES = {
        "0": "Off",
        "1": "Waiting for key",
        "2": "Continuous",
        "3": "On/Off Modulation",
        "4": "Modulation",
        "5": "Fault",
        "6": "Aborted",
    }
    INTERLOCK_STATE_CODES = {
        "0": "OK",
        "1": "interlock open",
    }
    OPERATING_FAULT_CODES = {
        "0": "no errors",
        "1": "temperature error",
        "3": "interlock error",
        "4": "constant power timeout",
    }
    ANALOG_LOW_IMPEDANCE_CODES = {
        "0": "HIGH Z (1000 Ohm)",
        "1": "50 Ohm",
    }

    def get_error(self) -> str:
        """
        Get Last Error from Device.
        :return str: Empty String if no Error occurred, otherwise Error Message
        :raises NotImplementedError:
        """
        error_msg = self._LAST_ERROR.removeprefix("OK")
        self._LAST_ERROR = ''
        return error_msg

    def reset(self):
        """
        Reset Device to default Settings
        """
        self.set_mode_ci(current=0.0)
        self._LAST_ERROR = self.read("cf")

    def get_serial_number(self):
        """
        Get Serial Number
        """
        return self.read("gsn?")

    def set_output(self, state=False):
        """
        Set Laser Output
        :param bool state: Output State
        """
        self._LAST_ERROR = self.read(f"{'@cob1' if state else 'l0'}")

    def get_output(self):
        """
        Get Laser Output State
        """
        return '1' in self.read("l?")

    def get_key_state(self):
        """
        Get Key Switch State
        """
        return '1' in self.read("@cobasks?")

    def set_direct_input(self, state=False):
        """
        Set 5V Direct Input (OEM only)
        """
        self._LAST_ERROR = self.read(f"@cobasdr{'1' if state else '2'}")

    def set_power(self, power=0.0):
        """
        Set Constant Power
        :param float power: Output Power in W
        """
        self._LAST_ERROR = self.read("cp")
        self._LAST_ERROR = self.read(f"p {power}")

    def get_power(self):
        """
        Get Current Power
        """
        return self.read("pa?")

    def get_current(self):
        """
        Get Current in A
        """
        return float(self.read("i?"))

    def set_mode_cw(self, power=0.0):
        """
        Set Constant Power Mode
        :param float power: Output Power in W
        """
        self._LAST_ERROR = self.read("cp")
        self._LAST_ERROR = self.read(f"p {power}")

    def set_mode_ci(self, current=0.0):
        """
        Set Constant Current Mode
        :param float current: Diode Current in A
        """
        self._LAST_ERROR = self.read("ci")
        self._LAST_ERROR = self.read(f"slc {current / mA}")

    def set_modulation_analog(self, power=0.0, state=True):
        """
        Set Analog Modulation
        :param float power: Output Power in W
        :param bool state: Modulation State
        """
        self._LAST_ERROR = self.read("em")
        self._LAST_ERROR = self.read("sdmes 0")
        self.set_power(power)
        self._LAST_ERROR = self.read(f"sames {'1' if state else '0'}")

    def set_modulation_digital(self, power=0.0, state=True):
        """
        Set Digital Modulation
        :param float power: Output Power in W
        :param bool state: Modulation State
        """
        self._LAST_ERROR = self.read("em")
        self._LAST_ERROR = self.read("sames 0")
        self.set_power(power)
        self._LAST_ERROR = self.read(f"sdmes {'1' if state else '0'}")

    def get_operating_mode(self):
        """
        Get Operation Mode
        """
        mode = self.read("gom?")
        return self.OPERATING_MODE_CODES[mode]

    def get_interlock_state(self):
        """
        Get Interlock State
        """
        state = self.read("ilk?")
        return self.INTERLOCK_STATE_CODES[state]

    def get_operating_fault(self):
        """
        Get Operating Fault
        """
        fault = self.read("f?")
        return self.OPERATING_FAULT_CODES[fault]

    def get_diode_operating_hours(self):
        """
        Get Diode Operating Hours
        """
        return self.read("hrs?")

    def get_analog_modulation_state(self):
        """
        Get Analog Modulation State
        """
        return self.read("games?")

    def set_modulation_mode(self):
        """
        Set Modulation Mode
        """
        self._LAST_ERROR = self.read("em")

    def get_laser_current(self):
        """
        Read actual Laser Current
        """
        return self.read("rlc?")

    def get_laser_current_set_point(self):
        """
        Get Laser Current Set Point
        """
        return self.read("glc?")

    def get_output_power_set_point(self):
        """
        Get Output Power Set Point
        """
        return self.read("p?")

    def set_laser_current(self, current):
        """
        Set Laser Current
        :param float current: Current in A
        """
        self._LAST_ERROR = self.read(f"slc {current / mA}")

    # DPL specific Commands

    def set_modulation_high_current(self, current):
        """
        Set Modulation High Current
        :param float current: Current in A
        """
        self._LAST_ERROR = self.read(f"smc {current*mA}")

    def get_modulation_high_current(self):
        """
        Get Modulation High Current
        """
        return self.read("gmc?")

    def set_modulation_low_current(self, current):
        """
        Set Modulation Low Current
        :param float current: Current in A
        """
        self._LAST_ERROR = self.read(f"slth {current*mA}")

    def get_modulation_low_current(self):
        """
        Get Modulation Low Current
        """
        return self.read("glth?")

    def set_temperature(self, temperature):
        """
        Set TEC LD MOD Temperature
        :param float temperature: Temperature in °C
        """
        self._LAST_ERROR = self.read(f"stec4t {temperature}")

    def get_temperature(self):
        """
        Get TEC LD MOD Temperature
        """
        return self.read("gtec4t?")

    def get_actual_temperature(self):
        """
        Get Actual TEC LD MOD temperature
        """
        return self.read("rtec4t?")

    # MLD specific Commands

    def get_laser_modulation_power_set_point(self):
        """
        Get Laser Modulation Power Set Point
        """
        return self.read("glmp?")

    def set_laser_modulation_power(self, power):
        """
        Set Laser Modulation ower
        :param float power: Power in W
        """
        self._LAST_ERROR = self.read(f"slmp {power*mW}")

    def get_analog_low_impedance_state(self):
        """
        Get Analog Low Impedance State
        0: 1000 Ohm, 1: 50 Ohm
        """
        impedance = self.read("galis?")
        return self.ANALOG_LOW_IMPEDANCE_CODES[impedance]

    def set_analog_low_impedance_state(self, impedance):
        """
        Set Analog Low Impedance State
        :param str impedance: 0 HIGH Z (1000 Ohm) | 1 50 Ohm
        """
        self._LAST_ERROR = self.read(f"salis {impedance}")

    def gui_open(self):
        """
        Open GUI of Device
        """
        self._app = LaserCoboltWindow(self)


class LaserCoboltWindow(QMainWindow):

    def __init__(self, device: LaserCobolt):
        super().__init__()
        # Variables
        self._device = device
        self._ci_mode_current = 0.0

        # Appearance
        self.setWindowTitle(f"{self._device.name}")
        self.setGeometry(900, 500, 0, 0)

        # Channel 1
        widget_cb = QWidget()
        layout_cb = QFormLayout()
        self._widget_form = QWidget()
        self._layout_form = QVBoxLayout()
        self._cb_mode = QComboBox()
        self._cb_mode.addItems(["Continous Current", "Continous Power", "Digital Modulation"])
        self._cb_mode.currentIndexChanged.connect(self._handle_mode_changed)    # NOQA
        layout_cb.addRow(QLabel("Operating Mode"), self._cb_mode)
        widget_cb.setLayout(layout_cb)

        widget_info = QWidget()
        layout_info = QFormLayout()
        layout_info.addWidget(QLabel("Info"))
        widget_info.setLayout(layout_info)

        # Output Buttons
        self._btn_output = ToggleButton(state=self._device.get_output())
        self._btn_output.clicked.connect(self._handle_btn_output)

        # Total Layout
        widget_total = QWidget()
        self._layout_form.addWidget(widget_cb)
        self._layout_form.addWidget(self._widget_form)
        self._layout_form.addWidget(self._btn_output)
        widget_total.setLayout(self._layout_form)
        self.setCentralWidget(widget_total)

        # Status Bar
        self._status_bar_label = QLabel()
        self.statusBar().addWidget(self._status_bar_label)

        # Status Bar Timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_error_label)  # NOQA
        self._timer.start(2000)

        # Initialization
        self._handle_mode_changed()

        self.show()

    @pyqtSlot()
    def _handle_mode_changed(self):
        """
        Replace Parameter Form according to selected operating mode
        """
        widget_new = QWidget()
        layout_new = QFormLayout()
        widget_new.setLayout(layout_new)

        cur_mode = self._cb_mode.currentText()

        # Create Layout depending on selected Waveform
        if cur_mode == "Continous Current":
            self._device.read("ci")
            sb_current = QDoubleSpinBox()
            sb_current.setDecimals(0)
            sb_current.setRange(0, 220)
            sb_current.setValue(self._device.get_current()*mA)
            sb_current.textChanged.connect(  # NOQA
                lambda: self._device.set_laser_current(sb_current.value()*mA))
            layout_new.addRow(QLabel("Current / mA"), sb_current)

        elif cur_mode == "Continous Power":
            layout_new.addRow(QLabel("Not Implemented"))

        elif cur_mode == "Digital Modulation":
            layout_new.addRow(QLabel("Not Implemented"))

        # Replace old Widget
        self._layout_form.replaceWidget(self._widget_form, widget_new)
        self._widget_form.hide()
        self._widget_form.destroy()
        self._widget_form = widget_new

    @pyqtSlot()
    def _handle_btn_output(self):
        """
        Switch Laser ON | OFF
        """
        # The Laser ON and OFF commands require the key to be turned each time. So instead we pause the output by
        # setting the laser current to 0mA when turning it off and resetting it to the old value when turning it on.
        cur_mode = self._cb_mode.currentText()
        if cur_mode == "Continous Current":
            if self._btn_output.isChecked():
                self._device.set_mode_ci(current=self._ci_mode_current*mA)
            else:
                self._ci_mode_current = self._device.get_current()
                self._device.set_mode_ci(current=0.0)

    @pyqtSlot()
    def _update_error_label(self):
        """
        Update Error in Status Bar
        """
        error_msg = self._device.get_error()
        if error_msg:
            self._status_bar_label.setText(f"\u26A0 Device Error: '{error_msg}'")

    @pyqtSlot()
    def closeEvent(self, event):
        """
        Stop Timer when Window is closed
        """
        if hasattr(self, "_timer"):
            self._timer.stop()
        event.accept()
