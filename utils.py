from collections import Counter
import re
import pickle as pkl
from os.path import exists
import gdown
from pdfminer.layout import LTChar


pdf_bad_chars = re.compile(r'([\n\t•­\f])|(\(cid:[0-9]+\))')

epub_bad_classes = {'s', 's2', 's3','s4','s5', 's6', 's7', 's8', 
               'calibre1', 'section1', 'hsection1'}

words_pattern = re.compile(r'\w+-\w*')


def load_vocab():
    if not exists('vocab.pkl'):
        print('Downloading vocab for pdf...')
        url = "https://drive.google.com/uc?id=1VYvJ1oNOPO1Yhu4gNs2R-HREy3TFlt35"
        gdown.download(url, 'vocab.pkl', quiet=True)
    with open('vocab.pkl', 'rb') as f:
        return pkl.load(f)


vocab = load_vocab()


def fix_hyphens(indices, paragraphs_old):
    paragraphs_new = paragraphs_old.copy()

    for i in indices:
        par = paragraphs_old[i]
        o = 0  # offset
        for m in words_pattern.finditer(par):
            st, ed = m.span()
            word = m.group()
            word_repl = word.replace('-', '')
            if not word.lower() in vocab and word_repl.lower() in vocab:
                par = par[:st-o] + word_repl + par[ed-o:]
                o += 1

        paragraphs_new[i] = par

    return paragraphs_new


def make_obj(text, obj_type):
    attrs = {}
    if obj_type.startswith('h'):
        attrs['level'] = int(obj_type[-1])
        obj_type = 'heading'
    obj = {
        'type': obj_type,
        'attrs': attrs,
        'content': [{'type': "text", "text": text}]
    }
    return obj


def get_size(element):
    for line in element:
        if isinstance(line, LTChar):
            return round(line.size)
        return get_size(line)


def infer_text_types_pdf(font_sizes):
    font_counts = Counter(font_sizes)
    p_size = font_counts.most_common(1)[0][0]

    head_w = [p_size*w for w in (2, 1.5, 1.25)]

    types = []
    for size in font_sizes:
        if size >= head_w[0]:
            types.append('h1')
        elif size >= head_w[1]:
            types.append('h2')
        elif size >= head_w[2]:
            types.append('h3')
        elif size > p_size:
            types.append('h4')
        else:
            types.append('paragraph')

    return types
