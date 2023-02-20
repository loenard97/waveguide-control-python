"""
Stanford Pulse Streamer
"""

from PyQt6.QtCore import pyqtSlot, QTimer
from PyQt6.QtWidgets import QWidget, QLabel, QComboBox, QDoubleSpinBox, QMainWindow, QGridLayout

from src.devices.device_main import EthernetDevice


class StanfordPulseStreamer(EthernetDevice):

    TERMINATION_READ = 2

    def get_identification(self):
        """
        Get Identification String
        """
        return self.read("*IDN?")

    def calibrate(self):
        """
        Run Auto Calibration and return success
        """
        return self.read("*CAL?")

    def get_error(self):
        """
        Get Last Error
        """
        return self.read("LERR?")

    def clear(self):
        """
        clear register
        """
        self.write("*CLS")

    def reset(self):
        """
        reset to default settings
        """
        self.write("*RST")

    def trigger(self):
        """
        trigger a pulse sequence
        """
        self.write("*TRG")
    
    def get_operation_complete(self):
        """
        Returns 1 if all operations are complete
        """
        return self.read("*OPC?")

    def get_status_register(self):
        """
        0 TRIG
        1 RATE
        2 END_OF_DELAY
        3 END_OF_BURST
        4 INHIBIT
        5 ABORT_DELAY
        6 PLL_UNLOCK
        7 RB_UNLOCK
        """
        return self.read("INSR?")

    def get_status_byte(self):
        return self.read("*STB?")

    def set_amplitude(self, channel, amplitude):
        """
        Set Amplitude in V
        """
        if isinstance(amplitude, str):
            amplitude = amplitude.replace(',', '.')
        self.write(f"LAMP{channel},{amplitude}")

    def get_amplitude(self, channel):
        """
        Get Amplitude in V
        """
        return float(self.read(f"LAMP?{channel}"))

    def set_offset(self, channel, offset):
        """
        Set Offset in V
        """
        if isinstance(offset, str):
            offset = offset.replace(',', '.')
        self.write(f"LOFF{channel},{offset}")

    def get_offset(self, channel):
        """
        Get Offset in V
        """
        return float(self.read(f"LOFF?{channel}"))

    def set_time_start(self, channel, time_start):
        """
        Set Start Time in s
        """
        if isinstance(time_start, str):
            time_start = time_start.replace(',', '.')
        self.write(f"DLAY{2*channel},0,{time_start}")

    def get_time_start(self, channel):
        """
        Get Start Time in s
        """
        return float(self.read(f"DLAY?{2*channel}")[2:])

    def set_time_stop(self, channel, time_stop):
        """
        Set Stop Time in s
        """
        if isinstance(time_stop, str):
            time_stop = time_stop.replace(',', '.')
        self.write(f"DLAY{2*channel+1},0,{time_stop}")

    def get_time_stop(self, channel):
        """
        Get Stop Time in s
        """
        return float(self.read(f"DLAY?{2*channel+1}")[2:])

    def set_polarity(self, channel, polarity):
        """
        Set Polarity 1 positive | 0 negative
        """
        if polarity:
            self.write(f"LPOL{channel},0")
        else:
            self.write(f"LPOL{channel},1")

    def get_polarity(self, channel):
        """
        Get Polarity 1 positive | 0 negative
        """
        return int(self.read(f"LPOL?{channel}"))

    def set_burst_mode(self, state, number_cycles=0, period=0.0):
        """
        set burst mode
        :param state:            (True | False) turn burst mode on|off
        :param number_cycles:   number of cycles to repeat
        :param period:          length of sequence in s
        """
        if state:
            self.write(f"BURM 1")
            self.write(f"BURC {int(number_cycles)}")
            self.write(f"BURP {period}")
        else:
            self.write(f"BURM 0")

    def set_pulse(self, channel=1, amplitude=1.0, offset=0.0, t_start=0.0, t_stop=0.1, inverted=False):
        """
        set rectangle pulse
        :param channel      channel [1,4]
        :param amplitude    in V
        :param offset       in V
        :param t_start      time of rising edge in s
        :param t_stop       time of falling edge in s
        :param inverted     invert Signal if True
        """
        self.write(f"LAMP {channel},{amplitude}")
        self.write(f"LOFF {channel},{offset}")
        self.write(f"DLAY {2*channel},0,{t_start}")
        self.write(f"DLAY {2*channel+1},0,{t_stop}")
        if inverted:
            self.write(f"LPOL {channel},0")
        else:
            self.write(f"LPOL {channel},1")

    def gui_open(self):
        """
        Open GUI
        """
        self.app = StanfordPulseStreamerWindow(self)


