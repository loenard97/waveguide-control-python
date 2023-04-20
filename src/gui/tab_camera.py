import os
import logging
import numpy as np
import pyqtgraph as pg

from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt, pyqtSlot, QPointF, QSize, QTimer, QSettings
from PyQt6.QtWidgets import QMessageBox, QWidget, QPushButton, QVBoxLayout, QGridLayout, QLabel, QHBoxLayout, \
    QTableView, QLineEdit, QGraphicsPixmapItem, QFrame, QFormLayout, QDoubleSpinBox, QComboBox, QCheckBox, QFileDialog

from src.static_gui_elements.table_model import TableModel


class CameraTab(QWidget):
    """
    Camera Tab in MainWindow
    """

    def __init__(self, main_window, flags=Qt.WindowType.Widget):
        super().__init__(main_window, flags)
        self._main_window = main_window

        # Camera Picture
        self._cam_plot = pg.PlotItem(enableMenu=False)
        self._cam_image = pg.ImageItem()
        self._cam_roi = pg.RectROI(
            pos=[1, 1], size=[30, 30],
            rotatable=False, removable=False, aspectLocked=True
        )
        self._cam_roi.sigRegionChangeFinished.connect(self._handle_roi_changed)
        self._cam_color_bar = pg.ColorBarItem(interactive=False)
        self._cam_widget = pg.PlotWidget(plotItem=self._cam_plot)
        self._cam_widget.sceneObj.sigMouseClicked.connect(self._handle_picture_mouse_click)
        self._img_shape = [0, 0]

        # Camera Buttons
        button_take_picture = QPushButton("Take Picture", self)
        button_take_picture.clicked.connect(self._refresh_camera_picture)    # NOQA
        button_save_picture = QPushButton("Save Picture as...", self)
        button_save_picture.clicked.connect(self._handle_button_save_picture)    # NOQA

        # Camera Settings
        cam = self._main_window.devices.get("cam")
        layout_camera_settings = QFormLayout()
        layout_camera_settings.addRow(QLabel("<b>Camera Settings</b>"))
        if cam:
            line_edit_camera_exposure_time = QDoubleSpinBox()
            line_edit_camera_exposure_time.setRange(0, 1000)
            line_edit_camera_exposure_time.setDecimals(0)
            line_edit_camera_exposure_time.setValue(cam.get_exposure_time() * 1000)
            line_edit_camera_exposure_time.valueChanged.connect(    # NOQA
                lambda: cam.set_exposure_time(line_edit_camera_exposure_time.value() / 1000))
            layout_camera_settings.addRow(QLabel("Exposure Time / ms"), line_edit_camera_exposure_time)
            line_edit_camera_gain = QDoubleSpinBox()
            gain_lowest, gain_highest = cam.get_emccd_gain_range()
            line_edit_camera_gain.setRange(gain_lowest, gain_highest)
            line_edit_camera_gain.setDecimals(0)
            line_edit_camera_gain.setValue(cam.get_emccd_gain())
            line_edit_camera_gain.valueChanged.connect(    # NOQA
                lambda: cam.set_emccd_gain(int(line_edit_camera_gain.value())))
            layout_camera_settings.addRow(QLabel("EMCCD Gain"), line_edit_camera_gain)
            self._label_camera_temperature = QLabel(str(cam.get_temperature()))
            layout_camera_settings.addRow(QLabel("Current Temperature / °C"), self._label_camera_temperature)
            line_edit_camera_target_temperature = QDoubleSpinBox()
            line_edit_camera_target_temperature.setRange(-90, 20)
            line_edit_camera_target_temperature.setDecimals(0)
            line_edit_camera_target_temperature.setValue(cam.get_target_temperature())
            line_edit_camera_target_temperature.valueChanged.connect(    # NOQA
                lambda: cam.set_target_temperature(int(line_edit_camera_target_temperature.value())))
            layout_camera_settings.addRow(QLabel("Target Temperature / °C"), line_edit_camera_target_temperature)

            # Timer
            self.timer = QTimer()
            self.timer.timeout.connect(self._refresh_values)    # NOQA
            self.timer.start(2000)
        else:
            layout_camera_settings.addRow(QLabel("No Camera Connected"))
            logging.error("Tab Camera: Could not load Camera settings. No Camera connected")

        # Image settings
        layout_camera_settings.addRow(QLabel(""))
        layout_camera_settings.addRow(QLabel("<b>Image Settings</b>"))
        self._combo_box_camera_color_map = QComboBox()
        self._combo_box_camera_color_map.addItems(["cividis", "inferno", "magma", "plasma", "viridis"])
        self._combo_box_camera_color_map.currentTextChanged.connect(self._save_settings)    # NOQA
        self._combo_box_camera_color_map.currentTextChanged.connect(self._refresh_camera_picture)    # NOQA
        layout_camera_settings.addRow(QLabel("Color Map"), self._combo_box_camera_color_map)
        self._line_edit_roi_size = QDoubleSpinBox()
        self._line_edit_roi_size.setDecimals(0)
        self._line_edit_roi_size.setRange(0, 1000)
        self._line_edit_roi_size.setValue(float(QSettings().value("tab_camera/roi size", 0.0)))
        self._line_edit_roi_size.valueChanged.connect(self._save_settings)    # NOQA
        layout_camera_settings.addRow(QLabel("ROI Size"), self._line_edit_roi_size)
        self._line_edit_click_to_move_factor = QDoubleSpinBox()
        self._line_edit_click_to_move_factor.setDecimals(5)
        self._line_edit_click_to_move_factor.setRange(0, 5)
        self._line_edit_click_to_move_factor.setValue(float(QSettings().value("tab_camera/ctm factor", 0.0)))
        self._line_edit_click_to_move_factor.valueChanged.connect(self._save_settings)    # NOQA
        layout_camera_settings.addRow(QLabel("Click to Move Factor"), self._line_edit_click_to_move_factor)

        # Stage Settings
        layout_camera_settings.addRow(QLabel(""))
        layout_camera_settings.addRow(QLabel("<b>Stage Settings</b>"))
        self._checkbox_move_on_click = QCheckBox()
        self._checkbox_move_on_click.setTristate(False)
        self._checkbox_move_on_click.setChecked(QSettings().value("tab_camera/click stage", False))
        self._checkbox_move_on_click.clicked.connect(self._save_settings)    # NOQA
        layout_camera_settings.addRow(QLabel("Move Stage on Click"), self._checkbox_move_on_click)
        self._checkbox_stage_invert = QCheckBox()
        self._checkbox_stage_invert.setTristate(False)
        self._checkbox_stage_invert.setChecked(QSettings().value("tab_camera/invert stages", False))
        self._checkbox_stage_invert.clicked.connect(self._save_settings)    # NOQA
        layout_camera_settings.addRow(QLabel("Invert xy-Stage Direction"), self._checkbox_stage_invert)

        # Separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)

        # Stage Move
        widget_stage_move = QWidget()
        layout_stage_move = QGridLayout()
        step_size_xy = float(QSettings().value("tab_camera/stage_step_size_xy", 0.01))
        step_size_z = float(QSettings().value("tab_camera/stage_step_size_z", 0.01))
        self._textbox_step_size_xy = QLineEdit(self)
        self._textbox_step_size_xy.setText(str(step_size_xy))
        self._textbox_step_size_xy.editingFinished.connect(self._save_settings)    # NOQA
        button_up = QPushButton('Up', self)
        button_up.clicked.connect(lambda: self._move_stage('+y'))    # NOQA
        button_down = QPushButton('Down', self)
        button_down.clicked.connect(lambda: self._move_stage('-y'))    # NOQA
        button_left = QPushButton('Left', self)
        button_left.clicked.connect(lambda: self._move_stage('+x'))    # NOQA
        button_right = QPushButton('Right', self)
        button_right.clicked.connect(lambda: self._move_stage('-x'))    # NOQA
        self._textbox_step_size_z = QLineEdit(self)
        self._textbox_step_size_z.setText(str(step_size_z))
        self._textbox_step_size_z.editingFinished.connect(self._save_settings)    # NOQA
        button_fwd = QPushButton('Forwards', self)
        button_fwd.clicked.connect(lambda: self._move_stage('+z'))    # NOQA
        button_bwd = QPushButton('Backwards', self)
        button_bwd.clicked.connect(lambda: self._move_stage('-z'))    # NOQA

        layout_stage_move.addWidget(QLabel("<b>Sample</b>"), 0, 1)
        layout_stage_move.addWidget(QLabel("<b>Objective</b>"), 0, 3)
        layout_stage_move.addWidget(button_up, 1, 1)
        layout_stage_move.addWidget(button_down, 3, 1)
        layout_stage_move.addWidget(button_left, 2, 0)
        layout_stage_move.addWidget(button_right, 2, 2)
        layout_stage_move.addWidget(self._textbox_step_size_xy, 2, 1)
        layout_stage_move.addWidget(button_fwd, 1, 3)
        layout_stage_move.addWidget(button_bwd, 3, 3)
        layout_stage_move.addWidget(self._textbox_step_size_z, 2, 3)
        widget_stage_move.setLayout(layout_stage_move)

        # Stage Position
        widget_stage_position = QWidget()
        layout_stage_position = QGridLayout()
        layout_stage_position.addWidget(QLabel("x / mm"), 0, 1)
        layout_stage_position.addWidget(QLabel("y / mm"), 0, 2)
        layout_stage_position.addWidget(QLabel("z / mm"), 0, 3)
        layout_stage_position.addWidget(QLabel("Current Position:"), 1, 0)
        if hasattr(self._main_window, "stage_x") and hasattr(self._main_window, "stage_y"):
            self._label_pos_x = QLabel(str(self._main_window.stage_x.get_position()))
            self._label_pos_y = QLabel(str(self._main_window.stage_y.get_position()))
        elif hasattr(self._main_window, "stage_xy"):
            x, y = self._main_window.stage_xy.get_position()
            self._label_pos_x = QLabel(str(x))
            self._label_pos_y = QLabel(str(y))
        else:
            self._label_pos_x = QLabel("Stage not connected")
            self._label_pos_y = QLabel("Stage not connected")
            logging.error("Tab Camera: Could not get Stage x/y Positions. Stage(s) not connected")
        if hasattr(self._main_window, "stage_z"):
            self._label_pos_z = QLabel(str(self._main_window.stage_z.get_position()))
        else:
            self._label_pos_z = QLabel("Stage not connected")
            logging.error("Tab Camera: Could not get Stage z Position. Stage not connected")
        layout_stage_position.addWidget(self._label_pos_x, 1, 1)
        layout_stage_position.addWidget(self._label_pos_y, 1, 2)
        layout_stage_position.addWidget(self._label_pos_z, 1, 3)
        button_get_position = QPushButton("Get Position")
        button_get_position.clicked.connect(self._update_position_labels)    # NOQA
        layout_stage_position.addWidget(button_get_position, 1, 4)
        widget_stage_position.setLayout(layout_stage_position)

        # Table Buttons
        widget_table_buttons = QWidget()
        layout_table_buttons = QHBoxLayout()
        button_save_pos = QPushButton("Save current position", self)
        button_save_pos.clicked.connect(self._handle_button_save_position)    # NOQA
        button_move_pos = QPushButton("Move to selected position", self)
        button_move_pos.clicked.connect(self._handle_button_move_position)    # NOQA
        button_del_pos = QPushButton("Delete selected positions", self)
        button_del_pos.clicked.connect(self._handle_button_delete_positions)    # NOQA
        layout_table_buttons.addWidget(button_save_pos)
        layout_table_buttons.addWidget(button_move_pos)
        layout_table_buttons.addWidget(button_del_pos)
        widget_table_buttons.setLayout(layout_table_buttons)

        # Positions Table
        self._table_model = TableModel(
            header=['Name', 'x / mm', 'y / mm', 'z / mm'],
            data_types=[str, float, float, float]
        )
        self._table_view = QTableView()
        self._table_view.setModel(self._table_model)
        for pos in QSettings().value("tab_camera/stage_positions", []):
            self._table_model.appendRow(pos)

        # Layout Right Side
        widget_right_side = QWidget()
        layout_right_side = QVBoxLayout()
        layout_right_side.addWidget(widget_stage_move)
        layout_right_side.addWidget(widget_stage_position)
        layout_right_side.addWidget(widget_table_buttons)
        layout_right_side.addWidget(self._table_view)
        widget_right_side.setLayout(layout_right_side)

        # Total Layout
        layout_camera = QHBoxLayout()
        layout_camera_picture = QVBoxLayout()
        layout_camera_picture.addWidget(self._cam_widget)
        layout_camera_picture.addWidget(button_take_picture)
        layout_camera_picture.addWidget(button_save_picture)
        layout_camera.addLayout(layout_camera_picture)
        layout_camera.addLayout(layout_camera_settings)

        layout = QHBoxLayout()
        layout.addLayout(layout_camera)
        layout.addWidget(line, alignment=Qt.AlignmentFlag.AlignRight)
        layout.addWidget(widget_right_side, alignment=Qt.AlignmentFlag.AlignRight)
        self.setLayout(layout)

    def _save_settings(self):
        """
        Save all settings
        """
        QSettings().setValue("tab_camera/color map", self._combo_box_camera_color_map.currentText())
        QSettings().setValue("tab_camera/roi pos", self._cam_roi.pos())
        QSettings().setValue("tab_camera/roi size", self._cam_roi.size())
        QSettings().setValue("tab_camera/ctm factor", self._line_edit_click_to_move_factor.text())
        QSettings().setValue("tab_camera/click stage", self._checkbox_move_on_click.checkState())
        QSettings().setValue("tab_camera/invert stages", self._checkbox_stage_invert.checkState())
        QSettings().setValue("tab_camera/stage positions", self._table_model.getData())

    def _refresh_camera_picture(self):
        """
        Take Camera Picture and plot it
        """
        # Take Picture
        logging.info("Tab Camera: Taking Picture")
        try:
            image_data = self._main_window.devices["cam"].take_picture()
        except AttributeError:
            logging.error("Tab Camera: Could not take Picture. No Camera connected")
            image_data = np.zeros((1200, 1200))
        if image_data is None:
            logging.error("Tab Camera: Could not take Picture. No Camera connected")
            image_data = np.zeros((1200, 1200))

        # Plot Picture
        self._cam_image.setImage(image_data)
        color_map = QSettings().value("tab_camera/color_map", "inferno")
        try:
            self._cam_image.setColorMap(pg.colormap.get(color_map))
        except FileNotFoundError:
            logging.error(f"Tab Camera: Could not find Color Map '{color_map}'.")
        self._cam_plot.clear()
        self._cam_plot.addItem(self._cam_image)
        self._cam_plot.addItem(self._cam_roi)
        self._cam_color_bar.setLevels(low=np.min(image_data), high=np.max(image_data))
        self._cam_color_bar.setImageItem(self._cam_image, insert_in=self._cam_plot)

        # Add Crosshair
        self._img_shape = image_data.shape
        size = max(self._img_shape)
        # offset = (self._img_shape[1] - self._img_shape[0]) / 2
        crosshair_icon = QIcon(os.path.join("src", "gui", "img", "crosshair.svg"))
        crosshair = QGraphicsPixmapItem(crosshair_icon.pixmap(QSize(size, size)))
        crosshair.setOffset(0, 0)
        self._cam_plot.addItem(crosshair)

    @pyqtSlot()
    def _refresh_values(self):
        """
        Refresh Labels
        """
        self._label_camera_temperature.setText(str(self._main_window.devices["cam"].get_temperature()))

    @pyqtSlot()
    def _handle_roi_changed(self):
        size = self._cam_roi.size()
        size_x, size_y = int(size.x()), int(size.y())
        pos = self._cam_roi.pos()
        pos_x, pos_y = int(pos.x()+size_x/2), int(pos.y()+size_y/2)

        if hasattr(self._main_window, "cam"):
            self._main_window.device["cam"].resize_dimensions = [pos_x, size_x, pos_y, size_y]
        self._line_edit_roi_size.setValue(size_x)

        logging.info(f"Tab Camera: Set ROI to Pos: 'x={pos_x}, y={pos_y}', Size: 'x={size_x}, y={size_y}'")

    def _handle_picture_mouse_click(self, event):
        """
        Move Stage on Mouse Left Click
        """
        click_stage = bool(QSettings().value("tab_camera/click stage", False))
        ctm_factor = float(QSettings().value("tab_camera/ctm factor", 0.0))

        # Map Mouse Click to Image Coordinates
        mouse_click_point = QPointF(event.pos().x(), event.pos().y())
        mapped_click = self._cam_widget.getPlotItem().vb.mapSceneToView(mouse_click_point)

        # Left-Click
        if event.button() == 1 and click_stage:
            move_rel_x = ctm_factor * (mapped_click.x() - self._img_shape[0] / 2)
            move_rel_y = ctm_factor * (mapped_click.y() - self._img_shape[1] / 2)
            logging.info(f"Tab Camera: Mouse Click at {mapped_click.x():.2f}, {mapped_click.y():.2f}, Moving relative "
                         f"by {move_rel_x}, {move_rel_y}")

            if hasattr(self._main_window, "stage_x") and hasattr(self._main_window, "stage_y"):
                self._main_window.stage_x.move_relative(move_rel_x)
                self._main_window.stage_y.move_relative(move_rel_y)
            elif hasattr(self._main_window, "stage_xy"):
                self._main_window.stage_xy.move_relative(move_rel_x, move_rel_y)

    @pyqtSlot()
    def _update_position_labels(self):
        """
        Update Labels of Stage Positions
        """
        # Check if x and y are connected as one Stage or two
        if hasattr(self._main_window, "stage_x") and hasattr(self._main_window, "stage_z"):
            self._label_pos_x.setText(str(self._main_window.devices["stage_x"].get_position()))
            self._label_pos_y.setText(str(self._main_window.devices["stage_y"].get_position()))
        elif hasattr(self._main_window, "stage_xy"):
            pos_x, pos_y = self._main_window.stage_xy.get_position()
            self._label_pos_x.setText(str(pos_x))
            self._label_pos_y.setText(str(pos_y))
        else:
            self._label_pos_x.setText("No Stage connected")
            self._label_pos_y.setText("No Stage connected")

        # Check if z Stage is connected
        if hasattr(self._main_window, "stage_z"):
            self._label_pos_z.setText(str(self._main_window.devices["stage_z"].get_position()))
        else:
            self._label_pos_z.setText("No Stage connected")

    @pyqtSlot()
    def _move_stage(self, direction):
        """
        Move Stage x|y|z in Direction
        """
        # Invert Direction according to Settings
        if QSettings().value("tab_camera/invert stage"):
            if direction[0] == '+':
                direction = direction.replace('+', '-')
            elif direction[0] == '-':
                direction = direction.replace('-', '+')

        xy = float(self._textbox_step_size_xy.text())
        z = float(self._textbox_step_size_z.text())

        # Check if x and y Stages are different Devices or one Device
        if hasattr(self._main_window, "stage_x") and hasattr(self._main_window, "stage_y") and \
                hasattr(self._main_window, "stage_z"):
            if direction == '+x':
                self._main_window.stage_x.move_relative(xy)
            elif direction == '+y':
                self._main_window.stage_y.move_relative(xy)
            elif direction == '+z':
                self._main_window.stage_z.move_relative(z)

            elif direction == '-x':
                self._main_window.stage_x.move_relative(-xy)
            elif direction == '-y':
                self._main_window.stage_y.move_relative(-xy)
            elif direction == '-z':
                self._main_window.stage_z.move_relative(-z)

        elif hasattr(self._main_window, "stage_xy") and hasattr(self._main_window, "stage_z"):
            if direction == '+x':
                self._main_window.stage_xy.move_relative(xy, 0)
            elif direction == '+y':
                self._main_window.stage_xy.move_relative(0, xy)
            elif direction == '+z':
                self._main_window.stage_z.move_relative(z)

            elif direction == '-x':
                self._main_window.stage_xy.move_relative(-xy, 0)
            elif direction == '-y':
                self._main_window.stage_xy.move_relative(0, -xy)
            elif direction == '-z':
                self._main_window.stage_z.move_relative(-z)

        else:
            # Throw Warning if Stages not connected
            logging.error("Tab Camera: Could not move Stage. One or more Stages are not connected.")
            QMessageBox.critical(self._main_window, "Error", "Could not move Stage. One or more Stages are not "
                                                             "connected.")
            return

        self._refresh_camera_picture()
        self._update_position_labels()

    @pyqtSlot()
    def _handle_button_save_position(self):
        """
        Save Current Stage Positions in Table
        """
        # Get Current Positions
        if hasattr(self._main_window, "stage_x") and hasattr(self._main_window, "stage_y"):
            x, y = self._main_window.stage_x.get_position(), self._main_window.stage_y.get_position()
        elif hasattr(self._main_window, "stage_xy"):
            x, y = self._main_window.stage_xy.get_position()
        else:
            logging.error("Tab Camera: Could not retrieve Stage x and y Position: Stages not connected")
            QMessageBox.critical(self._main_window, "Error", "Could not retrieve Stage x and y Position: Stages not "
                                                             "connected")
            return

        if hasattr(self._main_window, "stage_z"):
            z = self._main_window.stage_z.get_position()
        else:
            logging.error("Tab Camera: Could not retrieve Stage z Position: Stage not connected")
            QMessageBox.critical(self._main_window, "Error", "Could not retrieve Stage z Position: Stage not connected")
            return

        x, y, z = float(x), float(y), float(z)

        # Check for Errors
        if x == -1 or y == -1 or z == -1:
            logging.error("Tab Camera: Could not retrieve Stage Position: Stages returned Error")
            QMessageBox.critical(self._main_window, "Error", "Could not retrieve Stage Positions: One or more Stage "
                                                             "returned an Error Code")
            return

        # Add Positions to Table and Save in File
        self._table_model.appendRow(["Empty Name", x, y, z])
        self._save_settings()

    def _get_selected_rows(self) -> list:
        """
        Return List of selected Rows (ordered and no duplicates)
        """
        rows = []
        rows_sorted = []
        for e in self._table_view.selectionModel().selectedRows():
            rows.append(e.row())                                                    # get all rows of selected rows
        for e in self._table_view.selectionModel().selectedIndexes():
            rows.append(e.row())                                                    # get all rows of selected items
        [rows_sorted.append(x) for x in rows if x not in rows_sorted]               # remove duplicates
        rows_sorted.sort(reverse=True)                                              # sort list
        print(rows_sorted)
        return rows_sorted

    @pyqtSlot()
    def _handle_button_move_position(self):
        """
        Move to currently selected Position
        """
        # use first row if multiple rows/items are selected, ignore if no row/item selected
        try:
            _, x, y, z = self._table_model.getData(self._get_selected_rows()[-1])
        except IndexError:
            return

        if hasattr(self._main_window, "stage_x") and hasattr(self._main_window, "stage_y"):
            self._main_window.stage_x.move_absolute(x)
            self._main_window.stage_y.move_absolute(y)
        elif hasattr(self._main_window, "stage_xy"):
            self._main_window.stage_xy.move_absolute(x, y)
        else:
            logging.error("Tab Camera: Could not move Stage x and y: Stages not connected")
            QMessageBox.critical(self._main_window, "Error", "Could not move Stage x and y: Stages not connected")

        if hasattr(self._main_window, "stage_z"):
            self._main_window.stage_z.move_absolute(z)
        else:
            logging.error("Tab Camera: Could not move Stage z: Stage not connected")
            QMessageBox.critical(self._main_window, "Error", "Could not move Stage z: Stage not connected")
            return

    @pyqtSlot()
    def _handle_button_delete_positions(self):
        """
        Remove Selected Rows from Table
        """
        for row in self._get_selected_rows():
            self._table_model.removeRow(row)
        self._save_settings()

    @pyqtSlot()
    def _handle_button_save_picture(self):
        """
        Save last Picture
        """
        if not hasattr(self._main_window, "cam"):
            logging.error("Tab Camera: Could not save Picture. No Camera connected.")
            QMessageBox.critical(self._main_window, "Error", "No Camera connected")
            return

        file_name, _ = QFileDialog.getSaveFileName(
            None, "Save Picture as...", os.getcwd(),
            "All (*.*);;Image Files (*.png);;Raw Images (*.npy)"
        )
        self._main_window.devices["cam"].save_picture(file_name)
