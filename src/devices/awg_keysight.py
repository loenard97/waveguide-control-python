"""
Keysight Arbitrary Waveform Generator
"""

from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QFormLayout, QVBoxLayout, QMainWindow, QFrame

from src.devices.main_device import EthernetDevice
from src.static_gui_elements.toggle_button import ToggleButton
from src.static_gui_elements.delayed_spin_box import DelayedDoubleSpinBox


class AWGKeysight(EthernetDevice):
    """
    Arbitrary Waveform Generator by Keysight
    """

    def __init__(self, name="AWG Keysight", address="", settings=None):
        super().__init__(name, address, settings)

        # Channel Names
        self.channel = ["1", "2"]
        if "Channel" in self.settings:
            for name, value in self.settings["Channel"].items():
                self.channel[name - 1] = value

        # Set maximum sample rate for arbitrary functions
        model_nr = self.get_identification().split(',')[1]
        if model_nr == "33622A":
            self.MAX_SRAT = 250E6
        else:
            self.MAX_SRAT = 62.5E6

    def get_error(self) -> None | str:
        """
        Get Last Error
        """
        err = self.read("SYST:ERR?", error_checking=False)
        if err == '+0,"No error"':
            return None
        return err

    def _convert_channel(self, channel):
        """
        Convert Channel String to int
        :param int | str channel: Channel Number or Name
        """
        if isinstance(channel, int):
            return channel
        if isinstance(channel, str) and channel in self.channel:
            return self.channel.index(channel) + 1
        raise ValueError(f"{self.name}: Unknown Channel '{channel}'")

    def get_identification(self):
        """
        Get Identification String
        """
        return self.read("*IDN?")

    def clear(self):
        """
        Clear Status
        """
        self.write("*CLS")

    def reset(self):
        """
        Reset Device to default Settings
        """
        self.write("*RST")

    def soft_reset(self):
        """
        Reset Device but keep initial Settings
        """
        self.reset()

    def trigger(self):
        """
        Trigger Command
        """
        self.write("*TRG")

    # Settings
    def set_output(self, channel=1, state=False):
        """
        Set Output State
        :param int | str channel: Channel Name
        :param bool state: State
        """
        channel = self._convert_channel(channel)
        self.write(f"OUTP{channel} {'ON' if state else 'OFF'}")

    def get_output(self, channel: int) -> bool:
        """
        Get Output of channel 1|2
        """
        return self.read(f"OUTP{channel}?") == "1"

    def set_function(self, channel, function):
        """
        Set Function SIN|SQU|TRI|RAMP|PULS|PRBS|NOIS|ARB|DC
        """
        self.write(f"SOUR{channel}:FUNC {function}")

    def get_function(self, channel):
        """
        Get Function SIN|SQU|TRI|RAMP|PULS|PRBS|NOIS|ARB|DC
        """
        return self.read(f"SOUR{channel}:FUNC?")

    def set_frequency(self, channel, frequency):
        """
        Set Frequency in Hz
        """
        self.write(f"SOUR{channel}:FREQ {frequency}")

    def get_frequency(self, channel):
        """
        Get Frequency in Hz
        """
        return float(self.read(f"SOUR{channel}:FREQ?"))

    def set_amplitude(self, channel, amplitude):
        """
        Set Amplitude in V
        """
        self.write(f"SOUR{channel}:VOLT {amplitude}")

    def get_amplitude(self, channel):
        """
        Get Amplitude in V
        """
        return float(self.read(f"SOUR{channel}:VOLT?"))

    def set_offset(self, channel, offset):
        """
        Set Offset in V
        """
        self.write(f"SOUR{channel}:VOLT:OFFS {offset}")

    def get_offset(self, channel: int) -> float:
        """
        Get Offset in V
        """
        return float(self.read(f"SOUR{channel}:VOLT:OFFS?"))

    def set_phase(self, channel, phase):
        """
        Set Phase in °
        """
        self.write(f"SOUR{channel}:PHAS {phase}")

    def get_phase(self, channel: int) -> float:
        """
        Get Phase in °
        """
        return float(self.read(f"SOUR{channel}:PHAS?"))

    # Waveform Settings
    def set_square_duty_cycle(self, channel, duty_cycle):
        """
        Set Duty Cycle of Square Mode
        """
        if isinstance(duty_cycle, str):
            duty_cycle = duty_cycle.replace(',', '.')
        self.write(f"SOUR{channel}:FUNC:SQU:DCYC {duty_cycle}")

    def get_square_duty_cycle(self, channel):
        """
        Get Duty Cycle of Square Mode
        """
        return float(self.read(f"SOUR{channel}:FUNC:SQU:DCYC?"))

    def set_ramp_symmetry(self, channel, symmetry):
        """
        Set Symmetry of Ramp Mode
        """
        if isinstance(symmetry, str):
            symmetry = symmetry.replace(',', '.')
        self.write(f"SOUR{channel}:FUNC:RAMP:SYMM {symmetry}")

    def get_ramp_symmetry(self, channel):
        """
        Get Symmetry of Ramp Mode
        """
        return float(self.read(f"SOUR{channel}:FUNC:RAMP:SYMM?"))

    def set_pulse_width(self, channel, width):
        """
        Set Width of Pulse Mode
        """
        if isinstance(width, str):
            width = width.replace(',', '.')
        self.write(f"SOUR{channel}:FUNC:PULS:WIDT {width}")

    def get_pulse_width(self, channel):
        """
        Get Width of Pulse Mode
        """
        return float(self.read(f"SOUR{channel}:FUNC:PULS:WIDT?"))

    def set_pulse_lead_edge(self, channel, lead_edge):
        """
        Set Lead Edge of Pulse Mode
        """
        if isinstance(lead_edge, str):
            lead_edge = lead_edge.replace(',', '.')
        self.write(f"SOUR{channel}:FUNC:PULS:TRAN:LEAD {lead_edge}")

    def get_pulse_lead_edge(self, channel):
        """
        Get Lead Edge of Pulse Mode
        """
        return float(self.read(f"SOUR{channel}:FUNC:PULS:TRAN:LEAD?"))

    def set_pulse_trail_edge(self, channel, trail_edge):
        """
        Set Trail Edge of Pulse Mode
        """
        if isinstance(trail_edge, str):
            trail_edge = trail_edge.replace(',', '.')
        self.write(f"SOUR{channel}:FUNC:PULS:TRAN:TRA {trail_edge}")

    def get_pulse_trail_edge(self, channel):
        """
        Get Trail Edge of Pulse Mode
        """
        return float(self.read(f"SOUR{channel}:FUNC:PULS:TRAN:TRA?"))

    # Trigger Settings
    def set_trigger_count(self, channel, count):
        """
        Set Trigger Count
        """
        if isinstance(count, str):
            count = count.replace(',', '.')
        self.write(f"TRIG{channel}:COUN {count}")

    def get_trigger_count(self, channel):
        """
        Get Trigger Count
        """
        return float(self.read(f"TRIG{channel}:COUN?"))

    def set_trigger_delay(self, channel, delay):
        """
        Set Trigger Delay in s
        """
        if isinstance(delay, str):
            delay = delay.replace(',', '.')
        self.write(f"TRIG{channel}:DEL {delay}")

    def get_trigger_delay(self, channel):
        """
        Get Trigger Delay in s
        """
        return float(self.read(f"TRIG{channel}:DEL?"))

    def set_trigger_slope(self, channel, slope):
        """
        Set Trigger Slope POS | NEG
        """
        if slope.upper() in ["POS", "NEG"]:
            self.write(f"TRIG{channel}:SLOP {slope.upper()}")
        else:
            raise ValueError("Trigger Slope has to be 'POS' or 'NEG'")

    def get_trigger_slope(self, channel):
        """
        Get Trigger Slope POS | NEG
        """
        return float(self.read(f"TRIG{channel}:SLOP?"))

    def set_trigger_source(self, channel, source):
        """
        Set Trigger Source IMM | EXT | TIM | BUS
        """
        if source.upper() in ["IMM", "EXT", "TIM", "BUS"]:
            self.write(f"TRIG{channel}:SOUR {source.upper()}")
        else:
            raise ValueError("Trigger Source has to be 'IMM', 'EXT', 'TIM' or 'BUS'")

    def get_trigger_source(self, channel):
        """
        Get Trigger Source IMM | EXT | TIM | BUS
        """
        return float(self.read(f"TRIG{channel}:SOUR?"))

    def set_trigger_timer(self, channel, timer):
        """
        Set Trigger Timer in s
        """
        if isinstance(timer, str):
            timer = timer.replace(',', '.')
        self.write(f"TRIG{channel}:TIM {timer}")

    def get_trigger_timer(self, channel):
        """
        Get Trigger Timer in s
        """
        return float(self.read(f"TRIG{channel}:TIM?"))

    def set_burst_state(self, channel, state):
        """
        Set Burst State ON | OFF
        """
        if state.upper() in ["ON", "OFF"]:
            self.write(f"SOUR{channel}:BURS:STAT {state.upper()}")
        else:
            raise ValueError("Burst State has to be 'ON' or 'OFF'")

    def get_burst_state(self, channel):
        """
        Get Burst State
        """
        return self.read(f"SOUR{channel}:BURS:STAT?")

    def set_burst_number_cycles(self, channel, number_cycles):
        """
        Set Burst Number of Cycles
        """
        if isinstance(number_cycles, str):
            number_cycles = number_cycles.replace(',', '.')
        self.write(f"SOUR{channel}:BURS:NCYC {number_cycles}")

    def get_burst_number_cycles(self, channel):
        """
        Get Burst Number of Cycles
        """
        return float(self.read(f"SOUR{channel}:BURS:NCYC?"))

    def get_burst_mode(self, channel):
        """
        Get Burst Mode
        """
        return self.read(f"SOUR{channel}:BURS:MODE?")

    # Burst and Trigger
    def set_trigger(self, channel=1, source="EXT", slope="POS"):
        """
        Set Trigger Settings
        :param int | str channel: Channel Name
        :param str source: Trigger Source (EXT | INT)
        :param str slope: Trigger Slope (POS | NEG)
        """
        channel = self._convert_channel(channel)
        self.write(f"TRIG{channel}:SOURCE {source}")
        self.write(f"TRIG{channel}:SLOPE {slope}")

    def set_burst_mode(self, channel=1, number_cycles=1, mode="TRIG", state=False):
        """
        Set Burst Mode
        :param int | str channel: Channel Name
        :param int number_cycles: Number of Cycles
        :param str mode: Mode TRIG
        :param bool state: State
        """
        channel = self._convert_channel(channel)
        self.write(f"SOUR{channel}:BURS:NCYC {number_cycles}")
        self.write(f"SOUR{channel}:BURS:MODE {mode}")
        self.write(f"SOUR{channel}:BURS:STAT {'ON' if state else 'OFF'}")

    # Waveforms
    def set_constant_dc(self, channel=1, offset=0.0, state=False):
        """
        Set constant DC Signal
        :param int | str channel: Channel Name
        :param float offset: Offset in V
        :param bool state: Turn output on or off
        """
        channel = self._convert_channel(channel)
        self.write(f"SOUR{channel}:APPL:DC DEF, DEF, {offset}V")
        self.set_output(channel=channel, state=state)

    def set_constant_ttl(self, channel=1, state=False):
        """
        Set constant TTL Signal
        :param int | str channel: Channel Name
        :param bool state: TTL State (True = 3.3V | False = 0.0V)
        """
        channel = self._convert_channel(channel)
        self.write(f"SOUR{channel}:APPL:DC DEF, DEF, {3.3 if state else 0.0}V")

    def set_function_pulse(self, channel=1, frequency=1.0, amplitude=1.0, offset=0.0, duty_cycle=50.0):
        """
        Set Pulse function
        :param int | str channel: Channel Name
        :param float frequency: Frequency in Hz
        :param float amplitude: Amplitude in V
        :param float offset: Offset in V
        :param float duty_cycle: Duty Cycle in %
        """
        channel = self._convert_channel(channel)

        self.write(f"SOUR{channel}:FUNC PULS")
        self.write(f"SOUR{channel}:FREQ {frequency}")
        self.write(f"SOUR{channel}:VOLT {amplitude}")
        self.write(f"SOUR{channel}:VOLT:OFFS {offset}")
        self.write(f"SOUR{channel}:FUNC:PULS:DCYC {duty_cycle}")
        self.write(f"SOUR{channel}:FUNC:PULS:HOLD DCYC")

    def set_function_arbitrary(
            self, channel=1, amplitude=1.0, offset=0.0, sequence=None, sample_rate=None,
            trigger_source="EXT", trigger_slope="POS",
            burst_cycles=1, burst_mode="TRIG", burst_state=True,
            output_state=True):
        """
        Set Arbitrary Function.
        Default settings play the waveform once on an external trigger signal.
        :param int | str channel: Channel Name
        :param float amplitude: Amplitude in V
        :param float offset: Offset in V
        :param sequence: Pulse Sequence
        :param float sample_rate: Sample Rate in Samples per Second. Default is maximum possible sample rate and depends
            on the specific Model and Version of the AWG.
        :param str trigger_source: Trigger Source (EXT | INT)
        :param str trigger_slope: Trigger Slope (POS | NEG)
        :param int burst_cycles: Number of Cycles
        :param str burst_mode: Mode TRIG
        :param bool burst_state: Burst State
        :param bool output_state: Output State
        """
        channel = self._convert_channel(channel)
        if sample_rate is None:
            sample_rate = self.MAX_SRAT
        arb_str = sequence.get_sequence_keysight_awg(sample_rate)

        self.write(f"SOUR{channel}:DATA:VOL:CLE")
        self.write(f"SOUR{channel}:DATA:ARB myArb, {arb_str}")
        self.write(f"SOUR{channel}:FUNC:ARB myArb")
        self.write(f"SOUR{channel}:FUNC ARB")
        self.write(f"SOUR{channel}:FUNC:ARB:FILT OFF")
        self.write(f"SOUR{channel}:FUNC:ARB:SRAT {sample_rate}")
        self.write(f"SOUR{channel}:VOLT {amplitude}")
        self.write(f"SOUR{channel}:VOLT:OFFS {offset}")
        self.set_trigger(channel=channel, source=trigger_source, slope=trigger_slope)
        self.set_burst_mode(channel=channel, number_cycles=burst_cycles, mode=burst_mode, state=burst_state)
        self.set_output(channel=channel, state=output_state)

    def gui_open(self):
        """
        Open GUI
        """
        self._app = WaveformKeysightDualWindow(self)


