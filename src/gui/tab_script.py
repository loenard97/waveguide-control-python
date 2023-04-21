import os
import re
import sys
import inspect
import logging
import importlib
import traceback

import numpy as np
from PyQt6.QtCore import Qt, pyqtSlot, QSettings
from PyQt6.QtWidgets import QPushButton, QLineEdit, QLabel, QHBoxLayout, QComboBox, QWidget, QFormLayout, QTableView, \
    QVBoxLayout, QCheckBox, QGridLayout, QMessageBox, QStyle, QFrame, QTextEdit

from src.static_gui_elements.table_model import TableModel


class ScriptTab(QWidget):

    def __init__(self, main_window, flags=Qt.WindowType.Widget):
        # Settings
        super().__init__(main_window, flags)
        self._main_window = main_window
        self.measurement_pointer = None
        self.folders = [name for name in os.listdir("scripts") if os.path.isdir(os.path.join("scripts", name))
                        and not name.startswith("_")]

        directory = QSettings().value("tab_script/directory")
        measurement = QSettings().value("tab_script/measurement")

        # Folder and Measurement Combo Boxes
        self._layout_combo_boxes = QFormLayout()
        self._cb_directory = QComboBox()
        for folder in self.folders:
            self._cb_directory.addItem(folder)
        if directory:
            self._cb_directory.setCurrentText(directory)
        self._cb_directory.currentIndexChanged.connect(self._handle_cb_directory_changed)    # NOQA
        self._layout_combo_boxes.addRow(QLabel("<b>Folder</b>"), self._cb_directory)
        self._cb_script = QComboBox()
        if measurement:
            self._cb_script.setCurrentText(measurement)    # TODO: load script names before this
        self._cb_script.currentIndexChanged.connect(self._handle_cb_script_changed)    # NOQA
        self._layout_combo_boxes.addRow(QLabel("<b>Script</b>"), self._cb_script)

        # Iterator Table
        self._cb_iterators = QComboBox()
        self._tv_iterators = QTableView()
        self._tm_iterators = TableModel(header=["Variable", "Iterator"], data_types=[str, str])
        self._tm_iterators.dataChanged.connect(self._save_settings)    # NOQA
        self._tv_iterators.setModel(self._tm_iterators)

        # Total Layout
        self._layout = QVBoxLayout()
        self._widget_bottom = QWidget()
        self._layout.addLayout(self._layout_combo_boxes)
        self._layout.addWidget(self._widget_bottom)
        self.setLayout(self._layout)

        # Refresh to initialize
        self._handle_cb_directory_changed()
        self._handle_cb_script_changed()

    @property
    def directory(self) -> str:
        """
        Get currently selected script directory
        """
        return self._cb_directory.currentText()

    @property
    def script(self) -> str:
        """
        Get currently selected script
        """
        return self._cb_script.currentText()

    @property
    def script_path(self) -> str:
        """
        Get File Path of currently selected script
        """
        return os.path.join(os.getcwd(), "scripts", self._cb_directory.currentText(), self._cb_script.currentText())

    @property
    def parameters(self) -> dict:
        """
        Get parameters for current script
        """
        params = {}
        for widget in (self.form_layout_parameters.itemAt(i) for i in range(0, self.form_layout_parameters.count(), 2)):
            try:
                params[widget.widget().text()] = float(widget.widget().buddy().text().replace(',', '.'))    # NOQA
            except ValueError:
                params[widget.widget().text()] = 0.0   # NOQA
        return params

    @property
    def comment(self) -> str:
        """
        Get comment for current script
        """
        return self.text_edit_comment.toPlainText()

    @property
    def iterators_str(self) -> list:
        """
        Get iterators for current script as list of strings
        """
        return self._tm_iterators.getData()

    @staticmethod
    def _iterator_str_to_array(iter_str):
        """
        Convert Iterator String to Numpy Array
        """
        try:
            return float(iter_str)  # iterator is single number
        except ValueError:  # iterator is range of data points
            value = re.split('[/;]', iter_str)
            start = float(value[0])
            stop = float(value[1])
            if len(value) == 3:
                step = float(value[2])
            else:
                step = 1
            n_points = int(round((stop - start) / step + 1))
            stop = start + ((n_points - 1) * step)
            return np.linspace(start, stop, n_points)

    @property
    def iterators_array(self) -> list:
        """
        Get Numpy Arrays from Current Iterators
        """
        # All Whitespace Characters are ignored
        # Comma separated List (eg '1,2,3,4' = 1,2,3,4) is seen as individual data points
        # Slash means range of values with semicolon for step size (eg 0/10;2 = 0,2,4,6,8,10)
        # No Semicolon with Range of Values means Range 1 (eg 0/5 = 0,1,2,3,4,5)
        # Multiple Segments can be appended together (eg 0/4,10,15 = 0,1,2,3,4,10,15)

        if not self.iterators_str:
            return [("Iterator", np.array([1]))]

        iterators_list = []
        for iter_name, iter_str in self.iterators_str:
            current_iterator = np.empty(0)
            for segment in ''.join(iter_str.split()).split(','):  # remove whitespace characters
                try:
                    current_iterator = np.append(current_iterator, self._iterator_str_to_array(segment))
                except ValueError:
                    QMessageBox.critical(
                        self._main_window, "Error",
                        f"The Iterator '{iter_name}': '{iter_str}' is not a List or a Range of Numbers.")
                    return []
            if self.options["Randomize Iterators"]:
                np.random.shuffle(current_iterator)
            iterators_list.append((iter_name, current_iterator))
        return iterators_list

    @property
    def options(self) -> dict:
        """
        Get selected Options
        """
        return {"Randomize Iterators": self.checkbox_randomize.isChecked()}

    @pyqtSlot()
    def _handle_cb_directory_changed(self):
        """
        Refresh Combo Box Measurements.
        Gets called when new Folder is selected.
        """
        self._cb_script.clear()
        for name, folder, files in os.walk(os.path.join("scripts", self.directory)):
            for file in files:
                if not file.startswith("_") and file.endswith(".py"):
                    file_path = str.join("", name.split(os.sep)[2:])
                    self._cb_script.addItem(os.path.join(file_path, file))
        self._save_settings()

    @pyqtSlot()
    def _handle_cb_script_changed(self):
        """
        Refresh Parameters and Iterator Label when different Measurement is selected
        """
        # Import Module of Selected Measurement
        directory = self._cb_directory.currentText()
        measurement = self._cb_script.currentText()
        if not measurement:
            return

        module_name = "scripts." + directory + "." + measurement.replace(os.sep, ".")[:-3]
        if module_name in sys.modules:
            logging.debug(f"Parameter Tab: Reloading Module {module_name}")
            importlib.reload(sys.modules[module_name])
        else:
            logging.debug(f"Parameter Tab: Importing Module {module_name}")
            try:
                importlib.import_module(module_name)
            except (ModuleNotFoundError, SyntaxError) as err:
                logging.error(f"Tab Parameter: Could not load Module {module_name}. Error: '{err}'")
                QMessageBox.critical(
                    self._main_window, "Error",
                    f"A fatal error occurred while trying to load the Measurement '{module_name}':\n\n"
                    f"Error Message: {err}\n\n"
                    f"{traceback.format_exc()}")
                return

        for _, obj in inspect.getmembers(sys.modules[module_name], inspect.isclass):
            parent_folder = str(obj).split('.')[0][8:]
            if parent_folder == "scripts":
                try:
                    self.measurement_pointer = obj(self._main_window, self._main_window.devices)
                except BaseException as err:
                    logging.error(f"Parameter Tab: Could not load Module '{module_name}'. Error: '{err}'")
                    QMessageBox.critical(
                        self._main_window, "Error",
                        f"A fatal error occurred while trying to load the Measurement '{module_name}':\n\n"
                        f"Error Message: {err}\n\n"
                        f"{traceback.format_exc()}")
                    return
                logging.debug(f"Loading Measurement {self.measurement_pointer}")

        if self.measurement_pointer is None:
            logging.error(f"Parameter Tab: Could not load Module '{module_name}'. self.measurement_pointer is None")
            QMessageBox.critical(
                self._main_window, "Error",
                f"Could not load the Script '{module_name}'. It seems like the script is empty.")
            return

        logging.debug(f"Parameter Tab: Loaded Measurement '{self.measurement_pointer}'")

        # Load Settings
        settings_dict = {}
        default_parameters = {}
        settings_path = "script/" + self.directory + '/' + self.script
        for param in self.measurement_pointer.parameters:
            default_parameters[param] = None
        settings_dict["options"] = QSettings().value("tab_script/options", False)
        settings_dict["parameters"] = QSettings().value(settings_path+"parameters", default_parameters)
        settings_dict["comment"] = QSettings().value(settings_path+"comment", "Empty space for comments...")
        settings_dict["iterators"] = QSettings().value(settings_path+"iterators", [])

        # Load Iterators into Table
        self._tm_iterators.resetData()
        if settings_dict["iterators"]:
            for iterator in settings_dict["iterators"]:
                self._tm_iterators.appendRow(iterator)

        # ------ Start building new Widget ------ #
        # Parameter Form Layout
        layout_parameters_new = QFormLayout()
        if settings_dict["parameters"]:
            for key, value in settings_dict["parameters"].items():
                line_edit = QLineEdit()
                line_edit.setText(str(value))
                line_edit.setFixedSize(100, 19)
                line_edit.textChanged.connect(self._save_settings)    # NOQA
                layout_parameters_new.addRow(str(key), line_edit)
        self.form_layout_parameters = layout_parameters_new

        separator_horizontal = QFrame()
        separator_horizontal.setFrameShape(QFrame.Shape.HLine)
        separator_horizontal.setFrameShadow(QFrame.Shadow.Sunken)

        # Comments Text Edit
        self.text_edit_comment = QTextEdit()
        self.text_edit_comment.setText(settings_dict["comment"])
        self.text_edit_comment.textChanged.connect(self._save_settings)    # NOQA

        # Layout Left Side
        layout_left_new = QVBoxLayout()
        layout_left_new.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_left_new.addWidget(QLabel("<b>Parameters</b>"))
        layout_left_new.addLayout(layout_parameters_new)
        layout_left_new.addWidget(separator_horizontal)
        layout_left_new.addWidget(QLabel("<b>Comments</b>"))
        layout_left_new.addWidget(self.text_edit_comment)

        # Separator
        separator_vertical = QFrame()
        separator_vertical.setFrameShape(QFrame.Shape.VLine)
        separator_vertical.setFrameShadow(QFrame.Shadow.Sunken)

        # Layout Middle
        layout_middle_new = QVBoxLayout()

        # Iterator Widget
        self._cb_iterators = QComboBox()
        if self.parameters:
            self._cb_iterators.addItem("Iterator")
            for key, value in self.parameters.items():
                self._cb_iterators.addItem(key)

        # Buttons
        layout_iterator_buttons = QGridLayout()
        button_add_iterator = QPushButton("Add Iterator")
        button_add_iterator.clicked.connect(self._handle_button_add_iterator)    # NOQA
        layout_iterator_buttons.addWidget(button_add_iterator, 1, 1)
        button_delete_iterator = QPushButton("Remove Iterator")
        button_delete_iterator.clicked.connect(self._handle_button_delete_iterators)    # NOQA
        layout_iterator_buttons.addWidget(button_delete_iterator, 1, 2)
        layout_iterator_buttons.addWidget(QLabel("<b>Iterators</b>"), 0, 0)
        label_help_icon = QLabel()
        icon = self.style().standardIcon(QStyle.StandardPixmap.SP_MessageBoxQuestion)
        label_help_icon.setPixmap(icon.pixmap(14))
        label_help_icon.setToolTip(
            "An Iterator has to be a String with the following formatting:\n"
            " - All Whitespace Characters are ignored\n"
            " - Commas (,) separate individual Data Points\n"
            " - A Range of Data Points can be set with a Slash (/), with an optional Step Size after a Semicolon (;)"
        )
        layout_iterator_buttons.addWidget(label_help_icon, 0, 1)
        layout_iterator_buttons.addWidget(self._cb_iterators, 1, 0)

        layout_middle_new.addLayout(layout_iterator_buttons)
        layout_middle_new.addWidget(self._tv_iterators)

        # Layout Right
        layout_right_new = QVBoxLayout()
        layout_right_new.addWidget(QLabel("<b>Additional Options</b>"))
        layout_right_new.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.checkbox_randomize = QCheckBox("Randomize Iterators")
        self.checkbox_randomize.clicked.connect(self._save_settings)    # NOQA
        layout_right_new.addWidget(self.checkbox_randomize)

        # Total Layout
        widget_new = QWidget()
        layout_new = QHBoxLayout()
        layout_new.addLayout(layout_left_new)
        layout_new.addWidget(separator_vertical)
        layout_new.addLayout(layout_middle_new)
        layout_new.addLayout(layout_right_new)
        widget_new.setLayout(layout_new)

        # Replace old Widget
        self._layout.replaceWidget(self._widget_bottom, widget_new)
        self._widget_bottom.hide()
        self._widget_bottom.destroy()
        self._widget_bottom = widget_new

        # Save Settings
        self._save_settings()

    @pyqtSlot()
    def _save_settings(self):
        """
        Save current Settings
        """
        settings_path = "script/" + self.directory + '/' + self.script
        try:
            QSettings().setValue("tab_script/directory", self.directory)
            QSettings().setValue("tab_script/measurement", self.script)
            QSettings().setValue("tab_script/options", self.options)
            QSettings().setValue(settings_path + "parameters", self.parameters)
            QSettings().setValue(settings_path + "comment", self.comment)
            QSettings().setValue(settings_path + "iterators", self.iterators_str)
        except AttributeError:
            pass

    @pyqtSlot()
    def _handle_button_add_iterator(self):
        """
        Add new Iterator to Table
        """
        self._tm_iterators.appendRow([self._cb_iterators.currentText(), "<empty>"])
        self._save_settings()

    @pyqtSlot()
    def _handle_button_delete_iterators(self):
        """
        Delete all selected Iterators from Table
        """
        rows = []
        rows_sorted = []
        for e in self._tv_iterators.selectionModel().selectedRows():
            rows.append(e.row())  # get all rows of selected rows
        for e in self._tv_iterators.selectionModel().selectedIndexes():
            rows.append(e.row())  # get all rows of selected items
        [rows_sorted.append(x) for x in rows if x not in rows_sorted]  # remove duplicates
        rows_sorted.sort(reverse=True)  # sort list
        for row in rows_sorted:
            self._tm_iterators.removeRow(row)
        self._save_settings()
