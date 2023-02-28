import os
import yaml
import logging
import importlib

from PyQt6.QtCore import Qt, pyqtSlot, QEvent, QSettings, QSize, QPoint
from PyQt6.QtGui import QIcon, QAction
from PyQt6.QtWidgets import QMainWindow, QTabWidget, QMessageBox

from src.gui.tab_camera import CameraTab
from src.gui.tab_script import ScriptTab
from src.gui.tab_measurement import MeasurementTab


class MainWindow(QMainWindow):
    """
    Main Window of the GUI
    """

    def __init__(self):
        super().__init__(flags=Qt.WindowType.Window)

        # Window Appearance
        self.resize(QSettings().value("main_window/size", QSize(1400, 700)))
        self.move(QSettings().value("main_window/position", QPoint(300, 150)))
        self.setWindowIcon(QIcon(os.path.join("src", "images", "icon.svg")))

        # Connect to Devices
        devices_dict = {}
        self.devices = {}
        failed_connections = ''
        if os.path.exists("devices.yaml"):
            with open("devices.yaml", 'r') as file:
                devices_dict = yaml.load(file, Loader=yaml.FullLoader)
        for name, args in devices_dict.items():
            try:
                logging.info(f"Main Window: Connecting to '{name}' at '{args['Address']}'.")
                device_class = getattr(importlib.import_module(f"src.devices.{args['File']}"), args['Class'])
                self.devices[args["Handle"]] = device_class(name, args["Address"], args.get("Settings"))
                logging.log(level=100, msg=f"Main Window: Connected to '{name}' at '{args['Address']}'.")

            except Exception as err:
                logging.error(f"Main Window: Could not connect to {name}. Error: '{err}'.")
                failed_connections += name + ', '

        # Show Warning for failed Connections
        if failed_connections:
            QMessageBox.critical(self, "Error", f"Could not connect to the following devices:\n\n"
                                                f"{failed_connections[:-2]}\n\n")

        # Add Tabs to Central Widget
        self.centralWidget = QTabWidget()
        self.tab_camera = CameraTab(self)
        self.tab_script = ScriptTab(self)
        self.tab_measurement = MeasurementTab(self)
        self.centralWidget.addTab(self.tab_camera, "Camera / Stage")
        self.centralWidget.addTab(self.tab_script, "Script")
        self.centralWidget.addTab(self.tab_measurement, "Measurement")
        self.setCentralWidget(self.centralWidget)

        # Device Menu
        menu_device = self.menuBar().addMenu('&Devices')
        for key, value in self.devices.items():
            action = QAction(value.name + '...', self)
            try:
                action.triggered.connect(value.gui_open)    # NOQA
            except AttributeError:
                logging.error(f"Main Window: '{value.name}' has no attribute 'gui_open'")
            menu_device.addAction(action)

        self.show()

    @pyqtSlot()
    def closeEvent(self, event: QEvent):
        """
        Close Main Window
        """
        logging.log(level=100, msg="Shutting down Main Window")

        # Disconnect from all Devices
        for name, device in self.devices.items():
            try:
                device.disconnect()
            except AttributeError:
                logging.info(f"Main Window: '{name}' has no 'disconnect' function.")

        # Save Settings
        QSettings().setValue("main_window/size", self.size())
        QSettings().setValue("main_window/position", self.pos())
        QSettings().sync()

        event.accept()