class WaveformKeysightDualWindow(QMainWindow):

    def __init__(self, device: AWGKeysight):
        super().__init__()
        # Variables
        self._device = device

        # Appearance
        self.setWindowTitle(f"{self._device.name}")
        self.setGeometry(900, 500, 0, 0)

        # Channel 1
        widget_combo_box_ch1 = QWidget()
        layout_combo_box_ch1 = QFormLayout()
        self._widget_form_ch1 = QWidget()
        self._layout_ch1 = QVBoxLayout()
        layout_combo_box_ch1.addRow(QLabel("<b>Channel 1</b>"))
        self._combo_box_waveform_ch1 = QComboBox()
        self._combo_box_waveform_ch1.addItems(["SIN", "SQU", "TRI", "RAMP", "PULS", "PRBS", "NOIS", "ARB", "DC"])
        self._combo_box_waveform_ch1.setCurrentText(self._device.get_function(channel=1))
        self._combo_box_waveform_ch1.currentIndexChanged.connect(lambda: self._handle_waveform_changed(channel=1))  # NOQA
        layout_combo_box_ch1.addRow(QLabel("Waveform"), self._combo_box_waveform_ch1)
        widget_combo_box_ch1.setLayout(layout_combo_box_ch1)

        widget_burst_ch1 = QWidget()
        layout_burst_ch1 = QFormLayout()
        layout_burst_ch1.addWidget(QLabel("Burst Settings"))
        combo_box_burst_state_ch1 = QComboBox()
        combo_box_burst_state_ch1.addItems(["ON", "OFF"])
        combo_box_burst_state_ch1.setCurrentText(self._device.get_burst_state(channel=1))
        combo_box_burst_state_ch1.currentIndexChanged.connect(  # NOQA
            lambda: self._device.set_burst_state(channel=1, state=combo_box_burst_state_ch1.currentText()))
        layout_burst_ch1.addWidget(combo_box_burst_state_ch1)
        widget_burst_ch1.setLayout(layout_burst_ch1)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        # Channel 2
        widget_combo_box_ch2 = QWidget()
        layout_combo_box_ch2 = QFormLayout()
        self._widget_form_ch2 = QWidget()
        self._layout_ch2 = QVBoxLayout()
        layout_combo_box_ch2.addRow(QLabel("<b>Channel 2</b>"))
        self._combo_box_waveform_ch2 = QComboBox()
        self._combo_box_waveform_ch2.addItems(["SIN", "SQU", "TRI", "RAMP", "PULS", "PRBS", "NOIS", "ARB", "DC"])
        self._combo_box_waveform_ch2.setCurrentText(self._device.get_function(channel=2))
        self._combo_box_waveform_ch2.currentIndexChanged.connect(lambda: self._handle_waveform_changed(channel=2))  # NOQA
        layout_combo_box_ch2.addRow(QLabel("Waveform"), self._combo_box_waveform_ch2)
        widget_combo_box_ch2.setLayout(layout_combo_box_ch2)

        # Output Buttons
        self._button_output_ch1 = ToggleButton(state=self._device.get_output(channel=1))
        self._button_output_ch1.clicked.connect(    # NOQA
            lambda: self._device.set_output(channel=1, state=self._button_output_ch1.isChecked())
        )
        self._button_output_ch2 = ToggleButton(state=self._device.get_output(channel=2))
        self._button_output_ch2.clicked.connect(    # NOQA
            lambda: self._device.set_output(channel=2, state=self._button_output_ch2.isChecked())
        )

        # Total Layout
        widget_ch1 = QWidget()
        self._layout_ch1.addWidget(widget_combo_box_ch1)
        self._layout_ch1.addWidget(self._widget_form_ch1)
        self._layout_ch1.addWidget(self._button_output_ch1)
        widget_ch1.setLayout(self._layout_ch1)

        widget_ch2 = QWidget()
        self._layout_ch2.addWidget(widget_combo_box_ch2)
        self._layout_ch2.addWidget(self._widget_form_ch2)
        self._layout_ch2.addWidget(self._button_output_ch2)
        widget_ch2.setLayout(self._layout_ch2)

        layout = QHBoxLayout()
        layout.addWidget(widget_ch1)
        layout.addWidget(line)
        layout.addWidget(widget_ch2)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Status Bar
        self._last_error = self._device.get_error()
        self._status_bar_label = QLabel()
        self.statusBar().addWidget(self._status_bar_label)

        # Status Bar Timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_error_label)  # NOQA
        self._timer.start(2000)

        # Initialization
        self._handle_waveform_changed(channel=1)
        self._handle_waveform_changed(channel=2)

        self.show()

    @pyqtSlot()
    def _handle_waveform_changed(self, channel):
        """
        Replace Parameter Form according to selected Waveform
        """
        widget_new = QWidget()
        layout_new = QFormLayout()
        widget_new.setLayout(layout_new)

        if channel == 1:
            waveform = self._combo_box_waveform_ch1.currentText()
        else:
            waveform = self._combo_box_waveform_ch2.currentText()

        self._device.set_function(channel, function=waveform)

        # Create Layout depending on selected Waveform
        if waveform == "SIN":
            line_edit_frequency = DelayedDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.value()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = DelayedDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.value()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = DelayedDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.value()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = DelayedDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.value()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)

        elif waveform == "SQU":
            line_edit_frequency = DelayedDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.value()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = DelayedDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.value()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = DelayedDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.value()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = DelayedDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.value()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)
            line_edit_duty_cycle = DelayedDoubleSpinBox()
            line_edit_duty_cycle.setDecimals(2)
            line_edit_duty_cycle.setRange(0.05, 99.95)
            line_edit_duty_cycle.setValue(self._device.get_square_duty_cycle(channel))
            line_edit_duty_cycle.textChanged.connect(  # NOQA
                lambda: self._device.set_square_duty_cycle(channel, line_edit_duty_cycle.value()))
            layout_new.addRow(QLabel("Duty Cycle / %"), line_edit_duty_cycle)

        elif waveform == "TRI":
            line_edit_frequency = DelayedDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.value()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = DelayedDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.value()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = DelayedDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.value()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = DelayedDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.value()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)

        elif waveform == "RAMP":
            line_edit_frequency = DelayedDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.value()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = DelayedDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.value()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = DelayedDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.value()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = DelayedDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.value()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)
            line_edit_symmetry = DelayedDoubleSpinBox()
            line_edit_symmetry.setDecimals(2)
            line_edit_symmetry.setRange(0, 100)
            line_edit_symmetry.setValue(self._device.get_ramp_symmetry(channel))
            line_edit_symmetry.textChanged.connect(  # NOQA
                lambda: self._device.set_ramp_symmetry(channel, line_edit_symmetry.value()))
            layout_new.addRow(QLabel("Symmetry / %"), line_edit_symmetry)

        elif waveform == "PULS":
            line_edit_frequency = DelayedDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.value()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = DelayedDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.value()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = DelayedDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.value()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = DelayedDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.value()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)
            line_edit_width = DelayedDoubleSpinBox()
            line_edit_width.setDecimals(9)
            line_edit_width.setRange(5e-9, 1e6)
            line_edit_width.setValue(self._device.get_pulse_width(channel))
            line_edit_width.textChanged.connect(lambda: self._device.set_pulse_width(channel, line_edit_width.value()))  # NOQA
            layout_new.addRow(QLabel("Width / s"), line_edit_width)
            line_edit_lead_edge = DelayedDoubleSpinBox()
            line_edit_lead_edge.setDecimals(9)
            line_edit_lead_edge.setRange(3e-9, 1e6)
            line_edit_lead_edge.setValue(self._device.get_pulse_lead_edge(channel))
            line_edit_lead_edge.textChanged.connect(  # NOQA
                lambda: self._device.set_pulse_lead_edge(channel, line_edit_lead_edge.value()))
            layout_new.addRow(QLabel("Lead Edge / s"), line_edit_lead_edge)
            line_edit_trail_edge = DelayedDoubleSpinBox()
            line_edit_trail_edge.setDecimals(9)
            line_edit_trail_edge.setRange(3e-9, 1e6)
            line_edit_trail_edge.setValue(self._device.get_pulse_trail_edge(channel))
            line_edit_trail_edge.textChanged.connect(  # NOQA
                lambda: self._device.set_pulse_trail_edge(channel, line_edit_trail_edge.value()))
            layout_new.addRow(QLabel("Trail Edge / s"), line_edit_trail_edge)

        elif waveform == "PRBS":
            layout_new.addRow(QLabel("Not Implemented"))

        elif waveform == "NOIS":
            layout_new.addRow(QLabel("Not Implemented"))

        elif waveform == "ARB":
            layout_new.addRow(QLabel("Not Implemented"))

        elif waveform == "DC":
            line_edit_offset = DelayedDoubleSpinBox()
            line_edit_offset.setDecimals(4)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(  # NOQA
                lambda: self._device.set_offset(channel, offset=line_edit_offset.value()))
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)

        # Replace old Widget
        if channel == 1:
            self._layout_ch1.replaceWidget(self._widget_form_ch1, widget_new)
            self._widget_form_ch1.hide()
            self._widget_form_ch1.destroy()
            self._widget_form_ch1 = widget_new
        else:
            self._layout_ch2.replaceWidget(self._widget_form_ch2, widget_new)
            self._widget_form_ch2.hide()
            self._widget_form_ch2.destroy()
            self._widget_form_ch2 = widget_new

    @pyqtSlot()
    def _update_error_label(self):
        """
        Update Error in Status Bar
        """
        err = self._device.get_error()
        if err is not None:
            self._last_error = err
            self._status_bar_label.setText(f"\u26A0 Device Error: '{self._last_error}'")

    @pyqtSlot()
    def closeEvent(self, event):
        """
        Stop Timer when Window is closed
        """
        if hasattr(self, "_timer"):
            self._timer.stop()
        event.accept()
