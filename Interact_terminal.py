from __future__ import print_function
import DRPaper
import os
import time
import threading
from blessings import Terminal 

class DRTerminal():
    def __init__(self):
        self.term   = Terminal()
        self.folder = ''
        self.files  = []
        self.e      = threading.Event()
        self.context_lines  = []
        self.expand_lines   = []
        self.drpaper    = DRPaper.DRPaper()
        self.prompt     = { 'on_start':self.term.bold('[DRPaper] ')+\
                                     'please enter the pdf file path you want to scan\n',
                            'on_ref_print':self.term.bold('[DRPaper] ')+\
                                     'enter '+self.term.green('"c+[ref numbers]"("c 1,2")')+' to show contexts of the references\n'+\
                                     ' '*10+'or enter '+self.term.green('"e+[ref numbers]"("e 1")')+' to expand whole contents of the ref\n'+\
                                     ' '*10+'or enter '+self.term.green('"d+[ref numbers]"("d 1,3,4")')+' to download the references\n'+\
                                     ' '*10+'or enter '+self.term.green('H')+' to start again\n'}

    def refresh(self):
        self.folder = ''
        self.files = []
        self.context_lines = []
        self.expand_lines = []
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
        print(self.term.clear)
        print(self.term.bright_blue('The paper contains '+\
                  str(len(self.drpaper.refdict))+' references.'))
        for k,v in self.drpaper.refdict.items():
            ref = self.drpaper.refdict[k]
            if ref.title:
                print(self.term.cyan("[%d] %s"%(k,ref.title)))
            else:
                print(self.term.cyan("[%d] EMPTY TITLE"%k))
            if k in self.context_lines:
                print(self.term.italic_black(self.drpaper.getref_context(k)))
            if k in self.expand_lines:
                print(ref.lines)

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

    def get_on_ref_param(self, param):
        self.context_lines = []
        self.expand_lines  = []
        lines = param.split()[1].split(',')
        for i,value in enumerate(lines):
            try:
                lines[i]=int(value)
            except ValueError:
                continue
        if param.startswith('c'):
            self.context_lines=lines
        if param.startswith('e'):
            self.expand_lines=lines
        return

    def display(self):
        while True:
            try:
                param = raw_input(self.prompt['on_start']).strip()
                if param.endswith('.pdf') and os.path.isfile(param):
                    self.files = [param]
                    t = threading.Thread(name='search_refs',target=self.search_refs,args=(0,))
                    t.daemon = True
                    t.start()
                    self.print_processing()
                    t.join()
                    self.print_refs()
                    while True:
                        param = raw_input(self.prompt['on_ref_print']).strip()
                        #get another input
                        if param.upper() == 'H':
                            break
                        elif param.startswith('c ') or param.startswith('e '):
                            self.get_on_ref_param(param)
                            self.print_refs()

                else:
                    print('[Error] The file is not a pdf or is not exist.')
                # elif os.path.isdir(param):
                    # self.folder = param
                    # self.searchfiles()
            except (KeyboardInterrupt, SystemExit):
                exit()