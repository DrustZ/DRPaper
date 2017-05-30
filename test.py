# coding: utf-8
import DRPaper

def test():
    drpaper = DRPaper.DRPaper()
    # def test(ls=['/Users/zmr/MEGAsync/campus/Spring2017/毕设/papers/motioncapture/MotionPredictFrequency.pdf', '/Users/zmr/MEGAsync/campus/Spring2017/毕设/papers/3Dcommunicate/hardware/telehumanCylinder.pdf', '/Users/zmr/MEGAsync/campus/Spring2017/毕设/papers/other/magnenatthalmann2006.pdf', '/Users/zmr/MEGAsync/campus/Spring2017/毕设/papers/other/2010-UIST-Gustafson-ImaginaryInterfaces.pdf', '/Users/zmr/MEGAsync/campus/Momenta/papers/1609.07009.pdf']):
    ls=[ '/Users/zmr/MEGAsync/campus/Spring2017/毕设/papers/motioncapture/MotionPredictFrequency.pdf','/Users/zmr/MEGAsync/campus/Spring2017/毕设/papers/3Dcommunicate/hardware/telehumanCylinder.pdf', '/Users/zmr/MEGAsync/campus/Spring2017/毕设/papers/other/magnenatthalmann2006.pdf', '/Users/zmr/MEGAsync/campus/Spring2017/毕设/papers/other/2010-UIST-Gustafson-ImaginaryInterfaces.pdf', '/Users/zmr/MEGAsync/campus/Momenta/papers/1609.07009.pdf']
    for i in ls:
        reference = drpaper.extract(i)
        for ref in reference:
            print ref
        
test()