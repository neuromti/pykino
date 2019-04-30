# -*- coding: utf-8 -*-
"""
watchdog wrapper to see when kinovea started recording
"""

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from datetime import datetime
from typing import Callable, List
import configparser
import os
# %%
class FileHandler(FileSystemEventHandler):
    
    def __init__(self):
        self.created_files = []
    
    def on_created(self, event):
        self.created_files.append(event.src_path)
        
class KinoWatcher():

    def __init__(self, path=r'C:\projects\kinovea'):
        self.path = path 
            
    def wait(self, show:Callable=None, number=2):
        handler = FileHandler()        
        self.observer = Observer()
        self.observer.schedule(handler, self.path, recursive=True)
        self.observer.start()        
        while not len(handler.created_files)>=number:
            if show is None:
                time.sleep(.1)                
            else:
                show()
        self.observer.stop()
        self.observer.join()
        return handler.created_files


class KinoLogger():
        
    @classmethod
    def sanitize_string(marker:str):
        translation = str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue',' ':'_'})
        return marker.lower().strip().translate(translation)
    
    def update_file(self):
        with open(self.fname, 'w') as file:
            self.log.write(file) 
        
    
    def __init__(self, fname=r'C:\projects\kinovea\logfile.ini'):
        self.fname = fname 
        self.logfile = configparser.ConfigParser()
        
    def add_newfiles(self, moviefiles:List[str]):
        self.moviefiles = moviefiles
        m = moviefiles[0]
        secA = os.path.splitext(os.path.split(m)[1])[0].split('_')[1]
        m = moviefiles[1]
        secB = os.path.splitext(os.path.split(m)[1])[0].split('_')[1]
        if secB == secA:
            self.current_section = secA
            self.logfile.add_section(self.current_section)
            self.write()
        else:
            raise FileNotFoundError('Movies have not started in sync: Restart')
        
    def log(self, msg:str):
        val = self.get_current_time        
        key = self.sanitize_string(msg)    
        self.logfile.set(self.current_section, key, val)
        self.update_file()
    
        
    @classmethod
    def get_current_time(cls):
        """return time as string similar to kinovea file format
        i.e. YearMonthDay - HourMinutesSeconds.Milliseconds        
        """
        return datetime.now().strftime("%H:%M:%S.%f")
# %%