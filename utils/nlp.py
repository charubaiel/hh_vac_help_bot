
import numpy as np
import re
import matplotlib.pyplot as plt
from navec import Navec
from natasha import (
    Segmenter,
    MorphVocab,
    NewsEmbedding,
    NewsMorphTagger,
    Doc
)
import os

plt.style.use('ggplot')


nav = Navec.load(f'{os.getcwd()}/utils/emb_navec.tar')


segmenter = Segmenter()
morph_vocab = MorphVocab()
emb = NewsEmbedding()
morph_tagger = NewsMorphTagger(emb)



def normalizer (text):
    words_only = re.sub('[^А-я]+',' ',text.lower())
    doc = Doc(words_only)
    doc.segment(segmenter)
    doc.tag_morph(morph_tagger)
    clean_text = []
    for token in doc.tokens:
        token.lemmatize(morph_vocab)
        if (len(set(token.lemma))>1):
            clean_text.append(token.lemma)
            
    return ' '.join(clean_text)
    

def get_sentence_vector(sentence_list,normalize=False):
    vectors = []
        
    for sentence in sentence_list:
        if normalize:
            sentence = normalizer(sentence)
        sent_vec = []
        for i in sentence.split():
            if i in nav:
                sent_vec.append(nav[i])
            else:
                sent_vec.append(nav['<unk>'])
        if sentence.strip() == '':
            sent_vec = [nav['<unk>']]
        vectors.append(np.mean(sent_vec,axis=0))
    return np.vstack(vectors)