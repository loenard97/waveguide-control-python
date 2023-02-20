"""
Windfreak SynthHDv2 Radio Frequency Generator
"""

# ----- Notes -----
# On rare occasions the PLL charge pump current resets itself to 0 (possibly firmware bug).
# If that happens, Frequency and Phase start drifting around.
# reset() sets it back to 5. Just call that function at the start of every measurement, and you should be fine.

from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtWidgets import QLabel, QFormLayout, QWidget, QGridLayout, QDoubleSpinBox

from src.devices.device_main import USBDevice
from src.static_gui_elements.toggle_button import ToggleButton


class SynthHDv2RFG(USBDevice):
    NAME = "RFG WindFreak SynthHDv2"
    ICON = "rfg"

    def get_identification(self):
        """
        Get Model and Serial Number
        """
        return self.read('+')

    def reset(self):
        """
        Reset to Default Settings
        """
        # Temperature Compensation: 10s
        # Reference Clock: external
        # Reference Clock Frequency: 10MHz
        # Trigger: software
        # Sweep Type: linear
        # Sweep Continuous Mode: off

        # Outputs: Off
        # Frequency: 1000MHz
        # Amplitude: 0dBm
        # Phase Step: 0
        # PLL charge pump current: 5

        self.set_temperature_compensation(state=3)
        self.set_clock_reference(state=0)
        self.set_clock_reference_frequency(frequency=10)
        self.set_trigger_mode(state=0)
        self.set_sweep_type(state=0)
        self.set_sweep_continuously(state=0)

        self.set_output(channel=1, state=False)
        self.set_frequency(channel=1, frequency=1000)
        self.set_amplitude(channel=1, amplitude=0)
        self.set_phase_step(channel=1, step=0)
        self.set_pll_charge_pump_current(channel=1, state=5)

        self.set_output(channel=2, state=False)
        self.set_frequency(channel=2, frequency=1000)
        self.set_amplitude(channel=2, amplitude=0)
        self.set_phase_step(channel=2, step=0)
        self.set_pll_charge_pump_current(channel=2, state=5)

    def set_channel(self, channel=1):
        """
        Set Channel 1 | 2
        """
        assert channel in [1, 2], "Channel has to be 1 or 2"

        if channel == 1:
            self.write("C0")
        elif channel == 2:
            self.write("C1")

    def get_channel(self):
        """
        Get Channel 1 | 2
        """
        return int(self.read("C?"))

    def set_output(self, channel=1, state=False):
        """
        Set Output of Channel 0 | 1 to True | False
        """
        assert isinstance(state, bool), "State has to be bool"

        self.set_channel(channel)
        if state:
            self.write("r1E1")
        else:
            self.write("r0E0")

    def get_output(self, channel=1):
        """
        Get Output of Channel 0 | 1
        """
        self.set_channel(channel)
        out = self.read("E?")
        if out == '1':
            return True
        else:
            return False

    def set_frequency(self, channel=1, frequency=1000.0):
        """
        Set Frequency in MHz
        """
        if isinstance(frequency, str):
            frequency = frequency.replace(',', '.')

        assert 53 <= float(frequency) < 14000, "Frequency has to be between 53MHz and 14000MHz"

        self.set_channel(channel)
        self.write(f"f{frequency}")

    def get_frequency(self, channel=1):
        """
        Get Frequency in MHz
        """
        self.set_channel(channel)
        try:
            return float(self.read("f?"))
        except ValueError:
            return -1.0

    def set_amplitude(self, channel=1, amplitude=0.0):
        """
        Set Amplitude in dBm
        """
        if isinstance(amplitude, str):
            amplitude = amplitude.replace(',', '.')

        assert -60 <= float(amplitude) <= 20, "Amplitude has to be between -60dBm and 20dBm"

        self.set_channel(channel)
        self.write(f"W{amplitude}")

    def get_amplitude(self, channel=1):
        """
        Get Amplitude in dBm
        """
        self.set_channel(channel)
        try:
            return float(self.read("W?"))
        except ValueError:
            return -1.0

    def get_calibration_status(self):
        """
        Get Calibration Status
        0 not successful | 1 successful
        """
        return self.read("V")

    def get_internal_temperature(self):
        """
        Get Internal Temperature in °C
        """
        return self.read("z")

    def set_temperature_compensation(self, state=3):
        """
        Set Temperature Compensation Mode
        0 off | 1 on | 2 every 3sec | 3 every 10sec
        """
        self.write(f"Z{state}")

    def get_temperature_compensation(self):
        """
        Get Temperature Compensation Mode
        0 off | 1 on | 2 every 3sec | 3 every 10sec
        """
        return self.read("Z?")

    def set_mute(self, state):
        """
        Set Mute RF Output
        """
        if state:
            self.write("h1")
        else:
            self.write("h0")

    def get_mute(self):
        """
        Get Mute RF Output
        """
        return self.read("h?")

    def set_pll_charge_pump_current(self, channel=1, state=5):
        """
        Set PLL charge pump current
        """
        assert 0 <= state <= 15, "State has to be between 0 and 15"

        self.set_channel(channel)
        self.write(f"U{state}")

    def get_pll_charge_pump_current(self, channel=1):
        """
        Get PLL charge pump current
        """
        self.set_channel(channel)
        return self.read(f"U?")

    def set_clock_reference(self, state=0):
        """
        Set Clock Reference (0 external | 1 internal 27MHz | 2 internal 10MHz)
        """
        assert 0 <= state <= 2, "State has to be between 0 and 2"

        self.write(f"x{state}")

    def get_clock_reference(self):
        """
        Get Clock Reference (0 external | 1 internal 27MHz | 2 internal 10MHz)
        """
        return self.read("x?")

    def set_clock_reference_frequency(self, frequency=10):
        """
        Set Frequency of External Clock Signal in MHz
        """
        assert 10 <= frequency <= 100, "Frequency has to be between 10MHz and 100MHz"

        self.write(f"*{frequency}")

    def get_clock_reference_frequency(self) -> float:
        """
        Get Frequency of External Clock Signal in MHz (10-100MHz)
        """
        try:
            return float(self.read("*?"))
        except ValueError:
            return -1.0

    def set_vga_dac(self, dac):
        """
        Set VGA DCA Setting [0, 45000]
        """
        self.write(f"a{dac}")

    def get_vga_dac(self):
        return self.read("a?")

    def set_phase_step(self, channel=1, step=0):
        self.set_channel(channel)
        self.write(f"~{step}")

    def get_phase_step(self):
        return self.read("~?")

    def set_sweep_lower_frequency(self, frequency):
        self.write(f"l{frequency}")

    def get_sweep_lower_frequency(self):
        return self.read("l?")

    def set_sweep_upper_frequency(self, frequency):
        self.write(f"u{frequency}")

    def get_sweep_upper_frequency(self):
        return self.read("u?")

    def set_sweep_step_size(self, step):
        self.write(f"s{step}")

    def get_sweep_step_size(self):
        return self.read("s?")

    def set_sweep_step_time(self, time):
        """
        Set Step Time for linear Sweeps
        min 4ms | max 10.000ms
        """
        self.write(f"t{time}")

    def get_sweep_step_time(self):
        """
        Get Step Time for linear Sweeps
        min 4ms | max 10.000ms
        """
        return self.read("t?")

    def set_sweep_lower_amplitude(self, amplitude):
        self.write(f"[{amplitude}")

    def get_sweep_lower_amplitude(self):
        return self.read("[?")

    def set_sweep_upper_amplitude(self, amplitude):
        self.write(f"]{amplitude}")

    def get_sweep_upper_amplitude(self):
        return self.read("]?")

    def set_sweep_direction(self, direction):
        """
        Set Sweep Direction
        0 down | 1 up
        """
        self.write(f"^{direction}")

    def get_sweep_direction(self):
        """
        Get Sweep Direction
        0 up | 1 down
        """
        return self.read("^?")

    def set_sweep_type(self, state=0):
        """
        Set Sweep Type
        0 linear | 1 tabular
        """
        assert 0 <= state <= 1, "State has to be between 0 and 1"

        self.write(f"X{state}")

    def get_sweep_type(self):
        """
        Get Sweep Direction
        0 linear | 1 tabular
        """
        return self.read("X?")

    def set_sweep_run(self, state):
        """
        Set Sweep Run
        Set to 1 to trigger sweep. Value stays at 1 during a sweep.
        Set to 0 during a sweep to pause it until it is set to 1 again.
        """
        self.write(f"g{state}")

    def get_sweep_run(self):
        """
        Get Sweep Run
        """
        return self.read("g?")

    def set_sweep_continuously(self, state=0):
        """
        Set Sweep Continuously
        0 single sweep | 1 continuous
        """
        assert 0 <= state <= 1, "State has to be 0 or 1"

        self.write(f"c{state}")

    def get_sweep_continuously(self):
        """
        Set Sweep Continuously
        0 single sweep | 1 continuous
        """
        return self.read("c?")

    def set_trigger_mode(self, state=0):
        """
        Set Trigger Mode
        0 No Triggers
        1 Trigger full frequency sweep
        2 Trigger single frequency step
        3 Trigger “stop all” which pauses sequencing through all functions of the SynthHD
        4 Trigger digital RF ON/OFF – Could be used for External Pulse Modulation
        5 Remove Interrupts (Makes modulation have less jitter – use carefully)
        6 Reserved
        7 Reserved
        8 External AM modulation input (requires AM Internal modulation LUT set to ramp)
        9 External FM modulation input (requires FM Internal modulation set to chirp
        """
        assert 0 <= state <= 9, "State has to be between 0 and 9"

        self.write(f"w{state}")

    def get_trigger_mode(self):
        """
        Set Trigger Mode
        0 No Triggers
        1 Trigger full frequency sweep
        2 Trigger single frequency step
        3 Trigger “stop all” which pauses sequencing through all functions of the SynthHD
        4 Trigger digital RF ON/OFF – Could be used for External Pulse Modulation
        5 Remove Interrupts (Makes modulation have less jitter – use carefully)
        6 Reserved
        7 Reserved
        8 External AM modulation input (requires AM Internal modulation LUT set to ramp)
        9 External FM modulation input (requires FM Internal modulation set to chirp
        """
        return self.read("w?")

    def gui_open(self):
        """
        Open SynthHDv2 RFG GUI Window
        """
        self.app = SynthHDv2RFGWindow(self)


