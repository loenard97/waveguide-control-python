import logging
import datetime
import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt, pyqtSlot, QEvent, QTimer
from PyQt6.QtWidgets import QWidget, QFormLayout, QLabel, QHBoxLayout, QPushButton, QVBoxLayout, QLineEdit, QComboBox

try:
    from src.devices.lib_camera_ximea import xiapi
except OSError:
    logging.error("Could not import Ximea Camera API. Is the Ximea Software installed?")


class CameraXimea:
    NAME = "Ximea Camera"
    ADDRESS_DEFAULT = ''
    app = None

    def __init__(self, address=ADDRESS_DEFAULT):
        self.address = address
        self._ser = xiapi.Camera()
        self._img = xiapi.Image()
        self._last_picture = None
        self.dimensions = [0, 2047, 0, 2047]        # TODO: read out image size

        try:
            self._ser.open_device()
        except xiapi.Xi_error:
            raise ConnectionError

        self._ser.set_imgdataformat('XI_MONO8')
        self._ser.start_acquisition()

    def disconnect(self):
        self._ser.stop_acquisition()
        self._ser.close_device()

    def get_exposure_time(self):
        return str(self._ser.get_exposure())

    def set_exposure_time(self, exposure_time):
        """
        Set Exposure Time in microseconds
        """
        self._ser.set_exposure(float(exposure_time))

    def set_cooling_mode(self, mode):
        """
        Set Cooling Mode OFF | AUTO | MANUAL
        """
        xi_mode = "XI_TEMP_CTRL_MODE_OFF"
        if mode == "AUTO":
            xi_mode = "XI_TEMP_CTRL_MODE_AUTO"
        elif mode == "MANUAL":
            xi_mode = "XI_TEMP_CTRL_MODE_MANUAL"

        self._ser.set_cooling(xi_mode)

    def get_cooling_mode(self):
        """
        Get Cooling Mode OFF | AUTO | MANUAL
        """
        xi_mode = self._ser.get_cooling()
        return xi_mode.split('_')[-1]

    def get_target_temperature(self):
        return f"{self._ser.get_target_temp():.2f}"

    def set_target_temperature(self, temperature):
        self._ser.set_target_temp(float(temperature))

    def get_temperature(self):
        return f"{self._ser.get_temp():.2f}"

    def get_picture(self):
        return self._last_picture

    def save_picture(self, file_name: str):
        np.save(file_name, self._last_picture)
        logging.info(f"{self.NAME}: Saved Picture as '{file_name}.npy'")

    def take_picture(self, save_as=None):
        """
        Take Picture and return as Numpy Array
        """
        # Take Picture
        try:
            self._ser.get_image(self._img)
        except xiapi.Xi_error:
            logging.warning(f"{self.NAME}: Could not take Picture")
        data = self._img.get_image_data_numpy()

        # Reshape and Resize
        try:
            data = data.reshape((2048, 2048), order='F')
            data = data[self.dimensions[0]:self.dimensions[1], self.dimensions[2]:self.dimensions[3]]
        except ValueError:
            return

        self._last_picture = data

        if save_as is not None:
            self.save_picture(file_name=save_as)

        return data

    def gui_open(self):
        self.app = CamXimeaWindow(self)


