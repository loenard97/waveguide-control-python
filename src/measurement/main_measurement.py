import os
import re
import h5py
import logging
import datetime
import subprocess
import numpy as np

from PyQt6.QtWidgets import QMessageBox

from src.gui.main_window import MainWindow
from src.measurement.pulse_sequence import Sequence
from src.static_functions.wait import event_loop_interrupt
from src.static_functions.parse_traceback import parse_traceback


class Measurement:
    name = "Name not defined"
    parameters = []

    def __init__(self, main_window: MainWindow, devices_dict: dict):
        self._main_window = main_window

        self.iterators_list = []
        self.number_points = 1
        self.parameters_dict = {}
        self.pulse_sequence = {}
        self.observables = {}
        self.current_point = 0
        self.flag_stop = False
        self.save_file_path = None
        self.timestamps = None

        # Setup Devices as Attributes
        self.devices = {}
        for key, device in devices_dict.items():
            setattr(self, key, device)
            self.devices[key] = device

    def measure(self):
        """
        Setup and run Measurement
        """
        # Reset Variables
        self.observables = {}
        self.current_point = 0
        self.flag_stop = False

        # Get Iterators and Parameters from Script Tab
        self.iterators_list = self._main_window.tab_script.iterators_array
        if not self.iterators_list:     # abort when iterators are not set correctly
            return
        self.parameters_dict = self._main_window.tab_script.parameters

        # Setup Timestamps
        self.number_points = 1
        for iterator in self.iterators_list:
            self.number_points *= len(iterator[1])
        self.timestamps = np.zeros(self.number_points)

        # Setup Save File
        measurement_name = re.sub(r"[ ./\\]", '', self.name).casefold()
        self.save_file_path = os.path.join(os.getcwd(), "data",
                                           f"{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}_{measurement_name}")
        if not os.path.isdir(self.save_file_path):
            os.makedirs(self.save_file_path)
        with h5py.File(os.path.join(self.save_file_path, "raw_data.h5"), 'a') as file:
            file.create_group("Meta Info")
            file.create_group("Iterators")
            file.create_group("Observables")

        # Execute Setup Function of Measurement
        logging.info(f"{self.name}: Starting Setup Function")
        try:
            self.setup_measurement(self.parameters_dict)    # NOQA
        except Exception as err:
            logging.error(f"{self.name}: Error during Setup of Script: '{err}'")
            file, line, line_number = parse_traceback()
            QMessageBox.critical(
                self._main_window, "Error",
                "A fatal error occurred during the Setup of the Measurement:\n\n"
                f"Error Message: '{err}'\n\n"
                f"in Script '{file}' at Line {line_number} during:\n"
                f"{line}")
            return
        self._main_window.tab_measurement.initialize_plots()

        # Run Measurement
        logging.info(f"{self.name}: Starting Run Measurement Function")
        self.iterate_measurement(self.parameters_dict, self.iterators_list, len(self.iterators_list) - 1)
        # self.main_window.tab_measurement.redraw_plots()   # TODO: fix
        self.save_data()

        # Shutdown Measurement
        logging.info(f"{self.name}: Starting Shutdown Function")
        try:
            self.shutdown_measurement(self.parameters_dict)    # NOQA
        except Exception as err:
            logging.error(f"{self.name}: Error during Setup of Script: '{err}'")
            file, line, line_number = parse_traceback()
            QMessageBox.critical(
                self._main_window, "Error",
                "A fatal error occurred during the Setup of the Measurement:\n\n"
                f"Error Message: '{err}'\n\n"
                f"in Script '{file}' at Line {line_number} during:\n"
                f"{line}")

    def iterate_measurement(self, var_dict: dict, iterators_array: list, index: int):
        """
        Recursively start one Loop for every Iterator
        """
        for iterator_value in iterators_array[index][1]:
            # Abort if Stop Button is Pressed
            if self.flag_stop:
                return

            # Overwrite Variable Values with Current Iterator Value
            var_dict[iterators_array[index][0]] = iterator_value

            # Recursion Statement (index > 0)
            if index > 0:
                self.iterate_measurement(var_dict, iterators_array, index - 1)

            # Break Statement (Reached last Iterator, e.g. index = 0)
            else:
                try:
                    self.run_measurement(var_dict)    # NOQA
                except Exception as error:
                    logging.error(f"{self.name}: Error during Measurement: '{error}'")
                    file, line, line_number = parse_traceback()
                    QMessageBox.critical(
                        self._main_window, "Error",
                        "A fatal error occurred during the Setup of the Measurement:\n\n"
                        f"Error Message: '{error}'\n\n"
                        f"in Script '{file}' at Line {line_number} during:\n"
                        f"{line}")
                    self.flag_stop = True
                    return

                # Save Data and redraw Plots after every Data Point
                self.timestamps[self.current_point] = datetime.datetime.timestamp(datetime.datetime.now())
                self._main_window.tab_measurement.redraw_plots()
                self.current_point += 1

    def add_observable(self, name: str, save=True, data_format="float", plot=True, plot_color="green",
                       plot_color_map="inferno", plot_color_bar=True, plot_windowed=False):
        """
        Add new Observable
        """
        # TODO: add counter
        assert data_format in ["float", "image", "histogram"], "data_format has to be 'float', 'image' or 'histogram'"

        # save all settings in dict
        attributes_dict = locals()
        attributes_dict.pop("self")
        attributes_dict["data"] = {}
        self.observables[name] = attributes_dict

    def add_data_point(self, observable: str, data):
        """
        Add Data Point to Observable
        :param str observable: Name
        :param data: Data Point
        """
        assert observable in self.observables, f"Observable '{observable}' does not exist."

        pos_1 = self.current_point % len(self.iterators_list[0][1])
        pos_2 = self.current_point // len(self.iterators_list[0][1])

        if self.observables[observable]["data_format"] == "float":
            if str(pos_2) not in self.observables[observable]["data"]:
                self.observables[observable]["data"][str(pos_2)] = np.zeros(shape=len(self.iterators_list[0][1]))
            self.observables[observable]["data"][str(pos_2)][pos_1] = data

        elif self.observables[observable]["data_format"] == "histogram":
            self.observables[observable]["data"][f"{pos_1}_{pos_2}"] = {}
            self.observables[observable]["data"][f"{pos_1}_{pos_2}"]["data"] = data.getData()
            self.observables[observable]["data"][f"{pos_1}_{pos_2}"]["index"] = data.getIndex()

    def set_pulse_sequence(self, name, *pulses):
        """
        Set Pulse Sequence
        :param str name: Name of Sequence
        :param Low | High pulses: Comma separated list of Pulses
        """
        pulses_list = []
        for pulse in pulses:
            pulses_list.append(pulse)
        self.pulse_sequence[name] = Sequence(pulse_sequence=pulses_list)

    def save_data(self):
        """
        Save Data of Measurement
        """
        # Meta Info
        measurement_info = np.array([
            f"Folder: {self._main_window.tab_script.directory}",
            f"Script: {self._main_window.tab_script.script}",
            f"Name: {self.name}",
            f"Time Start: {datetime.datetime.fromtimestamp(self.timestamps[0]):%Y-%m-%d %H:%M:%S}",
            f"Time Stop: {datetime.datetime.fromtimestamp(self.timestamps[0]):%Y-%m-%d %H:%M:%S}",
        ], dtype='S')
        git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
        git_tag = subprocess.check_output(['git', 'describe', '--tags']).decode('ascii').strip()
        script_info = f"# ----- Measurement Script {self._main_window.tab_script.script_path} ----- #\n" \
                      f"# Script was executed with Software Version:\n" \
                      f"# Git Hash: {git_hash}\n" \
                      f"# Git Tag: {git_tag}\n\n\n"
        with open(self._main_window.tab_script.script_path, 'r') as script_file:
            script_info += script_file.read()
        script_info = np.array([script_info], dtype='S')
        iterators_info = []
        for name, value in self._main_window.tab_script.iterators_str:
            iterators_info.append(f"{name}: {value}")
        iterators_info = np.array(iterators_info, dtype='S')
        parameters_info = []
        for name, value in self.parameters_dict.items():
            parameters_info.append(f"{name}: {value}")
        parameters_info = np.array(parameters_info, dtype='S')
        comments_info = np.array([self._main_window.tab_script.text_edit_comment.toPlainText()], dtype='S')
        device_info = []
        for name, device in self.devices.items():
            device_info.append(f"{name}: {device.name} at {device.address}")
        device_info = np.array(device_info, dtype='S')

        with h5py.File(os.path.join(self.save_file_path, "raw_data.h5"), 'a') as file:
            file["Meta Info"].create_dataset(name="Measurement", data=measurement_info)
            file["Meta Info"].create_dataset(name="Script", data=script_info)
            file["Meta Info"].create_dataset(name="Iterators", data=iterators_info)
            file["Meta Info"].create_dataset(name="Parameters", data=parameters_info)
            file["Meta Info"].create_dataset(name="Comments", data=comments_info)
            file["Meta Info"].create_dataset(name="Devices", data=device_info)
            if self.flag_stop:
                file["Meta Info"].create_dataset(name="Abort Flag", data=["This Measurement was aborted."])

        # Iterators
        with h5py.File(os.path.join(self.save_file_path, "raw_data.h5"), 'a') as file:
            file["Iterators"].create_dataset(name="Timestamps", data=self.timestamps)
            for name, value in self.iterators_list:
                file["Iterators"].create_dataset(name=name.replace('/', 'in'), data=value, dtype='f')

        # Observables
        with h5py.File(os.path.join(self.save_file_path, "raw_data.h5"), 'a') as file:
            for observable_name, observable_dict in self.observables.items():
                if not observable_dict["save"]:
                    continue

                obs_name_safe = observable_name.replace('/', 'in')
                file["Observables"].create_group(obs_name_safe)

                if observable_dict["data_format"] == "float":
                    for name, arr in observable_dict["data"].items():
                        file["Observables"][obs_name_safe].create_dataset(
                            name=name, data=arr, dtype='f')

                elif observable_dict["data_format"] == "histogram":
                    for data, value in observable_dict["data"].items():
                        if observable_dict["data_format"] == "histogram":
                            file["Observables"][obs_name_safe].create_dataset(
                                name=data, data=value["data"], dtype='f')

    @staticmethod
    def wait(timeout):
        event_loop_interrupt(timeout)
