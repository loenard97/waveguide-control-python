"""
SwabianInstruments Pulsestreamer 8/2

Website: https://www.swabianinstruments.com/pulse-streamer-8-2/
"""

import os
import logging
import contextlib
from pulsestreamer import PulseStreamer, OutputState, ClockSource

from PyQt6.QtWidgets import QLabel, QWidget, QMainWindow, QFormLayout, QHBoxLayout, QFrame

from src.static_functions.wait import event_loop_interrupt
from src.static_gui_elements.toggle_button import ToggleButton


class PulsestreamerSwabian:
    """
    PulseStreamer Series by Swabian Instruments
    """

    def __init__(self, name="Pulse Streamer", address=None, settings=None):
        # Variables
        self.name = name
        self.address = address
        if settings is None:
            self.settings = {}
        else:
            self.settings = settings
        self.app, self._ser, self._sequence = None, None, None
        self._output_state = OutputState([])
        self._clock_state = []

        # Connect
        with open(os.devnull, 'w') as devnull, contextlib.redirect_stdout(devnull):     # ignore stdout
            self._ser = PulseStreamer(self.address)
        self._sequence = self._ser.createSequence()
        self.reset()

        # Apply Settings
        self.digital_channel = ["D0", "D1", "D2", "D3", "D4", "D5", "D6", "D7"]
        if "Digital Channel" in self.settings:
            for name, value in self.settings["Digital Channel"].items():
                self.digital_channel[name] = value
        if "Clock Out Channel" in self.settings and self.settings["Clock Out Channel"]:
            self.set_function_clock(channel=self.settings["Clock Channel"])
        if "Clock In" in self.settings and self.settings["Clock In"]:
            self.set_external_clock(self.settings["Clock In"])

    def disconnect(self):
        """
        Disconnect from Device
        """
        self.reset()

    def reset(self):
        """
        Reset to Default Settings
        """
        self._ser.reset()
        self._clock_state = []
        self._output_state = OutputState([])
        self._ser.constant(self._output_state)
        logging.info(f"{self.name}: Reset.")

    def soft_reset(self):
        """
        Reset Device but keep initial Settings
        """
        self.reset()

    def reboot(self):
        """
        Reboot
        """
        self._ser.reboot()
        logging.info(f"{self.name}: Reboot.")

    def is_streaming(self) -> bool:
        """
        Get current streaming State
        :return: True if currently streaming
        """
        return self._ser.isStreaming()

    def wait_until_ready(self, rate=0.5):
        """
        Wait until current Stream is done
        :param int rate: Polling Rate in s
        """
        while self.is_streaming():
            event_loop_interrupt(rate)

    def _convert_channel(self, channel):
        """
        Convert Channel String to int
        :param int | str channel: Channel Number or Name
        """
        if isinstance(channel, int):
            return channel
        if isinstance(channel, str):
            return self.digital_channel.index(channel)
        raise ValueError("Channel has to be int or str")

    def set_function_clock(self, channel):
        """
        Set Channel to 125MHz Clock Signal
        :param int | list channel: Channel 0 to 7
        """
        if isinstance(channel, str):
            channel_list = []
            for c in channel.split(','):
                channel_list.append(int(c.strip()))
            self._ser.setSquareWave125MHz(channels=channel_list)
        else:
            if channel not in self._clock_state:
                self._clock_state.append(channel)
                self._clock_state.sort()
            self._ser.setSquareWave125MHz(channels=self._clock_state)

    def get_function_clock(self) -> list:
        """
        Get 125MHz Clock Channel
        :return: List of all Channels that output a 125MHz Clock Signal
        """
        return self._clock_state

    def set_external_clock(self, clock):
        """
        Set External Clock Signal
        :param str clock: INT | 10MHz | 125MHz
        """
        if clock == "10MHz":
            self._ser.selectClock(ClockSource.EXT_10MHZ)
        elif clock == "125MHz":
            self._ser.selectClock(ClockSource.EXT_125MHZ)
        else:
            self._ser.selectClock(ClockSource.INTERNAL)

    def get_external_clock(self) -> str:
        """
        Get External Clock Signal
        :return: INT | 10MHz | 125MHz
        """
        clock = self._ser.getClock()
        if clock == ClockSource.EXT_10MHZ:
            return "10MHz"
        if clock == ClockSource.EXT_125MHZ:
            return "125MHz"
        return "INT"

    def set_sequence(self, channel, sequence):
        """
        Set Pulse Sequence for Channel
        :param int | str channel: Channel Number or Name
        :param list sequence: Pulse Sequence
        """
        channel = self._convert_channel(channel)
        self._sequence.setDigital(channel=channel, channel_sequence=sequence)
        logging.info(f"{self.name}: Set Sequence.")

    def get_sequence_length(self) -> int:
        """
        Get Duration of Sequence in s
        """
        return self._sequence.getDuration()

    def set_constant_ttl(self, channel, state):
        """
        Set Constant TTL Output
        :param int | str channel: Channel Name or Number
        :param bool state: TTL State
        """
        channel = self._convert_channel(channel)
        output_list = self.get_output_state()
        output_list[channel] = int(state)
        channels = [i for i, e in enumerate(output_list) if e > 0]  # list of channels that are turned on
        self._output_state = OutputState(channels)
        self._ser.constant(self._output_state)
        logging.info(f"{self.name}: Set Channel '{channel}' to '{state}'.")

    def get_output_state(self, channel=None) -> int | list:
        """
        Get current State of Digital Outputs
        :param int channel: None or Channel Name or Number
        :return: List of all Output States or int of Output State of specific channel
        """
        # Ignore this mess please, I swear it's supposed to be like this
        if channel is None:
            return [int(i) for i in str(bin(self._output_state.getData()[0]))[2:].zfill(8)[::-1]]
        else:
            return [int(i) for i in str(bin(self._output_state.getData()[0]))[2:].zfill(8)[::-1]][channel]

    def set_function_arbitrary(self, channel, sequence):
        """
        Set Arbitrary Function
        :param int | str channel: Channel Name or Number
        :param sequence: Pulse Sequence
        """
        channel = self._convert_channel(channel)
        if isinstance(sequence, list):
            self._sequence.setDigital(channel=channel, channel_sequence=sequence)
        else:
            self._sequence.setDigital(channel=channel, channel_sequence=sequence.get_sequence_pulse_streamer())
        logging.info(f"{self.name}: Set Sequence with Duration {self._sequence.getDuration() * 1E-9}s")

    def stream(self, repetitions=1, blocking=True):
        """
        Start streaming Sequence
        :param float repetitions: Number of Repetitions
        :param bool blocking: Block until Stream is done
        """
        self._ser.stream(seq=self._sequence, n_runs=int(repetitions))
        logging.info(f"{self.name}: Start Stream.")
        if blocking:
            self.wait_until_ready()
            logging.info(f"{self.name}: Stream finished.")

    def get_channel_str(self, channel: int):
        """
        Return String representation of Channel
        :param int channel:
        """
        if self.settings["Digital Channel"] and channel in self.settings["Digital Channel"]:
            return self.settings["Digital Channel"][channel]
        return f"D{channel}"

    def get_channel_int(self, channel: str):
        pass

    def gui_open(self):
        """
        Open GUI
        """
        self.app = SwabianPulseStreamerWindow(self)


