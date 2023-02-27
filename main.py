import os
import sys
import logging
import platform
import datetime
import subprocess

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication

from src.gui.main_window import MainWindow


def main():
    """
    Start Main Window
    """
    app = QApplication(sys.argv)
    app.setOrganizationName("AGWidera")
    app.setApplicationName("MECA")
    QSettings.setDefaultFormat(QSettings.Format.IniFormat)

    for path in ["logs", "scripts"]:
        os.makedirs(path, exist_ok=True)

    # Logging Settings
    if "--debug" in sys.argv:
        logger_level = "DEBUG"
    else:
        logger_level = "WARNING"
    logging.basicConfig(
        level=logger_level,
        format="%(asctime)s: [%(levelname)s] - %(message)s",
        handlers=[
            logging.FileHandler(os.path.join("logs", f"{datetime.datetime.now():%Y-%m-%d_%H-%M-%S}.log")),
            logging.StreamHandler(sys.stdout),
        ]
    )

    # Log Meta Info
    system = platform.uname()
    logging.log(level=100, msg=f"System: {system.system}, Node Name: {system.node}, Release: {system.release}, "
                f"Version: {system.version}, Machine: {system.machine}")
    python_version = sys.version.replace('\n', '')
    logging.log(level=100, msg=f"Python Version: {python_version}")
    git_tag = subprocess.check_output(['git', 'describe', '--tags']).decode('ascii').strip()
    logging.log(level=100, msg=f"MECA Version: {git_tag}")

    # Start Main Window
    main_win = MainWindow()
    main_win.setWindowTitle(
        f"Microscope Experiment Control Application - {git_tag}{' (Debug)' if '--debug' in sys.argv else ''}")
    main_win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
