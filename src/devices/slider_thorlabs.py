import logging

from PyQt6.QtCore import QTimer, pyqtSlot, QEvent
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QGridLayout

from src.devices.device_main import USBDevice


class SliderThorlabs(USBDevice):
    NAME = "Thorlabs Slider"
    ICON = "stage"
    TIMEOUT = 0.5
    TERMINATION_READ = 2

    def __init__(self, address):
        super().__init__(address)
        self._devices = []
        # self.scan_devices()

    def scan_devices(self):
        """
        Scan Devices and Initialize them
        """
        self._devices = []
        for i in range(10):
            ret = self.read(f"{i}in")
            if ret != '':
                self._devices.append(i)
        logging.info(f"{self.NAME}: Found {len(self._devices)} Devices")

        for i in self._devices:
            self.read(f"{i}i1")

        return len(self._devices)

    def get_position(self):
        """
        Return List of Positions of all Devices
        """
        positions = []
        for i in self._devices:
            ret = self.read(f"{i}gp")
            try:
                ret = int(ret[3:], 16)
            except ValueError:
                ret = -1
            positions.append(ret)
        return positions

    def move_forward(self, device):
        """
        Move Slider Forward
        """
        self.write(f"{device}fw")

    def move_backward(self, device):
        """
        Move Slider Backward
        """
        self.write(f"{device}bw")

    def gui_open(self):
        """
        Open GUI
        """
        self.app = SliderThorlabsWindow(self)


class SliderThorlabsWindow(QWidget):

    def __init__(self, device: SliderThorlabs):
        super().__init__()
        self._device = device

        self.setWindowTitle(f"{self._device.NAME}")
        self.setGeometry(735, 365, 400, 0)

        layout = QGridLayout()
        layout.addWidget(QLabel("<b>Position / mm</b>"), 0, 1)
        layout.addWidget(QLabel("<b>Forward</b>"), 0, 2)
        layout.addWidget(QLabel("<b>Backward</b>"), 0, 3)

        self.label_positions = []
        number_devices = self._device.scan_devices()
        positions = self._device.get_position()

        for i in range(number_devices):
            layout.addWidget(QLabel(f"Slider {i}"), i+1, 0)
            label_position = QLabel(str(positions[i]))
            self.label_positions.append(label_position)
            layout.addWidget(label_position, i+1, 1)
            button_forward = QPushButton("Forward")
            button_forward.clicked.connect(lambda: self._device.move_forward(device=i+1))
            layout.addWidget(button_forward, i+1, 2)
            button_backward = QPushButton("Backward")
            button_backward.clicked.connect(lambda: self._device.move_backward(device=i+1))
            layout.addWidget(button_backward, i+1, 3)

        print(self.label_positions)

        self.setLayout(layout)

        self._timer = QTimer()
        self._timer.timeout.connect(self.refresh_values)
        # self._timer.start(2000)

        self.show()

    def refresh_values(self):
        """
        Refresh Labels
        """
        positions = self._device.get_position()
        print(positions)
        for i, label in enumerate(self.label_positions):
            print(label)
            label.setText(str(positions[i]))

    @pyqtSlot()
    def closeEvent(self, event: QEvent):
        """
        Close Window Event
        """
        self._timer.stop()
        event.accept()
