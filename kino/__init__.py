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
from threading import Barrier, Thread
#%%
def lock_until_file_is_safe(filename):
    isrecording = True
    old_size = -1
    while isrecording:
        new_size = os.path.getsize(filename)
        if new_size == old_size:
            break
        else:
            old_size = os.path.getsize(filename)
            time.sleep(.25)            
    return True

def lock_until_files_are_safe(filenames):
    def lock(f, b):
        lock_until_file_is_safe(f)
        b.wait()
        
    barrier = Barrier(len(filenames)+1)
    for filename in filenames:
        t = Thread(target=lock, args=(filename, barrier, ))
        t.start()
    barrier.wait()
# %%
class FileHandler(FileSystemEventHandler):
    
    def __init__(self):
        self.created_files = []
    
    def on_created(self, event):
        self.created_files.append(event.src_path)
    
    def on_modified(self, event):
        print(event)
        
class KinoWatcher():

    def __init__(self, path=r'C:\projects\kinovea'):
        self.path = path 
            
    def wait_start(self, show:Callable=None, number=2):
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
        self.files = handler.created_files
        return self.files

    def wait_finish(self, show:Callable=None):
        def lock(f, b):
            lock_until_file_is_safe(f)
            b.wait()
        
        barrier = Barrier(len(self.files)+1)
        for filename in self.files:
            t = Thread(target=lock, args=(filename, barrier, ))
            t.start()
        barrier.wait()
        return True
        

def sanitize_string(marker:str):
    translation = str.maketrans({'ä': 'ae', 'ö': 'oe', 'ü': 'ue',' ':'_'})
    return marker.lower().strip().translate(translation)

class KinoLogger():
    
    def update_file(self):
        with open(self.fname, 'w') as file:
            self.logfile.write(file) 
        
    
    def __init__(self, fname=r'C:\projects\kinovea\logfile.ini'):
        self.fname = fname 
        self.logfile = configparser.ConfigParser()
        self.logfile.add_section('Info')
        
    def new_recording(self, moviefiles:List[str]):
        self.logfile.add_section('Filenames')
        for i, m in enumerate(moviefiles):
            self.logfile.set('Filenames', str(i), m)
            self.update_file()
        
        self.moviefiles = moviefiles
        m = moviefiles[0]
        secA = os.path.splitext(os.path.split(m)[1])[0].split('_')[1]
        m = moviefiles[1]
        secB = os.path.splitext(os.path.split(m)[1])[0].split('_')[1]
        if secB == secA:
            self.current_section = secA
            self.logfile.add_section(self.current_section)
            self.update_file()
        else:
            raise FileNotFoundError('Movies have not started in sync: Restart')
            
    def set_info(self, key:str='Name', val:str='Unknown'):
        self.logfile.set('Info', key, val)
    
        
    def log(self, msg:str):
        key = self.get_current_time()      
        val = sanitize_string(msg)    
        self.logfile.set(self.current_section, key, val)
        self.update_file()
  
    @classmethod
    def get_current_time(cls):
        """return time as string similar to kinovea file format
        i.e. YearMonthDay - HourMinutesSeconds.Milliseconds        
        """
        return datetime.now().strftime("%H:%M:%S.%f")
# %%