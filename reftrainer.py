import lxml.html as html
import pycrfsuite

def preprocess(filename):
    words = []
    with open(filename) as f:
        lines = f.readlines()
        for line in lines:
            tree = html.fromstring(line)
            sents = []
            for ele in tree:
                tag = ele.tag
                contents = ele.text_content().split()
                sents.extend([(word, tag) for word in contents])
            words.append(sents)
    return words

def word2features(sent, i):
    word = sent[i][0]
    features = [
        'bias',
        'word.lower=' + word.lower(),
        'word[-3:]=' + word[-3:],
        'word[-2:]=' + word[-2:],
        'word.isupper=%s' % word.isupper(),
        'word.istitle=%s' % word.istitle(),
        'word.isdigit=%s' % word.isdigit(),
        'word.containdot=%s' % ('.' in word),
        'word.containcom=%s' % (',' in word),
    ]
    for n in range(1, 3):
        if i-n >= 0:
            word1 = sent[i-n][0]
            features.extend([
                '-%d:word=%s' % (n, word1),
                '-%d:word.lower=%s' % (n, word1.lower()),
                '-%d:word.istitle=%s' % (n, word1.istitle()),
                '-%d:word.isupper=%s' % (n, word1.isupper()),
            ])
        else:
            features.append('BOS')

    for n in range(1, 3):
        if i+n < len(sent):
            word1 = sent[i+n][0]
            features.extend([
                '+%d:word=%s' % (n, word1),
                '+%d:word.lower=%s' % (n, word1.lower()),
                '+%d:word.istitle=%s' % (n, word1.istitle()),
                '+%d:word.isupper=%s' % (n, word1.isupper()),
            ])
        else:
            features.append('EOS')
                
    return features


def sent2features(sent):
    return [word2features(sent, i) for i in range(len(sent))]

def sent2labels(sent):
    return [label for token, label in sent]

def sent2tokens(sent):
    return [token for token, label in sent]

def train():
    train_sents = preprocess('trainbib')
    #get features
    # print sent2features(train_sents[0])[0]
    X_train = [sent2features(s) for s in train_sents]
    y_train = [sent2labels(s) for s in train_sents]

    trainer = pycrfsuite.Trainer(verbose=False)

    for xseq, yseq in zip(X_train, y_train):
        trainer.append(xseq, yseq)

    trainer.set_params({
        'c1': 1.0,   # coefficient for L1 penalty
        'c2': 1e-3,  # coefficient for L2 penalty
        'max_iterations': 100,  # stop earlier

        # include transitions that are possible, but not observed
        'feature.possible_transitions': True
    })

    trainer.train('citation.crfsuite')
    print len(trainer.logparser.iterations), trainer.logparser.iterations[-1]

# train()