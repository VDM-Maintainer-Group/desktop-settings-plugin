#!/usr/bin/env python3
from abc import ABC, abstractmethod
import re
import dbus
import subprocess as sp

__all__ = ['NetworkManager']

SHELL_RUN = lambda cmd: sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, check=True)

class NetworkSettings(ABC):
    @staticmethod
    @abstractmethod
    def exists() -> bool:
        pass

    @abstractmethod
    def get_device_names(self) -> list:
        pass

    @abstractmethod
    def get_device_status(self):
        pass

    @abstractmethod
    def set_device_status(self, dev_name:str, dev_status):
        pass

    @staticmethod
    def _equal_status(s1:dict, s2:dict) -> bool:
        for key,val in s1.items():
            if key not in s2:
                return False
            if val != s2[key]:
                return False
        return True

    def get_all_status(self) -> dict:
        record = dict()
        device_names = self.get_device_names()
        for name in device_names:
            status = self.get_device_status(name)
            if status:
                record[name] = status
        ##
        return record

    def set_all_status(self, record:dict):
        current_status = self.get_all_status()
        ##
        device_names = self.get_device_names()
        for name,status in record.items():
            if name in device_names and not self._equal_status(status, current_status[name]):
                self.set_device_status(name, status)
        pass

    pass

class NetworkManager(NetworkSettings):
    @staticmethod
    def exists() -> bool:
        sess = dbus.SystemBus()
        flag = 'org.freedesktop.NetworkManager' in sess.list_names()
        return flag

    @staticmethod
    def parse_from_nmcli():
        _matcher = re.compile('(\S+)\s+(\S+)\s+(\S+)\s+(.+)')
        _output = SHELL_RUN('nmcli device').stdout.decode().strip()
        ##
        results = {}
        for (dev,_type,state,conn) in _matcher.findall(_output):
            if _type in ['ethernet', 'wifi', 'wifi-p2p']:
                conn = conn.strip()
                conn = '' if conn=='--' else conn
                results[dev] = {
                    'type': _type, 'state': state, 'conn': conn
                }
        return results

    def __init__(self):
        super().__init__()
        self.info = self.parse_from_nmcli()
    
    def get_device_names(self) -> list:
        try:
            _names = list( self.info.keys() )
        except:
            _names = list()
        return _names

    def get_device_status(self, dev_name:str):
        try:
            _status = self.info[dev_name]
        except:
            _status = None
        return _status

    def set_device_status(self, dev_name:str, dev_status):
        if dev_status['state']=='unmanaged':
            return
        ##
        try:
            conn = dev_status['conn']
            if not conn:
                if dev_status['type'] in ['wifi', 'wifi-p2p']:
                    SHELL_RUN('nmcli radio wifi off')
                SHELL_RUN( f'nmcli device disconnect {dev_name}' )
            else:
                if dev_status['type'] in ['wifi', 'wifi-p2p']:
                    SHELL_RUN('nmcli radio wifi on')
                SHELL_RUN( f'nmcli device connect {dev_name} {conn}' )
        except Exception as e:
            print(e)
        pass


if __name__=='__main__':
    import json
    
    settings = NetworkManager()
    _record = settings.get_all_status()
    print( json.dumps(_record, indent=4) )

    settings.set_all_status( _record )
