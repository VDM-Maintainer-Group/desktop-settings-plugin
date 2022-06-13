#!/usr/bin/env python3
from abc import ABC, abstractmethod
import os
import dbus
import shutil
import subprocess as sp

__all__ = ['UbuntuGnome']

SHELL_RUN = lambda cmd: sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True, check=True)

class WallpaperSettings(ABC):
    @staticmethod
    @abstractmethod
    def exists() -> bool:
        pass

    @abstractmethod
    def get_wallpaper_status(self):
        pass

    @abstractmethod
    def set_wallpaper_status(self, status):
        pass

class UbuntuGnome(ABC):
    @staticmethod
    def exists() -> bool:
        try:
            gnome_flag = 'GNOME' in os.environ['XDG_CURRENT_DESKTOP']
            gsettings_flag = shutil.which('gsettings') is not None
            return (gnome_flag and gsettings_flag)
        except:
            return False
    
    def get_wallpaper_status(self):
        try:
            _proc = SHELL_RUN('gsettings get org.gnome.desktop.background picture-uri')
            _uri  = _proc.stdout.decode().strip("'\n")
        except:
            _uri = ''
        return _uri

    def set_wallpaper_status(self, uri):
        try:
            SHELL_RUN(f'gsettings set org.gnome.desktop.background picture-uri {uri}')
        except Exception as e:
            print(e)
        pass


if __name__=='__main__':
    import json
    
    settings = UbuntuGnome()
    _record = settings.get_wallpaper_status()
    print( json.dumps(_record, indent=4) )

    settings.set_wallpaper_status( _record )