class CamXimeaWindow(QWidget):
    def __init__(self, device: CameraXimea):
        super().__init__()
        self.device = device

        self.setWindowTitle(f"{self.device.NAME}")
        self.setGeometry(100, 100, 1700, 900)

        self._cam_pic_canvas = pg.ImageView()
        self._cam_pic_canvas.clear()
        pic = self.device.get_picture()
        if pic is not None:
            self._cam_pic_canvas.setImage(pic)

        self._label_pic_info = QLabel()
        self._label_temperature = QLabel()

        self._line_edit_exposure_time = QLineEdit(self.device.get_exposure_time())
        self._combo_box_cooling_mode = QComboBox()
        self._combo_box_cooling_mode.addItem("AUTO")
        self._combo_box_cooling_mode.addItem("MANUAL")
        self._combo_box_cooling_mode.addItem("OFF")
        self._combo_box_cooling_mode.setCurrentText(self.device.get_cooling_mode())
        self._line_edit_target_temperature = QLineEdit(self.device.get_target_temperature())
        self._line_edit_x_min = QLineEdit(str(self.device.dimensions[0]))
        self._line_edit_x_max = QLineEdit(str(self.device.dimensions[1]))
        self._line_edit_y_min = QLineEdit(str(self.device.dimensions[2]))
        self._line_edit_y_max = QLineEdit(str(self.device.dimensions[3]))

        self.timer = QTimer()
        self.timer.timeout.connect(self._refresh_values)    # NOQA
        self.timer.start(2000)

        self._initialize_widgets()
        self._refresh_values()
        self.show()

    def _initialize_widgets(self):
        """
        Initialize Widgets
        """
        widget_picture = QWidget()
        layout_picture = QVBoxLayout()
        layout_picture.addWidget(self._cam_pic_canvas)
        button_take_picture = QPushButton("Take Picture")
        button_take_picture.clicked.connect(self._refresh_picture)    # NOQA
        button_save_picture = QPushButton("Save Picture")
        button_save_picture.clicked.connect(self._save_picture)    # NOQA
        layout_picture.addWidget(button_take_picture)
        layout_picture.addWidget(button_save_picture)
        widget_picture.setLayout(layout_picture)

        layout_settings = QFormLayout()
        widget_settings = QWidget()
        layout_settings.addRow(QLabel("<b>Values</b>"))
        layout_settings.addRow(QLabel("Temperature / °C"), self._label_temperature)
        layout_settings.addRow(QLabel("Max & Sum"), self._label_pic_info)
        layout_settings.addRow(QLabel(""))
        layout_settings.addRow(QLabel("<b>Settings</b>"))
        layout_settings.addRow(QLabel("Exposure Time / us"), self._line_edit_exposure_time)
        layout_settings.addRow(QLabel("Cooling Mode"), self._combo_box_cooling_mode)
        layout_settings.addRow(QLabel("Target Temperature / °C"), self._line_edit_target_temperature)
        layout_settings.addRow(QLabel(""))
        layout_settings.addRow(QLabel("<b>Resizing</b>"))
        layout_settings.addRow(QLabel("x min"), self._line_edit_x_min)
        layout_settings.addRow(QLabel("x max"), self._line_edit_x_max)
        layout_settings.addRow(QLabel("y min"), self._line_edit_y_min)
        layout_settings.addRow(QLabel("y max"), self._line_edit_y_max)
        widget_settings.setLayout(layout_settings)

        widget_buttons = QWidget()
        layout_buttons = QHBoxLayout()
        button_apply = QPushButton("Apply")
        button_apply.clicked.connect(self._handle_button_apply)    # NOQA
        layout_buttons.addWidget(button_apply)
        widget_buttons.setLayout(layout_buttons)

        widget_right_side = QWidget()
        layout_right_side = QVBoxLayout()
        layout_right_side.addWidget(widget_settings)
        layout_right_side.addWidget(widget_buttons)
        widget_right_side.setLayout(layout_right_side)

        layout = QHBoxLayout()
        layout.addWidget(widget_picture)
        layout.addWidget(widget_right_side, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)

    @pyqtSlot()
    def _handle_button_apply(self):
        self.device.set_exposure_time(self._line_edit_exposure_time.text())
        self.device.set_target_temperature(self._line_edit_target_temperature.text())
        self.device.set_cooling_mode(self._combo_box_cooling_mode.currentText())
        self.device.dimensions = [
            int(self._line_edit_x_min.text()),
            int(self._line_edit_x_max.text()),
            int(self._line_edit_y_min.text()),
            int(self._line_edit_y_max.text()),
        ]

    @pyqtSlot()
    def _refresh_values(self):
        self._label_temperature.setText(self.device.get_temperature())

    @pyqtSlot()
    def _refresh_picture(self):
        pic = self.device.take_picture()
        self._cam_pic_canvas.clear()
        self._cam_pic_canvas.setImage(pic)
        self._label_pic_info.setText(f"Max: {pic.max()}\nSum: {pic.sum()}")

    @pyqtSlot()
    def _save_picture(self):
        file_name = f"/mnt/DATA/meca/test_ximea/{datetime.datetime.now()}"
        self.device.save_picture(file_name)

    @pyqtSlot()
    def closeEvent(self, event: QEvent):
        """
        Close Window Event
        """
        self.timer.stop()
        event.accept()
