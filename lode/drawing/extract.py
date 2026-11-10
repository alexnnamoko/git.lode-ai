"""Drawing text extraction. OCR is optional and confidence-labelled; no geometry is inferred as fact."""
from __future__ import annotations
import io, re

def extract_pdf_pages(data: bytes):
    try: import fitz
    except Exception as e: raise RuntimeError('PyMuPDF is required to read PDFs. Install the requirements.txt dependencies.') from e
    doc=fitz.open(stream=data,filetype='pdf'); pages=[]
    for i,page in enumerate(doc):
        text=page.get_text('text') or ''
        words=page.get_text('words') or []
        pages.append({'page':i+1,'text':text,'words':[{'text':w[4],'bbox':[round(v,2) for v in w[:4]]} for w in words], 'width_pt':page.rect.width,'height_pt':page.rect.height,'is_scanned_candidate':len(text.strip())<20})
    return pages

def render_pdf_page(data: bytes, page_number: int, scale: float=1.5):
    import fitz
    doc=fitz.open(stream=data,filetype='pdf')
    if page_number<1 or page_number>len(doc): raise ValueError('Page number is outside this PDF.')
    pix=doc[page_number-1].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
    return pix.tobytes('png')

def extract_image_text(data: bytes):
    try:
        from PIL import Image
        import pytesseract
    except Exception:
        return {'text':'','available':False,'message':'OCR dependencies are unavailable. Image preview and manual verification are still supported.'}
    try:
        img=Image.open(io.BytesIO(data))
        d=pytesseract.image_to_data(img,output_type=pytesseract.Output.DICT)
        lines=[]; words=[]
        for i,t in enumerate(d['text']):
            t=t.strip()
            if not t: continue
            try: conf=float(d['conf'][i])
            except Exception: conf=-1
            words.append({'text':t,'confidence':conf,'bbox':[d['left'][i],d['top'][i],d['left'][i]+d['width'][i],d['top'][i]+d['height'][i]]})
        text=pytesseract.image_to_string(img)
        return {'text':text,'words':words,'available':True,'message':'OCR text is a draft only; verify every value against the drawing.'}
    except Exception as e: return {'text':'','available':False,'message':f'OCR could not process this image: {e}'}

def candidate_dimensions(text: str, page: int, word_items=None):
    """Surface dimension-like tokens for review; these are NOT interpreted as confirmed dimensions."""
    pattern=re.compile(r'(?<![A-Za-z0-9])(?:\d{1,5}(?:\.\d{1,3})?\s?(?:mm|cm|m)|\d{3,5})(?![A-Za-z0-9])',re.I)
    word_items=word_items or []
    out=[]
    for m in pattern.finditer(text or ''):
        token=m.group(0).strip()
        norm=lambda x: re.sub(r'[^a-z0-9.]','',str(x).lower())
        target=norm(token); matched=[]
        for w in word_items:
            wt=norm(w.get('text',''))
            if wt and (wt==target or wt in target or target in wt): matched.append(w)
        bbox=None
        if matched:
            boxes=[w.get('bbox') for w in matched if w.get('bbox') and len(w.get('bbox'))==4]
            if boxes:
                bbox=[min(x[0] for x in boxes),min(x[1] for x in boxes),max(x[2] for x in boxes),max(x[3] for x in boxes)]
        out.append({'value':token,'unit':'as printed / review required','page':page,'bounding_box':bbox,'confidence':'LOW — text candidate only','status':'Unverified','source':'Text/OCR candidate'})
    return out
