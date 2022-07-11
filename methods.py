from docx import Document
from pdfminer.layout import LTTextContainer, LTChar
from pdfminer.high_level import extract_pages
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from utils import make_obj, get_size, fix_hyphens, infer_text_types_pdf, pdf_bad_chars, epub_bad_classes



def convert_docx(fs):
    doc = Document(fs)
    paragraphs = []
    for p in doc.paragraphs:
        if (text := p.text) not in {'', ' '}:
            if (p_has_size := p.runs[0].font.size):
                if (p_size := p_has_size.pt) >= 27:
                    text_type = 'h1'
                elif p_size >= 24:
                    text_type = 'h2'
                elif p_size >= 21:
                    text_type = 'h3'
                elif p_size >= 18:
                    text_type = 'h4'
                else:
                    text_type = 'paragraph'
            else:
                text_type = 'paragraph'

            paragraphs.append(make_obj(text, text_type))
    return paragraphs


def convert_epub(fs):
    book = epub.read_epub(fs)
    docs = [d for d in book.get_items_of_type(ITEM_DOCUMENT)]
    order = [s[0] for s in book.spine]
    try:
        docs = sorted(docs, key=lambda d: order.index(d.id))
    except ValueError:
        print('Failed to sort parts in epub book')
    paragraphs = []
    for doc in docs:
        soup = BeautifulSoup(doc.get_body_content(), 'html.parser')
        tags = soup.find_all(['p', 'div', 'h1', 'h2'])
        for tag in tags:
            cls_attrs = tag.get('class', [None])
            if len(cls_attrs) > 1:
                print('Multiple classes!')
                continue
            else:
                cls = cls_attrs[0]
            text = tag.get_text().replace('\xa0', '').replace('\n', '')

            if text != "":
                if tag.name in {'h1', 'h2'} or cls in {'title', 'subtitle'}:
                    paragraphs.append(make_obj(text, 'h1'))
                elif cls in {'p1', 'paragraph', 'calibre3'} or cls not in epub_bad_classes:
                    paragraphs.append(make_obj(text, 'paragraph'))
    return paragraphs


def convert_pdf(fs):
    paragraphs, sizes = pdf_extract_by_elements(fs)

    if len(paragraphs) == 0:
        paragraphs, sizes = pdf_extract_by_chars(fs)

    targets = [i for i, par in enumerate(paragraphs) if par.count('-') > 0]

    paragraphs = fix_hyphens(targets, paragraphs)

    types = infer_text_types_pdf(sizes)
    assert len(types) == len(paragraphs)

    return [make_obj(text, text_type) for text, text_type in zip(paragraphs, types)]

def pdf_extract_by_elements(fs):
    paragraphs = []
    sizes = []
    concat_next = False

    for page_layout in extract_pages(fs):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                par = element.get_text()

                par = pdf_bad_chars.sub('', par).strip()
                if par not in {"", ".", "-"}:
                    if concat_next:
                        if not par[0].isdigit() and par[0].islower():
                            paragraphs[-1] = paragraphs[-1][:-1]+par
                            concat_next = False
                    else:
                        size = get_size(element)
                        paragraphs.append(par)
                        sizes.append(size)

                    if par.endswith('-'):
                        t = par.split()[-1]
                        if len(t) > 2:
                            concat_next = True

    return paragraphs, sizes

def pdf_extract_by_chars(fs):
    paragraphs = []
    sizes = []
    concat_next = False

    for page_layout in extract_pages(fs):
        size = None
        letterbag = []
        for element in page_layout:
            for child in element:
                if isinstance(child, LTChar):
                    letter = child.get_text()
                    letterbag.append(letter)
                    if not size:
                        size = round(child.size)

        par = "".join(letterbag)
        # todo: extract to portable method
        par = pdf_bad_chars.sub('', par).strip()
        if par not in {"", ".", "-"}:
            if concat_next:
                if not par[0].isdigit() and par[0].islower():
                    paragraphs[-1] = paragraphs[-1][:-1]+par
                    concat_next = False
            else:
                paragraphs.append(par)
                sizes.append(size)

            if par.endswith('-'):
                t = par.split()[-1]
                if len(t) > 2:
                    concat_next = True

    return paragraphs, sizes
