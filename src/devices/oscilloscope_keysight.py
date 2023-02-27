from src.devices.main_device import EthernetDevice
from src.static_gui_elements.toggle_button import ToggleButton

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QComboBox, QPushButton, QFormLayout, QDoubleSpinBox, \
    QVBoxLayout


def test_keysight_1200x_osci():
    import sys
    import logging

    logging.basicConfig(
        level=30,
        format="%(asctime)s: [%(levelname)s] %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

    osci = OscilloscopeKeysight("192.168.88.131")
    print(osci.get_identity())
    print(osci.read("ACQuire:TYPE?"))
    print(osci.read("ACQuire:COMPlete?"))
    print(osci.read("ACQuire:COUNt?"))
    print("Source", osci.read("MEASure:SOURce?"))
    print("Freq", osci.read("MEASure:FREQuency? CHAN1"))
    print("Vamp", osci.read("MEASure:VAMPlitude? CHAN1"))
    print("Vav", osci.read("MEASure:VAVerage? CHAN1"))
    print("max", osci.read("MEASure:VMAX? CHAN1"))
    print("min", osci.read("MEASure:VMIN? CHAN1"))
    print("Vpp", osci.read("MEASure:VPP? CHAN1"))
    # print(osci.read("DISPlay:DATA?"))
    # print(osci.read("LISTer:DATA?"))


class OscilloscopeKeysight(EthernetDevice):
    NAME = "Keysight 1200X Series Oscilloscope"
    ICON = "osci"

    def get_identity(self):
        return self.read("*IDN?")

    def measure_frequency(self, channel: int):
        return self.read(f"MEASure:FREQuency? CHANnel{channel}")

    def measure_volt_amplitude(self, channel: int):
        return self.read(f"MEASure:VAMPlitude? CHANnel{channel}")

    def measure_volt_maximum(self, channel: int):
        return self.read(f"MEASure:VMAX? CHANnel{channel}")

    def measure_volt_minimum(self, channel: int):
        return self.read(f"MEASure:VMIN? CHANnel{channel}")

    def measure_volt_peak_peak(self, channel: int):
        return self.read(f"MEASure:VPP? CHANnel{channel}")

    def gui_open(self):
        self.app = Keysight1200XOsciWindow(self)


class Keysight1200XOsciWindow(QWidget):
    def __init__(self, device: OscilloscopeKeysight):
        super().__init__()
        self.device = device

        self.setWindowTitle(f"{self.device.NAME}")
        self.setGeometry(735, 365, 450, 350)

        self.combo_box_mode_ch1 = QComboBox()
        self.combo_box_mode_ch1.addItems(["DC", "Sine", "Pulse"])
        self.line_edit_frequency_ch1 = QDoubleSpinBox()
        self.line_edit_frequency_ch1.setRange(0, 2147483647)
        self.line_edit_amplitude_ch1 = QDoubleSpinBox()
        self.line_edit_amplitude_ch1.setRange(-5, 5)
        self.line_edit_offset_ch1 = QDoubleSpinBox()
        self.line_edit_offset_ch1.setRange(-5, 5)

        self.combo_box_mode_ch2 = QComboBox()
        self.combo_box_mode_ch2.addItems(["DC", "Sine", "Pulse"])
        self.line_edit_frequency_ch2 = QDoubleSpinBox()
        self.line_edit_frequency_ch2.setRange(0, 2147483647)
        self.line_edit_amplitude_ch2 = QDoubleSpinBox()
        self.line_edit_amplitude_ch2.setRange(-5, 5)
        self.line_edit_offset_ch2 = QDoubleSpinBox()
        self.line_edit_offset_ch2.setRange(-5, 5)

        self.button_output_ch1 = ToggleButton(state=self.device.get_output(channel=1))
        self.button_output_ch2 = ToggleButton(state=self.device.get_output(channel=2))

        self.initialize_widgets()
        self.show()

    def initialize_widgets(self):
        # ----- Ch1 Widget left ----- #
        widget_form_ch1 = QWidget()
        layout_form_ch1 = QFormLayout()
        layout_form_ch1.addRow(QLabel("<b>Channel 1</b>"))
        layout_form_ch1.addRow(QLabel("Mode"), self.combo_box_mode_ch1)
        layout_form_ch1.addRow(QLabel("Frequency / Hz"), self.line_edit_frequency_ch1)
        layout_form_ch1.addRow(QLabel("Amplitude / V"), self.line_edit_amplitude_ch1)
        layout_form_ch1.addRow(QLabel("Offset / V"), self.line_edit_offset_ch1)
        widget_form_ch1.setLayout(layout_form_ch1)

        widget_buttons_ch1 = QWidget()
        layout_buttons_ch1 = QHBoxLayout()
        button_apply_ch1 = QPushButton("Apply")
        button_apply_ch1.clicked.connect(lambda: self._handle_button_apply(channel=1))
        self.button_output_ch1.clicked.connect(lambda: self._handle_button_output(channel=1))
        layout_buttons_ch1.addWidget(button_apply_ch1)
        layout_buttons_ch1.addWidget(self.button_output_ch1)
        widget_buttons_ch1.setLayout(layout_buttons_ch1)

        # ----- Ch2 Widget Right ----- #
        widget_form_ch2 = QWidget()
        layout_form_ch2 = QFormLayout()
        layout_form_ch2.addRow(QLabel("<b>Channel 2</b>"))
        layout_form_ch2.addRow(QLabel("Mode"), self.combo_box_mode_ch2)
        layout_form_ch2.addRow(QLabel("Frequency / Hz"), self.line_edit_frequency_ch2)
        layout_form_ch2.addRow(QLabel("Amplitude / V"), self.line_edit_amplitude_ch2)
        layout_form_ch2.addRow(QLabel("Offset / V"), self.line_edit_offset_ch2)
        widget_form_ch2.setLayout(layout_form_ch2)

        widget_buttons_ch2 = QWidget()
        layout_buttons_ch2 = QHBoxLayout()
        button_apply_ch2 = QPushButton("Apply")
        button_apply_ch2.clicked.connect(lambda: self._handle_button_apply(channel=2))
        self.button_output_ch2.clicked.connect(lambda: self._handle_button_output(channel=2))
        layout_buttons_ch2.addWidget(button_apply_ch2)
        layout_buttons_ch2.addWidget(self.button_output_ch2)
        widget_buttons_ch2.setLayout(layout_buttons_ch2)

        # ----- Main Widget ----- #
        layout_ch1 = QVBoxLayout()
        layout_ch2 = QVBoxLayout()
        layout_ch1.addWidget(widget_form_ch1)
        layout_ch1.addWidget(widget_buttons_ch1)
        layout_ch2.addWidget(widget_form_ch2)
        layout_ch2.addWidget(widget_buttons_ch2)
        layout = QHBoxLayout()
        widget_ch1 = QWidget()
        widget_ch2 = QWidget()
        widget_ch1.setLayout(layout_ch1)
        widget_ch2.setLayout(layout_ch2)
        layout.addWidget(widget_ch1)
        layout.addWidget(widget_ch2)

        self.setLayout(layout)

    @pyqtSlot()
    def _handle_button_apply(self, channel: int):
        if channel == 1:
            if self.combo_box_mode_ch1.currentText() == 'DC':
                self.device.set_function_dc(channel=1, offset=self.line_edit_offset_ch1.value())

            elif self.combo_box_mode_ch1.currentText() == 'Pulse':
                print('Applying Pulse')

            elif self.combo_box_mode_ch1.currentText() == 'Sine':
                print('Applying Sine')

        elif channel == 2:
            if self.combo_box_mode_ch2.currentText() == 'DC':
                self.device.set_function_dc(channel=2, offset=self.line_edit_offset_ch2.value())

            elif self.combo_box_mode_ch2.currentText() == 'Pulse':
                print('Applying Pulse')

            elif self.combo_box_mode_ch2.currentText() == 'Sine':
                print('Applying Sine')

    @pyqtSlot()
    def _handle_button_output(self, channel: int):
        if channel == 1:
            if self.button_output_ch1.isChecked():
                self.device.set_output(channel=1, state=True)
            else:
                self.device.set_output(channel=1, state=False)

        elif channel == 2:
            if self.button_output_ch2.isChecked():
                self.device.set_output(channel=2, state=True)
            else:
                self.device.set_output(channel=2, state=False)


if __name__ == '__main__':
    test_keysight_1200x_osci()
