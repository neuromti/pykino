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
from shutil import copyfile
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
        
class KinoWatcher():

    def __init__(self, path=r'C:\projects\kinovea'):
        self.path = path 
        self.files = None
            
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
                time.sleep(.1) 
        self.observer.stop()
        self.observer.join()
        self.files = handler.created_files
        return self.files

    def wait_finish(self, show:Callable=None):        
        if self.files is None:
            return
        
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
        
    
    def __init__(self, logpath=os.path.expanduser('~\Desktop\\recording'),
                 inifile=os.path.expanduser('~\Desktop\info.ini')):                
        # create log directory
        os.makedirs(logpath, exist_ok=True)        
        self.logpath = logpath
        
        #read ini file
        ini = configparser.ConfigParser()
        ini.read(inifile)        
        ID = ini.get('Info','id')
        fname = ID + '_' + datetime.now().strftime("%Y%m%d") + '.ini'        

        # initalize logfile        
        self.fname = os.path.join(self.logpath, fname)        
        self.logfile = configparser.ConfigParser()
        if os.path.exists(self.fname):
            self.logfile.read(self.fname)
        self.update_file()
        if not self.logfile.has_section('Info'):
            self.logfile.add_section('Info')
            for key in ini.options('Info'):
                val = ini.get('Info', key)
                self.logfile.set('Info', key, val)
        self.update_file()
        
    def new_recording(self, moviefiles:List[str]):
                       
        self.moviefiles = moviefiles
        m = moviefiles[-2]
        secA = os.path.splitext(os.path.split(m)[1])[0].split('_')[1]
        m = moviefiles[-1]
        secB = os.path.splitext(os.path.split(m)[1])[0].split('_')[1]
        if secB == secA:
            self.current_section = secA
            self.logfile.add_section(self.current_section)
            self.update_file()
            for i, m in enumerate(moviefiles):
                self.logfile.set(self.current_section, f'rawfile_{i}', m)
                self.update_file()

        else:
            raise FileNotFoundError('Movies have not started in sync: Restart')
            
    def log(self, msg:str):
        key = self.get_current_time()      
        val = sanitize_string(msg)    
        self.logfile.set(self.current_section, key, val)
        self.update_file()
  
    def dump(self):
        for source in self.moviefiles:
            destination = os.path.join(self.logpath, os.path.split(source)[1])
            copyfile(source, destination)
    
    
    @classmethod
    def get_current_time(cls):
        """return time as string similar to kinovea file format
        i.e. YearMonthDay - HourMinutesSeconds.Milliseconds        
        """
        return datetime.now().strftime("%Y%m%d-%H%M%S.%f")
# %%