class SynthHDv2RFGWindow(QWidget):
    def __init__(self, device: SynthHDv2RFG):
        super().__init__()
        # Variables
        self._device = device

        # Appearance
        self.setWindowTitle(f"{self._device.NAME}")
        self.setGeometry(735, 365, 450, 350)

        # Info
        layout_info = QFormLayout()
        widget_info = QWidget()
        layout_info.addRow(QLabel("<b>Info</b>"))
        self._label_temperature = QLabel()
        layout_info.addRow(QLabel("Temperature / °C"), self._label_temperature)
        self._device.set_clock_reference_frequency(30)
        self.line_edit_clock_frequency = QDoubleSpinBox()
        self.line_edit_clock_frequency.setRange(10, 100)
        self.line_edit_clock_frequency.setValue(self._device.get_clock_reference_frequency())
        # self.line_edit_clock_frequency.valueChanged.connect(
        #     lambda: self._device.set_clock_reference_frequency(frequency=self.line_edit_clock_frequency.text())
        # )
        layout_info.addRow(QLabel("Clock Frequency / MHz"), self.line_edit_clock_frequency)
        widget_info.setLayout(layout_info)

        # Channel 1
        widget_line_edit_ch1 = QWidget()
        layout_line_edit_ch1 = QFormLayout()
        layout_line_edit_ch1.addRow(QLabel("<b>Channel 1</b>"))
        self.line_edit_clock_frequency = QDoubleSpinBox()
        self.line_edit_clock_frequency.setRange(53, 13998)
        self.line_edit_clock_frequency.setValue(self._device.get_frequency(channel=1))
        self.line_edit_clock_frequency.valueChanged.connect(
            lambda: self._device.set_frequency(channel=1, frequency=self.line_edit_clock_frequency.text())
        )
        layout_line_edit_ch1.addRow(QLabel("Frequency / MHz"), self.line_edit_clock_frequency)
        self.line_edit_amplitude_ch1 = QDoubleSpinBox()
        self.line_edit_amplitude_ch1.setRange(-60, 20)
        self.line_edit_amplitude_ch1.setValue(self._device.get_amplitude(channel=1))
        self.line_edit_amplitude_ch1.valueChanged.connect(
            lambda: self._device.set_amplitude(channel=1, amplitude=self.line_edit_amplitude_ch1.text())
        )
        layout_line_edit_ch1.addRow(QLabel("Amplitude / dBm"), self.line_edit_amplitude_ch1)
        widget_line_edit_ch1.setLayout(layout_line_edit_ch1)

        # Channel 2
        widget_line_edit_ch2 = QWidget()
        layout_line_edit_ch2 = QFormLayout()
        layout_line_edit_ch2.addRow(QLabel("<b>Channel 2</b>"))
        self.line_edit_frequency_ch2 = QDoubleSpinBox()
        self.line_edit_frequency_ch2.setRange(53, 13998)
        self.line_edit_frequency_ch2.setValue(float(self._device.get_frequency(channel=2)))
        self.line_edit_frequency_ch2.valueChanged.connect(
            lambda: self._device.set_frequency(channel=2, frequency=self.line_edit_frequency_ch2.text())
        )
        layout_line_edit_ch2.addRow(QLabel("Frequency / MHz"), self.line_edit_frequency_ch2)
        self.line_edit_amplitude_ch2 = QDoubleSpinBox()
        self.line_edit_amplitude_ch2.setRange(-60, 20)
        self.line_edit_amplitude_ch2.setValue(float(self._device.get_amplitude(channel=2)))
        self.line_edit_amplitude_ch2.valueChanged.connect(
            lambda: self._device.set_amplitude(channel=2, amplitude=self.line_edit_amplitude_ch2.text())
        )
        layout_line_edit_ch2.addRow(QLabel("Amplitude / dBm"), self.line_edit_amplitude_ch2)
        widget_line_edit_ch2.setLayout(layout_line_edit_ch2)

        # Buttons
        self.button_output_ch1 = ToggleButton(state=self._device.get_output(channel=1))
        self.button_output_ch1.clicked.connect(
            lambda: self._device.set_output(channel=1, state=self.button_output_ch1.isChecked())
        )
        self.button_output_ch2 = ToggleButton(state=self._device.get_output(channel=2))
        self.button_output_ch2.clicked.connect(
            lambda: self._device.set_output(channel=2, state=self.button_output_ch1.isChecked())
        )

        # Total Layout
        layout = QGridLayout()
        layout.addWidget(widget_info, 0, 0)
        layout.addWidget(widget_line_edit_ch1, 2, 0)
        layout.addWidget(widget_line_edit_ch2, 2, 1)
        layout.addWidget(self.button_output_ch1, 3, 0)
        layout.addWidget(self.button_output_ch2, 3, 1)
        self.setLayout(layout)

        # Initialization
        self._refresh_values()

        # Timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._refresh_values)
        self._timer.start(3000)

        self.show()

    @pyqtSlot()
    def _refresh_values(self):
        """
        Refresh Info Labels
        """
        self._label_temperature.setText(self._device.get_internal_temperature())

    @pyqtSlot()
    def closeEvent(self, event):
        """
        Stop Timer when Window is closed
        """
        self._timer.stop()
        event.accept()
