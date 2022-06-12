#!/usr/bin/env python3
import os, time, json, dbus
import subprocess as sp
from pathlib import Path

from .utils import audio, network, wallpaper
from pyvdm.interface import CapabilityLibrary, SRC_API

DBG = 1
SLOT = 0.40

class DesktopSettings(SRC_API):

    def onStart(self):
        return 0

    def onStop(self):
        return 0

    def onSave(self, stat_file):
        return 0

    def onResume(self, stat_file):
        return 0

    def onClose(self):
        return 0
    pass

if __name__ == '__main__':
    _plugin = DesktopSettings()
    _plugin.onStart()

    ## gathering record
    record = _plugin._gather_record()
    print( json.dumps(record, indent=4) )
    _plugin.onClose()

    ## test resume
    time.sleep( 2.0 )
    _plugin._resume_status(record)
    pass
