"""
Andor Camera
"""

import os
import ctypes
import logging
import platform
import datetime
import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt, QEvent, pyqtSlot, QTimer
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QLabel, QFormLayout, QComboBox

from src.devices.main_device import Device
from src.static_gui_elements.delayed_spin_box import DelayedDoubleSpinBox


class CameraAndor(Device):
    NAME = "Andor Camera"
    ICON = "cam"

    STATUS_CODES = {
        20001: "DRV_self.STATUS_CODESS",
        20002: "DRV_SUCCESS",
        20003: "DRV_VXNOTINSTALLED",
        20006: "DRV_ERROR_FILELOAD",
        20007: "DRV_ERROR_VXD_INIT",
        20010: "DRV_ERROR_PAGELOCK",
        20011: "DRV_ERROR_PAGE_UNLOCK",
        20013: "DRV_ERROR_ACK",
        20024: "DRV_NO_NEW_DATA",
        20026: "DRV_SPOOLERROR",
        20034: "DRV_TEMP_OFF",
        20035: "DRV_TEMP_NOT_STABILIZED",
        20036: "DRV_TEMP_STABILIZED",
        20037: "DRV_TEMP_NOT_REACHED",
        20038: "DRV_TEMP_OUT_RANGE",
        20039: "DRV_TEMP_NOT_SUPPORTED",
        20040: "DRV_TEMP_DRIFT",
        20050: "DRV_COF_NOTLOADED",
        20053: "DRV_FLEXERROR",
        20066: "DRV_P1INVALID",
        20067: "DRV_P2INVALID",
        20068: "DRV_P3INVALID",
        20069: "DRV_P4INVALID",
        20070: "DRV_INIERROR",
        20071: "DRV_COERROR",
        20072: "DRV_ACQUIRING",
        20073: "DRV_IDLE",
        20074: "DRV_TEMPCYCLE",
        20075: "DRV_NOT_INITIALIZED",
        20076: "DRV_P5INVALID",
        20077: "DRV_P6INVALID",
        20083: "P7_INVALID",
        20089: "DRV_USBERROR",
        20091: "DRV_NOT_SUPPORTED",
        20095: "DRV_INVALID_TRIGGER_MODE",
        20099: "DRV_BINNING_ERROR",
        20990: "DRV_NOCAMERA",
        20991: "DRV_NOT_SUPPORTED",
        20992: "DRV_NOT_AVAILABLE"
    }

    def __init__(self, address=6924):
        # Variables
        self.address = int(address)      # Serial Number
        self.app = None
        self._ser = None

        # Settings
        self.last_picture = None
        self.resize_dimensions = [0, 1000, 0, 1000]
        self._target_temperature = 20
        self._fan_mode = "Low"
        self._image_width = 0
        self._image_height = 0
        self._image_width_bin_size = 1
        self._image_height_bin_size = 1
        self._scans = 1
        self._read_mode = 4
        self._acquisition_mode = 1
        self._exposure_time = 0.1
        self._emccd_gain = 1

        self.connect()

    def connect(self):
        """
        Connect to Camera
        """
        # Load Driver
        dir_path = os.path.abspath(os.getcwd())
        if platform.system() == "Windows" and platform.architecture()[0] == "32bit":
            dll_path = f"{dir_path}\\src\\devices\\lib_camera_andor\\atmcd32d"
        elif platform.system() == "Windows" and platform.architecture()[0] == "64bit":
            dll_path = f"{dir_path}\\src\\devices\\lib_camera_andor\\atmcd64d"
        elif platform.system() == "Linux":
            dll_path = "/usr/local/lib/libandor.so"
        else:
            raise ConnectionError("Unsupported Operating System. Windows or Linux required.")
        logging.debug(f"{self.NAME}: Found Driver '{dll_path}', for '{platform.system(), platform.architecture()[0]}'")
        self._ser = ctypes.CDLL(dll_path)

        # Search for Camera with correct Serial Number
        n_cams = self.get_available_cameras()
        logging.debug(f"{self.NAME}: Found {n_cams} Cameras, searching for correct serial number...")
        for i in range(n_cams):
            handle = self.get_handle(camera=i)
            self.set_handle(handle)
            self.initialize()
            serial = self.get_identification()
            logging.debug(f"{self.NAME}: Camera {i}: Handle {handle}, Serial Number {serial}")
            if serial == self.address:
                break

        # Check Status
        if self.get_last_error() == "DRV_NOT_INITIALIZED":
            logging.warning(f"{self.NAME}: Could not connect")
            return
        else:
            logging.debug(f"{self.NAME}: Ready")
        logging.debug(f"{self.NAME}: Found Detector '{self.get_detector()}'")

        # Settings
        # settings = load_settings(path=self.save_file_path, default_settings=self.get_settings())
        # for attribute, value in settings.items():
        #     self.__setattr__(attribute, value)

        # Default Settings
        self.set_cooler_on()
        self.set_target_temperature(self._target_temperature)
        self.set_fan_mode(self._fan_mode)
        self.set_read_mode(self._read_mode)
        self.set_acquisition_mode(self._acquisition_mode)
        self.set_exposure_time(self._exposure_time)
        self.set_emccd_gain(self._emccd_gain)
        self.set_trigger_mode(0)
        self.set_preamp_gain(0)
        self.set_em_gain_mode(0)
        self.set_vs_speed(1)
        self.set_baseline_clamp(1)
        self.set_shutter(1, 5, 30, 5)

    def disconnect(self):
        """
        Disconnect from Camera
        """
        # save_settings(path=self.save_file_path, settings=self.get_settings())
        status = self._ser.ShutDown()
        logging.info(f"{self.NAME}: Send ShutDown(), Status: {self.STATUS_CODES[status]}.")

    def get_settings(self):
        """
        Get Current Settings
        """
        return {
            "resize_dimensions": self.resize_dimensions,
            "_target_temperature": self._target_temperature,
            "_fan_mode": self._fan_mode,
            "_image_width_bin_size": self._image_width_bin_size,
            "_image_height_bin_size": self._image_height_bin_size,
            "_scans": self._scans,
            "_read_mode": self._read_mode,
            "_acquisition_mode": self._acquisition_mode,
            "_exposure_time": self._exposure_time,
            "_emccd_gain": self._emccd_gain,
        }

    def get_available_cameras(self):
        """
        Get Number of Available Cameras
        """
        n_cams = ctypes.c_int()
        status = self._ser.GetAvailableCameras(ctypes.byref(n_cams))
        logging.info(f"{self.NAME}: Recv: GetAvailableCameras({n_cams.value}), Status: {self.STATUS_CODES[status]}")
        return n_cams.value

    def get_handle(self, camera):
        """
        Get Handle Number of Camera
        """
        handle = ctypes.c_int()
        status = self._ser.GetCameraHandle(camera, ctypes.byref(handle))
        logging.info(f"{self.NAME}: Recv: GetCameraHandle({handle.value}), Status: {self.STATUS_CODES[status]}")
        return handle.value

    def set_handle(self, handle):
        """
        Set Handle Number
        """
        status = self._ser.SetCurrentCamera(ctypes.c_double(handle))
        logging.info(f"{self.NAME}: Send: SetCurrentCamera({handle}), Status: {self.STATUS_CODES[status]}")

    def initialize(self):
        """
        Initialize Camera
        """
        status = self._ser.Initialize(ctypes.c_char())
        logging.info(f"{self.NAME}: Send: Initialize(), Status: {self.STATUS_CODES[status]}")

    def get_identification(self):
        """
        Get Serial Number
        """
        serial = ctypes.c_int()
        status = self._ser.GetCameraSerialNumber(ctypes.byref(serial))
        logging.info(f"{self.NAME}: Recv: GetIdentification({serial.value}), Status: {self.STATUS_CODES[status]}")
        return serial.value

    def get_last_error(self):
        """
        Get Last Error
        """
        status = ctypes.c_int()
        error = self._ser.GetStatus(ctypes.byref(status))
        logging.info(f"{self.NAME}: Recv: GetStatus({status.value}), Status: {self.STATUS_CODES[error]}")
        return self.STATUS_CODES[error]

    def get_detector(self):
        """
        Get Width and Height of Detector
        """
        width = ctypes.c_int()
        height = ctypes.c_int()
        status = self._ser.GetDetector(ctypes.byref(width), ctypes.byref(height))
        logging.info(f"{self.NAME}: Recv: GetStatus({width.value}, {height.value}), "
                     f"Status: {self.STATUS_CODES[status]}")
        self._image_width, self._image_height = width.value, height.value
        self.resize_dimensions = [0, self._image_width, 0, self._image_height]

        return self._image_width, self._image_height

    def set_shutter(self, typ, mode, closing_time, opening_time):
        """
        Set Shutter Settings
        """
        status = self._ser.SetShutter(typ, mode, closing_time, opening_time)
        logging.info(f"{self.NAME}: Send: SetShutter({typ}, {mode}, {closing_time}, {opening_time}), "
                     f"Status: {self.STATUS_CODES[status]}")

    def set_image(self, h_bin=1, v_bin=1, h_start=1, h_end=1, v_start=1, v_end=1):
        """
        Set Image Settings
        """
        self._ser.SetImage(h_bin, v_bin, h_start, h_end, v_start, v_end)

    def set_read_mode(self, mode=4):
        """
        Set Read Mode 0 Full vertical binning | 1 Multitrack | 2 random track | 3 single track | 4 image
        """
        self._ser.SetReadMode(mode)
        self._read_mode = mode

    def set_acquisition_mode(self, mode=1):
        """
        Set Acquisition Mode 1 Single Scan | 3 Kinetic Scan
        """
        self._ser.SetAcquisitionMode(mode)
        self._acquisition_mode = mode

    def start_acquisition(self):
        """
        Start Acquisition Mode
        """
        self._ser.StartAcquisition()
        self._ser.WaitForAcquisition()

    def stop_acquisition(self):
        """
        Stop Acquisition Mode
        """
        self._ser.AbortAcquisition()

    def get_acquired_data(self, image_array=None):
        """
        Get last Image
        """
        if image_array is None:
            image_array = []

        # Get Number of Pixels
        if (self._read_mode, self._acquisition_mode) == (4, 1):
            n_pixel = self._image_width * self._image_height / self._image_height_bin_size / self._image_width_bin_size
        elif (self._read_mode, self._acquisition_mode) == (4, 3):
            n_pixel = self._image_width * self._image_height / self._image_height_bin_size / \
                      self._image_width_bin_size * self._scans
        elif (self._read_mode, self._acquisition_mode) in [(0, 1), (3, 1)]:
            n_pixel = self._image_width
        elif (self._read_mode, self._acquisition_mode) in [(0, 3), (3, 3)]:
            n_pixel = self._image_width * self._scans
        else:
            logging.warning(f"{self.NAME}: Could not get data: ReadMode or AcquisitionMode not set correctly")
            return

        n_pixel = int(n_pixel)
        ctypes_image_array = ctypes.c_int * n_pixel
        ctypes_image = ctypes_image_array()

        # Get Image
        self._ser.GetAcquiredData(ctypes.pointer(ctypes_image), ctypes.c_ulong(n_pixel))

        for i in range(len(ctypes_image)):
            image_array.append(ctypes_image[i])

        return image_array[:]

    def save_picture(self, file_name: str):
        """
        Save last Picture
        """
        if file_name.split('.')[-1] == 'npy':
            np.save(file_name, self.last_picture)
        else:
            logging.error(f"{self.NAME}: Could not save Picture. Format not supported")
            return

        logging.info(f"{self.NAME}: Saved Picture as '{file_name}.npy'")

    def set_trigger_mode(self, trigger_mode):
        """
        Set Trigger Mode
        """
        status = self._ser.SetTriggerMode(trigger_mode)
        logging.info(f"{self.NAME}: Send: SetTriggerMode({trigger_mode}), Status: {self.STATUS_CODES[status]}")

    def set_preamp_gain(self, preamp_gain):
        """
        Set PreAmp Gain
        """
        status = self._ser.SetPreAmpGain(preamp_gain)
        logging.info(f"{self.NAME}: Send: SetPreAmpGain({preamp_gain}), Status: {self.STATUS_CODES[status]}")

    def set_em_gain_mode(self, em_gain_mode):
        """
        Set EM Gain Mode
        """
        status = self._ser.SetEMGainMode(em_gain_mode)
        logging.info(f"{self.NAME}: Send: SetEMGainMode({em_gain_mode}), Status: {self.STATUS_CODES[status]}")

    def set_vs_speed(self, vs_speed):
        """
        Set VS Speed
        """
        status = self._ser.SetVSSpeed(vs_speed)
        logging.info(f"{self.NAME}: Send: SetVSSpeed({vs_speed}), Status: {self.STATUS_CODES[status]}")

    def set_baseline_clamp(self, baseline_clamp):
        """
        Set Baseline Clamp
        """
        status = self._ser.SetBaselineClamp(baseline_clamp)
        logging.info(f"{self.NAME}: Send: SetBaselineClamp({baseline_clamp}), Status: {self.STATUS_CODES[status]}")

    def set_exposure_time(self, exposure_time):
        """
        Set Exposure Time
        """
        status = self._ser.SetExposureTime(ctypes.c_float(exposure_time))
        self._exposure_time = exposure_time
        logging.info(f"{self.NAME}: Send: SetExposureTime({exposure_time}), Status: {self.STATUS_CODES[status]}")

    def get_exposure_time(self):
        """
        Get Exposure Time
        """
        return self._exposure_time

    def set_gain_mode(self, gain_mode):
        """
        Set EMCCD Gain Mode
        """
        status = self._ser.SetEMCCDGainMode(gain_mode)
        logging.info(f"{self.NAME}: Send: SetGainMode({gain_mode}), Status: {self.STATUS_CODES[status]}")

    def get_emccd_gain(self):
        """
        Get EMCCD Gain
        """
        gain = ctypes.c_int()
        status = self._ser.GetEMCCDGain(ctypes.byref(gain))
        self._emccd_gain = gain.value
        logging.info(f"{self.NAME}: Recv: GetEMCCDGain({gain.value}), Status: {self.STATUS_CODES[status]}")
        return gain.value

    def set_emccd_gain(self, gain):
        """
        Set EMCCD Gain
        """
        status = self._ser.SetEMCCDGain(gain)
        self._emccd_gain = gain
        logging.info(f"{self.NAME}: Send: SetEMCCDGain({gain}), Status: {self.STATUS_CODES[status]}")

    def get_emccd_gain_range(self):
        """
        Get EMCCD Gain Range
        """
        lowest = ctypes.c_int()
        highest = ctypes.c_int()
        status = self._ser.GetEMGainRange(ctypes.byref(lowest), ctypes.byref(highest))
        self._gain_range = lowest.value, highest.value
        logging.info(f"{self.NAME}: Recv: GetEMGainRange({self._gain_range}), Status: {self.STATUS_CODES[status]}")
        return self._gain_range

    def set_cooler_on(self):
        """
        Turn Cooler On
        """
        status = self._ser.CoolerON()
        logging.info(f"{self.NAME}: Send: CoolerON(), Status: {self.STATUS_CODES[status]}")

    def set_cooler_mode(self, mode):
        """
        Set Cooler Mode 0 Off | 1 On
        """
        status = self._ser.SetCoolerMode(mode)
        logging.info(f"{self.NAME}: Send: SetCoolerMode({mode}), Status: {self.STATUS_CODES[status]}")

    def set_fan_mode(self, mode):
        """
        Set Fan Mode 0 Full | 1 Low | 2 Off
        """
        if mode == "Full":
            status = self._ser.SetFanMode(0)
        elif mode == "Low":
            status = self._ser.SetFanMode(1)
        elif mode == "Off":
            status = self._ser.SetFanMode(2)
        else:
            raise ValueError("Fan Mode has to be Full, Low or Off")
        self._fan_mode = mode
        logging.info(f"{self.NAME}: Send: SetFanMode({mode}), Status: {self.STATUS_CODES[status]}")

    def get_fan_mode(self):
        """
        Get Fan Mode
        """
        return self._fan_mode

    def get_cooler_status(self):
        """
        Get Cooler Status
        """
        cooler_status = ctypes.c_int()
        status = self._ser.IsCoolerOn(ctypes.byref(cooler_status))
        logging.info(f"{self.NAME}: Recv: IsCoolerOn({cooler_status.value}), Status: {self.STATUS_CODES[status]}")
        return cooler_status.value

    def get_temperature(self):
        """
        Get Current Temperature in °C
        """
        temperature = ctypes.c_int()
        self._ser.GetTemperature(ctypes.byref(temperature))
        return temperature.value

    def set_target_temperature(self, temperature):
        """
        Set Desired Temperature in °C
        """
        self._ser.SetTemperature(temperature)
        self._target_temperature = temperature

    def get_target_temperature(self):
        """
        Get Desired Temperature in °C
        """
        return self._target_temperature

    def take_picture(self, exposure_time=None, emccd_gain=None, shutter=(1, 5, 30, 5), accumulations=1, resize=False,
                     dimensions=None):
        """
        Take Picture
        """
        # TODO: fix gain setting
        if exposure_time is None:
            exposure_time = self._exposure_time
        if emccd_gain is None:
            emccd_gain = self._emccd_gain
        if dimensions is None:
            dimensions = self.resize_dimensions

        # Settings
        self.set_exposure_time(exposure_time)
        self.set_emccd_gain(emccd_gain)
        self.set_image(1, 1, 1, self._image_width, 1, self._image_height)
        self.set_acquisition_mode(1)
        self.set_read_mode(4)
        self.set_shutter(*shutter)

        # Take Picture
        if accumulations == 1:
            self.start_acquisition()
            image = np.array(self.get_acquired_data())
            self.stop_acquisition()

        elif accumulations > 1:
            image = np.empty((self._image_width*self._image_height))
            for i in range(int(accumulations)):
                self.start_acquisition()
                image += np.array(self.get_acquired_data())
                self.stop_acquisition()

        else:
            logging.error(f"{self.NAME}: Could not take Picture. '{accumulations}=' has to be >0")
            return np.zeros((self._image_height, self._image_width))

        # Reshape, Flip and Resize
        image = np.reshape(image, (self._image_height, -1))
        image = np.flip(image, axis=1)
        image = image - 300 * accumulations
        if resize:
            image = image[dimensions[0]:dimensions[1], dimensions[2]:dimensions[3]]
        self.last_picture = image

        return image

    def gui_open(self):
        self.app = CameraAndorWindow(self)


