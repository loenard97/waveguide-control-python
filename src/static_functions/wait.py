"""
Helper Functions to interrupt Function with a QEventLoop
"""

from PyQt6.QtCore import QEventLoop, QTimer


def event_loop_interrupt(timeout=5):
    """
    Wait for Number of Seconds
    """
    def timeout_handler():
        local_loop.quit()

    local_loop = QEventLoop()
    QTimer().singleShot(int(timeout*1000), timeout_handler)
    local_loop.exec()


def wait_until_signal(signal, timeout=5000):
    """
    Wait for Signal
    """
    # TODO: check if working
    def timeout_handler():
        local_loop.quit()

    def check_condition():
        timeout_timer.stop()
        local_loop.quit()

    local_loop = QEventLoop()
    signal.connect(check_condition)
    timeout_timer = QTimer()
    timeout_timer.setSingleShot(True)
    timeout_timer.setInterval(int(timeout))
    timeout_timer.timeout.connect(timeout_handler)
    timeout_timer.start()

    local_loop.exec()
