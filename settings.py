#!/usr/bin/env python3
import os, time, json, dbus

from utils import audio, network, wallpaper
from pyvdm.interface import CapabilityLibrary, SRC_API

DBG = 1

class DesktopSettings(SRC_API):

    def _probe_environment(self):
        def _probe(module):
            for _candidate in module.__all__:
                _class = getattr(module, _candidate)
                if _class.exists():
                    return _class()
            return None
        ##
        self.settings = {
            'audio'   :  _probe(audio),
            'network' :  _probe(network),
            'wallpaper': _probe(wallpaper),
        }
        pass

    def _gather_records(self):
        return {
            key:_settings.get_all_status()
                for key,_settings in self.settings.items()
                if _settings is not None
        }

    def _resume_status(self, records):
        for name,status in records.items():
            if name in self.settings and self.settings[name] is not None:
                self.settings[name].set_all_status(status)
        pass

    def onStart(self):
        self._probe_environment()
        self._init_records = self._gather_records()
        return 0

    def onStop(self):
        return 0

    def onSave(self, stat_file):
        ## gathering records
        records = self._gather_records()
        ## write to file
        with open(stat_file, 'w') as f:
            json.dump(records, f)
        return 0

    def onResume(self, stat_file):
        ## load stat file with failure check
        with open(stat_file, 'r') as f:
            _file = f.read().strip()
        if len(_file)==0:
            return 0
        else:
            try:
                records = json.loads(_file)
            except:
                return -1
         ## resume settings from records
        self._resume_status(records)
        return 0

    def onClose(self):
        self._resume_status( self._init_records )
        return 0
    pass

if __name__ == '__main__':
    _plugin = DesktopSettings()
    _plugin.onStart()

    ## gathering record
    records = _plugin._gather_records()
    print( json.dumps(records, indent=4) )
    _plugin.onClose()

    ## test resume
    time.sleep( 2.0 )
    _plugin._resume_status(records)
    pass