class CameraAndorWindow(QWidget):
    def __init__(self, device: CameraAndor):
        super().__init__()
        self.device = device

        self.setWindowTitle(f"{self.device.NAME}")
        self.setGeometry(100, 100, 1700, 900)

        self._cam_pic_canvas = pg.ImageView()
        self._cam_pic_canvas.clear()
        if self.device.last_picture is not None:
            self._cam_pic_canvas.setImage(self.device.last_picture)

        self._label_pic_info = QLabel()
        self._label_temperature = QLabel()

        self._line_edit_exposure_time = DelayedDoubleSpinBox()
        self._line_edit_exposure_time.setValue(self.device.get_exposure_time())
        self._combo_box_cooling_mode = QComboBox()
        self._combo_box_cooling_mode.addItems(["Full", "Low", "Off"])
        self._combo_box_cooling_mode.setCurrentText(self.device.get_fan_mode())
        self._line_edit_target_temperature = DelayedDoubleSpinBox()
        self._line_edit_target_temperature.setValue(self.device.get_target_temperature())

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
        self.device.set_fan_mode(self._combo_box_cooling_mode.currentText())

    @pyqtSlot()
    def _refresh_values(self):
        self._label_temperature.setText(str(self.device.get_temperature()))

    @pyqtSlot()
    def _refresh_picture(self):
        pic = self.device.take_picture()
        self._cam_pic_canvas.clear()
        self._cam_pic_canvas.setImage(pic)
        self._label_pic_info.setText(f"Max: {np.max(pic)}\nSum: {pic.sum()}")
        # self._label_pic_info.setText(f"Max: {pic.max()}\nSum: {pic.sum()}")

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
