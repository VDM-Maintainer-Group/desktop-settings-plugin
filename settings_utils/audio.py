#!/usr/bin/env python3
from abc import ABC, abstractmethod
import re
import dbus
import subprocess as sp
from itertools import cycle

__all__ = ['PulseAudio']

SHELL_RUN = lambda cmd: sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, check=True)

class AudioSettings(ABC):
    @staticmethod
    @abstractmethod
    def exists() -> bool:
        pass

    @abstractmethod
    def get_default_sink(self) -> str:
        pass

    @abstractmethod
    def set_default_sink(self, name:str):
        pass

    @abstractmethod
    def get_sink_names(self) -> list:
        pass

    @abstractmethod
    def get_sink_status(self, sink_name:str):
        pass

    @abstractmethod
    def set_sink_status(self, sink_name:str, sink_status):
        pass

    def get_all_status(self) -> dict:
        sinks = dict()
        sink_names = self.get_sink_names()
        for name in sink_names:
            status = self.get_sink_status(name)
            if status:
                sinks[name] = status
        ##
        default = self.get_default_sink()
        record = {'default':default, 'sinks':sinks}
        return record

    def set_all_status(self, record:dict):
        sink_names = self.get_sink_names()
        for name,status in record['sinks'].items():
            if name in sink_names:
                self.set_sink_status(name, status)
        ##
        self.set_default_sink( record['default'] )
        pass

    pass

class PulseAudio(AudioSettings):
    @staticmethod
    def exists() -> bool:
        sess = dbus.SessionBus()
        flag = 'org.pulseaudio.Server' in sess.list_names()
        return flag
    
    @staticmethod
    def parse_from_pacmd():
        ##
        _output = SHELL_RUN('pacmd list-sinks').stdout.decode().strip()
        outputs = _output.split('\n')
        ##
        regex_fsm  = {
            'index':  re.compile('(.+)index: \d+'),
            'name':   re.compile('\s+name: \<(.+)\>'),
            'volume': re.compile('\s+volume: front-left: (\d+).+dB'),
            'muted':  re.compile('\s+muted: (.+)'),
            'desc':   re.compile('\s+device.description = "(.+)"'),
        }
        regex_iter = cycle( regex_fsm.keys() )
        regex_ptr  = next(regex_iter)

        _item = None
        name2desc = {}
        results = { 'default':'', 'sinks':{} }
        for _line in outputs:
            _matches = regex_fsm[regex_ptr].findall(_line)
            if _matches:
                _info = _matches[0]
                ##
                if regex_ptr=='index':
                    _item = {'default': _info.strip()=='*'}
                elif regex_ptr=='name':
                    _item['name'] = _info
                elif regex_ptr=='volume':
                    _item['volume'] = int(_info)
                elif regex_ptr=='muted':
                    _item['muted'] = _info=='yes'
                elif regex_ptr=='desc':
                    _desc = _info.strip()
                    ##
                    if _item['default']:
                        results['default'] = _desc
                    results['sinks'][_desc] = {
                        'name':_item['name'],
                        'volume':_item['volume'], 'muted':_item['muted']
                    }
                    name2desc[ _item['name'] ] = _desc
                    ##
                    _item = None
                    pass
                ##
                regex_ptr = next(regex_iter)
            pass
        return (name2desc, results)

    def __init__(self):
        super().__init__()
        self.name2desc, self.info = self.parse_from_pacmd()
    
    def get_default_sink(self) -> str:
        try:
            _default = self.info['default']
        except:
            _default = ''
        return _default

    def set_default_sink(self, desc:str):
        try:
            _name = self.info['sinks'][desc]['name']
            SHELL_RUN(f'pacmd set-default-sink {_name}')
        except Exception as e:
            print(e)
        pass

    def get_sink_names(self) -> list:
        try:
            _names = list( self.info['sinks'].keys() )
        except:
            _names = list()
        return _names

    def get_sink_status(self, desc:str):
        try:
            _status = self.info['sinks'][desc]
        except:
            _status = None
        return _status

    def set_sink_status(self, desc:str, sink_status):
        try:
            sink_name = self.info['sinks'][desc]['name']
            _volume = sink_status['volume']
            _mute   = 1 if sink_status['muted'] else 0
            SHELL_RUN(f'pacmd set-sink-volume {sink_name} {_volume}')
            SHELL_RUN(f'pacmd set-sink-mute {sink_name} {_mute}')
        except Exception as e:
            print(e)
        pass

    pass


if __name__=='__main__':
    import json
    
    settings = PulseAudio()
    _record = settings.get_all_status()
    print( json.dumps(_record, indent=4) )

    settings.set_all_status( _record )
