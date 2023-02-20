import yaml
import msgpack
import logging

from PyQt6.QtNetwork import QTcpSocket
from PyQt6.QtCore import QObject, pyqtSlot, QTimer, QEvent
from PyQt6.QtWidgets import QWidget, QPushButton, QFormLayout, QLabel, QHBoxLayout, QLineEdit, QGridLayout


class RedPitayaPulsecounter(QObject):
    """
    RedPitaya Pulsecounter
    A Pulse Counter Server running on the RedPitaya counts the rising edges of signals for different Counters.
    Each Counter can be read out and reset to 0.
    """

    NAME = "Red Pitaya"
    ICON = "rp"

    def __init__(self, address):
        super().__init__()
        self.app = QWidget()
        self._socket = QTcpSocket()
        self._unpacker = msgpack.Unpacker()
        self._registers = {}
        self.address = address
        self._socket.connectToHost(self.address, 8050)
        self._socket.waitForConnected()
        self._registers = self.get_registers()
        logging.info(f"{self.NAME}: Connected")

    def disconnect(self):
        """
        Disconnect from RedPitaya
        """
        self._socket.close()
        logging.info(f"{self.NAME}: Disconnected")

    def write(self, message: str, register: int, value=None):
        """
        Write Message to Register
        """
        if value is None:
            logging.info(f"{self.NAME}: send '{message}' to '{register}'")
            packed_bytes = msgpack.packb([message, register], use_bin_type=True)
        else:
            logging.info(f"{self.NAME}: send '{message}' to '{register}' with '{value}'")
            packed_bytes = msgpack.packb([message, register, value], use_bin_type=True)
        self._socket.write(packed_bytes)
        self._socket.waitForBytesWritten(3000)

    def read(self, message: str, register=None) -> str:
        """
        Read Message from Register
        """
        # Empty Socket
        self._socket.read(self._socket.bytesAvailable())

        # Write Message
        if register is None:
            data = [message]
        else:
            data = [message, register]
        packed_bytes = msgpack.packb(data, use_bin_type=True)
        self._socket.write(packed_bytes)
        self._socket.waitForBytesWritten(3000)

        # Read Message
        self._socket.waitForReadyRead()
        packed_bytes = self._socket.read(self._socket.bytesAvailable())

        self._unpacker.feed(packed_bytes)
        last_message = None
        for message in self._unpacker:
            logging.debug(f"{self.NAME}: Recv Message '{message}'")
            last_message = message

        return last_message

    def get_config(self):
        """
        Read Config File from RedPitaya
        """
        return self.read(message="get_config")

    def get_registers(self) -> dict:
        """
        Return Dictionary of all Registers
        """
        config = self.get_config()
        yaml_file = yaml.safe_load(config[1])
        counters = yaml_file["counters"]
        offsets = counters["offsets"]

        for name, value in offsets.items():
            offsets[name] = counters["page"] + value

        return offsets

    def get_counter(self, counter: int) -> int:
        """
        Get current Value of Counter
        """
        _, value = self.read("read_reg", self._registers[f"cnt_{counter}_value"])
        return int(value)

    def reset_counter(self, counter):
        """
        Reset Counter to 0
        :param counter  int Counter to reset | 'all' Reset all Counter
        """
        if counter == 'all':
            for i in range(15):
                self.write("write_reg", self._registers[f"cnt_{i}_rst"], 1)
                self.write("write_reg", self._registers[f"cnt_{i}_rst"], 0)
        else:
            self.write("write_reg", self._registers[f"cnt_{counter}_rst"], 1)
            self.write("write_reg", self._registers[f"cnt_{counter}_rst"], 0)

    def gui_open(self):
        """
        Open GUI for RedPitaya
        """
        self.app = RedPitayaWindow(self)


class RedPitayaWindow(QWidget):
    def __init__(self, device: RedPitayaPulsecounter):
        super().__init__()
        self.device = device

        self.setWindowTitle(f"{self.device.NAME}")
        self.setGeometry(735, 365, 450, 350)

        self.label_frequency_ch1 = QLabel()
        self.label_frequency_ch2 = QLabel()
        self.label_amplitude_ch1 = QLabel()
        self.label_amplitude_ch2 = QLabel()
        self.line_edit_frequency_ch1 = QLineEdit()
        self.line_edit_frequency_ch2 = QLineEdit()
        self.line_edit_amplitude_ch1 = QLineEdit()
        self.line_edit_amplitude_ch2 = QLineEdit()
        self.button_output_ch1 = QPushButton()
        self.button_output_ch2 = QPushButton()

        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_values)
        # self.timer.start()

        self.initialize_widgets()
        self.show()

    def initialize_widgets(self):
        layout_values_ch1 = QFormLayout()
        widget_values_ch1 = QWidget()
        layout_values_ch1.addRow(QLabel("<b>Pulse Counter</b>"))
        for i in range(15):
            layout_values_ch1.addRow(QLabel(f"Counter {i}"), QLabel(str(self.device.get_counter(counter=i))))
        widget_values_ch1.setLayout(layout_values_ch1)

        widget_buttons_ch1 = QWidget()
        layout_buttons_ch1 = QHBoxLayout()
        self.button_output_ch1 = QPushButton("Reset")

        def handle_reset():
            for j in range(15):
                self.device.reset_counter(counter=j)

        self.button_output_ch1.clicked.connect(handle_reset)

        layout_buttons_ch1.addWidget(self.button_output_ch1)
        widget_buttons_ch1.setLayout(layout_buttons_ch1)

        layout = QGridLayout()
        layout.addWidget(widget_values_ch1, 0, 0)
        layout.addWidget(widget_buttons_ch1, 2, 0)
        self.setLayout(layout)

    def refresh_values(self):
        self.label_frequency_ch1.setText(self.device.get_frequency(channel=1))
        self.label_frequency_ch2.setText(self.device.get_frequency(channel=2))
        self.label_amplitude_ch1.setText(self.device.get_amplitude(channel=1))
        self.label_amplitude_ch2.setText(self.device.get_amplitude(channel=2))

    @pyqtSlot()
    def closeEvent(self, event: QEvent):
        """
        Close Window Event
        """
        self.timer.stop()
        event.accept()
