# -*- coding: utf-8 -*-
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter,XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1, PDFObjRef
from cStringIO import StringIO
from reftrainer import sent2features

from collections import OrderedDict
import string
import pycrfsuite
import lxml.html
import unicodedata, re

def remove_control_characters(s):
    return ''.join([i if ord(i) < 128 else ' ' for i in s])

class DRReference():
    def __init__(self):
        self.authors = ""
        self.title = ""
        self.journal = ""
        self.arxiv = ""
        self.lines = ""

    # def download():

class DRPaper():
    def __init__(self):
        self.tagger = pycrfsuite.Tagger()
        self.tagger.open('citation.crfsuite')
        self.idxtype = 0
        self.refdict = OrderedDict()
        self.content = ""
        self.positions = {}

    def refresh(self):
        self.idxtype = 0
        self.refdict.clear()
        self.positions = {}
        self.content = ""

    def extract(self, filepath):
        self.refresh()
        text = self.conver_pdf_to_txt(filepath)
        # print 'text converted'
        text = remove_control_characters(text)
        # print 'text cleaned'
        refrange = self.find_references_range(text)
        
        return self.extract_references(refrange)

    def conver_pdf_to_txt(self, filepath):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec='utf-8', laparams=laparams)
        fp = file(filepath, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        pagenos=set()

        for page in PDFPage.get_pages(fp, pagenos, maxpages=0, password="",caching=True, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue()

        fp.close()
        device.close()
        retstr.close()
        return text

    def find_references_range(self, text):
        lines = text.split('\n')
        lines = [l.strip() for l in lines ]
        lines = filter(None, lines) #remove empty lines

        idx,appendix_idx = len(lines), -1
        keywords = ['REFERENCES', 'References', 'REFERENCE', 'Reference']
        appendix_keywords = ['SUPPLEMENTARY MATERIAL', 'Supplementary Material', 'Appendix', 'APPENDIX', 'Appendix:', 'APPENDIX:']
        for line in lines[::-1]:
            idx -= 1
            if any(x in line for x in appendix_keywords):
                appendix_idx = idx
            if any(x in line for x in keywords):
            #then we check if and only if the characters are 'reference(s)'
                pureline = " ".join(re.findall("[a-zA-Z]+",line))
                if any(x == pureline for x in keywords):
                    break

        if idx == 0:
            return None #not find keywords
        else:
            self.content = ' '.join(lines[:idx-1])
            refs = lines[idx+1:]
            if appendix_idx > idx:
                refs = lines[idx+1:appendix_idx]
            return refs

     # find one complete reference (may be cover multiple lines)
    def wrap_one_ref(self, lines):
        start, to = 0, 1
        if to == len(lines):
            return start, to

        if self.idxtype == 1:
            while not lines[to].startswith('['):
                to += 1
                if to >= len(lines):
                    return start, to
            return start, to
        elif self.idxtype == 2:
            while re.match(r'^[1-9][0-9]?\s?\.', lines[to]) is None:
                to += 1
                if to >= len(lines):
                    return start, to
            return start, to
        else:
            while  True:
                tags = self.tagger.tag(sent2features([[i] for i in lines[to].split()]))
                if tags[0] != 'author':
                    to += 1
                    if to >= len(lines):
                        return start, to
                else:
                    return start, to

    def extract_references(self, refs):
        if not refs or len(refs) < 1:
            return False
        #check the reference index format is [1] or '1.' or None
        self.idxtype = 0 # 0-None 1-[1] 2-1.
        testline = " ".join(refs[:3])
        if '[1]' in testline:
            self.idxtype = 1
        elif re.match(r'^1\s?\.', refs[0]):
            self.idxtype = 2

        #find reference within lines
        base, cnt = 0, 0
        references = []
        while base < len(refs):
            #find lines that contain one reference
            start, end = self.wrap_one_ref(refs[base:])
            # print 'start new session\n', refs[start+base:end+base]

            drref = DRReference()
            words = ' '.join(refs[base+start:base+end])
            words = words.replace('"', ' ').replace('.', '. ')
            #store the original lines
            drref.lines = words

            words = [[i] for i in words.split()]
            tags = self.tagger.tag(sent2features(words))
            assert len(tags) == len(words), 'length: tags is not equal to words\n'

            ref_idx = 0
            for i, tag in enumerate(tags):
                if tag == 'title':
                    drref.title += words[i][0] + ' '
                if tag == 'author':
                    drref.authors += words[i][0] + ' '
                if tag == 'journal' or tag == 'booktitle':
                    drref.journal += words[i][0] + ' '
                if tag == 'arxiv':
                    drref.arxiv += words[i][0]
                if tag == 'idx' and self.idxtype > 0:
                    ref_idx = int(''.join(x for x in words[i][0] if x.isdigit()))
            drref.title = drref.title.replace('-','').split('.')[0]
            if ref_idx > 0:
                self.refdict[ref_idx] = drref
            else:
                self.refdict[len(self.refdict)+1] = drref

            base += end
            cnt += 1.0
        # print 'find/actual:%f, find: %f, actual: %d\n' % (len(references)/cnt, len(references), cnt)
        return True

    def find_ref_in_text(self, refid):
        #first, if we haven't initialize the postition dict
        #we search all '[...]' occurence and save them in position dict
        if len(self.positions) == 0:
            #regex for [(number, ..., number, )number]
            rg = re.compile(r'\[(\d{1,2}, *)*\d{1,2}\]')
            it = re.finditer(rg, self.content)

            for i in it:
                 ocur = i.group()
                 num_group = ocur[1:-1].split(',')
                 for num in num_group:
                    self.positions.setdefault(int(num),[]).append(i.span())
        
        result = ""
        if not (refid in self.positions):
            return result
        for pos in self.positions[refid]:
            # before = self.content[max(pos[0]-100,0):pos[1]].split('.')
            # after = self.content[pos[1]:pos[1]+100].split('.')
            # if len(before) > 1:
                # result += '...'+'.'.join(before[-2:])
            # else:
            result += '...'+' '.join(self.content[max(pos[0]-100,0):pos[1]].split()[-15:])
            # if len(after) > 1:
                # result += '.'.join(after[:2]) + '...\n'
            # else:
            result += ' '.join(self.content[pos[1]:pos[1]+100].split()[:10]) + '...\n'
        return result

    def getref_context(self, refid):
        if refid < self.refdict.keys()[-1]:
            return self.find_ref_in_text(refid)
