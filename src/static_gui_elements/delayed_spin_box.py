"""
Children of QSpinBox and QDoubleSpinBox
"""

from PyQt6.QtCore import pyqtSlot, pyqtSignal, QTimer
from PyQt6.QtWidgets import QSpinBox, QDoubleSpinBox


class DelayedSpinBox(QSpinBox):

    delayedValueChanged = pyqtSignal(int)

    def __init__(self, delay=1000):
        """
        QSpinBox with a delayedValueChanged(int) signal
        :param int delay: Delay in ms
        """
        super().__init__()
        self.delay = delay
        self._delay_timer = QTimer()
        self._delay_timer.setSingleShot(True)
        self._delay_timer.timeout.connect(self._handle_delay_timer)    # NOQA
        self.valueChanged.connect(self._handle_value_changed)    # NOQA

    @pyqtSlot()
    def _handle_value_changed(self):
        """
        Start delay timer
        """
        self._delay_timer.start(self.delay)

    @pyqtSlot()
    def _handle_delay_timer(self):
        """
        Emit delayedValueChanged(int) signal
        """
        self.delayedValueChanged.emit(self.value())    # NOQA


class DelayedDoubleSpinBox(QDoubleSpinBox):

    delayedValueChanged = pyqtSignal(float)

    def __init__(self, delay=1000):
        """
        QSpinBox with a delayedValueChanged(float) signal
        :param int delay: Delay in ms
        """
        super().__init__()
        self.delay = delay
        self._delay_timer = QTimer()
        self._delay_timer.setSingleShot(True)
        self._delay_timer.timeout.connect(self._handle_delay_timer)    # NOQA
        self.valueChanged.connect(self._handle_value_changed)    # NOQA

    @pyqtSlot()
    def _handle_value_changed(self):
        """
        Start delay timer
        """
        self._delay_timer.start(self.delay)

    @pyqtSlot()
    def _handle_delay_timer(self):
        """
        Emit delayedValueChanged(int) signal
        """
        self.delayedValueChanged.emit(self.value())    # NOQA
