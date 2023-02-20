import os
import logging
import datetime
import numpy as np
import pyqtgraph as pg

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QVBoxLayout, QProgressBar, QLabel

from src.static_gui_elements.plot_widget import PlotWidget


class MeasurementTab(QWidget):
    """
    Tab Measurement
    Start / Stop Buttons, Variable Plots and Progress Bar
    """

    def __init__(self, main_window, flags=Qt.WindowType.Widget):
        super().__init__(main_window, flags)
        self._main_window = main_window

        # Buttons
        widget_buttons = QWidget()
        layout_buttons = QHBoxLayout()
        button_start = QPushButton()
        button_start.setIcon(QIcon(os.path.join("src", "images", "start.svg")))
        button_start.clicked.connect(self._handle_button_start)    # NOQA
        layout_buttons.addWidget(button_start, alignment=Qt.AlignmentFlag.AlignCenter)
        button_stop = QPushButton()
        button_stop.setIcon(QIcon(os.path.join("src", "images", "stop.svg")))
        button_stop.clicked.connect(self._handle_button_stop)    # NOQA
        layout_buttons.addWidget(button_stop, alignment=Qt.AlignmentFlag.AlignCenter)
        widget_buttons.setLayout(layout_buttons)

        # Plots
        self._plots_observables = {}
        self._plots_variables_widget = QWidget()

        # Progress Bar
        widget_progress = QWidget()
        layout_progress = QVBoxLayout()
        self._progress_bar = QProgressBar(self)
        self._progress_bar_label = QLabel()
        layout_progress.addWidget(self._progress_bar)
        layout_progress.addWidget(self._progress_bar_label)
        widget_progress.setLayout(layout_progress)

        # Layout
        self._layout = QVBoxLayout()
        self._layout.addWidget(widget_buttons, alignment=Qt.AlignmentFlag.AlignTop)
        self._layout.addWidget(self._plots_variables_widget)
        self._layout.addWidget(widget_progress)
        self.setLayout(self._layout)

    def initialize_plots(self):
        """
        Initialize all Plot Widgets.
        Gets called by Measurement Class when Measurement starts.
        """
        measurement = self._main_window.tab_script.measurement_pointer

        # ----- Variable Plots ----- #
        # New Widget
        new_widget = QWidget()
        new_layout = QHBoxLayout()
        new_widget.setLayout(new_layout)

        # Create one Plot per Variable in Data Container
        self._plots_observables = {}
        for observable_name, observable_dict in measurement.observables.items():
            if not observable_dict["plot"]:
                continue

            if observable_dict["data_format"] == "float":
                plot_widget = PlotWidget()
                plot_widget.set_labels(measurement.iterators_list[0][0], observable_name)
                self._plots_observables[observable_name] = plot_widget
                new_layout.addWidget(plot_widget)

            elif observable_dict["data_format"] == "image":
                plot_item = pg.PlotItem(enableMenu=False)
                image_item = pg.ImageItem()
                color_bar = pg.ColorBarItem(interactive=False)
                plot_widget = pg.PlotWidget(plotItem=plot_item)
                plot_dict = {
                    "plot_item": plot_item,
                    "image_item": image_item,
                    "color_bar": color_bar,
                    "plot_widget": plot_widget
                }
                self._plots_observables[observable_name] = plot_dict
                new_layout.addWidget(plot_widget)

            elif observable_dict["data_format"] == "histogram":
                plot_widget = PlotWidget()
                plot_widget.set_labels("Index / ps", "Counts")
                self._plots_observables[observable_name] = plot_widget
                new_layout.addWidget(plot_widget)

        # Replace old Widget
        self._layout.replaceWidget(self._plots_variables_widget, new_widget)
        self._plots_variables_widget.hide()
        self._plots_variables_widget.destroy()
        self._plots_variables_widget = new_widget

    def redraw_plots(self):
        """
        Redraw all Plots when one Data Point is finished
        """
        measurement = self._main_window.tab_script.measurement_pointer
        pos_2 = measurement.current_point // len(measurement.iterators_list[0][1])

        # Redraw Variable Plots
        for index, (observable_name, observable_dict) in enumerate(measurement.observables.items()):
            if not observable_dict["plot"]:
                continue

            if observable_dict["data_format"] == "float":
                self._plots_observables[observable_name].plot_data(
                    x_data=measurement.iterators_list[0][1], y_data=observable_dict["data"][str(pos_2)],
                    color=observable_dict["plot_color"])

            elif observable_dict["data_format"] == "image":
                self._plots_observables[observable_name]["image_item"].setImage(observable_dict["data"])
                try:
                    self._plots_observables[observable_name]["image_item"].setColorMap(
                        pg.colormap.get(observable_dict["plot_color_map"]))
                except FileNotFoundError:
                    logging.warning(f"Image Plot Widget: Could not find Color Map "
                                    f"'{observable_dict['plot_color_map']}'")
                self._plots_observables[observable_name]["plot_item"].clear()
                self._plots_observables[observable_name]["plot_item"].addItem(
                    self._plots_observables[observable_name]["image_item"])
                if observable_dict["plot_color_bar"]:
                    self._plots_observables[observable_name]["color_bar"].setLevels(
                        low=np.min(observable_dict["data"]), high=np.max(observable_dict["data"]))
                    self._plots_observables[observable_name]["color_bar"].setImageItem(
                        self._plots_observables[observable_name]["image_item"],
                        insert_in=self._plots_observables[observable_name]["plot_item"])

            elif observable_dict["data_format"] == "histogram":
                self._plots_observables[observable_name].plot_data(
                    x_data=list(observable_dict["data"].values())[-1]["index"],
                    y_data=list(observable_dict["data"].values())[-1]["data"],
                    color=observable_dict["plot_color"])

        # Progress Bar and Label
        percentage = 100 * measurement.current_point / measurement.number_points
        time_start = measurement.timestamps[0]
        time_now = measurement.timestamps[measurement.current_point]
        runtime = int(time_now - time_start)
        if percentage != 0:
            total_runtime = int(runtime / percentage * 100)
        else:
            total_runtime = 0
        eta = datetime.datetime.fromtimestamp(time_start + total_runtime)
        if measurement.flag_stop:
            self._progress_bar_label.setText("Measurement Stopped")
        else:
            self._progress_bar.setValue(int(percentage))
            self._progress_bar_label.setText(
                f"Percentage: {int(percentage)}%, "
                f"Current Runtime: {datetime.timedelta(seconds=runtime)}, "
                f"Estimated Total Runtime: {datetime.timedelta(seconds=total_runtime)}, "
                f"Estimated Remaining Runtime: {datetime.timedelta(seconds=total_runtime - runtime)}, "
                f"ETA: {eta:%d-%m-%Y %H:%M:%S}")

    @pyqtSlot()
    def _handle_button_start(self):
        """
        Start Measurement
        """
        logging.info("Starting Measurement: Start Button pressed")
        self._main_window.tab_script.measurement_pointer.measure()

    @pyqtSlot()
    def _handle_button_stop(self):
        """
        Stop Measurement
        """
        logging.info("Stopping Measurement: Stop Button pressed")
        self._main_window.tab_script.measurement_pointer.flag_stop = True
