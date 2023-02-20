"""
Children of PyQtGraph Plot Widgets
"""

import pyqtgraph as pg


class PlotWidget(pg.PlotWidget):
    """
    Regular Plot Widget
    """

    def __init__(self):
        super().__init__()
        self.x_label = "x Label"
        self.y_label = "y Label"
        self.showGrid(x=True, y=True)

    def plot_data(self, x_data, y_data, color="green"):
        """
        Redraw Plot with new Data
        """
        self.clear()
        self.plot(x_data, y_data, pen=color)

    def set_labels(self, x_label, y_label):
        """
        Set Axis Labels
        """
        self.x_label = x_label
        self.y_label = y_label
        self.setLabel('bottom', self.x_label)
        self.setLabel('left', self.y_label)
