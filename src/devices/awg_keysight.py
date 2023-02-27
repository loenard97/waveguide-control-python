"""
Keysight Arbitrary Waveform Generator
"""

from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QFormLayout, QDoubleSpinBox, QVBoxLayout, \
    QMainWindow, QFrame

from src.devices.main_device import EthernetDevice
from src.static_gui_elements.toggle_button import ToggleButton


class AWGKeysight(EthernetDevice):
    """
    Arbitrary Waveform Generator by Keysight
    """

    def __init__(self, name="AWG Keysight", address="", settings=None):
        super().__init__(name, address, settings)
        if settings is None:
            self.settings = {}
        else:
            self.settings = settings

        # Channel Names
        self.channel = ["1", "2"]
        if "Channel" in self.settings:
            for name, value in self.settings["Channel"].items():
                self.channel[name - 1] = value

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

    @staticmethod
    def _convert_decimal_notation(value):
        """
        Convert Decimal Notation
        """
        return value.replace(",", ".")

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
        out = self.read(f"OUTP{channel}?")
        if out == '1':
            return True
        return False

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
        if isinstance(frequency, str):
            frequency = frequency.replace(',', '.')
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
        if isinstance(amplitude, str):
            amplitude = amplitude.replace(',', '.')
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
        if isinstance(offset, str):
            offset = offset.replace(',', '.')
        self.write(f"SOUR{channel}:VOLT:OFFS {offset}")

    def get_offset(self, channel) -> float:
        """
        Get Offset in V
        """
        return float(self.read(f"SOUR{channel}:VOLT:OFFS?"))

    def set_phase(self, channel, phase):
        """
        Set Phase in °
        """
        if isinstance(phase, str):
            phase = phase.replace(',', '.')
        self.write(f"SOUR{channel}:PHAS {phase}")

    def get_phase(self, channel) -> float:
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

    # TODO: rename
    # def set_burst_mode(self, channel, mode):
    #     """
    #     Set Burst Mode TRIG | GAT
    #     """
    #     if mode.upper() in ["TRIG", "GAT"]:
    #         self.write(f"SOUR{channel}:BURS:MODE {mode.upper()}")
    #     else:
    #         raise ValueError("Burst Mode has to be 'TRIG' or 'GAT'")

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

    def set_burst_mode(self, channel=1, state=False, number_cycles=1, mode="TRIG"):
        """
        Set Burst Mode
        """
        channel = self._convert_channel(channel)
        if state:
            self.write(f"SOUR{channel}:BURS:STAT ON")                   # turn on
            self.write(f"SOUR{channel}:BURS:NCYC {number_cycles}")      # number of cycles
            self.write(f"SOUR{channel}:BURS:MODE {mode}")               # trigger mode
        else:
            self.write(f"SOUR{channel}:BURS:STAT OFF")

    # Waveforms
    def set_constant_dc(self, channel=1, offset=0.0):
        """
        Set constant DC Signal
        :param int | str channel: Channel Name
        :param float offset: Offset in V
        """
        channel = self._convert_channel(channel)
        self.write(f"SOUR{channel}:APPL:DC DEF, DEF, {offset}V")

    def set_constant_ttl(self, channel=1, state=False):
        """
        Set constant TTL Signal
        :param int | str channel: Channel Name
        :param bool state: TTL State (True = 3.3V | False = 0.0V)
        """
        channel = self._convert_channel(channel)
        self.write(f"SOUR{channel}:APPL:DC DEF, DEF, {3.3 if state else 0.0}V")

    def set_function_pulse(self, channel: int, frequency, amplitude, offset, duty_cycle):
        """
        Set Pulse function
        :param channel:      (1 | 2) Channel
        :param frequency:    Frequency in Hz
        :param amplitude:    Amplitude in V
        :param offset:     Amplitude Offset in V
        :param duty_cycle:    Duty Cycle in %
        :return:        status code
        """
        if isinstance(frequency, str):
            frequency = frequency.replace(',', '.')
        if isinstance(amplitude, str):
            amplitude = amplitude.replace(',', '.')
        if isinstance(offset, str):
            offset = offset.replace(',', '.')
        if isinstance(duty_cycle, str):
            duty_cycle = duty_cycle.replace(',', '.')

        self.write(f"SOUR{channel}:FUNC PULS")                       # set function to pulse
        self.write(f"SOUR{channel}:FREQ {frequency}")                     # set frequency in Hz
        self.write(f"SOUR{channel}:VOLT {amplitude}")                     # set amplitude in V
        self.write(f"SOUR{channel}:VOLT:OFFS {offset}")                  # set amplitude offset in V
        self.write(f"SOUR{channel}:FUNC:PULS:DCYC {duty_cycle}")           # duty cycle
        self.write(f"SOUR{channel}:FUNC:PULS:HOLD DCYC")              # hold duty cycle constant
        # self.write(f"SOUR{ch}:FUNC:PULS:PER 1")               # period in s
        # self.write(f"SOUR{ch}:FUNC:PULS:TRAN:BOTH 20e-9")     # flank length in s
        # self.write(f"OUTP{ch} ON")                            # switch output 2 on

    def set_function_arbitrary(self, channel, voltage_high, voltage_low, sequence, n_samples=1000):
        """
        Set Arbitrary Function
        :param int | str channel: Channel Name
        :param float voltage_high: Voltage High in V
        :param float voltage_low: Voltage Low in V
        :param sequence: Pulse Sequence
        :param float n_samples: Number of Samples
        """
        channel = self._convert_channel(channel)
        if isinstance(voltage_high, str):
            voltage_high = voltage_high.replace(',', '.')
        if isinstance(voltage_low, str):
            voltage_low = voltage_low.replace(',', '.')
        if isinstance(n_samples, str):
            n_samples = n_samples.replace(',', '.')
        arb_str, sample_rate = sequence.get_sequence_keysight_awg(n_samples)

        self.write(f"SOUR{channel}:DATA:VOL:CLE")                       # clear memory
        self.write(f"SOUR{channel}:DATA:ARB myArb, {arb_str}")          # set function
        self.write(f"SOUR{channel}:FUNC:ARB myArb")                     # select to arb waveform
        self.write(f"SOUR{channel}:FUNC ARB")                           # set to arb
        self.write(f"SOUR{channel}:FUNC:ARB:FILT off")                  # set filter to off
        self.write(f"SOUR{channel}:FUNC:ARB:SRAT {sample_rate}")          # set samplerate = (samples / period length)
        self.write(f"SOUR{channel}:VOLT:HIGH {voltage_high}")           # set voltage high
        self.write(f"SOUR{channel}:VOLT:LOW {voltage_low}")             # set voltage low

    def gui_open(self):
        """
        Open GUI
        """
        self.app = WaveformKeysightDualWindow(self)


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
        self._button_output_ch1.clicked.connect(
            lambda: self._device.set_output(channel=1, state=self._button_output_ch1.isChecked())
        )
        self._button_output_ch2 = ToggleButton(state=self._device.get_output(channel=2))
        self._button_output_ch2.clicked.connect(
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
            line_edit_frequency = QDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.text()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = QDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.text()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = QDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.text()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = QDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.text()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)

        elif waveform == "SQU":
            line_edit_frequency = QDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.text()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = QDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.text()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = QDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.text()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = QDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.text()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)
            line_edit_duty_cycle = QDoubleSpinBox()
            line_edit_duty_cycle.setDecimals(2)
            line_edit_duty_cycle.setRange(0.05, 99.95)
            line_edit_duty_cycle.setValue(self._device.get_square_duty_cycle(channel))
            line_edit_duty_cycle.textChanged.connect(  # NOQA
                lambda: self._device.set_square_duty_cycle(channel, line_edit_duty_cycle.text()))
            layout_new.addRow(QLabel("Duty Cycle / %"), line_edit_duty_cycle)

        elif waveform == "TRI":
            line_edit_frequency = QDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.text()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = QDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.text()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = QDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.text()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = QDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.text()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)

        elif waveform == "RAMP":
            line_edit_frequency = QDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.text()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = QDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.text()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = QDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.text()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = QDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.text()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)
            line_edit_symmetry = QDoubleSpinBox()
            line_edit_symmetry.setDecimals(2)
            line_edit_symmetry.setRange(0, 100)
            line_edit_symmetry.setValue(self._device.get_ramp_symmetry(channel))
            line_edit_symmetry.textChanged.connect(  # NOQA
                lambda: self._device.set_ramp_symmetry(channel, line_edit_symmetry.text()))
            layout_new.addRow(QLabel("Symmetry / %"), line_edit_symmetry)

        elif waveform == "PULS":
            line_edit_frequency = QDoubleSpinBox()
            line_edit_frequency.setDecimals(6)
            line_edit_frequency.setRange(1e-6, 30e6)
            line_edit_frequency.setValue(self._device.get_frequency(channel))
            line_edit_frequency.textChanged.connect(  # NOQA
                lambda: self._device.set_frequency(channel, line_edit_frequency.text()))
            layout_new.addRow(QLabel("Frequency / Hz"), line_edit_frequency)
            line_edit_amplitude = QDoubleSpinBox()
            line_edit_amplitude.setDecimals(3)
            line_edit_amplitude.setRange(1e-3, 5)
            line_edit_amplitude.setValue(self._device.get_amplitude(channel))
            line_edit_amplitude.textChanged.connect(  # NOQA
                lambda: self._device.set_amplitude(channel, line_edit_amplitude.text()))
            layout_new.addRow(QLabel("Amplitude / V"), line_edit_amplitude)
            line_edit_offset = QDoubleSpinBox()
            line_edit_offset.setDecimals(3)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(lambda: self._device.set_offset(channel, line_edit_offset.text()))  # NOQA
            layout_new.addRow(QLabel("Offset / V"), line_edit_offset)
            line_edit_phase = QDoubleSpinBox()
            line_edit_phase.setDecimals(3)
            line_edit_phase.setRange(0, 360)
            line_edit_phase.setValue(self._device.get_phase(channel))
            line_edit_phase.textChanged.connect(lambda: self._device.set_phase(channel, line_edit_phase.text()))  # NOQA
            layout_new.addRow(QLabel("Phase / °"), line_edit_phase)
            line_edit_width = QDoubleSpinBox()
            line_edit_width.setDecimals(9)
            line_edit_width.setRange(5e-9, 1e6)
            line_edit_width.setValue(self._device.get_pulse_width(channel))
            line_edit_width.textChanged.connect(lambda: self._device.set_pulse_width(channel, line_edit_width.text()))  # NOQA
            layout_new.addRow(QLabel("Width / s"), line_edit_width)
            line_edit_lead_edge = QDoubleSpinBox()
            line_edit_lead_edge.setDecimals(9)
            line_edit_lead_edge.setRange(3e-9, 1e6)
            line_edit_lead_edge.setValue(self._device.get_pulse_lead_edge(channel))
            line_edit_lead_edge.textChanged.connect(  # NOQA
                lambda: self._device.set_pulse_lead_edge(channel, line_edit_lead_edge.text()))
            layout_new.addRow(QLabel("Lead Edge / s"), line_edit_lead_edge)
            line_edit_trail_edge = QDoubleSpinBox()
            line_edit_trail_edge.setDecimals(9)
            line_edit_trail_edge.setRange(3e-9, 1e6)
            line_edit_trail_edge.setValue(self._device.get_pulse_trail_edge(channel))
            line_edit_trail_edge.textChanged.connect(  # NOQA
                lambda: self._device.set_pulse_trail_edge(channel, line_edit_trail_edge.text()))
            layout_new.addRow(QLabel("Trail Edge / s"), line_edit_trail_edge)

        elif waveform == "PRBS":
            layout_new.addRow(QLabel("Not Implemented"))

        elif waveform == "NOIS":
            layout_new.addRow(QLabel("Not Implemented"))

        elif waveform == "ARB":
            layout_new.addRow(QLabel("Not Implemented"))

        elif waveform == "DC":
            line_edit_offset = QDoubleSpinBox()
            line_edit_offset.setDecimals(4)
            line_edit_offset.setRange(-5, 5)
            line_edit_offset.setValue(self._device.get_offset(channel))
            line_edit_offset.textChanged.connect(  # NOQA
                lambda: self._device.set_offset(channel, offset=line_edit_offset.text()))
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
