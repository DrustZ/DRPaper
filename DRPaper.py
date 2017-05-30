# -*- coding: utf-8 -*-
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter,XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from pdfminer.pdftypes import resolve1, PDFObjRef
from cStringIO import StringIO
from reftrainer import sent2features
import pycrfsuite
import lxml.html
import unicodedata, re

def remove_control_characters(s):
    return ''.join([i if ord(i) < 128 else ' ' for i in s])

class DRReference():
    def __init__(self, authors, title, journal=None):
        self.authors = authors
        self.title = title
        self.journal = journal

    # def download():

class DRPaper():
    def __init__(self):
        self.tagger = pycrfsuite.Tagger()
        self.tagger.open('citation.crfsuite')

    def extract(self, filepath):
        text = self.conver_pdf_to_txt(filepath)
        # print 'text converted'
        text = remove_control_characters(text)
        # print 'text cleaned'
        refrange = self.find_references_range(text)
        # print 'range finded'
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
                if any(x in pureline for x in keywords):
                    break

        if idx == 0:
            return None #not find keywords
        else:
            refs = lines[idx+1:]
            if appendix_idx > idx:
                refs = lines[idx+1:appendix_idx]
            return refs

    def extract_references(self, refs):
        # find one complete reference (may be cover multiple lines)
        def wrap_one_ref(lines, idxtype):
            start, to = 0, 1
            if to == len(lines):
                return start, to

            if idxtype == 1:
                while not lines[to].startswith('['):
                    to += 1
                    if to >= len(lines):
                        return start, to
                return start, to
            elif idxtype == 2:
                while re.match(r'^[1-9][0-9]?\s?\.', lines[to]) is None:
                    to += 1
                    if to >= len(lines):
                        return start, to
                return start, to
            else:
                while  True:
                    tags = tagger.tag(sent2features([[i] for i in lines[to].split()]))
                    if tags[0] != 'author':
                        to += 1
                        if to >= len(lines):
                            return start, to
                    else:
                        return start, to
        
        #check the reference index format is [1] or '1.' or None
        idxtype = 0 # 0-None 1-[1] 2-1.
        testline = " ".join(refs[:2])
        if '[1]' in testline:
            idxtype = 1
        elif re.match(r'^1\s?\.', refs[0]) or re.match(r'^1\s?\.', refs[1]):
            idxtype = 2

        # print refs[:10]
        base, cnt = 0, 0
        references = []
        while base < len(refs):
            start, end = wrap_one_ref(refs[base:], idxtype)
            print 'start new session\n', refs[start+base:end+base]
            words = ' '.join(refs[base+start:base+end])
            words = [[i] for i in words.split()]
            tags = self.tagger.tag(sent2features(words))
            assert len(tags) == len(words)

            title = ""
            for i, tag in enumerate(tags):
                if tag == 'title':
                    title += words[i][0] + ' '
                elif title:
                    references.append(title)
                    break
            print title, '\n'
            base += end
            cnt += 1.0
        # print 'find/actual:', (cnt/len(references))
        return references
        