class StanfordPulseStreamerWindow(QMainWindow):

    def __init__(self, device: StanfordPulseStreamer):
        super().__init__()
        # Variables
        self._device = device

        # Appearance
        self.setWindowTitle(f"{self._device.name}")
        self.setGeometry(900, 500, 0, 0)

        # Total Layout
        widget = QWidget()
        layout = QGridLayout()

        # Label
        layout.addWidget(QLabel("Start / us"), 1, 0)
        layout.addWidget(QLabel("Stop / us"), 2, 0)
        layout.addWidget(QLabel("Offset / V"), 3, 0)
        layout.addWidget(QLabel("Amplitude / V"), 4, 0)
        layout.addWidget(QLabel("Polarity"), 5, 0)

        # Channel 1
        layout.addWidget(QLabel("Channel 1"), 0, 1)
        line_edit_ch1_start = QDoubleSpinBox()
        line_edit_ch1_start.setDecimals(6)
        line_edit_ch1_start.setRange(0, 1E6)
        line_edit_ch1_start.setValue(float(self._device.get_time_start(channel=1))*1E-6)
        line_edit_ch1_start.textChanged.connect(
            lambda: self._device.set_time_start(channel=1, time_start=float(line_edit_ch1_start.text())*1E-6)
        )
        layout.addWidget(line_edit_ch1_start, 1, 1)
        line_edit_ch1_stop = QDoubleSpinBox()
        line_edit_ch1_stop.setDecimals(6)
        line_edit_ch1_stop.setRange(0, 1E6)
        line_edit_ch1_stop.setValue(float(self._device.get_time_stop(channel=1))*1E-6)
        line_edit_ch1_stop.textChanged.connect(
            lambda: self._device.set_time_stop(channel=1, time_stop=float(line_edit_ch1_stop.text())*1E-6)
        )
        layout.addWidget(line_edit_ch1_stop, 2, 1)
        line_edit_ch1_amplitude = QDoubleSpinBox()
        line_edit_ch1_amplitude.setDecimals(2)
        line_edit_ch1_amplitude.setRange(0, 5)
        line_edit_ch1_amplitude.setValue(self._device.get_amplitude(channel=1))
        line_edit_ch1_amplitude.textChanged.connect(
            lambda: self._device.set_amplitude(channel=1, amplitude=line_edit_ch1_amplitude.text())
        )
        layout.addWidget(line_edit_ch1_amplitude, 3, 1)
        line_edit_ch1_offset = QDoubleSpinBox()
        line_edit_ch1_offset.setDecimals(3)
        line_edit_ch1_offset.setRange(0, 5)
        line_edit_ch1_offset.setValue(self._device.get_offset(channel=1))
        line_edit_ch1_offset.textChanged.connect(
            lambda: self._device.set_offset(channel=1, offset=line_edit_ch1_offset.text())
        )
        layout.addWidget(line_edit_ch1_offset, 4, 1)
        line_edit_ch1_polarity = QComboBox()
        line_edit_ch1_polarity.addItems(["Negative", "Positive"])
        line_edit_ch1_polarity.setCurrentIndex(self._device.get_polarity(channel=1))
        line_edit_ch1_polarity.currentIndexChanged.connect(
            lambda: self._device.set_polarity(channel=1, polarity=line_edit_ch1_polarity.currentIndex())
        )
        layout.addWidget(line_edit_ch1_polarity, 5, 1)

        # Channel 2
        layout.addWidget(QLabel("Channel 2"), 0, 2)
        line_edit_ch2_start = QDoubleSpinBox()
        line_edit_ch2_start.setDecimals(6)
        line_edit_ch2_start.setRange(0, 1E6)
        line_edit_ch2_start.setValue(float(self._device.get_time_start(channel=2))*1E-6)
        line_edit_ch2_start.textChanged.connect(
            lambda: self._device.set_time_start(channel=2, time_start=float(line_edit_ch2_start.text())*1E-6)
        )
        layout.addWidget(line_edit_ch2_start, 1, 2)
        line_edit_ch2_stop = QDoubleSpinBox()
        line_edit_ch2_stop.setDecimals(6)
        line_edit_ch2_stop.setRange(0, 1E6)
        line_edit_ch2_stop.setValue(float(self._device.get_time_stop(channel=2))*1E-6)
        line_edit_ch2_stop.textChanged.connect(
            lambda: self._device.set_time_stop(channel=2, time_stop=float(line_edit_ch2_stop.text())*1E-6)
        )
        layout.addWidget(line_edit_ch2_stop, 2, 2)
        line_edit_ch2_amplitude = QDoubleSpinBox()
        line_edit_ch2_amplitude.setDecimals(2)
        line_edit_ch2_amplitude.setRange(0, 5)
        line_edit_ch2_amplitude.setValue(self._device.get_amplitude(channel=2))
        line_edit_ch2_amplitude.textChanged.connect(
            lambda: self._device.set_amplitude(channel=2, amplitude=line_edit_ch2_amplitude.text())
        )
        layout.addWidget(line_edit_ch2_amplitude, 3, 2)
        line_edit_ch2_offset = QDoubleSpinBox()
        line_edit_ch2_offset.setDecimals(3)
        line_edit_ch2_offset.setRange(0, 5)
        line_edit_ch2_offset.setValue(self._device.get_offset(channel=2))
        line_edit_ch2_offset.textChanged.connect(
            lambda: self._device.set_offset(channel=2, offset=line_edit_ch2_offset.text())
        )
        layout.addWidget(line_edit_ch2_offset, 4, 2)
        line_edit_ch2_polarity = QComboBox()
        line_edit_ch2_polarity.addItems(["Negative", "Positive"])
        line_edit_ch2_polarity.setCurrentIndex(self._device.get_polarity(channel=2))
        line_edit_ch2_polarity.currentIndexChanged.connect(
            lambda: self._device.set_polarity(channel=2, polarity=line_edit_ch2_polarity.currentIndex())
        )
        layout.addWidget(line_edit_ch2_polarity, 5, 2)

        # Channel 3
        layout.addWidget(QLabel("Channel 3"), 0, 3)
        line_edit_ch3_start = QDoubleSpinBox()
        line_edit_ch3_start.setDecimals(6)
        line_edit_ch3_start.setRange(0, 1E6)
        line_edit_ch3_start.setValue(float(self._device.get_time_start(channel=3))*1E-6)
        line_edit_ch3_start.textChanged.connect(
            lambda: self._device.set_time_start(channel=3, time_start=float(line_edit_ch3_start.text())*1E-6)
        )
        layout.addWidget(line_edit_ch3_start, 1, 3)
        line_edit_ch3_stop = QDoubleSpinBox()
        line_edit_ch3_stop.setDecimals(6)
        line_edit_ch3_stop.setRange(0, 1E6)
        line_edit_ch3_stop.setValue(float(self._device.get_time_stop(channel=3))*1E-6)
        line_edit_ch3_stop.textChanged.connect(
            lambda: self._device.set_time_stop(channel=3, time_stop=float(line_edit_ch3_stop.text())*1E-6)
        )
        layout.addWidget(line_edit_ch3_stop, 2, 3)
        line_edit_ch3_amplitude = QDoubleSpinBox()
        line_edit_ch3_amplitude.setDecimals(2)
        line_edit_ch3_amplitude.setRange(0, 5)
        line_edit_ch3_amplitude.setValue(self._device.get_amplitude(channel=3))
        line_edit_ch3_amplitude.textChanged.connect(
            lambda: self._device.set_amplitude(channel=3, amplitude=line_edit_ch3_amplitude.text())
        )
        layout.addWidget(line_edit_ch3_amplitude, 3, 3)
        line_edit_ch3_offset = QDoubleSpinBox()
        line_edit_ch3_offset.setDecimals(3)
        line_edit_ch3_offset.setRange(0, 5)
        line_edit_ch3_offset.setValue(self._device.get_offset(channel=3))
        line_edit_ch3_offset.textChanged.connect(
            lambda: self._device.set_offset(channel=3, offset=line_edit_ch3_offset.text())
        )
        layout.addWidget(line_edit_ch3_offset, 4, 3)
        line_edit_ch3_polarity = QComboBox()
        line_edit_ch3_polarity.addItems(["Negative", "Positive"])
        line_edit_ch3_polarity.setCurrentIndex(self._device.get_polarity(channel=3))
        line_edit_ch3_polarity.currentIndexChanged.connect(
            lambda: self._device.set_polarity(channel=3, polarity=line_edit_ch3_polarity.currentIndex())
        )
        layout.addWidget(line_edit_ch3_polarity, 5, 3)

        # Channel 4
        layout.addWidget(QLabel("Channel 4"), 0, 4)
        line_edit_ch4_start = QDoubleSpinBox()
        line_edit_ch4_start.setDecimals(6)
        line_edit_ch4_start.setRange(0, 1E6)
        line_edit_ch4_start.setValue(float(self._device.get_time_start(channel=4))*1E-6)
        line_edit_ch4_start.textChanged.connect(
            lambda: self._device.set_time_start(channel=4, time_start=float(line_edit_ch4_start.text())*1E-6)
        )
        layout.addWidget(line_edit_ch4_start, 1, 4)
        line_edit_ch4_stop = QDoubleSpinBox()
        line_edit_ch4_stop.setDecimals(6)
        line_edit_ch4_stop.setRange(0, 1E6)
        line_edit_ch4_stop.setValue(float(self._device.get_time_stop(channel=4))*1E-6)
        line_edit_ch4_stop.textChanged.connect(
            lambda: self._device.set_time_stop(channel=4, time_stop=float(line_edit_ch4_stop.text())*1E-6)
        )
        layout.addWidget(line_edit_ch4_stop, 2, 4)
        line_edit_ch4_amplitude = QDoubleSpinBox()
        line_edit_ch4_amplitude.setDecimals(2)
        line_edit_ch4_amplitude.setRange(0, 5)
        line_edit_ch4_amplitude.setValue(self._device.get_amplitude(channel=4))
        line_edit_ch4_amplitude.textChanged.connect(
            lambda: self._device.set_amplitude(channel=4, amplitude=line_edit_ch4_amplitude.text())
        )
        layout.addWidget(line_edit_ch4_amplitude, 3, 4)
        line_edit_ch4_offset = QDoubleSpinBox()
        line_edit_ch4_offset.setDecimals(3)
        line_edit_ch4_offset.setRange(0, 5)
        line_edit_ch4_offset.setValue(self._device.get_offset(channel=4))
        line_edit_ch4_offset.textChanged.connect(
            lambda: self._device.set_offset(channel=4, offset=line_edit_ch4_offset.text())
        )
        layout.addWidget(line_edit_ch4_offset, 4, 4)
        line_edit_ch4_polarity = QComboBox()
        line_edit_ch4_polarity.addItems(["Negative", "Positive"])
        line_edit_ch4_polarity.setCurrentIndex(self._device.get_polarity(channel=4))
        line_edit_ch4_polarity.currentIndexChanged.connect(
            lambda: self._device.set_polarity(channel=4, polarity=line_edit_ch4_polarity.currentIndex())
        )
        layout.addWidget(line_edit_ch4_polarity, 5, 4)

        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Status Bar
        self._device.clear()
        self._last_error = self._device.get_error()
        self._status_bar_label = QLabel()
        self.statusBar().addWidget(self._status_bar_label)

        # Timer
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_error_label)
        self._timer.start(2000)

        self.show()

    @pyqtSlot()
    def _update_error_label(self):
        """
        Update Error in Status Bar
        """
        err = self._device.get_error()
        if err != '0':
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
