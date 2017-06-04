from __future__ import print_function
import DRPaper
import os
import time
import threading
from blessings import Terminal 

class DRTerminal():
    def __init__(self):
        self.term = Terminal()
        self.folder = ''
        self.files = []
        self.e = threading.Event()
        self.drpaper = DRPaper.DRPaper()

    def refresh(self):
        self.folder = ''
        self.files = []
        self.drpaper.refresh()

    def searchfiles(self):
        for root, dirs, files in os.walk(self.folder):
            path = root.split(os.sep)
            for file in files:
                if file.endswith('.pdf'):
                    self.files.append(root+'/'+file)

    def search_refs(self, fid):
        self.drpaper.extract(self.files[fid])
        self.e.set()

    def print_refs(self):
        for k,v in self.drpaper.refdict.items():
            ref = self.drpaper.refdict[k]
            print(ref.title+'\n')

    def print_context(self):
        pass

    def print_processing(self):
        processing = ['processing   ', 'processing.  ', 'processing.. ', 'processing...']
        cnt = 0
        print('\n')
        while not self.e.isSet():
            with self.term.location():
                print(self.term.move_up+processing[cnt%4])
                cnt += 1
                time.sleep(0.2)
        print(self.term.move_up,self.term.clear_eol)
        self.e.clear()

    def display(self):
        self.prompt = self.term.bold('[DRPaper]')+\
                                     'please enter the pdf file or folder you want to scan\n'
        while True:
            try:
                param = raw_input(self.prompt).strip()
                if param.endswith('.pdf') and os.path.isfile(param):
                    self.files = [param]
                    t = threading.Thread(name='search_refs',target=self.search_refs,args=(0,))
                    t.daemon = True
                    t.start()
                    self.print_processing()
                    t.join()
                    self.print_refs()
                # elif os.path.isdir(param):
                    # self.folder = param
                    # self.searchfiles()
            except (KeyboardInterrupt, SystemExit):
                exit()