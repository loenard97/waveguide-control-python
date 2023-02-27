"""
UC480 Thorlabs Camera
"""

import os
import sys
import logging
import numpy as np

if sys.platform == "win32":
    import clr    # NOQA
    sys.path.append(os.getcwd() + r"...\dll")
    clr.AddReference("devices\\lib_camera_thorlabs_uc480\\uc480DotNet")
    import uc480    # NOQA


class CameraThorlabs:
    NAME = "Thorlabs UC480 Camera"
    ICON = "cam"

    def __init__(self, address=None):
        super().__init__()
        self.address = address

        try:
            self._ser = uc480.Camera()
            self._ser.Init()
        except clr.System.DllNotFoundException:
            raise ConnectionError

        self._ser.Display.Mode.Set(uc480.Defines.DisplayMode.DiB)
        self._ser.PixelFormat.Set(uc480.Defines.ColorMode.RGBA8Packed)
        self._ser.Trigger.Set(uc480.Defines.TriggerMode.Software)
        self._ser.Timing.Exposure.Set(100)

    def disconnect(self):
        self._ser.Exit()

    def take_picture(self):
        try:
            self._ser.Memory.Free(1)                                             # free memory on camera
        except clr.System.NullReferenceException:
            logging.error(f"{self.NAME}: Could not take picture. Camera not initialized")
            return
        self._ser.Memory.Allocate(True)                                          # reallocate memory on camera
        _, width, height, bits, _ = self._ser.Memory.Inquire(1, 0, 0, 0, 0)      # ask details of memory
        self._ser.Acquisition.Freeze(uc480.Defines.DeviceParameter.Wait)         # take picture
        _, pic = self._ser.Memory.CopyToArray(1, bytearray(1))                   # copy image to memory

        pic = np.fromiter(pic, int)                                             # convert bytearray to int
        pic = np.transpose(pic)
        pic = pic.reshape((bits // 8, width, height), order='F')                # reshape to matrix
        pic = pic[0, 0:width, 0:height]

        return pic

    def start_video(self):
        self._ser.Memory.Free(1)
        self._ser.Memory.Allocate(True)
        self._ser.Acquisition.Capture()

    def get_video_frame(self):
        _, width, height, bits, _ = self._ser.Memory.Inquire(1, 0, 0, 0, 0)
        _, pic = self._ser.Memory.CopyToArray(1, bytearray(1))

        try:
            pic = np.fromiter(pic, int)  # convert bytearray to int
        except TypeError:
            logging.warning(f"{self.NAME}: Could not take picture")

        pic = np.transpose(pic)
        pic = pic.reshape((bits // 8, width, height), order='F')  # reshape to matrix
        pic = pic[0, 0:width, 0:height]

        return pic

    def stop_video(self):
        self._ser.Acquisition.Stop()
