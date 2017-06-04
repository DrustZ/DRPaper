# coding: utf-8
from Interact_terminal import DRTerminal
import os

pdfs = ['/Users/zmr/MEGAsync/campus/Momenta/papers/new_week11/1705.08214.pdf']
# traverse root directory, and list directories as dirs and files as files
# rooder="/Users/zmr/MEGAsync/campus/Momenta/papers"
# for root, dirs, files in os.walk(rooder):
#     path = root.split(os.sep)
#     # print( os.path.basename(root))
#     for file in files:
#         if file.endswith('.pdf'):
#             pdfs.append(root+'/'+file)

def test():
    drterminal = DRTerminal()
    drterminal.display()

test()