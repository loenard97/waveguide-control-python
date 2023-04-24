"""
Radio Frequency Generator by Rohde&Schwarz
The RFGRohdeSchwarz class is supposed to work with all R&S RFGs, but was only tested with the following versions:
 - SMB100A

Manuals:
https://scdn.rohde-schwarz.com/ur/pws/dl_downloads/dl_common_library/dl_manuals/gb_1/s/smb/SMB100A_OperatingManual_en_23.pdf
"""

import os
import logging
import numpy as np
from ftplib import FTP

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QVBoxLayout

from src.devices.main_device import EthernetDevice
from src.static_gui_elements.toggle_button import ToggleButton
from src.static_gui_elements.delayed_spin_box import DelayedDoubleSpinBox


class RFGRohdeSchwarz(EthernetDevice):

    save_file_path = os.path.join(".config", "devices", "rfg_rs_smbv100a")

    def get_identification(self):
        """
        Get Identification String
        """
        return self.read("*IDN?")

    def get_error(self):
        """
        Get Last Error
        """
        if self.read("SYST:ERR:COUN?", error_checking=False) == '0':
            return None
        return self.read("SYST:ERR:ALL?", error_checking=False)

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
        Trigger
        """
        self.write("*TRG")

    def wait(self):
        """
        Wait to Continue
        """
        self.write("*WAI")

    def get_event_status(self):
        """
        Get Event Status
        """
        return self.read("*ESR?")

    def get_operation_complete(self):
        """
        Get Operation Complete
        """
        return self.read("*OPC")

    def trigger_rearm(self):
        """
        Rearm Trigger
        """
        self.write("SOURce1:BB:ARB:TRIG:SEQ ARET")
        self.write("SOURce1:BB:ARB:TRIG:ARM:EXEC")

    @staticmethod
    def set_channel(channel=1):
        """
        Channel has to be 1
        """
        assert channel == 1

    @staticmethod
    def get_channel():
        """
        Channel has to be 1
        """
        return 1

    def set_output(self, channel=1, state=False):
        """
        Set Output
        """
        assert channel == 1, "Channel has to be 1"
        assert isinstance(state, bool), "State has to be bool"

        if state:
            self.write("OUTP:STAT 1")
        else:
            self.write("OUTP:STAT 0")

    def get_output(self, channel=1):
        """
        Get Output
        """
        self.set_channel(channel)
        if self.read("OUTP:STAT?") == 1:
            return True
        return False

    def set_amplitude(self, channel=1, amplitude=-40.0):
        """
        Set Amplitude in dBm
        """
        assert channel == 1, "Channel has to be 1"

        self.write(f"POW {amplitude}")

    def get_amplitude(self, channel=1):
        """
        Get Amplitude in dBm
        """
        self.set_channel(channel)
        return float(self.read("POW?"))

    def set_frequency(self, channel=1, frequency=1_000_000.0):
        """
        Set Frequency in Hz
        """
        assert channel == 1, "Channel has to be 1"

        self.write(f"FREQ {frequency}Hz")

    def get_frequency(self, channel=1):
        """
        Get Frequency in MHz
        """
        self.set_channel(channel)
        return float(self.read("FREQ?"))

    def set_constant_mw(self, channel=1, frequency=1_000_000.0, amplitude=-40.0, state=False):
        """
        Set Constant MW Output
        :param int channel: Channel Number
        :param float frequency: Frequency in Hz
        :param float amplitude: Amplitude in dBm
        :param bool state: Output on | off
        """
        self.set_frequency(channel=channel, frequency=frequency)
        self.set_amplitude(channel=channel, amplitude=amplitude)
        self.set_output(channel=channel, state=state)

    def set_pulse_modulation(self, channel=1, source="EXT", state=False):
        """
        Set Pulse Modulation
        :param int channel: Channel
        :param str source: Modulation Source INT | EXT
        :param bool state: Modulation State
        """
        self.write(f"SOUR{channel}:PULM:SOUR {source}")
        self.write(f"SOUR{channel}:PULM:STAT {'ON' if state else 'OFF'}")

    def set_function_constant(self, channel=1, frequency=1000, amplitude=-30, output=False):
        """
        Set Constant MW Output
        """
        assert channel == 1, "Channel has to be 1"

        self.write(f"SOUR{channel}:BB:ARB:STAT OFF")
        self.write(f"SOUR{channel}:IQ:STAT OFF")
        self.write("FREQ:MODE CW")
        self.set_amplitude(amplitude=amplitude)
        self.set_frequency(frequency=frequency)
        self.set_output(state=output)

    def set_function_arbitrary(self, frequency, amplitude, waveform, output):
        """
        load predefined waveform from Memory and wait for Trigger signal to play
        """
        self.write("SOURce1:BB:ARB:STAT ON")
        self.write("SOURce1:BB:DM:FILT:TYPE GAUS")
        self.write(f'SOURce1:BB:ARBitrary:WAV:SELect "/hdd/{waveform}"')
        self.write("SOURce1:IQ:STAT ON")
        self.write("SOURce1:BB:ARB:TRIG:SOUR EXT")
        self.write("SOURce1:INP:TRIG:SLOP POS")
        self.write(f"POW {amplitude}")
        self.write(f"FREQ {frequency}")
        self.write("SOURce1:BB:ARB:TRIG:SEQ RETR")
        self.write("SOURce1:BB:ARB:TRIG:SEQ ARET")
        self.write("SOURce1:BB:ARB:TRIG:ARM:EXEC")
        self.write(f"OUTP:STAT {output}")

    def set_function_arbitrary_single(self, frequency, amplitude, waveform, output):
        """
        load predefined waveform from Memory and wait for Trigger signal to play
        """
        self.write("SOURce1:BB:ARB:STAT ON")
        self.write("SOURce1:BB:DM:FILT:TYPE GAUS")
        self.write(f'SOURce1:BB:ARBitrary:WAV:SELect "/hdd/{waveform}"')
        self.write("SOURce1:IQ:SOUR BASeband")
        self.write("SOURce1:IQ:STAT ON")
        self.write("SOURce1:BB:DM:FILT:TYPE RECT")   # *RST: GAUSs
        self.write("SOURce1:BB:ARB:TRIG:SOUR EXT")
        self.write("SOURce1:INP:TRIG:SLOP POS")
        self.write(f"POW {amplitude}")
        self.write(f"FREQ {frequency}")
        self.write("SOUR1:BB:ARB:SEQ SING")           # Single Output
        self.write("SOUR1:BB:ARB:TRIG:SLUN SEQ")      # unit length of one sequence
        self.write("SOUR1:BB:ARB:TRIG:SLEN 1")        # play one unit
        self.write(f"OUTP:STAT {output}")
        self.write("POW:ALC OFF")
        self.write("POW:ALC:OMOD SHOL")

    def set_function_sweep(self, start_freq, stop_freq, step_freq, amplitude, dwell_time):
        """
        Run Sweep from Start to Stop Frequency
        """
        # Frequencies in Hz
        # Dwell Time in s
        self.set_function_constant(start_freq, amplitude, 1)    # turn on MW on start frequency with given amplitude
        self.write(f"SOURce1:FREQ:STARt {start_freq}")
        self.write(f"SOURce1:FREQ:STOP {stop_freq}")
        self.write("SOURce1:FREQ:MODE STEP'")
        self.write("SOURce1:SWE:MODE STEP'")
        self.write("SOURce1:SWE:FREQ:SPAC LIN'")
        self.write(f"SOURce1:SWE:FREQ:STEP:LIN {step_freq}")
        self.write(f"SOURce1:SWE:FREQ:DWEL {dwell_time}")
        self.write("TRIG:FSW:SOUR EXT'")
        self.write("SOURce1:SWE:FREQ:RETR ON'")
        self.write("SOURce1:FREQ:MODE SWE'")

    def set_analog_iq(self, frequency, amplitude, output):
        self.write("SOURce1:IQ:SOUR ANALog'")
        self.write("SOURce1:IQ:STAT ON'")
        self.write(f"POW {amplitude}")
        self.write(f"FREQ {frequency}")
        self.write(f"OUTP:STAT {output}")

    def set_function_iq(self, function_i, function_q, frequency, amplitude, samplerate, file_name):
        """
        Set IQ Modulation

        :param function_i: list of I values in range (-1, 1)
        :param function_q: list of Q values in range (-1, 1)
        :param frequency: float (Hz) frequency of the SMBV
        :param amplitude: float (dBm) power level of the SMBV
        :param samplerate: int (Hz) sampling rate for the output
        :param file_name: str list name
        :return:
        """

        # Create IQ Array
        i = np.array(function_i, dtype=np.int16) * 32767 + 0.5
        q = np.array(function_q, dtype=np.int16) * 32767 + 0.5
        iq = np.ravel((i, q), order="F")
        bit_length = len(i) * 4 + 1

        # Write local File
        os.makedirs(os.path.join(self.save_file_path, "iq_wave_files"))
        file_path = os.path.join(self.save_file_path, "iq_wave_files", f"{file_name}.wv")
        with open(file_path, "wb") as wave_file:
            wave_file.write(b"{TYPE: SMU-WV, 0}")
            wave_file.write(b"{CLOCK: %i}" % samplerate)
            wave_file.write(b"{LEVEL OFFS: 0.000000,0.000000}")
            wave_file.write(b"{SAMPLES: %i}" % len(i))
            wave_file.write(b"{WAVEFORM-%i:#" % bit_length)
            wave_file.write(iq.tobytes())
            wave_file.write(b"}")

        # Transfer local File to RFG
        with FTP(host=self.address, user="instrument", passwd="instrument") as ftp, \
                open(file_path, "rb") as wave_file:
            ftp.cwd("/share/hdd")
            ftp.storbinary(f"STOR {file_name}.wv", wave_file)

        # Write Settings
        self.write(f"FREQ {frequency:.12f}Hz")
        self.write(f"POW {amplitude}:.2f")
        self.write("BB:ARB:STAT ON")
        self.write(f"BB:ARB:WAV:SEL '/hdd/{file_name}.wv'")
        self.write("BB:ARB:SEQ SING")
        self.write("BB:ARB:TRIG:SLUN gSEQ")
        self.write("BB:ARB:TRIG:SLEN 1")
        self.write("BB:ARB:TRIG:SOUR EXT")
        self.write("BB:ARB:TRIG:EXT:SYNC:OUTP OFF")

        logging.info(f"{self.name}: Send: IQ Wave File '{file_name}.wv'")

    def set_amplitude_modulation_external(self, frequency, amplitude, depth, output):
        """
        RF frequency, RF amplitude, Modulation Depth in percent, Output state
        """
        self.write(f"POW {amplitude}")
        self.write(f"FREQ {frequency}")
        self.write(f"OUTP:STAT {output}")
        self.write(f"SOURce1:AM:STATe {output}")
        self.write("SOURce1:AM:SOURce EXT")
        self.write(f"SOURce1:AM: {depth}PCT")

    def gui_open(self):
        self.app = RFGRohdeSchwarzWindow(self)


class RFGRohdeSchwarzWindow(QWidget):

    def __init__(self, device: RFGRohdeSchwarz):
        super().__init__()

        # Variables
        self._device = device

        # Appearance
        self.setWindowTitle(f"{self._device.name}")
        self.setGeometry(735, 365, 450, 350)

        # Form Layout
        form_layout = QFormLayout()
        form_layout.addRow(QLabel("<b>CW RF Signal</b>"))
        dsb_frequency = DelayedDoubleSpinBox()
        dsb_frequency.setRange(0, 14000)
        dsb_frequency.setValue(self._device.get_frequency())
        dsb_frequency.valueChanged.connect(self._handle_frequency_changed)
        form_layout.addRow(QLabel("Frequency / MHz"), dsb_frequency)
        dsb_amplitude = DelayedDoubleSpinBox()
        dsb_amplitude.setRange(-60, 20)
        dsb_amplitude.setValue(self._device.get_amplitude())
        dsb_amplitude.valueChanged.connect(self._handle_amplitude_changed)
        form_layout.addRow(QLabel("Amplitude / dBm"), dsb_amplitude)

        # Buttons
        button_output = ToggleButton(state=self._device.get_output())
        button_output.clicked.connect(self._handle_button_output_clicked)

        # Total Layout
        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(button_output)
        self.setLayout(layout)
        self.show()

    # Event Slots
    @pyqtSlot(float)
    def _handle_frequency_changed(self, frequency):
        self._device.set_frequency(frequency=frequency)

    @pyqtSlot(float)
    def _handle_amplitude_changed(self, amplitude):
        self._device.set_amplitude(amplitude=amplitude)

    @pyqtSlot(bool)
    def _handle_button_output_clicked(self, state):
        self._device.set_output(state=state)