class SwabianPulseStreamerWindow(QMainWindow):

    def __init__(self, device: PulsestreamerSwabian):
        super().__init__()
        # Variables
        self._device = device

        # Appearance
        self.setWindowTitle(f"{self._device.name}")
        self.setGeometry(900, 500, 300, 0)

        # Channel Buttons
        layout_channel_buttons = QFormLayout()
        layout_channel_buttons.addRow(QLabel("<b>Channel</b>"), QLabel("<b>State</b>"))
        button_d0 = ToggleButton(state=self._device.get_output_state(channel=0))
        button_d0.clicked.connect(
            lambda: self._device.set_constant_ttl(channel=0, state=button_d0.isChecked()))
        layout_channel_buttons.addRow(QLabel(self._device.get_channel_str(0)), button_d0)
        button_d1 = ToggleButton(state=self._device.get_output_state(channel=1))
        button_d1.clicked.connect(
            lambda: self._device.set_constant_ttl(channel=1, state=button_d1.isChecked()))
        layout_channel_buttons.addRow(QLabel(self._device.get_channel_str(1)), button_d1)
        button_d2 = ToggleButton(state=self._device.get_output_state(channel=2))
        button_d2.clicked.connect(
            lambda: self._device.set_constant_ttl(channel=2, state=button_d2.isChecked()))
        layout_channel_buttons.addRow(QLabel(self._device.get_channel_str(2)), button_d2)
        button_d3 = ToggleButton(state=self._device.get_output_state(channel=3))
        button_d3.clicked.connect(
            lambda: self._device.set_constant_ttl(channel=3, state=button_d3.isChecked()))
        layout_channel_buttons.addRow(QLabel(self._device.get_channel_str(3)), button_d3)
        button_d4 = ToggleButton(state=self._device.get_output_state(channel=4))
        button_d4.clicked.connect(
            lambda: self._device.set_constant_ttl(channel=4, state=button_d4.isChecked()))
        layout_channel_buttons.addRow(QLabel(self._device.get_channel_str(4)), button_d4)
        button_d5 = ToggleButton(state=self._device.get_output_state(channel=5))
        button_d5.clicked.connect(
            lambda: self._device.set_constant_ttl(channel=5, state=button_d5.isChecked()))
        layout_channel_buttons.addRow(QLabel(self._device.get_channel_str(5)), button_d5)
        button_d6 = ToggleButton(state=self._device.get_output_state(channel=6))
        button_d6.clicked.connect(
            lambda: self._device.set_constant_ttl(channel=6, state=button_d6.isChecked()))
        layout_channel_buttons.addRow(QLabel(self._device.get_channel_str(6)), button_d6)
        button_d7 = ToggleButton(state=self._device.get_output_state(channel=7))
        button_d7.clicked.connect(
            lambda: self._device.set_constant_ttl(channel=7, state=button_d7.isChecked()))
        layout_channel_buttons.addRow(QLabel(self._device.get_channel_str(7)), button_d7)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        # Info
        layout_info = QFormLayout()
        layout_info.addRow(QLabel("<b>Device Info</b>"))
        layout_info.addRow("125MHz Clock Channels", QLabel(str(self._device.get_function_clock())))
        layout_info.addRow("External Clock", QLabel(str(self._device.get_external_clock())))

        central_layout = QHBoxLayout()
        central_layout.addLayout(layout_channel_buttons)
        central_layout.addWidget(line)
        central_layout.addLayout(layout_info)
        central_widget = QWidget()
        central_widget.setLayout(central_layout)
        self.setCentralWidget(central_widget)

        self.show()
