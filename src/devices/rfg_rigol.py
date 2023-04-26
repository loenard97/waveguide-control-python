"""
Radio Frequency Generator by Rigol
The class is supposed to work with all Rigol RFGs, but was only tested with the following versions:
 - DSG836A

Manuals:
https://beyondmeasure.rigoltech.com/acton/attachment/1579/f-063b/1/-/-/-/-/DSG800%20Programming%20Guide.pdf
"""

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QDoubleSpinBox, QVBoxLayout

from src.measurement.units import MHz
from src.devices.main_device import EthernetDevice
from src.static_gui_elements.toggle_button import ToggleButton


class RFGRigol(EthernetDevice):

    def get_identification(self):
        """
        Get Identification String
        """
        return self.read("*IDN?")

    def get_error(self):
        """
        Get Last Error
        """
        return None

    def reset(self):
        """
        Reset Device Settings
        """
        self.write("*RST")
        self.write("SYST:PRES:TYPE FAC")
        self.write("SYST:PRES")
        self.write("SYST:CLE")

    def set_output(self, state=False):
        """
        Set RF Output
        :param bool state: Output State
        """
        self.write(f"OUTP {'ON' if state else 'OFF'}")

    def get_output(self):
        """
        Get RF Output
        """
        if self.read("OUTP?") == "1":
            return True
        return False

    def set_frequency(self, frequency=1_000_000.0):
        """
        Set RF Frequency
        :param float frequency: Frequency in Hz
        """
        self.write(f"FREQ {frequency}")

    def get_frequency(self):
        """
        Get RF Frequency
        """
        return float(self.read("FREQ?"))

    def set_amplitude(self, amplitude=-60.0):
        """
        Set RF Amplitude
        :param float amplitude: Amplitude in dBm
        """
        self.write(f"LEV {amplitude}")

    def get_amplitude(self):
        """
        Get RF Amplitude
        """
        return float(self.read("LEV?"))

    def set_constant_mw(self, frequency=1_000_000.0, amplitude=-60.0, state=True):
        """
        Set constant MW Output
        :param float frequency: Frequency in Hz
        :param float amplitude: Amplitude in dBm
        :param bool state: Output State
        """
        self.write("SOUR:MOD:STAT OFF")
        self.set_frequency(frequency)
        self.set_amplitude(amplitude)
        self.set_output(state)

    def set_pulse_modulation(self, source="EXT", inverted=False, state=True):
        """
        Set Pulse Modulation
        :param str source: Source INT | EXT
        :param bool inverted: Invert Signal
        :param bool state: Output State
        """
        self.write(f"SOUR:PULM:SOUR {source}")
        self.write(f"SOUR:PULM:POL {'INV' if inverted else 'NORM'}")
        self.write(f"SOUR:PULM:STAT {'ON' if state else 'OFF'}")
        self.write(f"SOUR:MOD:STAT {'ON' if state else 'OFF'}")

    def set_am_modulation(self, source="EXT", state=True):
        """
        Set Amplitude Modulation
        """
        self.write(f"SOUR:AM:SOUR {source}")
        self.write(f"SOUR:AM:STAT {'ON' if state else 'OFF'}")
        self.write(f"SOUR:MOD:STAT {'ON' if state else 'OFF'}")

    def set_iq_modulation(self, frequency=1_000_000.0, amplitude=-60.0, source="EXT", iq_state=True, output_state=True):
        """
        Set IQ Modulation.
        Default settings use external I and Q inputs.
        :param float frequency: Frequency in Hz
        :param float amplitude: Amplitude in dBm
        :param string source: IQ signal source EXT | INT
        :param bool iq_state: IQ state
        :param bool output_state: Output State
        """
        self.set_constant_mw(frequency=frequency, amplitude=amplitude, state=output_state)
        self.write(f"SOUR:IQ:MOD {source}")
        self.write(f"SOUR:IQ:MOD:STAT {'ON' if iq_state else 'OFF'}")
        self.write(f"SOUR:MOD:STAT {'ON' if iq_state else  'OFF'}")

    def set_function_sweep(self, start_frequency, stop_frequency, start_amplitude, stop_amplitude, n_points, dwell_time,
                           state):
        """
        Set Function Frequency and Amplitude Sweep
        :param float start_frequency: Start Frequency in Hz
        :param float stop_frequency: Stop Frequency in Hz
        :param float start_amplitude: Start Amplitude in dBm
        :param float stop_amplitude: Stop Amplitude in dBm
        :param int n_points: Number of Sweep Points
        :param float dwell_time: Dwell Time in s
        :param bool state: RF Output State
        """
        self.reset()
        self.write(f"SWE:STEP:STAR:FREQ {start_frequency}Hz")
        self.write(f"SWE:STEP:STOP:FREQ {stop_frequency}Hz")
        self.write(f"SWE:STEP:STAR:LEV {start_amplitude}")
        self.write(f"SWE:STEP:STOP:LEV {stop_amplitude}")
        self.write(f"SWE:STEP:POIN {n_points}")
        self.write(f"SWE:STEP:DWEL {dwell_time}s")
        self.write("SWE:STAT LEV,FREQ")
        self.set_output(state=state)

    def get_iq_data_list(self):
        return self.read("MMEM:DATA:IQ:LIST?")

    def get_disk_information(self):
        return self.read("MMEM:DISK:INF? D:")

    def set_iq_data(self):
        self.write(":MMEM:DATA:IQ test1,0,2,#9000000011 1,10,11,20")

    def save_settings(self):
        self.write(":MMEM:SAV SET.STA")

    def make_dir(self, dir_name):
        self.write(f":MMEM:MDIR {dir_name}")

    def cat(self, path):
        return self.read(f":MMEM:CAT? {path}")

    def gui_open(self):
        self._app = RFGRigolWindow(self)


class RFGRigolWindow(QWidget):

    def __init__(self, device: RFGRigol):
        super().__init__()

        # Variables
        self._device = device

        # Appearance
        self.setWindowTitle(f"{self._device.name}")
        self.setGeometry(735, 365, 450, 350)

        # Form Layout
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("<b>CW RF Signal</b>"))
        dsb_frequency = QDoubleSpinBox()
        dsb_frequency.setRange(0, 14000)
        dsb_frequency.setValue(self._device.get_frequency())
        dsb_frequency.valueChanged.connect(self._handle_frequency_changed)    # NOQA
        form_layout.addRow(QLabel("Frequency / MHz"), dsb_frequency)
        dsb_amplitude = QDoubleSpinBox()
        dsb_amplitude.setRange(-60, 20)
        dsb_amplitude.setValue(self._device.get_amplitude())
        dsb_amplitude.valueChanged.connect(self._handle_amplitude_changed)    # NOQA
        form_layout.addRow(QLabel("Amplitude / dBm"), dsb_amplitude)

        # Buttons
        button_output = ToggleButton(state=self._device.get_output())
        button_output.clicked.connect(self._handle_button_output_clicked)    # NOQA

        # Total Layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(button_output)
        self.setLayout(layout)
        self.show()

    @pyqtSlot(float)
    def _handle_frequency_changed(self, frequency):
        self._device.set_frequency(frequency=frequency*MHz)

    @pyqtSlot(float)
    def _handle_amplitude_changed(self, amplitude):
        self._device.set_amplitude(amplitude=amplitude)

    @pyqtSlot(bool)
    def _handle_button_output_clicked(self, state):
        self._device.set_output(state=state)
